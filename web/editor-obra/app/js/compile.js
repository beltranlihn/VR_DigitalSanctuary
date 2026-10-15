/* Veation VR Studio · COMPILE: the dry run of the score against Unreal (lote 5 design A §5). Pure (no DOM, no files): it runs in
   Node (tools/score/compile.mjs is its command line, tools/score/compile_test.mjs its tests) and could run in the browser, so
   the app can show the same manifest. It reads, reports and refuses; it never writes anything and it applies nothing to Unreal.
   compile(inputs, options) → the manifest:
     refused    what stops a real compile (a cycle of anchors, an anchor to nothing, a mark that Unreal does not emit, placed twice
                or out of order, a sound whose name two files answer to): { code, id?, key?, msg }, in the order of the piece
     warnings   what does not stop it (W_MARK_MISSING, W_MARK_TIE, W_NO_IDMAP…)
     summary    the elements by where they stand with Unreal (js/reach.js): knob, wired, cue (bound and ready), cueReady (cue + what
                would be one once the score is bound), preview
     marks      where the score places each Unreal mark (typical user)
     knobs      the Partitura knobs whose value in Unreal differs from what the score does (what Send to Unreal could carry)
     cues       the elements a cue player could fire: { id, key, mark, offset, action, target, asset, path, state }
     wired      the elements Unreal decides by itself, with who
     preview    the elements only the editor and the 3D know, with the first reason
     trace      the score against the last Unreal run (js/calib.js), when there is one
   The marks of a schema 3 score are the ones it carries (beats[].marks); a schema 2 score has none, so the seed
   (obra/score/seed/marks-v1.json) is read instead and the manifest says so (inputs.score.marksFrom: 'seed'): the dry run is useful
   before the score is bound. Nothing here knows about files: the command line reads them and hands them in. Deterministic: the
   same inputs give the same manifest, apart from `generated`. */
(function (root) {
  'use strict';
  const dep = (file, name) => (typeof require === 'function' && typeof module !== 'undefined' ? require('./' + file) : root[name]);
  const r4 = x => Math.round(x * 10000) / 10000;
  const has = (o, k) => !!o && Object.prototype.hasOwnProperty.call(o, k);
  const TIE = 1e-3;                         // two phase marks closer than this are at the same time
  const VERSION = 'compile.mjs 1';

  /* a mistake in what was handed in (not a verdict about the piece): the command line says it and exits 1 */
  class BadInput extends Error { constructor(msg) { super(msg); this.name = 'BadInput'; } }

  /* every phase mark Unreal's director enters in a complete run, in order (S4.BYE does not exist: the last stage has no farewell) */
  function expectedMarks(Marks) {
    const out = ['OBRA.DISC', 'HALL.START'];
    for (let K = 0; K < Marks.STAGES.length; K++) for (const st of Marks.STEPS) if (st !== 'REQEND' && !(K === Marks.STAGES.length - 1 && st === 'BYE')) out.push('S' + K + '.' + st);
    return out.concat(['FINAL.DARK', 'FINAL.RETURN', 'FINAL.RESULTS', 'FINAL.EXIT', 'FINAL.CREDITS', 'FINAL.FADE']);
  }

  function compile(inp, opt) {
    opt = opt || {};
    const Engine = opt.Engine || dep('engine.js', 'ScoreEngine'), Edits = opt.Edits || dep('edits.js', 'Edits'), Marks = opt.Marks || dep('marks.js', 'Marks');
    const Reach = opt.Reach || dep('reach.js', 'Reach'), Partitura = opt.Partitura || dep('partitura.js', 'Partitura'), Calib = opt.Calib || dep('calib.js', 'Calib');
    const Integrity = opt.Integrity || dep('integrity.js', 'Integrity');
    const score = inp && inp.score, sha = (inp && inp.sha12) || {};
    if (!score || typeof score !== 'object') throw new BadInput('There is no score to compile.');
    if (!inp.contract || !Array.isArray(inp.contract.entries)) throw new BadInput('The contract with Unreal (obra/unreal/contract.json) is missing or has no entries.');
    // 1 · the score must be one the editor can read (the same validation as the editor and the server: schema 2 or 3, marks and bind in 3)
    let T0; try { T0 = Edits.validate(score, Engine); } catch (e) { throw new BadInput('The score is not valid: ' + e.message); }
    const B = score.beats, E = score.elements, order = score.acts.flatMap(a => a.beats).filter(b => B[b]);
    const name = id => (B[id] ? 'Moment ' : '') + ((B[id] || E[id] || {}).key || id), key = id => (B[id] || E[id] || {}).key || id;
    const refused = [], warnings = [];
    const refuse = (code, o) => refused.push(Object.assign({ code }, o));
    const warn = (code, o) => warnings.push(Object.assign({ code }, o));
    // the four simulated users, once each: the reach rules and the persona spread read them
    const sched = { typical: T0 };
    for (const p of Object.keys(Engine.PERSONAS)) if (p !== 'typical') sched[p] = Engine.resolve(score, { persona: p });

    // 2 · a loop of anchors or an anchor to nothing, in any option of any decision: a cue cannot hang from a time that does not exist
    const cyc = new Map(), dang = new Map();
    const runs = [{ at: '', opt: { persona: 'typical' }, res: T0 }];
    for (const on of Object.keys(score.branches || {})) for (const o of Object.keys(score.branches[on].options)) runs.push({ at: ` when ${on} is ${o}`, opt: { persona: 'typical', branch: { [on]: o } } });
    for (const r of runs) {
      const res = r.res || Engine.resolve(score, r.opt);
      for (const id of res.cycles || []) if (!cyc.has(id)) cyc.set(id, r.at);
      for (const id of res.dangling || []) if (!dang.has(id)) dang.set(id, r.at);
    }
    const byTime = (a, b) => ((T0.t[a] || [0])[0] - (T0.t[b] || [0])[0]) || (a < b ? -1 : a > b ? 1 : 0);
    for (const id of [...cyc.keys()].sort(byTime)) refuse('E_CYCLE', { id, key: key(id), msg: B[id] ? `${name(id)} has an anchor loop${cyc.get(id)}: the moment that should follow it starts at the same time. Break the loop in Problems first.` : `${name(id)} is in an anchor loop${cyc.get(id)}: its time depends on itself. Break the loop in Problems first.` });
    for (const id of [...dang.keys()].sort(byTime)) refuse('E_DANGLING', { id, key: key(id), msg: `${name(id)} is anchored to something that no longer exists${dang.get(id)}.` });

    // 3 · the marks: a bound score carries them, anything else is read from the seed
    const info = {}, marksT = Marks.scoreMarks(score, T0, inp.seed || null, info), lists = Reach.markLists(score, inp.seed || null);
    const marks = [], placedBy = {};
    for (const b of order) {
      for (const m of lists.lists[b] || []) {
        if (!m) continue;
        if (!Marks.isValid(m.name)) { refuse('E_MARK_UNKNOWN', { id: b, key: key(b), mark: String(m.name), msg: `${name(b)} names ${m.name}, which is not a mark Unreal emits.` }); continue; }
        if (m.rel !== 'start' && m.rel !== 'el') continue;
        const e = m.rel === 'el' ? E[m.el] : null;
        if (m.rel === 'el' && (!e || e.beat !== b)) { refuse('E_MARK_ELEMENT', { id: b, key: key(b), mark: m.name, msg: `${m.name} is the edge of ${e ? e.key + ', which is no longer in ' + name(b) : 'an element that no longer exists'}.` }); continue; }
        if (has(placedBy, m.name)) { refuse('E_MARK_DUP', { id: b, key: key(b), mark: m.name, msg: `${m.name} is placed twice (${name(placedBy[m.name])} and ${name(b)}): Unreal enters it once.` }); continue; }
        placedBy[m.name] = b;
        marks.push(Object.assign({ name: m.name, beat: b, key: key(b), rel: m.rel }, m.rel === 'el' ? { el: m.el, elKey: e.key, edge: m.edge === 'end' ? 'end' : 'start' } : {}, { t: r4(marksT[m.name]) }));
      }
    }
    marks.sort((x, y) => x.t - y.t || Marks.rank(x.name) - Marks.rank(y.name));
    if (!marks.length) refuse('E_NO_MARKS', { msg: 'No moment is tied to an Unreal mark: the score is not bound to Unreal and there is no marks seed (obra/score/seed/marks-v1.json).' });
    // phase marks in the order Unreal enters them (ties are noted: INTRO and BEGIN of the last stage are 0.6 s apart in Unreal and meet when its moments start together)
    const phase = marks.filter(m => Marks.isPhase(m.name)).sort((x, y) => Marks.rank(x.name) - Marks.rank(y.name));
    for (let i = 1; i < phase.length; i++) {
      const a = phase[i - 1], b = phase[i], clock = t => Integrity.fmt(t);
      if (b.t < a.t - TIE) refuse('E_MARK_ORDER', { id: b.beat, key: b.key, mark: b.name, after: a.name, msg: `Unreal enters ${a.name} before ${b.name}, but in the score ${b.name} (${name(b.beat)}, ${clock(b.t)}) comes before ${a.name} (${name(a.beat)}, ${clock(a.t)}).` });
      else if (Math.abs(b.t - a.t) <= TIE) warn('W_MARK_TIE', { mark: b.name, after: a.name, key: b.key, msg: `${a.name} and ${b.name} are at the same time in the score (${clock(b.t)}): Unreal enters them one after the other.` });
    }
    const tinfo = inp.trace ? Marks.traceInfo(inp.trace) : null;
    const missingMarks = expectedMarks(Marks).filter(n => !has(placedBy, n) && !(n === 'OBRA.DISC' && !(tinfo && tinfo.disclaimer)));
    if (marks.length) for (const n of missingMarks) warn('W_MARK_MISSING', { mark: n, msg: `The score places no ${n} (${Marks.describe(n)}): its cues cannot be tied to it.` });

    // 4 · each element where it stands with Unreal (the same rules as the status bar and the inspector)
    if (!inp.idmap) warn('W_NO_IDMAP', { msg: 'The Unreal assets are not scanned (obra/unreal/idmap.json): no sound can be linked, so none is cue-ready.' });
    const gov = inp.binding && inp.def ? Partitura.governedBy(score, T0, inp.binding) : {};
    const ctx = Reach.context({ score, schedT: T0, contract: inp.contract, gov, idmap: inp.idmap || null, seed: inp.seed || null, roles: inp.roles || null, resolve: p => sched[p] });
    const R = Reach.all(ctx), ids = Object.keys(E).sort(byTime);
    const cues = [], wired = [], preview = [];
    for (const id of ids) {
      const r = R.of[id], e = E[id];
      if (r.reach === 'cue' || r.bindable) {
        const c = r.cue;
        cues.push({ id, key: e.key, mark: c.mark, offset: r4(c.offset), action: c.action, target: c.target || null, asset: c.asset || null, path: c.path || null, state: r.reach === 'cue' ? r.state : 'not-bound' });
      } else if (r.reach === 'wired') wired.push({ id, key: e.key, contract: r.contract || null, owner: r.owner || null, why: r.why });
      else if (r.reach === 'preview') {
        preview.push({ id, key: e.key, why: r.why });
        // 5 · a sound that two files answer to: never guessed, the owner picks one (the asset is ambiguous only if the element could be a cue)
        if (r.ambiguous) refuse('E_ASSET_AMBIGUOUS', { id, key: e.key, asset: r.asset, msg: `${e.key}: ${r.why}` });
      }
    }
    const C = R.counts, summary = { elements: ids.length, reach: { knob: C.knob, wired: C.wired, cue: C.cue, cueReady: C.cue + C.bindable, preview: C.preview - C.bindable } };

    // 6 · the knob channel: what Send to Unreal could carry (compile never writes the proposal)
    const knobs = [];
    if (inp.def && inp.binding) for (const r of Partitura.drift(score, T0, inp.def, inp.live || null, inp.binding).rows) {
      if (r.missing || r.diff == null || r.diff === 0) continue;
      knobs.push({ knob: r.knob, stage: r.stage == null ? null : r.stage, score: r4(r.score), live: r4(r.da), diff: r4(r.diff), els: r.els.slice() });
    }

    // 7 · the last Unreal run, mark by mark (optional)
    let trace = null;
    if (tinfo) {
      const cmp = Calib.compare(marksT, Marks.traceMarks(inp.trace, inp.live || null), { info: tinfo, live: inp.live || null });
      trace = { offset: cmp.offset == null ? null : r4(cmp.offset), comparable: cmp.comparable, sections: cmp.sections.map(s => ({ name: s.name, score: r4(s.score), unreal: r4(s.trace), d: r4(s.d) })), total: cmp.total ? { score: r4(cmp.total.score), unreal: r4(cmp.total.trace), d: r4(cmp.total.d) } : null };
    }

    const p = inp.live;
    return {
      compiler: VERSION, generated: opt.now || new Date().toISOString(), dryRun: true,
      inputs: {
        score: { schema: score.schema, rev: score.rev == null ? null : score.rev, sha12: sha.score || null, marksFrom: info.from },
        idmap: inp.idmap ? { generated: inp.idmap.generated || null, sha12: sha.idmap || null } : null,
        contract: { sha12: sha.contract || null },
        partitura: p ? { hash: p.hash || null, exported: p.exportado || null } : null,
        trace: tinfo ? { generated: tinfo.generated, speed: tinfo.speed, sim: tinfo.sim } : null,
        seed: inp.seed ? { version: inp.seed.version == null ? null : inp.seed.version, status: inp.seed.status || null, sha12: sha.seed || null } : null,
      },
      ok: refused.length === 0, refused, warnings, summary, marks, knobs, cues, wired, preview, trace,
    };
  }

  /* one line for a person: what the manifest says (the command line prints it on stderr) */
  function summaryText(m) {
    const r = m.summary.reach, codes = {};
    for (const x of m.refused) codes[x.code] = (codes[x.code] || 0) + 1;
    const why = Object.entries(codes).map(([c, n]) => c + (n > 1 ? ' ×' + n : '')).join(', ');
    return `${m.ok ? 'compiled' : 'refused ' + m.refused.length + ' (' + why + ')'} · ${m.summary.elements} elements: ${r.knob} reach Unreal (timing) · ${r.wired} wired · ${r.cueReady} cue-ready · ${r.preview} preview`
      + ` · marks from the ${m.inputs.score.marksFrom} · ${m.warnings.length} warning${m.warnings.length === 1 ? '' : 's'}`;
  }

  const api = { compile, summaryText, expectedMarks, BadInput, VERSION, TIE };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.Compile = api;
})(typeof window !== 'undefined' ? window : globalThis);
