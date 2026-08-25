# BP_Sensor_Soul — el sensor que se toma con la mano hábil y CONTIENE las mecánicas (Core/Sensor/)

> `/Game/SoulCharger/Core/Sensor/BP_Sensor_Soul` · creado 2026-08-19 · **una instancia** en `MapsV2/L_SoulCharger` (`Sensor_Soul`, en **50/0/100**).
> **Estado: 🟡 modos + cableado con el director + fase de práctica verificados en PIE por log (2026-08-24, cero `Accessed None`); las mecánicas reales (respirar, latir, apuntar) necesitan visor.**

## Qué es
El sensor único de la versión limpia: **se toma UNA vez en el Hall** (esfera de 10 cm, **la mano con la que se toma define la mano hábil** — `bTookRight`; el salto de debug siembra la derecha) y **contiene TODAS las mecánicas de interacción de las etapas**, activadas por sala (decisión de Beltrán: *"contener todo el código de interacción en BP_Sensor_Soul y corregir desde ahí"*).

## 🔴 DECISIÓN 2026-08-24 (pivote de Beltrán): SIN sistema de calibración
> *"No vamos a hacer ningún sistema de calibración… ya tenemos unos valores bases. El usuario lee las instrucciones y parte a controlar la esfera con su respiración, siempre que esté dentro del umbral."*

- El **levantamiento de datos** vive aparte (el packaging de `Calibration/`); cuando haya datos suficientes, Beltrán los trae y **ahí** se afinan los valores del umbral.
- El umbral usa la **zona BASE** (`bZonePre`), **sin** `CalDist` por usuario. 🔬 **2026-08-24 (tarde): la zona salió del ANÁLISIS DE LOS 14 USUARIOS de la Quest** (`docs/ANALISIS-CALIBRACION-2026-08-24.md`): **`SafeHorizMax` 23 · `SafeVDropMin` 33 · `SafeVDropMax` 63 · `ActivateDelay` 1.5 s** (entrada al umbral más lenta — el reclamo de "reconoció demasiado rápido con la mano al aire"). Cobertura del estómago ≥99.7% y rechazo de la pierna 100% en los 11 usuarios válidos; `StillLin` 8 / `StillAng` 25 / `MinAmplitude` 0.003 confirmados por los datos. Escritos en CDO **y** en la instancia.
- La maquinaria de calibración quedó **DORMIDA, no borrada** (`BreathCalib`, `bCalibrated`, `CalDist/CalTimer/CalHold/CalGap/CalCooldown`, `bZonePost`, y la barra `CalibBar` del widget con su cadena `SetCalibProgress`): `BreathGate` la puentea llamando directo a `BreathThreshold`. Cuando vuelva la calibración con datos, se reconecta ahí.
- **El cierre de etapa es SOLO por tiempo** (*"la etapa tiene una duración definida"*): `CountBreaths` y `HeartBeatStep` **ya no llaman `MechDone`** — cuentan y loguean, nada más. `MechDone`/`OnMechDone`/`bMechDone` quedan dormidos (el gancho para cuando un cierre por mecánica vuelva a existir).

## 🎛️ El sistema de MODOS
- **`SetStage(StageIndex)`** (lo llama [[BP_Director_Story]]): guarda `Mode`, resetea el estado por-modo **y `bPractice`**, y prende/apaga el beam (`BeamMesh` visible sólo en modo 4).
- **`bPractice`** (lo escribe el director): la fase de **práctica** de Entering — el umbral corre durante las instrucciones y mueve el **círculo del widget**, pero la esfera del mundo ([[BP_BreathOrb_SC]]) espera. `StartStepTime` re-llama `SetStage(1)` → práctica off → la esfera aparece.
- **`TickMech(DT)`** (Tick): corre con `bTaken` && `!bMechDone` && pawn válido; despacha 1→`TickBreath` · 2→`TickHeart` · 4→`TickBeam` (if/elif — el `switch int` del DSL no acepta el case 4, §211).

| Mode | Sala | Mecánica |
|---|---|---|
| −1 / 0 | reposo / Hall | nada |
| **1** | Entering | **respiración por umbral** (base, sin calibración). Se arma **al mostrarse las instrucciones** (`ArmPractice`, con `bPractice=true`) y sigue toda la etapa. |
| **2** | Recognizing | **latido** al BPM del BioHub en zona de pecho (base). |
| 3 | Loving | nada (pasiva) |
| **4** | Attracting | **beam** desde el Aim de la mano hábil. |
| 5 | Surrounding | ⬜ stub (dibujo 3D = integrar `BP_DrawCanvas`, pendiente) |

## 🌬️ Modo 1 — respiración (los valores efectivos del CDO afinado de `BP_BreathSensor_V2`)
`TickBreath(DT)` → `BreathGate` (puente) → `BreathThreshold` → `BreathHaptic` → `DetectDir` → `CountBreaths`:
1. **Quietud**: velocidades del grip de la **mano hábil** (EMA ataque-rápido/caída-lenta, `StillTau` 0.3) → `bQuiet` = LinSpeed<8 && AngSpeed<25 && trackeado.
2. **Geometría** (`HeadGeom`): cámara del pawn vs `Body` → `GeomHoriz`/`GeomVDrop`/`SensDist`.
3. **Señal**: `Right.Z` del grip (LockedAxis=1 de V2). Band-pass `FastV`(τ 0.4) − `SlowV`(τ 20, el valor EFECTIVO del CDO — no el 90 del tracker viejo). Sin quietud → reseed.
4. **Umbral** (`BreathThreshold`): `_in = bQuiet && (bBreathing || bZonePre) && Amplitude ≥ MinAmplitude 0.003`, con debounce **1.5 s de entrada** / 0.5 s de salida → `bBreathing` + logs `UMBRAL IN/OUT` + **`Pulse()` en el flanco IN**.
5. **Háptico del umbral** (`BreathHaptic`): zumbido continuo (`SetHapticsbyValue`, `HapticAmp` 0.25 — el valor de V2, knob de CDO **no** instance-editable) en la mano hábil mientras `bBreathing`; apagado limpio en el flanco de salida. 🔴 Reescrito tras §213: el estado `bWasBreathing` se actualiza **dentro del flanco**, no antes (un `bind` de getter puro no es snapshot).
6. **ZigZag** (`DetectDir`): señal = `BreathV × (derecha ? +1 : −1)`, delta = `Amplitude × DirFrac 0.3` → `bInhaling`.
7. **Conteo** (`CountBreaths`): sostenidas de `InhaleHold` 4 s → `BreathCount` + pulso + log. **No cierra nada.**

### 🎚️🔴 `BreathLevel` v6 — LA SEÑAL ES EL DESPLAZAMIENTO, NO LA INCLINACIÓN (2026-08-24, cierre)
Beltrán, tras 3 iteraciones fallidas: *"no siento nada conectado el sensor con la esfera"*. Se midió con **label de verdad-terreno**: él apretaba el gatillo al inhalar y lo soltaba al exhalar, 51 s a 72 Hz. Veredicto: **la inclinación del mando (`bv`) NO discrimina** (AUC 0.587 = azar) — el problema nunca fue el mapeo, era la **entrada**. Detalle completo: Parte 3 de `docs/ANALISIS-CALIBRACION-2026-08-24.md`.

- **La señal buena es `GeomHoriz`** (distancia horizontal cabeza→sensor): al inhalar la panza **empuja el sensor hacia afuera**. AUC **0.837** en la corrida de Beltrán y **0.990 mediana en los 11 usuarios** de calibración, con **el mismo signo en 10/11** → **señal universal, sin calibración ni seed de signo**. La inclinación funcionaba en el prop de calibración (agarre fijo) pero no en la esfera pegada al grip (agarre arbitrario).
- **`UpdateLevel` v6**: `S = EMA(GeomHoriz,0.4) − EMA(GeomHoriz,HorizTau 3)` (reseed si no hay quietud) → `nivel = 0.5 + 0.5·x/(1+|x|)`, `x = S/GainK 0.5` (centímetros) → `FInterpTo(LevelFollow 5)`. El band-pass de 3 s **elimina la deriva postural por construcción**.
- Parámetros elegidos con los datos: `HorizTau` 3 s (barrido 2-8, AUC 0.997) · `GainK` 0.5 cm (recorrido 0.18↔0.81 en el usuario mediano, 0.70 en el más suave, nadie clavado).
- **Dormidas** (no borradas): `SeedTheSign`/`SeedSign`/`bSignSeeded` · `Baseline`/`PinT`/`PinTau`/`PinThr`/`PinDwell` · `EnvHi`/`EnvLo`/`EnvTau`/`MinSpan` · `NormK` · `SigTau` · `SignAcc`. `bFlipSign` queda como escape manual. `bv`/ZigZag: solo conteo por log.
- 🧪 **Instrumentación** (apagar al validar, ambas en el CDO): `bDebugBreath` → `BLOG,t,lb,bv,ss,bl,lvl,sg,zn,qt,br,h,v,ls,as` cada frame, con **`lb` = gatillo como label** (eventos `IA_Shoot_*` + `IMC_MenuTrigger` con la receta del picker, en `EnsureInput`/`MaybeInput`); `bDebugOrb` → `OLOG,t,sc,rv`. Analizadores en `scratchpad/quest/analyze_{label,transform,geom,gain}.py`.
- ✅ **Validado en visor por Beltrán** (*"ahora sí, mucho mejor"*). Ajustes de cierre de esa pasada:
  - **El UMBRAL también pasó a la señal buena**: la compuerta de amplitud usaba `Amplitude` (EMA de la inclinación = ruido). Ahora es `HAmp` = EMA(|HorizBP|, `TauAmp` 4) contra **`MinHAmp` 0.02 cm**.
  - 🐛 **`MinHAmp` nació en 0.12 y bloqueó el umbral POR COMPLETO** (Beltrán: *"nunca entró"*). Error de extrapolación: 0.12 salió de las amplitudes de la calibración (0.5-4 cm de recorrido pico a pico), pero `HAmp` es **el EMA del valor absoluto**, un estadístico mucho menor — medido en vivo: mediana 0.09-0.38. ✅ **El valor final se eligió SIMULANDO la máquina del umbral sobre las 3 corridas reales del log** (`scratchpad/quest/sim_threshold.py`): con 0.12 → *nunca abre*; con 0.02 → abre y queda abierto 50-78 % del tiempo. 👉 Regla: **un umbral sobre un estadístico derivado se fija midiendo ESE estadístico en vivo, nunca extrapolando del crudo.**
  - 🔴 **Estructura final del umbral (v3, elegida por simulación):** `_in = zonePre && (bBreathing || (quiet && HAmp ≥ MinHAmp))` — **entrar** exige zona + quietud + respiración real; **quedarse** exige sólo zona. Así moverse o mirar alrededor ya no desconecta (sólo sacar la mano de la panza), y un sostén largo tampoco tira el umbral. Medido sobre las corridas reales: sube el tiempo conectado de 64 %→78 % (corrida buena) y de 23 %→50 % (corrida con mucho movimiento). Mientras no hay quietud el band-pass se resetea, así que el nivel vuelve suave al neutro sin perder la conexión.
  - **Los visuales volvieron a gatear por `bBreathing`** (no por `bZonePre`): Beltrán reportó que reaccionaban *antes* del pulso háptico. Ahora visual y háptica entran juntos, y el freeze que motivó el cambio anterior ya no aplica porque el umbral es estable con la señal nueva.
- 🔴 **Lección**: tres iteraciones afinando el mapeo de una señal que no contenía la información. **Ante "no se siente conectado", medir primero si la ENTRADA discrimina** — con un label del usuario real, en su contexto real.

## ❤️ Modo 2 — latido (completado 2026-08-25 para la etapa Recognizing)
`TickHeart` → zona de pecho base (`HeartHorizMax` 25, `HeartVDrop` 10-45, a ojo — afinar en visor) con debounce (`ActivateDelay` 1.5 de entrada, salida instantánea) → **`HeartZoneFx(DT)`** (nueva, corre siempre en modo 2) → si en zona: `HeartBeatStep`: intervalo `60/(HeartSmooth/BeatDiv 2)` del [[BP_BioHub]] (fake LFO ya late) → `Pulse` + `OnBeatPulse` + **`BeatEnv=1`** + **audio `HeartBeatSound` (SpawnSoundAttached al `Body`)** + conteo. **No cierra nada** — el cierre de Recognizing lo hace [[BP_Elevator_SC]] por distancia.

**`HeartZoneFx`** (el feedback del umbral, patrón calcado de `BreathHaptic`):
1. `bHeartZone` = `bBioOk && ZoneTimer ≥ ActivateDelay` — **la bool pública del umbral** (la leen el director para el círculo del widget y quien haga falta).
2. `BeatEnv` decae con `FInterpTo(→0, BeatEnvDecay 2.5)` — el **envelope del latido** (salta a 1 en cada beat): el círculo de la página escala con esto.
3. Zumbido continuo en la mano hábil mientras `bHeartZone`, con apagado limpio en el flanco de salida (`bWasHeartZone` actualizado DENTRO del flanco, §213). 🆕 **2026-08-25: la amplitud LATE — `lerp(HapticAmp 0.25, 1.0, BeatEnv)`**: en cada latido la vibración salta a tope y decae con el envelope. Fue el fix del reporte de Beltrán *"falta el pulso fuerte"*: el `PlayHapticEffect` del `Pulse()` quedaba pisado porque `SetHapticsByValue` se re-aplica CADA TICK en zona (comparten canal) — en vez de pelear canales, el pulso viaja EN el zumbido.

⚠ La salida de zona es instantánea (sin `DeactivateDelay`): si en visor el zumbido parpadea al borde de la zona, agregar el debounce de salida como en breath.
⚠ Consumidores de `OnBeatPulse`: [[BP_Elevator_SC]] (el kick del ascensor).

## 🔦 Modo 4 — beam
`TickBeam`: trace Visibility desde el Aim de la mano hábil (`TraceDistance` 800) → publica `bBeamHit`/`BeamHitLoc` → estira `BeamMesh` (cilindro, `M_Beam_SC` unlit, NoCollision) del inicio al impacto. Visible sólo en modo 4.

## Registro de variables (además de las de la toma)
| Cat | Variables | Rol |
|---|---|---|
| C - Breath (knobs por instancia) | `TauSlow` 20 · `TauFast` 0.4 · `TauAmp` 4 · `MinAmplitude` 0.003 · `StillLin` 8 · `StillAng` 25 · `StillTau` 0.3 · `SafeTol` 9 · **`SafeHorizMax` 23 · `SafeVDropMin` 33 · `SafeVDropMax` 63** · `CalHold` 4.5 · `CalGap` 2 · **`ActivateDelay` 1.5** · `DeactivateDelay` 0.5 · `DirFrac` 0.3 · `InhaleHold` 4 · `MaxBreaths` 5 | zona y delay del análisis 2026-08-24 (`docs/ANALISIS-CALIBRACION-2026-08-24.md`); los `Cal*`/`SafeTol` hoy dormidos. `HapticAmp` 0.25 = knob de CDO (no editable, §212) |
| D - Heart | `BeatDiv` 2 · `HeartHorizMax` 25 · `HeartVDropMin` 10 · `HeartVDropMax` 45 · `MaxBeats` 15 · 🆕 `BeatEnvDecay` 2.5 · 🆕 `HeartBeatSound` = `Core/Audio/Sounds/HeartBeat` | `MaxBeats` hoy sin efecto (no cierra). Los 2 nuevos son **knobs de CDO, no instance-editable** (a propósito, §212). 🧪 Truco de PIE sin visor: `HeartVDropMin=0` en la instancia abre la zona con la mano de escritorio (VDrop=0). |
| E - Beam | `TraceDistance` 800 · `BeamRadius` 0.6 | |
| Z - Estado | `Mode` −1 · `bPractice` · `bMechDone`(dormida) · `bQuiet` · `bZonePre/Post` · filtros (`SlowV/FastV/BreathV/Amplitude/RunExtreme`) · `bCalibrated`/`CalDist`/`CalTimer`/`CalCooldown` (dormidas) · `InTimer/OutTimer` · `bBreathing`/`bInhaling`/`bWasBreathing`/`InhaleTimer`/`bHoldCounted`/`BreathCount` · `ZoneTimer/BeatTimer/BeatCount/bBioOk/BioRef` · `bBeamHit/BeamHitLoc` · `GeomHoriz/GeomVDrop/SensDist` · `HandRef/AimRef` · `bPendingRight` | |

🔴 **Los 25 knobs están escritos en la INSTANCIA del nivel** (§212: nacieron en 0 pese al CDO). Si se repone el actor, recargarlos.

## La toma (2026-08-19, intacta) + reintento
`Body`+`Twin` (`MI_Sensor`, NoCollision), detección por distancia², `Appear()`, `Take(Right)` → attach + sonido + háptica + `OnTaken`. `Take` sin pawn **se reintenta solo** cada 0.5 s (`RetryTake` + `bPendingRight`) — arregló la siembra de `DebugStartRoom` (pawn tardío).

## Verificado por log (2026-08-24, PIE `DebugStartRoom=1` + autotest)
- Práctica: `SetStage 1` + `bPractice=true` al mostrarse el panel (medido en la instancia PIE) → la esfera espera (`RevealT=0`).
- Paso: `SetStage 1` (práctica off) → **`ORB: true`** → 10 s → `SetStage -1` → **`ORB: false`**. Ciclo de salas intacto, **cero `Accessed None`**.
- ⚠ Lo que PIE no prueba: respirar de verdad (umbral/zona con el sensor en la panza), el zumbido, el círculo moviéndose — **visor**.

## Trampas pagadas acá
§210 (`get_node_type_pins` instancia un nodo sonda) · §211 (`Equal(Name)` no escribible → `==`; `switch int` sin case 4) · §212 (knobs instance-editable nacen en 0 en la instancia ya colocada) · **§213 (un `bind` de getter puro NO es snapshot — el patrón de flanco correcto actualiza el estado dentro del flanco)** · los literales bool/string a funciones propias se pierden (usar `:keyword` + variables) · el setter cross-class de una VARIABLE lleva el valor primero (`(Class|X|SetVar :self ref :pin valor)`) · `MotionControllerComponent` = `/Script/HeadMountedDisplay.` · en CDO de componentes: `bVisible` y `{"BodyInstance":{"CollisionEnabled":...}}`.

## TODO
- [ ] 🔴 **Visor**: umbral con el sensor en la panza (zona base, sin calibrar), zumbido + pulso del IN, círculo de práctica en la página 2, esfera al terminar instrucciones, y el beam en Attracting.
- [ ] Cuando lleguen los **datos del levantamiento**: definir los valores seguros del umbral (y decidir si vuelve la calibración por usuario — la maquinaria dormida está lista).
- [ ] Modo 5 (dibujo 3D) · visual real del beam · consumidores de `OnBeatPulse`.
