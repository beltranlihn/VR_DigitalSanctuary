// policy_test.mjs — what an edit does with the items integrity gives it (web/editor-obra/app/js/policy.js; lote 5 design B
// §8.1 and §11 step 2, audit D12): quiet, apply or the impact card, and what "Proceed anyway" writes in score.accepted.
// Everything runs in plain Node (no window). The cases of integrity_test are replayed through Policy.decide AND through a
// frozen copy of the branches commit() had before the extraction (app.js, 2026-10-05): both must give the same decision, so
// the extraction changed nothing. Same for the acceptance writer.
// It runs on the frozen fixture tools/score/fixtures/f0-score.json (so real edits of the piece never break it); --live runs it
// on obra/score/score.json (see tools/score/test_score.mjs). Exit 1 if any case fails.
//   node tools/score/policy_test.mjs [--live]
import fs from 'fs';
import path from 'path';
import { createRequire } from 'module';
import { fileURLToPath } from 'url';
import { testScore } from './test_score.mjs';
const require = createRequire(import.meta.url);
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const js = f => require(path.join(ROOT, 'web/editor-obra/app/js', f));
const E = js('engine.js'), X = js('edits.js'), P = js('partitura.js'), I = js('integrity.js'), Pol = js('policy.js');
const rd = p => JSON.parse(fs.readFileSync(path.join(ROOT, p), 'utf8'));
const { score, name: SRC } = testScore(); console.log('on the ' + SRC);
const before = JSON.stringify(score);
const contract = rd('obra/unreal/contract.json'), bind = rd('obra/unreal/partitura_binding.json');
const T0 = E.resolve(score, { persona: 'typical' }), P0 = I.staticProblems(score, T0, contract), gov = P.governedBy(score, T0, bind);
const kids = E.dependents(score), clone = o => JSON.parse(JSON.stringify(o));
const idOf = (k, b) => Object.keys(score.elements).find(id => score.elements[id].key === k && (!b || score.beats[score.elements[id].beat].key === b));
let fails = 0;
const check = (n, ok, info) => { console.log((ok ? '  ok   ' : '  FAIL ') + n + (info ? '  · ' + info : '')); if (!ok) fails++; };
// what commit() computes before it decides (relocations are the app's: none here, they are tested apart below)
const itemsOf = (op, next) => { const T1 = E.resolve(next, { persona: 'typical' }), P1 = I.staticProblems(next, T1, contract);
  return I.opItems(Object.assign({ prevScore: score }, op), next, { problems: P0 }, { problems: P1 }, contract, E, { gov }); };

/* ---------- frozen: commit()'s branches and its acceptance writer as they were in app.js before the extraction ---------- */
const TODAY_QUIET = new Set(['import', 'sync', 'propose', 'sent', 'add', 'paste', 'lane-new', 'lane-rename', 'lane-delete', 'lane-change', 'note', 'marker', 'audio', 'rename', 'reopen']);
// lote 5 design A §7.3: rename left the quiet set on purpose (renaming what Unreal has is judged like any edit)
const STILL_QUIET = new Set([...TODAY_QUIET].filter(t => t !== 'rename'));
function today(label, op, items, relocated, ripple) {
  if (TODAY_QUIET.has(op.type)) { const nw = items.filter(i => i.sv !== 'info' && i.ly !== 'C3').length; return { mode: 'quiet', toast: nw && !relocated.length && !ripple ? `${label} · ${nw} new warning${nw > 1 ? 's' : ''} in Problems (F8)` : null }; }
  const shown = items.filter(i => i.sv !== 'info');
  if (!shown.length) return { mode: 'apply', toast: null };
  // the card (ui.js impactCard): a reason when something blocks or a final value is locked; "Proceed anyway" when it breaks
  return { mode: 'card', toast: null, needReason: items.some(i => i.sv === 'block' || i.lock), breaks: items.some(i => i.sv === 'block' || i.sv === 'warn') };
}
function todayAccept(n, items, who, reason, at) {
  n.accepted = n.accepted || [];
  for (const it of items) if (it.sv === 'block' || it.sv === 'warn') for (const el of (it.ids || [it.el])) {
    const fp = it.rule + '|' + (el || ''), ev = { who, reason, at, msg: it.title + ': ' + it.body };
    const a = n.accepted.find(x => x.fp === fp);
    if (a) { a.history = (a.history || [{ who: a.who, reason: a.reason, at: a.at, msg: a.msg }]).concat(ev); Object.assign(a, { who, reason, at }); }
    else n.accepted.push({ fp, sv: it.sv, ly: it.ly, rule: it.rule, msg: it.title + ': ' + it.body, el, own: it.ev, who, reason, at });
  }
  return n.accepted;
}
const same = (label, op, items, relocated, ripple) => {
  const a = today(label, op, items, relocated, ripple), b = Pol.decide(op, items, { label, relocated, ripple });
  return a.mode === b.mode && a.toast === b.toast && (a.mode !== 'card' || (a.needReason === b.needReason && a.breaks === b.breaks))
    && JSON.stringify(b.shown) === JSON.stringify(items.filter(i => i.sv !== 'info'));
};

console.log('plain Node');
check('policy.js and integrity.js load without a window', typeof globalThis.window === 'undefined' && typeof Pol.decide === 'function' && typeof Pol.acceptRecords === 'function' && typeof I.opItems === 'function');

console.log('the same decision as before the extraction (replay)');
let n592 = 0, diff = 0, modes = {};
for (const id of Object.keys(score.elements)) {
  const r = itemsOf({ type: 'move', ids: [id] }, X.move(score, id, .1, {}, kids)), op = { type: 'move', ids: [id] };
  n592++; const d = Pol.decide(op, r.items, { label: 'Move', relocated: [], ripple: r.ripple }); modes[d.mode] = (modes[d.mode] || 0) + 1;
  if (!same('Move', op, r.items, [], r.ripple)) diff++;
  // the same items under every quiet verb, with and without a ripple or a relocation
  for (const t of STILL_QUIET) for (const [rel, rip] of [[[], ''], [[], r.ripple], [[{ id }], '']]) if (!same('Edit', { type: t, ids: [id] }, r.items, rel, rip)) diff++;
}
check(`nudge every element +0.1 s: Policy.decide = today's commit() for all ${n592} (and under the ${STILL_QUIET.size} quiet verbs)`, diff === 0, `${diff} differ · ${JSON.stringify(modes)}`);

const S = {};   // the cases of integrity_test, plus the ones of this step (§11 step 2), each with its items
{ const id = idOf('PASO', '2.7a'), n = clone(score); n.elements[id].dur.value = 9.5; S.trimPaso = [{ type: 'trim', ids: [id] }, n]; }
{ const id = idOf('CANDS_IN'), n = clone(score); n.elements[id].dur = { mode: 'fixed', value: n.elements[id].dur.value + 3 }; S.trimCands = [{ type: 'trim', ids: [id] }, n]; }
{ const id = idOf('VO_10'), n = clone(score); n.elements[id].text += ' and a much longer sentence that changes the length of the voice'; S.textVo10 = [{ type: 'text', ids: [id] }, n]; }
{ const id = idOf('DISCLAIMER'), n = clone(score); n.elements[id].dur.value = 320; S.disclaimer = [{ type: 'trim', ids: [id] }, n]; }
{ const id = idOf('VO_10'); S.vo10keep = [{ type: 'move', ids: [id] }, X.move(score, id, .3, {}, kids)]; }
{ const id = idOf('VO_13'); S.vo13order = [{ type: 'move', ids: [id] }, X.move(score, id, 5, { alone: true }, kids)]; }
{ const id = idOf('VO_10'), b2 = score.elements[idOf('VO_11')].beat, n = clone(score);
  n.elements[id].beat = b2; n.elements[id].at = { ref: b2, edge: 'start', off: 1 }; S.vo10moment = [{ type: 'move', ids: [id] }, n]; }
for (const [k, keys] of [['del01h', ['VO_01h']], ['delVo10', ['VO_10']], ['delVo10and11', ['VO_10', 'VO_11']], ['delAmb', ['AMB_01']]]) {
  const ids = keys.map(x => idOf(x)), n = clone(score), removed = {}; for (const id of ids) { removed[id] = score.elements[id]; delete n.elements[id]; }
  S[k] = [{ type: 'delete', ids, removed }, n]; }
{ const id = idOf('G_BELL'), n = clone(score); n.elements[id].gate.fw = 30; S.bell30 = [{ type: 'gate', ids: [id] }, n]; }
{ const id = idOf('G_BELL'), n = clone(score); n.elements[id].gate.expected += 1; S.bellSim = [{ type: 'sim', ids: [id] }, n]; }
{ const vo5 = idOf('VO_05'), r = X.reanchor(score, vo5, { ref: idOf('VO_04'), edge: 'end' }, E); S.reanchor = [{ type: 'reanchor', ids: [vo5] }, r.next]; }
{ const ids = [idOf('VO_13'), idOf('VO_14')]; S.moveMany = [{ type: 'move', ids }, X.moveMany(score, ids, 1, {}, E, kids)]; }
{ const tb = Object.keys(score.beats).find(k => score.beats[k].key === '2.4'), r = X.planPaste(score, X.clipOf(score, [idOf('VO_10')], E), { beat: tb, off: 3 }, E, { who: 'B' });
  S.paste = [{ type: 'paste', ids: r.ids }, r.next]; }
const R = {}; for (const k in S) R[k] = itemsOf(S[k][0], S[k][1]);
const D = k => Pol.decide(S[k][0], R[k].items, { label: k, relocated: [], ripple: R[k].ripple });
{ const bad = Object.keys(S).filter(k => !same(k, S[k][0], R[k].items, [], R[k].ripple));
  check(`the ${Object.keys(S).length} cases of integrity_test and this step: same decision as today`, !bad.length, bad.join(', ') || Object.keys(S).map(k => k + ':' + D(k).mode).join(' ')); }

console.log('the modes of design B §11 step 2');
{ const d = D('vo10keep'); check('a voice moved keeping its order (VO_10 +0.3 s): apply, the Unreal item stays a note', d.mode === 'apply' && R.vo10keep.items.some(i => i.sv === 'info' && i.rule === 'C3.VO.WIRED'), R.vo10keep.items.map(i => i.sv + ' ' + i.rule).join(', ')); }
{ const d = D('vo10moment'); check('a voice moved to another moment (VO_10 into 1.R4): card, a click (no reason)', d.mode === 'card' && d.breaks && !d.needReason && d.shown.some(i => /another moment/.test(i.body)), [...new Set(d.shown.map(i => i.sv + ' ' + i.rule))].join(', ')); }
{ const d = D('vo13order'); check('a voice moved past the next one (VO_13 +5 s alone): card', d.mode === 'card' && d.shown.some(i => /order|overlaps/.test(i.body))); }
{ const d = D('delVo10'); check('deleting a wired voice (VO_10): card with a written reason', d.mode === 'card' && d.needReason && d.shown.some(i => i.sv === 'block' && i.rule === 'C3.VO.WIRED')); }
{ const d = D('del01h'); check('deleting a voice Unreal does not call (VO_01h): no reason', !d.needReason, d.mode); }
{ const d = D('textVo10'); check('new words for a wired voice (VO_10): card, a click (no reason)', d.mode === 'card' && d.breaks && !d.needReason); }
{ const d = D('bell30'); check('G_BELL timeout 30 s (FW_Bell is a locked final value): card with a written reason', d.mode === 'card' && d.needReason && d.shown.some(i => i.lock)); }
{ const d = D('delAmb'); check('deleting an ambience Unreal picks by name: card with a written reason', d.mode === 'card' && d.needReason); }
{ const d = D('paste'); check('pasting a copy: quiet (the copy is new to Unreal)', d.mode === 'quiet' && !d.needReason); }
{ const d = D('reanchor'); check('a new anchor that keeps the time: apply (nothing to review)', d.mode === 'apply'); }

console.log('quiet verbs');
{ const extra = [...Pol.QUIET].filter(t => !TODAY_QUIET.has(t)).sort(), lost = [...TODAY_QUIET].filter(t => !Pol.QUIET.has(t));
  check('Policy.QUIET = the set commit() had + migrate, import-map, branch-view (design B §8.1) + accepted-clean (§9) + bind (design A §3.6, "Bind to Unreal") + import-add (design B §7.3, adding what guion.js has), minus rename (design A §7.3)', JSON.stringify(lost) === '["rename"]' && JSON.stringify(extra) === '["accepted-clean","bind","branch-view","import-add","import-map","migrate"]', 'extra: ' + extra.join(', ') + (lost.length ? ' · lost: ' + lost.join(', ') : '')); }
{ const note = [{ sv: 'info', ly: 'C3', rule: 'C3.TITLE.STAGE', title: 't', body: 'b', el: 'x', ids: ['x'] }], warn = [{ sv: 'warn', ly: 'C3', rule: 'C3.VO.WIRED', title: 't', body: 'b', el: 'x', ids: ['x'] }];
  const dr = it => Pol.decide({ type: 'rename', ids: ['x'] }, it, { label: 'Rename · X', relocated: [], ripple: '' });
  check('a rename with only notes applies; a rename that breaks something opens the card (never quiet)', dr([]).mode === 'apply' && dr(note).mode === 'apply' && dr(warn).mode === 'card' && dr(warn).breaks && !dr(warn).needReason, dr(note).mode + ' / ' + dr(warn).mode); }
{ const bad = [...Pol.QUIET].filter(t => { const d = Pol.decide({ type: t, ids: [] }, R.delVo10.items, { label: 'X', relocated: [], ripple: '' }); return d.mode !== 'quiet' || d.needReason; });
  check(`every quiet verb (${Pol.QUIET.size}) never opens a card, even with a block among its items`, !bad.length, bad.join(', ')); }
{ const bad = ['move', 'move-beat', 'offset', 'reanchor', 'delete', 'text', 'trim', 'gate', 'sim'].filter(t => Pol.QUIET.has(t));
  check('the verbs that change a time or a wire are not quiet', !bad.length, bad.join(', ')); }
{ const w1 = [{ sv: 'warn', ly: 'C2', rule: 'C2.VO.OVERLAP', title: 't', body: 'b', el: 'x' }], w2 = w1.concat([{ sv: 'block', ly: 'C1', rule: 'C1.ANCHOR.MISSING', title: 't', body: 'b', el: 'y' }]),
    c3 = [{ sv: 'warn', ly: 'C3', rule: 'C3.VO.WIRED', title: 't', body: 'b', el: 'z', ids: ['z'] }], dq = (it, rel, rip) => Pol.decide({ type: 'add' }, it, { label: 'Add · VO_X', relocated: rel, ripple: rip }).toast;
  check('a quiet edit counts its new warnings of the piece in a toast', dq(w1, [], '') === 'Add · VO_X · 1 new warning in Problems (F8)' && dq(w2, [], '') === 'Add · VO_X · 2 new warnings in Problems (F8)', dq(w2, [], ''));
  check('  not the Unreal items, and nothing when a relocation or a ripple speaks first', dq(c3, [], '') === null && dq(w1, [{ id: 'x' }], '') === null && dq(w1, [], '3 later items shift +1.0 s') === null); }
check('after the card: "Done", "Done · accepted and recorded in Problems", with the ripple', Pol.doneToast('repair', '') === 'Done' && Pol.doneToast('anyway', 'total 17:01 (+1.0 s)') === 'Done · accepted and recorded in Problems · total 17:01 (+1.0 s)');

console.log('Proceed anyway: the records (acceptRecords)');
{
  const t1 = '2026-10-05T10:00:00.000Z', t2 = '2026-10-05T11:00:00.000Z', t3 = '2026-10-05T12:00:00.000Z';
  const id10 = idOf('VO_10'), id11 = idOf('VO_11'), fp10 = 'C3.VO.WIRED|' + id10;
  // records already there: another element's, and one of an element that no longer exists
  const seed = [{ fp: 'C2.FLASH|' + idOf('VO_05'), sv: 'warn', ly: 'C2', rule: 'C2.FLASH', msg: 'm', el: idOf('VO_05'), own: '—', who: 'S', reason: 'kept', at: t1 },
    { fp: 'C3.VO.WIRED|el_gone', sv: 'block', ly: 'C3', rule: 'C3.VO.WIRED', msg: 'm', el: 'el_gone', own: 'x', who: 'B', reason: 'old', at: t1 }];
  const seedStr = JSON.stringify(seed), items = R.delVo10.items;
  const a1 = Pol.acceptRecords(seed, items, { who: 'B', reason: 'I will rewire it in Unreal', at: t1 });
  const r1 = a1.find(x => x.fp === fp10);
  check('one record per element and rule, with today\'s fields', !!r1 && r1.sv === 'block' && r1.ly === 'C3' && r1.rule === 'C3.VO.WIRED' && r1.el === id10 && r1.who === 'B' && r1.reason === 'I will rewire it in Unreal' && r1.at === t1 && /^Called by Unreal: /.test(r1.msg) && !r1.history, r1 && r1.msg.slice(0, 60));
  check('  the records it gets are kept, unchanged (pure: a new array)', JSON.stringify(seed) === seedStr && a1 !== seed && seed.every(s => a1.some(x => JSON.stringify(x) === JSON.stringify(s))));
  const a2 = Pol.acceptRecords(a1, items, { who: 'S', reason: 'second decision', at: t2 }), r2 = a2.find(x => x.fp === fp10);
  check('accepted again: same record, the new author/reason/time, its first message, history of both decisions', a2.length === a1.length && r2.who === 'S' && r2.reason === 'second decision' && r2.at === t2 && r2.msg === r1.msg
    && r2.history.length === 2 && r2.history[0].who === 'B' && r2.history[0].at === t1 && r2.history[1].who === 'S' && r2.history[1].reason === 'second decision' && !r1.history, JSON.stringify(r2.history.map(h => h.who + '@' + h.at.slice(11, 13))));
  const a3 = Pol.acceptRecords(a2, items, { who: 'B', reason: 'third', at: t3 });
  check('  a third time: history of three, nothing removed', a3.length === a2.length && a3.find(x => x.fp === fp10).history.length === 3 && a2.find(x => x.fp === fp10).history.length === 2);
  const g = R.delVo10and11.items.find(i => i.rule === 'C3.VO.WIRED' && i.ids && i.ids.length === 2), a4 = Pol.acceptRecords(a3, R.delVo10and11.items, { who: 'B', reason: 'both', at: t3 });
  check('an item for two voices gives a record for each', !!g && a4.some(x => x.fp === fp10) && a4.some(x => x.fp === 'C3.VO.WIRED|' + id11) && a4.length === a3.length + 1);
  check('a note (info) is never recorded', Pol.acceptRecords([], R.vo10keep.items, { who: 'B', reason: '', at: t1 }).length === 0 && R.vo10keep.items.length > 0);
  const twice = [{ sv: 'warn', ly: 'C2', rule: 'C2.VO.OVERLAP', title: 'Two voices at once', body: 'a', el: id11 }, { sv: 'warn', ly: 'C2', rule: 'C2.VO.OVERLAP', title: 'Two voices at once', body: 'b', el: id11 }];
  const a5 = Pol.acceptRecords(undefined, twice, { who: 'B', reason: 'r', at: t1 });
  check('the same rule and element twice in one decision: one record, two entries in its history (as before)', a5.length === 1 && a5[0].history.length === 2);
  // never deletes: every record it got is still there, whatever is accepted
  let lostAny = 0, acc = seed;
  for (const k in R) { const nx = Pol.acceptRecords(acc, R[k].items, { who: 'B', reason: k, at: t2 }); if (nx.length < acc.length || acc.some(a => !nx.some(x => x.fp === a.fp))) lostAny++; acc = nx; }
  check(`it never deletes a record (${Object.keys(R).length} acceptances in a row)`, !lostAny && acc.length >= seed.length, acc.length + ' records');
  // the same JSON as the writer commit() had, step by step (the score saved after Proceed anyway does not change), with the
  // documented additions: an Unreal item's record, and each decision of its history, keeps the verb it was accepted for (so
  // accepting a rename never answers a later delete), and since lote 5 step 9 (accepted means this value) the value, the state,
  // the revision and what Unreal had; accepting a break that leaves an element different from the APK also writes that
  // difference (a C3.DIVERGE record), and one that leaves a timeout different from Unreal's writes that drift (a C3.DRIFT record). Set those aside and it is byte for byte what it was
  const NEWF = new Set(['verb', 'value', 'state', 'rev', 'unreal']), noVerb = L => JSON.stringify((L || []).filter(x => x.rule !== 'C3.DIVERGE' && x.rule !== 'C3.DRIFT'), (k, v) => NEWF.has(k) ? undefined : v);
  let A = undefined, Bn = { accepted: undefined }, eq = true;
  const steps = [['delVo10', 'B', t1], ['delVo10', 'S', t2], ['textVo10', 'B', t2], ['delVo10and11', 'S', t3], ['bell30', 'B', t3], ['vo10moment', 'S', t3], ['delAmb', 'B', t1]];
  for (const [k, who, at] of steps) {
    A = Pol.acceptRecords(A, R[k].items, { who, reason: 'why ' + k, at }); todayAccept(Bn, R[k].items, who, 'why ' + k, at);
    if (noVerb(A) !== JSON.stringify(Bn.accepted)) eq = false; }
  { const T = { accepted: clone(seed) }; todayAccept(T, twice, 'B', 'r', t1); if (noVerb(Pol.acceptRecords(seed, twice, { who: 'B', reason: 'r', at: t1 })) !== noVerb(T.accepted)) eq = false; }
  check('the records are the ones commit() wrote before the extraction, byte for byte once the verb is set aside', eq, A.length + ' records');
  const r10 = A.find(x => x.fp === fp10), amb = A.find(x => x.rule === 'C3.AMB.PICK');
  check('  the verb of each decision for VO_10 (delete, delete, text, delete, move to another moment); delete for the ambience; none for the items of the piece', r10.verb === 'delete' && JSON.stringify(r10.history.map(h => h.verb)) === '["delete","delete","text","delete","move"]'
    && amb && amb.verb === 'delete' && Pol.acceptRecords([], twice, { who: 'B', reason: 'r', at: t1 }).every(x => !('verb' in x) && x.history.every(h => !('verb' in h))), JSON.stringify(r10.history.map(h => h.verb)));
}

// lote 5 step 6: an item that carries its own fingerprint (the branch rules say which side of the decision) is recorded under it
{ const items = [{ sv: 'block', ly: 'C1', rule: 'C1.BRANCH.ANCHOR', title: 'Anchor across branches', body: 'x', ev: 'rule C1.BRANCH.ANCHOR', el: 'el_a', fp: 'C1.BRANCH.ANCHOR|el_a|share=no' }, { sv: 'warn', ly: 'C2', rule: 'C2.VO.OVERLAP', title: 'Two voices at once', body: 'y', ev: 'rule C2.VO.OVERLAP', el: 'el_b' }];
  const acc = Pol.acceptRecords([], items, { who: 'B', reason: 'on purpose', at: '2026-10-07T12:00:00Z' });
  check('a branch item is recorded under rule|element with its side as the value; an item with no fingerprint of its own has no value (null: unknown)', acc.length === 2 && acc[0].fp === 'C1.BRANCH.ANCHOR|el_a' && acc[0].value === 'share=no' && acc[1].fp === 'C2.VO.OVERLAP|el_b' && acc[1].value === null, acc.map(a => a.fp + ' @ ' + a.value).join(' | '));
  check('  Policy.decide: a block of the branch rules opens the card and needs a reason; moving a side is not a quiet verb', Pol.decide({ type: 'reanchor', ids: ['el_a'] }, items, {}).mode === 'card' && Pol.decide({ type: 'branch', ids: ['el_a'] }, items, {}).needReason === true && !Pol.QUIET.has('branch') && Pol.decide({ type: 'branch', ids: [] }, [], {}).mode === 'apply'); }

check('the score of the test was never changed', JSON.stringify(score) === before);
console.log(fails ? `\n${fails} FAILED` : '\nall ok');
process.exit(fails ? 1 : 0);
