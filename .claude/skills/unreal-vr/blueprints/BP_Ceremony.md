# BP_Ceremony — la ceremonia de carga (Core/Flow/)

## Purpose
El sistema 1.b del plan del guión: **UN sistema que corre 5 veces**, al cerrar cada etapa y **antes de la puerta**.
```
la proto ameba se desprende del slot del HUD → viaja suave al ChargeSpot de la sala
+ VO de felicitación + SCharger + se dibuja el anillo del color de la etapa alrededor
+ la barra del HUD sube a n×20%  →  vuelve suave al slot con sus anillos acumulados
```
Los anillos **se acumulan**: la etapa n dibuja el anillo n−1 y los anteriores siguen visibles.

## Status
🟢 **Ciclo completo verificado por log en PIE (2026-08-14, salto `DebugStartStage=3`)**, cero `Accessed None`. ⬜ Falta: visor, clips de audio reales, arte de los anillos, y la carga final (etapa 5 → 100% + disolución del HUD).

## 🔴🔴 Por qué el director NO llama a la ceremonia: el pedido va por VARIABLE
El registro de nodos del MCP **no ve las funciones de una clase de BP creada en la misma sesión** (gotcha conocido): desde `BP_StageDirector` sólo aparecían `Class|BPCeremony|Get/SetDefaultSceneRoot`, nunca `RunCeremony`. Reiniciar el editor lo arreglaría, pero se lleva puesto el MCP.
**La solución es mejor que el workaround: se invirtió la dependencia.**
| Lado | Qué hace |
|---|---|
| **Director** (no conoce la ceremonia) | `MaybeCeremony` deja el pedido en su propia variable **`CeremonyRequest`** = StageIndex, marca `bCeremonyOpen` y agenda su cortafuegos. **Cero referencias a `BP_Ceremony`.** |
| **Ceremonia** (conoce al director) | Cachea el director en BeginPlay, **poll de 0,2 s** (`WatchDirector`), y al ver `CeremonyRequest >= 1` corre. Al terminar llama `Class|BPStageDirector|CeremonyDone`. |

Ventaja lateral: el director sigue funcionando **si la ceremonia no existe** (el cortafuegos cierra igual, ver abajo).
🔴 La ceremonia es un **actor COLOCADO en `L_Persistent`** (label `Ceremony`), no un spawn — así el director tampoco necesita la clase para crearla.

## El contrato con el director (dónde se engancha)
`EndStage` del director quedó así (la ceremonia se mete **entre la muerte de la etapa y el atenuado**, o sea antes de que se revele la puerta):
```
EndStage → KillStage → MaybeCeremony
                        ├─ es etapa (RoomKinds[StageIndex]==1)  → OpenCeremony  (pide y espera)
                        └─ no es etapa (Hall/final)             → AfterCeremony (cierre directo)

AfterCeremony (custom event) → DimAndReveal → RefreshLastRoom → CloseOrFinish   ← la cadena vieja, intacta
```
- **`CloseCeremonyOnce`** es el guardián de "una sola vez": tanto `CeremonyDone` (la ceremonia avisó) como `CeremonyGuard` (cortafuegos) pasan por él, y sólo dispara `AfterCeremony` si `bCeremonyOpen` sigue en true.
- **`CeremonyMaxWait` = 25 s** (CDO; la instancia lo hereda — **no es instance-editable a propósito**, para no caer en la trampa de "instance-editable nace en cero", que haría disparar el cortafuegos al instante).

## Los ChargeSpot — un TargetPoint por sala, DENTRO de su mapa
Patrón `AlmaSpawn` calcado: **un `BP_Anchor`** (que hereda de `TargetPoint`, y es invisible en juego) con tag **`ChargeSpot`**, guardado **dentro de cada `L_Room_*`**, no en el persistente (un tag compartido en el persistente contaminaría todas las salas).

| Sala | Posición del ChargeSpot | = sala + |
|---|---|---|
| Hall | (110, 0, 140) | (110, 0, 140) |
| Entering | (1310, 0, 140) | idem |
| Recognizing | (2510, 0, 140) | idem |
| Loving | (3710, 0, 140) | idem |
| Attracting | (4910, 0, 140) | idem |
| Surrounding | (6110, 0, 140) | idem |

**Para moverlo, se arrastra el TargetPoint en el mapa de la sala — cero código.** El pawn se para en la X de la sala, así que 110 cm es "un poco más allá del brazo" y 140 cm de altura lo deja apenas debajo de la línea de ojos (misma lógica que el `PitchDeg` negativo de la ameba).
⚠ **Si no hay ChargeSpot, NO hay callejón sin salida**: `FallbackSpot` calcula un punto `FallbackAhead` (110 cm) delante de la cámara con `FallbackDrop` (−15) y **loguea `CEREMONIA: FALTA el TargetPoint ChargeSpot en esta sala`**.

## Registro de variables
| Variable | Default | Rol |
|---|---|---|
| `DirRef` | — | El director, cacheado en BeginPlay (`CacheStageDirector`). Es la única vía de ida y vuelta. |
| `SoulRef` | — | La proto ameba **HUD**. `CacheCeremonySoul` recorre TODAS las `BP_ProtoSoul` del mundo y se queda con la que tiene `bIsHUD` (las candidatas del Hall nunca la confunden). |
| `HudRef` | — | El `BP_SoulHUD`, para `SetCharge`. Si no está, se loguea y la ceremonia sigue **sin barra** (no aborta). |
| `SpotLoc` | — | Destino del viaje, resuelto en `FindSpot`. |
| `bHasSpot` | false | Si salió del TargetPoint (true) o del fallback (false). Diagnóstico. |
| `StageIdx` | — | La etapa que cierra (1..5). Índice de anillo = `StageIdx − 1`. |
| `bDone` | false | Fin de la ceremonia. Lo lee el log; el aviso real al director es la llamada, no este flag. |
| `bRunning` | false | Antirebote del poll: evita re-arrancar mientras corre. Se apaga **después** de avisar al director (orden importante: si se apagara antes, el poll podría re-disparar en el mismo pedido). |
| `TravelTime` | **2.2 s** | Viaje ameba → ChargeSpot. |
| `RingTime` | **2.6 s** | Cuánto tarda en dibujarse el anillo **y** en subir la barra (van juntos a propósito). |
| `HoldTime` | **1.2 s** | Beat de contemplación con el anillo ya completo. |
| `ReturnTime` | **2.0 s** | Vuelta al slot. Total de la ceremonia ≈ **8,3 s**. |
| `FallbackAhead` / `FallbackDrop` | 110 / −15 | El punto de emergencia frente a la cámara. |
| `ChargeFrom` / `ChargeTo` | — | Rampa de la barra: `(n−1)×0.2` → `n×0.2`. |
| `RampElapsed` | 0 | Estado de la rampa (paso de 0,1 s). |
| `VoClips` | [] | 🔊 **Placeholder data-driven (decisión #8 del guión)**: array de `SoundBase` indexado por etapa. Vacío = silencio + `AUDIO: falta clip VO de la etapa N`. **Llenar el array = tener audio, cero código.** |
| `ChargeSfx` | vacío | Idem para **SCharger**. Vacío = `AUDIO: falta clip SCharger`. |

## Estructura de grafos
- **`EventBeginPlay`** — `CacheStageDirector` · timer loop `WatchDirector` 0,2 s.
- **`WatchDirector` → `PollRequest(D)` → `TakeRequest(D)`** — el poll con el guard de validez extraído a función (regla del multi-exec).
- **`RunCeremony(Index)`** — setea índice/rampa · `CacheCeremonySoul` · `CacheCeremonyHud` · `FindSpot` · `PlayVo` · `StartTravel`.
- **`StartTravel`** — `Soul.LeaveHud()` (detach KeepWorld) · `Soul.TravelToPoint(SpotLoc, TravelTime)` · timer `OnArrived`. Si no hay ameba: loguea y `Finish` (sin colgar el cierre).
- **`OnArrived`** — `VerifySpot` (aserción) · `PlayCharger` · `StartRing` (`Soul.DrawRing(StageIdx−1, RingTime)`) · timer loop `ChargeStep` 0,1 s · timer `OnCharged` a `RingTime + HoldTime`.
- **`ChargeStep` → `ApplyCharge(A)`** — `Hud.SetCharge(lerp(ChargeFrom, ChargeTo, A))`.
- **`OnCharged`** — limpia el timer de la rampa · `ApplyCharge(1.0)` (cierra el redondeo) · `StartReturn`.
- **`StartReturn`** — `Soul.ReturnToHud(ReturnTime)` · timer `OnFinished` a `ReturnTime + 0.3`.
- **`OnFinished` → `Finish` → `NotifyDirector`** — `bDone=true` · `Director.CeremonyDone()` · `bRunning=false`.

## 🧪 Aserción espacial: `VerifySpot`
Al llegar, loguea `CEREMONIA POSE: distancia ameba-ChargeSpot cm = ...`. **Medido: 0.0** (llegada exacta al TargetPoint). Es el mismo patrón que `VerifyHudPose`/`VerifySoulPose`, y es lo que convierte "el log dice que llegó" en "llegó".

## ✅ Verificado por log (2026-08-14, `DebugStartStage=3`, corrida completa)
```
17:11:24.8  DIR: pedida la ceremonia de carga de la etapa 3
17:11:25.0  CEREMONIA: arranca la carga de la etapa 3
17:11:25.0  CEREMONIA: ChargeSpot de la sala en X=3710 Y=0 Z=140     ← el TargetPoint del mapa
17:11:25.0  AUDIO: falta clip VO de la etapa 3                        ← placeholder, no rompe
17:11:25.0  SOUL: se desprende del slot del HUD
17:11:25.0  SOUL: viaja al ChargeSpot X=3710 Y=0 Z=140
17:11:27.2  CEREMONIA: la ameba llego al ChargeSpot   (2,2 s = TravelTime exacto)
17:11:27.2  CEREMONIA POSE: distancia ameba-ChargeSpot cm = 0.0       ← aserción espacial
17:11:27.2  AUDIO: falta clip SCharger
17:11:27.2  SOUL: empieza a dibujarse el anillo 2
17:11:29.8  SOUL: anillo completo - anillos acumulados = 3            (2,6 s = RingTime exacto)
17:11:31.0  CEREMONIA: anillo y barra completos                       (+HoldTime)
17:11:33.3  CEREMONIA: la ameba volvio al slot con sus anillos
17:11:33.3  CEREMONIA: terminada - carga = 0.6   ·   DIR: la ceremonia aviso que termino
```
**Cero `Accessed None`.** Sembrado previo correcto: `SOUL: anillos sembrados = 2` + `HUD: carga 0.4` (la barra sube 0.4 → 0.6 en la rampa, en pasos de 0,1 s).
**El otro camino también medido** (`DebugStartStage=0`): `DIR: sala sin ceremonia de carga - cierre directo` y, en el mismo milisegundo, `DIR: fin de sala - baja la luz` — el Hall no pide ceremonia y la cadena vieja sigue intacta.
⚠ **Lo verificado son DOS caminos, no cinco**: la etapa **3** (con ceremonia, 3 corridas idénticas) y el **Hall** (sin ceremonia). Las etapas 1/2/4/5 corren exactamente el mismo código con otro índice — pero **eso es un argumento, no una medición**: si alguna se comporta raro, mirar primero su `ChargeSpot` y su `RingColors[n]`.

## ⚠ Trampas pagadas al construirlo (2026-08-14)
1. 🔴🔴 **El DSL resolvió `CacheSoul`/`CacheHud` a funciones HOMÓNIMAS de OTROS Blueprints** (`Class|BPSelfTest|CacheSoul`, `Class|BPSoulChoice|CacheHud`) — compiló en verde y habría corrido contra el objeto equivocado. **Lo delató el `read_graph_dsl` posterior al write.** Fix: renombrar a `CacheCeremonySoul`/`CacheCeremonyHud`. Misma trampa con `CacheDirector` → `Class|BPDebugDirector|CacheDirector` (renombrada a `CacheStageDirector`). **Regla: nombres de función ÚNICOS entre Blueprints del proyecto.**
2. **Args de expresión a funciones propias exigen keyword** (`:A a`, `:D d`, `:P p`, `:Index i`): el posicional intenta conectarse al pin `self` y el write falla con *"Could not connect pin X to self"*. Con literales simples el posicional anda. (El write falló limpio y dejó sólo el `FunctionEntry` — verificado con `find_nodes`.)
3. **`Variables|Getareferencetoself`**, no `Utilities|...` — el `SetTimerByFunctionName` creado por cirugía necesita ese nodo en el pin `Object` o queda en 0 y el timer no dispara.

## TODO
- [ ] 🔴 **Visor**: los tiempos (2,2 / 2,6 / 1,2 / 2,0) son de escritorio; el ritmo de una ceremonia se juzga con el casco puesto.
- [ ] Los **clips reales**: llenar `VoClips` (VO 10, 13, 19, 23 + el de Entering) y `ChargeSfx`.
- [ ] **La carga final** (etapa 5): 100%, anillos girando, Niagaras de vortex y **disolución animada del HUD** (guión acto 8). Hoy la etapa 5 corre la ceremonia normal.
- [ ] Haptics: el pulso al completar el anillo (patrón "selección" del framework 1.d).
- [ ] Alma: hoy sigue visible durante la ceremonia (el `HideAlma` corre después, en `DimAndReveal`) — es lo correcto para el VO de felicitación, confirmar con Beltrán.

## Relacionados
[[BP_ProtoSoul]] (dueña del viaje y de los anillos) · [[BP_SoulHUD]] (`SetCharge`) · [[BP_StageDirector]] (`CeremonyRequest`/`CeremonyDone`) · `BP_Anchor` (el TargetPoint del ChargeSpot) · `M_SoulRing`
