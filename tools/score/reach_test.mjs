// reach_test.mjs — where each element of the score stands with Unreal (lote 5 design A §3.3): knob / wired / cue-ready / preview.
// Logic: web/editor-obra/app/js/reach.js. On the frozen fixture (tools/score/fixtures/f0-score.json) with the frozen marks seed and a
// frozen cut of the idmap it pins today's counts and explains how they differ from the design's 70 / 82 / 428 (the 12 voices
// the trackers say Unreal does not play). Schema 3 (bound) is tried on copies made here; nothing is written.
//   node tools/score/reach_test.mjs [--live]     (--live: the live score, seed and idmap; the pinned numbers are skipped)
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { testScore, schema3Copy, ROOT } from './test_score.mjs';
const require = createRequire(import.meta.url);
const J = p => path.join(ROOT, 'web/editor-obra/app/js', p);
const E = require(J('engine.js')), P = require(J('partitura.js')), R = require(J('reach.js')), I = require(J('integrity.js'));
const rd = p => JSON.parse(fs.readFileSync(path.join(ROOT, p), 'utf8'));
const clone = o => JSON.parse(JSON.stringify(o)), same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
const { score, live, name: SRC } = testScore();
console.log('on the ' + SRC);
const contract = rd('tools/score/fixtures/contract-f0.json'), binding = rd('tools/score/fixtures/binding-f0.json'), roles = rd('obra/unreal/roles.json');
const seed = rd(live ? 'obra/score/seed/marks-v1.json' : 'tools/score/fixtures/marks-seed-v1.json');
const idmap = rd(live ? 'obra/unreal/idmap.json' : 'tools/score/fixtures/idmap-20261008.json');
let fails = 0;
const check = (n, ok, info) => { console.log((ok ? '  ok   ' : '  FAIL ') + n + (info ? '  · ' + info : '')); if (!ok) fails++; };
const before = JSON.stringify(score) + JSON.stringify(contract) + JSON.stringify(idmap) + JSON.stringify(seed);

/* a context for a score, with every input spelled out so a test can change one */
function ctxOf(sc, o = {}) {
  const schedT = o.schedT || E.resolve(sc, { persona: 'typical' }), bd = o.binding || binding;
  return R.context({ score: sc, schedT, contract: o.contract || contract, gov: o.gov || P.governedBy(sc, schedT, bd), idmap: o.idmap === undefined ? idmap : o.idmap,
    seed: o.seed || seed, roles, resolve: p => E.resolve(sc, { persona: p }), player: !!o.player });
}
const idOf = (sc, key, beatKey) => Object.keys(sc.elements).find(id => sc.elements[id].key === key && (!beatKey || sc.beats[sc.elements[id].beat].key === beatKey));
const idsOfKey = (sc, key) => Object.keys(sc.elements).filter(id => sc.elements[id].key === key);
/* "Bind to Unreal", as the tests need it (the real operation is a separate chunk): the seed's marks into the moments, and a bind on the
   elements asked for. A schema 3 copy of the score; the argument is never changed */
function bound(sc, binds = {}) {
  const s = schema3Copy(sc);
  for (const b of Object.keys(s.beats)) if (seed.beats[b]) s.beats[b].marks = clone(seed.beats[b].marks);
  for (const [id, bd] of Object.entries(binds)) s.elements[id].bind = bd;
  return s;
}

const ctx = ctxOf(score), all = R.all(ctx), res = id => all.of[id];
const C = all.counts, N = Object.keys(score.elements).length;

console.log('the rules, in the order of the design');
{
  // 1 · made in the editor
  const sc = clone(score), src = idOf(sc, 'T_IN'); sc.elements.el_new = Object.assign(clone(sc.elements[src]), { isNew: true, key: 'T_NEW' });
  const r = R.of('el_new', ctxOf(sc));
  check('1 · made in the editor → preview, whatever it copies (it copies T_IN, a knob)', r.reach === 'preview' && /Made in the editor/.test(r.why));
  // 2 · contract: not in Unreal
  const unused = idOf(score, 'VO_01d'), r2 = res(unused);
  check('2 · a contract entry "not in Unreal" → preview, with its message (msg) and owner', r2.reach === 'preview' && r2.contract === 'vo.unused' && /no longer plays this voice/.test(r2.msg) && /^Not in Unreal/.test(r2.why) && !!r2.owner, r2.contract);
  const hap = Object.keys(score.elements).find(id => score.elements[id].type === 'haptic');
  check('...haptics are not in Unreal (the contract says so)', res(hap).reach === 'preview' && /[Hh]aptic/.test(res(hap).msg));
  // 2 beats 3: VO_24 is both unused and the voice a Partitura knob measures from
  const vo24 = idOf(score, 'VO_24');
  check('2 before 3: VO_24 (vo.unused AND measured by Despedida_Retardo) → preview, not knob (the binding still names a voice Unreal does not play)',
    res(vo24).reach === 'preview' && res(vo24).contract === 'vo.unused' && (ctx.gov[vo24] || []).some(g => g.knob === 'Despedida_Retardo'));
  // 3 · a Partitura knob
  const tin = idOf(score, 'T_IN'), r3 = res(tin);
  check('3 · a Partitura knob governs it → knob, and which', r3.reach === 'knob' && r3.knobs.includes('Etapa_TituloRevelaIni') && /Reaches Unreal when you send Etapa_TituloRevelaIni/.test(r3.why), r3.why);
  const r3b = R.of(tin, ctxOf(score, { gov: {} }));
  check('...also by the contract alone (kind "partitura") when no bind names it', r3b.reach === 'knob' && r3b.knobs.length > 0 && r3b.contract === 'title.stage');
  // 4 · the contract: wired
  const kinds = {}; for (const id of Object.keys(score.elements)) { const r = res(id); if (r.reach === 'wired' && r.kind) (kinds[r.kind] = kinds[r.kind] || []).push(id); }
  check('4 · the contract (hardwired, wired, a knob, not blocking) → wired, with the owner', ['literal', 'wired', 'knob', 'not-blocking'].every(k => kinds[k] && kinds[k].length) && Object.values(kinds).flat().every(id => !!res(id).owner), Object.entries(kinds).map(([k, v]) => k + ' ' + v.length).join(' · '));
  const gb = idOf(score, 'G_BELL');
  check('...G_BELL: a knob of an instance in the contract, wired', res(gb).reach === 'wired' && res(gb).kind === 'knob' && /^A knob in Unreal: /.test(res(gb).why), res(gb).why);
  const lit = kinds.literal[0];
  check('...a hardwired one says so, with its graph', /^Hardwired in Unreal: /.test(res(lit).why) && !!res(lit).graph, res(lit).why);
  // 6 · preview, the first reason
  const world = Object.keys(score.elements).find(id => score.elements[id].type === 'world' && res(id).reach === 'preview' && !res(id).contract);
  check('6 · nothing in Unreal addresses it → preview, saying so', res(world).reach === 'preview' && /^No Unreal action/.test(res(world).why), res(world).why);
}

console.log('\ncounts');
{
  check('every element has one answer; the four add up to all of them', Object.keys(all.of).length === N && C.knob + C.wired + C.cue + C.preview === N, JSON.stringify(C));
  check('schema 2 is never cue-ready: only an element with a bind can be (the 12 that could be are counted apart)', C.cue === 0 && all.schema === 2 && all.marksFrom === 'seed');
  if (!live) {
    check('pinned today: 69 reach Unreal (timing) · 71 wired · 452 preview (12 of them could be cues) · 592 elements', C.knob === 69 && C.wired === 71 && C.cue === 0 && C.preview === 452 && C.bindable === 12 && N === 592, JSON.stringify(C));
    // the design measured 70 / 82 / 428 with the contract as it was before the corrections of lote 5 step 6: the same rules, that contract
    const today = clone(contract);
    today.entries = today.entries.filter(c => c.id !== 'vo.unused' && c.id !== 'vo.noasset');
    for (const c of today.entries) { delete c.ids; delete c.idKeys; delete c.idsFrom; }
    delete today.entries.find(c => c.id === 'vo.wired').match.excludeKeys;
    const bToday = clone(binding); delete bToday.idsFrom; for (const b of bToday.binds) delete b.ids; for (const o of Object.values(bToday.origins)) delete o.ids;
    const a0 = R.all(ctxOf(score, { contract: today, binding: bToday }));
    check('with the contract of design A §0 (before bind_ids put 12 voices into vo.unused / vo.noasset): 70 · 82 · 428 + the 12 that could be cues', a0.counts.knob === 70 && a0.counts.wired === 82 && a0.counts.preview === 440 && a0.counts.preview - a0.counts.bindable === 428, JSON.stringify(a0.counts));
    const moved = Object.keys(score.elements).filter(id => a0.of[id].reach !== res(id).reach).map(id => a0.of[id].reach + '→' + res(id).reach + ' ' + score.elements[id].key).sort();
    const docd = ['VO_01d', 'VO_04b', 'VO_06a', 'VO_12b', 'VO_17b', 'VO_21', 'VO_34c', 'VO_35c', 'VO_36', 'VO_36c', 'VO_36d'].map(k => 'wired→preview ' + k).concat(['knob→preview VO_24']).sort();
    check('the whole difference is the 12 documented voices: 11 wired → preview and VO_24 knob → preview, nothing else', same(moved, docd), moved.join(', '));
  }
}

console.log('\nwhat could be a cue once the score is bound (the projection of schema 2)');
{
  const cands = Object.keys(score.elements).filter(id => res(id).bindable);
  const rows = cands.map(id => `${score.elements[id].key}@${res(id).cue.mark}+${res(id).cue.offset.toFixed(1)}`).sort();
  if (!live) {
    check('12 elements: FX_GHOSTAPPEAR ×6, FX_SOULDETACH ×5 (one per charge), FX_SOULJOIN ×1', cands.length === 12 && same(rows, ['FX_GHOSTAPPEAR@S0.INTRO+0.0', 'FX_GHOSTAPPEAR@S1.INTRO+0.0', 'FX_GHOSTAPPEAR@S3.BEGIN+75.0', 'FX_GHOSTAPPEAR@S3.INTRO+0.0', 'FX_GHOSTAPPEAR@S4.BEGIN+60.0', 'FX_GHOSTAPPEAR@S4.INTRO+0.0',
      'FX_SOULDETACH@S0.CHARGE+0.0', 'FX_SOULDETACH@S1.CHARGE+0.0', 'FX_SOULDETACH@S2.CHARGE+0.0', 'FX_SOULDETACH@S3.CHARGE+0.0', 'FX_SOULDETACH@S4.CHARGE+0.0', 'FX_SOULJOIN@FINAL.CREDITS+7.5'].sort()), rows.join(' '));
  }
  check('each one is a preview that says it could be a cue, with the compiled cue it would be', cands.every(id => res(id).reach === 'preview' && /could be a cue/.test(res(id).why) && res(id).cue.asset && /^\/Game\//.test(res(id).cue.path) && ['sound', 'vo_alma', 'vo_2d'].includes(res(id).cue.action)));
  check('none of them is called by an Unreal asset (referencedBy is empty), none is owned by the contract or a knob', cands.every(id => { const a = idmap.assets[res(id).cue.asset]; return a.referencedBy && a.referencedBy.length === 0; }));
  // the rules that keep a sound from being a cue
  const dep = idsOfKey(score, 'FX_GHOSTOUT').filter(id => /depends on the user/.test(res(id).why));
  check('it must be the same from the mark for every user: FX_GHOSTOUT hangs from a wait (the fast and the idle user are seconds apart) → preview', dep.length >= 3 && dep.every(id => res(id).reach === 'preview' && !res(id).bindable), dep.length + ' of them');
  const early = idOf(score, 'FX_VEIL', 'V1');
  check('...it must not start before the mark: FX_VEIL in V1 is before ENV_SWAP (S1.OPEN) → preview', !early || (res(early).reach === 'preview' && /starts before S1 open/.test(res(early).why)), early && res(early).why);
  const sw = idOf(score, 'FX_SOULSWIM'), sa = idOf(score, 'FX_SHAREAPPEAR');
  check('...no Unreal asset calls it: FX_SOULSWIM is called by BP_SoulFish_SC → preview (it would play twice); wired only once bound', res(sw).reach === 'preview' && res(sw).referenced && /BP_SoulFish_SC/.test(res(sw).why));
  check('...a plugin asset has no references read: FX_CHARGE_1 (Charge1 in SC_Base) is unsure, not cue-ready', res(idOf(score, 'FX_CHARGE_1')).unsure === true && C.unsure === 5);
  check('...an effect Unreal plays at a place (sound_at: FX_SHAREAPPEAR) needs a target the seed cannot give → preview', res(sa).reach === 'preview' && /place in Unreal/.test(res(sa).why));
  const amb = Object.keys(score.elements).find(id => score.elements[id].type === 'ambience' && !res(id).contract);
  check('...an ambience is Unreal\'s (AmbPick); a wait is its own graph; haptics are not there', !amb || /ambience/.test(res(amb).why));
  const sub = Object.keys(score.elements).find(id => /^Inside Hall step \d+: a step Unreal does not announce/.test(res(id).why));
  check('...inside a Hall step (rel "sub") the time is Unreal\'s: "Inside Hall step N"', !!sub && /^Inside Hall step \d+/.test(res(sub).why), sub && res(sub).why);
  const inn = Object.keys(score.elements).find(id => /^Inside .*: its time is set by Unreal knobs/.test(res(id).why));
  check('...inside a span the Partitura times (rel "in"): which knobs', !!inn && /\(\w+/.test(res(inn).why), inn && res(inn).why);
  check('...a moment the seed does not know says so, and it is not counted as bindable', (() => {
    const id = idOf(score, 'FX_SOULDETACH', '1.R6'), sd = clone(seed); delete sd.beats[score.elements[id].beat];
    const r = R.of(id, ctxOf(score, { seed: sd })); return r.reach === 'preview' && /no Unreal mark yet/.test(r.why) && !r.bindable;
  })());
}

console.log('\nschema 3, bound to Unreal');
{
  const picks = Object.keys(score.elements).filter(id => res(id).bindable);
  const binds = {}; for (const id of picks) { const c = res(id).cue; binds[id] = { action: c.action, target: null, asset: c.asset, branch: null }; }
  const s3 = bound(score, binds), c3 = ctxOf(s3), a3 = R.all(c3);
  check('a schema 3 score with the seed\'s marks but no bind reads like schema 2: the same 12 could be cues, none is cue-ready', R.all(ctxOf(bound(score))).counts.cue === 0 && R.all(ctxOf(bound(score))).counts.bindable === 12 && R.all(ctxOf(bound(score))).marksFrom === 'score');
  check('bound: the 12 are cue-ready', a3.counts.cue === 12 && picks.every(id => a3.of[id].reach === 'cue'), JSON.stringify(a3.counts));
  const c0 = a3.of[picks.find(id => s3.elements[id].key === 'FX_SOULJOIN')];
  check('...state "no-player" (BP_ScorePlayer_SC does not exist), and the cue is {mark, offset, action, target, asset, path}', c0.state === 'no-player' && c0.cue.mark === 'FINAL.CREDITS' && Math.abs(c0.cue.offset - 7.5) < 1e-9 && c0.cue.action === 'sound' && c0.cue.target === null && c0.cue.asset === 'FX_SOULJOIN' && c0.cue.path === idmap.assets.FX_SOULJOIN.path, JSON.stringify(c0.cue));
  check('...with a player, ready', R.of(picks[0], ctxOf(s3, { player: true })).state === 'ready');
  check('...the rest does not move: knob / wired as in schema 2, the preview ones lose only the 12', a3.counts.knob === C.knob && a3.counts.wired === C.wired && a3.counts.preview === C.preview - 12);
  check('the status bar shows cue-ready only now: "69 reach Unreal (timing) · 71 wired · 12 cue-ready · 440 preview"', !live ? R.statusText(a3) === '69 reach Unreal (timing) · 71 wired · 12 cue-ready · 440 preview' : /cue-ready/.test(R.statusText(a3)), R.statusText(a3));

  const one = (key, beatKey, bd, o = {}) => { const id = idOf(score, key, beatKey); const s = bound(score, { [id]: bd }); return R.of(id, ctxOf(s, o)); };
  const GOOD = { action: 'sound', target: null, asset: 'FX_SOULDETACH', branch: null };
  const base = one('FX_SOULDETACH', '1.R6', GOOD);
  check('one bound sound in a moment that starts at a mark: cue', base.reach === 'cue' && base.cue.mark === 'S0.CHARGE');
  const sw3 = one('FX_SOULSWIM', '9.1b', { action: 'sound', target: null, asset: 'FX_SOULSWIM' });
  check('an asset an Unreal Blueprint already calls: wired (a cue would play it twice), saying who', sw3.reach === 'wired' && /BP_SoulFish_SC/.test(sw3.why) && sw3.unsure === false, sw3.why);
  const pl = one('FX_SOULDETACH', '1.R6', { action: 'sound', target: null, asset: 'Charge1' });
  check('a plugin asset (references not read): wired too, and unsure — the safe side', pl.reach === 'wired' && pl.unsure === true && /not read/.test(pl.why), pl.why);
  const amb3 = one('FX_SOULDETACH', '1.R6', { action: 'sound', target: null, asset: 'VO_12c' });
  check('an ambiguous asset (VO_12c is in two folders): preview, both paths named', amb3.reach === 'preview' && amb3.ambiguous === true && amb3.asset === 'VO_12c' && /ambiguous/.test(amb3.why) && /Breath\/Audio\/VO_12c/.test(amb3.why) && /Obra\/Audio\/VO_12c/.test(amb3.why), amb3.why);
  const mis = one('FX_SOULDETACH', '1.R6', { action: 'sound', target: null, asset: 'FX_NOWHERE' });
  check('an asset that is not in Content: preview, naming it', mis.reach === 'preview' && /FX_NOWHERE is not in Unreal's Content/.test(mis.why));
  const noasset = one('FX_SOULDETACH', '1.R6', { action: 'sound', target: null, asset: null });
  check('a sound with no asset: preview', noasset.reach === 'preview' && /No asset/.test(noasset.why));
  check('no idmap yet: preview, saying to scan', (() => { const id = idOf(score, 'FX_SOULDETACH', '1.R6'); return /not scanned/.test(R.of(id, ctxOf(bound(score, { [id]: GOOD }), { idmap: null })).why); })());
  check('actions that are not cues: ambience, title, veil, wait → preview; none → "No Unreal action"', ['ambience', 'title', 'veil', 'wait'].every(a => one('FX_SOULDETACH', '1.R6', Object.assign({}, GOOD, { action: a })).reach === 'preview') && /Unreal picks the ambience/.test(one('FX_SOULDETACH', '1.R6', Object.assign({}, GOOD, { action: 'ambience' })).why) && /^No Unreal action/.test(one('FX_SOULDETACH', '1.R6', Object.assign({}, GOOD, { action: null })).why));
  const tg = (t, a = 'sound_at') => one('FX_SOULDETACH', '1.R6', { action: a, target: t, asset: 'FX_SOULDETACH' });
  check('sound_at needs a target: none → preview; role:Alma and a tag → cue; role:Nobody → "not in roles.json"; a bad prefix → refused',
    /needs a target/.test(tg(null).why) && tg('role:Alma').reach === 'cue' && tg('tag:Spot').reach === 'cue' && tg('role:Bell').reach === 'cue' && /not in roles.json/.test(tg('role:Nobody').why) && /not a role/.test(tg('Alma').why));
  const ap = one('FX_SOULDETACH', '1.R6', { action: 'appear', target: 'role:Alma', asset: null });
  check('appear needs a target, not an asset: cue', ap.reach === 'cue' && ap.cue.asset === null && ap.cue.path === null && ap.cue.target === 'role:Alma');
  // the moment's relation
  const inBeat = (rel, extra = {}) => { const id = idOf(score, 'FX_SOULDETACH', '1.R6'), s = bound(score, { [id]: GOOD }), b = s.elements[id].beat; s.beats[b].marks = [Object.assign({ name: 'S0.CHARGE', rel }, extra)]; return R.of(id, ctxOf(s)); };
  check('a moment whose mark is "in" a span → preview, with the knobs that time it', (() => { const r = inBeat('in', { by: ['Carga_Dur', 'Otro'] }); return r.reach === 'preview' && /^Inside S0 charge: its time is set by Unreal knobs \(Carga_Dur, Otro\)/.test(r.why); })());
  check('..."sub" → a step Unreal does not announce; "preview" → Unreal decides, with its reason', /a step Unreal does not announce/.test(inBeat('sub').why) && /^Unreal decides what happens here: stage layers/.test(inBeat('preview', { why: 'stage layers' }).why));
  check('a moment with no marks in the score (bound, but this one left out) → preview', (() => { const id = idOf(score, 'FX_SOULDETACH', '1.R6'), s = bound(score, { [id]: GOOD }); s.beats[s.elements[id].beat].marks = []; return R.of(id, ctxOf(s)).reach === 'preview'; })());
  // an el mark inside a moment that is not tied to one
  check('an extra "el" mark governs what comes after it, even in a moment that is "in" a span', (() => {
    const id = idOf(score, 'FX_SOULDETACH', '1.R6'), s = bound(score, { [id]: GOOD }), b = s.elements[id].beat;
    s.beats[b].marks = [{ name: 'S0.CHARGE', rel: 'in', by: ['x'] }, { name: 'S0.BYE', rel: 'el', el: id, edge: 'start' }];
    const r = R.of(id, ctxOf(s)); return r.reach === 'cue' && r.cue.mark === 'S0.BYE' && r.cue.offset === 0;
  })());
  check('...and a mark placed by another moment never governs (the first placement counts)', (() => {
    const id = idOf(score, 'FX_SOULDETACH', '1.R6'), s = bound(score, { [id]: GOOD }), b = s.elements[id].beat;
    s.beats[b].marks = [{ name: 'S0.OPEN', rel: 'start' }];   // S0.OPEN is already placed by 3.1 (earlier): this moment does not own it
    return R.of(id, ctxOf(s)).reach === 'preview';
  })());
  // an option of a decision the default run does not play
  check('an element that is not in the typical run (the other option of a decision) → preview, saying so', (() => { const id = idOf(score, 'FX_SOULDETACH', '1.R6'), s = bound(score, { [id]: GOOD }), st = E.resolve(s, { persona: 'typical' }); delete st.t[id]; return /other option of a decision/.test(R.of(id, ctxOf(s, { schedT: st })).why); })());
}

console.log('\nthe words of the status bar');
{
  const t2 = R.statusText(all);
  check('schema 2: "N reach Unreal (timing) · N wired · N preview" — cue-ready is not shown before the score can carry a bind', /^\d+ reach Unreal \(timing\) · \d+ wired · \d+ preview$/.test(t2) && (live || t2 === '69 reach Unreal (timing) · 71 wired · 452 preview'), t2);
  const tt = R.statusTitle(all);
  check('...its tooltip says what each number is, that 12 could be cues once bound, and that nothing reaches Unreal before Send', /Partitura knob/.test(tt) && /could be cues once the score is bound/.test(tt) && /Nothing reaches Unreal until Send to Unreal/.test(tt) && !/cue player could fire/.test(tt) && tt.includes(C.bindable + ' of them'));
  check('a schema 3 score not bound yet still says how many could be cues; once bound, it does not', (() => {
    const binds = {}; for (const id of Object.keys(score.elements)) if (res(id).bindable) binds[id] = { action: res(id).cue.action, target: null, asset: res(id).cue.asset };
    return R.statusTitle(R.all(ctxOf(bound(score)))).includes(C.bindable + ' of them could be cues') && !/could be cues/.test(R.statusTitle(R.all(ctxOf(bound(score, binds)))));
  })());
  check('schema 3: "N cue-ready" in between, even at 0', R.statusText(R.all(ctxOf(bound(score)))).includes(' wired · 0 cue-ready · ') && /cue player could fire/.test(R.statusTitle(R.all(ctxOf(bound(score))))));
  check('the words of each answer', R.REACH_WORD.knob === 'Reaches Unreal' && R.REACH_WORD.wired === 'Wired in Unreal' && R.REACH_WORD.cue === 'Cue-ready' && R.REACH_WORD.preview === 'Preview');
}

console.log('\nthe contexts and the cost');
{
  check('purity: the score, the contract, the idmap and the seed are as they were read', before === JSON.stringify(score) + JSON.stringify(contract) + JSON.stringify(idmap) + JSON.stringify(seed));
  check('deterministic: the same answer twice', same(R.all(ctxOf(score)).of, all.of));
  const t0 = Date.now(); R.all(ctxOf(score)); const ms = Date.now() - t0;
  check('the four users are resolved once, only if a rule needs them; the whole piece takes well under a frame budget of a compute (< 150 ms)', ms < 150, ms + ' ms');
  let n = 0; const c2 = R.context({ score, schedT: ctx.schedT, contract, gov: ctx.gov, idmap, seed, roles, resolve: p => { n++; return E.resolve(score, { persona: p }); } });
  R.all(c2);
  check('...fast, slow and idle only (typical is already there), each once', n === 3, String(n));
  const c3 = R.context({ score, schedT: ctx.schedT, contract, gov: ctx.gov, idmap, seed, roles, resolve: () => { throw new Error('should not resolve'); } });
  check('...and an element decided by the contract never asks for them', R.of(idOf(score, 'T_IN'), c3).reach === 'knob' && R.of(idOf(score, 'G_BELL'), c3).reach === 'wired');
  check('deriveAction: a voice → vo_alma (VO_33, VO_35a/b, VO_37 → vo_2d); a sound → sound (the four placed ones → sound_at); haptics none; title / veil / wait read', (() => {
    const e = o => Object.assign({ key: 'X', type: 'sound' }, o);
    return R.deriveAction(e({ type: 'vo', key: 'VO_10' })) === 'vo_alma' && R.deriveAction(e({ type: 'vo', key: 'VO_33' })) === 'vo_2d' && R.deriveAction(e({ type: 'vo', key: 'VO_35a#2', sound: 'VO_35a' })) === 'vo_2d'
      && R.deriveAction(e({ key: 'FX_A' })) === 'sound' && R.deriveAction(e({ key: 'FX_SOULVANISH' })) === 'sound_at' && R.deriveAction(e({ type: 'haptic' })) === null && R.deriveAction(e({ type: 'ambience' })) === 'ambience'
      && R.deriveAction(e({ type: 'object', key: 'T_IN' })) === 'title' && R.deriveAction(e({ type: 'object', key: 'VEIL_CLOSE' })) === 'veil' && R.deriveAction(e({ type: 'wait', key: 'G_X' })) === 'wait' && R.deriveAction(e({ type: 'world', key: 'LUZ' })) === null;
  })());
}

console.log(fails ? `\n${fails} FAILED` : '\nall ok');
process.exit(fails ? 1 : 0);
