> Anexo de la auditoría de herramientas del 2026-10-01 (revisión: tiempo e interacción). Lo que manda es [PLAN-EDITOR-OBRA-2026-10-01.md](../PLAN-EDITOR-OBRA-2026-10-01.md).

# Auditoría de las herramientas de tiempo e interacción del editor de la obra

Comparé la maqueta y el plan del editor con la evidencia de Unreal: trackers, volcados DSL, `MAPA-DE-AJUSTES` y guion. Lo hice todo en solo lectura y sin tocar el MCP `unreal`.

**Resumen:** el ejemplo central de la maqueta, la espera `G_BREATH`, describe algo que Unreal no hace. Entering no espera al usuario. Además, el cortafuegos de las etapas 3 y 4 no sigue el mismo camino que el final real. Los dos puntos se corrigen en la maqueta o el plan, o se agregan en Unreal, antes de F1.

Raíz: `C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/`. Abreviaturas:

| Abreviatura | Archivo |
|---|---|
| `MOCK` | `web/editor-obra/mockup/src-body.html` |
| `PLAN` | `docs/editor-obra/PLAN-EDITOR-OBRA-2026-10-01.md` |
| `TRK/` | `.claude/skills/unreal-vr/blueprints/` |
| `DUMP` | `VR_Test/Saved/ClaudeScripts/obra/dump/obra_all_now.txt` (volcado de las 13:07) |
| `HDUMP` | `VR_Test/Saved/ClaudeScripts/obra/dump/hall.txt` (volcado de las 07:52) |
| `GUION` | `docs/GUION-V5-2026-09-29.md` |
| `MAPA` | `docs/MAPA-DE-AJUSTES.md` |
| `MIX` | `VR_Test/Saved/ClaudeScripts/vo_final/duraciones_mezcla.txt` |
| `WEB/` | `web/prototipo-narrativo/` |

## Veredicto por herramienta

| Herramienta | Estado | Evidencia (archivo:línea) | Qué cambiar |
|---|---|---|---|
| Bloque Espera (`G_BREATH`, rayado, cola y cortafuegos) | **Corregir** | `MOCK:259,266,278`. Unreal: "El pacer arranca respire o no" (`TRK/BP_BreathStage_SC.md:58`); Entering dura unos 88 s fijos desde `StageBegin` (`:88`). Los valores 6/25/+12 salen de `WEB/guion.js:369,371` | **Maqueta:** Entering no tiene espera que bloquee. `bZone` es una *condición sin bloqueo*: solo apaga el fantasma y decide si suena VO_11h. Cambiar el ejemplo por una espera real (timbre, sensor o elección del Hall). |
| Frase de condición "touches zone belly for 1 s" | **Corregir** | `bZone` = zona geométrica **y** orientación del sensor, instantáneo (`TRK/BP_BreathRig_SC.md:59`). `bBreathing` = zona ∧ quietud ∧ amplitud, con retardo de entrada 1,5 s y de salida 0,2 s (`TRK/BP_BreathManager_SC.md:25,44,78`) | **Plan y maqueta:** "1 s" no existe. Usar dos condiciones: `breath.zone` (instantánea) y `breath.on` (1,5 s). El pulso y el zumbido de 0,25 cuelgan de `breath.on`, no de `zone` (`TRK/BP_BreathManager_SC.md:52-53,79`; hoy en `MOCK:289`). |
| Expected 6 s con candado | **Corregir** | `MOCK:461` (`{lock:1}`). No existe ninguna variable "esperado" en Unreal | **Maqueta:** marcarlo como supuesto de simulación, sin candado. El candado significa "valor aprobado en el nivel de test" (`MOCK:429`). |
| Help after 12 s | **Corregir** | Entering: VO_11h llega `HelpAfter` 4 s **después de VO_11b**, solo si `!Rig.bZone` (`TRK/BP_BreathStage_SC.md:103,105`). Heart: VO_16h a `HintAfter` 15 s sin pulsos ni mano (`TRK/BP_HeartManager_SC.md:175`). Attracting: VO_27h a PT 20 sin esferas (`DUMP:1994`). Drawing: VO_32h a PT 15 con tinta < 0,05 (`DUMP:2007`) | **Plan:** la ayuda necesita **ancla propia** (inicio de la espera o fin de una VO) y **condición propia**, distinta de la de Done. |
| Ayuda en el Hall | **Falta en Unreal** | VO_01h/03h pendientes (`TRK/BP_HallDirector_SC.md:7`); VO_01h figura sin uso (`TRK/BP_Obra_SC.md:216`). Hoy la única ayuda es el fantasma, desde el primer cuadro (`TRK/BP_Obra_SC.md:313-319`). El guion pide VO a 8 s (`GUION:128-129`) | **Decisión de Beltrán:** cablear las VO de ayuda, o aceptar el fantasma como ayuda. Si no, la regla "toda espera tiene ayuda" (`PLAN:75`) marca las 3 esperas del Hall. |
| Timeout 25 s | **Corregir** | El cortafuegos de la etapa es 180/120/240 (`DUMP:501`). Hall: `FW_Bell` 25, `FW_Tool` 20, `FW_Choose` 25, medidos desde el inicio del paso, VO incluida (`HDUMP:419-425,460`; `TRK/BP_HallDirector_SC.md:56`). El timbre se carga solo en `BellHold` 3 s más (`HDUMP:425`): efectivo ≈ 28 s | **Maqueta:** el timeout es por espera y sale de la cosecha. Mostrar el "relleno" del timbre (+`BellHold`). |
| On timeout "same as the real ending" | **Corregir / Falta en Unreal** | Es cierto en el Hall (`HDUMP:425,443-444,460-466`) y en SHARE (`DUMP:1552-1553`). **Falso en las etapas:** el cortafuegos de la fase 6 llama `CallOutro` directo (`DUMP:501-505`). Attracting sale sin SAVE ni coda (`TRK/BP_Sequencer_SC.md:516-517`); Drawing, sin presentación (`TRK/BP_TBStroke.md:2486-2487`). El guion pide "SAVE forzado" (`GUION:135-136,140`) | **Maqueta:** campo con valores reales por espera. **Unreal:** forzar SAVE en el cortafuegos de Attracting y Surrounding (decisión de Beltrán). |
| If early, corta la voz en 0,3 s | **Riesgo** | Existe **solo** en timbre, sensor y elección del Hall: `StepDur = StepTime + 0,3` + `FadeVoice(0,3)` (`HDUMP:436-441,454-459,479-484`). En las etapas la voz no se corta: se espera a Alma libre (Heart `TRK/BP_HeartManager_SC.md:175`) o se **salta** a los 8 s (Loving `TRK/BP_LovingCell_SC.md:67-69`). La web usa 0,5 s y corta toda voz (`WEB/timeline.js:329-337`) | **Plan:** por espera, apagado por defecto en las etapas. Alinear el motor web a 0,3. |
| Salidas Done / Late / Timeout | **Corregir** | "Late" no es un estado en Unreal (`docs/editor-obra/anexos/09-critica.md:61`). Las salidas de `G_BREATH` (`MOCK:464`) no existen: VO_11b suena al empezar la exploración, haya zona o no (`TRK/BP_BreathStage_SC.md:103`) | **Maqueta:** Done / Help (fue la VO `_h`) / Timeout, con lo que de verdad cuelga de cada una. |
| Marcas (`PLAN:249`) y `OnMark` (`PLAN:268`) | **Corregir** | Los números de fase son internos y se renumeraron por el DSL (`TRK/BP_Obra_SC.md:52`). El orden real es 0→4→5→6→7→8→2; las fases 1 y 3 son legado (`DUMP:478-485`). `VO.end` no existe en 2D, y `FadeVoice` no dispara `OnVOFinished` (`TRK/BP_Alma_SC.md:140,171`). Hay ~19 lugares donde se fija la fase (`DUMP:122,432,475-538,694,753,765,819,838,861,883,1357,1698,1832`) | **Plan:** usar marcas semánticas (lista abajo). Emitirlas con un detector de flanco al final de `TickAll` en lugar de 19 cirugías, y para el Hall con un solo nodo en `HallTickSteps` (`HDUMP:55`). |
| Usuario simulado (Fast / Typical / Slow / Idle) | **Corregir** | `MOCK:253` aplica un solo número a todas las esperas. Los gestos tienen mínimos: `BellHold` 3 s, retardo de entrada de 1,5 s, SAVE 3 s (`TRK/BP_Sequencer_SC.md:64`). No existe el modo `bSimulated` (`DUMP:1349-1353,1552-1553,1727`) | **Maqueta:** el perfil elige un percentil de **cada** espera con sus valores. Agregar el perfil "APK autoplay (`bSimulated`)". |
| Total contra 15:00 | **Corregir** | `totalTxt = 1029 + d − 6` solo mueve **una** espera (`MOCK:315`). Unreal: Heart ~103 s (`TRK/BP_HeartManager_SC.md:167`), Loving 60 (`TRK/BP_LovingCell_SC.md:73`), Entering ~88 s. Los cortafuegos de Unreal son mayores que los del guion (240 contra 120): el "peor caso ~16:30" (`GUION:90`) ya no vale | **Plan:** sumar las duraciones reales por etapa y mostrar Típico y Peor caso. Peor caso = cada cortafuegos real. |
| Ramas SHARE / DON'T | **Corregir** | `Shared` es un **estado que persiste** hasta la fase 14 (`DUMP:1648-1652`). Duraciones: SHARE 1,4 + 4 + 3 = 8,4 s, DON'T 2,6 s (`DUMP:1586`). El valor por defecto depende de `bSimulated` (`DUMP:1553`). También existe `DebugShare` (`DUMP:1550`) | **Plan:** rama = variable de estado con lectores aguas abajo, no una bifurcación local. El valor por defecto es configurable por build. |
| Bucle del pacer (×5, 4-3-4-3) | **Corregir** | El pacer arranca en `InhaleCueAt` 3,48 s **dentro** de VO_12c, con `LeadIn` superpuesto a la cuenta (`TRK/BP_BreathStage_SC.md:94-97`). Hay `LeadOut` 3 s (`TRK/BP_Pacer_SC.md:99`). Suenan pads por fase + un pluck por segundo, no `FX_BREATHCOUNT` (`TRK/BP_Pacer_SC.md:121-124`). Los sonidos están horneados a 4-3-4-3 (`:86`) | **Maqueta:** ancla en "inhale" de VO_12c; agregar LeadOut y VO_12f1/f2 del primer ciclo. La perilla Rhythm avisa que hay que regenerar los pads. |
| Bucle del fantasma | **Corregir (menor)** | Vuelta ≈ `LoopEnd` 4,9 s / `PlayRate` 1,25 + `LoopGap` 0,4 ≈ 4,3 s (`TRK/BP_GhostPlayer_SC.md:33,43`). Arranca en la fase 6 (`StageBegin`) y para en la primera acción (`TRK/BP_Obra_SC.md:321-328`). La maqueta usa vueltas de 5 s (`MOCK:382`) | **Maqueta:** leer el período de la toma y las perillas; anclar a `S<K>.BEGIN` y terminar con la condición de "primera acción". |
| Regla VO = dura su audio | **OK la regla / Corregir los datos** | `ObraSay`/`ObraVO2D` → `VODur = GetDuration` (`DUMP:1866-1876`). La maqueta tiene largos viejos: VO_10 7,4 contra 8,50, VO_11b 6,3 contra 7,45, VO_12c 2,4 contra 3,56 (`MOCK:264-268` contra `MIX:16-21`) | **Maqueta:** duraciones desde `MIX`. **Plan:** el modelo de duración necesita también `max(autoral, VO+x)`, desfase negativo (VO_36b: `VODur − 1,2`, `DUMP:1506`), "retener" y "saltar". |
| `AlmaTime = VO + 3` y Lead-in 1,5 | **Verificar en vivo** | El volcado dice `VODur + 3,5` (`DUMP:977`), luego `StAlma` y `max(VODur + 2,5)` (`DUMP:1459-1468`). El tracker dice "+3, sin `StAlma`" (`TRK/BP_Obra_SC.md:296`). El lead-in 1,5 es solo de `AlmaSpeak` (`DUMP:968`) | **Maqueta:** Alma = 1,5 de entrada + VO + 1,5 de cola. El lead-in va por punto de llamada, no por VO (`MOCK:470`). |
| Tiempos por timeline | **OK con matices** | Sonidos alineados a mano: golpe de `Charge1` y `ChargeFinal` (`TRK/BP_Obra_SC.md:217`); "inhale" de VO_12c (`TRK/BP_BreathStage_SC.md:97`) | **Plan:** representar "puntos de sincronía dentro de un audio" y avisar si un tiempo los descuadra. |

## Hallazgos importantes

1. **El ejemplo `G_BREATH` describe un mecanismo que no existe.** En Unreal, Entering corre por reloj:
   - `StageIntro` → herramienta a 0,8 s → VO_11 a 1,8 s → `StageBegin` → exploración de 12 s → cuenta → 5 ciclos (`TRK/BP_BreathStage_SC.md:57-59,103`).
   - El usuario solo decide si suena VO_11h y cuándo para el fantasma (`TRK/BP_Obra_SC.md:325`). VO_11h, si suena, puede atrasar VO_12, porque "la cuenta espera" (`TRK/BP_BreathStage_SC.md:103`).
   - **Corrección:** en la maqueta, mover `breath.zone` a una pista de condición sin rayado ni cortafuegos, y anclar todo a `S0.BEGIN`. Para ilustrar la espera, usar el timbre del Hall.

2. **El cortafuegos de las etapas no es "el mismo camino que el final real".**
   - En la fase 6, al vencer 180/120/240 s, se llama `CallOutro` directo (`DUMP:501-505`, log `por fin propio = false`). Lo mismo pasa con `SimCut` a 90 s (`DUMP:1727-1729`).
   - Attracting cierra sin SAVE ni las 2 pasadas (`TRK/BP_Sequencer_SC.md:516-517`). Drawing cierra sin exhibir el dibujo (`TRK/BP_TBStroke.md:2486`). Recognizing puede cortar la vuelta.
   - **Corrección:** el editor muestra "Timeout → StageOutro (sin coda)" en esas etapas. En Unreal falta el "SAVE forzado" del guion (`GUION:135-136`).

3. **La documentación de Unreal se contradice en los cortafuegos y las perillas.** Si la cosecha lee documentos en vez de la instancia, importa números falsos.

   | Documento | Dice | Unreal |
   |---|---|---|
   | `MAPA:401`, `TRK/BP_Obra_SC.md:26`, `TRK/BP_HeartManager_SC.md:130` | Recognizing 150 s | 180 s (`DUMP:501`) |
   | `MAPA:228` | `StageBeats` 38 | 19 pulsos con `BeatDiv` 2 (`TRK/BP_HeartManager_SC.md:170`) |
   | `MAPA:233` | `BackupAfter` 8 s | 30 s (`:173`) |
   | `MAPA:277` | Loving 80 s | 60 s |
   | `MAPA:178` | `CountTime` 3 | 3,6 (`TRK/BP_BreathStage_SC.md:95`) |
   | `MAPA:136` | "la Obra copia `AlmaTime`" | ya no la copia (anexo 03:79) |

   **Corrección (plan, §3.3):** `harvest_score.py` lee siempre la instancia; ningún valor se toma de `MAPA`.

4. **El usuario simulado y el total no modelan la obra.**
   - El tiempo que depende del usuario está en: las 3 esperas del Hall, el arranque de Heart (mano, o respaldo a 30 s), el juego de Attracting (SAVE o 240), el de Surrounding (tinta 30 m o SAVE o 240) y SHARE (30).
   - Entering y Loving no varían.
   - "Idle = 25 s en todo" es falso: el peor caso suma 28 + 20 + 25 + ~126 (Heart con respaldo, estimado) + 240 + 240 + 30, muy por encima de 15:00.
   - **Corrección:** una tabla de perfiles por espera; los mínimos físicos (3 s del timbre, 1,5 s de retardo, 3 s de SAVE) no se pueden bajar; perfil `bSimulated` (cortafuegos del Hall, Heart con respaldo, Attracting y Surrounding a 90 s, SHARE).

5. **Marcas: lista real que la Obra puede emitir.** Reemplaza la de `PLAN:249`.
   - **Arranque:** `OBRA.BOOT` (`StartObra`, `DUMP:183-189`) · `DISC.START`/`DISC.END` (fase 16, `DUMP:1357,1342-1344`) · `HALL.START` (fase 9, `DUMP:694`).
   - **Hall:**
     - `HALL.<1|2|3>.<paso>` (`HDUMP:55`; el paso 16 está vacío);
     - `HALL.BELL.done|fw` · `HALL.SENSOR.done|fw.R|L` · `HALL.SOUL.done|fw` (flanco de `bBellLive`/`bSensorLive`/`bPickLive`, comparando `StepTime` con `FW_*`);
     - `HALL.VOICECUT` · `HALL.HUD` (+ `HALL.EEG` 1 s después, `DUMP:715-722`) · `HALL.EXITEARLY` (`DUMP:724`) · `HALL.DONE`.
   - **Cada etapa K:**
     - `S<K>.OPEN` (0) → `S<K>.ALMA` (4) → `S<K>.INTRO` (5) → `S<K>.BEGIN` (6);
     - `S<K>.OUTRO.done|fw|sim` (7) → `S<K>.CHARGE` (8) → `S<K>.BYE` (2) → `S<K>.END` (`AdvanceStage`, `DUMP:353-362`);
     - `S<K>.INSTR_READY` solo en K 3-4 (`DUMP:2029`).
   - **Mecánicas:**
     - `MECH.0.zone|on|cycle.n|done`;
     - `MECH.1.zone|pulse.n|backup|orbit|done`;
     - `MECH.2.vo22|vo23` (o `.skip`);
     - `MECH.3.first|placed.n|save|done`;
     - `MECH.4.ink>x|empty|save|done`.
   - **Voz y ayuda:** `HELP.<vo_h>` (cuando arranca la VO de ayuda) · `VO.<id>.start` con la duración como dato · `VO.<id>.cut`. No `VO.end` ni `GATE.late`.
   - **Final:** `FINAL.BLACK` (10) · `FINAL.RETURN` (11) · `FINAL.RESULTS` (12) · `SHARE.<0|2|4|5|6|7|8|9>` (los estados reales; se saltan el 1 y el 3, `DUMP:1502,1507`) · `SHARE.PICK.yes|no|fw` · `FINAL.EXIT` (13) · `FINAL.CREDITS` (14) · `FINAL.FADE` (15) · `OBRA.RESTART`.
   - **Sobre `DebugStart`:** solo cubre 0/4/5/6/7 por etapa, el 8 en la etapa 4 y 8 pasos del Hall (`DUMP:1790,1905-1923`). "Casi coinciden" (`PLAN:249`) es optimista.

6. **El reloj nominal no es el real.**
   - La Obra corre con un timer de 0,011 s (`DUMP:265`) cuyo `Dt` se recorta a 0,1 (`DUMP:296`), así que `TickAll` corre más de una vez por cuadro.
   - `FlowVeil` salta T de 5,5 a 9 en la fase 0 (`DUMP:1330-1331`): Alma entra a T≈5,5, no a 5,8 (`DUMP:473`).
   - `Speed` acelera solo `RunObra` (`DUMP:273,285`), no las etapas ni el Hall, que recortan a 1/30.
   - **Corrección:** la marca se emite donde cambia el estado, y el editor superpone trazas medidas. No se calcula solo.

7. **Duraciones de VO en la maqueta: vienen de la web, no de la mezcla final** (`MOCK:264-268` contra `MIX:16-21`, entre 0,3 y 1,2 s más cortas).
   - `VODur` es una sola variable global que cada `ObraSay` pisa (`DUMP:1870`).
   - **Corrección:** cargar las duraciones de `MIX` y modelar las fórmulas reales de cada punto de llamada:
     - Hall: `clip + VOAir` (`HDUMP:262`);
     - fase 7: `max(OutroTime, VODur + 0,6)` (`DUMP:1890`);
     - despedida (`FlowBye`): VO a 0,9 s y `ByeEnd = 1,3 + VODur` (`DUMP:1406-1415`);
     - Attracting y Drawing: siguiente VO a `fin + 0,6` (`DUMP:1989`).

8. **El pacer está mal anclado** (`MOCK:260,287`). Corrección en la maqueta:
   - el ancla es `VO_12c.start + InhaleCueAt` (3,48);
   - agregar `LeadOut` 3 s y las voces VO_12f1/f2 del primer ciclo;
   - los sonidos son pads y plucks;
   - avisar que cambiar el ritmo exige regenerar audio (`TRK/BP_Pacer_SC.md:86`).

## Lo que hay que verificar en vivo en Unreal

1. **`L_SoulCharger_Obra` → `BP_Obra_SC_C_0`.**
   - `read_graph_dsl` de `AlmaSpeak`, `StageTimes` y `StageCues`: confirmar la fórmula de `AlmaTime` (+3 o +3,5 / `max` +2,5), si todavía usa `StAlma`/`StInstr`/`StOutro`, y `InstrTime` 0,6 en K=4.
   - Re-volcar `RunObra` (literales de la fase 6: 180/120/240) y `FlowVeil` (salto 5,5 → 9).
   - Propiedades de instancia: `StAlma`, `StInstr`, `StOutro`, `AlmaTime`, `InstrTime`, `OutroTime`, `bSimulated`, `SimStageMax`, `ShareFW`, `ExploreT`, `ResultsTime`, `DebugShare`, `bGhostsOn`, `Speed`, `DebugStart` (quedó en 3: −1 antes del APK).
2. **`Test_Hall` → `HallDirector` (`BP_HallDirector_SC_C_0`).**
   - Propiedades: `FW_Bell`, `FW_Tool`, `FW_Choose`, `BellHold`, `TouchRadius`, `VOAir`, `IntroHold`, `Pace*`.
   - Grafos actuales `HallEnterIntro` (pasos 6, 12 y 14 con `bGate` false) y `HallTickTouch`/`HallTickPick`/`HallGrab` (corte de 0,3).
   - Array `VO`: confirmar que no hay VO_01h ni VO_03h.
3. **`Test_Entering`.**
   - `Entering_Stage`: `ExploreTime`, `CountTime` (3 o 3,6), `ToolDelay`, `HelpAfter`, `SayAfterTool`, `SayGap`, `InhaleCueAt`, `bCycleVO`.
   - `Entering_Pacer`: `Cycles`, `InhaleTime`/`Hold1Time`/`ExhaleTime`/`Hold2Time`, `LeadIn`, `LeadOut`, `PulseMode`.
   - `Entering_BreathRig`: `ActivateDelay`, `DeactivateDelay`, `FacingMin`.
   - `StageRunner` (K 0): `InstrTime` (6 u 8,5), `AlmaTime`.
4. **`Test_Heart`.**
   - `HeartManager`: `StageBeats`, `BeatDiv`, `OrbitAtBeat`, `BackupAfter`, `HintAfter`, `VO17cAtBeat`, `ActivateDelay`.
   - `BP_HeartScape_SC`: duración de la vuelta y del regreso.
5. **`Test_Fluid` → `LovingCell`:** `StageDuration`, `IntroDelay`, `VO22At`, `VO23At`, `VOWait`.
6. **`Test_Sequencer`.**
   - `GAL_12_Sequencer`: `FinalPasses`, `bReplayOnSave`, `StepBPM`.
   - `GAL_12_SaveMelody`: `HoldDuration`.
7. **`L_TBTest_SC` → `TBDirector`:** `InkMeters`, `HoldTime`.
8. **Los 7 `Ghost_*` y el `BP_Alma_SC` del persistente.**
   - Fantasmas: `PlayRate`, `LoopGap`, `LoopEnd` y `Frames`/`Hz` de cada `DA_Ghost_*`.
   - Alma: `VODelayIn`, `VODelayOut`, `AppearTime`.
9. **Traza PIE de referencia** (`Speed` 1, en la cola), filtrando por estas líneas del log:
   - `OBRA: StageIntro|StageBegin|StageOutro, por fin propio =`
   - `HALL: modo`, `HALL: voz cortada`, `HALL: alma elegida`
   - `BREATH: UMBRAL IN`, `HEART: latido de respaldo`
   - `OBRA: compartir =`, `OBRA: modo simulado`

   La traza se hace dos veces: una con `bSimulated` true y otra con false.