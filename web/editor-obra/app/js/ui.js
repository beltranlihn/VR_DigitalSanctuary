/* Soul Charger editor · UI: everything that is drawn, and the pointer. State and edits live in app.js (App, Act, commit);
   this file never changes the score by itself, it always calls Act. Markup follows the ISP/VEATION classes (css/isp.css). */
(function () {
  'use strict';
  const HDR = 168;                                   // lane header width (ISP .trackhdr)
  const LANE_H = { vo: 36, fx: 22, amb: 22, hap: 22 }, LANE_DEF = 26;
  const laneH = g => LANE_H[g] || LANE_DEF;
  const X = t => t * App.pps;
  const ICON = { wait: 'hourglass', vo: 'wave', sound: 'sound', ambience: 'sound', haptic: 'haptic', path: 'walk', world: 'world', object: 'obj', instruction: 'ghost', interaction: 'logic' };
  const KIND = { wait: 'Wait', vo: 'Voice', sound: 'Sound', ambience: 'Ambience', haptic: 'Haptic', path: 'Path', world: 'World', object: 'Object', instruction: 'Instruction', interaction: 'Interaction' };
  const WHO = { B: { n: 'Beltrán', c: '#8468BE' }, S: { n: 'Partner', c: '#4E78B3' } };
  const KINDTXT = { literal: 'Hardwired in Unreal', wired: 'Wired in Unreal', knob: 'Knob in Unreal', 'not-blocking': 'Different in Unreal', 'not-in-unreal': 'Not in Unreal yet' };
  const fmtMS = t => { t = Math.max(0, t); const m = Math.floor(t / 60), s = Math.floor(t - m * 60); return m + ':' + String(s).padStart(2, '0'); };
  const persona = () => ScoreEngine.PERSONAS[App.persona];
  const El = id => App.score.elements[id];
  let laneTop = {}, groupTop = {}, booted = false;

  /* colour of the text on a group colour (ISP textOn) */
  const _lum = h => { const c = [1, 3, 5].map(i => { const v = parseInt(h.slice(i, i + 2), 16) / 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }); return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]; };
  const textOn = h => { const L = _lum(h), LD = _lum('#0E0F11'), LL = _lum('#F2F4F8'); return (Math.max(L, LD) + .05) / (Math.min(L, LD) + .05) >= (Math.max(L, LL) + .05) / (Math.min(L, LL) + .05) ? '#0E0F11' : '#F2F4F8'; };
  const hueOf = gid => (App.score.groups.find(g => g.id === gid) || {}).hue || App.HUE[gid] || '#777777';
  const isInstant = e => !e.gate && !e.end && (!e.dur || e.dur.mode === 'instant' || !(e.dur.value > 0));
  function roleFor(e) {
    for (const [name, r] of Object.entries(App.roles.roles)) { const m = r.match || {}; if ((m.group && m.group === e.group) || (m.key && new RegExp(m.key).test(e.key))) return name; }
    return null;
  }
  function pbMap() { const m = {}; for (const p of App.problems) if (p.el && p.st === 'open' && (p.sv === 'block' || p.sv === 'warn')) { if (m[p.el] !== 'block') m[p.el] = p.sv; } return m; }
  function pbCounts() { const o = App.problems.filter(p => p.st === 'open'); return { b: o.filter(p => p.sv === 'block').length, w: o.filter(p => p.sv === 'warn').length, i: o.filter(p => p.sv === 'info').length, a: App.problems.filter(p => p.st === 'accepted').length }; }
  const keyOf = id => (App.score.beats[id] || El(id) || {}).key || id || '—';
  function timeFromClient(cx) { const sc = $('#sctl'), r = sc.getBoundingClientRect(); return Math.max(0, ((cx - r.left) / App.k + sc.scrollLeft - HDR) / App.pps); }

  /* ================= top bar + menus ================= */
  function renderTop() {
    const P = persona();
    $('#top').innerHTML = `<span class="dot"></span><div class="menubar">${['File', 'Edit', 'Experience', 'Window'].map(m => `<button class="menubtn" data-menu="${m}">${m}</button>`).join('')}</div><div style="flex:1;"></div>
      <div class="well" title="Window layout">${[['all', 'All-in-one'], ['v3d', '3D view'], ['tl', 'Timeline']].map(([k, l]) => `<button data-win="${k}" class="${App.mode === k ? 'on' : ''}">${l}</button>`).join('')}</div>
      <button class="who" data-who title="Who edits on this computer: signs notes and accepted breaks · click to switch"><i style="background:${WHO[App.who].c}">${App.who}</i>${WHO[App.who].n}</button>
      <span class="syncpill" title="The bridge to Unreal comes in phase F3-F4. Today the score lives in obra/score/score.json and nothing is sent to Unreal."><span class="sd"></span>Unreal: not connected · contract v0</span>
      <span style="font-size:11px;font-weight:600;letter-spacing:-0.008em;color:var(--ink-2);white-space:nowrap;margin-left:6px;">Soul Charger · Experience</span>
      <span class="tnum savest${App.dirty ? ' dirty' : ''}">rev ${App.baseRev}${App.dirty ? ' · unsaved' : ''} · ${P.name.toLowerCase()} ${fmtMS(App.sched.total)}</span>`;
  }
  function menuItems(name) {
    const sel = App.selKind === 'el' && El(App.sel);
    if (name === 'File') return [
      ['Save', 'Ctrl+S', save], ['Export score…', '', exportScore], ['Import score…', '', () => $('#jsonIn').click()],
      'sep', ['Reload from disk', 'discards unsaved', () => { if (!App.dirty || confirm('Discard your unsaved changes and reload score.json?')) reloadFromDisk(); }],
      'sep', ['Open the 3D view in a new tab', '', openSecondTab]];
    if (name === 'Edit') return [
      ['Undo', 'Ctrl+Z', undo, { dis: !App.undo.length }], ['Redo', 'Ctrl+Shift+Z', redo, { dis: !App.redo.length }],
      'sep', ['Add at the playhead…', 'Shift+A', () => quickAdd()], ['New lane', 'Alt+T', () => Act.newLane(sel ? sel.group : 'fx')],
      ['Delete selection', 'Del', () => sel && Act.remove([App.sel]), { dis: !sel, danger: true }],
      'sep', ['Bookmark at the playhead', 'M', () => Act.bookmark()], ['Note for the team', 'Shift+M', () => noteBox()]];
    if (name === 'Experience') return [{ head: 'Simulated user' }, ...Object.entries(ScoreEngine.PERSONAS).map(([k, p]) => [p.name, p.note, () => setPersona(k), { on: App.persona === k }]),
      'sep', ['Problems', 'F8', () => toggleDrawer()], ['Show anchors', 'A', () => { App.showAnchors = !App.showAnchors; renderTimelineSelection(); renderTransport(); }, { on: App.showAnchors }]];
    if (name === 'Window') return [['All-in-one', '', () => setMode('all'), { on: App.mode === 'all' }], ['3D view', '', () => setMode('v3d'), { on: App.mode === 'v3d' }], ['Timeline', '', () => setMode('tl'), { on: App.mode === 'tl' }],
      'sep', ['Open the 3D view in a new tab', '', openSecondTab]];
    return [];
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
    for (const [id, e] of Object.entries(App.score.elements)) { const s = e.sound || (e.isNew ? e.key : null); if (!s) continue; if (!m.has(s)) m.set(s, { id: s, uses: [], group: e.group, isNew: !!e.isNew, audio: e.audio }); m.get(s).uses.push(id); }
    return [...m.values()].sort((a, b) => (b.isNew - a.isNew) || a.id.localeCompare(b.id));
  }
  function renderLibrary() {
    const S = App.score, T = App.sched.t, q = (App.libQuery || '').toLowerCase().trim();
    const tabs = [['scenes', 'Scenes'], ['roles', 'Roles'], ['sounds', 'Sounds'], ['actions', 'Actions']].map(([k, l]) => `<button data-lib="${k}" class="${App.libTab === k ? 'on' : ''}" style="padding:0 8px;">${l}</button>`).join('');
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
    } else if (App.libTab === 'roles') {
      rows = Object.entries(App.roles.roles).filter(([n]) => !q || n.toLowerCase().includes(q)).map(([name, R]) => {
        const n = R.groups.reduce((a, g) => a + g.rows.length, 0);
        return `<div class="mitem click${App.selRole === name ? ' sel' : ''}" data-role="${esc(name)}"><div class="mthumb gl" style="background:${R.icon === 'alma' ? '#8468BE' : R.icon === 'sound' ? App.HUE.fx : R.icon === 'logic' ? App.HUE.int : App.HUE.obj};">${ICO(R.icon, 14)}</div><div class="mtxt"><span class="mname">${esc(name)}</span><span class="mmeta">${esc(R.actor)} · ${n} knob${n === 1 ? '' : 's'}</span></div><span class="chip ok">in Unreal</span></div>`;
      }).join('') + `<div class="knote">Read from Unreal by hand on ${esc(App.roles.verified || '—')}. Read-only until the bridge (phase F3).</div>`;
    } else if (App.libTab === 'sounds') {
      rows = soundIndex().filter(s => !q || s.id.toLowerCase().includes(q)).map(s => {
        const kind = s.group === 'vo' ? 'VO' : s.group === 'amb' ? 'Ambience' : s.group === 'hap' ? 'Haptic' : 'FX';
        const meta = s.isNew ? `${kind} · ${s.audio ? esc(s.audio.file) : 'no file yet'}` : `${kind} · used ${s.uses.length}×`;
        const chip = s.isNew ? '<span class="chip prov">not in Unreal</span>' : s.group === 'hap' ? '<span class="chip lit">preview</span>' : '';
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

  /* ================= viewer ================= */
  function renderViewerBar(msg) {
    $('#vptool').innerHTML = `<span style="display:flex;color:var(--ink-3);">${ICO('viewer')}</span><span class="vlab">3D preview · narrative prototype${App.SC ? '' : ' · loading…'}</span><div style="flex:1;"></div>
      ${App.view === '3d' ? '<span class="vlab">Follows the timeline tab</span>' : `<button class="crbtn" data-pop title="Open the 3D view in its own tab: it follows this playhead">${ICO('popout', 12)}<span class="crlbl" style="display:inline;">New tab</span></button>`}`;
    const v = $('#vmsg'), t = msg || (App.persona !== 'typical' ? `3D plays the typical user · the timeline shows the ${persona().name.toLowerCase()} one`
      : App.protoDiff ? `3D shows the prototype's own timing · ${App.protoDiff} element${App.protoDiff > 1 ? 's' : ''} of your score differ` : '');
    v.textContent = t; v.classList.toggle('on', !!t);
  }

  /* ================= transport ================= */
  function renderTransport() {
    const b = beatAt(App.ph), bs = App.sched.t[b][0], P = persona(), k = pbCounts();
    $('#transport').innerHTML = `<span class="plabel">Simulated user</span><button class="ddbtn" data-persdd title="How long the simulated user takes in each wait. Not an Unreal value."><span style="display:flex;color:var(--ink-3);">${ICO('person', 11)}</span><span>${P.name}</span><span style="display:flex;color:var(--ink-3);">${ICO('chevDown', 9)}</span></button>
      <div class="tccenter"><button class="tbtn" data-tr="start" title="Go to start · Home">${ICO('toStart')}</button><button class="playb" data-tr="play" title="Play · Space">${ICO(App.playing ? 'pause' : 'play')}</button><button class="tbtn" data-tr="end" title="Go to end · End">${ICO('toEnd')}</button><button class="tbtn${App.follow ? ' on' : ''}" data-tr="follow" title="Follow the playhead">${ICO('follow')}</button>
       <div class="tcbox"><span class="tc" id="tcv">${tc(App.ph)}</span><div style="width:.5px;height:14px;background:rgba(255,255,255,0.08);"></div><span class="rel" id="tcrel">+${fmtS(App.ph - bs)} s in ${esc(App.score.beats[b].key)}</span></div>
       <button class="tbtn" data-tr="mark" title="Bookmark at the playhead · M" style="color:var(--ink-2);">${ICO('flag')}</button></div>
      <div style="flex:1;"></div>
      ${App.mode === 'v3d' ? '' : `<div class="editseg"><button data-tr="anchors" class="${App.showAnchors ? 'on' : ''}" title="Anchor curves of the selection · A">${ICO('anchor', 11)} Anchors</button><button data-tr="problems" class="${App.drawer === 'problems' ? 'on' : ''}" title="Problems · F8">${ICO('warn', 11)} Problems${k.b + k.w ? ` <span style="color:var(--danger);margin-left:3px;">${k.b + k.w}</span>` : ''}</button><button data-tr="fit" title="Fit the whole piece">${ICO('fit')} Fit</button></div>
      <div class="zoomgrp"><button data-tr="zout" title="Zoom out · Ctrl+wheel">${ICO('zoomOut')}</button><button data-tr="zin" title="Zoom in · Ctrl+wheel">${ICO('zoomIn')}</button></div>`}`;
  }

  /* ================= timeline ================= */
  function tickStep() { const steps = [1, 2, 5, 10, 15, 30, 60, 120, 300]; for (const s of steps) if (s * App.pps >= 64) return s; return 600; }
  function renderTimeline() {
    if (App.mode === 'v3d') return;
    const S = App.score, T = App.sched.t, total = App.sched.total, W = Math.ceil(X(total) + 240);
    const pbm = pbMap(), order = S.acts.flatMap(a => a.beats);
    const acts = App.sched.acts.map((a, i) => { const A = S.acts[i]; return `<div class="actb a${i % 2}" data-act="${a.id}" style="left:${X(a.s)}px;width:${Math.max(0, X(a.e) - X(a.s))}px;" title="${esc(A.name)}">${esc(A.name)}</div>`; }).join('');
    const mj = tickStep(), mn = mj >= 60 ? mj / 6 : mj / 5;
    let ticks = '';
    for (let t = 0; t <= total + 30; t += mn) { const isM = Math.abs(t / mj - Math.round(t / mj)) < 1e-6; if (!isM && mn * App.pps < 7) continue; ticks += `<span class="tk ${isM ? 'mj' : 'mn'}" style="left:${X(t)}px"></span>`; if (isM) ticks += `<span class="tkl tnum" style="left:${X(t)}px">${fmtMS(t)}</span>`; }
    for (const [id, sv] of Object.entries(pbm)) if (T[id]) ticks += `<span class="rulmark" style="left:${X(T[id][0]) - 2}px;background:var(--danger);opacity:${sv === 'warn' ? .55 : 1}"></span>`;
    for (const [id, e] of Object.entries(S.elements)) if (e.neAPK && T[id]) ticks += `<span class="rulmark" style="left:${X(T[id][0]) - 2}px;background:var(--auto-ovr)"></span>`;
    for (const [mid, m] of Object.entries(S.markers || {})) ticks += `<span class="mkr" data-mk="${mid}" style="left:${X(m.t)}px" title="${esc(m.name)} · ${tc(m.t)}"></span>`;
    const pb = beatAt(App.ph);
    const moms = order.map((b, i) => { const s = T[b][0], nx = i < order.length - 1 ? T[order[i + 1]][0] : T[b][1]; const w = Math.max(16, X(nx) - X(s) - 6);
      return `<div class="momb${b === pb ? ' on' : ''}" data-beat="${b}" style="left:${X(s) + 3}px;max-width:${w}px;" title="${esc(S.beats[b].key + ' · ' + S.beats[b].title)} · drag to move the moment"><b>${esc(S.beats[b].key)}</b>${esc(S.beats[b].title)}</div>`; }).join('');
    const momLines = order.map(b => `<div class="momline" style="left:${HDR + X(T[b][0])}px"></div>`).join('');
    const byLane = {};
    for (const [id, e] of Object.entries(S.elements)) (byLane[e.lane] = byLane[e.lane] || []).push(id);
    let rows = '', alt = 0;
    for (const g of S.groups) {
      const col = !!App.collapsed[g.id], hue = g.hue || hueOf(g.id), aud = App.AUD.has(g.id) ? ' aud' : '';
      let sum = '';
      if (col) for (const l of g.lanes) for (const id of byLane[l] || []) { const e = El(id); if (isInstant(e)) continue; const [s, en] = T[id]; sum += `<span class="sum" style="left:${X(s)}px;width:${Math.max(6, X(en) - X(s))}px;background:${hue};color:${textOn(hue)}">${esc(e.key)}</span>`; }
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
    const tlc = $('#tlc');
    tlc.style.width = (HDR + W) + 'px';
    tlc.innerHTML = `<div class="tlhead"><div class="hpad"><div style="height:18px;">Acts</div><div style="height:24px;">Time</div><div style="height:16px;">Moments</div></div><div class="hfld"><div class="actrow">${acts}</div><div class="rulerow" id="ruler">${ticks}<div class="phr" id="phr"></div></div><div class="momrow">${moms}</div></div></div>
      <div id="moml">${momLines}</div>${rows}<svg class="anc" id="anc"></svg><div class="ph" id="ph"></div>`;
    laneTop = {}; groupTop = {};
    tlc.querySelectorAll('.row[data-lane]').forEach(r => { laneTop[r.dataset.lane] = r.offsetTop; });
    tlc.querySelectorAll('.row.grow').forEach(r => { groupTop[r.dataset.group] = r.offsetTop; });
    movePlayhead(); renderTimelineSelection();
  }
  function laneHTML(ids, h, hue, pbm) {
    const T = App.sched.t; let out = '';
    const fg = textOn(hue);
    ids.forEach((id, i) => {
      const e = El(id), [s, en] = T[id], x = X(s);
      const pb = pbm[id], tip = `${e.key}${e.label && e.label !== e.key ? ' · ' + e.label : ''}`;
      if (isInstant(e)) {
        let nx = Infinity; for (let j = i + 1; j < ids.length; j++) { nx = X(T[ids[j]][0]); break; }
        const lw = Math.max(18, Math.min(220, nx - x - 12));
        out += `<div class="evt${e.isNew ? ' new' : ''}${pb ? ' pb-' + pb : ''}${e.neAPK ? ' neapk' : ''}" data-id="${id}" style="left:${x - 3.5}px;top:${(h - 16) / 2}px;max-width:${lw}px;" title="${esc(tip)}"><i style="background:${hue}"></i><span>${esc(e.key)}</span></div>`;
        return;
      }
      const w = Math.max(6, X(en) - x), ch = h - 8;
      const help = !!e.help, inact = help && App.sched.helpActive[id] === false;
      const con = Integrity.contractFor(e, App.contract).filter(c => c.kind !== 'not-in-unreal');
      let cls = 'clip' + (e.gate ? ' wait' : '') + (help ? ' help' : '') + (inact ? ' inact' : '') + (pb ? ' pb-' + pb : '') + (e.neAPK ? ' neapk' : '');
      let gl = e.type === 'vo' ? ICO('wave', 11) : e.gate ? ICO('hourglass', 10) : e.type === 'instruction' ? ICO('ghost', 11) : '';
      if (con.length) gl = ICO('wire', 10) + gl;
      let body = '';
      if (e.type === 'vo' && ch > 20) body = `<div class="bd">${wave(e.key, w, ch - 16, fg)}<div class="vtx">${esc(e.text || '')}</div></div>`;
      const sub = e.type === 'vo' ? (help ? 'help' : '') : (e.label && e.label !== e.key ? e.label : '');
      const trim = !App.locked[e.group] && (e.gate || (e.dur && e.dur.mode === 'fixed'));
      out += `<div class="${cls}" data-id="${id}" style="left:${x}px;width:${w}px;height:${ch}px;" title="${esc(tip)}"><div class="fill" style="background-color:${hue}"></div><div class="scrim"></div><div class="tt" style="background:${hue};color:${fg}"><span class="gl">${gl}</span>${esc(e.key)}${sub ? `<span class="cpx">${esc(sub)}</span>` : ''}</div>${body}${pb ? `<span class="pbdot${pb === 'warn' ? ' ring' : ''}" title="Open problem · see Problems (F8)"></span>` : ''}${e.neAPK ? '<span class="neapkchip" title="Accepted break: the APK still does what Unreal is wired to do">≠ APK</span>' : ''}${trim ? '<div class="hd r" data-trim="1" title="Drag to change the duration"></div>' : ''}</div>`;
      if (e.gate) {
        const fwx = X(s + e.gate.fw);
        if (fwx > x + w + 1) out += `<div class="wtail" style="left:${x + w}px;width:${fwx - x - w}px;height:${ch}px;"><span class="wt">up to ${fmtS(e.gate.fw)} s</span></div>`;
        out += `<div class="wfw" style="left:${fwx - 1}px;height:${h - 4}px;" title="Timeout ${e.gate.fw} s"><span>${e.gate.fw} s</span></div>`;
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
  function familyOf(id) { return id && El(id) ? ScoreEngine.family(App.score, id, App.kids) : new Set(); }
  function renderTimelineSelection() {
    const tlc = $('#tlc'); if (!tlc || App.mode === 'v3d') return;
    tlc.querySelectorAll('.sel,.gsel').forEach(n => n.classList.remove('sel', 'gsel'));
    if (App.selKind === 'el' && El(App.sel)) {
      tlc.querySelectorAll(`[data-id="${App.sel}"]`).forEach(n => n.classList.add('sel'));
      for (const k of familyOf(App.sel)) tlc.querySelectorAll(`[data-id="${k}"]`).forEach(n => n.classList.add('gsel'));
    }
    if (App.selKind === 'beat') tlc.querySelectorAll(`[data-beat="${App.sel}"]`).forEach(n => n.classList.add('sel'));
    drawAnchors();
  }
  function drawAnchors() {
    const svg = $('#anc'), tlc = $('#tlc'); if (!svg || !tlc) return;
    svg.setAttribute('width', tlc.scrollWidth); svg.setAttribute('height', tlc.scrollHeight);
    const id = App.sel, e = App.selKind === 'el' && El(id);
    if (!App.showAnchors || !e) { svg.innerHTML = ''; return; }
    const T = App.sched.t, S = App.score;
    const yOf = r => { if (S.beats[r]) return 50; const x = El(r); if (!x) return null; if (App.collapsed[x.group]) return groupTop[x.group] + 11; return laneTop[x.lane] != null ? laneTop[x.lane] + laneH(x.group) / 2 : null; };
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
  function revealEl(id) {
    const e = El(id); if (!e) return; revealTime(App.sched.t[id][0]);
    const sc = $('#sctl'); if (!sc) return; const y = App.collapsed[e.group] ? groupTop[e.group] : laneTop[e.lane];
    if (y != null && (y < sc.scrollTop + 58 || y > sc.scrollTop + sc.clientHeight - 40)) sc.scrollTop = Math.max(0, y - 58 - 40);
  }

  /* ================= problems drawer ================= */
  function toggleDrawer() { App.drawer = App.drawer === 'problems' ? null : 'problems'; renderDrawer(); renderTransport(); }
  function renderDrawer() {
    const d = $('#drawer'), tl = $('#timeline');
    if (App.drawer !== 'problems' || App.mode === 'v3d') { d.innerHTML = ''; tl.classList.remove('withdrawer'); return; }
    tl.classList.add('withdrawer');
    const k = pbCounts(), f = App.pbFilter || 'open', rank = { block: 0, inv: 0, warn: 1, info: 2 };
    let list = App.problems.filter(p => f === 'all' ? true : f === 'accepted' ? p.st === 'accepted' : f === 'apk' ? (p.ly === 'C3' && p.sv !== 'info') : p.st === 'open');
    list = list.slice().sort((a, b) => (a.st === 'accepted') - (b.st === 'accepted') || rank[a.sv] - rank[b.sv] || (a.el && App.sched.t[a.el] ? App.sched.t[a.el][0] : 0) - (b.el && App.sched.t[b.el] ? App.sched.t[b.el][0] : 0));
    d.innerHTML = `<div class="pdraw"><div class="ph2"><b>Problems</b><span>${k.b} blocking · ${k.w} warnings · ${k.i} notes · ${k.a} accepted</span><div class="well" style="margin-left:12px;">${[['open', 'Open'], ['apk', 'Affects APK'], ['accepted', 'Accepted'], ['all', 'All']].map(([v, l]) => `<button data-pf="${v}" class="${f === v ? 'on' : ''}">${l}</button>`).join('')}</div><div style="flex:1;"></div><span style="color:var(--ink-3);">Rules re-run on every edit · ${persona().name.toLowerCase()} user</span><button class="ibtn flat" data-tr="problems" title="Close · F8">${ICO('chevDown')}</button></div>
      <div class="plist"><div class="prw hd"><span></span><span>Layer</span><span>Rule</span><span>Message</span><span>Element</span><span>Owner in Unreal</span><span>State</span><span>Author · reason</span></div>
      ${list.map(p => `<div class="prw"><span class="sv ${p.st === 'accepted' ? 'acc' : p.sv === 'inv' ? 'block' : p.sv}"></span><span>${p.ly}</span><span title="${esc(p.rule)}">${esc(p.rule)}</span><span class="m" title="${esc(p.msg)}">${esc(p.msg)}</span>${p.el ? `<span class="el" data-goto="${p.el}">${esc(keyOf(p.el))}</span>` : '<span>—</span>'}<span title="${esc(p.own || '')}">${esc(p.own || '—')}</span><span class="st ${p.st === 'accepted' ? 'acc' : 'open'}">${p.st === 'accepted' ? `Accepted${p.neAPK ? ' · ≠ APK' : ''} · <a data-reopen="${esc(p.fp)}" style="cursor:pointer;text-decoration:underline;">reopen</a>` : 'Open'}</span><span title="${esc(p.reason || '')}">${p.who ? esc(p.who) + ' · "' + esc(p.reason || '') + '"' : '—'}</span></div>`).join('') || '<div class="knote" style="padding:10px 0;">Nothing here.</div>'}</div></div>`;
  }

  /* ================= inspector ================= */
  function prow(lab, val, u, pct, pc, o) {
    o = o || {};
    return `<div class="prow"${pc ? ` style="--pc:${pc}"` : ''}${o.title ? ` title="${esc(o.title)}"` : ''}><span class="lab">${lab}</span><div class="field" style="cursor:default;">${pct != null ? `<div class="track"><i style="width:${Math.max(0, Math.min(100, pct))}%;${pc ? `background:${pc}` : ''}"></i></div>` : ''}<div class="box"><span class="num">${esc(val)}</span><span class="u">${esc(u || '')}</span></div></div>${o.lock ? `<span class="lock" title="Final value approved in the test level">${ICO('lock', 11)}</span>` : ''}</div>`;
  }
  const prowTxt = (lab, html, title) => `<div class="prow"${title ? ` title="${esc(title)}"` : ''}><span class="lab">${lab}</span><span class="val">${html}</span></div>`;
  const prowIn = (lab, f, v, u, title, step) => `<div class="prow"${title ? ` title="${esc(title)}"` : ''}><span class="lab">${lab}</span><span class="val"></span><input class="ni tnum" data-f="${f}" type="number" step="${step || 0.1}" value="${+(+v).toFixed(3)}"><span class="u2">${u || ''}</span></div>`;
  function sec(id, t, body) {
    const open = !(App.secClosed && App.secClosed[id]);
    return `<button class="sechead" data-sec="${id}"><span style="color:var(--ink-dim);display:flex;${open ? '' : 'transform:rotate(-90deg);'}">${ICO('chevDown')}</span><span class="t">${t}</span><span class="ln"></span></button>${open ? body : ''}`;
  }
  function head(hue, icon, name, meta) {
    return `<div style="height:4px;width:100%;background:${hue};"></div><div class="selhead"><div class="selthumb" style="display:grid;place-items:center;background:var(--s2);color:var(--ink-2);">${ICO(icon, 16)}</div><div style="flex:1;min-width:0;"><div class="selname" title="${esc(name)}">${esc(name)}</div><div class="selmeta">${meta}</div></div></div>`;
  }
  function insTabs() {
    const n = Object.keys(App.score.notes || {}).length;
    return `<div class="panhead"><div class="well" style="height:22px;"><button class="instab${App.insTab === 'insp' ? ' on' : ''}" data-itab="insp" style="display:inline-flex;align-items:center;gap:5px;">${ICO('panel')}<span class="ttl">Inspector</span></button><button class="instab${App.insTab === 'notes' ? ' on' : ''}" data-itab="notes" style="display:inline-flex;align-items:center;gap:5px;">${ICO('note')}<span class="ttl">Notes</span>${n ? `<span class="countbadge" style="margin-left:2px;">${n}</span>` : ''}</button></div></div>`;
  }
  function knobGroups(name) {
    const R = App.roles.roles[name];
    return R.groups.map(g => `<div class="owner"><b>${esc(g.owner)}</b><span class="sc">${esc(g.scope)}</span></div>` + g.rows.map(k => k[3] == null
      ? prowTxt(esc(k[0]), `${esc(k[1])}${k[2] ? ' ' + esc(k[2]) : ''}${g.scope === 'literal' ? ' <span class="chip lit">literal</span>' : ''}`, `${k[5]} · ${g.owner}`)
      : prow(esc(k[0]), k[1], k[2], k[3], k[4], { title: `${k[5]} · ${g.owner} · ${g.scope}`, lock: k[6] })).join('')).join('')
      + (R.note ? `<div class="knote warn">${esc(R.note)}</div>` : '')
      + `<div class="knote">Read from Unreal (${esc(App.roles.verified || '—')}). Hover a knob to see its variable. Changing them from here comes with the bridge (phase F3); the lock marks values approved in the test levels.</div>`;
  }
  function anchorChip(a, edgeWord) {
    if (!a || !a.ref) return `<span class="anchip"><i>${ICO('anchor', 11)}</i>start of the piece</span>`;
    const isBeat = !!App.score.beats[a.ref];
    const word = isBeat ? (a.edge === 'end' ? 'end of' : 'start of') : (a.edge === 'end' ? (edgeWord || 'after') : 'with');
    return `<span class="anchip" data-goto="${a.ref}" title="Select the anchor">${'<i>' + ICO('anchor', 11) + '</i>'}${word} ${esc(keyOf(a.ref))}</span>`;
  }
  function renderInspector() {
    const el = $('#inspector'), body = el.querySelector('.insbody'), st = body ? body.scrollTop : 0, same = el.dataset.for === (App.sel || App.selRole || '') + App.insTab;
    let h = insTabs();
    if (App.insTab === 'notes') h += notesHTML();
    else if (App.selKind === 'role' && App.roles.roles[App.selRole]) h += roleHTML(App.selRole);
    else if (App.selKind === 'beat' && App.score.beats[App.sel]) h += beatHTML(App.sel);
    else if (App.selKind === 'el' && El(App.sel)) h += elementHTML(App.sel);
    else h += `<div class="insbody"><div class="insEmpty">Select an item<br>in the timeline or the library</div></div>`;
    el.innerHTML = h; el.dataset.for = (App.sel || App.selRole || '') + App.insTab;
    if (same) { const b = el.querySelector('.insbody'); if (b) b.scrollTop = st; }
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
      + sec('time', 'Time', prowTxt('Starts', anchorChip(at) + ` <span class="tnum" style="color:var(--ink-3);margin-left:4px;">${tc(T[0])}</span>`)
        + prowIn('Offset', 'beatoff', at.off || 0, 's', 'Seconds after its anchor. Everything after this moment moves with it.')
        + prowTxt('Ends', `${tc(T[1])} · with its last element`))
      + sec('els', `Elements · ${els.length}`, els.map(([id, e]) => `<div class="prow"><span class="mdot" style="background:${hueOf(e.group)}"></span><span class="val"><a data-goto="${id}" style="cursor:pointer;color:var(--ink);">${esc(e.key)}</a> · ${KIND[e.type] || e.type}</span><span class="u2 tnum">${fmtS(App.sched.t[id][0] - T[0])}</span></div>`).join(''))
      + '</div>';
  }
  function elementHTML(id) {
    const e = El(id), T = App.sched.t[id], hue = hueOf(e.group), g = App.score.groups.find(x => x.id === e.group), B = App.score.beats[e.beat];
    const dur = T[1] - T[0], role = roleFor(e), con = Integrity.contractFor(e, App.contract);
    const meta = `${KIND[e.type] || e.type} · ${isInstant(e) ? 'instant' : fmtS(dur) + ' s'} · ${esc(B ? B.key : '—')}${e.isNew ? ' · <span style="color:var(--auto-ovr)">not in Unreal yet</span>' : ''}`;
    let h = `<div class="insbody">${head(hue, e.isNew ? 'sound' : ICON[e.type] || 'obj', e.key, meta)}`;
    if (e.label && e.label !== e.key) h += `<div class="knote" style="color:var(--ink-2);">${esc(e.label)}</div>`;
    if (e.note) h += `<div class="knote">${esc(e.note)}</div>`;
    // time
    let durRow;
    if (e.gate) durRow = prowTxt('Duration', `${fmtS(dur)} s · ${persona().name.toLowerCase()} user`);
    else if (e.end && e.end.ref) durRow = prowTxt('Lasts', anchorChip(e.end, 'until the end of').replace('after', 'until'));
    else if (isInstant(e)) durRow = prowTxt('Duration', e.type === 'sound' || e.type === 'ambience' ? 'instant · the file plays to its end' : 'instant');
    else if (e.dur.mode === 'audio') durRow = prowTxt('Duration', `${fmtS(dur)} s · its audio <span class="lock" title="A voice lasts as long as its audio file">${ICO('lock', 11)}</span>`);
    else durRow = prowIn('Duration', 'dur', e.dur.value, 's', 'Fixed duration. Drag the right edge of the clip, or type it here.');
    const laneOpts = g.lanes.map(l => `<option value="${l}"${l === e.lane ? ' selected' : ''}>${esc(App.score.lanes[l].name)}</option>`).join('');
    h += sec('time', 'Time', prowTxt('Starts', anchorChip(e.at) + ` <span class="tnum" style="color:var(--ink-3);margin-left:4px;">${tc(T[0])}</span>`)
      + prowIn('Offset', 'off', (e.at && e.at.off) || 0, 's', 'Seconds after its anchor. Elements anchored to this one move with it.')
      + durRow
      + `<div class="prow"><span class="lab">Lane</span><select class="selsel" data-f="lane">${laneOpts}</select></div>`);
    // wait
    if (e.gate) {
      const helps = Object.entries(App.score.elements).filter(([, x]) => x.help === id);
      const pers = Object.entries(ScoreEngine.PERSONAS).map(([k, P]) => { const r = ScoreEngine.resolve(App.score, { persona: k }); const hp = helps.some(([hid]) => r.helpActive[hid]); return `<div data-pers="${k}" class="${App.persona === k ? 'on' : ''}" title="${esc(P.note)}"><span>${P.name}</span><b class="tnum">${fmtS(P.wait(e.gate))} s</b><span>${helps.length ? (hp ? 'help plays' : 'no help') : '—'}</span></div>`; }).join('');
      const c = con.find(x => x.kind === 'knob' && x.knob);
      h += sec('wait', 'Wait', prowIn('Expected', 'exp', e.gate.expected, 's', 'How long a typical user takes. A simulation value: it never reaches Unreal.')
        + prowIn('Timeout', 'fw', e.gate.fw, 's', c ? `${c.knob.name} in ${c.owner}` : 'After this the piece moves on by itself.')
        + (c ? prowTxt('In Unreal', `${esc(c.knob.name)} = ${c.knob.value} s${c.knob.lock ? ' <span class="lock">' + ICO('lock', 11) + '</span>' : ''}`) : '')
        + prowTxt('Help', helps.length ? helps.map(([hid, x]) => `<span class="anchip" data-goto="${hid}">${ICO('wave', 11)} ${esc(x.key)}</span>`).join(' ') : '<span style="color:var(--auto-ovr)">none · every wait needs a help line</span>')
        + `<div class="knote">Simulated users (not Unreal values):</div><div class="perstab">${pers}</div>`);
    }
    // voice
    if (e.type === 'vo') {
      h += sec('voice', 'Voice', `<textarea class="vtext" data-f="text" spellcheck="false">${esc(e.text || '')}</textarea>`
        + prowTxt('Audio', `${esc(e.sound || e.key)} · ${e.dur.mode === 'audio' ? 'final mix' : esc(e.dur.mode)}`)
        + prowTxt('From', 'Alma (2D)')
        + (e.help ? prowTxt('Helps', anchorChip({ ref: e.help, edge: 'start' })) : '')
        + `<div class="knote">Changing the text re-estimates the length until the real audio exists (1 s + words ÷ 2.4 + 0.5 s per ellipsis).</div>`);
    }
    // sound
    if (e.isNew) h += sec('sound', 'Sound', newSoundHTML(id, e));
    else if (e.type === 'sound' || e.type === 'ambience' || e.type === 'haptic') h += sec('sound', 'Sound', prowTxt('File', `${esc(e.sound || e.key)} ${e.type === 'haptic' ? '<span class="chip lit">preview</span>' : '<span class="chip ok">real</span>'}`) + (e.simOnly ? `<div class="knote">Simulation only: it doesn't exist in Unreal.</div>` : ''));
    if (e.type === 'instruction' && (e.hint || e.ghost)) h += sec('ghost', 'Instruction', prowTxt('Ghost', esc(e.ghost || '—')) + (e.hint ? `<div class="knote" style="color:var(--ink-2);">"${esc(e.hint)}"</div>` : ''));
    if (role) h += sec('knobs', `${esc(role)} · knobs`, knobGroups(role));
    // unreal
    h += sec('unreal', 'Unreal', con.length ? con.map(c => `<div class="owner"><b>${esc(KINDTXT[c.kind] || c.kind)}</b><span class="sc">${esc(c.owner || '')}${c.graph ? ' › ' + esc(c.graph) : ''}</span></div><div class="knote">${esc(c.msg)}</div>`).join('')
      : `<div class="knote">${e.isNew ? 'New: it reaches Content after the next import and the APK only when a cue uses it.' : 'No contract entry yet: this element is a preview of the narrative prototype until the score is wired to Unreal (phase F4).'}</div>`);
    const mine = App.problems.filter(p => p.el === id);
    if (mine.length) h += sec('pb', `Problems · ${mine.length}`, mine.map(p => `<div class="knote ${p.st === 'accepted' ? 'warn' : p.sv === 'info' ? '' : 'bad'}">${p.st === 'accepted' ? 'Accepted · ' : ''}${esc(p.msg)}${p.reason ? ` · "${esc(p.reason)}"` : ''}</div>`).join(''));
    if (e.legacy) h += sec('legacy', 'Origin', prowTxt('Prototype', esc(e.legacy.uid)) + prowTxt('Track', esc(e.legacy.track)));
    h += `<div style="padding:10px 12px 16px;display:flex;gap:6px;"><button class="mbtn" data-act="del" title="Delete · Del">${ICO('trash', 12)} Delete</button></div>`;
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
      + prowTxt('Goes to', `Obra/Audio/FX/${esc(e.key)}`)
      + (a && a.inbox ? prowTxt('Waiting in', esc(a.inbox)) : '')
      + `<div class="knote">On the next import it becomes a SoundWave with this name. Keep the source WAV: Unreal's auto-import deletes the asset if the file disappears.</div>`;
  }
  function notesHTML() {
    const N = Object.entries(App.score.notes || {}).sort((a, b) => a[1].t - b[1].t);
    return `<div class="insbody notesl"><div style="padding:8px 12px;border-bottom:.5px solid var(--line-soft);"><textarea class="vtext" id="noteIn" placeholder="Note at ${tc(App.ph)} for the team…" spellcheck="false" style="margin:0;width:100%;"></textarea><div style="display:flex;justify-content:flex-end;margin-top:6px;"><button class="mbtn" data-act="addnote" style="height:22px;">Add note · ${WHO[App.who].n}</button></div></div>`
      + (N.length ? N.map(([, n]) => `<div class="nrow"><span class="av" style="background:${(WHO[n.who] || WHO.B).c}">${esc(n.who || '?')}</span><div class="nt"><span class="tnum" data-seek="${n.t}">${tc(n.t)} · ${esc(App.score.beats[beatAt(n.t)].key)}${n.el && El(n.el) ? ' · ' + esc(El(n.el).key) : ''}</span><p>${esc(n.text)}</p></div></div>`).join('') : '<div class="knote" style="padding:12px 2px;">No notes yet.</div>') + '</div>';
  }

  /* ================= status ================= */
  function renderStatus() {
    const k = pbCounts(), n = Object.keys(App.score.elements).length, e = App.selKind === 'el' && El(App.sel);
    let info = '';
    if (e) {
      const con = Integrity.contractFor(e, App.contract), lit = con.find(c => c.kind === 'literal');
      if (lit) info = `<span class="statinfo why"><span class="k">${esc(e.key)}</span> — hardwired in Unreal (${esc(lit.owner)}${lit.graph ? ' › ' + esc(lit.graph) : ''}) · changing it needs a graph change</span>`;
      else if (e.isNew) info = `<span class="statinfo why"><span class="k">${esc(e.key)}</span> — new sound · ${e.audio ? 'file loaded' : 'load a WAV in the inspector'}</span>`;
      else if (e.gate) info = `<span class="statinfo"><span class="k">${esc(e.key)}</span> — the user decides how long · timeout ${e.gate.fw} s · drag to move, its anchored elements follow</span>`;
      else if (e.type === 'vo') info = `<span class="statinfo"><span class="k">${esc(e.key)}</span> — lasts as long as its audio · drag to move, its anchored elements follow · Ctrl+drag moves it alone</span>`;
      else info = `<span class="statinfo"><span class="k">${esc(e.key)}</span> — drag to move, its anchored elements follow · Ctrl+drag moves it alone · Alt+←/→ nudges</span>`;
    } else if (App.selKind === 'beat') info = `<span class="statinfo"><span class="k">${esc(keyOf(App.sel))}</span> — drag its chip in the moments band: everything after it moves too</span>`;
    else if (App.selKind === 'role') info = `<span class="statinfo"><span class="k">${esc(App.selRole)}</span> — knobs read from Unreal · read-only until the bridge</span>`;
    $('#status').innerHTML = `<span>Ready</span>${info}<div style="flex:1;"></div><span class="pbc" data-tr="problems" title="Problems · F8"><b class="bl">●</b> ${k.b} blocking <i class="wa"></i> ${k.w} warnings <b class="ac">●</b> ${k.a} accepted</span><span>${persona().name} · total ${fmtMS(App.sched.total)} · goal 15:00</span><span>0 of ${n} reach Unreal</span><span class="${App.dirty ? '' : 'ok'}" style="${App.dirty ? 'color:var(--auto-ovr)' : ''}">${App.dirty ? 'unsaved · Ctrl+S' : 'score rev ' + App.baseRev + (App.savedAt ? ' · saved' : '')}</span>`;
  }

  /* ================= overlays: impact card, quick add, note ================= */
  let impactCb = null;
  function impactCard(label, items, repairs, cb) {
    closeOverlay();
    // block (or a locked final value) needs a written reason; a warning can go ahead with one click, and is still recorded
    const mustReason = items.some(i => i.sv === 'block' || i.lock), breaks = items.some(i => i.sv === 'block' || i.sv === 'warn');
    const dot = sv => sv === 'warn' ? '<span class="d warn"></span>' : sv === 'info' ? '<span class="d" style="background:var(--ink-3)"></span>' : '<span class="d" style="background:var(--danger)"></span>';
    const word = sv => sv === 'block' ? 'Breaks' : sv === 'inv' ? 'Needs a decision' : sv === 'warn' ? 'Changes' : 'Note';
    const back = document.createElement('div'); back.className = 'impback ov';
    const d = document.createElement('div'); d.className = 'imp ov';
    d.innerHTML = `<h3>${esc(label)}<span>${items.filter(i => i.sv !== 'info').length} to review</span></h3>
      ${items.map(i => `<div class="it">${dot(i.sv)}<div style="min-width:0;"><b>${word(i.sv)} · ${esc(i.title)}</b>${esc(i.body)}${i.keys && i.keys.length > 1 ? `<div class="evl">Also: ${i.keys.slice(1, 8).map(esc).join(', ')}${i.keys.length > 8 ? '…' : ''}</div>` : ''}${i.ev ? `<div class="evl">${esc(i.ev)}</div>` : ''}</div></div>`).join('')}
      ${repairs.length ? `<div class="rep">${repairs.map((r, k) => `<label><input type="radio" name="rep" value="${r.id}"${r.checked ? ' checked' : ''}> ${esc(r.label)}</label>`).join('')}</div>` : ''}
      ${breaks ? `<div class="rep"${repairs.length ? ' style="border-top:none;"' : ''}><input class="rsn" id="rsn" placeholder="${mustReason ? 'Reason (12+ characters)' : 'Reason (optional)'} · e.g. I'll connect it to a new cue in Unreal" spellcheck="false"><span style="color:var(--ink-3);font-size:10px;">It goes to Problems as accepted, signed by ${WHO[App.who].n}${items.some(i => i.c3) ? ', and the element shows ≠ APK until Unreal follows' : ''}.</span></div>` : ''}
      <div class="btns"><button data-imp="cancel">Cancel</button>${breaks ? `<button class="anyway" data-imp="anyway"${mustReason ? ' disabled' : ''}>Proceed anyway</button>` : `<button class="pri" data-imp="repair">${repairs.length ? 'Proceed and repair' : 'Proceed'}</button>`}</div>`;
    document.body.appendChild(back); document.body.appendChild(d);
    if (App.k < 1) d.style.transform = `translate(-50%,-50%) scale(${App.k})`;
    impactCb = cb;
    const rsn = d.querySelector('#rsn'), any = d.querySelector('[data-imp=anyway]');
    if (rsn) { rsn.addEventListener('input', () => { if (mustReason) any.disabled = rsn.value.trim().length < 12; }); rsn.addEventListener('keydown', ev => { if (ev.key === 'Enter' && !any.disabled) any.click(); if (ev.key === 'Escape') { ev.stopPropagation(); done('cancel'); } }); setTimeout(() => rsn.focus(), 30); }
    else setTimeout(() => { const p = d.querySelector('.pri'); if (p) p.focus(); }, 30);
    const done = dec => { const rep = (d.querySelector('input[name=rep]:checked') || {}).value || null; const r = rsn ? rsn.value.trim() : ''; const f = impactCb; impactCb = null; back.remove(); d.remove(); f(dec, r, rep); };
    d.addEventListener('click', ev => { const b = ev.target.closest('[data-imp]'); if (b && !b.disabled) done(b.dataset.imp); });
    back.addEventListener('click', () => done('cancel'));
    d._cancel = () => done('cancel');
  }
  function scaleOv(n) { if (App.k < 1) { n.style.transformOrigin = '0 0'; n.style.transform = `scale(${App.k})`; } }
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
  function noteBox() { App.insTab = 'notes'; if (App.mode === 'v3d') setMode('all'); renderInspector(); setTimeout(() => { const n = $('#noteIn'); if (n) n.focus(); }, 20); }

  /* ================= pointer: timeline ================= */
  let drag = null;
  const ghostEl = () => { let g = $('#dragGhost'); if (!g) { g = document.createElement('div'); g.id = 'dragGhost'; g.className = 'ghost'; g.innerHTML = '<div class="tt"></div>'; } return g; };
  const snapEl = () => { let s = $('#snapLine'); if (!s) { s = document.createElement('div'); s.id = 'snapLine'; s.className = 'snapline'; } return s; };
  function snapTimes(exclude) {
    const out = [App.ph]; for (const b of App.score.acts.flatMap(a => a.beats)) out.push(App.sched.t[b][0]);
    for (const [id, t] of Object.entries(App.sched.t)) if (!exclude.has(id) && El(id)) { out.push(t[0]); if (t[1] > t[0]) out.push(t[1]); }
    for (const m of Object.values(App.score.markers || {})) out.push(m.t);
    return out;
  }
  function snap(ns, dur, ev) {
    if (ev.altKey) return { ns, at: null };
    const tol = 6 / App.pps; let best = null;
    for (const c of drag.snaps) { for (const [edge, v] of [[0, ns], [dur, ns + dur]]) { const d = Math.abs(c - v); if (d < tol && (!best || d < best.d)) best = { d, ns: c - edge, at: c }; } }
    return best ? { ns: best.ns, at: best.at } : { ns, at: null };
  }
  function onTimelineDown(ev) {
    if (ev.button !== 0) return;
    const t = ev.target;
    if (t.closest('#ruler')) { ev.preventDefault(); drag = { kind: 'scrub' }; seek(timeFromClient(ev.clientX)); return; }
    const mom = t.closest('.momb');
    if (mom) { ev.preventDefault(); const b = mom.dataset.beat; drag = { kind: 'beat', id: b, x0: ev.clientX, s: App.sched.t[b][0], started: false, el: mom, left0: parseFloat(mom.style.left), snaps: snapTimes(new Set()) }; return; }
    const act = t.closest('.actb'); if (act) { const a = App.sched.acts.find(x => x.id === act.dataset.act); seek(a.s); revealTime(a.s); return; }
    if (t.closest('.gch')) { const g = t.closest('.gch').dataset.col; App.collapsed[g] = !App.collapsed[g]; savePref(); renderTimeline(); return; }
    if (t.closest('[data-lock]')) { const g = t.closest('[data-lock]').dataset.lock; App.locked[g] = !App.locked[g]; renderTimeline(); toast(App.locked[g] ? 'Group locked: nothing in it can be moved or deleted' : 'Group unlocked'); return; }
    if (t.closest('[data-newlane]')) { Act.newLane(t.closest('[data-newlane]').dataset.newlane); return; }
    const c = t.closest('[data-id]');
    if (c && c.closest('.fld')) {
      ev.preventDefault();
      const id = c.dataset.id, e = El(id); if (!e) return;
      if (ev.shiftKey && App.selKind === 'el') { select(id); return; }
      const [s, en] = App.sched.t[id];
      if (App.locked[e.group]) { select(id); toast(`${hueName(e.group)} is locked`); return; }
      if (t.closest('[data-trim]')) {
        if (e.type === 'vo') { toast('A voice lasts as long as its audio. Edit the text or load new audio.'); return; }
        drag = { kind: 'trim', id, x0: ev.clientX, s, en, started: false, el: c, snaps: snapTimes(new Set([id])) }; return;
      }
      const fam = familyOf(id); fam.add(id);
      drag = { kind: 'move', id, x0: ev.clientX, y0: ev.clientY, s, en, dur: en - s, started: false, el: c, lane: e.lane, group: e.group, target: e.lane, newLane: false, bad: false, fam, snaps: snapTimes(fam) };
      return;
    }
    if (t.closest('.fld')) { if (App.sel) select(null); }
  }
  function hueName(gid) { return (App.score.groups.find(g => g.id === gid) || {}).name || gid; }
  function onMove(ev) {
    if (!drag) return;
    if (drag.kind === 'scrub') { seek(timeFromClient(ev.clientX)); return; }
    if (drag.kind === 'resize') { const h = Math.max(160, Math.min(innerHeight / App.k - 220, drag.h0 - (ev.clientY - drag.y0) / App.k)); document.documentElement.style.setProperty('--tlh', h + 'px'); App.tlhUser = true; return; }
    if (drag.kind === 'gutter') { const w = Math.max(220, Math.min(520, drag.side === 'l' ? drag.w0 + (ev.clientX - drag.x0) / App.k : drag.w0 - (ev.clientX - drag.x0) / App.k)); drag.panel.style.width = w + 'px'; return; }
    const dx = (ev.clientX - drag.x0) / App.k;
    if (!drag.started) { if (Math.abs(dx) < 3 && Math.abs(ev.clientY - (drag.y0 || ev.clientY)) < 3) return; drag.started = true; if (drag.el) drag.el.classList.add('dragging'); if (drag.kind === 'move') { const sl = document.querySelector(`.slot[data-slot="${drag.group}"]`); if (sl) sl.style.display = 'flex'; } }
    const sline = snapEl();
    if (drag.kind === 'beat') {
      const r = snap(drag.s + dx / App.pps, 0, ev); drag.ns = Math.max(0, r.ns);
      drag.el.style.left = (drag.left0 + X(drag.ns - drag.s)) + 'px';
      showSnap(sline, r.at); setInfo(`Moment ${keyOf(drag.id)} · ${(drag.ns - drag.s >= 0 ? '+' : '')}${fmtS(drag.ns - drag.s)} s · everything after it moves too`);
      return;
    }
    if (drag.kind === 'trim') {
      const r = snap(drag.en + dx / App.pps, 0, ev); const nd = Math.max(.1, r.ns - drag.s); drag.nd = nd;
      const g = ghostEl(), fld = drag.el.parentElement; if (g.parentElement !== fld) fld.appendChild(g);
      g.className = 'ghost'; g.style.left = X(drag.s) + 'px'; g.style.width = X(nd) + 'px'; g.style.height = (fld.offsetHeight - 8) + 'px'; g.firstChild.textContent = `${keyOf(drag.id)} · ${fmtS(nd)} s`;
      showSnap(sline, r.at); return;
    }
    // move
    let r = snap(drag.s + dx / App.pps, drag.dur, ev); let ns = Math.max(0, r.ns);
    const under = document.elementFromPoint(ev.clientX, ev.clientY);
    const row = under && under.closest('.row[data-lane], .slot');
    let target = drag.target, newLane = drag.newLane;
    if (row && row.dataset.group === drag.group) { target = row.dataset.lane; newLane = false; }
    else if (row && row.classList.contains('slot') && row.dataset.slot === drag.group) { newLane = true; }
    drag.target = target; drag.newLane = newLane; drag.ns = ns;
    const busy = !newLane && laneBusy(target, ns, ns + Math.max(drag.dur, .05), drag.fam);
    drag.bad = !!busy;
    const fld = newLane ? document.querySelector(`.slot[data-slot="${drag.group}"] .sfl`) : document.querySelector(`[data-fld="${target}"]`);
    const g = ghostEl(); if (fld && g.parentElement !== fld) { fld.style.position = 'relative'; fld.appendChild(g); }
    g.className = 'ghost' + (busy ? ' bad' : '');
    g.style.left = X(ns) + 'px'; g.style.width = Math.max(10, X(drag.dur)) + 'px'; g.style.height = Math.max(10, (fld ? fld.offsetHeight : 20) - 8) + 'px';
    const d = ns - drag.s;
    g.firstChild.textContent = busy ? `${keyOf(drag.id)} · occupied by ${keyOf(busy)}` : `${keyOf(drag.id)} · ${d >= 0 ? '+' : ''}${fmtS(d)} s${newLane ? ' · new lane' : ''}`;
    showSnap(sline, r.at);
    setInfo(busy ? `${keyOf(drag.id)} → occupied: drop it on another lane, or on "+ New lane"` : `${keyOf(drag.id)} ${d >= 0 ? '+' : ''}${fmtS(d)} s${drag.fam.size > 1 ? ` · ${drag.fam.size - 1} anchored element${drag.fam.size > 2 ? 's' : ''} follow` : ''}${ev.ctrlKey || ev.metaKey ? ' · Ctrl: alone' : ''}${ev.altKey ? ' · Alt: no snap' : ''}`, busy);
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
    if (D.kind === 'beat') { if (!D.started) { select(D.id, 'beat'); seek(D.s); renderLibrary(); return; } Act.moveBeat(D.id, D.ns - D.s); renderTimeline(); return; }
    if (D.kind === 'trim') { if (D.started) Act.trim(D.id, D.nd); return; }
    if (!D.started) { select(D.id); return; }
    if (D.bad) { toast('Occupied: that lane already has something there. Drop it on another lane, or on "+ New lane".'); renderTimeline(); return; }
    Act.move(D.id, D.ns - D.s, D.newLane ? { newIn: D.group } : (D.target !== D.lane ? D.target : null), ev.ctrlKey || ev.metaKey);
    if (App.sel !== D.id) select(D.id);
  }
  function onContext(ev) {
    const t = ev.target;
    const fld = t.closest('.fld'), hdr = t.closest('[data-lanehdr]'), c = t.closest('[data-id]');
    if (!fld && !hdr) return;
    ev.preventDefault();
    const lid = fld ? fld.dataset.fld : hdr.dataset.lanehdr, gid = App.score.lanes[lid].group, gname = hueName(gid);
    if (c) {
      const id = c.dataset.id, e = El(id); select(id);
      openMenu(ev.clientX, ev.clientY, [{ head: e.key }, ['Go to its start', '', () => { seek(App.sched.t[id][0]); }], e.at && e.at.ref ? ['Select its anchor', keyOf(e.at.ref), () => goto(e.at.ref)] : null, ['Note about it', 'Shift+M', () => noteBox()], 'sep', ['Delete', 'Del', () => Act.remove([id]), { danger: true, dis: App.locked[e.group] }]].filter(Boolean), 200);
      return;
    }
    const items = [];
    if (fld) {
      const tt = timeFromClient(ev.clientX); seek(tt);
      items.push({ head: `Add here · ${gname} · ${tc(tt)}` });
      if (gid === 'vo') items.push(['Alma voice line', 'text + audio later', () => Act.add('vo'), { sw: App.HUE.vo }]);
      if (gid === 'fx' || gid === 'amb') items.push(['Empty sound…', 'name it, load a WAV', () => Act.add('sound'), { sw: App.HUE.fx }]);
      if (gid === 'int') items.push(['Wait', 'the user decides', () => Act.add('wait'), { sw: App.HUE.int }]);
      items.push(['Anything…', 'Shift+A', () => quickAdd({ x: ev.clientX, y: ev.clientY })], ['Bookmark here', 'M', () => Act.bookmark()], ['Note for the team', 'Shift+M', () => noteBox()], 'sep');
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
  function goto(id) {
    if (App.score.beats[id]) { select(id, 'beat'); seek(App.sched.t[id][0]); revealTime(App.sched.t[id][0]); return; }
    if (!El(id)) return; const e = El(id);
    if (App.collapsed[e.group]) { App.collapsed[e.group] = false; renderTimeline(); }
    select(id); seek(App.sched.t[id][0]); revealEl(id);
  }
  function zoom(f, cx) {
    const sc = $('#sctl'); if (!sc) return; const r = sc.getBoundingClientRect();
    const lx = cx == null ? HDR + (sc.clientWidth - HDR) / 2 : (cx - r.left) / App.k;   // pointer x inside the scroller, in app px
    const t = (lx + sc.scrollLeft - HDR) / App.pps;
    App.pps = Math.max(.4, Math.min(80, App.pps * f)); savePref(); renderTimeline();
    sc.scrollLeft = Math.max(0, t * App.pps + HDR - lx);
  }
  function fit() { const sc = $('#sctl'); if (!sc) return; App.pps = Math.max(.4, (sc.clientWidth - HDR - 40) / App.sched.total); savePref(); renderTimeline(); sc.scrollLeft = 0; }

  /* ================= wiring (once) ================= */
  function init() {
    if (booted) return; booted = true;
    const sctl = $('#sctl');
    sctl.addEventListener('mousedown', onTimelineDown);
    sctl.addEventListener('contextmenu', onContext);
    sctl.addEventListener('dblclick', ev => {
      const nm = ev.target.closest('[data-lanehdr] .nm'); if (nm) { renameLane(nm.closest('[data-lanehdr]').dataset.lanehdr); return; }
      if (ev.target.closest('.fld') && !ev.target.closest('[data-id]')) seek(timeFromClient(ev.clientX));
      const mk = ev.target.closest('[data-mk]'); if (mk) seek(App.score.markers[mk.dataset.mk].t);
    });
    sctl.addEventListener('wheel', ev => { if (!(ev.ctrlKey || ev.metaKey)) return; ev.preventDefault(); zoom(ev.deltaY < 0 ? 1.18 : 1 / 1.18, ev.clientX); }, { passive: false });
    sctl.addEventListener('scroll', () => document.querySelectorAll('.menu.ov').forEach(n => n.remove()));
    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
    document.addEventListener('mousedown', ev => { if (!ev.target.closest('.ov') && !ev.target.closest('[data-menu]') && !ev.target.closest('[data-persdd]')) document.querySelectorAll('.menu.ov,.qa.ov').forEach(n => n.remove()); }, true);
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
      if (ev.target.closest('[data-who]')) { App.who = App.who === 'B' ? 'S' : 'B'; savePref(); renderTop(); toast(`Editing as ${WHO[App.who].n}`); }
    });
    // transport + status + drawer share data-tr
    const tr = ev => {
      const b = ev.target.closest('[data-tr]'); if (b) {
        const k = b.dataset.tr;
        if (k === 'start') seek(0); else if (k === 'end') seek(App.sched.total); else if (k === 'play') play(!App.playing);
        else if (k === 'follow') { App.follow = !App.follow; savePref(); renderTransport(); }
        else if (k === 'mark') Act.bookmark(); else if (k === 'anchors') { App.showAnchors = !App.showAnchors; renderTimelineSelection(); renderTransport(); }
        else if (k === 'problems') toggleDrawer(); else if (k === 'fit') fit(); else if (k === 'zin') zoom(1.4); else if (k === 'zout') zoom(1 / 1.4);
        return;
      }
      const pd = ev.target.closest('[data-persdd]');
      if (pd) { const r = pd.getBoundingClientRect(); openMenu(r.left, r.bottom + 2, Object.entries(ScoreEngine.PERSONAS).map(([k, P]) => [P.name, P.note, () => setPersona(k), { on: App.persona === k }]), 240); }
      const pf = ev.target.closest('[data-pf]'); if (pf) { App.pbFilter = pf.dataset.pf; renderDrawer(); }
      const go = ev.target.closest('[data-goto]'); if (go) goto(go.dataset.goto);
      const ro = ev.target.closest('[data-reopen]'); if (ro) Act.reopen(ro.dataset.reopen);
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
      const sn = t.closest('[data-snd]'); if (sn) { goto(sn.dataset.snd); renderLibrary(); return; }
    });
    lib.addEventListener('input', ev => { if (ev.target.id === 'libq') { App.libQuery = ev.target.value; const pos = ev.target.selectionStart; renderLibrary(); const n = $('#libq'); n.focus(); n.setSelectionRange(pos, pos); } });
    // viewer
    $('#vptool').addEventListener('click', ev => { if (ev.target.closest('[data-pop]')) openSecondTab(); });
    // inspector
    const ins = $('#inspector');
    ins.addEventListener('click', ev => {
      const t = ev.target;
      const it = t.closest('[data-itab]'); if (it) { App.insTab = it.dataset.itab; renderInspector(); return; }
      const sh = t.closest('[data-sec]'); if (sh) { App.secClosed = App.secClosed || {}; App.secClosed[sh.dataset.sec] = !App.secClosed[sh.dataset.sec]; renderInspector(); return; }
      const go = t.closest('[data-goto]'); if (go) { goto(go.dataset.goto); return; }
      const ps = t.closest('[data-pers]'); if (ps) { setPersona(ps.dataset.pers); return; }
      const sk = t.closest('[data-seek]'); if (sk) { seek(+sk.dataset.seek); revealTime(+sk.dataset.seek); return; }
      const a = t.closest('[data-act]'); if (!a) return;
      const k = a.dataset.act;
      if (k === 'del') Act.remove([App.sel]);
      else if (k === 'wav') { App.wavTarget = App.sel; $('#wavIn').click(); }
      else if (k === 'play') { const u = BLOBS[App.sel]; if (u) new Audio(u).play().catch(() => {}); else toast('The file is in obra/audio/inbox; reload it here to listen.'); }
      else if (k === 'addnote') { const n = $('#noteIn'); if (n && n.value.trim()) Act.addNote(n.value); }
    });
    ins.addEventListener('change', ev => {
      const f = ev.target.dataset.f; if (!f) return; const v = ev.target.value, id = App.sel;
      if (f === 'off') Act.setOffset(id, parseFloat(v));
      else if (f === 'dur') Act.trim(id, parseFloat(v));
      else if (f === 'exp') Act.setGate(id, 'expected', parseFloat(v));
      else if (f === 'fw') Act.setGate(id, 'fw', parseFloat(v));
      else if (f === 'lane') Act.setLane(id, v);
      else if (f === 'text') Act.setText(id, v);
      else if (f === 'name') Act.rename(id, cleanId(v));
      else if (f === 'beatoff') { const B = App.score.beats[id], order = App.score.acts.flatMap(a => a.beats), prev = order[order.indexOf(id) - 1]; const cur = B.at ? B.at.off || 0 : 0; Act.moveBeat(id, parseFloat(v) - cur); }
    });
    ins.addEventListener('keydown', ev => { if (ev.key === 'Enter' && ev.target.matches('input.ni,input.nmin')) ev.target.blur(); if (ev.key === 'Enter' && (ev.ctrlKey || ev.metaKey) && ev.target.id === 'noteIn') { Act.addNote(ev.target.value); } });
    ins.addEventListener('dragover', ev => { const d = ev.target.closest('[data-drop]'); if (d) { ev.preventDefault(); d.classList.add('hot'); } });
    ins.addEventListener('dragleave', ev => { const d = ev.target.closest('[data-drop]'); if (d) d.classList.remove('hot'); });
    ins.addEventListener('drop', ev => { const d = ev.target.closest('[data-drop]'); if (!d) return; ev.preventDefault(); const f = ev.dataTransfer.files && ev.dataTransfer.files[0]; if (f) loadWav(App.sel, f); });
    $('#wavIn').addEventListener('change', ev => { const f = ev.target.files && ev.target.files[0]; if (f && App.wavTarget) loadWav(App.wavTarget, f); ev.target.value = ''; });
    $('#jsonIn').addEventListener('change', ev => { const f = ev.target.files && ev.target.files[0]; if (f) importScore(f); ev.target.value = ''; });
    let rz = 0; addEventListener('resize', () => { clearTimeout(rz); rz = setTimeout(drawAnchors, 120); });
  }

  function renderAll() { init(); renderTop(); renderLibrary(); renderViewerBar(); renderTransport(); renderTimeline(); renderDrawer(); renderInspector(); renderStatus(); }
  window.UI = { renderAll, renderTop, renderLibrary, renderViewerBar, renderTransport, renderTimeline, renderTimelineSelection, renderDrawer, renderInspector, renderStatus, movePlayhead, impactCard, quickAdd, noteBox, closeOverlay, goto };
})();
