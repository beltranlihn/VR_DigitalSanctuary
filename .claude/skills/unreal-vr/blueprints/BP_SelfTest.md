# BP_SelfTest — batería de aserciones por log (Core/Debug/)

## Purpose
Verificar **funcionamiento** sin visor y sin que nadie esté frente a la máquina. Corre una batería de aserciones en PIE y las loguea con veredicto:

```
TEST RUN: arranca la bateria
TEST PASS: <nombre>
TEST FAIL: <nombre>
TEST SKIP: <nombre>
TEST SUMMARY: 15 pass, 0 fail, 0
```

Nació el 2026-08-11 de un pedido concreto de Beltrán: *"ve si puedes armar maneras en las que puedas probar tú sin necesidad de que yo me ponga las cajas. Lo que sea de sentir cómo funciona, eso sí lo puedo ver yo. Pero de funcionamiento, trata de probarlo tú."*

🔴 **La división de trabajo que esto formaliza:** lo que se **mide** lo verifico yo por log; lo que se **siente** (comodidad, ritmo, si la viñeta molesta) solo se juzga con la cabeza puesta. No confundir las dos: un `TEST PASS` no dice que algo se sienta bien.

## El bucle completo, sin humano
```
EditorAppToolset.StartPIE({bSimulate, playMode, warmupSeconds})
LogsToolset.GetLogEntries(pattern:"TEST ", category:"LogBlueprintUserMessages")
EditorAppToolset.StopPIE()
```
`warmupSeconds` tiene que ser **mayor que `StartDelay`** (12 s por defecto) o la batería no llegó a correr cuando leo el log. Con 16 s va bien.

⚠ **Leer también `GetLogEntries(pattern:"Accessed None", category:"")`.** Un `TEST SUMMARY` todo verde **no** garantiza que no haya errores de runtime: las aserciones miran valores, no la salud del grafo. Los "Accessed None" aparecen aparte.
⚠ **Y mirar los timestamps.** El log es acumulativo: entradas de corridas anteriores se confunden con las nuevas. Más de una vez casi saqué la conclusión equivocada por eso.

## 🔴 Correr en SIMULATE encuentra bugs que el PIE normal esconde
`bSimulate: true` + `playMode: "PlayMode_Simulate"` corre el mundo **sin spawnear ni poseer un pawn**.

**Ya pagó el primer día:** en Simulate, `BP_ProtoSoul.UpdateFollow` empezó a tirar *"Accessed None trying to read property CamRef"* **cada frame**. En PIE normal nunca se vio, porque la cámara siempre existe. El bug era real —`UpdateFollow` leía `CamRef` sin guarda, mientras `ApplyPlacement` sí la tenía— y en el visor habría aparecido como un log sucio o algo peor si el pawn tardaba en spawnear.

👉 **Correr las dos: PIE normal y Simulate.** Simulate es el que expone las dependencias no declaradas con el pawn y la cámara.

## Cómo está armado (y por qué así)
🔴 **Todas las aserciones son expresiones booleanas puras.** Eso es deliberado: el parser del DSL solo admite **un nodo multi-exec al final** de una lista, así que si las aserciones necesitaran `IsValid` no se podrían encadenar. La solución es que las funciones de caché hagan el `Cast` (multi-exec) y **dejen un bool** (`bHasBio`, `bHasSoul`…); después `RunAll` es una lista plana de `Check`.

| Función | Rol |
|---|---|
| `Check(TestName, bOk)` | Cuenta y loguea PASS/FAIL. **El único lugar con una rama.** |
| `Skip(TestName)` | Cuenta y loguea SKIP, para lo que no aplica en este modo. |
| `CacheBio` / `CacheSoul` / `CacheDir` / `CacheWorld` / `CachePawn` | Un `Cast` cada una, y dejan su bool. |
| `RunBio` / `RunSoul` | `if bHasX → asserts, else Skip`. Evita leer una ref nula. |
| `BioAsserts` / `SoulAsserts` | Las aserciones en sí, planas. |
| `Summary` | La línea de totales. |
| `RunAll` | Orquesta. Se dispara por timer a `StartDelay`. |

## Qué cubre hoy (18 aserciones)
**Presencia:** BioHub · ProtoSoul · StageDirector · **una sala visible en el mundo** (o sea que el streaming la mostró de verdad).
**BioHub:** conectado con el fake · 180 casillas dimensionadas · casilla 0 acumuló · **casilla 170 es hueco explícito** · `CalmSmooth` en 0-1 · `HeartSmooth` plausible 30-200 · `GetCalmBinAvg(0)` devuelve dato · **`GetCalmBinAvg(170)` devuelve 0 en el hueco**.
**Ameba:** el pulso avanza · pitch negativo (bajo el horizonte) · zona muerta en rango.
**Sensores** (🆕 2026-08-11): hay **exactamente 2** · **exactamente 1 es derecho** · los 2 cachearon su mano del pawn.

💡 **Las dos aserciones del "hueco explícito" son las que más valen.** Son la propiedad de §5 de la que depende que el panel dibuje huecos *tenues* y no *rotos*, y es exactamente el tipo de cosa que se rompe en silencio con un refactor.
💡 **La de "exactamente 1 es derecho" es la del mismo tipo.** Los dos sensores con el mismo `bIsRight` es el bug que el tracker de `BP_TouchSensor` marca en rojo, es invisible mirando el nivel, y ahora lo caza una corrida de PIE.

🔴 **Cómo se agrega un grupo de aserciones nuevo** (el patrón, que ya se repitió 3 veces): una función `ScanX` que hace el `GetAllActorsOfClass` y **cuenta en variables** (con `TallyX` para el cuerpo del loop, porque un `ForEach` es multi-exec), una `XAsserts` plana con los `Check`, y una línea en `RunAll`.
⚠ **`RunAll` NO se re-escribe con `write_graph_dsl`: se DUPLICA.** Hay que borrar el grafo y recrearlo — y entre el `remove` y el `add` va un compile (que va a dar error por el llamador huérfano) o el grafo nuevo sale con sufijo `_0`.

## Config
| Variable | Default | Rol |
|---|---|---|
| `bAutoRun` | true | Si corre solo al empezar. Apagarlo para disparar `RunAll` a mano. |
| `StartDelay` | 12 s | Cuánto espera antes de correr. Tiene que alcanzar para que el director cargue la sala y el BioHub llene alguna casilla. |

## TODO
- [ ] Aserciones del **ciclo de transición**: hoy solo verifico que haya una sala visible. Falta comprobar que `CurLevel` cambie tras un swap y que el `StageIndex` avance.
- [ ] Aserciones del **walker** (posición sobre el spline) y de la **puerta** (`RevealProgress`/`OpenProgress`), que **requieren pawn** → van con `bHasPawn` y `Skip` en Simulate.
- [ ] Que el `TEST FAIL` incluya el valor esperado y el obtenido. Hoy solo dice qué falló, no por cuánto.
- [ ] Evaluar los **Functional Tests** de Unreal (`/Script/FunctionalTesting.FunctionalTest` está disponible, y el MCP tiene `AutomationTestToolset` con `RunTests`/`GetTestResults`). Darían resultados estructurados en vez de log parseado, pero necesitan mapa de test y más andamiaje. El arnés por log ya cubre la necesidad; esto es la versión industrial.

## Relacionados
- [[BP_BioHub]] · [[BP_ProtoSoul]] · [[BP_StageDirector]] · [[BP_DebugDirector]] (el modo **soak** de ese es el complemento: deja el ciclo corriendo solo para buscar leaks)
