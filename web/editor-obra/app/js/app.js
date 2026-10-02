/* Soul Charger editor · APP: state, edits (always through integrity), undo, save, 3D preview sync, keyboard. */
'use strict';
const $ = s => document.querySelector(s);
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const clamp = (x, a, b) => Math.min(b, Math.max(a, x));
const fmtS = v => (Math.round(v * 10) / 10).toFixed(1);
function tc(t) { t = Math.max(0, t); const m = Math.floor(t / 60), r = t - m * 60; return String(m).padStart(2, '0') + ':' + (r < 10 ? '0' : '') + r.toFixed(1); }
function voDur(text) { text = String(text || ''); return 1 + text.split(/\s+/).filter(Boolean).length / 2.4 + (text.match(/…/g) || []).length * .5; }   // same estimate as the prototype (world.js:154)
const LS_DRAFT = 'sc-editor-draft-v1', LS_PREF = 'sc-editor-pref-v1';
const lsGet = k => { try { return JSON.parse(localStorage.getItem(k) || 'null'); } catch (_) { return null; } };
const lsSet = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (_) {} };

const App = {
  score: null, roles: null, contract: null, sched: null, problems: [], kids: {},
  k: 1, persona: 'typical', mode: 'all', sel: null, selKind: null, selRole: null, insTab: 'insp', libTab: 'scenes', libQuery: '',
  openActs: new Set(), collapsed: {}, locked: {}, pps: 8, ph: 0, playing: false, follow: true, drawer: null, showAnchors: true,
  undo: [], redo: [], baseRev: 0, dirty: false, savedAt: null, who: 'B', SC: null, edited: false,
  tab: Math.random().toString(36).slice(2), view: new URLSearchParams(location.search).get('view') || null,
  HUE: { int: '#777777', vo: '#398559', ui: '#7F7936', obj: '#4E78B3', world: '#9A6E42', pawn: '#5E6570', fx: '#398559', amb: '#398559', hap: '#B34FB3' },
  AUD: new Set(['vo', 'fx', 'amb']),
};

/* ---------- boot ---------- */
async function boot() {
  const get = async u => { const r = await fetch(u, { cache: 'no-store' }); if (!r.ok) throw new Error(u + ' → ' + r.status); return r.json(); };
  try {
    [App.score, App.roles, App.contract] = await Promise.all([get('/obra/score/score.json'), get('/obra/unreal/roles.json'), get('/obra/unreal/contract.json')]);
  } catch (e) { document.body.innerHTML = `<div style="padding:40px;color:#E0E0E0;font:13px Geist,system-ui">Could not load the score: ${esc(e.message)}.<br>Run <b>python tools/editor/serve_editor.py</b> and open http://localhost:8767/editor-obra/app/</div>`; return; }
  App.baseRev = App.score.rev || 1;
  const pref = lsGet(LS_PREF) || {};
  Object.assign(App, { persona: pref.persona || 'typical', pps: pref.pps || 8, who: pref.who || 'B', collapsed: pref.collapsed || {}, follow: pref.follow !== false });
  const d = lsGet(LS_DRAFT);
  if (d && d.baseRev === App.baseRev && d.score && JSON.stringify(d.score) !== JSON.stringify(App.score)) {
    App.score = d.score; App.dirty = true; App.edited = true; if (App.view !== '3d') setTimeout(() => toast('Restored your unsaved changes · File ▸ Reload from disk discards them'), 400);
  }
  if (App.view === '3d') App.mode = 'v3d';
  fitScale(); compute(); applyMode(); UI.renderAll(); initViewer(); initKeys(); initChannel();
  let rz = 0; addEventListener('resize', () => { clearTimeout(rz); rz = setTimeout(() => { fitScale(); UI.renderTimelineSelection(); protoResize(); }, 100); });
  const first = App.score.acts[1]; if (first) App.openActs.add(first.id);
  UI.renderLibrary();
}
/* ISP is designed at 1:1 for 1280×720 and up; below that the whole app scales down instead of breaking (App.k) */
function fitScale() {
  const k = Math.min(1, innerWidth / 1280, innerHeight / 720), a = $('#app'); App.k = k;
  if (k < 1) Object.assign(a.style, { transform: `scale(${k})`, transformOrigin: '0 0', width: innerWidth / k + 'px', height: innerHeight / k + 'px' });
  else Object.assign(a.style, { transform: '', width: '', height: '' });
  // ISP rule: the timeline is 402 px, or 45% of the window when it is short (unless the user dragged it)
  if (!App.tlhUser) document.documentElement.style.setProperty('--tlh', Math.round(Math.min(402, innerHeight / k * .45)) + 'px');
}
function compute() {
  App.sched = ScoreEngine.resolve(App.score, { persona: App.persona });
  App.kids = ScoreEngine.dependents(App.score);
  App.problems = Integrity.staticProblems(App.score, App.sched, App.contract);
  // how far the score is from what the 3D prototype plays (its own schedule = score.golden, typical user)
  const G = (App.score.golden || {}).times || {}, T = App.sched.t; let d = 0;
  for (const id in G) { const a = T[id], g = G[id]; if (!a || Math.abs(a[0] - g[0]) > 1e-3 || Math.abs(a[1] - g[1]) > 1e-3) d++; }
  for (const id in App.score.elements) if (!G[id]) d++;
  App.protoDiff = d;
}
function savePref() { lsSet(LS_PREF, { persona: App.persona, pps: App.pps, who: App.who, collapsed: App.collapsed, follow: App.follow }); }

/* ---------- edits: every change goes through here ---------- */
const QUIET = new Set(['add', 'lane-new', 'lane-rename', 'lane-delete', 'lane-change', 'note', 'marker', 'audio', 'rename', 'reopen']);
function commit(label, op, mutate) {
  const beforeStr = JSON.stringify(App.score);
  const next = JSON.parse(beforeStr);
  if (mutate(next) === false) return false;
  const sched = ScoreEngine.resolve(next, { persona: App.persona });
  const after = { problems: Integrity.staticProblems(next, sched, App.contract) };
  const opx = Object.assign({ prevScore: App.score }, op);
  const { items, repairs } = Integrity.opItems(opx, next, { problems: App.problems }, after, App.contract, ScoreEngine);
  const finish = extra => {
    App.undo.push(beforeStr); if (App.undo.length > 80) App.undo.shift(); App.redo = [];
    if (extra) extra(next);
    App.score = next; markDirty(); compute(); UI.renderAll();
  };
  const shown = QUIET.has(op.type) ? [] : items.filter(i => i.sv !== 'info');
  if (QUIET.has(op.type)) { finish(); const nw = items.filter(i => i.sv !== 'info' && i.ly !== 'C3').length; if (nw) toast(`${label} · ${nw} new warning${nw > 1 ? 's' : ''} in Problems (F8)`); return true; }
  if (!shown.length) { finish(); const inf = items.find(i => i.sv === 'info'); if (inf) toast(inf.body); return true; }
  UI.impactCard(label, items, repairs, (decision, reason, rep) => {
    if (decision === 'cancel') { UI.renderInspector(); return; }   // inputs go back to the value that stayed
    finish(n => {
      if (op.type === 'delete' && rep) applyDeleteRepair(n, op, rep);
      if (decision === 'anyway') {
        n.accepted = n.accepted || [];
        for (const it of items) if (it.sv === 'block' || it.sv === 'warn') {
          const fp = it.rule + '|' + (it.el || '');
          if (!n.accepted.some(a => a.fp === fp)) n.accepted.push({ fp, sv: it.sv, ly: it.ly, rule: it.rule, msg: it.title + ': ' + it.body, el: it.el, own: it.ev, who: App.who, reason, at: new Date().toISOString(), neAPK: !!it.c3 });
          if (it.c3 && n.elements[it.el]) n.elements[it.el].neAPK = true;
        }
      }
    });
    toast(decision === 'anyway' ? 'Done · accepted and recorded in Problems' : 'Done');
  });
  return true;
}
/* delete keeps the score computable: dependents are re-anchored to the deleted element's anchor (same times), or deleted too */
function applyDeleteRepair(n, op, rep) {
  const before = App.score, t = App.sched.t;
  const kids = ScoreEngine.dependents(before);
  if (rep === 'family') {
    for (const id of op.ids) for (const k of ScoreEngine.family(before, id, kids)) delete n.elements[k];
    return;
  }
  for (const id of op.ids) {
    const gone = before.elements[id]; if (!gone) continue;
    for (const k of kids[id] || []) {
      const e = n.elements[k]; if (!e) continue;
      if (e.at && e.at.ref === id) {
        const a = gone.at, ref = a && a.ref;
        const base = ref ? (a.edge === 'start' ? t[ref][0] : t[ref][1]) : 0;
        e.at = { ref: ref || null, edge: a ? a.edge : 'start', off: +(t[k][0] - base).toFixed(4) };
      }
      if (e.end && e.end.ref === id) { e.dur = { mode: 'fixed', value: +(t[k][1] - t[k][0]).toFixed(4) }; e.end = null; }
      if (e.help === id) e.help = null;
    }
  }
}
function undo() { if (!App.undo.length) return toast('Nothing to undo'); App.redo.push(JSON.stringify(App.score)); App.score = JSON.parse(App.undo.pop()); markDirty(); compute(); UI.renderAll(); }
function redo() { if (!App.redo.length) return toast('Nothing to redo'); App.undo.push(JSON.stringify(App.score)); App.score = JSON.parse(App.redo.pop()); markDirty(); compute(); UI.renderAll(); }

/* ---------- edit verbs ---------- */
const Act = {
  move(id, dt, lane, keepKids) {
    const e = App.score.elements[id]; if (!e) return;
    const newIn = lane && lane.newIn; if (newIn) lane = null;
    const relane = newIn || (lane && lane !== e.lane);
    if (Math.abs(dt) < 1e-4 && !relane) return;   // grabbed and released in place: nothing changes
    // a lane is only how the timeline is drawn: changing it alone never touches Unreal
    const type = Math.abs(dt) < 1e-4 ? 'lane-change' : 'move';
    commit(`${type === 'move' ? 'Move' : 'Lane'} · ${e.key}`, { type, ids: [id] }, n => {
      const x = n.elements[id];
      x.at = x.at || { ref: x.beat, edge: 'start', off: 0 };
      x.at.off = +(x.at.off + dt).toFixed(4);
      if (newIn) x.lane = addLane(n, newIn);
      else if (lane) x.lane = lane;
      if (keepKids) for (const k of App.kids[id] || []) { const y = n.elements[k]; if (y && y.at && y.at.ref === id) y.at.off = +(y.at.off - dt).toFixed(4); }
    });
  },
  moveBeat(bid, dt) {
    const b = App.score.beats[bid]; if (!b || Math.abs(dt) < 1e-4) return;
    const ids = (App.score.acts.flatMap(a => a.beats)); const prev = ids[ids.indexOf(bid) - 1];
    const own = Object.keys(App.score.elements).filter(k => App.score.elements[k].beat === bid);
    commit(`Move moment · ${b.key}`, { type: 'move-beat', ids: own }, n => {
      const x = n.beats[bid];
      x.at = x.at || (prev ? { ref: prev, edge: 'end', off: 0 } : { ref: null, edge: 'start', off: 0 });
      x.at.off = +(x.at.off + dt).toFixed(4);
    });
  },
  trim(id, dur) {
    const e = App.score.elements[id]; if (!e) return;
    commit(`Trim · ${e.key}`, { type: 'trim', ids: [id] }, n => {
      const x = n.elements[id];
      if (x.gate) x.gate.expected = +Math.max(.5, Math.min(dur, x.gate.fw)).toFixed(3);
      else { x.dur = { mode: 'fixed', value: +Math.max(.1, dur).toFixed(3) }; }
    });
  },
  setOffset(id, off) {
    const e = App.score.elements[id]; if (!e || !isFinite(off)) return;
    commit(`Move · ${e.key}`, { type: 'offset', ids: [id] }, n => { n.elements[id].at.off = +off; });
  },
  setGate(id, field, v) {
    const e = App.score.elements[id]; if (!e || !e.gate || !isFinite(v)) return;
    // expected is the simulated user (never reaches Unreal); the timeout is the real knob
    commit(`Wait · ${e.key} · ${field === 'fw' ? 'timeout' : 'expected'}`, { type: field === 'fw' ? 'gate' : 'sim', ids: [id] }, n => { n.elements[id].gate[field] = +v; });
  },
  setText(id, text) {
    const e = App.score.elements[id]; if (!e) return;
    commit(`Text · ${e.key}`, { type: 'text', ids: [id] }, n => { const x = n.elements[id]; x.text = text; if (x.type === 'vo' && !(x.audio && x.audio.dur)) x.dur = { mode: 'audio', value: +voDur(text).toFixed(4) }; });
  },
  setLane(id, lane) {
    const e = App.score.elements[id]; if (!e || lane === e.lane) return;
    const [s, en] = App.sched.t[id];
    if (laneBusy(lane, s, en, new Set([id]))) { toast('Occupied: that lane already has something there. Pick another lane or create one.'); UI.renderInspector(); return; }
    commit(`Lane · ${e.key}`, { type: 'lane-change', ids: [id] }, n => { n.elements[id].lane = lane; });
  },
  remove(ids) {
    ids = ids.filter(id => App.score.elements[id]); if (!ids.length) return;
    const removed = {}; ids.forEach(id => removed[id] = App.score.elements[id]);
    commit(`Delete · ${ids.map(id => App.score.elements[id].key).join(', ')}`, { type: 'delete', ids, removed }, n => { ids.forEach(id => delete n.elements[id]); });
    if (!App.score.elements[App.sel]) select(null);
  },
  newLane(gid, after) {
    const g = App.score.groups.find(x => x.id === gid); if (!g) return null;
    let id = null;
    commit(`New lane · ${g.name}`, { type: 'lane-new', ids: [] }, n => { id = addLane(n, gid, after); });
    return id;
  },
  renameLane(lid, name) {
    name = String(name || '').trim(); if (!name || !App.score.lanes[lid] || App.score.lanes[lid].name === name) return UI.renderTimeline();
    commit('Rename lane', { type: 'lane-rename', ids: [] }, n => { n.lanes[lid].name = name; });
  },
  deleteLane(lid) {
    const used = Object.values(App.score.elements).some(e => e.lane === lid);
    if (used) return toast('Only empty lanes can be deleted. Move or delete its elements first.');
    const g = App.score.groups.find(x => x.lanes.includes(lid));
    if (g && g.lanes.length < 2) return toast('A group keeps at least one lane.');
    commit('Delete lane', { type: 'lane-delete', ids: [] }, n => { const gg = n.groups.find(x => x.lanes.includes(lid)); gg.lanes = gg.lanes.filter(x => x !== lid); delete n.lanes[lid]; });
  },
  add(kind, extra) {
    const t = App.ph, bid = beatAt(t), bs = App.sched.t[bid][0];
    const spec = {
      vo: { group: 'vo', type: 'vo', key: uniqueKey('VO_NEW'), label: 'New line', text: 'New line…', dur: { mode: 'audio', value: +voDur('New line…').toFixed(4) } },
      sound: { group: 'fx', type: 'sound', key: extra && extra.sound || uniqueKey('FX_NEW_SOUND'), label: extra && extra.sound || 'FX_NEW_SOUND', sound: extra && extra.sound || null, isNew: !(extra && extra.sound), dur: { mode: 'instant', value: 0 } },
      wait: { group: 'int', type: 'wait', key: uniqueKey('G_NEW'), label: 'New wait', gate: { expected: 6, fw: 25 }, dur: { mode: 'elastic', value: 6 } },
    }[kind];
    if (!spec) return;
    const len = spec.gate ? spec.gate.expected : spec.dur.value || .05;
    const lane = freeLane(spec.group, t, t + Math.max(len, .05));
    const id = 'el_n' + Date.now().toString(36);
    let laneId = lane;
    commit(`Add · ${spec.key}`, { type: 'add', ids: [id] }, n => {
      if (!laneId) laneId = addLane(n, spec.group);
      n.elements[id] = Object.assign({ beat: bid, lane: laneId, at: { ref: bid, edge: 'start', off: +(t - bs).toFixed(4) }, end: null, text: null, sound: null, note: null, gate: null, help: null, simOnly: false, when: null, hint: null, ghost: null, legacy: null, by: App.who, created: new Date().toISOString() }, spec);
    });
    select(id);
  },
  rename(id, name) {
    const e = App.score.elements[id]; if (!e || !name || name === e.key) return UI.renderInspector();
    if (Object.values(App.score.elements).some(x => x !== e && x.key === name)) { toast(name + ' already exists'); return UI.renderInspector(); }
    const go = inbox => commit(`Rename · ${e.key}`, { type: 'rename', ids: [id] }, n => { const x = n.elements[id]; x.key = name; x.label = name; if (x.isNew || x.sound === e.key) x.sound = name; if (inbox) x.audio.inbox = inbox; });
    // a WAV already waiting in the inbox follows the new name, so Unreal imports it with the right one
    if (e.isNew && e.audio && e.audio.inbox) fetch(`/api/audio/rename?from=${encodeURIComponent(e.key)}&to=${encodeURIComponent(name)}`, { method: 'POST' })
      .then(r => r.json().then(j => { if (!r.ok) throw new Error(j.error); go(j.path); }))
      .catch(err => { toast('Could not rename the WAV in the inbox: ' + err.message); UI.renderInspector(); });
    else go(null);
  },
  reopen(fp) {
    commit('Reopen problem', { type: 'reopen', ids: [] }, n => {
      const a = (n.accepted || []).find(x => x.fp === fp); if (!a) return false;
      n.accepted = n.accepted.filter(x => x !== a);
      if (a.el && n.elements[a.el] && !n.accepted.some(x => x.el === a.el && x.neAPK)) delete n.elements[a.el].neAPK;
    });
  },
  addNote(text) {
    text = String(text || '').trim(); if (!text) return;
    commit('Note', { type: 'note', ids: [] }, n => { n.notes = n.notes || {}; n.notes['nt_' + Date.now().toString(36)] = { t: +App.ph.toFixed(2), who: App.who, text, at: new Date().toISOString(), el: App.selKind === 'el' ? App.sel : null }; });
  },
  bookmark() {
    commit('Bookmark', { type: 'marker', ids: [] }, n => { n.markers = n.markers || {}; const k = Object.keys(n.markers).length + 1; n.markers['mk_' + Date.now().toString(36)] = { t: +App.ph.toFixed(2), name: 'Bookmark ' + k, who: App.who }; });
    toast('Bookmark at ' + tc(App.ph));
  },
};
function addLane(n, gid, after) {
  const gg = n.groups.find(x => x.id === gid); let i = gg.lanes.length + 1, id;
  do { id = 'ln_' + gid + '_' + (i++); } while (n.lanes[id]);
  n.lanes[id] = { name: gg.name + ' ' + (gg.lanes.length + 1), group: gid };
  const at = after ? gg.lanes.indexOf(after) + 1 : gg.lanes.length; gg.lanes.splice(at, 0, id);
  return id;
}
function uniqueKey(base) { const keys = new Set(Object.values(App.score.elements).map(e => e.key)); if (!keys.has(base)) return base; let i = 2; while (keys.has(base + '_' + i)) i++; return base + '_' + i; }
function beatAt(t) { let best = null; for (const a of App.score.acts) for (const b of a.beats) { const [s] = App.sched.t[b]; if (s <= t + 1e-6 && (!best || s >= App.sched.t[best][0])) best = b; } return best || App.score.acts[0].beats[0]; }
function laneBusy(lane, s, e, exclude) {
  const E = App.score.elements, T = App.sched.t; const e2 = Math.max(e, s + .05);
  for (const id in E) { if (E[id].lane !== lane || (exclude && exclude.has(id))) continue; const [a, b0] = T[id]; const b = Math.max(b0, a + .05); if (a < e2 - 1e-4 && b > s + 1e-4) return id; }
  return null;
}
/* ISP laneLibreCerca: the nearest free lane of the same group; null = create one */
function freeLane(gid, s, e) { const g = App.score.groups.find(x => x.id === gid); for (const l of g.lanes) if (!laneBusy(l, s, e)) return l; return null; }

/* ---------- selection, playhead, persona, modes ---------- */
function select(id, kind) {
  App.sel = id; App.selKind = id ? (kind || (App.score.beats[id] ? 'beat' : 'el')) : null; App.selRole = null;
  if (App.insTab !== 'insp') App.insTab = 'insp';
  UI.renderTimelineSelection(); UI.renderInspector(); UI.renderStatus();
}
function selectRole(name) { App.selRole = name; App.sel = null; App.selKind = 'role'; App.insTab = 'insp'; UI.renderTimelineSelection(); UI.renderInspector(); UI.renderLibrary(); UI.renderStatus(); }
function setPersona(p) { App.persona = p; savePref(); compute(); UI.renderAll(); }
function applyMode() {
  const app = $('#app'), lib = $('#library'), tr = $('#transport'), body = $('#bodyrow');
  app.classList.toggle('mode-v3d', App.mode === 'v3d'); app.classList.toggle('mode-tl', App.mode === 'tl');
  const g = document.querySelector('.libgut'); if (g) g.remove();
  if (App.mode === 'tl') {
    // timeline only: library on the left of the whole body, transport full width on top (ISP timeline window)
    body.insertBefore(lib, $('#stagecol')); const gut = document.createElement('div'); gut.className = 'gutter libgut'; lib.after(gut);
    app.insertBefore(tr, body);
  } else {
    if (lib.parentElement !== $('#mid')) $('#mid').insertBefore(lib, $('#mid').firstChild);
    if (tr.parentElement !== $('#stagecol')) $('#stagecol').insertBefore(tr, $('#timeline'));
  }
}
function setMode(m) { App.mode = m; applyMode(); UI.renderAll(); if (App.SC) { seekProto(App.ph, true); protoResize(); } }
function seek(t, fromChannel) {
  App.ph = clamp(t, 0, App.sched.total);
  seekProto(App.ph); UI.movePlayhead();
  if (!fromChannel) post({ t: App.ph, playing: App.playing });
}
let _sp = 0;
function seekProto(t, now) { if (!App.SC) return; if (now) { try { App.SC.seek(t); } catch (_) {} return; } if (_sp) return; _sp = requestAnimationFrame(() => { _sp = 0; try { App.SC.seek(App.ph); } catch (_) {} }); }
let _last = 0, _ticking = false, _lastPost = 0;
function play(on, fromChannel) {
  App.playing = on; _last = performance.now();
  if (App.SC) { try { App.SC.setPlaying(on); } catch (_) {} }
  if (on && !_ticking) { _ticking = true; requestAnimationFrame(tick); }
  UI.renderTransport();
  if (!fromChannel) post({ t: App.ph, playing: on });
}
function tick(now) {
  if (!App.playing) { _ticking = false; return; }
  if (App.SC && App.SC.S) App.ph = App.SC.S.t; else App.ph += (now - _last) / 1000;
  _last = now;
  if (App.ph >= App.sched.total) { App.ph = App.sched.total; play(false); }
  // the other tab corrects its drift once a second
  if (now - _lastPost > 1000) { _lastPost = now; post({ t: App.ph, playing: App.playing }); }
  UI.movePlayhead(true); requestAnimationFrame(tick);
}

/* ---------- 3D preview: the narrative prototype, driven by the playhead ---------- */
function initViewer() {
  const f = $('#proto'); f.src = '/prototipo-narrativo/index.html?debug';
  f.addEventListener('load', () => {
    let n = 0; const iv = setInterval(() => {
      const w = f.contentWindow, d = f.contentDocument; n++;
      if (w && w.SC && d) {
        clearInterval(iv);
        const st = d.createElement('style');
        st.textContent = '#bar,#explore,#look,#intro,#top,#cues,#lefthand,#where{display:none!important} body{background:#05080d!important}';
        d.head.appendChild(st);
        try { w.SC.S.started = true; const intro = d.querySelector('#intro'); if (intro) intro.hidden = true; } catch (_) {}
        // the editor owns the keyboard: keys pressed with the 3D view focused run the editor's shortcuts, never the prototype's
        w.addEventListener('keydown', ev => { onKey(ev); ev.stopImmediatePropagation(); }, true);
        w.addEventListener('keyup', ev => ev.stopImmediatePropagation(), true);
        w.addEventListener('mousedown', () => document.querySelectorAll('.menu.ov,.qa.ov').forEach(n => n.remove()), true);
        try { f.blur(); window.focus(); } catch (_) {}
        App.SC = w.SC; seekProto(App.ph, true); UI.renderViewerBar(); protoResize();
      } else if (n > 120) { clearInterval(iv); UI.renderViewerBar('The 3D preview could not start.'); }
    }, 100);
  });
}

/* the prototype sizes its canvas on window resize: tell it whenever its frame changes (UI hidden, mode, scale) */
function protoResize() { const f = $('#proto'); try { setTimeout(() => f.contentWindow.dispatchEvent(new Event('resize')), 30); } catch (_) {} }

/* ---------- save / load ---------- */
let _draftT = 0;
function markDirty() { App.dirty = true; App.edited = true; clearTimeout(_draftT); _draftT = setTimeout(() => { lsSet(LS_DRAFT, { baseRev: App.baseRev, savedAt: Date.now(), score: App.score }); post({ score: App.score }); }, 400); }
async function save() {
  if (App.view === '3d') return toast('Save from the timeline tab.');
  const next = JSON.parse(JSON.stringify(App.score)); next.rev = (App.baseRev || 1) + 1; next.savedBy = App.who; next.savedAt = new Date().toISOString();
  try {
    const r = await fetch('/api/score', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(next) });
    const j = await r.json(); if (!r.ok) throw new Error(j.error || r.status);
    App.score.rev = next.rev; App.score.savedBy = next.savedBy; App.score.savedAt = next.savedAt;
    App.baseRev = next.rev; App.dirty = false; App.savedAt = j.saved; try { localStorage.removeItem(LS_DRAFT); } catch (_) {}
    UI.renderTop(); UI.renderStatus(); toast('Saved · rev ' + next.rev + ' · obra/score/score.json');
  } catch (e) { toast('Could not save: ' + e.message); }
}
async function reloadFromDisk() { try { localStorage.removeItem(LS_DRAFT); } catch (_) {} location.reload(); }
function exportScore() { const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([JSON.stringify(App.score, null, 1)], { type: 'application/json' })); a.download = 'score-rev' + App.baseRev + '.json'; a.click(); }
function importScore(file) {
  file.text().then(t => { const s = JSON.parse(t); if (s.schema !== 2 || !s.elements) throw new Error('not a score'); App.undo.push(JSON.stringify(App.score)); App.score = s; markDirty(); compute(); UI.renderAll(); toast('Imported ' + file.name); })
    .catch(e => toast('Could not import: ' + e.message));
}

/* ---------- WAV for a new sound ---------- */
function wavHeader(buf) { try { const d = new DataView(buf); if (d.getUint32(0, false) !== 0x52494646 || d.getUint32(8, false) !== 0x57415645) return null; let o = 12; while (o + 8 <= d.byteLength) { const id = d.getUint32(o, false), sz = d.getUint32(o + 4, true); if (id === 0x666d7420) return { fmt: d.getUint16(o + 8, true), ch: d.getUint16(o + 10, true), sr: d.getUint32(o + 12, true), bits: d.getUint16(o + 22, true) }; o += 8 + sz + (sz & 1); } } catch (_) {} return null; }
const BLOBS = {};
async function loadWav(id, file) {
  const e = App.score.elements[id]; if (!e) return;
  const buf = await file.arrayBuffer(); const hdr = wavHeader(buf);
  if (!hdr) return toast('Not a WAV file: Unreal needs a PCM WAV.');
  let dur = 0; try { const ac = new (window.AudioContext || window.webkitAudioContext)(); const ab = await ac.decodeAudioData(buf.slice(0)); dur = ab.duration; ac.close(); } catch (_) {}
  BLOBS[id] = URL.createObjectURL(new Blob([buf], { type: 'audio/wav' }));
  let name = e.key; if (/^FX_NEW_SOUND/.test(name)) name = cleanId(file.name);
  let uploaded = null;
  try { const r = await fetch('/api/audio?name=' + encodeURIComponent(name), { method: 'POST', body: buf }); const j = await r.json(); if (r.ok) uploaded = j.path; else toast('Upload: ' + j.error); } catch (_) {}
  commit(`Load WAV · ${name}`, { type: 'audio', ids: [id] }, n => { const x = n.elements[id]; x.key = name; x.label = name; x.sound = name; x.audio = { file: file.name, dur: +dur.toFixed(3), sr: hdr.sr, ch: hdr.ch, bits: hdr.bits, pcm: hdr.fmt === 1, inbox: uploaded }; });
  if (uploaded) toast('WAV saved to ' + uploaded + ' · imported into Unreal on the next push');
}
function cleanId(v) { v = String(v || '').trim().replace(/\.[^.]+$/, '').replace(/[^A-Za-z0-9_]+/g, '_').replace(/^_+|_+$/g, ''); if (/^hap_/i.test(v)) v = v.slice(4); const m = v.match(/^(fx|vo|amb)_/i); return m ? m[1].toUpperCase() + v.slice(m[1].length) : 'FX_' + (v || 'NEW_SOUND'); }

/* ---------- two tabs: timeline + 3D view stay in sync ---------- */
let BC = null;
function initChannel() {
  try {
    BC = new BroadcastChannel('sc-editor');
    BC.onmessage = m => {
      const d = m.data || {}; if (d.from === App.tab) return;
      // the 3D tab gets every edit, so its moment names and totals never go stale (it never saves)
      if (d.score && App.view === '3d') { App.score = d.score; App.edited = true; compute(); UI.renderTransport(); UI.renderViewerBar(); UI.renderStatus(); }
      if (d.t != null && (!App.playing || Math.abs(d.t - App.ph) > .25)) seek(d.t, true);
      if (d.playing != null && d.playing !== App.playing) play(d.playing, true);
    };
  } catch (_) {}
}
function post(m) { if (BC) try { BC.postMessage(Object.assign({ from: App.tab }, m)); } catch (_) {} }
function openSecondTab() { window.open(location.pathname + '?view=3d', '_blank'); }

/* ---------- toasts, keys ---------- */
let _toastT = 0;
function toast(msg) { let t = document.querySelector('.toast'); if (!t) { t = document.createElement('div'); t.className = 'toast'; document.body.appendChild(t); } t.textContent = msg; t.style.display = 'block'; t.style.transform = `translateX(-50%) scale(${App.k || 1})`; clearTimeout(_toastT); _toastT = setTimeout(() => { t.style.display = 'none'; }, 3200); }
function initKeys() { document.addEventListener('keydown', onKey); }
function onKey(e) {
  {
    const typing = e.target.closest && e.target.closest('input,textarea,select,[contenteditable=true]');
    const mod = e.ctrlKey || e.metaKey, k = (e.key || '').toLowerCase();
    if (mod && e.key.toLowerCase() === 's') { e.preventDefault(); save(); return; }
    if (typing) { if (e.key === 'Escape') e.target.blur(); return; }
    if (UI.closeOverlay && e.key === 'Escape' && UI.closeOverlay()) return;
    if (mod && e.key.toLowerCase() === 'z') { e.preventDefault(); e.shiftKey ? redo() : undo(); return; }
    if (mod && e.key.toLowerCase() === 'y') { e.preventDefault(); redo(); return; }
    if (e.key === ' ') { e.preventDefault(); play(!App.playing); return; }
    if (e.key === 'Home') return seek(0);
    if (e.key === 'End') return seek(App.sched.total);
    if (e.key === 'F8') { e.preventDefault(); App.drawer = App.drawer === 'problems' ? null : 'problems'; UI.renderDrawer(); UI.renderTransport(); return; }
    if (k === 'a' && e.shiftKey && !mod) { e.preventDefault(); UI.quickAdd(); return; }
    if (k === 'a' && !e.shiftKey && !mod && !e.altKey) { App.showAnchors = !App.showAnchors; UI.renderTimelineSelection(); UI.renderTransport(); return; }
    if (k === 'm' && !mod && !e.altKey) { e.preventDefault(); e.shiftKey ? UI.noteBox() : Act.bookmark(); return; }
    if (e.altKey && k === 't') { e.preventDefault(); const g = App.selKind === 'el' && App.score.elements[App.sel] ? App.score.elements[App.sel].group : 'fx'; Act.newLane(g); return; }
    if ((e.key === 'Delete' || e.key === 'Backspace') && App.selKind === 'el') { e.preventDefault(); Act.remove([App.sel]); return; }
    if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
      e.preventDefault(); const sg = e.key === 'ArrowLeft' ? -1 : 1, step = e.shiftKey ? 1 : .1;
      if (e.altKey && App.selKind === 'el') Act.move(App.sel, sg * step, null, false); else seek(App.ph + sg * step);
      return;
    }
    if (e.key === 'Escape') select(null);
  }
}
window.App = App; window.Act = Act;
window.addEventListener('beforeunload', e => { if (App.dirty && App.view !== '3d') { e.preventDefault(); e.returnValue = ''; } });
document.addEventListener('DOMContentLoaded', boot);
