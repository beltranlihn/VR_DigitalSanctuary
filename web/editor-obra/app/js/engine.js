/* Soul Charger editor · SCORE ENGINE (pure: no DOM, no three). Runs in the browser and in Node (golden test).
   Same timing semantics as the narrative prototype (web/prototipo-narrativo/timeline.js:58-146), without its EDITS layer:
   an element starts at its anchor (moment start, or another element's start/end) + offset; `end` makes it last until an anchor;
   a moment chains after the previous one unless anchored; a moment ends with the last of its own elements
   (not counting sound, ambience, help or elements that span into another moment). */
(function (root) {
  'use strict';
  const PERSONAS = {
    fast:    { name: 'Fast',    note: 'acts right away',            wait: g => Math.max(0.8, g.expected * 0.3) },
    typical: { name: 'Typical', note: 'the expected time',          wait: g => g.expected },
    slow:    { name: 'Slow',    note: 'reaches the help',           wait: g => g.expected + 0.5 * Math.max(0, g.fw - g.expected) },
    idle:    { name: 'Idle',    note: 'hits every timeout',         wait: g => g.fw },
  };
  const NOT_IN_BEAT_END = new Set(['fx', 'amb']);

  function resolve(score, opt) {
    opt = opt || {};
    const persona = PERSONAS[opt.persona || 'typical'];
    const B = score.beats, E = score.elements;
    const node = id => B[id] || E[id];
    const kidsOfBeat = {};
    for (const id in E) (kidsOfBeat[E[id].beat] = kidsOfBeat[E[id].beat] || []).push(id);
    const beatOrder = [];
    for (const a of score.acts) for (const b of a.beats) beatOrder.push(b);
    const prevBeat = {}; beatOrder.forEach((b, i) => { prevBeat[b] = i ? beatOrder[i - 1] : null; });
    const crossSpan = id => { const e = E[id]; if (!e.end || !e.end.ref) return false; const r = e.end.ref; return (B[r] ? r : (E[r] && E[r].beat)) !== e.beat; };

    const mS = new Map(), mE = new Map(), vS = new Set(), vE = new Set(), cycles = [];
    const atOf = id => { if (B[id]) return B[id].at || (prevBeat[id] ? { ref: prevBeat[id], edge: 'end', off: 0 } : { ref: null, edge: 'start', off: 0 }); return E[id].at; };
    // an anchor to something that no longer exists falls back to the start of the element's own moment (and is reported)
    const dangling = [];
    const tAnchor = (a, self) => {
      if (!a) return 0;
      if (a.ref && !node(a.ref)) { dangling.push(self); const e = E[self]; return (e && B[e.beat] && e.beat !== self ? tStart(e.beat) : 0) + (a.off || 0); }
      return a.ref ? (a.edge === 'start' ? tStart(a.ref) : tEnd(a.ref)) + (a.off || 0) : a.off || 0;
    };
    function tStart(id) {
      if (mS.has(id)) return mS.get(id);
      if (vS.has(id)) { cycles.push(id); return 0; }
      vS.add(id); const v = tAnchor(atOf(id), id); vS.delete(id); mS.set(id, v); return v;
    }
    function tDur(id) {
      const e = E[id];
      if (e.end) return Math.max(0, tAnchor(e.end, id) - tStart(id));
      if (e.gate) return persona.wait(e.gate);
      return e.dur ? e.dur.value || 0 : 0;
    }
    function tEnd(id) {
      if (mE.has(id)) return mE.get(id);
      if (vE.has(id)) { cycles.push(id); return tStart(id); }
      vE.add(id); let v;
      if (B[id]) { v = tStart(id); for (const k of kidsOfBeat[id] || []) { const e = E[k]; if (!NOT_IN_BEAT_END.has(e.group) && !crossSpan(k) && !e.help) v = Math.max(v, tEnd(k)); } }
      else v = tStart(id) + tDur(id);
      vE.delete(id); mE.set(id, v); return v;
    }
    const t = {};
    for (const id of beatOrder) t[id] = [tStart(id), tEnd(id)];
    for (const id in E) t[id] = [tStart(id), tEnd(id)];
    // help is only active if it starts before its wait ends (prototype helpActive)
    const helpActive = {};
    for (const id in E) if (E[id].help && t[E[id].help]) helpActive[id] = t[id][0] < t[E[id].help][1] - 1e-6;
    let total = 0; for (const id of beatOrder) total = Math.max(total, t[id][1]);
    const acts = score.acts.map(a => ({ id: a.id, s: t[a.beats[0]][0], e: Math.max(...a.beats.map(b => t[b][1])) }));
    return { t, total, acts, helpActive, cycles: [...new Set(cycles)], dangling: [...new Set(dangling)] };
  }

  /* who depends on whom (anchors and "until"): id → [ids] */
  function dependents(score) {
    const kids = {};
    const add = (a, id) => { if (a && a.ref) (kids[a.ref] = kids[a.ref] || []).push(id); };
    for (const id in score.beats) add(score.beats[id].at, id);
    for (const id in score.elements) { add(score.elements[id].at, id); add(score.elements[id].end, id); }
    return kids;
  }
  function family(score, id, kids) {
    kids = kids || dependents(score); const out = new Set(), st = [id];
    while (st.length) { const x = st.pop(); for (const k of kids[x] || []) if (!out.has(k)) { out.add(k); st.push(k); } }
    return out;
  }
  const api = { PERSONAS, resolve, dependents, family };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.ScoreEngine = api;
})(typeof window !== 'undefined' ? window : globalThis);
