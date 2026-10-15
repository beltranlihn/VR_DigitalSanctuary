// edits_test.mjs — replays the cases of the audit (docs/editor-obra/anexos/18-auditoria-app.md) against the score of the piece,
// with the pure edit logic of the app (web/editor-obra/app/js/edits.js). Exit 1 if any case fails.
// It runs on the frozen fixture tools/score/fixtures/f0-score.json (so real edits of the piece never break it); --live runs it
// on obra/score/score.json (see tools/score/test_score.mjs).
//   node tools/score/edits_test.mjs [--live]
import fs from 'fs';
import path from 'path';
import { createRequire } from 'module';
import { fileURLToPath } from 'url';
import { testScore, schema3Copy } from './test_score.mjs';
const require = createRequire(import.meta.url);
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const E = require(path.join(ROOT, 'web/editor-obra/app/js/engine.js'));
const X = require(path.join(ROOT, 'web/editor-obra/app/js/edits.js'));
const { score, name: SRC } = testScore();
console.log('on the ' + SRC);
const T0 = E.resolve(score, { persona: 'typical' });
const idOf = (key, beatKey) => Object.keys(score.elements).find(id => score.elements[id].key === key && (!beatKey || score.beats[score.elements[id].beat].key === beatKey));
const beatOf = key => Object.keys(score.beats).find(b => score.beats[b].key === key);
const addLane = (n, gid) => { const g = n.groups.find(x => x.id === gid); let i = g.lanes.length + 1, id; do { id = 'ln_' + gid + '_' + (i++); } while (n.lanes[id]); n.lanes[id] = { name: g.name + ' ' + i, group: gid }; g.lanes.push(id); return id; };
let fails = 0;
const check = (name, ok, info) => { console.log((ok ? '  ok   ' : '  FAIL ') + name + (info ? '  · ' + info : '')); if (!ok) fails++; };
const fmt = s => Math.floor(s / 60) + ':' + String(Math.round(s % 60)).padStart(2, '0');

console.log('delete with repair (A1, B3, +B1, +D3)');
for (const [key, beat] of [['PASO', '2.7a'], ['VO_15', null], ['G_BELL', null], ['TO_HUD', null], ['G_SAVE5', null], ['WALK1', null], ['G_CHOOSE', null], ['VEIL_OPEN', 'V1']]) {
  const id = idOf(key, beat), p = X.planDelete(score, [id], E);
  if (!p) { check(`${key}: nothing hangs from it`, true); continue; }
  const A = p.reanchor, B = p.family;
  check(`${key} · re-anchor: dependents keep their times, nothing dangles`, A.ok, `${p.direct.length} direct (${p.anchoredMoments.length} moments) · ${A.moved} items move · total ${fmt(A.total0)} → ${fmt(A.total1)}`);
  check(`${key} · delete them too: no moment deleted, nothing dangles`, B.ok && Object.keys(B.next.beats).length === Object.keys(score.beats).length, `deletes ${B.deleted} · total ${fmt(B.total1)}`);
}
// persona-independent: the plan never depends on the user shown on screen
{ const id = idOf('G_BELL'), a = X.planDelete(score, [id], E), kid = idOf('FX_BELLRING');
  check('G_BELL · re-anchor uses the typical user (FX_BELLRING offset)', a.reanchor.next.elements[kid].at.off === +(T0.t[kid][0] - T0.t[a.reanchor.next.elements[kid].at.ref][a.reanchor.next.elements[kid].at.edge === 'end' ? 1 : 0]).toFixed(4)); }

console.log('move alone (A7, +B4)');
for (const [key, dt] of [['VO_10', 2], ['VO_15', 2], ['ALMA_IN', 1], ['BIO', 3]]) {
  const id = idOf(key), kids = E.dependents(score), n = X.move(score, id, dt, { alone: true }, kids), T1 = E.resolve(n, { persona: 'typical' });
  const moved = Object.keys(n.elements).concat(Object.keys(n.beats)).filter(k => Math.abs(T0.t[k][0] - T1.t[k][0]) > 1e-3 || Math.abs(T0.t[k][1] - T1.t[k][1]) > 1e-3);
  const others = moved.filter(k => k !== id && !score.beats[k]);
  check(`${key} +${dt}s alone: anchored elements stay`, (kids[id] || []).every(k => !moved.includes(k)), `${moved.length} items change time (${others.length} elements besides it)`);
}
{ const id = idOf('BIO'), n = X.move(score, id, 10, { alone: true }, E.dependents(score)), T1 = E.resolve(n, { persona: 'typical' });
  check('BIO (lasts until an event) +10s alone: start moves, it still ends with its event',
    Math.abs(T1.t[id][0] - T0.t[id][0] - 10) < 1e-3 && Math.abs(T1.t[id][1] - T0.t[id][1]) < 1e-3, `${(T0.t[id][1] - T0.t[id][0]).toFixed(2)} → ${(T1.t[id][1] - T1.t[id][0]).toFixed(2)} s`); }

console.log('overlaps (+A2)');
for (const [key, dt] of [['HALL_OFF', -2], ['TO_HUD', -2]]) {
  const id = idOf(key), n = X.move(score, id, dt, {}, E.dependents(score));
  const movedTo = X.fixOverlaps(score, n, E, addLane), T1 = E.resolve(n, { persona: 'typical' }).t;
  const left = X.lanesOverlap(n, T1, Object.keys(n.elements));
  const before = X.lanesOverlap(score, T0.t, Object.keys(score.elements));
  check(`${key} ${dt}s: no new overlap after the fix`, left.length <= before.length, `${movedTo.length} relocated (${movedTo.map(m => score.elements[m.id].key + '→' + m.to).join(', ')}) · overlaps ${before.length} → ${left.length}`);
}

console.log('validate (A9, +B3)');
const bad = [{ schema: 2, elements: {} }, Object.assign(JSON.parse(JSON.stringify(score)), { acts: [{ id: 'x', beats: ['nope'] }] })];
for (const [i, s] of bad.entries()) { let threw = false; try { X.validate(s, E); } catch (e) { threw = true; } check(`broken score ${i + 1} is rejected`, threw); }
{ let ok = true; try { X.validate(score, E); } catch (e) { ok = false; console.log(e.message); } check('the score validates', ok); }

console.log('change the anchor (C9)');
{ const before = JSON.stringify(score), all = s => Object.keys(s.elements).concat(Object.keys(s.beats));
  // same time for EVERYTHING with the typical user, no new loop, and the anchor is the one asked for
  const kept = r => { if (!r.ok) return false; const T1 = E.resolve(r.next, { persona: 'typical' }); return all(r.next).every(k => Math.abs(T1.t[k][0] - T0.t[k][0]) < 1e-3 && Math.abs(T1.t[k][1] - T0.t[k][1]) < 1e-3) && T1.cycles.length === T0.cycles.length; };
  const at = (r, id) => (score.beats[id] ? r.next.beats : r.next.elements)[id].at;
  const vo5 = idOf('VO_05'), vo4 = idOf('VO_04'), bell = idOf('G_BELL'), ring = idOf('FX_BELLRING');
  let r = X.reanchor(score, vo5, { ref: vo4, edge: 'end' }, E);
  check('VO_05 after VO_04: keeps its time, nothing else moves', kept(r) && at(r, vo5).ref === vo4 && at(r, vo5).edge === 'end', r.ok ? `off ${at(r, vo5).off} s (was ${score.elements[vo5].at.off} after ${score.elements[score.elements[vo5].at.ref].key})` : r.why);
  check('  the off is its start minus the new edge', r.ok && Math.abs(at(r, vo5).off - (T0.t[vo5][0] - T0.t[vo4][1])) < 1e-3);
  check('  only its anchor changed', r.ok && JSON.stringify(Object.assign(JSON.parse(JSON.stringify(r.next)), { elements: Object.assign({}, r.next.elements, { [vo5]: score.elements[vo5] }) })) === before);
  // the edge: start ↔ end of the same anchor (the off grows by the anchor's length)
  r = X.reanchor(score, ring, { ref: bell, edge: 'start' }, E);
  check('FX_BELLRING: end of G_BELL → its start keeps the time', kept(r) && at(r, ring).ref === bell && at(r, ring).edge === 'start' && Math.abs(at(r, ring).off - (T0.t[bell][1] - T0.t[bell][0])) < 1e-3, r.ok ? `off ${at(r, ring).off} s` : r.why);
  check('  G_BELL is a wait: the other simulated users shift (only the typical time is kept)', r.ok && r.others.idle < -1 && r.others.fast > 0 && !('typical' in r.others), r.ok ? JSON.stringify(r.others) : '');
  check('  and back to its end: the same anchor it had', (() => { const b = X.reanchor(r.next, ring, { ref: bell, edge: 'end' }, E); return b.ok && Math.abs(b.at.off - score.elements[ring].at.off) < 1e-3 && kept(b); })());
  // detach: an element goes to the start of its own moment
  r = X.reanchor(score, vo5, null, E);
  check('detach VO_05: anchored to the start of its moment, same time', kept(r) && at(r, vo5).ref === score.elements[vo5].beat && at(r, vo5).edge === 'start', r.ok ? `off ${at(r, vo5).off} s` : r.why);
  check('  homeAnchor of an element = its moment start', JSON.stringify(X.homeAnchor(score, vo5)) === JSON.stringify({ ref: score.elements[vo5].beat, edge: 'start' }));
  check('  detaching it again: nothing to do', (() => { const b = X.reanchor(r.next, vo5, null, E); return !b.ok && b.same; })());
  // loops are refused, with a reason that names them
  r = X.reanchor(score, vo5, { ref: vo5, edge: 'end' }, E);
  check('anchored to itself: refused', !r.ok && r.self && /itself/.test(r.why), r.why);
  const kid = (E.dependents(score)[vo4] || []).find(k => score.elements[k] && score.elements[k].at.ref === vo4);
  r = X.reanchor(score, vo4, { ref: kid, edge: 'end' }, E);
  check(`VO_04 to ${score.elements[kid].key}, which hangs from it: refused (loop)`, !r.ok && r.loop && r.why.includes(score.elements[kid].key), r.why);
  const w1 = idOf('WALK1'), deep = [...E.family(score, w1)].find(k => score.elements[k] && !(E.dependents(score)[w1] || []).includes(k));
  r = X.reanchor(score, w1, { ref: deep, edge: 'start' }, E);
  check('WALK1 to something that hangs from it two steps away: refused, says through what', !r.ok && r.loop && /through/.test(r.why), deep ? `${score.elements[deep].key} · ${r.why}` : 'no deep dependent');
  r = X.reanchor(score, vo4, { ref: score.elements[vo4].beat, edge: 'end' }, E);
  check('VO_04 to the end of its own moment (which waits for it): refused', !r.ok && r.loop && /^The end of moment .* depends on VO_04/.test(r.why), r.why);
  r = X.reanchor(score, vo5, { ref: score.elements[vo5].at.ref, edge: score.elements[vo5].at.edge }, E);
  check('the anchor it already has: nothing to do', !r.ok && r.same, r.why);
  // precise, not just "in the family": what does NOT wait for it is a valid anchor
  const fx = Object.keys(score.elements).find(k => score.elements[k].group === 'fx' && !E.inBeatEnd(score, k) && score.elements[k].at.ref !== score.elements[k].beat && X.reanchor(score, k, { ref: score.elements[k].beat, edge: 'end' }, E, { others: false }).ok);
  check(`a sound (${fx && score.elements[fx].key}) to the end of its own moment: allowed (a sound does not make its moment longer)`, !!fx && kept(X.reanchor(score, fx, { ref: score.elements[fx].beat, edge: 'end' }, E)));
  let until = null;   // y lasts until x, but its start does not hang from x: x may be anchored to y's start, never to its end
  for (const [k, e] of Object.entries(score.elements)) {
    if (!e.end || !score.elements[e.end.ref] || e.end.ref === k) continue;
    const xx = e.end.ref; if (!E.family(score, xx).has(k) || X.hangingFrom(score, xx, E).has(k + '|S')) continue;
    const ra = X.reanchor(score, xx, { ref: k, edge: 'start' }, E, { others: false }); if (ra.ok) { until = { k, xx, ra }; break; }
  }
  check('an anchor to the start of what lasts until it: allowed (Engine.family alone would refuse it)', !!until && kept(until.ra), until ? `${score.elements[until.xx].key} → start of ${score.elements[until.k].key}` : 'no case in the score');
  if (until) { r = X.reanchor(score, until.xx, { ref: until.k, edge: 'end' }, E); check('  …and to its end: refused (it ends with it)', !r.ok && r.loop, r.why); }
  // moments
  const m27b = beatOf('2.7b'), m27a = beatOf('2.7a'), paso = idOf('PASO', '2.7a');
  r = X.reanchor(score, m27b, null, E);
  check('detach moment 2.7b (after PASO): it follows 2.7a, same time', kept(r) && at(r, m27b).ref === m27a && at(r, m27b).edge === 'end', r.ok ? `off ${at(r, m27b).off} s` : r.why);
  r = X.reanchor(score, m27b, { ref: paso, edge: 'start' }, E);
  check('moment 2.7b to the start of PASO: same time, off = PASO length', kept(r) && Math.abs(at(r, m27b).off - (T0.t[paso][1] - T0.t[paso][0])) < 1e-3, r.ok ? `off ${at(r, m27b).off} s` : r.why);
  r = X.reanchor(score, m27a, { ref: idOf('PASO', '2.7b'), edge: 'end' }, E);
  check('moment 2.7a to a PASO of 2.7b (it hangs from 2.7a): refused', !r.ok && r.loop, r.why);
  const m16 = beatOf('1.6'), own = Object.keys(score.elements).find(k => score.elements[k].beat === m16 && score.elements[k].at && score.elements[k].at.ref === m16);
  r = X.reanchor(score, m16, { ref: own, edge: 'end' }, E);
  check('moment 1.6 to one of its own elements: refused', !r.ok && r.loop, r.why);
  const first = score.acts[0].beats[0];
  check('homeAnchor of the first moment = the start of the piece', X.homeAnchor(score, first).ref === null);
  r = X.reanchor(score, beatOf('2.7c'), { ref: m27a, edge: 'end' }, E);
  check('moment 2.7c after the end of 2.7a (skipping 2.7b): nothing between waits for it, same time', kept(r) && r.at.ref === m27a && r.at.edge === 'end', r.ok ? `off ${r.at.off} s` : r.why);
  // a score with no `at` on a moment (it follows the previous one): the anchor it reports is that one
  { const s2 = JSON.parse(before); delete s2.beats[m27a].at; const a = X.anchorOf(s2, m27a), order = s2.acts.flatMap(x => x.beats);
    check('a moment without an anchor follows the previous one', a.ref === order[order.indexOf(m27a) - 1] && a.edge === 'end');
    check('  and detaching it: nothing to do', (() => { const d = X.reanchor(s2, m27a, null, E); return !d.ok && d.same; })()); }
  // C1: an anchor to something that no longer exists can be detached where it is now (moment or element)
  { const s3 = JSON.parse(before), v = idOf('VO_05'); s3.beats[m27b].at.ref = 'el_gone'; s3.elements[v].at.ref = 'el_gone2';
    const Tg = E.resolve(s3, { persona: 'typical' }), rb = X.reanchor(s3, m27b, null, E), Tb = rb.ok && E.resolve(rb.next, { persona: 'typical' });
    check('a moment anchored to something deleted: detach keeps the time it falls back to, nothing dangles from it', rb.ok && Math.abs(Tb.t[m27b][0] - Tg.t[m27b][0]) < 1e-3 && !Tb.dangling.includes(m27b), rb.ok ? `${Tg.dangling.length} → ${Tb.dangling.length} dangling` : rb.why);
    const re = X.reanchor(s3, v, null, E), Te = re.ok && E.resolve(re.next, { persona: 'typical' });
    check('  an element too', re.ok && Math.abs(Te.t[v][0] - Tg.t[v][0]) < 1e-3 && !Te.dangling.includes(v), re.ok ? '' : re.why);
    check('  but not to the anchor that is gone', !X.reanchor(s3, v, { ref: 'el_gone2', edge: 'start' }, E).ok); }
  // C1 with a lost END (what it lasts until): the Problems "Detach" repairs THAT one; a start that still exists is never touched
  { const keptVs = (Ta, n) => { const Tb = E.resolve(n, { persona: 'typical' }); return all(n).every(k => Math.abs(Tb.t[k][0] - Ta.t[k][0]) < 1e-3 && Math.abs(Tb.t[k][1] - Ta.t[k][1]) < 1e-3) && Tb.cycles.length === Ta.cycles.length; };
    const calm = idOf('CALM'), gw = idOf('GROOVE_WAIT'), s4 = JSON.parse(before);
    s4.elements[calm].end.ref = 'el_gone3'; s4.elements[gw].end.ref = 'el_gone4';
    const Tg = E.resolve(s4, { persona: 'typical' });
    check('lost end: the engine reports CALM and GROOVE_WAIT', Tg.dangling.includes(calm) && Tg.dangling.includes(gw));
    check('  lostAnchors says it is the end, not the start', JSON.stringify(X.lostAnchors(s4, calm)) === '["end"]' && JSON.stringify(X.lostAnchors(s4, gw)) === '["end"]');
    let d = X.detachLost(s4, calm, E), Td = d.ok && E.resolve(d.next, { persona: 'typical' });
    check('  CALM: only its end is repaired (its start anchor stays), same times, it no longer dangles', d.ok && JSON.stringify(d.next.elements[calm].at) === JSON.stringify(s4.elements[calm].at)
      && d.next.elements[calm].end.ref === s4.elements[calm].beat && d.next.elements[calm].end.edge === 'start' && keptVs(Tg, d.next) && !Td.dangling.includes(calm), d.ok ? JSON.stringify(d.fields) : d.why);
    d = X.detachLost(s4, gw, E); Td = d.ok && E.resolve(d.next, { persona: 'typical' });
    check('  GROOVE_WAIT (its start is already its moment): the end is repaired, not "already anchored"', d.ok && d.fields.length === 1 && d.fields[0].field === 'end' && keptVs(Tg, d.next) && !Td.dangling.includes(gw), d.ok ? '' : d.why);
    check('  the old verb on the start would not have fixed it (the bug of the review)', (() => { const o = X.reanchor(s4, gw, null, E); return !o.ok && o.same; })());
    const s5 = JSON.parse(before); s5.elements[calm].at.ref = 'el_gone5'; s5.elements[calm].end.ref = 'el_gone6';
    const T5 = E.resolve(s5, { persona: 'typical' }), b = X.detachLost(s5, calm, E), Tb = b.ok && E.resolve(b.next, { persona: 'typical' });
    check('  start and end both lost: both repaired in one go, same times, nothing dangles', b.ok && b.fields.map(f => f.field).join() === 'at,end' && keptVs(T5, b.next) && !Tb.dangling.length, b.ok ? '' : b.why);
    check('  nothing lost: nothing to repair', !X.detachLost(score, calm, E).ok);
    const s6 = JSON.parse(before); s6.elements[calm].end.ref = 'el_gone7'; s6.elements[calm].end.off = 900;
    const lg = X.detachLost(s6, calm, E);
    check('  a lost end far past its moment: refused (repaired it would count in its moment\'s end), says so', !lg.ok && /last longer/.test(lg.why), lg.why);
    // what an element lasts until, with opts.field 'end'
    check('  an end can\'t last until itself', !X.reanchor(score, calm, { ref: calm, edge: 'end' }, E, { field: 'end' }).ok);
    check('  a moment has no end anchor', !X.reanchor(score, m27b, null, E, { field: 'end' }).ok);
    const fixed = Object.keys(score.elements).find(k => !score.elements[k].end);
    check('  an element with a length has no end anchor', !X.reanchor(score, fixed, null, E, { field: 'end' }).ok);
    // a loop through the end: X lasts until Y, Y starts at the end of X
    const pair = Object.keys(score.elements).map(y => [score.elements[y].at, y]).find(([a]) => a && a.ref && a.edge === 'end' && score.elements[a.ref] && score.elements[a.ref].end);
    if (pair) { const xx = pair[0].ref, yy = pair[1], lp = X.reanchor(score, xx, { ref: yy, edge: 'start' }, E, { field: 'end' });
      check(`  ${score.elements[xx].key} lasting until ${score.elements[yy].key}, which starts at its end: refused (loop)`, !lp.ok && lp.loop, lp.why); }
    else check('  a pair to test the end loop exists in the score', false); }
  check('nothing above touched the score', JSON.stringify(score) === before); }

console.log('several at once: move, delete (C10)');
{ const before = JSON.stringify(score), kids = E.dependents(score), all = s => Object.keys(s.elements).concat(Object.keys(s.beats));
  const T = n => E.resolve(n, { persona: 'typical' }).t, near = (a, b) => Math.abs(a - b) < 1e-3;
  const lands = (n, ids, dt) => { const T1 = T(n); return ids.every(id => near(T1[id][0], T0.t[id][0] + dt)); };
  const vo4 = idOf('VO_04'), kid = (kids[vo4] || []).find(k => score.elements[k] && score.elements[k].at.ref === vo4), other = (kids[vo4] || []).filter(k => k !== kid && score.elements[k]);
  let n = X.moveMany(score, [vo4, kid], 2, {}, E, kids);
  check(`VO_04 and ${score.elements[kid].key} (anchored to it) +2 s: both land +2 s, not +4`, lands(n, [vo4, kid], 2) && n.elements[kid].at.off === score.elements[kid].at.off, `${score.elements[kid].key} off ${n.elements[kid].at.off}`);
  check('  what hangs from VO_04 and is not selected follows', lands(n, other, 2), other.map(k => score.elements[k].key).join(', ') || 'none');
  n = X.moveMany(score, [vo4, kid], 2, { alone: true }, E, kids);
  check('  alone: both +2 s, the rest of what hangs from VO_04 stays', lands(n, [vo4, kid], 2) && lands(n, other, 0));
  // a clip pushed by its moment (the previous moment ends with the other selected clip) is not moved twice either
  const order = score.acts.flatMap(a => a.beats); let pair = null;
  for (let i = 0; i < order.length - 1 && !pair; i++) {
    const b = order[i], nb = order[i + 1], dep = (id) => X.hangingFrom(score, id, E, 'end');
    const x = Object.keys(score.elements).find(k => score.elements[k].beat === b && E.inBeatEnd(score, k) && near(T0.t[k][1], T0.t[b][1]) && dep(k).has(nb + '|S'));
    const y = x && Object.keys(score.elements).find(k => score.elements[k].beat === nb && score.elements[k].at.ref === nb && score.elements[k].at.edge === 'start');
    if (x && y && Object.keys(score.elements).filter(k => score.elements[k].beat === b && E.inBeatEnd(score, k) && near(T0.t[k][1], T0.t[b][1])).length === 1) pair = [x, y];
  }
  n = pair && X.moveMany(score, pair, 3, {}, E, kids);
  check('the last clip of a moment and a clip of the next one +3 s: both +3 s (the second one only follows its moment)', !!pair && lands(n, pair, 3) && n.elements[pair[1]].at.off === score.elements[pair[1]].at.off, pair ? pair.map(k => score.elements[k].key).join(' + ') : 'no case in the score');
  // anchored BEFORE what it hangs from (a negative offset, made here: the score has none): measured after it, not moved twice
  { const s2 = JSON.parse(before); s2.elements[kid].at.off = -(T0.t[vo4][1] - T0.t[vo4][0]) - 1;
    const T2 = T(s2), n2 = X.moveMany(s2, [kid, vo4], -1.5, {}, E, E.dependents(s2)), T3 = T(n2);
    check(`${score.elements[kid].key} 1 s before VO_04 (anchored to its end), both −1.5 s: both −1.5 s`, T2[kid][0] < T2[vo4][0] && [kid, vo4].every(k => near(T3[k][0], T2[k][0] - 1.5)) && near(n2.elements[kid].at.off, s2.elements[kid].at.off)); }
  check('one id: the same as move()', JSON.stringify(X.moveMany(score, [vo4], 1.2, {}, E, kids)) === JSON.stringify(X.move(score, vo4, 1.2, {}, kids)));
  // delete several: a chain x → y → z, deleting x and y keeps z where it was
  const chain = Object.keys(score.elements).map(z => { const y = score.elements[z].at.ref, Y = score.elements[y]; return Y && score.elements[Y.at.ref] ? [Y.at.ref, y, z] : null; }).find(Boolean);
  const p = X.planDelete(score, chain.slice(0, 2), E), keep = r => { const T1 = T(r.next); return all(r.next).filter(k => !chain.slice(0, 2).includes(k)).every(k => near(T1[k][0], T0.t[k][0]) && near(T1[k][1], T0.t[k][1])); };
  check(`delete ${score.elements[chain[0]].key} and ${score.elements[chain[1]].key} together: ${score.elements[chain[2]].key} (hanging from the second) keeps its time`, p && p.reanchor.ok && keep(p.reanchor) && !chain.slice(0, 2).includes(p.reanchor.next.elements[chain[2]].at.ref), p ? `${p.direct.length} direct · ${p.reanchor.moved} move` : 'no plan');
  check('  "delete them too" takes both families, no moment deleted', p && p.family.ok && chain.every(k => p.family.ids.includes(k)) && Object.keys(p.family.next.beats).length === Object.keys(score.beats).length, p ? `${p.family.deleted} deleted` : '');
  const two = [idOf('VO_15'), idOf('G_SAVE5')], p2 = X.planDelete(score, two, E);
  check('delete two unrelated elements: re-anchor keeps every dependent of both where it was', !!p2 && p2.reanchor.ok && p2.family.ok, p2 ? `${p2.direct.length} direct · ${p2.reanchor.moved} items move (a moment gets shorter)` : 'nothing hangs');
  // seven voices of five moments (a box drawn in the timeline): moment 2.7a hangs from the last one; the earlier ones make their
  // moments shorter, so everything after moves earlier, 2.7a with it, at its place after 2.6 (the old check said "not possible")
  const seven = ['VO_03', 'VO_03h', 'VO_04', 'VO_04b', 'VO_05', 'VO_06a', 'VO_06b'].map(k => idOf(k)), p7 = X.planDelete(score, seven, E), m27a = beatOf('2.7a');
  const a7 = p7 && p7.reanchor.next.beats[m27a].at, T7 = p7 && T(p7.reanchor.next);
  check('delete 7 voices of 5 moments: re-anchor is possible, nothing dangles', !!p7 && p7.reanchor.ok && p7.reanchor.dangling === 0, p7 ? `${p7.reanchor.moved} items move · total ${fmt(p7.reanchor.total0)} → ${fmt(p7.reanchor.total1)}` : 'no plan');
  check('  moment 2.7a keeps its place after what it now hangs from', !!a7 && !seven.includes(a7.ref) && near(T7[m27a][0] - (a7.edge === 'start' ? T7[a7.ref][0] : T7[a7.ref][1]), T0.t[m27a][0] - (a7.edge === 'start' ? T0.t[a7.ref][0] : T0.t[a7.ref][1])), a7 ? `${score.beats[a7.ref] ? 'moment ' + score.beats[a7.ref].key : score.elements[a7.ref].key} ${a7.edge} + ${a7.off}` : '');
  // the card must not say "stay where they are" when an earlier deletion moved them (review of C10): drift lists them
  const T7a = p7 && T(p7.reanchor.next), drift7 = p7 ? p7.reanchor.drift : null;
  check('  drift = what hung from them and is not where it was (2.7a moved earlier): the card says so', !!drift7 && drift7.includes(m27a) && drift7.every(k => !seven.includes(k) && !(near(T7a[k][0], T0.t[k][0]) && near(T7a[k][1], T0.t[k][1]))), drift7 ? drift7.map(k => score.beats[k] ? 'moment ' + score.beats[k].key : score.elements[k].key).join(', ') : '');
  check('  one deleted and re-anchored: nothing drifts', [idOf('VO_15'), idOf('G_BELL')].every(id => { const q = X.planDelete(score, [id], E); return !q || !q.reanchor.ok || !q.reanchor.drift.length; }));
  check('nothing above touched the score', JSON.stringify(score) === before); }

console.log('copy, paste, duplicate (C10)');
{ const before = JSON.stringify(score), T = n => E.resolve(n, { persona: 'typical' }), near = (a, b) => Math.abs(a - b) < 1e-3;
  const keys0 = new Set(Object.values(score.elements).map(e => e.key)), untouched = n => Object.keys(score.elements).every(id => JSON.stringify(n.elements[id]) === JSON.stringify(score.elements[id]));
  let seq = 0; const opts = { who: 'B', at: '2026-10-05T00:00:00Z', now: () => 1e12, rand: () => ((seq++ * 7) % 36) / 36, addLane };
  check('uniqueKey: free stays, taken gets _2, then _3', X.uniqueKey(new Set(['A']), 'B') === 'B' && X.uniqueKey(new Set(['A']), 'A') === 'A_2' && X.uniqueKey(new Set(['A', 'A_2']), 'A') === 'A_3');
  { const s1 = { elements: { el_x: {} }, beats: {}, lanes: {} }; let r = 0; const fixed = X.newId(s1, 'el_', { now: () => 35, rand: () => 0 }), next = X.newId(s1, 'el_', { now: () => 35, rand: () => (r++ ? .5 : 0), taken: new Set([fixed]) });
    check('newId: prefix + time + 4 random chars, never one in use', fixed === 'el_z0000' && next !== fixed && /^el_[A-Za-z0-9]{3,40}$/.test(next), fixed + ' · ' + next); }
  // a wait with its help line and a clip that hangs from it, pasted into another moment
  const w = Object.keys(score.elements).find(k => score.elements[k].gate && Object.values(score.elements).some(x => x.help === k) && (E.dependents(score)[k] || []).some(c => score.elements[c] && !score.elements[c].help));
  const h = Object.keys(score.elements).find(k => score.elements[k].help === w), f = E.dependents(score)[w].find(c => score.elements[c] && !score.elements[c].help);
  const tb = beatOf('2.4'), clip = X.clipOf(score, [w, h, f], E), r = X.planPaste(score, clip, { beat: tb, off: 5 }, E, opts);
  check(`paste ${[w, h, f].map(k => score.elements[k].key).join(', ')} into 2.4 at +5 s`, r.ok && r.ids.length === 3, r.ok ? r.keys.join(', ') : r.why);
  const T1 = r.ok && T(r.next), nx = r.ok ? r.next.elements : {}, cw = r.map[w], ch = r.map[h], cf = r.map[f];
  check('  new ids, new unique keys, isNew, no legacy, copyOf, in the target moment', r.ok && r.ids.every(id => !score.elements[id] && nx[id].isNew === true && nx[id].legacy === null && nx[id].beat === tb && !keys0.has(nx[id].key) && score.elements[nx[id].copyOf]) && new Set(r.keys).size === 3);
  const mapped = fld => { const a = score.elements[f][fld]; return !a || a.ref !== w || (nx[cf][fld].ref === cw && nx[cf][fld].edge === a.edge && nx[cf][fld].off === a.off); };
  check('  the help line helps the COPY of the wait; the clip that hung from the wait hangs from its copy', r.ok && nx[ch].help === cw && mapped('at') && mapped('end') && [nx[cf].at, nx[cf].end].some(a => a && a.ref === cw));
  check('  same layout with the typical user: first one 5 s into 2.4, the rest where they were from it, same lengths', r.ok && clip.items.every(it => near(T1.t[r.map[it.id]][0] - T1.t[tb][0], 5 + it.s - clip.t0) && near(T1.t[r.map[it.id]][1] - T1.t[r.map[it.id]][0], it.e - it.s)));
  check('  the originals are untouched, the score validates, no copy lands on another clip', r.ok && untouched(r.next) && (() => { try { X.validate(r.next, E); return true; } catch (e) { return false; } })() && !X.lanesOverlap(r.next, T1.t, r.ids).length, r.ok ? `lanes ${r.ids.map(id => nx[id].lane).join(', ')}${r.newLanes.length ? ' · new ' + r.newLanes.join(', ') : ''}` : '');
  // anchors to what is not copied become the start of the target moment
  const r2 = X.planPaste(score, X.clipOf(score, [h], E), { beat: tb, off: 2 }, E, opts), c2 = r2.ok && r2.next.elements[r2.ids[0]];
  check('a help line pasted without its wait: an ordinary line, anchored to the start of the moment', r2.ok && c2.help === null && c2.at.ref === tb && c2.at.edge === 'start' && near(c2.at.off, 2));
  const until = Object.keys(score.elements).find(k => { const e = score.elements[k]; return e.end && e.end.ref && score.elements[e.end.ref] && e.end.ref !== e.at.ref && T0.t[k][1] - T0.t[k][0] > 1; });
  const r3 = X.planPaste(score, X.clipOf(score, [until], E), { beat: tb, off: 1 }, E, opts), c3 = r3.ok && r3.next.elements[r3.ids[0]], T3 = r3.ok && T(r3.next);
  check(`${score.elements[until].key} (lasts until another clip) pasted alone: it lasts the same, its end hangs from the moment`, r3.ok && c3.end.ref === tb && near(T3.t[r3.ids[0]][1] - T3.t[r3.ids[0]][0], T0.t[until][1] - T0.t[until][0]), r3.ok ? `${(T0.t[until][1] - T0.t[until][0]).toFixed(2)} s` : r3.why);
  // duplicate: right after itself, in its own moment, twice
  const vo5 = idOf('VO_05'), len = T0.t[vo5][1] - T0.t[vo5][0], d1 = X.planPaste(score, X.clipOf(score, [vo5], E), { dt: len }, E, opts);
  const Td = d1.ok && T(d1.next), c5 = d1.ok && d1.next.elements[d1.ids[0]];
  check('duplicate VO_05: right after itself, in its moment, VO_05_2, not in Unreal yet', d1.ok && near(Td.t[d1.ids[0]][0], T0.t[vo5][1]) && c5.beat === score.elements[vo5].beat && c5.key === 'VO_05_2' && c5.isNew && c5.legacy === null, d1.ok ? `${c5.key} at ${Td.t[d1.ids[0]][0].toFixed(2)} · lane ${c5.lane}` : d1.why);
  const d2 = d1.ok && X.planPaste(d1.next, X.clipOf(d1.next, [vo5], E), { dt: len }, E, opts);
  check('  again: VO_05_3', d2 && d2.ok && d2.keys[0] === 'VO_05_3');
  const d2b = d1.ok && X.planPaste(d1.next, X.clipOf(d1.next, d1.ids, E), { dt: len }, E, opts);
  check('  a copy of the copy counts from the original: VO_05_3, not VO_05_2_2; copyOf says what it was copied from', d2b && d2b.ok && d2b.keys[0] === 'VO_05_3' && d2b.next.elements[d2b.ids[0]].copyOf === d1.ids[0], d2b && d2b.keys[0]);
  const pair = [idOf('VO_04'), (E.dependents(score)[idOf('VO_04')] || []).find(k => score.elements[k] && score.elements[k].at.ref === idOf('VO_04'))];
  const cp = X.clipOf(score, pair, E), d3 = X.planPaste(score, cp, { dt: cp.t1 - cp.t0 }, E, opts), Tp = d3.ok && T(d3.next);
  check('duplicate two clips, one anchored to the other: the copy hangs from the copy, the pair keeps its layout', d3.ok && d3.next.elements[d3.map[pair[1]]].at.ref === d3.map[pair[0]] && pair.every(k => near(Tp.t[d3.map[k]][0], T0.t[k][0] + cp.t1 - cp.t0)), d3.ok ? '' : d3.why);
  // lanes: the one asked for (Alt+drag) when it is free, or a new one
  const gl = score.groups.find(g => g.id === score.elements[vo5].group).lanes, other = gl.find(l => l !== score.elements[vo5].lane);
  const d4 = X.planPaste(score, X.clipOf(score, [vo5], E), { dt: 0 }, E, Object.assign({}, opts, { lanes: { [vo5]: 'new' } }));
  check('  dropped on "+ New lane": a new lane of its group', d4.ok && d4.newLanes.length === 1 && d4.next.elements[d4.ids[0]].lane === d4.newLanes[0] && d4.next.lanes[d4.newLanes[0]].group === score.elements[vo5].group);
  const d5 = other && X.planPaste(score, X.clipOf(score, [vo5], E), { dt: len }, E, Object.assign({}, opts, { lanes: { [vo5]: other } }));
  check('  dropped on another lane of its group: that lane, when it is free there', !!d5 && d5.ok && d5.next.elements[d5.ids[0]].lane === (X.lanesOverlap(d5.next, T(d5.next).t, d5.ids).length ? null : other), d5 && d5.ok ? d5.next.elements[d5.ids[0]].lane : '');
  const d6 = X.planPaste(score, X.clipOf(score, [vo5], E), { dt: 0 }, E, opts);
  check('  at the same time: never on top of the original (another lane)', d6.ok && d6.next.elements[d6.ids[0]].lane !== score.elements[vo5].lane);
  // clips of CONSECUTIVE moments (review of C10): the copy in the earlier moment makes it longer and pushes the next one;
  // the copy there must not get that push on top of its dt (VO_04b + VO_05, Alt+drag +3 s, landed +6 s)
  const ok3 = (r, f) => { try { X.validate(r.next, E); } catch (e) { return false; } return untouched(r.next) && f(T(r.next).t); };
  const span = its => { const s = {}; for (const it of its) { const b = it.el.beat, q = s[b] || (s[b] = [Infinity, -Infinity]); q[0] = Math.min(q[0], it.s); q[1] = Math.max(q[1], it.e); } return b => s[b][1] - s[b][0] > .05 ? s[b][1] - s[b][0] : 1; };
  { const a = idOf('VO_04b'), b = idOf('VO_05'), cb = X.clipOf(score, [a, b], E);
    const r = X.planPaste(score, cb, { dt: 3 }, E, opts), Tr = r.ok && T(r.next).t;
    check('Alt+drag VO_04b (2.5) + VO_05 (2.6) +3 s: each copy lands +3 s from where it was (where the drag showed it), not +6', r.ok && ok3(r, Tn => cb.items.every(it => near(Tn[r.map[it.id]][0], it.s + 3) && near(Tn[r.map[it.id]][1], it.e + 3))),
      r.ok ? cb.items.map(it => `${r.next.elements[r.map[it.id]].key} ${Tr[r.map[it.id]][0].toFixed(2)}`).join(' · ') + ` · total ${fmt(r.total0)} → ${fmt(r.total1)}` : r.why);
    check('  no copy on top of another clip', r.ok && !X.lanesOverlap(r.next, Tr, Object.keys(r.next.elements)).length);
    const d = X.planPaste(score, cb, { after: true }, E, opts), Td = d.ok && T(d.next).t, dt = span(cb.items);
    check('Ctrl+D VO_04b + VO_05: each copy right after its original (VO_05 after it was pushed), the piece grows by what was duplicated', d.ok && ok3(d, Tn => cb.items.every(it => near(Tn[d.map[it.id]][0], Tn[it.id][0] + dt(it.el.beat)))) && near(Td[d.map[b]][0], Td[b][1]) && d.total1 - d.total0 < (cb.items.reduce((s, it) => s + it.e - it.s, 0) + 1e-3),
      d.ok ? cb.items.map(it => `${d.next.elements[d.map[it.id]].key} ${Td[d.map[it.id]][0].toFixed(2)}`).join(' · ') + ` · total ${fmt(d.total0)} → ${fmt(d.total1)}` : d.why); }
  { const vos = Object.keys(score.elements).filter(k => score.elements[k].type === 'vo' && !score.elements[k].help).sort((a, b) => T0.t[a][0] - T0.t[b][0]);
    const pairs = vos.slice(1).map((v, i) => [vos[i], v]).filter(([a, b]) => score.elements[a].beat !== score.elements[b].beat);
    const bad = { d3: [], dm: [], after: [] };
    for (const pr of pairs) {
      const cb = X.clipOf(score, pr, E), name = pr.map(k => score.elements[k].key).join('+'), dt = span(cb.items);
      for (const [tag, dd] of [['d3', 3], ['dm', -1]]) {
        const r = X.planPaste(score, cb, { dt: dd }, E, opts);
        if (!r.ok || !ok3(r, Tn => cb.items.every(it => near(Tn[r.map[it.id]][0], it.s + dd) && near(Tn[r.map[it.id]][1], it.e + dd)) && !X.lanesOverlap(r.next, Tn, Object.keys(r.next.elements)).length)) bad[tag].push(name);
      }
      const d = X.planPaste(score, cb, { after: true }, E, opts);
      if (!d.ok || !ok3(d, Tn => cb.items.every(it => near(Tn[d.map[it.id]][0], Tn[it.id][0] + dt(it.el.beat)) && near(Tn[d.map[it.id]][1] - Tn[d.map[it.id]][0], it.e - it.s)) && !X.lanesOverlap(d.next, Tn, Object.keys(d.next.elements)).length)) bad.after.push(name);
    }
    check(`every pair of consecutive voices of two moments (${pairs.length}): Alt+drag +3 s and −1 s land where the drag showed, Ctrl+D right after each original`, pairs.length > 5 && !bad.d3.length && !bad.dm.length && !bad.after.length,
      ['d3', 'dm', 'after'].filter(k => bad[k].length).map(k => `${k}: ${bad[k].join(', ')}`).join(' · ') || `${pairs.length} pairs`); }
  { const d1b = X.planPaste(score, X.clipOf(score, [vo5], E), { after: true }, E, opts);
    check('Ctrl+D of one clip = Alt+drag by its length', d1b.ok && d1.ok && near(T(d1b.next).t[d1b.ids[0]][0], Td.t[d1.ids[0]][0])); }
  check('refused: nothing copied, a moment that no longer exists', !X.planPaste(score, { items: [] }, { beat: tb, off: 0 }, E).ok && !X.planPaste(score, clip, { beat: 'bt_gone', off: 0 }, E).ok);
  check('nothing above touched the score', JSON.stringify(score) === before); }

console.log('honest "unsaved" (C14)');
{ const clone = o => JSON.parse(JSON.stringify(o)), anyEl = Object.keys(score.elements)[0];
  check('a copy of the score is the same score', X.sameScore(score, clone(score)));
  check('rev, savedBy and savedAt do not count (a save writes them)', X.sameScore(score, Object.assign(clone(score), { rev: score.rev + 1, savedBy: 'S', savedAt: '2030-01-01T00:00:00Z' })));
  const noVol = clone(score); delete noVol.rev; delete noVol.savedBy; delete noVol.savedAt;
  check('a score without them is still the same', X.sameScore(score, noVol) && X.sameScore(noVol, score));
  const reordered = {}; for (const k of Object.keys(score).reverse()) reordered[k] = clone(score[k]);
  const e0 = reordered.elements[anyEl]; reordered.elements[anyEl] = Object.fromEntries(Object.entries(e0).reverse());
  check('key order does not count (a key deleted and added back)', X.sameScore(score, reordered));
  const moved = clone(score), m = moved.elements[anyEl]; m.at = m.at || { ref: m.beat, edge: 'start', off: 0 }; m.at.off += .1;
  check('an element 0.1 s later is a change', !X.sameScore(score, moved));
  const noted = clone(score); noted.notes = Object.assign({}, noted.notes, { nt_x: { t: 1, who: 'B', text: 'x' } });
  check('a new note is a change', !X.sameScore(score, noted));
  const marked = clone(score); marked.markers = Object.assign({}, marked.markers, { mk_x: { t: 1, name: 'Bookmark 1', who: 'B' } });
  check('a new bookmark is a change', !X.sameScore(score, marked));
  const nulled = clone(score); nulled.elements[anyEl].zz_test = null;
  check('a field that appears (even null) is a change', !X.sameScore(score, nulled) && !X.sameScore(nulled, score));
  const acts = clone(score); acts.acts = acts.acts.slice().reverse();
  check('the order of an array counts', !X.sameScore(score, acts));
  // the editor's undo: JSON snapshots; edit, edit, undo, undo = the loaded score again (clean)
  const undo = []; let cur = clone(score);
  for (const f of [s => { s.markers.mk_u = { t: 2, name: 'B', who: 'B' }; }, s => { s.markers.mk_u.name = 'Renamed'; }]) { undo.push(JSON.stringify(cur)); f(cur); }
  check('two edits are a change', !X.sameScore(score, cur));
  cur = JSON.parse(undo.pop()); check('one undo is still a change', !X.sameScore(score, cur));
  cur = JSON.parse(undo.pop()); check('undo back to the loaded score = clean', X.sameScore(score, cur));
  check('null and missing scores', X.sameScore(null, null) && !X.sameScore(score, null)); }

console.log('import names everything it replaces, not only the elements (review of lote 5 step 1)');
{ const clone = o => JSON.parse(JSON.stringify(o));
  // what extract_v1 always writes: no bookmarks, no notes, no accepted problems, a golden without .voices, rev 1, never saved
  const extraction = (s => { s.markers = {}; s.notes = {}; delete s.accepted; delete s.propuestas; delete s.savedBy; delete s.savedAt; s.rev = 1; if (s.golden) delete s.golden.voices; return s; })(clone(score));
  const same0 = X.importDiff(score, clone(score)), w0 = X.importWords(same0);
  check('the same score: nothing differs, nothing to keep, no words', same0.ownGone === 0 && !w0.own && !w0.also && !w0.base && !w0.other
    && ['elements', 'beats', 'lanes', 'markers', 'notes'].every(k => !same0[k].added.length && !same0[k].changed.length && !same0[k].gone.length));
  // the reviewer's case: one bookmark, then an extraction with the same elements
  const marked = clone(score); marked.markers = { mk_r: { t: 12, name: 'Bookmark 1', who: 'B' } };
  const d1 = X.importDiff(marked, extraction), w1 = X.importWords(d1);
  check('a bookmark the file does not have is named (0 elements differ is not "nothing changes")',
    d1.elements.added.length + d1.elements.changed.length + d1.elements.gone.length === 0 && d1.ownGone === 1 && w1.own === '1 bookmark', `own "${w1.own}"`);
  const k1 = X.keepOwn(marked, extraction);
  check('  keeping it = the score as it was (nothing else changes)', X.sameScore(k1, marked) && k1.markers.mk_r.name === 'Bookmark 1');
  check('  importing it as it is drops it', !Object.keys(extraction.markers).length);
  // notes, accepted problems, values waiting for Unreal and the real voice lengths applied to the baseline
  const own = clone(score), vo = Object.keys(own.elements).filter(id => own.elements[id].type === 'vo').slice(0, 2);
  own.notes = { nt_a: { t: 3, who: 'B', text: 'a', el: vo[0] }, nt_b: { t: 9, who: 'N', text: 'b', el: null } };
  own.accepted = [{ fp: 'C2.FLASH|' + vo[0], sv: 'warn', ly: 'C2', rule: 'C2.FLASH', el: vo[0], who: 'B', reason: 'on purpose', at: '2026-10-03T10:00:00Z' }];
  own.propuestas = { valores: { Etapa_Tope: 61 }, motivos: { Etapa_Tope: 'longer' }, base: 'h0' };
  own.golden = clone(own.golden); for (const id of vo) own.golden.times[id] = own.golden.times[id].map(x => x + .5);
  own.golden.voices = [{ at: '2026-10-03T11:00:00Z', by: 'B', ids: vo, src: 'final mix' }];
  own.baseline = { note: 'a field this editor does not know yet' };
  const d2 = X.importDiff(own, extraction), w2 = X.importWords(d2);
  check('notes, accepted problems and values waiting for Unreal are named', d2.ownGone === 4 && w2.own === '2 notes, 1 accepted problem and 1 value waiting for Unreal', `own "${w2.own}"`);
  check('the "≠ APK" baseline: the times that differ and the real voice lengths that would be lost',
    /baseline becomes the file's \(2 reference times differ\)/.test(w2.base) && /real voice lengths applied on 2026-10-03 \(2 voices\) are not in it/.test(w2.base), w2.base);
  check('a field the editor does not know is named too', w2.other === 'Also not in the file: baseline.', w2.other);
  const ownStr = JSON.stringify(own), extStr = JSON.stringify(extraction), k2 = X.keepOwn(own, extraction);
  check('keepOwn changes neither the score nor the file', JSON.stringify(own) === ownStr && JSON.stringify(extraction) === extStr);
  check('  it keeps the notes, the accepted problem and the value waiting for Unreal (with its reason and base)',
    Object.keys(k2.notes).length === 2 && k2.accepted.length === 1 && k2.accepted[0].reason === 'on purpose'
    && k2.propuestas.valores.Etapa_Tope === 61 && k2.propuestas.motivos.Etapa_Tope === 'longer' && k2.propuestas.base === 'h0');
  check('  the baseline and the unknown field stay the file\'s (they go with its times)', JSON.stringify(k2.golden) === JSON.stringify(extraction.golden) && !('baseline' in k2));
  check('  and the timing is the file\'s', Math.abs(E.resolve(k2, { persona: 'typical' }).total - E.resolve(extraction, { persona: 'typical' }).total) < 1e-9);
  // the file wins where both have the same record; what the file adds is not a loss
  const a = clone(score), f = clone(score);
  a.markers = { mk_1: { t: 1, name: 'Mine', who: 'B' } }; f.markers = { mk_1: { t: 1, name: 'Theirs', who: 'N' }, mk_2: { t: 5, name: 'New', who: 'N' } };
  f.propuestas = { valores: { Etapa_Tope: 70 }, motivos: {} }; a.propuestas = { valores: { Etapa_Tope: 61 }, motivos: {} };
  const d3 = X.importDiff(a, f), w3 = X.importWords(d3), k3 = X.keepOwn(a, f);
  check('the same bookmark in both: the file\'s, said as such, nothing to keep', d3.ownGone === 0 && /1 bookmark changes to the file's/.test(w3.also) && /1 value waiting for Unreal changes to the file's/.test(w3.also)
    && k3.markers.mk_1.name === 'Theirs' && k3.markers.mk_2 && k3.propuestas.valores.Etapa_Tope === 70, w3.also);
  // the structure: moments, lanes, acts and groups
  const cur4 = clone(score); addLane(cur4, cur4.groups[0].id);   // an empty lane the file does not have
  const st = clone(score), bk = Object.keys(st.beats)[3]; st.beats[bk] = Object.assign({}, st.beats[bk], { title: 'Renamed' });
  const w4 = X.importWords(X.importDiff(cur4, st));
  check('moments, lanes and groups that change are named', /1 moment differs/.test(w4.also) && /1 lane would disappear/.test(w4.also) && /the groups change/.test(w4.also) && !/acts/.test(w4.also), w4.also); }

console.log('schema 3 is readable (lote 5 step 4): validate, new ids, the APK baseline that moves');
if (!(score.schema === 2 && score.golden)) console.log('  info  the score under test is not a schema-2 score with its golden: these cases need one, skipped');
else {
  const clone = o => JSON.parse(JSON.stringify(o)), id = k => idOf(k), near = (a, b, tol = 1e-3) => Math.abs(a - b) <= tol;
  const throws = (s, re) => { try { X.validate(s, E); return false; } catch (e) { return re ? re.test(e.message) : true; } };
  // by hand, what a migrated score holds (the in-app migration is another step): the SHARE branch with four of its elements,
  // an alternative anchor, blocking flags, a knob, a uidMap with a tombstone, an accepted record, the baseline
  const s3 = schema3Copy(score), share = id('G_SHARE'), v36c = id('VO_36c'), v36d = id('VO_36d'), v35b = id('VO_35b'), v35c = id('VO_35c'), v37 = id('VO_37'), gb = id('G_BREATH'), gl = id('G_BELL'), v11h = id('VO_11h');
  const plain = clone(s3);   // schema 3 and nothing else: only the baseline
  s3.branches = { share: { name: 'Share or not', gate: share, options: { yes: { label: 'SHARE', mark: 'SHARE.yes' }, no: { label: "DON'T SHARE", mark: 'SHARE.no' } }, default: 'yes', onTimeout: 'no', note: 'BP_Obra_SC FlowShare' } };
  s3.elements[v36c].branch = { on: 'share', value: 'yes' }; s3.elements[v36d].branch = { on: 'share', value: 'no' };
  s3.elements[v35b].branch = { on: 'share', value: 'yes' }; s3.elements[v35c].branch = { on: 'share', value: 'no' };
  s3.elements[v37].alt = { 'share=no': { at: { ref: v35c, edge: 'end', off: 0 } } };
  s3.elements[gl].gate = Object.assign({}, s3.elements[gl].gate, { blocking: true, cond: 'hall.bell.charged', knob: 'BP_HallDirector_SC.FW_Bell' });
  s3.elements[gb].gate = Object.assign({}, s3.elements[gb].gate, { blocking: false, cond: 'breath.zone' });
  s3.elements[v11h].at = Object.assign({}, s3.elements[v11h].at, { knob: 'BP_BreathStage_SC.HelpAfter' });
  s3.uidMap = { '1.8/G_BELL': { id: gl, sig: '1a2b3c4d5e' }, '@1.8': { id: score.elements[gl].beat, sig: null }, '1.R4/VO_11x': { id: 'el_gone', state: 'deleted-here' } };
  s3.accepted = [{ fp: 'C3.DRIFT|' + gl, rule: 'C3.DRIFT', ly: 'C3', sv: 'warn', el: gl, value: '30|25', state: 'accepted', who: 'B', reason: 'on purpose', at: '2026-10-07T10:00:00Z', rev: 3, history: [{ state: 'accepted', value: '30|25', who: 'B' }] }];

  // validate reads schema 2 and schema 3
  { let r2 = null, r3 = null, rp = null, e3 = '';
    try { r2 = X.validate(score, E); } catch (e) { e3 = e.message; } try { rp = X.validate(plain, E); } catch (e) { e3 = e.message; } try { r3 = X.validate(clone(s3), E); } catch (e) { e3 = e.message; }
    check('validate reads schema 2 (as ever) and schema 3, with every field of the design', !!r2 && !!rp && !!r3, e3);
    check('  a schema 3 that only moved its baseline is the same piece: every time with the typical user, bit for bit', !!rp && JSON.stringify(rp.t) === JSON.stringify(r2.t) && rp.total === r2.total, rp ? rp.total.toFixed(3) : '');
    check('  the engine times the hand-made schema 3 (branches, alt, a stage-clock wait): a finite total, typical user in the default branch', !!r3 && Number.isFinite(r3.total) && r3.branch && r3.branch.share === 'yes', r3 ? r3.total.toFixed(2) + ' s · ' + JSON.stringify(r3.branch) : '');
    check('  a schema 3 survives JSON (what the draft and the file are)', !throws(JSON.parse(JSON.stringify(s3)))); }

  // validate refuses what is not a schema-3 field in shape (each case on its own copy; the message names the problem)
  const rej = [
    ['a schema newer than the editor reads', n => { n.schema = 4; }, /schema 4 score: this editor reads schema 2 and 3/],
    ['a schema that is text', n => { n.schema = '3'; }, /not a schema 2 or 3/],
    ['no schema', n => { delete n.schema; }, /not a schema 2 or 3/],
    ['an element in a branch that does not exist', n => { n.elements[v36c].branch = { on: 'nope', value: 'yes' }; }, /its branch is not a branch option/],
    ['an element in an option that does not exist', n => { n.elements[v36c].branch.value = 'maybe'; }, /its branch is not a branch option/],
    ['a branch that is not { on, value }', n => { n.elements[v36c].branch = 'share=yes'; }, /its branch is not a branch option/],
    ['an element in a branch when the score has none', n => { delete n.branches; }, /branch option/],
    ['a decision with one option', n => { delete n.branches.share.options.no; }, /at least two options/],
    ['a default that is not an option', n => { n.branches.share.default = 'maybe'; }, /default is not one of its options/],
    ['an onTimeout that is not an option', n => { n.branches.share.onTimeout = 'maybe'; }, /onTimeout is not one of its options/],
    ['a deciding gate that is not a wait', n => { n.branches.share.gate = v37; }, /gate is not a wait of the score/],
    ['a branch name with "="', n => { n.branches['a=b'] = clone(n.branches.share); }, /without "="/],
    ['an option name with "="', n => { n.branches.share.options['x=y'] = {}; }, /without "="/],
    ['branches that are a list', n => { n.branches = []; }, /branches is not an object/],
    ['an alt key that is not branch=option', n => { n.elements[v37].alt = { share: { at: { ref: v35c, edge: 'end' } } }; }, /is not "<branch>=<option>"/],
    ['an alt of a branch that does not exist', n => { n.elements[v37].alt = { 'nope=no': { at: { ref: v35c, edge: 'end' } } }; }, /not a branch option of the score/],
    ['an alt of an option that does not exist', n => { n.elements[v37].alt = { 'share=maybe': { at: { ref: v35c, edge: 'end' } } }; }, /not a branch option of the score/],
    ['an alt anchored to something that does not exist', n => { n.elements[v37].alt['share=no'].at.ref = 'el_gone'; }, /points to something that does not exist/],
    ['an alt with nothing in it', n => { n.elements[v37].alt['share=no'] = {}; }, /holds an at and\/or an end anchor/],
    ['an alt with a field that is not an anchor', n => { n.elements[v37].alt['share=no'].dur = 3; }, /holds an at and\/or an end anchor/],
    ['an alt that is a list', n => { n.elements[v37].alt = [1]; }, /alt is not an object/],
    ['an alt anchor with an edge that does not exist', n => { n.elements[v37].alt['share=no'].at.edge = 'middle'; }, /edge is "start" or "end"/],
    ['an alt anchor with an offset that is text', n => { n.elements[v37].alt['share=no'].at.off = '2'; }, /offset is not a number/],
    ['an alt anchor that is not an object', n => { n.elements[v37].alt['share=no'].at = 'x'; }, /an anchor is an object/],
    ['a moment with an alt end (a moment has none)', n => { n.beats[score.elements[v37].beat].alt = { 'share=no': { end: { ref: v35c, edge: 'end' } } }; }, /a moment has no end anchor/],
    ['blocking written as text', n => { n.elements[gb].gate.blocking = 'no'; }, /blocking is true or false/],
    ['blocking null', n => { n.elements[gb].gate.blocking = null; }, /blocking is true or false/],
    ['a wait cond that is a number', n => { n.elements[gl].gate.cond = 5; }, /cond is a name/],
    ['a wait knob that is empty', n => { n.elements[gl].gate.knob = ''; }, /knob is a name/],
    ['an offset knob that is a number', n => { n.elements[v11h].at.knob = 3; }, /at knob is a name/],
    ['a baseline without its relative times', n => { delete n.baseline.rel; }, /relative times \(rel\) are missing/],
    ['a baseline entry that is not [start, length]', n => { n.baseline.rel[v37] = [1]; }, /not \[start in its moment, length\]/],
    ['a baseline entry with text in it', n => { n.baseline.rel[v37] = ['1', 2]; }, /not \[start in its moment, length\]/],
    ['a baseline total that is text', n => { n.baseline.total = 'a'; }, /total is not a number/],
    ['a baseline log that is not a list of records', n => { n.baseline.log = [1]; }, /log is a list of records/],
    ['a uidMap entry without an id', n => { n.uidMap['1.8/G_BELL'] = { sig: 'x' }; }, /not \{ id, sig, state \}/],
    ['a uidMap that is a list', n => { n.uidMap = []; }, /uidMap is not an object/],
    ['an accepted record without a fingerprint', n => { delete n.accepted[0].fp; }, /no fingerprint/],
    ['an accepted record in a state that does not exist', n => { n.accepted[0].state = 'gone'; }, /not accepted or reopened/],
    ['an accepted history that is not a list', n => { n.accepted[0].history = {}; }, /history of .* is not a list/],
    ['an accepted value that is a number', n => { n.accepted[0].value = 30; }, /value of .* is text/],
    ['accepted that is not a list', n => { n.accepted = {}; }, /accepted is not a list/],
  ];
  const missed = rej.filter(([, f, re]) => { const n = clone(s3); f(n); return !throws(n, re); }).map(([w]) => w);
  check(`validate refuses ${rej.length} malformed schema-3 scores (branch, alt, blocking, baseline, uidMap, accepted), each with its own message`, !missed.length, missed.join(' | '));
  // the same structures in a score that says it is schema 2 are refused: the schema number tells every reader which rules apply
  const s2with = [['branches', n => { n.branches = clone(s3.branches); }], ['a branch on an element', n => { n.elements[v36c].branch = { on: 'share', value: 'yes' }; }], ['an alt on an element', n => { n.elements[v37].alt = {}; }],
    ['an alt on a moment', n => { n.beats[score.elements[v37].beat].alt = {}; }], ['gate.blocking', n => { n.elements[gl].gate.blocking = true; }], ['a baseline', n => { n.baseline = clone(s3.baseline); }], ['a uidMap', n => { n.uidMap = {}; }]];
  const missed2 = s2with.filter(([, f]) => { const n = clone(score); f(n); return !throws(n, /schema 2 score can't have .* belong to schema 3/); }).map(([w]) => w);
  check(`a schema 2 score with schema-3 structures is refused (${s2with.length} of them)`, !missed2.length, missed2.join(' | '));
  check('  the control: the same schema 2 without them validates, and the schema-3 field `when` of the prototype is not one of them', !throws(score) && Object.values(score.elements).some(e => e.when));

  // new ids (design B §2)
  { let k = 0; const rnd = () => (k++ % 36) / 36, s = { elements: { el_z0123: {} }, beats: { bt_a: {} }, lanes: {}, uidMap: { '1/X': { id: 'el_z4567' }, '1/Y': { id: 'el_zdead', state: 'deleted-here' } } };
    const n1 = X.newId(s, 'el_', { now: 35, rand: rnd }), n2 = (k = 0, X.newId(s, 'el_', { now: () => 35, rand: rnd, taken: new Set(['el_z89ab']) }));
    check('newId: the time as a number or a function, 4 random characters, never an id in the elements, the uidMap or the batch', n1 === 'el_z89ab' && n2 === 'el_zcdef', n1 + ' · ' + n2);
    const many = new Set(), seen = { elements: {}, beats: {}, lanes: {} }; for (let i = 0; i < 300; i++) { const x = X.newId(seen, 'el_', { taken: many }); many.add(x); }
    check('  without injection: 300 ids of a batch are distinct and the server takes them (el_ + 3 to 40 letters or digits)', many.size === 300 && [...many].every(x => /^el_[A-Za-z0-9]{3,40}$/.test(x)), [...many][0]);
    check('  another prefix (moments, lanes)', /^bt_[0-9a-z]{12}$/.test(X.newId(seen, 'bt_')) && /^ln_/.test(X.newId(seen, 'ln_')));
    const seq = [13, 14, 10, 13, 11, 14, 14, 15]; let q = 0;   // "dead" (a tombstone of the uidMap), then "beef"
    check('  a tombstone of the uidMap keeps its id for good: dead is skipped, beef taken', X.newId(s, 'el_', { now: 35, rand: () => seq[q++] / 36 }) === 'el_zbeef'); }

  // the APK baseline moves with what the APK does: pure, schema 3 (relative to each moment) and schema 2 (absolute)
  { const b0 = plain.baseline, g0 = score.golden, before = JSON.stringify([b0, g0]);
    const vo = id('VO_04'), n = clone(score);
    for (const k of ['VO_04', 'VO_10', 'VO_13', 'VO_15', 'VO_20']) { const x = n.elements[id(k)]; x.dur = { mode: 'audio', value: x.dur.value + 1.5 }; }   // five recordings 1.5 s longer: what follows each one in its moment, and the moments after, move
    const T1 = E.resolve(n, { persona: 'typical' }), A = { score, sched: T0 }, B = { score: n, sched: T1 };
    const entry = { op: 'voices', at: '2026-10-07T12:00:00Z', by: 'B', ids: [vo], src: 'final mix' };
    const all = X.shiftBaseline(b0, A, B, null, entry);
    const relB = id2 => T1.t[id2][0] - T1.t[n.elements[id2].beat][0], lenB = id2 => T1.t[id2][1] - T1.t[id2][0];
    const ids = Object.keys(b0.rel), moved = ids.filter(i => !near(relB(i), b0.rel[i][0]) || !near(lenB(i), b0.rel[i][1]));
    check('shiftBaseline: the baseline becomes what the change does, element by element (start in its moment, length), and the total', ids.every(i => near(all.rel[i][0], relB(i)) && near(all.rel[i][1], lenB(i))) && near(all.total, T1.total) && moved.length > 3, `${moved.length} of ${ids.length} moved · total ${b0.total.toFixed(2)} → ${all.total.toFixed(2)}`);
    check('  the log gets the entry (the old entries stay), the other fields stay', all.log.length === b0.log.length + 1 && JSON.stringify(all.log[all.log.length - 1]) === JSON.stringify(entry) && all.kind === b0.kind);
    check('  pure: the baseline it was given and its arrays are not touched or shared', JSON.stringify([b0, g0]) === before && all !== b0 && all.rel[ids[0]] !== b0.rel[ids[0]] && all.log !== b0.log);
    const one = moved.find(i => i !== vo), sub = X.shiftBaseline(b0, A, B, [one], entry);
    check('  with ids: only those elements move, the rest stays where the APK has it', ids.every(i => i === one ? near(sub.rel[i][0], relB(i)) && near(sub.rel[i][1], lenB(i)) : JSON.stringify(sub.rel[i]) === JSON.stringify(b0.rel[i])), score.elements[one].key);
    const gone = clone(n); delete gone.elements[one]; const Tg = E.resolve(gone, { persona: 'typical' }), sg = X.shiftBaseline(b0, A, { score: gone, sched: Tg }, null, null);
    check('  an element that is no longer there keeps its reference (the APK still has it); no entry, no log record', JSON.stringify(sg.rel[one]) === JSON.stringify(b0.rel[one]) && sg.log.length === b0.log.length);
    // an element that changes moment: its new place is what the APK does (the Entering "Match Unreal" of design B §6.3)
    const dest = score.elements[id('VO_11b')].beat, mv = clone(score); mv.elements[v11h].beat = dest; mv.elements[v11h].at = { ref: dest, edge: 'start', off: 1 };
    const Tm = E.resolve(mv, { persona: 'typical' }), sm = X.shiftBaseline(b0, A, { score: mv, sched: Tm }, [v11h], { op: 'match-unreal', ids: [v11h] });
    check('  an element that moves to another moment: its reference is its place in the new one', near(sm.rel[v11h][0], Tm.t[v11h][0] - Tm.t[dest][0]) && sm.rel[v11h][0] !== b0.rel[v11h][0], `${b0.rel[v11h][0].toFixed(2)} → ${sm.rel[v11h][0].toFixed(2)} s in ${score.beats[dest].key}`);
    const noTotal = X.shiftBaseline({ rel: { [vo]: b0.rel[vo] } }, A, B, null), g1 = X.shiftGolden(g0, T0, T1, { at: entry.at, by: 'B', ids: [vo], src: 'final mix' });
    check('  a baseline with no total takes the one it was measured on', near(noTotal.total, T1.total) && Array.isArray(noTotal.log) && !noTotal.log.length);
    check('shiftGolden (schema 2): every absolute time, moments too, becomes what the change does; the total; the voices record', Object.keys(g0.times).every(k => near(g1.times[k][0], T1.t[k][0]) && near(g1.times[k][1], T1.t[k][1])) && near(g1.total, T1.total) && g1.voices.length === 1 && g1.voices[0].src === 'final mix', `total ${g0.total.toFixed(2)} → ${g1.total.toFixed(2)}`);
    check('  pure too: the golden it was given is not touched', JSON.stringify([b0, g0]) === before && g1.times !== g0.times); }

  // what an import says about the baseline: schema 3 against schema 3, and the form changing from 2 to 3
  { const c3 = clone(plain), f3 = clone(plain), vo = id('VO_04');
    const w0 = X.importWords(X.importDiff(c3, f3));
    check('two schema-3 scores that are the same: nothing about the baseline', !w0.base && !w0.other && !w0.own);
    c3.baseline.log.push({ op: 'voices', at: '2026-10-07T11:00:00Z', by: 'B', ids: [vo], src: 'final mix' });   // a correction in the editor that the file does not have
    const w1 = X.importWords(X.importDiff(c3, f3));
    check('the real voice lengths applied to the baseline of a schema-3 score are named when the file lacks them', /real voice lengths applied on 2026-10-07 \(1 voice\) are not in it/.test(w1.base), w1.base);
    const f4 = clone(f3); f4.baseline.rel[vo] = [f4.baseline.rel[vo][0] + 1, f4.baseline.rel[vo][1]];
    check('  and a reference time that differs, counted', /baseline becomes the file's \(1 reference time differs\)/.test(X.importWords(X.importDiff(f3, f4)).base), X.importWords(X.importDiff(f3, f4)).base);
    const d2 = X.importDiff(score, f3), w2 = X.importWords(d2);
    check('a schema-3 file over a schema-2 score: the baseline changes form, its times are not compared one by one', d2.baseline.form && !d2.baseline.times.changed.length && !d2.baseline.times.gone.length && /baseline becomes the file's\./.test(w2.base), w2.base);
    const noBase = clone(f3); delete noBase.baseline;
    check('a schema-3 file without a baseline: the score would lose it, and the card says so', X.importWords(X.importDiff(f3, noBase)).other === 'Also not in the file: baseline.', X.importWords(X.importDiff(f3, noBase)).other); }

  // the alternative anchors of schema 3 count (review of lote 5 step 5): whoever hangs from something in ONE option of a decision
  // still hangs from it, so deleting it or moving it alone has to know (VO_37 starts from VO_35b in SHARE and from VO_35c in DON'T SHARE)
  console.log('the alternative anchors (alt) are dependents too: delete, move, loops (review of step 5)');
  { const timesAt = (s, o) => E.resolve(s, { persona: 'typical', branch: { share: o } }).t, ok = (a, b) => near(a[0], b[0]) && near(a[1], b[1]);
    const base = clone(s3); base.uidMap['9.7/VO_35c'] = { id: v35c, sig: 'aa' }; base.uidMap['9.7/VO_35b'] = { id: v35b, sig: 'bb' }; base.uidMap['9.7/VO_37'] = { id: v37, sig: 'cc' };
    const before = JSON.stringify(base), kids = E.dependents(base), K = k => (kids[k] || []).map(x => base.elements[x].key);
    check('dependents: VO_37 hangs from VO_35b (its anchor) and from VO_35c (its alt for DON\'T SHARE); once each', K(v35b).join() === 'VO_37' && K(v35c).join() === 'VO_37');
    check('  anchorsOf says which are its own and which are the alternative ones; a moment has no `end`', JSON.stringify(E.anchorsOf(base.elements[v37]).map(x => [x.f, x.k, x.a.ref === v35c])) === JSON.stringify([['at', null, false], ['at', 'share=no', true]])
      && !E.anchorsOf({ at: { ref: 'a' }, end: { ref: 'b' } }, ['at']).some(x => x.f === 'end') && !E.anchorsOf(null).length);
    { const d = clone(score), a = id('VO_10'), b = id('VO_15'); d.elements[b].at = { ref: a, edge: 'start', off: 0 }; d.elements[b].end = { ref: a, edge: 'end', off: 0 };
      check('  a clip that holds the same anchor in `at` and in `end` is listed once, and a schema 2 score has no other kind', E.dependents(d)[a].filter(k => k === b).length === 1 && Object.values(E.dependents(score)).every(l => new Set(l).size === l.length)); }

    for (const [name, ids] of [['VO_35c', [v35c]], ['VO_35b', [v35b]], ['VO_35b and VO_35c', [v35b, v35c]]]) {
      const p = X.planDelete(base, ids, E);
      check(`delete ${name}: VO_37 is seen as hanging from it`, !!p && p.direct.length === 1 && p.direct[0] === v37);
      if (!p) continue;
      for (const [w, v] of [['re-anchor', p.reanchor], ['family', p.family]]) {
        const s = v.next, kept = w === 're-anchor';
        let valid = true; try { X.validate(s, E); } catch (e) { valid = false; }
        check(`  ${w}: nothing dangles, the score is valid${kept ? ', VO_37 stays where it was in SHARE and in DON\'T SHARE, nothing moves' : ', VO_37 goes with it'}`, v.ok && valid && v.dangling === 0 && (kept ? v.moved === 0 && v.kept && ['yes', 'no'].every(o => ok(timesAt(s, o)[v37], timesAt(base, o)[v37])) : !s.elements[v37]),
          kept ? `VO_37 alt ${JSON.stringify(s.elements[v37].alt)}` : `deletes ${v.deleted}`);
        if (kept) {
          const alt = s.elements[v37].alt['share=no'].at, atp = s.elements[v37].at;
          check('  re-anchor: no anchor of VO_37, own or alternative, points to what was deleted', !ids.includes(alt.ref) && !ids.includes(atp.ref) && (!alt.ref || !!s.elements[alt.ref] || !!s.beats[alt.ref]) && (!atp.ref || !!s.elements[atp.ref] || !!s.beats[atp.ref]));
          check('  re-anchor: its own anchor changes only if what it hung from is deleted (VO_35b), its alternative only if VO_35c is', JSON.stringify(atp) === JSON.stringify(ids.includes(v35b) ? atp : base.elements[v37].at) && (ids.includes(v35b) ? atp.ref !== v35b : atp.ref === v35b)
            && (ids.includes(v35c) ? alt.ref !== v35c : JSON.stringify(alt) === JSON.stringify(base.elements[v37].alt['share=no'].at)));
        }
        check(`  ${w}: the uidMap keeps each deleted name as deleted-here, with its id and signature; the others (and the tombstone it already had) are as they were`,
          ids.concat(kept ? [] : [v37]).every(i => { const u = Object.entries(s.uidMap).find(([, q]) => q.id === i); return u && u[1].state === 'deleted-here' && u[1].sig === Object.entries(base.uidMap).find(([, q]) => q.id === i)[1].sig; })
          && Object.entries(s.uidMap).filter(([, q]) => q.state).length === ids.length + (kept ? 0 : 1) + 1 && JSON.stringify(s.uidMap['1.8/G_BELL']) === JSON.stringify(base.uidMap['1.8/G_BELL']) && JSON.stringify(s.uidMap['1.R4/VO_11x']) === JSON.stringify(base.uidMap['1.R4/VO_11x']));
      }
    }
    check('  the plan is pure: the score it was given is exactly as it was', JSON.stringify(base) === before);
    // the uidMap step on its own (the verbs that delete without a plan, and commit() as the safety net)
    { const d = clone(base), gone = id('FX_DISCLAIMER'), uid = '0/FX_DISCLAIMER'; d.uidMap[uid] = { id: gone, sig: 'dd' }; const was = clone(d); delete d.elements[gone];
      const done = X.reconcileUidMap(was, d);
      check('reconcileUidMap: an element that was taken out gets state deleted-here, keeping id and sig; only that one', done.join() === uid && JSON.stringify(d.uidMap[uid]) === JSON.stringify({ id: gone, sig: 'dd', state: 'deleted-here' }) && Object.keys(d.uidMap).filter(k => d.uidMap[k].state).length === 2);
      check('  idempotent; and without a base it marks every dead live name (a score that comes from nowhere)', !X.reconcileUidMap(was, d).length && X.reconcileUidMap(null, Object.assign(clone(was), { elements: {} })).length > 3);
      const dead = clone(base); dead.uidMap['x/OLD'] = { id: 'el_old1' }; const after = clone(dead); delete after.elements[v37];
      check('  a name that was already dead before this edit is not touched (a debt of the base, not of the edit)', X.reconcileUidMap(dead, after).join() === '9.7/VO_37' && !after.uidMap['x/OLD'].state);
      check('  schema 2 (no uidMap) and a moment: nothing to do', !X.reconcileUidMap(score, clone(score)).length && !X.reconcileUidMap(null, null).length);
      const T = clone(base); T.uidMap['t/GONE'] = { id: 'el_k0aaaa', state: 'deleted-here' };
      let again = null; try { again = X.newId(T, 'el_', { now: parseInt('k0', 36), rand: () => 10.5 / 36 }); } catch (e) { again = 'refused'; }
      check('  a tombstoned id is never given to something new (newId counts it as taken)', again === 'refused'); }

    // move alone keeps what hangs from it in its option too
    { const moved = (b, who, dt, alone) => X.move(b, who, dt, { alone }, E.dependents(b)), sh = (s, o) => timesAt(s, o)[v37];
      const A = moved(base, v35c, 2, true), B = moved(base, v35c, 2, false);
      check('move VO_35c alone by 2 s: VO_37 stays where it was in DON\'T SHARE (its alt offset takes the 2 s) and in SHARE', ok(sh(A, 'no'), sh(base, 'no')) && ok(sh(A, 'yes'), sh(base, 'yes')) && near(A.elements[v37].alt['share=no'].at.off, base.elements[v37].alt['share=no'].at.off - 2));
      check('  not alone: VO_37 follows it in DON\'T SHARE (it hangs from its end) and does not in SHARE', near(sh(B, 'no')[0] - sh(base, 'no')[0], 2) && ok(sh(B, 'yes'), sh(base, 'yes')));
      const own = clone(base), x = own.elements[v35c]; x.alt = { 'share=no': { at: { ref: x.at.ref, edge: x.at.edge, off: x.at.off } } };   // in DON'T SHARE VO_35c starts from its alternative: its own `at` is not what moves it there
      const C = moved(own, v35c, 2, true);
      check('  if VO_35c starts from an alternative of its own in DON\'T SHARE, moving its own anchor does not move it there, so VO_37 is not given an offset it does not need', ok(sh(C, 'no'), sh(own, 'no')) && near(C.elements[v37].alt['share=no'].at.off, own.elements[v37].alt['share=no'].at.off));
      const M = X.moveMany(base, [v35c], 2, { alone: true }, E, E.dependents(base));
      check('  moveMany (alone) the same', ok(sh(M, 'no'), sh(base, 'no')) && ok(sh(M, 'yes'), sh(base, 'yes'))); }

    // a loop through an alternative anchor is a loop (the server would refuse it at save)
    { const r = X.reanchor(base, v35c, { ref: v37, edge: 'start' }, E);
      check('anchor VO_35c to the start of VO_37: refused as a loop, because VO_37 starts from the end of VO_35c in DON\'T SHARE', !r.ok && r.loop === true, r.why); }
  }
}
console.log('SHARE / DON\'T SHARE in the editor (lote 5 step 6): the side of an element, "Anchor in DON\'T SHARE", moving where you look');
if (score.schema !== 2) console.log('  info  the score under test is not schema 2: these cases use the migrated fixture, skipped');
else {
  const contract = JSON.parse(fs.readFileSync(path.join(ROOT, 'obra/unreal/contract.json'), 'utf8'));
  const n3 = X.migrate3(score, E, contract, { at: '2026-10-07T12:00:00Z', who: 'B' }).next, clone = o => JSON.parse(JSON.stringify(o)), before = JSON.stringify(n3);
  const K = k => Object.keys(n3.elements).find(i => n3.elements[i].key === k), v35b = K('VO_35b'), v35c = K('VO_35c'), v37 = K('VO_37'), su = K('SOUL_UP');
  const fx = Object.keys(n3.elements).find(i => n3.elements[i].key === 'FX_TITLE' && n3.beats[n3.elements[i].beat].key === '9.7');
  const side = (s, o) => E.resolve(s, { persona: 'typical', branch: { share: o } }).t, near = (a, b, e = 1e-3) => Math.abs(a - b) <= e;
  const T = (s, o) => o ? side(s, o) : E.resolve(s, { persona: 'typical' }).t;
  const TOT = (s, o) => E.resolve(s, { persona: 'typical', branch: o ? { share: o } : undefined }).total;
  const same = (s, a, b) => Object.keys(a).every(k => near(a[k][0], b[k][0]) && near(a[k][1], b[k][1]));
  const kids = E.dependents(n3);

  // what the inspector shows
  { const a = X.branchAnchors(n3, v37);
    check('branchAnchors(VO_37): one anchor of its own in DON\'T SHARE (the end of VO_35c), none that crosses', a.length === 1 && a[0].k === 'share=no' && a[0].field === 'at' && a[0].alt.ref === v35c && !a[0].cross, JSON.stringify(a.map(x => [x.k, x.field, x.cross])));
    const r = X.reanchor(n3, fx, { ref: v35b, edge: 'start' }, E), c = X.branchAnchors(r.next, fx);
    check('  FX_TITLE anchored to VO_35b (SHARE only): it needs an anchor in DON\'T SHARE: cross, no alt', r.ok && c.length === 1 && c[0].k === 'share=no' && c[0].cross && !c[0].alt);
    check('  a clip that hangs from nothing of a branch has none; neither has a score with no branches', !X.branchAnchors(n3, K('AMB_09')).length && !X.branchAnchors(score, v37).length && !X.branchAnchors(n3, 'nope').length);
    const sa = X.branchAnchors(X.setBranch(n3, [su], 'share', 'no').next, K('FX_SOULJOIN'));
    check('  one SHARE clip hanging from a DON\'T SHARE one crosses in SHARE (the other way round)', sa.length === 1 && sa[0].k === 'share=yes' && sa[0].cross, JSON.stringify(sa.map(x => [x.k, x.cross]))); }

  // which side plays it
  { const r = X.setBranch(n3, [su, fx], 'share', 'no');
    check('setBranch: SOUL_UP and FX_TITLE to DON\'T SHARE only', r.ok && r.changed.length === 2 && r.next.elements[su].branch.value === 'no' && r.next.elements[fx].branch.on === 'share', JSON.stringify(r.next.elements[su].branch));
    check('  it is pure, it leaves everything else alone, and the result is a valid schema 3', JSON.stringify(n3) === before && Object.keys(r.next.elements).length === Object.keys(n3.elements).length && (() => { try { X.validate(r.next, E); return true; } catch (e) { return false; } })());
    const b = X.setBranch(r.next, [su], 'share', null);
    check('  to both sides takes the branch out (not a branch with no value)', b.ok && !('branch' in b.next.elements[su]) && b.next.elements[fx].branch.value === 'no');
    check('  already there says so; a decision or a side that does not exist is refused with the reason; a clip that does not exist is skipped', X.setBranch(r.next, [su], 'share', 'no').same === true && !X.setBranch(n3, [su], 'nope', 'no').ok && /no such decision/.test(X.setBranch(n3, [su], 'nope', 'no').why) && /not a side/.test(X.setBranch(n3, [su], 'share', 'maybe').why) && !X.setBranch(n3, ['el_gone'], 'share', 'no').ok && !X.setBranch(score, [su], 'share', 'no').ok); }

  // "Anchor in DON'T SHARE": the same promise as the anchor of lote 4, in one side
  { const r0 = X.reanchor(n3, fx, { ref: v35b, edge: 'start' }, E).next;
    const ra = X.reanchorAlt(r0, fx, 'share=no', { ref: v35c, edge: 'start' }, E);
    check('an anchor of its own in DON\'T SHARE (FX_TITLE to the start of VO_35c): ok, written as `alt`, the primary anchor untouched', ra.ok && ra.k === 'share=no' && ra.field === 'at' && ra.next.elements[fx].alt['share=no'].at.ref === v35c && JSON.stringify(ra.next.elements[fx].at) === JSON.stringify(r0.elements[fx].at) && ra.at.ref === v35c && ra.label === 'DON\'T SHARE', JSON.stringify(ra.next.elements[fx].alt));
    check('  nothing moves, in either side, for any clip or moment (665 + 73)', same(ra.next, T(ra.next), T(r0)) && same(ra.next, T(ra.next, 'no'), T(r0, 'no')) && same(ra.next, T(ra.next, 'yes'), T(r0, 'yes')));
    check('  pure: the score it was given is as it was; the other users are told how they would hear it', JSON.stringify(r0) === JSON.stringify(X.reanchor(n3, fx, { ref: v35b, edge: 'start' }, E).next) && typeof ra.others === 'object' && JSON.stringify(n3) === before);
    // refusals, each with its reason
    const why = (id, k, a, o) => { const r = X.reanchorAlt(n3, id, k, a, E, o); return r.ok ? 'OK' : r.why; };
    check('  VO_37 to the same anchor it has in DON\'T SHARE: refused ("already hangs from")', /already hangs from the end of VO_35c in DON'T SHARE/.test(why(v37, 'share=no', { ref: v35c, edge: 'end' })), why(v37, 'share=no', { ref: v35c, edge: 'end' }));
    check('  to something that does not play in that side (VO_35b in DON\'T SHARE): refused, says which and where', /VO_35b is not there in DON'T SHARE/.test(why(v37, 'share=no', { ref: v35b, edge: 'end' })), why(v37, 'share=no', { ref: v35b, edge: 'end' }));
    check('  to itself, to nothing, to something deleted, to a branch that does not exist: each refused', /to itself/.test(why(v37, 'share=no', { ref: v37, edge: 'start' })) && /Pick a clip/.test(why(v37, 'share=no', { ref: null })) && /no longer exists/.test(why(v37, 'share=no', { ref: 'el_gone', edge: 'start' })) && /no such option/.test(why(v37, 'nope=no', { ref: su, edge: 'start' })) && /no such option/.test(why(v37, 'share=maybe', { ref: su, edge: 'start' })) && /no such option/.test(why(v37, 'share', { ref: su, edge: 'start' })));
    check('  a loop through the alternative of another clip (VO_35c to the start of VO_37, which hangs from VO_35c in DON\'T SHARE): refused', /loop/.test(why(v35c, 'share=no', { ref: v37, edge: 'start' })), why(v35c, 'share=no', { ref: v37, edge: 'start' }));
    check('  a clip that has no end to change, and a moment (no end at all): refused for `end`', /has a length, not an end anchor/.test(why(fx, 'share=no', { ref: v35c, edge: 'start' }, { field: 'end' })) && /has no end anchor/.test(why(n3.elements[fx].beat, 'share=no', { ref: v35c, edge: 'start' }, { field: 'end' })) && /no longer exists/.test(why('nope', 'share=no', { ref: v35c, edge: 'start' })));
    // one that cannot keep every time there is refused with how many things would move, and never written: here the end of L would
    // start to count in its moment in DON'T SHARE (it hangs from something of its own moment there), so the moment gets longer
    { const at = (ref, edge, off) => ({ ref, edge, off: off || 0 }), bt = key => ({ key, title: key, desc: '', act: 0, at: null });
      const el = (key, beat, over) => Object.assign({ key, type: 'world', group: 'world', beat, lane: 'l', at: at(beat, 'start'), end: null, dur: { mode: 'fixed', value: 1 }, gate: null, help: null }, over);   // fx and ambience never count in their moment's end
      const s = { schema: 3, rev: 1, acts: [{ id: 'a', name: 'A', beats: ['b1', 'b2'] }], beats: { b1: bt('1'), b2: bt('2') }, groups: [], lanes: {}, markers: {}, notes: {},
        branches: { share: { name: 'Share', options: { yes: { label: 'SHARE' }, no: { label: "DON'T SHARE" } }, default: 'yes' } },
        elements: { Y: el('Y', 'b1', { dur: { mode: 'fixed', value: 5 }, branch: { on: 'share', value: 'yes' } }), N: el('N', 'b1', { dur: { mode: 'fixed', value: 2 }, branch: { on: 'share', value: 'no' } }),
          Z: el('Z', 'b2', { dur: { mode: 'fixed', value: 3 } }), L: el('L', 'b1', { end: at('Z', 'end') }) } };
      const r = X.reanchorAlt(s, 'L', 'share=no', { ref: 'N', edge: 'end' }, E, { field: 'end' });
      check('  its end in DON\'T SHARE to something of its own moment: refused, because its end would start to count in that moment and the items after it would move', !r.ok && /can't keep its end in DON'T SHARE like that: \d+ items? would move/.test(r.why), r.why || 'OK (written)');
      const r2 = X.reanchorAlt(s, 'L', 'share=yes', { ref: 'Y', edge: 'end' }, E, { field: 'end' });
      check('  the same in SHARE (the default option): the alternative of the default option is judged in the default run', !r2.ok || r2.next.elements.L.alt['share=yes'].end.ref === 'Y', r2.why || 'ok'); }
    // the way back: "the same anchor as everywhere else"
    const ra2 = X.reanchorAlt(n3, fx, 'share=no', { ref: v35c, edge: 'start' }, E), gone = ra2.ok && X.reanchorAlt(ra2.next, fx, 'share=no', null, E);
    check('  and back to "the same anchor as everywhere else": the alternative goes away; the score is exactly what it was', ra2.ok && gone.ok && JSON.stringify(gone.next) === before && gone.at === null, gone.why || ra2.why || '');
    check('  the one that was made on top of a crossing anchor cannot go back (it would hang from something that is not there): refused, nothing written', !X.reanchorAlt(ra.next, fx, 'share=no', null, E).ok && /not there in DON'T SHARE/.test(X.reanchorAlt(ra.next, fx, 'share=no', null, E).why));
    check('  with none to take away it says so; VO_37 cannot go back to the primary one (it hangs from VO_35b, which is not there): refused, nothing written', /no anchor of its own in DON'T SHARE/.test(why(su, 'share=no', null)) && /left hanging from something that is not there in DON'T SHARE/.test(why(v37, 'share=no', null)), why(v37, 'share=no', null));
    // the end of a clip, in a side
    const e0 = clone(n3); e0.elements[fx].end = { ref: v35b, edge: 'end', off: 0 }; e0.elements[fx].alt = {};
    const rb = X.reanchorAlt(e0, fx, 'share=no', { ref: v35c, edge: 'end' }, E, { field: 'end' }), ba = X.branchAnchors(e0, fx);
    check('what a clip lasts until works the same: its `end` in DON\'T SHARE is its own, the start is not touched', rb.ok && rb.field === 'end' && rb.next.elements[fx].alt['share=no'].end.ref === v35c && !rb.next.elements[fx].alt['share=no'].at && ba.some(b => b.field === 'end' && b.cross), JSON.stringify(rb.next && rb.next.elements[fx].alt)); }

  // moving a clip in the side you are looking at
  { const kk = (o, ks) => X.move(n3, v37, o, { ks }, kids), d = T(n3), dn = T(n3, 'no');
    const a = kk(1, ['share=no']);
    check('move VO_37 by 1 s with DON\'T SHARE on screen: its own anchor there moves, the primary one (SHARE) does not', near(a.elements[v37].alt['share=no'].at.off, n3.elements[v37].alt['share=no'].at.off + 1) && JSON.stringify(a.elements[v37].at) === JSON.stringify(n3.elements[v37].at) && near(T(a, 'no')[v37][0], dn[v37][0] + 1) && near(T(a)[v37][0], d[v37][0]));
    const b = kk(1, ['share=yes']), c = kk(1, []), e = kk(1);
    check('  with SHARE on screen, or no side given (a schema 2 caller), the primary anchor moves, as it always did', near(b.elements[v37].at.off, n3.elements[v37].at.off + 1) && near(c.elements[v37].at.off, n3.elements[v37].at.off + 1) && near(e.elements[v37].at.off, n3.elements[v37].at.off + 1) && JSON.stringify(b.elements[v37].alt) === JSON.stringify(n3.elements[v37].alt));
    const o = X.move(n3, K('FX_TITLE'), 1, { ks: ['share=no', 'share=yes'] }, kids), t0 = K('AMB_09');
    check('  a clip with no anchor of its own in the side on screen moves the primary one, whatever the keys', near(o.elements[K('FX_TITLE')].at.off, n3.elements[K('FX_TITLE')].at.off + 1) && !o.elements[K('FX_TITLE')].alt && JSON.stringify(X.move(n3, t0, 2, { ks: ['share=no'] }, kids).elements[t0].at) !== JSON.stringify(n3.elements[t0].at));
    // alone: what hangs from it in that side stays (here something hangs from VO_35c in DON'T SHARE: VO_37)
    const own = clone(n3); own.elements[v35c].alt = { 'share=no': { at: { ref: own.elements[v35c].at.ref, edge: own.elements[v35c].at.edge, off: own.elements[v35c].at.off } } };
    const m = X.move(own, v35c, 2, { alone: true, ks: ['share=no'] }, E.dependents(own));
    check('  alone, with the clip\'s own anchor in that side moving: what hangs from it there keeps its time in DON\'T SHARE (VO_37 takes the 2 s in its alternative offset)', near(T(m, 'no')[v37][0], T(own, 'no')[v37][0]) && near(T(m, 'no')[v35c][0], T(own, 'no')[v35c][0] + 2) && near(T(m)[v37][0], T(own)[v37][0]), `${T(m, 'no')[v37][0]} vs ${T(own, 'no')[v37][0]}`);
    // moveMany leaves the alternatives alone (the primary offsets move: a group is moved in the side everyone shares)
    const mm = X.moveMany(n3, [v37, K('AMB_09')], 1, {}, E, kids);
    check('  a selection of several with no side given is moved on the primary anchors (what they share), every one lands 1 s later in SHARE', near(T(mm)[v37][0], d[v37][0] + 1) && near(T(mm)[K('AMB_09')][0], d[K('AMB_09')][0] + 1)); }

  // a selection moved in the side you are looking at (review: the clip you drag has to move on screen)
  { const d = T(n3), dn = T(n3, 'no'), amb = K('AMB_09'), sel = [v37, amb];
    const mn = X.moveMany(n3, sel, 2, { ks: ['share=no'] }, E, kids), ms = X.moveMany(n3, sel, 2, { ks: ['share=yes'] }, E, kids);
    check('moveMany with DON\'T SHARE on screen: every clip lands 2 s later THERE; VO_37 (its own anchor there) takes it in its alternative and stays where it was in SHARE', near(T(mn, 'no')[v37][0], dn[v37][0] + 2) && near(T(mn, 'no')[amb][0], dn[amb][0] + 2) && near(T(mn)[v37][0], d[v37][0]) && near(mn.elements[v37].alt['share=no'].at.off, n3.elements[v37].alt['share=no'].at.off + 2) && JSON.stringify(mn.elements[v37].at) === JSON.stringify(n3.elements[v37].at), `VO_37 in DON'T SHARE ${dn[v37][0].toFixed(2)} -> ${T(mn, 'no')[v37][0].toFixed(2)}, in SHARE ${d[v37][0].toFixed(2)} -> ${T(mn)[v37][0].toFixed(2)}`);
    check('  the clip with no anchor of its own there moves as it always did (primary anchor: both sides)', near(T(mn)[amb][0], d[amb][0] + 2) && JSON.stringify(mn.elements[amb].at) !== JSON.stringify(n3.elements[amb].at));
    check('  with SHARE on screen: the primary anchors move, VO_37 lands 2 s later in SHARE and does not move in DON\'T SHARE', near(T(ms)[v37][0], d[v37][0] + 2) && near(T(ms, 'no')[v37][0], dn[v37][0]) && JSON.stringify(ms.elements[v37].alt) === JSON.stringify(n3.elements[v37].alt));
    const ma = X.moveMany(n3, [v35c, v37], 1.5, { ks: ['share=no'], alone: true }, E, kids), ma0 = X.moveMany(n3, [v35c, v37], 1.5, { ks: ['share=no'] }, E, kids);
    check('  both of a pair that hang from each other in DON\'T SHARE (VO_35c, VO_37): they land 1.5 s later there, once each, alone or not', near(T(ma0, 'no')[v35c][0], T(n3, 'no')[v35c][0] + 1.5) && near(T(ma0, 'no')[v37][0], T(n3, 'no')[v37][0] + 1.5) && near(T(ma, 'no')[v35c][0], T(n3, 'no')[v35c][0] + 1.5) && near(T(ma, 'no')[v37][0], T(n3, 'no')[v37][0] + 1.5), `${T(ma0, 'no')[v37][0].toFixed(2)} / ${T(ma, 'no')[v37][0].toFixed(2)}`); }

  // copy, paste, duplicate of a clip that has an anchor of its own in the other side (review: the copy hung from the original's neighbour)
  { const b12 = Object.keys(n3.beats).find(b => n3.beats[b].key === '1.2'), b97 = n3.elements[v37].beat, d = T(n3), dn = T(n3, 'no');
    const clip = X.clipOf(n3, [v37], E), item = clip.items[0];
    check('Ctrl+C keeps where the clip is in the other side too (ks), only when there is one', near(item.ks['share=no'].s, dn[v37][0]) && near(item.ks['share=no'].e, dn[v37][1]) && item.ks['share=no'].off === false && !('ks' in X.clipOf(score, [idOf('VO_37')], E).items[0]), JSON.stringify(item.ks));
    const sameT = (a, b) => near(a[0], b[0]) && near(a[1], b[1]);
    // pasted into another moment: it lands in the same place in both sides and nothing hangs from the original's neighbour
    const p = X.planPaste(n3, clip, { beat: b12, off: 1 }, E, { who: 'B', addLane }), c = p.ids && p.ids[0];
    check('paste VO_37 into moment 1.2 (1 s in): the copy starts at 0:27 in SHARE AND in DON\'T SHARE, not at the end of VO_35c', p.ok && near(T(p.next)[c][0], T(p.next)[b12][0] + 1) && near(T(p.next, 'no')[c][0], T(p.next, 'no')[b12][0] + 1) && !JSON.stringify(p.next.elements[c].alt || {}).includes(v35c), p.ok ? `SHARE ${T(p.next)[c][0].toFixed(2)} · DON'T SHARE ${T(p.next, 'no')[c][0].toFixed(2)} · alt ${JSON.stringify(p.next.elements[c].alt)}` : p.why);
    check('  the moment is the same length in both sides, and the totals grow by the same amount in both', p.ok && near(T(p.next, 'no')[b12][1] - T(p.next, 'no')[b12][0], T(p.next)[b12][1] - T(p.next)[b12][0]) && near(TOT(p.next, 'no') - TOT(n3, 'no'), TOT(p.next) - TOT(n3)), p.ok ? `SHARE +${(TOT(p.next) - TOT(n3)).toFixed(2)} · DON'T SHARE +${(TOT(p.next, 'no') - TOT(n3, 'no')).toFixed(2)}` : p.why);
    check('  the plan names the totals of the other sides (the card and the toast can say them)', p.sides.length === 1 && p.sides[0].k === 'share=no' && near(p.sides[0].total0, TOT(n3, 'no')) && near(p.sides[0].total1, TOT(p.next, 'no')));
    check('  the copy is a valid schema 3 and the original is untouched', (() => { try { X.validate(p.next, E); return true; } catch (e) { return false; } })() && JSON.stringify(p.next.elements[v37]) === JSON.stringify(n3.elements[v37]) && JSON.stringify(n3) === before);
    // Ctrl+D and Alt+drag: the copy lands next to the original in each side
    const du = X.planPaste(n3, clip, { after: true }, E, { who: 'B', addLane }), cd = du.ids && du.ids[0];
    check('Ctrl+D VO_37: the copy starts where the original ends in SHARE and where it ends in DON\'T SHARE, each', du.ok && near(T(du.next)[cd][0], d[v37][1]) && near(T(du.next, 'no')[cd][0], dn[v37][1]), du.ok ? `SHARE ${T(du.next)[cd][0].toFixed(2)} (${d[v37][1].toFixed(2)}) · DON'T SHARE ${T(du.next, 'no')[cd][0].toFixed(2)} (${dn[v37][1].toFixed(2)})` : du.why);
    const dr = X.planPaste(n3, clip, { dt: 3 }, E, { who: 'B', addLane }), cr = dr.ids && dr.ids[0];
    check('Alt+drag VO_37 3 s later: 3 s after the original in both sides', dr.ok && near(T(dr.next)[cr][0], d[v37][0] + 3) && near(T(dr.next, 'no')[cr][0], dn[v37][0] + 3));
    check('  and the total of the other side moves exactly as much as the one of SHARE (the same layout in both)', du.ok && dr.ok && near(du.sides[0].total1 - du.sides[0].total0, du.total1 - du.total0) && near(dr.sides[0].total1 - dr.sides[0].total0, dr.total1 - dr.total0), du.ok ? `${(du.total1 - du.total0).toFixed(2)} / ${(du.sides[0].total1 - du.sides[0].total0).toFixed(2)}` : '');
    // a pair that hang from each other in DON'T SHARE: the copy of VO_37 hangs from the copy of VO_35c there
    const pair = X.clipOf(n3, [v35c, v37], E), pp = X.planPaste(n3, pair, { beat: b12, off: 1 }, E, { who: 'B', addLane }), c35 = pp.ok && pp.map[v35c], c37 = pp.ok && pp.map[v37];
    check('paste VO_35c + VO_37: the copy of VO_37 hangs from the end of the COPY of VO_35c in DON\'T SHARE, with the same gap (0 s) as the originals', pp.ok && pp.next.elements[c37].alt['share=no'].at.ref === c35 && pp.next.elements[c37].alt['share=no'].at.edge === 'end' && near(T(pp.next, 'no')[c37][0], T(pp.next, 'no')[c35][1] + (dn[v37][0] - dn[v35c][1])) && near(T(pp.next, 'no')[c35][0], T(pp.next, 'no')[b12][0] + 1), pp.ok ? `VO_37 copy ${T(pp.next, 'no')[c37][0].toFixed(2)} after VO_35c copy ends ${T(pp.next, 'no')[c35][1].toFixed(2)}` : pp.why);
    check('  the copy of VO_35c is DON\'T SHARE only, as the original; SHARE places the pair as they are there (VO_37 from VO_35b\'s place)', pp.ok && pp.next.elements[c35].branch.value === 'no' && near(T(pp.next)[c37][0] - T(pp.next)[b12][0], 1 + d[v37][0] - Math.min(d[v35c][0], d[v37][0])));
    // a pair where the other half only plays in SHARE: VO_37 hangs from the copy of VO_35b in SHARE, from the start of the moment in DON'T SHARE
    const pb = X.planPaste(n3, X.clipOf(n3, [v35b, v37], E), { beat: b12, off: 1 }, E, { who: 'B', addLane }), cb = pb.ok && pb.map[v35b], c37b = pb.ok && pb.map[v37];
    check('paste VO_35b + VO_37: in SHARE the copy of VO_37 follows the copy of VO_35b; in DON\'T SHARE (where VO_35b does not play) it lands 1 s into the moment, with no anchor across sides',
      pb.ok && near(T(pb.next)[c37b][0], T(pb.next)[cb][1]) && near(T(pb.next, 'no')[c37b][0], T(pb.next, 'no')[b12][0] + 1) && E.resolve(pb.next, { persona: 'typical', branch: { share: 'no' } }).crossBranch.length === E.resolve(n3, { persona: 'typical', branch: { share: 'no' } }).crossBranch.length, pb.ok ? '' : pb.why);
    // a score with a clip with two sides that cannot be told apart from SHARE is not given an alternative that says nothing
    const plain = X.planPaste(n3, X.clipOf(n3, [K('AMB_09')], E), { beat: b12, off: 1 }, E, { who: 'B', addLane });
    check('a clip with no alternative anchor is copied exactly as before (no alt appears)', plain.ok && !plain.next.elements[plain.ids[0]].alt);
    // an alternative anchor that ends up the same as the primary one says nothing: it does not stay
    const sa = X.planPaste(n3, clip, { beat: b97, off: 5 }, E, { who: 'B', addLane });
    check('  the copy of a clip whose alternative would end up the same as its primary anchor has none (the inspector lists only what is there)', sa.ok && (!sa.next.elements[sa.ids[0]].alt || Object.keys(sa.next.elements[sa.ids[0]].alt).every(k => JSON.stringify(sa.next.elements[sa.ids[0]].alt[k].at) !== JSON.stringify(sa.next.elements[sa.ids[0]].at))), sa.ok ? JSON.stringify(sa.next.elements[sa.ids[0]].alt) : sa.why); }

  // a score with no branches is not touched by any of it
  { const r = X.reanchorAlt(score, idOf('VO_37'), 'share=no', { ref: idOf('VO_35c'), edge: 'end' }, E);
    check('a schema 2 score: no side to anchor in, said so; moving with sides given is moving as ever', !r.ok && /no such option/.test(r.why) && JSON.stringify(X.move(score, idOf('VO_10'), 1, { ks: ['share=no'] }, E.dependents(score))) === JSON.stringify(X.move(score, idOf('VO_10'), 1, {}, E.dependents(score)))); }
  check('none of this wrote the migrated score', JSON.stringify(n3) === before);
}

console.log('what an edit must not do to a score that was fine (review of the editor, 10-15): Edits.wouldBreak, branchGates, branchError');
if (!(score.schema === 2 && score.golden)) console.log('  info  the score under test is not a schema-2 score with its golden: these cases need one, skipped');
else {
  const clone = o => JSON.parse(JSON.stringify(o)), id = k => idOf(k);
  const s3 = schema3Copy(score), share = id('G_SHARE'), shareIn = id('SHARE_IN');
  s3.branches = { share: { name: 'Share or not', gate: share, options: { yes: { label: 'SHARE', mark: 'SHARE.yes' }, no: { label: "DON'T SHARE", mark: 'SHARE.no' } }, default: 'yes', onTimeout: 'no', note: 'BP_Obra_SC FlowShare' } };
  // the wait that decides SHARE / DON'T SHARE
  const g = X.branchGates(s3, [share]);
  check('branchGates: G_SHARE is the wait that decides "Share or not"', g.length === 1 && g[0].on === 'share' && g[0].key === 'G_SHARE' && g[0].name === 'Share or not');
  check('branchGates: another clip is not, and a schema 2 score has no decision', !X.branchGates(s3, [id('G_BELL')]).length && !X.branchGates(score, [share]).length);
  const gone = clone(s3); delete gone.elements[share];
  check('branchError: the score with its decision is fine; without the deciding wait it says so', X.branchError(s3) === null && /gate is not a wait/.test(X.branchError(gone)));
  check('branchError: a schema 2 score has nothing to say', X.branchError(score) === null);
  // deleting it (the bug: it left a score that could not be saved, and no card said so)
  const w = X.wouldBreak(s3, gone, E);
  check('wouldBreak: taking G_SHARE out is refused, with its words', /would break the score/.test(w) && /gate is not a wait/.test(w) && /nothing changed/.test(w), w);
  check('wouldBreak: a score that was already without it is not blamed again', X.wouldBreak(gone, clone(gone), E) === null);
  const p1 = X.planDelete(s3, [shareIn], E), p2 = X.planDelete(s3, [share], E);
  check('planDelete: deleting SHARE_IN and what hangs from it would take G_SHARE: that way is not offered', p1 && p1.family.ok === false && p1.family.gates.length === 1 && p1.family.gates[0].key === 'G_SHARE');
  check('  deleting only SHARE_IN keeps G_SHARE: that way is still offered', p1 && p1.reanchor.ok === true && !p1.reanchor.gates.length);
  check('  G_SHARE itself: neither way is offered', p2 && p2.reanchor.ok === false && p2.family.ok === false);
  const p3 = X.planDelete(score, [shareIn], E);
  check('  a schema 2 score has no decision: both ways stay open', p3 && p3.family.ok === true && p3.reanchor.ok === true && !p3.family.gates.length);
  // a moment before 0:00 (the Offset of the first moment took -1 s; a clip says "It would start before 0:00")
  const b0 = beatOf('0'), early = clone(s3); early.beats[b0].at = { ref: null, edge: 'start', off: -1 };
  const e1 = X.wouldBreak(s3, early, E);
  check('wouldBreak: the first moment 1 s before 0:00 is refused', /Moment 0 would start before 0:00/.test(e1), e1);
  const later = clone(s3); later.beats[b0].at = { ref: null, edge: 'start', off: 2 };
  check('wouldBreak: the first moment 2 s later is fine', X.wouldBreak(s3, later, E) === null);
  check('wouldBreak: a score that already started before 0:00 is not blamed again', X.wouldBreak(early, clone(early), E) === null);
  // a clip: a copy dropped far to the left (Alt+drag stops at 0:00 by itself; Act.duplicate and Edits.planPaste do not)
  const vo = id('VO_10'), cl = X.clipOf(s3, [vo], E), far = X.planPaste(s3, cl, { dt: -99999 }, E, { who: 'B', addLane }), near1 = X.planPaste(s3, cl, { dt: -0.5 }, E, { who: 'B', addLane });
  const e3 = far.ok ? X.wouldBreak(s3, far.next, E) : 'planPaste refused';
  check('wouldBreak: a copy that lands before 0:00 is refused, with its key', /^VO_10_2 would start before 0:00/.test(e3 || ''), e3);
  check('wouldBreak: a copy half a second earlier is fine (it starts where it must)', near1.ok && X.wouldBreak(s3, near1.next, E) === null, near1.ok ? '' : near1.why);
  const mv = X.move(s3, vo, -99999, {}, E.dependents(s3)), e4 = X.wouldBreak(s3, mv, E);
  check('wouldBreak: a clip moved to before 0:00 is refused too', /would start before 0:00/.test(e4 || ''), e4);
  check('wouldBreak: an ordinary move is fine', X.wouldBreak(s3, X.move(s3, vo, 2, {}, E.dependents(s3)), E) === null);
  // a piece over an hour (a typed 1e9 in a duration made the timeline throw: Invalid string length)
  const huge = clone(s3), bo = id('BACK_OUT'); huge.elements[bo].dur = { mode: 'fixed', value: 1e9 };
  const e2 = X.wouldBreak(s3, huge, E);
  check('wouldBreak: a duration of 1e9 s is refused (the piece would run over an hour)', /longer than an hour/.test(e2), e2);
  const ok = clone(s3); ok.elements[bo].dur = { mode: 'fixed', value: 8 };
  check('wouldBreak: 8 s is fine; a score that was already over an hour is not blamed again', X.wouldBreak(s3, ok, E) === null && X.wouldBreak(huge, clone(huge), E) === null);
  const lim = T0.total + 100, longer = clone(s3); longer.elements[bo].dur = { mode: 'fixed', value: 300 };
  check("wouldBreak: the limit is the caller's (o.maxTotal): 300 s over a limit 100 s above the total is refused, 8 s is not", /longer than an hour/.test(X.wouldBreak(s3, longer, E, { maxTotal: lim }) || '') && X.wouldBreak(s3, ok, E, { maxTotal: lim }) === null);
}

console.log(fails ? `\n${fails} FAILED` : '\nall ok');
process.exit(fails ? 1 : 0);
