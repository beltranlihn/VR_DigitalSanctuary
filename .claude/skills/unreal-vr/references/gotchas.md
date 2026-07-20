# Gotchas & hard rules (hard-won — don't relearn these)

## 🔴 Háptico en OpenXR/Quest: `SetHapticsByValue` NO puede vibrar rápido — usa un asset de curva
**El síntoma:** el háptico se siente como un pulso lento en vez de un zumbido continuo, y subir "Frequency" no cambia nada.

**La causa.** `SetHapticsByValue(Frequency, Amplitude, Hand)` **miente**: el pin parece normalizado 0-1, pero en OpenXR **no lo es**. La cadena, verificada en código:
1. `SetHapticsByValue` construye `FHapticFeedbackValues Values(Frequency, Amplitude)` (`PlayerController.cpp:4562`) — **el constructor clampea la frecuencia a [0,1]** (`IInputInterface.h:87`). Pasar 20 o 200 no sirve: sale 1.0.
2. OpenXR la pasa **cruda, sin conversión**, a `XrHapticVibration.frequency` (`OpenXRInput.cpp:1505`), **que está en Hz**.

→ **Por esta API el rango alcanzable es 0-1 Hz.** `Frequency=1.0` no es "rápido al máximo": es **1 Hz = un pulso por segundo** — el pulso más lento que se puede pedir sin apagarlo. Es una jaula: **no existe ningún valor que dé una vibración rápida**.

### ✅ La solución: `PlayHapticEffect` con un `HapticFeedbackEffect_Curve`
El asset de curva **escapa del clamp**, y no por casualidad:
- El tick de hápticos declara `FHapticFeedbackValues LeftHaptics, RightHaptics;` (`PlayerController.cpp:4713`) con el **constructor por defecto, que NO clampea**.
- `UHapticFeedbackEffect_Curve::GetValues` **escribe la frecuencia directo en el struct**: `Values.Frequency = HapticDetails.Frequency...Eval(EvalTime)` (`HapticFeedbackEffect.cpp:84`) — nunca pasa por el constructor que clampea.
- Eso llega crudo a `XrHapticVibration.frequency` en Hz. **Una curva con Frequency = 160 pide 160 Hz de verdad.**

Bonus: `bLoop` funciona y **se auto-reinicia** (`PlayerController.cpp:4803`: `bLoop ? Restart() : Reset()`), así que es **una llamada al entrar y `StopHapticEffect` al salir** — más barato que llamar `SetHapticsByValue` cada tick.

**El asset hay que crearlo A MANO** en el editor (click derecho → Input → Haptic Feedback Effect Curve): no hereda de `UDataAsset`, así que `DataAssetTools.create` lo rechaza ("cannot be stored in a DataAsset") y `AssetTools` no tiene creación genérica. Después sí se le configuran las curvas por `ObjectTools.set_properties`.

### Plan B si no quieres un asset: `Frequency = 0.0`
`XR_FREQUENCY_UNSPECIFIED` vale **0** (`openxr.h:74`) y significa *"runtime, elige tú la frecuencia óptima"* → el Quest usa su zumbido nativo. El guard que detiene el háptico es `Amplitude <= 0 || Frequency < XR_FREQUENCY_UNSPECIFIED`, o sea `Frequency < 0` — **el 0 pasa sin problema**. Contraintuitivo: el valor que se lee como "apagado" es el mejor de los alcanzables. Peor que la curva (no eliges tú la frecuencia), pero mejor que cualquier otro valor de `SetHapticsByValue`.

### Corolarios
- **La amplitud sí es real** 0-1 por ambos caminos — esa palanca funciona normal. En `PlayHapticEffect` se escala con el pin `Scale`.
- `GetHapticFrequencyRange` devuelve **Min=Max=0** en OpenXR (`OpenXRInput.cpp:1557-1558`): el motor declara que **no hay rango de frecuencia consultable**. No es que la frecuencia no exista — es que el motor no la publica.
- `HapticValue.duration = CurrentDeltaTime` (`OpenXRInput.cpp:1504`) → dura **un frame**. Si usas `SetHapticsByValue`, llamarlo cada tick **es correcto y necesario**, no es desperdicio.
- Para cortar: `Amplitude = 0` dispara `xrStopHapticFeedback`; con el asset, `StopHapticEffect(Hand)`.
- `HapticFeedbackEffect_Buffer` y `_SoundWave` **hardcodean `Frequency = 1.0`** (`HapticFeedbackEffect.cpp:126,169`) y dependen de `Values.HapticBuffer`, que en OpenXR **solo hace algo si un extension plugin engancha el chain struct** (`OpenXRInput.cpp:1543-1546`). No son el camino en Quest. **Curve es el único que da control de frecuencia.**

## Tres trampas más del DSL (test 20 — costaron varios intentos hasta acertar)
- **Un getter booleano en un `(bind ...)` del preámbulo puede fallar aunque el MISMO getter funcione inline** dentro del cuerpo del `if`/rama. Si un `bind` de variable booleana da error raro, probar a inlinearlo en el uso en vez de bindearlo arriba.
- **`Math|Vector|Vector_Zero` / `Vector_GetAbs` no existen** — los nombres reales son **`VectorZero`** y **`VectorGetAbs`** (sin guion bajo). `find_node_types` con el filtro exacto antes de asumir el nombre.
- **`(else _)` no es una sentencia válida.** Un placeholder de "no hacer nada" en un `else` hay que reemplazarlo por una sentencia real (p. ej. releer una variable sin cambiarla), no dejar un guion bajo suelto.

## 🔴 `read_graph_dsl` NO es entrada válida para `write_graph_dsl` — son dialectos distintos
No es "casi igual con detalles": copiar la salida del read y editarla **falla siempre**. Cuatro asimetrías medidas (costaron 5 escrituras fallidas seguidas):

| El read emite | Por qué falla al escribir | Lo que hay que escribir |
|---|---|---|
| `(|GetbInvert)` (prefijo vacío) | `\|GetbInvert does not exist` **y** `Variables\|Default\|GetbInvert` tampoco | `(Variables\|Default\|GetInvert)` — **ver abajo** |
| `(bind _returnvalue_5 -1.0)` | *"expression produced no output pin. Use a node call expression, not a literal"* | inlinear el literal donde se usa: `(select _b -1.0 1.0)` |
| `Math\|Vector\|vector-vector` (y `+`/`*`) | `does not exist` — es el **nombre visible** del nodo, no un type_id | los operadores: `(- a b)`, `(+ a b)`, `(* v f)` — resuelven por tipo |
| `(GetLinearVelocity mc)` en un contexto booleano | **el read es LOSSY**: colapsa el nodo a su **pin 0** y pierde qué pin estaba conectado de verdad | `(bind (_vel _ok) (MotionControllerUpdate\|GetLinearVelocity mc))` |

### 🔴 La peor: los nodos multi-output se leen MAL, no solo distinto
`GetLinearVelocity` devuelve `OutLinearVelocity` (Vector, pin 0) **y** `ReturnValue` (Boolean, pin 1). El grafo real usaba el **bool**; el read imprimió `(and (MotionControllerUpdate|GetLinearVelocity _mcref) (...))`, que leído literalmente es "and de dos vectores" — **una mentira, no una abreviatura**. Al escribirlo: `Could not connect pin OutLinearVelocity to A`.
→ **Ante cualquier nodo con más de un output, `get_node_type_pins` antes de creer el read.** Y capturar con `(bind (a b) (Node ...))`, que además evita que el nodo puro se reevalúe por consumidor (el `Step` original llamaba `GetLinearVelocity` **4 veces** por este motivo).

### 🔴 Los booleanos PIERDEN la `b` en el type_id del nodo
La variable se llama `bInvert`, `bStill`, `bBreathing`, `bDebug`, `bInThreshold`, `bInit`, `bTracked`… pero el nodo es **`Variables|Default|GetInvert`**, `GetStill`, `GetBreathing`, `GetDebug`, `GetInThreshold`, `GetInit`, `GetTracked`. El motor usa el **display name** (que se come el prefijo húngaro `b`), no el nombre de la variable. `get_variable_category` devuelve `"Default"` igual, así que **no da ninguna pista**. Aplica también a variables de otro objeto: `bIsRightHand` → `(Class|BPBreathSensor|GetIsRightHand ref)`.
→ Método barato y definitivo: **`find_node_types(graph, "Variables|Default|", [])`** lista los getters/setters reales de TODAS las variables del BP de una vez. Hacerlo **antes** de escribir, no después de 5 errores.

## ✅ LIMPIEZA DE HUÉRFANOS — método validado (BP_BreathProbe: 8.88 MB → 1.20 MB, 3683 nodos borrados)
Cada `write_graph_dsl` deja el cuerpo viejo como isla muerta. Tras ~15 reescrituras, `Step` tenía **3665 nodos donde viven 405**. La limpieza va con **ProgrammaticToolset** (los listados gigantes nunca tocan el contexto) y este criterio:

**🔴 DETECCIÓN — `read_graph_dsl` NO muestra los huérfanos** (solo renderiza lo alcanzable desde los eventos vivos). Un grafo se ve prolijo en el DSL y estar inflado igual. Para saber si hay bloat: comparar `find_nodes(graph, title="")` (total REAL de nodos) contra el conteo del DSL vivo. Ej. medido 2026-07-20: `FadeFromBlack` mostraba ~8 nodos en el DSL pero tenía 13 (5 huérfanos); el `EventGraph` de BP_FadeSphere ~30 vivos pero ~120 totales (~90 huérfanos). **"Limpiar" mirando solo el DSL o borrando event-stubs vacíos NO alcanza — hay que contar nodos.** Basta UNA reescritura de una función/evento existente para dejar la copia vieja huérfana.

**🔴 La trampa que invalida el criterio ingenuo:** "conectado a algo" NO significa vivo. Los cuerpos huérfanos **siguen enchufados al pin de datos del FunctionEntry** (el entry es único por función; todos los cuerpos viejos leen su parámetro `DT`), y en el EventGraph al pin `DeltaSeconds` del Tick. Un BFS no-dirigido desde las entradas marca TODO como alcanzable (medido: 3665/3665 "vivos").

**El criterio correcto — vitalidad dirigida en 2 pasadas:**
1. **EXEC hacia adelante** desde los puntos de entrada (`K2Node_FunctionEntry/FunctionResult/Event/CustomEvent/Tunnel` — estos NUNCA se borran): seguir solo pines de salida `type_id == "Exec"`.
2. **Cierre de DATOS hacia atrás** sobre los vivos: toda fuente conectada a un pin de entrada no-Exec de un nodo vivo es viva (transitivo).

Un huérfano consume datos del entry pero **nadie ejecuta ni consume lo que produce** → muerto. Borrar el resto con `delete_node`.

**✅ Script listo para usar: [`scripts/clean_orphans.py`](../scripts/clean_orphans.py)** — implementa este método (dry-run + borrado + verificación DSL antes/después). Validado 2026-07-20: borró **531 huérfanos** en 4 BP (Step 645→226, FadeSphere EventGraph 118→40, WBP SetVisMode 47→25, etc.), `.uasset` −47/−49%, DSL vivo **idéntico byte por byte**. Quirks del sandbox anotados en el header del script (sin `collections`; los dicts de las tools son `_StrictDict` sin `.get(default)`). Correr con `dry=True` primero; borrar sólo si los conteos cierran; guardar sólo si `identical=True`. Backup en disco de los `.uasset` antes (no hay git).
**Validación del método:** en los grafos escritos UNA sola vez (`UpdateAudio`, `DoFadeIn/Out`) dio **0 borrados** — no arranca nada vivo. `compile_blueprint` después como detector, y `read_graph_dsl` del EventGraph para confirmar la lógica. Control de tamaño: el `.uasset` en disco antes/después.

## ⚠ Los `toolset_name` requieren el PATH COMPLETO (cambió)
`call_tool` con el nombre corto **falla**: `Toolset 'SceneTools' not found`. Hay que pasar el registrado por `list_toolsets`:
`editor_toolset.toolsets.scene.SceneTools`, `...blueprint.BlueprintTools`, `...object.ObjectTools`, `...asset.AssetTools`, `...primitive.PrimitiveTools`, `...material.MaterialTools`.
Excepciones (otro namespace): **`EditorToolset.LogsToolset`**, **`EditorToolset.EditorAppToolset`**, **`ToolsetRegistry.AgentSkillToolset`**.
Las rutas completas ya están en los encabezados de [toolsets.md](toolsets.md).

## ⚠ Audio: dos trampas que dejaron los WAV mudos (test 25)
1. **El `Sound` de un AudioComponent NO llega del CDO a la instancia colocada** — misma familia que los defaults del CDO. Configurar el componente del CDO (`...BP_C:AudioX_GEN_VARIABLE`) dejó la **instancia del nivel** (`...BP_C_0.AudioX`) con `Sound=None`, `bAutoActivate=true`, `bAllowSpatialization=true`. → Setear las props **en la instancia del componente** (`<actorInstance>.AudioX`), no solo en el template.
2. **🔴 `set_properties` sobre un SUB-OBJETO (componente) aplica SOLO la primera propiedad del JSON.** Medido: `{Sound, bAutoActivate, bAllowSpatialization}` aplicó solo `Sound`; `{bAutoActivate, bAllowSpatialization}` aplicó solo `bAutoActivate`. (En el ACTOR sí aplica múltiples — pasó siempre con los params de respiración.) → En componentes, **una propiedad por llamada**, o verificar cada una con `get_properties` después.
- Sonido 2D correcto para respiración: `bAllowSpatialization=false` (además nuestros WAV son estéreo → no se espacializan igual). `bAutoActivate=false` (el playback lo maneja `UpdateAudio` con FadeIn/FadeOut). El WAV de loop necesita `bLooping=true` en el **asset** (ya está).

## Firmas que NO son las obvias (verificadas — no adivinar)
- **`ObjectTools.set_properties`** = `{instance: {refPath}, values: "<JSON STRING>"}` — NO `{object, properties}`. `values` es un **string** con el JSON adentro, no un objeto.
- **`ObjectTools.get_properties`** = `{instance, properties: ["A","B"]}` — la lista se llama `properties`, no `property_names`. Devuelve un JSON string.
- **`LogsToolset.GetLogEntries`** = `{category, pattern, maxEntries}` — NO `search_regex`/`max_entries`. Y `category` tiene default `"LogsToolset"` que **no existe** → pasar `category: ""`.
- **`SceneTools`** no tiene `get_actors`. Para listar todo el nivel: **`find_actors {name:"", tag:"", collision_channels:[]}`**.

## DSL: `elif` / `else` se ANIDAN, y los eventos se declaran ANTES de llamarlos
- **`(elif)` debe ser la ÚLTIMA forma del cuerpo del `(if)`, y el `(else)` va DENTRO del `(elif)`** — no son hermanos. Error si no: *"(elif) must be the last form inside an (if) or (elif) body"*.
```
(if c1  stmtA...
  (elif c2  stmtB...
    (else stmtC...)))
```
- **Un `(event Custom|X ...)` debe aparecer en el código ANTES de cualquier `(CallFunction|X)`**, o falla con *"CallFunction|X does not exist"*. El orden del texto importa.

## ⚠⚠ `write_graph_dsl` DEJA HUÉRFANOS: cada reescritura ACUMULA los nodos viejos
**Reescribir un grafo NO borra los nodos anteriores.** Crea la cadena nueva y **abandona la vieja dentro del grafo**. Compila igual (los huérfanos no se ejecutan), no aparece ningún warning, y el Blueprint **crece sin límite**.
**Medido en BP_BreathProbe (~6 reescrituras):**
| | Real | Debería | Tamaño |
|---|---|---|---|
| `Step` antes | **1355 nodos** (186 VariableSet) | ~300 (41 Sets) | **3.99 MB** |
| `Step` recreado | 41 VariableSet | 41 | **1.78 MB** |
| `EventGraph` | **76 VariableSet** | 11 | (falta limpiar) |
Los IDs delatan las generaciones: `VariableSet_15..36`, `_52..73`, `_85..89`, `_98..102`, `_111..115`, `_121..136` — un bloque por reescritura. Comparación de control: `BP_BreathSensor`, escrito **una vez**, pesa **0.16 MB**; el probe llegó a 3.99 MB con lógica equivalente.
⚠ `get_connected_subgraph` **NO sirve** para detectar esto: devolvió los 1355 nodos como "alcanzables".
**Cómo limpiar un FUNCTION graph:** `remove_function_graph` → **`compile_blueprint`** (obligatorio: sin compilar, el nombre sigue tomado y `add_function_graph` te devuelve `Step_0`) → `add_function_graph` → `add_function_param` → `write_graph_dsl`.
**El EventGraph no se puede borrar y recrear** → o se borran los huérfanos a mano, o se acepta el peso, o se rehace el BP.
**Regla práctica: iterar un grafo a fuerza de `write_graph_dsl` tiene un costo acumulativo real.** Para iteraciones múltiples, recrear el function graph cada N reescrituras, o mover la lógica volátil a funciones (que sí se pueden recrear limpias) y dejar el EventGraph mínimo.
✅ **`compile_blueprint` SÍ reporta errores** cuando los hay (verificado: *"Could not find a function named Step"*). Un `returnValue: null` es realmente compilación limpia.

## `write_graph_dsl` NO borra los eventos que faltan en el código nuevo
Reescribir un grafo **reconstruye solo los eventos que declarás**; los que existían y ya no están en el código **sobreviven huérfanos**. Peor: si borraste una variable que ese evento usaba, su getter se reemplaza por un **literal** (`(if (GetbUseRightHand))` → `(if true)`) y **compila igual**, en silencio.
**Regla: después de reescribir un grafo, `list_events` y borrá a mano los eventos que quedaron de más** (`find_nodes` con `node_class: /Script/BlueprintGraph.K2Node_CustomEvent` → `get_node_infos` para identificar cuál es cuál por su `type_id` `AddEvent|Custom|X` → `delete_node`). El título en `find_nodes` no matchea ("Acquire Controller" devuelve `[]`); pasá `title: ""` y filtrá por type_id.

## Llamar a una función propia desde el DSL: el arg 0 es `self`
`(CallFunction|MiFuncion DeltaSeconds)` falla con *"Could not connect pin DeltaSeconds to self"* — el primer pin posicional de una función de la clase es **`self`**. Usar **keyword**: `(CallFunction|MiFuncion :MiParam DeltaSeconds)`.
Además: **una función SÍ puede llamar a un custom event** (útil para meter un `Delay` — que en una función está prohibido — dentro de un evento y llamarlo desde ahí).

## `read_graph_dsl` OMITE los pines que están en su valor por defecto
Un `(Game|Feedback|SetHapticsByValue pc 1.0 0.4 "Left")` se relee como `(Game|Feedback|SetHapticsByValue pc 1.0 0.4)` — porque `"Left"` **es el default del pin**. Con freq/amp en 0 queda `(SetHapticsByValue pc)`. **Parece que perdiste argumentos y no perdiste nada.** Sumado al inlining de puros y al mislabeling por colisión: un read "roto" casi nunca es un bug real → confirmar con `get_node_infos` antes de "arreglar".

## 🔴 `read_graph_dsl` muestra los eventos de Enhanced Input como VACÍOS aunque estén cableados
Un `(event EnhancedInputActionIA_Shoot_Right (...))` sin cuerpo en el DSL **NO significa que esté vacío**: el reader NO recorre los pines de exec con nombre (`Triggered`/`Started`/`Ongoing`/`Completed`/`Canceled`) del nodo de input. La lógica cuelga de esos pines y el DSL no la renderiza. **Para ver lo que realmente dispara un evento de input → `get_node_infos` sobre el nodo** (`type_id` `Input|EnhancedActionEvents|EnhancedInputAction<IA>`): ahí ves `Triggered.connected_pins` y `Completed.connected_pins`. Verificado 2026-07-19 — casi me hace borrar un evento vivo por creerlo vacío. Regla general: para eventos de input, el DSL es solo un índice de "qué eventos existen", no de su cuerpo.

## `blueprint` param de BlueprintTools exige el object-path con sufijo `.AssetName`
`list_graphs`/`list_variables`/`compile_blueprint`/etc. reciben `blueprint: {refPath}` y el ref **debe ser el object-path completo** `/Game/.../BP_X.BP_X` — el package-path a secas `/Game/.../BP_X` da *"is not a valid object path"*. (Los refs de grafo ya lo traen: `...BP_X.BP_X:EventGraph`.) Mismo criterio para assets en `ObjectTools`/`AssetTools` que piden `instance`/object_path.

## Editing existing graphs — the #1 rule
- **`write_graph_dsl` on an event that ALREADY exists (hand-built, user-edited, or `Assign`-generated) DUPLICATES it** — creates a parallel `<Name>_0` event with its own node chain and orphans the original. It does NOT edit in place reliably.
- **Read before editing**: `read_graph_dsl` + `list_variables`. Then edit **surgically**: `get_node_infos` (map pins/refs) → `create_node` / `connect_pins` / `set_pin_value` / `delete_node`. Connecting to an input pin that's already connected REPLACES the connection.
- Reserve `write_graph_dsl` for **new / empty** graphs (freshly created BP, new function graph).
- After any edit, verify with `read_graph_dsl` and/or `get_node_infos`.

## Lo que el MCP NO puede crear (verificado — no reintentar)
- **Structs (UserDefinedStruct) y Enums**: no hay toolset. `BlueprintTools.create` con `asset_type = /Script/Engine.UserDefinedStruct` **falla con un popup en el editor**: *"Cannot create a blueprint based on the class 'UserDefinedStruct'"* — `create` solo hace Blueprints. **Los crea el humano (2 clics).** Pedírselos por adelantado, en lote, con nombre y campos definidos.
- **Instalar plugins** y **Project Settings**: también manual.
- **Comment boxes** (los cuadros etiquetados que agrupan nodos): **no hay tool**. `find_node_types` devuelve `|AddComment...` pero `create_node` con `AddComment`/`|AddComment` **falla** ("does not exist") — ese `...` es la acción de editor *"Add Comment to Selection"*, que necesita selección manual, no es invocable. **El ordenado visual + comments lo hace el humano.** (Verificado 2026-07-19.)
- Sí se pueden crear **niveles** (duplicando un template — ver nodes.md), Blueprints, Data Assets, materiales.

## Ordenar/leer el LAYOUT de un grafo — lo que hay y lo que falta
- `arrange_nodes(nodes[])` (auto-layout algorítmico) y `set_node_position(node, {x,y})` (uno por llamada) **existen** y son cosméticos (no tocan conexiones ni lógica → seguros incluso en grafos frágiles). Pero: no controlás el **agrupamiento semántico**, y **no hay captura del editor de Blueprint** (`CaptureViewport` es del nivel) → reposicionar es trabajar **a ciegas**. Para un grafo grande, ordenarlo por API es mal negocio: sin comments y sin poder verlo, el humano lo hace mejor y más rápido.
- 🔴 **Causa raíz de los grafos "eternos y superpuestos":** `write_graph_dsl` coloca los nodos en una línea naive. El arreglo NO es ordenar después — es **construir modular de entrada**: partir la lógica en **sub-funciones nombradas** (chicas, auto-documentadas) en vez de un mega-EventGraph/función. Ver [bp-lean-construction.md](bp-lean-construction.md) y [bp-practices.md](bp-practices.md) (partir NO mejora runtime, solo legibilidad — hacerlo por claridad, no por perf).

## ⚠⚠ Los defaults del CDO NO llegan a los actores YA COLOCADOS en el nivel
**El bug más caro hasta ahora — 3 síntomas distintos, una sola causa.** Si agregás una variable `instance-editable` a un BP **después** de haber colocado el actor en el nivel, esa instancia se queda en **0 / vacío**, y `set_properties` sobre el CDO **no la toca**. Peor: las variables que ya existían conservan el valor que tenían **al momento de colocarse**, así que cambiar el default del CDO tampoco las actualiza.
Síntomas reales que produjo (todos a la vez, y ninguno parecía relacionado): `ActivateDelay=0` y `DeactivateDelay=0` → el debounce "no funcionaba" (activaba/desactivaba en 1 frame); `HapticAmplitude=0` → **no se sentía ningún háptico**; `Gain`/`MinAmplitude`/`TauAmp` seguían en los valores viejos → los "ajustes" no hacían nada.
**Regla: después de tocar defaults, `set_properties` TAMBIÉN sobre la instancia del nivel** (`.../L_X.L_X:PersistentLevel.BP_Y_C_0`), y **verificar con `get_properties` sobre la INSTANCIA, no sobre el CDO**. El CDO solo sirve para actores que se coloquen/spawneen a futuro.
(Alternativa: borrar y re-colocar el actor — hereda los defaults frescos.)

## `set_properties` sobre un CDO NO surte efecto hasta COMPILAR el Blueprint
Cambiar el CDO (`Default__BP_X_C`) con `ObjectTools.set_properties` **se lee de vuelta bien y se guarda**, pero **no llega a los defaults de la clase hasta que compilás el Blueprint**. Síntoma real: seteé `DefaultPawnClass` en el GameMode, `get_properties` devolvía el pawn correcto, el log confirmaba `Game class is 'BP_SoulChargerGameMode_C'`… y en runtime spawneaba `DefaultPawn`. **Faltaba `compile_blueprint`.**
**Regla: después de tocar un CDO por propiedades → `compile_blueprint` SIEMPRE, antes de `save_assets`.** `get_properties` NO detecta este problema: te miente devolviendo el valor que seteaste.

## Diagnóstico en runtime: PrintString → el log, y lo leés vos
`Development|PrintString` escribe a `LogBlueprintUserMessages`. Con `LogsToolset.GetLogEntries` podés leerlo directo: **el humano solo corre PIE y vos diagnosticás solo**, sin que transcriba nada.
- ⚠ `GetLogEntries` tiene `category` con default `"LogsToolset"` (que NO existe → error). **Pasá `category: ""`** para buscar en todo el log.
- Patrón que funciona: prefijos numerados por actor (`"SC 1: …"`, `"FS 2: …"`) + `GetLogEntries` con regex (`"FS \\d|SC \\d"`).
- **Imprimí IDENTIDADES, no solo "OK"**: `(Utilities|String|Append "pawn = " (Utilities|GetDisplayName pawn))` reveló en un intento que el pawn era `DefaultPawn_0` y no el nuestro. Un print de "pawn OK" nos tuvo dando vueltas dos iteraciones porque el pawn *era* válido — solo que era el equivocado.
- `Utilities|String|Append` para concatenar (**no** existe `Concat_StrStr`). `Utilities|GetDisplayName` para el nombre.

## Level Streaming: `LoadStreamLevel` exige registro previo; `LoadLevelInstance` NO
`Game|LoadStreamLevel(byName)` **falla** si el nivel no está registrado como sublevel del persistente (`LogLevel: Warning: Failed to find streaming level object associated with 'X'`) — y falla **en silencio** para el jugador.
**Usá `LevelStreaming|LoadLevelInstance(byName)`**: crea el streaming level en runtime sin registro previo, acepta la **ruta completa** (`/Game/.../L_X`), y devuelve **`bOutSuccess`** (imprimilo) + un `LevelStreamingDynamic` ref para descargar después con `Default|UnloadLevelInstance`.

## Structs de usuario: los pines del Make llevan GUID → usar POSICIONALES
El nodo es **`Utilities|Struct|Make<NombreSinGuionBajo>`** (`F_Signal` → `MakeFSignal`; Unreal quita el `_`, igual que con las clases). Sus pines de entrada llevan **sufijo GUID**: `Value_6_14154BAA…`, `Confidence_7_B7A6…`. Los keyword args son inviables → **pasar los campos por POSICIÓN**, en el orden en que están declarados en el struct: `(Utilities|Struct|MakeFSignal v 1.0 1.0)`. Ídem `BreakF<X>` y `SetmembersinF<X>`.
- ⚠ `find_node_types` con el nombre CON guion bajo (`"F_Signal"`) devuelve **vacío**. Buscar sin él, o filtrar `Utilities|Struct|Make` (ojo: esa categoría devuelve ~99k chars → volcarla a archivo y grepear).

## Herencia de Blueprints: función sin retorno = se hereda como EVENTO
Si el padre tiene una **función sin valor de retorno**, la hija **no puede overridearla como function graph**: `add_function_graph` falla con *"is an inherited event-shape function; it must be placed as an event node"*. Hay que usar **`add_event`** con ese nombre.
Y el nombre en el DSL **NO es el de la función**: Unreal le antepone `Event`. Una función `UpdateSignal` del padre se overridea en la hija como **`(event EventUpdateSignal …)`**, no `(event UpdateSignal …)`. `read_graph_dsl` te da el nombre real — usalo.
- La hija auto-crea `EventBeginPlay`/`EventTick` con llamadas `(|Parent:BeginPlay)` / `(|Parent:Tick DeltaSeconds)`. La cadena padre→hija funciona sola; no las borres.

## Variables — el prefijo `b` de los booleanos DESAPARECE en el nodo
Una variable `bFading` genera nodos **`Variables|Default|GetFading` / `SetFading`**, NO `GetbFading`. Unreal quita la `b` inicial en el display name de los booleanos, y el type_id usa el display name. `SetbFading` → "does not exist". Si un setter/getter de bool no existe, probá sin la `b`. (`list_variables` muestra el nombre REAL `bFading`, que no coincide con el del nodo — no te fíes de él para construir el type_id.)

## Nodos PUROS: se re-evalúan en CADA consumidor
Blueprint ejecuta un nodo puro **una vez por cada input que lo consume**, no una vez por frame. Bindear no lo evita: `(bind x (+ (GetVar) dt))` con dos consumidores evalúa el `+` dos veces.
**El bug clásico:** escribir una variable y después reusar un puro que la lee →
```
(bind e (+ (GetFadeElapsed) dt))
(SetFadeElapsed e)        ; escribe
(bind a (/ e duration))   ; RE-EVALÚA el +, ahora lee el valor YA escrito → e + dt otra vez
```
**El fix:** escribir primero, y después leer la variable **fresca** con un getter nuevo:
```
(SetFadeElapsed (+ (GetFadeElapsed) dt))       ; el + tiene UN solo consumidor
(bind a (/ (GetFadeElapsed) duration))         ; getter nuevo → valor actualizado
```
Regla: si un puro lee algo que vas a modificar, no lo reuses a través de la escritura.

## write_graph_dsl: cuándo duplica y cuándo no (matizado)
- **Duplica** eventos hechos a mano, editados por el usuario, o generados por un nodo `Assign`.
- **NO duplica** eventos que el propio `write_graph_dsl` creó: reescribirlos los reconstruye limpio. Verificado.
- Ante la duda: reescribí y hacé `read_graph_dsl` para confirmar antes de seguir.

## read_graph_dsl is not literal
- Inlines PURE nodes at each use site (a pure getter feeding X/Y/Z shows 3×) — that's ONE node, not duplicates.
- Can MISLABEL nodes by name collision (showed `Class|AudioVectorscope|GetScale` for a BP `scale` variable-get). Confirm with `get_node_infos` (check `type_id` + target pin type) before "fixing" a non-bug.

## Nodes / pins
- `call_tool` `tool_name` = SHORT name (after last dot), never the full path.
- `find_nodes` REQUIRES a `title` arg (pass `""` to match all) plus optional `node_class` ref.
- `find_node_types` needs a reasonably SPECIFIC `type_id_filter` — broad filters return hundreds of entries (token waste). Trailing pipe `Cat|Sub|` lists a whole category.
- `describe_toolset` on BlueprintTools is ~72k chars (auto-dumped to file). Use references/toolsets.md instead.

## Variables & params
- `add_variable` types: bool int float byte string name text + Vector Rotator Transform Vector2D LinearColor. Other structs → `add_struct_variable` / `add_struct_function_param` (struct_type ref like `/Script/OSC.OSCMessage`). Object types → `add_object_variable` / `add_object_function_param`.
- Param-adding tools work on FUNCTION or event-dispatcher graphs, NOT on custom-event nodes. To get a typed custom event, let the `Assign` node generate it (below).
- BP member variables are public/readable from other BPs by default — good for cross-BP reads.

## Components on a Blueprint
- `PrimitiveTools.add_sphere/add_cube/add_cylinder/add_cone` (and component adds) need the BP's **CDO**, not the asset path: `BlueprintTools.get_default_object {blueprint}` → `/Game/.../Default__X_C`; pass THAT as `actor`.
- The component becomes a graph getter `Variables|Default|Get<ComponentName>`.

## Delegates (binding a runtime multicast delegate, e.g. OSC OnOscMessageReceived)
- Binding to a hand-made function/CreateEvent FAILS ("not a compatible function / Valid functions: []") because C++ delegates pass structs by `const&` (by-ref) and tool-made params are by-value.
- FIX: `create_node` the **`Assign<Delegate>`** node (e.g. `Audio|OSC|AssignOnOscMessageReceived`). It auto-generates a custom event with the EXACT delegate signature (by-ref included), already wired to its Delegate pin. Then wire the Assign node's `execute` + target (`self`) into the flow and write the body into that generated event.

## SwitchOnString case strings
- Cannot be set via API: `add_node_pin` auto-names cases `Case_N`; the DSL can't set the match string; `set_pin_value` doesn't apply to case exec outputs.
- Preserve an existing switch that already has the strings (don't rewrite it), or the user types them in the editor's Details panel.

## Source of truth
- The LIVE server is authoritative for toolset APIs, node `type_id`s and pins. Web/Epic docs are for CONCEPTS only; always verify exact ids live.
