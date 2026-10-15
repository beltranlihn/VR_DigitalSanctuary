// bind_ids_test.mjs — tools/score/bind_ids.mjs (lote 5 design A §7.4): the ids it generates equal today's rules and key
// lookups, except the documented corrections; a re-run keeps what a rename or a delete in the score would otherwise lose; the
// files on disk are its output; it never writes the score. Runs on the frozen fixture tools/score/fixtures/f0-score.json.
//   node tools/score/bind_ids_test.mjs
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { build, UNUSED, NOASSET, trackerUnused, scanAssets, pathMap, remapPaths, writeBinding, fmtJson } from './bind_ids.mjs';
const require = createRequire(import.meta.url);
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const E = require(path.join(ROOT, 'web/editor-obra/app/js/engine.js'));
const P = require(path.join(ROOT, 'web/editor-obra/app/js/partitura.js'));
const I = require(path.join(ROOT, 'web/editor-obra/app/js/integrity.js'));
const rd = p => fs.readFileSync(path.join(ROOT, p), 'utf8');
const clone = o => JSON.parse(JSON.stringify(o)), same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
let fails = 0;
const check = (n, ok, info) => { console.log((ok ? '  ok   ' : '  FAIL ') + n + (info ? '  · ' + info : '')); if (!ok) fails++; };

const scoreText = rd('tools/score/fixtures/f0-score.json'), score = JSON.parse(scoreText), K = id => score.elements[id].key;
const idOf = (k, b) => Object.keys(score.elements).find(id => score.elements[id].key === k && (!b || score.beats[score.elements[id].beat].key === b));
// the catalogs generated for the fixture (frozen F0 copies): the live ones follow the owner's edits of the score
const FX = { contract: 'tools/score/fixtures/contract-f0.json', binding: 'tools/score/fixtures/binding-f0.json' };
const disk = { contract: JSON.parse(rd(FX.contract)), binding: JSON.parse(rd(FX.binding)) };
// "today": the contract before the ids (the hand rules only: no ids, no corrections, vo.wired without its generated excludeKeys)
const today = clone(disk.contract);
today.entries = today.entries.filter(c => c.id !== 'vo.unused' && c.id !== 'vo.noasset');
for (const c of today.entries) { delete c.ids; delete c.idKeys; delete c.idsFrom; }
delete today.entries.find(c => c.id === 'vo.wired').match.excludeKeys;
const bindToday = clone(disk.binding); delete bindToday.idsFrom; for (const b of bindToday.binds) delete b.ids; for (const o of Object.values(bindToday.origins)) delete o.ids;
const sched = E.resolve(score, { persona: 'typical' });

console.log('the contract: ids = today\'s rules, except the documented corrections');
const out = build({ score, scoreText, contract: today, binding: bindToday, at: '2026-10-07' });
const byId = Object.fromEntries(out.contract.entries.map(c => [c.id, c]));
{ const bad = out.contract.entries.filter(c => !['vo.wired', 'vo.unused', 'vo.noasset'].includes(c.id) && !same(c.ids, out.regex0[c.id]));
  check(`every other entry (${out.contract.entries.length - 3}): ids = today's rule, element for element`, !bad.length, bad.map(c => c.id).join(', ')); }
const docd = [...UNUSED, ...NOASSET];
{ const want = out.regex0['vo.wired'].filter(id => !docd.includes(K(id))), lost = out.regex0['vo.wired'].filter(id => !byId['vo.wired'].ids.includes(id)).map(K).sort();
  check('vo.wired = today\'s 68 minus the 12 documented voices it had (VO_01h never was in it): 56', same(byId['vo.wired'].ids, want) && out.regex0['vo.wired'].length === 68 && want.length === 56 && lost.length === 12, lost.join(', ')); }
check('vo.unused = the 10 voices of the BP_Obra_SC tracker; vo.noasset = VO_12b, VO_17b, VO_21 (not-in-unreal, Director ack pending)',
  same(byId['vo.unused'].ids.map(K).sort(), UNUSED.slice().sort()) && same(byId['vo.noasset'].ids.map(K).sort(), NOASSET.slice().sort())
  && byId['vo.unused'].kind === 'not-in-unreal' && byId['vo.noasset'].kind === 'not-in-unreal' && byId['vo.unused'].pending === 'Director ack' && byId['vo.noasset'].pending === 'Director ack'
  && same(byId['vo.wired'].match.excludeKeys, docd));
{ const bad = out.contract.entries.filter(c => !same(c.ids, Object.keys(score.elements).filter(id => I.ruleMatches(c, score.elements[id]))));
  check('after the corrections every rule says the same as its ids (C3.CONTRACT.RULE is silent at load)', !bad.length, bad.map(c => c.id).join(', ')); }
{ const pairs = out.contract.entries.reduce((a, c) => a + c.ids.length, 0), distinct = new Set(out.contract.entries.flatMap(c => c.ids)).size;
  check('178 (entry, element) pairs over 175 elements (before: 176 over 174; VO_01h joins as vo.unused; lote 5 step 8: VO_11h is also in help.after, the knob that places it)', pairs === 178 && distinct === 175 && Object.values(out.regex0).reduce((a, x) => a + x.length, 0) === 177, pairs + ' / ' + distinct); }
check('idKeys keep the name each element had (the "was" of a rename); idsFrom names the score and the day', out.contract.entries.every(c => c.ids.every(id => c.idKeys[id] === K(id)) && /^rev \d+ sha12 [0-9a-f]{12}$/.test(c.idsFrom.score) && c.idsFrom.at === '2026-10-07'));
check('the tracker line still lists the documented 10 (re-checked against BP_Obra_SC.md)', same(trackerUnused(rd('.claude/skills/unreal-vr/blueprints/BP_Obra_SC.md')), UNUSED));
{ const a = scanAssets(ROOT);
  check('the 3 voices still have no asset in VR_Test (Content or plugins)', NOASSET.every(k => !a.has(k)) && a.has('VO_10'), NOASSET.filter(k => a.has(k)).join(', ')); }

console.log('the bindings: ids = Partitura.measure by key, every stage');
{ let n = 0; const bad = [];
  for (const b of out.binding.binds) for (const k of b.perStage ? [0, 1, 2, 3, 4] : [null]) {
    const plain = bindToday.binds.find(x => x.knob === b.knob), r0 = P.measure(score, sched, bindToday, plain, k), r1 = P.measure(score, sched, out.binding, b, k);
    const f = b.ids && b.ids[k == null ? '*' : k];
    if (!r0) { if (f !== undefined) bad.push(b.knob + '[' + k + '] has an id without a counterpart'); continue; }
    n++;
    if (!same([].concat(f), r0.els)) bad.push(b.knob + '[' + k + '] ids ≠ key lookup');
    if (!r1 || r1.stale || r1.value !== r0.value || !same(r1.els, r0.els)) bad.push(b.knob + '[' + k + '] measured by id differs');
  }
  check(`${n} stage ids, each = the key lookup, and measured by id gives the same value with no stale note`, !bad.length && n === 81, bad.slice(0, 4).join('; ')); }
{ const o = out.binding.origins, env = ['V1', 'V2', 'V3', 'V4'].map(b => idOf('ENV_SWAP', b));
  check('the origin phase0 is frozen on ENV_SWAP of V1..V4 (stage 0 is the moment itself: nothing to freeze); hall and consts are moments', same(o.phase0.ids, { 1: env[0], 2: env[1], 3: env[2], 4: env[3] }) && !o.hall.ids && !o.consts.ids, JSON.stringify(o.phase0.ids)); }
check('idsFrom goes right after "verified"', same(Object.keys(out.binding).slice(0, 3), ['note', 'verified', 'idsFrom']));

console.log('re-runnable');
{ const again = build({ score, scoreText, contract: out.contract, binding: out.binding, at: '2026-12-31' });
  check('a second run changes nothing (not even the dates)', same(again.contract, out.contract) && same(again.binding, out.binding) && !again.report.corrections.length && again.report.binds.every(b => !b.changed && !b.rebound.length)); }
{ // the owner renames T_IN (V2) and deletes VO_10, saves, and someone runs the generator again
  const tin = idOf('T_IN', 'V2'), vo10 = idOf('VO_10'), s2 = clone(score); s2.elements[tin].key = s2.elements[tin].label = 'T_INTRO'; delete s2.elements[vo10];
  const r = build({ score: s2, contract: out.contract, binding: out.binding, at: '2026-12-31' }), c = r.contract.entries.find(x => x.id === 'title.stage'), w = r.contract.entries.find(x => x.id === 'vo.wired');
  const bT = r.binding.binds.find(b => b.knob === 'Etapa_TituloRevelaIni');
  check('re-run after a rename: T_INTRO keeps its place in title.stage, still known as T_IN; the Partitura bind keeps its id (not re-bound)', c.ids.includes(tin) && c.idKeys[tin] === 'T_IN' && bT.ids['2'] === tin
    && r.report.entries.find(e => e.id === 'title.stage').renamed[0] === 'T_IN → T_INTRO' && !r.report.binds.find(b => b.knob === 'Etapa_TituloRevelaIni').rebound.length);
  check('  after a delete: VO_10 stays as an orphan (Unreal still has it); --prune drops it', w.ids.includes(vo10) && w.idKeys[vo10] === 'VO_10' && !build({ score: s2, contract: out.contract, binding: out.binding, prune: true }).contract.entries.find(x => x.id === 'vo.wired').ids.includes(vo10));
  const P2 = I.staticProblems(s2, E.resolve(s2, { persona: 'typical' }), r.contract).filter(p => /^C3\.CONTRACT/.test(p.rule)).map(p => p.rule + ' ' + (p.el ? s2.elements[p.el].key : '-')).sort();
  check('  and the editor still says both (T_INTRO was T_IN; VO_10 no longer in the score)', same(P2, ['C3.CONTRACT.ORPHAN -', 'C3.CONTRACT.RULE T_INTRO']), P2.join(', ')); }
{ // a corrected voice gets its recording (it leaves vo.noasset and goes back to vo.wired)
  const r = build({ score, scoreText, contract: out.contract, binding: out.binding, noasset: ['VO_12b', 'VO_17b'], at: '2026-12-31' }), w = r.contract.entries.find(x => x.id === 'vo.wired');
  check('a voice that gets its asset (VO_21) goes back to vo.wired, and leaves vo.noasset', w.ids.includes(idOf('VO_21')) && !w.match.excludeKeys.includes('VO_21') && !r.contract.entries.find(x => x.id === 'vo.noasset').ids.includes(idOf('VO_21')), r.report.corrections.join(' | ')); }
{ // review of the chunk: a rename never moves an element into another entry; the rules are applied to the name Unreal knows
  const holders = (c, id) => c.entries.filter(x => (x.ids || []).includes(id)).map(x => x.id).join(',');
  for (const [k, cid] of [['VO_24', 'vo.unused'], ['VO_12b', 'vo.noasset']]) {
    const id = idOf(k), s2 = clone(score); s2.elements[id].key = s2.elements[id].label = k + 'x';
    const r = build({ score: s2, contract: out.contract, binding: out.binding, at: '2026-12-31' }), c = r.contract.entries.find(x => x.id === cid);
    const P2 = I.staticProblems(s2, E.resolve(s2, { persona: 'typical' }), r.contract).filter(p => /^C3\.CONTRACT/.test(p.rule));
    check(`re-run after renaming ${k} → ${k}x: still only in ${cid} (known as ${k}), never in vo.wired; the editor says only "${k}x was ${k}"`, holders(r.contract, id) === cid && c.idKeys[id] === k
      && r.report.entries.find(e => e.id === cid).renamed[0] === `${k} → ${k}x` && same(r.contract.entries.find(x => x.id === 'vo.wired').ids, out.contract.entries.find(x => x.id === 'vo.wired').ids)
      && P2.length === 1 && P2[0].el === id && new RegExp(`^${k}x was ${k}: still not in Unreal`).test(P2[0].msg), holders(r.contract, id) + ' · ' + P2.map(p => p.msg).join(' | '));
    const again = build({ score: s2, contract: r.contract, binding: r.binding, at: '2027-01-01' });
    check('  and a second re-run changes nothing', same(again.contract, r.contract) && same(again.binding, r.binding));
  }
  { const id = idOf('VO_12b'), s2 = clone(score); s2.elements[id].key = s2.elements[id].label = 'VO_12bx';
    const r1 = build({ score: s2, contract: out.contract, binding: out.binding, at: '2026-12-31' }), r2 = build({ score: s2, contract: r1.contract, binding: r1.binding, noasset: ['VO_17b', 'VO_21'], at: '2027-01-01' });
    check('  renamed VO_12b gets its recording later: it goes back to vo.wired (still known as VO_12b) and leaves vo.noasset', holders(r2.contract, id) === 'vo.wired' && r2.contract.entries.find(x => x.id === 'vo.wired').idKeys[id] === 'VO_12b', holders(r2.contract, id)); }
  { const id = idOf('VO_10'), s2 = clone(score); s2.elements[id].key = s2.elements[id].label = 'GHOST_TEN';
    const r = build({ score: s2, contract: out.contract, binding: out.binding, at: '2026-12-31' });
    check('  a wired voice renamed into another rule (VO_10 → GHOST_TEN, ghost.take is ^GHOST_): stays in vo.wired only', holders(r.contract, id) === 'vo.wired', holders(r.contract, id)); }
}

console.log('the files on disk are its output');
{ const fx = new Set(Object.keys(score.elements)), bad = [];
  for (const c of out.contract.entries) { const d = disk.contract.entries.find(x => x.id === c.id); if (!d || !same((d.ids || []).filter(id => fx.has(id)), c.ids)) bad.push(c.id); }
  for (const b of out.binding.binds) { const d = disk.binding.binds.find(x => x.knob === b.knob); if (!d || !same(d.ids, b.ids)) bad.push(b.knob); }
  if (!same(disk.binding.origins, out.binding.origins)) bad.push('origins');
  check('obra/unreal/contract.json and partitura_binding.json carry these ids (generated, not by hand)', !bad.length && disk.contract.entries.length === out.contract.entries.length, bad.join(', ')); }
{ const txt = rd(FX.binding), w = writeBinding(txt, disk.binding), blank = t => t.split(/\r?\n/).filter(l => !l.trim()).length;
  check('the binding keeps its hand layout: one bind and one origin per line, its blank lines', same(JSON.parse(w), disk.binding) && blank(w) === blank(txt) && w === txt
    && disk.binding.binds.every(b => w.split('\n').some(l => l.trim().startsWith('{ "knob": "' + b.knob + '"')))); }
check('contract.json is in the house format (formatting it again changes nothing)', rd(FX.contract).replace(/\r\n/g, '\n') === fmtJson(disk.contract) + '\n'
  && rd('obra/unreal/contract.json').replace(/\r\n/g, '\n') === fmtJson(JSON.parse(rd('obra/unreal/contract.json'))) + '\n');
{ const h = f => crypto.createHash('sha1').update(fs.readFileSync(path.join(ROOT, f))).digest('hex');
  const watch = ['obra/score/score.json', 'tools/score/fixtures/f0-score.json', 'obra/unreal/roles.json', 'obra/unreal/contract.json', 'obra/unreal/partitura_binding.json', FX.contract, FX.binding], before = watch.map(h);
  let code = 0, txt = ''; try { txt = execFileSync(process.execPath, [path.join(ROOT, 'tools/score/bind_ids.mjs'), '--check', '--score', 'tools/score/fixtures/f0-score.json', '--contract', FX.contract, '--binding', FX.binding], { encoding: 'utf8' }); } catch (e) { code = e.status; txt = e.stdout; }
  check('--check on the fixture: up to date (so a later change of the live score never turns this red), and it writes nothing (score, fixture, roles, contract, binding)', code === 0 && /up to date/.test(txt) && same(before, watch.map(h)), txt.trim().split('\n').pop()); }

console.log('Unreal paths: the maps of 2026-10-02 and the disk');
{ const ctx = { root: ROOT, assets: scanAssets(ROOT), paths: pathMap(ROOT) };
  const r = remapPaths({ a: 'pacer in /Game/SoulCharger/Mechanics/Breath/Audio/SND_PacerExhale, voices in /Game/SoulCharger/Obra/Audio', b: ['/Game/NoSuch/Thing'] }, 't', ctx);
  check('an asset that moved to a plugin is rewritten (/SC_Breath/Audio/SND_PacerExhale); a folder that exists is kept; an unknown path is reported', r.doc.a.includes('/SC_Breath/Audio/SND_PacerExhale') && r.doc.a.includes('/Game/SoulCharger/Obra/Audio') && r.unmapped.length === 1 && r.changes.length === 1, r.changes.concat(r.unmapped).join(' | '));
  const f = remapPaths({ a: '/Game/SoulCharger/Mechanics/Sequencer/Audio' }, 't', ctx);
  check('a folder emptied into a plugin maps to its new folder (Sequencer/Audio → /SC_Sequencer/Audio)', f.doc.a === '/SC_Sequencer/Audio', f.changes.concat(f.unmapped).join(' | '));
  const live = [remapPaths(disk.contract, 'contract', ctx), remapPaths(disk.binding, 'binding', ctx), remapPaths(JSON.parse(rd('obra/unreal/roles.json')), 'roles', ctx)];
  check('the three files: no path to move and none unmapped (the voice folders /Game/SoulCharger/Obra/Audio, Mechanics/Breath/Audio and Hall/Audio, all three still there)', live.every(x => !x.changes.length && !x.unmapped.length) && live[0].kept.length === 3 && !live[1].kept.length && !live[2].kept.length, live.flatMap(x => x.kept).join(' | ')); }

check('the fixture was never changed', rd('tools/score/fixtures/f0-score.json') === scoreText);
console.log(fails ? `\n${fails} FAILED` : '\nall ok');
process.exit(fails ? 1 : 0);
