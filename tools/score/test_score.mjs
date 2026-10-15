// Which score a test runs on (audit A13, lote 5 design B §4.1).
// By default the FROZEN fixture tools/score/fixtures/f0-score.json (the F0 extraction of the prototype), so the owner's
// real edits to obra/score/score.json never break a test. `--live` runs it on the live score instead; `--live <path>`
// on another copy (used by fixture_test.mjs). Nothing here writes anything.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
export const FIXTURE = path.join(ROOT, 'tools/score/fixtures/f0-score.json');
export const EXPECT = path.join(ROOT, 'tools/score/fixtures/f0-expect.json');
export const LIVE = path.join(ROOT, 'obra/score/score.json');
/* the catalogs that go with the score under test: the frozen F0 copies by default (contract and Partitura bindings by
   element id are generated from the live score, so they follow the owner's edits), obra/unreal/ with --live */
export const catalogPath = (kind, argv = process.argv.slice(2)) => argv.includes('--live')
  ? path.join(ROOT, 'obra/unreal', kind === 'binding' ? 'partitura_binding.json' : kind + '.json')
  : path.join(ROOT, 'tools/score/fixtures', kind + '-f0.json');

const readJson = (p, what) => {
  if (!fs.existsSync(p)) {
    console.error(`${what} not found: ${p}` + (p === FIXTURE || p === EXPECT ? '\nFreeze it once with: node tools/score/extract_v1.mjs --fixture' : ''));
    process.exit(1);
  }
  return JSON.parse(fs.readFileSync(p, 'utf8'));
};
export const readFixture = () => readJson(FIXTURE, 'frozen fixture');
export const readExpect = () => readJson(EXPECT, 'frozen expectations');

/* the path given to --live (or the live score), null without --live */
export function livePath(argv = process.argv.slice(2)) {
  const i = argv.indexOf('--live');
  if (i < 0) return null;
  const p = argv[i + 1];
  return p && !p.startsWith('--') ? path.resolve(process.cwd(), p) : LIVE;
}

/* A schema-3 copy of a schema-2 score, made by hand for the tests of the chunks that read schema 3 (lote 5 design B §2, §4.3):
   `golden` becomes `baseline` (relative times: [start inside its moment, length]) and nothing else changes, so nothing moves
   for the typical user. It is NOT the in-app migration (Edits.migrate3: branches, waits, uidMap, accepted...), only what these
   tests need. Pure: the argument is never changed. */
export function schema3Copy(score) {
  const s = JSON.parse(JSON.stringify(score)), g = s.golden, rel = {};
  for (const id of Object.keys(s.elements)) { const t = g.times[id], b = g.times[s.elements[id].beat]; if (t && b) rel[id] = [t[0] - b[0], t[1] - t[0]]; }
  s.schema = 3;
  s.baseline = { kind: 'prototype-f0', total: g.total, rel, log: [{ op: 'migrate', at: '2026-10-07T00:00:00.000Z', by: 'test' }].concat((g.voices || []).map(v => Object.assign({ op: 'voices' }, v))) };
  delete s.golden;
  return s;
}

/* { score, live, name } for the test: the fixture, or with --live the live score (or the given copy) */
export function testScore(argv = process.argv.slice(2)) {
  const lp = livePath(argv);
  if (!lp) return { score: readFixture(), live: false, name: 'frozen fixture F0 (tools/score/fixtures/f0-score.json)' };
  return { score: readJson(lp, 'score'), live: true, name: lp === LIVE ? 'LIVE score (obra/score/score.json)' : 'score ' + lp };
}
