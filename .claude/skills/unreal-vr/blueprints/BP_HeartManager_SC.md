# BP_HeartManager_SC — el latido PORTABLE (Mechanics/Heart/)

> `/Game/SoulCharger/Mechanics/Heart/BP_HeartManager_SC` · creado 2026-09-19 · **una instancia** en `/Game/TestMeshes` (`Galeria/_Sistema`).
> Pedido de Beltrán: *"en esta estación vas a quitar la respiración y traer la mecánica de ritmo cardíaco, en la que el usuario tiene que poner el control en su corazón y cuando reconozca que está en el umbral de quietud va a generar un pulso háptico con cada ritmo cardíaco y con cada nacimiento de la ola, y además emitir el sonido de pulso"*.
> Es el **paso 4 del plan de extracción** de [`docs/MECANICAS-PORTABLES.md`](../../../../docs/MECANICAS-PORTABLES.md) §4.8.
> **Estado: 🟡 construido y compilando. ⬜ SIN PIE y SIN visor.**

## Qué es
El modo 2 de [[BP_Sensor_Soul]] (`TickHeart` + `HeartBeatStep` + `HeartZoneFx`) **sacado del sensor**, con el mismo patrón que [[BP_BreathManager_SC]]: no conoce al pawn por clase, no conoce directores, no es dueño del input y no tiene etapas. `BP_Sensor_Soul` **no se tocó**.

El manager **no detecta el latido**: detecta la **mano en el pecho** y le pone reloj al BPM que publica `BP_BioHub` (`HeartSmooth`, por OSC o por `bFakeSignal`).

## API — lo que publica (`Y - Publicado`)
| Señal | Tipo | Uso |
|---|---|---|
| `bHeartZone` | bool | el mando está en la zona del pecho y quieto el tiempo de `ActivateDelay` (con histéresis de salida) |
| `BeatCount` | int | latidos contados. 🔴 **solo avanza dentro del umbral** |
| `BeatEnv` | float 1→0 | envelope del latido (decae a `BeatEnvDecay`) — modula el zumbido |
| `HeartBPM` | float | el BPM efectivo, ya clampeado 30–200 |
| **`OnHeartBeat`** | dispatcher | se emite en cada latido |

🔴 **Se llama `OnHeartBeat`, NO `OnBeatPulse`.** `BP_Sensor_Soul` ya tiene un dispatcher `OnBeatPulse` y el DSL, al resolver `Default|CallOnBeatPulse`, **agarró el del sensor** y el BP falló a compilar con *"This blueprint (self) is not a BP_Sensor_Soul_C"*. Es el gotcha de colisión de nombres del DSL. Renombrarlo fue el arreglo.
⚠ Quedó un dispatcher `OnBeatPulse` huérfano: el MCP **no tiene `remove_event_dispatcher`**, hay que borrarlo a mano en el panel My Blueprint.

## 🔑 El umbral manda TODO (corregido por Beltrán en visor, 2026-09-19)
🔴 **Primera versión (equivocada):** dejé el reloj corriendo siempre y gateé solo la háptica y el sonido, razonando que si no las olas morirían al bajar el mando. Beltrán lo probó: *"se activó solo. Esto se debe activar con la mecánica de poner el sensor en mi corazón... si no estoy en el umbral, no salen más pulsos"*. **Que el campo quede quieto NO es un defecto: es la obra.** La estación existe para que el gesto de llevarse el mando al pecho encienda el latido.

✅ **Ahora `HeartBeatStep` entero está gateado por `bHeartZone`**: sin umbral no hay latido, ni pulso, ni sonido, ni `OnHeartBeat`, ni ola nueva. Las olas ya vivas terminan su viaje y mueren solas (`WaveDist` sigue corriendo).
🔎 Dos detalles de tacto: al **salir** de la zona el timer se arma (`BeatTimer = 9999`) para que el **primer latido salga en el instante** en que el umbral vuelve a abrir — confirmación inmediata del gesto; y la **primera ola** llega en el 2º latido (con `BeatsPerWave` 2), así que la secuencia es: umbral → pulso → pulso + ola.
⚠ `BP_PulseField_SC.ResetRise` (en `BeginPlay`) ahora **limpia también el estado de las olas** (`RingBirth`, `WaveDist`, `PulsePhase`, `LastBeat`): si no, las olas que el Construction Script siembra para la vista previa salían solas al dar Play.

## Perillas
| Cat | Variable | Default | Rol |
|---|---|---|---|
| **A - Zona** | `HeartHorizMax` | 25 | distancia horizontal máx. cabeza→mando (cm) |
| | `HeartVDropMin` / `HeartVDropMax` | 10 / 45 | caída vertical cabeza→mando (cm). ⚠ **puestos A OJO en la obra, sin respaldo de datos** |
| | `ActivateDelay` / `DeactivateDelay` | 1,5 / 0,3 s | debounce: entrar lento, salir rápido (la histéresis que en el sensor era deuda) |
| **B - Ritmo** | `BeatDiv` | **1** | latidos por pulso emitido. El sensor usaba 2 (medio latido) para el ascensor; acá 1 = un pulso por latido |
| | `BeatEnvDecay` | 2,5 | caída del envelope |
| **C - Feedback** | `bHaptics` · `HapticAmp` 0,25 · `HapticEffect` (`GrabHapticEffect`) · `bSound` · `HeartBeatSound` (`Core/Audio/Sounds/HeartBeat`) | | 🔴 el pulso viaja **DENTRO** del zumbido (`lerp(HapticAmp, 1, BeatEnv)`): `SetHapticsByValue` continuo PISA un `PlayHapticEffect` del mismo canal |
| **D - Mano** | `bAutoHand` / `bRightHand` | true / true | con auto, elige la mano más cerca del pecho mientras NO hay umbral |
| **E - Prueba** | `bFakeBeat` / `FakeBPM` | false / 60 | latido sintético sin BioHub ni sensor |

## Estructura
`EventTick` → `TickHeart(DT)` → `CacheBio` · si `bReady`: `PickHand` → `SenseHeart` → `HeartZoneFx` → `HeartBeatStep` · si no: `Acquire`.

| Función | Responsabilidad |
|---|---|
| `Acquire` / `FindHand(bRight)` | **copiadas de `BP_BreathManager_SC`**: cámara del pawn + SceneComponents `HandRight`/`HandLeft` por nombre. Sin cast al pawn. Imprime `HEART: listo` |
| `CacheBio` | `GetActorOfClass` + cast a `BP_BioHub`, una sola vez (se auto-gatea con `bBioOk`) |
| `SenseHeart(DT)` | geometría cámara→mano (`GeomHoriz`/`GeomVDrop`) y los dos timers (`ZoneTimer`/`OutTimer`), sin ramas |
| `HeartZoneFx(DT)` | histéresis del umbral, decaimiento de `BeatEnv`, zumbido continuo en la mano activa y apagado limpio en el flanco |
| `HeartBeatStep(DT)` | el reloj: `BeatTimer += DT`, y al cruzar `60/(BPM/BeatDiv)` emite |
| `ReadBPM` | escribe `HeartBPM` sin tocar un `BioRef` nulo (un `select` puro **evaluaría las dos ramas** y tiraría `Accessed None`) |
| `BeatFeedback` | `PulseHaptic` + `SpawnSoundAttached` a la mano |

## Enchufe en un nivel nuevo
1. Copiar `Mechanics/Heart/`. Depende de `BP_BioHub`, `GrabHapticEffect` y el sonido (las tres, perillas reemplazables).
2. Pawn con `CameraComponent` y SceneComponents `HandRight`/`HandLeft`.
3. Colocar **un** `BP_BioHub` (con `bFakeSignal` si no hay sensor) y **un** `BP_HeartManager_SC`.
4. PIE: tiene que salir `HEART: listo` una vez.

## ⚠ Para probar en ESCRITORIO
En PIE sin gafas la mano queda a la altura de la cámara y la zona del pecho **nunca abre**. Poner `HeartVDropMin = 0` en la instancia para ver el feedback (es la misma receta que ya estaba anotada para el sensor).

## Consumidor: `BP_PulseField_SC`
`bUseHeart` (`B - Ritmo`, true) hace que **el nacimiento de la ola cuelgue de `BeatCount`** en vez de la fase integrada: `BeatSrc = BeatCount` y el índice sigue siendo `floor(BeatSrc / BeatsPerWave)`. Con `BeatsPerWave` 2 → una ola cada 2 latidos, **exactamente sobre un latido**. En el nacimiento, `BirthFeedback` dispara un pulso háptico EXTRA (el latido de la ola se siente acentuado), también gateado por `bHeartZone`.

## Log
- **2026-09-19** — extraído. Compila. ⬜ PIE, ⬜ visor, ⬜ nivel sin guardar.


## 🔴🔴 2026-09-19 (2a) — EL UMBRAL ES QUIETUD + POSICIÓN
Beltrán, probando en gafas: *"ahora entra al umbral apenas acerco la mano. Como si solo estuviera determinado por posición. Acuérdate que el umbral está definido por quietud más posición."* Y la pregunta que duele: *"¿Dónde está todo eso anotado, acaso no existe?"*

**Sí existía — a medias, y ahí estuvo la falla.** La quietud está documentada en [[BP_BreathManager_SC]] y en `MECANICAS-PORTABLES.md` §4.7, pero **la ficha del latido (§4.8) documentaba solo la caja de posición**. El manager extraído nació sin quietud por copiar esa ficha en vez de la función. Ya está corregido en §4.8.

### Lo que ahora hace `SenseHeart` (portado de `BP_BreathManager_SC.SenseHand`, no reescrito)
```
k   = clamp(DT / StillTau)
lin = |GetLinearVelocity(mc)| ;  LinSpeed = max(lin, LinSpeed + (lin-LinSpeed)*k)
ang = |GetAngularVelocity(mc)| ; AngSpeed = max(ang, AngSpeed + (ang-AngSpeed)*k)
bQuiet = LinSpeed < StillLin  AND  AngSpeed < StillAng  AND  (los dos flags de tracking válido)
raw    = posición_en_caja  AND  bQuiet
```
🔑 El `max(v, ema)` es **ataque instantáneo y caída suave**: en cuanto movés el mando sale del umbral al toque, pero para volver a entrar tiene que quedarse quieto ~`StillTau`. Es lo que evita el parpadeo.

**Perillas nuevas en `A - Zona`:** `StillLin` 14 cm/s · `StillAng` 45 °/s · `StillTau` 0,3 — los valores afinados en visor de respiración. **Publicado nuevo:** `bQuiet`.

⚠ **`HandR`/`HandL` tuvieron que cambiar de tipo** a `MotionControllerComponent` (`/Script/HeadMountedDisplay.MotionControllerComponent`, NO `/Script/Engine.…`): las velocidades salen del MotionController, no de un SceneComponent cualquiera.

🧹 **`PickHand` se borró.** Elegía "la mano más cerca de la cámara en horizontal", que no es "la mano en el pecho" — un brazo colgando al costado también está cerca en horizontal, así que elegía la izquierda y medía la mano equivocada (síntoma: el umbral tardaba hasta 10 s y de forma errática). Ahora `SenseHeart` evalúa **las dos manos** en el mismo tick y elige **la que está dentro de la caja**. Con `bAutoHand = false` manda `bRightHand`.

👉 **La costura para la obra final** (pedido de Beltrán): la mano la va a fijar el momento en que el usuario toma el primer sensor. Ese sistema solo tiene que escribir **`bRightHand`** en el manager con `bAutoHand` en falso; el resto lo sigue solo.

### El método que faltó, y que es la lección real de la jornada
Tres entregas sin medir, y el bug se veía en UNA llamada: `ObjectTools.get_properties` sobre el actor del mundo de PIE (`/Game/UEDPIE_0_<Mapa>…`) **comparado contra el BP que ya funciona**. Regla: **antes de entregar una mecánica extraída, diffear sus refs cacheadas contra las del original.**
