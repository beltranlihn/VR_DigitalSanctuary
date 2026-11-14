# Variables de la mecánica de respiración — explicadas simple

Blueprint: `BP_BreathProbe`. Hay muchas variables, pero **solo un puñado las tienes que tocar para calibrar** (las marcadas con 🎛️). El resto son cálculos internos que el sistema usa solo — no las toques.

Valores entre paréntesis = lo que está puesto hoy (funcionando).

---

## 🎛️ Las que SÍ ajustas para calibrar (editables por instancia)

### Tamaño de la caja
| Variable | Qué hace | Valor |
|---|---|---|
| **ScaleMin** | Tamaño mínimo de la caja (exhalado). Es un multiplicador del tamaño con el que dibujaste la caja. 1.0 = tamaño original. | 1.0 |
| **ScaleMax** | Tamaño máximo (inhalado). 2.5 = dos veces y media el original. | 2.5 |
| **RiseTime** | Segundos que tarda la caja en ir de mínimo a máximo inhalando sin parar. | 5 |
| **FallTime** | Segundos que tarda en ir de máximo a mínimo exhalando. | 5 |

### Detección de la respiración (lo más delicado)
| Variable | Qué hace | Valor |
|---|---|---|
| **TurnFrac** | 🔑 **La más importante para calibrar.** Qué tan grande tiene que ser un cambio de dirección para que cuente como inhalar/exhalar. Alto = ignora el ruido pero puede perder respiraciones suaves. Bajo = capta todo pero rebota con cualquier temblor. | 0.25 |
| **MinExcursion** | El "piso" del umbral de giro: cuando tu señal viene débil, evita que el umbral se vuelva demasiado chico (ruido) o demasiado grande (no te toma). Si una sesión "no te toma", bajar esto ayuda. | 0.035 |
| **MinAmplitude** | Qué tan fuerte tiene que ser tu respiración para que el sistema diga "te estoy leyendo". Más bajo = entra con señal más débil. | 0.003 |

### Tiempos de entrada y salida
| Variable | Qué hace | Valor |
|---|---|---|
| **ActivateDelay** | Segundos que tienes que estar respirando bien antes de que se active el umbral. Más bajo = entra más rápido. | 0.5 |
| **DeactivateDelay** | Segundos fuera del umbral antes de que se apague (al sacar la mano). | 0.5 |
| **ArmDelay** | Al entrar, medio segundo de "armado" mientras el filtro se acomoda, antes de empezar a detectar dirección. Evita que arranque a moverse solo. | 0.5 |

### Quietud (distinguir respiración de mover el brazo)
| Variable | Qué hace | Valor |
|---|---|---|
| **StillLinThreshold** | Velocidad de la mano (cm/s) por encima de la cual se considera "te moviste, no es respiración". | 8 |
| **StillAngThreshold** | Igual pero para el giro de la mano (grados/s). | 25 |

### Háptico (vibración del mando)
| Variable | Qué hace | Valor |
|---|---|---|
| **HapticAmplitude** | Intensidad de la vibración cuando estás dentro del umbral. | 0.25 |

### Audio
| Variable | Qué hace | Valor |
|---|---|---|
| **AudioFadeTime** | Segundos de fade in/out de los sonidos. | 1 |

### Debug
| Variable | Qué hace | Valor |
|---|---|---|
| **bDebug** | Enciende/apaga los mensajes de log (`BP 6:`). | true |
| **DebugInterval** | Cada cuántos segundos escribe un mensaje de log. | 0.1 |

---

## ⚙️ Las que NO tocas (calibración fina, rara vez)

Estas afinan los filtros internos. Ya están bien; solo si algo específico falla.

| Variable | Qué hace |
|---|---|
| **TauSlow** (90) | Qué tan lento el filtro "olvida" la posición base de tu mano. Alto = aguantas la respiración más tiempo sin que se desincronice, pero tarda más en recuperarse si mueves la postura. |
| **TauFast** (0.4) | Qué tan rápido el filtro sigue la señal. |
| **TauAmp** (4) | Qué tan rápido mide la fuerza de tu respiración. |
| **TauMid** (10) | Filtro que centra la señal para medir bien la amplitud (arregla que la deriva no se confunda con respiración). |
| **StillTau** (0.3) | Suavizado de la medición de velocidad de la mano. |
| **ExcRiseAlpha** (0.4) / **ExcFallAlpha** (0.05) | Qué tan rápido aprende/olvida el tamaño de tu respiración. Sube rápido, baja lento (evita que un giro falso encoja el umbral). |
| **ReCenterLinThreshold** (4) / **TauSlowFast** (0.5) | Si mueves la postura, el filtro se re-centra rápido para no quedar ciego 90 segundos. |
| **AxisHystFrac** (0.3) / **AxisDwell** (4) | Del sistema viejo de auto-elegir eje. Hoy no se usan porque el eje va fijo (ver abajo). |
| **PhaseThreshFrac** / **DerivTau** | Muertas. De un detector viejo (por derivada). Ya no deciden nada. Ignóralas. |

---

## 🔧 Las que fijan cómo se lee el mando (setear una vez, no en cada sesión)

| Variable | Qué hace | Valor |
|---|---|---|
| **bLockAxis** | Fija el eje de lectura en vez de auto-elegirlo (auto-elegir causaba inversiones). | true |
| **LockedAxis** | Cuál de los 3 ejes del mando se lee (0/1/2). El 1 es el que funciona con el agarre actual. | 1 |
| **bInvert** | Invierte el signo de la señal (si inhalar achicara en vez de agrandar). Está calibrado PARA el eje 1. | true |

---

## 🚫 Las que NO son configuración — son la memoria interna del sistema

Estas las escribe y lee el código solo, frame a frame. **Nunca las toques.** Las listo solo para que sepas que no son perillas:

- **Estado del filtro:** `SlowV`, `FastV`, `AmpV`, `MidV`, `BreathV`, `BreathValue`, `Amplitude`, `PrevBreathValue`, `DBreath`
- **Detección de dirección:** `Phase` (+1 inhalar / −1 exhalar / 0 indeterminado), `RunMax`, `RunMin`, `Excursion`, `ActiveAxis`, `PrevAxis`
- **Velocidades y quietud:** `LinSpeed`, `AngSpeed`, `bStill`, `bTracked`, `bInThreshold`, `bBreathing`, `bInit`
- **La caja:** `Level` (0 a 1, la posición actual de la caja), `BaseScale`
- **Temporizadores:** `InTimer`, `OutTimer`, `ArmTimer`, `AxisDwellTimer`, `DebugTimer`
- **Referencias:** `MCRef` (el mando), `SensorRef` (el cubo sensor)
- **Audio interno:** `LastAudioPhase`, `bLastAudioBreathing`

---

## Si una sesión "no te toma bien" — guía rápida

1. **Primero: acomoda el mando.** La superficie plana bien apoyada y firme contra la barriga. Es la palanca más grande — la señal varía mucho según la posición.
2. Si sigue flojo: mira el log. Si el valor `Exc` es chico (< 0.03) y `Dlt` es más de la mitad de `Exc`, el umbral está muy alto para esa señal → **baja `MinExcursion`**.
3. Si **rebota** (empieza a exhalar y vuelve a inflarse solo): **sube `TurnFrac`**.
4. Si **tarda en entrar** al umbral: **baja `ActivateDelay`**.

> ⚠️ Ojo con la tensión: `TurnFrac` alto arregla los rebotes pero puede hacer que sesiones con señal débil "no te tomen". No hay un número perfecto para todas las sesiones — depende de qué tan fuerte venga tu señal ese día.
