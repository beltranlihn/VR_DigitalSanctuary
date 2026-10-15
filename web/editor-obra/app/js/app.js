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
  selMore: new Set(), clipboard: null, toastSeq: 0,   // C10: the rest of a multiselection (App.sel is the primary: the inspector), what Ctrl+C kept
  openActs: new Set(), collapsed: {}, locked: {}, pps: 8, ph: 0, playing: false, follow: true, drawer: null, showAnchors: false,
  adv: false, insDetails: false, traceOpen: false, qsSeen: false,   // the view (prefs): Simple (plain words) or Advanced ("Show technical details"), the inspector's Details, the run folded in Problems, Quick start shown once
  rate: 1, inT: null, outT: null, snap: true, kHeld: false,   // transport (C10): signed speed, the In/Out range (prefs, never the score), snapping
  branchView: {},   // lote 5 (design B §5): which option of each decision the timeline and the 3D show: { share: 'auto' | 'yes' | 'no' }; missing = its default (SHARE). A preference, never the score
  laneSize: 'compact',   // C11: lane height, compact or comfortable (prefs)
  unreadable: {},   // optional files (obra/unreal/*.json, the seed of the marks) that are there but could not be read
  undo: [], redo: [], baseRev: 0, dirty: false, savedAt: null, who: 'B', SC: null, edited: false, pick: null,
  tab: Math.random().toString(36).slice(2), view: new URLSearchParams(location.search).get('view') || null,
  HUE: { int: '#777777', vo: '#398559', ui: '#7F7936', obj: '#4E78B3', world: '#9A6E42', pawn: '#5E6570', fx: '#398559', amb: '#398559', hap: '#B34FB3' },
  AUD: new Set(['vo', 'fx', 'amb']),
};

/* ---------- boot ---------- */
async function boot() {
  const get = async u => { const r = await fetch(u, { cache: 'no-store' }); if (!r.ok) throw new Error(u + ' → ' + r.status); return r.json(); };
  try {
    const st = await fetch('/obra/score/score.json', { cache: 'no-store' }); if (!st.ok) throw new Error('/obra/score/score.json → ' + st.status);
    const txt = await st.text(); App.score = JSON.parse(txt); App.diskHash = await sha12(txt); App.savedScore = JSON.parse(txt);   // what is on disk now: saving checks it did not change
    [App.roles, App.contract] = await Promise.all([get('/obra/unreal/roles.json'), get('/obra/unreal/contract.json')]);
  } catch (e) { document.body.innerHTML = `<div style="padding:40px;color:#E0E0E0;font:13px Geist,system-ui"><b>Veation VR Studio</b> could not load the score: ${esc(e.message)}.<br>Open it with tools/editor/abrir-editor.bat, or run <b>python tools/editor/serve_editor.py --app</b></div>`; return; }
  // Unreal side (the director's DA_Partitura_Obra and knob dump): optional, the editor works without them
  // a file that is there but cannot be read (a trace half-written by smoke_obra.py, a seed corrected by hand with a slip) is
  // treated as absent and said in Problems: it never stops the editor from opening
  const opt = async u => { const v = await optJson(u); noteUnreadable(u, v === UNREADABLE); return v === UNREADABLE || v === undefined ? null : v; };
  [App.pdef, App.plive, App.pbind, App.prop, App.perillas, App.traza, App.idmap, App.knobs] = await Promise.all(['partitura_def', 'partitura', 'partitura_binding', 'partitura_propuesta', 'perillas', 'traza', 'idmap', 'knobs'].map(n => opt('/obra/unreal/' + n + '.json')));
  // a definition or a binding that parses but is not the shape the editor reads (a tool wrote something else): treated as absent and said,
  // never a blank page (compute() reads def.knobs and binding.binds on every edit)
  const odd = [];
  if (App.pdef && !(Array.isArray(App.pdef.knobs) && Array.isArray(App.pdef.stages))) { App.pdef = null; odd.push('partitura_def.json'); }
  if (App.pbind && !Array.isArray(App.pbind.binds)) { App.pbind = null; odd.push('partitura_binding.json'); }
  if (odd.length) setTimeout(() => toast(`obra/unreal/${odd.join(' and ')} is not in the shape the editor reads: it works without ${odd.length > 1 ? 'them' : 'it'}`), 1100);
  App._bigAt = Date.now();   // idmap.json and knobs.json are big and made by hand-run tools: refreshUnreal reads them again on focus, or every two minutes
  App.prop = App.prop || { valores: {}, motivos: {} };   // what was SENT (the file); what waits to be sent lives in score.propuestas
  // the last Unreal run (traza.json, tools/unreal/smoke_obra.py --traza) is compared with the score at the marks of the seed
  // (tools/score/seed_marks.mjs) until the score is bound to Unreal (schema 3): both optional
  App.markSeed = await opt('/obra/score/seed/marks-v1.json');
  await loadRunHistory();
  // the recordings of the piece (final voice mix first) and the sound files of obra/audio/media_map.json: served read-only by
  // the editor's server, optional
  const med = (await opt('/api/media')) || {};
  App.media = med.items || null; App.mediaUnmapped = med.unmapped || {}; App.mediaError = med.mapError || null;
  App.baseRev = App.score.rev || 1;
  const pref = lsGet(LS_PREF) || {};
  const tnum = v => Number.isFinite(v) && v >= 0 ? v : null;
  // a preference from an older version, or one edited by hand, never stops the editor from opening (View.cleanPref: what it cannot read is the default)
  const cp = View.cleanPref(pref, ScoreEngine.PERSONAS);
  Object.assign(App, { persona: cp.persona, pps: cp.pps, who: cp.who, collapsed: cp.collapsed, follow: pref.follow !== false, locked: cp.locked, sound: !!pref.sound,
    inT: tnum(pref.inT), outT: tnum(pref.outT), snap: pref.snap !== false, laneSize: pref.lanes === 'comfortable' ? 'comfortable' : 'compact',
    runLane: pref.runLane !== false, runAlign: pref.runAlign === 'hall' ? 'hall' : 'mark',
    adv: pref.adv === true, insDetails: pref.details === true, traceOpen: pref.traceOpen === true, qsSeen: pref.qsSeen === true,
    branchView: pref.branchView && typeof pref.branchView === 'object' && !Array.isArray(pref.branchView) ? pref.branchView : {} });
  App.showAnchors = App.adv;   // Simple starts with the anchor curves off (A turns them on); Advanced as always
  if (App.view !== '3d') await restoreDraft();
  if (App.view === '3d') App.mode = 'v3d';
  fitScale(); compute(); applyMode(); UI.renderAll(); initViewer(); initKeys(); initChannel();
  addEventListener('focus', () => refreshUnreal(undefined, true)); setInterval(() => { if (!document.hidden) refreshUnreal(); }, 20000);
  let rz = 0; addEventListener('resize', () => { clearTimeout(rz); rz = setTimeout(() => { fitScale(); UI.renderTimelineSelection(); UI.fitTransport(); protoResize(); }, 100); });
  const first = App.score.acts[1]; if (first) App.openActs.add(first.id);
  UI.renderLibrary();
  // the first launch: Help ▸ Quick start opens by itself, once (opening it sets the flag, so it never comes back by itself)
  if (App.view !== '3d' && !App.qsSeen) setTimeout(() => { if (!App.cardOpen && !document.querySelector('.ov')) UI.quickStart(); }, 800);
  const bad = Object.keys(App.unreadable); if (bad.length) setTimeout(() => toast(`${bad.join(', ')} could not be read: the editor works without it (Problems says so)`), 900);
}
/* an optional JSON file: its content; null when it is not there; UNREADABLE when it is there but is not valid JSON;
   undefined when the server cannot be reached. The parse is awaited here, so a broken file never rejects the caller */
const UNREADABLE = Object.freeze({ unreadable: true });
async function optJson(u) {
  let r; try { r = await fetch(u, { cache: 'no-store' }); } catch (_) { return undefined; }
  if (!r.ok) return null;
  try { return await r.json(); } catch (_) { return UNREADABLE; }
}
/* which optional files could not be read the last time they were looked at (compute() lists them as info in Problems);
   true when the state of that file changed */
function noteUnreadable(u, bad) {
  const f = String(u).replace(/^\//, ''), was = !!App.unreadable[f];
  if (bad) App.unreadable[f] = true; else delete App.unreadable[f];
  return was !== !!bad;
}
async function sha12(text) {
  try { const b = await crypto.subtle.digest('SHA-1', new TextEncoder().encode(text)); return [...new Uint8Array(b)].map(x => x.toString(16).padStart(2, '0')).join('').slice(0, 12); } catch (_) { return null; }
}
/* unsaved work from a previous session: restored only if it was made on THIS score; otherwise it is kept as a copy, never lost */
async function restoreDraft() {
  const d = lsGet(LS_DRAFT); if (!d || !d.score) return;
  if (Edits.sameScore(d.score, App.score)) { try { localStorage.removeItem(LS_DRAFT); } catch (_) {} return; }   // nothing unsaved in it
  const sameBase = d.baseRev === App.baseRev && (!d.baseHash || !App.diskHash || d.baseHash === App.diskHash);
  let ok = true; try { Edits.validate(d.score, ScoreEngine); } catch (e) { ok = false; }
  if (sameBase && ok) { App.score = d.score; App.dirty = true; App.edited = true; setTimeout(() => toast('Restored your unsaved changes · File ▸ Reload from disk discards them'), 400); return; }
  const path = await saveCopy(d.score, ok ? 'draft-old-base' : 'draft-broken');
  try { localStorage.removeItem(LS_DRAFT); } catch (_) {}
  setTimeout(() => toast(ok ? `Your unsaved changes were made on an older score (rev ${d.baseRev}); someone saved after. They are kept in ${path || 'a copy'}` : `Your unsaved changes could not be opened; they are kept in ${path || 'a copy'}`), 600);
}
async function saveCopy(score, why) {
  try { const r = await fetch('/api/score/copy?who=' + encodeURIComponent(App.who) + '&why=' + encodeURIComponent(why), { method: 'POST', body: JSON.stringify(score) }); const j = await r.json(); return r.ok ? j.path : null; } catch (_) { return null; }
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
  pruneSel();   // an undo, a delete or a reload can take selected clips away
  // what is on screen: the simulated user in the option of each decision picked in the transport (schema 2: nothing to pick)
  const bo = branchOpt();
  App.sched = ScoreEngine.resolve(App.score, { persona: App.persona, branch: bo });
  // the typical user in the default option of every decision decides what is written and what is checked; the others are only a
  // simulation on screen. The other options are resolved apart (schedAlt) for the rules that depend on which one plays
  App.schedT = App.persona === 'typical' && !bo ? App.sched : ScoreEngine.resolve(App.score, { persona: 'typical' });
  // the typical user in the option(s) on screen: what the guards of a drag or an offset measure (schedT is the default option, and
  // what you look at in the other side starts elsewhere)
  App.schedV = !bo ? App.schedT : App.persona === 'typical' ? App.sched : ScoreEngine.resolve(App.score, { persona: 'typical', branch: App.sched.branch });
  App.schedAlt = ScoreEngine.altRuns(App.score);
  App.kids = ScoreEngine.dependents(App.score);
  App.problems = Integrity.staticProblems(App.score, App.schedT, App.contract, App.schedAlt, knobCtx());
  App.voiceGaps = voiceGaps();
  // what other modules add to the problems (the Partitura, the Unreal run, ≠ APK, the voices, unreadable files) is collected here and
  // judged with the same rule as the rest, against the accepted records: accepted means THIS value (Integrity.settle, design B §9)
  const extra = [], acc = App.score.accepted || [];
  computePartitura(extra);
  computeReach();
  computeRun(extra);
  // derived, never stored (audit B6/C6): what differs from the APK baseline the score carries (`baseline` in schema 3, `golden`
  // in schema 2; what a Partitura knob governs is C3.PARTITURA's, not counted twice), and what changed since the last save.
  // The row carries how much it differs (C3.DIVERGE|el|<start>|<length>): accepted at one difference, it opens again at another
  const dvp = Integrity.divergeProblems(App.score, App.schedT, App.contract, App.gov, Integrity.baselineOf(App.score));
  App.diverged = new Set(dvp.map(p => p.el)); extra.push(...dvp);
  App.editedSet = Integrity.editedSince(App.savedScore, App.score, ScoreEngine);
  // in Unreal a voice lasts what its recording lasts (its pause is a separate knob): one row for all the voices that don't
  if (App.voiceGaps.length) {
    const sig = JSON.stringify(App.voiceGaps.map(g => [g.id, g.now]));
    if (App._vgSig !== sig) {   // what the piece would last with the recordings (one resolve, only when the voices change)
      const n = JSON.parse(JSON.stringify(App.score)); for (const g of App.voiceGaps) n.elements[g.id].dur = { mode: 'audio', value: g.real };
      App._vgSig = sig; App._vgTotal = ScoreEngine.resolve(n, { persona: 'typical' }).total;
    }
    extra.push({ fp: 'C2.VO.REAL||' + Integrity.voiceRealParam(App.voiceGaps), sv: 'warn', ly: 'C2', rule: 'C2.VO.REAL', el: null, own: 'final voice mix', voices: true,
      msg: `${App.voiceGaps.length} voice${App.voiceGaps.length > 1 ? 's' : ''} last${App.voiceGaps.length > 1 ? '' : 's'} differently here than in the final mix. ` +
        (Integrity.fmt(App._vgTotal) === Integrity.fmt(App.schedT.total) ? `With the recordings the piece still runs ${Integrity.fmt(App._vgTotal)}.` : `With the recordings the piece runs ${Integrity.fmt(App._vgTotal)}, not ${Integrity.fmt(App.schedT.total)}.`) });   // "runs 18:10, not 18:10" says nothing
  }
  // an optional file that is there but could not be read: said, never in the way (it is read again every 20 s)
  for (const f of Object.keys(App.unreadable)) {
    const run = /traza\.json$/.test(f), seed = /marks-v1\.json$/.test(f), tool = /(idmap|knobs)\.json$/.test(f);
    const had = run ? App.traza : seed ? App.markSeed : /idmap\.json$/.test(f) ? App.idmap : /knobs\.json$/.test(f) ? App.knobs : /\/partitura\.json$/.test(f) ? App.plive : /partitura_propuesta\.json$/.test(f) ? App.prop && App.prop.estado : null;
    extra.push({ fp: 'C3.UNREADABLE|' + f, sv: 'info', ly: 'C3', rule: 'C3.UNREADABLE', el: null, own: f, where: f.split('/').pop(), grp: run || seed ? 'run' : undefined,
      msg: `${f} is there but could not be read (it is not valid JSON${run ? '; Unreal may be writing it right now' : seed ? '; check the last change made to it by hand' : tool ? '; make it again with node tools/score/' + f.split('/').pop().replace('.json', '.mjs') : ''}). ${had ?'The editor keeps what it read before' : 'The editor works without it'} and reads it again ${tool ? 'when the window gets the focus, or every two minutes' : 'every 20 s'}.` });
  }
  App.problems = Integrity.settle(App.problems, extra, acc);
  if (App.SC) pushSoon();
}
/* the live value of an Unreal knob named "<Blueprint>.<variable>" (obra/unreal/perillas.json: the dump of the Blueprints) or
   "DA_Partitura_Obra.<knob>" (the Partitura); undefined when Unreal's files do not have it (the rules then use the contract's value) */
function knobValue(name) {
  const i = String(name).indexOf('.'); if (i < 0) return undefined;
  const bp = name.slice(0, i), v = name.slice(i + 1);
  if (bp === 'DA_Partitura_Obra') { const x = knobLive(v); return typeof x === 'number' ? x : undefined; }
  const row = ((App.perillas && App.perillas.bps && App.perillas.bps[bp]) || []).find(r => Array.isArray(r) && r[0] === v);
  if (!row) return undefined;
  try { const x = JSON.parse(row[2])[v]; return Number.isFinite(x) ? x : undefined; } catch (_) { return undefined; }
}
const knobCtx = () => ({ knob: knobValue });
/* what the engine is asked to show (schema 3): the option of each decision as picked in the transport ('auto' follows the simulated
   user: the one that hits every timeout takes Unreal's own timeout answer), the default one when nothing was picked. undefined =
   every decision on its default option: the run the checks use */
function branchOpt() {
  const brs = App.score.branches; if (!brs) return undefined;
  const o = {}; let picked = false;
  for (const on of Object.keys(brs)) {
    const v = App.branchView[on], ok = v === 'auto' || (v && Object.prototype.hasOwnProperty.call(brs[on].options, v));
    o[on] = ok ? v : 'default'; if (ok && (v === 'auto' || v !== brs[on].default)) picked = true;
  }
  return picked ? o : undefined;
}
/* the options on screen as the keys of an alternative anchor ("share=no"): what a drag of a clip that hangs from something else
   there (alt) has to move */
function viewKeys() { const b = App.sched && App.sched.branch; return b ? Object.keys(b).map(on => on + '=' + b[on]) : []; }
/* the typical user in ONE option ("share=no"; null or the default option: the default run), already worked out by compute() */
function timeIn(k) { const a = k && App.schedAlt.find(x => x.k === k); return a ? a.sched : App.schedT; }
/* where a clip starts NOW, for the guards of an edit that moves it ("It would start before 0:00"): in the option whose own anchor
   the edit changes (an alt start on screen, Edits.altKeyOf), else the earliest of the default option and the one on screen,
   since the primary anchor moves it in both */
function startNow(id) {
  const k = Edits.altKeyOf(App.score.elements[id], viewKeys());
  return k ? timeIn(k).t[id][0] : Math.min(App.schedT.t[id][0], App.schedV.t[id][0]);
}
/* the name of an option in words ("SHARE", "DON'T SHARE") */
function optionName(on, v) { return Integrity.branchText(App.score, { [on]: v }); }
/* the transport's choice: an option, 'auto' (follow the simulated user) or null (back to the default) */
function setBranchView(on, v) {
  const br = App.score.branches && App.score.branches[on]; if (!br) return;
  if (v != null && v !== 'auto' && !Object.prototype.hasOwnProperty.call(br.options, v)) return;
  if (v == null || v === br.default) delete App.branchView[on]; else App.branchView[on] = v;
  savePref(); compute(); UI.renderAll(); post({ branchView: App.branchView });   // the 3D tab shows the same side
  toast(v === 'auto' ? `${br.name}: the simulated user decides · ${optionName(on, App.sched.branch[on])} now` : `Showing ${optionName(on, App.sched.branch[on])} · ${Integrity.fmt(App.sched.total)} (this is how the timeline and the 3D play it; nothing in the score changes)`);
}

/* the final mix of a voice (by its key: VO_10#2 is VO_10), only the final mix counts as its real length; a sound effect or an
   ambience never does (owner rule: times come from the timeline). Logic and tests: js/media.js */
function mixOf(e) { return Media.mixOf(e, App.media); }
function voiceGaps() { return Media.voiceGaps(App.score, App.media); }
/* the score against DA_Partitura_Obra (always measured with the typical user, like Unreal's own timeline) */
function computePartitura(extra) {
  App.gov = {}; App.pdrift = null;
  if (!App.pdef || !App.pbind || !window.Partitura) return;
  const st = App.schedT;
  App.gov = Partitura.governedBy(App.score, st, App.pbind);
  App.pdrift = Partitura.drift(App.score, st, App.pdef, App.plive, App.pbind);
  // a bind whose frozen element no longer holds (deleted, moved to another moment, no longer the first voice): a note
  extra.push(...Partitura.staleProblems(App.pdrift, App.pdef.stages));
  const by = {};
  for (const r of App.pdrift.rows) if (r.diff != null && Math.abs(r.diff) > .05) (by[r.knob] = by[r.knob] || []).push(r);
  App.pOff = by;
  for (const [k, rows] of Object.entries(by)) {
    const st5 = rows[0].stage == null ? '' : ' in ' + rows.length + ' stage' + (rows.length > 1 ? 's' : '');
    const sig = rows.map(r => (r.stage == null ? '' : r.stage + ':') + r.score).join(',');
    const p = { fp: 'C3.PARTITURA|' + k + '|' + sig, knob: k, sv: 'warn', ly: 'C3', rule: 'C3.PARTITURA', el: rows[0].els[rows[0].els.length - 1] || null, own: 'DA_Partitura_Obra › ' + k,
      msg: `${k} is ${fmtV(rows[0].da)} s in Unreal; the score does ${[...new Set(rows.map(r => fmtV(r.score)))].join(' / ')} s${st5}.` };
    extra.push(p);
  }
}
/* where each element stands with Unreal (reach: knob / wired / cue-ready / preview), worked out once per compute() from the contract, the
   Partitura's knobs, the marks of the seed (or the score once it is bound) and the idmap of Unreal's assets. Only read: the status bar
   and the inspector show it. Logic and tests: js/reach.js */
function computeReach() {
  App.reach = null;
  if (!window.Reach || !App.contract) return;
  const sc = App.score;   // the personas are worked out only if an element needs them, always on this score
  App.reach = Reach.all(Reach.context({ score: sc, schedT: App.schedT, contract: App.contract, gov: App.gov || {}, idmap: App.idmap, seed: App.markSeed, roles: App.roles,
    resolve: p => ScoreEngine.resolve(sc, { persona: p }) }));
}
/* the score against the last Unreal run (obra/unreal/traza.json, lote 5 design A §6), Hall start → end, mark by mark.
   Checked with the typical user, like everything that is checked (C3.TRACE.*: a stage warns over 3 s; the segments are
   listed only under Problems ▸ Unreal run); the lane of the ruler shows it against the user on screen. Computed here, once
   per compute (the lane only turns it into pixels). Read-only: nothing matches the score to the run (owner decision D-4).
   Logic and tests: js/marks.js, js/calib.js */
function computeRun(extra) {
  App.run = App.runView = App.runNoise = null; App.runSeg = []; App.runLaneData = [];
  if (!App.traza || !window.Calib || !window.Marks) return;
  const info = Marks.traceInfo(App.traza); if (!info) return;
  const tm = Marks.traceMarks(App.traza, App.plive), opt = { info, live: App.plive }, mi = {};
  App.run = Calib.compare(Marks.scoreMarks(App.score, App.schedT, App.markSeed, mi), tm, opt);
  App.run.beat = mi.beat;
  // earlier runs of the same kind (speed, simulated or not), when the director keeps them: their noise raises the thresholds
  const same = (App.runHist || []).filter(t => { const i = Marks.traceInfo(t); return i && i.speed === info.speed && i.sim === info.sim; });
  App.runNoise = Calib.noise([tm, ...same.map(t => Marks.traceMarks(t, App.plive))]);
  for (const p of Calib.problems(App.run, { accepted: App.score.accepted, issues: mi.issues, noise: App.runNoise })) (p.only === 'run' ? App.runSeg : extra).push(p);
  App.runView = App.sched === App.schedT ? App.run : Calib.compare(Marks.scoreMarks(App.score, App.sched, App.markSeed), tm, opt);
  App.runLaneData = Calib.lane(App.runView, App.runAlign, { noise: App.runNoise });
}
/* earlier runs the trace lists (history: inline, or file names under obra/unreal/), at most four files */
async function loadRunHistory() {
  App.runHist = [];
  const info = App.traza && window.Marks && Marks.traceInfo(App.traza); if (!info) return;
  App.runHist = info.history.slice();
  for (const f of info.historyFiles.filter(f => /^[\w\-./]+\.json$/.test(f) && !f.includes('..')).slice(0, 4)) {
    try { const r = await fetch('/obra/unreal/' + f.replace(/^\.?\//, ''), { cache: 'no-store' }); const t = r.ok ? await r.json() : null; if (t && Array.isArray(t.fases)) App.runHist.push(t); } catch (_) {}
  }
}
/* the "Unreal run" lane: shown or not, and how it aligns (each mark on the score's, or the run as it was from the Hall start) */
function setRunLane(on) { App.runLane = !!on; savePref(); UI.renderTimeline(); }
function setRunAlign(m) { App.runAlign = m === 'hall' ? 'hall' : 'mark'; App.runLane = true; savePref(); App.runLaneData = Calib.lane(App.runView, App.runAlign, { noise: App.runNoise }); UI.renderTimeline(); }
const fmtV = v => Array.isArray(v) ? v.map(x => +(+x).toFixed(2)).join(' · ') : v == null ? '—' : String(+(+v).toFixed(2));
const knobBind = name => App.pbind && App.pbind.binds.find(b => b.knob === name);
const knobDef = name => App.pdef && App.pdef.knobs.find(k => k.name === name);
const knobLive = name => { const L = window.Partitura && Partitura.liveValues(App.plive); return L && name in L ? L[name] : (knobDef(name) || {}).initial; };
function savePref() { lsSet(LS_PREF, { persona: App.persona, pps: App.pps, who: App.who, collapsed: App.collapsed, follow: App.follow, locked: App.locked, sound: !!App.sound, inT: App.inT, outT: App.outT, snap: App.snap, lanes: App.laneSize, runLane: App.runLane, runAlign: App.runAlign, branchView: App.branchView,
  adv: !!App.adv, details: !!App.insDetails, traceOpen: !!App.traceOpen, qsSeen: !!App.qsSeen }); }
/* Simple (the default) or Advanced: only what is drawn changes, never the score, the checks or a verb. A group the user opened or closed
   keeps that choice in both; the ones Simple starts collapsed (Simple.COLLAPSED) are collapsed only until then */
const groupCollapsed = gid => Simple.collapsedFor(App.collapsed, gid, App.adv);
function setAdvanced(on) {
  App.adv = !!on; App.showAnchors = App.adv; savePref(); UI.renderAll();
  toast(App.adv ? 'Technical details on · Window ▸ Show technical details turns them off' : 'Simple view · Window ▸ Show technical details brings the Unreal details back');
}

/* ---------- edits: every change goes through here ----------
   what an edit does with its items (quiet, apply or the impact card) and what "Proceed anyway" records: js/policy.js */
/* the 3D view (its own tab, or Window ▸ 3D view) is read-only: only the transport works there, whoever asks (keys, menus,
   verbs). In Window ▸ 3D view only what finishes something already done outside the score is still recorded: a send already
   written to disk, a WAV already uploaded (review of C10) */
const view3d = () => App.view === '3d' || App.mode === 'v3d';
const FINISHES = new Set(['sent', 'audio']);
const readOnly3d = () => toast(App.view === '3d' ? 'This tab only shows the 3D view: edit in the timeline tab' : 'The 3D view only plays the piece: Window ▸ All-in-one or Timeline to edit');
function commit(label, op, mutate) {
  if (App.view === '3d' || (App.mode === 'v3d' && !FINISHES.has(op.type))) { readOnly3d(); return false; }
  if (App.cardOpen) { toast('Finish the open decision first'); return false; }
  const beforeStr = JSON.stringify(App.score);
  const next = JSON.parse(beforeStr);
  if (mutate(next) === false) return false;
  // schema 3: whatever this edit took out of the score stays in the uidMap as deleted-here (same step, same undo): a live name
  // that points to nothing is a score the server refuses to save. Any verb that deletes goes through here, so none can forget it
  Edits.reconcileUidMap(App.score, next);
  // schema 3, bound: an `el` mark of the Unreal binding hangs on one element of its moment. The element that goes takes its mark with
  // it, in this same step and undo, and the toast / card says so; and whatever else an edit might do, it never takes a bound score from
  // saveable to unsaveable without the user knowing (the save would refuse it, with no warning before)
  Edits.settleMarks(next, App.score);
  const lostMarks = Edits.marksLost(App.score, next), bindErr = next.schema === 3 ? Edits.bindError(next) : null;
  if (bindErr && !Edits.bindError(App.score)) { toast(`That would break the Unreal binding (${bindErr}): nothing changed`); UI.renderInspector(); return false; }
  // and what else would take a score that was fine to one that is not: the wait that decides SHARE / DON'T SHARE leaves (the save would refuse
  // it: S.BRANCH.FIELD), a moment starts before 0:00, the piece runs over an hour (S.TOTAL; a typed 1e9 stopped the timeline from drawing)
  const brk = Edits.wouldBreak(App.score, next, ScoreEngine, { maxTotal: window.Check ? Check.MAX_TOTAL : 3600 });
  if (brk) { toast(brk); UI.renderInspector(); return false; }
  // a locked group cannot change, whoever asks (mouse, keyboard, inspector, menus)
  const hit = Object.keys(App.score.elements).find(id => App.locked[App.score.elements[id].group] && JSON.stringify(App.score.elements[id]) !== JSON.stringify(next.elements[id]));
  if (hit) { const e = App.score.elements[hit]; toast(`${e.key} is in the locked group ${(App.score.groups.find(g => g.id === e.group) || {}).name}: unlock it first`); UI.renderInspector(); return false; }
  // nothing lands on top of another clip: what an edit pushes onto an occupied lane goes to the nearest free one
  const relocated = Edits.fixOverlaps(App.score, next, ScoreEngine, addLane);
  const schedT = ScoreEngine.resolve(next, { persona: 'typical' });
  const after = { problems: Integrity.staticProblems(next, schedT, App.contract, ScoreEngine.altRuns(next), knobCtx()) };
  const opx = Object.assign({ prevScore: App.score }, op);
  const op3 = Integrity.opItems(opx, next, { problems: App.problems }, after, App.contract, ScoreEngine, { gov: App.gov });
  const { items, repairs } = op3, ripple = [op3.ripple, Edits.marksWords(lostMarks)].filter(Boolean).join(' · ');
  const finish = extra => {
    if (JSON.stringify(App.score) !== beforeStr) { toast('The score changed while deciding: nothing applied, try again'); return; }
    App.undo.push(beforeStr); if (App.undo.length > 80) App.undo.shift(); App.redo = [];
    if (extra) extra(next);
    App.score = next; markDirty(); compute(); UI.renderAll();
    if (relocated.length) toast(`${relocated.map(m => next.elements[m.id].key).join(', ')} moved to a free lane (it would have landed on another clip)`);
    else if (ripple && !op.quietRipple) { App.lastRipple = ripple; toast(`${label} · ${ripple}`); }
  };
  const pol = Policy.decide(op, items, { label, relocated, ripple });
  if (pol.mode !== 'card') { finish(); if (pol.toast) toast(pol.toast); return true; }
  App.cardOpen = true;
  UI.impactCard(label, items, repairs, (decision, reason) => {
    App.cardOpen = false;
    if (decision === 'cancel') { UI.renderInspector(); UI.renderTimeline(); if (op.afterCard) op.afterCard(decision); return; }   // inputs go back to the value that stayed
    finish(n => { if (decision === 'anyway') n.accepted = Policy.acceptRecords(n.accepted, items, { who: App.who, reason, at: new Date().toISOString(), rev: App.baseRev }); });
    toast(Policy.doneToast(decision, ripple));
    if (op.afterCard) op.afterCard(decision);   // the panel that asked comes back on what is left (op.afterCard: Changes in guion.js)
  }, ripple);
  return true;
}
/* a decision card is open: the rest of the editor waits (A4) */
const busy = () => { if (App.cardOpen) { toast('Finish the open decision first'); return true; } if (view3d()) { readOnly3d(); return true; } return false; };
function undo() { if (busy()) return; if (!App.undo.length) return toast('Nothing to undo'); App.redo.push(JSON.stringify(App.score)); App.score = JSON.parse(App.undo.pop()); markDirty(); compute(); UI.renderAll(); }
function redo() { if (busy()) return; if (!App.redo.length) return toast('Nothing to redo'); App.undo.push(JSON.stringify(App.score)); App.score = JSON.parse(App.redo.pop()); markDirty(); compute(); UI.renderAll(); }

/* ---------- edit verbs ---------- */
const Act = {
  move(id, dt, lane, keepKids) {
    const e = App.score.elements[id]; if (!e) return;
    const newIn = lane && lane.newIn; if (newIn) lane = null;
    const relane = newIn || (lane && lane !== e.lane);
    if (Math.abs(dt) < 1e-4 && !relane) return;   // grabbed and released in place: nothing changes
    if (startNow(id) + dt < -1e-3) return toast('It would start before 0:00');
    // a lane is only how the timeline is drawn: changing it alone never touches Unreal
    const type = Math.abs(dt) < 1e-4 ? 'lane-change' : 'move';
    commit(`${type === 'move' ? 'Move' : 'Lane'} · ${e.key}${keepKids ? ' (alone)' : ''}`, { type, ids: [id], alone: !!keepKids }, n => {
      const m = Math.abs(dt) < 1e-4 ? n : Edits.move(n, id, dt, { alone: !!keepKids, ks: viewKeys() }, App.kids);
      if (m !== n) Object.assign(n, m);
      if (newIn) n.elements[id].lane = addLane(n, newIn);
      else if (lane) n.elements[id].lane = lane;
    });
  },
  // C10: several clips by the same dt, one edit, one undo step. A clip that follows another selected one (anchored to it, or
  // pushed by its moment) is not moved twice (Edits.moveMany). keepKids = Ctrl: what hangs from them and is not selected stays
  moveMany(ids, dt, keepKids) {
    if (busy()) return false;
    ids = [...new Set(ids)].filter(id => App.score.elements[id]); if (!ids.length) return false;
    if (ids.length === 1) { Act.move(ids[0], dt, null, keepKids); return true; }
    if (!Number.isFinite(dt) || Math.abs(dt) < 1e-4) return false;
    const lk = ids.map(id => App.score.elements[id]).find(e => App.locked[e.group]);
    if (lk) { toast(`${lk.key} is in a locked group: unlock it first`); return false; }
    if (Math.min(...ids.map(startNow)) + dt < -1e-3) { toast('The first of them would start before 0:00'); return false; }
    // the side on screen (schema 3): "dt later" is measured there, and a clip with its own anchor there moves that one
    return commit(`Move · ${ids.length} clips${keepKids ? ' (alone)' : ''}`, { type: 'move', ids, alone: !!keepKids }, n => {
      Object.assign(n, Edits.moveMany(n, ids, dt, { alone: !!keepKids, ks: viewKeys() }, ScoreEngine, App.kids));
    });
  },
  // C10: Ctrl+C keeps the elements and their layout (typical user) in App.clipboard; the system clipboard gets the JSON when
  // the browser lets it (never needed: paste reads App.clipboard)
  copy(ids) {
    ids = (ids || selIds()).filter(id => App.score.elements[id]);
    if (!ids.length) { toast('Select one or more clips to copy'); return false; }
    App.clipboard = Edits.clipOf(App.score, ids, ScoreEngine);
    try { const j = JSON.stringify({ veation: 'clips', rev: App.baseRev, items: App.clipboard.items }); navigator.clipboard.writeText(j).catch(() => {}); } catch (_) {}
    toast(`Copied ${keysText(App.clipboard.items.map(i => i.el.key))} · Ctrl+V pastes at the playhead`);
    return true;
  },
  // C10: Ctrl+V, at the playhead, into the moment under it (its offset measured on the timeline you are looking at, like Add)
  paste() {
    if (busy()) return false;
    const c = App.clipboard; if (!c || !c.items.length) { toast('Nothing copied yet: select clips and press Ctrl+C'); return false; }
    const b = beatAt(App.ph);
    return pasteClips(c, { beat: b, off: +Math.max(0, App.ph - App.sched.t[b][0]).toFixed(4) }, 'Paste', `at ${tc(App.ph)} in ${App.score.beats[b].key}`);
  },
  // C10: Ctrl+D, right after itself in its own moment (per moment: what is duplicated from it; an instant: 1 s later).
  // Alt+drag gives dt (each copy lands dt after its original, where the drag showed it) and the lane it was dropped on
  duplicate(ids, dt, lanes) {
    if (busy()) return false;
    ids = (ids || selIds()).filter(id => App.score.elements[id]);
    if (!ids.length) { toast('Select one or more clips to duplicate'); return false; }
    const c = Edits.clipOf(App.score, ids, ScoreEngine);
    if (dt == null) return pasteClips(c, { after: true }, 'Duplicate', `right after ${c.items.length > 1 ? 'the originals' : 'the original'}`, lanes);
    return pasteClips(c, { dt: +dt.toFixed(4) }, 'Duplicate', `${dt >= 0 ? '+' : '−'}${fmtS(Math.abs(dt))} s`, lanes);
  },
  moveBeat(bid, dt) {
    const b = App.score.beats[bid]; if (!b || !Number.isFinite(dt) || Math.abs(dt) < 1e-4) return false;
    const ids = (App.score.acts.flatMap(a => a.beats)); const prev = ids[ids.indexOf(bid) - 1];
    const own = Object.keys(App.score.elements).filter(k => App.score.elements[k].beat === bid);
    return commit(`Move moment · ${b.key}`, { type: 'move-beat', ids: own }, n => {
      const x = n.beats[bid];
      x.at = x.at || (prev ? { ref: prev, edge: 'end', off: 0 } : { ref: null, edge: 'start', off: 0 });
      x.at.off = +(x.at.off + dt).toFixed(4);   // a moment before 0:00 is refused by commit (Edits.wouldBreak): the drag stops at 0:00, the Offset field did not
    });
  },
  trim(id, dur) {
    const e = App.score.elements[id]; if (!e || !Number.isFinite(dur)) return UI.renderInspector();
    // a wait is drawn with the simulated user on screen: only the typical one says how long it is EXPECTED to take
    if (e.gate && App.persona !== 'typical') { UI.renderInspector(); return toast('Switch the simulated user to Typical to change how long this wait is expected to take'); }
    if (e.gate && dur > e.gate.fw - .1) { UI.renderInspector(); return toast(`Expected must stay below the timeout (${e.gate.fw} s): change the timeout first`); }
    commit(`Trim · ${e.key}`, { type: 'trim', ids: [id] }, n => {
      const x = n.elements[id];
      if (x.gate) x.gate.expected = +Math.max(.5, dur).toFixed(3);
      else { x.dur = { mode: 'fixed', value: +Math.max(.1, dur).toFixed(3) }; }
    });
  },
  // k ("share=no"): the offset of the anchor it has of its own in that option (alt), not the primary one
  setOffset(id, off, k) {
    const e = App.score.elements[id]; if (!e || !Number.isFinite(off)) return UI.renderInspector();
    if (Math.abs(off) > 3600) { UI.renderInspector(); return toast('More than an hour away from its anchor: type a smaller offset'); }
    const alt = k && e.alt && e.alt[k] && e.alt[k].at;
    if (k && !alt) return UI.renderInspector();
    const cur = (alt ? alt.off : e.at && e.at.off) || 0;
    // an offset changes the time in the option whose anchor it is (an alternative: that side; the primary one: the default option
    // and, with the primary one on screen, the side shown)
    const now = alt ? timeIn(k).t[id][0] : Math.min(App.schedT.t[id][0], App.schedV.t[id][0]);
    if (now + (off - cur) < -1e-3) { UI.renderInspector(); return toast('It would start before 0:00'); }
    commit(`Move · ${e.key}${alt ? ' in ' + Edits.optionLabel(App.score, k) : ''}`, { type: 'offset', ids: [id] }, n => {
      const x = n.elements[id];
      if (alt) x.alt[k].at.off = +off; else { x.at = x.at || { ref: x.beat, edge: 'start', off: 0 }; x.at.off = +off; }
    });
  },
  setGate(id, field, v) {
    const e = App.score.elements[id]; if (!e || !e.gate || !Number.isFinite(v)) return UI.renderInspector();
    if (v > 3600) { UI.renderInspector(); return toast('More than an hour: type a smaller time'); }   // as the offset below: a wait is seconds, not hours
    if (field === 'fw' && v < e.gate.expected + .1) { UI.renderInspector(); return toast(`The timeout must be longer than the expected time (${e.gate.expected} s)`); }
    if (field === 'expected' && (v < .5 || v > e.gate.fw - .1)) { UI.renderInspector(); return toast(`Expected goes between 0.5 s and the timeout (${e.gate.fw} s)`); }
    // expected is the simulated user (never reaches Unreal); the timeout is the real knob
    commit(`Wait · ${e.key} · ${field === 'fw' ? 'timeout' : 'expected'}`, { type: field === 'fw' ? 'gate' : 'sim', ids: [id] }, n => { n.elements[id].gate[field] = +v; });
  },
  /* "Waits for the user (as in Unreal)" (schema 3, design B §6.2): does the stage stop at this wait, or run on its own clock and
     let the user only decide the help line and what hangs from the end of the wait. Op 'gate' (what: 'blocking'): integrity
     judges it against what Unreal does (C3.BLOCKING, and C2.WAIT.WHERE inside a stage), the card says so */
  setBlocking(id, blocking) {
    const e = App.score.elements[id]; if (!e || !e.gate) return UI.renderInspector();
    if (App.score.schema < 3) { UI.renderInspector(); return toast('A schema 2 score cannot say it: upgrade it first (Problems ▸ Upgrade…)'); }
    blocking = !!blocking;
    if ((e.gate.blocking !== false) === blocking) return UI.renderInspector();
    const was = App.score;
    if (commit(`Wait · ${e.key} · ${blocking ? 'waits for the user' : 'runs on the stage clock'}`, { type: 'gate', what: 'blocking', ids: [id] }, n => { n.elements[id].gate.blocking = blocking; }) === false) return UI.renderInspector();
    // the typical user lives the same either way (the card's ripple stays quiet): say what changes for the slow and the idle ones
    if (!App.cardOpen && App.score !== was) {
      const d = ['slow', 'idle'].map(k => [ScoreEngine.PERSONAS[k].name, ScoreEngine.resolve(was, { persona: k }).total, ScoreEngine.resolve(App.score, { persona: k }).total]).filter(x => Math.abs(x[2] - x[1]) > .05);
      toast(`${e.key} ${blocking ? 'waits for the user' : 'runs on the stage clock'}` + (d.length ? ' · ' + d.map(x => `${x[0]} ${Integrity.fmt(x[1])} → ${Integrity.fmt(x[2])}`).join(' · ') + ' (Typical does not change)' : ' · no simulated user changes'));
    }
  },
  setText(id, text) {
    const e = App.score.elements[id]; if (!e) return;
    // a recorded voice keeps its length (the APK plays the recording); only a new line is re-estimated from its words
    commit(`Text · ${e.key}`, { type: 'text', ids: [id] }, n => { const x = n.elements[id]; x.text = text; if (x.type === 'vo' && x.isNew && !(x.audio && x.audio.dur)) x.dur = { mode: 'audio', value: +voDur(text).toFixed(4) }; });
  },
  setLane(id, lane) {
    const e = App.score.elements[id]; if (!e || lane === e.lane) return;
    const [s, en] = App.schedT.t[id];
    if (laneBusy(lane, s, en, new Set([id]))) { toast('Occupied: that lane already has something there. Pick another lane or create one.'); UI.renderInspector(); return; }
    commit(`Lane · ${e.key}`, { type: 'lane-change', ids: [id] }, n => { n.elements[id].lane = lane; });
  },
  remove(ids) {
    if (busy()) return;
    ids = ids.filter(id => App.score.elements[id]); if (!ids.length) return;
    const lockedOne = ids.map(id => App.score.elements[id]).find(e => App.locked[e.group]);
    if (lockedOne) return toast(`${lockedOne.key} is in a locked group: unlock it first`);
    // the wait that decides SHARE / DON'T SHARE is not deleted: the decision would be left with nothing to decide it
    const gate = Edits.branchGates(App.score, ids)[0];
    if (gate) return toast(`${gate.key} is the wait that decides "${gate.name}": the piece needs it, so it cannot be deleted`);
    const keys = keysText(ids.map(id => App.score.elements[id].key)), many = ids.length > 1;
    const plan = Edits.planDelete(App.score, ids, ScoreEngine);
    const go = (variant, label) => {
      const removed = {}; variant.ids.forEach(id => removed[id] = App.score.elements[id]);
      commit(label, { type: 'delete', ids: variant.ids, removed, repaired: true }, n => { for (const k of Object.keys(n)) delete n[k]; Object.assign(n, JSON.parse(JSON.stringify(variant.next))); });
      if (!App.score.elements[App.sel]) select(null);
    };
    if (!plan) {   // nothing hangs from it
      const del = () => {
        const removed = {}; ids.forEach(id => removed[id] = App.score.elements[id]);
        commit(`Delete · ${keys}`, { type: 'delete', ids, removed }, n => { ids.forEach(id => delete n.elements[id]); });
        if (!App.score.elements[App.sel]) select(null);
      };
      // a bound score: the Unreal mark of a moment can be the edge of this very clip (ENV_SWAP is S1.OPEN): it goes with the clip, so say it BEFORE
      const lost = Edits.marksOf(App.score, ids);
      if (!lost.length) return del();
      UI.chooseCard(`Delete · ${keys}`, `${Edits.marksWords(lost)}: the mark is the edge of ${many ? 'one of them' : 'this clip'}, so it goes with ${many ? 'it' : 'the clip'}. Nothing else changes: no time moves.`, [
        { id: 'go', primary: true, danger: true, label: many ? `Delete these ${ids.length}` : 'Delete it', detail: 'Ctrl+Z brings the clip and its Unreal mark back.' }], c => { if (c === 'go') del(); });
      return;
    }
    // something hangs from it: show what each way really does, BEFORE choosing (B3)
    const S = App.score, nm = id => S.beats[id] ? 'moment ' + S.beats[id].key : (S.elements[id] || {}).key;
    const tot = (a, b) => { const d = b - a; return Math.abs(d) < .05 ? 'The total does not change.' : `The piece gets ${d > 0 ? 'longer' : 'shorter'}: ${d > 0 ? '+' : ''}${d.toFixed(1)} s.`; };
    const pl = (n, one, many) => n + ' ' + (n === 1 ? one : many);
    const A = plan.reanchor, B = plan.family, helps = Object.keys(S.elements).filter(k => ids.includes(S.elements[k].help));
    const list = plan.direct.slice(0, 5).map(nm).join(', ') + (plan.direct.length > 5 ? '…' : ''), one = plan.direct.length === 1;
    // several deleted: what hangs from them keeps its place among what is left, so an earlier deletion can still move it
    const drift = (A.drift || []).filter(k => !ids.includes(k)), hang = `${list} ${one ? 'hangs' : 'hang'} from ${many ? 'them' : 'it'}`;
    const stays = !drift.length ? `${hang} and ${one ? 'stays where it is' : 'stay where they are'}`
      : drift.length === plan.direct.length ? `${hang} and ${one ? 'keeps its' : 'keep their'} place relative to what is left, so ${one ? 'it moves' : 'they move'} too`
      : `${hang} and keep their place relative to what is left: ${keysText(drift.map(nm))} ${drift.length === 1 ? 'moves' : 'move'} too, the rest stay where they are`;
    const opts = [
      { id: 'reanchor', primary: true, disabled: !A.ok, label: many ? `Delete only these ${ids.length}` : 'Delete only it',
        detail: A.ok ? `${stays}. ${A.moved ? pl(A.moved, 'item moves', 'items move') + ' because a moment gets shorter or longer. ' : ''}${tot(A.total0, A.total1)}${helps.length ? ' ' + helps.map(nm).join(', ') + (helps.length > 1 ? ' stop being help lines.' : ' stops being a help line.') : ''}${A.marks.length ? ' ' + Edits.marksWords(A.marks) + '.' : ''}`
          : 'Not possible: something would be left without an anchor.' },
    ];
    if (B.deleted > ids.length) opts.push({ id: 'family', danger: true, disabled: !B.ok, label: `Delete ${many ? 'them' : 'it'} and ${pl(B.deleted - ids.length, 'element', 'elements')} that ${B.deleted - ids.length === 1 ? 'hangs' : 'hang'} from ${many ? 'them' : 'it'}`,
      detail: B.gates.length ? `Not possible: it would also delete ${B.gates[0].key}, the wait that decides "${B.gates[0].name}".`
        : `Deletes ${pl(B.deleted, 'element', 'elements')} in all.${plan.anchoredMoments.length ? ' ' + plan.anchoredMoments.map(nm).join(', ') + (plan.anchoredMoments.length > 1 ? ' stay' : ' stays') + ' (a moment is never deleted).' : ''} ${tot(B.total0, B.total1)}${B.marks.length ? ' ' + Edits.marksWords(B.marks) + '.' : ''}` });
    UI.chooseCard(`Delete · ${keys}`, `Something hangs from ${many ? 'them' : 'it'}. Choose what happens to it; the next step still warns about Unreal.`, opts, choice => {
      if (choice === 'reanchor') go(A, `Delete · ${keys}`);
      else if (choice === 'family') go(B, `Delete · ${keys} and ${B.deleted - ids.length} more`);
    });
  },
  // a locked group protects its lanes too: a new, renamed or deleted lane is a change to it (what the lock button says: "protects it from edits")
  newLane(gid, after) {
    const g = App.score.groups.find(x => x.id === gid); if (!g) return null;
    if (App.locked[gid]) { toast(`${g.name} is locked: unlock it first`); return null; }
    let id = null;
    commit(`New lane · ${g.name}`, { type: 'lane-new', ids: [] }, n => { id = addLane(n, gid, after); });
    return id;
  },
  renameLane(lid, name) {
    name = String(name || '').trim(); if (!name || !App.score.lanes[lid] || App.score.lanes[lid].name === name) return UI.renderTimeline();
    const g = App.score.groups.find(x => x.lanes.includes(lid));
    if (g && App.locked[g.id]) { toast(`${g.name} is locked: unlock it first`); return UI.renderTimeline(); }
    commit('Rename lane', { type: 'lane-rename', ids: [] }, n => { n.lanes[lid].name = name; });
  },
  deleteLane(lid) {
    const used = Object.values(App.score.elements).some(e => e.lane === lid);
    if (used) return toast('Only empty lanes can be deleted. Move or delete its elements first.');
    const g = App.score.groups.find(x => x.lanes.includes(lid));
    if (g && App.locked[g.id]) return toast(`${g.name} is locked: unlock it first`);
    if (g && g.lanes.length < 2) return toast('A group keeps at least one lane.');
    commit('Delete lane', { type: 'lane-delete', ids: [] }, n => { const gg = n.groups.find(x => x.lanes.includes(lid)); gg.lanes = gg.lanes.filter(x => x !== lid); delete n.lanes[lid]; });
  },
  add(kind, extra) {
    const t = App.ph, bid = beatAt(t), bs = App.sched.t[bid][0];   // offset inside the moment, on the timeline you are looking at
    const spec = {
      vo: { group: 'vo', type: 'vo', key: uniqueKey('VO_NEW'), label: 'New line', text: 'New line…', isNew: true, dur: { mode: 'audio', value: +voDur('New line…').toFixed(4) } },
      sound: { group: 'fx', type: 'sound', key: extra && extra.sound || uniqueKey('FX_NEW_SOUND'), label: extra && extra.sound || 'FX_NEW_SOUND', sound: extra && extra.sound || null, isNew: !(extra && extra.sound), dur: { mode: 'instant', value: 0 } },
      wait: { group: 'int', type: 'wait', key: uniqueKey('G_NEW'), label: 'New wait', isNew: true, gate: Object.assign({ expected: 6, fw: 25 }, App.score.schema >= 3 ? { blocking: true } : {}), dur: { mode: 'elastic', value: 6 } },
    }[kind];
    if (!spec) return;
    const len = spec.gate ? spec.gate.expected : spec.dur.value || .05;
    const lane = freeLane(spec.group, t, t + Math.max(len, .05));
    const id = 'el_n' + Date.now().toString(36);
    let laneId = lane;
    const ok = commit(`Add · ${spec.key}`, { type: 'add', ids: [id] }, n => {
      if (!laneId) laneId = addLane(n, spec.group);
      n.elements[id] = Object.assign({ beat: bid, lane: laneId, at: { ref: bid, edge: 'start', off: +(t - bs).toFixed(4) }, end: null, text: null, sound: null, note: null, gate: null, help: null, simOnly: false, when: null, hint: null, ghost: null, legacy: null, by: App.who, created: new Date().toISOString() }, spec);
    });
    if (!ok || !App.score.elements[id]) return;   // refused (a card is open, the 3D view): nothing to select
    UI.goto(id);   // selected and shown: the playhead may be out of sight, or the group collapsed
    const T = App.schedT.t; if (T[id] && T[id][0] > T[bid][1] + .05) toast(`With the typical user this lands after moment ${App.score.beats[bid].key} ends`);
  },
  rename(id, name) {
    const e = App.score.elements[id]; if (!e || !name || name === e.key) return UI.renderInspector();
    // names are unique; going back to the name Unreal knows it by (T_IN is in every stage) only has to be unique in its moment
    const back = name === Integrity.knownKey(id, App.contract);
    if (Object.values(App.score.elements).some(x => x !== e && x.key === name && (!back || x.beat === e.beat))) { toast(name + ' already exists'); return UI.renderInspector(); }
    // the WAV in the inbox is named by the element id, so a rename (and its undo) never touches the disk. The name only: what
    // Unreal plays (sound, bind.asset) stays (Edits.renameEl); it is judged like any edit (on.rename of the contract)
    commit(`Rename · ${e.key}`, { type: 'rename', ids: [id] }, n => { Edits.renameEl(n.elements[id], name); });
  },
  // Reopen never deletes the record: it stays (state 'reopened', one more entry in its history), so what was decided is never lost
  reopen(fp) {
    commit('Reopen problem', { type: 'reopen', ids: [] }, n => {
      const r = Policy.reopen(n.accepted, fp, { who: App.who, at: new Date().toISOString() });
      if (r === n.accepted) return false;
      n.accepted = r;
    });
  },
  // the accepted records of elements that are no longer in the score stay visible ("element deleted") until this is asked for
  cleanAccepted() {
    const n0 = Policy.cleanRecords(App.score.accepted, App.score).removed.length;
    if (!n0) return toast('No accepted problem belongs to something that was deleted');
    commit(`Clean up accepted · ${n0} record${n0 > 1 ? 's' : ''}`, { type: 'accepted-clean', ids: [] }, n => {
      const r = Policy.cleanRecords(n.accepted, n); if (!r.removed.length) return false;
      n.accepted = r.next;
    });
  },
  // bring the score to what Unreal does for one knob (stage K, or every stage): the score follows the DA
  syncKnob(name, stage) {
    const b = knobBind(name); if (!b) return;
    const v = knobLive(name); let res = null;
    commit(`Match Unreal · ${name}`, { type: 'sync', ids: [] }, n => { res = Partitura.apply(n, ScoreEngine, App.pbind, b, v, stage); if (!res.changed.length) return false; });
    if (res && !res.changed.length) toast(res.skipped.length ? 'Nothing to change: ' + res.skipped[0].why : `The score already does what Unreal does for ${name}`);
  },
  syncAll() {
    if (!App.pbind) return; let n0 = 0, sk = 0;
    commit('Match Unreal timing', { type: 'sync', ids: [] }, n => {
      for (const b of App.pbind.binds) { const r = Partitura.apply(n, ScoreEngine, App.pbind, b, knobLive(b.knob), null); n0 += r.changed.length; sk += r.skipped.length; }
      if (!n0) return false;
    });
    toast(n0 ? `${n0} values now match DA_Partitura_Obra${sk ? ` · ${sk} have no counterpart in the score` : ''}` : 'The score already matches Unreal');
  },
  // a change for Unreal WAITS in the score (undoable, saved with Ctrl+S). Nothing reaches Unreal until "Send to Unreal".
  propose(name, stage, value, reason) {
    const d = knobDef(name); if (!d || !isFinite(value) || value < 0) return toast('Not a valid value');
    if (String(reason || '').trim().length < 12) return toast('Write why (12+ characters): it travels with the change');
    const live = knobLive(name), v = +(+value).toFixed(3);
    commit(`For Unreal · ${name}`, { type: 'propose', ids: [] }, n => {
      const P = n.propuestas = n.propuestas || { valores: {}, motivos: {} };
      if (!P.base && App.plive) P.base = App.plive.hash;   // the Unreal export these changes were prepared on
      let nv = v;
      if (d.type === 'a5') { nv = (P.valores[name] || live).slice(); if (stage == null) nv = nv.map(() => v); else nv[stage] = v; }
      if (JSON.stringify(nv) === JSON.stringify(live)) { delete P.valores[name]; delete P.motivos[name]; return; }
      P.valores[name] = nv;
      P.motivos[name] = { por: App.who, motivo: String(reason).trim(), antes: live, cuando: new Date().toISOString() };
    });
    toast(`${name}${d.type === 'a5' && stage != null ? ' [' + App.pdef.stages[stage] + ']' : ''} = ${v} s · waiting to be sent (Send to Unreal)`);
  },
  unpropose(name) {
    if (!pendingVals()[name]) return;
    commit(`For Unreal · remove ${name}`, { type: 'propose', ids: [] }, n => { delete n.propuestas.valores[name]; delete n.propuestas.motivos[name]; });
  },
  // the ONLY door to Unreal: a review card first; the file is written only if you confirm
  sendToUnreal() {
    const pend = pendingVals(), names = Object.keys(pend);
    if (!names.length) return toast('Nothing waiting for Unreal: add changes from a knob (Timing tab)');
    const live = (window.Partitura && Partitura.liveValues(App.plive)) || {};
    const prevWaiting = App.prop && App.prop.estado === 'enviada' ? App.prop : null;
    const merged = Object.assign({}, prevWaiting ? prevWaiting.valores : {}, pend);
    const vals = Object.assign({}, live, merged); vals.__changed = new Set(Object.keys(merged));
    const checks = Partitura.checks(vals, live, App.pdef);
    UI.sendCard({ names: Object.keys(merged), pend: merged, live, motivos: Object.assign({}, prevWaiting ? prevWaiting.motivos : {}, App.score.propuestas.motivos), checks, prevWaiting,
      stale: App.plive && App.score.propuestas.base && App.score.propuestas.base !== App.plive.hash }, () => doSend(merged, prevWaiting));
  },
  // stage the values Unreal had before the last applied change (it still needs Send)
  stageUndoInUnreal() {
    const r = App.prop && App.prop.estado === 'aplicada' && App.prop.respaldo; if (!r) return;
    commit('For Unreal · undo the last applied change', { type: 'propose', ids: [] }, n => {
      const P = n.propuestas = n.propuestas || { valores: {}, motivos: {} };
      for (const [k, v] of Object.entries(r)) { P.valores[k] = v; P.motivos[k] = { por: App.who, motivo: 'undo of the change applied ' + (App.prop.aplicado || ''), antes: knobLive(k), cuando: new Date().toISOString() }; }
    });
    toast('The previous values are waiting to be sent · Send to Unreal');
  },
  // C2.VO.REAL: each voice lasts what its recording in the final mix lasts (Unreal: the voice, then its own pause knob)
  useRealLengths(ids) {
    if (busy()) return;
    const gaps = (App.voiceGaps || []).filter(g => !ids || ids.includes(g.id)); if (!gaps.length) return toast('Every voice already lasts its recording');
    const apply = n => { for (const g of gaps) { const x = n.elements[g.id]; const m = mixOf(x); x.dur = { mode: 'audio', value: +m.dur.toFixed(4) }; x.audio = { dur: +m.dur.toFixed(4), file: m.file, src: 'mix' }; } };
    const S0 = App.score, T0 = ScoreEngine.resolve(S0, { persona: 'typical' }), probe = JSON.parse(JSON.stringify(S0)); apply(probe);
    const T1 = ScoreEngine.resolve(probe, { persona: 'typical' }), ef = Integrity.effect(App.score, probe, ScoreEngine), rip = Integrity.rippleLine(ef);
    const one = gaps.length === 1, g0 = gaps[0];
    const list = gaps.slice().sort((a, b) => Math.abs(b.real - b.now) - Math.abs(a.real - a.now)).slice(0, 4).map(g => `${g.key} ${fmtS(g.now)} → ${fmtS(g.real)} s`).join(' · ');
    UI.chooseCard(one ? `Real length · ${g0.key}` : `Real voice lengths · ${gaps.length} voices`,
      `In Unreal a voice lasts what its recording lasts, and the pause after it is its own knob. Here ${one ? 'it was' : 'they were'} estimated from the words. ${one ? '' : 'Largest: ' + list + '.'}`, [
        { id: 'go', primary: true, label: one ? `Use the recording: ${fmtS(g0.real)} s` : `Use the recordings (${gaps.length} voices)`,
          detail: `${rip || 'Nothing else moves'}. What follows each voice moves with it, as in the APK, so the APK baseline moves too (it was measured with the estimates). Undo takes it back.` },
      ], c => {
        if (c !== 'go') return;
        commit(one ? `Real length · ${g0.key}` : 'Real voice lengths', { type: 'trim', ids: gaps.map(g => g.id), quietRipple: false }, n => {
          apply(n);
          // the baseline of "≠ APK" was the prototype with estimated voices: shift it by exactly what this change shifts
          // (schema 3: score.baseline, relative to each moment; schema 2: score.golden, absolute times)
          const rec = { at: new Date().toISOString(), by: App.who, ids: gaps.map(g => g.id), src: 'final mix' };
          if (n.baseline && n.baseline.rel) n.baseline = Edits.shiftBaseline(n.baseline, { score: S0, sched: T0 }, { score: n, sched: T1 }, null, Object.assign({ op: 'voices' }, rec));
          else if (n.golden && n.golden.times) n.golden = Edits.shiftGolden(n.golden, T0, T1, rec);
        });
      });
  },
  // C3.DRIFT: the timeout takes the value Unreal has
  matchTimeout(id) {
    const e = App.score.elements[id]; if (!e || !e.gate) return;
    const c = Integrity.contractFor(id, e, App.contract).find(x => x.kind === 'knob' && x.knob); if (!c) return;
    Act.setGate(id, 'fw', c.knob.value);
  },
  // C3.KNOB.OFFSET (lote 5 design B §6.3): a time that IS an Unreal knob counted from another element (VO_11h plays HelpAfter seconds
  // after VO_11b ends). It takes the anchor Unreal has (`ref.edge + knob`, with `at.knob`) in the moment of the element it counts
  // from, and the ≠ APK reference moves for it alone. A card first, with what changes for each simulated user measured now; then ONE
  // undoable edit that the user saves himself. Nothing else is touched.
  matchKnobAnchor(id) {
    if (busy()) return false;
    const S = App.score, e = S.elements[id]; if (!e) return false;
    if (App.locked[e.group]) { toast(`${e.key} is in a locked group: unlock it first`); return false; }
    const c = Integrity.contractFor(id, e, App.contract).find(x => x.kind === 'knob' && x.anchor && x.knob);
    const k = c && Integrity.knobOffset(S, App.schedT, id, c, App.contract, knobCtx());
    if (!k) { toast('Nothing to match: Unreal does not count this one from a knob'); return false; }
    if (k.ok) { toast(`${e.key} already plays ${+(+k.value).toFixed(2)} s after ${S.elements[k.refId].key}`); return false; }
    const spec = () => ({ ref: k.refId, edge: k.edge, off: k.value, knob: k.name, at: new Date().toISOString(), by: App.who });
    const m = Edits.matchKnobAnchor(S, id, spec(), ScoreEngine);
    if (!m.ok) { toast(m.why); return false; }
    const U = m.users, order = ['fast', 'typical', 'slow', 'idle'], who = p => ScoreEngine.PERSONAS[p].name, rk = S.elements[k.refId].key;
    const knob = k.name.replace(/^[^.]*\./, ''), owner = k.name.split('.')[0], clk = Integrity.clock;
    const flips = order.filter(p => U[p].help0 != null && U[p].help0 !== U[p].help1)
      .map(p => `The ${who(p).toLowerCase()} user ${U[p].help1 ? 'now hears' : 'no longer hears'} it (they act at ${fmtS(U[p].acts)} s; it comes at ${fmtS(U[p].comes)} s).`);
    const dT = order.filter(p => Math.abs(U[p].total1 - U[p].total0) > .05).map(p => `${who(p)} ${clk(U[p].total0)} → ${clk(U[p].total1)}`);
    const body = [`${e.key} now plays ${+(+k.value).toFixed(2)} s after ${rk} ${k.edge === 'start' ? 'starts' : 'ends'} (${knob} in ${owner}), as in Unreal: ${clk(m.t0)} → ${clk(m.t1)}. ${m.moved.length ? `${m.moved.length} other item${m.moved.length > 1 ? 's' : ''} move${m.moved.length > 1 ? '' : 's'} with it.` : 'Nothing else moves.'} ${flips.join(' ')}`.trim(),
      dT.length ? `The total changes for ${dT.join(' · ')}.` : 'The total does not change for any simulated user.',
      `Counting ${knob} from the ${k.edge === 'start' ? 'START' : 'END'} of ${rk} is the current reading of the Unreal tracker (${String(c.ev || '').split(' · ')[0]}), pending the Director's confirmation. If Unreal counts it another way, Undo returns it.`].join('\n\n');
    UI.chooseCard(`Match Unreal · ${e.key}`, body, [
      { id: 'go', primary: true, label: `Move ${e.key} to ${clk(m.t1)}`, detail: `It hangs from ${rk} ${k.edge === 'start' ? 'start' : 'end'} + ${+(+k.value).toFixed(2)} s and moves to its moment. The APK baseline moves for ${e.key} alone, so it is not marked ≠ APK. Ctrl+Z returns it; nothing is saved until you press Ctrl+S.` },
    ], ch => {
      if (ch !== 'go') return;
      // measured again on the score that is there when it is applied (the card blocks edits, so it is the same one)
      const ok = commit(`Match Unreal · ${e.key}`, { type: 'sync', ids: [] }, n => {
        const r = Edits.matchKnobAnchor(n, id, spec(), ScoreEngine);
        if (!r.ok) { toast(r.why); return false; }
        for (const key of Object.keys(n)) delete n[key];
        Object.assign(n, r.next);
      });
      if (ok) toast(`${e.key} now plays ${clk(m.t1)}, ${+(+k.value).toFixed(2)} s after ${rk} ${k.edge === 'start' ? 'starts' : 'ends'} · save with Ctrl+S`);
    });
    return true;
  },
  // C2.WAIT.NOHELP: a help line the slow user hears before the timeout (a new line: words now, recording later)
  addHelp(waitId) {
    const w = App.score.elements[waitId]; if (!w || !w.gate) return;
    const off = +Math.max(1, Math.min(w.gate.fw - 4, w.gate.expected + 4)).toFixed(2), id = 'el_n' + Date.now().toString(36);
    const T = App.schedT.t, s0 = T[waitId][0] + off, lane = freeLane('vo', s0, s0 + 3);
    const ok = commit(`Help line · ${w.key}`, { type: 'add', ids: [id] }, n => {
      const ln = lane || addLane(n, 'vo');
      n.elements[id] = { key: uniqueKey(w.key.replace(/^G_/, 'VO_') + '_HELP'), type: 'vo', group: 'vo', beat: w.beat, lane: ln, at: { ref: waitId, edge: 'start', off }, end: null,
        dur: { mode: 'audio', value: +voDur('Help line for this wait…').toFixed(4) }, label: 'Help line', text: 'Help line for this wait…', help: waitId, isNew: true, by: App.who, created: new Date().toISOString(),
        sound: null, note: null, gate: null, simOnly: false, when: null, hint: null, ghost: null, legacy: null };
    });
    if (!ok || !App.score.elements[id]) return;   // refused (a card is open, the 3D view)
    UI.goto(id); toast(`Help line ${off} s after ${w.key} starts (before its ${w.gate.fw} s timeout) · write its words in the inspector`);   // shown: it is far from the playhead and from the Problems list that asked
  },
  // C1.ANCHOR.CYCLE: two honest ways out, with their effect, before choosing
  breakLoop(beatId) {
    if (busy()) return;
    const p = Edits.planLoop(App.score, beatId, ScoreEngine); if (!p) return toast('Nothing to fix here');
    const S = App.score, b = S.beats[beatId].key, nb = S.beats[p.next].key, d = x => { const v = x.total1 - x.total0; return Math.abs(v) < .05 ? 'the total does not change' : `total ${Integrity.fmt(x.total0)} → ${Integrity.fmt(x.total1)}`; };
    UI.chooseCard(`Anchor loop in moment ${b}`, `The end of ${b} depends on something in ${nb}, so ${nb} starts together with ${b}. The prototype does the same. Choose how it should be:`, [
      { id: 'keep', primary: true, disabled: !p.keep.ok, label: `${nb} starts together with ${b}, as now`, detail: 'Nothing moves; the loop is gone.' },
      { id: 'order', disabled: !p.order.ok, label: `${nb} starts when ${b} ends, as the script reads`, detail: `${p.order.pinned.map(id => S.elements[id].key).join(', ')} stay where they are inside ${b}. ${nb} moves from ${tc(p.order.nextStart0)} to ${tc(p.order.nextStart1)}; everything after follows: ${d(p.order)}.` },
    ], c => {
      const v = c === 'keep' ? p.keep.next : p.order.next;
      commit(`Anchor loop · ${b}`, { type: 'sync', ids: [] }, n => { for (const k of Object.keys(n)) delete n[k]; Object.assign(n, JSON.parse(JSON.stringify(v))); });
    });
  },
  // C1.SCHEMA: the upgrade to schema 3 (Edits.migrate3: SHARE branches, waits that run on the stage clock, stable names, the APK
  // baseline inside the score). Never automatic: a card with numbers measured here, now, and then ONE undoable edit that the
  // user saves himself. If it cannot promise that nothing moves for the typical user, the card says why and offers nothing
  upgradeSchema() {
    if (busy()) return;
    const S = App.score; if (S.schema !== 2) return toast(`This score is already schema ${S.schema}`);
    const ctx = () => ({ who: App.who, gov: App.gov }), r = Edits.migrate3(S, ScoreEngine, App.contract, ctx());
    if (!r.next) {
      UI.chooseCard('The score cannot be upgraded yet', `The upgrade changes no time and guesses nothing, so it stopped:\n${r.report.refusals.map(x => '• ' + x.msg).join('\n')}`, [], () => {}, 'Close');
      return;
    }
    // a locked group cannot change, even by this
    const lockedHit = Object.keys(S.elements).filter(id => App.locked[S.elements[id].group] && JSON.stringify(S.elements[id]) !== JSON.stringify(r.next.elements[id]));
    if (lockedHit.length) { const e = S.elements[lockedHit[0]]; return toast(`${e.key} is in the locked group ${(S.groups.find(g => g.id === e.group) || {}).name}: unlock it first (the upgrade changes ${lockedHit.length} element${lockedHit.length > 1 ? 's' : ''} there)`); }
    const rep = r.report, T = rep.totals, clk = t => { const q = Math.round(t * 10), m = Math.floor(q / 600), s = (q - m * 600) / 10; return `${m}:${s < 10 ? '0' : ''}${s.toFixed(1)}`; };
    const list = a => a.length < 2 ? a.join('') : a.slice(0, -1).join(', ') + ' and ' + a[a.length - 1];
    const who = p => ScoreEngine.PERSONAS[p].name, others = ['fast', 'slow', 'idle'], moves = p => Math.abs(T[p].view - T[p].today) > .05;
    const users = others.filter(moves).map(p => `${who(p)} ${clk(T[p].today)} → ${clk(T[p].view)}`).concat(others.filter(p => !moves(p)).map(p => `${who(p)} stays ${clk(T[p].today)}`)).join(' · ');
    const lab = o => ((Edits.MIGRATE3.branch.def.options[o] || {}).label || o);
    const alt = rep.branch.alt.map(a => `${a.key} gets its own anchor in ${lab(a.option.split('=')[1])} (${a.twin ? 'after ' + a.to + ', as today' : 'from ' + a.to + ', at the time it has today'})`);
    const body = [`The score learns three things Unreal already does. Nothing moves for the typical user (${clk(T.typical.today)}).`,
      `Waits: ${list(rep.waits.blocking)} wait for the user, as in Unreal. ${list(rep.waits.stageClock)} run on the stage clock: a slower user only decides whether the help line plays. ${users}.`,
      `SHARE and DON'T SHARE: ${rep.branch.elements} elements now belong to their side (${rep.branch.share} SHARE, ${rep.branch.no} DON'T SHARE)${alt.length ? ' and ' + list(alt) : ''}. The timeline shows SHARE; DON'T SHARE runs ${fmtS(T.typical.share - T.typical.no)} s shorter.`,
      `Stable names: the ${rep.names.elements} prototype elements and ${rep.names.moments} moments keep their ids for good, so a new guion.js can't rename an element or give its id to another clip.`,
      `APK baseline: the prototype schedule stored in the score becomes the APK baseline. ≠ APK marks: ${rep.baseline.apk.before} → ${rep.baseline.apk.after}.`]
      .concat(rep.accepted.n ? [`Accepted problems: ${rep.accepted.n} record${rep.accepted.n > 1 ? 's' : ''} stay and now carry the value they were accepted at${rep.accepted.n > rep.accepted.withValue ? ` (${rep.accepted.n - rep.accepted.withValue} without one: the card that accepted ${rep.accepted.n - rep.accepted.withValue > 1 ? 'them' : 'it'} did not keep it)` : ''}.`] : [])
      .concat(rep.notes.map(n => 'Note: ' + n))
      .concat([`Other open editor tabs must reload after you save: an older editor can't save over a schema 3 score.`]).join('\n\n');
    UI.chooseCard('Upgrade the score to schema 3', body, [
      { id: 'go', primary: true, label: 'Upgrade (you can undo it)', detail: 'Ctrl+Z returns the score exactly as it is now. Nothing is saved until you press Ctrl+S.' },
    ], c => {
      if (c !== 'go') return;
      // measured again on the score that is there when it is applied (the card blocks edits, so it is the same one)
      const ok = commit('Upgrade to schema 3', { type: 'migrate', ids: [] }, n => {
        const m = Edits.migrate3(n, ScoreEngine, App.contract, ctx());
        if (!m.next) { toast('The upgrade stopped: ' + m.report.refusals[0].msg); return false; }
        for (const k of Object.keys(n)) delete n[k];
        Object.assign(n, m.next);
      });
      if (ok) toast('Upgraded to schema 3 · nothing moved for the typical user · save with Ctrl+S');
    }, 'Not now');
  },
  // lote 5 (design A §3.6): "Bind to Unreal", the optional step after the upgrade: the Unreal mark of every moment and the Unreal
  // asset / action / target of every element (Edits.bindUnreal). Like the upgrade: the owner's button, a card with numbers measured
  // here, now, and ONE undoable edit that the user saves himself. It adds `marks` and `bind` and nothing else; if any time would move
  // it refuses itself. The menu entry (Experience ▸ Bind to Unreal…) asks bindStatus for its hint and whether it is available
  bindStatus() {
    const st = Edits.bindState(App.score);
    if (st === 'needs3') return { can: false, hint: 'Upgrade to schema 3 first' };
    if (st === 'bound') return { can: false, hint: 'Already bound' };
    if (!App.markSeed) return { can: false, hint: 'No marks seed' };
    if (!App.idmap) return { can: false, hint: 'No Unreal assets scan' };
    return { can: true, hint: 'marks and assets' };
  },
  bindUnreal() {
    if (busy()) return;
    const S = App.score, st = Act.bindStatus();
    if (!st.can) return toast(st.hint === 'Upgrade to schema 3 first' ? 'Upgrade the score to schema 3 first (Problems ▸ Upgrade…): only then can it carry marks and assets'
      : st.hint === 'Already bound' ? 'This score is already bound to Unreal' : st.hint === 'No marks seed' ? 'obra/score/seed/marks-v1.json is not there: it says which Unreal mark each moment corresponds to' : 'obra/unreal/idmap.json is not there: make it with node tools/score/idmap.mjs');
    const ctx = () => ({ gov: App.gov, Engine: ScoreEngine }), r = Edits.bindUnreal(S, App.markSeed, App.idmap, App.contract, App.roles, ctx());
    if (!r.next) {
      UI.chooseCard('The score cannot be bound yet', `Binding changes no time and guesses nothing, so it stopped:\n${r.report.refusals.map(x => '• ' + x.msg).join('\n')}`, [], () => {}, 'Close');
      return;
    }
    // a locked group cannot change, even by this
    const lockedHit = Object.keys(S.elements).filter(id => App.locked[S.elements[id].group] && JSON.stringify(S.elements[id]) !== JSON.stringify(r.next.elements[id]));
    if (lockedHit.length) { const e = S.elements[lockedHit[0]]; return toast(`${e.key} is in the locked group ${(S.groups.find(g => g.id === e.group) || {}).name}: unlock it first (binding changes ${lockedHit.length} element${lockedHit.length > 1 ? 's' : ''} there)`); }
    const rep = r.report, b = rep.beats, s = rep.sounds, cues = rep.reach.cues, rc = rep.reach.after, moves = cues.filter(c => c.action === 'appear' || c.action === 'disappear').length;
    const n = (k, one, many) => `${k} ${k === 1 ? one : many || one + 's'}`;
    const amb = s.ambiguous.length ? ` · ${s.ambiguous.length} ambiguous (${[...new Set(s.ambiguous.map(a => a.asset))].join(', ')}: two files with that name, left unlinked)` : '';
    const body = [`Every moment gets the Unreal mark it corresponds to and every sound its Unreal asset. No time changes: the typical user stays at ${Integrity.fmt(rep.totals.typical)}, and so do the other simulated users.`,
      `${n(b.total, 'moment')}: ${b.onMark} on an Unreal mark, ${b.inside} inside one, ${b.preview} preview only${b.unmarked.length ? `, ${b.unmarked.length} without a mark` : ''}.`,
      `${n(s.linked, 'sound')} linked to Unreal assets${amb} · ${s.missing + s.haptics} not in Unreal (${s.missing} not in Content yet, ${n(s.haptics, 'haptic')}).`,
      `${n(rep.elements.bound, 'element')} now say${rep.elements.bound === 1 ? 's' : ''} what ${rep.elements.bound === 1 ? 'it is' : 'they are'} in Unreal (action, target, asset)${rep.elements.noUnreal ? `; the ${rep.elements.noUnreal} the contract says Unreal does not play get no action` : ''}.`]
      .concat(rep.seed.pending ? [`The marks come from obra/score/seed/marks-v1.json, which is still ${rep.seed.status}${rep.seed.review ? ` (${n(rep.seed.review, 'open question')}, such as where S2.BEGIN falls)` : ''}. Binding does not make them final: Ctrl+Z takes them out again.`] : [])
      .concat([`${n(rc.cue, 'element')} become${rc.cue === 1 ? 's' : ''} cue-ready: a cue could fire ${rc.cue === 1 ? 'it' : 'them'} from an Unreal mark${rc.wired > rep.reach.before.wired ? `. ${rc.wired - rep.reach.before.wired} more count as wired: Unreal already calls their asset` : ''}. There is no cue player in Unreal yet (BP_ScorePlayer_SC), so nothing changes in the APK.`
        + (moves ? ` ${moves} of the cue-ready are Alma's appear and disappear: BP_Obra_SC already does them with its own graph, so ask the Director before a player relies on them.` : '')])
      .concat(rep.notes.map(t => 'Note: ' + t)).join('\n\n');
    UI.chooseCard('Bind the score to Unreal', body, [
      { id: 'go', primary: true, label: 'Bind (you can undo it)', detail: 'Ctrl+Z returns the score exactly as it is now. Nothing is sent to Unreal and nothing is saved until you press Ctrl+S.' },
    ], c => {
      if (c !== 'go') return;
      // measured again on the score that is there when it is applied (the card blocks edits, so it is the same one)
      const ok = commit('Bind to Unreal', { type: 'bind', ids: [] }, nx => {
        const m = Edits.bindUnreal(nx, App.markSeed, App.idmap, App.contract, App.roles, ctx());
        if (!m.next) { toast('Binding stopped: ' + m.report.refusals[0].msg); return false; }
        for (const k of Object.keys(nx)) delete nx[k];
        Object.assign(nx, m.next);
      });
      if (ok) toast(`Bound to Unreal · ${b.marked} moments, ${s.linked} sounds · nothing moved · save with Ctrl+S`);
    }, 'Cancel');
  },
  /* ---------- lote 5 (design B §7, audit D2): "Changes in guion.js" ----------
     guion.js is an import source, never the truth. File ▸ Check guion.js for changes… asks the server to read it (the extractor
     writes obra/score/score.extracted.json, never the score), compares that with the score here (ImportDiff: the same module the
     command line, tools/score/import_report.mjs, uses) and shows each difference as a row with its own verbs. Nothing is taken
     unless chosen: the default is what is safe (new clips, new words, a new name); a time is never taken by default (DA_Partitura_Obra
     rules the timing). Taking is ONE edit through commit() (one card at most), undoable, saved by the user. A schema 2 score only
     gets the report: its names are not stable until the upgrade, so nothing can be matched to its ids.
     App.guion = { extracted, at, ms, pick: { rid: [verbs] }, error } while the panel is open */
  guionPlan() {
    const G = App.guion; if (!G || !G.extracted) return null;
    const d = ImportDiff.diff(App.score, G.extracted), sel = {};
    for (const r of d.rows) { const p = G.pick[r.rid] || (G.pick[r.rid] = r.defaults.slice()); if (p.length) sel[r.rid] = p; }
    for (const k of Object.keys(G.pick)) if (!d.rows.some(r => r.rid === k)) delete G.pick[k];   // a row that is gone takes its choices with it
    // a dry run, to say what taking would flag before anything is taken
    const plan = d.stable ? ImportDiff.applyImportRows(App.score, G.extracted, d, sel, { Edits, who: App.who }) : null;
    return { d, sel, plan, names: Object.keys(d.mapUpdates).filter(o => d.mapUpdates[o].via !== 'rename') };
  },
  async guionCheck() {
    if (busy()) return;
    App.guion = null; const seq = App.guionSeq = (App.guionSeq || 0) + 1;
    UI.guionPanel({ reading: true });
    try {
      const r = await fetch('/api/guion/scan', { method: 'POST' }), j = await r.json().catch(() => ({}));
      if (!r.ok || !j.ok) throw new Error(j.error || `the server answered ${r.status}`);
      const f = await fetch(j.extracted + '?t=' + Date.now(), { cache: 'no-store' });
      if (!f.ok) throw new Error(`${j.extracted} → ${f.status}`);
      App.guion = { extracted: await f.json(), at: j.at, ms: j.ms, pick: {} };
    } catch (e) { App.guion = { error: e.message || String(e), pick: {} }; }
    if (seq === App.guionSeq && document.querySelector('.imp.gdiff')) UI.guionPanel();   // closed while it was reading: nothing to show
  },
  // take what is chosen in the panel (rows → sel) as ONE edit. The edit says which elements it changed and how (text, rename) so that
  // integrity judges it like any edit: a text change to a voice Unreal plays opens the usual card
  guionTake(sel, label, quiet, afterCard) {
    if (busy()) return false;
    const G = App.guion; if (!G || !G.extracted) return false;
    const d = ImportDiff.diff(App.score, G.extracted), r = ImportDiff.applyImportRows(App.score, G.extracted, d, sel, { Edits, who: App.who });
    if (!r.ok) { toast(r.why || 'Nothing to take'); return false; }
    const t = r.taken, judged = t.text || t.timing || t.renamed;
    const parts = [t.moments && `${t.moments} moment${t.moments > 1 ? 's' : ''} added`, t.added && `${t.added} clip${t.added > 1 ? 's' : ''} added`, t.renamed && `${t.renamed} renamed`, t.text && `${t.text} text`, t.timing && `${t.timing} timing`,
      t.kept && `${t.kept} kept`, t.dismissed && `${t.dismissed} dismissed`, !(t.moments + t.added + t.renamed + t.text + t.timing + t.kept + t.dismissed) && t.names && `${t.names} name${t.names > 1 ? 's' : ''} follow guion.js`].filter(Boolean);
    const op = { type: judged ? 'import-guion' : quiet ? 'import-map' : 'import-add', ids: r.ids, verbs: r.verbs, afterCard };
    const ok = commit(label || 'Take from guion.js · ' + parts.join(', '), op, n => { for (const k of Object.keys(n)) delete n[k]; Object.assign(n, JSON.parse(JSON.stringify(r.next))); });
    if (ok && !App.cardOpen) toast(`${parts.join(', ')} · from guion.js${r.flagged.length ? ` · ${r.flagged.length} to check` : ''} · Ctrl+Z undoes it, Ctrl+S saves`);
    return ok;
  },
  // each action closes the panel (it holds the editor still), edits, and opens it again on what is left unless a decision card is open
  guionApply() {
    const P = Act.guionPlan(); if (!P) return;
    UI.closeOverlay(); Act.guionTake(P.sel, null, false, () => UI.guionPanel()); if (!App.cardOpen) UI.guionPanel();
  },
  guionRow(rid, verb) {   // keep / dismiss one row: bookkeeping only, quiet
    UI.closeOverlay(); Act.guionTake({ [rid]: [verb] }, `${verb === 'keep' ? 'Keep' : 'Dismiss'} · guion.js change`, true); if (!App.cardOpen) UI.guionPanel();
  },
  guionNames() {   // the names that follow guion.js with no row to take (a renumbered moment, a '#n' that shifted): the ids stay
    UI.closeOverlay(); Act.guionTake({}, 'Names follow guion.js', true); if (!App.cardOpen) UI.guionPanel();
  },
  guionDelete(rid) {   // a clip guion.js no longer has: delete it here through the usual delete (its own card, with what hangs from it)
    const G = App.guion, d = G && G.extracted && ImportDiff.diff(App.score, G.extracted), r = d && d.rows.find(x => x.rid === rid);
    if (!r || !App.score.elements[r.id]) return;
    UI.closeOverlay();
    Act.remove([r.id]);
  },
  // C9: a new anchor for an element or a moment (null = detach), at the same time with the typical user.
  // Refused with the reason when it would loop; returns false then (the timeline's pick mode stays on to try another)
  reanchor(id, anchor) {
    if (busy()) return false;
    const S = App.score, isB = !!S.beats[id], x = S.elements[id] || S.beats[id];
    if (!x) { toast('It no longer exists'); return false; }
    if (!isB && App.locked[x.group]) { toast(`${x.key} is in a locked group: unlock it first`); return false; }
    const r = Edits.reanchor(S, id, anchor, ScoreEngine);
    if (!r.ok) { toast(r.why); return false; }
    const who = (isB ? 'moment ' : '') + x.key, to = anchorText(r.at);
    if (!commit(`Anchor · ${who} → ${to}`, { type: 'reanchor', ids: isB ? [] : [id] }, n => { (n.elements[id] || n.beats[id]).at = Object.assign({}, r.at); })) return false;
    if (App.cardOpen) return true;   // the card says what happens next
    // only the typical user keeps the time: say who else hears it somewhere else (and if that is the one on screen)
    const oth = Object.entries(r.others).map(([p, d]) => `${ScoreEngine.PERSONAS[p].name.toLowerCase()} ${d > 0 ? '+' : '−'}${fmtS(Math.abs(d))} s`);
    const seen = App.persona !== 'typical' && r.others[App.persona] != null ? ' (the one on screen moves)' : '';
    toast(`${who[0].toUpperCase() + who.slice(1)} now hangs from the ${to}: same time for the typical user${oth.length ? ' · other simulated users shift: ' + oth.join(', ') + seen : ' and every simulated user'}`);
    return true;
  },
  // lote 5 (design B §5.3): which side of a decision plays this element. value null = both sides. A normal edit: it can lengthen or
  // shorten the moments, and an element that something common hangs from leaves that one without an anchor on the other side
  // (C1.BRANCH.ANCHOR, a block): the card says so before anything is written
  setBranch(ids, on, value) {
    if (busy()) return false;
    ids = [...new Set(ids)].filter(id => App.score.elements[id]); if (!ids.length) return false;
    const lk = ids.map(id => App.score.elements[id]).find(e => App.locked[e.group]);
    if (lk) { toast(`${lk.key} is in a locked group: unlock it first`); UI.renderInspector(); return false; }
    const r = Edits.setBranch(App.score, ids, on, value);
    if (!r.ok) { if (!r.same) toast(r.why); UI.renderInspector(); return false; }
    const keys = keysText(r.changed.map(id => App.score.elements[id].key)), what = value == null ? 'both sides' : optionName(on, value) + ' only';
    if (!commit(`Branch · ${keys} · ${what}`, { type: 'branch', ids: r.changed }, n => { for (const id of r.changed) { if (value == null) delete n.elements[id].branch; else n.elements[id].branch = { on, value }; } })) { UI.renderInspector(); return false; }
    return true;
  },
  // "Anchor in DON'T SHARE": a new anchor for one option of a decision (null: the same as everywhere else), at the same time there.
  // Refused with the reason when it would loop, hang from something that is not there in that option, or move anything
  reanchorAlt(id, k, anchor, field) {
    if (busy()) return false;
    const S = App.score, isB = !!S.beats[id], x = S.elements[id] || S.beats[id];
    if (!x) { toast('It no longer exists'); return false; }
    if (!isB && App.locked[x.group]) { toast(`${x.key} is in a locked group: unlock it first`); return false; }
    const r = Edits.reanchorAlt(S, id, k, anchor, ScoreEngine, { field });
    if (!r.ok) { toast(r.why); return false; }
    const who = (isB ? 'moment ' : '') + x.key, to = r.at ? anchorText(r.at) : 'the same anchor as everywhere else';
    if (!commit(`Anchor in ${r.label} · ${who} → ${to}`, { type: 'reanchor', ids: isB ? [] : [id] }, n => {
      const y = n.elements[id] || n.beats[id], z = r.next.elements[id] || r.next.beats[id];
      if (z.alt) y.alt = JSON.parse(JSON.stringify(z.alt)); else delete y.alt;
    })) return false;
    if (App.cardOpen) return true;
    const oth = Object.entries(r.others).map(([p, d]) => `${ScoreEngine.PERSONAS[p].name.toLowerCase()} ${d > 0 ? '+' : '−'}${fmtS(Math.abs(d))} s`);
    toast(r.at ? `${who[0].toUpperCase() + who.slice(1)} now hangs from the ${to} in ${r.label}: same time there, and nothing changes in the other side${oth.length ? ' · other simulated users shift: ' + oth.join(', ') : ''}`
      : `${who[0].toUpperCase() + who.slice(1)} uses the same anchor as everywhere else in ${r.label}`);
    return true;
  },
  // C1.ANCHOR.MISSING: repair only the anchor that is lost (its start, what it lasts until, or both), where it falls now.
  // An anchor that still exists is never touched (the Problems row "Detach (keeps its time)")
  fixLostAnchor(id) {
    if (busy()) return false;
    const S = App.score, isB = !!S.beats[id], x = S.elements[id] || S.beats[id];
    if (!x) { toast('It no longer exists'); return false; }
    if (!isB && App.locked[x.group]) { toast(`${x.key} is in a locked group: unlock it first`); return false; }
    const r = Edits.detachLost(S, id, ScoreEngine);
    if (!r.ok) { toast(r.why); return false; }
    const who = (isB ? 'moment ' : '') + x.key, Who = who[0].toUpperCase() + who.slice(1);
    const say = r.fields.map(f => f.field === 'end'
      ? `lasts until ${Math.abs(f.anchor.off) < .05 ? 'the ' + anchorText(f.anchor) : fmtS(Math.abs(f.anchor.off)) + ' s ' + (f.anchor.off > 0 ? 'after' : 'before') + ' the ' + anchorText(f.anchor)}`
      : `hangs from the ${anchorText(f.anchor)}`).join(' and ');
    if (!commit(`Anchor · ${who} → repaired`, { type: 'reanchor', ids: isB ? [] : [id] }, n => { const y = n.elements[id] || n.beats[id]; for (const f of r.fields) y[f.field] = Object.assign({}, f.anchor); })) return false;
    if (App.cardOpen) return true;
    const oth = Object.entries(r.others).map(([p, d]) => `${ScoreEngine.PERSONAS[p].name.toLowerCase()} ${d > 0 ? '+' : '−'}${fmtS(Math.abs(d))} s`);
    toast(`${Who} now ${say}: same time for the typical user${oth.length ? ' · other simulated users shift: ' + oth.join(', ') : ''}`);
    return true;
  },
  // notes for the team (audit C13): add, edit, resolve or reopen, delete. Quiet edits, undoable like any other
  addNote(text) {
    text = String(text || '').trim(); if (!text) return false;
    return commit('Note', { type: 'note', ids: [] }, n => { n.notes = n.notes || {}; n.notes['nt_' + Date.now().toString(36)] = { t: +App.ph.toFixed(2), who: App.who, text, at: new Date().toISOString(), el: App.selKind === 'el' ? App.sel : null }; });
  },
  editNote(nid, text) {
    const x = (App.score.notes || {})[nid]; text = String(text || '').trim(); if (!x) return false;
    if (!text) { toast('A note needs words: to remove it, use Delete'); return false; }
    if (text === x.text) return true;   // nothing changed
    return commit('Note · edit', { type: 'note', ids: [] }, n => { const y = n.notes[nid]; y.text = text; y.edited = { who: App.who, at: new Date().toISOString() }; });
  },
  resolveNote(nid, on) {
    const x = (App.score.notes || {})[nid]; if (!x || !!x.resolved === !!on) return;
    commit(on ? 'Note · resolved' : 'Note · reopened', { type: 'note', ids: [] }, n => { if (on) n.notes[nid].resolved = { who: App.who, at: new Date().toISOString() }; else delete n.notes[nid].resolved; });
  },
  deleteNote(nid) {
    if (!(App.score.notes || {})[nid]) return;
    if (commit('Delete note', { type: 'note', ids: [] }, n => { delete n.notes[nid]; })) toast('Note deleted · Ctrl+Z brings it back');
  },
  // bookmarks (score.markers): a named point in time; rename, move along the ruler, delete (audit C13)
  bookmark() {
    const ok = commit('Bookmark', { type: 'marker', ids: [] }, n => {
      n.markers = n.markers || {}; const taken = new Set(Object.values(n.markers).map(m => m.name)); let k = Object.keys(n.markers).length + 1;
      while (taken.has('Bookmark ' + k)) k++;   // a deleted or renamed one never leaves two with the same name
      n.markers['mk_' + Date.now().toString(36)] = { t: +App.ph.toFixed(2), name: 'Bookmark ' + k, who: App.who };
    });
    if (ok) toast('Bookmark at ' + tc(App.ph) + ' · double-click it to rename, drag it to move');
  },
  renameMarker(mid, name) {
    const m = (App.score.markers || {})[mid]; name = String(name || '').trim();
    if (!m || !name || name === m.name) return UI.renderTimeline();
    if (!commit(`Rename bookmark · ${m.name}`, { type: 'marker', ids: [] }, n => { n.markers[mid].name = name; })) UI.renderTimeline();
  },
  moveMarker(mid, t) {
    const m = (App.score.markers || {})[mid]; if (!m || !Number.isFinite(t)) return UI.renderTimeline();
    t = +clamp(t, 0, App.sched.total).toFixed(2); if (Math.abs(t - m.t) < .005) return UI.renderTimeline();
    if (!commit(`Move bookmark · ${m.name}`, { type: 'marker', ids: [] }, n => { n.markers[mid].t = t; })) UI.renderTimeline();   // refused: it goes back
  },
  deleteMarker(mid) {
    const m = (App.score.markers || {})[mid]; if (!m) return;
    if (commit(`Delete bookmark · ${m.name}`, { type: 'marker', ids: [] }, n => { delete n.markers[mid]; })) toast(`${m.name} deleted · Ctrl+Z brings it back`);
  },
};
function addLane(n, gid, after) {
  const gg = n.groups.find(x => x.id === gid); let i = gg.lanes.length + 1, id;
  do { id = 'ln_' + gid + '_' + (i++); } while (n.lanes[id]);
  n.lanes[id] = { name: gg.name + ' ' + (gg.lanes.length + 1), group: gid };
  const at = after ? gg.lanes.indexOf(after) + 1 : gg.lanes.length; gg.lanes.splice(at, 0, id);
  return id;
}
/* an anchor in words: "start of moment 2.4", "end of VO_04", "end of PASO in 2.7a" (a key used in several moments says which) */
function anchorText(a) {
  const S = App.score; if (!a || !a.ref) return 'start of the piece';
  const edge = a.edge === 'start' ? 'start' : 'end';
  if (S.beats[a.ref]) return `${edge} of moment ${S.beats[a.ref].key}`;
  const e = S.elements[a.ref]; if (!e) return `${edge} of ${a.ref}`;
  const dup = Object.values(S.elements).some(o => o !== e && o.key === e.key);
  return `${edge} of ${e.key}${dup && S.beats[e.beat] ? ' in ' + S.beats[e.beat].key : ''}`;
}
function uniqueKey(base) { return Edits.uniqueKey(new Set(Object.values(App.score.elements).map(e => e.key)), base); }
/* "VO_05, VO_06 and 3 more" */
function keysText(keys) { return keys.length <= 3 ? keys.join(', ') : keys.slice(0, 2).join(', ') + ` and ${keys.length - 2} more`; }
/* paste or duplicate (C10): planned first (Edits.planPaste), then ONE quiet commit. The copies are new (not in Unreal yet),
   so the card has nothing from Unreal to say; the ripple and new warnings go to the toast. A locked group gets nothing */
function pasteClips(c, target, verb, where, lanes) {
  const lk = c.items.find(it => App.locked[it.el.group]);
  if (lk) { toast(`${(App.score.groups.find(g => g.id === lk.el.group) || {}).name || lk.el.group} is locked: unlock it to ${verb.toLowerCase()} ${lk.el.key}`); return false; }
  const plan = Edits.planPaste(App.score, c, target, ScoreEngine, { who: App.who, addLane, lanes });
  if (!plan.ok) { toast(plan.why); return false; }
  const label = `${verb} · ${keysText(plan.keys)}`, seq = App.toastSeq;
  if (!commit(label, { type: 'paste', ids: plan.ids }, n => { for (const k of Object.keys(n)) delete n[k]; Object.assign(n, JSON.parse(JSON.stringify(plan.next))); })) return false;
  setSelection(plan.ids, plan.ids[0]);
  if (App.toastSeq === seq) toast(`${label} · ${where} · new: not in Unreal yet${plan.newLanes.length ? ` · ${plan.newLanes.length} new lane${plan.newLanes.length > 1 ? 's' : ''}` : ''}`);
  return true;
}
function beatAt(t) { let best = null; for (const a of App.score.acts) for (const b of a.beats) { const [s] = App.sched.t[b]; if (s <= t + 1e-6 && (!best || s >= App.sched.t[best][0])) best = b; } return best || App.score.acts[0].beats[0]; }
function laneBusy(lane, s, e, exclude) {
  const E = App.score.elements, T = App.schedT.t; const e2 = Math.max(e, s + .05);   // lanes are checked on the typical timeline
  for (const id in E) { if (E[id].lane !== lane || (exclude && exclude.has(id))) continue; const [a, b0] = T[id]; const b = Math.max(b0, a + .05); if (a < e2 - 1e-4 && b > s + 1e-4) return id; }
  return null;
}
/* ISP laneLibreCerca: the nearest free lane of the same group; null = create one */
function freeLane(gid, s, e) { const g = App.score.groups.find(x => x.id === gid); for (const l of g.lanes) if (!laneBusy(l, s, e)) return l; return null; }

/* ---------- selection, playhead, persona, modes ---------- */
/* the selected clips: the primary (App.sel, what the inspector shows) first, then the rest (audit C10) */
function selIds() {
  if (App.selKind !== 'el' || !App.score.elements[App.sel]) return [];
  return [App.sel, ...[...App.selMore].filter(id => id !== App.sel && App.score.elements[id])];
}
function select(id, kind) {
  App.selMore = new Set();
  App.sel = id; App.selKind = id ? (kind || (App.score.beats[id] ? 'beat' : 'el')) : null; App.selRole = null;
  if (App.insTab !== 'insp') App.insTab = 'insp';
  UI.renderTimelineSelection(); UI.renderInspector(); UI.renderStatus();
}
/* several clips; primary = the one the inspector shows (Ctrl/Shift+click: the last one clicked) */
function setSelection(ids, primary) {
  ids = [...new Set(ids)].filter(id => App.score.elements[id]);
  if (!ids.length) return select(null);
  const p = ids.includes(primary) ? primary : ids[0];
  App.sel = p; App.selKind = 'el'; App.selRole = null; App.selMore = new Set(ids.filter(id => id !== p));
  if (App.insTab !== 'insp') App.insTab = 'insp';
  UI.renderTimelineSelection(); UI.renderInspector(); UI.renderStatus();
}
/* Ctrl+click: in or out of the selection · Shift+click: in */
function toggleSel(id) { const cur = selIds(); if (!cur.includes(id)) return setSelection(cur.concat(id), id); const rest = cur.filter(x => x !== id); setSelection(rest, id === App.sel ? rest[rest.length - 1] : App.sel); }
function addSel(id) { setSelection(selIds().concat(id), id); }
/* Ctrl+A: every element of the moment at the playhead (locked groups stay out, as locked tracks in Premiere) */
function selectMoment() {
  const b = beatAt(App.ph), T = App.sched.t, own = Object.keys(App.score.elements).filter(id => App.score.elements[id].beat === b).sort((x, y) => T[x][0] - T[y][0]);
  const ids = own.filter(id => !App.locked[App.score.elements[id].group]), out = own.length - ids.length;
  if (!ids.length) return toast(own.length ? `Every element of moment ${App.score.beats[b].key} is in a locked group` : `Moment ${App.score.beats[b].key} has no elements`);
  setSelection(ids, ids[0]);
  toast(`${ids.length} element${ids.length > 1 ? 's' : ''} of moment ${App.score.beats[b].key} selected${out ? ` · ${out} in locked groups left out` : ''} · Esc clears`);
}
/* what no longer exists leaves the selection; the primary passes to another selected clip */
function pruneSel() {
  if (App.selKind !== 'el' || !App.score) return;
  for (const id of [...App.selMore]) if (!App.score.elements[id]) App.selMore.delete(id);
  if (!App.score.elements[App.sel]) { const nx = [...App.selMore][0] || null; App.sel = nx; if (nx) App.selMore.delete(nx); else App.selKind = null; }
}
function selectRole(name) { App.selMore = new Set(); App.selRole = name; App.sel = null; App.selKind = 'role'; App.insTab = 'insp'; UI.renderTimelineSelection(); UI.renderInspector(); UI.renderLibrary(); UI.renderStatus(); }
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
  if (App.sound) ambSoon();
  if (!fromChannel) post({ t: App.ph, playing: App.playing, rate: App.rate });   // the speed travels with it: a seek never resets the other tab to 1×
}
let _sp = 0;
function seekProto(t, now) { if (!App.SC) return; if (now) { try { App.SC.seek(t); } catch (_) {} return; } if (_sp) return; _sp = requestAnimationFrame(() => { _sp = 0; try { App.SC.seek(App.ph); } catch (_) {} }); }
let _last = 0, _ticking = false, _lastPost = 0, _lastAmb = 0;
/* transport (audit C10). App.rate is the signed speed: 1, 2, 4 forward (the 3D plays at that speed, with its sound) or
   −1, −2, −4 backwards (the editor's clock drives and the 3D is sought every frame, silent). Stopping goes back to 1×.
   With an In/Out range, playback starts at In when the playhead is outside it and stops at Out (Transport.startAt/advance) */
const playBounds = () => Transport.bounds({ inT: App.inT, outT: App.outT }, App.sched.total);
function play(on, fromChannel, rate) {
  const was = App.playing, wasR = App.rate, r = on ? (rate || (was ? App.rate : 1)) : 1;
  // a new start (or a change of direction) enters the range; the other tab only follows
  if (on && !fromChannel && (!was || Math.sign(r) !== Math.sign(wasR))) { const t = Transport.startAt(App.ph, r, playBounds(), App.sched.total); if (Math.abs(t - App.ph) > 1e-6) seek(t, true); }
  App.playing = on; App.rate = r; _last = performance.now();
  // the 3D starts from the playhead itself (a jump to In is not left to the next frame), at the speed, with its sound
  if (App.SC && (was !== on || wasR !== r)) { try { if (on && !(was && wasR > 0)) App.SC.seek(App.ph); App.SC.S.speed = r > 0 ? r : 1; App.SC.setPlaying(on && r > 0); } catch (_) {} }
  if (on && !_ticking) { _ticking = true; requestAnimationFrame(tick); }
  if (on && App.sound) ambSoon();
  UI.renderTransport();
  if (!fromChannel) post({ t: App.ph, playing: on, rate: r });
}
function tick(now) {
  if (!App.playing) { _ticking = false; return; }
  // forward, the 3D clock leads while it plays (at the same speed); if it stops first (its end, a gap), or backwards,
  // the editor's own clock carries on
  const ps = App.SC && App.SC.S, r = App.rate, prev = App.ph;
  const next = r > 0 && ps && ps.playing && Math.abs(ps.t - prev) < Math.max(1, r) ? ps.t : prev + (now - _last) / 1000 * r;
  _last = now;
  const st = Transport.advance(prev, next, r, playBounds(), App.sched.total);
  App.ph = st.t;
  if (st.stop) { play(false); seekProto(App.ph, true); }   // at Out, In or an end: the 3D lands exactly there
  else if (r < 0) seekProto(App.ph, true);                // backwards: the 3D follows the playhead frame by frame
  // the other tab corrects its drift once a second
  if (now - _lastPost > 1000) { _lastPost = now; post({ t: App.ph, playing: App.playing, rate: App.rate }); }
  // the next ambience is decoded before the playhead reaches it
  if (App.sound && now - _lastAmb > 2000) { _lastAmb = now; ambSoon(); }
  UI.movePlayhead(true); requestAnimationFrame(tick);
}
/* J (−1) / L (+1): faster each press, up to 4×; K held: a step of 0.1 s, paused */
function shuttle(dir) {
  const s = Transport.shuttle({ playing: App.playing, rate: App.rate, kHeld: App.kHeld }, dir);
  if (s.step) { if (App.playing) play(false); seek(App.ph + s.step); return; }
  play(true, false, s.rate);
}
/* I / O / Alt+X: the play range. Playback state of this computer (prefs) shared with the 3D tab, never in the score */
function setRange(r, msg, fromChannel) {
  App.inT = r.inT; App.outT = r.outT; UI.renderRange(); UI.renderTransport();
  // the tab that marked it saves only the range (the 3D tab may hold older prefs: they are not written back)
  if (!fromChannel) { lsSet(LS_PREF, Object.assign(lsGet(LS_PREF) || {}, { inT: App.inT, outT: App.outT })); post({ range: [App.inT, App.outT] }); }
  if (msg) toast(msg);
}
function markIn() {
  const r = Transport.markIn({ inT: App.inT, outT: App.outT }, App.ph);
  setRange(r, `In at ${tc(r.inT)} · Play starts here${r.outT != null ? ' and stops at Out ' + tc(r.outT) : ''}${r.cleared ? ' · the Out was before it: cleared' : ''} · Alt+X clears`);
}
function markOut() {
  const r = Transport.markOut({ inT: App.inT, outT: App.outT }, App.ph);
  setRange(r, `Out at ${tc(r.outT)} · Play stops here${r.inT != null ? ', from In ' + tc(r.inT) : ''}${r.cleared ? ' · the In was after it: cleared' : ''} · Alt+X clears`);
}
function clearRange() {
  if (App.inT == null && App.outT == null) return toast('No in or out to clear');
  setRange({ inT: null, outT: null }, 'In and out cleared · Play runs to the end again');
}
/* ↑ / ↓: the start of the previous or next moment, on the timeline you are looking at */
function stepMoment(dir) {
  const starts = App.score.acts.flatMap(a => a.beats).map(b => App.sched.t[b] && App.sched.t[b][0]);
  const t = Transport.momentStep(starts, App.ph, dir, App.playing ? .4 * Math.abs(App.rate) : 0);
  if (t == null) return toast(dir > 0 ? 'This is the last moment' : 'This is the start of the piece');
  seek(t); UI.revealTime(t);
}
function toggleSnap() { App.snap = !App.snap; savePref(); UI.renderTransport(); toast(App.snap ? 'Snapping on · S turns it off' : 'Snapping off · S turns it on'); }

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
        w.addEventListener('keyup', ev => { onKeyUp(ev); ev.stopImmediatePropagation(); }, true);   // K released, Alt released
        w.addEventListener('mousedown', () => document.querySelectorAll('.menu.ov,.qa.ov').forEach(n => n.remove()), true);
        try { f.blur(); window.focus(); } catch (_) {}
        // the editor drives: interaction is simulated (waits last what the score says), voices play with their subtitles
        try { w.SC.S.live = false; w.SC.S.voMode = 'both'; for (const k in w.SC.GL) delete w.SC.GL[k]; for (const k in w.SC.CUT) delete w.SC.CUT[k]; } catch (_) {}
        App.SC = w.SC; pushScoreToProto(); seekProto(App.ph, true); UI.renderViewerBar(); protoResize();
        if (App.sound) setSound(true);
      } else if (n > 120) { clearInterval(iv); UI.renderViewerBar('The 3D preview could not start.'); }
    }, 100);
  });
}

/* The 3D plays THIS score (audit lote 3). Every beat and clip gets its time from the score as an absolute edit, in
   memory only: the prototype's files and its own saved timeline are never written. Times are the ones on screen
   (the simulated user chosen). A clip the score no longer has goes quiet (as an inactive help line); an element that
   is new in the score has no 3D yet. */
let _pushT = 0;
function pushSoon() { clearTimeout(_pushT); _pushT = setTimeout(pushScoreToProto, 150); }
function pushScoreToProto() {
  const SC = App.SC; if (!SC || !SC.EDITS || !SC.BYUID || !SC.CLIPS) return;
  const T = App.sched.t, off = App.sched.off || {}, next = {}, inScore = new Set(), ends = {}, reactGate = {}, hints = {}; let notIn3d = 0;
  for (const [b, B] of Object.entries(App.score.beats)) if (SC.BYUID.get(B.key) && T[b]) next[B.key] = { at: { ref: null, edge: 'start', off: +T[b][0].toFixed(4) } };
  for (const [id, e] of Object.entries(App.score.elements)) {
    const uid = e.legacy && e.legacy.uid, c = uid && SC.BYUID.get(uid);
    if (!c || !T[id]) { notIn3d++; continue; }
    if (off[id]) continue;   // the other option of a decision: quiet in the 3D, like a deleted clip (the option on screen is exact)
    inScore.add(uid); ends[uid] = +T[id][1].toFixed(4);
    const x = { at: { ref: null, edge: 'start', off: +T[id][0].toFixed(4) }, dur: +Math.max(0, T[id][1] - T[id][0]).toFixed(4) };
    if (e.gate) x.fw = e.gate.fw;
    if (e.type === 'vo' && e.text != null) x.text = e.text;
    if (e.hint != null) hints[uid] = e.hint;   // what the 3D shows on screen comes from the score (in English), not from guion.js
    // a help line of a wait that runs on the stage's clock plays only if it comes before THIS user acts (the engine's `react`), not
    // before the wait's clock ends, which is all the prototype can tell by itself
    const w = e.help && App.score.elements[e.help];
    if (w && w.gate && w.gate.blocking === false && App.sched.react && App.sched.react[e.help] != null && Math.abs(App.sched.react[e.help] - App.sched.t[e.help][1]) > 1e-6) reactGate[uid] = +App.sched.react[e.help].toFixed(4);
    next[uid] = x;
  }
  const gone = SC.CLIPS.filter(c => !inScore.has(c.uid)).map(c => c.uid);
  const br = App.sched.branch;   // schema 3: the option on screen (null for schema 2: nothing to tell the 3D)
  const sig = JSON.stringify([next, gone, br, reactGate, hints]);
  App.proto3d = { notIn3d, gone: gone.length };
  if (sig === App._protoSig) return; App._protoSig = sig;
  // the prototype's own `when` closures show the same option the score is timed in (runtime only, never written)
  if (br && br.share != null) { try { SC.S.share = br.share !== 'no'; } catch (_) {} }
  const E = SC.EDITS; for (const k of Object.keys(E)) delete E[k]; Object.assign(E, next);
  for (const c of SC.CLIPS) {
    if (!('_vvr' in c)) c._vvr = { endA: c.endA, help: c.help, helpGate: c.helpGate, when: c.when, hint: c.hint };   // the prototype's own, to give back
    c.hint = c.uid in hints ? hints[c.uid] : c._vvr.hint;
    // schema 3: which side plays a clip is the score's (`branch`; the other side is quiet above), not the prototype's `when`: an
    // element the editor made common plays in both sides. Schema 2 keeps the prototype's own closures
    c.when = br && inScore.has(c.uid) ? null : c._vvr.when;
    // the end too comes from the score (a recording longer than its clip still plays to its end: that is what you hear)
    if (inScore.has(c.uid)) { c.help = c._vvr.help; c.helpGate = reactGate[c.uid] != null ? { e: reactGate[c.uid] } : c._vvr.helpGate; c.endA = { ref: null, edge: 'start', off: ends[c.uid] }; }
    else { c.help = 'not in the score'; c.helpGate = { e: -1 }; }
  }
  (SC.LOCS || []).forEach(L => { L.k = 1; });   // no stretching: the score's times are the times
  try { SC.computeSchedule(); SC.seek(App.ph); } catch (_) {}
  UI.renderViewerBar();
}
/* Sound in the 3D: the real voices (final mix, earlier takes where there is no mix), the sound effects and ambiences that
   obra/audio/media_map.json maps, and the prototype's synthetic markers for the rest. Decoded inside the 3D frame (its own
   realm). Voices and effects: all of them, once, the first time sound is turned on. Ambiences (30-50 MB each): only the one
   at the playhead and the next one (Media.ambWindow), the rest is dropped. A file never changes a time: the 3D plays it at its
   clip's time, to its own end (an ambience loops until the next one), at Unreal's volume when the map gives it. */
let _sounds = null;
/* one file into the 3D's AUDIO under its sound id. 'shared' (optional): the same file at the same volume under several ids
   (Charge1 is FX_CHARGE_1..4) is fetched and decoded once; never for ambiences, which must be freed when far */
async function decodeSound(id, ctx, shared) {
  const SC = App.SC, w = $('#proto').contentWindow, m = App.media[id], key = (m.path || m.url) + '|' + (m.gain == null ? 1 : m.gain);
  let p = shared && shared.get(key);
  if (!p) {
    p = (async () => {
      const r = await w.fetch(m.url); if (!r.ok) throw new Error(m.url + ' → ' + r.status);
      const ab = await r.arrayBuffer(), buf = await ctx.decodeAudioData(ab);
      if (m.gain != null) Media.scale(Array.from({ length: buf.numberOfChannels }, (_, c) => buf.getChannelData(c)), m.gain);
      return { buf, bytes: ab.byteLength };
    })();
    if (shared) shared.set(key, p);
  }
  const { buf, bytes } = await p;
  SC.AUDIO[id] = { name: m.file, dur: buf.duration, bytes, buf, local: true, src: m.src };
}
function loadSounds() {
  if (_sounds) return _sounds;
  const SC = App.SC, w = $('#proto').contentWindow; if (!SC || !App.media || !w) return Promise.resolve(0);
  const ids = Media.eagerIds(App.media, App.score); let n = 0;
  _sounds = (async () => {
    const ctx = new w.OfflineAudioContext(2, 1, 48000), queue = ids.slice(), shared = new Map();
    UI.renderViewerBar(`Loading the sounds · 0 of ${ids.length}`);
    const one = async () => { for (let id; (id = queue.shift());) {
      if (SC.AUDIO[id] && SC.AUDIO[id].buf) { n++; continue; }
      try { await decodeSound(id, ctx, shared); n++; if (n % 8 === 0) UI.renderViewerBar(`Loading the sounds · ${n} of ${ids.length}`); } catch (_) {}
    } };
    await Promise.all([one(), one(), one(), one()]);
    App._protoSig = null; pushScoreToProto(); UI.renderViewerBar();
    return n;
  })();
  return _sounds;
}
/* the ambiences around the playhead: called after a seek, at play and every few seconds while playing (debounced) */
let _ambT = 0, _ambBusy = false, _ambAgain = false;
function ambSoon() { if (!App.SC || !App.media) return; clearTimeout(_ambT); _ambT = setTimeout(syncAmbiences, 250); }
async function syncAmbiences() {
  const SC = App.SC; if (!SC || !App.media) return;
  const want = App.sound ? Media.ambWindow(App.score, App.sched.t, App.ph, App.media, 2) : [];
  for (const id of Media.ambienceIds(App.score)) if (!want.includes(id) && SC.AUDIO[id] && SC.AUDIO[id].src === 'fx') delete SC.AUDIO[id];
  if (_ambBusy) { _ambAgain = true; return; }
  _ambBusy = true;
  try {
    let ctx = null;
    for (const id of want) {
      if (SC.AUDIO[id] && SC.AUDIO[id].buf) continue;
      UI.renderViewerBar(`Loading the ambience ${id}…`);
      try { const w = $('#proto').contentWindow; ctx = ctx || new w.OfflineAudioContext(2, 1, 48000); await decodeSound(id, ctx); } catch (_) { continue; }
      // the one sounding now arrived after the 3D started it (with its marker): it takes over from the playhead
      if (App.sound && SC.S.playing && id === Media.ambAt(App.score, App.sched.t, App.ph)) { try { SC.setPlaying(true); } catch (_) {} }
    }
  } finally { _ambBusy = false; UI.renderViewerBar(); }
  if (_ambAgain) { _ambAgain = false; syncAmbiences(); }
}
async function setSound(on) {
  App.sound = on; savePref();
  const SC = App.SC; if (!SC) return UI.renderViewerBar();
  if (on && App.media) await loadSounds();
  // the prototype creates its audio context with the first voice it plays, and its ambience skips a play without one: the
  // first play after Sound on would start without its ambience (world.js audioOn / setAmbient)
  if (on) { try { const w = $('#proto').contentWindow; if (typeof w.audioOn === 'function') w.audioOn(); } catch (_) {} }
  try { SC.S.sound = App.sound; SC.setPlaying(!!SC.S.playing); } catch (_) {}
  UI.renderViewerBar();
  await syncAmbiences();   // off: the ambiences are dropped (memory); on: the one at the playhead and the next one
}
/* listen to one recording or mapped sound file from the inspector (plain audio in the editor, not the 3D) */
let _listen = null;
/* the link says Stop while its file plays (and Listen otherwise): only the text of the links changes, never a redraw (a field being typed in
   in the inspector would lose its text); the inspector draws the same word when it is drawn (App.listening) */
function listenState(id) {
  App.listening = id;
  document.querySelectorAll('[data-listen]').forEach(a => { a.textContent = a.dataset.listen === id ? 'Stop' : 'Listen'; });
}
function listen(id) {
  const m = App.media && App.media[id]; if (!m) return;
  if (_listen) { _listen.pause(); const same = _listen._id === id; _listen = null; listenState(null); if (same) return; }
  const a = _listen = new Audio(m.url); a._id = id; listenState(id);
  a.play().catch(() => { toast('Could not play ' + m.file); if (_listen === a) { _listen = null; listenState(null); } });
  a.onended = () => { if (_listen === a) { _listen = null; listenState(null); } };
}

/* the prototype sizes its canvas on window resize: tell it whenever its frame changes (UI hidden, mode, scale) */
function protoResize() { const f = $('#proto'); try { setTimeout(() => f.contentWindow.dispatchEvent(new Event('resize')), 30); } catch (_) {} }

const pendingVals = () => (App.score.propuestas && App.score.propuestas.valores) || {};
async function doSend(merged, prevWaiting) {
  const live = (window.Partitura && Partitura.liveValues(App.plive)) || {}, now = new Date().toISOString();
  const motivos = Object.assign({}, prevWaiting ? prevWaiting.motivos : {}, App.score.propuestas.motivos);
  const respaldo = {}; for (const k of Object.keys(merged)) respaldo[k] = live[k];
  const doc = { estado: 'enviada', enviado: now, por: App.who, asset: (App.plive || {}).asset || '/Game/SoulCharger/Obra/Partitura/DA_Partitura_Obra',
    base: App.plive ? { hash: App.plive.hash, exportado: App.plive.exportado } : null, valores: merged, motivos, respaldo,
    nota: 'Enviado a mano desde Veation VR Studio. Se aplica solo cuando se pide, con respaldo, prueba de humo y vuelta atras si falla (obra/unreal/LEEME.md).' };
  try {
    const r = await fetch('/api/partitura/propuesta', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(doc) });
    const j = await r.json(); if (!r.ok) throw new Error(j.error || r.status);
  } catch (e) { return toast('Not sent: ' + e.message); }
  App.prop = doc;
  commit('Sent to Unreal', { type: 'sent', ids: [] }, n => { n.propuestas = { valores: {}, motivos: {} }; });   // what was sent now lives in the file
  toast(`Sent to Unreal: ${Object.keys(merged).length} change${Object.keys(merged).length > 1 ? 's' : ''} · obra/unreal/partitura_propuesta.json · Save (Ctrl+S) to keep the score`);
}
/* Unreal publishes new values (partitura.json), the fate of what was sent (partitura_propuesta.json) and a new run
   (traza.json); the seed of the marks may be corrected by hand: look again when the window gets focus and every 20 s.
   Never writes anything. */
async function refreshUnreal(quiet, big) {
  const U = ['/obra/unreal/partitura.json', '/obra/unreal/partitura_propuesta.json', '/obra/unreal/traza.json', '/obra/score/seed/marks-v1.json'];
  // idmap.json and knobs.json (100 and 200 KB) are made by tools somebody runs by hand: read again when the window gets the focus
  // again (back from the terminal), else every two minutes
  const heavy = !!big || !App._bigAt || Date.now() - App._bigAt > 120000;
  if (heavy) U.push('/obra/unreal/idmap.json', '/obra/unreal/knobs.json');
  const got = await Promise.all(U.map(optJson));
  if (got[0] === undefined) return;   // server down: keep what we have
  // a file that cannot be read now (being written, a slip by hand) keeps what was read before (undefined = no change), and
  // Problems says so; the toast only when it breaks, not every 20 s
  let changed = false; const broke = [];
  const [live, prop, traza, seed, idmap, knobs] = got.map((v, i) => { const bad = v === UNREADABLE; if (noteUnreadable(U[i], bad)) { changed = true; if (bad) broke.push(U[i].slice(1)); } return bad ? undefined : v; });
  if (broke.length && !quiet) toast(`${broke.join(', ')} could not be read: the editor keeps what it had read before (Problems says so)`);
  if (live && (!App.plive || live.hash !== App.plive.hash)) { App.plive = live; changed = true; if (!quiet) toast('Unreal published new timing values (DA_Partitura_Obra ' + live.hash + ')'); }
  if (traza !== undefined && JSON.stringify(traza) !== JSON.stringify(App.traza || null)) {
    App.traza = traza; await loadRunHistory(); changed = true;
    if (!quiet && traza) toast(`New Unreal run: ${Calib.runLabel(Marks.traceInfo(traza)).replace(/^Unreal run · /, '')} · the Unreal run lane and Problems are up to date`);
  }
  if (seed !== undefined && JSON.stringify(seed) !== JSON.stringify(App.markSeed || null)) { App.markSeed = seed; changed = true; }
  if (heavy) {
    App._bigAt = Date.now();
    if (idmap !== undefined && JSON.stringify(idmap) !== JSON.stringify(App.idmap || null)) { App.idmap = idmap; changed = true; }
    if (knobs !== undefined && JSON.stringify(knobs) !== JSON.stringify(App.knobs || null)) { App.knobs = knobs; changed = true; }
  }
  const was = App.prop && App.prop.estado, now = prop && prop.estado;
  if (prop !== undefined && JSON.stringify(prop || null) !== JSON.stringify(App.prop && App.prop.estado ? App.prop : null)) {
    App.prop = prop || { valores: {}, motivos: {} }; changed = true;
    if (!quiet && now && now !== was) toast(now === 'aplicada' ? 'Unreal applied the changes you sent · smoke test OK' : now === 'rechazada' ? 'Unreal did NOT apply the changes: ' + (prop.motivo_rechazo || 'see the Timing tab') + ' · nothing changed in the APK' : 'Sent · waiting for Unreal');
  }
  if (changed) { compute(); UI.renderAll(); }
}
async function saveProposal(P, msg) {
  P.propuesto = new Date().toISOString(); P.asset = (App.plive || {}).asset || '/Game/SoulCharger/Obra/Partitura/DA_Partitura_Obra';
  P.base = App.plive ? { hash: App.plive.hash, exportado: App.plive.exportado } : null;   // the live export this proposal was made on
  try {
    const r = await fetch('/api/partitura/propuesta', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(P) });
    const j = await r.json(); if (!r.ok) throw new Error(j.error || r.status);
    App.prop = P; UI.renderLibrary(); UI.renderInspector(); UI.renderTop(); toast(msg + ' · obra/unreal/partitura_propuesta.json');
  } catch (e) { toast('Could not save the proposal: ' + e.message); }
}

/* ---------- save / load ---------- */
let _draftT = 0;
/* the score changed (an edit, undo or redo). "Unsaved" is honest (audit C14): only while it differs from the last score
   saved or loaded; undoing back to it is clean again: no badge, no prompt on close, no draft kept */
function markDirty() {
  App.dirty = !Edits.sameScore(App.score, App.savedScore); App.edited = true; App.editSeq = (App.editSeq || 0) + 1;
  if (App.view === '3d') return;   // the 3D tab never writes the draft
  clearTimeout(_draftT);
  if (!App.dirty) { try { localStorage.removeItem(LS_DRAFT); } catch (_) {} }
  _draftT = setTimeout(() => { if (App.dirty) lsSet(LS_DRAFT, { baseRev: App.baseRev, baseHash: App.diskHash, savedAt: Date.now(), score: App.score }); post({ score: App.score }); }, 400);
}
async function save(force) {
  if (App.view === '3d') return toast('Save from the timeline tab.');
  if (App.saving) return; if (App.cardOpen) return toast('Finish the open decision first');
  const next = JSON.parse(JSON.stringify(App.score)); next.rev = (App.baseRev || 1) + 1; next.savedBy = App.who; next.savedAt = new Date().toISOString();
  // the rules of the piece first (js/check.js: the same module the server runs with node, tools/score/check.mjs): a score that
  // breaks one is not even sent. Not even with force: that only skips the conflict, never the rules
  const rules = checkScore(next, App.savedScore);
  if (rules && !rules.ok) return ruleCard(rules.errors);
  const seq = App.editSeq || 0; App.saving = true;
  try {
    const r = await fetch('/api/score', { method: 'PUT', headers: { 'Content-Type': 'application/json', 'X-Base-Rev': String(App.baseRev || 0), 'X-Base-Hash': App.diskHash || '', 'X-Force': force ? '1' : '0' }, body: JSON.stringify(next) });
    const j = await r.json();
    if (r.status === 409 && j.code !== 'schema-down') { App.saving = false; return conflict(j); }
    if (r.status === 422 && j.code === 'invariants') { App.saving = false; return ruleCard(j.errors); }   // the server found one the editor did not (another base)
    if (!r.ok) throw new Error(j.error || r.status);
    App.score.rev = next.rev; App.score.savedBy = next.savedBy; App.score.savedAt = next.savedAt;
    App.baseRev = next.rev; App.diskHash = j.hash || null; App.savedAt = j.saved; App.savedScore = JSON.parse(JSON.stringify(next));
    if ((App.editSeq || 0) === seq) { App.dirty = false; try { localStorage.removeItem(LS_DRAFT); } catch (_) {} }   // an edit made while saving stays unsaved
    else markDirty();
    // saved, but the server could not run the full check (no node, VVR_CHECK=off, a timeout): said, never silent
    UI.renderTop(); UI.renderStatus(); toast(j.check && j.check !== 'full' ? `Saved without the full check (${j.checkWhy || j.check}) · rev ${next.rev}` : 'Saved · rev ' + next.rev + ' · obra/score/score.json');
  } catch (e) { toast('Could not save: ' + e.message); }
  App.saving = false;
}
/* the invariants of a score against the one it replaces (js/check.js); null when the check itself could not run: the server
   still checks, and a broken check never stops the work */
function checkScore(score, base) {
  try { return window.Check ? Check.invariants(score, base, { Engine: ScoreEngine, Edits, contract: App.contract, knobs: Check.knobNames(App.pdef, App.perillas) }) : null; } catch (_) { return null; }
}
/* a rule of the piece is broken (found here, or by the server with a 422): nothing was written, score.json is as it was, and the
   work is never lost: it can be kept as a copy (obra/score/copias/, which does not judge it) while it is fixed */
function ruleCard(errors) {
  errors = errors || [];
  const shown = errors.slice(0, 6), more = errors.length - shown.length, first = errors.find(e => (e.ids || []).length);
  const body = 'Nothing was saved: score.json is as it was.\n' + shown.map(e => `• ${e.msg} (${e.code})`).join('\n') + (more > 0 ? `\n… and ${more} more` : '');
  UI.chooseCard('This score breaks a rule', body, [
    { id: 'copy', primary: true, label: 'Save a copy of my version', detail: 'It goes to obra/score/copias/. You keep editing; the score on disk stays as it is.' },
    ...(first ? [{ id: 'show', label: 'Show me the first one', detail: 'Selects it in the timeline so you can fix it. Ctrl+Z undoes your last edit.' }] : []),
  ], async c => {
    if (c === 'show') return UI.goto(first.ids[0]);
    const path = await saveCopy(App.score, 'rule-broken');
    toast(path ? 'Your version is safe in ' + path : 'Could not save the copy: nothing was changed');
  });
}
/* someone saved after you opened it: say who, and let you choose (A2) */
function conflict(j) {
  const who = j.savedBy ? ` by ${j.savedBy}` : '', when = j.savedAt ? ' at ' + String(j.savedAt).replace('T', ' ').slice(0, 16) : '';
  UI.chooseCard('Someone saved after you', `obra/score/score.json is now rev ${j.rev}${who}${when}. You opened rev ${App.baseRev}. Saving now would erase their work.`, [
    { id: 'copy', primary: true, label: 'Keep both: save mine as a copy and open theirs', detail: 'Your version goes to obra/score/copias/; you can compare and bring over what you need.' },
    { id: 'mine', label: 'Save mine as a copy and keep working on it', detail: 'Nothing is overwritten; the score on disk stays theirs.' },
    { id: 'force', danger: true, label: 'Overwrite theirs with mine', detail: 'Their version stays only in obra/score/history/.' },
  ], async c => {
    if (c === 'force') return save(true);
    const path = await saveCopy(App.score, 'conflict');
    if (!path) return toast('Could not save the copy: nothing was changed');
    if (c === 'copy') { App.dirty = false; try { localStorage.removeItem(LS_DRAFT); } catch (_) {} toast('Your version: ' + path + ' · opening theirs'); setTimeout(() => location.reload(), 900); }
    else toast('Your version is safe in ' + path);
  });
}
async function reloadFromDisk() { try { localStorage.removeItem(LS_DRAFT); } catch (_) {} location.reload(); }
function exportScore() { const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([JSON.stringify(App.score, null, 1)], { type: 'application/json' })); a.download = 'score-rev' + App.baseRev + '.json'; a.click(); }
function importScore(file) {
  if (busy()) return;
  file.text().then(t => {
    const s = JSON.parse(t); const r = Edits.validate(s, ScoreEngine);   // never assign something that does not compute (A9); schema 2 and 3
    // the schema only goes up (the server refuses an older score over a newer one): an older file would be refused at the first save
    if (s.schema < App.score.schema) return toast(`${file.name} is a schema ${s.schema} score and this one is schema ${App.score.schema}: an older score can't replace it. Nothing was imported`);
    // the same rules the save will ask (js/check.js), against the score it would replace: a file that breaks one could never be saved
    const rules = checkScore(s, App.score);
    if (rules && !rules.ok) return toast(`${file.name} breaks a rule: ${rules.errors[0].msg}${rules.errors.length > 1 ? ` (and ${rules.errors.length - 1} more)` : ''} Nothing was imported`);
    // the card names everything the import replaces, not only the elements; the bookmarks, notes, accepted problems and
    // values waiting for Unreal that the file does not have are the team's, and can stay (logic and tests: js/edits.js)
    const d = Edits.importDiff(App.score, s), w = Edits.importWords(d);
    const nd = d.elements.added.length + d.elements.changed.length, gone = d.elements.gone.length, one = d.ownGone === 1;
    const body = `It replaces the whole score: ${nd} element${nd === 1 ? ' differs' : 's differ'}, ${gone} would disappear, total ${Integrity.fmt(App.schedT.total)} → ${Integrity.fmt(r.total)}.`   // minutes and seconds as everywhere else (18.17 min read as 18:17; it is 18:10)
      + (s.schema > App.score.schema ? ` The file is schema ${s.schema}: the score becomes schema ${s.schema} (an older editor can't save over it).` : '')
      + (w.also ? ` It also replaces: ${w.also}.` : '') + (w.base ? ' ' + w.base : '') + (w.unbound ? ' ' + w.unbound : '') + (w.own ? ` Not in the file: ${w.own}.` : '') + (w.other ? ' ' + w.other : '') + ' You can undo it.';
    const opts = d.ownGone ? [
      { id: 'keep', primary: true, label: `Import it and keep ${w.own}`, detail: 'They are the team\'s, not the file\'s. Everything else comes from the file.' },
      { id: 'import', label: 'Import it as it is', detail: `${w.own} ${one ? 'is' : 'are'} lost (Ctrl+Z brings ${one ? 'it' : 'them'} back).` }]
      : [{ id: 'import', primary: true, label: 'Import it' }];
    UI.chooseCard(`Import ${file.name}`, body, opts, c => {
      if (c !== 'import' && c !== 'keep') return;
      const src = c === 'keep' ? Edits.keepOwn(App.score, s) : s;
      commit('Import ' + file.name, { type: 'import', ids: [] }, n => { for (const k of Object.keys(n)) delete n[k]; Object.assign(n, src, { rev: App.score.rev }); });
    });
  }).catch(e => toast('Could not import: ' + e.message));
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
  let name = e.key;
  if (/^FX_NEW_SOUND/.test(name)) {   // a new name must not be another element's, nor a real sound of the piece (A11)
    const taken = new Set(Object.entries(App.score.elements).filter(([k]) => k !== id).flatMap(([, x]) => [x.key, x.sound]).filter(Boolean));
    name = cleanId(file.name); let i = 2; const base = name; while (taken.has(name)) name = base + '_' + (i++);
  }
  let uploaded = null;
  try { const r = await fetch('/api/audio?name=' + encodeURIComponent(id) + '&overwrite=1', { method: 'POST', body: buf }); const j = await r.json(); if (r.ok) uploaded = j.path; else toast('Upload: ' + j.error); } catch (_) {}
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
      if (d.branchView && App.view === '3d') { App.branchView = d.branchView; compute(); UI.renderTransport(); UI.renderViewerBar(); UI.renderStatus(); }   // the side of SHARE / DON'T SHARE on screen
      if (d.range) setRange({ inT: d.range[0], outT: d.range[1] }, null, true);
      if (d.t != null && (!App.playing || Math.abs(d.t - App.ph) > .25)) seek(d.t, true);
      // the speed and the direction travel too (J/K/L in either tab); a message without a rate keeps this tab's speed
      const f = Transport.follow(d, { playing: App.playing, rate: App.rate });
      if (f) play(f.on, true, f.rate);
    };
  } catch (_) {}
}
function post(m) { if (BC) try { BC.postMessage(Object.assign({ from: App.tab }, m)); } catch (_) {} }
function openSecondTab() { window.open(location.pathname + '?view=3d', '_blank'); }

/* ---------- toasts, keys ---------- */
let _toastT = 0;
function toast(msg) { App.toastSeq++; let t = document.querySelector('.toast'); if (!t) { t = document.createElement('div'); t.className = 'toast'; document.body.appendChild(t); } t.textContent = msg; t.style.display = 'block'; t.style.transform = `translateX(-50%) scale(${App.k || 1})`; clearTimeout(_toastT); _toastT = setTimeout(() => { t.style.display = 'none'; }, 3200); }
/* Alt+←/→ taps are gathered into one edit: one check, one undo step (audit B2); with several selected, all of them (C10) */
let _nudge = null;
function nudge(ids, dt) {
  ids = [].concat(ids); const key = ids.join(',');
  if (_nudge && _nudge.key !== key) flushNudge();
  if (!_nudge) _nudge = { ids, key, dt: 0 };
  _nudge.dt = +(_nudge.dt + dt).toFixed(3); clearTimeout(_nudge.t); _nudge.t = setTimeout(flushNudge, 650);
  UI.renderStatus(`${ids.length > 1 ? ids.length + ' clips' : (App.score.elements[ids[0]] || {}).key} ${_nudge.dt >= 0 ? '+' : ''}${_nudge.dt.toFixed(1)} s · release Alt to apply`);
}
function flushNudge() { const n = _nudge; _nudge = null; if (n) { clearTimeout(n.t); if (Math.abs(n.dt) > 1e-4) { if (n.ids.length > 1) Act.moveMany(n.ids, n.dt, false); else Act.move(n.ids[0], n.dt, null, false); } } }
function onKeyUp(e) {
  if (e.key === 'Alt' && _nudge) flushNudge();
  if ((e.key || '').toLowerCase() === 'k') App.kHeld = false;
}
function initKeys() {
  document.addEventListener('keyup', onKeyUp); document.addEventListener('keydown', onKey);
  addEventListener('blur', () => { App.kHeld = false; });   // K released somewhere else is not held here
  // focus traps (audit C14): a select or number field that just changed gives the keyboard back, so arrows move the playhead
  // again and Space plays (inside a decision card the keyboard stays with the card)
  document.addEventListener('change', ev => { const t = ev.target; if (t && t.matches && t.matches(STEPPER) && !t.closest('.ov') && document.activeElement === t) t.blur(); });
  // the wheel over a focused number field scrolls the panel; it never changes the value behind your back
  document.addEventListener('wheel', ev => { const a = document.activeElement; if (a && a.type === 'number' && a === ev.target) a.blur(); }, { capture: true, passive: true });
}
const STEPPER = 'select, input[type=number], input[type=checkbox], input[type=radio], input[type=range]';
/* a focused select keeps only the keys that choose in it; any other key is the editor's (←/→ never change a lane) */
const SELECT_KEYS = new Set(['ArrowUp', 'ArrowDown', 'Enter', 'Tab', 'Escape', 'F4', 'Shift', 'Control', 'Alt', 'Meta', 'CapsLock']);
/* the 3D view (its own tab, or Window ▸ 3D view) is read-only: only the transport keys work there (view3d, above commit) */
function onKey(e) {
  {
    let typing = e.target && e.target.closest && e.target.closest('input,textarea,select,[contenteditable=true]');
    if (typing && typing.tagName === 'SELECT' && !SELECT_KEYS.has(e.key) && !typing.closest('.ov')) { e.preventDefault(); typing.blur(); typing = null; }
    const mod = e.ctrlKey || e.metaKey, k = (e.key || '').toLowerCase();
    if (App.cardOpen && !typing) { if (e.key === 'Escape' && UI.closeOverlay) UI.closeOverlay(); else if (e.key !== 'Enter' && e.key !== 'Tab') e.preventDefault(); return; }
    // the list of shortcuts is open: Esc or ? closes it; Ctrl+S closes it and saves (never the browser's Save page);
    // any other key only scrolls it
    if (UI.helpOpen() && !typing) {
      if (e.key === 'Escape' || e.key === '?') { e.preventDefault(); UI.closeOverlay(); }
      else if (mod && k === 's') { e.preventDefault(); UI.closeOverlay(); if (!e.repeat) save(); }
      return;
    }
    if (mod && k === 's') { e.preventDefault(); if (!e.repeat) save(); return; }   // in the 3D tab it says where to save
    // C11: find in the timeline (never the browser's find); from any field too, except inside a decision card
    if (mod && k === 'f' && !e.altKey && !e.shiftKey) { e.preventDefault(); if (!App.cardOpen && !e.repeat) UI.openFind(); return; }
    if (App.pick && e.key === 'Escape') { e.preventDefault(); UI.endPick('Anchor not changed'); return; }   // picking an anchor in the timeline
    if (typing) { if (e.key === 'Escape') e.target.blur(); return; }
    if (e.key === '?') { e.preventDefault(); UI.shortcuts(); return; }
    // while picking, nothing else edits: not the mouse (onTimelineDown) and not the keys (delete, nudge, undo/redo, add,
    // bookmark, note, new lane). Transport, I/O, zoom, snapping, F8, A (show anchors) and Ctrl+S still work
    if (App.pick && (e.key === 'Delete' || e.key === 'Backspace' || (mod && (k === 'z' || k === 'y' || k === 'v' || k === 'd')) || (k === 'm' && !mod && !e.altKey)
        || (k === 'a' && e.shiftKey && !mod) || (e.altKey && (k === 't' || e.key === 'ArrowLeft' || e.key === 'ArrowRight')))) {
      e.preventDefault(); toast('Finish picking the anchor first (Esc cancels)'); return;
    }
    if (UI.closeOverlay && e.key === 'Escape' && UI.closeOverlay()) return;
    if (transportKey(e, k, mod)) return;
    if (view3d()) return;
    if (mod && k === 'z') { e.preventDefault(); e.shiftKey ? redo() : undo(); return; }
    if (mod && k === 'y') { e.preventDefault(); redo(); return; }
    // C10: select all in the moment, copy, paste at the playhead, duplicate (Ctrl+C with nothing selected stays the browser's)
    if (mod && k === 'a' && !e.altKey) { e.preventDefault(); selectMoment(); return; }
    if (mod && k === 'c' && !e.altKey) { if (selIds().length) { e.preventDefault(); Act.copy(); } return; }
    if (mod && k === 'v' && !e.altKey) { e.preventDefault(); if (!e.repeat) Act.paste(); return; }
    if (mod && k === 'd' && !e.altKey) { e.preventDefault(); if (!e.repeat) Act.duplicate(); return; }
    if (e.key === 'F8') { e.preventDefault(); App.drawer = App.drawer === 'problems' ? null : 'problems'; UI.renderDrawer(); UI.renderTransport(); return; }
    if (k === 'a' && e.shiftKey && !mod) { e.preventDefault(); UI.quickAdd(); return; }
    if (k === 'a' && !e.shiftKey && !mod && !e.altKey) { App.showAnchors = !App.showAnchors; UI.renderTimelineSelection(); UI.renderTransport(); return; }
    if (k === 'm' && !mod && !e.altKey) { e.preventDefault(); e.shiftKey ? UI.noteBox() : Act.bookmark(); return; }
    if (e.altKey && k === 't') { e.preventDefault(); const g = App.selKind === 'el' && App.score.elements[App.sel] ? App.score.elements[App.sel].group : 'fx'; Act.newLane(g); return; }
    if ((e.key === 'Delete' || e.key === 'Backspace') && App.selKind === 'el') { e.preventDefault(); Act.remove(selIds()); return; }
    if (e.altKey && (e.key === 'ArrowLeft' || e.key === 'ArrowRight') && App.selKind === 'el') { e.preventDefault(); nudge(selIds(), (e.key === 'ArrowLeft' ? -1 : 1) * (e.shiftKey ? 1 : .1)); return; }
    // the view of the timeline (Premiere's keys): snapping, zoom around the playhead, fit the piece
    if (k === 's' && !mod && !e.altKey && !e.shiftKey) { e.preventDefault(); toggleSnap(); return; }
    if (!mod && !e.altKey && (e.key === '=' || e.key === '+')) { e.preventDefault(); UI.zoomAt(1.4); return; }
    if (!mod && !e.altKey && (e.key === '-' || e.key === '_')) { e.preventDefault(); UI.zoomAt(1 / 1.4); return; }
    if (e.key === '\\') { e.preventDefault(); UI.fit(); return; }   // with any modifier: on some layouts \ is AltGr+key
    if (e.key === 'Escape') select(null);
  }
}
/* the keys that only play or move the playhead (and the play range): they work everywhere, the 3D view included */
function transportKey(e, k, mod) {
  if (e.key === ' ') { e.preventDefault(); play(!App.playing); return true; }
  if (e.key === 'Home') { seek(0); return true; }
  if (e.key === 'End') { seek(App.sched.total); return true; }
  // ←/→ move the playhead; Alt+←/→ with a clip selected nudges it instead (an edit: the timeline handles it)
  if ((e.key === 'ArrowLeft' || e.key === 'ArrowRight') && !(e.altKey && App.selKind === 'el' && !view3d())) {
    e.preventDefault(); seek(App.ph + (e.key === 'ArrowLeft' ? -1 : 1) * (e.shiftKey ? 1 : .1)); return true;
  }
  if (mod) return false;
  if ((e.key === 'ArrowUp' || e.key === 'ArrowDown') && !e.altKey) { e.preventDefault(); stepMoment(e.key === 'ArrowUp' ? -1 : 1); return true; }
  if (e.altKey) { if (k === 'x' || e.code === 'KeyX') { e.preventDefault(); clearRange(); return true; } return false; }
  if (k === 'l' || k === 'j') { e.preventDefault(); shuttle(k === 'l' ? 1 : -1); return true; }
  if (k === 'k') { e.preventDefault(); if (!e.repeat) { App.kHeld = true; if (App.playing) play(false); } return true; }
  if (k === 'i' || k === 'o') {
    e.preventDefault();
    if (!e.shiftKey) { k === 'i' ? markIn() : markOut(); return true; }
    const t = k === 'i' ? App.inT : App.outT;   // Shift+I / Shift+O: go to In / Out
    if (t == null) toast(`No ${k === 'i' ? 'In' : 'Out'} marked · ${k.toUpperCase()} marks it at the playhead`); else { seek(t); UI.revealTime(t); }
    return true;
  }
  return false;
}
window.App = App; window.Act = Act;
window.addEventListener('beforeunload', e => { if (App.dirty && App.view !== '3d') { e.preventDefault(); e.returnValue = ''; } });
document.addEventListener('DOMContentLoaded', boot);
