/* Veation VR Studio · VIEW: how the timeline reads (audit C11), pure (no DOM) so it runs in the browser and in Node
   (tools/score/view_test.mjs): the title of a clip, an anchor in words, the search (Ctrl+F), the zoom math (fit a range,
   zoom in enough to read a clip, scroll to show it) and what a wait on the stage's clock shows (its tail, its simulated users).
   Never changes the score. Times in seconds; widths in app pixels. */
(function (root) {
  'use strict';
  const clamp = (x, a, b) => Math.min(b, Math.max(a, x));
  const f1 = v => (Math.round(v * 10) / 10).toFixed(1);

  /* ---------- the title of a clip ----------
     A technical key (HALL_LOAD, G_SENSOR: capitals, digits, _ # . -) says little to a reader: a non-voice element that has a
     label shows the label first and the key after it, small. A voice keeps its key (VO_05 is how it is called everywhere).
     A label that repeats its key in front ("GHOST_BELL · "Rest your hand…"") drops that repetition. */
  const TECH = /^[A-Z0-9][A-Z0-9_#.\-]*$/;
  function titleOf(e) {
    const key = String((e && e.key) || ''), label = String((e && e.label) || '').trim();
    if (!e || e.type === 'vo' || !TECH.test(key) || !label || label === key) return { main: key, sub: e && e.type !== 'vo' && label !== key ? label : '', labelFirst: false };
    const rep = label.startsWith(key) ? label.slice(key.length).match(/^\s*[·:\-–]\s*([\s\S]*)$/) : null;
    const main = rep ? rep[1].trim() : label;
    return main ? { main, sub: key, labelFirst: true } : { main: key, sub: '', labelFirst: false };
  }

  /* what has an audio file of its own: a voice, a sound, an ambience, a haptic. A new wait, or a copy of an object, is new but is no sound:
     it has no WAV to load, it is not in the Library's Sounds and the status bar does not call it "new sound" */
  const hasAudio = e => !!e && /^(vo|sound|ambience|haptic)$/.test(e.type);

  /* ---------- the preferences of this computer, as they are read back (localStorage) ----------
     One written by an older version, or edited by hand, may hold anything. A persona or a who that does not exist threw while the top
     bar was drawn: a blank page, and nothing to say why. What cannot be read becomes the default; the rest stays as it was */
  const plainObj = o => (o && typeof o === 'object' && !Array.isArray(o) ? o : {});
  function cleanPref(pref, personas) {
    pref = plainObj(pref);
    return {
      persona: Object.prototype.hasOwnProperty.call(personas || {}, pref.persona) ? pref.persona : 'typical',
      pps: Number.isFinite(pref.pps) && pref.pps >= .4 && pref.pps <= 80 ? pref.pps : 8,   // the zoom limits of the timeline
      who: pref.who === 'S' ? 'S' : 'B',
      collapsed: plainObj(pref.collapsed), locked: plainObj(pref.locked),
    };
  }

  /* ---------- an anchor in words, as the inspector's anchor chip says it, with its offset ----------
     element: "after VO_04 +2.0 s" (its end) or "with VO_04" (its start); moment: "end of moment 2.3"; none: "start of the
     piece". A key used in several moments says which ("after PASO in 2.7a"). until: what an element lasts until (`end`). */
  const edgeOf = a => a && a.ref ? (a.edge === 'start' ? 'start' : 'end') : 'start';   // the engine reads anything but 'start' as the end
  function anchorPhrase(score, a, o) {
    o = o || {};
    const off = a && Number.isFinite(+a.off) ? +a.off : 0;
    const offTxt = Math.abs(off) >= .05 ? ` ${off > 0 ? '+' : '−'}${f1(Math.abs(off))} s` : '';
    if (!a || !a.ref) return (o.until ? 'until ' : '') + 'start of the piece' + offTxt;
    const edge = edgeOf(a), B = score.beats[a.ref];
    if (B) return o.until ? (edge === 'end' ? `until the end of moment ${B.key}` : `until moment ${B.key} starts`) + offTxt : `${edge} of moment ${B.key}${offTxt}`;
    const x = score.elements[a.ref];
    if (!x) return `${o.until ? 'until ' : ''}a deleted anchor${offTxt}`;
    let dup = '';
    for (const k in score.elements) { const y = score.elements[k]; if (y !== x && y.key === x.key) { dup = score.beats[x.beat] ? ' in ' + score.beats[x.beat].key : ''; break; } }
    if (o.until) return (edge === 'end' ? `until the end of ${x.key}${dup}` : `until ${x.key}${dup} starts`) + offTxt;
    return `${edge === 'end' ? 'after' : 'with'} ${x.key}${dup}${offTxt}`;
  }
  /* the anchor a moment has now (one without its own follows the end of the previous moment, as the engine does) */
  function beatAnchor(score, b) {
    const B = score.beats[b]; if (B && B.at) return B.at;
    const o = score.acts.flatMap(a => a.beats), i = o.indexOf(b);
    return i > 0 ? { ref: o[i - 1], edge: 'end', off: 0 } : { ref: null, edge: 'start', off: 0 };
  }

  /* ---------- search (Ctrl+F): elements by key, label or voice text; moments by key or title ----------
     Case and accents do not matter ("titulo" finds "título"); several words must all appear, in any order. The result is
     in time order (T: the schedule on screen), a moment before what starts with it, then top to bottom by lane. */
  const norm = s => String(s == null ? '' : s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  function findMatches(score, q, T) {
    const words = norm(q).trim().split(/\s+/).filter(Boolean); if (!words.length) return [];
    const hit = hay => { hay = norm(hay); return words.every(w => hay.includes(w)); };
    const laneIx = {}; let n = 0; for (const g of score.groups || []) for (const l of g.lanes) laneIx[l] = n++;
    const out = [];
    for (const a of score.acts) for (const b of a.beats) { const B = score.beats[b]; if (B && hit(B.key + ' ' + (B.title || ''))) out.push({ kind: 'beat', id: b, t: T && T[b] ? T[b][0] : 0, ln: -1, key: B.key }); }
    for (const [id, e] of Object.entries(score.elements)) if (hit([e.key, e.label, e.text].filter(Boolean).join(' '))) out.push({ kind: 'el', id, t: T && T[id] ? T[id][0] : 0, ln: laneIx[e.lane] != null ? laneIx[e.lane] : 1e6, key: e.key });
    out.sort((a, b) => a.t - b.t || a.ln - b.ln || (a.key < b.key ? -1 : a.key > b.key ? 1 : 0) || (a.id < b.id ? -1 : 1));
    return out;
  }
  /* Enter (dir +1) / Shift+Enter (−1). From the current match (cur ≥ 0), the next or previous one, wrapping. With none yet,
     from the playhead: the first match at or after it (Enter), or the last one before it (Shift+Enter), wrapping too. */
  function findStep(list, cur, dir, ph) {
    const m = list.length; if (!m) return -1;
    if (cur != null && cur >= 0 && cur < m) return (cur + (dir < 0 ? -1 : 1) + m) % m;
    if (dir < 0) { for (let i = m - 1; i >= 0; i--) if (list[i].t < ph - 1e-6) return i; return m - 1; }
    for (let i = 0; i < m; i++) if (list[i].t >= ph - 1e-6) return i;
    return 0;
  }

  /* ---------- waits as Unreal does them (lote 5 design B §6.2) ----------
     A wait that blocks (the prototype's way, every wait of a schema 2 score) lasts what each simulated user takes. One that runs on
     the stage's clock (`gate.blocking === false`) lasts its clock for everybody: the user only decides when the things that hang
     from its end happen, and whether its help line plays. */
  const clockWait = e => !!(e && e.gate && e.gate.blocking === false);
  /* the thin tail of a wait on the stage's clock: from where its clock ends to when the simulated user on screen acts (t = its
     [start, end] on screen, react = when this user acts, name = "Slow"). null when there is nothing to show: a wait that blocks (its
     length already is the user's), a user who acts before the clock ends (Fast) or right on it (Typical) */
  function waitReaction(e, t, react, name) {
    if (!clockWait(e) || !t || react == null || !(react > t[1] + .05)) return null;
    return { from: t[1], to: react, label: `the ${String(name || '').toLowerCase()} user acts here · the stage does not wait` };
  }
  /* the simulated users of a wait, for the inspector: when each one acts (seconds after the wait starts) and whether the help line
     of the wait plays for them (null: it has none). Read from the engine's own `react` and `helpActive`, whatever the flag says */
  function waitUsers(score, Engine, id) {
    const e = score.elements[id]; if (!e || !e.gate) return [];
    const helps = Object.keys(score.elements).filter(k => score.elements[k].help === id);
    return Object.keys(Engine.PERSONAS).map(k => {
      const P = Engine.PERSONAS[k], r = Engine.resolve(score, { persona: k });
      return { k, name: P.name, note: P.note, acts: r.react[id] - r.t[id][0], help: helps.length ? helps.some(h => r.helpActive[h]) : null };
    });
  }

  /* ---------- zoom ----------
     fitRange: the zoom (px/s) that shows [s, e] in `width` px with a margin on each side, and the time at the left edge that
     centres it. A very short range is shown as at least minSpan seconds. */
  function fitRange(s, e, width, o) {
    o = o || {};
    const min = o.min != null ? o.min : .4, max = o.max != null ? o.max : 80, pad = o.pad != null ? o.pad : .05, minSpan = o.minSpan != null ? o.minSpan : 2;
    if (!(width > 0)) return null;
    const span = Math.max(e - s, minSpan), pps = clamp(width / (span * (1 + 2 * pad)), min, max);
    return { pps, left: Math.max(0, (s + e) / 2 - width / pps / 2) };
  }
  /* enough zoom to read a found clip: at least minW px wide (an instant: at least instantPps), never past cap, never out */
  function revealPps(pps, dur, o) {
    o = o || {};
    const minW = o.minW != null ? o.minW : 80, cap = o.cap != null ? o.cap : 32, inst = o.instantPps != null ? o.instantPps : 12;
    const need = dur > 1e-6 ? minW / dur : inst;
    return pps >= need ? pps : Math.max(pps, Math.min(cap, need));
  }
  /* the scroll that shows [x0, x1] (content px, the lane header excluded) in a view `width` px wide: unchanged if it is
     already in view; centred if it fits; otherwise its start a margin from the left */
  function revealScroll(scroll, width, x0, x1, o) {
    const m = (o && o.margin != null) ? o.margin : 40;
    if (x0 >= scroll + m && x1 <= scroll + width - m) return scroll;
    if (x1 - x0 <= width - 2 * m) return Math.max(0, (x0 + x1) / 2 - width / 2);
    return Math.max(0, x0 - m);
  }

  const api = { titleOf, hasAudio, cleanPref, anchorPhrase, beatAnchor, findMatches, findStep, fitRange, revealPps, revealScroll, norm, clockWait, waitReaction, waitUsers };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.View = api;
})(typeof window !== 'undefined' ? window : globalThis);
