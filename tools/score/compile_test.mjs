// compile_test.mjs — the dry-run compiler (tools/score/compile.mjs, web/editor-obra/app/js/compile.js, lote 5 design A §5 and §5.4):
// what it refuses, what it lists, where it may write and where never, and that it is the same answer twice.
// On the frozen fixture tools/score/fixtures/f0-score.json (with the frozen marks seed, the frozen cut of the idmap and the frozen Unreal
// run) so the real edits of the piece never break it; the real files are only READ at the end, and their hashes must not change.
// Everything it writes goes to a temp folder that it removes (and the paths the compiler must refuse are checked not to exist).
// Exit 1 if any case fails.
//   node tools/score/compile_test.mjs
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import crypto from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { readFixture, ROOT } from './test_score.mjs';
const require = createRequire(import.meta.url);
const J = f => require(path.join(ROOT, 'web/editor-obra/app/js', f));
const E = J('engine.js'), X = J('edits.js'), K = J('compile.js'), Pt = J('partitura.js'), R = J('reach.js');
const rd = p => JSON.parse(fs.readFileSync(path.join(ROOT, p), 'utf8'));
const clone = o => JSON.parse(JSON.stringify(o)), same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
const COMPILE = path.join(ROOT, 'tools/score/compile.mjs');
const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'vvr-compile-'));
let fails = 0;
const check = (n, ok, info) => { console.log((ok ? '  ok   ' : '  FAIL ') + n + (info ? '  · ' + info : '')); if (!ok) fails++; };
const sha = f => (fs.existsSync(f) && fs.statSync(f).isFile() ? crypto.createHash('sha1').update(fs.readFileSync(f)).digest('hex') : null);
// the catalogs that go with the fixture (frozen F0 copies), unless a case passes its own
const fxCat = args => (args.includes('--contract') ? [] : ['--contract', path.join(ROOT, 'tools/score/fixtures/contract-f0.json')])
  .concat(args.includes('--binding') ? [] : ['--binding', path.join(ROOT, 'tools/score/fixtures/binding-f0.json')]);
const cli = (args, cwd = ROOT) => { const r = spawnSync(process.execPath, [COMPILE, ...args, ...fxCat(args)], { cwd, encoding: 'utf8' }); return { code: r.status, out: r.stdout || '', err: r.stderr || '' }; };
const parse = s => { try { return JSON.parse(s); } catch (_) { return null; } };

// the real files that must come out of this exactly as they went in
const WATCH = ['obra/score/score.json', 'obra/score/seed/marks-v1.json', 'obra/unreal/contract.json', 'obra/unreal/roles.json', 'obra/unreal/idmap.json', 'obra/unreal/partitura.json', 'obra/unreal/partitura_def.json',
  'obra/unreal/partitura_binding.json', 'obra/unreal/traza.json', 'obra/unreal/perillas.json', 'tools/score/fixtures/f0-score.json', 'tools/score/fixtures/marks-seed-v1.json', 'tools/score/fixtures/idmap-20261008.json'].map(f => path.join(ROOT, f));
const watch0 = WATCH.map(sha);

const fx = readFixture(), contract = rd('tools/score/fixtures/contract-f0.json'), roles = rd('obra/unreal/roles.json'), def = rd('obra/unreal/partitura_def.json'), binding = rd('tools/score/fixtures/binding-f0.json');
const seed = rd('tools/score/fixtures/marks-seed-v1.json'), idmap = rd('tools/score/fixtures/idmap-20261008.json'), traza = rd('tools/score/fixtures/traza-20261002.json');
const live = { exportado: '2026-10-02T18:06:10', hash: '54ef5a851e4b', valores: { Fundido_Dur: 3.5, Sim_EtapaMax: 90 } };   // the Unreal export of that day, as calib_test freezes it
const FIX = 'tools/score/fixtures/';
const args0 = ['--score', FIX + 'f0-score.json', '--idmap', FIX + 'idmap-20261008.json', '--seed', FIX + 'marks-seed-v1.json', '--trace', FIX + 'traza-20261002.json'];
const liveFile = path.join(TMP, 'partitura-live.json'); fs.writeFileSync(liveFile, JSON.stringify(live));
const inputs = (score, o = {}) => Object.assign({ score, contract, roles, def, binding, live, seed, idmap, trace: traza }, o);
const T = sc => E.resolve(sc, { persona: 'typical' });
const fixLoops = (sc, how = 'keep') => { let s = clone(sc); for (const k of ['2.R4', '5.R4']) { const id = Object.keys(s.beats).find(b => s.beats[b].key === k), p = X.planLoop(s, id, E); s = clone(p[how].next); } return s; };
const codes = m => m.refused.map(r => r.code + (r.key ? ' ' + r.key : '')).sort();

try {
  console.log('the piece as it is (the frozen fixture: schema 2, so the marks come from the seed)');
  {
    const r = cli([...args0, '--live', liveFile]);
    const m = parse(r.out);
    check('exit 2: compiled WITH refusals, and the manifest is printed anyway', r.code === 2 && m && m.dryRun === true && m.ok === false && m.compiler === K.VERSION, `exit ${r.code}`);
    check('  refused contains exactly E_CYCLE for 2.R4 and 5.R4 (the anchor loops of annex 18 / A12), each with the id of the moment and a sentence that says what to do', m && same(codes(m), ['E_CYCLE 2.R4', 'E_CYCLE 5.R4']) && m.refused.every(x => /^bt_/.test(x.id) && /anchor loop/.test(x.msg) && /Problems/.test(x.msg)), JSON.stringify(m && codes(m)));
    check('  the summary: 69 reach Unreal (timing) · 71 wired · 0 cue · 12 cue-ready · 440 preview (the design said 70 · 82 · 428: Reach and its test explain the 12 voices that moved)', m && same(m.summary, { elements: 592, reach: { knob: 69, wired: 71, cue: 0, cueReady: 12, preview: 440 } }), JSON.stringify(m && m.summary));
    check('  the manifest says where each input came from: the score is schema 2 rev 1 (marks from the seed), the idmap, the contract, the Partitura export, the Unreal run, the seed — each with its hash', m && m.inputs.score.schema === 2 && m.inputs.score.marksFrom === 'seed' && /^[0-9a-f]{12}$/.test(m.inputs.score.sha12) && m.inputs.idmap.generated && /^[0-9a-f]{12}$/.test(m.inputs.contract.sha12)
      && m.inputs.partitura.hash === '54ef5a851e4b' && m.inputs.trace.speed === 1 && m.inputs.trace.sim === true && m.inputs.seed.version === 1 && /pending/.test(m.inputs.seed.status), JSON.stringify(m && m.inputs).slice(0, 200));
    check('  warnings (they do not refuse): S1.BEGIN, S2.BEGIN and S4.BEGIN are at the same time as their INTRO (the loops, and the owner\'s question about 3.R3)', m && same(m.warnings.map(w => w.code + ' ' + w.mark).sort(), ['W_MARK_TIE S1.BEGIN', 'W_MARK_TIE S2.BEGIN', 'W_MARK_TIE S4.BEGIN']), JSON.stringify(m && m.warnings.map(w => w.code + w.mark)));
    check('  the 12 cues that would be (schema 2 projection): FX_GHOSTAPPEAR ×6, FX_SOULDETACH ×5, FX_SOULJOIN — in time order, each {mark, offset, action, target, asset, path}, state "not-bound"', m && m.cues.length === 12 && m.cues.every(c => c.state === 'not-bound' && c.mark && typeof c.offset === 'number' && c.action && c.asset && /^\/Game\//.test(c.path)) && same(m.cues.map(c => c.key).sort(), ['FX_GHOSTAPPEAR', 'FX_GHOSTAPPEAR', 'FX_GHOSTAPPEAR', 'FX_GHOSTAPPEAR', 'FX_GHOSTAPPEAR', 'FX_GHOSTAPPEAR', 'FX_SOULDETACH', 'FX_SOULDETACH', 'FX_SOULDETACH', 'FX_SOULDETACH', 'FX_SOULDETACH', 'FX_SOULJOIN']), m && m.cues.map(c => c.key + '@' + c.mark).join(' '));
    check('  wired: 71, each with the contract entry that says so and who owns it; preview: 440, each with the first reason', m && m.wired.length === 71 && m.wired.every(w => w.owner && w.why) && m.preview.length === 440 && m.preview.every(p => p.why), m && `${m.wired.length} / ${m.preview.length}`);
    check('  the three lists and the 69 knob elements add up to every element, once each', m && new Set([...m.cues, ...m.wired, ...m.preview].map(x => x.id)).size === 71 + 12 + 440 && m.cues.length + m.wired.length + m.preview.length + 69 === 592);
    check('  marks: where the score places each Unreal mark for the typical user, in time order; HALL.START at 23.0 (moment 1.1), OBRA.END is derived and not listed', m && m.marks.length === 42 && m.marks.every((x, i, a) => !i || a[i - 1].t <= x.t) && m.marks.find(x => x.name === 'HALL.START').t === 23 && !m.marks.some(x => x.name === 'OBRA.END') && new Set(m.marks.map(x => x.name)).size === 42, m && String(m.marks.length));
    check('  the last Unreal run, mark by mark: offset 19.8237 and the seven sections (Hall +1.0, Entering +15.6, Recognizing −94.2, Loving −3.1, Attracting +33.4, Surrounding −12.5, Final +35.1, total −24.7)', m && m.trace && m.trace.offset === 19.8237 && same(m.trace.sections.map(s => [s.name, Math.round(s.d * 10) / 10]), [['Hall', 1], ['Entering', 15.6], ['Recognizing', -94.2], ['Loving', -3.1], ['Attracting', 33.4], ['Surrounding', -12.5], ['Final', 35.1]]) && Math.round(m.trace.total.d * 10) / 10 === -24.7);
    const dr = Pt.drift(fx, T(fx), def, live, binding).rows.filter(x => !x.missing && x.diff != null && x.diff !== 0);
    check('  the knob channel: the Partitura knobs whose value in Unreal differs from what the score does — the same rows Partitura.drift gives, with the elements they measure; compile writes no proposal', m && m.knobs.length === dr.length && dr.every((x, i) => m.knobs[i].knob === x.knob && m.knobs[i].diff === Math.round(x.diff * 10000) / 10000 && same(m.knobs[i].els, x.els)), m && String(m.knobs.length));
    check('  one line for a person on stderr, the manifest alone on stdout', /^compile: refused 2 \(E_CYCLE ×2\)/.test(r.err) && r.out.trim().startsWith('{') && r.out.trim().endsWith('}'));
    const m2 = parse(cli([...args0, '--live', liveFile]).out), strip = x => { const y = clone(x); delete y.generated; return JSON.stringify(y); };
    check('deterministic: two runs give the same bytes, apart from `generated`', m2 && strip(m) === strip(m2));
    const a = K.compile(inputs(fx), { now: 't' }), b = K.compile(inputs(fx), { now: 't' });
    check('  in process too (and `now` is the only clock it reads)', JSON.stringify(a) === JSON.stringify(b) && a.generated === 't');
  }

  console.log('\nwith the two anchor loops fixed (in memory, as Problems ▸ "Fix the loop…" does it)');
  for (const how of ['keep', 'order']) {
    const sc = fixLoops(fx, how), m = K.compile(inputs(sc), { now: 't' });
    check(`"${how}": refused is empty, ok, and the cue-ready set is the 12 the design predicted`, m.ok && !m.refused.length && m.summary.reach.cueReady === 12 && m.cues.length === 12 && m.summary.reach.knob === 69 && m.summary.reach.wired === 71, JSON.stringify(m.summary.reach));
    const ties = m.warnings.filter(w => w.code === 'W_MARK_TIE').map(w => w.mark).sort();
    check(`  ties: ${how === 'keep' ? 'S1.BEGIN, S2.BEGIN, S4.BEGIN (the next moment starts together with the one before, as today)' : 'only S2.BEGIN (the owner\'s question about 3.R3); "order" separates INTRO and BEGIN of Recognizing and Surrounding'}`, same(ties, how === 'keep' ? ['S1.BEGIN', 'S2.BEGIN', 'S4.BEGIN'] : ['S2.BEGIN']), ties.join());
  }
  {
    const sc = fixLoops(fx), file = path.join(TMP, 'fixed-score.json'); fs.writeFileSync(file, JSON.stringify(sc));
    const r = cli(['--score', file, '--idmap', FIX + 'idmap-20261008.json', '--seed', FIX + 'marks-seed-v1.json', '--live', liveFile]);
    check('the command line: exit 0 when nothing is refused', r.code === 0 && parse(r.out) && parse(r.out).ok === true && /^compile: compiled · 592 elements/.test(r.err), `exit ${r.code} · ${r.err.slice(0, 90)}`);
  }

  console.log('\na score bound to Unreal (schema 3 with marks and bind): the marks are the score\'s own');
  {
    const mg = X.migrate3(fx, E, contract, { at: '2026-10-08T12:00:00.000Z', who: 'B' }), s3 = mg.next;
    const bd = X.bindUnreal(s3, seed, idmap, contract, roles, { Engine: E, gov: Pt.governedBy(s3, T(s3), binding) }), bound = bd.next;
    check('the fixture upgraded and bound in memory (the two buttons of the owner)', !!mg.next && !!bound && bd.report.ok);
    const m = K.compile(inputs(bound), { now: 't' }), m2 = K.compile(inputs(fx), { now: 't' });
    check('compile reads the marks from the score (marksFrom "score"), refuses the same two loops, and places the same marks at the same times as the seed did', m.inputs.score.marksFrom === 'score' && m2.inputs.score.marksFrom === 'seed' && same(codes(m), ['E_CYCLE 2.R4', 'E_CYCLE 5.R4']) && same(m.marks, m2.marks));
    check('  18 cue-ready now, state "no-player" (BP_ScorePlayer_SC does not exist): the 12 sounds and 6 of Alma\'s appear / disappear; 80 wired (9 more: Unreal already calls their asset)', m.summary.reach.cue === 18 && m.summary.reach.cueReady === 18 && m.cues.length === 18 && m.cues.every(c => c.state === 'no-player') && m.summary.reach.wired === 80, JSON.stringify(m.summary.reach));
    const fixed = fixLoops(bound), mf = K.compile(inputs(fixed), { now: 't' });
    check('  with the loops fixed on the bound score: ok, refused empty, the same 18', mf.ok && !mf.refused.length && mf.cues.length === 18 && mf.summary.reach.cueReady === 18, JSON.stringify(codes(mf)));
    check('  the cues are in time order and carry their action and target (Alma\'s: appear / disappear on role:Alma)', mf.cues.every((c, i, a) => !i || T(fixed).t[a[i - 1].id][0] <= T(fixed).t[c.id][0]) && mf.cues.filter(c => c.target === 'role:Alma' && /appear$/.test(c.action)).length === 6);
  }

  console.log('\nwhat it refuses, each from a minimal score made here');
  {
    const mini = (o = {}) => Object.assign({
      schema: 2, rev: 1, acts: [{ id: 'a1', name: 'Act', beats: ['b1', 'b2', 'b3'] }], groups: [{ id: 'obj', name: 'Objects', lanes: ['l1'] }, { id: 'fx', name: 'FX', lanes: ['l2'] }],
      lanes: { l1: { name: 'Objects 1', group: 'obj' }, l2: { name: 'FX 1', group: 'fx' } }, beats: { b1: { key: '1', title: 'One' }, b2: { key: '2', title: 'Two' }, b3: { key: '3', title: 'Three' } },
      elements: Object.assign(Object.fromEntries(['b1', 'b2', 'b3'].map((b, i) => ['e' + (i + 1), { key: 'OBJ_' + (i + 1), type: 'object', group: 'obj', beat: b, lane: 'l1', at: { ref: b, edge: 'start', off: 0 }, end: null, dur: { mode: 'fixed', value: 5 } }])),
        { s1: { key: 'FX_A', type: 'sound', group: 'fx', beat: 'b1', lane: 'l2', at: { ref: 'b1', edge: 'start', off: 1 }, end: null, dur: { mode: 'instant', value: 0 }, sound: 'FX_A' } }),
      markers: {}, notes: {},
    }, o);
    const sd = marks => ({ version: 1, status: 'reviewed', beats: Object.fromEntries(Object.entries(marks).map(([b, ms]) => [b, { key: b, marks: ms }])) });
    const idm = o => Object.assign({ generated: 'x', assets: { FX_A: { path: '/Game/Obra/Audio/FX_A.FX_A', cls: 'SoundWave', referencedBy: [] } }, ambiguous: {}, aliases: {} }, o);
    const run = (sc, extra = {}) => K.compile({ score: sc, contract: { entries: [] }, roles: { roles: {} }, idmap: idm(), seed: sd({ b1: [{ name: 'S0.OPEN', rel: 'start' }], b2: [{ name: 'S0.ALMA', rel: 'start' }], b3: [{ name: 'S0.INTRO', rel: 'start' }] }), ...extra }, { now: 't' });
    const base = run(mini());
    check('a minimal score with its marks in order compiles: ok, the sound is cue-ready (1 s after S0.OPEN) and the missing marks are warnings', base.ok && base.cues.length === 1 && base.cues[0].mark === 'S0.OPEN' && base.cues[0].offset === 1 && base.cues[0].asset === 'FX_A' && base.warnings.filter(w => w.code === 'W_MARK_MISSING').length > 30 && base.warnings.every(w => w.code !== 'W_NO_IDMAP'), codes(base).join());
    check('  E_MARK_UNKNOWN: a name Unreal does not emit (S9.OPEN), with the moment', (() => { const m = run(mini(), { seed: sd({ b1: [{ name: 'S9.OPEN', rel: 'start' }] }) }); return !m.ok && m.refused.some(x => x.code === 'E_MARK_UNKNOWN' && x.mark === 'S9.OPEN' && x.key === '1' && /not a mark Unreal emits/.test(x.msg)); })());
    check('  E_MARK_DUP: a phase mark placed by two moments (Unreal enters it once)', (() => { const m = run(mini(), { seed: sd({ b1: [{ name: 'S0.OPEN', rel: 'start' }], b2: [{ name: 'S0.OPEN', rel: 'start' }] }) }); return !m.ok && m.refused.some(x => x.code === 'E_MARK_DUP' && x.mark === 'S0.OPEN' && x.key === '2' && /placed twice/.test(x.msg)); })());
    check('  E_MARK_ORDER: S0.CHARGE before S0.OPEN in the score (Unreal enters them the other way round), saying which and when', (() => { const m = run(mini(), { seed: sd({ b1: [{ name: 'S0.CHARGE', rel: 'start' }], b2: [{ name: 'S0.OPEN', rel: 'start' }] }) }); return !m.ok && m.refused.some(x => x.code === 'E_MARK_ORDER' && x.mark === 'S0.CHARGE' && x.after === 'S0.OPEN' && /0:05/.test(x.msg) && /0:00/.test(x.msg)); })());
    check('  a tie is not an order error (W_MARK_TIE): two phase marks at the same time are noted, the compile goes on', (() => { const m = run(mini(), { seed: sd({ b1: [{ name: 'S0.INTRO', rel: 'start' }, { name: 'S0.BEGIN', rel: 'el', el: 'e1', edge: 'start' }] }) }); return m.ok && m.warnings.some(w => w.code === 'W_MARK_TIE' && w.mark === 'S0.BEGIN'); })());
    check('  E_MARK_ELEMENT: a mark on an element that is not in its moment (or no longer exists)', (() => { const m = run(mini(), { seed: sd({ b1: [{ name: 'S0.OPEN', rel: 'el', el: 'e3', edge: 'start' }] }) }); return !m.ok && m.refused.some(x => x.code === 'E_MARK_ELEMENT' && /no longer in/.test(x.msg)); })());
    check('  E_NO_MARKS: a score with no marks and no seed has nothing to tie a cue to', (() => { const m = run(mini(), { seed: null }); return !m.ok && m.refused.some(x => x.code === 'E_NO_MARKS') && !m.warnings.some(w => w.code === 'W_MARK_MISSING'); })());
    // E_ASSET_AMBIGUOUS needs a bound element: a schema 3 score
    const bound = mini({ schema: 3 }); bound.beats.b1.marks = [{ name: 'S0.OPEN', rel: 'start' }]; bound.elements.s1.bind = { action: 'sound', target: null, asset: 'VO_12c', branch: null };
    const amb = idm({ ambiguous: { VO_12c: [{ path: '/Game/SoulCharger/Mechanics/Breath/Audio/VO_12c.VO_12c' }, { path: '/Game/SoulCharger/Obra/Audio/VO_12c.VO_12c' }] } });
    const ma = run(bound, { idmap: amb });
    check('  E_ASSET_AMBIGUOUS: a cue-eligible sound whose name two files answer to is refused, listing both paths — never a guess', !ma.ok && ma.refused.length === 1 && ma.refused[0].code === 'E_ASSET_AMBIGUOUS' && ma.refused[0].asset === 'VO_12c' && /Breath\/Audio\/VO_12c/.test(ma.refused[0].msg) && /Obra\/Audio\/VO_12c/.test(ma.refused[0].msg) && !ma.cues.length, ma.refused[0] && ma.refused[0].msg);
    const mb = run((() => { const q = clone(bound); q.elements.s1.bind.asset = 'FX_NOWHERE'; return q; })());
    check('  an asset that is not in Content is NOT a refusal: it is honest previs (preview, naming it)', mb.ok && !mb.cues.length && mb.preview.some(p => p.key === 'FX_A' && /FX_NOWHERE is not in Unreal's Content/.test(p.why)));
    const mc = run((() => { const q = clone(bound); q.elements.s1.bind.asset = 'FX_A'; return q; })());
    check('  bound and in Content: a cue with state "no-player" and its path', mc.ok && mc.cues.length === 1 && mc.cues[0].state === 'no-player' && mc.cues[0].path === '/Game/Obra/Audio/FX_A.FX_A' && mc.inputs.score.marksFrom === 'score');
    check('  W_NO_IDMAP: without the scan of Unreal\'s assets it says so and nothing is cue-ready', (() => { const m = run(mini(), { idmap: null }); return m.ok && m.warnings.some(w => w.code === 'W_NO_IDMAP') && m.summary.reach.cueReady === 0 && m.inputs.idmap === null; })());
    // E_DANGLING: validate refuses a missing anchor first, so the check is reached only with a validator that lets it through (a stand-in)
    const dang = mini(); dang.elements.e2.at = { ref: 'gone', edge: 'start', off: 0 };
    check('  E_DANGLING: an anchor to nothing that the editor\'s own validation let through (the engine falls back, the compile refuses)', (() => { const m = K.compile({ score: dang, contract: { entries: [] }, seed: null }, { now: 't', Edits: { validate: (s, Eng) => Eng.resolve(s, { persona: 'typical' }) } }); return m.refused.some(x => x.code === 'E_DANGLING' && x.key === 'OBJ_2'); })());
    check('  a score the editor cannot read is not a verdict but a bad input (BadInput; the command line exits 1)', (() => { try { K.compile({ score: Object.assign(mini(), { schema: 4 }), contract: { entries: [] } }); return false; } catch (e) { return e instanceof K.BadInput && /schema 4/.test(e.message); } })()
      && (() => { try { K.compile({ score: mini(), contract: null }); return false; } catch (e) { return e instanceof K.BadInput && /contract/.test(e.message); } })());
    check('  nothing it was given is changed', (() => { const sc = mini(), c = JSON.stringify(sc); run(sc); return JSON.stringify(sc) === c; })());
  }

  console.log('\nthe command line: where it may write and where never');
  {
    const snap = WATCH.map(sha), mustNotExist = [];
    const refuse = (what, out, extra = []) => {
      const abs = path.resolve(ROOT, out.replace(/[. ]+$/, '').split('::')[0]);
      const existed = fs.existsSync(abs), h = sha(abs), r = cli([...args0, '--live', liveFile, '--out', out, ...extra]);
      check(`--out ${out}  (${what}): exit 1, nothing on stdout, nothing written`, r.code === 1 && r.out === '' && /Refused to write/.test(r.err) && (existed ? sha(abs) === h : !fs.existsSync(abs)), `exit ${r.code} · ${r.err.slice(0, 90).trim()}`);
      mustNotExist.push([abs, existed]);
    };
    refuse('the Unreal project', 'VR_Test/compile-test-out.json');
    refuse('a file of the Unreal project', 'VR_Test/Content/compile-test-out.uasset');
    refuse('the Director\'s and the web\'s files for Unreal', 'obra/unreal/compile-test-out.json');
    refuse('the score itself', 'obra/score/score.json');
    refuse('the score\'s folder (history, copies, the seed)', 'obra/score/compile-test-out.json');
    refuse('the seed', 'obra/score/seed/compile-test-out.json');
    refuse('a path that goes up and comes back', 'obra/unreal/../unreal/compile-test-out.json');
    refuse('the prototype (read-only)', 'web/prototipo-narrativo/compile-test-out.json');
    refuse('the frozen fixtures', 'tools/score/fixtures/compile-test-out.json');
    refuse('an Unreal asset anywhere', path.join(TMP, 'compile-test-out.uasset'));
    refuse('a folder', 'tools/score');
    if (process.platform === 'win32') {
      refuse('the same folder in another case', 'OBRA/Unreal/compile-test-out.json');
      refuse('a trailing dot (Windows writes it to the same file)', 'obra/unreal/compile-test-out.json.');
      refuse('a trailing space', 'obra/unreal/compile-test-out.json ');
      refuse('a :stream', 'obra/unreal/compile-test-out.json::$DATA');
      refuse('the score in another case', 'OBRA/SCORE/Score.JSON');
    }
    // never over one of its own inputs (the score handed in, the idmap…)
    const mine = path.join(TMP, 'score-copy.json'); fs.writeFileSync(mine, JSON.stringify(fixLoops(fx))); const h = sha(mine);
    const ri = cli(['--score', mine, '--idmap', FIX + 'idmap-20261008.json', '--seed', FIX + 'marks-seed-v1.json', '--out', mine]);
    check('--out one of its own inputs: exit 1, the input is byte for byte what it was', ri.code === 1 && /one of the inputs/.test(ri.err) && sha(mine) === h);
    const link = path.join(TMP, 'link.json'); let linked = false; try { fs.linkSync(mine, link); linked = true; } catch (_) { /* no hard links here */ }
    if (linked) { const rl = cli(['--score', mine, '--idmap', FIX + 'idmap-20261008.json', '--seed', FIX + 'marks-seed-v1.json', '--out', link]); check('  nor over a hard link to it', rl.code === 1 && /one of the inputs/.test(rl.err) && sha(mine) === h); }
    // the right place: a manifest in the temp folder (and its folders are made)
    const out = path.join(TMP, 'deep', 'er', 'manifest.json'), ok = cli([...args0, '--live', liveFile, '--out', out]);
    const wm = parse(fs.existsSync(out) ? fs.readFileSync(out, 'utf8') : 'x');
    check('--out a file outside the repo\'s data: written (its folders made), exit 2 for the loops, nothing on stdout, a person\'s line on stderr that says where', ok.code === 2 && ok.out === '' && wm && wm.dryRun === true && wm.refused.length === 2 && /wrote /.test(ok.err), `exit ${ok.code}`);
    check('  and it is the manifest that stdout would have had', same(Object.assign({}, wm, { generated: 0 }), Object.assign({}, parse(cli([...args0, '--live', liveFile]).out), { generated: 0 })));
    // bad input
    const bad = (what, args, re) => { const r = cli(args); check(`bad input: ${what} → exit 1 with the reason`, r.code === 1 && r.out === '' && re.test(r.err), r.err.slice(0, 100).trim()); };
    bad('a score that is not there', ['--score', path.join(TMP, 'nope.json')], /not there/);
    const junk = path.join(TMP, 'junk.json'); fs.writeFileSync(junk, '{ not json');
    bad('a file that is not JSON', ['--score', junk], /not valid JSON/);
    const s4 = path.join(TMP, 'schema4.json'); fs.writeFileSync(s4, JSON.stringify(Object.assign(clone(fx), { schema: 4 })));
    bad('a score the editor cannot read (schema 4)', ['--score', s4], /not valid.*schema 4/);
    bad('an option it does not have', ['--force'], /Unknown option --force/);
    bad('an option without its value', ['--out'], /needs a value/);
    bad('a contract that is not there', ['--contract', path.join(TMP, 'nope.json')], /not there/);
    // a path somebody typed that is not there is a mistake, not an absence (the default places may be missing: in process, the manifest says what it could not judge)
    bad('an optional file named on the command line that is not there (a typo must not silently drop the idmap)', [...args0, '--idmap', path.join(TMP, 'none.json')], /idmap: .* is not there/);
    const mo = K.compile({ score: fx, contract }, { now: 't' });
    check('the optional files may be missing from their default place (idmap, run, seed, Partitura): it says what it could not judge, and refuses what it cannot place', !mo.ok && mo.inputs.idmap === null && mo.inputs.trace === null && mo.inputs.seed === null && mo.inputs.partitura === null && mo.trace === null && !mo.knobs.length
      && mo.refused.some(x => x.code === 'E_NO_MARKS') && mo.warnings.some(w => w.code === 'W_NO_IDMAP'));
    check('nothing the checks above refused was created', mustNotExist.every(([p, existed]) => existed || !fs.existsSync(p)));
    check('the repo\'s data are as they were: score, seed, contract, roles, idmap, the Director\'s export, the fixtures (hashes)', same(snap, WATCH.map(sha)));
  }

  console.log('\nit knows nothing of Unreal but its files');
  {
    const src = ['tools/score/compile.mjs', 'web/editor-obra/app/js/compile.js'].map(f => fs.readFileSync(path.join(ROOT, f), 'utf8')).join('\n');
    const strip = f => fs.readFileSync(path.join(ROOT, f), 'utf8').replace(/\/\*[\s\S]*?\*\/|\/\/[^\n]*/g, ''), code = ['tools/score/compile.mjs', 'web/editor-obra/app/js/compile.js'].map(strip).join('\n'), pure = strip('web/editor-obra/app/js/compile.js');
    check('it imports nothing from tools/unreal/ and opens no network or process', !/tools\/unreal/.test(code) && !/node:(http|https|net|child_process)|\bfetch\(|require\(['"](http|https|net|child_process)['"]\)/.test(code));
    check('compile.js writes nothing: no file API at all (the command line is the only one that writes, and only its manifest)', !/\b(writeFile|writeFileSync|appendFile|mkdirSync|unlink|rmSync|createWriteStream)\b/.test(pure) && !/\brequire\(['"](node:)?fs['"]\)/.test(pure));
  }

  console.log('\nthe real files, only read (whatever they are today)');
  {
    const h = WATCH.map(sha), r = cli([]), m = parse(r.out);
    check('node tools/score/compile.mjs with no options reads obra/ and prints a manifest: exit 0 or 2, never 1, and says which marks it used', (r.code === 0 || r.code === 2) && m && m.dryRun === true && ['score', 'seed'].includes(m.inputs.score.marksFrom) && m.summary.elements > 0 && m.ok === (r.code === 0), `exit ${r.code} · ${r.err.trim().slice(0, 150)}`);
    check('  and not one of the real files changed', same(h, WATCH.map(sha)));
  }
} finally {
  fs.rmSync(TMP, { recursive: true, force: true });
}

console.log(fails ? `\n${fails} FAILED` : '\nall ok');
process.exit(fails ? 1 : 0);
