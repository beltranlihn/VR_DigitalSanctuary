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

## 🔴🔴 2026-08-12 — REVISIÓN CON BELTRÁN: 4 cambios estructurales decididos
Antes de tocar este BP, leer `docs/PLAN-2026-08-13.md` §0. Estado de aplicación:
1. ✅ **APLICADO (2026-08-12): son 6 salas, no 7.** `FINAL` salió de `StageNames`/`StageColors`/`RoomKinds` (ahora `[0,1,1,1,1,1]`, 6 entradas en las tres listas, seteadas en el CDO — la instancia NO tiene override de estas listas, hereda del CDO). Tras SURROUNDING (índice 5), `RefreshLastRoom` → `FinishObra`. La tabla de 7 salas de abajo queda obsoleta en la fila FINAL.
2. ✅ **APLICADO (2026-08-12): `RoomMaps` (array de string, instance-editable) reemplaza a `RoomMap`** (variable eliminada). `PreloadNext(Suffix)` ahora hace `LoadLevelInstance(RoomMaps[Suffix])` — **el parámetro `Suffix` volvió a tener uso: es el ÍNDICE del mapa**, los llamadores le pasan el índice de sala correcto (BeginPlay→0, CloseRoom→StageIndex ya incrementado). Los 6 mapas: `Maps/Rooms/L_Room_{Hall,Entering,Recognizing,Loving,Attracting,Surrounding}` (hoy copias del placeholder; Beltrán los diseña a su ritmo). **Registrados en `MapsToCook`** de `DefaultGame.ini`. Aserción nueva en `BP_SelfTest.DirMapsAsserts`: RoomMaps mismo largo que StageNames.
3. ✅ **APLICADO (2026-08-12): la puerta queda CERRADA hasta llegar.** `WalkOut` ya NO llama `OpenDoor` directo: agenda un timer a `OpenDoor` con **`DoorOpenDelay`** (nueva instance-editable, **1.6 s** en CDO e instancia, verificada). Timeline desde `WalkOut`: t=0 camina hacia la puerta cerrada (cartel encendido) · t=1.2 arranca el negro (`FadeOutDelay`) · t=1.6 la puerta abre contra el negro cayendo · t≈2.7 negro pleno · t=3.0 swap. ⚠ Restricción nueva: **`DoorOpenDelay` < `FadeOutDelay` + `FadeOutTime`** (abrir después del negro pleno sería invisible). ⚠ El pin `Object` del timer quedó en `0` al crearlo por cirugía — hubo que cablear un nodo `Getareferencetoself`; **revisar ese pin siempre que se cree un `SetTimerbyFunctionName` por cirugía**.
4. ✅ **APLICADO (2026-08-12): `FinishObra` → `BP_Room.Dissolve(LightFadeTime)`**: rampa a 0 + esconde piso y muro → queda el exterior. Verificado por log (`ROOM: la sala se deshizo`, 2.0 s después del deshacerse). Falta encima: gráfico → pregunta de Alma → constelación (paso 5 del §10).
⚠ **Trampa pagada acá:** `set_properties`/`reset_properties` sobre la INSTANCIA reportaron error al achicar los arrays, **pero el valor efectivo quedó bien** (la instancia heredaba del CDO, nunca tuvo override de las listas). Verificar siempre con `get_properties` después: el mensaje de error de arrays miente en ambos sentidos.

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

## 🆕 2026-08-12 — la obra son 7 SALAS, y 5 de ellas son etapas
Hasta ahora el director confundía "sala" con "etapa" y loopeaba sobre 3 placeholders. Ahora lleva la **lista real**, sacada del documento maestro (§3 y la tabla de etapas):

| # | `StageNames` | `RoomKinds` | Color | Qué es |
|---|---|---|---|---|
| 0 | `HALL` | 0 | blanco cálido | Alma recibe, explica, calibración, **elección del Proto Soul** |
| 1 | `ENTERING` | 1 | azul | respiración con el mando en el estómago |
| 2 | `RECOGNIZING` | 1 | rojo | mando en el pecho, latido · 🔴 **la única que sube** |
| 3 | `LOVING` | 1 | morado | contemplativa, **sin sensor**, 3 preguntas |
| 4 | `ATTRACTING` | 1 | naranja | burbujas sonoras con el puntero |
| 5 | `SURROUNDING` | 1 | verde | dibujo 3D, mandala radial |
| 6 | `FINAL` | 2 | blanco frío | la arquitectura se transforma · **sin compuerta** |

⚠ **`FINAL` es un nombre placeholder** y sale en el cartel de la última puerta (la de `SURROUNDING`). Decisión autoral pendiente.
💡 **El cartel y el resplandor son de la sala que VIENE**, no de la actual (§ "La luz que se cuela y el cartel son de la sala que viene… ya es rojo si vas a Recognizing"). Eso ya funcionaba por accidente —`CloseRoom` incrementa el índice **antes** de revelar la puerta— y **hay que no romperlo**: si alguna vez se mueve el incremento, el cartel empieza a mentir.

### La duración sale del tipo de sala
`RefreshDuration` (+ `DurationByKind` / `DurationFinal`, partidas en tres porque el parser sólo admite **un** multi-exec al final) elige entre `HallDuration`, `StageDuration` y `FinalDuration`, y deja el resultado en `CurDuration`, que es lo que usa el timer de `EnterRoom`.
⚠ **Los tres valores son placeholders de test** (10 / 8 / 12 s). Los reales son **~90 s el Hall, ~2 min cada etapa y ~2 min la final** (§3). Con los reales una vuelta completa son 14–15 min, así que para probar el ciclo se dejan cortos a propósito.

### El caso terminal: la última sala no tiene salida
```
EndStage → DimAndReveal → RefreshLastRoom → CloseOrFinish
                                             ├─ CloseRoom()   (avanza, precarga, revela la puerta, agenda WalkOut)
                                             └─ FinishObra()  (no hay puerta, no hay salida: la obra termina)
```
🔴 **`RefreshLastRoom` corre ANTES de incrementar** y pregunta por `StageIndex + 1 >= largo`, o sea *"¿hay una sala siguiente?"*. Preguntarlo después del incremento sería preguntar otra cosa.
- **`bLoopRooms`** (instance-editable, **false**): en `true` vuelve al comportamiento viejo de loopear para siempre — es lo que sirve para el modo **soak** de `BP_DebugDirector`. En `false`, `WrapIndex` queda inalcanzable por construcción.
- `FinishObra` hoy sólo loguea. Le falta el cierre real: §3 pide gráfico de datos, la pregunta de Alma, la constelación y la despedida.

## 🆕 2026-08-12 — EL CORREDOR DE LA INTRO + TIMBRE (tarea 6 del plan, construido y verificado por log)
`StartExperience()` ya NO entra directo a la primera sala: ahora corre la **escena 2 del guion** (la caminata por el vacío hasta la puerta del Center). Cadena completa, toda por funciones + timers:

```
StartExperience → StartCorridor:
    BuildPath(500 + CorridorLength)              ← spline largo del corredor
    StartWalk(L, 2L, RampIn, RampOut)            ← el pawn (en X=−500) camina L cm por el vacío
    SpawnCenterDoor                              ← BP_Door spawneado en X = L−500+DoorAhead, Configure("SOUL CHARGER CENTER", color del Hall) + Reveal
       └ SpawnBell(DoorX)                        ← BP_MenuButton en modo timbre (bHoldByHover, "PLACE YOUR HAND"), spawneado junto a la puerta, SIN armar
    timer CorridorArrive a (L/Speed + 1.5)
CorridorArrive → Arm(bell) · timer CheckBell 0.2s LOOP · MaybeAutoRing
CheckBell (poll) → si bell.bDone → BellPressed:
    ClearTimer(CheckBell) · Open(puerta) · Fade(1.0, FadeOutTime) · timer EnterCenter a FadeOutTime+0.4
EnterCenter → BuildPath(500) · KillCenterDoor (destruye puerta+timbre, cero residuos) · ShowAndEnter  ← entra al ciclo normal de salas
```

| Variable nueva | Valor | Rol |
|---|---|---|
| `CorridorLength` | **800** (placeholder de test) | Largo del corredor en cm. **El valor real sale de la duración de la voz** (~45 s ≈ 7000-7800). Cambiarlo NO toca código. |
| `DoorAhead` | 140 | Cuánto más allá del punto de parada está la puerta. |
| `BellHoldTime` | 1.5 s | Cuánto hay que sostener la mano en el timbre. |
| `bAutoRing` | false | 🧪 Andamiaje: en true, 1 s después de llegar dispara `RingBell` → `Fire()` del timbre — **simula la mano por el MISMO camino** que un timbre real (filosofía ForceComplete). Para correr la obra completa sin visor. |

**Verificado por log (2026-08-12 14:31):** corredor 6.3 s → llegada → auto-ring → `timbre aceptado - el Center abre` → puerta+timbre destruidos → swap → Hall → ciclo normal. El walker reconstruye el spline **1300 → 500** en los momentos correctos.
⚠ **El hold real del timbre (mano 1.5 s) es territorio del visor** — el auto-ring lo saltea por diseño.
⚠ **Trampa nueva pagada acá:** un literal NUMÉRICO posicional a una función propia también se pierde (`(CallFunction|Fade 1.0 X)` quedó como `Fade(Alpha←X, Duration=0)`). No es solo con strings: **releer TODO llamado a función propia con literales** después de un write.

## Cómo está encadenado
🔴 **Los saltos entre tramos van por `SetTimerByFunctionName`, no por `Delay`.** Un `Delay` no es válido dentro de una función, y el ciclo necesita esperas entre pasos; los timers por nombre funcionan sobre **custom events** igual que sobre funciones, así que cada tramo es un evento aparte y el anterior lo agenda. Ventaja lateral: cada tramo es un punto de entrada nombrado, así que `BP_DebugDirector` va a poder saltar a cualquiera.

| Evento | Qué hace | Agenda |
|---|---|---|
| `BeginPlay` | Cachea fade y walker · **negro instantáneo** · `PreloadNext(0)` | `ShowAndEnter` a 1.5 s |
| `ShowAndEnter` | `SwapRooms()` = oculta la vieja · **`UnloadOldRoom()`** · muestra la nueva | `TryEnter` a `BlackHold` |
| `EnterRoom` | Cachea room y door de la sala nueva · `ConfigureRoom()` · fade **from** black · `Walk(0→500)` = entra desde el umbral al centro | `EndStage` a `StageDuration` |
| `EndStage` | `DimAndReveal()` (sólo atenúa) · `RefreshLastRoom()` · `CloseOrFinish()` → o **`CloseRoom`** (`StageIndex++` · `WrapIndex` · `PreloadNext(i)` · `RevealDoor()`, que **agenda** el revelado) o **`FinishObra`** | `WalkOut` a `RevealHold`, **desde `CloseRoom`** |
| `WalkOut` | `Walk(500→1000)` = del centro al umbral · `OpenDoor()` | `GoBlack` a `FadeOutDelay` |
| `GoBlack` | fade **to** black | `ShowAndEnter` a `LegTime` |

El loop cierra en `ShowAndEnter`, así que con el placeholder recorre las 3 etapas de prueba y vuelve a empezar indefinidamente.

🆕 **2026-08-13 — el paso a etapas reales:**
- **`SpawnStage`** ramifica por índice vía `SpawnEnteringOrBase`: 0 → `SpawnHallStage` · 1 → **`SpawnEnteringStage`** ([[BP_Stage_Entering]], la primera etapa con mecánica real) · resto → `SpawnBaseStage`. Agregar una etapa nueva = otra rama en `SpawnEnteringOrBase` + su `SpawnXStage`.
- **`ExtendTimeout(Seconds)`** — API para las etapas reales: re-agenda el timer por nombre `"EndStage"` (los timers por nombre se resetean al re-setear con el mismo nombre), así el cortafuegos de inactividad no mata una mecánica que tarda minutos. La llama el `RunStage` de la etapa (Entering usa 240 s). Log: `DIR: cortafuegos extendido por la etapa real`.

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
| `StageNames` | **las 7 salas** (ver abajo) | 🔴 **Es la lista de SALAS, no de etapas** — el nombre quedó del diseño viejo y la API no puede renombrar variables. **Su largo define cuántas salas tiene la obra.** |
| `StageColors` | 7 colores | El acento de cada sala y de su puerta. Es lo que hace que las transiciones se **vean** distintas siendo el mismo asset. |
| `RoomKinds` | `[0,1,1,1,1,1,2]` | 🆕 **Qué ES cada sala:** `0` = Hall · `1` = etapa · `2` = sala final. De acá sale la duración, y va a salir qué mecánica corre cuando exista `BP_StageBase`. |
| `StageIndex` | 0 | **Sala** actual. |
| `RoomSerial` | 0 | 🆕 Contador **monótono** que nombra la instancia de nivel. **No es el índice de etapa** — ver bug #2. |
| `CurLevel` / `NextLevel` | — | Los `LevelStreamingDynamic` que devuelve `LoadLevelInstance`. |
| `PrevRoom` | — | La sala de la que ya se entró. Es la mitad no obvia del fix del bug #0. |

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
🔴 **Estos son los valores EFECTIVOS de la instancia de `L_Persistent`, leídos con `get_properties` el 2026-08-11**, no los defaults del CDO. Las variables instance-editable se serializan como override en el actor, así que **cambiar el CDO no las mueve** — hay que setear la instancia y verificarla.

| Variable | Valor | Rol |
|---|---|---|
| `StageDuration` | 8.0 s | Placeholder de la mecánica de la etapa. Lo reemplaza `BP_StageBase.RunStage()`. |
| `LightRiseTime` | 2.5 s | La sala nueva sube de luz. |
| `LightFadeTime` | 2.0 s | La sala baja al terminar la etapa. |
| `RevealHold` | **4.2 s** | Cuánto se mira el marco trazado antes de empezar a caminar. Cubre `LightFadeTime + RevealTime` + un beat. |
| `FadeOutDelay` | 1.2 s | Desde que arranca la caminata hasta que empieza el negro. |
| `FadeOutTime` | 1.5 s | Duración del fundido a negro. |
| `FadeInTime` | **1.4 s** | Duración del fundido de entrada. |
| `LegTime` | **1.8 s** | Cuánto se deja correr el tramo de salida antes del swap. **Tiene que ser ≥ `FadeOutTime`** o el swap se ve. |
| `BlackHold` | **0.4 s** | Beat de negro deliberado después del swap. Ya **no** es la tapadera de la carrera con `AddToWorld` (eso lo cubre el retry de `TryEnter`). |
| `bAutoStart` | true | Hoy arranca solo para poder probar. **Lo apaga el menú** cuando exista: el punto de entrada es `StartExperience()`. |

## Streaming — lo que se respetó de `references/streaming-arch.md`
- ✅ **`OptionalLevelNameOverride` en cada `LoadLevelInstance`** (`Room_0`, `Room_1`, …). Sin eso cada llamada crea un paquete nuevo y **filtra niveles**. Verificado en el log de PIE: las instancias se cargan como `Room_N`.
- 🔴 **El sufijo sale de `RoomSerial`, un contador MONÓTONO, no de `StageIndex`.** Ver el bug #2 de abajo: con el índice de etapa el nombre **se repite** al cerrar el loop y `LoadLevelInstance` devuelve `nullptr`.
- ✅ **`UnloadOldRoom()` en el swap** (2026-08-11): descarga la sala que se acaba de ocultar, **bajo negro**, que es donde el GC que fuerza no se siente.
- ✅ **Precarga invisible**: el nodo BP de `LoadLevelInstance` **no expone `bInitiallyVisible`** y su default en el struct es `true`, así que se llama `SetShouldBeVisible(false)` inmediatamente después. Es la única forma de conseguir el "Make Visible After Load = false" del §9.2 por Blueprint.
- ✅ El swap sólo **cambia visibilidad**, que es lo instantáneo; la carga ya ocurrió segundos antes, durante el revelado de la puerta.
- ✅ El bug #0 (`BlackHold` era una carrera contra `AddToWorld`) está arreglado. Ver abajo.

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

### 1. ✅ ARREGLADO — `OnPawnPassed` de la puerta nueva disparaba espurio en el swap
Visto en el log: dos `OnPawnPassed` seguidos, uno legítimo y otro 0,7 s después, justo tras el swap. Causa: al momento del swap el pawn está en X≈500 (fin del tramo de salida) y la puerta de la sala nueva está en X=460, así que `dot(pawn−door, forward) > 0` es verdadero **antes** de que el tramo de entrada lo reposicione a −500. Como `bPassed` se pone una sola vez, el cruce real de esa puerta después **ya no disparaba**.
**Fix aplicado:** `CheckPassed` de [[BP_Door]] está gateado a `RevealProgress > 0.5`. Es lo semánticamente correcto además: una puerta que **todavía no existe** (§9.8) no se puede cruzar.

### 2. ✅ ARREGLADO — el nombre de la instancia de nivel se REPETÍA al cerrar el loop
🔴 **Lo encontró el barrido de errores del log, no una observación** — es invisible mirando:
```
LogLevelStreaming: Error: LoadLevelInstance called with a name that already exists,
returning nullptr. LevelPackageName:/Game/SoulCharger/Maps/Rooms/UEDPIE_0_Room_0
```
`PreloadNext(Suffix)` construía el nombre desde el **`StageIndex`**, que da la vuelta (`WrapIndex`). Al volver a la etapa 0, el nombre `Room_0` **ya existía** — porque los sublevels viejos nunca se descargaban — así que `LoadLevelInstance` devolvía **`nullptr`**, `NextLevel` quedaba nulo y **la obra se quedaba en negro para siempre**. Con 3 etapas placeholder eso pasa a la cuarta transición.

**Fix aplicado, en dos partes, y las dos hacen falta:**
1. **`RoomSerial`**, un contador **monótono** que se incrementa en cada `PreloadNext` y es el que nombra la instancia. Por construcción no puede repetirse, sin depender de que la descarga haya terminado (que es **asíncrona**).
2. **`UnloadOldRoom()`** en `SwapRooms`, entre ocultar la vieja y mostrar la nueva: `SetIsRequestingUnloadandRemoval` sobre `CurLevel`, que en ese instante todavía apunta a la sala **vieja**. Cierra además el leak de sublevels.

⚠ **`Suffix` quedó como parámetro sin uso** de `PreloadNext` (los llamadores le siguen pasando el `StageIndex`). No molesta, pero **el nombre de la instancia ya no tiene relación con la etapa**: `Room_3` no es la etapa 3.

**Verificado por log** (PIE, 3 ciclos completos, batería corrida a los 42 s): preloads `Room_0 → Room_1 → Room_2 → Room_3`, y `SELFTEST: salas en el mundo = 1` con **`TEST PASS: no se acumulan salas`**. Sin la descarga ese número crecería por ciclo.

⚠ **Los 2 errores de "name already exists" que quedan en el log son un artefacto de recompilar con PIE corriendo** (el recompile re-corre `BeginPlay` sobre la instancia viva y vuelve a precargar con el mismo nombre). No son del ciclo: mirar el timestamp contra el del compile antes de perseguirlos.

### 3. ⚠ **La puerta abre antes del negro, no después.** El §9.2 literal dice `negro completo -> swap -> la puerta abre`. Acá abre durante la aproximación, así que se camina a través de una puerta abierta hacia el negro. Se hizo así porque con todas las salas en el mismo origen, la puerta que "abre revelando la sala nueva" quedaría **detrás** del pawn tras el swap. **Es una decisión autoral pendiente de Beltrán**, no un descuido.

## Verificado por log (2026-08-12): el recorrido COMPLETO
Una corrida entera con las 7 salas: `Room_0 … Room_6`, **7 precargas sin colisión de nombre**, 7 entradas, y al cerrar la última:
```
DIR: fin de sala - baja la luz
DIR: ultima sala - la obra termina aca, sin compuerta ni salida
```
y **se detiene**: no agenda `WalkOut`, no revela puerta, no loopea. Batería: **24 pass / 0 fail** en PIE · 23/0/1 skip en Simulate.

## TODO
- [ ] 🔴 Test en visor.
- [ ] La decisión autoral del bug #3 (¿la puerta abre antes o después del negro?).
- [x] ~~Separar "sala" de "etapa"~~ · ~~caso terminal~~ (2026-08-12).
- [ ] 🔴 **La sala final tiene que ABRIRSE para devolver el exterior.** La obra va *exterior → Center → exterior* (§3 y la nota de estructura en [[BP_IntroSequence]]): la constelación pasa **afuera**, en el mismo vacío del comienzo. `FinishObra` hoy sólo loguea; le falta esconder el muro de `BP_Room` (no sólo atenuarlo) para que se vea `BP_Void` de nuevo. `BP_Room` necesita un `OpenWalls(Alpha)` o equivalente.
- [ ] **El tramo de la intro**: caminar por el vacío hasta la puerta del hall, **sin sala visible**. `BP_Walker.BuildPath(HalfLen)` ya existe para eso (45 s a 175 cm/s ≈ 78 m, contra los 10 m del tramo entre salas). Falta el `BP_Door` en el persistente al final del corredor y el estado nuevo en el director.
- [ ] Las **duraciones reales** (90 / 120 / 120 s) cuando se pruebe la obra de punta a punta; hoy son 10 / 8 / 12 para poder testear.
- [ ] Renombrar `StageNames`/`StageColors`/`StageIndex` a `Room*`. ⚠ **La API no puede renombrar variables**: es a mano en el editor, y hay que recompilar todo lo que las lea.
- [ ] Llamar `SetMode` de [[BP_Sensor]] al entrar a cada etapa, y `Release` al cerrarla.
- [ ] `StageDuration` sale cuando exista `BP_StageBase`: el cierre lo va a pedir la etapa, no un timer.
- [ ] Medir el hitch de la descarga **en device**. El GC que fuerza (`s.ForceGCAfterLevelStreamedOut` viene en 1) queda bajo negro, que es lo correcto, pero eso no prueba que no se sienta en Quest.

## Relacionados
- [[BP_Room]] (`Configure`/`SetLight`/`RampLight`) · [[BP_Door]] (`Configure`/`Reveal`/`Open`) · [[BP_Walker]] (`StartWalk`) · `BP_FadeSphere` · `BP_DebugDirector` (sin construir)

## 🆕 EL RECORRIDO REAL (2026-08-13, entrega 2) — las salas viven en el mundo, no apiladas en el origen
Antes: las 6 salas se cargaban **todas en el origen** y el pawn caminaba un segmento recto de 10 m reconstruido en cada sala. Ahora hay **un solo recorrido** ([[BP_Journey]]) y cada sala ocupa su parada.
- **`CacheRouteActor`** (BeginPlay, después de `CacheWalker`) cachea el `BP_Journey`. 🔴 **Se llama así y no `CacheJourney` a propósito**: el walker YA tiene una función con ese nombre y el DSL, ante un nombre ambiguo, resuelve a la clase equivocada (mordió en esta sesión: el BeginPlay del director terminó llamando al `CacheJourney` del walker). Nombres únicos entre BPs.
- **`PreloadNext(Suffix)`** carga el level instance pasándole `Journey.GetStopLocation(Suffix+1)` como Location. Mapeo: **StageIndex n → parada n+1**.
- 🔴🔴 **PERO el Location de `LoadLevelInstance(byName)` NO movió los actores** (medido: parada esperada X=1200, sala en X=0.000). Por eso `CacheRoom` termina llamando a **`PlaceRoomAtStop`**, que hace `SetActorLocation` sobre el `BP_Room` a su parada — vía directa, bajo nuestro control, y que además **loguea la posición efectiva** (`DIR: sala movida a su parada X=...`). Verificado: sala 2 en X=1200.000.
- **`EnterRoom` ya no reposiciona** (se quitó el `Walk(0→500)`): el pawn llega caminando el tramo.
- **`WalkOut` → `StartLegWalk`**: `WalkLeg(StageIndex)` + agenda `GoBlack` a **`LegTime − FadeOutTime`**, así el negro termina de caer justo al llegar. Todo se deriva del tiempo del tramo → **cambiar `LegTimes` en el Journey no descuadra la transición**.
- **`EnterCenter`** (fin del corredor de la intro) hace `PlaceAtStop(1)` bajo negro: es el puente entre el corredor viejo (que sigue con su `BuildPath` propio) y el recorrido.

**Medido en PIE:** tramo 1 en 7.98 s contra 8.0 pedidos · sala nueva encendiendo 0.72 s después de la llegada · sala 2 en su parada exacta.

### ⚠ Pendientes conocidos de esta entrega
- `CacheRoom` se ejecuta **dos veces por entrada** (dos bloques idénticos en el mismo ms). Es idempotente, pero hay una llamada de más que conviene rastrear.
- `CacheRoom` usa `GetActorOfClass(BP_Room)` = "la primera que aparezca". Hoy sólo hay una sala viva a la vez y funciona, pero es el mismo patrón frágil que el `CacheHud` de [[BP_SoulChoice]]: si alguna vez conviven dos salas, agarra la equivocada.
- El **corredor de la intro** sigue con el mecanismo viejo (`BuildPath` + `StartWalk` sobre el spline propio del walker). Migrarlo a ser el tramo 0 del recorrido es el paso natural siguiente.
