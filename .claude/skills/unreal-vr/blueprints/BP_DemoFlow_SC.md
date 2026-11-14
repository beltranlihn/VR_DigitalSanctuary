# BP_DemoFlow_SC — el director de cada experiencia de la demo (guion v2, 2026-10-19)

- **refPath**: `/Game/SoulCharger/Demo/Blueprints/BP_DemoFlow_SC` · parent Actor (+ `Veil` esfera `M_TourVeil_SC`, `Title` plano con el MI del título) · creado 2026-10-19 (sesión Director, guion de Beltrán).
- **Colocado en**: `L_Demo_Breath` (`Exp` 0) y `L_Demo_Draw` (`Exp` 1), label `DemoFlow`. **Reemplaza** en esos niveles a `BP_StageRunner_SC` y `BP_DemoInstr_SC` (sacados de los niveles) y a la Alma de ensayo.
- **Fuente**: `VR_Test/Saved/ClaudeScripts/Demo2/flow_dsl.py` → `dump_codes.py` → escritor genérico (`writer_mcp.py`). Respaldo de los niveles antes del cambio: `VR_Test/Saved/Backup/Demo_2026-10-19_1600/`.
- **Estado**: 🟢 Breath y Draw de punta a punta en `-game` (perillas de prueba), 0 errores · 🟢 robot (receptor) siguiendo al Quest falso · ⬜ visor.

## Fases (`Phase`, reloj `RT` y `PT`, `Dt ≤ 1/30`)
| Fase | Breath (`Exp` 0) | Draw (`Exp` 1) |
|---|---|---|
| 0 | velo abre + título (tiempos = `DA_Partitura_Demo`: velo 1→4, título 0,5→5,7) · `StageEnv` a 0,1 s · a `PanelAt` (6 s) `ShowPanel` | igual, sin `StageEnv` |
| 1 | página 1: el sensor (`BP_BioSensorArt_SC`, tag `demo_pedestal`) flota a `ReachFwd` 48 / `ReachDown` 28 de los ojos; **se toma con la mano a < `TouchRadius` 14 cm** (valores del Hall) → `Grab` | página 1: el mando (`BP_QuestCtrl_SC`, tag `demo_pedestal`) |
| `Grab` | `UserTool.ShowMando(R)` + `ToSensor` (el sensor aparece luz primero en esa mano y la mano se esconde) · `BreathRig.SetHandedness` · `SeqRig.SetRightHanded` | `TB.SetHandedness(!R)` + `TB.StageIntro` (mesa, punta, paleta en la otra mano) |
| 2→3 | página 2 + `BreathRig.SetRigActive(true)` · avanza con `bZone` 1,5 s seguidos | página 2 + `TB.StageBegin` (se puede dibujar) |
| 3→4 | página 3 (círculo que sigue la respiración en la imagen) · avanza con `Breaths` (2) respiraciones (`BreathSigned` < −0,3 → > 0,4) o `BreathWait` 30 s | trazo de práctica: `InkUsed ≥ PracticeM` (1 m) y sin dibujar → `SetStageLock(true)`, `PracticeCut` |
| 4→5 | página 4 + botón START (`demo_go`) + láser (`ResultsBeam`, `SaveHands`) | los trazos se achican 0,8 s → `UndoAll` (`UndoLast` × N) + `InkUsed` 0 + se va el panel + `VO_DD1` + reloj |
| 5 | `PickGo` (hover + clic) | reloj: `Kit.TimeLeft = DrawTime − TimerT`; a `DrawTime` (150) → `TB.StageRequestEnd` (guarda y presenta); por tinta, igual |
| 6 | se van START y panel, `ResultsBeam(false)`, `RestoreHands` | presentación: con `SketchPhase ≥ 3`, a `SpinTurnsT` (10 s) `ShiftStart` (el dibujo se corre `ShiftCm` 160 a la derecha) + `VO_DD2` → 15. Sin dibujo: directo a 15 |
| 7-10 | `StageIntro` + `VO_DB1` · `StageBegin` · `VO_DB2` a `ExploreTime − 3,2` · tope `TopeS` 170 → `StageRequestEnd` · `bStageDone` → `StageOutro` · `VO_DB3` | — |
| 15 | al terminar la voz: `Kit.HudPlop` | igual |
| 16-17 | `Results.ResShow` · `ResultsHold` 35 s → `ResHide` | igual |
| 18-19 | velo a negro (2,5 s) + `Amb.FadeAll` → `OpenLevel(MenuLevel)` | igual |

## Perillas (instance-editable)
`Exp` · `CTop`/`CHor` (colores del velo = los del ensayo viejo) · `TitleMI` · `TagTitle` (`sc0_title`/`sc4_title`) · `EyeRef` 120 · `MenuLevel` · `VeilA0/A1`, `TitleR0/R1`, `TitleO0/O1`, `TitleHide` · `PanelAt` 6 · `TopeS` 170 · `DrawTime` 150 · `PracticeM` 1 · `ResultsHold` 35 · `ReachFwd`/`ReachDown`/`TouchRadius` · `SensorColor` · `Breaths` 2 · `BreathWait` 30 · `SpinTurnsT` 10 · `ShiftCm` (Draw 160) · `Vo1/Vo2/Vo3` · **`Pages`** (MI del texto por página, slot 1 de la placa) · **`Images`** (MI de la imagen por página, slot 2) · `WinRingMat` (slot 3, la cinta de la ventana) · `Black`.
**Prueba** (🔴 en 0/false en el APK): `AutoHand` (1 derecha / 2 izquierda: toma sola a los 2 s) · `AutoGo` (N s: las páginas avanzan solas y aprieta START) · `bTestSynth` (Draw: trazo sintético `DbgSynth`).
**Robot**: `RemotePhase` / `bRemoteRight` los escribe `RemoteSync` leyendo `BP_MirrorLink_SC.RStF` (slots 2 y 3) cuando el enlace es receptor; con `RemotePhase` mayor, el robot toma con la misma mano, pasa páginas, aprieta START, corta la práctica y pide el cierre.

## Trampas de esta construcción
- `BP_BreathStage_SC` encadena sus voces (en la demo, silencio) desde `ToolDelay` + `SayAfterTool`: con `ToolDelay` 9999 la exploración no terminaba nunca (sin cuenta ni pacer). `ToolDelay` 0,8 y es inocuo: `ToSensor` con el sensor ya puesto no hace nada (`ToolApply` solo aplica si cambia el modo).
- `bAutoStart` de la etapa en **false** en `L_Demo_Breath` (con true arrancaba el flujo viejo sola a los 1,5 s).
- `Utilities|IsValid` es una macro con ramas: después no puede haber código ("Unreachable code") → una función por `IsValid` (`GoAdjust`, `EnsureHands`, `RemoteSync`).
- Las variables nuevas de un BP no aparecen en el catálogo de nodos de OTROS BPs hasta reiniciar el editor (gotcha 436): por eso el robot no escribe en el director, el director lee al enlace.
- `Get(acopy)` sobre un arreglo vacío deja un warning de Blueprint: `Go` se busca con `Length > 0`.

## 2026-10-19 (noche): revisión a fondo — tiempos límite, robot y arreglos
Fuente: `VR_Test/Saved/ClaudeScripts/Demo2/flow_dsl.py` (respaldos `flow_dsl_backup_1730/1800/1840.py`).
- **Tiempos límite** (variables editables, CDO): `GrabWait` 25 (toma sola con la derecha), `ZoneWait` 30 (pág. 2), `GoWait` 60 (START solo), `PracticeWait` 45 (corta con lo que haya, también 0 trazos). Ya estaban `BreathWait` 30. Topes fijos: Breath `:9` cierra a `TopeS + 30` aunque la etapa no responda; Draw `:5` pasa a resultados a `DrawTime + 30` tras pedir el cierre; `:6` se corre a `2 × SpinTurnsT` aunque el giro no avance. La prueba "nadie hace nada" = `probar_nivel.py` con los valores de público.
- **`ShiftStep` no movía el dibujo**: `_d` es un `bind` puro con `ShiftK` adentro y se re-evaluaba DESPUÉS de `SetShiftK` → traslación 0 (gotcha 409). `SetShiftK` va al final.
- `SpinTurnsT` 10 → **12** (2 vueltas a `SpinSpeed` 60).
- Trazo de práctica: se achica hacia **su centro** (`StrokeCen` = origen de `GetActorBounds`; los trazos viven en el origen del mundo con los vértices en coordenadas de mundo, y antes volaban hacia (0,0,0)).
- `PsYaw` (yaw del PlayerStart) en `FBoot`; `ShowPanel` y `ShiftStart` lo usan (antes asumían yaw 0/180).
- **Robot**: `RobotMode` (sin `OpenLevel` al final: el nivel lo cambia el enlace), `MLink` cacheado en `FindLink` (antes `GetActorOfClass` por cuadro), **`RobotHold`**: con el enlace en modo receptor y sin pose (`GetPoseReady` false) no corren `RT`/`PT` → el título y el panel se ubican con la cámara real cuando el Quest aterriza.
- 🔴🔴 **Después del trazo de práctica no se podía dibujar** (encontrado 19-10 18:35 con el robot; afectaba igual al Quest): `SetStageLock(true)` en `:3` hace que `BP_TBDirector_NC.ContractLock` llame `DisableInput`, y `:4` solo ponía `StageLock` en false → la entrada del director quedaba apagada los 2:30. Lo único que la reabre es **`StageBegin`** (→ `InstallInput`: `EnableInput` + `IMC_TB_Draw_R` + `IMC_Weapon_*`), así que `:4` llama `StageBegin` de nuevo. Las pruebas viejas no lo vieron porque `bTestSynth` dibuja sin pasar por la entrada. Probado: el robot dibuja en la sesión con el gatillo inyectado (`cierre_draw`).
- El corte de la práctica por `PracticeWait` (o por tinta) espera a que no haya trazo en curso (`GetDrawing`): cortar con el gatillo apretado dejaría el trazo huérfano (`UndoLast` no hace nada si `bDrawing`). El robot corta igual cuando el visor ya cortó (`RemotePhase` ≥ 4).
- `LogPivot`: registra el pivote del dibujo al correrse y al aparecer los resultados (probado: Y 0 → 160). El dibujo se presenta a ~5,5 m al frente y 1,5 m bajo los ojos (lo decide el director del dibujo).
- En el robot, al final (`EndTick :3`) imprime `DEMOFLOW: robot espera al visor (no abre el menu)`: el menú lo abre `LevelStep` cuando el visor cambia de nivel.

## 2026-10-20 — prueba de Beltrán en Unreal
- 🔴 **En Draw la paleta y el mando aparecían al cargar el nivel**: `BP_TBDirector_NC.TourBegin` duerme solo si hay un actor con tag `TOUR` o `bForceTour`; la etiqueta la traía el ensayo viejo (`BP_StageRunner_SC`, tags `TestOnly` + `TOUR`) y se fue con él el 19-10. Ahora `bForceTour` true en el `TBDirector` de `L_Demo_Draw` (la guardia lo exige): duerme hasta el `StageIntro` de `Grab`. Verificado en PIE: `bTourMode` true, `bAwake` false, `bReady` false a los 4 s. (No se usó el tag `TOUR`: también duerme al `BP_SeqRig_SC`.)
- `Grab`: háptico `GrabHapticEffect` (el del XRFramework, el mismo del SeqRig) en la mano que toma.
- Prueba (20-10): `TopeS` 30 (Breath) y `DrawTime` 30 (Draw) en las instancias; la guardia no deja cocinar así.

## 2026-10-20 (tarde) — después de que Beltrán probó Draw ("va súper bien")
- **Háptico = el de la Obra**: `Grab` y `PickGo` llaman `BP_SeqRig_SC.Pulse(bRight)` (`PlayHapticEffect` + `GrabHapticEffect` al PlayerController, el patrón del timbre; `docs/MECANICAS-PORTABLES.md` §4.9). No usar `SetHapticsByValue` para pulsos: pisa el canal.
- **`PedSpin`** (en `GrabStep`, fase 1): el objeto que flota gira `SpinDeg` (30°/s) y sube y baja `BobCm` (1 cm) sobre `PedBase` (se guarda en `ShowPanel`).
- **`SayPage`** (en `FPanel`): voz de la página, `PageVo[Page]` (instancia: Breath `VO_IB1-4`, Draw `VO_ID1-2`). Breath `:3` y `:4` avanzan solos solo si no hay voz (`not Speaking`); los tiempos límite no esperan.
- **Final de Draw**: `:6` llama `HandsBack` a los `OutroTime` s (el director ya sacó los mandos; `HandsBack` pone `bHidePawnHands` false en el director y muestra las mallas de mano del pawn). Al correrse el dibujo: `ShiftStart` + `VO_DD2` + `HudPlop` + `ResShow` en el mismo cuadro → fase 17 (se saltean 15 y 16). Sin dibujo (`:5`): `TB.StageOutro` + `HandsBack`. `ShiftStep` corre también la mesa (`MoveTable(D)`, la `DrawTable` de la herramienta), antes de `SetShiftK`.
- Variables nuevas: `PedBase`, `SpinDeg`, `BobCm`, `bHandsOn`, `PageVo` (fuente `Demo2/flow_dsl.py`, cambios en `edit_flow_1020b.py`, respaldo `flow_dsl_backup_1020b.py`).
- Probado en `-game` con toma automática y trazo sintético (después devueltos): Draw y Breath completos, voces de página, manos de vuelta, HUD + resultados + corrimiento en el mismo cuadro, corte a 30 s; 0 errores.

## 2026-10-20 (tarde) — Heart, la tercera experiencia (`Exp` 2, `L_Demo_Heart`)
- **`HeartTick`** (fases seguidas 0-6: el switch del DSL NO admite saltos de número, `write_graph_dsl` falla con "Unknown exec output"): `:0` a los 0,1 s `HM.TourSleep` + `ScapeGo(0)` (solo el mar) · `ShowPanel` · `:1` `GrabStep` · `Grab` (rama `Exp` 2): sensor del pedestal se va, `UserTool.ShowMando`/`ToSensor(SensorColor)`, `HM.bAutoHand` false + `bRightHand`, **`HM.StageIntro`** (la esfera sale del agua, sensor rojizo) · `:2` página 1 + **`HM.StageBegin`** · `:3` avanza con `HM.bHeartZone` 1,5 s (sin voz) / `ZoneWait` / `AutoGo` / robot ≥ 4 · `:4` página 2 → al terminar su voz se va el panel · `:5` el latido: `VO_DH1` (Vo1) al primer pulso, `VO_DH2` (Vo2) en `OrbitAtBeat`, tope `TopeS` → `StageRequestEnd`; `bStageDone` (o tope + 30) → `StageOutro` · `:6` `VO_DH3` → 15 (cierre común).
- Variables nuevas: `HM` (BP_HeartManager_SC), `bSaidH1`, `bSaidH2`. `FBoot` busca `HM`; `ShowPanel` prepara el sensor que flota también en `Exp` 2.
- Sin Alma en el nivel, el `StageVO` del manager queda en silencio (su `AlmaCheck` nunca la encuentra): las voces las dice este director.
- 🔴 El catálogo de nodos no ve las funciones de `BP_HeartManager_SC` hasta que algo del BP lo referencia: agregar primero la variable `HM` y compilar, recién después `find_node_types`/`write_graph_dsl`.
- Probado en `-game` (toma y avance automáticos, después devueltos): páginas con voz, `StageIntro`/`StageBegin`, latido de respaldo a los 30 s sin mano, `VO_DH1`, tope 30 s, `StageOutro`, `VO_DH3`, plop, resultados; 0 errores. Fuente: `Demo2/edit_heart_1020.py` sobre `flow_dsl.py`.
- (revisión) `HandsBack` ya no exige el director del dibujo (IsValid al final) y lo usan los tres: Draw a los `OutroTime` s, Breath y Heart en la fase que sigue al `StageOutro` (1,2 s). Breath `:9` llama `UserTool.Release` (Heart lo hace el manager). Breath `:4`: `Rig.SetRightHanded(!Right)` antes de `ResultsBeam` (láser en la mano libre); `PickGo` vibra la mano del láser. Heart: `VO_DH2` además pide `StageT ≥ 10`. Fuente `Demo2/edit_review_1020.py`.

## 2026-10-20 (noche) — tras la prueba de Beltrán (fuente `flow_dsl.py`, scripts `edit_flow_1020t.py` + parches; respaldos `flow_dsl_backup_1020t/1020n.py`)
- Variables nuevas: `bPulsePend`, `TiltDeg` (28, editable), `PedYaw`, `HeartPulses` (3, editable), `FigZ`. CDO: `SpinDeg` 40, `BobCm` 2,5. Función nueva `HeartFig`.
- **Háptico al tomar**: `Grab` ya no llama `SeqRig.Pulse`; marca `PulsePend` y `FlowTick` dispara el pulso a PT ≥ 0,12 s. En el mismo cuadro `HeartManager.StageIntro`→`TourSleep` y `BreathRig.SetHandedness` ponen `SetHapticsByValue` 0 en las dos manos y se comían el pulso.
- `Grab`: el objeto que flota se esconde en el acto (`SetActorHiddenInGame`), sin la animación de `AppearLuz`.
- `PedSpin`: rotación absoluta (yaw `PedYaw` + `SpinDeg`·PT, roll/pitch `TiltDeg`·sin; en Draw ×0,35) + `BobCm`.
- `FVeil`: `_lt` = RT (se fue el salto de 3,5 s a los 5,5 s que cortaba el título); el título lo gobiernan `TitleO0/O1/TitleHide` del nivel (8 / 9,3 / 9,4) y `PanelAt` 9,8. Piso del velo (`Floor`) en 0 al cerrar a negro (fase ≥ 18).
- Breath sin START: :4 página 3 → :5 espera la voz (≥ 2,5 s, tope 25 s, robot `rp` ≥ 6) → :6 se va el panel → :7 muestra metaball y guía (escondidos desde `FBoot`) + `StageIntro`. `PickGo` queda sin uso.
- Heart fases 0-5: :2 página 1 + `StageBegin` (+ `ScapeGo 0`: la esfera sigue abajo) · :3 `HeartFig` hasta `BeatCount ≥ HeartPulses` (o `ZoneWait`, robot `rp` ≥ 4) → se va el panel + `ScapeGo(Max(1,0))` (el 1.0 cableado: un literal a función propia se pierde) · :4 etapa (tope robot `rp` ≥ 5) · :5 cierre. `Grab` en Heart hace `StageIntro` + `ScapeGo 0`.
- Probado sin visor: Breath completo (página 3 → panel se va → `StageIntro` → `StageBegin` → cierre), Heart hasta la página 2 con `StageBegin`; 0 errores de Blueprint.

## 2026-10-20 (noche, 2.ª tanda) — sin click al cambiar de nivel
- Variable `MasterMix` (SoundSubmix, CDO `/Engine/EngineSounds/Submixes/MasterSubmixDefault`).
- `FBoot` arranca con `SetSubmixOutputVolume(MasterMix, 1)`: el nivel anterior lo dejó en 0.
- `EndTick` fase 18 (negro): rampa del maestro 1 → 0 en 3 s y el menú se abre a los **4 s** (antes 3: el `FadeAll` de la música todavía sonaba y el `OpenLevel` lo cortaba = click).

## 2026-10-21 (noche) — arreglos de Beltrán (`docs/demo/ARREGLOS-2026-10-21.md`)
DSL: `Saved/ClaudeScripts/Demo2/flow_dsl.py` (respaldos `flow_dsl_backup_1021{n,p,q,r}.py`). Variables nuevas creadas con `Test_QuestCtrl` abierto (las instancias de los niveles nacen con el valor del CDO).
- **FINISH (4)**: `Fin` (BP_ShareButton_SC) + `bFinDone`. `FinSpawn` (una vez) · `FinShow` (150 cm al frente, 42 cm abajo, pitch 15, MI `MI_DemoBtn_PlateTopFinish_SC` = `T_Finish_Text`; `Appear` + `ResultsBeam` true) · `FinPick` (hover = `BeamHitActor == Fin` y `AppearT ≥ 0,999`; clic = cambió `ResPressN`). `EndTick :1` y `DrawTick :6` llaman `FinShow` después de `ResShow`; `EndTick :2` cierra con el tiempo **o** `bFinDone` (mismo cierre: `ResultsBeam` false, `Vanish` de FINISH si no se apretó, `ResHide`, negro, menú).
- **Heart, dos poemas (11)**: `bSaidH3/H4`, `Poem1At` (CDO 60) / `Poem2At` (100), instance-editable. Fase 6: `VO_DH4` a `Poem1At` s de etapa (después del primer pulso, sin voz sonando), `VO_DH5` a `Poem2At` (después del primero, antes del pedido de cierre). Rutas de los clips escritas en el grafo.
- **Heart, polvo más amplio (1)**: fase 0 (con el entorno) → `BP_HeartDust_SC.StaticMeshComponent.SetStaticMesh(SM_HeartDust_Demo_SC)`. La Obra sigue con `SM_HeartDust_SC`.
- **Breath, breathwork (12)**: `Pacer` (ref), `LastPh` (int, CDO −1), `bSetF1/F2`, `bSaidCount`, `bSaidNat`, perillas `FinIn 5 · FinHold 3 · FinEx 10 · FinEmpty 5 · SighIn 5 · SighEx 6`.
  - Fase 8: guarda el pacer y pone las banderas en cero. Fase 9: `Vo2` (la explicación) a `ExploreTime − (Vo2.Duration + 0,8)` · la cuenta `VO_DBC` cuando la etapa pasa a su fase 12 · `BreathCue` cada cuadro.
  - **`BreathCue`**: con el pacer corriendo, al empezar el ciclo `Cycles − 2` → `PacerSetTimes(FinIn, FinHold, FinEx, FinEmpty)`; al empezar el `Cycles − 1` → `PacerSetTimes(SighIn, 0, SighEx, 0)` (el inhalar dura lo mismo en los tres patrones: el cambio no salta). Cambio de `CurPhase` → `BreathSay`. Cuando el pacer para después del último patrón → `VO_BF6`.
  - **`BreathSay`**: por fase (0 inhalar · 1 sostener · 2 exhalar · 3 sostener 2) y ciclo; una retención de < 0,05 s no habla; el primer inhalar lo dice la cuenta.
  - La etapa (`BP_BreathStage_SC` de `L_Demo_Breath`) quedó muda: `bCycleVO` false, `CountSound` = `SND_Demo_Silence` (0,1 s), `InhaleCueAt` 2,37 (= "inhale" en `VO_DBC`), `CountTime` 2,5, `ExploreTime` 30. Pacer de la instancia: 5-3-8-0, `Cycles` 7, pads `SND_PacerPad{Inhale,Exhale}_Demo`.
  - ⚠ La lectura del DSL rotula `GetDuration` como `Components|GeometryCache` y `GetPhase` de la etapa como `Variables|Default`: `get_node_infos` confirma `self` = SoundBase y BP Breath Stage SC.
- **Nitidez (2)**: `RenderPct` (instance-editable, CDO 100) + `bPctDone`. **`RenderPctStep`** (en `FlowTick`, después de `FVeil`): a RT ≥ 1 s (después del `BeginPlay` del pawn, que pone 100) ejecuta `xr.SecondaryScreenPercentage.HMDRenderTarget <RenderPct>`; `-DemoRenderPct=N` en la línea de comandos lo pisa. `L_Demo_Draw` 115; Breath y Heart 100 (CDO).
- Probado en -game (sin visor): Heart completo (poemas a 50/100 s, polvo nuevo, cuadro + FINISH, 0 errores) · Breath completo (149,5 s de etapa, las 13 voces en orden, cuadro + FINISH, 0 errores).

## 2026-10-23 — FINISH con los sonidos de la mezcla
`FinSpawn` (respaldo `flow_dsl_backup_1023.py`): al crear FINISH le pone `HoverSound` `SND_Demo_HoverOn`, `HoverOutSound` `SND_Demo_HoverOut`, `PressSound` `SND_Demo_Select` y a su `AppearLuz` In/Out `SND_Demo_InOut` (FINISH se crea en tiempo de juego: no hay instancia que editar).
