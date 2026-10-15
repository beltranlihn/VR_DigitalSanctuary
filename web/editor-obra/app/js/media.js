/* Veation VR Studio · MEDIA: which file sounds for an element of the score, pure (no DOM) so it runs in the browser and in
   Node (tools/score/media_test.mjs). The index is the server's /api/media items: the voices by their name (final mix, then
   earlier takes) and the sound effects and ambiences that obra/audio/media_map.json names (src 'fx').
   Owner rule: a time of the score comes from the timeline, never from a file. Only the final mix of a VOICE is offered as its
   real length (in Unreal a voice lasts its recording: C2.VO.REAL); an effect or an ambience plays at its clip's time, to its
   own end, and nothing here can change a duration. */
(function (root) {
  'use strict';
  const base = k => String(k == null ? '' : k).replace(/#\d+$/, '');
  const SOUNDING = new Set(['vo', 'sound', 'ambience']);

  /* the sound id an element plays: a voice by its recording (its 'sound' field, which a rename keeps: VO_10 renamed is still
     VO_10; a voice made in the editor by its key; VO_10#2 is VO_10), a sound or an ambience by its 'sound' field */
  function soundId(e) {
    if (!e || !SOUNDING.has(e.type)) return null;
    return base(e.type === 'vo' ? (!e.isNew && e.sound) || e.key : (e.sound || e.key)) || null;
  }
  /* its file: a voice only from the voice folders, an effect or an ambience only from the map (never crossed) */
  function fileOf(e, media) {
    const id = soundId(e), m = id && media ? media[id] : null;
    if (!m) return null;
    return (e.type === 'vo') === (m.src !== 'fx') ? m : null;
  }
  /* the final mix of a voice: the only file whose length counts */
  function mixOf(e, media) {
    const m = e && e.type === 'vo' ? fileOf(e, media) : null;
    return m && m.src === 'mix' && m.dur ? m : null;
  }
  /* the voices whose length here differs from their final mix (Problems ▸ C2.VO.REAL). A voice anchored by its end, a new one
     or one not timed by its audio is left alone */
  function voiceGaps(score, media) {
    const out = []; if (!media || !score) return out;
    for (const [id, e] of Object.entries(score.elements)) {
      if (e.type !== 'vo' || e.isNew || (e.end && e.end.ref) || !e.dur || e.dur.mode !== 'audio') continue;
      const m = mixOf(e, media); if (m && Math.abs(e.dur.value - m.dur) > .05) out.push({ id, key: e.key, now: e.dur.value, real: m.dur });
    }
    return out;
  }

  /* ---------- what the 3D loads ----------
     Voices and effects are small: all of them, once, when Sound is turned on. An ambience is 30-50 MB (112-180 s of stereo):
     only the one sounding at the playhead and the next ones are kept decoded (ambWindow), the rest is dropped. */
  function ambienceIds(score) {
    const s = new Set(); if (!score) return s;
    for (const e of Object.values(score.elements)) if (e.type === 'ambience') { const id = soundId(e); if (id) s.add(id); }
    return s;
  }
  function eagerIds(media, score) {
    const amb = ambienceIds(score);
    return Object.keys(media || {}).filter(id => media[id].src === 'fx' ? !amb.has(id) : /^VO_/.test(id));
  }
  /* the ambience elements in playing order: [{ id (element), sid (sound id), s (start) }] */
  function ambOrder(score, times) {
    return Object.entries(score.elements).filter(([id, e]) => e.type === 'ambience' && times[id])
      .map(([id, e]) => ({ id, sid: soundId(e), s: times[id][0] })).sort((a, b) => a.s - b.s || (a.id < b.id ? -1 : 1));
  }
  /* the sound id of the ambience sounding at t (the last one started), or null before the first */
  function ambAt(score, times, t) {
    let cur = null; for (const a of ambOrder(score, times)) { if (a.s <= t + 1e-6) cur = a.sid; else break; }
    return cur;
  }
  /* the ambiences to keep decoded at t: from the one sounding there onwards, the first n that have a file */
  function ambWindow(score, times, t, media, n) {
    n = n || 2;
    const list = ambOrder(score, times), out = [];
    let i = 0; for (let k = 0; k < list.length; k++) if (list[k].s <= t + 1e-6) i = k;
    for (let k = i; k < list.length && out.length < n; k++) {
      const sid = list[k].sid, m = media && media[sid];
      if (m && m.src === 'fx' && !out.includes(sid)) out.push(sid);
    }
    return out;
  }
  /* Unreal's volume for a mapped file (0-1, the map's 'gain'), applied to the decoded samples of the preview only */
  function scale(channels, gain) {
    if (gain == null || !(gain >= 0) || gain === 1) return false;
    for (const d of channels) for (let i = 0; i < d.length; i++) d[i] *= gain;
    return true;
  }

  const api = { soundId, fileOf, mixOf, voiceGaps, ambienceIds, eagerIds, ambOrder, ambAt, ambWindow, scale };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.Media = api;
})(typeof window !== 'undefined' ? window : globalThis);
