# Stage Touch — "Attracting" (etapa de música) · brief + plan de construcción

> **Para el dev (Nico) y su Claude.** Este documento es la fuente autoritativa de la mecánica y el **orden de construcción**. **Supera la §4.4 del `Soul-Charger-Design.md`** (esa versión hablaba de "atraer con gesto suave / tirón brusco dispersa" y de generación procedural; la mecánica vigente es la de abajo: agarre a distancia con trigger + clips, no síntesis).
> Antes de tocar audio: leé `.claude/skills/unreal-vr/references/audio-quest.md` (MetaSounds/Quartz/config Android verificado contra el motor). Antes de tocar el pawn/input: `vr-pawn.md` + `input.md`. Widgets: `widgets-vr.md`.

Carpeta: `VR_Test/Content/SoulCharger/Stages/Touch/` · Nivel: `L_Touch` (duplicar de un nivel VR que ya funcione, p.ej. el patrón de `L_Test_Breath`, para heredar pawn + grab). Color de etapa: amarillo/naranja.

---

## 1. La mecánica (qué construimos)
El usuario llega a un **mesón/secuenciador con 5 bloques** vacíos. A su alrededor flotan **~20 burbujas sonoras** (mini-amebas), cada una con un **one-shot rítmico** distinto (mismo key/tempo). De fondo suena un **pad** suave, en loop, enganchado al reloj del secuenciador (que ya está en play).

**Loop de interacción:**
1. En el mando hay un **beam/láser sutil** (estilo el puntero default de Meta), por line-trace desde la pose *aim* del controlador.
2. **Hover** sobre una burbuja → pequeña reacción visual (material/Niagara, *placeholder*) + su sonido entra en **loop con fade-in 1s** (preview). Sacás el hover → **fade-out 1s**. Así explorás timbres.
3. Si te gusta, **trigger** → la "agarrás a distancia": su **posición objetivo pasa a ser la del mando** y se mueve hacia vos con **interpolación suave** (far-grab tipo varita, reusar el patrón de grab-con-interp ya probado). Movés la mano → te sigue.
4. La acercás a un **bloque** de la mesa; al tocarlo, queda **attach** a ese bloque y **entra al secuenciador**: ahora suena **cuando el playhead pasa por su step** (cuantizado, sin glitches, vía Quartz).
5. Cada vez que un bloque suena → **animación audioreactiva** (hook listo, animación después — Niagara o deformación de mesh).
6. Podés seguir agarrando otras y llenando bloques. Si posás sobre un **bloque ocupado** → **swap**: la nueva se attachea y la vieja **vuelve a su posición flotante original**. Todo con interp suave.
7. Con los **5 bloques llenos** se habilita el botón **"Guardar melodía"** (frente a la mesa, apuntable con el beam + trigger; deshabilitado hasta tener los 5).
8. Al guardar: la melodía se **persiste** (SaveGame), **suena una vez más** y **reinicia el level** (cierre de prueba, igual que los otros stages).

**Flujo del stage (como los demás):** instrucciones (widget world-space) → experiencia (explorar/colocar) → cierre (guardar → melodía 1 vez → reinicia).

## 2. Decisiones cerradas (no re-preguntar)
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
| **`BP_SoundBubble`** | Una burbuja. Estado (`Floating`/`Hovered`/`Grabbed`/`Placed`), su `HomeLocation` (para el swap), su `ClipID`/`SoundWave`. Preview loop con fade; follow-interp cuando `Grabbed`; hook audioreactivo cuando suena. |
| **`BP_SeqTable`** + **`BP_SeqSlot`** | La mesa y sus 5 slots. Cada slot conoce su `StepIndex` (0-4) y su `Occupant` (burbuja o vacío). Detecta cuando una burbuja se posa encima. |
| **`BP_AimBeam`** (componente/actor del lado del mando, NO metido en el pawn) | Line-trace desde la pose *aim*; resuelve el hover (qué burbuja/botón está apuntado); expone eventos Hover/Unhover/Trigger. |
| **`BP_SaveButton`** | Botón apuntable "Guardar melodía". Gateado por `bAllSlotsFull`. Al triggear → pide al Director guardar + cerrar. |
| **`WBP_TouchInstructions`** + su BP | Instrucciones (world-space, patrón de los otros stages). |
| **`SG_Melody`** (SaveGame) | Persistencia: `array<int> ClipIDs` (5) + metadata. Patrón idéntico al de `Calibration/` (`SG_CalibSession`). |
| **`DA_SoundBank`** (DataAsset o array) | Los 20 SoundWaves + su preview. Placeholders al inicio. |

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

## 5. Cabos técnicos clave (para que Claude no los redescubra)
- **Quartz es el que evita glitches**: dispará los clips con **`Play Quantized`** en boundary `Beat`, nunca directo desde el game thread (jitter de frame). `WatchOutput`/subscribe para mover el playhead y el audioreactivo **en** el beat. Todo en `audio-quest.md`.
- **Beam/hover/trigger**: input por Enhanced Input EVENTS (los value-getters de OpenXR dan 0 fuera de su IMC — lección ya aprendida en el sensor de Breath). Pose *aim* ≠ *grip* (ver `motion-controller-data.md`).
- **Far-grab**: reusar el patrón de grab-con-`FInterpTo` ya probado (proyecto de dibujo / `Recursos/`); el objeto interpola su world-location hacia la pose del mando.
- **Persistencia**: copiar el patrón de `Content/SoulCharger/Calibration/` (SaveGame + slot), y `bUseExternalFilesDir=True` ya está puesto en `DefaultEngine.ini`.
- **Quest standalone**: fuentes espacializadas deben ser **mono** (ITD Panner in-graph si querés que las burbujas suenen posicionadas); todo horneado; ver `materials-vr.md`/`lighting-quest.md` para la estética.
- **Widgets world-space** obligatorio (`widgets-vr.md`), event-driven, no property binding.

## 6. Assets que hay que proveer (usuario / sound designer)
- **20 one-shots** rítmicos, mismo key y tempo, seekeables → import **ADPCM**. (Placeholders mientras.)
- **1 pad** de fondo en loop, mismo key/tempo → **Bink**.
- Definir el **tempo/BPM** final (propuesta 72) y si el loop son 5 beats u otra subdivisión.

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
