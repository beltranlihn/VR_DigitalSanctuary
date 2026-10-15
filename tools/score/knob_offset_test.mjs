// knob_offset_test.mjs — "Match Unreal" for a time that IS an Unreal knob (lote 5 design B §6.3 and §11 step 8): the contract entry
// help.after (VO_11h plays BP_BreathStage_SC.HelpAfter seconds after VO_11b ends), the rule C3.KNOB.OFFSET, and Edits.matchKnobAnchor
// (the operation the Problems action runs behind its card), on a schema 2 score and on a schema 3 one. Pure Node, no window.
// It runs on the frozen fixture tools/score/fixtures/f0-score.json (so real edits of the piece never break it); --live runs it on
// obra/score/score.json (see tools/score/test_score.mjs). Nothing here writes anything. Exit 1 if any case fails.
//   node tools/score/knob_offset_test.mjs [--live]
import fs from 'fs';
import path from 'path';
import { createRequire } from 'module';
import { fileURLToPath } from 'url';
import { testScore, schema3Copy } from './test_score.mjs';
const require = createRequire(import.meta.url);
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const js = f => require(path.join(ROOT, 'web/editor-obra/app/js', f));
const E = js('engine.js'), X = js('edits.js'), P = js('partitura.js'), I = js('integrity.js'), Pol = js('policy.js'), Ck = js('check.js');
const rd = p => JSON.parse(fs.readFileSync(path.join(ROOT, p), 'utf8'));
const { score, name: SRC } = testScore(); console.log('on the ' + SRC);
const before = JSON.stringify(score);
const contract = rd('obra/unreal/contract.json'), bind = rd('obra/unreal/partitura_binding.json'), perillas = rd('obra/unreal/perillas.json'), pdef = rd('obra/unreal/partitura_def.json');
const clone = o => JSON.parse(JSON.stringify(o));
let fails = 0;
const check = (n, ok, info) => { console.log((ok ? '  ok   ' : '  FAIL ') + n + (info ? '  · ' + info : '')); if (!ok) fails++; };
const T = (s, p) => E.resolve(s, { persona: p || 'typical' });
const probs = (s, ctx) => I.staticProblems(s, T(s), contract, E.altRuns(s), ctx || {});
const knobRows = (s, ctx) => probs(s, ctx).filter(p => p.rule === 'C3.KNOB.OFFSET');
const HELP = 'BP_BreathStage_SC.HelpAfter';

console.log('the contract entry help.after');
const idOf = (s, k) => Object.keys(s.elements).find(id => s.elements[id].key === k);
const vo11h = idOf(score, 'VO_11h'), vo11b = idOf(score, 'VO_11b'), breath = idOf(score, 'G_BREATH');
{
  const c = contract.entries.find(e => e.id === 'help.after');
  check('it is in obra/unreal/contract.json: VO_11h, kind knob, anchor VO_11b end, BP_BreathStage_SC.HelpAfter = 4 (perillas.json), bound by id', !!c && c.kind === 'knob' && c.anchor.ref === 'VO_11b' && c.anchor.edge === 'end' && c.knob.name === HELP && c.knob.value === 4
    && c.knob.source === 'perillas.json' && JSON.stringify(c.ids) === JSON.stringify([vo11h]) && c.idKeys[vo11h] === 'VO_11h' && c.on.move === 'warn' && c.on.trim === 'info', c && JSON.stringify(c.ids));
  check('  it says it is pending the Director (that HelpAfter counts from the END of VO_11b)', /Director ack/.test(c.pending) && /END of VO_11b/.test(c.pending), c.pending);
  const row = ((perillas.bps.BP_BreathStage_SC || []).find(r => r[0] === 'HelpAfter') || [])[2];
  check('the value in the contract is the one in the Blueprint dump (perillas.json, the CDO of BP_BreathStage_SC)', row === '{"HelpAfter":4}', row);
  const names = Ck.knobNames(pdef, perillas);
  check('Check.knobNames knows the knob as "BP_BreathStage_SC.HelpAfter" (so the file check does not warn W.CONTRACT about it)', names.has(HELP) && names.has('HelpAfter') && names.has('FW_Bell'));
  const r = Ck.invariants(score, score, { Engine: E, Edits: X, contract, knobs: names });
  check('  Check.invariants with the real contract and Unreal\'s names: ok, and no W.CONTRACT warning', r.ok && !r.warnings.some(w => w.code === 'W.CONTRACT'), r.warnings.map(w => w.msg).join(' | '));
  check('  VO_11h is in the contract twice: vo.wired (its voice) and help.after (its time)', I.contractFor(vo11h, score.elements[vo11h], contract).map(x => x.id).join() === 'vo.wired,help.after');
}

const upgraded = X.migrate3(score, E, contract, { at: '2026-10-07T12:00:00.000Z', who: 'B' }).next;   // the owner's button, in memory: G_BREATH runs on the stage clock
for (const [label, S0] of [['schema 2', score], ['schema 3 (baseline instead of golden)', schema3Copy(score)], ['schema 3 as upgraded (Edits.migrate3)', upgraded]]) {
  console.log(label + ': the rule C3.KNOB.OFFSET');
  const snap0 = JSON.stringify(S0);
  const v11h = idOf(S0, 'VO_11h'), v11b = idOf(S0, 'VO_11b'), g = idOf(S0, 'G_BREATH');
  const T0 = T(S0), K0 = knobRows(S0);
  check('at load: one warning, on VO_11h, with the numbers (it hangs from G_BREATH start + 12 s, at 3:50.1 instead of 3:57.1)', K0.length === 1 && K0[0].el === v11h && K0[0].sv === 'warn' && K0[0].ly === 'C3' && K0[0].st === 'open'
    && K0[0].msg === 'VO_11h plays 4 s after VO_11b ends in Unreal (HelpAfter in BP_BreathStage_SC); here it hangs from G_BREATH start + 12 s, at 3:50.1 instead of 3:57.1.', K0[0] && K0[0].msg);
  check('  its fingerprint is rule | element | what hangs where now and the knob: it is the value an acceptance would be for', K0[0].fp === `C3.KNOB.OFFSET|${v11h}|${g}.start+12|4` && K0[0].fpBase === `C3.KNOB.OFFSET|${v11h}` && K0[0].param === `${g}.start+12|4`, K0[0].fp);
  const live = knobRows(S0, { knob: n => n === HELP ? 6 : undefined });
  check('  the live knob wins over the contract\'s value (HelpAfter = 6 → "6 s after VO_11b ends … instead of 3:59.1")', live.length === 1 && /^VO_11h plays 6 s after VO_11b ends/.test(live[0].msg) && /instead of 3:59\.1\.$/.test(live[0].msg) && live[0].param.endsWith('|6'), live[0] && live[0].msg);
  check('  a knob Unreal does not know (live = undefined) falls back to the contract\'s 4 s', knobRows(S0, { knob: () => undefined })[0].param.endsWith('|4'));

  console.log(label + ': Match Unreal (Edits.matchKnobAnchor)');
  const spec = { ref: v11b, edge: 'end', off: 4, knob: HELP, at: '2026-10-07T12:00:00.000Z', by: 'B' };
  const m = X.matchKnobAnchor(S0, v11h, spec, E);
  check('it can be done', m.ok, m.why);
  const N = m.next, Tn = T(N);
  check('only VO_11h moves: typical 3:50.1 → 3:57.1 (237.1 s), in the moment of VO_11b, hanging from VO_11b end + 4 s with the knob\'s name; nothing else moves for the typical user',
    m.moved.length === 0 && Math.abs(Tn.t[v11h][0] - 237.1333) < 1e-3 && I.clock(m.t0) === '3:50.1' && I.clock(m.t1) === '3:57.1' && N.elements[v11h].beat === S0.elements[v11b].beat
    && JSON.stringify(N.elements[v11h].at) === JSON.stringify({ ref: v11b, edge: 'end', off: 4, knob: HELP }) && Object.keys(S0.elements).every(id => id === v11h || (T0.t[id][0] === Tn.t[id][0] && T0.t[id][1] === Tn.t[id][1])) && Object.keys(S0.beats).every(b => T0.t[b][0] === Tn.t[b][0] && T0.t[b][1] === Tn.t[b][1]), `${m.t0} → ${m.t1}`);
  check('  it is still the help of G_BREATH, in its lane, with its length, text and sound; the rest of the element is as it was', N.elements[v11h].help === g && N.elements[v11h].lane === S0.elements[v11h].lane && N.elements[v11h].dur.value === S0.elements[v11h].dur.value && N.elements[v11h].text === S0.elements[v11h].text
    && JSON.stringify(Object.assign({}, N.elements[v11h], { at: 0, beat: 0 })) === JSON.stringify(Object.assign({}, S0.elements[v11h], { at: 0, beat: 0 })));
  const U = m.users, tot = ['fast', 'typical', 'slow', 'idle'].every(p => Math.abs(U[p].total0 - U[p].total1) < 1e-6);
  check('the totals do not change for any of the four simulated users', tot, ['fast', 'typical', 'slow', 'idle'].map(p => p + ' ' + U[p].total0.toFixed(1) + '/' + U[p].total1.toFixed(1)).join(' '));
  check('  the fast and the typical user do not hear it before or after; the slow user heard it and no longer does (they act at 15.5 s)', U.fast.help0 === false && U.fast.help1 === false && U.typical.help0 === false && U.typical.help1 === false && U.slow.help0 === true && U.slow.help1 === false && Math.abs(U.slow.acts - 15.5) < 1e-6 && U.slow.comes > U.slow.acts, JSON.stringify(U.slow));
  check('  the idle user, who only acts at the 25 s timeout, hears it before and after (it comes at 19.0 s: Unreal plays it, and the card must not say the opposite)', U.idle.help0 === true && U.idle.help1 === true && Math.abs(U.idle.acts - 25) < 1e-6 && Math.abs(U.idle.comes - 19) < 1e-3 && Math.abs(U.slow.comes - 19) < 1e-3 && Math.abs(U.slow.comes0 - 12) < 1e-6, JSON.stringify(U.idle));
  if (label.startsWith('schema 3 as upgraded')) {
    // here the engine itself runs G_BREATH on the stage clock, so it must say what the card says (design B section 1.4): VO_11h 230.1 → 237.1 (fast, typical), 241.7 → 248.7 (slow), 266.7 → 273.7 (idle); the slow user stops hearing it
    const want = { fast: [230.1, 237.1], typical: [230.1, 237.1], slow: [241.7, 248.7], idle: [266.7, 273.7] };
    const eng = p => ({ a: E.resolve(S0, { persona: p }), b: E.resolve(N, { persona: p }) });
    check('  the engine agrees with the card for the four users: the times of the design table, and whether the line plays (slow: yes → no; idle: yes → yes)', Object.keys(want).every(p => { const { a, b } = eng(p); return Math.abs(a.t[v11h][0] - want[p][0]) < .06 && Math.abs(b.t[v11h][0] - want[p][1]) < .06 && !!a.helpActive[v11h] === U[p].help0 && !!b.helpActive[v11h] === U[p].help1; }), Object.keys(want).map(p => { const { a, b } = eng(p); return p + ' ' + a.t[v11h][0].toFixed(1) + '→' + b.t[v11h][0].toFixed(1) + ' ' + a.helpActive[v11h] + '→' + b.helpActive[v11h]; }).join(' · '));
  }
  // the APK reference moves for VO_11h alone
  const gov = P.governedBy(S0, T0, bind), D0 = I.divergent(S0, T0, contract, gov), D1 = I.divergent(N, Tn, contract, P.governedBy(N, Tn, bind));
  check('≠ APK does not flag it: the baseline moved for VO_11h, the set is the same as before (empty at load)', D0.size === 0 && D1.size === 0 && !D1.has(v11h), `${D0.size} → ${D1.size}`);
  const ref0 = I.baselineOf(S0), ref1 = I.baselineOf(N), rel = (S, b, id) => I.relOf(S, b, id);
  const others = Object.keys(S0.elements).filter(id => id !== v11h);
  check('  and ONLY VO_11h: every other time of the baseline is the one it had', others.every(id => JSON.stringify(rel(S0, ref0, id)) === JSON.stringify(rel(N, ref1, id))) && JSON.stringify(rel(S0, ref0, v11h)) !== JSON.stringify(rel(N, ref1, v11h)), '');
  if (S0.schema === 3) {
    const last = N.baseline.log[N.baseline.log.length - 1];
    check('  schema 3: the baseline log says what was matched, by whom and when; its relative time for VO_11h is where it plays in the moment of VO_11b', last.op === 'match-unreal' && last.knob === HELP && last.by === 'B' && last.at === spec.at && JSON.stringify(last.ids) === JSON.stringify([v11h])
      && Math.abs(N.baseline.rel[v11h][0] - (Tn.t[v11h][0] - Tn.t[N.elements[v11h].beat][0])) < 1e-3, JSON.stringify(last) + ' ' + JSON.stringify(N.baseline.rel[v11h]));
  } else check('  schema 2: the golden moved for VO_11h only (absolute times), with no record added to its voice list', Math.abs(N.golden.times[v11h][0] - 237.1333) < 2e-3 && (N.golden.voices || []).length === (S0.golden.voices || []).length
    && Object.keys(S0.golden.times).filter(k => k !== v11h).every(k => JSON.stringify(S0.golden.times[k]) === JSON.stringify(N.golden.times[k])), JSON.stringify(N.golden.times[v11h]));
  check('the warning is gone, and the score passes the same invariants the server applies on save', knobRows(N).length === 0 && Ck.invariants(N, S0, { Engine: E, Edits: X, contract, knobs: Ck.knobNames(pdef, perillas) }).ok, Ck.invariants(N, S0, { Engine: E, Edits: X, contract }).errors.map(e => e.msg).join(' | '));
  check('  it validates (the knob\'s name is plain text in the anchor) and the schema stays what it was', (() => { try { X.validate(N, E); return true; } catch (e) { return false; } })() && N.schema === S0.schema);
  check('Undo is the snapshot: the score it got is exactly as it was (the operation is pure)', JSON.stringify(S0) === snap0);

  console.log(label + ': after it, and the edge cases');
  const moved = X.move(N, v11h, 1, {}, E.dependents(N)), kr = knobRows(moved);
  check('moving VO_11h by hand afterwards (+1 s) brings the warning back, now about an offset of 5 s against the knob\'s 4 s', kr.length === 1 && kr[0].param === `${v11b}.end+5|4` && moved.elements[v11h].at.knob === HELP, kr[0] && kr[0].param);
  const mv = I.opItems({ type: 'move', ids: [v11h], prevScore: N }, moved, { problems: probs(N) }, { problems: probs(moved) }, contract, E, { gov: {} });
  const hi = mv.items.find(i => i.rule === 'C3.HELP.AFTER');
  check('  and the edit itself asks first (a card: the entry says move = warn), with the value it would be accepted at', !!hi && hi.sv === 'warn' && hi.title === 'Knob in Unreal' && /HelpAfter seconds/.test(hi.body) && /^\d+\.\d\d\|\d+\.\d\d\|1\.R5a$/.test(hi.values[v11h]), hi && JSON.stringify(hi.values));
  const again = X.matchKnobAnchor(moved, v11h, spec, E);
  check('  Match Unreal again puts it back (4 s), and doing it on what already matches changes nothing at all', again.ok && Math.abs(T(again.next).t[v11h][0] - Tn.t[v11h][0]) < 1e-9 && JSON.stringify(X.matchKnobAnchor(N, v11h, spec, E).next.elements[v11h]) === JSON.stringify(N.elements[v11h]));
  const ren = clone(S0); X.renameEl(ren.elements[v11b], 'VO_11bx');
  check('renaming VO_11b does not break it: the entry counts from the name Unreal knows (VO_11b), found by the ids of the contract', knobRows(ren).length === 1 && knobRows(ren)[0].param.startsWith(`${v11h ? idOf(ren, 'G_BREATH') : ''}.start+12`) && /after VO_11bx ends/.test(knobRows(ren)[0].msg), knobRows(ren)[0] && knobRows(ren)[0].msg);
  const loop = clone(S0); loop.elements[v11b].at = { ref: v11h, edge: 'end', off: 0 };
  const rl = X.matchKnobAnchor(loop, v11h, spec, E);
  check('a loop (VO_11b hangs from VO_11h) is refused with a reason, nothing is returned to apply', !rl.ok && rl.loop === true && /would make a loop/.test(rl.why) && !rl.next, rl.why);
  check('  so are: itself, an element that is not there, a knob without a value, an element that is not there to move', !X.matchKnobAnchor(S0, v11h, Object.assign({}, spec, { ref: v11h }), E).ok && !X.matchKnobAnchor(S0, v11h, Object.assign({}, spec, { ref: 'el_nope' }), E).ok && !X.matchKnobAnchor(S0, v11h, Object.assign({}, spec, { off: null }), E).ok && !X.matchKnobAnchor(S0, 'el_nope', spec, E).ok);
  const dh = clone(S0); delete dh.elements[v11b];
  check('  with VO_11b deleted there is nothing to count from: no warning, no crash (the contract orphan says Unreal still has it)', knobRows(dh).length === 0 && probs(dh).some(p => p.rule === 'C3.CONTRACT.ORPHAN' && /VO_11b/.test(p.msg)));
  // the policy: the operation is a quiet 'sync' (the card in front of it is the decision), and accepting the warning means THIS offset
  check('the edit it is committed as is quiet: no second card', Pol.decide({ type: 'sync', ids: [] }, mv.items, {}).mode === 'quiet');
  const acc = Pol.acceptRecords([], [{ sv: 'warn', ly: 'C3', rule: 'C3.KNOB.OFFSET', title: 'Time of a knob', body: kr[0].msg, ev: 'BP_BreathStage_SC', el: v11h, ids: [v11h], keys: ['VO_11h'], fp: kr[0].fp }], { who: 'B', reason: 'we want it later', at: '2026-10-07T12:00:00.000Z' });
  const acceptedRow = knobRows(Object.assign(clone(moved), { accepted: acc }))[0], reopened = knobRows(Object.assign(clone(X.move(moved, v11h, 1, {}, E.dependents(moved))), { accepted: acc }))[0];
  check('accepting that warning accepts that offset only: at +1 s more it is open again and says what it was accepted at', acceptedRow.st === 'accepted' && reopened.st === 'open' && reopened.was.value === kr[0].param
    && I.reopenedText(reopened) === 'Reopened: accepted at an offset of 5 s (Unreal: 4 s) by B ("we want it later"), now an offset of 6 s (Unreal: 4 s).', reopened && I.reopenedText(reopened));
  check('none of the above changed the score it started from (' + label + ')', JSON.stringify(S0) === snap0);
}

console.log('shiftGolden: only the elements asked for');
{
  const g = score.golden || schema3Copy(score).baseline, T0 = T(score), T1 = T(score);
  if (score.golden) {
    const t1 = { t: Object.assign({}, T1.t, { [vo11h]: [T1.t[vo11h][0] + 5, T1.t[vo11h][1] + 5], [vo11b]: [T1.t[vo11b][0] + 5, T1.t[vo11b][1] + 5] }), total: T1.total };
    const all = X.shiftGolden(score.golden, T0, t1, null), one = X.shiftGolden(score.golden, T0, t1, null, [vo11h]);
    check('the golden shifts everything that changed, or only the ids given (the old callers are unchanged)', Math.abs(all.times[vo11b][0] - score.golden.times[vo11b][0] - 5) < 1e-3 && Math.abs(one.times[vo11b][0] - score.golden.times[vo11b][0]) < 1e-9 && Math.abs(one.times[vo11h][0] - score.golden.times[vo11h][0] - 5) < 1e-3);
  } else check('(no golden in this score)', true);
}

check('the score of the test was never changed', JSON.stringify(score) === before);
console.log(fails ? `\n${fails} FAILED` : '\nall ok');
process.exit(fails ? 1 : 0);
