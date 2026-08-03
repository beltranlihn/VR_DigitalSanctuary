# BP_BrushPalette — progress tracker

- **refPath**: `/Game/SoulCharger/Stages/Movement/BP_BrushPalette.BP_BrushPalette` · **parent**: Actor · **en nivel**: no (la **spawnea `BP_BrushTool`** al agarrar el pincel).
- **Propósito**: la **paleta de configuración** del stage Movement. Grilla plana de **9 celdas (3×3)** sobre la mano no hábil: 3 colores · 3 grosores · 3 pinceles. Se selecciona tocando con la punta del pincel. El pincel lee color/ancho/material de acá al empezar cada trazo. Plan: [`docs/stages/movement-surrounding.md`](../../../../docs/stages/movement-surrounding.md) §5.3 y §8.b.
- **Estado**: 🟢 **Fases 4.1 + 4.2 + 4.3 construidas y VALIDADAS en visor (2026-08-03).** La paleta aparece en la mano contraria; **color y grosor funcionan end-to-end** (el grosor tras arreglar el bug del pin `Width`, ver abajo). El pincel todavía no se nota porque los 3 apuntan al mismo material → **falta 4.4**.

## ✅ RESUELTO (2026-08-03) — era `ComputeWidth` inline en el pin `Width`
**Confirmado por `get_node_infos`:** el pin `Width` del `AddPoint` estaba `"value":"0.0", "connected_pins":[]` — **desconectado**. Los demás pines (`NewLoc`, `ControllerUp`, `Calm`) sí tenían cable. Causa: **una función impura inline como argumento de datos** (ver `gotchas.md`, sección destacada). El ancho llegaba **0** → todos los trazos con el grosor mínimo (sólo el piso de `MinThickness`), sin importar la selección.
**Fix aplicado:** `ComputeWidth` **borrada** (ya no aportaba nada: el ancho dejó de venir de la presión) y `:Width` cableado con el getter puro `GetBrushWidth`. Verificado en visor: **"ahora sí, muy perceptible"**. Prints de debug removidos de `UpdateTouch` y `UpdateStroke`.
🔑 **Bonus:** esto también explicaba parte del *"se ve muy geométrico"* — con semi-ancho 0, lo que se veía era un filamento de sección constante (el `MinThickness`), no la cinta real.

<details><summary>Diagnóstico original (histórico)</summary>

### CAUSA MÁS PROBABLE DEL ANCHO (hallada 2026-08-03) — `ComputeWidth` inline en el pin `Width`
**El log descartó todo lo demás.** `MVPAL h=3/4/5 selW=0/1/2` y `MVDRAW w=0.5 / 2.5 / 6.0` → la selección funciona, el alcance funciona (se tocan las 9 celdas), y `BrushWidth` **llega correcto** al arranque del trazo. Y `WriteRing` sí usa `W` para el semi-ancho (`side × W×0.5`). Sin embargo no se ve ningún cambio.

**Sospecha #1 (revisar PRIMERO):** en `BP_BrushTool.UpdateStroke` el ancho se pasa así:
```
(Class|BPDrawCanvas|AddPoint _c :NewLoc _f :ControllerUp _up
   :Width (CallFunction|ComputeWidth :DT _dt)   ← ⚠ función IMPURA inline como argumento de datos
   :Calm (Variables|Default|GetCalmVal))
```
🔴 **Es exactamente el mismo fallo que ya nos pasó con `UpdateTouch`** (ver sección de Fase 4.3): **una función con pines de exec NO se puede inlinear como expresión de datos** — el DSL la acepta, compila, y deja el pin destino **sin conectar en su valor por defecto** (0). Si `Width` llega 0, todos los trazos salen del mismo grosor mínimo (el piso lo da `MinThickness`), **sin importar lo que elijas** — que es exactamente el síntoma.
- **Verificar:** `get_node_infos` del nodo `AddPoint` en `UpdateStroke` → mirar si el pin `Width` tiene `connected_pins` o quedó en `"0.0"`.
- **Fix:** llamar `ComputeWidth` como **statement** y bindear su resultado, o —más simple, ya que hoy sólo devuelve `BrushWidth`— **borrar `ComputeWidth`** y pasar `:Width (Variables|Default|GetBrushWidth)` directo (un getter puro, seguro). El ancho ya no depende de la presión (se descartó), así que la función no aporta nada.
- **Nota:** el mismo patrón puede estar mordiendo en otros lados; revisar cualquier `(CallFunction|X ...)` usado como argumento.

**Sospecha #2 (si la #1 no era):** el taper geométrico congelado. `RefreshTail` sólo refresca los últimos `TailRefresh`=6 anillos; con `MinDist=0.5` y decimación angular a 2°, esos 6 anillos abarcan **menos** que `TaperOut`=3 cm → los anillos salen de la ventana con `fOut` a medio camino y **se congelan afinados**. 🔑 **El proyecto de Tilt Brush hace el taper en el MATERIAL, no en la geometría** (ver `references/movement-3d-drawing.md`), justamente porque así no existe esta clase de bug. Fuerte candidato a migrar.

## 🐛 FIX PENDIENTE (2026-07-30) — la fila de GROSOR (y quizá la de PINCEL) no responde
> ⚠️ **Parcialmente RESUELTO por el log (2026-08-03):** el alcance NO era el problema (se tocan las 9 celdas: `h=0..8` en el log) y la selección funciona (`selW` cambia 0/1/2). Queda sólo el "por qué no se ve", con las dos sospechas de arriba. La hipótesis original de pose/alcance quedó **descartada**.

</details>
**Síntoma en visor:** la fila de **color** (fila 0) funciona perfecto (tocar cambia el color del trazo siguiente). Las filas de **grosor** (fila 1) y **pincel** (fila 2) "no hacen nada". El pincel es esperable (los 3 materiales son iguales hasta 4.4); el **grosor debería cambiar el ancho y no lo hace**.

**🔑 Diagnóstico que decide todo (hacer primero):** al tocar una celda de grosor/pincel, **¿se ENCIENDE (highlight)?**
- **Si NO se enciende** → es un problema de **alcance/pose físico**, NO de lógica. La fila 0 (color, `X=+4`) queda accesible pero las filas 1-2 (`X=0`, `X=-4`) quedan anguladas/detrás por la pose de `AttachToHand` (offset `loc (7,0,5)` + `rot pitch=-55`, que fue un valor de arranque a ojo). **Hipótesis principal.** Fix: ajustar la pose del panel y/o la orientación de la grilla para que las 9 celdas miren al usuario y la punta llegue a todas. Probar el offset/rotación moviendo `AttachToHand` (o exponer la relative-transform como vars instance-editable para tunear sin recompilar, como se hizo con el mesh del sensor en `BP_CalibProbe`).
- **Si SÍ se enciende** (highlight ok) pero el ancho no cambia → bug de **aplicación del ancho**. Revisar la cadena: `UpdateTouch` setea `SelWidth` → `Highlight` setea `CurWidth = PaletteWidths[SelWidth]` → `CheckPalette` sincroniza `BrushWidth = pal.CurWidth` → `ComputeWidth` devuelve `BrushWidth` → `AddPoint.Width` → `WriteRing`/`PtWidth`. Verificar con un `PrintString` de `CurWidth`/`BrushWidth` dónde se corta. (La lógica se revisó y **parece correcta**, por eso la pose es la sospecha #1.)

**Otras cosas a chequear de paso:**
- `CellRadius=2.0` con spacing 4 cm → las zonas de toque de celdas vecinas se tocan justo en el punto medio; si hay selección errática, bajar a ~1.6.
- Confirmar que el highlight de grosor/pincel efectivamente prende (mismo `Highlight`, índices `3+SelWidth` / `6+SelBrush` — revisados, ok).

**🔴 Aplicar ANTES de 4.4.** Si es la pose (hipótesis #1), la fila de PINCEL también está inalcanzable → no se podría **seleccionar ni testear** los brushes B/C que crea 4.4. Arreglar el alcance primero desbloquea probar todo.

## Falta 4.4
Los 3 materiales de pincel de verdad — hoy los 3 son `M_Brush_Light`.

## Componentes
- `DefaultSceneRoot`
- **`Panel`** — cubo chato 14×14×0.3 cm en `z=-0.4` (fondo).
- **`Cell0`..`Cell8`** — 9 cubos chatos 3×3×0.3 cm en grilla 3×3, spacing 4 cm. Índice = fila×3 + col.
  - **Fila 0 (color):** Cell0/1/2 · **Fila 1 (grosor):** Cell3/4/5 · **Fila 2 (pincel):** Cell6/7/8.
  - Local: fila 0 en `X=+4`, fila 1 `X=0`, fila 2 `X=-4`; col 0 `Y=-4`, col 1 `Y=0`, col 2 `Y=+4`.

## Material de celda
`Materials/M_PaletteCell` — **Unlit · Opaque**. Emissive = `CellColor` (VectorParam) × `Glow` (ScalarParam). Base `Glow=0.35` (celda tenue), seleccionada `Glow=1.6` (encendida). Cada celda recibe un MID vía `SetVectorParameterValueonMaterials`/`SetScalarParameterValueonMaterials`.

## Registro de variables
- **`Cells`** (StaticMeshComponent[]) — las 9 celdas, poblado en `BuildCells` (índice = getter Cell0..8). Permite loopear init/highlight.
- `LeftGrip`/`RightGrip`/`AttachedController` (MotionControllerComponent) — grips del pawn + al que se pegó.
- `bAttached` (bool).
- `SelColor`/`SelWidth`/`SelBrush` (int, default 0/1/0) — opción elegida por fila.
- `LastCell` (int, -1) — para el debounce de toque (Fase 4.2).
- `CellRadius` (float, 2.0) — radio de proximidad de toque (Fase 4.2).
- **Contenido (Class Defaults, editable en un lugar):**
  - `CellColors` (LinearColor[9]) — color de display de cada celda. [0,1,2]=los 3 colores de dibujo (verde/ámbar/cian), [3-8]=neutros. 🔑 `GetColor()` (Fase 4.3) devuelve `CellColors[SelColor]`.
  - `PaletteWidths` (float[3]) — `0.6 / 1.3 / 2.6` cm.
  - `PaletteBrushes` (MaterialInterface[3]) — hoy los 3 = `M_Brush_Light` (placeholder hasta 4.4: B "Velo" y C).

## Funciones
- **`BuildCells()`** — llena `Cells` con Cell0..8 (BeginPlay).
- **`InitCells()`** — loop 0..8: asigna `M_PaletteCell` a cada celda + setea `CellColor` desde `CellColors[i]`. Llama `Highlight`.
- **`Highlight()`** — loop pone `Glow=0.35` en todas; luego `1.6` en la celda seleccionada de cada fila (`SelColor`, `3+SelWidth`, `6+SelBrush`).
- **`AcquireControllers()`** — castea el pawn `BP_VRPawn_SC`, cachea grips (patrón del pincel/sensor).
- **`AttachToHand(bBrushIsRight)`** — la llama el pincel. Se adjunta al grip **contrario** (`select bBrushIsRight → LeftGrip : RightGrip`), `AttachActorToComponent` SnapToTarget, + offset relativo `loc (7,0,5)` `rot pitch=-55` (pose de arranque, **el usuario la afina en el editor** como hizo con el mesh del sensor).

## EventGraph
- `EventBeginPlay`: `bAttached=false`, `LastCell=-1`, `BuildCells`, `AcquireControllers`, `InitCells`.

## Cómo la usa el pincel (`BP_BrushTool.DoAttach`)
Al agarrar el pincel: spawnea `BP_BrushPalette`, guarda `PaletteRef`, llama `PaletteRef.AttachToHand(bIsRightHand)`. Así la paleta cae en la mano contraria a la que tomó el pincel.

## Selección por toque (Fase 4.2, 2026-07-30)
- **`UpdateTouch(TipWorld)`** (void; guarda el resultado en `bOver`): loop 0..8, `HoverCell` = la celda cuya distancia punta↔`GetWorldLocation` < `CellRadius` (las celdas no se solapan → a lo sumo una matchea). On **ENTER** (`HoverCell != -1 AND != LastCell`): setea la fila (`<3`→SelColor, `<6`→SelWidth, else→SelBrush) + `HapticPulse` + `Highlight`. `LastCell = HoverCell`. Al final `bOver = dist(punta, Panel) < PanelRadius`.
- **`HapticPulse`** (custom event, en EventGraph): `SetHapticsByValue` on → `Delay 0.06` → off, en la mano de la paleta (`bPaletteRight`, branch por mano porque el literal `"Right"`/`"Left"` va directo al pin enum; un `select` de strings NO coerce). 🔴 Se hizo custom event (no función) para poder meter el `Delay`.
- **`bOver`** (bool) — lo lee el pincel. **`PanelRadius`** (float, 7) — radio de "sobre la paleta" para suprimir el dibujo. **`HoverCell`** (int) — celda tocada este frame. **`bPaletteRight`** (bool) — de qué mano quedó la paleta (para el háptico), seteado en `AttachToHand`.
- **El pincel** (`BP_BrushTool.CheckPalette`, llamado en `UpdateStroke` cada frame): `PaletteRef.UpdateTouch(tip)` + `bOverPalette = PaletteRef.bOver`. El dibujo se gatea con `(bTrigHeld AND NOT bOverPalette)` → no se dibuja sobre la paleta. 🔴 **Gotcha:** una función con exec (`UpdateTouch`) **no se puede inlinear como argumento** de un Set; hay que llamarla como statement y leer el resultado de una variable con un getter cross-clase (`Class|BPBrushPalette|GetOver`).

## El pincel usa la selección (Fase 4.3, 2026-07-30)
- **La paleta expone la selección como variables** `CurColor` (LinearColor) · `CurWidth` (float) · `CurBrushMat` (MaterialInterface), actualizadas al final de **`Highlight`** (que corre en cada selección y en el init) desde `CellColors[SelColor]` / `PaletteWidths[SelWidth]` / `PaletteBrushes[SelBrush]`. 🔴 Se usan **variables + getters cross-clase**, no funciones con return — el bind de un return cross-clase falla en el DSL ("produced no output pin").
- **El pincel sincroniza cada frame** (`CheckPalette`, cuando `PaletteRef` es válido): `BrushColor = pal.CurColor`, `BrushWidth = pal.CurWidth`, `BrushMat = pal.CurBrushMat`. Como corre siempre, en `BeginStroke` las 3 ya están frescas. Null-safe: sólo lee dentro del `IsValid`.
- **El canvas recibe el material:** `BP_DrawCanvas.BeginStroke` ganó el param **`Mat`** → var `StrokeMat` → `OpenSection` lo usa en `SetMaterial` (cirugía: se reemplazó el pin del literal `M_Brush_Light` por un getter de `StrokeMat`; el `read` de `OpenSection` es lossy en `CreateMeshSection` así que NO se reescribió). `ContinueSection` hereda `StrokeMat` (misma sección del trazo).
- 🔴 **Gotcha:** reescribir `write_graph_dsl` sobre una FUNCIÓN existente (no vacía) deja el cuerpo viejo como huérfanos (pasó con `CheckPalette`: 4 nodos exec sueltos). Verificar con vitalidad dirigida y borrar. (El `auto_layout.py` ahora reporta huérfanos de paso.)

## TODO
- [ ] **Probar 4.1+4.2+4.3 en visor:** tocar color → trazo de ese color; tocar grosor → ese ancho; tocar pincel → (mismo look hasta 4.4). No se dibuja sobre la paleta.
- [ ] **Probar 4.1+4.2 en visor:** paleta aparece en la mano contraria; tocar una celda la enciende + vibra (una por fila); no se puede dibujar sobre la paleta. Afinar el offset de `AttachToHand` y `CellRadius`/`PanelRadius`.
- [ ] **4.3 El pincel lee la paleta:** en `BeginStroke` color=`GetColor()`, `BrushWidth`=`GetWidth()`, material=`GetBrushMat()`. 🔴 `BP_DrawCanvas.BeginStroke` gana un param `Material` → `StrokeMat` → `OpenSection`/`ContinueSection` lo usan en `SetMaterial` (hoy hardcodean `M_Brush_Light`). El pincel llama `UpdateTouch` cada frame y gatea el trazo con `bSuppressDraw`.
- [ ] **4.4 Los 3 materiales:** B `M_Brush_Veil` (translúcido aditivo), C tercero. `PaletteBrushes` apunta a los 3.
- [ ] Visuales de las filas grosor/pincel (hoy neutras): puntos de tamaño / muestras de pincel. Marks hijos escalados por grosor.
- [ ] Polish: aparición por giro de muñeca, preview vivo.

## Session log
- **2026-07-30 (4.2)** — Selección por toque: `UpdateTouch` (hit-test + selección + suppress), `HapticPulse` (evento con Delay, branch por mano), `Highlight`, `bOver`/`PanelRadius`/`HoverCell`/`bPaletteRight`. En el pincel: `CheckPalette` + `bOverPalette` gateando el dibujo en `UpdateStroke`. Compila limpio, ordenado. **Sin probar en visor.**
- **2026-07-30** — Creada (Fase 4.1). 10 componentes (Panel + 9 celdas), `M_PaletteCell`, 15 variables, 6 funciones, BeginPlay. El pincel la spawnea y la manda a la mano contraria en `DoAttach`. Compila limpio, grafos ordenados con `auto_layout.py`. **Sin probar en visor.**
