/* Soul Charger · prototipo narrativo · LA LÍNEA DE TIEMPO
   El guion es una lista de momentos (beats) con clips anclados. Cada clip empieza en un ancla (el inicio del momento,
   o el inicio/fin de otro clip) + un corrimiento; por eso lo que se dispara junto se mueve junto.
   El estado del mundo es una función del tiempo: en cada cuadro se parte de la base y se aplican, en orden, todos los
   clips que ya empezaron (un clip terminado sigue aplicando su estado final). Así se puede recorrer la línea de tiempo
   hacia adelante y hacia atrás como en un editor de video.
   Las esperas (gates) son el tiempo que se le da al usuario: en modo "en vivo" sostienen todo lo que sigue hasta que
   el usuario actúa (o salta el cortafuegos); en modo "simulado" duran lo esperado y se resuelven solas. */
'use strict';

const TRACKS = [
  { id: 'vo', name: 'Voz de Alma' },
  { id: 'fx', name: 'Sonido' },
  { id: 'amb', name: 'Música' },
  { id: 'hap', name: 'Háptica' },
  { id: 'pawn', name: 'Pawn' },
  { id: 'world', name: 'Mundo' },
  { id: 'obj', name: 'Objetos' },
  { id: 'ui', name: 'Instrucción' },
  { id: 'int', name: 'Interacción' },
];

/* ============ registro ============ */
const ACTS = [], BEATS = [], CLIPS = [], GATES = [], BYUID = new Map();
let curActDef = null, curBeatDef = null;
function act(name) { curActDef = { name, beats: [] }; ACTS.push(curActDef); }
function beatTL(uid, title, desc, at, body) {
  const b = { uid, title, desc, act: curActDef, atSpec: at, clips: [], idx: BEATS.length, isBeat: true };
  curActDef.beats.push(b); BEATS.push(b); BYUID.set(uid, b); curBeatDef = b; body(); curBeatDef = null; return b;
}
function clip(o) {
  const b = curBeatDef; let key = o.key;
  if (b.clips.some(c => c.key === key)) { let n = 2; while (b.clips.some(c => c.key === key + '#' + n)) n++; key += '#' + n; }
  o.key = key; o.beat = b; o.uid = b.uid + '/' + key; o.idx = CLIPS.length; o.atSpec = o.at ?? 0; o.endSpec = o.end || null;
  o.label = o.label || key; o.dur = o.dur ?? 0;
  b.clips.push(o); CLIPS.push(o); BYUID.set(o.uid, o); if (o.gate) GATES.push(o); return o;
}
const vo = (key, text, at = 0, o = {}) => clip({ key, track: 'vo', text, dur: voDur(text), at, label: key, ...o });
const fx = (id, at = 0, note = '', o = {}) => clip({ key: id, id, track: 'fx', at, note, label: id, ...o });
const hap = (id, at = 0, note = '', o = {}) => clip({ key: id, id, track: 'hap', at, note, label: id, ...o });
const amb = (id, at = 0, note = '') => clip({ key: id, id, track: 'amb', at, note, label: id === 'SILENCIO' ? 'Silencio' + (note ? ' · ' + note : '') : id });
function walk(key, label, from, to, dur, at, o = {}) {
  const c = clip({ key, track: 'pawn', label, dur, at, apply: k => {
    const e = o.linear ? k : ease(k); rig.position.set(lerp(from.x, to.x, e), 0, lerp(from.z, to.z, e)); rig.rotation.y = to.yaw;
    if (k < 1) camera.position.y = EYE + Math.sin(k * dur * 11) * .006 * Math.sin(k * Math.PI);
  } });
  fx('FX_WALK', [c.key, 'start', +(dur * (o.stepsAt ?? .1)).toFixed(2)], 'pasos: ' + label);
  return c;
}
function gate(key, label, expected, fw, g, at = 0) { return clip({ key, track: 'int', label, dur: expected, at, gate: { fw, ...g }, sounds: g.sounds }); }
function ghostSpan(id, color, at, end, hintText) {
  const c = clip({ key: id, track: 'ui', label: id + (hintText ? ' · "' + hintText.split('   ·')[0] + '"' : ''), at, end, hint: hintText, ghost: id, color });
  fx('FX_GHOSTAPPEAR', [c.key, 'start'], id); fx('FX_GHOSTOUT', [c.key, 'end'], id);
  return c;
}

/* referencias: "KEY" (en el mismo momento), "1.4" (un momento), "1.4/KEY" (un clip de otro momento) */
function refNode(str, beat) {
  if (BYUID.has(str)) return BYUID.get(str);
  if (beat && BYUID.has(beat.uid + '/' + str)) return BYUID.get(beat.uid + '/' + str);
  console.warn('Referencia desconocida:', str, 'en', beat && beat.uid); return beat || null;
}
function parseAt(spec, beat, self) {
  if (typeof spec === 'number') return { ref: beat && beat !== self ? beat : null, edge: 'start', off: spec };
  const [r, edge = 'end', off = 0] = spec; return { ref: refNode(r, beat), edge, off };
}
function resolveAll() {
  BEATS.forEach((b, i) => {
    b.at = b.atSpec == null ? (i ? { ref: BEATS[i - 1], edge: 'end', off: 0 } : { ref: null, edge: 'start', off: 0 }) : parseAt(b.atSpec, null, b);
  });
  CLIPS.forEach(c => {
    c.at = parseAt(c.atSpec, c.beat, c);
    c.endA = c.endSpec ? parseAt(c.endSpec, c.beat, c) : null;
    c.crossSpan = !!(c.endA && c.endA.ref && (c.endA.ref.isBeat ? c.endA.ref : c.endA.ref.beat) !== c.beat);
    if (c.help) c.helpGate = refNode(c.help, c.beat);
  });
  // quién depende de quién (para mover juntos y para mostrarlo)
  [...BEATS, ...CLIPS].forEach(n => n.kids = []);
  const link = (n, a) => { if (a && a.ref) a.ref.kids.push(n); };
  BEATS.forEach(b => link(b, b.at)); CLIPS.forEach(c => { link(c, c.at); if (c.endA) link(c, c.endA); });
}

/* ============ el horario: cuándo empieza y termina cada cosa ============ */
let EDITS = {};  // uid → { d: corrimiento (s), dur, fw, at: { ref, edge, off } }
const GL = {};   // estado vivo de las esperas: uid → { dur, resolved, how, p, ... }
const CUT = {};  // voces que el usuario cortó al actuar antes de que terminaran: uid → duración (tiempo base)
let dirty = true, TOTAL = 0, ORDER = [];
const mS = new Map(), mE = new Map(), visS = new Set(), visE = new Set();
function effAt(n) { const e = EDITS[n.uid]; if (e && e.at) { const r = e.at.ref ? BYUID.get(e.at.ref) : null; return { ref: r || null, edge: e.at.edge, off: e.at.off }; } return n.at; }
function tAnchor(a) { return a.ref ? (a.edge === 'start' ? tStart(a.ref) : tEnd(a.ref)) + a.off : a.off; }
function tStart(n) {
  if (mS.has(n)) return mS.get(n);
  if (visS.has(n)) { console.warn('Ciclo de anclas en', n.uid); return 0; }
  visS.add(n); const v = tAnchor(effAt(n)) + ((EDITS[n.uid] && EDITS[n.uid].d) || 0); visS.delete(n);
  mS.set(n, v); return v;
}
const VO_MODES = { both: 'Voz: texto + audio', text: 'Voz: solo texto', audio: 'Voz: solo audio' };
const voAudio = c => S.voMode !== 'text' && audioFor(soundIdOf(c));
function audioMeta(id) { return AUDIO[id] || AUDIO[id.replace(/_\d+$/, '')] || null; }
function textOf(c) { const e = EDITS[c.uid]; return e && e.text != null ? e.text : c.text; }
function expectedDur(c) { const e = EDITS[c.uid]; if (c.track === 'vo' && S.voMode !== 'text') { const a = AUDIO[soundIdOf(c)]; if (a && a.dur) return a.dur + .3; }
  if (c.track === 'fx' && c.id) { const a = audioMeta(c.id); if (a && a.dur) return a.dur; }
  if (e && e.dur != null) return e.dur; if (e && e.text != null && c.track === 'vo') return voDur(e.text); return c.dur; }
function fwOf(c) { const e = EDITS[c.uid]; return e && e.fw != null ? e.fw : c.gate.fw; }
function tDur(c) {
  if (CUT[c.uid] != null) return CUT[c.uid];
  if (c.endA) return Math.max(0, tAnchor(c.endA) - tStart(c));
  if (c.gate) { const g = GL[c.uid]; if (g && g.dur != null) return g.dur; }
  return expectedDur(c);
}
function tEnd(n) {
  if (mE.has(n)) return mE.get(n);
  if (visE.has(n)) { console.warn('Ciclo de anclas en', n.uid); return tStart(n); }
  visE.add(n); let v;
  if (n.isBeat) { v = tStart(n); for (const c of n.clips) if (c.track !== 'amb' && c.track !== 'fx' && !c.crossSpan && !c.help) v = Math.max(v, tEnd(c)); }
  else v = tStart(n) + tDur(n);
  visE.delete(n); mE.set(n, v); return v;
}
/* LOCATORS: marcan las partes de la obra. Cada uno está anclado a un momento (+ un corrimiento) y guarda la escala
   de la parte que termina en él (k): arrastrarlo estira o comprime proporcionalmente todo lo de esa parte, y lo que
   viene después se corre sin deformarse. Las voces con audio real no se estiran (duran lo que dura su audio). */
let LOCS = null, WARP = [];
function defaultLocs() { return ACTS.slice(1).map((a, i) => ({ id: 'act' + (i + 1), name: a.name, ref: a.beats[0].uid, off: 0, k: 1 })); }
function buildWarp() {
  const list = (LOCS || []).map(L => { const n = BYUID.get(L.ref); return n ? { L, b: n.bs + L.off } : null; }).filter(Boolean).sort((a, b) => a.b - b.b);
  let F = 0, prev = 0; WARP = [];
  for (const x of list) { if (x.b <= prev + 1e-6) { x.b = prev + 1e-3; } F += (x.b - prev) * x.L.k; WARP.push({ b: x.b, F, k: x.L.k, L: x.L, pb: prev }); prev = x.b; }
}
function warp(t) { let pb = 0, pF = 0; for (const w of WARP) { if (t <= w.b) return pF + (t - pb) * w.k; pb = w.b; pF = w.F; } return pF + (t - pb); }
function unwarp(T) { let pb = 0, pF = 0; for (const w of WARP) { if (T <= w.F) return pb + (T - pF) / w.k; pb = w.b; pF = w.F; } return pb + (T - pF); }
function kAtBase(t) { for (const w of WARP) if (t <= w.b) return w.k; return 1; }
const keepsDur = c => (c.track === 'vo' && S.voMode !== 'text' && !!(AUDIO[soundIdOf(c)] && AUDIO[soundIdOf(c)].dur)) || (c.track === 'fx' && !!c.id && !!(audioMeta(c.id) || {}).dur);
function computeSchedule() {
  mS.clear(); mE.clear();
  BEATS.forEach(b => { b.bs = tStart(b); b.be = tEnd(b); });
  CLIPS.forEach(c => { c.bs = tStart(c); c.be = tEnd(c); });
  if (!LOCS) LOCS = defaultLocs();
  buildWarp();
  BEATS.forEach(b => { b.s = warp(b.bs); b.e = warp(b.be); });
  CLIPS.forEach(c => { c.s = warp(c.bs); c.e = keepsDur(c) ? c.s + (c.be - c.bs) : warp(c.be); });
  BEATS.forEach(b => { for (const c of b.clips) if (c.track !== 'amb' && c.track !== 'fx' && !c.crossSpan && !c.help) b.e = Math.max(b.e, c.e); });
  ACTS.forEach(a => { a.s = a.beats[0].s; a.e = Math.max(...a.beats.map(b => b.e)); });
  ORDER = CLIPS.slice().sort((a, b) => a.s - b.s || a.idx - b.idx);
  TOTAL = Math.max(...BEATS.map(b => b.e));
  dirty = false;
}
function helpActive(c) { return c.s < c.helpGate.e - 1e-6; }

/* ============ el estado deseado del mundo (se arma en cada cuadro) ============ */
const W = {};
function resetW() {
  Object.assign(W, { appear: {}, pop: null, hudGlow: null, halo: null, sister: 0, hint: '', vo: null, ghost: null, bellFill: 0, sensor: 'off', sensorScale: 1, sensorKind: 'ctrl', bioOn: false, sensorPos: null, cont: 'off', hud: 0, env: [-1, 0], veil: 0,
    blob: 0, pacer: 0, pacerOn: false, pacerK: 0, heartOn: false, cell: 0, cellShape: 0, spiral: 0, lovingOn: false,
    worm: 0, orbs: 0, orbsSlottedOnly: false, beam: false, attract: false, coda: false, table: 0, draw: false, palette: false, save: false,
    strokesRot: 0, strokesScale: 1, mote: null, card: 0, results: 0, resBeam: false, resPlay: false, heartSphere: 0, bioTint: 0, stars: 0, spinFast: false, beat: null, gateHold: null,
    sr: [0, 0, 0, 0, 0], ringK: 1, ringIn: false, fish: null, hallT: { west: [0, 0], east: [0, 0] },
    shareBtns: 0, sharePress: null, bellPress: 0, travel: 0, orb: null, hallWave: 1, fishHalo: 0, drawGrow: null, pacerProg: 0, disclaimer: 0 });
}
function baseWorld() {
  voidSky.material.uniforms.uAmt.value = 0; dustMat.uniforms.uAmt.value = 0;
  { const vs = voidSky.material.uniforms; vs.uTop.value.set(lookVal('intro', 'fogTop')); vs.uHor.value.set(lookVal('intro', 'fogHor')); }   // el afuera azulado de 2.9 no se queda pegado
  hallG.visible = false; hallU.uLight.value = 0; setDoor('west', 0); setDoor('east', 0); doors.east.mat.uniforms.uCool.value = 0;
  centerTitle.material.uniforms.uR.value = 0; centerTitle.material.uniforms.uO.value = 0; hallTitle('west', 0, 0); hallTitle('east', 0, 0);
  tiles.forEach((t, i) => { setTile(i, 0, 0); t.label.material.uniforms.uR.value = 0; t.label.material.uniforms.uO.value = 0; });
  bell.visible = false; alma.visible = false; cands.forEach(c => c.visible = false);
  ringG.scale.setScalar(1); cavities.forEach((c, i) => setCavity(i, 0)); soul.material.uniforms.uGlow.value = 0; soul.visible = true;
  calib.forEach(c => c.material.opacity = 0);
  TL_TITLES.forEach(m => { m.visible = false; m.material.uniforms.uR.value = 0; m.material.uniforms.uO.value = 0; });
  rigTo(PS0); camera.position.y = EYE;
}
function applyW() {
  // texto y voz
  const hintEl = $('#hint'); if (hintEl.textContent !== W.hint) { hintEl.textContent = W.hint; hintEl.style.opacity = W.hint ? 1 : 0; }
  if (W.vo && S.voMode === 'audio' && voAudio(W.vo)) W.vo = null; // solo audio: sin subtítulo (si no hay wav, se muestra el texto igual)
  const v = $('#vo'), vid = W.vo ? W.vo.uid + '|' + textOf(W.vo) : '';
  if (v.dataset.uid !== vid) { v.dataset.uid = vid; v.hidden = !W.vo; if (W.vo) { v.querySelector('.id').textContent = W.vo.key + ' · Alma'; v.querySelector('.txt').textContent = textOf(W.vo); } }
  if (W.ghost) drawGhost(W.ghost.id, W.ghost.local, W.ghost.color); else hideGhost();
  if (bell.visible) { setBellFill(W.bellFill); setBellPress(W.bellPress, S.playing ? frameDt : 1); }
  // sensor, anillo, HUD
  sensor.visible = W.sensor !== 'off'; S.sensorOn = W.sensor === 'hand'; if (W.sensor === 'float' && W.sensorPos) sensor.position.copy(W.sensorPos); S.sensorKind = W.sensorKind; S.bioOn = W.bioOn; sensorHalo.visible = W.sensor === 'float'; S.sensorScale = W.sensorScale;  // flotando: donde lo dejó su clip; en la mano: lo mueve la mano
  applySensorOrb(W.orb, W.sensorPos || sensor.position); hallU.uWave.value = W.hallWave;
  container.visible = W.cont !== 'off'; S.inHud = W.cont === 'hud';
  { const x = clamp(W.ringK), xm = x - 1, f = W.ringIn ? 1 + 2.70158 * xm * xm * xm + 1.70158 * xm * xm : x * (1 + .25 * Math.sin(Math.PI * x)); ringG.scale.setScalar(Math.max(.001, f)); }   // el anillo se va / vuelve animado
  hallTitle('west', W.hallT.west[0], W.hallT.west[1]); hallTitle('east', W.hallT.east[0], W.hallT.east[1]);
  hudPanel.visible = W.hud > 0; if (W.hud > 0) hudPanel.scale.setScalar(Math.max(.01, W.hud));
  // entornos
  showEnv(W.env[0], W.env[1]); veilU.uAmt.value = W.veil; veilU.uVar.value = S.tw.veil;
  const e0 = envs[0].userData; e0.blob.visible = W.blob > .011; e0.blob.children.forEach((m, j, a) => m.scale.setScalar(Math.max(.01, ease(seg(W.blob, j / a.length * .45, j / a.length * .45 + .55)))));   // nace MORFEANDOSE: cada gota crece a su tiempo y se funde (Beltran, 09-30)
  S.pacerOn = W.pacerOn; S.pacerK = W.pacerK; if (!W.pacerOn) e0.pacer.children.forEach(r => { r.material.opacity = W.pacer; r.scale.setScalar(1); });
  S.heartOn = W.heartOn;
  { const hs = envs[1].userData.heart; hs.visible = W.heartSphere > .011; hs.scale.setScalar(Math.max(.01, W.heartSphere)); }   // la esfera brota recien en las instrucciones
  bioWavesU.uCol.value.setRGB(lerp(.62, 1, W.bioTint), lerp(.76, .6, W.bioTint), lerp(1, .56, W.bioTint));   // el mismo sensor: azulado en Entering, rojizo en Recognizing
  const cell = envs[2].userData.cell; cell.visible = W.cell > .011; cell.scale.setScalar(Math.max(.01, W.cell)); S.lovingOn = W.lovingOn; S.cellShape = W.cellShape;
  cell.rotation.x = W.spiral * 6; cell.position.y = EYE - .05 + W.spiral * 1.5;
  envU[2].uTravel.value = W.travel; (envs[2].userData.mids || []).forEach(m => { m.position.x = ((m.userData.x0 - W.travel + 12) % 24 + 24) % 24 - 12; });   // el viaje de Mind
  const e3 = envs[3].userData; e3.worm.forEach(w => { w.visible = W.worm > .011; w.scale.setScalar(Math.max(.01, W.worm)); });
  e3.orbs.forEach((o, k) => o.visible = k < W.orbs && (!W.orbsSlottedOnly || o.userData.state === 'slot'));
  S.beamOn = W.beam; S.attractOn = W.attract; S.coda = W.coda;
  if (!W.beam && beamLine.parent) beamLine.visible = false; // el beam solo existe en ATTRACTING
  const table = envs[4].userData.table; table.visible = W.table > 0; table.position.y = EYE - .62 - .8 + .8 * ease(W.table);
  S.drawOn = W.draw; setLeftHand(W.palette, W.save);
  const g = envs[4].userData.strokes; g.rotation.y = W.strokesRot; g.scale.setScalar(Math.max(.01, W.strokesScale)); g.visible = W.strokesScale > 0;
  if (W.mote) { mote.visible = true; const [n, k] = W.mote; mote.material.color.set(STAGES[n].color); const a = MOTE_FROM, b = cavities[n].getWorldPosition(new THREE.Vector3()); mote.position.lerpVectors(a, b, ease(k)); mote.position.y += Math.sin(k * Math.PI) * .6; }
  else mote.visible = false;
  card.visible = W.card > 0; card.material.opacity = W.card;
  STARS.visible = W.stars > 0; STARS.userData.k = W.stars;
  S.spinFast = W.spinFast; S.speaking = !!W.vo && alma.visible;   // solo Alma VISIBLE reacciona: después del último Hall las voces son omnipresentes
  applyShareBtns(); applyPacerProg(); applyDisclaimer();
}


/* ============ ESTÉTICA por parte: niebla, cielo, suelo, partículas, velo ============
   Cada parte de la obra (el inicio, el Hall y cada etapa) tiene sus perillas. Se ven en vivo, se guardan en la obra
   (timeline/main → look) y el panel sigue al cabezal: muestra las perillas de la parte que se está viendo. */
const hexOf = c => '#' + c.getHexString();
const linToHex = a => '#' + new THREE.Color(a[0], a[1], a[2]).convertLinearToSRGB().getHexString();
const hexToLin = h => { const c = new THREE.Color(h).convertSRGBToLinear(); return [c.r, c.g, c.b]; };
const LOOK_SECTIONS = [{ key: 'intro', name: 'Inicio · niebla azul' }, { key: 'hall', name: 'Hall' }, ...STAGES.map((st, i) => ({ key: 'st' + i, name: 'Etapa ' + (i + 1) + ' · ' + st.name, stage: i }))];
const LOOK_PARAMS = {
  intro: [['fogTop', 'Niebla arriba', 'color'], ['fogHor', 'Niebla horizonte', 'color'], ['fogBright', 'Brillo de la niebla', 'range', 0, 2, .05], ['dustColor', 'Partículas: color', 'color'], ['dustAmt', 'Partículas: cantidad de luz', 'range', 0, 3, .05], ['dustSize', 'Partículas: tamaño', 'range', .3, 3, .05]],
  hall: [['warm', 'Luz del interior', 'color'], ['bright', 'Intensidad', 'range', .2, 2, .05], ['dustColor', 'Partículas: color', 'color'], ['dustAmt', 'Partículas: cantidad de luz', 'range', 0, 3, .05], ['dustSize', 'Partículas: tamaño', 'range', .3, 3, .05]],
  st: [['skyTop', 'Cielo arriba', 'color'], ['skyHor', 'Cielo horizonte', 'color'], ['skyBright', 'Brillo del cielo', 'range', 0, 2, .05], ['ground', 'Suelo: tinte', 'color'], ['dustColor', 'Partículas: color', 'color'], ['dustAmt', 'Partículas: cantidad de luz', 'range', 0, 3, .05], ['dustSize', 'Partículas: tamaño', 'range', .3, 3, .05], ['veilTop', 'Velo de entrada: arriba', 'color'], ['veilHor', 'Velo de entrada: horizonte', 'color']],
};
let LOOK = {}, LOOK_DEF = {}, lookSec = 'intro', lookFollow = true;
const paramsOf = key => LOOK_PARAMS[key.startsWith('st') ? 'st' : key];
function captureLookDefaults() {
  const vs = voidSky.material.uniforms;
  LOOK_DEF.intro = { fogTop: hexOf(vs.uTop.value), fogHor: hexOf(vs.uHor.value), fogBright: 1, dustColor: hexOf(dustMat.uniforms.uTint.value), dustAmt: 1, dustSize: 1 };
  LOOK_DEF.hall = { warm: hexOf(hallU.uWarm.value), bright: 1, dustColor: hexOf(dustMat.uniforms.uTint.value), dustAmt: 1, dustSize: 1 };
  STAGES.forEach((st, i) => { const su = envs[i].userData.sky.material.uniforms;
    LOOK_DEF['st' + i] = { skyTop: hexOf(su.uTop.value), skyHor: hexOf(su.uHor.value), skyBright: 1, ground: '#ffffff', dustColor: hexOf(dustMat.uniforms.uTint.value), dustAmt: 1, dustSize: 1, veilTop: linToHex(st.top), veilHor: linToHex(st.hor) }; });
}
const lookVal = (sec, p) => (LOOK[sec] && LOOK[sec][p] != null) ? LOOK[sec][p] : LOOK_DEF[sec][p];
const _dust = {};
/* lo que no cambia cuadro a cuadro se aplica solo cuando se toca una perilla */
function applyLookStatic() {
  const vs = voidSky.material.uniforms; vs.uTop.value.set(lookVal('intro', 'fogTop')); vs.uHor.value.set(lookVal('intro', 'fogHor'));
  hallU.uWarm.value.set(lookVal('hall', 'warm'));
  STAGES.forEach((st, i) => { const k = 'st' + i, su = envs[i].userData.sky.material.uniforms;
    su.uTop.value.set(lookVal(k, 'skyTop')); su.uHor.value.set(lookVal(k, 'skyHor')); envU[i].uGround.value.set(lookVal(k, 'ground'));
    st.top = hexToLin(lookVal(k, 'veilTop')); st.hor = hexToLin(lookVal(k, 'veilHor')); });
  LOOK_SECTIONS.forEach(s => { _dust[s.key] = new THREE.Color(lookVal(s.key, 'dustColor')); });
}
function currentSection() { if (W.env[0] >= 0) return 'st' + W.env[0]; if (hallG.visible && hallU.uLight.value > .05) return 'hall'; return 'intro'; }
/* cada cuadro, después de evaluar la línea de tiempo */
function applyLookFrame() {
  const sec = currentSection();
  voidSky.material.uniforms.uBright.value = lookVal('intro', 'fogBright');
  STAGES.forEach((st, i) => envs[i].userData.sky.material.uniforms.uBright.value = lookVal('st' + i, 'skyBright'));
  hallU.uLight.value *= lookVal('hall', 'bright');
  dustMat.uniforms.uAmt.value *= lookVal(sec, 'dustAmt'); dustMat.uniforms.uSize.value = lookVal(sec, 'dustSize');
  dustMat.uniforms.uTint.value.copy(_dust[sec]);
  if (lookFollow && sec !== lookSec && !$('#explore').hidden) { lookSec = sec; renderLook(); }
}
function renderLook() {
  const box = $('#look'); if (!box) return;
  const sel = `<label class="wide">Parte <select id="look_sec">${LOOK_SECTIONS.map(s => `<option value="${s.key}"${s.key === lookSec ? ' selected' : ''}>${s.name}</option>`).join('')}</select></label>
    <label class="chk"><input id="look_follow" type="checkbox"${lookFollow ? ' checked' : ''}> Seguir al cabezal</label>`;
  const rows = paramsOf(lookSec).map(([p, lab, type, mn, mx, st]) => {
    const v = lookVal(lookSec, p), ed = LOOK[lookSec] && LOOK[lookSec][p] != null;
    return type === 'color' ? `<label class="lk">${lab}${ed ? ' ✎' : ''}<input type="color" data-lk="${p}" value="${v}"></label>`
      : `<label class="lk rg">${lab}${ed ? ' ✎' : ''}<output>${(+v).toFixed(2)}</output><input type="range" data-lk="${p}" min="${mn}" max="${mx}" step="${st}" value="${v}"></label>`;
  }).join('');
  box.innerHTML = sel + rows + `<button id="look_reset">Volver a lo original en esta parte</button>`;
  $('#look_sec').onchange = e => { lookSec = e.target.value; lookFollow = false; renderLook(); const s = LOOK_SECTIONS.find(x => x.key === lookSec); if (s && s.stage != null) { const b = BYUID.get((s.stage + 1) + '.R2'); b && seek(b.s + 2); } };
  $('#look_follow').onchange = e => { lookFollow = e.target.checked; };
  box.querySelectorAll('[data-lk]').forEach(inp => inp.oninput = () => {
    const p = inp.dataset.lk, v = inp.type === 'range' ? +inp.value : inp.value; (LOOK[lookSec] || (LOOK[lookSec] = {}))[p] = v;
    if (inp.type === 'range') inp.previousElementSibling.textContent = (+v).toFixed(2);
    applyLookStatic(); scheduleSave();
  });
  $('#look_reset').onclick = () => { delete LOOK[lookSec]; applyLookStatic(); renderLook(); scheduleSave(); };
}

/* ============ evaluar el tiempo t ============ */
let prevT = null;
function fireStart(c) {
  const sid = soundIdOf(c);
  if (c.track === 'vo') { if (!(S.voMode !== 'text' && startVoice(c.uid, sid, 0, envOf(c)))) speak(textOf(c)); }
  else if (c.track === 'fx' && sid && audioFor(sid)) { cue('fx', c.id, c.note || '', true); startVoice(c.uid, sid, 0, envOf(c)); }
  else if (c.track === 'amb') { cue('amb', c.id, c.note || '', true); setAmbient(c.id, 0, finOf(c)); }
  else if (c.track === 'fx' || c.track === 'hap' || c.track === 'amb') { if (c.id) cue(c.track, c.id, c.note || ''); }
  if (c.vfx) cue('vfx', c.vfx);
  c.onStart && c.onStart(c);
}
function evaluate(t) {
  resetW(); baseWorld();
  const cross = S.playing && prevT != null && t >= prevT && t - prevT < 2;
  for (const c of ORDER) {
    if (c.s > t + 1e-9) break;
    if (c.simOnly && S.live) continue;
    if (c.help && !helpActive(c)) continue;
    if (c.when && !c.when()) continue;   // rama (p. ej. SHARE / DON'T SHARE): el clip existe en la línea pero no actúa
    const local = t - c.s, dur = c.e - c.s, k = dur > 0 ? clamp(local / dur) : 1;
    if (c.gate) { const g = S.live ? GL[c.uid] : null; c.gate.visual && c.gate.visual(k, local, c, g); if (g && !g.resolved && local >= expectedDur(c)) W.gateHold = c; }
    c.apply && c.apply(k, local, c);
    if (local < dur) {
      if (c.ghost) W.ghost = { id: c.ghost, local, color: c.color };
      if (c.hint) W.hint = c.hint;
      if (c.track === 'vo') W.vo = c;
      c.during && c.during(local, c, cross ? prevT - c.s : null);
    }
    if (cross) {
      if (prevT < c.s) fireStart(c);
      if (c.fire) for (const [ft, fn] of c.fire) if (prevT - c.s < ft && ft <= local) fn();
      if (c.onEnd && dur > 0 && prevT < c.e && c.e <= t) c.onEnd(c);
    }
  }
  for (let i = BEATS.length - 1; i >= 0; i--) if (BEATS[i].s <= t + 1e-9) { W.beat = BEATS[i]; break; }
  applyW(); applyLookFrame();
}

/* esperas en vivo: el usuario resuelve, o el cortafuegos; mientras tanto, todo lo que sigue espera */
function tickGates(t) {
  for (const c of GATES) {
    if (c.s > t || prevT == null || prevT >= c.e) continue;
    let g = GL[c.uid]; if (g && g.resolved) continue;
    if (!g) g = GL[c.uid] = { resolved: false, dur: null, p: 0 };
    const local = t - c.s, exp = expectedDur(c), fw = fwOf(c) * kAtBase(c.bs);
    const kk = kAtBase(c.bs);
    if (c.gate.tick && c.gate.tick(local, g)) { g.resolved = true; g.how = 'usuario'; g.dur = local / kk; c.gate.onUser && c.gate.onUser(g); dirty = true; cutPlayingVoices(t); }
    else if (local >= fw) { g.resolved = true; g.how = 'cortafuegos'; g.dur = fw / kk; cue('vfx', 'CORTAFUEGOS', c.label + ' · ' + fw + ' s'); c.gate.onFire && c.gate.onFire(g); dirty = true; }
    else if (local >= exp * kk) { g.dur = local / kk + 1e-3; dirty = true; }
    else if (g.dur != null) { g.dur = null; dirty = true; }
  }
}
/* el usuario hizo lo que se le pedía antes de que Alma terminara de hablar: la voz se va en fundido y lo que
   seguía se adelanta (el clip se acorta hasta ahí). Solo en vivo. */
const CUT_FADE = .5;
function cutPlayingVoices(t) {
  let any = false;
  for (const c of ORDER) {
    if (c.s > t) break; if (c.track !== 'vo' || t >= c.e - CUT_FADE) continue; if (c.help && !helpActive(c)) continue; if (c.when && !c.when()) continue;
    CUT[c.uid] = Math.max(.05, (t - c.s) / kAtBase(c.bs) + CUT_FADE); stopVoice(c.uid, CUT_FADE); any = true;
  }
  if (any) { hush(); dirty = true; cue('vfx', 'la voz se va en fundido', 'el usuario ya actuó'); }
}
function resolveHeldGate() { // el botón "Resolver espera": como si el usuario hubiera actuado
  if (dirty) computeSchedule();
  const c = GATES.find(c => c.s <= S.t && S.t < c.e); if (!c) return false;
  const g = GL[c.uid] || (GL[c.uid] = { p: 1 }); g.resolved = true; g.how = 'saltada'; g.dur = Math.max(0, S.t - c.s) / kAtBase(c.bs); g.p = 1;
  c.gate.onFire && c.gate.onFire(g); dirty = true; if (S.live) cutPlayingVoices(S.t); return true;
}

/* ============ audios reales: cada sonido de la obra (VO, FX, AMB) puede tener su archivo ============
   Se guardan en la obra: el archivo va como asset (envuelto en JSON, porque los assets no aceptan audio directo)
   y la base guarda qué asset corresponde a cada ID (colección `audio`, un documento por ID). Si un ID no tiene
   archivo, suena el marcador sintético. Al reemplazar un archivo, todas las apariciones de ese ID usan el nuevo. */
const AUDIO = {};            // ID → { asset, name, dur, bytes, buf, loading, local }
let assetsCap = null;
const voices = new Map();    // voces que suenan ahora (se cortan al pausar o saltar)
let realOut = null;
function soundIdOf(c) { if (c.track === 'vo') return c.key.replace(/#\d+$/, ''); if (c.track === 'fx' || c.track === 'amb') return c.id || null; return null; }
function audioFor(id) { if (!id) return null; const a = AUDIO[id] || AUDIO[id.replace(/_\d+$/, '')]; return a && a.buf ? a : null; }
function knownIds() {
  const s = new Set(Object.keys(FXSYN).concat(Object.keys(AMB)));
  CLIPS.forEach(c => { const id = soundIdOf(c); if (id && id !== 'SILENCIO') s.add(id); (c.sounds || []).forEach(x => expandSound(x).forEach(i => s.add(i))); }); return s;
}
const expandSound = x => /^FX_ORB_\*$/.test(x) ? Array.from({ length: 20 }, (_, i) => 'FX_ORB_' + (i + 1)) : [x];
function out() { audioOn(); if (!realOut) { realOut = AC.createGain(); realOut.gain.value = 1; realOut.connect(AC.destination); } return realOut; }
/* fundidos: fin = entrada; fout = salida al final del audio. Dos voces que se pisan se cruzan solas (crossfade
   del largo de la superposición). Un ambiente nuevo entra en su fundido mientras el anterior sale en el mismo tiempo. */
function finOf(c) { const e = EDITS[c.uid]; if (e && e.fin != null) return e.fin; return c.track === 'amb' ? (c.id === 'SILENCIO' ? 6 : 3) : 0; }
function foutOf(c) { const e = EDITS[c.uid]; return e && e.fout != null ? e.fout : 0; }
function audioNeighbor(c, dir) {
  const i = ORDER.indexOf(c); for (let j = i + dir; j >= 0 && j < ORDER.length; j += dir) { const o = ORDER[j]; if (o.track !== c.track) continue; if (o.help && !helpActive(o)) continue; if (audioFor(soundIdOf(o))) return o; }
  return null;
}
function envOf(c) {
  const a = audioFor(soundIdOf(c)); if (!a) return {}; const dur = a.buf.duration;
  let fin = finOf(c), fout = foutOf(c), foutAt = fout > 0 ? dur - fout : null, foutDur = fout;
  if (c.track === 'vo') {
    const nx = audioNeighbor(c, 1); if (nx && nx.s < c.s + dur) { const ov = c.s + dur - nx.s; foutAt = nx.s - c.s; foutDur = Math.max(ov, fout); }
    const pv = audioNeighbor(c, -1), pa = pv && audioFor(soundIdOf(pv)); if (pa && c.s < pv.s + pa.buf.duration) fin = Math.max(fin, pv.s + pa.buf.duration - c.s);
  }
  return { fin, foutAt, foutDur };
}
function startVoice(key, id, offset = 0, opts = {}) {
  const a = audioFor(id); if (!a || !S.sound) return false; const o = out();
  stopVoice(key, .03);
  const dur = a.buf.duration, off = opts.loop ? offset % dur : offset; if (!opts.loop && off >= dur - .02) return true;
  const src = AC.createBufferSource(); src.buffer = a.buf; src.loop = !!opts.loop; src.playbackRate.value = S.speed;
  const g = AC.createGain(), t = AC.currentTime, r = S.speed, fin = Math.max(.015, opts.fin ?? opts.fade ?? .015);
  const gIn = offset < fin ? offset / fin : 1;
  let gNow = gIn;
  if (opts.foutAt != null && opts.foutDur > 0 && offset > opts.foutAt) gNow = Math.min(gIn, clamp(1 - (offset - opts.foutAt) / opts.foutDur));
  g.gain.setValueAtTime(gNow, t);
  if (offset < fin) g.gain.linearRampToValueAtTime(1, t + (fin - offset) / r);
  if (opts.foutAt != null && opts.foutDur > 0) {
    const a0 = (opts.foutAt - offset) / r, a1 = (opts.foutAt + opts.foutDur - offset) / r;
    if (a0 > 0) g.gain.setValueAtTime(1, t + Math.max(a0, offset < fin ? (fin - offset) / r : 0));
    if (a1 > 0) g.gain.linearRampToValueAtTime(0, t + a1);
  }
  src.connect(g); g.connect(o); src.start(t, Math.max(0, off));
  const v = { src, g }; src.onended = () => { if (voices.get(key) === v) voices.delete(key); }; voices.set(key, v); return true;
}
function stopVoice(key, fade = .08) {
  const v = voices.get(key); if (!v) return; voices.delete(key); const t = AC.currentTime;
  v.g.gain.cancelScheduledValues(t); v.g.gain.setValueAtTime(v.g.gain.value, t); v.g.gain.linearRampToValueAtTime(0, t + fade); try { v.src.stop(t + fade + .02); } catch (e) {}
}
function stopAllVoices(fade = .08) { [...voices.keys()].forEach(k => stopVoice(k, fade)); }
/* lo que llaman los marcadores (cue) de world.js */
function playSoundId(id) { return startVoice('fx:' + id + ':' + Math.random().toString(36).slice(2, 6), id, 0); }
function setAmbient(id, offset = 0, fade = 3) {
  if (!S.sound || !AC) return; fade = Math.max(.05, fade);
  if (id && audioFor(id)) { stopVoice('amb', Math.max(.05, fade - offset)); ambient(null, fade); startVoice('amb', id, offset, { loop: true, fin: fade }); }
  else { stopVoice('amb', fade); ambient(id && AMB[id] ? id : null, fade); }
}
/* al dar play o saltar: suena lo que corresponde a ese instante, desde el punto justo */
function syncAudio() {
  stopAllVoices(.05); hush();
  if (!S.playing || !S.sound) { if (AC) ambient(null, .3); return; }
  let ac = null; for (const c of ORDER) { if (c.s > S.t) break; if (c.track === 'amb') ac = c; }
  setAmbient(ac ? ac.id : null, ac ? S.t - ac.s : 0, ac ? Math.max(.6, finOf(ac)) : .6);
  for (const c of ORDER) {
    if (c.s > S.t) break; if (c.track !== 'vo' && c.track !== 'fx') continue; if (c.track === 'vo' && S.voMode === 'text') continue; if (c.simOnly && S.live) continue; if (c.help && !helpActive(c)) continue;
    const a = audioFor(soundIdOf(c)); if (!a) continue; const off = S.t - c.s; if (off > .03 && off < a.buf.duration) startVoice(c.uid, soundIdOf(c), off, envOf(c));
  }
}

/* ---------- empaquetar y subir ---------- */
function b64FromBytes(u8) { let s = ''; for (let i = 0; i < u8.length; i += 0x8000) s += String.fromCharCode.apply(null, u8.subarray(i, i + 0x8000)); return btoa(s); }
function bytesFromB64(b) { const s = atob(b), u8 = new Uint8Array(s.length); for (let i = 0; i < s.length; i++) u8[i] = s.charCodeAt(i); return u8; }
/* si el archivo es muy grande para un asset (20 MB con el envoltorio), se pasa a WAV mono 16 bits de menor frecuencia */
function wavFrom(buf, rate) {
  const n = Math.floor(buf.duration * rate), ch = buf.numberOfChannels, src = [...Array(ch)].map((_, c) => buf.getChannelData(c)), ratio = buf.sampleRate / rate;
  const out = new DataView(new ArrayBuffer(44 + n * 2)); const w = (o, s) => [...s].forEach((c, i) => out.setUint8(o + i, c.charCodeAt(0)));
  w(0, 'RIFF'); out.setUint32(4, 36 + n * 2, true); w(8, 'WAVEfmt '); out.setUint32(16, 16, true); out.setUint16(20, 1, true); out.setUint16(22, 1, true);
  out.setUint32(24, rate, true); out.setUint32(28, rate * 2, true); out.setUint16(32, 2, true); out.setUint16(34, 16, true); w(36, 'data'); out.setUint32(40, n * 2, true);
  for (let i = 0; i < n; i++) { let v = 0; const j = Math.min(src[0].length - 1, Math.floor(i * ratio)); for (let c = 0; c < ch; c++) v += src[c][j]; v = clamp(v / ch, -1, 1); out.setInt16(44 + i * 2, v * 32767, true); }
  return new Uint8Array(out.buffer);
}
async function packAudio(file, buf) {
  let bytes = new Uint8Array(await file.arrayBuffer()), mime = file.type || 'audio/*', note = '';
  if (bytes.length > 14.5e6) { for (const r of [32000, 22050, 16000]) { bytes = wavFrom(buf, r); mime = 'audio/wav'; note = `pasado a WAV mono ${r / 1000} kHz por tamaño`; if (bytes.length < 14.5e6) break; } }
  return { json: JSON.stringify({ format: 'sc-audio-v1', name: file.name, mime, b64: b64FromBytes(bytes) }), note };
}
function isAudioFile(f) { return /^audio\//.test(f.type) || /\.(wav|mp3|ogg|oga|opus|m4a|aac|flac|webm)$/i.test(f.name); }
async function assignAudio(id, file) {
  if (!isAudioFile(file)) { toast(file.name + ' no es un archivo de audio.'); return false; }
  audioOn(); let buf;
  try { buf = await AC.decodeAudioData((await file.arrayBuffer()).slice(0)); } catch (e) { toast('No pude leer ' + file.name + ' como audio.'); return false; }
  const prev = AUDIO[id];
  AUDIO[id] = { name: file.name, dur: buf.duration, bytes: file.size, buf, local: true };
  if (assetsCap && db) {
    try {
      const { json, note } = await packAudio(file, buf);
      const r = await assetsCap.upload(new Blob([json], { type: 'application/json' }), { type: 'application/json' });
      AUDIO[id].asset = r.id; AUDIO[id].local = false;
      await db.doc('audio/' + id).set({ id, asset: r.id, name: file.name, dur: +buf.duration.toFixed(3), bytes: file.size, note, at: Date.now() });
      if (prev && prev.asset && prev.asset !== r.id && !assetInUse(prev.asset, id)) assetsCap.delete(prev.asset).catch(() => {}); // el archivo anterior ya no lo usa nadie
    } catch (e) { toast('No se pudo guardar ' + file.name + ' en la obra (' + (e && e.code || 'error') + '): suena solo en esta sesión.'); }
  }
  audioChanged(id); autoSound(); return true;
}
async function removeAudio(id) {
  const a = AUDIO[id]; if (!a) return; delete AUDIO[id];
  if (db) { try { await db.doc('audio/' + id).delete(); } catch (e) {} }
  if (a.asset && assetsCap && !assetInUse(a.asset, id)) assetsCap.delete(a.asset).catch(() => {});
  audioChanged(id);
}
/* muchos audios llegan juntos al abrir: se repinta una sola vez por tanda, no una vez por audio */
let audioChangedTimer = 0; const audioChangedIds = new Set();
function audioChanged(id) {
  dirty = true; audioChangedIds.add(id); clearTimeout(audioChangedTimer);
  audioChangedTimer = setTimeout(() => {
    const ids = new Set(audioChangedIds); audioChangedIds.clear();
    CLIPS.forEach(c => { if (ids.has(soundIdOf(c))) paintClip(c); });
    if (UI.expanded) { layout(); renderInspector(); } if (S.playing) syncAudio();
    audioStatus();
  }, 250);
}
function setSound(on, byUser) {
  if (byUser) S.soundUserOff = !on;
  audioOn(); S.sound = on; $('#b_sound').textContent = 'Sonido: ' + (on ? 'encendido' : 'apagado'); $('#b_sound').classList.toggle('on', on);
  if (!on) { ambient(null, .5); stopAllVoices(.2); } else syncAudio();
}
function autoSound() { if (!S.sound && !S.soundUserOff && Object.keys(AUDIO).length) setSound(true); }
function audioStatus() { const n = Object.keys(AUDIO).length, k = knownIds().size; $('#b_audio').textContent = `Audios ${n}/${k}`; }
/* varios archivos a la vez: cada uno va al ID que dice su nombre (FX_DOOROPEN.wav → FX_DOOROPEN) */
function idFromName(name, ids) {
  const up = new Map([...ids].map(id => [id.toUpperCase(), id])); // VO_01a y vo_01A son el mismo
  let b = name.replace(/\.[^.]+$/, '').trim().toUpperCase().replace(/[\s-]+/g, '_');
  for (let i = 0; i < 3; i++) { if (up.has(b)) return up.get(b); b = b.replace(/(_?\(\d+\)|_(V\d+|FINAL|MASTER|MIX|EDIT|OK))$/, ''); }
  return up.get(b) || null;
}
async function assignFiles(files) {
  const ids = knownIds(), list = [...files].filter(isAudioFile), missing = [];
  let done = 0;
  for (const f of list) { const id = idFromName(f.name, ids); if (!id) { missing.push(f.name); continue; } setStatus(`Subiendo audios ${++done}/${list.length}…`); await assignAudio(id, f); }
  setStatus(db ? 'Guardado' : 'Guardado en este navegador');
  if (missing.length) toast(`No encontré a qué sonido corresponde${missing.length > 1 ? 'n' : ''}: ${missing.join(', ')}. Ponle al archivo el ID del clip (ej. FX_DOOROPEN.wav) o arrástralo sobre el clip.`);
  else if (done) toast(done === 1 ? 'Audio cargado.' : `${done} audios cargados.`);
}
/* cargar desde la obra (y escuchar cambios: si se sube un audio desde otra ventana, aparece aquí) */
const BUNDLES = new Map(); let decodeQueue = Promise.resolve();
function fetchAsset(asset) { if (!BUNDLES.has(asset)) BUNDLES.set(asset, fetch('/_blob/' + asset).then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })); return BUNDLES.get(asset); }
const assetInUse = (asset, exceptId) => Object.entries(AUDIO).some(([k, v]) => k !== exceptId && v.asset === asset);
async function loadAudioDoc(d) {
  const id = d.id, a = AUDIO[id]; if (a && a.asset === d.asset && (a.part || null) === (d.part || null) && (a.buf || a.loading)) return;
  AUDIO[id] = { asset: d.asset, part: d.part || null, name: d.name, dur: d.dur, bytes: d.bytes }; dirty = true; audioStatus();
  const e = AUDIO[id];
  e.loading = fetchAsset(d.asset)
    .then(j => (decodeQueue = decodeQueue.catch(() => {}).then(() => new Promise(r => setTimeout(r, 0))).then(() => { const it = d.part ? j.items[d.part] : j; audioOn(); return AC.decodeAudioData(bytesFromB64(it.b64).buffer); })))
    .then(buf => { if (AUDIO[id] !== e) return; e.buf = buf; e.dur = buf.duration; audioChanged(id); autoSound(); })
    .catch(() => { e.err = true; });
  return e.loading;
}
async function initAudio() {
  audioStatus();
  if (!window.claude || typeof window.claude.use !== 'function') return;
  try { assetsCap = await window.claude.use('assets'); } catch (e) { assetsCap = null; }
  if (!db) return;
  try {
    db.collection('audio').onSnapshot(snap => {
      const seen = new Set();
      snap.docs.forEach(doc => { const d = doc.data(); if (!d || !d.asset) return; seen.add(doc.id); loadAudioDoc({ ...d, id: doc.id }); });
      Object.keys(AUDIO).forEach(id => { if (!seen.has(id) && !AUDIO[id].local) { delete AUDIO[id]; audioChanged(id); } });
    }, () => {});
  } catch (e) {}
}

/* ============ transporte ============ */
function seek(t) {
  if (dirty) computeSchedule();
  t = clamp(t, 0, TOTAL);
  for (const c of GATES) if (GL[c.uid] && t < c.e) { delete GL[c.uid]; dirty = true; }
  for (const uid in CUT) { const c = BYUID.get(uid); if (!c || t < c.e + .01) { delete CUT[uid]; dirty = true; } }
  for (const c of CLIPS) if (c.reset && t < c.s) c.reset();
  S.t = t; prevT = S.playing ? t - 1e-4 : null; hush(); S.lastStep = -1;
  if (dirty) computeSchedule(); if (S.playing) syncAudio(); else stopAllVoices(.05);
  if (UI.expanded && !UI.scrubbing) { const sc = $('#tl-scroll'), x = HEAD + t * UI.pxs; if (x < sc.scrollLeft + HEAD || x > sc.scrollLeft + sc.clientWidth - 40) sc.scrollLeft = x - HEAD - 80; }
}
function setPlaying(p) {
  S.playing = p; prevT = p ? S.t - 1e-4 : null; if (dirty) computeSchedule(); syncAudio();
  $('#b_play').textContent = p ? 'Pausa' : 'Play'; $('#b_play').classList.toggle('on', p);
}
function togglePlay() { if (!S.started) startPiece(false); if (S.t >= TOTAL - .01) seek(0); setPlaying(!S.playing); }

/* ============ el editor ============ */
const HEAD = 124, LANE = 20, ROWPAD = 5, RULER = 22, LOCROW = 22, ACTROW = 18, BEATROW = 24;
const UI = { pxs: 12, sel: null, expanded: false, h: Math.round(innerHeight * .56), snap: true, follow: true, lanesFrozen: false, rows: {}, els: new Map(), beatEls: new Map() };
const undoStack = [], redoStack = [];
function snapshot() { return JSON.stringify({ E: EDITS, L: LOCS }); }
function pushUndo(snap) { undoStack.push(snap); if (undoStack.length > 120) undoStack.shift(); redoStack.length = 0; }
function restore(json) { const j = JSON.parse(json); EDITS = j.E || {}; LOCS = j.L || null; dirty = true; computeSchedule(); refreshTitles(); layout(); renderInspector(); scheduleSave(); }
function refreshTitles() { CLIPS.forEach(paintClip); }
function undo() { if (!undoStack.length) return; redoStack.push(snapshot()); restore(undoStack.pop()); }
function redo() { if (!redoStack.length) return; undoStack.push(snapshot()); restore(redoStack.pop()); }
function edit(uid) { return EDITS[uid] || (EDITS[uid] = {}); }
function cleanEdit(uid) { const e = EDITS[uid]; if (!e) return; if (e.d != null && Math.abs(e.d) < 1e-4) delete e.d; if (!Object.keys(e).length) delete EDITS[uid]; }

const fmt = s => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;
const fmtP = s => `${Math.floor(s / 60)}:${(s % 60).toFixed(1).padStart(4, '0')}`;
const trackOf = id => TRACKS.findIndex(t => t.id === id);
function ambEnd(c) { const nx = ORDER.find(o => o.track === 'amb' && o.s > c.s + 1e-6); return nx ? nx.s : TOTAL; }
function labelPx(c) { return 16 + c.label.length * 6.1; }

function buildEditor() {
  const heads = $('#tl-heads'), layer = $('#tl-layer'); heads.innerHTML = ''; layer.innerHTML = '';
  // filas fijas: actos, momentos
  const hL = document.createElement('div'); hL.className = 'hd sub'; hL.innerHTML = 'Locators <button id="b_addloc" title="Agregar un locator donde está el cabezal">+</button>'; heads.appendChild(hL); UI.hL = hL;
  const hA = document.createElement('div'); hA.className = 'hd sub'; hA.textContent = 'Actos'; heads.appendChild(hA); UI.hA = hA;
  UI.locLayer = document.createElement('div'); UI.locLayer.id = 'tl-locs'; layer.appendChild(UI.locLayer);
  const hB = document.createElement('div'); hB.className = 'hd sub'; hB.textContent = 'Momentos'; heads.appendChild(hB); UI.hB = hB;
  UI.trackHeads = TRACKS.map(t => { const d = document.createElement('div'); d.className = 'hd t-' + t.id; d.textContent = t.name; heads.appendChild(d); return d; });
  UI.trackBgs = TRACKS.map((t, i) => { const d = document.createElement('div'); d.className = 'rowbg' + (i % 2 ? ' odd' : ''); layer.appendChild(d); return d; });
  UI.actEls = ACTS.map(a => { const d = document.createElement('div'); d.className = 'actblk'; d.innerHTML = `<span>${a.name}</span>`; d.onclick = () => { seek(a.s); }; layer.appendChild(d); return d; });
  BEATS.forEach(b => { const d = document.createElement('div'); d.className = 'beatblk'; d.dataset.uid = b.uid; d.innerHTML = `<span><b>${b.uid}</b> ${b.title}</span>`; d.title = b.title + '\n' + (b.desc || ''); layer.appendChild(d); UI.beatEls.set(b, d); });
  CLIPS.forEach(c => {
    const d = document.createElement('div'); d.dataset.uid = c.uid;
    if (c.sounds && c.sounds.length && !c.label.includes('♫')) c.label += ' ♫';
    d.className = 'clip t-' + c.track + (c.gate ? ' gate' : '') + (c.help ? ' help' : '') + (c.simOnly ? ' simonly' : '') + (c.endA ? ' span' : '');
    d.innerHTML = `<span></span>` + (!c.endA && c.track !== 'amb' ? '<i class="rz" title="Arrastra para cambiar la duración"></i>' : '') + (c.gate ? '<i class="fw" title="Cortafuegos"></i>' : '') + (c.track === 'amb' ? '' : '') + (c.track === 'fx' || c.track === 'amb' ? '<i class="tail"></i>' : '') + (c.track === 'fx' || c.track === 'amb' || c.track === 'vo' ? '<i class="fi"></i><i class="fo"></i>' : '');
    layer.appendChild(d); UI.els.set(c, d); paintClip(c);
  });
  const ph = document.createElement('div'); ph.id = 'tl-ph'; layer.appendChild(ph);
  setTimeout(bindLocs, 0);
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg'); svg.id = 'tl-links'; layer.appendChild(svg);
  bindEditorEvents();
}
function paintClip(c) { const d = UI.els.get(c); if (!d) return; const sp = d.querySelector('span'); const esc = x => String(x).replace(/&/g, '&amp;').replace(/</g, '&lt;');
  sp.innerHTML = c.track === 'vo' ? `<b>${esc(c.key)}</b> ${esc(textOf(c))}` : esc(c.label); d.title = clipTitle(c); d.classList.toggle('edited', !!(c.track === 'vo' && EDITS[c.uid] && EDITS[c.uid].text != null));
  const sid = soundIdOf(c), a = sid && AUDIO[sid]; d.classList.toggle('has-audio', !!a); if (a) d.title += `\nAudio: ${a.name} · ${(a.dur || 0).toFixed(1)} s`; }
function clipTitle(c) {
  const kinds = { vo: 'Voz', fx: 'Sonido', amb: 'Música', hap: 'Háptica', pawn: 'Pawn', world: 'Mundo', obj: 'Objeto', ui: 'Instrucción', int: 'Interacción' };
  return `${c.label}\n${kinds[c.track]}${c.gate ? ' · espera del usuario' : ''}${c.help ? ' · solo si el usuario tarda' : ''}${c.simOnly ? ' · en vivo lo dispara el usuario' : ''}${c.text ? '\n“' + textOf(c) + '”' : ''}${c.note ? '\n' + c.note : ''}`;
}

/* reparte los clips de cada pista en carriles para que no se tapen */
function computeLanes() {
  UI.lane = new Map(); UI.laneCount = TRACKS.map(() => 1);
  TRACKS.forEach((t, ti) => {
    const list = CLIPS.filter(c => c.track === t.id).sort((a, b) => a.s - b.s || a.idx - b.idx), ends = [];
    list.forEach(c => {
      const x0 = c.s * UI.pxs, x1 = c.track === 'amb' ? ambEnd(c) * UI.pxs - 1 : Math.max(c.e * UI.pxs, x0 + (c.e - c.s < .05 ? labelPx(c) : 18)) + 3;
      let l = ends.findIndex(e => e <= x0); if (l < 0) { l = ends.length; ends.push(0); } ends[l] = x1; UI.lane.set(c, l);
    });
    UI.laneCount[ti] = Math.max(1, ends.length);
  });
  UI.beatLane = new Map(); const bEnds = [];
  BEATS.slice().sort((a, b) => a.s - b.s || a.idx - b.idx).forEach(b => {
    const x0 = b.s * UI.pxs, x1 = Math.max(b.e * UI.pxs, x0 + 14 + (b.uid.length + b.title.length) * 6.2) + 2;
    let l = bEnds.findIndex(e => e <= x0 + .5); if (l < 0) { l = bEnds.length; bEnds.push(0); } bEnds[l] = x1; UI.beatLane.set(b, l);
  });
  UI.beatLanes = Math.max(1, bEnds.length);
}
function layout() {
  if (dirty) computeSchedule();
  if (!UI.lanesFrozen) computeLanes();
  const W_ = TOTAL * UI.pxs + 240;
  $('#tl-rows').style.width = $('#tl-ruler').style.width = (HEAD + W_) + 'px';
  let y = 0;
  UI.hL.style.height = LOCROW + 'px'; UI.rowLocs = y; y += LOCROW;
  UI.hA.style.height = ACTROW + 'px'; UI.rowActs = y; y += ACTROW;
  const bh = UI.beatLanes * BEATROW + 4; UI.hB.style.height = bh + 'px'; UI.rowBeats = y; y += bh;
  UI.rowY = TRACKS.map((t, i) => { const h = UI.laneCount[i] * LANE + ROWPAD * 2; UI.trackHeads[i].style.height = h + 'px'; const bg = UI.trackBgs[i]; bg.style.top = y + 'px'; bg.style.height = h + 'px'; bg.style.width = W_ + 'px'; const r = y; y += h; return r; });
  UI.H = y; $('#tl-rows').style.height = y + 'px'; $('#tl-ph').style.height = y + 'px';
  $('#tl-links').setAttribute('width', W_); $('#tl-links').setAttribute('height', y);
  ACTS.forEach((a, i) => { const d = UI.actEls[i]; d.style.left = a.s * UI.pxs + 'px'; d.style.width = Math.max(2, (a.e - a.s) * UI.pxs - 2) + 'px'; d.style.top = UI.rowActs + 'px'; });
  place(); buildRuler(); drawLinks(); updateSelClasses();
}
function place() {
  BEATS.forEach(b => { const d = UI.beatEls.get(b); d.style.left = b.s * UI.pxs + 'px'; d.style.width = Math.max(3, (b.e - b.s) * UI.pxs - 1) + 'px'; d.style.top = (UI.rowBeats + 2 + (UI.beatLane.get(b) || 0) * BEATROW) + 'px'; });
  CLIPS.forEach(c => {
    const d = UI.els.get(c), ti = trackOf(c.track), inst = c.track !== 'amb' && c.e - c.s < .05;
    d.classList.toggle('inst', inst);
    d.style.left = c.s * UI.pxs + 'px'; d.style.width = inst ? labelPx(c) + 'px' : Math.max(4, ((c.track === 'amb' ? ambEnd(c) : c.e) - c.s) * UI.pxs) + 'px';
    d.style.top = (UI.rowY[ti] + ROWPAD + UI.lane.get(c) * LANE) + 'px';
    if (c.help) d.classList.toggle('off', !helpActive(c));
    if (c.gate) { const fwx = fwOf(c) * kAtBase(c.bs) * UI.pxs; const f = d.querySelector('.fw'); f.style.left = fwx + 'px'; }
    const tail = d.querySelector('.tail'), a = AUDIO[soundIdOf(c)];
    let len = 0; if (c.track === 'amb') len = ambEnd(c) - c.s; else if (inst && a && a.dur) len = a.dur;
    if (tail) tail.style.width = (c.track === 'amb' ? 0 : len * UI.pxs) + 'px';
    const fi = d.querySelector('.fi'), fo = d.querySelector('.fo');
    if (fi) { const fin = c.track === 'amb' || a ? finOf(c) : 0, fout = a ? foutOf(c) : 0, w = inst ? len : (c.e - c.s);
      fi.style.width = Math.min(fin, w || fin) * UI.pxs + 'px'; fo.style.width = Math.min(fout, w) * UI.pxs + 'px'; fo.style.left = Math.max(0, (w - fout)) * UI.pxs + 'px'; }
  });
  $('#tt').textContent = '~' + fmt(TOTAL);
  buildMini(); placeLocs();
}
function placeLocs() {
  const box = UI.locLayer; if (!box) return; box.innerHTML = ''; const H = UI.H || 400;
  let pF = 0;
  WARP.forEach((w, i) => {
    const x = w.F * UI.pxs, sel = UI.sel && UI.sel.isLoc && UI.sel.L === w.L;
    const line = document.createElement('div'); line.className = 'locline' + (sel ? ' sel' : ''); line.style.left = x + 'px'; line.style.height = H + 'px'; box.appendChild(line);
    const m = document.createElement('div'); m.className = 'loc' + (sel ? ' sel' : ''); m.style.left = x + 'px'; m.style.top = (UI.rowLocs + 2) + 'px'; m.dataset.i = i;
    m.innerHTML = `<span>${w.L.name.replace(/</g, '&lt;')}</span>`; m.title = w.L.name + '\nArrastra: estira o comprime la parte anterior. Doble clic: renombrar.'; box.appendChild(m);
    if (Math.abs(w.k - 1) > .005) { const sc = document.createElement('div'); sc.className = 'locscale'; sc.style.left = (pF * UI.pxs) + 'px'; sc.style.width = Math.max(0, x - pF * UI.pxs) + 'px'; sc.style.top = (UI.rowLocs + 2) + 'px';
      sc.innerHTML = `<span>${w.k > 1 ? '↔' : '→←'} ${Math.round(w.k * 100)} %</span>`; box.appendChild(sc); }
    pF = w.F;
  });
}
function addLocatorAt(T) {
  if (dirty) computeSchedule(); const bb = unwarp(T);
  let beat = BEATS[0]; for (const b of BEATS) if (b.bs <= bb + 1e-6 && b.bs >= beat.bs) beat = b;
  const s0 = snapshot(), k = kAtBase(bb), n = LOCS.filter(L => /^Locator/.test(L.name)).length + 1;
  const L = { id: 'L' + Date.now().toString(36), name: 'Locator ' + n, ref: beat.uid, off: +(bb - beat.bs).toFixed(3), k };
  LOCS.push(L); pushUndo(s0); dirty = true; layout(); select({ isLoc: true, L }); scheduleSave();
}
function bindLocs() {
  UI.locLayer.onpointerdown = e => {
    const m = e.target.closest('.loc'); if (!m || e.button !== 0) return; e.preventDefault(); e.stopPropagation();
    const w = WARP[+m.dataset.i], L = w.L, i = +m.dataset.i, pF = i ? WARP[i - 1].F : 0, span = w.b - w.pb, x0 = e.clientX, F0 = w.F, snap0 = snapshot(); let moved = false;
    select({ isLoc: true, L });
    const cands = [S.t, ...BEATS.map(b => b.s)];
    try { UI.locLayer.setPointerCapture(e.pointerId); } catch (_) {}
    const mv = ev => { const dx = ev.clientX - x0; if (!moved && Math.abs(dx) < 3) return; moved = true;
      const F = Math.max(pF + .2, snapT(F0 + dx / UI.pxs, cands)); L.k = +clamp((F - pF) / span, .1, 10).toFixed(4); dirty = true; computeSchedule(); place(); drawLinks(); renderInspector(); };
    const up = () => { UI.locLayer.removeEventListener('pointermove', mv); UI.locLayer.removeEventListener('pointerup', up); if (moved) { pushUndo(snap0); layout(); scheduleSave(); } };
    UI.locLayer.addEventListener('pointermove', mv); UI.locLayer.addEventListener('pointerup', up);
  };
  UI.locLayer.ondblclick = e => { const m = e.target.closest('.loc'); if (!m) return; const L = WARP[+m.dataset.i].L; const v = prompt('Nombre del locator', L.name); if (v && v.trim()) { const s0 = snapshot(); L.name = v.trim(); pushUndo(s0); placeLocs(); renderInspector(); scheduleSave(); } };
  $('#b_addloc').onclick = e => { e.stopPropagation(); addLocatorAt(S.t); };
}
function buildRuler() {
  const r = $('#tl-ticks'); r.innerHTML = '';
  const steps = [1, 2, 5, 10, 15, 30, 60, 120], step = steps.find(s => s * UI.pxs >= 64) || 120;
  for (let t = 0; t <= TOTAL + step; t += step) { const d = document.createElement('div'); d.className = 'tick'; d.style.left = (HEAD + t * UI.pxs) + 'px'; d.textContent = fmt(t); r.appendChild(d); }
}
function buildMini() {
  const box = $('#track .acts'); if (box.childElementCount !== ACTS.length) { box.innerHTML = ''; ACTS.forEach(a => { const d = document.createElement('div'); d.className = 'seg'; d.title = a.name; d.innerHTML = `<span>${a.name.replace(/^(Acto|Etapa) /, '')}</span>`; d.onclick = e => { e.stopPropagation(); if (!S.started) startPiece(false); seek(a.s); if (!S.playing) setPlaying(true); }; box.appendChild(d); }); }
  ACTS.forEach((a, i) => box.children[i].style.flex = Math.max(.1, a.e - a.s));
}

/* familia de un nodo: todo lo que se mueve con él */
function family(n, out = new Set()) { for (const k of n.kids) if (!out.has(k)) { out.add(k); family(k, out); } return out; }
function parentOf(n) { const a = effAt(n); return a.ref; }
function updateSelClasses() {
  UI.els.forEach(d => d.classList.remove('sel', 'kid', 'par')); UI.beatEls.forEach(d => d.classList.remove('sel', 'kid', 'par'));
  const n = UI.sel; if (!n || n.isLoc) return;
  const el = n.isBeat ? UI.beatEls.get(n) : UI.els.get(n); el && el.classList.add('sel');
  family(n).forEach(k => { const e = k.isBeat ? UI.beatEls.get(k) : UI.els.get(k); e && e.classList.add('kid'); });
  const p = parentOf(n); if (p) { const e = p.isBeat ? UI.beatEls.get(p) : UI.els.get(p); e && e.classList.add('par'); }
}
function nodeY(n) { if (n.isBeat) return UI.rowBeats + 2 + (UI.beatLane.get(n) || 0) * BEATROW + BEATROW / 2 - 2; return UI.rowY[trackOf(n.track)] + ROWPAD + UI.lane.get(n) * LANE + LANE / 2 - 1; }
function drawLinks() {
  const svg = $('#tl-links'); svg.innerHTML = ''; const n = UI.sel; if (!n || n.isLoc) return;
  const line = (a, b, cls) => { const p = document.createElementNS(svg.namespaceURI, 'path'); const x1 = a[0], y1 = a[1], x2 = b[0], y2 = b[1], mx = (x1 + x2) / 2;
    p.setAttribute('d', `M${x1},${y1} C${mx},${y1} ${mx},${y2} ${x2},${y2}`); p.setAttribute('class', cls); svg.appendChild(p); };
  const anchorPt = (m) => { const a = effAt(m); if (!a.ref) return null; const r = a.ref; return [(a.edge === 'start' ? r.s : r.e) * UI.pxs, nodeY(r)]; };
  const pa = anchorPt(n); if (pa) line(pa, [n.s * UI.pxs, nodeY(n)], 'par');
  n.kids.forEach(k => { if (k.isBeat && k !== n) return; const p = anchorPt(k); if (p) line(p, [k.s * UI.pxs, nodeY(k)], 'kid'); });
}

/* ---------- interacción con el editor ---------- */
function xToT(clientX) { const r = $('#tl-layer').getBoundingClientRect(); return (clientX - r.left) / UI.pxs; }
function select(n) { UI.sel = n; updateSelClasses(); drawLinks(); renderInspector(); placeLocs(); }
function snapCands(n) {
  const fam = family(n); fam.add(n); const out = [S.t];
  const later = b => b.idx > (n.isBeat ? n.idx : n.beat.idx);
  CLIPS.forEach(c => { if (fam.has(c) || later(c.beat)) return; out.push(c.s, c.e); });
  BEATS.forEach(b => { if (!fam.has(b) && !later(b)) out.push(b.s, b.e); });
  return out;
}
function snapT(t, cands, alsoLen = 0) {
  if (!UI.snap) return t; const th = 8 / UI.pxs; let best = t, bd = th;
  for (const c of cands) { const d1 = Math.abs(c - t); if (d1 < bd) { bd = d1; best = c; } if (alsoLen) { const d2 = Math.abs(c - (t + alsoLen)); if (d2 < bd) { bd = d2; best = c - alsoLen; } } }
  return best;
}
function bindEditorEvents() {
  const layer = $('#tl-layer');
  layer.onpointerdown = e => {
    if (e.button !== 0) return; e.preventDefault();
    const clipEl = e.target.closest('.clip'), beatEl = e.target.closest('.beatblk');
    if (!clipEl && !beatEl) { if (!e.target.closest('.actblk')) select(null); return; }
    const n = BYUID.get((clipEl || beatEl).dataset.uid); select(n);
    const resize = !!e.target.closest('.rz') && !n.isBeat;
    const x0 = e.clientX, snap0 = snapshot(), s0 = n.s, d0 = (EDITS[n.uid] && EDITS[n.uid].d) || 0, dur0 = n.isBeat ? 0 : (n.gate ? expectedDur(n) : n.be - n.bs), kk = kAtBase(n.bs);
    const cands = snapCands(n); let moved = false; UI.lanesFrozen = true;
    try { layer.setPointerCapture(e.pointerId); } catch (_) {}
    const mv = ev => {
      const dx = ev.clientX - x0; if (!moved && Math.abs(dx) < 3) return; moved = true;
      if (resize) { let nd = Math.max(.1, dur0 + dx / UI.pxs / kk); const endT = snapT(s0 + nd * kk, cands); nd = Math.max(.1, (endT - s0) / kk); edit(n.uid).dur = +nd.toFixed(3); }
      else { const len = n.e - n.s; const ns = snapT(s0 + dx / UI.pxs, cands, len); edit(n.uid).d = +(d0 + (ns - s0) / kk).toFixed(3); cleanEdit(n.uid); }
      dirty = true; computeSchedule(); place(); drawLinks(); renderInspector(true);
    };
    const up = () => { layer.removeEventListener('pointermove', mv); layer.removeEventListener('pointerup', up); layer.removeEventListener('pointercancel', up); UI.lanesFrozen = false;
      if (moved) { pushUndo(snap0); layout(); scheduleSave(); } };
    layer.addEventListener('pointermove', mv); layer.addEventListener('pointerup', up); layer.addEventListener('pointercancel', up);
  };
  layer.addEventListener('mousedown', e => { if (e.detail > 1) e.preventDefault(); });
  layer.ondblclick = e => { const s = getSelection(); s && s.removeAllRanges(); const el = e.target.closest('.clip, .beatblk'); if (!el) return; const n = BYUID.get(el.dataset.uid); seek(n.s); };
  // botón del medio (la rueda): arrastrar la vista del timeline en cualquier dirección
  const sc = $('#tl-scroll');
  sc.addEventListener('mousedown', e => { if (e.button === 1) e.preventDefault(); });
  sc.addEventListener('auxclick', e => { if (e.button === 1) e.preventDefault(); });
  sc.addEventListener('pointerdown', e => {
    if (e.button !== 1) return; e.preventDefault(); e.stopPropagation();
    const x0 = e.clientX, y0 = e.clientY, l0 = sc.scrollLeft, t0 = sc.scrollTop; sc.classList.add('panning'); try { sc.setPointerCapture(e.pointerId); } catch (_) {}
    const mv = ev => { sc.scrollLeft = l0 - (ev.clientX - x0); sc.scrollTop = t0 - (ev.clientY - y0); };
    const up = () => { sc.classList.remove('panning'); sc.removeEventListener('pointermove', mv); sc.removeEventListener('pointerup', up); sc.removeEventListener('pointercancel', up); };
    sc.addEventListener('pointermove', mv); sc.addEventListener('pointerup', up); sc.addEventListener('pointercancel', up);
  }, true);
  // la regla: clic o arrastre = mover el cabezal
  const ruler = $('#tl-ruler');
  ruler.onpointerdown = e => { if (e.button !== 0) return; e.preventDefault(); if (!S.started) startPiece(false); const was = S.playing; if (was) setPlaying(false); UI.scrubbing = true; seek(xToT(e.clientX)); try { ruler.setPointerCapture(e.pointerId); } catch (_) {}
    const mv = ev => seek(xToT(ev.clientX)); const up = () => { UI.scrubbing = false; ruler.removeEventListener('pointermove', mv); ruler.removeEventListener('pointerup', up); if (was) setPlaying(true); };
    ruler.addEventListener('pointermove', mv); ruler.addEventListener('pointerup', up); };
  // zoom con ctrl + rueda, alrededor del mouse
  $('#tl-scroll').addEventListener('wheel', e => { if (!e.ctrlKey && !e.altKey) return; e.preventDefault(); const t = xToT(e.clientX); zoomTo(UI.pxs * (e.deltaY < 0 ? 1.18 : 1 / 1.18), t, e.clientX); }, { passive: false });
}
function zoomTo(pxs, aroundT, clientX) {
  const sc = $('#tl-scroll'); const r = sc.getBoundingClientRect(); const cx = clientX != null ? clientX - r.left : sc.clientWidth / 2;
  if (aroundT == null) aroundT = (sc.scrollLeft + cx - HEAD) / UI.pxs;
  UI.pxs = clamp(pxs, .6, 200); layout(); sc.scrollLeft = HEAD + aroundT * UI.pxs - cx;
}
function fitAll() { const sc = $('#tl-scroll'); UI.pxs = clamp((sc.clientWidth - HEAD - 30) / TOTAL, .6, 200); layout(); sc.scrollLeft = 0; }

/* ---------- inspector ---------- */
function anchorOptions(n) {
  const opts = [];
  if (n.isBeat) { opts.push({ v: '', l: 'Fin del momento anterior' }); return opts; }
  const fam = family(n); const b = n.beat;
  opts.push({ v: b.uid + '|start', l: 'Inicio del momento ' + b.uid });
  b.clips.forEach(c => { if (c === n || fam.has(c)) return; opts.push({ v: c.uid + '|start', l: 'Inicio de ' + c.label }); opts.push({ v: c.uid + '|end', l: 'Fin de ' + c.label }); });
  const a = effAt(n); if (a.ref && !b.clips.includes(a.ref) && a.ref !== b) { opts.push({ v: a.ref.uid + '|' + a.edge, l: (a.edge === 'start' ? 'Inicio de ' : 'Fin de ') + (a.ref.label || a.ref.title) + ' (otro momento)' }); }
  return opts;
}
function voNow(n) { const a = AUDIO[soundIdOf(n)]; if (S.voMode === 'text' || !a) return 'Ahora suena: el texto' + (S.voice ? ' (voz sintética)' : ' (subtítulo)') + '.'; return S.voMode === 'audio' ? 'Ahora suena: el audio, sin subtítulo.' : 'Ahora suena: el audio, con este texto como subtítulo.'; }
function soundsBlock(n) {
  if (!n.sounds || !n.sounds.length) return '';
  const esc = x => String(x).replace(/&/g, '&amp;').replace(/</g, '&lt;');
  const rows = n.sounds.map(x => { const ids = expandSound(x);
    if (ids.length > 1) { const k = ids.filter(i => AUDIO[i]).length; return `<div class="snd"><b>FX_ORB_1 … FX_ORB_20</b><span>una por esfera · ${k}/20 con archivo</span></div>`; }
    const a = AUDIO[x]; return `<div class="snd"><b>${esc(x)}</b><span>${a ? '♪ ' + esc(a.name) + ' · ' + (a.dur || 0).toFixed(1) + ' s' : 'sin archivo'}</span>${a ? `<button data-snd-play="${esc(x)}">Escuchar</button>` : ''}<button data-snd-load="${esc(x)}">${a ? 'Reemplazar' : 'Cargar'}</button></div>`; }).join('');
  return `<div class="aud"><b>Sonidos de esta interacción</b><span class="meta">Suenan cuando el usuario actúa, no en un momento fijo; por eso no son clips. Cárgales el audio aquí.</span>${rows}</div>`;
}
function bindSoundsBlock(box) {
  box.querySelectorAll('[data-snd-play]').forEach(b => b.onclick = () => { audioOn(); const was = S.sound; S.sound = true; startVoice('preview', b.dataset.sndPlay, 0); S.sound = was; });
  box.querySelectorAll('[data-snd-load]').forEach(b => b.onclick = () => { const id = b.dataset.sndLoad, inp = $('#audio-one');
    inp.onchange = async () => { const f = inp.files[0]; inp.value = ''; if (f) { setStatus('Subiendo audio…'); await assignAudio(id, f); setStatus(db ? 'Guardado' : 'Guardado en este navegador'); renderInspector(); } }; inp.click(); });
}
function audioBlock(n) {
  const sid = soundIdOf(n); if (!sid || sid === 'SILENCIO') return soundsBlock(n);
  const a = AUDIO[sid], esc = x => String(x).replace(/&/g, '&amp;').replace(/</g, '&lt;');
  const uses = CLIPS.filter(c => soundIdOf(c) === sid).length;
  return `<div class="aud"><b>Audio ${esc(sid)}</b>` + (a ? `<span>${esc(a.name)} · ${(a.dur || 0).toFixed(1)} s${a.buf ? '' : ' · cargando…'}${a.local ? ' · solo en esta sesión' : ''}</span>` : `<span>Sin archivo: suena un marcador sintético.</span>`) +
    (n.track === 'amb' ? `<label>Fundido de entrada <input data-f="fin" type="number" step="0.5" min="0" value="${finOf(n)}"> s</label><span class="meta">Es el crossfade: el ambiente anterior sale en el mismo tiempo.</span>` :
      `<label>Fundido de entrada <input data-f="fin" type="number" step="0.1" min="0" value="${finOf(n)}"> s</label><label>Fundido de salida <input data-f="fout" type="number" step="0.1" min="0" value="${foutOf(n)}"> s</label>` + (n.track === 'vo' ? `<span class="meta">Si dos voces se pisan, se cruzan solas en la parte que comparten.</span>` : '')) +
    `<div class="row">${a ? '<button data-au="play">Escuchar</button>' : ''}<button data-au="load">${a ? 'Reemplazar' : 'Cargar audio'}</button>${a ? '<button data-au="del">Quitar</button>' : ''}</div>` +
    `<span class="meta">${uses > 1 ? `Este sonido se usa en ${uses} clips: el archivo vale para todos. ` : ''}También puedes arrastrar el archivo sobre el clip.</span></div>`;
}
function bindAudioBlock(box, n) {
  const sid = soundIdOf(n); if (!sid) return;
  box.querySelectorAll('button[data-au]').forEach(b => b.onclick = async () => {
    if (b.dataset.au === 'play') { audioOn(); const was = S.sound; S.sound = true; if (voices.has('preview')) stopVoice('preview'); else startVoice('preview', sid, 0); S.sound = was; }
    if (b.dataset.au === 'load') { const inp = $('#audio-one'); inp.onchange = async () => { const f = inp.files[0]; inp.value = ''; if (f) { setStatus('Subiendo audio…'); await assignAudio(sid, f); setStatus(db ? 'Guardado' : 'Guardado en este navegador'); } }; inp.click(); }
    if (b.dataset.au === 'del') { if (confirm('¿Quitar el audio de ' + sid + '? Vuelve a sonar el marcador sintético.')) removeAudio(sid); }
  });
}
function renderInspector(soft) {
  const box = $('#tl-insp'); const n = UI.sel;
  if (soft && n && !n.isLoc && box.dataset.uid === n.uid) { const s = box.querySelector('[data-f=start]'), d = box.querySelector('[data-f=dur]'); if (s && document.activeElement !== s) s.value = n.s.toFixed(2); if (d && document.activeElement !== d) d.value = (n.gate ? expectedDur(n) : n.e - n.s).toFixed(2); return; }
  box.dataset.uid = n ? (n.uid || '') : '';
  if (!n) { box.innerHTML = `<h4>Cómo se usa</h4><ul>
    <li><b>Arrastra</b> un clip para moverlo: lo que está anclado a él se mueve con él (se ve en color). El borde derecho cambia la duración.</li>
    <li>Arrastra un <b>momento</b> (la franja de arriba) para correr el momento entero y todo lo que viene después.</li>
    <li><b>Clic en la regla</b> o arrastrar: mover el cabezal. <b>Doble clic</b> en un clip: ir a su inicio.</li>
    <li><kbd>Espacio</kbd> play · <kbd>←</kbd><kbd>→</kbd> mueve el clip elegido 0,1 s (<kbd>Shift</kbd> 1 s) · <kbd>Ctrl</kbd>+rueda: zoom · <kbd>Ctrl</kbd>+<kbd>Z</kbd> deshacer.</li>
    <li>Las <b>esperas</b> (rayadas) son el tiempo del usuario. En vivo sostienen la obra hasta que actúas; la marca roja es el cortafuegos.</li>
    <li>Los clips punteados son <b>ayudas</b>: solo suenan si el usuario tarda más que ese punto.</li>
    <li><b>Audios</b>: suelta archivos sobre la ventana (van al ID que dice su nombre, ej. <kbd>FX_DOOROPEN.wav</kbd>) o sobre un clip. ♪ = el clip ya tiene su archivo; una voz con audio dura lo que dura el audio.</li></ul>`; return; }
  const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;');
  if (n.isLoc) {
    const L = n.L, w = WARP.find(x => x.L === L), i = WARP.indexOf(w), prevName = i > 0 ? WARP[i - 1].L.name : 'el inicio';
    box.dataset.uid = 'loc:' + L.id;
    box.innerHTML = `<h4>${esc(L.name)}</h4><p class="meta">Locator · en el momento ${esc(L.ref)}${L.off ? ' + ' + L.off.toFixed(1) + ' s' : ''} · ${w ? fmtP(w.F) : ''}</p>
      <label class="wide">Nombre <input data-l="name" type="text" value="${esc(L.name)}"></label>
      <label>Escala de la parte anterior <input data-l="k" type="number" step="5" min="10" max="1000" value="${Math.round(L.k * 100)}"> %</label>
      <p class="meta">Desde ${esc(prevName)} hasta aquí: ${w ? ((w.b - w.pb)).toFixed(1) + ' s originales → ' + ((w.b - w.pb) * L.k).toFixed(1) + ' s' : ''}. Arrastra el locator para estirar o comprimir esa parte; lo que viene después se corre.</p>
      <div class="row"><button data-l="go">Ir aquí</button><button data-l="one">Volver a 100 %</button><button data-l="del">Borrar locator</button></div>`;
    box.querySelector('[data-l=name]').onchange = ev => { const s0 = snapshot(); L.name = ev.target.value.trim() || L.name; pushUndo(s0); placeLocs(); scheduleSave(); };
    box.querySelector('[data-l=k]').onchange = ev => { const v = parseFloat(ev.target.value); if (!isFinite(v)) return; const s0 = snapshot(); L.k = clamp(v / 100, .1, 10); pushUndo(s0); dirty = true; layout(); renderInspector(); scheduleSave(); };
    box.querySelector('[data-l=go]').onclick = () => w && seek(w.F);
    box.querySelector('[data-l=one]').onclick = () => { const s0 = snapshot(); L.k = 1; pushUndo(s0); dirty = true; layout(); renderInspector(); scheduleSave(); };
    box.querySelector('[data-l=del]').onclick = () => { const s0 = snapshot(); LOCS = LOCS.filter(x => x !== L); pushUndo(s0); dirty = true; select(null); layout(); scheduleSave(); };
    return;
  }
  if (n.isBeat) {
    box.innerHTML = `<h4>${esc(n.uid)} · ${esc(n.title)}</h4><p class="desc">${esc(n.desc || '')}</p>
      <label>Empieza <input data-f="start" type="number" step="0.1" value="${n.s.toFixed(2)}"> s</label>
      <p class="meta">Dura ${(n.e - n.s).toFixed(1)} s · ${n.clips.length} clips · ${n.act.name}</p>
      <button data-a="reset">Volver al original</button>`;
  } else {
    const a = effAt(n), cur = a.ref ? a.ref.uid + '|' + a.edge : '';
    const kids = [...family(n)].filter(k => !k.isBeat);
    const durField = n.endA ? `<p class="meta">Dura hasta ${esc(n.endA.ref.label || n.endA.ref.title)} (${(n.e - n.s).toFixed(1)} s)</p>` :
      `<label>${n.gate ? 'Tiempo esperado del usuario' : 'Duración'} <input data-f="dur" type="number" step="0.1" min="0" value="${(n.gate ? expectedDur(n) : n.e - n.s).toFixed(2)}"> s</label>`;
    box.innerHTML = `<h4>${esc(n.label)}</h4>
      <p class="meta">${esc(n.uid)} · ${TRACKS[trackOf(n.track)].name}${n.gate ? ' · espera' : ''}${n.help ? ' · ayuda' : ''}</p>
      ${n.track === 'vo' ? `<label class="wide">Texto de Alma${EDITS[n.uid] && EDITS[n.uid].text != null ? ' <em>(editado)</em>' : ''}<textarea data-f="text" rows="4" spellcheck="false">${esc(textOf(n))}</textarea></label><p class="meta">${voNow(n)} Duración estimada con este texto: ${voDur(textOf(n)).toFixed(1)} s${EDITS[n.uid] && EDITS[n.uid].dur != null ? ' (fijaste la duración a mano)' : ''}. Se guarda al salir del cuadro o con Ctrl+Enter.</p>${EDITS[n.uid] && EDITS[n.uid].text != null ? `<p class="meta">Original: “${esc(n.text)}”</p>` : ''}` : ''}${n.note ? `<p class="desc">${esc(n.note)}</p>` : ''}
      ${audioBlock(n)}
      <label>Empieza <input data-f="start" type="number" step="0.1" value="${n.s.toFixed(2)}"> s</label>
      ${durField}
      ${n.gate ? `<label>Cortafuegos <input data-f="fw" type="number" step="1" min="1" value="${fwOf(n)}"> s</label>` : ''}
      <label class="wide">Anclado a <select data-f="at">${anchorOptions(n).map(o => `<option value="${esc(o.v)}"${o.v === cur ? ' selected' : ''}>${esc(o.l)}</option>`).join('')}</select></label>
      <p class="meta">${kids.length ? `Se mueven con este clip (${kids.length}): ${kids.slice(0, 8).map(k => esc(k.label)).join(', ')}${kids.length > 8 ? '…' : ''}` : 'Nada está anclado a este clip.'}</p>
      <div class="row"><button data-a="go">Ir aquí</button><button data-a="reset">Volver al original</button></div>`;
  }
  box.querySelectorAll('input[data-f]').forEach(inp => inp.onchange = () => {
    const v = parseFloat(inp.value); if (!isFinite(v)) return; const snap0 = snapshot(), f = inp.dataset.f;
    if (f === 'start') { const e = edit(n.uid); e.d = +(((e.d || 0) + (v - n.s) / kAtBase(n.bs))).toFixed(3); cleanEdit(n.uid); }
    if (f === 'dur') edit(n.uid).dur = Math.max(0, v);
    if (f === 'fw') edit(n.uid).fw = Math.max(1, v);
    if (f === 'fin') edit(n.uid).fin = Math.max(0, v);
    if (f === 'fout') edit(n.uid).fout = Math.max(0, v);
    pushUndo(snap0); dirty = true; layout(); renderInspector(); scheduleSave();
  });
  bindAudioBlock(box, n); bindSoundsBlock(box);
  const ta = box.querySelector('textarea[data-f=text]');
  if (ta) { const commit = () => { const v = ta.value.trim(); const cur = textOf(n); if (v === cur) return; const snap0 = snapshot();
      if (!v || v === n.text) { const e = EDITS[n.uid]; if (e) { delete e.text; cleanEdit(n.uid); } } else edit(n.uid).text = v;
      pushUndo(snap0); dirty = true; paintClip(n); layout(); renderInspector(); scheduleSave(); };
    ta.onchange = commit; ta.onkeydown = e => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); commit(); } }; }
  const sel = box.querySelector('select[data-f=at]');
  if (sel) sel.onchange = () => {
    const snap0 = snapshot(), [ref, edge] = sel.value.split('|'), r = BYUID.get(ref); if (!r) return;
    const s = n.s; const e = edit(n.uid); e.at = { ref, edge, off: 0 }; delete e.d; dirty = true; computeSchedule();
    e.at.off = +(s - (edge === 'start' ? r.s : r.e)).toFixed(3); dirty = true; pushUndo(snap0); layout(); renderInspector(); scheduleSave();
  };
  box.querySelectorAll('button[data-a]').forEach(b => b.onclick = () => {
    if (b.dataset.a === 'go') { seek(n.s); return; }
    if (b.dataset.a === 'reset') { const snap0 = snapshot(); delete EDITS[n.uid]; pushUndo(snap0); dirty = true; if (!n.isBeat) paintClip(n); layout(); renderInspector(); scheduleSave(); }
  });
}

/* ---------- guardar: en la base de la obra (la ve Claude) y en este navegador ----------
   Cada cambio se escribe al instante en este navegador y, 1,2 s después del último, en la base de la obra
   (timeline/main). Al cerrar o cambiar de pestaña se escribe enseguida. Si la base quedó atrás (se cerró sin
   conexión), gana lo más nuevo. Los ajustes de clips que una versión nueva del guion ya no tiene se conservan
   aparte (no se borran). Antes del primer cambio de cada sesión se guarda una copia de respaldo (timeline/bk-…). */
const LS_KEY = 'sc-timeline-v1'; let db = null, saveTimer = 0, saving = false, again = false, pending = false, backedUp = false, loadedState = null;
let ORPHANS = [], localAt = 0;
function setStatus(t) { $('#tl-status').textContent = t; }
function editsArray() { return Object.entries(EDITS).map(([uid, e]) => ({ uid, ...e })).concat(ORPHANS); }
function editsFromArray(arr) { const o = {}; ORPHANS = []; (arr || []).forEach(x => { const { uid, ...e } = x; if (BYUID.has(uid)) o[uid] = e; else ORPHANS.push(x); }); return o; }
function planSummary() {
  if (dirty) computeSchedule();
  return { total: +TOTAL.toFixed(1), locators: WARP.map(w => [w.L.name, +w.F.toFixed(2), +w.k.toFixed(3)]), beats: BEATS.map(b => [b.uid, +b.s.toFixed(2), +b.e.toFixed(2)]),
    edited: Object.keys(EDITS).map(uid => { const n = BYUID.get(uid); const r = [uid, n.label || n.title, +n.s.toFixed(2), +(n.e - n.s).toFixed(2)]; if (EDITS[uid].text != null) r.push(EDITS[uid].text); return r; }) };
}
const hhmm = t => new Date(t).toLocaleTimeString('es', { hour: '2-digit', minute: '2-digit' });
function scheduleSave() {
  localAt = Date.now(); pending = true;
  try { localStorage.setItem(LS_KEY, JSON.stringify({ at: localAt, edits: editsArray(), locators: LOCS, look: LOOK })); } catch (e) {}
  clearTimeout(saveTimer); setStatus(db ? 'Guardando…' : 'Guardado en este navegador'); saveTimer = setTimeout(flushSave, 1200);
}
async function flushSave() {
  clearTimeout(saveTimer); saveTimer = 0;
  if (!db) { pending = false; return; } if (saving) { again = true; return; } saving = true;
  try {
    if (!backedUp && loadedState && loadedState.edits && loadedState.edits.length) {
      const d = new Date(), id = 'bk-' + d.toISOString().slice(0, 16).replace(/[-:T]/g, '');
      await db.doc('timeline/' + id).set({ ...loadedState, backupOf: 'main', backupAt: Date.now() }).catch(() => {});
    }
    backedUp = true;
    const at = Date.now();
    await db.doc('timeline/main').set({ v: 1, savedAt: at, edits: editsArray(), locators: LOCS, look: LOOK, plan: planSummary() });
    pending = false; setStatus('Guardado ' + hhmm(at));
  } catch (e) { setStatus(e && (e.code === 'not_granted' || e.code === 'revoked') ? 'Solo lectura: queda en este navegador' : 'No se pudo guardar en la obra: queda en este navegador'); }
  saving = false; if (again) { again = false; flushSave(); }
}
function loadLocal() {
  try { const j = JSON.parse(localStorage.getItem(LS_KEY) || 'null');
    if (Array.isArray(j)) { EDITS = editsFromArray(j); localAt = 0; }
    else if (j && Array.isArray(j.edits)) { EDITS = editsFromArray(j.edits); localAt = j.at || 0; if (Array.isArray(j.locators)) LOCS = j.locators; if (j.look) LOOK = j.look; } } catch (e) {}
  dirty = true;
}
async function initDb() {
  if (!window.claude || typeof window.claude.use !== 'function') { setStatus('Guardado en este navegador'); return; }
  try { db = await window.claude.use('db'); } catch (e) { db = null; }
  if (!db) { setStatus('Guardado en este navegador'); return; }
  try {
    const snap = await db.doc('timeline/main').get();
    const d = snap.exists ? snap.data() : null;
    loadedState = d ? { v: d.v, savedAt: d.savedAt, edits: d.edits, locators: d.locators || null, look: d.look || null, plan: d.plan } : null;
    if (d && Array.isArray(d.edits) && (d.savedAt || 0) >= localAt - 2000) {
      EDITS = editsFromArray(d.edits); if (Array.isArray(d.locators)) LOCS = d.locators; if (d.look) { LOOK = JSON.parse(JSON.stringify(d.look)); applyLookStatic(); renderLook(); } dirty = true; refreshTitles(); layout(); renderInspector();
      setStatus('Guardado ' + hhmm(d.savedAt || Date.now()));
    } else if (Object.keys(EDITS).length || ORPHANS.length) {
      setStatus('Recuperando tus últimos cambios…'); scheduleSave(); // este navegador tiene algo más nuevo que la obra
    } else setStatus('Guardado');
  } catch (e) { setStatus('Sin conexión: guardado en este navegador'); }
}
// al cerrar o salir de la pestaña, lo pendiente se escribe ya
addEventListener('visibilitychange', () => { if (document.visibilityState === 'hidden' && pending) flushSave(); });
addEventListener('pagehide', () => { if (pending) flushSave(); });
addEventListener('beforeunload', e => { if (pending && db) { flushSave(); e.preventDefault(); e.returnValue = ''; } });

/* ---------- exportar / importar ---------- */
function openExport() {
  const m = $('#tl-modal'); m.hidden = false;
  const plan = planSummary();
  const lines = ['momento\tempieza\ttermina\ttítulo', ...BEATS.map(b => `${b.uid}\t${fmtP(b.s)}\t${fmtP(b.e)}\t${b.title}`)];
  $('#tl-json').value = JSON.stringify({ v: 1, edits: editsArray(), plan }, null, 1);
  $('#tl-table').value = lines.join('\n');
}
function importJson() {
  try { const j = JSON.parse($('#tl-json').value); const snap0 = snapshot(); EDITS = editsFromArray(j.edits || j); pushUndo(snap0); dirty = true; refreshTitles(); layout(); renderInspector(); scheduleSave(); $('#tl-modal').hidden = true; }
  catch (e) { alert('El texto no es un JSON válido de la línea de tiempo.'); }
}

/* ---------- panel: abrir, cerrar, alto ---------- */
function setExpanded(on) {
  UI.expanded = on; document.body.classList.toggle('tl-open', on); $('#b_tl').textContent = on ? 'Ocultar timeline' : 'Timeline';
  applyPanelHeight(); if (on) { layout(); renderInspector(); requestAnimationFrame(() => followHead(true)); }
}
function applyPanelHeight() {
  const h = UI.expanded ? clamp(UI.h, 180, innerHeight - 160) : $('#bar').offsetHeight;
  document.documentElement.style.setProperty('--tlh', h + 'px'); if (UI.expanded) $('#bar').style.height = h + 'px'; else $('#bar').style.height = '';
  resize();
}
function followHead(force) {
  if (!UI.expanded || (!UI.follow && !force)) return; const sc = $('#tl-scroll'), x = HEAD + S.t * UI.pxs;
  if (force || x < sc.scrollLeft + HEAD + 20 || x > sc.scrollLeft + sc.clientWidth - 60) sc.scrollLeft = x - HEAD - 80;
}

/* ============ simulación por cuadro ============ */
let frameDt = 0, lastNow = performance.now();
const tmp = new THREE.Vector3();
function frame(now) {
  const rdt = Math.min(.05, (now - lastNow) / 1000); lastNow = now; S.clock += rdt;
  frameDt = S.playing ? rdt * S.speed : 0;
  if (S.playing) {
    S.t = Math.min(TOTAL, S.t + frameDt);
    if (S.live) tickGates(S.t);
    if (dirty) { computeSchedule(); if (UI.expanded) place(); }
  } else if (dirty) { computeSchedule(); if (UI.expanded) place(); }
  const T = S.clock;
  // mirada
  S.yaw = lerp(S.yaw, S.targetYaw, .12); camera.rotation.set(S.pitch, S.yaw, 0, 'YXZ');
  evaluate(S.t);
  // cámara de revisión: más campo visual o unos pasos detrás de los ojos del pawn (no existe en el visor)
  { const bob = camera.position.y - EYE; camera.position.set(0, EYE + bob, 0); if (S.camBack > 0) camera.position.add(tmp.set(0, 0, S.camBack).applyEuler(camera.rotation)); }
  prevT = S.playing ? S.t : null;
  if (S.playing && S.t >= TOTAL) setPlaying(false);
  // mano: rayo del mouse a ~0,6 m
  ray.setFromCamera(S.mouse, camera); S.handPrev.copy(S.hand); S.hand.copy(ray.ray.origin).addScaledVector(ray.ray.direction, .6);
  S.handVel.subVectors(S.hand, S.handPrev).divideScalar(Math.max(rdt, 1e-3));
  const mv = S.handVel.length(); S.stillness = lerp(S.stillness, clamp(1 - mv / 1.2), .05);
  handMesh.position.copy(S.hand); handMesh.visible = !S.sensorOn;
  const cq = camera.getWorldQuaternion(new THREE.Quaternion());
  if (S.sensorOn) { sensor.position.lerp(tmp.copy(S.hand).add(V(.05, -.09, 0).applyQuaternion(cq)), .5); sensor.scale.setScalar((MODELS.ctrl ? 1 : .7) * Math.max(.01, S.sensorScale)); sensor.quaternion.copy(cq); sensor.rotateX(-.5); sensor.userData.press && sensor.userData.press(S.down ? 1 : 0); }
  else if (sensor.visible) { sensor.rotation.y += rdt * .35; sensor.scale.setScalar(Math.max(.01, S.sensorScale)); sensorHalo.scale.setScalar(1 + .08 * Math.sin(T * 3)); }
  if (BIO.live) {
    const bioNow = S.sensorOn && S.sensorKind === 'bio'; BIO.live.visible = bioNow && sensor.visible;
    if (bioNow) { sensor.visible = false; BIO.live.position.copy(sensor.position); BIO.live.quaternion.copy(cq); BIO.live.rotateX(-Math.PI / 2 + .35); BIO.live.scale.setScalar(Math.max(.01, S.sensorScale)); }
    BIO.on = lerp(BIO.on, bioNow && S.bioOn ? 1 : 0, .06); bioWavesU.uOn.value = BIO.on; bioWavesU.uT.value = T;
    BIO.live.userData.mats.forEach(m => { if (m.uniforms.uLight.value > .5) m.uniforms.uOn.value = BIO.on; });
  }
  // uniforms
  const camW = camera.getWorldPosition(tmp.set(0, 0, 0)).clone();
  dustMat.uniforms.uCam.value.copy(camW); dustMat.uniforms.uHand.value.copy(S.hand); dustMat.uniforms.uVel.value.copy(S.handVel).clampLength(0, 3); dustMat.uniforms.uT.value = T;
  voidSky.position.copy(camW); veil.position.copy(camW); voidSky.material.uniforms.uT.value = T; veilU.uT.value = T; hallU.uT.value = T;
  envU.forEach(u => u.uT.value = T);
  BLOBS.forEach(m => m.uniforms.uT.value = T);
  tickAlmaVoice(T, rdt);   // audiorreactiva suave + esfera de partículas (Beltrán 09-30)
  TL_TITLES.forEach(t => t.material.uniforms.uT.value = T); tiles.forEach(t => t.label.material.uniforms.uT.value = T); centerTitle.material.uniforms.uT.value = T; HALL_T.west.concat(HALL_T.east).forEach(m => m.material.uniforms.uT.value = T);
  tickStageRings(T); tickFish();
  // anillo
  if (container.visible) {
    ringG.rotation.z += rdt * (S.spinFast ? 3 : [0, .15, .6][S.tw.spin | 0]);
    if (S.inHud) { container.position.copy(hudWorldPos()); container.quaternion.copy(hudWorldQuat()); }
  }
  // HUD: EEG y latido
  if (hudPanel.visible) {
    for (let k = 0; k < 48; k++) { eegPts[k * 3] = k / 47 * .16; eegPts[k * 3 + 1] = Math.sin(T * 2 + k * .5) * .012 * (1.3 - S.stillness) + Math.sin(T * 5.3 + k) * .004; eegPts[k * 3 + 2] = 0; }
    eegGeo.attributes.position.needsUpdate = true; heartDot.scale.setScalar(1 + .6 * Math.exp(-((T * S.data.bpm / 60) % 1) * 8));
    if (HUD3.root) {   // HUD 3D: EEG alto en su ventana y la ameba que late a la mitad del ritmo
      for (let k = 0; k < 48; k++) { const y = Math.sin(T * 2 + k * .5) * .0085 * (1.3 - S.stillness) + Math.sin(T * 5.3 + k) * .003; HUD3.eegPts[k * 3] = -.055 + k / 47 * .11; HUD3.eegPts[k * 3 + 1] = clamp(y, -.013, .013); HUD3.eegPts[k * 3 + 2] = 0; }
      HUD3.eeg.geometry.attributes.position.needsUpdate = true;
      if (HUD3.pulse) { const u = ((T * S.data.bpm / 120) % 1) * 6, f = u * u * Math.exp(2 * (1 - u)); HUD3.pulse.scale.setScalar(1 + .2 * f); HUD3.pulseU.uGlow.value = f;
        if (HUD3.sister) { const a = W.sister, e = a < .6 ? out3(a / .6) * 1.15 : lerp(1.15, 1, inOut3((a - .6) / .4));   // la hermana nace con un pum chico y late a la mitad del ritmo
          HUD3.sister.visible = a > 0; HUD3.sister.scale.setScalar(Math.max(.001, .23 * e * (1 + .2 * f))); } }
    }
  }
  // E1 respiración
  const e0 = envs[0];
  if (e0.visible) {
    const b0 = S.breath || 0; S.breath = lerp(b0, S.down ? 1 : 0, rdt * .8); envU[0].uBreath.value = S.breath;
    // Beltrán 09-30: las lomas siempre ondulan; al exhalar el oleaje va ~3x más rápido y vuelve suave a su velocidad al inhalar/sostener
    { const dbr = (S.breath - b0) / Math.max(rdt, 1e-3), pk = S.pacerK != null ? S.pacerK : 0, exh = dbr < -.02 || (S.pacerOn && pk < (S.prevPK != null ? S.prevPK : pk) - 1e-4);
      S.prevPK = pk; S.swellK = lerp(S.swellK || 1, exh ? 3 : 1, clamp(rdt * 2.5)); envU[0].uSwellT.value += rdt * S.swellK; }
    // el aliento: inhalar (la respiración sube) trae las motas hacia la boca; exhalar las lleva afuera, espejo exacto
    const db = (S.breath - b0) / Math.max(rdt, 1e-3); aliento.u.uPhase.value -= db * rdt * .9; aliento.u.uT.value = T;
    aliento.u.uAmt.value = lerp(aliento.u.uAmt.value, clamp(Math.abs(db) * 3), .1);
    if (S.playing && Math.random() < .2) { S.data.breath.push(S.breath); if (S.data.breath.length > 200) S.data.breath.shift(); }
    e0.userData.blob.children.forEach(m => { const r = lerp(.62, .12, S.breath); m.position.set(0, Math.sin(m.userData.a + T * .4) * r * .6, Math.cos(m.userData.a + T * .3) * r); });
    if (S.pacerOn) e0.userData.pacer.children.forEach(r => { r.material.opacity = .7; r.scale.setScalar(lerp(1.4, .45, S.pacerK)); });
  }
  if (!e0.visible) aliento.u.uAmt.value = 0;
  // E3 calma
  if (envs[2].visible) {
    const calm = S.lovingOn ? S.stillness : .5; envU[2].uCalm.value = lerp(envU[2].uCalm.value, calm, .02);
    if (S.playing && S.lovingOn && Math.random() < .15) { S.data.calm.push(envU[2].uCalm.value); if (S.data.calm.length > 160) S.data.calm.shift(); }
    const c = envU[2].uCalm.value;
    envs[2].userData.cell.userData.limbs.forEach(m => { const a = m.userData.a + T * .1 + (S.cellShape || 0) * .6; const r = lerp(.75, .34, c); m.position.set(0, Math.sin(a) * r * .7, Math.cos(a) * r); m.scale.setScalar(lerp(.7, 1.15, c)); });
  }
  // E4 beam, esferas, secuenciador · E5 dibujo
  if (envs[3].visible) tickAttract(T);
  tickPalette3D(rdt);
  if (envs[4].visible && S.drawOn) { tickDraw(); tickTip(rdt); } else hideTip();
  // SAVE sostenido
  if (S.saveDown && S.playing) S.saveHeld = (S.saveHeld || 0) + frameDt;
  else if (S.saveHeld > 0 && S.saveHeld < 3) S.saveHeld = Math.max(0, S.saveHeld - frameDt * 3);
  const f = document.querySelector('#save .fill'); f && (f.style.transform = `scaleX(${clamp((S.saveHeld || 0) / 3)})`);
  if (STARS.visible) STARS.userData.mats.forEach((m, k) => m.opacity = clamp(STARS.userData.k * 21 - k) * (.6 + .4 * Math.sin(T * 2 + k)));
  tickResults(T, rdt);
  tickAppear(); tickPop(); tickHalo(T);
  renderer.render(scene, camera);
  // consola
  $('#t').textContent = fmtP(S.t); $('#tl-time').textContent = fmtP(S.t) + ' / ' + fmt(TOTAL);
  $('#track .head').style.left = `calc(${clamp(S.t / TOTAL) * 100}% - 1px)`;
  if (UI.expanded) { $('#tl-ph').style.transform = `translateX(${S.t * UI.pxs}px)`; $('#tl-rh').style.transform = `translateX(${HEAD + S.t * UI.pxs}px)`; if (S.playing) followHead(false); }
  const b = W.beat; if (b && $('#beat').dataset.uid !== b.uid) { $('#beat').dataset.uid = b.uid; $('#beat').textContent = b.uid + ' · ' + b.title; $('#beatdesc').textContent = b.desc || ''; $('#act').textContent = b.act.name; }
  const hold = W.gateHold; $('#b_skip').classList.toggle('on', !!hold); $('#b_skip').textContent = hold ? 'Resolver espera · ' + hold.label.replace(/^Espera: /, '') : 'Resolver espera';
  S.clicked = false;
  schedule();
}
// ?timer: bucle por setTimeout (vistas de prueba donde requestAnimationFrame no corre)
const TIMER = /[?&]timer/.test(location.search);
function schedule() { if (TIMER) setTimeout(() => frame(performance.now()), 16); else requestAnimationFrame(frame); }
function hudWorldPos() { hudPanel.updateMatrixWorld(true); return hudAnchor.getWorldPosition(new THREE.Vector3()); }

/* ============ controles ============ */
function startPiece(sound) {
  if (S.started) return; S.started = true; $('#intro').hidden = true;
  if (sound) { audioOn(); S.sound = true; $('#b_sound').textContent = 'Sonido: encendido'; $('#b_sound').classList.add('on'); }
}
function bindControls() {
  $('#b_play').onclick = togglePlay;
  const SPEEDS = [1, 2, 4, 8]; $('#b_speed').onclick = () => { S.speed = SPEEDS[(SPEEDS.indexOf(S.speed) + 1) % SPEEDS.length]; $('#b_speed').textContent = `Velocidad ${S.speed}×`; $('#spd').textContent = S.speed + '×'; syncAudio(); };
  $('#b_skip').onclick = () => { resolveHeldGate(); };
  $('#b_live').onclick = () => { S.live = !S.live; for (const k in GL) delete GL[k]; for (const k in CUT) delete CUT[k]; dirty = true; $('#b_live').textContent = 'Interacción: ' + (S.live ? 'en vivo' : 'simulada'); $('#b_live').classList.toggle('on', S.live); };
  $('#b_sound').onclick = () => setSound(!S.sound, true);
  // el navegador deja sonar el audio solo después de un gesto: cualquier clic o tecla en la página lo habilita
  addEventListener('pointerdown', () => audioOn(), true); addEventListener('keydown', () => audioOn(), true);
  $('#b_voice').onclick = () => { S.voice = !S.voice; $('#b_voice').textContent = 'Voz sintética: ' + (S.voice ? 'encendida' : 'apagada'); $('#b_voice').classList.toggle('on', S.voice); if (!S.voice) hush(); };
  $('#b_tl').onclick = () => setExpanded(!UI.expanded);
  $('#b_fs').onclick = () => {
    const d = document; if (d.fullscreenElement) { d.exitFullscreen().catch(() => {}); return; }
    const p = d.documentElement.requestFullscreen ? d.documentElement.requestFullscreen() : Promise.reject();
    p.catch(() => toast('Este visor no permite pantalla completa desde la página. Usa la pantalla completa del navegador (F11).'));
  };
  $('#b_zin').onclick = () => zoomTo(UI.pxs * 1.4); $('#b_zout').onclick = () => zoomTo(UI.pxs / 1.4); $('#b_fit').onclick = fitAll;
  $('#b_snap').onclick = () => { UI.snap = !UI.snap; $('#b_snap').classList.toggle('on', UI.snap); };
  $('#b_follow').onclick = () => { UI.follow = !UI.follow; $('#b_follow').classList.toggle('on', UI.follow); };
  $('#b_undo').onclick = undo; $('#b_redo').onclick = redo;
  $('#b_resetall').onclick = () => { if (!Object.keys(EDITS).length) return; if (!confirm('¿Volver toda la línea de tiempo a los tiempos originales del guion?')) return; const s0 = snapshot(); EDITS = {}; LOCS = null; pushUndo(s0); dirty = true; refreshTitles(); layout(); renderInspector(); scheduleSave(); };
  $('#b_export').onclick = openExport; $('#b_import').onclick = importJson; $('#b_close').onclick = () => $('#tl-modal').hidden = true;
  try { const m = localStorage.getItem('sc-vomode'); if (VO_MODES[m]) S.voMode = m; } catch (e) {}
  const paintVoMode = () => { $('#b_vomode').textContent = VO_MODES[S.voMode]; $('#b_vomode').classList.toggle('on', S.voMode !== 'both'); };
  $('#b_vomode').onclick = () => { const k = Object.keys(VO_MODES); S.voMode = k[(k.indexOf(S.voMode) + 1) % k.length]; try { localStorage.setItem('sc-vomode', S.voMode); } catch (e) {}
    paintVoMode(); dirty = true; computeSchedule(); if (UI.expanded) { layout(); renderInspector(); } syncAudio(); };
  paintVoMode();
  $('#b_audio').onclick = () => $('#audio-many').click();
  $('#audio-many').onchange = async e => { const fs = [...e.target.files]; e.target.value = ''; if (fs.length) await assignFiles(fs); };
  addEventListener('dragover', e => { if ([...(e.dataTransfer && e.dataTransfer.types || [])].includes('Files')) { e.preventDefault(); document.body.classList.add('dropping'); const el = e.target.closest && e.target.closest('.clip'); document.querySelectorAll('.clip.drop').forEach(x => x !== el && x.classList.remove('drop')); if (el && soundIdOf(BYUID.get(el.dataset.uid))) el.classList.add('drop'); } });
  addEventListener('dragleave', e => { if (!e.relatedTarget) { document.body.classList.remove('dropping'); document.querySelectorAll('.clip.drop').forEach(x => x.classList.remove('drop')); } });
  addEventListener('drop', async e => {
    if (!e.dataTransfer || !e.dataTransfer.files.length) return; e.preventDefault(); document.body.classList.remove('dropping');
    document.querySelectorAll('.clip.drop').forEach(x => x.classList.remove('drop'));
    const el = e.target.closest && e.target.closest('.clip'), n = el && BYUID.get(el.dataset.uid), sid = n && soundIdOf(n), fs = [...e.dataTransfer.files];
    if (sid && sid !== 'SILENCIO' && fs.length === 1) { setStatus('Subiendo audio…'); await assignAudio(sid, fs[0]); setStatus(db ? 'Guardado' : 'Guardado en este navegador'); select(n); }
    else await assignFiles(fs);
  });
  $('#b_explore').onclick = () => { const e = $('#explore'); e.hidden = !e.hidden; $('#b_explore').classList.toggle('on', !e.hidden); if (!e.hidden) { if (lookFollow) lookSec = currentSection(); renderLook(); } };
  $('#b_start').onclick = () => { startPiece(false); seek(0); setPlaying(true); };
  $('#b_start_sound').onclick = () => { startPiece(true); seek(0); setPlaying(true); };
  $('#b_start_edit').onclick = () => { startPiece(false); seek(0); setExpanded(true); };
  // el borde superior del panel se arrastra para cambiar su alto
  const rz = $('#tl-grip'); rz.onpointerdown = e => { try { rz.setPointerCapture(e.pointerId); } catch (_) {} const y0 = e.clientY, h0 = UI.h;
    const mv = ev => { UI.h = h0 + (y0 - ev.clientY); applyPanelHeight(); }; const up = () => { rz.removeEventListener('pointermove', mv); rz.removeEventListener('pointerup', up); layout(); };
    rz.addEventListener('pointermove', mv); rz.addEventListener('pointerup', up); };
  $('#track').onclick = e => { const r = $('#track').getBoundingClientRect(); if (!S.started) startPiece(false); seek((e.clientX - r.left) / r.width * TOTAL); };
  // barra espaciadora = play / pausa, siempre (salvo escribiendo un texto). Se atrapa antes que nadie para que
  // un botón con foco no se "apriete" con el espacio, y los botones sueltan el foco después de cada clic.
  const typing = el => el && el.closest && (el.closest('textarea') || el.closest('input:not([type=range]):not([type=checkbox]):not([type=button])') || el.isContentEditable);
  addEventListener('keydown', e => { if ((e.key === ' ' || e.code === 'Space') && !typing(e.target)) { e.preventDefault(); e.stopPropagation(); if (!e.repeat) togglePlay(); } }, true);
  addEventListener('keyup', e => { if ((e.key === ' ' || e.code === 'Space') && !typing(e.target)) { e.preventDefault(); e.stopPropagation(); } }, true);
  addEventListener('click', e => { const b = e.target.closest && e.target.closest('button, input[type=range]'); if (b) setTimeout(() => b.blur(), 0); }, true);
  addEventListener('change', e => { if (e.target.matches && e.target.matches('select, input[type=range]')) e.target.blur(); }, true);
  addEventListener('pointerdown', () => { try { window.focus(); } catch (_) {} }, true);
  try { window.focus(); } catch (_) {}
  addEventListener('keydown', e => {
    if (e.target.closest && e.target.closest('input, select, textarea')) return;
    const n = UI.sel;
    if (e.key === ' ') { e.preventDefault(); }
    else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'z') { e.preventDefault(); e.shiftKey ? redo() : undo(); }
    else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'y') { e.preventDefault(); redo(); }
    else if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
      e.preventDefault(); const sgn = e.key === 'ArrowLeft' ? -1 : 1;
      if (n && UI.expanded) { const s0 = snapshot(), ed = edit(n.uid); ed.d = +((ed.d || 0) + sgn * (e.shiftKey ? 1 : .1)).toFixed(3); cleanEdit(n.uid); pushUndo(s0); dirty = true; layout(); renderInspector(); scheduleSave(); }
      else seek(S.t + sgn * (e.shiftKey ? 5 : 1));
    }
    else if (e.key === 'Home') seek(0); else if (e.key === 'End') seek(TOTAL);
    else if (e.key === 'Escape') select(null);
    else if ((e.key === 'Delete' || e.key === 'Backspace') && n && n.isLoc) { const s0 = snapshot(); LOCS = LOCS.filter(x => x !== n.L); pushUndo(s0); dirty = true; select(null); layout(); scheduleSave(); }
    else if ((e.key === 'm' || e.key === 'M') && UI.expanded) addLocatorAt(S.t);
    else if (e.key === 't' || e.key === 'T') setExpanded(!UI.expanded);
  });
  // explorar (las animaciones que se deciden juntos)
  const bind = (id, key, fmtv, cb) => { const el = $('#x_' + id), out = $('#o_' + id); const f = () => { S.tw[key] = +el.value; out && (out.textContent = fmtv(+el.value)); cb && cb(); }; el.addEventListener('input', f); f(); };
  bind('lift', 'lift', v => v + ' cm'); bind('glow', 'glow', v => v.toFixed(2)); bind('spin', 'spin', v => ['quieto', 'lento', 'rápido'][v]);
  bind('gfps', 'gfps', v => v); bind('gecho', 'gecho', v => v); bind('travel', 'travel', v => v ? 'sí' : 'no'); bind('spark', 'spark', v => v ? 'sí' : 'no');
  $('#x_veil').addEventListener('change', e => { S.tw.veil = +e.target.value; });
  const view = (() => { try { return JSON.parse(localStorage.getItem('sc-view') || '{}'); } catch (e) { return {}; } })();
  const fovEl = $('#x_fov'), backEl = $('#x_back');
  if (view.fov) fovEl.value = view.fov; if (view.back != null) backEl.value = view.back;
  const applyView = () => { camera.fov = +fovEl.value; camera.updateProjectionMatrix(); S.camBack = +backEl.value;
    $('#o_fov').textContent = fovEl.value + '°'; $('#o_back').textContent = (+backEl.value).toFixed(1) + ' m';
    try { localStorage.setItem('sc-view', JSON.stringify({ fov: +fovEl.value, back: +backEl.value })); } catch (e) {} };
  fovEl.addEventListener('input', applyView); backEl.addEventListener('input', applyView); applyView();
  $('#b_view').onclick = () => { fovEl.value = 72; backEl.value = 0; applyView(); };
  addEventListener('resize', () => { applyPanelHeight(); });
}
function toast(t) { const d = $('#toast'); d.textContent = t; d.hidden = false; clearTimeout(d._t); d._t = setTimeout(() => d.hidden = true, 5000); }

function boot() {
  resolveAll(); captureLookDefaults(); loadLocal(); applyLookStatic(); computeSchedule(); buildEditor(); bindControls(); layout(); renderInspector();
  applyPanelHeight(); seek(0); evaluate(0);
  refreshCard();
  fontReady.then(() => { FONTS_OK = true; refreshCard(); TITLE_REG.forEach(r => { const { tex, aspect } = textTexture(r.text, r.opts.px || 110, r.opts.font || 'Michroma', r.opts.weight || ''); r.mesh.material.uniforms.uTex.value = tex; r.mesh.geometry.dispose(); r.mesh.geometry = new THREE.PlaneGeometry(r.height * aspect, r.height); if (r.opts.left) r.mesh.geometry.translate(r.height * aspect / 2, 0, 0); }); }).catch(() => {});
  initDb().then(initAudio);
  schedule();
  if (/[?&]debug\b/.test(location.search)) window.SC = { CUT, loadAudioDoc, get LOCS() { return LOCS; }, get WARP() { return WARP; }, addLocatorAt, envOf, finOf, AUDIO, voices, packAudio, bytesFromB64, S, W, GL, BEATS, CLIPS, BYUID, seek, setPlaying, computeSchedule, evaluate, tickGates, resolveHeldGate, layout, UI, get EDITS() { return EDITS; }, get TOTAL() { return TOTAL; } };
}
