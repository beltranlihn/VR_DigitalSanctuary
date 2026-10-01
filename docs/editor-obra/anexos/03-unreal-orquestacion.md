> Anexo de la auditoría del 2026-10-01 (informe: cómo está orquestada la obra en Unreal). Lo que manda es [PLAN-EDITOR-OBRA-2026-10-01.md](../PLAN-EDITOR-OBRA-2026-10-01.md); donde este anexo lo contradiga, gana el plan.

# Auditoría: cómo está orquestada la obra en Unreal (insumo para el editor web)

**Raíz:** `C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/`. Abreviaturas:
- `TRK/` = `.claude/skills/unreal-vr/blueprints/`
- `DUMP` = `VR_Test/Saved/ClaudeScripts/obra/dump/obra_all_now.txt`. Es el volcado DSL de los 122 grafos de `BP_Obra_SC`, hecho a las 13:07 del 2026-10-01. Después se agregaron funciones (HandTick, GhostTick…), así que los conteos son aproximados.

---

## 1. Cómo se representa el tiempo hoy

**En Unreal no hay una línea de tiempo.** Hay tres máquinas de estados anidadas. Avanzan por condición ("gate") o por cortafuegos, y cada una tiene su propio reloj.

1. **La Obra (`BP_Obra_SC`)**
   - Lleva dos relojes: `T` (de la etapa) y `PT` (de la fase), multiplicados por `Speed` (`TRK/BP_Obra_SC.md:16`).
   - `RunObra` es un `switch` de fases 0-15 más la 16, que es el aviso (`TRK/BP_Obra_SC.md:18-35`, `:85-86`; `DUMP:438-545`).
   - Recorrido de cada etapa: fase 0 (velo y título) → 4 (Alma recibe) → 5 (instrucciones) → 6 (mecánica) → 7 (salida) → 8 (carga) → 2 (cierre del velo, `AdvanceStage`).
   - Recorrido del cierre: 9 (Hall) → 10-15 (final a negro, regreso, resultados, salida, créditos, fundido y reinicio).
   - Alrededor de `RunObra` corren **orquestadores paralelos** que se llaman desde `TickAll`/`FinalFlow`: `FlowVeil`, `FlowDisc`, `IntroTitle`, `AmbPick`/`AmbTick`, `FlowFinal`, `FlowBye`, `FlowShare` (estados `ShareSt` 0-8), `FlowConst`, `StageCues`/`CueAttract`/`CueDraw`, `HallRingStep` (`HRState` 0-4), `HandsTick`, `GhostTick`, `SimCut` y `ObraDbgFF` (`TRK/BP_Obra_SC.md:70-90`, `:224`, `:248-258`, `:309-332`).
   - Muchos de ellos escriben "lo que gana en ese cuadro" según el orden de llamada (`:70`, `:248`). El orden de ejecución también es parte de la coreografía.
2. **El Hall (`BP_HallDirector_SC`)**
   - Usa `Mode` (1 Intro, 2 Return, 3 Exit) y `Step` 0-30.
   - Avanza cuando `StepTime ≥ StepDur` y `bGate` es verdadero. Cada paso es un `case` que fija `StepDur`, `bGate` y `bWaitWalk` (`TRK/BP_HallDirector_SC.md:33-34`, `:42-45`).
   - La Obra lo llama (`HallIntro/Return/Exit`) y lee sus banderas (`bHallDone`, `bHudBorn`, `DoorW/E`…) (`:15-27`).
3. **Cada etapa**
   - Contrato `StageIntro/StageBegin/StageOutro` + `bStageDone` (`docs/PLAN-NOCHE-2026-09-30.md:38-48`; `DUMP:487-501`).
   - Por dentro, cada una tiene su propio reloj: ciclos del pacer, latidos, `StageDuration`, tinta, SAVE.

**Entorno de ensayo, que duplica la coreografía:**
- `BP_StageRunner_SC` repite las fases 0-7 en cada nivel de test (`TRK/BP_StageRunner_SC.md:13-23`).
- `BP_HallRunner_SC` repite la fase 9 en Test_Hall (`TRK/BP_HallRunner_SC.md:7-17`).
- Los dos llevan **sus propios literales**. El título del runner revela de 1 a 5,5 s y sale de 9 a 12,5 s (`TRK/BP_StageRunner_SC.md:16`). En la Obra revela de 0,5 a 1,8 s y sale de 4,6 a 5,6 s (`DUMP` RunObra, `TRK/BP_Obra_SC.md:226`). **Ya divergieron.**

**DebugStart.** Es un índice de puntos de entrada: −1 normal, 1-9 Hall por pasos, 10-54 etapa×subfase, 60-64 final (`TRK/BP_Obra_SC.md:129-160`, `:219`). Llega a cada punto cumpliendo las condiciones de salida fase por fase (`ObraDbgFF`). Es, de hecho, el **vocabulario de anclas** que ya existe en Unreal.

### Qué es dato y qué está cableado

| Es DATO (perilla editable en instancia o CDO) | Está CABLEADO en los grafos |
|---|---|
| `AlmaTime`, `InstrTime`, `OutroTime`, `ChargeTimes[5]`, `ResultsTime`, `CreditsTime`, `DiscTime`, `ExploreT`, `ShareFW`, `SwimTime`, `AwayTime`, `SimStageMax`, `AmbClips[9]`, `AmbVolumes[9]`, `AmbFadeIn/Out`, `CTops/CHors`, `StageCols`, perillas `Hall - Anillo` (`TRK/BP_Obra_SC.md:47-48`, `:91`, `:200`, `:259`, `:293`) | **El orden** de fases y de etapas (`switch`, índice de celda) |
| Hall: `JourneyTime…ExitTime`, `IntroHold`, ~18 `Pace*`, `FW_*`, `BellHold`, `VOAir` (`TRK/BP_HallDirector_SC.md:51-58`, `:98-111`) | La secuencia de los 31 pasos del Hall y qué VO va en cada paso (índice en el `.dsl`, `:57`) |
| Posiciones: TargetPoints `TP_sc<K>_*`, `TP_hall_*`, `final_*`, flechas `Stop*`, actores colocados (`Final_*`, `Timbre`, `Sensor`, `TituloInicio`, `CreditStar_*`) | Cortafuegos de la mecánica **180/120/240 s** (`DUMP:501`); título 0,5/1,8/4,6/5,6/5,7; Alma a T 5,8; cierre 69→71,5 (`DUMP:473-481`) |
| Duración de la VO: `SoundBase.GetDuration` → `VODur` (`TRK/BP_Obra_SC.md:211`) | **Qué VO** suena en cada momento: rutas de asset literales en `AlmaSpeak/AlmaCharge/FlowBye/StageCues/CueAttract/CueDraw` (`DUMP:1978-2050`) |
| | Las condiciones y los tiempos de las pistas de VO de Attracting y Drawing: 20 s/75 s, 15/40/60 s, tinta > 0,3/0,6 (`DUMP:1978-2021`) |
| | Qué ambiente va en qué fase (`AmbPick`: índices literales, `DUMP:1145`) |
| | Velo de la última carga 9,5→11,5 y `ReadCharge` 5,6+C (`TRK/BP_Obra_SC.md:267-270`); llenado de la carga 2,47→8,47 (literal en ChargeFx, `:217`) |
| | Visibilidad de las manos por fase y etapa (`:228`), mapa fantasma→bandera (`:313-329`), estados de `FlowShare` |

En el volcado hay **536 literales de punto flotante en 122 grafos**. Los grafos que más concentran son: RunObra 57, ResultsFade 56, IntroTitle 50, FlowVeil 42, ResultsShow 23 y HallRingStep 20. No todos son tiempos (hay geometría y escalas), pero los tiempos narrativos más visibles están ahí.

---

## 2. Inventario de parámetros autorables por parte de la obra

Notación de "dónde vive": **I** = instancia en el nivel · **CDO** = valor por defecto de la clase · **TP** = TargetPoint · **A** = actor colocado (transform) · **L** = literal en un grafo.

**Inicio (aviso, título, viaje)**
- `BP_Obra_SC`: `bDisclaimer` (bool, I), `DiscTime` 9 (float, CDO), `bSimulated` (bool, I), `DebugStart`/`DebugSoul` (int, I), `Speed` (float, I) (`TRK/BP_Obra_SC.md:86`, `:227`).
- Texto del aviso: entra 0,5→2 y sale 3,5→4,8 (L en `BP_Disclaimer_SC.DiscStep`, `:218`).
- Título: aparece a 2,5 s, revela 3→6,5, la bajada 5→7,5, los logos 6→8,6 y sale 10→12,5 (L, **duplicado** en `IntroTitle` y `HRTitle`). La pose es `TituloInicio` (A) (`TRK/BP_IntroTitle_SC.md`, Grafos).
- Velo del Hall: negro hasta PT 3,5 y abre de 3,5 a 5,5 (L, `FlowVeil`). `HallIntro` arranca a PT 3 (L).
- Ambientes: `AmbClips`/`AmbVolumes` (array, I). Qué clip suena y cuándo: L.

**Hall** (instancia `HallDirector` en Test_Hall)
- Tiempos y ritmo: `JourneyTime` 26, `EnterTime` 7, `OutTime` 8, `ReturnTime` 8, `ExitTime` 7, `AccelTime`, `BrakeTime`, `IntroHold` 12, `VOAir` 0,5, `Pace*` (float, I+CDO).
- Cortafuegos: `FW_Bell` 25, `FW_Tool` 20, `FW_Choose` 25, `BellHold` 3.
- Puertas y baldosas: `DoorOpenDeg`, `DoorTime`, `DoorWarm`/`DoorCold`, `Tile*`.
- Paradas: `StopStart…StopExit` (ArrowComponent, transform).
- Puntos: `TP_hall_alma_center/side/exit`, `TP_hall_pawn`, `TP_hall_soul_present` (TP).
- Objetos: `Timbre`, `Sensor`, `HallSoul_0..4` (A + `Size` y colores) (`docs/MAPA-DE-AJUSTES.md:51-73`).
- En la Obra: `HallRingFit`, `HallRingSpeedIn`, `HallHomeSpeed`, `HallHomeDelay` (I, `TRK/BP_Obra_SC.md:259`).

**Común a las 5 etapas** (K 0-4)
- `TP_sc<K>_alma_in/_alma_side/_charge/_title`: TP en el nivel de test; la escala del de carga es el tamaño del anillo.
- `StageRunner`: `InstrTime`, `OutroTime`, `CTop`, `CHor` (I, la Obra los copia en `ReadRunners`).
- En la Obra: `ChargeTimes`, `StageCols`, `CavNames` (arrays, I).
- Cortafuegos 180/120/240 (L), título y velo (L), VO de bienvenida, de carga y de despedida (L), `bGhostsOn` (I).
- ⚠ `AlmaTime` del runner **ya no lo usa la Obra**: ahora es `VODur + 3` (`TRK/BP_Obra_SC.md:296`). `docs/MAPA-DE-AJUSTES.md:136` sigue diciendo "La Obra lo copia": **la documentación está desactualizada.**

**Etapas, perillas internas de tiempo** (todas I salvo donde se indica; `docs/MAPA-DE-AJUSTES.md`)
- **Entering**: `ExploreTime` 12, `CountTime` 3, `ToolDelay` 0,8 (`Entering_Stage`); pacer 4-3-4-3, `Cycles` 5, `LeadIn`/`LeadOut` (`:176-178`). Los sonidos del pacer están hechos para 4-3-4-3.
- **Recognizing**: `StageBeats` 38, `OrbitAtBeat` 19, `BackupAfter` 8 (`HeartManager`); `OrbitTime` 60, `EntryTime` 2,5 (`HeartScape`) (`:228-233`).
- **Loving**: `StageDuration` 80, `IntroTime`/`OutroTime` 3 (`LovingCell`); `TravelSpeed`/`TravelEase` (`:277-279`).
- **Attracting**: `FinalPasses` 2, `ExitTime` 1,5, `IntroOrbsAt` 1,2, `IntroToolsAt` 2,4; `HoldDuration` 3; `StepBPM` 90 (**solo CDO**, `:340`); pistas de VO (L en la Obra).
- **Surrounding**: `InkMeters` 30, `HoldTime` 5, `SpinSpeed`, `IntroTime` 0,8, `ContractPaletteDelay` 0,6; pistas de VO (L en la Obra) (`:375-377`).

**Final** (`L_SoulCharger_Obra`)
- `ReturnWait`, `ResultsTime` 150 (cortafuegos), `ExploreT` 25, `ShareFW` 30, `SwimTime` 4, `AwayTime` 3, `CreditsTime` 60, `ResAlmaLeft`, `ResAlmaScale`, `SketchSpeed` (I).
- Estados de `FlowShare` (+1,8, PT 8, etc.): L, en parte derivados de la VO (`TRK/BP_Obra_SC.md:213`).
- Poses: `Final_Cuadro`, `Final_Boton*`, `AnilloCarga`, `Final_AlmaPez`, `Final_Creditos` (A); `final_sketch/alma/fish_door/fish_away` (TP); `CreditStar_00..29` (A) (`docs/MAPA-DE-AJUSTES.md:75-89`).

**Look por etapa** (cielos, paletas, materiales): cientos de perillas I en los actores de cada nivel de test (`docs/MAPA-DE-AJUSTES.md:163-371`). Son de autor visual, no de montaje.

---

## 3. El puente actual Unreal ↔ web

**Exporta** `VR_Test/Saved/ClaudeScripts/obra/ensayo_export.py`:
- De los 5 niveles de test (`:10`): PlayerStart (posición y yaw), los 4 TP `sc<K>_*` relativos al PlayerStart (fwd/side/up/yaw/scale, `:51-59`) y 8 propiedades del `StageRunner` (`AlmaTime, InstrTime, OutroTime, ChargeTime, TimeoutS, EyeRef, CTop, CHor`, `:43`) → `ensayo_export.json` (`:62`).
- ⚠ Para leer, **cambia el nivel abierto del editor compartido** (`load_level` en `:37` y vuelta a la Obra en `:61`).

**Genera** `gen_ensayo_js.py`:
- **No está en el repo**: vive en el scratchpad de otra sesión (`…/Temp/claude/…/4e6c96c4-…/scratchpad/obra/gen_ensayo_js.py`).
- Tiene **cableados** `VOLEN` y `BASE` (`:5-7`).
- Escribe `web/prototipo-narrativo/ensayo.js`, que pisa `top/hor` y `CHARGE_T`, y expone `ensDelta` y `ensPause` (`:21-27`). La web aplica **desplazamientos** respecto de la base, no posiciones absolutas.

**Direcciones**
- Unreal → web: **manual**, en 3 pasos (script MCP → Python → publicar).
- Web → Unreal: **100 % manual**. Hay que cambiar la instancia o el TP a mano y re-exportar (`TRK/BP_StageRunner_SC.md:39`; `docs/MAPA-DE-AJUSTES.md:146`).
- Lo que se edita en la web (`edits`, `locators`, `look` en la base del artifact, `timeline.js:920`) **no llega nunca a Unreal**.

**Qué se pierde**
- Todo el Hall, todo el final, las variables de la Obra (`ChargeTimes`, `AmbClips`, `DiscTime`, `ExploreT`…), las perillas internas de cada etapa y todos los literales.
- Exporta valores del runner que la Obra no usa (`TimeoutS`, `ChargeTime`, `AlmaTime`).

**Deriva ya medible:**

| Dato | Web | Unreal |
|---|---|---|
| Largo de la VO de bienvenida (`gen_ensayo_js.py:5`) | 8,54 / 9,33 / 5,15 / 7,43 / 13,05 | mezcla final 8,50 / **3,67** / 7,77 / **4,27** / 10,27 (`VR_Test/Saved/ClaudeScripts/vo_final/duraciones_mezcla.txt`) |
| Cortafuegos de Recognizing (`ensayo.js:126`) | 150 | 180 (`DUMP:501`) |
| Aviso | `DISCLAIMER` dur 20 (`guion.js:87`) | `DiscTime` 9 |
| Cortafuegos del sensor | `G_SENSOR` 15 (`guion.js:175`) | `FW_Tool` 20 |
| Cortafuegos de la elección | `G_CHOOSE` 30 (`guion.js:189`) | `FW_Choose` 25 |
| Título de etapa | — | runner 1→5,5 / 9→12,5 contra Obra 0,5→1,8 / 4,6→5,6 |

---

## 4. Capacidades de integración disponibles

**Plugins** (`VR_Test/VR_Test.uproject`)

| Plugin | Estado | Nota |
|---|---|---|
| OSC | ✅ activo | Corre en el APK. El servidor del BioHub escucha en el **puerto 10000** (`TRK/BP_BioHub.md:165`, `:180`). Se puede extender con direcciones propias, siempre un solo servidor por puerto (`:135`). |
| ModelContextProtocol + EditorToolset | ✅ activo | Arrastran a ToolsetRegistry, que depende de **PythonScriptPlugin** y EditorScriptingUtilities (`Engine/Plugins/Experimental/ToolsetRegistry/ToolsetRegistry.uplugin:30-35`). Python de editor existe (UncookedOnly), **solo en el editor**. |
| RemoteControl / WebRemoteControl | ❌ no activo | Aunque se active, WebRemoteControl solo corre en **Win64/Mac/Linux** (`RemoteControl.uplugin:44-47`): jamás en el Quest. Útil como mucho para leer PIE en el editor. |
| JsonBlueprintUtilities | ❌ no activo | Módulo Runtime **sin restricción de plataforma**, en beta (`JsonBlueprintUtilities.uplugin`). Permitiría leer un JSON en el Quest. |

**El MCP permite** (`.claude/skills/unreal-vr/references/toolsets.md`):
- Leer y escribir propiedades de instancias y CDO (`:163`) y transforms de actores (`:159`).
- `DataTableTools`: create, import_file, get/set_rows con JSON (`:208-210`); `DataAssetTools.create` (`:213`); `CurveTable` y `StringTable` (`:216-219`).
- PIE y logs (`:222`, `:251`) y scripts por lotes (`:254`). El sandbox no tiene `exec` ni `math` (`TRK/BP_StageRunner_SC.md:44`) y solo escribe en `Saved/` con extensiones limitadas (`toolsets.md:243`).
- **Precedente de datos cocinados escritos desde el editor:** `BP_GhostTake_SC` (PrimaryDataAsset con arrays) + 10 `DA_Ghost_*` en el APK (`TRK/BP_GhostPlayer_SC.md:53-54`).

**Restricciones duras**
- **No se pueden crear structs ni enums por MCP** (`references/gotchas.md:305`, `:670`). Una DataTable necesita un struct de fila hecho a mano (2 clics + campos).
- **Gotcha 402:** cambiar la estructura de un BP con instancia colocada puede perder el actor (`gotchas.md:2586`). Hay que tocar `BP_Obra_SC` con la Obra cerrada (`TRK/BP_Obra_SC.md:98`).
- Las variables nuevas instance-editable **nacen en 0** en la instancia del nivel abierto (`gotchas.md:1438`; caso real en `TRK/BP_Obra_SC.md:299`). Con el nivel cerrado, la instancia toma el CDO (`gotchas.md:2694`). El CDO no se propaga a las instancias colocadas (`gotchas.md:317`; `TRK/BP_HallDirector_SC.md:111`).
- **Editor único compartido, con cola** (`docs/PLAN-NOCHE-2026-09-30.md:65-66`). Un `execute_tool_script` que falla dispara un Undo que se lleva trabajo (`CLAUDE.md` §2.b).
- `.uasset` y `.umap` son binarios y no se mergean.
- **Quest standalone:** sin editor en runtime, todo dato tiene que ir cocinado. Se empaqueta en Development.
- El empaque de la Obra usa `.ini` **temporales**: lo commiteado tiene `GameDefaultMap` = Test_Sequencer (`VR_Test/Config/DefaultEngine.ini:7`) y la Obra no está en `MapsToCook` (`DefaultGame.ini:131-137`).
  - Un JSON suelto exigiría tocar el staging.
  - Un DataTable o DataAsset **referenciado en firme** por `BP_Obra_SC` se cocina solo.
- El artifact vive en claude.ai: no hay que asumir que pueda hablar con `localhost:8000` (no verificado; lo más probable es que no). El puente realista es una sesión de Claude (ArtifactData ↔ archivos ↔ MCP en su turno de la cola).

---

## 5. Propuesta de costura: una "partitura" de datos

### Principios
1. **La fuente canónica es un texto en el repo** (`score.json`: diffeable y mergeable). La base del artifact es la copia de trabajo del montajista; el asset de Unreal es el compilado.
2. **Cada campo tiene un dueño:**

| Familia | Dueño | En la web |
|---|---|---|
| Tiempos, desfases, cortafuegos, qué asset suena en qué pista | la **partitura** (web) | editable |
| Posiciones (TP, actores) y look | **Unreal** | solo lectura; propuestas que se aplican en la cola |
| Umbrales de las mecánicas (zonas, tinta…) | Unreal | no se exponen al montajista |

3. **Anclas comunes en los dos lados.** Las marcas las emite Unreal: entrada a cada fase `S<K>.P<n>`, `HALL.<paso>`, eventos del contrato (`INTRO`/`BEGIN`/`DONE`/`OUTRO`) y gates (`BELL`, `TAKE`, `CHOOSE`, `SAVE`, `INK>x`). Es el mismo modelo de ancla `['KEY','end',2]` y de `gate(fw)` que ya tiene la web (`guion.js:1-7`, `:132-189`), y casi el mismo índice que `DebugStart`.
4. **Regla de Beltrán:** solo la VO dura lo que su audio. La web nunca autora duraciones de VO: las importa de `duraciones_mezcla.txt` y Unreal las mide con `GetDuration`.

### Las cuatro capas
- **A. Perillas de partitura (la costura mínima).**
  - Promover a variables (categoría "Partitura") solo los ~30 literales que le importan al montajista: título y velo, entrada de Alma, cortafuegos 180/120/240, cierre 69→71,5, velo de la última carga, tiempos de `FlowShare`/`FlowConst` y del aviso.
  - Una función `ScoreApply()` al comienzo de `StartObra` las copia desde el asset. Si `ScoreAsset` está vacío no hace nada (es reversible).
  - **No se reescribe `RunObra`.** Es cirugía nodo por nodo: el literal pasa a un getter (regla de oro 2 de `CLAUDE.md`).
  - Formato, dos opciones:
    - (a) **DataTable** con struct de fila `F_ScoreKnob {Value, Note}` creado a mano una vez por Beltrán. Ventaja: el import y el *Reimport* desde el JSON los hace él solo en el editor, sin Claude y sin cola.
    - (b) **PrimaryDataAsset** con `Map<Name,float>` (precedente `DA_Ghost`). Sin paso humano, pero escrito solo por MCP; la escritura de Map por `set_properties` está **sin verificar**.
- **B. Pista de cues: `BP_ScoreCues_SC`, un actor observador.**
  - Lee `Obra.Phase/Stage/PT` y `Hall.Mode/Step` cada cuadro, detecta flancos y emite marcas. Dispara cues con forma `{ancla, offset, acción, asset, objetivo}`. El director no lo conoce.
  - Es el patrón ya probado de `BP_HallTitle_SC`, `BP_HallGlow_SC` y `BP_HallAmbience_SC` (`TRK/BP_HallDirector_SC.md:76`, `:92`; `gotchas.md:2871`), así que no agrega variables a `BP_Obra_SC`.
  - Vocabulario cerrado de acciones: VO (`Alma.SayClip` / 2D), SFX en un actor o tag (con `ATT_Objeto_SC`), cambio de ambiente, mostrar u ocultar por tag, rampa de un parámetro escalar, fantasma Play/Stop y subtítulo.
  - Esto le da al montajista "cuándo aparece cada cosa" sin tocar grafos. Las condiciones de las mecánicas (`InkUsed`, `Phase` del secuenciador) se exponen como gates con nombre, no como lógica editable.
- **C. Puesta en escena** (TP y actores). Queda en los `.umap`. Se cosecha hacia la web en solo lectura. Si el montajista mueve algo en la vista 3D, se genera un *parche* (`set_actor_transform`) que aplica una sesión en su turno de la cola, después de ver el diff.
- **D. Lazo de sincronía**, semi-automático, una skill por dirección:
  - `score_pull`: base del artifact → `score.json`, con diff.
  - `score_push`: `score.json` → asset de partitura (DataTableTools o Reimport de Beltrán).
  - `unreal_harvest`: Unreal → web. Ampliar `ensayo_export` al Hall, al final, a las perillas de la Obra y a las duraciones de VO, y **leer los subniveles ya cargados del persistente** en vez de cambiar de nivel (`docs/MAPA-DE-AJUSTES.md:22-27`).
  - **Traza real:** `BP_ScoreCues_SC` loguea `SCORE|t|marca`. Esa traza se importa desde el PIE o desde logcat del APK y se superpone en el timeline como "lo que pasó de verdad" (los gates dependen del usuario).
  - **"Probar desde aquí":** cue de la web → código `DebugStart` → PIE.
  - Opcional, más adelante: (1) recarga en caliente en el APK Development con JsonBlueprintUtilities + `adb push score.json` (permite iterar tiempos en el visor sin reempaquetar); (2) transporte (play o ir a un punto) por OSC con un relevo local WebSocket→UDP sobre el servidor del BioHub.

### Cuánto hay que tocar de `BP_Obra_SC`
- Capa A: ~30 variables nuevas, en **una sola tanda estructural** con la Obra cerrada; después, cirugía de ~30-60 pines en ~8 grafos (RunObra, FlowVeil, IntroTitle, FlowShare, FlowConst, FlowFinal, StageTimes, ChargeStart) + `ScoreApply`.
- Capa B: cero cambios en la Obra para *agregar* cues. Para *migrar* las pistas existentes, un bool `bLegacyCues` por familia que corta `StageCues`/`CueAttract`/`CueDraw`/`AmbPick` en su llamada (cirugía de un nodo cada uno).
- `HallRunner` y `StageRunner` tienen que leer la **misma** partitura (o desaparecer como coreógrafos) para cortar la divergencia del ensayo.

### Orden incremental (cada paso con el mismo resultado que el anterior)
0. **Congelar.** Cosechar todos los valores actuales a `score.json v0` (son los valores FINALES aprobados) y grabar una traza de PIE de referencia.
1. Sincronía de solo lectura Unreal → web: la web adopta los valores de Unreal y desaparece la deriva de la §3.
2. `BP_ScoreCues_SC` colocado **sin cues**, solo emitiendo marcas. Control: su traza tiene que coincidir con los `OBRA:` del log.
3. Migrar una familia (ambientes o pistas de VO de Attracting/Drawing) con valores idénticos y A/B con `bLegacyCues`. Comparar trazas.
4. Capa A (perillas + `ScoreApply`). Verificar instancia contra CDO contra partitura, valor por valor.
5. Abrir la escritura web → partitura → Unreal, con diff y aprobación de Beltrán.
6. Opcionales: JSON en caliente en el visor y transporte por OSC.

---

## 6. Riesgos concretos

1. **Dos fuentes de verdad ya divergen** (§3). Sin dueño por campo y sin hash/`savedAt` en el lazo, el editor va a mostrar una obra que no es la del APK.
2. **El editor compartido.** `ensayo_export.py` cambia el nivel abierto (`:37`, `:61`) y puede pisar la sesión de otro; un script que falla dispara un Undo. Toda escritura tiene que pasar por la cola, contar actores antes y después y guardar con rutas explícitas.
3. **Gotcha 402, nacer en cero, CDO ≠ instancia.** Las perillas nuevas pueden dejar a Alma en tamaño 0 o romper la ameba del Hall (ya pasó: `TRK/BP_Obra_SC.md:299`). Verificar leyendo la instancia, no el CDO.
4. **Los valores de los niveles de test son FINALES.** Cualquier migración tiene que dar exactamente los mismos valores, y eso se demuestra con el diff de trazas, no por inspección.
5. **El tiempo nominal no es el real.** `FinalFlow` corre ~1,5 veces por cuadro y el reloj de `FlowBye` va 1,5× (`TRK/BP_Obra_SC.md:207`). Además, `HandsTick` y los orquestadores dependen del orden de llamada. El timeline tiene que mostrar las trazas medidas, no solo la suma de duraciones.
6. **El tiempo no es lineal.** Gates y cortafuegos dependen del usuario, y `bSimulated`/`SimCut` cambian la duración de las etapas (`TRK/BP_Obra_SC.md:123`). El editor tiene que modelar gates; si "aplana" la obra, miente.
7. **Structs fuera del alcance del MCP.** La opción DataTable requiere un paso manual de Beltrán. Si no se hace, queda el DataAsset con Map, que todavía no está verificado.
8. **Empaque con `.ini` temporales.** Un JSON en runtime exige staging nuevo en config compartida. El asset con referencia firme no tiene ese problema.
9. **Costo en el Quest.** `BP_ScoreCues_SC` tiene que limitarse a detectar flancos (nada de buscar en Map cada cuadro dentro de `RunObra`) y respetar `Dt ≤ 1/30` y "nada arranca en el cuadro en que se enciende la celda" (`docs/PLAN-NOCHE-2026-09-30.md:102-108`).
10. **Coreografía triplicada** (Obra, StageRunner, HallRunner). Mientras no lean la partitura, lo que se ensaya no es lo que se juega.
11. **Sin versión ni dueño.** `gen_ensayo_js.py` está en el scratchpad de otra sesión (si esa sesión se borra, se pierde) y `docs/MAPA-DE-AJUSTES.md:136` ya está desactualizado.
12. **Banderas de depuración.** La Obra quedó guardada con `DebugStart` 3 (`TRK/BP_Obra_SC.md:347`). Si el editor expone banderas de debug, `score_push` nunca debe escribirlas y el checklist del APK tiene que verificarlas.
13. **Precisión de este informe.** Los conteos de literales salen del volcado de las 13:07; `BP_Obra_SC` cambió después (fantasmas, zurdos, manos). Antes de la capa A hay que re-volcar.