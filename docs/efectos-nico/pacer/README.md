# Pacers de respiración — referencia para Unreal Engine

Paquete mínimo: solo los archivos de los pacers, para reconstruir la misma
estética y comportamiento en Unreal (Niagara / Material / UMG).

## Archivos

- `pacer-glsl.js` — fuente de verdad. Define:
  - 3 tipos: **Aros**, **Órbita**, **Arco** (`PACER_TYPES`).
  - El GLSL real (`PACER_FUNCS_GLSL`) que dibuja cada marcador como función
    de distancia radial `r` y ángulo `u` dentro de un anillo `[r0, r1]`,
    dejando el centro (`uPacClear`) intacto — traducible a un Material de
    Unreal (Custom HLSL node o Material Function) con la misma lógica.
  - El reloj de fases (`createBreathClock`): inhale → hold → exhale → hold,
    en bucle, con suavizado quintic (`smoother`, equivalente a `smoothstep`
    de 6ta potencia). Portar 1:1 a Blueprint/C++ como una máquina de estados
    con un `Timeline` o un `Tick` acumulando `dt`.
  - Presets de ritmo (`PACER_PRESETS`): Coherente 6-0-6-0, Box 4-4-4-4,
    4-7-8, Larga 5-2-8-2 — segundos por fase.
  - Uniforms/parámetros (`makePacerUniforms`, `PACER_DEFAULTS`): centro libre,
    opacidad, grosor, color, duración de cada fase — mapean directo a
    parámetros de instancia de Material o variables de Niagara.

- `pacers.html` — galería de referencia visual (SVG, no shader). Reimplementa
  los 3 marcadores en SVG puro para poder ver/tocar el timing sin GPU.
  Útil para comparar el resultado en Unreal contra el original a ojo.
  Abrir directo en el navegador.

## Conceptos clave a preservar en Unreal

- **Anillo perimetral, centro libre**: todo el trazo vive entre `uPacClear`
  (borde interior, 0.35–0.92 de radio) y el borde del disco útil (~0.97).
  Nunca invade el centro reservado al contenido del domo.
- **Un solo reloj de fases** alimenta los tres marcadores — no son relojes
  independientes. En Unreal: un único componente/actor de "reloj de
  respiración" que expone `lung` (0–1), `cycle` (0–1), `phase` (enum),
  `phasePos` (0–1) a lo que dibuje cada marcador.
- **Aros**: 5 aros concéntricos con retardo escalonado (`lag = i/5 * 0.3`)
  expandiéndose desde el centro libre hacia el borde según `lung`.
- **Órbita**: un punto recorre el perímetro una vez por ciclo completo;
  arcos separan visualmente las 4 fases proporcionalmente a su duración;
  un aro interior respira con `lung`.
- **Arco**: un solo arco se llena en la fase activa y se vacía en los
  sostenidos; escala de 60 marcas (mayor cada 15) en el borde; el más
  minimalista de los tres.
- Todo se dibuja en un **espacio polar normalizado** (radio 0–1, ángulo 0–1
  con `atan2`) — es el mismo espacio que un Material de Unreal calcularía
  desde UVs centrados (`nd = uv*2-1`, `r = length(nd)`, `u = atan2/TAU`).
