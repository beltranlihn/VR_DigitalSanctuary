/* Veation VR Studio · CALIB: the score against the last Unreal run (obra/unreal/traza.json), lote 5 design A §6. Pure (no
   DOM): it runs in the browser and in Node (tools/score/calib_test.mjs). Both timelines are aligned at the Hall start (the
   smoke test runs without the disclaimer); every mark Unreal logged is compared with where the score places it
   (Marks.scoreMarks), segment by segment (a mark → the next one) and section by section (the Hall, each stage, the final).
   Measured with the typical user, like everything that is checked. It never changes the score: there is no "match the
   score to the Unreal run" (owner decision D-4). */
(function (root) {
  'use strict';
  const Marks = root.Marks || (typeof require === 'function' ? require('./marks.js') : null);

  // thresholds: owner decision D-3 (design A §6.5). Proposals; change them here. With two runs or more of the same kind the
  // noise between them raises them (max(threshold, 3σ)), never lowers them
  const X_STAGE = 3;     // s · a section (the Hall, a stage, the final) differs more than this → warning C3.TRACE.STAGE
  const X_SEG = 1;       // s · a segment (a mark → the next) differs more than this → info C3.TRACE.SEG, only under "Unreal run"
  const ALIGN = 'HALL.START';
  const SIM_FROM = 3;    // with bSimulated the director asks Attracting (3) and Surrounding (4) to close at Sim_EtapaMax
  const SECTIONS = [
    { id: 'HALL', name: 'Hall', from: 'HALL.START', to: 'S0.OPEN' },
    { id: 'S0', name: 'Entering', from: 'S0.OPEN', to: 'S1.OPEN' },
    { id: 'S1', name: 'Recognizing', from: 'S1.OPEN', to: 'S2.OPEN' },
    { id: 'S2', name: 'Loving', from: 'S2.OPEN', to: 'S3.OPEN' },
    { id: 'S3', name: 'Attracting', from: 'S3.OPEN', to: 'S4.OPEN' },
    { id: 'S4', name: 'Surrounding', from: 'S4.OPEN', to: 'FINAL.DARK' },
    { id: 'FINAL', name: 'Final', from: 'FINAL.DARK', to: 'OBRA.END' },
  ];
  // why a segment may differ, by the mark it starts at (a stage step stands for the five stages), design A §6.4
  const CAUSES = {
    'HALL.START': "The Hall: in Unreal the user's waits (bell, sensor, choice) set it.",
    OPEN: 'Alma enters at Alma_Entra in Unreal (the Timing tab shows the same difference).',
    ALMA: "Alma's welcome: her voice plus Alma_TrasVoz in Unreal.",
    INTRO: 'The instructions: Instr_Dur in Unreal (Attracting also waits for its voices, up to Instr_EsperaMax).',
    BEGIN: 'The mechanic: in Unreal the stage closes by its own path, or is asked to at Etapa_Tope.',
    OUTRO: "Unreal plays Alma's congratulation in the outro, before the charge; the score has it after the charge.",
    CHARGE: 'The charge: Carga_Dur in Unreal.',
    BYE: "In Unreal Alma's congratulation already played before the charge, and the veil closes in Velo_CierreDur.",
    'FINAL.DARK': 'To black: Unreal jumps to the Hall at Regreso_HallA.',
    'FINAL.RETURN': 'The return: the Regreso_* knobs in Unreal.',
    'FINAL.RESULTS': "The results and SHARE: the Res_* knobs and the user's choice.",
    'FINAL.EXIT': 'The Hall exit: a simulated run leaves it almost at once.',
    'FINAL.CREDITS': 'The credits: Creditos_Dur in Unreal.',
    'FINAL.FADE': 'The fade: Fundido_Dur in Unreal.',
  };
  const f1 = v => (Math.round(v * 10) / 10).toFixed(1);
  const sgn = v => (v >= 0 ? '+' : '−') + f1(Math.abs(v));
  const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  /* "2026-10-02T18:59:38" → "2 Oct 18:59" */
  const when = iso => { const m = String(iso || '').match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/); return m ? `${+m[3]} ${MON[+m[2] - 1]} ${m[4]}:${m[5]}` : ''; };
  /* the header of the lane: "Unreal run · 2 Oct 18:59 · speed 1 · simulated" (short: the first two) */
  function runLabel(info, o) {
    const p = ['Unreal run']; if (!info) return p[0];
    if (when(info.at)) p.push(when(info.at));
    if (o && o.short) return p.join(' · ');
    if (info.speed != null) p.push('speed ' + +(+info.speed).toFixed(2));
    if (info.sim) p.push('simulated');
    return p.join(' · ');
  }

  /* sm = Marks.scoreMarks(...) ({name: t}), tm = Marks.traceMarks(...) ([{mark, t}] in the run's order, OBRA.END last).
     opt = { info: Marks.traceInfo(traza), live: obra/unreal/partitura.json, align }
     → { offset, comparable, rows: [{mark, to, score, trace, d, segScore, segTrace, dSeg, sim, cause}], sections: [{id, name,
         from, to, score, trace, d, sim}], unmeasured: [{id, name, from, to, trace, lost}] (sections the run has and the score
         no longer places a mark of), total, missing (score marks the run never reached), extra (run marks the score does
         not place), stale: [{code, msg}], marks (sm), trace ({name: t} of the run), info, simCap }
     d = score − Unreal run: negative when the score is shorter. A segment goes from a mark to the next mark that both
     timelines have, in the run's order. */
  function compare(sm, tm, opt) {
    opt = opt || {}; sm = sm || {};
    const info = opt.info || {}, live = opt.live || null, align = opt.align || ALIGN;
    const cap = Marks.liveVal(live, 'Sim_EtapaMax');
    const res = { align, offset: null, comparable: true, rows: [], sections: [], unmeasured: [], total: null, missing: [], extra: [], stale: [], marks: sm, trace: {}, info, simCap: cap };
    const T = res.trace, seq = [];
    for (const m of tm || []) if (m && !(m.mark in T)) { T[m.mark] = m.t; seq.push(m); }
    const stale = (code, msg) => res.stale.push({ code, msg });
    if (info.speed != null && Math.abs(info.speed - 1) > 1e-6) {
      res.comparable = false;
      stale('speed', `The last Unreal run went at speed ${+(+info.speed).toFixed(2)}: the director's clock ran faster than the mechanics, so its durations do not compare with the score. A run to compare: python tools/unreal/smoke_obra.py --speed 1 --traza.`);
    }
    if (info.clock === 'wall') stale('clock', 'The run has no director clock (reloj_obra_s): its wall clock is used, up to one frame off per mark.');
    const exp = live && Marks.isoOf(live.exportado);
    if (exp && info.at && exp > info.at) stale('older', `The last Unreal run (${when(info.at)}) is older than the Unreal timing export (${when(exp)}): the knobs may have changed after it.`);
    if (info.hash && live && live.hash && info.hash !== live.hash) stale('hash', `The last Unreal run was made with DA_Partitura_Obra ${info.hash}; Unreal has ${live.hash} now.`);
    if (info.sim) stale('sim', `Simulated run (smoke test): Attracting and Surrounding were asked to close at ${cap != null ? cap + ' s' : 'Sim_EtapaMax'} (Sim_EtapaMax), not by a user, so their mechanic is shown but not compared.`);
    if (info.unknown && info.unknown.length) stale('unknown', `${info.unknown.length} phase change${info.unknown.length > 1 ? 's' : ''} of the run ${info.unknown.length > 1 ? 'are' : 'is'} not a mark the editor knows (${info.unknown.map(u => 'phase ' + u.fase + (u.etapa != null ? ' stage ' + u.etapa : '')).join(', ')}).`);
    if (!(align in T) || !(align in sm)) {
      res.comparable = false;
      stale('align', !(align in sm) ? `The score places no ${Marks.label(align)} mark (is obra/score/seed/marks-v1.json there?): the run has nothing to be aligned with.` : 'The Unreal run never reached the Hall start: nothing to align it with.');
      return res;
    }
    if (!('OBRA.END' in T) && 'FINAL.FADE' in T) stale('end', 'The end of the run is FINAL.FADE + Fundido_Dur, and Fundido_Dur is unknown (obra/unreal/partitura.json missing): the final is not compared.');
    const off = res.offset = sm[align] - T[align];
    const both = seq.filter(m => m.mark in sm);
    for (const m of seq) if (!(m.mark in sm)) res.extra.push(m.mark);
    for (const n of Object.keys(sm)) if (!(n in T) && Marks.isPhase(n) && n !== 'OBRA.END' && !(n === 'OBRA.DISC' && !info.disclaimer)) res.missing.push(n);
    res.missing.sort((a, b) => Marks.rank(a) - Marks.rank(b));
    for (let i = 0; i < both.length; i++) {
      const m = both[i], nx = both[i + 1]; if (m.mark === 'OBRA.END') continue;   // the end closes the last segment
      const K = Marks.stageOf(m.mark), st = Marks.stepOf(m.mark);
      const r = { mark: m.mark, to: nx ? nx.mark : null, score: sm[m.mark], trace: m.t + off, d: sm[m.mark] - (m.t + off), segScore: null, segTrace: null, dSeg: null,
        sim: !!info.sim && st === 'BEGIN' && K >= SIM_FROM, cause: CAUSES[m.mark] || CAUSES[st] || '' };
      if (nx) { r.segScore = sm[nx.mark] - sm[m.mark]; r.segTrace = nx.t - m.t; r.dSeg = r.segScore - r.segTrace; }
      res.rows.push(r);
    }
    for (const S of SECTIONS) {
      // the run measured it but the score lost one of its marks (its element or moment deleted): the section cannot be
      // compared any more, and that is said as loudly as the difference was (it never just disappears)
      if (S.from in T && S.to in T && !(S.from in sm && S.to in sm)) { res.unmeasured.push({ id: S.id, name: S.name, from: S.from, to: S.to, trace: T[S.to] - T[S.from], lost: [S.from, S.to].filter(n => !(n in sm)) }); continue; }
      if (!(S.from in sm && S.to in sm && S.from in T && S.to in T)) continue;
      const a = sm[S.to] - sm[S.from], b = T[S.to] - T[S.from], r0 = Marks.rank(S.from), r1 = Marks.rank(S.to);
      res.sections.push({ id: S.id, name: S.name, from: S.from, to: S.to, score: a, trace: b, d: a - b, sim: res.rows.some(r => r.sim && Marks.rank(r.mark) >= r0 && Marks.rank(r.mark) < r1) });
    }
    if ('OBRA.END' in sm && 'OBRA.END' in T) {
      const a = sm['OBRA.END'] - sm[align], b = T['OBRA.END'] - T[align];
      res.total = { from: align, to: 'OBRA.END', score: a, trace: b, d: a - b };
    }
    return res;
  }

  /* how much two runs or more of the same piece differ by themselves (rule "a baseline is two runs"): the largest sample
     standard deviation of a segment, and of a section. runs = [Marks.traceMarks(...), …]; null with fewer than two */
  function noise(runs) {
    runs = (runs || []).filter(r => Array.isArray(r) && r.length); if (runs.length < 2) return null;
    const sd = xs => { const n = xs.length, m = xs.reduce((a, b) => a + b, 0) / n; return Math.sqrt(xs.reduce((a, x) => a + (x - m) * (x - m), 0) / (n - 1)); };
    const segs = {}, secs = {};
    for (const run of runs) {
      const T = {}, seq = []; for (const m of run) if (!(m.mark in T)) { T[m.mark] = m.t; seq.push(m); }
      for (let i = 0; i + 1 < seq.length; i++) { const k = seq[i].mark + '>' + seq[i + 1].mark; (segs[k] = segs[k] || []).push(seq[i + 1].t - seq[i].t); }
      for (const S of SECTIONS) if (S.from in T && S.to in T) (secs[S.id] = secs[S.id] || []).push(T[S.to] - T[S.from]);
    }
    const mx = o => Math.max(0, ...Object.values(o).filter(v => v.length >= 2).map(sd));
    return { runs: runs.length, seg: mx(segs), stage: mx(secs) };
  }
  function thresholds(nz, opt) {
    opt = opt || {};
    const xs = opt.xStage != null ? opt.xStage : X_STAGE, xg = opt.xSeg != null ? opt.xSeg : X_SEG;
    return { xStage: nz ? Math.max(xs, 3 * nz.stage) : xs, xSeg: nz ? Math.max(xg, 3 * nz.seg) : xg, noise: nz || null };
  }

  /* the comparison as problems, Integrity's shape ({fp, sv, ly, rule, msg, el, own, st}) plus: grp 'run' (the "Unreal run"
     filter), span [mark, mark] (Show in timeline), where (the section or the mark, in words), only 'run' for the segment
     rows (alert fatigue, audit B2: they are listed only under that filter), lost (the marks a section can no longer be
     measured by: C3.TRACE.STAGE|<id>|lost:<marks>, a warning too).
     opt = { xStage, xSeg, noise, accepted (score.accepted), issues (from Marks.scoreMarks) } */
  function problems(cmp, opt) {
    opt = opt || {};
    const P = []; if (!cmp) return P;
    const th = thresholds(opt.noise, opt), own = runLabel(cmp.info, { short: true }), cap = cmp.simCap != null ? cmp.simCap + ' s' : 'Sim_EtapaMax';
    const add = (sv, rule, slot, param, msg, x) => P.push(Object.assign({ fp: rule + '|' + slot + '|' + param, sv, ly: 'C3', rule, msg, el: null, own, grp: 'run' }, x || {}));
    for (const s of cmp.stale) add('info', 'C3.TRACE.STALE', '', s.code, s.msg);
    const issues = opt.issues || [], why = {};
    for (const i of issues) if (!why[i.mark]) why[i.mark] = i;
    if (cmp.comparable) {
      // a section the score can no longer measure (it lost one of its marks) warns too: deleting the element that carries a
      // stage mark must not make a stage warning silently disappear
      for (const u of cmp.unmeasured || []) {
        const n = u.lost[0];
        add('warn', 'C3.TRACE.STAGE', u.id, 'lost:' + u.lost.join('+'), `${u.name} can no longer be compared with the last Unreal run (${f1(u.trace)} s there): the score does not place ${u.lost.map(x => `${Marks.label(x)} (${Marks.describe(x)})`).join(' nor ')} any more${why[n] ? ': ' + why[n].why : ''}.`,
          { where: u.name, el: why[n] ? why[n].beat : null, lost: u.lost.slice() });
      }
      // the fingerprint carries the rounded difference: an accepted one opens again when it moves 1 s (audit A6/B5)
      for (const s of cmp.sections) if (Math.abs(s.d) > th.xStage)
        add('warn', 'C3.TRACE.STAGE', s.id, Math.round(s.d), `${s.name} runs ${f1(s.score)} s here; the last Unreal run took ${f1(s.trace)} s (${sgn(s.d)} s).`
          + (s.sim ? ` The run was simulated: its mechanic was asked to close at ${cap}, not by a user.` : ''), { span: [s.from, s.to], where: s.name });
      for (const r of cmp.rows) if (!r.sim && r.dSeg != null && Math.abs(r.dSeg) > th.xSeg)
        add('info', 'C3.TRACE.SEG', r.mark, Math.round(r.dSeg), `${Marks.label(r.mark)} → ${Marks.label(r.to)}: ${f1(r.segScore)} s here, ${f1(r.segTrace)} s in the Unreal run (${sgn(r.dSeg)} s).${r.cause ? ' ' + r.cause : ''}`,
          { span: [r.mark, r.to], where: Marks.label(r.mark), only: 'run' });
    }
    for (const n of cmp.missing) add('info', 'C3.TRACE.MISSING', n, 'run', `The last Unreal run never reached ${Marks.label(n)} (${Marks.describe(n)}).`, { where: Marks.label(n) });
    for (const n of cmp.extra) add('info', 'C3.TRACE.MISSING', n, 'score', `The Unreal run has ${Marks.label(n)} (${Marks.describe(n)}) but the score does not place it${why[n] ? ': ' + why[n].why : ''}.`, { where: Marks.label(n), el: why[n] ? why[n].beat : null });
    for (const i of issues) if (!cmp.extra.includes(i.mark)) add('info', 'C3.TRACE.MARK', i.beat, i.mark, `${i.why}.`, { el: i.beat, where: Marks.label(i.mark) });
    // accepted means this value (design B §9): the record of the stage, accepted at the rounded difference, answers while it holds;
    // 1 s further and the row is open again and says what it was accepted at
    const Int = root.Integrity || (typeof require === 'function' ? require('./integrity.js') : null);
    return Int.judge(P, opt.accepted || []);
  }

  /* the status bar pill: "Unreal run · −24.7 s" (the score minus the run, Hall start → end) */
  function pillText(cmp) {
    if (!cmp) return '';
    if (!cmp.comparable) return 'Unreal run · not comparable';
    return cmp.total ? 'Unreal run · ' + sgn(cmp.total.d) + ' s' : 'Unreal run';
  }

  /* what the "Unreal run" lane of the ruler draws, in seconds (ui.js only turns them into pixels). mode 'mark' (default):
     each segment starts at the score's mark and lasts what Unreal took, so a bar that goes past the score's next mark is an
     overrun ('over') and one that stops short leaves a 'gap'; 'hall': the run as it happened, aligned at the Hall start.
     kinds: tick (a mark), bar, over, gap, sim (a simulated mechanic), order (the score has the next mark before this one);
     big = the segment differs more than the segment threshold */
  function lane(cmp, mode, opt) {
    const out = []; if (!cmp || cmp.offset == null) return out;
    const xg = thresholds(opt && opt.noise, opt).xSeg, abs = mode === 'hall';
    for (const r of cmp.rows) {
      const s = abs ? r.trace : r.score;
      out.push({ kind: 'tick', s, mark: r.mark });
      if (r.segTrace == null) continue;
      const e = s + r.segTrace, big = !r.sim && Math.abs(r.dSeg) > xg;
      if (r.sim) { out.push({ kind: 'sim', s, e, row: r, big: false }); continue; }
      if (abs) { out.push({ kind: 'bar', s, e, row: r, big }); continue; }
      const nx = r.score + r.segScore;
      if (r.segScore < -1e-6) { out.push({ kind: 'order', s, e, row: r, big: true }); continue; }
      if (Math.min(e, nx) > s + 1e-6) out.push({ kind: 'bar', s, e: Math.min(e, nx), row: r, big });
      if (e > nx + 1e-6) out.push({ kind: 'over', s: nx, e, row: r, big });
      else if (e < nx - 1e-6) out.push({ kind: 'gap', s: e, e: nx, row: r, big });
    }
    const end = abs ? (cmp.trace['OBRA.END'] != null ? cmp.trace['OBRA.END'] + cmp.offset : null) : cmp.marks['OBRA.END'];
    if (end != null && cmp.rows.some(r => r.to === 'OBRA.END')) out.push({ kind: 'tick', s: end, mark: 'OBRA.END' });
    return out;
  }

  const api = { X_STAGE, X_SEG, ALIGN, SIM_FROM, SECTIONS, CAUSES, compare, noise, thresholds, problems, pillText, runLabel, when, lane };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.Calib = api;
})(typeof window !== 'undefined' ? window : globalThis);
