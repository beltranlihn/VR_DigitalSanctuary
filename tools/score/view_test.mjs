// view_test.mjs — how the timeline reads (audit C11): clip titles, anchors in words, the search (Ctrl+F) and the zoom
// math, pure, against the score of the piece. Logic: web/editor-obra/app/js/view.js. Exit 1 if any case fails.
// It runs on the frozen fixture tools/score/fixtures/f0-score.json (so real edits of the piece never break it); --live runs it
// on obra/score/score.json (see tools/score/test_score.mjs).
//   node tools/score/view_test.mjs [--live]
import path from 'path';
import { createRequire } from 'module';
import { fileURLToPath } from 'url';
import { testScore } from './test_score.mjs';
const require = createRequire(import.meta.url);
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const E = require(path.join(ROOT, 'web/editor-obra/app/js/engine.js'));
const V = require(path.join(ROOT, 'web/editor-obra/app/js/view.js'));
const { score, name: SRC } = testScore();
console.log('on the ' + SRC);
const before = JSON.stringify(score);
const T = E.resolve(score, { persona: 'typical' }).t;
let fails = 0;
const check = (name, ok, info) => { console.log((ok ? '  ok   ' : '  FAIL ') + name + (info ? '  · ' + info : '')); if (!ok) fails++; };
const near = (a, b, eps) => a != null && b != null && Math.abs(a - b) < (eps || 1e-6);
const idOf = key => Object.keys(score.elements).find(id => score.elements[id].key === key);
const beatOf = key => Object.keys(score.beats).find(b => score.beats[b].key === key);
const els = Object.values(score.elements);

console.log('clip titles: the label first for a technical key, voices keep theirs');
{
  const nonVo = els.filter(e => e.type !== 'vo' && e.label && e.label !== e.key), vo = els.filter(e => e.type === 'vo');
  const lf = nonVo.filter(e => V.titleOf(e).labelFirst);
  check('every non-voice element with its own label shows the label first and the key after it', lf.length === nonVo.length && lf.every(e => V.titleOf(e).sub === e.key), `${lf.length} of ${nonVo.length}`);
  check('every voice keeps its key as the title (no label first)', vo.every(e => { const t = V.titleOf(e); return t.main === e.key && !t.labelFirst && !t.sub; }), `${vo.length} voices`);
  const h = V.titleOf(score.elements[idOf('HALL_LOAD')] || { key: 'HALL_LOAD', type: 'world', label: 'Recién en el negro aparece el Hall' });
  check('HALL_LOAD: label first, key small after it', h.labelFirst && h.sub === 'HALL_LOAD' && h.main !== 'HALL_LOAD', h.main);
  const g = V.titleOf(score.elements[idOf('GHOST_BELL')]);
  check('GHOST_BELL: the label that repeats the key in front drops it', g.labelFirst && !g.main.startsWith('GHOST_BELL') && g.sub === 'GHOST_BELL', g.main);
  const s = els.find(e => e.type === 'sound');
  check('a sound whose label is its key: the key alone', V.titleOf(s).main === s.key && !V.titleOf(s).sub && !V.titleOf(s).labelFirst, s.key);
  check('a key that is not technical keeps the key first, the label after it', (() => { const t = V.titleOf({ key: 'Puerta', type: 'object', label: 'La puerta' }); return t.main === 'Puerta' && t.sub === 'La puerta' && !t.labelFirst; })());
  check('a label that is only the repeated key falls back to the key', (() => { const t = V.titleOf({ key: 'FOG_IN', type: 'world', label: 'FOG_IN · ' }); return t.main === 'FOG_IN' && !t.labelFirst; })());
  check('a label that only begins like the key is kept whole', V.titleOf({ key: 'FOG_IN', type: 'world', label: 'FOG_INSIDE the hall' }).main === 'FOG_INSIDE the hall');
}

console.log('anchors in words (the inspector chip, with its offset)');
{
  check('no anchor: start of the piece', V.anchorPhrase(score, null) === 'start of the piece' && V.anchorPhrase(score, { ref: null, edge: 'start', off: 12 }) === 'start of the piece +12.0 s');
  const vo4 = idOf('VO_04');
  check('after an element\'s end, with the offset', V.anchorPhrase(score, { ref: vo4, edge: 'end', off: 2 }) === 'after VO_04 +2.0 s', V.anchorPhrase(score, { ref: vo4, edge: 'end', off: 2 }));
  check('with an element\'s start; a tiny offset is not said', V.anchorPhrase(score, { ref: vo4, edge: 'start', off: .01 }) === 'with VO_04');
  check('a negative offset uses the minus sign', V.anchorPhrase(score, { ref: vo4, edge: 'end', off: -1.25 }) === 'after VO_04 −1.3 s', V.anchorPhrase(score, { ref: vo4, edge: 'end', off: -1.25 }));
  const b = beatOf('2.4');
  check('a moment: start of / end of moment K', V.anchorPhrase(score, { ref: b, edge: 'start', off: 3 }) === 'start of moment 2.4 +3.0 s' && V.anchorPhrase(score, { ref: b, edge: 'end', off: 0 }) === 'end of moment 2.4');
  const dupKey = (() => { const m = {}; for (const e of els) m[e.key] = (m[e.key] || 0) + 1; return Object.keys(m).find(k => m[k] > 1); })();
  const dupId = idOf(dupKey);
  check('a key used in several moments says which', V.anchorPhrase(score, { ref: dupId, edge: 'end', off: 0 }) === `after ${dupKey} in ${score.beats[score.elements[dupId].beat].key}`, V.anchorPhrase(score, { ref: dupId, edge: 'end', off: 0 }));
  check('a deleted anchor says so', V.anchorPhrase(score, { ref: 'el_gone', edge: 'end', off: 0 }) === 'a deleted anchor');
  check('until: what an element lasts until', V.anchorPhrase(score, { ref: vo4, edge: 'end' }, { until: true }) === 'until the end of VO_04' && V.anchorPhrase(score, { ref: b, edge: 'start' }, { until: true }) === 'until moment 2.4 starts');
  const order = score.acts.flatMap(a => a.beats);
  const loose = order.find((x, i) => i > 0 && !score.beats[x].at);
  check('a moment without its own anchor follows the previous one (as the engine)', loose ? V.beatAnchor(score, loose).ref === order[order.indexOf(loose) - 1] : V.beatAnchor(score, order[1]) === score.beats[order[1]].at);
  // every element and moment of the score gets a phrase without throwing, and never "undefined"
  let bad = 0; for (const [id, e] of Object.entries(score.elements)) { const p = V.anchorPhrase(score, e.at) + (e.end ? V.anchorPhrase(score, e.end, { until: true }) : ''); if (/undefined|NaN/.test(p)) bad++; }
  for (const x of order) if (/undefined|NaN/.test(V.anchorPhrase(score, V.beatAnchor(score, x)))) bad++;
  check('the whole score reads without "undefined" or "NaN"', !bad, `${els.length} elements · ${order.length} moments`);
}

console.log('search (Ctrl+F)');
{
  const all = V.findMatches(score, 'VO_0', T);
  check('by key: VO_0 finds the voices VO_01…VO_09, in time order', all.length > 5 && all.every(m => m.kind === 'el' && /VO_0/.test(score.elements[m.id].key)) && all.every((m, i) => !i || all[i - 1].t <= m.t), `${all.length} matches`);
  const acc = V.findMatches(score, 'titulo', T), acc2 = V.findMatches(score, 'TÍTULO', T);
  check('case and accents do not matter ("titulo" finds "El título")', acc.length > 0 && acc.length === acc2.length && acc.some(m => m.kind === 'beat'), `${acc.length} matches`);
  const vt = els.find(e => e.type === 'vo' && e.text && e.text.split(/\s+/).length > 4), w = vt.text.split(/\s+/).filter(x => x.length > 3).slice(0, 2);
  const byText = V.findMatches(score, w.reverse().join('  '), T);
  check('by voice text: two words in any order', byText.some(m => m.id === idOf(vt.key) || score.elements[m.id] && score.elements[m.id].text === vt.text), w.join(' + '));
  const mom = V.findMatches(score, '2.4', T).filter(m => m.kind === 'beat');
  check('moments by key', mom.some(m => m.id === beatOf('2.4')));
  const tie = V.findMatches(score, '1.1', T), bi = tie.findIndex(m => m.id === beatOf('1.1'));
  check('a moment comes before what starts with it', bi >= 0 && tie.slice(0, bi).every(m => m.t < tie[bi].t - 1e-9));
  check('blank query: nothing', V.findMatches(score, '   ', T).length === 0 && V.findMatches(score, '', T).length === 0);
  check('nothing matches: empty', V.findMatches(score, 'zzqqxx_nada', T).length === 0);
  const L = [{ t: 0 }, { t: 10 }, { t: 20 }, { t: 30 }];
  check('Enter with no current match: the first at or after the playhead', V.findStep(L, -1, 1, 10) === 1 && V.findStep(L, -1, 1, 11) === 2 && V.findStep(L, -1, 1, 31) === 0);
  check('Shift+Enter with no current match: the last before the playhead', V.findStep(L, -1, -1, 10) === 0 && V.findStep(L, -1, -1, 0) === 3);
  check('from the current match, next and previous wrap around', V.findStep(L, 3, 1, 0) === 0 && V.findStep(L, 0, -1, 0) === 3 && V.findStep(L, 1, 1, 99) === 2);
  check('no matches: -1', V.findStep([], -1, 1, 0) === -1);
}

console.log('zoom: fit a range, zoom in enough, reveal');
{
  const r = V.fitRange(100, 160, 800, { pad: .05 });
  check('fit 60 s in 800 px with 5% margins', near(r.pps, 800 / (60 * 1.1)) && near(r.left + 800 / r.pps / 2, 130), `${r.pps.toFixed(2)} px/s · left ${r.left.toFixed(1)} s`);
  check('a range at the start never scrolls before 0:00', V.fitRange(0, 10, 800).left === 0);
  const tiny = V.fitRange(50, 50, 800, { minSpan: 2, max: 80 });
  check('an empty range is shown as minSpan seconds, capped at the max zoom', tiny.pps <= 80 && near(tiny.left + 800 / tiny.pps / 2, 50), `${tiny.pps} px/s`);
  check('no width: null', V.fitRange(0, 10, 0) === null);
  const order = score.acts.flatMap(a => a.beats), b = order[5], fb = V.fitRange(T[b][0], T[b][1], 900);
  check('a real moment fits inside the view', fb.left * fb.pps <= T[b][0] * fb.pps && (T[b][1] - fb.left) * fb.pps <= 900 + 1e-6, `${score.beats[b].key}: ${fb.pps.toFixed(2)} px/s`);
  check('zoom enough: a 2 s clip at 8 px/s goes to 32 px/s (the cap)', V.revealPps(8, 2) === 32);
  check('zoom enough: a 4 s clip at 8 px/s goes to 20 px/s (80 px wide)', near(V.revealPps(8, 4), 20));
  check('zoom enough: a long clip keeps the zoom; it never zooms out', V.revealPps(8, 60) === 8 && V.revealPps(50, 1) === 50);
  check('zoom enough: an instant gets at least 12 px/s', V.revealPps(8, 0) === 12 && V.revealPps(20, 0) === 20);
  check('reveal: already in view stays', V.revealScroll(100, 800, 300, 400) === 100);
  check('reveal: fits, centred', V.revealScroll(0, 800, 2000, 2100) === 1650);
  check('reveal: longer than the view, its start a margin from the left', V.revealScroll(0, 800, 2000, 3500) === 1960);
  check('reveal: never before 0', V.revealScroll(500, 800, 10, 20) === 0);
}

console.log('what has an audio file: a new wait is new but no sound (review of the editor, 10-15)');
{
  const t = k => ({ type: k });
  check('hasAudio: a voice, a sound, an ambience and a haptic have a file', ['vo', 'sound', 'ambience', 'haptic'].every(k => V.hasAudio(t(k))));
  check('hasAudio: a wait, an object, an instruction, a world, a path and an interaction do not (a new wait showed "Drop a WAV here" and "new sound")', ['wait', 'object', 'instruction', 'world', 'path', 'interaction'].every(k => !V.hasAudio(t(k))));
  check('hasAudio: nothing is not a sound', !V.hasAudio(null) && !V.hasAudio(undefined) && !V.hasAudio({}));
  // every kind of element the piece has: the ones with a recording or a sound file are the ones the Library lists as sounds
  const kinds = [...new Set(els.map(e => e.type))], audio = kinds.filter(k => V.hasAudio(t(k)));
  check('the kinds of the piece split into with a file and without', audio.length > 0 && audio.length < kinds.length, `with: ${audio.join(', ')} · without: ${kinds.filter(k => !audio.includes(k)).join(', ')}`);
  check('  every element that has a sound name (e.sound) of a kind without a file is none: sound names belong to the kinds that have one', els.filter(e => e.sound).every(e => V.hasAudio(e)));
}

console.log('the preferences read back from localStorage (review of the editor, 10-15): a bad one never stops the editor from opening');
{
  const P = E.PERSONAS, good = { persona: 'slow', pps: 12.5, who: 'S', collapsed: { hap: false }, locked: { vo: true } };
  const c0 = V.cleanPref(good, P);
  check('cleanPref: a good preference stays as it was', c0.persona === 'slow' && c0.pps === 12.5 && c0.who === 'S' && c0.collapsed.hap === false && c0.locked.vo === true);
  const c1 = V.cleanPref({ persona: 'bogus', who: 'Z', pps: 'abc', collapsed: [1], locked: 'x' }, P);
  check('cleanPref: a persona and a who that do not exist, a zoom that is not a number, a list or a text where an object goes: the defaults (they threw while the top bar was drawn: a blank page)',
    c1.persona === 'typical' && c1.who === 'B' && c1.pps === 8 && JSON.stringify(c1.collapsed) === '{}' && JSON.stringify(c1.locked) === '{}', JSON.stringify(c1));
  check('cleanPref: a name that every object has (toString, constructor, __proto__) is not a persona', ['toString', 'constructor', '__proto__', 'hasOwnProperty'].every(k => V.cleanPref({ persona: k }, P).persona === 'typical'));
  check('cleanPref: the four simulated users are kept', Object.keys(P).length >= 4 && Object.keys(P).every(k => V.cleanPref({ persona: k }, P).persona === k), Object.keys(P).join(', '));
  check('cleanPref: a zoom outside the timeline limits (0.4 to 80) is the default, the limits themselves are fine', [0, -3, 0.39, 80.01, Infinity, NaN, null, '8'].every(v => V.cleanPref({ pps: v }, P).pps === 8) && V.cleanPref({ pps: 0.4 }, P).pps === 0.4 && V.cleanPref({ pps: 80 }, P).pps === 80);
  check('cleanPref: nothing, null, a text or a list is every default', [undefined, null, 'x', 5, []].every(v => { const c = V.cleanPref(v, P); return c.persona === 'typical' && c.pps === 8 && c.who === 'B'; }));
  const before = JSON.stringify(good); V.cleanPref(good, P);
  check('cleanPref: never changes what it gets', JSON.stringify(good) === before);
}

check('nothing here writes the score', JSON.stringify(score) === before);
console.log(fails ? `\n${fails} FAILED` : '\nall ok');
process.exit(fails ? 1 : 0);
