/* Veation VR Studio · FIXES: when an edit (or the score as it stands) has a problem, a way out to PROPOSE, pure (no DOM) so it runs in
   the browser and in Node (tools/score/fixes_test.mjs). The owner decides: nothing here writes anything, the app applies a fix only when
   he accepts it, as ONE edit (one undo step) on top of his own.
   propose(item, ctx) → [fix]. `item` is what integrity says is wrong: an item of the impact card (Integrity.opItems) or a row of Problems
   (rule, fp, el, ids, verbs, knob). ctx = { score: the score the problem is in (the edit already applied), before: the score before the
   edit (null for a row of Problems), sched: its typical schedule, contract, gov, pdef / plive / pbind (the Partitura), knob(name),
   Engine, Edits, Integrity, op: the edit, who, now }.
   fix = { id, label, detail, apply(n), keepsEdit, op, rule, el }: `label` is short and plain; `detail` says what moves and by how much (the
   effect of Integrity.effect and its ripple line, measured on the score the edit leaves); `apply(n)` mutates a clone of that score, ON TOP
   of the edit (false: it cannot); `op` is the edit it is applied as when it stands alone (the verb commit() judges it by); `keepsEdit` is true when the edit stays and something else adjusts, false when the fix replaces it.
   Every fix is checked before it is offered: applied on a copy, it must solve the problem and create no new warning or block, no
   anchor loop, no anchor to nothing, no start before 0:00 and no new difference from a Partitura knob; and it must not open a card of
   its own. A fix that gives back the score before the edit is Cancel, so it is not offered. Only fixes that make things better are.
   analyze(item, ctx) → { fixes, why } also says why there is none when it knows (a voice that has no room that keeps Unreal's order). */
(function (root) {
  'use strict';
  const dep = (file, name) => (typeof require === 'function' && typeof module !== 'undefined' ? require('./' + file) : root[name]);
  const clone = o => JSON.parse(JSON.stringify(o));
  const r4 = x => Math.round(x * 10000) / 10000;
  const s1 = x => String(+(+x).toFixed(2));
  const GAP = .3, HELP_LEAD = 2, FLASH_MIN = .3, MAX_FIXES = 3, MAX_LIST = 4;
  const nodeOf = (s, id) => s.elements[id] || s.beats[id];
  const keyOf = (s, id) => (nodeOf(s, id) || {}).key || id;
  const isBranchKey = x => /^[^=|]+=[^=|]+$/.test(x || '');   // "share=no": the option a problem was found in (the last part of a fingerprint)
  const replaceAll = (n, next) => { for (const k of Object.keys(n)) delete n[k]; Object.assign(n, clone(next)); };

  /* the rules this module has a fix for (the C3 ones that come from a contract entry are recognised by the entry, see candidates) */
  const RULES = new Set(['C2.VO.OVERLAP', 'C2.HELP.LATE', 'C2.WAIT.NOHELP', 'C3.DRIFT', 'C3.PARTITURA', 'C3.KNOB.OFFSET', 'C3.BLOCKING', 'C2.WAIT.WHERE',
    'C1.ANCHOR.CYCLE', 'C1.BRANCH.ANCHOR', 'C1.ANCHOR.MISSING', 'C2.FLASH', 'C2.ALMA.EARLY']);
  const open = p => !p.ghost && p.st !== 'accepted' && (p.sv === 'warn' || p.sv === 'block');
  const IGNORE = new Set(['C2.TOTAL.GOAL']);   // the band reopens it when the total grows: it is no problem of the fix
  /* is it something this module can look at? (cheap: no schedule is worked out) */
  const handles = item => !!item && item.sv !== 'info' && item.st !== 'accepted' && !item.ghost && (RULES.has(item.rule) || !!item.c3);

  /* ---------- what a fix needs, worked out once per ctx ---------- */
  function kit(ctx) {
    if (ctx._fx) return ctx._fx;
    const Engine = ctx.Engine || dep('engine.js', 'ScoreEngine'), Edits = ctx.Edits || dep('edits.js', 'Edits'), Int = ctx.Integrity || dep('integrity.js', 'Integrity');
    const typical = s => Engine.resolve(s, { persona: 'typical' });
    return (ctx._fx = { ctx, Engine, Edits, Int, Part: ctx.Partitura || dep('partitura.js', 'Partitura'), typical, score: ctx.score, before: ctx.before || null, op: ctx.op || null,
      contract: ctx.contract || null, T: ctx.sched || typical(ctx.score), who: ctx.who || 'B', now: ctx.now || new Date().toISOString() });
  }
  /* the typical user in one option of a decision ("share=no"), the default run when k is null */
  const sched = (K, s, k) => (k ? K.Edits.runOf(s, K.Engine, k) : K.typical(s));
  const kctx = K => ({ knob: typeof K.ctx.knob === 'function' ? K.ctx.knob : undefined });
  const touched = (K, id) => !!K.op && (K.op.ids || []).includes(id);
  const aloneOf = (K, id) => !!K.op && !!K.op.alone && touched(K, id);   // the owner moved it Ctrl+drag: what hangs from it stayed
  const users = (K, s) => Object.keys(K.Engine.PERSONAS).reduce((o, p) => (o[p] = K.Engine.resolve(s, { persona: p }).total, o), {});

  /* ---------- a time that is a knob of Unreal's Partitura ----------
     A row of Partitura.drift is "waiting" when a change for that knob (and stage) is staged in score.propuestas and it is what the score does:
     the difference is decided, it only needs Send to Unreal. Problems reads it the same way (app.js computePartitura) */
  function waiting(score, row) {
    const v = score && score.propuestas && score.propuestas.valores && score.propuestas.valores[row.knob]; if (v == null) return false;
    const w = Array.isArray(v) ? (row.stage == null ? v[0] : v[row.stage]) : v;
    return row.score != null && typeof w === 'number' && Math.abs(w - row.score) < .05;
  }
  const rowOpen = (score, r) => r.diff != null && Math.abs(r.diff) > .05 && !waiting(score, r);
  function knobRows(K, s, T) {
    const c = K.ctx; if (!K.Part || !c.pdef || !c.pbind) return [];
    return K.Part.drift(s, T, c.pdef, c.plive, c.pbind).rows;
  }
  const openKnobs = (K, s, T) => new Set(knobRows(K, s, T).filter(r => rowOpen(s, r)).map(r => r.knob + '|' + (r.stage == null ? '' : r.stage)));

  /* ---------- moving a start ---------- */
  const ownAnchor = (x, k) => (k && x.alt && x.alt[k] && x.alt[k].at ? x.alt[k].at : x.at);
  function setAnchor(x, k, a) { if (k && x.alt && x.alt[k] && x.alt[k].at) x.alt[k].at = a; else x.at = a; }
  /* start element `id` of `n` at time t (the typical user, in option k). It keeps the kind of anchor it has and moves its offset, unless
     `prefer` ({ ref, edge }) is a clean way to say it: the other element is in the same moment and nothing hangs the other way round (no loop).
     o.alone: what hangs from it stays where it is (the way the owner moved it, Ctrl+drag). Mutates n; false when it cannot */
  function retime(K, n, id, t, o) {
    o = o || {};
    const x = n.elements[id]; if (!x) return false;
    const S = sched(K, n, o.k), pf = o.prefer;
    if (!S.t[id]) return false;
    if (o.alone) { replaceAll(n, K.Edits.move(n, id, r4(t - S.t[id][0]), { alone: true, ks: o.k ? [o.k] : [] }, K.Engine.dependents(n))); return true; }
    if (pf && pf.ref && pf.ref !== id && n.elements[pf.ref] && S.t[pf.ref] && n.elements[pf.ref].beat === x.beat
        && !K.Edits.hangingFrom(n, id, K.Engine, 'start').has(pf.ref + (pf.edge === 'start' ? '|S' : '|E'))) {
      setAnchor(x, o.k, { ref: pf.ref, edge: pf.edge, off: r4(t - S.t[pf.ref][pf.edge === 'start' ? 0 : 1]) });
      return true;
    }
    const cur = ownAnchor(x, o.k) || { ref: x.beat, edge: 'start', off: 0 }, next = Object.assign({}, cur, { off: r4((cur.off || 0) + (t - S.t[id][0])) });
    delete next.knob;   // it is no longer the Unreal knob's value
    setAnchor(x, o.k, next);
    return true;
  }
  /* the voices of a moment in the order they play (help lines do not count: they follow their wait) */
  function voiceOrder(s, T, beat) {
    return Object.keys(s.elements).filter(id => s.elements[id].beat === beat && s.elements[id].type === 'vo' && !s.elements[id].help && T[id]).sort((a, b) => T[a][0] - T[b][0]);
  }

  /* ---------- a help line for a wait (what Problems ▸ Add a help line has always made) ---------- */
  const helpId = (score, now) => { let id = 'el_n' + (now || Date.now()).toString(36); while (score.elements[id] || score.beats[id] || score.lanes[id]) id += 'x'; return id; };
  const voLength = text => { text = String(text || ''); return 1 + text.split(/\s+/).filter(Boolean).length / 2.4 + (text.match(/…/g) || []).length * .5; };   // as the prototype (app.js voDur)
  /* mutates n; returns the id of the new line, or null. The line plays between the user's usual time and the timeout, and goes to a free lane */
  function addHelpLine(Edits, Engine, n, waitId, o) {
    o = o || {};
    const w = n.elements[waitId]; if (!w || !w.gate) return null;
    const T = Engine.resolve(n, { persona: 'typical' }).t, off = +Math.max(1, Math.min(w.gate.fw - 4, w.gate.expected + 4)).toFixed(2), s0 = T[waitId][0] + off;
    const id = o.id || helpId(n, o.now);
    const busy = lane => Object.keys(n.elements).some(k => { const e = n.elements[k]; if (e.lane !== lane || !T[k]) return false; const b = Math.max(T[k][1], T[k][0] + .05); return T[k][0] < s0 + 3 - 1e-4 && b > s0 + 1e-4; });
    const g = n.groups.find(x => x.id === 'vo'), lane = g.lanes.find(l => !busy(l)) || Edits.addLaneTo(n, 'vo');
    n.elements[id] = { key: Edits.uniqueKey(new Set(Object.values(n.elements).map(e => e.key)), w.key.replace(/^G_/, 'VO_') + '_HELP'), type: 'vo', group: 'vo', beat: w.beat, lane, at: { ref: waitId, edge: 'start', off }, end: null,
      dur: { mode: 'audio', value: +voLength('Help line for this wait…').toFixed(4) }, label: 'Help line', text: 'Help line for this wait…', help: waitId, isNew: true, by: o.who || 'B', created: o.at || new Date().toISOString(),
      sound: null, note: null, gate: null, simOnly: false, when: null, hint: null, ghost: null, legacy: null };
    return id;
  }

  /* ---------- the candidates of each rule ----------
     { id, label, apply(n), keepsEdit, main: [ids it is about], solved?(n, T), words?(K, n, T1), tail?, users?, op?, quiet?, knobs? }
     `solved` says the problem is gone when the item has no fingerprint of its own to look for; `quiet`: it is judged like Match Unreal (never a card) */
  function overlapCands(item, K) {
    const S = K.score, E = S.elements, id = item.el, j = E[id]; if (!j) return [];
    const f = String(item.fp || '').split('|'), k = f.slice(2).find(isBranchKey) || null, Tt = sched(K, S, k).t;
    const i = Object.keys(E).find(o => o !== id && E[o].type === 'vo' && !E[o].help && E[o].key === f[2] && Tt[o]); if (!i || !Tt[id]) return [];
    const I = E[i], same = I.beat === j.beat, out = [];
    // the later voice waits for the earlier one (keeping its kind of anchor, or hanging from the end of the earlier one when both are in the same moment)
    out.push({ id: 'vo.after', label: `Start ${j.key} after ${I.key} ends`, keepsEdit: !touched(K, id), main: [id],
      apply: n => retime(K, n, id, sched(K, n, k).t[i][1] + GAP, { k, alone: aloneOf(K, id), prefer: same ? { ref: i, edge: 'end' } : null }),
      words: () => `${j.key} starts ${GAP} s after ${I.key} ends.` });
    // the voice that moved goes back to where it belongs: right after the voice that came before it
    const m = touched(K, id) ? id : touched(K, i) ? i : null;
    if (m && K.before && K.before.elements[m]) {
      const ord = voiceOrder(K.before, K.typical(K.before).t, K.before.elements[m].beat), p = ord[ord.indexOf(m) - 1];
      if (p && E[p]) out.push({ id: 'vo.back', label: `Put ${E[m].key} back right after ${E[p].key}`, keepsEdit: false, main: [m],
        apply: n => retime(K, n, m, sched(K, n, k).t[p][1] + GAP, { k, alone: aloneOf(K, m), prefer: E[p].beat === E[m].beat ? { ref: p, edge: 'end' } : null }) });
    }
    // the earlier voice is the one that moved (or nobody did): it ends before the later one starts
    if (touched(K, i) || !K.op) out.push({ id: 'vo.before', label: `End ${I.key} before ${j.key} starts`, keepsEdit: !touched(K, i), main: [i],
      apply: n => { const T = sched(K, n, k).t; return retime(K, n, i, T[id][0] - GAP - (T[i][1] - T[i][0]), { k, alone: aloneOf(K, i) }); } });
    return out;
  }
  function helpLateCands(item, K) {
    const S = K.score, id = item.el, h = S.elements[id], w = h && h.help && S.elements[h.help]; if (!w || !w.gate) return [];
    const k = String(item.fp || '').split('|').slice(2).find(isBranchKey) || null;
    return [{ id: 'help.late', label: `Move ${h.key} to ${HELP_LEAD} s before the timeout of ${w.key}`, keepsEdit: !touched(K, id), main: [id],
      apply: n => { const x = n.elements[id], g = x && x.help && n.elements[x.help]; if (!g || !g.gate) return false; return retime(K, n, id, sched(K, n, k).t[x.help][0] + Math.max(.5, g.gate.fw - HELP_LEAD), { k, alone: aloneOf(K, id), prefer: { ref: x.help, edge: 'start' } }); },
      words: (_, n) => `${h.key} plays ${s1(Math.max(.5, w.gate.fw - HELP_LEAD))} s into the wait, before its ${s1(w.gate.fw)} s timeout.` }];
  }
  function noHelpCands(item, K) {
    const id = item.el, w = K.score.elements[id]; if (!w || !w.gate) return [];
    return [{ id: 'help.add', label: `Add a help line to ${w.key}`, keepsEdit: true, main: [],
      apply: n => addHelpLine(K.Edits, K.Engine, n, id, { who: K.who, now: Date.parse(K.now) || undefined, at: K.now }) ? undefined : false,
      solved: n => Object.values(n.elements).some(e => e.help === id),
      words: (_, n) => { const q = Object.keys(n.elements).find(x => !K.score.elements[x]), e = q && n.elements[q]; return e ? `A new line (${e.key}) plays ${s1(e.at.off)} s after ${w.key} starts, before its ${s1(w.gate.fw)} s timeout. Its words are a placeholder: write them in the inspector.` : ''; },
      tail: 'No other time changes.' }];
  }
  function flashCands(item, K) {
    const id = item.el, e = K.score.elements[id]; if (!e || !e.dur) return [];
    return [{ id: 'flash.min', label: `Make ${e.key} ${FLASH_MIN} s long`, keepsEdit: !touched(K, id), main: [id], op: { type: 'trim', ids: [id] },
      apply: n => { const x = n.elements[id]; if (!x) return false; x.dur = Object.assign({}, x.dur, { mode: 'fixed', value: FLASH_MIN }); },
      words: () => `${e.key} is on for ${s1(e.dur.value)} s; ${FLASH_MIN} s is the least that reads in the headset.` }];
  }
  function almaCands(item, K) {
    const S = K.score, E = S.elements, id = item.el, v = E[id]; if (!v) return [];
    const k = String(item.fp || '').split('|').slice(2).find(isBranchKey) || null, R = sched(K, S, k);
    const a = Object.keys(E).find(x => E[x].beat === v.beat && /^ALMA_(IN|BACK)$/.test(E[x].key) && !(R.off && R.off[x])); if (!a) return [];
    return [{ id: 'alma.after', label: `Start ${v.key} when ${E[a].key} ends`, keepsEdit: !touched(K, id), main: [id],
      apply: n => retime(K, n, id, sched(K, n, k).t[a][1], { k, alone: aloneOf(K, id), prefer: { ref: a, edge: 'end' } }),
      words: () => `${v.key} starts when Alma has appeared (${E[a].key} ends).` }];
  }
  /* a timeout that is not Unreal's: take Unreal's */
  function driftCands(id, value, K) {
    const e = K.score.elements[id]; if (!e || !e.gate || !Number.isFinite(value) || e.gate.fw === value) return [];
    return [{ id: 'drift.unreal', label: `Use Unreal's ${s1(value)} s timeout`, keepsEdit: !touched(K, id), main: [id], users: true, op: { type: 'gate', ids: [id] },
      apply: n => { const x = n.elements[id]; if (!x || !x.gate) return false; x.gate.fw = +value; },
      solved: n => n.elements[id].gate.fw === +value,
      words: () => `${e.key}'s timeout goes from ${s1(e.gate.fw)} s to ${s1(value)} s, as in Unreal.` }];
  }
  const knobEntry = (id, K) => K.Int.contractFor(id, K.score.elements[id], K.contract).find(x => x.kind === 'knob' && x.knob);
  /* a wait whose flag disagrees with Unreal, or sits where only the stage clock runs: set it as Unreal has it */
  function blockingCands(item, K) {
    const id = item.el, e = K.score.elements[id]; if (!e || !e.gate || !(K.score.schema >= 3)) return [];
    const k = K.Int.blockingClash(id, e, K.contract), want = k ? k.unreal !== 'clock' : item.rule === 'C2.WAIT.WHERE' ? false : null; if (want === null) return [];
    return [{ id: 'blocking.set', label: want ? `Make ${e.key} wait for the user, as Unreal does` : `Let ${e.key} run on the stage clock, as Unreal does`, keepsEdit: false, main: [], users: true, op: { type: 'gate', what: 'blocking', ids: [id] },
      apply: n => { const x = n.elements[id]; if (!x || !x.gate) return false; x.gate.blocking = want; },
      words: () => `${e.key} ${want ? 'waits for the user' : 'runs on the stage clock'}.` }];
  }
  /* a time that IS a knob of Unreal counted from another element (VO_11h): Match Unreal */
  function knobOffsetCands(id, K) {
    const e = K.score.elements[id], c = e && K.Int.contractFor(id, e, K.contract).find(x => x.kind === 'knob' && x.anchor && x.knob);
    const k = c && K.Int.knobOffset(K.score, K.T, id, c, K.contract, kctx(K)); if (!k || k.ok) return [];
    const spec = { ref: k.refId, edge: k.edge, off: k.value, knob: k.name, at: K.now, by: K.who };
    return [{ id: 'knob.match', label: `Play ${e.key} ${s1(k.value)} s after ${keyOf(K.score, k.refId)} ${k.edge === 'start' ? 'starts' : 'ends'}, as Unreal does`, keepsEdit: false, main: [id], op: { type: 'sync', ids: [] }, quiet: true,
      apply: n => {
        const r = K.Edits.matchKnobAnchor(n, id, spec, K.Engine); if (!r.ok) return false; replaceAll(n, r.next);
        // the reference of "≠ headset" follows Match Unreal from where the clip was BEFORE the owner's edit (the edit is his, the match is Unreal's)
        const b = K.before && K.before.elements[id] && K.Edits.matchKnobAnchor(K.before, id, spec, K.Engine);
        if (b && b.ok) { if (b.next.baseline) n.baseline = clone(b.next.baseline); if (b.next.golden) n.golden = clone(b.next.golden); }
      },
      solved: (n, T) => { const k2 = K.Int.knobOffset(n, T, id, c, K.contract, kctx(K)); return !k2 || k2.ok; },
      words: () => `${e.key} counts ${s1(k.value)} s from the ${k.edge === 'start' ? 'start' : 'end'} of ${keyOf(K.score, k.refId)} (${k.name.replace(/^[^.]*\./, '')} in Unreal).` }];
  }
  /* a knob of the Partitura that the score no longer agrees with: keep the score and tell Unreal (it waits to be sent), or put the score back.
     ctx.knobs (optional): the other knobs the same edit left different, so one decision covers them all (the toast of the edit) */
  function partituraCands(item, K) {
    const c = K.ctx; if (!item.knob || !c.pdef || !c.pbind || !K.Part) return [];
    const names = [...new Set([item.knob].concat(c.knobs || []))], ST = c.pdef.stages || [];
    const LV = K.Part.liveValues(c.plive), defOf = nm => c.pdef.knobs.find(x => x.name === nm), liveOf = d => (LV && d.name in LV ? LV[d.name] : d.initial);
    const openRows = s => knobRows(K, s, s === K.score ? K.T : K.typical(s)).filter(r => names.includes(r.knob) && defOf(r.knob) && rowOpen(s, r));
    const group = rows => { const g = {}; for (const r of rows) (g[r.knob] = g[r.knob] || []).push(r); return g; };
    const rows = openRows(K.score); if (!rows.length) return [];
    const keys = rows.map(r => r.knob + '|' + (r.stage == null ? '' : r.stage)), G = group(rows), knobs = Object.keys(G);
    const fmt = v => Array.isArray(v) ? v.map(x => s1(x)).join(' · ') : s1(v);
    const stageWords = (d, r) => (r.stage == null || d.type !== 'a5' ? '' : ' in ' + (ST[r.stage] || 'stage ' + (r.stage + 1)));
    const one = knobs.length === 1, lone = G[knobs[0]];
    const stage = n => {   // what Act.propose does for each knob: the value of the score waits in score.propuestas (nothing is sent)
      const R = group(openRows(n)), ks = Object.keys(R); if (!ks.length) return false;
      const P = n.propuestas = n.propuestas || { valores: {}, motivos: {} };
      if (!P.base && c.plive) P.base = c.plive.hash;
      for (const knob of ks) {
        const d = defOf(knob), live = liveOf(d), rs = R[knob], v = r => +(+r.score).toFixed(3);
        let nv;
        if (d.type === 'a5') { nv = (P.valores[knob] || live).slice(); for (const r of rs) { if (r.stage == null) nv = nv.map(() => v(r)); else nv[r.stage] = v(r); } }
        else nv = v(rs[0]);
        if (JSON.stringify(nv) === JSON.stringify(live)) { delete P.valores[knob]; delete P.motivos[knob]; continue; }
        P.valores[knob] = nv;
        P.motivos[knob] = { por: K.who, motivo: `The score now does ${fmt(rs.map(r => r.score))} s (Unreal has ${fmt(live)} s): moved in the editor.`, antes: live, cuando: K.now };
      }
    };
    const list = knobs.slice(0, 3).map(k => `${k} ${fmt(G[k].map(r => r.da))} → ${fmt(G[k].map(r => r.score))} s`).join(' · ') + (knobs.length > 3 ? ` · and ${knobs.length - 3} more` : '');
    const out = [{ id: 'partitura.propose', label: one ? `Keep it and tell Unreal: ${knobs[0]} ${fmt(lone.map(r => r.score))} s` : `Keep it and tell Unreal about the ${knobs.length} timing changes`, keepsEdit: true, main: [], op: { type: 'propose', ids: [] }, quiet: true, knobs: keys, apply: stage,
      words: () => `${one ? `${knobs[0]} would go from ${fmt(lone.map(r => r.da))} s to ${fmt(lone.map(r => r.score))} s${lone.length === 1 ? stageWords(defOf(knobs[0]), lone[0]) : ''}` : list}. The change waits in this score: Unreal changes only when you press Send to Unreal.`,
      tail: 'Nothing in the score moves.' }];
    if (knobs.every(k => c.pbind.binds.some(b => b.knob === k))) out.push({ id: 'partitura.back', label: one ? `Put it back at Unreal's ${fmt(liveOf(defOf(knobs[0])))} s` : "Put them back at Unreal's values", keepsEdit: false, main: rows.flatMap(r => r.els).slice(-2), op: { type: 'sync', ids: [] }, quiet: true, knobs: keys,
      apply: n => { let changed = 0; for (const k of knobs) changed += K.Part.apply(n, K.Engine, c.pbind, c.pbind.binds.find(b => b.knob === k), liveOf(defOf(k)), null).changed.length; return changed ? undefined : false; },
      words: () => `${one ? knobs[0] + ' goes' : 'The ' + knobs.length + ' knobs go'} back to what Unreal has: the score follows it.` });
    return out;
  }
  /* a wired voice (Unreal plays the chain of a moment in order): the closest start that keeps its moment, its place among the voices and no overlap */
  function orderPlan(K, n, ids) {
    const B0 = K.before, T0 = K.typical(B0).t, Ts = K.typical(n).t, moves = [];
    for (const id of ids.slice().sort((a, b) => Ts[a][0] - Ts[b][0])) {
      const x = n.elements[id], beat0 = B0.elements[id].beat, ord = voiceOrder(B0, T0, beat0), at = ord.indexOf(id);
      const prev = ord.slice(0, at).reverse().find(o => n.elements[o]), next = ord.slice(at + 1).find(o => n.elements[o]);
      // between the voices with the same gap the rest of the piece leaves; with none when there is no room for it
      const Tn = K.typical(n).t, dur = Tn[id][1] - Tn[id][0], lo0 = prev ? Tn[prev][1] : Tn[beat0][0], hi0 = next ? Tn[next][0] - dur : Infinity;
      let lo = lo0 + (prev ? GAP : 0), hi = hi0 - (next ? GAP : 0); if (lo > hi + 1e-6) { lo = lo0; hi = hi0; }
      if (lo > hi + 1e-6) return { ok: false, why: `There is no room for ${x.key} ${prev ? 'after ' + n.elements[prev].key : ''}${prev && next ? ' and ' : ''}${next ? 'before ' + n.elements[next].key : ''} that keeps the order Unreal plays: ${x.key} lasts ${s1(dur)} s and the gap is ${s1(Math.max(0, hi - lo + dur))} s.` };
      const t = Math.min(Math.max(Tn[id][0], lo), hi);
      if (x.beat !== beat0) { x.beat = beat0; x.at = { ref: beat0, edge: 'start', off: 0 }; }
      if (!retime(K, n, id, t, { alone: aloneOf(K, id) })) return { ok: false, why: `${x.key} cannot be placed there.` };
      moves.push({ id, beat0, ord: ord.filter(o => n.elements[o]), t });
    }
    return { ok: true, moves };
  }
  function orderCands(item, K) {
    const B0 = K.before; if (!B0) return { cands: [] };
    const ids = (item.ids || [item.el]).filter(id => (item.verbs || {})[id] === 'move' && K.score.elements[id] && B0.elements[id] && K.score.elements[id].type === 'vo');
    if (!ids.length) return { cands: [] };
    const probe = orderPlan(K, clone(K.score), ids);
    if (!probe.ok) return { cands: [], why: probe.why };
    const key = ids.map(id => keyOf(K.score, id)).join(', ');
    return { cands: [{ id: 'order.keep', label: `Keep the order Unreal plays: place ${key} between its neighbours`, keepsEdit: false, main: ids,
      apply: n => (orderPlan(K, n, ids).ok ? undefined : false),
      solved: n => { const T = K.typical(n).t; return probe.moves.every(m => n.elements[m.id].beat === m.beat0 && JSON.stringify(voiceOrder(n, T, m.beat0).filter(o => m.ord.includes(o))) === JSON.stringify(m.ord)); } }] };
  }
  /* an anchor loop / an anchor across the sides of a decision / an anchor to something deleted */
  function detachCand(K, c) {
    const x = nodeOf(K.score, c), moment = !!K.score.beats[c];
    return { id: 'loop.detach', label: moment ? `Anchor moment ${x.key} to the end of the moment before it, at the same time` : `Anchor ${x.key} to the start of its moment, at the same time`, keepsEdit: !touched(K, c), main: moment ? [] : [c],
      apply: n => { const r = K.Edits.reanchor(n, c, null, K.Engine, { others: false }); if (!r.ok) return false; nodeOf(n, c).at = Object.assign({}, r.at); } };
  }
  function cycleCands(item, K) {
    const S = K.score, id = item.el, out = [];
    if (K.before) {   // the anchors this edit changed: the one that closed the loop is among them
      const a = o => JSON.stringify([o && o.at, o && o.end, o && o.alt]);
      const changed = Object.keys(S.elements).concat(Object.keys(S.beats)).filter(c => nodeOf(K.before, c) && a(nodeOf(K.before, c)) !== a(nodeOf(S, c)));
      for (const c of changed.slice(0, 4)) {
        out.push(detachCand(K, c));
        // a loop makes the times of the score un-keepable (reanchor refuses): the clip goes to the start of its moment at the time it had before the edit
        if (S.elements[c]) out.push({ id: 'loop.back', label: `Anchor ${S.elements[c].key} to the start of its moment, where it was`, keepsEdit: false, main: [c],
          apply: n => { const x = n.elements[c], tb = K.typical(K.before).t; if (!x || !tb[c] || !tb[x.beat]) return false; x.at = { ref: x.beat, edge: 'start', off: r4(tb[c][0] - tb[x.beat][0]) }; } });
      }
    }
    if (S.beats[id]) {
      const p = K.Edits.planLoop(S, id, K.Engine);
      if (p) {
        const b = S.beats[id].key, nb = S.beats[p.next].key;
        out.push({ id: 'loop.keep', label: `Start moment ${nb} together with ${b}, as it is now`, keepsEdit: !K.op, main: [], apply: n => { const q = K.Edits.planLoop(n, id, K.Engine); if (!q || !q.keep.ok) return false; replaceAll(n, q.keep.next); } });
        out.push({ id: 'loop.order', label: `Start moment ${nb} when ${b} ends, as the script reads`, keepsEdit: !K.op, main: [], apply: n => { const q = K.Edits.planLoop(n, id, K.Engine); if (!q || !q.order.ok) return false; replaceAll(n, q.order.next); } });
      }
    } else if (!K.before && S.elements[id]) out.push(detachCand(K, id));
    return out;
  }
  function branchCands(item, K) {
    const S = K.score, id = item.el, x = nodeOf(S, id), f = String(item.fp || '').split('|'), k = f[2], field = f[3] === 'end' ? 'end' : 'at';
    if (!x || !isBranchKey(k)) return [];
    const lab = K.Edits.optionLabel(S, k), home = field === 'end' ? { ref: x.beat, edge: 'start' } : K.Edits.homeAnchor(S, id);
    return [{ id: 'branch.alt', label: `Anchor ${x.key} ${field === 'end' ? 'to end ' : ''}at the start of its moment in ${lab}`, keepsEdit: true, main: [],
      apply: n => { const r = K.Edits.reanchorAlt(n, id, k, home, K.Engine, { field }); if (!r.ok) return false; const y = nodeOf(n, id), z = nodeOf(r.next, id); if (z.alt) y.alt = clone(z.alt); else delete y.alt; } }];
  }
  function missingCands(item, K) {
    const id = item.el, r = nodeOf(K.score, id) && K.Edits.detachLost(K.score, id, K.Engine); if (!r || !r.ok) return [];
    return [{ id: 'missing.detach', label: `Detach ${keyOf(K.score, id)} from what was deleted, keeping its time`, keepsEdit: true, main: [],
      apply: n => { const q = K.Edits.detachLost(n, id, K.Engine); if (!q.ok) return false; const y = nodeOf(n, id); for (const f of q.fields) y[f.field] = Object.assign({}, f.anchor); } }];
  }
  /* what the contract says about the item's rule: the entry its rule is made from (C3.VO.WIRED ← vo.wired) */
  const entryOf = (item, K) => K.contract && K.contract.entries.find(c => 'C3.' + c.id.toUpperCase() === item.rule);

  function candidates(item, K) {
    const r = item.rule || '';
    if (r === 'C2.VO.OVERLAP') return { cands: overlapCands(item, K) };
    if (r === 'C2.HELP.LATE') return { cands: helpLateCands(item, K) };
    if (r === 'C2.WAIT.NOHELP') return { cands: noHelpCands(item, K) };
    if (r === 'C2.FLASH') return { cands: flashCands(item, K) };
    if (r === 'C2.ALMA.EARLY') return { cands: almaCands(item, K) };
    if (r === 'C3.BLOCKING' || r === 'C2.WAIT.WHERE') return { cands: blockingCands(item, K) };
    if (r === 'C3.PARTITURA') return { cands: partituraCands(item, K) };
    if (r === 'C1.ANCHOR.CYCLE') return { cands: cycleCands(item, K) };
    if (r === 'C1.BRANCH.ANCHOR') return { cands: branchCands(item, K) };
    if (r === 'C1.ANCHOR.MISSING') return { cands: missingCands(item, K) };
    if (r === 'C3.DRIFT') { const c = item.el && K.score.elements[item.el] && knobEntry(item.el, K); return { cands: c ? driftCands(item.el, c.knob.value, K) : [] }; }
    if (r === 'C3.KNOB.OFFSET') return { cands: knobOffsetCands(item.el, K) };
    // an item of the card that comes from a contract entry (its rule is C3.<entry>): the verb of the edit says which fix fits
    const c = item.c3 && entryOf(item, K);
    if (c) {
      const ids = item.ids || [item.el], verb = id => (item.verbs || {})[id];
      if (c.kind === 'knob' && c.anchor && c.knob && ids.some(id => verb(id) === 'move')) return { cands: ids.filter(id => verb(id) === 'move').flatMap(id => knobOffsetCands(id, K)) };
      if (c.kind === 'knob' && c.knob && ids.some(id => verb(id) === 'gate')) return { cands: ids.filter(id => verb(id) === 'gate').flatMap(id => driftCands(id, (item.unreal || {})[id] != null ? item.unreal[id] : c.knob.value, K)) };
      if (c.id === 'vo.wired' && ids.some(id => verb(id) === 'move')) return orderCands(item, K);
    }
    return { cands: [] };
  }

  /* ---------- the check every fix passes before it is offered ---------- */
  function base(K) {
    if (K.base) return K.base;
    const S = K.score, P = K.ctx.problems || K.Int.staticProblems(S, K.T, K.contract, K.Engine.altRuns(S), kctx(K));
    return (K.base = { P, fps: new Set(P.filter(open).map(p => p.fp)), cycles: new Set(K.T.cycles), dangling: new Set(K.T.dangling),
      neg: new Set(Object.keys(K.T.t).filter(id => K.T.t[id][0] < -1e-3)), knobs: openKnobs(K, S, K.T) });
  }
  /* the items of the card of the edit itself (what commit() showed), and what that card would say about `n` = the edit plus a fix */
  const asked = i => i.sv === 'block' || i.sv === 'warn';
  const sameItem = (a, b) => a.rule === b.rule && (a.fp || b.fp ? a.fp === b.fp : (a.ids || [a.el]).some(x => (b.ids || [b.el]).includes(x)));
  function itemsBefore(K) {
    if (K.items0) return K.items0;
    const B = base(K), op = Object.assign({ prevScore: K.before }, K.op);
    return (K.items0 = (K.ctx.items || K.Int.opItems(op, K.score, { problems: beforeProblems(K) }, { problems: B.P }, K.contract, K.Engine, { gov: K.ctx.gov }).items).filter(asked));
  }
  const beforeProblems = K => K.beforeP || (K.beforeP = K.ctx.beforeProblems || K.Int.staticProblems(K.before, K.typical(K.before), K.contract, K.Engine.altRuns(K.before), kctx(K)));
  const remaining = (K, n, P1) => K.Int.opItems(Object.assign({ prevScore: K.before }, K.op), n, { problems: beforeProblems(K) }, { problems: P1 }, K.contract, K.Engine, { gov: K.ctx.gov }).items.filter(asked);
  const opOf = cand => Object.assign({}, cand.op || { type: 'fix', ids: [] });   // the edit it is applied as: what commit() judges it by
  /* the score the fix leaves (a copy), or null when it does not hold */
  function trial(K, item, cand) {
    const n = clone(K.score), B = base(K), no = r => { if (typeof K.ctx.trace === 'function') K.ctx.trace(cand.id, r); return null; };   // ctx.trace: why a candidate was dropped (tests, diagnostics)
    try { if (cand.apply(n) === false) return no('it cannot be applied'); } catch (e) { return no('it threw: ' + e.message); }
    const T1 = K.typical(n);
    if (T1.cycles.some(c => !B.cycles.has(c))) return no('an anchor loop');
    if (T1.dangling.some(d => !B.dangling.has(d))) return no('an anchor to nothing');
    if (Object.keys(T1.t).some(id => T1.t[id][0] < -1e-3 && !B.neg.has(id))) return no('a start before 0:00');
    const P1 = K.Int.staticProblems(n, T1, K.contract, K.Engine.altRuns(n), kctx(K)), open1 = P1.filter(open);
    const made = open1.find(p => !B.fps.has(p.fp) && !IGNORE.has(p.rule)); if (made) return no('it creates ' + made.rule + ' ' + made.fp);
    if (cand.solved ? !cand.solved(n, T1) : item.fp && open1.some(p => p.fp === item.fp)) return no('the problem is still there');
    const kn = openKnobs(K, n, T1);
    for (const key of kn) if (!B.knobs.has(key)) return no('a new difference from the Partitura: ' + key);
    if ((cand.knobs || []).some(key => kn.has(key))) return no('the knob still differs');
    if (K.before && K.op) {
      // in the card of an edit: the card is judged again on the edit plus the fix, as commit() will. The fix may not make it say anything new,
      // and the item it is for must be gone. (Match Unreal replaces the edit and is judged as always, quiet: its own `solved` says it)
      if (!(cand.quiet && !cand.keepsEdit)) {
        const rem = remaining(K, n, P1), items0 = itemsBefore(K);
        const more = rem.find(r => !items0.some(o => sameItem(o, r))); if (more) return no('the card would say more: ' + more.rule);
        if (items0.some(o => sameItem(o, item)) && rem.some(r => sameItem(r, item))) return no('the card would still say it');
      }
    } else if (!cand.quiet) {
      // a row of Problems, or a fix on its own: it must not open a card of its own (Match Unreal and the staging of a change are quiet)
      const it = K.Int.opItems(Object.assign({ prevScore: K.score }, opOf(cand)), n, { problems: B.P }, { problems: P1 }, K.contract, K.Engine, { gov: K.ctx.gov });
      const bad = it.items.find(i => i.sv === 'block' || i.sv === 'warn'); if (bad) return no('it would open a card: ' + bad.rule);
    }
    return { n, T1 };
  }
  const moveWords = (K, T1, ids) => ids.filter(id => K.T.t[id] && T1.t[id] && Math.abs(T1.t[id][0] - K.T.t[id][0]) > .05).slice(0, 2).map(id => {
    const d = T1.t[id][0] - K.T.t[id][0];
    return `${keyOf(K.score, id)} moves from ${K.Int.clock(K.T.t[id][0])} to ${K.Int.clock(T1.t[id][0])} (${d > 0 ? '+' : '−'}${Math.abs(d).toFixed(1)} s).`;
  });
  const usersWords = (K, n) => {
    const a = users(K, K.score), b = users(K, n), name = p => K.Engine.PERSONAS[p].name, ch = Object.keys(a).filter(p => Math.abs(b[p] - a[p]) > .05);
    return ch.length ? `${ch.map(p => `${name(p)} ${K.Int.fmt(a[p])} → ${K.Int.fmt(b[p])}`).join(' · ')}${Math.abs(b.typical - a.typical) > .05 ? '' : ' (Typical does not change)'}.` : '';
  };
  function build(K, item, cand, t) {
    const eff = K.Int.effect(K.score, t.n, K.Engine), rip = K.Int.rippleLine(eff);
    const said = cand.words ? cand.words(K, t.n, t.T1) : moveWords(K, t.T1, cand.main || []).join(' ');
    const detail = [K.op ? (cand.keepsEdit ? 'Your change stays.' : 'Replaces your change.') : '', said, cand.users ? usersWords(K, t.n) : '', cand.tail || (rip ? rip + '.' : 'Nothing else moves.')].filter(Boolean).join(' ');
    const apply = n => { try { return cand.apply(n); } catch (e) { return false; } };   // it held on the copy; on a score it was not made for, it just says no
    return { id: cand.id, label: cand.label, detail, apply, keepsEdit: !!cand.keepsEdit, op: opOf(cand), rule: item.rule, el: item.el || null };
  }
  // the reference of "≠ headset" (baseline, golden) is derived, not part of what an edit does: Match Unreal moves it even when it only gives the score back
  const noRef = s => { const c = Object.assign({}, s); delete c.baseline; delete c.golden; return c; };
  const signature = n => { const t = JSON.stringify([n.elements, n.beats, n.propuestas || null]); let h = 5381; for (let i = 0; i < t.length; i++) h = ((h << 5) + h + t.charCodeAt(i)) | 0; return (h >>> 0).toString(36) + ':' + t.length; };

  function analyze(item, ctx) {
    if (!handles(item) || !ctx || !ctx.score) return { fixes: [], why: '' };
    const K = kit(ctx), { cands, why } = candidates(item, K), fixes = [], seen = new Set();
    for (const cand of cands) {
      if (fixes.length >= MAX_FIXES) break;
      const t = trial(K, item, cand); if (!t) continue;
      const sig = signature(t.n); if (seen.has(sig)) continue;   // two ways that end in the same score are one
      if (K.before && K.Edits.sameScore(noRef(t.n), noRef(K.before))) continue;   // it only takes the edit back: that is Cancel
      seen.add(sig); fixes.push(Object.assign(build(K, item, cand, t), { sig }));
    }
    return { fixes, why: fixes.length ? '' : why || '' };
  }
  const propose = (item, ctx) => analyze(item, ctx).fixes;
  /* the fixes for every item of a card as one list: the rules of the piece first (C1, C2), then what Unreal says (C3); two fixes that end in
     the same score are one. why: what the first item without a fix says, when there is no fix at all */
  function suggest(items, ctx) {
    const rank = { C1: 0, C2: 1, C3: 2 }, list = [], seen = new Set(); let why = '';
    for (const it of items.map((x, i) => [x, i]).sort((a, b) => (rank[a[0].ly] != null ? rank[a[0].ly] : 3) - (rank[b[0].ly] != null ? rank[b[0].ly] : 3) || a[1] - b[1]).map(x => x[0])) {
      const r = analyze(it, ctx);
      for (const f of r.fixes) if (!seen.has(f.sig) && list.length < MAX_LIST) { seen.add(f.sig); list.push(f); }
      if (!why && r.why) why = r.why;
    }
    return { list, why: list.length ? '' : why };
  }

  const api = { propose, analyze, suggest, handles, RULES, waiting, addHelpLine, helpId, GAP, HELP_LEAD, FLASH_MIN };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.Fixes = api;
})(typeof window !== 'undefined' ? window : globalThis);
