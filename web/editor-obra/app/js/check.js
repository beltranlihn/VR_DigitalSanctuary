/* Veation VR Studio · CHECK: what a score must keep to be saved (lote 5 design B §8.2, audit D12). Pure (no DOM, no files): it
   runs in the browser (save() asks it before the PUT), in Node (tools/score/check.mjs, tools/score/check_test.mjs) and, through
   that CLI, in the server (tools/editor/serve_editor.py, inside the write lock). The three give the same verdict, because the
   cycles of anchors depend on the exact evaluation order of the engine and a second engine would have to be kept identical.
   One rule decides what is rejected: only what is NEW relative to `base` (the score on disk). The piece has known debt (two
   anchor loops, 2.R4 and 5.R4): rejecting every loop would block every save, so the debt stays visible (Problems, and the
   `grandfathered` list here) and the ratchet forbids adding more. Without a base nothing can be called new: the loops and the
   cross-branch anchors are reported as warnings, the rest as errors.
   invariants(score, base, ctx) → { ok, errors, warnings, grandfathered, totals: { typical }, schema }; every item is
   { code, msg, ids } (ids: moments or elements to select). ctx = { Engine, Edits (default: the ones loaded next to this file),
   contract, knobs (a Set: knobNames()) } (the last two only feed the warnings). */
(function (root) {
  'use strict';
  const MAX_TOTAL = 3600;   // seconds: a typical total over an hour is a mistake, not a piece (the goal is 15:00)
  const dep = (file, name) => (typeof require === 'function' && typeof module !== 'undefined' ? require('./' + file) : root[name]);
  const has = (o, k) => !!o && typeof o === 'object' && Object.prototype.hasOwnProperty.call(o, k);
  const isObj = o => !!o && typeof o === 'object' && !Array.isArray(o);
  const fmt = s => { s = Math.round(Math.max(0, s)); const m = Math.floor(s / 60); return m + ':' + String(s - m * 60).padStart(2, '0'); };

  /* the short name of each code (the card and the CLI show it before the message); the table of design B §8.2 */
  const TITLES = {
    'S.STRUCT': 'Not a valid score', 'S.IDS.DUP': 'An id is used twice', 'S.ANCHOR.MISSING': 'Anchor lost', 'S.CYCLE.NEW': 'New anchor loop',
    'S.SCHEMA.DOWN': 'Older schema', 'S.BRANCH.FIELD': 'Malformed branch', 'S.BIND.FIELD': 'Malformed Unreal binding', 'S.BRANCH.CROSS.NEW': 'Anchor across branches', 'S.UIDMAP': 'Dangling uidMap entry',
    'S.TOTAL': 'Total out of range', 'W.CYCLE': 'Anchor loop', 'W.BRANCH.CROSS': 'Anchor across branches', 'W.CONTRACT': 'Contract with Unreal',
    'W.ACCEPTED.ORPHAN': 'Accepted record of a deleted element', 'W.BASELINE.STALE': 'APK baseline of a deleted element' };

  /* the names Unreal's knobs go by: the Partitura (partitura_def.json: knobs[].name) and the Blueprint variables of the dump
     (perillas.json: bps → [[name, category, value]]), each also as "<owner>.<name>". null when neither file is there (the knob check is then skipped) */
  function knobNames(pdef, perillas) {
    if (!pdef && !perillas) return null;
    const out = new Set();
    for (const k of (pdef && pdef.knobs) || []) if (k && k.name) out.add(k.name);
    // a variable by its name and as "<Blueprint>.<variable>" (how an entry that counts a time from a knob names it: BP_BreathStage_SC.HelpAfter)
    for (const [bp, vars] of Object.entries((perillas && perillas.bps) || {})) for (const v of Array.isArray(vars) ? vars : []) if (Array.isArray(v) && v[0]) { out.add(v[0]); out.add(bp + '.' + v[0]); }
    for (const k of (pdef && pdef.knobs) || []) if (k && k.name) out.add('DA_Partitura_Obra.' + k.name);
    return out;
  }

  /* ---------- scans that need no engine ---------- */
  const keyOf = (s, id) => (has(s.beats, id) ? s.beats[id] : has(s.elements, id) ? s.elements[id] : {}).key || id;
  const nameOf = (s, id) => (has(s.beats, id) ? 'Moment ' : '') + keyOf(s, id);
  const exists = (s, id) => has(s.beats, id) || has(s.elements, id);

  /* every anchor that points to nothing: at / end of moments and elements, the anchors of every option of an `alt`, and the
     wait a help line belongs to */
  function missingAnchors(s) {
    // without its moments or elements every anchor "points to nothing": that is S.STRUCT's to say, once
    if (!isObj(s.beats) || !isObj(s.elements)) return [];
    const out = [], gone = a => isObj(a) && a.ref && !exists(s, a.ref);
    const scan = (id, x) => {
      if (!isObj(x)) return;
      for (const f of ['at', 'end']) if (gone(x[f])) out.push({ id, what: f === 'at' ? 'starts from' : 'lasts until' });
      if (isObj(x.alt)) for (const k of Object.keys(x.alt)) for (const f of ['at', 'end']) if (isObj(x.alt[k]) && gone(x.alt[k][f])) out.push({ id, what: `in ${k} ${f === 'at' ? 'starts from' : 'lasts until'}` });
      if (x.help && !has(s.elements, x.help)) out.push({ id, what: 'is the help of' });
    };
    for (const id of Object.keys(s.beats || {})) scan(id, s.beats[id]);
    for (const id of Object.keys(s.elements || {})) scan(id, s.elements[id]);
    return out;
  }

  /* an id in more than one of acts / groups / lanes / beats / elements / markers / notes (or twice in a list), and two live
     uidMap entries naming the same id: fingerprint → { msg, ids } */
  function dupIds(s) {
    const seen = new Map(), out = new Map();
    const add = (id, where) => { if (id == null || id === '') return; if (!seen.has(id)) seen.set(id, []); seen.get(id).push(where); };
    for (const a of Array.isArray(s.acts) ? s.acts : []) add(a && a.id, 'acts');
    for (const g of Array.isArray(s.groups) ? s.groups : []) add(g && g.id, 'groups');
    for (const w of ['lanes', 'beats', 'elements', 'markers', 'notes']) if (s[w] && typeof s[w] === 'object') for (const id of Object.keys(s[w])) add(id, w);
    for (const [id, where] of seen) if (where.length > 1) out.set('id|' + id + '|' + where.join('+'), { msg: `The id ${id} is used more than once (${[...new Set(where)].join(', ')}${new Set(where).size === 1 ? ' twice' : ''}): one id must name one thing.`, ids: exists(s, id) ? [id] : [] });
    const live = new Map();
    for (const [uid, u] of Object.entries(isObj(s.uidMap) ? s.uidMap : {})) if (isObj(u) && !u.state && u.id) { if (!live.has(u.id)) live.set(u.id, []); live.get(u.id).push(uid); }
    for (const [id, uids] of live) if (uids.length > 1) out.set('uid|' + id, { msg: `The uidMap has ${uids.length} live entries for ${nameOf(s, id)} (${uids.slice(0, 3).join(', ')}${uids.length > 3 ? ', …' : ''}): a prototype name maps to one id.`, ids: exists(s, id) ? [id] : [] });
    return out;
  }

  /* live uidMap entries (no `state`: a tombstone points to nothing on purpose) whose id is no longer in the score: uid → id */
  function deadUids(s) {
    const out = new Map();
    for (const [uid, u] of Object.entries(isObj(s.uidMap) ? s.uidMap : {})) if (isObj(u) && !u.state && !(typeof u.id === 'string' && exists(s, u.id))) out.set(uid, u.id);
    return out;
  }

  /* ---------- what the engine says: the typical user, and every option of every branch (design B §8.2) ---------- */
  function runsOf(s) {
    const r = [{ label: 'typical', opt: { persona: 'typical' } }];
    for (const on of Object.keys(isObj(s.branches) ? s.branches : {})) for (const o of Object.keys((isObj(s.branches[on]) && s.branches[on].options) || {})) r.push({ label: `${on}=${o}`, opt: { persona: 'typical', branch: { [on]: o } } });
    return r;
  }
  /* cycles and cross-branch anchors, by node id: the first run that shows a loop; for an anchor across branches, what it
     points to (an element of another option: `to`, with the decision `on` and the option `value` it is only there for).
     `typical` is that run already resolved */
  function engineInfo(s, Engine, typical) {
    const cycles = new Map(), cross = new Map();
    for (const r of runsOf(s)) {
      const res = typical && r.label === 'typical' ? typical : Engine.resolve(s, r.opt);
      for (const id of res.cycles || []) if (!cycles.has(id)) cycles.set(id, r.label);
      for (const id of res.crossBranch || []) if (!cross.has(id)) {
        const x = s.beats[id] || s.elements[id], alt = isObj(x.alt) ? Object.values(x.alt) : [];
        const refs = [x.at, x.end].concat(alt.flatMap(o => (isObj(o) ? [o.at, o.end] : []))).map(a => a && a.ref).filter(ref => ref && res.off && res.off[ref]);
        const to = refs[0], b = to && s.elements[to].branch;
        cross.set(id, { to: to || null, on: b ? b.on : null, value: b ? b.value : null });
      }
    }
    return { cycles, cross };
  }
  const safe = (fn, fallback) => { try { return fn(); } catch (_) { return fallback; } };

  function invariants(score, base, ctx) {
    ctx = ctx || {};
    const errors = [], warnings = [], grandfathered = [];
    const result = totals => ({ ok: !errors.length, errors, warnings, grandfathered, totals: { typical: totals }, schema: score && score.schema });
    if (!isObj(score)) { errors.push({ code: 'S.STRUCT', msg: 'This is not a score.', ids: [] }); return result(null); }
    const Engine = ctx.Engine || dep('engine.js', 'ScoreEngine'), Edits = ctx.Edits || dep('edits.js', 'Edits');
    const err = (code, msg, ids) => errors.push({ code, msg, ids: ids || [] });
    const warn = (code, msg, ids) => warnings.push({ code, msg, ids: ids || [] });
    const old = (code, msg, ids) => grandfathered.push({ code, msg, ids: ids || [] });
    const B = isObj(score.beats) ? score.beats : {}, E = isObj(score.elements) ? score.elements : {};
    const baseObj = isObj(base) ? base : null;

    // S.SCHEMA.DOWN · an old tab saving over a migrated score
    if (baseObj && Number.isInteger(baseObj.schema) && Number.isInteger(score.schema) && score.schema < baseObj.schema)
      err('S.SCHEMA.DOWN', `This is a schema ${score.schema} score and the one on disk is schema ${baseObj.schema}: an older score cannot replace it.`);

    // S.ANCHOR.MISSING · always (today there are none)
    const missing = safe(() => missingAnchors(score), []);
    for (const m of missing) err('S.ANCHOR.MISSING', `${nameOf(score, m.id)} ${m.what} something that no longer exists.`, [m.id]);

    // S.IDS.DUP · only the new ones (a base with a repeated id is not made worse, and can still be fixed)
    const dups = safe(() => dupIds(score), new Map()), baseDups = baseObj ? safe(() => dupIds(baseObj), null) : null;
    for (const [fp, d] of dups) { if (baseDups && baseDups.has(fp)) old('S.IDS.DUP', d.msg, d.ids); else err('S.IDS.DUP', d.msg, d.ids); }

    // S.STRUCT / S.BRANCH.FIELD · the editor's own validation (schema 2 or 3), and whether the engine can compute the piece
    let typical = null;
    try { typical = Edits.validate(score, Engine); } catch (e) {
      const msg = String(e && e.message || e);
      // the branch fields and the Unreal binding (marks, bind) have their own codes: same function, same message
      let code = 'S.STRUCT';
      const says = fn => { try { fn(score, m => { throw new Error(m); }); } catch (x) { return x.message === msg; } return false; };
      if (score.schema === 3 && Edits.validateBranches && says(Edits.validateBranches)) code = 'S.BRANCH.FIELD';
      else if (score.schema === 3 && Edits.validateBind && says(Edits.validateBind)) code = 'S.BIND.FIELD';
      // a dangling anchor was just said, with its element: the same sentence from validate adds nothing
      if (!(missing.length && /points to something that does not exist/.test(msg))) err(code, msg);
    }

    // the rest needs the piece to compute
    let baseInfo = null, cur = null;
    if (typical) {
      try { cur = engineInfo(score, Engine, typical); } catch (e) { err('S.STRUCT', 'The timeline does not compute: ' + String(e && e.message || e)); }
      if (baseObj) baseInfo = safe(() => engineInfo(baseObj, Engine), null);   // a base the engine cannot read forgives nothing
    }
    if (typical) {
      const total = typical.total;
      if (!Number.isFinite(total) || total > MAX_TOTAL) err('S.TOTAL', Number.isFinite(total) ? `The typical total is ${fmt(total)}: over ${fmt(MAX_TOTAL)} it is not a piece, it is a mistake.` : 'The typical total is not a number.');
    }
    if (cur) {
      // S.CYCLE.NEW · the loops of the base are the known debt
      for (const [id, run] of cur.cycles) {
        const where = run === 'typical' ? '' : ` in ${run}`;
        const what = has(B, id) ? `${nameOf(score, id)} has an anchor loop${where}: the moment that should follow it starts at the same time.`
          : `${nameOf(score, id)} is in an anchor loop${where}: its time depends on itself.`;
        if (!baseInfo) warn('W.CYCLE', what, [id]);
        else if (baseInfo.cycles.has(id)) old('S.CYCLE.NEW', what + ' It was already in the saved score.', [id]);
        else err('S.CYCLE.NEW', `New anchor loop: ${what}`, [id]);
      }
      // S.BRANCH.CROSS.NEW · an anchor that crosses to the other option (its phantom time is used, so nothing jumps, but it is a trap)
      for (const [id, c] of cur.cross) {
        const what = `${nameOf(score, id)} is anchored to ${c.to ? keyOf(score, c.to) + ', which only exists when ' + c.on + ' is ' + c.value : 'something that only exists in another option'}.`;
        if (!baseInfo) warn('W.BRANCH.CROSS', what, [id]);
        else if (baseInfo.cross.has(id)) old('S.BRANCH.CROSS.NEW', what + ' It was already in the saved score.', [id]);
        else err('S.BRANCH.CROSS.NEW', `New anchor across branches: ${what} Give it an alternative anchor for the other option.`, [id]);
      }
    }

    // S.UIDMAP · a live uidMap entry whose element is gone (schema 3); the ones the base already had are not made worse
    const dead = safe(() => deadUids(score), new Map()), baseDead = baseObj ? safe(() => deadUids(baseObj), null) : null;
    for (const [uid, id] of dead) {
      const msg = `The uidMap entry ${uid} points to ${id}, which is no longer in the score: a deleted element stays in the map as deleted-here.`;
      if (baseDead && baseDead.has(uid)) old('S.UIDMAP', msg); else err('S.UIDMAP', msg);
    }

    // warnings: debt that is shown, never rejected
    if (isObj(ctx.contract) && Array.isArray(ctx.contract.entries)) {
      const keys = new Set(Object.values(E).map(e => e && e.key));
      for (const c of ctx.contract.entries) {
        const lost = ((c.match && c.match.keys) || []).filter(k => !keys.has(k));
        if (lost.length) warn('W.CONTRACT', `The contract entry '${c.id}' lists ${lost.join(', ')}, which ${lost.length === 1 ? 'is' : 'are'} not in the score.`);
        if (c.knob && c.knob.name && ctx.knobs instanceof Set && !ctx.knobs.has(c.knob.name)) warn('W.CONTRACT', `The contract entry '${c.id}' names the knob ${c.knob.name}, which is not in the Partitura or the Blueprint dump.`);
      }
    }
    for (const a of Array.isArray(score.accepted) ? score.accepted : []) if (isObj(a) && a.el && !exists(score, a.el)) warn('W.ACCEPTED.ORPHAN', `The accepted problem ${a.fp} belongs to an element that no longer exists.`, []);
    if (isObj(score.baseline) && isObj(score.baseline.rel)) {
      const stale = Object.keys(score.baseline.rel).filter(id => !has(E, id));
      if (stale.length) warn('W.BASELINE.STALE', `The APK baseline has ${stale.length} element${stale.length === 1 ? '' : 's'} that no longer exist${stale.length === 1 ? 's' : ''}.`);
    }
    return result(typical ? typical.total : null);
  }

  const api = { invariants, knobNames, TITLES, MAX_TOTAL };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.Check = api;
})(typeof window !== 'undefined' ? window : globalThis);
