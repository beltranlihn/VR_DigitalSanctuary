// F0 · Extract the narrative prototype (web/prototipo-narrativo/guion.js) into an editor score (schema 2).
// It runs guion.js in a Node vm with:
//   - the prototype's own registration + schedule code, copied verbatim from timeline.js (lines 23-81 and 84-146),
//   - the real values that affect time (STAGES, CHARGE_T, voDur, ensayo.js),
//   - an inert stand-in for everything three.js / DOM (only used inside visual closures).
// The output carries a `golden` table: start/end of every element computed by the prototype's engine, so the editor
// engine can prove it reproduces the same timing (tools/score/golden_test.mjs).
//
// It NEVER writes obra/score/score.json (the score is written only by the editor, through an import the user sees,
// can undo and saves himself). Any output path that resolves to it is refused with exit code 2. There is no --force.
// Also refused (exit 2): a path inside a folder that someone else owns (obra/unreal, web/prototipo-narrativo, obra/score other
// than score.extracted.json, tools/score/fixtures, VR_Test) and any existing file that is not an earlier extraction.
//
// Usage:
//   node tools/score/extract_v1.mjs                → obra/score/score.extracted.json (ignored by git)
//   node tools/score/extract_v1.mjs --out <path>   → that file
//   node tools/score/extract_v1.mjs --fixture      → tools/score/fixtures/f0-score.json + f0-expect.json, only if missing
//   node tools/score/extract_v1.mjs --refreeze     → rewrites both on purpose (a developer act that shows in git)
//   node tools/score/extract_v1.mjs --proto <dir>  → read the prototype from a COPY of web/prototipo-narrativo (also VVR_PROTO=<dir>):
//                                                     for tests and for trying a change to guion.js before it reaches the prototype. It
//                                                     only reads it. Never together with --fixture/--refreeze.
// f0-expect.json holds what the PROTOTYPE's engine gives on that score for the 4 simulated users (total, help lines that
// play, anchor loops); the freeze is refused if the editor engine does not give the same (fix the engine first).
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import crypto from 'node:crypto';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const LIVE = path.join(ROOT, 'obra/score/score.json');
const DEFAULT_OUT = path.join(ROOT, 'obra/score/score.extracted.json');
const F0_SCORE = path.join(ROOT, 'tools/score/fixtures/f0-score.json');
const F0_EXPECT = path.join(ROOT, 'tools/score/fixtures/f0-expect.json');
const REFUSE = 'score.json is only written by the editor: File ▸ Check guion.js for changes… brings what changed in guion.js into the score (rows you choose, undoable), and File ▸ Import score… takes a whole score.extracted.json.';
const USAGE = 'usage: node tools/score/extract_v1.mjs [--out <path>] [--proto <dir>] | --fixture | --refreeze';
const rel = p => { const r = path.relative(ROOT, p); return !r || r.startsWith('..') || path.isAbsolute(r) ? p : r.split(path.sep).join('/'); };
const fail = (code, msg) => { console.error(msg); process.exit(code); };

// ---- arguments first: nothing is computed (or written) before the output is known to be allowed ----
let out = null, fixture = false, refreeze = false, proto = process.env.VVR_PROTO || null;
const argv = process.argv.slice(2);
for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  if (a === '--out') { out = argv[++i]; if (!out || out.startsWith('--')) fail(1, '--out needs a path\n' + USAGE); }
  else if (a.startsWith('--out=')) { out = a.slice(6); if (!out) fail(1, '--out needs a path\n' + USAGE); }
  else if (a === '--proto') { proto = argv[++i]; if (!proto || proto.startsWith('--')) fail(1, '--proto needs a folder\n' + USAGE); }
  else if (a.startsWith('--proto=')) { proto = a.slice(8); if (!proto) fail(1, '--proto needs a folder\n' + USAGE); }
  else if (a === '--fixture') fixture = true;
  else if (a === '--refreeze') { fixture = true; refreeze = true; }
  else if (a === '--help' || a === '-h') { console.log(USAGE); process.exit(0); }
  else fail(1, `unknown option ${a}\n${USAGE}`);
}
if (out != null && fixture) fail(1, '--out and --fixture/--refreeze do not go together: the fixture always lives in tools/score/fixtures/\n' + USAGE);

/* the same file, however it is spelled: case (Windows, macOS), "..", a trailing dot or space or a ":stream" (Windows
   writes those to the file itself), a junction or a symlink, a hard link (same inode) */
function real(p) {
  let r = path.resolve(p);
  if (process.platform === 'win32') { const d = path.dirname(r), b = path.basename(r).split(':')[0].replace(/[. ]+$/, ''); r = path.join(d, b); }
  try { r = fs.realpathSync.native(r); }
  catch (_) { try { r = path.join(fs.realpathSync.native(path.dirname(r)), path.basename(r)); } catch (__) { /* parent missing: keep it */ } }
  return r;
}
const canon = p => (process.platform === 'win32' || process.platform === 'darwin' ? real(p).toLowerCase() : real(p));
function sameFile(a, b) {
  if (canon(a) === canon(b)) return true;
  try { const x = fs.statSync(a), y = fs.statSync(b); return !!x.ino && x.dev === y.dev && x.ino === y.ino; } catch (_) { return false; }
}
const within = (p, dir) => { const r = path.relative(canon(dir), canon(p)); return !r || (!r.startsWith('..') && !path.isAbsolute(r)); };
const OUT = out != null ? path.resolve(process.cwd(), out) : DEFAULT_OUT;
if (sameFile(OUT, LIVE)) fail(2, REFUSE);
if (!fixture && (sameFile(OUT, F0_SCORE) || sameFile(OUT, F0_EXPECT))) fail(2, 'The frozen fixture is written only with --fixture (when it is missing) or --refreeze.');
if (!fixture) {
  // folders other people or tools own: Unreal's (the Director session), the prototype (read-only), the editor's score folder
  // (copies, history; only score.extracted.json is the extractor's), the fixture, the Unreal project
  const OWNED = [['obra/unreal', 'it belongs to Unreal (the Director session)'], ['web/prototipo-narrativo', 'the narrative prototype is read-only'],
    ['obra/score', 'only score.extracted.json is the extractor\'s there'], ['tools/score/fixtures', 'the fixture is written only with --fixture or --refreeze'],
    ['VR_Test', 'it is the Unreal project']];
  const own = !sameFile(OUT, DEFAULT_OUT) && OWNED.find(([d]) => within(OUT, path.join(ROOT, d)));
  if (own) fail(2, `Not written to ${rel(real(OUT))}: ${own[1]}. Use the default (obra/score/score.extracted.json) or a path outside ${own[0]}/.`);
  // and never over a file that is not an earlier extraction (an extraction is rev 1 and was never saved by the editor)
  let st = null; try { st = fs.statSync(real(OUT)); } catch (_) { /* a new file */ }
  if (st && st.isDirectory()) fail(2, `${rel(real(OUT))} is a folder: give a file path.`);
  if (st) {
    let prev = null; try { prev = JSON.parse(fs.readFileSync(real(OUT), 'utf8')); } catch (_) { /* not JSON */ }
    const earlier = prev && prev.schema === 2 && prev.rev === 1 && prev.source && prev.source.kind === 'prototype' && prev.golden && !prev.savedBy && !prev.savedAt;
    if (!earlier) fail(2, `Not written: ${rel(real(OUT))} exists and is not an earlier extraction. Choose a new file (or move that one away first).`);
  }
}
if (fixture && !refreeze && (fs.existsSync(F0_SCORE) || fs.existsSync(F0_EXPECT)))
  fail(1, `The fixture is frozen (${rel(F0_SCORE)}, ${rel(F0_EXPECT)}): nothing written. Rewrite it on purpose with --refreeze.`);

// ---- the extraction (unchanged since F0) ----
const WEB = proto ? path.resolve(process.cwd(), proto) : path.join(ROOT, 'web/prototipo-narrativo');
if (proto && !fs.existsSync(path.join(WEB, 'guion.js'))) fail(1, `--proto ${proto}: there is no guion.js in that folder`);
const read = f => fs.readFileSync(path.join(WEB, f), 'utf8');

const timeline = read('timeline.js').split('\n');
const REG = timeline.slice(22, 81).join('\n');      // act, beatTL, clip, vo, fx, hap, amb, walk, gate, ghostSpan, refNode, parseAt, resolveAll
const SCHED = timeline.slice(83, 146).join('\n');   // EDITS, tStart, tEnd, tDur, warp, computeSchedule
const world = read('world.js');
const pick = (src, re) => { const m = src.match(re); if (!m) throw new Error('not found in world.js: ' + re); return m[0]; };
const WORLD_REAL = [
  pick(world, /const clamp = [^\n]+/), pick(world, /const lerp = [^\n]+/), pick(world, /const smooth = [^\n]+/),
  pick(world, /const ease = [^\n]+/), pick(world, /const TAU = [^\n]+/),
  pick(world, /const STAGES = \[[\s\S]*?\n\];/), pick(world, /const CHARGE_T = [^\n]+/), pick(world, /const CHARGE_HOLD = [^\n]+/),
  pick(world, /const HALL = [^\n]+/), pick(world, /const EYE = [^\n]+/), pick(world, /function voDur\(text\) [^\n]+/),
].join('\n');

// an inert value: any property, call or construction returns another inert value; numbers read as 0
function inert() {
  const f = function () {};
  return new Proxy(f, {
    get(t, k) {
      if (k === Symbol.toPrimitive) return () => 0;
      if (k === Symbol.iterator) return function* () {};
      if (k === 'length') return 0;
      if (k === 'then') return undefined;
      return inert();
    },
    apply() { return inert(); }, construct() { return inert(); }, set() { return true; }, has() { return true; },
  });
}
let OUTBOX = null;
const WARN = [];   // the prototype's console.warn (anchor loops: "Ciclo de anclas en <uid>"), collected instead of printed
const sandbox = {
  __emit: o => { OUTBOX = o; },
  console: { log: console.log, error: console.error, info: console.info, warn: (...a) => WARN.push(a.join(' ')) },
  Math, JSON, Object, Array, Number, String, Map, Set, Symbol, Error, isFinite, parseFloat, parseInt, Date,
  S: { voMode: 'both', tw: { lift: 3, glow: .45, spin: 1, gfps: 11, gecho: 4, veil: 3, travel: 1, spark: 0 }, data: {}, melody: [] },
  AUDIO: {}, audioFor: () => null, soundIdOf: c => (c.track === 'vo' ? c.key.replace(/#\d+$/, '') : c.id) || c.key,
};
const ctx = vm.createContext(new Proxy(sandbox, {
  has: () => true,
  get(t, k) { if (k in t) return t[k]; if (typeof k === 'symbol') return undefined; return (t[k] = inert()); },
  set(t, k, v) { t[k] = v; return true; },
}));

// `simulate` replays the prototype's own schedule with every wait lasting what a simulated user takes (the prototype's
// live gate length, GL[uid].dur), and reports the total, the help lines that play (its helpActive) and the anchor loops.
const code = [WORLD_REAL, read('ensayo.js'), REG, SCHED, read('guion.js'),
  `resolveAll(); computeSchedule();
   __emit({ ACTS, BEATS, CLIPS, TOTAL, simulate(wait, r4) {
     for (const c of CLIPS) if (c.gate) GL[c.uid] = { dur: wait({ expected: r4(c.dur), fw: c.gate.fw }) };
     const w0 = __warn.length; computeSchedule();
     return { total: TOTAL, help: CLIPS.filter(c => c.help && c.helpGate && c.s < c.helpGate.e - 1e-6).map(c => c.uid), warn: __warn.slice(w0),
       times: Object.fromEntries(CLIPS.map(c => [c.uid, [c.s, c.e]]).concat(BEATS.map(b => ['@' + b.uid, [b.s, b.e]]))) };
   } });`].join('\n;\n');
sandbox.__warn = WARN;
vm.runInContext(code, ctx, { filename: 'prototype-extract.js' });
const { ACTS, BEATS, CLIPS, TOTAL, simulate } = OUTBOX;

// stable ids from the prototype uid (same uid → same id on every extraction)
const hash = s => { let h1 = 0x811c9dc5, h2 = 0x9e3779b9; for (const ch of s) { const c = ch.codePointAt(0); h1 = Math.imul(h1 ^ c, 16777619) >>> 0; h2 = Math.imul(h2 ^ c, 2246822519) >>> 0; } return (h1.toString(36) + h2.toString(36)).slice(0, 10); };
const bid = b => 'bt_' + hash(b.uid), eid = c => 'el_' + hash(c.uid);
const refId = n => (n ? (n.isBeat ? bid(n) : eid(n)) : null);
const anchor = a => (a ? { ref: refId(a.ref), edge: a.edge, off: +(+a.off).toFixed(4) } : null);
const r4 = x => Math.round(x * 1e4) / 1e4;

// groups (editor order: interaction first, then picture, then sound) — tracks of the prototype map 1:1
const GROUPS = [
  ['int', 'Interaction', '#777777'], ['vo', 'Voice', '#398559'], ['ui', 'Instruction', '#7F7936'], ['obj', 'Objects', '#4E78B3'],
  ['world', 'World', '#9A6E42'], ['pawn', 'Path', '#5E6570'], ['fx', 'Sound', '#398559'], ['amb', 'Music', '#398559'], ['hap', 'Haptics', '#B34FB3'],
];
const TYPE = { vo: 'vo', fx: 'sound', amb: 'ambience', hap: 'haptic', pawn: 'path', world: 'world', obj: 'object', ui: 'instruction', int: 'interaction' };

const elements = {}, golden = {};
for (const c of CLIPS) {
  const id = eid(c);
  const type = c.gate ? 'wait' : TYPE[c.track] || c.track;
  const durMode = c.gate ? 'elastic' : c.endA ? 'until' : c.track === 'vo' ? 'audio' : (c.dur ? 'fixed' : 'instant');
  elements[id] = {
    key: c.key.replace(/#\d+$/, ''), type, group: c.track, beat: bid(c.beat), lane: null,
    at: anchor(c.at), end: anchor(c.endA),
    dur: { mode: durMode, value: r4(c.dur) },
    label: c.label, text: c.text ?? null, sound: c.id ?? (c.track === 'vo' ? c.key.replace(/#\d+$/, '') : null), note: c.note || null,
    gate: c.gate ? { expected: r4(c.dur), fw: c.gate.fw } : null,
    help: c.help ? refId(c.helpGate) : null, simOnly: !!c.simOnly,
    when: c.when ? (c.when.name || 'condition') : null, hint: c.hint || null, ghost: c.ghost || null,
    legacy: { uid: c.uid, track: c.track, behavior: !!(c.apply || c.during || c.fire || c.onStart || c.onEnd) },
  };
  golden[id] = [r4(c.s), r4(c.e)];
}
const beats = {};
for (const b of BEATS) beats[bid(b)] = { key: b.uid, title: b.title, desc: b.desc || '', act: ACTS.indexOf(b.act), at: anchor(b.at) };
for (const b of BEATS) golden[bid(b)] = [r4(b.s), r4(b.e)];

// lanes: pack each group ONCE here (persisted afterwards, never recomputed by the editor). Instants get 2 s of room for their label.
const lanes = {}, groups = [];
for (const [gid, name, hue] of GROUPS) {
  const items = CLIPS.filter(c => c.track === gid).map(c => ({ id: eid(c), s: c.s, e: Math.max(c.e, c.s + 2) })).sort((a, b) => a.s - b.s || a.e - b.e);
  const ends = [], laneIds = [];
  for (const it of items) {
    let i = ends.findIndex(e => e <= it.s + 1e-6);
    if (i < 0) { i = ends.length; ends.push(0); const lid = 'ln_' + gid + '_' + (i + 1); laneIds.push(lid); lanes[lid] = { name: name + ' ' + (i + 1), group: gid }; }
    ends[i] = it.e; elements[it.id].lane = laneIds[i];
  }
  if (!laneIds.length) { const lid = 'ln_' + gid + '_1'; laneIds.push(lid); lanes[lid] = { name: name + ' 1', group: gid }; }
  groups.push({ id: gid, name, hue, lanes: laneIds });
}

const score = {
  schema: 2, rev: 1,
  source: { kind: 'prototype', file: proto ? rel(path.join(WEB, 'guion.js')) : 'web/prototipo-narrativo/guion.js', note: 'F0 freeze of the narrative prototype. Not yet reconciled with Unreal (F3).' },
  acts: ACTS.map((a, i) => ({ id: 'act_' + i, name: a.name, beats: a.beats.map(bid) })),
  beats, groups, lanes, elements, markers: {}, notes: {},
  golden: { total: r4(TOTAL), times: golden },
};
const byType = {}; for (const e of Object.values(elements)) byType[e.type] = (byType[e.type] || 0) + 1;
const summary = () => {
  console.log(`${ACTS.length} acts · ${BEATS.length} moments · ${CLIPS.length} elements · total ${TOTAL.toFixed(1)} s`);
  console.log('by type', byType);
  console.log('lanes per group', Object.fromEntries(groups.map(g => [g.id, g.lanes.length])));
  if (WARN.length) console.log('prototype warnings:', [...new Set(WARN)].join(' · '));
};

if (!fixture) {
  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, JSON.stringify(score, null, 1));
  console.log(`wrote ${rel(OUT)}`); summary();
  if (sameFile(OUT, DEFAULT_OUT)) console.log('score.json is untouched. To bring this into the piece: File ▸ Import score… in the editor. It replaces the whole score: its card names everything that changes, and offers to keep the bookmarks, notes, accepted problems and values waiting for Unreal that this file does not have. It can be undone; you save it.');
  process.exit(0);
}

// ---- the frozen fixture: the score + what the prototype gives for the 4 simulated users ----
const Engine = createRequire(import.meta.url)(path.join(ROOT, 'web/editor-obra/app/js/engine.js'));
const loops = new Set(WARN.map(w => (w.match(/Ciclo de anclas en (\S+)/) || [])[1]).filter(Boolean));
const expect = {
  note: 'What the prototype engine gives on f0-score.json for each simulated user (schema-2 semantics): total, help lines that play (prototype uids), anchor loops, and the start and end of every element (prototype uid) and moment ("@" + its key). Written by extract_v1.mjs --fixture / --refreeze, checked by golden_test.mjs.',
  frozen: new Date().toISOString().slice(0, 10),
  guion_sha1: crypto.createHash('sha1').update(fs.readFileSync(path.join(WEB, 'guion.js'))).digest('hex'),
  totals: {}, help: {}, cycles: [], times: {},
};
for (const p of Object.keys(Engine.PERSONAS)) {
  const r = simulate(Engine.PERSONAS[p].wait, r4);
  expect.totals[p] = r4(r.total); expect.help[p] = r.help;
  expect.times[p] = Object.fromEntries(Object.entries(r.times).map(([k, v]) => [k, [r4(v[0]), r4(v[1])]]));
  for (const w of r.warn) { const m = w.match(/Ciclo de anclas en (\S+)/); if (m) loops.add(m[1]); }
}
expect.cycles = [...loops].sort();
// the editor engine has to agree before anything is frozen (otherwise the fixture would freeze a parity bug)
const uidOf = id => (score.elements[id] ? score.elements[id].legacy.uid : score.beats[id] ? score.beats[id].key : id);
const disagree = [], idByUid = {};
for (const id in score.elements) idByUid[score.elements[id].legacy.uid] = id;
for (const id in score.beats) idByUid['@' + score.beats[id].key] = id;
const idOfUid = u => idByUid[u];
for (const p of Object.keys(Engine.PERSONAS)) {
  const r = Engine.resolve(score, { persona: p });
  const help = Object.keys(r.helpActive).filter(k => r.helpActive[k]).map(uidOf);
  if (Math.abs(r.total - expect.totals[p]) > 1e-3) disagree.push(`${p}: total ${r.total.toFixed(4)} (editor) vs ${expect.totals[p]} (prototype)`);
  if (JSON.stringify(help.slice().sort()) !== JSON.stringify(expect.help[p].slice().sort())) disagree.push(`${p}: help ${help.join(',')} (editor) vs ${expect.help[p].join(',')} (prototype)`);
  const cyc = r.cycles.map(uidOf).sort();
  if (JSON.stringify(cyc) !== JSON.stringify(expect.cycles)) disagree.push(`${p}: loops ${cyc.join(',')} (editor) vs ${expect.cycles.join(',')} (prototype)`);
  const off = Object.entries(expect.times[p]).filter(([u, [s, e]]) => { const id = idOfUid(u); return !r.t[id] || Math.abs(r.t[id][0] - s) > 1e-3 || Math.abs(r.t[id][1] - e) > 1e-3; });
  if (off.length) disagree.push(`${p}: ${off.length} of ${Object.keys(expect.times[p]).length} times differ (first: ${off[0][0]})`);
}
if (disagree.length) fail(1, 'Not frozen: the editor engine and the prototype disagree on this extraction. Fix the engine first.\n  ' + disagree.join('\n  '));
fs.mkdirSync(path.dirname(F0_SCORE), { recursive: true });
fs.writeFileSync(F0_SCORE, JSON.stringify(score, null, 1));
// the times block is long: one line per element ([start, end]) instead of one per number
fs.writeFileSync(F0_EXPECT, JSON.stringify(expect, null, 1).replace(/\[\s+(-?[\d.eE+-]+),\s+(-?[\d.eE+-]+)\s+\]/g, '[$1, $2]') + '\n');
console.log(`${refreeze ? 'refroze' : 'froze'} ${rel(F0_SCORE)} and ${rel(F0_EXPECT)}`); summary();
console.log('totals', expect.totals, '· loops', expect.cycles.join(', '), '· help (slow)', expect.help.slow.length);
