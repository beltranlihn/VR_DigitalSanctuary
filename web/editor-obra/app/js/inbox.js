/* Veation VR Studio · INBOX: the WAV files of the sounds made in the editor, pure (no DOM, no network) so it runs in the browser
   and in Node (tools/score/inbox_test.mjs).
   A WAV loaded into a new sound waits in obra/audio/inbox/<element id>.wav until Unreal imports it. The score says WHICH file
   (audio.hash: the first 12 hex digits of the SHA-1 of its bytes, the same the server gives in GET /api/audio/inbox); the inbox
   has to hold exactly that file, whatever was done since: replace it, undo, delete the sound, copy it. plan() says what to send
   and what to take out so that the inbox and the score agree; the editor runs it after every undo or redo and before every save.
   check() is the gate a file passes before it is accepted (Unreal imports a PCM WAV: nothing else is taken, and a file that
   would not play or has no sound in it is said at once, not discovered at the import). */
(function (root) {
  'use strict';
  const ELEM_ID = /^el_[A-Za-z0-9]{3,40}$/;   // what the server takes as a name (tools/editor/serve_editor.py)
  const pathOf = id => 'obra/audio/inbox/' + id + '.wav';
  const CODEC = { 2: 'ADPCM', 3: 'floating point', 6: 'A-law', 7: 'mu-law', 0x11: 'IMA ADPCM', 0x55: 'MP3', 0xFFFE: 'an unknown format' };

  /* the facts of a WAV, read from its header (no decoding: a 20 MB file costs nothing), and whether Unreal can take it.
     { ok: true, pcm, ch, sr, bits, dur, bytes } or { ok: false, why } where why finishes the sentence "<file name> …" */
  function check(buf) {
    const u = buf instanceof Uint8Array ? buf : new Uint8Array(buf), n = u.byteLength, d = new DataView(u.buffer, u.byteOffset, n);
    const tag = o => String.fromCharCode(u[o], u[o + 1], u[o + 2], u[o + 3]);
    if (n < 12 || tag(0) !== 'RIFF' || tag(8) !== 'WAVE') return { ok: false, why: 'is not a WAV file: Unreal needs a PCM WAV.' };
    let fmt = null, data = null, o = 12;
    while (o + 8 <= n) {
      const id = tag(o), sz = d.getUint32(o + 4, true);
      if (id === 'fmt ' && sz >= 16 && o + 8 + sz <= n) {
        const t = d.getUint16(o + 8, true);
        // WAVE_FORMAT_EXTENSIBLE (what DAWs write for 24-bit or more than two channels): the real format is the first word of its sub-format
        fmt = { tag: t === 0xFFFE && sz >= 40 ? d.getUint16(o + 8 + 24, true) : t, ch: d.getUint16(o + 10, true), sr: d.getUint32(o + 12, true), byteRate: d.getUint32(o + 16, true), align: d.getUint16(o + 20, true), bits: d.getUint16(o + 22, true) };
      } else if (id === 'data') { data = { at: o + 8, size: sz }; break; }
      o += 8 + sz + (sz & 1);
    }
    if (!fmt) return { ok: false, why: 'is not a complete WAV: its format chunk is missing.' };
    if (!data) return { ok: false, why: 'is not a complete WAV: it has no sound data.' };
    if (fmt.tag !== 1) return { ok: false, why: `is ${CODEC[fmt.tag] || 'format ' + fmt.tag}, not PCM: Unreal needs a PCM WAV. Export it again as 16 or 24-bit PCM.` };
    if (!(fmt.ch >= 1) || !(fmt.sr > 0) || !(fmt.bits > 0)) return { ok: false, why: 'is not a usable WAV: its format says no channels, no rate or no bits.' };
    const rate = fmt.byteRate > 0 ? fmt.byteRate : fmt.sr * fmt.ch * Math.ceil(fmt.bits / 8), have = n - data.at;
    // a header that promises more sound than the file has is a file cut short (a copy that did not finish); 0xFFFFFFFF is what a recorder
    // that streams writes when it cannot know the length: the file is the sound
    const streamed = data.size === 0xFFFFFFFF;
    if (!streamed && data.size > have + 1) return { ok: false, why: `is cut short: its header says ${(data.size / rate).toFixed(2)} s but only ${(have / rate).toFixed(2)} s are in the file.` };
    const dur = (streamed ? have : data.size) / rate;
    if (!(dur >= 0.01)) return { ok: false, why: 'has no sound in it (0 s).' };
    return { ok: true, pcm: true, ch: fmt.ch, sr: fmt.sr, bits: fmt.bits, dur: +dur.toFixed(3), bytes: n };
  }

  /* the name a sound takes from a file or from the name field: letters, digits and _, the accents dropped (ñandú → nandu) and the
     prefix of what it IS (FX_ for a sound effect, VO_ for a voice, AMB_ for an ambience): a sound effect never takes a voice's name */
  const PREFIX = { sound: 'FX_', vo: 'VO_', ambience: 'AMB_', haptic: 'FX_' };
  function nameFor(v, type) {
    v = String(v || '').trim().replace(/\.[^.]+$/, '').normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^A-Za-z0-9_]+/g, '_').replace(/^_+|_+$/g, '');
    if (/^hap_/i.test(v)) v = v.slice(4);
    v = v.replace(/^(fx|vo|amb)_/i, '');
    return (PREFIX[type] || 'FX_') + (v || 'NEW_SOUND');
  }

  /* what the inbox has to hold for a score: { element id: hash } for every element whose audio says which file it is */
  function wanted(score) {
    const w = {};
    for (const [id, e] of Object.entries((score && score.elements) || {})) if (ELEM_ID.test(id) && e && e.audio && typeof e.audio.hash === 'string' && e.audio.hash) w[id] = e.audio.hash;
    return w;
  }

  /* what to do so that the inbox agrees with the score on screen.
     listing: { id: hash } of what the inbox holds now. opts: held(hash) = this page has the bytes; mine = the ids whose file this page put
     there (the only ones it may take out again: a file nobody here wrote is never touched); keep = other scores whose files must stay (the
     one saved on disk: a file it names is not taken out because the screen no longer does).
     upload: [{ id, hash, was?, from? }] the file is not there (or is another one, `was` its hash): send the bytes this page has, or copy them
     from `from`, another inbox file with the same bytes (a duplicate of a sound loaded in an earlier session); missing: [{ id, hash, was? }]
     nobody has the bytes (the page was reloaded and the file is gone, or another one is there): it has to be loaded again; remove: [id]
     files this page put there that nothing needs any more; defer: the same as upload, for a file that a SAVED score (keep) names and
     that the screen replaces: it stays where it is until a save (opts.final) says the new one is THE one, so an undo, a reload or a closed
     tab before the save still finds the file the piece has */
  function plan(score, listing, opts) {
    opts = opts || {}; listing = listing || {};
    const want = wanted(score), kept = (opts.keep || []).map(wanted), keep = Object.assign({}, ...kept), upload = [], defer = [], missing = [], remove = [];
    for (const [id, hash] of Object.entries(want)) {
      const was = listing[id];
      if (was === hash) continue;
      let job = null;
      if (opts.held && opts.held(hash)) job = { id, hash };
      else {
        const from = Object.keys(listing).find(k => k !== id && listing[k] === hash && ELEM_ID.test(k));
        if (from) job = { id, hash, from };
      }
      if (!job) { missing.push(was != null ? { id, hash, was } : { id, hash }); continue; }
      if (was != null) job.was = was;
      (was != null && !opts.final && kept.some(k => k[id] === was) ? defer : upload).push(job);
    }
    for (const id of opts.mine || []) if (listing[id] != null && !(id in want) && !(id in keep)) remove.push(id);
    return { upload, defer, missing, remove };
  }

  const api = { check, nameFor, wanted, plan, pathOf, ELEM_ID };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.Inbox = api;
})(typeof window !== 'undefined' ? window : globalThis);
