// Golden test: the editor engine must reproduce the prototype's timing for every moment and element (±1 ms).
// Usage: node tools/score/golden_test.mjs   (exit code 1 on failure)
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const require = createRequire(import.meta.url);
const Engine = require(path.join(ROOT, 'web/editor-obra/app/js/engine.js'));
const score = JSON.parse(fs.readFileSync(path.join(ROOT, 'obra/score/score.json'), 'utf8'));
const r = Engine.resolve(score, { persona: 'typical' });
let bad = 0, n = 0;
for (const [id, [s, e]] of Object.entries(score.golden.times)) {
  n++; const got = r.t[id];
  if (!got || Math.abs(got[0] - s) > 1e-3 || Math.abs(got[1] - e) > 1e-3) {
    if (bad++ < 12) { const x = score.elements[id] || score.beats[id]; console.log('MISMATCH', (x.legacy && x.legacy.uid) || x.key, 'golden', s, e, 'engine', got); }
  }
}
console.log(`golden: ${n - bad}/${n} match · total engine ${r.total.toFixed(3)} vs golden ${score.golden.total} · cycles ${JSON.stringify(r.cycles)}`);
process.exit(bad || Math.abs(r.total - score.golden.total) > 1e-3 ? 1 : 0);
