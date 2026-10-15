// engine_test.mjs — engine v3 (lote 5, design B §3): branches, alternative anchors, non-blocking waits, reaction anchors.
// Small synthetic schema-3 scores, one rule at a time, and the real piece (the frozen fixture F0) with its four stage-clock waits.
// Schema-2 parity (nothing changes when a score uses none of this) is golden_test.mjs, against the prototype's own times.
//   node tools/score/engine_test.mjs        (exit code 1 on failure)
import path from 'node:path';
import { createRequire } from 'node:module';
import { ROOT, readFixture, readExpect } from './test_score.mjs';
const require = createRequire(import.meta.url);
const E = require(path.join(ROOT, 'web/editor-obra/app/js/engine.js'));
let fails = 0;
const check = (name, ok, info) => { console.log((ok ? '  ok   ' : '  FAIL ') + name + (info ? '  · ' + info : '')); if (!ok) fails++; };
const near = (a, b, tol = 1e-6) => Math.abs(a - b) <= tol;
const clone = o => JSON.parse(JSON.stringify(o));
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
const P4 = ['fast', 'typical', 'slow', 'idle'];

// ---- a tiny score builder: beats chain one after the other; elements default to a 1 s voice at the start of their moment ----
const at = (ref, edge, off) => ({ ref, edge, off: off || 0 });
const bt = (key, over) => Object.assign({ key, title: key, desc: '', act: 0, at: null }, over);
const el = (key, beat, over) => Object.assign({ key, type: 'voice', group: 'vo', beat, at: at(beat, 'start'), end: null, dur: { mode: 'fixed', value: 1 }, gate: null, help: null, label: key }, over);
const gate = (expected, fw, blocking) => ({ expected, fw, blocking });
const mini = (beats, elements, extra) => Object.assign({ schema: 3, rev: 1, acts: [{ id: 'act_0', name: 'A', beats: Object.keys(beats) }], beats, groups: [], lanes: {}, elements, markers: {}, notes: {} }, extra);
const SHARE = { share: { name: 'Share or not', gate: 'GS', options: { yes: { label: 'SHARE' }, no: { label: "DON'T SHARE" } }, default: 'yes', onTimeout: 'no' } };
const R = (s, p, branch) => E.resolve(s, { persona: p, branch });

console.log('output shape: a schema-2 score gets the new fields, empty');
{ const s = mini({ b1: bt('1') }, { G: el('G', 'b1', { group: 'int', gate: { expected: 6, fw: 25 } }), V: el('V', 'b1') }); delete s.schema; s.schema = 2;
  const r = R(s, 'idle');
  check('off {}, reactive [], crossBranch [], branch null; react only for waits', same(r.off, {}) && same(r.reactive, []) && same(r.crossBranch, []) && r.branch === null && same(Object.keys(r.react), ['G']));
  check('a wait with no blocking flag blocks (schema 2): idle waits its whole timeout, react = its end', near(r.t.G[1], 25) && near(r.react.G, 25) && near(r.total, 25)); }

console.log('non-blocking wait (design B §3.2.4)');
{ const mk = nb => mini({ b1: bt('1'), b2: bt('2') }, { G: el('G', 'b1', { group: 'int', gate: gate(6, 25, nb ? false : true), dur: { mode: 'elastic', value: 6 } }), V: el('V', 'b1', { dur: { mode: 'fixed', value: 3 } }), N: el('N', 'b2', { dur: { mode: 'fixed', value: 2 } }) });
  const nb = mk(true), bl = mk(false), want = { fast: 1.8, typical: 6, slow: 15.5, idle: 25 };
  check('the stage clock: the moment lasts `expected` for every user, so the next moment starts at 6 whoever is watching',
    P4.every(p => { const r = R(nb, p); return near(r.t.G[1], 6) && near(r.t.b2[0], 6) && near(r.total, 8); }), P4.map(p => R(nb, p).total).join(' / '));
  check('react = when THIS user acts: 1.8 / 6 / 15.5 / 25 s after the wait starts', P4.every(p => near(R(nb, p).react.G, want[p])), P4.map(p => R(nb, p).react.G).join(' / '));
  check('the same wait blocking: the moment waits for the user (fast 1.8 → 3 s moment, idle 25 s) and react = its end',
    P4.every(p => { const r = R(bl, p); return near(r.t.G[1], want[p]) && near(r.react.G, want[p]) && near(r.t.b2[0], Math.max(3, want[p])); }), P4.map(p => R(bl, p).t.b2[0]).join(' / '));
  check('typical is the same blocking or not', same(R(nb, 'typical').t, R(bl, 'typical').t)); }
{ // a wait with an end of its own is not the stage clock nor a reaction: `end` always won
  const s = mini({ b1: bt('1') }, { V: el('V', 'b1', { dur: { mode: 'fixed', value: 8 } }), G: el('G', 'b1', { group: 'int', gate: gate(6, 25, false), end: at('V', 'end') }), K: el('K', 'b1', { at: at('G', 'end') }) });
  const r = R(s, 'idle');
  check('non-blocking with an `end` anchor: it ends there for everybody, react = that end, nothing hangs from the user', near(r.t.G[1], 8) && near(r.react.G, 8) && near(r.t.K[0], 8) && !r.reactive.length); }

console.log('reaction elements follow the user and never lengthen their moment (§3.2.5)');
{ const mk = nb => mini({ b1: bt('1'), b2: bt('2') }, {
    G: el('G', 'b1', { group: 'int', gate: gate(6, 25, nb ? false : true), dur: { mode: 'elastic', value: 6 } }),
    V: el('V', 'b1', { dur: { mode: 'fixed', value: 3 } }),
    GH: el('GH', 'b1', { group: 'ui', end: at('G', 'end') }),                                       // lasts until the user acts
    FXIN: el('FXIN', 'b1', { group: 'fx', at: at('GH', 'start') }), FXOUT: el('FXOUT', 'b1', { group: 'fx', at: at('GH', 'end') }),
    BIO: el('BIO', 'b1', { group: 'obj', at: at('G', 'end'), dur: { mode: 'fixed', value: 4 } }),   // starts when the user acts
    AFTER: el('AFTER', 'b1', { at: at('GH', 'end', 1), dur: { mode: 'fixed', value: 2 } }),          // and what hangs from a reaction is one too
    N: el('N', 'b2', { dur: { mode: 'fixed', value: 2 } }) });
  const nb = mk(true), bl = mk(false), act = { fast: 1.8, typical: 6, slow: 15.5, idle: 25 };
  check('reactive = what hangs from the end of the wait, and what hangs from them (not what hangs from a start that does not follow)',
    same(R(nb, 'idle').reactive.slice().sort(), ['AFTER', 'BIO', 'FXOUT', 'GH']), R(nb, 'idle').reactive.join(', '));
  check('the ghost lasts until THIS user acts (1.8 / 6 / 15.5 / 25) and its sound-out follows', P4.every(p => { const r = R(nb, p); return near(r.t.GH[1], act[p]) && near(r.t.FXOUT[0], act[p]); }));
  check('the placement element starts when the user acts; what hangs from the ghost, a second later', P4.every(p => { const r = R(nb, p); return near(r.t.BIO[0], act[p]) && near(r.t.BIO[1], act[p] + 4) && near(r.t.AFTER[0], act[p] + 1); }));
  check('its start does not follow (the ghost appears at the moment\'s start for everybody)', P4.every(p => near(R(nb, p).t.FXIN[0], 0)));
  check('and none of them lengthens the moment: the next one starts at 6 for every user, whatever the idle user is still doing',
    P4.every(p => near(R(nb, p).t.b1[1], 6) && near(R(nb, p).t.b2[0], 6)) && R(nb, 'idle').t.BIO[1] > R(nb, 'idle').t.b1[1], `idle: moment 0-6, the placement element 25-29`);
  check('contrast, the same wait blocking (schema 2): the idle user holds the moment until its placement element ends (25 + 4)', near(R(bl, 'idle').t.b1[1], 29) && near(R(bl, 'idle').t.b2[0], 29));
  const tn = R(nb, 'typical'), tb = R(bl, 'typical');
  check('typical: every element is where it was; only the moment ends at the stage clock (6 s) and not after its placement element (10 s)',
    ['G', 'V', 'GH', 'FXIN', 'FXOUT', 'BIO', 'AFTER'].every(k => same(tn.t[k], tb.t[k])) && near(tn.t.b1[1], 6) && near(tb.t.b1[1], 10)); }
{ // pinned: only what really follows the user is excluded; something that merely starts with the ghost counts in its moment as anything else
  const s = mini({ b1: bt('1'), b2: bt('2') }, { G: el('G', 'b1', { group: 'int', gate: gate(6, 25, false), dur: { mode: 'elastic', value: 6 } }), GH: el('GH', 'b1', { group: 'ui', end: at('G', 'end') }),
    STAY: el('STAY', 'b1', { at: at('GH', 'start', 1), dur: { mode: 'fixed', value: 9 } }), N: el('N', 'b2') });
  const r = R(s, 'idle');
  check('a voice that starts 1 s after the ghost appears is not a reaction: it keeps the moment to 10 s', !r.reactive.includes('STAY') && near(r.t.b1[1], 10) && near(r.t.b2[0], 10)); }
{ // pinned: a MOMENT anchored to the end of a non-blocking wait follows the user (the author said "start when it ends")
  const s = mini({ b1: bt('1'), b2: bt('2', { at: at('G', 'end') }) }, { G: el('G', 'b1', { group: 'int', gate: gate(6, 25, false), dur: { mode: 'elastic', value: 6 } }), N: el('N', 'b2') });
  check('moment anchored to the end of a non-blocking wait: starts when this user acts (6 for typical, 25 for idle); its elements stay its own',
    near(R(s, 'typical').t.b2[0], 6) && near(R(s, 'idle').t.b2[0], 25) && near(R(s, 'idle').t.b2[1], 26) && !R(s, 'idle').reactive.length); }

console.log('help lines against the user\'s reaction (§3.2.6)');
{ const mk = nb => mini({ b1: bt('1') }, { G: el('G', 'b1', { group: 'int', gate: gate(6, 25, nb ? false : true), dur: { mode: 'elastic', value: 6 } }),
    H12: el('H12', 'b1', { at: at('G', 'start', 12), help: 'G', dur: { mode: 'fixed', value: 2 } }), H19: el('H19', 'b1', { at: at('G', 'start', 19), help: 'G', dur: { mode: 'fixed', value: 2 } }) });
  const nb = mk(true), bl = mk(false), pl = (s, p) => ['H12', 'H19'].filter(h => R(s, p).helpActive[h]).join('+') || 'none';
  check('help plays when it starts before the user acts: 12 s → slow (acts at 15.5) and idle; 19 s → idle only; fast and typical never',
    [pl(nb, 'fast'), pl(nb, 'typical'), pl(nb, 'slow'), pl(nb, 'idle')].join(' | ') === 'none | none | H12 | H12+H19', [pl(nb, 'fast'), pl(nb, 'typical'), pl(nb, 'slow'), pl(nb, 'idle')].join(' | '));
  check('the same lines play when the wait blocks (the help does not depend on the flag)', P4.every(p => pl(nb, p) === pl(bl, p))); }
{ // a help line whose `help` is not a wait: against that element's end, as always
  const s = mini({ b1: bt('1') }, { V: el('V', 'b1', { dur: { mode: 'fixed', value: 5 } }), H: el('H', 'b1', { at: at('b1', 'start', 3), help: 'V' }), H2: el('H2', 'b1', { at: at('b1', 'start', 6), help: 'V' }) });
  check('help on a non-wait: active only while that element has not ended', R(s, 'typical').helpActive.H === true && R(s, 'typical').helpActive.H2 === false); }

console.log('branches (design B §3.2.1) · one moment, a voice for each option');
const brScore = extra => mini({ b0: bt('0'), b1: bt('1'), b2: bt('2') }, Object.assign({
  GS: el('GS', 'b0', { group: 'int', gate: gate(6, 30, true), dur: { mode: 'elastic', value: 6 } }),
  C: el('C', 'b1', { dur: { mode: 'fixed', value: 2 } }),
  Y: el('Y', 'b1', { dur: { mode: 'fixed', value: 10 }, branch: { on: 'share', value: 'yes' } }), N: el('N', 'b1', { dur: { mode: 'fixed', value: 5 }, branch: { on: 'share', value: 'no' } }),
  HN: el('HN', 'b1', { at: at('GS', 'start', 1), help: 'GS', branch: { on: 'share', value: 'no' } }),
  T: el('T', 'b2', { dur: { mode: 'fixed', value: 1 } }) }, extra), { branches: clone(SHARE) });
{ const s = brScore(), len = (r) => r.t.b1[1] - r.t.b1[0];
  check('SHARE: the moment lasts its longest voice (10 s); DON\'T SHARE: 5 s; all branches at once: 10 s', near(len(R(s, 'typical', { share: 'yes' })), 10) && near(len(R(s, 'typical', { share: 'no' })), 5) && near(len(R(s, 'typical', 'all')), 10));
  check('the total follows the branch (5 s shorter in DON\'T SHARE)', near(R(s, 'typical', { share: 'yes' }).total - R(s, 'typical', { share: 'no' }).total, 5));
  check('`off` names the other option\'s elements; `branch` says what was resolved', same(Object.keys(R(s, 'typical', { share: 'yes' }).off).sort(), ['HN', 'N']) && same(Object.keys(R(s, 'typical', { share: 'no' }).off), ['Y'])
    && same(R(s, 'typical', { share: 'no' }).branch, { share: 'no' }) && R(s, 'typical', 'all').branch === null && !Object.keys(R(s, 'typical', 'all').off).length);
  check('an element of the other option is still timed (phantom): its time never jumps from one view to the other', same(R(s, 'typical', { share: 'yes' }).t.N, R(s, 'typical', { share: 'no' }).t.N) && near(R(s, 'typical', { share: 'yes' }).t.N[1] - R(s, 'typical', { share: 'yes' }).t.N[0], 5));
  check('a help line of the other option plays nowhere (no entry) and counts where it is there', !('HN' in R(s, 'idle', { share: 'yes' }).helpActive) && R(s, 'idle', { share: 'no' }).helpActive.HN === true);
  check('`branch` left out: each branch at its default (SHARE); an unknown value falls back to it; a score with no `branches` is not filtered',
    same(R(s, 'idle').t, R(s, 'idle', { share: 'yes' }).t) && same(R(s, 'typical', { share: 'maybe' }).branch, { share: 'yes' }) && R(mini({ b1: bt('1') }, { A: el('A', 'b1') }), 'typical', { share: 'no' }).branch === null);
  const cyc = brScore({ Y2: el('Y2', 'b1', { at: at('Y', 'start') }) }); delete cyc.branches;
  check('no `branches` entry, no filtering: every element counts (even one that carries `branch`)', near(R(cyc, 'typical').t.b1[1] - R(cyc, 'typical').t.b1[0], 10) && !Object.keys(R(cyc, 'typical').off).length); }

console.log('alternative anchors (§3.2.2) and anchors that cross to the other option (§3.2.3)');
{ const s = brScore({
    X: el('X', 'b2', { at: at('Y', 'end'), alt: { 'share=no': { at: at('N', 'end') } }, end: at('C', 'end', 20) }),   // an alt for `at` only: `end` stays the primary one
    X3: el('X3', 'b2', { end: at('Y', 'end') }),                                                                      // an `end` can cross too
    X2: el('X2', 'b2', { at: at('Y', 'end') }),                                                                       // no alt: crosses in DON'T SHARE
    NX: el('NX', 'b2', { at: at('Y', 'end'), branch: { on: 'share', value: 'no' } }) });                              // an element of DON'T SHARE hanging from a SHARE one
  const yes = R(s, 'typical', { share: 'yes' }), no = R(s, 'typical', { share: 'no' }), all = R(s, 'typical', 'all');
  const b1s = yes.t.b1[0];
  check('the alt anchor applies only in its option: X starts at the end of Y (SHARE) and at the end of N (DON\'T SHARE)', near(yes.t.X[0], b1s + 10) && near(no.t.X[0], b1s + 5), `${yes.t.X[0] - b1s} / ${no.t.X[0] - b1s}`);
  check('all branches at once uses the primary anchor; the alt never leaks', near(all.t.X[0], b1s + 10));
  check('a field the alt does not name stays the primary one (`end` is still 20 s after C ends, in both views)', near(no.t.X[1], b1s + 2 + 20) && near(yes.t.X[1], b1s + 2 + 20));
  check('with an alt for the other option, X is not reported; in neither view', !yes.crossBranch.includes('X') && !no.crossBranch.includes('X') && !all.crossBranch.includes('X'));
  check('no alt: in DON\'T SHARE the anchor into SHARE\'s Y is reported, with Y\'s phantom time (nothing jumps)', no.crossBranch.includes('X2') && near(no.t.X2[0], yes.t.X2[0]) && !yes.crossBranch.includes('X2'));
  check('an element of the other option is never reported: NX only matters when its own option is on', !yes.crossBranch.includes('NX') && no.crossBranch.includes('NX'));
  check('an `end` anchor that crosses is reported too (X3 lasts until Y ends: only a problem when Y is not there)', no.crossBranch.includes('X3') && !yes.crossBranch.includes('X3'));
  check('all branches at once never reports (no element is "the other option")', !all.crossBranch.length);
  const m = brScore({}); m.beats.b2.at = at('Y', 'end'); m.beats.b2.alt = { 'share=no': { at: at('N', 'end') } };
  check('a moment takes an alt anchor too (it starts after Y, or after N in DON\'T SHARE)', near(R(m, 'typical', { share: 'yes' }).t.b2[0], R(m, 'typical', { share: 'yes' }).t.b1[0] + 10) && near(R(m, 'typical', { share: 'no' }).t.b2[0], R(m, 'typical', { share: 'no' }).t.b1[0] + 5)
    && !R(m, 'typical', { share: 'no' }).crossBranch.includes('b2'));
  const m2 = brScore({}); m2.beats.b2.at = at('Y', 'end');
  check('and a moment anchored across without an alt is reported by its id', R(m2, 'typical', { share: 'no' }).crossBranch.includes('b2') && !R(m2, 'typical', { share: 'yes' }).crossBranch.length); }

console.log('what integrity asks of the engine (lote 5 step 6): crossInfo says which anchor crosses, altRuns gives the other options');
{ const s = brScore({
    X: el('X', 'b2', { at: at('Y', 'end'), alt: { 'share=no': { at: at('N', 'end') } } }),
    X3: el('X3', 'b2', { end: at('Y', 'end') }), X2: el('X2', 'b2', { at: at('Y', 'end') }),
    NX: el('NX', 'b2', { at: at('Y', 'end'), branch: { on: 'share', value: 'no' } }) });
  const no = R(s, 'typical', { share: 'no' }), yes = R(s, 'typical', { share: 'yes' });
  const info = no.crossInfo.map(c => c.id + ':' + c.field + ':' + c.ref).sort().join(' ');
  check('crossInfo: who, which anchor (at / end) and what it points to; crossBranch is the same ids, once each', info === 'NX:at:Y X2:at:Y X3:end:Y' && same(no.crossBranch.slice().sort(), ['NX', 'X2', 'X3']), info);
  check('  nothing crosses in SHARE, nor with every branch at once, nor in a schema 2 score', !yes.crossInfo.length && !R(s, 'typical', 'all').crossInfo.length && same(R(Object.assign(clone(s), { schema: 2, branches: undefined }), 'typical').crossInfo, []));
  const ar = E.altRuns(s);
  check('altRuns: one run for the option that is not the default (share=no), the same schedule as asking for it', ar.length === 1 && ar[0].k === 'share=no' && same(ar[0].sel, { share: 'no' }) && same(ar[0].sched.t, no.t) && ar[0].sched.branch.share === 'no');
  check('  for another user, that user in DON\'T SHARE; a score with no branches has none', near(E.altRuns(s, 'idle')[0].sched.total, R(s, 'idle', { share: 'no' }).total) && E.altRuns(Object.assign(clone(s), { branches: undefined })).length === 0);
  const two = clone(s); two.branches.pick = { name: 'Pick', options: { a: { label: 'A' }, b: { label: 'B' }, c: { label: 'C' } }, default: 'a' };
  check('  two decisions, four options that are not a default: each alone, the other on its default', E.altRuns(two).map(r => r.k).join() === 'share=no,pick=b,pick=c' && E.altRuns(two).every(r => Object.keys(r.sched.branch).length === 2 && Object.entries(r.sel).every(([on, v]) => r.sched.branch[on] === v)), E.altRuns(two).map(r => r.k).join()); }

console.log('\'auto\': what a user who hits the timeout does (Unreal\'s ShareFW = DON\'T SHARE)');
{ const s = brScore(), br = (p, b) => R(s, p, b).branch.share;
  check('auto: Idle waits its whole timeout (30 s) → onTimeout (DON\'T SHARE); fast, typical and slow decide → default (SHARE)', [br('fast', { share: 'auto' }), br('typical', { share: 'auto' }), br('slow', { share: 'auto' }), br('idle', { share: 'auto' })].join() === 'yes,yes,yes,no');
  check('a key that is missing from the object is auto too', br('idle', {}) === 'no' && br('slow', {}) === 'yes');
  check('explicit choices win over auto, for every user', P4.every(p => br(p, { share: 'yes' }) === 'yes' && br(p, { share: 'no' }) === 'no'));
  check('left out (the default view) is the default for everybody, Idle too: the typical numbers never depend on the user', br('idle', undefined) === 'yes');
  const idleNo = R(s, 'idle', { share: 'auto' }), idleYes = R(s, 'idle', { share: 'yes' });
  check('and the voices follow: the idle user hears DON\'T SHARE\'s 5 s, not SHARE\'s 10 s', near(idleNo.t.b1[1] - idleNo.t.b1[0], 5) && near(idleYes.t.b1[1] - idleYes.t.b1[0], 10));
  const noTimeout = brScore(); delete noTimeout.branches.share.onTimeout;
  check('a branch with no onTimeout: auto = its default', R(noTimeout, 'idle', { share: 'auto' }).branch.share === 'yes'); }

console.log('the real piece (frozen F0) with its four stage-clock waits (design B §1.2)');
{ const f0 = readFixture(), ex = readExpect(), E0 = f0.elements, id = k => Object.keys(E0).find(x => E0[x].key === k);
  const c = clone(f0), NB = ['G_BREATH', 'G_HEART', 'G_GRAB', 'G_DRAW'];
  for (const x in c.elements) if (NB.includes(c.elements[x].key)) c.elements[x].gate.blocking = false;
  const moved = (p) => { const a = R(f0, p), b = R(c, p); return Object.keys(E0).filter(x => Math.abs(a.t[x][0] - b.t[x][0]) > 1e-3).length + Object.keys(f0.beats).filter(x => Math.abs(a.t[x][0] - b.t[x][0]) > 1e-3).length; };
  const sameT = (a, b) => same(a.t, b.t);
  check('typical: nothing moves, not one of the 665 starts and ends (total ' + ex.totals.typical + ')', sameT(R(f0, 'typical'), R(c, 'typical')) && near(R(c, 'typical').total, ex.totals.typical, 1e-3));
  check('fast: no start moves and the total stays ' + ex.totals.fast, moved('fast') === 0 && near(R(c, 'fast').total, ex.totals.fast, 1e-3));
  check('slow: 17:56.6 (1076.61) instead of ' + ex.totals.slow + ' · 466 starts move (as measured in the design)', near(R(c, 'slow').total, 1076.61, 0.01) && moved('slow') === 466, `${R(c, 'slow').total.toFixed(2)} · ${moved('slow')} start(s)`);
  check('idle: 19:08.6 (1148.61) instead of ' + ex.totals.idle + ' · 466 starts move', near(R(c, 'idle').total, 1148.61, 0.01) && moved('idle') === 466, `${R(c, 'idle').total.toFixed(2)} · ${moved('idle')} start(s)`);
  const uidOf = x => E0[x].legacy.uid, helps = r => Object.keys(r.helpActive).filter(h => r.helpActive[h]).map(uidOf).sort();
  check('the help lines that play are the same for the four users', P4.every(p => same(helps(R(c, p)), helps(R(f0, p)))), P4.map(p => helps(R(c, p)).length).join('/'));
  check('the anchor loops stay where they were (2.R4, 5.R4) for every user', P4.every(p => same(R(c, p).cycles.slice().sort(), R(f0, p).cycles.slice().sort()) && R(c, p).cycles.length === 2));
  const keys = R(c, 'idle').reactive.map(x => E0[x].key).sort().join(' ');
  check('12 reaction elements: BIO_ON ×2, the four ghosts, their FX_GHOSTOUT, HAP_PULSE_SOFT and HAP_BREATH_HUM (design: 16, with the four FX_GHOSTAPPEAR, which hang from the START of a ghost)',
    keys === 'BIO_ON BIO_ON FX_GHOSTOUT FX_GHOSTOUT FX_GHOSTOUT FX_GHOSTOUT GHOST_ATTRACT GHOST_BREATH GHOST_DRAW GHOST_HEART HAP_BREATH_HUM HAP_PULSE_SOFT', keys);
  const ghost = id('GHOST_BREATH'), g = id('G_BREATH'), r = R(c, 'idle');
  check('the idle user\'s ghost stays 25 s (until it acts) and the stage does not wait for it', near(r.t[ghost][1] - r.t[g][0], 25) && near(r.t[g][1] - r.t[g][0], 6), `ghost ${(r.t[ghost][1] - r.t[ghost][0]).toFixed(1)} s · wait ${(r.t[g][1] - r.t[g][0]).toFixed(1)} s`);
  check('react for the four waits is start + each user\'s time; for the blocking ones it is their end', P4.every(p => { const q = R(c, p); return NB.every(k => near(q.react[id(k)], q.t[id(k)][0] + E.PERSONAS[p].wait(E0[id(k)].gate))) && near(q.react[id('G_BELL')], q.t[id('G_BELL')][1]); }));
  check('the blocking waits still block: the idle user\'s 6 other waits last their whole timeout', ['G_BELL', 'G_SENSOR', 'G_CHOOSE', 'G_SAVE4', 'G_SAVE5', 'G_SHARE'].every(k => near(R(c, 'idle').t[id(k)][1] - R(c, 'idle').t[id(k)][0], E0[id(k)].gate.fw)));
  // flags that say what the schema-2 engine already does change nothing: blocking true everywhere, and a branch nobody belongs to
  const d = clone(f0); for (const x in d.elements) if (d.elements[x].gate) d.elements[x].gate.blocking = true;
  d.branches = clone(SHARE); d.branches.share.gate = id('G_SHARE');
  check('`blocking: true` on every wait and an unused branch: the four users unchanged (times and help)', P4.every(p => same(R(d, p).t, R(f0, p).t) && same(R(d, p).helpActive, R(f0, p).helpActive) && R(d, p).total === R(f0, p).total));
  check('and `inBeatEnd` still answers for a score as it is (two arguments, primary anchors)', typeof E.inBeatEnd === 'function' && E.inBeatEnd(f0, id('G_BREATH')) === true && E.inBeatEnd(f0, id('FX_GHOSTOUT')) === false); }

console.log(fails ? `\n${fails} FAILED` : '\nall ok');
process.exit(fails ? 1 : 0);
