# BP_ConstExplorer — apuntar una ameba de la constelación y escuchar su melodía (Core/Flow/)

## Purpose
El último beat interactivo del guión: *"VO 29 · **beams para explorar**: hover sobre una ameba = suena SU melodía"*. Después de que la ameba propia viaja a la constelación, el usuario puede recorrer las amebas de **usuarios anteriores** y escuchar la firma sonora que cada uno dejó.

## Status
🟢 **Verificado por log de punta a punta** (2026-08-15): con una ameba sembrada en el archivo, el explorador la encontró, resolvió su índice y sacó su melodía —
```
EXPLORAR: apunta una ameba de la constelacion para escuchar su melodia
EXPLORAR: ameba 0 | melodia = 1,2,3
AUDIO: melodia con notas = 3
AUDIO: id de clip fuera de rango = 2      ← el banco sólo tiene 2 clips: el secuenciador SÍ recorrió las 3 notas
```
Cero `Accessed None`. ⬜ Falta visor (apuntar con la mano de verdad) y ⬜ que el banco de clips tenga las notas reales.

## 🔴 Por qué NO usa `BP_AimBeam` para seleccionar
El protocolo manda reusar, y `BP_AimBeam` **está probado en visor**. Pero selecciona por **line trace**, y eso exige que el objetivo **tenga colisión**: `BP_ProtoSoul` no la tiene, y dársela para esto arriesga romper el agarre final y el dibujo de Surrounding.

👉 La selección va **por ÁNGULO**, que además es lo natural para apuntar cosas lejanas (son estrellas, no botones): se compara el producto punto entre la dirección de la mano y la dirección a cada ameba, y gana la más centrada dentro de `MaxAngleDeg`. **Sin colisión, sin trace, sin tocar `BP_ProtoSoul`.**
💡 Efecto secundario muy útil: **cae a la CÁMARA cuando no hay mando** (`PickAim`), y por eso esto se puede verificar en PIE sin visor — que es exactamente lo que faltaba en todo lo demás del final.
⬜ El **láser visible** todavía no está: hoy la selección es correcta pero invisible. Cuando se pruebe en visor se decide si alcanza con un `NS_TouchBeam` puramente visual o si conviene darle colisión a la ameba y usar `BP_AimBeam` completo.

## Cómo corre
```
BP_Finale.StartExplore  → BeginExplore → BP_ConstExplorer.StartExploring
StartExploring: CacheExplore (constelación · archivo · audio · haptics) · CacheAim (pawn) · timer LOOP PollTime
PollHover:  PickAim → ScanSouls → ExploreResolve
   PickAim:    mano derecha si es válida, si no la cámara → AimOrigin / AimDir
   ScanSouls:  BestDot = cos(MaxAngleDeg) · recorre Constellation.Spawned → ScanOne → KeepBest
   ExploreResolve: si hubo mejor y CAMBIÓ respecto del anterior → CommitHover → PlayHovered
PlayHovered: índice = FindItem(Spawned, LastHovered) → Melodies[i] → AudioHub.StartMelody + háptico
BP_Finale.FinaleFadeOut → EndExplore → StopExploring
```
`BestFound` es un **int 0/1**, no un bool, a propósito: los bools con prefijo `b` **no se pueden escribir por DSL** (ver gotcha).

| Variable | Default | Rol |
|---|---|---|
| `MaxAngleDeg` | 10° | Cuán fino hay que apuntar. **La palanca de comodidad**: más grande = más fácil enganchar, más chico = más preciso. |
| `PollTime` | 0,15 s | Cada cuánto se rastrea. No hace falta por frame. |
| `BestDot` / `BestActor` / `BestFound` | — | El mejor candidato de la pasada actual. |
| `LastHovered` | — | Contra qué se compara para disparar **sólo al cambiar** (si no, la melodía se reiniciaría cada 0,15 s). |

## 🆕 El reproductor de melodías vive en [[BP_AudioHub]]
Porque lo van a necesitar dos lugares (acá y Attracting cuando tenga audio real):
- **`StartMelody(Melody)`** — parsea el CSV (`PlayMelodyString` → `ParseIntoArray` → `MelodyPushId`), arranca un timer y va disparando `MelodyTick` → `MelodyStepPlay` → **`PlayClipId(Id)`**, que toca `MelodyClips[Id]` y **avisa por log si el id está fuera de rango** en vez de fallar en silencio.
- `MelodyClips` (array de `SoundBase`, instance-editable) y `MelodyStep` (0,32 s) son de **Beltrán**: el banco y el tempo se autoran desde el editor. Hoy tiene los 2 MetaSounds de Touch (`MS_Synth`, `MS_Perc`).

## 🔴 Deuda real, y hay que decirla con precisión
**Lo que se guarda hoy como "melodía" NO son notas.** `BP_Finale.MelodyFromSlots` recorre los `BP_SeqSlot` y anota **`StepIndex`**, o sea *la posición en la secuencia*, no qué sonido hay en cada posición. Con eso, todas las melodías guardadas salen iguales (`0,1,2,3…`).
La serialización correcta es: **por cada slot en orden, el id de clip del ocupante**. No se puede escribir todavía porque **`BP_SoundBubble` no tiene un id de clip** — sólo un `PreviewSound`. Eso llega con **R8 de Attracting (el audio real)**, que ya estaba pendiente. Cuando la burbuja tenga su id, es un cambio de tres líneas en `MelodyFromSlots`.
👉 Mientras tanto, **toda la cadena de exploración ya funciona** con el string que haya; sólo cambia lo que ese string significa.

## TODO
- [ ] 🔴 **Visor**: apuntar con la mano, si 10° es cómodo, y si se necesita láser visible.
- [ ] 🔴 Arreglar `MelodyFromSlots` cuando `BP_SoundBubble` tenga id de clip (ver arriba).
- [ ] Feedback visual en la ameba apuntada (un anillo, un brillo) — hoy sólo suena y vibra.
- [ ] VO 29 antes de que arranque la exploración.

## Relacionados
- [[BP_Constellation]] (de dónde salen las amebas) · [[BP_SoulArchive]] (las melodías guardadas) · [[BP_AudioHub]] (el reproductor) · [[BP_Finale]] (quién lo abre y lo cierra) · [[BP_AimBeam]] (el beam de Attracting, que acá NO se usa para seleccionar)
