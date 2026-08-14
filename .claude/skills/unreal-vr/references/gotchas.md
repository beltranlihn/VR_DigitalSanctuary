# Gotchas & hard rules (hard-won — don't relearn these)

## 🔴🔴 `read_graph_dsl` SOLO imprime el pin exec PRIMARIO — lo demás se ve VACÍO aunque esté cableado
**El síntoma:** leés un grafo y un evento aparece sin cuerpo — `(event EnhancedInputActionIA_Shoot_Right (ActionValue ...))` y nada más. Concluís que es código muerto. **Está perfectamente cableado**, pero por `Started` / `Completed` / `CastFailed` / `Is Not Valid`, que el read **no imprime**.

Costó **tres desvíos en un solo día** (2026-08-03): se dio por muertos los eventos de input de `BP_BrushTool`, `BP_CalibProbe` y `BP_Instructions` — y eran justamente **el patrón que funciona**, con `Triggered`/`Completed` conectados. Eso mandó a inventar una IA propia que nunca disparó.

**La regla:** ante un evento o rama que el read muestra vacía, **`get_node_infos` del nodo y mirar `connected_pins` de CADA pin de salida** antes de sacar conclusiones. Lo mismo para caminos que convergen (dos exec a un mismo destino): el read muestra uno solo.

⚠ Relacionado: el read también miente con el **prefijo de clase** cuando dos BPs tienen funciones con el mismo nombre (`Class|BPCalibProbe|DoFadeOut` para una función propia). El `type_id` real del nodo (`|DoFadeOut`, con pin `self`) es lo que vale.

## 🔴🔴🔴 Recompilar un BP puede BORRAR sus actores del nivel EN MEMORIA — no guardes el nivel, recargalo
**El síntoma:** después de agregarle variables/funciones a un Blueprint y recompilarlo, **sus instancias desaparecen del nivel**. Pasó el 2026-08-05 con `BP_SeqSlot` (×5) y `BP_AttractDirector` tras una tanda de cambios: se fueron la mesa y, con el Director, las burbujas que él spawnea.

**Lo importante: casi siempre es solo la copia EN MEMORIA.** El `.umap` en disco está intacto mientras no lo guardes.

**Protocolo cuando falten actores:**
1. **NO guardar el nivel.** Guardar en ese estado es lo que convierte una molestia en pérdida real.
2. Confirmar que el disco está sano: `git status -- ruta/al/L_Xxx.umap` → **sin cambios = el nivel bueno sigue ahí**.
3. Recargar: `SceneTools.load_level` **falla** con *"the level has unsaved changes"*. La salida es **cargar otro nivel primero** (p. ej. `/Engine/Maps/Templates/OpenWorld`), lo que descarta los cambios en memoria, y después volver a cargar el nuestro.
4. Verificar el conteo de actores y los valores por instancia (`StepIndex`, etc.) antes de seguir.

👉 **Corolario preventivo: commitear el nivel ANTES de una tanda de cambios a Blueprints con instancias colocadas.** Es lo que salvó este caso.
⚠ **`find_actors(name)` matchea el LABEL, no el nombre del objeto** — 23 TargetPoints etiquetados "Bubble…" devolvían 0 buscando "TargetPoint". Para inventariar de verdad: `find_actors` con `name: ""` y leer los `refPath`.

## 🔴🔴 Esconder un actor NO lo saca del line-trace — y un WidgetComponent bloquea el rayo
**El síntoma:** algo invisible sigue frenando el `LineTraceByChannel` (el beam hace hover contra la nada, o no se puede agarrar lo que está detrás).
- **`SetActorHiddenInGame(true)` no toca la colisión.** Para sacar algo de en medio hay que **`SetActorEnableCollision(false)`** además, o directamente **`DestroyActor`** si no vuelve a usarse. Mordió dos veces el 2026-08-05: en `BP_SaveButton` al confirmar y en `BP_TouchInstrPanel` al terminar las instrucciones.
- 🔴 **Un `WidgetComponent` en world-space usa el perfil de colisión `UI`, que BLOQUEA el canal Visibility** → cualquier panel de UI se come el rayo del puntero.
  **Y no se arregla desde el editor:** poner `BodyInstance.collisionEnabled = NoCollision` funciona en el CDO pero **la instancia del nivel lo revierte** (el WidgetComponent lo regenera del perfil). Hay que hacerlo **por código en BeginPlay**: `Collision|SetCollisionEnabled(Panel, NoCollision)`. Verificar siempre el **valor efectivo de la instancia**, no el del CDO.

## 🔴🔴 Animar escala: SIEMPRE partir de la escala AUTORAL, nunca de 1.0
**El síntoma:** el objeto aparece **gigante** en el visor (o microscópico) apenas empieza a correr la lógica de escala. En el editor se veía bien.

**La causa:** `PrimitiveTools.add_sphere/add_cube/add_cylinder(radius, height, …)` **no crea un mesh de ese tamaño**: usa los `/Engine/BasicShapes/*` (100 unidades) y **codifica el tamaño pedido en el `RelativeScale3D` del componente**, que además suele ser **NO uniforme** — un `add_cylinder(radius=8, height=3)` deja `(0.16, 0.16, 0.03)`. Cualquier `SetRelativeScale3D` con un valor uniforme (típico `MakeVector(s,s,s)` con `s≈1`) **pisa esa escala** y devuelve el mesh a su tamaño base de 1 metro.

**La regla:** guardar la escala autoral en una variable **Vector** en BeginPlay —
```
BaseScale = Class|SceneComponent|GetRelativeScale3D(Mesh)
```
— y animar multiplicando por un **factor escalar**: `SetRelativeScale3D(Mesh, BaseScale * factor)`. Así funciona con escalas no uniformes y **sobrevive a que después cambien el tamaño en el editor**.
🔎 Mordió el 2026-08-05 en `BP_SaveButton` (el botón tapaba toda la vista en el visor). Relacionado con la nota vieja de "escala autoral 0.3 de componentes".

## 🔴🔴 EL error recurrente del proyecto: "declarado ≠ aplicado". Verificá el VALOR EFECTIVO, no la declaración
**El patrón**, encontrado **cinco veces en un solo día** (2026-08-03, stage Touch): la pieza existe, está declarada, compila — y **nunca se aplicó al lugar donde tenía que llegar**. Ninguna de las cinco produjo un error de compilación:

| Lo declarado | Lo efectivo | Síntoma |
|---|---|---|
| Var `PreviewSound` = `MS_Synth` | `AudioComponent.Sound` = **None** | `FadeIn` hacía el fade **del silencio** |
| Trackers: burbujas "~120cm al frente", slots "X=55, Z=75" | **Todos los actores en (0,0,0)** | El stage entero apilado en el origen |
| Eventos `IA_Grab_Right_*` + funciones `TryGrab`/`TryRelease` | Los eventos **sin conectar a nada** | Far-grab "hecho" que no existía |
| CDO `bIsRight` = true | Instancia del nivel = **false** | La mano derecha se comportaba como izquierda |
| Tracker: cubo en `(150,0,120)` | Cubo en `(0,0,120)` | — |

**La causa raíz es la misma:** una variable/asset **describe** algo, y alguien asume que por describirlo ya llega a destino. Un `AudioComponent` reproduce **su** `Sound`, no tu variable. Un actor está donde dice su transform, no donde dice el tracker. Un evento dispara lo que tiene **cableado al pin exec**, no lo que sugiere su nombre.

**La regla:** después de conectar algo, **leé el valor efectivo en el objeto final**, no el que escribiste.
- ¿Audio? → `get_properties(AudioComponent, ["Sound"])`, no la variable que lo alimenta.
- ¿Posiciones? → `get_actor_transform`, nunca el tracker.
- ¿Variable nueva en un BP con instancias ya colocadas? → leerla **en cada instancia** (Unreal NO propaga el default nuevo a instancias ya serializadas).
- ¿Evento o función que "ya está"? → mirar que el **pin exec esté conectado**; `list_functions` diciendo `bIsImplemented: true` no significa que alguien la llame.

🔴 **Corolario: `compile_blueprint` sin error NO es evidencia de nada.** Las cinco fallas compilaban. Lo único que prueba el compilador es que los tipos cierran.

## 🔴 El registro de nodos NO ve las funciones/variables creadas por MCP **desde otro Blueprint** hasta reiniciar el editor
**El síntoma:** creás `MiFuncion` en `BP_A` (aparece en `list_functions` como `bIsImplemented: true`, compila, guarda). Desde el grafo de `BP_B` querés llamarla y **`Class|BPA|MiFuncion` "does not exist"**: no la lista `find_node_types` ni la instancia `create_node`. Las funciones/variables de `BP_A` creadas **antes**, en cambio, sí aparecen.

**Lo que NO lo arregla** (probado 2026-08-03): `compile_blueprint` de `BP_A` · `compile_blueprint` de `BP_B` · `save_assets` · `AssetTools.load_asset` de `BP_A`. El snapshot del registro para esa clase queda congelado en un punto anterior de la sesión.

**Qué hacer:** dentro del **mismo** BP no hay problema (`CallFunction|MiFuncion` funciona al toque). Para cross-blueprint: o creás la función **antes** de necesitarla desde afuera, o dejás esa única conexión pendiente y la hacés después de **reiniciar el editor** (que sí refresca el registro — ojo que se lleva puesto el MCP, ver arriba). **Planificá el orden**: si `BP_B` va a llamar algo de `BP_A`, creá esa API de `BP_A` temprano.

## 🔴 El editor DEBE estar en inglés — si está localizado, el DSL de Blueprints no resuelve
**El síntoma:** `write_graph_dsl` falla con "`Variables|Default|Get…` does not exist", el azúcar `if`/`switch`/`for` falla ("`Utilities|FlowControl|Branch` does not exist"), y `create_node` no instancia nodos. `find_node_types` devuelve ids en otro idioma (`Variables|Predeterminado|Obtener…`, `Utilidades|ControlDeFlujo|Rama`, `Colisión|LineTraceByChannel`).

**La causa.** El registro de nodos y sus type_ids se construyen con los **display names localizados** al arrancar el editor. La skill (dsl.md/nodes.md) y el azúcar de control de flujo del DSL asumen los ids **en inglés**. Con el editor en español (o cualquier idioma), esos ids no existen → el DSL es inusable para grafos con ramas.

**La solución:** **Editor Preferences → General → Region & Language → Editor Language = `English`**, y **reiniciar el editor por completo** (el UI cambia en vivo pero la base de nodos solo se reconstruye en un arranque nuevo; hasta entonces `find_node_types` sigue devolviendo el idioma viejo aunque el menú se vea en inglés). Verificá con `find_node_types(graph,"CurrentHovered",[])` → debe dar `Variables|Default|Get…` (no `Obtener…`). La preferencia queda guardada → futuras sesiones abren en inglés solas. **Ojo:** el reinicio del editor tira el MCP (reconectar con ToolSearch / reiniciar Claude) y puede reabrir otro mapa (verificá `get_current_level` antes de `add_to_scene`). Descubierto 2026-07-29 armando `BP_AimBeam`.

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

### 🔴 Un nodo puro se RE-EVALÚA en cada consumidor → leer-modificar-escribir la misma variable se corrompe
Un `(bind _arc (+ (GetArcLength) _dist))` consumido por **`SetArcLength`** y además por un `CallFunction` produce **dos** evaluaciones de la suma. La primera escribe `old+dist`; la segunda ya lee el valor nuevo y entrega `old+2·dist`. Compila limpio, no hay warning, y el síntoma aparece recién en runtime como un valor que crece al doble.
**Regla:** cuando un valor derivado de una variable se escribe en **esa misma** variable y además se pasa a otro nodo, poner **primero el `Set`** y después **leer la variable otra vez** — dos getters distintos, sin `bind` que los una. (Bindear un puro sigue siendo lo correcto cuando el valor **no** depende de algo que el propio grafo muta en el medio; ver `bp-lean-construction.md` §1.)
Verificarlo: `get_node_infos` sobre el nodo consumidor y mirar qué nodo alimenta cada pin. El `read_graph_dsl` inlinea los puros y **no** deja ver esto.

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
- **`AssetTools.save_assets`** = `{asset_paths: ["/Game/Ruta/MiAsset"]}` — **strings sueltos, SIN el sufijo `.MiAsset`** y **sin** el envoltorio `{refPath}` que usa el resto de las tools. Con `{assets:[{refPath}]}` falla pidiendo `asset_paths`. (2026-08-04)

## 🔴 `CollisionProfileName` NO aplica el perfil — hay que setear `collisionEnabled`
Setear `BodyInstance.collisionProfileName = "NoCollision"` por `set_properties` **deja `collisionEnabled` en `QueryAndPhysics`**: el componente sigue colisionando. El perfil es una etiqueta; lo que gobierna es el enum. **Setear los dos** (`{"BodyInstance":{"collisionEnabled":"NoCollision","collisionProfileName":"NoCollision"}}`) y verificar el valor efectivo. Otro caso de manual de "declarado ≠ aplicado". (2026-08-04, `BP_TouchSensor.Mesh`)

## ⚠ Un nombre de variable `bFoo` se come el nombre de función `SetFoo`
La var `bEquipped` genera un setter llamado **`SetEquipped`** (el DSL le come la `b` inicial). Si además querés una función pública que haga más cosas al setearla, **NO la llames `SetEquipped`** — colisiona. En `BP_AimBeam` se resolvió llamándola **`Equip(NewEquipped)`**. (2026-08-04)

## ⚠ `find_node_types` con filtro genérico devuelve CIENTOS de entradas
El `type_id_filter` es *substring*, no prefijo. `"Distance"` devolvió ~300 type_ids (todo PCG, Interchange, fog, spline…) = miles de tokens tirados. **El filtro tiene que ser el prefijo completo del namespace**: `"Math|Vector|VectorLength"`, no `"VectorLength"`; `"Variables|Default|Get"`, no `"Get"`. (2026-08-04)

## ⚠ Los type_ids con PARÉNTESIS que emite el `read` son riesgosos de escribir
`Math|Vector|Distance(Vector)`, `Utilities|Array|Get(acopy)` — los paréntesis del nombre chocan con el parser del S-expr. Si hay una alternativa sin paréntesis, usarla: para "¿llegué al destino?" salió **`Math|Vector|VectorLengthSquared` del delta** (y de paso evita la raíz cuadrada). (2026-08-04)

## 🔴 `VInterpTo` con `InterpSpeed <= 0` SALTA al target — un default en 0 es un teleport silencioso
Si agregás una var de velocidad por MCP, su default es **0.0** y `add_variable` no lo cambia. Un `VInterpTo` alimentado con esa var **no interpola: teleporta**, sin error ni warning — exactamente el bug que la interpolación venía a arreglar. **Setear el default en el CDO (`ObjectTools.set_properties` + compilar) y verificarlo con `get_properties`.** (2026-08-04, `BP_SoundBubble.TravelSpeed`)

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

## `SpawnActorFromClass`: el pin `SpawnTransform` es BY-REF → hay que cablearlo SIEMPRE
Dejarlo en su valor por defecto compila mal: *"'Spawn Transform' in action 'BeginDeferredActorSpawnFromClass' must have an input wired into it ("by ref" params expect a valid input to operate on)"*. Para spawnear en la identidad: `(Math|Transform|MakeTransform)` **sin argumentos** (su default de Scale ya es 1,1,1). Y ojo — el error aparece en el **compile**, o sea que el `write_graph_dsl` ya escribió los nodos: si falla así, hay que **recrear el function graph**, no reescribirlo (o quedan huérfanos).

## `create_node` con `CallFunction|<CustomEvent>`: la búsqueda normaliza mayúsculas de forma inconsistente
Verificado 2026-07-29 en `BP_BrushTool`, con los cuatro eventos creados en la misma pasada de DSL: `CallFunction|TrigOnL` ✅ · `CallFunction|TrigOffL` ✅ · `CallFunction|TrigOffR` ✅ · **`CallFunction|TrigOnR` ❌ "does not exist"** → `CallFunction|TrigonR` (con la `o` minúscula) ✅. Es la misma familia que la normalización de los bools (`bWasInZone` → `GetWasinZone`).
→ Si `create_node` dice que una función/evento que **sabés que existe** no existe: confirmá con `list_events` (que sí da el nombre real), y después probá la variante con la letra siguiente a un prefijo en minúscula. **No asumas que el evento no se creó.**

## `get_node_type_pins` NO deja el nodo en el grafo
Devuelve un `refPath` con pinta de nodo real (`...:MiFuncion.K2Node_CallFunction_0`), pero es transitorio: `delete_node` sobre él responde *"is not valid EdGraphNode"*. O sea que consultar pines **no ensucia el grafo** y no hace falta limpiar después. (Verificado 2026-07-29.)

## 🔴🔴 UNA FUNCIÓN IMPURA INLINE COMO ARGUMENTO DE DATOS = PIN SILENCIOSAMENTE DESCONECTADO
La trampa más cara del DSL hasta ahora — **costó dos sesiones de debug** (2026-07-30 y 2026-08-03, stage Movement).
```
(Class|BPDrawCanvas|AddPoint _c :NewLoc _f :Width (CallFunction|ComputeWidth :DT _dt) …)
                                        ↑ función CON pines de exec, usada como expresión de datos
```
**Qué pasa:** el parser lo acepta, el nodo de la función **se crea y se enchufa a la cadena de exec**, el Blueprint **compila limpio** (incluso con `warnings_as_errors`)… y el pin destino (`Width`) queda **sin conectar, en su valor por defecto (0.0)**. Cero errores, cero warnings.
**Síntoma:** el parámetro "no hace nada" por más que loguees que el valor de origen es correcto. En Movement, `Width` llegaba 0 → **todos los trazos salían del grosor mínimo** sin importar lo que eligiera el usuario en la paleta; y como el ancho real era 0, lo que se veía era sólo el piso de `MinThickness` — un filamento de sección fija, que **también explicaba el "se ve muy geométrico"**.
- 🔑 **Sólo aplica a funciones IMPURAS** (las que crea `add_function_graph` por defecto, o cualquiera que toque variables). Los **getters de variable y los nodos puros SÍ se inlinean bien**.
- **Cómo escribirlo bien:** llamar la función como **statement** y bindear su resultado — `(bind _w (CallFunction|MiFn :X v))` — y recién ahí usar `_w`. ⚠ Ojo: si la función es de **otra clase**, el bind del return **también falla** ("produced no output pin") → en ese caso la otra clase expone el resultado en una **variable** y se lee con un getter cross-clase (patrón usado en `BP_BrushPalette.bOver`/`CurWidth`).
- **Y si no hace falta la función**, mejor: pasar el getter puro directo.
- 🔴 **CÓMO DETECTARLO (hacerlo siempre tras escribir un `CallFunction` con argumentos):** `get_node_infos` del nodo consumidor y verificar que **cada pin de entrada tenga `connected_pins` no vacío**. Un pin con `"value":"0.0", "connected_pins":[]` que *debería* venir cableado es exactamente este bug. **El `read_graph_dsl` NO lo muestra** (el pin desconectado se relee como su literal por defecto, indistinguible de un valor puesto a mano).
- Mismo fallo, mismo día, en `(Variables|Default|SetOverPalette (Class|…|UpdateTouch …))`.

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

## 🔴 CVars muertos: un `.ini` con un nombre inexistente se IGNORA EN SILENCIO (verificado 2026-07-25)
Un CVar mal escrito o renombrado **no da error ni warning**: la línea del `.ini` simplemente no hace nada, y uno cree tener aplicada una config que nunca existió. Encontrados así en este proyecto (2 años de config muerta):

| En el `.ini` | Realidad |
|---|---|
| `vr.PixelDensity=1.2` | **No existe desde UE 5.5.** Renombrado a `xr.SecondaryScreenPercentage.HMDRenderTarget`, y la escala pasó de `1.0` a **`100` = porcentaje**. Se renderizaba al 100%, no al 120%. |
| `xr.OpenXRFB.FoveationLevel=2` | **No existe.** El nombre real va **sin punto** tras `OpenXRFB`: `xr.OpenXRFBFoveationLevel`. El FFR nunca se activó. |

**Regla: antes de confiar en cualquier línea de `[SystemSettings]`, verificar que el CVar exista.**
```
EditorAppToolset.SearchCVars {name: "PixelDensity"}   → {} significa QUE NO EXISTE
```
Devuelve además el `value` actual y el `help`, así que sirve para confirmar el valor efectivo, no el que uno cree. En un build en device: escribir el nombre en la consola; si no imprime valor, no existe.

**Config de nitidez VR correcta en 5.5+ (Quest 3, OpenXR, mobile forward):**
```ini
[/Script/OpenXRHMD.OpenXRHMDSettings]
bIsFBFoveationEnabled=True          ; habilita la extension XR_FB_foveation

[SystemSettings]
xr.SecondaryScreenPercentage.HMDRenderTarget=125   ; 100=recomendado del runtime, 125~=panel nativo Quest 3
xr.OpenXRFBFoveationLevel=1         ; 1=Low. Nivel 2-3 degrada visiblemente texto/UI del centro
xr.OpenXRFBFoveationDynamic=1
r.VRS.Enable=1                      ; el FFR por hardware necesita Support(ya=1) Y Enable
```

**Y lo que NO existe / no sirve en mobile forward** (no perder tiempo): TAA, TSR, TAAU y FXAA no están soportados en Forward (solo MSAA); `r.Tonemapper.Sharpen` no es de móvil y además con `r.MobileHDR=False` no hay tonemapper; MSAA >4x lo desaconseja Meta (mejor gastar en resolución). 🔴 **MSAA no actúa sobre objetos transparentes** → el aliasing de UI/iconos alpha-blend de un WidgetComponent (vive DENTRO de un render target) no lo arregla ningún MSAA; ahí las palancas son resolución de render, ajustes de textura, y sobre todo **Stereo Layers** (el panel va al compositor y no sufre el resampleo del eye buffer).

---

## 🔴 Crashea al dar Play en VR y NO es el proyecto: el runtime de Meta se actualizó abajo del editor
Diagnosticado el 2026-08-12, con evidencia 1:1 en 8 sesiones de log.

**Los síntomas, en este orden:**
1. Primer intento → **no** crashea el render, falla la creación de la sesión:
   ```
   XR call xrCreateSession(...) failed with result: XR_ERROR_INSTANCE_LOST
   ```
2. Todos los intentos siguientes → **crash duro** con `EXCEPTION_ACCESS_VIOLATION` dentro de **`LibOVRRTImpl64_1`** (la DLL de Meta), llamada desde `UnrealEditor_OpenXRHMD` → `D3D12RHI`, en el **RHI submission thread**, con el breadcrumb `EndDrawingViewport` del **primer frame** enviado al visor.

**La causa:** el editor arrancó con una versión del runtime de Oculus y **Meta Quest Link se actualizó con el editor abierto**. `XR_ERROR_INSTANCE_LOST` es literalmente "la instancia de OpenXR que tenías ya no existe". Los logs lo muestran sin ambigüedad: todas las sesiones con **1.205.0** funcionaron, incluida una **el mismo día**, y las dos primeras con **1.206.0** crashearon.

**El primer arreglo intentado:** cerrar Unreal y reabrirlo (+ reiniciar Link). ⚠ **Eso NO lo arregla: consigue una sesión buena.** El crash volvió a las 13:00 del mismo día, ya arrancando en 1.206.0, sin ninguna actualización en el medio. Dicho de otra forma: **es intermitente en 1.206.0** — 4 sesiones, 3 crashearon y 1 anduvo.
⚠ Cerrar Unreal **mata el MCP** → después hay que reiniciar Claude con Unreal ya abierto.

### Lo que se descartó (y cómo), para no volver a pagarlo
| Sospechoso | Veredicto |
|---|---|
| **SteamVR** (instalado el mismo día) | ❌ **Descartado.** Ni una línea de `steamvr`/`api layer`/`openvr` en ningún log de Unreal, y `tasklist` sin `vrserver`/`vrmonitor` corriendo. El log dice `Initialized OpenXR on Oculus runtime version…`, o sea que el runtime activo es el de Meta. |
| **Canal público de prueba (PTC) de Link** | ❌ **Descartado.** Está apagado: 1.206.0 es el **canal estable**, no un beta. |
| **GPU híbrida / adaptador equivocado** | ❌ **Sin palanca.** Es un laptop con RTX 4060 + Intel UHD, y el banner rojo de Link dice *"el hardware del sistema no es compatible"* — pero **el panel de NVIDIA no expone "Procesador de gráficos preferido"**, o sea que la máquina está en modo dGPU fijo y no hay adaptador que elegir. |

### 🔴 La hipótesis que sí es NUESTRA y se puede accionar: pedirle foveación a Meta por Link
El log, justo antes de morir, dice:
```
Warning: Requesting 10 bit swapchain, but not supported: fall back to 8bpc
Warning: Resizing VR buffer to 4368 by 2400      <- primera asignacion (125%)
Warning: Resizing VR buffer to 3488 by 1920      <- SEGUNDA asignacion
Warning: No layer resource or HMD swapchain available for stereo debug layer
[crash dentro de LibOVRRTImpl64_1, RHI submission thread, EndDrawingViewport]
```
**`XR_FB_foveation` es una extensión de META, implementada dentro de `LibOVRRTImpl64_1.dll`** — la misma DLL donde crashea. Y el proyecto la tenía habilitada en **`DefaultEngine.ini`**, o sea en la config **compartida**, así que la sesión de PC por Link también la pedía. Ídem el `125%`, que provoca la **doble asignación del swapchain** que se ve arriba.

✅ **Acción tomada (2026-08-12): mover los cvars de device a `Config/Android/AndroidEngine.ini`** — `bIsFBFoveationEnabled`, `xr.SecondaryScreenPercentage.HMDRenderTarget`, `xr.OpenXRFBFoveationLevel/Dynamic`, `r.VRS.Enable`. En el visor todo queda igual; por Link ya no se entra a ese camino.
⚠ **Los cambios de `.ini` requieren reiniciar el editor.** Y ojo: `VR_Test/Config/` es config **compartida** (regla §7 del `CLAUDE.md`).
💡 **Lección general, más allá del crash: los cvars de tuning del Quest no van en `DefaultEngine.ini`.** Si están ahí, el VR Preview de PC finge ser un Quest y arrastra los caminos de código del runtime del visor.

### Ajustes del panel de NVIDIA que estaban mal para VR (aunque no fueran el crash)
- 🔴 `Antialiasing - Modo: Anular cualquier configuración de la aplicación` con `2x` → **le pisa el MSAA 4x al proyecto**: lo que se ve por Link no es lo que se ve en el visor. Va en **Controlado por la aplicación**.
- 🔴 `Velocidad máxima de fotogramas: 60 FPS` (global y de aplicación) → el Quest corre a **72 Hz**; con techo de 60 se juzga comodidad y ritmo sobre judder que en el device no existe. Va en **Desactivado**.

### 🔴 Cómo distinguir "es el proyecto" de "es el runtime XR" en dos minutos
```
1. StartPIE({bSimulate:false, playMode:"PlayMode_InViewPort"})   ← PIE NO-VR por MCP
   Si la bateria de BP_SelfTest da verde, el contenido esta sano y el problema es la sesion XR.
2. En VR_Test/Saved/Crashes/, el CrashContext.runtime-xml de la carpeta mas reciente:
   <ErrorMessage> y <CallStack>. Si el tope del stack es LibOVRRTImpl64_1, es la DLL de Meta.
3. Comparar el runtime entre sesiones que andaban y la que no:
   grep "Initialized OpenXR on Oculus runtime version" en VR_Test/Saved/Logs/*.log
   (el titulo de la ventana tambien lo trae: "OpenXR Oculus (1.205.0)")
```
💡 **El paso 3 es el que cierra el caso.** Un crash dentro de una DLL de terceros no prueba de quién es la culpa; **el cambio de versión correlacionado con el cambio de comportamiento, sí.**
⚠ Y no confundir dos crashes distintos del mismo día: acá el de las 11:38 era `XR_ERROR_INSTANCE_LOST` en `xrCreateSession` (todavía en 1.205) y los de las 11:39 eran el access violation en 1.206. Leer el `ErrorMessage` de **cada** carpeta antes de meterlos en la misma bolsa.

## 🔴🔴 Cirugía de EXEC: conectar a un input ya conectado NO reemplaza — los exec aceptan FAN-IN (2026-08-12)
La regla "connecting to an already-connected input REPLACES it" vale para pines de **DATOS**. Los **inputs exec** aceptan **varias entradas** (fan-in legal en Blueprint), así que reordenar una cadena solo con `connect_pins` deja los cables viejos VIVOS y puede formar un **ciclo**.
**El caso que lo probó:** el fix del off-by-one de `BP_SoulChoice.SpawnOne` dejó `SetSpawnIndex.then → SpawnActor.execute` colgado → bucle `Spawn → … → SetIndex → Spawn` → **~300.000 actores spawneados en UN frame**, editor congelado ~5 min (un core clavado, 12 GB), 4× `Runaway loop detected (over 1 000 000 iterations)`. Compiló limpio y el `read_graph_dsl` se veía PERFECTO (el read linealiza y no muestra el segundo cable).
**Reglas:**
1. Al reordenar una cadena exec por cirugía: **`break_pins` explícito de cada cable exec viejo**, no confiar en el reemplazo.
2. Después: `get_node_infos` y verificar que **cada pin `execute` tenga UNA sola entrada** (`connected_pins` de largo 1). Es la única verificación que ve el fan-in; el `read_graph_dsl` NO lo muestra.
3. Un cuelgue de minutos con un core al 100% y memoria subiendo que DESPUÉS se recupera = sospechar **runaway loop de Blueprint** (el detector corta a 1M iteraciones por llamada), no shaders. Grep `Runaway` en el log.

## 🔴🔴 Cirugía de FIRMAS (params de función): termina en compile explícito o el BP queda muerto en silencio (2026-08-13)
**El caso:** la cirugía de capas de `BP_SoulChoice` (2026-08-12) declaró los params `H` como `MotionControllerComponent` mientras las variables `HandR/HandL` eran `SceneComponent`. **El BP quedó SIN COMPILAR toda la jornada** — y nadie lo vio: el run automático no ejercita el camino de las manos, PIE corre igual con el bytecode que sí compiló, y los logs se veían perfectos. En visor, la elección por toque estuvo muerta en TODOS los tests de Beltrán ("tampoco pude elegir" era literal).
**Reglas:**
1. **Toda cirugía que toque tipos o params termina con `compile_blueprint` explícito del BP.** "El run anda" no prueba nada: el run usa el último bytecode bueno.
2. `remove_function_param` + `add_object_function_param` con el mismo nombre → **el nombre viejo queda reservado para siempre** y el param nuevo nace con sufijo (`H` → `H1`). No pelearlo: el nombre del param es cosmético, lo que importa es el cableado.
3. **Los nodos de LLAMADA no se reconstruyen al cambiar la firma de la función**: conservan el pin viejo (con su tipo y sus conexiones) y los errores de compile persisten aunque la función ya esté bien. El fix real: `delete_node` de cada nodo de llamada + `create_node "CallFunction|<Fn>"` + recablear (exec, self implícito, params).
4. Los ids DSL de getters/setters de una variable `bAlgo` estripan la `b`: `add_variable "bHandsNear"` → `Variables|Default|Get/SetHandsNear`.

## 🔴🔴 `write_graph_dsl`: el `(if cond A B)` de 3 argumentos puede salir ENCADENADO, y el read te lo devuelve BIEN (2026-08-13)
**El caso:** se escribió `(if (GetbHandsNear) (SetTimer... 0.3) (CallFunction|ArmPick))` esperando then/else. El writer produjo **`then → SetTimer → ArmPick` y `else → NADA`** (las dos ramas en secuencia sobre el then, else colgado). Y lo peor: **`read_graph_dsl` devolvía el `(if ... A B)` de dos ramas tal como se había escrito** — el read RECONSTRUYE la forma bonita y no refleja el cableado real. Síntoma en runtime: rama false = dead-end silencioso (ni print, ni error, ni reintento).
**Reglas:**
1. Tras escribir un `(if cond A B)` con DSL, **verificar el Branch con `get_node_infos`**: `then` debe ir a A, **`else` debe ir a B** — no confiar en el read.
2. Un camino que muere sin log ni error en un punto exacto = sospechar **pin exec sin conectar** (dead-end legal en Blueprint). El diagnóstico barato: un PrintString quirúrgico al inicio de la función que sí corre, y seguir el exec nodo a nodo con `get_node_infos`.

## 🔴🔴🔴 Verificar la posición del SPAWN no es verificar la posición ESTABLE (2026-08-13)
**El caso que costó TRES días y tres diagnósticos equivocados:** las 5 candidatas de `BP_SoulChoice` nacían en 5 TargetPoints distintos — el log lo probaba, y lo canté como "verificado" tres veces. Pero `BP_ProtoSoul` tenía **`bIsHUD = true` en el CDO**, y su Tick (`HudStep → ApplyPlacement`) teletransporta el actor a la posición del HUD relativa a la cámara. **Un frame después del spawn, las 5 estaban apiladas dentro de la cara del usuario.** El print del spawn decía la verdad en el instante equivocado.
**Reglas:**
1. **Si algo tiene que QUEDARSE en un lugar, la aserción va segundos DESPUÉS de crearlo**, no al crearlo. Patrón: timer a 2-3 s que re-loguea la posición (`LateAudit` en `BP_SoulChoice` es la implementación de referencia). Un actor con Tick puede deshacer en un frame todo lo que el spawn dejó bien.
2. **Antes de spawnear N copias de un BP, mirá su CDO** — un flag de comportamiento en `true` por default (aquí `bIsHUD`) convierte cada copia en algo que no querés. Hermana de [[instance-editable-nace-en-cero]]: ahí el problema era el 0, acá el true.
3. 🔴 **El arnés por log NO ve lo que el usuario ve** (PIE sin manos ni HMD no ejercita casi nada de VR). Cuando el reporte del usuario contradice al log, **el log está midiendo la cosa equivocada** — no insistir con más logs del mismo tipo. **Pedir un VIDEO del visor**: acá 16 frames resolvieron en minutos lo que dos días de logs no.
4. Corolario de honestidad: no decir "verificado" cuando lo verificado es un camino que el usuario no recorre. Decir **qué** se verificó y **qué no**.

## ⚠ Un actor attacheado a la cámara NO sirve para medir la cámara (2026-08-13)
`BP_DebugDirector` está attacheado al `CameraComponent` con **KeepWorld**, así que conserva el offset que tenía al momento del attach: su `GetActorLocation` = cámara + ese offset. Para medir la cabeza de verdad hay que leer el componente:
`GetPlayerPawn(0) → Actor|GetComponentByClass("/Script/Engine.CameraComponent") → Transformation|GetWorldLocation`.
(En este proyecto el offset resultó ~0, pero por casualidad; la lectura correcta no depende de la suerte.)

## 🔴 Agregar un componente a un BP NO lo configura en las instancias ya colocadas (2026-08-13)
Se agregó un `TextRenderComponent` a `BP_Anchor` **después** de colocar 14 instancias. Las instancias recibieron el componente **con los defaults de UNREAL**, no con los valores del CDO: `bHiddenInGame=false` (los rótulos de debug se habrían visto EN JUEGO) y `WorldSize=26` en vez de 8. Es la familia de [[instance-editable-nace-en-cero]], pero para componentes.
**Regla:** tras agregar un componente a un BP con instancias en el nivel, **setear sus propiedades en CADA instancia y verificar el valor efectivo** (un `ProgrammaticToolset` con un bucle lo hace en una llamada).
⚠ Y un detalle que muerde: **`WorldSize` (y floats en general) sólo tomó `8.0`**; con `8` entero, `set_properties` devolvió `true` y el valor siguió en 26. **Escribir los floats con decimal, y releer.**

## 💡 Para enriquecer un actor "marcador" ya cableado por clase: HEREDÁ de esa clase (2026-08-13)
`BP_Anchor` (marcador visible con mesh + rótulo) se hizo **hijo de `TargetPoint`**, así que los ~8 buscadores existentes `GetAllActorsOfClassWithTag(TargetPoint, tag)` lo encuentran sin cambiar una línea (el filtro de clase es por `IsA`). Alternativa descartada: cambiar la clase en cada buscador — más trabajo y más superficie de error.

## 🔴🔴🔴 Escribir `SplineCurves` por propiedad puede MATAR el editor (2026-08-13)
`ObjectTools.set_properties` sobre `SplineCurves` de un `SplineComponent` **vivo en el viewport** tiró el editor entero:
```
Assertion failed: Rotation.Points.Num() == NumPoints && Scale.Points.Num() == NumPoints
  SplineComponent.cpp:738
```
**Por qué es una trampa con gatillo:** UE exige que las curvas `position`, `rotation` y `scale` tengan **siempre la misma cantidad de puntos**. Pero un solo `set_properties` que **agrande** el array falla con *"ArrayAdd: elements changed alongside the size change"*, así que el único camino es de **DOS pasos** (vaciar `[]` → escribir los puntos)… y entre esos dos pasos el spline queda inconsistente. Si el engine lo toca en esa ventana (redibujo del visualizador, el actor seleccionado, un tick del editor), **assert y crash**.
**Reglas:**
1. Escribir puntos de spline por propiedad **sólo sobre el CDO de un BP que no esté abierto**, nunca sobre una instancia colocada y menos si está seleccionada. Funcionó así la primera vez (`BP_Journey` recién creado); explotó al repetirlo sobre la instancia del nivel.
2. Si el spline hay que rearmarlo por código de forma recurrente, **no se escribe la propiedad**: se hace desde el **Construction Script** con `ClearSplinePoints` + `AddSplinePoint` desde un array editable. Es el único camino que no deja la ventana inconsistente.
3. Tras un crash así: el disco conserva lo último **guardado**. Commitear seguido es lo que convierte un crash en 2 minutos perdidos en vez de una tarde.

### 🆕 Y sobre una instancia con puntos ARRASTRADOS: no crashea, pero NO APLICA (2026-08-13 tarde)
Con la instancia ya editada en el viewport (override propio), `set_properties(SplineCurves)` con el struct completo y **la misma cantidad de puntos** devuelve `true` y **no cambia nada**: el *component instance data* del spline restaura las curvas del arrastre tras el PostEditChange. Es "declarado ≠ aplicado" en su forma más silenciosa — verificar SIEMPRE releyendo.
**La receta que sí funcionó** para re-escribir paradas por MCP:
1. `set_properties(SplineCurves)` sobre el **template del CDO** (`<BP>_C:Route_GEN_VARIABLE`, vía `get_default_object` + `get_components`) — con el mismo conteo alcanza UNA llamada (el two-step es sólo para redimensionar). Verificar y compilar.
2. **`remove_from_scene` + `add_to_scene_from_asset`**: la instancia nueva hereda del CDO. Se pierden los overrides de instancia (re-setear `LegTimes` y verificar sobre la instancia).

## 🌾 COSECHA 2026-08-13 (la jornada esqueleto→obra) — trampas técnicas nuevas, todas pagadas
**Del DSL / cirugía:**
1. **`add_event("Destroyed")` crea un CustomEvent INÚTIL** (nunca dispara). El evento real del motor va por `create_node("AddEvent|EventDestroyed")`.
2. **El pin exec de salida de un nodo de EVENTO es index 1** (el 0 es el delegate). En nodos normales es 0.
3. **`elif` se ANIDA**: debe ser la última forma dentro del cuerpo del if/elif anterior, no un hermano.
4. **Statements después de un `(if)` caen DENTRO de la última rama** — no continúan la cadena. Si algo debe correr en ambos caminos: cablear fan-in por cirugía, o reestructurar con el if al final.
5. **Un `(Utilities|IsValid ...)` que no sea la última forma** hace el resto "unreachable" para el parser → extraer a función guardia (`KillIfValid(A)`) y encadenar llamadas planas.
6. **Los property-setters (`Class|X|SetVar`) toman el VALOR como primer posicional y el target segundo** — `(Set... true Lvl)`. Las funciones normales son target-first. El error de pines lo delata.
7. **Los operadores promotables (`float+float`, `vector+vector`) NO se pueden crear con `create_node`** (no aparecen en `find_node_types`). Solo el `write_graph_dsl` los resuelve → patrón **"función puente"**: escribir la aritmética en una función NUEVA por DSL y llamarla con un solo nodo de cirugía.
8. **`remove_function_graph` + `add_function_graph` inmediato puede devolver un nombre fantasma** (`X_0`). Receta: borrar el `_0`, compilar (falla — purga el nombre), re-crear con el nombre bueno.
9. **Retipar una variable (remove+add) BORRA sus getters/setters en los grafos** y deja los nodos llamadores de funciones con el pin del tipo viejo (no se refrescan al compilar) → recrear los grafos afectados por DSL.
10. **`GetActorOfClass` como bind: su output 0 es el exec `then`; el ReturnValue es index 1.** Conectar el 0 a un pin de datos da "incompatible types".
11. **Una función propia BlueprintCallable (no pure) como `GetLegTime` va EN la cadena exec** — el DSL la muestra inline como si fuera pure, pero la cirugía necesita cablearle el exec.
12. **`arrange_nodes` no toma un grafo: toma `nodes` (array de refPaths)** — receta: `find_nodes(title:"")` → pasar todos.
13. **Un cleanup por timer-loop MUERE con el actor destruido** (los timers de un actor destruido no disparan) → para limpiar N spawneados desde `EventDestroyed`, cadena SÍNCRONA de llamadas (KillOne×N), no un loop re-agendado.
14. **`execute_tool_script`**: `_StrictDict` sin `.get(default)`; un script fallido rollbackea `create_node` pero NO `remove_from_scene`; `try/except` de Python puro (parsing) SÍ funciona — lo que aborta es el fallo de una tool.
15. **`shutdown /r` desde el Bash tool falla** (MSYS convierte los flags en rutas) → comandos con flags `/x` van por el tool PowerShell.
16. **`SetActorHiddenInGame` idempotente por poll** es la forma barata de mantener oculto un actor que otro sistema spawnea (el detector invisible pegado a la mano).

**De la arquitectura (decisiones que ya no se re-discuten):**
- **El mapa es la autoridad de posición** de cada sala; parada del Journey debe coincidir. El director no mueve actores.
- **Los puntos/spawns propios de UNA sala viven DENTRO de su sublevel** (la búsqueda por tag queda per-sala por visibilidad). Los del recorrido/menú, en el persistente. Un tag compartido en el persistente contamina TODAS las salas.
- **Los sensores persistentes son LA herramienta**: las etapas no spawnean objetos de mano visibles — incorporan su detector INVISIBLE a la mano (`ForceAttachToHand` + hide por poll). Patrón probado 2×: Breath y Heart.

## 🔴 `bIsEditorOnlyActor` NO impide que un `LevelInstance` cargue en PIE (2026-08-13)
Para ver las 6 salas en el editor se probó poner **actores `ALevelInstance`** apuntando a cada `L_Room_*.umap`, marcados con `bIsEditorOnlyActor = true`. **Igual cargan su nivel en PIE**: el contador `GetAllActorsOfClass(BP_Room)` dio **2** en un momento donde sólo debía haber **1** (una sola precarga hecha). O sea, salas duplicadas en juego.
**Lo que sí funciona** para "visible en el editor, inexistente en juego": una **instancia del actor real con un flag `bEditorPreview`** que en `BeginPlay` haga `DestroyActor(self)`. Determinista, verificable y sin depender de semántica de cook. Implementado en [[BP_Room]]; verificado con el contador dando **1**.
💡 **El test que lo decide** no es mirar el viewport: es **contar los actores en PIE** en un instante donde sabés cuántos debería haber.

## 🌾 COSECHA 2026-08-14 (BioHub 3 señales + BP_SoulHUD) — trampas nuevas
1. 🔴🔴 **`Utilities|IsValid` en posición de EXPRESIÓN resuelve al MACRO multi-exec y el `write_graph_dsl` produce un grafo ROTO que COMPILA en verde**: el cuerpo entero queda como isla desconectada (la función corre vacía) y el PIE "pasa" sin hacer nada. El caso: `(if (and (> n 0) (Utilities|IsValid bio)) ...)` en `BP_SoulHUD.GraphStep`. **Lo delató el barrido de huérfanos** (20 borrados / 3 vivos) + el `read_graph_dsl` posterior. Reglas: (a) IsValid SIEMPRE como statement con `(:"Is Valid")`; (b) un guard dentro de una condición se extrae a función; (c) **después de CADA `write_graph_dsl`, LEER el grafo** — el éxito del write y el compile verde no prueban nada.
2. **`Actor|GetComponentsbyTag` pierde SUS DOS args posicionales en silencio** (quedó `ComponentClass=ActorComponent`, `Tag=None` → 0 resultados en runtime, sin error). Fix por `set_pin_value` de los pines 1 y 2. Ante nodos con args clase+name, verificar pines tras el write.
3. **La colisión de un componente en el template del CDO es `BodyInstance.collisionEnabled` (anidada)** — `collisionEnabled` plano no existe ahí (ni para leer). `{"BodyInstance": {"collisionEnabled": "NoCollision"}}` funciona (21/21 verificado).
4. **Args con expresión a funciones propias o setters con pin `self`**: el posicional intenta conectarse al pin `self` ("Could not connect pin X to self") → usar **keyword args** (`:Suffix`, `:NewRelativeLocation`, `:Addr`). Con literales simples el posicional anda.
5. **No existe conversión explícita `ToFloat(Integer)` en el DSL** — el operador promotable (`(* 0.2 int)`) promueve solo.
6. **`CaptureViewport` con PIE corriendo puede capturar el viewport del EDITOR** (se delata por el gizmo de ejes en la esquina), no la vista del juego → dos capturas idénticas con el mundo cambiando = estás mirando el editor. Para verificar algo head-locked/de juego: log + visor.
7. **`SceneTools.add_to_scene_from_class`** existe para clases del motor (TargetPoint); `add_to_scene_from_asset` solo para assets. Y el `xform` se ignora igual (trampa vieja): setear `relativeLocation` del root component después y verificar con `get_actor_transform`.
8. 🔴 **La trampa #1 de esta cosecha MORDIÓ DOS VECES EL MISMO DÍA** (`(if (and (Utilities|IsValid a) (Utilities|IsValid b)) ...)` en `UpdateHud`/`ConnStep` — cuerpos desconectados, compile verde). El patrón correcto para doble guard: IsValid del primero como statement → en su `:then`, llamar una función `ApplyX` que hace el IsValid del segundo. **El barrido de huérfanos post-escritura es lo que la detecta**: correr SIEMPRE el sweep después de una tanda de writes y sospechar de cualquier `deleted >> remaining`.
9. **UMG por MCP** (`UMGToolSet` + `ObjectTools`): los widgets del árbol son variables bajo **`Variables|WBP_<Nombre>|Get<Widget>`** (no `Variables|Default|`) · las funciones de widget estilo `SetPercent`/`SetColorandOpacity` existen en DOS formas — la de función (`Progress|SetPercent`, target primero) y la property-setter (`Class|X|Set...`, VALOR primero) — si una falla por pines, probar la otra · `Utilities|Array|MakeArray` del DSL acepta UN solo pin (armar arrays con N `Array Add` en cadena) · el evento Construct se escribe **`(event UserInterface|EventConstruct ...)`** · círculos/píldoras sin texturas = brush `RoundedBox` + `outlineSettings.roundingType=HalfHeightRadius` · los slots se configuran por `ObjectTools.set_properties` con los nombres EXACTOS de `list_properties` (CanvasPanelSlot=`layoutData.offsets`, HorizontalBoxSlot=`size`/`padding`/`verticalAlignment`).
10. **`remove_component` compila y FALLA si un grafo referencia el componente** ("self is not a SceneComponent...") — reescribir/vaciar primero las funciones que lo usan, borrar componentes después. El orden importa.
11. **Override de `OnPaint` (UMG) por MCP — receta inversa a `RunStage`**: `add_event("OnPaint")` falla ("inherited function-shape override; must be placed as a function graph") → **`add_function_graph("OnPaint")`** lo crea con su param `Context` y `(return)` listos. `Painting|DrawLines(Context, Points[], Tint, bAntiAlias, Thickness)` dibuja polilíneas en el espacio local del widget — la vía widget-nativa para gráficos de onda en tiempo real (reconstruir el array de puntos al llegar la MUESTRA, no en cada paint).
12. 🔴🔴 **INSTANCIAS FANTASMA tras churn de componentes en el CDO** (2026-08-14, BP_SoulHUD ×2): una instancia colocada de un BP cuyo CDO sufrió agregar/quitar componentes repetido queda en estado corrupto — `get_properties`/`get_actor_transform` RESPONDEN normal, pero el actor **no renderiza nada** (ni un cubo de 1 m), sus componentes no aplican `set_properties` (leen valores viejos tras un set exitoso) y **`remove_from_scene` devuelve `false`**. El diagnóstico que lo separó de "el widget no se ve": FocusOnActors + captura → ni la MALLA de control renderizaba. **Fix: borrar la instancia A MANO en el Outliner (o reiniciar el editor) y colocarla de nuevo con el CDO ya estable.** Regla: colocar instancias de un BP DESPUÉS de estabilizar su set de componentes, no entre cirugías.
13. 🔴 **`SetActorRelativeLocation` sobre un padre ESCALADO se multiplica por su escala** (2026-08-14, el HUD invisible en Play): el HUD colgado del cubo de cabeza (escala 0.15) con offset (40,0,−8) terminó a **4,5 cm** del ojo — dentro de la esfera de fade, invisible. La posición relativa vive en el espacio escalado del padre. Regla: attachear objetos head-locked **DIRECTO al CameraComponent del pawn** (escala 1); los actores de referencia escalados (cubo) no son padres válidos para offsets en cm. **Lo que lo encontró: la aserción espacial por log** (`VerifyHudPose`: distancia HUD→cámara 1 s después del attach) — el "attacheado OK" del log de flujo decía verdad y mentía a la vez: attacheado sí, a 4,5 cm.
14. 🔴 **Un actor de REFERENCIA que se mueve en runtime invalida las restas contra él** (2026-08-14, la ameba a 184 cm): el offset autoral "TP − cubo de cabeza" se calculaba bien en el HUD (lee el cubo ANTES de pegarlo a la cámara) pero mal en la ameba (para entonces el cubo YA estaba en la cámara). Regla: el PRIMER lector cachea la posición autoral (`HeadRefLoc` del BP_SoulHUD) y los demás **leen el valor cacheado, nunca el actor vivo**. Lo delató (otra vez) la aserción espacial: 184 cm contra los 32,76 esperados.
15. **UMG remates de la jornada HUD** (2026-08-14, tarde): (a) 🔴 **el render target del WidgetComponent RECORTA en el DrawSize** — un widget arrastrado fuera del lienzo (el recuadro punteado del Designer, acá 800×400) se ve en el Designer pero DESAPARECE en el actor/mundo/Play; si "se ve en el WBP pero no en el BP", medir los `layoutData.offsets` de los CanvasPanelSlots primero. (b) **`HalfHeightRadius` degenera en una LENTE en barras más altas que anchas** (radio = mitad de la ALTURA): para barras verticales usar `FixedRadius` con radio = mitad del ANCHO (cápsula); HalfHeight solo para círculos y píldoras horizontales. (c) **El track por defecto del ProgressBar es casi invisible sobre fondo oscuro** — setear `widgetStyle.backgroundImage`/`fillImage` explícitos. (d) **Translúcido sobre el vacío negro se lava**: alphas ≥0.5 para elementos que deben leerse "suaves"; el fondo oscuro ya aporta la suavidad.

## 🌾 COSECHA 2026-08-14 (tarde) — la ceremonia de carga
16. 🔴🔴🔴 **EL DSL RESUELVE UN NOMBRE DE FUNCIÓN AMBIGUO A LA CLASE EQUIVOCADA, Y COMPILA EN VERDE.** Escribiendo `(CallFunction|CacheSoul)` y `(CallFunction|CacheHud)` dentro de `BP_Ceremony` — que **tiene** esas funciones — el write produjo `Class|BPSelfTest|CacheSoul` y `Class|BPSoulChoice|CacheHud`. Idem `(CallFunction|CacheDirector)` → `Class|BPDebugDirector|CacheDirector`. Compila, corre, y llama al objeto equivocado. Ya había mordido con `CacheJourney` (2026-08-13) y **volvió a morder 3 veces en un rato**: no es una rareza, es el comportamiento por defecto ante homónimos.
    - **Lo detecta el `read_graph_dsl` post-write** (aparece `Class|OtroBP|...` donde debía decir `CallFunction|...`). El compile no dice nada.
    - **Regla dura del proyecto: los nombres de función deben ser ÚNICOS ENTRE TODOS los Blueprints.** Prefijar por dominio (`CacheCeremonySoul`, `CacheStageDirector`, `SeedSoulRings`) sale gratis y elimina la clase entera de bug.
17. 🔴🔴 **El registro de nodos NO ve las FUNCIONES de una clase de BP creada en la MISMA sesión** — pero sí ve sus componentes, así que `find_node_types` devuelve `Class|BPNuevo|GetDefaultSceneRoot` y **parece** que la clase está. En cambio, las funciones NUEVAS de una clase que **ya existía** al arrancar el editor sí aparecen (verificado: el director veía `Class|BPProtoSoul|SeedRings` recién creada). O sea: el problema es la CLASE nueva, no la función nueva.
    - **Solución de diseño, no workaround: invertir la dependencia.** El BP viejo publica el pedido en una **variable propia** (`CeremonyRequest`) y el BP nuevo la poll-ea y devuelve el resultado llamando una función del viejo (eso sí resuelve). Bonus: el viejo sigue funcionando si el nuevo no existe.
    - Colocar el actor nuevo **a mano en el nivel** (`add_to_scene_from_asset`) también esquiva el problema de tener que spawnearlo desde el BP viejo.
18. 🔴🔴 **Un `Tick` sin gate que escribe la transform PISA el attach, y el log de flujo no se entera.** `TravelAdvance` corría desde `BeginPlay` (me olvidé el `if bTraveling`) haciendo `SetActorLocation(Lerp(0,0,0 → 0,0,0))` cada frame: el actor quedó clavado en el origen del mundo mientras el log decía "anclada al slot" (cierto… durante un frame). **Lo cazó la aserción espacial**: `SOUL POSE: distancia a la camara cm = 3600.0`, que es exactamente la X de la sala. Regla: **todo escritor de transform por Tick empieza por su gate**, y toda cadena attach→algo lleva una aserción de distancia 1 s después.
19. **`Variables|Getareferencetoself`**, NO `Utilities|...` — el nodo "self" para el pin `Object` de un `SetTimerByFunctionName` creado por cirugía. Con el nombre equivocado, `create_node` falla con "does not exist" (barato); lo caro es no ponerlo: el pin queda en 0 y **el timer no dispara nunca**.
20. **Un write que falla ROLLBACKEA limpio** (verificado con `find_nodes`: quedó sólo el `K2Node_FunctionEntry`). Así que ante un error del parser se puede corregir y reescribir el mismo grafo sin miedo a duplicar — pero **verificalo con `find_nodes` antes**, no lo asumas.
21. **Material de anillo procedural sin texturas, receta completa** (`M_SoulRing`): `mask = saturate(1 − |Distance(TexCoord,(0.5,0.5)) − Radius| / Thickness)` (caída triangular = borde blando gratis, 6 nodos) × `sweep = saturate((Progress − angle01)×40)` con `angle01 = Arctangent2Fast(dy,dx)/6.2831853 + 0.5`. Unlit + **BLEND_Additive** + TwoSided; `Emissive = Color×Brightness`, `Opacity = mask×sweep`. ⚠ **El barrido necesita que `Progress` llegue a ~1.05**, no a 1.0: en la costura `Progress − angle01` da 0 y el último gajo del anillo nunca se enciende.
22. **`Rendering|Material|SetColorParameterValueonMaterials`** existe además de `SetVector...` y toma un **LinearColor** (el `SetVector...` toma un FVector, sin alfa). Su pin `self` es *Mesh Component*, así que sirve para StaticMeshComponent y crea el MID solo. Es la vía corta para tintar un componente desde un array de `LinearColor`.

## 🌾 COSECHA 2026-08-14 (noche) — el rework de Entering
23. 🔴🔴 **La trampa "los literales de una función PROPIA se pierden" TAMBIÉN pasa con ENTEROS** — `dsl.md` §4 la documentaba sólo para strings. Escribiendo `(switch ... (:0 (CallFunction|GotoPage 2)) (:1 (CallFunction|GotoPage 2)) (:2 (CallFunction|GotoPage 3)) (:3 (CallFunction|GotoPage 4)))` **las cuatro ramas quedaron en `GotoPage(0)`**: un cortafuegos de páginas que, en vez de avanzar, habría devuelto al usuario a la página 1 para siempre. Compila en verde. **Lo cazó el `read_graph_dsl` post-write**; arreglado con `set_pin_value` del pin del parámetro (índice 2: execute=0, self=1, param=2). **Regla ampliada: después de escribir un grafo que llame funciones propias con CUALQUIER literal, leerlo.**
24. **`Actor|DestroyActor`**, no `Game|DestroyActor`. La forma barata de acertar: **leer una función del mismo BP que ya lo haga** (acá `CleanupBox`) en vez de adivinar el namespace.
25. **`Variables|Getareferencetoself`** y **`Rendering|Components|TextRender|SetText`** — dos ids que no salen por intuición. El `SetText` de TextRender está bajo `Rendering|Components|`, no bajo `Widget|` (que es el de UMG) ni `Class|Text|`.
26. **Crear la API ANTES de llamarla, cuando cruza Blueprints.** `write_graph_dsl` de `NotifyPacerStage` falló con *"Class|BPStageEntering|PacerFinished does not exist"* porque la función todavía no existía en el otro BP. El orden correcto es: crear la función destino → compilar el BP destino → recién ahí escribir el llamador.

## 🌾 COSECHA 2026-08-15 — la explicación de etapas del Hall (BP_StageIntro)
27. 🔴🔴 **La trampa del NODO PURO re-evaluado volvió a morder — y ya estaba documentada acá arriba** (§"Nodos PUROS: se re-evalúan en CADA consumidor"). Lo nuevo y útil es **su firma clínica**: cuando el puro alimenta a la vez el argumento Y la condición de corte, el síntoma es un **off-by-one en DOS lugares al mismo tiempo** (arrancó en la etapa 1 en vez de la 0 **y** cortó una etapa antes). Si sólo estuviera mal el argumento, sería otra causa. Regla de reconocimiento: *dos off-by-one simultáneos = un puro leído a través de una escritura*.
28. **`UMGToolSet.AddWidget` informa `bIsVariable: true` pero NO lo aplica.** Los hijos del widget tree no existen como `Variables|<WBP>|Get<Hijo>` hasta llamar **`ToggleWidgetAsVariable`** por cada uno **y** **`CompileWidgetBlueprint`** (el `compile_blueprint` genérico no alcanzó).
29. **`find_node_types` no es prueba de ausencia.** Aun después de que los getters de los hijos del widget existían (y `write_graph_dsl` los resolvía sin chistar), `find_node_types` seguía devolviendo lista vacía para ellos. Se perdió tiempo buscando un problema que no existía.
30. **`ObjectTools` cambia el nombre del parámetro según la tool**: `get_properties` = `instance` + **`properties`**; `set_properties` = `instance` + **`values`**. Con el nombre equivocado el error habla de "input param X is required", no de la propiedad.
31. **Llamar una función PROPIA con posicionales puede enchufar el primer arg al pin `self`** → *"Could not connect pin ReturnValue to self"*. Usar keyword: `(CallFunction|MiFn :Param v)`. Lo mismo para el **setter de una variable de OTRO objeto**: `(Class|BPProtoSoul|SetIsHUD :self obj :bIsHUD false)`; con posicionales el target se va al pin de valor.
32. **`StartPIE` puede devolver `"Timed out waiting for PIE to start"` habiendo arrancado igual** — los logs de esa corrida son válidos y hay que leerlos. Pero **hay que `StopPIE` antes del siguiente `StartPIE`**, o el segundo falla con *"A play session is already running"*.
33. 🔴 **Elegir un prefijo de log sin buscarlo primero cuesta una corrida.** `INTRO:` ya lo usaba `BP_IntroSequence` (logos + menú de arranque): la primera lectura del log mezcló las dos cosas. Se renombró a `EXPLICA:`. **Antes de estrenar un prefijo, `GetLogEntries` con ese patrón.**
34. Un `WidgetComponent` puede **crear su widget DOS VECES** en el arranque (se midió: dos `Construct` con 2 frames de diferencia). Si se cachea la referencia, se termina pintando un widget que ya no es el que se ve. **Releer `GetUserWidgetObject` en cada uso** y hacer la función de pintado **idempotente** (repintar el estado completo, no sólo el delta).
35. Los `Event Tick` / `Event PreConstruct` / `Event ActorBeginOverlap` **vacíos** que deja `write_graph_dsl` al escribir un EventGraph hay que **borrarlos**: un Tick vacío igual tickea (y en un widget, igual invalida).
36. **`bUsedWithUI` no es una propiedad seteable** de un material; para un material de UI el campo es **`materialDomain: "MD_UI"`**.

## 🌾 COSECHA 2026-08-15 (tarde) — el framework de audio + haptics
37. 🔴🔴🔴 **`(return (CallFunction|MiFuncionImpura …))` conecta el VALOR pero deja el nodo FUERA de la cadena de exec.** El grafo queda `Branch --then--> FunctionResult` y la llamada cuelga sola con su `then` en `[]`. **Compila en verde y devuelve el default del pin.** En el caso real el llamador tenía un fallback razonable, así que **el tiempo medido era idéntico al correcto** — el bug era invisible por temporización; lo delató que faltaba una línea de log. **La forma correcta: llamar como statement, bindear, y devolver la variable** → `(bind _d (CallFunction|X …))` + `(return _d)`. Verificar SIEMPRE con las conexiones de exec (`get_node_infos`), no con el `read_graph_dsl`, que imprime las dos formas igual.
38. 🔴🔴 **`clean_orphans.py` NO limpia los restos de reescribir una función CON VALOR DE RETORNO**: `K2Node_FunctionResult` está en la lista `ENTRY`, así que cada `FunctionResult` viejo se marca vivo y **mantiene viva toda la isla muerta que lo alimenta**. El barrido reporta 0 huérfanos y el grafo tiene una copia entera de la versión anterior. **Hay que borrar a mano los `FunctionResult` sobrantes antes de barrer.** (Con funciones sin retorno esto no pasa.)
39. **Los Map SÍ se crean por MCP**: `add_object_variable` con `container_type: "Map"` da *Map of Strings to Sound Base Object References* — clave String por defecto. No hace falta el truco de dos arrays paralelos.
40. 🔴 **`Audio|Components|Audio|FadeIn`/`FadeOut` están DUPLICADOS** (AudioComponent y SynthComponent) y el DSL agarra el de **Synth**. Se ve en el pin `self`: *Synth Component Object Reference*. Salida: `create_node` con **`declaring_class: /Script/Engine.AudioComponent`** y cablear por cirugía; conviene encapsularlo en una función mínima de 2 nodos para poder llamarla desde el DSL.
41. **Un pin de ENUM sólo acepta un literal, nunca un cable.** `(select bRight "Right" "Left")` en el pin `Hand` de `SetHapticsByValue` falla con *"Could not connect pin ReturnValue to Hand"*. Solución: ramificar con un `if` y poner el literal en cada rama — o pasar la elección como `bool` y resolverla adentro.
42. **`Class|SoundBase|GetDuration` se lee como un VARIABLE GETTER** (`|GetDuration` con `self` de tipo *Sound Base Object Reference*), y el `read_graph_dsl` lo etiqueta como `Components|GeometryCache|GetDuration`. Otra vez: **la etiqueta del read no es prueba de nada**, `get_node_infos` sí.
43. **`remove_function_param` exige `input_param`** aunque el nombre del parámetro ya lo identifique. Y **un script de `execute_tool_script` que falla ROLLBACKEA los `add_function_graph` previos** del mismo script — hay que rehacerlos.
