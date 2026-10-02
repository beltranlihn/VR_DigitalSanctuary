# Perillas de cada mecanica

> Generado por `tools/unreal/gen_perillas_doc.py` desde un volcado del editor (`perillas.json`, 2026-10-02). Valores = los del Blueprint (CDO).
> 🔴 Si una perilla tambien esta puesta en la INSTANCIA de su nivel de test, manda la instancia: mirar el Details del actor en ese nivel.

**Regla de donde se ajusta cada cosa** (detalle en `docs/GUIA-DE-DIRECCION.md`):
- **Cuando** pasa algo en la obra -> `DA_Partitura_Obra` (`docs/PARTITURA.md`).
- **Donde** pasa -> TargetPoints y actores en el nivel de test de la etapa.
- **Como se ve y se siente** una mecanica -> las perillas de esta pagina, en su nivel de test.

Las categorias que parecen internas (Interno, Estado, Z-...) se omiten: no son perillas.

## El director de la Obra — `BP_Obra_SC`

Nivel donde se ajusta: **L_SoulCharger_Obra**. Los tiempos NO se tocan aca: van en DA_Partitura_Obra (ver docs/PARTITURA.md). En la instancia del nivel solo cuentan Config y Debug.

**Ambientes** — `AmbClips` [{"refPath":"/Game/SoulCharger/Core/Audio/AmbientClips/Ambient_Clip_1_... · `AmbVolumes` [0.80000000000000004,0.80000000000000004,0.80000000000000004,0.8000000... · `AmbFadeIn` 3 · `AmbFadeOut` 3

**Config** — `bDisclaimer` true · `bSimulated` true

**Debug** — `Speed` 1 · `bPhotos` false · `LastShot` 0 · `bDebugEnding` false · `DebugShare` -1 · `DebugStart` -1 · `DebugSoul` 0 · `DbgK` -1 · `DbgS` 0 · `DbgHallStep` 0 · `DbgDrawSynth` false · `Smoke` false · `SmokePhase` -99 · `SmokeStage` -99

**Etapas** — `StartLoc` [{"x": 0, "y": 0, "z": 0}, {"x": 0, "y": 0, "z": 0}, {"x": 0, "y": 0, ... · `StartYaw` [0, 0, 0, 0, 0, 0] · `CTops` [{"r":0.55000001192092896,"g":0.63999998569488525,"b":0.81999999284744... · `CHors` [{"r":0.6600000262260437,"g":0.73000001907348633,"b":0.879999995231628... · `TitleMIs` [{"refPath":"/Game/SoulCharger/Tour/MI_TourTitle_ENTERING.MI_TourTitle... · `LevelPaths` ["/Game/Test_Entering","/Game/Test_Heart","/Game/Test_Fluid","/Game/Te... · `LevelNames` ["Test_Entering", "Test_Heart", "Test_Fluid", "Test_Sequencer", "L_TBT... · `StageNames` ["ENTERING", "RECOGNIZING", "LOVING", "ATTRACTING", "SURROUNDING", "HA... · `StageCols` [{"r":0.10949999839067459,"g":0.21220000088214874,"b":0.74540001153945... · `CavNames` ["Charge_Entering", "Charge_Recognizing", "Charge_Loving", "Charge_Att... · `TpIn` ["sc0_alma_in", "sc1_alma_in", "sc2_alma_in", "sc3_alma_in", "sc4_alma... · `TpSide` ["sc0_alma_side", "sc1_alma_side", "sc2_alma_side", "sc3_alma_side", "... · `TpCharge` ["sc0_charge", "sc1_charge", "sc2_charge", "sc3_charge", "sc4_charge"] · `TpTitle` ["sc0_title", "sc1_title", "sc2_title", "sc3_title", "sc4_title"] · `StAlma` [] · `StInstr` [] · `StOutro` []

**Final** — `RingRoll` 0 · `SoulSpot` {"x": 0, "y": 0, "z": 0} · `RingSpot` {"x": 0, "y": 0, "z": 0} · `DoorPt` {"x": 0, "y": 0, "z": 0} · `AwayPt` {"x": 0, "y": 0, "z": 0} · `ResAlmaLeft` 45 · `ResAlmaScale` 0.7 · `SketchSpeed` 20

**Hall - Anillo** — `HallRingFit` 1 · `HallRingSpeedIn` 1.5 · `HallHomeSpeed` 2 · `HallHomeDelay` 0.3

**Instrucciones** — `bGhostsOn` true

**Partitura** — `AlmaTime` 8 · `InstrTime` 6 · `OutroTime` 2.5 · `ResultsTime` 150 · `CreditsTime` 60 · `ChargeTimes` [4, 4, 4, 4, 6] · `DiscTime` 19 · `ExploreT` 25 · `ShareFW` 30 · `SwimTime` 4 · `AwayTime` 3 · `SimStageMax` 90 · `Partitura` {"refPath": "/Game/SoulCharger/Obra/Partitura/DA_Partitura_Obra.DA_Par... · `Titulo_Aparece` 2.5 · `Titulo_RevelaIni` 3 · `Titulo_RevelaFin` 6.5 · `Bajada_RevelaIni` 5 · `Bajada_RevelaFin` 7.5 · `Logos_RevelaIni` 6 · `Logos_RevelaFin` 8 · `Titulo_SaleIni` 17 · `Titulo_SaleFin` 19.5 · `Titulo_Fin` 20 · `Hall_VeloAbreIni` 3.5 · `Hall_VeloAbreFin` 5.5 · `Hall_IntroA` 3 · `HUD_EEGRetardo` 1 · `Etapa_VeloAbreIni` 1 · `Etapa_VeloAbreFin` 4 · `Etapa_TituloRevelaIni` 0.5 · `Etapa_TituloRevelaFin` 1.8 · `Etapa_TituloSaleIni` 4.6 · `Etapa_TituloSaleFin` 5.6 · `Etapa_TituloOculto` 5.7 · `Alma_Entra` 5.5 · `Alma_VozRetardo` 1.5 · `Alma_TrasVoz` 3 · `Instr_Dur` [8.5, 6, 6, 6, 0.6] · `Instr_EsperaMax` 20 · `Etapa_Tope` [240, 180, 120, 240, 240] · `Salida_Dur` [2.5, 2.5, 2.5, 2.5, 2.5] · `Salida_TrasVoz` 0.6 · `Carga_Minima` 1 · `Despedida_Retardo` 0.9 · `Despedida_TrasVoz` 1.3 · `Velo_CierreDur` 2.5 · `Final_NegroRampa` 2 · `Regreso_HallA` 0.3 · `Regreso_VeloIni` 0.2 · `Regreso_VeloFin` 1.4 · `Regreso_PezA` 1.6 · `Res_AlmaA` 0.5 · `Res_PezMin` 1.8 · `Res_PezMax` 3.4 · `Res_GusanoA` 2 · `Res_InvitaRecorte` 1.2 · `Res_BotonesVoz` 1.8 · `Res_SalidaRetardo` 0.5 · `Salida_HallA` 0.5 · `Const_AlmaLlega` 5 · `Const_Voz35` 8 · `Const_Voz37TrasVoz` 0.6 · `Fundido_Dur` 3.5 · `Velo_CierreFinT` 71.5 · `Final_NegroIniPT` 9.5 · `Hall_VeloGuarda` 6 · `Etapa_TopeK` 240 · `Corte_Espera` 30

_118 perillas listadas de 221 variables._

## El ensayo de una etapa en su nivel de test — `BP_StageRunner_SC`

Nivel donde se ajusta: **cada Test_* (actor TestOnly)**. Tiempos desde la Partitura; en la instancia quedan StageK, colores del velo (CTop/CHor), tags de los TargetPoints, Loop, Speed.

**Default** — `IsObra` false · `RPhase` 0 · `RT` 0 · `PT` 0 · `RDone` false · `ByeSt` 0 · `PStart` {"x": 0, "y": 0, "z": 0} · `PYaw` 0

**Ensayo** — `StageK` 0 · `Loop` true · `Speed` 1 · `AlmaTime` 10.5 · `InstrTime` 6 · `OutroTime` 2.5 · `TimeoutS` 240 · `ChargeTime` 4 · `EyeRef` 120 · `CTop` {"r": 0.550000011920929, "g": 0.6399999856948853, "b": 0.8199999928474... · `CHor` {"r": 0.6600000262260437, "g": 0.7300000190734863, "b": 0.879999995231... · `LevelName` Test_Entering · `TagIn` sc0_alma_in · `TagSide` sc0_alma_side · `TagCharge` sc0_charge · `TagTitle` sc0_title · `TitleMI` {"refPath": "/Game/SoulCharger/Tour/MI_TourTitle_ENTERING.MI_TourTitle... · `VOEntrada` [{"refPath":"/Game/SoulCharger/Obra/Audio/VO_10.VO_10"},{"refPath":"/G...

**Partitura** — `Partitura` {"refPath": "/Game/SoulCharger/Obra/Partitura/DA_Partitura_Obra.DA_Par... · `Etapa_VeloAbreIni` 1 · `Etapa_VeloAbreFin` 4 · `Etapa_TituloRevelaIni` 0.5 · `Etapa_TituloRevelaFin` 1.8 · `Etapa_TituloSaleIni` 4.6 · `Etapa_TituloSaleFin` 5.6 · `Etapa_TituloOculto` 5.7 · `Alma_Entra` 5.5 · `Alma_TrasVoz` 3 · `Despedida_Retardo` 0.9 · `Corte_Espera` 30 · `EtapaTopeRun` 240

_39 perillas listadas de 40 variables._

## El ensayo del Hall — `BP_HallRunner_SC`

Nivel donde se ajusta: **Test_Hall (TestOnly)**. DebugStart 2-9 para arrancar en un paso del Hall.

**Default** — `IsObra` false · `RT` 0 · `Called` false · `TitleSt` 0 · `AmbNow` -2 · `HudDone` false · `HudAt` -1 · `EEGDone` false · `EndT` -1 · `Ended` false · `JumpStep` 0 · `HudReset` false

**Ensayo** — `DebugStart` -1 · `DebugSoul` 0 · `Loop` true · `LevelName` Test_Hall · `FakeBio` true · `KeepChargeTest` false

_18 perillas listadas de 18 variables._

## El Hall: inicio, regreso y salida — `BP_HallDirector_SC`

Nivel donde se ajusta: **Test_Hall**. Las paradas son flechas arrastrables en el nivel; los ritmos estan en sus categorias.

**Default** — `bHallDone` false · `bReturnDone` false · `bExitDone` false · `ChosenSoul` -1 · `bRightHanded` true · `bHudBorn` false · `LeadActor` None · `bTestIntro` false · `bTestReturn` false · `bTestExit` false · `TestDelay` 2 · `JourneyTime` 26 · `EnterTime` 7 · `OutTime` 11 · `ReturnTime` 8 · `ExitTime` 12 · `AccelTime` 2.5 · `BrakeTime` 3 · `VOAir` 0.5 · `DoorOpenDeg` 16.5 · `DoorTime` 3 · `TileLiftCm` 3 · `TileGlowMax` 0.35 · `ReturnGlow` 0.6 · `TileTime` 1.5 · `ReachFwd` 48 · `ReachDown` 28 · `TouchRadius` 14 · `BellHold` 3 · `FW_Bell` 25 · `FW_Tool` 20 · `FW_Choose` 25 · `VO` [{"refPath":"/Game/SoulCharger/Mechanics/Hall/Audio/VO_01a.VO_01a"},{"... · `SndDoor` {"refPath": "/Game/SoulCharger/Core/Audio/Sounds/DoorOpen.DoorOpen"} · `SndBell` {"refPath": "/Game/SoulCharger/Core/Audio/Sounds/Bell.Bell"} · `SndSteps` {"refPath": "/Game/SoulCharger/Core/Audio/Sounds/Pasos.Pasos"} · `Mode` 0 · `Step` 0 · `StepTime` 0 · `StepDur` 0 · `bGate` true · `bWaitWalk` false · `WalkA` {"x": 0, "y": 0, "z": 0} · `WalkB` {"x": 0, "y": 0, "z": 0} · `WalkT` 0 · `WalkDur` 0 · `DoorW` 0 · `DoorE` 0 · `DoorWT` 0 · `DoorET` 0 · `TileCur` [] · `TileTgt` [] · `TileGain` 0.35 · `bTitles` true · `BellCharge` 0 · `bBellLive` false · `bSensorLive` false · `bPickLive` false · `ReachLoc` {"x": 0, "y": 0, "z": 0} · `EyeLoc` {"x": 0, "y": 0, "z": 0} · `Pawn` None · `Alma` None · `Lights` None · `Bell` None · `Sensor` None · `Picker` None · `Fog` None · `StepsAudio` None · `Leaves` [] · `LeafYaw` [] · `LeafSign` [] · `LeafEast` [] · `TileMIDs` [] · `Souls` [] · `TestSpeed` 1 · `DoorWarm` {"r": 1, "g": 0.7200000286102295, "b": 0.4000000059604645, "a": 1} · `DoorCold` {"r": 0.550000011920929, "g": 0.6399999856948853, "b": 0.8199999928474... · `TitleComps` [] · `TestFromStep` -1 · `IntroHold` 12 · `PaceWalkToVO` 3 · `PaceJourneyPause` 1.5 · `PaceArrive` 0.5 · `PaceBellVO` 0.5 · `PaceBellRing` 0.8 · `PaceDoorOpen` 1.5 · `PaceAlmaAppear` 2.5 · `PaceAfterTool` 0.5 · `PaceTilesOff` 1.5 · `PaceHudBirth` 3 · `PaceFollowMe` 2 · `PaceLightsOffOut` 5 · `PaceReturnDark` 2 · `PaceReturnLight` 1.5 · `PaceReturnDoor` 1 · `PaceReturnVO` 1 · `PaceDoorClose` 1 · `PaceExitLightsOff` 6 · `BellPressDepth` 1 · `DoorLeadDist` 620 · `BellPressTime` 0.12 · `BellPress` 0 · `BellRest` {"x": 0, "y": 0, "z": 0} · `BellTouch` false · `BellSnd` None

_105 perillas listadas de 105 variables._

## Entering: la etapa — `BP_BreathStage_SC`

Nivel donde se ajusta: **Test_Entering**. 

**0 - Etapa** — `bAutoStart` true · `StartDelay` 1.5 · `PacerDelay` 2 · `BlobOutDelay` 0.6

**0-Contrato** — `bContractTest` false · `ExploreTime` 12 · `CountTime` 3.6 · `ToolDelay` 0.8 · `SensorColor` {"r": 0.3499999940395355, "g": 0.699999988079071, "b": 1, "a": 1} · `CountSound` {"refPath": "/Game/SoulCharger/Mechanics/Breath/Audio/VO_12c.VO_12c"} · `BlobInSound` {"refPath": "/Game/NeuralCanvas/Sound/VR_shep_scale_up_01.VR_shep_scal... · `BlobOutSound` {"refPath": "/Game/NeuralCanvas/Sound/VR_shep_scale_down_02.VR_shep_sc... · `bCycleVO` true · `InhaleCueAt` 2.56 · `CueLead` 0.3 · `HoldSound` {"refPath": "/Game/SoulCharger/Mechanics/Breath/Audio/VO_12f1.VO_12f1"... · `ExhaleSound` {"refPath": "/Game/SoulCharger/Mechanics/Breath/Audio/VO_12f2.VO_12f2"... · `SayAfterTool` 1 · `SayGap` 0.5 · `HelpAfter` 4 · `ClipInstr` {"refPath": "/Game/SoulCharger/Obra/Audio/VO_11.VO_11"} · `ClipExplore` {"refPath": "/Game/SoulCharger/Obra/Audio/VO_11b.VO_11b"} · `ClipHelp` {"refPath": "/Game/SoulCharger/Obra/Audio/VO_11h.VO_11h"} · `ClipReady` {"refPath": "/Game/SoulCharger/Obra/Audio/VO_12.VO_12"}

**Default** — `OnBreathStageDone` () · `bStageDone` false

_26 perillas listadas de 51 variables._

## Entering: el sensor de respiracion (mandos) — `BP_BreathRig_SC`

Nivel donde se ajusta: **Test_Entering**. Umbral y suavizado de la respiracion.

**0 - Rig** — `bStartActive` false · `bShowControllers` true · `bShowSensors` true · `bHideHands` true · `CtrlColor` {"r": 0.3499999940395355, "g": 0.800000011920929, "b": 1, "a": 1} · `SensorColor` {"r": 0.8859999775886536, "g": 0.6039999723434448, "b": 0.446999996900... · `CtrlBrightness` 1.5 · `RevealTime` 0.6 · `CtrlMat` {"refPath": "/Game/SoulCharger/Mechanics/Breath/M_BreathCtrl_SC.M_Brea...

**A - Umbral** — `SafeHorizMax` 23 · `SafeVDropMin` 33 · `SafeVDropMax` 63 · `StillLin` 14 · `StillAng` 45 · `StillTau` 0.3 · `MinHAmp` 0.02 · `ActivateDelay` 1.5 · `DeactivateDelay` 0.2 · `bEnabled` true · `bIgnoreTracking` false · `FacingMin` 0.34 · `FacingHyst` 0.25

**B - Senal** — `TauFast` 0.4 · `HorizTau` 8 · `TauAmp` 4 · `GainK` 0.5 · `LevelFollow` 5 · `HoldSlow` 0.25 · `HoldMovK` 1 · `bFlipSign` false · `AmpTau` 8 · `AmpFloorCm` 0.3

**C - Haptica** — `bHaptics` true · `HapticAmp` 0.25 · `HapticEffect` {"refPath": "/Game/XRFramework/Haptics/GrabHapticEffect.GrabHapticEffe...

**D - Salida** — `DriveFollow` 4 · `SignedGain` 1 · `bAutoHand` false · `bRightHand` true · `SmoothFreq` 4 · `RangeNorm` 1 · `RangeTau` 6 · `RangeFloor` 0.25 · `BreathFollowTime` 3 · `BreathFollowAttack` 0.12

**E - Prueba** — `PreviewBreath` 0 · `FakePeriod` 6 · `bFakeBreath` false · `FakeAmpCm` 1.5

**Y - Publicado** — `bBreathing` false · `BreathLevel` 0.5 · `BreathDrive` 0.5 · `BreathSigned` 0 · `BreathOn` 0 · `BreathNorm` 0

_55 perillas listadas de 88 variables._

## Entering: el metaball — `BP_BreathBlob_SC`

Nivel donde se ajusta: **Test_Entering**. 

**A - Forma** — `SizeCM` 220 · `BlobRadius` 13.58 · `Smoothness` 9 · `Spread` 19.46

**A-Forma** — `SizeVariation` 0.45 · `BlobCount` 6

**B - Atraccion** — `AttractSpeed` 0.18 · `AttractMin` 0.05 · `AttractMax` 0.92

**C - Curl** — `CurlAmount` 19.37 · `CurlSpeed` 0.42

**D - Color** — `Brightness` 1.546483 · `ColorLight` {"r": 0.921875, "g": 0.9447950124740601, "b": 1, "a": 1} · `ColorShadow` {"r": 0.02616499923169613, "g": 0.013101999647915363, "b": 0.119791999...

**Default** — `MID` None · `OnBlobGone` ()

**E - Calidad** — `Steps` 64

**E-Calidad** — `ProxyTrim` {"x": 0, "y": 0, "z": 0}

**F - Entrada Salida** — `EnvT` 1 · `IntroTime` 2.5 · `OutroTime` 2.5 · `bAutoAppear` false · `MorphScale` 0.5 · `MorphRadius` 0.08 · `MorphSizeVar` 1.6 · `MorphSpread` 1.9 · `MorphSpreadOut` 2.3 · `MorphSmooth` 0.2 · `MorphBright` 1.35 · `MorphCurl` 1.3

**G - Movimiento** — `MotionGain` 2 · `MotionFollow` 2.5 · `GradSpeed` 0.9 · `GradWave` 0.35 · `MotionIdle` 0.25 · `FlowAmt` 0.6 · `FlowScale` 0.12

**R - Respiracion** — `BreathAttract` 1 · `BreathSpreadIn` -0.85 · `BreathSpreadOut` 0.6 · `BreathCurlIn` -0.7 · `BreathCurlOut` 0.5 · `BreathRadiusIn` 0 · `BreathRadiusOut` -0.15 · `BreathBrightIn` 0 · `BreathBrightOut` 0

_46 perillas listadas de 50 variables._

## Entering: el pacer (guia de respiracion) — `BP_Pacer_SC`

Nivel donde se ajusta: **Test_Entering**. Ciclos y tiempos 4-3-4-3.

**A - Ritmo** — `InhaleTime` 6 · `Hold1Time` 0 · `ExhaleTime` 6 · `Hold2Time` 0 · `Mode` 1 · `Preset` 1 · `Cycles` 0 · `bAutoPlay` true · `bInhaleToCenter` true · `LeadIn` 3 · `LeadOut` 3

**B - Forma** — `SizeCm` 60 · `ClearCenter` 0.62 · `LineWidth` 0.008 · `AAWidth` 1

**C - Color** — `Opacity` 0.85 · `Brightness` 1 · `PacerColor` {"r": 0.7990000247955322, "g": 0.6510000228881836, "b": 0.564000010490... · `AccentColor` {"r": 0.7599999904632568, "g": 0.3240000009536743, "b": 0.165999993681... · `EmissiveAlpha` 1

**D - Audio** — `PulseInterval` 1 · `SfxVolume` 1 · `PulseMode` 0 · `SndInhale` None · `SndExhale` None · `SndHold` None · `SndPulse` None · `SndPulseInhale` None · `SndPulseHold` None · `SndPulseExhale` None

**Default** — `T` 0 · `PulseT` 0 · `Total` 0 · `CycleIndex` 0 · `CurPhase` 0 · `bRunning` false · `MID` None · `OnPacerPhase` () · `OnPacerCycle` () · `OnPacerFinished` () · `CurFramePhase` 0 · `EnvT` 1 · `IntroTime` 0.6 · `OutroTime` 0.6

**E - Enlace** — `ExternalLung` 0 · `bUseExternalLung` false

**F - Halo** — `HaloStrength` 0.55 · `HaloWidth` 0.07 · `HaloFadeOut` 1.5

**G - Progreso** — `bShowProgress` true · `ProgRadius` -0.035 · `ProgAmt` 1

_52 perillas listadas de 56 variables._

## Recognizing: el latido — `BP_HeartManager_SC`

Nivel donde se ajusta: **Test_Heart**. StageBeats = latidos hasta el fin.

**8 - Voz** — `HintAfter` 15 · `VO17cAtBeat` 8 · `VO16` {"refPath": "/Game/SoulCharger/Obra/Audio/VO_16.VO_16"} · `VO16h` {"refPath": "/Game/SoulCharger/Obra/Audio/VO_16h.VO_16h"} · `VO17a` {"refPath": "/Game/SoulCharger/Obra/Audio/VO_17a.VO_17a"} · `VO17c` {"refPath": "/Game/SoulCharger/Obra/Audio/VO_17c.VO_17c"}

**A - Zona** — `HeartHorizMax` 25 · `HeartVDropMin` 10 · `HeartVDropMax` 45 · `ActivateDelay` 0.35 · `DeactivateDelay` 0.15 · `StillLin` 14 · `StillAng` 45 · `StillTau` 0.3 · `bIgnoreTracking` false

**B - Ritmo** — `BeatDiv` 2 · `BeatEnvDecay` 2.5

**C - Feedback** — `bHaptics` true · `HapticAmp` 0.25 · `bSound` true · `HapticEffect` {"refPath": "/Game/XRFramework/Haptics/GrabHapticEffect.GrabHapticEffe... · `HeartBeatSound` {"refPath": "/Game/SoulCharger/Core/Audio/Sounds/HeartBeat.HeartBeat"} · `SoundVolume` 1

**D - Mano** — `bAutoHand` true · `bRightHand` true

**Default** — `OnBeatPulse` () · `OnHeartBeat` () · `bStageDone` false · `bContractTest` false · `StageBeats` 19 · `BackupAfter` 30 · `SensorColor` {"r": 1, "g": 0.3400000035762787, "b": 0.2800000011920929, "a": 1} · `OrbitAtBeat` 8

**E - Prueba** — `bFakeBeat` false · `FakeBPM` 60 · `bDebug` false · `bForceZone` false

**Y - Publicado** — `bHeartZone` false · `BeatEnv` 0 · `HeartBPM` 60 · `BeatCount` 0 · `bQuiet` false

_42 perillas listadas de 72 variables._

## Loving: la celula — `BP_LovingCell_SC`

Nivel donde se ajusta: **Test_Fluid**. StageDuration = duracion de la mecanica.

**2-Forma** — `GroupCount` 5 · `GroupSize` 1 · `GroupSpread` 1 · `CenterAttraction` 1 · `ConnectionStrength` 1 · `CentreRadius` 16 · `DistSeparated` 72 · `DistConnected` 48 · `FigureTilt` 15 · `SizeVariation` 0.5 · `bBridges` false

**3-Membrana** — `MembraneThickness` 1 · `MembraneOpacity` 1 · `EnvelopeHug` 0

**4-Vida** — `NoiseAmount` 1 · `OrganicMotion` 1 · `PulseSpeed` 1 · `PreviewTime` 0 · `FloatAmount` 1 · `Reach` 1 · `StrandCurl` 1

**5-Particulas** — `DustOpacity` 0.55 · `DustSize` 0.35 · `DustDrift` 0.6 · `DustOffset` 2 · `DustColor` {"r": 0.8500000238418579, "g": 0.8799999952316284, "b": 1, "a": 1}

**6-Envoltura** — `OuterOpacity` 0.32 · `OuterMargin` 3 · `OuterBody` 60 · `OuterSoftness` 1 · `OuterWobble` 0.2 · `OuterColor` {"r": 0.6200000047683716, "g": 0.5199999809265137, "b": 0.860000014305...

**7-Color** — `AmoebaColor1` {"r": 0.9700000286102295, "g": 0.949999988079071, "b": 1, "a": 1} · `AmoebaColor2` {"r": 0.41999998688697815, "g": 0.36000001430511475, "b": 0.8500000238... · `ShadowColor` {"r": 0.10000000149011612, "g": 0.05999999865889549, "b": 0.3400000035... · `CoreContrast` 0.7 · `BallContrast` 0.6 · `MembraneColor` {"r": 0.8199999928474426, "g": 0.8600000143051147, "b": 1, "a": 0.0599... · `MembraneRim` {"r": 0.9200000166893005, "g": 0.949999988079071, "b": 1, "a": 0.18000...

**8-Agua** — `WaterLight` 0 · `WaterLightShell` 1

**9-Etapa** — `bContractTest` false · `StageDuration` 80 · `IntroTime` 3 · `OutroTime` 3 · `TestGap` 3 · `SndVolume` 0.8 · `Fluid` None · `SndIntro` {"refPath": "/Game/SoulCharger/Mechanics/Loving/Audio/SND_MindAppear.S... · `SndOutro` {"refPath": "/Game/SoulCharger/Mechanics/Loving/Audio/SND_MindVanish.S... · `IntroDelay` 2 · `VO22At` 15 · `VO23At` 42 · `VOWait` 8 · `VO22` {"refPath": "/Game/SoulCharger/Obra/Audio/VO_22.VO_22"} · `VO23` {"refPath": "/Game/SoulCharger/Obra/Audio/VO_23.VO_23"}

**9-Rendimiento** — `SimDivider` 3

**Default** — `Tgt` {"x": 0, "y": 0, "z": 0} · `LV0` {"r": 0, "g": 0, "b": 0, "a": 0} · `LV1` {"r": 0, "g": 0, "b": 0, "a": 0} · `LV2` {"r": 0, "g": 0, "b": 0, "a": 0} · `LV3` {"r": 0, "g": 0, "b": 0, "a": 0} · `LV4` {"r": 0, "g": 0, "b": 0, "a": 0} · `LV5` {"r": 0.5, "g": 1, "b": 0, "a": 0} · `bStageDone` false

_65 perillas listadas de 133 variables._

## Loving: el fluido cerebral — `BP_FluidMedium_SC`

Nivel donde se ajusta: **Test_Fluid**. 

**0-EEG** — `EEG` 0.3 · `bFakeEEG` false · `FakePeriod` 60 · `EEGSmoothing` 2 · `EEGFlow` 0.7 · `EEGClarity` 0.5 · `ActiveBoost` 0

**1-Movimiento** — `CurrentSpeed` 4 · `CurrentYaw` 20 · `CurrentPitch` 8 · `Meander` 35 · `FlowAmp` 22 · `FlowScale` 130 · `FlowSpeed` 0.14 · `Turbulence` 0.7 · `StreakTime` 0

**2-Liquido** — `FluidTop` {"r": 0.06849999725818634, "g": 0.1273999959230423, "b": 0.55199998617... · `FluidMid` {"r": 0.01940000057220459, "g": 0.035599999129772186, "b": 0.201600000... · `FluidBottom` {"r": 0.0032999999821186066, "g": 0.00559999980032444, "b": 0.03310000... · `GlowColor` {"r": 0.4020000100135803, "g": 0.5519999861717224, "b": 1, "a": 1} · `GlowAmount` 0.45 · `GlowPower` 3 · `AbsorbDist` 800 · `AbsorbMax` 0.92 · `AbsorbAlpha` 0.35

**3-Particulas** — `MoteColor` {"r": 0.7231000065803528, "g": 0.8069999814033508, "b": 1, "a": 1} · `MoteBright` 1.25 · `NearSize` 0.45 · `MidSize` 1.3 · `FarSize` 6 · `NearAlpha` 0.85 · `MidAlpha` 0.6 · `FarAlpha` 0.5 · `Bokeh` 3 · `BokehDist` 60

**4-Celulas** — `MidCellCount` 12 · `MidCellScale` 1.1 · `FarCellCount` 48 · `FarCellSize` 80 · `CellFlow` 0.6 · `CellHigh` {"r": 0.9700000286102295, "g": 0.949999988079071, "b": 1, "a": 1} · `CellLow` {"r": 0.30000001192092896, "g": 0.25999999046325684, "b": 0.7200000286... · `CellContrast` 1 · `CellFill` {"r": 0.10000000149011612, "g": 0.05999999865889549, "b": 0.3400000035... · `CellLight` {"x": -0.551, "y": -0.401, "z": 0.732} · `MidCellRange` 1800 · `CellBody` 0.35

**5-Luz** — `CausticAmount` 0.6 · `CausticScale` 18 · `CausticSpeed` 0.6 · `MoteSparkle` 0.8 · `ShaftAmount` 0.14 · `VeilAmount` 0.5

**6-Manos** — `bHandStir` false · `StirStrength` 0.18 · `StirRadius` 22 · `StirSwirl` 0.8 · `HandVelSpeed` 5 · `HandMaxSpeed` 300

**7-Viaje** — `bTravel` false · `TravelSpeed` 25 · `TravelEase` 4 · `TravelEaseOut` 2 · `TravelYaw` 180 · `TravelPitch` 0

_65 perillas listadas de 88 variables._

## Attracting: el secuenciador — `BP_Sequencer_SC`

Nivel donde se ajusta: **Test_Sequencer**. 

**0 - Config** — `ModuleSounds` [{"refPath":"/Game/SoulCharger/Core/Audio/AttractingSounds/Module1/M1S... · `FinalOffset` {"x": -120, "y": 0, "z": 35} · `PadFadeOut` 2 · `NumSteps` 8 · `FinalPasses` 2 · `PadSound` {"refPath": "/Game/SoulCharger/Core/Audio/AttractingSounds/Module1/Pad... · `ModuleIndex` 0 · `ClipsPerModule` 20 · `ModulePads` [{"refPath": "/Game/SoulCharger/Core/Audio/AttractingSounds/Module1/Pa... · `FinalTag` seq_final_attracting · `IntroDelay` 2

**0-Config** — `bAutoStart` false · `PadDelay` 0 · `OrbZOffset` 12 · `OrbColors` [{"r":1,"g":0.25,"b":0.18000000715255737,"a":1},{"r":1,"g":0.800000011... · `bWaitIntroConfirm` false · `ExitTime` 1.5 · `bReplayOnSave` true · `ContractGap` 8 · `IntroOrbsAt` 1.2 · `IntroToolsAt` 2.4 · `OutroStep` 0.5 · `ResultsWidth` 90 · `ResultsPad` 9 · `StepBPM` 90 · `ResultsSpacing` 21.4 · `ResultsPadDelay` 0.5

**9-Debug** — `DebugTourCmd` 0 · `bContractTest` false · `bResultsTest` false · `ResultsHold` 20

**Default** — `Tmp` [] · `OnMelodyFinished` () · `OnIntroShown` () · `OnIntroFinished` () · `OnStageFinished` () · `bStageDone` false

_37 perillas listadas de 65 variables._

## Attracting: los mandos y el laser — `BP_SeqRig_SC`

Nivel donde se ajusta: **Test_Sequencer**. 

**0-Rig** — `TraceDistance` 2500 · `bOwnInput` true · `bShowControllers` true · `bStartActive` false · `CtrlOffsetR` {"location":{"x":3.5600000000000001,"y":-0.80000000000000004,"z":-2.87... · `CtrlOffsetL` {"location":{"x":3.5600000000000001,"y":0.80000000000000004,"z":-2.870... · `HapticEffect` {"refPath": "/Game/XRFramework/Haptics/GrabHapticEffect.GrabHapticEffe... · `IMCRight` {"refPath": "/Game/XRFramework/Input/IMC_Weapon_Right.IMC_Weapon_Right... · `IMCLeft` {"refPath": "/Game/XRFramework/Input/IMC_Weapon_Left.IMC_Weapon_Left"} · `CtrlMeshR` {"refPath": "/Game/ControllerR.ControllerR"} · `CtrlMeshL` {"refPath": "/Game/ControllerL.ControllerL"} · `CtrlMat` {"refPath": "/Game/SoulCharger/Mechanics/Sequencer/M_SeqCtrl_SC.M_SeqC... · `bRightHanded` true · `bMountButton` true · `BtnOffset` {"location":{"x":5.5700000000000003,"y":0.80000000000000004,"z":-2.080... · `bHideHands` true · `CtrlColor` {"r": 0.3499999940395355, "g": 0.800000011920929, "b": 1, "a": 1} · `CtrlBrightness` 1.5 · `RetireSpeed` 4 · `bQuestCtrl` true · `QCtrlLocR` {"x": 5.686, "y": 0.54, "z": -1.678} · `QCtrlRotR` {"pitch": -13.566, "yaw": -83.539, "roll": 64.231} · `QCtrlLocL` {"x": 5.877, "y": -1.567, "z": -2.05} · `QCtrlRotL` {"pitch": 0, "yaw": -95, "roll": 65} · `QCtrlScale` 1.0875

**1-Puntero** — `PtrGap` 10 · `PtrLen` 40 · `PtrWidth` 0.45 · `PtrTipFade` 1.5 · `PtrDotSize` 1.14178 · `PtrDotIdle` 75 · `PtrOpacity` 0.58 · `PtrDotOpacity` 0.45 · `PtrDotRef` 75 · `PtrDotPersp` 0.604 · `PtrSort` 100 · `PtrColor` {"r": 0.44999998807907104, "g": 0.8500000238418579, "b": 1, "a": 1} · `PtrBeamMat` {"refPath": "/Game/SoulCharger/Core/Sensor/M_Pointer_SC.M_Pointer_SC"} · `PtrDotMat` {"refPath": "/Game/SoulCharger/Core/Sensor/M_PointerDot_SC.M_PointerDo...

_39 perillas listadas de 73 variables._

## Surrounding: el dibujo (director) — `BP_TBDirector_NC`

Nivel donde se ajusta: **L_TBTest_SC**. Tinta, paleta, presentacion.

**00 MANO** — `bLeftHanded` false · `bHidePawnHands` true

**01 COLOR** — `ColorMode` 0 · `SlotColorA` [{"r":1,"g":0.55000001192092896,"b":0.20000000298023224,"a":1},{"r":0.... · `SlotColorB` [{"r":1,"g":0.20000000298023224,"b":0.10000000149011612,"a":1},{"r":0.... · `bColorGradient` true · `BrushIds` [0, 5, 3, 6] · `bPrimaryAtTip` true

**02 ANIMACION** — `bSwayEnabled` true · `SwayStrength` 1.5 · `SwayWave` 0.18 · `SwaySpeed` 0.5 · `SwaySpan` 40 · `SwaySpeedVar` 0.6 · `SwayScale` 0.03 · `SwayDir` {"x": 1, "y": 0.6, "z": 0.15} · `SwayFade` 1.2

**03 SKETCH** — `HideTime` 2 · `ShowTime` 2.5 · `SketchGap` 0.4 · `bCenterZ` false · `SketchDist` 90 · `SketchUp` 0 · `RevealTaper` 6 · `SketchTarget` None · `SpinSpeed` 20 · `HoldTime` 5 · `DrawTable` None · `SaveHoldTime` 3 · `OutroTime` 1.2 · `TableColor` {"r": 0.25, "g": 0.550000011920929, "b": 1, "a": 1}

**04 AUDIO** — `BrushLoop` [{"refPath":"/Game/NeuralCanvas/Sound/FF_OHT_124_texture_loop_emoted_G... · `BrushLoopVol` [0.6, 0.6, 0.6, 0.6] · `LoopFade` 0.25 · `ClickSound` {"refPath": "/Game/NeuralCanvas/Sound/VR_click1.VR_click1"} · `HideSound` {"refPath": "/Game/NeuralCanvas/Sound/VR_shep_scale_down_02.VR_shep_sc... · `ShowSound` {"refPath": "/Game/NeuralCanvas/Sound/VR_shep_scale_up_02.VR_shep_scal... · `SfxVol` 1 · `ClickVol` 0.7 · `SliderSound` {"refPath": "/Game/NeuralCanvas/Sound/VR_click2.VR_click2"} · `SliderVol` 0.3 · `ChargeSound` {"refPath": "/Game/NeuralCanvas/Sound/VR_shep_scale_up_01.VR_shep_scal... · `ChargeVol` 0.6

**05 HAPTICA** — `DrawHapAmp` 0.25 · `DrawHapFreq` 1 · `ClickHapAmp` 0.6 · `ClickHapDur` 0.06 · `DrawHapPulse` 0

**06 PUNTA** — `TipOffset` {"x": 2.5, "y": 0, "z": 0} · `TipScale` 0.006 · `bHalo` true · `HaloScale` 3 · `HaloIntensity` 0.6 · `HaloBoost` 1 · `HaloWaveSpeed` 0.35 · `HaloPulseSpeed` 0.4 · `TipGain` 1.5 · `TipLift` 0.06

**07 PALETA** — `PaletteOffset` {"x": 2.1884, "y": 2.7613, "z": 7.5137} · `PaletteRot` {"pitch": 0, "yaw": 146.1207, "roll": -37.3071} · `SelectLift` 0.5 · `NoDrawRadius` 14 · `StartSize` 0.45 · `bSizeByStick` false · `SliderMinSize` 0.5 · `SliderMaxSize` 1.5 · `PaletteScale` 0.6 · `PaletteTilt` 0 · `PaletteBank` 0 · `PaletteSpin` 0 · `PaletteSide` 0 · `PaletteUp` 0 · `PaletteNear` 0

**08 TOUR** — `bForceTour` false

**10 TINTA** — `bInk` true · `InkMeters` 30

**11 CONTRATO** — `bContractTest` false · `ContractBeginDelay` 8 · `ContractFirewall` 240 · `IntroTime` 0.8 · `ContractPaletteDelay` 0.6

**Default** — `bReady` false · `RightAim` None · `LeftGrip` None · `Palette` None · `RightGrip` None · `bHapOn` false · `LoopComp` None · `LastClick` 0 · `ClickHapT` 0 · `HapState` 0 · `HapPhase` 0 · `bWasDrawing` false · `LastSlider` 0 · `SrcAim`  · `SrcPalGrip`  · `SrcDrawGrip`  · `LastStage` 0 · `OnStageFinished` () · `bSystemDone` false · `OutroT` 0 · `RHandS0` {"x": 0, "y": 0, "z": 0} · `LHandS0` {"x": 0, "y": 0, "z": 0} · `TipS0` {"x": 0, "y": 0, "z": 0} · `PalS0` {"x": 0, "y": 0, "z": 0} · `ChargeComp` None · `bCharging` false · `bTourMode` false · `bAwake` false · `bStageDone` false

_110 perillas listadas de 134 variables._

## Surrounding: la herramienta de dibujo — `BPC_TBTool_NC`

Nivel donde se ajusta: **L_TBTest_SC**. 

**09 DEBUG** — `bSynth` false · `SynthSpeed` 45 · `SynthR` 15 · `SynthDur` 8 · `SynthDelay` 3 · `bSynthDry` false

**Default** — `bDrawing` false · `Pressure` 1 · `BrushColor` {"r": 1, "g": 0.2635999917984009, "b": 0.03240000084042549, "a": 1} · `bCanDraw` true · `Tip` None · `Current` None · `StrokeHistory` [] · `BrushIndex` 0 · `Size01` 1 · `SizeRate` 0.6 · `RedoStack` [] · `CfgSwayOn` true · `CfgStrength` 1.5 · `CfgWave` 0.18 · `CfgSpeed` 0.5 · `CfgSpan` 40 · `CfgSpeedVar` 0.6 · `CfgScale` 0.03 · `CfgDir` {"x": 1, "y": 0.6, "z": 0.15} · `CfgFade` 1.2 · `GradColorB` {"r": 1, "g": 1, "b": 1, "a": 1} · `CfgGradOn` false · `CfgPrimaryAtTip` true · `CfgHideTime` 2 · `CfgShowTime` 2.5 · `CfgGap` 0.4 · `CfgCenterZ` false · `CfgSketchDist` 90 · `CfgSketchUp` 0 · `CfgSfxVol` 1 · `SketchPhase` 0 · `SketchT` 0 · `SketchSet` [] · `HideSound` {"refPath": "/Game/NeuralCanvas/Sound/VR_shep_scale_down_02.VR_shep_sc... · `ShowSound` {"refPath": "/Game/NeuralCanvas/Sound/VR_shep_scale_up_02.VR_shep_scal... · `BMin` {"x": 0, "y": 0, "z": 0} · `BMax` {"x": 0, "y": 0, "z": 0} · `CfgTaper` 6 · `SketchTarget` None · `CfgSpin` 20 · `CfgHold` 5 · `SketchPivot` {"x": 0, "y": 0, "z": 0} · `SketchAxis` {"x": 0, "y": 0, "z": 0} · `bPivotSet` false · `StageCount` 0 · `DrawTable` None · `TableHome` {"location": {"x": 0, "y": 0, "z": 0}, "rotation": {"pitch": 0, "yaw":... · `PrevPhase` 0 · `TableT` 10 · `CfgSizeLo` 0.5 · `CfgSizeHi` 1.5

_57 perillas listadas de 61 variables._

## Alma (la guia) — `BP_Alma_SC`

Nivel donde se ajusta: **todos**. Su aspecto vive en el material; aca la voz y los movimientos.

**0 - Cuerpo** — `Size` 0.6

**A - Deformacion** — `WobbleAmount` 0.096 · `WobbleFreq` 0.02 · `WobbleSpeed` 0.4

**B - Superficie** — `FresnelPower` 0.2 · `Brightness` 1 · `OpacityCore` 0.2 · `OpacityRim` 0.25 · `CoreColor` {"r": 0.6000000238418579, "g": 0.5400000214576721, "b": 1, "a": 1} · `RimColor` {"r": 0.15892000496387482, "g": 0.14583300054073334, "b": 1, "a": 1}

**C - Gradiente** — `GradFreq` 0.01 · `GradSpeed` 0.25 · `GradAmount` 0.468641 · `GradColorA` {"r": 1, "g": 0.096949003636837, "b": 0.4557630121707916, "a": 1} · `GradColorB` {"r": 0.47788500785827637, "g": 0.33881399035453796, "b": 1, "a": 1}

**D - Borde** — `EdgePower` 1.87 · `EdgeIntensity` 1.4 · `EdgeColor` {"r": 0.05597899854183197, "g": 0.08929699659347534, "b": 1, "a": 1}

**Default** — `OnVOFinished` () · `FoundScl` 1 · `TravelSclFrom` 1 · `TravelSclTo` 1 · `AuraRef` None

**E - Flotar** — `FloatAmount` {"x": 3.958462, "y": 3.752256, "z": 4.309997} · `FloatSpeed` 0.1 · `RotAmount` {"pitch": 5, "yaw": 8, "roll": 5} · `RotSpeed` 0.1 · `PhaseSeed` 0.344

**F - Aparicion** — `AppearTime` 1.2 · `DisappearTime` 0.6

**G - Recorrido** — `TravelTime` 3

**H - Test** — `bDebugKeys` true · `DebugPoints` ["alma_hall_appear","alma_hall_move","alma_entering_appear","alma_ente... · `SayTestClip` {"refPath": "/Game/SoulCharger/Core/Audio/VO/Voice_Over_2.Voice_Over_2... · `bSayTest` false

**I - Voz** — `VOClips` ["None",{"refPath":"/Game/SoulCharger/Core/Audio/VO/Voice_Over_1.Voice... · `bStartHidden` true · `VOVolume` 1 · `VODelayIn` 0 · `VODelayOut` 0 · `VOReact` 1 · `VOReactWobble` 0.8 · `VOReactBright` 0.35 · `VOReactSize` 0.05 · `VOAttack` 0.12 · `VORelease` 0.35 · `VOGain` 3 · `VOReactWarm` 0.35 · `VOWarmColor` {"r": 1, "g": 0.7200000286102295, "b": 0.5, "a": 1}

**J - Aura** — `AuraAlpha` 0.35 · `AuraSize` 0.16 · `AuraTwinkle` 0.45 · `AuraCurl` 5.5 · `AuraFlow` 0.35 · `AuraGlow` 1

_55 perillas listadas de 73 variables._

## El HUD (pildora) — `BP_SoulHUD3D_SC`

Nivel donde se ajusta: **L_SoulCharger_Obra**. 

**Default** — `HudScale` 1 · `HudCurve` 0 · `FrameOpacity` 0.45 · `GlassOpacity` 0.3

_4 perillas listadas de 4 variables._

## La carga del anillo — `BP_ChargeFx_SC`

Nivel donde se ajusta: **L_SoulCharger_Obra**. 

**Default** — `AutoStart` false · `StartAfter` 9.5 · `ChargeTime` 4 · `BigScale` 1 · `PopHudSize` 3 · `StageColor` {"r": 0.10999999940395355, "g": 0.20999999344348907, "b": 0.75, "a": 1... · `StartTime` 0 · `Running` false · `RestRingLoc` {"x": 0, "y": 0, "z": 0} · `RestRingScale` {"x": 0, "y": 0, "z": 0} · `RestSoulScale` {"x": 0, "y": 0, "z": 0} · `HudRef` None · `TargetRef` None · `WarnSound` {"refPath": "/Game/SoulCharger/Core/Audio/Sounds/ProtoHover.ProtoHover... · `PopOutSound` {"refPath": "/Game/SoulCharger/Core/Audio/Sounds/SBubbleHoverOut.SBubb... · `PopInSound` {"refPath": "/Game/SoulCharger/Core/Audio/Sounds/SBubbleHoverOn.SBubbl... · `ChargeSound` {"refPath": "/Game/SoulCharger/Core/Audio/Sounds/Charge1.Charge1"} · `SettleSound` {"refPath": "/Game/SoulCharger/Core/Audio/Sounds/ProtoSelect.ProtoSele... · `HoldTime` 2 · `CavParam` Charge_Entering · `SpinDeg` -450 · `FinalBurst` false · `BurstIdx` 0 · `RingShow` true · `RingK` 1 · `MuteFeel` false

_26 perillas listadas de 26 variables._

## El objeto de la mano (mando/sensor) — `BP_UserTool_SC`

Nivel donde se ajusta: **L_SoulCharger_Obra**. 

**A-Herramienta** — `bRight` true · `bShowMandoOnBegin` false · `MorphTime` 0.8 · `ColorTime` 1.2 · `LightColor` {"r": 1, "g": 0.7200000286102295, "b": 0.44999998807907104, "a": 1} · `SensorXfR` {"location":{"x":4.324999,"y":-1.6850000000000001,"z":-2.3351850000000... · `SensorXfL` {"location":{"x":4.324999,"y":1.6850000000000001,"z":-2.33518500000000... · `MandoXfR` {"location":{"x":5.6859419999999998,"y":0.540018,"z":-1.677589},"rotat... · `MandoXfL` {"location":{"x":5.8765140000000002,"y":-1.566667,"z":-2.0496370000000... · `MandoSound` {"refPath": "/Game/SoulCharger/Calibration/Audio/Tomado.Tomado"}

**Default** — `TrigDegrees` 14 · `TrigSign` -1 · `TrigFollow` 25 · `TrigV` 0 · `bTrigInput` false · `TrigAxisR` {"x": 0.976, "y": -0.2177, "z": -0.0083} · `TrigAxisL` {"x": 0.976, "y": 0.2177, "z": 0.0083}

_17 perillas listadas de 29 variables._

## Los fantasmas de instrucciones — `BP_GhostPlayer_SC`

Nivel donde se ajusta: **L_SoulCharger_Obra**. 

**Ghost** — `StepHz` 30 · `EchoAlpha` [1] · `GhostOpacity` 0.85 · `FadeIn` 0.4 · `FadeOut` 0.6 · `LoopGap` 0.4 · `LoopFade` 0.3 · `bShowText` true · `TextOffset` {"x": 60, "y": 0, "z": -40} · `TextSize` 2.4 · `TextColor` {"r": 0.8999999761581421, "g": 0.8999999761581421, "b": 0.879999995231... · `AppearSound` None · `VanishSound` None · `SfxVol` 0.8 · `BeamLength` 140 · `BeamRadius` 0.22 · `AutoPlayDelay` 2 · `Take` None · `FollowTag` None · `bPreview` true · `PreviewTime` 0.5 · `PreviewPoses` 10 · `PreviewOnion` 0.2 · `PathDot` 0.012 · `GhostColor` {"r": 0.7799999713897705, "g": 0.8799999952316284, "b": 1, "a": 1} · `TriggerColor` {"r": 1, "g": 0.6200000047683716, "b": 0.25, "a": 1} · `TriggerGlow` 3 · `OrbRest` {"x": 600, "y": 150, "z": 120} · `OrbSize` 18 · `OrbHoldDist` 80 · `OrbSpeed` 1.5 · `OrbGrab` 30 · `StrokeWidth` 0.8 · `bAutoPlay` false · `LiveOpacity` 0.7 · `bAutoMirror` false · `PlayRate` 1.25 · `LoopEnd` 0

**GhostMesh** — `BodyMeshR` {"refPath": "/Game/SoulCharger/Mechanics/QuestController/SM_QuestCtrl_... · `BodyMeshL` {"refPath": "/Game/SoulCharger/Mechanics/QuestController/SM_QuestCtrl_... · `TrigMeshR` {"refPath": "/Game/SoulCharger/Mechanics/QuestController/SM_QuestCtrl_... · `TrigMeshL` {"refPath": "/Game/SoulCharger/Mechanics/QuestController/SM_QuestCtrl_... · `BeamMesh` {"refPath": "/Engine/BasicShapes/Cylinder.Cylinder"} · `GhostMat` {"refPath": "/Game/SoulCharger/Mechanics/Ghost/M_Ghost_SC.M_Ghost_SC"} · `TextMat` {"refPath": "/Game/SoulCharger/Core/UI/Materials/M_TextUnlit.M_TextUnl... · `GripToMeshR` {"location":{"x":5.6859419999999998,"y":0.540018,"z":-1.677589},"rotat... · `GripToMeshL` {"location":{"x":5.8765140000000002,"y":-1.566667,"z":-2.0496370000000... · `HingePivotR` {"x": 1.565, "y": 2.432, "z": -0.145} · `HingeAxisR` {"x": 0.976, "y": -0.2177, "z": -0.0083} · `PressDegrees` 14 · `PressSign` -1 · `SensorMesh` {"refPath": "/Game/SoulCharger/Mechanics/BioSensor/SM_BioSensor_SC.SM_... · `SaveMesh` {"refPath": "/Game/SoulCharger/Mechanics/SaveMelody/SM_SaveMelody_Plat... · `PaletteMesh` {"refPath": "/Game/SoulCharger/Mechanics/DrawPalette/SM_DrawPalette_Ba... · `OrbMesh` {"refPath": "/Engine/BasicShapes/Sphere.Sphere"} · `StrokeMesh` {"refPath": "/Engine/BasicShapes/Cylinder.Cylinder"} · `PathMesh` {"refPath": "/Engine/BasicShapes/Sphere.Sphere"} · `HandXfR` {"location":{"x":-2.9812599999999998,"y":3.5,"z":4.5617530000000004},"... · `HandXfL` {"location":{"x":-2.9812599999999998,"y":-3.5,"z":4.5617530000000004},... · `SensorXf` {"location":{"x":4.3250000000000002,"y":-1.6850000000000001,"z":-2.335... · `SaveXf` {"location":{"x":5.5700000000000003,"y":0.80000000000000004,"z":-2.080... · `PaletteXf` {"location":{"x":2.1899999999999999,"y":2.7599999999999998,"z":7.50999... · `TipOffset` {"x": 2.5, "y": 0, "z": 0}

_63 perillas listadas de 126 variables._

## Resultados: el contenido — `BP_JourneyContent_SC`

Nivel donde se ajusta: **L_SoulCharger_Obra**. 

**Journey** — `BreathScores` [0.62, 0.83, 1, 0.71] · `Minutes` 0 · `StageColors` [{"r":0.10899999737739563,"g":0.21199999749660492,"b":0.74500000476837... · `Cream` {"r": 0.8790000081062317, "g": 0.8389999866485596, "b": 0.760999977588... · `Grey` {"r": 0.8389999866485596, "g": 0.8069999814033508, "b": 0.745000004768... · `FontPx` 24 · `bPreviewInEditor` false · `ClickVol` 1 · `TipKeys` ["calm", "heart", "breath", "melody", "soul", "drawing"] · `TipNames` ["CALM", "HEART RATE", "BREATH", "YOUR MELODY", "YOUR SOUL", "YOUR DRA... · `TipStage` [2, 1, 0, 3, -1, 4] · `TipTexts` ["The calm of your mind across the whole journey, read from your brain... · `ClickSound` {"refPath": "/Game/NeuralCanvas/Sound/VR_click1.VR_click1"} · `bBuildOnPlay` false

_14 perillas listadas de 45 variables._

## Resultados: el cuadro — `BP_ResultsArt_SC`

Nivel donde se ajusta: **L_SoulCharger_Obra**. 

**Default** — `AppearOnPlay` false · `AppearDelay` 3 · `Waiting` false · `WaitLeft` 0 · `LastT` -1 · `LastTipK` -1 · `TipK` 0 · `TipTarget` 0 · `RestGlass` {"location": {"x": 0, "y": 0, "z": 0}, "rotation": {"pitch": 0, "yaw":... · `RestWinCalm` {"location": {"x": 0, "y": 0, "z": 0}, "rotation": {"pitch": 0, "yaw":... · `RestWinHeart` {"location": {"x": 0, "y": 0, "z": 0}, "rotation": {"pitch": 0, "yaw":... · `RestWinBreath` {"location": {"x": 0, "y": 0, "z": 0}, "rotation": {"pitch": 0, "yaw":... · `RestWinMelody` {"location": {"x": 0, "y": 0, "z": 0}, "rotation": {"pitch": 0, "yaw":... · `RestTip` {"location": {"x": 0, "y": 0, "z": 0}, "rotation": {"pitch": 0, "yaw":... · `KTitle` 0 · `KCalm` 0 · `KHeart` 0 · `KBreath` 0 · `KMelody` 0 · `KTip` 0

_20 perillas listadas de 20 variables._

