# BPC_DrawTool — la HERRAMIENTA de dibujo portable (ActorComponent)

**Ruta:** `/Game/SoulCharger/Stages/Movement/BPC_DrawTool`
**Clase padre:** `ActorComponent`
**Estado:** 🟡 construido, compila con `warnings_as_errors`, verificado nodo a nodo por `get_node_infos`; **sin visor**.
**Creado:** 2026-09-04 (paso 1 del plan de `docs/MECANICAS-PORTABLES.md`).

## Purpose
La **capa MANAGER del dibujo**, extraída del modo 5 de [[BP_Sensor_Soul]] y de [[BP_ControllerRig]] a un ActorComponent reusable. Es el "driver" del contrato de 3 capas: filtra la punta (One-Euro), calcula la calma, gobierna el ciclo del trazo y habla con el MOTOR ([[BP_DrawCanvas]]). 🔴 **NO es dueño del input**: expone `Press()` / `Release()` y el anfitrión (el rig, o cualquier pawn) decide con qué gatillo los llama. Ese es el mandato de [[mecanicas-exportables-mandato]].

Reemplaza la lógica que estaba **duplicada** entre el rig (versión pobre: sin filtro, calma fija en 1.0) y el sensor (versión completa pero enterrada con metas/beam/toma). Ahora el rig es su **primer consumidor**.

## Cómo se usa (contrato del anfitrión)
1. Agregar el componente `DrawTool` al actor anfitrión (en el CDO).
2. En BeginPlay del anfitrión (tras resolver la mano), llamar **`Setup(Tip, Hand, Right, Width, Color, Mat, HapAmp)`**:
   - `Tip` = el SceneComponent desde cuyo `WorldLocation` nace el trazo (el `Marker` del rig).
   - `Hand` = el `MotionControllerComponent` de esa mano (para leer velocidad lineal/angular → calma). Puede ser null: `CalmStep` lo saltea con `IsValid`.
   - `Right`/`Width`/`Color`/`Mat`/`HapAmp` = configuración del trazo.
3. El anfitrión cablea su input a **`Press()`** (gatillo down) y **`Release()`** (gatillo up).
4. El **Tick del componente** hace todo lo demás solo (filtro + calma + háptica + feed al canvas) — no hace falta llamar nada por frame.

## Registro de variables
**Config (las setea `Setup`):**
- `TipRef` (SceneComponent) — la punta. El Tick no corre si es null.
- `HandMC` (MotionControllerComponent) — la mano para la calma.
- `DrawMat` (MaterialInterface, def `M_Emissive_Inst`) — 🔴 material del trazo; sin él `BeginStroke` haría `SetMaterial(None)`.
- `DrawColor` (LinearColor, def 0.35/0.7/1/1) · `DrawWidth` (float, def 1.8) · `HapticAmp` (float, def 0.25).
- `bRight` (bool) — mano hábil, para el canal háptico.
- `bCanDraw` (bool, def true) — salvaguarda propia del componente (el gate de input real lo pone el anfitrión).

**Estado interno:**
- `CanvasRef` (BP_DrawCanvas) — el motor, spawneado por `EnsureCanvas`.
- `bDrawHeld` — trazo activo. `bWasDrawHap` — flanco de la háptica. `bFiltInit` — semilla del One-Euro.
- `CalmVal` (def 1.0) — la calma viva 0-1, alimenta `VertexColor.A` del canvas.
- `FiltPos`/`FiltVel` (Vector) — estado del One-Euro. `SpeedEMA`/`TurnEMA` — EMAs de la calma.

**Constantes del One-Euro / calma (copiadas del CDO del sensor, probadas en visor):**
`MinCutoff` 1 · `Beta` 0.007 · `DCutoff` 1 · `VMax` 120 · `TurnMax` 200 · `SpeedTau` 0.15 · `CalmTauDown` 0.12 · `CalmTauUp` 0.6.

## Estructura de grafos
- **`Setup(...)`** — escribe la config, resetea `bFiltInit`/`bDrawHeld`/`CalmVal`, llama `EnsureCanvas`.
- **`EnsureCanvas()`** — si `CanvasRef` no es válido, spawnea `BP_DrawCanvas_C` en transform identidad. 🔴 El canvas SIEMPRE en identidad (el pincel manda puntos en mundo, el PMC los interpreta en local).
- **`Press()`** — `EnsureCanvas` → si `bCanDraw && !bDrawHeld`: `BeginStroke(Canvas, 0, Tip.WorldLoc, Tip.Up, DrawColor, DrawMat)` + `bDrawHeld=true`.
- **`Release()`** — si `bDrawHeld`: `EndStroke(Canvas)` + `bDrawHeld=false` + `DrawHapOff`.
- **`ToolTick(DT)`** (llamada desde `EventTick` bajo `IsValid(TipRef)`) — `DrawFilter(Tip.WorldLoc, DT)` → `CalmStep(DT)` → `DrawHaptic` → si `bDrawHeld`: `FeedPoint(Canvas, filtered, Tip.Up, DrawWidth, CalmVal)`.
- **`DrawFilter(Raw, DT)→Vector`** — One-Euro (clon exacto del sensor; primer frame siembra `FiltPos=Raw`).
- **`CalmStep(DT)`** — guard `IsValid(HandMC)` → `DrawCalm(DT)`.
- **`DrawCalm(DT)`** — EMA de velocidad lineal/angular del `HandMC` → `CalmVal` con tau asimétrico (clon del sensor).
- **`DrawHaptic()` / `DrawHapOff()`** — zumbido continuo `SetHapticsByValue(1.0, HapticAmp)` mientras `bDrawHeld`, flanco con `bWasDrawHap` (clon del sensor).

🔴 **Usa `FeedPoint` (no `AddPoint`)**: `FeedPoint` es el despachador del motor que elige sello (BrushId>0) o cinta (`AddPoint`). Ver [[BP_DrawCanvas]].

## Session log
- **2026-09-04**: creado. 20 variables + 11 grafos. Defaults escritos y verificados en el CDO por valor efectivo. Compila estricto. `BP_ControllerRig` migrado como primer consumidor (ver su tracker). Trampas del DSL evitadas: bools sin `b` en la forma larga (`SetFiltInit`, `SetDrawHeld`), `IsValid` al final de lista, llamadas locales mislabeladas por el read (`|DrawFilter`/`|CalmStep`/`|Setup`/`|Press`/`|Release`) confirmadas por `get_node_infos`.
- **2026-09-04 — ✅ VERIFICADO EN PIE** (aserción sobre el valor efectivo de las instancias vivas, no sobre la declaración). Con los 2 rigs de `/Game/TestMeshes`:
  | Qué | Rig izquierdo | Rig derecho |
  |---|---|---|
  | `TipRef` | su propio `Marker` | su propio `Marker` |
  | `HandMC` | `MotionControllerLeftGrip` | `MotionControllerRightGrip` |
  | `CanvasRef` | `BP_DrawCanvas_C_0` | `BP_DrawCanvas_C_1` (**uno por herramienta**) |
  | `bRight` · `DrawWidth` · `DrawMat` · `HapticAmp` | false · 1.8 · `M_Emissive_Inst` · 0.25 | true · ídem |
  `RIGDRAW INIT` una vez por rig, cero errores del componente en el log. **La cadena `InitDraw → Setup → EnsureCanvas` funciona end-to-end.** Falta solo el visor (el trazo real).

## TODO
- ⬜ **Visor**: que el rig dibuje con el componente (debería reproducir lo que ya andaba, más el filtro y la calma que el rig no tenía).
- ⬜ Desatar `BP_BrushPalette` del pawn y darle al componente una entrada de paleta (`SetColor`/`SetWidth`/`SetMat` en vivo, o leer una paleta por referencia) — hoy la config es fija por `Setup`.
- ⬜ Evaluar exponer `Wipe()` (destruir+respawn del canvas) si un consumidor necesita "borrar".

## Open questions
- El `bCanDraw` del componente es redundante con el gate de input del anfitrión. Se dejó como salvaguarda barata; revisar si molesta.
