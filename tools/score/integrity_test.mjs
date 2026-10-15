// integrity_test.mjs — the integrity rules (web/editor-obra/app/js/integrity.js) against the score of the piece: alert fatigue,
// silent breaks and the cases of the audit (docs/editor-obra/anexos/18-auditoria-app.md, lote 2).
// It runs on the frozen fixture tools/score/fixtures/f0-score.json (so real edits of the piece never break it); --live runs it
// on obra/score/score.json (see tools/score/test_score.mjs).
//   node tools/score/integrity_test.mjs [--live]
import fs from 'fs';
import path from 'path';
import { createRequire } from 'module';
import { fileURLToPath } from 'url';
import { testScore, schema3Copy, catalogPath } from './test_score.mjs';
const require = createRequire(import.meta.url);
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
// plain Node: integrity.js is UMD like engine.js and edits.js, no window shim (audit D12, lote 5 design B §8.1)
const E = require(path.join(ROOT, 'web/editor-obra/app/js/engine.js'));
const X = require(path.join(ROOT, 'web/editor-obra/app/js/edits.js'));
const P = require(path.join(ROOT, 'web/editor-obra/app/js/partitura.js'));
const I = require(path.join(ROOT, 'web/editor-obra/app/js/integrity.js'));
const M = require(path.join(ROOT, 'web/editor-obra/app/js/media.js'));
const P_ = require(path.join(ROOT, 'web/editor-obra/app/js/policy.js'));
const rd = p => JSON.parse(fs.readFileSync(path.join(ROOT, p), 'utf8'));
const { score, name: SRC } = testScore(); console.log('on the ' + SRC);
const contract = JSON.parse(fs.readFileSync(catalogPath('contract'), 'utf8')), bind = JSON.parse(fs.readFileSync(catalogPath('binding'), 'utf8'));
const T0 = E.resolve(score, { persona: 'typical' }), P0 = I.staticProblems(score, T0, contract), gov = P.governedBy(score, T0, bind);
const idOf = (k, b) => Object.keys(score.elements).find(id => score.elements[id].key === k && (!b || score.beats[score.elements[id].beat].key === b));
let fails = 0;
const check = (n, ok, info) => { console.log((ok ? '  ok   ' : '  FAIL ') + n + (info ? '  · ' + info : '')); if (!ok) fails++; };
const judge = (op, next) => { const T1 = E.resolve(next, { persona: 'typical' }); const P1 = I.staticProblems(next, T1, contract);
  const r = I.opItems(Object.assign({ prevScore: score }, op), next, { problems: P0 }, { problems: P1 }, contract, E, { gov });
  return Object.assign(r, { card: r.items.some(i => i.sv !== 'info'), reason: r.items.some(i => i.sv === 'block' || i.lock) }); };
const clone = o => JSON.parse(JSON.stringify(o));

console.log('at load');
check('integrity.js loads in plain Node (no window): require gives the API (D12)', typeof globalThis.window === 'undefined' && ['contractFor', 'staticProblems', 'opItems', 'effect', 'rippleLine', 'divergent', 'editedSince', 'fmt'].every(k => typeof I[k] === 'function'));
const byRule = {}; for (const p of P0) if (p.st === 'open' && p.sv !== 'info') byRule[p.rule] = (byRule[p.rule] || 0) + 1;
console.log('  open problems: ' + JSON.stringify(byRule));
check('no "blocking" at load (the anchor loops are warnings with a fix)', !P0.some(p => p.st === 'open' && p.sv === 'block'));

console.log('alert fatigue (B2/C3): nudge every element +0.1 s');
let cards = 0, reasons = 0, vo = 0, voCards = 0; const kids = E.dependents(score);
for (const id of Object.keys(score.elements)) {
  const r = judge({ type: 'move', ids: [id] }, X.move(score, id, .1, {}, kids));
  if (r.card) cards++; if (r.reason) reasons++;
  if (score.elements[id].type === 'vo') { vo++; if (r.card) voCards++; }
}
check(`cards on a 0.1 s nudge: ${cards} of 592 (audit: 146)`, cards < 60, `${reasons} need a reason · voices ${voCards}/${vo} (audit: 70/70)`);

console.log('silent breaks (A5, C2, +D1, B4)');
{ const id = idOf('PASO', '2.7a'), n = clone(score); n.elements[id].dur.value = 9.5; const r = judge({ type: 'trim', ids: [id] }, n);
  check('trim PASO to 9.5 s says the ripple', /later item/.test(r.ripple) && /total/.test(r.ripple), r.ripple); }
{ const id = idOf('CANDS_IN'), n = clone(score); n.elements[id].dur = { mode: 'fixed', value: n.elements[id].dur.value + 3 }; const r = judge({ type: 'trim', ids: [id] }, n);
  check('trim CANDS_IN +3 s checks VO_04 that it carries (+D1)', r.items.some(i => i.keys.includes('VO_04')), r.items.map(i => i.rule + ':' + i.keys.join(',')).join(' ')); }
{ const id = idOf('VO_10'), n = clone(score); n.elements[id].text += ' and a much longer sentence that changes the length of the voice'; const r = judge({ type: 'text', ids: [id] }, n);
  check('changing the words of a wired voice warns (needs re-recording)', r.items.some(i => i.sv === 'warn' && /record/.test(i.body)), r.ripple); }
{ const n = clone(score), id = idOf('DISCLAIMER'); n.elements[id].dur.value = 320; const r = judge({ type: 'trim', ids: [id] }, n);
  check('DISCLAIMER to 320 s: total in the ripple line and the Partitura knob named', /total/.test(r.ripple) && r.items.some(i => i.rule === 'C3.PARTITURA'), r.ripple); }

console.log('voices (B2, B8)');
{ const id = idOf('VO_10'), r = judge({ type: 'move', ids: [id] }, X.move(score, id, .3, {}, kids));
  check('VO_10 +0.3 s keeping its order: no card', !r.card, r.items.map(i => i.sv + ' ' + i.rule).join(', ')); }
{ const a = idOf('VO_13'), r = judge({ type: 'move', ids: [a] }, X.move(score, a, 5, { alone: true }, kids));
  check('VO_13 +5 s past VO_14: warns about the order', r.items.some(i => i.sv === 'warn' && /order|overlaps/.test(i.body)), r.items.map(i => i.body).join(' | ').slice(0, 160)); }
{ const id = idOf('VO_01h'), r = judge({ type: 'delete', ids: [id], removed: { [id]: score.elements[id] } }, (() => { const n = clone(score); delete n.elements[id]; return n; })());
  check('VO_01h (not wired) can be deleted without a reason', !r.reason); }
{ const n = clone(score); const id = 'el_new1'; n.elements[id] = Object.assign(clone(score.elements[idOf('VO_10')]), { key: 'VO_NEW', isNew: true });
  check('a voice made in the editor has no contract', I.contractFor(id, n.elements[id], contract).length === 0); }

console.log('fingerprints (A6, B5, +D2)');
{ const n = clone(score); n.beats[Object.keys(n.beats).find(b => n.beats[b].key === '1.2')].at.off += 60;
  const P1 = I.staticProblems(n, E.resolve(n, { persona: 'typical' }), contract);
  const f0 = P0.find(p => p.rule === 'C2.TOTAL.GOAL').fp, f1 = P1.find(p => p.rule === 'C2.TOTAL.GOAL').fp;
  check('+60 s gives the 15:00 rule a new fingerprint (it reopens)', f0 !== f1, f0 + ' → ' + f1); }

console.log('≠ APK derived (B6, C6)');
{ const d0 = I.divergent(score, T0, contract, gov, score.golden); check('no divergence at load', d0.size === 0, d0.size + '');
  const id = idOf('VO_05'), n = X.move(score, id, 5, {}, kids), T1 = E.resolve(n, { persona: 'typical' });
  const d1 = I.divergent(n, T1, contract, P.governedBy(n, T1, bind), score.golden);
  check('moving VO_05 marks it ≠ APK', d1.has(id)); const back = X.move(n, id, -5, {}, E.dependents(n));
  check('moving it back clears it', !I.divergent(back, E.resolve(back, { persona: 'typical' }), contract, gov, score.golden).has(id)); }

console.log('change the anchor (C9)');
{ const vo5 = idOf('VO_05'), r = X.reanchor(score, vo5, { ref: idOf('VO_04'), edge: 'end' }, E), j = judge({ type: 'reanchor', ids: [vo5] }, r.next);
  check('VO_05 re-anchored after VO_04: no card, no ripple (the typical time is kept)', r.ok && !j.card && !j.ripple, j.items.map(i => i.sv + ' ' + i.rule).join(', ') || j.ripple);
  const ed = I.editedSince(score, r.next, E);
  check('  it counts as edited (and only it)', ed.has(vo5) && ed.size === 1, [...ed].map(k => score.elements[k].key).join(', '));
  const T1 = E.resolve(r.next, { persona: 'typical' });
  check('  nothing becomes ≠ APK', I.divergent(r.next, T1, contract, P.governedBy(r.next, T1, bind), score.golden).size === 0); }
{ const b = Object.keys(score.beats).find(k => score.beats[k].key === '2.7b'), r = X.reanchor(score, b, null, E), j = judge({ type: 'reanchor', ids: [] }, r.next);
  check('moment 2.7b detached (follows 2.7a): no card, no ripple', r.ok && !j.card && !j.ripple, j.ripple);
  check('  no element counts as edited (a moment has no clip to mark)', I.editedSince(score, r.next, E).size === 0); }
// C1.ANCHOR.MISSING with a lost END: the message says it is what it lasts until; the repair touches only that anchor
{ const calm = idOf('CALM'), s = clone(score); s.elements[calm].end.ref = 'el_gone_test';
  const Ts = E.resolve(s, { persona: 'typical' }), p = I.staticProblems(s, Ts, contract).find(x => x.rule === 'C1.ANCHOR.MISSING' && x.el === calm);
  check('a lost end is reported as "lasts until something that no longer exists"', !!p && /lasts until something that no longer exists/.test(p.msg), p && p.msg);
  const r = X.detachLost(s, calm, E), Tn = r.ok && E.resolve(r.next, { persona: 'typical' }), Pn = r.ok && I.staticProblems(r.next, Tn, contract);
  check('  Detach repairs it: no C1.ANCHOR.MISSING left, its start anchor untouched', r.ok && !Pn.some(x => x.rule === 'C1.ANCHOR.MISSING') && JSON.stringify(r.next.elements[calm].at) === JSON.stringify(s.elements[calm].at), r.ok ? '' : r.why);
  const ed = r.ok && I.editedSince(s, r.next, E);
  check('  it counts as edited (and only it)', r.ok && ed.has(calm) && ed.size === 1); }

console.log('copies and several at once (C10)');
{ const vo10 = idOf('VO_10'), tb = Object.keys(score.beats).find(k => score.beats[k].key === '2.4');
  const r = X.planPaste(score, X.clipOf(score, [vo10], E), { beat: tb, off: 3 }, E, { who: 'B' }), c = r.ok && r.next.elements[r.ids[0]];
  check('a copy of a wired voice (VO_10) is new: no contract, so no Unreal item on the card', r.ok && I.contractFor(r.ids[0], c, contract).length === 0 && I.contractFor(vo10, score.elements[vo10], contract).length > 0
    && !judge({ type: 'paste', ids: r.ids }, r.next).items.some(i => i.ly === 'C3' && i.sv !== 'info'), r.ok ? c.key : r.why);
  const T1 = r.ok && E.resolve(r.next, { persona: 'typical' });
  check('  the copy is never ≠ APK and the original does not become it', r.ok && I.divergent(r.next, T1, contract, P.governedBy(r.next, T1, bind), score.golden).size === 0);
  const ids = [idOf('VO_13'), idOf('VO_14')], n = X.moveMany(score, ids, 1, {}, E, kids), j = judge({ type: 'move', ids }, n);
  check('VO_13 and VO_14 +1 s together, in order: judged by effect like one move (no card)', !j.card, j.items.map(i => i.sv + ' ' + i.rule).join(', ') || j.ripple); }

console.log('contract and Partitura bound by element id (D10, lote 5 design A §7)');
{
  const def = rd('obra/unreal/partitura_def.json');
  // controls: the same files without their ids (rules and key lookups, as the editor judged before), and the contract as it
  // was before tools/score/bind_ids.mjs (no ids, no vo.unused / vo.noasset, vo.wired without excludeKeys)
  const contract0 = clone(contract); for (const c of contract0.entries) { delete c.ids; delete c.idKeys; delete c.idsFrom; }
  const bind0 = clone(bind); for (const b of bind0.binds) delete b.ids; for (const o of Object.values(bind0.origins)) delete o.ids;
  const before = clone(contract0); before.entries = before.entries.filter(c => c.id !== 'vo.unused' && c.id !== 'vo.noasset'); delete before.entries.find(c => c.id === 'vo.wired').match.excludeKeys;
  const ren = (s, id, name) => { const n = clone(s); X.renameEl(n.elements[id], name); return n; };
  const judgeOn = (prev, op, next, c, b) => { const Tp = E.resolve(prev, { persona: 'typical' }), Tn = E.resolve(next, { persona: 'typical' });
    const r = I.opItems(Object.assign({ prevScore: prev }, op), next, { problems: I.staticProblems(prev, Tp, c) }, { problems: I.staticProblems(next, Tn, c) }, c, E, { gov: P.governedBy(prev, Tp, b) });
    return Object.assign(r, { card: r.items.some(i => i.sv !== 'info'), reason: r.items.some(i => i.sv === 'block' || i.lock) }); };
  const rules = it => it.items.map(i => i.sv + ' ' + i.rule).join(', ') || '—';
  const stale = (s, b) => P.staleProblems(P.drift(s, E.resolve(s, { persona: 'typical' }), def, null, b), def.stages);

  // at load the ids change nothing but what is documented
  const pin = { 'C1.ANCHOR.CYCLE': 2, 'C2.TOTAL.GOAL': 1, 'C2.VO.OVERLAP': 6, 'C2.WAIT.NOHELP': 4, 'C3.DRIFT': 2, 'C3.KNOB.OFFSET': 1 }, srt = o => JSON.stringify(Object.keys(o).sort().map(k => [k, o[k]]));
  check('at load: the open problems are the ones before the ids, plus the one help.after adds (VO_11h is not where HelpAfter puts it: C3.KNOB.OFFSET) (pinned)', srt(byRule) === srt(pin), JSON.stringify(byRule));
  const PB = I.staticProblems(score, T0, before), fps = L => L.filter(p => p.rule !== 'C3.SCOPE').map(p => p.fp).sort();
  const scope = L => L.find(p => p.rule === 'C3.SCOPE').msg.slice(0, 24);
  check('  every problem as before; only C3.SCOPE counts one more (VO_01h is now in vo.unused): 174 → 175 of 592', JSON.stringify(fps(P0)) === JSON.stringify(fps(PB)) && scope(PB) === '174 of 592 elements are ' && scope(P0) === '175 of 592 elements are ', scope(PB) + ' → ' + scope(P0));
  const notes = P0.filter(p => /^C3\.(CONTRACT|BINDING)/.test(p.rule)).concat(stale(score, bind));
  check('  no C3.CONTRACT.RULE / ORPHAN and no C3.BINDING.STALE at load', !notes.length, notes.map(p => p.rule + ' ' + p.msg).join(' | '));
  const nIds = bind.binds.reduce((a, b) => a + Object.keys(b.ids || {}).length, 0);
  check('  the knobs govern the same elements by id as by key (81 stage ids; phase0 origin frozen for 4 stages)', JSON.stringify(gov) === JSON.stringify(P.governedBy(score, T0, bind0)) && nIds === 81 && Object.keys(bind.origins.phase0.ids).length === 4,
    Object.keys(gov).length + ' elements · ' + nIds + ' ids');
  check('  and measure the same values (drift by id = drift by key)', JSON.stringify(P.drift(score, T0, def, null, bind).rows) === JSON.stringify(P.drift(score, T0, def, null, bind0).rows));

  // the documented corrections: 10 voices Unreal no longer plays, 3 with no recording; vo.wired 68 → 56 (VO_01h never was in it)
  const keysIn = cid => (contract.entries.find(c => c.id === cid).ids || []).map(id => score.elements[id].key).sort();
  check('vo.unused = the 10 voices BP_Obra_SC no longer calls; vo.noasset = VO_12b, VO_17b, VO_21; vo.wired 56', JSON.stringify(keysIn('vo.unused')) === JSON.stringify(['VO_01d', 'VO_01h', 'VO_04b', 'VO_06a', 'VO_24', 'VO_34c', 'VO_35c', 'VO_36', 'VO_36c', 'VO_36d'])
    && JSON.stringify(keysIn('vo.noasset')) === JSON.stringify(['VO_12b', 'VO_17b', 'VO_21']) && keysIn('vo.wired').length === 56, keysIn('vo.wired').length + ' wired');
  { const id = idOf('VO_24'), n = X.move(score, id, .5, {}, kids), j = judgeOn(score, { type: 'move', ids: [id] }, n, contract, bind);
    check('  moving VO_24 says "Unreal no longer plays this voice" (a note), not "called by Unreal"', !j.card && j.items.some(i => i.rule === 'C3.VO.UNUSED' && i.sv === 'info' && /no longer plays/.test(i.body)) && !j.items.some(i => i.rule === 'C3.VO.WIRED' && i.keys.includes('VO_24')), rules(j));
    const d = clone(score); delete d.elements[id]; const jd = judgeOn(score, { type: 'delete', ids: [id], removed: { [id]: score.elements[id] } }, d, contract, bind), jb = judgeOn(score, { type: 'delete', ids: [id], removed: { [id]: score.elements[id] } }, d, before, bind0);
    const c3r = j => j.items.some(i => i.ly === 'C3' && (i.sv === 'block' || i.lock));
    check('  deleting VO_24: no Unreal item asks for a reason now (before: "the graph still calls it", a block); no orphan note', !c3r(jd) && jb.items.some(i => i.rule === 'C3.VO.WIRED' && i.sv === 'block') && !I.staticProblems(d, E.resolve(d, { persona: 'typical' }), contract).some(p => p.rule === 'C3.CONTRACT.ORPHAN'), rules(jd) + ' · before: ' + rules(jb)); }

  // rename T_IN, then move it: still the stage title and still the Partitura knob (by key and regex: silent after the rename)
  { const tin = idOf('T_IN', 'V2'), R1 = ren(score, tin, 'T_INTRO'), jr = judgeOn(score, { type: 'rename', ids: [tin] }, R1, contract, bind);
    const Pol = require(path.join(ROOT, 'web/editor-obra/app/js/policy.js')), d = Pol.decide({ type: 'rename', ids: [tin] }, jr.items, { label: 'Rename · T_IN', relocated: [], ripple: jr.ripple });
    check('rename T_IN → T_INTRO: judged, not quiet (applies with notes): the stage title and "Still governed by" its knob', d.mode === 'apply' && jr.items.some(i => i.rule === 'C3.TITLE.STAGE' && i.sv === 'info' && /Unreal still knows it as T_IN/.test(i.body)) && jr.items.some(i => i.rule === 'C3.PARTITURA' && /^Still governed by Etapa_Titulo/.test(i.body)), d.mode + ' · ' + rules(jr));
    const PR = I.staticProblems(R1, E.resolve(R1, { persona: 'typical' }), contract).filter(p => p.rule === 'C3.CONTRACT.RULE');
    check('  Problems: "T_INTRO was T_IN" (C3.CONTRACT.RULE, a note)', PR.length === 1 && PR[0].el === tin && PR[0].sv === 'info' && /^T_INTRO was T_IN/.test(PR[0].msg), PR.map(p => p.msg).join(' | '));
    const M2 = X.move(R1, tin, 2, {}, E.dependents(R1)), jm = judgeOn(R1, { type: 'move', ids: [tin] }, M2, contract, bind), j0 = judgeOn(R1, { type: 'move', ids: [tin] }, M2, contract0, bind0);
    check('  then +2 s: the card still has C3.TITLE.STAGE and the Partitura item', jm.items.some(i => i.rule === 'C3.TITLE.STAGE') && jm.items.some(i => i.rule === 'C3.PARTITURA' && /Etapa_TituloRevela/.test(i.body)), rules(jm));
    check('  (control: by key and regex the same move says nothing about Unreal)', !j0.items.some(i => i.ly === 'C3'), rules(j0));
    const T1 = E.resolve(R1, { persona: 'typical' }), bT = bind.binds.find(b => b.knob === 'Etapa_TituloRevelaIni'), m1 = P.measure(R1, T1, bind, bT, 2);
    check('  Partitura.measure finds T_INTRO by its id: same value, no stale note', m1 && m1.els[0] === tin && !m1.stale && m1.value === P.measure(score, T0, bind, bT, 2).value && !stale(R1, bind).length, m1 && m1.value); }

  // rename ENV_SWAP (the origin of every stage knob of V2): still measured from it
  { const env = idOf('ENV_SWAP', 'V2'), R2 = ren(score, env, 'ENV_CHANGE'), T2 = E.resolve(R2, { persona: 'typical' }), b = bind.binds.find(x => x.knob === 'Etapa_VeloAbreIni');
    const m = P.measure(R2, T2, bind, b, 2), m0 = P.measure(R2, T2, bind0, bind0.binds.find(x => x.knob === 'Etapa_VeloAbreIni'), 2);
    check('rename ENV_SWAP of V2: Etapa_VeloAbreIni (Loving) is still measured from it, same value (by key: lost)', m && m.origin === env && !m.stale && m.value === P.measure(score, T0, bind, b, 2).value && !m0, m && m.value); }

  // rename G_BELL, then a 60 s timeout: the drift with FW_Bell is still there
  { const id = idOf('G_BELL'), R3 = ren(score, id, 'G_RING'), n = clone(R3); n.elements[id].gate.fw = 60;
    const Tn = E.resolve(n, { persona: 'typical' }), d = I.staticProblems(n, Tn, contract).filter(p => p.rule === 'C3.DRIFT' && p.el === id), d0 = I.staticProblems(n, Tn, contract0).filter(p => p.rule === 'C3.DRIFT' && p.el === id);
    check('rename G_BELL → G_RING, timeout 60 s: C3.DRIFT still shows (FW_Bell 25 s)', d.length === 1 && /FW_Bell is 25 s/.test(d[0].msg), d.map(p => p.msg).join(''));
    check('  (control: by regex it disappears)', !d0.length);
    const jg = judgeOn(R3, { type: 'gate', ids: [id] }, n, contract, bind);
    check('  and the timeout change still asks for a written reason (FW_Bell is a locked final value)', jg.card && jg.reason, rules(jg)); }

  // rename VO_10: its recording stays VO_10 (sound, bind.asset); the card says Unreal plays it by its file name
  { const id = idOf('VO_10'), n = ren(score, id, 'VO_10_ALT'), j = judgeOn(score, { type: 'rename', ids: [id] }, n, contract, bind);
    check('rename VO_10 → VO_10_ALT: key and label change, sound stays VO_10 (the 3D and the inspector still find its recording)', n.elements[id].sound === 'VO_10' && n.elements[id].key === 'VO_10_ALT' && n.elements[id].label === 'VO_10_ALT' && M.soundId(n.elements[id]) === 'VO_10');
    check('  card (warn, one click, no reason): "Unreal plays this voice by its file name (VO_10)"', j.card && !j.reason && j.items.some(i => i.sv === 'warn' && i.rule === 'C3.VO.WIRED' && /by its file name \(VO_10\)/.test(i.body)), rules(j));
    const s3 = clone(score); s3.elements[id].bind = { asset: '/Game/SoulCharger/Obra/Audio/VO_10' }; const n3 = ren(s3, id, 'VO_10_ALT'), j3 = judgeOn(s3, { type: 'rename', ids: [id] }, n3, contract, bind);
    check('  with bind.asset (schema 3) the asset stays and it is a note: "Unreal still plays VO_10"', n3.elements[id].bind.asset === s3.elements[id].bind.asset && !j3.card && j3.items.some(i => i.sv === 'info' && /Unreal still plays VO_10\./.test(i.body)), rules(j3));
    const nw = clone(score); nw.elements.el_new_ren = Object.assign(clone(score.elements[id]), { key: 'FX_NEW_SOUND', type: 'sound', group: 'fx', sound: 'FX_NEW_SOUND', isNew: true });
    check('  a sound made in the editor (isNew) is still named by its key', ren(nw, 'el_new_ren', 'FX_WIND').elements.el_new_ren.sound === 'FX_WIND');
    const fx = Object.keys(score.elements).find(k => score.elements[k].type === 'sound' && score.elements[k].sound === score.elements[k].key && !score.elements[k].isNew);
    check('  an effect of the piece keeps its sound too (before: it followed the new name and lost its file)', ren(score, fx, 'FX_RENAMED').elements[fx].sound === score.elements[fx].sound, score.elements[fx].key); }

  // a copy is not in the ids. A copy of VO_10 (VO_10_2) still matches vo.wired's rule: a note that Unreal does not know it,
  // never a block. A copy of T_IN is T_IN_2 (keys stay unique): it does not match ^T_(IN|OUT)$, so there is nothing to say
  { const tb = Object.keys(score.beats).find(k => score.beats[k].key === '2.4'), r = X.planPaste(score, X.clipOf(score, [idOf('VO_10'), idOf('T_IN', 'V2')], E), { beat: tb, off: 3 }, E, { who: 'B' });
    const Pn = r.ok && I.staticProblems(r.next, E.resolve(r.next, { persona: 'typical' }), contract).filter(p => r.ids.includes(p.el) && /^C3/.test(p.rule));
    const vo = r.ok && r.ids.find(id => r.next.elements[id].type === 'vo');
    check('paste VO_10 and T_IN: VO_10_2 gets C3.CONTRACT.RULE "matches the rule of vo.wired but Unreal does not know it" (a note); T_IN_2 nothing; no block', r.ok && Pn.length === 1 && Pn[0].el === vo && Pn[0].rule === 'C3.CONTRACT.RULE' && Pn[0].sv === 'info' && /^VO_10_2 matches the rule of 'vo.wired' but Unreal does not know it/.test(Pn[0].msg)
      && !judgeOn(score, { type: 'paste', ids: r.ids }, r.next, contract, bind).items.some(i => i.sv === 'block'), r.ok ? Pn.map(p => p.msg).join(' | ') : r.why); }
  { const id = idOf('VO_10'), n = clone(score); delete n.elements[id];
    const o = I.staticProblems(n, E.resolve(n, { persona: 'typical' }), contract).filter(p => p.rule === 'C3.CONTRACT.ORPHAN');
    check('delete VO_10: C3.CONTRACT.ORPHAN "VO_10 is no longer in the score, but Unreal still has it" (a note, nothing to select)', o.length === 1 && o[0].sv === 'info' && !o[0].el && /^VO_10 is no longer in the score, but Unreal still has it \(vo\.wired\)/.test(o[0].msg), o.map(p => p.msg).join(' | '));
    const sv = stale(n, bind);
    check('  and the Partitura says the first voice of 1.R2 is gone (C3.BINDING.STALE on Alma_VozRetardo and Alma_TrasVoz, one note)', sv.length === 1 && sv[0].sv === 'info' && !sv[0].el && /^Alma_VozRetardo, Alma_TrasVoz \(Entering\): the first voice of moment 1\.R2 is no longer in the score; they are measured on nothing by name/.test(sv[0].msg), sv.map(p => p.msg).join(' | ')); }

  // a frozen bind that no longer holds: measured by key meanwhile, and said (C3.BINDING.STALE, a note)
  { const ch = Object.keys(score.elements).find(id => score.elements[id].key === 'CHARGE' && score.beats[score.elements[id].beat].key === '1.R6'), n = clone(score); delete n.elements[ch];
    const st = stale(n, bind);
    check('delete the CHARGE of 1.R6: C3.BINDING.STALE on Carga_Dur (Entering), a note', st.length === 1 && st[0].knob === 'Carga_Dur' && st[0].sv === 'info' && /^Carga_Dur \(Entering\): CHARGE is no longer in the score; it is measured on nothing/.test(st[0].msg), st.map(p => p.msg).join(' | ')); }
  { const vo10 = idOf('VO_10'), b = score.elements[vo10].beat, r = X.planPaste(score, X.clipOf(score, [vo10], E), { beat: b, off: 0 }, E, { who: 'B' });
    const Tn = r.ok && E.resolve(r.next, { persona: 'typical' }), first = r.ok && Tn.t[r.ids[0]][0] < Tn.t[vo10][0];
    const m = r.ok && P.measure(r.next, Tn, bind, bind.binds.find(x => x.knob === 'Alma_VozRetardo'), 0), st = r.ok ? stale(r.next, bind) : [];
    check('a copy of VO_10 before it in 1.R2: Alma_VozRetardo is measured on the new first voice, and one note says it for both knobs of VO_10', first && m && m.els[1] === r.ids[0] && m.stale && m.stale[0].why === 'order' && m.stale[0].key === 'VO_10'
      && st.length === 1 && /^Alma_VozRetardo, Alma_TrasVoz \(Entering\): VO_10 is no longer the first voice of moment 1\.R2; they are measured on VO_10_2/.test(st[0].msg), st.map(p => p.msg).join(' | ') || (r.ok ? 'not first' : r.why)); }

  // "Proceed anyway" on a rename covers that rename only (review of the chunk): accepting it never silences a delete, a move
  // or new words of the same wired voice
  { const Pol = require(path.join(ROOT, 'web/editor-obra/app/js/policy.js')), id = idOf('VO_10'), at = '2026-10-07T10:00:00.000Z';
    const R1 = ren(score, id, 'VO_10z'), jr = judgeOn(score, { type: 'rename', ids: [id] }, R1, contract, bind);
    R1.accepted = Pol.acceptRecords(R1.accepted, jr.items, { who: 'B', reason: '', at });
    const rec = R1.accepted.find(a => a.fp === 'C3.VO.WIRED|' + id);
    check('rename VO_10 → VO_10z, Proceed anyway: the record keeps its verb (rename)', !!rec && rec.verb === 'rename' && I.acceptedFor(R1.accepted, rec.fp, 'rename', 'warn') && !I.acceptedFor(R1.accepted, rec.fp, 'delete', 'block'), rec && rec.verb);
    const back = ren(R1, id, 'VO_10'), jbk = judgeOn(R1, { type: 'rename', ids: [id] }, back, contract, bind);
    check('  back to VO_10 (the name Unreal knows): a note, no card, and no C3.CONTRACT.RULE left', !jbk.card && jbk.items.some(i => i.rule === 'C3.VO.WIRED' && i.sv === 'info' && /^Back to VO_10, the name Unreal knows it by/.test(i.body))
      && !I.staticProblems(back, E.resolve(back, { persona: 'typical' }), contract).some(p => p.el === id && p.rule === 'C3.CONTRACT.RULE'), rules(jbk));
    const delOn = s => { const d = clone(s); delete d.elements[id]; return judgeOn(s, { type: 'delete', ids: [id], removed: { [id]: s.elements[id] } }, d, contract, bind); };
    const jd = delOn(R1);
    check('  then delete it: C3.VO.WIRED still blocks and asks for a written reason (before the fix: a note, deleted silently)', jd.items.some(i => i.rule === 'C3.VO.WIRED' && i.sv === 'block') && jd.reason, rules(jd));
    const b2 = score.elements[idOf('VO_11')].beat, mv = clone(R1); mv.elements[id].beat = b2; mv.elements[id].at = { ref: b2, edge: 'start', off: 1 };
    const jm = judgeOn(R1, { type: 'move', ids: [id] }, mv, contract, bind);
    check('  or move it to another moment: still the warning (a click)', jm.card && jm.items.some(i => i.rule === 'C3.VO.WIRED' && i.sv === 'warn' && /another moment/.test(i.body)), rules(jm));
    const tx = clone(R1); tx.elements[id].text += ' and more words'; const jt = judgeOn(R1, { type: 'text', ids: [id] }, tx, contract, bind);
    check('  or change its words: still the warning', jt.card && jt.items.some(i => i.rule === 'C3.VO.WIRED' && i.sv === 'warn'), rules(jt));
    // the same verb at the SAME place is still answered by its record (a note); at another place it is a new decision (design B §9):
    // accepted means this value. A second move to the same place, and a third to a different one
    mv.accepted = Pol.acceptRecords(mv.accepted, jm.items, { who: 'B', reason: 'first place', at });
    const b3 = score.elements[idOf('VO_13')].beat, mv2 = clone(mv); mv2.elements[id].beat = b3; mv2.elements[id].at = { ref: b3, edge: 'start', off: 1 };
    const mvAway = clone(mv); mvAway.elements[id].beat = b3; mvAway.elements[id].at = { ref: b3, edge: 'start', off: 1 };   // away from the accepted place, then back to it
    const jm1 = judgeOn(mvAway, { type: 'move', ids: [id] }, clone(mv), contract, bind);
    const jm2 = judgeOn(mv, { type: 'move', ids: [id] }, mv2, contract, bind), r2 = mv.accepted.find(a => a.fp === 'C3.VO.WIRED|' + id);
    check('  a move accepted, then the same place again: the Unreal item is a note, no card for it', jm1.items.some(i => i.rule === 'C3.VO.WIRED' && i.sv === 'info') && !jm1.items.some(i => i.rule === 'C3.VO.WIRED' && i.sv !== 'info'), rules(jm1));
    check('  then a move to ANOTHER place: the warning is back, and the card tells what was accepted before (and its reason)', jm2.items.some(i => i.rule === 'C3.VO.WIRED' && i.sv === 'warn' && i.before && i.before.reason === 'first place' && /s into moment /.test(i.before.words)) && JSON.stringify(I.verbsOf(r2)) === '["rename","rename","move"]', rules(jm2) + ' · ' + JSON.stringify(I.verbsOf(r2)));
    check('  and the delete after both still blocks', delOn(mv).items.some(i => i.rule === 'C3.VO.WIRED' && i.sv === 'block'));
    // a record written before the verb was kept: it never answers a rename nor turns a block into a note (it still answers a warning)
    const old = [{ fp: 'C3.VO.WIRED|' + id, sv: 'warn', ly: 'C3', rule: 'C3.VO.WIRED', msg: 'm', el: id, own: 'x', who: 'B', reason: 'old', at }];
    check('  a record with no verb: no rename, no block; a warning of another verb yes', !I.acceptedFor(old, old[0].fp, 'rename', 'warn') && !I.acceptedFor(old, old[0].fp, 'delete', 'block') && I.acceptedFor(old, old[0].fp, 'move', 'warn'));
    const s0 = clone(score); s0.accepted = old; const jd0 = delOn(s0);
    check('  so with that record the delete still blocks', jd0.items.some(i => i.rule === 'C3.VO.WIRED' && i.sv === 'block'), rules(jd0)); }

  // a voice Unreal no longer plays (vo.unused) or has no recording of (vo.noasset), renamed: still that, never "a wired voice
  // Unreal does not know" (review of the chunk)
  for (const [k, cid] of [['VO_24', 'vo.unused'], ['VO_12b', 'vo.noasset']]) {
    const id = idOf(k), n = ren(score, id, k + 'x'), Pn = I.staticProblems(n, E.resolve(n, { persona: 'typical' }), contract).filter(p => p.el === id && /^C3/.test(p.rule));
    const j = judgeOn(score, { type: 'rename', ids: [id] }, n, contract, bind);
    check(`rename ${k} → ${k}x: one note "${k}x was ${k}: still not in Unreal (${cid})", no "matches the rule of 'vo.wired'"; the rename itself says nothing`,
      Pn.length === 1 && Pn[0].rule === 'C3.CONTRACT.RULE' && Pn[0].sv === 'info' && new RegExp(`^${k}x was ${k}: still not in Unreal \\(${cid.replace('.', '\\.')}\\), preview only`).test(Pn[0].msg) && !j.items.some(i => i.ly === 'C3' && i.rule !== 'C3.PARTITURA'),
      Pn.map(p => p.msg).join(' | ') + ' · ' + rules(j));
  }
  check('Integrity.knownKey: the name Unreal knows (T_IN for every stage; null for an element no entry holds)', I.knownKey(idOf('T_IN', 'V2'), contract) === 'T_IN' && I.knownKey(idOf('VO_10'), contract) === 'VO_10'
    && I.knownKey(Object.keys(score.elements).find(id => !I.contractFor(id, score.elements[id], contract).length), contract) === null);
}

console.log('the APK baseline: schema 2 golden and schema 3 baseline (lote 5 step 4)');
if (!(score.schema === 2 && score.golden)) console.log('  info  the score under test is not a schema-2 score with its golden: these cases need one, skipped');
else {
  const s3 = schema3Copy(score), T3 = E.resolve(s3, { persona: 'typical' }), base3 = s3.baseline, kids3 = E.dependents(s3);
  const keys = set => [...set].map(id => score.elements[id].key).sort().join(', ');
  const sameSet = (a, b) => JSON.stringify([...a].sort()) === JSON.stringify([...b].sort());
  const wired = Object.keys(score.elements).filter(id => I.contractFor(id, score.elements[id], contract).some(c => c.kind !== 'not-in-unreal'));
  // which reference a score carries
  check('baselineOf: the baseline of schema 3, the golden of schema 2, the baseline when both, nothing when none',
    I.baselineOf(score) === score.golden && I.baselineOf(s3) === s3.baseline && I.baselineOf(Object.assign({}, s3, { golden: score.golden })) === s3.baseline && I.baselineOf({ elements: {} }) === null && I.baselineOf({ baseline: { note: 'x' } }) === null);
  check('relOf: the same [start in its moment, length] from the golden (derived) and from the baseline (stored)', wired.every(id => { const a = I.relOf(score, score.golden, id), b = I.relOf(s3, base3, id); return a && b && Math.abs(a[0] - b[0]) < 1e-9 && Math.abs(a[1] - b[1]) < 1e-9; }), wired.length + ' wired elements');
  // at load nothing differs, with the reference given or left out (the score's own)
  check('no divergence at load on schema 3, with the baseline given or the score\'s own', I.divergent(s3, T3, contract, gov, base3).size === 0 && I.divergent(s3, T3, contract, gov).size === 0 && I.divergent(score, T0, contract, gov).size === 0);
  check('  null says there is no reference: nothing to compare', I.divergent(s3, T3, contract, gov, null).size === 0 && I.divergent(s3, T3, contract, gov, {}).size === 0);
  // a battery: every element Unreal knows moved by 0.4 s and by 5 s: golden and baseline flag exactly the same ones
  { let same = 0, flagged = 0, diff = [];
    for (const dt of [.4, 5]) for (const id of wired) {
      const n2 = X.move(score, id, dt, {}, kids), n3 = X.move(s3, id, dt, {}, kids3), a = I.divergent(n2, E.resolve(n2, { persona: 'typical' }), contract, {}, n2.golden), b = I.divergent(n3, E.resolve(n3, { persona: 'typical' }), contract, {}, n3.baseline);
      if (sameSet(a, b)) same++; else diff.push(score.elements[id].key + ' ' + dt); flagged += a.size;
    }
    check(`${2 * wired.length} moves of what Unreal knows (+0.4 s, +5 s): the golden of schema 2 and the baseline of schema 3 flag the same set each time`, !diff.length && flagged > 20, `${same} equal · ${flagged} flagged in all${diff.length ? ' · DIFFER: ' + diff.slice(0, 5).join(', ') : ''}`); }
  // the Partitura's elements are judged by C3.PARTITURA, never twice here
  { const vo5 = idOf('VO_05'), n = X.move(score, vo5, 5, {}, kids), Tn = E.resolve(n, { persona: 'typical' });
    check('VO_05 +5 s is ≠ APK; if a Partitura knob governed it, it is not (C3.PARTITURA says whether the score and Unreal agree)', I.divergent(n, Tn, contract, {}, score.golden).has(vo5) && !I.divergent(n, Tn, contract, { [vo5]: [{ knob: 'Alma_VozRetardo', stage: null }] }, score.golden).has(vo5)); }
  { const both = Object.keys(gov).filter(id => wired.includes(id)); let hidden = 0, shown = 0;
    for (const id of both) { const n = X.move(score, id, 3, {}, kids), Tn = E.resolve(n, { persona: 'typical' }); if (I.divergent(n, Tn, contract, {}, score.golden).has(id)) shown++; if (I.divergent(n, Tn, contract, gov, score.golden).has(id)) hidden++; }
    check(`the ${both.length} elements that are both wired and governed by a knob: moved 3 s each, ≠ APK counts none of them (it counted ${shown} before the Partitura took them)`, both.length > 20 && shown > 0 && hidden === 0, `${shown} flagged without gov · ${hidden} with it`); }

  // lote 3's claim: after "Real voice lengths" (the recordings replace the estimates) nothing is ≠ APK, because what follows each voice
  // moves with it in the APK too and the baseline moves by exactly that. Fake recordings: 24 wired voices, ±0.5…1.1 s
  { const vos = wired.filter(id => score.elements[id].type === 'vo' && !score.elements[id].help && score.elements[id].dur && score.elements[id].dur.value > 1.5).slice(0, 24);
    const real = (s, i) => { for (const [k, id] of vos.entries()) s.elements[id].dur = { mode: 'audio', value: +(score.elements[id].dur.value + (k % 2 ? .5 + (k % 3) * .3 : -.5)).toFixed(4) }; return s; };
    const n2 = real(clone(score)), n3 = real(clone(s3)), T1 = E.resolve(n2, { persona: 'typical' }), rec = { at: '2026-10-07T12:00:00Z', by: 'B', ids: vos, src: 'final mix' };
    const pre = I.divergent(n2, T1, contract, gov, score.golden), pre3 = I.divergent(n3, T1, contract, gov, base3);
    check(`before the shift: the ${vos.length} recordings make ≠ APK appear (the control: without the baseline moving, the claim would not need shiftBaseline)`, pre.size > 10 && sameSet(pre, pre3), `${pre.size} elements`);
    const g2 = X.shiftGolden(score.golden, T0, T1, rec), post2 = I.divergent(n2, T1, contract, gov, g2), post2b = I.divergent(n2, T1, contract, {}, g2);
    check('schema 2 · after the real lengths shift golden.times: ≠ APK = 0 (with the knobs and without), the total and the voices record moved', post2.size === 0 && post2b.size === 0 && Math.abs(g2.total - T1.total) < 1e-3 && g2.voices.length === 1, `${pre.size} → 0 · total ${I.fmt(T0.total)} → ${I.fmt(T1.total)}`);
    const b3 = X.shiftBaseline(base3, { score: s3, sched: T3 }, { score: n3, sched: T1 }, null, Object.assign({ op: 'voices' }, rec)), post3 = I.divergent(n3, T1, contract, gov, b3), post3b = I.divergent(n3, T1, contract, {}, b3);
    check('schema 3 · after the real lengths shift score.baseline: ≠ APK = 0 (with the knobs and without), the total and the log moved', post3.size === 0 && post3b.size === 0 && Math.abs(b3.total - T1.total) < 1e-3 && b3.log[b3.log.length - 1].op === 'voices', `${pre3.size} → 0`);
    n3.baseline = b3;
    check('  and with the shifted baseline inside the score, the score\'s own is used: 0 (what compute() does)', I.divergent(n3, T1, contract, gov).size === 0 && I.divergent(n3, T1, contract, gov, I.baselineOf(n3)).size === 0);
    // only some of them matched (a subset of ids): what moved and was not matched is still ≠ APK
    const half = vos.slice(0, 12), bh = X.shiftBaseline(base3, { score: s3, sched: T3 }, { score: n3, sched: T1 }, half, null), n3h = Object.assign(clone(n3), { baseline: bh }), ph = I.divergent(n3h, T1, contract, gov, bh);
    check('  matching only 12 of the 24 voices: those 12 are not ≠ APK, the others that moved still are', half.every(id => !ph.has(id)) && ph.size > 0 && ph.size < pre3.size, `${ph.size} of ${pre3.size} left`); }
}
console.log('SHARE / DON\'T SHARE in the editor (lote 5 step 6): the rules that depend on the option judge every option');
if (score.schema !== 2) console.log('  info  the score under test is not schema 2: the branches are checked on the migrated fixture, skipped');
else {
  const m = X.migrate3(score, E, contract, { at: '2026-10-07T12:00:00Z', who: 'B' });   // the migrated fixture: the owner's button, in memory
  const n3 = m.next, K = k => Object.keys(n3.elements).find(i => n3.elements[i].key === k), kids3 = E.dependents(n3);
  const run3 = s => ({ T: E.resolve(s, { persona: 'typical' }), A: E.altRuns(s) });
  const probs = s => { const r = run3(s); return I.staticProblems(s, r.T, contract, r.A); };
  const P3 = probs(n3), PD = I.staticProblems(n3, E.resolve(n3, { persona: 'typical' }), contract);
  const gov3 = P.governedBy(n3, E.resolve(n3, { persona: 'typical' }), bind);
  const judge3 = (prev, op, next) => { const a = run3(prev), b = run3(next), r = I.opItems(Object.assign({ prevScore: prev }, op), next, { problems: I.staticProblems(prev, a.T, contract, a.A) }, { problems: I.staticProblems(next, b.T, contract, b.A) }, contract, E, { gov: gov3 });
    return Object.assign(r, { card: r.items.some(i => i.sv !== 'info'), reason: r.items.some(i => i.sv === 'block' || i.lock) }); };
  const rule = (L, r) => L.filter(p => p.rule === r), both = (L, a, b) => L.filter(p => p.rule === 'C2.VO.OVERLAP' && p.msg.includes(a) && p.msg.includes(b));
  const v35b = K('VO_35b'), v35c = K('VO_35c'), v37 = K('VO_37'), fxTitle = Object.keys(n3.elements).find(i => n3.elements[i].key === 'FX_TITLE' && n3.beats[n3.elements[i].beat].key === '9.7'), alts = E.altRuns(n3);
  const T0s = E.resolve(n3, { persona: 'typical' });

  // the second option is its own run
  check('altRuns: one run for the option that is not the default (DON\'T SHARE), 3.25 s shorter than SHARE', alts.length === 1 && alts[0].k === 'share=no' && alts[0].sel.share === 'no' && Math.abs((T0s.total - alts[0].sched.total) - 3.25) < 1e-3, alts.map(a => a.k + ' ' + a.sched.total.toFixed(2)).join(', ') + ' vs ' + T0s.total.toFixed(2));
  check('  a schema 2 score has none', E.altRuns(score).length === 0);
  // the old rule's false positive goes away: the SHARE side and the DON'T SHARE side of 9.7 are never at once
  { const s2 = I.staticProblems(score, T0, contract);
    check('schema 2 (no branches): VO_35c and VO_37 are reported as sounding together, the only way it could read them', both(s2, 'VO_35c', 'VO_37').length === 1, both(s2, 'VO_35c', 'VO_37').map(p => p.msg).join(' | '));
    check('schema 3: VO_35b / VO_35c / VO_37 are never reported as overlapping, in any run (elements of different sides never overlap)', !both(P3, 'VO_35b', 'VO_35c').length && !both(P3, 'VO_35c', 'VO_37').length && !both(P3, 'VO_35b', 'VO_37').length, P3.filter(p => p.rule === 'C2.VO.OVERLAP').length + ' overlaps left'); }
  check('  even placed on top of each other: VO_35b and VO_35c start together (and VO_35c moved 3 s into VO_35b) still no overlap row', (() => { const n = X.move(n3, v35c, 3, { alone: true }, kids3), Pn = probs(n); return !both(Pn, 'VO_35b', 'VO_35c').length; })());
  { // the six real overlaps of the piece are in every run: one row each, with the fingerprint they always had and no side named
    const was = rule(PD, 'C2.VO.OVERLAP').map(p => p.fp).sort(), now = rule(P3, 'C2.VO.OVERLAP').map(p => p.fp).sort();
    check('the voice overlaps that exist in every run are one row each, with the same fingerprint as without the other run and no side in the message', JSON.stringify(was) === JSON.stringify(now) && rule(P3, 'C2.VO.OVERLAP').every(p => !/ in (SHARE|DON'T SHARE)/.test(p.msg)), `${now.length} rows`);
    check('  and the two anchor loops of the piece (2.R4, 5.R4) too: two rows, unchanged', rule(P3, 'C1.ANCHOR.CYCLE').length === 2 && JSON.stringify(rule(P3, 'C1.ANCHOR.CYCLE').map(p => p.fp).sort()) === JSON.stringify(rule(PD, 'C1.ANCHOR.CYCLE').map(p => p.fp).sort())); }
  // an overlap that exists in one side says which
  { const n = X.move(n3, v35c, 2, { alone: true }, kids3), Pn = probs(n), r = both(Pn, 'VO_35c', 'VO_37');
    check('an overlap in DON\'T SHARE only (VO_35c moved 2 s later, VO_37 stays) says "in DON\'T SHARE", names the length and has a fingerprint that says the side', r.length === 1 && / for 2\.0 s in DON'T SHARE\.$/.test(r[0].msg) && /\|share=no$/.test(r[0].fp), r.map(p => p.msg + ' · ' + p.fp).join(' | '));
    const Ps = Pn.filter(p => p.rule === 'C2.VO.OVERLAP' && !PD.some(q => q.fp === p.fp));
    check('  and only that one is new (nothing in SHARE)', Ps.length === 1, Ps.map(p => p.msg).join(' | '));
    const j = judge3(n3, { type: 'move', ids: [v35c], alone: true }, n);
    check('  the edit opens a card with the new problem and the side in it (VO_35c is not wired: no reason asked)', j.card && j.items.some(i => i.rule === 'C2.VO.OVERLAP' && / in DON'T SHARE\.$/.test(i.body)) && !j.reason, j.items.map(i => i.sv + ' ' + i.rule).join(', ')); }
  { const n = X.move(n3, v35b, 2, { alone: true }, kids3), Pn = probs(n), r = both(Pn, 'VO_35b', 'VO_37');
    check('an overlap in SHARE only (VO_35b moved 2 s later, VO_37 stays) says "in SHARE" and keeps the fingerprint it always has', r.length === 1 && / in SHARE\.$/.test(r[0].msg) && r[0].fp === 'C2.VO.OVERLAP|' + v37 + '|VO_35b', r.map(p => p.msg + ' · ' + p.fp).join(' | ')); }
  // Alma early and a help line that comes too late: judged in each side, on small scores of their own
  { const at = (ref, edge, off) => ({ ref, edge, off: off || 0 }), bt = key => ({ key, title: key, desc: '', act: 0, at: null });
    const el = (key, beat, over) => Object.assign({ key, type: 'sound', group: 'fx', beat, lane: 'l', at: at(beat, 'start'), end: null, dur: { mode: 'fixed', value: 1 }, gate: null, help: null }, over);
    const mini = els => ({ schema: 3, rev: 1, acts: [{ id: 'a', name: 'A', beats: ['b1'] }], beats: { b1: bt('1') }, groups: [], lanes: {}, elements: els, markers: {}, notes: {},
      branches: { share: { name: 'Share', options: { yes: { label: 'SHARE' }, no: { label: "DON'T SHARE" } }, default: 'yes' } } });
    const side = (s, r) => { const a = E.altRuns(s); return I.staticProblems(s, E.resolve(s, { persona: 'typical' }), null, a).filter(p => p.rule === r); };
    const vo = (key, over) => el(key, 'b1', Object.assign({ type: 'vo', group: 'vo', dur: { mode: 'fixed', value: 1.5 } }, over));
    const alma = el('ALMA_IN', 'b1', { at: at('b1', 'start', 2) });
    const e1 = side(mini({ ALMA: alma, VO_A: vo('VO_A', { branch: { on: 'share', value: 'no' } }), VO_B: vo('VO_B', { at: at('b1', 'start', 3), branch: { on: 'share', value: 'yes' } }) }), 'C2.ALMA.EARLY');
    check("Alma early in one side only (the voice of DON'T SHARE starts before she appears): one row, in DON'T SHARE, and the SHARE voice (after her) is fine", e1.length === 1 && e1[0].el === 'VO_A' && / in DON'T SHARE\.$/.test(e1[0].msg) && /\|share=no$/.test(e1[0].fp), e1.map(p => p.msg + ' · ' + p.fp).join(' | '));
    const e2 = side(mini({ ALMA: alma, VO_A: vo('VO_A') }), 'C2.ALMA.EARLY');
    check('  a voice of both sides that starts before her is one row for both: no side in the message, the fingerprint it always had', e2.length === 1 && !/ in (SHARE|DON'T SHARE)/.test(e2[0].msg) && e2[0].fp === 'C2.ALMA.EARLY|VO_A|2.0', e2.map(p => p.msg + ' · ' + p.fp).join(' | '));
    const w = el('G', 'b1', { type: 'wait', group: 'int', gate: { expected: 5, fw: 10 }, dur: { mode: 'elastic', value: 5 } });
    const h1 = side(mini({ G: w, H_A: vo('H_A', { help: 'G', at: at('G', 'start', 12), branch: { on: 'share', value: 'no' } }), H_B: vo('H_B', { help: 'G', at: at('G', 'start', 6), branch: { on: 'share', value: 'yes' } }) }), 'C2.HELP.LATE');
    check("a help line that comes after the timeout only in DON'T SHARE: one row, in DON'T SHARE (the SHARE one is on time)", h1.length === 1 && h1[0].el === 'H_A' && / in DON'T SHARE: it never plays\.$/.test(h1[0].msg) && /\|share=no$/.test(h1[0].fp), h1.map(p => p.msg + ' · ' + p.fp).join(' | ')); }

  // the anchor that crosses to the other side
  { const r = X.reanchor(n3, fxTitle, { ref: v35b, edge: 'start' }, E), n = r.next, Pn = probs(n), c = rule(Pn, 'C1.BRANCH.ANCHOR');
    check('anchoring a common element (FX_TITLE) to VO_35b, which only plays in SHARE: the anchor itself is allowed (nothing moves in SHARE)', r.ok);
    check('  the new problem is C1.BRANCH.ANCHOR, a block, in DON\'T SHARE, and it names what to do', c.length === 1 && c[0].sv === 'block' && c[0].el === fxTitle && /FX_TITLE is anchored to VO_35b, which is not there in DON'T SHARE/.test(c[0].msg) && /Anchor in DON'T SHARE/.test(c[0].msg) && /\|share=no$/.test(c[0].fp), c.map(p => p.msg).join(' | '));
    const j = judge3(n3, { type: 'reanchor', ids: [fxTitle] }, n);
    check('  the edit opens a card that needs a written reason (a block), with the problem and its fingerprint', j.card && j.reason && j.items.some(i => i.rule === 'C1.BRANCH.ANCHOR' && i.sv === 'block' && i.fp === c[0].fp), j.items.map(i => i.sv + ' ' + i.rule).join(', '));
    check('  VO_37 anchored to the same VO_35b does not complain: it has its own anchor in DON\'T SHARE', !c.some(p => p.el === v37) && !rule(P3, 'C1.BRANCH.ANCHOR').length);
    // the way out: give it an anchor of its own in DON'T SHARE (it keeps its time there)
    const ra = X.reanchorAlt(n, fxTitle, 'share=no', { ref: v35c, edge: 'start' }, E), Pa = ra.ok && probs(ra.next);
    check('  "Anchor in DON\'T SHARE" (VO_35c) clears it: no C1.BRANCH.ANCHOR left, FX_TITLE keeps its time in both sides', ra.ok && !rule(Pa, 'C1.BRANCH.ANCHOR').length && Math.abs(E.resolve(ra.next, { persona: 'typical', branch: { share: 'no' } }).t[fxTitle][0] - E.resolve(n3, { persona: 'typical', branch: { share: 'no' } }).t[fxTitle][0]) < 1e-3, ra.why || '');
    // accepting it records the fingerprint of THIS problem (the side is in it), so the row reads accepted
    const acc = P_.acceptRecords(n.accepted, j.items, { who: 'B', reason: 'on purpose', at: '2026-10-07T12:00:00Z' }), n2 = Object.assign(clone(n), { accepted: acc }), Pq = rule(probs(n2), 'C1.BRANCH.ANCHOR');
    check('  "Proceed anyway" records exactly that fingerprint: the row reads accepted afterwards, and a different side would not', acc.some(a => a.fp === I.fpParts(c[0].fp).base && a.value === I.fpParts(c[0].fp).param) && Pq.length === 1 && Pq[0].st === 'accepted', acc.map(a => a.fp + ' @ ' + a.value).join(' | ')); }
  // an end that crosses says so in its own words
  { const n = clone(n3); n.elements[fxTitle].end = { ref: v35b, edge: 'end', off: 0 }; const c = rule(probs(n), 'C1.BRANCH.ANCHOR').filter(p => p.el === fxTitle);
    check('a clip that LASTS UNTIL something of the other side says so ("lasts until"), apart from its start', c.length === 1 && /FX_TITLE lasts until VO_35b/.test(c[0].msg) && /Lasts until in DON'T SHARE/.test(c[0].msg) && /\|share=no\|end$/.test(c[0].fp), c.map(p => p.msg).join(' | ')); }

  // C1.BRANCH.FIELD: what an edit can leave behind
  { const n = clone(n3); n.elements[K('VO_36c')].branch = { on: 'share', value: 'maybe' }; n.elements[v37].alt['nope=x'] = { at: { ref: v35c, edge: 'end', off: 0 } };
    const f = rule(probs(n), 'C1.BRANCH.FIELD');
    check('C1.BRANCH.FIELD (block): an element in a side that does not exist, an alternative of an option that does not exist', f.length === 2 && f.every(p => p.sv === 'block') && f.some(p => /VO_36c belongs to a branch option/.test(p.msg)) && f.some(p => /nope=x/.test(p.msg)), f.map(p => p.msg).join(' | '));
    check('  a good schema 3 has none, and schema 2 never asks', !rule(P3, 'C1.BRANCH.FIELD').length && !rule(I.staticProblems(score, T0, contract), 'C1.BRANCH.FIELD').length); }

  // the "branch" edit: which side plays an element
  { const r = X.setBranch(n3, [v35b], 'share', null), j = r.ok && judge3(n3, { type: 'branch', ids: [v35b] }, r.next);
    check('VO_35b to both sides: VO_35b and VO_35c would now sound together in DON\'T SHARE: a card with the side in it, and VO_35b wired says Unreal does not know the branch', r.ok && j.card && j.items.some(i => i.rule === 'C2.VO.OVERLAP' && / in DON'T SHARE\.$/.test(i.body)) && j.items.some(i => i.rule === 'C3.VO.WIRED' && /does not know about the branch/.test(i.body)), j.items.map(i => i.sv + ' ' + i.rule + ': ' + i.body.slice(0, 60)).join(' | '));
    const su = K('SOUL_UP'), r2 = X.setBranch(n3, [su], 'share', 'no'), j2 = r2.ok && judge3(n3, { type: 'branch', ids: [su] }, r2.next), c2 = r2.ok ? rule(probs(r2.next), 'C1.BRANCH.ANCHOR') : [];
    check('SOUL_UP (the spine of 9.7) to DON\'T SHARE only: everything common that hangs from it is left without an anchor in SHARE: blocks, and the card needs a reason', r2.ok && c2.length > 3 && c2.every(p => /in SHARE\./.test(p.msg) || /for SHARE/.test(p.msg)) && j2.reason, c2.length + ' blocked · ' + (c2[0] || {}).msg); }

  // an edit that changes the time only in the other side is still an edit (effect measures every side)
  { const r = X.move(n3, v37, 1, { ks: ['share=no'] }, kids3), ef = I.effect(n3, r, E), Td = E.resolve(r, { persona: 'typical' }), Tn = E.resolve(r, { persona: 'typical', branch: { share: 'no' } }), Tn0 = E.resolve(n3, { persona: 'typical', branch: { share: 'no' } });
    check('moving VO_37 1 s in DON\'T SHARE (its own anchor): SHARE does not move, DON\'T SHARE does, and the effect says VO_37 changed', Math.abs(Td.t[v37][0] - T0s.t[v37][0]) < 1e-6 && Math.abs(Tn.t[v37][0] - Tn0.t[v37][0] - 1) < 1e-6 && ef.changed.includes(v37), 'changed: ' + ef.changed.length);
    const w = X.move(n3, v37, 1, {}, kids3), ew = I.effect(n3, w, E);
    check('  the same move on the primary anchor changes SHARE (and not DON\'T SHARE): effect says changed too, as it always did', ew.changed.includes(v37) && Math.abs(E.resolve(w, { persona: 'typical', branch: { share: 'no' } }).t[v37][0] - Tn0.t[v37][0]) < 1e-6); }
  // the ripple line names the total of the other side when it moved differently from the one shown (review of step 6)
  { const r = X.move(n3, v37, 60, { ks: ['share=no'] }, kids3), ef = I.effect(n3, r, E), line = I.rippleLine(ef), dn = E.resolve(n3, { persona: 'typical', branch: { share: 'no' } });
    check('moving VO_37 60 s later in DON\'T SHARE (it then ends after everything else there): the effect carries the total of that side, and the line says "DON\'T SHARE total" (SHARE\'s did not move)', ef.sides.length === 1 && ef.sides[0].k === 'share=no' && ef.sides[0].label === "DON'T SHARE" && Math.abs(ef.sides[0].total1 - ef.sides[0].total0 - (dn.t[v37][1] + 60 - dn.total)) < 1e-3 && /^DON'T SHARE total 17:\d\d \(\+13\.4 s\)$/.test(line), line);
    const w = X.move(n3, v37, 60, {}, kids3), lw = I.rippleLine(I.effect(n3, w, E));
    check('  the same on the primary anchor moves SHARE\'s total and DON\'T SHARE\'s does not: the line does not name the side', !/DON'T SHARE total/.test(lw) && /total /.test(lw), lw);
    const b12 = Object.keys(n3.beats).find(b => n3.beats[b].key === '1.2'), pp = X.planPaste(n3, X.clipOf(n3, [v37], E), { beat: b12, off: 1 }, E, { who: 'B', addLane: (n, g) => { const gg = n.groups.find(x => x.id === g); const id = 'ln_' + g + '_x'; n.lanes[id] = { name: 'x', group: g }; gg.lanes.push(id); return id; } }), lp = I.rippleLine(I.effect(n3, pp.next, E));
    check('  a paste that grows both sides by the same amount says it once (the side is not repeated)', pp.ok && /total /.test(lp) && !/DON'T SHARE total/.test(lp), lp);
    check('  a score with no branches has no sides, and the line is what it always was', I.effect(score, X.move(score, idOf('VO_10'), 2, {}, E.dependents(score)), E).sides.length === 0); }
  check('the typical numbers are the same with or without the other run (the default run decides what is written)', Math.abs(P3.find(p => p.rule === 'C2.TOTAL.GOAL').fp.length - PD.find(p => p.rule === 'C2.TOTAL.GOAL').fp.length) === 0 && probs(n3).length === P3.length);
}

console.log(fails ? `\n${fails} FAILED` : '\nall ok');
process.exit(fails ? 1 : 0);
