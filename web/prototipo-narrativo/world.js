/* Soul Charger · prototipo narrativo · EL MUNDO: escena three.js, objetos, materiales, sonidos de marcador.
   Lo que pasa y cuándo lo decide la línea de tiempo (guion.js + engine.js). Unidades: metros; el pawn está sentado (ojos a 1,2 m). */
'use strict';
const $ = s => document.querySelector(s);
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const lerp = (a, b, t) => a + (b - a) * t;
const smooth = t => { t = clamp(t); return t * t * (3 - 2 * t); };
const ease = t => { t = clamp(t); return t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; };
const col = a => new THREE.Color(a[0], a[1], a[2]).convertLinearToSRGB();
const TAU = Math.PI * 2;

/* ============ datos de la obra (valores de las últimas versiones) ============ */
const STAGES = [
  { key: 'ENTERING', name: 'Entering', color: '#5d7fe0', tileDeg: 180, top: [.55, .64, .82], hor: [.66, .73, .88],   // = vidrio de salida del Hall (Beltrán 09-30)
    grad: [[.855, .7605, .9131], [.7305, .6445, .8388], [.4342, .5271, .855], [.0612, .117, .3515]] },
  { key: 'RECOGNIZING', name: 'Recognizing', color: '#e0566b', tileDeg: 108, top: [.40, .30, .31], hor: [.95, .85, .83],   // velo = cielo de Test_Heart (SkyColorHorizon 09-30; antes el azul viejo)
    grad: [[1, .92, .88], [1, .78, .72], [1, .34, .28], [.34, .07, .09]] },   // paleta blanca-rojiza de Test_Heart
  { key: 'LOVING', name: 'Loving', color: '#9a6ee6', tileDeg: 36, top: [.0369, .0273, .0482], hor: [.0176, .0130, .0232],   // velo = fluido morado de Test_Fluid (#362E3E / #241E2A)
    grad: [[.93, .838, .965], [.651, .546, .693], [.434, .3, .665], [.07, .045, .109]] },   // morado de Test_Fluid (Mind)
  { key: 'ATTRACTING', name: 'Attracting', color: '#e8a04e', tileDeg: 324, top: [.863, .745, .631], hor: [.973, .815, .565],   // velo = cielo Uyuni de Test_Sequencer (#efe0d0 / #fce9c6)
    grad: [[1, .896, .761], [.896, .631, .413], [.855, .565, .353], [.3, .17, .08]] },   // Uyuni de Test_Sequencer
  { key: 'SURROUNDING', name: 'Surrounding', color: '#4fc28f', tileDeg: 252, top: [.0027, .0033, .008], hor: [.0137, .0194, .0395],
    grad: [[.92, .97, .94], [.62, .82, .72], [.25, .58, .45], [.05, .2, .15]] },   // verdes del mar del dibujo
];
const CHARGE_T = [4, 4, 4, 4, 6];   // = ChargeTimes de BP_Obra_SC (Beltrán 09-30: la común 4 s; la final 6 s con tres explosiones, giro, vibración y háptico)
const CHARGE_HOLD = 2;   // quietud con la luz ya encendida antes de volver al HUD (HoldTime de BP_ChargeTest_SC, Beltrán 09-30)
const NOTE = [261.6, 293.7, 329.6, 392.0, 440.0]; // una nota por etapa: juntas, el acorde de la obra
const HALL = { rIn: 7.0, rim: 5.6, apex: 6.5, ocR: 1.2, doorR: 1.75, doorY: 1.95, tileR1: 1.0, tileR2: 2.5 };
const EYE = 1.2;

/* ============ estado ============ */
const S = {
  speed: 1, playing: false, t: 0, clock: 0, sound: false, voice: false, started: false, live: true,
  tw: { lift: 3, glow: .45, spin: 1, gfps: 11, gecho: 4, veil: 3, travel: 1, spark: 0 },
  hand: new THREE.Vector3(), handPrev: new THREE.Vector3(), handVel: new THREE.Vector3(), mouse: new THREE.Vector2(),
  down: false, clicked: false, rdown: false, yaw: 0, pitch: -.05, targetYaw: 0,
  choice: 2, dominant: 'right', voMode: 'both', melody: new Array(8).fill(-1),
  data: { breath: [], beats: 0, bpm: 68, calm: [], melody: [], strokes: [] },
  stillness: 1, // 0 = mucho movimiento, 1 = quieto
};

/* ============ render ============ */
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
$('#stage').appendChild(renderer.domElement);
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x000000);
const camera = new THREE.PerspectiveCamera(72, 1, .03, 4000);
const rig = new THREE.Group(); rig.add(camera); camera.position.y = EYE; scene.add(rig);
const hud = new THREE.Group(); camera.add(hud); // lo que viaja con la cabeza
function resize() { const r = $('#stage').getBoundingClientRect(), w = Math.max(1, r.width), h = Math.max(1, r.height); renderer.setSize(w, h); camera.aspect = w / h; camera.updateProjectionMatrix(); }
addEventListener('resize', resize); resize();

/* ============ audio de marcador (WebAudio) ============ */
let AC = null, master = null, ambGain = null, ambNodes = [];
function audioOn() {
  if (AC) { if (AC.state === 'suspended') AC.resume().catch(() => {}); return; }
  AC = new (window.AudioContext || window.webkitAudioContext)();
  master = AC.createGain(); master.gain.value = .5; master.connect(AC.destination);
  ambGain = AC.createGain(); ambGain.gain.value = 0; ambGain.connect(master);
}
function tone(f, dur = 1, type = 'sine', g = .15, attack = .02, when = 0) {
  if (!S.sound || !AC) return;
  const t = AC.currentTime + when, o = AC.createOscillator(), a = AC.createGain();
  o.type = type; o.frequency.value = f; a.gain.setValueAtTime(0, t);
  a.gain.linearRampToValueAtTime(g, t + attack); a.gain.exponentialRampToValueAtTime(.0005, t + dur);
  o.connect(a); a.connect(master); o.start(t); o.stop(t + dur + .05);
}
function swell(f0, f1, dur, g = .1, type = 'sine') {
  if (!S.sound || !AC) return;
  const t = AC.currentTime, o = AC.createOscillator(), a = AC.createGain();
  o.type = type; o.frequency.setValueAtTime(f0, t); o.frequency.exponentialRampToValueAtTime(f1, t + dur);
  a.gain.setValueAtTime(0, t); a.gain.linearRampToValueAtTime(g, t + dur * .7); a.gain.linearRampToValueAtTime(0, t + dur);
  o.connect(a); a.connect(master); o.start(t); o.stop(t + dur + .05);
}
function noise(dur = 2, g = .06, f = 800) {
  if (!S.sound || !AC) return;
  const n = AC.createBufferSource(), b = AC.createBuffer(1, AC.sampleRate * dur, AC.sampleRate), d = b.getChannelData(0);
  for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
  n.buffer = b; const fl = AC.createBiquadFilter(); fl.type = 'lowpass'; fl.frequency.value = f;
  const a = AC.createGain(), t = AC.currentTime; a.gain.setValueAtTime(0, t); a.gain.linearRampToValueAtTime(g, t + dur * .5); a.gain.linearRampToValueAtTime(0, t + dur);
  n.connect(fl); fl.connect(a); a.connect(master); n.start(t);
}
const AMB = { AMB_01: [110, 165, 220], AMB_02: [98, 147, 196], AMB_03: [130.8, 196, 246.9], AMB_04: [110, 164.8, 246.9],
  AMB_05: [87.3, 130.8, 174.6], AMB_06: [73.4, 110, 164.8], AMB_07: [98, 146.8, 185], AMB_08: [123.5, 185, 246.9], AMB_09: [110, 165, 220] };
function ambient(id, fade = 3) {
  if (!S.sound || !AC) return;
  const t = AC.currentTime;
  ambNodes.forEach(n => { n.g.gain.cancelScheduledValues(t); n.g.gain.setValueAtTime(n.g.gain.value, t); n.g.gain.linearRampToValueAtTime(0, t + fade); n.o.forEach(o => o.stop(t + fade + .1)); });
  ambNodes = [];
  if (!id || !AMB[id]) return;
  const g = AC.createGain(); g.gain.value = 0; g.connect(master);
  const os = AMB[id].map((f, i) => { const o = AC.createOscillator(); o.type = i ? 'sine' : 'triangle'; o.frequency.value = f; o.detune.value = (i - 1) * 4; o.connect(g); o.start(); return o; });
  g.gain.linearRampToValueAtTime(.035, t + fade); ambNodes.push({ g, o: os });
}
const FXSYN = {
  FX_TITLE: () => NOTE.forEach((f, i) => tone(f * 2, 4, 'sine', .04, 1.2, i * .12)),
  FX_TITLE_WARM: () => [196, 247, 294].forEach((f, i) => tone(f * 2, 3, 'sine', .04, .8, i * .1)),
  FX_PORTALGLOW: () => swell(55, 82, 4, .12, 'triangle'),
  FX_BELLAPPEAR: () => tone(1318, 1, 'sine', .06),
  FX_CARGABELL: () => swell(220, 660, 3, .08, 'triangle'),
  FX_BELLRING: () => { tone(523, 3, 'sine', .12); tone(1046, 2.4, 'sine', .05); },
  FX_DOOROPEN: () => noise(3, .05, 600),
  FX_ALMAAPPEAR: () => { noise(1.4, .03, 2500); tone(659, 1.4, 'sine', .04, .5); },
  FX_ALMAMOVE: () => noise(2, .02, 1800), FX_ALMAOUT: () => { noise(1, .03, 2500); tone(494, 1, 'sine', .03); },
  FX_CONTROLLERAPEAR: () => tone(880, 1.4, 'sine', .05, .3),
  FX_CONTROLLERATACHED: () => { tone(330, .4, 'triangle', .12); tone(660, .3, 'sine', .05); },
  FX_PROTOAPPEAR: () => NOTE.forEach((f, i) => tone(f * 4, .9, 'sine', .04, .01, i * .4)),
  FX_PROTOHOVER: () => tone(NOTE[S.hoverNote | 0] * 4, .5, 'sine', .03),
  FX_PROTOSELECT: () => [0, 2, 4].forEach(k => tone(NOTE[(S.choice + k) % 5] * 2, 1.6, 'sine', .06)),
  FX_RINGAPPEAR: () => swell(330, 660, 1.5, .05), FX_RINGDIM: () => NOTE.forEach(f => tone(f, 2, 'sine', .03)),
  FX_CALIBRATION: () => swell(200, 900, 2.5, .05), FX_HUDBIRTH: () => [392, 494, 587].forEach((f, i) => tone(f, 1, 'sine', .05, .02, i * .2)),
  FX_SOULTOFACE: () => tone(NOTE[S.choice] * 2, 1.5, 'sine', .05, .4), FX_SOULDETACH: () => tone(NOTE[S.choice] * 2, 1.5, 'sine', .05, .4),
  FX_DOORREVEAL: () => swell(65, 98, 3, .1, 'triangle'), FX_STAGEREVEAL: () => noise(5, .04, 1200),
  FX_VEIL: () => noise(10, .05, 700), FX_TOOLAPPEAR: () => tone(740, .8, 'sine', .05, .05), FX_TOOLOUT: () => tone(370, .8, 'sine', .04),
  FX_GHOSTAPPEAR: () => noise(1, .02, 3000), FX_GHOSTOUT: () => tone(988, .6, 'sine', .03),
  // aparición "luz primero" (sintético mientras no haya audio): un barrido que sube y se asienta; la salida, el mismo al revés
  // teletransporte del alma: aviso que sube, el pum de salida (hueco) y el de llegada (brillante), y el asiento en el HUD
  FX_SOULPOP_OUT: () => { tone(90, .35, 'sine', .12, .005); noise(.18, .05, 2400); }, FX_SOULPOP_IN: () => { tone(660, .5, 'sine', .07, .005); tone(990, .7, 'sine', .04, .005, .04); noise(.25, .04, 3200); },
  FX_SOULSETTLE: () => tone(1320, .25, 'triangle', .04, .003), FX_SISTERAPPEAR: () => { tone(NOTE[S.choice] * 2, .8, 'sine', .05, .005); tone(NOTE[S.choice] * 3, .6, 'sine', .03, .005, .08); }, FX_SOULWARN_BACK: () => swell(300, 700, .8, .05),
  FX_BELLVANISH: () => swell(900, 300, 1.5, .04), FX_PALETTEAPPEAR: () => swell(300, 900, 1.5, .04), FX_PALETTEVANISH: () => swell(900, 300, 1.5, .04),
  FX_SENSORAPPEAR: () => swell(300, 900, 1.5, .04), FX_SENSORVANISH: () => swell(900, 300, 1.5, .04), FX_RINGAPPEAR: () => swell(260, 780, 1.5, .04), FX_HUDVANISH: () => swell(780, 260, 1.5, .04),
  FX_HEARTBEAT: () => { tone(55, .5, 'sine', .3, .005); tone(80, .3, 'sine', .15, .005, .02); },
  FX_MEMBRANE: () => tone(45, 1.4, 'sine', .15, .01),
  FX_BEAMON: () => swell(400, 1600, .5, .05, 'sawtooth'), FX_ORBGRAB: () => swell(300, 600, .4, .05), FX_SLOTSNAP: () => tone(1760, .25, 'triangle', .06),
  FX_SAVEHOLD: () => swell(220, 660, 3, .06, 'triangle'), FX_WORMRISE: () => noise(3, .04, 400), FX_ORBSWAVE: () => NOTE.forEach((f, i) => tone(f * 8, .6, 'sine', .02, .01, i * .1)),
  FX_TABLERISE: () => noise(3, .04, 500), FX_PALETTEAPPEAR: () => tone(1175, .6, 'sine', .04), FX_SENSORRELEASE: () => swell(880, 220, 2, .04),
  FX_CARDAPPEAR: () => noise(2, .03, 3000), FX_SOULLEAD: () => tone(NOTE[S.choice] * 2, 3, 'sine', .05, 1),
  FX_CONSTELLATION: () => NOTE.forEach((f, i) => tone(f * 4, 2, 'sine', .02, .5, i * .5)),
  FX_CHARGEFINAL: () => NOTE.forEach((f, i) => tone(f, 12, 'sine', .05, 3, i * .2)),
  FX_CELLFORM: () => noise(4, .03, 900), FX_BLOBFORM: () => noise(3, .03, 700), FX_MINDSPIRAL: () => swell(110, 880, 6, .05),
  // provisorios (Beltrán 09-30: "mientras no tenga todos los sonidos"): se reemplazan soltando un audio sobre el clip
  FX_SOULSWIM: () => [0, 2, 4, 1, 3, 0, 2, 4].forEach((n, i) => { tone(NOTE[n] * 4 * (i % 3 === 2 ? 1.5 : 1), 1.3, 'sine', .022, .004, i * .38 + (i % 2) * .07); tone(NOTE[n] * 8, .5, 'sine', .008, .004, i * .38 + .012); }),
  FX_SHAREAPPEAR: () => swell(300, 900, 1.2, .04), FX_SHAREHOVER: () => tone(1568, .14, 'triangle', .03, .003),
  FX_SHARESELECT: () => [0, 2, 4].forEach((k, i) => tone(NOTE[k] * 4, 1.4, 'sine', .05, .005, i * .07)),
  FX_SOULVANISH: () => { swell(880, 220, 1.8, .03); noise(1.4, .015, 3200); }, FX_SOULJOIN: () => NOTE.forEach((f, i) => tone(f * 4, 2.8, 'sine', .022, .25, i * .14)),
  FX_RINGVANISH: () => swell(660, 220, .9, .04), FX_DISCLAIMER: () => tone(196, 5, 'sine', .025, 1.5),
  FX_PACER_INHALE: () => swell(220, 330, 3.5, .04), FX_PACER_EXHALE: () => swell(330, 220, 3.5, .04), FX_PACER_HOLD: () => tone(275, 2.5, 'sine', .02, 1),
};

/* ============ consola: marcas, voz, pasos ============ */
function cue(kind, id, note = '', silent = false) {
  const el = document.createElement('div'); el.className = 'cue ' + kind;
  el.innerHTML = `<i>${{ fx: 'SONIDO', hap: 'HÁPTICA', vfx: 'EFECTO', amb: 'MÚSICA' }[kind]}</i>${id}${note ? ' · ' + note : ''}`;
  $('#cues').prepend(el); setTimeout(() => el.remove(), 3300);
  while ($('#cues').children.length > 9) $('#cues').lastChild.remove();
  if (silent) return;
  if (kind === 'fx') { if (typeof playSoundId === 'function' && playSoundId(id)) return; const base = id.replace(/_\d+$/, ''); (FXSYN[id] || FXSYN[base] || (() => {}))(); }
  if (kind === 'amb') { if (typeof setAmbient === 'function') setAmbient(id, 0, 3); else ambient(id); }
}
/* duración estimada de un clip de voz (se reemplaza por la del audio real cuando llegue) */
function voDur(text) { return 1 + text.split(/\s+/).length / 2.4 + (text.match(/…/g) || []).length * .5; }
function speak(text) {
  if (!S.voice || S.speed !== 1 || !('speechSynthesis' in window)) return;
  try { speechSynthesis.cancel(); const u = new SpeechSynthesisUtterance(text.replace(/…/g, '...')); u.lang = 'en-US'; u.rate = .88; u.pitch = 1.05; speechSynthesis.speak(u); } catch (e) {}
}
function hush() { try { 'speechSynthesis' in window && speechSynthesis.cancel(); } catch (e) {} }

/* ============ shaders compartidos ============ */
const NOISE = `
float h3(vec3 p){ p=fract(p*.3183099+.1); p*=17.; return fract(p.x*p.y*p.z*(p.x+p.y+p.z)); }
float vn(vec3 x){ vec3 i=floor(x), f=fract(x); f=f*f*(3.-2.*f);
  return mix(mix(mix(h3(i),h3(i+vec3(1,0,0)),f.x),mix(h3(i+vec3(0,1,0)),h3(i+vec3(1,1,0)),f.x),f.y),
             mix(mix(h3(i+vec3(0,0,1)),h3(i+vec3(1,0,1)),f.x),mix(h3(i+vec3(0,1,1)),h3(i+vec3(1,1,1)),f.x),f.y),f.z); }`;

/* cielo / niebla envolvente (esfera enorme que sigue a la cámara) */
function skyMat(top, hor, amount = 1) {
  return new THREE.ShaderMaterial({
    uniforms: { uTop: { value: col(top) }, uHor: { value: col(hor) }, uAmt: { value: amount }, uT: { value: 0 }, uBright: { value: 1 } },
    vertexShader: `varying vec3 vD; void main(){ vD = normalize(position); gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.); }`,
    fragmentShader: `uniform vec3 uTop,uHor; uniform float uAmt,uT,uBright; varying vec3 vD; ${NOISE}
      void main(){ float h=vD.y; float n=vn(vD*3.+vec3(uT*.02,0,uT*.015));
        vec3 c=mix(uHor,uTop,smoothstep(-.25,.9,h+.08*n)); c*=.85+.3*n; gl_FragColor=vec4(c*uAmt*uBright,1.); }`,
    side: THREE.BackSide, depthWrite: false,
  });
}

/* ============ el vacío: niebla azul + polvo que sigue a la mano ============ */
const voidG = new THREE.Group(); scene.add(voidG);
// Beltrán 09-30: el entorno del inicio y del final es OSCURO (como en Unreal): azul noche casi negro, horizonte apenas más claro
const voidSky = new THREE.Mesh(new THREE.SphereGeometry(900, 48, 24), skyMat([.006, .009, .022], [.028, .042, .095], 0));
voidSky.renderOrder = -10; voidG.add(voidSky);
const DUST_N = 2600, DUST_BOX = 24;
const dustGeo = new THREE.BufferGeometry(); {
  const p = new Float32Array(DUST_N * 3), s = new Float32Array(DUST_N);
  for (let i = 0; i < DUST_N; i++) { p[i * 3] = (Math.random() - .5) * DUST_BOX; p[i * 3 + 1] = Math.random() * 8 - 2; p[i * 3 + 2] = (Math.random() - .5) * DUST_BOX; s[i] = Math.random(); }
  dustGeo.setAttribute('position', new THREE.BufferAttribute(p, 3)); dustGeo.setAttribute('seed', new THREE.BufferAttribute(s, 1));
}
const dustMat = new THREE.ShaderMaterial({
  uniforms: { uCam: { value: new THREE.Vector3() }, uHand: { value: new THREE.Vector3() }, uVel: { value: new THREE.Vector3() }, uT: { value: 0 }, uAmt: { value: 1 }, uTint: { value: new THREE.Color(.85, .9, 1) }, uBox: { value: DUST_BOX }, uSize: { value: 1 } },
  vertexShader: `attribute float seed; uniform vec3 uCam,uHand,uVel; uniform float uT,uBox,uSize; varying float vA;
    void main(){ vec3 p=position; p.x+=sin(uT*.13+seed*40.)*.4; p.y+=sin(uT*.11+seed*23.)*.3; p.z+=cos(uT*.09+seed*31.)*.4;
      vec3 rel=p-uCam; rel.xz=mod(rel.xz+uBox*.5,uBox)-uBox*.5; p=uCam+rel; p.y=position.y+sin(uT*.1+seed*9.)*.3+uCam.y-1.2;
      vec3 d=p-uHand; float fall=exp(-dot(d,d)*6.); vec3 sw=cross(normalize(uVel+vec3(1e-4)),vec3(0,1,0))*length(uVel);
      p+=(uVel*.35+sw*.25)*fall*1.6;
      vec4 mv=modelViewMatrix*vec4(p,1.); gl_Position=projectionMatrix*mv;
      gl_PointSize=min((1.+seed*1.4)*(40./-mv.z),5.)*uSize; vA=smoothstep(22.,4.,-mv.z)*smoothstep(.25,1.2,-mv.z)*(.3+.6*seed); }`,
  fragmentShader: `uniform vec3 uTint; uniform float uAmt; varying float vA; void main(){ vec2 q=gl_PointCoord-.5; float d=smoothstep(.5,.0,length(q));
    gl_FragColor=vec4(uTint,d*vA*uAmt); }`,
  transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
});
const dust = new THREE.Points(dustGeo, dustMat); dust.frustumCulled = false; scene.add(dust);

/* mano: un brillo translúcido donde está el mouse */
const handMesh = new THREE.Mesh(new THREE.SphereGeometry(.014, 16, 12), new THREE.MeshBasicMaterial({ color: 0xdfe8ff, transparent: true, opacity: .5, depthWrite: false }));
scene.add(handMesh);

/* ============ texto con el material líquido de los títulos ============ */
let FONTS_OK = false; const TITLE_REG = [];
const fontReady = document.fonts ? document.fonts.load('64px Michroma') : Promise.resolve();
function textTexture(text, px = 96, font = 'Michroma', weight = '') {
  const c = document.createElement('canvas'), g = c.getContext('2d');
  g.font = `${weight} ${px}px ${font}`; const w = Math.ceil(g.measureText(text).width + px * .8);
  c.width = w; c.height = Math.ceil(px * 1.6); g.font = `${weight} ${px}px ${font}`;
  g.fillStyle = '#fff'; g.textBaseline = 'middle'; g.fillText(text, px * .4, c.height / 2);
  const t = new THREE.CanvasTexture(c); t.anisotropy = 8; return { tex: t, aspect: c.width / c.height };
}
function titleMesh(text, height, grad, opts = {}) {
  const { tex, aspect } = textTexture(text, opts.px || 110, opts.font || 'Michroma', opts.weight || '');
  const m = new THREE.ShaderMaterial({
    uniforms: { uTex: { value: tex }, uR: { value: 0 }, uO: { value: 0 }, uT: { value: 0 }, uWhite: { value: opts.white ? 1 : 0 },
      c0: { value: col(grad[0]) }, c1: { value: col(grad[1]) }, c2: { value: col(grad[2]) }, c3: { value: col(grad[3]) } },
    vertexShader: `varying vec2 vUv; void main(){ vUv=uv; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.); }`,
    fragmentShader: `uniform sampler2D uTex; uniform float uR,uO,uT,uWhite; uniform vec3 c0,c1,c2,c3; varying vec2 vUv;
      void main(){ float a=texture2D(uTex,vUv).a; float t=uT;
        float q=sin(vUv.x*7.+t*.35+sin(vUv.y*9.+t*.21)*1.3); float k=.5+.5*sin(6.2831*(vUv.x*1.15+q*.08-t*.022));
        vec3 c=mix(c0,c1,smoothstep(0.,.36,k)); c=mix(c,c2,smoothstep(.3,.68,k)); c=mix(c,c3,smoothstep(.62,1.,k));
        c=mix(c,vec3(1.),uWhite);
        float front=uR*1.4-.2; float rv=1.-smoothstep(front-.2,front,vUv.x+.05*sin(vUv.y*9.+t*.8));
        float n=.5+.5*sin(vUv.x*23.+sin(vUv.y*7.+t*.5)*2.+t*.4); float gone=smoothstep(n-.18,n+.18,uO*1.2);
        gl_FragColor=vec4(c,a*rv*(1.-gone)); }`,
    transparent: true, depthWrite: false, depthTest: opts.depthTest !== false,
  });
  const geo = new THREE.PlaneGeometry(height * aspect, height); if (opts.left) geo.translate(height * aspect / 2, 0, 0);
  const mesh = new THREE.Mesh(geo, m);
  mesh.renderOrder = opts.order || 20; if (!FONTS_OK) TITLE_REG.push({ mesh, text, height, opts }); return mesh;
}

/* ============ el Hall: pabellón circular, óculo, dos puertas, cinco baldosas ============ */
const hallG = new THREE.Group(); scene.add(hallG); hallG.visible = false;
const hallU = { uWave: { value: 1 }, uLight: { value: 0 }, uWest: { value: 0 }, uEast: { value: 0 }, uT: { value: 0 }, uWarm: { value: new THREE.Color(.93, .72, .50) } };
{
  const pts = [];
  for (let i = 0; i <= 10; i++) pts.push(new THREE.Vector2(HALL.rIn, HALL.rim * i / 10 - .02));
  for (let i = 1; i <= 24; i++) { const a = i / 24 * Math.PI / 2; pts.push(new THREE.Vector2(lerp(HALL.ocR, HALL.rIn, Math.cos(a)), HALL.rim + (HALL.apex - HALL.rim) * Math.sin(a))); }
  const lathe = new THREE.LatheGeometry(pts, 96);
  const doorCut = `
    bool door(vec3 p){ float dz=p.z, dy=p.y-${HALL.doorY.toFixed(2)}; return abs(p.x)>5.5 && dz*dz+dy*dy<${(HALL.doorR * HALL.doorR).toFixed(3)}; }`;
  const inner = new THREE.ShaderMaterial({
    uniforms: hallU, side: THREE.BackSide,
    vertexShader: `varying vec3 vP; void main(){ vP=position; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.); }`,
    fragmentShader: `uniform float uLight,uT,uWave; uniform vec3 uWarm; varying vec3 vP; ${NOISE} ${doorCut}
      void main(){ if(door(vP)) discard; float h=vP.y/${HALL.apex.toFixed(1)};
        vec3 warm=uWarm; vec3 c=warm*(1.05-.55*smoothstep(.5,1.,h)); c*=.92+.08*vn(vP*9.);
        float ln=smoothstep(.035,.0,abs(fract(h*16.)-.5)-.465)*step(.04,h)*(1.-smoothstep(.86,.95,h)); float lit=smoothstep(0.,.12,uWave*1.25-h);
        c*=1.-.22*ln*(1.-lit); c+=warm*.55*ln*lit;
        float oc=smoothstep(2.4,1.2,length(vP.xz))*smoothstep(.8,1.,h); c+=vec3(.9,.8,.62)*oc*.6;
        gl_FragColor=vec4(c*uLight,1.); }`,
  });
  const outer = new THREE.ShaderMaterial({
    uniforms: hallU, side: THREE.FrontSide,
    vertexShader: `varying vec3 vP; void main(){ vP=position; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.); }`,
    fragmentShader: `uniform float uLight; uniform vec3 uWarm; varying vec3 vP; ${doorCut}
      void main(){ if(door(vP)) discard; float dz=vP.z, dy=vP.y-${HALL.doorY.toFixed(2)}; float r=sqrt(dz*dz+dy*dy);
        float frame= abs(vP.x)>5.5 ? smoothstep(.08,.0,abs(r-1.86)) : 0.; gl_FragColor=vec4(vec3(.012)*uLight+uWarm*vec3(1.075,1.08,1.)*frame*uLight,1.); }`,
  });
  hallG.add(new THREE.Mesh(lathe, inner));
  const outerMesh = new THREE.Mesh(lathe, outer); outerMesh.scale.set(1.043, 1.02, 1.043); hallG.add(outerMesh);
  const floor = new THREE.Mesh(new THREE.CircleGeometry(HALL.rIn, 96), new THREE.ShaderMaterial({
    uniforms: hallU, vertexShader: `varying vec3 vP; void main(){ vP=position; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.); }`,
    fragmentShader: `uniform float uLight; uniform vec3 uWarm; varying vec3 vP; ${NOISE} void main(){ float r=length(vP.xy);
      vec3 c=uWarm*vec3(.86,.86,.9)*(.9+.1*vn(vec3(vP.xy*6.,0.))); c*=1.-.25*smoothstep(3.,7.,r);
      c*=1.-.35*smoothstep(.02,0.,abs(r-2.9))-.3*smoothstep(.02,0.,abs(r-6.2)); gl_FragColor=vec4(c*uLight,1.); }` }));
  floor.rotation.x = -Math.PI / 2; hallG.add(floor);
  // cielo del óculo y haz de luz
  const oc = new THREE.Mesh(new THREE.CircleGeometry(HALL.ocR, 48), new THREE.ShaderMaterial({ uniforms: hallU, vertexShader: 'void main(){ gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.); }', fragmentShader: 'uniform float uLight; void main(){ gl_FragColor=vec4(vec3(1.,.95,.86)*uLight,1.); }', side: THREE.DoubleSide }));
  oc.rotation.x = Math.PI / 2; oc.position.y = HALL.apex - .01; hallG.add(oc); hallG.userData.oc = oc;
  const shaft = new THREE.Mesh(new THREE.CylinderGeometry(HALL.ocR, 2.2, HALL.apex, 48, 1, true), new THREE.ShaderMaterial({
    uniforms: hallU, vertexShader: `varying vec2 vUv; void main(){ vUv=uv; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.); }`,
    fragmentShader: `uniform float uLight; varying vec2 vUv; void main(){ gl_FragColor=vec4(vec3(1.,.9,.72),.10*uLight*smoothstep(0.,.9,vUv.y)); }`,
    transparent: true, depthWrite: false, side: THREE.DoubleSide, blending: THREE.AdditiveBlending }));
  shaft.position.y = HALL.apex / 2; hallG.add(shaft);
}
/* hojas de las puertas: medias lunas de vidrio que corren sobre el muro (pivote en el eje del edificio) */
function glassMat(which) {
  return new THREE.ShaderMaterial({
    uniforms: { uLight: hallU.uLight, uCool: { value: 0 }, uWarm: hallU.uWarm },
    vertexShader: `varying vec2 vUv; void main(){ vUv=uv; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.); }`,
    fragmentShader: `uniform float uLight,uCool; uniform vec3 uWarm; varying vec2 vUv; void main(){ vec3 warm=uWarm*vec3(1.075,1.03,.9), cool=vec3(.77,.82,.92);   /* blanco azulado medio = el velo que abre Entering (Beltrán 09-30) */
      vec3 c=mix(warm,cool,uCool)*1.15*uLight; float m=.82+.14*smoothstep(0.,.7,length(vUv-.5)); gl_FragColor=vec4(c,m*(.55+.4*uLight)); }`,
    transparent: true, depthWrite: false, side: THREE.DoubleSide,
  });
}
const doors = {};
['west', 'east'].forEach(side => {
  const sgn = side === 'east' ? 1 : -1, mat = glassMat(side);
  const leaves = [-1, 1].map(half => {
    const pivot = new THREE.Group(); hallG.add(pivot);
    const leaf = new THREE.Mesh(new THREE.CircleGeometry(1.86, 48, half > 0 ? -Math.PI / 2 : Math.PI / 2, Math.PI), mat);
    leaf.rotation.y = sgn * Math.PI / 2; leaf.position.set(sgn * (HALL.rIn * 1.05 + .02), HALL.doorY, 0);
    pivot.add(leaf); pivot.userData.half = half; return pivot;
  });
  doors[side] = { leaves, mat, open: 0, sgn };
});
function setDoor(side, k) { const d = doors[side]; d.open = k; d.leaves.forEach(p => p.rotation.y = p.userData.half * .30 * ease(k)); }
/* baldosas */
const tiles = STAGES.map((st, i) => {
  const gap = .22 / ((HALL.tileR1 + HALL.tileR2) / 2), len = TAU / 5 - gap, a0 = st.tileDeg * Math.PI / 180 - len / 2;
  const sh = new THREE.Shape(); sh.moveTo(Math.cos(a0) * HALL.tileR1, Math.sin(a0) * HALL.tileR1); sh.absarc(0, 0, HALL.tileR2, a0, a0 + len, false); sh.absarc(0, 0, HALL.tileR1, a0 + len, a0, true);
  const geo = new THREE.ExtrudeGeometry(sh, { depth: .03, bevelEnabled: true, bevelThickness: .01, bevelSize: .014, bevelSegments: 3, curveSegments: 48 });   // biselada (Beltrán, 09-30): al subir no se ven cantos rectos
  const m = new THREE.ShaderMaterial({
    uniforms: { uLight: hallU.uLight, uCol: { value: new THREE.Color(st.color) }, uGlow: { value: 0 } },
    vertexShader: `varying vec2 vP; varying vec3 vN; void main(){ vP=position.xy; vN=normalize(normalMatrix*normal); gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.); }`,
    // al subir se ENCIENDE con el color de su etapa, como las teclas de la paleta del dibujo (Beltrán, 09-30)
    fragmentShader: `uniform float uLight,uGlow; uniform vec3 uCol; varying vec2 vP; varying vec3 vN; void main(){ vec3 base=mix(vec3(.62,.5,.4),uCol,.28);
      float sh=.78+.22*clamp(dot(normalize(vN),normalize(vec3(-.2,.9,.4))),0.,1.); float g=clamp(uGlow,0.,1.);
      vec3 c=mix(base*(.55+.3*uLight),uCol*1.2+vec3(.05),g)*sh+uCol*max(uGlow-1.,0.)*.5; gl_FragColor=vec4(c*max(uLight,g),1.); }`,
  });
  const mesh = new THREE.Mesh(geo, m); mesh.rotation.x = -Math.PI / 2; mesh.position.y = -.034; hallG.add(mesh);
  const label = titleMesh(st.key, .16, st.grad, { px: 90 });
  const mid = st.tileDeg * Math.PI / 180, R = (HALL.tileR1 + HALL.tileR2) / 2;
  label.position.set(Math.cos(mid) * R, .42, -Math.sin(mid) * R); label.lookAt(-3.2, EYE, 0); hallG.add(label);
  return { mesh, m, label, lift: 0 };
});
function setTile(i, lift, glow) { const t = tiles[i]; t.lift = lift; t.glowRaw = glow; t.mesh.position.y = -.034 + lift * S.tw.lift / 100; t.m.uniforms.uGlow.value = glow * S.tw.glow / .45; }
const centerTitle = titleMesh('SOUL CHARGER CENTER', .32, [[1, .9, .75], [.98, .78, .55], [.92, .66, .45], [.8, .55, .38]], { px: 100 });
centerTitle.position.set(-HALL.rIn * 1.05 - .05, HALL.doorY + 2.35, 0); centerTitle.rotation.y = -Math.PI / 2; hallG.add(centerTitle); centerTitle.visible = false;   // reemplazado por HALL_T
/* Beltrán 09-30: SOUL CHARGER / CENTER en dos líneas alineadas a la izquierda, al costado DERECHO de la puerta por la que
   nos acercamos (Oeste a la ida, Este a la vuelta), con la entrada y salida líquidas de los títulos. */
const HALL_T_GRAD = [[1, .9, .75], [.98, .78, .55], [.92, .66, .45], [.8, .55, .38]];
const HALL_T = { west: [], east: [] };
[['west', -1], ['east', 1]].forEach(([side, sg]) => ['SOUL CHARGER', 'CENTER'].forEach((txt, j) => {
  const m = titleMesh(txt, .3, HALL_T_GRAD, { px: 100, left: true }); m.rotation.y = sg * Math.PI / 2;
  m.position.set(sg * (HALL.rIn * 1.05 + .05), HALL.doorY + .22 - j * .4, -sg * (HALL.doorR + .35)); hallG.add(m); HALL_T[side].push(m); }));
function hallTitle(side, r, o) { HALL_T[side].forEach((m, j) => { const u = m.material.uniforms; u.uR.value = ease(clamp(r * 1.15 - j * .15)); u.uO.value = ease(o); m.visible = r > 0 && o < 1; }); }

/* Alma: ameba translúcida que respira y reacciona a su voz */
const BLOBS = [];
function blobMat(c, alpha = .85) {
  const bm = new THREE.ShaderMaterial({
    uniforms: { uT: { value: 0 }, uCol: { value: new THREE.Color(c) }, uAmp: { value: .12 }, uA: { value: alpha }, uGlow: { value: 0 } },
    vertexShader: `uniform float uT,uAmp; varying vec3 vN, vV; ${NOISE}
      void main(){ vec3 p=position; float n=vn(normalize(p)*2.3+vec3(uT*.35))-.5; p*=1.+n*uAmp*2.;
        vN=normalize(normalMatrix*normal); vec4 mv=modelViewMatrix*vec4(p,1.); vV=normalize(-mv.xyz); gl_Position=projectionMatrix*mv; }`,
    fragmentShader: `uniform vec3 uCol; uniform float uA,uGlow; varying vec3 vN,vV; void main(){ float f=pow(1.-abs(dot(vN,vV)),1.8);
      vec3 c=uCol*(.35+.9*f)+uCol*uGlow; gl_FragColor=vec4(c,clamp(uA*(.25+.85*f),0.,1.)); }`,
    transparent: true, depthWrite: false,
  }); BLOBS.push(bm); return bm;
}
const alma = new THREE.Mesh(new THREE.IcosahedronGeometry(.28, 4), blobMat('#ffc9af', .75)); alma.visible = false; scene.add(alma); alma.userData.s = 1;
const ALMA_SIZE = .5 / .28;   // look de la maqueta (Heart 09-30): Alma mide ~1 m (Size 0,6 -> 1), durazno tibio, Brightness 1,5
/* Alma habla (Beltrán 09-30): reactividad MUY notoria pero SUAVE — nunca picos: la envolvente sube en ~0,12 s y baja en ~0,35 s,
   con rodilla (raíz) y tope. Mueve el wobble, el color (más luminoso y un poco cálido) y +5 % de tamaño. La envuelve una esfera
   de partículas diminutas y muy translúcidas con curl noise, que se aviva cuando habla (la diferencia de la protoameba). */
const ALMA_COL0 = new THREE.Color('#ffc9af'), ALMA_COL1 = new THREE.Color('#ffddbc');   // CoreColor (1; 0,585; 0,426) lineal -> al hablar se entibia hacia (1; 0,72; 0,5)
const ALMA_SHELL = (() => { const N = 900, p = new Float32Array(N * 3), sd = new Float32Array(N);
  for (let k = 0; k < N; k++) { const u = Math.random() * 2 - 1, a = Math.random() * TAU, r = .36 + Math.random() * .16, q = Math.sqrt(1 - u * u);
    p[k * 3] = q * Math.cos(a) * r; p[k * 3 + 1] = u * r; p[k * 3 + 2] = q * Math.sin(a) * r; sd[k] = Math.random(); }
  const gm = new THREE.BufferGeometry(); gm.setAttribute('position', new THREE.BufferAttribute(p, 3)); gm.setAttribute('seed', new THREE.BufferAttribute(sd, 1));
  const m = new THREE.Points(gm, new THREE.ShaderMaterial({ uniforms: { uT: { value: 0 }, uE: { value: 0 } }, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    vertexShader: `attribute float seed; uniform float uT,uE; varying float vA,vS;
      vec3 fl(vec3 q,float t){ return vec3(sin(q.y*7.3+t*.9)+sin(q.z*5.1-t*.6), sin(q.z*6.7+t*.8)+sin(q.x*4.9+t*.5), sin(q.x*7.9-t*.7)+sin(q.y*5.3+t*.4)); }
      void main(){ float t=uT*(.35+1.1*uE)+seed*40.; vec3 q=position; vec3 f=fl(q*3.,t); q+=.035*(1.+1.4*uE)*cross(f,normalize(q)+.3*f);
        q*=1.+.06*uE*sin(t*2.+seed*9.); vec4 mv=modelViewMatrix*vec4(q,1.); gl_Position=projectionMatrix*mv; gl_PointSize=clamp((.8+.9*seed)*(9./-mv.z),1.,3.);
        vA=(.10+.22*uE)*(.4+.6*seed); vS=seed; }`,
    fragmentShader: `varying float vA,vS; void main(){ float r=length(gl_PointCoord-.5)*2.; gl_FragColor=vec4(mix(vec3(1.,.97,.94),vec3(1.,.91,.81),vS),vA*max(0.,1.-r*r)); }` }));   // aura de Heart (09-30): ColA 1/0,94/0,86 -> ColB 1/0,80/0,62 (lineal)
  m.frustumCulled = false; m.renderOrder = 3; alma.add(m); return m; })();
const ALMA_V = { env: 0 };
function almaVoiceLevel(T) {   // con audio real: el nivel del bus de voz; si no, una envolvente de sílabas sintética
  if (typeof voiceLevel === 'function') { const v = voiceLevel(); if (v != null) return v; }
  return .55 + .45 * Math.abs(Math.sin(T * 5.1) * Math.sin(T * 2.3 + 1));
}
function tickAlmaVoice(T, dt) {
  const target = S.speaking ? Math.min(1, Math.sqrt(almaVoiceLevel(T))) * .9 : 0, tau = target > ALMA_V.env ? .12 : .35;
  ALMA_V.env += (target - ALMA_V.env) * (1 - Math.exp(-Math.max(dt, 1e-4) / tau));
  const e = ALMA_V.env, u = alma.material.uniforms;
  u.uAmp.value = .08 + .11 * e; u.uGlow.value = .12 + .18 * e;   // Brightness 1,5 de base u.uCol.value.copy(ALMA_COL0).lerp(ALMA_COL1, .55 * e);
  if (alma.visible) alma.scale.setScalar(Math.max(.01, alma.userData.s) * ALMA_SIZE * (1 + .05 * e));
  ALMA_SHELL.material.uniforms.uT.value = T; ALMA_SHELL.material.uniforms.uE.value = e;
}

/* timbre */
const bell = new THREE.Group(); bell.visible = false; scene.add(bell);
{
  const body = new THREE.Mesh(new THREE.CylinderGeometry(.11, .11, .05, 48), new THREE.MeshBasicMaterial({ color: 0x8a7462 }));
  body.rotation.x = Math.PI / 2; bell.add(body);
  const ring = new THREE.Mesh(new THREE.TorusGeometry(.125, .006, 8, 64), new THREE.MeshBasicMaterial({ color: 0xffc98a })); ring.position.z = .026; bell.add(ring);
  const fill = new THREE.Mesh(new THREE.RingGeometry(.13, .15, 64, 1, Math.PI / 2, .001), new THREE.MeshBasicMaterial({ color: 0xffe2b8, side: THREE.DoubleSide, transparent: true }));
  fill.position.z = .03; bell.add(fill); bell.userData = { body, fill, p: -1, pk: 0 };
}
const BELL_PRESS_DEPTH = .01, BELL_PRESS_TIME = .12;   // = BellPressDepth 1 cm / BellPressTime 0,12 s del Hall (09-30)
function setBellPress(t, dt) { const u = bell.userData; u.pk = t > u.pk ? Math.min(t, u.pk + dt / BELL_PRESS_TIME) : Math.max(t, u.pk - dt / BELL_PRESS_TIME); u.body.position.z = -BELL_PRESS_DEPTH * ease(u.pk); }
function setBellFill(p) { if (Math.abs(p - bell.userData.p) < .004 && (p > 0) === (bell.userData.p > 0)) return; bell.userData.p = p; const f = bell.userData.fill; f.geometry.dispose(); f.geometry = new THREE.RingGeometry(.13, .15, 64, 1, Math.PI / 2, Math.max(.001, -p * TAU)); }

/* el sensor (motion controller) */
function controllerModel(mat) { // el provisorio (se reemplaza por SM_QuestCtrl_SC cuando carga)
  const g = new THREE.Group();
  const grip = new THREE.Mesh(new THREE.CylinderGeometry(.018, .022, .11, 20), mat); grip.rotation.x = .35; g.add(grip);
  const ring = new THREE.Mesh(new THREE.TorusGeometry(.045, .008, 10, 40), mat); ring.position.set(0, .06, -.02); ring.rotation.x = 1.2; g.add(ring);
  const trig = new THREE.Mesh(new THREE.BoxGeometry(.012, .02, .02), mat.clone()); trig.position.set(0, .02, -.03); g.add(trig);
  g.userData.trig = trig;
  g.userData.look = (color, op, trigOn) => { g.children.forEach(m => { m.material.color.set(color); m.material.opacity = op; }); trig.material.opacity = op * (trigOn ? 1.6 : .6); };
  g.userData.press = () => {}; return g;
}
const sensorMat = new THREE.MeshBasicMaterial({ color: 0xd9dde8 });
const sensor = controllerModel(sensorMat); sensor.visible = false; scene.add(sensor);
// orbe del mando (BP_SensorOrb_SC, Hall 09-30): r 14 cm, blanco azulado, nucleo .06 / borde .55; estalla al tomar el mando
const sensorOrb = new THREE.Mesh(new THREE.SphereGeometry(.14, 32, 16), new THREE.ShaderMaterial({ uniforms: { uA: { value: 0 } }, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
  vertexShader: `varying vec3 vN,vV; void main(){ vec4 mv=modelViewMatrix*vec4(position,1.); vN=normalize(normalMatrix*normal); vV=normalize(-mv.xyz); gl_Position=projectionMatrix*mv; }`,
  fragmentShader: `uniform float uA; varying vec3 vN,vV; void main(){ float f=pow(1.-abs(dot(normalize(vN),normalize(vV))),2.2); gl_FragColor=vec4(mix(vec3(.85,.92,1.),vec3(.9,.95,1.),f),(.06+.49*f)*uA); }` }));
sensorOrb.visible = false; sensorOrb.renderOrder = 40; scene.add(sensorOrb);
function applySensorOrb(o, at) { sensorOrb.visible = !!o && o.a > .005; if (!sensorOrb.visible) return; if (at) sensorOrb.position.copy(at); sensorOrb.scale.setScalar(o.s); sensorOrb.material.uniforms.uA.value = o.a; }
const sensorHalo = new THREE.Mesh(new THREE.TorusGeometry(.09, .003, 8, 64), new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: .6 }));
sensor.add(sensorHalo);

/* las cinco almas candidatas + el alma elegida dentro de su anillo (el contenedor) */
/* las 5 protoamebas, desaturadas para entrar en la paleta de la obra (Beltrán 09-30): el Core de cada BP_ProtoSoul_SC del
   Hall en Unreal (S×0,55 en HSV; la verde girada a 150°), pasado a sRGB. Antes: #8fb4ff #ff9fb2 #c7a6ff #ffc98a #93e6c0 */
const CAND_COLS = ['#caecff', '#ffd2e5', '#e5d2ff', '#ffe6c1', '#b1edd2'];
const cands = STAGES.map((st, i) => { const m = new THREE.Mesh(new THREE.IcosahedronGeometry(.07, 3), blobMat(CAND_COLS[i], .9)); m.visible = false; scene.add(m); return m; });
const container = new THREE.Group(); container.visible = false; scene.add(container);
const soul = new THREE.Mesh(new THREE.IcosahedronGeometry(.065, 3), blobMat(CAND_COLS[0], .9)); container.add(soul);
const ringG = new THREE.Group(); container.add(ringG);
ringG.add(new THREE.Mesh(new THREE.TorusGeometry(.12, .012, 12, 96), new THREE.MeshBasicMaterial({ color: 0x3a3c44 })));
const cavities = STAGES.map((st, i) => {
  const a = Math.PI / 2 + i * TAU / 5; // antihorario desde arriba
  const m = new THREE.Mesh(new THREE.SphereGeometry(.013, 12, 8), new THREE.MeshBasicMaterial({ color: new THREE.Color(st.color), transparent: true }));
  m.position.set(Math.cos(a) * .12, Math.sin(a) * .12, .012); ringG.add(m); m.userData.v = 0; return m;
});
container.traverse(o => { if (o.material) { o.material.depthTest = false; o.renderOrder = 65; } });
function setCavity(i, v) { const c = cavities[i]; c.userData.v = v; c.material.color.set(STAGES[i].color).multiplyScalar(.12 + .88 * v); c.scale.setScalar(.8 + .5 * v); ringU.uCharge.value[i] = v <= .125 ? 0 : clamp(v); }

/* ============ MODELOS REALES: los GLB que se exportan de los .blend de la obra (ver README.md de esta carpeta) ============
   Cada objeto de la obra tiene su lugar; mientras no llega el modelo real se ve el provisorio de arriba. */
const MODELS = { ring: null };
/* el GLB viaja envuelto en JSON (modelos/<archivo>.glb.json) porque los artifacts no sirven .glb */
function loadGLB(file) {
  return fetch('modelos/' + file + '.json').then(r => { if (!r.ok) throw new Error(r.status); return r.json(); }).then(j => new Promise((res, rej) => {
    if (!THREE.GLTFLoader) return rej(new Error('sin GLTFLoader'));
    const s = atob(j.b64), u8 = new Uint8Array(s.length); for (let i = 0; i < s.length; i++) u8[i] = s.charCodeAt(i);
    new THREE.GLTFLoader().parse(u8.buffer, '', g => res(g.scene), rej);
  }));
}
/* SM_ChargeRing_SC: el anillo contenedor. Mismo contrato que en Unreal: en el piso de las cavidades U = etapa + t,
   y la carga de cada etapa (0..1) llena su cavidad en el sentido de avance. */
const ringU = { uCharge: { value: [0, 0, 0, 0, 0] }, uCol: { value: STAGES.map(s => new THREE.Color(s.color)) }, uPastel: { value: .3 },
  uEmpty: { value: .1 }, uFull: { value: .9 }, uEdge: { value: .015 }, uFront: { value: .6 } };
const RING_LIGHT = new THREE.ShaderMaterial({ uniforms: ringU, depthTest: false, depthWrite: false,
  vertexShader: `varying vec2 vUv; void main(){ vUv=uv; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.); }`,
  fragmentShader: `uniform float uCharge[5]; uniform vec3 uCol[5]; uniform float uPastel,uEmpty,uFull,uEdge,uFront; varying vec2 vUv;
    void main(){ float u=clamp(vUv.x,0.,4.999); float st=floor(u), t=u-st; float ch=0.; vec3 col=vec3(1.);
      for(int i=0;i<5;i++){ if(float(i)==st){ ch=uCharge[i]; col=uCol[i]; } }
      col=mix(col,vec3(1.),uPastel); float lit=1.-smoothstep(ch-uEdge,ch+uEdge,t);
      float front=(ch>0.001&&ch<.999)?exp(-pow((t-ch)/(uEdge*3.),2.))*uFront:0.;
      gl_FragColor=vec4(col*(uEmpty+(uFull-uEmpty)*lit)+col*front,1.); }` });
const RING_FRAME = new THREE.ShaderMaterial({ depthTest: false, depthWrite: false,
  vertexShader: `varying vec3 vN,vV; void main(){ vN=normalize(normalMatrix*normal); vec4 mv=modelViewMatrix*vec4(position,1.); vV=normalize(-mv.xyz); gl_Position=projectionMatrix*mv; }`,
  // Beltrán 09-30: el cuerpo del anillo deja el metal oscuro y pasa al HORMIGÓN claro de la familia (timbre, SAVE, sensor; Mesh 3D)
  fragmentShader: `varying vec3 vN,vV; void main(){ vec3 n=normalize(vN), l=normalize(vec3(-.3,.8,.5)); float d=max(dot(n,l)*.6+.4,0.);
    float sp=pow(max(dot(reflect(-l,n),vV),0.),24.);
    vec3 c=vec3(.725,.698,.655)*(.3+.65*d)+vec3(1.)*sp*.06; gl_FragColor=vec4(c,1.); }` });
function installRing(root) {
  const meshes = []; root.traverse(o => { if (o.isMesh) meshes.push(o); });
  const holder = new THREE.Group(); holder.add(root);
  // la cara del anillo mira a +X en Blender: se gira para que mire a la cámara (+Z)
  root.rotation.y = Math.PI / 2; root.scale.setScalar(.6);
  meshes.forEach(m => { const name = (m.material && m.material.name) || '';
    m.material = /Light/i.test(name) ? RING_LIGHT : RING_FRAME; m.renderOrder = 66; m.frustumCulled = false; });
  // si la etapa 0 (U en 0..1) no queda arriba a la izquierda vista de frente, se da vuelta el anillo
  holder.updateMatrixWorld(true); let sx = 0, n = 0;
  meshes.forEach(m => { const uv = m.geometry.attributes.uv, p = m.geometry.attributes.position; if (!uv || m.material !== RING_LIGHT) return;
    const v = new THREE.Vector3(); for (let i = 0; i < uv.count; i += 7) if (uv.getX(i) < 1) { v.fromBufferAttribute(p, i).applyMatrix4(m.matrixWorld); sx += v.x; n++; } });
  if (n && sx / n > 0) root.rotation.y = -Math.PI / 2;
  ringG.children.forEach(c => c.visible = false);        // se va el provisorio
  ringG.add(holder); MODELS.ring = holder;
  // las cavidades quedan como puntos invisibles donde llega la luz de cada carga
  const R = .23 * .6 * .74;
  cavities.forEach((c, i) => { const a = (126 + i * 72) * Math.PI / 180; c.position.set(Math.cos(a) * R, Math.sin(a) * R, 0); c.visible = false; });
}
loadGLB('SM_ChargeRing_SC.glb').then(installRing).catch(e => console.warn('Anillo real no cargado:', e && e.message));
cavities.forEach((c, i) => setCavity(i, 0));

/* HUD: nace frente a la cara, abajo; el anillo con la ameba se ancla ahí */
const hudPanel = new THREE.Group(); hudPanel.position.set(0, -.34, -.9); hud.add(hudPanel); hudPanel.visible = false;
const eegPts = new Float32Array(48 * 3); const eegGeo = new THREE.BufferGeometry(); eegGeo.setAttribute('position', new THREE.BufferAttribute(eegPts, 3));
const eeg = new THREE.Line(eegGeo, new THREE.LineBasicMaterial({ color: 0xbfd0ff, transparent: true, opacity: .8 })); eeg.position.set(.02, 0, 0); hudPanel.add(eeg);
const heartDot = new THREE.Mesh(new THREE.CircleGeometry(.008, 20), new THREE.MeshBasicMaterial({ color: 0xff7a8a })); heartDot.position.set(.2, 0, 0); hudPanel.add(heartDot);
const hudAnchor = new THREE.Object3D(); hudAnchor.position.set(-.12, 0, 0); hudPanel.add(hudAnchor);
hudPanel.children.forEach(c => { if (c.material) { c.material.depthTest = false; c.renderOrder = 60; } });

/* ondas de calibración */
const calib = [0, 1, 2].map(i => { const m = new THREE.Mesh(new THREE.TorusGeometry(1.1, .004, 6, 96), new THREE.MeshBasicMaterial({ color: 0xe6ecff, transparent: true, opacity: 0 })); m.rotation.x = Math.PI / 2; scene.add(m); return m; });

/* ============ velo de color (esfera de 50 m que sigue a la cámara) ============ */
const veilU = { uTop: { value: new THREE.Color() }, uHor: { value: new THREE.Color() }, uAmt: { value: 0 }, uT: { value: 0 }, uVar: { value: 3 } };
const veil = new THREE.Mesh(new THREE.SphereGeometry(50, 48, 24), new THREE.ShaderMaterial({
  uniforms: veilU,
  vertexShader: `varying vec3 vD; void main(){ vD=normalize(position); gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.); }`,
  fragmentShader: `uniform vec3 uTop,uHor; uniform float uAmt,uT,uVar; varying vec3 vD;
    void main(){ float h=vD.y, t=uT; float n1=sin(vD.x*2.3+t*.05)*sin(vD.z*1.9-t*.037); vec3 c;
      if(uVar<.5) c=mix(uHor,uTop,smoothstep(-.35,.95,h+.1*n1));
      else if(uVar<2.5){ float k=.5+.28*n1+.25*h; c=mix(uHor,uTop,clamp(k,0.,1.)); vec3 mid=.5*(uHor+uTop);
        float lm=dot(mid,vec3(.2126,.7152,.0722)), lc=max(dot(c,vec3(.2126,.7152,.0722)),1e-4); c*=lm/lc; }
      else c=mix(uHor,uTop,.45);
      c=max(c,vec3(.02)); float a=uAmt*1.6-.35; gl_FragColor=vec4(c,smoothstep(0.,1.,clamp(a,0.,1.))); }`,
  side: THREE.BackSide, transparent: true, depthTest: false, depthWrite: false,
}));
veil.renderOrder = 50; scene.add(veil);
function outsideColor() { return col(STAGES[0].hor).lerp(col(STAGES[0].top), .45); }   // = el velo de Entering en su variante plana
function setVeilColors(a, b, k) { veilU.uTop.value.copy(col(a.top)).lerp(col(b.top), k); veilU.uHor.value.copy(col(a.hor)).lerp(col(b.hor), k); }


/* el aliento de ENTERING (Breath, 2026-09-29): cono de ±18° × ±8° frente a la boca, de 40 a 95 cm; inhalar trae las
   motas hacia la boca y exhalar es el espejo exacto (mismo volumen, mismo tamaño, sin crecer); va pegado a la cabeza */
const aliento = (() => {
  const N = 420, dir = new Float32Array(N * 3), sd = new Float32Array(N);
  for (let k = 0; k < N; k++) { const az = (Math.random() * 2 - 1) * 18 * Math.PI / 180, el = (Math.random() * 2 - 1) * 8 * Math.PI / 180;
    dir[k * 3] = Math.sin(az) * Math.cos(el); dir[k * 3 + 1] = Math.sin(el); dir[k * 3 + 2] = -Math.cos(az) * Math.cos(el); sd[k] = Math.random(); }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(dir, 3)); g.setAttribute('seed', new THREE.BufferAttribute(sd, 1));
  const u = { uPhase: { value: 0 }, uAmt: { value: 0 }, uT: { value: 0 } };
  const m = new THREE.Points(g, new THREE.ShaderMaterial({ uniforms: u, transparent: true, depthWrite: false, depthTest: false, blending: THREE.AdditiveBlending,
    vertexShader: `attribute float seed; uniform float uPhase,uT; varying float vA; void main(){ float k=fract(seed+uPhase); float r=mix(.40,.95,k);
      vec3 q=vec3(0.,-.08,0.)+normalize(position)*r; q.x+=sin(uT*1.3+seed*40.)*.01; q.y+=sin(uT*1.1+seed*23.)*.01;
      vec4 mv=modelViewMatrix*vec4(q,1.); gl_Position=projectionMatrix*mv; gl_PointSize=2.2*(1./-mv.z)*2.; vA=smoothstep(0.,.15,k)*smoothstep(1.,.85,k); }`,
    fragmentShader: `uniform float uAmt; varying float vA; void main(){ float d=smoothstep(.5,0.,length(gl_PointCoord-.5)); gl_FragColor=vec4(vec3(.85,.9,1.),d*vA*uAmt*.55); }` }));
  m.frustumCulled = false; m.renderOrder = 55; camera.add(m); return { m, u };
})();

/* ============ el Centro: cinco entornos en el mismo punto ============ */
const CENTER = new THREE.Vector3(24, 0, 0); // detrás de la puerta Este y el umbral oscuro
const envs = STAGES.map(() => { const g = new THREE.Group(); g.position.copy(CENTER); g.visible = false; scene.add(g); return g; });
const TRAVEL_V = .25, TRAVEL_IN = 4, TRAVEL_OUT = 2;   // Mind 09-30: TravelSpeed 25 cm/s, TravelEase 4 s, TravelEaseOut 2 s
function travelDist(L, D) { const sI = x => { const u = clamp(x / TRAVEL_IN); return TRAVEL_IN * (u * u * u - u * u * u * u / 2); }; const a = Math.min(L, D), m = clamp(L - D, 0, TRAVEL_OUT), w = m / TRAVEL_OUT;
  const inP = a < TRAVEL_IN ? sI(a) : TRAVEL_IN / 2 + (a - TRAVEL_IN); return TRAVEL_V * (inP + (m - TRAVEL_OUT * (w * w * w - w * w * w * w / 2))); }
const envU = STAGES.map(() => ({ uTravel: { value: 0 }, uT: { value: 0 }, uSwellT: { value: 0 }, uAmt: { value: 1 }, uBreath: { value: 0 }, uBeat: { value: -100 }, uCalm: { value: .5 }, uMandala: { value: 0 }, uGround: { value: new THREE.Color(1, 1, 1) } }));
function addSky(i, top, hor) { const m = new THREE.Mesh(new THREE.SphereGeometry(600, 48, 24), skyMat(top, hor, 1)); m.material.uniforms.uAmt = envU[i].uAmt; m.material.uniforms.uT = envU[i].uT; envs[i].add(m); envs[i].userData.sky = m; return m; }
function groundMat(i, frag) {
  return new THREE.ShaderMaterial({ uniforms: envU[i],
    vertexShader: `uniform float uT,uSwellT,uBreath,uBeat,uMandala; varying vec3 vP; varying float vH; ${NOISE}
      void main(){ vec3 p=position; ${frag.vs || ''} vP=p; gl_Position=projectionMatrix*modelViewMatrix*vec4(p,1.); }`,
    fragmentShader: `uniform float uT,uAmt,uBreath,uBeat,uCalm,uMandala; uniform vec3 uGround; varying vec3 vP; varying float vH; ${NOISE} void main(){ ${frag.fs} gl_FragColor=vec4(c*uGround*uAmt,1.); }` });
}
/* E1 · el valle */
{
  const i = 0; addSky(i, [.18, .27, .52], [.52, .58, .82]);
  const g = new THREE.PlaneGeometry(420, 420, 160, 160); g.rotateX(-Math.PI / 2);
  envs[i].add(new THREE.Mesh(g, groundMat(i, {
    vs: `float d=length(p.xz); float per=mix(20.,40.,vn(p*.013)); float br=1.+.45*sin(6.2831*uSwellT/per+vn(p*.01)*6.);
      float swP=mix(15.,23.,vn(p*.005)); float sw=sin(6.2831*uSwellT/swP+p.x*.02+p.z*.013)*4.5*smoothstep(90.,180.,d);   // uSwellT: el oleaje corre ~3x al exhalar (Beltrán 09-30)
      p.y+=(vn(p*.02)*18.*br+vn(p*.07)*4.)*smoothstep(8.,60.,d)+sw-1.2; vH=p.y;`,
    fs: `float d=length(vP.xz); vec3 lo=vec3(.10,.14,.30), hi=vec3(.42,.47,.72); vec3 c=mix(lo,hi,smoothstep(-2.,16.,vH));
      float fog=smoothstep(30.,190.,d)*(.7+.3*uBreath); c=mix(c,vec3(.55,.6,.84),fog);`,
  })));
  // metaball: seis gotas que se juntan al inhalar y se separan al exhalar
  const blob = new THREE.Group(); blob.position.set(4.5, EYE - .1, 0); blob.visible = false; envs[i].add(blob); envs[i].userData.blob = blob;
  for (let k = 0; k < 6; k++) { const m = new THREE.Mesh(new THREE.IcosahedronGeometry(.16, 3), blobMat('#9fb6ff', .8)); m.userData.a = k / 6 * TAU; blob.add(m); }
  // pacer: dos aros guía
  const pacer = new THREE.Group(); pacer.position.set(4.3, EYE - .1, 0); pacer.rotation.y = Math.PI / 2; envs[i].add(pacer); envs[i].userData.pacer = pacer;
  // polvo ambiente del valle: 6144 motas de 1,3 a 110 m (Breath, 2026-09-29)
  { const N = 6144, p = new Float32Array(N * 3), sd = new Float32Array(N);
    for (let k = 0; k < N; k++) { const r = 1.3 * Math.pow(110 / 1.3, Math.random()), a = Math.random() * TAU, y = (Math.random() - .35) * Math.min(r, 30) * .5;
      p[k * 3] = Math.cos(a) * r; p[k * 3 + 1] = EYE + y; p[k * 3 + 2] = Math.sin(a) * r; sd[k] = Math.random(); }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(p, 3)); g.setAttribute('seed', new THREE.BufferAttribute(sd, 1));
    const m = new THREE.Points(g, new THREE.ShaderMaterial({ uniforms: envU[i], transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
      vertexShader: `attribute float seed; uniform float uT,uBreath; varying float vA; void main(){ vec3 q=position; q.y+=sin(uT*.07+seed*30.)*.6; q.x+=sin(uT*.05+seed*17.)*.8;
        vec4 mv=modelViewMatrix*vec4(q,1.); gl_Position=projectionMatrix*mv; float z=-mv.z; gl_PointSize=clamp((1.+seed)*(30./z),1.,4.); vA=(.25+.35*seed)*smoothstep(.8,2.5,z)*(1.-smoothstep(60.,110.,z))*(.75+.25*uBreath); }`,
      fragmentShader: `uniform float uAmt; varying float vA; void main(){ float d=smoothstep(.5,0.,length(gl_PointCoord-.5)); gl_FragColor=vec4(vec3(.82,.86,1.),d*vA*uAmt); }` }));
    m.frustumCulled = false; envs[i].add(m); envs[i].userData.valleyDust = m; }
  [0, 1].forEach(k => pacer.add(new THREE.Mesh(new THREE.TorusGeometry(.55 + k * .12, .004, 6, 96), new THREE.MeshBasicMaterial({ color: 0xe9eeff, transparent: true, opacity: 0 }))));
}
/* E2 · la membrana del latido */
{
  const i = 1; addSky(i, [.40, .30, .31], [.95, .85, .83]);   // blanco-rojizo, surreal (Beltrán, 09-30): el azul es de la respiración
  const g = new THREE.PlaneGeometry(400, 400, 220, 220); g.rotateX(-Math.PI / 2);
  envs[i].add(new THREE.Mesh(g, groundMat(i, {
    vs: `float d=length(p.xz-vec2(4.,0.)); float age=uT-uBeat; float w=exp(-pow(d-age*3.2,2.)*.35)*exp(-age*.45); p.y=-.9-w*.35-exp(-d*d*.5)*.25*exp(-age*2.)*step(0.,age); vH=w;`,
    fs: `float d=length(vP.xz); vec3 c=mix(vec3(.34,.22,.23),vec3(.97,.82,.80),smoothstep(0.,.3,vH)+.12*vn(vP*.4));
      c=mix(c,vec3(.80,.66,.66),smoothstep(20.,160.,d));`,
  })));
  const heart = new THREE.Mesh(new THREE.IcosahedronGeometry(.3, 4), blobMat('#ffd3cd', .85)); heart.position.set(4, -.2, 0); envs[i].add(heart); envs[i].userData.heart = heart;
  const orbs = []; for (let k = 0; k < 14; k++) { const m = new THREE.Mesh(new THREE.IcosahedronGeometry(.18, 2), blobMat('#ffe2dc', .6)); m.visible = false; envs[i].add(m); orbs.push(m); } envs[i].userData.orbs = orbs;
}
/* E3 · el fluido cerebral y la célula */
{
  const i = 2; addSky(i, [.0369, .0273, .0482], [.0176, .0130, .0232]); // morado poco saturado = el fluido de Test_Fluid (Mind, 09-30: arriba #362E3E, medio #241E2A; lineal)
  const N = 1800, geo = new THREE.BufferGeometry(), p = new Float32Array(N * 3);
  for (let k = 0; k < N; k++) { const r = 2 + Math.random() * 22, a = Math.random() * TAU, y = (Math.random() - .5) * 14; p[k * 3] = Math.cos(a) * r; p[k * 3 + 1] = y + EYE; p[k * 3 + 2] = Math.sin(a) * r; }
  geo.setAttribute('position', new THREE.BufferAttribute(p, 3));
  const motes = new THREE.Points(geo, new THREE.ShaderMaterial({ uniforms: envU[i],
    vertexShader: `uniform float uT,uCalm,uTravel; varying float vA; void main(){ vec3 q=position; q.x=mod(q.x-uTravel+24.,48.)-24.; float sp=mix(4.5,.5,uCalm);   // Beltrán 09-30: con actividad todo el mundo se activa (antes 1,8)
      float a=uT*.05*sp+q.y*.1; q.xz=mat2(cos(a),-sin(a),sin(a),cos(a))*q.xz; q.y+=sin(uT*.3*sp+q.x)*.4;
      vec4 mv=modelViewMatrix*vec4(q,1.); gl_Position=projectionMatrix*mv; gl_PointSize=2.2*(40./-mv.z); vA=smoothstep(30.,2.,-mv.z); }`,
    fragmentShader: `uniform float uCalm; varying float vA; void main(){ float d=smoothstep(.5,0.,length(gl_PointCoord-.5));
      gl_FragColor=vec4(mix(vec3(.62,.56,.72),vec3(.867,.792,.902),uCalm),d*vA*.7); }`, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending }));   // motas #DDCAE6 (Mind)
  motes.frustumCulled = false; envs[i].add(motes);
  // la célula centrada al frente, a 2 m del usuario (Test_Fluid: 200/0/115, yaw 180; Mind 09-30)
  const cell = new THREE.Group(); cell.position.set(2.0, EYE - .05, 0); cell.visible = false; envs[i].add(cell); envs[i].userData.cell = cell;
  const nucleus = new THREE.Mesh(new THREE.IcosahedronGeometry(.28, 4), blobMat('#e8d8f0', .9)); cell.add(nucleus);   // membrana (Mind)
  const limbs = []; for (let k = 0; k < 5; k++) { const m = new THREE.Mesh(new THREE.IcosahedronGeometry(.12, 3), blobMat('#bfa2d5', .75)); m.userData.a = k / 5 * TAU; cell.add(m); limbs.push(m); }   // borde (Mind)
  cell.userData.limbs = limbs; cell.userData.nucleus = nucleus;
  for (let k = 0; k < 7; k++) { const a = k / 7 * TAU + .4, r = 1.6 + (k % 3) * .7, m = new THREE.Group(); m.position.set(Math.cos(a) * r + 1.2, EYE + (k % 2 ? .5 : -.35) + (k % 3) * .2, Math.sin(a) * r);
    const R = .09 + (k % 3) * .025, mem = new THREE.Mesh(new THREE.IcosahedronGeometry(R, 3), blobMat('#c0accc', .22)); m.add(mem);   // membrana CellHigh #C0ACCC, 0,19 al centro → 0,75 en el Fresnel (Mind 09-30)
    const core = new THREE.Mesh(new THREE.IcosahedronGeometry(R * (k % 3 ? .45 : .5), 2), blobMat('#8f7f99', .85)); m.add(core); envs[i].add(m); m.userData.x0 = m.position.x; (envs[i].userData.mids = envs[i].userData.mids || []).push(m); }   // núcleo perla difuso (luz #C0ACCC, sombra #342A3E)
}
/* E4 · el salar de Chladni, el gusano y el domo de esferas */
{
  const i = 3; addSky(i, [.863, .745, .631], [.973, .815, .565]);   // Uyuni desaturado = Test_Sequencer (Secuencer 09-30: SkyTop #efe0d0, SkyHorizon #fce9c6; lineal)
  const g = new THREE.PlaneGeometry(300, 300, 200, 200); g.rotateX(-Math.PI / 2);
  envs[i].add(new THREE.Mesh(g, groundMat(i, {
    vs: `float d=length(p.xz), a=atan(p.z,p.x); float m=cos(5.*a+d*.9)*sin(d*1.3-uT*.4)*exp(-d*.06)*0.; p.y=-1.1+m*.12*uMandala; vH=m*uMandala;`,   // piso apagado (Beltrán, 09-30): sin patrón ni movimiento; se retoma
    fs: `float d=length(vP.xz); vec3 salt=vec3(.95,.86,.82), dusk=vec3(.62,.55,.72); vec3 c=mix(salt,dusk,smoothstep(8.,120.,d));
      c=vec3(1.,.98,.949); c*=.97+.03*vn(vP*1.3);`,   // sal lisa SaltLit #fffaf2 (FloorPattern false)
  })));
  // gusano: ocho gotas = ocho pasos (slots)
  const worm = []; for (let k = 0; k < 8; k++) { const a = (k / 7 - .5) * 1.4; const m = new THREE.Mesh(new THREE.IcosahedronGeometry(.05, 3), blobMat('#e5c6a3', .85));
    m.position.set(1.25 - Math.cos(a) * .25, EYE - .45, Math.sin(a) * 1.1); m.userData.slot = k; m.visible = false; envs[i].add(m); worm.push(m); }
  envs[i].userData.worm = worm;
  // domo: 68 esferas (20 sonidos)
  const orbs = []; for (let k = 0; k < 68; k++) { const ph = Math.acos(1 - (k + .5) / 68 * .9), th = k * 2.39996;
    const r = 7.5, m = new THREE.Mesh(new THREE.IcosahedronGeometry(.16, 2), blobMat(['#f6e2b8', '#f3d0ac', '#fbeedb', '#eec6a0'][k % 4], .9));   // Color1-4 de las esferas (Secuencer, Uyuni)
    m.position.set(Math.abs(Math.cos(th) * Math.sin(ph) * r) + 1.5, EYE + Math.cos(ph) * r * .55 + .4, Math.sin(th) * Math.sin(ph) * r);
    m.userData = { note: k % 20, home: m.position.clone(), state: 'home' }; m.visible = false; envs[i].add(m); orbs.push(m); }
  envs[i].userData.orbs = orbs;
  var ORB_HALO_T = window.ORB_HALO_T = { value: 0 };
  // halo de cada esfera (Secuencer 09-30): cáscara de partículas muy chicas y translúcidas de su color, a 1,3× su radio, con curl
  // noise suave; al agarrarla se empujan hacia afuera y se apagan (0,9 s); al volver a casa reaparece (1,6 s); en el gusano no tiene
  { const N = 60, p = new Float32Array(N * 3), sd = new Float32Array(N);
    for (let k = 0; k < N; k++) { const u = Math.random() * 2 - 1, a = Math.random() * TAU, q = Math.sqrt(1 - u * u), r = .19 + Math.random() * .05;
      p[k * 3] = q * Math.cos(a) * r; p[k * 3 + 1] = u * r; p[k * 3 + 2] = q * Math.sin(a) * r; sd[k] = Math.random(); }
    const gm = new THREE.BufferGeometry(); gm.setAttribute('position', new THREE.BufferAttribute(p, 3)); gm.setAttribute('seed', new THREE.BufferAttribute(sd, 1));
    orbs.forEach((o, k) => { const u = { uT: ORB_HALO_T, uA: { value: 0 }, uPush: { value: 0 }, uCol: { value: o.material.uniforms.uCol.value.clone() } };
      const h = new THREE.Points(gm, new THREE.ShaderMaterial({ uniforms: u, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
        vertexShader: `attribute float seed; uniform float uT,uPush; varying float vA;
          void main(){ float t=uT*.45+seed*30.; vec3 q=position; vec3 f=vec3(sin(q.y*21.+t),sin(q.z*19.-t*.8),sin(q.x*23.+t*.6)); q+=.012*cross(f,normalize(q));
            q*=1.+1.4*uPush*(.6+.4*seed); vec4 mv=modelViewMatrix*vec4(q,1.); gl_Position=projectionMatrix*mv; gl_PointSize=clamp((.6+.6*seed)*(6./-mv.z),1.,2.5); vA=.35+.65*seed; }`,
        fragmentShader: `uniform float uA; uniform vec3 uCol; varying float vA; void main(){ float r=length(gl_PointCoord-.5)*2.; gl_FragColor=vec4(uCol,.28*uA*vA*max(0.,1.-r*r)); }` }));
      h.frustumCulled = false; o.add(h); o.userData.halo = h; o.userData.haloA = 1; }); }
}
/* E5 · el océano del dibujo y la mesa */
{
  const i = 4; addSky(i, [.004, .005, .012], [.02, .03, .06]);
  const g = new THREE.PlaneGeometry(400, 400, 200, 200); g.rotateX(-Math.PI / 2);
  envs[i].add(new THREE.Mesh(g, groundMat(i, {
    vs: `p.y=-1.3+sin(p.x*.18+uT*.4)*.25+sin(p.z*.23-uT*.33)*.2+sin((p.x+p.z)*.5+uT*.7)*.06; vH=p.y+1.3;`,
    fs: `float d=length(vP.xz); vec3 c=mix(vec3(.03,.04,.12),vec3(.10,.12,.30),smoothstep(-.4,.5,vH)); c=mix(c,vec3(.02,.025,.06),smoothstep(20.,160.,d));`,
  })));
  const table = new THREE.Mesh(new THREE.CylinderGeometry(.4, .4, .03, 64), new THREE.MeshBasicMaterial({ color: 0x1b2036 }));
  table.position.set(.75, EYE - .62, 0); table.visible = false; envs[i].add(table); envs[i].userData.table = table;
  const strokes = new THREE.Group(); envs[i].add(strokes); envs[i].userData.strokes = strokes;
}
function showEnv(i, amt = 1) { envs.forEach((g, k) => g.visible = k === i); if (i >= 0) envU[i].uAmt.value = amt; }

/* ============ fantasma de las instrucciones: estela entrecortada ============ */
const ghostMat = new THREE.MeshBasicMaterial({ color: 0xcfe0ff, transparent: true, opacity: .55, depthWrite: false });
const ghostCopies = [];
for (let k = 0; k < 7 * 2; k++) { const m = controllerModel(ghostMat.clone()); m.visible = false; camera.add(m); ghostCopies.push(m); }
/* un gesto = lista de keyframes [t, [x,y,z] relativo a la cabeza, gatillo 0..1]; opcionalmente una segunda mano (b) */
const GESTURES = {
  GHOST_BELL: { dur: 4, a: [[0, [.25, -.45, -.3], 0], [1.3, [.02, -.28, -.52], 0], [1.6, [.0, -.28, -.56], 1], [3.4, [.0, -.28, -.56], 1], [4, [.2, -.4, -.35], 0]] },
  GHOST_TAKE: { dur: 3.5, a: [[0, [.28, -.45, -.25], 0], [1.6, [.02, -.25, -.55], 0], [2.2, [.02, -.25, -.55], 1], [3.5, [.22, -.35, -.3], 1]] },
  GHOST_PICK: { dur: 3.5, a: [[0, [.22, -.35, -.3], 0], [1.2, [.1, -.18, -.45], 0], [1.8, [.1, -.18, -.45], 1], [3.5, [.2, -.3, -.32], 0]] },
  GHOST_BREATH: { dur: 6, bio: true, a: [[0, [.2, -.3, -.35], 0], [1.5, [0, -.62, -.18], 0], [3.2, [0, -.58, -.24], 0], [4.8, [0, -.62, -.18], 0], [6, [0, -.6, -.2], 0]] },
  GHOST_HEART: { dur: 5, bio: true, a: [[0, [.22, -.3, -.35], 0], [1.6, [-.06, -.36, -.16], 0], [5, [-.06, -.36, -.16], 0]] },
  GHOST_ATTRACT: { dur: 5, a: [[0, [.2, -.3, -.35], 0], [1, [.2, -.15, -.4], 0], [1.5, [.2, -.15, -.4], 1], [3, [.05, -.35, -.5], 1], [3.8, [.05, -.35, -.5], 0], [5, [.2, -.3, -.35], 0]] },
  GHOST_DRAW: { dur: 5, a: [[0, [.18, -.35, -.35], 0], [1, [.12, -.42, -.55], 1], [2, [.02, -.36, -.6], 1], [3, [-.08, -.44, -.58], 1], [4, [-.02, -.5, -.55], 1], [5, [.18, -.35, -.35], 0]],
    b: [[0, [-.25, -.35, -.4], 0], [.6, [-.2, -.3, -.45], 0], [1, [-.2, -.3, -.45], 1], [5, [-.25, -.35, -.4], 0]] },
  GHOST_SAVE: { dur: 4, b: [[0, [-.22, -.38, -.38], 0], [.8, [-.2, -.32, -.42], 1], [3.2, [-.2, -.32, -.42], 1], [4, [-.22, -.38, -.38], 0]] },
};
function samplePath(keys, t) {
  let a = keys[0], b = keys[keys.length - 1];
  for (let k = 0; k < keys.length - 1; k++) if (t >= keys[k][0] && t <= keys[k + 1][0]) { a = keys[k]; b = keys[k + 1]; break; }
  const u = b[0] > a[0] ? smooth((t - a[0]) / (b[0] - a[0])) : 0;
  return { p: new THREE.Vector3(lerp(a[1][0], b[1][0], u), lerp(a[1][1], b[1][1], u), lerp(a[1][2], b[1][2], u)), trig: u < .5 ? a[2] : b[2] };
}
/* el fantasma en un tiempo local dado: determinista, así se ve igual al recorrer la línea de tiempo */
function drawGhost(id, local, color) {
  const P = GESTURES[id]; if (!P) return;
  const fps = S.tw.gfps, cyc = P.dur + 1, tq = (Math.floor(local * fps) / fps) % cyc, echoes = S.tw.gecho | 0, per = 7;
  const bio = P.bio && BIO.ghosts.length; (bio ? ghostCopies : BIO.ghosts).forEach(c => c.visible = false);
  ['a', 'b'].forEach((hk, hi) => {
    const keys = P[hk];
    for (let e = 0; e < per; e++) {
      const c = bio ? (hi ? null : BIO.ghosts[e]) : ghostCopies[hi * per + e]; if (!c) { if (bio) ghostCopies[hi * per + e].visible = false; continue; }
      if (!keys || e > echoes) { c.visible = false; continue; }
      const s = samplePath(keys, clamp(tq - e / fps, 0, P.dur));
      c.visible = tq <= P.dur + .5; c.position.set(s.p.x * 1.1, s.p.y * .45 + .02, s.p.z - .3); // encuadre de pantalla: en VR el usuario mira hacia abajo
      const op = [.6, .36, .21, .12, .07, .04, .02][e];
      c.userData.look(color, op, !!s.trig); if (bio) c.rotation.set(-Math.PI / 2 + .5, 0, 0);
    }
  });
}
function hideGhost() { ghostCopies.forEach(c => c.visible = false); BIO.ghosts.forEach(c => c.visible = false); }

/* SM_QuestCtrl_SC (Mesh 3D, aprobado por Beltrán 2026-09-29): el mando nuevo, a partir de la malla de Meta.
   Cuerpo negro con la tapa gris-blanca marcada en la UV1 "CapMask" (x > 0 = tapa); el gatillo gira sobre su bisagra
   +14° al apretar. Reemplaza al sensor provisorio y a los fantasmas de las instrucciones (derecho = a, izquierdo = b). */
const CTRL_AXIS = new THREE.Vector3(.976, -.008, -.218).normalize(); // eje de la bisagra (Blender .976 .218 -.008 → glTF)
function ctrlMaterial(ghost) {
  return new THREE.ShaderMaterial({ transparent: ghost, depthWrite: !ghost,
    uniforms: { uGhost: { value: ghost ? 1 : 0 }, uCol: { value: new THREE.Color(0xcfe0ff) }, uOp: { value: 1 }, uGlow: { value: 0 } },
    vertexShader: `attribute vec2 uv2; varying float vCap; varying vec3 vN,vV; void main(){ vCap=uv2.x; vN=normalize(normalMatrix*normal); vec4 mv=modelViewMatrix*vec4(position,1.); vV=normalize(-mv.xyz); gl_Position=projectionMatrix*mv; }`,
    fragmentShader: `uniform float uGhost,uOp,uGlow; uniform vec3 uCol; varying float vCap; varying vec3 vN,vV;
      void main(){ vec3 n=normalize(vN); float fr=pow(1.-abs(dot(n,vV)),2.);
        if(uGhost>.5){ gl_FragColor=vec4(uCol*(.55+.9*fr)+uCol*uGlow,uOp*(.35+.65*fr)); return; }
        vec3 l=normalize(vec3(-.3,.8,.5)); float d=max(dot(n,l),0.), sp=pow(max(dot(reflect(-l,n),vV),0.),32.);
        vec3 base=mix(vec3(.03,.032,.036),vec3(.80,.81,.83),step(0.,vCap));
        gl_FragColor=vec4(base*(.35+.7*d)+vec3(1.)*sp*.25+vec3(.5,.55,.65)*fr*.12,1.); }` });
}
function ctrlTemplate(meshes, side) {
  const body = meshes.find(m => m.name.includes('Body_' + side)), trig = meshes.find(m => m.name.includes('Trigger_' + side));
  if (!body || !trig) return null;
  return { body, trig };
}
function buildCtrl(tpl, ghost) {
  const g = new THREE.Group(), holder = new THREE.Group(); g.add(holder); holder.rotation.y = Math.PI;   // girado 180°: la cara del mando mira hacia adelante, no al usuario (Beltrán, 2026-09-30)
  const mb = ctrlMaterial(ghost), mt = ctrlMaterial(ghost);
  const body = new THREE.Mesh(tpl.body.geometry, mb); body.position.copy(tpl.body.position); body.quaternion.copy(tpl.body.quaternion); holder.add(body);
  const pivot = new THREE.Group(); pivot.position.copy(tpl.trig.position); holder.add(pivot);
  const trig = new THREE.Mesh(tpl.trig.geometry, mt); pivot.add(trig);
  if (ghost) { body.renderOrder = trig.renderOrder = 56; }
  g.userData = { real: true, mats: [mb, mt], trigMat: mt, pivot,
    press(k) { pivot.quaternion.setFromAxisAngle(CTRL_AXIS, k * 14 * Math.PI / 180); },
    look(color, op, trigOn) { mb.uniforms.uCol.value.set(color); mt.uniforms.uCol.value.set(color); mb.uniforms.uOp.value = op; mt.uniforms.uOp.value = op * (trigOn ? 1.6 : .8); mt.uniforms.uGlow.value = trigOn ? .5 : 0; this.press(trigOn ? 1 : 0); } };
  return g;
}
function swapModel(target, fresh) { // cambia el contenido de un grupo existente (conserva su posición, su halo y quién lo sigue)
  target.children.slice().forEach(ch => { if (ch !== sensorHalo) target.remove(ch); });
  fresh.children.slice().forEach(ch => target.add(ch)); target.userData = Object.assign(target.userData || {}, fresh.userData);
}
function installController(root) {
  const meshes = []; root.traverse(o => { if (o.isMesh) meshes.push(o); });
  const R = ctrlTemplate(meshes, 'R'), L = ctrlTemplate(meshes, 'L'); if (!R) throw new Error('faltan las mallas del mando');
  swapModel(sensor, buildCtrl(R, false));
  ghostCopies.forEach((c, k) => swapModel(c, buildCtrl(k < 7 || !L ? R : L, true)));
  MODELS.ctrl = { R, L };
}
loadGLB('SM_QuestCtrl_SC.glb').then(installController).catch(e => console.warn('Mando real no cargado:', e && e.message));

/* ============ entrada: mouse = mano ============ */
const ray = new THREE.Raycaster();
const cvs = renderer.domElement;
cvs.addEventListener('contextmenu', e => e.preventDefault());
cvs.addEventListener('pointermove', e => {
  const r = cvs.getBoundingClientRect(); S.mouse.set((e.clientX - r.left) / r.width * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
  if (S.rdown) { S.targetYaw -= e.movementX * .004; S.pitch = clamp(S.pitch - e.movementY * .003, -.9, .7); }
});
cvs.addEventListener('pointerdown', e => { if (e.button === 2) { S.rdown = true; return; } S.down = true; S.clicked = true; audioOn(); });
addEventListener('pointerup', e => { if (e.button === 2) S.rdown = false; else S.down = false; });
function pick(objs) { ray.setFromCamera(S.mouse, camera); const hits = ray.intersectObjects(objs.filter(o => o.visible), true); return hits.length ? hits[0] : null; }
function consumeClick() { const c = S.clicked; S.clicked = false; return c; }
function hover(obj) { return !!pick([obj]); }

/* ============ helpers de escena ============ */
const V = (x, y, z) => new THREE.Vector3(x, y, z);
/* una pose fija del pawn en el mundo: lo que se coloca "al frente" se calcula desde ella, no desde donde está la cámara */
function pose(x, z, yaw) { return { x, z, yaw, q: new THREE.Quaternion().setFromEuler(new THREE.Euler(0, yaw, 0)) }; }
function front(p, dist, dy = 0, side = 0) { const c = Math.cos(p.yaw), s = Math.sin(p.yaw); return V(p.x + side * c - dist * s, EYE + dy, p.z - side * s - dist * c); }
function rigTo(p) { rig.position.set(p.x, 0, p.z); rig.rotation.y = p.yaw; }
function inFront(dist, dy = 0, side = 0) { return rig.localToWorld(new THREE.Vector3(side, EYE + dy, -dist)); }
function attachSensor(on) { sensor.visible = on; sensorHalo.visible = !on; S.sensorOn = on; }

function buildCard() {
  const c = document.createElement('canvas'); c.width = 1600; c.height = 900; const g = c.getContext('2d');
  g.fillStyle = 'rgba(14,16,26,.92)'; g.fillRect(0, 0, 1600, 900); g.strokeStyle = 'rgba(233,183,127,.5)'; g.lineWidth = 3; g.strokeRect(20, 20, 1560, 860);
  g.fillStyle = '#e9ecf6'; g.font = '44px Michroma'; g.fillText('YOUR SOUL', 470, 110);
  const secs = [['BREATH', '#5d7fe0'], ['HEARTBEAT', '#e0566b'], ['CALM', '#9a6ee6'], ['MELODY', '#e8a04e'], ['DRAWING', '#4fc28f']];
  secs.forEach(([n, cl], i) => { const y = 170 + i * 140; g.fillStyle = cl; g.font = '26px Michroma'; g.fillText(n, 470, y + 28);
    g.strokeStyle = cl; g.lineWidth = 4; g.beginPath();
    if (i === 0) { const d = S.data.breath.length ? S.data.breath : Array.from({ length: 120 }, (_, k) => .5 + .45 * Math.sin(k / 9)); d.forEach((v, k) => g.lineTo(760 + k * (760 / d.length), y + 60 - v * 70)); }
    if (i === 1) { for (let k = 0; k < 40; k++) { const x = 760 + k * 19; g.lineTo(x, y + 30); g.lineTo(x + 4, y + (k % 2 ? -10 : 30)); g.lineTo(x + 8, y + 30); } }
    if (i === 2) { const d = S.data.calm.length ? S.data.calm : Array.from({ length: 80 }, (_, k) => .3 + .6 * (k / 80)); d.forEach((v, k) => g.lineTo(760 + k * (760 / d.length), y + 60 - v * 70)); }
    g.stroke();
    if (i === 3) { (S.data.melody.length ? S.data.melody : [-1, -1, -1, -1, -1, -1, -1, -1]).forEach((v, k) => { g.fillStyle = v >= 0 ? `hsl(${20 + v * 9},70%,65%)` : 'rgba(255,255,255,.15)'; g.beginPath(); g.arc(790 + k * 90, y + 30, 26, 0, TAU); g.fill(); }); }
    if (i === 4) { g.strokeStyle = cl; S.data.strokes.slice(-12).forEach(s => { g.beginPath(); s.forEach((p, k) => g.lineTo(1000 + p.x * 900, y + 40 - p.y * 300)); g.stroke(); }); if (!S.data.strokes.length) { g.fillStyle = 'rgba(255,255,255,.2)'; g.fillRect(760, y, 760, 80); } }
  });
  return new THREE.CanvasTexture(c);
}
const card = new THREE.Mesh(new THREE.PlaneGeometry(2, 1.125), new THREE.MeshBasicMaterial({ transparent: true, opacity: 0, depthWrite: false }));
card.renderOrder = 40; card.visible = false; scene.add(card);
function refreshCard() { if (card.material.map) card.material.map.dispose(); card.material.map = buildCard(); card.material.needsUpdate = true; }
/* la constelación: 21 luces en la niebla, la última (la tuya) queda vacía para que llegue tu alma */
function buildConstellation(p) {
  const g = new THREE.Group(); g.userData.k = 0; const mats = [];
  for (let k = 0; k < 21; k++) { const a = -.9 + k / 20 * 1.8, r = 7 + Math.sin(k * 3.1) * 2; const m = new THREE.Mesh(new THREE.SphereGeometry(.05 + (k % 3) * .02, 12, 8), new THREE.MeshBasicMaterial({ color: new THREE.Color().setHSL((k * .13) % 1, .5, .75), transparent: true, opacity: 0 }));
    const c = Math.cos(p.yaw), s = Math.sin(p.yaw), lx = Math.sin(a) * r, lz = -Math.cos(a) * r;
    m.position.set(p.x + lx * c + lz * s, EYE + .8 + Math.cos(k * 1.7) * 1.6, p.z - lx * s + lz * c); g.add(m); mats.push(m.material);
    if (k === 20) { g.userData.yours = m.position.clone(); m.visible = false; } }
  g.userData.mats = mats; g.visible = false; scene.add(g); return g;
}

/* ============ paleta / SAVE (la mano no dominante): se arma solo cuando cambia lo que se pide ============ */
const PAL = ['#f4f1ff', '#8fb4ff', '#ff9fb2', '#ffc98a', '#93e6c0', '#c7a6ff'];
let leftState = '';
function setLeftHand(palette, save) {
  if (PAL3.root) { PAL3.root.visible = !!palette; palette = false; }
  const key = (palette ? 'p' : '') + (save ? 's' : ''); if (key === leftState) return; leftState = key;
  const lh = $('#lefthand'); lh.innerHTML = ''; lh.hidden = !key;
  if (palette) { PAL.forEach((c, i) => { const b = document.createElement('button'); b.className = 'sw' + (c === (S.brush || PAL[1]) ? ' on' : ''); b.style.background = c; b.title = 'Color';
    b.onclick = () => { S.brush = c; lh.querySelectorAll('.sw').forEach(x => x.classList.remove('on')); b.classList.add('on'); cue('fx', 'FX_PALETTECLICK'); cue('hap', 'HAP_TICK'); }; lh.appendChild(b); }); S.brush = S.brush || PAL[1]; }
  if (save) { const b = document.createElement('button'); b.id = 'save'; b.innerHTML = '<div class="fill"></div><span>MANTENER · SAVE</span>';
    b.onpointerdown = () => { S.saveDown = true; cue('fx', 'FX_SAVEHOLD'); cue('hap', 'HAP_CHARGE_RAMP'); }; b.onpointerup = b.onpointerleave = () => { S.saveDown = false; };
    lh.appendChild(b); }
  else { S.saveDown = false; }
}

/* ============ secuenciador de ATTRACTING: 8 pasos, 5,333 s por vuelta ============ */
function tickOrbHalos(T, dt) {
  ORB_HALO_T.value = T;
  envs[3].userData.orbs.forEach(o => { const st = o.userData.state, u = o.userData.halo && o.userData.halo.material.uniforms; if (!u) return;
    if (st === 'home') { o.userData.haloA = Math.min(1, o.userData.haloA + dt / 1.6); u.uPush.value = Math.max(0, u.uPush.value - dt / .6); }
    else { o.userData.haloA = Math.max(0, o.userData.haloA - dt / .9); if (st === 'carry') u.uPush.value = Math.min(1, u.uPush.value + dt / .9); }
    u.uA.value = ease(o.userData.haloA); o.userData.halo.visible = u.uA.value > .01; });
}
function resetOrbs() { const orbs = envs[3].userData.orbs; orbs.forEach(o => { o.userData.state = 'home'; o.userData.slot = undefined; o.position.copy(o.userData.home); }); S.melody = new Array(8).fill(-1); S.carry = null; S.seqOn = false; }
function tickAttract(T) {
  const env = envs[3], orbs = env.userData.orbs, worm = env.userData.worm;
  tickOrbHalos(T, Math.min(.05, T - (S.lastHaloT ?? T))); S.lastHaloT = T;
  if (S.beamOn) {
    if (!beamLine.parent) scene.add(beamLine);
    const h = pick(orbs.filter(o => o.userData.state === 'home'));
    const end = h ? h.point : S.hand.clone().add(ray.ray.direction.clone().multiplyScalar(8));
    beamLine.geometry.setFromPoints([sensor.position.clone(), end]); beamLine.visible = true;
    if (h && h.object !== S.hovOrb) S.hovOrb = h.object;   // hover = solo visual (la esfera crece un poco); sin sonido ni háptico, como en Unreal
    else if (!h && S.hovOrb) S.hovOrb = null;
    if (S.attractOn && S.clicked && S.playing) {
      if (!S.carry && h) { S.carry = h.object; S.carry.userData.state = 'carry'; const oid = 'FX_ORB_' + (S.carry.userData.note + 1); if (!(typeof audioFor === 'function' && audioFor(oid))) tone(NOTE[S.carry.userData.note % 5] * (1 + (S.carry.userData.note / 5 | 0) * .5), .8, 'triangle', .07); cue('fx', oid); cue('fx', 'FX_ORBGRAB'); cue('hap', 'HAP_PULSE_SOFT'); }
      else if (S.carry) { const w = pick(worm); if (w) { const k = w.object.userData.slot; const prev = orbs.find(o => o.userData.slot === k); if (prev) { prev.userData.state = 'home'; prev.userData.slot = undefined; }
          S.carry.userData.state = 'slot'; S.carry.userData.slot = k; S.melody[k] = S.carry.userData.note; S.carry = null; cue('fx', 'FX_SLOTSNAP'); cue('hap', 'HAP_SNAP'); if (!S.seqOn) { S.seqOn = true; S.seqT0 = T; cue('vfx', 'PadM1 arranca con la primera esfera'); } }
        else { S.carry.userData.state = 'home'; S.carry = null; cue('fx', 'FX_ORBHOME'); } }
    }
  } else if (beamLine.parent) beamLine.visible = false;
  orbs.forEach(o => { const u = o.userData; if (u.state === 'home') o.position.lerp(u.home, .08); else if (u.state === 'carry') o.position.lerp(tmp.copy(S.hand).addScaledVector(ray.ray.direction, .15).sub(CENTER), .2); else if (u.state === 'slot') o.position.lerp(worm[u.slot].position.clone().add(V(0, .12, 0)), .2); o.scale.setScalar(u.state === 'home' ? 1 : .55); });
  const placed = S.melody ? S.melody.filter(x => x >= 0).length : 0; envU[3].uMandala.value = lerp(envU[3].uMandala.value, placed / 8, .02);
  if (S.seqOn || S.coda) { const step = Math.floor(((T - (S.seqT0 || 0)) / (5.333 / 8)) % 8); worm.forEach((w, k) => w.material.uniforms.uGlow.value = k === step ? .9 : (S.melody[k] >= 0 ? .25 : 0));
    if (step !== S.lastStep && S.playing) { S.lastStep = step; const real = typeof audioFor === 'function';
      if (S.melody[step] >= 0) { const oid = 'FX_ORB_' + (S.melody[step] + 1); if (!(real && playSoundId(oid))) tone(NOTE[S.melody[step] % 5] * (1 + (S.melody[step] / 5 | 0) * .5), .6, 'triangle', .06); }
      if (step % 2 === 0 && !(real && audioFor('PAD_M1'))) tone(110, .4, 'sine', .04); } }
}
const beamLine = new THREE.Line(new THREE.BufferGeometry(), new THREE.LineBasicMaterial({ color: 0xffe3c4, transparent: true, opacity: .8 }));
function playMelody(passes) { const mel = S.data.melody.length ? S.data.melody : [0, -1, 2, -1, 4, -1, 2, -1]; for (let p = 0; p < passes; p++) mel.forEach((v, k) => { if (v >= 0) tone(NOTE[v % 5] * (1 + (v / 5 | 0) * .5), .6, 'triangle', .06, .01, (p * 8 + k) * .667 / S.speed); }); }

/* ============ dibujo: el trazo sigue la mano ============ */
let stroke = null;
function taperTip(geo, curve, T, R) {
  const L = curve.getLength(), pos = geo.attributes.position, c = new THREE.Vector3(), v = new THREE.Vector3();
  for (let j = 0; j <= T; j++) { const fromEnd = (1 - j / T) * L; if (fromEnd >= .04) continue; const f = .25 + .75 * smooth(fromEnd / .04);
    curve.getPointAt(j / T, c); for (let r = 0; r <= R; r++) { const i = j * (R + 1) + r; v.fromBufferAttribute(pos, i).sub(c).multiplyScalar(f).add(c); pos.setXYZ(i, v.x, v.y, v.z); } }
  pos.needsUpdate = true;
}
/* el degradado del trazo: de la cola (donde empezó) a la punta (junto a la mano), por anillo del tubo */
function gradientAlong(geo, T, R, tip, tail, veins) {
  const a = new THREE.Color(tail), b = new THREE.Color(tip), c = new THREE.Color(), col = new Float32Array(geo.attributes.position.count * 3);
  for (let j = 0; j <= T; j++) { c.copy(a).lerp(b, j / T);
    for (let r = 0; r <= R; r++) { const k = veins ? 1 + .05 * Math.sin((r % R) * 2.7 + 1.3) : 1; col.set([c.r * k, c.g * k, c.b * k], (j * (R + 1) + r) * 3); } }  // el marcador: vetas a lo largo del trazo, ±5 % de brillo
  geo.setAttribute('color', new THREE.BufferAttribute(col, 3));
}
/* ============ la PUNTA del pincel: estela de preview + halo (Drawing, 2026-09-30) ============
   Estela (preview de Tilt Brush): solo sin dibujar y fuera de la paleta; vuelve 0,25 s después de soltar. Poses de los
   últimos 0,12 s (tope 16) → cinta con pincel y color actuales; ancho = 0,7 × tamaño × min(1,(i−1)/max(1,n−3)) × min(1, largo/6 cm).
   Halo: esfera aditiva de 3× la punta, color del pincel, intensidad 0,6; resplandor pow(ndv,2)² + 3 anillos hacia afuera
   (0,35 ciclos/s) + pulso 0,4 Hz ±20 %; dibujando: brillo ×1,8, anillos marcados, tiempo ×2,5 (TipHaloPS.hlsl). */
const TIP = { hist: [], upT: -9, was: false, ph: 0, pt: 0, boost: 0 };
TIP.haloU = { uCol: { value: new THREE.Color() }, uInt: { value: .6 }, uBoost: { value: 0 }, uPh: { value: 0 }, uPulse: { value: 0 }, uFreq: { value: 3 }, uSoft: { value: 2 } };
TIP.halo = new THREE.Mesh(new THREE.SphereGeometry(1, 24, 16), new THREE.ShaderMaterial({ uniforms: TIP.haloU, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
  vertexShader: `varying vec3 vN,vV; void main(){ vN=normalize(normalMatrix*normal); vec4 mv=modelViewMatrix*vec4(position,1.); vV=normalize(-mv.xyz); gl_Position=projectionMatrix*mv; }`,
  fragmentShader: `uniform vec3 uCol; uniform float uInt,uBoost,uPh,uPulse,uFreq,uSoft; varying vec3 vN,vV;
    void main(){ float ndv=clamp(dot(normalize(vN),normalize(vV)),0.,1.); float r=sqrt(clamp(1.-ndv*ndv,0.,1.)); float core=pow(ndv,max(uSoft,.5));
      float ring=.5+.5*sin((r*uFreq-uPh)*6.2831853); ring=ring*ring*(r*(1.-r)*4.); float pulse=.8+.2*uPulse;
      float e=core*core*pulse*(1.+.8*uBoost)+ring*(.18+.5*uBoost)*ndv; gl_FragColor=vec4(uCol*e*uInt,1.); }` }));
TIP.halo.renderOrder = 59; TIP.halo.visible = false; scene.add(TIP.halo);
TIP.dot = new THREE.Mesh(new THREE.SphereGeometry(1, 16, 12), new THREE.MeshBasicMaterial({ color: 0xffffff })); TIP.dot.renderOrder = 58; TIP.dot.visible = false; scene.add(TIP.dot);   // SM_Tip: pincel × TipGain 1,5 + TipLift 0,06
TIP.trail = new THREE.Mesh(new THREE.BufferGeometry(), new THREE.MeshBasicMaterial({ color: 0xffffff, side: THREE.DoubleSide, transparent: true, opacity: .85, depthWrite: false }));
TIP.trail.frustumCulled = false; TIP.trail.visible = false; scene.add(TIP.trail);
function hideTip() { TIP.halo.visible = TIP.trail.visible = TIP.dot.visible = false; TIP.hist.length = 0; }
function tickTip(dt) {
  const B = PAL3.root ? PAL_BRUSHES[PAL3.brush] : null, size = 2 * (B ? lerp(B.r[0], B.r[1], PAL3.thick) : .006), col = PAL3.root ? PAL_COLORS[PAL3.color] : (S.brush || '#8fb4ff');
  const drawing = !!(S.down && S.playing && !S.overPalette); if (TIP.was && !drawing) TIP.upT = S.clock; TIP.was = drawing;
  // halo
  TIP.boost += ((drawing ? 1 : 0) - TIP.boost) * Math.min(1, dt * 8); const rate = drawing ? 2.5 : 1;
  TIP.ph = (TIP.ph + dt * .35 * rate) % 1; TIP.pt += dt * rate;
  TIP.haloU.uCol.value.set(col); TIP.haloU.uBoost.value = TIP.boost; TIP.haloU.uPh.value = TIP.ph; TIP.haloU.uPulse.value = .5 + .5 * Math.sin(TIP.pt * 2 * Math.PI * .4);
  TIP.halo.position.copy(S.hand); TIP.halo.scale.setScalar(1.5 * size); TIP.halo.visible = !S.overPalette;   // radio = 1,5 × diámetro → 3× la punta
  TIP.dot.position.copy(S.hand); TIP.dot.scale.setScalar(.5 * size); TIP.dot.visible = !S.overPalette;
  { const c = new THREE.Color(col).convertSRGBToLinear(); c.setRGB(Math.min(1, c.r * 1.5 + .06), Math.min(1, c.g * 1.5 + .06), Math.min(1, c.b * 1.5 + .06)).convertLinearToSRGB(); TIP.dot.material.color.copy(c); }
  // estela: poses de los últimos 0,2 s, tope 16
  TIP.hist.push({ p: S.hand.clone(), t: S.clock }); while (TIP.hist.length > 16 || (TIP.hist.length && S.clock - TIP.hist[0].t > .12)) TIP.hist.shift();
  const n = TIP.hist.length, show = !drawing && !S.overPalette && S.clock - TIP.upT > .25 && n >= 3;
  let len = 0; for (let i = 1; i < n; i++) len += TIP.hist[i].p.distanceTo(TIP.hist[i - 1].p);
  TIP.trail.visible = show && len > .002; if (!TIP.trail.visible) return;
  const cam = camera.getWorldPosition(new THREE.Vector3()), pos = new Float32Array(n * 6), side = new THREE.Vector3(), tan = new THREE.Vector3(), view = new THREE.Vector3(), idx = [];
  for (let i = 0; i < n; i++) { const p = TIP.hist[i].p; tan.subVectors(TIP.hist[Math.min(n - 1, i + 1)].p, TIP.hist[Math.max(0, i - 1)].p).normalize(); view.subVectors(cam, p).normalize();
    side.crossVectors(tan, view).normalize(); const w = size * Math.min(1, Math.max(0, i - 1) / Math.max(1, n - 3)) * Math.min(1, len / .06) * .5 * .7;  // TrailIdeal 6 cm, TrailWidth 0,7 (Drawing, 2026-09-30)
    pos.set([p.x + side.x * w, p.y + side.y * w, p.z + side.z * w, p.x - side.x * w, p.y - side.y * w, p.z - side.z * w], i * 6);
    if (i) idx.push(2 * i - 2, 2 * i - 1, 2 * i, 2 * i - 1, 2 * i + 1, 2 * i); }
  const g = TIP.trail.geometry; g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.setIndex(idx); g.attributes.position.needsUpdate = true;
  TIP.trail.material.color.set(col); TIP.trail.material.blending = B && B.glow ? THREE.AdditiveBlending : THREE.NormalBlending;
}
const INK_METERS = 30;   // tanque de tinta (director de Drawing, 10 TINTA)
function clearStrokes() { S.inkUsed = 0; S.inkSaved = false; const g = envs[4].userData.strokes; g.children.slice().forEach(m => { g.remove(m); m.geometry.dispose(); }); S.data.strokes = []; stroke = null; }
function tickDraw() {
  const env = envs[4], g = env.userData.strokes;
  const ink = 1 - (S.inkUsed || 0) / INK_METERS; if (PAL3.inkU) PAL3.inkU.uFill.value = Math.max(0, ink);
  // sin tinta: suelta el trazo y guarda solo, una vez (el mismo guardado que mantener SAVE); si no hay trazos, reintenta
  if (ink <= 0) { stroke = null; if (!S.inkSaved && S.data.strokes.length) S.inkSaved = true; return; }
  if (S.down && S.playing && !S.overPalette && !$('#lefthand').matches(':hover')) {
    const p = S.hand.clone(); env.worldToLocal(p);
    if (!stroke) { stroke = { pts: [], mesh: null, color: PAL3.root ? PAL_COLORS[PAL3.color] : (S.brush || '#8fb4ff'), tail: PAL3.root ? PAL_TAILS[PAL3.color] : null }; S.data.strokes.push(stroke.pts); PAL3.redo.length = 0; cue('fx', 'FX_DRAW_BRUSH', 'loop mientras dibuja'); cue('hap', 'HAP_DRAW_HUM'); }
    const lastP = stroke.pts[stroke.pts.length - 1]; if (!lastP || lastP.distanceTo(p) > .01) { if (lastP) S.inkUsed = (S.inkUsed || 0) + lastP.distanceTo(p); stroke.pts.push(p);
      if (stroke.pts.length > 2) { if (stroke.mesh) { g.remove(stroke.mesh); stroke.mesh.geometry.dispose(); }
        const B = PAL3.root ? PAL_BRUSHES[PAL3.brush] : null, rad = B ? lerp(B.r[0], B.r[1], PAL3.thick) : .006;
        const mat = new THREE.MeshBasicMaterial({ color: stroke.tail ? 0xffffff : stroke.color, vertexColors: !!stroke.tail, transparent: !!(B && (B.glow || B.wet)), opacity: B && B.wet ? .7 : 1, blending: B && B.glow ? THREE.AdditiveBlending : THREE.NormalBlending, depthWrite: !(B && B.glow) });
        const curve = new THREE.CatmullRomCurve3(stroke.pts), T = stroke.pts.length * 2, geo = new THREE.TubeGeometry(curve, T, rad, 6, false);
        taperTip(geo, curve, T, 6); // la punta junto a la mano: 4 cm fijos que se afinan (Drawing, 2026-09-30)
        if (stroke.tail) gradientAlong(geo, T, 6, stroke.color, stroke.tail, PAL3.brush === 0);
        stroke.mesh = new THREE.Mesh(geo, mat); stroke.mesh.userData.pts = stroke.pts; g.add(stroke.mesh); } }
  } else stroke = null;
  g.children.forEach((m, k) => m.position.y = Math.sin(S.clock * .8 + k) * .004);
}

/* ============ la PALETA 3D de SURROUNDING (Mesh 3D + Drawing, 2026-09-29) ============
   SM_DrawPalette_*_SC: disco de hormigón de 40 cm modelado, a escala 0,6 (~24 cm) en la mano izquierda (aquí: abajo a la
   izquierda de la vista). Todo por PROXIMIDAD de la punta, sin gatillo (aquí: pasar el mouse por encima):
   · 4 colores (derecha) y 4 pinceles (izquierda): se elige al acercar; la elegida sube ~0,9 cm y brilla, con la punta
     encima sube un poco más · casquete central = color elegido · deshacer/rehacer (arriba a la izquierda, al 65 %):
     se disparan al entrar, una vez por toque, se hunden y destellan · slider en arco abajo: izquierda fino y disco chico,
     derecha grueso y disco grande. Ángulos y radios de BP_DrawPalette_SC.md (en grados de Blender: Unreal = −Blender). */
const PAL_COLORS = ['#E3E8E1', '#A8D2BF', '#8EC4D4', '#23443F'];  // paleta "A · niebla y agua" (Drawing, 2026-09-30): hueso, celadón, celeste, petróleo = PUNTA del trazo
const PAL_TAILS = ['#A3C2BC', '#549C95', '#5C79B2', '#638C79'];   // la COLA del degradado de cada color (degradados encendidos)
const PAL_BRUSHES = [{ id: 'TaperedMarker', r: [.002, .007] }, { id: 'OilPaint', r: [.003, .012] }, { id: 'Light', r: [.002, .009], glow: true }, { id: 'WetPaint', r: [.003, .011], wet: true }];
const PAL_SIDE_SCALE = 1.40;  // SideScale de BP_DrawPalette_SC (SideSize / escala de la paleta)
const PAL3 = { root: null, keys: [], side: {}, knob: null, swatch: null, color: 1, brush: 1, thick: .5, hover: null, inside: null, press: { undo: 0, redo: 0 }, redo: [] };
function palMaterial(kind) {
  return new THREE.ShaderMaterial({ depthTest: false, depthWrite: false,
    uniforms: { uCol: { value: kind === 'groove' ? new THREE.Color().setRGB(.342, .571, .456).convertLinearToSRGB() : new THREE.Color(0xb9b2a7) }, uGlow: { value: 0 }, uKind: { value: kind === 'groove' ? 1 : 0 } },
    vertexShader: `varying vec3 vN,vV,vP; void main(){ vP=position; vN=normalize(normalMatrix*normal); vec4 mv=modelViewMatrix*vec4(position,1.); vV=normalize(-mv.xyz); gl_Position=projectionMatrix*mv; }`,
    fragmentShader: `uniform vec3 uCol; uniform float uGlow,uKind; varying vec3 vN,vV,vP; ${NOISE}
      void main(){ if(uKind>.5){ gl_FragColor=vec4(uCol*1.2,1.); return; }
        vec3 n=normalize(vN), l=normalize(vec3(-.35,.75,.55)); float w=max(dot(n,l)*.6+.4,0.);
        float grain=vn(vP*900.)*.08+vn(vP*140.)*.1; vec3 c=uCol*(.28+.62*w)*(.9+grain)+uCol*uGlow; gl_FragColor=vec4(c,1.); }` });
}
function installPalette(root) {
  const byName = {}; root.traverse(o => { if (o.isMesh) { const k = (o.name.match(/DrawPalette_(\w+?)_SC/) || [])[1] || (o.parent && (o.parent.name.match(/DrawPalette_(\w+?)_SC/) || [])[1]); (byName[k] = byName[k] || []).push(o); } });
  const pal = new THREE.Group(); pal.visible = false; camera.add(pal);
  pal.position.set(-.25, -.19, -.5); pal.rotation.set(Math.PI / 2 - .6, .3, 0); pal.scale.setScalar(.6); // en la mano izquierda, inclinada hacia el usuario
  const clone = (m, mat) => { const x = new THREE.Mesh(m.geometry, mat); x.renderOrder = 58; return x; };
  // base: cuerpo + ranura emisiva
  (byName.Base || []).forEach(m => pal.add(clone(m, palMaterial(/Groove/i.test((m.material && m.material.name) || '') ? 'groove' : 'body'))));
  // 4 colores y 4 pinceles: la misma cuña girada (grados de Blender alrededor de la normal de la paleta = +Y en glTF)
  const keyGeo = byName.Key && byName.Key[0];
  [60, 20, -20, -60, 120, 160, 200, 240].forEach((deg, i) => {
    const g = new THREE.Group(); g.rotation.y = deg * Math.PI / 180; const mat = palMaterial('body');
    const lift = new THREE.Group(); g.add(lift); lift.add(clone(keyGeo, mat)); pal.add(g);
    PAL3.keys.push({ kind: i < 4 ? 'color' : 'brush', idx: i % 4, deg, lift, mat, y: 0 });
  });
  // deshacer (abajo) y rehacer (arriba), agrandados a SideScale S sin superponerse (Drawing, 2026-09-30): cada tecla gira
  // alrededor del centro de la paleta a 180 ± SideHalf, SideHalf = atan2d(0,2079·S, 1 − 0,0219·S) + 2°, y se corre
  // 19,6·(S−1) cm hacia el centro. Con S = 1 queda como el modelado (±14°); hoy S = 1,40 → ±18,7°.
  const side = byName.SideKey && byName.SideKey[0]; side.geometry.computeBoundingBox(); const cen = side.geometry.boundingBox.getCenter(new THREE.Vector3());
  const S = PAL_SIDE_SCALE, SH = Math.atan2(.2079 * S, 1 - .0219 * S) * 180 / Math.PI + 2; PAL3.sideHalf = SH;
  [['redo', 14 - SH], ['undo', 14 + SH]].forEach(([k, deg]) => {
    // como en Unreal: la tecla escala desde el centro de la paleta (su pivote) y después se corre hacia adentro
    const g = new THREE.Group(); g.rotation.y = deg * Math.PI / 180; const piv = new THREE.Group();
    piv.position.copy(cen).setY(0).normalize().multiplyScalar(-.196 * (S - 1));
    const mat = palMaterial('body'); mat.uniforms.uCol.value.setRGB(.40, .37, .33).convertLinearToSRGB();
    const mesh = clone(side, mat); piv.add(mesh); piv.scale.setScalar(S); g.add(piv); pal.add(g);
    PAL3.side[k] = { piv, mat, base: piv.position.y }; PAL3.sideR = S * Math.hypot(cen.x, cen.z) - .196 * (S - 1);
  });
  (byName.Slider || []).forEach(m => pal.add(clone(m, palMaterial('body'))));
  const knobMat = palMaterial('body'); const knob = clone(byName.Knob[0], knobMat); pal.add(knob); PAL3.knob = { mesh: knob, mat: knobMat };
  const swMat = palMaterial('body'); pal.add(clone(byName.Swatch[0], swMat)); PAL3.swatch = swMat;
  // el ARCO DE TINTA (Drawing, 2026-09-30; InkArcPS.hlsl): cinta de 64 segmentos entre el slider y rehacer, bajo el borde.
  // Radio 21,40–22,06 cm, z −1,6 cm; de 319,9° (junto al slider) a 180 − 2·SideHalf + SideGap − InkGap (junto a rehacer),
  // antihorario. UV.x 0 = slider → 1 = rehacer. Fill = tinta que queda; se vacía hacia el slider.
  { const a0 = 319.9, a1 = 360 + 180 - 2 * PAL3.sideHalf + 2 - 6, N = 64, pos = [], uv = [], idx = [];
    for (let i = 0; i <= N; i++) { const u = i / N, th = (a0 + (a1 - a0) * u) * Math.PI / 180;
      [.2140, .2206].forEach((r, j) => { pos.push(r * Math.cos(th), -.016, -r * Math.sin(th)); uv.push(u, j); });
      if (i) idx.push(2 * i - 2, 2 * i - 1, 2 * i, 2 * i - 1, 2 * i + 1, 2 * i); }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2)); g.setIndex(idx);
    const lin = (r, gg, b) => new THREE.Color().setRGB(r, gg, b).convertLinearToSRGB();
    PAL3.inkU = { uFill: { value: 1 }, uCol: { value: lin(.39, .79, .48) }, uTrack: { value: lin(.20, .32, .25) } };
    const m = new THREE.Mesh(g, new THREE.ShaderMaterial({ uniforms: PAL3.inkU, transparent: true, depthTest: false, depthWrite: false, side: THREE.DoubleSide,
      vertexShader: `varying vec2 vUv; void main(){ vUv=uv; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.); }`,
      fragmentShader: `uniform float uFill; uniform vec3 uCol,uTrack; varying vec2 vUv;
        void main(){ float x=vUv.x, edge=clamp((1.-abs(vUv.y*2.-1.))*3.,0.,1.), f=clamp(uFill,0.,1.), w=.012;
          float m=clamp((f-x)/w+.5,0.,1.), head=exp(-abs(x-f)/(w*2.))*step(.0005,f);
          vec3 c=mix(uTrack,uCol,m)*1.4+uCol*head*.9; float a=edge*clamp(mix(.06,.85,m)+head*.45,0.,1.);
          gl_FragColor=vec4(c,a); }` }));
    m.renderOrder = 59; pal.add(m); PAL3.ink = m; }
  PAL3.root = pal; PAL3.plane = new THREE.Plane(); paletteLook();
}
/* el aspecto según el estado (se llama cada cuadro con la paleta visible) */
function paletteLook(dt = 0) {
  const k = 1 - Math.exp(-14 * dt);
  PAL3.keys.forEach(key => {
    const sel = key.kind === 'color' ? key.idx === PAL3.color : key.idx === PAL3.brush, hov = PAL3.hover === key;
    const target = (sel ? .009 : 0) + (hov ? .0035 : 0); key.y += (target - key.y) * (dt ? k : 1); key.lift.position.y = key.y;
    if (key.kind === 'color') key.mat.uniforms.uCol.value.set(PAL_COLORS[key.idx]);  // teclas de color con ganancia 1,0 (antes 0,7) else key.mat.uniforms.uCol.value.setRGB(.40, .37, .33).convertLinearToSRGB();
    key.mat.uniforms.uGlow.value = (sel ? .35 : 0) + (hov ? .15 : 0);
  });
  ['undo', 'redo'].forEach(n => { const s = PAL3.side[n], p = PAL3.press[n]; s.piv.position.y = s.base - .008 * p; s.mat.uniforms.uGlow.value = .7 * p + (PAL3.hover === n ? .15 : 0); PAL3.press[n] = Math.max(0, p - dt / .35); });
  const a = (227 + 86 * PAL3.thick) * Math.PI / 180; PAL3.knob.mesh.position.set(.2173 * Math.cos(a), -.01705, -.2173 * Math.sin(a));
  PAL3.knob.mesh.scale.setScalar(lerp(.5, 1.6, PAL3.thick)); PAL3.knob.mat.uniforms.uGlow.value = PAL3.hover === 'slider' ? .3 : .1;
  PAL3.swatch.uniforms.uCol.value.set(PAL_COLORS[PAL3.color]); PAL3.swatch.uniforms.uGlow.value = PAL_BRUSHES[PAL3.brush].glow ? .6 : .15;
}
/* dónde está la punta sobre la paleta: se cruza el rayo del mouse con el plano del disco y se pasa a polar (grados de Blender) */
function paletteHit() {
  const pal = PAL3.root; pal.updateMatrixWorld(true);
  const n = new THREE.Vector3(0, 1, 0).transformDirection(pal.matrixWorld), o = pal.getWorldPosition(new THREE.Vector3());
  PAL3.plane.setFromNormalAndCoplanarPoint(n, o); const hit = new THREE.Vector3(); if (!ray.ray.intersectPlane(PAL3.plane, hit)) return null;
  const loc = pal.worldToLocal(hit.clone()); const bx = loc.x, by = -loc.z, r = Math.hypot(bx, by); let deg = Math.atan2(by, bx) * 180 / Math.PI; if (deg < 0) deg += 360;
  return { r, deg };
}
function paletteRegion(h) {
  if (!h || h.r > .26) return null;
  if (h.r > .05 && h.r < .155) { const near = PAL3.keys.find(k => Math.abs(((h.deg - k.deg) % 360 + 540) % 360 - 180) < 19); if (near) return near; }
  { const SH = PAL3.sideHalf || 14, rc = PAL3.sideR || .2, hw = .03 * PAL_SIDE_SCALE;
    if (h.r > rc - hw && h.r < rc + hw && Math.abs(h.deg - 180) < SH + 10) return h.deg < 180 ? 'redo' : 'undo'; }
  if (h.r > .15 && h.r < .245 && h.deg > 222 && h.deg < 318) return 'slider';
  return h.r < .2 ? 'disk' : null;
}
function tickPalette3D(dt) {
  if (!PAL3.root || !PAL3.root.visible) { PAL3.hover = null; PAL3.inside = null; S.overPalette = false; return; }
  const h = paletteHit(), reg = paletteRegion(h); S.overPalette = !!reg; PAL3.hover = reg;
  if (reg && typeof reg === 'object' && S.playing) {
    if (reg.kind === 'color' && PAL3.color !== reg.idx) { PAL3.color = reg.idx; S.brush = PAL_COLORS[reg.idx]; cue('fx', 'FX_PALETTECLICK', 'color'); cue('hap', 'HAP_TICK'); }
    if (reg.kind === 'brush' && PAL3.brush !== reg.idx) { PAL3.brush = reg.idx; cue('fx', 'FX_PALETTECLICK', PAL_BRUSHES[reg.idx].id); cue('hap', 'HAP_TICK'); }
  }
  if ((reg === 'undo' || reg === 'redo') && PAL3.inside !== reg && S.playing) { PAL3.press[reg] = 1; cue('fx', 'FX_PALETTECLICK', reg === 'undo' ? 'deshacer' : 'rehacer'); cue('hap', 'HAP_TICK'); reg === 'undo' ? undoStroke() : redoStroke(); }
  if (reg === 'slider' && S.playing) PAL3.thick = clamp((h.deg - 227) / 86);
  PAL3.inside = typeof reg === 'string' ? reg : (reg ? 'key' : null);
  paletteLook(dt);
}
function undoStroke() { const g = envs[4].userData.strokes, m = g.children[g.children.length - 1]; if (!m) return; g.remove(m); PAL3.redo.push(m); S.data.strokes.pop(); }
function redoStroke() { const m = PAL3.redo.pop(); if (!m) return; envs[4].userData.strokes.add(m); S.data.strokes.push(m.userData.pts || []); }
loadGLB('SM_DrawPalette_SC.glb').then(installPalette).catch(e => console.warn('Paleta real no cargada:', e && e.message));

/* ============ el SENSOR BIO de ENTERING y RECOGNIZING (Mesh 3D, aprobado por Beltrán 2026-09-30) ============
   SM_BioSensor_SC: disco de Ø 19 cm y 6,8 cm de profundidad; la cara de la panza mira a -Z en Blender (-Y en glTF).
   7 slots: Body, Face, Button, Grip (media esfera de grafito) y las luces Ring, BackRing, TipLight.
   SM_BioSensorWaves_SC: los aros, un cilindro que sale de la cinta hacia la panza; nacen y se desvanecen en ciclo
   continuo y se juntan al alejarse. Se encienden cuando el sensor está apoyado. En esas dos etapas reemplaza al mando
   en la mano y en la demostración (el fantasma). */
const BIO = { live: null, ghosts: [], waves: null, on: 0 };
const bioWavesU = { uT: { value: 0 }, uOn: { value: 0 }, uCol: { value: new THREE.Color(.72, .82, 1) } };
function bioMaterial(slot, ghost) {
  const light = /Ring|TipLight/.test(slot), col = { Body: 0xbdb6ab, Face: 0xd8d4cc, Button: 0x6e6a64, Grip: 0x2a2b2e }[slot] || 0xbdb6ab;
  return new THREE.ShaderMaterial({ transparent: ghost, depthWrite: !ghost,
    uniforms: { uCol: { value: new THREE.Color(light ? 0xcfe0ff : col) }, uLight: { value: light ? 1 : 0 }, uOn: { value: 0 }, uGhost: { value: ghost ? 1 : 0 }, uOp: { value: 1 }, uTint: { value: new THREE.Color(0xcfe0ff) } },
    vertexShader: `varying vec3 vN,vV,vP; void main(){ vP=position; vN=normalize(normalMatrix*normal); vec4 mv=modelViewMatrix*vec4(position,1.); vV=normalize(-mv.xyz); gl_Position=projectionMatrix*mv; }`,
    fragmentShader: `uniform vec3 uCol,uTint; uniform float uLight,uOn,uGhost,uOp; varying vec3 vN,vV,vP; ${NOISE}
      void main(){ vec3 n=normalize(vN); float fr=pow(1.-abs(dot(n,vV)),2.);
        if(uGhost>.5){ gl_FragColor=vec4(uTint*(.55+.9*fr),uOp*(.35+.65*fr)); return; }
        if(uLight>.5){ gl_FragColor=vec4(uCol*(.35+.9*uOn),1.); return; }
        vec3 l=normalize(vec3(-.3,.8,.5)); float d=max(dot(n,l)*.6+.4,0.); float g=vn(vP*700.)*.06;
        gl_FragColor=vec4(uCol*(.3+.65*d)*(.94+g)+vec3(1.)*pow(max(dot(reflect(-l,n),vV),0.),20.)*.08,1.); }` });
}
function bioBuild(meshes, ghost) {
  const g = new THREE.Group(), holder = new THREE.Group(); g.add(holder); const mats = [];
  meshes.forEach(m => { const slot = ((m.material && m.material.name) || '').replace(/^M_BioSensor_/, '');
    if (/Waves/.test(slot)) { if (ghost) return; const w = new THREE.Mesh(m.geometry, BIO_WAVES); w.renderOrder = 57; w.frustumCulled = false; holder.add(w); return; }
    const mat = bioMaterial(slot, ghost); mats.push(mat); const x = new THREE.Mesh(m.geometry, mat); if (ghost) x.renderOrder = 56; holder.add(x); });
  g.userData = { mats, look(color, op) { mats.forEach(m => { m.uniforms.uTint.value.set(color); m.uniforms.uOp.value = op; }); } };
  g.visible = false; return g;
}
const BIO_WAVES = new THREE.ShaderMaterial({ uniforms: bioWavesU, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide,
  vertexShader: `varying float vS; void main(){ vS=clamp((-position.y-.006)/.0685,0.,1.); gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.); }`,
  fragmentShader: `uniform float uT,uOn; uniform vec3 uCol; varying float vS; void main(){ float s=pow(vS,.7); float ph=fract(s*2.6-uT*.55);
    float ring=smoothstep(.0,.12,ph)*smoothstep(.34,.12,ph); float life=smoothstep(0.,.15,vS)*(1.-smoothstep(.7,1.,vS));
    gl_FragColor=vec4(uCol,ring*life*uOn*.8); }` });
function installBioSensor(root) {
  const meshes = []; root.traverse(o => { if (o.isMesh) meshes.push(o); });
  BIO.live = bioBuild(meshes, false); scene.add(BIO.live);
  for (let k = 0; k < 7; k++) { const g = bioBuild(meshes, true); camera.add(g); BIO.ghosts.push(g); }
}
loadGLB('SM_BioSensor_SC.glb').then(installBioSensor).catch(e => console.warn('Sensor bio no cargado:', e && e.message));

/* ============ el HUD como objeto 3D (Mesh 3D, 2026-09-30; aprobado el formato por Beltrán) ============
   SM_HUD_SC: píldora de 256 × 56 × 12 mm con marco de la familia (Frame + Seat), lámina translúcida (Glass, lo único
   translúcido) y la AMEBA QUE LATE (Pulse) en su asiento a la izquierda. Al centro, la ventana del EEG de 120 × 30 mm
   (el gráfico en vivo; en Unreal es el widget del OSC). A la derecha, el nido del anillo con el alma (Ø ext. 45 mm).
   A 55 cm y 30° bajo el horizonte, inclinada hacia el ojo. La ameba late a la MITAD del ritmo (curva u²·e^(2(1−u))). */
const HUD_RING_S = .115;   // escala del contenedor del anillo en el nido: Ø exterior ~45 mm
const HUD3 = { root: null, pulse: null, pulseU: null, eeg: null };
const HUD_RIM_U = { uSweep: { value: 0 }, uRimGlow: { value: 0 } };
function hudRim(col, alpha) {
  return new THREE.ShaderMaterial({ uniforms: { uCol: { value: new THREE.Color(col) }, ...HUD_RIM_U }, transparent: true, depthWrite: false,
    vertexShader: `varying vec3 vN,vV,vP; void main(){ vP=position; vN=normalize(normalMatrix*normal); vec4 mv=modelViewMatrix*vec4(position,1.); vV=normalize(-mv.xyz); gl_Position=projectionMatrix*mv; }`,
    fragmentShader: `uniform vec3 uCol; uniform float uSweep,uRimGlow; varying vec3 vN,vV,vP; ${NOISE}
      void main(){ vec3 n=normalize(vN), l=normalize(vec3(-.3,.8,.5)); float d=max(dot(n,l)*.6+.4,0.); float g=vn(vP*900.)*.07+vn(vP*140.)*.05;
        vec3 c=uCol*(.3+.65*d)*(.93+g)+vec3(1.)*pow(max(dot(reflect(-l,n),vV),0.),24.)*.06;
        float u=fract(atan(-vP.z*4.7,vP.x)/6.2831853); float lit=clamp((uSweep-u)/.04+.5,0.,1.);
        float dd=abs(u-uSweep); dd=min(dd,1.-dd); float head=exp(-dd*dd/.0012)*step(.001,uSweep)*step(uSweep,.999);
        float e=(lit*.55+head*1.6)*uRimGlow; gl_FragColor=vec4(c+vec3(1.,.78,.55)*e,clamp(${alpha.toFixed(2)}+e*.5,0.,1.)); }` });
}
function hudConcrete(col, grain, alpha = 1) {
  return new THREE.ShaderMaterial({ uniforms: { uCol: { value: new THREE.Color(col) } }, transparent: alpha < 1, depthWrite: alpha >= 1,
    vertexShader: `varying vec3 vN,vV,vP; void main(){ vP=position; vN=normalize(normalMatrix*normal); vec4 mv=modelViewMatrix*vec4(position,1.); vV=normalize(-mv.xyz); gl_Position=projectionMatrix*mv; }`,
    fragmentShader: `uniform vec3 uCol; varying vec3 vN,vV,vP; ${NOISE}
      void main(){ vec3 n=normalize(vN), l=normalize(vec3(-.3,.8,.5)); float d=max(dot(n,l)*.6+.4,0.); float g=vn(vP*900.)*${grain}+vn(vP*140.)*.05;
        gl_FragColor=vec4(uCol*(.3+.65*d)*(.93+g)+vec3(1.)*pow(max(dot(reflect(-l,n),vV),0.),24.)*.06,${alpha.toFixed(2)}); }` });
}
function installHud(root) {
  const pill = new THREE.Group(); pill.add(root); root.rotation.x = Math.PI / 2;   // glTF (cara +Y) → la cara hacia +Z, ejes de Blender
  root.traverse(o => { if (!o.isMesh) return; const n = (o.material && o.material.name) || '';
    if (/Rim|Frame|Bezel/.test(n)) { o.material = hudRim(0xb9b2a7, .45); o.renderOrder = 62; }   // v4: borde y contornos finos y translúcidos
    else if (/Seat/.test(n)) o.material = hudConcrete(0x2e2c29, '.05');   // los fondos del nido y del asiento, opacos
    else if (/Glass/.test(n)) { o.material = new THREE.MeshBasicMaterial({ color: 0xe6ebf5, transparent: true, opacity: .22, depthWrite: false }); o.renderOrder = 61; }   // lechosa: que se lea como base
    else if (/Pulse/.test(n)) { HUD3.pulseU = { uGlow: { value: 0 } };
      o.material = new THREE.ShaderMaterial({ uniforms: HUD3.pulseU,
        vertexShader: `varying vec3 vN,vV; void main(){ vN=normalize(normalMatrix*normal); vec4 mv=modelViewMatrix*vec4(position,1.); vV=normalize(-mv.xyz); gl_Position=projectionMatrix*mv; }`,
        fragmentShader: `uniform float uGlow; varying vec3 vN,vV; void main(){ vec3 n=normalize(vN); float ndv=max(dot(n,normalize(vV)),0.), fr=pow(1.-ndv,2.);
          vec3 base=vec3(.95,.55,.70), core=vec3(1.,.82,.9); gl_FragColor=vec4(mix(base*(.45+.35*ndv),core,fr*.5)+core*uGlow*.45*ndv,1.); }` });
      HUD3.pulse = o; } });
  // el EEG en su ventana: 48 muestras, alto (casi todo el alto de la ventana), un poco hundido detrás del marco interior
  const pts = new Float32Array(48 * 3), g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pts, 3));
  HUD3.eeg = new THREE.Line(g, new THREE.LineBasicMaterial({ color: 0xbfd0ff })); HUD3.eeg.position.z = -.001; HUD3.eeg.frustumCulled = false; pill.add(HUD3.eeg); HUD3.eegPts = pts;
  // la HERMANA: el pulso del latido es tu propia ameba (Beltrán, 2026-09-30). Misma malla y mismo material que el alma
  // del anillo (color, vida y brillo compartidos), en el asiento de la izquierda, más grande (~30 mm) que la del anillo.
  if (HUD3.pulse) { HUD3.pulse.visible = false; HUD3.sister = new THREE.Mesh(soul.geometry, soul.material); HUD3.sister.position.copy(HUD3.pulse.position); HUD3.sister.renderOrder = 63; HUD3.sister.visible = false; HUD3.pulse.parent.add(HUD3.sister); }
  hudPanel.add(pill); HUD3.root = pill;
  hudPanel.position.set(0, -.275, -.476); hudPanel.rotation.x = -Math.PI / 6;   // 55 cm, 30° bajo el horizonte, mirando al ojo
  hudAnchor.position.set(.1011, 0, 0); eeg.visible = heartDot.visible = false;   // el anillo va al nido de la derecha (v4: ±101,1 mm)
}
loadGLB('SM_HUD_SC.glb').then(installHud).catch(e => console.warn('HUD 3D no cargado:', e && e.message));
function hudWorldQuat() { hudPanel.updateMatrixWorld(true); return hudPanel.getWorldQuaternion(new THREE.Quaternion()); }

/* ============ aparición "LUZ PRIMERO" (Mesh 3D, aprobada por Beltrán 2026-09-30; receta en blender-3d/assets/aparicion-luz.md) ============
   1,5 s. Una cabeza de luz dibuja el contorno de la ranura en el aire, el cuerpo nace como RENDIJA de luz de canto a la
   vista, se abre como un PÁRPADO hasta quedar de frente, toma espesor y la luz se enfría en hormigón. La salida es la
   misma con t de 1 a 0. El anillo va sin trazo (tiempos corridos). La maneja el timeline: los clips ponen W.appear[nombre]
   = t y cada cuadro tickAppear() arma la pose encima de la transformación normal del objeto, sin tocarla. */
const APPEAR = {
  bell:    { get: () => bell, axis: [0, 0, 1], r: .125, h: .026, trace: true },
  palette: { get: () => PAL3.root, axis: [0, 1, 0], r: .185, h: 0, trace: true },
  sensor:  { get: () => BIO.live && BIO.live.children[0], axis: [0, -1, 0], r: .0622, h: .0061, trace: true },
  ring:    { get: () => ringG, axis: [0, 0, 1], r: 0, h: 0, trace: false },
  hud:     { get: () => HUD3.root, axis: [0, 0, 1], r: 0, h: 0, trace: false },
};
const LIGHT = new THREE.Color(1, .72, .45);
const inOut3 = x => x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2, out3 = x => 1 - Math.pow(1 - x, 3);
const seg = (t, a, b) => clamp((t - a) / (b - a));
function appearTrace(A) {
  const w = A.r * .09, u = { uSweep: { value: 0 }, uHead: { value: 0 }, uGlow: { value: 0 }, uR: { value: A.r }, uW: { value: w }, uCol: { value: LIGHT } };
  const m = new THREE.Mesh(new THREE.RingGeometry(A.r - w, A.r + w, 128, 1), new THREE.ShaderMaterial({ uniforms: u, transparent: true, depthWrite: false, depthTest: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide,
    vertexShader: `varying vec2 vP; void main(){ vP=position.xy; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.); }`,
    fragmentShader: `uniform float uSweep,uHead,uGlow,uR,uW; uniform vec3 uCol; varying vec2 vP;
      float gs(float x){ return exp(-x*x); }
      void main(){ float u=fract((atan(vP.y,vP.x)-1.5707963)/6.2831853), v=(length(vP)-(uR-uW))/(2.*uW);
        float prof=gs((v-.5)/.09)+.3*gs((v-.5)/.28), lit=clamp((uSweep*1.05-u)/.05,0.,1.);
        float dd=abs(u-uSweep); dd=min(dd,1.-dd); float head=gs(dd/.028)*uHead;
        gl_FragColor=vec4(uCol*prof*(lit*uGlow+head),1.); }` }));
  m.renderOrder = 70; m.frustumCulled = false; A.traceU = u;
  A.helper = new THREE.Group(); A.helper.add(m);
  m.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), new THREE.Vector3(...A.axis)); m.position.set(...A.axis).multiplyScalar(A.h);
}
function appearFlash(A, obj) {
  A.flash = []; const list = []; obj.traverse(o => { if (o.isMesh && !o.userData.isFlash) list.push(o); });
  list.forEach(o => { const mat = new THREE.MeshBasicMaterial({ color: LIGHT, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false, depthTest: !(o.material && o.material.depthTest === false) });
    const f = new THREE.Mesh(o.geometry, mat); f.userData.isFlash = true; f.renderOrder = (o.renderOrder || 0) + 1; f.frustumCulled = false; f.visible = false; o.add(f); A.flash.push(f); });
}
function tickAppear() {
  Object.entries(APPEAR).forEach(([name, A]) => {
    const obj = A.get(); if (!obj) return; const t = W.appear ? W.appear[name] : undefined;
    if (!(t !== undefined && t < 1 && obj.parent)) {
      if (A.posed) { obj.matrixAutoUpdate = true; A.posed = false; (A.flash || []).forEach(f => f.visible = false); if (A.helper) A.helper.visible = false; } return; }
    if (!A.flash) appearFlash(A, obj); if (A.trace && !A.helper) appearTrace(A);
    const T0 = A.trace ? { s: [.24, .34], lid: [.30, .54], z: [.36, .56], fl: [.30, .60], fk: 1 } : { s: [0, .20], lid: [.12, .46], z: [.18, .48], fl: [.14, .56], fk: 1.6 };
    const sx = out3(seg(t, ...T0.s)), lid = inOut3(seg(t, ...T0.lid)), sz = lerp(.05, 1, seg(t, ...T0.z)), flash = (1 - seg(t, ...T0.fl)) * T0.fk;
    // la pose, en el espacio del padre y alrededor del pivote en el plano de la ranura
    obj.updateMatrix(); const Mb = obj.matrix.clone(); obj.matrixAutoUpdate = false; A.posed = true;
    const n = new THREE.Vector3(...A.axis).applyQuaternion(obj.quaternion).normalize(), p = obj.position.clone().addScaledVector(n, A.h * obj.scale.x);
    const parent = obj.parent; parent.updateMatrixWorld(true); camera.updateMatrixWorld(true);
    const eye = parent.worldToLocal(camera.getWorldPosition(new THREE.Vector3()));
    const right = new THREE.Vector3(1, 0, 0).applyQuaternion(camera.getWorldQuaternion(new THREE.Quaternion())).applyQuaternion(parent.getWorldQuaternion(new THREE.Quaternion()).invert());
    const X = right.addScaledVector(n, -right.dot(n)); if (X.lengthSq() < 1e-8) X.set(1, 0, 0); X.normalize();
    // X' = la derecha de la cámara en el plano de la cara; n' = X' × (ojo − pivote): con ese giro el plano queda de canto
    const n2 = new THREE.Vector3().crossVectors(X, eye.sub(p)).normalize(); if (n2.dot(n) < 0) n2.negate();
    const th = Math.atan2(new THREE.Vector3().crossVectors(n, n2).dot(X), n.dot(n2)), Y = new THREE.Vector3().crossVectors(n, X);
    const B = new THREE.Matrix4().makeBasis(X, Y, n), S = new THREE.Matrix4().makeScale(Math.max(sx, 1e-4), Math.max(sx, 1e-4), sz);
    const Bs = B.clone().multiply(S).multiply(B.clone().transpose());
    const M = new THREE.Matrix4().makeTranslation(p.x, p.y, p.z).multiply(new THREE.Matrix4().makeRotationAxis(X, th * (1 - lid))).multiply(Bs).multiply(new THREE.Matrix4().makeTranslation(-p.x, -p.y, -p.z));
    obj.matrix.copy(M.multiply(Mb)); obj.matrixWorldNeedsUpdate = true; if (sx < .002) obj.visible = false;
    A.flash.forEach(f => { f.visible = flash > .003; f.material.opacity = .85 * Math.min(1, flash); });
    // el trazo: en el aire, donde queda la ranura (no se escala con el cuerpo)
    if (A.helper) {
      if (A.helper.parent !== parent) parent.add(A.helper);
      A.helper.position.copy(obj.position); A.helper.quaternion.copy(obj.quaternion); A.helper.scale.copy(obj.scale); A.helper.visible = true;
      A.traceU.uSweep.value = inOut3(seg(t, .02, .30)); A.traceU.uHead.value = 3.2 * seg(t, 0, .05) * (1 - seg(t, .28, .38));
      A.traceU.uGlow.value = (t > .26 && t < .42 ? 1 + .5 * Math.sin(Math.PI * (t - .26) / .16) : 1) * (1 - seg(t, .46, .60));
    }
  });
}

/* ============ TELETRANSPORTE del alma a la carga y de vuelta (idea de Beltrán, 2026-09-30) ============
   Aviso (vibra + háptico que crece) → toma aire (se encoge y se hincha) → ¡pum! (colapsa a un punto de luz) → silencio →
   ¡pum! de llegada (nace pasado de tamaño y se asienta, con una onda de luz). Opcional: una chispa que salta entre los
   dos lugares durante el silencio (Estética → "Carga: chispa entre lugares"). La luz del pum y la onda viven aquí; los
   clips ponen W.pop = { p, k, s, kind }. */
const POP = { core: new THREE.Mesh(new THREE.SphereGeometry(1, 20, 14), new THREE.MeshBasicMaterial({ color: 0xfff1dc, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false, depthTest: false })),
  wave: new THREE.Mesh(new THREE.RingGeometry(.86, 1, 96), new THREE.MeshBasicMaterial({ color: 0xffe2bf, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false, depthTest: false, side: THREE.DoubleSide })),
  line: new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(), new THREE.Vector3()]), new THREE.LineBasicMaterial({ color: 0xffe2bf, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthTest: false })) };
POP.core.renderOrder = POP.wave.renderOrder = POP.line.renderOrder = 72; POP.line.frustumCulled = false;
scene.add(POP.core, POP.wave, POP.line); POP.core.visible = POP.wave.visible = POP.line.visible = false;
function tickPop() {
  const G = W.hudGlow; HUD_RIM_U.uSweep.value = G ? G.sweep : 0; HUD_RIM_U.uRimGlow.value = G ? G.glow : 0;
  const P = W.pop; POP.core.visible = POP.wave.visible = POP.line.visible = false; if (!P || P.k >= 1) return;
  const k = P.k, cq = camera.getWorldQuaternion(new THREE.Quaternion());
  if (P.kind === 'spark') {   // la chispa que salta durante el silencio
    const p = P.a.clone().lerp(P.b, inOut3(k)); POP.core.position.copy(p); POP.core.scale.setScalar(.012); POP.core.material.opacity = Math.sin(Math.PI * k); POP.core.visible = true;
    POP.line.geometry.setFromPoints([P.a.clone().lerp(P.b, Math.max(0, inOut3(k) - .25)), p]); POP.line.material.opacity = .7 * Math.sin(Math.PI * k); POP.line.visible = true; return; }
  POP.core.position.copy(P.p); POP.core.visible = true;
  POP.core.scale.setScalar(P.s * (P.kind === 'out' ? lerp(.9, .15, k) : lerp(.25, 1.1, out3(k)))); POP.core.material.opacity = Math.pow(1 - k, 2) * 1.2;
  POP.wave.material.color.set(P.col || 0xffe2bf); POP.core.material.color.set(P.col ? 0xfff6ec : 0xfff1dc); POP.wave.position.copy(P.p); POP.wave.quaternion.copy(cq); POP.wave.scale.setScalar(P.s * (1 + (P.kind === 'out' ? 3 : 7) * out3(k))); POP.wave.material.opacity = (1 - k) * (P.kind === 'out' ? .5 : .8); POP.wave.visible = true;
}

/* ============ el HALO de la carga (idea de Beltrán, 2026-09-30) ============
   Mientras se enciende la luz de la etapa en el anillo, detrás vibra un halo del color de esa etapa: un disco aditivo
   con caída suave desde el borde del anillo, que tiembla rápido (~30 Hz de brillo, ±3 % de tamaño) y respira lento.
   Nace en el primer 15 % de la carga y se apaga en el último. Los clips ponen W.halo = { n, k }. */
const HALO_U = { uCol: { value: new THREE.Color() }, uAmt: { value: 0 }, uT: { value: 0 } };
const HALO = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), new THREE.ShaderMaterial({ uniforms: HALO_U, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
  vertexShader: `varying vec2 vUv; void main(){ vUv=uv*2.-1.; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.); }`,
  fragmentShader: `uniform vec3 uCol; uniform float uAmt,uT; varying vec2 vUv;
    void main(){ float r=length(vUv); float om=smoothstep(.38,.46,r); float ring=exp(-pow((r-.5)/.14,2.))*om; float fall=smoothstep(1.,.6,r)*om*.3;   // solo por fuera del anillo: no entra al hueco del alma
      float flick=.82+.18*sin(uT*190.)*sin(uT*67.+1.3); gl_FragColor=vec4(uCol*(ring+fall)*uAmt*flick,1.); }` }));
HALO.renderOrder = 5; HALO.visible = false; scene.add(HALO);
function tickHalo(T) {
  const H = W.halo; HALO.visible = !!(H && H.k < 1 && container.visible); if (!HALO.visible) return;
  const amt = seg(H.k, 0, .15) * (1 - seg(H.k, .85, 1)); HALO_U.uAmt.value = amt * .55; HALO_U.uT.value = T; HALO_U.uCol.value.set(STAGES[H.n].color);
  const cam = camera.getWorldPosition(new THREE.Vector3()), away = container.position.clone().sub(cam).normalize();
  HALO.position.copy(container.position).addScaledVector(away, .15); HALO.quaternion.copy(camera.getWorldQuaternion(new THREE.Quaternion()));
  const d = container.position.distanceTo(cam);
  HALO.scale.setScalar(.62 * container.scale.x / 1.6 * (d + .15) / d *   // compensa que está 15 cm más atrás
    (1 + .03 * Math.sin(T * 47) + .02 * Math.sin(T * 29 + 2) + .04 * Math.sin(T * 1.6)));
}

/* ============ CARGA FINAL: un anillo de color por cada carga (Beltrán, 2026-09-30) ============
   Cinco anillos concéntricos alrededor del anillo del alma, del más interno (Entering) al más externo (Surrounding),
   igual que StageRing0..4 de BP_ChargeFx_SC en Unreal. Los clips ponen W.sr[k] (0..1) y W.ringK (anillo visible). */
const STAGE_RINGS = STAGES.map((st, k) => { const m = new THREE.Mesh(new THREE.RingGeometry(.955, 1, 128), new THREE.MeshBasicMaterial({ color: new THREE.Color(st.color).multiplyScalar(1.25), transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false, depthTest: false, side: THREE.DoubleSide }));
  m.renderOrder = 71; m.visible = false; scene.add(m); return m; });
function tickStageRings(T) {
  const cq = camera.getWorldQuaternion(new THREE.Quaternion()), s = container.scale.x * .138;   // .138 = radio exterior del anillo real
  STAGE_RINGS.forEach((m, k) => { const a = (W.sr ? W.sr[k] : 0) * (W.ringK == null ? 1 : W.ringK); m.visible = a > .002 && container.visible;
    if (!m.visible) return; m.position.copy(container.position); m.quaternion.copy(cq); m.scale.setScalar(s * (27 + 4.5 * k) / 23);
    m.material.opacity = Math.min(1, a) * (.62 + .06 * Math.sin(T * 1.7 + k * 1.3)); });
}
/* ============ LA AMEBA-PEZ (Beltrán, 2026-09-30) ============
   Después de la carga final el anillo se va y el alma sale nadando como un pez: trayectoria con curvas, un poco de
   estiramiento al nadar y una estela de chispas chicas. Determinista (depende solo del tiempo del clip): funciona
   igual al mover el cabezal. Los clips ponen W.fish = { a, b, t, dur, amp, vis }. */
const FISH = new THREE.Mesh(soul.geometry, soul.material); FISH.visible = false; FISH.renderOrder = 66; scene.add(FISH);
const FISH_N = 48, FISH_EVERY = .026, FISH_LIFE = 1.1;   // cometa: muchas chispas chicas y tenues, casi una estela continua
const FISH_SP = new THREE.Points(new THREE.BufferGeometry(), new THREE.ShaderMaterial({ uniforms: { uCol: { value: new THREE.Color(.85, .9, 1) } }, transparent: true, depthWrite: false, depthTest: false, blending: THREE.NormalBlending,   // uCol = el color del alma; mezcla normal: las chispas superpuestas no se queman a blanco
  vertexShader: `attribute float aA; attribute float aS; varying float vA; void main(){ vec4 mv=modelViewMatrix*vec4(position,1.); gl_Position=projectionMatrix*mv; gl_PointSize=max(1.,aS*(40./-mv.z)); vA=aA; }`,
  fragmentShader: `uniform vec3 uCol; varying float vA; void main(){ float r=length(gl_PointCoord-.5)*2.; float d=exp(-r*r*5.)*(1.-r); gl_FragColor=vec4(uCol,max(d,0.)*vA); }` }));
FISH_SP.geometry.setAttribute('position', new THREE.BufferAttribute(new Float32Array(FISH_N * 3), 3));
FISH_SP.geometry.setAttribute('aA', new THREE.BufferAttribute(new Float32Array(FISH_N), 1));
FISH_SP.geometry.setAttribute('aS', new THREE.BufferAttribute(new Float32Array(FISH_N), 1));
FISH_SP.frustumCulled = false; FISH_SP.renderOrder = 66; FISH_SP.visible = false; scene.add(FISH_SP);
function fishAt(F, t) {   // posición de la ameba a los t segundos del tramo
  const u = clamp(t / F.dur), e = u * u * (3 - 2 * u), base = F.a.clone().lerp(F.b, e);
  const dir = F.b.clone().sub(F.a); if (dir.lengthSq() < 1e-6) dir.set(0, 0, -1); dir.normalize();
  const perp = new THREE.Vector3().crossVectors(dir, V(0, 1, 0)); if (perp.lengthSq() < 1e-6) perp.set(1, 0, 0); perp.normalize();
  const amp = F.amp == null ? .22 : F.amp, env = .35 + .65 * Math.sin(Math.PI * Math.min(1, u * 1.2));
  return base.addScaledVector(perp, amp * env * Math.sin(t * 3.1 + (F.seed || 0))).add(V(0, .05 * Math.sin(t * 4.3 + 1) + .03 * Math.sin(t * 1.7), 0));
}
function tickFish() {
  const F = W.fish; FISH.visible = FISH_SP.visible = !!(F && F.vis > .01); FISH_HALO.visible = FISH.visible && W.fishHalo > .01; if (!FISH.visible) return;
  const p = fishAt(F, F.t), q = fishAt(F, F.t + .03), vel = q.clone().sub(p);
  FISH.position.copy(p); if (vel.lengthSq() > 1e-8) FISH.lookAt(q);
  const sw = Math.sin(F.t * 6.2), s = 1.6 * .065 / .065 * F.vis;   // mismo tamaño que el alma dentro del anillo
  FISH.scale.set(s * (1 - .06 * sw), s * (1 + .03 * sw), s * (1 + .12 * sw));
  const pos = FISH_SP.geometry.attributes.position, aA = FISH_SP.geometry.attributes.aA, aS = FISH_SP.geometry.attributes.aS;
  const last = Math.floor(F.t / FISH_EVERY);
  for (let i = 0; i < FISH_N; i++) { const n = last - i, te = n * FISH_EVERY, age = F.t - te;
    if (n < 0 || age > FISH_LIFE) { aA.setX(i, 0); continue; }
    const h = Math.sin(n * 12.9898) * 43758.5453 % 1, h2 = Math.sin(n * 78.233) * 12543.1 % 1;
    const sp = fishAt(F, te).add(V(h * .025, .012 + h2 * .015, h2 * .025).multiplyScalar(age));   // se abren poco: cola fina
    const life = 1 - age / FISH_LIFE; pos.setXYZ(i, sp.x, sp.y, sp.z); aA.setX(i, Math.pow(life, 1.7) * Math.min(1, age / .15) * .42 * F.vis); aS.setX(i, (.5 + .3 * Math.abs(h)) * (.35 + .65 * life)); }   // Beltrán 09-30: pequeñitas, que nada se sienta grande
  FISH_SP.material.uniforms.uCol.value.copy(soul.material.uniforms.uCol.value).lerp(new THREE.Color(1, 1, 1), .1);   // la estela es del color del alma
  if (FISH_HALO.visible) { FISH_HALO.position.copy(FISH.position); FISH_HALO.quaternion.copy(camera.getWorldQuaternion(new THREE.Quaternion())); FISH_HALO.scale.setScalar(.42);
    FISH_HALO.material.uniforms.uA.value = W.fishHalo * .55; FISH_HALO.material.uniforms.uCol.value.copy(soul.material.uniforms.uCol.value).lerp(new THREE.Color(1, 1, 1), .35); }
  pos.needsUpdate = aA.needsUpdate = aS.needsUpdate = true;
}

/* ============ COMPARTIR (Beltrán 09-30): dos botones de la familia del SAVE bajo el cuadro, láser + gatillo ============ */
const SHARE_G = new THREE.Group(); SHARE_G.visible = false; scene.add(SHARE_G);
const SHARE_BTNS = [['SHARE', -.15], ["DON'T SHARE", .15]].map(([txt, x]) => {   // 30 cm centro a centro (Mesh 3D)
  const b = new THREE.Group(); b.position.set(x, 0, 0); SHARE_G.add(b);
  const body = new THREE.Mesh(new THREE.ShapeGeometry(rrShape(.24, .075, .03), 8), new THREE.MeshBasicMaterial({ color: 0xc8c1b5, transparent: true, opacity: .9, depthWrite: false })); body.renderOrder = 75; b.add(body);   // borde de hormigón (el SAVE de Mesh 3D)
  const face = new THREE.Mesh(new THREE.ShapeGeometry(rrShape(.222, .06, .024), 8), new THREE.MeshBasicMaterial({ color: 0xd9d2c6, transparent: true, opacity: .85, depthWrite: false })); face.position.z = .002; face.renderOrder = 76; b.add(face);   // placa
  const strip = new THREE.Mesh(new THREE.ShapeGeometry(rrShape(.232, .068, .028), 8), new THREE.MeshBasicMaterial({ color: 0xf0c995, transparent: true, opacity: .5, depthWrite: false })); strip.position.z = .001; strip.renderOrder = 75.5; b.add(strip);   // canal con cinta de luz cálida
  const tl = textTexture(txt, 72), lab = new THREE.Mesh(new THREE.PlaneGeometry(.024 * tl.aspect, .024), new THREE.MeshBasicMaterial({ map: tl.tex, transparent: true, depthWrite: false, color: 0xfbf4ea })); lab.position.z = .004; lab.renderOrder = 77; b.add(lab);
  const glow = new THREE.Mesh(new THREE.ShapeGeometry(rrShape(.26, .09, .04), 8), new THREE.MeshBasicMaterial({ color: 0xffe9c8, transparent: true, opacity: 0, depthWrite: false, blending: THREE.AdditiveBlending })); glow.position.z = -.002; glow.renderOrder = 74; b.add(glow);
  const hit = new THREE.Mesh(new THREE.PlaneGeometry(.26, .09), new THREE.MeshBasicMaterial({ visible: false })); hit.userData.share = x < 0; b.add(hit);
  b.userData = { body, face, strip, lab, glow, hit, hov: 0 }; return b;
});
/* el arte real de Mesh 3D (SM_ShareButton_SC: Base, Plate, Slider; cara +Z, arriba +Y; texto por máscara en UV1) */
const SB_TEX = ['T_Share_Text.png', 'T_DontShare_Text.png'].map(f => { const t = new THREE.TextureLoader().load('modelos/' + f); t.flipY = false; t.anisotropy = 8; return t; });
const sbConcrete = (base) => new THREE.ShaderMaterial({ uniforms: { uA: { value: 1 } }, transparent: true, depthWrite: false,
  vertexShader: `varying vec3 vN,vV; void main(){ vN=normalize(normalMatrix*normal); vec4 mv=modelViewMatrix*vec4(position,1.); vV=normalize(-mv.xyz); gl_Position=projectionMatrix*mv; }`,
  fragmentShader: `uniform float uA; varying vec3 vN,vV; void main(){ vec3 n=normalize(vN), l=normalize(vec3(-.3,.8,.5)); float d=max(dot(n,l)*.6+.4,0.);
    vec3 c=vec3(${base.join(',')})*(.45+.6*d); gl_FragColor=vec4(c,uA); }` });
function installShareButtons(root) {
  SHARE_BTNS.forEach((b, i) => {
    const r = root.clone(true), u = b.userData, top = { uMask: { value: SB_TEX[i] }, uLit: { value: 0 }, uA: { value: 1 } };
    [u.body, u.face, u.strip, u.lab].forEach(m => m.visible = false);
    r.traverse(o => { if (!o.isMesh) return; const n = (o.material && o.material.name) || ''; o.renderOrder = 76; o.frustumCulled = false;
      if (/Ring/i.test(n)) { o.material = new THREE.MeshBasicMaterial({ color: 0xffb873, transparent: true, opacity: .7, depthWrite: false }); u.ringM = o.material; }
      else if (/Slider/i.test(n)) { o.material = new THREE.MeshBasicMaterial({ color: 0xffc98f, transparent: true, opacity: 0, depthWrite: false, blending: THREE.AdditiveBlending }); u.sliderM = o.material; }
      else if (/PlateTop/i.test(n)) { o.material = new THREE.ShaderMaterial({ uniforms: top, transparent: true, depthWrite: false,
          vertexShader: `attribute vec2 uv2; varying vec2 vT; void main(){ vT=uv2; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.); }`,
          fragmentShader: `uniform sampler2D uMask; uniform float uLit,uA; varying vec2 vT; void main(){ float m=texture2D(uMask,vT).r;
            vec3 plate=vec3(.84,.81,.76), txt=mix(vec3(.97,.95,.91),vec3(1.,.8,.55),uLit); gl_FragColor=vec4(mix(plate,txt,m),uA); }` }); u.topU = top; }
      else if (/PlateSide/i.test(n)) { o.material = sbConcrete([.80, .77, .72]); (u.mats = u.mats || []).push(o.material); }
      else { o.material = sbConcrete([.76, .73, .68]); (u.mats = u.mats || []).push(o.material); } });
    r.traverse(o => { if (/Plate/i.test(o.name) && !o.isMesh && !u.plate) u.plate = o; });
    if (!u.plate) r.traverse(o => { if (!u.plate && /Plate/i.test(o.name)) u.plate = o; });
    if (u.plate) u.plateZ = u.plate.position.z;
    b.add(r); u.real = r; u.hit.position.z = .02; });
}
loadGLB('SM_ShareButton_SC.glb').then(installShareButtons).catch(e => console.warn('Botones SHARE reales no cargados:', e && e.message));
function applyShareBtns() {
  const k = W.shareBtns; SHARE_G.visible = k > .01 && !!RES.root; if (!SHARE_G.visible) return;
  SHARE_G.position.copy(RES.root.localToWorld(V(0, -RES_H / 2 - .1, .05))); SHARE_G.quaternion.copy(RES.root.quaternion);
  SHARE_BTNS.forEach((b, i) => { const u = b.userData, a = ease(clamp(k * 1.3 - i * .3)), hovT = S.shareHov === i ? 1 : 0; u.hov = lerp(u.hov, hovT, .2);
    const pr = W.sharePress && W.sharePress[0] === i ? W.sharePress[1] : 0;
    b.scale.setScalar(Math.max(.01, a) * (1 + .04 * u.hov - .05 * Math.sin(Math.PI * pr))); b.position.z = .004 * u.hov;
    u.glow.material.opacity = (.12 * u.hov + .5 * Math.sin(Math.PI * pr)) * a; u.body.material.opacity = .9 * a; u.face.material.opacity = .85 * a;
    u.strip.material.opacity = (.45 + .5 * Math.max(u.hov, pr > 0 ? 1 : 0)) * a; u.lab.material.color.setHex(u.hov > .5 || pr > 0 ? 0xffe2b8 : 0xfbf4ea); u.lab.material.opacity = a;
    if (u.real) { const lit = Math.max(u.hov, pr > 0 ? 1 : 0); u.ringM.opacity = (.7 + .3 * lit) * a; if (u.sliderM) u.sliderM.opacity = Math.sin(Math.PI * pr) * a;
      if (u.topU) { u.topU.uLit.value = lit; u.topU.uA.value = a; } (u.mats || []).forEach(m => m.uniforms.uA.value = a);
      if (u.plate) u.plate.position.z = u.plateZ + .001 * u.hov - .004 * Math.sin(Math.PI * Math.min(1, pr * 1.6)); u.glow.material.opacity *= .5; } });
}
/* el alma en la constelación (rama SHARE): sin anillo, un poco más brillante y con halo */
const FISH_HALO = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.ShaderMaterial({ uniforms: { uA: { value: 0 }, uCol: { value: new THREE.Color(1, 1, 1) } }, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
  vertexShader: `varying vec2 vU; void main(){ vU=uv; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.); }`,
  fragmentShader: `uniform float uA; uniform vec3 uCol; varying vec2 vU; void main(){ float r=length(vU-.5)*2.; float h=exp(-r*r*6.)*.7+exp(-pow(abs(r-.62)*9.,2.))*.35; gl_FragColor=vec4(uCol,h*uA*(1.-smoothstep(.9,1.,r))); }` }));
FISH_HALO.visible = false; FISH_HALO.renderOrder = 65; scene.add(FISH_HALO);
/* el pacer muestra el avance de la etapa (Breath 09-30): pista fina dentro del aro chico, un punto por ciclo desde las 12 y un arco
   que se llena en sentido horario durante todos los ciclos; los puntos alcanzados se encienden */
const PACER_PROG = (() => { const g = new THREE.Group(), pac = envs[0].userData.pacer; g.position.copy(pac.position); g.rotation.copy(pac.rotation); envs[0].add(g);
  const track = new THREE.Mesh(new THREE.RingGeometry(.468, .472, 96), new THREE.MeshBasicMaterial({ color: 0xe9eeff, transparent: true, opacity: 0, side: THREE.DoubleSide, depthWrite: false })); g.add(track);
  const arcU = { uP: { value: 0 }, uA: { value: 0 } };
  const arc = new THREE.Mesh(new THREE.RingGeometry(.464, .476, 128), new THREE.ShaderMaterial({ uniforms: arcU, transparent: true, depthWrite: false, side: THREE.DoubleSide,
    vertexShader: `varying vec2 vP; void main(){ vP=position.xy; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.); }`,
    fragmentShader: `uniform float uP,uA; varying vec2 vP; void main(){ float a=atan(vP.y,vP.x)-1.5707963; a=mod(a,6.2831853)/6.2831853; if(a>uP) discard; gl_FragColor=vec4(.95,.97,1.,uA); }` })); g.add(arc);
  // un punto por ciclo (Cycles 5), desde las 12 en sentido del reloj (Breath 09-30)
  const dots = []; for (let k = 0; k < 5; k++) { const a = Math.PI / 2 - k / 5 * TAU, d = new THREE.Mesh(new THREE.CircleGeometry(.011, 16), new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0, side: THREE.DoubleSide, depthWrite: false }));
    d.position.set(Math.cos(a) * .47, Math.sin(a) * .47, .001); g.add(d); dots.push(d); }
  return { g, track, arcU, dots };
})();
function applyPacerProg() {
  const a = W.pacerOn ? .7 : W.pacer, p = W.pacerProg; PACER_PROG.g.visible = a > .005 && envs[0].visible;
  PACER_PROG.track.material.opacity = .18 * a; PACER_PROG.arcU.uP.value = p; PACER_PROG.arcU.uA.value = .75 * a;
  PACER_PROG.dots.forEach((d, k) => d.material.opacity = (p * PACER_PROG.dots.length >= k + 1e-3 && p > 0 ? .95 : .22) * a);
}
/* aviso inicial (Beltrán 09-30): 20 s en negro — este build es un prototipo con datos simulados (sin sensor, arranca solo) */
const DISC = (() => { const lines = [['SIMULATED PROTOTYPE', .26, .085],
    ['Soul Charger is designed to respond to your brain activity and heart rate,', .10, .05],
    ['measured live by a biofeedback sensor.', .03, .05],
    ['This build runs without the sensor: the biometric data you will see is simulated.', -.07, .05],
    ['The experience will begin on its own.', -.19, .05]];
  return lines.map(([txt, dy, h], i) => { const tt = textTexture(txt, i ? 64 : 96); const m = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ map: tt.tex, transparent: true, opacity: 0, depthWrite: false, depthTest: false, color: i ? 0xe6e9f0 : 0xfbf6ee }));
    m.userData = { dy, h, ar: tt.aspect }; m.renderOrder = 120; m.visible = false; scene.add(m); return m; }); })();
function applyDisclaimer() {
  const k = W.disclaimer; DISC.forEach((m, i) => { m.visible = k > .003; if (!m.visible) return; const ar = m.userData.ar, h = m.userData.h * Math.min(1, 1.9 / (m.userData.h * ar));   // ninguna línea más ancha que 1,9 m
    m.scale.set(h * ar, h, 1); m.position.copy(front(PS0, 2.4, m.userData.dy)); m.quaternion.copy(PS0.q);
    m.material.opacity = clamp(k * 1.6 - i * .12); });
}
/* ============ RESULTADOS · "Your Journey Through Soul Charger" (Beltrán, 2026-09-30) ============
   De vuelta en el Hall, después de la última carga: una versión grande del HUD (marco + base translúcida + ventanas
   enmarcadas). Cuatro cuadros: la calma y el ritmo cardíaco de toda la obra (las 180 casillas de 5 s del BioHub), un
   anillo por ciclo de respiración (el disco llena su anillo cuanto mejor salió el ciclo) y el gusano sonando. A la
   izquierda flota el anillo con tu alma; a la derecha, tu dibujo, del mismo alto. Con el láser se apunta a cada parte y
   arriba del panel aparece qué es. Sin datos reales (saltando con el cabezal) se ven datos de muestra. */
const RES_W = 1.1, RES_H = 1.02, RES_CW = 1.03, RES_DIST = 2.0, RES_SIDE = 1.12, BREATH_CYCLES = 4;
const RES_RING_S = RES_H * .9 / 2 / .138;   // Beltrán 09-30: el anillo grande, un poco menos que el alto del panel   // = los ciclos del pacer (1.R5b)
const RES_PXM = 1800;   // píxeles por metro de las texturas del panel
const RES_SPANS = [[.10, .28], [.28, .44], [.44, .62], [.62, .80], [.80, .97]];   // dónde cayó cada etapa en la línea de tiempo
const RES_ITEMS = {
  calm:    { name: 'CALM', stage: 2, text: 'The calm of your mind across the whole journey, read from your brain activity every few seconds. The higher the line, the quieter your mind was.' },
  heart:   { name: 'HEART RATE', stage: 1, text: 'Your heartbeat from the first step to the last: your average pulse every few seconds. Notice where it slowed down.' },
  breath:  { name: 'BREATH', stage: 0, text: 'One ring for each breathing cycle you followed in Entering. The more the light fills its ring, the closer you were to the rhythm: inhale, hold, exhale.' },
  melody:  { name: 'YOUR MELODY', stage: 3, text: 'The melody you composed in Attracting, playing again. Every sphere you placed is one of its notes.' },
  soul:    { name: 'YOUR SOUL', stage: -1, text: 'Your soul, fully charged: five lights, one for each stage you lived.' },
  drawing: { name: 'YOUR DRAWING', stage: 4, text: 'What you created in Surrounding, with your own hands.' },
};
// el panel, de arriba abajo (metros, centro del panel = 0)
const RES_ROWS = [{ key: 'calm', y: .26, h: .21 }, { key: 'heart', y: .03, h: .21 }, { key: 'breath', y: -.18, h: .17 }, { key: 'melody', y: -.38, h: .19 }];
const RES = { root: null, panel: null, art: null, proc: [], cards: {}, tip: null, tipKey: null, want: null, tipK: 0, hover: null, worm: [], orbs: [], drawing: null, beam: null, dot: null, lastStep: -1, t0: 0 };

function rrShape(w, h, r) {
  const s = new THREE.Shape(), x = -w / 2, y = -h / 2;
  s.moveTo(x + r, y); s.lineTo(x + w - r, y); s.quadraticCurveTo(x + w, y, x + w, y + r); s.lineTo(x + w, y + h - r); s.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  s.lineTo(x + r, y + h); s.quadraticCurveTo(x, y + h, x, y + h - r); s.lineTo(x, y + r); s.quadraticCurveTo(x, y, x + r, y); return s;
}
function rrFrame(w, h, r, t, depth, mat) {   // un contorno redondeado con espesor (el marco del HUD en grande)
  const s = rrShape(w, h, r); s.holes.push(rrShape(w - 2 * t, h - 2 * t, Math.max(.002, r - t)));
  return new THREE.Mesh(depth ? new THREE.ExtrudeGeometry(s, { depth, bevelEnabled: false, curveSegments: 12 }) : new THREE.ShapeGeometry(s, 12), mat);
}
function resPlane(canvas, w, h, order) {
  const t = new THREE.CanvasTexture(canvas); t.anisotropy = 8;
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ map: t, transparent: true, depthWrite: false })); m.renderOrder = order; return m;
}
function resCanvas(w, h) { const c = document.createElement('canvas'); c.width = Math.round(w * RES_PXM); c.height = Math.round(h * RES_PXM); return c; }

/* los datos: las 180 casillas del BioHub (5 s cada una); de muestra si la obra no corrió entera */
const bump = (t, a, b) => smooth(seg(t, a, a + .05)) * (1 - smooth(seg(t, b - .05, b)));
function resSeries(kind) {
  const real = S.data.journey && S.data.journey[kind]; if (real && real.length > 20) return real;
  const out = []; for (let i = 0; i < 180; i++) { const t = i / 179;
    if (kind === 'calm') out.push(clamp(.3 + .38 * smooth(t * 1.1) + .09 * Math.sin(t * 19 + 1) * (1 - .5 * t) + .045 * Math.sin(t * 57 + 2) + .14 * bump(t, .44, .62) - .08 * bump(t, .62, .8)));
    else out.push(83 - 17 * smooth(t) + 4.5 * Math.sin(t * 14 + .5) + 2 * Math.sin(t * 41) + 5 * bump(t, .62, .8) - 3 * bump(t, .44, .62)); }
  return out;
}
function resBreath() { const d = S.data.breathScores; if (d && d.length) return d.slice(0, BREATH_CYCLES); return [.62, .83, 1, .71, .96, .88, .9, .78].slice(0, BREATH_CYCLES); }
function resMelody() { return S.data.melody && S.data.melody.some(v => v >= 0) ? S.data.melody : [0, 7, 2, -1, 11, 4, -1, 14]; }

function resHead(g, it, mm, w) {   // nombre del cuadro (color de su etapa) y su dato a la derecha
  const col = it.stage >= 0 ? STAGES[it.stage].color : '#eef0f6';
  g.textBaseline = 'alphabetic'; g.fillStyle = col; g.font = `${20 * mm}px Michroma`; g.fillText(it.name, 26 * mm, 40 * mm);
  return col;
}
function resMeta(g, text, mm, w) { g.fillStyle = 'rgba(236,232,224,.72)'; g.font = `500 ${19 * mm}px Manrope`; g.textAlign = 'right'; g.fillText(text, w - 26 * mm, 40 * mm); g.textAlign = 'left'; }
function lighten(hex, k) { const c = new THREE.Color(hex); c.lerp(new THREE.Color(1, 1, 1), k); return '#' + c.getHexString(); }

function drawGraphCard(key, w, h) {
  const c = resCanvas(w, h), g = c.getContext('2d'), mm = RES_PXM / 1000, W_ = c.width, H_ = c.height, it = RES_ITEMS[key];
  const col = resHead(g, it, mm, W_), d = resSeries(key), heart = key === 'heart';
  const lo = Math.min(...d), hi = Math.max(...d), avg = d.reduce((a, b) => a + b, 0) / d.length;
  const fmtV = v => heart ? Math.round(v) + '' : Math.round(v * 100) + '';
  resMeta(g, heart ? `average ${Math.round(avg)} bpm` : `average ${Math.round(avg * 100)} / 100`, mm, W_);
  const x0 = 104 * mm, x1 = W_ - 26 * mm, yTop = 66 * mm, yBot = H_ - 42 * mm, pad = (hi - lo) * .12 || 1;
  const X = i => x0 + (x1 - x0) * i / (d.length - 1), Y = v => yBot - (yBot - yTop) * (v - (lo - pad)) / ((hi + pad) - (lo - pad));
  // guías del máximo y el mínimo, con su valor
  g.setLineDash([7 * mm, 7 * mm]); g.lineWidth = 1.6 * mm; g.strokeStyle = 'rgba(236,232,224,.28)';
  [hi, lo].forEach(v => { g.beginPath(); g.moveTo(x0, Y(v)); g.lineTo(x1, Y(v)); g.stroke(); }); g.setLineDash([]);
  g.fillStyle = 'rgba(236,232,224,.9)'; g.font = `600 ${21 * mm}px Manrope`; g.textAlign = 'right'; g.textBaseline = 'middle';
  g.fillText(fmtV(hi), x0 - 16 * mm, Y(hi)); g.fillText(fmtV(lo), x0 - 16 * mm, Y(lo)); g.textAlign = 'left';
  // el área y la línea, suavizada
  const path = () => { g.beginPath(); g.moveTo(X(0), Y(d[0])); for (let i = 1; i < d.length; i++) { const xm = (X(i - 1) + X(i)) / 2, ym = (Y(d[i - 1]) + Y(d[i])) / 2; g.quadraticCurveTo(X(i - 1), Y(d[i - 1]), xm, ym); } g.lineTo(X(d.length - 1), Y(d[d.length - 1])); };
  path(); g.lineTo(x1, yBot); g.lineTo(x0, yBot); g.closePath(); const fill = g.createLinearGradient(0, yTop, 0, yBot); fill.addColorStop(0, col + '55'); fill.addColorStop(1, col + '00'); g.fillStyle = fill; g.fill();
  path(); g.strokeStyle = col + '66'; g.lineWidth = 11 * mm; g.lineJoin = g.lineCap = 'round'; g.stroke();
  path(); g.strokeStyle = lighten(col, .45); g.lineWidth = 4 * mm; g.stroke();
  // la banda de las etapas: el mismo color de cada luz del anillo
  const yb = H_ - 22 * mm; RES_SPANS.forEach(([a, b], i) => { g.fillStyle = STAGES[i].color; g.globalAlpha = .85; g.fillRect(x0 + (x1 - x0) * a + 2 * mm, yb, (x1 - x0) * (b - a) - 4 * mm, 6 * mm); });
  g.globalAlpha = 1; g.fillStyle = 'rgba(236,232,224,.5)'; g.font = `500 ${15 * mm}px Manrope`; g.textBaseline = 'middle'; g.fillText('start', 26 * mm, yb + 3 * mm); g.textAlign = 'right'; g.fillText('end', W_ - 6 * mm, yb - 12 * mm); g.textAlign = 'left';
  return c;
}
function drawBreathCard(w, h) {
  const c = resCanvas(w, h), g = c.getContext('2d'), mm = RES_PXM / 1000, W_ = c.width, H_ = c.height, it = RES_ITEMS.breath;
  const col = resHead(g, it, mm, W_), sc = resBreath(); resMeta(g, `${sc.length} cycles · inhale, hold, exhale`, mm, W_);
  const n = sc.length, x0 = 70 * mm, x1 = W_ - 70 * mm, cy = H_ * .6, R = Math.min(46 * mm, (x1 - x0) / (n - 1) * .36);
  sc.forEach((s, i) => { const x = n > 1 ? x0 + (x1 - x0) * i / (n - 1) : W_ / 2, full = s >= .95, r = full ? R - 2.5 * mm : Math.max(4 * mm, s * (R - 9 * mm));
    // el anillo = el ciclo perfecto
    g.beginPath(); g.arc(x, cy, R, 0, TAU); g.strokeStyle = full ? lighten(col, .5) : col + 'cc'; g.lineWidth = (full ? 4.5 : 3.2) * mm;
    if (full) { g.shadowColor = col; g.shadowBlur = 26 * mm; } g.stroke(); g.shadowBlur = 0;
    // el disco = cuánto se acercó
    const rg = g.createRadialGradient(x - r * .25, cy - r * .3, r * .1, x, cy, r); rg.addColorStop(0, lighten(col, .75)); rg.addColorStop(1, col);
    g.beginPath(); g.arc(x, cy, r, 0, TAU); g.fillStyle = rg; if (full) { g.shadowColor = col; g.shadowBlur = 30 * mm; } g.fill(); g.shadowBlur = 0; });
  return c;
}
function drawMelodyCard(w, h) {
  const c = resCanvas(w, h), g = c.getContext('2d'), mm = RES_PXM / 1000, W_ = c.width, it = RES_ITEMS.melody;
  resHead(g, it, mm, W_); resMeta(g, '♪  playing', mm, W_); return c;
}
function drawResHeader(w, h) {
  const c = resCanvas(w, h), g = c.getContext('2d'), mm = RES_PXM / 1000, W_ = c.width;
  g.textAlign = 'center'; g.textBaseline = 'alphabetic'; g.fillStyle = '#f1ece2'; g.font = `${29 * mm}px Michroma`; g.fillText('YOUR JOURNEY THROUGH SOUL CHARGER', W_ / 2, 44 * mm);
  g.fillStyle = 'rgba(236,232,224,.6)'; g.font = `500 ${18 * mm}px Manrope`; g.fillText('14 min  ·  5 stages  ·  5 lights', W_ / 2, 74 * mm); return c;
}
function drawResTip(key, w, h) {
  const c = resCanvas(w, h), g = c.getContext('2d'), mm = RES_PXM / 1000, W_ = c.width, H_ = c.height, it = RES_ITEMS[key];
  const col = it.stage >= 0 ? STAGES[it.stage].color : '#eef0f6', r = 26 * mm, p = 4 * mm;
  g.beginPath(); g.roundRect ? g.roundRect(p, p, W_ - 2 * p, H_ - 2 * p, r) : g.rect(p, p, W_ - 2 * p, H_ - 2 * p);
  g.fillStyle = 'rgba(15,17,25,.74)'; g.fill(); g.lineWidth = 2.4 * mm; g.strokeStyle = 'rgba(236,228,214,.55)'; g.stroke();
  g.fillStyle = col; g.fillRect(34 * mm, 30 * mm, 5 * mm, H_ - 60 * mm);   // la marca del color de su luz
  g.textBaseline = 'alphabetic'; g.fillStyle = col; g.font = `${19 * mm}px Michroma`; g.fillText(it.name, 60 * mm, 50 * mm);
  g.fillStyle = '#f1ece2'; g.font = `500 ${23 * mm}px Manrope`; const words = it.text.split(' '), maxW = W_ - 96 * mm; let line = '', y = 86 * mm;
  words.forEach(wd => { const t = line ? line + ' ' + wd : wd; if (g.measureText(t).width > maxW) { g.fillText(line, 60 * mm, y); line = wd; y += 31 * mm; } else line = t; }); if (line) g.fillText(line, 60 * mm, y);
  return c;
}

/* el dibujo: tus trazos (o unos de muestra), centrados y del alto del panel */
function resDemoStrokes(group) {
  const blades = [[-.2, .95, .07, 0], [-.07, .78, -.05, 1], [.05, 1.0, .06, 2], [.16, .7, -.08, 1], [-.14, .6, .09, 3], [.1, .85, .02, 0], [.22, .55, .1, 2]];
  blades.forEach(([x, hgt, lean, ci], b) => {
    const pts = []; for (let j = 0; j <= 24; j++) { const t = j / 24; pts.push(V(x + lean * t + .035 * Math.sin(t * 5.5 + b) * t, t * hgt, .03 * Math.sin(t * 4 + b * 1.7))); }
    const curve = new THREE.CatmullRomCurve3(pts), T = 96, R = 6, geo = new THREE.TubeGeometry(curve, T, .011 + .004 * (b % 3), R, false);
    const pos = geo.attributes.position, cp = new THREE.Vector3(), v = new THREE.Vector3();
    for (let j = 0; j <= T; j++) { const f = .12 + .88 * Math.pow(Math.sin(Math.PI * Math.min(1, j / T * 1.08)), .7); curve.getPointAt(j / T, cp);
      for (let r = 0; r <= R; r++) { const i = j * (R + 1) + r; v.fromBufferAttribute(pos, i).sub(cp).multiplyScalar(f).add(cp); pos.setXYZ(i, v.x, v.y, v.z); } }
    gradientAlong(geo, T, R, PAL_COLORS[ci], PAL_TAILS[ci], ci === 0);
    const glow = b === 2 || b === 5;
    group.add(new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ color: 0xffffff, vertexColors: true, transparent: glow, blending: glow ? THREE.AdditiveBlending : THREE.NormalBlending, depthWrite: !glow })));
  });
}
function resBuildDrawing() {
  const g = new THREE.Group(), src = envs[4].userData.strokes;
  if (src.children.length) src.children.forEach(m => g.add(new THREE.Mesh(m.geometry.clone(), m.material))); else resDemoStrokes(g);   // copia: el crecimiento no toca la etapa
  const box = new THREE.Box3().setFromObject(g), size = box.getSize(new THREE.Vector3()), ctr = box.getCenter(new THREE.Vector3());
  const s = Math.min(.95 / Math.max(size.y, 1e-3), .62 / Math.max(size.x, size.z, 1e-3));
  g.children.forEach(m => { m.position.sub(ctr); m.renderOrder = 66; });
  const holder = new THREE.Group(); holder.add(g); holder.scale.setScalar(s); holder.userData.s0 = s; return holder;
}

function buildResults() {
  const root = new THREE.Group(), panel = new THREE.Group(); root.add(panel); root.visible = false; scene.add(root);
  // el marco (borde + contorno interior), la base translúcida
  const rim = rrFrame(RES_W, RES_H, .06, .011, .012, hudRim(0xb9b2a7, .55)); rim.renderOrder = 74; panel.add(rim); RES.proc.push(rim);
  const bez = rrFrame(RES_W - .034, RES_H - .034, .045, .003, .004, new THREE.MeshBasicMaterial({ color: 0xe9e2d6, transparent: true, opacity: .3, depthWrite: false })); bez.renderOrder = 74; panel.add(bez); RES.proc.push(bez);
  const glass = new THREE.Mesh(new THREE.ShapeGeometry(rrShape(RES_W - .01, RES_H - .01, .055), 12), new THREE.MeshBasicMaterial({ color: 0x151823, transparent: true, opacity: .55, depthWrite: false }));
  glass.position.z = -.004; glass.renderOrder = 70; panel.add(glass); RES.proc.push(glass);
  const head = resPlane(drawResHeader(RES_CW, .095), RES_CW, .095, 73); head.position.set(0, .4325, .006); panel.add(head);
  // los cuatro cuadros: ventana enmarcada (como la del EEG en el HUD) + su contenido
  RES_ROWS.forEach(row => {
    const g = new THREE.Group(); g.position.set(0, row.y, .006); panel.add(g);
    const fill = new THREE.Mesh(new THREE.ShapeGeometry(rrShape(RES_CW, row.h, .03), 10), new THREE.MeshBasicMaterial({ color: 0x0b0d14, transparent: true, opacity: .3, depthWrite: false })); fill.renderOrder = 71; g.add(fill);
    const frameMat = new THREE.MeshBasicMaterial({ color: 0xe9e2d6, transparent: true, opacity: .34, depthWrite: false });
    const frame = rrFrame(RES_CW, row.h, .03, .0035, .003, frameMat); frame.renderOrder = 72; g.add(frame); RES.proc.push(fill, frame);
    const cv = row.key === 'breath' ? drawBreathCard(RES_CW, row.h) : row.key === 'melody' ? drawMelodyCard(RES_CW, row.h) : drawGraphCard(row.key, RES_CW, row.h);
    const content = resPlane(cv, RES_CW, row.h, 73); content.position.z = .002; content.userData.resKey = row.key; g.add(content);
    RES.cards[row.key] = { group: g, frameMat, fillMat: fill.material, content };
  });
  // el gusano en su cuadro: ocho gotas (los pasos) con las esferas que colocaste, y el cabezal que las va encendiendo
  const my = RES_ROWS[3].y - .015, mel = resMelody();
  for (let k = 0; k < 8; k++) { const x = -.385 + k * .11;
    const m = new THREE.Mesh(new THREE.IcosahedronGeometry(.04, 3), blobMat('#e5c6a3', .85)); m.position.set(x, my + Math.sin(k * .9) * .01, .045); m.renderOrder = 76; panel.add(m); RES.worm.push(m);
    const v = mel[k]; if (v >= 0) { const o = new THREE.Mesh(new THREE.IcosahedronGeometry(.02, 2), blobMat(`hsl(${20 + v * 1.8},40%,78%)`, .95)); o.position.copy(m.position).add(V(0, 0, .012)); o.renderOrder = 77; panel.add(o); RES.orbs.push(o); } }
  RES.cards.melody.content.userData.worm = true;
  // el texto que explica, arriba del panel
  RES.tip = resPlane(resCanvas(.92, .17), .92, .17, 78); RES.tip.position.set(0, RES_H / 2 + .115, .01); RES.tip.material.opacity = 0; root.add(RES.tip);
  // el dibujo, a la derecha y del alto del panel, girado hacia ti
  RES.drawing = resBuildDrawing(); RES.drawing.position.set(RES_SIDE, 0, .05); RES.drawing.rotation.y = -.32; root.add(RES.drawing);
  RES.drawHit = new THREE.Mesh(new THREE.PlaneGeometry(.66, 1.0), new THREE.MeshBasicMaterial({ visible: false })); RES.drawHit.position.copy(RES.drawing.position); RES.drawHit.rotation.y = -.32; RES.drawHit.userData.resKey = 'drawing'; root.add(RES.drawHit);
  RES.ringHit = new THREE.Mesh(new THREE.CircleGeometry(.42, 32), new THREE.MeshBasicMaterial({ visible: false })); RES.ringHit.position.set(-RES_SIDE, 0, .05); RES.ringHit.rotation.y = .32; RES.ringHit.userData.resKey = 'soul'; root.add(RES.ringHit);
  // el láser (como el de ATTRACTING): una varilla fina de luz y su punto
  RES.beam = new THREE.Mesh(new THREE.CylinderGeometry(.0018, .0018, 1, 8, 1, true), new THREE.MeshBasicMaterial({ color: 0xffe3c4, transparent: true, opacity: .75, blending: THREE.AdditiveBlending, depthWrite: false }));
  RES.beam.renderOrder = 80; RES.beam.visible = false; scene.add(RES.beam);
  RES.dot = new THREE.Mesh(new THREE.SphereGeometry(.009, 12, 8), new THREE.MeshBasicMaterial({ color: 0xfff1de })); RES.dot.renderOrder = 81; RES.dot.visible = false; scene.add(RES.dot);
  RES.root = root; RES.panel = panel;
  if (MODELS.results) useResultsArt(MODELS.results);
}
/* el marco REAL del cuadro (Mesh 3D, SM_Results_SC.glb: cara +Z, alto +Y, en metros): reemplaza al marco procedural */
function useResultsArt(src) {
  if (RES.art || !RES.panel) return; const art = src.clone(true); RES.art = art; RES.proc.forEach(m => m.visible = false);
  art.traverse(o => { if (!o.isMesh) return; const n = (o.material && o.material.name) || '', nn = o.name + ' ' + (o.parent ? o.parent.name : '');
    const key = /Calm/.test(nn) ? 'calm' : /Heart/.test(nn) ? 'heart' : /Breath/.test(nn) ? 'breath' : /Melody/.test(nn) ? 'melody' : null;
    if (/Tip/.test(n) || /Tip/.test(nn)) { o.visible = false; return; }   // la cajita la dibuja el texto de la web
    if (/Rim/.test(n)) { o.material = hudRim(0xb9b2a7, .55); o.renderOrder = 74; }
    else if (/Pane/.test(n)) { o.material = new THREE.MeshBasicMaterial({ color: 0x0b0d14, transparent: true, opacity: .3, depthWrite: false }); o.renderOrder = 71; if (key) RES.cards[key].fillMat = o.material; }
    else if (/Frame/.test(n)) { o.material = new THREE.MeshBasicMaterial({ color: 0xe9e2d6, transparent: true, opacity: .34, depthWrite: false }); o.renderOrder = 72; if (key) RES.cards[key].frameMat = o.material; }
    else { o.material = new THREE.MeshBasicMaterial({ color: 0x151823, transparent: true, opacity: .55, depthWrite: false }); o.renderOrder = 70; } });
  art.position.z = -.004; RES.panel.add(art);
}
loadGLB('SM_Results_SC.glb').then(r => { MODELS.results = r; useResultsArt(r); }).catch(e => console.warn('Cuadro real no cargado:', e && e.message));
APPEAR.results = { get: () => RES.panel, axis: [0, 0, 1], r: 0, h: 0, trace: false };   // el panel entra con la aparición luz primero
function resPlace(p) {   // frente a la pose p (Hall, parada 2)
  if (!RES.root) buildResults();
  RES.root.position.copy(front(p, RES_DIST, .02)); RES.root.quaternion.copy(p.q);
}
function resRingPos(p) { return front(p, RES_DIST - .05, .02, -RES_SIDE); }
function resRingQuat(p) { return p.q.clone().multiply(new THREE.Quaternion().setFromEuler(new THREE.Euler(0, .32, 0))); }
function growStrokes(holder, gk) {
  const ms = holder.children[0] ? holder.children[0].children : [], N = ms.length;
  ms.forEach((m, i) => { const a = N > 1 ? i / N * .75 : 0, f = clamp((gk - a) / .25), geo = m.geometry;
    const cnt = geo.index ? geo.index.count : geo.attributes.position.count; geo.setDrawRange(0, Math.floor(cnt * f / 3) * 3); m.visible = f > .001; });
}
function tickResults(T, dt) {
  if (!RES.root) return; const on = W.results > 0; RES.root.visible = on; if (!on) { RES.beam.visible = RES.dot.visible = false; RES.hover = null; return; }
  const k = W.results;
  // el dibujo y el anillo aparecen con el panel; el dibujo se mece como en la mesa
  RES.drawing.scale.setScalar(RES.drawing.userData.s0 * Math.max(.001, out3(seg(k, .1, .5))));
  growStrokes(RES.drawing, W.drawGrow == null ? 1 : W.drawGrow);   // trazo a trazo, del primero al último
  RES.drawing.rotation.y = -.32 + Math.sin(T * .35) * .18;
  // el gusano suena: el cabezal recorre los ocho pasos (5,333 s la vuelta) y toca las notas que colocaste
  const mel = resMelody(), step = Math.floor(((T - RES.t0) / (5.333 / 8)) % 8);
  RES.worm.forEach((m, i) => m.material.uniforms.uGlow.value = i === step ? .9 : (mel[i] >= 0 ? .22 : 0));
  if (W.resPlay && step !== RES.lastStep && S.playing) { RES.lastStep = step; const real = typeof audioFor === 'function';
    if (mel[step] >= 0) { const oid = 'FX_ORB_' + (mel[step] + 1); if (!(real && playSoundId(oid))) tone(NOTE[mel[step] % 5] * (1 + (mel[step] / 5 | 0) * .5), .6, 'triangle', .05); }
    if (step % 2 === 0 && !(real && audioFor('PAD_M1'))) tone(110, .4, 'sine', .03); }
  // el láser: apuntas a una parte y arriba aparece qué es
  let key = null, hit = null;
  if (W.resBeam) { const targets = [...Object.values(RES.cards).map(c => c.content), RES.drawHit, RES.ringHit]; hit = pick(targets); key = hit ? hit.object.userData.resKey : null; }
  RES.beam.visible = RES.dot.visible = !!W.resBeam;
  if (W.resBeam) { const a = camera.localToWorld(V(.14, -.24, -.38)), b = hit ? hit.point : a.clone().add(ray.ray.direction.clone().multiplyScalar(4)), len = a.distanceTo(b);
    RES.beam.position.copy(a).lerp(b, .5); RES.beam.scale.set(1, len, 1); RES.beam.quaternion.setFromUnitVectors(V(0, 1, 0), b.clone().sub(a).normalize()); RES.dot.position.copy(b); RES.dot.visible = !!hit; }
  if (key !== RES.hover) { if (key) { cue('hap', 'HAP_TICK'); cue('fx', 'FX_ORBHOVER'); } RES.hover = key; }
  Object.entries(RES.cards).forEach(([ck, c]) => { const h = ck === key; c.frameMat.opacity = lerp(c.frameMat.opacity, h ? .95 : .34, .2); c.fillMat.opacity = lerp(c.fillMat.opacity, h ? .12 : .3, .2); });
  // el texto: se funde, cambia y vuelve
  RES.want = key || null;
  if (RES.want !== RES.tipKey) { RES.tipK = Math.max(0, RES.tipK - dt * 6); if (RES.tipK <= 0) { RES.tipKey = RES.want; if (RES.tipKey) { const m = RES.tip.material; m.map && m.map.dispose(); m.map = new THREE.CanvasTexture(drawResTip(RES.tipKey, .92, .17)); m.map.anisotropy = 8; m.needsUpdate = true; } } }
  else if (RES.tipKey) RES.tipK = Math.min(1, RES.tipK + dt * 5);
  RES.tip.material.opacity = RES.tipK * seg(k, .8, 1); RES.tip.visible = RES.tipK > .01;
}
