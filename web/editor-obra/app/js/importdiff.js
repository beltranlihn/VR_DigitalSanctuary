/* Veation VR Studio · IMPORT DIFF: what changed in guion.js since the score last took it, and how to take it (lote 5 design B §7, audit D2).
   Pure (no DOM, no files): it runs in the browser (the panel "Changes in guion.js") and in Node (tools/score/import_report.mjs,
   tools/score/import_test.mjs). guion.js is an import source, never the truth: nothing here applies by itself.
   A record speaks of everything in prototype names (uids), never in ids: an extraction gives the same record whatever ids it
   made, and an id never changes for a clip once the uidMap has it. recordOfScore / recordsOf / sigOf are also what the schema-3
   upgrade (Edits.migrate3) seeds `score.uidMap` with, so what the upgrade stores and what the importer compares are the same
   text by construction.
   record of an element: { uid, beat (the key of its moment), key, type, group, at, end (anchors: { ref: uid, edge, off }), dur,
   gate { expected, fw }, help (uid of its wait), when (the closure's name guion.js wrote), text, label, hint, note }
   record of a moment: { uid: '@' + key, key, title, desc, act, at }.
   diff(score, extraction)   → { beatRen, rows, mapUpdates, refresh, revive, hidden, stable }: the rows are what the panel and the CLI show.
   applyImportRows(score, extraction, d, sel, ctx) → the score with the rows the user chose taken (pure: it returns a new one).
   Without a uidMap (schema 2) the names come from `legacy.uid`, the signature is the score's own, and the result is only a report
   (nothing can be applied: the ids of an extraction are not stable until the schema-3 upgrade). */
(function (root) {
  'use strict';
  const has = (o, k) => Object.prototype.hasOwnProperty.call(o, k);
  const nul = v => (v === undefined ? null : v);
  /* the text of a value with its keys sorted: the same record is the same text whatever order it was written in */
  function canon(v) {
    if (v === null || typeof v !== 'object') return JSON.stringify(nul(v));
    if (Array.isArray(v)) return '[' + v.map(canon).join(',') + ']';
    return '{' + Object.keys(v).sort().map(k => JSON.stringify(k) + ':' + canon(v[k])).join(',') + '}';
  }
  /* 10 hex characters of a 53-bit hash of the text (cyrb53: the same number in every browser and in Node) */
  function sigOf(record) {
    const s = canon(record);
    let h1 = 0xdeadbeef, h2 = 0x41c6ce57;
    for (let i = 0; i < s.length; i++) { const c = s.charCodeAt(i); h1 = Math.imul(h1 ^ c, 2654435761); h2 = Math.imul(h2 ^ c, 1597334677); }
    h1 = Math.imul(h1 ^ (h1 >>> 16), 2246822507) ^ Math.imul(h2 ^ (h2 >>> 13), 3266489909);
    h2 = Math.imul(h2 ^ (h2 >>> 16), 2246822507) ^ Math.imul(h1 ^ (h1 >>> 13), 3266489909);
    return (4294967296 * (2097151 & h2) + (h1 >>> 0)).toString(16).padStart(14, '0').slice(-10);
  }
  /* the prototype name of a moment ('@' + key) or of an element (its legacy uid); an element made in the editor has none:
     its id stands in (it is never in guion.js, so it is never compared) */
  function uidOf(score, id) {
    const b = score.beats && score.beats[id]; if (b) return '@' + b.key;
    const e = score.elements && score.elements[id];
    return e ? (e.legacy && e.legacy.uid) || id : id;
  }
  const anchorOf = (score, a) => (a ? { ref: a.ref ? uidOf(score, a.ref) : null, edge: a.edge || 'start', off: nul(a.off) } : null);
  /* the record of one element or moment of a score (id), or null when it is not there */
  function recordOfScore(score, id) {
    const b = score.beats && has(score.beats, id) ? score.beats[id] : null;
    if (b) return { uid: '@' + b.key, key: b.key, title: nul(b.title), desc: nul(b.desc), act: nul(b.act), at: anchorOf(score, b.at) };
    const e = score.elements && has(score.elements, id) ? score.elements[id] : null; if (!e) return null;
    const bt = score.beats[e.beat], lg = e.legacy || {};
    return {
      uid: lg.uid || id, beat: bt ? bt.key : null, key: e.key, type: e.type, group: e.group,
      at: anchorOf(score, e.at), end: anchorOf(score, e.end),
      dur: e.dur ? { mode: e.dur.mode, value: nul(e.dur.value) } : null,
      gate: e.gate ? { expected: e.gate.expected, fw: e.gate.fw } : null,
      help: e.help ? uidOf(score, e.help) : null,
      // the closure's name: schema 2 keeps it in `when`, schema 3 moved it to legacy.when (the record does not change with the upgrade)
      when: has(lg, 'when') ? nul(lg.when) : nul(e.when),
      text: nul(e.text), label: nul(e.label), hint: nul(e.hint), note: nul(e.note),
    };
  }
  /* every record a score (or an extraction, which has the same shape) holds, by prototype name: the elements that came from
     guion.js (they have a legacy uid) and the moments ('@' + key). { uid: record } */
  function recordsOf(score) {
    const out = {};
    for (const id of Object.keys(score.beats || {})) { const r = recordOfScore(score, id); out[r.uid] = r; }
    for (const id of Object.keys(score.elements || {})) { const e = score.elements[id]; if (e.legacy && e.legacy.uid) { const r = recordOfScore(score, id); out[r.uid] = r; } }
    return out;
  }

  /* ================= what changed in guion.js (design B §7.2) =================
     diff(score, extraction) → { beatRen, rows, mapUpdates, refresh, revive, hidden, stable, counts }
       rows        what the panel shows; each has a `rid`, a `kind` and the verbs it offers (`defaults`: the ones taken by default)
         moment-added    guion.js has a moment the score doesn't ({ rec, elements: the uids of its clips })        add-moment
         added           a clip the score doesn't have ({ rec })                                                     add
         renamed         the same clip under another key ({ was, wasKey, rec })                                     rename
         changed         a clip whose text / timing / structure differ ({ groups: { text|timing|structure: [{ field, was, now }] } })  text, timing
         moment-changed  the same for a moment (title, description / its anchor / its act)                          text, timing
         removed         a clip the score has and guion.js no longer does                                           keep (and "delete here", its own card)
         moment-removed  a moment guion.js no longer has (it stays: a moment is never deleted)                      keep
         `edited`: the score also changed that element since it took guion's (its own signature differs from the stored one);
         `estimate`: a voice whose length differs only because its words did (the recording decides, so it is never taken);
         `sig`: the signature of guion's record, what the score stores once it has taken it
       mapUpdates  { oldUid: { to, id, via } }: a name moved (a renumbered moment, a '#n' that shifted, a renamed key); the id stays
       refresh     { uid: sig }: guion's record changed but the score already says the same (a reference followed a renamed clip)
       revive      uids kept ("removed in guion") that guion.js has again
       hidden      rows left out because they were dismissed (until guion.js changes them again) or already kept
       stable      false: the names came from legacy.uid (schema 2): a report, nothing can be applied
     What a row shows is guion.js NOW against the score NOW, but only for elements whose guion record changed since the score took
     it (signature ≠ the stored one): if nobody changed guion.js there is no row, whatever the user edited here. When an element
     was edited on both sides (`edited`), the fields that differ may be the user's own edit: such a row is never taken by default. */
  const clone = o => JSON.parse(JSON.stringify(o));
  const isObj = o => !!o && typeof o === 'object' && !Array.isArray(o);
  const same = (a, b) => canon(a) === canon(b);
  const FIELDS = { text: ['text', 'label', 'hint', 'note'], timing: ['at', 'end', 'dur', 'gate'], structure: ['type', 'group', 'help', 'when', 'beat'] };
  const MOMENT_FIELDS = { text: ['title', 'desc'], timing: ['at'], structure: ['act'] };
  const KIND_ORDER = ['moment-added', 'added', 'renamed', 'changed', 'moment-changed', 'removed', 'moment-removed'];
  const fam = uid => uid.replace(/#\d+$/, '');
  const isMoment = uid => uid[0] === '@';
  const momentOf = uid => (isMoment(uid) ? uid.slice(1) : uid.slice(0, Math.max(0, uid.indexOf('/'))));
  const keyOfUid = uid => (isMoment(uid) ? uid.slice(1) : uid.slice(uid.indexOf('/') + 1));

  /* the names the score has: its uidMap (schema 3), or the ones its elements came with (legacy.uid) and its moments' keys, each with
     the signature of its own record (schema 2: there is no earlier guion record to compare with, so the score is its own base) */
  function mapOf(score) {
    if (isObj(score.uidMap)) return { map: score.uidMap, stable: true };
    const map = {};
    for (const id of Object.keys(score.beats || {})) map['@' + score.beats[id].key] = { id, sig: sigOf(recordOfScore(score, id)) };
    for (const id of Object.keys(score.elements || {})) { const lg = score.elements[id].legacy; if (lg && lg.uid) map[lg.uid] = { id, sig: sigOf(recordOfScore(score, id)) }; }
    return { map, stable: false };
  }
  const orderOf = s => (s.acts || []).reduce((a, x) => a.concat(x.beats || []), []);

  function diff(score, extracted) {
    const { map, stable } = mapOf(score), G = recordsOf(extracted), E = score.elements || {}, B = score.beats || {};
    const there = id => has(E, id) || has(B, id), dead = uid => !!map[uid] && map[uid].state === 'deleted-here';
    // the live names of the score: a moment, an element; the ones decided "keep" (removed in guion) are still in the score
    const oldM = [], oldE = [], kept = new Set();
    for (const uid of Object.keys(map)) {
      const u = map[uid]; if (!isObj(u) || !there(u.id)) continue;
      if (u.state === 'removed-in-guion') kept.add(uid); else if (u.state) continue;
      (isMoment(uid) ? oldM : oldE).push(uid);
    }
    const srCache = {}, sr = uid => srCache[uid] || (srCache[uid] = recordOfScore(score, map[uid].id));
    const gOrder = {}; Object.keys(G).forEach((u, i) => { gOrder[u] = i; });

    // 1 · moments: by name; a moment the score has and guion.js lost, with a moment guion.js has and the score never heard of,
    // the same title: renumbered (several with one title: the same act first, then the nearest in order)
    const posO = {}, posN = {};
    orderOf(score).forEach((id, i) => { if (B[id]) posO['@' + B[id].key] = i; });
    orderOf(extracted).forEach((id, i) => { const b = extracted.beats[id]; if (b) posN['@' + b.key] = i; });
    const newM = Object.keys(G).filter(u => isMoment(u) && !map[u]), usedN = new Set(), beatRen = {};
    for (const o of oldM.filter(u => !G[u])) {
      const sb = B[map[o].id]; if (!sb.title) continue;
      const c = newM.filter(n => !usedN.has(n) && G[n].title === sb.title)
        .sort((a, b) => ((G[a].act === sb.act ? 0 : 1) - (G[b].act === sb.act ? 0 : 1)) || (Math.abs(posN[a] - posO[o]) - Math.abs(posN[b] - posO[o])));
      if (c.length) { beatRen[o.slice(1)] = c[0].slice(1); usedN.add(c[0]); }
    }
    const renUid = uid => { const b = momentOf(uid); return has(beatRen, b) ? (isMoment(uid) ? '@' + beatRen[b] : beatRen[b] + uid.slice(b.length)) : uid; };

    // 2 · clips: a family (moment + key, without '#n') that keeps its names is matched by name; one that does not (a '#n' moved) is
    // matched by content, the cheapest pairs first, up to a cost of 4
    function cost(a, b) {
      let c = 0;
      const la = a.key !== b.key && a.label ? a.label.split(a.key).join(b.key) : a.label;   // a label that is the key follows the key
      if (!same(la, b.label)) c += 2;
      for (const f of ['note', 'hint', 'text']) if (!same(a[f], b[f])) c += 2;
      const A = a.at || {}, Bt = b.at || {};
      if (renUid(A.ref || '') !== (Bt.ref || '') || (A.edge || 'start') !== (Bt.edge || 'start')) c += 2;
      if (Math.abs((A.off || 0) - (Bt.off || 0)) > 1e-6) c += 1;
      if (!same(a.dur, b.dur)) c += 1;
      return c;
    }
    const famOld = {}, famNew = {};
    for (const o of oldE) { const f = fam(renUid(o)); (famOld[f] = famOld[f] || []).push(o); }
    for (const n of Object.keys(G)) if (!isMoment(n) && !dead(n)) { const f = fam(n); (famNew[f] = famNew[f] || []).push(n); }
    const pairs = [], added = [], removed = [];
    for (const f of Object.keys(famOld).concat(Object.keys(famNew).filter(k => !famOld[k]))) {
      const O = famOld[f] || [], N = famNew[f] || [];
      if (O.length === N.length && O.every(u => N.includes(renUid(u)))) { for (const u of O) pairs.push([u, renUid(u)]); continue; }
      const cand = [];
      for (const o of O) for (const n of N) cand.push([cost(sr(o), G[n]) - (renUid(o) === n ? .1 : 0), o, n]);
      cand.sort((x, y) => x[0] - y[0] || (x[1] < y[1] ? -1 : x[1] > y[1] ? 1 : 0) || (x[2] < y[2] ? -1 : 1));
      const uo = new Set(), un = new Set();
      for (const [c, o, n] of cand) if (!uo.has(o) && !un.has(n) && c <= 4) { uo.add(o); un.add(n); pairs.push([o, n]); }
      for (const o of O) if (!uo.has(o)) removed.push(o);
      for (const n of N) if (!un.has(n)) added.push(n);
    }
    // 3 · a key renamed in guion.js: a clip the score has and guion.js lost, and a new one in the same moment, of the same type,
    // that differs only by its key (and a label that was the key)
    const ren = new Set();
    for (const o of removed.slice()) {
      const a = sr(o), m = has(beatRen, a.beat) ? beatRen[a.beat] : a.beat;
      const n = added.find(u => G[u].beat === m && G[u].type === a.type && G[u].group === a.group && G[u].key !== a.key && cost(a, G[u]) === 0);
      if (n) { removed.splice(removed.indexOf(o), 1); added.splice(added.indexOf(n), 1); pairs.push([o, n]); ren.add(o); }
    }
    const remap = {};
    for (const [o, n] of pairs) remap[o] = n;
    for (const o of oldM) remap[o] = renUid(o);
    const nm = u => (u == null ? u : has(remap, u) ? remap[u] : renUid(u));
    const normA = a => (a ? Object.assign({}, a, { ref: a.ref ? nm(a.ref) : a.ref }) : a);
    // the score's record in the names of guion.js now: what is compared with guion's
    function inNew(a, n, g) {
      const r = Object.assign({}, a, { uid: n, at: normA(a.at) });
      if (isMoment(n)) return Object.assign(r, { key: g.key });
      r.beat = has(beatRen, a.beat) ? beatRen[a.beat] : a.beat; r.end = normA(a.end); r.help = a.help ? nm(a.help) : null;
      if (a.key !== g.key) { r.label = a.label ? a.label.split(a.key).join(g.key) : a.label; r.key = g.key; }   // the key has its own row (renamed) or is the user's own
      return r;
    }
    function fieldDiff(a, g, fields) {
      const out = {};
      for (const grp of Object.keys(fields)) for (const f of fields[grp]) {
        let x = a[f], y = g[f];
        if (f === 'dur' && x && y && x.mode === 'audio' && y.mode === 'audio') { x = { mode: 'audio' }; y = { mode: 'audio' }; }   // a voice lasts its recording: its estimate is not a time
        if (!same(x, y)) (out[grp] = out[grp] || []).push({ field: f, was: a[f] === undefined ? null : a[f], now: g[f] === undefined ? null : g[f] });
      }
      return out;
    }

    // 4 · the rows
    const rows = [], mapUpdates = {}, refresh = {}, revive = [];
    let hidden = 0;
    const lostM = oldM.filter(u => !G[renUid(u)]);
    const allPairs = pairs.concat(oldM.filter(u => G[renUid(u)]).map(u => [u, renUid(u)]));
    for (const [o, n] of allPairs) {
      const u = map[o], moment = isMoment(o), a = sr(o), g = G[n], gsig = sigOf(g);
      if (o !== n) mapUpdates[o] = { to: n, id: u.id, via: ren.has(o) ? 'rename' : moment ? 'moment' : 'order' };
      if (kept.has(o)) revive.push(n);
      if (u.sig && o === n && gsig === u.sig) continue;   // guion.js has not changed it since the score took it
      const edited = !!u.sig && sigOf(a) !== u.sig;
      if (ren.has(o)) {
        if (u.seen === gsig) { hidden++; continue; }
        rows.push({ rid: 'renamed:' + n, kind: 'renamed', uid: n, was: o, wasKey: a.key, id: u.id, key: g.key, moment: g.beat, type: g.type, rec: g, edited, defaults: ['rename'], sig: gsig });
        continue;
      }
      const groups = fieldDiff(inNew(a, n, g), g, moment ? MOMENT_FIELDS : FIELDS);
      if (!Object.keys(groups).length) { if (gsig !== u.sig) refresh[n] = gsig; continue; }   // the score already says what guion.js says
      if (u.seen === gsig) { hidden++; continue; }
      const dn = !moment && a.type === 'vo' && groups.text && a.dur && g.dur && a.dur.mode === 'audio' && g.dur.mode === 'audio' && a.dur.value !== g.dur.value ? { now: g.dur.value } : null;
      rows.push({ rid: (moment ? 'moment-changed:' : 'changed:') + n, kind: moment ? 'moment-changed' : 'changed', uid: n, was: o !== n ? o : null, id: u.id, key: g.key, moment: moment ? g.key : g.beat, type: g.type,
        groups, estimate: dn, edited, defaults: groups.text && !edited ? ['text'] : [], sig: gsig });
    }
    // what guion.js has that the score never heard of: a new moment (its clips go with it) or a clip
    const newMoments = newM.filter(u => !usedN.has(u)), inNewMoment = n => newMoments.indexOf('@' + G[n].beat) >= 0;
    for (const m of newMoments) rows.push({ rid: 'moment-added:' + m, kind: 'moment-added', uid: m, key: G[m].key, moment: G[m].key, title: G[m].title, rec: G[m],
      elements: added.filter(n => G[n].beat === G[m].key).sort((x, y) => gOrder[x] - gOrder[y]), defaults: ['add-moment'], sig: sigOf(G[m]) });
    for (const n of added) if (!inNewMoment(n)) rows.push({ rid: 'added:' + n, kind: 'added', uid: n, key: G[n].key, moment: G[n].beat, type: G[n].type, group: G[n].group, rec: G[n], defaults: ['add'], sig: sigOf(G[n]) });
    // what the score has and guion.js no longer does: it stays until somebody deletes it here (a clip of a moment that is gone is
    // listed under its moment)
    for (const m of lostM) {
      if (kept.has(m)) { hidden++; continue; }
      rows.push({ rid: 'moment-removed:' + m, kind: 'moment-removed', uid: m, id: map[m].id, key: m.slice(1), moment: m.slice(1), title: sr(m).title,
        elements: removed.filter(o => momentOf(o) === m.slice(1)), defaults: [], sig: null });
    }
    const inLost = o => lostM.indexOf('@' + momentOf(o)) >= 0;
    for (const o of removed) {
      if (inLost(o)) continue;
      if (kept.has(o)) { hidden++; continue; }
      const a = sr(o);
      rows.push({ rid: 'removed:' + o, kind: 'removed', uid: o, id: map[o].id, key: a.key, moment: a.beat, type: a.type, edited: !!map[o].sig && sigOf(a) !== map[o].sig, defaults: [], sig: null });
    }
    const at = r => (gOrder[r.uid] === undefined ? 1e9 : gOrder[r.uid]);
    rows.sort((x, y) => KIND_ORDER.indexOf(x.kind) - KIND_ORDER.indexOf(y.kind) || at(x) - at(y));
    const counts = {}; for (const r of rows) counts[r.kind] = (counts[r.kind] || 0) + 1;
    return { beatRen, rows, mapUpdates, refresh, revive, hidden, stable, counts };
  }

  /* ================= the words of a row (the panel and the CLI say the same) ================= */
  const FIELD_NAME = { text: 'Text', label: 'Label', hint: 'Hint', note: 'Note', at: 'Starts', end: 'Lasts until', dur: 'Length', gate: 'Wait', title: 'Title', desc: 'Description',
    act: 'Act', type: 'Type', group: 'Group', help: 'Help line of', when: 'Condition', beat: 'Moment', key: 'Name' };
  const fieldName = f => FIELD_NAME[f] || f;
  const num = x => String(Math.round(x * 100) / 100);
  /* "FX_GHOSTAPPEAR#2 (1.8)" for a clip, "moment 1.8" for a moment */
  function nameOf(uid) { if (!uid) return 'nothing'; return isMoment(uid) ? 'moment ' + uid.slice(1) : `${keyOfUid(uid)} (${momentOf(uid)})`; }
  function anchorWords(a) {
    if (!a) return 'nothing';
    const off = a.off ? ` ${a.off > 0 ? '+' : '−'} ${num(Math.abs(a.off))} s` : '';
    return `${a.edge === 'start' ? 'start' : 'end'} of ${nameOf(a.ref)}${off}`;
  }
  const clip = (s, n) => (s.length > n ? s.slice(0, n - 1) + '…' : s);
  function wordsOf(field, v) {
    if (v == null || v === '') return '(none)';
    if (field === 'at' || field === 'end') return anchorWords(v);
    if (field === 'dur') return `${v.mode === 'audio' ? 'the recording' : v.mode} ${num(v.value)} s`;
    if (field === 'gate') return `expected ${num(v.expected)} s, timeout ${num(v.fw)} s`;
    if (field === 'help') return nameOf(v);
    if (field === 'text' || field === 'label' || field === 'hint' || field === 'note' || field === 'title' || field === 'desc') return '“' + clip(String(v), 120) + '”';
    return String(v);
  }
  /* one line per row (the CLI; the panel builds its own markup from the same pieces) */
  function rowWords(r) {
    const where = r.moment ? ` in ${r.moment}` : '', fl = g => r.groups[g].map(x => fieldName(x.field).toLowerCase()).join(', ');
    switch (r.kind) {
      case 'moment-added': return `new moment ${r.key}${r.title ? ' · ' + clip(r.title, 60) : ''} · ${r.elements.length} clip${r.elements.length === 1 ? '' : 's'}`;
      case 'added': return `new ${r.type || 'clip'} ${r.key}${where}`;
      case 'renamed': return `${r.wasKey} is now ${r.key}${where}`;
      case 'changed': return `${r.key}${where}: ` + Object.keys(r.groups).map(g => `${g} (${fl(g)}${g === 'text' && r.estimate ? '; its length is an estimate, the recording decides' : ''})`).join(' · ') + (r.edited ? ' · edited here too' : '');
      case 'moment-changed': return `moment ${r.key}: ` + Object.keys(r.groups).map(g => `${g} (${fl(g)})`).join(' · ') + (r.edited ? ' · edited here too' : '');
      case 'removed': return `${r.key}${where} is not in guion.js any more`;
      case 'moment-removed': return `moment ${r.key} is not in guion.js any more${r.elements.length ? ' · ' + r.elements.length + ' clip' + (r.elements.length === 1 ? '' : 's') : ''}`;
      default: return r.kind + ' ' + r.uid;
    }
  }

  /* ================= taking rows (design B §7.3) =================
     applyImportRows(score, extraction, d, sel, ctx) → { ok, next, ids, added, verbs, flagged, taken, why }
     d = diff(score, extraction); sel = { rid: [verbs] }: add, add-moment, rename, text, timing, keep, dismiss (a row with no entry is left
     as it is, and keeps showing). Pure: the score it gets is never changed; `next` is a new one. Only a schema 3 score takes rows.
       · names follow guion.js: the uidMap moves its entries to the new names (the ids never change) and the elements' legacy.uid and
         the moments' keys with them. A renamed clip's name moves only when its rename is taken (otherwise the row keeps showing).
       · add: a new id (Edits.newId) for each clip and moment; anchors go through the uidMap, or to what the same batch adds (made in
         dependency order); an anchor that points at something the score doesn't have falls back to the start of the clip's moment
         with the offset guion gave, and is flagged. A new moment goes after its predecessor in its act.
       · rename: key and label; what Unreal plays (sound, bind.asset) stays.  text: the fields of the row.  timing: the anchors,
         the length and the wait times of the row (an anchor taken from guion.js loses a knob it had). A voice's estimated length is never taken.
       · keep: the clip stays and the map says 'removed-in-guion'.  dismiss: the row hides until guion.js changes that element again.
       · every entry it takes stores guion's signature; one with a group left (timing, say, not taken) keeps the old one, so that
         group keeps showing.
     ids = the elements it touched (added, renamed, text or timing changed); verbs = { id: 'text' | 'rename' } for the integrity
     judgement of the edit. ctx = { who, at, now, rand (ids), Edits, Engine + addLane (free lanes for the clips it adds) } */
  const dep = (file, name) => (typeof require === 'function' && typeof module !== 'undefined' ? require('./' + file) : root[name]);
  function applyImportRows(score, extracted, d, sel, ctx) {
    ctx = ctx || {}; sel = sel || {};
    const taken = { added: 0, moments: 0, renamed: 0, text: 0, timing: 0, kept: 0, dismissed: 0, names: 0 };
    const res = { ok: false, next: null, ids: [], added: [], verbs: {}, flagged: [], taken, why: null };
    if (!score || score.schema !== 3 || !isObj(score.uidMap)) { res.why = 'Only a schema 3 score can take rows from guion.js: its stable names are what the rows are matched on. Upgrade the score first.'; return res; }
    const Edits = ctx.Edits || dep('edits.js', 'Edits');
    const next = clone(score), map = next.uidMap, E = next.elements, B = next.beats, when = ctx.at || new Date().toISOString(), G = recordsOf(extracted);
    const rowOf = {}; for (const r of d.rows) rowOf[r.rid] = r;
    const want = (r, v) => !!r && Array.isArray(sel[r.rid]) && sel[r.rid].indexOf(v) >= 0;
    const flag = (uid, msg) => res.flagged.push({ uid, key: keyOfUid(uid), msg });
    const touched = new Set(), batch = {}, made = new Set();
    const newOne = prefix => { const id = Edits.newId(next, prefix, { now: ctx.now, rand: ctx.rand, taken: made }); made.add(id); return id; };

    // 1 · the names follow guion.js (all at once: an entry can take the name another one leaves)
    const rev = {}; for (const o of Object.keys(d.mapUpdates)) rev[d.mapUpdates[o].to] = d.mapUpdates[o].id;
    const moving = Object.keys(d.mapUpdates).filter(o => { const m = d.mapUpdates[o]; return m.via !== 'rename' || want(rowOf['renamed:' + m.to], 'rename'); }), saved = {};
    for (const o of moving) { saved[o] = map[o]; delete map[o]; }
    for (const o of moving) {
      const m = d.mapUpdates[o]; if (!saved[o]) continue;
      map[m.to] = saved[o]; taken.names++;
      if (isMoment(m.to)) { if (B[m.id]) B[m.id].key = m.to.slice(1); } else if (E[m.id]) E[m.id].legacy = Object.assign({}, E[m.id].legacy, { uid: m.to });
    }
    for (const uid of Object.keys(d.refresh || {})) if (map[uid]) map[uid].sig = d.refresh[uid];
    for (const uid of d.revive || []) if (map[uid] && map[uid].state === 'removed-in-guion') delete map[uid].state;
    // the map entry of a row, found by its id: step 1 has moved the names (a '#n' that shifted, a renumbered moment), and a name now
    // can belong to another clip (the one this same batch adds), so a row's own name or the one it had is not a safe way in
    const entryOf = r => { if (!r.id) return null; const k = Object.keys(map).find(q => isObj(map[q]) && map[q].id === r.id && map[q].state !== 'deleted-here'); return k ? map[k] : null; };
    const idOf = uid => {
      if (batch[uid]) return batch[uid];
      const u = map[uid]; if (u && (!u.state || u.state === 'removed-in-guion') && (E[u.id] || B[u.id])) return u.id;
      return rev[uid] && (E[rev[uid]] || B[rev[uid]]) ? rev[uid] : null;
    };

    // 2 · what is added: new moments first (their clips go with them), then clips, each after what it hangs from
    const addM = [], addU = [];
    for (const r of d.rows) if (r.kind === 'moment-added' && want(r, 'add-moment')) {
      const act = next.acts[G[r.uid].act];
      if (!act) { flag(r.uid, `guion.js has an act the score does not (act ${G[r.uid].act}): add the moment by hand`); continue; }
      addM.push(r); for (const u of r.elements) addU.push(u);
    }
    for (const r of d.rows) if (r.kind === 'added' && want(r, 'add')) addU.push(r.uid);
    for (const r of addM) batch[r.uid] = newOne('bt_');
    for (const u of addU) batch[u] = newOne('el_');
    const anchorFor = (a, fallback, uid, what) => {
      if (!a) return fallback;
      const id = a.ref ? idOf(a.ref) : null;
      if (id) return { ref: id, edge: a.edge, off: a.off };
      flag(uid, `${what} hangs from ${nameOf(a.ref)}, which the score does not have: it hangs from ${fallback && fallback.ref ? 'its place' : 'nothing'} instead`);
      return fallback ? Object.assign({}, fallback, { off: a.off || 0 }) : null;
    };
    for (const r of addM) {
      const rec = G[r.uid], id = batch[r.uid], act = next.acts[rec.act];
      const names = (((extracted.acts || [])[rec.act] || {}).beats || []).map(bid => extracted.beats[bid] && '@' + extracted.beats[bid].key);
      let pred = null;
      for (let k = names.indexOf(r.uid) - 1; k >= 0 && !pred; k--) { const pid = names[k] && idOf(names[k]); if (pid && act.beats.indexOf(pid) >= 0) pred = pid; }
      B[id] = { key: rec.key, title: rec.title, desc: rec.desc == null ? '' : rec.desc, act: rec.act, at: anchorFor(rec.at, pred ? { ref: pred, edge: 'end', off: 0 } : null, r.uid, 'The moment') };
      act.beats.splice(pred ? act.beats.indexOf(pred) + 1 : 0, 0, id);
      map[r.uid] = { id, sig: r.sig }; taken.moments++;
    }
    const exByUid = {};
    for (const id of Object.keys(extracted.elements || {})) { const x = extracted.elements[id]; if (x.legacy && x.legacy.uid) exByUid[x.legacy.uid] = x; }
    const order = [], seen = new Set();
    const visit = u => {
      if (seen.has(u)) return; seen.add(u);
      const rec = G[u]; for (const a of [rec.at, rec.end]) if (a && a.ref && addU.indexOf(a.ref) >= 0) visit(a.ref);
      if (rec.help && addU.indexOf(rec.help) >= 0) visit(rec.help);
      order.push(u);
    };
    addU.forEach(visit);
    const M3 = Edits.MIGRATE3;
    for (const u of order) {
      const rec = G[u], x = exByUid[u] || {}, id = batch[u], beat = idOf('@' + rec.beat), grp = next.groups.find(q => q.id === rec.group);
      if (!beat || !grp) { flag(u, !beat ? `its moment ${rec.beat} is not in the score` : `the group ${rec.group} is not in the score`); delete batch[u]; continue; }
      const el = { key: rec.key, type: rec.type, group: rec.group, beat, lane: grp.lanes[0],
        at: anchorFor(rec.at, { ref: beat, edge: 'start', off: 0 }, u, 'It'), end: anchorFor(rec.end, null, u, 'Its end'), dur: rec.dur ? clone(rec.dur) : null,
        label: rec.label, text: rec.text, sound: x.sound === undefined ? null : x.sound, note: rec.note,
        gate: rec.gate ? Object.assign({}, rec.gate, { blocking: true }) : null, help: null, simOnly: !!x.simOnly, hint: rec.hint, ghost: x.ghost || null,
        legacy: { uid: u, track: (x.legacy && x.legacy.track) || rec.group, behavior: !!(x.legacy && x.legacy.behavior) }, by: ctx.who || null, created: when };
      if (rec.help) { const h = idOf(rec.help); if (h) el.help = h; else flag(u, `it is the help of ${nameOf(rec.help)}, which the score does not have`); }
      if (rec.when) {   // schema 3 says the side of SHARE in `branch`; the name guion.js wrote stays in legacy.when
        const v = M3.inline && has(M3.inline, u) ? M3.inline[u] : has(M3.when, rec.when) ? M3.when[rec.when] : null;
        el.legacy.when = rec.when;
        if (v && next.branches && next.branches[M3.branch.on]) el.branch = { on: M3.branch.on, value: v };
        else flag(u, `guion.js gives it a condition (${rec.when}) and the score cannot place it on a side of SHARE: choose its branch in the inspector`);
      }
      if (rec.gate) flag(u, 'it is a new wait: check whether the stage stops at it (Waits for the user) and what it waits for');
      E[id] = el; res.added.push(id); touched.add(id); map[u] = { id, sig: sigOf(rec) }; taken.added++;
    }

    // 3 · renamed, text, timing
    for (const r of d.rows) {
      if (r.kind === 'renamed' && want(r, 'rename') && E[r.id]) {
        E[r.id].key = r.rec.key; E[r.id].label = r.rec.label;
        res.verbs[r.id] = 'rename'; touched.add(r.id); taken.renamed++; { const e = entryOf(r); if (e) e.sig = r.sig; }
      }
      if (r.kind !== 'changed' && r.kind !== 'moment-changed') continue;
      const moment = r.kind === 'moment-changed', x = moment ? B[r.id] : E[r.id]; if (!x) continue;
      const done = [];
      if (want(r, 'text') && r.groups.text) {
        for (const f of r.groups.text) x[f.field] = f.now;
        done.push('text'); taken.text++; if (!moment) { res.verbs[r.id] = 'text'; touched.add(r.id); }
      }
      if (want(r, 'timing') && r.groups.timing) {
        let all = true;
        for (const f of r.groups.timing) {
          if (f.field === 'at' || f.field === 'end') {
            if (!f.now) { if (f.field === 'end') x.end = null; else all = false; continue; }
            const ref = f.now.ref ? idOf(f.now.ref) : null;
            if (!ref) { flag(r.uid, `${fieldName(f.field)} hangs from ${nameOf(f.now.ref)}, which the score does not have: it keeps its own`); all = false; continue; }
            x[f.field] = { ref, edge: f.now.edge, off: f.now.off };
          } else if (f.field === 'dur' && f.now) x.dur = clone(f.now);
          else if (f.field === 'gate' && f.now && x.gate) x.gate = Object.assign({}, x.gate, { expected: f.now.expected, fw: f.now.fw });
        }
        if (all) { done.push('timing'); taken.timing++; if (!moment) touched.add(r.id); }
      }
      // the signature moves only when everything the row could take has been taken (the structure group is only ever shown)
      if (done.length) {
        const e = entryOf(r);
        if (e && ['text', 'timing'].filter(g => r.groups[g]).every(g => done.indexOf(g) >= 0)) e.sig = r.sig;
      }
    }

    // 4 · keep and dismiss
    const tomb = (uid, sig) => { map[uid] = { id: newOne(isMoment(uid) ? 'bt_' : 'el_'), sig, state: 'deleted-here', seen: sig }; };
    for (const r of d.rows) {
      if (r.kind === 'removed' || r.kind === 'moment-removed') {
        if (!want(r, 'keep') && !want(r, 'dismiss')) continue;
        if (map[r.uid]) map[r.uid].state = 'removed-in-guion';
        for (const u of r.elements || []) if (map[u]) map[u].state = 'removed-in-guion';
        taken.kept++; continue;
      }
      if (!want(r, 'dismiss')) continue;
      if (r.kind === 'added') tomb(r.uid, r.sig);
      else if (r.kind === 'moment-added') { tomb(r.uid, r.sig); for (const u of r.elements) tomb(u, sigOf(G[u])); }
      else { const e = entryOf(r); if (!e) continue; e.seen = r.sig; }   // nothing recorded, nothing counted
      taken.dismissed++;
    }
    res.ids = [...touched];
    if (ctx.Engine && res.added.length) Edits.fixOverlaps(score, next, ctx.Engine, ctx.addLane || addLaneTo);
    if (JSON.stringify(next) === JSON.stringify(score)) { res.why = 'Nothing was chosen, or what was chosen changes nothing.'; return res; }
    res.ok = true; res.next = next;
    return res;
  }
  /* a lane at the end of its group (the same as the editor's own addLane) */
  function addLaneTo(n, gid) {
    const g = n.groups.find(x => x.id === gid); let i = g.lanes.length + 1, id;
    do { id = 'ln_' + gid + '_' + (i++); } while (n.lanes[id]);
    n.lanes[id] = { name: g.name + ' ' + (g.lanes.length + 1), group: gid }; g.lanes.push(id);
    return id;
  }

  const api = { canon, sigOf, uidOf, recordOfScore, recordsOf, mapOf, diff, applyImportRows, rowWords, fieldName, wordsOf, anchorWords, nameOf, FIELDS, MOMENT_FIELDS, KIND_ORDER };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.ImportDiff = api;
})(typeof window !== 'undefined' ? window : globalThis);
