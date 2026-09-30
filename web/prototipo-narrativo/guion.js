/* Soul Charger · prototipo narrativo · EL GUION V5 COMO LÍNEA DE TIEMPO (docs/GUION-V5-2026-09-29.md)
   Cada momento (beat) agrupa sus clips. Un clip se ancla con `at`:
     número            → segundos desde el inicio del momento
     ['KEY', 'end', 2] → 2 s después del fin del clip KEY (del mismo momento); 'start' para su inicio
     ['1.4/WALK1']     → un clip de otro momento · ['1.4', 'start', 19] → otro momento
   `end` hace que un clip dure hasta un ancla (el fantasma dura lo que dura la espera).
   `apply(k)` fija el estado del mundo para el avance k (0..1) y se sigue aplicando con k = 1 cuando el clip termina. */
'use strict';

/* ---------- lugares y poses ---------- */
const WEST = V(-HALL.rIn * 1.05, 0, 0), EAST = V(HALL.rIn * 1.05, 0, 0);
const P0 = V(-40, 0, 0), P1 = V(-HALL.rIn * 1.05 - 2.5, 0, 0), P2 = V(-3.2, 0, 0);
const FACE_EAST = -Math.PI / 2, FACE_WEST = Math.PI / 2;
const PS0 = pose(P0.x, 0, FACE_EAST), PS1 = pose(P1.x, 0, FACE_EAST), PS2 = pose(P2.x, 0, FACE_EAST), PSC = pose(CENTER.x, 0, FACE_EAST);
const PSD = pose(EAST.x + 1.5, 0, FACE_EAST);
const PF1 = pose(EAST.x + 4, 0, FACE_WEST), PF2 = pose(3.2, 0, FACE_WEST), PF3 = pose(P0.x - 10, 0, FACE_WEST);

const BELL_POS = front(PS1, .7, -.3), SENSOR_POS = front(PS2, .55, -.22), CONT_HALL = front(PS2, .7, -.25), CONT_C = front(PSC, .75, -.1);
const CAND_POS = [0, 1, 2, 3, 4].map(i => { const a = (i - 2) * .38, c = Math.cos(PS2.yaw), s = Math.sin(PS2.yaw), lx = Math.sin(a) * 1.05, lz = -Math.cos(a) * 1.05; return V(PS2.x + lx * c + lz * s, EYE - .15, PS2.z - lx * s + lz * c); });
const SOUL_PRESENT = V(0, 1.6, 0), SOUL_PRESENT_S = .5 / .13;   // 50 cm (el alma mide .13 a escala 1)
const ALMA_HALL = V(0, 1.35, 0), ALMA_RES = front(PF2, 3.3, .75, -2.2), ALMA_SIDE = V(-1.2, 1.45, -1.3), ALMA_ST = front(PSC, 2.2, .15, -.8), ALMA_ST2 = front(PSC, 2.6, .3, -1.6);
const MOTE_FROM = front(PSC, 6, 1.5, -2);
// ENSAYO de etapa (ensayo.js, generado desde Unreal): lo que Beltrán mueve en los TargetPoints sc<K>_* se mueve igual acá
const ensAdd = (v, k, nm) => { const d = ensDelta(k, nm); return v.clone().add(front(PSC, d.f, d.u, d.s).sub(front(PSC, 0, 0, 0))); };
const almaSt = k => ensAdd(ALMA_ST, k, 'alma_in'), almaSt2 = k => ensAdd(ALMA_ST2, k, 'alma_side'), contC = k => ensAdd(CONT_C, k, 'charge');
const mote = new THREE.Mesh(new THREE.SphereGeometry(.03, 12, 8), new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true })); mote.visible = false; scene.add(mote);
card.position.copy(front(PF2, 1.6, 0)); card.quaternion.copy(PF2.q); card.updateMatrixWorld(true);
const CARD_SLOT = card.localToWorld(V(-.62, .18, .02));
const STARS = buildConstellation(PF3);

/* ---------- ayudantes de estado ---------- */
const _lv = new THREE.Vector3();
const lv = (a, b, k) => _lv.copy(a).lerp(b, k);
function almaAt(p, s) { alma.visible = s > .011; alma.position.copy(p); alma.scale.setScalar(Math.max(.01, s) * ALMA_SIZE); alma.userData.s = s; }
const TL_TITLES = [];
function titleAt(text, grad, p, dist, dy, h, white = false) {
  const m = titleMesh(text, h, grad, { white, depthTest: false, order: 70 }); m.position.copy(front(p, dist, dy)); m.quaternion.copy(p.q); m.visible = false; scene.add(m); TL_TITLES.push(m); return m;
}
function revealTitle(m, k) { m.visible = true; m.material.uniforms.uR.value = ease(k); }
function outTitle(m, k) { m.material.uniforms.uO.value = ease(k); if (k >= 1) m.visible = false; }
function contTo(target, k, s0, s1, q) { W.cont = 'world'; container.position.lerp(target, ease(k)); if (s0 != null) container.scale.setScalar(lerp(s0, s1, ease(k))); if (q) container.quaternion.copy(q); }
/* el alma se teletransporta: aviso → toma aire → ¡pum! → silencio → ¡pum! de llegada. from/to: () => posición; s0/s1 escalas;
   q0/q1: () => orientación; toHud: al final queda anclada al HUD. La última pieza lleva la key `key` (para anclar lo que sigue). */
function teleport(key, at, from, to, s0, s1, q0, q1, toHud, o = {}) {
  const W1 = key + '_WARN', OUT = key + '_OUT', GAP = key + '_GAP';
  clip({ key: W1, track: 'obj', label: 'El alma vibra y toma aire', dur: .8, at, apply: (k, local) => {
    W.cont = 'world'; const a = .0016 * seg(k, 0, .75) * (s0 / HUD_RING_S > 3 ? 4 : 1), w = seg(k, .75, 1);
    const cam = camera.getWorldQuaternion(new THREE.Quaternion()), j = new THREE.Vector3(Math.sin(local * 97) * a, Math.sin(local * 83 + 1.7) * a, 0).applyQuaternion(cam);
    container.position.copy(from()).add(j); container.quaternion.copy(q0()); container.scale.setScalar(s0 * (1 - .1 * Math.sin(Math.PI * Math.min(1, w / .45)) * (w < .45 ? 1 : 0) + .25 * Math.pow(seg(w, .45, 1), 2)));
    if (!toHud) W.hudGlow = { sweep: inOut3(k), glow: .35 + .65 * k }; } });   // el HUD se ilumina: una luz le da la vuelta hasta soltar el alma
  if (o.warnFx) fx(o.warnFx, [W1, 'start'], 'aviso'); hap('HAP_CHARGE_RAMP', [W1, 'start'], 'aviso: crece 0,1 → 0,7');
  clip({ key: OUT, track: 'obj', label: '¡Pum! desaparece', dur: .12, at: [W1, 'end'], apply: k => {
    if (!toHud) W.hudGlow = { sweep: 1, glow: 1.6 - .3 * k };
    W.cont = k < 1 ? 'world' : 'off'; container.position.copy(from()); container.quaternion.copy(q0()); container.scale.setScalar(Math.max(.001, s0 * 1.25 * (1 - k)));
    if (k < 1) W.pop = { p: from(), k: k * .35, s: .03 * s0 / HUD_RING_S * (s0 > .5 ? .25 : 1), kind: 'out' }; } });
  fx('FX_SOULPOP_OUT', [OUT, 'start'], '¡pum! de salida'); hap('HAP_PULSE_STRONG', [OUT, 'start'], 'golpe corto');
  clip({ key: GAP, track: 'obj', label: 'Silencio (el ojo busca)', dur: .45, at: [OUT, 'end'], apply: k => {
    if (!toHud) W.hudGlow = { sweep: 1, glow: 1.3 * Math.pow(1 - k, 2) };
    W.cont = 'off'; const s = .03 * s0 / HUD_RING_S * (s0 > .5 ? .25 : 1); if (k < 1) W.pop = { p: from(), k: .35 + .65 * k, s, kind: 'out' };
    if (S.tw.spark && k < 1) W.pop = { a: from(), b: to(), k, kind: 'spark' }; } });
  clip({ key, track: 'obj', label: toHud ? '¡Pum! vuelve al HUD' : '¡Pum! aparece girando donde se carga', dur: toHud ? .6 : 1.1, at: [GAP, 'end'], apply: k => {
    const e = k < .55 ? out3(k / .55) * 1.1 : lerp(1.1, 1, inOut3((k - .55) / .45));
    if (k >= 1 && toHud) { W.cont = 'hud'; container.scale.setScalar(s1); return; }
    W.cont = 'world'; container.position.copy(to()); container.quaternion.copy(q1());
    if (toHud) { container.scale.setScalar(Math.max(.001, s1 * e)); W.hudGlow = { sweep: 1, glow: .7 * (1 - k) }; }
    else {   // el anillo nace con su aparición luz primero (rendija → párpado) y gira sobre su eje 1¼ vueltas, frenando
      container.scale.setScalar(s1 * lerp(.55, 1, out3(seg(k, 0, .3)))); if (k < 1) W.appear.ring = k;
      container.rotateZ(-Math.PI * 2.5 * Math.pow(1 - k, 3)); }
    if (k < 1) W.pop = { p: to(), k, s: toHud ? .03 : .16, kind: 'in' }; } });
  fx('FX_SOULPOP_IN', [key, 'start'], '¡pum! de llegada'); hap('HAP_PULSE_STRONG', [key, 'start'], 'golpe de llegada');
  if (toHud) { fx('FX_SOULSETTLE', [key, 'end'], 'se asienta en el nido'); hap('HAP_TICK', [key, 'end']); }
}
/* el anillo vuelve al HUD: parte de donde esté (lo dejó el clip anterior en este mismo cuadro) */
function toHudClip(key, at, s0) {
  fx('FX_SOULTOFACE', at, 'VFX_SOULTOFACE');
  return clip({ key, track: 'obj', label: 'El anillo se ancla al HUD', dur: 1.5, at, apply: k => {
    if (k >= 1) { W.cont = 'hud'; container.scale.setScalar(HUD_RING_S); return; }
    W.cont = 'world'; container.position.lerp(hudWorldPos(), ease(k)); container.scale.setScalar(lerp(s0, HUD_RING_S, ease(k))); container.quaternion.copy(camera.getWorldQuaternion(new THREE.Quaternion())).slerp(hudWorldQuat(), ease(k));
  } });
}
const GRAD_TITLE = [[.86, .9, 1], [.62, .7, .95], [.42, .5, .86], [.2, .26, .55]];

/* ================= ACTO 0 ================= */
act('Acto 0 · Arranque');
beatTL('0', 'Negro', 'Aviso de 20 s en negro: este build es un prototipo con datos simulados (sin sensor; arranca solo). Después, el pawn se recentra y el nivel se precalienta en negro.', null, () => {
  fx('FX_DISCLAIMER', 0, 'aviso: prototipo simulado');
  clip({ key: 'DISCLAIMER', track: 'world', label: 'Aviso: SIMULATED PROTOTYPE (datos biométricos simulados, arranca solo)', dur: 20, at: 0, apply: k => { const s = k * 20; W.disclaimer = s < 17.5 ? ease(clamp(s / 2.5)) : 1 - ease(clamp((s - 17.5) / 2)); } });
  clip({ key: 'NEGRO', track: 'world', label: 'Negro · el nivel se precalienta', dur: 3, at: ['DISCLAIMER', 'end'] });
});

/* ================= ACTO 1 · INICIO ================= */
act('Acto 1 · Inicio');
const T_MAIN = titleAt('SOUL CHARGER', GRAD_TITLE, PS0, 4, .35, .42), T_SUB = titleAt('A VR Interactive Biofeedback Experience by Alma Digital', GRAD_TITLE, PS0, 4, .02, .09, true);
beatTL('1.1', 'La niebla azul', 'Del negro a un azul suave con niebla. Polvo diminuto que se arremolina con las manos.', null, () => {
  amb('AMB_01');
  fx('FX_DUSTSWIRL', 0, 'sigue la velocidad de la mano');
  clip({ key: 'FOG_IN', track: 'world', label: 'Niebla azul y polvo entran', vfx: 'VFX_INTROFOG + VFX_DUST', dur: 3, at: 0, apply: k => { voidSky.material.uniforms.uAmt.value = k; dustMat.uniforms.uAmt.value = k; } });
});
beatTL('1.2', 'El título', 'SOUL CHARGER y su bajada. El mismo material líquido de los títulos de transición.', null, () => {
  fx('FX_TITLE');
  clip({ key: 'TITLE_IN', track: 'world', label: 'Título SOUL CHARGER', vfx: 'VFX_TITLEREVEAL', dur: 4.5, at: 0, apply: k => revealTitle(T_MAIN, k) });
  clip({ key: 'SUB_IN', track: 'world', label: 'Bajada del título', dur: 2, at: ['TITLE_IN', 'end'], apply: k => revealTitle(T_SUB, k) });
});
beatTL('1.3', 'Quietos con el título', 'Estamos quietos en la niebla azul mientras el título se queda unos segundos (Beltrán 09-30; en Unreal IntroHold 12 s del Hall). El build de la postulación arranca solo (sin OSC).', null, () => {
  clip({ key: 'ESPERA_OSC', track: 'int', label: 'Espera del play · el polvo responde a las manos (interacción libre, sin instrucción)', dur: 7, at: 0 });
  clip({ key: 'OSC', track: 'int', label: 'OSC /soulcharger/start', dur: 0, at: ['ESPERA_OSC', 'end'], vfx: 'OSC /soulcharger/start · prueba: automático' });
});
beatTL('1.4', 'El viaje', 'Se va el título y empezamos a avanzar entre motas frías del espacio (dan la sensación de avance). La niebla azul se va a negro hacia la mitad del trayecto; recién ahí aparece el Hall, en el negro. Los pasos suenan solo al final, llegando (Beltrán 09-30).', null, () => {
  amb('AMB_02');
  clip({ key: 'TITLE_OUT', track: 'world', label: 'Se van los títulos', vfx: 'VFX_TITLEOUT', dur: 2.5, at: 0, apply: k => { outTitle(T_MAIN, k); outTitle(T_SUB, k); } });
  clip({ key: 'SKY_OFF', track: 'world', label: 'La niebla azul se va a negro hacia la mitad del viaje', dur: 12, at: 0, apply: k => voidSky.material.uniforms.uAmt.value = 1 - ease(k) });
  clip({ key: 'HALL_LOAD', track: 'world', label: 'Recién en el negro aparece el Hall (antes está oculto)', dur: 0, at: ['SKY_OFF', 'end'], apply: () => { hallG.visible = true; } });
  walk('WALK1', 'Avanza entre las motas (los pasos suenan solo al llegar)', PS0, PS1, 25, 0, { stepsAt: .85 });
  vo('VO_01a', 'What resonates inside you when you hear the word "soul"?… What does it mean to you?', 3);
  vo('VO_01b', 'Listen to the sounds around you.', ['VO_01a', 'end', 3]);
  vo('VO_01c', 'As you get comfortable in your seat, take a moment to listen… What is the sound of your soul?', ['VO_01b', 'end', 3]);
});
beatTL('1.5', 'Aparece el portal', 'En la oscuridad, la puerta redonda: el interior se enciende cálido detrás del vidrio esmerilado.', ['1.4', 'start', 19], () => {
  fx('FX_PORTALGLOW');
  clip({ key: 'PORTAL', track: 'world', label: 'El interior se enciende: el portal', vfx: 'VFX_HALLGLOW · MPC_Room.RoomLight 0→1', dur: 4, at: 0, apply: k => hallU.uLight.value = k * .9 });
  clip({ key: 'GROOVE_WAIT', track: 'world', label: 'Las hendiduras del domo esperan apagadas', at: 0, end: ['1.10', 'start'], during: () => { W.hallWave = 0; } });
});
beatTL('1.6', 'SOUL CHARGER CENTER', 'A la derecha de la puerta, en dos líneas alineadas a la izquierda, cálido suave (Beltrán, 09-30).', ['1.4/WALK1', 'end'], () => {
  fx('FX_TITLE_WARM');
  clip({ key: 'CENTER_T', track: 'world', label: 'SOUL CHARGER / CENTER, a la derecha de la puerta', dur: 3, at: 0, apply: k => { W.hallT.west = [k, 0]; } });
});
beatTL('1.7', 'El timbre', 'Aparece flotando a la altura de la mano: redondo, del material del muro, con un aro de luz cálida.', null, () => {
  fx('FX_BELLAPPEAR');
  clip({ key: 'BELL_IN', track: 'obj', label: 'Aparece el timbre (luz primero)', vfx: 'VFX_BELLAPPEAR', dur: 1.5, at: 0, apply: k => { bell.visible = true; bell.position.copy(BELL_POS); bell.quaternion.copy(PS1.q); bell.scale.setScalar(.7); W.appear.bell = k; } });
});
beatTL('1.8', 'Cargar el timbre', 'Mantén el clic sobre el timbre: el aro radial carga en 3 s. Si sueltas, vuelve a 0.', null, () => {
  gate('G_BELL', 'Espera: cargar el timbre', 5, 25, {
    tick: (local, g) => { const on = S.down && hover(bell.userData.body);
      if (on && !g.charging) { g.charging = true; cue('fx', 'FX_CARGABELL'); cue('hap', 'HAP_CHARGE_RAMP', '0,15→0,6'); }
      if (!on) g.charging = false; g.p = clamp(g.p + (on ? 1 / 3 : -2) * frameDt); return g.p >= 1; },
    onFire: g => { g.p = 1; }, sounds: ['FX_CARGABELL', 'HAP_CHARGE_RAMP'],
    visual: (k, local, c, g) => { W.bellFill = g ? g.p : clamp((local - (c.e - c.s - 3)) / 3); W.bellPress = g ? (g.charging ? 1 : 0) : (k < 1 && local > c.e - c.s - 3 ? 1 : 0); },   // el timbre se hunde 1 cm mientras la mano lo aprieta (Hall 09-30)
  });
  ghostSpan('GHOST_BELL', 0xffe0bd, 0, ['G_BELL', 'end'], 'Rest your hand and hold');
  vo('VO_01d', 'Rest your hand on the bell… and hold it until the light fills the ring.', 0); // la demostración siempre va con su voz: qué hacer
  vo('VO_01h', 'Rest your hand on it.', ['G_BELL', 'start', 8], { help: 'G_BELL' });
  fx('FX_CARGABELL', ['G_BELL', 'end', -3], 'cuando empieza a cargar', { simOnly: true });
  hap('HAP_CHARGE_RAMP', ['G_BELL', 'end', -3], '0,15→0,6', { simOnly: true });
  hap('HAP_PULSE_STRONG', ['G_BELL', 'end']); fx('FX_BELLRING', ['G_BELL', 'end']);
});
beatTL('1.9', 'Se abren las puertas', 'El timbre se encoge a un punto de luz. Las medias lunas de vidrio corren sobre el muro.', null, () => {
  fx('FX_BELLVANISH', 0, 'salida del timbre');
  clip({ key: 'BELL_OUT', track: 'obj', label: 'El timbre se va (luz primero al revés)', dur: 1.5, at: 0, apply: k => { if (k < 1) W.appear.bell = 1 - k; W.bellFill = 1; if (k >= 1) bell.visible = false; } });
  fx('FX_DOOROPEN', ['BELL_OUT', 'end']);
  clip({ key: 'DOORS_W', track: 'world', label: 'Se abren las medias lunas', dur: 3, at: ['BELL_OUT', 'end'], apply: k => { setDoor('west', k); W.hallT.west = [1, k]; hallU.uLight.value = .9 + .1 * k; } });
});
beatTL('1.10', 'Entrar al Hall', 'Avance automático hasta un poco antes del centro, justo afuera del anillo de baldosas.', null, () => {
  walk('WALK2', 'Entra al Hall', PS1, PS2, 6.5, 0);
  clip({ key: 'GROOVE_WAVE', track: 'world', label: 'Las hendiduras del domo se encienden en onda al entrar (Hall 09-30)', dur: 6, at: 0, apply: k => { W.hallWave = ease(k); } });
  amb('AMB_03', 1.5); fx('FX_HALLROOM', 1.5);
  clip({ key: 'DOORS_W_CLOSE', track: 'world', label: 'La puerta se cierra detrás', dur: 1.5, at: ['WALK2', 'end'], apply: k => setDoor('west', 1 - k) });
});
beatTL('1.11', 'Aparece Alma', 'Nace desde un punto de luz bajo el óculo. Su firma sonora se repite cada vez que aparece.', ['1.10', 'start', 1.5], () => {
  fx('FX_ALMAAPPEAR');
  clip({ key: 'ALMA_IN', track: 'obj', label: 'Alma nace bajo el óculo', vfx: 'VFX_ALMAAPPEAR', dur: 1.2, at: 0, apply: k => almaAt(ALMA_HALL, ease(k)) });
  vo('VO_02', 'Hi… welcome to a soul charging experience. I\'m Alma, and I\'ll be with you the whole way. Here, your body speaks… and this place listens. Your breath, your heartbeat, the quiet of your mind: each of them will charge a part of you.', ['1.10/WALK2', 'end']);
});

/* ================= ACTO 2 · HALL ================= */
act('Acto 2 · Hall');
beatTL('2.1', 'Alma se corre', 'Hacia la izquierda del usuario.', null, () => {
  fx('FX_ALMAMOVE');
  clip({ key: 'ALMA_SIDE', track: 'obj', label: 'Alma se corre a la izquierda', dur: 3, at: 0, apply: k => almaAt(lv(ALMA_HALL, ALMA_SIDE, ease(k)), 1) });
});
beatTL('2.2', 'El sensor', 'Flota frente a ti, girando suave, con un aro de luz que invita a tomarlo. Clic sobre el sensor: queda en tu mano hábil para toda la obra.', null, () => {
  fx('FX_CONTROLLERAPEAR');
  clip({ key: 'SENSOR_IN', track: 'obj', label: 'Aparece el sensor', vfx: 'VFX_SENSORAPPEAR', dur: .8, at: 0, apply: k => { W.sensor = 'float'; W.sensorPos = SENSOR_POS; W.sensorScale = ease(k); } });
  clip({ key: 'ORB_IN', track: 'obj', label: 'El orbe blanco azulado envuelve al mando (r 14 cm)', at: 0, end: ['G_SENSOR', 'end'], during: (local) => { W.orb = { a: ease(clamp(local / .8)), s: 1 }; } });
  vo('VO_03', 'Before we begin, take this sensor with the hand that feels most natural to you. It will be your connection with this place.', 0);
  gate('G_SENSOR', 'Espera: tomar el sensor', 8, 15, { tick: () => consumeClick() && hover(sensor), onFire: () => cue('vfx', 'mano dominante', 'derecha (cortafuegos)') });
  ghostSpan('GHOST_TAKE', 0xcfe0ff, 0, ['G_SENSOR', 'end'], 'Take it with your favorite hand');
  vo('VO_03h', 'Just reach out and take it.', ['G_SENSOR', 'start', 8], { help: 'G_SENSOR' });
  clip({ key: 'SENSOR_HAND', track: 'obj', label: 'El sensor queda en tu mano', dur: 0, at: ['G_SENSOR', 'end'], apply: () => { W.sensor = 'hand'; W.sensorScale = 1; } });
  fx('FX_CONTROLLERATACHED', ['G_SENSOR', 'end']); hap('HAP_PULSE_STRONG', ['G_SENSOR', 'end']);
  fx('FX_PROTOSELECT', ['G_SENSOR', 'end'], 'el orbe estalla al tomar el mando');
  clip({ key: 'ORB_BURST', track: 'obj', label: 'El orbe estalla (0,45 s, x1,7)', dur: .45, at: ['G_SENSOR', 'end'], apply: k => { W.orb = k < 1 ? { a: 1 - k, s: 1 + .7 * (1 - Math.pow(1 - k, 3)) } : null; } });
});
beatTL('2.4', 'Las cinco almas', 'Aparecen en semicírculo, una cada 0,4 s, cada una con su color y su nota.', null, () => {
  fx('FX_PROTOAPPEAR');
  clip({ key: 'CANDS_IN', track: 'obj', label: 'Aparecen las cinco almas', vfx: 'VFX_PROTOAPPEAR', dur: 2.2, at: 0, apply: k => cands.forEach((c, i) => { c.visible = true; c.position.copy(CAND_POS[i]); c.scale.setScalar(Math.max(.01, ease(clamp((k * 2.2 - i * .4) / .6)))); }) });
  vo('VO_04', 'Now, choose the soul that best represents you today. Don\'t think too much… let one of them call you.', ['CANDS_IN', 'end']);
});
beatTL('2.5', 'Elegir', 'Pasa el mouse por las almas (crecen y suenan) y haz clic en una.', ['2.4/CANDS_IN', 'end'], () => {
  gate('G_CHOOSE', 'Espera: elegir tu alma', 7, 30, {
    tick: (local, g) => { const h = pick(cands); const idx = h ? cands.indexOf(h.object) : -1;
      if (idx !== g.hov) { g.hov = idx; if (idx >= 0) { S.hoverNote = idx; const real = !!audioFor('FX_PROTOHOVER'); cue('fx', 'FX_PROTOHOVER', '', real); if (real) startVoice('protohover', 'FX_PROTOHOVER', 0, { fin: .05 }); cue('hap', 'HAP_TICK'); } }
      if (consumeClick() && idx >= 0) { S.choice = idx; return true; } return false; },
    onFire: () => { S.choice = 2; stopVoice('protohover', .4); }, onUser: () => stopVoice('protohover', .4), sounds: ['FX_PROTOHOVER', 'HAP_TICK'],
    visual: (k, local, c, g) => { if (!g || g.resolved) return; g.sc = g.sc || [1, 1, 1, 1, 1]; cands.forEach((cd, i) => { g.sc[i] = lerp(g.sc[i], i === g.hov ? 1.45 : 1, .15); cd.scale.setScalar(g.sc[i]); }); },
  });
  ghostSpan('GHOST_PICK', 0xcfe0ff, 0, ['G_CHOOSE', 'end'], 'Point and pull the trigger');
  vo('VO_04b', 'Point at the one that calls you… and pull the trigger.', ['2.4/VO_04', 'end']);
  fx('FX_PROTOSELECT', ['G_CHOOSE', 'end'], 'VFX_PROTOSELECT'); hap('HAP_PULSE_STRONG', ['G_CHOOSE', 'end']);
});
beatTL('2.6', 'Tu alma', 'Las otras se desvanecen; la elegida viaja al frente y su anillo se cierra alrededor: el contenedor.', null, () => {
  clip({ key: 'SOUL_COLOR', track: 'obj', label: 'Tu alma toma su color', dur: 0, at: 0, apply: () => soul.material.uniforms.uCol.value.copy(cands[S.choice].material.uniforms.uCol.value) });
  fx('FX_PROTOFADE');
  clip({ key: 'OTHERS_OUT', track: 'obj', label: 'Las otras se desvanecen', dur: 1, at: 0, apply: k => cands.forEach((c, i) => { if (i === S.choice || k >= 1) c.visible = false; else c.scale.setScalar(Math.max(.01, 1 - k)); }) });
  // Hall 09-30: tu alma va al centro del Hall, bajo el oculo (TP_hall_soul_present 0,0,160, escala 0,3 = 50 cm a 3 m), en 4 s con smootherstep y SIN anillo (se cierra recien en el HUD)
  clip({ key: 'SOUL_FRONT', track: 'obj', label: 'Tu alma viaja al centro del Hall (50 cm, sin anillo)', dur: 4, at: 0, apply: k => { const e = k * k * k * (k * (k * 6 - 15) + 10); W.cont = 'world'; container.position.copy(CAND_POS[S.choice]).lerp(SOUL_PRESENT, e); container.scale.setScalar(lerp(1, SOUL_PRESENT_S, e)); container.quaternion.copy(PS2.q); } });
  clip({ key: 'RING_HIDDEN', track: 'obj', label: 'En el Hall no hay anillo', at: 0, end: ['2.8/TO_HUD', 'start'], during: () => { W.ringK = 0; } });
  vo('VO_05', 'This is your soul. It will grow with everything you give it.', ['SOUL_FRONT', 'end']);
});
beatTL('2.7', 'Las cinco etapas: las baldosas del Hall', 'Alma presenta el viaje. Después, cada etapa es su propio paso (2.7a-e): su baldosa sube y brilla, aparece su nombre y se enciende su luz en tu anillo. La calibración mide en silencio.', null, () => {
  clip({ key: 'BIOHUB', track: 'int', label: 'BioHub: línea base EEG + BPM', dur: 0, at: 0, vfx: 'BioHub: línea base EEG + BPM · mientras escucha quieto' });
  vo('VO_06a', 'Your journey has five stages.', 0);
});
/* un paso por etapa: la barra PASO manda el ritmo (arrastrar su borde = cuánto dura esa etapa y cuándo entra la siguiente),
   sin importar lo que dure la voz; la baldosa, el nombre, la luz del anillo y la voz arrancan juntos al inicio del paso */
const STAGE_LINES = ['Entering… you will breathe with this place.', 'Recognizing… you will listen to your heart.', 'Loving… you will let your mind rest.', 'Attracting… you will gather sounds into a melody of your own.', 'Surrounding… you will draw what you carry inside.'];
let prevStep = ['2.7/VO_06a', 'end'];
STAGES.forEach((st, i) => {
  const uid = '2.7' + 'abcde'[i], id = 'VO_06' + 'bcdef'[i];
  beatTL(uid, 'Etapa ' + (i + 1) + ': ' + st.name, `La baldosa de ${st.name} (biselada) sube un par de centímetros y se ENCIENDE con su color, como las teclas de la paleta; su nombre aparece encima y se enciende su luz en tu anillo. Estira la barra PASO para cambiar cuánto dura.`, prevStep, () => {
    clip({ key: 'PASO', track: 'int', label: 'Paso ' + st.name + ' · estira para cambiar el ritmo', dur: 4.5, at: 0 });
    vo(id, STAGE_LINES[i], 0);
    fx('FX_TILERISE_' + (i + 1), 0, 'VFX_TILERISE_' + (i + 1), { onStart: () => tone(NOTE[i], 2.2, 'sine', .06, .3) });
    clip({ key: 'TILE', track: 'world', label: 'Baldosa ' + st.name + ' sube y se enciende con su color', dur: 1.5, at: 0, apply: k => { setTile(i, ease(k), ease(k)); } });
    clip({ key: 'LABEL', track: 'world', label: 'Nombre ' + st.key, dur: 3, at: 0, apply: k => tiles[i].label.material.uniforms.uR.value = ease(k) });
    clip({ key: 'LUZ', track: 'obj', label: 'Se enciende la luz ' + (i + 1) + ' del anillo', dur: 1.5, at: 0, apply: k => setCavity(i, ease(k)) });
  });
  prevStep = [uid + '/PASO', 'end'];
});
beatTL('2.7f', 'Cada etapa carga una luz', 'Alma cierra la presentación; las baldosas bajan y el anillo queda tenue, esperando las cargas.', prevStep, () => {
  vo('VO_06g', 'Each stage will charge one light of your soul.', 0);
  fx('FX_TILESDOWN', ['VO_06g', 'end'], 'VFX_TILESDOWN + VFX_RINGDIM');
  clip({ key: 'TILES_DOWN', track: 'world', label: 'Las baldosas bajan · el anillo queda tenue', dur: 2, at: ['VO_06g', 'end'], apply: k => { tiles.forEach((t, i) => { setTile(i, 1 - k, lerp(1, .25, k)); t.label.material.uniforms.uR.value = 1; t.label.material.uniforms.uO.value = k; }); cavities.forEach((c, i) => setCavity(i, lerp(1, .12, k))); } });
});
beatTL('2.8', 'Nace el HUD', 'Ondas de luz suben alrededor (fin de la calibración). Nace el HUD y el anillo con tu alma se ancla ahí.', null, () => {
  fx('FX_CALIBRATION', 0, 'VFX_CALIBRATION');
  clip({ key: 'CALIB', track: 'world', label: 'Ondas de calibración', dur: 2.5, at: 0, apply: k => calib.forEach((c, i) => { const kk = clamp(k * 1.4 - i * .2); c.position.set(PS2.x, .1 + kk * 2.2, PS2.z); c.material.opacity = k < 1 ? Math.sin(kk * Math.PI) * .6 : 0; }) });
  fx('FX_HUDBIRTH', ['CALIB', 'end'], 'VFX_HUDBIRTH');
  clip({ key: 'HUD_IN', track: 'obj', label: 'Nace el HUD (luz primero)', dur: 1.5, at: ['CALIB', 'end'], apply: k => { W.hud = HUD3.root ? 1 : Math.max(.01, ease(k)); W.appear.hud = k; } });
  // como en Unreal: el alma del Hall se desvanece en el centro y nace en el HUD con su anillo
  fx('FX_SOULTOFACE', ['HUD_IN', 'end'], 'VFX_SOULTOFACE');
  clip({ key: 'TO_HUD', track: 'obj', label: 'Tu alma del Hall se desvanece y nace en el HUD con su anillo', dur: 1.5, at: ['HUD_IN', 'end'], apply: k => {
    if (k < .45) { W.cont = 'world'; container.position.copy(SOUL_PRESENT); container.scale.setScalar(Math.max(.001, SOUL_PRESENT_S * (1 - ease(k / .45)))); W.ringK = 0; return; }
    W.cont = 'hud'; container.scale.setScalar(HUD_RING_S); W.ringK = ease((k - .45) / .55); W.ringIn = true; } });
  // al anclarse tu alma en el HUD por primera vez, una HERMANA suya se ancla en el asiento del pulso (izquierda)
  clip({ key: 'SISTER_IN', track: 'obj', label: 'Una hermana de tu alma se ancla en el pulso', dur: .7, at: ['TO_HUD', 'end'], apply: k => { W.sister = k; } });
  fx('FX_SISTERAPPEAR', ['SISTER_IN', 'start'], 'nace la hermana'); hap('HAP_PULSE_SOFT', ['SISTER_IN', 'start']);
  hap('HAP_PULSE_SOFT', ['TO_HUD', 'end']);
  vo('VO_07', 'There you are. Everything is ready. Follow me.', ['TO_HUD', 'end']);
});
beatTL('2.9', 'La puerta de salida', 'Alma se va hacia la puerta Este; su vidrio y lo que se ve por ella pasan suave a blanco azulado (el color de Breath). Se abre y sales a ese color. El Hall se apaga detrás.', null, () => {
  fx('FX_ALMAOUT');
  clip({ key: 'ALMA_OUT', track: 'obj', label: 'Alma se va', dur: .6, at: 0, apply: k => almaAt(ALMA_SIDE, 1 - k) });
  fx('FX_DOORREVEAL', ['ALMA_OUT', 'end'], 'VFX_DOORREVEAL');
  clip({ key: 'DOOR_E_COOL', track: 'world', label: 'El vidrio de salida pasa suave a blanco azulado (el color de Breath)', dur: 3, at: ['ALMA_OUT', 'start'], apply: k => doors.east.mat.uniforms.uCool.value = ease(k) });
  clip({ key: 'OUTSIDE_BLUE', track: 'world', label: 'Afuera, por la puerta, todo pasa a blanco azulado (el velo de Entering)', dur: 3.5, at: ['DOOR_E_COOL', 'start', .5], apply: k => { const vs = voidSky.material.uniforms, c = outsideColor(); vs.uTop.value.copy(c); vs.uHor.value.copy(c); vs.uAmt.value = ease(k); } });
  fx('FX_DOOROPEN', ['DOOR_E_COOL', 'end']);
  clip({ key: 'DOOR_E_OPEN', track: 'world', label: 'Se abre la puerta Este', dur: 2.5, at: ['DOOR_E_COOL', 'start', 1.5], apply: k => setDoor('east', k) });
  amb('SILENCIO', ['DOOR_E_OPEN', 'end'], 'AMB_03 sale');
  walk('WALK3', 'Al umbral', PS2, PSD, 3, ['DOOR_E_OPEN', 'end', -.8]);
  clip({ key: 'HALL_OFF', track: 'world', label: 'El Hall se apaga detrás', dur: 1.2, at: ['WALK3', 'end'], apply: k => hallU.uLight.value = 1 - k });
  walk('WALK4', 'Al Centro', PSD, PSC, 3, ['HALL_OFF', 'start']);
  clip({ key: 'HALL_HIDE', track: 'world', label: 'El Hall se descarga', dur: 0, at: ['WALK4', 'end'], apply: () => { hallG.visible = false; setDoor('east', 0); doors.east.mat.uniforms.uCool.value = 0; } });
});

/* ================= ACTO 3 · LLEGADA ================= */
act('Acto 3 · Llegada');
const T_STAGE = STAGES.map((st, i) => { const m = titleAt(st.key, st.grad, PSC, 5, .5, .42); m.position.copy(ensAdd(m.position, i, 'title')); return m; });
beatTL('3.1', 'Se enciende el primer mundo', 'Afuera ya es blanco azulado: el velo de Entering (del mismo tono) lo cubre, el valle se enciende oculto y el velo abre (4,5 s), como en las otras transiciones.', null, () => {
  amb('AMB_04'); fx('FX_STAGEREVEAL');
  clip({ key: 'VEIL1_IN', track: 'world', label: 'El velo de Entering cubre el afuera (mismo tono)', dur: .6, at: 0, apply: k => { setVeilColors(STAGES[0], STAGES[0], 0); W.veil = ease(k); if (k >= 1) { W.env = [0, 1]; const vs = voidSky.material.uniforms; vs.uAmt.value = 0; vs.uTop.value.set(lookVal('intro', 'fogTop')); vs.uHor.value.set(lookVal('intro', 'fogHor')); } } });
  clip({ key: 'ENV1_IN', track: 'world', label: 'El velo abre: aparece el valle', dur: 4.5, at: ['VEIL1_IN', 'end', .6], apply: k => { setVeilColors(STAGES[0], STAGES[0], 0); W.veil = 1 - ease(k); W.env = [0, 1]; } });
  clip({ key: 'T1_IN', track: 'world', label: 'Título ENTERING', dur: 4.5, at: 0, apply: k => revealTitle(T_STAGE[0], k) });
  clip({ key: 'T1_OUT', track: 'world', label: 'Se va el título', dur: 3, at: ['ENV1_IN', 'end'], apply: k => outTitle(T_STAGE[0], k) });
});

/* ================= LAS CINCO ETAPAS: la plantilla del ritual ================= */
const VO_ST = [
  { a: ['VO_10', 'This is Entering. Imagine your breath like gentle waves… moving naturally within you.'], charge: ['VO_13', 'Your breath has opened the first light.'], bye: ['VO_14', 'Now… let\'s listen a little deeper.'] },
  { a: ['VO_15', 'This is Recognizing. Let\'s redirect the focus to the heart… melting the thoughts of the mind.'], charge: ['VO_18', 'Your heartbeat has lit the second light.'], bye: ['VO_19', 'Now, let your thoughts become quiet.'] },
  { a: ['VO_20', 'This is Loving. There is nothing to do here… just let go.'], charge: ['VO_24', 'Your calm has lit the third light.'], bye: ['VO_25', 'Now… let\'s activate your body a little bit.'] },
  { a: ['VO_26', 'This is Attracting. Every sound around you is waiting for you.'], charge: ['VO_29', 'Your melody has lit the fourth light.'], bye: ['VO_30', 'One last stage. Now… you create.'] },
  { a: ['VO_31', 'This is Surrounding, the final stage of your journey. Use this space as a canvas… to create your own world.'] },
];
function veilBeat(n) {
  const a = STAGES[n - 1], b = STAGES[n];
  beatTL(`V${n}`, `Velo ${n}→${n + 1}`, 'Una niebla de color que envuelve todo (esfera de 50 m) cierra, cambia la etapa oculta y abre. Sin dither de ruido.', null, () => {
    fx('FX_VEIL', 0, 'velo'); amb(['', 'AMB_05', 'AMB_06', 'PAD_M1', 'AMB_07'][n], 0, n === 3 ? 'sin ambiente: el pad del secuenciador de fondo' : '');
    clip({ key: 'VEIL_CLOSE', track: 'world', label: 'El velo cierra', dur: 4, at: 0, apply: k => { setVeilColors(a, b, k); W.veil = ease(k); W.env = [n - 1, 1]; } });
    clip({ key: 'ENV_SWAP', track: 'world', label: 'La etapa se enciende oculta', vfx: 'la etapa se enciende oculta, por capas', dur: 0, at: ['VEIL_CLOSE', 'end'], apply: () => W.env = [n, 1] });
    fx('FX_TITLE', ['VEIL_CLOSE', 'end']);
    clip({ key: 'T_IN', track: 'world', label: 'Título ' + b.key, dur: 3.5, at: ['VEIL_CLOSE', 'end'], apply: k => revealTitle(T_STAGE[n], k) });
    fx('FX_STAGEREVEAL', ['VEIL_CLOSE', 'end', 1.5]);
    clip({ key: 'VEIL_OPEN', track: 'world', label: 'El velo abre', dur: 4.5, at: ['VEIL_CLOSE', 'end', 1.5], apply: k => W.veil = 1 - ease(k) });
    clip({ key: 'T_OUT', track: 'world', label: 'Se va el título', dur: 3, at: ['VEIL_OPEN', 'end'], apply: k => outTitle(T_STAGE[n], k) });
  });
}
function almaBeat(n, at) {
  const [id, text] = VO_ST[n].a;
  beatTL(`${n + 1}.R2`, `R2 · ${STAGES[n].name}: Alma`, 'Alma aparece al frente, un poco a la izquierda.', at, () => {
    fx('FX_ALMAAPPEAR');
    clip({ key: 'ALMA_IN', track: 'obj', label: 'Aparece Alma', dur: 1.2, at: 0, apply: k => almaAt(almaSt(n), ease(k)) });
    vo(id, text, ['ALMA_IN', 'end']);
    fx('FX_ALMAMOVE', [id, 'end', ensPause(n)]);
    clip({ key: 'ALMA_MOVE', track: 'obj', label: 'Alma se corre a un lado', dur: 3, at: [id, 'end', ensPause(n)], apply: k => almaAt(lv(almaSt(n), almaSt2(n), ease(k)), 1) });
  });
  return `${n + 1}.R2/${id}`;
}
function closingBeats(n) {
  beatTL(`${n + 1}.R5x`, 'R5 Retirada', 'La herramienta y los objetos de la mecánica se van; el entorno se queda.', null, () => {
    fx('FX_TOOLOUT'); hap('HAP_PULSE_SOFT'); fx('FX_ALMAOUT');
    clip({ key: 'ALMA_GONE', track: 'obj', label: 'Alma se va con la salida de la etapa', dur: .6, at: 0, apply: k => almaAt(almaSt2(n), 1 - k) });
    clip({ key: 'PAUSA', track: 'int', label: 'Pausa', dur: 2, at: 0 });
  });
  chargeBeat(n);
  const [bid, btext] = VO_ST[n].bye;
  const [cid, ctext] = VO_ST[n].charge;
  beatTL(`${n + 1}.R8`, 'R8 Despedida', 'Alma vuelve al frente: celebra la luz encendida, invita a la siguiente etapa y se va (como FlowBye en la Obra).', null, () => {
    fx('FX_ALMAAPPEAR');
    clip({ key: 'ALMA_BACK', track: 'obj', label: 'Alma vuelve al frente', dur: 1.2, at: 0, apply: k => almaAt(almaSt(n), ease(k)) });
    vo(cid, ctext, .9);
    vo(bid, btext, [cid, 'end', .5]);
    fx('FX_ALMAOUT', [bid, 'end', .4]);
    clip({ key: 'ALMA_OUT', track: 'obj', label: 'Alma se va', dur: .6, at: [bid, 'end', .4], apply: k => almaAt(almaSt(n), 1 - k) });
  });
}
function chargeBeat(n, final) {
  beatTL(`${n + 1}.R6`, final ? '9.1 La última carga' : 'R6 La carga', final ? 'La carga más fuerte de la obra (6 s): cinco explosiones, una por etapa; cada una deja un anillo de su color alrededor del alma. El anillo gira, vibra, háptico en los dos mandos. Las cinco luces juntas y el HUD se disuelve.' : `El anillo, con tu alma adentro, se desprende del HUD y va al frente. Se enciende su luz ${n + 1} de verdad (${CHARGE_T[n]} s).`, null, () => {
    if (final) clip({ key: 'ALMA_HIDE', track: 'obj', label: 'Alma ya no está', dur: 0, at: 0, apply: () => almaAt(almaSt2(n), 0) });
    // el alma se teletransporta del HUD al frente (antes volaba 1,5 s)
    teleport('DETACH', 0, () => hudWorldPos(), () => contC(n), HUD_RING_S, 1.6 * ensDelta(n, 'charge').sc, () => hudWorldQuat(), () => PSC.q, false, { warnFx: 'FX_SOULDETACH' });
    // sin la luz que viajaba al anillo (Beltrán: "quitemos esa pelota, que cargue su parte nomás"): la carga empieza al llegar
    fx('FX_CHARGE_' + (n + 1), ['DETACH', 'end'], CHARGE_T[n] + ' s', { onStart: () => { if (!audioFor('FX_CHARGE_' + (n + 1))) tone(NOTE[n], CHARGE_T[n], 'sine', .05 + n * .015, CHARGE_T[n] * .6); } }); hap('HAP_CHARGE_RAMP', ['DETACH', 'end']);
    clip({ key: 'CHARGE', track: 'obj', label: `Se enciende la luz ${n + 1} (${STAGES[n].name})`, vfx: 'VFX_CHARGE_' + (n + 1), dur: CHARGE_T[n], at: ['DETACH', 'end'], apply: k => { setCavity(n, ease(k)); soul.material.uniforms.uGlow.value = k < 1 ? Math.sin(k * Math.PI) * .6 : 0; if (k < 1) W.halo = { n, k }; } });   // + el halo vibrante del color de la etapa, detrás
    hap('HAP_PULSE_STRONG', ['CHARGE', 'end'], final ? 'dos manos' : '');
    if (final) {
      fx('FX_CHARGEFINAL', ['CHARGE', 'end'], 'VFX_CHARGEFINAL');
      clip({ key: 'FINAL', track: 'obj', label: 'Las cinco luces juntas · el HUD se disuelve', dur: 3, at: ['CHARGE', 'end'], apply: k => { cavities.forEach((c, i) => setCavity(i, 1)); soul.material.uniforms.uGlow.value = k * .8; W.spinFast = k < 1; W.hud = k < 1 ? (HUD3.root ? 1 : Math.max(.01, 1 - k)) : 0; if (k < 1) W.appear.hud = 1 - k; } });
      clip({ key: 'FINAL_BURST', track: 'obj', label: 'Cinco explosiones, una por etapa: cada una deja su anillo de color', dur: CHARGE_T[n], at: ['CHARGE', 'start'], apply: (k, local) => {
        const F = [.1, .28, .46, .64, .82]; let j = -1; F.forEach((f, i) => { if (k >= f) j = i; });
        W.sr = F.map((f, i) => clamp((k - f) * CHARGE_T[n] / .6));   // cada anillo aparece en 0,6 s y queda
        if (j >= 0 && k < 1) { const kk = (k - F[j]) * CHARGE_T[n]; if (kk < 1) { W.pop = { p: container.position.clone(), k: kk, s: .5 + j * .07, kind: 'in', col: STAGES[j].color }; W.sr[j] *= 1 + .8 * Math.sin(Math.PI * kk); } }
        if (k < 1) W.spinFast = true; } });
      fx('FX_CHARGEFINAL_BURST', ['FINAL_BURST', 'start', CHARGE_T[n] * .1], 'cinco golpes, uno por etapa (tono 0,8 → 1,25)');
      hap('HAP_PULSE_STRONG', ['FINAL_BURST', 'start', CHARGE_T[n] * .1], 'cinco golpes que se apagan, dos manos');
      fx('FX_HUDVANISH', ['FINAL', 'start'], 'el HUD se disuelve');
      clip({ key: 'ENV_DARK', track: 'world', label: 'El océano funde a negro mientras carga', dur: CHARGE_T[n] + 3, at: ['CHARGE', 'start'], apply: k => W.env = k < 1 ? [4, 1 - ease(k)] : [-1, 0] });
      vo('VO_33', 'Your soul is fully charged.', ['FINAL', 'end']);
    } else {
      // y de vuelta al nido del HUD, también con el pum, después de CHARGE_HOLD s de quietud con la luz encendida
      teleport('BACK', ['CHARGE', 'end', CHARGE_HOLD], () => contC(n), () => hudWorldPos(), 1.6 * ensDelta(n, 'charge').sc, HUD_RING_S, () => PSC.q, () => hudWorldQuat(), true, { warnFx: 'FX_SOULWARN_BACK' });
    }
  });
}

/* ---------- E1 · ENTERING: respiración (mantener el clic = inhalar) ---------- */
act('Etapa 1 · Entering');
let stAt = almaBeat(0, ['3.1/ENV1_IN', 'end']);
beatTL('1.R3', 'R3 Capas', 'El metaball se condensa desde la bruma; el pacer aparece quieto.', [stAt, 'end'], () => {
  fx('FX_BLOBFORM');
  clip({ key: 'BLOB_IN', track: 'obj', label: 'El metaball crece morfeándose: las gotas nacen, crecen y se funden', dur: 4, at: 0, apply: k => W.blob = ease(k) });
  clip({ key: 'PACER_DIM', track: 'obj', label: 'El pacer aparece quieto', dur: 0, at: ['BLOB_IN', 'end'], apply: () => W.pacer = .25 });
});
beatTL('1.R4', 'R4 Herramienta y demostración', 'El sensor cilíndrico se arma en tu mano. El fantasma baja al estómago y respira. En el prototipo: MANTÉN el clic para inhalar, suelta para exhalar.', null, () => {
  fx('FX_TOOLAPPEAR_BREATH'); hap('HAP_PULSE_SOFT');
  clip({ key: 'BIO', track: 'obj', label: 'El mando se transforma en el sensor (azulado) y sigue en la mano hasta Recognizing', at: 0, end: ['2.R4', 'start'], during: () => W.sensorKind = 'bio' });
  clip({ key: 'BIO_ON', track: 'obj', label: 'Sensor apoyado: se encienden los aros', at: ['G_BREATH', 'end'], end: ['1.R5x', 'start'], during: () => W.bioOn = true });
  clip({ key: 'SENSOR_IN3', track: 'obj', label: 'Aparece el sensor (luz primero)', dur: 1.5, at: ['BIO', 'start'], apply: k => { W.appear.sensor = k; } });
  vo('VO_11', 'Rest the sensor on your belly. Feel how it rises and falls with you.', 0);
  gate('G_BREATH', 'Espera: sensor al estómago', 6, 25, { tick: () => S.down });
  ghostSpan('GHOST_BREATH', 0xcfe0ff, 0, ['G_BREATH', 'end'], 'Rest the sensor on your belly   ·   (aquí: mantén el clic para inhalar)');
  vo('VO_11h', 'Just below your ribs… flat side toward you.', ['G_BREATH', 'start', 12], { help: 'G_BREATH' });
  hap('HAP_PULSE_SOFT', ['G_BREATH', 'end'], 'entra al umbral'); hap('HAP_BREATH_HUM', ['G_BREATH', 'end'], '0,25 mientras respira');
});
beatTL('1.R5a', 'R5 Exploración libre (~12 s)', 'El pacer todavía no arranca: respira como quieras y mira cómo todo responde.', null, () => {
  vo('VO_11b', 'Take a moment to explore… breathe as you like, and notice how everything moves with you.', 0);
  clip({ key: 'LIBRE', track: 'int', label: 'Respiración libre · ExploreTime 12 s (Breath 09-30)', dur: 12, at: ['VO_11b', 'end'] });
});
beatTL('1.R5b', 'R5 El pacer (5 ciclos de 4-3-4-3)', 'El pacer aparece con la cuenta 3, 2, 1 y arranca 3 s después (LeadIn). Los aros guían: se juntan al inhalar, halo en la retención.', null, () => {
  vo('VO_12', 'Now, let\'s do a simple breathing exercise. Follow me with your breath.', 0);
  vo('VO_12c', 'Three… two… one…', ['VO_12', 'end']);
  clip({ key: 'PACER', track: 'int', label: 'Pacer · 5 ciclos 4-3-4-3 (Cycles 5)', dur: 70, at: ['VO_12c', 'start', 3],
    apply: k => { W.pacerProg = k; if (k >= 1) W.pacer = 0; },   // + el avance en el aro chico (Breath 09-30)
    during: local => { const c = local % 14; W.pacerOn = true; W.pacerK = c < 4 ? c / 4 : c < 7 ? 1 : c < 11 ? 1 - (c - 7) / 4 : 0; },
    fire: [0, 1, 2, 3, 4].flatMap(c => { const q = () => !!audioFor('FX_BREATHCOUNT'); return [[c * 14, () => cue('fx', 'FX_PACER_INHALE', '', q())], [c * 14 + 4, () => cue('fx', 'FX_PACER_HOLD', '', q())], [c * 14 + 7, () => cue('fx', 'FX_PACER_EXHALE', '', q())], [c * 14 + 11, () => cue('fx', 'FX_PACER_HOLD', '', q())]]; }) });
  [0, 1, 2, 3, 4].forEach(c => fx('FX_BREATHCOUNT', ['PACER', 'start', c * 14], 'ciclo ' + (c + 1) + ' del pacer'));
  vo('VO_12b', 'Inhale to hallucinate life… exhale to create destiny.', ['PACER', 'end']);
  clip({ key: 'BLOB_OUT', track: 'obj', label: 'El metaball se disuelve', dur: 2, at: ['VO_12b', 'end'], apply: k => W.blob = 1 - k });
});
closingBeats(0);

/* ---------- E2 · RECOGNIZING: latido ---------- */
act('Etapa 2 · Recognizing');
veilBeat(1);
stAt = almaBeat(1, ['V1/VEIL_OPEN', 'end']);
beatTL('2.R4', 'R4 Herramienta y demostración', 'El fantasma lleva el mando al pecho y queda quieto. En el prototipo: deja el mouse quieto en la zona del pecho (abajo a la izquierda) o mantén el clic.', [stAt, 'end'], () => {
  vo('VO_16', 'Place the sensor on your chest… and stay still for a moment.', 0);
  clip({ key: 'BIO', track: 'obj', label: 'El sensor bio en la mano (reemplaza al mando)', at: 0, end: ['2.R5x', 'start'], during: () => W.sensorKind = 'bio' });
  clip({ key: 'BIO_ON', track: 'obj', label: 'Sensor apoyado: se encienden los aros', at: ['G_HEART', 'end'], end: ['2.R5x', 'start'], during: () => W.bioOn = true });
  clip({ key: 'SENSOR_TINT', track: 'obj', label: 'El mismo sensor se vuelve rojizo', dur: 1.2, at: 0, apply: k => { W.bioTint = k; } });
  clip({ key: 'SPHERE_IN', track: 'world', label: 'La esfera brota del mar (recién en las instrucciones)', dur: 2.5, at: 0, apply: k => { W.heartSphere = out3(k); } });
  fx('FX_SPHERERISE', 0, 'la esfera brota');
  clip({ key: 'SENSOR_OUT3', track: 'obj', label: 'Se va el sensor (al revés)', dur: 1.5, at: ['BIO', 'end', -1.5], apply: k => { if (k < 1) W.appear.sensor = 1 - k; } });
  fx('FX_SENSORVANISH', ['SENSOR_OUT3', 'start'], 'salida del sensor');
  gate('G_HEART', 'Espera: sensor al pecho', 6, 25, { tick: () => S.down || (S.mouse.x < -.2 && S.mouse.y < -.25 && S.stillness > .9) });
  ghostSpan('GHOST_HEART', 0xffc6cf, 0, ['G_HEART', 'end'], 'Hold the sensor on your heart   ·   (aquí: mantén el clic)');
  vo('VO_16h', 'A little higher… and very still.', ['G_HEART', 'start', 14], { help: 'G_HEART' });
});
/* el latido es determinista (68 BPM simulados): se ve igual al recorrer la línea de tiempo */
const HEART_ORB_POS = Array.from({ length: 64 }, (_, j) => { const a = ((j * 2.399) % 1) * TAU, r = 3 + ((j * .618) % 1) * 6; return V(4 + Math.cos(a) * r, -1, Math.sin(a) * r); });
function heartAt(local, prev) {
  const P = 60 / S.data.bpm, n = Math.floor(local / P);
  if (prev != null && Math.floor(prev / P) < n) { cue('hap', 'HAP_HEARTBEAT'); S.data.beats++; cue('fx', 'FX_HEARTBEAT', 'con cada latido'); if (!audioFor('FX_HEARTBEAT')) FXSYN.FX_MEMBRANE(); }   // un pulso con CADA latido (Heart, 09-30: BeatDivider 1)
  const lastEven = n * P; envU[1].uBeat.value = S.clock - (local - lastEven);
  const h = envs[1].userData.heart, age = local - lastEven; h.position.y = -.2 - .12 * Math.exp(-age * 3) * Math.sin(Math.min(age * 6, Math.PI));
  const orbs = envs[1].userData.orbs, m = Math.floor(local / P);
  orbs.forEach(o => o.visible = false);
  for (let j = Math.max(0, m - 13); j <= m; j++) { const o = orbs[j % orbs.length], a = local - j * P; if (a < 0 || a > 20) continue;
    o.visible = true; o.position.copy(HEART_ORB_POS[j % 64]); o.position.y = -1 + a * .12; o.material.uniforms.uA.value = .6 * clamp(1 - a / 20); }
  W.heartOn = true;
}
beatTL('2.R5', 'R5 Mecánica viva', 'Latidos reales (Muse → BioHub). Un pulso visual con cada latido y su sonido: un solo "pum", un solo empuje.', null, () => {
  vo('VO_17a', 'Can you hear your heartbeat?… Can you feel its rhythm?', 0);
  clip({ key: 'HEART', track: 'int', label: 'Latido vivo · 68 BPM (simulado) · termina a los 38 latidos (StageBeats, la mitad desde 09-30: ~0:34 a 68 bpm, ~0:45 a 50)', sounds: ['FX_HEARTBEAT', 'HAP_HEARTBEAT'], dur: 34, at: ['VO_17a', 'end'], during: (local, c, prev) => heartAt(local, prev), apply: k => { if (k >= 1) envs[1].userData.orbs.forEach(o => o.visible = false); } });
  vo('VO_17b', 'Now… you can see it.', ['HEART', 'start']);
  clip({ key: 'SPHERE_OUT', track: 'world', label: 'La esfera se hunde en el mar', dur: 2.5, at: ['HEART', 'end'], apply: k => { W.heartSphere = 1 - out3(k); } });
  vo('VO_17c', 'Does gratitude flow through your heartbeat?', ['HEART', 'start', 12]);
});
closingBeats(1);

/* ---------- E3 · LOVING: sin herramienta; quieto = calma ---------- */
act('Etapa 3 · Loving');
veilBeat(2);
stAt = almaBeat(2, ['V2/VEIL_OPEN', 'end']);
beatTL('3.R3', 'Sin R4: la calma', 'Sin sensor: solo tus manos, que mueven las partículas. La calma del EEG (aquí: tener el mouse quieto) frena el remolino y conecta la célula, centrada frente a ti.', [stAt, 'end'], () => {
  clip({ key: 'SOLO_MANOS', track: 'obj', label: 'Solo las manos (sin mando)', at: 0, end: ['3.R5', 'end'], during: () => { W.sensor = 'off'; } });
  fx('FX_TOOLSLEEP', 0, 'VFX_TOOLSLEEP'); fx('FX_CELLFORM');
  clip({ key: 'CELL_IN', track: 'obj', label: 'Se forma la célula', dur: 4, at: 0, apply: k => W.cell = ease(k) });
  const qs = [['VO_21', 'What you see around you… is your own mind, right now.'], ['VO_22', 'Observe your thoughts like distant constellations… each one quietly forming, then fading.'], ['VO_23', 'Which thought carries a quiet wisdom today?']];
  let prev = ['CELL_IN', 'end'];
  qs.forEach(([id, text], i) => {
    clip({ key: 'SHAPE_' + (i + 1), track: 'obj', label: 'Forma ' + (i + 1) + ' de la célula', dur: 0, at: prev, apply: () => W.cellShape = i });
    fx('FX_MIND_' + (i + 1), prev);
    vo(id, text, prev);
    clip({ key: 'SIL_' + (i + 1), track: 'int', label: 'Silencio · 12 s', dur: 12, at: [id, 'end'] });
    prev = ['SIL_' + (i + 1), 'end'];
  });
  clip({ key: 'CALM', track: 'int', label: 'Calma viva (EEG)', at: ['CELL_IN', 'end'], end: ['SIL_3', 'end'], during: () => W.lovingOn = true });
  // el viaje (Mind 09-30): las partículas del medio fluyen hacia ti a 25 cm/s desde Begin (entrada 4 s) y frenan en 2 s con la salida; tú y la neurona quietos
  clip({ key: 'TRAVEL', track: 'world', label: 'Viaje: el medio fluye hacia ti (25 cm/s)', at: 0, end: ['V3/VEIL_CLOSE', 'end'], during: (local, c) => { const r5 = BYUID.get('3.R5'); W.travel = travelDist(local, r5 && r5.e != null ? r5.e - c.s : 1e9); } });
});
beatTL('3.R5', 'La espiral', 'Del guion antiguo: todo el fluido gira en espiral de los pies a la coronilla y se disuelve hacia arriba. Entra a la carga.', null, () => {
  fx('FX_MINDSPIRAL', 0, 'VFX_MINDSPIRAL');
  vo('VO_23b', 'Let\'s gather all these thoughts… and use this inner motion to charge your soul.', 0);
  clip({ key: 'SPIRAL', track: 'obj', label: 'Espiral de los pies a la coronilla', dur: 6, at: 0, apply: k => { W.spiral = k < 1 ? k : 0; }, during: () => W.lovingOn = true });
  fx('FX_TOOLWAKE', ['SPIRAL', 'end']); hap('HAP_PULSE_SOFT', ['SPIRAL', 'end']);
});
closingBeats(2);

/* ---------- E4 · ATTRACTING: gusano, esferas, beam, SAVE ---------- */
act('Etapa 4 · Attracting');
veilBeat(3);
stAt = almaBeat(3, ['V3/VEIL_OPEN', 'end']);
beatTL('4.R3', 'R3 Capas', 'Idea de Beltrán: primero Alma, después el gusano, después las esferas.', [stAt, 'end'], () => {
  fx('FX_WORMRISE');
  clip({ key: 'WORM_IN', track: 'obj', label: 'Sube el gusano', dur: 3, at: 0, apply: k => W.worm = ease(k) });
  fx('FX_ORBSWAVE', ['WORM_IN', 'end'], 'siembra escalonada de 68 esferas');
  clip({ key: 'ORBS_IN', track: 'obj', label: 'Siembra de 68 esferas', dur: .6, at: ['WORM_IN', 'end'], apply: k => W.orbs = Math.ceil(k * 68) });
});
beatTL('4.R4', 'R4 Herramienta y demostración', 'El beam aparece por primera vez en la obra. El fantasma apunta, aprieta, trae una esfera y la encaja.', null, () => {
  fx('FX_BEAMON'); hap('HAP_PULSE_STRONG');
  clip({ key: 'BEAM', track: 'obj', label: 'Beam encendido', dur: 0, at: 0, apply: () => W.beam = true, reset: resetOrbs });
  vo('VO_27', 'Reach into the space… every motion forms new connections, sounds, rhythms.', 0);
  vo('VO_27d', 'Point at a sphere and pull the trigger to bring it to you… then place it on the worm.', ['VO_27', 'end']);
  gate('G_GRAB', 'Espera: primera esfera', 6, 25, { tick: () => !!S.carry, sounds: ['FX_ORBGRAB', 'FX_ORB_*', 'FX_SLOTSNAP', 'FX_ORBHOME', 'HAP_TICK', 'HAP_PULSE_SOFT', 'HAP_SNAP'] });
  clip({ key: 'ATTRACT', track: 'int', label: 'Esferas habilitadas', dur: 0, at: ['G_GRAB', 'start'], apply: () => W.attract = true });
  ghostSpan('GHOST_ATTRACT', 0xffe2c2, 0, ['G_GRAB', 'end'], 'Point · pull the trigger · place it');
  vo('VO_27h', 'Point at a sphere and pull the trigger.', ['G_GRAB', 'start', 14], { help: 'G_GRAB' });
});
beatTL('4.R5', 'R5 Mecánica viva', 'Apunta y haz clic en una esfera: suena y viaja a tu mano. Haz clic en una gota del gusano para colocarla. El pad arranca con la primera.', null, () => {
  gate('G_SAVE4', 'Espera: guardar la melodía (SAVE)', 95, 120, { tick: () => S.saveHeld >= 3, onUser: () => { S.saveHeld = 0; }, sounds: ['FX_ORBGRAB', 'FX_ORB_*', 'FX_SLOTSNAP', 'FX_ORBHOME', 'FX_SAVEHOLD', 'HAP_CHARGE_RAMP'] });
  vo('VO_27b', 'Can you feel your magnetism?… What are you attracting?', ['G_SAVE4', 'start', 25]);
  clip({ key: 'SAVE_SHOW', track: 'ui', label: 'SAVE brilla en la otra mano', at: ['G_SAVE4', 'start', 75], end: ['G_SAVE4', 'end'], during: () => W.save = true });
  ghostSpan('GHOST_SAVE', 0xffe2c2, ['G_SAVE4', 'start', 75], ['G_SAVE4', 'end'], 'Hold SAVE');
  vo('VO_27c', 'When it sounds like you, hold SAVE.', ['G_SAVE4', 'start', 75]);
});
beatTL('4.coda', 'La coda', 'SAVE: se retiran beam y mandos; la mesa vuelve más alta y al frente y suenan dos pasadas completas de tu melodía.', null, () => {
  fx('FX_TOOLOUT');
  clip({ key: 'BEAM_OFF', track: 'obj', label: 'Se retiran beam y mandos · quedan las esferas colocadas', dur: 0, at: 0, apply: () => { W.beam = false; W.attract = false; W.orbsSlottedOnly = true; }, onStart: () => { S.data.melody = S.melody.slice(); S.saveHeld = 0; } });
  vo('VO_28', 'Listen… this is your melody.', 0);
  clip({ key: 'CODA', track: 'int', label: 'Dos pasadas de tu melodía', dur: 10.7, at: 0, during: () => W.coda = true, onStart: () => { S.seqT0 = S.clock; } });
  clip({ key: 'WORM_OUT', track: 'obj', label: 'El gusano y las esferas se van', dur: 0, at: ['CODA', 'end'], apply: () => { W.worm = 0; W.orbs = 0; } });
});
closingBeats(3);

/* ---------- E5 · SURROUNDING: dibujo ---------- */
act('Etapa 5 · Surrounding');
veilBeat(4);
stAt = almaBeat(4, ['V4/VEIL_OPEN', 'end']);
beatTL('5.R3', 'R3 Capas', 'La mesa sube del océano frente a ti.', [stAt, 'end'], () => {
  fx('FX_TABLERISE');
  clip({ key: 'TABLE_IN', track: 'obj', label: 'Sube la mesa', dur: 3, at: 0, apply: k => W.table = Math.max(.001, k) });
});
beatTL('5.R4', 'R4 Herramienta y demostración', 'La punta de dibujo en tu mano y la paleta en la otra. El fantasma: un mando elige color, el otro dibuja (idea de Beltrán).', null, () => {
  fx('FX_PALETTEAPPEAR');
  clip({ key: 'PALETTE', track: 'ui', label: 'Paleta en la otra mano · dibujo habilitado', at: 0, end: ['5.R5/G_SAVE5', 'end'], during: local => { W.palette = true; W.draw = true; if (local < 3) W.appear.palette = 0; }, reset: clearStrokes });   // escondida hasta que aparece
  clip({ key: 'PAL_IN', track: 'obj', label: 'Aparece la paleta (luz primero, 3 s de espera: AppearDelay)', dur: 1.5, at: ['PALETTE', 'start', 3], apply: k => { W.appear.palette = k; } });
  fx('FX_PALETTEAPPEAR', ['PAL_IN', 'start'], 'entrada de la paleta');
  clip({ key: 'PAL_OUT', track: 'obj', label: 'Se va la paleta (al revés)', dur: 1.5, at: ['PALETTE', 'end', -1.5], apply: k => { if (k < 1) W.appear.palette = 1 - k; } });
  fx('FX_PALETTEVANISH', ['PAL_OUT', 'start'], 'salida de la paleta');
  vo('VO_32', 'A painting of love, a dance of life, an image of the soul.', 0);
  vo('VO_32d', 'Bring your brush close to a color on your other hand to choose it… then hold the trigger and move to draw.', ['VO_32', 'end']);
  gate('G_DRAW', 'Espera: primer trazo', 6, 25, { tick: () => S.data.strokes.length > 0, sounds: ['FX_DRAW_BRUSH', 'FX_PALETTECLICK', 'HAP_DRAW_HUM', 'HAP_TICK'] });
  ghostSpan('GHOST_DRAW', 0xc9f0dd, 0, ['G_DRAW', 'end'], 'Pick a color · draw with the trigger   ·   (aquí: arrastra con el clic)');
  vo('VO_32h', 'Press the trigger and move your hand.', ['G_DRAW', 'start', 14], { help: 'G_DRAW' });
});
beatTL('5.R5', 'R5 Mecánica viva', 'Dibuja: los trazos se mecen suave. A los ~40 s una pregunta; a los ~60 s brilla SAVE.', null, () => {
  gate('G_SAVE5', 'Espera: guardar el dibujo (SAVE)', 75, 120, { tick: () => S.saveHeld >= 3 || S.inkSaved,   // o se acabó la tinta: guarda solo
    onUser: () => { S.saveHeld = 0; }, sounds: ['FX_DRAW_BRUSH', 'FX_PALETTECLICK', 'HAP_DRAW_HUM', 'FX_SAVEHOLD', 'HAP_CHARGE_RAMP'] });
  vo('VO_32b', 'Can your emotions become visible textures?', ['G_SAVE5', 'start', 40]);
  clip({ key: 'SAVE_SHOW', track: 'ui', label: 'SAVE brilla en la otra mano', at: ['G_SAVE5', 'start', 60], end: ['G_SAVE5', 'end'], during: () => W.save = true });
  ghostSpan('GHOST_SAVE', 0xc9f0dd, ['G_SAVE5', 'start', 60], ['G_SAVE5', 'end'], 'Hold SAVE');
  vo('VO_32c', 'Take your time… and when you feel it\'s complete, hold SAVE.', ['G_SAVE5', 'start', 60]);
});
beatTL('5.close', 'Cierre del dibujo', 'Tu dibujo crece, gira y se exhibe; después se encoge a un punto de luz y se guarda para la carta (no se borra).', null, () => {
  clip({ key: 'EXHIBIT', track: 'obj', label: 'Tu dibujo gira y se exhibe', dur: 4, at: 0, apply: k => W.strokesRot = k * 1.2 });
  clip({ key: 'SHRINK', track: 'obj', label: 'Se encoge a un punto de luz', dur: 1.5, at: ['EXHIBIT', 'end'], apply: k => { W.strokesRot = 1.2; W.strokesScale = k >= 1 ? 0 : 1 - k; } });
});
beatTL('5.release', 'Se van las herramientas', 'La punta y la paleta se disuelven en luz; vuelven las manos translúcidas (el sensor ya se fue al terminar Recognizing).', null, () => {
  fx('FX_SENSORRELEASE', 0, 'VFX_SENSORRELEASE'); hap('HAP_PULSE_SOFT');
  clip({ key: 'SENSOR_OUT', track: 'obj', label: 'El sensor se disuelve · vuelven las manos', dur: 2, at: 0, apply: k => { W.sensorScale = 1 - k; if (k >= 1) W.sensor = 'off'; } });
  clip({ key: 'TABLE_OUT', track: 'obj', label: 'La mesa se va', dur: 0, at: ['SENSOR_OUT', 'end'], apply: () => W.table = 0 });
});

/* ================= ACTO 9 · FINAL ================= */
act('Acto 9 · Final');
chargeBeat(4, true);
beatTL('9.1b', 'El alma sale nadando', 'El anillo se va (se hincha apenas y se cierra, junto con sus cinco anillos de color). El alma queda libre y nada como un pez, con curvas y una estela de chispas chicas (Beltrán, 09-30).', ['5.R6/FINAL', 'end', .5], () => {
  clip({ key: 'TELEPORT', track: 'pawn', label: 'En negro: el pawn aparece afuera de la puerta Este (el anillo sigue en su lugar)', dur: 0, at: 0, apply: () => { rigTo(PF1); hallG.visible = true; tiles.forEach((t, i) => setTile(i, 0, .55)); W.cont = 'world'; container.position.copy(front(PF1, .75, -.1)); container.quaternion.copy(PF1.q); } });
  fx('FX_RINGVANISH', 0, 'el anillo se va');
  clip({ key: 'RING_OUT', track: 'obj', label: 'El anillo se va animado', dur: .9, at: 0, apply: k => { W.ringIn = false; W.ringK = 1 - k; W.sr = [1, 1, 1, 1, 1]; soul.visible = k < .44; if (k >= 1) W.cont = 'off'; } });
  fx('FX_SOULSWIM', .4, 'el alma nada (estela de chispas)');
  clip({ key: 'FISH_OUT', track: 'obj', label: 'El alma sale nadando hacia la puerta', dur: 3, at: .4, apply: (k, local) => { W.fish = { a: front(PF1, .75, -.1), b: front(PF1, 2.4, .05), t: local, dur: 3, vis: clamp(local / .4), seed: 0 }; soul.material.uniforms.uGlow.value = lerp(.8, .12, ease(clamp(local / 1.5))); } });   // cometa sutil: el brillo de la carga se apaga al nadar
});
beatTL('9.3', 'El portal otra vez', 'Apenas el alma se desprende del anillo, en el negro empieza a aparecer el Center: la puerta se ilumina cálida y se abre sola; el alma nada adelante y la sigues.', ['9.1b', 'start', .3], () => {
  fx('FX_PORTALGLOW'); amb('AMB_08');
  clip({ key: 'PORTAL2', track: 'world', label: 'La puerta se ilumina cálida', dur: 3, at: 0, apply: k => hallU.uLight.value = k });
  clip({ key: 'CENTER_T2', track: 'world', label: 'SOUL CHARGER / CENTER, a la derecha de la puerta Este', dur: 3, at: 0, apply: k => { W.hallT.east = [k, 0]; } });
  clip({ key: 'CENTER_T2_OUT', track: 'world', label: 'Se va el título', dur: 1.5, at: ['PORTAL2', 'end', 1], apply: k => { W.hallT.east = [1, k]; } });
  fx('FX_DOOROPEN', ['PORTAL2', 'end']);
  clip({ key: 'DOOR_E2', track: 'world', label: 'Se abre sola', dur: 2.5, at: ['PORTAL2', 'end'], apply: k => setDoor('east', k) });
  vo('VO_34a', 'As you gently return… notice what has changed.', ['PORTAL2', 'end']);
  walk('WALK5', 'Vuelve a entrar al Hall', PF1, PF2, 6, ['PORTAL2', 'end']);
  clip({ key: 'CONT_FOLLOW', track: 'obj', label: 'El alma nada hacia adentro del Hall; la sigues', dur: 6, at: ['PORTAL2', 'end'], apply: (k, local) => { W.fish = { a: front(PF1, 2.4, .05), b: front(PF2, 2.0, .1, -.4), t: local, dur: 6, vis: 1, seed: 2 }; } });
  clip({ key: 'FISH_IDLE', track: 'obj', label: 'El alma nada en el lugar, esperándote', dur: 20, at: ['CONT_FOLLOW', 'end'], apply: (k, local) => { W.fish = { a: front(PF2, 2.0, .1, -.4), b: front(PF2, 2.0, .1, -.4), t: local + 6, dur: 26, amp: .12, vis: 1, seed: 2 }; } });
  clip({ key: 'DOOR_E2_CLOSE', track: 'world', label: 'La puerta se cierra', dur: 0, at: ['WALK5', 'end'], apply: () => setDoor('east', 0) });
});
beatTL('9.4', 'Los resultados', 'Alma te recibe y se corre a la izquierda. Al frente aparece el panel de tu viaje, una versión grande del HUD: la calma y el latido de toda la obra, un anillo por ciclo de respiración y el gusano con tu melodía sonando. A la izquierda flota tu alma con sus cinco luces; a la derecha, tu dibujo. Con el láser apuntas a cada parte y arriba aparece qué es.', null, () => {
  fx('FX_ALMAAPPEAR');
  clip({ key: 'ALMA_BACK', track: 'obj', label: 'Alma bajo el óculo', dur: 0, at: 0, apply: () => almaAt(ALMA_HALL, 1) });
  vo('VO_34c', 'Your journey is complete. Welcome back… Let me show you what I could perceive of you.', 0);
  clip({ key: 'ALMA_LEFT', track: 'obj', label: 'Alma se corre a la izquierda', dur: 3, at: ['VO_34c', 'end'], apply: k => almaAt(lv(ALMA_HALL, ALMA_RES, ease(k)), 1) });
  fx('FX_CARDAPPEAR', ['ALMA_LEFT', 'start', 1], 'VFX_RESULTS');
  clip({ key: 'RES_IN', track: 'obj', label: 'Aparece el panel de tu viaje (luz primero)', vfx: 'VFX_RESULTS', dur: 1.5, at: ['ALMA_LEFT', 'start', 1], apply: k => { resPlace(PF2); W.results = Math.max(.001, k); W.appear.results = k; W.resPlay = k >= 1; } });   // el gusano suena cuando el cuadro ya apareció y el pawn está quieto
  clip({ key: 'SOUL_TO_RES', track: 'obj', label: 'El alma nada hasta el costado izquierdo del panel', dur: 1.6, at: ['RES_IN', 'start'], apply: (k, local) => { W.fish = { a: front(PF2, 2.0, .1, -.4), b: resRingPos(PF2), t: local, dur: 1.6, amp: .12, vis: 1, seed: 3 }; } });
  fx('FX_RINGAPPEAR', ['SOUL_TO_RES', 'end'], 'el anillo vuelve');
  clip({ key: 'RING_IN', track: 'obj', label: 'El anillo reaparece grande alrededor del alma (~0,9 del alto del panel)', dur: .9, at: ['SOUL_TO_RES', 'end'], apply: k => { W.fish = null; W.cont = 'world'; container.position.copy(resRingPos(PF2)); container.quaternion.copy(resRingQuat(PF2)); container.scale.setScalar(RES_RING_S); W.ringIn = true; W.ringK = k; W.sr = [0, 0, 0, 0, 0]; } });
  vo('VO_34b', 'This is what I could perceive of you: your breath… your heartbeat… your calm… your melody… and what you carry inside.', ['RES_IN', 'end']);
  clip({ key: 'DRAW_GROW', track: 'obj', label: 'Tu dibujo se construye trazo a trazo (la animación de su etapa)', dur: 4, at: ['RES_IN', 'start', .4], apply: k => { W.drawGrow = ease(k); } });
  clip({ key: 'EXPLORA', track: 'int', label: 'Tiempo para explorar el cuadro con el láser: apunta a cada parte', dur: 25, at: ['VO_34b', 'end'], hint: 'Apunta con el mouse a cada parte: arriba aparece qué es', during: () => { W.resBeam = true; } });
});
beatTL('9.5', 'La invitación a compartir', 'Después de explorar, Alma pregunta si quieres compartir tu viaje: bajo el cuadro aparecen SHARE y DON\'T SHARE (la familia del SAVE). Se elige con láser + gatillo. Cortafuegos: no compartir.', null, () => {
  vo('VO_36', 'Is this you? Or only what I could measure of you?', 0);
  vo('VO_36b', 'Would you like to share your journey with others? If you do, your soul will join the constellation of every soul that passed through here.', ['VO_36', 'end', .6]);
  fx('FX_SHAREAPPEAR', ['VO_36b', 'end', -1.2], 'aparecen los botones');
  clip({ key: 'SHARE_IN', track: 'obj', label: 'Aparecen SHARE y DON\'T SHARE (luz primero)', dur: 1.2, at: ['VO_36b', 'end', -1.2], apply: k => { W.shareBtns = k; } });
  vo('VO_36p', 'Point at your answer… and pull the trigger.', ['SHARE_IN', 'end', .3]);
  gate('G_SHARE', 'Espera: compartir o no (láser + gatillo)', 6, 30, {
    tick: () => { const h = pick(SHARE_BTNS.map(b => b.userData.hit)); const idx = h ? (h.object.userData.share ? 0 : 1) : -1;
      if (idx !== S.shareHov) { S.shareHov = idx; if (idx >= 0) { cue('fx', 'FX_SHAREHOVER'); cue('hap', 'HAP_TICK'); } }
      if (consumeClick() && idx >= 0) { S.share = idx === 0; S.shareHov = -1; return true; } return false; },
    onFire: () => { S.share = false; S.shareHov = -1; }, sounds: ['FX_SHAREHOVER', 'HAP_TICK'],
    visual: (k, local, c, g) => { if (k >= 1) { S.shareHov = -1; return; } W.resBeam = true; if (!S.live) S.shareHov = local > 3.5 ? (S.share === false ? 1 : 0) : -1; },
  }, ['SHARE_IN', 'end']);
  fx('FX_SHARESELECT', ['G_SHARE', 'end'], 'confirmación'); hap('HAP_PULSE_STRONG', ['G_SHARE', 'end']);
  clip({ key: 'SHARE_PRESS', track: 'obj', label: 'El botón elegido se hunde y brilla', dur: .5, at: ['G_SHARE', 'end'], apply: k => { W.sharePress = [S.share === false ? 1 : 0, k]; } });
});
beatTL('9.5b', 'Tu respuesta', 'SHARE: se va lo del frente, tu alma se desprende del anillo y sale nadando como cometa, con campanitas, por la puerta del comienzo (se abre sola), rumbo a la constelación. DON\'T SHARE: tu alma se desvanece junto con lo demás y no estará en la constelación.', ['9.5/SHARE_PRESS', 'end'], () => {
  const yes = () => S.share !== false, no = () => S.share === false;
  vo('VO_36c', 'Thank you. Let it go… your light will find its place among the others.', .2, { when: yes });
  vo('VO_36d', 'That\'s alright. What you lived here stays with you.', .2, { when: no });
  fx('FX_HUDVANISH', 0, 'el cuadro, el dibujo y los botones se van');
  clip({ key: 'RES_OUT', track: 'obj', label: 'El cuadro, el dibujo y los botones se van (luz primero al revés; el dibujo se deshace)', dur: 1.5, at: 0, apply: k => { W.results = k < 1 ? 1 - k : 0; W.appear.results = 1 - k; W.resPlay = k < .5; W.shareBtns = 1 - k; W.drawGrow = 1 - ease(k); } });
  // SHARE
  fx('FX_RINGVANISH', .8, 'el anillo se va', { when: yes });
  clip({ key: 'RING_FREE', track: 'obj', label: 'SHARE · el anillo se va; el alma queda libre', dur: .9, at: .8, when: yes, apply: k => { W.cont = k < 1 ? 'world' : 'off'; container.position.copy(resRingPos(PF2)); container.quaternion.copy(resRingQuat(PF2)); container.scale.setScalar(RES_RING_S); W.ringIn = false; W.ringK = 1 - k; soul.visible = k < .44; } });
  fx('FX_SOULSWIM', 1.2, 'campanitas: el alma navega', { when: yes });
  clip({ key: 'FISH_DOOR', track: 'obj', label: 'SHARE · el alma nada hacia la puerta del comienzo', dur: 4, at: 1.2, when: yes, apply: (k, local) => { W.fish = { a: resRingPos(PF2), b: V(WEST.x + .7, 1.7, 0), t: local, dur: 4, amp: .22, vis: clamp(local / .4), seed: 4 }; } });
  fx('FX_DOOROPEN', ['FISH_DOOR', 'start', 1.3], 'la puerta se abre sola para el alma', { when: yes });
  clip({ key: 'DOOR_W_SOUL', track: 'world', label: 'SHARE · la puerta del comienzo se abre sola para el alma', dur: 2.5, at: ['FISH_DOOR', 'start', 1.3], when: yes, apply: k => setDoor('west', k) });
  fx('FX_SOULSWIM', ['FISH_DOOR', 'end'], 'campanitas: sale', { when: yes });
  clip({ key: 'FISH_AWAY', track: 'obj', label: 'SHARE · sale y se pierde en la oscuridad, rumbo a la constelación', dur: 3, at: ['FISH_DOOR', 'end'], when: yes, apply: (k, local) => { W.fish = { a: V(WEST.x + .7, 1.7, 0), b: V(WEST.x - 5, 2.4, .6), t: local, dur: 3, amp: .25, vis: 1 - ease(clamp((k - .55) / .45)), seed: 5 }; } });
  // DON'T SHARE
  fx('FX_SOULVANISH', .6, 'tu alma se desvanece', { when: no });
  clip({ key: 'SOUL_VANISH', track: 'obj', label: 'DON\'T SHARE · el anillo y tu alma se desvanecen con lo demás', dur: 1.6, at: .6, when: no, apply: k => { W.cont = k < 1 ? 'world' : 'off'; container.position.copy(resRingPos(PF2)); container.quaternion.copy(resRingQuat(PF2)); container.scale.setScalar(RES_RING_S * (1 - .45 * ease(k))); W.ringIn = false; W.ringK = 1 - k; soul.visible = k < .85; } });
});
beatTL('9.6', 'Salida del Hall', 'Alma se despide y ya no vuelve: desde aquí las voces son omnipresentes. La puerta del comienzo se abre (si tu alma salió, ya está abierta) y caminas hasta la parada 0. La niebla vuelve a ser azul.', null, () => {
  fx('FX_ALMAOUT');
  clip({ key: 'ALMA_GONE', track: 'obj', label: 'Alma se despide para siempre', dur: 1.2, at: 0, apply: k => almaAt(ALMA_RES, 1 - ease(k)) });
  fx('FX_DOOROPEN', .5, '', { when: () => S.share === false });
  clip({ key: 'DOOR_W2', track: 'world', label: 'Se abre la puerta del comienzo (si tu alma salió, ya estaba abierta)', dur: 2.5, at: .5, apply: k => setDoor('west', S.share === false ? k : 1) });
  walk('WALK6', 'Caminas hasta la parada 0', PF2, PF3, 10, .5);
  clip({ key: 'FOG_BACK', track: 'world', label: 'La niebla vuelve a ser azul · el Hall se apaga', dur: 10, at: .5, apply: k => { const f = clamp((k - .45) / .55); voidSky.material.uniforms.uAmt.value = f; dustMat.uniforms.uAmt.value = f; hallU.uLight.value = 1 - f; } });
  clip({ key: 'HALL_GONE', track: 'world', label: 'El Hall y la carta se van', dur: 0, at: ['WALK6', 'end'], apply: () => { hallG.visible = false; W.card = 0; } });
});
const T_END = [titleAt('SOUL CHARGER', GRAD_TITLE, PF3, 4, .35, .42), titleAt('A VR Interactive Biofeedback Experience', GRAD_TITLE, PF3, 4, .02, .09, true)];
// créditos oficiales (Beltrán, 2026-09-30): una tarjeta por rol, rol chico arriba y nombre grande abajo, de a una
const CREDITS = [
  ['CREATED AND PRODUCED BY', ['ALMA DIGITAL STUDIO']],
  ['WRITTEN AND DIRECTED BY', ['VICENTE MANZANO']],
  ['MUSIC BY', ['VICENTE MANZANO']],
  ['DEVELOPMENT DIRECTOR', ['BELTRÁN LIHN']],
  ['DEVELOPMENT ASSISTANT', ['NICOLÁS PERILLI']],
  ['IN COLLABORATION WITH', ['JOHNS HOPKINS', 'BERMAN INSTITUTE OF BIOETHICS']],
];
const CREDIT_IN = 1.5, CREDIT_HOLD = 4, CREDIT_OUT = 1.5;   // 7 s por tarjeta → 42 s las seis
const T_CREDITS = CREDITS.map(([role, names]) => [titleAt(role, GRAD_TITLE, PF3, 4, -.2, .045, true), ...names.map((n, j) => titleAt(n, GRAD_TITLE, PF3, 4, -.31 - j * .11, .085, true))]);
beatTL('9.7', 'La constelación y los créditos', 'Afuera del Hall, en la niebla azul: las almas anteriores flotan alrededor y la tuya es la última luz. Al frente el título SOUL CHARGER y abajo los créditos. Un minuto, fundido a negro y el nivel se reinicia.', null, () => {
  amb('AMB_09', 0, 'créditos');
  fx('FX_CONSTELLATION', 0, 'VFX_CONSTELLATION');
  clip({ key: 'STARS_IN', track: 'world', label: 'Se encienden las almas anteriores', dur: 5, at: 0, apply: k => W.stars = k });
  clip({ key: 'SOUL_UP', track: 'obj', label: 'SHARE · tu alma llega a su lugar: sin anillo, más brillante y con halo', dur: 3, at: ['STARS_IN', 'end'], apply: (k, local) => { if (S.share === false) return; const y = STARS.userData.yours; W.cont = 'off'; W.fish = { a: V(y.x - 1.4, y.y - .7, y.z + .4), b: y, t: local, dur: 3, amp: .15, vis: ease(clamp(k * 2)), seed: 6 }; W.fishHalo = ease(k); soul.material.uniforms.uGlow.value = lerp(.12, .5, ease(k)); } });
  fx('FX_SOULJOIN', ['SOUL_UP', 'end', -.5], 'tu alma se suma a la constelación', { when: () => S.share !== false });
  vo('VO_35b', 'Every soul that passed through here left a light. Now, yours is among them.', ['SOUL_UP', 'end'], { when: () => S.share !== false });
  vo('VO_35c', 'Every soul that passed through here left a light… look how they shine together.', ['SOUL_UP', 'end'], { when: () => S.share === false });
  vo('VO_37', 'If your soul left you a gift today… what would it be? Hold it softly throughout your day. Thank you for showing up.', ['VO_35b', 'end']);
  fx('FX_TITLE', ['SOUL_UP', 'end']);
  clip({ key: 'TF_IN', track: 'world', label: 'Título SOUL CHARGER al frente', dur: 4, at: ['SOUL_UP', 'end'], apply: k => revealTitle(T_END[0], k) });
  clip({ key: 'L1_IN', track: 'world', label: 'Créditos, abajo del título', dur: 2, at: ['TF_IN', 'end'], apply: k => revealTitle(T_END[1], k) });
  T_CREDITS.forEach((card, i) => {
    const K = 'CR' + (i + 1), at = i === 0 ? ['L1_IN', 'end', 2] : ['CR' + i + '_OUT', 'end'];
    clip({ key: K + '_IN', track: 'world', label: `Crédito ${i + 1}: ${CREDITS[i][0].toLowerCase()} ${CREDITS[i][1].join(' ')}`, dur: CREDIT_IN, at, apply: k => card.forEach(m => { m.material.uniforms.uO.value = 0; revealTitle(m, k); }) });
    clip({ key: K + '_OUT', track: 'world', label: `Se va el crédito ${i + 1}`, dur: CREDIT_OUT, at: [K + '_IN', 'end', CREDIT_HOLD], apply: k => card.forEach(m => outTitle(m, k)) });
  });
  clip({ key: 'QUEDA', track: 'int', label: 'Un minuto con la constelación, el título y los créditos', dur: 60, at: ['TF_IN', 'start'] });
  fx('FX_CREDITS', ['QUEDA', 'end']);
  clip({ key: 'NEGRO_FIN', track: 'world', label: 'Fundido a negro', dur: 3, at: ['QUEDA', 'end'], apply: k => { veilU.uTop.value.setRGB(0, 0, 0); veilU.uHor.value.setRGB(0, 0, 0); W.veil = ease(k); } });
  clip({ key: 'FIN', track: 'int', label: 'El nivel se reinicia (estado del inicio)', dur: 2, at: ['NEGRO_FIN', 'end'], apply: () => { voidSky.material.uniforms.uAmt.value = 1; dustMat.uniforms.uAmt.value = 1; } });
});

boot();
