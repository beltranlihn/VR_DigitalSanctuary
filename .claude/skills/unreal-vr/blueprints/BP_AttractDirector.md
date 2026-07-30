# BP_AttractDirector — progress tracker

Cerebro del stage **Touch = "Attracting"** (etapa de música). Plan completo y organigrama de construcción: [`docs/stages/touch-attracting.md`](../../../../docs/stages/touch-attracting.md). Este tracker es el detalle vivo del BP; actualizarlo al final de cada sesión.

- **refPath**: `/Game/SoulCharger/Stages/Touch/BP_AttractDirector.BP_AttractDirector`  ·  **parent**: Actor  ·  **in level**: sí — `L_Touch` (`BP_AttractDirector_C_0` en `(0,0,50)`)
- **Purpose**: orquestador del stage — máquina de flujo (instrucciones → experiencia → guardar → cierre), **dueño del reloj Quartz y del step sequencer de 5 pasos** (avanza el playhead, dispara el clip del slot en su beat, corre el pad de fondo), cuenta bloques llenos → habilita el botón Guardar.
- **Status**: 🟡 Esqueleto del secuenciador (Fase 5) construido por TIMER y compila. Falta migrar a Quartz + audio (necesita clips) y el flujo de stage (instrucciones/guardar/cierre).

## Fase 5 (secuenciador de 5 pasos) — 2026-07-30
**Vars:** `BPM`(72), `CurrentStep`(-1 → arranca en 0), `NumSteps`(5).
**BeginPlay:** `SetTimerbyFunctionName("OnBeat", 60/BPM, Looping=true)` → playhead por timer.
**`OnBeat()`:** `CurrentStep = (CurrentStep+1) % NumSteps`; PrintString "STEP n"; `GetAllActorsOfClass(BP_SeqSlot)` → el slot con `StepIndex==CurrentStep`; si su `Occupant` es válido → PrintString "BEAT HIT (occupied)" (hook de disparo).
🔴 **Es un ESQUELETO por timer, NO Quartz.** Decisión (sin clips de audio, Quartz es intesteable y complejo a ciegas): el timer da el playhead testeable por log ya. **Migrar a Quartz cuando existan los clips** — adaptar `Core/Sequencer/BP_Sequencer`: `CreateNewClock`+`StartClock`+`SubscribetoQuantizationEvent(Beat)` (nodos ya localizados) reemplazan el timer, y en el BEAT HIT usar **`Play Quantized`** del clip del Occupant (sin jitter, ver `audio-quest.md`). El pad de fondo también por Quartz.
**Test actual (sin audio):** PIE → en el log se ve el playhead avanzando "STEP 0..4" en loop a 72 BPM; al colocar una burbuja en un slot, ese step imprime "BEAT HIT".

## Componentes (previstos)
- `QuartzClock` — se crea en runtime (Quartz Subsystem), no es un component. BPM ~72 (ajustable en un solo lugar).
- `PadAudio` (AudioComponent) — el pad de fondo en loop, enganchado al clock.
- (opción A de instrucciones) `InstrPanel` (WidgetComponent, `WidgetClass=WBP_TouchInstructions`, World space) — si se manejan las páginas desde acá en vez del driver duplicado de Breath. Ver decisión A/B en el brief §6.b.

## Variables (previstas)
- `StepIndex : int` — playhead actual 0-4 · privado.
- `NumSteps : int = 5` — pasos del secuenciador.
- `BPM : float = 72` — tempo · instance-editable (un solo lugar de ajuste).
- `Slots : array<BP_SeqSlot ref>` — los 5 slots de la mesa (en orden de step).
- `FilledCount : int` — bloques ocupados; cuando llega a 5 → habilita el botón.
- `bAllSlotsFull : bool` — gate del `BP_SaveButton`.
- `Phase : enum {Instructions, Experience, Saving, Closing}` — máquina de flujo del stage.
- `SaveButton : BP_SaveButton ref` · `Table : BP_SeqTable ref`.
- (opción A) `InstrWidget : WBP_TouchInstructions ref`, `PageIndex : int`, `bStarted : bool`.

## Grafos (previstos — aún sin construir)
- **EventBeginPlay**: cachear refs (mesa, slots, botón, pad); mostrar instrucciones (widget world-space); NO arrancar el sequencer hasta terminar instrucciones. Crear el Quartz Clock (sin start aún).
- **StartExperience()**: `Phase=Experience`; arrancar el Quartz Clock; correr el `PadAudio` en loop cuantizado; suscribir el evento de cuantización `Beat`.
- **OnQuartzBeat (Quantization Event)**: avanzar `StepIndex = (StepIndex+1) % NumSteps`; si `Slots[StepIndex]` está ocupado → `Play Quantized` su clip en boundary `Beat`; disparar `OnBeatHit` a la burbuja de ese slot (hook audioreactivo, placeholder).
- **NotifySlotFilled() / NotifySlotEmptied()**: recuenta `FilledCount`; setea `bAllSlotsFull`; propaga al `BP_SaveButton` (habilita/deshabilita).
- **SaveMelody()**: llamado por `BP_SaveButton` cuando `bAllSlotsFull`; arma `SG_Melody` con los 5 `ClipID` (en orden de step) → `SaveGameToSlot`; `Phase=Saving`; reproduce la melodía una vuelta más; luego `Phase=Closing` → fade → `OpenLevel(L_Touch)` (reinicia, cierre de prueba como los otros stages).
- **(opción A) GotoPage(idx)**: mostrar/ocultar páginas del `WBP_TouchInstructions` por índice; avanzar con el trigger vía Enhanced Input EVENTS.

## Done ✅
- **Fase 0 — setup COMPLETA** (2026-07-28):
  - `L_Touch` creado en `Maps/Tests/` (duplicado byte a byte de `L_Test_Breath` → hereda pawn VR + grab + `BP_SoulChargerGameMode`). GameMode override verificado.
  - Quitados los 2 actores específicos de Breath heredados: `BP_BreathStageManager` + `BP_IntroFade` (mismo criterio que el nivel de Calibración; el flujo de Touch lo maneja este Director).
  - `BP_AttractDirector` colocado en `L_Touch` en `(0,0,50)` (`BP_AttractDirector_C_0`).
  - `DA_SoundBank` creado (parent `PrimaryDataAsset`) con arrays `Clips: array<SoundWave>` + `Previews: array<SoundWave>`. **Vacío** — falta poblarlo cuando lleguen los one-shots placeholder (no hay SoundWaves en el proyecto todavía).
  - Todo guardado. Tracker + `_INDEX.md` actualizados.
- Rama `stage/touch` creada.

## TODO / next (organigrama del brief §4)
- **Test de Fase 0 (pendiente en visor):** abrir `L_Touch` en VR/PIE → confirmar que aparece el pawn + el piso. (No verificado en headset aún.)
- **Poblar `DA_SoundBank`** con 5-6 SoundWaves placeholder cuando existan (importarlos primero; hoy no hay audio en el proyecto).
- **Registrar `L_Touch` en Packaging → MapsToCook** (necesario para el APK; no bloquea PIE). Ver `packaging-pso.md`.
- ✅ **Fase 1** — `BP_AimBeam` cableada (line-trace aim, láser, dispatchers OnHoverBegin/End + `CurrentHovered`). En `L_Touch`. Falta test visor.
- ✅ **Fase 2** — `BP_SoundBubble` cableada (preview loop con fade 1s en hover, polling de `beam.CurrentHovered`). 3 en `L_Touch`. Falta asignar audio.
- **Fase 3** — far-grab + follow (`FInterpTo`). ← **PRÓXIMA**
- **Fase 4** — `BP_SeqTable` + 5 `BP_SeqSlot` + attach.
- **Fase 5** — **acá entra este BP en serio**: Quartz Clock + step sequencer + pad. 🔧 **REFERENCIA: `/Game/SoulCharger/Core/Sequencer/BP_Sequencer`** (la "Remix Machine" cargada por el usuario) — reusar su núcleo Quartz: `StartRemixMachine` (crea el clock a BPM), evento cuantizado `BarEvents` (QuantizationType=Bar → Beat/BeatFraction) y `Play Quantized` en boundary Beat. **Adaptar a 5 pasos secuenciales** (su versión es 8 STEP × 4 pistas por overlap; nosotros: 5 slots, 1 clip c/u, disparo por beat). NO se coloca en el nivel (decisión usuario opción B, 2026-07-29): es referencia, se construye fresco acá.
- **Fase 6** — hook audioreactivo (`OnBeatHit`, placeholder).
- **Fase 7** — swap sobre slot ocupado.
- **Fase 8** — `BP_SaveButton` + `SG_Melody` (patrón `Calibration/`).
- **Fase 9** — instrucciones + cierre end-to-end.
- **Fase 10** — pulido + Android (fix `.ini` audio, codecs, profiling en device).

## Open questions / risks
- **Decisión A/B de instrucciones** (brief §6.b): Opción A (recomendada) = manejar páginas desde este Director con `GotoPage` simple y borrar `BP_TouchInstructions`; Opción B = repuntar el driver duplicado de Breath. **Pendiente de decidir antes de la Fase 9** (o antes si se hace la parte visual primero).
- **Quartz**: disparar clips SIEMPRE con `Play Quantized` en boundary `Beat`, nunca directo desde game thread (jitter). Ver [`audio-quest.md`](../references/audio-quest.md).
- **Input**: beam/hover/trigger por Enhanced Input EVENTS (los value-getters de OpenXR dan 0 fuera de su IMC — lección del sensor de Breath). Pose *aim* ≠ *grip* ([`motion-controller-data.md`](../references/motion-controller-data.md)).
- `SG_Melody` necesita el array de 5 `int` ClipIDs agregado **en el editor** (`add_variable` por MCP no crea arrays).
- Tempo/loop propuesto ~72 BPM, 5 beats (feel 5/4) — ajustable, confirmar con sound designer.

## Session log
- 2026-07-23: creado el tracker (Fase 0). Rama `stage/touch` creada desde `main`. Nivel `L_Touch` y `DA_SoundBank` pendientes (requieren Unreal abierto). Stubs de los BPs ya existían del scaffold.
- 2026-07-28: **Fase 0 completada por MCP.** `L_Touch` (dup de `L_Test_Breath`, sin los BPs de Breath) + `BP_AttractDirector` colocado (0,0,50) + `DA_SoundBank` (PrimaryDataAsset, arrays Clips/Previews vacíos). GameMode `BP_SoulChargerGameMode` verificado. Guardado. Falta test en visor + poblar audio + MapsToCook. (El MCP se cortó y reconectó a mitad; los assets ya estaban guardados, sin pérdida.)
