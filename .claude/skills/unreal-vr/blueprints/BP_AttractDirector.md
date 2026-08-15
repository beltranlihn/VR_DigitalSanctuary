# BP_AttractDirector — progress tracker

Cerebro del stage **Touch = "Attracting"** (etapa de música). Plan completo y organigrama de construcción: [`docs/stages/touch-attracting.md`](../../../../docs/stages/touch-attracting.md). Este tracker es el detalle vivo del BP; actualizarlo al final de cada sesión.

- **refPath**: `/Game/SoulCharger/Stages/Touch/BP_AttractDirector.BP_AttractDirector`  ·  **parent**: Actor  ·  **in level**: sí — `L_Touch` (`BP_AttractDirector_C_0` en `(0,0,50)`)
- **Purpose**: orquestador del stage — máquina de flujo (instrucciones → experiencia → guardar → cierre), **dueño del reloj Quartz y del step sequencer de 5 pasos** (avanza el playhead, dispara el clip del slot en su beat, corre el pad de fondo), cuenta bloques llenos → habilita el botón Guardar.
- **Status**: 🟡 Esqueleto del secuenciador (Fase 5) por TIMER + spawn de burbujas por TargetPoint. Compila. Falta migrar a Quartz + audio (necesita clips) y el flujo de stage (instrucciones/guardar/cierre).

## Spawn de burbujas por TargetPoint — 2026-08-03
Las burbujas **ya no se colocan a mano en el nivel**: el Director las spawnea en `BeginPlay`, una por cada `TargetPoint` con el tag **`BubbleSpawn`**. Así la composición se arma moviendo/duplicando TargetPoints en el viewport, sin tocar Blueprints, y la cantidad es data-driven (escala a las ~20 del brief).

**También registra el input del stage:** `BeginPlay` arranca con `AddMappingContext(IMC_Touch, priority=1)` vía `GetEnhancedInputLocalPlayerSubsystem(GetPlayerController(0))`. Prioridad 1 para ganarle a `IMC_Default` el gatillo. Sin esto los `IA_Attract_*` del beam no disparan.

**BeginPlay (cirugía de nodos, no reescritura):**
`GetAllActorsOfClassWithTag(TargetPoint, "BubbleSpawn")` → `ForEachLoop` → `SpawnActorFromClass(BP_SoundBubble, GetActorTransform(elemento), AlwaysSpawn)` → al `Completed` sigue el `SetTimerbyFunctionName("OnBeat")` de antes.
- `CollisionHandlingOverride` puesto explícito en **`AlwaysSpawn`** (con `Undefined` una burbuja podía no spawnear por colisión).
- En `L_Touch` hay 6 puntos: `TP_Bubble_01..06`. Las 3 burbujas colocadas a mano fueron **borradas** del nivel.
- Las burbujas spawneadas nacen sin `PreviewSound` (el CDO está vacío) → mudas hasta que se pueble `DA_SoundBank` y se asigne el clip en el spawn.
- Se borraron del EventGraph un `EventTick` y un `ActorBeginOverlap` **vacíos** (el Tick vacío hacía tickear el actor al pedo).

## ✅ Quartz RESUELTO — 2026-08-03 (el playhead ya no es timer)
`BeginPlay`: `GetQuartzSubsystem` → `CreateNewClock("TouchClock")` → `SetClock` → `SetBeatsPerMinute(BPM)` → `SubscribeToQuantizationEvent(Beat, <custom event>)` → `StartClock`. El custom event llama `OnBeat`, que ya tenía la lógica de step. **`SetTimerbyFunctionName` eliminado** → se acabó el drift contra el reloj de audio.
⚠ **`CreateNewClock` NO compila sin el `QuartzSubsystem` conectado a su pin Target.**
🔴 **El único paso que el MCP no puede hacer:** crear el custom event con la firma del metrónomo (`add_event` no crea parámetros tipados). Lo hace el usuario en 10 segundos: nodo `Subscribe to Quantization Event` → click derecho en el pin rojo `On Quantization Event` → **"Add Custom Event…"**. Después el resto se cablea por MCP.

<details><summary>Historial del bloqueo (resuelto)</summary>

## 🔴 Quartz: BLOQUEADO por una limitación del MCP — 2026-08-03
La migración del playhead a Quartz **no se pudo completar por MCP**. El bloqueo es concreto y conviene no volver a chocarlo:

**`QuartzClock|SubscribetoQuantizationEvent` pide un pin `OnQuantizationEvent` de tipo `Delegate (by ref)`.** Para llenarlo hace falta un **custom event con la firma exacta del metrónomo de Quartz** (`ClockName:Name`, `QuantizationType:enum`, `NumBars:int`, `Beat:int`, `BeatFraction:float`). `BlueprintTools.add_event` **crea custom events pero NO parámetros tipados**, y `list_compatible_event_functions` sobre un `EventDispatchers|CreateEvent` conectado a ese pin devuelve **`[]`** (no hay ningún evento con esa firma para bindear). Mismo problema en `NotifyonQuantizationBoundary`: toda la API de eventos de Quartz es delegate-based.

**Paso manual que lo desbloquea (10 segundos en el editor):** poner el nodo `Subscribe to Quantization Event`, **click derecho en el pin rojo `On Quantization Event` → "Add Custom Event…"** — Unreal genera el evento con la firma correcta sola. A partir de ahí el resto sí se cablea por MCP.

**No se dejó nada a medias:** el playhead sigue por **timer** y el BP compila. No conviene crear el clock hasta poder suscribirse, porque un clock que no dispara nada agrega complejidad sin beneficio.

**Cuando se retome, el plan es:** `CreateNewClock` (BPM desde la var `BPM`) → `SubscribetoQuantizationEvent(Beat, <el custom event>)` → `StartClock`.
⚠ **Por qué el timer no alcanza como sustituto:** el timer y el clock corren por separado y **driftean**; a 72 BPM en 15 min son ~1080 beats, y unos pocos por ciento de deriva ya se oyen como un golpe doble o un beat vacío.

</details>

## Pendiente de audio (mejora, no bug)
Hoy el clip lo dispara la burbuja con un `Play()` común desde `PulseOnBeat`. Lo **ideal** es **`Audio|Components|Audio|PlayQuantized`** en boundary `Beat`, que elimina el jitter de frame (ver `audio-quest.md`). Vive en el **AudioComponent**, así que hay que pasarle el `ClockHandle` a la burbuja. Con el playhead ya en Quartz, la diferencia es fina; con clips percusivos reales puede notarse.

## Slots cacheados + `Core/Sequencer` sacado de Core — 2026-08-03
**`Slots : array<BP_SeqSlot>`** + función **`CacheSlots()`** (llamada en `BeginPlay` justo después del `AddMappingContext`): recorre `GetAllActorsOfClass` **una sola vez** y hace `SetArrayElem(Index = slot.StepIndex, bSizeToFit = true)` → el array queda **indexado por StepIndex**, no por orden de descubrimiento.
**`OnBeat` reescrito**: se fue el `GetAllActorsOfClass` **por beat** y el loop de búsqueda. Ahora es `IsValidIndex(Slots, step)` → `Slots[step]` → chequear `Occupant`. Acceso directo O(1). El array sigue sirviendo igual cuando se migre a Quartz.
⚠ `OnBeat` se puede borrar y recrear sin miedo: el timer lo referencia **por string** (`SetTimerbyFunctionName "OnBeat"`), no por nodo.

**`Core/Sequencer/` desarmado** (violaba §7 del CLAUDE.md: `Core/` es compartido y eran assets migrados de terceros). Nada del stage lo referenciaba. Quedó:
- `Stages/Touch/Audio/` → **`MS_Synth`** y **`MS_Perc`**, los 2 MetaSounds **procedurales** (sin dependencias externas) → **usables como placeholders ya**. Cargados en `DA_SoundBank.Clips`.
- `Stages/Touch/Ref/` → `BP_Sequencer`, `MS_Kick`, `MS_HiHats`, `M_ON`, `M_OFF`. **Solo referencia.** 🔴 Siguen con **4 referencias rotas** (`SM_Button`, `P_Destruction_Electric`, `A_drumz_kick_dirty`, `RAW_DDT_HAT_02`) → **riesgo de que el cook falle**. Recomendación: borrarlos (nadie los usa) o proveer los samples faltantes.

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
- 2026-08-03: **traspaso del stage a Beltrán** (rama `stage/touch` actualizada con `main`). 🔴 **Hallazgo grave al abrir `L_Touch`: TODOS los actores de gameplay estaban en (0,0,0)** — beam, 3 burbujas, 5 slots y el Director apilados en el origen. Los trackers documentaban posiciones (burbujas "~120cm al frente", slots "X=55, Z=75", cubo de test "(150,0,120)") que **no estaban en el `.umap` guardado**; el cubo apareció en (0,0,120), o sea perdió la X. Conclusión: las Fases 1-4 nunca fueron testeables, y no por el código sino porque la escena no estaba armada. **Lección: verificar la posición real de los actores con `get_actor_transform` antes de dar una fase por lista** — que compile no dice nada de la escena, y el tracker puede describir una escena que no existe. Arreglado: slots en fila (X=55, Z=75, Y −60/−30/0/+30/+60, `StepIndex` 0-4 verificados y coincidentes con el orden espacial), burbujas migradas a spawn por TargetPoint.
- 2026-07-28: **Fase 0 completada por MCP.** `L_Touch` (dup de `L_Test_Breath`, sin los BPs de Breath) + `BP_AttractDirector` colocado (0,0,50) + `DA_SoundBank` (PrimaryDataAsset, arrays Clips/Previews vacíos). GameMode `BP_SoulChargerGameMode` verificado. Guardado. Falta test en visor + poblar audio + MapsToCook. (El MCP se cortó y reconectó a mitad; los assets ya estaban guardados, sin pérdida.)

## 🆕 Secuenciador de 8 pasos a 90 BPM (2026-08-15)
Cambio pedido por Beltrán. Tres piezas:

**1. El reloj.** `BPM` 72 → **90** y `NumSteps` 5 → **8** en el CDO. Verificado en PIE: **`STEP 7` vuelve cada 5,333 s**, que es exactamente 8 × (60/90). El Quartz ya estaba bien armado; sólo cambiaron los números.

**2. Los slots.** La fila pasó de 5 a 8, **simétrica y con el mismo espaciado de 30 cm** que ya usabas: `Y = −105, −75, −45, −15, +15, +45, +75, +105` en `X=4855, Z=75`. Se movieron los 5 existentes y se crearon `TP_Slot5/6/7` con tags `SlotSpawn5/6/7`. `BP_Stage_Attracting.SpawnSlots` ahora spawnea los ocho. Log: `TCH|Dir slots=8 bubbles=20 beams=2`.
💡 El ancho total quedó en **2,1 m**, que sería inalcanzable para una obra sentada — pero **las burbujas se agarran con el beam, no con la mano**, así que la fila puede ser ancha. El espaciado de 30 cm se mantuvo a propósito: `BP_SoundBubble.PlaceRadius` es 25 cm, y apretar más la fila haría que una burbuja caiga en el slot vecino.

**3. Guardar con UN solo slot.** Antes `RefreshAvailable` exigía **todos** los slots ocupados (arrancaba en `true` y apagaba al primer hueco). Ahora arranca en `false` y **el primer ocupante lo enciende**: el usuario puede quedarse con su melodía sin llenar los ocho.

### 🔴 Cómo se hizo el punto 3, porque no se podía escribir
`bAvailable` tiene prefijo `b`, y **su setter no se puede escribir por DSL desde su propia clase** (gotcha §62) — o sea `RefreshAvailable` era **irreescribible**. Pero los dos nodos `SetbAvailable` **ya existían en el grafo**, así que la inversión se hizo por **cirugía**, sin crear ni borrar nada:
1. el `true` del arranque → `false` (un `set_pin_value`),
2. el `false` del loop → `true` (otro `set_pin_value`),
3. y ese nodo se colgó del pin **Is Valid** en vez de **Is Not Valid** (un `connect_pins`).
💡 **La lección general:** cuando una función no se puede reescribir, mirar si los nodos que hacen falta **ya están ahí**. Invertir una condición suele ser mover un cable y cambiar dos constantes, no reconstruir la función.

### ⚠ Dos cosas vistas de paso
- Los tres anchors nuevos **cayeron primero en `L_Room_Surrounding`** (era el nivel activo del editor) y hubo que rehacerlos: se borraron, se abrió `L_Room_Attracting` como mapa, se crearon ahí y se volvió al persistente. 🔴 **Un actor nuevo va al nivel ACTIVO, no al que uno tiene en la cabeza** — y en una sala equivocada el `GetAllActorsOfClassWithTag` no lo encuentra, porque esa sala no está cargada durante la etapa.
- `BP_AimBeam` escupe **una línea de debug por segundo por mano** (`TCH|B L fx=...`). Es ruido de desarrollo que conviene apagar antes del APK.

## 🆕 El Módulo 1 suena (2026-08-15)
Beltrán subió `Core/Audio/AttractingSounds/Module1/`: un **pad de base** y los clips de las burbujas.

- **El pad** entra como voz en loop **`LAttractPad`** del [[BP_AudioHub]], con **3 s de fade** — arranca en `LogInit` (`PadOn`) y se apaga en el `CleanupAttract` de la etapa (`PadOff`). Es lo que reemplaza al ambiente: esta sala ya no lleva Ambient Clip, manda la música.
- **Los clips de burbuja** viven en **`ModuleSounds`** (array instance-editable del director). `AssignBubbleSounds` recorre las burbujas recién spawneadas y a cada una le pasa **su clip y su id** (`BP_SoundBubble.SetClip`), que escribe el `Sound` del `BeatAudio` que la burbuja ya tenía, el `PreviewSound` del hover, y guarda el **`ClipId`**.
- Log de la corrida: `TCH|Dir slots=8 clips repartidos=20`. Cero `Accessed None`.

🔴 **Con esto se cierra la deuda de la melodía.** `BP_Finale.MelodyFromSlots` anotaba el **`StepIndex`** — la posición en la secuencia, no el sonido — y por eso **todas las melodías guardadas salían iguales**. Ahora anota el **`ClipId` del ocupante**, y `-1` para el slot vacío, que es una melodía de verdad: qué sonido hay en cada paso. El explorador de la constelación ([[BP_ConstExplorer]]) ya reproduce ese string sin cambios.

⚠ **Falta `M1S10`.** La carpeta trae 19 clips (1-9 y 11-20) y hay **20 `BubbleSpawn`**, así que una burbuja queda muda — `AssignOneBubble` la saltea sin romper nada. Cuando aparezca el archivo, se agrega al array y listo.

⚠ **`CleanupAttract` se reescribió con bucles.** Tenía 12 `KillOneBubble` y unos cuantos `KillOneSlot` **escritos a mano**, y con 20 burbujas y 8 slots ya no alcanzaban: quedaban residuos. Ahora son `KillAllBubbles` / `KillAllSlots`, que recorren todo. **Es la clase de bug que aparece cuando cambian las cantidades y nadie revisa el barrido.**

### El debug del beam, apagado
`BP_AimBeam.LogBeamPose` escribía **una línea por segundo y por mano**. Se le borró el `PrintString` (y a `LogInit`); las funciones quedan vacías para no romper a sus llamadores.
💡 De paso: ese log leía **`Beam_Start`** con guión bajo, y los parámetros reales del sistema son **`User.BeamStart` / `User.BeamEnd`** (confirmado con `GetUserVariables` sobre `NS_TouchBeam`). O sea el `okS=false` que mostraba **era del log, no del beam**. La escritura de `UpdateBeamPoints` con el nombre pelado sigue siendo la correcta.
