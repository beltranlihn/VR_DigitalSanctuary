# Plan: FLUIDO CEREBRAL en Unreal — `BP_FluidMedium_SC`

> 2026-09-28. Pedido de Beltrán: *"hacer sentir al usuario que estamos sumergidos en un entorno líquido, como el
> líquido del cerebro; que se sienta 3D, amplio, etéreo"*. Ajustes del mismo día: **sin latido ni respiración** (eso
> vive en Heart), *"basta con movimiento curl de las partículas en general y que se sienta un movimiento de fluido"*,
> *"más de estos seres celulares repartidos en el espacio, desvanecidos porque están en el agua"*, y **la única
> entrada de la etapa es el EEG: una variable 0-1**. *"Siempre pensando que corra en un APK."*
>
> **Referencia visual y matemática (fuente de verdad del look):** `docs/prototipos/fluido-cerebral.html`
> (publicado: https://claude.ai/artifact/2y5MS73Eo8PFgFLL6UjVPZ). Todo lo que sigue es portar ESE prototipo, no
> rediseñarlo: mismas funciones, mismas perillas con los mismos nombres.
>
> Estado (2026-09-28, noche): 🟢 prototipo web · 🟢 **F1, F2 y F3 construidas en `Test_Fluid`** (detalle y trampas en el
> tracker `.claude/skills/unreal-vr/blueprints/BP_FluidMedium_SC.md`) · ⬜ PIE con `bFakeEEG` · ⬜ F4 manos · ⬜ F5 célula de
> Loving adentro · ⬜ visor · ⬜ medición (F6).
>
> **Lo que la revisión de fidelidad agregó y ya está aplicado en la construcción:** fondo con radio ≥ 70 m (se usó 100 m);
> `Test_Fluid` con el Ganzfeld OCULTO (no borrado); las manos son una SEGUNDA entrada, apagadas por defecto (`bHandStir`);
> orden de dibujo explícito (velos −2, haces −1, partículas lejos 1 / media 2 / cerca 50); haces PROPIOS (no
> `BP_LightShaft_SC`: trae pulso y respiración); los datos de F2-F3 empaquetados en los vectores libres de la MPC
> (`Extras`, `FarA.w`, `Light.w`); nombres de perilla `FakePeriod`/`bFakeEEG`.
> **Desvíos del prototipo decididos mirando el editor:** células medias en un cubo de 18 m (no 26: quedaban a 6-10 m, 15 px),
> escala 1,1 (no 0,55), contraste 1 (no 0,6: elipses planas), núcleo con los pseudópodos de Loving y satélites pegados
> (1,9-2,3 radios); siluetas lejanas de 80 cm; hash ENTERO en los shaders (gotcha 481).

---

## 1. Qué se construye

Un actor **portable** `BP_FluidMedium_SC` (carpeta `/Game/SoulCharger/Mechanics/Fluid/`) que se coloca en el nivel de
una etapa y crea el medio líquido alrededor del usuario. No toca el pawn ni `Core/`. La célula de Loving
(`BP_LovingCell_SC`) sigue siendo su propio actor: el fluido la envuelve, no la contiene.

| Capa | Qué hace | Cómo (Quest) |
|---|---|---|
| **Fondo** | El medio en el infinito: degradado de 3 colores + luz desde arriba | Esfera invertida (reusar `SM_GanzShell`, 9k tris) + `M_FluidBackground_SC` opaco unlit, dither R2. **Reemplaza al Ganzfeld** en la etapa (el fluido de Ganzfeld pesa ~13 ms; esto es un degradado) |
| **Partículas** ×3 | Cerca (cubo 3,6 m) · media (12 m) · lejos (40 m), recicladas alrededor de la cabeza | Nubes de quads con semillas en las UV, posicionadas en el VS (técnica `SM_LovingDust_SC`). Una llamada por capa |
| **Movimiento** | Corriente que cambia de rumbo despacio + remolinos CURL sin divergencia de dos escalas + estela | Todo en el VS, cerrado en función de dos datos que integra el BP: la fase y el arrastre acumulado |
| **Absorción** | Todo se funde hacia el color del medio EN ESA DIRECCIÓN | La misma función `FluidColor` del fondo, en cada material: lo lejano cae exacto en el fondo. Sin transparencia |
| **Células medias** (8-16) | Seres simplificados a 3-13 m, llevados por la corriente | UNA malla con 16 células de baja resolución (núcleo + 3-5 satélites), movidas en el VS. **Opacas**: el desvanecido es color |
| **Células lejanas** (48) | Siluetas a 10-35 m | Nube de quads; silueta (núcleo + satélites) en el PS; borde por **alpha-to-coverage** (MSAA 4x) |
| **Luz en el agua** | Cáusticas sobre las células, destellos en partículas, haces tenues, velos lejanos | Función cáustica sin textura; haces: evaluar reusar `BP_LightShaft_SC` antes de hacer uno propio; velos: 6 quads en una malla |
| **Manos** | Revuelven el medio (empuje + remolino) | 2 manos = 4 vectores en la MPC; la fuente de las posiciones se decide (§7) |
| **Sonido** | Rumor filtrado "bajo el agua" | Loop ambiente con pasa-bajos (ver `references/audio-quest.md`) — fase final |

**Entrada única: `EEG` (0 = mente activa, 1 = calma)** — la misma convención que `GlobalState` de
`BP_LovingCell_SC`; la etapa escribe el mismo valor en los dos actores. El BP lo suaviza (`EEGSmoothing`) y con él escala:

| Activo (0) | Calma (1) |
|---|---|
| remolinos hasta 1,8× más rápidos (`EEGFlow`), más remolinos chicos, más estela, corriente +40 % | velocidad a la mitad, casi sin remolinos chicos, estela −40 %, corriente −40 % |
| el agua un poco más densa (absorción −20 %) | el agua se aclara: distancia de absorción hasta 1,8× (`EEGClarity`) → se ve más lejos, el espacio se abre |

Las fórmulas exactas están en `frame()` del prototipo (bloque "EEG: la única entrada").

---

## 2. Arquitectura (mismo patrón que Loving y `MPC_Breath`)

**El BP integra el TIEMPO; los shaders calculan la FORMA.** Nada de estado por partícula, nada en la CPU por partícula.

```
BP_FluidMedium_SC (Tick)
 ├─ EEG → EEGS (suavizado) → EFF (perillas moduladas)            ← §1
 ├─ integra: FlowPhase += dt·EFF.FlowSpeed · CausticPhase += dt·CausticSpeed
 │           Drift += DriftVel·dt   (DriftVel = rumbo con Meander × EFF.CurrentSpeed)
 ├─ HeadL = cámara en espacio LOCAL del actor (GetPlayerCameraManager → InverseTransformLocation)
 └─ empuja UNA MPC: MPC_Fluid_SC (≈12 vectores)                    ← una escritura por vector por cuadro
        │
        ├─ M_FluidBackground_SC   (fondo)
        ├─ M_FluidMotes_SC        (3 componentes; por capa: LayerA/LayerB en MID, fijados en el CS)
        ├─ M_FluidMidCells_SC     (1 componente)
        ├─ M_FluidFarCells_SC     (1 componente, alpha-to-coverage)
        ├─ M_FluidVeil_SC / haces
        └─ (opcional, fase 5) los materiales de la célula de Loving leen la MPC para absorción + cáusticas
```

- **MPC y no parámetros por material**: los datos globales (colores del medio, absorción, fases, arrastre, cabeza,
  manos) son los mismos para todos los materiales; una MPC los publica una vez y cualquier material del proyecto
  puede leerlos (incluida la célula) sin acoplar Blueprints. Precedentes: `MPC_Breath`, `MPC_LightShaft`, `MPC_NeuralWeb`.
- **Espacio LOCAL del actor, como Loving**: el actor va con rotación identidad en el origen del usuario; toda la
  cuenta usa `LocalPosition` y la cámara en local (`CamL` por ojo; `HeadL` = centro de los cubos, igual para los dos
  ojos). Evita el LWC de `AbsoluteWorldPosition` en los Custom.
- **Límite del WPO**: los wrappers de Loving recortan el desplazamiento a 400 cm; aquí las partículas viajan hasta
  ~35 m desde su vértice → recorte a **20 000 cm**. Y **BoundsScale grande** en cada componente (la geometría real está
  siempre alrededor del usuario; nunca debe descartarse por frustum).

### Variables del BP (los nombres de las perillas del prototipo, tal cual)
| Categoría | Variables (default del prototipo) |
|---|---|
| `0-EEG` | `EEG` 0,3 · `EEGSmoothing` 2 s · `EEGFlow` 0,7 · `EEGClarity` 0,5 · `bFakeEEG` (señal de prueba 60 s, como `bFakeSignal` de la célula) |
| `1-Movimiento` | `CurrentSpeed` 4 cm/s · `CurrentYaw` 20° · `CurrentPitch` 8° · `Meander` 35° · `FlowAmp` 22 cm · `FlowScale` 130 cm · `FlowSpeed` 0,14 rad/s · `Turbulence` 0,7 · `StreakTime` 0,22 s |
| `2-Liquido` | `FluidTop/Mid/Bottom` · `GlowColor` · `GlowAmount` 0,45 · `GlowPower` 3 · `AbsorbDist` 800 cm · `AbsorbMax` 0,92 · `AbsorbAlpha` 0,35 |
| `3-Particulas` | `MoteColor` · `MoteBright` 1,25 · `NearSize/MidSize/FarSize` 0,45/1,3/6 cm · `NearAlpha/MidAlpha/FarAlpha` 0,85/0,6/0,5 · `Bokeh` 3 · `BokehDist` 60 cm |
| `4-Celulas` | `MidCellCount` 8 · `MidCellScale` 0,55 · `FarCellCount` 48 · `FarCellSize` 55 cm · `CellFlow` 0,6 · `CellHigh/CellLow` |
| `5-Luz` | `CausticAmount` 0,6 · `CausticScale` 18 cm · `CausticSpeed` 0,6 · `MoteSparkle` 0,8 · `ShaftAmount` 0,14 · `VeilAmount` 0,5 |
| `6-Manos` | `StirStrength` 0,18 s · `StirRadius` 22 cm · `StirSwirl` 0,8 |
| `Z-Interno` | `EEGS` · `FlowPhase` · `CausticPhase` · `Drift` · `DriftVel` · `Eff*` |
Colores por defecto: paleta "Frío profundo" del prototipo (botón "Copiar valores" → JSON con los colores ya LINEALES).
🔴 Las **cantidades** de partículas y células son MALLAS generadas (ver §3): en Unreal se eligen al generar, no en vivo.
Para poder bajar sin regenerar, cada malla trae su índice normalizado en una UV y el material colapsa los quads por
encima de `Count/Total` (el VS sigue corriendo: bajar la cantidad así ahorra RELLENO, no vértices).

---

## 3. Assets

### Shaders (fuente única en texto, como Loving)
- `VR_Test/Shaders/Fluid/FluidLib.ush` — port LÍNEA POR LÍNEA del GLSL del prototipo: `FluidColor`, `AbsorbAt`,
  `Caustic`, `SinCurl`, `RotR`, `RotRT`, `FlowAt`, `Stir`, `WrapHead`, `CellShade`. (GLSL → HLSL: `mix→lerp`,
  `fract→frac`, `clamp(x,0,1)→saturate`, `vecN→floatN`, `cameraPosition→CamL`, fases → parámetros de la MPC.)
- `VR_Test/Shaders/Fluid/wrappers/`: `FluidBgPS`, `FluidMotesVS/PS`, `FluidMidCellsVS/PS`, `FluidFarCellsVS/PS`,
  `FluidVeilVS/PS` (+ `FluidShaftVS/PS` si no se reusa el haz existente).
- **Herramientas**: generalizar `compose_loving.py` y `check_loving_hlsl.py` con `--lib/--wrappers/--out` (defaults =
  Loving, sin romper su uso actual) en vez de duplicarlas. El chequeo DXC offline es obligatorio antes de tocar el editor.
- Verificación numérica: un port Python de `FlowAt` contra el JS del prototipo (misma salida a 1e-6 en 10k puntos) y
  la divergencia del campo ≈ 0 por diferencias finitas.

### Mallas (Blender headless, generador versionado `scripts/gen_fluid_canvases.py`, patrón `polvo()` de Loving)
| Malla | Contenido | Vértices |
|---|---|---|
| `SM_FluidMotes_Near/Mid/Far_SC` | 600 / 2400 / 4000 quads de 0,4 cm; UV0 esquina, UV1 semilla xy, UV2 (semilla z, fase/tamaño), UV3 índice normalizado | 2,4k / 9,6k / 16k |
| `SM_FluidMidCells_SC` | 16 células × (núcleo icoesfera **642** v + 5 satélites 42 v); cada vértice lleva su célula y su pieza en las UV; la posición es la dirección unitaria | 13,6k en Blender · **18 624 en UE** (costuras de la UV0 cúbica) |
| `SM_FluidFarCells_SC` | 64 quads (se usan `FarCellCount`) | 256 |
| `SM_FluidVeils_SC` | 6 quads con centro/tamaño/tinte en las UV | 24 |
| fondo | **reusar `SM_GanzShell`** (Core/Light) | 9k tris |
⚠ Gotcha 302: Unreal invierte la V al importar (`UV.y = 1 − v`): las semillas al azar no se enteran, pero los ÍNDICES
codificados en V sí → codificarlos en U o compensar `1 − v`. ⚠ Semillas: activar **Full Precision UVs** en las mallas
(en half, una semilla sobre un cubo de 40 m cuantiza a ~2 cm: aceptable; los índices de pieza NO).

### Materiales (`/Game/SoulCharger/Mechanics/Fluid/Materials/`)
| Material | Blend | Notas |
|---|---|---|
| `M_FluidBackground_SC` | Opaco unlit, two-sided | dirección = `normalize(WorldPos − CameraPos)` (independiente del centro de la esfera); dither R2 |
| `M_FluidMotes_SC` | Translucent (alfa normal), unlit | un maestro; `LayerA/LayerB` por componente (MID fijado en el CS) |
| `M_FluidMidCells_SC` | Opaco unlit | `CellShade` + cáusticas + absorción; normal = radial desde el centro de cada pieza (exacta en el VS) |
| `M_FluidFarCells_SC` | **Masked + alpha-to-coverage** | 🔴 verificar la propiedad en UE 5.8 (`bUseAlphaToCoverage`) y que funcione en el móvil con MSAA; plan B: dither R2 de pantalla sobre Masked |
| `M_FluidVeil_SC` | Translucent unlit | velos: pocos y lejanos; es la capa de más RELLENO → perilla `VeilAmount` 0 = componente oculto |
Reglas Quest de siempre: `floatPrecisionMode = MFPM_Full_MaterialExpressionOnly` donde el PS recalcule algo del VS;
tiempo por fase integrada (nunca `Time × velocidad` con una perilla: gotcha 329); sin arreglos ni índices dinámicos
(las 5 órbitas de satélite: bucle de cota constante); cada Custom con salidas mínimas (un Custom que alimenta WPO e
interpoladores corre dos veces).

---

## 4. Orden de construcción (cada fase se prueba antes de la siguiente)

**F0 — Sin editor (puedo adelantarla ya):** `FluidLib.ush` + wrappers portados del prototipo · scripts generalizados ·
DXC "TODO COMPILA" · verificación numérica JS↔HLSL · `gen_fluid_canvases.py` + FBX de las mallas · este plan revisado.

**F1 — El medio (editor, ~1 sesión):**
1. Nivel de prueba **`/Game/Test_Fluid`** (copia de `Test_Loving` CON la célula y su Ganzfeld oculto; `Test_Loving` queda intacto).
2. Importar mallas; crear `MPC_Fluid_SC`, `M_FluidBackground_SC`, `M_FluidMotes_SC`.
3. `BP_FluidMedium_SC`: componentes (fondo + 3 capas), variables §2, `Tick` con EEG/fases/arrastre/HeadL → MPC,
   Construction Script que fija `LayerA/LayerB` y `BoundsScale`.
4. Verificar en PIE: el cubo se recicla sin saltos visibles (borde con fundido), la corriente cambia de rumbo sin
   saltos, cambiar `FlowSpeed` en vivo NO salta, `bFakeEEG` recorre activo ↔ calma. Capturas con el recorte del
   ELEMENTO (memoria "verificar-recorte-del-elemento").

**F2 — Células en el agua:** `SM_FluidMidCells_SC` + `M_FluidMidCells_SC`; `SM_FluidFarCells_SC` +
`M_FluidFarCells_SC` (alpha-to-coverage). Verificar: ninguna célula media a menos de 2,5 m (se achica), bordes del
cubo invisibles, las lejanas se funden en el fondo.

**F3 — Luz en el agua:** cáusticas en las células medias; destellos en partículas; velos; haces (primero probar
`BP_LightShaft_SC` con parámetros tenues; si no da el look, `FluidShaftVS/PS` del prototipo).

**F4 — Manos y sonido:** posiciones y velocidades de las dos manos a la MPC (fuente a decidir, §7); rumor filtrado.

**F5 — Con la célula de Loving:** colocar `BP_FluidMedium_SC` en `Test_Loving`; ocultar el Ganzfeld (🔴 sacar un
actor se pregunta: se oculta, no se borra, hasta que Beltrán diga); opcional: que los materiales de la célula lean la
MPC para absorción + cáusticas (a 1,7 m la absorción es chica pero unifica el color; es una edición de `LovingLib`,
se coordina con ese tracker).

**F6 — APK Development + medición** (reescrito tras la revisión COS-6: las perillas NO se pueden cambiar en un APK, y
el banco de FrameTime de Attracting tenía ~1 ms de resolución): un **`BP_PerfFluid_SC`** en `Core/Debug` con el patrón de
`BP_PerfEntering_SC` (busca el fluido por clase, `ke * PerfF0..N`, cada modo con eco en logcat; hace SetVisibility por
componente — el BP de la etapa no se entera). Medir **App GPU de VrApi** con una copia de `quest_entering_perf.ps1` /
`resumen_entering.py` (resolución 0,09 ms en Entering), pasadas ida-vuelta-ida en UNA sesión, 30 s por modo descartando
los 2 s iniciales, visor quieto y arrastre congelado (CurrentSpeed 0, Meander 0). Modos: P0 todo · P1 sin velos ·
P2 sin haces (CONTROL NEGATIVO: ≈ 0) · P3 sin medias · P4 medias 16 (¿corta el early return?) · P5 sin lejanas · P6 sin
motas (P6b solo sin las lejanas) · P7 sin fondo · **P8 fondo = `M_GanzSolid_SC`** (el incremento real sobre lo que la etapa
ya pagaba) · P9 sin fluido (aditividad). Los modos de < 0,1 ms (haces, lejanas) se agrupan. Resultado al tracker.

---

## 5. Presupuesto (estimado, hay que medirlo)

Referencia medida: la membrana de Heart, 78 849 vértices × ~4 400 op-eq → 3,8-5,4 ms. La célula V4 estimada ~4,1 ms
de vértices (5 grupos).

| Capa | Vértices | Costo por vértice | Relleno | Estimado |
|---|---|---|---|---|
| Partículas (3 capas) | ~28k | 2× `FlowAt` (estela) + cáustica ≈ 600-800 op-eq | puntos diminutos; el desenfoque cercano es la parte cara | ~0,3-0,6 ms |
| Células medias | **18 624** (12 de 16 vivas) | ameba (4 lóbulos) + `FlowAt` + órbitas; el Custom se evalúa 2 veces (WPO + interpoladores) | opacas, poca pantalla | **~0,3-0,45 ms** (revisión COS-1; −0,07-0,1 con los hashes agrupados) |
| Células lejanas | 256 | `FlowAt` | quads chicos, A2C sin ordenar | <0,2 ms |
| Velos (6) | 24 | trivial | **quads enormes translúcidos**: ~0,8 pantallas por ojo (p95 1,5-1,7) | **~0,15-0,45 ms** (p95 hasta 0,9) para ≤ 1 escalón en casi todo su área |
| Fondo | 9k tris | trivial | pantalla completa OPACA, 1 degradado | +0,4-0,75 ms sobre `M_GanzSolid_SC` con el dither de dos `pow`; **~cero extra con el dither sqrt** (COS-2, aplicado) |
Objetivo: el fluido completo **≤ 1,5 ms** sumado a la célula. Estimado tras la revisión y sus arreglos (COS-2/3/4): **~0,9-1,8 ms**,
a confirmar en F6. Palancas si no entra, en orden: velos (relleno; `VeilAmount` 0 = componente oculto), cantidad de células
medias, motas lejanas (4000 → 2000 exige regenerar la malla: no hay perilla de cantidad), fondo con color por vértice.

---

## 6. Verificaciones que NO se saltean
- DXC offline antes de cada inyección; log del editor con corte por línea después de cada `recompile`.
- Capturar dos veces tras reinyectar un material (la primera sale sin él: gotcha 476).
- Componentes nuevos en una instancia YA colocada: diffear instancia vs plantilla y escribir de a una propiedad
  (gotcha 478); variables nuevas nacen en 0 en la instancia.
- `IsPIERunning` antes de compilar/guardar; guardar con rutas explícitas; contar actores antes/después; nada de
  `save_assets([])` (hay otras sesiones en el editor).

## 7. Decisiones abiertas (para Beltrán)
1. **Manos**: ¿de dónde toma el fluido las posiciones de las manos en la etapa? Opciones: (a) la etapa se las pasa
   (`SetHandComponents`), (b) el actor busca los `MotionControllerComponent` del pawn por clase. (a) respeta la
   arquitectura Manager/Control; (b) es autónomo. Recomendado: (a).
2. **Haces**: reusar `BP_LightShaft_SC` o los del prototipo (más finos). Se decide mirando en F3.
3. **Paleta**: "Frío profundo" (default del prototipo), "Tibio orgánico" o "Lavanda (Loving)"; se cambia con perillas.
4. **La célula dentro del fluido**: ¿su color se unifica con el medio (F5 opcional) o queda como está?

## 8. Primera sesión con el editor (orden exacto)
1. Coordinar la ventana con las otras sesiones (SendMessage), `IsPIERunning`, nivel abierto.
2. Crear `Test_Fluid` (copia de `Test_Loving`, con la célula y el Ganzfeld oculto) — contar actores.
3. Importar las mallas de F0; crear la MPC y los tres primeros materiales; inyectar el HLSL compuesto; recompilar
   y leer el log.
4. Crear `BP_FluidMedium_SC` (componentes, variables, Tick, CS) con el DSL escrito en F0; compilar con
   `warnings_as_errors`.
5. Colocarlo; `bFakeEEG` = true; PIE; capturas de activo y de calma; mostrar a Beltrán.
