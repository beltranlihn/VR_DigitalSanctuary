/* Veation VR Studio · POLICY: what an edit does with the items integrity gives it, pure (no DOM) so it runs in the browser and
   in Node (tools/score/policy_test.mjs). Lote 5 design B §8.1 (audit D12): commit() in app.js keeps the DOM parts (the impact
   card, the toasts, the render) and asks here.
   decide(): quiet (applied; its new warnings go to Problems), apply (nothing to review) or card (the impact card first).
   acceptRecords() / reopen() / cleanRecords(): what "Proceed anyway", Reopen and "Clean up accepted" do to score.accepted: one record per
   rule and element, with the value it was accepted at, every decision kept, nothing removed but by an explicit clean-up. */
(function (root) {
  'use strict';
  // edits that never open a card: they add or arrange what Unreal does not know yet, or record something decided elsewhere.
  // migrate, bind, import-map and branch-view are the lote 5 operations whose own card is the decision (design B §8.1, §10.4; design A §3.6:
  // "Bind to Unreal" adds marks and bind only and refuses itself if a time would move).
  // import-add and import-map are what "Changes in guion.js" writes when it only ADDS clips and moments, follows guion's names, or keeps
  // and dismisses rows: nothing that Unreal has changes. Taking guion's text, a rename or a time is op 'import-guion' and is judged like any edit.
  // rename is not quiet (design A §7.3): renaming what Unreal has is judged like any edit (on.rename of the contract, a note
  // when the entry does not say)
  const QUIET = new Set(['import', 'sync', 'propose', 'sent', 'add', 'paste', 'lane-new', 'lane-rename', 'lane-delete', 'lane-change', 'note', 'marker', 'audio', 'reopen',
    'migrate', 'bind', 'import-map', 'import-add', 'branch-view', 'accepted-clean']);
  // a block, or a locked final value, needs a written reason; a warning goes ahead with one click and is still recorded
  const needsReason = items => items.some(i => i.sv === 'block' || i.lock);
  // something breaks: the card offers "Proceed anyway" (recorded in Problems), not "Proceed"
  const breaks = items => items.some(i => i.sv === 'block' || i.sv === 'warn');

  /* op = {type, ids, …} as commit() gets it; items = Integrity.opItems(…).items; ctx = { label, relocated, ripple }
     → { mode: 'quiet' | 'apply' | 'card', shown, needReason, breaks, toast } (toast: what a quiet edit says after it lands) */
  function decide(op, items, ctx) {
    ctx = ctx || {};
    const shown = items.filter(i => i.sv !== 'info');
    if (QUIET.has(op.type)) {
      // only the new problems of the piece count (they stay in Problems; a C3 item speaks of the edit itself); a relocation or
      // a ripple speaks first
      const nw = items.filter(i => i.sv !== 'info' && i.ly !== 'C3').length;
      const toast = nw && !(ctx.relocated || []).length && !ctx.ripple ? `${ctx.label} · ${nw} new warning${nw > 1 ? 's' : ''} in Problems (F8)` : null;
      return { mode: 'quiet', shown, needReason: false, breaks: false, toast };
    }
    if (!shown.length) return { mode: 'apply', shown, needReason: false, breaks: false, toast: null };
    return { mode: 'card', shown, needReason: needsReason(items), breaks: breaks(items), toast: null };
  }
  /* the toast once the card is decided (cancel says nothing) */
  const doneToast = (decision, ripple) => (decision === 'anyway' ? 'Done · accepted and recorded in Problems' : 'Done') + (ripple ? ' · ' + ripple : '');

  /* ---------- the records (lote 5 design B §9, audit D11): accepted means "this value" ----------
     "Proceed anyway": one record per rule and element (fp = rule|el, the fpBase), with the VALUE it was accepted at (`value`: the
     param of the problem, or where the element ended up in its moment for an Unreal item; null when the item did not say), its
     `state` ('accepted'; Policy.reopen sets 'reopened'), the score revision (`rev`) and what Unreal had when the rule knows it
     (`unreal`), and every decision kept in `history`. Pure: returns a new array, never removes a record and never changes the
     ones it gets. A record accepted again keeps its first message, takes the new author, reason, value and time, and its history
     gets the new decision (the first one included). ≠ APK is derived, not written: but accepting an Unreal break that leaves an
     element different from the APK ALSO accepts that difference, at that value (a C3.DIVERGE record: item.apk). by = { who,
     reason, at, rev? }
     Each record (and each decision of its history) keeps the VERB it was accepted for (move, trim, text, gate, delete,
     rename: item.verbs of Integrity.opItems): opItems lets a record answer only that same verb and value (Integrity.acceptedFor),
     so accepting a rename never silences a later delete. Items of the piece (C1/C2) have no verb and are written as before.
     An item that carries its own fingerprint (the problems of the piece, the wait flag) is recorded under its rule|el, with the
     rest of it as the value. */
  const I = () => root.Integrity || (typeof require === 'function' ? require('./integrity.js') : null);
  const withVerb = (o, v) => v ? Object.assign(o, { verb: v }) : o;
  /* write one decision into the list `out` (a record for its fpBase, new or updated); the first message and verb are kept */
  function put(out, spec, by) {
    const Int = I(), base = Int.fpParts(spec.fp).base, value = spec.value == null ? null : String(spec.value);
    const ev = withVerb({ state: 'accepted', value, who: by.who, reason: by.reason, at: by.at, msg: spec.msg }, spec.verb);
    let k = -1;
    for (let i = 0; i < out.length; i++) if (Int.recordOf(out[i]).base === base && (k < 0 || Int.recordOf(out[i]).value === value)) k = i;
    const extra = Object.assign({}, by.rev != null ? { rev: by.rev } : {}, spec.unreal != null ? { unreal: spec.unreal } : {});
    if (k < 0) { out.push(withVerb(Object.assign({ fp: base, sv: spec.sv, ly: spec.ly, rule: spec.rule, msg: spec.msg, el: spec.el, own: spec.own, value, state: 'accepted', who: by.who, reason: by.reason, at: by.at }, extra), spec.verb)); return; }
    const a = out[k], was = Int.recordOf(a);
    const first = withVerb({ state: was.state, value: was.value, who: a.who, reason: a.reason, at: a.at, msg: a.msg }, a.verb);
    out[k] = Object.assign({}, a, extra, { fp: base, value, state: 'accepted', history: (a.history || [first]).concat(ev), who: by.who, reason: by.reason, at: by.at });
  }
  function acceptRecords(accepted, items, by) {
    const out = (accepted || []).slice();
    for (const it of items) if (it.sv === 'block' || it.sv === 'warn') for (const el of (it.ids || [it.el])) {
      const Int = I(), fp = it.fp || it.rule + '|' + (el || ''), f = Int.fpParts(fp), verb = it.verbs && it.verbs[el];
      const value = it.values && it.values[el] != null ? it.values[el] : it.fp ? f.param : null;   // a problem of the piece has its param ('' when none); a card item says its own value or none
      put(out, { fp, sv: it.sv, ly: it.ly, rule: it.rule, msg: it.title + ': ' + it.body, el, own: it.ev, value, verb, unreal: it.unreal && it.unreal[el] }, by);
      // the difference from the APK this edit leaves is accepted too, at the value it has now (a rename or a delete leaves none)
      const key = (it.keys || [])[(it.ids || [el]).indexOf(el)] || 'It';
      // a timeout that is not the one in Unreal is the drift of Problems (C3.DRIFT|el|<timeout>|<Unreal's>): accepted here, at this value
      const dr = it.drift && it.drift[el];
      if (dr != null) put(out, { fp: 'C3.DRIFT|' + el, sv: 'warn', ly: 'C3', rule: 'C3.DRIFT', msg: `${key}: its timeout is not the one in Unreal.`, el, own: it.ev, value: dr, unreal: it.unreal && it.unreal[el] }, by);
      const apk = it.apk && it.apk[el];
      if (apk != null) {
        put(out, { fp: 'C3.DIVERGE|' + el, sv: 'warn', ly: 'C3', rule: 'C3.DIVERGE', msg: `${key}: its time here differs from what the APK does today.`, el, own: 'APK baseline', value: apk }, by);
      }
    }
    return out;
  }

  /* Reopen: the record stays (state 'reopened', one more entry in its history: who and when), so what was decided is never lost.
     `fp` is the one of the problem (rule|el|value) or its fpBase; of several records of that base, the one at the problem's value.
     Returns the same array when there is nothing to reopen */
  function reopen(accepted, fp, by) {
    const Int = I(), f = Int.fpParts(fp), out = (accepted || []).slice();
    let k = -1;
    for (let i = 0; i < out.length; i++) { const r = Int.recordOf(out[i]); if (r.base === f.base && r.state === 'accepted' && (k < 0 || (f.has && r.value === f.param))) k = i; }
    if (k < 0) return accepted;
    const a = out[k], was = Int.recordOf(a);
    const first = withVerb({ state: was.state, value: was.value, who: a.who, reason: a.reason, at: a.at, msg: a.msg }, a.verb);
    out[k] = Object.assign({}, a, { state: 'reopened', history: (a.history || [first]).concat({ state: 'reopened', who: by.who, at: by.at }) });
    return out;
  }

  /* "Clean up accepted": the records of elements (or moments) that are no longer in the score. They stay visible as "element
     deleted" until this is asked for. → { next, removed: [records] } */
  function cleanRecords(accepted, score) {
    const Int = I(), next = [], removed = [];
    for (const a of accepted || []) (Int.isGone(score, a) ? removed : next).push(a);
    return { next, removed };
  }

  const api = { QUIET, decide, doneToast, needsReason, breaks, acceptRecords, reopen, cleanRecords };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.Policy = api;
})(typeof window !== 'undefined' ? window : globalThis);
