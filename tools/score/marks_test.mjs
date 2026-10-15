// marks_test.mjs — the marks Unreal emits (lote 5 design A §1-§2): the phase table, the vocabulary and its order, the run
// (obra/unreal/traza.json, frozen copy tools/score/fixtures/traza-20261002.json, today's shape and the optional fields the
// director may add), where each mark falls in the score (seed or schema 3), and the seed: pinned on its frozen copy as
// generated (tools/score/fixtures/marks-seed-v1.json), shape only on the live obra/score/seed/marks-v1.json (--live: pinned
// on the live one).
// Logic: web/editor-obra/app/js/marks.js, tools/score/seed_marks.mjs. Exit 1 if any case fails. Writes nothing.
//   node tools/score/marks_test.mjs [--live]
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { testScore, ROOT } from './test_score.mjs';
import { buildSeed, counts, SEED } from './seed_marks.mjs';
const require = createRequire(import.meta.url);
const E = require(path.join(ROOT, 'web/editor-obra/app/js/engine.js'));
const M = require(path.join(ROOT, 'web/editor-obra/app/js/marks.js'));
const { score, live, name: SRC } = testScore();
console.log('on the ' + SRC);
const TRAZA = JSON.parse(fs.readFileSync(path.join(ROOT, 'tools/score/fixtures/traza-20261002.json'), 'utf8'));
const LIVE = { exportado: '2026-10-02T18:06:10', hash: '54ef5a851e4b', valores: { Fundido_Dur: 3.5, Sim_EtapaMax: 90 } };   // the export of that day, frozen
// the seed as generated, frozen (tools/score/fixtures/marks-seed-v1.json): the counts and times are pinned on it, so the
// owner's corrections to the live seed never break a test; --live pins them on the live seed instead. The live seed itself
// gets only shape and validation checks (at the end)
const SEED_FIX = path.join(ROOT, 'tools/score/fixtures/marks-seed-v1.json');
const seed = JSON.parse(fs.readFileSync(live ? SEED : SEED_FIX, 'utf8'));
const before = JSON.stringify(score), seedBefore = JSON.stringify(seed), trBefore = JSON.stringify(TRAZA);
let fails = 0;
const check = (name, ok, info) => { console.log((ok ? '  ok   ' : '  FAIL ') + name + (info ? '  · ' + info : '')); if (!ok) fails++; };
const near = (a, b, eps) => a != null && b != null && Math.abs(a - b) < (eps || 1e-6);
const clone = o => JSON.parse(JSON.stringify(o));
const beatOf = key => Object.keys(score.beats).find(b => score.beats[b].key === key);
const elIn = (bk, key) => Object.keys(score.elements).find(id => score.elements[id].beat === beatOf(bk) && score.elements[id].key === key);
const S = E.resolve(score, { persona: 'typical' });

console.log('the phase table: phase numbers live only in marks.js');
{
  const want = { 16: 'OBRA.DISC', 9: 'HALL.START', 0: 'S1.OPEN', 4: 'S1.ALMA', 5: 'S1.INTRO', 6: 'S1.BEGIN', 7: 'S1.OUTRO', 8: 'S1.CHARGE', 2: 'S1.BYE', 3: null,
    10: 'FINAL.DARK', 11: 'FINAL.RETURN', 12: 'FINAL.RESULTS', 13: 'FINAL.EXIT', 14: 'FINAL.CREDITS', 15: 'FINAL.FADE' };
  const got = Object.keys(want).map(f => [f, M.fromPhase(+f, 1)]);
  check('the 16 phase codes of RunObra give their mark (3, legacy OpenLevel, gives none)', got.every(([f, n]) => n === want[f]) && Object.keys(M.PHASE).length === 16, got.filter(([f, n]) => n !== want[f]).map(x => x.join('→')).join(' ') || '16 codes');
  check('stage phases carry their stage: phase 6 of stage 3 is S3.BEGIN, stage 0 is S0', M.fromPhase(6, 3) === 'S3.BEGIN' && M.fromPhase(0, 0) === 'S0.OPEN' && M.fromPhase('8', '4') === 'S4.CHARGE');
  check('the last stage has no farewell: phase 2 of stage 4 is no mark (S4.BYE is invalid)', M.fromPhase(2, 4) === null && !M.isValid('S4.BYE'));
  check('an unknown phase, a stage out of 0-4 or no stage: no mark', M.fromPhase(1, 0) === null && M.fromPhase(0, 5) === null && M.fromPhase(4, null) === null && M.fromPhase(99, 0) === null);
  check('phases that are not per stage ignore the stage', M.fromPhase(9, 3) === 'HALL.START' && M.fromPhase(12, null) === 'FINAL.RESULTS');
}

console.log('the vocabulary (design A §1.2) and its canonical order');
{
  const ok = ['OBRA.DISC', 'OBRA.END', 'HALL.START', 'HALL.INTRO', 'HALL.1.6', 'HALL.3.30', 'S0.OPEN', 'S2.REQEND', 'S4.CHARGE', 'FINAL.FADE', 'SHARE.ASK', 'SHARE.NO'];
  const bad = ['S4.BYE', 'GATE.BELL', 'VO.end', 'S5.OPEN', 'HALL.4.1', 'HALL.1.123', 'hall.start', 'S1.begin', '', null, 42, 'FINAL.END'];
  check('every name of the vocabulary is valid', ok.every(M.isValid), ok.filter(n => !M.isValid(n)).join(' '));
  check('names Unreal does not emit are refused (GATE.*, VO.end, S4.BYE, lower case, …)', bad.every(n => !M.isValid(n)), bad.filter(n => M.isValid(n)).join(' '));
  check('sub-marks: Hall steps, the close request, SHARE; the rest are phase marks', ['HALL.INTRO', 'HALL.1.6', 'S3.REQEND', 'SHARE.YES'].every(M.isSub) && ['HALL.START', 'S1.BEGIN', 'FINAL.EXIT', 'OBRA.END', 'OBRA.DISC'].every(n => M.isPhase(n) && !M.isSub(n)) && !M.isPhase('S4.BYE'));
  const canon = ['OBRA.DISC', 'HALL.START', 'HALL.INTRO', 'HALL.1.1', 'HALL.1.6', 'HALL.1.12', 'HALL.1.30', 'HALL.2.1', 'S0.OPEN', 'S0.ALMA', 'S0.INTRO', 'S0.BEGIN', 'S0.REQEND', 'S0.OUTRO', 'S0.CHARGE', 'S0.BYE',
    'S1.OPEN', 'S3.BYE', 'S4.OPEN', 'S4.BEGIN', 'S4.REQEND', 'S4.OUTRO', 'S4.CHARGE', 'FINAL.DARK', 'FINAL.RETURN', 'FINAL.RESULTS', 'SHARE.ASK', 'SHARE.YES', 'SHARE.NO', 'FINAL.EXIT', 'FINAL.CREDITS', 'FINAL.FADE', 'OBRA.END'];
  const r = canon.map(M.rank);
  check('rank follows the canonical order (Hall steps by number, not as text: 6 < 12)', r.every((v, i) => v != null && (i === 0 || v > r[i - 1])), canon.length + ' names');
  check('rank of a name that is not a mark is null', M.rank('S4.BYE') === null && M.rank('GATE.X') === null);
  check('marks in words: short for the lane, long for a tooltip', M.label('S1.BEGIN') === 'S1 begin' && M.label('HALL.START') === 'Hall' && M.label('HALL.1.6') === 'Hall step 6' && M.label('S2.REQEND') === 'S2 close asked'
    && M.describe('S1.BEGIN') === 'Recognizing · the mechanic' && M.describe('FINAL.RETURN') === 'the return through the dark to the Hall', M.describe('S1.BEGIN'));
  check('stage and step of a mark', M.stageOf('S3.INTRO') === 3 && M.stepOf('S3.INTRO') === 'INTRO' && M.stageOf('FINAL.DARK') === null && M.stepOf('HALL.START') === null);
}

console.log('the Unreal run of 2 Oct 18:59 (frozen copy of obra/unreal/traza.json)');
{
  const tm = M.traceMarks(TRAZA, LIVE), last = tm[tm.length - 1];
  check('41 phase marks in the run, then OBRA.END = FINAL.FADE + Fundido_Dur = 1022.885', tm.length === 42 && tm.filter(m => !m.derived).length === 41 && last.mark === 'OBRA.END' && last.derived && near(last.t, 1022.885217, 1e-6), last && last.t.toFixed(3));
  check('the run starts at the Hall (no disclaimer: the smoke test runs without it) at 3.18 s on the director clock', tm[0].mark === 'HALL.START' && near(tm[0].t, 3.176292) && !tm.some(m => m.mark === 'OBRA.DISC'));
  check('every mark of the run is valid and appears once', tm.every(m => M.isValid(m.mark)) && new Set(tm.map(m => m.mark)).size === tm.length);
  const rk = tm.map(m => M.rank(m.mark));
  check('the run follows the canonical order (rank only grows)', rk.every((v, i) => i === 0 || v > rk[i - 1]));
  check('the five stages give OPEN … CHARGE, and BYE in stages 0-3 only', [0, 1, 2, 3, 4].every(K => ['OPEN', 'ALMA', 'INTRO', 'BEGIN', 'OUTRO', 'CHARGE'].every(s => tm.some(m => m.mark === `S${K}.${s}`))) && tm.filter(m => /\.BYE$/.test(m.mark)).length === 4);
  check('without the Partitura export the end of the run is unknown: no OBRA.END', M.traceMarks(TRAZA, null).length === 41 && M.traceMarks(TRAZA, { valores: {} }).length === 41);
  check('the director\'s values can also come bare ({Fundido_Dur})', near(M.traceMarks(TRAZA, { Fundido_Dur: 3.5 }).pop().t, 1022.885217));
  const I = M.traceInfo(TRAZA);
  check('what the run says: when, speed 1, director clock, no disclaimer, nothing unknown', I.generated === '20261002-185938' && I.at === '2026-10-02T18:59:38' && I.speed === 1 && I.clock === 'director' && I.disclaimer === false && I.unknown.length === 0 && I.dup.length === 0 && I.phases === 41 && I.marks === 41, JSON.stringify({ at: I.at, speed: I.speed }));
  check('simulated unless it says otherwise (only the smoke test writes it, always with -ObraSmoke)', I.sim === true && I.simSaid === false);
  check('no optional fields today: no hash, config, Hall steps, voices or history', I.hash === null && I.config === null && I.subs === 0 && I.vo === 0 && I.history.length === 0 && I.historyFiles.length === 0);
  check('nothing read, nothing changed: the run and the score stay as they were', JSON.stringify(TRAZA) === trBefore);
  check('no run, or not a run: nothing', M.traceMarks(null, LIVE).length === 0 && M.traceInfo(null) === null && M.traceInfo({}) === null && M.traceMarks({ fases: 'x' }).length === 0);
}

console.log('the optional fields the director may add (design A §6.8)');
{
  const t = clone(TRAZA);
  Object.assign(t, { config: { bSimulated: false, bDisclaimer: 'True', Speed: 1, DebugStart: -1 }, partitura_hash: '54ef5a851e4b',
    hall: [{ modo: 1, paso: 6, reloj_obra_s: 70.5 }, { mode: 1, step: 12, reloj_obra_s: 110.2 }, { mode: 1, step: 999, reloj_obra_s: 1 }],
    vo: [{ clip: 'VO_10', reloj_obra_s: 210, dur: 4.2 }], marks: [{ name: 'S3.REQEND', reloj_obra_s: 700 }, { name: 'GATE.X', reloj_obra_s: 1 }],
    history: [clone(TRAZA), 'trazas/traza-20261001-120000.json'] });
  t.fases.unshift({ fase: 16, etapa: 0, pared_s: 0, reloj_obra_s: 0.5, speed: 1 });
  t.fases.push({ fase: 2, etapa: 4, pared_s: 1, reloj_obra_s: 1100, speed: 1 }, { fase: 1, etapa: 0, pared_s: 1, reloj_obra_s: 1101, speed: 1 });
  const I = M.traceInfo(t);
  check('config: simulated and disclaimer as the director says them ("True" is true)', I.sim === false && I.simSaid === true && I.disclaimer === true);
  check('partitura_hash, Hall steps, voice clips and other marks are read', I.hash === '54ef5a851e4b' && I.subs === 3 && I.vo === 1, `${I.subs} sub-marks`);
  const subs = M.traceSubs(t);
  check('sub-marks: HALL.1.6 and HALL.1.12 from modo/paso or mode/step, S3.REQEND; invalid names left out', subs.map(s => s.mark).join(' ') === 'HALL.1.6 HALL.1.12 S3.REQEND', subs.map(s => s.mark).join(' '));
  check('history: earlier runs inline and file names, apart', I.history.length === 1 && I.historyFiles.length === 1 && I.historyFiles[0] === 'trazas/traza-20261001-120000.json');
  check('a phase that is no mark (S4.BYE, phase 1) is listed as unknown, never guessed', I.unknown.length === 2 && I.unknown[0].fase === 2 && I.unknown[1].fase === 1 && M.traceMarks(t, LIVE).length === 43, JSON.stringify(I.unknown));
  check('a run with its disclaimer has OBRA.DISC first', M.traceMarks(t, LIVE)[0].mark === 'OBRA.DISC');
  const w = clone(TRAZA); w.fases[5].reloj_obra_s = null;
  const tw = M.traceMarks(w, LIVE);
  check('a row without the director clock: the whole run uses the wall clock (one clock per run)', M.traceInfo(w).clock === 'wall' && near(tw[0].t, 4.6) && tw.length === 42, tw[0].t);
  const sp = clone(TRAZA); delete sp.speed; sp.fases.forEach(f => { f.speed = 4; });
  check('the speed comes from config, then the file, then its rows', M.traceInfo(sp).speed === 4 && M.traceInfo(t).speed === 1);
  check('dates: the smoke test\'s tag and ISO strings, never a time zone', M.isoOf('20261002-185938') === '2026-10-02T18:59:38' && M.isoOf('2026-10-02T18:06:10') === '2026-10-02T18:06:10' && M.isoOf('2026-10-02 18:06') === '2026-10-02T18:06:00' && M.isoOf('') === null && M.isoOf('x') === null);
}

console.log('where each mark falls in the score (schema 2: the seed)');
{
  const info = {}, sm = M.scoreMarks(score, S, seed, info);
  const names = Object.keys(sm);
  check('43 marks with a time: the 41 of the run, OBRA.DISC and the end', names.length === 43 && 'OBRA.DISC' in sm && 'OBRA.END' in sm, names.length);
  check('from the seed, nothing wrong in it', info.from === 'seed' && info.issues.length === 0, JSON.stringify(info.issues));
  if (!live) {
    check('HALL.START is the start of 1.1 (23.0 s), S0.OPEN the start of 3.1 (200.3 s)', near(sm['HALL.START'], 23, 1e-3) && near(sm['S0.OPEN'], S.t[beatOf('3.1')][0]) && near(sm['S0.OPEN'], 200.3, .05), sm['S0.OPEN'].toFixed(2));
    check('S1.OPEN … S4.OPEN are ENV_SWAP of V1 … V4 (rel el)', [1, 2, 3, 4].every(K => near(sm[`S${K}.OPEN`], S.t[elIn('V' + K, 'ENV_SWAP')][0])), [1, 2, 3, 4].map(K => sm[`S${K}.OPEN`].toFixed(1)).join(' '));
    check('the extra marks on elements: S2.BEGIN at CELL_IN, FINAL.DARK at FINAL, FINAL.FADE at NEGRO_FIN', near(sm['S2.BEGIN'], S.t[elIn('3.R3', 'CELL_IN')][0]) && near(sm['FINAL.DARK'], 821.98, .01) && near(sm['FINAL.FADE'], 1013, .01));
    check('OBRA.END is the end of the score', near(sm['OBRA.END'], S.total));
    check('the moment of each mark is kept (for Show in timeline)', info.beat['S1.BEGIN'] === beatOf('2.R5') && info.beat['FINAL.DARK'] === beatOf('5.R6'));
  }
  // what goes wrong, on copies: an element gone, a moment gone, a mark placed twice, a name Unreal does not emit
  const c1 = clone(score); delete c1.elements[elIn('3.R3', 'CELL_IN')];
  const i1 = {}, s1 = M.scoreMarks(c1, E.resolve(c1, { persona: 'typical' }), seed, i1);
  check('an el mark whose element was deleted: no time, and it says why', !('S2.BEGIN' in s1) && i1.issues.length === 1 && i1.issues[0].mark === 'S2.BEGIN' && /CELL_IN in moment 3\.R3 no longer exists/.test(i1.issues[0].why), i1.issues[0] && i1.issues[0].why);
  const sd2 = clone(seed), b26 = beatOf('2.R6'); sd2.beats[beatOf('1.R6')].marks.push({ name: 'S1.CHARGE', rel: 'start' });
  const i2 = {}, s2 = M.scoreMarks(score, S, sd2, i2);
  check('a mark placed twice: the first one in the piece counts, and it says so', near(s2['S1.CHARGE'], S.t[b26][0]) === false && near(s2['S1.CHARGE'], S.t[beatOf('1.R6')][0]) && i2.issues.some(x => x.mark === 'S1.CHARGE' && /placed twice/.test(x.why)), i2.issues.map(x => x.why).join(' | '));
  const sd3 = clone(seed); sd3.beats.bt_gone = { key: '7.7', marks: [{ name: 'SHARE.ASK', rel: 'start' }] }; sd3.beats[beatOf('1.1')].marks.push({ name: 'GATE.BELL', rel: 'el', el: 'x' });
  const i3 = {}; M.scoreMarks(score, S, sd3, i3);
  check('a seed moment that is not in the score, a name Unreal does not emit: said, never placed', i3.issues.some(x => x.beat === 'bt_gone' && /moment 7\.7 no longer exists/.test(x.why)) && i3.issues.some(x => x.mark === 'GATE.BELL'), i3.issues.length + ' issues');
  check('no seed: only the end', JSON.stringify(Object.keys(M.scoreMarks(score, S, null))) === '["OBRA.END"]');
  check('in/sub/preview relations give no time (the moment is inside the span, not on the mark)', !('HALL.1.6' in sm) && !Object.keys(sm).some(n => /^HALL\.1\./.test(n)));
}

console.log('schema 3: the marks live in the score (beats[].marks), the seed is not read');
{
  const c = clone(score); c.schema = 3;
  for (const [b, x] of Object.entries(seed.beats)) if (c.beats[b]) c.beats[b].marks = clone(x.marks);
  const i = {}, a = M.scoreMarks(c, S, null, i), b = M.scoreMarks(score, S, seed);
  check('the same marks at the same times as from the seed', i.from === 'score' && JSON.stringify(a) === JSON.stringify(b));
  const c2 = clone(c); c2.beats[beatOf('2.R5')].marks = [{ name: 'S1.BEGIN', rel: 'el', el: elIn('2.R5', 'G_HEARTDONE') || Object.keys(c2.elements).find(id => c2.elements[id].beat === beatOf('2.R5')), edge: 'end' }];
  const e = c2.beats[beatOf('2.R5')].marks[0].el;
  check('an el mark on an element\'s end uses its end', near(M.scoreMarks(c2, S, null)['S1.BEGIN'], S.t[e][1]), score.elements[e].key);
  check('a seed given to a schema 3 score is ignored', JSON.stringify(M.scoreMarks(c, S, { beats: {} })) === JSON.stringify(a));
  // lote 5 step 4: a score upgraded to schema 3 but not bound to Unreal yet carries no marks: the run lane must not go blank
  const u = clone(score); u.schema = 3; const iu = {}, au = M.scoreMarks(u, S, seed, iu);
  check('a schema 3 that carries no marks yet (upgraded, not bound) still reads the seed: the same marks as schema 2', iu.from === 'seed' && JSON.stringify(au) === JSON.stringify(b) && Object.keys(au).length === 43, iu.from);
  u.beats[beatOf('1.1')].marks = [];
  check('  an empty list is no marks either', M.scoreMarks(u, S, seed, iu) && iu.from === 'seed');
}

console.log((live ? 'the live seed obra/score/seed/marks-v1.json' : 'the seed as generated (frozen copy tools/score/fixtures/marks-seed-v1.json)') + ' (design A §3.4, pending the owner\'s review)');
{
  const B = seed.beats, ids = Object.keys(B), c = counts(B);
  check('status says it waits for the owner\'s review, and lists what he decides', seed.status === 'proposed, pending owner review' && seed.version === 1 && Array.isArray(seed.review) && seed.review.length >= 3);
  check('73 moments, every moment of the score, keyed by moment id, in the order of the piece', ids.length === 73 && JSON.stringify(ids) === JSON.stringify(score.acts.flatMap(a => a.beats)), ids.length);
  check('35 start · 4 el · 4 in · 27 sub · 3 preview, plus 3 marks on elements', c.start === 35 && c.el === 4 && c.in === 4 && c.sub === 27 && c.preview === 3 && c.extra === 3, JSON.stringify(c));
  check('each moment\'s key is its key in the score', ids.every(b => score.beats[b] && score.beats[b].key === B[b].key));
  const all = ids.flatMap(b => B[b].marks.map((m, i) => ({ b, m, i })));
  check('every name is a mark Unreal emits; relations are start/el/in/sub/preview', all.every(x => M.isValid(x.m.name) && ['start', 'el', 'in', 'sub', 'preview'].includes(x.m.rel)));
  check('marks[0] is the moment\'s own relation; the rest are el marks on its elements', all.every(x => x.i === 0 || x.m.rel === 'el'));
  const els = all.filter(x => x.m.rel === 'el');
  check('every el mark points to an element OF ITS moment, with the key it was resolved from', els.length === 7 && els.every(x => score.elements[x.m.el] && score.elements[x.m.el].beat === x.b && score.elements[x.m.el].key === x.m.elKey && x.m.edge === 'start'), els.map(x => x.m.elKey).join(' '));
  const placed = all.filter(x => (x.m.rel === 'start' || x.m.rel === 'el') && M.isPhase(x.m.name)).map(x => x.m.name);
  check('every phase mark is placed once (42: the 41 of the run and OBRA.DISC)', placed.length === 42 && new Set(placed).size === 42, placed.length);
  check('in and sub say what addresses them in Unreal (by); preview says why', all.filter(x => x.m.rel === 'in').every(x => x.m.by && x.m.by.length) && all.filter(x => x.m.rel === 'preview').every(x => x.m.why));
  check('the Hall moments are sub of a Hall step, in order', ids.filter(b => /^HALL\.1\./.test(B[b].marks[0].name)).length === 22);
  if (!live) {
    let fresh = null, err = null; try { fresh = buildSeed(score); } catch (e) { err = e.message; }
    check('a fresh build from the table on the fixture gives the same file (tools/score/seed_marks.mjs)', fresh && JSON.stringify(fresh) === JSON.stringify(B), err || '');
  }
  check('the generator refuses a score the table does not fit (a moment of the table missing)', (() => { const x = clone(score); const b = beatOf('9.6'); x.acts.forEach(a => { a.beats = a.beats.filter(y => y !== b); }); delete x.beats[b]; for (const id in x.elements) if (x.elements[id].beat === b) delete x.elements[id]; try { buildSeed(x); return false; } catch (e) { return /moment 9\.6 of the table is not in the score/.test(e.message); } })());
}

console.log('the live seed obra/score/seed/marks-v1.json: shape only (the owner may correct it by hand; its counts: --live)');
{
  let L = null, err = null;
  const there = fs.existsSync(SEED);
  if (there) { try { L = JSON.parse(fs.readFileSync(SEED, 'utf8')); } catch (e) { err = e.message; } }
  if (!there) console.log('  (no live seed yet: node tools/score/seed_marks.mjs)');
  else {
    check('it is valid JSON (a slip by hand here makes the editor say so in Problems, not fail to open)', !!L, err || '');
    if (L) {
      const B = L.beats && typeof L.beats === 'object' ? L.beats : null;
      check('version, a status and its moments (beats keyed by moment id, each with its key and marks)', typeof L.version === 'number' && typeof L.status === 'string' && !!B && Object.values(B).every(b => b && typeof b.key === 'string' && Array.isArray(b.marks) && b.marks.length > 0));
      const all = B ? Object.values(B).flatMap(b => (b.marks || []).map((m, i) => ({ m, i }))) : [];
      const badName = all.filter(x => !M.isValid(x.m.name)).map(x => x.m.name);
      const badRel = all.filter(x => !['start', 'el', 'in', 'sub', 'preview'].includes(x.m.rel) || (x.i > 0 && x.m.rel !== 'el') || (x.m.rel === 'el' && typeof x.m.el !== 'string'));
      check('every name is a mark Unreal emits; relations start/el/in/sub/preview, the extra ones el with an element', !!B && !badName.length && !badRel.length, badName.concat(badRel.map(x => x.m.name + ':' + x.m.rel)).join(' '));
    }
  }
}

check('nothing was changed: the score, the seed and the run are as they were read', JSON.stringify(score) === before && JSON.stringify(seed) === seedBefore && JSON.stringify(TRAZA) === trBefore);
console.log(fails ? `\n${fails} FAILED` : '\nall marks cases pass');
process.exit(fails ? 1 : 0);
