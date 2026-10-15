/* Veation VR Studio · REACH: where each element of the score stands with Unreal (lote 5 design A §3.3). Pure (no DOM): it runs in
   the browser and in Node (tools/score/reach_test.mjs). Computed on every compute(), never stored in the score.
     knob     its time reaches Unreal: a Partitura knob governs it, so "Send to Unreal" carries a change of it
     wired    Unreal decides it (the contract: hardwired, wired, an instance knob, not blocking; or an asset Unreal already calls)
     cue      schema 3, bound: a future cue player could fire it from an Unreal mark (state 'no-player': BP_ScorePlayer_SC does not exist)
     preview  only the editor and the 3D know it (made here, not in Unreal, or nothing in Unreal addresses its time)
   First rule that matches wins (the order of the design):
     1 made in the editor → preview · 2 contract "not in Unreal" → preview · 3 a Partitura knob governs it → knob
     4 contract literal | wired | knob | not-blocking → wired · 5 cue (below) · 6 preview, with the first reason it fails
   A cue needs ALL of: a cue-capable action; its moment tied to an Unreal mark (start of the moment, or one of its elements); a time
   from that mark that is the same for the fast, typical, slow and idle user (under 1/72 s apart) and not before it; an asset found in
   obra/unreal/idmap.json, once; that no Unreal asset already calls it (else it is wired: no double fire); a target when it needs one.
   Schema 2 has no `bind` and no marks of its own: the moment's marks come from the seed (obra/score/seed/marks-v1.json) and the asset
   from the sound's name, as a PROJECTION: such an element is counted as preview and flagged `bindable` (it would be a cue once the
   score is bound to Unreal). Only a schema 3 element with a `bind` is ever cue-ready, or wired because Unreal calls its asset. */
(function (root) {
  'use strict';
  const Marks = root.Marks || (typeof require === 'function' ? require('./marks.js') : null);
  const Integrity = root.Integrity || (typeof require === 'function' ? require('./integrity.js') : null);
  const Media = root.Media || (typeof require === 'function' ? require('./media.js') : null);
  const EPS = 1 / 72;                                   // one frame of the headset: the same time for every user within this
  const PERSONAS = ['fast', 'typical', 'slow', 'idle'];
  const own = (o, k) => !!o && Object.prototype.hasOwnProperty.call(o, k);

  // the action catalog (design A §3.2): what a cue could do. The rest are read-only for the score (Unreal decides them)
  const CUE_ACTIONS = new Set(['vo_alma', 'vo_2d', 'sound', 'sound_at', 'appear', 'disappear', 'ghost']);
  const NEEDS_ASSET = new Set(['vo_alma', 'vo_2d', 'sound', 'sound_at', 'ghost']);
  const NEEDS_TARGET = new Set(['sound_at', 'appear', 'disappear', 'ghost']);
  const ACTION_WORD = { vo_alma: 'Alma says it', vo_2d: 'a voice in 2D', sound: 'a sound', sound_at: 'a sound at a place', appear: 'appear', disappear: 'disappear', ghost: 'a ghost take',
    ambience: 'an ambience', title: 'a stage title', veil: 'a colour veil', wait: 'a wait' };
  // by the trackers (BP_Obra_SC.md): the voices that stay in 2D, and the effects Unreal plays at a place. Pending the Director's ack
  const VO_2D = new Set(['VO_33', 'VO_35a', 'VO_35b', 'VO_37']);
  const SOUND_AT = new Set(['FX_SHAREAPPEAR', 'FX_SHARESELECT', 'FX_SOULVANISH', 'FX_RINGVANISH']);
  const WIRED_WORD = { literal: 'Hardwired in Unreal', wired: 'Wired in Unreal', knob: 'A knob in Unreal', 'not-blocking': 'Different in Unreal' };
  const REACH_WORD = { knob: 'Reaches Unreal', wired: 'Wired in Unreal', cue: 'Cue-ready', preview: 'Preview' };

  const baseKey = k => String(k == null ? '' : k).replace(/#\d+$/, '');
  /* the action an element would have once bound (schema 2 projection, design A §3.4): the sound and the voices only; the ones that
     need a target or a role API (appear, ghost, sound_at) are chosen when the score is bound, never guessed here */
  function deriveAction(e) {
    const k = baseKey(e.key);
    if (e.type === 'vo') return VO_2D.has(baseKey(Media.soundId(e) || k)) ? 'vo_2d' : 'vo_alma';
    if (e.type === 'sound') return SOUND_AT.has(baseKey(Media.soundId(e) || k)) ? 'sound_at' : 'sound';
    if (e.type === 'ambience') return 'ambience';
    if (e.type === 'haptic') return null;
    if (e.type === 'wait') return 'wait';
    if (/^T\d?_|^T_(IN|OUT)$/.test(k)) return 'title';
    if (/^VEIL/.test(k)) return 'veil';
    return null;
  }

  /* the marks of every moment: schema 3 reads beats[].marks (once "Bind to Unreal" put them there), anything else the seed */
  function markLists(score, seed) {
    const B = score.beats, fromScore = score.schema >= 3 && Object.values(B).some(b => Array.isArray(b.marks) && b.marks.length), lists = {};
    for (const b of Object.keys(B)) { const l = fromScore ? B[b].marks : seed && seed.beats && seed.beats[b] ? seed.beats[b].marks : null; if (Array.isArray(l)) lists[b] = l; }
    return { from: fromScore ? 'score' : 'seed', lists };
  }

  /* the context of one run of the editor: everything the rules read, with the personas worked out only if a rule needs them.
     inp = { score, schedT (the typical user, default option), contract, gov (Partitura.governedBy), idmap, seed, roles,
             resolve(persona) → sched, player (true once a cue player exists) } */
  function context(inp) {
    const ctx = Object.assign({ player: false }, inp), memo = {};
    ctx.lists = markLists(ctx.score, ctx.seed);
    ctx.sched = p => {
      if (p === 'typical') return ctx.schedT;
      if (!memo[p]) memo[p] = ctx.resolve ? ctx.resolve(p) : ctx.schedT;
      return memo[p];
    };
    const mt = {};
    // where each mark falls for one user, and which moment placed it (the first one counts, as Marks.scoreMarks says)
    ctx.marksFor = p => {
      if (!mt[p]) { const info = {}; mt[p] = { t: Marks.scoreMarks(ctx.score, ctx.sched(p), ctx.seed, info), beat: info.beat }; }
      return mt[p];
    };
    ctx.byBeat = null;
    return ctx;
  }

  /* the marks of a moment that can govern its elements (rel start or el, placed by this moment), in time order for `p` */
  function govMarks(ctx, b, p) {
    const list = ctx.lists.lists[b]; if (!list) return null;
    const M = ctx.marksFor(p), out = [];
    list.forEach((m, i) => { if (m && (m.rel === 'start' || m.rel === 'el') && M.beat[m.name] === b && M.t[m.name] != null) out.push({ name: m.name, rel: m.rel, i, t: M.t[m.name] }); });
    return out.sort((x, y) => x.t - y.t || x.i - y.i);
  }

  const ownRel = (ctx, b) => { const l = ctx.lists.lists[b]; return l && l[0] ? l[0] : null; };
  const markText = n => Marks.label(n);

  /* the compiled cue of element `id`, or { why } for the first reason it cannot be one. bound = a schema 3 element with `bind` */
  function cueOf(id, ctx) {
    const E = ctx.score.elements, e = E[id], bound = ctx.score.schema >= 3 && e.bind && typeof e.bind === 'object';
    const action = bound ? (e.bind.action || null) : deriveAction(e);
    const fail = (why, extra) => Object.assign({ why, bound, action }, extra);
    if (!action) return fail(e.type === 'haptic' ? 'Haptics are not in Unreal.' : 'No Unreal action: only the editor and the 3D play it.');
    if (!CUE_ACTIONS.has(action)) return fail(action === 'ambience' ? 'Unreal picks the ambience itself (AmbPick).' : action === 'wait' ? "A wait: Unreal's own graph decides it." : `${ACTION_WORD[action] || action}: a knob of Unreal decides it.`);
    if (!bound && NEEDS_TARGET.has(action)) return fail('It needs a place in Unreal: chosen when the score is bound.');
    const b = e.beat, list = ctx.lists.lists[b], rel = ownRel(ctx, b);
    if (!list || !rel) return fail(ctx.lists.from === 'seed' && ctx.score.schema >= 3 ? 'This moment is not bound to an Unreal mark yet.' : 'This moment has no Unreal mark yet.');
    const T = ctx.schedT.t;
    if (!T[id]) return fail('It plays in the other option of a decision.');
    const gm = govMarks(ctx, b, 'typical') || [];
    const usable = rel.rel === 'start' || rel.rel === 'el' ? gm : gm.filter(m => m.rel === 'el');
    if (!usable.length) {
      const by = rel.by && rel.by.length ? ` (${rel.by.slice(0, 3).join(', ')}${rel.by.length > 3 ? '…' : ''})` : '';
      return fail(rel.rel === 'in' ? `Inside ${markText(rel.name)}: its time is set by Unreal knobs${by}.` : rel.rel === 'sub' ? `Inside ${markText(rel.name)}: a step Unreal does not announce to the score${by}.`
        : rel.rel === 'preview' ? `Unreal decides what happens here${rel.why ? ': ' + rel.why : ''}.` : 'This moment has no Unreal mark that can be reached.');
    }
    const s = T[id][0];
    let g = null; for (const m of usable) if (m.t <= s + EPS) g = m;
    if (!g) return fail(`It starts before ${markText(usable[0].name)}, the first Unreal mark of its moment: nothing can fire it earlier.`, { mark: usable[0].name });
    // the same time from that mark for every user
    const offs = PERSONAS.map(p => { const tt = ctx.sched(p).t[id], mt = ctx.marksFor(p).t[g.name]; return tt && mt != null ? tt[0] - mt : null; });
    if (offs.some(o => o == null)) return fail('It plays only for some of the users.', { mark: g.name });
    const spread = Math.max(...offs) - Math.min(...offs);
    if (spread >= EPS) return fail(`It depends on the user: ${spread.toFixed(1)} s apart from ${markText(g.name)} between the fast and the idle user.`, { mark: g.name, spread });
    const offset = offs[PERSONAS.indexOf('typical')];
    // asset
    let asset = null, rec = null, sid = null;
    if (NEEDS_ASSET.has(action)) {
      sid = bound ? e.bind.asset : Media.soundId(e);
      if (!sid) return fail('No asset to play.', { mark: g.name });
      if (!ctx.idmap) return fail('The Unreal assets are not scanned yet (obra/unreal/idmap.json).', { mark: g.name });
      const al = own(ctx.idmap.aliases, sid) ? ctx.idmap.aliases[sid] : null, name = bound ? sid : (al || sid);
      asset = name;
      if (own(ctx.idmap.ambiguous, name)) return fail(`The asset is ambiguous: ${ctx.idmap.ambiguous[name].map(r => r.path.replace(/\.[^./]+$/, '')).join(' and ')}.`, { mark: g.name, asset: name, ambiguous: true });
      if (!own(ctx.idmap.assets, name)) return fail(`${name} is not in Unreal's Content.`, { mark: g.name, asset: name });
      rec = ctx.idmap.assets[name];
    }
    // a target (bound only; the projection never gets here for the actions that need one)
    const target = bound ? (e.bind.target || null) : null;
    if (NEEDS_TARGET.has(action) && !target) return fail('It needs a target in Unreal.', { mark: g.name });
    if (target && !/^(role|tag):.+/.test(target)) return fail(`The target ${target} is not a role: or a tag:.`, { mark: g.name });
    if (target && /^role:/.test(target) && ctx.roles && ctx.roles.roles && !own(ctx.roles.roles, target.slice(5)) && target !== 'role:Alma') return fail(`The role ${target.slice(5)} is not in roles.json.`, { mark: g.name });
    // does Unreal already play it? then it is wired: a cue would play it twice
    if (rec) {
      const by = rec.referencedBy;
      if (by === null || by === undefined) return { referenced: true, unsure: true, why: `Unreal may already play ${asset}: the references of a plugin asset are not read.`, action, bound, mark: g.name, asset };
      if (by.length) return { referenced: true, why: `Unreal already calls ${asset} (${by.slice(0, 2).map(p => p.split('/').pop()).join(', ')}${by.length > 2 ? ' +' + (by.length - 2) : ''}): a cue would play it twice.`, action, bound, mark: g.name, asset, by };
    }
    return { cue: { mark: g.name, offset, action, target, asset, path: rec ? rec.path : null, rel: g.rel }, bound, action };
  }

  /* where element `id` stands: { reach, why, ...} (see the top) */
  function of(id, ctx) {
    const score = ctx.score, e = score.elements[id];
    if (!e) return { reach: 'preview', why: 'It is not in the score.' };
    if (e.isNew) return { reach: 'preview', why: 'Made in the editor: Unreal does not know it.' };
    const cs = Integrity.contractFor(id, e, ctx.contract);
    const nu = cs.find(c => c.kind === 'not-in-unreal');
    if (nu) return { reach: 'preview', why: 'Not in Unreal: the contract says so.', msg: nu.msg || null, owner: nu.owner || null, contract: nu.id };
    const gv = (ctx.gov || {})[id], part = cs.find(c => c.kind === 'partitura');
    if (gv && gv.length || part) {
      const names = gv && gv.length ? [...new Set(gv.map(g => g.knob))] : (part.knobs || []);
      return { reach: 'knob', why: names.length ? `Reaches Unreal when you send ${names.slice(0, 3).join(', ')}${names.length > 3 ? ' (+' + (names.length - 3) + ')' : ''}.` : 'Its time is a Partitura knob.', knobs: names, contract: part ? part.id : null };
    }
    const wc = cs.find(c => WIRED_WORD[c.kind]);
    if (wc) return { reach: 'wired', why: `${WIRED_WORD[wc.kind]}: ${wc.owner || 'Unreal'}${wc.graph ? ' › ' + wc.graph : ''}.`, owner: wc.owner || null, graph: wc.graph || null, contract: wc.id, kind: wc.kind };
    const c = cueOf(id, ctx);
    // a bound element whose asset Unreal already calls IS wired (design A §3.3, rule 5); in the projection of a score not bound yet it
    // stays preview: nothing in the contract says so, only a scan of the files
    if (c.referenced) return c.bound ? { reach: 'wired', why: c.why, asset: c.asset, unsure: !!c.unsure, mark: c.mark, calls: c.by || null }
      : { reach: 'preview', why: c.why, asset: c.asset, referenced: true, unsure: !!c.unsure, mark: c.mark };
    if (c.cue) {
      if (c.bound) return { reach: 'cue', why: `A cue could fire it ${Math.abs(c.cue.offset).toFixed(1)} s after ${markText(c.cue.mark)}.`, cue: c.cue, state: ctx.player ? 'ready' : 'no-player' };
      // schema 2 (or a score not bound yet): the same rules say it WOULD be a cue; it is preview until the score is bound
      return { reach: 'preview', why: 'Only the editor and the 3D play it. It could be a cue once the score is bound to Unreal.', cue: c.cue, bindable: true };
    }
    // an ambiguous asset is said apart (the dry-run compiler refuses it: two files answer to that name)
    return Object.assign({ reach: 'preview', why: c.why, mark: c.mark || null }, c.ambiguous ? { ambiguous: true, asset: c.asset } : {});
  }

  /* every element: { of: { id: result }, counts: { knob, wired, cue, preview, bindable, unsure }, schema, marksFrom } */
  function all(ctx) {
    const res = {}, counts = { knob: 0, wired: 0, cue: 0, preview: 0, bindable: 0, unsure: 0 };
    for (const id of Object.keys(ctx.score.elements)) {
      const r = of(id, ctx); res[id] = r; counts[r.reach]++;
      if (r.bindable) counts.bindable++;
      if (r.unsure) counts.unsure++;
    }
    return { of: res, counts, schema: ctx.score.schema, marksFrom: ctx.lists.from };
  }

  /* the words of the status bar: "70 reach Unreal (timing) · 56 wired · 12 cue-ready · 428 preview". The cue-ready part is shown
     only for a schema 3 score (the one that can carry a bind); before that it is in the tooltip as what binding would give */
  function statusText(a) {
    const c = a.counts, parts = [`${c.knob} reach Unreal (timing)`, `${c.wired} wired`];
    if (a.schema >= 3) parts.push(`${c.cue} cue-ready`);
    parts.push(`${c.preview} preview`);
    return parts.join(' · ');
  }
  function statusTitle(a) {
    const c = a.counts, t = [
      `${c.knob}: a Partitura knob sets their time, so Send to Unreal carries a change of them.`,
      `${c.wired}: Unreal decides them (hardwired, wired, a knob of an instance, or an asset it already calls)${c.unsure ? `; ${c.unsure} of them only because the references of plugin assets are not read` : ''}.`];
    if (a.schema >= 3) t.push(`${c.cue}: bound to an Unreal mark and asset; a future cue player could fire them (no player yet).`);
    t.push(`${c.preview}: only the editor and the 3D know them` + (c.bindable ? `; ${c.bindable} of them could be cues once the score is bound to Unreal.` : '.'));
    t.push('Nothing reaches Unreal until Send to Unreal.');
    return t.join('\n');
  }

  const api = { PERSONAS, EPS, CUE_ACTIONS, ACTION_WORD, REACH_WORD, deriveAction, markLists, context, of, all, cueOf, statusText, statusTitle };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.Reach = api;
})(typeof window !== 'undefined' ? window : globalThis);
