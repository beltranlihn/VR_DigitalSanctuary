# BP_Director_Story — el director del GUIÓN (Core/Flow/)

> `/Game/SoulCharger/Core/Flow/BP_Director_Story` · creado 2026-08-19 · **una instancia** en `MapsV2/L_SoulCharger` (`Director_Story`, en −5000/200/0).
> **Estado: 🟡 recorrido completo verificado en PIE por log en modo `bAutoTest` (sin manos); falta el visor.**

## Qué es
La **maqueta de funcionamiento de la obra de principio a fin**, pedida por Beltrán el 2026-08-19: *"armar el puzzle"* con los 33 voice overs de Alma como anclas de timing. Es un **secuenciador de pasos**: cada paso **dispara** cosas (VO, Alma, sensor, picker, anillos, panel, salas) y declara **qué espera** (`WaitFor`) para avanzar. **No sabe de visuales ni de audio**: sólo llama a la API de los otros BPs y escucha sus dispatchers.

🔴 **Todo el cableado del guión vive ACÁ** (binds a dispatchers en `Boot`). Los demás BPs sólo exponen verbos (`Speak`, `AppearAt`, `Awake`, `Show`, `DrawRing`…) y avisos (`OnVOFinished`, `OnArrived`, `OnRingDone`, `OnTaken`, `OnChosen`, `OnFinished`, `OnLegStarted`). Para cambiar el orden de la obra se toca **este** BP (o, mejor, sus arrays).

## 🔢 Los VO se indexan con el NÚMERO de Beltrán
`BP_Alma_SC.VOClips` tiene **34 entradas**: la entrada `i` es *Voice Over i*. **La 0 y la 6 están vacías** (el 6 no existe). Así, los números que se hablan son los que están en el array: *"VO 13"* = `VOClips[13]`. Un índice vacío o fuera de rango **no traba la obra**: Alma lo dice por log y avisa `OnVOFinished` al segundo.

## Registro de variables
### A - Guion por sala — arrays de 6, **índice = sala** (0 Hall · 1 Entering · 2 Recognizing · 3 Loving · 4 Attracting · 5 Surrounding)
| Variable | Valor | Qué es |
|---|---|---|
| `RoomNames` | hall, entering, recognizing, loving, attracting, surrounding | 🔴 **De acá salen los tags**: `alma_<n>_appear`, `alma_<n>_move`, `instr_<n>`. |
| `VOAppear` | 2, 10, 15, 20, 24, 28 | VO al **aparecer Alma** al cruzar la puerta. |
| `VOMove` | 3, 11, 16, 21, 25, 29 | VO al **moverse Alma** a su 2º punto. |
| `bPanel` | ✘ ✔ ✔ ✘ ✔ ✔ | Si la sala muestra **instrucciones** (panel + botón) junto con `VOMove`. Loving no tiene. |
| `VOStep` | 4, 12, 17, −1, −1, −1 | VO que arranca **junto con el step game time** (−1 = sin VO). En el Hall es el VO del sensor. |
| `VOPick` | 8, 13, 18, 22, 26, 30 | VO cuando la proto ameba **viaja a `soul_pick_<sala>`**. |
| `RingIndex` | −1, 0, 1, 2, 3, −1 | Qué anillo se dibuja al terminar `VOPick` (−1 = ninguno → en Surrounding dispara el **final**). |
| `VOFace` | 9, 14, 19, 23, 27, −1 | VO cuando la proto ameba **vuelve a la cara**; al terminar, Alma desaparece y la sala cierra. |

### B - VO sueltos
`VOStart` 1 (arranca con la caminata) · `VOTaken` 5 (al tomar el sensor) · `VOChoose` 7 (al despertar las 5 candidatas) · `VOEnd1/2/3` 31/32/33 (el final).

### C - Tiempos y tags
`StepGameTime` **10 s** (el cortafuegos por etapa) · `EndingPause` **2 s** (lo que espera después de cerrar Surrounding, antes del VO 31) · `DoorCrossOffset` 0 cm (+ = el "cruzamos la puerta" se dispara más adentro) · `FaceTag` `soul_face`.

### D - Test
🧪 **`DebugStartRoom`** (int, **instance-editable**, −1) — **la palanca para empezar la obra en cualquier sala.** Ver la sección dedicada más abajo. · `DebugStartDelay` (0.3 s) y `DebugStopBase` (3) — 🔴 **NO instance-editable a propósito**: si lo fueran nacerían en 0 en el actor ya colocado (la trampa de siempre) y el salto quedaría roto en silencio. Se tocan en el CDO.

`bAutoTest` (false) — 🧪 **la obra se recorre SOLA, sin manos**: cada espera humana (panel, timbre, sensor, elección) se fuerza a los `AutoTestDelay` (2 s). Es como se verificó por log. · `bDebugKey` (true) — **tecla `9`** = fuerza la espera actual (si es humana la "hace"; si no, salta el paso).

### Z - Estado interno
`Room` / `Sub` (sala y paso actual) · `WaitFor` (Name: `panel` · `door` · `vo` · `taken` · `chosen` · `arrived` · `ring` · `time` · `timer` · `none`) · `bEnding` · `bDoorArmed` · `bWinnerBound` · refs cacheadas: `AlmaRef`, `MoveRef`, `RoomsRef`, `PickerRef`, `SensorRef`, `PanelRef` (el panel vigente: primero el de la partida, después el de cada sala), `WinnerRef` (la proto ameba elegida), `DoorRef`, `BellRef`.

## 🎬 El guión, paso por paso (lo que corre de verdad)
**Hall (`Room 0`)** — `RunHallA` / `RunHallB`:
| Sub | Dispara | Espera |
|---|---|---|
| 0 | (Boot) | `panel` — el botón **Start experience** del panel de la partida |
| 1 | VO 1 (la caminata ya la arranca el propio panel) | `door` — cruzar la puerta del Hall (la abre `BP_Bell`) |
| 2 | `Alma.AppearAt(alma_hall_appear)` + VO 2 | `vo` |
| 3 | `Alma.MoveTo(alma_hall_move)` + VO 3 | `vo` |
| 4 | VO 4 + `Sensor.Appear()` | `taken` |
| 5 | VO 5 | `vo` |
| 6 | VO 7 + `Picker.Awake()` (las 5 candidatas aparecen) | `chosen` |
| 7 | VO 8 (la elegida ya viaja sola a `soul_pick_0`, lo hace `Select`) | `vo` |
| 8 | `Winner.MoveTo(soul_face)` | `arrived` |
| 9 | VO 9 | `vo` |
| 10 | `Alma.Disappear()` + `Rooms.EndStage()` → `NextRoom` | `door` |

**Salas 1-5** — `RunRoomA` / `RunRoomB` (genérico, leyendo los arrays con `Room`):
| Sub | Dispara | Espera |
|---|---|---|
| 1 | `AppearAt(alma_<n>_appear)` + `VOAppear` | `vo` |
| 2 | `MoveTo(alma_<n>_move)` + `VOMove` + **si `bPanel`:** `ShowPanel()` · **si no:** `StartStepTime` y salta a Sub 3 | `panel` / `time` |
| 3 | `StartStepTime` + `VOStep` | `time` |
| 4 | `VOPick` + `Winner.MoveTo(soul_pick_<n>)` | `vo` |
| 5 | **si `RingIndex ≥ 0`:** `Winner.DrawRing(RingIndex)` · **si no (Surrounding):** `BeginEnding` | `ring` / `timer` |
| 6 | `Winner.MoveTo(soul_face)` | `arrived` |
| 7 | `VOFace` | `vo` |
| 8 | `Alma.Disappear()` + `Rooms.EndStage()` → `NextRoom` | `door` |

**Final** (`bEnding`, Surrounding) — `BeginEnding` + `RunEnding` (🆕 rediseñado 2026-08-20):
`BeginEnding`: `Rooms.CloseRoom()` (fundido + descarga, **sin** sala siguiente) y timer = `FadeOutTime + BlackHold + EndingPause` → **6**: VO 31 (`vo`) → **7**: VO 32 + `Picker.Rearm()` = **modo compartir**: hover + gatillo SOSTENIDO agarra la ameba a la mano; soltar la devuelve; **acercarla bajo el visor la comparte** (`shared`, vía `OnShared` de la ganadora) → **8**: el guión la manda a `soul_pick_6` (`arrived`) → **9**: VO 33 (`vo`) → **10**: `Alma.Disappear()` + step game time (`time`) → **11**: `FinaleOut()` = `StartCameraFade(0→1, FinaleFadeTime, con AUDIO, hold)` + timer → `ReloadLevel()` = `OpenLevel(L_SoulCharger)`: **la obra se recarga desde 0**. ⚠ El fade es el de la cámara (`bShouldFadeAudio` apaga también la música); **falta confirmar en visor que el compositor lo muestre** — si no, el plan B es la esfera de fade.
Esperas nuevas: `shared` (humana; el autotest la fuerza con `Picker.ForceShare()`). `FinaleFadeTime` (2 s) en *C - Tiempos y tags*.

## Cómo avanza: `WaitFor` + un `Next()`
- Cada paso termina con `SetWaitFor "<x>"` + `ArmWait()` (loguea `STORY: sala r paso s espera: x` y, en autotest, arma el `Poke`).
- Cada aviso entra por su evento y **sólo avanza si coincide con lo que se espera**: `OnVOFinished_Event → if WaitFor=="vo" → Next()`; ídem `OnTaken_Event`/taken, `OnChosen_Event`/chosen, `OnFinished_Event`/panel, `HandleArrived`/arrived, `HandleRingDone`/ring, `StepTimeDone`/time, `EndingWaitDone`/timer, `CheckDoor`/door. Un aviso fuera de turno **se ignora** (por eso un VO que termina mientras se espera otra cosa no rompe nada).
- `Next()` = `WaitFor="none"`, `Sub++`, `RunStep()` → `RunHall` / `RunRoom` / `RunEnding` según `Room` y `bEnding`.

### 🚪 "Cruzamos la puerta" se mide por posición, no por tiempo
`OnLegStarted` del recorrido → `FindDoor()` (la única `BP_Door_SC` cargada: la de la sala que entra) → `bDoorArmed`. El Tick (`TickDoor → CheckDoor`) compara la **X del pawn** contra la **X de la puerta + `DoorCrossOffset`** y dispara una sola vez. Funciona igual para el Hall (la abre el timbre) y para las 5 salas (las abre la transición). Si no hay puerta cargada al arrancar el tramo (el primer tramo, antes de que exista el Hall) no arma nada.

### 🔗 Los binds (todos en el `EventGraph`, vía nodos `Assign`)
`BindAllEvt` (desde `Boot`): `Alma.OnVOFinished`, `Move.OnLegStarted`, `Picker.OnChosen`, `Sensor.OnTaken`. `BindPanelEvt`: `PanelRef.OnFinished` — se llama en `Boot` (panel de la partida) y en cada `ShowPanel` (panel de la sala, que vive en el sublevel). `BindWinnerEvt`: `Winner.OnArrived` + `Winner.OnRingDone`, **una sola vez**, al primer `OnChosen` (`bWinnerBound`).
🔴 **`AssignOnArrived` lo creó `create_node` con `declaring_class = BP_ProtoSoul_SC_C`**: el DSL resolvía el nombre al `OnArrived` de `BP_Director_Movement` (gotcha nuevo, ver abajo).

## 🧪 Cómo se prueba sin visor: `bAutoTest`
Con `bAutoTest=true` en la instancia, `ArmWait` agenda `Poke` a los `AutoTestDelay`: `panel` → `PanelRef.Finish()` · `taken` → `Sensor.Take(true)` · `chosen` → `Picker.ForceChoose()` (elige la primera como si estuviera hovereada) · `door` en el Hall → busca `BP_Bell` y, cuando el pawn dejó de caminar, `Fire()` (si aún no existe el timbre, reintenta cada segundo). Las demás esperas se resuelven solas. **Apagarlo para el visor.**

## 🧪 2026-08-21 — `DebugStartRoom`: empezar la obra en cualquier sala (CONSTRUIDO Y VERIFICADO POR LOG)
Pedido de Beltrán: *"una herramienta de debug que nos permita iniciar el juego en distintas etapas, para poder probar más rápido"*, y que **considere las cosas que ya habría hecho el usuario** (*"si quiero partir en una etapa más adelante, que automáticamente el usuario tenga una protoameba elegida y el sensor"*).

Es el mismo principio que el `DebugStartStage` del esqueleto viejo ([[BP_StageDirector]] §2026-08-14): **saltar SIEMPRE por el flujo real**, nunca con niveles de prueba paralelos.

| Valor | Comportamiento |
|---|---|
| **−1** (default, CDO **y** instancia) | Obra completa normal: panel de partida → caminata → Hall → salas. |
| **0** | Arranca **dentro del Hall**, en el paso 2 (Alma aparece): sin panel de partida, sin caminata, sin timbre. No siembra nada — el sensor y la elección se viven de verdad ahí. |
| **1..5** | Arranca **dentro de esa sala**, en el paso 1, **con todo lo que el usuario ya habría hecho**. |

**Cómo se usa:** seleccionar `Director_Story` en `L_SoulCharger` → Details → *D - Test* → `Debug Start Room` → índice de sala (0 Hall · 1 Entering · 2 Recognizing · 3 Loving · 4 Attracting · 5 Surrounding) → Play.
🔴🔴 **ESTA PALANCA LA MANEJA BELTRÁN — no la restaures.** (Pedido explícito, 2026-08-25: *"si estamos testeando ahora en hall, es medio lento tener que volver a ajustar ese valor todo el rato"*.) Si necesitás otro valor para una prueba propia, **leé el que estaba y dejalo así al terminar**; nunca la devuelvas a `−1` por prolijidad. Lo mismo con `bAutoTest`. Antes de commitear un hito, preguntarle a él en qué valor la quiere.

### Qué siembra (salas 1-5), todo con los verbos que YA existían
| Lo que el usuario habría hecho | Cómo se siembra |
|---|---|
| Tener el sensor en las manos | `Sensor.Appear()` + `Sensor.Take(true)` |
| Que las candidatas EXISTAN | 🔴 **`Picker.Awake()`** — sin esto no se ve nada, ver el bug de abajo |
| Tener su proto ameba elegida | `Picker.ForceChoose()` → dispara el **`OnChosen` real**, así que `OnChosenBody` cachea `WinnerRef` y liga sus eventos por el camino de siempre; las otras 4 candidatas se destruyen solas |
| La ameba anclada a la cara | `Winner.MoveTo(FaceTag)` |
| Los anillos de las etapas ya vividas | 🔴 **`Winner.SeedRings(Room − 1)`** (verbo nuevo en [[BP_ProtoSoul_SC]]), **no** `DrawRing` en un bucle — ver el bug de abajo |
| Estar parado en esa sala | `Move.GotoStop(Room + DebugStopBase)` — 🔴 **parada = sala + 3** (el spline tiene 3 paradas antes del Hall: −5000 · −2500 · −773) |
| La sala cargada | `Rooms.DebugJumpTo(Room)` (ver [[BP_Director_Rooms]]) |

### La cadena
```
Boot()  → ...lo de siempre... → SetTimerByFunctionName("DebugBoot", 1.0)   ← el ÚNICO nodo agregado a Boot
DebugBoot()  guarda propia: si DebugStartRoom < 0 no hace NADA (por eso Boot lo llama sin condición)
             Room = DebugStartRoom · WaitFor="none" · GotoStop · DebugJumpTo
             + timer DebugGo (DebugStartDelay)
             + si Room > 0: Sensor.Appear + Sensor.Take + Picker.Awake
DebugGo()    🔴 NO es un delay: es un POLL. Si Rooms.Phase < 3 se reagenda a 0,1 s.
             Cuando la sala entra en fase 3 (= empieza a encenderse desde el negro):
             Room>0 → ForceChoose + Winner.SeedRings(Room−1) + Winner a la cara + Sub=0 + Next()  ⇒ paso 1
             Room=0 →                                                             Sub=1 + Next()  ⇒ paso 2
```
⏱ **`Awake()` va en `DebugBoot` y `ForceChoose()` en `DebugGo`, a propósito**: así el revelado de las candidatas (que se anima en `AppearTime`) transcurre durante la carga de la sala y llega terminado. Medido: `appearT = 1` cuando arranca el guión.

🔴 **Por qué el arranque va por POLL y no por delay** (pedido de Beltrán, 2026-08-21): *"quiero que inicie cuando estamos en negro y entramos a la sala, así alcanzamos a tener los voice over de Alma al entrar en el level"*. Con un delay fijo el guión arrancaba **2,4 s después** de que la sala ya estaba encendida y el VO caía en una sala quieta. Y la carga **no** dura siempre lo mismo: entre dos corridas medidas dio **0,58 s y 1,67 s** — casi 3×. Enganchando la **fase 3** del director de salas el guión entra siempre en el mismo instante dramático, sea cual sea lo que tarde el streaming.

### Por qué `DebugBoot` se llama incondicionalmente y se guarda solo
`Boot` es un grafo **que ya existía**, y reescribirlo con `write_graph_dsl` lo duplica. Poner la rama adentro habría exigido cirugía de varios nodos. Con la guarda **dentro de `DebugBoot`**, la cirugía sobre `Boot` se reduce a **UN nodo** (`SetTimerByFunctionName` colgado del `then` de `ArmWait`, que estaba libre). El costo es un timer de 1 s que en la obra normal cae en una función que no hace nada.
- El 1,0 s es para que corra **después** del `Boot` de [[BP_Director_Rooms]], que va a 0,25 s.
- `DebugBoot` pone `WaitFor="none"`, así que la espera del panel que armó `Boot` queda desactivada. Y si además estuviera `bAutoTest`, el `Poke` agendado **relee `WaitFor` al dispararse**, así que se acopla a la espera vigente en vez de romper nada.

### ✅ Verificado por log (2026-08-21, 3 corridas en PIE)
- **Salto a la sala 3 (Loving):** `sala visible` 13:55:45.130 → `arranca el guion` **:45.464 (todavía en negro)** → `sala encendida` :47.464. O sea el VO de Alma corre **mientras** la luz sube. Anillos sembrados = 2 ✓.
- **La cadena posterior es la real:** Loving corrió los pasos 1→7, cerró sola, encadenó `transicion hacia sala 4`, el pawn **caminó** a la parada 7 y Attracting arrancó. El salto no deja la obra en un estado especial.
- **Salto a la sala 0 (Hall):** usa el Hall **precargado** (`HallInstant`, sin recargar) y cae en el paso 2. De Play a guión: **0,3 s**.
- **Cero `Accessed None`** en las dos corridas nuevas.
- ⚠ Trampas pagadas: `(CallFunction|BeginTransition Index false)` posicional chocó con `self` → keywords (`:Index`) · el parámetro de `MoveTo` es **`PointTag`**, no `Tag` · `remove_function_graph` **no libera el nombre hasta compilar** (un `add` inmediato devuelve `DebugBoot_0`, y como el timer llama **por string** eso rompe el enganche en silencio) · el `read_graph_dsl` renderiza `Class|BPSensorSoul|Appear` como `Class|BPAlmaSC|Appear` (colisión de nombres del lector, igual que el `Media|MediaPlayer|Next` que ya estaba en `OnChosenBody`): **es artefacto del lector, no del grafo** — si fuera de la otra clase el compile habría tirado error de tipo.
- 🔴 **La trampa de la instancia mordió de nuevo, y quedó medida:** con el CDO en −1, la instancia ya colocada nació en **0** → la obra habría arrancado siempre saltando al Hall. `DebugStartDelay` y `DebugStopBase`, que **no** son instance-editable, heredaron bien (0.3 y 3): control natural del mecanismo en la misma lectura.

### 🐛 Los 3 bugs del primer visor de Beltrán (2026-08-21) — todos por saltear pasos del camino real
Reporte: *"tiró una serie de errores. Probé apareciendo en Loving. Mi proto ameba no se veía. Solo el anillo rojo de recognizing. El azul tampoco lo vi."*

**1. La ameba invisible — faltaba `Picker.Awake()`.** Las 5 candidatas están colocadas y en `BeginPlay` el picker las **duerme**: `Sleep()` pone la escala del `Body` en **0**. Y `Select()` (lo que dispara `ForceChoose`) **no revela**: sólo apaga el hover, suena y llama a `MoveTo`. O sea la ameba viajaba correctamente a la cara del usuario… en escala 0. En el Hall real quien las despierta es `Awake()` (paso 6), y el salto se lo estaba salteando. ✅ Verificado midiendo el estado, no el log: `Body.relativeScale3D = 0.02` (= `Size`, el valor de autor) y `appearT = 1`.
👉 **Regla:** *"sembrar por el camino real"* significa **todos** los pasos del camino, no sólo el último. Si una función pública asume un estado previo, ese estado también hay que sembrarlo.

**2. Sólo se veía un anillo — `DrawRing` NO se puede llamar en bucle.** `DrawRing(Index)` escribe en un **slot único** (`DrawIndex = Index`, `RingReveal[Index] = 0`) y `StepRings` anima **sólo** el anillo que esté en `DrawIndex`. Dos llamadas en el mismo frame ⇒ la segunda pisa a la primera y **el primer anillo queda en reveal 0 para siempre** = invisible. Por eso se veía el de Recognizing (el último sembrado) y no el de Entering. ✅ Fix: **`BP_ProtoSoul_SC.SeedRings(Count)`**, que pone `RingReveal[i] = 1.05` (el valor final del ease de `StepRings`) y llama `PushRingMat(i)` — sin tocar `DrawIndex`, así los anillos aparecen **ya completos** y sin animación. Verificado: `ringReveal = [1.05, 1.05, …]`, `drawIndex = -1`.
👉 **Regla:** antes de llamar en bucle a una función de "animar", mirar si su estado es un slot único. `DrawRing` es un reproductor, no un setter.

**3. La catarata de `Accessed None` de la puerta — la expuso el salto, pero el bug era viejo.** [[BP_Door_SC]] hace `BeginPlay → SetTimer("Boot", 0.3)` y los materiales dinámicos (`MID_L`/`MID_R`) nacen ahí, **pero el `Tick` corre desde el frame 1** y llama `Apply`, que los lee. En la obra normal se llega caminando a la puerta mucho después de 0,3 s y nunca se nota; **el salto deja al pawn pegado a la puerta en el frame 1** y dispara el error en todos esos frames. ✅ Fix en la puerta: guarda `IsValid(MID_L)` sobre los dos `SetVectorParameterValue` de `Apply` (los dos MID nacen juntos, así que uno alcanza). Beneficia también al flujo normal.
👉 **Regla:** una herramienta de debug que teletransporta es un **test de estrés de las suposiciones temporales**. Todo lo que "siempre alcanzó a inicializarse" queda expuesto.

## 🎛️ 2026-08-24 — el sensor de mecánicas, versión FINAL del día (tras el pivote de Beltrán: sin calibración)
Cableado con el sistema de modos de [[BP_Sensor_Soul]]. La jornada pasó por dos diseños descartados (cierre por mecánica con `MechTimeout`; calibración con barra y candado del botón) que se revirtieron por pedido explícito — lo que quedó:

- **`ArmPractice`** (primera llamada de `ShowPanel`): si `Room == 1` → `Sensor.SetStage(1)` + `Sensor.bPractice = true` — **el umbral de respiración corre desde que aparecen las instrucciones**, en modo práctica. Log: `umbral activo en modo practica durante las instrucciones`.
- **`TickPractice(DT)`** (última de la cadena del Tick: `TickDebugKey → TickDoor → TickPractice`): mientras `Room==1 && WaitFor=="panel"` (guardas `IsValid` sobre sensor y panel — el `and` de K2 no cortocircuita), 🆕 (noche, v3) toma **`Sensor.BreathLevel`** gateado por **`bZonePre`** (la zona instantánea, no el umbral debounceado — mismo motivo que el orbe) y empuja `PracticeScale = FInterpTo(lerp(0.8, 2.1, nivel), 4.0)` a `PanelRef.SetPractice(S)` → **el círculo de la página de instrucciones respira con el usuario**.
- **`StartStepTime`**: print + `Sensor.SetStage(Room)` (resetea `bPractice` → la esfera del mundo aparece) + timer por sala: 🆕 **`StepTimes`** (array de 6 en *C - Tiempos y tags*, **NO instance-editable** — manda el CDO; entrada 0 o faltante = fallback a `StepGameTime`). Hoy `[0, 90, 0, 0, 0, 0]`: **Entering dura 90 s** para probar con calma, el resto sigue en 10 s — 🔴 **el cierre de etapa es SOLO por la duración definida** (decisión de Beltrán); la mecánica no cierra nada. `TickMechDone` y `MechTimeout` se **eliminaron**.
- **`StepTimeDone`**: `SetStage(-1)` (apaga mecánica y beam) + `Next()`.
- ⚠ El botón de instrucciones quedó **exactamente como el original** (sin candado; el experimento `bLocked`/`bAdvanceLocked` se revirtió y sus variables se eliminaron).
- ⚠ Trampas pagadas hoy: `(CallFunction|FindPanel _tag)` posicional choca con `self` (§179) → `:Tag` · `Utilities|Name|Equal(Name)` no es escribible → `==` (§211) · el setter cross-class de una VARIABLE lleva el valor primero → `(Class|BPSensorSoul|SetPractice :self ref :bPractice true)` · el compile sin guardar reprodujo los eventos vacíos de los `Assign` (gotcha del [[BP_BioHub]]) — limpiados y verificado `0 reaparecidos`.
- ✅ Verificado por log + medición directa en la instancia PIE (`DebugStartRoom=1` + autotest): práctica ON durante el panel (esfera oculta, `RevealT=0`), paso → `ORB: true`, 10 s → `SetStage -1` → `ORB: false`, salas 2-5 intactas, **cero `Accessed None`**.

### 🎬 2026-08-25 — la explicación de las etapas entra en el VO 3 y **manda al sensor**
- **`PlayStageIntro()`** (nueva): busca [[BP_StageIntro_SC]] por clase (vive en el sublevel del Hall), lo cachea en `IntroRef` y llama `IntroPlay()`. Se insertó **por cirugía en el sub 3 de `RunHallA`, entre `Alma.MoveTo` y el `Say(VO 3)`** — la lámina arranca cuando Alma se corre a un costado.
  ⚠ `RunHallA` **no se reescribe desde el `read`**: el lector muestra `BP_Sensor_Soul.Appear` como `Class|BPAlmaSC|Appear` (colisión de nombres) y una reescritura rompería la aparición del sensor.
- 🔴 **El sub 3 ya no espera el VO, espera la EXPLICACIÓN**: su `SetWaitFor` pasó de `"vo"` a **`"intro"`** (cambio de un literal). **`TickIntroDone`** (en el Tick, tras `TickPractice`) poll-ea `IntroRef.bIntroDone` y, cuando la animación de salida termina, hace `Next()` → sub 4 = **VO 4 + `Sensor.Appear()`**. Dependencia invertida por poll, como la ceremonia: sin nodos `Assign` y sin sus trampas.
- ✅ Verificado en PIE: `arranca la explicacion (VO 3)` → `INTRO: termino la animacion de salida` → `la explicacion termino - sigue el sensor` → `SENSOR: aparece`; pasos `3 espera: intro` → `4 espera: taken`, cero `Accessed None`.

### ❤️ 2026-08-25 — la etapa Recognizing: el sensor late en las instrucciones y el ASCENSOR cierra
La mecánica vive en [[BP_Elevator_SC]] (nuevo) + el modo 2 completado de [[BP_Sensor_Soul]]. Lo que cambió ACÁ:
- **`ArmHeart()`** (nueva): `Room==2` → `Sensor.SetStage(2)` — colgada por cirugía del **pin `else`** del branch de `ArmPractice` (que solo atendía Room==1). El sensor late (zona + zumbido + audio + `OnBeatPulse`) **desde que aparece el panel**.
- **`TickHeartFx(DT)`** (nueva, al final de la cadena del Tick: `…TickIntroDone → TickHeartFx`): mientras `Room==2 && WaitFor=="panel"` (guardas `IsValid` como `TickPractice`) empuja al panel `SetHeartFx(S, O)` con **S = 1 + 0.6·Sensor.BeatEnv** (el círculo salta con cada latido y decae) y **O = `HeartVis`** = `FInterpTo` hacia `bHeartZone` (el círculo solo se ve dentro del umbral). Var nueva: `HeartVis` (Z - Estado interno).
- **`ElevatorCue()`** (nueva): `Room==2` → busca [[BP_Elevator_SC]] y `ElvArm()`. Colgada del `then` de `BreathRingCue` al final de `StartStepTime` — el ascensor queda armado al terminar las instrucciones y arranca con el primer latido en zona.
- **`StepTimes` CDO = `[0, 90, 240, 0, 0, 0]`**: Recognizing tiene cortafuegos de **240 s**; el cierre real lo dispara el ascensor por distancia vía `StepTimeDone` (misma convivencia que el anillo de Entering — la guarda `WaitFor=="time"` evita el doble cierre; verificado: una corrida cerró por el cortafuegos a los 240.0 s exactos y otra por el ascensor).

## Trampas pagadas acá (van a `gotchas.md`)
1. **Los literales `bool` y `string`/`name` pasados a una función PROPIA se pierden** (ya se sabía de los strings; hoy también los bool: `(CallFunction|Take true)` llegó como `false`). Salidas: pasar el literal por un nodo nativo (`MakeLiteralName`, `MakeLiteralBool`) o escribir la variable antes y que la función la lea. A funciones de **otra** clase (`Class|BPSensorSoul|Take ref true`) el literal **sí** llega.
2. **`Default|CallOnX` / `Default|AssignOnX` con nombre repetido entre clases resuelve a la clase equivocada** (`OnArrived` existe en `BP_Director_Movement` y en `BP_ProtoSoul_SC`): `CallOnArrived` dentro de ProtoSoul se cableó al delegado del Movement y el compile dijo *"self is not a BP_Director_Movement_C"*. Fix: `create_node` con `declaring_class`.
3. **Un `Assign` en el DSL + un `(event Custom|X_Event …)` con el mismo nombre en la MISMA escritura → el Assign se liga a un `X_Event_0` vacío y tu cuerpo queda en un evento huérfano.** Fix por cirugía: conectar `OutputDelegate` del evento con cuerpo al pin `Delegate` del Assign y borrar los `_0`/`_1` fantasmas. O declarar el handler con OTRO nombre (`HandleArrived`) y conectarlo.
4. **`elif` se anida**: `(if A … (elif B … (elif C … (else …))))`. Como hermanos dentro del mismo `if` el parser los rechaza.
5. **Un script con errores atrapados igual se reporta como error** — pero no dispara Undo (canario verificado 44→44). Lo que sí pasa: si un `write_graph_dsl` de un lote falla y se relanza TODO el lote, los que habían salido bien se **duplican** (pasó en `BP_Alma_SC`: 24 huérfanos, limpiados con `clean_orphans.py`, `identical=true`). **Reescribir sólo lo que falló.**

## 🎵 2026-08-26 — la etapa Attracting limpia: `ArmBeam` + el cierre por SAVE MELODY
- **`ArmBeam()`** (nueva): `Room==4` → `Sensor.SetStage(4)` + **`Sensor.MaybeInput()`** (arma el IMC del gatillo para el far-grab) + `GetActorOfClass(BP_Sequencer_SC)` → `SeqIntro()` (aparecen slots, botón y la esfera de las instrucciones). Colgada **por cirugía del pin `else` del branch de `ArmHeart`** (la misma cadena `ArmPractice → ArmHeart → ArmBeam`).
- **La espera `panel` de la sala 4 se resuelve POR MECÁNICA**: no hay botón de instrucciones en `L_Attracting_SC` (se eliminó la instancia). El usuario arrastra la esfera de las instrucciones a un slot → `BP_Sequencer_SC.NotifyPlaced` → `panel.Finish()` → `OnFinished` → `Next()` como siempre. En autotest, `Poke` fuerza `Finish()` y el `TickIntro` del secuenciador completa la intro solo.
- **`StepTimes` CDO = `[0, 90, 240, 0, 300, 0]`**: Attracting tiene cortafuegos de **300 s**; el cierre real lo dispara el botón SAVE MELODY → 2 pasadas del loop → `Sequencer.TellDirector` → `StepTimeDone` (la guarda `WaitFor=="time"` de siempre). El watchdog inverso también existe: si el cortafuegos gana, el secuenciador ve `Mode != 4` y se cierra solo.
- Detalle completo del ecosistema: [[BP_Sequencer_SC]].

## 🔴🔴 2026-08-26 (tarde) — el actor `Director_Story` se PERDIÓ y se repuso
Un `execute_tool_script` con un **error de Python no atrapado** (un `TypeError` de formateo, fuera de los `T()`) disparó el Undo del editor. Ese Undo (a) revirtió **el lote entero** de writes del script (todo el script es UNA transacción) y (b) **se comió el actor `Director_Story` del persistente** — el diff contra HEAD mostró que era el ÚNICO actor perdido, y el log probó que a las 11:32 (corridas de Beltrán de la mañana) todavía existía. Un `save_assets([])` posterior grabó el nivel mutilado.
**Repuesto** (2026-08-26): `BP_Director_Story_C_0` en (−5000, 200, 0), carpeta `01 - Directores`, con `DebugStartRoom=3` / `bAutoTest=false` (los valores del tracker de ayer — ⚠ la última corrida real de Beltrán esa mañana usaba **4**: confirmar con él en qué valor la quiere), `WebOutTime=4`, y `StepGameTime=18` restaurado en CDO + instancia (se leía 10 tras el incidente).
👉 Lecciones (van a gotchas): `except BaseException` por llamada **no** protege de los errores del script mismo; y tras CUALQUIER script fallido, **verificar el actor-diff contra HEAD**, no solo contar actores.

## ✏️ 2026-08-26 (noche) — Surrounding V2: el dibujo integrado (plan: `docs/stages/surrounding-v2.md`)
- **`ArmDraw()`** (nueva): `Room==5` → `Sensor.SetStage(5)` + `bPractice=true` + `MaybeInput()`. Colgada del **pin `else` del branch de `ArmBeam`** — la cadena quedó `ArmPractice → ArmHeart → ArmBeam → ArmDraw`.
- **`TickDrawPractice()`** (nueva, al final de la cadena del Tick, tras `TickHeartFx`): mientras `Room==5 && WaitFor=="panel"`, si `Sensor.DrawTotalNow ≥ Sensor.PracticeCm` → `PanelRef.Finish()` — **el metro de práctica cierra las instrucciones** (patrón Attracting, sin botón: la instancia de `BP_InstrButton_SC` se ELIMINÓ de `L_Surrounding_SC` y el panel quedó en UNA página, `StartIndex=EndIndex=9`).
- **El cierre de la etapa lo dispara el sensor**: a los 10 m llama `StepTimeDone` (la guarda `WaitFor=="time"` de siempre). **`StepTimes` CDO = `[0,90,240,0,300,300]`** — Surrounding tiene cortafuegos de 300 s.
- **La firma**: en el **sub 9 de `RunEnding`** (VO 33, recién llegada la ganadora a `soul_pick_6`) se insertó `Sensor.ShowSignature()` (cirugía: 1 nodo + getter entre `Say` y `SetWaitFor`). El punto es el TargetPoint **`TP_signature_spot`** (tag `signature_spot`) colocado en el persistente a la derecha del punto final — **posición y ESCALA los ajusta Beltrán en el viewport** (la escala del TP es la escala de la firma).
- **`bDrawPracticeDone`** (candado, Z - Estado): sin él, `TickDrawPractice` llamaba `Finish()` ~30 veces (una por frame hasta que el panel resolvía). Se arma en `TickDrawPractice` al disparar y se resetea en `ArmDraw`. (`TickDrawPractice` se recreó con remove→compile→add; el nodo de llamada del EventTick re-resolvió solo, verificado.)
- 🆕 **2026-08-27 — la práctica cierra en SECUENCIA** (ajuste de Beltrán tras validar en gafas): al llegar a `PracticeCm` (subido a **300** = 3 m, CDO+instancia del sensor) → `TickDrawPractice` **bloquea el dibujo** (`Sensor.bDrawDone=true` — congela `TickDraw` vía DrawGate) + timer → **`PracticeClose`** (a los **`PracticeHold`** 3 s): el trazo de práctica se desvanece (`Sensor.FadeTo(0)`) + timer → **`PracticeGo`** (a los **`PracticeExit`** 3 s): `Sensor.bDrawDone=false` (re-habilita el wipe) + `PanelRef.Finish()` → StartStepTime → canvas fresco. Knobs de CDO: `PracticeHold`/`PracticeExit`.
- 🆕 **El cierre de los 10 m también es en secuencia**: `DrawFinish` del sensor ya NO llama `StepTimeDone` directo — corta la mecánica, disuelve, y un timer (`DrawFadeTime`+0.4) dispara **`DrawClosed`** → recién con el dibujo desvanecido del todo llama `StepTimeDone` y arranca la carga.
- ✅ Verificado por robot con timestamps exactos (2026-08-27): bloqueo → +3.0 s desvanece → +3.0 s cierre → dibujo libre → completo → +2.9 s → carga. Cero errores.
- 🆕 **2026-08-27 (3ª tanda) — el panel de Surrounding entra tarde y sale con el trazo:**
  - **`ShowPanelWait()`** (nueva, reemplaza a `ShowPanel` en el sub 2 de `RunRoomA` para TODAS las salas): si `Room==5` → `SetTimer("ShowPanel", PanelDelay)`; si no → `ShowPanel()` directo (las salas 1/2/4 no cambian). Así el widget **y** el modo dibujo (que se arma dentro de `ShowPanel` → `ArmDraw`) entran **`PanelDelay` = 5 s (CDO)** después del VO, dándole a Alma tiempo de llegar a su posición.
  - **`PracticeHide()`** (nueva, llamada desde `PracticeClose`): `WaitFor="none"` + `PanelRef.Finish()`. El widget arranca su salida **junto con el fade del trazo**; poner `WaitFor="none"` hace que el `OnFinished` del panel (que llega ~0.5 s después, su `ExitTime`) **se ignore** y no adelante el guión.
  - **`PracticeGo`** ya no llama `Finish()`: ahora hace `Sensor.bDrawDone=false` + **`Next()`** (avanza el guión a mano, con el trazo ya desvanecido). Como el `Next→StartStepTime→SetStage(5)` corre en el MISMO frame que el desbloqueo, no queda ventana para que el `bDrawHeld`/`bStroking` viejos disparen un zumbido — era el "pulso háptico entre las instrucciones y la mecánica" que reportó Beltrán.
  - ✅ Robot, timestamps: paso 2 → +5.0 s panel+modo → práctica → bloqueo → +3.0 s (fade del trazo **y** salida del panel juntos) → +3.0 s desbloqueo+`Next`+canvas fresco, todo en el mismo ms. Cero `Accessed None`.
  - 🎚️ **Afinado, 2ª pasada de Beltrán**: `PanelDelay` **5 → 2.5 s** (5 se sentía eterno). Se probó igualar la salida subiendo el `ExitTime` del panel a 2.5 y **salió mal**: 🔴 **`ExitTime` maneja las DOS animaciones del panel** — `StepShow` (agrandarse) y `TickLeave` (achicarse) usan el mismo `1/max(ExitTime,0.05)`, así que la entrada quedó lentísima.
  - 🎚️ **3ª pasada — la buena**: `ExitTime` de vuelta en **0.5** (entra y sale como los otros paneles) y el que se acelera es el **fade del trazo de práctica**: nuevo `PracticeFadeTime` (0.5) en el sensor + `FadeFast()`, que `PracticeClose` llama en lugar de `FadeTo(0)`. La disolución final sigue lenta (`DrawFadeTime` 2.5) porque `FadeTo` reescribe la velocidad. También `PracticeExit` **3 → 1.5 s** (con el fade en 0.5 s, 3 s dejaban aire muerto). Medido por robot: panel fuera **0.50 s**, desbloqueo **1.50 s** después, y la disolución final intacta en **2.9 s**.
- ✅ Ciclo completo verificado 3× — la última con **el ROBOT dibujando de verdad** (rutina 3 de [[BP_Robot]]): práctica cierra el panel por mecánica (1 print), 10 m cierran la etapa (~20 s, sin cortafuegos), firma con el dibujo real que **sobrevive al paso 10** (guardas `bDrawDone` del sensor), `FIN del guion`, cero `Accessed None`. Flags restauradas (`DebugStartRoom=3`, `bAutoTest=false`, `StepTimes[5]=300`, robot OFF).

## TODO
- [ ] 🔴 **Visor**: hover real de las 5, toma del sensor con la mano, el hold del panel y del timbre.
- [ ] 🔴 **Visor Surrounding V2**: dibujar de verdad (trazo, paleta, práctica de 1 m, cierre a los 10 m, la firma) — y de paso el F0 pendiente (el look de la cinta plana).
- [ ] Confirmar con Beltrán el valor de `DebugStartRoom` (quedó en 3; su última corrida usaba 4 para testear Attracting).
- [ ] Los puntos `alma_<sala>_appear` están **en el centro de cada sala (x=0,1500…, z=150), justo donde se para el pawn** → Alma aparece encima de la cabeza. Moverlos (son datos de autor de Beltrán; no se tocaron).
- [ ] Apagar `bDebugKey` en la obra final.
- [ ] Persistir la elección / el arco final (VO 33 es el último paso; no hay créditos ni cierre).


## 🕸️ 2026-08-26 — enganche de la red neuronal de Loving (`CloseStageFX`)
**Qué se agregó:** en `StepTimeDone` el `Next()` final se reemplazó por **`CallFunction|CloseStageFX`** (cirugía por nodos, 1 nodo creado + 1 borrado + 1 cable).

```
(fn StepTimeDone ()
  (if (WaitFor == "time")
    (Sensor.SetStage -1)
    (CallFunction|CloseStageFX)))     ; <- antes era (Next)
```

`CloseStageFX` busca [[NS_NeuralWeb_SC]] con `GetActorOfClass`; **si existe** llama su `WebOut()` (fade suave) y programa el avance con `SetTimerbyFunctionName(self, "Next", WebOutTime)`; **si no existe llama `Next()` directo**. 👉 Por eso **no hace falta condicionar por sala**: la red solo está colocada en `L_Loving_SC`, así que las otras 5 salas se comportan exactamente igual que antes (el único costo es un `GetActorOfClass` por cierre de etapa).

**Variable nueva:** `WebOutTime` (float, 4 s, categoría *C - Tiempos y tags*). ⚠ **Nació en 0 en el actor ya colocado** — la trampa de siempre con las instance-editable nuevas; hay que setearla en la instancia además del CDO.

🔴 **`StepGameTime` se subió de 10 a 18 s** porque la red nacía ~8 s después de arrancar el step time y solo vivía 1,7 s. Con 18 vive 12,7 s. **Es un valor GLOBAL, no por sala**: alarga el cortafuegos de las 5 salas. Inocuo en Entering y Recognizing (cierran por su propia mecánica), pero si Loving necesita un tiempo distinto al resto hay que convertirlo en **array por sala**.

**Verificado por log en una corrida real** (`DebugStartRoom=3`, `bAutoTest` temporal): VO 21 → nace la red → step time → sale → se destruye → paso 4 (desprendimiento de la proto ameba) → paso 5 (la carga). Las flags de debug se restauraron a como estaban (`DebugStartRoom=3`, `bAutoTest=false`).


## 🆕 2026-08-27 — el retrato entra en el sub 6 de `RunEnding` (F2 del plan de cierre)
Cirugía mínima, **un nodo insertado y un valor de pin cambiado**; el resto de `RunEnding` no se tocó.

```
sub 6 (antes):  Say(VOEnd1)  →  WaitFor "vo"    → ArmWait
sub 6 (ahora):  Say(VOEnd1)  →  ShowPortrait()  →  WaitFor "timer" → ArmWait
```

**`ShowPortrait()`** (función nueva): arma el timer de **`PortraitHold`** hacia `EndingWaitDone`, encuentra
el [[BP_Portrait_SC]] por clase (lo cachea en `PortraitRef`) y le llama `Show(WinnerRef)`.

🎛️ **`PortraitHold` = 20 s**, instance-editable — es "el rato de contemplación" del paso 4 del plan.
⚠ Se puso **en la instancia además de en el CDO**: las variables instance-editable **nacen en 0** en un
actor ya colocado, y el `BP_Director_Story_C_0` del nivel tenía `PortraitHold = 0`.

🔴 **La espera pasó de `"vo"` a `"timer"`**: el VO 31 ahora suena **dentro** de los 20 s en vez de
mandarlos. Si el VO llegara a durar más, subir `PortraitHold`.

⚠ **El sub 9 sigue llamando a `ShowSignature()`** y no se tocó. Con el flujo nuevo la firma ya apareció en
el sub 6 (la dispara el retrato), así que esa segunda llamada la reubica en el mismo TargetPoint — es un
no-op visual. Si Beltrán decide que el dibujo tiene que quedarse atrás cuando el alma viaja a
`soul_pick_6`, hay que **sacar ese nodo del sub 9**.

⚠ `DebugStartRoom` (hoy **5**) y `bAutoTest` (hoy **false**) son flags de Beltrán: **no se tocaron**.


## 🆕 2026-08-27 — el archivo se escribe al compartir (F3 del plan de cierre)
En el **sub 8** de `RunEnding` (el paso que corre cuando llega el aviso `shared`) se insertó
**`SaveMyPortrait()`** ANTES del `MoveTo`: encuentra el [[BP_SoulArchive_SC]] por clase y le llama
**`AppendMeFromWorld()`**, que recolecta del mundo y escribe la entrada en el `.sav`.
Un nodo insertado; el resto del sub 8 sin tocar.

✅ **Verificado en una corrida de autotest de punta a punta (2026-08-27)**, con los tiempos del log:
```
14:57:26  paso 5 espera: timer                          (5º anillo)
14:57:32  STORY: aparece el retrato                     ← ShowPortrait
14:57:32  paso 6 espera: timer                          ← antes esperaba "vo"
14:57:36  paso 7 espera: shared                         ← +4 s = PortraitHold
14:57:38  STORY: mi retrato queda guardado en el archivo ← SaveMyPortrait
14:57:38  ARCHIVO: entre en la constelacion con indice 19
14:57:38  paso 8 espera: arrived
14:57:42  paso 9 espera: vo
```
Cero `Accessed None`. El `.sav` ganó su entrada por el camino real del director.

### 🎛️ `StepTimes[5]` bajado de 300 a **20 s** (pedido de Beltrán, 2026-08-27)
Es el **cortafuegos** de Surrounding: cuánto espera el paso 3 antes de seguir solo si el dibujo no
termina por mecánica. Con 300 s cada prueba en PIE tardaba 5 minutos.
🔴 **Es un valor de PRUEBA: hay que volver a subirlo antes de empaquetar.** Palabras de Beltrán:
*"ya con el juego listo las alargamos"*.
⚠ **`StepTimes` vive en el CDO, no en la instancia**: `set_properties` sobre
`BP_Director_Story_C_0` **falla** (*"the following properties could not be set: StepTimes"*), y hay que
escribirlo en `Default__BP_Director_Story_C`. La instancia lo lee de ahí.
⚠ `StepTimes[4]` (Attracting) **sigue en 300**, por si también molesta.


---

## 2026-08-27 (F4 + F5) — `RunEnding` pasa de 6 a **13 pasos**

`RunEnding` se **reescribió entero** (remove → compile → add → write; los pasos 6-8 quedaron
idénticos). Los pasos nuevos son el 9, el 10 y el 11:

| Sub | Qué pasa | Espera |
|---|---|---|
| 6 | VO 31 + `ShowPortrait()` | `timer` (`PortraitHold`, 20 s) |
| 7 | VO 32 + `Picker.Rearm(tag)` = modo compartir por gesto | `shared` |
| 8 | `SaveMyPortrait()` + la ganadora viaja a `soul_pick_6` | `arrived` |
| **9** | 🆕 **`ShowConstellation()`** → `Constellation.Build()` | `timer` (**`ConstHold`**, 10 s) |
| **10** | 🆕 **`StartExplore()`** → `Constellation.StartExploring()` | `timer` (**`ExploreSeconds`**, 60 s) |
| **11** | 🆕 VO 33 + **`StopExplore()`** = `StopExploring()` + `FadeOut()` | `vo` |
| 12 | `Alma.Disappear()` + `StartStepTime()` | `time` |
| 13 | `FIN del guion` + `FinaleOut()` → `ReloadLevel()` | — |

**Variables nuevas** (`C - Tiempos y tags`, instance-editable): `ConstHold` (10 s) y `ExploreSeconds`
(60 s). Más `ConstRef` (interna).

🔴 **Se sacó `Sensor.ShowSignature()` del viejo paso 9.** Ahora la firma la muestra el **retrato**
(`BP_Portrait_SC.PlaceDraw`, paso 6) y después la reusa la exploración para el dibujo del vecino.
Llamarla de nuevo al aparecer la constelación habría vuelto a encender el dibujo propio justo cuando la
ameba ya se fue.

✅ **Corrida completa por autotest, con cada perilla clavada** (2026-08-27):
```
15:43:36  paso 6  retrato            15:43:58  paso 10 EXPLORACION   +10,0 s
15:43:42  paso 7  compartir  +6,0 s  15:44:23  paso 11 VO 33         +25,0 s
15:43:44  paso 8  llegada            15:44:33  paso 12 step time
15:43:48  paso 9  CONSTELACION       15:44:53  STORY: FIN del guion  +20,0 s
```
Y en el medio: `CONSTELACION: mi ameba ya viajo sola - salteo su entrada` →
`cielo completo, estrellas = 19` (las 19 guardadas + la propia = 20). Cero `Accessed None`.

### ⚠ Trampas de esta reescritura
- **`CallFunction|X` con parámetros va con KEYWORDS.** Posicional, el primer argumento se enchufa al pin
  `self`: *"Could not connect pin VOEnd1 to self"* al escribir `(CallFunction|Say (GetVOEnd1))`.
  Lo correcto es `(CallFunction|Say :Index (GetVOEnd1))`.
- **El keyword tiene que ser el nombre REAL del pin**, que el error lista: `Rearm` lo llama **`NewTag`**,
  no `ChosenTag`.
- **`remove_function_graph` → `add_function_graph` sin `compile_blueprint` en el medio devuelve
  `RunEnding_0`.** Y el compile del medio **falla** ("Could not find a function named RunEnding"):
  ese error es esperado y hay que dejarlo pasar. Al re-agregar con el nombre bueno, `RunStep`
  **se re-resuelve solo**.
- 🔴 **`ConstHold` y `ExploreSeconds` nacieron en CERO en la instancia colocada** (como pasa siempre con
  las instance-editable nuevas). Hay que escribirlas también en `BP_Director_Story_C_0`.


---

## 2026-08-28 — el cierre tardaba 5 minutos: el paso 12 reusaba el reloj de la ETAPA

**Reporte de Beltrán tras probar el APK:** *"llegué al final y se quedó eternamente con la ameba al frente
y nunca reinició"*. Después, probando otra vez: *"ahí vi que se reseteó, pero se demoró muchos minutos"*.

### 🔬 Cómo se encontró: se bajó el log DEL VISOR
No hizo falta reproducirlo ni adivinar. El APK de Development escribe su log en el dispositivo:
```
adb pull /sdcard/Android/data/com.almadigital.soulcharger/files/UnrealGame/VR_Test/VR_Test/Saved/Logs/VR_Test.log
```
y ahí estaba la corrida real, con el minuto exacto en que se quedó:
```
15:19:09  ALMA: termino VO 33
15:19:10  STORY: step game time de 300.0      <-- el paso 12 armó una espera de 300 s
15:19:10  STORY: sala 5 paso 12 espera: Time
```

### La causa
El sub 12 llamaba a **`StartStepTime()`**, que es el reloj de las ETAPAS: toma `StepTimes[Room]` y con
`Room = 5` eso es **300 s = los 5 minutos de Surrounding**. Además `StartStepTime` hace
`SetStage(SensorRef, Room)` — o sea que **volvía a armar el modo dibujo** justo en el cierre.

### El arreglo
Función nueva **`OutroBeat()`**, que reemplaza a `StartStepTime` **sólo en el sub 12** (cirugía de un nodo:
`K2Node_CallFunction_28` fuera, `CallFunction|OutroBeat` en su lugar, mismo exec de entrada y de salida):
```
(fn OutroBeat ()
  (SetTimerbyFunctionName self "StepTimeDone" (max OutroHold 0.5))   ; MISMO camino, sólo que corto
  (IsValid WinnerRef :"Is Valid" (Class|BPProtoSoulSC|Disappear WinnerRef)))
```
🔑 **Se conserva el camino `WaitFor = "time"` → `StepTimeDone` → `CloseStageFX` → sub 13 → `FinaleOut`**,
que es el que la corrida de Beltrán demostró que llega hasta la recarga. Lo único que cambia es **cuánto
espera** y que **la ameba del usuario también se apaga**.

**`OutroHold`** (float, `C - Tiempos y tags`, editable) = **4 s**. El cierre completo tras el VO 33 pasa de
**~305 s a ~6,5 s**: 4 de `OutroHold` + `CloseStageFX` (inmediato, no hay NeuralWeb en Surrounding) +
2 de `FinaleFadeTime` + 0,5 de la recarga.

### 🔴 Por qué la ameba se quedaba a la vista
`StopExplore` (sub 11) apaga **la constelación** (`FadeOut` → `FadeLoop` → `KillStars`), pero la ameba del
usuario **no es parte de `Spawned`** — viajó sola a `soul_pick_6` y la constelación la saltea a propósito
(`"mi ameba ya viajo sola - salteo su entrada"`). Nadie la apagaba. Ahora la apaga `OutroBeat`.
⚠ En la corrida de Beltrán el archivo tenía **una sola entrada** (instalación nueva), así que
`CONSTELACION: no quedo ninguna estrella en el cielo` — la única ameba en pantalla era la suya.

### ⚠ Dos trampas del camino
- **`Class|BPAlmaSC|Disappear` NO acepta un `WinnerRef`** (*"Could not connect pin WinnerRef to self"*)
  aunque `Class|BPAlmaSC|MoveTo` sí lo acepta en el sub 8. El id bueno es **`Class|BPProtoSoulSC|Disappear`**,
  que `find_node_types` lista al lado del otro. El read posterior igual lo etiqueta como el de Alma.
- **`OutroHold` nació en CERO en la instancia** del director. Con el `max(…, 0.5)` no rompe, pero el cierre
  habría sido de medio segundo. Séptima vez.

### ⛔ Por qué NO se reescribió `RunEnding` entero
El read de esa función devuelve **`(Class|BPFinale|StartExplore)`** en el sub 10 — un id mal etiquetado por
colisión de nombres, que escrito de vuelta llamaría a la función de OTRO Blueprint. Por eso el cambio fue
cirugía de un solo nodo y no una reescritura.
