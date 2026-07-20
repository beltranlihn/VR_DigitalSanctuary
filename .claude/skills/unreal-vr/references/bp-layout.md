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

## 🔴 Qué puedo y qué NO puedo hacer por MCP
- ❌ **Comment boxes: NO creables por API** (ver [gotchas.md](gotchas.md), sección "Lo que el MCP NO puede crear"). Los cuadros etiquetados los agrega el humano.
- ✅ `set_node_position(node,{x,y})` **sí** me deja imponer el layout (cosmético, no toca lógica → seguro incluso en grafos frágiles). Convención de coordenadas al construir/ordenar:
  - **Fila de exec:** todos los exec nodes en un baseline (ej. `y=0`), `x` creciente en pasos de ~280–320.
  - **Datos debajo:** cada pure/getter que alimenta a un exec node en `(x_consumidor − 40, y + 160)`. Si alimenta a varios exec nodes → **un getter debajo de CADA uno** (no un cable cruzando el grafo).
  - **Separación de etapas:** gap grande de `x` (o cambio de banda `y`) entre bloques de tarea. Como no puedo etiquetar, dejo el gap y **aviso al humano "acá va el comment box de \<etapa\>"**.
  - **Straighten aproximado:** ajustar el `y` del nodo para que su pin de exec coincida con el del driver. Es aproximado (no conozco el offset exacto de cada pin por altura variable del nodo), pero el layout general (exec en fila + datos abajo) ya da el ~80% de la legibilidad.
- 🔴 **Causa raíz de los grafos "eternos y superpuestos":** `write_graph_dsl` coloca los nodos en una línea naive. El arreglo de fondo NO es ordenar después, es **construir modular de entrada** (sub-funciones nombradas chicas) y aplicar esta convención con `set_node_position` a medida que se construye.

## Sin herramienta de captura del editor de BP
No hay screenshot del grafo (`CaptureViewport` es del nivel). Al ordenar por API se trabaja **a ciegas** → para grafos grandes conviene que el humano ajuste; para grafos chicos/nuevos, aplicar la convención al construir y que el humano valide.
