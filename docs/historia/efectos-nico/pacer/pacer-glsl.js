/* ───────────────────────────────────────────────────────────────────────────
   PACER · marcador de respiración dibujado EN EL SHADER, en el anillo exterior
   del dome master. Vive en el pase final (visor y export), así que aparece
   idéntico en la secuencia PNG. Nunca entra en el disco central reservado al
   efecto: todo se dibuja entre uPacClear y el borde.
   ─────────────────────────────────────────────────────────────────────────── */

export const PACER_TYPES = ['Ninguno', 'Aros', 'Órbita', 'Arco'];

export const PACER_UNIFORMS_GLSL = `
uniform int uPacer, uPacPhase;
uniform float uPacClear, uPacOpacity, uPacWidth, uPacLung, uPacCycle, uPacPhasePos;
uniform vec4 uPacSegs;
uniform vec3 uPacColor;
`;

export const PACER_FUNCS_GLSL = `
float pacSm(float x){ x = clamp(x, 0.0, 1.0); return x*x*x*(x*(x*6.0-15.0)+10.0); }
float pacStroke(float d, float w, float aa){ return 1.0 - smoothstep(w - aa, w + aa, abs(d)); }
float pacDot(vec2 p, vec2 c, float rad, float aa){ return 1.0 - smoothstep(rad, rad + aa*2.0, length(p - c)); }

float pacerAlpha(vec2 nd, float aa){
  if(uPacer == 0) return 0.0;
  float r = length(nd);
  float r0 = clamp(uPacClear, 0.1, 0.94), r1 = 0.97;
  if(r < r0 - 0.03 || r > r1 + 0.03) return 0.0;      // el centro queda intacto
  float band = max(r1 - r0, 0.02);
  float w = max(uPacWidth, 0.0004)*0.5;
  float ang = atan(nd.x, -nd.y);
  float u = ang < 0.0 ? (ang + 6.2831853)/6.2831853 : ang/6.2831853;
  float a = 0.0;

  if(uPacer == 1){                                    // ── Aros
    for(int i=0;i<5;i++){
      float fi = float(i);
      float lag = fi/5.0*0.30;
      float v = pacSm((uPacLung - lag)/(1.0 - lag));
      float rr = r0 + 0.012 + v*band*0.94*(fi + 1.0)/5.0;
      a = max(a, pacStroke(r - rr, w, aa)*(0.9 - fi*0.11));
    }
  } else if(uPacer == 2){                             // ── Órbita
    float rr = r1 - 0.012;
    a = max(a, pacStroke(r - rr, w*0.6, aa)*0.2);
    a = max(a, pacStroke(r - rr, w, aa)*step(u, uPacCycle)*0.9);
    float ca = uPacCycle*6.2831853;
    a = max(a, pacDot(nd, vec2(sin(ca), -cos(ca))*rr, w*2.2, aa));
    float rb = r0 + 0.012 + uPacLung*(rr - r0 - 0.04);
    a = max(a, pacStroke(r - rb, w*0.6, aa)*(0.25 + uPacLung*0.5));
  } else if(uPacer == 3){                             // ── Arco
    float rr = r1 - 0.03;
    a = max(a, pacStroke(r - rr, w*0.5, aa)*0.16);
    bool held = (uPacPhase == 1 || uPacPhase == 3);
    float frac = held ? 1.0 - uPacPhasePos : uPacPhasePos;
    a = max(a, pacStroke(r - rr, w*1.2, aa)*step(u, frac)*(held ? 0.45 : 0.95));
    // escala de 60 marcas al borde
    float tick = abs(fract(u*60.0) - 0.5)/60.0*6.2831853*max(r, 1e-3);
    float major = step(0.5, abs(fract(u*4.0) - 0.5)*2.0 + 0.5);
    float tLen = mix(0.016, 0.03, major);
    float inTick = step(r1 - tLen, r)*step(r, r1);
    a = max(a, pacStroke(tick, w*0.45, aa)*inTick*0.26);
    float rb = r0 + 0.012 + uPacLung*(rr - r0 - 0.05);
    a = max(a, pacStroke(r - rb, w*0.6, aa)*(0.22 + uPacLung*0.4));
  }
  return clamp(a, 0.0, 1.0)*uPacOpacity;
}
`;

/* Devuelve el bloque de uniformes compartido: pásalo POR REFERENCIA a todos los
   materiales que dibujan el pase final (visor y export) para actualizar una vez. */
export function makePacerUniforms(THREE){
  return {
    uPacer:      { value: 0 },
    uPacPhase:   { value: 0 },
    uPacClear:   { value: 0.62 },
    uPacOpacity: { value: 0.75 },
    uPacWidth:   { value: 0.006 },
    uPacLung:    { value: 0 },
    uPacCycle:   { value: 0 },
    uPacPhasePos:{ value: 0 },
    uPacSegs:    { value: new THREE.Vector4(0.5, 0, 0.5, 0) },
    uPacColor:   { value: new THREE.Color('#E7D3C6') },
  };
}

/* Línea a insertar en el fragmento justo antes de escribir el color final. */
export const PACER_COMPOSITE_GLSL = `
  { float pa = pacerAlpha(nd, 2.0/max(uRes.y, 1.0));
    c = mix(c, uPacColor, pa); }
`;

const smoother = x => { x = Math.min(1, Math.max(0, x)); return x*x*x*(x*(x*6-15)+10); };
const PHASE_IDX = { inhale:0, hold1:1, exhale:2, hold2:3 };

/* Reloj de fases reutilizable (inhale · hold · exhale · hold), en bucle. */
export function createBreathClock(P){
  const c = { t:0, lung:0, cycle:0, phase:'inhale', phasePos:0, total:12 };
  c.tick = dt => {
    const a = Math.max(0.2, P.pacInhale), b = Math.max(0, P.pacHold1),
          e = Math.max(0.2, P.pacExhale), h = Math.max(0, P.pacHold2);
    const total = a + b + e + h;
    c.total = total;
    c.t = (c.t + dt) % total;
    c.cycle = c.t/total;
    const x = c.t;
    if(x < a){          c.phase='inhale'; c.phasePos = x/a;                        c.lung = smoother(c.phasePos); }
    else if(x < a+b){   c.phase='hold1';  c.phasePos = (x-a)/Math.max(b,1e-4);     c.lung = 1; }
    else if(x < a+b+e){ c.phase='exhale'; c.phasePos = (x-a-b)/e;                  c.lung = 1 - smoother(c.phasePos); }
    else {              c.phase='hold2';  c.phasePos = (x-a-b-e)/Math.max(h,1e-4); c.lung = 0; }
  };
  return c;
}

/* Vuelca el reloj en los uniformes. lungOverride permite atar el pacer al
   pulmón que ya calcula el efecto (organism) en vez de al reloj propio. */
export function syncPacerUniforms(U, P, clock, lungOverride){
  U.uPacer.value = Math.max(0, PACER_TYPES.indexOf(P.pacer));
  U.uPacClear.value = P.pacClear;
  U.uPacOpacity.value = P.pacOpacity;
  U.uPacWidth.value = P.pacWidth;
  U.uPacLung.value = lungOverride !== undefined ? lungOverride : clock.lung;
  U.uPacCycle.value = clock.cycle;
  U.uPacPhase.value = PHASE_IDX[clock.phase];
  U.uPacPhasePos.value = clock.phasePos;
  const a = Math.max(0.2, P.pacInhale), b = Math.max(0, P.pacHold1),
        e = Math.max(0.2, P.pacExhale), h = Math.max(0, P.pacHold2);
  const t = a + b + e + h;
  U.uPacSegs.value.set(a/t, b/t, e/t, h/t);
  U.uPacColor.value.set(P.pacColor);
}

export const PACER_DEFAULTS = {
  pacer:'Aros', pacClear:0.62, pacOpacity:0.85, pacWidth:0.008,
  pacColor:'#6E4534', pacInhale:6, pacHold1:0, pacExhale:6, pacHold2:0,
  pacPreset:'Coherente 6-0-6-0',
};

export const PACER_PRESETS = {
  'Coherente 6-0-6-0':[6,0,6,0], 'Box 4-4-4-4':[4,4,4,4],
  '4-7-8':[4,7,8,0], 'Larga 5-2-8-2':[5,2,8,2],
};

/* Carpeta de GUI estándar. onChange se llama tras cualquier cambio. */
export function addPacerGUI(gui, P, clock, folderName = 'Pacer de respiración'){
  const f = gui.addFolder(folderName);
  f.add(P, 'pacer', PACER_TYPES).name('Marcador');
  f.add(P, 'pacClear', 0.35, 0.92, 0.01).name('Centro libre');
  f.add(P, 'pacOpacity', 0, 1, 0.01).name('Opacidad');
  f.add(P, 'pacWidth', 0.001, 0.02, 0.0005).name('Grosor');
  f.addColor(P, 'pacColor').name('Color');
  const ctrls = [];
  f.add(P, 'pacPreset', Object.keys(PACER_PRESETS)).name('Preset').onChange(v => {
    const m = PACER_PRESETS[v];
    if(m){ [P.pacInhale, P.pacHold1, P.pacExhale, P.pacHold2] = m; clock.t = 0;
      ctrls.forEach(c => c.updateDisplay()); }
  });
  ctrls.push(f.add(P, 'pacInhale', 1, 20, 0.5).name('Inhale s'));
  ctrls.push(f.add(P, 'pacHold1', 0, 20, 0.5).name('Hold s'));
  ctrls.push(f.add(P, 'pacExhale', 1, 20, 0.5).name('Exhale s'));
  ctrls.push(f.add(P, 'pacHold2', 0, 20, 0.5).name('Hold s'));
  f.add({ r: () => { clock.t = 0; } }, 'r').name('Reiniciar ciclo');
  f.close();
  return f;
}
