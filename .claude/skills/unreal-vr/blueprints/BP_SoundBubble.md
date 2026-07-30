# BP_SoundBubble — progress tracker

Burbuja sonora del stage Touch (Fase 2 del brief [`docs/stages/touch-attracting.md`](../../../../docs/stages/touch-attracting.md)). Al apuntarla con el beam suena su clip en **loop con fade-in 1s** (preview); al salir del hover, **fade-out 1s**.

- **refPath**: `/Game/SoulCharger/Stages/Touch/BP_SoundBubble.BP_SoundBubble`  ·  **parent**: Actor  ·  **in level**: sí — 3 en `L_Touch` (`SoundBubble_A/B/C`, ~120cm al frente).
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
**Pendiente (Fase 7):** al re-agarrar una burbuja colocada, no se libera el `Occupant` del slot viejo (queda stale) → agregar `ClearOccupant` en el grab.

## Session log
- 2026-07-29: Fase 2 construida. Componentes Mesh+PreviewAudio, vars PreviewSound/BeamRef/bWasHovered, tag "Aimable". EventGraph (BeginPlay cachea beam; Tick polling+edge-detection). Fades en funciones `DoFadeIn/DoFadeOut`. **Gotcha:** `Audio|Components|Audio|FadeIn/Out` tiene overload AudioComponent Y SynthComponent con el mismo type_id → el DSL elegía SynthComponent ("Could not connect PreviewAudio to self"). Solución: crear los nodos por `create_node` con `declaring_class=/Script/Engine.AudioComponent` en funciones aparte. Compila. 3 burbujas en `L_Touch`. `PreviewSound` vacío (falta audio). Guardado.
