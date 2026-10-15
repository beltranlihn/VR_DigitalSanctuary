// waits_test.mjs — waits as Unreal does them (lote 5 design B §6.1-§6.2, step 7): the "Waits for the user" flag of a wait
// (`gate.blocking`, schema 3), the rules that read it (C2.WAIT.WHERE, C3.BLOCKING, C3.NOTBLOCKING retired), the card of the
// edit that changes it and what the timeline and the inspector show (View.waitReaction, View.waitUsers). Pure, against the
// score of the piece: schema 2 keeps today's behaviour, the schema-3 copy is the owner's "Upgrade to schema 3" made in memory.
// Logic: web/editor-obra/app/js/integrity.js, view.js, engine.js, policy.js. Exit 1 if any case fails.
// It runs on the frozen fixture tools/score/fixtures/f0-score.json (so real edits of the piece never break it); with --live it
// reads obra/score/score.json (a schema 3 score is checked as it is, a schema 2 one is upgraded in memory first).
//   node tools/score/waits_test.mjs [--live]
import fs from 'fs';
import path from 'path';
import { createRequire } from 'module';
import { fileURLToPath } from 'url';
import { testScore } from './test_score.mjs';
const require = createRequire(import.meta.url);
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const E = require(path.join(ROOT, 'web/editor-obra/app/js/engine.js'));
const X = require(path.join(ROOT, 'web/editor-obra/app/js/edits.js'));
const I = require(path.join(ROOT, 'web/editor-obra/app/js/integrity.js'));
const V = require(path.join(ROOT, 'web/editor-obra/app/js/view.js'));
const P_ = require(path.join(ROOT, 'web/editor-obra/app/js/policy.js'));
const rd = p => JSON.parse(fs.readFileSync(path.join(ROOT, p), 'utf8'));
const { score, name: SRC } = testScore(); console.log('on the ' + SRC);
const contract = rd('obra/unreal/contract.json');
const clone = o => JSON.parse(JSON.stringify(o));
const before = JSON.stringify(score);
let fails = 0;
const check = (n, ok, info) => { console.log((ok ? '  ok   ' : '  FAIL ') + n + (info ? '  · ' + info : '')); if (!ok) fails++; };
const near = (a, b, eps) => Math.abs(a - b) < (eps || 1e-3);
const probs = (s, c) => { const T = E.resolve(s, { persona: 'typical' }); return I.staticProblems(s, T, c === undefined ? contract : c, E.altRuns(s)); };
const rule = (L, r) => L.filter(p => p.rule === r);
const tot = (s, k) => E.resolve(s, { persona: k }).total;
const USERS = ['fast', 'typical', 'slow', 'idle'];

// the score under test, schema 2 and schema 3 (the upgrade in memory when the score is still schema 2)
const s2 = score.schema === 2 ? score : null;
const s3 = score.schema >= 3 ? clone(score) : X.migrate3(score, E, contract, { at: '2026-10-07T12:00:00Z', who: 'B' }).next;
const K = (s, k) => Object.keys(s.elements).find(i => s.elements[i].key === k);
const bel = K(s3, 'G_BELL'), breath = K(s3, 'G_BREATH'), heart = K(s3, 'G_HEART'), save4 = K(s3, 'G_SAVE4'), share = K(s3, 'G_SHARE');
const flag = (s, id, v) => { const n = clone(s); n.elements[id].gate.blocking = v; return n; };

console.log('the flag, as the upgrade writes it');
check('the ten waits carry a boolean: the Hall, SHARE and SAVE waits block, G_BREATH / G_HEART / G_GRAB / G_DRAW run on the stage clock',
  Object.values(s3.elements).filter(e => e.gate).length === 10 && Object.values(s3.elements).filter(e => e.gate && e.gate.blocking === false).map(e => e.key).sort().join(',') === 'G_BREATH,G_DRAW,G_GRAB,G_HEART'
  && [bel, save4, share].every(id => s3.elements[id].gate.blocking === true));
check('  View.clockWait says the same (and false for anything that is not a wait)', V.clockWait(s3.elements[breath]) && !V.clockWait(s3.elements[bel]) && !V.clockWait(s3.elements[K(s3, 'VO_10')]) && !V.clockWait(null));

console.log('schema 2: today\'s behaviour');
if (!s2) console.log('  info  the score under test is already schema 3: the schema 2 cases are skipped (run on the frozen fixture)');
else {
  const P2 = probs(s2);
  check('C3.NOTBLOCKING (info) is still there for the four stage-clock waits, and nothing says C3.BLOCKING', rule(P2, 'C3.NOTBLOCKING').length === 4 && rule(P2, 'C3.NOTBLOCKING').every(p => p.sv === 'info') && !rule(P2, 'C3.BLOCKING').length, rule(P2, 'C3.NOTBLOCKING').map(p => s2.elements[p.el].key).join(', '));
  // the rule as it always was: a wait Unreal does not know, in a moment of a stage
  const old = Object.keys(s2.elements).filter(id => s2.elements[id].gate && !I.contractFor(id, s2.elements[id], contract).length && /^(\d\.R|V\d|\d\.(coda|close|release))/.test(s2.beats[s2.elements[id].beat].key)).sort();
  check('C2.WAIT.WHERE is the same rows as the rule of before (a wait Unreal does not know, in a stage)', JSON.stringify(rule(P2, 'C2.WAIT.WHERE').map(p => p.el).sort()) === JSON.stringify(old), old.length + ' rows');
  check('no schema 2 wait has the flag: every wait blocks (the prototype\'s way)', Object.values(s2.elements).every(e => !e.gate || e.gate.blocking === undefined));
  // the table of the inspector is the one it always was: the simulated user's wait, and the help from `helpActive`
  const g2 = K(s2, 'G_BREATH'), u2 = V.waitUsers(s2, E, g2);
  check('  the simulated users of G_BREATH read 1.8 · 6 · 15.5 · 25 s (Persona.wait), help only for the slow and the idle ones', u2.map(u => +u.acts.toFixed(2)).join(' ') === '1.8 6 15.5 25' && u2.map(u => u.help).join() === 'false,false,true,true');
  check('  and no tail is drawn for any of them (a schema 2 wait blocks: its length is the user\'s)', USERS.every(k => { const r = E.resolve(s2, { persona: k }); return V.waitReaction(s2.elements[g2], r.t[g2], r.react[g2], E.PERSONAS[k].name) === null; }));
}

console.log('schema 3 as upgraded: nothing to say');
{
  const P3 = probs(s3);
  check('C3.NOTBLOCKING is retired (the flag says it itself) and C3.BLOCKING / C2.WAIT.WHERE have nothing to say about the ten waits', !rule(P3, 'C3.NOTBLOCKING').length && !rule(P3, 'C3.BLOCKING').length && !rule(P3, 'C2.WAIT.WHERE').length);
  check('  every wait agrees with the contract (blockingClash is null for all ten)', Object.keys(s3.elements).filter(id => s3.elements[id].gate).every(id => I.blockingClash(id, s3.elements[id], contract) === null));
}

console.log('toggling a wait to what Unreal does not do');
{
  const n = flag(s3, breath, true), P = probs(n), c = rule(P, 'C3.BLOCKING');
  check('G_BREATH to "waits for the user" (Unreal runs it on the stage clock): one C3.BLOCKING, a warn, with the owner and the fingerprint of the value', c.length === 1 && c[0].sv === 'warn' && c[0].ly === 'C3' && c[0].el === breath && c[0].fp === `C3.BLOCKING|${breath}|blocks` && /Entering_Stage/.test(c[0].own), c.map(p => p.fp + ' · ' + p.own).join(' | '));
  check('  its words say what Unreal does and what the slow user would live (up to 19.0 s more)', /G_BREATH waits for the user here, but in Unreal the stage runs on its clock/.test(c[0].msg) && /up to 19\.0 s more than in Unreal/.test(c[0].msg), c[0].msg);
  check('  C2.WAIT.WHERE does not say it a second time (one row for one cause)', !rule(P, 'C2.WAIT.WHERE').some(p => p.el === breath));
  const t0 = E.resolve(s3, { persona: 'typical' }), t1 = E.resolve(n, { persona: 'typical' });
  check('  Fast and Typical do not change at all; every one of the 665 times of the typical user stays', near(tot(n, 'fast'), tot(s3, 'fast')) && near(tot(n, 'typical'), tot(s3, 'typical')) && JSON.stringify(t0.t) === JSON.stringify(t1.t));
  const w0 = E.resolve(s3, { persona: 'idle' }), w1 = E.resolve(n, { persona: 'idle' }), len = r => r.t[breath][1] - r.t[breath][0];
  check('  the Idle user waits 19.0 s more at G_BREATH (25 s instead of the 6 s clock)', near(len(w1) - len(w0), 19.0), `${len(w0).toFixed(1)} → ${len(w1).toFixed(1)} s`);
  const dI = tot(n, 'idle') - tot(s3, 'idle'), dS = tot(n, 'slow') - tot(s3, 'slow');
  check('  and the Idle total grows (+18.2 s: the moment already ran 0.8 s past the end of the 6 s wait) and the Slow one (+8.7 s)', near(dI, 18.167, 5e-3) && near(dS, 8.667, 5e-3) && dI > 0 && dS > 0, `idle +${dI.toFixed(3)} · slow +${dS.toFixed(3)}`);
  // the reaction elements stop following the user: nothing hangs from the end of a blocking wait except through its end
  const ghost = K(s3, 'GHOST_BREATH');
  check('  GHOST_BREATH (hangs from the end of the wait) no longer follows the user: it now follows the longer wait', ghost && E.resolve(s3, { persona: 'idle' }).reactive.includes(ghost) && !w1.reactive.includes(ghost));
}
{
  const n = flag(s3, bel, false), c = rule(probs(n), 'C3.BLOCKING');
  check('G_BELL to "runs on the stage clock" (Unreal waits for the user at FW_Bell): C3.BLOCKING, a warn, in the other direction', c.length === 1 && c[0].sv === 'warn' && c[0].fp === `C3.BLOCKING|${bel}|clock` && /runs on the stage clock here, but in Unreal the piece waits for the user/.test(c[0].msg) && /A slow user would not be waited for/.test(c[0].msg), c.map(p => p.msg).join(' | '));
  check('  a Partitura wait (G_SHARE, G_SAVE4) says it too', [share, save4].every(id => rule(probs(flag(s3, id, false)), 'C3.BLOCKING').length === 1));
  check('  the Slow and the Idle users no longer hold the Hall back (their totals go down); Typical does not move', tot(n, 'idle') < tot(s3, 'idle') && tot(n, 'slow') < tot(s3, 'slow') && near(tot(n, 'typical'), tot(s3, 'typical')));
}
{
  const n = flag(flag(s3, breath, true), breath, false);
  check('putting it back to what Unreal does clears it: the problems are the ones of before', JSON.stringify(probs(n).map(p => p.fp).sort()) === JSON.stringify(probs(s3).map(p => p.fp).sort()));
  check('a wait the contract does not know (a new one) can be either way without C3.BLOCKING', (() => { const m = clone(s3), id = 'el_newwait'; m.elements[id] = Object.assign(clone(m.elements[breath]), { key: 'G_NEW', isNew: true, help: null }); delete m.elements[id].bind;
    return !rule(probs(m), 'C3.BLOCKING').length && !rule(probs(flag(m, id, true)), 'C3.BLOCKING').length; })());
}

console.log('C2.WAIT.WHERE reads the flag (schema 3)');
{
  const at = (ref, edge, off) => ({ ref, edge, off: off || 0 });
  const mini = (beatKey, gate, key, schema) => ({ schema: schema || 3, rev: 1, acts: [{ id: 'a', name: 'A', beats: ['b1'] }], beats: { b1: { key: beatKey, title: beatKey, desc: '', act: 0, at: null } }, groups: [], lanes: {}, markers: {}, notes: {},
    elements: { G: { key: key || 'G_X', type: 'wait', group: 'int', beat: 'b1', lane: 'l', at: at('b1', 'start'), end: null, dur: { mode: 'elastic', value: 6 }, gate, help: null }, H: { key: 'H_X', type: 'vo', group: 'vo', beat: 'b1', lane: 'l', at: at('G', 'start', 3), end: null, dur: { mode: 'fixed', value: 1 }, gate: null, help: 'G' } } });
  const where = (s, c) => rule(probs(s, c), 'C2.WAIT.WHERE').length;
  check('a wait that blocks inside a stage that Unreal does not know: warns', where(mini('3.R4', { expected: 6, fw: 25, blocking: true }), null) === 1);
  check('  the same wait on the stage clock: nothing to say', where(mini('3.R4', { expected: 6, fw: 25, blocking: false }), null) === 0);
  check('  a wait with no flag blocks (the default), and warns too', where(mini('3.R4', { expected: 6, fw: 25 }), null) === 1);
  check('  a SAVE wait blocks on purpose (G_SAVE9 in a stage): nothing', where(mini('3.R5', { expected: 6, fw: 25, blocking: true }, 'G_SAVE9'), null) === 0);
  check('  in the Hall it blocks as it should (moment 1.8): nothing', where(mini('1.8', { expected: 6, fw: 25, blocking: true }), null) === 0);
  check('  a schema 2 score with the same wait keeps asking whether Unreal knows it (it has no flag)', where(mini('3.R4', { expected: 6, fw: 25 }, null, 2), null) === 1 && where(mini('3.R4', { expected: 6, fw: 25 }, 'G_BELL', 2), { entries: [{ id: 'wait.hall.bell', kind: 'knob', match: { key: '^G_BELL$' }, owner: 'x', msg: 'x', knob: { name: 'k', value: 25 } }] }) === 0);
  // a wait the contract knows, set to block inside a stage: C3.BLOCKING speaks, C2.WAIT.WHERE stays quiet (one row for one cause)
  const n = flag(s3, heart, true), P = probs(n);
  check('the contract knows G_HEART (stage clock): set to block it is one C3.BLOCKING and no C2.WAIT.WHERE', rule(P, 'C3.BLOCKING').filter(p => p.el === heart).length === 1 && !rule(P, 'C2.WAIT.WHERE').some(p => p.el === heart));
}

console.log('the card of the edit (op gate, what: blocking)');
{
  const T0 = E.resolve(s3, { persona: 'typical' }), P0 = probs(s3);
  const judge = (prev, op, next) => { const Pp = probs(prev), Pn = probs(next); return I.opItems(Object.assign({ prevScore: prev }, op), next, { problems: Pp }, { problems: Pn }, contract, E, { gov: {} }); };
  const op = id => ({ type: 'gate', what: 'blocking', ids: [id] });
  const n = flag(s3, breath, true), r = judge(s3, op(breath), n), items = r.items;
  check('G_BREATH to "waits for the user": one item, the C3.BLOCKING warn with the words of Problems, and the policy opens a card that breaks', items.length === 1 && items[0].rule === 'C3.BLOCKING' && items[0].sv === 'warn' && items[0].body === rule(probs(n), 'C3.BLOCKING')[0].msg && P_.decide(op(breath), items, {}).mode === 'card' && P_.decide(op(breath), items, {}).breaks, items.map(i => i.rule + ' ' + i.sv).join(', '));
  check('  the ripple stays quiet (the typical user does not move)', !r.ripple && r.effect.changed.length === 0, JSON.stringify(r.ripple));
  const acc = P_.acceptRecords(n.accepted, items, { who: 'B', reason: 'testing', at: '2026-10-07T12:00:00Z' }), n2 = Object.assign(clone(n), { accepted: acc });
  check('"Proceed anyway" writes the fingerprint of the row Problems shows: afterwards that row reads accepted', acc.length === 1 && acc[0].fp === `C3.BLOCKING|${breath}` && acc[0].value === 'blocks' && acc[0].verb === 'gate' && rule(probs(n2), 'C3.BLOCKING')[0].st === 'accepted');
  check('  accepted for this value: the same toggle later is only an info (no card)', (() => { const r2 = judge(Object.assign(clone(s3), { accepted: acc }), op(breath), n2); return r2.items.length === 1 && r2.items[0].sv === 'info' && P_.decide(op(breath), r2.items, {}).mode === 'apply'; })());
  const back = judge(n2, op(breath), flag(n2, breath, false));
  check('back to what Unreal does: no item, no card (aligning removes a break)', back.items.length === 0 && P_.decide(op(breath), back.items, {}).mode === 'apply');
  const r3 = judge(s3, op(bel), flag(s3, bel, false));
  check('G_BELL to the stage clock: the item says Unreal waits there, with FW_Bell\'s owner', r3.items.length === 1 && r3.items[0].rule === 'C3.BLOCKING' && /in Unreal the piece waits for the user/.test(r3.items[0].body) && /HallDirector/.test(r3.items[0].ev), r3.items.map(i => i.ev).join());
  const r4 = judge(s3, { type: 'gate', ids: [bel] }, (() => { const m = clone(s3); m.elements[bel].gate.fw = 30; return m; })());
  check('the other "gate" edit, the timeout, is judged as before (the knob of the Hall: a warn, never the flag)', r4.items.length === 1 && /^C3\.WAIT\.HALL\.BELL/i.test(r4.items[0].rule) && r4.items[0].rule !== 'C3.BLOCKING', r4.items.map(i => i.rule).join());
  // a wait the contract does not know, in a stage, made to block: the card is the rule of the piece
  const m = clone(s3), id = 'el_newwait'; m.elements[id] = Object.assign(clone(m.elements[breath]), { key: 'G_NEW', isNew: true, help: null }); delete m.elements[id].bind; m.elements[id].gate.blocking = false;
  const r5 = judge(m, op(id), flag(m, id, true));
  check('a new wait in a stage made to block: the card says "A wait where Unreal does not wait" (C2.WAIT.WHERE)', r5.items.some(i => i.rule === 'C2.WAIT.WHERE' && /does not wait/.test(i.title)) && P_.decide(op(id), r5.items, {}).mode === 'card', r5.items.map(i => i.rule).join());
}

console.log('the timeline and the inspector (View.waitReaction, View.waitUsers)');
{
  const t = (s, k) => E.resolve(s, { persona: k });
  const rt = k => { const r = t(s3, k); return V.waitReaction(s3.elements[breath], r.t[breath], r.react[breath], E.PERSONAS[k].name); };
  const s = t(s3, 'slow'), i = t(s3, 'idle'), f = t(s3, 'fast'), ty = t(s3, 'typical');
  check('the wait draws its clock for everybody: 6 s for Fast, Typical, Slow and Idle', [f, ty, s, i].every(r => near(r.t[breath][1] - r.t[breath][0], 6)));
  check('no tail for Typical (it acts right on the clock) nor for Fast (it acts before it ends)', rt('typical') === null && rt('fast') === null);
  const a = rt('slow'), b = rt('idle');
  check('the Slow user\'s tail runs from the end of the clock to 15.5 s after the wait starts, labelled "the slow user acts here · the stage does not wait"', a && near(a.from, s.t[breath][0] + 6) && near(a.to, s.t[breath][0] + 15.5) && a.label === 'the slow user acts here · the stage does not wait', a && a.label);
  check('  the Idle user\'s ends at its timeout (25 s)', b && near(b.to, i.t[breath][0] + 25) && b.label === 'the idle user acts here · the stage does not wait');
  check('  a wait that blocks (G_BELL) has no tail for anybody, and neither has a thing that is not a wait', USERS.every(k => { const r = t(s3, k); return V.waitReaction(s3.elements[bel], r.t[bel], r.react[bel], k) === null && V.waitReaction(s3.elements[K(s3, 'VO_10')], r.t[K(s3, 'VO_10')], 0, k) === null; }));
  const u = V.waitUsers(s3, E, breath);
  check('the per-user table of G_BREATH reads "acts at" 1.8 · 6 · 15.5 · 25 s from the engine\'s react; help plays for Slow and Idle only (the line comes 12 s in)', u.map(x => +x.acts.toFixed(2)).join(' ') === '1.8 6 15.5 25' && u.map(x => x.help).join() === 'false,false,true,true', u.map(x => x.name + ' ' + x.acts.toFixed(1) + ' ' + x.help).join(' · '));
  const ub = V.waitUsers(s3, E, bel);
  check('  a blocking wait (G_BELL) lists its own simulated waits, as before (1.5 · 5 · 15 · 25 s)', ub.map(x => +x.acts.toFixed(2)).join(' ') === '1.5 5 15 25');
  check('  a wait with no help line says "—" (null)', (() => { const m = clone(s3); for (const e of Object.values(m.elements)) if (e.help === breath) e.help = null; return V.waitUsers(m, E, breath).every(x => x.help === null); })());
  // the help line of the stage clock follows the user: a help line that plays at 12 s plays for the one who acts at 15.5 and 25, not for the one who acts at 6
  const h = K(s3, 'VO_11h'), r = t(s3, 'slow');
  check('helpActive follows react, not the clock: VO_11h (12 s in) plays for Slow and Idle even though the 6 s clock ended before', h && r.helpActive[h] === true && t(s3, 'idle').helpActive[h] === true && t(s3, 'typical').helpActive[h] === false && t(s3, 'fast').helpActive[h] === false);
  check('  and made a blocking wait, a slow user holds the stage: the line is still on time for them and the tail is gone', (() => { const n = flag(s3, breath, true), q = E.resolve(n, { persona: 'slow' }); return q.helpActive[h] === true && V.waitReaction(n.elements[breath], q.t[breath], q.react[breath], 'Slow') === null; })());
}

console.log('the simulated user never changes what is written or checked');
{
  // compute() in app.js: schedT is the typical user in the default option, whoever is on screen. Resolving the other users first
  // (what the timeline does when you pick Slow) must leave it exactly as it was, and flipping the flag must not change it either
  const base = JSON.stringify(E.resolve(s3, { persona: 'typical' }));
  const after = USERS.map(k => { E.resolve(s3, { persona: k }); return JSON.stringify(E.resolve(s3, { persona: 'typical' })); });
  check('resolving fast, slow and idle in between never changes the typical schedule (the one that decides writes, effects and "≠ APK")', after.every(x => x === base));
  const P = JSON.stringify(probs(s3).map(p => p.fp)), P2 = (E.resolve(s3, { persona: 'idle' }), JSON.stringify(probs(s3).map(p => p.fp)));
  check('  and the problems are the same before and after looking at the idle user', P === P2);
  check('  with the flag flipped, the typical times are still the ones of the upgrade (665/665: nothing moves for Typical)', USERS.slice(0, 2).every(k => JSON.stringify(E.resolve(flag(s3, breath, true), { persona: 'typical' }).t) === JSON.stringify(E.resolve(s3, { persona: 'typical' }).t)));
}

check('none of this wrote the score (the fixture is as it was read)', JSON.stringify(score) === before);
console.log(fails ? `\n${fails} FAILED` : '\nall ok');
process.exit(fails ? 1 : 0);
