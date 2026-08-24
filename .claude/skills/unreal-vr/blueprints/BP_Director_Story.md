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

**Cómo se usa:** seleccionar `Director_Story` en `L_SoulCharger` → Details → *D - Test* → `Debug Start Room` → índice de sala (0 Hall · 1 Entering · 2 Recognizing · 3 Loving · 4 Attracting · 5 Surrounding) → Play. 🔴 **Volver a −1 al terminar** (y así queda commiteado siempre).

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

## Trampas pagadas acá (van a `gotchas.md`)
1. **Los literales `bool` y `string`/`name` pasados a una función PROPIA se pierden** (ya se sabía de los strings; hoy también los bool: `(CallFunction|Take true)` llegó como `false`). Salidas: pasar el literal por un nodo nativo (`MakeLiteralName`, `MakeLiteralBool`) o escribir la variable antes y que la función la lea. A funciones de **otra** clase (`Class|BPSensorSoul|Take ref true`) el literal **sí** llega.
2. **`Default|CallOnX` / `Default|AssignOnX` con nombre repetido entre clases resuelve a la clase equivocada** (`OnArrived` existe en `BP_Director_Movement` y en `BP_ProtoSoul_SC`): `CallOnArrived` dentro de ProtoSoul se cableó al delegado del Movement y el compile dijo *"self is not a BP_Director_Movement_C"*. Fix: `create_node` con `declaring_class`.
3. **Un `Assign` en el DSL + un `(event Custom|X_Event …)` con el mismo nombre en la MISMA escritura → el Assign se liga a un `X_Event_0` vacío y tu cuerpo queda en un evento huérfano.** Fix por cirugía: conectar `OutputDelegate` del evento con cuerpo al pin `Delegate` del Assign y borrar los `_0`/`_1` fantasmas. O declarar el handler con OTRO nombre (`HandleArrived`) y conectarlo.
4. **`elif` se anida**: `(if A … (elif B … (elif C … (else …))))`. Como hermanos dentro del mismo `if` el parser los rechaza.
5. **Un script con errores atrapados igual se reporta como error** — pero no dispara Undo (canario verificado 44→44). Lo que sí pasa: si un `write_graph_dsl` de un lote falla y se relanza TODO el lote, los que habían salido bien se **duplican** (pasó en `BP_Alma_SC`: 24 huérfanos, limpiados con `clean_orphans.py`, `identical=true`). **Reescribir sólo lo que falló.**

## TODO
- [ ] 🔴 **Visor**: hover real de las 5, toma del sensor con la mano, el hold del panel y del timbre.
- [ ] Los puntos `alma_<sala>_appear` están **en el centro de cada sala (x=0,1500…, z=150), justo donde se para el pawn** → Alma aparece encima de la cabeza. Moverlos (son datos de autor de Beltrán; no se tocaron).
- [ ] Apagar `bDebugKey` en la obra final.
- [ ] Persistir la elección / el arco final (VO 33 es el último paso; no hay créditos ni cierre).
