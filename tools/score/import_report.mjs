// import_report.mjs · what changed in guion.js since the score took it (lote 5 design B §7, audit D2). Read-only: it prints, it never writes
// the score. The same module the editor's panel uses (web/editor-obra/app/js/importdiff.js) does the comparing, so this and
// File ▸ Check guion.js for changes… say the same.
//
//   node tools/score/import_report.mjs                          extracts guion.js to obra/score/score.extracted.json (tools/score/extract_v1.mjs,
//                                                               its default output) and compares it with obra/score/score.json
//   node tools/score/import_report.mjs --json                   the rows as JSON
//   node tools/score/import_report.mjs --extracted <path>       compare an extraction that is already made (no extraction runs)
//   node tools/score/import_report.mjs --out <path>             where the extraction it runs goes (extract_v1's own rules: never the score)
//   node tools/score/import_report.mjs --score <path>           compare another score (a copy; it is only read)
//   VVR_PROTO=<folder> node tools/score/import_report.mjs       extract from a COPY of web/prototipo-narrativo (see extract_v1.mjs --proto)
// A schema 2 score has no stable names yet: the report compares the score with guion.js as it is, and says that the editor cannot
// take rows until the schema-3 upgrade. Exit 0 whatever it finds (1: it could not read or extract; 2: bad arguments).
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const D = createRequire(import.meta.url)(path.join(ROOT, 'web/editor-obra/app/js/importdiff.js'));
const LIVE = path.join(ROOT, 'obra/score/score.json'), DEFAULT_EXTRACTED = path.join(ROOT, 'obra/score/score.extracted.json');
const USAGE = 'usage: node tools/score/import_report.mjs [--json] [--extracted <path> | --out <path>] [--score <path>]';
const rel = p => { const r = path.relative(ROOT, p); return !r || r.startsWith('..') || path.isAbsolute(r) ? p : r.split(path.sep).join('/'); };
const fail = (code, msg) => { console.error(msg); process.exit(code); };

let json = false, extractedPath = null, outPath = null, scorePath = LIVE;
const argv = process.argv.slice(2);
for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  if (a === '--json') json = true;
  else if (a === '--extracted') { extractedPath = argv[++i]; if (!extractedPath || extractedPath.startsWith('--')) fail(2, '--extracted needs a path\n' + USAGE); }
  else if (a === '--out') { outPath = argv[++i]; if (!outPath || outPath.startsWith('--')) fail(2, '--out needs a path\n' + USAGE); }
  else if (a === '--score') { scorePath = argv[++i]; if (!scorePath || scorePath.startsWith('--')) fail(2, '--score needs a path\n' + USAGE); }
  else if (a === '--help' || a === '-h') { console.log(USAGE); process.exit(0); }
  else fail(2, `unknown option ${a}\n${USAGE}`);
}
const read = (p, what) => { try { return JSON.parse(fs.readFileSync(p, 'utf8')); } catch (e) { fail(1, `cannot read ${what} (${p}): ${e.message}`); } };

scorePath = path.resolve(process.cwd(), scorePath);
if (extractedPath && outPath) fail(2, '--extracted and --out do not go together: --out is where an extraction made here goes\n' + USAGE);
if (!extractedPath) {
  // guion.js is run and its extraction goes to the extractor's default file (or --out): extract_v1 refuses the score, whatever the spelling
  const r = spawnSync(process.execPath, [path.join(ROOT, 'tools/score/extract_v1.mjs')].concat(outPath ? ['--out', path.resolve(process.cwd(), outPath)] : []), { encoding: 'utf8' });
  if (r.status !== 0) fail(1, 'the extraction of guion.js failed:\n' + (r.stderr || r.stdout).trim());
  extractedPath = outPath || DEFAULT_EXTRACTED;
}
extractedPath = path.resolve(process.cwd(), extractedPath);
const score = read(scorePath, 'the score'), extracted = read(extractedPath, 'the extraction');
const d = D.diff(score, extracted);

if (json) {
  console.log(JSON.stringify({ score: { path: rel(scorePath), schema: score.schema, rev: score.rev }, extracted: rel(extractedPath), stable: d.stable,
    rows: d.rows, mapUpdates: d.mapUpdates, beatRen: d.beatRen, refresh: d.refresh, revive: d.revive, hidden: d.hidden }, null, 1));
  process.exit(0);
}
console.log(`guion.js against the score · ${rel(scorePath)} (schema ${score.schema}, rev ${score.rev}) · extraction ${rel(extractedPath)}`);
if (!d.stable) console.log('This score is schema 2: its names are the extraction\'s, so this only compares it with guion.js as it is, and some differences may be your own edits (the score does not remember what it took from guion.js). The editor takes rows after the schema-3 upgrade (Problems ▸ Upgrade…).');
const names = Object.keys(d.mapUpdates), tail = [];
if (d.hidden) tail.push(`${d.hidden} row${d.hidden === 1 ? '' : 's'} hidden (dismissed or kept)`);
if (!d.rows.length && !names.length) { console.log('No changes since the score took it.' + (tail.length ? ' · ' + tail.join(' · ') : '')); process.exit(0); }
const SIGN = { 'moment-added': '+', added: '+', renamed: '~', changed: '~', 'moment-changed': '~', removed: '-', 'moment-removed': '-' };
console.log(`${d.rows.length} row${d.rows.length === 1 ? '' : 's'}${names.length ? ` · ${names.length} name${names.length === 1 ? '' : 's'} follow guion.js` : ''}${tail.length ? ' · ' + tail.join(' · ') : ''}`);
for (const r of d.rows) {
  console.log(`  ${SIGN[r.kind]} ${r.kind.padEnd(14)} ${D.rowWords(r)}`);
  for (const g of Object.keys(r.groups || {})) for (const f of r.groups[g]) if (g !== 'structure' || f.field !== 'beat') console.log(`        ${D.fieldName(f.field)}: ${D.wordsOf(f.field, f.was)}  →  ${D.wordsOf(f.field, f.now)}`);
  if (r.estimate) console.log(`        its length would be about ${r.estimate.now} s: an estimate from the words, the recording decides (never taken)`);
}
if (Object.keys(d.beatRen).length) console.log('  moments renumbered: ' + Object.entries(d.beatRen).map(([a, b]) => `${a} → ${b}`).join(', '));
if (names.length) console.log('  names that follow (the ids stay): ' + names.slice(0, 8).map(o => `${o} → ${d.mapUpdates[o].to}`).join(', ') + (names.length > 8 ? `, … (${names.length - 8} more)` : ''));
if (d.stable) console.log('Nothing is applied here: in the editor, File ▸ Check guion.js for changes… offers each row with its own verb (you choose, it is one undoable edit).');
process.exit(0);
