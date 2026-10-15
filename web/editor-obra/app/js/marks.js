/* Veation VR Studio · MARKS: the moments Unreal really emits (lote 5 design A §1), pure (no DOM): it runs in the browser and
   in Node (tools/score/marks_test.mjs). The phase numbers of BP_Obra_SC.RunObra live ONLY here: the score and the editor
   store mark names (S1.BEGIN, FINAL.RETURN…), never phase numbers (they were renumbered once already).
   traceMarks/traceInfo read obra/unreal/traza.json (written by tools/unreal/smoke_obra.py --traza, read-only here);
   scoreMarks says where each mark falls in the score: schema 3 from beats[].marks (the seed while it carries none), schema 2
   from the seed obra/score/seed/marks-v1.json (keyed by moment id). Never changes the score. */
(function (root) {
  'use strict';
  // phase code of RunObra → mark. Stage phases are per stage K (0 Entering … 4 Surrounding): S<K>.<step>
  const PHASE = {
    16: { mark: 'OBRA.DISC', what: 'the prototype disclaimer' },
    9: { mark: 'HALL.START', what: 'the Hall' },
    0: { step: 'OPEN', what: 'the stage opens: colour veil and title' },
    4: { step: 'ALMA', what: 'Alma receives' },
    5: { step: 'INTRO', what: 'the instructions' },
    6: { step: 'BEGIN', what: 'the mechanic' },
    7: { step: 'OUTRO', what: "the stage outro and Alma's congratulation" },
    8: { step: 'CHARGE', what: 'the ring charge' },
    2: { step: 'BYE', what: 'the farewell, the veil closes' },
    3: { legacy: true, what: 'legacy OpenLevel, unused' },
    10: { mark: 'FINAL.DARK', what: 'the HUD goes, to black' },
    11: { mark: 'FINAL.RETURN', what: 'the return through the dark to the Hall' },
    12: { mark: 'FINAL.RESULTS', what: 'the results and SHARE' },
    13: { mark: 'FINAL.EXIT', what: 'the Hall exit' },
    14: { mark: 'FINAL.CREDITS', what: 'the constellation and the credits' },
    15: { mark: 'FINAL.FADE', what: 'the fade, then the restart' },
  };
  const STAGES = ['Entering', 'Recognizing', 'Loving', 'Attracting', 'Surrounding'];
  const STEPS = ['OPEN', 'ALMA', 'INTRO', 'BEGIN', 'REQEND', 'OUTRO', 'CHARGE', 'BYE'];
  const TAIL = ['FINAL.DARK', 'FINAL.RETURN', 'FINAL.RESULTS', 'SHARE.ASK', 'SHARE.YES', 'SHARE.NO', 'FINAL.EXIT', 'FINAL.CREDITS', 'FINAL.FADE', 'OBRA.END'];
  const WORD = { 'OBRA.DISC': 'disclaimer', 'HALL.START': 'Hall', 'HALL.INTRO': 'Hall intro', 'FINAL.DARK': 'to black', 'FINAL.RETURN': 'return', 'FINAL.RESULTS': 'results',
    'FINAL.EXIT': 'Hall exit', 'FINAL.CREDITS': 'credits', 'FINAL.FADE': 'fade', 'OBRA.END': 'end', 'SHARE.ASK': 'share asked', 'SHARE.YES': 'share', 'SHARE.NO': "don't share" };
  const RE = /^(OBRA\.(DISC|END)|HALL\.(START|INTRO)|HALL\.[123]\.\d{1,2}|S[0-4]\.(OPEN|ALMA|INTRO|BEGIN|OUTRO|CHARGE|BYE|REQEND)|FINAL\.(DARK|RETURN|RESULTS|EXIT|CREDITS|FADE)|SHARE\.(ASK|YES|NO))$/;
  const num = v => (v === null || v === undefined || v === '' || !Number.isFinite(+v)) ? null : +v;

  /* the last stage has no farewell: phase 8 of K=4 goes straight to phase 10 */
  const isValid = n => typeof n === 'string' && RE.test(n) && n !== 'S4.BYE';
  /* a sub-mark lives inside a phase (Hall steps, the close request, SHARE); a phase mark is one phase change of RunObra
     (OBRA.END, derived from FINAL.FADE + Fundido_Dur, counts as one) */
  const isSub = n => isValid(n) && (/^HALL\.([123]\.\d+|INTRO)$/.test(n) || /\.REQEND$/.test(n) || /^SHARE\./.test(n));
  const isPhase = n => isValid(n) && !isSub(n);
  function fromPhase(fase, etapa) {
    const p = PHASE[num(fase)]; if (!p || p.legacy) return null;
    const K = num(etapa), n = p.mark || (K != null && Number.isInteger(K) ? 'S' + K + '.' + p.step : null);
    return n && isValid(n) ? n : null;
  }
  /* canonical order (design A §1.2): OBRA.DISC < HALL.START < HALL.INTRO < HALL.<mode>.<step> < S0.OPEN … S4.CHARGE < FINAL.DARK
     < FINAL.RETURN < FINAL.RESULTS < SHARE.* < FINAL.EXIT < FINAL.CREDITS < FINAL.FADE < OBRA.END. null when not a mark */
  function rank(n) {
    if (!isValid(n)) return null;
    if (n === 'OBRA.DISC') return 0;
    if (n === 'HALL.START') return 1000;
    if (n === 'HALL.INTRO') return 1001;
    let m = n.match(/^HALL\.(\d)\.(\d+)$/); if (m) return 1000 + +m[1] * 100 + +m[2];
    m = n.match(/^S(\d)\.(\w+)$/); if (m) return 10000 + +m[1] * 100 + STEPS.indexOf(m[2]);
    return 20000 + TAIL.indexOf(n);
  }
  const stageOf = n => { const m = isValid(n) && n.match(/^S(\d)\./); return m ? +m[1] : null; };
  const stepOf = n => { const m = isValid(n) && n.match(/^S\d\.(\w+)$/); return m ? m[1] : null; };
  /* a mark in words: short for the lane ("S1 begin", "Hall step 6"), long for tooltips ("Recognizing · the mechanic") */
  function label(n) {
    if (WORD[n]) return WORD[n];
    const h = String(n).match(/^HALL\.(\d)\.(\d+)$/); if (h) return 'Hall step ' + h[2] + (h[1] !== '1' ? ' (mode ' + h[1] + ')' : '');
    const K = stageOf(n), st = stepOf(n);
    return K != null ? 'S' + K + ' ' + (st === 'REQEND' ? 'close asked' : st.toLowerCase()) : String(n);
  }
  function describe(n) {
    const K = stageOf(n), st = stepOf(n);
    if (K != null) { const p = Object.values(PHASE).find(x => x.step === st); return STAGES[K] + ' · ' + (p ? p.what : st === 'REQEND' ? 'the director asks the stage to close' : st.toLowerCase()); }
    const p = Object.values(PHASE).find(x => x.mark === n);
    if (p) return p.what;
    if (n === 'OBRA.END') return 'the end of the piece';
    if (/^HALL\./.test(n)) return 'the Hall';
    if (/^SHARE\./.test(n)) return 'the SHARE choice';
    return String(n);
  }

  /* ---------- the Unreal run (obra/unreal/traza.json) ----------
     Today's shape: { generado: "20261002-185938", speed, nota, fases: [{fase, etapa, pared_s, reloj_obra_s, speed}] }.
     Optional fields the director may add (design A §6.8), all read when present: config {bSimulated, bDisclaimer, Speed,
     DebugStart}, partitura_hash, hall [{mode|modo, step|paso, reloj_obra_s|pared_s}], vo [{clip, reloj_obra_s, dur}],
     marks [{name, reloj_obra_s}] (S<K>.REQEND…), history|historial|runs [earlier runs inline, or their file names]. */
  const liveVal = (live, k) => { const v = live ? (live.valores || live.values || live) : null; return v && num(v[k]) != null ? num(v[k]) : null; };
  const rowsOf = traza => (traza && Array.isArray(traza.fases) ? traza.fases : []).filter(f => f && typeof f === 'object');
  /* one clock per run: the director's (reloj_obra_s = TourT) when every row has it, otherwise the wall clock (pared_s) */
  const wallClock = traza => rowsOf(traza).some(f => num(f.reloj_obra_s) == null);
  const tOf = (o, wall) => { const t = num(wall ? (o.pared_s != null ? o.pared_s : o.t) : (o.reloj_obra_s != null ? o.reloj_obra_s : o.t)); return t != null && t >= 0 ? t : null; };   // pared_s -1 = unknown
  function traceMarks(traza, live) {
    const out = [], wall = wallClock(traza);
    for (const f of rowsOf(traza)) {
      const mark = fromPhase(f.fase, f.etapa), t = tOf(f, wall);
      if (!mark || t == null) continue;
      out.push({ mark, t, fase: num(f.fase), etapa: num(f.etapa) });
    }
    const fade = out.filter(m => m.mark === 'FINAL.FADE').pop(), fd = liveVal(live, 'Fundido_Dur');
    if (fade && fd != null) out.push({ mark: 'OBRA.END', t: fade.t + fd, fase: null, etapa: null, derived: true });
    return out;
  }
  /* the sub-marks a run may carry (Hall steps, S<K>.REQEND…), on the same clock as its phases */
  function traceSubs(traza) {
    if (!traza) return [];
    const wall = wallClock(traza), out = [];
    for (const h of Array.isArray(traza.hall) ? traza.hall : []) {
      if (!h) continue; const mode = num(h.mode != null ? h.mode : h.modo), step = num(h.step != null ? h.step : h.paso), t = tOf(h, wall);
      const name = 'HALL.' + (mode == null ? 1 : mode) + '.' + step;
      if (step != null && t != null && isValid(name)) out.push({ mark: name, t });
    }
    for (const m of Array.isArray(traza.marks) ? traza.marks : []) { const t = m && tOf(m, wall); if (m && isValid(m.name) && t != null) out.push({ mark: m.name, t }); }
    return out.sort((a, b) => a.t - b.t);
  }
  /* "20261002-185938" (local time, as smoke_obra.py writes it) or an ISO string → "2026-10-02T18:59:38", never a Date
     (both sides of every comparison are the director's local time) */
  function isoOf(s) {
    s = String(s || '');
    let m = s.match(/^(\d{4})(\d{2})(\d{2})[-_T]?(\d{2})(\d{2})(\d{2})/); if (m) return `${m[1]}-${m[2]}-${m[3]}T${m[4]}:${m[5]}:${m[6]}`;
    m = s.match(/^(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2})(:\d{2})?/); return m ? `${m[1]}T${m[2]}${m[3] || ':00'}` : null;
  }
  const truthy = v => v == null ? null : v === true || v === 1 || /^(true|1|yes|s[ií])$/i.test(String(v).trim());
  function traceInfo(traza) {
    if (!traza || !Array.isArray(traza.fases)) return null;
    const c = traza.config && typeof traza.config === 'object' ? traza.config : {};
    const pick = (...v) => v.find(x => x !== undefined && x !== null);
    const rows = rowsOf(traza), first = rows.find(f => num(f.speed) != null);
    const sim = truthy(pick(c.bSimulated, c.simulated, c.Simulated, traza.simulado, traza.simulated));
    const disc = truthy(pick(c.bDisclaimer, c.disclaimer, c.Disclaimer, traza.disclaimer));
    const hist = pick(traza.history, traza.historial, traza.runs);
    const seen = new Set(), dup = [];
    for (const f of rows) { const n = fromPhase(f.fase, f.etapa); if (n && seen.has(n)) dup.push(n); if (n) seen.add(n); }
    return {
      generated: traza.generado || traza.generated || null, at: isoOf(traza.generado || traza.generated),
      speed: num(pick(c.Speed, c.speed, traza.speed, first && first.speed)),
      // only tools/unreal/smoke_obra.py writes it, always with -ObraSmoke (simulated signals): simulated unless it says otherwise
      sim: sim == null ? true : sim, simSaid: sim != null,
      disclaimer: disc == null ? rows.some(f => num(f.fase) === 16) : disc,
      clock: wallClock(traza) ? 'wall' : 'director',
      hash: pick(traza.partitura_hash, traza.partituraHash, c.partitura_hash) || null,
      config: traza.config || null,
      phases: rows.length, marks: seen.size, dup,
      unknown: rows.filter(f => !fromPhase(f.fase, f.etapa)).map(f => ({ fase: num(f.fase), etapa: num(f.etapa) })),
      subs: traceSubs(traza).length, vo: Array.isArray(traza.vo) ? traza.vo.length : 0,
      history: Array.isArray(hist) ? hist.filter(h => h && typeof h === 'object' && Array.isArray(h.fases)) : [],
      historyFiles: Array.isArray(hist) ? hist.filter(h => typeof h === 'string') : [],
    };
  }

  /* ---------- where each mark falls in the score ----------
     { name: t } for the marks that have a time (rel 'start': the moment's start; rel 'el': that element's edge), plus OBRA.END
     = the end of the score. `info` (optional) gets: from ('score' | 'seed'), beat {name: moment id}, issues [{mark, beat, why}]
     (a mark whose element left its moment, a moment that no longer exists, a name placed twice: the first one counts) */
  function scoreMarks(score, sched, seed, info) {
    const out = {}, inf = info || {}, B = score.beats, E = score.elements, T = sched.t;
    // schema 3 reads the marks it carries (beats[].marks, from "Bind to Unreal"); one that does not carry any yet (upgraded, not bound) still reads the seed
    inf.from = score.schema >= 3 && Object.values(B).some(b => Array.isArray(b.marks) && b.marks.length) ? 'score' : 'seed'; inf.beat = {}; inf.issues = [];
    const src = inf.from === 'score' ? null : (seed && seed.beats) || {};
    const listOf = b => inf.from === 'score' ? (B[b] || {}).marks : (src[b] || {}).marks;
    const keyOf = b => (B[b] || (src && src[b]) || {}).key || b;
    for (const b of score.acts.flatMap(a => a.beats)) {
      const list = listOf(b); if (!Array.isArray(list)) continue;
      for (const m of list) {
        if (!m || (m.rel !== 'start' && m.rel !== 'el')) continue;
        if (!isValid(m.name)) { inf.issues.push({ mark: String(m.name), beat: b, why: `${m.name} is not a mark Unreal emits` }); continue; }
        let t = null;
        if (m.rel === 'start') t = T[b] ? T[b][0] : null;
        else {
          const e = E[m.el];
          if (!e || e.beat !== b || !T[m.el]) { inf.issues.push({ mark: m.name, beat: b, why: e ? `${e.key} is no longer in moment ${keyOf(b)}` : `its element ${m.elKey || m.el} in moment ${keyOf(b)} no longer exists` }); continue; }
          t = T[m.el][m.edge === 'end' ? 1 : 0];
        }
        if (t == null || !Number.isFinite(t)) continue;
        if (m.name in out) { inf.issues.push({ mark: m.name, beat: b, why: `${m.name} is placed twice (moments ${keyOf(inf.beat[m.name])} and ${keyOf(b)}): the first one counts` }); continue; }
        out[m.name] = t; inf.beat[m.name] = b;
      }
    }
    if (src) for (const b of Object.keys(src)) if (!B[b]) for (const m of (src[b].marks || [])) if (m && (m.rel === 'start' || m.rel === 'el') && !(m.name in out))
      inf.issues.push({ mark: m.name, beat: b, why: `its moment ${src[b].key || b} no longer exists` });
    if (!('OBRA.END' in out) && Number.isFinite(sched.total)) out['OBRA.END'] = sched.total;
    return out;
  }

  const api = { PHASE, STAGES, STEPS, isValid, isSub, isPhase, fromPhase, rank, stageOf, stepOf, label, describe, isoOf, liveVal, traceMarks, traceSubs, traceInfo, scoreMarks };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.Marks = api;
})(typeof window !== 'undefined' ? window : globalThis);
