// accepted_test.mjs — "accepted means this value" (lote 5 design B §9 and §11 step 9, audit D11): the records of Proceed anyway carry
// the value they were accepted at, a problem reads accepted only at that value, Reopen keeps the record, nothing is removed but by
// "Clean up accepted". Pure Node, no window: integrity.js (fpBase/param, judge, settle, reopenedText, the card's values and `before`),
// policy.js (acceptRecords, reopen, cleanRecords) and the way app.js joins them (staticProblems + divergeProblems + settle).
// It runs on the frozen fixture tools/score/fixtures/f0-score.json (so real edits of the piece never break it); --live runs it on
// obra/score/score.json (see tools/score/test_score.mjs). Nothing here writes anything. Exit 1 if any case fails.
//   node tools/score/accepted_test.mjs [--live]
import fs from 'fs';
import path from 'path';
import { createRequire } from 'module';
import { fileURLToPath } from 'url';
import { testScore, schema3Copy } from './test_score.mjs';
const require = createRequire(import.meta.url);
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const js = f => require(path.join(ROOT, 'web/editor-obra/app/js', f));
const E = js('engine.js'), X = js('edits.js'), P = js('partitura.js'), I = js('integrity.js'), Pol = js('policy.js'), Cal = js('calib.js');
const rd = p => JSON.parse(fs.readFileSync(path.join(ROOT, p), 'utf8'));
const { score, name: SRC } = testScore(); console.log('on the ' + SRC);
const before = JSON.stringify(score);
const contract = rd('obra/unreal/contract.json'), bind = rd('obra/unreal/partitura_binding.json');
const clone = o => JSON.parse(JSON.stringify(o));
const idOf = k => Object.keys(score.elements).find(id => score.elements[id].key === k);
let fails = 0;
const check = (n, ok, info) => { console.log((ok ? '  ok   ' : '  FAIL ') + n + (info ? '  · ' + info : '')); if (!ok) fails++; };
const T = s => E.resolve(s, { persona: 'typical' });
const probs = s => I.staticProblems(s, T(s), contract, E.altRuns(s), {});
// the Problems list as app.js builds it: the static ones + ≠ APK, judged by the same rule and joined (Integrity.settle)
const rows = s => { const t = T(s), gov = s.schema >= 2 ? P.governedBy(s, t, bind) : {}; return I.settle(probs(s), I.divergeProblems(s, t, contract, gov, I.baselineOf(s)), s.accepted || []); };
const items = (prev, op, next) => { const Tp = T(prev), Tn = T(next);
  return I.opItems(Object.assign({ prevScore: prev }, op), next, { problems: probs(prev) }, { problems: probs(next) }, contract, E, { gov: P.governedBy(prev, Tp, bind) }).items; };
const rule = (L, r) => L.filter(p => p.rule === r);
const t1 = '2026-10-07T10:00:00.000Z', t2 = '2026-10-07T11:00:00.000Z', t3 = '2026-10-07T12:00:00.000Z';

console.log('the fingerprint: rule | element | value');
{
  const f = I.fpParts('C3.DRIFT|el_1|30|25'), g = I.fpParts('C2.VO.REAL|'), h = I.fpParts('C2.TOTAL.GOAL||33'), k = I.fpParts('C1.ANCHOR.CYCLE|el_2');
  check('fpBase is the first two parts, the param the rest (its own "|" included)', f.base === 'C3.DRIFT|el_1' && f.param === '30|25' && f.has && g.base === 'C2.VO.REAL|' && g.param === '' && h.base === 'C2.TOTAL.GOAL|' && h.param === '33' && k.base === 'C1.ANCHOR.CYCLE|el_2' && k.param === '' && !k.has);
  const nw = I.recordOf({ fp: 'C3.DRIFT|el_1', value: '30|25', state: 'accepted' }), s2 = I.recordOf({ fp: 'C3.DRIFT|el_1|30|25' }), card = I.recordOf({ fp: 'C3.VO.WIRED|el_1' }), rv = I.recordOf({ fp: 'C3.DRIFT|el_1', value: '30|25', state: 'reopened' });
  check('a record reads the same in its three shapes: new (fp = base + value), schema 2 (the whole fingerprint), a card\'s (rule|el, value unknown)', nw.base === 'C3.DRIFT|el_1' && nw.value === '30|25' && s2.base === nw.base && s2.value === '30|25' && card.value === null && rv.state === 'reopened' && nw.state === 'accepted');
  const probsL = [{ fp: 'C3.DRIFT|el_1|30|25' }, { fp: 'C3.DRIFT|el_1|300|25' }, { fp: 'C3.DRIFT|el_2|30|25' }];
  I.judge(probsL, [{ fp: 'C3.DRIFT|el_1|30|25', who: 'B', reason: 'old shape', at: t1 }]);
  check('a schema-2 record (the whole fingerprint) answers its value only: 30 s accepted, 300 s open and says it was 30, another element open', probsL[0].st === 'accepted' && probsL[1].st === 'open' && probsL[1].was.value === '30|25' && probsL[2].st === 'open' && !probsL[2].was);
  const pc = [{ fp: 'C3.VO.WIRED|el_1' }]; I.judge(pc, [{ fp: 'C3.VO.WIRED|el_1', who: 'B', reason: 'a card', at: t1 }]);
  check('a card\'s old record (no value) answers nothing: the problem is open and says the value was not kept', pc[0].st === 'open' && pc[0].was.value === null && /accepted before \(its value was not kept\) by B \("a card"\)/.test(I.reopenedText(pc[0])), I.reopenedText(pc[0]));
}

console.log('the audit scenario (D11): G_BELL timeout 30 s accepted, later 300 s');
const bell = idOf('G_BELL'), knobFw = 25, set = (s, fw) => { const n = clone(s); n.elements[bell].gate.fw = fw; return n; };
let S30, rec, recD;
{
  const n30 = set(score, 30), it30 = items(score, { type: 'gate', ids: [bell] }, n30);
  const it = it30.find(i => i.rule === 'C3.WAIT.HALL.BELL');
  check('editing the timeout to 30 s opens a card (FW_Bell is a locked final value: it needs a reason); the item knows its value and what Unreal has', !!it && it.sv === 'warn' && it.lock && it.values[bell] === 'gate:30|' + score.elements[bell].gate.expected && it.unreal[bell] === knobFw && it.drift[bell] === '30|25', it && JSON.stringify([it.values, it.unreal, it.drift]));
  const acc = Pol.acceptRecords(n30.accepted, it30, { who: 'B', reason: 'the room needs 30 s', at: t1, rev: 2 });
  rec = acc.find(a => a.fp === 'C3.WAIT.HALL.BELL|' + bell); recD = acc.find(a => a.fp === 'C3.DRIFT|' + bell);
  check('Proceed anyway writes the card\'s record AND the drift it leaves, both at this value, with the state, the revision and what Unreal has', !!rec && !!recD && rec.value === 'gate:30|' + score.elements[bell].gate.expected && rec.verb === 'gate' && rec.state === 'accepted' && rec.rev === 2 && rec.unreal === 25
    && recD.value === '30|25' && recD.state === 'accepted' && recD.rule === 'C3.DRIFT' && recD.unreal === 25 && recD.who === 'B' && recD.reason === 'the room needs 30 s', JSON.stringify([rec && rec.value, recD && recD.value]));
  S30 = Object.assign(clone(n30), { accepted: acc });
  const d30 = rule(probs(S30), 'C3.DRIFT').find(p => p.el === bell);
  check('the drift row reads accepted at 30 s (the record\'s value is its param)', d30 && d30.st === 'accepted' && d30.param === '30|25' && d30.value === '30|25' && d30.who === 'B', d30 && d30.fp);
  const S300 = set(S30, 300), d300 = rule(probs(S300), 'C3.DRIFT').find(p => p.el === bell);
  check('300 s: the same row is OPEN again (before: it stayed accepted forever) and says what it was accepted at', d300 && d300.st === 'open' && d300.was && d300.was.value === '30|25' && d300.was.who === 'B', d300 && JSON.stringify(d300.was));
  check('  "Reopened: accepted at 30 s by B ("…"), now 300 s"', I.reopenedText(d300) === 'Reopened: accepted at 30 s by B ("the room needs 30 s"), now 300 s.', I.reopenedText(d300));
  const back = set(S300, 30), db = rule(probs(back), 'C3.DRIFT').find(p => p.el === bell);
  check('set back to 30 s: accepted again (the record never went away)', db && db.st === 'accepted' && back.accepted.length === S300.accepted.length);
  // the card for the 300 s edit: the break is back, with what was accepted before and its reason (to pre-fill; a click still decides)
  const it300 = items(S30, { type: 'gate', ids: [bell] }, S300).find(i => i.rule === 'C3.WAIT.HALL.BELL');
  check('the edit to 300 s opens the card again, and it says: you accepted this before at 30 s: "…" (the reason pre-fills the box)', it300 && it300.sv === 'warn' && it300.before && it300.before.reason === 'the room needs 30 s' && /timeout 30 s/.test(it300.before.words) && it300.before.who === 'B', it300 && JSON.stringify(it300.before));
  const it30b = items(set(S30, 300), { type: 'gate', ids: [bell] }, S30).find(i => i.rule === 'C3.WAIT.HALL.BELL');
  check('  and back to 30 s the item is only a note (accepted at exactly this value): no card', !it30b || it30b.sv === 'info', it30b && it30b.sv);
}

console.log('Reopen keeps the record');
{
  const rp = Pol.reopen(S30.accepted, 'C3.DRIFT|' + bell + '|30|25', { who: 'S', at: t2 }), r = rp.find(a => a.fp === 'C3.DRIFT|' + bell), r0 = S30.accepted.find(a => a.fp === 'C3.DRIFT|' + bell);
  check('reopening gives state "reopened" and a second entry in the history; the record, its value and its reason stay', rp.length === S30.accepted.length && r.state === 'reopened' && r.history.length === 2 && r.history[0].state === 'accepted' && r.history[0].value === '30|25' && r.history[1].state === 'reopened' && r.history[1].who === 'S' && r.value === '30|25' && r.reason === r0.reason, JSON.stringify(r.history.map(h => h.state)));
  check('  pure: the records it got are as they were (no history on the first one), and reopening what is already open changes nothing', !r0.history && r0.state === 'accepted' && Pol.reopen(rp, 'C3.DRIFT|' + bell, { who: 'S', at: t3 }) === rp);
  const Sr = Object.assign(clone(S30), { accepted: rp }), d = rule(probs(Sr), 'C3.DRIFT').find(p => p.el === bell);
  check('the row is open again at the SAME value, and says who reopened it', d.st === 'open' && d.was.state === 'reopened' && d.was.reopenedBy === 'S' && I.reopenedText(d) === 'Reopened by S: accepted at 30 s by B ("the room needs 30 s").', I.reopenedText(d));
  // reopening the card's own record too (it is a separate row: the card item and the drift are two records)
  const rp2 = Pol.reopen(rp, 'C3.WAIT.HALL.BELL|' + bell, { who: 'S', at: t2 }), Sr2 = Object.assign(clone(S30), { accepted: rp2 });
  const itr = items(set(Sr2, 300), { type: 'gate', ids: [bell] }, Sr2).find(i => i.rule === 'C3.WAIT.HALL.BELL');
  check('  a reopened record answers nothing: the same edit asks again, and the card remembers that it was reopened', itr && itr.sv === 'warn' && itr.before && itr.before.state === 'reopened', itr && JSON.stringify(itr.before));
  const re = Pol.acceptRecords(rp2, items(set(Sr2, 300), { type: 'gate', ids: [bell] }, Sr2), { who: 'B', reason: 'again, with a reason', at: t3, rev: 3 }), rr = re.find(a => a.fp === 'C3.DRIFT|' + bell), rc = re.find(a => a.fp === 'C3.WAIT.HALL.BELL|' + bell);
  check('accepted again after a reopen: back to "accepted", the history keeps all three decisions; the decisions before the reopen no longer answer', rr.state === 'accepted' && rr.history.map(h => h.state).join() === 'accepted,reopened,accepted' && I.decisionsOf(rr).length === 1 && rc.state === 'accepted' && I.decisionsOf(rc).length === 1, rr.history.map(h => h.state).join());
  // accepted at 300 s AFTER the reopen: the 30 s decided before it is not a decision that holds any more
  const n300 = set(Sr2, 300), re300 = Pol.acceptRecords(rp2, items(Sr2, { type: 'gate', ids: [bell] }, n300), { who: 'B', reason: 'now 300 s, on purpose', at: t3, rev: 3 });
  const S300b = Object.assign(clone(n300), { accepted: re300 }), to30 = items(S300b, { type: 'gate', ids: [bell] }, set(S300b, 30)).find(i => i.rule === 'C3.WAIT.HALL.BELL');
  check('  accepted at 300 s after the reopen, going back to 30 s asks again (the 30 s accepted before the reopen no longer holds); 300 s itself is a note', to30 && to30.sv === 'warn' && to30.before && to30.before.value === 'gate:300|5'
    && items(set(S300b, 30), { type: 'gate', ids: [bell] }, S300b).find(i => i.rule === 'C3.WAIT.HALL.BELL').sv === 'info', to30 && JSON.stringify(to30.before));
}

console.log('≠ APK: accepted at one difference, open at another');
{
  const v27 = idOf('VO_27h'), kids = E.dependents(score);
  const m2 = X.move(score, v27, 2, { alone: true }, kids), it2 = items(score, { type: 'move', ids: [v27] }, m2);
  const it = it2.find(i => i.rule === 'C3.CUES.34');
  check('a time edit on something Unreal has wired opens a card; the item carries the ≠ APK it leaves and the place it ends up at', !!it && it.sv === 'warn' && it.apk[v27] === '2.0|0.0' && /^[\d.]+\|[\d.]+\|[\w.]+$/.test(it.values[v27]), it && JSON.stringify([it.apk, it.values]));
  const acc = Pol.acceptRecords(m2.accepted, it2, { who: 'B', reason: 'I will rewire it', at: t1, rev: 2 }), dv = acc.find(a => a.fp === 'C3.DIVERGE|' + v27);
  check('Proceed anyway ALSO accepts that difference, at that value (a C3.DIVERGE record)', !!dv && dv.value === '2.0|0.0' && dv.state === 'accepted' && dv.who === 'B' && dv.reason === 'I will rewire it' && !dv.verb);
  const n2 = Object.assign(clone(m2), { accepted: acc }), L2 = rows(n2), d2 = rule(L2, 'C3.DIVERGE').filter(p => p.el === v27);
  check('the ≠ APK row reads accepted, once (the record listed alone gives way to the real row)', d2.length === 1 && d2[0].st === 'accepted' && d2[0].fp === 'C3.DIVERGE|' + v27 + '|2.0|0.0' && !L2.some(p => p.ghost && p.fpBase === 'C3.DIVERGE|' + v27), d2.map(p => p.fp + ' ' + p.st).join(' | '));
  const m3 = X.move(n2, v27, 1, { alone: true }, E.dependents(n2)), d3 = rule(rows(m3), 'C3.DIVERGE').find(p => p.el === v27);
  check('1 s further (3.0 s): the row is OPEN again and says it was accepted at 2.0 s', d3.st === 'open' && d3.param === '3.0|0.0' && d3.was.value === '2.0|0.0' && I.reopenedText(d3) === 'Reopened: accepted at starts 2.0 s later than the APK by B ("I will rewire it"), now starts 3.0 s later than the APK.', I.reopenedText(d3));
  const it3 = items(n2, { type: 'move', ids: [v27] }, m3).find(i => i.rule === 'C3.CUES.34');
  check('  and the move asks again: the card shows "You accepted this before" with the reason', it3 && it3.sv === 'warn' && it3.before && it3.before.reason === 'I will rewire it');
  const m2b = X.move(m3, v27, -1, { alone: true }, E.dependents(m3)), d2b = rule(rows(Object.assign(m2b, { accepted: acc })), 'C3.DIVERGE').find(p => p.el === v27);
  check('  back to 2.0 s: accepted again', d2b.st === 'accepted');
  // a rename does not change a time: it accepts nothing about ≠ APK
  const ren = clone(n2); X.renameEl(ren.elements[v27], 'VO_27hx'); const itn = items(n2, { type: 'rename', ids: [v27] }, ren);
  check('a rename accepted never writes a ≠ APK record', !itn.some(i => i.apk) && !Pol.acceptRecords([], itn, { who: 'B', reason: 'r', at: t1 }).some(a => a.rule === 'C3.DIVERGE'));
  // a different element is not covered by it (before: any accepted C3 record of an element hid its ≠ APK forever)
  const kd = Object.assign({}, n2.accepted.find(a => a.fp === 'C3.CUES.34|' + v27)), other = X.move(n2, idOf('VO_32h'), 2, { alone: true }, E.dependents(n2)), d32 = rule(rows(other), 'C3.DIVERGE').find(p => p.el === idOf('VO_32h'));
  check('  and an accepted card of VO_27h does not hide the ≠ APK of VO_32h', !!kd && d32 && d32.st === 'open' && !d32.was);
}

console.log('the total: the band decides, as before');
{
  const disc = idOf('DISCLAIMER'), tot = T(score).total, band = Math.floor(tot / 30), over = k => { const n = clone(score); n.elements[disc].dur.value += k; return n; };
  const withRec = (s, value) => Object.assign(clone(s), { accepted: [{ fp: 'C2.TOTAL.GOAL|', value, state: 'accepted', sv: 'warn', ly: 'C2', rule: 'C2.TOTAL.GOAL', who: 'B', reason: 'we know', at: t1 }] });
  const g0 = rule(probs(score), 'C2.TOTAL.GOAL')[0], gA = rule(probs(withRec(score, String(band))), 'C2.TOTAL.GOAL')[0];
  check('C2.TOTAL.GOAL carries its band (floor(total / 30 s)); accepted at this band it reads accepted', g0 && g0.fp === 'C2.TOTAL.GOAL||' + band && g0.param === String(band) && gA.st === 'accepted', g0 && g0.fp);
  const small = rule(probs(withRec(over(10), String(band))), 'C2.TOTAL.GOAL')[0], big = rule(probs(withRec(over(60), String(band))), 'C2.TOTAL.GOAL')[0];
  check('  +10 s in the same band: still accepted; +60 s (two bands up): open again, "accepted at a total over …"', Math.floor(T(over(10)).total / 30) === band ? small.st === 'accepted' : true, '') ;
  check('  and the open one says so', big.st === 'open' && big.was && /^Reopened: accepted at a total over \d+:\d\d by B \("we know"\), now a total over \d+:\d\d\.$/.test(I.reopenedText(big)), I.reopenedText(big));
  const legacy = Object.assign(clone(score), { accepted: [{ fp: 'C2.TOTAL.GOAL||' + band, who: 'B', reason: 'schema 2 record', at: t1 }] });
  check('  a schema-2 record (fp C2.TOTAL.GOAL||<band>) works the same', rule(probs(legacy), 'C2.TOTAL.GOAL')[0].st === 'accepted');
}

console.log('the voices that last differently in the final mix (C2.VO.REAL)');
{
  const gaps = [{ id: 'a', now: 3.2, real: 4.1 }, { id: 'b', now: 2, real: 2.5 }], p1 = I.voiceRealParam(gaps), p2 = I.voiceRealParam(gaps.slice().reverse()), p3 = I.voiceRealParam(gaps.slice(0, 1)), p4 = I.voiceRealParam([{ id: 'a', now: 3.2, real: 4.3 }, gaps[1]]);
  check('the param is how many and which, with their lengths: the same set in any order is the same value; another set or another length is another', p1 === p2 && /^2\|/.test(p1) && p3 !== p1 && p4 !== p1 && /^1\|/.test(p3), [p1, p3, p4].join(' '));
  const row = param => ({ fp: 'C2.VO.REAL||' + param, sv: 'warn', ly: 'C2', rule: 'C2.VO.REAL', el: null });
  const acc = [{ fp: 'C2.VO.REAL|', value: p1, state: 'accepted', who: 'B', reason: 'later', at: t1 }];
  const a = I.judge([row(p1)], acc)[0], b = I.judge([row(p3)], acc)[0];
  check('accepted for these voices: accepted; one voice more or less: open, "accepted at 2 voices … now 1 voice"', a.st === 'accepted' && b.st === 'open' && I.reopenedText(b) === 'Reopened: accepted at 2 voices by B ("later"), now 1 voice.', I.reopenedText(b));
}

console.log('the Unreal run (C3.TRACE.*): the same rule through Calib');
{
  const cmp = { info: {}, stale: [], comparable: true, sections: [{ id: 'S1', name: 'Recognizing', d: -94.2, score: 100, trace: 194, from: 'a', to: 'b' }], rows: [], missing: [], extra: [], unmeasured: [], total: null };
  let ok = true; try { Cal.runLabel(cmp.info, { short: true }); } catch (_) { ok = false; }
  if (ok) {
    const acc = [{ fp: 'C3.TRACE.STAGE|S1', value: '-94', state: 'accepted', who: 'B', reason: 'the loop A12', at: t1 }];
    const a = Cal.problems(cmp, { accepted: acc }).find(p => p.where === 'Recognizing');
    const c2 = clone(cmp); c2.sections[0].d = -95.0;
    const b = Cal.problems(c2, { accepted: acc }).find(p => p.where === 'Recognizing');
    check('a stage accepted at −94 s: accepted while it rounds the same, open at −95 s ("accepted at −94 s … now −95 s")', a.st === 'accepted' && b.st === 'open' && I.reopenedText(b) === 'Reopened: accepted at −94.0 s by B ("the loop A12"), now −95.0 s.', I.reopenedText(b));
  } else console.log('  (skipped: Calib.runLabel needs a trace)');
}

console.log('Clean up accepted: only what was deleted, only when asked');
{
  const el = idOf('VO_10'), gone = idOf('VO_13');
  const recs = [{ fp: 'C2.FLASH|' + el, value: '0.2', state: 'accepted', sv: 'warn', ly: 'C2', rule: 'C2.FLASH', el, who: 'B', reason: 'kept', at: t1 },
    { fp: 'C3.VO.WIRED|' + gone, state: 'accepted', sv: 'block', ly: 'C3', rule: 'C3.VO.WIRED', el: gone, who: 'B', reason: 'old', at: t1 },
    { fp: 'C2.TOTAL.GOAL|', value: '33', state: 'accepted', sv: 'warn', ly: 'C2', rule: 'C2.TOTAL.GOAL', el: null, who: 'S', reason: 'goal', at: t1 }];
  const n = clone(score); n.accepted = recs; delete n.elements[gone];
  const L = probs(n), ghosts = L.filter(p => p.ghost);
  check('the record of a deleted element stays listed, as "element deleted" (gone), until it is cleaned; the others are not touched', ghosts.length >= 1 && ghosts.find(p => p.el === gone).gone === true && !ghosts.some(p => p.el === el && p.gone), ghosts.map(p => p.fp + (p.gone ? ' (gone)' : '')).join(' | '));
  const c = Pol.cleanRecords(n.accepted, n);
  check('Clean up accepted removes exactly the records of deleted elements and keeps the rest (even those without an element)', c.removed.length === 1 && c.removed[0].el === gone && c.next.length === 2 && c.next.every(a => a.el !== gone) && n.accepted.length === 3);
  const rp = Pol.reopen(recs, 'C3.VO.WIRED|' + gone, { who: 'B', at: t2 });
  check('a record reopened is not listed any more (it is not accepted), but it is still there; cleaning takes it too when its element is gone', !probs(Object.assign(clone(n), { accepted: rp })).some(p => p.ghost && p.el === gone) && rp.length === 3 && Pol.cleanRecords(rp, n).removed.length === 1);
  check('the clean-up is a quiet edit (no card), like the other bookkeeping', Pol.QUIET.has('accepted-clean') && Pol.decide({ type: 'accepted-clean', ids: [] }, [], {}).mode === 'quiet');
  check('nothing it did wrote the score or the lists it got', JSON.stringify(recs) === JSON.stringify(n.accepted.length === 3 ? recs : null));
}

console.log('a problem of the piece (C1/C2): the same rule, through the card');
{
  // an appearance of 0.2 s reads as a glitch (C2.FLASH): its value is the length. Accepted at 0.2 s, the card for 1 s further asks again
  const flash = Object.keys(score.elements).find(id => /^(object|world|instruction)$/.test(score.elements[id].type) && !/_(OUT|GAP|WARN)d*$/.test(score.elements[id].key) && !(score.elements[id].dur && score.elements[id].dur.mode === 'fixed' && score.elements[id].dur.value < .3));
  const withLen = (s, v) => { const n = clone(s); n.elements[flash].dur = { mode: 'fixed', value: v }; return n; };
  const n02 = withLen(score, .2), it = items(score, { type: 'trim', ids: [flash] }, n02), fl = it.find(i => i.rule === 'C2.FLASH');
  check('the item of a problem of the piece carries the fingerprint of its problem, value included', !!fl && fl.sv === 'warn' && fl.fp === 'C2.FLASH|' + flash + '|0.2', fl && fl.fp);
  const acc = Pol.acceptRecords(n02.accepted, it, { who: 'B', reason: 'it is a flash on purpose', at: t1, rev: 2 }), rec = acc.find(a => a.rule === 'C2.FLASH');
  check('  Proceed anyway writes rule|element and the length as its value', !!rec && rec.fp === 'C2.FLASH|' + flash && rec.value === '0.2' && rec.state === 'accepted' && rec.rev === 2, rec && JSON.stringify([rec.fp, rec.value]));
  const S02 = Object.assign(clone(n02), { accepted: acc }), S1 = withLen(S02, 1), S01 = withLen(S02, .1);
  check('  the row reads accepted at 0.2 s and is gone at 1 s; at 0.1 s it is OPEN again and says it was 0.2 s', rule(probs(S02), 'C2.FLASH')[0].st === 'accepted' && !rule(probs(S1), 'C2.FLASH').some(p => !p.ghost) && rule(probs(S01), 'C2.FLASH')[0].st === 'open' && /^Reopened: accepted at 0.2 s by B/.test(I.reopenedText(rule(probs(S01), 'C2.FLASH')[0])), I.reopenedText(rule(probs(S01), 'C2.FLASH')[0]));
  // the edit that brings it back
  const again = items(S1, { type: 'trim', ids: [flash] }, S02).find(i => i.rule === 'C2.FLASH'), other = items(S1, { type: 'trim', ids: [flash] }, S01).find(i => i.rule === 'C2.FLASH');
  check('  back to exactly 0.2 s: only a note (no card); at 0.1 s it asks again, with what was accepted before and its reason', again && again.sv === 'info' && other && other.sv === 'warn' && other.before && other.before.reason === 'it is a flash on purpose' && /0.2 s/.test(other.before.words), JSON.stringify([again && again.sv, other && other.before]));
  // the bug the first draft had: the record listed alone after its element is deleted was read as a NEW problem caused by the delete
  const del = clone(S02); delete del.elements[flash];
  const dI = I.opItems({ type: 'delete', ids: [flash], prevScore: S02, removed: { [flash]: S02.elements[flash] } }, del, { problems: probs(S02) }, { problems: probs(del) }, contract, E, { gov: {} });
  check('deleting an element that has an accepted problem causes no item for it (its record is only listed, "element deleted")', !dI.items.some(i => i.rule === 'C2.FLASH') && probs(del).some(p => p.ghost && p.rule === 'C2.FLASH' && p.gone), dI.items.map(i => i.rule).join(', '));
  check('  and a flash that was only a note leaves the policy at "apply" (nothing to review)', Pol.decide({ type: 'trim', ids: [flash] }, [again], {}).mode === 'apply');
}

console.log("the differences that Proceed anyway accepts alongside (≠ APK, a timeout that is not Unreal's)");
{
  const v27 = idOf('VO_27h'), kids = E.dependents(score), m2 = X.move(score, v27, 2, { alone: true }, kids), it2 = items(score, { type: 'move', ids: [v27] }, m2);
  const acc = Pol.acceptRecords(m2.accepted, it2, { who: 'B', reason: 'rewire later', at: t1 }), n2 = Object.assign(clone(m2), { accepted: acc });
  const back = X.move(n2, v27, -2, { alone: true }, E.dependents(n2));
  check('while the element differs the ≠ APK record is the row; once it matches again the record is not listed (there is nothing to accept)', rule(rows(n2), 'C3.DIVERGE').some(p => p.el === v27 && p.st === 'accepted' && !p.ghost) && !rows(back).some(p => p.rule === 'C3.DIVERGE' && p.el === v27) && back.accepted.some(a => a.rule === 'C3.DIVERGE'), '');
  const del = clone(n2); delete del.elements[v27];
  check('  but deleted, its records are listed as "element deleted" until Clean up accepted takes them (the one of the card and the ≠ APK one)', probs(del).filter(p => p.ghost && p.gone && p.el === v27).length >= 2 && Pol.cleanRecords(del.accepted, del).removed.length >= 2);
}

console.log('importing a file does not take a record of one value for another');
{
  const A = { fp: 'C3.DRIFT|el_1', value: '30|25', state: 'accepted', who: 'B', reason: 'a', at: t1 }, B = Object.assign({}, A, { value: '300|25' });
  const cur = Object.assign(clone(score), { accepted: [A, B] }), file = Object.assign(clone(score), { accepted: [A] });
  const d = X.importDiff(cur, file), kept = X.keepOwn(cur, file);
  check('two records of one rule|element at different values are two records: the one the file lacks is carried over, not taken for the other', d.accepted.gone.length === 1 && d.accepted.changed.length === 0 && kept.accepted.length === 2 && kept.accepted.some(a => a.value === '300|25'), JSON.stringify(d.accepted));
}

console.log('schema 3: the same, the migration keeps the records');
{
  const s3 = schema3Copy(score), b3 = idOf('G_BELL'), n = clone(s3); n.elements[b3].gate.fw = 30;
  const it = items(s3, { type: 'gate', ids: [b3] }, n), acc = Pol.acceptRecords(n.accepted, it, { who: 'B', reason: 'on a schema 3 score', at: t1 }), n2 = Object.assign(clone(n), { accepted: acc });
  const d = rule(probs(n2), 'C3.DRIFT').find(p => p.el === b3);
  check('on a schema 3 score the drift accepted at 30 s reads accepted', d && d.st === 'accepted');
  const m = X.migrate3(Object.assign(clone(score), { accepted: [{ fp: 'C3.DRIFT|' + bell + '|30|25', who: 'B', reason: 'schema 2 record', at: t1 }, { fp: 'C3.VO.WIRED|' + idOf('VO_10'), who: 'B', reason: 'card', at: t1 }] }), E, contract, { at: t1, who: 'B' });
  const q = m.next && m.next.accepted;
  check('the migration splits the fingerprint (fp = rule|element, value = the rest; null for a card\'s record) and the record still answers at its value', !!q && q[0].fp === 'C3.DRIFT|' + bell && q[0].value === '30|25' && q[1].fp === 'C3.VO.WIRED|' + idOf('VO_10') && q[1].value === null && q.every(a => a.state === 'accepted'), q && JSON.stringify(q.map(a => [a.fp, a.value])));
  if (m.next) { const nn = clone(m.next); nn.elements[bell].gate.fw = 30; const dm = rule(probs(nn), 'C3.DRIFT').find(p => p.el === bell); check('  (G_BELL at 30 s on the upgraded score: accepted; at 25 s there is no drift to accept)', dm && dm.st === 'accepted' && !rule(probs(m.next), 'C3.DRIFT').some(p => p.el === bell)); }
}

check('the score of the test was never changed', JSON.stringify(score) === before);
console.log(fails ? `\n${fails} FAILED` : '\nall ok');
process.exit(fails ? 1 : 0);
