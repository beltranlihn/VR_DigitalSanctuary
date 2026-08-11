# BP_StageDirector — el ciclo de transición (Core/Flow/)

## Purpose
El orquestador del §9.4: lleva la lista ordenada de etapas, mueve el pawn por el spline y maneja las compuertas. Vive en el **nivel persistente**. Implementa el ciclo de transición del §9.2 completo:

```
precarga del sublevel siguiente (invisible)
la luz de la sala baja + se traza el marco + se enciende el cartel
negro completo -> swap: oculta A, muestra B, reposiciona el pawn
la puerta abre -> la nueva sala sube de luz
```

**Reemplaza a `BP_FlowDirector`**, que era un smoke test con delays hardcodeados (su actor ya se quitó de `L_Persistent`).

## Status
🟡 **Ciclo completo funcionando y loopeando, verificado por log en PIE (2026-08-11).** Falta el test en visor y quedan 2 bugs conocidos (abajo).

## 🔴🔴 LA OBRA NO EMPIEZA ACÁ — hay una INTRO antes (§3), y cambia supuestos
Aclarado por Beltrán el 2026-08-11 y confirmado contra §3 del documento maestro. **La experiencia arranca en negro con logos, título y menú principal (Start / About); recién al apretar Start el pawn empieza a avanzar, y avanza hasta la puerta del Hall.** La escena completa:

| # | Escena | Duración |
|---|---|---|
| 0 | **Intro** — logos, título, Start / About | — |
| 1 | **Oscuridad** — voz femenina espacializada | ~45 s |
| 2 | **La caminata** — desde el botón Start. Pasos, silueta de puerta, *Soul Charger Center*. **Timbre: apoyás la mano y te escanea** | ~45 s |
| 3 | **Hall** — Alma recibe, explica las etapas, calibración, elegís tu Proto Soul | ~90 s |
| 4–8 | Las cinco etapas | 5 × ~2 min |
| 9 | **Sala final** — la arquitectura se transforma, **NO hay compuerta** | ~2 min |

**Lo que esto corrige de lo ya construido:**
1. ✅ **El director NO es dueño del arranque** — arreglado. `BeginPlay` ya no dispara la experiencia: llama `MaybeAutoStart()`, que sólo arranca si **`bAutoStart`** (true hoy, para poder probar). **El punto de entrada público es `StartExperience()`**, que es lo que va a llamar el botón Start del menú. Que el director **quede en negro esperando** ya es el comportamiento correcto (§3 escena 0). La precarga de la primera sala sigue en `BeginPlay`, y eso es **deseable**: la intro y el menú dan de sobra para cargar sin hitch.
2. 🔴 **La caminata de la intro NO es un beat de 5–7 s: son ~45 s**, y §3 pide **30–40 s de avance estable** porque *"la caminata de la intro tiene dos trabajos: instala el mood y es donde se toma el baseline"* (§5). A 175 cm/s eso son **52–70 m** de spline, contra los 10 m de `PathHalfLength` actual. **La intro necesita su propio camino largo, no el spline de transición entre salas.** Ver el TODO de [[BP_Walker]].
3. ⚠ **Son 7 salas, no 5**: Hall + 5 etapas + sala final. `StageNames`/`StageColors` hoy tienen 3 entradas placeholder y confunden "sala" con "etapa". Cuando entre `BP_StageBase` hay que separar los dos conceptos.
4. ⚠ **La sala final no lleva puerta** ("no hay compuerta"): el ciclo de transición **no aplica** al último tramo. El director necesita un caso terminal, no `WrapIndex` en loop.
5. 💡 **El timbre del Center es el tutorial del gesto del sensor** (§3): apoyar la mano para que te escanee es la misma gramática que tomar el sensor. El timbre y los sensores **deben parecerse visualmente**. Es un requisito de diseño para cuando se construya la puerta del Hall, no un detalle.

## Cómo está encadenado
🔴 **Los saltos entre tramos van por `SetTimerByFunctionName`, no por `Delay`.** Un `Delay` no es válido dentro de una función, y el ciclo necesita esperas entre pasos; los timers por nombre funcionan sobre **custom events** igual que sobre funciones, así que cada tramo es un evento aparte y el anterior lo agenda. Ventaja lateral: cada tramo es un punto de entrada nombrado, así que `BP_DebugDirector` va a poder saltar a cualquiera.

| Evento | Qué hace | Agenda |
|---|---|---|
| `BeginPlay` | Cachea fade y walker · **negro instantáneo** · `PreloadNext(0)` | `ShowAndEnter` a 1.5 s |
| `ShowAndEnter` | `SwapRooms()` | `EnterRoom` a `BlackHold` |
| `EnterRoom` | Cachea room y door de la sala nueva · `ConfigureRoom()` · fade **from** black · `Walk(0→500)` = entra desde el umbral al centro | `EndStage` a `StageDuration` |
| `EndStage` | `StageIndex++` · `WrapIndex()` · `PreloadNext(i)` · `DimAndReveal()` (sólo atenúa) · `RevealDoor()` (**agenda** el revelado) | `WalkOut` a `RevealHold` |
| `WalkOut` | `Walk(500→1000)` = del centro al umbral · `OpenDoor()` | `GoBlack` a `FadeOutDelay` |
| `GoBlack` | fade **to** black | `ShowAndEnter` a `LegTime` |

El loop cierra en `ShowAndEnter`, así que con el placeholder recorre las 3 etapas de prueba y vuelve a empezar indefinidamente.

🔴 **El reposicionamiento del pawn NO es un teleport aparte**: lo hace `Walk(0, 500, ...)` de `EnterRoom`, porque `StartWalk` fija `Dist = FromDist` y el primer tick coloca al pawn en `spline(0)` = X −500. Un solo mecanismo para mover y para reposicionar, y ocurre bajo negro.

## Registro de variables

### Referencias (se cachean con `GetActorOfClass` + cast)
| Variable | Cuándo se cachea |
|---|---|
| `FadeRef` / `WalkerRef` | `BeginPlay` — viven en el persistente |
| `RoomRef` / `DoorRef` | **cada `EnterRoom`** — son de la sala nueva, así que hay que re-buscarlas después de cada swap |

⚠ Funciona buscar con `GetActorOfClass` (que devuelve el primero) **sólo porque se oculta A antes de mostrar B**: en el instante del swap hay una sola sala en el mundo. Los actores de un sublevel precargado-invisible **no están en el mundo** (no corrió `AddToWorld`), así que no aparecen en la búsqueda. Si alguna vez se muestran dos salas a la vez, esto se rompe.

### Flujo
| Variable | Default | Rol |
|---|---|---|
| `RoomMap` | `/Game/.../L_Room_Placeholder` | El mapa que se instancia. Placeholder: siempre el mismo, cambia sólo el nombre de la instancia. |
| `StageNames` | ENTERING / RECOGNIZING / SURROUNDING | Placeholder de 3 etapas. **Su largo define cuántas hay** (`WrapIndex` cierra el loop). |
| `StageColors` | azul / rojo / verde | El acento de cada sala y de su puerta. Es lo que hace que las transiciones se **vean** distintas siendo el mismo asset. |
| `StageIndex` | 0 | Etapa actual. |
| `CurLevel` / `NextLevel` | — | Los `LevelStreamingDynamic` que devuelve `LoadLevelInstance`. |

## 🔴 El ORDEN de la transición, y por qué estos números (ajustado en visor 2026-08-11)
Beltrán reportó dos cosas al probarlo, y las dos eran de secuencia, no de código:

**1. "Las puertas aparecen cuando todavía se ve todo. Es rudo, aparecen de la nada."**
`EndStage` disparaba `DimAndReveal()` y `RevealDoor()` en el **mismo instante**, así que el marco se trazaba sobre una sala brillante. El orden correcto (y el del §9.2) es **primero oscuro, después la puerta**.
→ **`RevealDoor()` ahora sólo AGENDA**: pone un timer a `DoRevealDoor` a `LightFadeTime`, o sea cuando el atenuado terminó. `DoRevealDoor` tiene el cuerpo real (Configure + Reveal).
→ Como el revelado arranca tarde, `RevealHold` **se mide desde `EndStage`** y tiene que cubrir `LightFadeTime + RevealTime` **más un beat**, o se empieza a caminar con el marco a medio dibujar.

**2. "Al pasar la puerta pasa mucho rato oscuro hasta que volvemos a ver."**
`LegTime` estaba en 4.2 s porque lo había dimensionado para que el tramo de salida **terminara**. No hace falta: el tramo de entrada resetea `Dist` igual, así que lo único que `LegTime` tiene que cubrir es que **el fundido a negro haya terminado**. Sobraban ~2,7 s de negro puro esperando de gusto.
→ `LegTime` 4.2 → **1.8** (= `FadeOutTime` 1.5 + margen), `BlackHold` 0.8 → **0.4** (el retry de `TryEnter` cubre la espera real), `FadeInTime` 1.8 → **1.4**.

**Medido por log después del ajuste** (segunda transición, t desde `EndStage`):
| t | Qué |
|---|---|
| 0,00 s | la sala empieza a atenuarse |
| **+2,03 s** | se traza el marco — **ya a oscuras** |
| +3,83 s | el marco queda completo |
| **+4,37 s** | abre (0,5 s de beat con la puerta ya dibujada) |
| +7,10 s | swap |
| +8,37 s | sala nueva confirmada, sube la luz |

**Negro puro: 1,3 s** (antes 3,7).

⚠ **La restricción a respetar si se toca cualquiera de estos números:** `RevealHold > LightFadeTime + RevealTime` y `LegTime ≥ FadeOutTime`. Romper la primera hace que se camine con el marco a medio trazar; romper la segunda hace que **el swap se vea**.

### Tiempos (todos instance-editable en el actor del persistente)
| Variable | Default | Rol |
|---|---|---|
| `StageDuration` | 8.0 s | Placeholder de la mecánica de la etapa. Lo reemplaza `BP_StageBase.RunStage()`. |
| `LightRiseTime` | 2.5 s | La sala nueva sube de luz. |
| `LightFadeTime` | 2.0 s | La sala baja al terminar la etapa. |
| `RevealHold` | 2.8 s | Cuánto se mira el marco trazado antes de empezar a caminar. |
| `FadeOutDelay` | 1.2 s | Desde que arranca la caminata hasta que empieza el negro. |
| `FadeOutTime` | 1.5 s | Duración del fundido a negro. |
| `FadeInTime` | 1.8 s | Duración del fundido de entrada. |
| `LegTime` | 4.2 s | Cuánto se deja correr el tramo de salida antes del swap. **Tiene que ser ≥ `FadeOutDelay + FadeOutTime`** o el swap se ve. |
| `BlackHold` | 0.5 s | Negro sostenido después del swap, para que `AddToWorld` termine. |

## Streaming — lo que se respetó de `references/streaming-arch.md`
- ✅ **`OptionalLevelNameOverride` en cada `LoadLevelInstance`** (`Room_0`, `Room_1`, …). Sin eso cada llamada crea un paquete nuevo y **filtra niveles**. Verificado en el log de PIE: las instancias se cargan como `Room_N`.
- ✅ **Precarga invisible**: el nodo BP de `LoadLevelInstance` **no expone `bInitiallyVisible`** y su default en el struct es `true`, así que se llama `SetShouldBeVisible(false)` inmediatamente después. Es la única forma de conseguir el "Make Visible After Load = false" del §9.2 por Blueprint.
- ✅ El swap sólo **cambia visibilidad**, que es lo instantáneo; la carga ya ocurrió segundos antes, durante el revelado de la puerta.
- 🔴🔴 **BUG ACTIVO — `BlackHold` es una CARRERA, no una espera.** Es el bug #0 y hay que arreglarlo antes de seguir. Ver abajo.

## 🐛 Bugs conocidos

### 0. ✅ ARREGLADO — `BlackHold` era una CARRERA contra `AddToWorld`
**Detectado por log el 2026-08-11, y es el caso de libro de lo que `streaming-arch.md` prohíbe.** El log decía:
```
DIR: swap hecho bajo negro
DIR: la sala visible no tiene BP_Room
DIR: la sala visible no tiene BP_Door
```
`SetShouldBeVisible(true)` arranca un **`AddToWorld` incremental**; los actores del sublevel no están en el mundo hasta que termina. `EnterRoom` corría `BlackHold` después del swap y buscaba `BP_Room`/`BP_Door` con `GetActorOfClass` → **null**, los casts fallaban, y como `SetRoomRef` sólo se llama en la rama de éxito, **`RoomRef` se quedaba apuntando a la sala VIEJA, que acababa de ocultarse** → la luz se rampeaba en una sala invisible.

⚠ **Y lo agravamos nosotros:** bajar `s.LevelStreamingActorsUpdateTimeLimit` de 5.0 a 1.5 ms (correcto para el presupuesto de frame de Quest) hace `AddToWorld` **más lento**, así que la ventana de la carrera es más ancha justamente en el target.

🔴 **Insidioso:** con `BlackHold = 0.5` la carrera se gana a veces. La primera corrida completa pareció andar perfecta; la falla apareció recién en la segunda. **Una corrida verde no prueba nada acá.**

## ✅ EL FIX (2026-08-11): esperar la CONDICIÓN, no un tiempo
`ShowAndEnter` ya no agenda `EnterRoom` directo, agenda **`TryEnter`**:
```
TryEnter():  CacheRoom · CacheDoor · si RoomRef inválido -> re-agendarse a 0.1 s
                                    si válido -> EnterIfFresh()
EnterIfFresh():  si RoomRef == PrevRoom -> re-agendar TryEnter (es la sala VIEJA)
                 si no -> PrevRoom = RoomRef · EnterRoom()
```
🔴 **La comparación contra `PrevRoom` es la mitad no obvia del fix, y sin ella el arreglo es falso.** Cuando un nivel se oculta **queda cargado**: sus actores no se destruyen, así que la referencia vieja **sigue pasando `IsValid`**. Chequear sólo validez habría entrado con la sala anterior en las transiciones 2+ y el bug se habría "arreglado" sólo en la primera. `PrevRoom` se actualiza recién cuando se confirma una sala **distinta**.

⚠ Se eligió esperar "el actor existe" en vez de `OnLevelShown` porque **es la condición que el director de verdad necesita**: que el nivel esté visible no garantiza que sus actores estén registrados. (`EventDispatchers|AssignOnLevelShown` queda verificado y disponible si algún día hace falta; su binding tendría que ir por cirugía, porque los eventos no existen en grafos de función.)

**Verificado por log:** swap a las 18:02:36.499 → `DIR: sala nueva confirmada en el mundo` a las 18:02:37.499 (el retry esperó ~0.2 s más que `BlackHold`) → `EnterRoom`. **Cero** mensajes de cast fallido en toda la corrida. `BlackHold` volvió a **0.8 s**, que ahora es sólo un beat de negro deliberado y no una tapadera de la carrera.

⚠ **Nota de método:** con `BlackHold = 0.5` la carrera se ganaba **a veces** — la primera corrida completa pareció perfecta y la falla salió en la segunda. **Una corrida verde no prueba nada en este tipo de bug.** Lo que lo delató fue leer el log, no mirar.

### 1. 🔴 **`OnPawnPassed` de la puerta nueva dispara espurio en el swap.** Visto en el log: dos `OnPawnPassed` seguidos, uno legítimo y otro 0,7 s después, justo tras el swap. Causa: al momento del swap el pawn está en X≈500 (fin del tramo de salida) y la puerta de la sala nueva está en X=460, así que `dot(pawn−door, forward) > 0` es verdadero **antes** de que el tramo de entrada lo reposicione a −500. Como `bPassed` se pone una sola vez, el cruce real de esa puerta después **ya no dispara**.
   **Fix propuesto:** gatear `CheckPassed` a que la puerta esté revelada (`RevealProgress > 0.5`). Es semánticamente correcto además: una puerta que todavía no existe (§9.8) no se puede cruzar. Requiere borrar y recrear el grafo `CheckPassed` (reescribirlo duplicaría el cuerpo).
   **Impacto hoy: ninguno** — nadie consume el dispatcher todavía. Pero hay que arreglarlo **antes** de que el director lo use.
2. ⚠ **La puerta abre antes del negro, no después.** El §9.2 literal dice `negro completo -> swap -> la puerta abre`. Acá abre durante la aproximación, así que se camina a través de una puerta abierta hacia el negro. Se hizo así porque con todas las salas en el mismo origen, la puerta que "abre revelando la sala nueva" quedaría **detrás** del pawn tras el swap. **Es una decisión autoral pendiente de Beltrán**, no un descuido.

## TODO
- [ ] Test en visor.
- [ ] Los 2 bugs de arriba.
- [ ] `OnLevelShown` en lugar de `BlackHold`.
- [ ] Descargar la sala vieja (`SetIsRequestingUnloadAndRemoval`) — hoy quedan todas las instancias cargadas e invisibles. Con 3 salas placeholder no importa; con 9 salas reales **sí**. ⚠ Descargar fuerza un GC (`s.ForceGCAfterLevelStreamedOut` viene en 1) y ese GC **es** el hitch → hacerlo bajo negro.
- [ ] `StageDuration` sale cuando exista `BP_StageBase`: el cierre lo va a pedir la etapa, no un timer.

## Relacionados
- [[BP_Room]] (`Configure`/`SetLight`/`RampLight`) · [[BP_Door]] (`Configure`/`Reveal`/`Open`) · [[BP_Walker]] (`StartWalk`) · `BP_FadeSphere` · `BP_DebugDirector` (sin construir)
