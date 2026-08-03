# Orden y legibilidad de grafos Blueprint

Cómo dejar un grafo legible. Fuentes: **Allar `ue5-style-guide` §3.4** (el gold standard de la comunidad), **techarthub**, **Epic docs**. Confirma los principios que pidió el usuario (exec en línea, variables debajo, getters duplicados, bloques por tarea).

## Las reglas (con fuente)
- **Flujo izquierda→derecha = avance de ejecución.** Epic/techarthub: *"the further right you move in the graph, the further along the execution chain."* La línea blanca de exec va en **UNA fila horizontal**.
- **Alineá WIRES, no NODOS.** Allar §3.4.2 (verbatim): *"Always align wires, not nodes."* Se **escalonan los nodos** para que el cable quede recto — hotkey **Q** (Straighten Connections). No pongas los nodos en una grilla prolija; poné los cables rectos.
- **La línea blanca de exec tiene prioridad sobre las de datos.** Allar §3.4.3 (verbatim): *"If you ever have to decide between straightening a linear white exec line or straightening data lines of some kind, always straighten the white exec line."*
- **Nodos de datos DEBAJO de su consumidor.** techarthub: *"position dependent nodes either alongside or underneath parents."* Los getters/math que alimentan a un exec node van **abajo**, con su output subiendo hacia el pin.
- **Un getter por consumidor, NO un cable largo.** techarthub (verbatim): *"Use multiple variable 'get' nodes instead of long wires to reduce visual clutter."* ← exactamente lo que pidió el usuario.
- **Bloques por tarea envueltos en comment.** Allar §3.4.4: *"Blocks of nodes should be wrapped in comments that describe their higher-level behavior."* Con descripción concreta ("Cálculo de daño final considerando ataque y defensa"), no genérica ("Daño").
- **Sin spaghetti / sin nodos muertos.** Allar §3.4.1 (*"Wires should have clear beginnings and ends"*) y §3.4.6 (*"all nodes must have a purpose"*).
- **Reroute nodes** (doble-click en un cable) usados liberalmente para evitar cruces y cables por encima de nodos.
- Otros de la comunidad: **Convert to Validated Get** (en vez de IsValid+Get suelto); **Collapse to Function/Macro** para sub-grafos, máximo una capa de anidamiento.

## Reconciliación con el conteo de nodos (importante — no se contradicen)
"Duplicar getters" parece chocar con [bp-lean-construction.md](bp-lean-construction.md) ("cachear pures compartidos para bajar nodos"). **No chocan:**
- Un **getter de variable es trivial** (bytecode mínimo) → duplicarlo por consumidor es **gratis en runtime** y mejora legibilidad. **Duplicalo.**
- El cacheo aplica a **pures CAROS compartidos** (cálculos, no getters): ahí sí una sola copia y reusar el resultado.
- Regla: **getters baratos → duplicar por legibilidad; cálculos caros → cachear por perf.**

## 🔴 Convención de coordenadas del proyecto (medidas del usuario, `BlueprintTestOrden`, 2026-07-29)
El usuario armó a mano un BP de referencia con el orden que quiere. Extraído nodo por nodo — **estos son los números a usar** (recordar: en el grafo de UE, **+X = derecha, +Y = ABAJO**):
- **Fila de exec en un baseline** (ej. `y=0`), `x` creciente en pasos de **~380–460**. El evento/entry arranca la fila.
- **Getters/pures DEBAJO de su consumidor**, `y_consumidor + ~190`, `x` alineado con el consumidor (o un pelo a la izquierda para que el cable suba recto al pin).
- **Regla del getter por consumidor:** si una **variable** alimenta a N nodos, **un `Get` distinto debajo de cada uno** — NO un getter con N cables largos. (Sólo para variables/getters baratos; un **cálculo caro compartido** sí se cachea en un nodo — ver reconciliación abajo.)
- **Branch:** la rama `then` (True) sube y la `else` (False) baja respecto del branch, separadas **~±200–240** en `y`, y cada cadena sigue en su propio baseline. Con branches anidados, cada nivel abre su propia banda vertical.
- **Cadena de pures** (ej. `loc + fwd*offset`): apilada debajo, con el resultado final subiendo al pin del consumidor.
Demostrado aplicándolo a `BP_BrushTool:UpdateStroke` (IsValid + 3 branches anidados) el 2026-07-29: quedó de un pile en `x=2240–4480` a un árbol legible.

## 🔴 Qué puedo y qué NO puedo hacer por MCP
- ❌ **Comment boxes: NO creables por API** (ver [gotchas.md](gotchas.md)). Los cuadros etiquetados los agrega el humano; yo dejo el gap y aviso "acá va el comment de \<etapa\>".
- ✅ `set_node_position(node,{x,y})` **sí** me deja imponer el layout (cosmético, no toca lógica → seguro incluso en grafos frágiles).
- ✅ **Aplicar la regla del getter-por-consumidor SÍ se puede**, pero es cirugía de topología, no sólo mover: `create_node` del getter duplicado + `connect_pins` a cada consumidor. 🔴 **Gotcha crítico (2026-07-29):** sobre un pin de entrada **object-reference**, `connect_pins` **NO reemplaza el cable existente — AGREGA un segundo** (el pin queda con 2 fuentes; compila igual pero es inválido). Hay que **`break_pins` del cable viejo explícitamente** después de conectar el nuevo. (Distinto de lo que dice la doc general "connecting replaces"; para exec y quizá otros tipos sí reemplaza, para object-ref no.) Verificar con `get_node_infos` que el pin quedó con UNA sola fuente.
- **Straighten aproximado:** ajusto el `y` para que los pines de exec queden casi rectos; el offset interno de cada pin varía con la altura del nodo, así que queda ~90% y el humano remata con **Q**.
- 🔴 **Causa raíz de los grafos "eternos y superpuestos":** `write_graph_dsl` coloca los nodos en una línea naive apilada. El arreglo de fondo NO es ordenar después, es **aplicar esta convención con `set_node_position` a medida que se construye** (y construir modular: sub-funciones nombradas chicas). **Nueva regla operativa del proyecto: todo grafo que yo construya o toque queda ordenado con esta convención antes de darlo por cerrado.**

## 🔴 Ordenar un grafo GRANDE (>~40 nodos): `scripts/auto_layout.py`, NO a mano
Para grafos chicos (como `UpdateStroke`, 25 nodos) se puede ordenar con `set_node_position` uno por uno desde el modelo. **Para grafos grandes NO** — mover 200+ nodos a ciegas de a uno es inviable y un error de posición se propaga. La herramienta es **`scripts/auto_layout.py`** (ProgrammaticToolset): un algoritmo de layout jerárquico que **corre dentro del editor**, lee las N conexiones sin traerlas a mi contexto, computa columnas por profundidad de exec + un carril por rama + datos debajo del consumidor + una banda por evento, y aplica todas las posiciones en una sola llamada.
- **Validado 2026-07-30 en `BP_CalibDirector:EventGraph` (263 nodos):** 262 colocados, **`identical: true`** (el DSL vivo quedó byte por byte igual → cero cambio de lógica), en una llamada.
- **Uso:** editar `G` al grafo objetivo → `execute_tool_script` → `compile` + `save`. Devuelve `{total, placed, roots, unplaced, identical}`.
- **`unplaced`:** un getter **sin consumidor** (huérfano suelto) no se puede ubicar (no tiene de qué colgar) → queda en su sitio; moverlo a mano a un costado o borrarlo con `clean_orphans.py`.
- **Tuning** (arriba del script): `SX` paso de exec, `SYL` separación de carriles, `BAND` separación entre eventos, `DATA_DY`/`DATA_DX`/`STK` para los datos.
- Sigue siendo **~85%**: el humano da **Q** (straighten fino) y agrega los comment boxes por banda. Pero convierte un "pile" ilegible en un árbol navegable.

## Procedimiento para ordenar un grafo CHICO a mano (a ciegas, pero completo)
1. `find_nodes(graph, "")` → lista de todos los nodos.
2. `get_node_infos` en lote → mapear la topología: cadena(s) de exec (quién dispara a quién) y qué dato alimenta cada pin.
3. Computar posiciones con la convención de arriba (exec en fila; then arriba / else abajo; datos debajo del consumidor).
4. `set_node_position` en lote.
5. (Opcional, regla getter-por-consumidor) duplicar getters de variables compartidas: `create_node` + `connect_pins` + **`break_pins` del cable viejo**.
6. `compile` (detector de errores) + `save`. El humano abre el grafo, da **Q** para el straighten fino y agrega los comment boxes.

## Sin herramienta de captura del editor de BP
No hay screenshot del grafo (`CaptureViewport` es del nivel). Al ordenar por API se trabaja **a ciegas** → para grafos grandes conviene que el humano ajuste; para grafos chicos/nuevos, aplicar la convención al construir y que el humano valide.
