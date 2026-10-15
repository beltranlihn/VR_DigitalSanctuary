// Seed of the Unreal marks of every moment (lote 5 design A §2 and §3.4): which mark of BP_Obra_SC each moment of the score
// corresponds to, and how. Generated ONCE from the table of design A §2 into obra/score/seed/marks-v1.json (keyed by moment
// id; the `el` keys resolved to element ids now), then reviewed by the owner: its "status" says so until he does.
// Until the score is bound (schema 3, "Bind to Unreal"), the editor reads its marks from this seed (js/marks.js scoreMarks):
// that is how the Unreal run (obra/unreal/traza.json) is compared with the score.
//
// It never writes the score, nor anything under obra/unreal, VR_Test, web/prototipo-narrativo or tools/score/fixtures. It
// does not overwrite an existing seed (the owner may have corrected it by hand) unless --force.
//
//   node tools/score/seed_marks.mjs                 → obra/score/seed/marks-v1.json, only if missing
//   node tools/score/seed_marks.mjs --check         → exit 1 if the file differs from a fresh build (the date aside)
//   node tools/score/seed_marks.mjs --stdout        → print it, write nothing
//   node tools/score/seed_marks.mjs --force         → rewrite it on purpose (a developer act that shows in git)
//   [--score <path>]                                → resolve ids on another score (default obra/score/score.json, read-only)
// Relations: start = the moment starts at the mark · el = the mark is that element's start · in = inside the mark's span, its
// offset set by Partitura knobs (by) · sub = inside, addressed by a sub-mark or an instance knob (by) · preview = inside,
// nothing in Unreal addresses it (why).
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';

const require = createRequire(import.meta.url);
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
export const SEED = path.join(ROOT, 'obra/score/seed/marks-v1.json');
const Engine = require(path.join(ROOT, 'web/editor-obra/app/js/engine.js'));
const Marks = require(path.join(ROOT, 'web/editor-obra/app/js/marks.js'));

const H = n => 'HALL.1.' + n;
// design A §2, in the order of the piece: [moment key, mark, relation, {el, by, why, note, also: [[mark, {el}]]}]
export const TABLE = [
  ['0', 'OBRA.DISC', 'start', { note: 'phase 16, only with bDisclaimer (Aviso_Dur)' }],
  ['1.1', 'HALL.START', 'start', { note: 'phase 9' }],
  ['1.2', 'HALL.START', 'in', { by: ['Titulo_RevelaIni', 'Titulo_RevelaFin', 'Bajada_RevelaIni', 'Bajada_RevelaFin'] }],
  ['1.3', 'HALL.START', 'in', { by: ['Titulo_SaleIni'], note: 'hold = reveal end → leave start' }],
  ['1.4', H(1), 'sub', { note: 'Hall step 1 (walk); VO_01a/b/c = steps 2-4' }],
  ['1.5', H(5), 'sub', { note: 'Hall step 5' }],
  ['1.6', H(5), 'sub', { note: 'BP_HallTitle_SC reads Step' }],
  ['1.7', H(6), 'sub', { note: 'Hall step 6' }],
  ['1.8', H(6), 'sub', { by: ['FW_Bell'], note: 'Hall step 6 gate' }],
  ['1.9', H(7), 'sub', { note: 'Hall steps 7-8' }],
  ['1.10', H(9), 'sub', { note: 'Hall step 9' }],
  ['1.11', H(10), 'sub', { note: 'Hall steps 10-11' }],
  ['2.1', H(12), 'sub', { note: 'Hall step 12' }],
  ['2.2', H(12), 'sub', { by: ['FW_Tool'], note: 'Hall step 12 gate' }],
  ['2.4', H(14), 'sub', { note: 'Hall step 14' }],
  ['2.5', H(14), 'sub', { by: ['FW_Choose'], note: 'Hall step 14 gate' }],
  ['2.6', H(15), 'sub', { note: 'Hall step 15' }],
  ['2.7', H(16), 'sub', { note: 'Hall step 16' }],
  ['2.7a', H(17), 'sub', { note: 'one Hall step per tile' }],
  ['2.7b', H(18), 'sub', { note: 'one Hall step per tile' }],
  ['2.7c', H(19), 'sub', { note: 'one Hall step per tile' }],
  ['2.7d', H(20), 'sub', { note: 'one Hall step per tile' }],
  ['2.7e', H(21), 'sub', { note: 'one Hall step per tile' }],
  ['2.7f', H(22), 'sub', { note: 'one Hall step per tile' }],
  ['2.8', H(24), 'sub', { note: 'Hall steps 23-25 (tiles down, HUD, VO_07)' }],
  ['2.9', H(26), 'sub', { note: 'Hall steps 26-30 (bHallDone)' }],
  ['3.1', 'S0.OPEN', 'start', { note: 'phase 0' }],
  ['1.R2', 'S0.ALMA', 'start', { note: 'phase 4' }],
  ['1.R3', 'S0.ALMA', 'preview', { why: 'stage layers: the stage BP decides (StageIntro), no knob' }],
  ['1.R4', 'S0.INTRO', 'start', { note: 'phase 5' }],
  ['1.R5a', 'S0.BEGIN', 'start', { note: 'phase 6' }],
  ['1.R5b', 'S0.BEGIN', 'sub', { by: ['ExploreTime', 'CountTime', 'Cycles'], note: 'Entering_Stage instance knobs · BREATH.* log' }],
  ['1.R5x', 'S0.OUTRO', 'start', { note: 'phase 7' }],
  ['1.R6', 'S0.CHARGE', 'start', { note: 'phase 8' }],
  ['1.R8', 'S0.BYE', 'start', { note: 'phase 2' }],
  ['V1', 'S1.OPEN', 'el', { el: 'ENV_SWAP', note: 'phase 0; its VEIL_CLOSE is the tail of S0.BYE (Velo_CierreDur)' }],
  ['2.R2', 'S1.ALMA', 'start', { note: 'phase 4' }],
  ['2.R4', 'S1.INTRO', 'start', { note: 'phase 5' }],
  ['2.R5', 'S1.BEGIN', 'start', { note: 'phase 6; today it starts with 2.R4 (anchor loop A12)' }],
  ['2.R5x', 'S1.OUTRO', 'start', { note: 'phase 7' }],
  ['2.R6', 'S1.CHARGE', 'start', { note: 'phase 8' }],
  ['2.R8', 'S1.BYE', 'start', { note: 'phase 2' }],
  ['V2', 'S2.OPEN', 'el', { el: 'ENV_SWAP', note: 'phase 0; its VEIL_CLOSE is the tail of S1.BYE (Velo_CierreDur)' }],
  ['3.R2', 'S2.ALMA', 'start', { note: 'phase 4' }],
  ['3.R3', 'S2.INTRO', 'start', { note: 'phase 5', also: [['S2.BEGIN', { el: 'CELL_IN', note: 'phase 6 · to review: CELL_IN or VO_22 (design A §2, owner)' }]] }],
  ['3.R5', 'S2.BEGIN', 'sub', { by: ['StageDuration'], note: 'LovingCell StageDuration 60 (instance knob)' }],
  ['3.R5x', 'S2.OUTRO', 'start', { note: 'phase 7' }],
  ['3.R6', 'S2.CHARGE', 'start', { note: 'phase 8' }],
  ['3.R8', 'S2.BYE', 'start', { note: 'phase 2' }],
  ['V3', 'S3.OPEN', 'el', { el: 'ENV_SWAP', note: 'phase 0; its VEIL_CLOSE is the tail of S2.BYE (Velo_CierreDur)' }],
  ['4.R2', 'S3.ALMA', 'start', { note: 'phase 4' }],
  ['4.R3', 'S3.ALMA', 'preview', { why: 'stage layers: the stage BP decides (StageIntro), no knob' }],
  ['4.R4', 'S3.INTRO', 'start', { note: 'phase 5: Instr_Dur[3] + Instr_EsperaMax' }],
  ['4.R5', 'S3.BEGIN', 'start', { note: 'phase 6' }],
  ['4.coda', 'S3.BEGIN', 'sub', { by: ['S3.REQEND'], note: 'the close path after Etapa_Tope[3]; VO_28 = CueAttract Phase ≥ 3' }],
  ['4.R5x', 'S3.OUTRO', 'start', { note: 'phase 7' }],
  ['4.R6', 'S3.CHARGE', 'start', { note: 'phase 8' }],
  ['4.R8', 'S3.BYE', 'start', { note: 'phase 2' }],
  ['V4', 'S4.OPEN', 'el', { el: 'ENV_SWAP', note: 'phase 0; its VEIL_CLOSE is the tail of S3.BYE (Velo_CierreDur)' }],
  ['5.R2', 'S4.ALMA', 'start', { note: 'phase 4' }],
  ['5.R3', 'S4.ALMA', 'preview', { why: 'stage layers: the stage BP decides (StageIntro), no knob' }],
  ['5.R4', 'S4.INTRO', 'start', { note: 'phase 5: Instr_Dur[4] 0.6' }],
  ['5.R5', 'S4.BEGIN', 'start', { note: 'phase 6; today it starts with 5.R4 (anchor loop A12)' }],
  ['5.close', 'S4.BEGIN', 'sub', { by: ['S4.REQEND'], note: 'the presentation after Etapa_Tope[4]' }],
  ['5.release', 'S4.OUTRO', 'start', { note: 'phase 7' }],
  ['5.R6', 'S4.CHARGE', 'start', { note: 'phase 8 (final charge)', also: [['FINAL.DARK', { el: 'FINAL', note: 'phase 10' }]] }],
  ['9.1b', 'FINAL.RETURN', 'start', { note: 'phase 11' }],
  ['9.3', 'FINAL.RETURN', 'in', { by: ['Regreso_VeloIni', 'Regreso_VeloFin', 'Regreso_PezA'] }],
  ['9.4', 'FINAL.RESULTS', 'start', { note: 'phase 12' }],
  ['9.5', 'FINAL.RESULTS', 'in', { by: ['Res_InvitaRecorte', 'Res_BotonesVoz', 'Res_Cortafuegos'], note: 'FlowShare st2-st5; later SHARE.ASK' }],
  ['9.5b', 'FINAL.RESULTS', 'sub', { by: ['SHARE.YES', 'SHARE.NO'], note: 'the SHARE branches (design B); Unreal does not log them yet' }],
  ['9.6', 'FINAL.EXIT', 'start', { note: 'phase 13' }],
  ['9.7', 'FINAL.CREDITS', 'start', { note: 'phase 14', also: [['FINAL.FADE', { el: 'NEGRO_FIN', note: 'phase 15' }]] }],
];
// what the owner decides before this seed binds the score (design A §2 and §10, D-2)
export const REVIEW = [
  'S2.BEGIN (the Loving mechanic starts) is placed at CELL_IN, the start of 3.R3, so S2.INTRO lasts 0 s in the score (Unreal: Instr_Dur[2] = 6 s). Alternatives: VO_22, or split 3.R3 into an intro of 6 s and the calm.',
  'The R3 layers moments (1.R3, 4.R3, 5.R3) are preview only; they could instead be sub of S<K>.INTRO if the layers are the first thing StageIntro shows.',
  'S<K>.INTRO is placed at the start of R4 (this table); the run comparison of design A §6.1 measured it at ALMA_MOVE in R2 (Alma goes aside), which is 1 to 2 s away from the start of R4 in every stage.',
  'V<K>: the mark is ENV_SWAP; the VEIL_CLOSE before it belongs to the farewell of the stage before.',
];

/* the seed for a score (ids resolved on it; the typical user picks the first of a repeated key). Throws if the table and the
   score disagree (a moment or an element missing, a mark name Unreal does not emit, a phase mark placed twice) */
export function buildSeed(score) {
  const T = Engine.resolve(score, { persona: 'typical' }).t, B = score.beats, E = score.elements;
  const byKey = {}; for (const id of Object.keys(B)) byKey[B[id].key] = id;
  const order = score.acts.flatMap(a => a.beats), errs = [], beats = {}, placed = {};
  const elIn = (b, key) => Object.keys(E).filter(id => E[id].beat === b && E[id].key === key).sort((x, y) => T[x][0] - T[y][0] || (x < y ? -1 : 1))[0] || null;
  const rows = new Map(TABLE.map(r => [r[0], r]));
  for (const k of rows.keys()) if (!byKey[k]) errs.push(`moment ${k} of the table is not in the score`);
  for (const b of order) {
    const r = rows.get(B[b].key); if (!r) { errs.push(`moment ${B[b].key} is not in the table`); continue; }
    const [, name, rel, o] = r, marks = [];
    const one = (n, rl, x) => {
      if (!Marks.isValid(n)) errs.push(`${B[b].key}: ${n} is not a mark Unreal emits`);
      const m = { name: n, rel: rl };
      if (rl === 'el') { const id = elIn(b, x.el); if (!id) errs.push(`${B[b].key}: no element ${x.el}`); Object.assign(m, { el: id, elKey: x.el, edge: 'start' }); }
      if (x.by) m.by = x.by.slice();
      if (x.why) m.why = x.why;
      if (x.note) m.note = x.note;
      if ((rl === 'start' || rl === 'el') && Marks.isPhase(n)) { if (placed[n]) errs.push(`${n} placed twice (${placed[n]} and ${B[b].key})`); placed[n] = B[b].key; }
      marks.push(m);
    };
    one(name, rel, o);
    for (const [n, x] of o.also || []) one(n, 'el', x);
    beats[b] = { key: B[b].key, marks };
  }
  if (errs.length) throw new Error('the seed does not fit the score:\n  ' + errs.join('\n  '));
  return beats;
}
export function seedDoc(score, src, when) {
  const sha = require('node:crypto').createHash('sha1').update(JSON.stringify(score)).digest('hex').slice(0, 12);
  return {
    version: 1,
    status: 'proposed, pending owner review',
    generated: when,
    from: { table: 'docs/editor-obra/anexos/19-lote5-diseno-unreal.md §2', generator: 'tools/score/seed_marks.mjs', score: `${src} (schema ${score.schema}, rev ${score.rev}, sha ${sha})` },
    note: 'Keyed by moment id. marks[0] is the moment\'s own relation; any other entry is a mark that falls on one of its elements (rel el). Until the score is bound to Unreal (schema 3) the editor reads its marks from here. The score is not changed by this file.',
    review: REVIEW.slice(),
    beats: buildSeed(score),
  };
}
const counts = beats => { const c = { start: 0, el: 0, in: 0, sub: 0, preview: 0, extra: 0 }; for (const b of Object.values(beats)) { c[b.marks[0].rel]++; c.extra += b.marks.length - 1; } return c; };
export { counts };

// ---- the command (only when run, not when a test imports the table) ----
if (process.argv[1] && import.meta.url.toLowerCase() === pathToFileURL(path.resolve(process.argv[1])).href.toLowerCase()) {
  const argv = process.argv.slice(2), has = f => argv.includes(f);
  const fail = (code, msg) => { console.error(msg); process.exit(code); };
  const si = argv.indexOf('--score'), scorePath = si >= 0 ? path.resolve(process.cwd(), argv[si + 1] || '') : path.join(ROOT, 'obra/score/score.json');
  if (!fs.existsSync(scorePath)) fail(1, 'score not found: ' + scorePath);
  const rel = p => path.relative(ROOT, p).split(path.sep).join('/');
  const score = JSON.parse(fs.readFileSync(scorePath, 'utf8'));
  let doc; try { doc = seedDoc(score, rel(scorePath), new Date().toISOString().slice(0, 10)); } catch (e) { fail(1, e.message); }
  const c = counts(doc.beats);
  const line = `${Object.keys(doc.beats).length} moments: ${c.start} start, ${c.el} el, ${c.in} in, ${c.sub} sub, ${c.preview} preview; ${c.extra} more marks on elements`;
  if (has('--stdout')) { process.stdout.write(JSON.stringify(doc, null, 1) + '\n'); process.exit(0); }
  if (has('--check')) {
    if (!fs.existsSync(SEED)) fail(1, 'no seed yet: ' + rel(SEED));
    const old = JSON.parse(fs.readFileSync(SEED, 'utf8'));
    const diff = Object.keys(doc.beats).filter(b => JSON.stringify(doc.beats[b]) !== JSON.stringify((old.beats || {})[b])).concat(Object.keys(old.beats || {}).filter(b => !doc.beats[b]));
    if (diff.length) fail(1, `${rel(SEED)} differs from a fresh build in ${diff.length} moment(s): ${diff.map(b => (doc.beats[b] || old.beats[b]).key).join(', ')}`);
    console.log(`${rel(SEED)} matches a fresh build · ${line} · status: ${old.status}`); process.exit(0);
  }
  if (fs.existsSync(SEED) && !has('--force')) fail(1, `${rel(SEED)} exists (the owner may have reviewed it): nothing written. Use --check to compare, --force to rewrite it on purpose.`);
  fs.mkdirSync(path.dirname(SEED), { recursive: true });
  fs.writeFileSync(SEED, JSON.stringify(doc, null, 1) + '\n');
  console.log(`wrote ${rel(SEED)} · ${line} · status: ${doc.status}`);
}
