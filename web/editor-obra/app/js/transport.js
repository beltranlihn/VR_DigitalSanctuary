/* Veation VR Studio · TRANSPORT: the rules of playback of an NLE (audit C10), pure (no DOM) so they run in the browser and
   in Node (tools/score/transport_test.mjs): the J/K/L shuttle, the In/Out range, where Play starts and where it stops, and
   the previous or next moment. Times in seconds. A rate is the signed speed: 1, 2, 4 forward; −1, −2, −4 backwards.
   The range is playback state (App + prefs), never part of the score. */
(function (root) {
  'use strict';
  const MAX = 4, STEP = .1, EPS = 1e-3;
  const r3 = x => Math.round(x * 1000) / 1000;
  const clamp = (x, a, b) => Math.min(b, Math.max(a, x));

  /* J (dir −1) or L (dir +1). With K held: one step of 0.1 s that way, paused. Stopped, or going the other way: 1× that
     way. The same way again: twice as fast, up to 4×. Returns { rate } to play at, or { step } to move the playhead by. */
  function shuttle(st, dir) {
    if (st.kHeld) return { step: dir * STEP };
    const cur = st.playing ? st.rate : 0;
    if (!cur || Math.sign(cur) !== dir) return { rate: dir };
    return { rate: dir * Math.min(MAX, Math.abs(cur) * 2) };
  }

  /* I and O at t. One that lands on the wrong side of the other clears the other (as in Premiere), and says so (cleared) */
  function markIn(r, t) {
    t = r3(Math.max(0, t)); const clash = r.outT != null && r.outT <= t + EPS;
    return { inT: t, outT: clash ? null : r.outT, cleared: clash ? 'out' : null };
  }
  function markOut(r, t) {
    t = r3(Math.max(0, t)); const clash = r.inT != null && r.inT >= t - EPS;
    return { inT: clash ? null : r.inT, outT: t, cleared: clash ? 'in' : null };
  }

  /* the stretch playback is held to: [In, or the start; Out, or the end], inside the piece. null: no range, or nothing
     left of it (a score that got shorter than its In) */
  function bounds(r, total) {
    if (!r || (r.inT == null && r.outT == null)) return null;
    const lo = clamp(r.inT == null ? 0 : r.inT, 0, total), hi = clamp(r.outT == null ? total : r.outT, 0, total);
    return hi > lo + EPS ? [lo, hi] : null;
  }

  /* where playback starts. With a range: where the playhead is when it is inside, otherwise at In (at Out going backwards).
     Without one: forward from the very end starts over from 0:00, as in Premiere */
  function startAt(ph, rate, b, total) {
    if (b) {
      if (rate > 0) return ph < b[0] - EPS || ph >= b[1] - EPS ? b[0] : ph;
      return ph > b[1] + EPS || ph <= b[0] + EPS ? b[1] : ph;
    }
    if (rate > 0 && ph >= total - EPS) return 0;
    return ph;
  }

  /* one frame of playback, from prev to next: where it lands and whether it stops. It stops when it CROSSES Out (In,
     backwards), so a playhead taken past it while playing carries on to the end; and always at the ends of the piece */
  function advance(prev, next, rate, b, total) {
    if (rate > 0) {
      if (b && prev <= b[1] + EPS && next >= b[1]) return { t: b[1], stop: true };
      if (next >= total) return { t: total, stop: true };
    } else {
      if (b && prev >= b[0] - EPS && next <= b[0]) return { t: b[0], stop: true };
      if (next <= 0) return { t: 0, stop: true };
    }
    return { t: next, stop: false };
  }

  /* ↑ / ↓: the start of the previous or next moment (moments that start together count once). slack: going back, a start
     less than this behind the playhead is skipped (while playing, so a second ↑ does not land on the same one); null at
     the first or the last */
  function momentStep(starts, ph, dir, slack) {
    const s = [...new Set(starts.filter(Number.isFinite).map(r3))].sort((a, b) => a - b), sl = Math.max(EPS, slack || 0);
    if (dir > 0) { for (const t of s) if (t > ph + EPS) return t; return null; }
    for (let i = s.length - 1; i >= 0; i--) if (s[i] < ph - sl) return s[i];
    return null;
  }

  /* what the transport shows next to the timecode: nothing at 1×; "2×", "−1×" (backwards) otherwise */
  const rateLabel = rate => !rate || rate === 1 ? '' : (rate < 0 ? '−' : '') + Math.abs(rate) + '×';

  /* the other tab (timeline / 3D view) said { playing, rate }: what this tab does. null: nothing (no playing in it, or
     already the same). Otherwise { on, rate } to play at. A message without a rate (or a rate that is not a speed) keeps
     this tab's speed: it never falls back to 1× forward, which would undo a J or an L L pressed here */
  const okRate = x => Number.isFinite(x) && x !== 0 && Math.abs(x) <= MAX;
  function follow(d, st) {
    if (!d || d.playing == null) return null;
    const on = !!d.playing, cur = st.playing ? st.rate : 1, rate = on ? (okRate(d.rate) ? d.rate : cur) : 1;
    if (on === !!st.playing && (!on || rate === st.rate)) return null;
    return { on, rate };
  }

  const api = { MAX, STEP, shuttle, markIn, markOut, bounds, startAt, advance, momentStep, rateLabel, follow };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.Transport = api;
})(typeof window !== 'undefined' ? window : globalThis);
