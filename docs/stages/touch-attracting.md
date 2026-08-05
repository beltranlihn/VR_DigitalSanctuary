# Stage Touch — "Attracting" (etapa de música) · brief + plan de construcción

> **Para el dev (Nico) y su Claude.** Este documento es la fuente autoritativa de la mecánica y el **orden de construcción**. **Supera la §4.4 del `Soul-Charger-Design.md`** (esa versión hablaba de "atraer con gesto suave / tirón brusco dispersa" y de generación procedural; la mecánica vigente es la de abajo: agarre a distancia con trigger + clips, no síntesis).
> Antes de tocar audio: leé `.claude/skills/unreal-vr/references/audio-quest.md` (MetaSounds/Quartz/config Android verificado contra el motor). Antes de tocar el pawn/input: `vr-pawn.md` + `input.md`. Widgets: `widgets-vr.md`.

Carpeta: `VR_Test/Content/SoulCharger/Stages/Touch/` · Nivel: `L_Touch` (duplicar de un nivel VR que ya funcione, p.ej. el patrón de `L_Test_Breath`, para heredar pawn + grab). Color de etapa: amarillo/naranja.

---

## 1. La mecánica (qué construimos)
El usuario llega a un **mesón/secuenciador con 5 bloques** vacíos. A su alrededor flotan **~20 burbujas sonoras** (mini-amebas), cada una con un **one-shot rítmico** distinto (mismo key/tempo). De fondo suena un **pad** suave, en loop, enganchado al reloj del secuenciador (que ya está en play).

**Loop de interacción:**
1. 🆕 **Tomar los sensores.** Frente al usuario flotan **dos sensores: uno de mano izquierda y uno de mano derecha** — cada uno **solo responde a su propia mano**. **Al tocarlo con la mano que le corresponde** (sin botón: por proximidad) el sensor **se attachea a ese mando** — su mesh pasa a ser la herramienta que se ve en la mano — y **eso enciende el beam de esa mano**. Antes de tomarlos no hay láser ni interacción posible: es el gesto que "entra" a la mecánica, igual que la varita de Movement (`BP_BrushTool`) y el sensor de Breath.
2. Con el sensor en mano hay un **beam/láser sutil** (estilo el puntero default de Meta), por line-trace desde la pose *aim* del controlador.
3. **Hover** sobre una burbuja → **se agranda un poco** (suave, entra y sale interpolado; `HoverScale`=1.15) + su sonido entra en **loop con fade-in 1s** (preview). Sacás el hover → **fade-out 1s**. Así explorás timbres. **Apuntar la misma burbuja con las dos manos NO duplica el audio** (ver §2).
4. Si te gusta, **trigger** → la "agarrás a distancia": su **posición objetivo pasa a ser la del mando** y se mueve hacia vos con **interpolación suave** (far-grab tipo varita). Movés la mano → te sigue.
5. La acercás a un **bloque** de la mesa; al soltarla cerca, **interpola hasta el bloque** y **entra al secuenciador**: ahora suena **cuando el playhead pasa por su step** (cuantizado, sin glitches, vía Quartz).
6. Cada vez que un bloque suena → **animación audioreactiva** (hook listo, animación después — Niagara o deformación de mesh).
7. Podés seguir agarrando otras y llenando bloques. Si posás sobre un **bloque ocupado** → **swap**: la nueva entra y la vieja **vuelve flotando a su posición original**.
8. 🆕 **Sacar una burbuja a mano.** Volvés a agarrar con el trigger una burbuja ya colocada y la soltás lejos de la mesa → el slot **queda libre** y la burbuja **vuelve flotando a su `HomeLocation`**. Se puede deshacer y rehacer la melodía todas las veces que se quiera.
9. Con los **5 bloques llenos** se habilita el botón **"FINISH MELODY"** (frente a la mesa, apuntable con el beam + trigger; deshabilitado y apagado hasta tener los 5).
10. Al activarlo: la melodía se **persiste** (SaveGame), **suena una vez más** y **cierra la etapa** (fade → reinicia el level, cierre de prueba igual que los otros stages).

**Flujo del stage (como los demás):** instrucciones (widget world-space) → experiencia (explorar/colocar) → cierre (guardar → melodía 1 vez → reinicia).

## 2. Decisiones cerradas (no re-preguntar)

### 2.a 🆕 Rearmado de la mecánica (2026-08-04) — supera lo anterior donde choque
- **Dos sensores flotantes, uno por mano, tomados POR CONTACTO.** No hay botón para tomarlos: el sensor detecta la mano cerca y **se attachea al mando**. Su propio mesh **es** la herramienta visible en la mano (un solo asset resuelve "tomar" y "mesh atachado"). Nace de la continuidad con las otras etapas: en Movement se agarra `BP_BrushTool`, en Breath se sostiene el sensor.
  - 🔴 **Un sensor POR MANO, y cada uno solo responde a la SUYA.** El sensor izquierdo solo se attachea si lo toca la mano izquierda, el derecho solo con la derecha. No es "el primero que toca gana": tocar el sensor derecho con la izquierda **no hace nada**. Implementación: var **`bIsRight : bool` instance-editable** en `BP_TouchSensor` (mismo patrón que ya usa `BP_AimBeam`), y el sensor mide la distancia **solo contra el beam cuyo `bIsRight` coincide con el suyo**.
    - ⚠ **Trampa ya vivida con `bIsRight` en `BP_AimBeam`:** al agregar la variable, **la instancia ya colocada en el nivel NO hereda el default nuevo del CDO**. Después de colocar los 2 sensores, **verificar el `bIsRight` de cada instancia en el nivel**, no el del Blueprint.
  - **Detección por distancia, NO por colisión del pawn.** El sensor chequea en su Tick la distancia contra la mano de **su** `BP_AimBeam` (que ya vive attacheado al pawn y ya cachea su motion controller). Son 2 actores × 1 distancia por frame = trivial, y **no toca `Core/` ni el pawn** (regla §7 del `CLAUDE.md`: el pawn queda liviano y los assets compartidos no se tocan).
  - **No se sueltan.** Una vez tomados quedan hasta el cierre de la etapa. Si alguna vez hace falta soltar, se agrega después; hoy es complejidad sin propósito.
- **El beam arranca APAGADO y lo enciende el sensor.** `BP_AimBeam` gana un `bEquipped` (default `false`): sin él no hay line-trace, ni Niagara, ni cursor, ni far-grab. Beneficio doble: el gesto de entrada existe, y se acaba el ruido visual de dos láseres permanentemente encendidos en una obra contemplativa.
- **Apuntar con las dos manos NO duplica el audio.** El preview se maneja con un **contador `HoverCount`, no un bool**: fade-in solo en la transición 0→1, fade-out solo al volver a 0 (con clamp en 0). Ya está implementado en `BP_SoundBubble`; **falta confirmarlo en visor con las dos manos sobre la misma burbuja**.
- **Swap por superposición.** Soltar una burbuja sobre un slot **ocupado** intercambia: la nueva entra, la vieja vuelve a su `HomeLocation`. Ya implementado (`EvictSlot` + `PlaceInNearestSlot` busca el slot **más cercano**, no el primero del array).
- **Sacar burbujas a mano.** Re-agarrar una burbuja colocada **libera su slot inmediatamente** (ya arreglado: el `Occupant` stale se limpia al agarrar). Si se la suelta **fuera del radio de cualquier slot** → **vuelve flotando a su `HomeLocation`**. Nunca queda una burbuja abandonada fuera de alcance del usuario sentado.
- 🔴 **TODO movimiento interpola, sin excepción.** Hoy el follow del far-grab interpola (`VInterpTo`) pero **el snap al slot y el `ReturnHome` son `SetActorLocation` instantáneo** — se ven como teleports. Unificar en `BP_SoundBubble` con un **único destino interpolado**: vars `TargetLocation` + `MoveMode` (`Follow` / `ToSlot` / `ToHome` / `Idle`) y **un solo `VInterpTo` en el Tick** hacia `TargetLocation`. Colocar y volver a casa pasan a ser "setear el destino y cambiar de modo". Además de arreglar el teleport, **baja nodos** (un solo interp compartido, patrón de `bp-lean-construction.md`).
- **El botón se llama "FINISH MELODY"** (🔴 textos in-headset en **inglés**, regla del proyecto). Es el mismo `BP_SaveButton`: gateado por los 5 slots llenos, guarda la melodía y cierra la etapa. Apagado/sin respuesta al beam mientras falten bloques.

### 2.b Decisiones previas (vigentes)
- **Secuenciador = 5 pasos secuenciales.** Un playhead recorre bloque 1→2→3→4→5 en loop; cada bloque lleno dispara su clip al pasar. La melodía es un patrón rítmico de 5 golpes.
- **Clips = one-shots rítmicos**, mismo key y tempo (los provee el usuario/sound designer; mientras tanto **placeholders**). Nada sintetizado en Unreal — solo reproducción de clips. Quartz solo agenda el timing (no es "audio generado").
- **Preview en hover = loop con fade 1s** (entra/sale suave).
- **Guardado = SaveGame persistente**: la melodía es un **array de 5 clip-IDs** (qué sonido en qué bloque) en un `.sav`, para reusar en futuras mecánicas de Soul Charger. Al guardar: suena 1 vez y reinicia.
- **Tempo/loop (propuesta, ajustable):** ~72 BPM, 1 step por beat → loop de 5 beats (feel hipnótico 5/4). Se cambia en un lugar.
- **Todos los movimientos con interpolación suave** (FInterpTo), fades de 1s.
- **Audioreactivo = placeholder** (evento listo, animación luego).

## 3. Arquitectura de Blueprints (respetar: 1 responsabilidad por BP, pawn liviano)
| BP / Asset | Responsabilidad |
|---|---|
| **`BP_AttractDirector`** | Cerebro del stage: máquina de flujo (instrucciones→experiencia→guardar→cierre), dueño del **reloj Quartz** y del **step sequencer** (avanza el playhead, dispara el clip del slot en su beat, corre el pad). Cuenta bloques llenos → habilita el botón. |
| 🆕 **`BP_TouchSensor`** | El sensor flotante que se toma con la mano. **2 instancias en `L_Touch` — una izquierda y una derecha, cada una con su `bIsRight`** — y cada una **solo responde a su mano**. Detecta esa mano por distancia, se attachea a ese mando, y **enciende el beam de esa mano** (`beam.SetEquipped(true)`). Su mesh es la herramienta visible. Deja de tickear una vez tomado. |
| **`BP_SoundBubble`** | Una burbuja. Estado (`Floating`/`Hovered`/`Grabbed`/`Placed`), su `HomeLocation` (para el swap y el retorno), su `ClipID`/`SoundWave`. Preview loop con fade (por `HoverCount`, sirve a las 2 manos); **un único destino interpolado** (`TargetLocation` + `MoveMode`) para follow / snap a slot / vuelta a casa; hook audioreactivo cuando suena. |
| **`BP_SeqTable`** + **`BP_SeqSlot`** | La mesa y sus 5 slots. Cada slot conoce su `StepIndex` (0-4) y su `Occupant` (burbuja o vacío). Detecta cuando una burbuja se posa encima. |
| **`BP_AimBeam`** (actor del lado del mando, NO metido en el pawn) | Line-trace desde la pose *aim*; resuelve el hover (qué burbuja/botón está apuntado); expone eventos Hover/Unhover/Trigger. 🆕 **Gateado por `bEquipped`**: inerte hasta que su sensor lo enciende. |
| **`BP_SaveButton`** | Botón apuntable **"FINISH MELODY"**. Gateado por `bAllSlotsFull`. Al triggear → pide al Director guardar + cerrar. |
| **`WBP_TouchInstructions`** + su BP | Instrucciones (world-space, patrón de los otros stages). |
| **`SG_Melody`** (SaveGame) | Persistencia: `array<int> ClipIDs` (5) + metadata. Patrón idéntico al de `Calibration/` (`SG_CalibSession`). |
| **`DA_SoundBank`** (DataAsset o array) | Los 20 SoundWaves + su preview. Placeholders al inicio. |

## 3.b 🔊 Arquitectura de audio — decisión cerrada (2026-08-04)
**La pregunta era: si trabajamos con clips, ¿igual usamos MetaSound?** Respuesta: **sí, pero para la voz — no para el banco.** Son dos cosas distintas que conviene no mezclar.

| Pieza | Qué usar | Por qué |
|---|---|---|
| **Banco de clips** | **`DA_SoundBank`** (DataAsset con los SoundWaves) | Un MetaSound es un **grafo de reproducción**, no una biblioteca de assets. Además la Builder API **solo modifica MetaSounds en editor** (`audio-quest.md`) → **no se puede hornear un MetaSound en el dispositivo**: el banco tiene que ser datos igual. Un grafo monolítico con los 20 clips adentro sería peor: carga todo, no se versiona bien y bloquea al sound designer. |
| **Voz de la burbuja** | 🆕 **UN solo `MS_BubbleVoice`** con un **pin de entrada `Wave`**, compartido por las 20 burbujas | Cada burbuja setea su wave con **`SetObjectParameter` ANTES del Play** (**pin de constructor**: read-only, sin actualización en runtime = la variante barata). Un solo asset concentra: **salida mono** (obligatoria para que se espacialice — los stereo no pasan por el spatializer), **`ITD Panner` in-graph** (paneo binaural real sin plugin, ideal para elementos que orbitan a un usuario sentado), la envolvente/fades del hover consistente entre todas, y un **Plate Reverb** compartido → el "espacio" del stage se ajusta en un asset, no burbuja por burbuja. |
| **Pad de fondo** | **`MS_Pad`** con **`On Nearly Finished`** del Wave Player | Encadena variaciones **sin corte**, cosa imposible con un SoundWave en loop plano. |
| **Disparo en el beat** | **Quartz `PlayQuantized`** sobre el AudioComponent | Ya está el reloj (`TouchClock`). Elimina el jitter de frame del `Play()` común. Requiere pasarle el `ClockHandle` a la burbuja. |
| **Pulso audioreactivo** | **`WatchOutput`** desde el grafo | El grafo es dueño del beat y **empuja** eventos a Blueprint, en vez de que BP adivine el timing. |
| **Codecs** | **ADPCM** one-shots · **Bink** pad | 🔴 **Nunca `PLATFORM_SPECIFIC`**: en Android es Vorbis y **no soporta seek** → rompe los loop points y el `Start Time` del Wave Player. |

⚠ **Lo que NO justifica el cambio:** si lo único que se necesita es "sonar el clip con fade de 1s", el `AudioComponent` ya tiene `FadeIn`/`FadeOut` nativos y un SoundWave plano es más barato. Cada instancia de MetaSound tiene overhead de grafo y **nadie publicó el presupuesto de voces de MetaSound en Quest** — con ~20 burbujas en preview hay que **medirlo con Audio Insights en el visor**. Palanca si aprieta: `au.MetaSound.BlockRate=50` **solo en Android** (es `FPerPlatformFloat`).

🕐 **Cuándo hacerlo: en la Fase 10, cuando lleguen los clips reales.** Hoy `MS_Synth`/`MS_Perc` (MetaSounds procedurales, sin dependencias) ya cumplen como placeholder y el refactor de `BP_SoundBubble` no daría ninguna ganancia audible todavía.

## 4. 🗺️ Organigrama de construcción (fase → test → siguiente)
**Método (igual que Breath/Calibration): construir una fase, COMPILAR, TESTEAR en visor, actualizar el tracker del BP, recién ahí la siguiente.** Cada fase es testeable sola.

| # | Construir | Cómo se testea (visor/PIE) |
|---|---|---|
| **0. Setup** | Carpeta `Stages/Touch/`, `L_Touch` duplicando un nivel VR con pawn+grab. `DA_SoundBank` con 5-6 placeholders. Crear tracker `blueprints/BP_AttractDirector.md`. | El nivel abre en VR, ves el pawn, el piso. |
| **1. Beam de apuntado** | `BP_AimBeam`: line-trace desde pose *aim* del mando; dibuja el láser sutil; detecta hit sobre un actor "apuntable". Eventos Hover/Unhover. | Apuntás a un cubo de prueba → se resalta al hover, se apaga al salir. |
| **2. Burbujas + preview de sonido** | `BP_SoundBubble` (mesh/placeholder + AudioComponent). Al Hover → preview **loop con fade-in 1s**; Unhover → **fade-out 1s**. Colocar ~6 burbujas flotando. | Apuntás una burbuja → suena su clip en loop suave; soltás → se desvanece. |
| **3. Far-grab + follow** | Trigger sobre burbuja hovered → `Grabbed`; su target = pose del mando; `FInterpTo` suave hacia ahí. Segundo trigger/soltar la libera. | Agarrás una burbuja, la movés con la mano y te sigue suave como varita. |
| **4. Mesa + slots + attach** | `BP_SeqTable` + 5 `BP_SeqSlot` (en alcance de brazos **sentado**). Al soltar una burbuja `Grabbed` cerca de un slot vacío → se attachea (interp) y queda `Placed`; el slot guarda su `Occupant`. | Posás una burbuja en un slot → queda pegada y centrada. |
| **5. Quartz + step sequencer + pad** | En `BP_AttractDirector`: crear Quartz Clock (BPM), correr el **pad** en loop, playhead 0→4 por beat (subscribe a Quantization Event `Beat`); en cada step, si el slot está ocupado → **Play Quantized** su clip. | Con 2-3 slots llenos, escuchás el patrón rítmico en loop, cuantizado, sobre el pad. Sin glitches. |
| **6. Hook audioreactivo** | Cuando un slot dispara → evento a su burbuja `OnBeatHit` → animación **placeholder** (ej. un pulso de escala simple). | La burbuja "late" en su beat. |
| **7. Swap** | Soltar sobre slot **ocupado** → intercambio: la nueva se attachea, la vieja vuelve a su `HomeLocation` (interp). | Posás sobre un bloque lleno → se cambian, la vieja vuelve flotando a su lugar. |
| **8. Botón Guardar + SaveGame** | `BP_SaveButton` apuntable, habilitado solo con `bAllSlotsFull`. Trigger → `SG_Melody` con los 5 `ClipID` → `SaveGameToSlot`. (Reusar patrón de `Calibration/`.) | Con 5 llenos, apuntás el botón, trigger → se guarda; verificás el `.sav`. |
| **9. Instrucciones + cierre** | `WBP_TouchInstructions` (patrón otros stages) al inicio. Al guardar → melodía suena 1 vez → fade → `OpenLevel` (reinicia). | Corre end-to-end: instrucciones → explorar → llenar 5 → guardar → suena → reinicia. |
| **10. Pulido + Android** | Fix del bug de audio del `.ini` (mover bloque a `AndroidRuntimeSettings`, ver `audio-quest.md`); codecs (ADPCM one-shots, Bink pad); `Non-Spatialized Radius`; medir voces con Audio Insights; empaquetar Development y probar en device. | Corre en el APK real sin glitches; mezcla a −16 LUFS. |

### 4.b 🆕 Fases del rearmado (2026-08-04) — el orden a seguir desde acá
Las fases 0-7 de la tabla de arriba están **cerradas y funcionando en visor**. Lo que sigue reemplaza/extiende las fases 8-10 con el rearmado de la mecánica. **Mismo método: construir → compilar → testear en visor → actualizar el tracker → recién ahí la siguiente.**

| # | Construir | Cómo se testea (visor) |
|---|---|---|
| ✅ **R1. Interp unificada** | **HECHO 2026-08-04.** En `BP_SoundBubble`: vars `TargetLocation` / `bMoving` / `TravelSpeed`, función nueva **`UpdateMove`** con **un solo `VInterpTo`**, llamada incondicional desde el Tick. `PlaceInNearestSlot` y `ReturnHome` dejaron de hacer `SetActorLocation` y ahora solo setean destino. `DoFollow` eliminada. Detalle en su tracker. | **FALTA EL TEST:** colocar una burbuja en un slot **ya no debe teletransportar**: viaja suave. El swap muestra a la vieja **volando** de vuelta a su lugar, no apareciendo ahí. |
| ✅ **R2. Sacar burbuja a mano** | **HECHO 2026-08-04.** La rama "Is Not Valid" de `PlaceInNearestSlot` (estaba vacía) ahora llama `ReturnHome()`. El slot ya se libera al agarrar. | **FALTA EL TEST:** sacás una burbuja de un slot y la soltás en el aire → el slot deja de sonar en su beat y la burbuja vuelve flotando a su punto de origen. Repetible N veces. |
| ✅ **R3. Sensores + gateo del beam** | **HECHO 2026-08-04.** `BP_TouchSensor` nuevo (mesh + `TakeRadius`=12 + `bIsRight`; `CacheBeam`/`TryTake`/`Take`) y en `BP_AimBeam` la var `bEquipped`=false + función `Equip()` + early-out del Tick + guard en `TryGrab`. **2 instancias** colocadas en `L_Touch` con su `bIsRight` verificado por instancia. Trackers: [`BP_TouchSensor`](../../.claude/skills/unreal-vr/blueprints/BP_TouchSensor.md), [`BP_AimBeam`](../../.claude/skills/unreal-vr/blueprints/BP_AimBeam.md). | **FALTA EL TEST:** al empezar **no hay láser**. Acercás la mano derecha al sensor derecho → se pega, aparece el mesh y **se enciende el beam derecho**; la izquierda sigue apagada. **Tocar el sensor derecho con la mano izquierda NO hace nada.** Y el gatillo antes de tomar el sensor no agarra nada ni tira warnings. |
| **R4. Doble hover** | Nada nuevo que construir — `HoverCount` ya está. **Verificar**. | Apuntás la **misma** burbuja con las dos manos: el preview suena **una sola vez** (no se dobla el volumen). Sacás una mano → sigue sonando. Sacás la otra → recién ahí hace fade-out. |
| **R5. Botón FINISH MELODY** | `BP_SaveButton`: tag `Aimable`, estado apagado/encendido por `bAllSlotsFull` (el Director se lo notifica al llenar/vaciar slots), trigger → `Director.SaveMelody()`. Texto **en inglés**. | Con 4 slots el botón está apagado y el trigger no hace nada. Al llenar el 5º se enciende. Lo apuntás + trigger → guarda. Sacás una burbuja → se vuelve a apagar. |
| **R6. SaveGame + cierre** | `SG_Melody` con el array de 5 `ClipID` (crear el array **en el editor**, `add_variable` por MCP no crea arrays) → `SaveGameToSlot`. Después: melodía suena 1 vuelta más → fade → `OpenLevel(L_Touch)`. | Guardás, escuchás la vuelta final, funde y reinicia. Verificás el `.sav` en disco. |
| **R7. Instrucciones** | Opción A del §6.b (páginas manejadas desde el Director). Textos **en inglés**. | Corre end-to-end: instrucciones → tomar sensores → explorar → llenar 5 → FINISH MELODY → suena → reinicia. |
| **R8. Audio real + Android** | La arquitectura del §3.b: `MS_BubbleVoice` parametrizado, `MS_Pad`, `PlayQuantized`, codecs. Fix del `.ini` de audio (mover el bloque a `AndroidRuntimeSettings`). Medir voces con Audio Insights. | Corre en el APK real sin glitches; mezcla a −16 LUFS. |

## 5. Cabos técnicos clave (para que Claude no los redescubra)
- **Quartz es el que evita glitches**: dispará los clips con **`Play Quantized`** en boundary `Beat`, nunca directo desde el game thread (jitter de frame). `WatchOutput`/subscribe para mover el playhead y el audioreactivo **en** el beat. Todo en `audio-quest.md`.
- **Beam/hover/trigger**: input por Enhanced Input EVENTS (los value-getters de OpenXR dan 0 fuera de su IMC — lección ya aprendida en el sensor de Breath). Pose *aim* ≠ *grip* (ver `motion-controller-data.md`).
- **Far-grab**: reusar el patrón de grab-con-`FInterpTo` ya probado (proyecto de dibujo / `Recursos/`); el objeto interpola su world-location hacia la pose del mando.
- **Persistencia**: copiar el patrón de `Content/SoulCharger/Calibration/` (SaveGame + slot), y `bUseExternalFilesDir=True` ya está puesto en `DefaultEngine.ini`.
- **Quest standalone**: fuentes espacializadas deben ser **mono** (ITD Panner in-graph si querés que las burbujas suenen posicionadas); todo horneado; ver `materials-vr.md`/`lighting-quest.md` para la estética.
- **Widgets world-space** obligatorio (`widgets-vr.md`), event-driven, no property binding.
- 🆕 **El sensor NO necesita colisión en el pawn.** Chequear distancia contra la mano en el Tick del sensor es más barato y más robusto que ponerle colliders al pawn — y evita tocar `Core/`, que es compartido (§7 del `CLAUDE.md`).
- 🆕 **Attach a la mano:** `AttachActorToComponent` sobre el motion controller del pawn (pose **grip**, no *aim* — la herramienta se sostiene, no apunta; ver `motion-controller-data.md`). El beam sigue trazando desde la pose *aim*, que es lo probado; el mesh del sensor solo tiene que **leerse** como el origen del láser, no serlo literalmente.
- 🆕 **Antes de agregar cualquier input nuevo, leer `assets-existentes.md`.** Lo que funciona hoy es `IA_Shoot_Right`/`IA_Shoot_Left` del XRFramework (`Started`→`TryGrab`, `Completed`→`TryRelease`); los `IA_Attract_*` propios **nunca dispararon** pese a registrarse bien. El sensor por contacto se eligió justamente para **no agregar input nuevo**.

## 6. Assets y contenido que hay que proveer (usuario / sound designer)
**Audio:**
- **20 one-shots** rítmicos, mismo key y tempo, seekeables → import **ADPCM**. (Placeholders mientras.)
- **1 pad** de fondo en loop, mismo key/tempo → **Bink**.
- Definir el **tempo/BPM** final (propuesta 72) y si el loop son 5 beats u otra subdivisión.
- 🔴 **Mono, no stereo**, para todo lo que deba sonar posicionado: los archivos multicanal **no pasan por el spatializer** (ver §3.b).

**Modelado / VFX:**
- 🆕 **Mesh del sensor** — la herramienta que queda en la mano. Placeholder mientras (una forma simple emisiva).

**Contenido POR DEFINIR (bloquea el pulido, no el armado de la mecánica):**
- 🖊️ **Textos del widget de instrucciones** de esta etapa (`WBP_TouchInstructions`) — **quedan por definir.** El widget ya está (fondo naranja); falta escribir las páginas (qué dice cada instrucción). Mientras, van placeholders.
- 🖼️ **Imágenes / íconos para los materiales** de esta etapa (íconos de las páginas de instrucciones, y las texturas/íconos de las burbujas y la mesa si aplica) — **quedan por definir.** Se usan placeholders hasta que el usuario los cree/entregue.

## 6.b 🧰 Scaffold ya creado en `Stages/Touch/` (punto de partida)
Ya están estos assets en `VR_Test/Content/SoulCharger/Stages/Touch/` para arrancar sin partir de cero:
- **`Widget/WBP_TouchInstructions`** — duplicado del widget de instrucciones de Breath, **con fondo NARANJA** (`BG` Border a rgb ~0.9/0.35/0.05). Es el visual de las páginas. Compila.
- **`BP_TouchInstructions`** — driver duplicado de `BP_Instructions` (la máquina de 5 páginas: `GotoPage/InitRefs/UpdateFade` + `SpawnSensor/SpawnBox` heredados de Breath). **Sin wirear todavía** (ver abajo).
- **`Widget/Material/W_TouchInstruction`** — material duplicado (para no pisar el de Breath).
- **Stubs vacíos** (Actor, listos para rellenar): `BP_AttractDirector`, `BP_SoundBubble`, `BP_SeqTable`, `BP_SeqSlot`, `BP_AimBeam`, `BP_SaveButton`.
- **`SG_Melody`** (SaveGame, vacío — agregarle el array de 5 `int` ClipIDs en el editor; `add_variable` por MCP no crea arrays).

### 🔧 Primeras tareas de wiring (lo que quedó pendiente a propósito, para hacer con el visor)
El driver `BP_TouchInstructions` **todavía apunta al widget de Breath** (`InitRefs` castea a `WBP_BreathInstructions` y su `Panel`/`WRef` son de Breath). Repuntarlo a ciegas rompía la compilación, así que se dejó como primer tarea. **Dos caminos:**
- **Opción A (recomendada, más limpia):** NO reusar el driver breath. Quedarse solo con `WBP_TouchInstructions` (el visual naranja) y **manejar las páginas desde `BP_AttractDirector`** con un `GotoPage` simple (mostrar/ocultar páginas por índice, avanzar con el trigger vía Enhanced Input EVENTS). Así el stage de música no arrastra la lógica de spawn de Breath. Borrar `BP_TouchInstructions` si se va por acá.
- **Opción B (reusar el driver):** repuntar `BP_TouchInstructions`: (1) el `WidgetClass` de la `WidgetComponent` que alimenta `Panel` (se asigna en runtime, rastrear desde `BP_IntroFade`), (2) retargetear el cast `CastToWBP_BreathInstructions`→`WBP_TouchInstructions` en `InitRefs`, (3) retipar la var `WRef` a `WBP_TouchInstructions`, (4) borrar/neutralizar `SpawnSensor`/`SpawnBox`/`StartBreathStage` (son de Breath). Verificar en visor que el trigger avanza páginas.
- El **fondo naranja ya está**; ajustar el tono si hace falta en el Border `BG` de `WBP_TouchInstructions`.

## 7. Naming
"Touch" (carpeta/nivel `L_Touch`) = "Attracting" (nombre de obra) = esta etapa de música. Rama de git sugerida: **`stage/touch`**. Al avanzar, actualizar `docs/ESTADO-STAGES.md` y los trackers en `.claude/skills/unreal-vr/blueprints/`.
