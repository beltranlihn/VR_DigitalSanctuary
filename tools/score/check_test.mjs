// check_test.mjs — the invariants a score must keep to be saved (web/editor-obra/app/js/check.js and tools/score/check.mjs;
// lote 5 design B §8.2-§8.3 and §11 step 10, audit D12): one case per code of the table, the ratchet (only what is NEW relative
// to the base is rejected: the two known anchor loops 2.R4 and 5.R4 are grandfathered), and the exit codes of the CLI.
// The module runs in plain Node (no window). The CLI is run as the server runs it (a child process, `--stdin --base`) and from
// a file; nothing here writes obra/score/score.json (the CLI tests prove it: same bytes before and after).
// It runs on the frozen fixture tools/score/fixtures/f0-score.json (so real edits of the piece never break it); --live runs it
// on obra/score/score.json (see tools/score/test_score.mjs). Exit 1 if any case fails.
//   node tools/score/check_test.mjs [--live]
import fs from 'fs';
import os from 'os';
import path from 'path';
import crypto from 'crypto';
import { spawnSync } from 'child_process';
import { createRequire } from 'module';
import { fileURLToPath } from 'url';
import { testScore, schema3Copy, LIVE } from './test_score.mjs';
const require = createRequire(import.meta.url);
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const js = f => require(path.join(ROOT, 'web/editor-obra/app/js', f));
const E = js('engine.js'), X = js('edits.js'), C = js('check.js');
const { score, name: SRC } = testScore(); console.log('on the ' + SRC);
const before = JSON.stringify(score);
let fails = 0;
const check = (n, ok, info) => { console.log((ok ? '  ok   ' : '  FAIL ') + n + (info ? '  · ' + info : '')); if (!ok) fails++; };
const clone = o => JSON.parse(JSON.stringify(o));
const idOf = (k, s = score) => Object.keys(s.elements).find(i => s.elements[i].key === k);
const codes = r => r.errors.map(e => e.code).sort().join(',');
const run = (s, base, ctx) => C.invariants(s, base, Object.assign({ Engine: E, Edits: X }, ctx));
const key = (s, id) => (s.beats[id] || s.elements[id] || {}).key;

const S2 = score, S3 = schema3Copy(score);
const v37 = idOf('VO_37'), v35b = idOf('VO_35b'), gShare = idOf('G_SHARE');

/* a new anchor loop: the first element of a moment that counts in its end is anchored to the end of the next moment's first
   element (that moment follows this one, so its start depends on this end, which depends on it) */
function withLoop(s) {
  const n = clone(s), order = n.acts.flatMap(a => a.beats);
  for (let i = 3; i + 1 < order.length; i++) {
    const a = order[i], b = order[i + 1], known = new Set(E.resolve(s, { persona: 'typical' }).cycles);
    const at = n.beats[b].at;
    if (known.has(a) || known.has(b) || !at || at.ref !== a || at.edge !== 'end') continue;   // a moment that already loops, or one that does not follow this one
    const ea = Object.keys(n.elements).find(id => n.elements[id].beat === a && E.inBeatEnd(n, id));
    const eb = Object.keys(n.elements).find(id => n.elements[id].beat === b && !n.elements[id].help);
    if (!ea || !eb) continue;
    n.elements[ea].at = { ref: eb, edge: 'end', off: 0 };
    if (E.resolve(n, { persona: 'typical' }).cycles.some(c => !known.has(c))) return { n, el: ea, from: a, to: b };
  }
  throw new Error('the fixture has no moment pair where a loop can be made');
}
const loop = withLoop(S2);
/* a schema 3 score with the SHARE decision: the way the migration will write it (the server tests use the same shape) */
function withBranches(s) {
  const n = clone(s);
  n.branches = { share: { name: 'Share or not', gate: gShare, options: { yes: { label: 'SHARE' }, no: { label: "DON'T SHARE" } }, default: 'yes', onTimeout: 'no' } };
  return n;
}

console.log('the piece as it is');
{
  const r = run(S2, S2);
  check('against itself it holds: no error, no warning', r.ok && !r.errors.length && !r.warnings.length, `${r.errors.length} errors, ${r.warnings.length} warnings`);
  const keys = r.grandfathered.map(g => key(S2, g.ids[0])).sort();
  check('the two known anchor loops (2.R4, 5.R4) are grandfathered and listed, never rejected', r.grandfathered.every(g => g.code === 'S.CYCLE.NEW') && keys.join(',') === '2.R4,5.R4', keys.join(','));
  check('the result carries the typical total and the schema (the CLI prints them)', Math.abs(r.totals.typical - E.resolve(S2, { persona: 'typical' }).total) < 1e-9 && r.schema === 2);
  check('every item has a code with a title, a message and ids', [...r.errors, ...r.warnings, ...r.grandfathered].every(i => C.TITLES[i.code] && typeof i.msg === 'string' && i.msg && Array.isArray(i.ids)));
  const r3 = run(S3, S3);
  check('a schema 3 score holds the same way (same two loops)', r3.ok && r3.grandfathered.length === 2 && r3.schema === 3, `${r3.errors.map(e => e.code)}`);
  check('the score and the base are never changed', JSON.stringify(S2) === before);
  const t = Date.now(); for (let i = 0; i < 5; i++) run(S2, S2); const ms = (Date.now() - t) / 5;
  check('a check is fast enough to run on every save (server: inside the write lock)', ms < 400, ms.toFixed(0) + ' ms');
}

console.log('S.CYCLE.NEW (the ratchet)');
{
  const r = run(loop.n, S2);
  check('a new anchor loop is rejected', !r.ok && codes(r) === 'S.CYCLE.NEW', `${codes(r)} · ${r.errors[0] && r.errors[0].msg}`);
  check('  it says where: the moment to select, by its name', r.errors[0] && r.errors[0].ids.length === 1 && key(S2, loop.from) && /anchor loop/.test(r.errors[0].msg), JSON.stringify(r.errors[0] && r.errors[0].ids));
  check('  the two known loops are still listed as grandfathered, not mixed with the new one', r.grandfathered.length === 2);
  const again = run(loop.n, loop.n);
  check('a loop that is already in the base is not made worse: grandfathered', again.ok && again.grandfathered.length === 3, `${again.grandfathered.length} grandfathered`);
  check('fixing a loop is always allowed (the base has it, the next does not)', run(S2, loop.n).ok);
  const nb = run(loop.n, null);
  check('without a base nothing is "new": the loops are warnings, never errors', nb.ok && nb.warnings.length === 3 && nb.warnings.every(w => w.code === 'W.CYCLE') && !nb.grandfathered.length, `${nb.warnings.length} warnings`);
  const unreadable = run(loop.n, { schema: 2 });
  check('a base the engine cannot read forgives nothing: same as no base', unreadable.ok && unreadable.warnings.length === 3);
}

console.log('S.ANCHOR.MISSING (always)');
{
  const a = clone(S2), el = idOf('VO_10'); a.elements[el].at = { ref: 'el_gone', edge: 'end', off: 0 };
  let r = run(a, S2);
  check('an element anchored to nothing is rejected, once, with its name', !r.ok && codes(r) === 'S.ANCHOR.MISSING' && r.errors.length === 1 && /VO_10 starts from something that no longer exists/.test(r.errors[0].msg) && r.errors[0].ids[0] === el, `${codes(r)} ${r.errors[0] && r.errors[0].msg}`);
  const e = clone(S2); e.elements[el].end = { ref: 'el_gone', edge: 'end', off: 0 };
  r = run(e, S2); check('so is an element that lasts until nothing', codes(r) === 'S.ANCHOR.MISSING' && /lasts until/.test(r.errors[0].msg));
  const b = clone(S2), bt = Object.keys(b.beats)[3]; b.beats[bt].at = { ref: 'bt_gone', edge: 'end', off: 0 };
  r = run(b, S2); check('so is a moment anchored to nothing', codes(r) === 'S.ANCHOR.MISSING' && /^Moment /.test(r.errors[0].msg) && r.errors[0].ids[0] === bt);
  const h = clone(S2), hl = Object.keys(h.elements).find(i => h.elements[i].help); h.elements[hl].help = 'el_gone';
  r = run(h, S2); check('so is a help line whose wait is gone', codes(r) === 'S.ANCHOR.MISSING' && /is the help of/.test(r.errors[0].msg));
  const al = withBranches(S3); al.elements[v37].alt = { 'share=no': { at: { ref: 'el_gone', edge: 'end', off: 0 } } };
  r = run(al, S3); check('so is the anchor of an alternative (schema 3), whatever the option shown', !r.ok && r.errors.some(x => x.code === 'S.ANCHOR.MISSING' && /in share=no starts from/.test(x.msg)), codes(r));
  check('a base that has it does not forgive it (today there are none)', !run(a, a).ok);
  check('without a base it is rejected too', !run(a, null).ok);
  const clean = clone(S2); const o = clean.elements[el].at; clean.elements[el].at = { ref: '', edge: 'start', off: o.off || 0 };
  check('an empty ref is "no anchor", not a missing one', !run(clean, S2).errors.some(x => x.code === 'S.ANCHOR.MISSING'));
  const proto = clone(S2); proto.elements[el].at = { ref: 'constructor', edge: 'end', off: 0 };
  check("a ref named like an Object property is missing, not found on the prototype", run(proto, S2).errors.some(x => x.code === 'S.ANCHOR.MISSING' && x.ids[0] === el));
}

console.log('S.IDS.DUP');
{
  const bt = Object.keys(S2.beats)[2], el = Object.keys(S2.elements)[5];
  const a = clone(S2); a.elements[bt] = clone(S2.elements[el]);
  let r = run(a, S2);
  check('an id in both the moments and the elements is rejected', !r.ok && r.errors.some(x => x.code === 'S.IDS.DUP' && x.msg.includes(bt) && /beats, elements/.test(x.msg)), `${codes(r)} ${r.errors.map(x => x.msg)[0]}`);
  const b = clone(S2); b.lanes[Object.keys(S2.elements)[1]] = { name: 'x', group: 'int' };
  r = run(b, S2); check('so is a lane named like an element', r.errors.some(x => x.code === 'S.IDS.DUP' && /lanes, elements/.test(x.msg)));
  const c = clone(S2); c.acts.push(clone(c.acts[0]));
  r = run(c, S2); check('so is an act listed twice (the same id inside one list)', r.errors.some(x => x.code === 'S.IDS.DUP' && /acts twice/.test(x.msg)), codes(r));
  const d = clone(S2); d.markers = { mk_x: { t: 1, name: 'm', who: 'B' } }; d.notes = { mk_x: { t: 2, who: 'B', text: 't' } };
  r = run(d, S2); check('so is a bookmark and a note with the same id', r.errors.some(x => x.code === 'S.IDS.DUP' && /markers, notes/.test(x.msg)));
  const e = clone(S2); e.groups[0].id = 'ln_int_1';
  check('so is a group named like a lane (the group ids are checked by the structure too)', run(e, S2).errors.some(x => x.code === 'S.IDS.DUP'));
  r = run(a, a);
  check('a repeated id the base already has is not made worse: grandfathered, and the score can still be fixed', !r.errors.some(x => x.code === 'S.IDS.DUP') && r.grandfathered.some(g => g.code === 'S.IDS.DUP'));
  check('without a base a repeated id is an error (nothing to forgive)', run(a, null).errors.some(x => x.code === 'S.IDS.DUP'));
  const u = clone(S3); u.uidMap = { '1.1/A': { id: el, sig: 'x' }, '1.1/B': { id: el, sig: 'y' } };
  r = run(u, S3); check('two live uidMap entries with the same id are rejected', r.errors.some(x => x.code === 'S.IDS.DUP' && /uidMap has 2 live entries/.test(x.msg)), codes(r));
  const t = clone(S3); t.uidMap = { '1.1/A': { id: el, sig: 'x' }, '1.1/B': { id: el, state: 'deleted-here' } };
  check('a tombstone beside a live entry is not a duplicate', run(t, S3).ok);
}

console.log('S.SCHEMA.DOWN');
{
  const r = run(S2, S3);
  check('a schema 2 score over a schema 3 base is rejected, and says why', !r.ok && r.errors.some(x => x.code === 'S.SCHEMA.DOWN' && /schema 2/.test(x.msg) && /schema 3/.test(x.msg)), codes(r));
  check('schema 3 over schema 2 (the upgrade) is not a descent', !run(S3, S2).errors.some(x => x.code === 'S.SCHEMA.DOWN'));
  check('the same schema is not a descent', !run(S2, S2).errors.some(x => x.code === 'S.SCHEMA.DOWN') && !run(S3, S3).errors.some(x => x.code === 'S.SCHEMA.DOWN'));
  check('without a base there is nothing to go down from', !run(S2, null).errors.some(x => x.code === 'S.SCHEMA.DOWN'));
}

console.log('S.STRUCT and S.BRANCH.FIELD');
{
  const bad = (n, fn, re, base = S2) => { const s = clone(S2); fn(s); const r = run(s, base); check(n, !r.ok && r.errors.some(x => x.code === 'S.STRUCT' && re.test(x.msg)), `${codes(r)} · ${(r.errors[0] || {}).msg}`); };
  bad('a schema this editor does not read', s => { s.schema = 4; }, /schema 4/);
  bad('a score without its moments', s => { delete s.beats; }, /beats is missing/);
  bad('an element in a moment that does not exist', s => { s.elements[Object.keys(s.elements)[0]].beat = 'bt_nope'; }, /missing moment/);
  bad('a wait with times that are not numbers', s => { s.elements[gShare].gate.fw = 'x'; }, /wait times/);
  bad('a schema 2 score with schema 3 structures', s => { s.branches = {}; }, /belong to schema 3/);
  check('not a score at all (null, an array, a number)', [null, [], 7].every(x => { const r = run(x, S2); return !r.ok && r.errors[0].code === 'S.STRUCT'; }));
  const sc = (n, fn, re) => { const s = withBranches(S3); fn(s); const r = run(s, S3); check(n, !r.ok && r.errors.some(x => x.code === 'S.BRANCH.FIELD' && re.test(x.msg)) && !r.errors.some(x => x.code === 'S.STRUCT'), `${codes(r)} · ${(r.errors[0] || {}).msg}`); };
  sc('an element in a branch that does not exist: S.BRANCH.FIELD', s => { s.elements[v37].branch = { on: 'nope', value: 'yes' }; }, /not a branch option/);
  sc('an element in an option that does not exist', s => { s.elements[v37].branch = { on: 'share', value: 'maybe' }; }, /not a branch option/);
  sc('a decision with one option', s => { delete s.branches.share.options.no; }, /at least two options/);
  sc('a default that is not an option', s => { s.branches.share.default = 'maybe'; }, /default is not one of its options/);
  sc('an alt key that is not <branch>=<option>', s => { s.elements[v37].alt = { share: { at: { ref: v35b, edge: 'end' } } }; }, /not "<branch>=<option>"/);
  sc('an alt of an option that does not exist', s => { s.elements[v37].alt = { 'share=maybe': { at: { ref: v35b, edge: 'end' } } }; }, /not a branch option/);
  const good = withBranches(S3); good.elements[v37].alt = { 'share=no': { at: { ref: idOf('VO_35c'), edge: 'end', off: 0 } } };
  check('a well-formed branch with its alternative holds', run(good, S3).ok, codes(run(good, S3)));
}

console.log('S.TOTAL');
{
  const s = clone(S2), last = Object.keys(s.elements).filter(i => s.elements[i].beat === s.acts.at(-1).beats.at(-1) && E.inBeatEnd(s, i) && s.elements[i].dur)[0];
  s.elements[last].dur = { mode: 'fixed', value: 4000 };
  const r = run(s, S2);
  check('a typical total over an hour is rejected', !r.ok && r.errors.some(x => x.code === 'S.TOTAL' && /over 60:00/.test(x.msg)), `${codes(r)} · total ${(r.totals.typical / 60).toFixed(1)} min`);
  s.elements[last].dur = { mode: 'fixed', value: Infinity };
  const r2 = run(s, S2); check('a total that is not a number is rejected', r2.errors.some(x => x.code === 'S.TOTAL' && /not a number/.test(x.msg)), codes(r2));
  check('the goal (15:00) is not a limit: the piece is over it today and saves', run(S2, S2).ok && E.resolve(S2, { persona: 'typical' }).total > 900);
}

console.log('S.BRANCH.CROSS.NEW');
{
  // VO_37 (common) hangs from VO_35b.end; making VO_35b a DON'T SHARE element puts that anchor across the branches
  const cross = withBranches(S3); cross.elements[v35b].branch = { on: 'share', value: 'no' };
  const r = run(cross, S3);
  check('a common element anchored to the other option is rejected, with the way out', !r.ok && r.errors.some(x => x.code === 'S.BRANCH.CROSS.NEW' && /VO_37 is anchored to VO_35b, which only exists when share is no/.test(x.msg) && /alternative anchor/.test(x.msg) && x.ids[0] === v37), `${codes(r)} · ${(r.errors[0] || {}).msg}`);
  const alt = clone(cross); alt.elements[v37].alt = { 'share=yes': { at: { ref: alt.elements[v37].beat, edge: 'start', off: 3 } } };
  check('with an alternative anchor for that option it holds', run(alt, S3).ok, codes(run(alt, S3)));
  check('one already in the base is grandfathered, not rejected', (() => { const k = run(cross, cross); return k.ok && k.grandfathered.some(g => g.code === 'S.BRANCH.CROSS.NEW'); })());
  const nb = run(cross, null);
  check('without a base it is a warning', nb.ok && nb.warnings.some(w => w.code === 'W.BRANCH.CROSS'));
  check('a schema 2 score has no branches to cross', !run(S2, S2).grandfathered.some(g => g.code === 'S.BRANCH.CROSS.NEW'));
  // every option of every decision is run: a loop that only exists in one of them is found too (VO_35b would start when VO_37 ends,
  // and VO_37 starts when VO_35b ends: only in DON'T SHARE)
  const lp = withBranches(S3); lp.elements[v35b].alt = { 'share=no': { at: { ref: v37, edge: 'end', off: 0 } } };
  const rl = run(lp, S3);
  check("a loop that exists only in DON'T SHARE is found, and says in which", !rl.ok && rl.errors.some(x => x.code === 'S.CYCLE.NEW' && / in share=no:/.test(x.msg)), `${codes(rl)} · ${(rl.errors[0] || {}).msg}`);
  check('  and the default option alone (what the editor shows) would not have shown it', E.resolve(lp, { persona: 'typical' }).cycles.length === 2);
}

console.log('S.UIDMAP');
{
  const el = Object.keys(S2.elements)[7];
  const live = clone(S3); live.uidMap = { '1.1/A': { id: el, sig: 'x' }, '@1.1': { id: Object.keys(S2.beats)[0], sig: null }, '1.1/GONE': { id: 'el_gone', sig: 'z' } };
  const r = run(live, S3);
  check('a live uidMap entry whose element is gone is rejected, and says which', !r.ok && r.errors.length === 1 && r.errors[0].code === 'S.UIDMAP' && /1\.1\/GONE/.test(r.errors[0].msg) && /deleted-here/.test(r.errors[0].msg), codes(r));
  const tomb = clone(live); tomb.uidMap['1.1/GONE'] = { id: 'el_gone', state: 'deleted-here' };
  check('a tombstone (deleted-here, removed-in-guion) points to nothing on purpose', run(tomb, S3).ok);
  check('the entry of a moment (@…) points to a moment, and counts as found', !run(live, S3).errors.some(x => /@1\.1/.test(x.msg)));
  const k = run(live, live);
  check('one the base already has is grandfathered (the ratchet), a new one is not', k.ok && k.grandfathered.some(g => g.code === 'S.UIDMAP'));
  check('a schema 2 score has no uidMap to check', !run(S2, S2).errors.some(x => x.code === 'S.UIDMAP'));
}

console.log('warnings (shown, never rejected)');
{
  const contract = { entries: [{ id: 'x.keys', kind: 'literal', match: { keys: ['VO_10', 'NOT_IN_THE_SCORE', 'ALSO_NOT'] } }, { id: 'x.knob', kind: 'knob', match: { key: '^G_BELL$' }, knob: { name: 'FW_Nope', value: 25 } }, { id: 'x.ok', kind: 'knob', match: { key: '^G_SENSOR$' }, knob: { name: 'FW_Tool', value: 20 } }] };
  const knobs = C.knobNames({ knobs: [{ name: 'Aviso_Dur' }] }, { bps: { BP_X: [['FW_Tool', 'cat', '{}']] } });
  const r = run(S2, S2, { contract, knobs });
  check('knobNames reads the Partitura and the Blueprint dump', knobs instanceof Set && knobs.has('Aviso_Dur') && knobs.has('FW_Tool') && !knobs.has('FW_Nope') && C.knobNames(null, null) === null);
  check('W.CONTRACT: keys that match no element, and a knob that is nowhere', r.ok && r.warnings.length === 2 && r.warnings.every(w => w.code === 'W.CONTRACT') && /NOT_IN_THE_SCORE, ALSO_NOT, which are not in the score/.test(r.warnings[0].msg) && /FW_Nope/.test(r.warnings[1].msg), r.warnings.map(w => w.msg).join(' | '));
  check('without knob names the knob part is skipped (the keys are still checked)', run(S2, S2, { contract, knobs: null }).warnings.length === 1);
  const acc = clone(S2); acc.accepted = [{ fp: 'C3.DRIFT|el_gone', el: 'el_gone', rule: 'C3.DRIFT' }, { fp: 'C2.TOTAL.GOAL|', el: null }, { fp: 'x|' + el7() }];
  function el7() { return Object.keys(S2.elements)[7]; }
  const ra = run(acc, S2);
  check('W.ACCEPTED.ORPHAN: an accepted problem of a deleted element (not one without element)', ra.ok && ra.warnings.length === 1 && ra.warnings[0].code === 'W.ACCEPTED.ORPHAN', ra.warnings.map(w => w.code).join());
  const bl = clone(S3); bl.baseline.rel.el_gone = [0, 1]; bl.baseline.rel.el_gone2 = [0, 1];
  const rb = run(bl, S3);
  check('W.BASELINE.STALE: baseline ids that no longer exist (schema 3)', rb.ok && rb.warnings.length === 1 && rb.warnings[0].code === 'W.BASELINE.STALE' && /2 elements/.test(rb.warnings[0].msg));
  check('warnings never turn ok to false', ra.ok && rb.ok && r.ok);
}

console.log('the engine is the one the editor uses');
{
  const n = clone(S2), el = Object.keys(n.elements)[3];
  const r1 = C.invariants(n, S2), tmp = globalThis.ScoreEngine; // defaults: the modules next to check.js (no ctx)
  check('without a ctx it loads engine.js and edits.js beside itself (Node)', r1.ok && r1.grandfathered.length === 2 && tmp === undefined);
  check('the inputs of every case above were never changed', JSON.stringify(S2) === before && !!el);
}

/* ---------- the CLI (what the server runs) ---------- */
console.log('check.mjs (CLI)');
{
  const CLI = path.join(ROOT, 'tools/score/check.mjs'), tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'vvr-check-'));
  const write = (n, o) => { const p = path.join(tmp, n); fs.writeFileSync(p, typeof o === 'string' ? o : JSON.stringify(o)); return p; };
  const cli = (args, input) => { const r = spawnSync(process.execPath, [CLI, ...args], { input, encoding: 'utf8', timeout: 30000 }); return { code: r.status, out: r.stdout, err: r.stderr, json: (() => { try { return JSON.parse(r.stdout); } catch (_) { return null; } })() }; };
  const sha = p => crypto.createHash('sha1').update(fs.readFileSync(p)).digest('hex');
  const liveBefore = fs.existsSync(LIVE) ? sha(LIVE) : null;
  const good = write('good.json', S2), looped = write('loop.json', loop.n), s3f = write('s3.json', S3);

  let r = cli([good, '--base', good, '--json']);
  check('exit 0 when it holds; --json is one JSON line with ok, schema, totals, errors, warnings, grandfathered, ms', r.code === 0 && r.json && r.json.ok === true && r.json.schema === 2 && Math.abs(r.json.totals.typical - E.resolve(S2, { persona: 'typical' }).total) < 1e-6 && r.json.errors.length === 0 && r.json.grandfathered.length === 2 && typeof r.json.ms === 'number' && r.out.trim().split('\n').length === 1, r.out.slice(0, 120));
  r = cli([looped, '--base', good, '--json']);
  check('exit 1 when a rule is broken, and the errors are in the JSON (S.CYCLE.NEW)', r.code === 1 && r.json && r.json.ok === false && r.json.errors.length === 1 && r.json.errors[0].code === 'S.CYCLE.NEW', `${r.code} ${r.out.slice(0, 100)}`);
  r = cli([looped, '--base', looped, '--json']);
  check('  the same score against a base that has the loop: exit 0, three grandfathered', r.code === 0 && r.json.grandfathered.length === 3);
  r = cli([looped, '--json']);
  check('  without --base the loops are warnings: exit 0', r.code === 0 && r.json.warnings.length === 3 && r.json.ok === true);
  r = cli(['--stdin', '--base', good, '--json'], JSON.stringify(loop.n));
  check('--stdin --base (the server\'s call): the same verdict, exit 1', r.code === 1 && r.json && r.json.errors[0].code === 'S.CYCLE.NEW');
  r = cli(['--stdin', '--base', good, '--json'], '﻿' + JSON.stringify(S2));
  check('--stdin: a BOM in front of the JSON is not part of it; exit 0', r.code === 0 && r.json.ok);
  r = cli([good, '--base', s3f, '--json']);
  check('exit 1 for a schema that goes down (S.SCHEMA.DOWN)', r.code === 1 && r.json.errors.some(e => e.code === 'S.SCHEMA.DOWN'));
  r = cli([good]);
  check('without --json it says it in words (what, how many, each item with its code)', r.code === 0 && /schema 2, typical \d+:\d\d — ok/.test(r.out) && /W\.CYCLE/.test(r.out), r.out.split('\n')[0]);
  r = cli([looped, '--base', good]);
  check('  and the errors first', r.code === 1 && /1 rule broken/.test(r.out) && /ERROR S\.CYCLE\.NEW/.test(r.out) && /known S\.CYCLE\.NEW/.test(r.out));
  const ct = write('contract.json', { entries: [{ id: 'x', kind: 'literal', match: { keys: ['NOPE_KEY'] } }] });
  r = cli([good, '--base', good, '--contract', ct, '--json']);
  check('--contract adds its warnings (never an error); the knob names come from the files beside it', r.code === 0 && r.json.warnings.length === 1 && r.json.warnings[0].code === 'W.CONTRACT');

  // exit 2: nothing was judged
  const two = (n, args, input, re) => { const x = cli(args, input); check(n, x.code === 2 && (!re || re.test(x.err)) && !x.out.trim(), `${x.code} ${x.err.split('\n')[0]}`); };
  two('exit 2 without arguments, with the usage', [], undefined, /usage: node tools\/score\/check\.mjs/);
  two('exit 2 for a file that is not there', [path.join(tmp, 'nope.json')], undefined, /cannot read the score/);
  two('exit 2 for a score that is not JSON', [write('bad.json', '{ broken')], undefined, /is not valid JSON/);
  two('exit 2 for a base that is not there', [good, '--base', path.join(tmp, 'nope.json')], undefined, /cannot read the base score/);
  two('exit 2 for a base that is not JSON', [good, '--base', write('bad2.json', 'nope')], undefined, /is not valid JSON/);
  two('exit 2 for --stdin with nothing valid on it', ['--stdin'], 'not json', /standard input is not valid JSON/);
  two('exit 2 for --stdin and a file together', ['--stdin', good], '{}', /not both/);
  two('exit 2 for an unknown option', [good, '--nope'], undefined, /unknown option --nope/);
  two('exit 2 for --base without a file', [good, '--base'], undefined, /--base needs a file/);
  two('exit 2 for a contract that is not there', [good, '--contract', path.join(tmp, 'none.json')], undefined, /cannot read the contract/);
  two('exit 2 for two score files', [good, s3f], undefined, /only one score file/);
  r = cli(['--help']);
  check('--help prints the usage and exits 0', r.code === 0 && /usage:/.test(r.out));

  check('the CLI never writes: the live score has the same bytes (and the files it read, theirs)', (liveBefore === null || sha(LIVE) === liveBefore) && fs.readFileSync(good, 'utf8') === JSON.stringify(S2));
  fs.rmSync(tmp, { recursive: true, force: true });
}

console.log('\n' + (fails ? fails + ' FAILED' : 'all ok'));
process.exit(fails ? 1 : 0);
