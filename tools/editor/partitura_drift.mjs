// partitura_drift.mjs — compares what the score does today with the knobs of DA_Partitura_Obra.
//   node tools/editor/partitura_drift.mjs            → table on screen + obra/unreal/partitura_drift.json
// Uses the live export (obra/unreal/partitura.json) when it exists; otherwise the values the asset was created with.
import fs from 'fs';
import path from 'path';
import { createRequire } from 'module';
import { fileURLToPath } from 'url';
const require = createRequire(import.meta.url);
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const rd = p => JSON.parse(fs.readFileSync(path.join(ROOT, p), 'utf8'));
const Engine = require(path.join(ROOT, 'web/editor-obra/app/js/engine.js'));
const Partitura = require(path.join(ROOT, 'web/editor-obra/app/js/partitura.js'));

const score = rd('obra/score/score.json'), def = rd('obra/unreal/partitura_def.json'), binding = rd('obra/unreal/partitura_binding.json');
const live = fs.existsSync(path.join(ROOT, 'obra/unreal/partitura.json')) ? rd('obra/unreal/partitura.json') : null;
const sched = Engine.resolve(score, { persona: 'typical' });
const d = Partitura.drift(score, sched, def, live, binding);
const ST = def.stages.map(s => s.slice(0, 4));
const f = v => v == null ? '—' : (Math.round(v * 100) / 100).toString();
console.log(`DA values: ${d.source === 'live' ? 'live export ' + (live.exported || '') : 'initial (no live export yet)'}\n`);
console.log('knob'.padEnd(24) + 'stage'.padEnd(7) + 'DA'.padStart(8) + 'score'.padStart(9) + 'diff'.padStart(9));
let n = 0, off = 0;
for (const r of d.rows) {
  if (r.missing) { console.log(r.knob.padEnd(24) + '   not in partitura_def'); continue; }
  n++; const bad = r.diff != null && Math.abs(r.diff) > 0.05; if (bad) off++;
  console.log(r.knob.padEnd(24) + (r.stage == null ? '' : ST[r.stage]).padEnd(7) + f(r.da).padStart(8) + f(r.score).padStart(9) + (r.diff == null ? '   n/a' : f(r.diff)).padStart(9) + (bad ? '  ≠' : '') + (r.approx ? '  ~' : ''));
}
console.log(`\n${off} of ${n} measured values differ by more than 0.05 s · ~ = approximate binding`);
fs.writeFileSync(path.join(ROOT, 'obra/unreal/partitura_drift.json'), JSON.stringify({ generated: new Date().toISOString(), ...d }, null, 1));
