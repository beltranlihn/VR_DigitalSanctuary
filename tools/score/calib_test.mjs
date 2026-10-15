// calib_test.mjs — the score against the last Unreal run (lote 5 design A §6): alignment, segments, sections, the problems
// (C3.TRACE.*), the stale and simulated cases, the noise of several runs, and what the "Unreal run" lane draws.
// Logic: web/editor-obra/app/js/calib.js (+ marks.js). On the frozen fixture with the frozen run of 2 Oct 18:59
// (tools/score/fixtures/traza-20261002.json) it pins the numbers measured on 2026-10-02 (design A §6.3). Writes nothing.
//   node tools/score/calib_test.mjs [--live]     (--live: the live score; the pinned numbers are skipped)
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { testScore, ROOT } from './test_score.mjs';
const require = createRequire(import.meta.url);
const E = require(path.join(ROOT, 'web/editor-obra/app/js/engine.js'));
const M = require(path.join(ROOT, 'web/editor-obra/app/js/marks.js'));
const C = require(path.join(ROOT, 'web/editor-obra/app/js/calib.js'));
const { score, live, name: SRC } = testScore();
console.log('on the ' + SRC);
const TRAZA = JSON.parse(fs.readFileSync(path.join(ROOT, 'tools/score/fixtures/traza-20261002.json'), 'utf8'));
// the seed as generated (frozen copy, tools/score/fixtures/marks-seed-v1.json): the owner's corrections to the live seed never
// break the pinned numbers; --live reads the live seed (obra/score/seed/marks-v1.json) with the live score
const SEED = JSON.parse(fs.readFileSync(path.join(ROOT, live ? 'obra/score/seed/marks-v1.json' : 'tools/score/fixtures/marks-seed-v1.json'), 'utf8'));
const LIVE = { exportado: '2026-10-02T18:06:10', hash: '54ef5a851e4b', valores: { Fundido_Dur: 3.5, Sim_EtapaMax: 90 } };   // the export of that day, frozen
const before = JSON.stringify(score);
let fails = 0;
const check = (name, ok, info) => { console.log((ok ? '  ok   ' : '  FAIL ') + name + (info ? '  · ' + info : '')); if (!ok) fails++; };
const f1 = v => v == null ? 'null' : (Math.round(v * 10) / 10).toFixed(1);
const clone = o => JSON.parse(JSON.stringify(o));
const S = E.resolve(score, { persona: 'typical' });
const run = (o = {}) => {
  const sc = o.score || score, sd = o.seed || SEED, tr = o.traza || TRAZA, lv = o.live === undefined ? LIVE : o.live;
  const info = {}, sm = M.scoreMarks(sc, o.score ? E.resolve(sc, { persona: 'typical' }) : S, sd, info);
  const cmp = C.compare(sm, M.traceMarks(tr, lv), { info: M.traceInfo(tr), live: lv });
  return { cmp, issues: info.issues, P: C.problems(cmp, Object.assign({ issues: info.issues }, o.popt || {})) };
};
const sec = (cmp, id) => cmp.sections.find(s => s.id === id);
const row = (cmp, m) => cmp.rows.find(r => r.mark === m);
const { cmp, P } = run();

console.log('alignment and the whole piece');
{
  check('aligned at the Hall start: score 23.0 s, run 3.18 s → offset 19.82 s', f1(cmp.offset * 10) === '198.2' && cmp.align === 'HALL.START', cmp.offset.toFixed(3));
  check('comparable: speed 1, the director clock', cmp.comparable && cmp.info.speed === 1 && cmp.info.clock === 'director');
  check('41 rows, one per mark of the run, each with its segment to the next (the last one to the end)', cmp.rows.length === 41 && cmp.rows.every(r => r.segTrace != null) && cmp.rows[40].mark === 'FINAL.FADE' && cmp.rows[40].to === 'OBRA.END');
  check('nothing missing on either side (OBRA.DISC is not asked of a run without disclaimer)', cmp.missing.length === 0 && cmp.extra.length === 0, JSON.stringify([cmp.missing, cmp.extra]));
  const sumSec = cmp.sections.reduce((a, s) => a + s.d, 0);
  check('the seven sections add up to the whole', cmp.sections.length === 7 && Math.abs(sumSec - cmp.total.d) < 1e-6, f1(sumSec));
  if (!live) check('Hall → end: score 995.0 s, Unreal run 1019.7 s, −24.7 s (design A §0)', f1(cmp.total.score) === '995.0' && f1(cmp.total.trace) === '1019.7' && f1(cmp.total.d) === '-24.7', `${f1(cmp.total.score)} vs ${f1(cmp.total.trace)}`);
  check('the pill: "Unreal run · −24.7 s"', live || C.pillText(cmp) === 'Unreal run · −24.7 s', C.pillText(cmp));
  check('the lane header: "Unreal run · 2 Oct 18:59 · speed 1 · simulated"', C.runLabel(cmp.info) === 'Unreal run · 2 Oct 18:59 · speed 1 · simulated' && C.runLabel(cmp.info, { short: true }) === 'Unreal run · 2 Oct 18:59', C.runLabel(cmp.info));
}

if (!live) {
  console.log('per section (design A §6.3, measured 2026-10-02): pinned');
  const want = { HALL: ['177.3', '176.3', '1.0'], S0: ['157.4', '141.8', '15.6'], S1: ['83.8', '178.0', '-94.2'], S2: ['105.1', '108.3', '-3.1'], S3: ['164.3', '130.9', '33.4'], S4: ['111.0', '123.5', '-12.5'], FINAL: ['196.0', '160.9', '35.1'] };
  for (const [id, [a, b, d]] of Object.entries(want)) {
    const s = sec(cmp, id);
    check(`${s ? s.name : id}: ${a} s here, ${b} s in the run (${d})`, s && f1(s.score) === a && f1(s.trace) === b && f1(s.d) === d, s && `${f1(s.score)} · ${f1(s.trace)} · ${f1(s.d)}`);
  }
  check('Attracting and Surrounding hold the simulated mechanic; the others do not', ['S3', 'S4'].every(id => sec(cmp, id).sim) && ['HALL', 'S0', 'S1', 'S2', 'FINAL'].every(id => !sec(cmp, id).sim));

  console.log('per segment (design A §6.2): the run side is identical; the score side differs only where the seed places S<K>.INTRO');
  // [mark, score seg, run seg]. Design A §6.2 measured S<K>.INTRO at ALMA_MOVE (Alma goes aside, inside R2); the seed follows
  // the table of design A §2 (S<K>.INTRO = the start of R4), so S<K>.ALMA and S<K>.INTRO segments move by 1-2 s (owner review)
  const SEG = [['HALL.START', '177.3', '176.3'], ['S0.OPEN', '5.7', '5.5'], ['S0.ALMA', '12.1', '11.5'], ['S0.INTRO', '6.8', '8.5'], ['S0.BEGIN', '106.0', '89.1'], ['S0.OUTRO', '2.0', '6.8'], ['S0.CHARGE', '10.4', '10.8'], ['S0.BYE', '14.3', '9.7'],
    ['S1.OPEN', '6.0', '5.5'], ['S1.ALMA', '9.4', '6.7'], ['S1.INTRO', '0.0', '6.0'], ['S1.BEGIN', '42.2', '134.5'], ['S1.OUTRO', '2.0', '5.8'], ['S1.CHARGE', '10.4', '10.8'], ['S1.BYE', '13.8', '8.8'],
    ['S2.OPEN', '6.0', '5.5'], ['S2.ALMA', '7.7', '10.8'], ['S2.INTRO', '0.0', '6.0'], ['S2.BEGIN', '63.8', '60.0'], ['S2.OUTRO', '2.0', '6.0'], ['S2.CHARGE', '10.4', '10.8'], ['S2.BYE', '15.1', '9.2'],
    ['S3.OPEN', '6.0', '5.5'], ['S3.ALMA', '10.4', '7.3'], ['S3.INTRO', '15.5', '7.3'], ['S3.BEGIN', '105.7', '90.0'], ['S3.OUTRO', '2.0', '3.2'], ['S3.CHARGE', '10.4', '10.8'], ['S3.BYE', '14.3', '6.8'],
    ['S4.OPEN', '6.0', '5.5'], ['S4.ALMA', '14.0', '13.3'], ['S4.INTRO', '0.0', '0.6'], ['S4.BEGIN', '80.5', '90.0'], ['S4.OUTRO', '2.0', '2.5'], ['S4.CHARGE', '8.5', '11.6'],
    ['FINAL.DARK', '3.5', '0.3'], ['FINAL.RETURN', '29.3', '15.1'], ['FINAL.RESULTS', '79.7', '80.7'], ['FINAL.EXIT', '10.5', '1.3'], ['FINAL.CREDITS', '68.0', '60.0'], ['FINAL.FADE', '5.0', '3.5']];
  const bad = SEG.filter(([m, a, b]) => { const r = row(cmp, m); return !r || f1(r.segScore) === 'null' || f1(r.segScore) !== a || f1(r.segTrace) !== b; });
  check('the 41 segments, score and run, to 0.1 s', bad.length === 0 && SEG.length === 41, bad.map(([m]) => { const r = row(cmp, m); return `${m} ${r ? f1(r.segScore) + '/' + f1(r.segTrace) : 'none'}`; }).join(' · '));
  const D62 = { 'S0.ALMA': '10.1', 'S0.INTRO': '8.9', 'S1.ALMA': '11.3', 'S1.INTRO': '-2.0', 'S2.ALMA': '9.8', 'S2.INTRO': '-2.1', 'S3.ALMA': '8.8', 'S3.INTRO': '17.1', 'S4.ALMA': '13.0', 'S4.INTRO': '1.0' };
  const moved = SEG.filter(([m, a]) => D62[m] && D62[m] !== a);
  check('exactly the 10 ALMA/INTRO score segments differ from §6.2; their pairs still add up to the same', moved.length === 10 && [0, 1, 2, 3, 4].every(K => { const r = (m, k) => +SEG.find(x => x[0] === `S${K}.${m}`)[k]; return Math.abs((r('ALMA', 1) + r('INTRO', 1)) - (+D62[`S${K}.ALMA`] + +D62[`S${K}.INTRO`])) < .15; }), moved.map(x => x[0]).join(' '));
  check('the simulated rows are the mechanic of Attracting and Surrounding only', cmp.rows.filter(r => r.sim).map(r => r.mark).join(' ') === 'S3.BEGIN S4.BEGIN');
  check('each row knows its cause (design A §6.4), by the kind of mark', row(cmp, 'S1.OUTRO').cause.includes('before the charge') && row(cmp, 'S2.CHARGE').cause.includes('Carga_Dur') && row(cmp, 'FINAL.CREDITS').cause.includes('Creditos_Dur') && row(cmp, 'HALL.START').cause.includes('waits'));
}

console.log('the problems (Integrity\'s shape, filter group "Unreal run")');
{
  const st = P.filter(p => p.rule === 'C3.TRACE.STAGE');
  check('every problem is C3, grouped as "Unreal run", open, with no element of the score', P.length && P.every(p => p.ly === 'C3' && p.grp === 'run' && p.st === 'open' && /^C3\.TRACE\./.test(p.rule) && p.fp.startsWith(p.rule + '|')));
  if (!live) {
    check('6 stage warnings at 3 s: Entering, Recognizing, Loving, Attracting, Surrounding, Final (the Hall passes)', st.length === 6 && st.every(p => p.sv === 'warn') && st.map(p => p.where).join(',') === 'Entering,Recognizing,Loving,Attracting,Surrounding,Final', st.map(p => p.where).join(','));
    check('the fingerprint carries the rounded difference: C3.TRACE.STAGE|S1|-94', st.map(p => p.fp).join(' ') === 'C3.TRACE.STAGE|S0|16 C3.TRACE.STAGE|S1|-94 C3.TRACE.STAGE|S2|-3 C3.TRACE.STAGE|S3|33 C3.TRACE.STAGE|S4|-13 C3.TRACE.STAGE|FINAL|35', st.map(p => p.fp).join(' '));
    const r1 = st.find(p => p.where === 'Recognizing');
    check('in words: "Recognizing runs 83.8 s here; the last Unreal run took 178.0 s (−94.2 s)."', r1.msg === 'Recognizing runs 83.8 s here; the last Unreal run took 178.0 s (−94.2 s).', r1.msg);
    check('a simulated stage says so', /simulated: its mechanic was asked to close at 90 s/.test(st.find(p => p.where === 'Attracting').msg) && !/simulated/.test(r1.msg));
    check('Show in timeline: each one knows its span (from mark, to mark)', r1.span.join('→') === 'S1.OPEN→S2.OPEN' && st.find(p => p.where === 'Final').span.join('→') === 'FINAL.DARK→OBRA.END');
  }
  const seg = P.filter(p => p.rule === 'C3.TRACE.SEG');
  check('segment rows are info, listed only under the "Unreal run" filter (only: run), never for a simulated mechanic', seg.length > 0 && seg.every(p => p.sv === 'info' && p.only === 'run') && !seg.some(p => /^S[34]\.BEGIN$/.test(p.span[0])), seg.length + ' segments');
  if (!live) {
    check('25 segments over 1 s', seg.length === 25, seg.length);
    const s1 = seg.find(p => p.span[0] === 'S1.BEGIN');
    check('in words, with its cause: "S1 begin → S1 outro: 42.2 s here, 134.5 s in the Unreal run (−92.3 s). …"', s1 && s1.msg.startsWith('S1 begin → S1 outro: 42.2 s here, 134.5 s in the Unreal run (−92.3 s). The mechanic') && s1.fp === 'C3.TRACE.SEG|S1.BEGIN|-92', s1 && s1.msg);
  }
  const sim = P.filter(p => p.rule === 'C3.TRACE.STALE');
  check('one stale info: the run is simulated (Attracting and Surrounding asked to close at 90 s)', sim.length === 1 && sim[0].fp === 'C3.TRACE.STALE||sim' && /90 s \(Sim_EtapaMax\)/.test(sim[0].msg), sim.map(p => p.fp).join(' '));
  check('no missing marks today', !P.some(p => p.rule === 'C3.TRACE.MISSING' || p.rule === 'C3.TRACE.MARK'));
}

console.log('thresholds, accepted records and the fingerprint rule');
{
  const hi = C.problems(cmp, { xStage: 16, xSeg: 5 });
  if (!live) check('with 16 s per stage: Recognizing, Attracting, Final only; with 5 s per segment: fewer rows', hi.filter(p => p.rule === 'C3.TRACE.STAGE').map(p => p.where).join(',') === 'Recognizing,Attracting,Final' && hi.filter(p => p.rule === 'C3.TRACE.SEG').length < P.filter(p => p.rule === 'C3.TRACE.SEG').length);
  check('the defaults are the constants at the top of calib.js (3 s, 1 s)', C.X_STAGE === 3 && C.X_SEG === 1 && C.thresholds(null).xStage === 3 && C.thresholds(null).xSeg === 1);
  if (!live) {
    const acc = [{ fp: 'C3.TRACE.STAGE|S1|-94', who: 'B', reason: 'the loop A12, fixing it next' }];
    const a = C.problems(cmp, { accepted: acc }).find(p => p.where === 'Recognizing');
    check('an accepted record keeps it accepted while the difference rounds the same', a.st === 'accepted' && a.who === 'B');
    const t = clone(TRAZA); for (const f of t.fases) if (f.reloj_obra_s > 499) f.reloj_obra_s += .8;   // Recognizing 0.8 s longer in the run
    const c2 = C.compare(M.scoreMarks(score, S, SEED), M.traceMarks(t, LIVE), { info: M.traceInfo(t), live: LIVE });
    const b = C.problems(c2, { accepted: acc }).find(p => p.where === 'Recognizing');
    check('…and opens again when it moves (−94.2 → −95.0 s: C3.TRACE.STAGE|S1|-95)', b.st === 'open' && b.fp === 'C3.TRACE.STAGE|S1|-95' && f1(sec(c2, 'S1').d) === '-95.0', b.fp);
  }
}

console.log('a run that does not compare, or that the score cannot meet');
{
  const fast = clone(TRAZA); fast.speed = 4; fast.fases.forEach(f => { f.speed = 4; });
  const a = run({ traza: fast });
  check('speed 4: not comparable, no stage or segment problems, one stale info that says how to run it', !a.cmp.comparable && !a.P.some(p => /STAGE|SEG/.test(p.rule)) && a.P.some(p => p.fp === 'C3.TRACE.STALE||speed' && /--speed 1 --traza/.test(p.msg)) && C.pillText(a.cmp) === 'Unreal run · not comparable');
  const b = run({ live: Object.assign(clone(LIVE), { exportado: '2026-10-03T09:00:00', hash: 'abcdef123456' }) });
  check('a run older than the Partitura export is stale (info, still compared)', b.cmp.comparable && b.P.some(p => p.fp === 'C3.TRACE.STALE||older'));
  const h = clone(TRAZA); h.partitura_hash = '000000000000';
  const c = run({ traza: h });
  check('a run made with another DA_Partitura_Obra (partitura_hash) is stale', c.P.some(p => p.fp === 'C3.TRACE.STALE||hash' && /000000000000/.test(p.msg)) && !run().P.some(p => p.fp === 'C3.TRACE.STALE||hash'));
  const real = clone(TRAZA); real.config = { bSimulated: false, bDisclaimer: false, Speed: 1 };
  const d = run({ traza: real });
  check('a real run (bSimulated false): nothing simulated, the mechanics of Attracting and Surrounding are compared', !d.cmp.rows.some(r => r.sim) && !d.P.some(p => p.fp === 'C3.TRACE.STALE||sim') && d.P.some(p => p.rule === 'C3.TRACE.SEG' && p.span[0] === 'S3.BEGIN'));
  const nolive = run({ live: null });
  check('without the Partitura export: no end of the run, the final is not compared, and it says why', !nolive.cmp.sections.some(s => s.id === 'FINAL') && nolive.cmp.total === null && nolive.P.some(p => p.fp === 'C3.TRACE.STALE||end') && C.pillText(nolive.cmp) === 'Unreal run');
  const disc = clone(TRAZA); disc.config = { bDisclaimer: true };
  check('a run with the disclaimer on but no phase 16: OBRA.DISC is missing from it', run({ traza: disc }).P.some(p => p.fp === 'C3.TRACE.MISSING|OBRA.DISC|run'));
  const cut = clone(TRAZA); cut.fases = cut.fases.filter(f => f.fase !== 13);
  const e = run({ traza: cut });
  check('a run that never reached the Hall exit: missing (info), and results → credits is one segment', e.P.some(p => p.fp === 'C3.TRACE.MISSING|FINAL.EXIT|run' && /never reached Hall exit/.test(p.msg)) && row(e.cmp, 'FINAL.RESULTS').to === 'FINAL.CREDITS');
  const noHall = clone(TRAZA); noHall.fases = noHall.fases.filter(f => f.fase !== 9);
  const g = run({ traza: noHall });
  check('a run without the Hall start: nothing to align it with', !g.cmp.comparable && g.cmp.offset === null && g.cmp.rows.length === 0 && g.P.some(p => p.fp === 'C3.TRACE.STALE||align'));
  const noSeed = run({ seed: { beats: {} } });
  check('a score without marks (no seed, schema 2): nothing to align, it says where the seed is', !noSeed.cmp.comparable && noSeed.P.some(p => /marks-v1\.json/.test(p.msg)));
  const sd = clone(SEED); for (const b of Object.values(sd.beats)) b.marks = b.marks.filter(m => m.name !== 'S2.BEGIN' || m.rel !== 'el');
  const f = run({ seed: sd });
  check('a mark the score does not place (S2.BEGIN): said, and S2 intro runs to S2 outro', f.P.some(p => p.fp === 'C3.TRACE.MISSING|S2.BEGIN|score') && row(f.cmp, 'S2.INTRO').to === 'S2.OUTRO' && !row(f.cmp, 'S2.BEGIN'));
  if (!live) {
    const sc = clone(score); const cell = Object.keys(sc.elements).find(id => sc.elements[id].key === 'CELL_IN'); delete sc.elements[cell];
    const k = run({ score: sc });
    const p = k.P.find(x => x.fp === 'C3.TRACE.MISSING|S2.BEGIN|score');
    check('…and when its element was deleted, the problem says why and points to the moment', p && /CELL_IN in moment 3\.R3 no longer exists/.test(p.msg) && sc.beats[p.el] && sc.beats[p.el].key === '3.R3', p && p.msg);
  }
  // a stage mark lost by a delete (review of lote 5): the stage warnings never just disappear
  {
    const sc = clone(score), v2 = Object.keys(sc.beats).find(b => sc.beats[b].key === 'V2');
    const env = Object.keys(sc.elements).find(id => sc.elements[id].beat === v2 && sc.elements[id].key === 'ENV_SWAP');
    delete sc.elements[env];
    const k = run({ score: sc }), W = k.P.filter(x => x.rule === 'C3.TRACE.STAGE');
    const lost = W.filter(x => /\|lost:/.test(x.fp));
    check('deleting ENV_SWAP of V2 (it carries S2 open): Recognizing and Loving warn "can no longer be compared", not silence', !!env && lost.length === 2 && lost.map(x => x.where).join(',') === 'Recognizing,Loving'
      && lost.every(x => x.sv === 'warn' && x.st === 'open' && /S2 open/.test(x.msg) && /can no longer be compared/.test(x.msg) && x.fp === 'C3.TRACE.STAGE|' + (x.where === 'Recognizing' ? 'S1' : 'S2') + '|lost:S2.OPEN'), lost.map(x => x.fp + ' · ' + x.msg).join(' | '));
    check('…the moment it was in is shown (Show), and its cause is said', lost.every(x => x.el === v2 && /ENV_SWAP in moment V2 no longer exists/.test(x.msg)));
    check('…the other stages are still measured: the stage warnings keep their count', W.length === P.filter(x => x.rule === 'C3.TRACE.STAGE').length && k.cmp.unmeasured.map(u => u.id).join(',') === 'S1,S2', W.length);
    check('a section the run never measured is not "lost" (only MISSING run, info)', run({ traza: Object.assign(clone(TRAZA), { fases: TRAZA.fases.filter(f => !(f.fase === 0 && f.etapa === 2)) }) }).cmp.unmeasured.length === 0);
  }
}

console.log('two runs or more: the noise between them raises the thresholds, never lowers them');
{
  const t1 = M.traceMarks(TRAZA, LIVE);
  check('one run: no noise, the thresholds stay', C.noise([t1]) === null && C.thresholds(C.noise([t1])).xSeg === 1);
  const z = C.noise([t1, t1]);
  check('two identical runs: noise 0, thresholds 3 s / 1 s', z.runs === 2 && z.seg === 0 && z.stage === 0 && C.thresholds(z).xSeg === 1 && C.thresholds(z).xStage === 3);
  const t2 = t1.map(m => Object.assign({}, m, { t: m.t + (M.rank(m.mark) > M.rank('S1.BEGIN') ? .5 : 0) }));   // the heart stage 0.5 s longer
  const n = C.noise([t1, t2]), th = C.thresholds(n);
  check('0.5 s apart on one segment: σ = 0.35 s, so 3σ = 1.06 s per segment; the stage threshold stays 3 s', Math.abs(n.seg - .5 / Math.SQRT2) < 1e-6 && Math.abs(th.xSeg - 1.5 / Math.SQRT2) < 1e-6 && th.xStage === 3, `σ ${n.seg.toFixed(3)} · xSeg ${th.xSeg.toFixed(3)}`);
  const withN = C.problems(cmp, { noise: n }).filter(p => p.rule === 'C3.TRACE.SEG').length, without = P.filter(p => p.rule === 'C3.TRACE.SEG').length;
  check('with that noise fewer segments are reported', withN <= without, `${without} → ${withN}`);
}

console.log('what the "Unreal run" lane draws (seconds; ui.js turns them into pixels)');
{
  const L = C.lane(cmp, 'mark');
  check('one tick per mark plus the end (42), on the score\'s marks', L.filter(x => x.kind === 'tick').length === 42 && L.filter(x => x.kind === 'tick').every(x => x.mark === 'OBRA.END' ? x.s === cmp.marks['OBRA.END'] : x.s === cmp.marks[x.mark]));
  if (!live) {
    const b = L.filter(x => x.row && x.row.mark === 'S1.BEGIN');
    check('S1 begin: the bar runs to the score\'s next mark (6:55.3), then an overrun to 8:27.6 (134.5 s after 6:13.1)', b.length === 2 && b[0].kind === 'bar' && f1(b[0].s) === '373.1' && f1(b[0].e) === '415.3' && b[1].kind === 'over' && f1(b[1].e) === '507.6' && b[1].big, b.map(x => x.kind + ' ' + f1(x.s) + '-' + f1(x.e)).join(' · '));
    const g = L.filter(x => x.row && x.row.mark === 'S0.BEGIN');
    check('S0 begin: Unreal stops 16.9 s before the score\'s next mark: a gap, amber (over 1 s)', g.length === 2 && g[1].kind === 'gap' && f1(g[1].e - g[1].s) === '16.9' && g[1].big);
    const c = L.filter(x => x.row && x.row.mark === 'S2.CHARGE');
    check('S2 charge: 0.3 s over, drawn but not amber (under 1 s)', c.length === 2 && c[1].kind === 'over' && !c[1].big);
    check('the simulated mechanics are one hatched bar each, never amber', L.filter(x => x.kind === 'sim').map(x => x.row.mark).join(' ') === 'S3.BEGIN S4.BEGIN' && L.filter(x => x.kind === 'sim').every(x => !x.big));
    check('S1 intro: 0 s in the score, 6 s in Unreal: all of it is overrun', L.filter(x => x.row && x.row.mark === 'S1.INTRO').map(x => x.kind).join() === 'over');
  }
  const H = C.lane(cmp, 'hall'), bars = H.filter(x => x.kind === 'bar' || x.kind === 'sim');
  check('aligned at the Hall start: the run as it happened, bars end to end from 0:23', f1(bars[0].s) === '23.0' && bars.every((x, i) => i === 0 || Math.abs(x.s - bars[i - 1].e) < 1e-6) && !H.some(x => x.kind === 'over' || x.kind === 'gap'));
  check('no run: nothing to draw', C.lane(null).length === 0 && C.lane(run({ traza: (() => { const t = clone(TRAZA); t.fases = t.fases.filter(f => f.fase !== 9); return t; })() }).cmp).length === 0);
}

check('nothing was changed: the score is as it was read', JSON.stringify(score) === before);
console.log(fails ? `\n${fails} FAILED` : '\nall calibration cases pass');
process.exit(fails ? 1 : 0);
