// obra/unreal/idmap.json: which sound (and which ghost take) of the score is which asset of the Unreal project (lote 5 design A §4).
// It scans VR_Test/Content (mount /Game) AND the content plugins VR_Test/Plugins/<P>/Content (mount /<P>) by their files alone: no
// Unreal, no MCP, and VR_Test is only read. It never writes the score, nor anything but --out.
//
//  · only .uasset files under an `Audio` folder, plus DA_Ghost_* under a `Ghost` folder; `_Deprecated`, `Developers`,
//    `Collections` and the external-actor folders are skipped;
//  · the class is sniffed from the first bytes of the file (the import table names it): an ObjectRedirector is listed apart (a
//    leftover of a move: it is not an asset), a SoundCue is told from a SoundWave by its sound nodes (a cue also imports the waves
//    it plays), anything else under Audio (SoundAttenuation, SoundClass...) is counted and left out;
//  · a name that two live folders carry is AMBIGUOUS: it leaves `assets` and goes to `ambiguous`, with every candidate (never
//    guess which one the score means);
//  · `referencedBy`: which Unreal packages point at the asset, from the dependency graph that tools/unreal/deps.py writes (the
//    Director's tool; it already handles the FName "_<number>" split, so it is run, not rewritten here). deps.py reads /Game only:
//    a plugin asset gets `referencedBy: null` ("unknown"), which reach.js treats as referenced (the safe side). No deps file at all:
//    null everywhere;
//  · obra/unreal/idmap_aliases.json (hand-kept, reviewed by the Director) says which asset a score sound id means when the names
//    differ (FX_BELLRING is Bell). It is copied into the file so the editor reads one thing.
//
//   node tools/score/idmap.mjs                         → scan, write obra/unreal/idmap.json
//   node tools/score/idmap.mjs --deps auto             → also run tools/unreal/deps.py (in a temp folder) for `referencedBy`
//   node tools/score/idmap.mjs --deps <deps.json>      → `referencedBy` from a deps.json you already have
//   node tools/score/idmap.mjs --check [--deps ...]    → exit 1 if the file on disk differs from a fresh scan (nothing written)
//   [--out <file>]  [--root <repo>]  [--score <score.json>: said at the end, which ids of the score still find no asset]
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import crypto from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { fileURLToPath, pathToFileURL } from 'node:url';

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const SKIP_DIR = /^(_Deprecated|Developers|Collections|__ExternalActors__|__ExternalObjects__)$/;
const HEAD = 64 * 1024;   // the class names are in the first KB of the file; the rest is audio

/* what a file is, from its first bytes (latin1): 'redirector' | 'SoundWave' | 'SoundCue' | null (not a sound) */
export function classify(head) {
  if (head.includes('ObjectRedirector')) return 'redirector';
  // a SoundCue imports the SoundWaves its nodes play, so SoundWave alone does not make a wave: its nodes make it a cue
  if (head.includes('SoundNode') || (head.includes('SoundCue') && !head.includes('NumChannels'))) return 'SoundCue';
  if (head.includes('SoundWave')) return 'SoundWave';
  return null;
}

const own = (o, k) => !!o && Object.prototype.hasOwnProperty.call(o, k);   // a sound id is user text: 'toString' is not an asset
const sha12 = buf => crypto.createHash('sha1').update(buf).digest('hex').slice(0, 12);
function hashFile(p) {   // streamed: an ambience is 10-50 MB
  const h = crypto.createHash('sha1'), fd = fs.openSync(p, 'r'), buf = Buffer.alloc(1 << 20);
  try { for (let n; (n = fs.readSync(fd, buf, 0, buf.length, null)) > 0;) h.update(buf.subarray(0, n)); } finally { fs.closeSync(fd); }
  return h.digest('hex').slice(0, 12);
}
function readHead(p) {
  const fd = fs.openSync(p, 'r');
  try { const buf = Buffer.alloc(HEAD), n = fs.readSync(fd, buf, 0, HEAD, 0); return buf.subarray(0, n).toString('latin1'); } finally { fs.closeSync(fd); }
}

/* the content roots of a project: /Game and one /<Plugin> per content plugin */
export function contentRoots(root) {
  const ue = path.join(root, 'VR_Test'), out = [{ mount: '/Game', dir: path.join(ue, 'Content') }];
  let plugins = []; try { plugins = fs.readdirSync(path.join(ue, 'Plugins'), { withFileTypes: true }).filter(d => d.isDirectory()).map(d => d.name).sort(); } catch (_) {}
  for (const p of plugins) { const dir = path.join(ue, 'Plugins', p, 'Content'); if (fs.existsSync(dir)) out.push({ mount: '/' + p, dir }); }
  return out;
}

/* { scanned, assets, ambiguous, redirectors, skipped } of the project under `root` (assets: name → record, in path order) */
export function scan(root) {
  const found = [], redirectors = [], skipped = {};
  let scanned = 0;
  const walk = (dir, mount, rel) => {
    let list; try { list = fs.readdirSync(dir, { withFileTypes: true }); } catch (_) { return; }
    list.sort((a, b) => (a.name < b.name ? -1 : a.name > b.name ? 1 : 0));
    for (const d of list) {
      const full = path.join(dir, d.name), r = rel ? rel + '/' + d.name : d.name;
      if (d.isDirectory()) { if (!SKIP_DIR.test(d.name)) walk(full, mount, r); continue; }
      if (!d.name.endsWith('.uasset')) continue;
      const name = d.name.slice(0, -'.uasset'.length), pkg = mount + '/' + r.slice(0, -'.uasset'.length), objPath = pkg + '.' + name;
      const inAudio = /(^|\/)Audio\//i.test(r), ghost = /^DA_Ghost_/.test(name) && /(^|\/)Ghost\//i.test(r);
      if (!inAudio && !ghost) continue;
      scanned++;
      const head = readHead(full), cls = classify(head);
      if (cls === 'redirector') { redirectors.push(objPath); continue; }
      let kind = cls;
      if (ghost) kind = 'GhostTake';
      else if (!cls) { const k = head.includes('SoundAttenuation') ? 'SoundAttenuation' : 'other'; skipped[k] = (skipped[k] || 0) + 1; continue; }
      found.push({ name, pkg, rec: { path: objPath, cls: kind, bytes: fs.statSync(full).size, sha1: hashFile(full), wav: fs.existsSync(full.slice(0, -'.uasset'.length) + '.wav') } });
    }
  };
  for (const r of contentRoots(root)) walk(r.dir, r.mount, '');
  const byName = new Map();
  for (const f of found) (byName.get(f.name) || byName.set(f.name, []).get(f.name)).push(f);
  const assets = {}, ambiguous = {}, pkgOf = {};
  for (const name of [...byName.keys()].sort()) {
    const list = byName.get(name).sort((a, b) => (a.rec.path < b.rec.path ? -1 : 1));
    if (list.length === 1) { assets[name] = list[0].rec; pkgOf[name] = list[0].pkg; } else ambiguous[name] = list.map(f => f.rec);
  }
  return { scanned, assets, ambiguous, redirectors: redirectors.sort(), skipped, pkgOf };
}

/* who points at each package, from a deps graph { package: [packages it points at] } (tools/unreal/deps.py). A package the graph
   does not list (a plugin asset, today) is unknown: null */
export function referencedBy(deps, pkg) {
  if (!deps || !(pkg in deps)) return null;
  const out = []; for (const q of Object.keys(deps)) if (q !== pkg && deps[q].includes(pkg)) out.push(q);
  return out.sort();
}

/* the aliases file: { aliases: { scoreSoundId: assetName } } → the map, checked */
export function readAliases(text) {
  const d = JSON.parse(text);
  if (!d || typeof d.aliases !== 'object' || Array.isArray(d.aliases)) throw new Error('idmap_aliases.json needs an "aliases" object');
  for (const [k, v] of Object.entries(d.aliases)) if (typeof v !== 'string' || !v) throw new Error(`alias ${k}: the asset name must be a non-empty string`);
  return d.aliases;
}

/* the idmap, pure on its inputs: s = scan(), aliasesText = the file, deps = the graph or null, generated = ISO time */
export function build(s, aliasesText, deps, generated) {
  const aliases = readAliases(aliasesText), assets = {};
  for (const name of Object.keys(s.assets)) assets[name] = Object.assign({}, s.assets[name], { referencedBy: referencedBy(deps, s.pkgOf[name]) });
  const ambiguous = {};
  for (const name of Object.keys(s.ambiguous)) ambiguous[name] = s.ambiguous[name].map(r => Object.assign({}, r));
  const unresolved = Object.keys(aliases).sort().filter(k => !own(assets, aliases[k]) && !own(ambiguous, aliases[k]));
  return {
    generated, source: 'fs-scan', scanned: s.scanned,
    deps: deps ? { source: 'tools/unreal/deps.py', packages: Object.keys(deps).length } : null,
    assets, ambiguous, redirectors: s.redirectors, skipped: s.skipped,
    aliasesFrom: 'obra/unreal/idmap_aliases.json', aliasesSha: sha12(Buffer.from(aliasesText.replace(/\r\n/g, '\n'))), aliases,
    unresolvedAliases: unresolved,
  };
}

/* where a score sound id lands: { state: 'asset' | 'alias' | 'ambiguous' | 'missing', name, rec?, cands? } */
export function resolveSound(idmap, sid) {
  if (!idmap || !sid) return { state: 'missing', name: sid || null };
  const al = own(idmap.aliases, sid) ? idmap.aliases[sid] : null, name = al || sid;
  if (own(idmap.ambiguous, name)) return { state: 'ambiguous', name, cands: idmap.ambiguous[name] };
  if (own(idmap.assets, name)) return { state: al ? 'alias' : 'asset', name, rec: idmap.assets[name] };
  return { state: 'missing', name };
}

/* ---------- writing: one asset per line, so a diff reads ---------- */
export function fmt(doc) {
  const MAPS = new Set(['assets', 'ambiguous', 'aliases', 'skipped']);
  const rows = Object.keys(doc).map(k => {
    const v = doc[k];
    if (MAPS.has(k) && v && typeof v === 'object' && Object.keys(v).length) return ' ' + JSON.stringify(k) + ': {\n' + Object.keys(v).map(n => '  ' + JSON.stringify(n) + ': ' + JSON.stringify(v[n])).join(',\n') + '\n }';
    if (k === 'redirectors' && v.length) return ' "redirectors": [\n' + v.map(p => '  ' + JSON.stringify(p)).join(',\n') + '\n ]';
    return ' ' + JSON.stringify(k) + ': ' + JSON.stringify(v);
  });
  return '{\n' + rows.join(',\n') + '\n}\n';
}

/* the file --out may be: not inside the Unreal project, not one of the files other sessions or the score own, and, if it exists,
   a previous idmap */
export function outProblem(root, out) {
  const rel = path.relative(root, out).replace(/\\/g, '/');
  if (rel.startsWith('..')) return null;   // outside the repo: a temp file, fine
  if (/^VR_Test(\/|$)/.test(rel)) return `${rel} is inside the Unreal project: this tool never writes there`;
  if (/^obra\/score\//.test(rel)) return `${rel} is a score file: this tool never writes the score`;
  if (/^obra\/unreal\/(partitura|perillas|traza|LEEME|roles|contract|knobs)/.test(rel) && !/idmap/.test(path.basename(rel))) return `${rel} belongs to the Director or to another tool`;
  if (fs.existsSync(out)) { try { const d = JSON.parse(fs.readFileSync(out, 'utf8')); if (!d || d.source == null || typeof d.assets !== 'object') return `${rel} exists and is not an idmap`; } catch (_) { return `${rel} exists and is not an idmap`; } }
  return null;
}

/* tools/unreal/deps.py writes deps.json into its working folder: a temp one, never the repo */
function runDeps(root) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'idmap-deps-'));
  const script = path.join(root, 'tools/unreal/deps.py');
  if (!fs.existsSync(script)) throw new Error('tools/unreal/deps.py is not there');
  let r;
  for (const cmd of [process.env.PYTHON, 'python', 'py'].filter(Boolean)) { r = spawnSync(cmd, [script], { cwd: dir, encoding: 'utf8' }); if (!r.error && r.status === 0) break; }
  if (!r || r.error || r.status !== 0) throw new Error('could not run python tools/unreal/deps.py: ' + (r && (r.error ? r.error.message : r.stderr)));
  try { return JSON.parse(fs.readFileSync(path.join(dir, 'deps.json'), 'utf8')); } finally { fs.rmSync(dir, { recursive: true, force: true }); }
}

/* what differs between two idmaps, leaving the time and (when asked) referencedBy out: lines to print, [] = same */
export function diff(a, b, opt = {}) {
  const lines = [], strip = o => { const c = JSON.parse(JSON.stringify(o)); delete c.generated; if (opt.noRefs) { delete c.deps; for (const r of Object.values(c.assets || {})) delete r.referencedBy; } return c; };
  const A = strip(a), B = strip(b);
  for (const k of ['assets', 'ambiguous']) {
    const x = A[k] || {}, y = B[k] || {};
    for (const n of Object.keys(y)) if (!(n in x)) lines.push(`${k}: + ${n}`);
    for (const n of Object.keys(x)) if (!(n in y)) lines.push(`${k}: − ${n}`);
    for (const n of Object.keys(y)) if (n in x && JSON.stringify(x[n]) !== JSON.stringify(y[n])) lines.push(`${k}: ~ ${n}`);
  }
  for (const k of ['redirectors', 'aliases', 'skipped', 'scanned', 'aliasesSha', 'unresolvedAliases']) if (JSON.stringify(A[k]) !== JSON.stringify(B[k])) lines.push(`${k} differs`);
  return lines;
}

/* ---------- CLI ---------- */
if (process.argv[1] && import.meta.url.toLowerCase() === pathToFileURL(path.resolve(process.argv[1])).href.toLowerCase()) {
  const argv = process.argv.slice(2), has = f => argv.includes(f), arg = f => { const i = argv.indexOf(f); return i >= 0 ? argv[i + 1] : null; };
  const root = path.resolve(arg('--root') || ROOT), out = path.resolve(root, arg('--out') || 'obra/unreal/idmap.json');
  const log = s => console.log(s), die = s => { console.error(s); process.exit(1); };
  const bad = outProblem(root, out); if (bad) die('refused: ' + bad);
  const aliasPath = path.join(root, 'obra/unreal/idmap_aliases.json');
  let aliasesText; try { aliasesText = fs.readFileSync(aliasPath, 'utf8'); readAliases(aliasesText); } catch (e) { die(`${path.relative(root, aliasPath)}: ${e.message}`); }
  let deps = null;
  const dp = arg('--deps');
  if (dp === 'auto') { if (root !== ROOT) die('--deps auto only works on this repo'); try { deps = runDeps(root); } catch (e) { die(e.message); } }
  else if (dp) { try { deps = JSON.parse(fs.readFileSync(path.resolve(dp), 'utf8')); } catch (e) { die(`--deps ${dp}: ${e.message}`); } }

  const s = scan(root), now = new Date().toISOString();
  const doc = build(s, aliasesText, deps, now);
  const n = o => Object.keys(o).length;
  log(`scanned ${doc.scanned} files under Audio/ (and DA_Ghost_*): ${n(doc.assets)} assets, ${n(doc.ambiguous)} ambiguous name${n(doc.ambiguous) === 1 ? '' : 's'}${n(doc.ambiguous) ? ' (' + Object.keys(doc.ambiguous).join(', ') + ')' : ''}, ${doc.redirectors.length} redirector${doc.redirectors.length === 1 ? '' : 's'}${n(doc.skipped) ? ', not sounds: ' + Object.entries(doc.skipped).map(([k, v]) => v + ' ' + k).join(', ') : ''}`);
  log(deps ? `referencedBy from ${n(deps)} packages of the dependency graph (/Game only: the plugin assets stay unknown)` : 'no dependency graph (--deps): referencedBy is null everywhere');
  if (doc.unresolvedAliases.length) log('aliases that point at no asset: ' + doc.unresolvedAliases.join(', '));

  const scorePath = arg('--score');
  if (scorePath) {
    const score = JSON.parse(fs.readFileSync(path.resolve(root, scorePath), 'utf8')), ids = new Set();
    for (const e of Object.values(score.elements)) if (e.sound && e.type !== 'haptic') ids.add(String(e.sound).replace(/#\d+$/, ''));
    const by = { asset: 0, alias: 0, ambiguous: 0, missing: 0 }, miss = [];
    for (const id of [...ids].sort()) { const r = resolveSound(doc, id); by[r.state]++; if (r.state === 'missing') miss.push(id); }
    log(`the score names ${ids.size} sounds: ${by.asset} exact, ${by.alias} by alias, ${by.ambiguous} ambiguous, ${by.missing} with no asset`);
  }

  if (has('--check')) {
    let disk = null; try { disk = JSON.parse(fs.readFileSync(out, 'utf8')); } catch (_) {}
    if (!disk) { log(`${path.relative(root, out)} is missing or unreadable`); process.exit(1); }
    const d = diff(disk, doc, { noRefs: !deps });
    if (!deps) log('referencedBy not compared (pass --deps auto to compare it)');
    log(d.length ? `${path.relative(root, out)} is out of date:\n  ` + d.slice(0, 40).join('\n  ') + (d.length > 40 ? `\n  … ${d.length - 40} more` : '') : `${path.relative(root, out)} is up to date`);
    process.exit(d.length ? 1 : 0);
  }
  // a re-run that changes nothing keeps the file (and its time) as it was
  let keep = null; try { keep = JSON.parse(fs.readFileSync(out, 'utf8')); } catch (_) {}
  if (keep && !diff(keep, doc).length && JSON.stringify(keep.deps) === JSON.stringify(doc.deps)) { log(`${path.relative(root, out)}: nothing changed, not rewritten`); process.exit(0); }
  fs.mkdirSync(path.dirname(out), { recursive: true });
  fs.writeFileSync(out, fmt(doc));
  log(`written: ${path.relative(root, out)}`);
}
