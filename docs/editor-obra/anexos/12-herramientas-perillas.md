> Anexo de la auditoría de herramientas del 2026-10-01 (revisión: perillas y roles). Lo que manda es [PLAN-EDITOR-OBRA-2026-10-01.md](../PLAN-EDITOR-OBRA-2026-10-01.md).

## Veredicto por herramienta

Abreviaturas: **MOCK** = `web/editor-obra/mockup/src-body.html` · **PLAN** = `docs/editor-obra/PLAN-EDITOR-OBRA-2026-10-01.md` · **TRK/** = `.claude/skills/unreal-vr/blueprints/` · **MAPA** = `docs/MAPA-DE-AJUSTES.md` · **DUMP** = `VR_Test/Saved/ClaudeScripts/obra/dump/obra_all_now.txt` (13:07) · **HDUMP** = `…/obra/dump/hall.txt` · **CS/** = `VR_Test/Saved/ClaudeScripts/`

| Herramienta (maqueta) | Estado | Evidencia | Qué cambiar |
|---|---|---|---|
| Bell · Appear 1.5 s | OK (falta indicar el dueño) | MOCK:242 · TRK/BPC_AppearLuz_SC.md:29 (`Duration` 1,5, instance-editable), :65 | En el tooltip: `Appear.Duration` del componente de `Timbre` (BP_BellArt_SC, Test_Hall/Ajustes) |
| Bell · Press depth 1.0 cm | Corregir el dueño (valor y unidad bien) | MOCK:242 (tooltip `BellPressDepth` sin BP, bajo el encabezado "From BP_BellArt_SC") · TRK/BP_HallDirector_SC.md:107, :120 · HDUMP:427 | Poner `BellPressDepth · HallDirector (BP_HallDirector_SC, Test_Hall)`. La unidad cm es correcta (unidades de Unreal) |
| Bell · Press time 0.12 s | Corregir el dueño + Verificar en vivo | MOCK:242 · TRK/BP_HallDirector_SC.md:99-107 (nació en la tanda T4 con la instancia colocada) · TRK/../references/gotchas.md:2694 | Mismo dueño. Leer el valor de la instancia: puede haber nacido en 0 |
| Bell · Hold to ring 3.0 s | OK | MOCK:242 · TRK/BP_HallDirector_SC.md:56 · HDUMP:425 | Agregar el candado (valor de test final) y el literal de descarga −2/s al soltar |
| Bell · Timeout 25 s | Corregir la semántica | MOCK:242 · HDUMP:425 (pasado `FW_Bell` la carga sube sola a 1/`BellHold`) | Mostrar "25 s + 3 s de autollenado ≈ 28 s" |
| Bell · Used in "2.6 · Hall exit" | Corregir | MOCK:241 · TRK/BP_HallDirector_SC.md:19 (el regreso abre "sin timbre") · docs/GUION-V5-2026-09-29.md:329 (2.6 es "Tu alma") | Dejar solo 1.7/1.8 (pasos 6-7 de HallIntro) |
| Bell · Sounds FX_BELL* | Falta en Unreal | MOCK:241 · TRK/BP_BellArt_SC.md:41 (`AppearSound/VanishSound` pendientes) · TRK/BP_HallDirector_SC.md:185 (el real es `SndBell`=`Bell`, al tocar) | Listar `Bell` (SndBell, al tocar, FadeOut 0,5). Marcar FX_BELLAPPEAR/VANISH como "no asignados" |
| Bio sensor · Appear 1.5 s | OK, pero son dos actores | MOCK:244 · TRK/BP_HallDirector_SC.md:160 (`Sensor` del Hall) · TRK/BP_UserTool_SC.md:14, :19 (`UserTool_Obra`) | Separar "Sensor del Hall" (BP_BioSensorArt_SC) de "Sensor en mano" (UserTool_Obra) |
| Bio sensor · Tool delay 0.8 s | OK, el dueño es otro | MOCK:244 · TRK/BP_BreathStage_SC.md:86 | Moverlo a un rol "Stage · Entering" (`Entering_Stage`) |
| Bio sensor · "Rings on · sensor resting" (BIO_ON) | Falta en Unreal / Verificar en vivo | MOCK:278 · CS/obra/dump/waves.json:1 (el material tiene `Active`) · CS/obra/dump/usertool_all.txt:27 (solo se escribe `Color`) | Marcarlo "solo previs" hasta confirmar quién escribe `Active` |
| Pacer · Cycles 5 | OK | MOCK:246 · MAPA:176 · TRK/BP_Pacer_SC.md:72 | Candado |
| Pacer · Rhythm 4-3-4-3 (texto) | Corregir | MOCK:246 · MAPA:176 (`Preset` tiene que ser 0) · TRK/BP_Pacer_SC.md:86 (sonidos horneados a 4-3-4-3) | Cuatro perillas: `InhaleTime`/`Hold1Time`/`ExhaleTime`/`Hold2Time`, más `Preset`, más un aviso de "regenerar audio" |
| Pacer · Lead-in 3.0 s | OK | MOCK:246 · TRK/BP_Pacer_SC.md:99 | Agregar `LeadOut` 3 s |
| Pacer · Count 3.0 s | Corregir valor y dueño | MOCK:246 · PLAN:170 · TRK/BP_BreathStage_SC.md:95 (`CountTime` 3 → **3,6**) | 3,6 s en `Entering_Stage`. Agregar `InhaleCueAt` 3,48 (:97) |
| Pacer · "Appears still" en 1.R3 (PACER_DIM) | Falta en Unreal | MOCK:279 · TRK/BP_Pacer_SC.md:35 (BeginPlay `EnvT` 0, invisible) · TRK/BP_BreathStage_SC.md:95 (`PacerPlay` recién con la cuenta) | Insignia "preview only", o pedir la función en Unreal |
| Alma · Size 1.0 (sin unidad) | Corregir | MOCK:248 · TRK/BP_Alma_SC.md:69 (diámetro en m) · CS/Obra/alma_diff.json:95 (CDO 0,6 → instancia 1) · DUMP:2117-2125 (la escala del actor = escala X del TP) | Unidad "m (diámetro)". Mostrar el tamaño efectivo = `Size` × escala del TP |
| Alma · Brightness 1.5 | OK | MOCK:248 · CS/Obra/alma_diff.json:15 (CDO 1 → instancia 1,5) | Candado. Corregir TRK/BP_Alma_SC.md:71, que dice que el CDO es 1,5 |
| Alma · Stays "VO + 3 s" | Corregir + Verificar en vivo | MOCK:248 · DUMP:968, :977 (habla a +1,5 s y `AlmaTime` = VODur + 3,5) · DUMP:1459-1468 (lo pisa `StAlma[K]` y lo sube a ≥ VODur + 2,5) · TRK/BP_Obra_SC.md:296 (dice VODur + 3, sin StAlma) | Marcar como literal de `BP_Obra_SC` (no es perilla), con la regla real "aire tras la voz = AlmaTime − 1,5 − VODur" |
| Alma · "Light first · Alma" (AP1, 1,5 s) | Corregir | MOCK:283 · CS/obra/dump/alma.txt:256 (sin componente Appear) · TRK/BP_Alma_SC.md:75 (escala 0 → `Size` en `AppearTime` 1,2) | Alma aparece por escala en 1,2 s. AL_IN (MOCK:274, 1,2 s) es correcto, AP1 no |
| Metaball · Explore 12 s | Corregir el dueño y la semántica | MOCK:250, :260 · TRK/BP_BreathStage_SC.md:86, :103 (la cuenta espera la cadena de VO: mínimo 12 s, elástica) | Va en "Stage · Entering". Dibujar LIBRE como elástica (mínimo 12 s, hasta que VO_12 termina + 0,3 s) |
| Metaball · BLOB_IN 4 s | Corregir | MOCK:276 · TRK/BP_BreathBlob_SC.md:83 (`IntroTime` 2,5) | 2,5 s. Las perillas propias del metaball son `SizeCM`, `IntroTime`, `OutroTime` y `Brightness` |
| Place · Stop "sc0 · Entering" | OK solo para etapas | MOCK:471 · TRK/BP_StageRunner_SC.md:4 · MAPA:126 | En el Hall el marco es el `HallDirector`, con flechas `Stop*` (TRK/BP_HallDirector_SC.md:30). En el final es `StopCard`/`StopExit` |
| Place · Front/Side/Height | Corregir | MOCK:471 (2.20/−0.90/+0.05 en todo clip de objeto) · CS/Obra/ensayo_export.py:3, :58 · CS/Obra/ensayo_export.json:20-25 (alma_side 140/−300/+20) | Valores por elemento. Side + = derecha. Height = sobre el ojo de autor (piso + 120). Sin Place para el sensor en mano |
| Place · Scale 1.00 × | Corregir (significa algo distinto en cada rol) | MOCK:471 · TRK/BP_Obra_SC.md:232 (TP lateral 0,6) · TRK/BP_BreathBlob_SC.md:23 (`SizeCM`, el CS pisa la escala) · MAPA:83, :134 | Semántica por rol (ver catálogo). Para el metaball y el pacer, "Size cm" en vez de escala |
| Place · "el gizmo edita la marca" | Riesgo | PLAN:192 · TRK/BP_HallDirector_SC.md:165 (ya no hay marcas en el Hall) · TRK/BP_Obra_SC.md:178-184 | La marca es el TP solo para Alma, la carga, el título, el sketch, el pez y la elegida. En Timbre, Sensor, HallSoul_N, TituloInicio y Final_* el gizmo mueve el actor |
| Place · falta el giro | Corregir | DUMP:1482-1486 (`TitleTP` usa el yaw del TP) · TRK/BP_Obra_SC.md:180 (botones pitch 15) | Agregar Yaw (y Pitch donde aplique) |
| Biblioteca de roles · nombres de malla | Corregir | MOCK:328 (`SM_HUD_SC`, `SM_Results_SC`, `SM_DrawPalette_SC`, `SM_QuestCtrl_SC` no existen como asset; el árbol de `VR_Test/Content` tiene `SM_HUDBezel_SC`, `SM_ResultsRim_SC`, `SM_DrawPalette_Base_SC`, `SM_QuestCtrl_Body_R_SC`) | Referir roles por actor, BP y tag (PLAN:240-241: "rol que Unreal resuelve por tag") |
| Origen del valor (candado) | Falta en la maqueta | PLAN:178 · MOCK:432 (`knobRows` no pasa `lock`) | Candado en toda perilla de instancia de un nivel de test |

## Hallazgos importantes

1. **Las perillas del timbre se atribuyen al objeto, pero viven en el director.** El encabezado dice "From BP_BellArt_SC" (MOCK:241, :432). Sin embargo, `BellPressDepth`, `BellPressTime`, `BellHold`, `FW_Bell` y `TouchRadius` son de `HallDirector` (TRK/BP_HallDirector_SC.md:56, :107; HDUMP:425-427). Una propuesta del editor iría al actor equivocado. **Corrección:** cada perilla lleva su propio `owner` (actor, nivel y clase), no el del rol.

2. **Hay valores que se muestran como perilla y son literales de grafo, o que están desactualizados.**
   - `CountTime` es 3,6 y no 3 (TRK/BP_BreathStage_SC.md:95). El mismo error está en PLAN:170 y en MAPA:178.
   - "Stays VO + 3" no es una variable. El volcado de las 13:07 dice VODur + 3,5, y `StageTimes` lo pisa con `StAlma[K]` (DUMP:977, :1459-1468). El tracker dice que después quedó VODur + 3 (TRK/BP_Obra_SC.md:296). Además, la voz entra 1,5 s después de aparecer (literal, DUMP:968).
   - **Corrección:** tres tipos de origen en el inspector: `instancia`, `CDO` y `literal (requiere cirugía U2)`. Un literal no se puede proponer como perilla.

3. **El bloque Place es el mismo para todo objeto y sus números no corresponden a ningún punto real.**
   - 2.20 / −0.90 / +0.05 / 1.00 (MOCK:471) mezcla `alma_in` (220/0/+5) con un costado inventado. `sc0_alma_side` es 140 / −300 / +20 (CS/Obra/ensayo_export.json:20-25), con escala 0,6 hoy (TRK/BP_Obra_SC.md:232).
   - El sensor en mano no tiene parada: su pose es `SensorXfR` respecto del grip (TRK/BP_UserTool_SC.md:22).
   - El metaball y el pacer son transforms de actor en coordenadas de mundo: (380, 0, 125) y (200, 0, 70) con pitch 90 (MAPA:156-158). Su tamaño es `SizeCM`/`SizeCm`, porque el CS pisa la escala (TRK/BP_BreathBlob_SC.md:23).
   - **Corrección:** Place por tipo de anclaje: TP de etapa, actor del Hall, actor del final, pose en mano o actor de etapa.

4. **Las convenciones de Place no están declaradas.**
   - El exportador define side + = derecha y up = sobre `PlayerStart.z + EyeRef` 120 (CS/Obra/ensayo_export.py:3, :58).
   - La corrección de altura en runtime no es la misma en todos lados:
     - en las etapas, contra `StartLoc[K].z + 120` (DUMP:1437-1446);
     - en el Hall y el final, contra `pawn.z + 120` (TRK/BP_HallDirector_SC.md:160, TRK/BP_Obra_SC.md:186).
   - No hay evidencia de que `Entering_Blob` y `Entering_Pacer` se corrijan por altura (sus trackers no lo dicen).
   - **Corrección:** declarar en la UI "Side: + derecha" y "Height: sobre el ojo de autor (piso + 1,20 m)", y marcar el metaball y el pacer como "altura absoluta" hasta verificarlo.

5. **"El gizmo edita la marca" (PLAN:192) ya no vale para el Hall ni para el final.** Las marcas `BP_AuthorMark_SC` se retiraron, y `Timbre` y `Sensor` son actores reales con tag `hall_bell`/`hall_sensor` (TRK/BP_HallDirector_SC.md:158-165). Lo mismo pasa con `Final_*` (TRK/BP_Obra_SC.md:178-183). **Corrección:** el gizmo mueve el TP o el actor según el rol, y el plan tiene que decirlo.

6. **La maqueta muestra en Entering cosas que Unreal no hace.**
   - El pacer quieto en 1.R3: en Unreal nace invisible (TRK/BP_Pacer_SC.md:35).
   - "Rings on" con el sensor apoyado: nadie escribe `Active` (CS/obra/dump/usertool_all.txt:27).
   - "Light first · Alma" (MOCK:283): Alma aparece por escala (CS/obra/dump/alma.txt:256).
   - De otras familias, pero tocan estos roles: no existe una espera `G_BREATH` con timeout 25 s. La exploración se mide por tiempo y espera a la VO, y `VO_11h` sale `HelpAfter` 4 s después de `VO_11b`, solo si `Rig.bZone` es false (TRK/BP_BreathStage_SC.md:103-105). La maqueta pone la ayuda a los 12 s (MOCK:259, :269).
   - **Corrección:** insignia "preview only" en esos clips.

7. **La escala efectiva de Alma es `Size` × escala del TP, y eso no se ve.** `AlmaSclIn`/`AlmaSclAside` copian la escala X de `ObraAlmaA/B`, que viene del TP (DUMP:2117-2131). Los laterales están en 0,6 y `hall_alma_side` en 0,5 (TRK/BP_Obra_SC.md:232, :360). **Corrección:** en el inspector de Alma, "Size 1,00 m × 0,6 en este punto = 0,60 m".

8. **Hay dos Almas con look distinto según dónde se pruebe.** `Alma_HallTest` (TestOnly) tenía Size 0,864, Brightness 1,0956 y OpacityCore 1,62. `Obra_Alma` tiene 1 y 1,5 (CS/Obra/alma_diff.json:123, :219). Ensayar en Test_Hall muestra otra Alma que la de la Obra. **Corrección:** la cosecha lee siempre `Obra_Alma` del persistente.

9. **Riesgo de doble giro del sensor del Hall.** `BP_SensorOrb_SC.OrbLive` lo gira `SpinDeg` (15, MAPA:64; CS/obra/dump/orb.txt:12). A la vez, `HallSensorSpin` le suma 40°/s literal mientras `SensorLive` (TRK/BP_HallDirector_SC.md:186). Una perilla "giro" en el editor no controlaría el giro total.

10. **Los documentos de referencia ya divergieron de los trackers.** Si la cosecha o la web se apoyan en MAPA, van a mostrar valores viejos:

    | Perilla | MAPA | Tracker |
    |---|---|---|
    | `StageBeats` | 38 (MAPA:228) | 19 (TRK/BP_HeartManager_SC.md:170) |
    | `BeatDiv` | 1 (MAPA:242) | 2 (TRK/BP_HeartManager_SC.md:170) |
    | `BackupAfter` | 8 (MAPA:233) | 30 (TRK/BP_HeartManager_SC.md:173) |
    | `StageDuration` | 80 (MAPA:277) | 60 (TRK/BP_LovingCell_SC.md:73) |
    | `OutTime` / `ExitTime` | 11 / 12 (MAPA:55) | 8 / 7 (TRK/BP_HallDirector_SC.md:184) |

    Además, `ensayo_export.json` es del 09-30 y trae `alma_side` en escala 1 (:25). **Corrección:** el catálogo sale solo de la cosecha en vivo.

11. **Los roles mezclan perillas de la etapa.** `ToolDelay`, `CountTime` y `ExploreTime` son de `Entering_Stage`, no del sensor, el pacer ni el metaball (MOCK:244-250). **Corrección:** crear el rol "Stage · Entering" con esas perillas más `InhaleCueAt`, `HelpAfter`, `SayAfterTool`, `SayGap` y `SensorColor`.

### Catálogo v0 de perillas por rol (solo variables que existen)

| Rol | Perilla (nombre de cine) | Variable real | Dónde vive | Valor | Unidad | Editable |
|---|---|---|---|---|---|---|
| Timbre | Aparición | `Appear.Duration` | componente de `Timbre` (BP_BellArt_SC), Test_Hall | 1,5 (TRK/BPC_AppearLuz_SC.md:29) | s | instancia (componente) |
| Timbre | Lugar, giro y tamaño | transform de `Timbre` (tag `hall_bell`) | Test_Hall/Ajustes | — (MAPA:66) | cm/°/× | actor |
| Timbre | Hundido al apretar | `BellPressDepth` | HallDirector, Test_Hall | 1,0 (TRK/BP_HallDirector_SC.md:107) | cm | instancia (verificar) |
| Timbre | Velocidad del hundido | `BellPressTime` | HallDirector | 0,12 (:107) | s | instancia (verificar) |
| Timbre | Sostener para sonar | `BellHold` | HallDirector | 3 (:56) | s | instancia |
| Timbre | Cortafuegos | `FW_Bell` | HallDirector | 25 + autollenado (HDUMP:425) | s | instancia |
| Timbre | Radio de toque | `TouchRadius` | HallDirector | 14 (:56) | cm | instancia |
| Timbre | Descarga al soltar | literal −2/s | `HallTickTouch` | −2 (HDUMP:425) | 1/s | literal |
| Timbre | Sonido al tocar | `SndBell` (`Bell`) | HallDirector | Bell (:57, :185) | asset | instancia |
| Sensor (Hall) | Lugar | transform de `Sensor` (tag `hall_sensor`) | Test_Hall/Ajustes | — (MAPA:67) | cm/° | actor |
| Sensor (Hall) | Giro y orbe | `SpinDeg`, `OrbSize`, `AppearTime`, `BurstTime`, `BurstGrow` | `HallSensorOrb` | 15 · 0,5 · 1,6 · 0,7 · 0,3 (MAPA:64) | °/s, ×, s | instancia |
| Sensor (Hall) | Cortafuegos para tomarlo | `FW_Tool` | HallDirector | 20 (:56) | s | instancia |
| Sensor (mano) | Pose en la mano | `SensorXfR/L` | UserTool_Obra (persistente de la Obra) | (4,325; −1,685; −2,335) roll 90 (TRK/BP_UserTool_SC.md:22) | cm/° | instancia |
| Sensor (mano) | Mando → sensor, color | `MorphTime`, `ColorTime` | UserTool_Obra | 0,8 · 1,2 (:27) | s | instancia |
| Candidatas | Lugar | transform de `HallSoul_0..4` | Test_Hall | Y ±27/±54 (TRK/BP_Obra_SC.md:365) | cm | actor |
| Candidatas | Tamaño y color | `Size`, `CoreColor`, `EdgeColor`, `GradColorA/B` | HallSoul_N | 0,15 (MAPA:69) | m (diámetro) | instancia |
| Candidatas | Tamaño de la elegida | escala X de `TP_hall_soul_present` | Test_Hall | 0,7 (TRK/BP_Obra_SC.md:366) | × = Size | TP |
| Candidatas | Cortafuegos | `FW_Choose` | HallDirector | 25 (:56) | s | instancia |
| Puertas | Apertura y tiempo | `DoorOpenDeg`, `DoorTime` | HallDirector | 16,5 · 3 (:55) | °, s | instancia |
| Puertas | Vidrio cálido/frío | `DoorWarm`, `DoorCold` | HallDirector | (1; 0,72; 0,40) · (0,55; 0,64; 0,82) (:55, :75) | lineal | instancia + CDO |
| Baldosas | Subida, brillo, tiempo | `TileLiftCm`, `TileGlowMax`, `TileTime`, `ReturnGlow` | HallDirector | 3 · 0,35 · 1,5 · 0,6 (:55) | cm, —, s | instancia |
| Baldosas | Atenuación del reposo | `RestDim` | material `M_Hall_Tile_SC` | 0,7 (:177) | — | CDO del material |
| Baldosas | Nombres de etapa | componentes `Title0..4` | HallDirector | — (MAPA:60) | transform | componente |
| Título inicio | Lugar y tamaño | transform de `TituloInicio` + `TitleP`/`SubP`/`Logo*` | Test_Hall/Ajustes | (−3600; 0; 151,97) (TRK/BP_IntroTitle_SC.md:25) | cm/× | actor |
| Título inicio | Tiempos | 2,5 · 3→6,5 · 5→7,5 · 10→12,5 · 13 | `IntroTitle` (Obra) + `HRTitle` (duplicado) | (TRK/BP_IntroTitle_SC.md:21) | s | literal |
| Stage · Entering | Exploración libre (mínimo) | `ExploreTime` | `Entering_Stage`, Test_Entering | 12 (TRK/BP_BreathStage_SC.md:86) | s | instancia |
| Stage · Entering | Cuenta "three, two, one" | `CountTime` | Entering_Stage | 3,6 (:95) | s | CDO (la instancia hereda) |
| Stage · Entering | Momento del "inhale" | `InhaleCueAt` | Entering_Stage | 3,48 (:97) | s | instancia/CDO |
| Stage · Entering | Llega el sensor | `ToolDelay` | Entering_Stage | 0,8 (:86) | s | instancia |
| Stage · Entering | Ayuda sin zona | `HelpAfter` | Entering_Stage | 4 (:105) | s tras VO_11b | instancia |
| Stage · Entering | Aire entre voces | `SayAfterTool`, `SayGap` | Entering_Stage | 1 · 0,5 (:105) | s | instancia |
| Stage · Entering | Color del sensor | `SensorColor` | Entering_Stage | (0,35; 0,7; 1) (MAPA:170) | lineal | instancia |
| Pacer | Ciclos | `Cycles` | `Entering_Pacer` | 5 (MAPA:176) | — | instancia |
| Pacer | Ritmo | `InhaleTime`/`Hold1Time`/`ExhaleTime`/`Hold2Time` (+`Preset` 0) | Entering_Pacer | 4/3/4/3 (MAPA:176) | s | instancia (audio horneado, TRK/BP_Pacer_SC.md:86) |
| Pacer | Pausas | `LeadIn`, `LeadOut` | Entering_Pacer | 3 · 3 (MAPA:177) | s | instancia |
| Pacer | Crece / se achica | `IntroTime`, `OutroTime` | BP_Pacer_SC | 0,6 · 0,6 (TRK/BP_Pacer_SC.md:34) | s | CDO |
| Pacer | Tamaño y lugar | `SizeCm` + transform | Entering_Pacer | 350 · (200; 0; 70) pitch 90 (MAPA:158) | cm | instancia/actor |
| Pacer | Brillo y halo | `Brightness`, `HaloStrength`, `HaloFadeOut` | Entering_Pacer | 1,43 · 0,55 · 1,5 (MAPA:167, :177) | —, s | instancia |
| Metaball | Tamaño | `SizeCM` | `Entering_Blob` | 220 (MAPA:157) | cm | instancia |
| Metaball | Lugar | transform | Entering_Blob | (380; 0; 125) (MAPA:156) | cm | actor |
| Metaball | Nace / se va (morfeo) | `IntroTime`, `OutroTime` | Entering_Blob | 2,5 · 2,5 (TRK/BP_BreathBlob_SC.md:77, :83) | s | instancia |
| Metaball | Brillo y reacción | `Brightness`, `BreathSpreadIn/Out`, `BreathCurlIn`, `BreathRadiusOut` | Entering_Blob | 1,546 · −0,85/0,6 · −0,7 · −0,15 (MAPA:166, :188) | factor | instancia |
| Membrana | Esfera | `HeartSize`, `HeartHeight`, `HeartPush` | `HeartScape`, Test_Heart | 68,1 · 113 · 24,4 (MAPA:209-210) | cm (verificar) | instancia |
| Membrana | Largo y vuelta | `StageBeats`, `BeatDiv`, `OrbitAtBeat`, `OrbitTime` | HeartManager / HeartScape | 19 · 2 · 8 · 60 (TRK/BP_HeartManager_SC.md:170; MAPA:230) | pulsos, s | instancia (verificar) |
| Membrana | Respaldo sin mano | `BackupAfter` | HeartManager | 30 (TRK/BP_HeartManager_SC.md:173) | s | instancia |
| Membrana | Color del sensor | `SensorColor` | HeartManager | (1; 0,34; 0,28) (:156) | lineal | instancia |
| Célula | Largo | `StageDuration` | `LovingCell`, Test_Fluid | 60 (TRK/BP_LovingCell_SC.md:73) | s | instancia |
| Célula | Espera a Alma, entrada y salida | `IntroDelay`, `IntroTime`, `OutroTime` | LovingCell | 2 · 3 · 3 (:65, :73; MAPA:278) | s | instancia |
| Célula | Núcleo | `CentreRadius`, `GroupSize` | LovingCell | 16 · 1 (MAPA:257) | cm, × | instancia |
| Célula | Voces dentro | `VO22At`, `VO23At`, `VOWait` | LovingCell | 15 · 42 · 8 (TRK/BP_LovingCell_SC.md:73) | s | instancia |
| Gusano | Lugar | transform de `GAL_12_BlobChain` | Test_Sequencer | — (MAPA:304) | cm | actor |
| Gusano | Grosor y fusión | `BlobRadius`, `Smooth`, `OrbFuse` | GAL_12_BlobChain | 8,5 · 17,68 · 0,872 (MAPA:309) | cm | instancia |
| Esferas | Domo y anclaje | `OrbCount`, `DomeRadius`, `AnchorScale` | `GAL_12_OrbDirector` | 68 · ~976 · 0,13 (MAPA:307-308) | —, cm, × | instancia |
| Esferas | SAVE y cierre | `HoldDuration`; `FinalPasses`, `ExitTime` | GAL_12_SaveMelody; GAL_12_Sequencer | 3; 2 · 1,5 (MAPA:324, :336) | s | instancia |
| Esferas | Tempo | `StepBPM` | BP_Sequencer_SC | 90 (MAPA:340) | bpm | solo CDO |
| Paleta/tinta | Largo de la etapa | `InkMeters` | `TBDirector`, L_TBTest_SC | 30 (MAPA:375) | m | instancia |
| Paleta/tinta | Pose de la paleta | `PaletteSide/Up/Near`, `PaletteScale` | TBDirector | 0,464 (MAPA:357) | cm, × | instancia |
| Paleta/tinta | Entrada y exhibición | `IntroTime`, `ContractPaletteDelay`, `HoldTime`, `SpinSpeed` | TBDirector | 0,8 · 0,6 · 5 · 20 (MAPA:376-377) | s, °/s | instancia |
| Cuadro (final) | Lugar | transform de `Final_Cuadro` | Obra/Final | (206,45; 0; 201,97) (TRK/BP_Obra_SC.md:179) | cm | actor |
| Cuadro (final) | Cortafuegos y exploración | `ResultsTime`, `ExploreT` | BP_Obra_SC | 150 · 25 (TRK/BP_Obra_SC.md:115; MAPA:45) | s | CDO / instancia |
| Botones SHARE | Lugar | transform de `Final_BotonShare` / `Final_BotonDontShare` | Obra/Final | (206,45; ±15; 137,97) pitch 15 (TRK/BP_Obra_SC.md:180) | cm/° | actor |
| Botones SHARE | Apretar y hover | `PressDepth`, `HoverLift`, `PressTime`, `HoverInTime/OutTime` | BP_ShareButton_SC | 0,4 · 0,1 · 0,45 · 0,12/0,18 (TRK/BP_ShareButton_SC.md:49-51) | cm, s | instancia |
| Botones SHARE | Cortafuegos | `ShareFW` | BP_Obra_SC | 30 (TRK/BP_Obra_SC.md:110) | s | instancia |
| Anillo (final) | Lugar y tamaño | transform de `AnilloCarga` | Obra/Final | escala 1,9 (TRK/BP_Obra_SC.md:181) | ×46 cm | actor |
| Alma-pez | Lugar y tamaño | transform de `Final_AlmaPez` | Obra/Final | escala 2,115 (:182) | × | actor |
| Alma-pez | Nado y halo | `SwimTime`, `AwayTime`; `HaloAmt`, `HaloSize` | BP_Obra_SC; BP_SoulFish_SC | 4 · 3; 0,55 · 0,3 (:113, :118) | s; — | instancia |
| Alma-pez | Recorrido | TP `final_fish_door` → `final_fish_away` | Obra | (:184) | cm | TP |
| Créditos | Lugar y tiempos | transform de `Final_Creditos`; `CreditsTime`; `GrowTime`, `StarStep` | Obra/Credits; BP_Credits_SC | 60; 1,2 · 0,18 (:48, :239) | s | actor / instancia |
| Créditos | Estrellas | `CreditStar_00..29` | Obra/Credits | — (MAPA:89) | cm | actor |
| Alma | Tamaño | `Size` | `Obra_Alma` (persistente) | 1 (CS/Obra/alma_diff.json:95) | m (diámetro) | instancia |
| Alma | Tamaño por lugar | escala X de `TP_sc<K>_alma_in/_side`, `hall_alma_*`, `final_alma` | niveles de test / Obra | lateral 0,6, hall_side 0,5 (TRK/BP_Obra_SC.md:232, :360) | × | TP |
| Alma | Brillo | `Brightness` | Obra_Alma | 1,5 (alma_diff.json:15) | — | instancia |
| Alma | Aparece, se va, viaja | `AppearTime`, `DisappearTime`, `TravelTime` | Obra_Alma | 1,2 · 0,6 · 3 (TRK/BP_Alma_SC.md:75-76) | s | instancia (verificar) |
| Alma | Voz tras aparecer / se queda | 1,5 y VODur + 3,5 (o +3) | BP_Obra_SC `AlmaSpeak` / `StageTimes` | (DUMP:968, :977, :1468) | s | literal |
| Alma | Reacción a la voz | `VOReact`, `VOReactWobble`, `VOReactBright`, `VOReactSize` | BP_Alma_SC | 1 · 0,8 · 0,35 · 0,05 (TRK/BP_Alma_SC.md:150, :163) | — | CDO/instancia |
| Alma | Aura | `AuraAlpha`, `AuraSize`, `AuraTwinkle`, `AuraCurl`, `AuraFlow`, `AuraGlow` | BP_Alma_SC (J - Aura) | = MI (TRK/BP_Alma_SC.md:176) | — | instancia |
| Anillo de carga | Duración por etapa | `ChargeTimes[5]` | BP_Obra_SC | 4/4/4/4/6 (TRK/BP_Obra_SC.md:42) | s | instancia |
| Anillo de carga | Lugar y tamaño por etapa | `TP_sc<K>_charge` | nivel de test | 253/0/+37, escala 2,115 (MAPA:134) | × `BigScale` 46 cm (TRK/BP_ChargeTest_SC.md:23) | TP |
| Anillo de carga | Color por etapa | `StageCols` | BP_Obra_SC | (TRK/BP_Obra_SC.md:48) | lineal | instancia |
| Anillo de carga | Quietud y giro | `HoldTime` 2/9999, `SpinDeg` −450/−1440 | `ChargeStart` | (DUMP:674-675) | s, ° | literal |
| Anillo de carga | Anillo del Hall | `HallRingFit`, `HallRingSpeedIn`, `HallHomeSpeed`, `HallHomeDelay` | BP_Obra_SC | 1 · 1,5 · 2 · 0,3 (TRK/BP_Obra_SC.md:259) | ×, s | instancia |
| HUD | Escala y curva | `HudScale`, `HudCurve` | BP_SoulHUD3D_SC (Obra) | 1 · +30 en la prueba (TRK/BP_SoulHUD3D_SC.md:19-20) | ×, cm locales | instancia |
| HUD | Opacidades | `FrameOpacity`, `GlassOpacity` | ídem | 0,45 · 0,30 (:42) | — | instancia |
| HUD | Nacimiento y EEG | `BirthDelay`, `GraphRate`, `MaxSamples`, `GlowWidth` | ídem | 4 · 30 · 180 · 11 (:50, :59-60) | s, Hz | instancia/CDO |

## Lo que hay que verificar en vivo en Unreal

Todo es lectura, sin `load_level`, en el turno de la cola.

1. **Test_Hall → `HallDirector` (BP_HallDirector_SC_C_0):** `BellPressDepth`, `BellPressTime` (que no estén en 0), `BellHold`, `FW_Bell`, `FW_Tool`, `FW_Choose`, `TouchRadius`, `TileLiftCm`, `TileGlowMax`, `TileTime`, `DoorOpenDeg`, `DoorTime`, `OutTime`, `ExitTime`, y la `RelativeLocation` de `StopCard` y `StopExit`. Para `StopCard`, `CS/Hall/director_overrides.json:2` dice 300 y TRK/BP_Obra_SC.md:178 dice 396,45.
2. **Test_Hall → función `HallSensorSpin` del director y `HallSensorOrb.SpinDeg`:** confirmar si los dos giros se suman.
3. **Test_Hall → `Timbre` y `Sensor`:** `Appear.Duration`, `Appear.AppearSound`, `Appear.VanishSound` y transform. Después, `TituloInicio` (transform), `TP_hall_alma_center/side/exit` y `TP_hall_soul_present` (escala X), y `HallSoul_0..4` (transform y `Size`).
4. **Test_Entering → `Entering_Stage`:** `ExploreTime`, `CountTime` (3,6), `ToolDelay`, `InhaleCueAt`, `HelpAfter`, `SayAfterTool`, `SayGap`, `SensorColor`, `BlobInSound`.
5. **Test_Entering → `Entering_Pacer`:** `Preset` (tiene que ser 0), los 4 tiempos, `Cycles`, `LeadIn`, `LeadOut`, `SizeCm` y transform. **`Entering_Blob`:** `SizeCM`, `IntroTime`, `OutroTime`, `Brightness` y transform. Confirmar si alguno se corrige por altura de ojos.
6. **Los 5 niveles de test → `TP_sc<K>_alma_in/_alma_side/_charge/_title`:** transform y escala X. Se espera `alma_side` en 0,6.
7. **L_SoulCharger_Obra → `BP_Alma_SC_C_0`:** `Size`, `Brightness`, `AppearTime`, `DisappearTime`, `TravelTime`.
8. **L_SoulCharger_Obra → grafos de `BP_Obra_SC`:** `AlmaSpeak` (¿+3 o +3,5?), `StageTimes` (¿sigue leyendo `StAlma`?), `AlmaSclTick` (fase 9) y `AlmaResults` (¿usa `final_alma` o `ResAlmaLeft`/`ResAlmaScale`?). Además, las variables de instancia `ResAlmaLeft`, `ResAlmaScale`, `ChargeTimes`, `ShareFW`, `ExploreT`, `SwimTime`, `AwayTime`, `CreditsTime` y `ResultsTime`.
9. **L_SoulCharger_Obra → `UserTool_Obra`:** el parámetro `Active` del MID de `Waves` en PIE, con `BreathRig.bZone` en true. Esto dice si "Rings on" existe.
10. **L_SoulCharger_Obra → HUD (`BP_SoulHUD3D_SC`):** `HudScale`, `HudCurve`, `FrameOpacity`, `GlassOpacity`, `BirthDelay`. **`AnilloCarga` (BP_ChargeFx_SC_C_0):** `BigScale` y escala. Los transforms de `Final_*` y de `final_*`.
11. **Test_Heart → `HeartManager`:** `BeatDiv`, `StageBeats`, `OrbitAtBeat`, `BackupAfter`. **Test_Fluid → `LovingCell`:** `StageDuration`, `IntroDelay`. Con esto se resuelven las divergencias de MAPA.