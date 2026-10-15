/* Soul Charger editor · SCORE ENGINE (pure: no DOM, no three). Runs in the browser and in Node (golden test).
   Same timing semantics as the narrative prototype (web/prototipo-narrativo/timeline.js:58-146), without its EDITS layer:
   an element starts at its anchor (moment start, or another element's start/end) + offset; `end` makes it last until an anchor;
   a moment chains after the previous one unless anchored; a moment ends with the last of its own elements
   (not counting sound, ambience, help or elements that span into another moment).
   Schema 3 (lote 5, design B §3) adds four things, none of which changes a schema-2 score (golden_test: 4 users, bit-identical):
   · branches: an element with `branch: { on, value }` only exists in that option of the decision (SHARE / DON'T SHARE);
   · alternative anchors: `alt: { "share=no": { at, end } }` replaces the anchor in that option;
   · non-blocking waits: `gate.blocking === false` is the stage's own clock (it lasts `expected` for everybody); the user only
     decides when the things that hang from its END happen (`react`), and those never lengthen their moment;
   · everything is still computed in the OLD order (same evaluation, same loops): a different order breaks the anchor loops
     (2.R4, 5.R4) at another place and moves times. Branch and reaction only change what is APPLIED, never what is evaluated. */
(function (root) {
  'use strict';
  const PERSONAS = {
    fast:    { name: 'Fast',    note: 'acts right away',            wait: g => Math.max(0.8, g.expected * 0.3) },
    typical: { name: 'Typical', note: 'the expected time',          wait: g => g.expected },
    slow:    { name: 'Slow',    note: 'reaches the help',           wait: g => g.expected + 0.5 * Math.max(0, g.fw - g.expected) },
    idle:    { name: 'Idle',    note: 'hits every timeout',         wait: g => g.fw },
  };
  const NOT_IN_BEAT_END = new Set(['fx', 'amb']);
  const blocking = g => g.blocking !== false;   // schema 2 has no flag: every wait blocks (the prototype's way)
  /* does this element's end count in its moment's end? (not sound, ambience, help, nor what lasts into another moment)
     `pick` (optional) reads the anchors of one branch option; without it, the element's own */
  function inBeatEnd(score, id, pick) {
    const B = score.beats, E = score.elements, e = E[id];
    if (!e || NOT_IN_BEAT_END.has(e.group) || e.help) return false;
    const en = pick ? pick(e, 'end') : e.end;
    if (!en || !en.ref) return true;
    const r = en.ref; return (B[r] ? r : (E[r] && E[r].beat)) === e.beat;
  }
  /* which option of each branch is on screen: null = every branch at once, primary anchors (schema 2, golden test);
     otherwise { branch: value }. opt.branch: 'all' · undefined (each branch's `default`) · { share: 'yes' | 'no' | 'auto' }.
     'auto' (or a key that is missing from the object) = `onTimeout` when this user hits the deciding wait's timeout
     (Idle: Unreal's own timeout answer), else `default`. A value the branch does not offer falls back to its default. */
  function selectBranches(score, opt, persona) {
    const want = opt.branch;
    if (want === 'all' || !score.branches) return null;
    const sel = {};
    for (const on in score.branches) {
      const br = score.branches[on], asked = want && typeof want === 'object' ? (want[on] == null ? 'auto' : want[on]) : 'default';
      let v = asked;
      if (asked === 'auto') { const g = (score.elements[br.gate] || {}).gate; v = g && br.onTimeout != null && persona.wait(g) >= g.fw ? br.onTimeout : br.default; }
      else if (asked === 'default' || (br.options && !Object.prototype.hasOwnProperty.call(br.options, asked))) v = br.default;
      sel[on] = v;
    }
    return sel;
  }

  function resolve(score, opt) {
    opt = opt || {};
    const persona = PERSONAS[opt.persona || 'typical'];
    const B = score.beats, E = score.elements;
    const node = id => B[id] || E[id];
    const sel = selectBranches(score, opt, persona);
    // an element of another option is still timed (its phantom time: nothing that hangs from it jumps) but it is not "there"
    const off = {};
    if (sel) for (const id in E) { const b = E[id].branch; if (b && sel[b.on] != null && sel[b.on] !== b.value) off[id] = true; }
    // the anchor that applies in the chosen option (alt) or the primary one
    const pick = (x, f) => {
      if (sel && x.alt) for (const k in x.alt) { const i = k.indexOf('='); if (i > 0 && sel[k.slice(0, i)] === k.slice(i + 1) && x.alt[k][f] !== undefined) return x.alt[k][f]; }
      return x[f];
    };
    // a wait that does not stop the stage and has no `end` of its own: what hangs from its END happens when the user acts
    const reacts = id => { const e = E[id]; return !!(e && e.gate && !blocking(e.gate) && !pick(e, 'end')); };
    const kidsOfBeat = {};
    for (const id in E) (kidsOfBeat[E[id].beat] = kidsOfBeat[E[id].beat] || []).push(id);
    const beatOrder = [];
    for (const a of score.acts) for (const b of a.beats) beatOrder.push(b);
    const prevBeat = {}; beatOrder.forEach((b, i) => { prevBeat[b] = i ? beatOrder[i - 1] : null; });

    /* elements whose time follows the user's reaction (§3.2.5): the ones that hang from the end of a non-blocking wait and, from
       them, whatever hangs from their start (when that start follows) or end (when that end follows). Worked out before anything is
       timed, so it never depends on the order things are computed in, and not at all when no wait is non-blocking (schema 2). */
    const sR = new Set(), eR = new Set();
    if (Object.keys(E).some(id => E[id].gate && !blocking(E[id].gate))) {
      const follows = a => !!(a && a.ref && E[a.ref] && (a.edge === 'start' ? sR.has(a.ref) : reacts(a.ref) || eR.has(a.ref)));
      for (let more = true; more;) {
        more = false;
        for (const id in E) {
          if (!sR.has(id) && follows(pick(E[id], 'at'))) { sR.add(id); more = true; }
          if (!eR.has(id) && (sR.has(id) || follows(pick(E[id], 'end')))) { eR.add(id); more = true; }
        }
      }
    }

    const mS = new Map(), mE = new Map(), vS = new Set(), vE = new Set(), cycles = [];
    const atOf = id => { if (B[id]) return pick(B[id], 'at') || (prevBeat[id] ? { ref: prevBeat[id], edge: 'end', off: 0 } : { ref: null, edge: 'start', off: 0 }); return pick(E[id], 'at'); };
    // an anchor to something that no longer exists falls back to the start of the element's own moment (and is reported)
    const dangling = [];
    const tAnchor = (a, self) => {
      if (!a) return 0;
      if (a.ref && !node(a.ref)) {
        dangling.push(self);
        if (B[self]) return (prevBeat[self] ? tEnd(prevBeat[self]) : 0) + (a.off || 0);   // a moment never falls to 0:00: it follows the previous one
        const e = E[self]; return (e && B[e.beat] && e.beat !== self ? tStart(e.beat) : 0) + (a.off || 0);
      }
      if (a.ref && a.edge !== 'start' && reacts(a.ref)) return tStart(a.ref) + persona.wait(E[a.ref].gate) + (a.off || 0);   // when THIS user acts
      return a.ref ? (a.edge === 'start' ? tStart(a.ref) : tEnd(a.ref)) + (a.off || 0) : a.off || 0;
    };
    function tStart(id) {
      if (mS.has(id)) return mS.get(id);
      if (vS.has(id)) { cycles.push(id); return 0; }
      vS.add(id); const v = tAnchor(atOf(id), id); vS.delete(id); mS.set(id, v); return v;
    }
    function tDur(id) {
      const e = E[id], en = pick(e, 'end');
      if (en) return Math.max(0, tAnchor(en, id) - tStart(id));
      if (e.gate) return blocking(e.gate) ? persona.wait(e.gate) : e.gate.expected;   // a non-blocking wait is the stage's clock, whoever is watching
      return e.dur ? e.dur.value || 0 : 0;
    }
    function tEnd(id) {
      if (mE.has(id)) return mE.get(id);
      if (vE.has(id)) { cycles.push(id); return tStart(id); }
      vE.add(id); let v;
      if (B[id]) {
        v = tStart(id);
        // every kid that could count is timed in the old order and place; the other branch and the reactions are only left out of the max
        for (const k of kidsOfBeat[id] || []) if (inBeatEnd(score, k, pick)) { const x = tEnd(k); if (!off[k] && !eR.has(k)) v = Math.max(v, x); }
      } else v = tStart(id) + tDur(id);
      vE.delete(id); mE.set(id, v); return v;
    }
    const t = {};
    for (const id of beatOrder) t[id] = [tStart(id), tEnd(id)];
    for (const id in E) t[id] = [tStart(id), tEnd(id)];
    // when each wait is over for THIS user: a blocking wait ends then; a non-blocking one goes on, the user just acts
    const react = {};
    for (const id in E) if (E[id].gate) react[id] = reacts(id) ? t[id][0] + persona.wait(E[id].gate) : t[id][1];
    // help is only active if it starts before its wait is over (prototype helpActive); a line of the other option plays nowhere
    const helpActive = {};
    for (const id in E) if (E[id].help && t[E[id].help] && !off[id]) helpActive[id] = t[id][0] < (E[id].help in react ? react[E[id].help] : t[E[id].help][1]) - 1e-6;
    // an anchor that crosses to the other option (C1): its phantom time is used, so nothing jumps, but it is reported
    // (crossBranch: who; crossInfo: who, which anchor (at / end) and what it points to, for the message)
    const crossBranch = [], crossInfo = [];
    if (sel) {
      for (const id of beatOrder) { const a = pick(B[id], 'at'); if (a && a.ref && off[a.ref]) { crossBranch.push(id); crossInfo.push({ id, field: 'at', ref: a.ref }); } }
      for (const id in E) if (!off[id]) for (const f of ['at', 'end']) { const a = pick(E[id], f); if (a && a.ref && off[a.ref]) { if (!crossBranch.includes(id)) crossBranch.push(id); crossInfo.push({ id, field: f, ref: a.ref }); } }
    }
    let total = 0; for (const id of beatOrder) total = Math.max(total, t[id][1]);
    const acts = score.acts.map(a => ({ id: a.id, s: t[a.beats[0]][0], e: Math.max(...a.beats.map(b => t[b][1])) }));
    return { t, total, acts, helpActive, cycles: [...new Set(cycles)], dangling: [...new Set(dangling)],
      off, react, reactive: Object.keys(E).filter(id => eR.has(id)), crossBranch: [...new Set(crossBranch)], crossInfo, branch: sel };
  }

  /* one run per option of each decision that is not the one the piece shows by default: the other sides of the branch-sensitive
     rules (integrity.js staticProblems, design B §5.2). [{ k: 'share=no', sel: { share: 'no' }, sched }]; schema 2: none.
     The other decisions stay on their default option, whoever the persona is (typical unless said) */
  function altRuns(score, persona) {
    const out = [], brs = score.branches || {};
    for (const on of Object.keys(brs)) {
      const br = brs[on];
      for (const o of Object.keys((br && br.options) || {})) {
        if (o === br.default) continue;
        const want = {}; for (const b of Object.keys(brs)) want[b] = b === on ? o : 'default';
        out.push({ k: on + '=' + o, sel: { [on]: o }, sched: resolve(score, { persona: persona || 'typical', branch: want }) });
      }
    }
    return out;
  }

  /* every anchor a node carries: its own (`at`, and `end` for an element) and, in schema 3, the ones of each option of a branch
     (`alt: { "share=no": { at, end } }`): [{ f: 'at' | 'end', a, k }] with k = null for its own and "<branch>=<option>" for an
     alternative. Only anchors that point to something (a ref). fields: which ones to read (a moment has no `end`) */
  function anchorsOf(x, fields) {
    const out = [], fs = fields || ['at', 'end'];
    if (!x) return out;
    for (const f of fs) if (x[f] && x[f].ref) out.push({ f, a: x[f], k: null });
    if (x.alt && typeof x.alt === 'object') for (const k of Object.keys(x.alt)) for (const f of fs) { const a = x.alt[k] && x.alt[k][f]; if (a && a.ref) out.push({ f, a, k }); }
    return out;
  }
  /* who depends on whom (anchors and "until"): id → [ids], each once. The alternative anchors (`alt`, schema 3) count: whoever
     hangs from something only in one option of a decision still hangs from it, and deleting or moving it has to know */
  function dependents(score) {
    const kids = {};
    const add = (x, id, fields) => { for (const { a } of anchorsOf(x, fields)) { const l = kids[a.ref] = kids[a.ref] || []; if (!l.includes(id)) l.push(id); } };
    for (const id in score.beats) add(score.beats[id], id, ['at']);
    for (const id in score.elements) add(score.elements[id], id);
    return kids;
  }
  function family(score, id, kids) {
    kids = kids || dependents(score); const out = new Set(), st = [id];
    while (st.length) { const x = st.pop(); for (const k of kids[x] || []) if (!out.has(k)) { out.add(k); st.push(k); } }
    return out;
  }
  const api = { PERSONAS, resolve, altRuns, dependents, family, inBeatEnd, anchorsOf };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.ScoreEngine = api;
})(typeof window !== 'undefined' ? window : globalThis);
