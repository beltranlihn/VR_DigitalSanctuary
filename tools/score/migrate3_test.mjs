// migrate3_test.mjs — the upgrade to schema 3 (Edits.migrate3, lote 5 design B §10 and §11 step 5): what it does to the score, what it
// promises (nothing moves for the typical user), what it refuses, and the stable names it seeds (js/importdiff.js).
// It runs on the frozen fixture tools/score/fixtures/f0-score.json (so real edits of the piece never break it); --live runs it on
// obra/score/score.json (see tools/score/test_score.mjs). If that one is already schema 3 there is nothing to upgrade: only the
// refusal is checked. Everything it writes goes to a temp folder that it removes; the score is never written.
// Exit 1 if any case fails.
//   node tools/score/migrate3_test.mjs [--live]
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { testScore, readExpect, ROOT } from './test_score.mjs';
const require = createRequire(import.meta.url);
const js = f => require(path.join(ROOT, 'web/editor-obra/app/js', f));
const E = js('engine.js'), X = js('edits.js'), I = js('integrity.js'), C = js('check.js'), P = js('policy.js'), D = js('importdiff.js');
const contract = JSON.parse(fs.readFileSync(path.join(ROOT, 'obra/unreal/contract.json'), 'utf8'));
const { score, name: SRC } = testScore();
console.log('on the ' + SRC);
let fails = 0;
const check = (name, ok, info) => { console.log((ok ? '  ok   ' : '  FAIL ') + name + (info ? '  · ' + info : '')); if (!ok) fails++; };
const clone = o => JSON.parse(JSON.stringify(o));
const near = (a, b, e = 1e-3) => Math.abs(a - b) <= e;
const at = '2026-10-07T12:00:00.000Z';
const mig = (s, c = contract, ctx) => X.migrate3(s, E, c, Object.assign({ at, who: 'B' }, ctx));
const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'vvr-migrate3-'));

try {
  if (score.schema !== 2) {
    console.log(`the score is schema ${score.schema}: there is nothing to upgrade (the upgrade is checked on the frozen fixture)`);
    const r = mig(score);
    check('a schema 3 score is refused, with the reason, and nothing comes back to apply', !r.next && !r.report.ok && r.report.refusals.some(x => x.code === 'M3.SCHEMA' && /already schema 3/.test(x.msg)));
  } else {
    const before = JSON.stringify(score), idByUid = {};
    for (const id of Object.keys(score.elements)) idByUid[score.elements[id].legacy.uid] = id;
    const T0 = E.resolve(score, { persona: 'typical' }), key = id => (score.elements[id] || score.beats[id]).key;
    let t = Date.now(); const r = mig(score); const ms = Date.now() - t, n = r.next, rep = r.report;

    console.log('what it makes');
    check('the fixture upgrades: ok, no refusal, a score comes back', rep.ok && n && !rep.refusals.length, `${ms} ms`);
    check('  pure: the score it was given is exactly as it was', JSON.stringify(score) === before && n !== score && n.elements !== score.elements);
    check('  schema 3, the same rev; golden and the per-element `when` gone; branches, baseline and uidMap there', n.schema === 3 && n.rev === score.rev && !('golden' in n) && !!n.branches && !!n.baseline && !!n.uidMap);
    let ok = true; try { X.validate(n, E); } catch (e) { ok = false; console.log(e.message); }
    check('  Edits.validate reads it, and the invariants the server applies pass against the schema-2 score it came from', ok && C.invariants(n, score, { Engine: E, Edits: X, contract }).ok);
    check('  the ids, lanes, groups, acts, markers and notes are the same ones', JSON.stringify(Object.keys(n.elements)) === JSON.stringify(Object.keys(score.elements)) && JSON.stringify(Object.keys(n.beats)) === JSON.stringify(Object.keys(score.beats))
      && JSON.stringify([n.lanes, n.groups, n.acts, n.markers, n.notes]) === JSON.stringify([score.lanes, score.groups, score.acts, score.markers, score.notes]));

    console.log('nothing moves for the typical user (§10.2 step 9)');
    const T1 = E.resolve(n, { persona: 'typical' }), T1a = E.resolve(n, { persona: 'typical', branch: 'all' }), T1y = E.resolve(n, { persona: 'typical', branch: { share: 'yes' } });
    const ids = Object.keys(T0.t), worst = T => Math.max(...ids.map(i => Math.max(Math.abs(T.t[i][0] - T0.t[i][0]), Math.abs(T.t[i][1] - T0.t[i][1]))));
    check(`typical, default branch: ${ids.length}/${ids.length} starts and ends equal (±1 ms), total ${T1.total.toFixed(4)}`, ids.length === 665 && worst(T1) <= 1e-3 && near(T1.total, T0.total));
    check('  all branches at once, and SHARE chosen: the same 665', worst(T1a) <= 1e-3 && worst(T1y) <= 1e-3 && near(T1a.total, T0.total) && near(T1y.total, T0.total));
    check('  the two known anchor loops are still the only ones (2.R4, 5.R4), and nothing dangles', JSON.stringify(T1.cycles.map(key).sort()) === JSON.stringify(T0.cycles.map(key).sort()) && T1.cycles.length === 2 && !T1.dangling.length);
    const Tn = E.resolve(n, { persona: 'typical', branch: { share: 'no' } });
    const shifts = {}; for (const i of ids) { const d = Tn.t[i][0] - T1y.t[i][0]; if (Math.abs(d) > 1e-3) { const k = d.toFixed(2); shifts[k] = (shifts[k] || 0) + 1; } }
    check(`DON'T SHARE: the total is 3.25 s shorter and 37 later items start earlier (36 by 3.25 s; VO_37 by 2.75 s: VO_35c is 0.5 s shorter than VO_35b)`, near(T1y.total - Tn.total, 3.25) && JSON.stringify(shifts) === JSON.stringify({ '-3.25': 36, '-2.75': 1 }), JSON.stringify(shifts));
    check('  no anchor crosses to the other side in either option', !T1y.crossBranch.length && !Tn.crossBranch.length && !E.resolve(n, { persona: 'typical' }).crossBranch.length);

    console.log('the four simulated users: the table of design B §1.2 (±0.01 s, the table has two decimals)');
    const expect = readExpect(), want = { fast: [988.80, 988.80, 988.80, 985.55], typical: [1018.00, 1018.00, 1018.00, 1014.75], slow: [1085.28, 1076.61, 1076.61, 1073.36], idle: [1176.28, 1148.61, 1148.61, 1145.36] };
    for (const p of Object.keys(want)) {
      const tt = rep.totals[p], w = want[p], moved = rep.moved[p];
      check(`${p.padEnd(7)} today ${tt.today.toFixed(2)} (F0 ${expect.totals[p]}) → v3 ${tt.all.toFixed(2)} · SHARE ${tt.share.toFixed(2)} · DON'T SHARE ${tt.no.toFixed(2)} · ${moved} items start elsewhere`,
        near(tt.today, expect.totals[p]) && [tt.today, tt.all, tt.share, tt.no].every((v, i) => near(v, w[i], .006)) && near(tt.view, tt.share) && moved === ({ fast: 0, typical: 0, slow: 466, idle: 466 })[p]);
    }
    // what is measured again, independent of the report
    for (const p of ['slow', 'idle']) { const a = E.resolve(score, { persona: p }), v = E.resolve(n, { persona: p });
      check(`  ${p}: the engine agrees with the report (${a.total.toFixed(2)} → ${v.total.toFixed(2)})`, near(a.total, rep.totals[p].today) && near(v.total, rep.totals[p].view)); }

    console.log('SHARE and DON\'T SHARE (D7)');
    const sideOf = id => n.elements[id].branch, hasWhen = Object.keys(score.elements).filter(i => score.elements[i].when);
    const yes = ['9.5b/VO_36c', '9.5b/FX_RINGVANISH', '9.5b/RING_FREE', '9.5b/FX_SOULSWIM', '9.5b/FISH_DOOR', '9.5b/FX_DOOROPEN', '9.5b/DOOR_W_SOUL', '9.5b/FX_SOULSWIM#2', '9.5b/FISH_AWAY', '9.7/FX_SOULJOIN', '9.7/VO_35b'];
    const no = ['9.5b/VO_36d', '9.5b/FX_SOULVANISH', '9.5b/SOUL_VANISH', '9.6/FX_DOOROPEN', '9.7/VO_35c'];
    check('16 elements carry `when` in the score: 11 go to SHARE and 5 to DON\'T SHARE, each the one the table says (by prototype uid)', hasWhen.length === 16 && yes.every(u => sideOf(idByUid[u]) && sideOf(idByUid[u]).on === 'share' && sideOf(idByUid[u]).value === 'yes')
      && no.every(u => sideOf(idByUid[u]) && sideOf(idByUid[u]).value === 'no') && rep.branch.elements === 16 && rep.branch.share === 11 && rep.branch.no === 5, `${rep.branch.share} / ${rep.branch.no}`);
    check('  `when` is gone from those 16 and its text is kept in legacy.when ("when" for the four inline closures); the rest are as they were', hasWhen.every(i => !('when' in n.elements[i]) && n.elements[i].legacy.when === score.elements[i].when)
      && n.elements[idByUid['9.7/VO_35b']].legacy.when === 'when' && n.elements[idByUid['9.5b/VO_36c']].legacy.when === 'yes'
      && Object.keys(score.elements).filter(i => !hasWhen.includes(i)).every(i => 'when' in n.elements[i] && JSON.stringify(n.elements[i]) === JSON.stringify(score.elements[i]) || n.elements[i].gate || n.elements[i].alt));
    const b = n.branches.share;
    check('  branches.share: name, gate = G_SHARE, SHARE / DON\'T SHARE with their marks, default SHARE, on timeout DON\'T SHARE (BP_Obra_SC FlowShare)', Object.keys(n.branches).join() === 'share' && b.gate === idByUid['9.5/G_SHARE'] && b.default === 'yes' && b.onTimeout === 'no'
      && b.options.yes.label === 'SHARE' && b.options.no.label === "DON'T SHARE" && b.options.yes.mark === 'SHARE.yes' && b.options.no.mark === 'SHARE.no' && /FlowShare/.test(b.note));
    const v37 = idByUid['9.8/VO_37'] || Object.keys(score.elements).find(i => score.elements[i].key === 'VO_37'), v35c = idByUid['9.7/VO_35c'], v35b = idByUid['9.7/VO_35b'];
    const withAlt = Object.keys(n.elements).filter(i => n.elements[i].alt).concat(Object.keys(n.beats).filter(i => n.beats[i].alt));
    check('VO_37 (anchored to the end of VO_35b) gets an anchor for DON\'T SHARE: the end of VO_35c, +0, as today; nothing else needs one', withAlt.length === 1 && withAlt[0] === v37 && n.elements[v37].at.ref === v35b
      && JSON.stringify(n.elements[v37].alt) === JSON.stringify({ 'share=no': { at: { ref: v35c, edge: 'end', off: 0 } } }) && rep.branch.alt.length === 1 && rep.branch.alt[0].to === 'VO_35c', JSON.stringify(n.elements[v37].alt));
    check('  its primary anchor and every time in SHARE are untouched; in DON\'T SHARE it follows VO_35c', JSON.stringify(n.elements[v37].at) === JSON.stringify(score.elements[v37].at) && near(T1y.t[v37][0], T0.t[v37][0]) && near(Tn.t[v37][0], Tn.t[v35c][1]));

    console.log('waits (D8)');
    const gates = Object.keys(score.elements).filter(i => score.elements[i].gate), clock = ['G_BREATH', 'G_HEART', 'G_GRAB', 'G_DRAW'];
    const g = k => n.elements[Object.keys(n.elements).find(i => n.elements[i].key === k)].gate;
    check('10 waits; the four of the stage clock say blocking: false, the six that wait for the user say true; expected and fw are as they were', gates.length === 10 && gates.every(i => n.elements[i].gate.blocking === !clock.includes(n.elements[i].key)
      && n.elements[i].gate.expected === score.elements[i].gate.expected && n.elements[i].gate.fw === score.elements[i].gate.fw) && JSON.stringify(rep.waits.stageClock) === JSON.stringify(clock) && rep.waits.blocking.length === 6, rep.waits.blocking.join(' '));
    check('  each one names what it waits for (vocabulary v0) and, where the Unreal knob IS its timeout, the knob', g('G_BELL').cond === 'hall.bell.charged' && g('G_BELL').knob === 'BP_HallDirector_SC.FW_Bell' && g('G_SENSOR').knob === 'BP_HallDirector_SC.FW_Tool'
      && g('G_CHOOSE').knob === 'BP_HallDirector_SC.FW_Choose' && g('G_SHARE').knob === 'DA_Partitura_Obra.Res_Cortafuegos' && g('G_SHARE').cond === 'share.pick' && g('G_BREATH').cond === 'breath.zone' && g('G_DRAW').cond === 'draw.ink>0'
      && !('knob' in g('G_BREATH')) && !('knob' in g('G_SAVE4')) && g('G_SAVE4').cond === 'attract.saved' && g('G_SAVE5').cond === 'draw.saved' && g('G_HEART').cond === 'heart.zone' && g('G_GRAB').cond === 'attract.first');
    const fromContract = id => !I.contractFor(id, score.elements[id], contract).some(c => c.kind === 'not-blocking');
    check('MIGRATE3.waits agrees with the contract (not-blocking entries) for the 10 waits, and the upgrade uses the contract', Object.entries(X.MIGRATE3.waits).length === 10 && Object.entries(X.MIGRATE3.waits).every(([u, w]) => idByUid[u] && fromContract(idByUid[u]) === w.blocking
      && n.elements[idByUid[u]].gate.blocking === fromContract(idByUid[u])) && !rep.notes.length, rep.notes.join(' | '));
    { const c2 = clone(contract); c2.entries = c2.entries.filter(c => c.id !== 'wait.notblocking');   // the contract says G_BREATH / G_HEART block: that is what is written (and said)
      const r2 = mig(score, c2); check('  if the contract changed (G_BREATH and G_HEART blocking), it is the contract that decides, and the note says it differs from what was expected',
        !!r2.next && r2.next.elements[idByUid['1.R4/G_BREATH']].gate.blocking === true && r2.next.elements[idByUid['2.R4/G_HEART']].gate.blocking === true && r2.report.notes.length === 2 && /contract says it blocks/.test(r2.report.notes[0])); }

    console.log('the APK baseline (D4)');
    const bl = n.baseline;
    check('baseline: kind, the total of the prototype, one [start in its moment, length] per element (592), a log that says it was migrated', bl.kind === 'prototype-f0' && near(bl.total, score.golden.total, 1e-6) && Object.keys(bl.rel).length === 592
      && Object.keys(bl.rel).every(i => { const t = score.golden.times[i], q = score.golden.times[score.elements[i].beat]; return near(bl.rel[i][0], t[0] - q[0], 1e-4) && near(bl.rel[i][1], t[1] - t[0], 1e-4); })
      && bl.log.length === 1 && bl.log[0].op === 'migrate' && bl.log[0].at === at && bl.log[0].by === 'B' && rep.baseline.elements === 592);
    check('  ≠ APK: 0 before and 0 after on the score as it is', rep.baseline.apk.before === 0 && rep.baseline.apk.after === 0);
    { // the same set of ≠ APK elements before and after, with something to find: five voices of Unreal moved, one wired wait changed
      const e = clone(score); for (const k of ['VO_04', 'VO_10', 'VO_13']) e.elements[Object.keys(e.elements).find(i => e.elements[i].key === k)].at.off += 2;
      e.golden.voices = [{ at: '2026-10-06T09:00:00.000Z', by: 'S', ids: ['x'], src: 'final mix' }];
      const Te = E.resolve(e, { persona: 'typical' }), D0 = I.divergent(e, Te, contract), re = mig(e), D1 = re.next && I.divergent(re.next, E.resolve(re.next, { persona: 'typical' }), contract);
      check('  a score with edits: the same elements are ≠ APK after as before (the baseline came over faithfully), and the log keeps the voices that were applied', !!re.next && D0.size > 0 && D0.size === D1.size && [...D0].every(i => D1.has(i))
        && re.next.baseline.log.length === 2 && re.next.baseline.log[1].op === 'voices' && re.next.baseline.log[1].src === 'final mix' && re.next.baseline.log[1].by === 'S', `${D0.size} elements`);
      // lote 3's claim on the migrated shape: after the real voice lengths, ≠ APK is 0 (shiftBaseline on a migrated baseline)
      const q = clone(n); for (const id of Object.keys(q.elements)) if (q.elements[id].type === 'vo') q.elements[id].dur = { mode: 'audio', value: q.elements[id].dur.value + 0.7 };
      const Tq = E.resolve(q, { persona: 'typical' }), q2 = clone(q); q2.baseline = X.shiftBaseline(q.baseline, { score: n, sched: T1 }, { score: q, sched: Tq }, null, { op: 'voices' });
      check('  shiftBaseline works on the migrated baseline: after every voice lasts 0.7 s longer and the baseline moves with it, nothing is ≠ APK',
        I.divergent(q, Tq, contract).size > 0 && I.divergent(q2, Tq, contract).size === 0, `${I.divergent(q, Tq, contract).size} → ${I.divergent(q2, Tq, contract).size}`); }

    console.log('stable names (D2): uidMap');
    const um = n.uidMap, uids = Object.keys(um);
    check('uidMap: 592 elements by their prototype uid and 73 moments by "@" + key, each with its id and a signature', uids.length === 665 && uids.filter(u => u[0] === '@').length === 73 && uids.every(u => um[u].id && /^[0-9a-f]{10}$/.test(um[u].sig))
      && Object.keys(score.elements).every(i => um[score.elements[i].legacy.uid].id === i) && Object.keys(score.beats).every(i => um['@' + score.beats[i].key].id === i) && rep.names.elements === 592 && rep.names.moments === 73);
    const recs = D.recordsOf(score), recsAfter = D.recordsOf(n);
    check('  the signature is that of the record guion.js gave: it is the same on the schema-2 score and on the upgraded one, 665/665 (the record does not depend on `when` moving to legacy)', Object.keys(recs).length === 665 && uids.every(u => um[u].sig === D.sigOf(recs[u]) && D.sigOf(recsAfter[u]) === um[u].sig));
    check('  two different records do not share a signature (a guion.js edit would show), and the order of keys does not matter', new Set(uids.map(u => um[u].sig)).size > 600 && D.sigOf({ a: 1, b: { c: [1, 2], d: null } }) === D.sigOf({ b: { d: null, c: [1, 2] }, a: 1 }) && D.sigOf({ a: 1 }) !== D.sigOf({ a: 2 }));
    // against a FRESH extraction of guion.js (the prototype as it is now): only when it is the one the fixture was frozen from
    const exp = readExpect(), sha = fs.existsSync(path.join(ROOT, 'web/prototipo-narrativo/guion.js')) ? require('node:crypto').createHash('sha1').update(fs.readFileSync(path.join(ROOT, 'web/prototipo-narrativo/guion.js'))).digest('hex') : null;
    if (!sha || sha !== exp.guion_sha1) console.log('  info  guion.js changed since the fixture was frozen: a fresh extraction is not the fixture any more (the signatures are compared with the fixture only)');
    else {
      const out = path.join(TMP, 'fresh.json'), x = spawnSync(process.execPath, [path.join(ROOT, 'tools/score/extract_v1.mjs'), '--out', out], { cwd: ROOT, encoding: 'utf8' });
      const fresh = x.status === 0 && JSON.parse(fs.readFileSync(out, 'utf8')), fr = fresh && D.recordsOf(fresh);
      const same = fr && uids.filter(u => fr[u] && D.sigOf(fr[u]) === um[u].sig).length, sameId = fr && Object.keys(score.elements).filter(i => fresh.elements[i] && fresh.elements[i].legacy.uid === score.elements[i].legacy.uid).length;
      check(`  a fresh extraction of guion.js gives the same signature for ${same}/665 and the same id for ${sameId}/592 of what the upgrade stored`, !!fr && same === 665 && sameId === 592 && Object.keys(fr).length === 665, x.status ? x.stderr.slice(0, 200) : '');
    }

    console.log('accepted problems (§9) keep their value');
    { const a = clone(score); a.accepted = [
        { fp: 'C3.DRIFT|' + idByUid['1.8/G_BELL'] + '|30|25', rule: 'C3.DRIFT', ly: 'C3', sv: 'warn', el: idByUid['1.8/G_BELL'], who: 'B', reason: 'ok', at: '2026-10-06T00:00:00.000Z', msg: 'm' },
        { fp: 'C3.WAIT.HALL.BELL|' + idByUid['1.8/G_BELL'], rule: 'C3.WAIT.HALL.BELL', ly: 'C3', sv: 'warn', el: idByUid['1.8/G_BELL'], who: 'S', reason: 'card', at: '2026-10-06T00:00:00.000Z', verb: 'gate', history: [{ who: 'S', reason: 'card', at: '2026-10-06T00:00:00.000Z', verb: 'gate' }] },
        { fp: 'C2.TOTAL.GOAL||33', rule: 'C2.TOTAL.GOAL', ly: 'C2', sv: 'warn', who: 'B', reason: 'goal', at: '2026-10-06T00:00:00.000Z' },
        { fp: 'C2.VO.REAL|', rule: 'C2.VO.REAL', ly: 'C2', sv: 'warn', who: 'B', reason: 'later', at: '2026-10-06T00:00:00.000Z' },
        { fp: 'C3.PARTITURA|Alma_Entra|5.5,5', rule: 'C3.PARTITURA', ly: 'C3', sv: 'warn', who: 'B', reason: 'k', at: '2026-10-06T00:00:00.000Z', state: 'reopened', value: 'kept' }];
      const ra = mig(a), q = ra.next && ra.next.accepted;
      check('  records with a parameter get it as `value` (the part after rule|element, with its own "|"); the ones without get null; an existing value and state stay', !!q && q.length === 5 && q[0].value === '30|25' && q[1].value === null && q[2].value === '33' && q[3].value === null && q[4].value === 'kept' && q[4].state === 'reopened'
        && q.slice(0, 4).every(x => x.state === 'accepted') && ra.report.accepted.n === 5 && ra.report.accepted.withValue === 3, q && q.map(x => x.value).join(' · '));
      check('  their fingerprint becomes rule|element (the value is the rest of it: a record answers a problem at that value, design B §9, Integrity.judge reads both shapes); author, reason, verb and history stay; the old records are not touched', !!q && q.every((x, i) => x.fp === I.fpParts(a.accepted[i].fp).base && x.who === a.accepted[i].who && x.reason === a.accepted[i].reason && x.verb === a.accepted[i].verb
        && JSON.stringify(x.history) === JSON.stringify(a.accepted[i].history)) && a.accepted[0].value === undefined && !('state' in a.accepted[0]));
      let v3ok = true; try { X.validate(ra.next, E); } catch (e) { v3ok = false; }
      check('  and the upgraded score with those records validates', v3ok); }

    console.log('refusals (never a guess)');
    const refused = (name, s, re, c = contract) => { const x = mig(s, c); check(name, !x.next && !x.report.ok && x.report.refusals.length > 0 && re.test(x.report.refusals.map(q => q.code + ' ' + q.msg).join(' | ')), x.report.refusals.map(q => q.code).join(',')); return x; };
    refused('a schema 3 score (the upgraded one again): refused, "already schema 3"', n, /M3\.SCHEMA .*already schema 3/);
    refused('not a score at all', null, /M3\.SCHEMA/);
    { const s = clone(score); s.elements[idByUid['9.7/VO_35b']].when = 'maybe'; const x = refused('a `when` the upgrade does not know (a name that is neither yes nor no, and no uid in the table): refused, naming it', s, /M3\.WHEN .*VO_35b \(maybe\)/); check('  and says which ids', x.report.refusals[0].ids.length === 1 && x.report.refusals[0].ids[0] === idByUid['9.7/VO_35b']); }
    { const s = clone(score); s.elements[idByUid['9.7/VO_35c']].when = 'yes'; refused('a `when` that says the opposite of the table (VO_35c is DON\'T SHARE): refused', s, /M3\.WHEN/); }
    { const s = clone(score), id = 'el_zz9mine', src = score.elements[idByUid['1.R4/G_BREATH']]; s.elements[id] = Object.assign(clone(src), { key: 'G_NEW', isNew: true, legacy: null }); const x = refused('a wait the upgrade does not know (made in the editor): refused, naming it', s, /M3\.WAIT .*G_NEW/); check('  and a wait whose uid is not in the table too', (() => { const s2 = clone(score); s2.elements[idByUid['1.R4/G_BREATH']].legacy.uid = '1.R4/G_ODD'; return /M3\.WAIT/.test(mig(s2).report.refusals.map(q => q.code).join()); })()); }
    refused('without the contract: refused (it says which waits block)', score, /M3\.CONTRACT/, null);
    { const s = clone(score); delete s.golden; refused('a score without its prototype schedule: refused (nothing to become the baseline)', s, /M3\.GOLDEN/); }
    { const s = clone(score); s.acts[0].beats.push('bt_nope'); refused('a score that is not valid: refused with the reason', s, /M3\.STRUCT .*missing moment/); }
    { const s = clone(score), a = idByUid['9.5b/FX_RINGVANISH'], c = idByUid['9.5b/VO_36d']; s.elements[a].at = { ref: c, edge: 'end', off: 0 };   // SHARE hanging from DON'T SHARE: no anchor can fix it
      refused('a clip of one side hanging from the other side: refused, naming it (nothing crosses between the sides after the upgrade)', s, /M3\.CROSS .*FX_RINGVANISH in SHARE/); }
    { const s = clone(score), c = idByUid['9.5b/SOUL_VANISH']; s.elements[c].dur = { mode: 'fixed', value: 30 };   // DON'T SHARE is the longest side: in SHARE the moment would end earlier
      const x = refused('the moment of the piece ends with a DON\'T SHARE clip: SHARE would shorten it, so the typical times move: refused (the upgrade changes no time)', s, /M3\.MOVED/); check('  and says how many items would move', /items? would move for the typical user/.test(x.report.refusals[0].msg) && x.report.refusals[0].ids.length > 3); }
    check('a refusal gives nothing to apply and never touches the score', JSON.stringify(score) === before);

    console.log('what it fits in');
    check('the upgrade is one of the quiet operations (its own card was the decision)', P.QUIET.has('migrate'));
    check('the staticProblems of a schema 2 score offer it (C1.SCHEMA, info, "Whole score"), a schema 3 score does not', (() => { const p = I.staticProblems(score, T0, contract).filter(x => x.rule === 'C1.SCHEMA'), p3 = I.staticProblems(n, T1, contract).filter(x => x.rule === 'C1.SCHEMA');
      return p.length === 1 && p[0].sv === 'info' && p[0].ly === 'C1' && p[0].where === 'Whole score' && p[0].el === null && !p3.length; })());
    { // what the CLI says about it, as the server runs it (against the schema 2 score on disk)
      const f = path.join(TMP, 'migrated.json'), b = path.join(TMP, 'base.json'); fs.writeFileSync(f, JSON.stringify(n)); fs.writeFileSync(b, JSON.stringify(score));
      const x = spawnSync(process.execPath, [path.join(ROOT, 'tools/score/check.mjs'), f, '--base', b, '--contract', path.join(ROOT, 'obra/unreal/contract.json'), '--json'], { cwd: ROOT, encoding: 'utf8' }), j = x.stdout && JSON.parse(x.stdout);
      check('check.mjs (the server\'s own check) accepts it over the schema-2 score: exit 0, no error, the two known loops grandfathered', x.status === 0 && j.ok && !j.errors.length && j.schema === 3 && j.grandfathered.length === 2, `exit ${x.status} · ${j && j.errors.map(e => e.code)}`);
      const x2 = spawnSync(process.execPath, [path.join(ROOT, 'tools/score/check.mjs'), b, '--base', f, '--json'], { cwd: ROOT, encoding: 'utf8' }), j2 = JSON.parse(x2.stdout);
      check('  the way back is refused (an old editor saving schema 2 over the upgraded score): S.SCHEMA.DOWN', x2.status === 1 && j2.errors.some(e => e.code === 'S.SCHEMA.DOWN')); }
    check('it is fast enough to run when the card opens and again when it is applied', ms < 1500, `${ms} ms`);

    console.log('after the upgrade the score stays saveable when it is edited (review of this step)');
    { const inv = s => C.invariants(s, n, { Engine: E, Edits: X, contract }), codes = r => r.errors.map(e => e.code).join();
      const gone = idByUid['0/FX_DISCLAIMER'] || Object.keys(n.elements)[0], uid = n.elements[gone].legacy.uid;
      // the control: a delete that forgets the uidMap is exactly what the server refuses (so the cases below could fail)
      const raw = clone(n); delete raw.elements[gone];
      check('control: taking an element out and leaving its name live in the uidMap is refused (S.UIDMAP): the check can fail', codes(inv(raw)) === 'S.UIDMAP', codes(inv(raw)));
      const done = X.reconcileUidMap(n, raw);
      check('  with the name kept as deleted-here (id and signature stay) the same score passes, and no other name changed', done.join() === uid && inv(raw).ok && raw.uidMap[uid].state === 'deleted-here' && raw.uidMap[uid].id === gone && raw.uidMap[uid].sig === n.uidMap[uid].sig
        && Object.keys(n.uidMap).filter(k => k !== uid).every(k => JSON.stringify(raw.uidMap[k]) === JSON.stringify(n.uidMap[k])));
      // any element, one by one, plainly (the 592): each delete passes the invariants once it goes through reconcileUidMap
      let bad = 0, first = '';
      for (const id of Object.keys(n.elements)) { const d = clone(n); delete d.elements[id]; X.reconcileUidMap(n, d); const r = inv(d); if (r.errors.some(e => e.code === 'S.UIDMAP' || e.code === 'S.IDS.DUP')) { bad++; first = first || n.elements[id].key; } }
      check('  every one of the 592 elements: deleted plainly, no uidMap error', bad === 0, bad ? bad + ' fail, first ' + first : '');

      // the planner: both ways out for what hangs from VO_35b / VO_35c (VO_37 hangs from both, in its own option)
      const v37 = idByUid['9.7/VO_37'], v35b = idByUid['9.7/VO_35b'], v35c = idByUid['9.7/VO_35c'], K = k => n.elements[k].key;
      const at = (s, o) => E.resolve(s, { persona: 'typical', branch: { share: o } }).t[v37];
      const snap = JSON.stringify(n);
      for (const ids of [[v35c], [v35b], [v35b, v35c]]) {
        const p = X.planDelete(n, ids, E);
        check(`delete ${ids.map(K).join(' + ')}: a plan is offered (VO_37 hangs from it), it is pure`, !!p && p.direct.join() === v37 && JSON.stringify(n) === snap);
        if (!p) continue;
        const a = p.reanchor, f = p.family, ra = inv(a.next), rf = inv(f.next);
        check('  re-anchor: ok, nothing moves, the invariants pass (no S.ANCHOR.MISSING, no S.UIDMAP), VO_37 keeps its time in SHARE and in DON\'T SHARE',
          a.ok && a.moved === 0 && ra.ok && [0, 1].every(i => near(at(a.next, 'yes')[i], at(n, 'yes')[i]) && near(at(a.next, 'no')[i], at(n, 'no')[i])), codes(ra));
        check('  its anchors point to things that exist, and the names of what was deleted are deleted-here', ['at', 'end'].every(f2 => !a.next.elements[v37][f2] || !a.next.elements[v37][f2].ref || !!a.next.elements[a.next.elements[v37][f2].ref])
          && !ids.includes(a.next.elements[v37].alt['share=no'].at.ref) && ids.every(i => a.next.uidMap[n.elements[i].legacy.uid].state === 'deleted-here'));
        check('  delete them too: VO_37 goes with it, the invariants pass, VO_37 is deleted-here too', f.ok && f.deleted === ids.length + 1 && rf.ok && f.next.uidMap['9.7/VO_37'].state === 'deleted-here', codes(rf));
      }
      // the totals do not drift: the other option's total after taking VO_35c out is what the engine says
      const P = X.planDelete(n, [v35c], E), tn = E.resolve(P.reanchor.next, { persona: 'typical', branch: { share: 'no' } }).total, t0 = E.resolve(n, { persona: 'typical', branch: { share: 'no' } }).total;
      check('  deleting a DON\'T SHARE clip does not change the SHARE total (the card\'s total), and VO_37 is where the plan says in the other option', near(P.reanchor.total1, P.reanchor.total0) && near(tn, t0), `DON'T SHARE total ${t0.toFixed(2)} → ${tn.toFixed(2)}`);
    }
    check('and again, with the same input, the same result (apart from the time it was done)', (() => { const a2 = mig(score).next; return JSON.stringify(a2) === JSON.stringify(n); })());
  }
} finally {
  fs.rmSync(TMP, { recursive: true, force: true });
}
console.log(fails ? `\n${fails} FAILED` : '\nall ok');
process.exit(fails ? 1 : 0);
