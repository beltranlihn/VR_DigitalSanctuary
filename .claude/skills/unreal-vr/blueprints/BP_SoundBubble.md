# BP_SoundBubble — progress tracker

Burbuja sonora del stage Touch (Fase 2 del brief [`docs/stages/touch-attracting.md`](../../../../docs/stages/touch-attracting.md)). Al apuntarla con el beam suena su clip en **loop con fade-in 1s** (preview); al salir del hover, **fade-out 1s**.

- **refPath**: `/Game/SoulCharger/Stages/Touch/BP_SoundBubble.BP_SoundBubble`  ·  **parent**: Actor  ·  **in level**: **no se colocan a mano** — las spawnea `BP_AttractDirector` en `BeginPlay`, una por `TargetPoint` con tag **`BubbleSpawn`** (hoy `TP_Bubble_01..06` en `L_Touch`). Para recomponer: mover/duplicar TargetPoints, sin tocar BPs. (2026-08-03)
- **Status**: 🟢 Fases 2-4 cableadas y compilan. Preview en hover + far-grab con follow + snap a slot. Falta: asignar `PreviewSound` (no hay audio aún) + test en visor.

## Componentes (CDO)
- `DefaultSceneRoot`.
- `Mesh` (StaticMesh esfera, radio 8 = placeholder de la burbuja). Su colisión bloquea el canal Visibility → el line-trace del beam la detecta.
- `PreviewAudio` (AudioComponent) — `bAutoActivate=false`. Reproduce `PreviewSound` con fade.

## Variables
- `PreviewSound` : SoundBase — el clip de la burbuja · **instance-editable** (cada burbuja el suyo). **Vacío** hasta que haya audio (import manual, no hay tool MCP de audio).
- `BeamRef` : BP_AimBeam ref — cacheado en BeginPlay.
- `bWasHovered` : bool — para edge-detection del hover en Tick.
- **Tag del actor: `Aimable`** (en el CDO) → el beam la reconoce como apuntable.

## 🔄 Modelo PUSH (reescritura para dos manos) — 2026-08-03
Con **dos beams** (uno por mano) el modelo viejo se rompía: `BeginPlay` hacía `GetActorOfClass(BP_AimBeam)` y cacheaba **un solo** beam, así que la otra mano era invisible. Ahora **el beam avisa** en vez de que la burbuja pregunte:

- **`BeginPlay` eliminado** (ya no cachea nada) y **el polling de hover en Tick eliminado**. `EventTick` quedó en una sola línea: `if bIsGrabbed → DoFollow(DeltaSeconds)`.
- **`HoverCount : int`** + funciones **`NotifyHoverStart()`** / **`NotifyHoverEnd()`** que llama el beam. Es un **contador, no un bool**, justamente porque **las dos manos pueden estar apuntando la misma burbuja**: entra el fade-in solo cuando pasa de 0→1 y el fade-out cuando vuelve a 0 (con clamp en 0 para que un aviso de más no lo deje negativo).
- **`SetGrabbed` tiene un parámetro nuevo `Beam : BP_AimBeam`** y lo primero que hace es `SetBeamRef(Beam)`. Así **`BeamRef` dejó de significar "el único beam del mundo" y pasa a ser "el beam que me está agarrando"** — con eso `DoFollow` (que lo usa 3 veces) **quedó intacto** y sigue la mano correcta sola. `TryRelease` lo llama con `Beam` nulo, que limpia la referencia.
- `bWasHovered` **borrada** (era del edge-detection del polling).

## Grafos
- **EventBeginPlay**: `GetActorOfClass(BP_AimBeam_C)` → `CastToBP_AimBeam` → `SetBeamRef`. (Cachea el beam para leer su `CurrentHovered`.)
- **EventTick**: `beam=GetBeamRef`; `IsValid(beam)` → `now = (beam.CurrentHovered == self)`; si `now != bWasHovered` → (`now` ? `DoFadeIn` : `DoFadeOut`) + `SetWasHovered(now)`. **Polling de `CurrentHovered`** (no se ata el dispatcher entre actores; el beam expone la var pública). Edge-detected → los fades disparan una sola vez por transición.
- **DoFadeIn() / DoFadeOut()**: funciones auxiliares. `PreviewAudio.FadeIn/FadeOut(1.0s)`. 🔴 **Los nodos FadeIn/FadeOut se crearon por cirugía con `declaring_class=/Script/Engine.AudioComponent`**: el DSL resolvía el overload de `SynthComponent` (mismo nombre) y no conectaba el AudioComponent. Ver gotcha en el session log.

## TODO / next
1. **Asignar `PreviewSound`** a las burbujas (importar un .wav placeholder — p.ej. `Recursos/Audio/Heart/HeartBeat.wav` — como SoundWave y ponerlo en el campo, o setear el default en el CDO). Sin sonido, el hover funciona (láser verde) pero el preview es mudo.
2. **Test en visor:** apuntar una burbuja → suena en loop con fade-in; salir → fade-out. (El loop depende de que el SoundWave/Cue sea looping.)
3. Estética: material unlit emisivo para la esfera (Quest); reemplazar la esfera placeholder por la mini-ameba.
4. Fases siguientes: far-grab + follow (Fase 3), attach a slot (Fase 4), audioreactivo (Fase 6), swap (Fase 7). Agregar el estado `Floating/Grabbed/Placed` cuando entre el grab.

## Open questions / risks
- El preview "loop" requiere que el clip sea looping (SoundWave con bLooping o un SoundCue con Looping). Definir al proveer el audio.
- Polling en Tick por burbuja (~20 burbujas) = 20 comparaciones/frame — trivial. Si escala mucho, migrar a los dispatchers `OnHoverBegin/End` del beam.
- Espacialización en Quest: fuentes deben ser mono + ITD Panner si se quieren posicionadas (ver `audio-quest.md`) — pendiente para el pulido de audio.

## Fase 3-4 (far-grab + placement) — 2026-07-30
**Vars nuevas:** `bIsGrabbed`, `GrabSpeed`(12), `bIsPlaced`, `MySlot`(BP_SeqSlot ref), `PlaceRadius`(25).
**Tick (cirugía):** se insertó un Branch al inicio → si `bIsGrabbed` → `DoFollow(DeltaSeconds)`; si no → la lógica de hover de antes.
**`DoFollow(DeltaSeconds)`:** `target = beam.MC_RightAim.GetWorldLocation + forward * beam.GrabHoldDistance`; `SetActorLocation(VInterpTo(GetActorLocation, target, DeltaSeconds, GrabSpeed))`. Sigue la mano tipo varita.
**`SetGrabbed(NewGrabbed)`:** setea `bIsGrabbed`; si grab → `bIsPlaced=false` (permite re-colocar); si release → `TryPlace()`.
**`TryPlace()`:** `GetAllActorsOfClass(BP_SeqSlot)` → for-each → primer slot con Occupant inválido Y `Distance < PlaceRadius` → snap (`SetActorLocation` al slot), `bIsPlaced=true`, `MySlot=slot`, `slot.SetOccupant(self)`. (⚠ el `SetOccupant` cross-class es `(:Occupant valor :self target)` — el positional mapea mal.)
**Quién dispara el grab:** el `BP_AimBeam` (input grip `IA_Grab_Right`) llama `SetGrabbed`. Ver su tracker.
✅ **Occupant stale ARREGLADO (2026-08-03).** `SetGrabbed` con `NewGrabbed=true` ahora hace `IsValid(MySlot)` → libera el slot viejo (`SetOccupant(null)`) → `MySlot = null` → `bIsPlaced = false`. Antes, re-agarrar una burbuja colocada dejaba el slot marcado como ocupado para siempre: el secuenciador lo seguía disparando y ninguna otra burbuja podía entrar ahí.
**Falta todavía el SWAP (Fase 7):** soltar sobre un slot **ocupado** no intercambia — `PlaceInNearestSlot` solo mira slots libres. Necesita (a) `HomeLocation` en la burbuja (capturada al spawnear) y (b) que la función considere también los ocupados y mande la vieja de vuelta a su `HomeLocation`.

✅ **ARREGLADO 2026-08-03 — `TryPlace` fue reemplazada por `PlaceInNearestSlot`.** Ahora hace **mínimo corriente**: arranca con `BestDist = PlaceRadius` y `BestSlot = null`, recorre los slots libres quedándose con el de menor distancia, y recién al final coloca si `BestSlot` es válido. Vars nuevas `BestSlot` / `BestDist`. `SetGrabbed` llama a la función nueva; `TryPlace` fue borrada.
⚠ Se usó la receta de `gotchas.md` para rehacer un function graph sin dejar escombros: `remove_function_graph` → **`compile_blueprint`** → `add_function_graph` → `write_graph_dsl`. Un `write_graph_dsl` que falla a mitad **deja nodos sueltos**; ante un error, recrear el grafo en vez de parchear.
⚠ `Utilities|Array|Get` **no existe** como type_id: es `Utilities|Array|Get(acopy)` / `Get(aref)`. Y `SetActorLocation` necesita `:NewLocation` explícito, si no el DSL mapea el vector al pin `self`.

<details><summary>Bug original (histórico)</summary>

🔴 **BUG conocido en `TryPlace` (detectado 2026-08-03, sin arreglar):** se queda con el **PRIMER** slot que devuelve `GetAllActorsOfClass` dentro de `PlaceRadius`, **no con el más cercano**. Con los slots cada 30cm y `PlaceRadius=25` las zonas de captura se superponen, así que soltar una burbuja entre dos slots la manda al que el array liste primero, no al que apuntó el usuario — en VR se siente como que el objeto salta al lugar equivocado. **Fix:** recorrer todos los slots libres, quedarse con el de menor distancia y recién ahí comparar contra `PlaceRadius`. Con eso el espaciado de la fila deja de ser crítico.

</details>

## Audio placeholder — 2026-08-03
`PreviewSound` tiene default en el CDO: **`Stages/Touch/Audio/MS_Synth`** (MetaSound **procedural**, no depende de ningún `.wav` → suena tal cual). Así las burbujas spawneadas dejan de ser mudas sin esperar al sound designer.
**Pendiente:** que cada burbuja tome un clip distinto de `DA_SoundBank` (hoy todas comparten el default). Requiere una ref al DataAsset en `BP_AttractDirector` y usar el `Array Index` del ForEach del spawn para hacer `SetPreviewSound(Clips[i % Length])`.

## Session log
- 2026-07-29: Fase 2 construida. Componentes Mesh+PreviewAudio, vars PreviewSound/BeamRef/bWasHovered, tag "Aimable". EventGraph (BeginPlay cachea beam; Tick polling+edge-detection). Fades en funciones `DoFadeIn/DoFadeOut`. **Gotcha:** `Audio|Components|Audio|FadeIn/Out` tiene overload AudioComponent Y SynthComponent con el mismo type_id → el DSL elegía SynthComponent ("Could not connect PreviewAudio to self"). Solución: crear los nodos por `create_node` con `declaring_class=/Script/Engine.AudioComponent` en funciones aparte. Compila. 3 burbujas en `L_Touch`. `PreviewSound` vacío (falta audio). Guardado.
