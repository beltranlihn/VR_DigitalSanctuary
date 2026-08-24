# BP_Director_Movement — el recorrido de la versión limpia (Core/Movement/)

## Purpose
**Un solo BP que mueve el pawn por un spline, parada por parada**, con el efecto de caminata (bob vertical + giro acoplados a la cadencia del paso) y el loop de pasos. Vive en el nivel persistente **`L_SoulCharger`** (`MapsV2`).

Pedido de Beltrán (2026-08-17): *"un BP con un spline sobre el cual avanzará el Pawn. También controlará el efecto de caminata, el sonido de los pasos"* — y **nuevo y limpio**, no una modificación de lo anterior.

Es el sucesor limpio de [[BP_Journey]] + [[BP_Walker]] (que siguen vivos en el persistente viejo `L_Persistent`). **Acá recorrido y caminata son el mismo actor.**

## Status
🟢 **Verificado en PIE por log (2026-08-17)**: recorrido completo, las 4 duraciones medidas contra lo pedido, la cadena de audio completa (spawn → fade in → fade out → kill) y **cero `Accessed None`**. **Falta el test en visor** — el bob, el giro y la comodidad solo se juzgan con el visor puesto.

## 🔴 Cambio 2026-08-17: el primer tramo ATRAVIESA la parada 1 sin frenar
Pedido de Beltrán: *"el recorrido entre el punto 0 y el punto 2, justo a la entrada del hall, debe ser continuo. El punto de entremedio sólo marca dónde empieza el efecto de caminata"*. Ahí no hay cambio de música ni nada.

**Solución: un tramo puede abarcar más de una parada.** `LegSpan` dice cuántas claves del spline cubre el tramo en curso; con **`bMergeFirstLeg`** (true) el tramo 0 vale **2**, así que el pawn va de la parada 0 a la **2** en un solo smootherstep. La parada 1 queda en el spline, se sigue arrastrando en el viewport, pero **ya no frena ahí**.

🔴 **Por qué no se borró el punto, que era el plan original:** **`set_properties` no puede sacar un elemento del array del spline.** Medido dos veces: quitar un punto de `splineCurves.position.points` falla con *"ArrayRemove: elements changed alongside the size change"*, y si se cambia tamaño **y** valores en la misma llamada **devuelve `true` sin aplicar nada** — la escritura se va a un `TRASH_SplineComponent` y el spline queda intacto. **La única forma de detectarlo es releer.** Borrar un punto es trabajo del viewport; abarcarlo con `LegSpan` sale gratis y además conserva el punto como cosa arrastrable.

**Dónde toca `LegSpan`:** `UpdateLeg` (clave = `LegKeyBase + s · LegSpan`) y `FinishLeg` (snap y `LegIndex += LegSpan`, donde antes había un literal 1). Lo resuelve `ResolveLegSpan()` al empezar cada tramo.

⚠ **Consecuencia en los tiempos:** después del tramo 0 el índice salta a **2**, así que el tramo siguiente usa `TimeLeg2to3` y **`TimeLeg1to2` queda sin uso**. Hoy: `TimeLeg0to1` = 10 s (0→2, continuo) · `TimeLeg2to3` = 5 s (−773→0) · `TimeLegRest` = 8 s.

**Verificado en PIE (2026-08-17)**: `tramo 0 continuo` → efecto de caminata + Hall a los **5,00 s** (mitad exacta de 10) → **`llego a la parada 2`** a los 9,98 s, sin pasar por la 1. Tramos siguientes: 4,98 s y 7,98 s contra 5 y 8 pedidos. Cero `Accessed None`.

## El spline: 9 paradas (la 1 se atraviesa, ver arriba)
Componente **`Path`** (`SplineComponent`), puntos en **`CIM_Linear`**, actor en el **origen** (coordenada local = mundial). Paradas:

| Índice | X | Nota |
|---|---|---|
| 0 | −5000 | inicio — **coincide con el `PlayerStart`** del mapa |
| 1 | −2500 | fin del tramo sin efecto de caminata |
| 2 | −1000 | |
| 3 | 0 | |
| 4 | 1500 | |
| 5 | 3000 | |
| 6 | 4500 | |
| 7 | 6000 | |
| 8 | 7500 | última parada |

- **Se editan arrastrando los puntos en el viewport.** No hay Construction Script que reconstruya el spline, justamente para que arrastrar no se pierda al recompilar.
- 🔴 **Todo usa `GetLocationAtSplinePoint` / `GetLocationAtSplineInputKey` — NUNCA distancia a lo largo del spline.** Los puntos se escribieron por `set_properties` sobre `SplineCurves` del CDO y eso **no recalcula el `reparamTable`**. Misma regla que en [[BP_Journey]].
- 💡 **El largo del tramo ya no importa para el timing**: desde el cambio a duraciones, mover un punto cambia la *velocidad* del tramo, no su duración.

## Registro de variables

### A - Recorrido (instance-editable)
| Variable | Default | Rol |
|---|---|---|
| `TimeLeg0to1` | 14 s | 🔴 **Duración del tramo 0→1**, en segundos. |
| `TimeLeg1to2` | 9 s | Duración del tramo 1→2. |
| `TimeLeg2to3` | 6 s | Duración del tramo 2→3. |
| `TimeLegRest` | 9 s | Duración de **todos los tramos restantes** (3→4 en adelante). |
| `StartIndex` | 0 | Parada donde arranca. Cambiarlo a 4 = probar desde la mitad. |
| `bPlaceAtStartOnBeginPlay` | true | Coloca el pawn en `StartIndex` al empezar. Con 0 no se nota: el `PlayerStart` ya está ahí. |
| 🆕 `bMergeFirstLeg` | **true** | 🔴 **El primer tramo atraviesa la parada 1 sin frenar** y termina en la 2 (la boca del Hall). En false vuelve al comportamiento viejo, parada por parada. |

> 🔁 **Cambio 2026-08-17 (pedido de Beltrán):** antes era velocidad (cm/s) por tramo en un array; ahora son **cuatro variables con nombre**, en segundos. Es más directo para ajustar el ritmo y no depende del largo del tramo. La resolución vive en `LegDuration(Index)`: 0 → 1 → 2 → resto.

### B - Caminata (instance-editable) — todas se pueden poner en 0
| Variable | Default | Rol |
|---|---|---|
| `LegWalkIntensity` | **`[1, 1, 1, 0, 0, 0, 0, 0]`** | 🔴 **Intensidad del efecto por tramo.** El **0 de la primera entrada** es el pedido: del punto 0 al 1 no hay efecto **ni pasos**. Es float: 0,5 = medio efecto. Fuera de rango → `WalkIntensity` sola. |
| `WalkIntensity` | 1.0 | Multiplicador **global** encima del array. |
| `BobHeight` | 1.75 cm | Amplitud vertical del paso (rango del doc: 1,5–2). |
| `BobRollDeg` | 1.5 ° | Amplitud del vaivén lateral (rango del doc: 1–2). |
| `StepsPerSecond` | 1.8 | Cadencia del bob (≈108 pasos/min). |
| `FXAttack` | 0.5 s | 🔴 **En cuánto tiempo ENTRA el efecto** al arrancar el tramo. Más chico = entra más rápido. Es en **segundos absolutos**. |
| 🆕 `FXReleaseFrac` | **0.2** | 🔴 **En qué FRACCIÓN FINAL del tramo se apaga el efecto.** 0,2 = durante el último 20 % del tramo. **Reemplazó a `FXRelease`, que estaba en segundos absolutos** — ver abajo por qué. |

### 🐛 El bob seguía "caminando" después de llegar al Hall (2026-08-18)
Beltrán: *"La caminata hasta la entrada del hall está rara. Se mantiene con el efecto de caminata un buen rato luego de que ya llegó. En las otras ya no pasa."*

**La causa es aritmética, no un bug de estado** — nada corre después de `FinishLeg` (ahí `bWalking=false` y `UpdateLeg` deja de llamarse). Lo que pasa es que **el smootherstep tiene la cola plínima** y `FXRelease` estaba en **segundos absolutos**:

| t (fracción del tramo) | s (fracción del camino) |
|---|---|
| 0,80 | **94,2 %** |
| 0,90 | **99,1 %** |

Con `TimeLeg0to1 = 25 s`, el pawn **ya recorrió el 94 % a los 20 s** y se arrastra los últimos 5 s — pero el bob seguía a amplitud plena hasta 24,4 s (`Duration − 0,6`). En los tramos de 5 y 8 s esa misma cola dura 0,5–1,6 s y no se nota: por eso *"en las otras ya no pasa"*.

✅ **El arreglo:** el divisor pasó de `FXRelease` (segundos) a **`Max(FXReleaseFrac × Duration, 0.05)`**. Como la cola **es** una fracción fija del tramo, atarla a la fracción la sigue automáticamente: con 0,2 el efecto empieza a apagarse justo cuando arranca el arrastre (t = 0,8), en un tramo de 25 s **y** en uno de 8. Un solo número para todos.
⚠ El `Max(·, 0.05)` evita la división por cero cuando la instancia nace con la variable en 0 — que fue exactamente lo que pasó (gotcha §119). Sembrada en la instancia y verificada.

### 🟢 Prender/apagar el efecto por tramo: YA EXISTE, es `LegWalkIntensity`
No hacía falta variable nueva. **`LegWalkIntensity[i] = 0` apaga el tramo `i`**, y apaga también **los pasos**: `StartSteps` arranca con `if CurIntensity > 0`. Valores intermedios funcionan (0,5 = medio efecto).

✅ **Configuración vigente (pedido de Beltrán, 2026-08-18): caminata SOLO en la llegada al Hall y en la entrada al Hall.** Las 9 paradas del spline están en x = −5000 · −2500 · **−773 (boca del Hall)** · **0 (dentro del Hall)** · 1500 · 3000 · 4500 · 6000 · 7500, o sea tramos 0 a 7 y el array de 8 los cubre exacto.

| Tramo | Recorrido | Intensidad |
|---|---|---|
| 0 (fusionado) | −5000 → **−773, la boca del Hall** | **1** |
| 2 | −773 → **0, dentro del Hall** | **1** |
| 3 a 7 | de sala en sala | **0** — sin bob, sin giro y **sin pasos** |

⚠ **Ojo con el fallback**: `GetLegIntensity` devuelve `WalkIntensity` sola cuando el índice cae **fuera** del array — o sea **fuera de rango = caminata ENCENDIDA**. Si algún día se agregan paradas al spline, hay que alargar el array o los tramos nuevos vuelven a caminar solos.

🔴 **Cuidado con los ÍNDICES, que NO son "la caminata número N"** — con `bMergeFirstLeg = true` el índice salta:

| Caminata | `LegIndex` | Entrada del array | Duración que usa |
|---|---|---|---|
| 1ª (0 → boca del Hall) | 0 | `LegWalkIntensity[0]` | `TimeLeg0to1` |
| 2ª | **2** | `LegWalkIntensity[2]` | `TimeLeg2to3` |
| 3ª | 3 | `LegWalkIntensity[3]` | `TimeLegRest` |
| 4ª en adelante | 4, 5… | `[4]`, `[5]`… | `TimeLegRest` |

⚠ **`LegWalkIntensity[1]` no se usa nunca** mientras `bMergeFirstLeg` esté en true — el tramo 0 se come la parada 1.
⚠ **La viñeta NO se apaga con esto**: en `UpdateLeg` no está multiplicada por `CurIntensity`. Es deliberado — la viñeta es **confort** (anti-mareo) y el bob es estética; acoplarlas haría que apagar el efecto por gusto quite la protección del movimiento. Para sacarla hay `VignetteMax = 0` (global). Si se quiere por tramo, se dice y se agrega.
| 🆕 `WalkStartFrac` | **0.5** | 🔴 **En qué fracción del PRIMER tramo arranca el efecto de caminata** (2026-08-17). Sólo aplica al tramo 0; en el resto el efecto entra desde el principio. 0,5 = a mitad de camino. **A 0 el tramo 0 se comporta como cualquier otro.** Gobierna el bob, el giro **y** el loop de pasos — y también es **el disparo del Hall**: [[BP_Director_Rooms]] enciende la sala cuando esta compuerta se abre, así que caminata y luces empiezan en el mismo instante. |

> 🔁 **Cambio 2026-08-17 (pedido de Beltrán: *"al empezar a caminar toma mucho tiempo antes de dar el efecto"*):** antes la amplitud del bob seguía a `v`, la **velocidad normalizada del recorrido**, que arranca casi en cero y sube como `t²` — en un tramo de 9 s el efecto no llegaba al 50 % hasta pasado un segundo y medio. Ahora el efecto tiene **su propia envolvente en segundos**, independiente de la curva del movimiento:
> `env = clamp(Elapsed / FXAttack) · clamp((Duration − Elapsed) / FXRelease)`
> Esa `env` gobierna la amplitud **y la cadencia**, así que el ciclo de paso arranca a ritmo normal enseguida (que además es lo que hace el loop de audio) mientras el cuerpo todavía acelera suave. El movimiento en sí **no cambió**: sigue siendo smootherstep.

### C - Pasos (instance-editable)
| Variable | Default | Rol |
|---|---|---|
| `StepsSound` | `Pasos` | El sonido del caminar. Es un **loop** (`bLooping=true`, 6,49 s, stereo). Vacío = silencio, sin error. |
| `StepsVolume` | 1.0 | Volumen del loop. |
| `StepsFade` | 0.2 s | Fade **in** al arrancar el tramo. |
| `StepsFadeOut` | 0.1 s | Fade **out** al llegar — y también **cuándo muere el componente** (el kill se agenda a este mismo tiempo). Separado del fade in a pedido de Beltrán: la salida tiene que ser más rápida que la entrada. |

### D - Test (instance-editable)
| Variable | Default | Rol |
|---|---|---|
| `bDebugKey` | **true** | 🧪 **La tecla `1` avanza un tramo.** Se consulta en el Tick con `WasInputKeyJustPressed`: **no necesita Enhanced Input, ni IMC, ni `EnableInput`**. Apagarlo para la obra final. |
| `bAutoAdvance` | false | 🧪 Recorre las 9 paradas solo. Es el preview del recorrido completo, y es como se verifica por log. |
| `AutoPause` | 1.5 s | Pausa entre tramos en modo automático. |

### Z - Estado interno (no tocar)
`bWalking` · `LegIndex` (parada actual; el tramo va de `LegIndex` a `LegIndex+1`) · `LegKeyBase` (la misma parada en float, para que la clave del spline sea float+float) · `Elapsed` / `Duration` · `Phase` (grados, acumulada) · `CurIntensity` · `BaseRot` · `PawnRef` · `bStepsOn` (gatea el fade out para que dispare una sola vez) · `StepsComp` (el AudioComponent spawneado del tramo en curso).

⚠ **La categoría NO puede llevar paréntesis**: se vuelve parte del `type_id` del DSL (`Variables|Z-Estadointerno|GetX`) y un paréntesis rompe el parser. Por eso es "Z - Estado interno" y no "Z - Estado (no tocar)".

## Dispatchers
- **`OnArrived`** — al llegar a cada parada, con `LegIndex` ya actualizado. El gancho para el futuro director de etapas.
- **`OnRouteFinished`** — al llegar a la última parada.

## El audio de pasos: se spawnea y se mata en cada tramo
🔴 **Pedido explícito de Beltrán: no arrastrar memoria, y que el kill sea DESPUÉS del fade out para que no se sienta un corte duro.** No hay `AudioComponent` permanente en el actor (se probó y se quitó).

| Momento | Qué pasa |
|---|---|
| Arranca un tramo con intensidad > 0 | `StartSteps` → `SpawnSound2D(StepsSound, StepsVolume, bAutoDestroy=true)` → guarda el componente en `StepsComp` → `FadeIn(StepsFade, 1.0)` |
| Faltan `StepsFade` segundos para llegar | `TickStepsFade` → `StopSteps` → `FadeOut(StepsFade, 0)` **y** agenda `KillSteps` a `StepsFade` segundos |
| Terminó el fade | `KillSteps` → `DestroyComponent` si sigue vivo. En la práctica **el `bAutoDestroy` ya lo liberó** justo al terminar el fade, y el log lo dice. Los dos caminos coinciden: el sonido nunca se corta duro. |

- El fade out arranca **antes** de llegar (en `Duration − StepsFade`), así el silencio coincide con la detención en vez de arrastrarse después.
- **Sonido 2D, sin espacialización** — son los pasos del propio usuario. Es además lo correcto para Quest: una fuente espacializada tiene que ser mono y `Pasos` es stereo.
- En el tramo 0 (intensidad 0) **no se spawnea nada**: ni bob, ni giro, ni pasos.

## La viñeta vive ADENTRO de este BP (2026-08-17)
Decisión de Beltrán: *"esa viñeta solo se utiliza en caminata, así no separamos fuerzas"* + *"creá de nuevo ese sistema, usando lo aprendido del `BP_Vignette`, para que el original no lo toquemos"*.

- **Componente `Vignette`** (StaticMesh) en este BP: `/Engine/BasicShapes/Sphere` a escala 0,5 (radio 25 cm), sin sombras, `translucencySortPriority = 100`, sin decals — **la configuración exacta del `Dome` de [[BP_Vignette]]**, que ya está probada.
- **Material propio `Core/Movement/M_VignetteWalk`**, duplicado de `M_Vignette`. Así se puede retocar sin tocar el original. 🔴 **Lo que se hereda ahí es lo caro**: la máscara **geométrica** (correcta en estéreo) y sobre todo la **calibración `InnerCos`/`OuterCos` hecha CONTRA EL FOV REAL del visor** — con valores elegidos "a ojo" la viñeta queda literalmente invisible (la historia completa, con los cosenos y los ángulos, está en `blueprints/BP_Vignette.md`; **leerla antes de tocar esos dos parámetros**).
- **`SetupVignette()`** (desde `InitRoute`): apaga la colisión — 🔴 **una esfera alrededor de la cabeza bloquearía todos los line traces de los punteros** — y **attachea el componente a la cámara del pawn** con la receta probada de `BP_FadeSphere` (`GetComponentByClass(CameraComponent)` + `SnapToTarget`/`SnapToTarget`/`KeepWorld`). Loguea si el pawn no tiene cámara.
- **`ApplyVignette(Amount)`**: `SetScalarParameterValueOnMaterials(Vignette, "Amount", …)`. Sin variable MID.
### Las palancas (categoría **D - Viñeta**, todas instance-editable)
| Variable | Default | Qué ajusta |
|---|---|---|
| `VignetteMax` | 1.0 | **Intensidad**: cuán negro llega. **A 0 = sin viñeta.** |
| `VignetteFadeIn` | 0.6 s | En cuánto **entra** al arrancar el tramo. |
| `VignetteFadeOut` | 0.6 s | En cuánto **sale** antes de llegar. |
| `VignetteInnerDeg` | **14°** | Dónde **empieza** a oscurecer, medido desde el centro de la mirada. Más chico = ventana limpia más chica. |
| `VignetteOuterDeg` | **44°** | Dónde llega a **negro pleno**. Entre los dos está el degradado. |
| `VignetteWidth` | 1.0 | **Ancho** de la ventana limpia. >1 abre a los costados, <1 cierra. |
| `VignetteHeight` | 1.0 | **Alto** de la ventana limpia. |

🔴 **`Inner`/`Outer` se exponen en GRADOS, no en cosenos.** El material sigue trabajando en cosenos (es lo que hace la máscara correcta en estéreo), pero el BP convierte con `Cos(Degrees)` antes de escribir el parámetro. Es deliberado: elegir cosenos "a ojo" ya dejó una viñeta **invisible** una vez (`BP_Vignette.md`), y en grados el error no existe — 14° y 44° se comparan directo contra los ~55° de medio FOV del Quest 3.

🔴 **El ancho y el alto NO son la escala del mesh.** La máscara usa `LocalPosition`, que es **previo a la escala**, así que agrandar la esfera no cambia nada de lo que se ve. Estaban en el material, y hasta hoy **no existían**: la máscara era radialmente simétrica. Se agregaron a `M_VignetteWalk` dos parámetros (`WidthScale`/`HeightScale`) que dividen las componentes Y y Z de `LocalPosition` antes de sacar el coseno:
`cos' = x / |(x, y/Width, z/Height)|` — **con Width = Height = 1 el resultado es idéntico byte por byte al de antes**, así que la calibración validada sigue siendo el punto de partida.

**La envolvente**: `Amount = VignetteMax · clamp(Elapsed/FadeIn) · clamp((Duration−Elapsed)/FadeOut)`. Antes seguía a `v` (la velocidad del tramo); ahora tiene sus propios tiempos, a pedido de Beltrán (*"debe entrar suave, no duro"*), lo que además la vuelve predecible: entra, se queda en meseta, y sale.

**Cuándo se aplican**: la forma (`Inner`/`Outer`/`Width`/`Height`) se escribe en `SetupVignette` **y al empezar cada tramo** (`ApplyVignetteShape` desde `WalkLeg`) → tocar un valor en el editor se ve **en el tramo siguiente**, sin reiniciar. La intensidad se escribe cada tick, así que responde al instante.

🔴 **La viñeta NO sigue la envolvente del efecto ni `CurIntensity`: sigue `v`, la velocidad real del tramo** (`v = 16t²(1−t)²`). Es deliberado y es la diferencia que importa: el tramo 0 **no tiene bob pero sí se mueve**, así que necesita viñeta — de hecho es donde más se notaba el arrastre percibido al frenar. Atarla a la intensidad la habría apagado justo donde hace falta.

### 🐛 ✅ ARREGLADO: la viñeta no se veía — el componente en el actor colocado estaba VACÍO
Beltrán reportó *"no se ve la viñeta, me tinca que no se está attachando a la cabeza"*. El attach estaba **bien** (medido: el padre del componente era la `Camera` del pawn). El problema era otro: el actor del nivel se había colocado **antes** de que existiera el componente, así que su `Vignette` llegó **sin malla y sin material** (`staticMesh: None`, `overrideMaterials: []`, escala 1) — perfecto en el CDO, vacío en la instancia. Sin malla no hay nada que dibujar; y aun con malla, el material básico es de **una sola cara**, así que desde adentro de la esfera tampoco se vería.
⚠ `set_properties` sobre el componente de la instancia **no lo arregla**: aplica la malla y **descarta en silencio** material, escala y sort priority.
✅ **Fix: subir los overrides de la instancia al CDO y REPONER el actor** (`remove_from_scene` + `add_to_scene_from_asset`), que nace heredando todo. Por eso hoy el CDO tiene los valores afinados por Beltrán y no los míos de fábrica. Detalle en `gotchas.md` §111.
✅ **Verificado en runtime**: el MID `MID_M_VignetteWalk_0` existe colgado del componente y su parámetro `Amount` valía `0.0011` con `t = 0.9875` — exactamente `16t²(1−t)²`, o sea la viñeta se mueve con la velocidad real del tramo (§112 para el método).

⚠ **`BP_Vignette` y `M_Vignette` quedan intactos** (los sigue usando `BP_Walker` en el persistente viejo). Si algún día se recalibra uno, hay que recalibrar el otro: son dos copias de la misma calibración.

## Estructura de grafos

**`EventGraph`**
- `BeginPlay` → `SetTimerByFunctionName("Boot", 0.25)`. 🔴 **El retraso no es cosmético**: `BeginPlay` corre **antes** del `Possess`, así que un `GetPlayerPawn(0)` inmediato puede devolver null (`references/vr-pawn.md`).
- `Tick` → `TickDebugKey()`, y si `bWalking` → `UpdateLeg(DeltaSeconds)`.

**`Boot()`** → `InitRoute()` y, si `bAutoAdvance`, agenda el primer `GoToNext`.
**`InitRoute()`** → cachea el pawn, `LegIndex = StartIndex`, loguea, coloca al pawn si corresponde.

**`GoToNext()`** — 🔴 **el único punto de entrada del avance** (la tecla 1, el modo automático y mañana el director de etapas). Si no está caminando y queda parada por delante → `WalkLeg(LegIndex)`.

**`WalkLeg(Index)`** — `Duration = max(LegDuration(Index), 0.1)`, resetea `Elapsed`/`Phase`, resuelve `CurIntensity`, cachea pawn y `BaseRot`, **arma la compuerta del efecto** (`ArmFXGate`, que reemplazó al `StartSteps` directo) y prende `bWalking`.

**🆕 `ArmFXGate()` / `OpenFXGate()`** (2026-08-17) — la compuerta del efecto de caminata. `ArmFXGate` apaga `bFXStarted`, calcula `FXStartTime = WalkStartFrac · Duration` y, **si es el tramo 0**, agenda `OpenFXGate` a ese tiempo; en cualquier otro tramo pone `FXStartTime = 0` y abre en el acto. `OpenFXGate` prende `bFXStarted` y llama a `StartSteps`.
🔴 **`bFXStarted` es público a propósito**: es lo que lee [[BP_Director_Rooms]] para encender el Hall en el mismo instante en que arranca la caminata. Un solo número (`WalkStartFrac`) gobierna los dos.
💡 En `UpdateLeg` la envolvente del efecto pasó de `clamp(Elapsed/FXAttack)` a **`clamp((Elapsed − FXStartTime)/FXAttack)`** — un solo nodo de resta insertado por cirugía. Antes de la compuerta el numerador es negativo, el `Clamp` lo lleva a 0 y no hay ni bob, ni giro, ni avance de `Phase`.

**`LegDuration(Index)`** — cadena `if/elif`: 0 → `TimeLeg0to1`, 1 → `TimeLeg1to2`, 2 → `TimeLeg2to3`, resto → `TimeLegRest`.

**`UpdateLeg(DT)`** — el corazón, un tick:
1. `Elapsed += DT`; `t = clamp(Elapsed / Duration)`.
2. 🔴 **`s = 6t⁵ − 15t⁴ + 10t³` (smootherstep)** → la posición sale de `Path.GetLocationAtSplineInputKey(LegKeyBase + s)`.
   **Por qué smootherstep y no smoothstep** (cambio 2026-08-17, *"que se detenga por completo, pero que sea suave"*): el smoothstep de antes llegaba con velocidad cero pero **aceleración distinta de cero** → el arranque y la frenada tenían un tirón perceptible. El de 5º grado tiene **velocidad Y aceleración cero en los dos extremos**: es la salida y la llegada más suaves posibles sin cambiar la duración.
   🔴 **Tiempo normalizado, NO `FInterpTo`**: llega **exacto** en el tiempo pedido. El `FInterpTo` es asintótico y fue el bug del arrastre en [[BP_Walker]].
3. **`env = clamp((Elapsed−FXStartTime)/FXAttack) · clamp((Duration−Elapsed)/(FXReleaseFrac·Duration))`** — la envolvente del efecto, **en segundos y aparte de la curva del movimiento** (ver el cambio arriba).
4. `Phase += DT · StepsPerSecond · env · 360`.
5. `vert = sin(Phase) · BobHeight · CurIntensity · env` · `roll = sin(Phase/2) · BobRollDeg · CurIntensity · env`.
   🔴 **El vertical va al doble de frecuencia que el giro**: una bajada por pisada, un vaivén por zancada. Es la relación real de la marcha humana.
6. `ApplyVignette(v · VignetteMax)` — la viñeta sigue la **velocidad real**, no la envolvente del efecto (ver arriba).
7. `SetActorLocation(pawn, spline + (0,0,vert))` y `SetActorRotation(pawn, BaseRot + roll)`.
   🔴 **La yaw del pawn NO se toca.** Girar el mundo alrededor del usuario marea y el camino es recto.
8. `TickStepsFade()` y, si `t ≥ 1`, `FinishLeg()`.

**`FinishLeg()`** — apaga la caminata, corta los pasos, **hace snap a la parada exacta**, loguea, **recién ahí** actualiza `LegIndex`, dispara `OnArrived`, avisa si es el fin del recorrido y, en automático, agenda el tramo siguiente.
**`GoToStop(Index)`** — teleport a una parada, sin caminata.
**Auxiliares**: `GetStopLocation` · `GetLegIntensity` · `NotifyIfRouteEnd` · `StartSteps` / `StopSteps` / `TickStepsFade` / `KillSteps` · `TickDebugKey`.

## 🐛 ✅ ARREGLADO en la verificación (2026-08-17): el pawn saltaba UNA PARADA DE MÁS al llegar
El log decía **"llego a la parada 2"** al terminar el primer tramo, y era un bug **visible**: `FinishLeg` hacía `SetLegIndex(i)` **antes** del snap, y como `i` es la expresión pura `LegIndex + 1`, **se re-evalúa en cada consumidor** → el `SetActorLocation` posterior leía el índice ya actualizado y mandaba el pawn a la parada siguiente; el tramo nuevo lo traía de vuelta.

**Fix (cirugía de exec, sin reescribir el grafo):** `SetLegIndex` se movió al **final**, después del snap y del log.

👉 **Regla general:** en el DSL, `(bind x <expresión pura>)` **no cachea nada**. **Los `Set` van al final**, o el valor se guarda en una variable propia.

## Verificado en PIE por log (2026-08-17)

**Duraciones** — medidas contra las cuatro variables:

| Tramo | Variable | Pedido | Medido |
|---|---|---|---|
| 0 | `TimeLeg0to1` | 14 s | **13,98 s** |
| 1 | `TimeLeg1to2` | 9 s | **8,98 s** |
| 2 | `TimeLeg2to3` | 6 s | **6,01 s** |
| 3 | `TimeLegRest` | 9 s | **9,00 s** |

**Audio** — el tramo 0 **no** dispara ningún log de pasos (intensidad 0, correcto); del tramo 1 en adelante la secuencia es siempre `fade in` al arrancar → `fade out` exactamente en `Duración − 0,2` → `liberados` 0,2 s después.

💡 **Cómo se probó que el componente vive TODO el tramo** (y no muere antes, dejando el tramo mudo): `StopSteps` llama a `FadeOut` sobre `StepsComp` al final del tramo y **no hay ni un `Accessed None` en toda la corrida** — si el componente se hubiera destruido antes, esa llamada sobre una referencia nula lo habría cantado. La ausencia del error es la prueba positiva.

⚠ Lo verificado es **el recorrido, los tiempos y la mecánica del audio**. Que el caminar se *sienta* bien —el bob, el giro, si 14 s para el primer tramo es el ritmo correcto— **no se puede juzgar por log**: eso es visor.

## TODO
- [ ] 🔴 **Test en visor.** Orden de ajuste sugerido: primero las duraciones, después `BobRollDeg` (el giro rota el espacio de tracking entero) y al final `BobHeight`.
- [ ] Escuchar el loop de `Pasos` contra la cadencia del bob: hoy son independientes (`StepsPerSecond` mueve el bob, el loop corre a su propio tempo). Si se ven desfasados en visor, hay que atar uno al otro.
- [x] ~~Viñeta~~ → ✅ **integrada adentro del BP (2026-08-17)**, ver la sección de arriba. Falta juzgarla en visor: `VignetteMax` es la palanca, y `InnerCos`/`OuterCos` de `M_VignetteWalk` solo se tocan leyendo antes la calibración de `BP_Vignette`.
- [ ] Enganchar `OnArrived` cuando exista el director de etapas de la versión limpia.
- [ ] Probar el caso accesible: `BobHeight = BobRollDeg = 0` tiene que quedar una traslación lisa y usable.

## Los 6 sublevels, por ahora, arrancan CARGADOS (2026-08-17)
Decisión de Beltrán: *"dejalos cargados por ahora, luego armaremos un sistema de carga y descarga con BP"*. Los 6 `LevelStreamingDynamic` de `L_SoulCharger` tienen **`bInitiallyLoaded` y `bInitiallyVisible` en true**, así que las 6 salas están en el mundo desde el primer frame y se ven mientras se ajusta el recorrido.

🔴 **La trampa que costó el diagnóstico:** poner `bShouldBeLoaded`/`bShouldBeVisible` en true **no alcanza** — se ven en el editor y el juego arranca vacío igual, porque `ULevelStreamingDynamic` reinicializa esos dos desde `bInitiallyLoaded`/`bInitiallyVisible` cuando el mundo es de juego. Detalle en `gotchas.md` §107.

**Cuando llegue el sistema de streaming**, hay que volver los dos flags a false y que el director cargue/descargue. Los sublevels se alcanzan por MCP en `/Game/SoulCharger/MapsV2/L_SoulCharger.L_SoulCharger:LevelStreamingDynamic_0..5` (§106).

Las salas de Beltrán ya están en las paradas del recorrido: **Hall 0 · Entering 1500 · Recognizing 3000 · Loving 4500 · Attracting 6000 · Surrounding 7500** (paradas 3 a 8), todas a Z=−45.

## 🔴 Contrato con los mapas
Las salas de `MapsV2/RoomsV2` tienen que estar **en la posición mundial de su parada** (el mapa es la autoridad de posición). Las paradas nuevas (0, 1500, 3000, 4500, 6000, 7500 para las 6 salas) **no son** las del recorrido viejo (0, 1200, …, 6000): si se copia una sala de `Maps/Rooms/`, hay que moverla.

## Relacionados
- [[BP_Journey]] y [[BP_Walker]] — los antecesores. De ahí salieron el tiempo normalizado, la relación `Phase` / `Phase/2` y el no-tocar-la-yaw; todo eso estaba probado y se copió tal cual.
- [[BP_StageDirector]] — el que va a consumir `OnArrived` cuando se rehaga en limpio.

## 🕶️ 2026-08-21 — la viñeta se OCULTA cuando no actúa (reporte del visor)
Beltrán en el APK: *"se ve el borde de la esfera que hace la viñeta, a pesar de que esté apagada — un cambio en los materiales donde termina"*. La esfera translúcida pegada a la cámara, aun con `Amount = 0`, altera lo que se ve a través (blending/sorting). **Fix**: `ApplyVignette(Amount)` ahora también hace `SetVisibility(Vignette, Amount > 0.004)` — invisible en reposo (el `ApplyVignette(0)` del `SetupVignette` la esconde desde el frame 1) y sólo existe mientras el fundido de caminata la enciende. `VignetteMax = 0` ahora sí la elimina del todo.
