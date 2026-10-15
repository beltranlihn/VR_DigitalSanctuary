// bind_unreal_test.mjs — "Bind to Unreal" (Edits.bindUnreal, lote 5 design A §3.1, §3.4-§3.6): the optional step after the upgrade to
// schema 3 that gives every moment its Unreal marks and every element its bind (action, target, asset). What it does to the score, what
// it promises (no time changes, nothing but marks and bind is added), what it refuses, the numbers of design A §3.4 recounted and the
// rules that read the result (Edits.validate, the server's invariants, Reach, Policy).
// It runs on the frozen fixture tools/score/fixtures/f0-score.json upgraded in memory (Edits.migrate3), with the frozen marks seed and a
// frozen cut of the idmap (so real changes of the piece or of Unreal's Content never break it); --live runs it on the live score, seed
// and idmap (the pinned numbers are skipped; a live score that is schema 2 is upgraded in memory, one already bound only checks the
// refusal). Nothing is written: every score here is a copy.
//   node tools/score/bind_unreal_test.mjs [--live]
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { testScore, ROOT } from './test_score.mjs';
const require = createRequire(import.meta.url);
const J = p => path.join(ROOT, 'web/editor-obra/app/js', p);
const E = require(J('engine.js')), X = require(J('edits.js')), I = require(J('integrity.js')), C = require(J('check.js')), P = require(J('partitura.js')), R = require(J('reach.js'));
const M = require(J('marks.js')), Media = require(J('media.js')), Pol = require(J('policy.js'));
const rd = p => JSON.parse(fs.readFileSync(path.join(ROOT, p), 'utf8'));
const clone = o => JSON.parse(JSON.stringify(o)), same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
const { score: base, live, name: SRC } = testScore();
console.log('on the ' + SRC);
const contract = rd('tools/score/fixtures/contract-f0.json'), roles = rd('obra/unreal/roles.json'), binding = rd('tools/score/fixtures/binding-f0.json');
const seed = rd(live ? 'obra/score/seed/marks-v1.json' : 'tools/score/fixtures/marks-seed-v1.json');
const idmap = rd(live ? 'obra/unreal/idmap.json' : 'tools/score/fixtures/idmap-20261008.json');
let fails = 0;
const check = (n, ok, info) => { console.log((ok ? '  ok   ' : '  FAIL ') + n + (info ? '  · ' + info : '')); if (!ok) fails++; };
const inputs0 = JSON.stringify([contract, roles, seed, idmap]);

// the schema 3 score to bind: a schema 2 one is upgraded here (the owner's other button), a schema 3 one is used as it is
let s3 = base;
if (base.schema === 2) {
  const m = X.migrate3(base, E, contract, { at: '2026-10-08T12:00:00.000Z', who: 'B' });
  if (!m.next) { console.log('the upgrade to schema 3 was refused: ' + m.report.refusals.map(r => r.msg).join(' | ')); process.exit(1); }
  s3 = m.next;
}
const typicalT = sc => E.resolve(sc, { persona: 'typical' });
const gov = P.governedBy(s3, typicalT(s3), binding);
const bind = (sc = s3, o = {}) => X.bindUnreal(sc, o.seed === undefined ? seed : o.seed, o.idmap === undefined ? idmap : o.idmap, o.contract === undefined ? contract : o.contract, o.roles === undefined ? roles : o.roles, Object.assign({ Engine: E, gov }, o.ctx));
const idOf = (sc, key, beatKey) => Object.keys(sc.elements).find(id => sc.elements[id].key === key && (!beatKey || sc.beats[sc.elements[id].beat].key === beatKey));
const beatOf = (sc, key) => Object.keys(sc.beats).find(b => sc.beats[b].key === key);
const stripped = sc => { const n = clone(sc); for (const b of Object.values(n.beats)) delete b.marks; for (const e of Object.values(n.elements)) delete e.bind; return n; };

if (X.bindState(s3) === 'bound') {
  console.log('the score is already bound: there is nothing to bind (it is checked on the frozen fixture)');
  const r = bind();
  check('a bound score is refused, with the reason, and nothing comes back to apply', !r.next && r.report.refusals.some(x => x.code === 'B3.BOUND' && /already bound/.test(x.msg)));
  console.log(fails ? `\n${fails} FAILED` : '\nall ok');
  process.exit(fails ? 1 : 0);
}

const before = JSON.stringify(s3);
let t = Date.now(); const r = bind(); const ms = Date.now() - t, n = r.next, rep = r.report;

console.log('what it makes');
check('the upgraded score binds: ok, no refusal, a score comes back', rep.ok && n && !rep.refusals.length, `${ms} ms`);
check('  pure: the score it was given, the seed, the idmap, the contract and the roles are exactly as they were', JSON.stringify(s3) === before && n !== s3 && n.elements !== s3.elements && n.beats !== s3.beats && JSON.stringify([contract, roles, seed, idmap]) === inputs0);
check('  the same schema 3 and rev; only marks and bind were added (take them away and it is byte for byte the score it came from)', n.schema === 3 && n.rev === s3.rev && JSON.stringify(stripped(n)) === before);
let ok = true; try { X.validate(n, E); } catch (e) { ok = false; console.log(e.message); }
check('  Edits.validate reads it, and the invariants the server applies pass against the score it came from', ok && C.invariants(n, s3, { Engine: E, Edits: X, contract }).ok);
check('  deterministic: the same inputs give the same score', same(bind().next, n));

console.log('no time changes (design A §3.6)');
{
  const ids = Object.keys(typicalT(s3).t), personas = Object.keys(E.PERSONAS), opts = [undefined, 'all', { share: 'yes' }, { share: 'no' }];
  let worst = 0, runs = 0, equal = true;
  for (const p of personas) for (const o of opts) {
    const a = E.resolve(s3, { persona: p, branch: o }), b = E.resolve(n, { persona: p, branch: o }); runs++;
    if (!same(a.t, b.t) || a.total !== b.total || !same(a.cycles, b.cycles) || !same(a.dangling, b.dangling)) equal = false;
    for (const id of Object.keys(a.t)) worst = Math.max(worst, Math.abs(a.t[id][0] - b.t[id][0]), Math.abs(a.t[id][1] - b.t[id][1]));
  }
  check(`${ids.length} elements and moments, the four simulated users, ${opts.length} views of the decision (${runs} runs): every start and end identical, the totals too`, equal && worst === 0, 'largest difference ' + worst);
  check('  the report says so: 0 items start elsewhere for every user, and the totals are the ones of the score', personas.every(p => rep.moved[p] === 0 && rep.totals[p] === E.resolve(s3, { persona: p }).total));
}

console.log('the marks (design A §2, §3.1)');
{
  const order = s3.acts.flatMap(a => a.beats), b = rep.beats;
  check('every moment the seed knows gets exactly its marks, in order, with the fields a mark has', order.every(id => { const sm = seed.beats[id]; return !sm || same(n.beats[id].marks, sm.marks.map(m => { const o = {}; for (const f of ['name', 'rel', 'el', 'elKey', 'edge', 'by', 'why', 'note']) if (m[f] != null) o[f] = m[f]; return o; })); }));
  const rel = {}, extra = [];
  for (const id of order) { const ms = n.beats[id].marks || []; if (ms.length) rel[ms[0].rel] = (rel[ms[0].rel] || 0) + 1; extra.push(...ms.slice(1).map(m => m.rel)); }
  check('the report counts them as the card says: on a mark = start + el, inside = in + sub, preview only', b.start === (rel.start || 0) && b.el === (rel.el || 0) && b.in === (rel.in || 0) && b.sub === (rel.sub || 0) && b.preview === (rel.preview || 0) && b.onMark === b.start + b.el && b.inside === b.in + b.sub && b.extra === extra.length && b.total === order.length);
  if (!live) check('  design A §3.4, recounted: 73 moments = 35 start + 4 el + 4 in + 27 sub + 3 preview, plus 3 extra `el` marks on elements of moments already counted (39 on a mark, 31 inside one, 3 preview)', b.total === 73 && b.start === 35 && b.el === 4 && b.in === 4 && b.sub === 27 && b.preview === 3 && b.extra === 3 && b.onMark === 39 && b.inside === 31 && b.placed === 42);
  const v1 = n.beats[beatOf(n, 'V1')].marks;
  check('the own relation is the first entry; V1 is the moment whose mark is its ENV_SWAP element (rel el, edge start, an element of that moment)', v1.length === 1 && v1[0].rel === 'el' && v1[0].name === 'S1.OPEN' && n.elements[v1[0].el].beat === beatOf(n, 'V1') && n.elements[v1[0].el].key === 'ENV_SWAP' && v1[0].edge === 'start');
  const r3 = n.beats[beatOf(n, '3.R3')].marks;
  check('3.R3 carries the open question of the owner (S2.BEGIN at CELL_IN) with its note: Bind does not decide it, the seed says "to review"', r3.length === 2 && r3[0].name === 'S2.INTRO' && r3[1].name === 'S2.BEGIN' && n.elements[r3[1].el].key === 'CELL_IN' && /to review/.test(r3[1].note));
  check('`in` and `sub` marks keep their knobs (by) and `preview` its reason (why)', (n.beats[beatOf(n, '1.2')].marks[0].by || []).includes('Titulo_RevelaIni') && /stage layers/.test(n.beats[beatOf(n, '1.R3')].marks[0].why) && n.beats[beatOf(n, '1.8')].marks[0].by.includes('FW_Bell'));
  const places = {};
  for (const id of order) for (const m of n.beats[id].marks || []) if ((m.rel === 'start' || m.rel === 'el') && M.isPhase(m.name)) places[m.name] = (places[m.name] || 0) + 1;
  check('a phase mark is placed once in the whole score (Unreal enters it once)', Object.values(places).every(c => c === 1), Object.keys(places).length + ' phase marks');
  check('the marks give the same places in the score as the seed did (Marks.scoreMarks reads the score now, not the seed): every time identical', (() => {
    const T = typicalT(n), a = M.scoreMarks(s3, typicalT(s3), seed), info = {}, c = M.scoreMarks(n, T, seed, info);
    return info.from === 'score' && same(a, c) && !info.issues.length;
  })());
}

console.log('the sounds and what each element is in Unreal (design A §3.4, recounted)');
{
  const E3 = n.elements, own = (o, k) => Object.prototype.hasOwnProperty.call(o || {}, k);
  let exact = 0, alias = 0, amb = 0, miss = 0, hap = 0, withSound = 0; const ids = { exact: new Set(), alias: new Set(), amb: new Set(), miss: new Set() };
  for (const e of Object.values(s3.elements)) {
    if (e.type === 'haptic') hap++;
    const sid = Media.soundId(e); if (!sid) continue;
    withSound++;
    const al = own(idmap.aliases, sid) ? idmap.aliases[sid] : null, nm = al || sid;
    if (own(idmap.ambiguous, nm)) { amb++; ids.amb.add(sid); } else if (own(idmap.assets, nm)) { if (al) { alias++; ids.alias.add(sid); } else { exact++; ids.exact.add(sid); } } else { miss++; ids.miss.add(sid); }
  }
  const S = rep.sounds;
  check('sounds by what became of them, counted again from the idmap: linked = exact + alias, ambiguous and missing apart', S.elements === withSound && S.exact === exact && S.alias === alias && S.linked === exact + alias && S.ambiguous.length === amb && S.missing === miss && S.haptics === hap, JSON.stringify({ withSound, exact, alias, amb, miss, hap }));
  check('  the same by distinct sound id', S.ids.total === new Set([...ids.exact, ...ids.alias, ...ids.amb, ...ids.miss]).size && S.ids.exact === ids.exact.size && S.ids.alias === ids.alias.size && S.ids.missing === ids.miss.size && same(S.ids.ambiguous, [...ids.amb].sort()));
  if (!live) {
    check('  design A §3.4: 99 exact + 29 alias = 128 elements linked, 1 ambiguous (VO_12c); 191 not in Unreal = 132 not in Content yet + 59 haptics (the design counted the haptics among the 320 "with a sound")', S.exact === 99 && S.alias === 29 && S.linked === 128 && S.ambiguous.length === 1 && S.ambiguous[0].key === 'VO_12c' && S.missing === 132 && S.haptics === 59 && S.missing + S.haptics === 191 && S.elements + S.haptics === 320, JSON.stringify(S).slice(0, 160));
    check('  design A §4.3 by distinct id: 76 exact + 19 alias + 1 ambiguous + 68 missing (63 + the 5 haptic ids) = 164', S.ids.exact === 76 && S.ids.alias === 19 && S.ids.ambiguous.length === 1 && S.ids.missing === 63 && S.ids.total + 5 === 164);
  }
  const bk = (k, b) => { const id = idOf(n, k, b); return id && E3[id].bind; };
  check('a bind has exactly action, target, asset and branch (null: reserved); an element with nothing to say has none (HAP_*)', Object.values(E3).every(e => !e.bind || same(Object.keys(e.bind), ['action', 'target', 'asset', 'branch']) && e.bind.branch === null) && !bk('HAP_PULSE_SOFT') && Object.values(E3).filter(e => e.type === 'haptic').every(e => !e.bind));
  check('a voice Alma says: vo_alma, role:Alma, its recording (VO_10); the four of the tracker stay in 2D (VO_33: vo_2d, no target)', same(bk('VO_10'), { action: 'vo_alma', target: 'role:Alma', asset: 'VO_10', branch: null }) && bk('VO_33').action === 'vo_2d' && bk('VO_33').target === null && bk('VO_33').asset === 'VO_33');
  check('what the contract says Unreal does not play gets no action but keeps its asset (VO_24 is vo.unused; its recording is the same)', same(bk('VO_24'), { action: null, target: null, asset: 'VO_24', branch: null }) && rep.elements.noUnreal === 13);
  check('the asset is the IDMAP name, not the sound id: FX_BELLRING → Bell, FX_CHARGE_1 → Charge1 (a rename in the score changes nothing of what Unreal plays); AMB_01 → Ambient_Clip_1_-_Intro in the role Ambiences', bk('FX_BELLRING').asset === 'Bell' && bk('FX_CHARGE_1').asset === 'Charge1' && bk('AMB_01').asset === 'Ambient_Clip_1_-_Intro' && bk('AMB_01').target === 'role:Ambiences' && bk('AMB_01').action === 'ambience');
  check('an asset two files answer to is never guessed (VO_12c: asset null, said in the report); a sound that is not in Content stays null; SILENCIO is an action, not an asset', bk('VO_12c').asset === null && bk('VO_12c').action === 'vo_alma' && bk('SILENCIO').asset === null && bk('SILENCIO').action === 'ambience');
  check('the placed sounds are sound_at (FX_SHAREAPPEAR…), the stage titles title, the veils veil, the waits wait; Alma comes and goes with appear and disappear on role:Alma', bk('FX_SHAREAPPEAR').action === 'sound_at' && bk('T_IN').action === 'title' && bk('VEIL_CLOSE').action === 'veil' && bk('G_BELL').action === 'wait' && bk('ALMA_IN').action === 'appear' && bk('ALMA_BACK').action === 'appear' && bk('ALMA_OUT').action === 'disappear' && bk('ALMA_GONE').action === 'disappear' && bk('ALMA_GONE').target === 'role:Alma');
  const wr = Object.keys(E3).filter(id => X.roleOf(roles, E3[id])), vo = Object.keys(E3).filter(id => E3[id].bind && E3[id].bind.action === 'vo_alma' && !X.roleOf(roles, E3[id]));
  check('the target is the role of roles.json the element belongs to (every one of them has it), and role:Alma for the voices she says', wr.every(id => E3[id].bind && E3[id].bind.target === 'role:' + X.roleOf(roles, E3[id])) && rep.elements.targets === wr.length + vo.length && bk('G_BELL').target === 'role:Bell' && bk('BELL_IN').target === 'role:Bell' && bk('BELL_IN').action === null, `${wr.length} by role + ${vo.length} Alma voices = ${rep.elements.targets}`);
  check('  every role named exists in roles.json (Reach would say "not in roles.json" otherwise)', Object.values(E3).every(e => !e.bind || !e.bind.target || e.bind.target === 'role:Alma' || own(roles.roles, e.bind.target.slice(5))));
  const byAction = {}; for (const e of Object.values(E3)) if (e.bind && e.bind.action) byAction[e.bind.action] = (byAction[e.bind.action] || 0) + 1;
  check('the report counts the actions as they are in the score', same(rep.elements.byAction, byAction) && rep.elements.bound === Object.values(E3).filter(e => e.bind).length && rep.elements.total === Object.keys(E3).length, JSON.stringify(byAction));
  if (!live) check('  pinned today (frozen fixture): 378 elements bound: 175 sound, 54 vo_alma, 3 vo_2d, 5 sound_at, 11 ambience, 10 wait, 10 title, 9 veil, 9 ghost, 11 appear, 10 disappear, and 71 with a target or an asset but no action', rep.elements.bound === 378 && rep.elements.noAction === 71 && same(byAction, { sound: 175, ambience: 11, vo_alma: 54, wait: 10, ghost: 9, appear: 11, disappear: 10, veil: 9, title: 10, vo_2d: 3, sound_at: 5 }));
  // ghost: the take is the DA_Ghost_<Name> of Content
  const withGhost = clone(idmap); withGhost.assets.DA_Ghost_Bell = { path: '/Game/SoulCharger/Shared/Ghost/Data/DA_Ghost_Bell.DA_Ghost_Bell', cls: 'GhostTake', referencedBy: [] };
  const g = bind(s3, { idmap: withGhost }).next, gid = idOf(g, 'GHOST_BELL');
  check('a ghost instruction finds its take by name (GHOST_BELL → DA_Ghost_Bell) when Content has it, and has none when it does not', g.elements[gid].bind.action === 'ghost' && g.elements[gid].bind.asset === 'DA_Ghost_Bell' && (live ? bk('GHOST_BELL').asset === (own(idmap.assets, 'DA_Ghost_Bell') ? 'DA_Ghost_Bell' : null) : bk('GHOST_BELL').asset === null));
}

console.log('where every element stands now (Reach, design A §3.3) — and what differs from the 12 of the design');
{
  const cx = (sc, T) => R.context({ score: sc, schedT: T, contract, gov, idmap, seed, roles, resolve: p => E.resolve(sc, { persona: p }) });
  const a0 = R.all(cx(s3, typicalT(s3))), a1 = R.all(cx(n, typicalT(n))), c0 = a0.counts, c1 = a1.counts;
  check('the report carries the counts before and after, as Reach gives them', same(rep.reach.before, c0) && same(rep.reach.after, c1));
  check('every element has one answer; knob and the rest of the contract do not move (Bind adds no knowledge about timing)', c1.knob === c0.knob && c1.knob + c1.wired + c1.cue + c1.preview === Object.keys(n.elements).length);
  check('before: a schema 3 score not bound reads like schema 2 (projection): none cue-ready, the ones that could be are counted apart (bindable)', c0.cue === 0 && a0.marksFrom === 'seed' && a1.marksFrom === 'score' && c1.bindable === 0);
  const cues = Object.keys(n.elements).filter(id => a1.of[id].reach === 'cue');
  check('the cues in the report are the ones Reach finds, by time, each {mark, offset, action, target, asset, path, state}', same(rep.reach.cues.map(c => c.id), cues.sort((x, y) => typicalT(n).t[x][0] - typicalT(n).t[y][0] || (x < y ? -1 : 1))) && rep.reach.cues.every(c => c.state === 'no-player' && c.mark && typeof c.offset === 'number'));
  const moves = rep.reach.cues.filter(c => c.action === 'appear' || c.action === 'disappear'), sounds = rep.reach.cues.filter(c => !(c.action === 'appear' || c.action === 'disappear'));
  if (!live) {
    check('cue-ready after binding: 18 = the 12 sounds the design predicted (FX_GHOSTAPPEAR ×6, FX_SOULDETACH ×5, FX_SOULJOIN) + 6 of Alma\'s appear / disappear that the design\'s projection did not look for', c1.cue === 18 && sounds.length === 12 && moves.length === 6
      && same(sounds.map(c => c.key + '@' + c.mark + '+' + c.offset).sort(), ['FX_GHOSTAPPEAR@S0.INTRO+0', 'FX_GHOSTAPPEAR@S1.INTRO+0', 'FX_GHOSTAPPEAR@S3.BEGIN+75', 'FX_GHOSTAPPEAR@S3.INTRO+0', 'FX_GHOSTAPPEAR@S4.BEGIN+60', 'FX_GHOSTAPPEAR@S4.INTRO+0', 'FX_SOULDETACH@S0.CHARGE+0', 'FX_SOULDETACH@S1.CHARGE+0', 'FX_SOULDETACH@S2.CHARGE+0', 'FX_SOULDETACH@S3.CHARGE+0', 'FX_SOULDETACH@S4.CHARGE+0', 'FX_SOULJOIN@FINAL.CREDITS+7.5'].sort()), JSON.stringify(c1));
    check('  the 6 moves are role:Alma verbs at the start of a mark: ALMA_GONE at S0..S3.OUTRO and FINAL.EXIT, ALMA_BACK at FINAL.RESULTS — BP_Obra_SC does these itself (tracker), nothing in the editor can tell; the card says so', same(moves.map(c => c.key + '@' + c.mark).sort(), ['ALMA_BACK@FINAL.RESULTS', 'ALMA_GONE@FINAL.EXIT', 'ALMA_GONE@S0.OUTRO', 'ALMA_GONE@S1.OUTRO', 'ALMA_GONE@S2.OUTRO', 'ALMA_GONE@S3.OUTRO']) && moves.every(c => c.target === 'role:Alma' && c.asset === null && c.offset === 0));
    const wiredNew = Object.keys(n.elements).filter(id => a1.of[id].reach === 'wired' && a0.of[id].reach !== 'wired').map(id => n.elements[id].key).sort();
    check('  9 more are wired: a bound element whose asset Unreal already calls (it would play twice); 5 of them only because the references of a plugin asset are not read', c1.wired === c0.wired + 9 && same(wiredNew, ['FX_CHARGE_1', 'FX_CHARGE_2', 'FX_CHARGE_3', 'FX_CHARGE_4', 'FX_CHARGEFINAL', 'FX_DISCLAIMER', 'FX_DOOROPEN', 'FX_SOULSWIM', 'FX_WALK'].sort()) && c1.unsure === 5, wiredNew.join(', '));
    check('  69 reach Unreal (timing) · 80 wired · 18 cue-ready · 425 preview (the status bar), against 69 · 71 · 0 · 452 before', R.statusText(a1) === '69 reach Unreal (timing) · 80 wired · 18 cue-ready · 425 preview' && c0.preview === 452 && c1.preview === 425);
  }
  const moved = Object.keys(n.elements).filter(id => a0.of[id].reach !== a1.of[id].reach && a1.of[id].reach !== 'cue' && a1.of[id].reach !== 'wired');
  check('nothing else changes its answer: an element becomes cue-ready or wired, never knob, never back to preview from somewhere else', moved.length === 0);
  check('the elements of a bound score read their asset from the bind: a renamed sound keeps what Unreal plays (renameEl keeps the bind)', (() => {
    const q = clone(n), id = idOf(q, 'FX_BELLRING'); X.renameEl(q.elements[id], 'FX_BELL_RENAMED');
    return same(q.elements[id].bind, n.elements[id].bind) && q.elements[id].key === 'FX_BELL_RENAMED';
  })());
}

console.log('what it refuses (each with its reason, nothing to apply)');
{
  const refuses = (name, r, code, re) => check(name, !r.next && !r.report.ok && r.report.refusals.some(x => x.code === code && (!re || re.test(x.msg))), (r.report.refusals[0] || {}).msg);
  refuses('a schema 2 score: upgrade it first', bind(base.schema === 2 ? base : (() => { const q = clone(n); q.schema = 2; return q; })()), 'B3.SCHEMA', /Upgrade the score to schema 3 first/);
  refuses('a score that is already bound: once is enough (the menu is greyed with "Already bound")', bind(n), 'B3.BOUND', /already bound/);
  refuses('without the marks seed', bind(s3, { seed: null }), 'B3.SEED', /marks-v1\.json/);
  refuses('without the scan of Unreal\'s assets', bind(s3, { idmap: null }), 'B3.IDMAP', /idmap\.json/);
  refuses('without the contract', bind(s3, { contract: null }), 'B3.CONTRACT', /contract\.json/);
  refuses('without the roles', bind(s3, { roles: {} }), 'B3.ROLES', /roles\.json/);
  refuses('a score that is not valid', bind((() => { const q = clone(s3); q.elements[Object.keys(q.elements)[0]].at = { ref: 'el_gone', edge: 'end', off: 0 }; return q; })()), 'B3.STRUCT', /not valid/);
  { // a seed whose element belongs to another moment: Bind does not write a mark validate would refuse
    const sd = clone(seed), b = beatOf(s3, '3.R3'), other = Object.keys(s3.elements).find(id => s3.elements[id].beat !== b);
    sd.beats[b].marks[1].el = other;
    refuses('a seed that points a mark at an element of another moment', bind(s3, { seed: sd }), 'B3.STRUCT', /not in this moment/);
  }
  { // binding must not change a time: an engine that moves one (a stand-in for a bug) is caught and nothing is returned
    const bad = { PERSONAS: E.PERSONAS, resolve: (sc, o) => { const res = E.resolve(sc, o); if (Object.values(sc.beats).some(b => b.marks)) { const id = Object.keys(res.t)[5]; res.t[id] = [res.t[id][0] + .5, res.t[id][1] + .5]; } return res; } };
    refuses('a time that would move (an engine that moves one is a stand-in for a bug)', bind(s3, { ctx: { Engine: bad } }), 'B3.MOVED', /must not change a time/);
  }
  check('  and a refusal leaves the score and every input as they were', JSON.stringify(s3) === before && JSON.stringify([contract, roles, seed, idmap]) === inputs0);
}

console.log('the edges: a moment the seed does not know, a seed with more, an element made in the editor');
{
  const sd = clone(seed), b = beatOf(s3, '1.4'); delete sd.beats[b]; sd.beats.bt_nowhere = { key: '9.9', marks: [{ name: 'S0.OPEN', rel: 'start' }] };
  const r2 = bind(s3, { seed: sd });
  check('a moment the seed does not know stays without marks (and is listed); a moment of the seed that is not in the score is ignored, with a note', r2.next && !r2.next.beats[b].marks && same(r2.report.beats.unmarked, ['1.4']) && r2.report.beats.marked === r2.report.beats.total - 1 && r2.report.notes.some(t => /9\.9/.test(t) && /ignored/.test(t)));
  check('  such a moment has no mark, so its elements are preview with "no Unreal mark yet" — and still nothing moved', r2.report.moved.typical === 0 && (() => { const a = R.all(R.context({ score: r2.next, schedT: typicalT(r2.next), contract, gov, idmap, seed, roles, resolve: p => E.resolve(r2.next, { persona: p }) })); const e = Object.keys(r2.next.elements).find(id => r2.next.elements[id].beat === b && a.of[id].reach === 'preview'); return !!e; })());
  const q = clone(s3), nid = 'el_madehere'; q.elements[nid] = Object.assign(clone(q.elements[idOf(q, 'FX_BELLRING')]), { key: 'FX_MINE', label: 'FX_MINE', sound: 'FX_MINE', isNew: true, legacy: null });
  const r3 = bind(q);
  check('an element made in the editor (isNew) is left alone: Unreal does not have it; the report says how many', r3.next && !r3.next.elements[nid].bind && r3.report.elements.fresh === 1 && r3.report.notes.some(t => /made in the editor/.test(t)));
  const pend = bind(s3, { seed: Object.assign(clone(seed), { status: 'reviewed by the owner 2026-10-09' }) }).report.seed;
  check('the seed still "proposed, pending owner review" says so (the card too); once its status says it was reviewed, it does not', rep.seed.pending === true && /pending owner review/.test(rep.seed.status) && rep.seed.review === 4 && pend.pending === false);
}

console.log('the rules that read marks and bind (Edits.validate, shared by the editor, the server and compile)');
{
  const bad = (name, fn, re, schema) => {
    const q = clone(n); fn(q); if (schema) q.schema = schema;
    let msg = null; try { X.validate(q, E); } catch (e) { msg = e.message; }
    const ck = C.invariants(q, n, { Engine: E, Edits: X, contract });
    check(`${name}: refused (${msg ? msg.slice(0, 70) : 'NOT refused'})`, !!msg && re.test(msg) && !ck.ok && ck.errors.some(x => x.code === (schema === 2 ? 'S.STRUCT' : 'S.BIND.FIELD')), ck.errors.map(x => x.code).join());
  };
  const b1 = beatOf(n, '1.4'), b2 = beatOf(n, '1.5'), bV = beatOf(n, 'V2'), any = id => n.elements[id];
  const elIn = b => Object.keys(n.elements).find(id => n.elements[id].beat === b);
  bad('marks that is not a list', q => { q.beats[b1].marks = { name: 'S0.OPEN' }; }, /marks is not a list/);
  bad('a mark Unreal does not emit', q => { q.beats[b1].marks[0].name = 'S9.OPEN'; }, /not a mark Unreal emits/);
  bad('S4.BYE (the last stage has no farewell)', q => { q.beats[b1].marks[0].name = 'S4.BYE'; }, /not a mark Unreal emits/);
  bad('a relation that is not start, el, in, sub or preview', q => { q.beats[b1].marks[0].rel = 'around'; }, /relation "around"/);
  bad('an `el` mark on an element of another moment', q => { q.beats[bV].marks[0].el = elIn(b1); }, /not in this moment/);
  bad('an `el` mark with no edge', q => { delete q.beats[bV].marks[0].edge; }, /no edge/);
  bad('two relations of its own in one moment', q => { q.beats[b1].marks.push({ name: 'S0.OPEN', rel: 'preview' }); }, /one entry, the first/);
  bad('the own relation after an `el` mark', q => { q.beats[beatOf(n, '3.R3')].marks.reverse(); }, /one entry, the first/);
  bad('a phase mark placed twice (Unreal enters it once)', q => { q.beats[b1].marks = [{ name: 'S0.OPEN', rel: 'start' }]; }, /S0\.OPEN is placed twice/);
  bad('the knobs of a mark that are not a list', q => { q.beats[b1].marks[0].by = 'FW_Bell'; }, /list of names/);
  bad('a bind that is not an object', q => { q.elements[idOf(q, 'VO_10')].bind = 'vo_alma'; }, /bind is not an object/);
  bad('an action that is not in the catalog', q => { q.elements[idOf(q, 'VO_10')].bind.action = 'shout'; }, /"shout" is not an action/);
  bad('a target without role: or tag:', q => { q.elements[idOf(q, 'VO_10')].bind.target = 'Alma'; }, /role:<name> or tag:<name>/);
  bad('an asset that is not a name', q => { q.elements[idOf(q, 'VO_10')].bind.asset = ''; }, /name of an Unreal asset/);
  bad('bind.branch (reserved: the side of a decision is the element\'s own `branch`)', q => { q.elements[idOf(q, 'VO_10')].bind.branch = { on: 'share', value: 'yes' }; }, /reserved/);
  bad('marks in a schema 2 score (they belong to schema 3)', q => { delete q.branches; delete q.baseline; delete q.uidMap; for (const e of Object.values(q.elements)) { delete e.branch; delete e.alt; delete e.bind; if (e.gate) delete e.gate.blocking; } for (const b of Object.values(q.beats)) delete b.alt; }, /can't have marks/, 2);
  check('  a mark placed by `in`, `sub` or `preview` may name a phase another moment places (HALL.START ×3, S0.ALMA ×2, the Hall steps): the seed does it and validates', (() => { try { X.validate(n, E); return n.beats[beatOf(n, '1.2')].marks[0].name === 'HALL.START' && n.beats[beatOf(n, '1.1')].marks[0].name === 'HALL.START'; } catch (e) { return false; } })());
  check('  the vocabulary is the one of js/marks.js and the catalog the one of Reach (no drift between the three places)', !X.MARK_RELS.some(r => !['start', 'el', 'in', 'sub', 'preview'].includes(r)) && same([...X.BIND_ACTIONS].sort(), Object.keys(R.ACTION_WORD).sort()) && [...R.CUE_ACTIONS].every(a => X.BIND_ACTIONS.includes(a)));
}

console.log('the edit around it (Policy, copies, undo)');
{
  check('Policy: op "bind" is quiet like "migrate" (its own card is the decision) — no impact card on top, and nothing for it to ask because no time moves', Pol.QUIET.has('bind') && Pol.QUIET.has('migrate') && Pol.decide({ type: 'bind', ids: [] }, [], { label: 'Bind to Unreal' }).mode === 'quiet');
  const eff = I.effect(s3, n, E);
  check('  Integrity.effect on the pair: 0 changed, 0 shifted, 0 added, 0 removed (what commit() judges the edit by)', !eff.changed.length && !(eff.shifted || []).length && !(eff.added || []).length && !(eff.removed || []).length, JSON.stringify(Object.fromEntries(Object.entries(eff).filter(([, v]) => Array.isArray(v)).map(([k, v]) => [k, v.length]))));
  const kc = { knob: () => undefined }, items = I.opItems({ type: 'bind', ids: [], prevScore: s3 }, n, { problems: I.staticProblems(s3, typicalT(s3), contract, E.altRuns(s3), kc) }, { problems: I.staticProblems(n, typicalT(n), contract, E.altRuns(n), kc) }, contract, E, { gov });
  check('  opItems for it: nothing to review', items.items.filter(i => i.sv !== 'info').length === 0);
  check('undo is exact: the snapshot before is the score before, byte for byte; redo (the same call on it) gives the same bound score', JSON.stringify(JSON.parse(before)) === JSON.stringify(s3) && same(bind(JSON.parse(before)).next, n));
  // a copy made in the editor does not carry the bind of the original
  const bellId = idOf(n, 'FX_BELLRING'); let seq = 0;
  const addLane = (nn, gid) => { const g = nn.groups.find(x => x.id === gid); let i = g.lanes.length + 1, id; do { id = 'ln_' + gid + '_' + (i++); } while (nn.lanes[id]); nn.lanes[id] = { name: g.name + ' ' + i, group: gid }; g.lanes.push(id); return id; };
  const pl = X.planPaste(n, X.clipOf(n, [bellId], E), { dt: 1 }, E, { who: 'B', at: '2026-10-08T00:00:00Z', now: () => 1e12, rand: () => ((seq++ * 7) % 36) / 36, addLane });
  check('a copy (Ctrl+C / Ctrl+D) is a new element Unreal does not have: isNew, no bind; the original keeps its own', pl.ok && pl.next.elements[pl.ids[0]].isNew === true && !('bind' in pl.next.elements[pl.ids[0]]) && same(pl.next.elements[bellId].bind, n.elements[bellId].bind));
  check('  the score with the copy still validates and passes the invariants', (() => { try { X.validate(pl.next, E); return C.invariants(pl.next, n, { Engine: E, Edits: X, contract }).ok; } catch (e) { return false; } })());
}

console.log('deleting what an Unreal mark hangs on (review: the bound score must stay saveable)');
{
  // an `el` mark is the edge of one clip of its moment. Delete the clip and the mark has nothing to hang on: Edits.validate (and the server)
  // would refuse the save, with no word before. The clip takes its mark with it, in the same edit, and the delete says so.
  const elMarks = [];
  for (const b of Object.keys(n.beats)) for (const mk of n.beats[b].marks || []) if (mk.rel === 'el') elMarks.push({ b, mk, el: mk.el, key: n.elements[mk.el].key });
  const valid = sc => { try { X.validate(sc, E); return true; } catch (e) { return false; } };
  const holds = (sc, from) => valid(sc) && C.invariants(sc, from, { Engine: E, Edits: X, contract }).ok;
  check('the bound fixture has the el marks the design lists: ENV_SWAP x4 (S1..S4.OPEN), CELL_IN (S2.BEGIN), FINAL (FINAL.DARK), NEGRO_FIN (FINAL.FADE)', live || (elMarks.length === 7 && same(elMarks.map(m => m.key + '@' + m.mk.name).sort(), ['CELL_IN@S2.BEGIN', 'ENV_SWAP@S1.OPEN', 'ENV_SWAP@S2.OPEN', 'ENV_SWAP@S3.OPEN', 'ENV_SWAP@S4.OPEN', 'FINAL@FINAL.DARK', 'NEGRO_FIN@FINAL.FADE'])), elMarks.length + ' el marks');
  check('  without the repair, deleting the clip leaves a score validate refuses ("... is the edge of an element that is not in this moment"): the bug this section pins', elMarks.every(m => { const q = clone(n); delete q.elements[m.el]; let msg = ''; try { X.validate(q, E); } catch (e) { msg = e.message; } return /not in this moment|points to something that does not exist/.test(msg); }));
  if (!elMarks.length) { console.log('  (the live score has no el mark: the rest of this section needs one)'); }
  else {
  // marksOf / marksLost / marksWords
  const first = elMarks[0], one = X.marksOf(n, [first.el]);
  check('marksOf names the mark a delete would cost: moment, name, clip, edge', one.length === 1 && one[0].beat === first.b && one[0].name === first.mk.name && one[0].el === first.el && one[0].key === first.key && one[0].edge === first.mk.edge && one[0].moment === n.beats[first.b].key);
  check('  nothing for a clip with no mark, for a score that is not bound (schema 3 not bound, schema 2); all of them for all the marked clips', !X.marksOf(n, [idOf(n, 'VO_10')]).length && !X.marksOf(s3, [first.el]).length && !X.marksOf(base, [first.el]).length && X.marksOf(n, elMarks.map(m => m.el)).length === elMarks.length);
  check('  marksWords: one sentence for one mark (it loses its Unreal mark), one for several (counted and named, three at most), none for nothing', X.marksWords(one) === `${first.mk.name} (moment ${n.beats[first.b].key}) loses its Unreal mark` && (elMarks.length < 4 || new RegExp('^' + elMarks.length + ' Unreal marks are lost: .*, …$').test(X.marksWords(X.marksOf(n, elMarks.map(m => m.el))))) && X.marksWords([]) === '' && X.marksWords(null) === '');
  // settleMarks: the repair commit() applies after every edit
  const results = elMarks.map(m => {
    const q = clone(n); delete q.elements[m.el];
    const lostList = X.marksLost(n, q), dropped = X.settleMarks(q, n);
    X.reconcileUidMap(n, q);   // commit() does this too: the deleted name stays in the uidMap as deleted-here
    return { m, q, lostList, dropped, hangs: !!X.planDelete(n, [m.el], E) };
  });
  check('settleMarks drops exactly the mark of the deleted clip (and reports it); marksLost says the same before it runs; the moment\'s other marks stay as they were', results.every(({ m, q, lostList, dropped }) => lostList.length === 1 && dropped.length === 1 && dropped[0].name === m.mk.name && dropped[0].key === m.key && same(lostList, dropped)
    && !(q.beats[m.b].marks || []).some(x => x.rel === 'el' && x.el === m.el) && same((n.beats[m.b].marks || []).filter(x => x.el !== m.el), q.beats[m.b].marks || [])));
  check('  and, for a clip nothing hangs from (a plain delete: ENV_SWAP), the score validates and passes the invariants the server applies, against the score it came from', results.filter(r => !r.hangs).length > 0 && results.filter(r => !r.hangs).every(({ q }) => holds(q, n)), results.filter(r => !r.hangs).length + ' clips');
  check('  a moment left with no mark loses the field; a moment with its own relation keeps it (3.R3 keeps S2.INTRO when CELL_IN goes)', results.every(({ m, q }) => { const rest = (n.beats[m.b].marks || []).filter(x => x.el !== m.el); return rest.length ? q.beats[m.b].marks.length === rest.length : !('marks' in q.beats[m.b]); })
    && (live || (() => { const r3 = results.find(r => r.m.key === 'CELL_IN'); return r3.q.beats[r3.m.b].marks.length === 1 && r3.q.beats[r3.m.b].marks[0].name === 'S2.INTRO'; })()));
  check('  idempotent; a no-op on a score with nothing hanging, on one not bound, on a schema 2 one, and on nothing', (() => { const q = results[0].q, a = JSON.stringify(q); X.settleMarks(q, n); const w = clone(n), w2 = clone(s3), w3 = clone(base); return JSON.stringify(q) === a && !X.settleMarks(w, n).length && same(w, n) && !X.settleMarks(w2).length && same(w2, s3) && !X.settleMarks(w3).length && same(w3, base) && !X.settleMarks(null).length; })());
  // bindError: the guard commit() uses so that no edit can take a bound score from saveable to unsaveable unnoticed
  check('bindError: null for a good bound score and for one not bound or in schema 2; the sentence validate throws for a dangling mark', X.bindError(n) === null && X.bindError(s3) === null && X.bindError(base) === null && X.bindError(null) === null
    && /is the edge of an element that is not in this moment/.test(X.bindError((() => { const q = clone(n); delete q.elements[first.el]; return q; })())));
  // planDelete: the plans (both repairs) are scores that validate, and say what the mark costs
  const up = new Set(elMarks.map(m => m.el));
  for (const st = [...up]; st.length;) { const x = st.pop(), e = n.elements[x]; for (const a of [e.at, e.end]) if (a && a.ref && n.elements[a.ref] && !up.has(a.ref)) { up.add(a.ref); st.push(a.ref); } }
  const plans = [...up].map(id => ({ id, plan: X.planDelete(n, [id], E) })).filter(x => x.plan);
  const marked = new Set(elMarks.map(m => m.el));
  check(`planDelete on the clips an el mark hangs on, and on what they hang from (${up.size} clips, ${plans.length} with something hanging): every plan (re-anchor and delete-the-family) is a score that validates and passes the invariants`, plans.length > 0 && plans.every(({ plan }) => holds(plan.reanchor.next, n) && holds(plan.family.next, n)), `${up.size} clips, ${plans.length} plans`);
  check('  each plan names the marks it costs: the clip\'s own in the re-anchor; in the family the marked clips among everything that goes; none when no marked clip goes', plans.every(({ id, plan }) => same(plan.reanchor.marks.map(m => m.el).sort(), marked.has(id) ? [id] : []) && plan.family.marks.length === elMarks.filter(m => plan.family.ids.includes(m.el)).length && plan.family.marks.every(m => plan.family.ids.includes(m.el))));
  check('  the family of a clip can hold more than one marked clip, and then each of their marks is listed', plans.some(({ plan }) => plan.family.marks.length > plan.reanchor.marks.length) || live, plans.map(p => p.plan.family.marks.length).join());
  const cell = idOf(n, 'CELL_IN'), pc = cell && X.planDelete(n, [cell], E);
  check('  CELL_IN (S2.BEGIN of 3.R3) has things hanging from it: the card can say "S2.BEGIN (moment 3.R3) loses its Unreal mark"', live || (pc && X.marksWords(pc.reanchor.marks) === 'S2.BEGIN (moment 3.R3) loses its Unreal mark'));
  // a plain delete of a marked clip alongside others (what Act.remove does when nothing hangs): the net settles it too
  const plain = elMarks.find(m => !X.planDelete(n, [m.el], E));
  const alongside = (() => { const q = clone(n); delete q.elements[plain.el]; X.reconcileUidMap(n, q); X.settleMarks(q, n); return q; })();
  check('  a plain delete of a marked clip nothing hangs from (Act.remove with no plan): the net commit() applies after the verb (uidMap + marks) leaves a saveable score', !!plain && holds(alongside, n));
  // the copy of a marked clip is not a marked clip (Ctrl+D / Ctrl+C): an `el` mark names the original only
  let seq2 = 0;
  const addLane2 = (nn, gid) => { const g = nn.groups.find(x => x.id === gid); let i = g.lanes.length + 1, id; do { id = 'ln_' + gid + '_' + (i++); } while (nn.lanes[id]); nn.lanes[id] = { name: g.name + ' ' + i, group: gid }; g.lanes.push(id); return id; };
  const pd = X.planPaste(n, X.clipOf(n, [first.el], E), { after: true }, E, { who: 'B', at: '2026-10-08T00:00:00Z', now: () => 1e12, rand: () => ((seq2++ * 11) % 36) / 36, addLane: addLane2 });
  check('  duplicating a marked clip leaves the mark on the original; deleting the COPY costs no mark, deleting the original still costs it', pd.ok && !X.marksOf(pd.next, [pd.ids[0]]).length && X.marksOf(pd.next, [first.el]).length === 1 && holds((() => { const q = clone(pd.next); delete q.elements[pd.ids[0]]; X.settleMarks(q, pd.next); return q; })(), pd.next));
  }
}

console.log('a seed that marks nothing is not a bind (review)');
{
  const keep = (name, sd, code) => {
    const r = bind(s3, { seed: sd });
    check(name, !r.next && !r.report.ok && r.report.refusals.some(x => x.code === code && /mark none of the moments/.test(x.msg)), (r.report.refusals[0] || {}).msg);
  };
  keep('a seed with no moments: refused (B3.SEED), nothing to apply -- not a "bound" score with no marks that can never be completed', Object.assign(clone(seed), { beats: {} }), 'B3.SEED');
  keep('a seed whose moments are all other ones (made for another piece): the same refusal', Object.assign(clone(seed), { beats: { bt_nowhere: { key: '9.9', marks: [{ name: 'S0.OPEN', rel: 'start' }] } } }), 'B3.SEED');
  keep('a seed whose moments have an empty list of marks: the same refusal', (() => { const sd = clone(seed); for (const k of Object.keys(sd.beats)) sd.beats[k].marks = []; return sd; })(), 'B3.SEED');
  const b14 = beatOf(s3, '1.4'), b12 = beatOf(s3, '1.2');
  const stay = bind(s3, { seed: Object.assign(clone(seed), { beats: { [b14]: { key: '1.4', marks: seed.beats[b14].marks } } }) });
  check('a seed with a few moments still binds (the others are listed as without a mark, in the card): that is a partial seed, not an empty one', stay.next && stay.report.beats.marked === 1 && stay.report.beats.unmarked.length === stay.report.beats.total - 1);
  const noPhase = bind(s3, { seed: Object.assign(clone(seed), { beats: { [b12]: { key: '1.2', marks: [{ name: 'HALL.START', rel: 'in' }] } } }) });
  check('  one that places no phase of Unreal\'s director (only `in` / `sub` / `preview`) binds and says so in a note; the real seed has no such note', noPhase.next && noPhase.report.notes.some(t => /places a phase/.test(t)) && !rep.notes.some(t => /places a phase/.test(t)));
  check('  and after a refusal the score and every input are as they were', JSON.stringify(s3) === before && JSON.stringify([contract, roles, seed, idmap]) === inputs0);
}

console.log('the import card names the binding it would take away (review)');
{
  const unb = clone(s3), bnd = clone(n);
  const w = (cur, file) => X.importWords(X.importDiff(cur, file));
  check('a bound score imported over by a file that is not bound: the card says the binding goes (with the way back)', X.importDiff(bnd, unb).unbound === true && /bound to Unreal.*the binding goes with it.*Ctrl\+Z/.test(w(bnd, unb).unbound));
  check('  nothing to say when the file is bound too, when the score was not bound, or for the same score', w(bnd, bnd).unbound === '' && w(unb, bnd).unbound === '' && w(unb, unb).unbound === '' && w(bnd, clone(bnd)).unbound === '' && X.importDiff(base, unb).unbound === false);
}

console.log('the cost');
{
  const t0 = Date.now(); bind(); const ms2 = Date.now() - t0;
  check('well under a second for the whole piece, with the four simulated users and the reach counted twice (< 1000 ms)', ms2 < 1000, ms2 + ' ms');
}

console.log(fails ? `\n${fails} FAILED` : '\nall ok');
process.exit(fails ? 1 : 0);
