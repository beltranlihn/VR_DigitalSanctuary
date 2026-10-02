// F0 · Extract the narrative prototype (web/prototipo-narrativo/guion.js) into the editor score (schema 2).
// It runs guion.js in a Node vm with:
//   - the prototype's own registration + schedule code, copied verbatim from timeline.js (lines 23-81 and 84-146),
//   - the real values that affect time (STAGES, CHARGE_T, voDur, ensayo.js),
//   - an inert stand-in for everything three.js / DOM (only used inside visual closures).
// Output: obra/score/score.json (the score) — with a `golden` table: start/end of every element computed by the
// prototype's engine, so the editor engine can prove it reproduces the same timing (tools/score/golden_test.mjs).
// Usage: node tools/score/extract_v1.mjs
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const WEB = path.join(ROOT, 'web/prototipo-narrativo');
const OUT = path.join(ROOT, 'obra/score/score.json');
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
const sandbox = {
  __emit: o => { OUTBOX = o; },
  console, Math, JSON, Object, Array, Number, String, Map, Set, Symbol, Error, isFinite, parseFloat, parseInt, Date,
  S: { voMode: 'both', tw: { lift: 3, glow: .45, spin: 1, gfps: 11, gecho: 4, veil: 3, travel: 1, spark: 0 }, data: {}, melody: [] },
  AUDIO: {}, audioFor: () => null, soundIdOf: c => (c.track === 'vo' ? c.key.replace(/#\d+$/, '') : c.id) || c.key,
};
const ctx = vm.createContext(new Proxy(sandbox, {
  has: () => true,
  get(t, k) { if (k in t) return t[k]; if (typeof k === 'symbol') return undefined; return (t[k] = inert()); },
  set(t, k, v) { t[k] = v; return true; },
}));

const code = [WORLD_REAL, read('ensayo.js'), REG, SCHED, read('guion.js'),
  `resolveAll(); computeSchedule();
   __emit({ ACTS, BEATS, CLIPS, TOTAL });`].join('\n;\n');
vm.runInContext(code, ctx, { filename: 'prototype-extract.js' });
const { ACTS, BEATS, CLIPS, TOTAL } = OUTBOX;

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
  source: { kind: 'prototype', file: 'web/prototipo-narrativo/guion.js', note: 'F0 freeze of the narrative prototype. Not yet reconciled with Unreal (F3).' },
  acts: ACTS.map((a, i) => ({ id: 'act_' + i, name: a.name, beats: a.beats.map(bid) })),
  beats, groups, lanes, elements, markers: {}, notes: {},
  golden: { total: r4(TOTAL), times: golden },
};
fs.mkdirSync(path.dirname(OUT), { recursive: true });
fs.writeFileSync(OUT, JSON.stringify(score, null, 1));
const byType = {}; for (const e of Object.values(elements)) byType[e.type] = (byType[e.type] || 0) + 1;
console.log(`score.json · ${ACTS.length} acts · ${BEATS.length} moments · ${CLIPS.length} elements · total ${TOTAL.toFixed(1)} s`);
console.log('by type', byType);
console.log('lanes per group', Object.fromEntries(groups.map(g => [g.id, g.lanes.length])));
