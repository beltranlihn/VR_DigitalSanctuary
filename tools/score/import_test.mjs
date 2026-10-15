// import_test.mjs · guion.js as an import source (lote 5 design B §7 and §11 steps 11-12): js/importdiff.js (diff, applyImportRows) and
// tools/score/import_report.mjs. The four scenarios of design B §1.5 are made here, in a temp folder, from a COPY of
// web/prototipo-narrativo (the original is only read: its checksum is compared at the end), extracted with
// tools/score/extract_v1.mjs --proto, and compared with the upgraded frozen fixture (tools/score/fixtures/f0-score.json, migrated in memory):
//   unchanged   no rows
//   ghost       an extra cue before ghostSpan in 1.8: 1 added + 1 name that follows ('#2'); the clip that was there keeps its id
//   rename      VO_11h became VO_11hb: 1 renamed row, the same id
//   text        a voice's words and the time of another one: 2 changed rows (the length of the voice is an estimate, never taken)
//   renum       moment 1.7 became 1.7a: the moment follows, its clips' names follow, 0 false changes
// then what the verbs do (pure), what they refuse, and that nothing here writes the score or the prototype.
//   node tools/score/import_test.mjs [--live]     --live: also compares the live score with today's guion.js (information only)
// Exit 1 if any case fails.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import crypto from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { readFixture, LIVE, ROOT } from './test_score.mjs';
const require = createRequire(import.meta.url);
const js = f => require(path.join(ROOT, 'web/editor-obra/app/js', f));
const E = js('engine.js'), X = js('edits.js'), C = js('check.js'), I = js('integrity.js'), D = js('importdiff.js');
const contract = JSON.parse(fs.readFileSync(path.join(ROOT, 'obra/unreal/contract.json'), 'utf8'));
const PROTO = path.join(ROOT, 'web/prototipo-narrativo'), EXTRACT = path.join(ROOT, 'tools/score/extract_v1.mjs'), REPORT = path.join(ROOT, 'tools/score/import_report.mjs');
const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'vvr-import-'));
let fails = 0;
const check = (name, ok, info) => { console.log((ok ? '  ok   ' : '  FAIL ') + name + (info ? '  · ' + info : '')); if (!ok) fails++; };
const clone = o => JSON.parse(JSON.stringify(o));
const sha = p => crypto.createHash('sha1').update(fs.readFileSync(p)).digest('hex');
const near = (a, b, e = 1e-3) => Math.abs(a - b) <= e;
const at = '2026-10-09T12:00:00.000Z';
let seq = 7; const rand = () => ((seq = (seq * 48271) % 2147483647) / 2147483647);   // ids made here are always the same ones
const take = (d, o) => D.applyImportRows(o.score, o.extracted, d, o.sel, Object.assign({ Edits: X, Engine: E, at, now: 1.8e12, rand, who: 'B' }, o.ctx));
const typ = s => E.resolve(s, { persona: 'typical' });
const protoFiles = ['guion.js', 'timeline.js', 'world.js', 'ensayo.js'];
const protoBefore = protoFiles.map(f => sha(path.join(PROTO, f)));
const liveBefore = fs.existsSync(LIVE) ? sha(LIVE) : null;

try {
  // ---- the scenarios: a copy of the prototype each, one line of guion.js changed ----
  console.log('the four scenarios of design B §1.5, extracted from copies of guion.js in ' + TMP);
  const src = fs.readFileSync(path.join(PROTO, 'guion.js'), 'utf8');
  const SCEN = {
    base: s => s,
    ghost: s => s.replace("  ghostSpan('GHOST_BELL'", "  fx('FX_GHOSTAPPEAR', 2, 'extra cue');\n  ghostSpan('GHOST_BELL'"),
    rename: s => s.replace("vo('VO_11h'", "vo('VO_11hb'"),
    text: s => s.replace('Just below your ribs… flat side toward you.', 'Just below your ribs… the flat side toward you.').replace("['SHARE_IN', 'end', .3]", "['SHARE_IN', 'end', .8]"),
    renum: s => s.replace("beatTL('1.7',", "beatTL('1.7a',"),
  };
  const EX = {};
  for (const k of Object.keys(SCEN)) {
    const dir = path.join(TMP, 'proto-' + k), out = path.join(TMP, 'ex-' + k + '.json');
    fs.cpSync(PROTO, dir, { recursive: true, filter: p => !/[\\/](modelos|hornear)([\\/]|$)/.test(p) });
    const g = SCEN[k](src);
    if (k !== 'base' && g === src) throw new Error('the scenario did not apply: ' + k);
    fs.writeFileSync(path.join(dir, 'guion.js'), g);
    // `base` goes through the environment (VVR_PROTO), the others through --proto: both ways read the copy
    const r = k === 'base' ? spawnSync(process.execPath, [EXTRACT, '--out', out], { encoding: 'utf8', env: Object.assign({}, process.env, { VVR_PROTO: dir }) })
      : spawnSync(process.execPath, [EXTRACT, '--proto', dir, '--out', out], { encoding: 'utf8' });
    if (r.status !== 0) throw new Error(`extraction of ${k} failed: ${r.stderr || r.stdout}`);
    EX[k] = JSON.parse(fs.readFileSync(out, 'utf8'));
  }
  check('each copy was extracted (extract_v1 --proto / VVR_PROTO read the copy, wrote only the given file)', Object.keys(EX).length === 5 && EX.ghost.source.file !== 'web/prototipo-narrativo/guion.js' && EX.base.source.file !== 'web/prototipo-narrativo/guion.js', EX.ghost.source.file.replace(/\\/g, '/').split('/').slice(-3).join('/'));
  const fx = readFixture(), r3 = X.migrate3(fx, E, contract, { at, who: 'B' }), s3 = r3.next;
  check('the frozen fixture upgrades in memory (the score the scenarios are compared with: schema 3, a uidMap of 665 names)', !!s3 && s3.schema === 3 && Object.keys(s3.uidMap).length === 665);
  const idOf = uid => s3.uidMap[uid].id;
  const exIdOf = (ex, uid) => Object.keys(ex.elements).find(i => ex.elements[i].legacy.uid === uid);

  console.log('unchanged guion.js (B §1.5 row 1)');
  { const d = D.diff(s3, EX.base);
    check('0 rows, nothing follows, nothing to refresh (592 clips and 73 moments, all as the score took them)', d.rows.length === 0 && !Object.keys(d.mapUpdates).length && !Object.keys(d.refresh).length && !d.hidden && d.stable === true);
    const d2 = D.diff(fx, EX.base);
    check('  the same on the schema 2 fixture, as a report (stable: false)', d2.rows.length === 0 && d2.stable === false);
    check('  the fixture itself is what an extraction of today\'s guion.js gives (one more frame of the same freeze)', JSON.stringify(Object.keys(EX.base.elements)) === JSON.stringify(Object.keys(fx.elements)));
  }

  console.log('an extra cue before ghostSpan in 1.8 (B §1.5 row 2)');
  { const d = D.diff(s3, EX.ghost), row = d.rows[0], U = '1.8/FX_GHOSTAPPEAR', U2 = U + '#2';
    check('1 row, an added one: the new cue (FX_GHOSTAPPEAR at 2 s, note "extra cue") — not a change to the cue that was there', d.rows.length === 1 && row.kind === 'added' && row.uid === U && row.rec.note === 'extra cue' && row.rec.at.off === 2 && row.defaults.join() === 'add');
    check('  1 name follows: the cue that was 1.8/FX_GHOSTAPPEAR is now …#2; it is the SAME id', Object.keys(d.mapUpdates).join() === U && d.mapUpdates[U].to === U2 && d.mapUpdates[U].id === idOf(U));
    const keep = s3.elements[idOf(U)];
    const r = take(d, { score: s3, extracted: EX.ghost, sel: { [row.rid]: ['add'] } }), n = r.next;
    check('  take it: ok, a new element, the new name is the new clip\'s and the old clip keeps its id under the shifted name', r.ok && r.added.length === 1 && n.uidMap[U].id === r.added[0] && n.uidMap[U2].id === idOf(U) && r.added[0] !== idOf(U));
    check('  the clip that was there is untouched but for its name (legacy.uid ' + U2 + ')', JSON.stringify(Object.assign({}, n.elements[idOf(U)], { legacy: keep.legacy })) === JSON.stringify(keep) && n.elements[idOf(U)].legacy.uid === U2 && n.elements[idOf(U)].key === keep.key);
    const ne = n.elements[r.added[0]];
    check('  the new element: the cue as guion.js gives it (sound, 2 s into 1.8, its note), in the lane of its group, with its name and signature in the map', ne.key === 'FX_GHOSTAPPEAR' && ne.note === 'extra cue' && ne.label === 'FX_GHOSTAPPEAR' && ne.type === 'sound' && ne.beat === idOf('@1.8') && ne.at.ref === idOf('@1.8') && ne.at.edge === 'start' && ne.at.off === 2
      && n.groups.find(g => g.id === 'fx').lanes.includes(ne.lane) && ne.legacy.uid === U && n.uidMap[U].sig === row.sig && ne.by === 'B');
    const T0 = typ(s3), T1 = typ(n), moved = Object.keys(T0.t).filter(i => !near(T0.t[i][0], T1.t[i][0]) || !near(T0.t[i][1], T1.t[i][1]));
    check('  no time moves for the typical user, the total is the same; the new cue is on a lane where nothing overlaps it', !moved.length && near(T0.total, T1.total) && !X.lanesOverlap(n, T1.t, r.added).length);
    const again = D.diff(n, EX.ghost);
    check('  after taking it: the same scan gives 0 rows and nothing follows (the signatures are the new ones)', again.rows.length === 0 && !Object.keys(again.mapUpdates).length && !Object.keys(again.refresh).length);
    check('  pure: the score it got is as it was; the new one validates and passes the invariants the server applies', JSON.stringify(s3) === JSON.stringify(r3.next) && (() => { try { X.validate(n, E); } catch (e) { console.log(e.message); return false; } return C.invariants(n, s3, { Engine: E, Edits: X, contract }).ok; })());
    // not taken: it keeps showing (the same row with the same name map), whoever scans again
    const none = take(d, { score: s3, extracted: EX.ghost, sel: {} });
    check('  not chosen: only the name that follows is written (the row is still there on the next scan)', none.ok && none.taken.names === 1 && none.added.length === 0 && D.diff(none.next, EX.ghost).rows.length === 1 && D.diff(none.next, EX.ghost).rows[0].kind === 'added' && none.next.uidMap[U2].id === idOf(U));
    // dismissed: hidden for good (a tombstone: this one was not wanted), the old clip still follows
    const no = take(d, { score: s3, extracted: EX.ghost, sel: { [row.rid]: ['dismiss'] } }), dd = D.diff(no.next, EX.ghost);
    check('  dismissed ("not this one"): no row any more, the shifted name still follows, the map remembers it was declined', no.ok && !dd.rows.length && no.next.uidMap[U].state === 'deleted-here' && no.next.uidMap[U2].id === idOf(U) && !no.added.length);
    check('  and the score that keeps that tombstone validates and passes the invariants the server applies (a declined clip is a dead name with a reserved id, not a dangling one)', (() => { try { X.validate(no.next, E); } catch (e) { console.log(e.message); return false; } return C.invariants(no.next, s3, { Engine: E, Edits: X, contract }).ok; })());
  }

  console.log('a change to a clip whose name moved: the row is handled through the id of the clip, not through a name that may belong to another clip now');
  { // the ghost cue is added AND the clip that was there (now …#2) changed in guion.js: its row says `was` = the name the NEW clip has
    const ex = clone(EX.ghost), U = '1.8/FX_GHOSTAPPEAR', U2 = U + '#2', nid = exIdOf(ex, U2); ex.elements[nid].note = 'a shifted note'; ex.elements[nid].hint = 'a hint';
    const d = D.diff(s3, ex), add = d.rows.find(q => q.kind === 'added'), ch = d.rows.find(q => q.kind === 'changed');
    check('the same cue is new AND the old one changed: 2 rows; the changed one is the old clip under its shifted name (was = the name the new clip has)', d.rows.length === 2 && !!add && !!ch && ch.uid === U2 && ch.was === U && ch.id === idOf(U));
    const one = take(d, { score: s3, extracted: ex, sel: { [ch.rid]: ['dismiss'] } }), d1 = D.diff(one.next, ex);
    check('  dismiss the changed row alone: it is recorded on the OLD clip (…#2), counted once, and its row is hidden; the new cue is still offered', one.ok && one.taken.dismissed === 1 && one.next.uidMap[U2].seen === ch.sig && !('seen' in one.next.uidMap[U2] && one.next.uidMap[U2].seen !== ch.sig)
      && !one.next.uidMap[U] && d1.rows.length === 1 && d1.rows[0].kind === 'added' && d1.hidden === 1);
    const two = take(d, { score: s3, extracted: ex, sel: { [ch.rid]: ['dismiss'], [add.rid]: ['add'] } }), d2 = D.diff(two.next, ex);
    check('  dismiss it and add the new cue in one batch: the new clip has no stray `seen`, the old clip has the signature; 0 rows, hidden 1', two.ok && two.taken.added === 1 && two.taken.dismissed === 1 && !('seen' in two.next.uidMap[U]) && two.next.uidMap[U2].seen === ch.sig && d2.rows.length === 0 && d2.hidden === 1);
    check('  and it comes back when guion.js changes that clip again', (() => { const ex3 = clone(ex); ex3.elements[nid].note = 'another note'; return D.diff(two.next, ex3).rows.some(q => q.kind === 'changed' && q.uid === U2); })());
    const tk = take(d, { score: s3, extracted: ex, sel: { [ch.rid]: ['text'], [add.rid]: ['add'] } }), dt = D.diff(tk.next, ex);
    check('  take its text and add the new cue: the signature lands on the old clip (…#2), the new clip keeps its own; 0 rows', tk.ok && tk.next.elements[idOf(U)].note === 'a shifted note' && tk.next.uidMap[U2].sig === ch.sig && tk.next.uidMap[U].sig === add.sig && dt.rows.length === 0);
    // a renumbered moment: its clips' rows carry `was` too
    const exr = clone(EX.renum), bid = exIdOf(exr, '1.7a/BELL_IN'); exr.elements[bid].note = 'a bell note';
    const dr = D.diff(s3, exr), cr = dr.rows.find(q => q.kind === 'changed');
    check('a clip of a renumbered moment changed: 1 row (was = the old name); dismiss: 0 rows, hidden 1, the 3 names follow, one is counted', dr.rows.length === 1 && cr.was === '1.7/BELL_IN' && (() => { const r = take(dr, { score: s3, extracted: exr, sel: { [cr.rid]: ['dismiss'] } }), q = D.diff(r.next, exr); return r.ok && r.taken.dismissed === 1 && r.taken.names === 3 && q.rows.length === 0 && q.hidden === 1; })());
  }

  console.log('VO_11h renamed VO_11hb (B §1.5 row 3)');
  { const d = D.diff(s3, EX.rename), row = d.rows[0], U = '1.R4/VO_11h', N = '1.R4/VO_11hb', id = idOf(U);
    check('1 row, renamed: key and label, the same id; the name follows only with it', d.rows.length === 1 && row.kind === 'renamed' && row.wasKey === 'VO_11h' && row.key === 'VO_11hb' && row.id === id && d.mapUpdates[U].to === N && d.mapUpdates[U].via === 'rename');
    const r = take(d, { score: s3, extracted: EX.rename, sel: { [row.rid]: ['rename'] } }), n = r.next, was = s3.elements[id], now = n.elements[id];
    check('  take the new name: key and label change; what Unreal plays (sound, bind) and everything else stays; the name and its signature move in the map; verb "rename"',
      r.ok && now.key === 'VO_11hb' && now.label === 'VO_11hb' && now.sound === was.sound && JSON.stringify(now.at) === JSON.stringify(was.at) && now.text === was.text && now.legacy.uid === N && n.uidMap[N].id === id && !n.uidMap[U] && n.uidMap[N].sig === row.sig && r.verbs[id] === 'rename' && r.ids.join() === id);
    check('  after taking it, 0 rows; the anchors that hang from it still do (ids)', D.diff(n, EX.rename).rows.length === 0 && Object.values(n.elements).every(e => (!e.at || !e.at.ref || n.elements[e.at.ref] || n.beats[e.at.ref])));
    const nope = take(d, { score: s3, extracted: EX.rename, sel: {} });
    check('  not taken: nothing is written (the name does not move without its rename, so the row stays), `why` says so', !nope.ok && /Nothing/.test(nope.why) && D.diff(s3, EX.rename).rows.length === 1);
    const dis = take(d, { score: s3, extracted: EX.rename, sel: { [row.rid]: ['dismiss'] } }), dd = D.diff(dis.next, EX.rename);
    check('  dismissed: the row is hidden (hidden: 1) until guion.js changes that clip again', dis.ok && dd.rows.length === 0 && dd.hidden === 1);
  }

  console.log('a voice\'s words and another voice\'s time (B §1.5 row 4)');
  { const d = D.diff(s3, EX.text), byKey = Object.fromEntries(d.rows.map(r => [r.key, r])), a = byKey.VO_11h, b = byKey.VO_36p;
    check('2 changed rows, nothing added, nothing renamed', d.rows.length === 2 && d.rows.every(r => r.kind === 'changed') && !Object.keys(d.mapUpdates).length);
    check('  VO_11h: the words (text); the length is an estimate and is not offered; offered by default', !!a && Object.keys(a.groups).join() === 'text' && a.groups.text.length === 1 && a.groups.text[0].field === 'text' && a.estimate && a.estimate.now > 0 && a.defaults.join() === 'text' && !a.edited);
    check('  VO_36p: the time it starts (at: 0.3 → 0.8 s after SHARE_IN); NOT offered by default (the Partitura rules the timing)', !!b && Object.keys(b.groups).join() === 'timing' && b.groups.timing[0].field === 'at' && b.groups.timing[0].was.off === .3 && b.groups.timing[0].now.off === .8 && b.defaults.length === 0);
    const wasT = s3.elements[a.id].text, T0 = typ(s3);
    const r1 = take(d, { score: s3, extracted: EX.text, sel: { [a.rid]: ['text'] } }), n1 = r1.next;
    check('  take VO_11h\'s words: the text changes, its length (the recording) does not, verb "text"; the timing row of the other voice is untouched and still shows',
      r1.ok && n1.elements[a.id].text !== wasT && n1.elements[a.id].text === EX.text.elements[Object.keys(EX.text.elements).find(i => EX.text.elements[i].legacy.uid === a.uid)].text
      && JSON.stringify(n1.elements[a.id].dur) === JSON.stringify(s3.elements[a.id].dur) && r1.verbs[a.id] === 'text' && D.diff(n1, EX.text).rows.length === 1 && D.diff(n1, EX.text).rows[0].key === 'VO_36p');
    const r2 = take(d, { score: s3, extracted: EX.text, sel: { [b.rid]: ['timing'] } }), n2 = r2.next, T2 = typ(n2);
    check('  take VO_36p\'s timing: it starts 0.5 s later and the anchor is the same clip (id) with the new offset; the score reads the new time; 0 rows after', r2.ok && n2.elements[b.id].at.off === .8 && n2.elements[b.id].at.ref === s3.elements[b.id].at.ref && near(T2.t[b.id][0] - T0.t[b.id][0], .5) && D.diff(n2, EX.text).rows.length === 1);
    const r3b = take(d, { score: s3, extracted: EX.text, sel: { [a.rid]: ['text'], [b.rid]: ['timing'] } });
    check('  both in one batch: 2 clips touched, one result, and the next scan is empty', r3b.ok && r3b.ids.length === 2 && D.diff(r3b.next, EX.text).rows.length === 0 && r3b.next.uidMap[a.uid].sig === a.sig && r3b.next.uidMap[b.uid].sig === b.sig);
    // the score also changed that clip: the row says so, and is never taken by default
    const ed = clone(s3); ed.elements[a.id].text = 'My own words for this line.';
    const de = D.diff(ed, EX.text), ea = de.rows.find(r => r.key === 'VO_11h');
    check('  a voice edited in the score AND in guion.js: the row says "edited here too" and offers nothing by default', ea.edited === true && ea.defaults.length === 0 && /edited here too/.test(D.rowWords(ea)) && D.diff(ed, EX.base).rows.length === 0);
    // taking only the words leaves the timing group of the same element showing (the signature moves when everything the row can take is taken)
    const both = clone(EX.text); const pick = both.elements[Object.keys(both.elements).find(i => both.elements[i].legacy.uid === b.uid)]; pick.text = 'A new line for VO_36p.';
    const d3 = D.diff(s3, both), rb = d3.rows.find(r => r.key === 'VO_36p');
    check('  one clip with its words and its time changed: ONE row with both groups', rb && Object.keys(rb.groups).sort().join() === 'text,timing');
    const r4 = take(d3, { score: s3, extracted: both, sel: { [rb.rid]: ['text'] } }), after = D.diff(r4.next, both).rows.find(r => r.key === 'VO_36p');
    check('  taking its words only: its time still shows (one group), its words do not; the signature stayed the old one', r4.ok && after && Object.keys(after.groups).join() === 'timing' && r4.next.uidMap[b.uid].sig === s3.uidMap[b.uid].sig);
  }

  console.log('moment 1.7 renumbered 1.7a (B §1.5 row 5)');
  { const d = D.diff(s3, EX.renum), U = Object.keys(d.mapUpdates).sort();
    check('moment renumbered: 1.7 → 1.7a, 0 rows (no false changes), 3 names follow: its 2 clips and the moment', JSON.stringify(d.beatRen) === '{"1.7":"1.7a"}' && !d.rows.length && U.length === 3
      && d.mapUpdates['@1.7'].to === '@1.7a' && d.mapUpdates['1.7/BELL_IN'].to === '1.7a/BELL_IN' && d.mapUpdates['1.7/FX_BELLAPPEAR'].to === '1.7a/FX_BELLAPPEAR');
    const T0 = typ(s3), r = take(d, { score: s3, extracted: EX.renum, sel: {} }), n = r.next;
    check('  "Update names": the moment\'s key becomes 1.7a, its clips\' legacy.uid follow, every id stays, the map has the new names and signatures', r.ok && r.taken.names === 3 && n.beats[idOf('@1.7')].key === '1.7a' && n.uidMap['@1.7a'].id === idOf('@1.7') && !n.uidMap['@1.7']
      && n.elements[idOf('1.7/BELL_IN')].legacy.uid === '1.7a/BELL_IN' && JSON.stringify(Object.keys(n.elements)) === JSON.stringify(Object.keys(s3.elements)) && !r.ids.length);
    const T1 = typ(n), moved = Object.keys(T0.t).filter(i => !near(T0.t[i][0], T1.t[i][0]) || !near(T0.t[i][1], T1.t[i][1]));
    check('  nothing moves; the next scan is empty (names, signatures, even what hung from the renumbered clips)', !moved.length && D.diff(n, EX.renum).rows.length === 0 && !Object.keys(D.diff(n, EX.renum).mapUpdates).length && !Object.keys(D.diff(n, EX.renum).refresh).length);
    check('  and the other direction, a score that already has 1.7a against the old guion.js, is the mirror (1.7a → 1.7)', JSON.stringify(D.diff(n, EX.base).beatRen) === '{"1.7a":"1.7"}' && D.diff(n, EX.base).rows.length === 0);
  }

  console.log('what a new moment, a removed clip and an anchor to nothing do (synthetic changes to an extraction)');
  { // a new moment after 1.8, in its act, with two clips: B hangs from A and is listed first
    const ex = clone(EX.base), actI = ex.beats[Object.keys(ex.beats).find(b => ex.beats[b].key === '1.8')].act, bid = 'bt_newmoment0';
    const b18 = Object.keys(ex.beats).find(b => ex.beats[b].key === '1.8'), act = ex.acts[actI];
    ex.beats[bid] = { key: '1.8b', title: 'A new moment', desc: 'Only in guion.js', act: actI, at: { ref: b18, edge: 'end', off: 0 } };
    act.beats.splice(act.beats.indexOf(b18) + 1, 0, bid);
    const mk = (k, extra) => Object.assign({ key: k, type: 'sound', group: 'fx', beat: bid, lane: null, at: { ref: bid, edge: 'start', off: 1 }, end: null, dur: { mode: 'instant', value: 0 }, label: k, text: null, sound: k, note: null, gate: null, help: null, simOnly: false, when: null, hint: null, ghost: null, legacy: { uid: '1.8b/' + k, track: 'fx', behavior: false } }, extra);
    ex.elements.el_nb = mk('FX_NEW_B', {}); ex.elements.el_na = mk('FX_NEW_A', {}); ex.elements.el_nb.at = { ref: 'el_na', edge: 'end', off: 1.5 };
    ex.elements.el_nb.legacy.uid = '1.8b/FX_NEW_B'; ex.elements.el_na.legacy.uid = '1.8b/FX_NEW_A';
    const d = D.diff(s3, ex), row = d.rows[0];
    check('a new moment with 2 clips: ONE row, the moment, listing its clips; offered as a whole', d.rows.length === 1 && row.kind === 'moment-added' && row.key === '1.8b' && row.elements.length === 2 && row.defaults.join() === 'add-moment');
    const r = take(d, { score: s3, extracted: ex, sel: { [row.rid]: ['add-moment'] } }), n = r.next, nb = idOf('@1.8'), bi = n.uidMap['@1.8b'].id, a = n.uidMap['1.8b/FX_NEW_A'].id, b = n.uidMap['1.8b/FX_NEW_B'].id;
    const ai = n.acts[actI].beats.indexOf(nb);
    check('  taken: the moment is in its act right after 1.8, anchored to the end of 1.8; its clips are in it', r.ok && n.acts[actI].beats[ai + 1] === bi && n.beats[bi].at.ref === nb && n.beats[bi].at.edge === 'end' && n.beats[bi].title === 'A new moment'
      && n.elements[a].beat === bi && n.elements[b].beat === bi && r.added.length === 2);
    check('  the clip that hangs from the other one (listed first) is made after it: its anchor is the new id of FX_NEW_A, with the offset guion gave; no anchor dangles', n.elements[b].at.ref === a && n.elements[b].at.off === 1.5 && n.elements[b].at.edge === 'end' && !r.flagged.length);
    const T = typ(n);
    check('  the engine places it (1.5 s after A, 1 s into its moment) and the rest of the piece is where it was (a moment with sound only: no time added)', T.dangling.length === typ(s3).dangling.length && !!T.t[bi] && near(T.t[b][0] - T.t[a][1], 1.5) && near(T.total, typ(s3).total, .01) && C.invariants(n, s3, { Engine: E, Edits: X, contract }).ok);
    check('  after taking it: 0 rows', D.diff(n, ex).rows.length === 0);
    const dis = take(d, { score: s3, extracted: ex, sel: { [row.rid]: ['dismiss'] } }), dd = D.diff(dis.next, ex);
    check('  dismissed: the moment and its two clips are declined together, nothing is offered', dis.ok && !dd.rows.length && dis.next.uidMap['@1.8b'].state === 'deleted-here' && dis.next.uidMap['1.8b/FX_NEW_A'].state === 'deleted-here' && !dis.added.length);
    // an anchor to something the score does not have
    const ex2 = clone(EX.base), bb = Object.keys(ex2.beats).find(q => ex2.beats[q].key === '1.8'); ex2.elements.el_orph = mk('FX_ORPHAN', { beat: bb, at: { ref: 'el_missing', edge: 'end', off: 2 }, legacy: { uid: '1.8/FX_ORPHAN', track: 'fx', behavior: false } });
    ex2.elements.el_orph.at = { ref: 'el_na', edge: 'end', off: 2 }; ex2.elements.el_na = mk('FX_NEW_A', { beat: bb, at: { ref: bb, edge: 'start', off: 4 }, legacy: { uid: '1.8/FX_NEW_A', track: 'fx', behavior: false } });
    const d2 = D.diff(s3, ex2), rows2 = Object.fromEntries(d2.rows.map(q => [q.key, q]));
    const r2 = take(d2, { score: s3, extracted: ex2, sel: { [rows2.FX_ORPHAN.rid]: ['add'] } }), o = r2.next.elements[r2.added[0]];
    check('an added clip that hangs from another added clip that was NOT chosen: it falls back to the start of its moment with guion\'s offset, and says so', r2.ok && o.at.ref === idOf('@1.8') && o.at.edge === 'start' && o.at.off === 2 && r2.flagged.length === 1 && /FX_NEW_A/.test(r2.flagged[0].msg));
    const r2b = take(d2, { score: s3, extracted: ex2, sel: { [rows2.FX_ORPHAN.rid]: ['add'], [rows2.FX_NEW_A.rid]: ['add'] } }), o2 = r2b.next.elements[r2b.added.find(i => r2b.next.elements[i].key === 'FX_ORPHAN')];
    check('  chosen together: it hangs from the new clip, no flag', r2b.ok && r2b.added.length === 2 && o2.at.ref === r2b.next.uidMap['1.8/FX_NEW_A'].id && o2.at.off === 2 && !r2b.flagged.length);
    // an added clip with a condition (a side of SHARE) and a wait
    const ex3 = clone(EX.base), b95 = Object.keys(ex3.beats).find(q => ex3.beats[q].key === '9.5b');
    ex3.elements.el_w = mk('FX_NEW_SIDE', { beat: b95, at: { ref: b95, edge: 'start', off: 1 }, when: 'no', legacy: { uid: '9.5b/FX_NEW_SIDE', track: 'fx', behavior: false } });
    ex3.elements.el_g = mk('G_NEW_WAIT', { beat: b95, type: 'wait', group: 'int', at: { ref: b95, edge: 'start', off: 1 }, dur: { mode: 'elastic', value: 4 }, gate: { expected: 4, fw: 20 }, legacy: { uid: '9.5b/G_NEW_WAIT', track: 'int', behavior: false } });
    const d3 = D.diff(s3, ex3), r3 = take(d3, { score: s3, extracted: ex3, sel: Object.fromEntries(d3.rows.map(q => [q.rid, ['add']])) }), side = r3.next.elements[r3.next.uidMap['9.5b/FX_NEW_SIDE'].id], gw = r3.next.elements[r3.next.uidMap['9.5b/G_NEW_WAIT'].id];
    check('  a new clip with a condition goes to its side of SHARE (branch, the old text in legacy.when); a new wait is blocking and flagged to check', r3.ok && side.branch.on === 'share' && side.branch.value === 'no' && side.legacy.when === 'no' && !('when' in side)
      && gw.gate.blocking === true && gw.gate.expected === 4 && gw.gate.fw === 20 && r3.flagged.some(f => /new wait/.test(f.msg)));
    check('  those pass validation and the invariants of the server', (() => { try { X.validate(r3.next, E); } catch (e) { console.log(e.message); return false; } return C.invariants(r3.next, s3, { Engine: E, Edits: X, contract }).ok; })());
  }
  { // a clip guion.js no longer has; a whole moment it no longer has
    const ex = clone(EX.base), gone = exIdOf(ex, '1.8/FX_BELLAPPEAR') || exIdOf(ex, Object.keys(s3.uidMap).find(u => /FX_/.test(u) && u[0] !== '@' && !s3.elements[s3.uidMap[u].id].type.includes('x')));
    const uid = ex.elements[gone].legacy.uid; delete ex.elements[gone];
    for (const i of Object.keys(ex.elements)) { for (const f of ['at', 'end']) if (ex.elements[i][f] && ex.elements[i][f].ref === gone) ex.elements[i][f] = { ref: ex.elements[i].beat, edge: 'start', off: 0 }; if (ex.elements[i].help === gone) ex.elements[i].help = null; }
    const d = D.diff(s3, ex), row = d.rows.find(r => r.kind === 'removed');
    check('a clip guion.js no longer has: a "removed" row; the score keeps it (nothing offered by default)', !!row && row.uid === uid && row.defaults.length === 0 && row.id === idOf(uid));
    const r = take(d, { score: s3, extracted: ex, sel: { [row.rid]: ['keep'] } }), dd = D.diff(r.next, ex);
    check('  Keep: the clip stays and the map says removed-in-guion; the row is gone (hidden: 1)', r.ok && r.next.uidMap[uid].state === 'removed-in-guion' && r.next.elements[idOf(uid)] && !dd.rows.some(q => q.kind === 'removed') && dd.hidden >= 1);
    check('  and the score that keeps it validates and passes the invariants too', (() => { try { X.validate(r.next, E); } catch (e) { console.log(e.message); return false; } return C.invariants(r.next, s3, { Engine: E, Edits: X, contract }).ok; })());
    const back = D.diff(r.next, EX.base);
    check('  and if guion.js has it again: it is live again, without a row (revive)', back.revive.includes(uid) && take(back, { score: r.next, extracted: EX.base, sel: {} }).next.uidMap[uid].state === undefined);
    const gone2 = clone(s3); delete gone2.elements[idOf(uid)]; X.reconcileUidMap(s3, gone2);
    check('  a clip deleted here is never offered again by a scan (its tombstone: deleted-here)', gone2.uidMap[uid].state === 'deleted-here' && D.diff(gone2, EX.base).rows.length === 0);
    // a moment gone, with its clips
    const ex2 = clone(EX.base), mb = Object.keys(ex2.beats).find(q => ex2.beats[q].key === '1.7'), mgone = Object.keys(ex2.elements).filter(i => ex2.elements[i].beat === mb);
    mgone.forEach(i => delete ex2.elements[i]); delete ex2.beats[mb]; ex2.acts.forEach(a => { a.beats = a.beats.filter(q => q !== mb); });
    const m = D.diff(s3, ex2), mrow = m.rows.find(q => q.kind === 'moment-removed');
    check('a moment guion.js no longer has: ONE row for the moment listing its clips (they are not listed twice); a moment is never deleted here: only "keep"', !!mrow && mrow.key === '1.7' && mrow.elements.length === 2 && !m.rows.some(q => q.kind === 'removed' && q.moment === '1.7') && mrow.defaults.length === 0);
  }

  console.log('what it refuses, and what it keeps');
  { const d = D.diff(fx, EX.ghost), r = D.applyImportRows(fx, EX.ghost, d, { [d.rows[0].rid]: ['add'] }, { Edits: X });
    check('a schema 2 score takes nothing (its names are not stable yet): the reason says to upgrade first; the report itself works', !r.ok && !r.next && /schema 3/.test(r.why) && /Upgrade/.test(r.why) && d.rows.length === 1 && d.stable === false);
    const d3 = D.diff(s3, EX.ghost), dis = take(d3, { score: s3, extracted: EX.ghost, sel: { [d3.rows[0].rid]: ['dismiss'] } }).next;
    const ex2 = clone(EX.ghost); const nid = Object.keys(ex2.elements).find(i => ex2.elements[i].legacy.uid === '1.8/FX_GHOSTAPPEAR'); ex2.elements[nid].label = 'a different cue now';
    const d4 = D.diff(dis, ex2);
    check('a tombstone is for good: a declined clip that guion.js changes again does not come back as new (use the editor to add it)', d4.rows.length === 0);
    // a changed row dismissed comes back when guion.js changes it again
    const dx = D.diff(s3, EX.text), ra = dx.rows.find(q => q.key === 'VO_11h'), dismissed = take(dx, { score: s3, extracted: EX.text, sel: { [ra.rid]: ['dismiss'] } }).next;
    const ex3 = clone(EX.text), tid = Object.keys(ex3.elements).find(i => ex3.elements[i].legacy.uid === ra.uid); ex3.elements[tid].text += ' And one more thing.';
    check('  a row dismissed stays hidden while guion.js says the same, and comes back when it changes that element again', D.diff(dismissed, EX.text).rows.length === 1 && D.diff(dismissed, EX.text).hidden === 1 && D.diff(dismissed, ex3).rows.some(q => q.key === 'VO_11h'));
    // nothing of the editor's own is a row: an element made in the editor has no uid, a rename here is not a change in guion.js
    const own = clone(s3); const nid2 = 'el_mine0000001'; own.elements[nid2] = Object.assign(clone(own.elements[idOf('1.8/G_BELL')]), { key: 'MINE', label: 'MINE', legacy: null, isNew: true });
    own.elements[idOf('1.R4/VO_11h')].key = 'VO_11_my_name'; own.elements[idOf('1.R4/VO_11h')].label = 'VO_11_my_name';
    check('what was made or renamed in the editor is not a change in guion.js: an element with no prototype name never shows, a clip renamed here is not offered a "rename" back', D.diff(own, EX.base).rows.length === 0);
    check('the diff is pure and quick: the score and the extraction are as they were; 592 clips and 73 moments in well under a second', (() => { const a = JSON.stringify(s3), b = JSON.stringify(EX.text), t = Date.now(); D.diff(s3, EX.text); return Date.now() - t < 1000 && JSON.stringify(s3) === a && JSON.stringify(EX.text) === b; })());
  }

  console.log('words of the rows (the panel and the CLI say the same) and the CLI');
  { const d = D.diff(s3, EX.text);
    check('rowWords / wordsOf: a row in one line, a value in words (an anchor, a length, a wait, text)', D.rowWords(d.rows[0]).startsWith('VO_11h in 1.R4: text') && D.wordsOf('at', { ref: '9.5/SHARE_IN', edge: 'end', off: .8 }) === 'end of SHARE_IN (9.5) + 0.8 s'
      && D.wordsOf('dur', { mode: 'audio', value: 5.25 }) === 'the recording 5.25 s' && D.wordsOf('gate', { expected: 4, fw: 20 }) === 'expected 4 s, timeout 20 s' && D.wordsOf('note', null) === '(none)' && D.fieldName('at') === 'Starts');
    const run = (args, env) => spawnSync(process.execPath, [REPORT, ...args], { encoding: 'utf8', env: Object.assign({}, process.env, env || {}) });
    const sp = path.join(TMP, 'score3.json'); fs.writeFileSync(sp, JSON.stringify(s3));
    const spBefore = sha(sp);
    const r0 = run(['--score', sp, '--extracted', path.join(TMP, 'ex-base.json')]);
    check('import_report: the base copy, 0 rows → "No changes since the score took it", exit 0', r0.status === 0 && /No changes since the score took it/.test(r0.stdout) && !/schema 2/.test(r0.stdout), r0.stdout.split('\n')[1]);
    const r1 = run(['--score', sp, '--extracted', path.join(TMP, 'ex-ghost.json')]);
    check('  the ghost copy: the added cue and the name that follows, exit 0', r1.status === 0 && /1 row/.test(r1.stdout) && /\+ added\s+new sound FX_GHOSTAPPEAR in 1\.8/.test(r1.stdout) && /1\.8\/FX_GHOSTAPPEAR → 1\.8\/FX_GHOSTAPPEAR#2/.test(r1.stdout));
    const r2 = run(['--score', sp, '--extracted', path.join(TMP, 'ex-text.json'), '--json']), j = r2.status === 0 && JSON.parse(r2.stdout);
    check('  --json: the rows with their groups; score and extraction named; stable true for a schema 3 score', !!j && j.rows.length === 2 && j.stable === true && j.score.schema === 3 && j.rows[0].groups && j.rows.every(r => r.sig));
    const r3 = run(['--score', path.join(TMP, 'no-such.json'), '--extracted', path.join(TMP, 'ex-text.json')]);
    check('  a score it cannot read: exit 1 with the reason (and nothing is written)', r3.status === 1 && /cannot read the score/.test(r3.stderr));
    const r4 = run(['--nope']);
    check('  an unknown option: exit 2 with the usage', r4.status === 2 && /usage/.test(r4.stderr));
    // with no --extracted it runs the extraction itself (guion.js as it is) and compares; the test sends it to --out so the extractor's
    // default file (obra/score/score.extracted.json, the one the editor's scan writes) is never left holding a scenario
    const xo = path.join(TMP, 'made-here.json'), r5 = run(['--score', sp, '--out', xo], { VVR_PROTO: path.join(TMP, 'proto-text') });
    check('  no --extracted: it extracts guion.js itself (here a copy through VVR_PROTO, to --out) and compares with the score it only read', r5.status === 0 && fs.existsSync(xo) && /2 rows/.test(r5.stdout) && sha(sp) === spBefore, r5.stdout.split('\n').slice(1, 3).join(' | ').slice(0, 140));
    const r6 = run(['--score', sp, '--out', LIVE]);
    check('  --out the score: refused by the extractor (exit 1, nothing written), the way extract_v1 refuses it', r6.status === 1 && /only written by the editor/.test(r6.stderr) && (liveBefore === null || sha(LIVE) === liveBefore));
    const r7 = run(['--score', sp, '--out', xo, '--extracted', xo]);
    check('  --out with --extracted: exit 2 (one of the two)', r7.status === 2);
  }

  if (process.argv.includes('--live') && fs.existsSync(LIVE)) {
    console.log('information: the live score against today\'s guion.js (never a failure)');
    const live = JSON.parse(fs.readFileSync(LIVE, 'utf8')), d = D.diff(live, EX.base);
    console.log(`  live score (schema ${live.schema}, rev ${live.rev}): ${d.rows.length} rows, ${Object.keys(d.mapUpdates).length} names follow${d.stable ? '' : ' · schema 2: report only'}`);
    for (const r of d.rows.slice(0, 12)) console.log('   · ' + D.rowWords(r));
  }

  console.log('nothing outside the temp folder was written');
  check('the prototype (guion.js, timeline.js, world.js, ensayo.js) is exactly as it was', JSON.stringify(protoFiles.map(f => sha(path.join(PROTO, f)))) === JSON.stringify(protoBefore));
  check('the live score is exactly as it was', liveBefore === null || sha(LIVE) === liveBefore);
  check('the frozen fixture was never changed (it is upgraded in memory)', fx.schema === 2 && !('uidMap' in fx));
} finally {
  fs.rmSync(TMP, { recursive: true, force: true });
}
console.log('\n' + (fails ? fails + ' FAILED' : 'all ok'));
process.exit(fails ? 1 : 0);
