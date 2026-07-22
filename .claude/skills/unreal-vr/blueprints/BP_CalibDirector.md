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
