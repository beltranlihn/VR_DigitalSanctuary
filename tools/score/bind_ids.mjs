// Contract and Partitura bindings by element id (lote 5 design A §7, audit D10): a rename in the score never takes an element
// out of what Unreal knows. One-shot and re-runnable. It is not a score writer: the score is only read.
//
// What it does:
//  · obra/unreal/contract.json: each entry keeps its `match` (the RULE: documentation, and what a new or pasted element is
//    compared with) and gains the generated `ids` (+ `idKeys`, the name each element had when it was bound, and `idsFrom`:
//    which score, which day). On a re-run every rule is applied to the name Unreal knows each element by (its idKeys), so an
//    element keeps its place while it is in the score, even renamed, and a rename never moves it into another entry (VO_24
//    renamed VO_24x stays in vo.unused, never in vo.wired); one that left the score stays as an orphan (Unreal still has it)
//    unless --prune.
//    Seeding corrections, re-checked on every run against the trackers and the disk (pending the Director's ack):
//    `vo.unused` (the voices BP_Obra_SC no longer calls: tracker BP_Obra_SC.md) and `vo.noasset` (voices with no recording in
//    VR_Test/Content nor in the plugins); both leave `vo.wired` through its generated `excludeKeys`, so its rule and its ids
//    agree.
//  · obra/unreal/partitura_binding.json: each bind gains `ids` per stage ("0".."4"; "*" for one value for all stages): the
//    element(s) Partitura.measure finds (a gap: [a, b]); the origins that name an element (phase0 → ENV_SWAP) too. A frozen
//    id that still holds is kept (a rename keeps it); one that no longer holds is re-bound by key, and said.
//  · Unreal asset paths written in contract.json, roles.json and partitura_binding.json are checked against the maps of the
//    2026-10-02 moves (tools/unreal/reorden_contenido_2026-10-02.json, plugin_*_2026-10-02.json) and the disk; a path that
//    moved is rewritten (roles.json is written only then), one that cannot be mapped is reported.
// It never writes the score, partitura.json, perillas.json, traza.json, LEEME.md, VR_Test or the prototype. Nothing in the app
// writes these files: they change only by running this.
//
//   node tools/score/bind_ids.mjs            → write the files that change, print the summary
//   node tools/score/bind_ids.mjs --dry      → print the summary, write nothing
//   node tools/score/bind_ids.mjs --check    → exit 1 if a file would change
//   [--score <path>]                         → read another score (default obra/score/score.json)
//   [--prune]                                → drop the ids of elements that are no longer in the score
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';

const require = createRequire(import.meta.url);
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const Engine = require(path.join(ROOT, 'web/editor-obra/app/js/engine.js'));
const Partitura = require(path.join(ROOT, 'web/editor-obra/app/js/partitura.js'));
const Integrity = require(path.join(ROOT, 'web/editor-obra/app/js/integrity.js'));
const F = {
  contract: path.join(ROOT, 'obra/unreal/contract.json'),
  binding: path.join(ROOT, 'obra/unreal/partitura_binding.json'),
  roles: path.join(ROOT, 'obra/unreal/roles.json'),
  tracker: path.join(ROOT, '.claude/skills/unreal-vr/blueprints/BP_Obra_SC.md'),
};
const NSTAGES = 5;

/* ---------- the documented corrections (design A §7.1), [DIRECTOR] to confirm ---------- */
// the 10 voices of the BP_Obra_SC tracker ("VO viejas que quedan sin uso (no borradas)", VO v3 of 2026-10-01)
export const UNUSED = ['VO_01d', 'VO_01h', 'VO_04b', 'VO_06a', 'VO_24', 'VO_34c', 'VO_35c', 'VO_36', 'VO_36c', 'VO_36d'];
// no asset in VR_Test/Content nor in the plugins (VO_12b: "eliminada", BP_BreathStage_SC.md; the Breath help is VO_12f1/f2)
export const NOASSET = ['VO_12b', 'VO_17b', 'VO_21'];
const NEW_ENTRIES = {
  'vo.unused': keys => ({ id: 'vo.unused', match: { keys }, kind: 'not-in-unreal', owner: 'BP_Obra_SC · HallDirector',
    ev: 'BP_Obra_SC.md ("VO viejas que quedan sin uso", VO v3 of 2026-10-01)',
    on: { move: 'info', trim: 'info', delete: 'info', text: 'info' },
    msg: 'Unreal no longer plays this voice: its graphs stopped calling it (VO v3, 2026-10-01); the recording is still in Content. Here it is preview only.',
    source: 'tracker BP_Obra_SC.md, re-read by tools/score/bind_ids.mjs', pending: 'Director ack' }),
  'vo.noasset': keys => ({ id: 'vo.noasset', match: { keys }, kind: 'not-in-unreal', owner: '—',
    ev: 'Content scan (VR_Test/Content and VR_Test/Plugins) · BP_BreathStage_SC.md ("VO_12b eliminada")',
    on: { move: 'info', trim: 'info', delete: 'info', text: 'info' },
    msg: 'There is no recording of this voice in Unreal: here it is preview only.',
    source: 'Content scan by tools/score/bind_ids.mjs', pending: 'Director ack' }),
};

const sha12 = txt => crypto.createHash('sha1').update(txt).digest('hex').slice(0, 12);
const today = () => new Date().toISOString().slice(0, 10);
const clone = o => JSON.parse(JSON.stringify(o));
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
const pick = (v, K) => (v && typeof v === 'object' && !Array.isArray(v)) ? (K != null && v[K] !== undefined ? v[K] : v['*']) : v;

/* the voice list of the BP_Obra_SC tracker, or null when the line is not there */
export function trackerUnused(text) {
  const m = /VO viejas que quedan sin uso[^:\n]*:\s*([^\n]+)/.exec(text || ''); if (!m) return null;
  return m[1].trim().replace(/\.$/, '').split(',').map(x => x.trim()).filter(x => /^\w+$/.test(x)).map(x => 'VO_' + x);
}

/* every .uasset/.umap of the project: name → [mount paths] (/Game/... or /SC_x/...) */
export function scanAssets(root) {
  const out = new Map(), base = path.join(root, 'VR_Test');
  const walk = (dir, mount) => {
    let list; try { list = fs.readdirSync(dir, { withFileTypes: true }); } catch (_) { return; }
    for (const d of list) {
      if (d.isDirectory()) { if (!/^(__ExternalActors__|__ExternalObjects__|Developers|Collections)$/.test(d.name)) walk(path.join(dir, d.name), mount + '/' + d.name); continue; }
      if (!/\.(uasset|umap)$/.test(d.name)) continue;
      const n = d.name.replace(/\.(uasset|umap)$/, '');
      (out.get(n) || out.set(n, []).get(n)).push(mount + '/' + n);
    }
  };
  walk(path.join(base, 'Content'), '/Game');
  let plugins = []; try { plugins = fs.readdirSync(path.join(base, 'Plugins'), { withFileTypes: true }).filter(d => d.isDirectory()); } catch (_) {}
  for (const p of plugins) walk(path.join(base, 'Plugins', p.name, 'Content'), '/' + p.name);
  return out;
}

/* old → new asset paths of 2026-10-02, chained (moved by the reorder and then into a plugin: it ends at the plugin) */
export function pathMap(root) {
  const dir = path.join(root, 'tools/unreal'), m = new Map();
  const files = ['reorden_contenido_2026-10-02.json'].concat(fs.readdirSync(dir).filter(f => /^plugin_.*_2026-10-02\.json$/.test(f)).sort());
  for (const f of files) { const d = JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8')); for (const [a, b] of d.mover || []) m.set(a, b); }
  const end = p => { const seen = new Set(); while (m.has(p) && !seen.has(p)) { seen.add(p); p = m.get(p); } return p; };
  return { map: m, end, files };
}

/* the Unreal paths written in a JSON value (any string): one that exists is kept, one that moved is rewritten, the rest is
   reported. A folder whose assets all went to one same folder maps to it */
export function remapPaths(doc, where, ctx) {
  const RX = /\/(?:Game|SC_[A-Za-z]+)\/[A-Za-z0-9_/]+/g, changes = [], kept = [], unmapped = [];
  const exists = p => {
    const name = p.split('/').pop(); if ((ctx.assets.get(name) || []).includes(p)) return true;
    const rel = p.replace(/^\/Game\//, 'VR_Test/Content/').replace(/^\/(SC_[A-Za-z]+)\//, 'VR_Test/Plugins/$1/Content/');
    try { return fs.statSync(path.join(ctx.root, rel)).isDirectory(); } catch (_) { return false; }
  };
  const fix = s => s.replace(RX, p => {
    const q = p.replace(/\/+$/, '');
    if (exists(q)) { kept.push(where + ': ' + q); return p; }
    let to = ctx.paths.end(q);
    if (to === q) {
      const dests = new Set([...ctx.paths.map].filter(([a]) => a.startsWith(q + '/')).map(([a]) => { const e = ctx.paths.end(a); return e.slice(0, e.length - (a.length - q.length)); }));
      if (dests.size === 1) to = [...dests][0];
    }
    if (to !== q && exists(to)) { changes.push(where + ': ' + q + ' → ' + to); return to; }
    unmapped.push(where + ': ' + q); return p;
  });
  const walk = v => typeof v === 'string' ? fix(v) : Array.isArray(v) ? v.map(walk) : v && typeof v === 'object' ? Object.fromEntries(Object.entries(v).map(([k, x]) => [k, walk(x)])) : v;
  return { doc: walk(doc), changes, kept, unmapped };
}

/* ---------- the build (pure on its inputs) ----------
   in: { score, scoreText, contract, binding, unused, noasset, at, prune } → { contract, binding, report, regex0 } */
export function build(inp) {
  const { score } = inp, E = score.elements, at = inp.at || today();
  const from = { score: `rev ${score.rev} sha12 ${sha12(inp.scoreText || JSON.stringify(score))}`, at };
  const R = { entries: [], corrections: [], binds: [], origins: [] };
  const contract = clone(inp.contract);
  // every rule is applied to the name Unreal knows the element by: the one it had when it was first bound (idKeys), its key
  // otherwise. A rename in the score never moves an element from one entry to another (VO_24 renamed VO_24x stays in
  // vo.unused and never becomes a wired voice); a rule or a correction that changes does (a voice that gets its recording
  // goes back to vo.wired, renamed or not)
  const known = {};
  for (const c of contract.entries) if (Array.isArray(c.ids) && c.idKeys) for (const id of c.ids) if (known[id] == null && c.idKeys[id] != null) known[id] = c.idKeys[id];
  const asKnown = id => known[id] != null && known[id] !== E[id].key ? Object.assign({}, E[id], { key: known[id] }) : E[id];
  const byRule = c => Object.keys(E).filter(id => !E[id].isNew && Integrity.ruleMatches(c, asKnown(id)));
  const keyOf = id => (E[id] || {}).key || id, knownOf = id => known[id] != null ? known[id] : keyOf(id);
  // what the rules say before this run's corrections (for the summary and the test)
  const regex0 = Object.fromEntries(contract.entries.map(c => [c.id, byRule(c)]));

  // the corrections: two entries after vo.wired; vo.wired leaves their voices out (excludeKeys, generated)
  const fix = { 'vo.unused': (inp.unused || UNUSED).slice(), 'vo.noasset': (inp.noasset || NOASSET).slice() };
  const wired = contract.entries.find(c => c.id === 'vo.wired');
  let pos = wired ? contract.entries.indexOf(wired) + 1 : contract.entries.length;
  for (const [cid, keys] of Object.entries(fix)) {
    let c = contract.entries.find(x => x.id === cid);
    if (!c) { c = NEW_ENTRIES[cid](keys); contract.entries.splice(pos, 0, c); R.corrections.push(`new entry ${cid}: ${keys.join(', ') || '(none)'}`); }
    else if (!same((c.match || {}).keys, keys)) { R.corrections.push(`${cid}: ${((c.match || {}).keys || []).join(', ')} → ${keys.join(', ')}`); c.match = Object.assign({}, c.match, { keys }); }
    pos = contract.entries.indexOf(c) + 1;
  }
  if (wired) {
    const out = [...new Set([...fix['vo.unused'], ...fix['vo.noasset']])];
    if (!same(wired.match.excludeKeys || [], out)) { R.corrections.push(`vo.wired leaves out ${out.join(', ')}`); wired.match = Object.assign({}, wired.match, { excludeKeys: out }); }
  }

  for (const c of contract.entries) {
    const had = Array.isArray(c.ids) ? c.ids : null, was = c.idKeys || {}, inHad = new Set(had || []);
    // bound before and gone (Unreal still has it): kept as an orphan. Renamed: still judged by the name Unreal knows (byRule)
    const orphans = (had || []).filter(id => !E[id]);
    const keep = new Set(byRule(c));
    const ids = Object.keys(E).filter(id => keep.has(id)).concat(inp.prune ? [] : orphans);
    const renamed = ids.filter(id => inHad.has(id) && E[id] && was[id] != null && E[id].key !== was[id]);
    const idKeys = Object.fromEntries(ids.map(id => [id, inHad.has(id) && was[id] != null ? was[id] : knownOf(id)]));
    if (!had || !same(had, ids) || !same(c.idKeys, idKeys)) { c.ids = ids; c.idKeys = idKeys; c.idsFrom = from; }
    const r0 = regex0[c.id] || [];
    R.entries.push({ id: c.id, n: ids.length, was: had ? had.length : null,
      add: ids.filter(id => !inHad.has(id)).map(keyOf), del: (had || []).filter(id => !ids.includes(id)).map(id => was[id] || keyOf(id)),
      renamed: renamed.map(id => was[id] + ' → ' + E[id].key), orphans: orphans.map(id => was[id] || id), pruned: inp.prune ? orphans.length : 0,
      vsRegex: { lost: r0.filter(id => !ids.includes(id)).map(keyOf), gained: ids.filter(id => E[id] && !r0.includes(id)).map(keyOf) } });
  }

  // the Partitura bindings: what Partitura.measure finds with the frozen ids that still hold, by key otherwise
  const binding = clone(inp.binding), sched = Engine.resolve(score, { persona: 'typical' }), oIds = {};
  for (const b of binding.binds) {
    const ids = {}, rebound = [], missing = [];
    for (const K of b.perStage ? [...Array(NSTAGES).keys()] : [null]) {
      const k = K == null ? '*' : String(K), r = Partitura.measure(score, sched, binding, b, K);
      for (const x of (r && r.stale) || []) rebound.push(`${k}: ${x.key || x.id} (${x.why}) → ${x.nowKey || 'nothing'}`);
      if (!r || !r.els.length) { missing.push(k); continue; }
      const specs = b.m.kind === 'gap' ? [b.m.a[0], b.m.b[0]] : [pick(b.m.el, K)];
      const f = r.els.map((id, i) => specs[i] === '@beat' ? null : id);
      if (f.some(x => x)) ids[k] = b.m.kind === 'gap' ? f : f[0];
      const o = b.m.from && binding.origins[b.m.from];
      if (o && r.origin && pick(o.el, K) !== '@beat') {
        const om = oIds[b.m.from] = oIds[b.m.from] || {};
        if (om[k] && om[k] !== r.origin) throw new Error(`origin ${b.m.from} [${k}]: two elements (${om[k]}, ${r.origin})`);
        om[k] = r.origin;
      }
    }
    const has = Object.keys(ids).length, changed = !same(b.ids || null, has ? ids : null);
    if (has) b.ids = ids; else delete b.ids;
    R.binds.push({ knob: b.knob, stages: has, changed, missing, rebound });
  }
  for (const [name, o] of Object.entries(binding.origins || {})) {
    const ids = oIds[name] || null, changed = !same(o.ids || null, ids);
    if (ids) o.ids = ids; else delete o.ids;
    R.origins.push({ name, stages: ids ? Object.keys(ids).length : 0, changed });
  }
  let out = binding;
  if (R.binds.some(x => x.changed) || R.origins.some(x => x.changed) || !binding.idsFrom) {
    out = {}; for (const k of Object.keys(binding)) { if (k === 'idsFrom') continue; out[k] = binding[k]; if (k === 'verified') out.idsFrom = from; }
    if (!out.idsFrom) out.idsFrom = from;
  }
  return { contract, binding: out, report: R, regex0 };
}

/* ---------- writing: the house formats ---------- */
// contract.json: one-space indent; short arrays and short flat objects on one line; long lists of ids (and the idKeys map)
// packed, several per line
export function fmtJson(v, ind = '') {
  const prim = x => x === null || typeof x !== 'object', inner = ind + ' ', W = 110;
  const pack = items => {   // items already serialized
    const rows = [[]]; let w = 0;
    for (const x of items) { if (w + x.length > W && rows[rows.length - 1].length) { rows.push([]); w = 0; } rows[rows.length - 1].push(x); w += x.length + 2; }
    return rows.map(r => inner + r.join(', ')).join(',\n');
  };
  if (prim(v)) return JSON.stringify(v);
  if (Array.isArray(v)) {
    if (!v.length) return '[]';
    if (v.every(prim)) { const one = '[' + v.map(x => JSON.stringify(x)).join(', ') + ']'; return one.length <= W ? one : '[\n' + pack(v.map(x => JSON.stringify(x))) + '\n' + ind + ']'; }
    return '[\n' + v.map(x => inner + fmtJson(x, inner)).join(',\n') + '\n' + ind + ']';
  }
  const ks = Object.keys(v); if (!ks.length) return '{}';
  if (ks.every(k => prim(v[k]))) {
    const parts = ks.map(k => JSON.stringify(k) + ': ' + JSON.stringify(v[k])), one = '{ ' + parts.join(', ') + ' }';
    if (one.length <= W && ks.length <= 4) return one;
    if (ks.length > 4 && parts.every(p => p.length < 60)) return '{\n' + pack(parts) + '\n' + ind + '}';
  }
  return '{\n' + ks.map(k => inner + JSON.stringify(k) + ': ' + fmtJson(v[k], inner)).join(',\n') + '\n' + ind + '}';
}
const inline = v => v === null || typeof v !== 'object' ? JSON.stringify(v) : Array.isArray(v) ? '[' + v.map(inline).join(', ') + ']'
  : '{ ' + Object.entries(v).map(([k, x]) => JSON.stringify(k) + ': ' + inline(x)).join(', ') + ' }';
// partitura_binding.json keeps its hand layout (one bind or origin per line, blank lines between groups): only those lines and
// the idsFrom line change. Anything else in the layout → the plain format
export function writeBinding(text, binding) {
  const eol = /\r\n/.test(text) ? '\r\n' : '\n', lines = text.split(/\r?\n/);
  const by = new Map(binding.binds.map(b => [b.knob, b])), done = new Set(), oDone = new Set(), O = binding.origins || {};
  let inO = false;
  for (let i = 0; i < lines.length; i++) {
    if (/^\s*"origins":\s*\{\s*$/.test(lines[i])) { inO = true; continue; }
    if (inO) {
      if (/^\s*\},?\s*$/.test(lines[i])) { inO = false; continue; }
      const m = /^(\s*)"([^"]+)": \{.*?\}(,?)\s*$/.exec(lines[i]); if (m && O[m[2]]) { lines[i] = m[1] + JSON.stringify(m[2]) + ': ' + inline(O[m[2]]) + m[3]; oDone.add(m[2]); }
      continue;
    }
    const m = /^(\s*)(\{ "knob": "([^"]+)".*?)(,?)\s*$/.exec(lines[i]); if (!m || !by.has(m[3])) continue;
    lines[i] = m[1] + inline(by.get(m[3])) + m[4]; done.add(m[3]);
  }
  const fi = lines.findIndex(l => /^\s*"idsFrom":/.test(l)), vi = lines.findIndex(l => /^\s*"verified":/.test(l));
  if (binding.idsFrom) { const fl = ' "idsFrom": ' + inline(binding.idsFrom) + ','; if (fi >= 0) lines[fi] = fl; else if (vi >= 0) lines.splice(vi + 1, 0, fl); }
  if (done.size !== binding.binds.length || oDone.size !== Object.keys(O).length || (binding.idsFrom && fi < 0 && vi < 0)) return fmtJson(binding) + eol;
  const txt = lines.join(eol);
  try { if (!same(JSON.parse(txt), binding)) return fmtJson(binding) + eol; } catch (_) { return fmtJson(binding) + eol; }
  return txt;
}

/* ---------- CLI ---------- */
if (process.argv[1] && import.meta.url.toLowerCase() === pathToFileURL(path.resolve(process.argv[1])).href.toLowerCase()) {
  const argv = process.argv.slice(2), has = f => argv.includes(f), arg = f => { const i = argv.indexOf(f); return i >= 0 ? argv[i + 1] : null; };
  const scorePath = path.resolve(ROOT, arg('--score') || 'obra/score/score.json');
  // --contract / --binding: other catalogs than obra/unreal/ (the tests use the frozen F0 copies in tools/score/fixtures)
  if (arg('--contract')) F.contract = path.resolve(ROOT, arg('--contract'));
  if (arg('--binding')) F.binding = path.resolve(ROOT, arg('--binding'));
  const rd = p => fs.readFileSync(p, 'utf8'), scoreText = rd(scorePath), score = JSON.parse(scoreText);
  const T = { contract: rd(F.contract), binding: rd(F.binding), roles: rd(F.roles) };
  const log = s => console.log(s);
  log(`score: ${path.relative(ROOT, scorePath)} (rev ${score.rev}, ${Object.keys(score.elements).length} elements; read only)`);

  // the corrections, re-checked against the tracker and the disk
  const assets = scanAssets(ROOT);
  let tracker = null; try { tracker = trackerUnused(rd(F.tracker)); } catch (_) {}
  const unused = tracker || UNUSED;
  log('\ncorrections, re-checked');
  log(tracker ? `  BP_Obra_SC.md lists ${tracker.length} voices no longer called${same(tracker, UNUSED) ? ' (the documented 10)' : ': ' + tracker.join(', ') + ' (the documented list was ' + UNUSED.join(', ') + ')'}`
    : '  BP_Obra_SC.md: the list of voices no longer called is not there; the documented list is kept');
  const noasset = NOASSET.filter(k => !assets.has(k)), found = NOASSET.filter(k => assets.has(k));
  log(`  no asset in Content nor in the plugins: ${noasset.join(', ') || 'none'}${found.length ? ' · now there: ' + found.map(k => k + ' (' + assets.get(k).join(', ') + ')').join(', ') : ''}`);
  const vos = [...new Set(Object.values(score.elements).filter(e => e.type === 'vo' && !e.isNew).map(e => (e.sound || e.key).replace(/#\d+$/, '')))];
  const other = vos.filter(k => !assets.has(k) && !noasset.includes(k));
  if (other.length) log(`  other voices of the score with no asset (not corrected, for the Director): ${other.join(', ')}`);
  const dup = vos.filter(k => (assets.get(k) || []).length > 1);
  if (dup.length) log(`  voices with more than one asset (for the Director): ${dup.map(k => k + ' (' + assets.get(k).join(', ') + ')').join('; ')}`);

  const { contract, binding, report } = build({ score, scoreText, contract: JSON.parse(T.contract), binding: JSON.parse(T.binding), unused, noasset, prune: has('--prune') });

  // Unreal paths in the three files
  const paths = pathMap(ROOT), ctx = { root: ROOT, assets, paths };
  const pc = remapPaths(contract, 'contract.json', ctx), pb = remapPaths(binding, 'partitura_binding.json', ctx), pr = remapPaths(JSON.parse(T.roles), 'roles.json', ctx);

  log('\ncontract.json (ids by element)');
  for (const e of report.entries) {
    const d = e.was == null ? `${e.n} ids (new)` : e.add.length || e.del.length ? `${e.was} → ${e.n} (+${e.add.join(', ') || '0'} −${e.del.join(', ') || '0'})` : `${e.n} (unchanged)`;
    const v = e.vsRegex.lost.length || e.vsRegex.gained.length ? ` · vs the rules before this run: −${e.vsRegex.lost.join(', ') || '0'} +${e.vsRegex.gained.join(', ') || '0'}` : '';
    const x = (e.renamed.length ? ' · renamed in the score, kept: ' + e.renamed.join(', ') : '') + (e.orphans.length ? (e.pruned ? ' · pruned: ' : ' · not in the score, kept (--prune drops them): ') + e.orphans.join(', ') : '');
    log(`  ${e.id.padEnd(18)} ${d}${v}${x}`);
  }
  for (const c of report.corrections) log('  correction: ' + c);
  const pairs = report.entries.reduce((a, e) => a + e.n, 0), distinct = new Set(contract.entries.flatMap(c => c.ids || [])).size;
  log(`  ${pairs} (entry, element) pairs over ${distinct} distinct elements`);
  log('\npartitura_binding.json (ids per stage)');
  log(`  ${report.binds.length} binds, ${report.binds.reduce((a, b) => a + b.stages, 0)} stage ids, ${report.binds.filter(b => b.changed).length} changed · origins frozen: `
    + (report.origins.filter(o => o.stages).map(o => `${o.name} (${o.stages} stages)`).join(', ') || 'none'));
  const partial = report.binds.filter(b => b.missing.length && b.stages); if (partial.length) log('  stages with no counterpart in the score: ' + partial.map(b => b.knob + '[' + b.missing.join(',') + ']').join(' '));
  const none = report.binds.filter(b => !b.stages).map(b => b.knob); if (none.length) log('  no counterpart in the score: ' + none.join(', '));
  for (const b of report.binds) for (const r of b.rebound) log(`  re-bound by key: ${b.knob} [${r}]`);
  log('\nUnreal paths (maps of 2026-10-02: ' + paths.files.join(', ') + '; and the disk)');
  for (const x of [pc, pb, pr]) { for (const c of x.changes) log('  moved, rewritten: ' + c); for (const c of x.kept) log('  still there: ' + c); for (const c of x.unmapped) log('  NOT MAPPED: ' + c); }
  if (![pc, pb, pr].some(x => x.changes.length || x.kept.length || x.unmapped.length)) log('  none written in the three files');
  // the owners are names (BP_x, DA_x), not paths: where they live now, for the record
  const names = [...new Set((T.contract + T.roles + T.binding).match(/\b(?:BP|DA)_[A-Za-z0-9]+(?:_SC|_Obra)\b/g) || [])].sort();
  log('  owners named (names, not paths; where they live now): ' + names.map(n => n + ' ' + ((assets.get(n) || ['NOT FOUND']).join(' | '))).join(' · '));

  // each file keeps its line endings (CRLF or LF)
  const norm = s => s.replace(/\r\n/g, '\n'), eolAs = (t, s) => /\r\n/.test(t) ? norm(s).replace(/\n/g, '\r\n') : norm(s);
  const out = { contract: eolAs(T.contract, fmtJson(pc.doc) + '\n'), binding: writeBinding(T.binding, pb.doc), roles: pr.changes.length ? eolAs(T.roles, fmtJson(pr.doc) + '\n') : T.roles };
  const differs = Object.keys(out).filter(k => norm(out[k]) !== norm(T[k]));
  if (has('--check')) { log(differs.length ? `\nwould change: ${differs.join(', ')}` : '\nup to date'); process.exit(differs.length ? 1 : 0); }
  if (has('--dry')) { log(`\n--dry: nothing written${differs.length ? ' (would change: ' + differs.join(', ') + ')' : ''}`); process.exit(0); }
  for (const k of differs) fs.writeFileSync(F[k], out[k]);
  log(differs.length ? `\nwritten: ${differs.map(k => path.relative(ROOT, F[k])).join(', ')}` : '\nnothing to write: up to date');
}
