# Plan de reconstrucción del Blueprint de respiración

**Objetivo:** rearmar la mecánica desde cero, limpia, paso a paso, probando cada etapa antes de seguir. Meta: ~20-25 variables en vez de 64, mucho menos nodos, fácil de configurar. Sin perder ninguno de los arreglos que nos costaron sangre hoy.

**Método:** duplicar `BP_BreathProbe` → dejar el original como **backup/referencia** (el proyecto no tiene git, así que el duplicado ES nuestra red). Construir uno nuevo limpio (sugerencia de nombre: `BP_BreathChannel`). Cuando necesitemos una pieza que ya funciona, la copiamos del viejo. Cada etapa: construir → probar en visor → dejar ✅ → recién ahí seguir.

---

## 1. Análisis de lo construido hoy

### ✅ Lo que está CORRECTO y se mantiene (no reinventar)
- **La fuente de señal: la inclinación del mando** (componentes Z de sus ejes, respecto de la gravedad). Validado hoy: es exactamente lo que usan los wearables médicos de respiración. El acelerómetro sería peor y ni siquiera es accesible en Quest.
- **Band-pass** (resta de dos filtros) para centrar la señal en cero → de ahí sale "hacia dónde va".
- **Detección por puntos de retorno (ZigZag)** → dos estados, inhalar/exhalar. Es el corazón, funciona.
- **Caja de dos estados con `FInterpToConstant`** (la función `UpdateLevel`): objetivo A/B interpolado a velocidad constante. Quedó limpia, una sola función. **Se copia tal cual.**
- **Separar en dos capas**: detección (produce `Phase`) vs comportamiento de la caja (consume `Phase`). Mantener esa separación.

### 🟢 La GRAN simplificación posible (el corazón de por qué serán pocas variables)
**Fijar el eje de lectura convierte TODO de vectores a números sueltos.** Hoy `SlowV/FastV/BreathV/MidV/AmpV` son vectores de 3 componentes (uno por eje) porque el sistema auto-elegía el eje. Si el eje va fijo (`LockedAxis=1`), trabajamos con **una sola componente** → esas 5 variables pasan de vector a `float`, y **desaparece todo el sistema de auto-selección de eje** (`ActiveAxis`, `PrevAxis`, `AxisHystFrac`, `AxisDwell`, `AxisDwellTimer` + su lógica de nodos). Esto solo ya borra ~8 variables y un tercio de los nodos.

### 🗑️ Grasa que se borra sin más (no hace nada)
- `PhaseThreshFrac`, `DerivTau`, `DBreath` — del detector viejo por derivada. Muertas.
- `PrevBreathValue` — de un cálculo que ya no existe.
- Todo el bloque de auto-selección de eje (ver arriba).

### 🟡 Simplificaciones a DECIDIR mañana (tienen un trade-off)
- **`Excursion` + `ExcRiseAlpha` + `ExcFallAlpha`** (aprende el tamaño de tu respiración para el umbral de giro). Propuesta: **borrarlas y usar directamente `Amplitude`** —que ya medimos— para el umbral (`delta = Amplitude * TurnFrac`). Menos variables, mismo efecto. Probar que funcione igual.
- **`TauSlow=90` + re-centrado adaptativo (`ReCenterLinThreshold`, `TauSlowFast`)**: el tau alto sirve para aguantar la respiración sin desincronizar, pero obliga al re-centrado adaptativo para no quedar ciego al mover la postura. Alternativa: **bajar `TauSlow` a ~20-30** → el re-centrado adaptativo deja de hacer falta (se borra), a cambio de que aguantar la respiración muchos segundos sea menos estable. Decidir según cuánto importa el aguante largo.

### 🔴 Complejidad que SE GANÓ SU LUGAR — NO borrar ingenuamente (o volvemos al bug)
Estas parecen de más pero cada una arregla un bug real que ya sufrimos. Copiarlas al nuevo BP:
1. **Reseed:** si el mando NO está quieto o NO trackeado → poner el filtro en el valor actual y señal en 0. Sin esto, apoyar el mando en la mesa se lee como respiración 45 segundos. (bug test 1)
2. **Usar los booleanos de retorno de `GetLinearVelocity`/`GetAngularVelocity` (`bTracked`)**, no solo el valor. Un mando dormido devuelve velocidad congelada que pasa el test de quietud. (test 1)
3. **Quietud con ataque rápido:** `LinSpeed = max(instantáneo, EMA)`. Sin esto, glitch al agarrar. (test 2)
4. **Centrar la señal antes de medir amplitud** (`Mid` = EMA de la señal; amplitud = EMA de `|señal − Mid|`). Sin esto, la amplitud mide la deriva y el sistema se queda sordo a mitad de sesión. (test 13)
5. **Ventana de armado (`ArmDelay`):** al entrar, ~0.5 s de espera antes de detectar dirección. Sin esto, la caja arranca a moverse sola. (test 10)
6. **Fase = 0 (neutro) al entrar/reseed:** no asumir dirección hasta ver el primer giro real. (test 7, 23)
7. **La lógica de giro NO va envuelta en `if Fase>=0`:** ese fue el bug que clavaba la fase en −1. El giro-a-inhalación tiene que ser alcanzable estando en −1. (test 22 — el más traicionero)
8. **Debounce de entrada/salida** (`ActivateDelay`/`DeactivateDelay`): evita el parpadeo del umbral.

---

## 2. El plan por etapas (tu estructura)

### Etapa 1 — Reconocer el umbral + háptico
**Construir:** leer inclinación del eje fijo → band-pass (scalar) → amplitud centrada. Quietud (`LinSpeed`, `AngSpeed` vs umbrales) + tracking. `bBreathing` = quieto Y trackeado Y amplitud ≥ mínimo, con debounce. Háptico continuo mientras `bBreathing`.
**Incluir sí o sí:** reseed (#1), bTracked (#2), ataque rápido (#3), centrado (#4), debounce (#8).
**Probar:** entrar al umbral → háptico arranca; sacar la mano → háptico para; repetir varias veces, entrando y saliendo. Con print de `bBreathing`, `Amplitude`, `bStill`, `bTracked`.
**Variables de esta etapa (~12):** config: `StillLinThreshold`, `StillAngThreshold`, `MinAmplitude`, `ActivateDelay`, `DeactivateDelay`, `HapticAmplitude`, `StillTau`, `TauSlow`, `TauFast`, `TauAmp` · estado: `Slow`, `Fast`, `Breath`, `Mid`, `Amp`, `LinSpeed`, `AngSpeed`, `bStill`, `bTracked`, `bBreathing`, `InTimer`, `OutTimer`, `bInit`, `MCRef`, `SensorRef`.
**✅ Check antes de seguir.**

### Etapa 2 — Reconocer inhalar / exhalar (las dos flechas)
**Construir:** sobre la señal centrada, el ZigZag: llevar `RunMax`/`RunMin`, y cuando la señal se revierte `delta` desde el extremo → cambiar `Phase` (+1/−1). `delta = Amplitude * TurnFrac` (con un piso `MinExcursion`).
**Incluir sí o sí:** armado (#5), Fase=0 al entrar (#6), y **la lógica de giro correcta, no envuelta en `if Fase>=0`** (#7).
**Probar:** print de `Phase`. Inhalar → `Phase=+1` y se mantiene; exhalar → `Phase=−1` y se mantiene; aguantar → mantiene el estado; no debe rebotar ni invertirse. Esta es tu "flecha hacia un lado / flecha hacia el otro".
**Variables que suma (~5):** `Phase`, `RunMax`, `RunMin`, `ArmTimer`, `TurnFrac`, `MinExcursion` (config). (Si NO borramos Excursion: +3.)
**✅ Check antes de seguir.**

### Etapa 3 — La caja (o lo que sea después)
**Construir:** copiar `UpdateLevel` tal cual del viejo (ya está limpia): inhalando→objetivo máximo, exhalando→mínimo, Fase=0→congela, fuera de umbral→base; `FInterpToConstant` a velocidad constante.
**Probar:** la caja crece/achica suave siguiendo los estados.
**Variables que suma (~4):** `Level`, `BaseScale`, `RiseTime`, `FallTime`, `ScaleMin`, `ScaleMax`.
**✅ Check. Y agregar el audio (ya funciona, se copia).**

---

## 3. Resultado esperado
- **~22-26 variables** en vez de 64, casi todas con un propósito claro.
- Un tercio menos de nodos (fuera el sistema de ejes y los vectores).
- Configurable de verdad: las ~8 perillas que importan, sin ruido alrededor.
- **Cero pérdida de robustez:** los 8 arreglos ganados van copiados desde el primer paso.

## 4. El gremlin que NO resuelve la reconstrucción (tenerlo presente)
La señal varía 2-4× entre sesiones según cómo se apoye el mando. Ningún reordenamiento de nodos arregla eso; es físico. Lo que SÍ podemos hacer mañana, si quieres: que el umbral de giro se **auto-calibre** con la fuerza de señal medida al entrar, para no depender de adivinar `TurnFrac`/`MinExcursion` cada sesión. Lo dejamos como opción de la Etapa 2.
