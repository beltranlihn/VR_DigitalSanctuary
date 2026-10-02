# Datos de referencia de los fantasmas v2 (2026-10-01)

Juntados SIN el editor, leyendo trackers, docs y scripts guardados. Cada valor viene de una fuente.
Lo marcado ⚠ es aproximado o viejo. El turno lo confirma o lo lee en vivo.

Atajos de ruta: `BP/` = `.claude/skills/unreal-vr/blueprints/`; `SC/` = `VR_Test/Saved/ClaudeScripts/`.

## Ojos y Hall
- **Ojos** = piso del pawn + 120. En juego se corrige con `z += EyeLoc.z − (pawn.z + 120)` (`SC/obra/step2.json`, `BP/BP_AuthorMark_SC.md:7`).
- **Pawn del Hall** `TP_hall_pawn`: (−980, 0, 76,97), yaw 0.
- **Timbre** `Timbre` (`BP_BellArt_SC`, tag `hall_bell`):
  - (−932, 0, 168,97), pitch **+59,7**, con la cara +Z hacia los ojos. Queda **48 al frente y 28 bajo los ojos**.
  - Mallas en `Hall/`: `SM_Bell_Base_SC`, `_Button_SC`, `_Slider_SC` y `_Trace_SC`, todas con el origen en el centro.
- **Sensor** `Sensor` (`BP_BioSensorArt_SC`, tag `hall_sensor`):
  - (−252, 0, 168,97), pitch **−59,7**, con la cara −Z hacia los ojos. Mismo 48/28, desde StopInside (−300).
  - Mientras está vivo gira en yaw del mundo a 20 °/s (`BP_SensorOrb_SC`).
- **Almas** `HallSoul_0..4` (`BP_ProtoSoul_SC`, `Size` 0,15, unos 15 cm). ⚠ Posiciones según la fórmula vieja de `HallPickStart`:
  - Fwd = 54 − 3|k|, Side = 19k, Down = 28, con k = 0, ±1, ±2.
  - Malla `/Game/SoulCharger/Core/Alma/SM_AlmaSphere` (r 50).
- **Ganchos de detección** (`SC/Hall/dsl/`):
  - Timbre vivo: paso 6, `bBellLive`. Se empieza a apretar cuando sube `BellPress` (mano a menos de 14 cm). Se completa con `BellCharge ≥ 1` (3 s).
  - Sensor vivo: paso 12. Se toma con `HallGrab`.
  - Almas vivas: paso 14. La elección se resuelve en `HallTickPick`.

## Mallas que sostiene la mano (relativas al GRIP)
- **Mando**: `SM_QuestCtrl_Body/Trigger_R/L_SC`.
  - R: (5,686, 0,540, −1,678), P −13,566, Y −83,539, R 64,231, escala 1,0875.
  - L: (5,877, −1,567, −2,050), (0, −95, 65).
  - Bisagra R: (1,565, 2,432, −0,145), eje (0,976, −0,2177, −0,0083), 14°, `PressSign` −1 (`BP/BP_TBStroke.md:603`, `BP/BP_QuestCtrl_SC.md`).
- **Mano**: `HandRight`/`HandLeft` del pawn (hijos de los Grips).
  - Malla `SKM_MannyXR_*`, `ABP_MannequinsXR`, material `MI_Hand_SC`.
  - R loc (−2,98, 3,5, 4,56). La rotación figura como "(25 · 0 · 90)", sin orden de ejes: **el turno la copia del CDO del pawn**.
- **Sensor**: `SensorXfR` (4,325, −1,685, −2,335), Roll +90. L (4,325, +1,685, −2,335), Roll −90 (`BP/BP_UserTool_SC.md:21`).
  - Mallas en `Shared/BioSensor/`: `SM_BioSensor_SC` (cuerpo), `_Button_SC`, `_Waves_SC` y `_Trace_SC`.
- **SAVE**: `BtnOffset` (5,57, 0,8, −2,08), rot (P0, Y−90, R55), escala **0,4**, en el grip **NO dominante** (`BP/BP_SeqRig_SC.md:84`).
  - Mallas en `Mechanics/Sequencer/`: `SM_SaveMelody_Base_SC`, `_Plate_SC`, `_Slider_SC` y `_Trace_SC` (150×60 mm).
- **Paleta**: ⚠ es el `ArtAnchor` por defecto de `BP_TBPalette`: (2,19, 2,76, 7,51), rot (0, 146,12, −37,31). La escala viva es 0,464.
  - La pose viva la arma `PlaceArt` con perillas del director que no están escritas en ningún lado.
  - Mallas en `Mechanics/Draw/`. Todas tienen el origen en el centro de la paleta y solo cambia el yaw:
    - `Base` y `Swatch`.
    - `Key` en −60/−20/20/60 (colores) y en −120/−160/−200/−240 (pinceles).
    - `SideKey` en −32,72 y +4,72, escala 1,4.
    - `Slider`.
    - `Knob` en (−5,48, 21,02, −1,705), escala 0,863.
- **Punta del pincel**: `SM_Tip` es hijo del **RightAim** (no del grip) en (2,5, 0, 0) (`BP/BP_TBStroke.md:1006`). Por eso v2 guarda la posición del AIM: stride 34.
  - La paleta se elige **solo por cercanía de la punta**, sin gatillo. El gatillo solo dibuja.

## Attracting
- **Esferas** (`BP_SoundOrb_SC`):
  - `GrabHoldDist` 80 y `GrabSpeed` 3; el `OrbDirector` lo pisa con **1,5**.
  - 68 esferas en un domo de unos 976 cm. Ya no hay esfera de introducción.
- **Slots** del gusano: ⚠ arco de radio 70 con centro 30 cm al frente, ±63° cada 18°. Los centrales quedan a 1 m, a z 80 del piso. El dato es del 09-23.
- **Ganchos**:
  - "Esfera puesta": `BP_SoundOrb_SC.PlaceInSlot` llama a `BP_Sequencer_SC.NotifyPlaced`.
  - SAVE: se sostiene 3 s.

## Breath, Heart y Draw (ganchos para apagar el fantasma)
- **Breath**: sube `BP_BreathRig_SC.bBreathing` (log "BREATH: UMBRAL IN"). El rig solo está activo después de `StageBegin`.
- **Heart**: sube `bHeartZone` (log "HEART: UMBRAL IN"). ⚠ `BeatBackup` fuerza la zona a los 8 s.
- **Draw**: no hay evento de primer trazo. Lo más cercano es `BeginStroke`, `bDrawing` o `InkUsed > 0`.

## Sonidos del grabador
- `/Game/SoulCharger/Mechanics/Draw/Sound/`:
  - Tic de la cuenta: `VR_click1`.
  - "Ya": `VR_shep_scale_up_02`.
  - Fin: `VR_shep_scale_down_02`.
  - OK: `VR_click2`.
