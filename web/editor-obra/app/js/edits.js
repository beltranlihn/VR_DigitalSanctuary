/* Veation VR Studio · EDITS: the delicate edit logic, pure (no DOM) so it runs in the browser and in Node
   (tools/score/edits_test.mjs replays the cases of the audit, docs/editor-obra/anexos/18-auditoria-app.md).
   Also: is it the same score as the saved one (the honest "unsaved").
   Every time here is measured with the TYPICAL user: the other users are simulations and never decide what is written. */
(function (root) {
  'use strict';
  const r4 = x => Math.round(x * 10000) / 10000;
  const clone = o => JSON.parse(JSON.stringify(o));
  const typical = (Engine, s) => Engine.resolve(s, { persona: 'typical' });
  const nodeOf = (s, id) => s.elements[id] || s.beats[id];
  const edgeT = (T, a) => a && a.ref ? (a.edge === 'start' ? T[a.ref][0] : T[a.ref][1]) : 0;
  const sameT = (a, b) => a && b && Math.abs(a[0] - b[0]) < 1e-3 && Math.abs(a[1] - b[1]) < 1e-3;
const isObj = o => !!o && typeof o === 'object' && !Array.isArray(o);

  /* ---------- the runs a score is judged on ----------
     The typical user in the default option of every decision (what the timeline shows) and, in schema 3, in every other option
     of every branch: a clip that hangs from something in one option of SHARE is timed in that option, so an edit that touches it
     has to be measured there too. Schema 2 has one run. Each run is Engine.resolve plus its `k` (null = the default one, else
     "<branch>=<option>", the key of an `alt`). An alt key of the default option reads the first run (tIn falls back to it). */
  function runsOf(score, Engine) {
    const runs = [Object.assign({ k: null }, Engine.resolve(score, { persona: 'typical' }))];
    for (const on of Object.keys(score.branches || {})) { const br = score.branches[on]; for (const o of Object.keys((br && br.options) || {})) if (o !== br.default) runs.push(Object.assign({ k: on + '=' + o }, Engine.resolve(score, { persona: 'typical', branch: { [on]: o } }))); }
    return runs;
  }
  const tIn = (R, k) => R.find(r => r.k === k) || R[0];
  /* the typical user in ONE option of a decision ("share=no"; null, a score with no such option: the default ones). The other
     decisions stay on their default option (an omitted key would be read as "auto") */
  function runOf(score, Engine, k) {
    const m = /^([^=]+)=([^=]+)$/.exec(k || ''), brs = score.branches;
    if (!m || !brs || !brs[m[1]]) return typical(Engine, score);
    const want = {}; for (const b of Object.keys(brs)) want[b] = b === m[1] ? m[2] : 'default';
    return Engine.resolve(score, { persona: 'typical', branch: want });
  }
  /* did it start or end elsewhere in any run where it is there (a clip of the other option is not "there": its phantom time does not count)? */
  const movedIn = (R0, R1, id) => R0.some((r, i) => !(r.off && r.off[id]) && !(R1[i].off && R1[i].off[id]) && !!r.t[id] && !!R1[i].t[id] && !sameT(r.t[id], R1[i].t[id]));

  /* ---------- schema 3: a deleted element stays in the uidMap as deleted-here (design B §2, rule S.UIDMAP) ----------
     The map says "prototype name → id". An id that is gone must not stay there as a live name (the server would refuse the save),
     and must not be forgotten either: the tombstone keeps id and sig, so a later scan of guion.js knows the element was deleted
     here and does not offer it again, and newId never gives that id to something else. Only entries that were live in `before`
     are touched (one that was already dead is a debt of the base, not of this edit). Mutates `next`; returns the names it marked. */
  function reconcileUidMap(before, next) {
    const m = next && isObj(next.uidMap) ? next.uidMap : null, done = [];
    if (!m) return done;
    const there = (s, id) => !!s && ((isObj(s.elements) && !!s.elements[id]) || (isObj(s.beats) && !!s.beats[id]));
    for (const uid of Object.keys(m)) {
      const u = m[uid];
      if (!isObj(u) || u.state || typeof u.id !== 'string' || there(next, u.id) || (before && !there(before, u.id))) continue;
      u.state = 'deleted-here'; done.push(uid);
    }
    return done;
  }

  /* ---------- delete: plan both repairs BEFORE asking, with their real effect ----------
     What hangs from something includes the alternative anchors of schema 3 (VO_37 starts from VO_35c in DON'T SHARE): it is
     re-anchored in its own option, where it keeps its time, exactly as a primary anchor is. The effect is measured in every option. */
  function planDelete(score, ids, Engine) {
    const R0 = runsOf(score, Engine), T0 = R0[0], kids = Engine.dependents(score), gone = new Set(ids);
    const direct = [...new Set(ids.flatMap(id => kids[id] || []))].filter(k => !gone.has(k));
    if (!direct.length && !ids.some(id => Object.values(score.elements).some(e => e.help === id))) return null;
    // the anchor a dependent inherits: the deleted element's own anchor in that option (walking up if that one is deleted too)
    const startOf = (x, k) => x && (k && x.alt && x.alt[k] && x.alt[k].at ? x.alt[k].at : x.at);
    const inherit = (del, s, k) => { let a = startOf(s.elements[del], k); const seen = new Set(); while (a && a.ref && del && (gone.has(a.ref) || (s._fam && s._fam.has(a.ref))) && !seen.has(a.ref)) { seen.add(a.ref); a = startOf(s.elements[a.ref], k); } return a && a.ref ? a : { ref: null, edge: 'start', off: 0 }; };
    const reanchor = (n, set, src, R) => {   // every node (element or moment) pointing at a deleted id keeps its time (R: the runs of src), in each option it points there
      R = R || R0; const T = R[0].t;
      for (const id of Object.keys(n.elements).concat(Object.keys(n.beats))) {
        const x = nodeOf(n, id);
        if (x.at && x.at.ref && set.has(x.at.ref)) { const a = inherit(x.at.ref, src); x.at = { ref: a.ref, edge: a.edge, off: r4(T[id][0] - edgeT(T, a)) }; }
        if (x.end && x.end.ref && set.has(x.end.ref)) { const a = inherit(x.end.ref, src); x.end = { ref: a.ref, edge: a.edge, off: r4(T[id][1] - edgeT(T, a)) }; }
        if (x.help && set.has(x.help)) x.help = null;
        if (x.alt) for (const k of Object.keys(x.alt)) {
          const Tk = tIn(R, k).t;
          for (const f of ['at', 'end']) { const o = x.alt[k][f]; if (o && o.ref && set.has(o.ref)) { const a = inherit(o.ref, src, k); x.alt[k][f] = { ref: a.ref, edge: a.edge, off: r4(Tk[id][f === 'at' ? 0 : 1] - edgeT(Tk, a)) }; } }
        }
      }
    };
    const stats = (n, deleted) => {
      const R1 = runsOf(n, Engine); let moved = 0;
      for (const id of Object.keys(n.elements).concat(Object.keys(n.beats))) if (movedIn(R0, R1, id)) moved++;
      // drift: what hung from the selection and is not where it was (several deleted: it kept its place among what is left,
      // and an earlier deletion moved that; the card says so instead of "stays where it is")
      const drift = direct.filter(k => !deleted.has(k) && movedIn(R0, R1, k));
      return { moved, kept: !drift.length, drift, dangling: new Set(R1.flatMap(r => r.dangling)).size, total0: T0.total, total1: R1[0].total };
    };
    // A · re-anchor: only the selection goes; everything that hung from it stays where it was. One after the other (C10),
    // each measured on the score the previous ones left: deleting clips of earlier moments shortens them and everything
    // after moves with them, what hung from a deleted clip too (it keeps its place among what is left)
    let A = score, keptAll = true;
    for (const id of ids) {
      if (!A.elements[id]) continue;
      const Rs = runsOf(A, Engine), ks = (Engine.dependents(A)[id] || []).filter(k => !gone.has(k)), n = clone(A);
      delete n.elements[id]; reanchor(n, new Set([id]), A, Rs);
      const Rn = runsOf(n, Engine); if (!ks.every(k => !movedIn(Rs, Rn, k))) keptAll = false;
      A = n;
    }
    if (A === score) A = clone(score);
    reconcileUidMap(score, A);
    settleMarks(A, score);   // an `el` mark (schema 3, bound) goes with its element: the plan is a score that validates
    const sa = Object.assign(stats(A, gone), ids.length > 1 ? { kept: keptAll } : {});
    // B · delete them too: the family through ELEMENTS only; a moment is never deleted, it is re-anchored
    const fam = new Set(ids), st = [...ids];
    while (st.length) { const x = st.pop(); for (const k of kids[x] || []) if (score.elements[k] && !fam.has(k)) { fam.add(k); st.push(k); } }
    const srcB = Object.assign(clone(score), { _fam: fam });
    const B = clone(score); fam.forEach(id => delete B.elements[id]);
    reanchor(B, fam, srcB);
    reconcileUidMap(score, B);
    settleMarks(B, score);
    const sb = stats(B, fam);
    const anchoredMoments = direct.filter(k => score.beats[k]);
    // the wait that decides SHARE / DON'T SHARE stays: the decision would be left with nothing to decide it (branchError)
    const gatesA = branchGates(score, [...gone]), gatesB = branchGates(score, [...fam]);
    return {
      direct, anchoredMoments,
      reanchor: { next: A, ids: [...gone], ok: sa.dangling === 0 && sa.kept && !gatesA.length, gates: gatesA, marks: marksLost(score, A), ...sa },
      family: { next: B, ids: [...fam], ok: sb.dangling === 0 && !gatesB.length, gates: gatesB, deleted: fam.size, marks: marksLost(score, B), ...sb },
    };
  }

  /* ---------- move: dt seconds; alone = everything anchored to it stays in place ---------- */
  /* schema 3: the option on screen (ks: the keys of the options shown, "share=no") in which this clip hangs from something else of
     its own (an `alt` start). null = the primary anchor is what you see. The one place that decides which anchor a drag moves */
  const altKeyOf = (x, ks) => (ks || []).find(k => x && x.alt && x.alt[k] && x.alt[k].at) || null;
  function move(score, id, dt, opts, kids) {
    opts = opts || {}; const n = clone(score), x = n.elements[id];
    // schema 3: in an option of a decision where this clip hangs from something else (alt), the offset that moves it there is the
    // alternative's, not the primary one (opts.ks: the options on screen, "share=no"): what you drag is what you see move
    const altK = altKeyOf(x, opts.ks);
    if (altK) x.alt[altK].at.off = r4((x.alt[altK].at.off || 0) + dt);
    else { x.at = x.at || { ref: x.beat, edge: 'start', off: 0 }; x.at.off = r4(x.at.off + dt); }
    // a clip that lasts "until" an event keeps ending with it: moving it moves its start only (the drag shows the new length)
    const endMoves = altK ? !(x.alt[altK].end !== undefined ? x.alt[altK].end : x.end) : !x.end;
    if (opts.alone && altK) {
      // moved only in that option: what hangs from it THERE (its alternative anchors for it) stays; the primary anchors, which
      // are the other options, did not move with it
      for (const k of kids[id] || []) {
        const y = nodeOf(n, k); if (!y || !y.alt || !y.alt[altK]) continue;
        for (const f of ['at', 'end']) { const a = y.alt[altK][f]; if (a && a.ref === id && (a.edge === 'start' || endMoves)) a.off = r4((a.off || 0) - dt); }
      }
    } else if (opts.alone) for (const k of kids[id] || []) {
      const y = nodeOf(n, k); if (!y) continue;
      if (y.at && y.at.ref === id && (y.at.edge === 'start' || endMoves)) y.at.off = r4(y.at.off - dt);
      if (y.end && y.end.ref === id && (y.end.edge === 'start' || endMoves)) y.end.off = r4((y.end.off || 0) - dt);
      // an alternative anchor (schema 3) of a clip that hangs from this one in another option: this clip moves in that option
      // only if its own start is not an alternative there; its end moves with it unless that option gives it an end
      if (y.alt) for (const key of Object.keys(y.alt)) {
        const own = x.alt && x.alt[key];
        if (own && own.at) continue;
        const endHere = own && own.end !== undefined ? !!own.end : !!x.end;
        for (const f of ['at', 'end']) { const a = y.alt[key] && y.alt[key][f]; if (a && a.ref === id && (a.edge === 'start' || !endHere)) a.off = r4((a.off || 0) - dt); }
      }
    }
    return n;
  }

  /* ---------- overlaps: after an edit, anything that now sits on top of another clip goes to a free lane ---------- */
  function lanesOverlap(score, T, ids) {
    const byLane = {};
    for (const [id, e] of Object.entries(score.elements)) (byLane[e.lane] = byLane[e.lane] || []).push(id);
    const hits = [];
    for (const id of ids) {
      const e = score.elements[id]; if (!e || !T[id]) continue;
      const a0 = T[id][0], a1 = Math.max(T[id][1], a0 + .05);
      for (const o of byLane[e.lane] || []) { if (o === id || !T[o]) continue; const b0 = T[o][0], b1 = Math.max(T[o][1], b0 + .05); if (a0 < b1 - 1e-4 && b0 < a1 - 1e-4) { hits.push([id, o]); break; } }
    }
    return hits;
  }
  function fixOverlaps(before, next, Engine, addLane) {
    const T0 = typical(Engine, before).t, T1 = typical(Engine, next).t;
    const changed = Object.keys(next.elements).filter(id => !sameT(T0[id], T1[id]) || !before.elements[id] || before.elements[id].lane !== next.elements[id].lane);
    const moved = [];
    for (const [id] of lanesOverlap(next, T1, changed)) {
      if (!lanesOverlap(next, T1, [id]).length) continue;   // an earlier relocation already freed it
      const e = next.elements[id], g = next.groups.find(x => x.id === e.group);
      const free = g.lanes.find(l => { const keep = e.lane; e.lane = l; const busy = lanesOverlap(next, T1, [id]).length; e.lane = keep; return !busy; });
      const from = e.lane; e.lane = free || addLane(next, e.group); moved.push({ id, from, to: e.lane });
    }
    return moved;
  }

  /* ---------- a score file that can be trusted: structure + references + it computes ----------
     Reads schema 2 (what the editor saves today) and schema 3 (lote 5, design B §2). Schema 3 adds branches / branch / alt,
     gate.blocking, uidMap, baseline and a record shape for `accepted`; they are checked here for SHAPE and for what they
     point to (the engine and the rules judge what they mean). A schema-2 score that carries the structures that only exist
     in schema 3 is refused: the schema number is what tells every reader which engine rules apply. */
  const isNum = v => typeof v === 'number' && Number.isFinite(v);
  const isName = k => typeof k === 'string' && k !== '' && !k.includes('=');   // a branch or an option: "<on>=<value>" keys of `alt` split on '='
  /* the branch fields of schema 3 (§2): branches, element `branch`, `alt` anchors */
  function validateBranches(s, err) {
    const nm = (id, x) => (x && x.key) || id;
    if (s.branches != null) {
      if (!isObj(s.branches)) err('branches is not an object');
      for (const [on, br] of Object.entries(s.branches)) {
        if (!isName(on)) err(`branch "${on}": its name must be a word without "="`);
        if (!isObj(br) || !isObj(br.options)) err(`branch ${on}: options are missing`);
        const opts = Object.keys(br.options);
        if (opts.length < 2) err(`branch ${on}: a decision needs at least two options`);
        for (const o of opts) if (!isName(o) || !isObj(br.options[o])) err(`branch ${on}: option "${o}" must be a word without "=" with an object`);
        if (!opts.includes(br.default)) err(`branch ${on}: its default is not one of its options`);
        if (br.onTimeout != null && !opts.includes(br.onTimeout)) err(`branch ${on}: onTimeout is not one of its options`);
        if (br.gate != null && !(s.elements[br.gate] && s.elements[br.gate].gate)) err(`branch ${on}: its gate is not a wait of the score`);
      }
    }
    const anchor = (a, what) => {
      if (!isObj(a)) err(`${what}: an anchor is an object`);
      if (a.ref != null && a.ref !== '' && !s.beats[a.ref] && !s.elements[a.ref]) err(`${what}: points to something that does not exist`);
      if (a.edge != null && a.edge !== 'start' && a.edge !== 'end') err(`${what}: its edge is "start" or "end"`);
      if (a.off != null && !isNum(a.off)) err(`${what}: its offset is not a number`);
    };
    const alt = (x, who, isBeat) => {
      if (x.alt == null) return;
      if (!isObj(x.alt)) err(`${who}: alt is not an object`);
      for (const [k, v] of Object.entries(x.alt)) {
        const m = /^([^=]+)=([^=]+)$/.exec(k);
        if (!m) err(`${who}: alt key "${k}" is not "<branch>=<option>"`);
        if (!s.branches || !s.branches[m[1]] || !Object.prototype.hasOwnProperty.call(s.branches[m[1]].options, m[2])) err(`${who}: alt "${k}" is not a branch option of the score`);
        if (!isObj(v) || Object.keys(v).some(f => f !== 'at' && f !== 'end') || (v.at === undefined && v.end === undefined)) err(`${who}: alt "${k}" holds an at and/or an end anchor`);
        if (isBeat && v.end !== undefined) err(`${who}: a moment has no end anchor to change in alt "${k}"`);
        for (const f of ['at', 'end']) if (v[f] !== undefined) anchor(v[f], `${who}: alt "${k}" ${f}`);
      }
    };
    for (const [id, e] of Object.entries(s.elements)) {
      if (e.branch != null) {
        const b = e.branch;
        if (!isObj(b) || !s.branches || !s.branches[b.on] || !Object.prototype.hasOwnProperty.call(s.branches[b.on].options, b.value)) err(`${nm(id, e)}: its branch is not a branch option of the score`);
      }
      alt(e, nm(id, e), false);
    }
    for (const [id, b] of Object.entries(s.beats)) alt(b, 'moment ' + nm(id, b), true);
  }
  /* waits and offsets that name an Unreal knob (§2): text only, the integrity rules compare them with Unreal */
  function validateKnobs(s, err) {
    for (const [id, e] of Object.entries(s.elements)) {
      const who = e.key || id, g = e.gate;
      if (g) {
        if (g.blocking !== undefined && typeof g.blocking !== 'boolean') err(`${who}: blocking is true or false`);
        for (const f of ['cond', 'knob']) if (g[f] != null && (typeof g[f] !== 'string' || !g[f])) err(`${who}: the wait's ${f} is a name`);
      }
      for (const f of ['at', 'end']) if (e[f] && e[f].knob != null && (typeof e[f].knob !== 'string' || !e[f].knob)) err(`${who}: the ${f} knob is a name`);
    }
  }
  /* what the APK is assumed to do (baseline), the frozen prototype names → ids (uidMap) and the accepted records */
  function validateRecords(s, err) {
    if (s.baseline != null) {
      const b = s.baseline;
      if (!isObj(b) || !isObj(b.rel)) err('baseline: its relative times (rel) are missing');
      for (const [id, r] of Object.entries(b.rel)) if (!Array.isArray(r) || r.length !== 2 || !r.every(isNum)) err(`baseline: ${id} is not [start in its moment, length]`);
      if (b.total != null && !isNum(b.total)) err('baseline: its total is not a number');
      if (b.log != null && !(Array.isArray(b.log) && b.log.every(isObj))) err('baseline: its log is a list of records');
    }
    if (s.uidMap != null) {
      if (!isObj(s.uidMap)) err('uidMap is not an object');
      for (const [uid, u] of Object.entries(s.uidMap)) if (!isObj(u) || typeof u.id !== 'string' || !u.id || (u.sig != null && typeof u.sig !== 'string') || (u.state != null && typeof u.state !== 'string')) err(`uidMap: ${uid} is not { id, sig, state }`);
    }
    if (s.accepted != null) {
      if (!Array.isArray(s.accepted)) err('accepted is not a list');
      for (const a of s.accepted) {
        if (!isObj(a) || typeof a.fp !== 'string' || !a.fp) err('accepted: a record has no fingerprint');
        if (a.state != null && a.state !== 'accepted' && a.state !== 'reopened') err(`accepted: ${a.fp} is "${a.state}", not accepted or reopened`);
        if (a.history != null && !Array.isArray(a.history)) err(`accepted: the history of ${a.fp} is not a list`);
        if (a.value != null && typeof a.value !== 'string') err(`accepted: the value of ${a.fp} is text`);
      }
    }
  }
  /* what a score says about Unreal once it is bound (lote 5 design A §3.1, §3.5): beats[].marks (which Unreal mark a moment corresponds to)
     and elements[].bind (who an element is in Unreal: action, target, asset). Neither is read by the engine: a malformed one does not
     stop the piece from computing, it stops the file from being saved (the server applies the same rules).
       mark   { name, rel: start|el|in|sub|preview, el?, edge?, by?, why? }: `el` is an element of THAT moment (its edge is the mark);
              a moment has at most one relation of its own (start, in, sub or preview) and it is the first entry; any number of `el`
              entries; a phase mark is placed (start or el) once in the whole score
       bind   { action, target, asset, branch }: action is in the catalog or null; target is role:<role> or tag:<tag> or null; asset is
              the name of an Unreal asset (obra/unreal/idmap.json) or null; branch is reserved (the side of a decision an element plays is
              its own `branch`) */
  const BIND_ACTIONS = ['vo_alma', 'vo_2d', 'sound', 'sound_at', 'appear', 'disappear', 'ghost', 'ambience', 'title', 'veil', 'wait'];
  const MARK_RELS = ['start', 'el', 'in', 'sub', 'preview'];
  const isText = v => typeof v === 'string' && v !== '';
  function validateBind(s, err) {
    const Marks = dep('marks.js', 'Marks'), placed = new Map();
    for (const [id, b] of Object.entries(s.beats)) {
      if (b.marks == null) continue;
      const who = 'moment ' + (b.key || id);
      if (!Array.isArray(b.marks)) err(`${who}: marks is not a list`);
      let own = 0;
      b.marks.forEach((m, i) => {
        if (!isObj(m)) err(`${who}: a mark is an object`);
        if (!Marks.isValid(m.name)) err(`${who}: ${m.name} is not a mark Unreal emits`);
        if (!MARK_RELS.includes(m.rel)) err(`${who}: ${m.name} has relation "${m.rel}"; it is start, el, in, sub or preview`);
        if (m.rel !== 'el' && (++own > 1 || i !== 0)) err(`${who}: its own relation to Unreal (start, in, sub or preview) is one entry, the first`);
        if (m.rel === 'el') {
          if (!isText(m.el) || !s.elements[m.el] || s.elements[m.el].beat !== id) err(`${who}: ${m.name} is the edge of an element that is not in this moment`);
          if (m.edge !== 'start' && m.edge !== 'end') err(`${who}: ${m.name} has no edge (start or end)`);
        }
        if (m.by != null && !(Array.isArray(m.by) && m.by.every(isText))) err(`${who}: the knobs (by) of ${m.name} are a list of names`);
        for (const f of ['why', 'note', 'elKey']) if (m[f] != null && typeof m[f] !== 'string') err(`${who}: the ${f} of ${m.name} is text`);
        // a phase mark is one phase change of Unreal's director: the score places it once (a moment may name it again to say it is inside it)
        if ((m.rel === 'start' || m.rel === 'el') && Marks.isPhase(m.name)) {
          if (placed.has(m.name)) err(`${m.name} is placed twice (moments ${placed.get(m.name)} and ${b.key || id}): Unreal enters it once`);
          placed.set(m.name, b.key || id);
        }
      });
    }
    for (const [id, e] of Object.entries(s.elements)) {
      if (e.bind == null) continue;
      const who = e.key || id, bd = e.bind;
      if (!isObj(bd)) err(`${who}: bind is not an object`);
      if (bd.action != null && !BIND_ACTIONS.includes(bd.action)) err(`${who}: "${bd.action}" is not an action Unreal knows`);
      if (bd.asset != null && !isText(bd.asset)) err(`${who}: the asset is the name of an Unreal asset`);
      if (bd.target != null && !(typeof bd.target === 'string' && /^(role|tag):.+$/.test(bd.target))) err(`${who}: the target is role:<name> or tag:<name>`);
      if (bd.branch != null) err(`${who}: bind.branch is reserved: the side of a decision an element plays is its own branch`);
    }
  }
  /* the first thing validateBind finds wrong, as text, or null: what commit() asks of an edit on a schema 3 score (an edit may not take
     a bound score from saveable to unsaveable without saying so) */
  function bindError(s) {
    if (!s || s.schema !== 3 || !isObj(s.beats) || !isObj(s.elements)) return null;
    try { validateBind(s, m => { throw new Error(m); }); } catch (e) { return e.message; }
    return null;
  }
  /* the same for the decisions (branches): the first thing validateBranches finds wrong, as text, or null. An edit that takes the wait
     which decides SHARE / DON'T SHARE out of the score would leave `branches.share.gate` pointing to nothing: the file is refused at
     the save (S.BRANCH.FIELD) and a draft of it can no longer be opened, so commit() says so before it happens */
  function branchError(s) {
    if (!s || s.schema !== 3 || !isObj(s.beats) || !isObj(s.elements)) return null;
    try { validateBranches(s, m => { throw new Error(m); }); } catch (e) { return e.message; }
    return null;
  }
  /* what an edit must not do to a score that was fine, said before it happens (commit() refuses it; otherwise the score would be
     refused at the save, or break the timeline): take away the wait that decides SHARE / DON'T SHARE, start a moment or a clip before 0:00, or make
     the piece longer than an hour (check.js S.TOTAL: a typed 1e9 would also stop the timeline from drawing). Returns the sentence for the
     toast, or null. Only what is NEW counts: a score that already was like that (a draft, an import) is not blamed for it again.
     o.maxTotal: seconds (default one hour) */
  function wouldBreak(before, next, Engine, o) {
    o = o || {};
    const max = o.maxTotal || 3600, be = branchError(next);
    if (be && !branchError(before)) return `That would break the score (${be}): nothing changed`;
    const T1 = typical(Engine, next), T0 = typical(Engine, before), before0 = (T, id) => !!(T.t[id] && T.t[id][0] < -1e-3);
    const early = Object.keys(next.beats || {}).find(b => before0(T1, b) && !before0(T0, b));
    if (early) return `Moment ${next.beats[early].key} would start before 0:00: nothing changed`;
    const earlyEl = Object.keys(next.elements || {}).find(id => before0(T1, id) && !before0(T0, id));   // a copy dropped far to the left, an API caller: the drag and the fields stop at 0:00 themselves
    if (earlyEl) return `${next.elements[earlyEl].key} would start before 0:00: nothing changed`;
    if (!(T1.total <= max) && T0.total <= max) return 'That would make the piece longer than an hour: type a smaller time. Nothing changed';
    return null;
  }
  /* the decisions whose deciding wait is among these elements: [{ on, name, id, key }] (what the delete verb refuses to take out) */
  function branchGates(score, ids) {
    const want = new Set(ids), out = [];
    if (!score || !isObj(score.branches) || !isObj(score.elements)) return out;
    for (const on of Object.keys(score.branches)) {
      const br = score.branches[on], g = isObj(br) ? br.gate : null;
      if (g != null && want.has(g) && score.elements[g]) out.push({ on, name: br.name || on, id: g, key: score.elements[g].key || g });
    }
    return out;
  }
  /* ---------- an `el` mark hangs on one element of its moment (lote 5 design A §3.1) ----------
     Delete that element and the mark has nothing to hang on: the file would be refused at the save ("S1.OPEN is the edge of an element
     that is not in this moment") without a word before. So an edit that takes the element out takes the mark out with it, in the same
     step and the same undo, and says so:
       marksOf(score, ids)     the `el` marks that name one of these elements (what deleting them would cost; the delete card says it)
       marksLost(before, next) the `el` marks of `before` whose element is no longer in `next` (what an edit cost; the toast says it)
       settleMarks(next)       drops the `el` marks that no longer name an element of their moment, in `next` (mutates it; returns them).
                               A moment left with no mark loses the field. The moment keeps its own relation (start, in, sub, preview)
       marksWords(list)        the sentence for either list */
  const elMark = (b, bt, m, src) => ({ beat: b, moment: bt.key || b, name: m.name, el: m.el, key: (src && src.elements && src.elements[m.el] && src.elements[m.el].key) || m.elKey || m.el, edge: m.edge });
  function marksOf(score, ids) {
    const want = new Set(ids), out = [];
    if (!score || score.schema !== 3 || !isObj(score.beats)) return out;
    for (const [b, bt] of Object.entries(score.beats)) for (const m of Array.isArray(bt.marks) ? bt.marks : []) if (m && m.rel === 'el' && want.has(m.el)) out.push(elMark(b, bt, m, score));
    return out;
  }
  function marksLost(before, next) {
    const out = [];
    if (!before || before.schema !== 3 || !isObj(before.beats)) return out;
    const live = next && isObj(next.elements) ? next.elements : {};
    for (const [b, bt] of Object.entries(before.beats)) for (const m of Array.isArray(bt.marks) ? bt.marks : []) if (m && m.rel === 'el' && !live[m.el]) out.push(elMark(b, bt, m, before));
    return out;
  }
  function settleMarks(next, before) {
    const dropped = [];
    if (!next || next.schema !== 3 || !isObj(next.beats) || !isObj(next.elements)) return dropped;
    for (const [b, bt] of Object.entries(next.beats)) {
      if (!Array.isArray(bt.marks)) continue;
      const keep = bt.marks.filter(m => {
        const bad = m && m.rel === 'el' && !(isText(m.el) && next.elements[m.el] && next.elements[m.el].beat === b);
        if (bad) dropped.push(elMark(b, bt, m, before || next));
        return !bad;
      });
      if (keep.length === bt.marks.length) continue;
      if (keep.length) bt.marks = keep; else delete bt.marks;
    }
    return dropped;
  }
  function marksWords(list) {
    if (!list || !list.length) return '';
    const nm = x => `${x.name} (moment ${x.moment})`;
    return list.length === 1 ? `${nm(list[0])} loses its Unreal mark` : `${list.length} Unreal marks are lost: ${list.slice(0, 3).map(nm).join(', ')}${list.length > 3 ? ', …' : ''}`;
  }
  /* what exists only in schema 3 (it changes how the engine times the piece, or who is in the file) */
  const SCHEMA3_ONLY = s => {
    const found = [];
    for (const k of ['branches', 'baseline', 'uidMap']) if (s[k] != null) found.push(k);
    for (const e of Object.values(s.elements || {})) {
      if (e.branch != null && !found.includes('branch')) found.push('branch');
      if (e.alt != null && !found.includes('alt')) found.push('alt');
      if (e.gate && e.gate.blocking !== undefined && !found.includes('gate.blocking')) found.push('gate.blocking');
      if (e.bind != null && !found.includes('bind')) found.push('bind');
    }
    for (const b of Object.values(s.beats || {})) { if (b.alt != null && !found.includes('alt')) found.push('alt'); if (b.marks != null && !found.includes('marks')) found.push('marks'); }
    return found;
  }
  function validate(s, Engine) {
    const err = m => { throw new Error(m); };
    if (!s || typeof s !== 'object' || (s.schema !== 2 && s.schema !== 3)) err(s && Number.isInteger(s.schema) && s.schema > 3 ? `this is a schema ${s.schema} score: this editor reads schema 2 and 3` : 'not a schema 2 or 3 score');
    for (const k of ['acts', 'groups']) if (!Array.isArray(s[k])) err(k + ' is missing');
    for (const k of ['beats', 'lanes', 'elements']) if (!s[k] || typeof s[k] !== 'object') err(k + ' is missing');
    for (const a of s.acts) for (const b of a.beats || []) if (!s.beats[b]) err(`act ${a.id} points to a missing moment ${b}`);
    for (const g of s.groups) for (const l of g.lanes || []) if (!s.lanes[l]) err(`group ${g.id} points to a missing lane ${l}`);
    for (const [id, e] of Object.entries(s.elements)) {
      if (!s.beats[e.beat]) err(`${e.key || id}: missing moment`);
      if (!s.lanes[e.lane]) err(`${e.key || id}: missing lane`);
      if (!s.groups.some(g => g.id === e.group)) err(`${e.key || id}: missing group`);
      for (const f of ['at', 'end']) if (e[f] && e[f].ref && !s.beats[e[f].ref] && !s.elements[e[f].ref]) err(`${e.key || id}: ${f} points to something that does not exist`);
      if (e.dur && !(e.dur.value >= 0)) err(`${e.key || id}: duration is not a number`);
      if (e.gate && !(e.gate.fw > 0 && e.gate.expected >= 0)) err(`${e.key || id}: wait times are not numbers`);
    }
    if (s.schema === 2) { const only = SCHEMA3_ONLY(s); if (only.length) err(`a schema 2 score can't have ${only.join(', ')}: those belong to schema 3`); }
    else { validateBranches(s, err); validateKnobs(s, err); validateRecords(s, err); validateBind(s, err); }
    const r = typical(Engine, s); if (!(r.total >= 0)) err('the timeline does not compute');
    return r;
  }

  /* ---------- an anchor loop (a moment whose end depends on a later moment): two honest ways out ----------
     keep  = the next moment starts with this one, as it does today (and in the prototype): nothing moves
     order = the next moment follows this one's end, as the script reads: what hung from later moments is pinned to its own */
  function planLoop(score, beatId, Engine) {
    const T0 = typical(Engine, score), order = score.acts.flatMap(a => a.beats), i = order.indexOf(beatId), nb = order[i + 1];
    if (i < 0 || !nb) return null;
    const idx = Object.fromEntries(order.map((b, k) => [b, k])), beatOf = id => score.beats[id] ? id : (score.elements[id] || {}).beat;
    const later = (id, depth, seen) => {
      if (depth > 8 || seen.has(id)) return false; seen.add(id); const x = score.elements[id]; if (!x) return false;
      for (const a of [x.at, x.end]) { if (!a || !a.ref) continue; if (idx[beatOf(a.ref)] > i) return true; if (score.elements[a.ref] && later(a.ref, depth + 1, seen)) return true; }
      return false;
    };
    const K = clone(score); K.beats[nb].at = { ref: beatId, edge: 'start', off: r4(T0.t[nb][0] - T0.t[beatId][0]) };
    const O = clone(score), pinned = [];
    for (const id of Object.keys(score.elements)) {
      const e = score.elements[id]; if (e.beat !== beatId || e.help) continue;
      if (e.end && e.end.ref && beatOf(e.end.ref) !== beatId) continue;   // spans into later moments: already outside the moment's end
      if (e.at && e.at.ref && later(id, 0, new Set())) { O.elements[id].at = { ref: beatId, edge: 'start', off: r4(T0.t[id][0] - T0.t[beatId][0]) }; pinned.push(id); }
    }
    const TK = typical(Engine, K), TO = typical(Engine, O);
    return { next: nb, keep: { next: K, ok: !TK.cycles.includes(beatId), total0: T0.total, total1: TK.total },
      order: { next: O, ok: !TO.cycles.includes(beatId) && pinned.length > 0, pinned, total0: T0.total, total1: TO.total, nextStart0: T0.t[nb][0], nextStart1: TO.t[nb][0] } };
  }

  /* ---------- change the anchor of an element or a moment (audit C9): a new anchor, the same time ----------
     It keeps its start with the TYPICAL user: off = its start − the new anchor's edge. Refused, with the reason, when it
     would make a loop: anchored to itself, to a time that depends on its start (whatever is anchored to it or lasts until
     it, directly or through others, and the moments that wait for it), or any new loop the engine finds. newAnchor null =
     detach: an element goes to the start of its own moment, a moment follows the previous one. The other simulated users
     may shift (a wait between the old anchor and the new one lasts differently for them): `others` says by how much.
     opts.field 'end' does the same with what an element lasts until (`end`): it keeps its END time; detach = the start
     of its own moment. Only the repair of a lost anchor uses it today (detachLost). */
  const beatOrder = s => s.acts.flatMap(a => a.beats);
  const edgeOf = a => a && a.ref ? (a.edge === 'start' ? 'start' : 'end') : 'start';   // the engine reads anything but 'start' as the end
  function homeAnchor(score, id) {
    if (score.elements[id]) return { ref: score.elements[id].beat, edge: 'start' };
    const o = beatOrder(score), i = o.indexOf(id);
    return i > 0 ? { ref: o[i - 1], edge: 'end' } : { ref: null, edge: 'start' };
  }
  /* the anchor it has now (a moment without one follows the previous moment) */
  function anchorOf(score, id) {
    const x = nodeOf(score, id), a = x && x.at;
    return a ? { ref: a.ref || null, edge: edgeOf(a) } : homeAnchor(score, id);
  }
  /* every time point ('id|S' start, 'id|E' end) that depends on the start of id (or on its end: from = 'end'),
     each with the point it comes from */
  function hangingFrom(score, id, Engine, from) {
    const kids = Engine.dependents(score), order = beatOrder(score), nextB = {};
    order.forEach((b, i) => { nextB[b] = order[i + 1]; });
    const counts = Engine.inBeatEnd || (() => true);   // an older engine: assume it counts (refuses more, never less)
    const pt = (ref, edge) => ref + (edge === 'start' ? '|S' : '|E');
    const p0 = pt(id, from === 'end' ? 'end' : 'start'), par = new Map([[p0, null]]), st = [p0];
    const add = (p, from) => { if (!par.has(p)) { par.set(p, from); st.push(p); } };
    while (st.length) {
      const p = st.pop(), i = p.lastIndexOf('|'), n = p.slice(0, i), end = p.slice(i + 1) === 'E';
      if (!end) add(n + '|E', p);   // its end comes after its start
      for (const k of kids[n] || []) {
        const x = nodeOf(score, k); if (!x) continue;
        // its own anchors and, in schema 3, the alternative ones (a loop in one option of SHARE is a loop)
        for (const { f, a } of Engine.anchorsOf ? Engine.anchorsOf(x, score.beats[k] ? ['at'] : undefined) : [{ f: 'at', a: x.at }, { f: 'end', a: x.end }]) {
          if (!a || a.ref !== n || pt(n, edgeOf(a)) !== p) continue;
          if (f === 'at') add(k + '|S', p); else if (score.elements[k]) add(k + '|E', p);
        }
      }
      if (end && score.beats[n] && nextB[n] && !score.beats[nextB[n]].at) add(nextB[n] + '|S', p);   // the next moment follows this one
      if (end && score.elements[n] && counts(score, n)) add(score.elements[n].beat + '|E', p);         // its moment ends with its last element
    }
    return par;
  }
  function reanchor(score, id, newAnchor, Engine, opts) {
    opts = opts || {};
    const x = nodeOf(score, id); if (!x) return { ok: false, why: 'It no longer exists' };
    const field = opts.field === 'end' ? 'end' : 'at', isEnd = field === 'end', ti = isEnd ? 1 : 0;
    const keys = {}; for (const e of Object.values(score.elements)) keys[e.key] = (keys[e.key] || 0) + 1;   // PASO is in five moments: say which
    const name = r => { if (score.beats[r]) return 'moment ' + score.beats[r].key; const e = score.elements[r]; if (!e) return r; return e.key + (keys[e.key] > 1 && score.beats[e.beat] ? ' in ' + score.beats[e.beat].key : ''); };
    const me = name(id), Me = me[0].toUpperCase() + me.slice(1);
    if (isEnd && !score.elements[id]) return { ok: false, why: `${Me} has no end anchor: a moment ends with its last element` };
    if (isEnd && !x.end) return { ok: false, why: `${Me} has a length, not an end anchor` };
    const home = isEnd ? { ref: x.beat, edge: 'start' } : homeAnchor(score, id);
    const a = newAnchor ? { ref: newAnchor.ref || null, edge: newAnchor.ref ? edgeOf(newAnchor) : 'start' } : home;
    const where = a.ref ? `the ${a.edge} of ${name(a.ref)}` : 'the start of the piece';
    if (a.ref && !nodeOf(score, a.ref)) return { ok: false, why: 'That anchor no longer exists' };
    if (a.ref === id) return { ok: false, self: true, why: isEnd ? `${Me} can't last until itself` : `${Me} can't be anchored to itself` };
    const cur = isEnd ? { ref: x.end.ref || null, edge: edgeOf(x.end) } : anchorOf(score, id);
    if (cur.ref === a.ref && cur.edge === a.edge) return { ok: false, same: true, why: isEnd ? `${Me} already lasts until ${where}` : `${Me} is already anchored to ${where}` };
    // a loop we can name: the new anchor waits for this very start (or end)
    const dep = hangingFrom(score, id, Engine, isEnd ? 'end' : 'start'), target = a.ref && a.ref + (a.edge === 'start' ? '|S' : '|E');
    if (target && dep.has(target)) {
      const via = []; for (let p = dep.get(target); p && dep.get(p); p = dep.get(p)) { const n = p.slice(0, p.lastIndexOf('|')); if (n !== a.ref && n !== id && !via.includes(n)) via.unshift(n); }
      const W = where[0].toUpperCase() + where.slice(1);
      return { ok: false, loop: true, why: `${W} depends on ${isEnd ? 'the end of ' : ''}${me}${via.length ? ' (through ' + via.slice(0, 3).map(name).join(', ') + (via.length > 3 ? '…' : '') + ')' : ''}: ${isEnd ? 'ending' : 'anchoring'} ${me} there would make a loop` };
    }
    const T0 = typical(Engine, score), n = clone(score), y = nodeOf(n, id);
    y[field] = { ref: a.ref, edge: a.edge, off: r4(T0.t[id][ti] - edgeT(T0.t, a)) };   // whatever else the old anchor said was about the old anchor
    const T1 = typical(Engine, n), was = new Set(T0.cycles), loop = T1.cycles.find(c => !was.has(c));
    if (loop) return { ok: false, loop: true, why: `${isEnd ? 'Ending' : 'Anchoring'} ${me} ${isEnd ? 'at' : 'to'} ${where} would make a loop through ${name(loop)}` };
    // the promise: nothing changes time with the typical user, not even itself
    const moved = Object.keys(n.elements).concat(Object.keys(n.beats)).filter(k => !sameT(T0.t[k], T1.t[k]));
    if (moved.length) {
      // an end inside its own moment counts in that moment's end (engine inBeatEnd): say so when that is what moves
      const longer = isEnd && Engine.inBeatEnd && Engine.inBeatEnd(n, id) && !Engine.inBeatEnd(score, id) && !sameT(T0.t[x.beat], T1.t[x.beat]);
      return { ok: false, why: `${Me} can't keep its ${isEnd ? 'end' : 'time'} ${isEnd ? 'lasting until' : 'anchored to'} ${where}: ${moved.length} item${moved.length > 1 ? 's' : ''} would move${longer ? ` (its end would then make ${name(x.beat)} last longer)` : T0.cycles.length ? ' (an anchor loop in the score is computed in order: fix it first in Problems)' : ''}` };
    }
    const others = {};
    if (opts.others !== false) for (const p of Object.keys(Engine.PERSONAS)) {
      if (p === 'typical') continue;
      const d = Engine.resolve(n, { persona: p }).t[id][ti] - Engine.resolve(score, { persona: p }).t[id][ti];
      if (Math.abs(d) > .05) others[p] = r4(d);
    }
    return { ok: true, next: n, field, at: y[field], was: cur, others };   // `at` = the new anchor of that field
  }

  /* ---------- "Match Unreal" for a time that IS an Unreal knob (lote 5 design B §6.3) ----------
     Unreal decides WHEN some lines play with a knob counted from another element (VO_11h: BP_BreathStage_SC.HelpAfter seconds after
     VO_11b ends). The element takes the anchor Unreal has, `ref.edge + knob`, in the moment of `ref`, and carries the knob's name
     (`at.knob`) so Integrity's C3.KNOB.OFFSET can tell later whether it still agrees. Unlike reanchor() this MOVES the element: the
     time is Unreal's, not the score's; it keeps everything else (its help wait, its lane, its length). The "≠ APK" reference moves
     for that element only (shiftBaseline; schema 2: the golden), so what it now does is not "different from the APK".
     spec = { ref (id), edge, off, knob (name), at (ISO), by }. Pure: never changes the score it gets.
     → { ok:false, why } | { ok:true, next, at, beat, t0, t1, moved: [ids that also move, typical], users: { persona: { t0, t1, total0,
       total1, help0, help1, acts, comes0, comes } } } with acts = when that user acts counted from the start of the wait and comes0 /
       comes = when the line plays (before / after), counted from the same point (only for a help line of a wait).
       Whether a user hears the line is read as Unreal plays it: its stage runs on a clock, the line comes at the place the chain
       puts it (the typical user's, counted from the start of the wait) and plays only if the user has not acted by then. The engine
       of a schema 2 score makes a slow user wait at G_BREATH before the next moment even starts, which would put the line after
       the wait for them (and the idle user would "stop hearing" a line that Unreal does play): not what the card should say */
  function matchKnobAnchor(score, id, spec, Engine) {
    const x = score.elements[id]; if (!x) return { ok: false, why: 'It no longer exists' };
    const ref = nodeOf(score, spec.ref); if (!ref) return { ok: false, why: 'The element Unreal counts it from is not in the score' };
    if (spec.ref === id) return { ok: false, why: "It can't be anchored to itself" };
    if (!isNum(spec.off)) return { ok: false, why: 'The knob has no value to count' };
    const edge = spec.edge === 'start' ? 'start' : 'end', n = clone(score), y = n.elements[id];
    y.at = { ref: spec.ref, edge, off: r4(spec.off), knob: spec.knob };
    y.beat = score.elements[spec.ref] ? score.elements[spec.ref].beat : spec.ref;
    const T0 = typical(Engine, score), T1 = typical(Engine, n), was = new Set(T0.cycles), loop = T1.cycles.find(c => !was.has(c));
    const nm = k => (nodeOf(score, k) || {}).key || k;
    if (loop) return { ok: false, loop: true, why: `${x.key} counted from ${nm(spec.ref)} would make a loop through ${nm(loop)}` };
    if (T1.dangling.length > T0.dangling.length) return { ok: false, why: 'An anchor would point to nothing' };
    const moved = Object.keys(n.elements).concat(Object.keys(n.beats)).filter(k => k !== id && !sameT(T0.t[k], T1.t[k]));
    const users = {}, w = x.help && T0.t[x.help] && T1.t[x.help] ? x.help : null, c0 = w ? T0.t[id][0] - T0.t[w][0] : null, c1 = w ? T1.t[id][0] - T1.t[w][0] : null;
    for (const p of Object.keys(Engine.PERSONAS)) {
      const a = Engine.resolve(score, { persona: p }), b = Engine.resolve(n, { persona: p }), acts = w ? Engine.PERSONAS[p].wait(score.elements[w].gate) : null;
      users[p] = { t0: a.t[id][0], t1: b.t[id][0], total0: a.total, total1: b.total, acts, comes0: c0, comes: c1,
        help0: w ? c0 < acts - 1e-6 : null, help1: w ? c1 < acts - 1e-6 : null };
    }
    // the reference moves for this element only
    const entry = { op: 'match-unreal', at: spec.at || new Date().toISOString(), by: spec.by || null, ids: [id], knob: spec.knob };
    if (n.baseline && n.baseline.rel) n.baseline = shiftBaseline(n.baseline, { score, sched: T0 }, { score: n, sched: T1 }, [id], entry);
    else if (n.golden && n.golden.times) n.golden = shiftGolden(n.golden, T0, T1, null, [id]);
    return { ok: true, next: n, at: y.at, beat: y.beat, t0: T0.t[id][0], t1: T1.t[id][0], moved, users };
  }

  /* ---------- branches in the editor (lote 5 design B §5.3) ---------- */
  const has2 = (o, k) => !!o && Object.prototype.hasOwnProperty.call(o, k);
  const splitKey = k => { const m = /^([^=]+)=([^=]+)$/.exec(k || ''); return m ? { on: m[1], opt: m[2] } : null; };
  const optionLabel = (score, k) => { const p = splitKey(k), o = p && score.branches && score.branches[p.on] && score.branches[p.on].options[p.opt]; return (o && o.label) || (p ? p.opt : k); };
  /* the anchors of one element or moment that depend on a decision (what the inspector's "Anchor in DON'T SHARE" shows): one entry
     per option and field where it has an anchor of its own (alt: its anchor there) or where its anchor points to something of the
     other option (cross: it needs one). [{ k: 'share=no', on, opt, field: 'at' | 'end', alt, cross }]; structure only, no times */
  function branchAnchors(score, id) {
    const x = nodeOf(score, id), out = []; if (!x || !score.branches) return out;
    const isEl = !!score.elements[id];
    for (const on of Object.keys(score.branches)) for (const opt of Object.keys(score.branches[on].options || {})) {
      const k = on + '=' + opt, here = !isEl || !x.branch || x.branch.on !== on || x.branch.value === opt;   // is it there in that option?
      for (const f of isEl ? ['at', 'end'] : ['at']) {
        const alt = x.alt && x.alt[k] && x.alt[k][f] || null, prim = x[f], tg = prim && prim.ref && score.elements[prim.ref];
        const cross = !!(here && !alt && tg && tg.branch && tg.branch.on === on && tg.branch.value !== opt);
        if (alt || cross) out.push({ k, on, opt, field: f, alt, cross });
      }
    }
    return out;
  }
  /* which side of a decision some elements belong to: value null = both sides (no branch). Pure; says why when it cannot */
  function setBranch(score, ids, on, value) {
    const br = score.branches && score.branches[on];
    if (!br) return { ok: false, why: 'This score has no such decision' };
    if (value != null && !has2(br.options, value)) return { ok: false, why: 'That is not a side of this decision' };
    const n = clone(score), changed = [];
    for (const id of ids) {
      const x = n.elements[id]; if (!x) continue;
      const was = x.branch && x.branch.on === on ? x.branch.value : null;
      if (was === value) continue;
      if (value == null) delete x.branch; else x.branch = { on, value };
      changed.push(id);
    }
    return changed.length ? { ok: true, next: n, changed } : { ok: false, same: true, why: 'Already there' };
  }
  /* ---------- the anchor of one option of a decision (alt, "Anchor in DON'T SHARE") ----------
     Same promise as reanchor, in ONE option: it keeps its time there with the typical user, and nothing else moves in ANY option
     (not its primary anchor, which is every other option, nor another alternative). k = "<branch>=<option>"; opts.field 'end' does
     the same with what it lasts until. newAnchor null = "the same anchor as everywhere else": the alternative goes away, allowed only
     when that keeps every time and nothing is left hanging from the other option. Refused, with the reason, when the new anchor is
     not there in that option, would make a loop, or would move something. */
  function reanchorAlt(score, id, k, newAnchor, Engine, opts) {
    opts = opts || {};
    const x = nodeOf(score, id); if (!x) return { ok: false, why: 'It no longer exists' };
    const kp = splitKey(k), br = kp && score.branches && score.branches[kp.on];
    if (!br || !has2(br.options, kp.opt)) return { ok: false, why: 'This score has no such option to anchor in' };
    const isB = !!score.beats[id], field = opts.field === 'end' ? 'end' : 'at', isEnd = field === 'end', ti = isEnd ? 1 : 0, lab = optionLabel(score, k);
    const keys = {}; for (const e of Object.values(score.elements)) keys[e.key] = (keys[e.key] || 0) + 1;
    const name = r => { if (score.beats[r]) return 'moment ' + score.beats[r].key; const e = score.elements[r]; if (!e) return r; return e.key + (keys[e.key] > 1 && score.beats[e.beat] ? ' in ' + score.beats[e.beat].key : ''); };
    const me = (isB ? 'moment ' : '') + x.key, Me = me[0].toUpperCase() + me.slice(1);
    const cur = x.alt && x.alt[k] && x.alt[k][field] || null, prim = isEnd ? x.end : x.at;
    if (isEnd && (isB || (!prim && !cur))) return { ok: false, why: isB ? Me + ' has no end anchor: a moment ends with its last element' : Me + ' has a length, not an end anchor' };
    const R0 = runsOf(score, Engine), run = tIn(R0, k), T0 = run.t;
    let a = null;
    if (newAnchor == null) {
      if (!cur) return { ok: false, same: true, why: Me + ' has no anchor of its own in ' + lab };
    } else {
      a = { ref: newAnchor.ref || null, edge: newAnchor.ref ? edgeOf(newAnchor) : 'start' };
      if (!a.ref) return { ok: false, why: 'Pick a clip or a moment' };
      if (!nodeOf(score, a.ref)) return { ok: false, why: 'That anchor no longer exists' };
      const where = 'the ' + a.edge + ' of ' + name(a.ref);
      if (a.ref === id) return { ok: false, self: true, why: isEnd ? Me + " can't last until itself" : Me + " can't be anchored to itself" };
      if (run.off && run.off[a.ref]) return { ok: false, why: name(a.ref) + ' is not there in ' + lab + ': ' + me + " can't hang from it there" };
      const now = cur || prim;
      if (now && (now.ref || null) === a.ref && edgeOf(now) === a.edge) return { ok: false, same: true, why: cur ? Me + ' already hangs from ' + where + ' in ' + lab : Me + ' already hangs from ' + where + ' (in ' + lab + ' too): pick something else for ' + lab };
      // a loop we can name: the new anchor waits for this very start (or end), in any option
      const dep = hangingFrom(score, id, Engine, isEnd ? 'end' : 'start'), target = a.ref + (a.edge === 'start' ? '|S' : '|E');
      if (dep.has(target)) return { ok: false, loop: true, why: where[0].toUpperCase() + where.slice(1) + ' depends on ' + (isEnd ? 'the end of ' : '') + me + ': ' + (isEnd ? 'ending' : 'anchoring') + ' ' + me + ' there in ' + lab + ' would make a loop' };
    }
    const n = clone(score), y = nodeOf(n, id);
    if (a) { y.alt = y.alt || {}; y.alt[k] = y.alt[k] || {}; y.alt[k][field] = { ref: a.ref, edge: a.edge, off: r4(T0[id][ti] - edgeT(T0, a)) }; }
    else { delete y.alt[k][field]; if (!Object.keys(y.alt[k]).length) delete y.alt[k]; if (!Object.keys(y.alt).length) delete y.alt; }
    const R1 = runsOf(n, Engine), was = new Set(R0.flatMap(r => r.cycles)), loop = R1.flatMap(r => r.cycles).find(c => !was.has(c));
    if (loop) return { ok: false, loop: true, why: Me + ' there in ' + lab + ' would make a loop through ' + name(loop) };
    const wasCross = new Set(R0.flatMap(r => r.crossBranch)), cross = R1.flatMap(r => r.crossBranch).find(c => !wasCross.has(c));
    if (cross) return { ok: false, why: name(cross) + ' would be left hanging from something that is not there in ' + lab + ': give it an anchor of its own first' };
    // the promise: nothing changes time, in any option, with the typical user
    const moved = Object.keys(n.elements).concat(Object.keys(n.beats)).filter(i => movedIn(R0, R1, i));
    if (moved.length) return { ok: false, why: Me + " can't keep its " + (isEnd ? 'end' : 'time') + ' in ' + lab + ' like that: ' + moved.length + ' item' + (moved.length > 1 ? 's' : '') + ' would move' };
    const others = {}, want = {}; for (const b of Object.keys(score.branches)) want[b] = b === kp.on ? kp.opt : 'default';
    if (opts.others !== false) for (const p of Object.keys(Engine.PERSONAS)) {
      if (p === 'typical') continue;
      const d = Engine.resolve(n, { persona: p, branch: want }).t[id][ti] - Engine.resolve(score, { persona: p, branch: want }).t[id][ti];
      if (Math.abs(d) > .05) others[p] = r4(d);
    }
    return { ok: true, next: n, field, k, at: a ? Object.assign({}, y.alt[k][field]) : null, was: cur, others, label: lab };   // at = the new alternative (null: it went away)
  }

  /* ---------- an anchor to something that no longer exists (C1.ANCHOR.MISSING): detach it where it falls now ----------
     The engine reports the item when its start (`at`) OR, for an element, what it lasts until (`end`) points to a missing id.
     lostAnchors says which; detachLost repairs each one at the time it falls back to with the typical user: a lost start goes
     to the start of its moment (a moment: after the previous one), a lost end to the start of its own moment + the same end
     time. An anchor that still exists is never touched. Refused with the reason if anything would move. */
  function lostAnchors(score, id) {
    const x = nodeOf(score, id); if (!x) return [];
    return ['at', 'end'].filter(f => x[f] && x[f].ref && !nodeOf(score, x[f].ref) && (f === 'at' || !!score.elements[id]));
  }
  function detachLost(score, id, Engine) {
    if (!nodeOf(score, id)) return { ok: false, why: 'It no longer exists' };
    const fields = lostAnchors(score, id); if (!fields.length) return { ok: false, why: 'Its anchors all exist: nothing to repair' };
    let s = score; const done = [];
    for (const f of fields) {
      const r = reanchor(s, id, null, Engine, { field: f, others: false });
      if (!r.ok) return { ok: false, field: f, why: r.why };
      s = r.next; done.push({ field: f, anchor: r.at });
    }
    const others = {};   // which simulated users hear it somewhere else (its start, else its end)
    for (const p of Object.keys(Engine.PERSONAS)) {
      if (p === 'typical') continue;
      const a = Engine.resolve(score, { persona: p }).t[id], b = Engine.resolve(s, { persona: p }).t[id];
      const d = Math.abs(b[0] - a[0]) > .05 ? b[0] - a[0] : b[1] - a[1];
      if (Math.abs(d) > .05) others[p] = r4(d);
    }
    return { ok: true, next: s, fields: done, others };
  }

  /* ---------- several at once (audit C10): move a selection by dt ----------
     Every selected clip lands dt later with the TYPICAL user, in one edit. A selected clip that already follows another
     selected one (anchored to it, directly or through others, or pushed by its moment) is never moved twice: each one is
     measured after the others moved and only what is still missing goes to its own offset. opts.alone = as in move():
     what hangs from them and is not selected stays where it was.
     opts.ks (schema 3): the options on screen ("share=no"). What you see move is what moves: "dt later" is measured in the first
     of them, and a clip that hangs from something else of its own there (an alt start) takes it in that anchor, as move() does. */
  function moveMany(score, ids, dt, opts, Engine, kids) {
    opts = opts || {};
    ids = [...new Set(ids)].filter(id => score.elements[id]); kids = kids || Engine.dependents(score);
    const view = (opts.ks || [])[0] || null, run = s => (view ? runOf(s, Engine, view) : typical(Engine, s)).t;
    const T0 = run(score), order = ids.slice().sort((a, b) => T0[a][0] - T0[b][0]);
    let n = clone(score), T = T0;
    for (let pass = 0; pass < 8; pass++) {   // one pass, unless a clip is anchored BEFORE what it hangs from (then one per link)
      let any = false;
      for (const id of order) {
        const d = r4(T0[id][0] + dt - T[id][0]); if (Math.abs(d) < 5e-4) continue;
        n = move(n, id, d, opts, kids); T = run(n); any = true;
      }
      if (!any) break;
    }
    return n;
  }

  /* ---------- copy, paste, duplicate (audit C10) ----------
     A copy is a NEW element: a new id, a unique key (VO_05 → VO_05_2), isNew (the contract ignores it: Unreal does not have
     it, so the inspector says "not in Unreal yet") and no legacy (no 3D yet). Anchors INSIDE the copied set go to the copies;
     an anchor to anything else (another element, a moment, the start of the piece) becomes the start of the target moment,
     at the time it had, so the copies keep their layout with the typical user. A help line stays one only with its wait.
     Schema 3: a copy of a clip that has an anchor of its own in another option of a decision (alt: VO_37 hangs from VO_35c in
     DON'T SHARE) keeps that too. An alternative anchor to a copy goes to the copy; one to anything else goes to the start of the
     target moment, like the primary one, at the time the original has in that option: the copy lands there where it lands in
     SHARE (the same place among its neighbours), instead of hanging from the original's neighbour. */
  const uniqueKey = (taken, base) => { if (!taken.has(base)) return base; let i = 2; while (taken.has(base + '_' + i)) i++; return base + '_' + i; };
  /* a copy of a copy counts from the original: VO_05_2 → VO_05_3, never VO_05_2_2 (only when its key is still original_N) */
  function keyBase(score, el) {
    let r = el; const seen = new Set();
    while (r.copyOf && score.elements[r.copyOf] && !seen.has(r.copyOf)) { seen.add(r.copyOf); r = score.elements[r.copyOf]; }
    return r !== el && el.key.startsWith(r.key + '_') && /^\d+$/.test(el.key.slice(r.key.length + 1)) ? r.key : el.key;
  }
  /* a new id (lote 5 design B §2): prefix + time in base 36 + 4 random base-36 chars, never one in use (in the elements, moments,
     lanes or the uidMap of the score, nor in o.taken: the ids made in this same batch). Tests inject now (a number or a function
     that gives it) and rand (a function that gives [0, 1)). The server accepts el_ + 3 to 40 letters or digits */
  function newId(score, prefix, o) {
    o = o || {}; const now = typeof o.now === 'number' ? () => o.now : o.now || Date.now, rand = o.rand || Math.random, also = o.taken;
    const inMap = id => !!score.uidMap && Object.values(score.uidMap).some(u => u && u.id === id);
    for (let k = 0; k < 1000; k++) {
      let id = (prefix || 'el_') + now().toString(36); for (let i = 0; i < 4; i++) id += Math.floor(rand() * 36).toString(36);
      if (!score.elements[id] && !score.beats[id] && !score.lanes[id] && !(also && also.has(id)) && !inMap(id)) return id;
    }
    throw new Error('no free id');
  }
  /* what Ctrl+C keeps: the elements as they are and their times with the typical user (the layout to paste) */
  function clipOf(score, ids, Engine) {
    const R = runsOf(score, Engine), T = R[0].t;
    // schema 3: where each one is in the other options of a decision too (ks), so a copy of a clip that hangs from something else
    // there keeps its layout there as well
    const items = [...new Set(ids)].filter(id => score.elements[id] && T[id]).sort((a, b) => T[a][0] - T[b][0] || T[a][1] - T[b][1])
      .map(id => {
        const it = { id, el: clone(score.elements[id]), s: r4(T[id][0]), e: r4(T[id][1]) };
        if (R.length > 1) { it.ks = {}; for (const r of R.slice(1)) if (r.t[id]) it.ks[r.k] = { s: r4(r.t[id][0]), e: r4(r.t[id][1]), off: !!(r.off && r.off[id]) }; }
        return it;
      });
    return { items, t0: items.length ? Math.min(...items.map(i => i.s)) : 0, t1: items.length ? Math.max(...items.map(i => i.e)) : 0 };
  }
  const addLaneTo = (n, gid) => { const g = n.groups.find(x => x.id === gid); let i = g.lanes.length + 1, id; do { id = 'ln_' + gid + '_' + (i++); } while (n.lanes[id]); n.lanes[id] = { name: g.name + ' ' + (g.lanes.length + 1), group: gid }; g.lanes.push(id); return id; };
  /* target { beat, off }: paste, every copy in that moment, the first one off seconds after its start.
     target { dt }: Alt+drag, each copy in the moment of its original, dt seconds after where its original was when copied
       (where the drag showed it), whatever the copies of earlier moments do to the moments after them.
     target { after: true }: Ctrl+D, each copy in the moment of its original, right after itself: per moment, the span of
       what is duplicated from that moment (an instant: 1 s), measured from its original where it ends up.
     opts: who, at (ISO), now/rand (ids), addLane(n, gid), lanes { originalId: laneId | 'new' } (Alt+drag onto a lane) */
  function planPaste(score, clip, target, Engine, opts) {
    opts = opts || {};
    const items = (clip && clip.items) || [], after = !!target && !!target.after, dup = after || (!!target && target.dt != null);
    if (!items.length) return { ok: false, why: 'Nothing copied yet: select clips and press Ctrl+C' };
    if (!dup && !(target && score.beats[target.beat])) return { ok: false, why: 'That moment no longer exists' };
    for (const it of items) {
      if (dup && !score.beats[it.el.beat]) return { ok: false, why: `The moment of ${it.el.key} no longer exists` };
      if (!score.groups.some(g => g.id === it.el.group)) return { ok: false, why: `The group of ${it.el.key} no longer exists` };
      if (after && !score.elements[it.id]) return { ok: false, why: `${it.el.key} no longer exists` };
    }
    const RA0 = runsOf(score, Engine), R0 = RA0[0], T = R0.t, t0 = Math.min(...items.map(i => i.s)), n = clone(score), map = {}, made = new Set();
    const taken = new Set(Object.values(score.elements).map(e => e.key)), at = opts.at || new Date().toISOString();
    for (const it of items) { const id = newId(score, 'el_', { now: opts.now, rand: opts.rand, taken: made }); made.add(id); map[it.id] = id; }
    // Ctrl+D: per moment, how far "right after itself" is
    const span = {};
    if (after) for (const it of items) { const sp = span[it.el.beat] || (span[it.el.beat] = [Infinity, -Infinity]); sp[0] = Math.min(sp[0], it.s); sp[1] = Math.max(sp[1], it.e); }
    const dtOf = b => span[b][1] - span[b][0] > .05 ? span[b][1] - span[b][0] : 1;
    // where each copy starts with the typical user, on the timeline Tn being built (it keeps the length it was copied with)
    const startOf = (it, Tn) => after ? Tn[it.id][0] + dtOf(it.el.beat) : dup ? it.s + target.dt : Tn[target.beat][0] + target.off + (it.s - t0);
    // the same in one option of a decision (schema 3), for the copies that have an anchor of their own there: where the original is
    // in that option (a clip that does not play there counts only if nothing in the copy does)
    const altKeys = [...new Set(items.flatMap(it => Object.keys(it.el.alt || {})))];
    const sk = (it, k) => (it.ks && it.ks[k]) || { s: it.s, e: it.e, off: false };
    const t0k = {};
    for (const k of altKeys) { const live = items.filter(i => !sk(i, k).off); t0k[k] = Math.min(...(live.length ? live : items).map(i => sk(i, k).s)); }
    const startOfK = (it, Tn, k) => after ? Tn[it.id][0] + dtOf(it.el.beat) : dup ? sk(it, k).s + target.dt : Tn[target.beat][0] + target.off + (sk(it, k).s - t0k[k]);
    const ids = [];
    for (const it of items) {
      const id = map[it.id], b = dup ? it.el.beat : target.beat, s = startOf(it, T);
      const inside = a => a && a.ref && map[a.ref] ? { ref: map[a.ref], edge: a.edge, off: a.off || 0 } : null;
      const x = clone(it.el);
      x.beat = b; x.lane = null;   // lanes below, once every copy has its time
      x.at = inside(x.at) || { ref: b, edge: 'start', off: r4(s - T[b][0]) };
      if (x.end) x.end = inside(x.end) || { ref: b, edge: 'start', off: r4(s + it.e - it.s - T[b][0]) };
      // its anchors of its own in another option: to a copy stay with the copies; to anything else they become the start of the
      // target moment (it plays in every option), at the time the original has there (settled below, like the primary ones)
      for (const k of Object.keys(x.alt || {})) {
        const o = sk(it, k), Tk = tIn(RA0, k).t, sK = startOfK(it, Tk, k);
        for (const f of ['at', 'end']) {
          const v = x.alt[k][f]; if (!v) continue;   // undefined: not its own there; null: it has no end there: both stay as they are
          x.alt[k][f] = inside(v) || { ref: b, edge: 'start', off: r4((f === 'at' ? sK : sK + o.e - o.s) - Tk[b][0]) };
        }
      }
      x.help = x.help && map[x.help] ? map[x.help] : null;
      x.key = uniqueKey(taken, keyBase(score, it.el)); taken.add(x.key);
      if (it.el.label === it.el.key) x.label = x.key;
      delete x.neAPK; delete x.bind;   // a copy is not what Unreal has: it carries nothing of the original's action, target or asset
      Object.assign(x, { isNew: true, legacy: null, copyOf: it.id, by: opts.who || null, created: at });
      n.elements[id] = x; ids.push(id);
    }
    let RA = runsOf(n, Engine), R1 = RA[0], T1 = R1.t;
    const loops = rs => rs.reduce((a, r) => a + r.cycles.length, 0);   // in any option of a decision
    if (loops(RA) > loops(RA0)) return { ok: false, why: 'Pasted there it would make an anchor loop' };
    // settle (review of C10): a copy that makes its moment longer pushes the moments after it, and the copies placed there
    // with them (they landed +dt twice). Each copy is measured on what the others left, in time order, and only its own
    // offsets change (its anchor stays): it starts where startOf says and keeps its length. A pass per link at most.
    // The same in each option where a copy has an anchor of its own (alt): only that anchor's offsets change
    for (let pass = 0; pass < 8; pass++) {
      let any = false;
      for (const it of items) {
        const id = map[it.id], x = n.elements[id], s = startOf(it, T1), e = s + it.e - it.s;
        const ms = Math.abs(T1[id][0] - s) >= 5e-4, me = !!x.end && Math.abs(T1[id][1] - e) >= 5e-4;
        if (ms || me) {
          if (ms) x.at.off = r4(s - edgeT(T1, x.at));
          if (me) x.end.off = r4(e - edgeT(T1, x.end));
          RA = runsOf(n, Engine); R1 = RA[0]; T1 = R1.t; any = true;
        }
        for (const k of Object.keys(x.alt || {})) {
          const a = x.alt[k], Rk = tIn(RA, k), Tk = Rk.t; if (Rk.off && Rk.off[id]) continue;   // not there in that option
          const o = sk(it, k), sK = startOfK(it, Tk, k), eK = sK + o.e - o.s;
          const msK = !!a.at && Math.abs(Tk[id][0] - sK) >= 5e-4, meK = !!a.end && Math.abs(Tk[id][1] - eK) >= 5e-4;
          if (!msK && !meK) continue;
          if (msK) a.at.off = r4(sK - edgeT(Tk, a.at));
          if (meK) a.end.off = r4(eK - edgeT(Tk, a.end));
          RA = runsOf(n, Engine); R1 = RA[0]; T1 = R1.t; any = true;
        }
      }
      if (!any) break;
    }
    // an alternative anchor that ended up the same as the primary one (a copy placed from the start of its moment, like its
    // original in SHARE) says nothing: out, so the inspector does not list "Anchor in DON'T SHARE" for a copy that has none to speak of
    for (const id of ids) {
      const x = n.elements[id]; if (!x.alt) continue;
      for (const k of Object.keys(x.alt)) {
        for (const f of ['at', 'end']) if (x.alt[k][f] && x[f] && JSON.stringify(x.alt[k][f]) === JSON.stringify(x[f]) && !(tIn(RA, k).off || {})[x[f].ref]) delete x.alt[k][f];
        if (!Object.keys(x.alt[k]).length) delete x.alt[k];
      }
      if (!Object.keys(x.alt).length) delete x.alt;
    }
    // lanes: the one asked for (Alt+drag), else its own, else the first free one of its group, else a new lane
    const addLane = opts.addLane || addLaneTo, newLanes = [];
    for (const id of ids.slice().sort((a, b) => T1[a][0] - T1[b][0])) {
      const x = n.elements[id], g = n.groups.find(q => q.id === x.group), src = items.find(i => map[i.id] === id), want = opts.lanes && opts.lanes[src.id];
      let lane = null;
      if (want !== 'new') lane = [want, src.el.lane, ...g.lanes].filter((l, i, a) => l && g.lanes.includes(l) && a.indexOf(l) === i)
        .find(l => { x.lane = l; return !lanesOverlap(n, T1, [id]).length; }) || null;
      if (!lane) { lane = addLane(n, x.group); newLanes.push(lane); }
      x.lane = lane;
    }
    return { ok: true, next: n, ids, map, keys: ids.map(id => n.elements[id].key), newLanes, beats: [...new Set(ids.map(id => n.elements[id].beat))], total0: R0.total, total1: R1.total,
      sides: RA.slice(1).map(r => ({ k: r.k, total0: tIn(RA0, r.k).total, total1: r.total })) };   // the other options of a decision: where the paste leaves their totals
  }

  /* ---------- unsaved = the score differs from the last one saved or loaded (audit C14) ----------
     Deep, key-order independent; ignores what only a save writes (rev, savedBy, savedAt). Undoing back to it = clean. */
  const VOLATILE = new Set(['rev', 'savedBy', 'savedAt']);
  const has = (o, k) => Object.prototype.hasOwnProperty.call(o, k);
  function same(a, b) {
    if (a === b) return true;
    if (!a || !b || typeof a !== 'object' || typeof b !== 'object' || Array.isArray(a) !== Array.isArray(b)) return false;
    if (Array.isArray(a)) return a.length === b.length && a.every((x, i) => same(x, b[i]));
    const ka = Object.keys(a); if (ka.length !== Object.keys(b).length) return false;
    return ka.every(k => has(b, k) && same(a[k], b[k]));
  }
  function sameScore(a, b) {
    if (!a || !b) return a === b;
    const ka = Object.keys(a).filter(k => !VOLATILE.has(k)), kb = Object.keys(b).filter(k => !VOLATILE.has(k));
    return ka.length === kb.length && ka.every(k => has(b, k) && same(a[k], b[k]));
  }

  /* ---------- what an import replaces, not only the elements (review of lote 5 step 1) ----------
     cur = the score in the editor, file = the score being imported. importDiff only counts; it decides nothing.
     What the people of the piece wrote in the editor (bookmarks, notes, accepted problems, values waiting for Unreal) is
     theirs, not the file's: keepOwn carries over the records the file does not have (the file wins where both have one).
     The "≠ APK" baseline (golden; baseline in schema 3) is never carried over: it belongs with the times of the file it came with.
     The schema-3 structures (branches, uidMap, baseline) are not in KNOWN on purpose: a file that lacks them says so ("not in the file"). */
  const KNOWN = new Set(['schema', 'rev', 'savedBy', 'savedAt', 'source', 'acts', 'beats', 'groups', 'lanes', 'elements', 'markers', 'notes', 'accepted', 'propuestas', 'golden']);
  const objOf = o => (o && typeof o === 'object' && !Array.isArray(o) ? o : {});
  function keyedDiff(a, b) {
    a = objOf(a); b = objOf(b);
    const d = { added: [], changed: [], gone: [] };
    for (const k of Object.keys(b)) if (!has(a, k)) d.added.push(k); else if (!same(a[k], b[k])) d.changed.push(k);
    for (const k of Object.keys(a)) if (!has(b, k)) d.gone.push(k);
    return d;
  }
  // a record is its fingerprint AND the value it was accepted at (lote 5 step 9: one rule|element can hold a record for each value, as the
  // schema 2 ones the upgrade splits do): the key keeps both, so the import never takes one for the other
  const byFp = list => { const o = {}; for (const x of Array.isArray(list) ? list : []) if (x && x.fp != null) o[x.fp + (typeof x.value === 'string' ? '' + x.value : '')] = x; return o; };
  const waiting = s => objOf(objOf(s.propuestas).valores);
  /* the "≠ APK" reference of a score in one shape: schema 3 keeps it as `baseline` (relative times, a log), schema 2 as `golden`
     (absolute times, the voices applied). A `baseline` without `rel` is not a schema-3 baseline: it is a field the editor does not know */
  function refOf(s) {
    const b = objOf(s.baseline), g = objOf(s.golden);
    if (isObj(b.rel)) return { kind: 3, times: b.rel, total: b.total, voices: (Array.isArray(b.log) ? b.log : []).filter(x => x && x.op === 'voices').map(x => { const r = Object.assign({}, x); delete r.op; return r; }) };   // as a golden.voices record
    return { kind: 2, times: objOf(g.times), total: g.total, voices: Array.isArray(g.voices) ? g.voices : [] };
  }
  function importDiff(cur, file) {
    const gc = refOf(cur), gf = refOf(file), vf = gf.voices;
    const d = {
      elements: keyedDiff(cur.elements, file.elements), beats: keyedDiff(cur.beats, file.beats), lanes: keyedDiff(cur.lanes, file.lanes),
      acts: !same(cur.acts, file.acts), groups: !same(cur.groups, file.groups),
      markers: keyedDiff(cur.markers, file.markers), notes: keyedDiff(cur.notes, file.notes),
      accepted: keyedDiff(byFp(cur.accepted), byFp(file.accepted)), waiting: keyedDiff(waiting(cur), waiting(file)),
      // times of two forms (absolute and relative to the moment) are not comparable one by one: the form changes, not the times
      baseline: { times: gc.kind === gf.kind ? keyedDiff(gc.times, gf.times) : { added: [], changed: [], gone: [] }, total: !same(gc.total, gf.total), form: gc.kind !== gf.kind,
        voicesGone: gc.voices.filter(v => !vf.some(w => same(v, w))) },
      other: Object.keys(cur).filter(k => !KNOWN.has(k) && !has(file, k)),
    };
    // the Unreal binding (marks and bind, lote 5) is the score's, and an unbound file does not have it: say so, it is not an element difference
    d.unbound = bindState(cur) === 'bound' && bindState(file) !== 'bound';
    d.ownGone = d.markers.gone.length + d.notes.gone.length + d.accepted.gone.length + d.waiting.gone.length;
    return d;
  }
  function keepOwn(cur, file) {
    const n = clone(file), d = importDiff(cur, file);
    if (d.markers.gone.length) { n.markers = objOf(n.markers); for (const k of d.markers.gone) n.markers[k] = clone(cur.markers[k]); }
    if (d.notes.gone.length) { n.notes = objOf(n.notes); for (const k of d.notes.gone) n.notes[k] = clone(cur.notes[k]); }
    if (d.accepted.gone.length) { const A = byFp(cur.accepted); n.accepted = (Array.isArray(n.accepted) ? n.accepted : []).concat(d.accepted.gone.map(fp => clone(A[fp]))); }
    if (d.waiting.gone.length) {
      const P = cur.propuestas, Q = n.propuestas = objOf(n.propuestas);
      Q.valores = objOf(Q.valores); Q.motivos = objOf(Q.motivos);
      for (const k of d.waiting.gone) { Q.valores[k] = clone(P.valores[k]); if (has(objOf(P.motivos), k)) Q.motivos[k] = clone(P.motivos[k]); }
      if (P.base && !Q.base) Q.base = P.base;
    }
    return n;
  }
  /* the words of the import card */
  const nOf = (n, one, many) => `${n} ${n === 1 ? one : many || one + 's'}`;
  function changes(k, one, many) {
    const n = k.added.length + k.changed.length, g = k.gone.length, p = [];
    if (n) p.push(`${nOf(n, one, many)} differ${n === 1 ? 's' : ''}`);
    if (g) p.push(`${nOf(g, one, many)} would disappear`);
    return p.join(', ');
  }
  function importWords(d) {
    const own = [];
    if (d.markers.gone.length) own.push(nOf(d.markers.gone.length, 'bookmark'));
    if (d.notes.gone.length) own.push(nOf(d.notes.gone.length, 'note'));
    if (d.accepted.gone.length) own.push(nOf(d.accepted.gone.length, 'accepted problem'));
    if (d.waiting.gone.length) own.push(nOf(d.waiting.gone.length, 'value waiting for Unreal', 'values waiting for Unreal'));
    const also = [changes(d.beats, 'moment'), changes(d.lanes, 'lane'), d.acts ? 'the acts change' : '', d.groups ? 'the groups change' : '',
      d.markers.changed.length ? `${nOf(d.markers.changed.length, 'bookmark')} change${d.markers.changed.length === 1 ? 's' : ''} to the file's` : '',
      d.notes.changed.length ? `${nOf(d.notes.changed.length, 'note')} change${d.notes.changed.length === 1 ? 's' : ''} to the file's` : '',
      d.waiting.changed.length ? `${nOf(d.waiting.changed.length, 'value waiting for Unreal', 'values waiting for Unreal')} change${d.waiting.changed.length === 1 ? 's' : ''} to the file's` : ''].filter(Boolean);
    const B = d.baseline, nt = B.times.added.length + B.times.changed.length + B.times.gone.length;
    let base = '';
    if (nt || B.total || B.form || B.voicesGone.length) {
      base = `The "≠ APK" baseline becomes the file's${nt ? ` (${nOf(nt, 'reference time')} differ${nt === 1 ? 's' : ''})` : ''}`;
      if (B.voicesGone.length) {
        const ids = new Set(B.voicesGone.flatMap(v => v.ids || [])), at = B.voicesGone.map(v => String(v.at || '').slice(0, 10)).filter(Boolean).sort();
        base += `: the real voice lengths applied${at.length ? ' on ' + [...new Set(at)].join(', ') : ''} (${nOf(ids.size, 'voice')}) are not in it`;
      }
      base += '.';
    }
    const list = a => a.length < 2 ? a.join('') : a.slice(0, -1).join(', ') + ' and ' + a[a.length - 1];
    return { own: list(own), also: also.join('; '), base, unbound: d.unbound ? 'This score is bound to Unreal (marks and assets) and the file is not: the binding goes with it (Ctrl+Z brings it back; Experience ▸ Bind to Unreal… puts it again).' : '', other: d.other.length ? `Also not in the file: ${d.other.join(', ')}.` : '' };
  }

  /* rename (lote 5 design A §7.3): the name only, key and label. What Unreal plays stays: `sound` and `bind.asset` never
     change for an element Unreal has (a wired voice would lose its recording); a sound made in the editor (isNew: its WAV in
     the inbox is named by the element id) is named by its key until it is imported, as before. Mutates the element it gets
     (commit()'s copy) */
  function renameEl(x, name) { x.key = name; x.label = name; if (x.isNew) x.sound = name; return x; }

  /* ---------- the "≠ APK" reference moves with what the APK does (lote 5 design B §4.3) ----------
     The score is compared with what the APK is assumed to do. When an edit IS what the APK already does (Unreal plays the
     real voice lengths; later, "Match Unreal"), the reference moves by exactly what the edit shifted, so that element is not
     "different from the APK" for having been matched. Pure: they return the new reference and never touch the old one.
     Schema 3 keeps it inside the score as `baseline`: { kind, total, rel: { id: [start in its moment, length] }, log }.
     Schema 2 keeps it as `golden`: { total, times: { id: [start, end] }, voices } (absolute times; elements and moments).
     A and B are the score and its typical-user schedule before and after: { score, sched } (sched = Engine.resolve result).
     ids = the elements that move (null: every element that is in both and in the baseline); entry = one record for the log. */
  function shiftBaseline(baseline, A, B, ids, entry) {
    const only = ids ? new Set(ids) : null, tA = A.sched.t, tB = B.sched.t, rel = {};
    const startIn = (S, T, id) => { const e = S.elements[id], b = e && T[e.beat]; return T[id] && b ? [T[id][0] - b[0], T[id][1] - T[id][0]] : null; };
    for (const id of Object.keys(baseline.rel || {})) {
      const r = baseline.rel[id], a = !only || only.has(id) ? startIn(A.score, tA, id) : null, b = a ? startIn(B.score, tB, id) : null;
      rel[id] = a && b ? [r4(r[0] + b[0] - a[0]), r4(r[1] + b[1] - a[1])] : r.slice();   // not in both, not asked for: where the APK has it
    }
    return Object.assign({}, baseline, { rel, total: r4((baseline.total != null ? baseline.total : A.sched.total) + B.sched.total - A.sched.total),
      log: (Array.isArray(baseline.log) ? baseline.log : []).concat(entry ? [entry] : []) });
  }
  /* the same for a schema-2 score: T0, T1 = the typical-user schedules before and after; every time, moments too, moves by what changed
     (ids: only those, as shiftBaseline) */
  function shiftGolden(golden, T0, T1, entry, ids) {
    const times = {}, only = ids ? new Set(ids) : null;
    for (const k of Object.keys(golden.times || {})) { const g = golden.times[k]; times[k] = T0.t[k] && T1.t[k] && (!only || only.has(k)) ? [r4(g[0] + T1.t[k][0] - T0.t[k][0]), r4(g[1] + T1.t[k][1] - T0.t[k][1])] : g.slice(); }
    return Object.assign({}, golden, { times, total: r4((golden.total || T0.total) + T1.total - T0.total), voices: (Array.isArray(golden.voices) ? golden.voices : []).concat(entry ? [entry] : []) });
  }

  /* ---------- the upgrade to schema 3 (lote 5 design B §10) ----------
     One operation, the owner's button (never automatic, never on load): migrate3(score, Engine, contract, ctx) → { next, report }.
     It teaches the score three things Unreal already does and changes no time for the typical user:
       · the SHARE / DON'T SHARE decision: `branches.share`, `branch` on the 16 elements that carry a `when`, `alt` on whatever
         hangs from one side and has to hang from something on the other (today VO_37);
       · waits that run on the stage clock (`gate.blocking`, from the contract) and the names of their condition and knob;
       · a stable name for everything the prototype made: `uidMap` (prototype name → id, with the signature of the record guion.js
         gave), and the prototype schedule that was `golden` becomes the APK baseline (`baseline`, relative times, with its log).
     The accepted problems keep their value (`value`) and their fingerprint becomes rule|element (D11: a record answers a problem
     only at the value it was accepted at, Integrity.judge reads both shapes, so nothing is reopened by the change).
     What it knows by name is below, by PROTOTYPE uid (legacy.uid: it never changes when an element is renamed here). A `when` or a
     wait it does not know is a refusal that says which, never a guess. The postconditions run inside: if any fails, nothing is
     returned to apply. Pure: it never changes the score it gets. ctx = { at (ISO), who, gov (Partitura governed set), and the
     modules Integrity, Check, ImportDiff when they are not the ones loaded next to this file } */
  const MIGRATE3 = {
    // the decision that splits the piece (BP_Obra_SC FlowShare: the timeout ShareFW is DON'T SHARE, bSimulated is SHARE)
    branch: { on: 'share', gate: '9.5/G_SHARE', def: { name: 'Share or not', options: { yes: { label: 'SHARE', mark: 'SHARE.yes' }, no: { label: "DON'T SHARE", mark: 'SHARE.no' } },
      default: 'yes', onTimeout: 'no', note: 'BP_Obra_SC FlowShare' } },
    // `when` of the prototype → option: its named closures say it themselves, the four inline ones are listed by uid
    when: { yes: 'yes', no: 'no' },
    inline: { '9.6/FX_DOOROPEN': 'no', '9.7/FX_SOULJOIN': 'yes', '9.7/VO_35b': 'yes', '9.7/VO_35c': 'no' },
    // the ten waits: whether they block (what the contract says: a `not-blocking` entry is a stage's own clock, here for the test
    // that the two agree), the condition they wait for (vocabulary v0, anexo 11) and the Unreal knob that is their timeout
    waits: {
      '1.8/G_BELL': { blocking: true, cond: 'hall.bell.charged', knob: 'BP_HallDirector_SC.FW_Bell' },
      '2.2/G_SENSOR': { blocking: true, cond: 'hall.sensor.live', knob: 'BP_HallDirector_SC.FW_Tool' },
      '2.5/G_CHOOSE': { blocking: true, cond: 'hall.soul.live', knob: 'BP_HallDirector_SC.FW_Choose' },
      '9.5/G_SHARE': { blocking: true, cond: 'share.pick', knob: 'DA_Partitura_Obra.Res_Cortafuegos' },
      '4.R5/G_SAVE4': { blocking: true, cond: 'attract.saved' },
      '5.R5/G_SAVE5': { blocking: true, cond: 'draw.saved' },
      '1.R4/G_BREATH': { blocking: false, cond: 'breath.zone' },
      '2.R4/G_HEART': { blocking: false, cond: 'heart.zone' },
      '4.R4/G_GRAB': { blocking: false, cond: 'attract.first' },
      '5.R4/G_DRAW': { blocking: false, cond: 'draw.ink>0' },
    },
  };
  // the modules the upgrade asks (they load next to this file; in the browser they are globals)
  const dep = (file, name) => (typeof require === 'function' && typeof module !== 'undefined' ? require('./' + file) : root[name]);
  /* a stable text for a number-heavy comparison: the elements and moments whose start or end differ by more than 1 ms */
  const movedIds = (A, B) => Object.keys(A).filter(id => !B[id] || Math.abs(A[id][0] - B[id][0]) > 1e-3 || Math.abs(A[id][1] - B[id][1]) > 1e-3);
  function migrate3(score, Engine, contract, ctx) {
    ctx = ctx || {};
    const refusals = [], notes = [], report = { ok: false, refusals, notes };
    const refuse = (code, msg, ids) => { refusals.push({ code, msg, ids: ids || [] }); };
    const fail = () => ({ next: null, report });
    if (!score || score.schema !== 2) { refuse('M3.SCHEMA', score && score.schema === 3 ? 'This score is already schema 3.' : 'Only a schema 2 score can be upgraded.'); return fail(); }
    if (!contract || !Array.isArray(contract.entries)) { refuse('M3.CONTRACT', 'The contract with Unreal (obra/unreal/contract.json) is not loaded: it says which waits block, so the upgrade cannot go on without it.'); return fail(); }
    if (!score.golden || !isObj(score.golden.times)) { refuse('M3.GOLDEN', 'This score has no prototype schedule (golden) to become the APK baseline.'); return fail(); }
    let T0; try { T0 = validate(score, Engine); } catch (e) { refuse('M3.STRUCT', 'This score is not valid: ' + e.message); return fail(); }
    const Integrity = ctx.Integrity || dep('integrity.js', 'Integrity'), Check = ctx.Check || dep('check.js', 'Check'), ID = ctx.ImportDiff || dep('importdiff.js', 'ImportDiff');
    const at = ctx.at || new Date().toISOString(), E = score.elements, B = score.beats, key = id => (E[id] || B[id] || {}).key || id;
    const uidOf = id => (E[id].legacy && E[id].legacy.uid) || null;
    const byUid = {}, twice = new Set();
    for (const id of Object.keys(E)) { const u = uidOf(id); if (u) { if (byUid[u]) twice.add(u); byUid[u] = id; } }
    const bkeys = Object.values(B).map(b => b.key), btwice = bkeys.filter((k, i) => bkeys.indexOf(k) !== i);
    if (twice.size || btwice.length) refuse('M3.UID', `Two things share a prototype name (${[...twice, ...btwice].slice(0, 3).join(', ')}): the stable names would be ambiguous.`);

    // the two sides of the decision: the `when` of the prototype, by its name or, for an inline closure, by its uid
    const sides = {}, noSide = [];
    for (const id of Object.keys(E)) {
      const w = E[id].when; if (!w) continue;
      const u = uidOf(id), byName = has(MIGRATE3.when, w) ? MIGRATE3.when[w] : null, inline = u && has(MIGRATE3.inline, u) ? MIGRATE3.inline[u] : null;
      // a listed uid is an inline closure: the extractor named it 'when' (or 'condition'); any other text there is not what was listed
      const known = inline ? (w === 'when' || w === 'condition' || byName === inline) : !!byName;
      if (!known) noSide.push(id); else sides[id] = inline || byName;
    }
    if (noSide.length) refuse('M3.WHEN', `${noSide.length === 1 ? 'An element has' : noSide.length + ' elements have'} a condition (when) that the upgrade cannot place on SHARE or DON'T SHARE: ${noSide.slice(0, 6).map(id => `${key(id)} (${E[id].when})`).join(', ')}${noSide.length > 6 ? ', …' : ''}.`, noSide);
    // the waits: each one by its prototype uid; the contract decides whether it blocks
    const waits = {}, noWait = [];
    for (const id of Object.keys(E)) { if (!E[id].gate) continue; const u = uidOf(id); if (u && has(MIGRATE3.waits, u)) waits[id] = MIGRATE3.waits[u]; else noWait.push(id); }
    if (noWait.length) refuse('M3.WAIT', `${noWait.length === 1 ? 'A wait is' : noWait.length + ' waits are'} not one the upgrade knows (does it block, what does it wait for?): ${noWait.slice(0, 6).map(key).join(', ')}${noWait.length > 6 ? ', …' : ''}.`, noWait);
    if (refusals.length) return fail();

    const blockingOf = id => !Integrity.contractFor(id, E[id], contract).some(c => c.kind === 'not-blocking');
    const next = clone(score), r4 = x => Math.round(x * 10000) / 10000;
    next.schema = 3;
    // the decision: its two sides and the wait that decides it (the engine reads onTimeout from that wait's timeout)
    const bd = MIGRATE3.branch, shareGate = byUid[bd.gate] || null;
    next.branches = { [bd.on]: Object.assign({ name: bd.def.name }, shareGate ? { gate: shareGate } : {}, { options: clone(bd.def.options), default: bd.def.default, onTimeout: bd.def.onTimeout, note: bd.def.note }) };
    if (!shareGate) notes.push(`The wait that decides SHARE (${bd.gate}) is not in the score: the simulated users all see the default side.`);
    // `when` → `branch`; the old text stays in legacy.when
    for (const [id, v] of Object.entries(sides)) {
      const x = next.elements[id]; x.branch = { on: bd.on, value: v };
      x.legacy = Object.assign({}, x.legacy, { when: E[id].when });
      delete x.when;
    }
    // what is common and hangs from one side has to have an anchor in the other: the twin on the other side (same moment, same type,
    // same primary anchor) with the same edge and offset, else what that clip itself hangs from, at the time it has now
    const sideOf = id => next.elements[id] && next.elements[id].branch, opts = on => Object.keys(next.branches[on].options);
    const sameAnchor = (a, b) => !!a && !!b && a.ref === b.ref && edgeOf(a) === edgeOf(b) && Math.abs((a.off || 0) - (b.off || 0)) < 1e-6;
    const twinOf = (id, o) => {
      const x = next.elements[id], same = Object.keys(next.elements).filter(k => { const y = next.elements[k]; return k !== id && y.beat === x.beat && y.type === x.type && y.branch && y.branch.on === x.branch.on && y.branch.value === o && sameAnchor(y.at, x.at); });
      return same.length === 1 ? same[0] : null;
    };
    const alts = [];
    const needsAlt = (id, x, fields) => {
      for (const f of fields) {
        const a = x[f], s = a && a.ref && sideOf(a.ref);
        if (!s || (x.branch && x.branch.on === s.on)) continue;   // common anchor, or inside one decision (the check below says if it crosses)
        for (const o of opts(s.on)) {
          if (o === s.value) continue;
          const k = s.on + '=' + o; if (x.alt && x.alt[k] && x.alt[k][f]) continue;
          const tw = twinOf(a.ref, o), own = next.elements[a.ref].at || { ref: next.elements[a.ref].beat, edge: 'start', off: 0 };
          const alt = tw ? { ref: tw, edge: a.edge, off: a.off || 0 } : { ref: own.ref, edge: own.edge, off: r4(T0.t[id][f === 'at' ? 0 : 1] - edgeT(T0.t, own)) };
          x.alt = Object.assign(x.alt || {}, { [k]: Object.assign((x.alt || {})[k] || {}, { [f]: alt }) });
          alts.push({ id, key: key(id), field: f, option: k, twin: !!tw, to: tw ? key(tw) : 'what ' + key(a.ref) + ' hangs from' });
        }
      }
    };
    for (const id of Object.keys(next.beats)) needsAlt(id, next.beats[id], ['at']);
    for (const id of Object.keys(next.elements)) needsAlt(id, next.elements[id], ['at', 'end']);
    // waits: blocking (the contract), condition and knob
    const stageClock = [], blocks = [];
    for (const [id, w] of Object.entries(waits)) {
      const b = blockingOf(id); (b ? blocks : stageClock).push(key(id));
      if (b !== w.blocking) notes.push(`${key(id)}: the contract says it ${b ? 'blocks' : 'runs on the stage clock'}; the upgrade used that (it expected ${w.blocking ? 'blocking' : 'the stage clock'}).`);
      next.elements[id].gate = Object.assign({}, next.elements[id].gate, { blocking: b, cond: w.cond }, w.knob ? { knob: w.knob } : {});
    }
    // the prototype schedule becomes the APK baseline: relative times, as divergent() compares them
    const gt = score.golden.times, rel = {};
    for (const id of Object.keys(E)) { const t = gt[id], b = gt[E[id].beat]; if (t && b) rel[id] = [r4(t[0] - b[0]), r4(t[1] - t[0])]; }
    next.baseline = { kind: 'prototype-f0', total: score.golden.total, rel,
      log: [{ op: 'migrate', at, by: ctx.who || null }].concat((Array.isArray(score.golden.voices) ? score.golden.voices : []).map(v => Object.assign({ op: 'voices' }, v))) };
    delete next.golden;
    // stable names: prototype name → id, with the signature of what guion.js gave (the same record, whatever the schema)
    const uidMap = {};
    for (const id of Object.keys(B)) uidMap['@' + B[id].key] = { id, sig: ID.sigOf(ID.recordOfScore(score, id)) };
    for (const id of Object.keys(E)) { const u = uidOf(id); if (u) uidMap[u] = { id, sig: ID.sigOf(ID.recordOfScore(score, id)) }; }
    next.uidMap = uidMap;
    // accepted problems (design B §9): the fingerprint becomes rule|element (fpBase) and the rest of it the value they were accepted at,
    // so a record answers only at that value; a card's record (rule|element only) never kept one: null, "value unknown", open
    if (Array.isArray(score.accepted)) next.accepted = score.accepted.map(a => {
      const o = clone(a), f = Integrity.fpParts(a.fp);
      if (!has(o, 'value')) o.value = f.has ? f.param : null;
      o.fp = f.base;
      if (!o.state) o.state = 'accepted';
      return o;
    });

    // the postconditions: nothing moves for the typical user, nothing crosses between the sides, nothing dangles, ≠ APK is the same
    // set, and the saved file would pass the same invariants the server applies
    const T1 = typical(Engine, next), T1a = Engine.resolve(next, { persona: 'typical', branch: 'all' });
    const moved = [...new Set(movedIds(T0.t, T1.t).concat(movedIds(T0.t, T1a.t)))];
    if (moved.length || Math.abs(T0.total - T1.total) > 1e-3 || Math.abs(T0.total - T1a.total) > 1e-3) refuse('M3.MOVED', `${moved.length} item${moved.length === 1 ? '' : 's'} would move for the typical user (${moved.slice(0, 4).map(key).join(', ')}${moved.length > 4 ? ', …' : ''}) and the total would be ${T1.total.toFixed(1)} s, not ${T0.total.toFixed(1)} s: the upgrade must not change a time.`, moved);
    const cross = [];
    for (const o of opts(bd.on)) for (const id of Engine.resolve(next, { persona: 'typical', branch: { [bd.on]: o } }).crossBranch) cross.push(`${key(id)} in ${o === 'yes' ? 'SHARE' : "DON'T SHARE"}`);
    if (cross.length) refuse('M3.CROSS', `${[...new Set(cross)].slice(0, 4).join(', ')} hang${cross.length === 1 ? 's' : ''} from the other side of SHARE and the upgrade cannot give them an anchor there.`);
    const was = new Set(T0.dangling), dangle = T1.dangling.filter(id => !was.has(id));
    if (dangle.length) refuse('M3.DANGLING', `${dangle.length} anchor${dangle.length === 1 ? '' : 's'} would point to nothing (${dangle.slice(0, 4).map(key).join(', ')}).`, dangle);
    const D0 = Integrity.divergent(score, T0, contract, ctx.gov), D1 = Integrity.divergent(next, T1, contract, ctx.gov);
    if (D0.size !== D1.size || [...D0].some(id => !D1.has(id))) refuse('M3.DIVERGENT', `The ≠ APK set would change (${D0.size} → ${D1.size}): the baseline was not carried over faithfully.`);
    const chk = Check.invariants(next, score, { Engine, Edits: api, contract });
    for (const e of chk.errors) refuse('M3.CHECK', `${e.code}: ${e.msg}`, e.ids);
    if (refusals.length) return fail();

    // what the card says, measured here, now: the four simulated users before and after, the sides, the waits, the names
    const totals = {}, movedBy = {};
    for (const p of Object.keys(Engine.PERSONAS)) {
      const a = Engine.resolve(score, { persona: p }), v = Engine.resolve(next, { persona: p });
      totals[p] = { today: a.total, view: v.total, all: Engine.resolve(next, { persona: p, branch: 'all' }).total,
        share: Engine.resolve(next, { persona: p, branch: { [bd.on]: 'yes' } }).total, no: Engine.resolve(next, { persona: p, branch: { [bd.on]: 'no' } }).total };
      movedBy[p] = Object.keys(a.t).filter(id => !v.t[id] || Math.abs(a.t[id][0] - v.t[id][0]) > 1e-3).length;   // elements and moments that start elsewhere
    }
    const nSide = v => Object.values(sides).filter(x => x === v).length, withValue = (next.accepted || []).filter(a => a.value != null).length;
    Object.assign(report, { ok: true, totals, moved: movedBy,
      branch: { elements: Object.keys(sides).length, share: nSide('yes'), no: nSide('no'), alt: alts, gate: shareGate },
      waits: { blocking: blocks, stageClock },
      names: { elements: Object.values(uidMap).length - Object.keys(B).length, moments: Object.keys(B).length },
      baseline: { elements: Object.keys(rel).length, apk: { before: D0.size, after: D1.size } },
      accepted: { n: (next.accepted || []).length, withValue } });
    return { next, report };
  }

  /* ---------- "Bind to Unreal" (lote 5 design A §3.1, §3.4-§3.6) ----------
     The optional second step after the upgrade to schema 3, the owner's button too: bindUnreal(score, seed, idmap, contract, roles, ctx)
     → { next, report }. It adds exactly two things and nothing else, and no time changes (not for any simulated user, in any option
     of a decision):
       · beats[].marks, from the seed obra/score/seed/marks-v1.json (keyed by moment id): which Unreal mark each moment corresponds to;
       · elements[].bind { action, target, asset, branch }, from what the element is (its type, its key, the roles of roles.json, the
         assets of obra/unreal/idmap.json, the contract): who it is in Unreal. Written only where there is something to say; an element
         made in the editor (isNew) is left alone, Unreal does not know it. The asset is the IDMAP name (FX_BELLRING → Bell, so a later
         rename in the score never changes what Unreal plays); ambiguous or missing ones stay null and are counted, never guessed.
     The seed may still be "proposed, pending owner review": the report says so (report.seed.pending), the card too.
     What it will not do: run on a schema 2 score (upgrade first), run twice (bindState), or return a score whose only difference from
     the one it got is not marks and bind (it checks that itself, and the invariants the server applies). Pure: it never changes what it
     gets. ctx = { Engine, gov (the Partitura governed set, for the reach counts), and the modules Marks, Reach, Media, Integrity,
     Check when they are not the ones loaded next to this file } */
  const bindState = s => !s || s.schema !== 3 ? 'needs3'
    : Object.values(s.beats || {}).some(b => Array.isArray(b.marks) && b.marks.length) || Object.values(s.elements || {}).some(e => e.bind != null) ? 'bound' : 'open';
  /* the role of roles.json an element belongs to (by its group or its key), or null: the target of its bind. The first that matches wins */
  function roleOf(roles, e) {
    for (const [name, r] of Object.entries((roles && roles.roles) || {})) { const m = r.match || {}; if ((m.group && m.group === e.group) || (m.key && new RegExp(m.key).test(e.key))) return name; }
    return null;
  }
  const BIND_MARK_FIELDS = ['name', 'rel', 'el', 'elKey', 'edge', 'by', 'why', 'note'];
  function bindUnreal(score, seed, idmap, contract, roles, ctx) {
    ctx = ctx || {};
    const refusals = [], notes = [], report = { ok: false, refusals, notes };
    const refuse = (code, msg, ids) => { refusals.push({ code, msg, ids: ids || [] }); };
    const fail = () => ({ next: null, report });
    if (!score || score.schema !== 3) { refuse('B3.SCHEMA', score && score.schema === 2 ? 'Upgrade the score to schema 3 first: only a schema 3 score can carry marks and assets.' : 'Only a schema 3 score can be bound to Unreal.'); return fail(); }
    if (bindState(score) === 'bound') { refuse('B3.BOUND', 'This score is already bound to Unreal.'); return fail(); }
    if (!seed || !isObj(seed.beats)) refuse('B3.SEED', 'The marks (obra/score/seed/marks-v1.json) are not loaded: they say which Unreal mark each moment corresponds to.');
    if (!idmap || !isObj(idmap.assets)) refuse('B3.IDMAP', 'The Unreal assets are not scanned (obra/unreal/idmap.json, made by node tools/score/idmap.mjs): without them no sound can be linked.');
    if (!contract || !Array.isArray(contract.entries)) refuse('B3.CONTRACT', 'The contract with Unreal (obra/unreal/contract.json) is not loaded: it says which elements Unreal does not play.');
    if (!roles || !isObj(roles.roles)) refuse('B3.ROLES', 'The roles (obra/unreal/roles.json) are not loaded: they say which element is which object in Unreal.');
    if (refusals.length) return fail();
    const Engine = ctx.Engine || dep('engine.js', 'ScoreEngine'), Marks = ctx.Marks || dep('marks.js', 'Marks'), Reach = ctx.Reach || dep('reach.js', 'Reach'), Media = ctx.Media || dep('media.js', 'Media');
    const Integrity = ctx.Integrity || dep('integrity.js', 'Integrity'), Check = ctx.Check || dep('check.js', 'Check');
    let T0; try { T0 = validate(score, Engine); } catch (e) { refuse('B3.STRUCT', 'This score is not valid: ' + e.message); return fail(); }
    const E = score.elements, B = score.beats, next = clone(score), order = score.acts.flatMap(a => a.beats).filter(b => B[b]);

    // the marks: the seed's, copied as they are (only the fields a mark has); a moment the seed does not know stays without
    const unmarked = [], renamed = [];
    for (const b of Object.keys(B)) {
      const sb = seed.beats[b];
      if (!sb || !Array.isArray(sb.marks) || !sb.marks.length) { unmarked.push(b); continue; }
      next.beats[b].marks = sb.marks.map(m => { const o = {}; for (const f of BIND_MARK_FIELDS) if (m && m[f] != null) o[f] = clone(m[f]); return o; });
      if (sb.key && sb.key !== B[b].key) renamed.push(`${sb.key} is now ${B[b].key}`);
    }
    // a seed that marks no moment of this score (an empty one, or one made for another piece) would "bind" with nothing to anchor to, and the
    // score would then read as bound for good (the button greys out): it is not a bind, it is a refusal
    if (unmarked.length === Object.keys(B).length) { refuse('B3.SEED', 'The marks (obra/score/seed/marks-v1.json) mark none of the moments of this score: binding would leave every moment without an Unreal mark.'); return fail(); }
    const strays = Object.keys(seed.beats).filter(b => !B[b]);
    if (strays.length) notes.push(`The seed has ${strays.length} moment${strays.length === 1 ? '' : 's'} that ${strays.length === 1 ? 'is' : 'are'} not in the score (${strays.slice(0, 3).map(b => seed.beats[b].key || b).join(', ')}${strays.length > 3 ? ', …' : ''}): ignored.`);
    if (renamed.length) notes.push(`${renamed.length} moment${renamed.length === 1 ? '' : 's'} ${renamed.length === 1 ? 'was' : 'were'} renamed since the seed was made (${renamed.slice(0, 3).join(', ')}${renamed.length > 3 ? ', …' : ''}): the seed follows the ids.`);

    // the elements: who each one is in Unreal
    const ghostName = e => { const m = /^GHOST_([A-Z0-9]+)/.exec(String(e.key || '').replace(/#\d+$/, '')) || /^GHOST_([A-Z0-9]+)/.exec(e.ghost || ''); return m ? 'DA_Ghost_' + m[1][0] + m[1].slice(1).toLowerCase() : null; };
    const own = (o, k) => !!o && Object.prototype.hasOwnProperty.call(o, k);
    const sounds = { elements: 0, exact: 0, alias: 0, ambiguous: [], missing: 0, haptics: 0, ids: { exact: new Set(), alias: new Set(), ambiguous: new Set(), missing: new Set() } };
    const byAction = {}, left = []; let targets = 0, fresh = 0, noUnreal = 0, bound = 0;
    for (const id of Object.keys(E)) {
      const e = E[id];
      if (e.type === 'haptic') sounds.haptics++;
      if (e.isNew) { fresh++; continue; }   // made in the editor: Unreal does not have it, there is nothing to bind
      // the action: what the element is; the contract is the authority on what Unreal does not play at all
      let action = Reach.deriveAction(e);
      const k = String(e.key || '').replace(/#\d+$/, '');
      if (!action) action = /^GHOST_/.test(k) ? 'ghost' : /^ALMA_(IN|BACK)$/.test(k) ? 'appear' : /^ALMA_(OUT|GONE)$/.test(k) ? 'disappear' : null;
      if (action && Integrity.contractFor(id, e, contract).some(c => c.kind === 'not-in-unreal')) { action = null; noUnreal++; }
      // the asset: by the sound the element plays (its name in the score → the alias table → the scan of Content)
      let asset = null;
      const sid = Media.soundId(e);
      if (sid) {
        const al = own(idmap.aliases, sid) ? idmap.aliases[sid] : null, name = al || sid, a = own(idmap.ambiguous, name) ? 'ambiguous' : own(idmap.assets, name) ? (al ? 'alias' : 'exact') : 'missing';
        sounds.elements++; sounds.ids[a].add(sid);
        if (a === 'ambiguous') sounds.ambiguous.push({ id, key: e.key, asset: name });
        else if (a === 'missing') sounds.missing++;
        else { sounds[a]++; asset = name; }
      } else if (action === 'ghost') { const g = ghostName(e); if (g && own(idmap.assets, g)) asset = g; }
      // the target: the role it belongs to in roles.json; Alma speaks the voices she says
      const role = roleOf(roles, e), target = action === 'vo_alma' ? 'role:Alma' : role ? 'role:' + role : null;
      if (!action && !asset && !target) continue;
      next.elements[id].bind = { action, target, asset, branch: null };
      bound++; if (target) targets++; if (action) byAction[action] = (byAction[action] || 0) + 1; else left.push(id);
    }

    // the postconditions: only marks and bind were added, the file is valid, nothing moves for any simulated user, the server's invariants hold
    const bare = clone(next); for (const b of Object.values(bare.beats)) delete b.marks; for (const e of Object.values(bare.elements)) delete e.bind;
    if (!same(bare, score)) refuse('B3.TOUCHED', 'Binding would change something other than marks and bind: it stopped.');
    let T1; try { T1 = validate(next, Engine); } catch (e) { refuse('B3.STRUCT', 'The bound score is not valid: ' + e.message); return fail(); }
    const totals = {}, moved = {};
    for (const p of Object.keys(Engine.PERSONAS)) for (const branch of [undefined, 'all']) {
      const a = Engine.resolve(score, { persona: p, branch }), v = Engine.resolve(next, { persona: p, branch });
      const gone = Object.keys(a.t).filter(i => !v.t[i] || Math.abs(a.t[i][0] - v.t[i][0]) > 1e-9 || Math.abs(a.t[i][1] - v.t[i][1]) > 1e-9).concat(Object.keys(v.t).filter(i => !a.t[i]));
      if (gone.length || Math.abs(a.total - v.total) > 1e-9) refuse('B3.MOVED', `${gone.length} item${gone.length === 1 ? '' : 's'} would move for the ${p} user (${gone.slice(0, 3).map(i => (E[i] || B[i]).key).join(', ')}): binding must not change a time.`, gone);
      if (!branch) { totals[p] = a.total; moved[p] = gone.length; }
    }
    const chk = Check.invariants(next, score, { Engine, Edits: api, contract });
    for (const e of chk.errors) refuse('B3.CHECK', `${e.code}: ${e.msg}`, e.ids);
    if (refusals.length) return fail();

    // what the card says, measured now: the moments by relation, the sounds by what became of them, what a cue could fire
    const rels = { start: 0, el: 0, in: 0, sub: 0, preview: 0 }; let extra = 0, placed = 0;
    for (const b of order) {
      const ms = next.beats[b].marks; if (!ms) continue;
      if (rels[ms[0].rel] != null) rels[ms[0].rel]++;
      extra += ms.filter((m, i) => i > 0 && m.rel === 'el').length;
      placed += ms.filter(m => m.rel === 'start' || m.rel === 'el').length;
    }
    const reachOf = (sc, T) => Reach.all(Reach.context({ score: sc, schedT: T, contract, gov: ctx.gov || {}, idmap, seed, roles, resolve: p => Engine.resolve(sc, { persona: p }) }));
    const R0 = reachOf(score, T0), R1 = reachOf(next, T1);
    const cues = Object.keys(R1.of).filter(id => R1.of[id].reach === 'cue').sort((x, y) => T1.t[x][0] - T1.t[y][0] || (x < y ? -1 : 1))
      .map(id => Object.assign({ id, key: E[id].key }, R1.of[id].cue, { state: R1.of[id].state }));
    const sd = s => new Set([...s.exact, ...s.alias]);
    Object.assign(report, { ok: true, totals, moved,
      seed: { version: seed.version || null, status: seed.status || null, pending: /pending|proposed/i.test(String(seed.status || '')), generated: seed.generated || null, review: Array.isArray(seed.review) ? seed.review.length : 0 },
      beats: { total: order.length, marked: order.length - unmarked.length, unmarked: unmarked.map(b => B[b].key), start: rels.start, el: rels.el, onMark: rels.start + rels.el, in: rels.in, sub: rels.sub, inside: rels.in + rels.sub, preview: rels.preview, extra, placed },
      sounds: { elements: sounds.elements, linked: sounds.exact + sounds.alias, exact: sounds.exact, alias: sounds.alias, ambiguous: sounds.ambiguous, missing: sounds.missing, haptics: sounds.haptics,
        ids: { total: new Set([...sounds.ids.exact, ...sounds.ids.alias, ...sounds.ids.ambiguous, ...sounds.ids.missing]).size, exact: sounds.ids.exact.size, alias: sounds.ids.alias.size, ambiguous: [...sounds.ids.ambiguous].sort(), missing: sounds.ids.missing.size, linked: sd(sounds.ids).size } },
      elements: { total: Object.keys(E).length, bound, byAction, targets, noUnreal, fresh, noAction: left.length },
      reach: { before: R0.counts, after: R1.counts, cues },
      idmap: { generated: idmap.generated || null } });
    if (!placed) notes.push("None of the marks places a phase of Unreal's director (start or el): nothing in the score is anchored to Unreal's clock yet.");
    if (fresh) notes.push(`${fresh} element${fresh === 1 ? '' : 's'} made in the editor ${fresh === 1 ? 'was' : 'were'} left unbound: Unreal does not have ${fresh === 1 ? 'it' : 'them'}.`);
    return { next, report };
  }

  const api = { planDelete, reconcileUidMap, runsOf, runOf, altKeyOf, move, moveMany, fixOverlaps, lanesOverlap, validate, validateBranches, validateBind, bindError, branchError, branchGates, wouldBreak, marksOf, marksLost, settleMarks, marksWords, planLoop, homeAnchor, anchorOf, hangingFrom, reanchor, reanchorAlt, branchAnchors, setBranch, optionLabel, lostAnchors, detachLost,
    uniqueKey, newId, clipOf, planPaste, sameScore, importDiff, keepOwn, importWords, renameEl, shiftBaseline, shiftGolden, matchKnobAnchor, migrate3, MIGRATE3, bindUnreal, bindState, roleOf, BIND_ACTIONS, MARK_RELS };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.Edits = api;
})(typeof window !== 'undefined' ? window : globalThis);
