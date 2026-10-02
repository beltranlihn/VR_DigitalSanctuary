# BP_Obra_SC — el director del NIVEL FINAL de la obra

- **refPath**: `/Game/SoulCharger/Obra/Blueprints/BP_Obra_SC.BP_Obra_SC` · parent Actor · duplicado de [[BP_StageTour_SC]] (2026-09-30, noche del director general).
- **Nivel**: `/Game/SoulCharger/Obra/L_SoulCharger_Obra` (duplicado de Test_Recorrido). Instancia `BP_Obra_SC_C_0`, **tag `TOUR`** (Attracting y Drawing lo usan para NO autoarrancar), `Speed` 1 (solo se sube para pruebas).
- **Plan y registro de la noche**: [`docs/PLAN-NOCHE-2026-09-30.md`](../../../../docs/PLAN-NOCHE-2026-09-30.md).

## 🔴 Estado vigente (2026-10-02, reordenamiento) — leer esto antes que la historia de abajo
- **Los tiempos salen de la Partitura** ([BP_Partitura_SC.md](BP_Partitura_SC.md)): `LoadPartitura` (primer nodo del BeginPlay, antes de `ObraCmdLine`) copia los 60 valores de `DA_Partitura_Obra` a variables de la categoría **Partitura**. **63 pines literales** de los grafos quedaron conectados a esas copias. Un tiempo **no** se cambia en este BP, se cambia en el DA. La tabla de fases de abajo da los valores de antes: los vigentes están en `docs/PARTITURA.md`.
- `StageTimes(K)`: `InstrTime = InstrDur[K]`, `OutroTime = SalidaDur[K]`, `EtapaTopeK = EtapaTope[K] + CorteEspera`, `AlmaTime = largo de la VO + AlmaTrasVoz`. `ReadRunners` ya no pisa esos tiempos (los ensayos leen la misma Partitura).
- **Cierre único de etapa** (`EtapaCortes`, en fase 6): cuando PT llega a `EtapaTope[K]` (o a `SimEtapaMax` con `bSimulated` desde la etapa 3), marca `CortePedido`, guarda `CorteAt`, corre el tope a `PT + CorteEspera`, imprime `OBRA: se acabo el tiempo de la etapa K - se le pide que cierre por su propio camino` y llama a **`RequestEnd(K)`** → `StageRequestEnd` del BP de la etapa (Breath, HeartManager, LovingCell, Sequencer, TBDirector). La etapa cierra sola y levanta `bStageDone`. Si no lo hace en `CorteEspera` (30 s), cierra el tope duro de siempre. `SimCut` se reescribió sobre esto y desaparecieron los `DrawCut*`.
- **Prueba de humo**: `ObraCmdLine` lee `-ObraSmoke` / `-ObraSpeed=N` y `SmokeTick` imprime `OBRA SMOKE: fase F etapa K reloj <TourT> speed <Speed>` en cada cambio y `OBRA SMOKE: FIN OK` + `QuitGame` en la fase 15. Se corre con `python tools/unreal/smoke_obra.py`.
- `HallRing`: tiene una guarda para cuando el alma elegida no es válida (antes eran unas 12 000 advertencias "Souls index -1" por pasada).
- **Categorías** (221 variables): Config (`bDisclaimer`, `bSimulated`) · Debug (`Speed`, `DebugStart`, `Smoke*`, banderas de prueba) · Partitura (copias del DA) · Interno (`Phase`, `Stage`, `PT`, `T`, `TourT` y las derivadas `Velo_CierreFinT`, `Final_NegroIniPT`, `Hall_VeloGuarda`, `Etapa_TopeK`) · y las de autor por momento. En el DSL: `Variables|Interno|GetPhase`, `Variables|Debug|GetSpeed`, `Variables|Partitura|GetInstrDur`, etc.
- Se borraron 15 variables sin uso (`DrawCut*`, `Fired`, `InitHidden`, `LevelOuter`, `HallWait`, `ReturnWait`, `ExitWait`, `DbgShot`, `ResRingScale`, `RingSide`, `ShareDrop`, `SketchYaw`).
- Pendiente: los títulos de `BP_HallRunner_SC` todavía tienen literales propios que no coinciden con `IntroTitle` de la Obra.

## Status
🟢 **Recorrido completo verificado en PIE (2026-09-30 10:21, Speed 6, dos vueltas seguidas)**: Hall → 5 etapas con su carga → final a negro → regreso → resultados → salida → créditos → fundido → `OpenLevel` → vuelve a arrancar solo. Las etapas cierran por tiempo (sin usuario). 0 errores propios.
🟡 Falta (T2b): llamadas reales al Hall (`BP_HallDirector_SC`), nacimiento del HUD, armado del cuadro de resultados, créditos (constelación + título + tarjetas), explosiones de la carga final. ⬜ Visor y APK.

## Motor (heredado de StageTour)
- Carga los **6 niveles de prueba** con `LoadLevelInstance` al arrancar, en negro: celdas 0-4 = Test_Breath, Test_Heart, Test_Mind (Loving), Test_Sequencer (Attracting), Test_Draw (Surrounding); **celda 5 = `/Game/SoulCharger/Hall/Maps/Test_Hall`**. `ClassifyOne` recorre 0..5.
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
- Actor **`BP_ChargeFx_SC_C_0`** (`/Game/SoulCharger/Obra/Blueprints/BP_ChargeFx_SC`, duplicado de [[BP_ChargeTest_SC]]; `HudRef` = el HUD del nivel, `AutoStart` false) + TargetPoint tag **`ObraChargeTarget`**.
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
- **Hall** (`/Game/SoulCharger/Hall/Blueprints/BP_HallDirector_SC`): `HallCheck` llama `HallIntro` con PT ≥ 1 (nunca en el cuadro de encender la celda), sigue `GetHudBorn` → `HudBirth` (la píldora `HUDAppear`) y el EEG (`BP_SoulHUD_SC.Birth`) 1 s después; termina con `GetHallDone`. `ReturnCheck`/`ExitCheck`: `SetLeadActor(:self hd :LeadActor anillo)` + `HallReturn`/`HallExit`, terminan con `GetReturnDone`/`GetExitDone`. `HallCalled` evita llamar dos veces; se resetea en HallStart/HallLeave/HallBack/ResultsHide.
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
- **Ambientes** (`AmbPick` → `AmbTo(K)` → `AmbFade`/`AmbStart`): `AmbCur` (AudioComponent) con `CreateSound2D` + FadeIn 3 s a 0,8 y FadeOut 3 s. Intro (1) → Start (2, al terminar el título) → Hall (3, cuando `DoorW` > 0,3; se queda hasta que `DoorE` > 0,05) → silencio → Breath (4) / Heart (5) / Mind (6) / Attracting = pad del secuenciador / Surrounding = el AmbientSound de `Test_Draw` (se enciende con la celda) → regreso y resultados = Salida (8) → créditos (9). Solo con `Booted` (antes el Hall no existe → Accessed None).
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
  - 🔴 **2026-10-02 — el corte del DIBUJO pasa por el guardado.** Antes, la etapa 4 también cortaba con `PT = 1000` → `StageOutro` cerraba el sistema sin `SaveSketch`: el dibujo se quedaba quieto, la carga ocurría delante y en resultados no aparecía (`SketchSet` vacío). Reportado por Beltrán en el APK del 10-01 y confirmado con su logcat.
    - Ahora solo Attracting (etapa 3) corta con `PT = 1000`. Drawing, al llegar a `SimStageMax` (simulado) o `DrawCutT` 205 (normal), llama una vez a `BP_TBDirector_NC.TimeUp()` (`DrawCutDone`, `DrawCutAt`) y `RunObra` espera el `bStageDone` normal, que llega al terminar la presentación (~12 s). Tope de seguridad: `DrawCutWait` 30 s → `PT = 1000`. `DrawCutDone` se resetea fuera de la fase 6. 205 + 30 < 240 (timeout de la fase 6).
    - Perilla de prueba `DbgDrawSynth` (CDO, false; no es editable por instancia): a los 2 s de la etapa 4 llama `TB.DbgSynth()` (trazo sintético) y se apaga sola.
    - ✅ PIE (DebugStart 50, sintético, corte a 40 s): corte → "se guarda el dibujo y se presenta" → 12 s → "StageOutro, por fin propio = true" → carga → resultados con el dibujo (aparece y se va con SHARE). 0 errores.
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
| 2 · 3 · 4 · 5 · 6 · 7 · 8 · 9 | Hall por pasos (2026-10-01): portal (paso 4) · **timbre** (6) · **justo dentro**, Alma aparece (10) · sensor (12) · elección (14) · baldosas (16) · nace el HUD (24) · Alma a la puerta (26) |
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
  - **Música**: el AmbientSound `Ambient_Surrounding` de `Test_Draw` (Ambient_Clip_7) se autoactiva al cargar la celda, y la Obra recién lo pausaba en `StartObra`. → **`ObraBootMute`** (primera llamada de `FinalFlow`): antes de `Booted`, pausa cada AmbientSound en cada cuadro. Es la misma pausa de `SetCell`, adelantada; al entrar a Surrounding `AudioOn` lo reanuda como antes.
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

## 2026-10-01 (Narrativa) — transiciones ágiles (pedido de Beltrán: el título nunca con Alma)
- Literales en `RunObra`: título `Reveal` T 0,5→2,3 · `Out` 3,3→4,5 · visible si T < 4,6 · salida de fase 0 (AlmaIn) T ≥ 4,7 · velo de cierre 69→71,5 y `AdvanceStage` a T ≥ 71,5 · apertura del velo 1→4 (en `RunObra` y en `FlowVeil`). Los tres umbrales `<`/`>=` son nodos `MakeLiteralFloat` aparte (no pines).
- ✅ PIE (DebugStart 14): de `AlmaOut` a la siguiente Alma 6,3 s (antes ~11,5). Pendiente: `FlowBye` acumula `GetWorldDeltaSeconds` por llamada y `FinalFlow` corre ~1,5 veces por cuadro → el reloj de la despedida va 1,5× (la 2.ª VO pisa a la 1.ª). Se arregla con el flujo nuevo de VO.
- `IntroTitle` con rama de logos (ver BP_IntroTitle_SC).

## 2026-10-01 (Narrativa) — VO v3: la mezcla final de Beltrán manda los tiempos
- Duraciones (con cola de reverb) en `VR_Test/Saved/ClaudeScripts/vo_final/duraciones_mezcla.txt`. **Ningún tiempo de VO está escrito a mano**: cada llamada pasa por `ObraSay(Clip)` (Alma habla con `SayClip`) u `ObraVO2D(Clip)` (2D), y las dos dejan el largo del clip en `VODur` (`SoundBase.GetDuration`). Cambiar un wav reacomoda el flujo solo.
- **Por etapa (K 0-4):** `AlmaSpeak` VO_10/15/20/26/31 → `AlmaTime = VODur + 2` · `StageTimes` asegura `AlmaTime ≥ VODur + 1` · fase 6 `AlmaCharge(K)` VO_13/18/23b/29 (K<4) **antes** de la carga → `OutroTime ≥ VODur + 0,6` · fase 7 `AlmaOut` + `ChargeStart` · `FlowBye` (reloj = `PT`): a 0,9 s VO_14/19/25/30, `ByeEnd = 1,3 + VODur`, después `AlmaOut`.
- **Final:** `FinalStart` VO_33 (2D) · `FlowShare` st0 `AlmaResults` + VO_34b, espera `VODur + ExploreT` · st2 VO_36b, espera `max(0,5; VODur − 1,2)` · st4 cuadro + botones + `FX_SHAREAPPEAR` · st5 (+1,8) VO_36p · `ShareAnswer` ya sin VO_36c/36d · `ShareExit` VO_35a (2D) · `FlowConst`: SHARE → VO_35b a PT 8 y VO_37 a 8 + VODur + 0,6; sin compartir → VO_37 a PT 8.
- Hall (`BP_HallDirector_SC.HallEnterIntro`): fuera VO_01d (el timbre va sin voz) y VO_06a.
- 🔴 Trampa del DSL: `(CallFunction|ObraSay "/Game/...")` con el literal **posicional** lo pone en el pin **self** y deja `Clip` vacío → "Accessed None ... Clip" en runtime. Arreglado con `set_pin_value` sobre `Clip` (y self en ''). Para funciones propias con parámetros: keyword `:Clip` o `set_pin_value`, nunca posicional.
- VO viejas que quedan sin uso (no borradas): 01d, 01h, 04b, 06a, 24, 34c, 35c, 36, 36c, 36d.
- **Sonido de carga (2026-10-01, pedido de Beltrán vía Breath):** función `ChargeSnd(K)`, llamada en `ChargeStart` justo antes de `RunCharge`. K < 4 → `ChargeFx.ChargeSound = Charge1` (11,4 s, golpe a 6,9 s; el ChargeFx lo dispara a 2,47 s → golpe a 9,37 s, cuando se va el anillo). K = 4 → `ChargeSound` vacío (el ChargeFx no toca nada a 2,47) y `ChargeFinal` (15 s, golpe a 10,5 s) con `PlaySoundAtLocation` **en t = 0 de la carga**, en el `ObraChargeTarget` (ya colocado frente al usuario; el ChargeFx en t = 0 puede seguir en su lugar viejo). Así lo armó Beltrán con la tabla de Breath (t = 0 en RunCharge: llenado 2,47→8,47, quieto hasta 10,97, fundido a negro 10,97→~13,97): el golpe marca el paso a negro. Los tiempos de la carga no cambian (manda el timeline).
- **Aviso inicial a 5 s (2026-10-01, Beltrán):** `DiscTime` 20 → 5 (CDO; la instancia no lo pisaba). `BP_Disclaimer_SC.DiscStep`: `Reveal` 0,5→2,0 (antes 3,5) · `Out` 3,5→4,8 (antes 17→19,5). Es el vacío negro donde irá el texto.
- **Puntos del Hall en la Obra (2026-10-01, pedido de Beltrán):** `DebugStart` 2-9 con el mismo mapa que `HallRunner`. `ObraDbgBoot` llama `ObraDbgHall(P)` antes de `HallStart`: fija `DbgHallStep`, pone `bTestIntro` y `TestFromStep` en el director y `TitleSt` 2 (sin título). `ObraDbgHallPost` (al inicio de `HallCheck`, cada cuadro) prepara lo previo (pawn a `StopInside` si ≥ 10; Alma al centro si ≥ 11; Alma al costado + sensor tomado si ≥ 13; almas y `ChosenSoul` = `DebugSoul` si ≥ 15; `bHudBorn` si ≥ 25) **solo cuando el director ya hizo su paso 0 y todavía no entró al pedido** (`Step == DbgHallStep − 1`). Hacerlo justo después de `HallIntro` no sirve: el paso 0 del director corre en su tick siguiente, te devuelve a la puerta (`hall_pawn`) y esconde a Alma. La misma trampa debe tener `HRPrep` en `HallRunner`. ✅ PIE: 3 → paso 6, timbre en su marca · 4 → paso 10, pawn en StopInside (−450,5; 0). 0 errores. Los puntos 2 y 5-9 no se probaron.

## 2026-10-01 (mañana) — correcciones de la prueba completa de Beltrán (plan: docs/PLAN-CORRECCIONES-2026-10-01.md)
- **Ambientes (A1):** `AmbTick(Dt)` (al comienzo de `TickAll`) suma `AmbAge`; cuando `AmbAge ≥ AmbLen − AmbFadeOut` llama `AmbTo(AmbNow)`: el mismo clip vuelve a entrar con FadeIn mientras el viejo sale con FadeOut (crossfade, nunca silencio). `AmbTo` guarda `AmbAge` 0 y `AmbLen` = `SoundBase.GetDuration`. `AmbVolumes` 0,6 → 0,38 (instancia).
- **Voz después de aparecer (A3):** `ObraSayLater(Clip, Delay)` + `SayPendingNow` (timer). `AlmaSpeak` usa Delay 1,5 y `AlmaTime = VODur + 3,5`; `StageTimes` asegura `AlmaTime ≥ VODur + 2,5`.
- **Voces de Attracting y Drawing (A2):** `StageCues` (TickAll) reinicia en la fase 4; en la fase 5, VO_27/VO_32 a 0,8 s y después VO_27d/VO_32d; en la fase 6, `CueAttract` (VO_28 al pasar el secuenciador a Phase ≥ 3, VO_27b con 3 esferas colocadas, VO_27h a 20 s sin ninguna, VO_27c a 75 s) y `CueDraw` (VO_32h a 15 s sin tinta, VO_32b a 40 s con tinta > 0,3, VO_32c a 60 s con tinta > 0,6). Nunca se pisan: `CueAt` = fin de la voz anterior + 0,6.
- **La fase 5 espera las instrucciones:** condición `(and (>= PT InstrTime) bInstrReady)`; `bInstrReady` = etapa < 3, o instrucciones dichas, o PT ≥ InstrTime + 20.
- **Tiempos:** título de etapa Reveal 0,5→1,8 · Out 4,6→5,6 · visible < 5,7 · Alma a 5,8 · Recognizing 180 s · velo de la última carga 8,6→10,9 (antes 2,47→9,97: oscurecía durante la carga) · `HallIntro` a PT 3 (antes 1) · título del inicio Out 12→14,5 y oculto a 15.
- **Aviso (A7):** `T_Disclaimer_SC` (Avenir Book, 2048×768) en `MI_Disclaimer_SC` (U0 0,08 / U1 0,92) · `DiscText` sort **32650** (estaba en 110, debajo del velo negro 32600: nunca se veía) · escala 2,13 × 0,8 · `DiscTime` 9 · `FlowDisc` lo pone frente a la cámara en sus primeros 0,3 s.
- **Manos (B1/B2) y háptico (B4):** `HandsTick(Dt)` en cada cuadro. Manos del pawn ocultas (`SetHiddenInGame`) según la línea de tiempo de Beltrán: en el Hall, desde el paso 13 (sensor tomado); en Entering, ocultas; en Heart, ocultas hasta la fase 7; en Loving, visibles hasta la fase 7; después, ocultas. `ChargeFx.MuteFeel` y háptico 0 en las fases 10-15 (salvo la 12). Paso del sensor del Hall a la herramienta: el `hall_sensor` se oculta 1,6 s después de que `UserTool.Mode` = 2.
- **Compartir (E2):** `ShareResOut` marca `ResOutT`; `ResultsOutK` (al final de `ResultsFade`) baja las K del cuadro a 0 en 0,8 s: se van los gráficos, no solo el marco.
- **Salida del Hall (A5):** `HallExitEarly` (al final de `HallCheck`): con el director en el paso ≥ 28 y el pawn en X ≥ 760 (pasó la puerta Este, en ~726), `DoneNow` → título de ENTERING al cruzar la puerta.
- **Manos, arreglo (09:00):** `HallGrabTick` lee el director del Hall con `IsValid` y escribe `HallGrabbed` (modo 1 y paso ≥ 13); `HandsTick` usa `HallGrabbed` en la fase 9. Antes el `GetActorOfClass` vacío daba "Accessed None" en cada cuadro fuera del Hall (lo vio Fantasmas a las 06:51).
- **Escala de Alma desde la Obra (C6), sin tocar BP_Alma_SC:** `TPOverA/B` copian también la escala del TP de la etapa a `ObraAlmaA/B`. `AlmaSclIn` (al final de `AlmaIn`) aplica la escala de `ObraAlmaA` de golpe. `AlmaSclAside` (al final de `AlmaAside`) fija `AlmaSclTgt` = escala de `ObraAlmaB`. `AlmaSclTick` (en `TickAll`) la lleva suave (Dt × 1,5). En el Hall (fase 9) y el final (≥ 10) el objetivo es 1. Los TP laterales están en 0,6 en las 5 etapas.
- **Vuelta al Hall (E1):** fase 11: el velo abre de 0,2 a 1,4 s (antes 0,8→3,8) y `ReturnCheck` espera PT ≥ 1,6 (antes 0,5) para soltar el pez y apagar el anillo. Así el desprendimiento se ve con el velo ya abierto. Antes saltaba al Hall con el velo todavía cerrado.
- ⚠ **E1, límite:** `M_ChargeRing_Frame_SC` y `M_ChargeRing_Light_SC` son **opacos**, y el velo (`M_TourVeil_SC`) es translúcido con `bDisableDepthTest`. El negro siempre tapa el anillo, sin importar el sort. Para que "el entorno se vaya a negro y el anillo no", el anillo necesita un material translúcido.

## 2026-10-01 (sesión Fantasmas, pedido de Beltrán vía Narrativa): las estrellas CRECEN
- `BP_Credits_SC`: `EventTick` → `CreditsStep` (sin cambios: sigue des-ocultando la estrella i a los i × 0,18 s) → **`StarsGrow`** (nueva).
  - `StarsGrow` guarda una vez (`StarsCacheGo`) las estrellas `CreditStar` y su escala del nivel.
  - Cada estrella va de 0 a SU escala en `GrowTime` 1,2 s, con 1 − (1 − t)³, empezando en i × `StarStep` (0,18; tiene que coincidir con `CreditsStep`).
  - Se apaga sola al terminar (`StarsDone`).
  - Si una perilla vale 0 (variables nuevas en una instancia ya colocada), usa 1,2 / 0,18.
  - Fuente: `scripts/credits/credits_stars.dsl`.
- ⬜ Verlo crecer en PIE o en el visor. No se pudo encender desde el MCP: `Run`/`CT` no son instance-editable y no hay comando de consola.
- ⚠ Visto en el PIE de 06:51: `HandsTick` → `Set HandsHid` lee un `GetActorOfClass` vacío en cada cuadro (cientos de "Accessed None").

## 2026-10-01 (10:40, Narrativa) — el anillo de la protoameba en el Hall y su vuelta al HUD (D7/D8)
Pedido de Beltrán: *"ya tienes la animación y el mesh; es hacer más rápida esa animación"*. Se reusa `BP_ChargeFx_SC` tal cual, sin tocarlo; su reloj se maneja desde la Obra.
- **`HallRing(Dt)`** está en `TickAll`, justo después de `HandsTick`, así su `MuteFeel` gana. Hace `IsValid` del director del Hall y llama a **`HallRingStep(Dt)`**, una máquina de estados en `HRState`:
  - **0 → 1.** En el Hall (fase 9, modo 1, pasos 15-23), cuando el alma elegida (`Souls[ChosenSoul]`) deja de viajar (o desde el paso 17):
    - el TargetPoint `ObraChargeTarget` va a la pose del alma, con escala `HallRingFit × Size × escala / (0,15 × BigScale)`: la misma proporción que en las cargas, con el hueco de 41 cm para un alma de 30 cm;
    - en el ChargeFx: `CavParam` "HallRingNone" (no carga ninguna cavidad), `HoldTime` 0 y `MuteFeel`;
    - `ApplySoulLook` y `BeginCharge`; el alma propia del anillo queda oculta (se ve la protoameba real);
    - suena `PopinSound`.
  - **1.** El "pum" de llegada (T 1,37 → 2,46) × `HallRingSpeedIn` 1,5.
  - **2.** Anillo quieto en T = 2,46: sin halo ni destellos. Sus 5 luces `Charge_<Etapa>` = `TileCur` del director, así encienden con las baldosas.
  - **3.** Arranca con `bHudBorn` (paso 24). Espera `HallHomeDelay` 0,3 s, porque el anillo del HUD se ve recién al 62 % de su entrada. Después corre la vuelta al nido de la carga (T = E → E + 2) × `HallHomeSpeed` 2, con los sonidos Warn, PopOut (y oculta la protoameba), PopIn en el nido y Settle. Al terminar: `EndCharge`, luces del anillo a 0 y `HoldTime` de vuelta a 2.
  - **4.** Terminado. Si se sale de la fase 9 con el anillo vivo, `EndCharge`.
- **Reloj:** `StepAll` del ChargeFx calcula T = ahora − `StartTime`. La Obra escribe `StartTime = ahora − T deseado` en cada cuadro, así que acelerar o congelar es solo aritmética.
- **Perillas (instancia, categoría "Hall - Anillo"):** `HallRingFit` 1 · `HallRingSpeedIn` 1,5 · `HallHomeSpeed` 2 · `HallHomeDelay` 0,3.
- ✅ **PIE (DebugStart 6, 0 errores):**
  - alma elegida a 58,4 s → anillo a su alrededor 4 s después (escala 2,0; Size 0,3);
  - paso 24 → vuelve al HUD en 1,3 s;
  - después: anillo del HUD en su pose de reposo (escala 0,098, misma posición que en el editor), ChargeFx con `Running` false, `HoldTime` 2 y `MuteFeel` false.
- ⬜ Falta verlo en el visor.

## 2026-10-01 (11:00, Narrativa) — la última carga termina y RECIÉN ahí el entorno se va a negro (E1, pedido de Beltrán)
- **Tiempos (con `ChargeTimes[4]` = 6):**
  - la carga llena la cavidad de 2,47 a 8,47 s;
  - `FlowVeil` fase 8, etapa 4: velo de **9,5 → 11,5 s** (antes 8,6 → 10,9; 0,13 s después de llenar se leía como "se va a negro mientras carga"). Literales 8,6 → 9,5 y 4,9 → 5,5 (en un `MakeLiteralFloat`);
  - `ReadCharge`: la etapa 4 sigue ocupada mientras PT < 5,6 + C = **11,6** (antes 4,97 + C), así `FinalStart` llega con el negro completo.
- **Negro del ENTORNO, no de todo:** `FinalLook` (ChargeFx) pone al anillo los materiales del HUD (DDT translúcidos) con sort **32610**, y llama a `TopSorts(true)`. Todo queda sobre el velo (32600) y bajo el aviso (32650) y los títulos (32700):
  - destellos 32612/32613;
  - anillos de etapa 32614-32618;
  - halo 32606;
  - el alma con **`MI_ChargeSoulTop_SC`** (`MI_ChargeSoul_SC` sobre `M_ProtoSoul_HUD`, DDT) a 32608, para que los trazos del dibujo no la corten en el negro.
- `NormalLook` → `TopSorts(false)` devuelve sorts (0 / 210-216) y `MI_ChargeSoul_SC`.
- Como cambia el material del alma, **`ApplySoulLook`** se llama ahora también después de `FinalLook` en `FlowFinal` y después de `NormalLook` en `ResultsShow`. `FinalStart` ya lo hacía.
- **Bug de fondo:** los dos `SetMaterial` del anillo en `FinalLook` tenían el material vacío (gotchas §561), así que el look del final nunca se había aplicado.
- ✅ **PIE (DebugStart 60, 0 errores):**
  - "final, a negro" 11,59 s después de arrancar la carga;
  - en el regreso, el anillo tiene sus MID de los materiales HUD y sort 32610, y el alma `MI_ChargeSoulTop_SC` a 32608;
  - en los resultados todo vuelve: materiales normales, sorts 0/210/216 y el alma con sus colores.
- ⬜ Falta verlo en el visor.

## 2026-10-01 (12:50, Narrativa) — 4 arreglos de la prueba de Beltrán en el visor
- **Breath corrido (grave):** la salida temprana del Hall (`HallExitEarly`, pawn x ≥ 760 en el paso ≥ 28) mandaba a Entering, pero el director del Hall seguía en el paso 28 con `HallTickWalk` moviendo al pawn por la caminata de salida (`OutTime` 8 s). El usuario quedaba lejos del título, del metaball y de Alma.
  - Arreglo: **`HallCutWalk`**, llamada una vez al cruzar. Pone `WalkT = WalkDur` en el director, `bWaitWalk` false y `bGate` true, y hace `Stop` de `StepsAudio`.
  - PIE (DebugStart 9): 4 s después del cruce el pawn sigue en `StartLoc[0]`, y el director cierra solo (paso 30, `bHallDone`); 0 errores.
- **Aviso al costado:** `FlowDisc` pegaba el aviso a la cámara solo con PT < 0,3; en el Quest la orientación del casco al arrancar todavía no es la final. Ahora se pega a la cámara con PT < 0,8 (aún invisible) y después la sigue suave (`RInterpTo` 1,5), siempre a la altura y posición del ojo.
- **Drawing tarda en dejar dibujar:** `bInstrReady` ahora se cumple al EMPEZAR la segunda instrucción (VO_27d / VO_32d), no al terminarla (literal `CueAt − 0.6` → `CueAt − 60`). Unos 7 s menos en Drawing y 5 en Attracting.
- **Timbre y sensor negros:** materiales (ver `references/materials-vr.md`).
### 2026-10-01 tarde — perillas y funciones nuevas
- Perillas: `Final` → `ResAlmaLeft` 45, `ResAlmaScale` 0,7, `SketchSpeed` 20 °/s; `Hall - Anillo` → `HallSoulScale` 2. Internas: `SketchYaw`, `SketchOff`, `SketchOn`, `HallBigDone`.
- `SketchSpin(Dt)` (fase 12: re-`PlaceSketch` con yaw creciente) y `HallSoulBig()` (fase 9, una vez: escala el punto `hall_soul_present`) se llaman al final de **`AlmaSclTick`** (que corre en cada `TickAll`).
- `AlmaSclTick`: objetivo 1 en fase 9 y ≥ 10, **salvo la 12** (resultados usa `AlmaSclTgt`, que fija `AlmaResults`).
- `StageTimes`: sin `StAlma`; `AlmaTime = VODur + 3`; K = 4 → `InstrTime 0,6`. `StageCues`: aviso 1 en fase 5 o 6; `bInstrReady` verdadero en la etapa 4. `ResultsOutK`: fase ≥ 12.

### 2026-10-01 (después de la visita) — zurdos, ameba del Hall y perillas en 0
- 🔴 **Perillas nuevas instance-editable nacieron en 0 en la instancia del nivel** (`HallSoulScale`, `ResAlmaLeft`, `ResAlmaScale`, `SketchSpeed`): la ameba del Hall se escalaba a 0 (desaparecía) y Alma quedaba en tamaño 0 en resultados. Arreglado: valores escritos en la instancia y nivel guardado. **Quitados** `HallSoulBig`, `HallSoulScale` y `HallBigDone`: Beltrán ya había agrandado `TP_hall_soul_present` a mano; esa escala manda.
- **Zurdos** (`HandTick`, llamada desde `AlmaSclTick` en cada tick):
  - `HandRead` copia `Hall.bRightHanded` (lo fija `HallGrab` con la mano que toma el sensor) a `UserRight` mientras el Hall está cargado.
  - Si `UserRight` es falso, una vez por etapa (`HandK`, reset en fase 0 y 9):
    - Entering, fase 4 (antes del Intro): `HandBreath` → `UserTool.bRight` y `bMounted` en falso, y `BreathRig.SetHandedness(false)`. Va antes porque duerme el rig.
    - Attracting, fase ≥ 5 (después del Intro): `HandSeq` → `SeqRig.SetHandedness(false)`.
    - Surrounding, fase ≥ 5 (después de `TourWake`): `HandDraw` → `TBDirector.SetHandedness(true)`.
  - Heart ya era ambidiestro (`bAutoHand`). Los diestros no cambian nada.
  - ⬜ Sin probar en visor.

### 2026-10-01 noche — fantasmas de instrucciones conectados (`GhostTick`)
- **`GhostTick`** (llamada al final de `AlmaSclTick`, cada cuadro): recorre los `BP_GhostPlayer_SC` cargados y, por el nombre de su `Take` (`DA_Ghost_*`), decide si debe estar en marcha.
  - Si debe y no lo está: `Play(Mirror = not UserRight)`.
  - Si no debe y lo está: `Stop()`.
- **Hall** (`GhostHall`, fase 9), con las banderas del director:

  | Fantasma | Bandera |
  |---|---|
  | `DA_Ghost_Bell` | `bBellLive` |
  | `DA_Ghost_Take` | `bSensorLive` |
  | `DA_Ghost_Pick` | `bPickLive` |

- **Etapas**: en fase 6 (después de `StageBegin`) y hasta la primera acción (`GhostFirst` → `GDoneK`):

  | Etapa | Primera acción |
  |---|---|
  | Breath | `BreathRig.bZone` |
  | Heart | `HeartManager.bHeartZone` |
  | Attract | `Sequencer.Phase ≥ 2` |
  | Draw | `TBDirector.InkUsed > 0` |

  Fuera de la fase 6 se apagan solos. `GDoneK` se resetea en las fases 0 y 9.
- **Perilla** `bGhostsOn` (categoría *Instrucciones*, instance-editable, true): apaga todos los fantasmas.
- Variables internas: `GBell`, `GTake`, `GPick`, `GDoneK`.
- ⬜ Faltan los fantasmas COLOCADOS en sus celdas (Animaciones), el PIE y el visor. Los fantasmas van mudos (pedido de Beltrán: suenan junto con el VO).
- ✅ **2026-10-01 noche:** Animaciones colocó los 7 fantasmas (`Ghost_<ID>`, carpeta *Fantasmas*):

  | Nivel | Fantasmas |
  |---|---|
  | Test_Hall | BELL, TAKE, PICK |
  | Test_Breath | BREATH |
  | Test_Heart | HEART |
  | Test_Sequencer | ATTRACT |
  | Test_Draw | DRAW |

  Todos con `bShowText` false, `bAutoPlay` false y sin sonido.
- PIE con `DebugStart` 3, 0 errores: el Hall llega al paso 6, coloca el timbre y en ese cuadro arranca `DA_Ghost_Bell`, que sigue al timbre real (`FollowTag`), en bucle. TAKE y PICK quedan quietos.
- PIE con `DebugStart` 12, 0 errores: con `StageBegin` (fase 6) arranca `DA_Ghost_Breath` (State 2, en bucle). El resto, quietos. Las 7 celdas cargan juntas sin choques de tags.
- La Obra quedó guardada con **`DebugStart` 3** (el timbre), por pedido de Beltrán, para verla. 🔴 **Antes de empaquetar: `DebugStart` −1.**

### 2026-10-01 noche — correcciones de Beltrán tras probar los fantasmas
- **Ambientes sin silencios.**
  - Causa: `AmbPick` devuelve −1 en varios momentos (arranque, puerta Este, fases finales) y `AmbTo(-1)` hacía `AmbFade` sin arrancar otro, así que el ambiente se apagaba hasta el siguiente.
  - Ahora `AmbTo` trata `K < 0`, y también `K ≥ 1` en fase ≥ 15, como "seguir con el actual": restituye `AmbNow = AmbLast`.
  - El bucle consigo mismo (`AmbTick`) se mantiene, con 3 s de fundido de entrada y 3 s de salida.
  - Variable nueva: `AmbLast`.
- **Final:** en fase ≥ 15, `AmbTick` funde la música (`AmbTo(0)`), y el velo ya iba a negro. A los 3,5 s, `OpenLevel`.
- **Recentrado:** al final de `HallStart`, `BP_VRPawn_SC.RecenterSeated`. Así, después de un reinicio el visor cae en el pawn aunque el usuario se haya movido. El pawn ya lo hacía en su `BeginPlay` (0,5 s), pero al recargar en el Quest no alcanzaba.
- **Alma en el Hall con la escala del TargetPoint:**
  - `AlmaHallScl` lee una vez los 3 puntos (`hall_alma_center` / `hall_alma_side` / `hall_alma_exit`: posición y escala X, en `HCL`/`HSL`/`HEL`, `HCS`/`HSS`/`HES`).
  - En cada cuadro de la fase 9, toma la escala del más cercano a Alma (`AlmaHallTgt`).
  - `AlmaSclTick` ya no fuerza 1 en el Hall. En `hall_alma_side` está 0,5 (Beltrán).
- **Dibujo de resultados:**
  - Causa del giro desbocado: `PlaceSketch` asume que el dibujo está en su origen; llamado en cada cuadro, componía la rotación y se acumulaba.
  - Ahora `SketchSpin` aplica cada cuadro un delta: `MakeTransform(p − R·p, R)` con `R = yaw(SketchSpeed·Dt)` y `p` = el centro donde lo dejó `PlaceSketch`. Va por `TBTool.SketchApplyXf`, como el giro del final de Drawing, a 20 °/s.
- **Test_Hall:**
  - las amebas pasan a 27 cm entre sí (antes 19), con Y = ±27 y ±54;
  - `TargetPoint_4` (`hall_soul_present`) a escala 0,7 (era 0,3; la ameba copia la escala X del punto como `Size`).
- **Ambientes por etapa (Beltrán, 10-01 noche).** `AmbPick` reescrito limpio, sin `bind` de literales:

  | Momento | K |
  |---|---|
  | Hall | 1 → 2 → 3 (−1 al abrir la puerta Este) |
  | Breath | 4 |
  | Heart | 5 |
  | Mind | 6 |
  | **Attracting** | **8 (Salida)** |
  | **Drawing** | **7 (Surrounding)** |
  | Fase 10 | −1 (sigue el de Drawing) |
  | **Fases 11-14** (Hall de salida, resultados, créditos) | **9 (Credits)** |
  | Fase 15 | funde a 0 |

  El `AmbientSound_0` (*Ambient_Surrounding*, Clip 7) de `Test_Draw` pasó a `TestOnly`: en la Obra se descarta (`TestOnly descartados` 19 → 20) y en su nivel de test sigue sonando. Antes se sumaba al de la Obra. PIE con `DebugStart` 50: "ambiente 7", 0 errores.
- **Tiempos del arranque (Beltrán, 10-01 noche):**
  - `DiscTime` 9 → **19** s (CDO; no es instance-editable).
  - En `BP_Disclaimer_SC.DiscStep`, la salida del texto (`Out`) pasó de 7,6-8,7 a **17,6-18,7** s. Estaba fija en segundos: si se cambia `DiscTime`, hay que correrla también.
  - En Test_Hall, `BP_HallDirector_SC.IntroHold` 12 → **17** s (título y logos antes de caminar).
  - **`DebugStart` −1**: la Obra arranca desde el negro, igual que en el APK.
  - En `IntroTitle` (título y logos del inicio), corridos +5 s junto con `IntroHold` 17: `Out` 12-14,5 → **17-19,5** s (los 3 `MapRangeClamped`) y se ocultan a los **20** s (2 `MakeLiteralFloat`; antes 15). También estaban fijos en segundos.
