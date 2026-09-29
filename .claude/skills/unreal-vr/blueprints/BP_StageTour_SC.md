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
5. **RunTick** (s = tiempo local de la etapa):
   - 0 → 7,5 s: el velo se abre (1,5→7,5) · título Reveal 0,5→4,5, Out 7→10,5 · `EarlyPlace` coloca el título frente a la cámara (solo yaw) mientras s < 0,4.
   - 7,5 s: `MarkStart` ("TOUR: transicion N->N+1 fin" si N>0, luego "TOUR: etapa N NOMBRE inicio").
   - 67,5 s: `MarkEnd` + `SleepStage` (el TourSleep va ANTES de ocultar, porque Breath necesita ≥4 s para salir).
   - 67,5 → 73,5 s: el velo se cierra mientras sus colores pasan de la paleta de la etapa i a la i+1.
   - 73,5 s: `AdvanceStage` = `HideSpawned` (oculta los actores nuevos desde la entrada: esferas del secuenciador, trazos del dibujo…) + `SetCell(i,false)` + `EnterStage(i+1)`. Después de la última: "TOUR: fin", velo opaco y a los 3 s `OpenLevel Test_Recorrido` (loop).
6. **EnterStage(k)**: SetCell(k,true) → teleport del pawn al PlayerStart de la celda → material del título `TitleMIs[k]` → `WakeStage(k)` → foto de actores (`Known`).
7. **SetCell / SetActorOn**: prende o apaga una celda **sin tocar el `bHidden` original** de cada actor: `SetVisibleInSceneCaptureOnly` en cada PrimitiveComponent (el BP no puede LEER el bHidden de otro actor, así que no se usa SetActorHiddenInGame para no revivir lo que nació oculto), colisión (`InitColl` guardado) y `SetPaused` de los AudioComponent. El **Tick solo se apaga en la celda 2 (Mind)**: las demás etapas manejan su Tick con su contrato (Breath lo pidió explícitamente).
8. **WakeStage / SleepStage**: switch por etapa → `BP_BreathStage_SC.TourWake/Sleep`, `BP_HeartManager_SC.TourWake/Sleep`, Mind = `WakeMind` (bFakeEEG / bFakeSignal + FakePeriod 60; sin sleep), `BP_Sequencer_SC.TourWake/Sleep` (una sola vez por corrida: repetido re-siembra 68 esferas), `BP_TBDirector_NC.TourWake/Sleep`.

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
| **`Speed`** (instance editable, 1) | acelera el recorrido para probar en PIE (8 = recorrido completo en ~1 min). **Dejar en 1 al guardar.** |

## Componentes
- `Veil`: esfera del motor, escala 0,6 (30 cm), `M_TourVeil_SC` (Unlit, Translucent, TwoSided, DisableDepthTest), sort 100. Parámetros Amount / CTop / CHor.
- `Title`: plano del motor, escala (4,1,1), relativa (300,0,0), rotación **(0, 90, 90)** (verificada: se lee derecho mirando +X), `MI_TourTitle_<NOMBRE>` (M_TourTitle_SC, mismo modo + sort 110). Parámetros Reveal / Out / Fade / Bias / C0..C3 / Tex (máscara R nítida, G difusa; SRGB off, TC_Masks).

## Verificado (2026-09-29, PIE a Speed 8)
- Las 5 etapas cargan, 47 actores en celdas, marcas completas y en orden, TourWake/TourSleep de cada etapa en el log, director TB `bAwake` en la etapa 5, loop por OpenLevel. 0 Accessed None, 0 Script Msg (después de arreglar LovingCell, ver abajo).
- Falta en visor: el velo en estéreo, el título, los FPS por etapa (script `scripts/quest_recorrido_perf.ps1`).

## Trampas que salieron acá
- **Editor minimizado = PIE congelado**: con la ventana de Unreal minimizada el mundo de PIE no tickea (ni Tick ni timers), aunque BeginPlay corre. Restaurar la ventana (`ShowWindow(h, 9)` por PowerShell) lo arregla.
- **`bind` no es asignación** (otra vez): en `Step`, `dt = now - LastTime` se evaluaba después de `SetLastTime(now)` → dt = 0 siempre. Llamar a TickAll ANTES de guardar LastTime.
- `get_node_type_pins` sobre `Class|Actor|GetActorHiddenInGame` no existe: el bHidden de otro actor no se puede leer desde BP → por eso `SetVisibleInSceneCaptureOnly`.
- El world de un LoadLevelInstance con override conserva su nombre original (`/Game/UEDPIE_0_SCTour2.Test_Fluid:PersistentLevel...`) y el paquete toma el override → se clasifica por las dos cosas.
- `BP_LovingCell_SC.LifeApply`: un Multiply `2.0 × B` con B desconectado dividía por 0 miles de veces por cuadro. Arreglado con B = 1e9 (mismo look, Asin≈0). El arreglo de diseño (conectar `_r1c`) queda para Beltrán.
