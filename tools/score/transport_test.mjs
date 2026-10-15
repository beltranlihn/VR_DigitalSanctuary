// transport_test.mjs — the playback rules of the editor (audit C10: J/K/L, I/O, ↑/↓), pure, against the score of the piece
// where it matters (moment starts). Logic: web/editor-obra/app/js/transport.js. Exit 1 if any case fails.
// It runs on the frozen fixture tools/score/fixtures/f0-score.json (so real edits of the piece never break it); --live runs it
// on obra/score/score.json (see tools/score/test_score.mjs).
//   node tools/score/transport_test.mjs [--live]
import path from 'path';
import { createRequire } from 'module';
import { fileURLToPath } from 'url';
import { testScore } from './test_score.mjs';
const require = createRequire(import.meta.url);
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const E = require(path.join(ROOT, 'web/editor-obra/app/js/engine.js'));
const T = require(path.join(ROOT, 'web/editor-obra/app/js/transport.js'));
const { score, name: SRC } = testScore();
console.log('on the ' + SRC);
let fails = 0;
const check = (name, ok, info) => { console.log((ok ? '  ok   ' : '  FAIL ') + name + (info ? '  · ' + info : '')); if (!ok) fails++; };
const near = (a, b) => a != null && b != null && Math.abs(a - b) < 1e-6;

console.log('J/K/L shuttle');
{
  const st = (playing, rate, kHeld) => ({ playing, rate, kHeld: !!kHeld });
  check('L stopped: forward 1×', T.shuttle(st(false, 1), 1).rate === 1);
  check('L at 1×: 2×, then 4×, then stays 4×', T.shuttle(st(true, 1), 1).rate === 2 && T.shuttle(st(true, 2), 1).rate === 4 && T.shuttle(st(true, 4), 1).rate === 4);
  check('J stopped: backwards 1×', T.shuttle(st(false, 1), -1).rate === -1);
  check('J backwards: −2×, then −4×, then stays', T.shuttle(st(true, -1), -1).rate === -2 && T.shuttle(st(true, -2), -1).rate === -4 && T.shuttle(st(true, -4), -1).rate === -4);
  check('L while going backwards: forward 1× (not faster)', T.shuttle(st(true, -4), 1).rate === 1);
  check('J while going forward at 4×: backwards 1×', T.shuttle(st(true, 4), -1).rate === -1);
  check('stopped with a leftover rate: L starts at 1×', T.shuttle(st(false, 4), 1).rate === 1);
  const a = T.shuttle(st(true, 2, true), 1), b = T.shuttle(st(false, 1, true), -1);
  check('K held + L / J: a step of 0.1 s, no rate', near(a.step, .1) && a.rate == null && near(b.step, -.1) && b.rate == null);
  check('rate label: nothing at 1×; 2×, 4×, −1×, −4× otherwise', T.rateLabel(1) === '' && T.rateLabel(2) === '2×' && T.rateLabel(4) === '4×' && T.rateLabel(-1) === '−1×' && T.rateLabel(-4) === '−4×');
}

console.log('I / O');
{
  let r = T.markIn({ inT: null, outT: null }, 12.34567);
  check('I alone: In at the playhead (to the ms), no Out', near(r.inT, 12.346) && r.outT == null && !r.cleared);
  r = T.markOut(r, 30);
  check('then O after it: both kept', near(r.inT, 12.346) && near(r.outT, 30) && !r.cleared);
  const r2 = T.markIn(r, 40);
  check('I after the Out: the Out is cleared, and says so', near(r2.inT, 40) && r2.outT == null && r2.cleared === 'out');
  const r3 = T.markOut(r, 5);
  check('O before the In: the In is cleared, and says so', r3.inT == null && near(r3.outT, 5) && r3.cleared === 'in');
  const r4 = T.markOut({ inT: 10, outT: null }, 10);
  check('O on the In: the In is cleared (no empty range)', r4.inT == null && near(r4.outT, 10));
  check('I before 0:00 is 0:00', T.markIn({ inT: null, outT: null }, -3).inT === 0);
}

console.log('bounds: what playback is held to');
{
  const total = 1018;
  check('no range: null', T.bounds({ inT: null, outT: null }, total) === null && T.bounds(null, total) === null);
  const b1 = T.bounds({ inT: 12, outT: null }, total), b2 = T.bounds({ inT: null, outT: 30 }, total), b3 = T.bounds({ inT: 12, outT: 30 }, total);
  check('In only: In → end; Out only: start → Out; both: In → Out', near(b1[0], 12) && near(b1[1], total) && near(b2[0], 0) && near(b2[1], 30) && near(b3[0], 12) && near(b3[1], 30));
  check('an Out past a score that got shorter: held to the end', near(T.bounds({ inT: 12, outT: 2000 }, total)[1], total));
  check('an In past the end of a shorter score: no range left (null)', T.bounds({ inT: 1500, outT: null }, total) === null);
}

console.log('where Play starts, where it stops');
{
  const total = 100, b = [20, 40];
  check('forward inside the range: from where it is', near(T.startAt(25, 1, b, total), 25));
  check('forward before In, after Out or on Out: from In', near(T.startAt(5, 1, b, total), 20) && near(T.startAt(70, 2, b, total), 20) && near(T.startAt(40, 1, b, total), 20));
  check('backwards inside: from where it is; outside or on In: from Out', near(T.startAt(25, -1, b, total), 25) && near(T.startAt(70, -1, b, total), 40) && near(T.startAt(5, -2, b, total), 40) && near(T.startAt(20, -1, b, total), 40));
  check('no range, forward from the end: starts over at 0:00', near(T.startAt(100, 1, null, total), 0) && near(T.startAt(50, 1, null, total), 50));
  check('no range, backwards from 0:00: stays (it stops at once)', near(T.startAt(0, -1, null, total), 0));
  let s = T.advance(39.9, 40.2, 1, b, total);
  check('forward crossing Out: stops exactly on Out', s.stop && near(s.t, 40));
  s = T.advance(30, 30.1, 4, b, total);
  check('forward inside: goes on', !s.stop && near(s.t, 30.1));
  s = T.advance(55, 55.1, 1, b, total);
  check('forward past Out (the playhead was taken there while playing): goes on', !s.stop && near(s.t, 55.1));
  s = T.advance(99.95, 100.3, 1, b, total);
  check('forward at the end of the piece: stops on the end', s.stop && near(s.t, 100));
  s = T.advance(20.1, 19.8, -1, b, total);
  check('backwards crossing In: stops exactly on In', s.stop && near(s.t, 20));
  s = T.advance(.05, -.2, -4, null, total);
  check('backwards at 0:00: stops on 0:00', s.stop && near(s.t, 0));
  s = T.advance(10, 9.5, -1, b, total);
  check('backwards before In (taken there while playing): goes on', !s.stop && near(s.t, 9.5));
}

console.log('two tabs: what a message from the other tab does to playback');
{
  const st = (playing, rate) => ({ playing, rate });
  const f = (d, s) => T.follow(d, s);
  check('a seek during −2× (it carries the rate): nothing changes, stays −2×', f({ t: 190, playing: true, rate: -2 }, st(true, -2)) === null);
  check('a message with no rate during −2×: keeps −2× (never back to 1× forward)', f({ t: 190, playing: true }, st(true, -2)) === null);
  check('a message with no rate during 4×: keeps 4×', f({ playing: true }, st(true, 4)) === null);
  const a = f({ playing: true, rate: -2 }, st(true, 1));
  check('the other tab pressed J J while this one plays 1×: −2× here too', a && a.on === true && a.rate === -2);
  const b = f({ playing: true }, st(false, 1));
  check('the other tab started (no rate) while this one is stopped: plays at 1×', b && b.on && b.rate === 1);
  const c = f({ playing: true, rate: 2 }, st(false, 1));
  check('the other tab started at 2× while this one is stopped: plays at 2×', c && c.on && c.rate === 2);
  const s = f({ playing: false, rate: 1 }, st(true, -4));
  check('the other tab stopped: stops here, back to 1×', s && s.on === false && s.rate === 1);
  check('stopped and told stopped: nothing', f({ playing: false }, st(false, 1)) === null);
  check('no playing in the message (a range, a score): nothing', f({ range: [1, 2] }, st(true, 2)) === null && f({ t: 5 }, st(true, -1)) === null);
  check('a rate that is not a speed (0, NaN, 9): keeps this tab\'s speed', f({ playing: true, rate: 0 }, st(true, -2)) === null && f({ playing: true, rate: NaN }, st(true, 2)) === null && f({ playing: true, rate: 9 }, st(true, 4)) === null);
}

console.log('↑ / ↓ on the score (moment starts, typical user)');
{
  const sch = E.resolve(score, { persona: 'typical' }), order = score.acts.flatMap(a => a.beats), starts = order.map(b => sch.t[b][0]);
  const uniq = [...new Set(starts.map(x => Math.round(x * 1000) / 1000))].sort((a, b) => a - b);
  const mid = uniq[10] + (uniq[11] - uniq[10]) / 2;
  check('↓ from the middle of a moment: the next start', near(T.momentStep(starts, mid, 1), uniq[11]), `${order.length} moments, ${uniq.length} distinct starts`);
  check('↑ from the middle of a moment: its own start', near(T.momentStep(starts, mid, -1), uniq[10]));
  check('↑ exactly on a start: the previous one', near(T.momentStep(starts, uniq[10], -1), uniq[9]));
  check('↓ exactly on a start: the next one', near(T.momentStep(starts, uniq[10], 1), uniq[11]));
  check('↑ while playing just past a start: skips it (no landing twice on the same one)', near(T.momentStep(starts, uniq[10] + .2, -1, .4), uniq[9]));
  check('↓ after the last start: null; ↑ at 0:00: null', T.momentStep(starts, uniq[uniq.length - 1] + 1, 1) === null && T.momentStep(starts, 0, -1) === null);
  // walking with ↓ from before 0:00 to the end lands once on every distinct start, always forward; ↑ walks it back
  const walk = (from, dir) => { const out = []; let t = from; for (let n = 0; n < order.length + 5; n++) { const x = T.momentStep(starts, t, dir); if (x == null) break; out.push(x); t = x; } return out; };
  const down = walk(-1, 1), up = walk(sch.total + 1, -1);
  const dup = order.length - uniq.length;
  check('↓ walks every distinct start once, in order (moments that start together count once)', down.length === uniq.length && down.every((x, i) => i === 0 || x > down[i - 1]), `${down.length} stops · ${dup} moment${dup === 1 ? '' : 's'} share a start`);
  check('↑ walks them back, the same stops', up.length === uniq.length && up.slice().reverse().every((x, i) => near(x, down[i])));
}

console.log(fails ? `\n${fails} FAILED` : '\nall ok');
process.exit(fails ? 1 : 0);
