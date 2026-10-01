# BP_HeartManager_SC — el latido PORTABLE (Mechanics/Heart/)

> `/Game/SoulCharger/Mechanics/Heart/BP_HeartManager_SC` · creado 2026-09-19 · **una instancia** en `/Game/TestMeshes` (`Galeria/_Sistema`).
> Pedido de Beltrán: *"en esta estación vas a quitar la respiración y traer la mecánica de ritmo cardíaco, en la que el usuario tiene que poner el control en su corazón y cuando reconozca que está en el umbral de quietud va a generar un pulso háptico con cada ritmo cardíaco y con cada nacimiento de la ola, y además emitir el sonido de pulso"*.
> Es el **paso 4 del plan de extracción** de [`docs/MECANICAS-PORTABLES.md`](../../../../docs/MECANICAS-PORTABLES.md) §4.8.
> **Estado: 🟢 PIE ok (2026-09-29, en `Test_Heart` con la membrana) · 🟢 contrato de etapa en PIE (2026-09-30). ⬜ SIN visor.**

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


## 🧪 2026-09-21 — `bIgnoreTracking`: el umbral se puede probar en PIE con el robot
**El problema, medido:** `bQuiet` terminaba en `… AND (bValidLin AND bValidAng)` — los bools de validez del tracking. En PIE no hay runtime XR, esos bools son `false`, y **el umbral no abría nunca** por más que la geometría fuera perfecta.

🔑 **Lo que NO era el problema:** la velocidad. En PIE `GetLinearVelocity` devuelve **0**, que se lee como *quieto* — exactamente lo que el umbral pide. Y `GeomHoriz`/`GeomVDrop` salen de **posiciones de mundo**, que el robot controla. Como dijo Beltrán: *"finalmente la mecánica es de posición y movimiento"*.

✅ **El cambio, de un nodo:**
```
bQuiet = velocidadesQuietas AND (trackingVálido OR bIgnoreTracking)
```
- **`bIgnoreTracking`** (bool, instance-editable, default **false**). En gafas el comportamiento es **idéntico** (el bool de validez es true, y `x OR false` = `x`).
- 🔴 **Lo prende el robot en RUNTIME** ([[BP_Robot]] rutinas 4 y 6), no el nivel → no puede quedar prendida por olvido.
- **Se conservó la protección a propósito**: si un mando se queda sin batería en la instalación, el bool de validez sigue cerrando el umbral en vez de dejar que una posición fantasma abra la zona.

✅ **Verificado en PIE** con el robot moviendo la mano: el umbral abre, la señal oscila y los consumidores reaccionan. Detalle y números en [[BP_Robot]].

## 🚶 Contrato TOUR (2026-09-29, pedido de Narrativa para `Test_Recorrido`)
`Test_Recorrido` carga `Test_Heart` entero con `LoadLevelInstance`, así que el manager no puede arrancar solo en las etapas que no le tocan.
- **`BeginPlay`**: si `GetAllActorsWithTag("TOUR")` devuelve algo → `TourSleep`.
- **`TourSleep()`** (pública, sin parámetros, idempotente): `SetActorTickEnabled(false)`, `bHeartZone`/`bWasHeartZone` = false, `BeatEnv` 0, `ZoneTimer` 0, `BeatTimer` 9999, y háptica 0 en las dos manos (guardado por `IsValid` del PlayerController). Dormido no hay latidos, ni háptica, ni sonido, ni `OnHeartBeat`. El pawn no se toca.
- **`TourWake()`** (pública, sin parámetros, idempotente): `ZoneTimer` 0, `BeatTimer` 9999, `SetActorTickEnabled(true)`. Arranca como al empezar la etapa: el primer latido sale en cuanto se abre el umbral.
- Se eligió apagar el Tick y no un bool de estado: es el mínimo de nodos y no toca `TickHeart`.

## 🎬 Contrato de etapa de la Obra (2026-09-30, `docs/PLAN-NOCHE-2026-09-30.md`)
Narrativa creó los stubs vacíos; Heart los llenó. La etapa es RECOGNIZING.

| Función / variable | Qué hace |
|---|---|
| `StageIntro()` | `bStageDone` false · `TourSleep` (sin latidos durante las instrucciones) · `ScapeGo(1)`: la esfera brota del agua en `EntryTime` · print `HEART: StageIntro / SetSensorColor` (hueco para `BP_UserTool_SC.SetSensorColor(rojizo)` que construye Breath; lo conecta Narrativa) |
| `StageBegin()` | `bStageDone` false · `BeatCount` 0 · `TourWake`. El latido arranca cuando el usuario lleva el sensor al pecho (el umbral de siempre) |
| `bStageDone` | lo pone en true **`StageCheck()`** (en el Tick, después de `TickHeart`) cuando `BeatCount ≥ StageBeats`, y hace el print `HEART: bStageDone` |
| `StageBeats` (int, perilla, **38**; era 75 hasta el 2026-09-30 noche) | latidos hasta el fin: ~0:38 a 60 lpm, ~0:45 a 50 lpm (Beltrán pidió la mitad tras probar la Obra). Cortafuegos del director: 150 s |
| `StageOutro()` | `TourSleep` · `ScapeGo(−1)`: la esfera se hunde (≤ 3 s) · print `HEART: StageOutro / Release` (hueco para `BP_UserTool_SC.Release()`) |
| `bContractTest` (bool, perilla, **false**) | En true, en el test suelto: `BeginPlay` → dormido y sin esfera → 2 s → `StageIntro` → 8 s → `StageBegin` → `StageOutro` solo, al llegar a `bStageDone` |
| `ScapeGo(D)` | `GetActorOfClass(BP_HeartScape_SC)` → `IsValid` → `SphereGo(D)`. Sin membrana en el nivel no hace nada |

- **`BeginPlay`** (reescrito): si hay tag `TOUR` **o** `bContractTest` → `TourSleep` + `ScapeGo(0)` (esfera oculta; solo el mar con su oleaje) → si `bContractTest`, la secuencia con `Delay`.
- **`TourWake`** (reescrito por gotcha 99): además llama `ScapeGo(1)`, para que `Test_Recorrido`, que no usa el contrato, siga teniendo esfera.
  - En la Obra, Narrativa **no** llama `TourWake` a Heart: la celda se enciende sin él, `StageBegin` despierta y `StageOutro` duerme.
  - Al final de la etapa llama `TourSleep`, que es idempotente y no toca la esfera.
- ✅ **PIE (2026-09-30)**, con valores temporales ya restaurados (`bContractTest`, `bFakeBeat` 60, `StageBeats` 8, `HeartVDropMin` −100, `bIgnoreTracking`):
  - `StageIntro` a los 33,27 s → `StageBegin` a los 41,27 s.
  - `UMBRAL IN` → un latido cada 1,00 s, con un pulso visual por latido en la membrana.
  - 8 latidos → `bStageDone` + `StageOutro` a los 48,84 s → `EntryT` 0.
  - 0 `Accessed None`.
- 🔴 Trampa nueva del DSL: los **literales numéricos** pasados a una función PROPIA también se pierden, igual que los string de la §4 de `dsl.md`. `(CallFunction|ScapeGo 1.0)` y `-1.0` quedaron en 0.0. Se arreglaron con `set_pin_value` y se verificaron con `get_pin_value`.

## Uso en `Test_Heart` (2026-09-29)
Actor con label `HeartManager` (`BeatDiv` 1) + `BioHub`. Su consumidor es [[BP_HeartScape_SC]] (`Assign OnHeartBeat` en su `BeginPlay`). **Modo de prueba sin sensor: `bFakeBeat`** (E - Prueba), guardado en **false**. Para PIE de escritorio, además `HeartVDropMin` −100 y `bIgnoreTracking` true (guardados en 10 / false).
⚠ Sin verificar: con `bFakeBeat` false y sin OSC, si `HeartSmooth` de BioHub queda en 0, `ReadBPM` lo clampa a 30 lpm (un latido lento, no ausencia de latido).
- **2026-09-29** — ✅ primer PIE real: `HEART: listo`, `UMBRAL IN`, latido cada 1,0 s a 60 BPM, 0 `Accessed None`.

## 🫀 2026-09-30 noche (turno 2) — latido de respaldo + sensor rojizo (sesión Heart, aprobado por Narrativa)
- **Por qué:** sin mando en el pecho o sin sensor no hay latidos → ni pulsos ni lunas, y `StageBeats` nunca se cumple (callejón sin salida). El APK de postulación corre sin sensor y en autoplay.
- **`BeatBackup()`** (lo llama `StageCheck` al principio, en cada tick de la etapa despierta): si `BeatCount` no sube durante `BackupAfter` (perilla, **8 s**; **1 s** si `BioRef.bFakeSignal`) → `bForceZone` = true + `bBackupOn` + log `HEART: latido de respaldo`. `NoBeatT`/`BackupLastCount` (Z).
- **`BackupReset()`** (al final de `StageBegin` y de `StageOutro`): pone en cero el contador y, si el respaldo estaba prendido, apaga `bForceZone`.
- ✅ PIE con el runner del ensayo (TOUR): entró a los **8,0 s** del `StageBegin`, llegan latidos, `SpawnOrb` corre, 0 Accessed None. ⚠ Sin señal el BioHub publica 0 y `ReadBPM` clampa a **30 lpm** → 38 latidos ≈ 76 s.
- **Sensor rojizo** (hallazgo de Breath: nadie llamaba al UserTool): `StageIntro` → **`SensorTint()`** = `GetActorOfClass(BP_UserTool_SC)` → `SetSensorColor(SensorColor)` (perilla, **1 / 0,34 / 0,28**, el `colorGlow` de la paleta); `StageOutro` → **`SensorRelease()`** → `Release()`. Sin UserTool → log `HEART: sin UserTool` y sigue. ⚠ El read los rotula `Variables|Default|SetSensorColor`, pero `get_node_infos` confirma que son llamadas con `self` = BP_UserTool_SC. ⬜ Probado solo en Test_Heart (que no tiene UserTool); falta verlo en la Obra con `UserTool_Obra`.
- Agregados por CIRUGÍA (create_node + connect al final de cada función) para no reescribir `StageIntro`/`StageOutro` y perder el literal de `ScapeGo`.

## 🌀 2026-10-01 — la vuelta: disparo a mitad de etapa + la etapa espera que termine
- `OrbitAtBeat` (int, editable, **19** = mitad de 38; 0 = sin vuelta). Estado (`Z - Estado`): `bOrbitAsked`, `bOrbitDone`, `ScapeRef`.
- `StageCheck` reescrito (gotcha 99): `BeatBackup` → **`OrbitAsk`** (a `BeatCount ≥ OrbitAtBeat`, una vez: `ScapeRef = GetActorOfClass(scape)` → `OrbitGo`, log `HEART: empieza la vuelta`) → **`OrbitDoneCalc`** (`bOrbitDone` = sin pedir: `OrbitAtBeat ≤ 0`; pedida: `ScapeRef.OrbitT ≥ 1`, o true si no hay scape) → `bStageDone` solo si `BeatCount ≥ StageBeats` **y** `bOrbitDone`.
- `StageBegin` → al final **`OrbitRestart`** (flags en false + `OrbitReset` del scape).
- Tiempos: a 50 lpm la vuelta arranca a ~23 s y la etapa cierra a ~83 s (antes ~46 s); a 30 lpm (respaldo) ~38 s → ~98 s. ⬜ PIE y visor.

## 🌀 2026-10-01 (2) — la etapa espera también el regreso
- `OrbitDoneCalc` ahora compara `OrbitT ≥ 2.0` (antes `1.0`): la etapa cierra cuando terminó la vuelta **y** el regreso del mar (ver [BP_HeartScape_SC](BP_HeartScape_SC.md), "vuelta que se aleja y regresa").
- Tiempos: a 50 lpm la vuelta arranca en el latido 19 (~23 s); 60 s de vuelta + 20 s de regreso → la etapa cierra a **~103 s** (antes ~83 s). A 30 lpm (respaldo sin señal) la vuelta arranca a ~38 s → cierra a **~118 s**. ⬜ PIE y visor.
