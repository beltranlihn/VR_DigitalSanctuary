/* Soul Charger editor · INTEGRITY (docs/editor-obra/anexos/17-integridad.md).
   Layers: C1 score structure · C2 rules of the piece · C3 contract with Unreal (obra/unreal/contract.json) · INV invariants.
   staticProblems() lists what is wrong in the score as it is; opItems() lists what an edit would break, for the impact card. */
(function (root) {
  'use strict';
  const GOAL = 15 * 60;
  const fmt = s => { s = Math.max(0, s); const m = Math.floor(s / 60); return m + ':' + String(Math.round(s - m * 60)).padStart(2, '0'); };

  function contractFor(el, contract) {
    if (!contract || !el) return [];
    return contract.entries.filter(c => {
      const m = c.match || {};
      if (m.group && m.group !== el.group) return false;
      if (m.key && !new RegExp(m.key).test(el.key)) return false;
      return !!(m.group || m.key);
    });
  }

  function staticProblems(score, sched, contract) {
    const P = [], E = score.elements;
    const add = (sv, ly, rule, msg, el, own) => P.push({ fp: rule + '|' + (el || ''), sv, ly, rule, msg, el: el || null, own: own || '—' });
    for (const id of sched.cycles) add('block', 'C1', 'C1.ANCHOR.CYCLE', `Anchor cycle in moment ${(score.beats[id] || E[id] || {}).key || id}: its time can't be computed (falls back to 0).`, id);
    for (const id of sched.dangling || []) add('block', 'C1', 'C1.ANCHOR.MISSING', `${(E[id] || {}).key || id} is anchored to an element that no longer exists: it falls back to the start of its moment.`, id);
    if (sched.total > GOAL) add('warn', 'C2', 'C2.TOTAL.GOAL', `Typical total ${fmt(sched.total)} is over the 15:00 goal.`, null);
    const helps = {};
    for (const id in E) if (E[id].help) (helps[E[id].help] = helps[E[id].help] || []).push(id);
    for (const id in E) {
      const e = E[id];
      if (e.gate) {
        if (!helps[id]) add('warn', 'C2', 'C2.WAIT.NOHELP', `${e.key} has no help before its timeout (rule: every wait has help).`, id);
        for (const h of helps[id] || []) {
          const hs = sched.t[h][0] - sched.t[id][0];
          if (hs >= e.gate.fw) add('warn', 'C2', 'C2.HELP.LATE', `${E[h].key} would come after the ${e.gate.fw} s timeout of ${e.key}: it never plays.`, h);
        }
        if (e.gate.fw <= e.gate.expected) add('warn', 'C2', 'C2.WAIT.FW', `${e.key}: the timeout (${e.gate.fw} s) is not longer than the expected time (${e.gate.expected} s).`, id);
      }
      for (const c of contractFor(e, contract)) {
        if (c.kind === 'knob' && c.knob && e.gate && e.gate.fw !== c.knob.value)
          add('warn', 'C3', 'C3.DRIFT', `${e.key} timeout is ${e.gate.fw} s here but ${c.knob.name} is ${c.knob.value} s in Unreal.`, id, c.owner);
        if (c.kind === 'not-blocking' && e.gate)
          add('info', 'C3', 'C3.NOTBLOCKING', `${e.key}: ${c.msg}`, id, c.owner + (c.graph ? ' › ' + c.graph : ''));
      }
    }
    const n = Object.keys(E).length;
    add('info', 'C3', 'C3.SCOPE', `0 of ${n} elements reach Unreal yet: the score is not wired (phase F4). Everything here is a preview.`, null);
    // accepted problems keep their state
    const acc = score.accepted || [];
    for (const p of P) { const a = acc.find(x => x.fp === p.fp); if (a) Object.assign(p, { st: 'accepted', who: a.who, reason: a.reason }); }
    for (const a of acc) if (!P.some(p => p.fp === a.fp)) P.push(Object.assign({ st: 'accepted' }, a));
    for (const p of P) p.st = p.st || 'open';
    return P;
  }

  /* what an edit breaks. op = {type:'move'|'move-beat'|'offset'|'trim'|'delete'|'gate'|…, ids:[...], ...}
     returns { items:[{sv:'inv'|'block'|'warn'|'info', ly, rule, title, body, ev, el}], repairs:[{id,label,checked}] } */
  function opItems(op, score, before, after, contract, Engine) {
    const items = [], repairs = [], E = score.elements, seen = new Set();
    // a moment move shifts everything after it the same amount: only the moment's own elements are checked
    const verb = { move: 'move', offset: 'move', 'move-beat': 'move', trim: 'trim', delete: 'delete', gate: 'gate' }[op.type] || op.type;
    const touched = new Set(op.ids || []);
    if (op.type === 'move' || op.type === 'offset') {
      const kids = Engine.dependents(score);
      for (const id of op.ids) for (const k of Engine.family(score, id, kids)) touched.add(k);
    }
    for (const id of touched) {
      const e = E[id] || op.removed && op.removed[id]; if (!e) continue;
      for (const c of contractFor(e, contract)) {
        const sv = (c.on || {})[verb]; if (!sv) continue;
        // matching the timeout to the Unreal knob is never a break: it removes a drift
        if (verb === 'gate' && c.kind === 'knob' && c.knob && E[id] && E[id].gate && E[id].gate.fw === c.knob.value) continue;
        const k = c.id + '|' + sv; if (seen.has(k)) { const it = items.find(i => i.key === k); if (it && !it.keys.includes(e.key)) it.keys.push(e.key); continue; }
        seen.add(k);
        const title = { literal: 'Hardwired in Unreal', wired: 'Wired in Unreal', knob: 'Knob in Unreal', 'not-blocking': 'Different in Unreal', 'not-in-unreal': 'Not in Unreal' }[c.kind] || 'Unreal';
        let body = (verb === 'delete' && c.msgDelete) ? c.msgDelete + ' ' + c.msg : c.msg;
        if (c.kind === 'knob' && c.knob && c.knob.lock) body += ' It is a final value approved in the test level: a reason is required.';
        items.push({ key: k, keys: [e.key], sv, ly: 'C3', rule: 'C3.' + c.id.toUpperCase(), title, body, ev: c.owner + (c.graph ? ' › ' + c.graph : ''), el: id, c3: true, lock: !!(c.knob && c.knob.lock) });
      }
    }
    if (op.type === 'delete') {
      const kids = Engine.dependents(op.prevScore || score); const orphans = [];
      for (const id of op.ids) for (const k of kids[id] || []) if (!op.ids.includes(k)) orphans.push(k);
      if (orphans.length) {
        items.push({ sv: 'inv', ly: 'C1', rule: 'C1.ORPHANS', title: `${orphans.length} element${orphans.length > 1 ? 's are' : ' is'} anchored to it`, body: 'They would lose their anchor: ' + orphans.slice(0, 6).map(k => (E[k] || {}).key || k).join(', ') + (orphans.length > 6 ? '…' : '') + '.', ev: '', el: op.ids[0] });
        repairs.push({ id: 'reanchor', label: 'Re-anchor them to its parent (they keep their times)', checked: true });
        repairs.push({ id: 'family', label: 'Delete them too', checked: false });
      }
    }
    // new static problems caused by the edit (C1/C2)
    if (after) {
      const fpB = new Set(before.problems.map(p => p.fp));
      // on a delete, the lost anchors are the C1.ORPHANS item above: its repair re-anchors them
      for (const p of after.problems) if (!fpB.has(p.fp) && p.ly !== 'C3' && p.sv !== 'info' && !(op.type === 'delete' && p.rule === 'C1.ANCHOR.MISSING'))
        items.push({ sv: p.sv, ly: p.ly, rule: p.rule, title: p.rule === 'C2.TOTAL.GOAL' ? 'Over the 15:00 goal' : p.rule === 'C1.ANCHOR.MISSING' ? 'Anchor lost' : p.rule === 'C2.HELP.LATE' ? 'Help would never play' : p.rule === 'C1.ANCHOR.CYCLE' ? 'Anchor cycle' : 'Rule of the piece', body: p.msg, ev: 'rule ' + p.rule, el: p.el });
    }
    return { items, repairs };
  }
  root.Integrity = { contractFor, staticProblems, opItems, fmt };
})(window);
