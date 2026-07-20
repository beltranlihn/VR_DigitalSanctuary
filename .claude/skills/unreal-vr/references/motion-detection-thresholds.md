# Detección de movimientos sutiles (IMU/pose) — filtros y umbrales

Guía de referencia para aislar oscilaciones diminutas (respiración por inclinación de un mando VR apoyado en el abdomen, ~1°, 0.1-0.3 Hz) del ruido de tracking y del movimiento voluntario. Pensada para reconstruir el detector con pocos nodos de Blueprint.

**Clasificación de fuentes en cada sección:**
- **(A)** fuente académica/oficial citable con URL.
- **(B)** principio estándar de DSP/control, bien conocido, sin un único paper canónico que citar.
- **(C)** solo nuestra experiencia empírica en este proyecto (BP_BreathProbe) — no está validado en literatura, es lo que medimos que funciona o falla acá.

---

## (a) Tabla rápida: tipo de umbral → cuándo usarlo → trampa

| Umbral | Cuándo usarlo | Trampa |
|---|---|---|
| **Simple absoluto** | Señal ya limpia, separación grande entre estados | Parpadea (chatter) si la señal ronda el umbral; no sirve solo, cerca del borde |
| **Histéresis / Schmitt** | Cualquier decisión binaria sobre señal ruidosa (¿está respirando?) | Los dos umbrales mal elegidos (muy juntos) no evitan el parpadeo; muy separados añaden retraso |
| **Debounce temporal** | Filtrar transitorios cortos (glitch de tracking, un frame de pérdida) | Si `N` es muy chico no filtra nada; si es muy grande añade latencia perceptible al feedback |
| **Dwell (tiempo mínimo en estado)** | Evitar que el estado cambie más rápido de lo fisiológicamente posible (inhalar↔exhalar) | Confundir dwell con debounce: dwell bloquea *salidas* tempranas del estado ya confirmado, debounce filtra la *entrada* |
| **Adaptativo (escala con ruido/amplitud)** | Sensores/usuarios con amplitud de señal variable, piso de ruido que cambia con la sesión | Si la ventana de estimación de ruido es muy corta, el propio umbral se agranda cuando aparece la señal real (se adapta al evento y deja de detectarlo) |
| **Peak/turning point (ZigZag, delta)** | Contar ciclos, segmentar inhalar/exhalar, medir amplitud pico a pico | `delta` fijo falla si la amplitud de la señal cambia (ver adaptativo); sensible a mínimos/máximos espurios si no hay filtro previo |

Regla general **(B)**: ningún umbral solo resuelve el problema — la práctica estándar en detección de eventos sobre señales ruidosas es **componer** filtro (quita ruido de alta frecuencia) + histéresis (decide sin parpadear) + debounce/dwell (impone tiempos mínimos fisiológicos). Cada capa cubre el fallo de la anterior.

---

## (b) Filtros para señales lentas y débiles

### EMA / low-pass simple **(B)**
```
alpha = clamp(DT / tau, 0, 1)
ema = ema + alpha * (x - ema)
```
`tau` es la constante de tiempo: cuánto tarda el filtro en seguir un escalón (~63% en un `tau`, ~95% en 3×`tau`). Criterio de elección: **tau debe ser menor que el período de la señal que quieres seguir y mayor que el período del ruido que quieres rechazar.** Para 0.1-0.3 Hz (período 3.3-10 s), un `tau` de ~0.5-1 s dejaria pasar la respiración pero atenúa jitter de tracking (que típicamente es de decenas de Hz). Es un pasa-bajos de un polo: atenúa todo por encima de `fc = 1/(2π·tau)`, incluida cualquier componente lenta no deseada (deriva postural) — **no** distingue "respiración" de "deriva lenta de postura", ambas están debajo de la misma `fc`. Por eso solo no alcanza.

### Media móvil (moving average) **(B)**
Promedio de las últimas N muestras. Equivalente aproximado a un low-pass de fase lineal (sin distorsión de fase, a diferencia del EMA) pero requiere guardar un buffer de N muestras — más caro en nodos/memoria que un EMA de un solo estado. Para 0.2 Hz a un tickrate de ~90 Hz (VR), una ventana de ~2-3 s ya son 180-270 muestras. En Blueprint el EMA (1 variable, 1 resta, 1 multiplicación, 1 suma) es más barato que mantener y promediar un buffer circular de ese tamaño — por eso preferimos EMA.

### Band-pass = FastEMA − SlowEMA **(B, aplicado por nosotros — nuestra elección validada empíricamente, C)**
```
fast = fast + clamp(DT/tauFast,0,1) * (x - fast)   // sigue la respiración y el ruido
slow = slow + clamp(DT/tauSlow,0,1) * (x - slow)   // sigue solo la deriva lenta (postura)
band = fast - slow                                  // oscilación centrada en 0
```
Es la forma estándar de aislar una banda de frecuencia con recursos mínimos: un low-pass de corte alto (`tauFast` corto, dentro de la banda de interés) menos un low-pass de corte bajo (`tauSlow` largo, por debajo de la banda de interés) es matemáticamente una **aproximación de band-pass** (diferencia de dos pasa-bajos = pasa-banda cuando los cortes están bien separados) — el mismo principio que un ecualizador gráfico o un detector de envolvente en audio construyen con "diferencia de promedios móviles". Criterio de tau: `tauFast` ~ 1-2 s (deja pasar 0.1-0.3 Hz con poco retraso), `tauSlow` ~ 15-30 s (mucho más lento que el ciclo respiratorio más lento que interesa, para no comerse la propia respiración dentro de la "línea de base").

### One-Euro Filter **(A)**
Fuente: Casiez, Roussel & Vogel (2012), *"1€ Filter: A Simple Speed-based Low-pass Filter for Noisy Input in Interactive Systems"*, CHI 2012. PDF: https://gery.casiez.net/publications/CHI2012-casiez.pdf — repo de referencia: https://github.com/casiez/OneEuroFilter

Fórmulas (verificadas contra el paper y la implementación de referencia):
```
// low-pass exponencial estándar, parametrizado por frecuencia de corte fc
alpha(fc, dt) = 1 / (1 + tau/dt),  tau = 1/(2*pi*fc)
xHat_i = alpha * x_i + (1-alpha) * xHat_(i-1)

// la "velocidad" (derivada) se filtra aparte con un corte fijo (dcutoff, default 1 Hz)
dx_i = (x_i - xHat_(i-1)) / dt
dxHat_i = lowpass(dx_i, alpha(dcutoff, dt))

// el corte de la señal principal se adapta a la velocidad filtrada
fc = mincutoff + beta * |dxHat_i|
```
Idea: a velocidad baja usa `mincutoff` (filtra fuerte, quita jitter); a velocidad alta sube el corte (`beta` controla cuánto), reduce el retraso (lag) para seguir movimientos rápidos e intencionales. Tuning: bajar `mincutoff` reduce el jitter en reposo; subir `beta` reduce el lag en movimiento.

**Por qué NO reemplaza directamente a nuestro band-pass:** el One-Euro está diseñado para que la señal **responda más rápido cuando el usuario se mueve rápido** (ideal para un puntero o una mano que agarra algo). En nuestro caso es **al revés**: cuando el sensor se mueve rápido (brazo voluntario) queremos **rechazar**, no seguir más rápido. Además el One-Euro es un pasa-bajos puro — no quita la deriva de baseline (postura), solo el jitter de alta frecuencia. Sirve como reemplazo del *FastEMA* (denoising previo, con la ventaja de autoajustar el tau según cuánto se mueve el sensor, un parámetro menos que tunear a mano), pero **la resta contra una línea de base lenta (el `SlowEMA`) sigue haciendo falta** para quitar la deriva DC. Ver conclusión en la respuesta corta.

---

## (c) Catálogo de umbrales — pseudocódigo

### Umbral simple absoluto **(B)**
Resuelve: decisión binaria cuando la separación entre estados es grande y estable.
Trampa: parpadea si la señal oscila alrededor del valor.
```
isActive = abs(signal) > K
```

### Histéresis / Schmitt trigger **(A: circuito eléctrico estándar — Schmitt 1938; aquí aplicado por analogía a software, B)**
Dos umbrales: uno para *entrar* al estado, otro (más laxo) para *salir*. El hueco entre ambos ("hysteresis gap") es lo que evita que ruido cerca de un único umbral produzca transiciones falsas repetidas.
```
if not isBreathing and abs(signal) > HIGH:
    isBreathing = true
elif isBreathing and abs(signal) < LOW:   // LOW < HIGH
    isBreathing = false
```
Trampa: el gap (`HIGH - LOW`) debe ser mayor que la amplitud pico-a-pico del ruido residual tras el filtro, si no, no elimina el parpadeo — solo lo hace menos frecuente.

### Debounce temporal **(B — patrón estándar de switch debouncing, aplicado a señal continua)**
Exige que la condición se sostenga N segundos antes de aceptar el cambio de estado (filtra transitorios cortos: un frame de pérdida de tracking, un pico de jitter).
```
if condition: pendingTimer += DT else: pendingTimer = 0
if pendingTimer > DEBOUNCE_TIME:
    confirmedState = condition
```
Trampa: introduce latencia de detección igual a `DEBOUNCE_TIME`; si el evento a detectar (ej. inhalar) dura menos que eso, nunca se confirma.

### Dwell (tiempo mínimo en el estado) **(C — nuestra formalización; patrón estándar en state machines de UI, B)**
Distinto de debounce: el debounce filtra la *entrada* a un estado nuevo; el dwell bloquea la *salida* de un estado ya confirmado hasta que pasó un mínimo fisiológico razonable (ej. un ciclo respiratorio no dura menos de ~1 s).
```
timeInState += DT
if newStateRequested != currentState and timeInState > MIN_DWELL:
    currentState = newStateRequested
    timeInState = 0
```
Trampa: si `MIN_DWELL` es mayor que la duración real más corta del evento (ej. una respiración rápida y superficial), el sistema no puede seguir el ritmo real del usuario.

### Umbral adaptativo (escala con ruido/amplitud) **(B, con análogo académico directo en A: ver MAD saccade)**
En vez de una constante fija, el umbral se recalcula en vivo a partir de una medida robusta del ruido de fondo o de la amplitud de la señal reciente.
```
noiseFloor = runningStd(recentSamples)          // o MAD, ver (d)
threshold = K * noiseFloor                      // K típico 2-4 (equivalente a "N sigma")
isSignal = abs(signal) > threshold
```
Fuente académica análoga **(A)**: *"MAD saccade: statistically robust saccade threshold estimation via the median absolute deviation"* — PMC7881893, https://pmc.ncbi.nlm.nih.gov/articles/PMC7881893/. Usa MAD para fijar un umbral de velocidad que se adapta al ruido de fondo del eye-tracker, exactamente el mismo problema estructural que separar respiración de jitter de tracking.
Trampa: si la ventana de estimación del ruido incluye la señal real (respiración), el umbral "se come" el propio evento que debía detectar — la ventana de estimación de ruido debe excluir o ser insensible a la señal de interés (ej. estimarla sobre el residuo de alta frecuencia, no sobre la señal band-pass completa).

### Peak / turning point detection (ZigZag, con `delta`) **(B — "turning point algorithm", estándar en series temporales y en indicadores técnicos de trading)**
Lleva un máximo y un mínimo corridos; cuando la señal se revierte más de `delta` desde el extremo corriente, confirma un punto de giro y cambia de estado.
```
if direction == UP:
    runningMax = max(runningMax, signal)
    if signal < runningMax - delta:
        confirmPeak(runningMax); direction = DOWN; runningMin = signal
else:
    runningMin = min(runningMin, signal)
    if signal > runningMin + delta:
        confirmTrough(runningMin); direction = UP; runningMax = signal
```
Trampa: `delta` fijo falla si la amplitud de la respiración cambia (respiración superficial vs profunda) — igual que el umbral simple, conviene derivarlo de la amplitud medida en vivo (sección d), típicamente `delta = 0.3-0.5 × amplitudReciente`.

---

## (d) Estimar amplitud/energía de una oscilación en vivo (sin FFT)

Cuatro técnicas, de más simple a más robusta **(B, principios estándar de detección de envolvente en DSP/audio)**:

| Técnica | Fórmula | Robustez |
|---|---|---|
| EMA del valor absoluto | `envelope = envelope + alpha*(abs(band) - envelope)` | Simple, pero sensible a outliers puntuales (un pico de jitter infla la estimación un rato) |
| Envelope follower (ataque rápido / caída lenta) | `alpha = alphaAttack if abs(x)>envelope else alphaRelease` | Sigue picos rápido y decae lento — estándar en compresores de audio; buen compromiso |
| RMS corrido | `msq = msq + alpha*(x*x - msq); rms = sqrt(msq)` | Mide energía, no amplitud pico; menos sensible a un solo outlier que el valor absoluto porque pondera todo el historial vía el filtro |
| Running peak-to-peak (del ZigZag) | `p2p = ultimoMax - ultimoMin` (de la sección c) | Más robusto para fijar el `delta` del propio ZigZag porque usa la misma métrica que consume; pero solo se actualiza en cada punto de giro, no cada frame (más lento en converger) |

**Recomendación para umbral adaptativo del detector de respiración:** envelope follower con ataque rápido/caída lenta sobre `abs(band)` — es la más barata en nodos (1 estado, comparación + 2 alphas) y la que mejor sigue una amplitud que crece y decae en pocos ciclos (a diferencia de RMS corrido, que promedia más historia y reacciona más lento a un cambio real de amplitud).

---

## (e) Deriva DC (baseline wander) — por qué aparece y cómo quitarla

**Por qué aparece (B + C):** un mando apoyado sobre el abdomen mide inclinación absoluta. Cualquier cambio de postura (reclinarse, ajustar el mando, tensión abdominal sostenida) desplaza el ángulo base sobre el que oscila la respiración — el "cero" de la señal se mueve. En electrocardiografía el fenómeno equivalente (**baseline wander**) es atribuido a impedancia de contacto variable, artefactos de movimiento y **la propia respiración cuando se mide otra señal** — es ruido de muy baja frecuencia (0.05-3 Hz) que se superpone a la señal de interés **(A)**: comparativa de métodos en *"Baseline wander removal methods for ECG signals: A comparative study"*, arXiv:1807.11359, https://arxiv.org/pdf/1807.11359v1. Nuestra experiencia empírica **(C)**: sin quitar esta deriva, cualquier umbral de amplitud mide la deriva postural, no la respiración — es exactamente el síntoma que sufrimos antes de introducir el `SlowEMA`.

**Técnicas estándar (B, con ejemplo académico A):**
- **High-pass filtering**: recorta todo por debajo de una `fc` (ej. 0.05-0.1 Hz para no comerse la respiración lenta). Riesgo documentado en la literatura de ECG: puede deformar la morfología de la señal e introducir un retraso de fase — por eso conviene un corte bien por debajo de la banda de interés.
- **Detrending**: estima una tendencia global/local y la resta explícitamente, en vez de filtrar en frecuencia.
- **Median baseline**: usa una mediana (o media móvil) sobre una ventana suficientemente larga como línea de base y la resta. Ejemplo concreto de esta técnica aplicada a respiración por IMU **(A)**: *"An IMU-Based Wearable System for Respiratory Rate Estimation"*, PMC9970135, https://pmc.ncbi.nlm.nih.gov/articles/PMC9970135/ — "the baseline is computed by means of the moving average on 97 samples for each quaternion component and subtracted to them to remove the residual non-breathing movement".
- **Nuestra solución (C, equivalente funcional a las anteriores):** el `SlowEMA` con `tau` largo *es* un high-pass/detrending de un polo — restarlo (`FastEMA - SlowEMA`) es matemáticamente la misma operación que "moving average como baseline, restado", solo que con un filtro exponencial en vez de una ventana rectangular. Cumple el mismo rol que documenta la literatura de respiración por IMU, con menos memoria (1 estado en vez de un buffer de 97 muestras).

---

## (f) Separar respiración (0.1-0.3 Hz) de movimiento voluntario del brazo

**Criterio estándar (B):** combinar banda de frecuencia + energía/velocidad. La respiración por inclinación postural es lenta y de amplitud pequeña (grados); mover el brazo es rápido (componentes de alta frecuencia, por encima de la banda de respiración) y grande (amplitud/velocidad angular órdenes de magnitud mayor). Dos señales redundantes y baratas de calcular:
1. **Umbral de velocidad/quietud absoluto** — ya aplicado por nosotros **(C)**: `abs(velocidadAngular) < X` para considerar "sensor quieto" (solo respirando, no gesticulando). Es el filtro más barato y el más directo, porque no depende de la banda de frecuencia — corta el movimiento voluntario en la fuente, antes de que contamine el band-pass.
2. **Energía fuera de banda** (si el umbral de velocidad no alcanza): comparar la energía del `FastEMA` (o de la señal cruda) contra la energía del `band` — si la señal cruda tiene mucha más energía que la banda de respiración esperada, es movimiento, no respiración.

**Por qué no basta con el band-pass solo (C):** un movimiento de brazo rápido tiene componentes de baja frecuencia también (el gesto empieza y termina, hay una componente lenta en su envolvente) — el band-pass solo no lo rechaza del todo, por eso el umbral de quietud absoluto sobre la velocidad cruda (antes de filtrar) es la defensa primaria, y el band-pass/histéresis es la defensa secundaria sobre lo que ya pasó el filtro de quietud.

---

## (g) Inhalar vs exhalar (dos estados)

Tres enfoques documentados, con ventajas/desventajas **(B, principios estándar de detección de fase en señales cuasi-periódicas; el paper de PMC9970135 usa distancia entre picos, que es la variante peak-based de este mismo criterio, A)**:

| Método | Cómo | Ventaja | Desventaja |
|---|---|---|---|
| **Signo de la pendiente filtrada** | `dSignal/dt` (sobre la señal ya band-pass, nunca sobre la cruda — ver sección siguiente) `> 0` → inhalando, `< 0` → exhalando | Reacciona inmediatamente, sin esperar a un extremo | Muy sensible a ruido residual cerca de los extremos (donde la pendiente es casi cero) → parpadeo; necesita histéresis sobre la propia pendiente |
| **Cruce por cero** | La señal band-pass (centrada en 0) cruza de negativo a positivo → un evento; de positivo a negativo → el otro | Simple, barato (una comparación) | Marca el punto medio del ciclo, no el extremo — no distingue "empezando a inhalar" de "a mitad de inhalar" tan bien como el turning point |
| **Turning points (ZigZag de la sección c)** | El máximo confirmado = fin de inhalar/inicio de exhalar; el mínimo confirmado = viceversa | Es el método más robusto al ruido porque exige una reversión de magnitud `delta`, no solo un cambio de signo | Tiene latencia estructural: por definición solo confirma el giro *después* de que la señal ya se revirtió `delta` — no es instantáneo |

**Recomendación:** turning points (ya implementado, sección c) para la detección robusta de ciclo completo y conteo; si se necesita el estado "inhalando/exhalando" con mínima latencia frame a frame, combinarlo con el signo de la pendiente del `band` (no de la señal cruda — derivar la señal cruda reintroduce el ruido de alta frecuencia que el band-pass existe para quitar, ver razón en la sección siguiente).

---

## Por qué band-pass y no derivada — razón para no derivar la señal cruda

**(B, hecho estándar de teoría de sistemas/DSP):** un diferenciador ideal tiene respuesta en frecuencia `H(jω) = jω` — la magnitud crece linealmente con la frecuencia. Esto significa que **cualquier ruido de alta frecuencia se amplifica proporcionalmente a su frecuencia**, mientras que la señal lenta de interés (0.1-0.3 Hz) apenas se amplifica. El jitter de tracking, que vive en frecuencias mucho más altas que la respiración, queda **más fuerte que la señal útil** después de derivar — es la razón formal detrás de lo que sufrimos empíricamente **(C)**: derivar la señal cruda del mando produjo una salida dominada por ruido, inutilizable para detectar pendiente.

**La forma estándar de aislar una banda de frecuencia es filtrar en esa banda antes de cualquier operación que amplifique frecuencias fuera de ella** (derivada incluida) — de ahí que el pipeline correcto sea: cruda → band-pass (quita tanto la deriva DC como el ruido de alta frecuencia) → recién ahí, si hace falta, derivar o tomar el signo de la pendiente sobre la señal ya limpia.

---

## Receta mínima para el detector (resumen accionable)

1. `FastEMA` (tau ~1-2s) y `SlowEMA` (tau ~15-30s) sobre la inclinación cruda → `band = Fast - Slow` (quita jitter de alta frecuencia y deriva DC en una sola resta).
2. Umbral de quietud absoluto sobre la **velocidad angular cruda** (no la filtrada) → gatea todo lo demás; si no está quieto, no evaluar respiración.
3. Envelope follower (ataque rápido/caída lenta) sobre `abs(band)` → estima amplitud en vivo → alimenta el `delta` del ZigZag y/o el umbral adaptativo.
4. Histéresis (dos umbrales, no uno) sobre `abs(band)` vs el envelope → decide "¿está respirando?" sin parpadear.
5. ZigZag/turning points con `delta` derivado del envelope → confirma inhalar/exhalar y cuenta ciclos; opcionalmente cruzado con el signo de `band` para latencia mínima frame a frame.
6. Reseed de `FastEMA`/`SlowEMA` al valor actual cuando se pierde tracking o hay un salto grande (evita que el escalón se propague como falso pico) — ya aplicado, mantenerlo.
