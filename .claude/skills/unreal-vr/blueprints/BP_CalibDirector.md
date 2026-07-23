# Sistema de Calibración (BP_CalibProbe + BP_CalibDirector + L_Calibration)

Nivel de captura de datos para testear muchos usuarios y tunear umbrales con evidencia. Detalle de diseño y contexto en la memoria `level-calibration-plan`. Motivación (por qué prompt-timing y no gatillo) en la memoria `calibracion-analisis-hallazgos`.

## BP_CalibProbe
- **refPath**: `/Game/SoulCharger/Calibration/BP_CalibProbe.BP_CalibProbe` · duplicado de `BP_BreathSensor_V2` (ver ese tracker para el pipeline de features/Step, intacto).
- **Cambios sobre el original**:
  - Var `RecSegment` (String) — nombre del segmento activo (lo setea `RecOn`).
  - `RecOn(Seg:String)` = `SetRecSegment(Seg)` + `SetCountingEnabled(true)`. `RecOff()` = `SetCountingEnabled(false)`. **Reusa `bCountingEnabled` como interruptor de grabación** — es el 2º término del gate de `CalibLog` `(and bCalibLog bCountingEnabled)`, así que grabar = `bCountingEnabled=true`. `CalibLog` NO se tocó (frágil por bool-getters).
  - CDO: `ContinuousInhaleTime=9999` (neutraliza el conteo → sin auto-ocultar ni háptico de respiración), `bCalibLog=true`, `bCountingEnabled=false`.
- El probe solo loguea `BRLOG,...` mientras está **agarrado** (Step corre en la rama de agarre) **Y** `bCountingEnabled=true` (ventana de record).

## BP_CalibDirector
- **refPath**: `/Game/SoulCharger/Calibration/BP_CalibDirector.BP_CalibDirector` · parent Actor · colocado en el nivel.
- **Vars**: `SegIndex/Phase(0 settle,1 record)/PhaseTimer/SettleTime(2)/NumSegs(7)/CurName/CurText/CurDur/CurPacer/Probe(ref BP_CalibProbe)`.
- **`ConfigureSegment(idx)`**: switch int que setea `Cur*` por segmento (0 LAP 15s, 1 BELLY 15s, 2 THIGH 10s, 3 ARM 8s, 4 BREATHE_NAT 20s, 5 BREATHE_PACED 40s pacer=true, 6 SHAKE 8s).
- **EventGraph**:
  - *BeginPlay*: `GetActorOfClass BP_CalibProbe` → `CastToBP_CalibProbe` → `Probe`; imprime `CALIB_SESSION_START` (log); `ConfigureSegment(0)`; muestra `CurText` (PrintString pantalla).
  - *Tick*: si `SegIndex<NumSegs`: `PhaseTimer+=DT`. Phase 0 (settle) y `PhaseTimer>=SettleTime` → Phase 1, timer 0, `Probe.RecOn(CurName)`, `Probe.PlayGrabHaptic`, marcador **`CSEG,<GetGameTimeInSeconds>,<CurName>`**. Phase 1 (record) y `PhaseTimer>=CurDur` → `Probe.RecOff`, háptico, **`CSEGEND,<t>`**, `SegIndex+1`, Phase 0, timer 0, y si quedan segmentos `ConfigureSegment(nuevo)` + mostrar texto, si no `CALIB_SESSION_END`.
- El **settle de 2s (sin grabar) = banda de guarda** incorporada al protocolo (descarta la transición donde el usuario se acomoda).

## Instrucciones por widget world-space (2026-07-23)
Reemplaza el `PrintString` por un widget visible en el visor, mismo formato que los otros stages.
- **`WBP_CalibInstructions`** (`Calibration/Widget/`) — duplicado de `WBP_BreathInstructions`. Trae `SetInstruction(Text)`, `SetIconMaterial(Material)` (imagen por página) y `SetVisMode(Mode)`. Se usa **Mode 1** = solo Icono + InstructionText (oculta los sliders/círculo de Breath). Fondo del Border `BG` queda el azul de Breath (ajustable). **Íconos por página: los pone el usuario después** vía `SetIconMaterial` (hoy muestra el ícono default de Breath como placeholder).
- **`BP_CalibInstrPanel`** (actor nuevo) — host del widget: un WidgetComponent `Panel`. 🔴 **Valores COPIADOS de `BP_Instructions.Panel` (Breath) para que se vea idéntico**: `DrawSize 1920x1080`, `RelativeScale3D 0.064`, `Pivot (0.5,0.5)`, `RelativeRotation 0`, `bIsTwoSided=true`, `Space=World`. (Al principio se puso 1000x600 / 0.1 a ojo → el texto se cortaba y quedaba chico; el widget está DISEÑADO a 1920x1080.) **Se SPAWNEA en runtime** en un TargetPoint, igual que los otros stages (antes era un WidgetComponent en el Director, horneado y visible en el editor; se removió).
- **`SetVisMode(0)`** en `CacheWidgetAndWelcome` (no Mode 1) → muestra la `HintRow` (el radial), como las páginas de instrucción de Breath.
- **`TP_WidgetSpawn`** (TargetPoint en `L_Calibration`, tag **`WidgetSpawn`**, en `(200,0,120)` yaw 180) — define dónde/cómo aparece el panel. **Ajustar posición/orientación moviendo este TargetPoint en el editor.**
- **Vars nuevas del Director**: `InstrWidget` (ref WBP_CalibInstructions), `bStarted` (bool).
- **Funciones nuevas**: `CacheWidgetAndWelcome()` (**`GetAllActorswithTag("WidgetSpawn")`[0]** → `SpawnActorfromClass BP_CalibInstrPanel` en su transform → `host.Panel.GetUserWidgetObject`+cast → `SetVisMode(1)` + muestra bienvenida) · `ShowInstruction()` (`InstrWidget.SetInstruction(CurText)`; el String→Text autoconvierte).
- **Flujo nuevo (EventGraph reescrito)**: BeginPlay → `CacheWidgetAndWelcome` (muestra bienvenida) + busca probe/uidx/header, **NO arranca**. Tick: si `!bStarted` → poll `(or probe.GetLabel probe.GetLabelR)` (gatillo) → `bStarted=true`, `ConfigureSegment(0)`, `ShowInstruction`. Si `bStarted` → la máquina settle/record de siempre, y en cada cambio de segmento llama `ShowInstruction`; al terminar → `ConfigureSegment(NumSegs)` (Default = texto "Listo!") + `ShowInstruction` + `SaveSession`. **Arranque por gatillo reusando `probe.GetLabel` (no se cableó input nuevo en el Director).**
- **Textos definitivos** (sin tildes por encoding): bienvenida + 7 ejercicios (Reposo/estómago/muslo/brazo/respira normal/respiración guiada/movimiento) + cierre "Listo! Datos guardados. Gracias." — están en `ConfigureSegment` (7) y `CacheWidgetAndWelcome` (bienvenida).

## L_Calibration (`Maps/Tests/`)
Duplicado de `L_Test_Breath` (reusa pawn VR + gamemode + grab). Quitados `BP_BreathStageManager` + `BP_IntroFade`. Agregados `BP_CalibDirector` (0,0,50) y `BP_CalibProbe` (50,0,100). En `MapsToCook`.

## Persistencia — SaveGame (base de datos que se expande)
Clases `SG_CalibSession` (`Data:String`, `UserIndex:int`) + `SG_CalibIndex` (`Count:int`). Funciones del Director: `NextUserIndex()` (carga `CalibIndex`, +1), `AppendRow()` (arma fila CSV desde getters del probe + geometría, la suma a `SessionData`; se llama cada tick en fase record), `SaveSession()` (guarda slot `CalibUser_<N>` + actualiza `CalibIndex`). **Un `.sav` por usuario, no se reescribe, persiste tras apagar.**
- Config: `bUseExternalFilesDir=True` en `DefaultEngine.ini` → `.sav` en `/sdcard/Android/data/<pkg>/files/SaveGames/` (USB, sin permisos). Empaquetar **Development**.
- Recuperar: sacar carpeta `SaveGames/` por USB; parsear cada `.sav` (el `Data` FString con el CSV se extrae con Python). Header `CCOLS,...` en 1ª línea. Fila = `CROW,t,seg,ls,as,amp,bv,sv,fv,re,df,in,br,cal,dist,horiz,vdrop,caldist`.
- El probe además loguea `BRLOG` al engine log (gate `bCalibLog`) — redundante, útil para debug en PIE; poner `bCalibLog=false` para el build final si molesta.

## Pendientes (v1 → v2)
- ⏳ **Test en visor** (verificar grab + marcadores + BRLOG). Instrucciones v1 = PrintString (solo Link/PIE; NO en build VR → falta TextRender 3D o `WBP_CalibInstructions`).
- ⏳ `BP_CalibPacer` (esfera 4s/4s) + wiring de `CurPacer` para el segmento 5.
- ⏳ Íconos (los crea el usuario al final). Al terminar captura: `bCalibLog=false`.

## 🔄 REDISEÑO 2026-07-23 (flujo del PDF de UI) — SUPERA todo lo anterior de este archivo
El usuario entregó un PDF con la UI. El flujo cambió por completo. **5 ejercicios**, cada uno con 3 pantallas.

### Widget `WBP_CalibInstructions` (extendido)
- Elementos nuevos (TextBlocks, variables): **CountdownNumber** (el 3-2-1), **CenterTitle** (título centrado), **CircleText** (INHALA/SOSTEN/EXHALA). Posición/tamaño fino los ajusta el usuario en el editor.
- Funciones nuevas: **`SetScreen(Mode)`** (colapsa todo + switch: `0`=instrucción[Icon+InstructionText+HintRow], `1`=countdown[CenterTitle+CountdownNumber], `2`=experiencia[CenterTitle+CalSlider], `3`=respiración[ReactiveCircle+CircleText+CalSlider]) · `SetCountdown(N:Text)` · `SetCenterTitle(T:Text)` · `SetCircleText(T:Text)`. Reusa las de Breath: `SetInstruction/SetCalProgress(slider)/SetTriggerProgress(radial)/SetCircleSize(RenderScale)`.

### Director `BP_CalibDirector` — máquina de estados (switch en `Phase`)
Vars nuevas: `Phase(0=WELCOME,1=INSTRUCTION,2=COUNTDOWN,3=EXPERIENCE,4=FINAL)` · `HoldTimer/HoldDur(1.0)` (trigger sostenido) · `CountDur(3.0)` · `CurTitle/CurType(0 normal,1 respiración)` · `bRightHand` · `BreathCycleTimer`.
- **`ConfigureSegment(idx)`**: 5 ejercicios (EST 20s, PIERNA 15s, NAT 20s, GUIADA 40s type1, MOV 10s) → setea CurName/CurTitle/CurText/CurDur/CurType. Default = pantalla "Gracias" (Alma Digital).
- **Tick (switch Phase):**
  - `0 WELCOME`: si (probe agarrado Y trigger) → llena radial; al completar `HoldDur` → captura `bRightHand=probe.GetIsRightHand`, Phase=1, ConfigureSegment(0), ShowInstruction.
  - `1 INSTRUCTION`: trigger sostenido llena el radial; al completar → Phase=2, SetScreen(1)+SetCenterTitle. (texto = `CurText`)
  - `2 COUNTDOWN`: PhaseTimer sube; SetCountdown "3"/"2"/"1" por umbral; a los `CountDur`s → Phase=3, `RecOn`, **`PlayGrabHaptic` (pulso inicio)**, SetScreen(2 o 3 si type1).
  - `3 EXPERIENCE`: PhaseTimer sube; `AppendRow`; SetCalProgress(et/CurDur); si type1 → BreathCycleTimer (wrap 10s) + `UpdateBreathing`; al llegar a CurDur → `RecOff`, **`PlayGrabHaptic` (pulso fin)**, SegIndex++; si quedan → Phase=1+ShowInstruction, si no → `SaveSession`+Phase=4+pantalla Gracias.
  - `4 FINAL`: trigger sostenido → `OpenLevel("L_Calibration")` (reinicia para el próximo usuario).
- **`UpdateBreathing(T)`** (T=0..10): inhala 0-4s (círculo 0.6→1.4, "INHALA"), sostén 4-6s (1.4, "SOSTEN"), exhala 6-10s (1.4→0.6, "EXHALA") vía `SetCircleSize`+`SetCircleText`.
- **Arranque por gatillo** = poll `(or probe.GetLabel probe.GetLabelR)`. No hay input nuevo en el Director.

### Audio/háptico
Solo 2 pulsos por ejercicio (inicio/fin, vía `PlayGrabHaptic`). **Neutralizado en el probe CDO**: `HapticAmplitude=0` (mata el háptico continuo) + `AudioUmbral.Sound=null` + `bAutoActivate=false` (mata el audio). El `GrabPulse` (los 2 pulsos) usa amplitud 1.0 independiente, sigue funcionando.

### ⏳ Pendiente (test del usuario en visor)
Posición/tamaño de CountdownNumber/CenterTitle/CircleText y del círculo/slider **a ajustar en el editor** (a ojo por ahora). Verificar el feel del trigger-hold, el ciclo de respiración, y que graba/guarda por ejercicio. Íconos por página (SetIconMaterial) siguen pendientes.
