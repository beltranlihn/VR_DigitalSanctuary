// check.mjs — the invariants a score must keep to be saved (lote 5 design B §8.3, audit D12), outside the browser.
// The same module the editor asks before saving (web/editor-obra/app/js/check.js) and the server asks inside its write lock
// (tools/editor/serve_editor.py, `--stdin --base <score.json>`): the three give the same verdict. Only what is NEW relative to
// --base is rejected: the two known anchor loops (2.R4 and 5.R4) are listed as grandfathered, never rejected.
// Reads only; it never writes anything.
//
//   node tools/score/check.mjs <score.json> [--base <score.json>] [--contract <contract.json>] [--json]
//   node tools/score/check.mjs --stdin --base obra/score/score.json --json          (what the server runs)
//
//   --base      the score to compare with (the one on disk). Without it nothing is "new": loops and anchors across
//               branches are warnings, the rest errors
//   --contract  obra/unreal/contract.json (default: the one of this repository, if it is there). Its folder's
//               partitura_def.json and perillas.json give the knob names. Feeds the warnings only
//   --stdin     the score comes from standard input instead of a file
//   --json      one JSON line on stdout: { ok, schema, totals: { typical }, errors, warnings, grandfathered, ms }
//   exit 0 = it holds · 1 = a rule is broken (the errors say which) · 2 = bad input or usage (nothing was judged)
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const js = f => require(path.join(ROOT, 'web/editor-obra/app/js', f));
const t0 = Date.now();

const bad = msg => { process.stderr.write('check.mjs: ' + msg + '\n'); process.exit(2); };
const USAGE = 'usage: node tools/score/check.mjs <score.json> [--base <score.json>] [--contract <contract.json>] [--json]\n'
  + '       node tools/score/check.mjs --stdin --base obra/score/score.json --json';

function parseArgs(argv) {
  const a = { file: null, base: null, contract: null, json: false, stdin: false };
  for (let i = 0; i < argv.length; i++) {
    const x = argv[i];
    if (x === '--json') a.json = true;
    else if (x === '--stdin') a.stdin = true;
    else if (x === '--base' || x === '--contract') { const v = argv[++i]; if (!v || v.startsWith('--')) bad(x + ' needs a file\n' + USAGE); a[x.slice(2)] = v; }
    else if (x === '-h' || x === '--help') { process.stdout.write(USAGE + '\n'); process.exit(0); }
    else if (x.startsWith('--')) bad('unknown option ' + x + '\n' + USAGE);
    else if (a.file) bad('only one score file at a time\n' + USAGE);
    else a.file = x;
  }
  if (a.stdin === !!a.file) bad((a.stdin ? 'give a file or --stdin, not both' : 'give a score file or --stdin') + '\n' + USAGE);
  return a;
}
// a JSON file (a BOM from Windows editors is not part of it); anything unreadable is bad input, not a verdict
const readJson = (text, what) => { try { return JSON.parse(String(text).replace(/^﻿/, '')); } catch (e) { return bad(what + ' is not valid JSON: ' + e.message); } };
const readFile = (p, what) => { try { return fs.readFileSync(p, 'utf8'); } catch (e) { return bad(`cannot read ${what} ${p}: ${e.code || e.message}`); } };

function main() {
  const a = parseArgs(process.argv.slice(2));
  let text;
  if (a.stdin) { try { text = fs.readFileSync(0, 'utf8'); } catch (e) { bad('cannot read the score from standard input: ' + (e.code || e.message)); } }
  else text = readFile(a.file, 'the score');
  const score = readJson(text, a.stdin ? 'the score on standard input' : a.file);
  const base = a.base ? readJson(readFile(a.base, 'the base score'), a.base) : null;

  // the contract (and the knob names beside it) only feed the warnings: absent or unreadable, they are skipped
  const cpath = a.contract || path.join(ROOT, 'obra/unreal/contract.json');
  let contract = null, knobs = null;
  if (a.contract || fs.existsSync(cpath)) {
    contract = readJson(readFile(cpath, 'the contract'), cpath);
    const sib = n => { const p = path.join(path.dirname(cpath), n); try { return fs.existsSync(p) ? JSON.parse(fs.readFileSync(p, 'utf8').replace(/^﻿/, '')) : null; } catch (_) { return null; } };
    knobs = js('check.js').knobNames(sib('partitura_def.json'), sib('perillas.json'));
  }

  const Check = js('check.js');
  const r = Check.invariants(score, base, { Engine: js('engine.js'), Edits: js('edits.js'), contract, knobs });
  const out = { ok: r.ok, schema: r.schema == null ? null : r.schema, totals: r.totals, errors: r.errors, warnings: r.warnings, grandfathered: r.grandfathered, ms: Date.now() - t0 };
  if (a.json) process.stdout.write(JSON.stringify(out) + '\n');
  else {
    const mm = s => (s == null ? '—' : Math.floor(s / 60) + ':' + String(Math.round(s % 60)).padStart(2, '0'));
    const line = (tag, i) => `  ${tag} ${i.code}  ${i.msg}`;
    console.log(`${a.stdin ? 'standard input' : a.file}: schema ${out.schema}, typical ${mm(r.totals.typical)} — ` + (r.ok ? 'ok' : `${r.errors.length} rule${r.errors.length === 1 ? '' : 's'} broken`)
      + ` · ${r.warnings.length} warning${r.warnings.length === 1 ? '' : 's'} · ${r.grandfathered.length} grandfathered (${out.ms} ms)`);
    for (const i of r.errors) console.log(line('ERROR', i));
    for (const i of r.warnings) console.log(line('warn ', i));
    for (const i of r.grandfathered) console.log(line('known', i));
  }
  process.exit(r.ok ? 0 : 1);
}

// anything unexpected is not a verdict about the score: exit 2, never the 1 that means "a rule is broken"
try { main(); } catch (e) { process.stderr.write('check.mjs: internal error: ' + (e && e.stack || e) + '\n'); process.exit(2); }
