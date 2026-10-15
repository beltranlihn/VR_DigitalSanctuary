// compile.mjs — the dry-run compiler of the score against Unreal (lote 5 design A §5). Command line of web/editor-obra/app/js/compile.js.
//
// It READS the score and what Unreal gave (obra/unreal/*.json, the marks seed), works out where every element stands with Unreal
// (knob / wired / cue-ready / preview), REFUSES what a real compile could not take (an anchor loop, an anchor to nothing, a mark
// that Unreal does not emit, placed twice or out of order, an asset two files answer to) and prints the MANIFEST. It writes nothing
// but that manifest, and only where it is safe to: never under VR_Test/ (the Unreal project), obra/unreal/ (the Director's and the
// web's files for Unreal), obra/score/ (the score, its history and the seed), web/prototipo-narrativo/ or tools/score/fixtures/,
// never over one of its own inputs, never a .uasset or .umap. It never imports anything from tools/unreal/ and never talks to Unreal.
//
//   node tools/score/compile.mjs [--score obra/score/score.json] [--idmap obra/unreal/idmap.json]
//     [--contract obra/unreal/contract.json] [--def obra/unreal/partitura_def.json] [--live obra/unreal/partitura.json]
//     [--binding obra/unreal/partitura_binding.json] [--trace obra/unreal/traza.json] [--seed obra/score/seed/marks-v1.json]
//     [--roles obra/unreal/roles.json] [--out <file>|-]      (--out: default "-" = the manifest on stdout)
//
//   exit 0  compiled, nothing refused
//   exit 2  compiled WITH refusals (the manifest is still printed or written; `ok` is false and `refused` says why)
//   exit 1  bad input (a file that is not there or not valid, a score the editor cannot read) or an unsafe --out: nothing written
//
// The score is the schema 2 or 3 one. A schema 3 score that is bound carries its own marks; any other reads them from the seed
// (inputs.score.marksFrom says which). The optional files (idmap, partitura_def/binding/live, trace, seed, roles) may be missing from
// their default place: the manifest says what could not be judged without them. A path given on the command line must exist. One line for a person goes to stderr.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const js = f => require(path.join(ROOT, 'web/editor-obra/app/js', f));
const Compile = js('compile.js');

export const DEFAULTS = {
  score: 'obra/score/score.json', idmap: 'obra/unreal/idmap.json', contract: 'obra/unreal/contract.json', def: 'obra/unreal/partitura_def.json',
  live: 'obra/unreal/partitura.json', binding: 'obra/unreal/partitura_binding.json', trace: 'obra/unreal/traza.json', seed: 'obra/score/seed/marks-v1.json', roles: 'obra/unreal/roles.json',
};
const REQUIRED = new Set(['score', 'contract']);
// where the manifest may never go (relative to the repo root), and the kinds of files that are never written
const PROTECTED = ['VR_Test', 'obra/unreal', 'obra/score', 'web/prototipo-narrativo', 'tools/score/fixtures'];
const NEVER = /\.(uasset|umap)$/i;

const fail = msg => { const e = new Error(msg); e.bad = true; return e; };
/* the same file, however it is spelled: case (Windows, macOS), "..", a trailing dot or space or a ":stream" (Windows writes those to
   the file itself), a junction or a symlink, a hard link (same inode). The same care as extract_v1.mjs */
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
/* may the manifest be written at `out`? → null when it may, else the reason */
export function unsafeOut(out, inputs = []) {
  if (NEVER.test(real(out))) return 'it is a .uasset or .umap';
  for (const dir of PROTECTED) if (within(out, path.join(ROOT, dir))) return `it is inside ${dir}/`;
  let st = null; try { st = fs.statSync(real(out)); } catch (_) { /* a new file */ }
  if (st && st.isDirectory()) return 'it is a folder';
  for (const f of inputs) if (f && sameFile(out, f)) return 'it is one of the inputs';
  return null;
}

export function parseArgs(argv) {
  const o = { out: '-' }, keys = new Set([...Object.keys(DEFAULTS), 'out']);
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (!a.startsWith('--') || !keys.has(a.slice(2))) throw fail(`Unknown option ${a}. Options: ${[...keys].map(k => '--' + k).join(' ')}`);
    const v = argv[++i]; if (v === undefined || (v.startsWith('--') && v !== '-')) throw fail(`${a} needs a value`);
    o[a.slice(2)] = v;
  }
  return o;
}
const sha12 = text => crypto.createHash('sha1').update(text).digest('hex').slice(0, 12);

/* reads the inputs (relative paths are the repo's: a path given on the command line is relative to where it is run) */
export function loadInputs(args) {
  const inp = { sha12: {} }, files = [];
  for (const [k, def] of Object.entries(DEFAULTS)) {
    const given = args[k] != null, file = path.resolve(given ? process.cwd() : ROOT, given ? args[k] : def);
    // a default that is not there is an absence the manifest will say; a path somebody typed that is not there is a mistake
    if (!fs.existsSync(file)) { if (REQUIRED.has(k) || given) throw fail(`${k}: ${file} is not there`); continue; }
    files.push(file);
    let text; try { text = fs.readFileSync(file, 'utf8'); } catch (e) { throw fail(`${k}: cannot read ${file}: ${e.message}`); }
    try { inp[k] = JSON.parse(text); } catch (e) { throw fail(`${k}: ${file} is not valid JSON: ${e.message}`); }
    inp.sha12[k] = sha12(text);
  }
  return { inp, files };
}

export function run(argv, { stdout = s => process.stdout.write(s), stderr = s => process.stderr.write(s), now } = {}) {
  let args, loaded, manifest;
  try {
    args = parseArgs(argv);
    // the output is judged first: an unsafe one stops everything before anything is read or written
    const out = args.out === '-' ? null : path.resolve(process.cwd(), args.out);
    loaded = loadInputs(args);
    if (out) { const why = unsafeOut(out, loaded.files); if (why) throw fail(`Refused to write ${args.out}: ${why}. The manifest goes outside the repo's data: print it on stdout (the default) or choose a path in a temp folder.`); }
    try { manifest = Compile.compile(loaded.inp, { now }); } catch (e) { if (e instanceof Compile.BadInput) throw fail(e.message); throw e; }
    const text = JSON.stringify(manifest, null, 2) + '\n';
    if (out) { fs.mkdirSync(path.dirname(out), { recursive: true }); fs.writeFileSync(out, text); } else stdout(text);
    stderr(`compile: ${Compile.summaryText(manifest)}${out ? ` · wrote ${path.relative(process.cwd(), out) || out}` : ''}\n`);
    return manifest.ok ? 0 : 2;
  } catch (e) {
    if (e && e.bad) { stderr(`compile: ${e.message}\n`); return 1; }
    stderr(`compile: unexpected error: ${e && e.stack || e}\n`); return 1;
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) process.exitCode = run(process.argv.slice(2));
