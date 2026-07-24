# Sistema de Calibración (BP_CalibProbe + BP_CalibDirector + L_Calibration)

Nivel de captura de datos para testear muchos usuarios y tunear umbrales con evidencia. Detalle de diseño y contexto en la memoria `level-calibration-plan`. Motivación (por qué prompt-timing y no gatillo) en la memoria `calibracion-analisis-hallazgos`.

## BP_CalibProbe
- **refPath**: `/Game/SoulCharger/Calibration/BP_CalibProbe.BP_CalibProbe` · duplicado de `BP_BreathSensor_V2` (ver ese tracker para el pipeline de features/Step, intacto).
- **Cambios sobre el original**:
  - Var `RecSegment` (String) — nombre del segmento activo (lo setea `RecOn`).
  - `RecOn(Seg:String)` = `SetRecSegment(Seg)` + `SetCountingEnabled(true)`. `RecOff()` = `SetCountingEnabled(false)`. **Reusa `bCountingEnabled` como interruptor de grabación** — es el 2º término del gate de `CalibLog` `(and bCalibLog bCountingEnabled)`, así que grabar = `bCountingEnabled=true`. `CalibLog` NO se tocó (frágil por bool-getters).
  - CDO: `ContinuousInhaleTime=9999` (neutraliza el conteo → sin auto-ocultar ni háptico de respiración), `bCalibLog=true`, `bCountingEnabled=false`.
- El probe solo loguea `BRLOG,...` mientras está **agarrado** (Step corre en la rama de agarre) **Y** `bCountingEnabled=true` (ventana de record).
- **Offset del mesh por mano (2026-07-24, VALIDADO en visor):** el `Cube` (mesh del sensor) necesita un offset distinto según la mano. **Flotando** = default del `Cube` (loc 0/rot 0/**scale 0.08**). **Al agarrar** = función nueva `ApplyGripOffset` (llamada 1ª cosa en el evento `Custom|AttachTo`, cuando `bIsRightHand` ya está seteado) hace `SetRelativeLocationAndRotation(Cube, ...)` según la mano. 4 vars **instance-editable** (valores finales confirmados):
  - **Derecha** `MeshLocR`=(2.5, -1.5, -3.5) · `MeshRotR`= Roll -20 / Pitch 3 / Yaw 170 (orden editor Roll/Pitch/Yaw = struct roll/pitch/yaw).
  - **Izquierda** `MeshLocL`=(2.5, **+1.5**, -3.5) · `MeshRotL`= Roll **-20** / Pitch **-3** / Yaw **10**. 🔴 **El espejo NO fue el textbook** (negar Y en todo dio "al revés"; keep-Roll/negar-Pitch+Yaw dio el cono para el otro lado). Lo que funcionó: **keep Roll, negar Pitch, y Yaw = espejo+180°** (170 → -170 → +10). Guardar esta receta para futuros props agarrables asimétricos.
  - El attach usa `AttachActorToComponent` con `SnapToTarget` loc+rot → el actor cae exacto en el mando y el offset del `Cube` lo posiciona. Scale 0.08 fija (del default). Seteado en CDO **y** en el instance del nivel.
- ⚠️ **Gotcha 2026-07-24:** el `BP_CalibProbe` se borró del world (el usuario, sin querer) → `BeginPlay` del Director (`GetActorOfClass` + cast → `SetProbe`) devolvió None → error runtime `Accessed None ... property Probe` en CADA tick (el Tick lee `Probe` sin guarda). **No era bug de código, era el actor faltante.** Fix: recolocar `BP_CalibProbe` en `L_Calibration`. (Mejora futura opcional: guardar el Tick con un `IsValid Probe` para degradar en vez de spamear.)

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
- **`UpdateBreathing(T)`** (T=0..10) — **REORDENADO 2026-07-24 para arrancar con sostén** (el usuario pidió que empiece en sostén "para que se acomode"): **sostén-reposo 0-2s** (círculo 1.2, "SOSTEN") → inhala 2-5s (1.2→2.8, "INHALA") → sostén 5-7s (2.8, "SOSTEN") → exhala 7-10s (2.8→1.2, "EXHALA"). Además **pausa el video guía** (`Media|MediaPlayer|Pause GetMP_Gui`) al inicio de la función → como UpdateBreathing solo corre en la experiencia guiada (type1), el video de `Page7_Guided` queda **congelado durante la respiración** (jugó en instrucción+countdown, se pausa al empezar el ejercicio). Nota: el sostén-reposo es **por ciclo** (cada respiración abre con 2s de sostén), no una sola vez; si se quiere one-time settle → gate por `PhaseTimer` en el EventGraph.
- **Arranque por gatillo** = poll `(or probe.GetLabel probe.GetLabelR)`. No hay input nuevo en el Director.

### Audio/háptico
Solo 2 pulsos por ejercicio (inicio/fin, vía `PlayGrabHaptic`). **Neutralizado en el probe CDO**: `HapticAmplitude=0` (mata el háptico continuo) + `AudioUmbral.Sound=null` + `bAutoActivate=false` (mata el audio). El `GrabPulse` (los 2 pulsos) usa amplitud 1.0 independiente, sigue funcionando.

### ⏳ Pendiente (test del usuario en visor)
Posición/tamaño de CountdownNumber/CenterTitle/CircleText y del círculo/slider **a ajustar en el editor** (a ojo por ahora). Verificar el feel del trigger-hold, el ciclo de respiración, y que graba/guarda por ejercicio. Íconos por página (SetIconMaterial) siguen pendientes.

### 🧹 Limpieza de huérfanos (2026-07-24)
Barrido de vitalidad dirigida (`ProgrammaticToolset`, ver `scripts/clean_orphans.py`) tras las múltiples reescrituras del rediseño + portada. **1007 huérfanos borrados** con DSL vivo `identical=true` en los 3 grafos (cero cambio de lógica). Conteo actual de nodos vivos: **EventGraph 226 · ConfigureSegment 58 · UpdateBreathing 28**. Compila limpio, guardado.

### 🖼️ Materiales de página asignados (2026-07-24)
Las 10 vars `Icon*` (instance-editable) apuntan a Material Instances de `M_Instruct_Calib` en `Calibration/Material/`. Mapa (var → MI): IconCover/IconFinal→Page1_Alma · IconWelcome→Page2_Sensor · IconEst→Page3_Umbral · IconApnea→Page4_Sosten · IconNat→Page5_Natural · IconRapida→Page6_Rapida · IconGuiada→Page7_Guided · IconPierna→Page8_Reposo · IconMov→Page9_Movement.
- 🔴 **GOTCHA (resuelto 2026-07-24):** setear los defaults en el **CDO** NO alcanza — el actor `BP_CalibDirector_C_0` **ya colocado** en `L_Calibration` tenía los `Icon*` serializados en `None` (vars instance-editable → el instance manda). Síntoma: cuadrado blanco en el widget en vez del material. Fix: `ObjectTools.set_properties` sobre el **actor del nivel** (`...L_Calibration:PersistentLevel.BP_CalibDirector_C_0`) + guardar el nivel. Las 8 vars de video (MP_*/Src_*) se agregaron después → heredaron bien el CDO. Al re-colocar el actor o en un nivel nuevo, re-asignar en el instance.

### 📐 Slot de imagen del widget +50% (2026-07-24)
`WBP_CalibInstructions` → `Icon` (Image) → `CanvasPanelSlot_0`. Anclas de relleno (min 0,0 / max 1,1) con márgenes. Agrandado **+50%** (de ~648×649 a ~972×973), pegado a la izquierda (left=0) y centrado vertical (top=bottom≈53). `layoutData.offsets` = {left 0, top 53.31, right 947.88, bottom 53.31}. Aplica a todas las páginas (el Icon es único, visible en todos los modes).

### 🎨 Master `M_Instruct_Calib` — alpha "solo negro total" (2026-07-24)
Translucent + MD_UI. `TextureSample.RGB → Emissive`; opacity = alpha por luminancia. Estaba `max(R,B)` **lineal** (grises oscuros semi-transparentes = "borraba mucho") y con bug de canal (ignoraba G, usaba `max(R,R)`). **Fix:** (1) reconecté canal G → `max(R,G,B)` real; (2) inserté rampa empinada `Max → Multiply(× AlphaSharpness) → Opacity`. **`AlphaSharpness`** = ScalarParameter (grupo "Alpha", default **16**, tuneable por instancia) → solo el negro casi-total (< ~1/16 luminancia) va a alpha, el resto opaco, conservando antialias de bordes. Subir el valor = recorte más agresivo.

### 🎬 Videos (MediaPlayer) — reproducción on-demand (2026-07-24)
**4 de las 10 páginas son video** (MediaTexture, no imagen fija): Page5_Natural(Inhaling_MD_Video), Page6_Rapida(Rapida_MP_Video), Page7_Guided(Guided_MP_Video), Page9_Movement(Movement_MP_Video). Cada MediaTexture ← un MediaPlayer (`_MP`/`_MD`) con **playOnOpen+loop=true** pero **sin source asignado** (playlist=None) → no arrancaban solos.
- **8 vars objeto nuevas** en el Director (defaults en CDO): 4 MediaPlayer `MP_Nat/MP_Rap/MP_Gui/MP_Mov` + 4 MediaSource `Src_Nat/Src_Rap/Src_Gui/Src_Mov`. Mapa player↔source por nombre: Inhaling_MD←Inhaling-exhaling, Rapida_MP←Rapida, Guided_MP←Guided, Movement_MP←MovementHand.
- **Función `UpdateSegmentMedia`** (llamada al final de `ShowInstruction`, 1× por segmento). **REESCRITA 2026-07-24 a PRE-CARGA** para eliminar el flash de apertura: abrir el video justo cuando su página aparece mostraba 1 frame stale/frame-0 y saltaba al ponerse en play (latencia de OpenSource async). Ahora cada video se **abre ~1 ejercicio ANTES** de su página, así ya está en loop cuando aparece (sin abrir en pantalla). Por SegIndex: `1→Open Nat` · `2→Open Rap` · `3→Open Gui + Close Nat` · `4→Close Rap` · `5→Open Mov + Close Gui`. **Máx 2 decoders simultáneos** (seguro para Quest). `AutoClear=true` en las 4 MediaTextures (frame negro→transparente por el material si algún hueco). ⚠️ Los videos pre-abiertos **reproducen invisibles** durante el ejercicio previo — si tuvieran pista de audio, sonaría (chequear que sean mudos). El pause de Gui (UpdateBreathing) sigue: Gui abre en seg3, juega hasta seg4 experiencia, ahí se congela.
- ⚠️ **Nota menor:** el último video (Movimiento, seg 6) sigue en loop invisible durante la pantalla "Gracias" (esa no llama ShowInstruction); se corta solo al recargar el nivel con el trigger. Sin impacto visible.
- ✅ **PACKAGING DE VIDEO RESUELTO (2026-07-24):** los 4 `.mp4` movidos a `VR_Test/Content/Media/` (misma carpeta que los videos de Breath, ya staged). Cada `FileMediaSource` con FilePath **relativo** `./Media/<X>.mp4` (Guided/Rapida/MovementHand/Inhaling-exhaling). `DefaultGame.ini` **ya tenía** `+DirectoriesToAlwaysStageAsUFS=(Path="Media")` → no hizo falta tocar el ini. Originales borrados de `Recursos/Asset/Calibration/` (quedan solo las `.png` fuente). Empaquetar **Development**. Ver memoria `video-packaging-quest`.
