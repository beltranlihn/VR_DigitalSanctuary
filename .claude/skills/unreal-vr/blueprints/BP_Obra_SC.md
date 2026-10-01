# BP_Obra_SC — el director del NIVEL FINAL de la obra

- **refPath**: `/Game/SoulCharger/Obra/BP_Obra_SC.BP_Obra_SC` · parent Actor · duplicado de [[BP_StageTour_SC]] (2026-09-30, noche del director general).
- **Nivel**: `/Game/SoulCharger/Obra/L_SoulCharger_Obra` (duplicado de Test_Recorrido). Instancia `BP_Obra_SC_C_0`, **tag `TOUR`** (Attracting y Drawing lo usan para NO autoarrancar), `Speed` 1 (solo se sube para pruebas).
- **Plan y registro de la noche**: [`docs/PLAN-NOCHE-2026-09-30.md`](../../../../docs/PLAN-NOCHE-2026-09-30.md).

## Status
🟢 **Recorrido completo verificado en PIE (2026-09-30 10:21, Speed 6, dos vueltas seguidas)**: Hall → 5 etapas con su carga → final a negro → regreso → resultados → salida → créditos → fundido → `OpenLevel` → vuelve a arrancar solo. Las etapas cierran por tiempo (sin usuario). 0 errores propios.
🟡 Falta (T2b): llamadas reales al Hall (`BP_HallDirector_SC`), nacimiento del HUD, armado del cuadro de resultados, créditos (constelación + título + tarjetas), explosiones de la carga final. ⬜ Visor y APK.

## Motor (heredado de StageTour)
- Carga los **6 niveles de prueba** con `LoadLevelInstance` al arrancar, en negro: celdas 0-4 = Test_Entering, Test_Heart, Test_Fluid (Loving), Test_Sequencer (Attracting), L_TBTest_SC (Surrounding); **celda 5 = `/Game/SoulCharger/Mechanics/Hall/Test_Hall`**. `ClassifyOne` recorre 0..5.
- Una celda apagada: `SetVisibleInSceneCaptureOnly` + sin colisión + sin tick. Encendido por cola (`QBatch`).
- `DestroyTestOnly`: al arrancar destruye todo actor con tag **`TestOnly`** (los andamios de prueba de cada nivel de test).
- Velo (`Veil`, esfera 30 cm con `M_TourVeil_SC`, Amount / CTop / CHor) y título (`Title`, plano con `MI_TourTitle_<ETAPA>`).
- `TickAll(Dt)` → `RunObra(Dt × Speed)` → `FinalRing(Dt × Speed)`; antes de `Booted`, `BootTick` → `StartObra`.

## Fases de `RunObra` (switch 0-15, `PT` = tiempo en la fase)
| Fase | Qué | Sale con |
|---|---|---|
| 0 | abre la etapa: velo 3→9 s, título | → 4 (Alma) |
| 2 | cierra (T 69→75) | `AdvanceStage` |
| 3 | legado | `OpenLevel` |
| 4 | Alma recibe (`AlmaIn` + `AlmaSpeak`: VO_10/15/20/26/31; `AlmaTime` = largo de la voz + 2 s) | `AlmaAside` + `CallIntro` |
| 5 | instrucciones (`InstrTime` 8) | `CallBegin` |
| 6 | la mecánica | `ReadDone` (bStageDone) o timeout (Recognizing 150 s, Loving 120 s, resto 240 s) → `CallOutro` + `AlmaOut` |
| 7 | salida de la etapa (`OutroTime` 3,5) | `ChargeStart(K)` |
| 8 | carga | `ReadCharge` → `ChargeEnd` (K<4: cierra y pasa a la siguiente; K=4: `FinalStart`) |
| 9 | Hall (`HallStart`) | `HallCheck` (hoy `HallWait` 6 s; T2b: `bHallDone`) → `HallLeave` |
| 10 | final: se va el HUD, a negro | PT ≥ 3 → `HallBack` |
| 11 | regreso por la oscuridad al Hall | `ReturnCheck` (`ReturnWait` 12) → `ResultsShow` |
| 12 | cuadro de resultados (`ResultsTime` 40) | `ResultsHide` |
| 13 | salida del Hall (`ExitWait` 10) | `ExitCheck` → `CreditsShow` |
| 14 | constelación + créditos (`CreditsTime` 60) | → 15 |
| 15 | fundido (3,5 s) | `OpenLevel "L_SoulCharger_Obra"` (reinicio) |

## Contrato de etapa (lo llama el director, las etapas no llaman al director)
`CallIntro/CallBegin/CallOutro/ReadDone(K)` con switch por clase: `BP_BreathStage_SC`, `BP_HeartManager_SC`, `BP_LovingCell_SC`, `BP_Sequencer_SC`, `BP_TBDirector_NC` → `StageIntro()`, `StageBegin()`, `StageOutro()`, `bStageDone`.

## La carga (T2a, 2026-09-30)
- Actor **`BP_ChargeFx_SC_C_0`** (`/Game/SoulCharger/Obra/BP_ChargeFx_SC`, duplicado de [[BP_ChargeTest_SC]]; `HudRef` = el HUD del nivel, `AutoStart` false) + TargetPoint tag **`ObraChargeTarget`**.
- `ChargeStart(K)`: pone el TargetPoint a **2,53 m al frente del yaw de la etapa, +37 cm, escala 2,115** (la pose aprobada por Beltrán en Test_Hall) y le pasa al anillo `TargetRef`, `CavParam` (`CavNames[K]`), `StageColor` (`StageCols[K]`), `ChargeTime` (`ChargeTimes` = **4 / 4 / 4 / 4 / 6 s**, Beltrán 09-30), `HoldTime` (2; la última 9999 = no vuelve al HUD), `SpinDeg` (−450; la última −1440) → `RunCharge`.
- `ReadCharge`: etapas 0-3 = `Running` del anillo; la última = `PT < 4,97 + ChargeTimes[4]`.
- `FinalStart`: `FinalLook` del anillo (materiales DDT del HUD, sort 204/205, por delante del negro), `HUDVanish` del arte del HUD, oculta el widget, fase 10.
- `FinalRing(Dt)`: en fases 10-11 el anillo sigue a la cámara a 2,53 m (+37 cm), gira 40°/s (`RingRoll`) y en el regreso se adelanta 1,4 m en 8 s (easeInOut).

## Variables de autor (en la instancia)
`Speed` · `AlmaTime` 8 (la pisa AlmaSpeak) · `InstrTime` 8 · `OutroTime` 3,5 · `HallWait` 6 · `ReturnWait` 12 · `ResultsTime` 40 · `ExitWait` 10 · `CreditsTime` 60 · `ChargeTimes` · `StageCols` (lineales: Entering .1095/.2122/.7454 · Recognizing .7454/.0931/.147 · Loving .3231/.1559/.7913 · Attracting .807/.3515/.0762 · Surrounding .0782/.5395/.2747) · `CavNames` (Charge_Entering … Charge_Surrounding).

## 🔴 Trampas de este BP
1. Los grafos heredados de StageTour traen **islas de nodos huérfanos** (6 `RunTick` en `TickAll`). Para reemplazar una llamada, tocar SOLO el nodo alcanzable desde la entrada (`find_nodes` + `get_node_infos`).
2. El `switch` del DSL solo admite casos **consecutivos** (0..N-1): por eso las fases se renumeraron 0-15.
3. Setter de variable de OTRO blueprint: `(Class|BPChargeFxSC|SetX :self fx :X valor)` — en posicional cablea al revés.
4. Un PIE de la Obra con el pincel sin instalar inundaba la salida del `StartPIE` con `Accessed None … Tip` (~90k tokens): venía de `BP_TBTrail_NC.TrailPush`. ✅ Blindado por Drawing (2026-09-30 11:21: 903 errores en 5 s → 0). Igual, leer el log de la Obra filtrado (`OBRA:|CHARGE|Accessed None`) y no la salida del tool.

## T2b (2026-09-30, mediodía) — Hall real, HUD, resultados y créditos
- **Hall** (`/Game/SoulCharger/Mechanics/Hall/BP_HallDirector_SC`): `HallCheck` llama `HallIntro` con PT ≥ 1 (nunca en el cuadro de encender la celda), sigue `GetHudBorn` → `HudBirth` (la píldora `HUDAppear`) y el EEG (`BP_SoulHUD_SC.Birth`) 1 s después; termina con `GetHallDone`. `ReturnCheck`/`ExitCheck`: `SetLeadActor(:self hd :LeadActor anillo)` + `HallReturn`/`HallExit`, terminan con `GetReturnDone`/`GetExitDone`. `HallCalled` evita llamar dos veces; se resetea en HallStart/HallLeave/HallBack/ResultsHide.
- **HUD en la Obra**: instancia con `bBirthOnStart` false; `StartObra` hace `HUDHideNow` (cancela el AppearOnPlay de 3 s del arte), EEG en 0 (`SetBirthT 0` + `PushBirth`) y **`SetBioFound false`** (el HUD cachea el primer BioHub que encuentra; si era un `TestOnly` que la Obra destruye, `StepSignals` inunda el log con "pending kill").
- **Resultados** (`ResultsShow`): `BP_ResultsArt_SC_C_0` + `BP_JourneyContent_SC_C_0` en el persistente (z −5000, `ResultsHideNow` + oculto en HallStart). Cuadro a 1,9 m frente a la cámara (−8 cm), mirando al usuario; contenido colgado con `AttachActorToActor` (así lee los K del marco); `SetBreathScores(CycleScores)` + `SetMinutes 0` + `Build` + `ResultsAppear`; anillo a la izquierda del usuario (−right × 100 cm, escala 0,5), dibujo a la derecha (`PlaceSketch`, 55 cm), gusano en la ventana de la melodía (`ResultsShow(Xf)`, z −38, X local = derecha del usuario), láser `ResultsBeam(true)`. `ResultsHover` (por cuadro en fase 12, desde `FinalRing`): impacto del láser en local del marco → |Y| ≤ 51,5 y bandas Z (calma ≥ 15,5 · ritmo ≥ −7,5 · respiración ≥ −26,5 · melodía ≥ −47,5) → `SetTip` + `TipShow/TipHide` solo al cambiar (`LastTipK`).
- **Créditos** (`CreditsShow` + `BP_Credits_SC`): el actor de créditos va al ojo mirando al frente; el anillo sube a `SoulSpot` (ojo + 4,8 m al frente + 1,5 m arriba, dentro de la niebla de 6 m del Hall); VO_35b a PT 8 y VO_37 a PT 18,5; en la fase 15 `Hide` funde el título (los planos son DDT sort 110 y quedarían por encima del velo negro). Estrellas = 30 `StaticMeshActor` con tag `CreditStar` (carpeta Credits del outliner), colocadas a mano-por-script alrededor de StopExit: se autoran moviéndolas en el viewport.
- **Modo fotos** (`bPhotos`, instance-editable, false): `PhotoTick` saca `HighResShot 1920x1080` en el Hall (pasos 13 y 27), cada mecánica (12 s), cada carga (2,5 s), el regreso (3 s), los resultados (4 s) y los créditos (19 s); tiempos en segundos reales (PT / Speed). Las capturas quedan en `Saved/Screenshots/WindowsEditor/`.

### Trampas de T2b
5. `CallFunction|Step` resolvió a **`BP_HeartSensor.Step`** (colisión de nombres del DSL): las funciones nuevas llevan nombres únicos (`CreditsStep`).
6. `Rendering|SetActorHiddenInGame` sobre self con un valor posicional perdió el `true`: usar **`:bNewHidden`**.
7. Reescribir un grafo desde su `read_graph_dsl` falla ("bind ... produced no output pin" con literales): se reescribe desde la fuente propia, no desde el read.
8. Un `set_properties` que falla en UNA propiedad hace que el `execute_tool_script` devuelva error aunque el resto se aplique: verificar con `get_properties` y contar actores (no hubo Undo).

## Inicio v2 (2026-09-30 tarde, prueba de Beltrán en visor) — `FinalFlow` y compañía
Todo lo nuevo vive en grafos NUEVOS; RunObra no se toca. `TickAll` llama `FinalFlow` después de `FinalRing` (rama Booted) y después de `BootTick` (arranque): lo que escribe gana en ese cuadro.
- **Arranque en negro puro**: `M_TourVeil_SC` tiene un parámetro **`Floor`** (0,02, piso de brillo contra las bandas en paletas oscuras) → con CTop/CHor negros igual da gris #2B2B2B. `FinalFlow` pone `Floor` 0 mientras no está `Booted` y en la fase 9 con PT < 6; en el resto 0,02.
- **Celdas apagadas en el negro**: la cola `QueueCell/StepQueue` apagaba de a `QBatch` componentes por cuadro y el velo se abría en el mismo cuadro → se veían las etapas (celdas a veces superpuestas en el origen). Ahora `QBatch` = 100000 durante el arranque (se guarda en `QSave`) y vuelve a su valor a PT 1 de la fase 9.
- **Velo del Hall**: fase 9, PT < 3,5 negro opaco; abre 3,5 → 5,5 a la niebla del Hall (que ya está a pleno).
- **`IntroTitle`**: SOUL CHARGER + bajada QUIETOS con `TitleP/SubP` de `BP_Credits_SC` (se coloca una vez a PT 2,5 frente a la cámara, −45 cm; revela PT 3 → 6,5, sale 10 → 12,5; `TitleSt` 0/1/2). La caminata del Hall arranca a PT 13 (`IntroHold` 12 s del Hall).
- **Ambientes** (`AmbPick` → `AmbTo(K)` → `AmbFade`/`AmbStart`): `AmbCur` (AudioComponent) con `CreateSound2D` + FadeIn 3 s a 0,8 y FadeOut 3 s. Intro (1) → Start (2, al terminar el título) → Hall (3, cuando `DoorW` > 0,3; se queda hasta que `DoorE` > 0,05) → silencio → Breath (4) / Heart (5) / Mind (6) / Attracting = pad del secuenciador / Surrounding = el AmbientSound de `L_TBTest_SC` (se enciende con la celda) → regreso y resultados = Salida (8) → créditos (9). Solo con `Booted` (antes el Hall no existe → Accessed None).
- **Fotos de depuración**: con `bPhotos`, HighResShot a PT 1 / 6 / 9 de la fase 9 (`DbgShot`).

### Trampas nuevas
9. `Audio|Components|Audio|FadeIn/FadeOut` del DSL resuelven a **SynthComponent** ("Could not connect pin AmbCur to self"). Se crean con `create_node` + `declaring_class: /Script/Engine.AudioComponent` y se cablean a mano.
10. `Math|Vector|vector+vector` aparece en el READ pero no existe al escribir: sumar vectores con `(+ a b)`.
11. El getter de `bPhotos` es `Variables|Default|GetPhotos` (el DSL saca la b).
12. `TickAll` tiene islas huérfanas heredadas (6 `BootTick`): al cablear "después de BootTick" se colgó un `FinalFlow` de cada isla (huérfanos inofensivos; limpiar con `clean_orphans.py`).

## Turno A2 (2026-09-30, ~17:15) — aviso, final nuevo, despedidas, velos
`FinalFlow` = orquestador (grafos chicos): `FlowVeil` (velo: arranque/aviso/inicio del Hall/última carga/negro/regreso/apertura ágil de cada etapa) · `FlowDisc` (fase 16) · `IntroTitle` · `AmbPick` · `FlowFinal` (FinalLook desde el comienzo de la última carga, salto al Hall a PT 0,3, el alma nada al anillo en resultados, `ResultsPlay` a PT 2) · `FlowBye` (despedida de Alma después de cada carga; el velo espera con T = 69).
- **Aviso**: `StartObra` llama `StartDisc` (antes HallStart): con `bSimulated` pone `bFakeSignal` en todos los BioHub; con `bDisclaimer` fase 16 + `BP_Disclaimer_SC.DiscShow` (20 s, `DiscTime`) → `HallStart`.
- **Regreso**: `ReturnCheck` a PT 0,5: el pez (`BP_SoulFish_SC`, colocado como `SoulFish`) nace donde está el alma del anillo (`BaseScale` = escala del anillo), `FishOn`, el anillo se va (`RingShow` false) y el Hall lleva al pez como `LeadActor`.
- **Resultados**: `ResultsShow` reescrita: anillo grande (`ResRingScale` 1,9, a `RingSide` 112 cm a la izquierda, `NormalLook`, oculto) en `RingSpot`; el pez nada hasta ahí (VInterp 0,8, mínimo 1,8 s) → `RingShow` true + `FishOff`; `SketchAppear` del dibujo.
- **Alma**: `AlmaIn` reescrita (ObraAlmaB a 140 al frente y 300 al costado izquierdo); `FlowBye` con `Alma.PlayClip` (VO de la carga + la invitación) y `AlmaOut`.
- **Velos**: `CTops`/`CHors` (CDO e instancia, ahora instance-editable) = el cielo real de cada etapa (igual que la web v47).
- Perillas nuevas: `bDisclaimer`, `bSimulated` (true en la instancia), `DiscTime` 20, `ResRingScale` 1,9, `RingSide` 112; `InstrTime` 6, `OutroTime` 2,5.
13. 🔴 **`find_node_types` no ve lo creado en esta sesión del editor** (BPs nuevos y funciones nuevas de BPs viejos: `BP_SoulFish_SC`, `BP_Disclaimer_SC`, `SketchAppear`), pero **`write_graph_dsl` sí los resuelve** por `Class|BPNombreSC|Funcion`. No confiar en el índice para decidir si algo existe: probar con una función de prueba vacía y leerla.
14. `set_properties` sobre un array de LinearColor de la INSTANCIA falla si la variable no es instance-editable; se hace editable y se escribe con claves r/g/b/a en minúscula.
15. Variables nuevas que se vuelven instance-editable DESPUÉS de colocada la instancia quedan en su valor por defecto (false) en la instancia: verificar y reponer (`bDisclaimer`/`bSimulated`).

## Ensayo de etapa (2026-09-30, ~18:10) — la Obra lee los niveles de test
Ver [[BP_StageRunner_SC]]. `DestroyTestOnly` llama primero a `ReadRunners` (colores del velo → `CTops/CHors[K]`; AlmaTime / InstrTime / OutroTime → `StAlma/StInstr/StOutro[K]`). `AlmaIn(K)` → `TPOverA/B(K)` (ObraAlmaA/B a los TP `TpIn/TpSide[K]`) + `StageTimes(K)`. `ChargeStart` → `ChargeTP(K)` (cirugía: entre SetActorScale3D y SetTargetRef, porque el anillo lee el destino al arrancar). `FinalFlow` → `TitleTP()` en fase 0 con T < 0,4. Arrays nuevos: `TpIn/TpSide/TpCharge/TpTitle` (CDO = `sc<K>_*`), `StAlma/StInstr/StOutro`. Altura: z + cámara − (StartLoc[K].z + 120).
16. Cambiar este BP con la Obra CERRADA (otro nivel abierto) evita el reinstanciado de la instancia colocada (gotcha 402).

## Turno B (2026-09-30, ~20:30) — el final con COMPARTIR (probado en PIE las dos ramas, 0 errores)
Fuente: `Saved/ClaudeScripts/Obra/turnB2.json` (+ `turnB2_build.py`, `fish3.json`). Tiempos como la web v48+ (beats 9.4-9.7): solo la VO usa su largo.
- `FinalFlow` → fase 12 `FlowShare`, fase 14 `FlowConst`.
- **FlowShare** (estados `ShareSt`, `ShareGo(S)` guarda `ShareT`):
  - 0: PT 0,5 `AlmaResults` (ObraAlmaB a la izquierda del anillo; AppearAt si estaba oculta, si no MoveTo) + VO_34c;
  - 1: +8 VO_34b;
  - 2: +17,8 + `ExploreT` (25) VO_36;
  - 3: +4,9 VO_36b;
  - 4: +9,6 `SharePlace` + Appear de los dos botones (`GetAllActorsOfClassWithTag` share_yes/share_no, `ShareDrop` 64 cm bajo el cuadro, pitch 15);
  - 5: +1,8 VO_36p + `LastPressN`;
  - 6: `SharePickStep`: hover por `BP_SeqRig_SC.BeamHitActor`, gatillo = `ResPressN` cambia con un botón apuntado; `DebugShare` (−1; 0/1 elige a los 3 s); cortafuegos `ShareFW` 30 s = DON'T, con **bSimulated = SHARE** (APK de postulación);
  - 7: +0,5 `ShareResOut` (ResultsVanish, SetTip None, Sequencer.ResultsHide, ResultsBeam off, SketchVanish);
  - 8: `ShareAnswer` (VO_36c/36d a 0,2).
- **SHARE**: a 0,8 s el anillo se va (`RingShow` false) y `ShareFree` pone el pez en `RingSpot` (BaseScale = escala del anillo) + FishOn; `ShareSwim` Lerp ease a `DoorPt` en `SwimTime` 4 y a `AwayPt` en `AwayTime` 3; `HallDoor(East false, Open 1)` a 2,5 s; FishOff; Alma Disappear a 1,4 + 4 + 3 s.
- **DON'T SHARE**: el anillo se va a 0,6 s + FX_SOULVANISH; Alma Disappear a 2,6 s.
- Después, `ShareExit` (ya no `ResultsHide`: oculta los trazos, HallCalled false, fase 13). `ExitCheck`: LeadActor = el pez (oculto; abre la Oeste al pasar). `ResultsTime` 150 (CDO) = solo cortafuegos.
- **FlowConst** (fase 14): `CreditsVO` 2 (apaga las VO viejas de FinalRing); SHARE → PT 5 pez en `SoulSpot` + `HaloOn` + FishOn; PT 8 VO_35b / VO_35c; VO_37 0,5 s después.
- `AlmaSpeak` y `FlowBye` → `Alma.SayClip` (Heart). Runner `RSay` también.
- BP_SoulFish_SC: componente `Halo` (Plane, MI_FishSpark_SC, sort 64) + `HaloOn`/`HaloAmt` 0,55/`HaloSize` 0,3 + `FishHalo` (llamada al final de FishSparks).
17. Una función no puede llamarse igual que una variable (`SharePick` → "not valid EdGraph"): renombrada `ShareChoose`.
18. `Math|Rotator|GetRightVector` no existe: `Math|Vector|GetRightVector` / `GetForwardVector`.
19. Llamar a un BP por tag: `GetAllActorsWithTag` devuelve Actor y la llamada tipada falla ("Could not connect pin Output to self"); usar `Actor|GetAllActorsOfClassWithTag` (sale tipado).
20. Getter de un bool con b de otro BP: `Class|BPHallDirectorSC|GetExitDone` (sin b).
- **`SimCut`** (FinalFlow, rama Booted): con `bSimulated` (APK de postulación, autoplay), Attracting y Surrounding (etapas 3-4) cierran a `SimStageMax` 90 s de mecánica (PT de la fase 6 → 1000; RunObra las cierra al cuadro siguiente). Sin usuario, antes esperaban el timeout de 240 s sin nada que ver.
- **PIE completo 2026-09-30 ~18:05 (log), Speed 2, flujo normal con bSimulated: 0 errores**:
  · aviso → Hall (alma del centro) → HUD;
  · Entering por fin propio · Recognizing con latido de respaldo y fin propio (~35 s) · Loving y Attracting por timeout;
  · Surrounding → carga final → regreso → resultados (el pad 0,5 s después de ResultsPlay) → SHARE por cortafuegos simulado → pez → constelación con halo → fundido.

## Arranque de debug (2026-10-01 ~00:30, pedido de Beltrán)
Dos variables en la instancia, categoría **Debug**: **`DebugStart`** (−1 = normal) y **`DebugSoul`** (0 = el alma que el Hall pone al centro).

| `DebugStart` | Parte en |
|---|---|
| −1 / 0 | normal (aviso si `bDisclaimer`) |
| 1 | Hall, inicio (sin aviso) |
| 10 · 11 · 12 · 13 · 14 | Entering: apertura · Alma recibe · instrucciones · mecánica · salida y carga |
| 20-24 | Recognizing (mismo orden) |
| 30-34 | Loving |
| 40-44 | Attracting |
| 50-54 | Surrounding |
| 60 | última carga |
| 61 | regreso al Hall |
| 62 | resultados |
| 63 | SHARE (botones a la vista) |
| 64 | constelación y créditos |

- **Cómo funciona.** `StartDisc` (reescrita) → si `DebugStart` ≥ 1, `ObraDbgBoot`:
  - Devuelve `QBatch` a su valor chico (`QSave`). El arranque lo deja en 100000 hasta PT 1; sin esto, `StepQueue` corre 100000 vueltas por cuadro → "Infinite loop" → el PIE se cierra.
  - `ObraDbgPrep(K)`: lista `Souls` del Hall = `GetAllActorsWithTag("soul_pick")` (el Hall la llena recién en `HallPickStart`; vacía → "index 0 of Souls length 0"), `ChosenSoul` = `DebugSoul`, oculta las 5 almas del Hall, `HudBirth` (colores del alma) + `Birth` del EEG, y enciende `Charge_<Etapa>` = 1 de las etapas anteriores en el anillo del HUD y en el grande.
  - Apaga la celda del Hall. Para 10-54 hace `EnterStage(K)`; para 60+ usa la misma entrada que `bDebugEnding` (fase 8, `ChargeStart 4`).
- **`ObraDbgFF`** (llamada al final de `SimCut`, rama Booted): hasta llegar al punto, cumple la condición de salida de cada fase y deja que `RunObra` haga su transición normal. Así cada etapa recibe `StageIntro`/`StageBegin`/`StageOutro` en orden.
  - En las fases 4, 5 y 6 pone PT = 1000 a los 0,3 s, con `Alma.FadeVoice(0.3)`.
  - En la fase 8 adelanta PT al fin de la última carga.
  - En la fase 11 pone `bReturnDone` del Hall; en la 13, `bExitDone`.
  - En la 12, para el SHARE, adelanta `ShareT` (estados 1-4); para la constelación, `ShareSt` 99 + PT = `ResultsTime`.
  - Al llegar: `DbgK` = −1 y log `OBRA: DEBUG - llegue al punto N`.
- **Probado en PIE, 0 errores**: 13 (≈6 s a la mecánica), 34 (sale y carga Loving), 43 (Attracting), 50, 63 (SHARE a los ≈3,5 s), 64 (créditos a los ≈3,5 s), 1.
- **Límites.** Lo saltado no deja resultados: el cuadro final muestra los valores por defecto (sin dibujo, sin melodía propia). En el 62-64, el `HallReturn`/`HallExit` del Hall sigue su curso de fondo. La apertura de la etapa (≈5,5 s) no se salta.
- ⚠ **Para el APK: `DebugStart` en −1.** `bDebugEnding` sigue igual y le gana a `DebugStart` (lo mira antes `StartObra`).

## Arranque limpio (2026-10-01 ~00:10)
- **Glitch reportado por Beltrán**: al dar Play se veían títulos de las transiciones y sonaba otra música ≈2,5 s antes del negro del aviso.
  - **Títulos**: `Title`/`Veil` de los 5 `BP_StageRunner_SC` nacían visibles (sort 32700, por encima del velo de la Obra, sort 32600) entre que la celda se registra y su BeginPlay. → ocultos en el CDO.
  - **Música**: el AmbientSound `Ambient_Surrounding` de `L_TBTest_SC` (Ambient_Clip_7) se autoactiva al cargar la celda, y la Obra recién lo pausaba en `StartObra`. → **`ObraBootMute`** (primera llamada de `FinalFlow`): antes de `Booted`, pausa cada AmbientSound en cada cuadro. Es la misma pausa de `SetCell`, adelantada; al entrar a Surrounding `AudioOn` lo reanuda como antes.
- **Auras huérfanas**: cada Alma de ensayo (TestOnly) spawnea su `BP_AlmaAura_SC` en su celda. Al destruirse el Alma quedaban 5 auras (900 motas cada una) dentro de las celdas.
  - `DestroyTestOnly` termina con **`DestroyOrphans`**, que destruye las auras cuyo `Owner` ya no es válido, antes de `Classify`.
  - La misma aura se destruye sola si pierde su `AlmaRef` (`AuraDrive`).
- **`IntroTitle` (2026-10-01)**: si existe la marca `mark_hall_title` (`BP_AuthorMark_SC` en Test_Hall = celda 5), el título SOUL CHARGER se pone en su pose y escala (altura corregida con la cámara), y a los 13 s la escala del actor de créditos vuelve a 1. Sin marca, como antes (cámara −45 cm).
- 21. Un `GetAlmaRef` sobre el aura resolvió a `BPStageDirector` (otra clase con una variable del mismo nombre): usar `GetOwner`.
- 22. En el DSL el `for` sobre un array es `(for _x arr ...)`; `(for _i _x arr)` falla con "Undefined variable _x" y deja el grafo vacío (se había borrado antes de escribir).

## 2026-10-01 (Narrativa) — `IntroTitle` usa el título real
- Igual que `BP_HallRunner_SC.HRTitle` (fase 9, PT ≥ 2,5): busca el tag `hall_intro_title` (`TituloInicio` en Test_Hall), corrige la altura una vez, lo muestra y anima; a 13 s lo oculta. Sin el actor, cae a los planos de `BP_Credits_SC`. Ya **no** copia ni restaura transforms de los planos de los créditos (antes compartían planos). Fuente `step2.json`.

## 2026-10-01 (Narrativa) — el FINAL con objetos colocados (paso 5)
Fuente `Saved/ClaudeScripts/Obra/step5.json` (generador `scratchpad/obra/gen_step5.py`); respaldo de lo anterior en `spawn/step5_backup.json` y `step5_restore.json`. Escrito con Test_Results abierto (sin instancias de la Obra ni de los créditos).
- **Colocados en el persistente, carpeta `Final`** (posiciones = las que antes calculaba el código desde la cabeza, con `StopCard` (396,45; 0) yaw 180 y `StopExit` (−1500; 0)):
  - `Final_Cuadro` (`BP_ResultsArt_SC`) (206,45; 0; 201,97) yaw 0, **Actor Hidden In Game**;
  - `Final_BotonShare` (206,45; 15; 137,97) y `Final_BotonDontShare` (206,45; −15; 137,97), pitch 15;
  - `AnilloCarga` (`BP_ChargeFx_SC`) (206,45; 112; 201,97) escala 1,9;
  - `Final_AlmaPez` (`BP_SoulFish_SC`) (−1980; 0; 346,97) escala 2,115;
  - `Final_Creditos` (`BP_Credits_SC`, carpeta Credits) (−1500; 0; 196,97) yaw 180;
  - TargetPoints `final_sketch` (206,45; −100; 201,97) · `final_alma` (166,45; 222; 226,97) · `final_fish_door` (−635,84; 0; 226,97) · `final_fish_away` (−1297,68; 0; 286,97).
  - `BP_JourneyContent_SC` sigue en z −5000: el código lo pega al cuadro.
- **Altura:** todo usa `z + (cam.z − (pawn.z + 120))`, aplicado una sola vez por puesta en escena.
- **Variables nuevas:** `RingHomeLoc`, `RingHomeScl`, `FishHomeLoc`, `FishHomeScl` (Vector), `HomeOK`.
- **`FinalHome`** (función nueva, primera llamada de `FinalFlow`, una vez): lee la pose colocada del anillo y del pez antes de que nadie los mueva, y apaga la colisión del cuadro y de los botones (`SetActorEnableCollision false`), porque están en el Hall y si no taparían el láser de otras etapas.
- **`ResultsShow`**: el cuadro usa su pose colocada (+ altura), se muestra, se le enciende la colisión y se prepara (`ResultsHideNow`) antes de `ResultsAppear`. El contenido se pega al cuadro. El gusano va en la ventana de la melodía, relativo al cuadro (+4 cm hacia el usuario, −38 cm; yaw del cuadro − 90). El anillo va a `RingHomeLoc` con escala `RingHomeScl`. El dibujo va a `final_sketch` (Size = escala X × 55). Ya no usa `RingSide` ni `ResRingScale` (quedan sin uso).
- **`SharePlace`**: los botones quedan donde están (+ altura) y se enciende su colisión. `ShareDrop` queda sin uso.
- **`ShareFree`**: `DoorPt`/`AwayPt` = `final_fish_door`/`final_fish_away` (+ altura).
- **`AlmaResults`**: `ObraAlmaB` toma la posición (+ altura) y la escala de `final_alma`.
- **`CreditsShow`**: los créditos quedan donde están (+ altura); `SoulSpot` = `FishHomeLoc` (+ altura). **`FlowConst`**: `BaseScale` = `FishHomeScl.x`.
- **`ObraDbgFF`**: al forzar `bReturnDone` (puntos 62-64) teletransporta el pawn a `StopCard`; al forzar `bExitDone` (64), a `StopExit` (`HallTeleport` corta la caminata).
- **`BP_Credits_SC`**: construcción con `Reveal` 1 en `TitleP`, `SubP` y `Card0` (se ven en el editor); `Show` pone `Reveal` 0 en los 8 planos antes de mostrarse (sin chispazo de un cuadro).
- ✅ PIE 2026-10-01 (escritorio, −120 en z): 62 → cuadro, anillo y pez en su puesto, Alma en `final_alma`, pawn en `StopCard`; 63 → botones en su puesto, el pez nada por door → away, constelación con el pez en `SoulSpot` y los créditos en `Final_Creditos`; 64 → pawn en `StopExit`; arranque normal limpio. 0 errores.
- El pez y el anillo nunca se ven juntos: al llegar, el pez se apaga (`VisTarget` 0) y el anillo se enciende en el mismo cuadro (cruce medido de ~0,1 s); en SHARE `ShareAnswer` apaga el anillo antes de que nazca el pez.

## 2026-10-01 (Narrativa) — paso 6: ambientes como variables y sonidos de objetos en 3D
- **Ambientes** (categoría `Ambientes`, editables en la instancia): `AmbClips` (SoundBase[9], el orden 1-9 de siempre), `AmbVolumes` (float[9], 0,8), `AmbFadeIn` / `AmbFadeOut` (3 s). `AmbTo(K)` crea el clip `AmbClips[K−1]` en 2D con volumen `AmbVolumes[K−1]`. `AmbStart` hace un `FadeIn` de `AmbFadeIn` a nivel 1,0 (el volumen ya viene en el clip) y `AmbFade` un `FadeOut` de `AmbFadeOut`; esos nodos `FadeIn`/`FadeOut` son los originales (AudioComponent), operados por cirugía. ✅ PIE: ambiente 1 = Clip_1 a 0,8, 2D.
- **FX del final en su lugar** (cirugía `PlaySound2D` → `PlaySoundAtLocation`): `FX_SHAREAPPEAR` (FlowShare) y `FX_SHARESELECT` (ShareChoose) en el cuadro (`GetActorOfClass` ResultsArt); `FX_SOULVANISH` (ShareAnswer) y `FX_RINGVANISH` (ShareResOut) en `RingSpot`. Las VO siguen en 2D.
- Variables `RingHomeLoc/Scl`, `FishHomeLoc/Scl` y `HomeOK` en la categoría `Interno`.
- Atenuación compartida `ATT_Objeto_SC` (ver MAPA-DE-AJUSTES, Sonido). Script genérico de la cirugía: `scratchpad/obra/sfx_swap.py` (conserva exec, sonido, volumen y tono; ubicación = self / actor de una variable / vector / actor de una clase).
