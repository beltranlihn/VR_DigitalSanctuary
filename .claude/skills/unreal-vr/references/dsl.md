# Blueprint Graph DSL (S-expressions) — `write_graph_dsl` / `read_graph_dsl`

`BlueprintTools.write_graph_dsl {graph, code}` converts an S-expr script into nodes and compiles. `read_graph_dsl {graph}` round-trips (but see caveats). `get_graph_dsl_docs` returns the full grammar live.

## Structure
```
(event EventName stmt...)              ; native event, e.g. EventBeginPlay, EventTick (DeltaSeconds)
(event Custom|MyEvent (P1 P2) stmt...) ; custom event — MUST prefix Custom| ; params must already exist on it
(fn FunctionName (P1 P2) stmt...)      ; function graph body
```
- Native events: `EventBeginPlay`, `EventTick (DeltaSeconds)`, `Collision|EventActorBeginOverlap (OtherActor)`, etc.
- A custom event only exposes params it already has (create it + typed params first — see gotchas for struct params).

## Statements & expressions
- `(bind var expr)` — capture a node output; reuse the var (don't repeat the call, it makes duplicate nodes).
- `(bind (a b) (Node ...))` — capture multiple outputs in pin order.
- `(NodeType|Id args...)` — exec/call a node. Positional args map to input pins in order (skipping exec).
- Keyword args: `:PinName value` sets that pin (e.g. `:Index 0`, `:X 1.0`).
- `self` — auto-bound Self Reference (the owning BP). Usable anywhere an Object pin is expected.
- Literals: `1  3.14  "text"  true  false`. **Class paths / enum values / asset refs MUST be quoted** (`"/Script/Engine.StaticMeshActor"`, `"AlwaysSpawn"`) or you get "Undefined variable".
- Ops: `+ - * / %`, `== != < <= > >=`, `and or xor not`, `(select cond a b)` ternary, `(neg x)`.
- Component access: `(.x v) (.y v) (.z v)`, `(.pitch r) (.yaw r) (.roll r)`, `(.location t) (.rotation t) (.scale t)`.
- Variables (on self): `(Variables|Default|GetMyVar)` / `(Variables|Default|SetMyVar value)`.
- Variable on ANOTHER object: `(Class|<ClassNoUnderscore>|Get<Var> targetRef)` e.g. `(Class|BPOSCReceiver|GetScale osc)`.

## Control flow
```
(if cond stmt... (elif cond stmt...) (else stmt...))   ; elif/else must be LAST in the body
(for i (range stop) stmt...)   (for e arr stmt...)
(while cond stmt...)
(switch int  expr (:0 ...) (:1 ...) (:Default ...))
(switch string expr (:Case_0 ...) (:Default ...))      ; string switch outputs are Case_0/1.. (NOT the match string)
(switch name  expr ...)
```
Enum switch: `(switch Utilities|FlowControl|Switch|SwitchOn<EnumName> expr (:Value ...))`.

## Multi-exec nodes (latent / branch / cast / IsValid)
Named exec outputs are sub-lists whose head starts with `:` and come AFTER data/keyword args. Data outputs are available inside as `_lowercasedpinname`, or name them via `(bind ...)`.
```
(bind meshActor (Utilities|Casting|CastToStaticMeshActor :Object spawned)
  (:then  (Development|PrintString "ok"))
  (:CastFailed))

(Utilities|IsValid obj
  (:"Is Valid"    ...)          ; pin names with spaces use the quoted form
  (:"Is Not Valid" ...))
```

## Before writing
- `find_node_types(graph, type_id_filter, context_pins:[])` to get the exact `type_id`.
- `get_node_type_pins(graph, type_id)` for exact pin names (and the derived `_underscore` output vars).

## 🔴 Escribir DSL COMPACTO — reglas para no inflar el grafo (aprendidas a la mala)
El conteo de nodos explota por DOS causas: (1) **escombros de reescritura**, (2) **subexpresiones repetidas**. Las dos se controlan.

### 1. `bind` TODA subexpresión que uses más de una vez — es la palanca #1
Cada nodo puro (getter, math, GetVelocity…) se **evalúa una vez POR consumidor**. Inlinearlo N veces = N evaluaciones Y N sub-árboles de nodos. Medido acá: el `Step` original llamaba `GetLinearVelocity` **4 veces inline** → 4 evaluaciones. Con `(bind (_vel _ok) (MotionControllerUpdate|GetLinearVelocity mc))` → **una**.
- Regla: si un valor aparece 2+ veces, `(bind _x ...)` arriba y reusar `_x`. No cuesta legibilidad y colapsa el grafo.
- Aplica también a `(Variables|Default|GetX)` repetidos: bindea una vez si lees la misma var varias veces en el mismo tramo (ojo: si la var cambia entre lecturas, NO bindear — releer).

### 2. Operadores, no nodos con nombre largo
`(+ a b)` `(- a b)` `(* v f)` `(select c a b)` `(neg x)` en vez de `Math|Float|Add`, `Math|Vector|...`. Un operador = un nodo compacto; resuelve por tipo (float, vector, etc.). ⚠ Lo que el `read` emite (`Math|Vector|vector+vector`, `Vector_Zero`) NO es escribible — usar `(+ )`, `Math|Vector|VectorZero`.

### 3. Un nodo que reemplaza una cadena
`(select cond a b)` en vez de branch + 2 SetVar cuando eliges un VALOR (no ejecución). `Math|Float|Clamp(Float)` (1 arg = clamp 0-1). `Math|Interpolation|FInterptoConstant` hace todo el "mover-hacia-objetivo-a-velocidad-constante" en un nodo (evita ~8 de min/max/clamp/step). Antes de encadenar 5 nodos de math, `find_node_types` buscando si hay uno que ya lo haga.

### 4. Extraer bloque autocontenido a una FUNCIÓN aparte + llamarla
Si un bloque es coherente (la caja, un filtro), ponerlo en una **función nueva** (`add_function_graph` → `write_graph_dsl` en grafo VACÍO = seguro, cero escombros) y en el grafo grande solo `(CallFunction|MiFuncion args)`. Beneficios: cada grafo queda chico, la reescritura de la función no toca el grafo grande frágil, y `write` en grafo vacío no acumula huérfanos. Así se hizo `UpdateLevel` (28 nodos limpios) sin tocar `Step`.

### 5. NUNCA re-`write_graph_dsl` un grafo grande existente desde el `read`
El `read` es LOSSY (ver caveats abajo): reescribir desde él corrompe la lógica Y **deja el cuerpo viejo como isla huérfana** (medido: 3665 nodos donde vivían 405 = 88% basura). Para cambiar un grafo grande ya construido: **cirugía de nodos** (`create_node`/`connect_pins`/`delete_node`) o extracción a función (#4). Reescritura completa SOLO en grafos nuevos/vacíos.

### 6. Después de CUALQUIER reescritura → barrer huérfanos
Correr la limpieza de vitalidad dirigida (ver gotchas §limpieza) vía `ProgrammaticToolset`. Es lo que separa "grafo de 400 nodos" de "grafo de 400 + 3000 de basura".

### Checklist antes de dar por cerrado un grafo
- [ ] ¿Algún valor puro se usa 2+ veces sin `bind`? → bindear.
- [ ] ¿Cadenas de math que un nodo haría en uno? → buscar el nodo.
- [ ] ¿Bloque autocontenido que debería ser función? → extraer.
- [ ] ¿Reescribí una función? → barrer huérfanos + `compile` (detector de errores) + `read` para verificar.

## read_graph_dsl caveats (see gotchas.md)
- Inlines PURE nodes at each use → one node feeding 3 inputs prints 3×. Not a duplicate.
- May MISLABEL a node by name-collision (e.g. a BP variable getter shown as `Class|AudioVectorscope|GetScale`). Verify with `get_node_infos`.
- Lossy for SwitchOnString case strings: shows `:/muse` but writing back needs `:Case_0` and loses the string.
