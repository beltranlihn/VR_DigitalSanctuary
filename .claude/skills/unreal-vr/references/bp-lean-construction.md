# Construcción lean de Blueprints — mínimo de nodos, cero duplicación

> Complementa [bp-practices.md](bp-practices.md) (no repite sus citas). Regla de fuentes: **(A)** doc oficial Epic con URL+cita textual · **(B)** código del motor UE 5.8 con archivo:línea · **(C)** fuente técnica seria con URL (marca si no se pudo verificar de primera mano) · **(D)** folclore sin fuente. Investigado 18/07/2026.

---

## (a) Checklist — antes de dar por cerrado un grafo

1. **¿Un pure/getter/cast alimenta a más de un consumidor?** → cachear una vez: `Set` de una **variable local** (impuro, ejecuta una sola vez) y leerla con `Get` en cada consumidor. No dejar que el mismo pure se re-evalúe N veces.
2. **¿La misma secuencia de ≥2 nodos aparece más de dos veces en el grafo?** → Epic lo dice explícito (ver bp-practices.md): conviértela en función o macro.
3. **¿Hay una cadena manual que un nodo combinador ya resuelve?** Ver tabla (d): `Select` en vez de Branch+variable temporal, `Switch` en vez de cadena de Branch sobre un enum/int, `MapRangeClamped` en vez de normalizar+clampear+lerpear a mano, `Make/Break Struct` en vez de N variables sueltas viajando juntas.
4. **¿Hay nodos sin conexión de exec ni de datos?** Son huérfanos de reescrituras previas — bórralos. Ver `dsl.md`/`gotchas.md` sobre basura acumulada medida en este proyecto (3.99 MB).
5. **¿La lógica se repite entre varios Blueprints, o solo dentro del mismo grafo?** Entre BPs → Function Library o función de un componente compartido. Dentro de un mismo grafo → función o macro local (ver sección c).
6. **¿Hay Cast repetido al mismo tipo en varios puntos del grafo?** Castea una vez y reusa el resultado (variable local o del BP). El costo de referencia dura es el mismo que declarar el tipo (bp-practices.md), pero el Cast repetido sigue siendo duplicación visual innecesaria.
7. **¿El tamaño del grafo se explica por matemática real (cada nodo aporta un cálculo distinto) o por copy-paste de la misma sub-cadena?** Lo primero es legítimo; lo segundo es inflado. Ver criterio (f).

---

## (b) La palanca #1: reuso de valores puros

**Mecanismo oficial (A):**
> "A Pure Function will be called one time for each node it is connected to."
> — [Functions in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/functions-in-unreal-engine) · UE5-actual (ya citado en bp-practices.md)

**Prueba en el compilador del motor (B) — más fuerte que cualquier doc:** el mecanismo no es solo "se evalúa N veces" en abstracto; el compilador **copia literalmente las statements del nodo puro dentro de cada consumidor**.
- `KismetCompiler.cpp`, función `FKismetCompilerContext::CreateExecutionSchedule` (bloque "pull out pure chains and inline their generated code"), líneas **2816–2905**.
- El nodo puro se saca de `LinearExecutionList` (línea 2877) y se registra en `PureNodesNeeded` como dependencia de cada consumidor (líneas 2858–2870).
- Por cada consumidor no-puro que depende de él: `Context.CopyAndPrependStatements(Node, NodeToInline);` — **línea 2898**. Esto es un `Append` del array de statements generadas para el pure node, copiado por cada consumidor (ver `FKismetFunctionContext::CopyAndPrependStatements`).
- **Conclusión verificable:** un pure conectado a 3 consumidores no genera "1 nodo, 3 lecturas baratas" — genera **3 copias completas de su bytecode**, una por consumidor. El grafo visual muestra 1 nodo; el bytecode compilado tiene 3.

**Patrón de mitigación — lo que SÍ es oficial vs lo que es deducción:**

| Pieza del patrón | Estado |
|---|---|
| Variables locales existen, están scopeadas a la función, son un "scratch pad" | **(A)** Epic, cita textual abajo |
| Usar una variable local para cachear un pure caro y evitar la re-evaluación | ⚠ **(D)** Epic nunca lo prescribe explícitamente — es la consecuencia lógica de combinar el mecanismo (A) con la existencia de variables locales, no una receta publicada |
| Convertir el pure en impuro (agregarle exec pins) para que el resultado se calcule una sola vez en su punto de ejecución | Deducción directa de la propia definición de impuro (A): *"nodes without execution pins reevaluate their outputs every time... nodes with execution pins store the values of their output pins when they execute"* |

**Cita textual de variables locales (A):**
> "Local variables are scoped, which means that they only exist where you define them." · "You can consider local variables a 'scratch pad' to work within a function." · "A local variable in a function is only visible to that function, and not to other functions, or the Event Graph."
> — [Blueprint Best Practices in Unreal Engine](https://dev.epicgames.com/documentation/unreal-engine/blueprint-best-practices-in-unreal-engine) · UE5.8

> "Class variables are for things that you are potentially going to be interested in accessing from multiple places in the Blueprint."
> — misma fuente. Esta es la línea divisoria oficial: **local** = uso de una sola función/grafo, se descarta al terminar; **variable de clase (miembro)** = se necesita desde varios puntos/grafos del mismo Blueprint. Ninguna de las dos existe para "evitar recalcular un pure" según texto — pero la propiedad de scope (guarda un valor calculado una vez) es la que resuelve el problema de (b) por construcción.

**Patrón concreto recomendado:**
```
[Cálculo caro (pure)] → [Set Variable Local "CachedX" (impuro, se ejecuta 1 vez en el flujo de exec)]
                                        │
                    ┌───────────────────┼───────────────────┐
              [Get CachedX]      [Get CachedX]        [Get CachedX]
              (consumidor 1)     (consumidor 2)       (consumidor 3)
```
`Get CachedX` es técnicamente puro y "se re-evalúa por consumidor" también — pero lo que re-evalúa es una **lectura de variable**, no el cálculo caro. Es la misma distinción que documenta (A) entre "nodes with execution pins store the values... every time a node connected to their outputs executes" — el costo se pagó una vez en el `Set`.

**¿Cuándo conviene variable local de función vs recalcular?** Regla práctica derivada de (b): si el pure tiene **más de un consumidor Y** el cálculo no es trivial (más de 1-2 nodos, o involucra un getter que toca el mundo — `GetActorLocation`, `GetComponentsByClass`, trace, etc.), cachea. Si el pure es un literal o una sola resta/suma y tiene 2 consumidores, el costo de la re-evaluación es insignificante comparado con el ruido visual de agregar un Set/Get — no vale la pena.

**Refuerzo de fuente técnica (C, verificado por fetch directo):**
> "Never connect an expensive pure function to more than 1 impure node."
> — [Blueprint Pure Functions: Yes? No? It's Complicated](https://raharuu.github.io/unreal/blueprint-pure-functions-complicated/) (raharudev). El artículo muestra el mismo remedio de dos vías: convertir a impuro, o cachear el output manualmente antes de distribuirlo. Sin afiliación a Epic — regla de comunidad, consistente con (A)+(B) pero no citable como "Epic dice".

> "the only direct overhead of Blueprints system is the function invoking overhead" · pure nodes "are being invoked for each line that comes out of their output" · "Even unused output pins create hidden local variables during function calls."
> — [Performance guideline for Blueprints and making sense of Blueprint VM](https://intaxwashere.github.io/blueprint-performance/) (Intax, verificado por fetch). Aporta un dato adicional no documentado por Epic: **hasta un pin de salida sin usar genera una variable local oculta** — otra razón para no dejar pines de output "por las dudas" en llamadas a función.

---

## (c) Funciones vs Macros vs Collapsed Graph vs Function Libraries — cuándo cada uno

Tabla base ya está en bp-practices.md (mecanismo función/macro/función-de-librería, con cita textual de Epic). Esto **complementa con el dato de motor que faltaba: si el macro realmente reduce nodos o no.**

**Prueba de motor (B) — los macros NO deduplican en el grafo compilado:**
- `KismetCompiler.cpp`, función `FKismetCompilerContext::ExpandTunnelsAndMacros`, línea **4251**.
- Comentario del propio código, línea **4300**: `// Clone the macro graph, then move all of its children, keeping a list of nodes from the macro`.
- Cada instancia de un macro node en el grafo fuente se expande en tiempo de compilación clonando **todo** el grafo del macro dentro de la función que lo usa. Si el mismo macro se usa 5 veces en una función, hay 5 copias completas de su lógica en el bytecode compilado.

**Consecuencia para "reducir nodos" — distinción que la doc no hace pero el motor sí obliga a hacer:**

| Nivel | Function | Macro |
|---|---|---|
| **Grafo que el asistente autoría/edita** (lo que importa para este proyecto: menos nodos que escribir/gestionar vía DSL) | 1 nodo de llamada por uso | 1 nodo de instancia por uso — **igual de compacto visualmente** |
| **Bytecode compilado / lógica realmente compartida** | 1 sola implementación, llamada N veces (verdadera deduplicación) | N copias completas de la lógica, una por sitio de uso — **cero deduplicación real** |
| **Puede tener nodos latentes (Delay, timers)** | ❌ No | ✅ Sí (bp-practices.md) |
| **Overridable en BPs hijos** | ✅ Sí | ❌ No |

**Regla derivada (no folclore de "cuál es más rápido" — es sobre qué objetivo cumple cada uno):** si el objetivo es **reducir el tamaño real del .uasset / evitar lógica duplicada en compilado**, usa **Función** (o Function Library si no depende de estado de instancia — ver bp-practices.md). Si el objetivo es solo **compactar lo que el asistente escribe en el grafo fuente** y la lógica necesita latentes o múltiples pines de exec, un **Macro** cumple igual de bien — pero no esperar que reduzca nada a nivel de ejecución.

**Collapsed Graph:** confirmado (A) — "Collections of nodes in the graph can be collapsed into sub-graphs for organizational purposes" ([Nodes in Unreal Engine](https://dev.epicgames.com/documentation/unreal-engine/nodes-in-unreal-engine)). Puramente visual, sin reuso fuera del grafo que lo contiene (igual que ya documentaba bp-practices.md) — el equivalente de motor es simplemente nodos "Tunnel" de entrada/salida sin llamada real.

---

## (d) Nodos que reemplazan cadenas — evita encadenar cuando 1 nodo alcanza

| Nodo | Reemplaza | Fuente |
|---|---|---|
| **Sequence** | Varias conexiones de exec saliendo del mismo pin repetidas manualmente / orden implícito confuso | **(A)** "The Sequence node allows for a single execution pulse to trigger a series of events in order." — [Flow Control in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/flow-control-in-unreal-engine) |
| **Switch (Int/String/Name/Enum)** | Cadena de Branch anidados sobre el mismo valor | **(A)** "A switch node reads in a data input, and based on the value of that input, sends the execution flow out of the matching (or optional default) execution output." — misma fuente |
| **Select** ("Ternary Select") | Branch + variable temporal + Set en cada rama, para elegir entre 2+ valores de datos | **(B)** `K2Node_Select.h` línea 31: `UCLASS(MinimalAPI, meta=(Keywords = "Ternary Select"))`. ⚠ No se encontró página de doc general de Epic dedicada al nodo Select para Blueprints (el resultado "Select Node" de dev.epicgames.com corresponde a RigVM/Control Rig, no a Blueprints) — la existencia y semántica del nodo están confirmadas por motor, no por doc de usuario. |
| **Map Range Clamped** | Normalizar + clampear + lerpear a mano (3-4 nodos de math) | **(A)** [Map Range Clamped](https://dev.epicgames.com/documentation/unreal-engine/BlueprintAPI/Math/Float/MapRangeClamped) — "returns a value mapped from one range into another where the value is clamped to the input range" |
| **Make/Break Struct** | N variables sueltas que siempre viajan juntas entre nodos | **(A)** "To create a Make Struct node, drag off of a struct input pin and select Make [Struct Name]..." / "Using a Break Struct node allows you to replicate that behavior throughout your Blueprint graph easily." — [Blueprint Struct Variables in Unreal Engine](https://dev.epicgames.com/documentation/unreal-engine/blueprint-struct-variables-in-unreal-engine) |
| **DoOnce / DoN** | Bandera booleana manual + Branch para "ejecutar solo la primera vez / solo N veces" | **(A)** "The DoOnce node will fire off an execution pulse just once... until a pulse is sent into its Reset input." · "The DoN node will fire off an execution pulse N times." — Flow Control |
| **Gate** | Bandera booleana manual + Branch para "abrir/cerrar" un flujo de ejecución | **(A)** "A Gate node is used as a way to open and close a stream of execution." — Flow Control |
| **MultiGate** | Índice manual + Switch para rotar/distribuir un pulso entre N salidas | **(A)** "The MultiGate node takes in a single data pulse and routs it to any number of potential outputs. This can take place sequentially, at random, and may or may not loop." — Flow Control |
| **Reroute / Knot nodes** | No reemplazan lógica — mejoran legibilidad sin costo | Confirmado por (C) [jdn.dev](https://jdn.dev/avoiding-blueprint-spaghetti/): "cable channels... to keep cables in-place", se crean con doble-click sobre una conexión existente. Blog independiente, sin afiliación Epic, sin métricas — pero el mecanismo (doble-click) es verificable en el editor. |

---

## (e) Anti-patrones que inflan el grafo

- **Repetir la misma sub-cadena >2 veces sin extraerla.** Ya documentado con cita textual de Epic en bp-practices.md ("If you find yourself using the same set of nodes more than twice..."). Es el único umbral numérico que Epic da en todo este tema.
- **Un pure caro con múltiples consumidores sin cachear.** Ver (b) — el motor duplica el bytecode por consumidor, no solo "lo re-evalúa conceptualmente".
- **Pines de salida sin usar en llamadas a función.** (C, intaxwashere): generan variables locales ocultas igual — no son gratis solo por no estar conectados a nada más.
- **Nodos huérfanos por reescrituras iterativas de un grafo vía DSL.** Ya documentado en gotchas/dsl.md de este proyecto (folclore-cero: es un hecho medido en este mismo proyecto, 3.99 MB de basura). Aplica directo al modo de trabajo del asistente: cada reescritura de un grafo debe ir seguida de una limpieza explícita de huérfanos, no asumir que el compilador los descarta del grafo fuente.
- **"De-spaghetti Your Blueprints, the Scientific Way"** — charla oficial de Unreal Fest 2024 (Valentin Galea, Hangar13), en el canal de aprendizaje de Epic. Propone medir la complejidad de un grafo con **cyclomatic complexity, Halstead complexity y maintainability index** — el intento más cercano a un criterio *cuantitativo* no-folclórico para "este grafo está inflado". ⚠ **(C) — no se pudo obtener transcripción**, solo la descripción del listado de Epic Developer Community: [enlace](https://dev.epicgames.com/community/learning/talks-and-demos/z0WW/unreal-engine-de-spaghetti-your-blueprints-the-scientific-way-unreal-fest-2024). No cito números concretos de la charla porque no los verifiqué de primera mano.
- **Optimizar sin perfilar primero.** (C, [Chris McCole](https://www.chrismccole.com/blog/blueprint-optimization-in-unreal), verificado por fetch): "always work from the most expensive, to least" — metodología de perfilar con Unreal Insights antes de tocar nada, consistente con lo que ya dice Epic textualmente en bp-practices.md sobre Insights.

---

## (f) Criterio: grafo grande legítimo vs grafo inflado

No existe un número oficial de Epic (confirmado en bp-practices.md). El criterio que sí se sostiene con lo investigado aquí:

**Legítimo** — cada nodo adicional aporta un **cálculo distinto** que no existe en ningún otro punto del grafo (ej.: un filtro band-pass real donde cada Multiply/Add pertenece a un coeficiente distinto de la ecuación; una interpolación con múltiples ejes que cada uno necesita su propio Lerp). Un cálculo matemático real de 40 nodos que no repite ninguna sub-cadena **no** es inflado — es simplemente ese el tamaño del problema. Epic no ofrece más regla que esta ausencia de repetición.

**Inflado** — el tamaño se explica por alguna de estas causas verificables, no por el problema en sí:
1. La misma sub-cadena (≥2 nodos) aparece más de dos veces → viola la regla explícita de Epic (bp-practices.md).
2. Un pure con múltiples consumidores sin cachear → el bytecode real es mayor de lo que el grafo visual sugiere (prueba de motor, sección b).
3. Nodos huérfanos de reescrituras → no aportan absolutamente nada, ni visual ni de bytecode (deberían estar en 0).
4. Una cadena manual reconstruye lo que un nodo combinador de la tabla (d) ya resuelve en 1 nodo.
5. Cast repetido al mismo tipo en vez de reusar el resultado de un único Cast.

**Test rápido:** si al borrar 1 nodo del grafo y seguir el flujo hacia atrás, encuentras 2+ nodos idénticos en configuración e inputs en otro punto del mismo grafo → es candidato a extracción (función/macro) o a cacheo (variable local), según si el problema es repetición de lógica o repetición de evaluación de un mismo valor.
