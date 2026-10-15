// Golden test: the editor engine must reproduce the prototype's timing for every moment and element (±1 ms).
// It reads the FROZEN fixture (tools/score/fixtures/f0-score.json + f0-expect.json, made by extract_v1.mjs --fixture),
// never the live score, so editing the piece never breaks it (audit A13):
//   1. 665/665 start/end times of the typical user against the prototype's golden table, and the total;
//   2. the 4 simulated users: total, help lines that play and anchor loops, as the prototype gives them
//      (catches evaluation-order regressions of the engine);
//   3. the same 4 users, every start and end (665 each), against the times the prototype gives them, and the schema-2 contract of
//      engine v3 (design B §3): no branch, no reaction, no cross-branch anchor, `branch: 'all'` identical to leaving it out.
// Usage: node tools/score/golden_test.mjs            (exit code 1 on failure)
//        node tools/score/golden_test.mjs --live     also says how many times of the live score differ from F0:
//                                                    information only ("the score was edited"), never a failure
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { createRequire } from 'node:module';
import { ROOT, readFixture, readExpect, livePath } from './test_score.mjs';
const require = createRequire(import.meta.url);
const Engine = require(path.join(ROOT, 'web/editor-obra/app/js/engine.js'));
const score = readFixture(), expect = readExpect();
let fails = 0;

// 1 · the prototype's golden table, typical user
const r = Engine.resolve(score, { persona: 'typical' });
let bad = 0, n = 0;
for (const [id, [s, e]] of Object.entries(score.golden.times)) {
  n++; const got = r.t[id];
  if (!got || Math.abs(got[0] - s) > 1e-3 || Math.abs(got[1] - e) > 1e-3) {
    if (bad++ < 12) { const x = score.elements[id] || score.beats[id]; console.log('MISMATCH', (x.legacy && x.legacy.uid) || x.key, 'golden', s, e, 'engine', got); }
  }
}
const totalOk = Math.abs(r.total - score.golden.total) <= 1e-3;
const uidOf = id => (score.elements[id] ? score.elements[id].legacy.uid : score.beats[id] ? score.beats[id].key : id);
console.log(`golden (fixture F0): ${n - bad}/${n} match · total engine ${r.total.toFixed(3)} vs golden ${score.golden.total} · loops ${r.cycles.map(uidOf).join(', ')}`);
if (bad || !totalOk) fails++;

// 2 · the 4 simulated users
const sorted = a => JSON.stringify(a.slice().sort());
for (const p of Object.keys(expect.totals)) {
  const q = Engine.resolve(score, { persona: p });
  const help = Object.keys(q.helpActive).filter(k => q.helpActive[k]).map(uidOf), cyc = q.cycles.map(uidOf);
  const ok = Math.abs(q.total - expect.totals[p]) <= 1e-3 && sorted(help) === sorted(expect.help[p] || []) && sorted(cyc) === sorted(expect.cycles);
  console.log(`${ok ? '  ok   ' : '  FAIL '}${p.padEnd(8)} total ${q.total.toFixed(4)} (F0 ${expect.totals[p]}) · help ${help.length ? help.join(', ') : 'none'} · loops ${cyc.join(', ')}`);
  if (!ok) { fails++; console.log(`         expected help ${(expect.help[p] || []).join(', ') || 'none'} · loops ${expect.cycles.join(', ')}`); }
}

// 3 · the 4 simulated users, element by element (the prototype's own times); engine v3 changes nothing for a schema-2 score
{
  const idOf = {}; for (const id in score.elements) idOf[score.elements[id].legacy.uid] = id; for (const id in score.beats) idOf['@' + score.beats[id].key] = id;
  const sameJson = (a, b) => JSON.stringify(a) === JSON.stringify(b);
  for (const p of Object.keys(expect.totals)) {
    const q = Engine.resolve(score, { persona: p }), all = Engine.resolve(score, { persona: p, branch: 'all' });
    let tb = 0, tn = 0, worst = 0;
    for (const [u, [s, e]] of Object.entries(expect.times[p])) {
      tn++; const got = q.t[idOf[u]], d = got ? Math.max(Math.abs(got[0] - s), Math.abs(got[1] - e)) : Infinity; worst = Math.max(worst, d);
      if (d > 1e-3) { if (tb++ < 5) console.log('MISMATCH', p, u, 'prototype', s, e, 'engine', got); }
    }
    const v3 = !q.branch && !q.crossBranch.length && !q.reactive.length && !Object.keys(q.off).length
      && Object.keys(score.elements).every(id => !score.elements[id].gate || q.react[id] === q.t[id][1])
      && sameJson(q.t, all.t) && sameJson(q.helpActive, all.helpActive) && q.total === all.total;
    const ok = !tb && tn === Object.keys(score.elements).length + Object.keys(score.beats).length && v3;
    console.log(`${ok ? '  ok   ' : '  FAIL '}${p.padEnd(8)} ${tn - tb}/${tn} times as the prototype (worst ${worst.toFixed(5)} s) · schema 2: no branch, no reaction, react = the wait's end${v3 ? '' : ' (BROKEN)'}`);
    if (!ok) fails++;
  }
}

// 4 · the same piece after the upgrade to schema 3 (Edits.migrate3, in memory: the fixture is never written): the prototype's golden table
// still holds for the typical user, with all the branches at once and with the default one, DON'T SHARE is 3.25 s shorter, and no
// anchor crosses between the two sides (design B §4.1; the whole upgrade is tested in migrate3_test.mjs)
{
  const Edits = require(path.join(ROOT, 'web/editor-obra/app/js/edits.js')), contract = JSON.parse(fs.readFileSync(path.join(ROOT, 'obra/unreal/contract.json'), 'utf8'));
  const m = Edits.migrate3(score, Engine, contract, { at: expect.frozen + 'T00:00:00.000Z' });
  if (!m.next) { fails++; console.log('  FAIL the upgrade to schema 3 was refused: ' + m.report.refusals.map(x => x.msg).join(' | ')); }
  else {
    const n3 = m.next;
    const miss = (T) => { let bad = 0, tot = 0; for (const [id, [s, e]] of Object.entries(score.golden.times)) { tot++; const got = T.t[id]; if (!got || Math.abs(got[0] - s) > 1e-3 || Math.abs(got[1] - e) > 1e-3) bad++; } return [tot - bad, tot]; };
    const all = Engine.resolve(n3, { persona: 'typical', branch: 'all' }), def = Engine.resolve(n3, { persona: 'typical' }), no = Engine.resolve(n3, { persona: 'typical', branch: { share: 'no' } });
    const [a, ta] = miss(all), [d, td] = miss(def);
    const ok = a === ta && d === td && Math.abs(def.total - score.golden.total) <= 1e-3 && Math.abs(def.total - no.total - 3.25) <= 1e-3 && !def.crossBranch.length && !no.crossBranch.length && !all.crossBranch.length && n3.baseline.kind === 'prototype-f0';
    console.log(`${ok ? '  ok   ' : '  FAIL '}schema 3 (upgraded in memory): ${a}/${ta} times as the prototype with all branches, ${d}/${td} with the default one · DON'T SHARE ${(def.total - no.total).toFixed(2)} s shorter · no anchor crosses the branches`);
    if (!ok) fails++;
  }
}

// information: guion.js changed since the freeze (the fixture still tests the engine; re-extract to see the changes)
try {
  const sha = crypto.createHash('sha1').update(fs.readFileSync(path.join(ROOT, 'web/prototipo-narrativo/guion.js'))).digest('hex');
  if (expect.guion_sha1 && sha !== expect.guion_sha1) console.log(`info: guion.js changed since F0 was frozen (${expect.frozen}). The fixture still tests the engine; see the changes with node tools/score/extract_v1.mjs.`);
} catch (_) { /* no prototype here: nothing to say */ }

// --live: information only, never a failure
const lp = livePath();
if (lp) {
  try {
    const live = JSON.parse(fs.readFileSync(lp, 'utf8')), L = Engine.resolve(live, { persona: 'typical' });
    let diff = 0, gone = 0;
    for (const [id, [s, e]] of Object.entries(score.golden.times)) {
      const got = L.t[id];
      if (!got) gone++; else if (Math.abs(got[0] - s) > 1e-3 || Math.abs(got[1] - e) > 1e-3) diff++;
    }
    const added = Object.keys(live.elements || {}).filter(id => !score.elements[id]).length;
    const shown = path.relative(ROOT, lp).startsWith('..') ? lp : path.relative(ROOT, lp).split(path.sep).join('/');
    console.log(`live (${shown}): ${diff ? `${diff} of ${n} times differ from F0 (the score was edited)` : `all ${n} times as in F0`}`
      + `${gone ? ` · ${gone} no longer in the score` : ''}${added ? ` · ${added} new elements` : ''} · total ${L.total.toFixed(3)} vs ${score.golden.total} · information, not a failure`);
  } catch (e) { console.log(`live: could not read ${lp} (${e.message}) · information, not a failure`); }
}
process.exit(fails ? 1 : 0);
