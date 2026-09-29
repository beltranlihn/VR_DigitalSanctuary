# BP_StageTour_SC — el recorrido de las 5 etapas (Test_Recorrido)

`/Game/SoulCharger/Tour/BP_StageTour_SC` · nivel `/Game/Test_Recorrido` (duplicado de Test_Fluid, sin sus actores; GameMode BP_XRGameMode → BP_VRPawn_SC).
Creado 2026-09-29 (noche) por la sesión "Narrativa" para el APK de prueba de Beltrán.

## Qué hace
1. **Begin** (BeginPlay): velo opaco con los colores de la etapa 1, carga los 5 niveles de prueba con `LoadLevelInstance(byName)` en su **posición original** (offset 0, para que los materiales con posición de mundo se vean igual) con `OptionalLevelNameOverride = "SCTour<k>"`, y arranca un **timer en bucle de 0,011 s** que llama a `Step`.
   - Orden: 0 ENTERING = /Game/Test_Entering · 1 RECOGNIZING = /Game/Test_Heart · 2 LOVING = /Game/Test_Fluid · 3 ATTRACTING = /Game/Test_Sequencer · 4 SURROUNDING = /Game/NeuralCanvas/Maps/L_TBTest_SC.
   - El actor tiene tag **TOUR**: todas las etapas con contrato nacen dormidas.
2. **Step → TickAll(Dt)**: pega la esfera del velo a la cámara (`GetPlayerCameraManager`, con IsValid). Mientras no arranca → `BootTick`; después → `RunTick(Dt × Speed)`.
3. **BootTick**: `CheckVis` (los 5 `IsLevelVisible`) → cuando los 5 están visibles durante 1,5 s → `StartTour`.
4. **StartTour**: `PrimeMind` (FakePeriod 60) → `Classify` (reparte actores en celdas por el nombre de su mundo/paquete: `LevelNames[k]` o `SCTour<k>`; guarda el PlayerStart de cada celda) → apaga las 5 celdas → `EnterStage(0)`.
5. **RunTick** (s = tiempo local de la etapa; v3+, 2026-09-29 mediodía):
   - 0 → 9 s: la etapa se enciende OCULTA detrás del velo (`ShowIfDue`: cola desde s ≥ 0,5) · el velo abre 3→9 · título Reveal 1→5,5, Out 9→12,5, visible s < 13 · `EarlyPlace` → `PlaceTitle` mientras s < 0,4.
   - 9 s: `MarkStart` ("TOUR: transicion N->N+1 fin" si N>0, luego "TOUR: etapa N NOMBRE inicio").
   - 69 s: `MarkEnd` + `SetVariant` + `SleepStage` (el TourSleep va ANTES de ocultar, porque Breath necesita ≥4 s para salir).
   - 69 → 75 s: el velo se cierra mientras sus colores pasan de la paleta de la etapa i a la i+1.
   - 75 s: `AdvanceStage` = `HideSpawned` + **`QueueCell(i,false)`** + `EnterStage(i+1)`. Después de la última: "TOUR: fin", velo opaco y a los 3 s `OpenLevel Test_Recorrido` (loop).
6. **EnterStage(k)**: teleport del pawn al PlayerStart de la celda + el velo salta con él (sin cuadro negro) → material del título `TitleMIs[k]` → `WakeStage(k)` → foto de actores (`Known`).
7. **Encendido/apagado de celdas** — sin tocar el `bHidden` original de cada actor: `SetVisibleInSceneCaptureOnly` en cada PrimitiveComponent (el BP no puede LEER el bHidden de otro actor), colisión (`InitColl`) y `SetPaused` de los AudioComponent. El **Tick solo se apaga en la celda 2 (Mind)**.
   - 🔴 **Durante el recorrido va por COLA, nunca de golpe** (`QueueCell(K,On)` llena `QC/QCOn` con los componentes y `QA/QAOn/QAColl/QATick` con los actores; `StepQueue`, llamada cada cuadro desde `ShowIfDue`, procesa **`QBatch` = 8 componentes + 1 actor por cuadro** y vacía la cola al terminar). Motivo medido en la Quest: prender una celda entera en un cuadro costaba ~30 ms → el compositor perdía 5-9 cuadros seguidos → con la cabeza en movimiento se ve un **corte negro** en los bordes (reproyección). `SetCell` directo queda solo para el arranque (`StartTour`).
8. **PlaceTitle**: el título se fija en el MUNDO, no según hacia dónde mira el usuario: XY del PlayerStart de la etapa, Z de la cámara, yaw = `StartYaw[k]` (el frente de la etapa, como los elementos interactivos). Pedido de Beltrán 2026-09-29.
9. **WakeStage / SleepStage**: switch por etapa → `BP_BreathStage_SC.TourWake/Sleep`, `BP_HeartManager_SC.TourWake/Sleep`, Mind = `WakeMind` (bFakeEEG / bFakeSignal + FakePeriod 60; sin sleep), `BP_Sequencer_SC.TourWake/Sleep` (una sola vez por corrida: repetido re-siembra 68 esferas), `BP_TBDirector_NC.TourWake/Sleep`.

## Variables
| Variable | Rol |
|---|---|
| `LevelPaths` / `LevelNames` / `StageNames` | niveles a cargar, nombre de su mundo para clasificar, nombre del título y del log |
| `LS` | los 5 LevelStreamingDynamic |
| `CellActors` / `CellIdx` / `InitColl` | actores de cada celda + su colisión original |
| `StartLoc` / `StartYaw` | PlayerStart de cada celda (teleport) |
| `CTops` / `CHors` | colores del velo por etapa (lineales, de `palettes.json` del prototipo web) |
| `TitleMIs` | las 5 MI del título |
| `Stage` / `Phase` (0 abre, 1 etapa, 2 cierra, 3 fin) / `T` | máquina de estados |
| `Booted` / `BootT` / `AllVis` | arranque |
| `Known` | actores que existían al entrar a la etapa (para `HideSpawned`) |
| `LastTime` | para el Dt del timer |
| `QC` `QCOn` `QA` `QAOn` `QAColl` `QATick` `QCI` `QAI` · **`QBatch`** (8) | la cola de encendido/apagado de celdas (ver §7) |
| **`Speed`** (instance editable, 1) | acelera el recorrido para probar en PIE (8 = recorrido completo en ~1 min). **Dejar en 1 al guardar.** |

## Componentes
- `Veil`: esfera del motor, escala 0,6 (30 cm), `M_TourVeil_SC` (Unlit, Translucent, TwoSided, DisableDepthTest), sort 100. Parámetros Amount / CTop / CHor.
- `Title`: plano del motor, escala (4,1,1), relativa (300,0,0), rotación **(0, 90, 90)** (verificada: se lee derecho mirando +X), `MI_TourTitle_<NOMBRE>` (M_TourTitle_SC, mismo modo + sort 110). Parámetros Reveal / Out / Fade / Bias / C0..C3 / Tex (máscara R nítida, G difusa; SRGB off, TC_Masks).

## Verificado (2026-09-29, PIE a Speed 8)
- Las 5 etapas cargan, 47 actores en celdas, marcas completas y en orden, TourWake/TourSleep de cada etapa en el log, director TB `bAwake` en la etapa 5, loop por OpenLevel. 0 Accessed None, 0 Script Msg (después de arreglar LovingCell, ver abajo).
- Falta en visor: el velo en estéreo, el título, los FPS por etapa (script `scripts/quest_recorrido_perf.ps1`).

## Cortes negros al cambiar de etapa — cómo se midieron (2026-09-29)
- Instrumento: el `Stale2/5/10/max` de la línea `VrApi FPS=` del logcat (máx. cuadros seguidos sin cuadro nuevo). Toda racha ≥5 con la cabeza moviéndose = borde negro visible.
- `-ExecCmds="stat dumphitches"` (en `UECommandLine.txt` del proyecto en el device) solo ve el game thread: cazó el spawn de 68 esferas de ATTRACTING (105 ms, ver `BP_Sequencer_SC.SpawnDomeStep`). `csvprofile frames=N` da GT/RT/RHI por cuadro: el cuadro del encendido de celda = 30 ms.
- `r.TextureStreaming 0` bajó la racha de 7-9 a 5 (y deja las texturas siempre a resolución completa): va en el `[SystemSettings]` TEMPORAL del empaquetado del recorrido.

### v5 (2026-09-29 tarde)
- **`QBatch` = 2** en el CDO. Se midió 8 / 2 / 1 → 2 es el mejor. Se puede probar en el device sin reempaquetar con `-ExecCmds="set BP_StageTour_SC_C QBatch N"`.
- **`BlobTick(K)`** (se llama al final de `EnterStage`): el gusano `BP_BlobChain_SC` **solo tickea en la etapa 4**. Antes tickeaba ~1,4 ms por cuadro durante todo el recorrido.
- **`HideOne` apaga también el Tick** de lo que esconde. Las 68 esferas seguían tickeando ~6 ms por cuadro después de ATTRACTING. Con esto, **la transición 4→5 quedó en 0 cuadros perdidos**.
- `StepQueue` imprime `Q: <componente>` por cada pieza que prende o apaga (diagnóstico; sacarlo cuando se cierre el tema).
- **Diagnóstico:** `-trace=cpu,frame,bookmark,log -tracefile=x.utrace` en el device, y después `UnrealInsights.exe -OpenTraceFile=… -NoUI -AutoQuit -ExecOnAnalysisCompleteCmd="TimingInsights.ExportTimingEvents out.csv -columns=… -threads=… -startTime=… -endTime=…"`. El "Self" de World Tick en `stat dumphitches` es **`xrWaitFrame`** (la espera del runtime), no trabajo.
- **Queda (medido):** 1→2 = 8, 2→3 = 9, 3→4 = 7. En 1→2 el CPU está limpio: el único cuadro lento es una espera de 27 ms en `xrWaitFrame`, justo después de prenderse la membrana del latido. La célula de LOVING cuesta 6-8 ms de Tick por cuadro (`Simulate` + 48 `SetColorParameterValueOnMaterials`): es optimización propia de esa etapa.

## Trampas que salieron acá
- **Editor minimizado = PIE congelado**: con la ventana de Unreal minimizada el mundo de PIE no tickea (ni Tick ni timers), aunque BeginPlay corre. Restaurar la ventana (`ShowWindow(h, 9)` por PowerShell) lo arregla.
- **`bind` no es asignación** (otra vez): en `Step`, `dt = now - LastTime` se evaluaba después de `SetLastTime(now)` → dt = 0 siempre. Llamar a TickAll ANTES de guardar LastTime.
- `get_node_type_pins` sobre `Class|Actor|GetActorHiddenInGame` no existe: el bHidden de otro actor no se puede leer desde BP → por eso `SetVisibleInSceneCaptureOnly`.
- El world de un LoadLevelInstance con override conserva su nombre original (`/Game/UEDPIE_0_SCTour2.Test_Fluid:PersistentLevel...`) y el paquete toma el override → se clasifica por las dos cosas.
- `BP_LovingCell_SC.LifeApply`: un Multiply `2.0 × B` con B desconectado dividía por 0 miles de veces por cuadro. Arreglado con B = 1e9 (mismo look, Asin≈0). El arreglo de diseño (conectar `_r1c`) queda para Beltrán.
