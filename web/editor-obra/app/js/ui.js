/* Soul Charger editor · UI: everything that is drawn, and the pointer. State and edits live in app.js (App, Act, commit);
   this file never changes the score by itself, it always calls Act. Markup follows the ISP/VEATION classes (css/isp.css). */
(function () {
  'use strict';
  const HDR = 168;                                   // lane header width (ISP .trackhdr)
  // lane height (audit C11, a preference): compact is the dense default; comfortable gives each clip a second line
  const LANE_H = { compact: { vo: 36, fx: 22, amb: 22, hap: 22, def: 26 }, comfortable: { vo: 56, fx: 30, amb: 30, hap: 30, def: 40 } };
  const laneH = g => { const L = LANE_H[App.laneSize] || LANE_H.compact; return L[g] || L.def; };
  const X = t => t * App.pps;
  const ICON = { wait: 'hourglass', vo: 'wave', sound: 'sound', ambience: 'sound', haptic: 'haptic', path: 'walk', world: 'world', object: 'obj', instruction: 'ghost', interaction: 'logic' };
  const KIND = { wait: 'Wait', vo: 'Voice', sound: 'Sound', ambience: 'Ambience', haptic: 'Haptic', path: 'Path', world: 'World', object: 'Object', instruction: 'Instruction', interaction: 'Interaction' };
  const WHO = { B: { n: 'Beltrán', c: '#8468BE' }, S: { n: 'Partner', c: '#4E78B3' } };
  const KINDTXT = { literal: 'Hardwired in Unreal', wired: 'Wired in Unreal', knob: 'Knob in Unreal', partitura: 'Partitura knob in Unreal', 'not-blocking': 'Different in Unreal', 'not-in-unreal': 'Not in Unreal yet' };
  // Simple says "Set by Unreal" where Advanced says "Wired in Unreal" (js/simple.js); the keys (wired, cue, preview...) never change
  const kindWord = k => ((App.adv ? KINDTXT : Simple.KIND_WORD)[k] || k);
  /* Simple mode: whatever reaches the screen (panels, cards, toasts, tooltips) speaks of the headset, not of the "APK".
     One observer instead of touching every message; the timeline itself is skipped (its chip already shows only ≠). */
  function plainPass(root) {
    if (App.adv || !root || !root.querySelectorAll) return;
    const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    for (let n = w.nextNode(); n; n = w.nextNode()) if (n.nodeValue.indexOf('APK') >= 0 && !(n.parentElement && n.parentElement.closest('#tlc'))) n.nodeValue = Simple.plainWords(n.nodeValue);
    for (const e of root.querySelectorAll('[title*="APK"]')) e.title = Simple.plainWords(e.title);
    if (root.title && root.title.indexOf('APK') >= 0) root.title = Simple.plainWords(root.title);
  }
  let _plainQ = null;
  new MutationObserver(ms => {
    if (App.adv) return;
    for (const m of ms) { const t = m.type === 'characterData' ? m.target.parentElement : m.target; if (t && !t.closest('#tlc')) (_plainQ = _plainQ || new Set()).add(t); }
    if (_plainQ && !_plainQ._sched) { _plainQ._sched = true; queueMicrotask(() => { const q = _plainQ; _plainQ = null; for (const t of q) if (t.isConnected) plainPass(t); }); }
  }).observe(document.documentElement, { childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ['title'] });
  const DIFFERS = 'Differs from what the headset build does today';   // the ≠ APK chip and mark, in Simple
  const previewChip = () => `<span class="chip lit">${App.adv ? 'preview' : 'only in the preview'}</span>`;
  const fmtMS = t => { t = Math.max(0, t); const m = Math.floor(t / 60), s = Math.floor(t - m * 60); return m + ':' + String(s).padStart(2, '0'); };
  const persona = () => ScoreEngine.PERSONAS[App.persona];
  // the side of each decision on screen in words ("SHARE"), '' for a score with no branches (schema 2)
  const sideText = () => App.sched.branch ? Integrity.branchText(App.score, App.sched.branch) : '';
  const El = id => App.score.elements[id];
  let laneTop = {}, groupTop = {}, booted = false;

  /* colour of the text on a group colour (ISP textOn) */
  const _lum = h => { const c = [1, 3, 5].map(i => { const v = parseInt(h.slice(i, i + 2), 16) / 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }); return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]; };
  const textOn = h => { const L = _lum(h), LD = _lum('#0E0F11'), LL = _lum('#F2F4F8'); return (Math.max(L, LD) + .05) / (Math.min(L, LD) + .05) >= (Math.max(L, LL) + .05) / (Math.min(L, LL) + .05) ? '#0E0F11' : '#F2F4F8'; };
  const hueOf = gid => (App.score.groups.find(g => g.id === gid) || {}).hue || App.HUE[gid] || '#777777';
  const isInstant = e => !e.gate && !e.end && (!e.dur || e.dur.mode === 'instant' || !(e.dur.value > 0));
  const hasAudio = View.hasAudio;   // a new wait is new but no sound: no WAV to load, not in the Library's Sounds, no "new sound" in the status bar
  const roleFor = e => Edits.roleOf(App.roles, e);   // the same rule "Bind to Unreal" uses for the target of a bind
  function pbMap() { const m = {}; for (const p of App.problems) if (p.el && p.st === 'open' && (p.sv === 'block' || p.sv === 'warn')) { if (m[p.el] !== 'block') m[p.el] = p.sv; } return m; }
  function pbCounts() { const o = App.problems.filter(p => p.st === 'open'); return { b: o.filter(p => p.sv === 'block').length, w: o.filter(p => p.sv === 'warn').length, i: o.filter(p => p.sv === 'info').length, a: App.problems.filter(p => p.st === 'accepted').length }; }
  // what "to review" counts: Simple counts what the Problems list opens on, with the comparison with the last Unreal run as ONE item (js/simple.js); Advanced counts every block and warning
  const attention = k => App.adv ? k.b + k.w : Simple.review(App.problems).count;
  const keyOf = id => (App.score.beats[id] || El(id) || {}).key || id || '—';
  // the "Unreal run" lane (lote 5): 12 px under the moments band, when there is a run and it is not hidden
  const runShown = () => !!(App.runLane && App.runView);
  const headH = () => 58 + (runShown() ? 12 : 0);   // the sticky ruler block: acts 18 + time 24 + moments 16 (+ the run)
  function timeFromClient(cx) { const sc = $('#sctl'), r = sc.getBoundingClientRect(); return Math.max(0, ((cx - r.left) / App.k + sc.scrollLeft - HDR) / App.pps); }

  /* ================= top bar + menus ================= */
  function renderTop() {
    const P = persona();
    $('#top').innerHTML = `<img class="vvrmark" src="brand/veation-vr-marca.svg" width="14" height="14" alt="Veation VR Studio" title="Veation VR Studio"><div class="menubar">${['File', 'Edit', 'Experience', 'Window', 'Help'].map(m => `<button class="menubtn" data-menu="${m}">${m}</button>`).join('')}</div><div style="flex:1;"></div>
      <div class="well" title="Window layout">${[['all', 'All-in-one'], ['v3d', '3D view'], ['tl', 'Timeline']].map(([k, l]) => `<button data-win="${k}" class="${App.mode === k ? 'on' : ''}">${l}</button>`).join('')}</div>
      <button class="who" data-who title="Who edits on this computer: signs notes and accepted breaks · click to switch"><i style="background:${WHO[App.who].c}">${App.who}</i>${WHO[App.who].n}</button>
      ${syncPill()}
      <span style="font-size:11px;font-weight:600;letter-spacing:-0.008em;color:var(--ink-2);white-space:nowrap;margin-left:6px;">Soul Charger · Experience</span>
      <span class="tnum savest${App.dirty ? ' dirty' : ''}"${App.adv ? '' : ` title="Score revision ${App.baseRev}"`}>${App.adv ? `rev ${App.baseRev}${App.dirty ? ' · unsaved' : ''} · ` : App.dirty ? 'unsaved · ' : ''}${P.name.toLowerCase()}${sideText() ? ' ' + esc(sideText()) : ''} ${Integrity.fmt(App.sched.total)}</span>`;
  }
  function sentState() {
    const P = App.prop || {}; if (!P.estado) return null;
    const when = String(P.aplicado || P.rechazado || P.enviado || '').replace('T', ' ').slice(5, 16);
    if (P.estado === 'enviada') return { cls: 'wait', txt: 'Sent ' + when + ' · waiting for Unreal' };
    if (P.estado === 'aplicada') return { cls: 'ok', txt: 'Applied in Unreal ' + when };
    if (P.estado === 'rechazada') return { cls: 'bad', txt: 'Not applied ' + when + (P.motivo_rechazo ? ': ' + P.motivo_rechazo : '') };
    return { cls: 'wait', txt: P.estado };
  }
  function syncPill() {
    const npend = Object.keys(pendingVals()).length, st = sentState();
    const send = npend ? `<button class="crbtn pri" data-send title="Review the ${npend} change${npend > 1 ? 's' : ''} waiting, then send them to Unreal. Nothing reaches Unreal before this.">${ICO('upload', 11)}<span class="crlbl" style="display:inline;">Send to Unreal · ${npend}</span></button>` : '';
    const stc = st && st.cls !== 'ok' ? `<span class="sendst ${st.cls}" data-lib-go="timing" title="${esc(st.txt)}">${esc(st.txt)}</span>` : '';
    if (!App.plive) return `<span class="syncpill" title="${App.adv ? 'No export of DA_Partitura_Obra yet (obra/unreal/partitura.json). The director publishes it with tools/unreal/partitura_export.py.' : 'Unreal has not published its timing yet, so the score cannot be compared with it. Whoever works in Unreal publishes it.'}"><span class="sd"></span>Unreal: no export yet</span>${stc}${send}`;
    const off = Object.keys(App.pOff || {}).length;
    const when = String(App.plive.exportado || '').replace('T', ' ').slice(5, 16);
    // Simple says it in words: this is the timing the headset build runs on, and whether the score agrees with it
    const tip = App.adv ? `Timing of the piece in Unreal: DA_Partitura_Obra, exported ${esc(App.plive.exportado)} (hash ${esc(App.plive.hash)}). ${off} knobs differ from the score. Click to open the Timing tab.`
      : `The waits and pauses the headset build runs on, as Unreal last published them (${esc(when)}). ${off ? `${off} of these settings differ from the score, so the headset would not time the piece the way you see it here: the Timing tab shows which, and how to match them.` : 'They match the score: the headset times the piece the way you see it here.'} Click to open the Timing tab. Nothing reaches Unreal until you press Send to Unreal.`;
    return `<button class="syncpill" data-lib-go="timing" title="${tip}"><span class="sd" style="background:${off ? 'var(--auto-ovr)' : '#9CCBB3'}"></span>Unreal timing · ${esc(when)}${off ? ` · ${off} ≠` : ' · in sync'}</button>${stc}${send}`;
  }
  function menuItems(name) {
    // the 3D view is read-only (its tab, or Window ▸ 3D view): what would edit the score is shown, but disabled
    const sel = App.selKind === 'el' && El(App.sel), ro = view3d();
    if (name === 'File') return [
      ['Save', 'Ctrl+S', save], ['Export score…', '', exportScore], ['Import score…', '', () => $('#jsonIn').click(), { dis: ro }],
      ['Check guion.js for changes…', App.score.schema >= 3 ? '' : 'schema 2: report only', () => Act.guionCheck(), { dis: ro }],
      'sep', ['Reload from disk', 'discards unsaved', () => { if (!App.dirty || confirm('Discard your unsaved changes and reload score.json?')) reloadFromDisk(); }],
      'sep', ['Open the 3D view in a new tab', '', openSecondTab]];
    if (name === 'Edit') return [
      ...(ro ? [{ head: 'The 3D view only plays: edit in the timeline' }] : []),
      ['Undo', 'Ctrl+Z', undo, { dis: ro || !App.undo.length }], ['Redo', 'Ctrl+Shift+Z', redo, { dis: ro || !App.redo.length }],
      'sep', ['Copy', 'Ctrl+C', () => Act.copy(), { dis: ro || !sel }], ['Paste at the playhead', 'Ctrl+V', () => Act.paste(), { dis: ro || !App.clipboard }],
      ['Duplicate', 'Ctrl+D', () => Act.duplicate(), { dis: ro || !sel }], ['Select all in this moment', 'Ctrl+A', () => selectMoment(), { dis: ro }],
      ['Find…', 'Ctrl+F', () => openFind(), { dis: App.view === '3d' }],
      'sep', ['Add at the playhead…', 'Shift+A', () => quickAdd(), { dis: ro }], ['New lane', 'Alt+T', () => Act.newLane(sel ? sel.group : 'fx'), { dis: ro }],
      ['Delete selection', 'Del', () => sel && Act.remove(selIds()), { dis: ro || !sel, danger: true }],
      'sep', ['Bookmark at the playhead', 'M', () => Act.bookmark(), { dis: ro }], ['Note for the team', 'Shift+M', () => noteBox(), { dis: App.view === '3d' }]];
    // asset and file names in the hints are for Advanced; Simple says the thing in words (or nothing)
    if (name === 'Experience') return [['Match the score to Unreal timing', App.adv ? 'DA_Partitura_Obra' : '', () => Act.syncAll(), { dis: ro || !App.pbind }],
      ['Bind to Unreal…', Act.bindStatus().hint, () => Act.bindUnreal(), { dis: ro || !Act.bindStatus().can }], 'sep', { head: 'Simulated user' }, ...Object.entries(ScoreEngine.PERSONAS).map(([k, p]) => [p.name, p.note, () => setPersona(k), { on: App.persona === k }]),
      ...branchMenu(),
      'sep', ['Problems', 'F8', () => toggleDrawer()], ['Show anchors', 'A', () => { App.showAnchors = !App.showAnchors; renderTimelineSelection(); renderTransport(); }, { on: App.showAnchors }],
      ['Snapping', 'S', () => toggleSnap(), { on: App.snap }]];
    if (name === 'Window') return [['All-in-one', '', () => setMode('all'), { on: App.mode === 'all' }], ['3D view', '', () => setMode('v3d'), { on: App.mode === 'v3d' }], ['Timeline', '', () => setMode('tl'), { on: App.mode === 'tl' }],
      'sep', { head: 'Lane height' }, ['Compact', '', () => setLaneSize('compact'), { on: App.laneSize !== 'comfortable' }], ['Comfortable', 'a second line', () => setLaneSize('comfortable'), { on: App.laneSize === 'comfortable' }],
      'sep', ['Unreal run lane', App.run ? (App.adv ? 'obra/unreal/traza.json' : '') : 'no Unreal run yet', () => setRunLane(!App.runLane), { on: !!(App.runLane && App.run), dis: !App.run }],
      'sep', ['Show technical details', App.adv ? 'on' : 'off', () => setAdvanced(!App.adv), { on: App.adv }],
      'sep', ['Open the 3D view in a new tab', '', openSecondTab]];
    if (name === 'Help') return [['Quick start', '', () => quickStart()], ['Keyboard shortcuts', '?', () => shortcuts()]];
    return [];
  }
  /* ================= branches (lote 5, design B §5.3) =================
     Which side of each decision (SHARE / DON'T SHARE) the timeline and the 3D show: a preference, never the score. Auto follows
     the simulated user (the one that hits every timeout takes Unreal's own timeout answer). A score with no branches (schema 2)
     shows every side together and says how to get the selector */
  function branchItems(on) {
    const br = App.score.branches[on], v = App.branchView[on];
    const tot = o => o === br.default ? App.schedT.total : ((App.schedAlt.find(a => a.k === on + '=' + o) || {}).sched || {}).total;
    return [['Auto', "the simulated user decides · Idle takes Unreal's timeout answer", () => setBranchView(on, 'auto'), { on: v === 'auto' }]]
      .concat(Object.keys(br.options).map(o => [optionName(on, o), (o === br.default ? 'default · ' : '') + 'typical ' + Integrity.fmt(tot(o) || 0), () => setBranchView(on, o), { on: v !== 'auto' && (v || br.default) === o }]));
  }
  function branchMenu() {
    const brs = App.score.branches;
    if (!brs) return ['sep', { head: 'Branch' }, ['Both together', 'Upgrade to schema 3 to see one branch at a time', () => {}, { dis: true }]];
    const out = [];
    for (const on of Object.keys(brs)) out.push('sep', { head: brs[on].name }, ...branchItems(on));
    return out;
  }
  function openBranchMenu(btn) {
    const on = btn.dataset.branchdd, br = App.score.branches && App.score.branches[on]; if (!br) return;
    const r = btn.getBoundingClientRect();
    openMenu(r.left, r.bottom + 2, [{ head: br.name }, ...branchItems(on)], 290);
  }
  function branchCtl() {
    const brs = App.score.branches;
    if (!brs) return `<span class="plabel">Branch</span><button class="ddbtn" disabled title="Upgrade to schema 3 to see one branch at a time (Problems ▸ Upgrade…). Until then the timeline shows every side of SHARE and DON'T SHARE together."><span>Both together</span></button>`;
    const many = Object.keys(brs).length > 1;
    return Object.keys(brs).map(on => {
      const br = brs[on], v = App.branchView[on], shown = optionName(on, App.sched.branch[on]);
      return `<span class="plabel">${esc(many ? br.name : 'Branch')}</span><button class="ddbtn${v ? ' on' : ''}" data-branchdd="${esc(on)}" title="${esc(br.name + ': which side the timeline and the 3D show. Auto follows the simulated user (the one that hits every timeout takes Unreal\'s own answer). Nothing in the score changes.')}"><span>${esc((v === 'auto' ? 'Auto · ' : '') + shown)}</span><span style="display:flex;color:var(--ink-3);">${ICO('chevDown', 9)}</span></button>`;
    }).join('');
  }

  function openMenu(x, y, items, minW) {
    closeOverlay();
    const m = document.createElement('div'); m.className = 'menu ov'; m.style.left = x + 'px'; m.style.top = y + 'px'; if (minW) m.style.minWidth = minW + 'px';
    const fns = [];
    m.innerHTML = items.map(it => {
      if (it === 'sep') return '<div class="sep"></div>';
      if (it.head) return `<div class="mh">${esc(it.head)}</div>`;
      const [label, k, fn, o0] = it, o = o0 || {}; fns.push(fn);
      return `<button data-mi="${fns.length - 1}" class="${o.on ? 'on' : ''}${o.danger ? ' danger' : ''}"${o.dis ? ' disabled' : ''}>${o.sw ? `<span class="sw" style="background:${o.sw}"></span>` : ''}${esc(label)}${k ? `<span class="k">${esc(k)}</span>` : ''}</button>`;
    }).join('');
    document.body.appendChild(m); scaleOv(m);
    const r = m.getBoundingClientRect();
    if (r.bottom > innerHeight - 6) m.style.top = Math.max(4, y - r.height - 4) + 'px';
    if (r.right > innerWidth - 6) m.style.left = Math.max(4, innerWidth - r.width - 6) + 'px';
    m.addEventListener('click', e => { const b = e.target.closest('[data-mi]'); if (!b || b.disabled) return; closeOverlay(); fns[+b.dataset.mi](); });
    return m;
  }

  /* ================= library ================= */
  function soundIndex() {
    const m = new Map();
    for (const [id, e] of Object.entries(App.score.elements)) { const s = e.sound || (e.isNew && hasAudio(e) ? e.key : null); if (!s) continue; if (!m.has(s)) m.set(s, { id: s, uses: [], group: e.group, isNew: !!e.isNew, audio: e.audio }); m.get(s).uses.push(id); }
    return [...m.values()].sort((a, b) => (b.isNew - a.isNew) || a.id.localeCompare(b.id));
  }
  function renderLibrary() {
    const S = App.score, T = App.sched.t, q = (App.libQuery || '').toLowerCase().trim();
    const tabs = [['scenes', 'Scenes'], ['timing', 'Timing'], ['roles', 'Roles'], ['sounds', 'Sounds'], ['actions', 'Actions']].map(([k, l]) => `<button data-lib="${k}" class="${App.libTab === k ? 'on' : ''}" style="padding:0 8px;">${l}</button>`).join('');
    let rows = '';
    if (App.libTab === 'scenes') {
      S.acts.forEach((a, ai) => {
        const A = App.sched.acts[ai], open = App.openActs.has(a.id) || !!q;
        const beats = a.beats.filter(b => !q || (S.beats[b].key + ' ' + S.beats[b].title).toLowerCase().includes(q));
        if (q && !beats.length) return;
        rows += `<div class="mitem click" data-actrow="${a.id}"><span class="tw">${ICO(open ? 'chevDown' : 'chevR', 10)}</span><span class="mdot" style="background:#5E6570"></span><div class="mtxt"><span class="mname">${esc(a.name)}</span><span class="mmeta">${fmtMS(A.s)} · ${a.beats.length} moment${a.beats.length > 1 ? 's' : ''} · ${fmtMS(A.e - A.s)}</span></div></div>`;
        if (!open) return;
        for (const b of beats) {
          const B = S.beats[b], n = Object.values(S.elements).filter(e => e.beat === b).length;
          rows += `<div class="mitem click${App.selKind === 'beat' && App.sel === b ? ' sel' : ''}" data-beatrow="${b}"><span class="lvl"></span><span class="tw"></span><div class="mtxt"><span class="mname">${esc(B.key)} · ${esc(B.title)}</span><span class="mmeta">${tc(T[b][0])} · ${fmtS(T[b][1] - T[b][0])} s · ${n} item${n === 1 ? '' : 's'}</span></div></div>`;
        }
      });
    } else if (App.libTab === 'timing') {
      rows = timingRows(q);
    } else if (App.libTab === 'roles') {
      rows = Object.entries(App.roles.roles).filter(([n]) => !q || n.toLowerCase().includes(q)).map(([name, R]) => {
        const n = R.groups.reduce((a, g) => a + g.rows.length, 0);
        return `<div class="mitem click${App.selRole === name ? ' sel' : ''}" data-role="${esc(name)}"><div class="mthumb gl" style="background:${R.icon === 'alma' ? '#8468BE' : R.icon === 'sound' ? App.HUE.fx : R.icon === 'logic' ? App.HUE.int : App.HUE.obj};">${ICO(R.icon, 14)}</div><div class="mtxt"><span class="mname">${esc(name)}</span><span class="mmeta">${esc(R.actor)} · ${n} knob${n === 1 ? '' : 's'}</span></div><span class="chip ok">in Unreal</span></div>`;
      }).join('') + `<div class="knote">Read from Unreal by hand on ${esc(App.roles.verified || '—')}. Read-only until the bridge (phase F3).</div>`;
    } else if (App.libTab === 'sounds') {
      rows = soundIndex().filter(s => !q || s.id.toLowerCase().includes(q)).map(s => {
        const kind = s.group === 'vo' ? 'VO' : s.group === 'amb' ? 'Ambience' : s.group === 'hap' ? 'Haptic' : 'FX';
        const meta = s.isNew ? `${kind} · ${s.audio ? esc(s.audio.file) : 'no file yet'}` : `${kind} · used ${s.uses.length}×`;
        const chip = s.isNew ? '<span class="chip prov">not in Unreal</span>' : s.group === 'hap' ? previewChip() : '';
        return `<div class="mitem click${App.selKind === 'el' && s.uses.includes(App.sel) ? ' sel' : ''}" data-snd="${esc(s.uses[0])}"><div class="mthumb gl" style="background:${s.isNew ? 'var(--s2)' : hueOf(s.group)};${s.isNew ? 'color:var(--auto-ovr);' : ''}">${ICO(s.isNew ? 'sound' : 'wave', 14)}</div><div class="mtxt"><span class="mname">${esc(s.id)}</span><span class="mmeta">${meta}</span></div>${chip}</div>`;
      }).join('');
    } else {
      const A = [['sound', 'Empty sound', 'Name it, load a WAV · goes to Unreal on the next import', 'sound'], ['wave', 'Alma voice line', 'Text now, audio later · lasts as long as its audio', 'vo'], ['hourglass', 'Wait', 'The user decides when it ends · needs a help line', 'wait'], ['flag', 'Bookmark', 'A named point in time · M', 'mark'], ['note', 'Note for the team', 'At the playhead · Shift+M', 'note']];
      rows = A.map(r => `<div class="mitem click" data-add="${r[3]}"><div class="mthumb gl" style="background:var(--s2);color:var(--ink-2);">${ICO(r[0], 14)}</div><div class="mtxt"><span class="mname">${r[1]}</span><span class="mmeta">${r[2]}</span></div></div>`).join('')
        + `<div class="knote">Every action adds at the playhead (${tc(App.ph)}), in the moment that contains it, on the first free lane of its group.</div>`;
    }
    const lib = $('#library'), list = lib.querySelector('.medialist'), st = list ? list.scrollTop : 0;
    lib.innerHTML = `<div class="panhead"><div class="pantab"><span style="color:var(--ink-3);display:flex;">${ICO('folder')}</span><span class="ttl">Library</span><span class="countbadge">${Object.keys(S.elements).length}</span></div></div>
      <div class="toolrow" style="height:28px;padding:0 8px;gap:8px;"><div class="well">${tabs}</div></div>
      <div class="toolrow crrow" style="height:28px;padding:0 8px;gap:4px;"><button class="crbtn pri" data-quick title="Add at the playhead · Shift+A">${ICO('plus')}<span class="crlbl" style="display:inline;">Add</span><span style="color:var(--ink-3);font-size:10px;margin-left:2px;">⇧A</span></button><button class="crbtn" data-add="sound" title="New empty sound: name it and load a WAV">${ICO('sound', 12)}<span class="crlbl" style="display:inline;">Sound</span></button><button class="crbtn" data-add="wait" title="New wait at the playhead">${ICO('hourglass', 12)}<span class="crlbl" style="display:inline;">Wait</span></button><button class="crbtn" data-add="note" title="Note at the playhead · Shift+M">${ICO('note', 12)}<span class="crlbl" style="display:inline;">Note</span></button></div>
      ${App.libTab === 'actions' ? '' : `<div class="toolrow" style="height:28px;padding:0 8px;"><input class="libsearch" id="libq" placeholder="Search ${App.libTab}" value="${esc(App.libQuery || '')}" spellcheck="false"></div>`}
      <div class="medialist">${rows}</div>`;
    lib.querySelector('.medialist').scrollTop = st;
  }

  /* the way to Unreal: what waits, what was sent and what happened to it */
  function timingSendBox() {
    const pend = pendingVals(), n = Object.keys(pend).length, st = sentState(), P = App.prop || {};
    let h = '<div class="sendbox">';
    h += n ? `<div class="sb-row"><b>${n} change${n > 1 ? 's' : ''} waiting</b><span>only in this score · not in Unreal</span></div><button class="crbtn pri" data-send style="margin:2px 0 4px;">${ICO('upload', 11)}<span class="crlbl" style="display:inline;">Review and send to Unreal…</span></button>`
      : '<div class="sb-row"><span>Nothing waiting for Unreal. Add changes from a knob.</span></div>';
    if (st) h += `<div class="sb-row sb-${st.cls}">${esc(st.txt)}</div>`;
    if (P.estado === 'aplicada' && P.respaldo) h += `<button class="crbtn" data-undo-unreal title="Put the values Unreal had before that change back on the waiting list (they still need Send)">Undo it in Unreal…</button>`;
    return h + '</div>';
  }
  /* the Partitura of the piece in Unreal (DA_Partitura_Obra): one row per knob */
  function timingRows(q) {
    if (!App.pdef) return '<div class="knote">No Partitura definition yet: run python tools/editor/sync_partitura.py</div>';
    const L = (window.Partitura && Partitura.liveValues(App.plive)) || {}, pend = pendingVals(), sent = (App.prop && App.prop.estado === 'enviada' && App.prop.valores) || {}, off = App.pOff || {};
    let out = `<div class="knote">${App.plive ? `DA_Partitura_Obra · exported ${esc(String(App.plive.exportado).replace('T', ' '))} · ${esc(App.plive.hash)}` : 'DA_Partitura_Obra · not exported yet: values the asset was created with'}. Unreal decides these times; the score follows, and proposes.</div>
      ${timingSendBox()}
      <div style="padding:0 7px 6px;"><button class="crbtn" data-psync title="Bring every bound element of the score to what Unreal does (one undoable edit)">${ICO('wire', 11)}<span class="crlbl" style="display:inline;">Match the score to Unreal</span>${Object.keys(off).length ? `<span style="color:var(--auto-ovr);margin-left:4px;">${Object.keys(off).length} ≠</span>` : ''}</button></div>`;
    let cat = null;
    for (const k of App.pdef.knobs) {
      if (q && !(k.name + ' ' + k.doc).toLowerCase().includes(q)) continue;
      if (k.category !== cat) { cat = k.category; out += `<div class="mh" style="padding:8px 7px 3px;font-size:10.5px;color:var(--ink-3);">${esc(cat.replace(/^\d+ /, ''))}</div>`; }
      const v = k.name in L ? L[k.name] : k.initial, bound = !!knobBind(k.name), o = off[k.name], p = k.name in pend;
      out += `<div class="mitem click${App.selKind === 'knob' && App.sel === k.name ? ' sel' : ''}" data-knob="${k.name}" title="${esc(k.doc)}"><div class="mtxt"><span class="mname">${k.name}</span><span class="mmeta tnum">${fmtV(v)} s${p ? ` → ${fmtV(pend[k.name])}` : ''}</span></div>${o ? '<span class="chip prov" title="The score does something else">≠ score</span>' : ''}${p ? '<span class="chip ok" title="Waiting to be sent">waiting</span>' : k.name in sent ? '<span class="chip lit" title="Sent, waiting for Unreal">sent</span>' : ''}${bound ? '' : '<span class="chip lit" title="No element of the score is bound to this knob yet">unbound</span>'}</div>`;
    }
    return out;
  }

  /* ================= viewer ================= */
  function renderViewerBar(msg) {
    const md = Object.values(App.media || {}), nv = Object.keys(App.media || {}).filter(k => /^VO_/.test(k)).length, nf = md.filter(m => m.src === 'fx').length;
    const stip = App.media ? `Sound in the 3D: the ${nv} recorded voices (final mix, earlier takes where there is no mix), ${nf} sound effects and ambiences from obra/audio/media_map.json, and the prototype's markers for the rest. A file never changes a time: it plays at its clip's time${App.mediaError ? ' · ' + App.mediaError : ''}`
      : 'Sound in the 3D: the prototype\'s markers (the editor\'s server gave no recordings or sound files)';
    $('#vptool').innerHTML = `<span style="display:flex;color:var(--ink-3);">${ICO('viewer')}</span><span class="vlab">3D preview · plays this score${App.SC ? '' : ' · loading…'}</span><div style="flex:1;"></div>
      <button class="crbtn${App.sound ? ' on' : ''}" data-sound title="${esc(stip)}">${ICO('sound', 12)}<span class="crlbl" style="display:inline;">Sound ${App.sound ? 'on' : 'off'}</span></button>
      ${App.view === '3d' ? '<span class="vlab">Read-only view · it follows the timeline tab, edit there</span>' : `<button class="crbtn" data-pop title="Open the 3D view in its own tab: it follows this playhead">${ICO('popout', 12)}<span class="crlbl" style="display:inline;">New tab</span></button>`}`;
    // what the 3D cannot show yet, said once, small
    const p3 = App.proto3d || {}, parts = [];
    if (App.persona !== 'typical') parts.push(`waits as the ${persona().name.toLowerCase()} user`);
    if (sideText() && Object.keys(App.branchView).length) parts.push(`showing ${sideText()}`);
    if (p3.notIn3d) parts.push(`${p3.notIn3d} new element${p3.notIn3d > 1 ? 's have' : ' has'} no 3D yet`);
    if (App.sound && App.voiceGaps && App.voiceGaps.length) parts.push(`${App.voiceGaps.length} voices sound longer or shorter than their clip (Problems)`);
    const v = $('#vmsg'), t = msg || (App.SC && parts.length ? '3D · ' + parts.join(' · ') : '');
    v.textContent = t; v.classList.toggle('on', !!t);
  }

  /* ================= transport ================= */
  function renderTransport() {
    const b = beatAt(App.ph), bs = App.sched.t[b][0], P = persona(), k = pbCounts();
    // J/K/L and I/O are keys, not buttons (plan §2.7): the transport only shows the speed and the range they set
    const spd = App.playing ? Transport.rateLabel(App.rate) : '', R = playBounds();
    const rng = R ? `<span class="rngchip tnum" title="Play range (I / O): Play starts at In when the playhead is outside it and stops at Out · Shift+I / Shift+O go to them · Alt+X clears">${App.inT != null ? 'In ' + tc(R[0]) : 'Start'} → ${App.outT != null ? 'Out ' + tc(R[1]) : 'end'}</span>` : '';
    $('#transport').innerHTML = `<div class="trl"><span class="plabel">Simulated user</span><button class="ddbtn" data-persdd title="How long the simulated user takes in each wait. Not an Unreal value."><span style="display:flex;color:var(--ink-3);">${ICO('person', 11)}</span><span>${P.name}</span><span style="display:flex;color:var(--ink-3);">${ICO('chevDown', 9)}</span></button>${branchCtl()}</div>
      <div class="tccenter"><button class="tbtn" data-tr="start" title="Go to start · Home">${ICO('toStart')}</button><button class="playb" data-tr="play" title="Play · Space · L forward, J backwards, K stops">${ICO(App.playing ? 'pause' : 'play')}</button><button class="tbtn" data-tr="end" title="Go to end · End">${ICO('toEnd')}</button><button class="tbtn${App.follow ? ' on' : ''}" data-tr="follow" title="Follow the playhead">${ICO('follow')}</button>
       <div class="tcbox"><span class="tc" id="tcv">${tc(App.ph)}</span>${spd ? `<span class="spd" title="${App.rate < 0 ? 'Playing backwards (J), without sound' : 'Playing faster (L)'} · K stops and goes back to 1×">${spd}</span>` : ''}<div class="trsep" style="width:.5px;height:14px;background:rgba(255,255,255,0.08);"></div><span class="rel" id="tcrel">+${fmtS(App.ph - bs)} s in ${esc(App.score.beats[b].key)}</span></div>
       ${rng}<button class="tbtn" data-tr="mark" title="Bookmark at the playhead · M" style="color:var(--ink-2);">${ICO('flag')}</button></div>
      <div style="flex:1;"></div>
      ${App.mode === 'v3d' ? '' : `<div class="trr"><div class="editseg"><button data-tr="snap" class="${App.snap ? 'on' : ''}" title="Snapping ${App.snap ? 'on' : 'off'} · S: a dragged clip, moment or bookmark snaps to clip edges, moments, bookmarks and the playhead">${ICO('snap', 11)}<span class="lb">Snap</span></button><button data-tr="anchors" class="${App.showAnchors ? 'on' : ''}" title="Anchor curves of the selection · A">${ICO('anchor', 11)}<span class="lb">Anchors</span></button><button data-tr="problems" class="${App.drawer === 'problems' ? 'on' : ''}" title="Problems · F8">${ICO('warn', 11)}<span class="lb">Problems</span>${attention(k) ? `<span style="color:var(--danger);">${attention(k)}</span>` : ''}</button></div>
      <div class="editseg zpre"><button data-tr="zmom" title="Zoom to fit the moment at the playhead (double-click a moment chip: that moment)">Moment</button><button data-tr="zact" title="Zoom to fit the act at the playhead">Act</button><button data-tr="fit" title="Fit the whole piece · \\">Piece</button></div>
      <div class="zoomgrp"><button data-tr="zout" title="Zoom out · - · Ctrl+wheel">${ICO('zoomOut')}</button><button data-tr="zin" title="Zoom in · = · Ctrl+wheel">${ICO('zoomIn')}</button></div></div>`}`;
    fitTransport();
  }
  /* the transport keeps its timecode centred (ISP) while everything fits; when the window is narrow it makes room, step
     by step: icons without words on the left of the zoom presets, then the timecode block flows after the simulated user,
     then the "+s in moment" goes. Measured only when the transport is drawn or the window resized (audit C11) */
  function fitTransport() {
    const tr = $('#transport'); if (!tr) return;
    tr.classList.remove('tr-icons', 'tr-flow', 'tr-norel');
    const c = tr.querySelector('.tccenter'), r = tr.querySelector('.trr'), l = tr.querySelector('.trl');
    if (!c || !r || !l || !tr.offsetWidth) return;
    const bad = () => { const C = c.getBoundingClientRect(), R = r.getBoundingClientRect(), L = l.getBoundingClientRect(), W = tr.getBoundingClientRect(); return C.left < L.right + 6 || R.left < C.right + 6 || R.right > W.right + .5; };
    for (const k of ['tr-icons', 'tr-flow', 'tr-norel']) { if (!bad()) return; tr.classList.add(k); }
  }

  /* ================= timeline ================= */
  function tickStep() { const steps = [1, 2, 5, 10, 15, 30, 60, 120, 300]; for (const s of steps) if (s * App.pps >= 64) return s; return 600; }
  function renderTimeline() {
    if (App.mode === 'v3d') return;
    hideHover();   // what it described is redrawn (or gone)
    const S = App.score, T = App.sched.t, total = App.sched.total, W = Math.ceil(X(total) + 240);
    const pbm = pbMap(), order = S.acts.flatMap(a => a.beats);
    const acts = App.sched.acts.map((a, i) => { const A = S.acts[i]; return `<div class="actb a${i % 2}" data-act="${a.id}" style="left:${X(a.s)}px;width:${Math.max(0, X(a.e) - X(a.s))}px;" title="${esc(A.name)}">${esc(A.name)}</div>`; }).join('');
    const mj = tickStep(), mn = mj >= 60 ? mj / 6 : mj / 5;
    let ticks = '';
    for (let t = 0; t <= Math.min(total, 36000) + 30; t += mn) { const isM = Math.abs(t / mj - Math.round(t / mj)) < 1e-6; if (!isM && mn * App.pps < 7) continue; ticks += `<span class="tk ${isM ? 'mj' : 'mn'}" style="left:${X(t)}px"></span>`; if (isM) ticks += `<span class="tkl tnum" style="left:${X(t)}px">${fmtMS(t)}</span>`; }
    for (const [id, sv] of Object.entries(pbm)) if (T[id]) ticks += `<span class="rulmark" style="left:${X(T[id][0]) - 2}px;background:var(--danger);opacity:${sv === 'warn' ? .55 : 1}"></span>`;
    for (const id of App.diverged || []) if (T[id]) ticks += `<span class="rulmark" style="left:${X(T[id][0]) - 2}px;background:var(--auto-ovr)" title="${App.adv ? '≠ APK' : DIFFERS}"></span>`;
    for (const [nid, n] of Object.entries(S.notes || {})) ticks += `<span class="nmk${n.resolved ? ' done' : ''}" data-nmk="${nid}" style="left:${X(n.t)}px;background:${(WHO[n.who] || WHO.B).c}" title="${esc((WHO[n.who] || { n: n.who || '?' }).n + (n.resolved ? ' · resolved' : '') + ' · ' + tc(n.t) + '\n' + n.text)}"></span>`;
    for (const [mid, m] of Object.entries(S.markers || {})) ticks += `<span class="mkr" data-mk="${mid}" style="left:${X(m.t)}px" title="${esc(m.name)} · ${tc(m.t)} · drag to move · double-click to rename · right-click for more"></span>`;
    const pb = beatAt(App.ph);
    const moms = order.map((b, i) => { const s = T[b][0], nx = i < order.length - 1 ? T[order[i + 1]][0] : T[b][1]; const w = Math.max(16, X(nx) - X(s) - 6);
      return `<div class="momb${b === pb ? ' on' : ''}" data-beat="${b}" style="left:${X(s) + 3}px;max-width:${w}px;"><b>${esc(S.beats[b].key)}</b>${esc(S.beats[b].title)}</div>`; }).join('');   // its hover card says the rest (C11)
    const momLines = order.map(b => `<div class="momline" style="left:${HDR + X(T[b][0])}px"></div>`).join('');
    const byLane = {};
    for (const [id, e] of Object.entries(S.elements)) (byLane[e.lane] = byLane[e.lane] || []).push(id);
    let rows = '', alt = 0;
    for (const g of S.groups) {
      const col = groupCollapsed(g.id), hue = g.hue || hueOf(g.id), aud = App.AUD.has(g.id) ? ' aud' : '';
      let sum = '';
      if (col) for (const l of g.lanes) for (const id of byLane[l] || []) { const e = El(id); if (isInstant(e)) continue; const [s, en] = T[id]; sum += `<span class="sum" style="left:${X(s)}px;width:${Math.max(6, X(en) - X(s))}px;background:${hue};color:${textOn(hue)}">${esc(View.titleOf(e).main)}</span>`; }
      rows += `<div class="row grow" data-group="${g.id}"><div class="ghd"><button class="gch" data-col="${g.id}" title="${col ? 'Expand' : 'Collapse'} group"><span style="display:inline-flex;transform:rotate(${col ? -90 : 0}deg);">${ICO('chevDown', 11)}</span></button><span class="glab" title="${esc(g.name)}">${esc(g.name)}</span><span class="gsp"></span><button class="gb lk${App.locked[g.id] ? ' on' : ''}" data-lock="${g.id}" title="${App.locked[g.id] ? 'Unlock group' : 'Lock group: protects it from edits'}">${ICO('lock', 10)}</button><button class="gb" data-newlane="${g.id}" title="New lane · Alt+T">+</button></div><div class="gfld">${sum}</div></div>`;
      if (col) continue;
      const h = laneH(g.id);
      g.lanes.forEach((lid, li) => {
        alt++;
        const ids = (byLane[lid] || []).slice().sort((a, b) => T[a][0] - T[b][0]);
        rows += `<div class="row" data-lane="${lid}" data-group="${g.id}"><div class="lanehdr sub${aud}" data-lanehdr="${lid}" style="height:${h}px;"><span class="bar" style="background:${hue}"></span><div class="lnrow"><span class="tag">${li + 1}</span><span class="nm" title="Double-click to rename">${esc(S.lanes[lid].name)}</span></div></div><div class="fld${aud}${alt % 2 ? '' : ' alt'}" data-fld="${lid}" style="height:${h}px;">${laneHTML(ids, h, hue, pbm)}</div></div>`;
      });
      rows += `<div class="slot" data-slot="${g.id}" style="display:none;"><div class="shd">+ New lane</div><div class="sfl"></div></div>`;
    }
    const tlc = $('#tlc'), comfy = App.laneSize === 'comfortable', run = runShown();
    tlc.style.width = (HDR + W) + 'px'; tlc.classList.toggle('comfy', comfy); tlc.style.setProperty('--tlhd', headH() + 'px');
    // the lane height switch sits where Premiere keeps its timeline display settings: above the lane headers (C11)
    const lsw = `<span class="lhsw" title="Lane height (also in Window)"><button data-lanes="compact" class="${comfy ? '' : 'on'}" title="Compact lanes">${ICO('rowsDense', 11)}</button><button data-lanes="comfortable" class="${comfy ? 'on' : ''}" title="Comfortable lanes: taller, with a second line for the key and two lines of each voice">${ICO('rowsTall', 11)}</button></span>`;
    tlc.innerHTML = `<div class="tlhead"><div class="hpad"><div style="height:18px;">Acts</div><div style="height:24px;">${lsw}<span style="flex:1;"></span>Time</div><div style="height:16px;">Moments</div>${run ? runHeadHTML() : ''}</div><div class="hfld"><div class="actrow">${acts}</div><div class="rulerow" id="ruler">${rangeHTML()}${ticks}<div class="phr" id="phr"></div></div><div class="momrow">${moms}</div>${run ? `<div class="runrow${App.runView.comparable ? '' : ' nc'}" id="runrow">${runLaneHTML()}</div>` : ''}</div></div>
      <div id="moml">${momLines}</div>${rows}<svg class="anc" id="anc"></svg><div class="ph" id="ph"></div>`;
    laneTop = {}; groupTop = {};
    tlc.querySelectorAll('.row[data-lane]').forEach(r => { laneTop[r.dataset.lane] = r.offsetTop; });
    tlc.querySelectorAll('.row.grow').forEach(r => { groupTop[r.dataset.group] = r.offsetTop; });
    movePlayhead(); renderTimelineSelection();
    if ($('#findbar')) { if (findSig() !== F.sig) refreshFind(false); else paintFind(); }   // the matches stay outlined
  }
  /* the play range (I / O) shaded on the ruler, ISP's work area: an open side (no In, or no Out) has no edge */
  function rangeHTML() {
    const R = playBounds(); if (!R) return '';
    return `<div class="work rng${App.inT == null ? ' nol' : ''}${App.outT == null ? ' nor' : ''}" id="rng" style="left:${X(R[0])}px;width:${Math.max(1, X(R[1]) - X(R[0]))}px;"></div>`;
  }
  function renderRange() { const ru = $('#ruler'); if (!ru) return; const o = $('#rng'); if (o) o.remove(); const h = rangeHTML(); if (h) ru.insertAdjacentHTML('afterbegin', h); }
  /* the "Unreal run" lane (lote 5, design A §6.6): one bar per segment of the last Unreal run. By default each bar starts at
     the score's mark and lasts what Unreal took, so its end shows how far Unreal goes: hatched amber past the score's next
     mark, an amber gap when it stops short (only over the segment threshold; grey under it), hatched grey for a simulated
     mechanic. Right-click: aligned at the Hall start instead (the run as it happened). The pieces come from Calib.lane,
     computed once per compute (App.runLaneData); this only turns seconds into pixels */
  const sgS = v => (v >= 0 ? '+' : '−') + fmtS(Math.abs(v));
  function runHeadHTML() {
    const R = App.runView, I = R.info || {}, N = App.runNoise, why = (R.stale.find(s => s.code === 'speed' || s.code === 'align') || {}).msg;
    const tip = [Calib.runLabel(I) + (I.sim && !I.simSaid ? ' (the smoke test)' : ''),
      App.runAlign === 'hall' ? 'Aligned at the Hall start: the run as it happened.' : 'Each bar starts at the score\'s mark and lasts what Unreal took.',
      R.comparable ? (R.total ? `Hall start → end: ${tc(R.total.score)} here, ${tc(R.total.trace)} in the run (${sgS(R.total.d)} s).` : '') : 'Not comparable: ' + (why || ''),
      App.persona !== 'typical' ? `Drawn against the ${persona().name.toLowerCase()} user on screen; Problems are checked with the typical user.` : '',
      N ? `${N.runs} runs: they differ by up to ${N.seg.toFixed(2)} s per segment.` : 'One run: how much two runs differ is not known yet.',
      'Click a bar: go to its mark · right-click: align or hide'].filter(Boolean).join('\n');
    return `<div class="runhd" style="height:12px;" title="${esc(tip)}">${esc(Calib.runLabel(I, { short: true }))}${I.sim ? '<i>sim</i>' : ''}</div>`;
  }
  function runLaneHTML() {
    const R = App.runView;
    if (!R.rows.length) return `<span class="rnone">${esc((R.stale.find(s => s.code === 'align') || { msg: 'Nothing of the run to compare' }).msg)}</span>`;
    const done = new Set(); let h = '';
    for (const p of App.runLaneData || []) {
      if (p.kind === 'tick') { h += `<span class="rtick" style="left:${X(p.s)}px"></span>`; continue; }
      const r = p.row, x = X(p.s), w = Math.max(1, X(p.e) - x);
      let lab = '';
      if (!done.has(r.mark) && (p.big || p.kind === 'sim')) {   // the first piece of a segment where its label fits
        const full = p.kind === 'sim' ? `${Marks.label(r.mark)} · simulated · ${fmtS(r.segTrace)} s` : `${Marks.label(r.mark)} · ${fmtS(r.segTrace)} s (${sgS(r.dSeg)})`;
        const short = p.kind === 'sim' ? 'simulated' : sgS(r.dSeg);
        lab = w >= full.length * 4.9 + 6 ? full : w >= short.length * 4.9 + 6 ? short : '';
        if (lab) done.add(r.mark);
      }
      h += `<span class="rseg r${p.kind}${p.big ? ' big' : ''}" data-rs="${esc(r.mark)}" style="left:${x}px;width:${w}px;" title="${esc(runTip(p))}">${esc(lab)}</span>`;
    }
    return h;
  }
  function runTip(p) {
    const r = p.row, R = App.runView, to = r.to ? Marks.label(r.to) : 'the end';
    const lines = [`${Marks.label(r.mark)} → ${to} · ${Marks.describe(r.mark)}`,
      `Here ${fmtS(r.segScore)} s, from ${tc(r.score)} · Unreal run ${fmtS(r.segTrace)} s, from ${tc(r.trace)} (aligned at the Hall start) · ${sgS(r.dSeg)} s`];
    if (p.kind === 'sim') lines.push(`Simulated run: the director asked this mechanic to close at ${R.simCap != null ? R.simCap + ' s' : 'Sim_EtapaMax'}, not a user. Not compared.`);
    else if (p.kind === 'over') lines.push(`Unreal goes on ${fmtS(p.e - p.s)} s after the score reaches ${to} (${tc(p.s)}).`);
    else if (p.kind === 'gap') lines.push(`Unreal reaches ${to} ${fmtS(p.e - p.s)} s before the score does (${tc(p.e)}).`);
    else if (p.kind === 'order') lines.push(`The score places ${to} before ${Marks.label(r.mark)}.`);
    if (r.cause && p.kind !== 'sim') lines.push(r.cause);
    return lines.join('\n');
  }
  /* the pill of the status bar opens the lane and the problems of the run; Show in timeline zooms to a section or segment */
  function openRun() {
    if (!App.run) return;
    if (App.mode === 'v3d') setMode('all');
    if (!App.runLane) { App.runLane = true; savePref(); }
    App.drawer = 'problems'; App.pbFilter = 'run'; renderTimeline(); renderDrawer(); renderTransport();
  }
  /* the status bar's "N to review": Problems on what needs a look (a second click closes it) */
  function openReview() {
    if (App.mode === 'v3d') setMode('all');
    if (App.drawer === 'problems' && Simple.filterFor(App.pbFilter, App.adv, !!App.run) === 'attn') { toggleDrawer(); return; }
    App.pbFilter = 'attn'; App.drawer = 'problems'; renderDrawer(); renderTransport();
  }
  function showRunSpan(a, b) {
    const M = App.runView && App.runView.marks, s = M && M[a], e = M && M[b]; if (s == null) return;
    if (App.mode === 'v3d') setMode('all');
    if (!App.runLane) { App.runLane = true; savePref(); }
    zoomTo(s, e != null && e > s ? e : s + 10); seek(s);
  }
  function laneHTML(ids, h, hue, pbm) {
    const T = App.sched.t; let out = '';
    const fg = textOn(hue), comfy = App.laneSize === 'comfortable';
    // C11: no native tooltips here: the hover card (hoverMove) says what each one is, at once. A technical key goes after
    // the label, small (View.titleOf); a voice keeps its key
    ids.forEach((id, i) => {
      const e = El(id), [s, en] = T[id], x = X(s);
      const pb = pbm[id], tt = View.titleOf(e), offb = !!(App.sched.off && App.sched.off[id]);   // the other side of a decision: dimmed and hatched, still editable
      if (isInstant(e)) {
        let nx = Infinity; for (let j = i + 1; j < ids.length; j++) { nx = X(T[ids[j]][0]); break; }
        const lw = Math.max(18, Math.min(220, nx - x - 12));
        out += `<div class="evt${offb ? ' offbr' : ''}${e.isNew ? ' new' : ''}${pb ? ' pb-' + pb : ''}${App.diverged && App.diverged.has(id) ? ' neapk' : ''}${App.editedSet && App.editedSet.has(id) ? ' edited' : ''}" data-id="${id}" style="left:${x - 3.5}px;top:${(h - 16) / 2}px;max-width:${lw}px;"><i style="background:${hue}"></i><span>${esc(tt.main)}${tt.labelFirst ? `<small>${esc(tt.sub)}</small>` : ''}</span></div>`;
        return;
      }
      const w = Math.max(6, X(en) - x), ch = h - 8;
      const help = !!e.help, inact = help && App.sched.helpActive[id] === false;
      const con = Integrity.contractFor(id, e, App.contract).filter(c => c.kind !== 'not-in-unreal');
      let cls = 'clip' + (offb ? ' offbr' : '') + (e.gate ? ' wait' : '') + (help ? ' help' : '') + (inact ? ' inact' : '') + (pb ? ' pb-' + pb : '') + (App.diverged && App.diverged.has(id) ? ' neapk' : '') + (App.editedSet && App.editedSet.has(id) ? ' edited' : '');
      let gl = e.type === 'vo' ? ICO('wave', 11) : e.gate ? ICO('hourglass', 10) : e.type === 'instruction' ? ICO('ghost', 11) : '';
      if (con.length) gl = ICO('wire', 10) + gl;
      let body = '';
      const sub = e.type === 'vo' ? (help ? 'help' : '') : tt.sub;
      if (e.type === 'vo' && ch > 20) body = `<div class="bd">${wave(e.key, w, ch - 16, fg)}<div class="vtx">${esc(e.text || '')}</div></div>`;
      else if (comfy && sub && ch >= 26) body = `<div class="bd"><div class="ktx">${esc(sub)}</div></div>`;   // comfortable: the key on its own line
      const trim = !App.locked[e.group] && (e.gate || (e.dur && e.dur.mode === 'fixed'));
      out += `<div class="${cls}" data-id="${id}" style="left:${x}px;width:${w}px;height:${ch}px;"><div class="fill" style="background-color:${hue}"></div><div class="scrim"></div><div class="tt" style="background:${hue};color:${fg}"><span class="gl">${gl}</span>${esc(tt.main)}${sub && !(body && e.type !== 'vo') ? `<span class="cpx">${esc(sub)}</span>` : ''}</div>${body}${pb ? `<span class="pbdot${pb === 'warn' ? ' ring' : ''}"></span>` : ''}${App.diverged && App.diverged.has(id) ? (App.adv ? '<span class="neapkchip">≠ APK</span>' : `<span class="neapkchip" title="${DIFFERS}">≠</span>`) : ''}${trim ? '<div class="hd r" data-trim="1"></div>' : ''}</div>`;
      if (e.gate) {
        const fwx = X(s + e.gate.fw), clock = View.clockWait(e);
        if (clock) {
          // on the stage's clock (schema 3): it draws its clock length for everybody; the user on screen only decides when he acts,
          // a thin hatched tail after it (none for the typical user, who acts right on it)
          const rt = View.waitReaction(e, T[id], App.sched.react && App.sched.react[id], persona().name);
          if (rt) out += `<div class="wreact" style="left:${x + w}px;width:${Math.max(2, X(rt.to) - x - w)}px;height:${ch}px;"><span class="wt">${esc(rt.label)}</span><i></i></div>`;
        } else if (fwx > x + w + 1) out += `<div class="wtail" style="left:${x + w}px;width:${fwx - x - w}px;height:${ch}px;"><span class="wt">up to ${fmtS(e.gate.fw)} s</span></div>`;
        out += `<div class="wfw${clock ? ' sim' : ''}" style="left:${fwx - 1}px;height:${h - 4}px;" title="${clock ? `Gives up at ${e.gate.fw} s · simulation only: in Unreal the stage runs on its clock` : `Timeout ${e.gate.fw} s`}"><span>${e.gate.fw} s</span></div>`;
      }
    });
    return out;
  }
  function wave(seed, w, h, fg) {
    w = Math.min(w, 2400); let d = '', s = 0; for (const c of seed) s = (s * 31 + c.charCodeAt(0)) >>> 0;
    const rnd = () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; };
    for (let x = 2; x < w - 2; x += 2) { const env = Math.sin(Math.PI * Math.min(1, x / Math.max(8, w))) * .9 + .1; const a = .85 * (h / 2 - 1) * env * (.35 + .65 * rnd()); d += `M${x} ${(h / 2 - a).toFixed(1)}V${(h / 2 + a).toFixed(1)}`; }
    return `<svg class="wv" width="${w}" height="${h}" style="position:absolute;left:0;bottom:0;opacity:.55;"><path d="${d}" stroke="${fg === '#0E0F11' ? 'rgba(14,15,17,.55)' : 'rgba(242,244,248,.5)'}" stroke-width="1"/></svg>`;
  }
  // what hangs from it (never itself: two items can hang from each other's other edge, e.g. a start from a start and an
  // end from an end, without a timing loop; see Edits.hangingFrom)
  function familyOf(id) { const f = id && El(id) ? ScoreEngine.family(App.score, id, App.kids) : new Set(); f.delete(id); return f; }
  function renderTimelineSelection() {
    const tlc = $('#tlc'); if (!tlc || App.mode === 'v3d') return;
    tlc.querySelectorAll('.sel,.gsel').forEach(n => n.classList.remove('sel', 'gsel'));
    const ids = selIds();   // C10: every selected clip renders selected; what hangs from it only with one selected
    for (const id of ids) tlc.querySelectorAll(`[data-id="${id}"]`).forEach(n => n.classList.add('sel'));
    if (ids.length === 1) for (const k of familyOf(App.sel)) tlc.querySelectorAll(`[data-id="${k}"]`).forEach(n => n.classList.add('gsel'));
    if (App.selKind === 'beat') tlc.querySelectorAll(`[data-beat="${App.sel}"]`).forEach(n => n.classList.add('sel'));
    if (App.selKind === 'knob') for (const [id, gs] of Object.entries(App.gov || {})) if (gs.some(g => g.knob === App.sel)) tlc.querySelectorAll(`[data-id="${id}"]`).forEach(n => n.classList.add('gsel'));
    drawAnchors();
  }
  function drawAnchors() {
    const svg = $('#anc'), tlc = $('#tlc'); if (!svg || !tlc) return;
    svg.setAttribute('width', tlc.scrollWidth); svg.setAttribute('height', tlc.scrollHeight);
    const id = App.sel, e = App.selKind === 'el' && El(id);
    if (!App.showAnchors || !e || App.selMore.size) { svg.innerHTML = ''; return; }   // several selected: no curves (whose?)
    const T = App.sched.t, S = App.score;
    const yOf = r => { if (S.beats[r]) return 50; const x = El(r); if (!x) return null; if (groupCollapsed(x.group)) return groupTop[x.group] + 11; return laneTop[x.lane] != null ? laneTop[x.lane] + laneH(x.group) / 2 : null; };
    const xOf = (r, edge) => HDR + X(edge === 'end' ? T[r][1] : T[r][0]);
    let out = '';
    const link = (from, edge, to, toEdge, label, live, dash) => {
      if (!T[from] || !T[to]) return; const ay = yOf(from), by = yOf(to); if (ay == null || by == null) return;
      const ax = xOf(from, edge), bx = xOf(to, toEdge), col = live ? 'var(--auto-live)' : 'var(--ink-2)', k = Math.max(18, Math.abs(by - ay) * .25);
      out += `<path d="M${ax} ${ay} C${ax + k} ${ay} ${bx - k} ${by} ${bx} ${by}" fill="none" stroke="${col}" stroke-width="1" stroke-opacity=".8"${dash ? ' stroke-dasharray="3 3"' : ''}/><circle cx="${ax}" cy="${ay}" r="2.5" fill="${col}"/><circle cx="${bx}" cy="${by}" r="2.5" fill="${col}"/>`;
      if (label) out += `<text x="${(ax + bx) / 2 + 4}" y="${(ay + by) / 2 - 3}" fill="${col}">${esc(label)}</text>`;
    };
    const offTxt = a => a && a.off ? (a.off > 0 ? '+' : '') + fmtS(a.off) + ' s' : '';
    const live = r => { const x = El(r); return !!(x && x.gate); };
    if (e.at && e.at.ref) link(e.at.ref, e.at.edge, id, 'start', offTxt(e.at), live(e.at.ref) && e.at.edge === 'end');
    if (e.end && e.end.ref) link(e.end.ref, e.end.edge, id, 'end', 'until', live(e.end.ref) && e.end.edge === 'end');
    if (e.help && El(e.help)) link(e.help, 'start', id, 'start', 'help', true, true);
    for (const k of App.kids[id] || []) { const y = El(k); if (!y) continue; if (y.at && y.at.ref === id) link(id, y.at.edge, k, 'start', offTxt(y.at), !!e.gate && y.at.edge === 'end'); if (y.end && y.end.ref === id) link(id, y.end.edge, k, 'end', 'until', !!e.gate); }
    if (e.gate) for (const [k, y] of Object.entries(S.elements)) if (y.help === id) link(id, 'start', k, 'start', 'help', true, true);
    svg.innerHTML = out;
  }
  let _pb = null;
  function movePlayhead(playing) {
    const ph = $('#ph'); if (ph) ph.style.left = (HDR + X(App.ph) - 1) + 'px';
    const phr = $('#phr'); if (phr) phr.style.left = (X(App.ph) - 1) + 'px';
    const b = beatAt(App.ph);
    const tcv = $('#tcv'); if (tcv) tcv.textContent = tc(App.ph);
    const rel = $('#tcrel'); if (rel) rel.textContent = `+${fmtS(App.ph - App.sched.t[b][0])} s in ${App.score.beats[b].key}`;
    if (b !== _pb) { _pb = b; document.querySelectorAll('.momb.on').forEach(n => n.classList.remove('on')); document.querySelectorAll(`.momb[data-beat="${b}"]`).forEach(n => n.classList.add('on')); }
    if (playing && App.follow) { const sc = $('#sctl'); if (sc) { const x = HDR + X(App.ph), vw = sc.clientWidth; if (x < sc.scrollLeft + HDR || x > sc.scrollLeft + vw - 40) sc.scrollLeft = x - HDR - (vw - HDR) * .2; } }
  }
  function revealTime(t) { const sc = $('#sctl'); if (!sc) return; const x = HDR + X(t), vw = sc.clientWidth; if (x < sc.scrollLeft + HDR + 10 || x > sc.scrollLeft + vw - 40) sc.scrollLeft = Math.max(0, x - HDR - (vw - HDR) * .25); }
  function revealEl(id) { const e = El(id); if (!e) return; revealTime(App.sched.t[id][0]); revealLane(e); }
  function revealLane(e) {
    const sc = $('#sctl'); if (!sc) return; const y = groupCollapsed(e.group) ? groupTop[e.group] : laneTop[e.lane];
    const hh = headH();   // under the sticky ruler block
    if (y != null && (y < sc.scrollTop + hh || y > sc.scrollTop + sc.clientHeight - 40)) sc.scrollTop = Math.max(0, y - hh - 40);
  }

  /* ================= hover card (audit C11) =================
     At once, over a clip, an instant or a moment chip: what it is, when it starts, how long it lasts, what it hangs from,
     where it is, and the first words of a voice. It never takes the pointer (pointer-events: none), hides while dragging
     and stays inside the window. Its content is built only when the pointer reaches another item; moving over the same
     one only places it. */
  let hov = null;
  const hcardEl = () => { let c = $('#hcard'); if (!c) { c = document.createElement('div'); c.id = 'hcard'; c.className = 'hcard'; c.setAttribute('role', 'tooltip'); document.body.appendChild(c); } return c; };
  function hideHover() { if (!hov) return; hov = null; const c = $('#hcard'); if (c) c.style.display = 'none'; }
  function hoverMove(ev) {
    if (drag || App.cardOpen || App.mode === 'v3d') return hideHover();
    const n = ev.target.closest && ev.target.closest('.fld [data-id], .momb');
    if (!n) return hideHover();
    const c = hcardEl(), k = App.k || 1;
    if (!hov || hov.node !== n) {
      const html = n.classList.contains('momb') ? beatCard(n.dataset.beat) : elCard(n.dataset.id);
      if (!html) return hideHover();
      // measured at the window's corner: where it was last time must not narrow it (and change its height)
      c.style.left = '0px'; c.style.top = '0px'; c.innerHTML = html; c.style.display = 'block'; c.style.transform = k < 1 ? `scale(${k})` : '';
      hov = { node: n, w: c.offsetWidth * k, h: c.offsetHeight * k };
    }
    let x = ev.clientX + 14, y = ev.clientY + 18;
    if (x + hov.w > innerWidth - 6) x = ev.clientX - hov.w - 10;
    if (y + hov.h > innerHeight - 6) y = ev.clientY - hov.h - 10;
    c.style.left = Math.max(4, Math.min(x, innerWidth - hov.w - 4)) + 'px'; c.style.top = Math.max(4, Math.min(y, innerHeight - hov.h - 4)) + 'px';
  }
  const firstWords = (t, n) => { const w = String(t || '').trim().split(/\s+/).filter(Boolean); return w.slice(0, n).join(' ') + (w.length > n ? '…' : ''); };
  const cut = (t, n) => { t = String(t || ''); return t.length > n ? t.slice(0, n - 1) + '…' : t; };
  const hrow = (lab, val) => `<div class="hc-r"><span>${lab}</span><b>${val}</b></div>`;
  function elCard(id) {
    const S = App.score, e = El(id), T = App.sched.t[id]; if (!e || !T) return '';
    const tt = View.titleOf(e), g = S.groups.find(x => x.id === e.group), B = S.beats[e.beat], d = T[1] - T[0];
    const clock = View.clockWait(e), acts = clock && App.sched.react ? App.sched.react[id] - T[0] : 0;
    const dur = clock ? `${fmtS(d)} s · the stage's clock · the ${persona().name.toLowerCase()} user acts at ${fmtS(acts)} s`
      : e.gate ? `${fmtS(d)} s · ${persona().name.toLowerCase()} user · timeout ${fmtS(e.gate.fw)} s`
      : e.end && e.end.ref ? `${fmtS(d)} s · ${View.anchorPhrase(S, e.end, { until: true })}`
      : isInstant(e) ? 'instant' : `${fmtS(d)} s`;
    let h = `<div class="hc-h"><i style="background:${hueOf(e.group)}"></i><b>${esc(tt.main)}</b></div><div class="hc-k">${esc([tt.sub, KIND[e.type] || e.type].filter(Boolean).join(' · '))}</div>`
      + hrow('Starts', `${tc(T[0])}${B ? ` · in ${esc(B.key)}` : ''}`) + hrow('Lasts', esc(dur)) + hrow('Anchor', esc(View.anchorPhrase(S, e.at)))
      + hrow('Lane', esc(`${(S.lanes[e.lane] || {}).name || e.lane} · ${g ? g.name : e.group}`));
    if (e.branch) h += hrow('Plays in', esc(Integrity.branchText(S, { [e.branch.on]: e.branch.value }) + ' only'));
    if (e.type === 'vo' && e.text) h += `<div class="hc-q">"${esc(firstWords(e.text, 16))}"</div>`;
    const pb = App.problems.filter(p => p.el === id && p.st === 'open' && p.sv !== 'info');
    if (pb.length) h += `<div class="hc-f bad">${pb.length > 1 ? pb.length + ' open problems' : 'Open problem'}: ${esc(cut(pb[0].msg, 110))} · F8</div>`;
    if (App.diverged && App.diverged.has(id)) h += App.adv ? '<div class="hc-f warn">≠ APK: its time here differs from what the APK does today (Unreal keeps its own until you send it)</div>'
      : '<div class="hc-f warn">≠ Its time here differs from what the headset build does today (Unreal keeps its own until you send it)</div>';
    if (App.sched.off && App.sched.off[id]) h += `<div class="hc-f warn">${esc(Integrity.branchText(S, { [e.branch.on]: e.branch.value }))} only: it does not play in ${esc(Integrity.branchText(S, App.sched.branch))}, which is what you are looking at</div>`;
    if (e.isNew) h += `<div class="hc-f warn">${e.copyOf ? 'A copy made in the editor' : 'New'}: not in Unreal yet</div>`;
    if (e.help) h += `<div class="hc-f">Help line of ${esc(keyOf(e.help))}</div>`;
    if (App.locked[e.group]) h += `<div class="hc-f">${ICO('lock', 10)} ${esc(g ? g.name : e.group)} is locked</div>`;
    else if (!App.pick) h += `<div class="hc-n">Drag to move it · right-click for more${e.gate || (e.dur && e.dur.mode === 'fixed') ? ' · its right edge: the duration' : ''}</div>`;
    return h;
  }
  function beatCard(b) {
    const S = App.score, B = S.beats[b], T = App.sched.t[b]; if (!B || !T) return '';
    const A = S.acts.find(a => a.beats.includes(b)); let n = 0; for (const k in S.elements) if (S.elements[k].beat === b) n++;
    return `<div class="hc-h"><i style="background:#5E6570"></i><b>${esc(B.title || B.key)}</b></div><div class="hc-k">Moment ${esc(B.key)}${A ? ' · ' + esc(A.name) : ''}</div>`
      + hrow('Starts', tc(T[0])) + hrow('Lasts', `${fmtS(T[1] - T[0])} s · until its last element`) + hrow('Anchor', esc(View.anchorPhrase(S, View.beatAnchor(S, b))))
      + hrow('Elements', String(n)) + (App.pick ? '' : '<div class="hc-n">Drag to move it: everything after it follows · double-click to zoom to it</div>');
  }

  /* ================= find (Ctrl+F, audit C11) =================
     Elements by key, label or voice text; moments by key or title (View.findMatches). Enter selects the next match and
     shows it (scrolls, and zooms in when it is too small to read); Shift+Enter the previous one; Esc closes. The matches
     are outlined meanwhile. Searching never moves the playhead and never changes the score. */
  const F = { q: '', list: [], i: -1, sig: '' };
  const findSig = () => (App.editSeq || 0) + '|' + App.persona;
  function openFind() {
    if (App.view === '3d') return toast('Search in the timeline tab: this one only shows the 3D view');
    if (App.mode === 'v3d') setMode('all');
    let bar = $('#findbar');
    if (!bar) {
      bar = document.createElement('div'); bar.className = 'findbar'; bar.id = 'findbar';
      bar.innerHTML = `<span class="fi">${ICO('search', 12)}</span><input id="findIn" placeholder="Find clips and moments" spellcheck="false" autocomplete="off" aria-label="Find clips and moments"><span class="fcount tnum" id="findCount"></span><button class="fb" data-find="prev" title="Previous · Shift+Enter">${ICO('chevUp', 11)}</button><button class="fb" data-find="next" title="Next · Enter">${ICO('chevDown', 11)}</button><button class="fb" data-find="close" title="Close · Esc">${ICO('close', 10)}</button>`;
      document.querySelector('#timeline .tlmain').appendChild(bar);
      const inp = bar.querySelector('#findIn'); inp.value = F.q;
      inp.addEventListener('input', () => { F.q = inp.value; refreshFind(true); });
      inp.addEventListener('keydown', ev => {   // the editor's keys do not see these (stopPropagation)
        if (ev.key === 'Enter') { ev.preventDefault(); ev.stopPropagation(); if (!ev.repeat) findGo(ev.shiftKey ? -1 : 1); }
        else if (ev.key === 'Escape') { ev.preventDefault(); ev.stopPropagation(); closeFind(); }
      });
      bar.addEventListener('mousedown', ev => { if (ev.target.closest('[data-find]')) ev.preventDefault(); });   // the field keeps the focus
      bar.addEventListener('click', ev => { const b = ev.target.closest('[data-find]'); if (!b) return; if (b.dataset.find === 'close') closeFind(); else findGo(b.dataset.find === 'prev' ? -1 : 1); });
    }
    const inp = bar.querySelector('#findIn'); inp.focus(); inp.select();
    refreshFind(false);
  }
  function closeFind() { const bar = $('#findbar'); if (!bar) return; if (bar.contains(document.activeElement)) document.activeElement.blur(); bar.remove(); F.i = -1; paintFind(); }
  /* the matches again (a new query: none current yet; after an edit: the current one kept, by id) */
  function refreshFind(reset) {
    const keep = !reset && F.i >= 0 && F.list[F.i] ? F.list[F.i].id : null;
    F.list = View.findMatches(App.score, F.q, App.sched.t); F.sig = findSig();
    F.i = keep ? F.list.findIndex(m => m.id === keep) : -1;
    paintFind(); countFind();
  }
  function countFind() {
    const c = $('#findCount'); if (!c) return; const m = F.list.length, q = F.q.trim();
    c.textContent = !q ? '' : !m ? 'No matches' : F.i >= 0 ? `${F.i + 1} of ${m}` : `${m} match${m > 1 ? 'es' : ''}`;
    c.classList.toggle('none', !!q && !m);
  }
  function paintFind() {
    const tlc = $('#tlc'); if (!tlc) return;
    tlc.querySelectorAll('.fhit').forEach(n => n.classList.remove('fhit'));
    if (!$('#findbar') || !F.list.length) return;
    const ids = new Set(F.list.map(m => m.id));
    tlc.querySelectorAll('.fld [data-id], .momb').forEach(n => { if (ids.has(n.dataset.id || n.dataset.beat)) n.classList.add('fhit'); });
  }
  function findGo(dir) {
    if (findSig() !== F.sig) refreshFind(false);   // an edit, or another simulated user, moved things: the order is redone
    if (!F.list.length) { countFind(); return; }
    const cur = F.i >= 0 ? F.i : F.list.findIndex(m => m.id === App.sel);   // from the selection when it is a match
    F.i = View.findStep(F.list, cur, dir, App.ph);
    countFind(); revealMatch(F.list[F.i]);
  }
  /* select it and show it: zoom in when it is too small to read (never out), then scroll to it, its lane included */
  function revealMatch(m) {
    const sc = $('#sctl'), T = m && App.sched.t[m.id]; if (!sc || !T) return;
    const e = m.kind === 'el' ? El(m.id) : null, inst = !!e && isInstant(e);
    if (e && groupCollapsed(e.group)) { App.collapsed[e.group] = false; renderTimeline(); }
    const pps = m.kind === 'beat' ? View.revealPps(App.pps, T[1] - T[0], { minW: 160 }) : View.revealPps(App.pps, inst ? 0 : T[1] - T[0]);
    if (Math.abs(pps - App.pps) > 1e-9) { App.pps = pps; savePref(); renderTimeline(); }
    if (e) select(m.id); else select(m.id, 'beat');
    sc.scrollLeft = View.revealScroll(sc.scrollLeft, sc.clientWidth - HDR, X(T[0]), inst ? X(T[0]) + 160 : Math.max(X(T[1]), X(T[0]) + 40));
    if (e) revealLane(e);
  }

  /* ================= problems drawer ================= */
  function toggleDrawer() { App.drawer = App.drawer === 'problems' ? null : 'problems'; renderDrawer(); renderTransport(); }
  function problemAction(p) {
    if (p.st === 'accepted') return `<a data-reopen="${esc(p.fp)}" class="pact">Reopen</a>`;
    const e = p.el && El(p.el);
    if (p.rule === 'C3.DRIFT' && e) { const c = Integrity.contractFor(p.el, e, App.contract).find(x => x.kind === 'knob' && x.knob); return c ? `<a data-pfix="drift" data-id="${p.el}" class="pact pri">Match Unreal · ${c.knob.value} s</a>` : ''; }
    if (p.rule === 'C2.WAIT.NOHELP' && e) return `<a data-pfix="help" data-id="${p.el}" class="pact pri">Add a help line</a>`;
    if (p.rule === 'C1.ANCHOR.CYCLE') return `<a data-pfix="loop" data-id="${p.el}" class="pact pri">Fix the loop…</a>`;
    // an anchor to something deleted (element or moment, C1): repair only the LOST one (its start, what it lasts until, or
    // both) where it falls now; offered only when that keeps every time, otherwise it says why
    if (p.rule === 'C1.ANCHOR.MISSING' && (e || App.score.beats[p.el])) {
      const r = Edits.detachLost(App.score, p.el, ScoreEngine);
      if (!r.ok) return `<a data-goto="${p.el}" class="pact" title="${esc('Detach is not possible: ' + r.why)}">Show</a>`;
      const what = r.fields.map(f => f.field === 'end' ? 'Its end stays where it is now, measured from the start of its moment.' : App.score.beats[p.el] ? 'It follows the previous moment, at the same time.' : 'It hangs from the start of its moment, at the same time.').join(' ');
      return `<a data-pfix="detach" data-id="${p.el}" class="pact pri" title="${esc(what + ' To pick another anchor for its start, use the menu of its anchor in the inspector.')}">Detach (keeps its time)</a>`;
    }
    if (p.rule === 'C1.BRANCH.ANCHOR' && e) { const q = p.fp.split('|'); return `<a data-pfix="branch" data-id="${p.el}" data-k="${esc(q[2])}" data-field="${q[3] === 'end' ? 'end' : 'at'}" class="pact pri">Anchor in ${esc(Edits.optionLabel(App.score, q[2]))}…</a>`; }
    if (p.rule === 'C3.PARTITURA' && p.knob) return `<a data-pfix="knob" data-id="${esc(p.knob)}" class="pact pri">Match Unreal</a>`;
    if (p.rule === 'C3.KNOB.OFFSET' && e) return `<a data-pfix="knobanchor" data-id="${p.el}" class="pact pri" title="${esc('Moves only ' + e.key + ': it takes the anchor Unreal has (a card shows what changes first)')}">Match Unreal</a>`;
    if (p.rule === 'C2.VO.REAL') return `<a data-pfix="voices" class="pact pri">Use the recordings…</a>`;
    if (p.rule === 'C1.SCHEMA') return `<a data-pfix="schema" class="pact pri">Upgrade…</a>`;   // a card first: nothing is automatic
    if (p.grp === 'run' && p.span) return `<a data-runspan="${esc(p.span.join('|'))}" class="pact">Show in timeline</a>`;   // C3.TRACE.STAGE / SEG
    if (p.el) return `<a data-goto="${p.el}" class="pact">Show</a>`;
    return '';
  }
  function renderDrawer() {
    const d = $('#drawer'), tl = $('#timeline');
    if (App.drawer !== 'problems' || App.mode === 'v3d') { d.innerHTML = ''; tl.classList.remove('withdrawer'); return; }
    tl.classList.add('withdrawer');
    // "Unreal run" (lote 5): everything the last Unreal run says, the segment rows too (only here: alert fatigue, audit B2)
    // Simple opens on what needs a look (js/simple.js); the run's rows are folded under one row of their own, except in the run filter
    const k = pbCounts(), rv = Simple.review(App.problems), f = Simple.filterFor(App.pbFilter, App.adv, !!App.run), rank = { block: 0, inv: 0, warn: 1, info: 2 };
    let list = f === 'run' ? App.problems.filter(p => p.grp === 'run').concat(App.runSeg || [])
      : App.problems.filter(p => f === 'all' ? true : f === 'accepted' ? p.st === 'accepted' : f === 'apk' ? (p.ly === 'C3' && p.sv !== 'info') : f === 'attn' ? Simple.needsLook(p) : p.st === 'open');
    const RM = App.runView ? App.runView.marks : {};
    const ptime = p => p.el && App.sched.t[p.el] ? App.sched.t[p.el][0] : p.span && RM[p.span[0]] != null ? RM[p.span[0]] : 0;
    list = list.slice().sort((a, b) => (a.st === 'accepted') - (b.st === 'accepted') || rank[a.sv] - rank[b.sv] || ptime(a) - ptime(b));
    const ed = App.editedSet ? App.editedSet.size : 0, dv = App.diverged ? App.diverged.size : 0, nClean = Policy.cleanRecords(App.score.accepted, App.score).removed.length;
    const filters = Simple.filters(App.adv, !!App.run);
    const where = p => p.knob ? `<span class="el" data-knobgo="${esc(p.knob)}">${esc(p.knob)}</span>` : p.span ? `<span class="el" data-runspan="${esc(p.span.join('|'))}">${esc(p.where)}</span>`
      : p.el ? `<span class="el" data-goto="${p.el}">${esc(keyOf(p.el))}</span>` : p.where ? `<span>${esc(p.where)}</span>` : '<span>—</span>';
    const runNote = f === 'run' && App.run ? `${esc(Calib.runLabel(App.run.info))} · ${esc(Calib.pillText(App.run).replace(/^Unreal run · /, ''))} · stages over ${fmtS(Calib.thresholds(App.runNoise).xStage)} s warn` : `${ed} edited since save · ${dv} ≠ APK`;
    // one problem: Advanced as always; Simple adds a plain headline (the rule code stays in the tooltips) before the message (not on the rows folded under the run: their row says it)
    const row = (p, sub) => {
      const t = App.adv || sub ? '' : Simple.titleOf(p), tip = esc(p.msg + (p.was ? ' · ' + Integrity.reopenedText(p) : '') + (p.own && p.own !== '—' ? ' · ' + p.own : '') + ' · ' + p.rule);
      return `<div class="prw2${sub ? ' sub' : ''}"><span class="sv ${p.st === 'accepted' ? 'acc' : p.sv === 'inv' ? 'block' : p.sv}" title="${esc(App.adv ? p.ly + ' · ' + p.rule : Simple.sevWord(p) + ' · ' + p.ly + ' · ' + p.rule)}"></span><span class="m" title="${tip}">${t ? `<b class="pt">${esc(t)}</b> <span class="pd">${esc(p.msg)}</span>` : esc(p.msg)}${p.gone ? ' <i>(element deleted)</i>' : ''}${p.was ? ` <i class="reop">${esc(Integrity.reopenedText(p))}</i>` : ''}</span>${where(p)}<span>${problemAction(p)}</span><span class="st ${p.st === 'accepted' ? 'acc' : 'open'}" title="${esc(p.st === 'accepted' ? (p.value ? 'Accepted at ' + Integrity.valueWords(p.rule, p.value) + (p.reason ? ' · ' : '') : '') + (p.reason || '') : p.was ? Integrity.reopenedText(p) : '')}">${p.st === 'accepted' ? `Accepted · ${esc(p.who || '')}${p.value ? ' · ' + esc(Integrity.valueWords(p.rule, p.value)) : ''}${p.reason ? ' · "' + esc(p.reason) + '"' : ''}` : p.was ? 'Reopened' : 'Open'}</span></div>`;
    };
    // Simple: everything the last Unreal run says is ONE row ("Compared with the last Unreal run · 7 stages differ") that opens to the rows
    const R = App.run, tot = R && R.comparable && R.total;
    const group = ms => {
      const open = !!App.traceOpen, live = ms.some(p => p.st === 'open'), sv = ms.some(p => p.st === 'open' && p.sv === 'block') ? 'block' : ms.some(p => p.st === 'open' && p.sv === 'warn') ? 'warn' : live ? 'info' : 'acc';
      return `<div class="prw2 grp"><span class="sv ${sv}" title="${esc(sv === 'acc' ? 'Accepted' : Simple.sevWord({ sv, st: 'open' }))}"></span><span class="m"><button class="trtog" data-trgrp aria-expanded="${open}" title="${open ? 'Hide' : 'Show'} the stages and marks that differ">${ICO('chevDown', 10)}<b class="pt">${esc(Simple.groupLabel(ms))}</b></button>${tot ? ` <span class="pd">Hall start to end: ${tc(tot.score)} here, ${tc(tot.trace)} in the run</span>` : ''}</span><span>Whole piece</span><span><a class="pact" data-tr="run" title="Show the Unreal run lane in the timeline and everything the run says">Show the run</a></span><span class="st ${live ? 'open' : 'acc'}">${live ? 'Open' : 'Accepted'}</span></div>`;
    };
    const body = App.adv || f === 'run' ? list.map(p => row(p)).join('') : Simple.fold(list).map(i => i.group ? group(i.group) + (App.traceOpen ? i.group.map(p => row(p, true)).join('') : '') : row(i.row)).join('');
    d.innerHTML = `<div class="pdraw"><div class="ph2"><b>Problems</b><span>${App.adv ? `${k.b} blocking · ${k.w} warnings` : `${rv.count} to review`} · ${k.a} accepted</span><div class="well" style="margin-left:12px;">${filters.map(([v, l]) => `<button data-pf="${v}" class="${f === v ? 'on' : ''}">${l}</button>`).join('')}</div>${nClean ? `<a class="pact" data-pfix="clean" style="margin-left:12px;" title="Remove the accepted records of elements that were deleted (one undoable edit)">Clean up accepted · ${nClean}</a>` : ''}<div style="flex:1;"></div>${App.adv || f === 'run' ? `<span style="color:var(--ink-3);">${runNote} · checked with the typical user</span>` : `<span style="color:var(--ink-3);" title="${ed} edited since the last save · ${dv} differ from what the headset build does today">Checked with the typical user</span>`}<button class="ibtn flat" data-tr="problems" title="Close · F8">${ICO('chevDown')}</button></div>
      <div class="plist"><div class="prw2 hd"><span></span><span>What</span><span>Where</span><span>Do</span><span>State</span></div>
      ${body || `<div class="knote" style="padding:10px 0;">${f === 'attn' ? 'Nothing to review.' : 'Nothing here.'}</div>`}</div></div>`;
  }


  /* ================= inspector ================= */
  function prow(lab, val, u, pct, pc, o) {
    o = o || {};
    return `<div class="prow"${pc ? ` style="--pc:${pc}"` : ''}${o.title ? ` title="${esc(o.title)}"` : ''}><span class="lab">${lab}</span><div class="field" style="cursor:default;">${pct != null ? `<div class="track"><i style="width:${Math.max(0, Math.min(100, pct))}%;${pc ? `background:${pc}` : ''}"></i></div>` : ''}<div class="box"><span class="num">${esc(val)}</span><span class="u">${esc(u || '')}</span></div></div>${o.lock ? `<span class="lock" title="Final value approved in the test level">${ICO('lock', 11)}</span>` : ''}</div>`;
  }
  const prowTxt = (lab, html, title) => `<div class="prow"${title ? ` title="${esc(title)}"` : ''}><span class="lab">${lab}</span><span class="val">${html}</span></div>`;
  const prowIn = (lab, f, v, u, title, step, k) => `<div class="prow"${title ? ` title="${esc(title)}"` : ''}><span class="lab">${lab}</span><span class="val"></span><input class="ni tnum" data-f="${f}"${k ? ` data-k="${esc(k)}"` : ''} type="text" inputmode="decimal" data-step="${step || 0.1}" value="${+(+v).toFixed(3)}"><span class="u2">${u || ''}</span></div>`;
  function sec(id, t, body) {
    const open = !(App.secClosed && App.secClosed[id]);
    return `<button class="sechead" data-sec="${id}"><span style="color:var(--ink-dim);display:flex;${open ? '' : 'transform:rotate(-90deg);'}">${ICO('chevDown')}</span><span class="t">${t}</span><span class="ln"></span></button>${open ? body : ''}`;
  }
  /* Simple keeps what is Unreal-internal (the owner and graph, reach and why, the binding, where it came from, the Partitura knobs) under one
     "Details" row that remembers whether it is open (prefs); the hint beside it is the one thing worth knowing without opening it.
     Advanced draws those sections in place, as always (the callers put them straight into the page) */
  function details(inner, hint) {
    if (!inner) return '';
    const open = !!App.insDetails;
    return `<button class="sechead" data-details aria-expanded="${open}" title="The Unreal and technical details of this item"><span style="color:var(--ink-dim);display:flex;${open ? '' : 'transform:rotate(-90deg);'}">${ICO('chevDown')}</span><span class="t">Details</span>${hint ? `<span class="dhint">${esc(hint)}</span>` : ''}<span class="ln"></span></button>${open ? inner : ''}`;
  }
  function head(hue, icon, name, meta) {
    return `<div style="height:4px;width:100%;background:${hue};"></div><div class="selhead"><div class="selthumb" style="display:grid;place-items:center;background:var(--s2);color:var(--ink-2);">${ICO(icon, 16)}</div><div style="flex:1;min-width:0;"><div class="selname" title="${esc(name)}">${esc(name)}</div><div class="selmeta">${meta}</div></div></div>`;
  }
  function insTabs() {
    const n = Object.values(App.score.notes || {}).filter(x => !x.resolved).length;   // the open ones: a resolved note is dimmed, not counted
    return `<div class="panhead"><div class="well" style="height:22px;"><button class="instab${App.insTab === 'insp' ? ' on' : ''}" data-itab="insp" style="display:inline-flex;align-items:center;gap:5px;">${ICO('panel')}<span class="ttl">Inspector</span></button><button class="instab${App.insTab === 'notes' ? ' on' : ''}" data-itab="notes" style="display:inline-flex;align-items:center;gap:5px;">${ICO('note')}<span class="ttl">Notes</span>${n ? `<span class="countbadge" style="margin-left:2px;" title="${n} open note${n > 1 ? 's' : ''}">${n}</span>` : ''}</button></div></div>`;
  }
  /* the knobs of a role. From obra/unreal/knobs.json (tools/score/knobs.mjs) while it was made from this roles.json: each row then
     says its key in the catalog when hovered; otherwise from roles.json, as before (lote 5 design A §8.1) */
  function knobGroups(name) {
    const R = App.roles.roles[name], cat = window.Knobs && App.knobs ? (Knobs.fresh(App.knobs, App.roles) ? Knobs.groupsOf(App.knobs, name) : false) : null;
    const groups = cat || R.groups;
    return groups.map(g => `<div class="owner"><b>${esc(g.owner)}</b><span class="sc">${esc(g.scope)}</span></div>` + g.rows.map((k, ri) => {
      const id = cat ? ' · ' + g.ids[ri] : '';
      return k[3] == null
        ? prowTxt(esc(k[0]), `${esc(k[1])}${k[2] ? ' ' + esc(k[2]) : ''}${g.scope === 'literal' ? ' <span class="chip lit">literal</span>' : ''}`, `${k[5]} · ${g.owner}${id}`)
        : prow(esc(k[0]), k[1], k[2], k[3], k[4], { title: `${k[5]} · ${g.owner} · ${g.scope}${id}`, lock: k[6] });
    }).join('')).join('')
      + (R.note ? `<div class="knote warn">${esc(R.note)}</div>` : '')
      + `<div class="knote">Read from Unreal (${esc(App.roles.verified || '—')})${cat ? ' through knobs.json (' + esc(String(App.knobs.generated || '').slice(0, 10)) + ')' : ''}. Hover a knob to see its variable${cat ? ' and its key in the catalog' : ''}. Changing them from here comes with the bridge (phase F3); the lock marks values approved in the test levels. Their values are written down, not read from Unreal: read-only.</div>`
      + (cat === false ? `<div class="knote warn">obra/unreal/knobs.json was made from an older roles.json: these rows come from roles.json. Make it again with node tools/score/knobs.mjs.</div>` : '');
  }
  function anchorChip(a, edgeWord) {
    if (!a || !a.ref) return `<span class="anchip"><i>${ICO('anchor', 11)}</i>start of the piece</span>`;
    const isBeat = !!App.score.beats[a.ref];
    const word = isBeat ? (a.edge === 'end' ? 'end of' : 'start of') : (a.edge === 'end' ? (edgeWord || 'after') : 'with');
    return `<span class="anchip" data-goto="${a.ref}" title="Select the anchor">${'<i>' + ICO('anchor', 11) + '</i>'}${word} ${esc(keyOf(a.ref))}</span>`;
  }
  /* change the anchor (audit C9): the same entries in the inspector, the clip menu and the moment menu */
  const anchorCaret = id => `<button class="ancmenu" data-ancmenu="${id}" title="Change the anchor: pick another in the timeline, detach it, or switch between start and end. It keeps its time.">${ICO('chevDown', 10)}</button>`;
  function anchorItems(id) {
    const S = App.score, isB = !!S.beats[id], x = S.elements[id] || S.beats[id]; if (!x) return [];
    const cur = Edits.anchorOf(S, id), home = Edits.homeAnchor(S, id), ro = App.view === '3d' || (!isB && !!App.locked[x.group]);
    const cap = s => s[0].toUpperCase() + s.slice(1);
    const items = [
      ['Anchor to…', 'pick in the timeline', () => pickAnchor(id), { dis: ro }],
      [isB ? (home.ref ? 'Detach: follow the previous moment' : 'Detach: start of the piece') : 'Detach: anchor to its moment', 'keeps its time', () => Act.reanchor(id, null), { dis: ro || (cur.ref === home.ref && cur.edge === home.edge) }],
    ];
    if (cur.ref && (S.elements[cur.ref] || S.beats[cur.ref])) for (const edge of ['start', 'end']) items.push([cap(anchorText({ ref: cur.ref, edge })), cur.edge === edge ? 'now' : 'keeps its time', () => Act.reanchor(id, { ref: cur.ref, edge }), { on: cur.edge === edge, dis: ro || cur.edge === edge }]);
    // schema 3: the anchor it has in another side of a decision (an alternative: the clip hangs from something else only there)
    const brs = S.branches;
    if (brs) for (const on of Object.keys(brs)) for (const o of Object.keys(brs[on].options)) if (o !== brs[on].default)
      items.push([`Anchor in ${optionName(on, o)}…`, 'pick in the timeline', () => pickAnchor(id, { k: on + '=' + o }), { dis: ro }]);
    return items;
  }
  /* lote 5 (design B §5.3), in the Time section: which side of each decision plays this element, and the anchors it has of its own
     in one side ("Anchor in DON'T SHARE"), or needs there because what it hangs from does not play there */
  /* the caret of the anchor of one side: pick another, or go back to the same one as everywhere else */
  const altCaret = (id, k, f, lab) => `<button class="ancmenu" data-altmenu="${id}|${k}|${f}" title="${esc('Change the anchor in ' + lab + ': pick another in the timeline, or use the same one as everywhere else. It keeps its time there.')}">${ICO('chevDown', 10)}</button>`;
  /* hide = the key of a side whose start anchor the main "Starts" and "Offset" rows already show (the side on screen): not twice */
  function branchRowsHTML(id, hide) {
    const S = App.score, brs = S.branches; if (!brs) return '';
    const isEl = !!S.elements[id], x = S.elements[id] || S.beats[id], many = Object.keys(brs).length > 1; let h = '';
    if (isEl) for (const on of Object.keys(brs)) {
      const br = brs[on], cur = x.branch && x.branch.on === on ? x.branch.value : '';
      h += `<div class="prow" title="${esc('Which side of "' + br.name + '" plays it. Both sides: it plays whatever the user answers.')}"><span class="lab">${esc(many ? br.name : 'Branch')}</span><select class="selsel" data-f="branch" data-on="${esc(on)}"><option value=""${cur === '' ? ' selected' : ''}>Both sides</option>${Object.keys(br.options).map(o => `<option value="${esc(o)}"${cur === o ? ' selected' : ''}>${esc(optionName(on, o))} only</option>`).join('')}</select></div>`;
    }
    for (const b of Edits.branchAnchors(S, id)) {
      if (hide && b.k === hide && b.field === 'at') continue;
      const lab = optionName(b.on, b.opt), until = b.field === 'end', a = b.alt || x[b.field];
      h += `<div class="prow"><span class="lab wide">${until ? 'Until in ' : 'Anchor in '}${esc(lab)}</span><span class="val">${a && a.ref ? anchorChip(a, until ? 'until the end of' : undefined).replace('<span class="anchip"', b.cross ? '<span class="anchip bad"' : '<span class="anchip"') : '<span class="anchip"><i>' + ICO('anchor', 11) + '</i>start of the piece</span>'}${altCaret(id, b.k, b.field, lab)}</span></div>`;
      if (b.cross) h += `<div class="knote bad">${esc(x.key)} ${until ? 'lasts until' : 'hangs from'} ${esc(keyOf(a.ref))}, which does not play in ${esc(lab)}. <a class="pact pri" data-altpick="${id}|${b.k}|${b.field}">Anchor in ${esc(lab)}…</a></div>`;
      else if (b.alt && !until) h += `<div class="prow"><span class="lab wide">Offset in ${esc(lab)}</span><span class="val"></span><input class="ni tnum" data-f="altoff" data-k="${esc(b.k)}" type="text" inputmode="decimal" value="${+(+b.alt.off || 0).toFixed(3)}"><span class="u2">s</span></div>`;
    }
    return h;
  }
  /* the menu of an anchor of one side: pick another, or go back to the same one as everywhere else */
  function altItems(id, k, f) {
    const S = App.score, x = S.elements[id] || S.beats[id]; if (!x) return [];
    const isB = !!S.beats[id], ro = App.view === '3d' || (!isB && !!App.locked[x.group]), has = !!(x.alt && x.alt[k] && x.alt[k][f]);
    const p = k.split('='), lab = optionName(p[0], p[1]);
    return [{ head: 'Anchor in ' + lab + (has ? ' · ' + anchorText(x.alt[k][f]) : '') },
      ['Anchor to…', 'pick in the timeline', () => pickAnchor(id, { k, field: f }), { dis: ro }],
      [`Same anchor as in ${optionName(p[0], S.branches[p[0]].default)}`, has ? 'keeps its time if it can' : 'now', () => Act.reanchorAlt(id, k, null, f), { dis: ro || !has }]];
  }
  /* pick mode: the next click on a clip or a moment chip is the new anchor (Esc cancels; a refused one says why and you
     can pick another). The half of a clip you click picks its start or its end. */
  function pickAnchor(id, alt) {
    if (App.mode === 'v3d' && App.view !== '3d' && !App.cardOpen) setMode('all');   // picking happens in the timeline
    if (busy()) return;
    const S = App.score, isB = !!S.beats[id], x = S.elements[id] || S.beats[id]; if (!x) return;
    if (!isB && App.locked[x.group]) return toast(`${x.key} is in a locked group: unlock it first`);
    closeOverlay(); endPick();
    // an anchor for one side of a decision (alt): that side is put on screen, so the clips it can hang from are the ones that play there
    if (alt && alt.k) { const q = alt.k.split('='); if (App.sched.branch && App.sched.branch[q[0]] !== q[1]) setBranchView(q[0], q[1]); }
    App.pick = { id, last: null, k: alt && alt.k || null, field: alt && alt.field === 'end' ? 'end' : 'at' };
    const bar = document.createElement('div'); bar.className = 'pickbar'; bar.id = 'pickbar';
    bar.innerHTML = `<span class="pk-i">${ICO('anchor', 12)}</span><div class="pk-t"><span><b>Anchor ${esc((isB ? 'moment ' : '') + x.key)}${App.pick.k ? ' in ' + esc(Edits.optionLabel(App.score, App.pick.k)) : ''} to…</b> Click the clip or moment to anchor to · Esc cancels</span><span class="pk-h" id="pickhint">${PICK_HINT}</span></div><button class="pbbtn" data-pick="cancel">Cancel</button>`;
    bar.addEventListener('click', ev => { if (ev.target.closest('[data-pick=cancel]')) endPick('Anchor not changed'); });
    document.querySelector('#timeline .tlmain').appendChild(bar); $('#app').classList.add('picking');
  }
  const PICK_HINT = 'On a clip, the half you click picks its start or its end. It keeps its time with the typical user.';
  function endPick(msg) {
    const was = !!App.pick; App.pick = null;
    const b = $('#pickbar'); if (b) b.remove(); $('#app').classList.remove('picking');
    document.querySelectorAll('.pickhot').forEach(n => n.classList.remove('pickhot', 'pk-start', 'pk-end'));
    if (was && msg) toast(msg);
  }
  function pickTarget(ev) {
    const t = ev.target, mom = t.closest('.momb'); if (mom) return { ref: mom.dataset.beat, edge: 'start', el: mom };
    const c = t.closest('[data-id]'); if (!c || !c.closest('.fld')) return null;
    let edge = 'start'; if (c.classList.contains('clip')) { const r = c.getBoundingClientRect(); if (ev.clientX - r.left > r.width / 2) edge = 'end'; }
    return { ref: c.dataset.id, edge, el: c };
  }
  /* while picking, the target under the pointer says what it would be, or why not, before the click */
  function pickHover(ev) {
    if (!App.pick) return;
    const tg = pickTarget(ev), k = tg ? tg.ref + '|' + tg.edge : '';
    if (k === App.pick.last) return; App.pick.last = k;
    document.querySelectorAll('.pickhot').forEach(n => n.classList.remove('pickhot', 'pk-start', 'pk-end'));
    const h = $('#pickhint'); if (!h) return;
    if (!tg) { h.textContent = PICK_HINT; h.classList.remove('bad'); return; }
    tg.el.classList.add('pickhot', 'pk-' + tg.edge);
    const P = App.pick, r = P.k ? Edits.reanchorAlt(App.score, P.id, P.k, tg, ScoreEngine, { others: false, field: P.field }) : Edits.reanchor(App.score, P.id, tg, ScoreEngine, { others: false }), to = anchorText(tg);
    h.textContent = r.ok ? `${to[0].toUpperCase() + to.slice(1)} · it keeps its time${P.k ? ' in ' + Edits.optionLabel(App.score, P.k) + ', and nothing changes in the other side' : ''}` : 'Not there: ' + r.why; h.classList.toggle('bad', !r.ok);
  }
  function renderInspector() {
    const forKey = (App.sel || App.selRole || '') + App.insTab + (App.selMore.size ? '+' + App.selMore.size : '');
    const el = $('#inspector'), body = el.querySelector('.insbody'), st = body ? body.scrollTop : 0, same = el.dataset.for === forKey;
    let h = insTabs();
    if (App.insTab === 'notes') h += notesHTML();
    else if (App.selKind === 'role' && App.roles.roles[App.selRole]) h += roleHTML(App.selRole);
    else if (App.selKind === 'knob' && knobDef(App.sel)) h += knobHTML(App.sel);
    else if (App.selKind === 'beat' && App.score.beats[App.sel]) h += beatHTML(App.sel);
    else if (App.selKind === 'el' && El(App.sel)) h += App.selMore.size ? multiHTML(selIds()) : elementHTML(App.sel);
    else h += `<div class="insbody"><div class="insEmpty">Select an item<br>in the timeline or the library</div></div>`;
    // a note being written keeps the caret through a redraw (only notes: a field that commits on blur must not get it back)
    const fa = document.activeElement, fq = fa && el.contains(fa) ? (fa.id === 'noteIn' ? '#noteIn' : fa.dataset.noteEdit ? `[data-note-edit="${fa.dataset.noteEdit}"]` : null) : null, fc = fq ? [fa.selectionStart, fa.selectionEnd] : null;
    el.innerHTML = h; el.dataset.for = forKey;
    if (fq) { const n = el.querySelector(fq); if (n) { n.focus(); n.setSelectionRange(fc[0], fc[1]); } }
    const le = App.selKind === 'el' && !App.selMore.size && El(App.sel);
    if (le && App.locked[le.group]) {   // locked group: everything here is read-only
      el.querySelectorAll('.insbody input, .insbody select, .insbody textarea, [data-act=del], [data-act=wav], [data-ancmenu], [data-altmenu]').forEach(n => { n.disabled = true; n.title = 'Locked group: unlock it in the timeline'; });
      const b = el.querySelector('.insbody'); if (b) b.insertAdjacentHTML('afterbegin', `<div class="knote warn" style="margin-top:8px;">${ICO('lock', 11)} ${esc(hueName(le.group))} is locked: nothing here can change. Unlock it from the group header.</div>`);
    }
    if (same) { const b = el.querySelector('.insbody'); if (b) b.scrollTop = st; }
  }
  function knobHTML(name) {
    const d = knobDef(name), live = knobLive(name), b = knobBind(name), pend = pendingVals()[name], mot = App.score.propuestas && App.score.propuestas.motivos[name];
    const sentV = App.prop && App.prop.estado === 'enviada' && App.prop.valores ? App.prop.valores[name] : undefined;
    const rows = App.pdrift ? App.pdrift.rows.filter(r => r.knob === name) : [], ST = App.pdef.stages;
    let h = `<div class="insbody">${head('#5E6570', 'hourglass', name, `Partitura · ${esc(d.category.replace(/^\d+ /, ''))} · ${d.type === 'a5' ? 'one value per stage' : 'seconds'}`)}<div class="knote" style="color:var(--ink-2);">${esc(d.doc)}</div>`;
    const cell = (r, i) => { const off = r && r.diff != null && Math.abs(r.diff) > .05; const el = r && r.els.length ? r.els[r.els.length - 1] : null;
      return `<div class="prow"><span class="lab" style="width:78px;">${i == null ? 'Value' : esc(ST[i])}</span><span class="val tnum">Unreal <b style="color:var(--ink);font-weight:500;">${fmtV(Array.isArray(live) ? live[i] : live)} s</b> · score ${r && r.score != null ? `<span style="color:${off ? 'var(--auto-ovr)' : 'var(--ink)'}">${fmtV(r.score)} s</span>` : '—'}</span>${el ? `<span class="anchip" data-goto="${el}" title="Show it in the timeline">${esc(keyOf(el))}</span>` : ''}</div>`; };
    h += sec('kval', 'Unreal and the score', (d.type === 'a5' || (b && b.perStage) ? ST.map((_, i) => cell(rows.find(r => r.stage === i), i)).join('') : cell(rows[0], null))
      + (d.type !== 'a5' && b && b.perStage ? '<div class="knote">One value for the 5 stages in Unreal.</div>' : '')
      + (!b ? '<div class="knote">No element of the score is bound to this knob yet (obra/unreal/partitura_binding.json).</div>' : '')
      + (b && b.approx ? `<div class="knote warn">Approximate: ${esc(b.approx)}</div>` : '')
      + (b ? `<div style="padding:4px 12px 8px;"><button class="mbtn" data-act="psync1" title="Change the bound elements of the score so they do what Unreal does (one undoable edit)">Match the score to Unreal</button></div>` : ''));
    const first = rows.find(r => r.score != null);
    const sugg = first ? first.score : Array.isArray(live) ? live[0] : live;
    h += sec('kprop', 'Change it in Unreal', (pend != null ? `<div class="prow"><span class="lab">Waiting</span><span class="val tnum" style="color:var(--ink);">${fmtV(pend)} s${mot ? ` · ${esc(mot.por)} · "${esc(mot.motivo)}"` : ''}</span><button class="mbtn" data-act="punprop" style="height:20px;padding:0 8px;font-size:10.5px;">Remove</button></div>` : '')
      + (sentV !== undefined ? `<div class="prow"><span class="lab">Sent</span><span class="val tnum" style="color:var(--auto-ovr);">${fmtV(sentV)} s · waiting for Unreal</span></div>` : '')
      + (d.type === 'a5' ? `<div class="prow"><span class="lab">Stage</span><select class="selsel" id="pStage"><option value="">All stages</option>${ST.map((n, i) => `<option value="${i}">${esc(n)}</option>`).join('')}</select></div>` : '')
      + `<div class="prow"><span class="lab">New value</span><span class="val"></span><input class="ni tnum" id="pVal" type="text" inputmode="decimal" value="${+(+sugg).toFixed(2)}"><span class="u2">s</span></div>`
      + `<div class="prow"><span class="lab">Why</span><input class="nmin" id="pWhy" placeholder="12+ characters, travels with the proposal" spellcheck="false"></div>`
      + `<div style="padding:4px 12px 4px;display:flex;gap:6px;"><button class="mbtn" data-act="pprop" title="It waits in this score; nothing reaches Unreal yet">Add to the changes for Unreal</button>${Object.keys(pendingVals()).length ? `<button class="mbtn pri" data-send>Send to Unreal…</button>` : ''}</div>`
      + `<div class="knote">Nothing reaches Unreal until you press <b>Send to Unreal</b> and confirm. Then a session with Unreal open applies it only when asked, keeps a backup of the previous values, runs the smoke test and puts the backup back if anything fails.</div>`);
    return h + '</div>';
  }
  function roleHTML(name) {
    const R = App.roles.roles[name];
    const used = Object.entries(App.score.elements).filter(([, e]) => roleFor(e) === name);
    return `<div class="insbody">${head(R.icon === 'alma' ? '#8468BE' : App.HUE.obj, R.icon, name, `Role · ${esc(R.actor)}`)}`
      + sec('knobs', 'Knobs', knobGroups(name))
      + sec('sounds', 'Sounds', R.sounds && R.sounds.length ? R.sounds.map(s => `<div class="prow"><span class="val">${esc(s[0])} · ${esc(s[1])}</span><span class="chip ${s[2] === 'real' ? 'ok' : 'prov'}">${esc(s[2])}</span></div>`).join('') : '<div class="knote">No sounds of its own in Unreal.</div>')
      + sec('used', `In the score · ${used.length}`, used.slice(0, 40).map(([id, e]) => `<div class="prow"><span class="val"><a data-goto="${id}" style="cursor:pointer;color:var(--ink);">${esc(e.key)}</a> · ${tc(App.sched.t[id][0])}</span></div>`).join('') + (R.used || []).map(u => `<div class="knote">${esc(u)}</div>`).join(''))
      + '</div>';
  }
  function beatHTML(b) {
    const B = App.score.beats[b], T = App.sched.t[b], order = App.score.acts.flatMap(a => a.beats), prev = order[order.indexOf(b) - 1];
    const at = B.at || (prev ? { ref: prev, edge: 'end', off: 0 } : { ref: null, edge: 'start', off: 0 });
    const els = Object.entries(App.score.elements).filter(([, e]) => e.beat === b).sort((x, y) => App.sched.t[x[0]][0] - App.sched.t[y[0]][0]);
    return `<div class="insbody">${head('#5E6570', 'flag', B.key + ' · ' + B.title, `Moment · ${tc(T[0])} · ${fmtS(T[1] - T[0])} s`)}`
      + (B.desc ? `<div class="knote" style="color:var(--ink-2);">${esc(B.desc)}</div>` : '')
      + sec('time', 'Time', prowTxt('Starts', anchorChip(at) + anchorCaret(b) + ` <span class="tnum" style="color:var(--ink-3);margin-left:4px;">${tc(T[0])}</span>`)
        + prowIn('Offset', 'beatoff', at.off || 0, 's', 'Seconds after its anchor. Everything after this moment moves with it.')
        + prowTxt('Ends', `${tc(T[1])} · with its last element`) + branchRowsHTML(b))
      + (App.adv ? marksHTML(b) : '')
      + sec('els', `Elements · ${els.length}`, els.map(([id, e]) => `<div class="prow"><span class="mdot" style="background:${hueOf(e.group)}"></span><span class="val"><a data-goto="${id}" style="cursor:pointer;color:var(--ink);">${esc(e.key)}</a> · ${KIND[e.type] || e.type}</span><span class="u2 tnum">${fmtS(App.sched.t[id][0] - T[0])}</span></div>`).join(''))
      + (App.adv ? '' : details(marksHTML(b)))
      + '</div>';
  }
  /* the recording of a voice: final mix, an earlier take, or none yet */
  function recordingHTML(id, e, dur) {
    const sid = Media.soundId(e), m = App.media && App.media[sid];   // its recording: a rename keeps it
    if (!App.media) return prowTxt('Recording', '<span style="color:var(--ink-3)">not found · the server looks in Recursos/Soul Charger - Escritorio 2026-10/Audio</span>');
    if (!m) return prowTxt('Recording', '<span style="color:var(--auto-ovr)">none yet</span>');
    const lis = `<a class="pact" data-listen="${esc(sid)}" title="${esc(m.file)}">${App.listening === sid ? 'Stop' : 'Listen'}</a>`;
    if (m.src !== 'mix') return prowTxt('Recording', `earlier take · ${esc(m.file)} ${lis}`) + `<div class="knote">Not in the final mix: its length here stays an estimate.</div>`;
    const off = !(e.end && e.end.ref) && Math.abs(dur - m.dur) > .05;
    return prowTxt('Recording', `final mix · ${fmtS(m.dur)} s ${lis}`)
      + (off ? `<div class="knote" style="color:var(--auto-ovr)">Here it lasts ${fmtS(dur)} s; in Unreal it lasts its recording. <a class="pact pri" data-act="vreal">Use ${fmtS(m.dur)} s</a></div>` : '');
  }
  /* the file of a sound effect or an ambience (obra/audio/media_map.json): what the 3D plays, or why there is none yet.
     Its length is shown, never offered: the clip's time comes from the timeline (owner rule) */
  function soundFileHTML(e) {
    const sid = Media.soundId(e), m = Media.fileOf(e, App.media), amb = e.type === 'ambience';
    const h = prowTxt('Sound', esc(sid || '—'));
    if (!App.media) return h + prowTxt('File', '<span style="color:var(--ink-3)">not found · the editor\'s server gave no sound files</span>');
    if (!m) {
      const why = (App.mediaUnmapped || {})[sid];
      return h + prowTxt('File', '<span style="color:var(--auto-ovr)">no file yet</span>')
        + `<div class="knote">${why ? esc(why) + ' ' : 'Nothing in obra/audio/media_map.json for it. '}${amb ? '' : 'The 3D plays the prototype\'s marker for it.'}</div>`;
    }
    const lis = `<a class="pact" data-listen="${esc(sid)}" title="${esc(m.path || m.file)}">${App.listening === sid ? 'Stop' : 'Listen'}</a>`;
    return h + prowTxt('File', `<span title="${esc(m.path || m.file)}">${esc(m.file)}</span>${m.dur ? ' · ' + fmtS(m.dur) + ' s' : ''} ${lis}`)
      + `<div class="knote">${m.why ? esc(m.why) + '<br>' : ''}With Sound on, the 3D plays it ${amb ? 'from its clip, looping until the next ambience' : 'at its clip\'s time, to its own end'}${m.gain != null ? `, at Unreal's volume (${m.gain})` : ''}. Its length never changes the score.</div>`;
  }
  /* where an element stands with Unreal (lote 5 design A §3.3, js/reach.js): its answer in words, and for a cue (or what could be one
     once the score is bound) the cue it is: how long after which Unreal mark, doing what, with which asset */
  function reachHTML(id) {
    const r = App.reach && App.reach.of[id]; if (!r) return '';
    let h = prowTxt('Reach', `<span class="chip${r.reach === 'knob' || r.reach === 'cue' ? ' ok' : ''}">${esc((App.adv ? Reach.REACH_WORD : Simple.REACH_WORD)[r.reach])}</span>`, App.adv ? 'Reaches Unreal: a Partitura knob sets its time · Wired: Unreal decides it · Cue-ready: bound to an Unreal mark and asset · Preview: only the editor and the 3D know it' : Simple.REACH_HELP)
      + `<div class="knote" style="color:var(--ink-2);">${esc(App.adv ? r.why : Simple.plainWhy(r.why))}</div>`;
    if (r.cue) {
      const c = r.cue, off = Math.abs(c.offset) < 1e-6 ? 'at' : `${fmtS(c.offset)} s after`;
      h += prowTxt(r.reach === 'cue' ? 'Cue' : 'Would be', esc(`${off} ${Marks.label(c.mark)} · ${Reach.ACTION_WORD[c.action] || c.action}${c.asset ? ' · ' + c.asset : ''}${c.target ? ' → ' + c.target : ''}`), c.path || c.mark);
      if (r.state === 'no-player') h += '<div class="knote">There is no cue player in Unreal yet (BP_ScorePlayer_SC): nothing plays it from the score.</div>';
    }
    // the binding of a bound element that is not (yet) a cue: what it is in Unreal (a cue shows the same in its own row)
    const bd = El(id).bind;
    if (bd && !r.cue && (bd.action || bd.asset || bd.target)) h += prowTxt('Bound to', esc(`${bd.action ? Reach.ACTION_WORD[bd.action] || bd.action : 'no action'}${bd.asset ? ' · ' + bd.asset : ''}${bd.target ? ' → ' + bd.target : ''}`), 'Who this element is in Unreal (Bind to Unreal): action, asset in Content, role');
    return h;
  }
  /* the Unreal marks of a moment, once the score is bound (lote 5 design A §3.1): how the moment relates to Unreal's own clock */
  const REL_WORD = { start: 'Starts at', el: 'Mark at', in: 'Inside', sub: 'Inside', preview: 'Preview' };
  function marksHTML(b) {
    const ms = App.score.beats[b].marks; if (!Array.isArray(ms) || !ms.length) return '';
    return sec('unreal', 'Unreal', ms.map(m => {
      const el = m.rel === 'el' && El(m.el), extra = (m.by && m.by.length ? ' · ' + m.by.join(', ') : '') + (m.why ? ' · ' + m.why : '');
      return prowTxt(REL_WORD[m.rel] || m.rel, esc(Marks.label(m.name) + (el ? ' · ' + el.key + (m.edge === 'end' ? ' (end)' : '') : '') + extra), Marks.describe(m.name) + (m.note ? ' · ' + m.note : ''));
    }).join(''));
  }
  function elementHTML(id) {
    const e = El(id), T = App.sched.t[id], hue = hueOf(e.group), g = App.score.groups.find(x => x.id === e.group), B = App.score.beats[e.beat];
    const dur = T[1] - T[0], role = roleFor(e), con = Integrity.contractFor(id, e, App.contract);
    const meta = `${KIND[e.type] || e.type} · ${isInstant(e) ? 'instant' : fmtS(dur) + ' s'} · ${esc(B ? B.key : '—')}${e.branch ? ' · ' + esc(Integrity.branchText(App.score, { [e.branch.on]: e.branch.value })) + ' only' : ''}${e.isNew ? ' · <span style="color:var(--auto-ovr)">not in Unreal yet</span>' : ''}`;
    let h = `<div class="insbody">${head(hue, e.isNew && hasAudio(e) ? 'sound' : ICON[e.type] || 'obj', e.key, meta)}`;
    if (e.label && e.label !== e.key) h += `<div class="knote" style="color:var(--ink-2);">${esc(e.label)}</div>`;
    if (e.note) h += `<div class="knote">${esc(e.note)}</div>`;
    // time
    let durRow;
    if (e.gate) durRow = prowTxt('Duration', `${fmtS(dur)} s · ${persona().name.toLowerCase()} user`);
    else if (e.end && e.end.ref) durRow = prowTxt('Lasts', anchorChip(e.end, 'until the end of').replace('after', 'until'));
    else if (isInstant(e)) durRow = prowTxt('Duration', e.type === 'sound' ? 'instant · the file plays to its end' : e.type === 'ambience' ? 'instant · until the next ambience' : 'instant');
    else if (e.dur.mode === 'audio') durRow = prowTxt('Duration', e.audio && e.audio.dur ? `${fmtS(dur)} s · its recording <span class="lock" title="A voice lasts as long as its recording; the pause after it is its own knob in Unreal">${ICO('lock', 11)}</span>` : `${fmtS(dur)} s · <span style="color:var(--auto-ovr)">estimated from the words</span>`);
    else durRow = prowIn('Duration', 'dur', e.dur.value, 's', 'Fixed duration. Drag the right edge of the clip, or type it here.');
    const laneOpts = g.lanes.map(l => `<option value="${l}"${l === e.lane ? ' selected' : ''}>${esc(App.score.lanes[l].name)}</option>`).join('');
    // the side on screen (schema 3), where this clip hangs from something of its own (alt): that anchor is what its time here comes
    // from, so it is the one the Starts and Offset rows show and change (the primary one is the other side's)
    const ak = Edits.altKeyOf(e, viewKeys()), aAt = ak && e.alt[ak].at, aLab = ak ? optionName(ak.split('=')[0], ak.split('=')[1]) : '';
    const startsRow = ak
      ? prowTxt('Starts', anchorChip(aAt) + altCaret(id, ak, 'at', aLab) + ` <span class="tnum" style="color:var(--ink-3);margin-left:4px;">${tc(T[0])} · in ${esc(aLab)}</span>`, `In ${aLab} this clip hangs from something of its own; the anchor it has in the other side is listed below.`)
      : prowTxt('Starts', anchorChip(e.at) + anchorCaret(id) + ` <span class="tnum" style="color:var(--ink-3);margin-left:4px;">${tc(T[0])}</span>`);
    const offRow = ak ? prowIn('Offset', 'altoff', aAt.off || 0, 's', `Seconds after its anchor in ${aLab}. It does not change where this clip is in the other side.`, null, ak)
      : prowIn('Offset', 'off', (e.at && e.at.off) || 0, 's', 'Seconds after its anchor. Elements anchored to this one move with it.');
    h += sec('time', 'Time', startsRow + offRow
      + durRow + branchRowsHTML(id, ak)
      + `<div class="prow"><span class="lab">Lane</span><select class="selsel" data-f="lane">${laneOpts}</select></div>`);
    // wait
    if (e.gate) {
      // schema 3 knows whether a wait stops the stage (as in Unreal) or runs on the stage's clock; schema 2 has no flag: it always stops
      const helps = Object.entries(App.score.elements).filter(([, x]) => x.help === id), clock = View.clockWait(e), s3 = App.score.schema >= 3;
      const users = View.waitUsers(App.score, ScoreEngine, id);
      const pers = users.map(u => `<div data-pers="${u.k}" class="${App.persona === u.k ? 'on' : ''}" title="${esc(u.note)}"><span>${u.name}</span><b class="tnum">${clock ? 'acts at ' : ''}${fmtS(u.acts)} s</b><span>${u.help == null ? '—' : u.help ? 'help plays' : 'no help'}</span></div>`).join('');
      const c = con.find(x => x.kind === 'knob' && x.knob);
      const flag = s3 ? `<div class="prow"><label class="chk" title="${esc(clock ? 'The stage runs on its clock; the user only decides whether the help line plays and when what hangs from the end of the wait happens.' : 'The stage stops here until the user acts, or the timeout runs out.')}"><input type="checkbox" data-f="blocking"${clock ? '' : ' checked'}><span>Waits for the user (as in Unreal)</span></label></div>` : '';
      h += sec('wait', 'Wait', flag
        + prowIn('Expected', 'exp', e.gate.expected, 's', clock ? "The stage's clock for this wait, and when a typical user acts. A simulation value: it never reaches Unreal." : 'How long a typical user takes. A simulation value: it never reaches Unreal.')
        + (clock ? prowIn('Gives up at', 'fw', e.gate.fw, 's') + '<div class="knote">Simulation only: in Unreal the stage runs on its clock.</div>'
          : prowIn('Timeout', 'fw', e.gate.fw, 's', c ? `${c.knob.name} in ${c.owner}` : 'After this the piece moves on by itself.'))
        + (c ? prowTxt('In Unreal', `${esc(c.knob.name)} = ${c.knob.value} s${c.knob.lock ? ' <span class="lock">' + ICO('lock', 11) + '</span>' : ''}`) : '')
        + prowTxt('Help', helps.length ? helps.map(([hid, x]) => `<span class="anchip" data-goto="${hid}">${ICO('wave', 11)} ${esc(x.key)}</span>`).join(' ') : '<span style="color:var(--auto-ovr)">none · every wait needs a help line</span>')
        + `<div class="knote">${clock ? 'Simulated users: when each one acts (the stage does not wait for them)' : 'Simulated users (not Unreal values):'}</div><div class="perstab${clock ? ' acts' : ''}">${pers}</div>`);
    }
    // voice
    if (e.type === 'vo') {
      h += sec('voice', 'Voice', `<textarea class="vtext" data-f="text" spellcheck="false">${esc(e.text || '')}</textarea>`
        + recordingHTML(id, e, dur)
        + prowTxt('From', 'Alma (2D)')
        + (e.help ? prowTxt('Helps', anchorChip({ ref: e.help, edge: 'start' })) : '')
        + `<div class="knote">${e.isNew || !App.media || !App.media[Media.soundId(e)] ? 'Until it is recorded, changing the words re-estimates its length (1 s + words ÷ 2.4 + 0.5 s per ellipsis).' : 'The recording sets its length: changing the words here changes the subtitle, not the time.'}</div>`);
    }
    // sound (a new or copied element that is not a sound has no file to load: C10; a new wait neither)
    if (e.isNew && hasAudio(e)) h += sec('sound', 'Sound', newSoundHTML(id, e));
    else if (e.type === 'sound' || e.type === 'ambience') h += sec('sound', 'Sound', soundFileHTML(e) + (e.simOnly ? `<div class="knote">Simulation only: it doesn't exist in Unreal.</div>` : ''));
    else if (e.type === 'haptic') h += sec('sound', 'Sound', prowTxt('File', `${esc(e.sound || e.key)} ${previewChip()}`) + (e.simOnly ? `<div class="knote">Simulation only: it doesn't exist in Unreal.</div>` : ''));
    if (e.type === 'instruction' && (e.hint || e.ghost)) h += sec('ghost', 'Instruction', prowTxt('Ghost', esc(e.ghost || '—')) + (e.hint ? `<div class="knote" style="color:var(--ink-2);">"${esc(e.hint)}"</div>` : ''));
    const tech = App.adv ? null : [], put = x => { if (tech) tech.push(x); else h += x; };   // Simple: the Unreal-internal sections wait for the Details row
    if (role) put(sec('knobs', `${esc(role)} · knobs`, knobGroups(role)));
    // unreal
    put(sec('unreal', 'Unreal', reachHTML(id) + (con.length ? con.map(c => `<div class="owner"><b>${esc(kindWord(c.kind))}</b><span class="sc">${esc(c.owner || '')}${c.graph ? ' › ' + esc(c.graph) : ''}</span></div><div class="knote">${esc(c.msg)}</div>`).join('')
      : e.copyOf || e.isNew || !App.reach ? `<div class="knote">${e.copyOf ? 'A copy made in the editor: Unreal does not have it, whatever the original is wired to. It reaches the APK only when it is wired in Unreal; the original stays as it is.' : e.isNew ? 'New: it reaches Content after the next import and the APK only when a cue uses it.' : 'No contract entry yet: this element is a preview of the narrative prototype until the score is wired to Unreal (phase F4).'}</div>` : '')));
    const mine = App.problems.filter(p => p.el === id);
    if (mine.length) h += sec('pb', `Problems · ${mine.length}`, mine.map(p => `<div class="knote ${p.st === 'accepted' ? 'warn' : p.sv === 'info' ? '' : 'bad'}">${p.st === 'accepted' ? 'Accepted · ' : ''}${esc(p.msg)}${p.reason ? ` · "${esc(p.reason)}"` : ''}${p.was ? ` <i class="reop">${esc(Integrity.reopenedText(p))}</i>` : ''}</div>`).join(''));
    const gv = (App.gov || {})[id];
    if (gv && gv.length) put(sec('ptime', 'Unreal timing', gv.map(g => { const r = App.pdrift && App.pdrift.rows.find(x => x.knob === g.knob && x.stage === g.stage); const lv = knobLive(g.knob); const v = Array.isArray(lv) ? lv[g.stage] : lv; const off = r && r.diff != null && Math.abs(r.diff) > .05;
      return `<div class="prow"><span class="val"><a data-knobgo="${g.knob}" style="cursor:pointer;color:var(--ink);">${esc(g.knob)}</a>${g.stage != null ? ' · ' + esc(App.pdef.stages[g.stage]) : ''}</span><span class="u2 tnum" style="color:${off ? 'var(--auto-ovr)' : 'var(--ink-3)'};">${fmtV(v)} s${off ? ' · score ' + fmtV(r.score) : ''}</span></div>`; }).join('')
      + '<div class="knote">These times are decided by DA_Partitura_Obra in Unreal. Editing them here changes the score only; propose the new value from the knob to reach the APK.</div>'));
    if (e.legacy) put(sec('legacy', 'Origin', prowTxt('Prototype', esc(e.legacy.uid)) + prowTxt('Track', esc(e.legacy.track))));
    else if (e.copyOf) put(sec('legacy', 'Origin', prowTxt('Copy of', El(e.copyOf) ? `<span class="anchip" data-goto="${e.copyOf}" title="Select the original">${esc(El(e.copyOf).key)}</span>` : 'an element that no longer exists') + '<div class="knote">No 3D yet: the preview has only what the prototype has.</div>'));
    if (tech) h += details(tech.join(''), App.reach && App.reach.of[id] ? Simple.REACH_WORD[App.reach.of[id].reach] : '');
    h += `<div style="padding:10px 12px 16px;display:flex;gap:6px;"><button class="mbtn" data-act="del" title="Delete · Del">${ICO('trash', 12)} Delete</button></div>`;
    return h + '</div>';
  }
  /* several selected (audit C10): what they are, where, and the verbs that act on all of them */
  function multiHTML(ids) {
    const T = App.sched.t, els = ids.map(El), s0 = Math.min(...ids.map(id => T[id][0])), s1 = Math.max(...ids.map(id => T[id][1]));
    const kinds = {}; for (const e of els) { const k = KIND[e.type] || e.type; kinds[k] = (kinds[k] || 0) + 1; }
    const beats = [...new Set(ids.slice().sort((a, b) => T[a][0] - T[b][0]).map(id => El(id).beat))].map(b => App.score.beats[b].key);
    const locked = els.filter(e => App.locked[e.group]), fresh = els.filter(e => e.isNew).length, ro = !!locked.length || App.view === '3d';
    const wired = ids.filter(id => Integrity.contractFor(id, El(id), App.contract).length || (App.gov || {})[id]).length;
    const rk = App.reach ? ids.reduce((a, id) => { a[(App.reach.of[id] || { reach: 'preview' }).reach]++; return a; }, { knob: 0, wired: 0, cue: 0, preview: 0 }) : null;
    const order = ids.slice().sort((a, b) => T[a][0] - T[b][0]), shown = order.slice(0, 14);
    let h = `<div class="insbody">${head('#5E6570', 'copy', ids.length + ' selected', `${Object.entries(kinds).map(([k, n]) => n + ' ' + k.toLowerCase() + (n > 1 && !/s$/.test(k) ? 's' : '')).join(' · ')} · ${tc(s0)} → ${tc(s1)}`)}`;
    if (locked.length) h += `<div class="knote warn" style="margin-top:8px;">${ICO('lock', 11)} ${esc(keysText(locked.map(e => e.key)))} ${locked.length > 1 ? 'are' : 'is'} in a locked group: nothing can move or be deleted until you unlock it (or take ${locked.length > 1 ? 'them' : 'it'} out with Ctrl+click).</div>`;
    h += sec('msel', `Selection · ${beats.length > 1 ? beats.length + ' moments' : 'moment ' + esc(beats[0])}`, shown.map(id => { const e = El(id); return `<div class="prow"><span class="mdot" style="background:${hueOf(e.group)}"></span><span class="val">${id === App.sel ? '<b style="color:var(--ink);font-weight:600;">' + esc(e.key) + '</b>' : esc(e.key)} · ${KIND[e.type] || e.type}${e.isNew ? ' · <span style="color:var(--auto-ovr)">new</span>' : ''}</span><span class="u2 tnum">${tc(T[id][0])}</span></div>`; }).join('')
      + (order.length > shown.length ? `<div class="knote">and ${order.length - shown.length} more</div>` : '')
      + '<div class="knote">Ctrl+click a clip takes it out or adds it · Shift+click adds · Esc clears.</div>');
    h += sec('mtime', 'Move', prowIn('Nudge', 'mnudge', 0, 's', 'Moves every selected clip by this many seconds, in one step. What hangs from them follows; a clip anchored to another selected one is not moved twice.').replace('<input', ro ? '<input disabled' : '<input')
      + '<div class="knote">Or drag any of them (Ctrl+drag: what hangs from them stays) · Alt+←/→ nudges 0.1 s (with Shift, 1 s).</div>');
    const mun = sec('munreal', 'Unreal', `<div class="knote">${rk ? (App.adv ? `${rk.knob} reach Unreal (timing) · ${rk.wired} wired${rk.cue ? ' · ' + rk.cue + ' cue-ready' : ''} · ${rk.preview} preview` : `${rk.knob} reach Unreal (timing) · ${rk.wired} set by Unreal${rk.cue ? ' · ' + rk.cue + ' can become an Unreal cue' : ''} · ${rk.preview} only in the preview`) : `${wired} of ${ids.length} ${wired === 1 ? 'is' : 'are'} checked against Unreal`}${fresh ? ` · ${fresh} new: not in Unreal yet` : ''}. A copy or a duplicate is always new: Unreal does not have it until it is wired there.</div>`);
    h += App.adv ? mun : details(mun);
    h += `<div style="padding:10px 12px 16px;display:flex;gap:6px;flex-wrap:wrap;"><button class="mbtn" data-act="mcopy" title="Copy · Ctrl+C">${ICO('copy', 12)} Copy</button><button class="mbtn" data-act="mdup" title="Duplicate right after itself · Ctrl+D"${ro ? ' disabled' : ''}>${ICO('copy', 12)} Duplicate</button><button class="mbtn" data-act="del" title="Delete all of them · Del"${ro ? ' disabled' : ''}>${ICO('trash', 12)} Delete ${ids.length}</button></div>`;
    return h + '</div>';
  }
  function newSoundHTML(id, e) {
    const a = e.audio;
    let fmt = '';
    if (a) fmt = `<div class="prow"><span class="lab">Format</span><span class="val wavinfo"><span class="${a.sr === 48000 ? 'ok' : 'warn'}">${(a.sr / 1000).toFixed(a.sr % 1000 ? 1 : 0)} kHz</span> · <span class="${a.ch === 1 ? 'ok' : 'warn'}">${a.ch === 1 ? 'mono' : a.ch + ' ch'}</span> · <span class="${a.pcm ? 'ok' : 'warn'}">${a.pcm ? 'PCM' : 'not PCM'} ${a.bits}-bit</span></span></div>`
      + (a.sr !== 48000 ? '<div class="knote warn">The project runs at 48 kHz: this file will be resampled.</div>' : '')
      + (a.ch > 1 ? '<div class="knote warn">Sounds placed on an object should be mono.</div>' : '');
    return `<div class="prow"><span class="lab">Name</span><input class="nmin" data-f="name" value="${esc(e.key)}" spellcheck="false" aria-label="Sound name"></div>`
      + (a ? prowTxt('File', `${esc(a.file)} · ${fmtS(a.dur)} s <button class="mbtn" data-act="play" style="height:18px;padding:0 6px;font-size:10px;margin-left:6px;">▶</button>`) + fmt
        + `<div class="prow"><span class="lab"></span><button class="mbtn" data-act="wav" style="height:20px;padding:0 8px;font-size:11px;">Replace WAV…</button></div>`
        : `<div class="drop" data-drop>${ICO('upload', 14)}<span>Drop a WAV here</span><button class="mbtn" data-act="wav" style="height:22px;padding:0 10px;">Load WAV…</button></div>`)
      + prowTxt('Goes to', `Obra/Audio/Placeholder/${esc(e.key)}`)
      + (a && a.inbox ? prowTxt('Waiting in', esc(a.inbox)) : '')
      + `<div class="knote">On the next import it becomes a SoundWave with this name. Keep the source WAV: Unreal's auto-import deletes the asset if the file disappears.</div>`;
  }
  /* notes for the team (audit C13): each one can be edited, resolved (dimmed, here and on the ruler) or reopened, and deleted.
     Read-only in the 3D tab. What is being typed lives in App (noteNew, noteDraft) so a redraw never loses it. */
  function notesHTML() {
    const N = Object.entries(App.score.notes || {}).sort((a, b) => a[1].t - b[1].t), ro = App.view === '3d';
    const about = App.selKind === 'el' && El(App.sel) ? ' about ' + El(App.sel).key : '';
    const who = w => (WHO[w] || { n: w || '?' }).n;
    const add = ro ? '<div class="knote" style="padding:8px 2px 0;">Read-only here: add and edit notes in the timeline tab.</div>'
      : `<div style="padding:8px 12px;border-bottom:.5px solid var(--line-soft);"><textarea class="vtext" id="noteIn" placeholder="Note at ${tc(App.ph)}${esc(about)} for the team…" spellcheck="false" style="margin:0;width:100%;">${esc(App.noteNew || '')}</textarea><div style="display:flex;align-items:center;justify-content:flex-end;gap:8px;margin-top:6px;"><span class="nhint">Ctrl+Enter adds</span><button class="mbtn" data-act="addnote" style="height:22px;">Add note · ${WHO[App.who].n}</button></div></div>`;
    const row = ([nid, n]) => {
      const ed = !ro && App.noteEdit === nid, done = !!n.resolved;
      const meta = `<span class="tnum" data-seek="${n.t}" title="Go to it">${tc(n.t)} · ${esc(App.score.beats[beatAt(n.t)].key)}${n.el && El(n.el) ? ` · <a data-goto="${n.el}" title="Select it">${esc(El(n.el).key)}</a>` : ''}</span>`;
      const body = ed ? `<textarea class="vtext" data-note-edit="${nid}" spellcheck="false" style="margin:2px 0 0;width:100%;">${esc(App.noteDraft != null ? App.noteDraft : n.text)}</textarea><div class="nact"><a class="pact pri" data-note="save">Save</a><a class="pact" data-note="cancel">Cancel</a><span class="nhint">Ctrl+Enter saves · Esc cancels</span></div>`
        : `<p>${esc(n.text)}</p>`;
      const state = [n.edited ? `edited by ${esc(who(n.edited.who))}` : '', done ? `resolved by ${esc(who(n.resolved.who))}` : ''].filter(Boolean).join(' · ');
      const acts = ro || ed ? '' : `<div class="nact"><a class="pact" data-note="edit">Edit</a><a class="pact" data-note="${done ? 'reopen' : 'resolve'}">${done ? 'Reopen' : 'Resolve'}</a><a class="pact" data-note="del">Delete</a></div>`;
      return `<div class="nrow${done ? ' done' : ''}${App.noteFlash === nid ? ' flash' : ''}" data-nid="${nid}"><span class="av" style="background:${(WHO[n.who] || WHO.B).c}" title="${esc(who(n.who))}">${esc(n.who || '?')}</span><div class="nt">${meta}${body}${state ? `<div class="nst">${state}</div>` : ''}${acts}</div></div>`;
    };
    return `<div class="insbody notesl">${add}` + (N.length ? N.map(row).join('') : '<div class="knote" style="padding:12px 2px;">No notes yet.</div>') + '</div>';
  }

  /* ================= status ================= */
  function renderStatus(msg) {
    const k = pbCounts(), n = Object.keys(App.score.elements).length, e = App.selKind === 'el' && El(App.sel);
    let info = '';
    if (e && App.selMore.size) info = `<span class="statinfo"><span class="k">${App.selMore.size + 1} selected</span> — drag any of them to move them all · Alt+←/→ nudges · Del deletes · Ctrl+C copies · Ctrl+D duplicates · Esc clears</span>`;
    else if (e) {
      const con = Integrity.contractFor(App.sel, e, App.contract), lit = con.find(c => c.kind === 'literal');
      if (lit) info = App.adv ? `<span class="statinfo why"><span class="k">${esc(e.key)}</span> — hardwired in Unreal (${esc(lit.owner)}${lit.graph ? ' › ' + esc(lit.graph) : ''}) · changing it needs a graph change</span>`
        : `<span class="statinfo why" title="${esc(lit.owner + (lit.graph ? ' › ' + lit.graph : ''))}"><span class="k">${esc(e.key)}</span> — built into Unreal · changing it for real needs a change inside Unreal</span>`;
      else if (e.copyOf) info = `<span class="statinfo why"><span class="k">${esc(e.key)}</span> — copy${El(e.copyOf) ? ' of ' + esc(El(e.copyOf).key) : ''} · not in Unreal yet · drag to move, Ctrl+D duplicates it again</span>`;
      else if (e.isNew && hasAudio(e)) info = `<span class="statinfo why"><span class="k">${esc(e.key)}</span> — new sound · ${e.audio ? 'file loaded' : 'load a WAV in the inspector'}</span>`;
      else if (e.isNew && !e.gate) info = `<span class="statinfo why"><span class="k">${esc(e.key)}</span> — new, not in Unreal yet · drag to move, its anchored elements follow</span>`;
      else if (View.clockWait(e)) info = `<span class="statinfo"><span class="k">${esc(e.key)}</span> — the stage runs on its clock · the user only decides when they act and whether the help plays · drag to move, its anchored elements follow</span>`;
      else if (e.gate) info = `<span class="statinfo"><span class="k">${esc(e.key)}</span> — the user decides how long · timeout ${e.gate.fw} s · drag to move, its anchored elements follow</span>`;
      else if (e.type === 'vo') info = `<span class="statinfo"><span class="k">${esc(e.key)}</span> — lasts as long as its audio · drag to move, its anchored elements follow · Ctrl+drag moves it alone</span>`;
      else info = `<span class="statinfo"><span class="k">${esc(e.key)}</span> — drag to move, its anchored elements follow · Ctrl+drag moves it alone · Alt+←/→ nudges</span>`;
    } else if (App.selKind === 'beat') info = `<span class="statinfo"><span class="k">${esc(keyOf(App.sel))}</span> — drag its chip in the moments band: everything after it moves too</span>`;
    else if (App.selKind === 'knob') info = `<span class="statinfo"><span class="k">${esc(App.sel)}</span> — timing knob of DA_Partitura_Obra in Unreal · the score follows it, and proposes changes</span>`;
    else if (App.selKind === 'role') info = `<span class="statinfo"><span class="k">${esc(App.selRole)}</span> — knobs read from Unreal · read-only until the bridge</span>`;
    // the 3D view only plays: "drag to move", "Del deletes" would be wrong there
    if (view3d()) info = `<span class="statinfo">${App.view === '3d' ? 'This tab only shows the 3D view: edit in the timeline tab' : 'The 3D view only plays the piece: Window ▸ All-in-one or Timeline to edit'}</span>`;
    if (typeof msg === 'string') info = `<span class="statinfo">${esc(msg)}</span>`;
    const chk = Object.entries(App.score.elements).filter(([id, e]) => Integrity.contractFor(id, e, App.contract).length || (App.gov || {})[id]).length;
    // lote 5: the score minus the last Unreal run, Hall start → end (typical user); a click opens the lane and its problems
    const R = App.run, rw = R ? App.problems.filter(p => p.rule === 'C3.TRACE.STAGE' && p.st === 'open').length : 0;
    const runp = R ? `<span class="runpill${R.comparable ? '' : ' nc'}${rw ? ' off' : ''}" data-tr="run" title="${esc((R.comparable && R.total ? `The score minus the last Unreal run, from the Hall start to the end, typical user: ${tc(R.total.score)} here, ${tc(R.total.trace)} in the run. ${rw} stage${rw === 1 ? '' : 's'} differ more than ${fmtS(Calib.thresholds(App.runNoise).xStage)} s.` : 'The last Unreal run does not compare with the score: Problems ▸ Unreal run says why.') + '\n' + Calib.runLabel(R.info) + ' · click: show the lane and its problems')}">${esc(Calib.pillText(R))}</span>` : '';
    if (!App.adv) {   // Simple: one line in plain words; the counters it used to show are in its tooltip (js/simple.js)
      const rvw = Simple.review(App.problems), ed = App.editedSet ? App.editedSet.size : 0, dv = App.diverged ? App.diverged.size : 0;
      const parts = Simple.statusParts({ persona: persona().name, side: sideText(), total: Integrity.fmt(App.sched.total), review: rvw.count, dirty: App.dirty });
      const runTxt = R ? (R.comparable && R.total ? `The last Unreal run: ${tc(R.total.score)} here, ${tc(R.total.trace)} in the run, from the Hall start to the end · ${rw} stage${rw === 1 ? '' : 's'} differ.` : 'The last Unreal run does not compare with the score.') : '';
      const tip = Simple.statusTip({ side: sideText(), review: rvw.count, reach: App.reach, edited: ed, diverged: dv, accepted: k.a, rev: App.baseRev, run: runTxt });
      $('#status').innerHTML = `<span>Ready</span>${info}<div style="flex:1;"></div><span class="stline" title="${esc(tip)}">${esc(parts.who)} · <span class="pbc revw${rvw.blocks ? ' bad' : ''}" data-tr="review" title="${esc('What needs a look: blocking items and warnings that are still open. Click to open Problems · F8')}">${esc(parts.review)}</span> · <span class="${App.dirty ? '' : 'ok'}" style="${App.dirty ? 'color:var(--auto-ovr)' : ''}">${esc(parts.save)}</span></span>`;
      return;
    }
    $('#status').innerHTML = `<span>Ready</span>${info}<div style="flex:1;"></div><span class="pbc" data-tr="problems" title="Problems · F8"><b class="bl">●</b> ${k.b} blocking <i class="wa"></i> ${k.w} warnings <b class="ac">●</b> ${k.a} accepted</span>${runp}<span title="${esc(sideText() ? 'The simulated user, the side of the decision on screen, and how long the piece runs that way. Change the side in the transport (Branch).' : 'The simulated user and how long the piece runs')}">${persona().name}${sideText() ? ' · ' + esc(sideText()) : ''} · total ${Integrity.fmt(App.sched.total)} · goal 15:00</span>${App.reach ? `<span class="reachst" title="${esc(Reach.statusTitle(App.reach))}">${esc(Reach.statusText(App.reach))}</span>` : `<span title="Elements whose timing is checked against Unreal (contract or Partitura). Nothing reaches Unreal until Send to Unreal.">${chk} of ${n} checked</span>`}<span title="Elements changed since the last save · elements that differ from the APK baseline">${App.editedSet ? App.editedSet.size : 0} edited · ${App.diverged ? App.diverged.size : 0} ≠ APK</span><span class="${App.dirty ? '' : 'ok'}" style="${App.dirty ? 'color:var(--auto-ovr)' : ''}">${App.dirty ? 'unsaved · Ctrl+S' : 'score rev ' + App.baseRev + (App.savedAt ? ' · saved' : '')}</span>`;
  }

  /* ================= overlays: impact card, quick add, note ================= */
  let impactCb = null;
  function impactCard(label, items, repairs, cb, ripple) {
    closeOverlay();
    // block (or a locked final value) needs a written reason; a warning can go ahead with one click, and is still recorded (policy.js)
    const mustReason = Policy.needsReason(items), breaks = Policy.breaks(items);
    // a new anchor loop or an anchor across the sides of a decision can be accepted here, but the save refuses it until it is fixed (S.CYCLE.NEW, S.BRANCH.CROSS.NEW): say so now, not at Ctrl+S
    const noSave = items.some(i => (i.rule === 'C1.BRANCH.ANCHOR' || i.rule === 'C1.ANCHOR.CYCLE') && (i.sv === 'block' || i.sv === 'warn'));
    const dot = sv => sv === 'warn' ? '<span class="d warn"></span>' : sv === 'info' ? '<span class="d" style="background:var(--ink-3)"></span>' : '<span class="d" style="background:var(--danger)"></span>';
    const word = sv => sv === 'block' ? 'Breaks' : sv === 'inv' ? 'Needs a decision' : sv === 'warn' ? 'Check' : 'Note';
    const back = document.createElement('div'); back.className = 'impback ov';
    const d = document.createElement('div'); d.className = 'imp ov';
    d.innerHTML = `<h3>${esc(label)}<span>${items.filter(i => i.sv !== 'info').length} to review</span></h3>
      ${ripple ? `<div class="ripple">${ICO('curves', 11)} ${esc(ripple)}</div>` : ''}
      ${items.map(i => `<div class="it">${dot(i.sv)}<div style="min-width:0;"><b>${word(i.sv)} · ${esc(App.adv ? i.title : Simple.plainWhy(i.title))}</b>${esc(i.body)}${i.keys && i.keys.length > 1 ? `<div class="evl">Also: ${i.keys.slice(1, 8).map(esc).join(', ')}${i.keys.length > 8 ? '…' : ''}</div>` : ''}${i.ev ? (App.adv ? `<div class="evl">${esc(i.ev)}${i.rule ? ' · ' + esc(i.rule) : ''}</div>` : /^rule /.test(i.ev) ? '' : `<div class="evl"${i.rule ? ` title="${esc('Rule ' + i.rule)}"` : ''}>${esc(i.ev)}</div>`) : ''}${i.before && i.sv !== 'info' ? `<div class="evl prev">You accepted this ${i.before.value == null ? esc(i.before.words) : 'before at ' + esc(i.before.words)}${i.before.who ? ' (' + esc(i.before.who) + ')' : ''}${i.before.reason ? ': "' + esc(i.before.reason) + '"' : ''}${i.before.state === 'reopened' ? ' · you reopened it' : ''}</div>` : ''}</div></div>`).join('')}
      ${repairs.length ? `<div class="rep">${repairs.map((r, k) => `<label><input type="radio" name="rep" value="${r.id}"${r.checked ? ' checked' : ''}> ${esc(r.label)}</label>`).join('')}</div>` : ''}
      ${breaks ? `<div class="rep"${repairs.length ? ' style="border-top:none;"' : ''}><input class="rsn" id="rsn" placeholder="${mustReason ? 'Reason (12+ characters)' : 'Reason (optional)'} · e.g. I'll connect it to a new cue in Unreal" spellcheck="false"><span style="color:var(--ink-3);font-size:10px;">It goes to Problems as accepted, signed by ${WHO[App.who].n}. This changes the score only: the APK keeps doing what Unreal does${items.every(i => i.rule === 'C3.BLOCKING') ? '' : ' (the clip shows ≠ APK)'}.${noSave ? ' It cannot be saved until it is fixed: the save refuses it.' : ''}</span></div>` : ''}
      <div class="btns"><button data-imp="cancel">Cancel</button>${breaks ? `<button class="anyway" data-imp="anyway"${mustReason ? ' disabled' : ''}>Proceed anyway</button>` : `<button class="pri" data-imp="repair">${repairs.length ? 'Proceed and repair' : 'Proceed'}</button>`}</div>`;
    document.body.appendChild(back); document.body.appendChild(d);
    if (App.k < 1) d.style.transform = `translate(-50%,-50%) scale(${App.k})`;
    impactCb = cb;
    const rsn = d.querySelector('#rsn'), any = d.querySelector('[data-imp=anyway]');
    // accepted before: its reason is already there (a click still decides: Enter never accepts)
    const pre = items.find(i => i.sv !== 'info' && i.before && i.before.reason);
    if (rsn && pre) { rsn.value = pre.before.reason; if (mustReason && any) any.disabled = rsn.value.trim().length < 12; }
    if (rsn) { rsn.addEventListener('input', () => { if (mustReason) any.disabled = rsn.value.trim().length < 12; }); rsn.addEventListener('keydown', ev => { if (ev.key === 'Enter') ev.preventDefault(); if (ev.key === 'Escape') { ev.stopPropagation(); done('cancel'); } }); }
    // Enter never accepts a break: the default button is Cancel (a click is a decision)
    setTimeout(() => { const p = breaks ? d.querySelector('[data-imp=cancel]') : d.querySelector('.pri'); if (p) p.focus(); }, 30);
    const done = dec => { const rep = (d.querySelector('input[name=rep]:checked') || {}).value || null; const r = rsn ? rsn.value.trim() : ''; const f = impactCb; impactCb = null; back.remove(); d.remove(); f(dec, r, rep); };
    d.addEventListener('click', ev => { const b = ev.target.closest('[data-imp]'); if (b && !b.disabled) done(b.dataset.imp); });
    back.addEventListener('click', () => done('cancel'));
    d._cancel = () => done('cancel');
  }
  function scaleOv(n) { if (App.k < 1) { n.style.transformOrigin = '0 0'; n.style.transform = `scale(${App.k})`; } }
  /* review before sending to Unreal: every change, what it would break, and a confirmation */
  function sendCard(o, onSend) {
    closeOverlay();
    const ST = App.pdef.stages, blocks = o.checks.filter(c => c.sv === 'block'), warns = o.checks.filter(c => c.sv === 'warn');
    const fmtA = (a, b) => { if (!Array.isArray(b)) return `${fmtV(a)} → <strong class="nv">${fmtV(b)}</strong> s`; return b.map((x, i) => x === a[i] ? null : `${esc(ST[i])} ${fmtV(a[i])} → <strong class="nv">${fmtV(x)}</strong>`).filter(Boolean).join(' · ') + ' s'; };
    const back = document.createElement('div'); back.className = 'impback ov';
    const d = document.createElement('div'); d.className = 'imp ov';
    d.innerHTML = `<h3>Send to Unreal<span>${o.names.length} change${o.names.length > 1 ? 's' : ''}</span></h3>
      ${o.names.map(n => `<div class="it"><span class="d" style="background:var(--auto-live)"></span><div style="min-width:0;"><b>${esc(n)}</b>${fmtA(o.live[n], o.pend[n])}${o.motivos[n] ? `<div class="evl">${esc(o.motivos[n].por || '')} · "${esc(o.motivos[n].motivo || '')}"</div>` : ''}</div></div>`).join('')}
      ${blocks.map(c => `<div class="it"><span class="d" style="background:var(--danger)"></span><div><b>Would break · ${esc(c.knob)}</b>${esc(c.msg)}</div></div>`).join('')}
      ${warns.map(c => `<div class="it"><span class="d warn"></span><div><b>Check · ${esc(c.knob)}</b>${esc(c.msg)}</div></div>`).join('')}
      ${o.prevWaiting ? `<div class="also">It replaces what you sent ${esc(String(o.prevWaiting.enviado || '').replace('T', ' ').slice(5, 16))}, which Unreal has not applied yet (those changes are included).</div>` : ''}
      ${o.stale ? '<div class="also" style="color:var(--auto-ovr);">Unreal published new values after you prepared these changes: check the "before" values.</div>' : ''}
      <div class="also">What happens next: the file goes to obra/unreal/partitura_propuesta.json. A session with Unreal open applies it <b>only when asked</b>, keeps a backup of the previous values, runs the smoke test and puts the backup back if anything fails. The APK changes only after that.</div>
      <div class="btns"><button data-snd="cancel">Cancel</button><button class="pri" data-snd="send"${blocks.length ? ' disabled title="Fix what would break first"' : ''}>${blocks.length ? 'Fix the red items first' : 'Send to Unreal'}</button></div>`;
    document.body.appendChild(back); document.body.appendChild(d);
    if (App.k < 1) d.style.transform = `translate(-50%,-50%) scale(${App.k})`;
    App.cardOpen = true;
    const done = go => { App.cardOpen = false; back.remove(); d.remove(); if (go) onSend(); };
    d.addEventListener('click', ev => { const b = ev.target.closest('[data-snd]'); if (b && !b.disabled) done(b.dataset.snd === 'send'); });
    back.addEventListener('click', () => done(false));
    d._cancel = () => done(false);
  }
  /* a decision with named options (delete with dependents, import, save conflict). While open, the editor waits. */
  function chooseCard(title, body, options, cb, cancelLabel) {
    closeOverlay();
    const back = document.createElement('div'); back.className = 'impback ov';
    const d = document.createElement('div'); d.className = 'imp ov';
    d.innerHTML = `<h3>${esc(title)}</h3>${body ? `<div style="margin:-4px 0 8px;color:var(--ink-2);line-height:1.45;white-space:pre-line;">${esc(body)}</div>` : ''}
      ${options.map(o => `<button class="choice${o.primary ? ' pri' : ''}${o.danger ? ' danger' : ''}" data-ch="${o.id}"${o.disabled ? ' disabled' : ''}><b>${esc(o.label)}</b>${o.detail ? `<span>${esc(o.detail)}</span>` : ''}</button>`).join('')}
      <div class="btns"><button data-ch="cancel">${esc(cancelLabel || 'Cancel')}</button></div>`;
    document.body.appendChild(back); document.body.appendChild(d);
    if (App.k < 1) d.style.transform = `translate(-50%,-50%) scale(${App.k})`;
    App.cardOpen = true;
    const done = c => { App.cardOpen = false; back.remove(); d.remove(); if (c !== 'cancel') cb(c); };
    d.addEventListener('click', ev => { const b = ev.target.closest('[data-ch]'); if (b && !b.disabled) done(b.dataset.ch); });
    back.addEventListener('click', () => done('cancel'));
    d._cancel = () => done('cancel');
    setTimeout(() => { const f = d.querySelector('.choice.pri:not([disabled])') || d.querySelector('[data-ch=cancel]'); if (f) f.focus(); }, 30);
  }
  function closeOverlay() {
    let any = false;
    const imp = document.querySelector('.imp.ov'); if (imp && imp._cancel) { imp._cancel(); return true; }
    document.querySelectorAll('.ov').forEach(n => { n.remove(); any = true; });
    document.querySelectorAll('.menubtn.on').forEach(n => n.classList.remove('on'));
    return any;
  }
  function quickAdd(at) {
    closeOverlay();
    const d = document.createElement('div'); d.className = 'qa ov'; d.style.position = 'fixed';
    const phEl = $('#ph'), r = phEl ? phEl.getBoundingClientRect() : null, sc = $('#sctl') && $('#sctl').getBoundingClientRect();
    let x = innerWidth / 2 - 180, y = innerHeight / 2 - 160;
    if (r && sc && r.left > sc.left + HDR && r.left < sc.right - 40) { x = r.left + 10; y = sc.top + 64; }
    if (at) { x = at.x; y = at.y; }
    d.style.left = Math.min(x, innerWidth - 370 * App.k) + 'px'; d.style.top = Math.max(6, y) + 'px';
    const base = [
      { g: 'New', label: 'Empty sound…', k: 'name it, load a WAV', sw: 'transparent;border:1px dashed var(--auto-ovr)', fn: () => Act.add('sound') },
      { g: 'New', label: 'Alma voice line', k: 'text now, audio later', sw: App.HUE.vo, fn: () => Act.add('vo') },
      { g: 'New', label: 'Wait', k: 'the user decides', sw: App.HUE.int, fn: () => Act.add('wait') },
      { g: 'Mark', label: 'Bookmark', k: 'M', sw: 'var(--ink-2)', fn: () => Act.bookmark() },
      { g: 'Mark', label: 'Note for the team', k: 'Shift+M', sw: 'var(--s2)', fn: () => noteBox() },
      ...soundIndex().filter(s => !s.isNew && (s.group === 'fx' || s.group === 'amb')).map(s => ({ g: 'Sound cue', label: s.id, k: `real · used ${s.uses.length}×`, sw: hueOf(s.group), fn: () => Act.add('sound', { sound: s.id }) })),
    ];
    let hi = 0, list = base;
    const draw = q => {
      q = (q || '').toLowerCase().trim(); list = base.filter(i => !q || (i.label + ' ' + i.g).toLowerCase().includes(q)); hi = Math.min(hi, Math.max(0, list.length - 1));
      let g = '', out = '';
      list.slice(0, 60).forEach((i, n) => { if (i.g !== g) { g = i.g; out += `<div class="qg">${g}</div>`; } out += `<button data-qi="${n}" class="${n === hi ? 'on' : ''}"><span class="sw" style="background:${i.sw}"></span>${esc(i.label)}<span class="k">${esc(i.k)}</span></button>`; });
      d.querySelector('.ql').innerHTML = out || '<div class="qg">Nothing matches</div>';
      const on = d.querySelector('.ql .on'); if (on) on.scrollIntoView({ block: 'nearest' });
    };
    const b = beatAt(App.ph);
    d.innerHTML = `<input id="qaIn" placeholder="Add at the playhead…" spellcheck="false" autocomplete="off"><div class="ql"></div><div class="qf"><span>↵ adds at <b>${tc(App.ph)}</b></span><span>in <b>${esc(App.score.beats[b].key)}</b></span><span>Esc closes</span></div>`;
    document.body.appendChild(d); scaleOv(d); draw('');
    // it opens at the playhead (or the pointer): keep it inside the window. At 1280×720 its list and its footer fell below the bottom edge
    { const r = d.getBoundingClientRect(); if (r.bottom > innerHeight - 6) d.style.top = Math.max(6, innerHeight - 6 - r.height) + 'px'; }
    const inp = d.querySelector('#qaIn'); setTimeout(() => inp.focus(), 10);
    const pick = n => { const i = list[n]; if (!i) return; closeOverlay(); i.fn(); };
    inp.addEventListener('input', () => { hi = 0; draw(inp.value); });
    inp.addEventListener('keydown', ev => {
      if (ev.key === 'ArrowDown') { ev.preventDefault(); hi = Math.min(list.length - 1, hi + 1); draw(inp.value); }
      else if (ev.key === 'ArrowUp') { ev.preventDefault(); hi = Math.max(0, hi - 1); draw(inp.value); }
      else if (ev.key === 'Enter') { ev.preventDefault(); pick(hi); }
      else if (ev.key === 'Escape') { ev.preventDefault(); closeOverlay(); }
    });
    d.addEventListener('mousedown', ev => ev.stopPropagation());
    d.addEventListener('click', ev => { const btn = ev.target.closest('[data-qi]'); if (btn) pick(+btn.dataset.qi); });
  }
  /* Help ▸ Keyboard shortcuts (and ?): every shortcut, grouped, and what Premiere or Resolve do where it differs (audit C10).
     [K] is a key cap. Keep it in step with onKey/transportKey (app.js) and the README table */
  const SHORTCUTS = [
    ['Playback', [
      ['[Space]', 'Play or pause'],
      ['[L]', 'Play forward · again: 2×, then 4×'],
      ['[J]', 'Play backwards, without sound · again: 2×, then 4×'],
      ['[K]', 'Pause, and back to 1×'],
      ['[K] held + [J] / [L]', 'Step 0.1 s back / forward', 'Premiere, Resolve: one frame'],
      ['[←] / [→]', 'Move the playhead 0.1 s · with Shift, 1 s', 'Premiere, Resolve: one frame (Premiere with Shift: five)'],
      ['[↑] / [↓]', 'Start of the previous / next moment', 'Premiere, Resolve: previous / next edit point'],
      ['[Home] / [End]', 'Start / end of the piece'],
      ['[I] / [O]', 'Mark In / Out at the playhead. Play starts at In when the playhead is outside the range and stops at Out', 'Premiere, Resolve: plain Play ignores them; Play In to Out is its own command'],
      ['[Shift+I] / [Shift+O]', 'Go to In / Out'],
      ['[Alt+X]', 'Clear In and Out', 'Premiere: Ctrl+Shift+X'],
    ]],
    ['Timeline view', [
      ['[=] / [-]', 'Zoom in / out around the playhead', 'Resolve: Ctrl+= / Ctrl+-'],
      ['[\\]', 'Fit the whole piece (Piece, in the timeline bar)', 'Resolve: Shift+Z'],
      ['Moment / Act', 'Zoom to fit the moment or the act at the playhead (buttons in the timeline bar)'],
      ['Double-click a moment chip', 'Zoom to fit that moment'],
      ['[Ctrl]+wheel', 'Zoom at the pointer', 'Premiere: Alt+wheel'],
      ['[Ctrl+F]', 'Find clips and moments: by key, label or the words of a voice'],
      ['[Enter] / [Shift+Enter]', 'In the find field: select and show the next / previous match'],
      ['Hover a clip or a moment', 'Its card: what it is, when, how long, its anchor, its lane'],
      ['[S]', 'Snapping on / off (Snap, in the timeline bar)', 'Resolve: N'],
      ['[A]', 'Anchor curves of the selection', 'Premiere: track select forward'],
      ['[F8]', 'Problems'],
    ]],
    ['Select', [
      ['Click', 'Select a clip or a moment'],
      ['[Ctrl]+click', 'Add a clip to the selection, or take it out', 'Resolve: the same · Premiere: Shift+click'],
      ['[Shift]+click', 'Add a clip to the selection'],
      ['Drag on an empty part of a lane', 'Select every clip the box touches · with Ctrl or Shift, add them (locked groups stay out)'],
      ['[Ctrl+A]', 'Select every element of the moment at the playhead (locked groups stay out)', 'Premiere, Resolve: everything in the timeline'],
      ['[Esc]', 'Clear the selection'],
    ]],
    ['Edit', [
      ['Drag a clip', 'Move it: what hangs from it follows · with several selected, all of them move by the same time'],
      ['[Ctrl]+drag', 'Move it (or them) alone: what hangs from it and is not selected stays', 'Premiere: insert edit'],
      ['[Alt]+drag', 'Duplicate it (or the selection) where you drop it: the copies land where the drag shows them; the originals stay'],
      ['Drag the right edge', 'Change the duration (fixed clips and waits)'],
      ['[Alt+←] / [Alt+→]', 'Nudge the selection 0.1 s · with Shift, 1 s', 'Premiere: one frame · Resolve: , and .'],
      ['[Del] / [Backspace]', 'Delete the selection; it asks what happens to what hangs from it', 'Premiere: Delete lifts, Shift+Delete ripple-deletes'],
      ['[Ctrl+C] / [Ctrl+V]', 'Copy the selection / paste it at the playhead, in the moment there. The copies are new: not in Unreal yet'],
      ['[Ctrl+D]', 'Duplicate the selection right after itself, each part in its own moment', 'Premiere: applies the default transition'],
      ['[Shift+A]', 'Add at the playhead'],
      ['[M]', 'Bookmark at the playhead'],
      ['[Shift+M]', 'Note for the team'],
      ['[Alt+T]', 'New lane'],
      ['[Ctrl+Z] / [Ctrl+Shift+Z]', 'Undo / redo (also Ctrl+Y)'],
      ['[Ctrl+S]', 'Save'],
    ]],
    ['Ruler, moments and menus', [
      ['Click or drag the ruler', 'Move the playhead'],
      ['Drag a moment chip', 'Move the moment: everything after it follows'],
      ['Drag a bookmark', 'Move it along the ruler'],
      ['Double-click', 'Rename a bookmark or a lane'],
      ['Right-click', 'The menu of a clip, a moment, a bookmark, a note or a lane'],
      ['Click / right-click the Unreal run lane', 'Go to that mark of the score / align each mark or at the Hall start, hide the lane'],
      ['[Esc]', 'Close a menu, the find field or this list · cancel picking an anchor'],
      ['[?]', 'This list'],
    ]],
  ];
  const keyCaps = s => esc(s).replace(/\[([^\]]+)\]/g, '<kbd>$1</kbd>');
  const helpOpen = () => !!document.querySelector('.kbdov');
  function shortcuts() {
    closeOverlay();
    const ov = document.createElement('div'); ov.className = 'overlay ov kbdov';
    ov.innerHTML = `<div class="modal kbdm" role="dialog" aria-label="Keyboard shortcuts"><div class="mh"><span class="t">Keyboard shortcuts</span><span class="kbdsub">and what Premiere or Resolve do where it differs</span><div style="flex:1;"></div><button class="ibtn flat" data-kbdx title="Close · Esc">${ICO('close', 12)}</button></div>
      <div class="mb kbdb" tabindex="-1">${SHORTCUTS.map(([g, rows]) => `<div class="kbdg">${esc(g)}</div>` + rows.map(([k, what, nle]) => `<div class="kbdr"><span class="kk">${keyCaps(k)}</span><span class="kw">${esc(what)}</span><span class="kn">${esc(nle || '')}</span></div>`).join('')).join('')}</div>
      <div class="kbdf">While you type in a field, the keys type. In the 3D view only the playback keys work: edit in the timeline. Esc or ? closes this list.</div></div>`;
    document.body.appendChild(ov);
    const m = ov.querySelector('.kbdm'); if (App.k < 1) m.style.transform = `scale(${App.k})`;
    ov.addEventListener('mousedown', ev => { if (ev.target === ov || ev.target.closest('[data-kbdx]')) { ev.preventDefault(); closeOverlay(); } });
    ov.querySelector('.kbdb').focus();   // ↑/↓, PgUp/PgDn and Space scroll it
  }
  /* Help ▸ Quick start: six steps in plain English (Simple.QUICK_START). It opens by itself once, on the very first launch: the pref flag is set the
     moment it opens, so it never comes back alone. It closes like the list of shortcuts (kbdov: Esc, a click outside, or the button) */
  function quickStart() {
    closeOverlay();
    if (!App.qsSeen) { App.qsSeen = true; savePref(); }
    const ov = document.createElement('div'); ov.className = 'overlay ov kbdov qsov';
    ov.innerHTML = `<div class="modal kbdm qsm" role="dialog" aria-label="Quick start"><div class="mh"><span class="t">Quick start</span><span class="kbdsub">six things to know</span><div style="flex:1;"></div><button class="ibtn flat" data-kbdx title="Close · Esc">${ICO('close', 12)}</button></div>
      <div class="mb kbdb" tabindex="-1">${Simple.QUICK_START.map(([t, w], i) => `<div class="qss"><span class="qsn tnum">${i + 1}</span><div class="qst"><b>${esc(t)}</b><p>${keyCaps(w)}</p></div></div>`).join('')}</div>
      <div class="kbdf"><span>${keyCaps('Help ▸ Quick start opens this again · Window ▸ Show technical details turns on the Unreal details · [?] lists every shortcut')}</span><button class="mbtn pri" data-kbdx>Got it</button></div></div>`;
    document.body.appendChild(ov);
    const m = ov.querySelector('.kbdm'); if (App.k < 1) m.style.transform = `scale(${App.k})`;
    ov.addEventListener('mousedown', ev => { if (ev.target === ov || ev.target.closest('[data-kbdx]')) { ev.preventDefault(); closeOverlay(); } });
    ov.querySelector('.kbdb').focus();
  }
  function noteBox() { App.insTab = 'notes'; if (App.mode === 'v3d') setMode('all'); renderInspector(); setTimeout(() => { const n = $('#noteIn'); if (n) n.focus(); }, 20); }
  function addNote() {
    const n = $('#noteIn'), v = n ? n.value : '';
    if (!v.trim()) return; App.noteNew = '';
    if (!Act.addNote(v)) { App.noteNew = v; renderInspector(); }   // refused: the words stay in the box
  }
  function noteAction(nid, k) {
    if (k === 'cancel') { App.noteEdit = App.noteDraft = null; renderInspector(); return; }
    if (k === 'save') {
      const was = App.noteDraft; App.noteEdit = App.noteDraft = null;
      if (was != null && !Act.editNote(nid, was)) { App.noteEdit = nid; App.noteDraft = was; }
      renderInspector(); return;
    }
    if (busy()) return;
    if (k === 'edit') { App.noteEdit = nid; App.noteDraft = null; renderInspector(); const ta = document.querySelector(`[data-note-edit="${nid}"]`); if (ta) { ta.focus(); ta.setSelectionRange(ta.value.length, ta.value.length); } }
    else if (k === 'resolve' || k === 'reopen') Act.resolveNote(nid, k === 'resolve');
    else if (k === 'del') Act.deleteNote(nid);
  }

  /* ================= pointer: timeline ================= */
  let drag = null;
  const ghostEl = () => { let g = $('#dragGhost'); if (!g) { g = document.createElement('div'); g.id = 'dragGhost'; g.className = 'ghost'; g.innerHTML = '<div class="tt"></div>'; } return g; };
  const snapEl = () => { let s = $('#snapLine'); if (!s) { s = document.createElement('div'); s.id = 'snapLine'; s.className = 'snapline'; } return s; };
  function snapTimes(exclude) {
    const out = [App.ph]; for (const b of App.score.acts.flatMap(a => a.beats)) out.push(App.sched.t[b][0]);
    for (const [id, t] of Object.entries(App.sched.t)) if (!exclude.has(id) && El(id)) { out.push(t[0]); if (t[1] > t[0]) out.push(t[1]); }
    for (const [mid, m] of Object.entries(App.score.markers || {})) if (!exclude.has(mid)) out.push(m.t);
    return out;
  }
  function snap(ns, dur) {
    if (!App.snap) return { ns, at: null };   // S toggles it (audit C10: Alt+drag is duplicate in Premiere and Resolve)
    const tol = 6 / App.pps; let best = null;
    for (const c of drag.snaps) { for (const [edge, v] of [[0, ns], [dur, ns + dur]]) { const d = Math.abs(c - v); if (d < tol && (!best || d < best.d)) best = { d, ns: c - edge, at: c }; } }
    return best ? { ns: best.ns, at: best.at } : { ns, at: null };
  }
  function onTimelineDown(ev) {
    hideHover();   // a press, a drag: the hover card steps aside (it comes back on the next move)
    if (ev.button !== 0) return;
    const t = ev.target;
    if (t.closest('.mkin')) return;   // typing a bookmark's name
    const ls = t.closest('[data-lanes]'); if (ls) { ev.preventDefault(); setLaneSize(ls.dataset.lanes); return; }   // lane height (a view preference)
    // picking an anchor: a clip or a moment chip is the answer; the ruler, the acts and collapsing still work, nothing else edits
    if (App.pick && !(t.closest('#ruler') && !t.closest('[data-mk],[data-nmk]')) && !t.closest('.actb') && !t.closest('.gch')) {
      ev.preventDefault();
      const tg = pickTarget(ev), id = App.pick.id; if (!tg) return;
      if (!El(id) && !App.score.beats[id]) { endPick('It no longer exists (undone or deleted): anchor not changed'); return; }
      const P = App.pick;
      if (P.k ? Act.reanchorAlt(id, P.k, { ref: tg.ref, edge: tg.edge }, P.field) : Act.reanchor(id, { ref: tg.ref, edge: tg.edge })) { endPick(); if (App.sel !== id) select(id); }
      return;
    }
    // a bookmark: click goes to it, drag moves it along the ruler (read-only in the 3D tab)
    const mk = t.closest('[data-mk]'), m = mk && (App.score.markers || {})[mk.dataset.mk];
    if (m) { ev.preventDefault(); drag = { kind: 'marker', id: mk.dataset.mk, x0: ev.clientX, s: m.t, started: false, ro: App.view === '3d', el: mk, snaps: snapTimes(new Set([mk.dataset.mk])) }; return; }
    const nk = t.closest('[data-nmk]'); if (nk) { ev.preventDefault(); openNote(nk.dataset.nmk); return; }
    if (t.closest('#ruler')) { ev.preventDefault(); drag = { kind: 'scrub' }; seek(timeFromClient(ev.clientX)); return; }
    // the Unreal run lane: a bar goes to its mark in the score (aligned at each mark), anywhere else to that time
    if (t.closest('#runrow')) {
      ev.preventDefault(); const sg = t.closest('[data-rs]'), m = sg && App.runAlign !== 'hall' && App.runView ? App.runView.marks[sg.dataset.rs] : null;
      seek(m != null ? m : timeFromClient(ev.clientX)); return;
    }
    const mom = t.closest('.momb');
    if (mom) { ev.preventDefault(); const b = mom.dataset.beat; drag = { kind: 'beat', id: b, x0: ev.clientX, s: App.sched.t[b][0], started: false, el: mom, left0: parseFloat(mom.style.left), snaps: snapTimes(new Set()) }; return; }
    const act = t.closest('.actb'); if (act) { const a = App.sched.acts.find(x => x.id === act.dataset.act); seek(a.s); revealTime(a.s); return; }
    if (t.closest('.gch')) { const g = t.closest('.gch').dataset.col; App.collapsed[g] = !groupCollapsed(g); savePref(); renderTimeline(); return; }
    if (t.closest('[data-lock]')) { const g = t.closest('[data-lock]').dataset.lock; App.locked[g] = !App.locked[g]; savePref(); renderTimeline(); renderInspector(); toast(App.locked[g] ? 'Group locked: nothing in it can be moved or deleted' : 'Group unlocked'); return; }
    if (t.closest('[data-newlane]')) { Act.newLane(t.closest('[data-newlane]').dataset.newlane); return; }
    const c = t.closest('[data-id]');
    if (c && c.closest('.fld')) {
      ev.preventDefault();
      const id = c.dataset.id, e = El(id); if (!e) return;
      const mod = ev.ctrlKey || ev.metaKey;
      if (ev.shiftKey && !mod && !ev.altKey) { addSel(id); return; }   // Shift+click adds it to the selection (C10)
      const [s, en] = App.sched.t[id];
      if (App.locked[e.group]) { if (mod) toggleSel(id); else select(id); toast(`${hueName(e.group)} is locked`); return; }
      if (t.closest('[data-trim]')) {
        if (e.type === 'vo') { toast('A voice lasts as long as its audio. Edit the text or load new audio.'); return; }
        if (e.gate && App.persona !== 'typical') { toast('Switch the simulated user to Typical to change how long this wait is expected to take'); return; }
        drag = { kind: 'trim', id, x0: ev.clientX, s, en, started: false, el: c, snaps: snapTimes(new Set([id])) }; return;
      }
      // a clip of a multiselection drags the whole selection (C10); Alt, pressed now or at the drop, duplicates instead
      const cur = selIds(), ids = cur.length > 1 && cur.includes(id) ? cur : [id], fam = new Set();
      for (const x of ids) { fam.add(x); for (const k of familyOf(x)) fam.add(k); }
      drag = { kind: 'move', id, ids, mod, dup: ev.altKey, minS: Math.min(...ids.map(x => App.sched.t[x][0])), x0: ev.clientX, y0: ev.clientY, s, en, dur: en - s, sT: App.schedT.t[id][0], enT: App.schedT.t[id][1], until: !!e.end, started: false, el: c, lane: e.lane, group: e.group, target: e.lane, newLane: false, bad: false, fam, snaps: snapTimes(fam) };
      return;
    }
    // empty lane space: a click clears the selection; a drag draws a box that selects every clip it touches (C10)
    if (t.closest('.fld')) {
      ev.preventDefault();
      const a = document.activeElement; if (a && a !== document.body && a.matches && a.matches('input,textarea,select')) a.blur();   // a field being typed in commits first
      const r0 = $('#tlc').getBoundingClientRect();
      drag = { kind: 'marquee', lx0: ev.clientX - r0.left, ly0: ev.clientY - r0.top, x0: ev.clientX, y0: ev.clientY, add: ev.ctrlKey || ev.metaKey || ev.shiftKey, base: selIds(), started: false, hit: [], skipped: 0 };
    }
  }
  /* the selection box: what it touches is shown selected while you drag; locked groups stay out (as locked tracks) */
  function marqueeMove(ev) {
    const D = drag, tlc = $('#tlc'), r0 = tlc.getBoundingClientRect();
    if (!D.started) {
      if (Math.abs(ev.clientX - D.x0) < 4 && Math.abs(ev.clientY - D.y0) < 4) return;
      D.started = true; D.nodes = new Map();
      D.rects = [...tlc.querySelectorAll('.fld [data-id]')].map(n => { const b = n.getBoundingClientRect(), id = n.dataset.id; if (!D.nodes.has(id)) D.nodes.set(id, []); D.nodes.get(id).push(n); return { id, l: b.left - r0.left, r: b.right - r0.left, t: b.top - r0.top, b: b.bottom - r0.top }; });
      D.box = document.createElement('div'); D.box.className = 'marquee'; tlc.appendChild(D.box);
    }
    const cx = ev.clientX - r0.left, cy = ev.clientY - r0.top, k = App.k || 1;
    const L = Math.min(D.lx0, cx), R = Math.max(D.lx0, cx), Tp = Math.min(D.ly0, cy), B = Math.max(D.ly0, cy);
    Object.assign(D.box.style, { left: L / k + 'px', top: Tp / k + 'px', width: (R - L) / k + 'px', height: (B - Tp) / k + 'px' });
    const hit = [...new Set(D.rects.filter(q => q.r >= L && q.l <= R && q.b >= Tp && q.t <= B).map(q => q.id))].filter(id => El(id));
    D.hit = hit.filter(id => !App.locked[El(id).group]).sort((a, b) => App.sched.t[a][0] - App.sched.t[b][0]); D.skipped = hit.length - D.hit.length;
    const show = new Set(D.add ? D.base.concat(D.hit) : D.hit);
    tlc.querySelectorAll('.fld .sel, .fld .gsel').forEach(n => n.classList.remove('sel', 'gsel'));
    for (const id of show) for (const n of D.nodes.get(id) || []) n.classList.add('sel');
    setInfo(`${show.size} selected${D.skipped ? ` · ${D.skipped} in locked groups left out` : ''} · release to select`);
  }
  function hueName(gid) { return (App.score.groups.find(g => g.id === gid) || {}).name || gid; }
  function onMove(ev) {
    if (!drag) return;
    if (drag.kind === 'scrub') { seek(timeFromClient(ev.clientX)); return; }
    if (drag.kind === 'resize') { const h = Math.max(160, Math.min(innerHeight / App.k - 220, drag.h0 - (ev.clientY - drag.y0) / App.k)); document.documentElement.style.setProperty('--tlh', h + 'px'); App.tlhUser = true; return; }
    if (drag.kind === 'gutter') { const w = Math.max(220, Math.min(520, drag.side === 'l' ? drag.w0 + (ev.clientX - drag.x0) / App.k : drag.w0 - (ev.clientX - drag.x0) / App.k)); drag.panel.style.width = w + 'px'; return; }
    if (drag.kind === 'marquee') { marqueeMove(ev); return; }
    const dx = (ev.clientX - drag.x0) / App.k;
    if (drag.ro) return;
    if (!drag.started) { if (Math.abs(dx) < 3 && Math.abs(ev.clientY - (drag.y0 || ev.clientY)) < 3) return; drag.started = true; if (drag.el) drag.el.classList.add('dragging'); if (drag.kind === 'move' && drag.ids.length === 1) { const sl = document.querySelector(`.slot[data-slot="${drag.group}"]`); if (sl) sl.style.display = 'flex'; } }
    const sline = snapEl();
    if (drag.kind === 'marker') {
      const r = snap(drag.s + dx / App.pps, 0); drag.ns = clamp(r.ns, 0, App.sched.total);
      drag.el.style.left = X(drag.ns) + 'px'; showSnap(sline, r.at);
      setInfo(`${App.score.markers[drag.id].name} · ${tc(drag.ns)}${App.snap ? '' : ' · snapping off (S)'}`);
      return;
    }
    if (drag.kind === 'beat') {
      const r = snap(drag.s + dx / App.pps, 0); drag.ns = Math.max(0, r.ns);
      drag.el.style.left = (drag.left0 + X(drag.ns - drag.s)) + 'px';
      showSnap(sline, r.at); setInfo(`Moment ${keyOf(drag.id)} · ${(drag.ns - drag.s >= 0 ? '+' : '')}${fmtS(drag.ns - drag.s)} s · everything after it moves too`);
      const db = drag.ns - drag.s; previewRipple(() => { const n = JSON.parse(JSON.stringify(App.score)), x = n.beats[drag.id], order = n.acts.flatMap(a => a.beats), pv = order[order.indexOf(drag.id) - 1]; x.at = x.at || (pv ? { ref: pv, edge: 'end', off: 0 } : { ref: null, edge: 'start', off: 0 }); x.at.off += db; return n; }, `Moment ${keyOf(drag.id)} ${db >= 0 ? '+' : ''}${fmtS(db)} s`);
      return;
    }
    if (drag.kind === 'trim') {
      const r = snap(drag.en + dx / App.pps, 0); const nd = Math.max(.1, r.ns - drag.s); drag.nd = nd;
      const g = ghostEl(), fld = drag.el.parentElement; if (g.parentElement !== fld) fld.appendChild(g);
      g.className = 'ghost'; g.style.left = X(drag.s) + 'px'; g.style.width = X(nd) + 'px'; g.style.height = (fld.offsetHeight - 8) + 'px'; g.firstChild.textContent = `${keyOf(drag.id)} · ${fmtS(nd)} s`;
      showSnap(sline, r.at);
      const e0 = El(drag.id); if (e0 && !e0.gate) previewRipple(() => { const n = JSON.parse(JSON.stringify(App.score)); n.elements[drag.id].dur = { mode: 'fixed', value: nd }; return n; }, `${keyOf(drag.id)} · ${fmtS(nd)} s`);
      return;
    }
    // move (one clip, or the whole selection: C10); with Alt the originals stay and copies land there
    const group = drag.ids.length > 1, dup = !!(drag.dup || ev.altKey); drag.dup = dup;
    let r = snap(drag.s + dx / App.pps, drag.dur); let ns = Math.max(drag.s - drag.minS, r.ns);   // the first of them stops at 0:00
    const under = document.elementFromPoint(ev.clientX, ev.clientY);
    const row = !group && under && under.closest('.row[data-lane], .slot');   // several move in time only: each keeps its lane
    let target = drag.target, newLane = drag.newLane;
    if (row && row.dataset.group === drag.group) { target = row.dataset.lane; newLane = false; }
    else if (row && row.classList.contains('slot') && row.dataset.slot === drag.group) { newLane = true; }
    drag.target = target; drag.newLane = newLane; drag.ns = ns;
    // lanes are checked on the typical timeline; a clip that lasts "until" an event keeps its end (it gets shorter or longer).
    // A copy never refuses a lane: it goes to the nearest free one
    const d0 = ns - drag.s, endT = drag.until ? drag.enT : drag.enT + d0;
    const busy = !group && !dup && !newLane && laneBusy(target, drag.sT + d0, Math.max(endT, drag.sT + d0 + .05), drag.fam);
    drag.bad = !!busy;
    drag.el.classList.toggle('dragging', !dup);
    if (group && !drag.others) drag.others = drag.ids.filter(x => x !== drag.id).flatMap(x => [...document.querySelectorAll(`#tlc .fld [data-id="${x}"]`)]).map(src => {
      const cl = src.cloneNode(true); cl.removeAttribute('data-id'); cl.classList.remove('sel', 'gsel', 'dragging'); cl.classList.add('mghost'); src.after(cl); return { src, cl }; });
    for (const o of drag.others || []) { o.src.classList.toggle('dragging', !dup); o.cl.style.transform = `translateX(${X(d0)}px)`; }
    const fld = newLane ? document.querySelector(`.slot[data-slot="${drag.group}"] .sfl`) : document.querySelector(`[data-fld="${target}"]`);
    const g = ghostEl(); if (fld && g.parentElement !== fld) { fld.style.position = 'relative'; fld.appendChild(g); }
    g.className = 'ghost' + (busy ? ' bad' : '');
    const glen = drag.until ? Math.max(.1, drag.en - ns) : drag.dur;
    g.style.left = X(ns) + 'px'; g.style.width = Math.max(10, X(glen)) + 'px'; g.style.height = Math.max(10, (fld ? fld.offsetHeight : 20) - 8) + 'px';
    const d = ns - drag.s;
    g.firstChild.textContent = busy ? `${keyOf(drag.id)} · occupied by ${keyOf(busy)}` : `${keyOf(drag.id)}${group ? ` + ${drag.ids.length - 1}` : ''} · ${d >= 0 ? '+' : ''}${fmtS(d)} s${dup ? ' · copy' : ''}${drag.until && !dup ? ` · ends with its event (${fmtS(glen)} s)` : ''}${newLane ? ' · new lane' : ''}`;
    showSnap(sline, r.at);
    const alone = (ev.ctrlKey || ev.metaKey) && !dup, n = drag.ids.length, follow = drag.fam.size - n;
    const head = `${group ? n + ' clips' : keyOf(drag.id)} ${d >= 0 ? '+' : ''}${fmtS(d)} s${dup ? ` · duplicate${group ? 's' : ''}: the original${group ? 's stay' : ' stays'}` : alone ? ' · alone' : follow > 0 ? ` · ${follow} anchored follow` : ''}${App.snap ? '' : ' · snapping off (S)'}`;
    setInfo(busy ? `${keyOf(drag.id)} → occupied: drop it on another lane, or on "+ New lane"` : head, busy);
    if (busy) return;
    if (dup) previewRipple(() => { const p = Edits.planPaste(App.score, drag.clip = drag.clip || Edits.clipOf(App.score, drag.ids, ScoreEngine), { dt: d }, ScoreEngine, { addLane }); return p.ok ? p.next : App.score; }, head);
    else if (group) previewRipple(() => Edits.moveMany(App.score, drag.ids, d, { alone, ks: viewKeys() }, ScoreEngine, App.kids), head);
    else previewRipple(() => Edits.move(App.score, drag.id, d, { alone, ks: viewKeys() }, App.kids), head);
  }
  /* while dragging, what the edit would do to the rest of the piece (audit C2): simulated at most every 150 ms */
  let _rp = 0;
  function previewRipple(make, prefix, why) {
    const now = performance.now(); if (now - _rp < 150) return; _rp = now;
    try { const line = Integrity.rippleLine(Integrity.effect(App.score, make(), ScoreEngine)); setInfo(prefix + (line ? ' · ' + line : ''), why); } catch (_) {}
  }
  function showSnap(sline, at) { const tlc = $('#tlc'); if (at == null) { sline.remove(); return; } if (sline.parentElement !== tlc) tlc.appendChild(sline); sline.style.left = (HDR + X(at)) + 'px'; sline.style.height = tlc.scrollHeight + 'px'; }
  function setInfo(txt, why) { const s = document.querySelector('#status .statinfo') || (() => { const x = document.createElement('span'); $('#status').children[0].after(x); return x; })(); s.className = 'statinfo' + (why ? ' why' : ''); s.textContent = txt; }
  function onUp(ev) {
    if (!drag) return;
    const D = drag; drag = null;
    const g = $('#dragGhost'); if (g) g.remove(); const sl = $('#snapLine'); if (sl) sl.remove();
    document.querySelectorAll('.slot').forEach(s => { s.style.display = 'none'; });
    if (D.el) D.el.classList.remove('dragging');
    if (D.kind === 'scrub' || D.kind === 'resize' || D.kind === 'gutter') { if (D.kind !== 'scrub') { drawAnchors(); } return; }
    if (D.kind === 'marquee') {
      if (D.box) D.box.remove();
      if (!D.started) { if (!D.add && (App.sel || App.selRole)) select(null); return; }   // a click on empty space clears the selection
      const ids = D.add ? D.base.concat(D.hit) : D.hit;
      if (!ids.length) { select(null); return; }
      setSelection(ids, D.add && D.base.includes(App.sel) ? App.sel : ids[0]);
      if (D.skipped) toast(`${D.skipped} clip${D.skipped > 1 ? 's' : ''} in locked groups left out`);
      return;
    }
    if (D.kind === 'marker') { if (!D.started) { seek(D.s); return; } Act.moveMarker(D.id, D.ns); renderStatus(); return; }
    if (D.kind === 'beat') { if (!D.started) { select(D.id, 'beat'); seek(D.s); renderLibrary(); return; } Act.moveBeat(D.id, D.ns - D.s); renderTimeline(); return; }
    if (D.kind === 'trim') { if (D.started) Act.trim(D.id, D.nd); return; }
    if (!D.started) { if (D.mod) toggleSel(D.id); else select(D.id); return; }   // Ctrl+click: in or out of the selection
    for (const o of D.others || []) { o.cl.remove(); o.src.classList.remove('dragging'); }
    if (D.dup || ev.altKey) {   // Alt+drag: copies where it was dropped (one clip: on the lane it was dropped on, if free)
      const lane = D.ids.length === 1 && (D.newLane ? 'new' : D.target !== D.lane ? D.target : null);
      if (!Act.duplicate(D.ids, D.ns - D.s, lane ? { [D.id]: lane } : null)) renderTimeline();
      return;
    }
    if (D.ids.length > 1) { if (!Act.moveMany(D.ids, D.ns - D.s, ev.ctrlKey || ev.metaKey)) renderTimeline(); return; }
    if (D.bad) { toast('Occupied: that lane already has something there. Drop it on another lane, or on "+ New lane".'); renderTimeline(); return; }
    Act.move(D.id, D.ns - D.s, D.newLane ? { newIn: D.group } : (D.target !== D.lane ? D.target : null), ev.ctrlKey || ev.metaKey);
    if (App.sel !== D.id) select(D.id);
  }
  function onContext(ev) {
    hideHover();
    const t = ev.target, ro = App.view === '3d';
    if ((t.closest('#runrow') || t.closest('.runhd')) && App.runView) {   // the Unreal run lane: how it aligns, its problems, hide it
      ev.preventDefault();
      openMenu(ev.clientX, ev.clientY, [{ head: Calib.runLabel(App.runView.info) }, ['Align each mark', 'from the score\'s marks', () => setRunAlign('mark'), { on: App.runAlign !== 'hall' }],
        ['Align at Hall start', 'the run as it was', () => setRunAlign('hall'), { on: App.runAlign === 'hall' }], 'sep', ['Problems of the Unreal run', '', () => openRun()],
        ['Hide the lane', 'Window brings it back', () => setRunLane(false)]], 250);
      return;
    }
    const mk = t.closest('[data-mk]'), m = mk && (App.score.markers || {})[mk.dataset.mk];
    if (m) {
      ev.preventDefault(); const mid = mk.dataset.mk;
      openMenu(ev.clientX, ev.clientY, [{ head: m.name }, ['Go to it', tc(m.t), () => { seek(m.t); revealTime(m.t); }], ['Rename', 'double-click', () => renameMarker(mid), { dis: ro }], 'sep', ['Delete', '', () => Act.deleteMarker(mid), { danger: true, dis: ro }]], 190);
      return;
    }
    const nk = t.closest('[data-nmk]'), n = nk && (App.score.notes || {})[nk.dataset.nmk];
    if (n) {
      ev.preventDefault(); const nid = nk.dataset.nmk;
      openMenu(ev.clientX, ev.clientY, [{ head: 'Note · ' + tc(n.t) }, ['Open in Notes', '', () => openNote(nid)], [n.resolved ? 'Reopen' : 'Resolve', '', () => Act.resolveNote(nid, !n.resolved), { dis: ro }], 'sep', ['Delete', '', () => Act.deleteNote(nid), { danger: true, dis: ro }]], 190);
      return;
    }
    // a moment chip: go to it, its anchor, change the anchor (C9)
    const mom = t.closest('.momb');
    if (mom) {
      ev.preventDefault(); const b = mom.dataset.beat, cur = Edits.anchorOf(App.score, b); select(b, 'beat');
      openMenu(ev.clientX, ev.clientY, [{ head: 'Moment ' + App.score.beats[b].key }, ['Go to it', tc(App.sched.t[b][0]), () => goto(b)], cur.ref ? ['Select its anchor', keyOf(cur.ref), () => goto(cur.ref)] : null, 'sep', ...anchorItems(b)].filter(Boolean), 240);
      return;
    }
    const fld = t.closest('.fld'), hdr = t.closest('[data-lanehdr]'), c = t.closest('[data-id]');
    if (!fld && !hdr) return;
    ev.preventDefault();
    const lid = fld ? fld.dataset.fld : hdr.dataset.lanehdr, gid = App.score.lanes[lid].group, gname = hueName(gid);
    if (c) {
      const id = c.dataset.id, e = El(id), cur = selIds();
      if (cur.length > 1 && cur.includes(id)) {   // a clip of a multiselection: the menu of the selection (C10)
        const lk = cur.some(x => App.locked[El(x).group]) || ro;
        openMenu(ev.clientX, ev.clientY, [{ head: cur.length + ' selected' }, ['Copy', 'Ctrl+C', () => Act.copy(cur)], ['Duplicate', 'Ctrl+D', () => Act.duplicate(cur), { dis: lk }], 'sep', [`Delete ${cur.length}`, 'Del', () => Act.remove(cur), { danger: true, dis: lk }]], 220);
        return;
      }
      select(id);
      openMenu(ev.clientX, ev.clientY, [{ head: e.key }, ['Go to its start', '', () => { seek(App.sched.t[id][0]); }], e.at && e.at.ref ? ['Select its anchor', keyOf(e.at.ref), () => goto(e.at.ref)] : null, 'sep', ...anchorItems(id), 'sep', ['Copy', 'Ctrl+C', () => Act.copy([id])], ['Duplicate', 'Ctrl+D', () => Act.duplicate([id]), { dis: App.locked[e.group] || ro }], 'sep', ['Note about it', 'Shift+M', () => noteBox()], 'sep', ['Delete', 'Del', () => Act.remove([id]), { danger: true, dis: App.locked[e.group] }]].filter(Boolean), 240);
      return;
    }
    const items = [];
    if (fld) {
      const tt = timeFromClient(ev.clientX); seek(tt);
      items.push({ head: `Add here · ${gname} · ${tc(tt)}` });
      if (gid === 'vo') items.push(['Alma voice line', 'text + audio later', () => Act.add('vo'), { sw: App.HUE.vo }]);
      if (gid === 'fx' || gid === 'amb') items.push(['Empty sound…', 'name it, load a WAV', () => Act.add('sound'), { sw: App.HUE.fx }]);
      if (gid === 'int') items.push(['Wait', 'the user decides', () => Act.add('wait'), { sw: App.HUE.int }]);
      items.push(['Anything…', 'Shift+A', () => quickAdd({ x: ev.clientX, y: ev.clientY })], ['Paste here', 'Ctrl+V', () => Act.paste(), { dis: !App.clipboard || ro }], ['Bookmark here', 'M', () => Act.bookmark()], ['Note for the team', 'Shift+M', () => noteBox()], 'sep');
    }
    items.push(['Rename lane', 'double-click', () => renameLane(lid)], ['New lane below', 'Alt+T', () => Act.newLane(gid, lid)], ['Delete empty lane', '', () => Act.deleteLane(lid), { danger: true }]);
    openMenu(ev.clientX, ev.clientY, items, 230);
  }
  function renameLane(lid) {
    const nm = document.querySelector(`[data-lanehdr="${lid}"] .nm`); if (!nm) return;
    nm.contentEditable = 'true'; nm.focus(); document.getSelection().selectAllChildren(nm);
    const end = ok => { nm.contentEditable = 'false'; nm.removeEventListener('keydown', kd); if (ok) Act.renameLane(lid, nm.textContent); else renderTimeline(); };
    const kd = e => { if (e.key === 'Enter') { e.preventDefault(); end(true); } if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); end(false); } };
    nm.addEventListener('keydown', kd); nm.addEventListener('blur', () => { if (nm.contentEditable === 'true') end(true); }, { once: true });
  }
  /* rename a bookmark in place, on the ruler: Enter (or clicking away) keeps it, Escape cancels */
  function renameMarker(mid) {
    const m = (App.score.markers || {})[mid], ru = $('#ruler'); if (!m || !ru || busy()) return;
    ru.querySelectorAll('.mkin').forEach(n => n.remove());
    const inp = document.createElement('input'); inp.className = 'mkin'; inp.value = m.name; inp.spellcheck = false; inp.setAttribute('aria-label', 'Bookmark name');
    inp.style.left = (X(m.t) + 6) + 'px'; ru.appendChild(inp); inp.focus(); inp.select();
    let done = false;
    const end = ok => { if (done) return; done = true; const v = inp.value; inp.remove(); if (ok) Act.renameMarker(mid, v); };
    inp.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); end(true); } else if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); end(false); } });
    inp.addEventListener('blur', () => end(true));
  }
  /* a note of the timeline, in the Notes tab (the playhead goes to it) */
  function openNote(nid) {
    const n = (App.score.notes || {})[nid]; if (!n) return;
    App.insTab = 'notes'; App.noteFlash = nid; if (App.mode === 'v3d') setMode('all');
    seek(n.t); renderInspector();
    const row = document.querySelector(`#inspector [data-nid="${nid}"]`); if (row) row.scrollIntoView({ block: 'nearest' });
    setTimeout(() => { if (App.noteFlash === nid) { App.noteFlash = null; const r = document.querySelector(`#inspector [data-nid="${nid}"]`); if (r) r.classList.remove('flash'); } }, 1600);
  }
  function goKnob(name) { App.libTab = 'timing'; App.libQuery = ''; if (App.mode === 'v3d') setMode('all'); select(name, 'knob'); renderLibrary(); const n = document.querySelector(`[data-knob="${name}"]`); if (n) n.scrollIntoView({ block: 'nearest' }); }
  function goto(id) {
    if (App.score.beats[id]) { select(id, 'beat'); seek(App.sched.t[id][0]); revealTime(App.sched.t[id][0]); return; }
    if (!El(id)) return; const e = El(id);
    if (groupCollapsed(e.group)) { App.collapsed[e.group] = false; renderTimeline(); }
    select(id); seek(App.sched.t[id][0]); revealEl(id);
  }
  function zoom(f, cx, at) {
    const sc = $('#sctl'); if (!sc) return; const r = sc.getBoundingClientRect();
    const lx = cx == null ? HDR + (sc.clientWidth - HDR) / 2 : (cx - r.left) / App.k;   // pointer x inside the scroller, in app px
    const t = at != null ? at : (lx + sc.scrollLeft - HDR) / App.pps;                   // the time that stays at lx
    App.pps = Math.max(.4, Math.min(80, App.pps * f)); savePref(); renderTimeline();
    sc.scrollLeft = Math.max(0, t * App.pps + HDR - lx);
  }
  /* = / -: zoom around the playhead. It keeps its place on screen; when it was off screen, it comes to the middle */
  function zoomAt(f) {
    const sc = $('#sctl'); if (!sc || App.mode === 'v3d') return; const r = sc.getBoundingClientRect();
    let lx = HDR + X(App.ph) - sc.scrollLeft; if (lx < HDR || lx > sc.clientWidth) lx = HDR + (sc.clientWidth - HDR) / 2;
    zoom(f, r.left + lx * App.k, App.ph);
  }
  function fit() { const sc = $('#sctl'); if (!sc) return; App.pps = Math.max(.4, (sc.clientWidth - HDR - 40) / App.sched.total); savePref(); renderTimeline(); sc.scrollLeft = 0; }
  /* zoom presets (audit C11): [s, e] fills the view, centred, with a small margin (View.fitRange). Moment and Act are the
     ones at the playhead; double-clicking a moment chip zooms to that moment; Piece is fit() */
  function zoomTo(s, e) {
    const sc = $('#sctl'); if (!sc || App.mode === 'v3d') return;
    const r = View.fitRange(s, e, sc.clientWidth - HDR, { min: .4, max: 80 }); if (!r) return;
    App.pps = r.pps; savePref(); renderTimeline(); sc.scrollLeft = Math.max(0, r.left * App.pps);
  }
  function zoomMoment(b) { b = b || beatAt(App.ph); const T = App.sched.t[b]; if (T) zoomTo(T[0], T[1]); }
  function zoomAct() { const b = beatAt(App.ph), i = App.score.acts.findIndex(a => a.beats.includes(b)), A = App.sched.acts[i]; if (A) zoomTo(A.s, A.e); }
  function setLaneSize(s) { if (s === App.laneSize || !LANE_H[s]) return; App.laneSize = s; savePref(); renderTimeline(); }

  /* ================= wiring (once) ================= */
  function init() {
    if (booted) return; booted = true;
    const sctl = $('#sctl');
    sctl.addEventListener('mousedown', onTimelineDown);
    sctl.addEventListener('contextmenu', onContext);
    sctl.addEventListener('dblclick', ev => {
      const nm = ev.target.closest('[data-lanehdr] .nm'); if (nm) { renameLane(nm.closest('[data-lanehdr]').dataset.lanehdr); return; }
      const mk = ev.target.closest('[data-mk]'); if (mk) { renameMarker(mk.dataset.mk); return; }
      const mom = ev.target.closest('.momb'); if (mom && !App.pick) { zoomMoment(mom.dataset.beat); return; }   // C11: zoom to fit that moment
      if (ev.target.closest('.fld') && !ev.target.closest('[data-id]')) seek(timeFromClient(ev.clientX));
    });
    sctl.addEventListener('wheel', ev => { hideHover(); if (!(ev.ctrlKey || ev.metaKey)) return; ev.preventDefault(); zoom(ev.deltaY < 0 ? 1.18 : 1 / 1.18, ev.clientX); }, { passive: false });
    sctl.addEventListener('scroll', () => { hideHover(); document.querySelectorAll('.menu.ov').forEach(n => n.remove()); });
    document.addEventListener('mousemove', onMove);
    sctl.addEventListener('mousemove', pickHover);
    sctl.addEventListener('mousemove', hoverMove);
    sctl.addEventListener('mouseleave', hideHover);
    document.addEventListener('mouseup', onUp);
    document.addEventListener('mousedown', ev => { if (!ev.target.closest('.ov') && !ev.target.closest('[data-menu]') && !ev.target.closest('[data-persdd]') && !ev.target.closest('[data-branchdd]')) document.querySelectorAll('.menu.ov,.qa.ov').forEach(n => n.remove()); }, true);
    $('#tlResize').addEventListener('mousedown', ev => { ev.preventDefault(); drag = { kind: 'resize', y0: ev.clientY, h0: $('#timeline').offsetHeight - (App.drawer ? 200 : 0) }; });
    document.addEventListener('mousedown', ev => {
      const gt = ev.target.closest('.gutter'); if (!gt) return; ev.preventDefault();
      const prev = gt.previousElementSibling, next = gt.nextElementSibling;
      if (prev && prev.id === 'library') drag = { kind: 'gutter', side: 'l', panel: prev, x0: ev.clientX, w0: prev.offsetWidth };
      else if (next && next.id === 'inspector') drag = { kind: 'gutter', side: 'r', panel: next, x0: ev.clientX, w0: next.offsetWidth };
    });
    // top bar
    $('#top').addEventListener('click', ev => {
      const m = ev.target.closest('[data-menu]');
      if (m) { const was = m.classList.contains('on'); closeOverlay(); if (was) return; m.classList.add('on'); const r = m.getBoundingClientRect(); openMenu(r.left, r.bottom + 2, menuItems(m.dataset.menu), 240); return; }
      const w = ev.target.closest('[data-win]'); if (w) { setMode(w.dataset.win); return; }
      if (ev.target.closest('[data-send]')) { Act.sendToUnreal(); return; }
      const lg = ev.target.closest('[data-lib-go]'); if (lg) { App.libTab = lg.dataset.libGo; if (App.mode === 'v3d') setMode('all'); renderLibrary(); return; }
      if (ev.target.closest('[data-who]')) { App.who = App.who === 'B' ? 'S' : 'B'; savePref(); renderTop(); toast(`Editing as ${WHO[App.who].n}`); }
    });
    // transport + status + drawer share data-tr
    const tr = ev => {
      const b = ev.target.closest('[data-tr]'); if (b) {
        const k = b.dataset.tr;
        if (k === 'start') seek(0); else if (k === 'end') seek(App.sched.total); else if (k === 'play') play(!App.playing);
        else if (k === 'follow') { App.follow = !App.follow; savePref(); renderTransport(); }
        else if (k === 'mark') Act.bookmark(); else if (k === 'anchors') { App.showAnchors = !App.showAnchors; renderTimelineSelection(); renderTransport(); }
        else if (k === 'problems') toggleDrawer(); else if (k === 'snap') toggleSnap(); else if (k === 'fit') fit(); else if (k === 'zin') zoom(1.4); else if (k === 'zout') zoom(1 / 1.4);
        else if (k === 'zmom') zoomMoment(); else if (k === 'zact') zoomAct(); else if (k === 'run') openRun(); else if (k === 'review') openReview();
        return;
      }
      const tg = ev.target.closest('[data-trgrp]'); if (tg) { App.traceOpen = !App.traceOpen; savePref(); renderDrawer(); return; }
      const rs = ev.target.closest('[data-runspan]'); if (rs) { const [a, b] = rs.dataset.runspan.split('|'); showRunSpan(a, b); return; }
      const pd = ev.target.closest('[data-persdd]');
      if (pd) { const r = pd.getBoundingClientRect(); openMenu(r.left, r.bottom + 2, Object.entries(ScoreEngine.PERSONAS).map(([k, P]) => [P.name, P.note, () => setPersona(k), { on: App.persona === k }]), 240); }
      const bd = ev.target.closest('[data-branchdd]'); if (bd) openBranchMenu(bd);
      const pf = ev.target.closest('[data-pf]'); if (pf) { App.pbFilter = pf.dataset.pf; renderDrawer(); }
      const go = ev.target.closest('[data-goto]'); if (go) goto(go.dataset.goto);
      const kg = ev.target.closest('[data-knobgo]'); if (kg) goKnob(kg.dataset.knobgo);
      const ro = ev.target.closest('[data-reopen]'); if (ro) Act.reopen(ro.dataset.reopen);
      const fx = ev.target.closest('[data-pfix]'); if (fx) { const k = fx.dataset.pfix, id = fx.dataset.id;
        if (k === 'drift') Act.matchTimeout(id); else if (k === 'help') Act.addHelp(id); else if (k === 'loop') Act.breakLoop(id); else if (k === 'detach') Act.fixLostAnchor(id); else if (k === 'knob') Act.syncKnob(id, null); else if (k === 'voices') Act.useRealLengths(); else if (k === 'schema') Act.upgradeSchema(); else if (k === 'knobanchor') Act.matchKnobAnchor(id); else if (k === 'clean') Act.cleanAccepted();
        else if (k === 'branch') { select(id); pickAnchor(id, { k: fx.dataset.k, field: fx.dataset.field }); } }
    };
    $('#transport').addEventListener('click', tr); $('#status').addEventListener('click', tr); $('#drawer').addEventListener('click', tr);
    // library
    const lib = $('#library');
    lib.addEventListener('click', ev => {
      const t = ev.target;
      const tab = t.closest('[data-lib]'); if (tab) { App.libTab = tab.dataset.lib; App.libQuery = ''; renderLibrary(); return; }
      if (t.closest('[data-quick]')) { quickAdd(); return; }
      const ad = t.closest('[data-add]'); if (ad) { const k = ad.dataset.add; if (k === 'mark') Act.bookmark(); else if (k === 'note') noteBox(); else Act.add(k); return; }
      const ar = t.closest('[data-actrow]'); if (ar) { const id = ar.dataset.actrow; App.openActs.has(id) ? App.openActs.delete(id) : App.openActs.add(id); renderLibrary(); return; }
      const br = t.closest('[data-beatrow]'); if (br) { goto(br.dataset.beatrow); renderLibrary(); return; }
      const ro = t.closest('[data-role]'); if (ro) { selectRole(ro.dataset.role); return; }
      const kn = t.closest('[data-knob]'); if (kn) { select(kn.dataset.knob, 'knob'); renderLibrary(); return; }
      if (t.closest('[data-psync]')) { Act.syncAll(); return; }
      if (t.closest('[data-send]')) { Act.sendToUnreal(); return; }
      if (t.closest('[data-undo-unreal]')) { Act.stageUndoInUnreal(); return; }
      const sn = t.closest('[data-snd]'); if (sn) { goto(sn.dataset.snd); renderLibrary(); return; }
    });
    lib.addEventListener('input', ev => { if (ev.target.id === 'libq') { App.libQuery = ev.target.value; const pos = ev.target.selectionStart; renderLibrary(); const n = $('#libq'); n.focus(); n.setSelectionRange(pos, pos); } });
    // viewer
    $('#vptool').addEventListener('click', ev => { if (ev.target.closest('[data-pop]')) openSecondTab(); else if (ev.target.closest('[data-sound]')) setSound(!App.sound); });
    // inspector
    const ins = $('#inspector');
    ins.addEventListener('click', ev => {
      const t = ev.target;
      const it = t.closest('[data-itab]'); if (it) { App.insTab = it.dataset.itab; renderInspector(); return; }
      const dt = t.closest('[data-details]'); if (dt) { App.insDetails = !App.insDetails; savePref(); renderInspector(); return; }
      const sh = t.closest('[data-sec]'); if (sh) { App.secClosed = App.secClosed || {}; App.secClosed[sh.dataset.sec] = !App.secClosed[sh.dataset.sec]; renderInspector(); return; }
      const am = t.closest('[data-ancmenu]'); if (am) { const id = am.dataset.ancmenu, r = am.getBoundingClientRect(); openMenu(r.left, r.bottom + 2, [{ head: 'Anchor · ' + anchorText(Edits.anchorOf(App.score, id)) }, ...anchorItems(id)], 250); return; }
      const aa = t.closest('[data-altmenu]'); if (aa) { const [aid, ak, af] = aa.dataset.altmenu.split('|'), r = aa.getBoundingClientRect(); openMenu(r.left, r.bottom + 2, altItems(aid, ak, af), 250); return; }
      const ap = t.closest('[data-altpick]'); if (ap) { const [aid, ak, af] = ap.dataset.altpick.split('|'); pickAnchor(aid, { k: ak, field: af }); return; }
      const go = t.closest('[data-goto]'); if (go) { goto(go.dataset.goto); return; }
      const kg = t.closest('[data-knobgo]'); if (kg) { goKnob(kg.dataset.knobgo); return; }
      const ps = t.closest('[data-pers]'); if (ps) { setPersona(ps.dataset.pers); return; }
      const sk = t.closest('[data-seek]'); if (sk) { seek(+sk.dataset.seek); revealTime(+sk.dataset.seek); return; }
      const li = t.closest('[data-listen]'); if (li) { listen(li.dataset.listen); return; }
      if (t.closest('[data-send]')) { Act.sendToUnreal(); return; }
      const no = t.closest('[data-note]'); if (no) { noteAction(no.closest('[data-nid]').dataset.nid, no.dataset.note); return; }
      const a = t.closest('[data-act]'); if (!a) return;
      const k = a.dataset.act;
      if (k === 'del') Act.remove(selIds());
      else if (k === 'mcopy') Act.copy();
      else if (k === 'mdup') Act.duplicate();
      else if (k === 'wav') { App.wavTarget = App.sel; $('#wavIn').click(); }
      else if (k === 'play') { const u = BLOBS[App.sel]; if (u) new Audio(u).play().catch(() => {}); else toast('The file is in obra/audio/inbox; reload it here to listen.'); }
      else if (k === 'psync1') Act.syncKnob(App.sel, null);
      else if (k === 'vreal') Act.useRealLengths([App.sel]);
      else if (a.hasAttribute('data-send')) Act.sendToUnreal();
      else if (k === 'punprop') Act.unpropose(App.sel);
      else if (k === 'pprop') { const st = $('#pStage'); Act.propose(App.sel, st && st.value !== '' ? +st.value : null, parseFloat($('#pVal').value.trim().replace(',', '.')), $('#pWhy').value); }
      else if (k === 'addnote') addNote();
    });
    ins.addEventListener('input', ev => { if (ev.target.id === 'noteIn') App.noteNew = ev.target.value; else if (ev.target.dataset.noteEdit) App.noteDraft = ev.target.value; });
    ins.addEventListener('change', ev => {
      // number fields are text fields (always shown with a dot, whatever the computer's language): a comma is read as a dot
      const f = ev.target.dataset.f; if (!f) return; const v = ev.target.classList.contains('ni') ? ev.target.value.trim().replace(',', '.') : ev.target.value, id = App.sel;
      if (['off', 'dur', 'exp', 'fw', 'beatoff', 'mnudge', 'altoff'].includes(f) && !Number.isFinite(parseFloat(v))) { renderInspector(); return toast('Type a number'); }
      if (f === 'mnudge') { if (!Act.moveMany(selIds(), parseFloat(v), false)) renderInspector(); }   // done or refused: it shows 0 again
      else if (f === 'off') Act.setOffset(id, parseFloat(v));
      else if (f === 'altoff') Act.setOffset(id, parseFloat(v), ev.target.dataset.k);
      else if (f === 'branch') Act.setBranch([id], ev.target.dataset.on, v === '' ? null : v);
      else if (f === 'dur') Act.trim(id, parseFloat(v));
      else if (f === 'exp') Act.setGate(id, 'expected', parseFloat(v));
      else if (f === 'fw') Act.setGate(id, 'fw', parseFloat(v));
      else if (f === 'blocking') Act.setBlocking(id, ev.target.checked);
      else if (f === 'lane') Act.setLane(id, v);
      else if (f === 'text') Act.setText(id, v);
      else if (f === 'name') Act.rename(id, cleanId(v));
      else if (f === 'beatoff') { const B = App.score.beats[id], order = App.score.acts.flatMap(a => a.beats), prev = order[order.indexOf(id) - 1]; const cur = B.at ? B.at.off || 0 : 0; if (!Act.moveBeat(id, parseFloat(v) - cur)) renderInspector(); }   // refused (or no change): the field shows the offset it has
    });
    ins.addEventListener('keydown', ev => {
      if (ev.key === 'Enter' && ev.target.matches('input.ni,input.nmin')) ev.target.blur();
      if (ev.key === 'Enter' && (ev.ctrlKey || ev.metaKey) && ev.target.id === 'noteIn') { ev.preventDefault(); addNote(); }
      const ne = ev.target.dataset.noteEdit;
      if (ne && ev.key === 'Enter' && (ev.ctrlKey || ev.metaKey)) { ev.preventDefault(); noteAction(ne, 'save'); }
      if (ne && ev.key === 'Escape') { ev.preventDefault(); ev.stopPropagation(); noteAction(ne, 'cancel'); }
    });
    ins.addEventListener('dragover', ev => { const d = ev.target.closest('[data-drop]'); if (d) { ev.preventDefault(); d.classList.add('hot'); } });
    ins.addEventListener('dragleave', ev => { const d = ev.target.closest('[data-drop]'); if (d) d.classList.remove('hot'); });
    ins.addEventListener('drop', ev => { const d = ev.target.closest('[data-drop]'); if (!d) return; ev.preventDefault(); const f = ev.dataTransfer.files && ev.dataTransfer.files[0]; if (f) loadWav(App.sel, f); });
    $('#wavIn').addEventListener('change', ev => { const f = ev.target.files && ev.target.files[0]; if (f && App.wavTarget) loadWav(App.wavTarget, f); ev.target.value = ''; });
    $('#jsonIn').addEventListener('change', ev => { const f = ev.target.files && ev.target.files[0]; if (f) importScore(f); ev.target.value = ''; });
    let rz = 0; addEventListener('resize', () => { clearTimeout(rz); rz = setTimeout(drawAnchors, 120); });
  }

  /* ================= "Changes in guion.js" (lote 5, design B §7.3) =================
     The rows of ImportDiff.diff(score, a fresh extraction of guion.js), each with the verbs it offers as checkboxes (the ones that are
     safe are checked: new clips, new words, a new name; a time never is) and a Dismiss (hide it until guion.js changes that element
     again). "Take" applies everything checked as ONE edit (Act.guionTake: one card at most, Ctrl+Z undoes it). Like a card it holds the
     editor still while it is open (App.cardOpen); an action closes it, edits, and opens it again on what is left. A schema 2 score gets
     the report without checkboxes: its names are not stable yet. */
  const GSEC = [['New in guion.js', ['moment-added', 'added']], ['Renamed', ['renamed']], ['Changed', ['changed', 'moment-changed']], ['No longer in guion.js', ['removed', 'moment-removed']]];
  /* schema 2 has no record of what the score took from guion.js, so the score is its own base and an edit of yours looks like a change: the report says "differences", never "changes" */
  const GSEC2 = [['In guion.js, not in the score', ['moment-added', 'added']], ['Named differently', ['renamed']], ['Different', ['changed', 'moment-changed']], ['In the score, not in guion.js', ['removed', 'moment-removed']]];
  function guionHTML(o) {
    const G = App.guion || {}, W = ImportDiff.wordsOf, FN = ImportDiff.fieldName;
    const head = sub => `<h3>${App.score.schema >= 3 ? 'Changes in guion.js' : 'Differences from guion.js'}<span>${esc(sub || '')}</span></h3>`;
    if (o.reading) return head('reading…') + `<div class="gmsg">Reading guion.js. The editor's server extracts it to obra/score/score.extracted.json; nothing in the score changes.</div><div class="btns"><button data-gact="close">Cancel</button></div>`;
    if (G.error) return head('') + `<div class="gmsg bad">Could not read guion.js: ${esc(G.error)}</div><div class="btns"><button data-gact="close">Close</button><button class="pri" data-gact="rescan">Try again</button></div>`;
    const P = Act.guionPlan(), d = P.d, st = d.stable, rows = d.rows, many = (n, a, b) => `${n} ${n === 1 ? a : b || a + 's'}`;
    const chosen = rows.reduce((n, r) => n + (P.sel[r.rid] || []).length, 0), names = P.names.length;
    const ck = (r, verb, text, why) => st ? `<label class="gck"${why ? ` title="${esc(why)}"` : ''}><input type="checkbox" data-gk="${esc(r.rid)}|${verb}"${(P.sel[r.rid] || []).includes(verb) ? ' checked' : ''}><span>${esc(text)}</span></label>` : '';
    const line = f => `<div class="gl"><span class="gn">${esc(FN(f.field))}</span><span class="gw">${esc(W(f.field, f.was))}</span><span class="ga">→</span><span class="gv">${esc(W(f.field, f.now))}</span></div>`;
    const where = r => (r.moment ? ` <span class="dim">in ${esc(r.moment)}</span>` : '');
    const dismiss = r => st ? `<button class="gbtn" data-gact="dismiss" data-rid="${esc(r.rid)}" title="${r.kind === 'added' || r.kind === 'moment-added' ? 'Not wanted: the score stays without it and it is not offered again' : 'Hide this until guion.js changes it again'}">Dismiss</button>` : '';
    const edited = r => (r.edited ? ` <span class="chip prov" title="The score has changed this element since it took guion.js: the values on the left may be your own edit, so nothing is checked for you">edited here too</span>` : '');
    function rowHTML(r) {
      let top = '', det = '', btn = dismiss(r);
      if (r.kind === 'added') {
        top = `${ck(r, 'add', 'Add')} <b>${esc(r.key)}</b> <span class="dim">${esc(r.type)}</span>${where(r)}`;
        det = `<div class="gl"><span class="gn">Starts</span><span class="gv">${esc(W('at', r.rec.at))}</span></div>` + (r.rec.text ? `<div class="gl"><span class="gn">Text</span><span class="gv">${esc(W('text', r.rec.text))}</span></div>` : '') + (r.rec.note ? `<div class="gl"><span class="gn">Note</span><span class="gv">${esc(W('note', r.rec.note))}</span></div>` : '');
      } else if (r.kind === 'moment-added') {
        top = `${ck(r, 'add-moment', 'Add the moment')} <b>${esc(r.key)}</b> ${r.title ? '<span class="dim">' + esc(W('title', r.title)) + '</span>' : ''}`;
        det = `<div class="gl"><span class="gn">Clips</span><span class="gv">${r.elements.length ? esc(r.elements.slice(0, 8).map(u => ImportDiff.nameOf(u).replace(/ \(.*\)$/, '')).join(', ') + (r.elements.length > 8 ? `, … (${r.elements.length - 8} more)` : '')) : 'none'}</span></div><div class="gl"><span class="gn">Goes</span><span class="gv">after the moment before it in its act, hanging from ${esc(W('at', r.rec.at))}</span></div>`;
      } else if (r.kind === 'renamed') {
        top = `${ck(r, 'rename', 'Take the new name', 'Its key and label change; what Unreal plays does not')} <b>${esc(r.wasKey)}</b> <span class="ga">→</span> <b>${esc(r.key)}</b>${where(r)}${edited(r)}`;
      } else if (r.kind === 'changed' || r.kind === 'moment-changed') {
        top = `<b>${esc(r.kind === 'moment-changed' ? 'Moment ' + r.key : r.key)}</b>${r.kind === 'changed' ? where(r) : ''}${edited(r)}`;
        for (const g of ['text', 'timing', 'structure']) {
          if (!r.groups[g]) continue;
          const t = g === 'text' ? "Take guion's text" : g === 'timing' ? "Take guion's timing" : '';
          det += `<div class="gg">${g === 'structure' ? '<span class="gtag">Shown only</span>' : ck(r, g, t, g === 'timing' ? 'The timing is DA_Partitura_Obra’s: the score keeps its own unless you take this' : '')}${r.groups[g].map(line).join('')}`
            + (g === 'timing' ? `<div class="gnote">DA_Partitura_Obra rules the timing; the score keeps its own unless you take this.</div>` : '')
            + (g === 'text' && r.estimate ? `<div class="gnote">Its length would be about ${esc(String(Math.round(r.estimate.now * 100) / 100))} s, an estimate from the words: the recording decides, so the length is not taken.</div>` : '')
            + (g === 'structure' ? `<div class="gnote">Change it in the timeline if you want it here too.</div>` : '') + '</div>';
        }
      } else if (r.kind === 'removed') {
        top = `<b>${esc(r.key)}</b>${where(r)}<span class="dim"> is not in guion.js any more</span>${edited(r)}`;
        det = '<div class="gnote">It stays in the score until you delete it.</div>';
        btn = `<button class="gbtn" data-gact="keep" data-rid="${esc(r.rid)}" title="Leave it in the score and stop listing it">Keep</button><button class="gbtn danger" data-gact="delete" data-rid="${esc(r.rid)}" title="Delete it here (the usual delete: it asks what hangs from it)">Delete here…</button>`;
        if (!st) btn = '';
      } else if (r.kind === 'moment-removed') {
        top = `<b>Moment ${esc(r.key)}</b>${r.title ? ' <span class="dim">' + esc(W('title', r.title)) + '</span>' : ''}<span class="dim"> is not in guion.js any more</span>`;
        det = `<div class="gnote">A moment is never deleted: it stays${r.elements.length ? ', with its ' + many(r.elements.length, 'clip') : ''}.</div>`;
        btn = st ? `<button class="gbtn" data-gact="keep" data-rid="${esc(r.rid)}" title="Leave it in the score and stop listing it">Keep</button>` : '';
      }
      return `<div class="grow" data-rid="${esc(r.rid)}"><div class="gtop"><div class="gmain">${top}</div><div class="gbtns">${btn}</div></div>${det}</div>`;
    }
    let h = head(rows.length ? many(rows.length, st ? 'change' : 'difference') : '');
    h += `<div class="gintro">${G.at ? 'Read at ' + esc(G.at.slice(11, 19)) + '. ' : ''}${st ? "The score keeps its own times and texts unless you take guion's. Everything checked is taken as one edit: Ctrl+Z undoes it, Ctrl+S saves it." : ''}</div>`;
    if (!st) h += `<div class="gwarn">This score is schema 2: its names are the extraction's, so nothing here can be matched to its ids with certainty. This is a report only: it compares the score with guion.js as it is, and a schema 2 score does not remember what it took from guion.js, so some differences may be your own edits. Upgrade the score to schema 3 first (Problems ▸ Upgrade…) and then each change can be taken.</div>`;
    if (!rows.length) h += `<div class="gmsg">No changes since the score took it.${d.hidden ? ` ${many(d.hidden, 'change is', 'changes are')} hidden (dismissed or kept) until guion.js changes ${d.hidden === 1 ? 'it' : 'them'} again.` : ''}</div>`;
    for (const [title, kinds] of st ? GSEC : GSEC2) {
      const list = rows.filter(r => kinds.includes(r.kind)); if (!list.length) continue;
      h += `<div class="gsec">${esc(title)}<span>${list.length}</span></div>` + list.map(rowHTML).join('');
    }
    if (names) h += `<div class="gnames">${many(names, 'name')} follow${names === 1 ? 's' : ''} guion.js (a renumbered moment, a #2 that moved): the ids stay${Object.keys(d.beatRen).length ? '. Renumbered: ' + esc(Object.entries(d.beatRen).map(([a, b]) => a + ' → ' + b).join(', ')) : ''}. ${st ? `They are written with whatever you take${rows.length ? '' : ', or on their own'}.` : 'After the upgrade they follow on their own.'}</div>`;
    const flags = (P.plan && P.plan.flagged) || [];
    if (flags.length) h += `<div class="gflags"><b>To check after taking this</b>${flags.slice(0, 6).map(f => `<div>${esc(f.key)}: ${esc(f.msg)}</div>`).join('')}${flags.length > 6 ? `<div>… and ${flags.length - 6} more</div>` : ''}</div>`;
    if (rows.length && d.hidden) h += `<div class="gnames">${many(d.hidden, 'change is', 'changes are')} hidden (dismissed or kept) until guion.js changes ${d.hidden === 1 ? 'it' : 'them'} again.</div>`;
    const lab = chosen ? `Take ${chosen} chosen` : names && st ? 'Update names' : 'Take chosen';
    h += `<div class="btns"><button data-gact="close">Close</button><button data-gact="rescan" title="Read guion.js again">Read again</button>${st ? `<button class="pri" data-gact="${chosen ? 'apply' : 'names'}"${chosen || names ? '' : ' disabled'}>${lab}</button>` : ''}</div>`;
    return h;
  }
  function guionPanel(o) {
    o = o || {};
    const old = document.querySelector('.imp.gdiff'), top = old ? old.scrollTop : 0;
    if (old) document.querySelectorAll('.gdiff,.gdback').forEach(n => n.remove()); else closeOverlay();
    const back = document.createElement('div'); back.className = 'impback ov gdback';
    const d = document.createElement('div'); d.className = 'imp ov gdiff';
    d.innerHTML = guionHTML(o);
    document.body.appendChild(back); document.body.appendChild(d);
    if (App.k < 1) d.style.transform = `translate(-50%,-50%) scale(${App.k})`;
    d.scrollTop = top; App.cardOpen = true;
    const shut = () => { App.cardOpen = false; back.remove(); d.remove(); };
    d._cancel = shut;
    back.addEventListener('click', shut);
    d.addEventListener('click', ev => {
      const b = ev.target.closest('[data-gact]'); if (!b || b.disabled) return;
      const a = b.dataset.gact, rid = b.dataset.rid;
      if (a === 'close') shut();
      else if (a === 'rescan') { shut(); Act.guionCheck(); }
      else if (a === 'apply') Act.guionApply();
      else if (a === 'names') { shut(); Act.guionNames(); }
      else if (a === 'dismiss' || a === 'keep') { shut(); Act.guionRow(rid, a); }
      else if (a === 'delete') Act.guionDelete(rid);
    });
    d.addEventListener('change', ev => {
      const c = ev.target.closest('[data-gk]'); if (!c || !App.guion) return;
      const k = c.dataset.gk, i = k.lastIndexOf('|'), rid = k.slice(0, i), verb = k.slice(i + 1), cur = (App.guion.pick[rid] || []).filter(x => x !== verb);
      App.guion.pick[rid] = c.checked ? cur.concat(verb) : cur;
      guionPanel();
    });
    setTimeout(() => { const f = d.querySelector('.btns .pri:not([disabled])') || d.querySelector('[data-gact=close]'); if (f) f.focus(); }, 30);
  }

  function renderAll() { init(); renderTop(); renderLibrary(); renderViewerBar(); renderTransport(); renderTimeline(); renderDrawer(); renderInspector(); renderStatus(); }
  window.UI = { chooseCard, sendCard, renderAll, renderTop, renderLibrary, renderViewerBar, renderTransport, renderTimeline, renderTimelineSelection, renderDrawer, renderInspector, renderStatus, movePlayhead, impactCard, quickAdd, noteBox, closeOverlay, goto, pickAnchor, endPick, guionPanel,
    renderRange, revealTime, zoomAt, fit, shortcuts, quickStart, helpOpen, openFind, closeFind, fitTransport, setLaneSize, zoomMoment, zoomAct, hideHover };
})();
