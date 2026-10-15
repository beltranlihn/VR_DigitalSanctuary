// media_test.mjs — real sound files in the 3D (rest of lote 3): which file sounds for an element, the owner rule (a file never
// changes a time of the score: only a voice's final mix is offered as its real length), which ambiences stay decoded around
// the playhead, and that obra/audio/media_map.json covers every sound id of the score (mapped, or a reason why not).
// Logic: web/editor-obra/app/js/media.js. Against the REAL score and map; nothing is written. Exit 1 if any case fails.
//   node tools/score/media_test.mjs
import fs from 'fs';
import path from 'path';
import { createRequire } from 'module';
import { fileURLToPath } from 'url';
const require = createRequire(import.meta.url);
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const E = require(path.join(ROOT, 'web/editor-obra/app/js/engine.js'));
const M = require(path.join(ROOT, 'web/editor-obra/app/js/media.js'));
// the frozen fixture by default (the owner's edits of the live score must not turn this red), --live for the real one
const score = JSON.parse(fs.readFileSync(path.join(ROOT, process.argv.includes('--live') ? 'obra/score/score.json' : 'tools/score/fixtures/f0-score.json'), 'utf8'));
const MAP = JSON.parse(fs.readFileSync(path.join(ROOT, 'obra/audio/media_map.json'), 'utf8'));
const before = JSON.stringify(score);
const T = E.resolve(score, { persona: 'typical' }).t;
let fails = 0;
const check = (name, ok, info) => { console.log((ok ? '  ok   ' : '  FAIL ') + name + (info ? '  · ' + info : '')); if (!ok) fails++; };
const els = Object.entries(score.elements);
const byKey = key => els.find(([, e]) => e.key === key);
const sids = new Set(els.filter(([, e]) => (e.type === 'sound' || e.type === 'ambience') && !e.isNew).map(([, e]) => M.soundId(e)));

console.log('the sound id of an element');
{
  check('a voice by its key (VO_10#2 is VO_10)', M.soundId({ type: 'vo', key: 'VO_10#2' }) === 'VO_10');
  check('a voice by its recording: renamed in the score it still sounds VO_10 (lote 5 design A §7.3); a new voice by its key', M.soundId({ type: 'vo', key: 'VO_10_ALT', sound: 'VO_10' }) === 'VO_10'
    && M.fileOf({ type: 'vo', key: 'VO_10_ALT', sound: 'VO_10' }, { VO_10: { src: 'mix', dur: 4 } }).dur === 4 && M.soundId({ type: 'vo', key: 'VO_NEW', sound: 'VO_10', isNew: true }) === 'VO_NEW');
  check("a sound by its 'sound' field, an ambience too", M.soundId({ type: 'sound', key: 'FX_WALK#2', sound: 'FX_WALK' }) === 'FX_WALK' && M.soundId({ type: 'ambience', key: 'Silence', sound: 'SILENCIO' }) === 'SILENCIO');
  check('a haptic, an object or nothing has none', M.soundId({ type: 'haptic', key: 'HAP_TICK', sound: 'HAP_TICK' }) === null && M.soundId({ type: 'object', key: 'X' }) === null && M.soundId(null) === null);
  const media = { VO_10: { src: 'mix', dur: 4 }, FX_X: { src: 'fx', dur: 2 }, VO_X: { src: 'fx', dur: 1 } };
  check('a voice never gets a mapped effect, an effect never gets a voice', M.fileOf({ type: 'vo', key: 'VO_10' }, media) === media.VO_10 && M.fileOf({ type: 'sound', key: 'FX_X' }, media) === media.FX_X
    && M.fileOf({ type: 'vo', key: 'VO_X' }, media) === null && M.fileOf({ type: 'sound', key: 'VO_10', sound: 'VO_10' }, media) === null);
}

console.log('owner rule: durations come from the timeline, never from a sound file');
{
  // every sound and ambience of the score gets a file that is far longer than its clip; the voices get none
  const media = {}; for (const id of sids) media[id] = { src: 'fx', dur: 999, file: id + '.wav' };
  const gaps = M.voiceGaps(score, media);
  check('no effect or ambience file is offered as a real length (no C2.VO.REAL row, no "Use the recording")', gaps.length === 0 && els.every(([, e]) => M.mixOf(e, media) === null), `${gaps.length} gaps`);
  const T2 = E.resolve(score, { persona: 'typical' }).t;
  check('the schedule is identical with every file present', JSON.stringify(T2) === JSON.stringify(T));
  // the same files plus the voices' final mix: only voices can differ, never an effect
  const vo = byKey('VO_02'); const m2 = Object.assign({}, media, { VO_02: { src: 'mix', dur: 7.3 } });
  const g2 = M.voiceGaps(score, m2);
  check("a voice's final mix still counts (only voices)", g2.length === 1 && g2[0].key === 'VO_02' && g2[0].real === 7.3, JSON.stringify(g2));
  check("an earlier take never counts as a voice's real length", M.voiceGaps(score, { VO_02: { src: 'take', dur: 7.3 } }).length === 0 && !!vo);
  const ch = [new Float32Array([1, -.5]), new Float32Array([.25, 0])];
  check("Unreal's volume scales the preview's samples, only when it is not 1", M.scale(ch, .4) && Math.abs(ch[0][0] - .4) < 1e-6 && Math.abs(ch[1][0] - .1) < 1e-6 && !M.scale(ch, 1) && !M.scale(ch, null));
}

console.log('ambiences: decoded around the playhead only');
{
  const media = {}; for (const id of Object.keys(MAP.map)) media[id] = { src: 'fx' };
  const t = k => T[byKey(k)[0]][0];
  check('the eager load has the voices and the effects, never an ambience', (() => { const ids = M.eagerIds(Object.assign({ VO_10: { src: 'mix' } }, media), score); return ids.includes('VO_10') && ids.includes('FX_DOOROPEN') && ids.includes('FX_HEARTBEAT') && !ids.some(i => /^AMB_/.test(i)) && !ids.includes('PAD_M1'); })());
  check('at 0 s: the first ambience and the next', JSON.stringify(M.ambWindow(score, T, 0, media)) === '["AMB_01","AMB_02"]', JSON.stringify(M.ambWindow(score, T, 0, media)));
  check('inside AMB_03: it and AMB_04 (the silence after it has no file)', JSON.stringify(M.ambWindow(score, T, t('AMB_03') + 1, media)) === '["AMB_03","AMB_04"]');
  check('in the silence: the ambiences that come next', JSON.stringify(M.ambWindow(score, T, t('SILENCIO') + .5, media)) === '["AMB_04","AMB_05"]' && M.ambAt(score, T, t('SILENCIO') + .5) === 'SILENCIO');
  check("Attracting's pad is an ambience too", JSON.stringify(M.ambWindow(score, T, t('PAD_M1') + 1, media)) === '["PAD_M1","AMB_07"]');
  check('at the end: only the last one', JSON.stringify(M.ambWindow(score, T, 1e6, media)) === '["AMB_09"]' && M.ambAt(score, T, 1e6) === 'AMB_09');
  check('an ambience starting exactly at t is the one sounding', M.ambAt(score, T, t('AMB_04')) === 'AMB_04' && M.ambAt(score, T, t('AMB_04') - .01) === 'SILENCIO');
  check('without files nothing is kept', M.ambWindow(score, T, 300, {}).length === 0 && M.ambWindow(score, T, 300, null).length === 0);
}

console.log('obra/audio/media_map.json');
{
  const ROOTS = { '': null, unreal: path.join(ROOT, 'VR_Test'), recursos: path.join(ROOT, 'Recursos') };
  const ids = Object.keys(MAP.map), bad = [], missing = [];
  for (const [id, rel] of Object.entries(MAP.map)) {
    const i = rel.indexOf(':'), root = i < 0 ? '' : rel.slice(0, i), p = i < 0 ? rel : rel.slice(i + 1);
    if (!(root in ROOTS) || /^[\\/]/.test(p) || p.split(/[\\/]/).includes('..') || !/\.(wav|mp3|ogg)$/i.test(p)) bad.push(id);
    else if (ROOTS[root] && !fs.existsSync(path.join(ROOTS[root], p))) missing.push(id);
  }
  check('version 1, every path inside a known root and an audio file', MAP.version === 1 && !bad.length, bad.join(', '));
  check("every 'unreal:' and 'recursos:' file is in the project", !missing.length, missing.join(', '));
  check('no voice is mapped (voices keep their name matching)', !ids.some(i => /^VO_/.test(i)));
  check('every gain is a volume between 0 and 1, of a mapped id', Object.entries(MAP.gain || {}).every(([k, g]) => typeof g === 'number' && g >= 0 && g <= 1 && k in MAP.map));
  check('every mapped id says why, and nothing is both mapped and unmapped', ids.every(i => typeof (MAP.why || {})[i] === 'string') && !ids.some(i => i in (MAP.unmapped || {})));
  const extra = ids.filter(i => !sids.has(i));
  check('a mapped id that is not in the score is a cue of the prototype, and says so', extra.every(i => /^Not a score element/.test(MAP.why[i])), extra.join(', '));
  const open = [...sids].filter(i => !(i in MAP.map) && !(i in (MAP.unmapped || {})));
  check('every sound id of the score is mapped or has a reason', !open.length, `${sids.size} ids · ${ids.length - extra.length} mapped · ${Object.keys(MAP.unmapped || {}).length} not` + (open.length ? ' · open: ' + open.join(', ') : ''));
}

check('the score was not touched', JSON.stringify(score) === before);
console.log('\n' + (fails ? fails + ' FAILED' : 'all ok'));
process.exit(fails ? 1 : 0);
