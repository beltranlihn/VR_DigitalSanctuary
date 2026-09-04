# Gotchas & hard rules (hard-won — don't relearn these)

## 🔴🔴🔴 Un nodo PURO se re-evalúa UNA VEZ POR CONSUMIDOR — si lee una variable que el mismo grafo escribe, cada consumidor ve un valor distinto
**El caso real (2026-08-16, costó todo un día en dos frentes).** `BP_AttractDirector.OnBeat` calculaba el paso del secuenciador así:

```
paso = (CurrentStep + 1) % NumSteps        ← nodo PURO
   consumidor 1: SetCurrentStep(paso)      ← ¡escribe CurrentStep!
   consumidor 2: IsValidIndex(slots, paso)
   consumidor 3: Get(slots, paso)          ← el slot que pulsa
   consumidor 4: ToString(paso)            ← el print "STEP n"
```

El compilador **copia el bytecode del puro una vez por cada consumidor** (ver `bp-lean-construction.md`, probado en `KismetCompiler.cpp`). El consumidor 1 actualiza `CurrentStep`; los otros tres **vuelven a calcular** leyendo el valor ya actualizado y salen **un paso adelante**. Resultado: el slot que pulsaba iba siempre uno adelante de la variable, el pad entraba en el slot equivocado, y una perilla de fase (`StepPhase`) fue "compensando" el síntoma con valores raros durante días.

**Lo que lo delató:** un log con las dos cosas en el mismo latido — `PAD entra en CurrentStep=0` y `STEP 1`. Imposible de deducir leyendo el grafo.

**La regla:** si un nodo puro depende de una variable que se escribe en ese mismo grafo, **no lo consumas más de una vez**. Cableá los consumidores al **valor guardado** — el pin de salida `Output_Get` del nodo `Set`— o cacheá el resultado en una variable local antes de usarlo. Vale para `%`, `+`, getters compuestos, cualquier pure.

**Olor a este bug:** una perilla de offset/fase que "casi" funciona y hay que retocar cada vez.

## 🔴🔴 Enhanced Input: el pin `Triggered` dispara CADA FRAME mientras el botón está apretado
No es un flanco. `BP_BrushTool` cableaba `IA_Shoot_Right → Triggered → bTrigHeld = true`, así que cualquier intento externo de apagar `bTrigHeld` duraba **un frame** y el input lo volvía a encender.

Síntoma típico: un guardia externo (una esfera límite, un bloqueo por zona) **loguea que actuó** y aun así la acción sigue ocurriendo. Se buscó el error en la geometría, que estaba perfecta (detectaba a 44,7 cm sobre un radio de 45).

**La regla:** nunca bloquees una acción pisando la variable que el input escribe. Agregá una **variable de bloqueo aparte** (que el input no toque) y sumala a la condición — `AND(bTrigHeld, NOT bOverPalette, NOT DrawBlocked)`. El que bloquea la enciende al entrar y **la apaga al salir**, así no hay que soltar y volver a apretar.

⚠ Y para nombrarla: usá un nombre **sin prefijo `b`** (`DrawBlocked`, no `bDrawBlocked`) o caés en el muro de los `b` y no la vas a poder escribir por DSL desde su propia clase.

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
| `r.MobileMSAA=4` | **No existe** (encontrado 2026-08-21, heredado del VRTemplate). En todo `Engine/Source` la cadena `MobileMSAA` aparece **solo como nombre de variables C++ internas** (`bool bMobileMSAA`), nunca como CVar registrado. El del sample count es **`r.MSAACount`** (`SceneTextures.cpp:48`, **default 4**), leído por `GetDefaultMSAACount()` (`SceneUtils.cpp:184`). Nos salvó que el default ya era 4 — el MSAA sí corría en 4x. |

🔴 **El log del device delata los CVars muertos y es la forma más barata de cazarlos.** La línea es literal:
```
LogConfig: CVar [[r.MobileMSAA:4]] deferred - dummy variable created
```
**`dummy variable created` = ese CVar NO EXISTE**: el motor creó una variable fantasma para guardar el valor de un nombre que nadie lee. Compará contra un CVar sano, que sale como `LogConfig: Set CVar [[r.MaxAnisotropy:16]]`. Un `grep "dummy variable created"` sobre el log de un build es una auditoría completa de la config en un segundo.
⚠ Ojo con un falso positivo: `bIsFBFoveationEnabled` también sale como *dummy* y **sí funciona** — porque no es un CVar sino una propiedad de `[/Script/OpenXRHMD.OpenXRHMDSettings]`, que se lee por otra vía.

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
xr.SecondaryScreenPercentage.HMDRenderTarget=135   ; 100=recomendado del runtime, 125~=panel nativo Quest 3
xr.OpenXRFBFoveationLevel=1         ; 1=Low. Nivel 2-3 degrada visiblemente texto/UI del centro
xr.OpenXRFBFoveationDynamic=0       ; 🔴 ver abajo: en 1 el aliasing aparece y desaparece solo
r.VRS.Enable=1                      ; el FFR por hardware necesita Support(ya=1) Y Enable
r.MSAACount=4                       ; el nombre REAL (r.MobileMSAA no existe)
```

🔴 **`xr.OpenXRFBFoveationDynamic=1` produce aliasing INTERMITENTE** (diagnosticado 2026-08-21). La doc del motor es literal — [SRC] `FBFoveationImageGenerator.cpp:16`:
> *"Whether dynamically changing foveation based on performance headroom is enabled."*

Con `1`, cuando la GPU se aprieta el runtime **sube solo el nivel de foveación** (1→2→3), y 2-3 degradan visiblemente. En una obra **fill-rate bound** eso significa que la periferia pierde resolución justo en las escenas cargadas → **diente de sierra que aparece en algunas salas y no en otras**, sin que cambie nada del contenido. Es de los síntomas más confusos de perseguir, porque no correlaciona con ningún asset.
**En `0` la foveación queda clavada en `Level` y nunca degrada: predecible le gana a adaptativo** cuando la calidad de imagen es el objetivo. El precio es que ya no hay red de seguridad automática de framerate — vigilar OVR Metrics.

**Y lo que NO existe / no sirve en mobile forward** (no perder tiempo): TAA, TSR, TAAU y FXAA no están soportados en Forward (solo MSAA); `r.Tonemapper.Sharpen` no es de móvil y además con `r.MobileHDR=False` no hay tonemapper; MSAA >4x lo desaconseja Meta (mejor gastar en resolución). 🔴 **MSAA no actúa sobre objetos transparentes** → el aliasing de UI/iconos alpha-blend de un WidgetComponent (vive DENTRO de un render target) no lo arregla ningún MSAA; ahí las palancas son resolución de render, ajustes de textura, y sobre todo **Stereo Layers** (el panel va al compositor y no sufre el resampleo del eye buffer).

---

## 🔴 Triaje del aliasing: MSAA arregla UNA sola de las tres clases (2026-08-21)
Antes de tocar nada, **clasificar el borde**, porque las tres clases tienen arreglos distintos y disjuntos. Perseguir la clase equivocada es gratis en tokens y caro en jornadas.

| Clase | Dónde se ve | Lo arregla | NO lo arregla |
|---|---|---|---|
| **Silueta de geometría** | Cantos de meshes contra el fondo | **MSAA** · resolución de render · foveación fija | Nada de texturas |
| **Borde de alpha del shader** | SDF de esquinas, máscaras de esfera, bordes de translúcidos | Ensanchar la transición alpha en el **material** (ver `BP_CalibDirector.md`: `AlphaSharpness` 16→5) · resolución | 🔴 **MSAA no toca transparencias** |
| **Textura / patrón** | Grillas, tiling, detalle fino en ángulo rasante | **mips + anisotropía + trilineal** · resolución | 🔴 **MSAA tampoco**: el patrón está DENTRO del triángulo, no en una silueta |

**La pregunta que discrimina en 10 segundos:** *¿se ve mal solo al inclinar/mover la cabeza, y el patrón es repetitivo?* → es **textura**, no bordes. Si el usuario dice la palabra "textura", creerle.

### El caso del piso de la obra: aniso SIN trilineal
El piso usa `M_RoomInterior` con `/Game/XRFramework/Textures/T_Grid` (grilla del VRTemplate: alto contraste, muy tileada — `localUVDensities` ~4398 en el mesh). La textura estaba **perfectamente configurada** (mips ON, `TEXTUREGROUP_World`, sRGB, `Filter=TF_Default`) y aun así aliaseaba.

**La causa estaba un nivel más arriba**, en el grupo de texturas que la textura hereda por tener `TF_Default`. Heredado de `[GlobalDefaults DeviceProfile]` (`BaseDeviceProfiles.ini:184`):
```
TEXTUREGROUP_World ... MinMagFilter=aniso, MipFilter=point
```
[SRC] `TextureLODSettings.cpp:130-137` — `aniso` + `MipFilter=point` resuelve a **`AnisotropicPoint`**: anisotrópico **sin trilineal**. El salto entre mips es un **corte duro, sin mezcla** → costura de mip visible que "nada" al mover la cabeza. Con `MipFilter=linear` resuelve a **`AnisotropicLinear`** = aniso **+** trilineal, y la costura desaparece.

⚠ **No se arregla en el asset:** poner `Filter=TF_Trilinear` en la textura mapea a `SF_Trilinear`, que **pierde la anisotropía** (misma función, rama `MinMagFilter=linear`). En un piso en ángulo rasante la anisotropía importa más que el trilineal → hay que conservar **las dos**, y eso solo se puede desde el grupo.

**Cómo sobrescribir un grupo de texturas sin romper los otros 40:**
[SRC] `DeviceProfile.cpp:131-157` `ValidateTextureLODGroups()` ordena el array por `Group` y **rellena desde el perfil PADRE** cualquier grupo que el hijo no declare. Entonces alcanza con declarar **solo el grupo que se cambia**. Va en el **perfil hoja** (el que el log del device reporta como `Selected Device Profile: [Meta_Quest_3]`), y hay que confirmar antes que **ni esa sección ni sus padres declaren ya ese `Group`** — una entrada duplicada para el mismo grupo es lo único que rompe el sort+insert. En este proyecto: `Config/Android/AndroidDeviceProfiles.ini`.

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
44. 🔴🔴 **`Array|Add` sobre el array de OTRO objeto opera sobre una COPIA y no acumula nada.** `(Utilities|Array|Add (Class|X|GetMiArray obj) V)` compila, corre y no guarda: el getter de una variable de otro objeto devuelve el array **por valor**. Con una variable **propia** sí funciona (es lo que hace `CollectRings`), y por eso la confusión es fácil. **Patrón correcto: leer → agregar → volver a escribir** (`bind` + `Add` + `Class|X|SetMiArray :self obj :MiArray _v`). El `Set` de otro objeto **exige keywords**: con posicionales el target se va al pin de valor (*"Could not connect pin Data to Variants"*).
45. **Los miembros de un UserDefinedStruct NO se pueden agregar por MCP** (no hay toolset de structs). Si hace falta persistir un registro compuesto, van **arrays paralelos** en el SaveGame, escritos todos en la misma función y con un log de longitudes que delate un desalineado.
46. **El pin de exec de un `K2Node_Event` NO es el índice 0** — ahí está `OutputDelegate`. Hay que buscar el pin cuyo `type_id` sea `Exec` y usar SU `index_id`. Con el 0 fijo, `connect_pins` falla con *"Could not connect pin OutputDelegate to execute"*.
47. 🔴🔴 **Recompilar un Blueprint REINSTANCIA su actor colocado**: el `refPath` cacheado pasa a apuntar a un `REINST_<Clase>_NN` y `set_properties` falla con *"the following properties could not be set"*. En un caso el actor **desapareció del nivel**. **Después de cada compile hay que volver a buscar el actor con `find_actors`**; y para los flags de prueba conviene setearlos en el **CDO**, que sobrevive al recompile, en vez de en la instancia.
48. 🔴 **Un guard que falta en una función que corre por Tick INUNDA el log**: `CheckHoverHand` leyendo una referencia nula generó **miles** de `Accessed None` en segundos y tapó todo lo demás (el propio `StartPIE` devolvió el error repetido como resultado). En funciones por frame el `IsValid` no es opcional — y si el objeto viene de afuera, **pasarlo como parámetro ya guardado** en vez de releer la variable.
49. ⚠ **Agregar un parámetro a una función que YA tiene llamadores rompe el compile** (*"Could not find a pin for the parameter X"*) y, como el `execute_tool_script` falla, **revierte los `add_function_graph` del mismo script**. Salida limpia: **no tocar firmas en uso** — encadenar una función nueva con el parámetro extra.
50. 💡 **La forma con KEYWORD evita la trampa del literal perdido.** `(CallFunction|GotoPage :NewPage 1)` conserva el 1; el posicional `(CallFunction|GotoPage 1)` es el que se pierde (trampa #23). Verificado con `get_node_infos` sobre los 4 pines de `ForceHeartPage`. **Regla: llamar funciones propias SIEMPRE con keyword.**
51. 🔴 **`Assign<Delegate>` deja un evento custom FANTASMA por cada escritura.** `BP_Stage_Attracting` acumuló `OnConfirmed_Event_0..5`: seis eventos vacíos, nunca conectados. **El barrido de huérfanos NO los toca** porque `K2Node_CustomEvent` está en `ENTRY`. Igual que los `FunctionResult` sobrantes (#38): hay que **buscarlos a mano y borrar los que tengan el exec sin conexiones**. Síntoma en el `read`: una fila de `(event Custom|X_0)`, `(event Custom|X_1)`… todas vacías.
52. ⚠ **Al buscar "el evento" por `type_id`, el nodo de DELEGADO matchea primero.** `AssignOnConfirmed` contiene un `AddEvent|Custom|OnConfirmed_Event` que **no tiene pines de exec conectados**, así que un scan por nombre lo agarra y concluye "el evento no está cableado". **Filtrar por `node_class: K2Node_CustomEvent`**, no por nombre.
53. 🔴🔴 **Un pin de exec de SALIDA admite UNA sola conexión** (los de ENTRADA sí aceptan fan-in, gotcha del 2026-08-12). Al reconectar dos consumidores al mismo `Started`, el segundo **reemplaza** al primero en silencio: `connect_pins` devuelve OK las dos veces. Síntoma: media cadena queda huérfana. **Verificar con `get_node_infos` cuántos destinos quedaron**, no asumir por el retorno.
54. 🔴 **Escuchar una `IA_*` cuyo IMC no está mapeado = evento que nunca dispara, sin ningún error.** `BP_SoulChoice` escuchaba `IA_Shoot_Left/Right` pero agregaba `IMC_MenuTrigger`, que sólo mapea `IA_Continue`; y los `IMC_Weapon_*` están vacíos. Compila, corre, el hover marca la candidata y el gatillo **nunca llega**. **Al cablear input, cruzar SIEMPRE: qué evento escucho ↔ qué acciones mapea el IMC que agrego.**
55. 🔴 **Un evento custom aparece en `list_graphs` como un grafo con su nombre, pero ese grafo es sólo un STUB.** `BP_StageDirector:EnterRoom` lee `(fn EnterRoom () (|ExecuteUbergraphBPStageDirector 0))` — el cuerpo real vive en el `EventGraph` como `K2Node_CustomEvent`. **Insertar nodos en el stub no hace absolutamente nada** y compila en verde. Regla: si el `read_graph_dsl` de una "función" devuelve un `ExecuteUbergraph`, es un evento — buscarlo en el EventGraph por `node_class: K2Node_CustomEvent`.
56. 🔴🔴 **Un helper que "engancha al final de la cadena" DESTRUYE una rama si la funcion tiene un `if`.** Caminar los exec-outputs hasta el ultimo nodo y conectar `ultimo.then -> nuevo` parece seguro, pero si el recorrido entra en la rama de un branch y el "ultimo" resulta ser el propio branch, la conexion **reemplaza** la salida `then` (exec de salida = una sola conexion, #53) y el cuerpo de la rama queda huerfano. Le paso a `BP_MenuButton.HoverEdge`, que perdio su `SetbWasHovered` + `HoverFeedback` y quedo llamando solo lo nuevo. **Sintoma: la funcion se encoge en el `read_graph_dsl`.** Reglas: (a) **leer siempre el grafo despues de un append automatico**; (b) para funciones propias y chicas, **reescribir el DSL entero es mas seguro que la cirugia**; (c) la cirugia se reserva para grafos grandes y verificados, y ahi se inserta en un punto CONOCIDO, no en "el final".
57. 🟢🟢 **RESUELTO — `SetNiagaraVariable(...)` va SIN el prefijo `User.`** (medido 2026-08-15 con un parámetro que existe de verdad). Con `"Calm"` la escritura llega y se lee de vuelta; el parámetro se llama `User.Calm` en el store pero el setter agrega el namespace solo. El bloque que afirmaba lo contrario en `assets-existentes.md` era falso, y por eso `BP_AimBeam` escribía `"User.BeamStart"` → **parámetro fantasma**, la causa más probable de que el beam no se viera en visor. Corregido.
58. 🔴🔴 **`bIsValid` de `GetNiagaraVariable` NO prueba que el parámetro exista.** Lee el **store de OVERRIDES del componente**, que arranca vacío: da `false` para parámetros perfectamente existentes y pasa a `true` **recién después de escribir**. La receta "verificalo en 1 minuto con bIsValid" da **falsos negativos**. Para existencia: `NiagaraToolset_System.GetUserVariables` sobre el sistema. Para comprobar que tu escritura llegó: **escribir y leer de vuelta**. Y **no gatear las escrituras con un probe** — un nombre inexistente sólo crea un parámetro fantasma inofensivo, así que escribir siempre sale más barato que detectar.
59. ⚠ Un `NiagaraComponent` con `bAutoActivate=false` **no tiene el store inicializado**: cualquier probe en `BeginPlay` da falso. Probar/escribir **después de `Activate`**.

---

## 🔴🔴🔴 60. El Undo que borra el nivel — el incidente del 2026-08-15

**Qué pasó:** `L_Persistent` apareció **sin `BP_StageDirector`, `BP_BioHub`, `BP_Finale`, `BP_SoulArchive` ni `BP_Constellation`**, y así quedó **guardado en disco**. Se recuperó del último commit (`888f5c3`) después de verificar con `grep` sobre el `.umap` que el blob commiteado sí los tenía y el de disco no.

**La causa, con el log como prueba:** cada `execute_tool_script` que **termina en excepción** hace que el plugin dispare un Undo del editor:
```
[13.42.22:594] LogScript: Warning: AssertionError: The node could not be created / ... does not exist
[13.42.22:636] LogEditorTransaction: Undo Execute tool script
```
Hubo **7 de esos entre las 13:41 y las 13:47** (todos por errores míos de DSL: `&&`, `Math|Float|Max`, `AddEvent|Gameplay|BeginPlay`, `SetbResultsOn`, "Param already exists"…). El Undo saca la transacción de **arriba de la pila de undo del editor, que es GLOBAL**: si el script que falló no alcanzó a hacer ningún cambio propio, ese Undo **se come una transacción anterior que no es mía** — y una de ellas era la lista de actores del nivel. El `save_assets` de las 13:48 grabó el nivel ya mutilado, y ahí dejó de ser reversible.

### Las 4 reglas que lo evitan (obligatorias)
1. 🔴 **Un script nunca debe dejar escapar una excepción.** Envolver **toda** llamada en `try/except BaseException` y devolver el error como **dato**. Un script que retorna `{'errores': [...]}` **no dispara Undo**. Plantilla lista para copiar: **[`scripts/safe_script.py`](../scripts/safe_script.py)**. ⚠ `except Exception` **no alcanza**: varios errores del plugin no derivan de `Exception`.
2. 🔴 **Canario de nivel antes y después de cada tanda**: contar los actores `BP_` del persistente (`level_canary()` en la plantilla). Si el número baja, **no guardar** y revisar.
3. 🔴 **`save_assets` sólo con el canario en verde.** Guardar es lo que convierte un accidente reversible en pérdida de trabajo.
4. 🔴 **Commitear ANTES de una tanda de construcción.** El rescate salió gratis únicamente porque había un commit de una hora antes.

### El aviso que ya existía y no se leyó
`BP_SelfTest` logueó **`TEST FAIL: presente: BP_StageDirector`** y **`TEST SKIP: aserciones del director (no hay director en el nivel)`** en la corrida siguiente. Estaba dicho. **Un `TEST FAIL` de presencia se investiga ANTES de seguir con lo propio** — es exactamente la clase de aserción que detecta este daño.

61. 🟡 **`read_graph_dsl` ATRIBUYE una llamada a la clase equivocada cuando el nombre colisiona** — y eso hace parecer que hay un bug donde no lo hay. Visto el 2026-08-15: una llamada propia a `HoverFeedback` se imprime como **`Class|BPMenuButton|HoverFeedback`**, `ResolveHover` como **`Class|BPAimBeam|ResolveHover`**, `SetRow` como `Layout|GridSlot|SetRow`, y `BP_SoulArchive.GetData` como `Class|ToolMenuEntryScript|GetData`.
    🔴 **La prueba de que es sólo el READ:** al borrar la función propia `SetRow`, el compile falló con *"Could not find a function named \"SetRow\" in 'WBP_Results_C'"* — o sea el nodo **sí apuntaba a la función propia**. Y `BP_MenuButton.UpdateHold`, que se lee como si llamara a `Class|BPDebugDirector|TickHold`, **funciona en visor**.
    👉 O sea: **no salgas a arreglar un bug que sólo existe en el texto del read.** Confirmá con `get_node_infos` antes de tocar nada (es la regla que ya estaba en las golden rules de `SKILL.md`, y que acá se pagó igual).
    ⚠ Aún así conviene **ponerle nombres únicos a las funciones propias** (`ExploreResolve`, `SetResultRow`, `CacheResultsBio`): no porque el compilador se confunda, sino porque **el read se vuelve legible** y no se pierde tiempo dudando.
62. 🔴 **Una variable bool con prefijo `b` no se puede ESCRIBIR por DSL.** Su setter se lee como `(|SetbCommitted true)` pero esa forma **no se puede escribir de vuelta**, y `(Variables|Default|SetbResultsOn false)` falla con *"does not exist"*. Consecuencias: (a) **para código nuevo, no usar prefijo `b`** en bools propios — o usar un `int` 0/1 si el nombre importa; (b) **una función que contenga uno de esos setters es de sólo lectura**: no se puede reescribir entera con `write_graph_dsl`, hay que hacer cirugía de nodos. Por eso `BP_Finale.CommitToHeart` quedó intacta y el panel de resultados se auto-oculta por tiempo en vez de engancharse ahí.
63. ⚠ **`ObjectTools.set_properties` recibe `values` como STRING JSON, no como objeto.** Pasándole un dict devuelve **`false` sin error y no cambia nada** — 40 propiedades del widget "se aplicaron" y ninguna lo hizo. Es la trampa "declarado ≠ aplicado" en su forma más barata de evitar: **`json.dumps(...)` en `values`, y verificar con `get_properties`**. `false` no significa "sin cambios": significa **falló**.
64. ⚠ Nodos que NO existen con el nombre que uno espera (cosecha 2026-08-15): `&&` (usar `if` anidados o `and`) · `Math|Float|Max` · `Math|Trig|Cos` (es **`Math|Trig|Cos(Degrees)`**) · `Math|Vector|vector-vector` (eso es sólo cómo lo IMPRIME el read) · `Utilities|Array|Find` (es **`Utilities|Array|FindItem`**) · `AddEvent|Gameplay|BeginPlay` (es **`AddEvent|EventBeginPlay`**). Para restar/normalizar en un paso: **`Math|Vector|GetUnitDirection(Vector)`**.
65. ⚠ **`FindItem` exige que el tipo del array y el del ítem coincidan exactamente.** Un array de `BP_ProtoSoul` no acepta un ítem `Actor`. Y **`remove_function_param` + `add_..._param` para cambiar el tipo de un parámetro NO funciona** (*"Param already exists"*): hay que **borrar la función y rehacerla** — vaciando antes a sus llamadores, o el compile rompe.
66. ✅ **Cirugía de nodos: la receta que funciona para AGREGAR un paso al final de una función que NO se puede reescribir.** Sirve cuando la función tiene formas que el DSL lee pero no escribe (bools con `b`, `vector*vector`, etc.). Cuatro pasos, y ninguno adivina nombres:
    1. `find_nodes` + `get_node_infos` sobre el grafo; el nodo final es el que tiene un **pin Exec de salida SIN conexión**.
    2. `find_node_types` con el nombre de tu función para sacar el **type_id real** (`CallFunction|RingProgress`, no `|RingProgress`).
    3. `create_node` con **`type_id`** (no `node_type`).
    4. `connect_pins` con **`output_pin`/`input_pin`** (no `from_pin`/`to_pin`), y pasándole **los `pin_id` tal como los devolvió `get_node_infos`** — construirlos a mano falla con *"could not convert incoming function input params Json to a UStruct"* (la dirección es `EGPD_Output`/`EGPD_Input`, no `"Output"`/`"Input"`).
    Después: `compile` + `read_graph_dsl` para ver el paso nuevo al final, y comparar el read de antes con el de después (así se ve si se rompió una rama).
67. 🔑 **El setter de un bool `b` SÍ se puede escribir… desde OTRA clase, y va sin la `b`.** Complemento indispensable del §62: `bTrigHeld` no se puede setear desde su propio Blueprint por DSL, pero desde afuera el nodo existe como **`Class|BPBrushTool|SetTrigHeld`** y se escribe con keywords: `(Class|BPBrushTool|SetTrigHeld :self _b :bTrigHeld false)` — **`:self` es el objetivo y el keyword del valor SÍ lleva la `b`**. Con posicionales el target se va al pin de valor. Esto abre la puerta a cambiar estado de un BP frágil **sin tocar sus grafos**, que es como `BP_DrawLimit` corta el trazo de `BP_BrushTool` sin editar el pipeline de dibujo.
68. ⚠ **`Game|SpawnActorBP<Loquesea>` sólo existe si el editor ya conoce esa clase en ese grafo.** Para una clase recién creada el nodo no aparece y hay que usar el genérico **`Game|SpawnActorfromClass`** (3 args: clase, transform, collision handling). El específico es azúcar del registro de nodos, no una API estable.
69. ⚠ **Una función recién creada no es llamable en el MISMO `write_graph_dsl` que la crea**: `CallFunction|X does not exist`. Hay que `add_function_graph` + **`compile_blueprint`** y recién después escribir al que la llama. Por eso conviene el orden: crear todas las funciones → compilar → escribir cuerpos de las hojas → compilar → escribir los llamadores.
70. ⚠ **`add_function_param` sobre un parámetro que ya existe LEVANTA excepción** ("Param already exists!") — y con eso dispara el Undo del §60. En scripts idempotentes, envolverlo (la plantilla `safe_script.py` ya lo hace) o consultar antes con `list_graphs`/`get_node_infos`.
71. 🔴 **Un SoundWave marcado `bLooping=true` reproducido con `PlaySound2D` NO SE DETIENE NUNCA.** No hay handle, no hay componente, no hay forma de pararlo: queda sonando hasta el fin del nivel. El 2026-08-15 cuatro one-shots de UI llegaron con el flag puesto (`SBubbleHoverOn` de **0,14 s**, `SBubbleHoverOut`, `Trigger_Select`, `ProtoSelect`) y cada hover sobre una burbuja dejaba un loop permanente — con 20 burbujas, un muro de ruido.
    👉 **Chequeo obligatorio al recibir audio nuevo**: leer `bLooping` y `duration` de cada asset y cruzarlos con cómo los va a tocar el código. La regla: **lo que se toca con `PlaySfx`/`PlaySound2D` va con `bLooping=false`; lo que se toca con `LoopPlay` va con `bLooping=true`.** Un clip corto marcado como loop es siempre un error; uno largo sin loop se corta a la mitad (le pasó al `PadM1`, 5,33 s = un compás a 90 BPM, que sin el flag sonaba una vez y desaparecía).
72. ⚠ **Antes de pedirle a alguien que pruebe, revisar los flags de debug del nivel.** El mismo día, Beltrán dio Play y report\u00f3 "no suena el Ambient 1": no era un bug — `DebugStartStage` había quedado en **4** de mi última prueba, así que la obra saltaba directo a Attracting, que **por diseño no lleva ambiente**. **Restaurar los flags es parte de terminar la prueba, no un paso opcional** — y conviene decir en qué estado quedan.
73. 🔴🔴 **`FadeIn` sobre un `AudioComponent` con `VolumeMultiplier = 0` no suena, y el log dice que sí.** `FadeIn(dur, level)` sube hasta **`level × VolumeMultiplier`** — con el multiplicador en 0, el destino es 0. Los `AmbA`/`AmbB` de `BP_AudioHub` estaban así desde que se crearon: la obra logueaba `AUDIO: ambiente -> Ambient1` y **no sonaba nada**. Es "declarado ≠ aplicado" en su forma más cara: el log del Blueprint es cierto, el resultado es silencio.
    👉 **Al crear un AudioComponent por MCP, verificar `volumeMultiplier` (debe ser 1.0) y `bAllowSpatialization` (false si es una cama sonora 2D).** Un componente de audio recién creado por API **no hereda los defaults que uno supone**.
74. ⚠ **Las variables con prefijo `b` no se pueden ni leer ni escribir por DSL desde su propia clase, y tampoco se les puede crear el nodo getter por `create_node`.** Se probaron `Variables|Default|GetbX`, `|GetbX` y `Variables|<BP>|GetbX`: los tres fallan. Consecuencia práctica: si una lógica necesita **leer** un bool `b` propio, hay que rediseñarla sin él (contador `int`, variable espejo sin prefijo) o dejar esa función intacta. Fue lo que obligó a resolver el háptico de salida del hover quitándolo en vez de corrigiéndolo.
75. 🔴🔴 **Arreglar el CDO NO arregla la instancia ya colocada.** El `volumeMultiplier=0` de los `AmbA`/`AmbB` del AudioHub se corrigió en el CDO, se guardó, y **el ambiente siguió mudo**: la instancia de `L_Persistent` tenía su propio override en 0. Es la misma familia que "instance-editable nace en cero", pero **aplicada a PROPIEDADES DE COMPONENTES**, que es más traicionera porque uno cree que el componente es del Blueprint.
    👉 **Verificar SIEMPRE en la instancia del nivel, no en el CDO** — `get_properties` sobre `<Level>:PersistentLevel.<Actor>.<Componente>` (ojo: es un punto, no `:`, para llegar al componente de una instancia).
76. 🔴 **Un `Plane` del motor es de una sola cara: rotado 180° en yaw, desaparece.** Los 5 anillos de la ameba de la explicación se sembraban bien (`SOUL: anillos sembrados = 5` en el log) y **no se veían**: la ameba se spawneaba con el `GetWorldTransform` de su anchor, que hereda el **yaw 180** del panel del widget, así que se estaba viendo el reverso descartado por backface culling. **Al spawnear algo con anillos/planos, tomar del anchor la posición y la escala pero NO la rotación.**
77. 🔴 **En `CallFunction`, los argumentos posicionales empiezan por `self`.** `(CallFunction|Ingest X Y)` intenta conectar `X` al pin **`self`** y falla con *"Could not connect pin X to self. The pins may be incompatible types"*. El mensaje no lo dice, pero **el problema no es el tipo: es que el primer posicional es el target**. En una sola tarea del 2026-08-15 mordió **tres veces seguidas** (`Ingest`, `IngestInt`, `FireJump`).
    👉 **Regla: toda llamada a función con parámetros va con keywords** (`:Addr`, `:Value`, `:N`, `:Bpm`). Y **el nombre del pin se verifica, no se supone** — el error de pin desconocido lista los válidos, y ahí apareció que `IngestInt` recibe **`V`** y no `Value`. Ojo también con el §67: al llamar a otra clase, `:self` es el target.
78. 🔑 **Antes de teorizar sobre un detector, buscar sus FLANCOS en el log.** La etapa Recognizing quedaba atascada y el tercer sospechoso era el umbral de quietud (`bBreathing`), que vive en `Step` — el pipeline frágil que no se puede reescribir. En vez de tocarlo, se buscó `UMBRAL` en el log **de la corrida del usuario**: `[BP_HeartSensor_C_0] UMBRAL IN` … 48 s … `UMBRAL OUT`. El umbral estaba cerrado casi un minuto: **el sospechoso quedó descartado con un dato, sin abrir el grafo.**
    👉 Los `PrintString` de flanco que ya existen en los detectores (`UMBRAL IN/OUT`, `DOOR: ...`) son **instrumentación gratis y retroactiva**: sobreviven en el log de la sesión del usuario y contestan preguntas que uno se haría teorizando. Mirarlos **antes** de tocar código frágil.
79. ⚠ **Dos "variables de referencia" distintas para la misma señal = una se queda sin simular.** Mientras el OSC real no está, la obra usa fuentes simuladas — pero había **dos**: el `BP_BioHub` con su LFO (que alimenta HUD y gráficos) y `BP_OSCReceiver.HeartRate`, un **float fijo 75.5** que alimenta el sensor de latido. La segunda ni siquiera tenía un actor en el nivel, así que la etapa del corazón no podía arrancar.
    👉 **Al montar una simulación, enumerar TODOS los consumidores de esa señal y verificar que todos cuelguen de la misma fuente.** Acá se resolvió con un puente (`BioHub.PushFakeHeart` escribe el BPM simulado en el receptor) que **se apaga solo** cuando llega la señal real, porque vive dentro de `FakeTick`.
80. 🔑🔑 **Las variables con prefijo `b` SÍ se leen desde otra clase, y el getter va SIN la `b`.** Complemento del §67 (los setters) y límite real del §74: la ceguera a los bools `b` es **sólo dentro de la propia clase**. Desde afuera existen `GetBreathing`, `GetAttached`, `GetCountingEnabled`, `GetChosen`, `GetAnyHover`, `GetDrawing`, `GetDone`, `GetRunning`… y se llaman con el target como argumento: `(Class|BPHeartSensor|GetCountingEnabled _s)`.
    👉 Esto es lo que hace posible **instrumentar desde afuera un Blueprint frágil sin tocarlo**: `BP_TestKit` reporta el estado interno de seis mecánicas distintas sin editar ninguna. Antes de rediseñar una lógica para esquivar un bool `b`, preguntarse si el lector puede vivir en otra clase.
81. ⚠ **`GetLogEntries` interpreta el `pattern` como REGEX.** Buscar `"PULSE|"` trajo **115.000 caracteres** (el `|` es alternancia: matchea "PULSE" o cadena vacía → todo el log). Usar el prefijo sin el pipe (`"PULSE"`), o escaparlo (`"PULSE\|"`). El mismo cuidado con `(`, `)`, `.` y `+` en los prefijos de log que uno mismo inventa — conviene que el separador de los mensajes NO sea un metacarácter si se va a filtrar por él.
82. 📸 **Cómo sacar una imagen del juego sin fundir el contexto.** Tres caminos, y sólo uno sirve de rutina:
    - ✅ `Development|ExecuteConsoleCommand("HighResShot 1920x1080")` desde un Blueprint → escribe el PNG en `Saved/Screenshots/WindowsEditor/` y se abre con `Read`. **Barato y es el bueno.**
    - ❌ `EditorAppToolset.CaptureEditorImage` con PIE corriendo → *"Failed to capture any editor windows"*.
    - ⚠ `EditorAppToolset.CaptureViewport` → funciona, pero devuelve el PNG **en base64 dentro de la respuesta**: 651.000 caracteres medidos. Inviable salvo caso puntual.
    ⚠ Los archivos se numeran de corrido **entre corridas** (`HighresScreenshot00000.png`, `00001`…): correlacionar con las marcas **por fecha de modificación**, nunca por el número del nombre.
83. 🤖 **En PIE se pueden falsear las manos: `SetWorldLocation` sobre el `MotionControllerComponent` SE QUEDA PEGADO.** Sin HMD no hay tracking que lo pise, así que el componente obedece. Y como toda la obra lee las manos por dos accesores del pawn (`GetMotionControllerLeftGrip/RightGrip`), **mover esos dos componentes es mover las manos para todas las mecánicas a la vez** — no hay que falsear cada una. Medido: `mano=X=2412 Y=0 Z=-32 | pecho=X=2412 Y=0 Z=-32 | dist=0.0`, y el sensor de latido se enganchó solo.
    ⚠ **Pero la cámara en PIE está en Z=0, el suelo**: sin HMD el pawn no recibe altura de tracking. Las lógicas relativas a la cabeza siguen valiendo; las posiciones absolutas del mundo, no. Para que PIE sea representativo hay que **falsear también la altura de la cabeza**.
    💡 Y el gatillo se puede sintetizar de verdad: existe **`Input|InjectInputforAction`**, que entrega la acción por el mismo camino que un usuario.
84. 🔴🔴 **El detector de respiración/latido no puede correr en PIE: depende del TRACKING, no de la posición.** `MotionControllerUpdate|GetLinearVelocity` devuelve **el vector Y un bool de validez**, y `BP_HeartSensor.Step` exige **los dos bValid en true** (`(and GetLinearVelocity.ReturnValue GetAngularVelocity.ReturnValue)`). Sin runtime XR ese bool es `false` y **falsear la mano no lo cambia**: medido con geometría perfecta (`horiz=12 ≤ 20`, `vdrop=32 ≥ 5`, `vel=0`), el temporizador de calibración se quedaba en `calT=0.0` para siempre.
    👉 Antes de intentar automatizar una mecánica en PIE, preguntarse **de qué dato depende**: si sale de la POSE, se puede falsear; si sale del TRACKING (velocidades, validez, bTracked), no.
    💡 Salida sin tocar el Blueprint frágil: saltear **sólo el detector** desde otra clase con los setters públicos (§67) y probar toda la cadena que viene después.
85. 🔑 **Para ganarle a una lógica que escribe por tick, no escribas más rápido: desarmá su condición de apagado.** El robot ponía `bBreathing=true` 20 veces por segundo y `Step` lo apagaba ~60 — y como `UpdateHeartbeat` corre **justo después de `Step` en el mismo tick**, leía `false` siempre. La solución no fue subir la frecuencia (es un problema de ORDEN, no de tasa) sino `SetDeactivateDelay(99999)`: con el retardo de desactivación en el infinito, `Step` nunca llega a apagarlo y **una sola escritura alcanza**.
86. ⚠ **Un actor de debug que mueve al jugador tiene que nacer APAGADO.** `BP_Robot` mueve los mandos del pawn; si su `RobotOn` quedara en 1, en una sesión con visor le llevaría las manos al pecho al usuario y arruinaría la corrida. Los flags de debug que **actúan sobre el jugador** (no sólo los que loguean) se dejan en 0 por defecto y se encienden por sesión — misma disciplina que `DebugStartStage` (§72).
87. 🔑 **Se puede sintetizar el gatillo de verdad: `Input|InjectInputForAction` entrega la acción por el mismo camino que un usuario.** Verificado: el robot armó el hover y apretó `BOTON apretado: START` sin ningún atajo, y eligió una proto ameba 330 ms después de inyectar.
    🔴 **La trampa:** hay DOS nodos con el mismo nombre y sólo uno sirve. `LocalPlayerSubsystems|GetEnhancedInputLocalPlayerSubsystem` (sin argumentos) **devuelve None** — el síntoma es que la inyección no hace nada y el log recién lo canta al cerrar PIE (`Accessed None ... CallFunc_GetLocalPlayerSubsystem_ReturnValue`). El bueno es **`PlayerController|LocalPlayerSubsystems|GetEnhancedInputLocalPlayerSubsystem`** con `Game|GetPlayerController 0`.
    ⚠ El valor se arma con `Input|MakeInputActionValueOfType` (X=1.0 para apretar, 0.0 para soltar).
88. 🔴🔴 **Control positivo ANTES de acusar al código: casi reporto un bug del juego que era mío.** El robot tenía hover, input listo y botón armado sobre una proto ameba, inyectaba el gatillo y no pasaba nada — exactamente el síntoma que Beltrán reportó en visor. La conclusión tentadora era "bug reproducido". En vez de eso probé la MISMA inyección contra un botón que ya sabía que funciona: tampoco anduvo → **el problema era mi instrumento** (§87). Con la inyección arreglada, la elección funcionó a la primera.
    👉 Regla: cuando una herramienta nueva "confirma" el bug que uno esperaba encontrar, **probarla contra un caso que se sabe sano** antes de escribir el diagnóstico.
89. 🔴🔴 **`DebugStartStage` coloca la sala pero NO lleva al pawn hasta ella: los tests salteados son geométricamente inválidos.** Medido: saltando a Attracting, el aim del robot apuntaba perfecto (`fwd=X=1.000` vs `dirBurbuja=X=0.999`) y aun así el beam golpeaba el vacío — porque **la burbuja estaba a 48 metros** (`dist=4820`), muy fuera del `TraceDistance`. El pawn se queda en el origen mientras la sala se coloca en su parada del spline.
    👉 **El atajo sirve para lógica y estado, NO para nada espacial** (punteros, trazos, alcance de la mano, hover por distancia). Cualquier mecánica que dependa de distancias hay que probarla en la **pasada completa**, con el pawn caminando hasta la sala.
90. 🔴🔴 **Una llamada a función sin pasar un parámetro NO es un error: el pin se queda en su default, y si el default es `false` la función hace lo contrario de lo que dice.** `BP_Stage_Attracting.EquipOneBeam` llamaba `Equip(beam)` sin el argumento `NewEquipped` → el puntero de Attracting **nacía apagado** (`bEquipped=false`, sin cursor, sin traza), y la etapa igual logueaba *"beams activados"*. Consecuencia en cadena: no hay hover, no se agarra ninguna burbuja, ningún slot se ocupa, FINISH MELODY nunca se habilita y la etapa cierra por cortafuego.
    👉 **Al leer un grafo, desconfiar de las llamadas con menos argumentos que parámetros** — el `read_graph_dsl` las muestra cortas y parecen correctas. Y al diagnosticar una mecánica muerta, **medir el estado del actor** (`bEquipped`, `bInputReady`) antes que su grafo: el log que dice "activado" puede ser cierto y el valor efectivo ser `false`.
91. 🔴🔴🔴 **Un instrumento que MODIFICA el mundo puede fabricar el bug que después reporta.** El robot escribía la *posición completa* del `VROrigin` cada frame para simular la cabeza a 115 cm — y el `VROrigin` es exactamente lo que el recorrido por spline desplaza. Resultado: el pawn se quedaba clavado en el origen, las salas aparecían a 12-48 m, y yo reporté como hallazgo mayor de la obra *"el jugador nunca se mueve"*. **Era mi robot.** Con `HeadOn=0` el pawn recorre 1200 → 2400 → 3600 y la cámara lo sigue exacto.
    👉 **Reglas que quedan:** (1) un instrumento que sólo LEE es seguro; uno que ESCRIBE hay que poder **apagarlo por separado** y medir con y sin él antes de concluir nada; (2) escribir un transform completo pisa lo que otro sistema esté animando — tocar **sólo la componente que hace falta** (acá: conservar X/Y y corregir sólo Z); (3) 🔴 **cuando el dato del visor contradice mi medición en PIE, gana el visor** — Beltrán venía diciendo *"en gafas íbamos pasando de sala en sala sin problema"* y tenía razón desde el principio.

## 🌾 Cosecha 2026-08-17 (construyendo `BP_Director_Movement` en limpio)
92. 🔴🔴 **`set_variable_category` CAMBIA el `type_id` del getter/setter en el DSL.** El "Default" de `Variables|Default|GetX` **es la categoría**, no una palabra fija. Al mover `bAutoAdvance` a la categoría "D - Test", el id pasó a **`Variables|D-Test|GetAutoAdvance`** (los espacios se comen) y un `write_graph_dsl` posterior falló con *"Variables|Default|GetAutoAdvance does not exist"* — con la variable existiendo y el grafo compilando perfecto.
    👉 **Ordená las categorías DESPUÉS de escribir todos los grafos**, o confirmá el id con `find_node_types(graph, "Get<Var>", [])` antes de cada write. Los nodos **ya creados** no se rompen: el cambio afecta sólo a lo que se escriba después.
93. 🔴🔴🔴 **`(bind x <expresión pura>)` NO cachea: si un `Set` corre antes que otro consumidor, ese consumidor lee el valor NUEVO.** Caso real y **visible**, no cosmético: `FinishLeg` hacía `SetLegIndex(i)` antes del snap, con `i = LegIndex + 1` inline → el `SetActorLocation` posterior re-evaluaba `i` y mandaba al pawn **una parada de más**, y el tramo siguiente lo traía de vuelta (salto adelante y atrás en cada llegada). Lo cazó el log: *"llego a la parada 2"* al terminar el primer tramo.
    👉 **Los `Set` de una variable que alimenta un `bind` puro van AL FINAL de la función**, o el valor se guarda en una variable propia. Y ojo: es la misma raíz que el aviso de la doc del DSL sobre repetir llamadas, pero muerde **aunque uses `bind`**, que es justo lo que parece protegerte.
94. **`add_variable` acepta `bool` / `int` / `float`, NO `Boolean` / `Integer`.** El error es claro y lista el vocabulario completo (`bool, int, float, byte, name, string, text, Vector, Rotator, Transform, Vector2D, LinearColor`), pero cuesta un round-trip. Para tipos objeto va `add_object_variable` (`/Script/Engine.SoundBase`, `/Script/Engine.Pawn`, …), que **sí existe** — no repitas que "el MCP no crea variables de objeto".
95. 🔴 **Llamar a una función PROPIA con argumento posicional intenta conectarlo al pin `self`.** `(CallFunction|GetStopLocation Index)` falla con *"Could not connect pin Index to self"*. **Siempre con keyword: `(CallFunction|GetStopLocation :Index Index)`.** (Ya había pasado con `PreloadNext`; ahora está acá.)
96. 💡 **Una tecla de teclado para debug NO necesita Enhanced Input, ni IMC, ni `EnableInput`.** El nodo de evento `InputKey` **no existe** por MCP (no aparece en `find_node_types`, ni como `AddEvent|`, ni el de `EnhancedInputAction`). La vía que sí funciona es **consultar la tecla en el Tick**: `Game|Player|WasInputKeyJustPressed(GetPlayerController(0), "One")`. El literal de la `FKey` entra como string (`"One"`) y anda. Cero assets creados, cero riesgo de pisar los IMCs del pawn.
97. ⚠ **El `read_graph_dsl` atribuye las llamadas a funciones propias a OTRA clase cuando el nombre existe en otro BP.** Acá renderizó `(Class|BPJourney|GetStopLocation …)` y `(Class|BPWalker|UpdateLeg …)` para funciones **de este mismo Blueprint**. Es la mislabel por colisión de nombres ya conocida, pero da un susto grande porque parece la trampa del overload equivocado (§DSL #3). **Cómo desmentirlo en una llamada:** `get_node_infos` → el `type_id` real de una llamada a función propia viene **con el prefijo de clase VACÍO** (`|GetStopLocation`) y el pin `self` sin conectar. Si de verdad fuera de otra clase, el `self` tendría que estar cableado.
98. ⚠ **`StartPIE` con `warmupSeconds` alto puede devolver "Timed out waiting for PIE to start" y aun así HABER ARRANCADO.** Con 32 s dio timeout; `IsPIERunning` devolvía `true` y el log tenía la corrida entera. **No re-lanzar PIE ante ese error: confirmar con `IsPIERunning` y leer el log.**
99. 🔑 **Para REESCRIBIR el cuerpo de una función sin romper a sus llamadores: borrar todos sus nodos MENOS el entry y hacer `write_graph_dsl` encima.** Verificado en 5 funciones: no duplica el entry, no deja islas huérfanas, y los nodos que la llaman desde otros grafos **siguen conectados** (a diferencia de `remove_function_graph` + `add_function_graph`, que los deja colgando — §Cosecha 2026-08-13 #9).
    🔴 **La excepción que muerde: si la función DEVUELVE valor y borraste el `|ReturnNode`, los `(return …)` se pierden EN SILENCIO.** El write crea las ramas y ningún retorno, compila sin una queja, y la función devuelve 0. Pasó con `GetLegTime`. **Conservar los `|ReturnNode` al vaciar** (o crear la función de nuevo con otro nombre si todavía no tiene llamadores).
100. 🔴 **Una categoría de variable con PARÉNTESIS es inusable desde el DSL.** "Z - Estado (no tocar)" da `Variables|Z-Estado(notocar)|GetX`, y ahí el parser corta en el `)`: *"Variables|Z-Estado(notocar) does not exist"*. (Los paréntesis al FINAL del id sí funcionan — `Math|Float|Clamp(Float)` — el problema es tener texto después.) **Categorías sin paréntesis.**
101. ⚠ **Tras `set_variable_category`, `find_node_types` sigue devolviendo el id VIEJO** (el registro de acciones está cacheado, aun compilando), **pero el id NUEVO ya funciona en el `write`**. No confiar en el listado para decidir: probar el id nuevo.
102. 🔴 **`Audio|Components|Audio|FadeIn` / `FadeOut` están DUPLICADOS y el DSL agarra el overload equivocado** (el de otra clase de componente). Síntoma: *"Could not connect pin StepsAudio to self"* — y no lo arregla pasarlo como `:self`. **Solución: `create_node` con `declaring_class: /Script/Engine.AudioComponent` y cablear los pines a mano.** Es el caso de libro de la trampa #3 del DSL.
103. 🔴🔴 **Confirmación en vivo de §60: dos `execute_tool_script` fallidos se comieron el ACTOR que había en el nivel**, no sólo lo que hacía el script. Lo detectó el canario de actores (21 → 20) al ir a leer sus propiedades. **Contar actores antes y después de cada tanda sigue siendo obligatorio**, y reponer es barato **si el BP ya tiene los defaults en el CDO** (la instancia nueva los hereda).
104. ⚠ **`set_properties` sobre un actor del nivel puede fallar con la clase `REINST_<BP>_C_NN`**: tras varios compiles seguidos, la referencia que tenías apunta a una instancia reinstanciada y **las propiedades nuevas no existen ahí**. Re-obtener el actor con `find_actors` antes de escribir. Si `find_actors` no lo encuentra, no es un problema de refresco: **es §103**, se lo llevó un Undo.
105. 💡 **La AUSENCIA de `Accessed None` sirve como prueba positiva de vida de un objeto.** Para verificar que un AudioComponent spawneado sobrevivía todo el tramo (y no moría antes, dejando el audio mudo) alcanzó con que el `FadeOut` del final se ejecutara **sin un solo `Accessed None`** en la corrida: si la referencia hubiera sido nula, el log lo habría cantado. Barato y concluyente cuando no hay forma de leer el estado en runtime.
106. 🔴🔴 **SÍ se pueden editar los sublevels registrados por MCP — lo que no se puede es REGISTRARLOS.** Los `ULevelStreaming` viven como objetos dentro del World y se alcanzan por refPath: **`/Game/.../<Mapa>.<Mapa>:LevelStreamingDynamic_N`** (N = 0,1,2… en el orden en que se agregaron; el `worldAsset` dice cuál es cuál). Con eso `ObjectTools.get_properties`/`set_properties` leen y escriben sus flags. ⚠ `ObjectTools.get_properties(World, ["streamingLevels"])` **sigue fallando** — hay que ir por el nombre del objeto, no por el array. Y agregar un sublevel nuevo sigue siendo trabajo del panel Levels.
107. 🔴🔴🔴 **`bShouldBeLoaded` NO es "Initially Loaded": en el juego se PISA.** Poner `bShouldBeLoaded`/`bShouldBeVisible` en true hace que el sublevel se vea en el editor y **no cambia nada en PIE** — `ULevelStreamingDynamic` (el método "Blueprint") reinicializa los dos desde **`bInitiallyLoaded` / `bInitiallyVisible`** cuando el mundo es de juego. Los que hay que escribir para que el nivel arranque cargado son **`bInitiallyLoaded` y `bInitiallyVisible`** (los checkboxes "Initially Loaded/Visible" del Details).
    **Síntoma exacto:** en el editor se ve todo, al dar play el mundo aparece vacío. Costó un diagnóstico entero el 2026-08-17.
108. 💡 **Durante PIE, `SceneTools.find_actors` devuelve el mundo de PIE, no el del editor** — los refPath vienen con el prefijo `UEDPIE_0_`. Es la forma más barata y concluyente de contestar *"¿este sublevel está cargado de verdad al jugar?"*: se cuentan los actores por mundo (`UEDPIE_0_L_Hall_SC`, …). Mejor que buscar en el log, que no registra la carga de sublevels con la verbosidad por defecto.
109. 🔴🔴🔴 **Una función llamada `SetX` COLISIONA con el setter automático de la variable/componente `X`, y el DSL elige el SETTER — en silencio y compilando.** Caso real: un componente `Vignette` y una función `SetVignette(Amount)`. Escribí `(CallFunction|SetVignette :Amount 0.0)` y el `read` devolvió **`(Variables|Default|SetVignette 0.0)`**: en vez de llamar a la función, el grafo **le asignaba 0 a la referencia del componente** (o sea, la anulaba al arrancar). Compila, corre, y todo lo que dependiera del componente habría fallado después sin decir por qué.
    👉 **Nunca nombrar una función `Set<Variable>` ni `Get<Variable>`.** El proyecto ya tenía el nombre bueno para este caso: **`ApplyVignette`** (de [[BP_Walker]]). Y otra vez: **lo cazó leer el grafo después de escribirlo**, no el compilador.
110. 💡 **Cómo distinguir en 10 segundos una llamada a función propia de una homónima de otra clase** (el `read` las etiqueta mal, §97): `get_node_infos` y mirar **el `type_id` y el pin `self`**. Función propia → `|MiFuncion` con **`self` SIN conectar**. Función de otro objeto → prefijo de clase y `self` cableado. Un setter de variable → **`Variables|<Categoria>|Set<Var>`**, que es otra cosa distinta (§109).
111. 🔴🔴🔴 **Confirmación brutal de §497, y peor de lo documentado: el componente agregado DESPUÉS de colocar el actor no llega con "los defaults de Unreal" — puede llegar SIN MALLA.** Medido el 2026-08-17: el `StaticMeshComponent` de la viñeta, perfecto en el CDO (`staticMesh` = Sphere, `overrideMaterials` = el material, escala 0,5), en la instancia ya colocada era `staticMesh: None`, `overrideMaterials: []`, escala 1. **Síntoma en el visor: no se ve absolutamente nada** (y si hubiera tenido malla sin material tampoco: el material básico es de una cara y desde adentro de la esfera se culea la backface).
    ⚠ **Y `set_properties` sobre el componente de la instancia NO alcanza para arreglarlo**: aplicó `staticMesh` y **ignoró en silencio** `overrideMaterials`, `relativeScale3D`, `castShadow` y `translucencySortPriority` (devolviendo éxito). Es el primo del caso del spline (§"instancia con puntos arrastrados").
    ✅ **La vía que SÍ funciona: reponer el actor** (`remove_from_scene` + `add_to_scene_from_asset`), que nace heredando todo del CDO. **Antes de reponer, leer los overrides de la instancia y subirlos al CDO** — así no se pierde el trabajo de ajuste del usuario y además la próxima instancia nace bien.
112. 💡 **Cómo leer el valor EFECTIVO de un parámetro de material en runtime.** `MaterialInstanceTools.get_scalar_parameter` **rechaza los MID** (*"is not valid MaterialInstanceConstant"*), así que para verificar un `SetScalarParameterValueOnMaterials` hay que ir por `ObjectTools.get_properties(<MID>, ["scalarParameterValues"])`, que devuelve la lista con `parameterInfo.name` y `parameterValue`. El MID vive colgado del componente: `<...>:PersistentLevel.<Actor>.<Componente>.MID_<Material>_0`.
    👉 **Dos verificaciones por el precio de una:** que el MID **exista** ya prueba que la llamada corrió, y su `parameterValue` prueba con qué valor. Fue así como se confirmó que la viñeta se movía con la velocidad del tramo (`Amount = 0.0011` con `t = 0.9875`, exactamente lo que da `16t²(1−t)²`).
113. 🔴 **Tercera vez en una jornada que un `execute_tool_script` fallido se come el actor del nivel** (2026-08-17). Esta vez el fallo fue trivial —`delete_unused_expressions` quiere `material`, no `material_or_function`— y el Undo igual borró el `BP_Director_Movement` del persistente, **después de que el script ya había guardado**. Dos conclusiones prácticas:
    - **El canario de actores no es opcional ni ceremonial**: es lo único que separó "un actor perdido y detectado en 10 segundos" de "el mapa roto sin que nadie se entere". Contar antes y después de CADA tanda.
    - 💡 **La reposición es barata SI los defaults del CDO ya son los buenos.** Por eso conviene, apenas el usuario termina de afinar una instancia, **subir esos valores al CDO**: a partir de ahí perder la instancia cuesta una llamada y no se pierde ni un ajuste. Aquí funcionó exactamente así.
114. 🔴🔴🔴 **REGLA DE TRABAJO, no técnica — precisada por Beltrán el 2026-08-17: COLOCAR sí, SACAR se pregunta.** **Agregar** un actor al nivel: adelante. **Eliminar, reponer (borrar+recolocar) o recolocar** algo que ya está: **pedir permiso siempre**, aunque sea "para arreglarlo". Y cuando pide **"limpia y ordena el Blueprint"** se refiere **a ESE Blueprint**: nodos huérfanos y variables sin uso. No al nivel.
    **Por qué, con el caso:** el 2026-08-17 perdió **dos veces** los valores de la viñeta que venía afinando a mano. Una porque se repuso el `BP_Director_Movement` por decisión propia (para arreglar un componente que en la instancia estaba vacío, §111) y otra por el Undo de un script fallido (§113). Las dos veces la instancia nueva nació con los defaults del CDO y **le pisó el trabajo de ajuste**.
    👉 **Beltrán ajusta la instancia EN PARALELO mientras uno trabaja.** Sus valores de instancia son **datos de autor**, no valores de prueba. Si hace falta reponer un actor: **pedir permiso**, y antes leer los overrides de la instancia y subirlos al CDO para que la instancia nueva nazca con ellos.
115. 🟢🔴 **ANTES de dar por perdido un actor que se comió un Undo: MIRÁ EL DISCO.** El 2026-08-17 un `compile_blueprint` fallido borró las 5 puertas de sus sublevels y parecía pérdida total (el usuario ya lo había visto en el editor). **Estaban intactas en los `.umap`**: el borrado era sólo en memoria, porque el `save_assets` posterior no llegó a re-escribir esos paquetes.
    **Diagnóstico en 2 segundos, sin tocar el editor:**
    - Comparar **tamaño de archivo** contra un mapa hermano que no tuvo el actor (17 KB vs 11 KB del que nunca tuvo puerta).
    - `grep -a "<NombreDelBP>" mapa.umap` — el nombre de clase queda como texto plano adentro.
    - Mirar la **hora de modificación**: si el `.umap` es anterior al borrado, el disco está sano.
    ✅ **Recuperación: `SceneTools.load_level` del persistente recarga desde disco y descarta la memoria sucia** — volvieron las 5 con las posiciones y los parámetros que el usuario había afinado.
    🔴🔴 **Y la regla que lo hace posible: NO GUARDAR mientras se investiga.** Un `save_assets` de más en ese momento convierte un susto en una pérdida real. Guardar SIEMPRE con `asset_paths` explícitos —nunca `[]`— cuando se está tocando Blueprints con instancias colocadas: `[]` guarda también los mapas, y ahí es donde se pierde el trabajo ajeno.
116. 🔴🔴 **`ObjectTools.set_properties` sobre un STRUCT aplica UN SOLO campo por llamada, y cuál depende del orden de las claves.** Medido el 2026-08-17 sobre `drawSize` (FIntPoint) y `relativeScale3D` (FVector) de un componente: `{"x":1200,"y":700}` dejó **x=1200, y=140** (la vieja); `{"y":700,"x":1200}` aplicó **las dos**; y `{"z":..,"y":..,"x":..}` aplicó **sólo z**. Devuelve éxito siempre.
    👉 **Escribir un campo por llamada** (`{"x":v}`, después `{"y":v}`, después `{"z":v}`) y **releer**. Es otra cara de "declarado ≠ aplicado", y explica por qué un componente parece ignorar la mitad de lo que se le pide.
117. 🔴 **El Construction Script NO puede pisar una propiedad de componente que la instancia tiene overrideada.** Unreal reaplica el *component instance data* **después** de correr el CS, así que un `SetDrawSize`/`SetRelativeScale3D` en el CS se ve revertido en el editor. (Es el mismo mecanismo que restaura los puntos arrastrados de un spline, ver la nota de [[BP_Journey]].)
    👉 Para actores **ya colocados**, la propiedad del componente se escribe **en la instancia** (§116). El CS sólo gobierna a los que se coloquen **después**. `reset_properties` limpia el override pero lo deja en el default del ENGINE, no en el del Blueprint.
118. 💡 **Un `WidgetComponent` en el editor puede no tener widget cuando corre el Construction Script** → `GetUserWidgetObject` devuelve null y todo lo que dependa de él no pasa (síntoma: se ve en PIE y no en el editor). **`InitWidget` no está expuesto**, pero sí **`UserInterface|SetWidget`**: crear el widget con `Game|ConstructObjectfromClass` (Outer = self) y asignarlo si no existe. Con eso el widget se arma en el editor y **se refresca en vivo al tocar cualquier variable** (el CS re-corre en cada cambio de propiedad).

## 🌾 Cosecha 2026-08-18 (el timbre)
119. 🔴🔴 **Una variable instance-editable NUEVA puede aparecer en los actores ya colocados con un valor que NO es el del CDO — incluso  cuando el default es .** Es el primo malo de "instance-editable nace en cero": esta vez nació en **true**. Caso real: al agregar `bOpenByBell` a `BP_Door_SC` (default false), la puerta suelta del persistente apareció con **true** y `BellSpawnTag = "None"` → su apertura por distancia quedó **apagada en silencio** y encima intentaba spawnear un timbre con tag vacío.
    👉 **Después de agregar una variable instance-editable a un BP que ya tiene instancias colocadas, LEER el valor efectivo en cada instancia.** No alcanza con setear el CDO.
120. 💡 **Dos actores en niveles distintos pueden compartir el nombre interno** (`BP_Door_SC_C_1` existía en el persistente **y** en `L_Entering_SC`). En el log salen idénticos, así que **dos líneas contradictorias del "mismo" actor pueden ser dos actores**. Antes de perseguir una rama imposible del grafo, contar cuántos actores de esa clase hay cargados.
121. ⚠ **El Message Log del editor NO se limpia entre sesiones de PIE.** Errores viejos siguen a la vista arriba de la corrida nueva y se leen como si fueran de ahora. **Confirmar siempre contra el timestamp de `VR_Test.log`** antes de diagnosticar (es la misma trampa del "log acumulativo", pero en el panel visual, donde engaña más).
122. 🔴 **Un `PrintString` de instrumentación que desreferencia una variable sin guarda genera `Accessed None` a 90 fps.** Al instrumentar, poner el log **dentro de la rama ya protegida**, no antes. El instrumento no puede ensuciar el log que se va a leer.
123. 🔴🔴🔴 **El TIMBRE ya existía y lo reconstruí igual: `BP_MenuButton` con `bHoldByHover=true`.** Tenía hold por hover sin gatillo, `HoldTime`, `HoverRadius`, audios de hover y confirmación, **`HapticHover` con la mano resuelta**, y audio + `HapticHold` continuos durante la carga. Su tracker decía textual lo único que le faltaba: *"⬜ Falta el ring slider visual 0→100"* — exactamente lo que se construyó de cero en [[BP_Bell]].
    **Por qué el protocolo no lo cazó:** se buscó por *"hold de 3 segundos"* y *"progreso radial"*, que es como estaba pensada la mecánica, no por **"timbre"** ni **"botón"**, que es como estaba **nombrada**. 👉 **Buscar por el NOMBRE DE LA COSA además de por su función**, y muy en particular **grepear el `_INDEX.md` y los trackers por el sustantivo del pedido** antes de escribir el primer nodo. Un `grep -ril "timbre" blueprints/` lo habría encontrado en 2 segundos.
    ⚠ Beltrán decidió **reconstruirlo igual en limpio** (los BPs viejos tenían glitches y la etapa es justamente rehacer ordenado) — decisión válida, pero se tomó **sabiendo** que existía, que es lo que hay que garantizar.
124. 🟢 **CORRECCIÓN a §111: `set_properties` de `overrideMaterials` sobre el componente de una INSTANCIA colocada SÍ funciona** — al menos solo, en su propia llamada. §111 lo dio por "ignorado en silencio" y por eso mandaba a **reponer el actor**, que es caro y pisa los ajustes del usuario (§114). Verificado el 2026-08-18 sobre el `Body` de un `BP_Bell` ya colocado: la escritura aplicó y el `read` posterior lo confirmó.
    👉 **Antes de reponer un actor por un material, probá el `set_properties` solo y releé.** La regla que queda de §111 sigue viva para el caso en que se escriben **varias propiedades en la misma llamada** (ahí sí se pierden en silencio) — el patrón seguro es **una propiedad por llamada + relectura**.
    ⚠ El caso que lo generó: un actor colocado **antes** de que su BP tuviera el material en el CDO nace con `overrideMaterials: []` y se ve con `DefaultMaterial`. Los que se coloquen **después** lo heredan bien.

125. 🔴🔴🔴 **Una función PROPIA usada como EXPRESIÓN no se ejecuta: el compilador la PODA y devuelve el default.** Es la trampa más cara de la jornada: `HandNear` llamaba a `AnyHandClose(Pawn)` adentro de un `(return …)`, o sea como valor puro. Una función de Blueprint **no es pura**: tiene pin `execute`, y si nadie se lo cablea el compilador la elimina y **lee el default del pin de salida** — `false` para siempre. El grafo se ve perfecto, `read_graph_dsl` lo muestra bien, y **compila**: sale sólo como *Warning*.
    > *`<Funcion>` was pruned because its Exec pin is not connected, the connected value is not available and will instead be read as default*
    👉 **Toda llamada a una función propia va como SENTENCIA con exec cableado**, y el resultado se guarda en una variable que después se lee. En el DSL: nunca `(return (MiFuncion x))` ni `(Set v (MiFuncion x))` como expresión; sí `(CallFunction|MiFuncion x)` en la cadena de exec + `(SetV …)`.
    ✅ **[DOC] Epic documenta el mecanismo**, en el paso *Compile Functions* del compilador — la pre-compilación de cada grafo de función hace, en este orden:
    > *"Schedules execution and calculates data dependencies."*
    > *"**Prunes any nodes that are unscheduled or not a data dependency.**"*
    > — [Compiler Overview for Blueprints Visual Scripting](https://dev.epicgames.com/documentation/en-us/unreal-engine/compiler-overview-for-blueprints-visual-scripting-in-unreal-engine) · UE5-actual
    O sea: **el pruning es una etapa normal del compilador, no un bug.** Una llamada a función propia sin exec cableado no entra en el *schedule*, y una función **no es** una dependencia de datos (eso sólo aplica a nodos puros) → se poda. El default que queda es el valor del pin, no el resultado.
    🔴 **Y la regla de proceso: LEER LOS WARNINGS DEL COMPILADOR.** Se auditaron los nodos uno por uno tres veces mientras el compilador decía exactamente qué pasaba. Lo cazó Beltrán mirando el panel. Barrido barato después de cada compilación: `LogsToolset.GetLogEntries({"pattern":"pruned|Warning","category":"LogBlueprint"})`.
126. ⚠ **El listado de `find_node_types` puede estar DESACTUALIZADO para variables recién creadas — pero `create_node` igual las acepta.** Al agregar el widget `Ring` a `WBP_BellRing`, ni compilar ni guardar hicieron aparecer `Variables|WBP_BellRing|GetRing` en la lista (sí salía el `GetArc` viejo). **`create_node` con ese mismo type_id funcionó a la primera.** 👉 Si sabés que la variable existe, **probá crear el nodo aunque el buscador no la liste**; y no concluyas "no existe" a partir de un `find_node_types` vacío.
127. 🔴 **`RadialSlider`: los colores son READ-ONLY desde Blueprint.** Existen `GetSliderProgressColor`/`GetSliderBarColor` pero **no los setters** (`create_node` responde *does not exist*). Lo único escribible en runtime es **`Value`** (y `ShowSliderHandle`/`ShowSliderHand`/`UseVerticalDrag`). 👉 Los colores se autoran **en el designer**, y si hace falta modularlos en vivo se tinta el **`WidgetComponent`** que lo hospeda con `UserInterface|SetTintColorAndOpacity`.
    ⚠ Al tintar, **el alfa también multiplica**: si se pasa `Color × Brillo` con el brillo metido en las 4 componentes, un brillo de 0,25 apaga el widget en vez de bajarle la intensidad. Construir el multiplicador como `MakeLinearColor(B,B,B,1.0)`.
128. 💡 **Para vaciar un grafo existente sin que `write_graph_dsl` lo duplique: borrar los nodos con `delete_node` salvo el `K2Node_FunctionEntry`, y después hacer cirugía.** Con 40+ nodos, un `execute_tool_script` que itera `find_nodes` → `delete_node` lo resuelve en una llamada (envuelto en `try/except BaseException`, y verificando al final que sólo quedó el entry).
129. 🔴🔴 **Un actor colocado ANTES de configurar un componente conserva los defaults del MOTOR, no los del Blueprint — y en un `WidgetComponent` eso son 5 METROS.** El 2026-08-18 el `BP_Bell` del Hall tenía su `RingW` con `DrawSize 500×500` y `Scale 1,0` (defaults de `UWidgetComponent`) mientras el CDO decía `400×400` y `0,1`: el anillo habría salido como un cuadrado de **5 m** en vez de 40 cm. Es el mismo mecanismo de §117 (*component instance data* se reaplica después del CS y le gana al Blueprint), pero con una magnitud que arruina la escena entera.
    👉 **Después de tocar CUALQUIER propiedad de un componente en el CDO, releer ese componente en las instancias ya colocadas.** El síntoma no siempre es "no se ve": puede ser "se ve enorme" o "se ve en otro lado".
    ⚠ Y aplica §116 con fuerza: sobre la **instancia**, `{"x":800,"y":800}` aplicó **sólo `y`**, y `{"x":.05,"y":.05,"z":.05}` aplicó **sólo `z`** — mientras que sobre el **CDO** el mismo struct entró entero. 👉 **En instancias, un CAMPO por llamada y relectura de todos**; el bucle de reintento hasta que coincidan con el CDO es barato y es la única prueba.
    💡 `relativeRotation` usa **`pitch`/`yaw`/`roll`**, no `x`/`y`/`z` — escribirle `x` tira `KeyError`.
    🔴🔴🔴 **El caso peor de esta familia: `WidgetClass = None` en la instancia.** Mismo día, mismo actor: el `RingW` del `BP_Bell` colocado tenía **`widgetClass` vacío** mientras el CDO apuntaba a `WBP_BellRing_C`. Síntoma: **el anillo se ve perfecto en el viewport del Blueprint y NO existe en el nivel ni en PIE.** Sin error, sin warning, sin `Accessed None` — un `WidgetComponent` sin clase simplemente no dibuja nada.
    ⚠ **Y el "en el BP sí se ve" es una pista falsa que hace perder el tiempo en el lado equivocado** (blend mode, orientación, backface culling, DrawSize, el widget mismo). Todo eso estaba bien. 👉 **Ante "se ve en el BP y no en el mundo", lo PRIMERO es diffear el componente de la instancia contra el del CDO** — no teorizar sobre renderizado:
    ```
    ObjectTools.get_properties(<comp del CDO>,  [props]) vs
    ObjectTools.get_properties(<comp de la instancia>, [props])
    ```
    Leer **una propiedad por llamada** (algunas revientan la llamada entera si el componente no las tiene, y se pierde el resto) y comparar. Tarda 10 segundos y contesta la pregunta.
130. 🎨 **`WidgetComponent.BlendMode` viene en `Masked` y eso arruina cualquier forma curva.** Alfa de 1 bit = borde escalonado por más `DrawSize` que le pongas. Para anillos, círculos y degradados va **`Transparent`**. Antes de subir la resolución de un widget que se ve feo, **mirá el blend mode**: suele ser eso y no los píxeles.
131. ⚡ **Si un actor "nace escondido", esconderlo en `BeginPlay` — nunca dentro de la función que corre por timer.** El patrón común es `BeginPlay → SetTimer(0.3) → Boot`, porque cachear el pawn necesita que el pawn exista. Pero si `Boot` es también quien pone la escala en 0, el actor **se ve a tamaño real durante esos 0,3 s** (≈18 frames) y después pega el salto a cero: el usuario ve un parpadeo y luego la animación de entrada. Pasó con [[BP_Bell]] el 2026-08-18.
    👉 **Partir el arranque en dos por lo que cada cosa necesita:** lo que no depende de nadie (capturar la escala autoral, esconderse) va en `BeginPlay`; lo que necesita que el mundo esté armado (cachear pawn, directores) se queda en el timer.
    ⚠ **Y NO mover eso al Construction Script**, aunque sea aún más temprano: el CS **re-corre en cada cambio de propiedad**, así que la segunda pasada capturaría la escala ya puesta en 0 y el actor no volvería a crecer jamás. Es la trampa de "guardar el valor autoral en el mismo lugar donde lo piso".

## 🌊 Cosecha 2026-08-18 (Alma: material, WPO y DSL)
132. 🔴🔴 **En un CDO, un struct hay que escribirlo ENTERO; campo por campo lo CORROMPE.** Es el **reverso exacto de §116**. Copiando los valores de una instancia al CDO de `BP_Alma_SC`, escribir los `LinearColor` campo a campo dejó los cinco colores en `r=5.6e-06, g=6.4e-43, b=-nan` — basura de memoria, sin ningún error.
    | Destino | Forma correcta |
    |---|---|
    | **Instancia de componente** | **un campo por llamada** (el struct entero aplica sólo uno, §116) |
    | **CDO** | **el struct ENTERO en una llamada** (campo por campo lo destruye) |
    👉 Y en los dos casos, **releer**: el `-nan` no lo detecta nadie más.
133. 🔴 **Translucidez a DOS CARAS = parches triangulares intermitentes.** Unreal ordena la translucidez **por objeto, no por triángulo**: dentro de una malla los triángulos se dibujan en **orden de índice**. Con `TwoSided` + opacidad baja se ven las dos superficies mezcladas y **gana la del índice más alto, no la más cercana** → parches con forma de triángulo que aparecen y desaparecen al orbitar. El usuario lo describe como *"se ve cuadriculada o pixelada"* y manda a buscar en el lugar equivocado (malla, textura, normales, resolución).
    ✅ **Arreglo: `TwoSided = false`**, que además corta a la mitad los píxeles translúcidos. ⚠ Es una propiedad **estática**: no puede ser parámetro de un material instance.
134. 🔴 **Con WPO hay que subir el `Bounds Scale` o el objeto se CULLEA.** El motor calcula la visibilidad con los bounds **originales**, ignorando el desplazamiento del vertex shader → el objeto desaparece de golpe al mirarlo de reojo. En Alma: 1.6. Silencioso y desconcertante.
135. 💡 **El nodo `Time` de un material anima EN EL VIEWPORT del editor; el Construction Script NO puede animar y Blueprint puro NO puede tickear en el editor sin C++.** 👉 Si el usuario quiere autorar una animación viendo el resultado sin darle Play, **el lugar es el material** (WPO), no el BP. Bonus: sale más barato (vertex shader vs Tick + `SetActorLocationAndRotation`). ⚠ El precio: el **actor no se mueve, sólo su dibujo** — nada que lea su posición verá el movimiento.
136. 🎨 **Un color emisivo SUMADO sobre una base clara siempre da BLANCO.** En móvil, sin HDR ni bloom, no existe "azul más brillante que el blanco": pasar de 1 en los tres canales **es** blanco. Síntoma: *"por más que elijo el color, se ve muy blanco siempre"*. ✅ Pasar la suma a **interpolación** (`lerp(base, Color, mascara)`) y mantener la intensidad en 1; para un tono saturado, usar un color con al menos **un canal bajo**.
137. ⚠ **Los índices `_N` de las expresiones de material NO son estables ni predecibles.** Agarrar `MaterialExpressionMultiply_11` "porque debería ser el del borde" rompió la cadena del gradiente. 👉 **Resolverlos siempre por `parameterName`**: recorrer `get_expressions` y leer la propiedad, nunca por número.
138. 🔧 **Cinco trampas del DSL / `create_node` encontradas de una sentada:**
    - **Los pines de salida de un EVENTO son `[OutputDelegate=0, then=1, ...]`.** Cablear el índice 0 falla con *"Could not connect pin OutputDelegate to execute"*. En funciones el `then` sí es 0.
    - **`Math|Vector|vector+vector` es el nombre que IMPRIME el read, no uno que acepte `create_node`.** Para crear operadores hay que usar el promocionable (`Utilities|Operators|Add` o `(+ …)` en DSL). Lo mismo para `-` y `*`.
    - **Los getters Y setters de bool pierden la `b` al CREARLOS**: `Variables|X|SetAppearing`, no `SetbAppearing` — aunque el `read` los imprima con la `b`.
    - **Nodos con nombre duplicado**: `Rendering|Material|SetScalarParameterValue` existe **dos veces** (la de Material Parameter Collections y la de MaterialInstanceDynamic) y `create_node` toma la primera. ✅ Se desambigua con **`declaring_class`** (`/Script/Engine.MaterialInstanceDynamic`).
    - **Algunas llamadas necesitan `self` explícito como primer argumento** (`SetActorLocationAndRotation`, llamadas a funciones propias con parámetros); si no, el DSL mapea el primer argumento al pin `self` y falla por tipos.
139. ⚠ **`remove_function_graph` + volver a crear el mismo nombre en la misma tanda → sale `Nombre_0`.** Hay que **compilar entre medio** para que el nombre se libere. Y si algún nodo llamaba a esa función, el BP **deja de compilar** hasta recablearlo.
140. 🎮 **Las teclas de debug NO funcionan en Simulate — hay que usar Play.** Medido en el mundo de PIE: en Simulate `Tick` y `BeginPlay` **sí corren**, y hasta **existe** un `PlayerController_0` con su `SpectatorPawn_0`. Lo que no pasa es el input: **el teclado lo consume el viewport del editor** para la cámara libre y no llega al stack del PlayerController, así que `WasInputKeyJustPressed` devuelve false siempre.
141. ⚠ **`set_properties` no puede cambiar TAMAÑO y VALORES de un array en la misma llamada** (*"ArrayAdd: elements changed alongside the size change"*) — el mismo límite que ya frenaba los puntos de un spline. ✅ **Dos pasos: primero crecer conservando los elementos existentes, después escribir los valores con el tamaño ya correcto.**
142. 🔴 **`Set{Scalar,Vector}ParameterValue` están DUPLICADOS y el DSL agarra el de *Material Parameter Collection*.** Amplía §138: no es sólo `create_node`, **el `write_graph_dsl` también** — y el síntoma es claro pero engañoso: *"Could not connect pin MID to Collection. The pins may be incompatible types."* Parece un problema con la variable `MID` y es una colisión de nombres. Se confirma en un vistazo: `find_node_types` con filtro `Rendering|Material|Set` devuelve **`SetVectorParameterValue` y `SetScalarParameterValue` dos veces cada uno**.
    ✅ **La salida buena NO es `declaring_class`, es no necesitar el MID:** usar **`Set{Scalar,Color,Vector}ParameterValueOnMaterials`**, cuyo pin `self` es el **componente de malla**. Crean y reusan el MID internamente → se van la variable `MID`, el `CreateDynamicMaterialInstance`, el `IsValid` **y** la ambigüedad. Tres sabores: `Color` toma **LinearColor** (con alfa), `Vector` toma **FVector**, `Scalar` un float. Usado en `BP_TurrellPanel_SC`: 15 parámetros empujados y **cero estado interno**.
143. 💡 **`bind` sobre un getter puro en el DSL cachea el nodo una sola vez.** `(bind _p (Variables|Default|GetPanel))` y después reusar `_p` en 16 llamadas crea **un** getter, no 16 — la palanca #1 de `bp-lean-construction.md`, aplicable directo desde el DSL sin cirugía de nodos. El `read` posterior lo devuelve con el nombre que le puso el compilador (`_panel`), no con el que se escribió.
144. ⚠ **El DSL inserta conversiones automáticas y las muestra en el read.** Un `(.x (GetSize))` sobre un `Vector2D` se relee como `(.x (Math|Conversions|ToVector(Vector2D) (GetSize)))`. **No es un nodo de más que haya que limpiar**: es el cast que el compilador necesita. Ojo con confundirlo con basura al auditar.

145. 🔴🔴 **Una expresión de material creada SIN setear su valor nace en CERO, y el material compila en verde.** Es [[soul-charger-declarado-no-aplicado]] otra vez, pero en el grafo de material: `add_expression` de un `Constant` sin el `set_properties` que le da el valor deja un `0` silencioso. Caso real (`M_TurrellGradient`, 2026-08-18): de dos constantes de valor 2, **a una se le puso el valor y a la otra no**. Esa alimentaba el `AppendVector` del aspecto → `float2(Aspect*2, 0)` → **el eje Y se anulaba antes del `length`**, y un gradiente radial salía **lineal sobre un solo eje**. Cero errores, cero warnings.
    👉 **Dos síntomas distintos que reporta el usuario pueden ser el mismo cero.** Acá fueron *"¿puedes hacerla radial?"* y *"no entendí lo del ColorOuter"*: la misma constante causaba las dos cosas (el color exterior quedaba arrinconado en dos franjas del borde).
    ✅ **Barrido barato que lo caza en una llamada:** recorrer `get_expressions` y listar **toda constante cuyo valor sea 0** — las que son cero a propósito son rarísimas, así que la lista debería venir vacía. Hacerlo **siempre** después de construir un material por script.
146. 🔴🔴🔴 **Sembrar una instancia NO es igualarla al CDO: se siembran SÓLO las variables que nacieron en cero.** El patrón "leer CDO, diffear contra la instancia, escribir todo lo que difiera" es correcto **el día que se coloca el actor** y **destructivo cualquier día posterior** — para entonces la instancia ya tiene **datos de autor** (§114-115). Error real (2026-08-18, `BP_TurrellPanel_SC`): al agregar 3 variables nuevas corrí ese diff y de paso **pisé 6 valores que Beltrán había ajustado a mano** (`Brightness` 0.256 → 1, `Aspect` 1.96 → 1, `PulseAmount` −0.164 → 0.08…). Se recuperaron **sólo porque el script imprimía el par `[cdo, instancia]` antes de escribir**.
    ✅ **Regla:** al agregar variables a un BP ya colocado, escribir **la lista explícita de nombres nuevos**, nunca un diff genérico. ✅ **Y siempre devolver el valor viejo en el output antes de pisarlo** — es lo único que convierte un accidente en algo reversible.
147. 🔴🔴 **La §116 tiene una regla exacta: en una instancia de componente `set_properties` aplica SÓLO EL PRIMER CAMPO del struct — así que poné primero el que te importa.** Medido el 2026-08-18 colocando `BP_InstructionsPanel_SC`: `{"relativeLocation":{"x":250,"y":0,"z":150}}` dejó `z` en 0 por más que se repitiera la llamada; **`{"relativeLocation":{"z":150,"x":250,"y":0}}` lo aplicó de una**. Idem `relativeRotation` con `yaw` adelante. ✅ Receta: **una llamada por campo, con ese campo al frente**, y verificar leyendo el componente (no `get_actor_transform`, que puede confundir porque refleja lo mismo).
148. 🧩 **UMG por MCP: `AddWidget` devuelve `None`, y las referencias se piden con `GetWidgets`.** Pasar el retorno de `AddWidget` como `parentWidget` da el error engañoso *"Widget can't have children"* — no es que el contenedor no acepte hijos, es que el padre llegó nulo. ✅ Los refPaths son **predecibles**: `<WBP>.<WBP>:WidgetTree.<Nombre>` para widgets y **`<WBP>.<WBP>:WidgetTree.<Padre>.<SlotName>` para los slots** (el slot cuelga del PADRE, no del hijo). `UMGToolSet.GetWidgets` devuelve el árbol entero con nombre, padre, slot, clase y `bIsVariable` — es la forma de verificar.
149. 🔴 **Las continuaciones de un multi-exec del DSL son sub-listas ETIQUETADAS, no statements sueltos.** Dentro de un `(bind x (CastTo...) ...)` hay que escribir `(:then <statements>)` y `(:CastFailed)`. Poner statements pelados —aunque sean llamadas exec normales— falla con *"(bind) expects only exec continuations after the expression"*. Costó tres intentos por leer el ejemplo de `dsl.md` a medias: **el ejemplo ya lo mostraba**.
150. 🔴🔴 **`(if (Utilities|IsValid x) A (else B))` COMPILA Y BORRA LAS DOS RAMAS.** `Utilities|IsValid` es el **macro multi-exec** (pines `Is Valid` / `Is Not Valid`), no un booleano puro: usarlo como condición de un `if` deja el grafo en **un solo nodo suelto**, sin `A` ni `B`. Compila en verde y la función no hace **nada**. Es la trampa del "IsValid en expresión", ahora con su firma exacta. ✅ Forma correcta: `(Utilities|IsValid x (:"Is Valid" A) (:"Is Not Valid" B))`. 👉 **Sólo se detecta con el `read_graph_dsl` posterior** — el write devuelve éxito. Cazado así el 2026-08-18 en `BP_InstrButton_SC`.
152. 🔴🔴 **La curva de DPI del proyecto hacía que el `WidgetComponent` NO coincidiera con el Designer — se dejó PLANA en 1.0 (2026-08-18).** Síntoma: con el Designer en `Custom 1920×1200` y **DPI Scale 1,0**, el mismo widget en el mundo mostraba la fuente ~2,5× más grande y el corner radius ~3× más grande, **pero la imagen anclada perfecta**. 👉 **Esa es la firma exacta**: se agranda todo lo definido en **píxeles** (fuente, radios, paddings) y **no** lo definido en **fracciones** (anclas) ⇒ el widget se está maquetando a una resolución lógica distinta y estirándose después. La causa es que el `WidgetComponent` aplica la curva de DPI y el Designer en modo `Custom` no.
    ✅ **Fix aplicado en `Config/DefaultEngine.ini`** (la sección `[/Script/Engine.UserInterfaceSettings]` **no existía**, o sea que se usaba la curva por defecto del motor): `UIScaleCurve` con **una sola llave en 1.0** y extrapolación constante, más `ApplicationScale=1.0`. **Razón de fondo: esta obra no tiene UI de pantalla** — todos los widgets son world-space y su tamaño físico lo da la escala del componente, así que la curva de DPI no adapta nada y sólo mete un factor invisible entre editor y mundo.
    ⚠ **Requiere reiniciar el editor** (las secciones de config se leen al arrancar) **y afecta a TODOS los widgets del proyecto** — revisar `WBP_BellRing`, `WBP_DoorTitle`, `WBP_SoulHUD` y los de Touch, que van a verse distintos (probablemente más chicos). Backup: `DefaultEngine.ini.bak-dpi`.
151. ⚠ **`PawnSC` en None: en Simulate NO hay pawn VR poseído.** `GetPlayerPawn(0)` no devuelve el `BP_VRPawn_SC`, el cast de `CachePawn` falla y la variable queda nula **para siempre**, porque `Boot` cachea **una sola vez** a los 0,3 s. Síntoma: *"Accessed None trying to read property PawnSC"* cada frame. 👉 **No es sólo cosa de Simulate**: si el pawn tarda en existir (streaming, orden de carga) pasa igual en Play. ✅ Patrón: el Tick pregunta `IsValid(PawnSC)` y, si no, **vuelve a llamar `CachePawn`** — se auto-repara solo. Afecta a **todo BP que cachee el pawn en un Boot con timer**, `BP_Bell` incluido.
153. 🟢 **`SetStaticMesh` en RUNTIME **NO** se lleva puesto el MID — el peligro estaba mal enunciado.** El tracker de `BP_ProtoSoul_SC` avisaba "cambiar la malla después se lleva el MID y se pierden todos los parámetros". **Medido el 2026-08-19** con un control positivo (loguear el material del slot 0 *después* del swap): dio `MID_M_ProtoSoul_0` en las 5 amebas. `UStaticMeshComponent::SetStaticMesh` sólo **recorta** los override materials cuando la malla nueva tiene **MENOS slots**; con una malla de un solo material el slot 0 sobrevive intacto.
    👉 **El enunciado correcto es sobre el ORDEN dentro del Construction Script** (donde los componentes se reconstruyen de cero en cada corrida): ahí `ApplyMesh` **sí** tiene que ir antes de `CreateDynamicMaterialInstance`. En runtime, sobre un componente ya construido, el swap es seguro.
    ⚠ El caso que **sí** rompe: una malla con **0 slots de material**. Síntoma: el objeto sale gris/con su material por defecto.
    💡 **Y la salida barata para re-empujar parámetros sin tocar el Construction Script**: `Rendering|Material|Set{Color,Scalar,Vector}ParameterValueOnMaterials` sobre el **componente** reusa el MID que ya está en el slot — se van la variable `MID`, el `CreateDynamicMaterialInstance` **y** la colisión de nombres del §142. Es lo que permitió configurar 5 almas distintas sin reescribir un CS que es intocable.
154. 🔧 **El `for` del DSL SÍ funciona, y SÍ admite anidarse dentro de una rama de `if`** (probado 2026-08-19 en `BP_SoulPicker_SC`, que nunca se había usado en este proyecto). Las dos formas andan: `(for i (range (Length arr)) ...)` y `(for e arr ...)`. El `read_graph_dsl` los devuelve con los nombres que les puso el compilador (`_index`, `_array_element`).
    ⚠ Pero **hereda la regla del multi-exec**: el `for`, como el `if`, **termina la lista de statements**. Nada puede ir después. Por eso una función que necesita "recorrer y después decidir" hay que partirla en dos — no es mal diseño, es la herramienta.
155. 💡 **`Game|SpawnActorfromClass` RE-TIPA su pin de salida si la clase va como literal en el DSL.** `(Game|SpawnActorfromClass "/Game/.../BP_X.BP_X_C" transform "AlwaysSpawn")` devuelve un `BP_X` de verdad — el `read` posterior lo delata porque el nodo pasa a llamarse `Game|SpawnActorBPX`. 👉 **No hace falta el `CastTo` de rigor**, que además es multi-exec y rompería la lista de statements. Si el pin quedara genérico (`Actor Object Reference`), las llamadas a funciones de la clase fallan al conectar y ahí sí hay que castear.
    ⚠ **No existe el `BeginDeferredActorSpawn` en la paleta**, así que **no se pueden setear variables ANTES del Construction Script** por esta vía (eso pediría *Expose on Spawn*, que el MCP no expone). El patrón que queda: spawnear y después llamar un `Configure(...)` en el actor recién nacido.

156. 🔴🔴 **Dos funciones escribiendo la MISMA propiedad: la guarda no puede depender de un flag que una de ellas apaga.** Caso real (`BP_ProtoSoul_SC`, 2026-08-19): `ApplyHoverScale` estaba guardada por `if (not bAppearing)` y `StepAppear` **se apaga a sí misma** (`SetbAppearing false`) al terminar la animación → el frame siguiente la otra se destraba y **pisa la escala**. Síntoma que reporta el usuario: *"se desvanecen y vuelven a aparecer"*.
    👉 **La firma del bug: el error ocurre UN FRAME DESPUÉS de que termina la animación**, que es justo cuando uno deja de mirar. Por eso había sobrevivido a varias sesiones de prueba con el rig de teclas.
    ✅ **Método:** escribir la **matriz de estados** y comprobar que cada celda tiene **exactamente un dueño** — incluida la celda terminal, que muchas veces tiene que tener **cero** dueños (nadie escribe = el valor se queda quieto).
157. 🔴🔴 **El `AND` de Blueprint NO hace corto-circuito: es una llamada a función y evalúa SIEMPRE los dos operandos.** `(and (IsValid X) (X.Algo))` **no protege** a `X.Algo` — se lee igual y tira `Accessed None`. Es la contraparte lógica de la trampa "IsValid en expresión" (§150), y muerde igual de silenciosa: el grafo compila y el log se llena.
    ✅ **Poner el gate como `Branch` aguas arriba**, no como operando de un `and`. En `BP_SoulPicker_SC` el recorrido del array de almas (algunas ya destruidas) se corta en `Choose` con un `if (not bChosen)`, no confiando en el `and` de `Judge`.
158. 💡 **Para destruir un actor DESPUÉS de su animación de salida: `Actor|SetLifeSpan(actor, duracion + margen)`.** Un nodo, sin timers, sin variables de estado, sin función auxiliar — y leé la duración del propio actor (`GetDisappearTime`) para que siga el parámetro de autor si cambia. Alternativa típica (timer + función de callback sin parámetros) cuesta 3 nodos más y una función.

159. 🔴🔴 **Agregar una variable a un Blueprint YA COLOCADO deja la INSTANCIA en cero aunque el CDO tenga el valor bien.** Es la §146 vista desde el otro lado, y se repite cada vez: el 2026-08-19 `BP_SoulPicker_SC` busedó almas con `PickTag = None` y `bAwakeOnStart = false` mientras su CDO decía `"soul_pick"` / `true`. Síntoma: **el sistema anda perfecto en el asset y no hace nada en el mundo.**
    ✅ **Al agregar variables a un BP colocado, escribirlas también en cada instancia — con la LISTA EXPLÍCITA de nombres nuevos**, nunca un diff genérico contra el CDO (eso pisaría los datos de autor, §146).
    💡 **Y lo que lo cazó en una sola corrida fue un `PrintString` con un CONTEO**, no con un "arranqué": `almas encontradas = 0` señala solo. **Al loguear, loguear la CANTIDAD o el VALOR, no el paso.**

160. 🔧 **`connect_expressions` de materiales: los nodos de UNA sola entrada la llaman `"None"`, no `"Input"`.** `Sine`, `Saturate`, `Abs`, `OneMinus`, `ComponentMask` — todos. Con `"Input"` la conexión falla y el material compila con *"Missing Sine input"*. Los binarios (`Add`, `Multiply`, `Subtract`, `Divide`, `AppendVector`) sí usan `A` / `B`.
    ✅ **No adivinar: `get_expression_input_names(expression)` lo contesta en una llamada** y devuelve `["None"]`. Lo mismo para las salidas con `get_expression_output_names` (la salida única es `""`).
161. 💡 **Un material UNLIT deja la NORMAL libre como almacenamiento por vértice.** En `BP_SoulRing_SC` se guarda ahí la **dirección del ancho de la cinta** en vez de la normal real, y el material la lee con `VertexNormalWS` para engordar, adelgazar y colapsar el trazo por WPO. Sin eso, un shader no tiene forma de saber hacia dónde "ensanchar" una geometría, y habría que gastar un UV extra o vertex colors.
    💡 Y el corolario del crecimiento: **colapsar la geometría a ancho 0 por WPO es más barato que enmascararla** — quedan triángulos degenerados, sin alpha test (que en tilers rompe el early-Z) y sin translucidez.
162. ⚠ **`execute_tool_script` no tiene `exec` ni `compile`**: no se puede bootstrapear un script largo leyéndolo del disco. Un script grande hay que mandarlo **inline** en `arguments`. 💡 Para que quepa: definir el grafo como **listas de tuplas** (nodos y aristas) y recorrerlas con un `for`, en vez de escribir una llamada por nodo — un material de 77 expresiones entra cómodo en una sola llamada.
    ⚠ `EditorAppToolset.CaptureViewport` **exige `captureTransform` Y `annotations`** aunque no se usen; sin ellos falla pidiendo "needs a default value", de a uno por vez.

163. 🔴 **En `execute_tool_script`, el `try/except` tiene que envolver el CUERPO ENTERO, no sólo las llamadas al tool.** La plantilla `safe_script.py` protege `T()`, pero **el código Python que está entre medio no está protegido** y si levanta, el Undo se dispara igual. Pasado el 2026-08-19: un `pins.get('input_pins', [])` sobre el dict que devuelve el plugin tiró `TypeError` y abortó el script a mitad.
    ⚠ **El sandbox usa `_StrictDict`: `.get(clave, default)` NO acepta el segundo argumento.** Usar `d['clave']` o `d.get('clave')` a secas.
    ✅ Patrón correcto: `def run():` con **todo** adentro de un `try/except BaseException` que devuelva `{'error': ...}`.

164. 🔴🔴 **Agregar un COMPONENTE a un Blueprint ya colocado: el componente aparece en las instancias, pero sus propiedades quedan en el DEFAULT DE FÁBRICA.** El componente se propaga a las instancias **en el instante del `add_component`**, capturando lo que valía entonces; cualquier `set_properties` posterior sobre el archetype (`<Comp>_GEN_VARIABLE`) **ya no las alcanza**.
    Caso real (2026-08-19, los anillos de `BP_ProtoSoul_SC`): 4 `ChildActorComponent` presentes en las 5 instancias con **`ChildActorClass = None`** mientras el CDO lo tenía bien. Síntoma: `anillos registrados = 0` — todo existe y nada funciona.
    ✅ **Orden correcto: `add_component` → configurar el archetype → RECIÉN AHÍ colocar los actores.** Si ya están colocados, hay que escribir las propiedades **en cada instancia** (n° actores × n° componentes llamadas). Es la §159 (variables) y la §146, ahora en su tercera cara: **componentes**.
    💡 Y otra vez lo que lo cazó en una corrida fue **loguear el CONTEO**, no el paso.

165. 🔴🔴🔴 **`ChildActorComponent`: el `ChildActorTemplate` de las instancias queda en `None` y NO es escribible por API — el actor hijo nace con los defaults de CLASE.** Es la cara más venenosa de la §164 porque **en el editor se ve BIEN**: el preview del Blueprint usa el template, así que el autor ajusta colores y tamaños, los ve, y recién al dar Play descubre que todos los hijos nacen iguales. `set_properties` sobre `ChildActorTemplate` responde *"the following properties could not be set"*.
    ✅ **La única salida limpia: recolocar los actores** (leyendo y restaurando sus valores primero) para que los componentes nazcan ya configurados. ✅ **La alternativa sin tocar el nivel:** que el actor padre **empuje la config al hijo por código** tras spawnearlo — conviene medir primero **qué varía de verdad entre hijos** (en `BP_ProtoSoul_SC` resultó ser **sólo el color**: todo lo demás era compartido y podía vivir en el CDO del hijo).
    🚩 **Tomado junto con §159 y §164, el patrón es uno solo: TODO lo que se agrega a un Blueprint después de colocar sus actores llega incompleto a las instancias** — variables, componentes y templates. **Regla: terminar la estructura del BP ANTES de poblar el nivel**; y si ya está poblado, asumir que hay que reparar instancia por instancia (o recolocar).
    💡 Corolario de diseño: el `ChildActorComponent` mete una indirección (componente → template → actor) que se rompe en cada uno de esos puntos. Para composición **dentro** de un actor, los componentes nativos no tienen ninguno de estos modos de fallo.

166. 🔴🔴 **El `WorldPositionOffset` se suma en ESPACIO DE MUNDO, o sea DESPUÉS de la escala del objeto — escalar un actor NO escala sus efectos de WPO.** Síntoma exacto (2026-08-19, los anillos de la proto ameba al viajar a la cara): *"los bordes son gruesos y duros; debería verse como una miniatura del que vemos en tamaño normal"*. La geometría se achica 6× y el ancho del trazo, el serpenteo y la deriva siguen midiendo los mismos centímetros.
    ✅ **Arreglo: un parámetro `ScaleComp` que multiplica TODO el WPO** justo antes de la salida (un nodo), alimentado con la escala de mundo del componente.
    🔴 **Y normalizarlo contra la escala AUTORADA, no usar la escala pelada:** si el objeto ya tenía una escala propia de diseño, la escala cruda cambia el look en tamaño normal. `ScaleComp = WorldScale / ScaleRef`, con `ScaleRef` capturado la primera vez → vale 1 mientras nadie lo achique.
    💡 **Que el objeto se compense SOLO** (leyendo su propia `GetWorldScale` en su Tick) lo vuelve inmune a quién lo escale, en vez de depender de que el padre le pase el factor. Y empujar al material **sólo cuando el valor cambia** deja el costo en cero.
    ⚠ Lo que NO hay que compensar: todo lo que ya vive en espacio UV (suavizados de borde, anchos de revelado, máscaras a lo largo del trazo) — eso es proporcional por construcción.

167. 🔴🔴🔴 **Un `ChildActorComponent` tiene CUATRO copias de cada valor, y la que corre en PIE es la tercera.** Cierra la serie §159/164/165. La cadena es: **CDO de la clase hija → `ChildActorTemplate` del componente → ACTOR HIJO YA SPAWNEADO EN EL MUNDO DEL EDITOR → su copia en PIE**. 🚨 **PIE DUPLICA el actor hijo del editor; no lo vuelve a crear desde el template.** Así que arreglar CDO + template y verificarlos en verde **no alcanza**: los hijos que ya vivían en el editor conservan lo viejo y son los que se juegan.
    Caso real (2026-08-19): los anillos seguían auto-dibujándose en loop con los 4 templates ya en `LoopDelay = 0` / `bDrawOnStart = false`, porque los 20 actores hijos del editor (5 duenos × 4) tenían aún `1.5` / `true`.
    ✅ **El arreglo NO es perseguir la copia que falta — es que el DUEÑO IMPONGA el estado al adoptar al hijo.** En `AddRing` alcanzaron 3 nodos (`bDrawOnStart = false`, `LoopDelay = 0`, `SetProgress(0)`), y de yapa vuelve el resultado **independiente del orden de `BeginPlay`**: si el hijo alcanza a arrancar solo, el dueño lo cancela.
    👉 **Regla general: cuando un actor es dueño de otro, no confiar en la configuración heredada — imponerla en el momento de adoptarlo.** Es barato y corta de un saque toda la cadena de copias.
    💡 Método: ante "cambié el default y sigue haciéndolo", **listar TODAS las copias del valor con `find_actors` sobre el mundo del editor** (los hijos aparecen como `<Comp>_GEN_VARIABLE_<Clase>_CAT_####`) antes de tocar nada. Ahí se ve cuál está rancia.

168. 🔴🔴🔴 **Recompilar el Blueprint HIJO deja `ChildActorTemplate` en `None` en todos los actores ya colocados.** Cierre definitivo de la serie §159/164/165/167. No importa cuántas veces se repare (ni recolocando los actores): **al siguiente `compile` del hijo se vuelve a romper**, y los hijos pasan a nacer con los defaults de CLASE. Síntoma: *"nacen todos iguales, sin los parámetros que había definido"* — con los templates y los actores hijos del editor **conteniendo los valores correctos**, porque los que fallan son los de PIE.
    🚩 **Consecuencia de diseño, no un bug a esquivar: el `ChildActorTemplate` NO es un lugar donde autorar** mientras el Blueprint hijo siga en desarrollo.
    ✅ **Patrón correcto:** medir **qué varía de verdad entre hijos** (en `BP_ProtoSoul_SC` resultó ser sólo el color) y partir la autoría en dos: **lo compartido al CDO del hijo** (inmune al compile) y **lo que varía a un array del padre**, que lo empuja al adoptar. Los templates quedan vestigiales.
169. 🔴🔴 **Los parámetros de material que empuja el Construction Script NO sobreviven a la duplicación del actor (PIE, child actors).** El MID creado en el CS se pierde; el componente vuelve con el material base y el primer `Set...ParameterValueOnMaterials` de runtime **crea un MID nuevo con los defaults del material**. Síntoma: el objeto se ve bien en el editor y sale con el look por defecto en Play, **aunque sus variables sean correctas** — lo que manda a buscar el bug en el lugar equivocado.
    ✅ **Regla: extraer los pushes a una función (`PushMaterial`) y llamarla desde el Construction Script Y desde `BeginPlay`.**
    💡 **Diagnóstico que lo separa en una llamada:** leer el **valor efectivo del MID** (`OverrideMaterials[0]` → `VectorParameterValues` / `ScalarParameterValues`) y compararlo con la variable del Blueprint. Si la variable está bien y el MID no, es esto. Mirar sólo las variables lleva horas en la dirección contraria.

170. 🚩 **CIERRE de la serie §159/164/165/167/168 — `ChildActorComponent` no sirve para composición dentro de un actor que se está desarrollando.** Cinco bugs distintos en una sola tarde, todos de la cadena **componente → template → actor hijo**: (1) `ChildActorClass` nulo en instancias, (2) variables nuevas en cero, (3) `ChildActorTemplate` nulo — y que **vuelve a nulo en cada compile del BP hijo**, (4) actores hijos rancios ya spawneados en el editor que PIE duplica tal cual, (5) el MID del Construction Script perdido al duplicar.
    ✅ **Con `ProceduralMeshComponent` (o cualquier componente nativo) NINGUNO de esos modos de falla existe.** No hay template que se anule, no hay actor intermedio que se quede rancio, y el estado vive en el mismo Blueprint que lo usa.
    💡 **Cuándo SÍ usar `ChildActorComponent`:** cuando el hijo es una clase **estable y terminada** que de verdad necesita ser un Actor (recibe input propio, se desprende, tiene su ciclo de vida). Para "cuatro copias de una malla generada", es la herramienta equivocada.
    💡 **Y la señal de que hay que migrar:** si al arreglar un bug de datos aparece **otro del mismo tipo en otra copia**, no seguir parcheando — el problema es la cadena de copias, no el valor.

171. 💾 **Para borrar y reponer actores sin perder nada: volcar sus propiedades a un `.json` en `VR_Test/Saved/`, no a la memoria del agente.** El script de lectura escribe con `AssetTools.write_file`; el de restauración lo lee con **`open()`** dentro de `execute_tool_script` (⚠ `exec` y `compile` están bloqueados en el sandbox, pero `open()` funciona). Ventajas: la restauración es **exacta**, sobrevive a que el agente pierda contexto entre medio, y queda un artefacto auditable.
    ✅ **Y cerrar SIEMPRE con un diff propiedad por propiedad que reporte el conteo** (`64/64 iguales`), no con un "listo". Es la diferencia entre creer que restauraste y saberlo.
    ⚠ Guardas obligatorias antes del borrado: que el json tenga la cantidad esperada **y** que el nivel tenga esa misma cantidad. Si no coinciden, abortar sin borrar.
172. ⚠ **`set_properties` sobre el ARCHETYPE de un componente NO propaga a las instancias** — y por lo tanto **no sirve para testear si la propagación del editor funciona**. La propagación real la dispara el editor (`PostEditChangeProperty` + `PropagateDefaultValueChange`) cuando se arrastra el componente en el viewport del Blueprint; una escritura por MCP se salta ese camino.
    👉 **No concluir "la propagación está rota" desde una prueba por MCP.** Ese experimento mide otra cosa. La única prueba válida es a mano en el editor — y hay que decirlo así, en vez de reportar un falso negativo.

173. 📐 **Al escalar un objeto, auditar CADA término del WPO por separado: los que están en unidades ABSOLUTAS se rompen, los que están en fracciones del objeto no.** Amplía la §166 con el método. En `M_ProtoSoul` convivían tres y sólo uno estaba mal:
    | Término | Unidad | ¿Escala solo? |
    |---|---|---|
    | Deformación | **fracción del `ObjectRadius`** | ✅ sí |
    | Rotación del flotar | producto cruz contra la **posición relativa** | ✅ sí (la posición ya viene escalada) |
    | Traslación del flotar | **centímetros absolutos** | ❌ no → el objeto chico "se va de su punto" |
    ✅ **Arreglo quirúrgico: insertar el multiplicador entre el PARÁMETRO y sus consumidores**, no al final del WPO — así sólo se afecta el término culpable y no se toca el resto del grafo. Se ubica al consumidor recorriendo `get_expression_inputs` de todas las expresiones y filtrando por la fuente.
    💡 **Regla de diseño para materiales que van a escalarse: expresar los desplazamientos como FRACCIÓN del tamaño del objeto desde el principio** (`ObjectRadius`), y dejar los centímetros absolutos sólo para lo que de verdad no deba escalar.

## Cosecha 2026-08-19 (el director del guión, `BP_Director_Story`)
174. 🔴 **Los literales `bool` pasados a una función PROPIA TAMBIÉN se pierden** (ya se sabía de los strings, §4 de `dsl.md`): `(CallFunction|Take true)` llegó como `false` y el sensor se "tomaba" siempre con la izquierda. A funciones de **otra** clase (`Class|BPSensorSoul|Take ref true`) el literal llega bien. Salidas: pasarlo por un nodo nativo (`Utilities|Name|MakeLiteralName`, `Math|Boolean|MakeLiteralBool`, `Utilities|String|MakeLiteralString`) o `set_pin_value` después. **Verificar los pines con `get_node_infos` tras escribir.**
175. 🔴 **`Default|CallOnX` / `Default|AssignOnX` con un dispatcher HOMÓNIMO en otra clase resuelve a la clase equivocada.** `OnArrived` existe en `BP_Director_Movement` y en `BP_ProtoSoul_SC`; dentro de ProtoSoul, `CallOnArrived` se cableó al delegado del Movement (`find_node_types` lo lista dos veces) y el compile dijo *"This blueprint (self) is not a BP_Director_Movement_C"*. Fix: `delete_node` + `create_node(type_id, declaring_class={refPath:<clase>_C})`. Regla: antes de usar un dispatcher por DSL, `find_node_types` con ese nombre — si sale repetido, `create_node` con `declaring_class`.
176. 🔴 **`Assign` + `(event Custom|X_Event …)` del mismo nombre en la misma escritura: el Assign se liga a un `X_Event_0` VACÍO y el cuerpo queda en un evento huérfano.** Además cada inspección/reescritura deja `X_Event_1`, `_2`… fantasmas (§51). Fix por cirugía: `connect_pins(OutputDelegate del evento con cuerpo → pin Delegate del AssignDelegate)` y borrar los `_N`. Más limpio: declarar el handler con OTRO nombre (`HandleArrived`) y conectarlo; los eventos fantasma son los `K2Node_CustomEvent` sin ninguna conexión de salida.
177. **`elif` se ANIDA, no se encadena:** `(if A … (elif B … (elif C … (else …))))`. Como hermanos dentro del mismo `if` el parser responde *"(elif) must be the last form inside an (if) or (elif) body"*.
178. 🔴 **Un lote de `write_graph_dsl` donde uno falla y se RELANZA ENTERO duplica los que ya habían salido** (la escritura de un grafo de función no es idempotente: el cuerpo nuevo queda como isla huérfana). Pasó en `BP_Alma_SC` (24 huérfanos). Regla: registrar qué escrituras devolvieron `ok` y reescribir **sólo** las que fallaron; después `clean_orphans.py` (dry → `identical=true` → wet). Nota: un `execute_tool_script` cuyos errores se atrapan igual se **reporta** como error en la respuesta, pero **no** dispara el Undo (canario 44→44).
179. **Llamar una función propia desde el DSL: el primer posicional es `self`.** `(CallFunction|StepAppear DeltaSeconds)` falla con *"Could not connect pin DeltaSeconds to self"*; va `(CallFunction|StepAppear :DT DeltaSeconds)` o `(CallFunction|StepAppear self DeltaSeconds)`. `add_event_dispatcher` lleva `name`, no `dispatcher_name`. `add_variable` de bool es `type_name:"bool"` (no `Boolean`).
180. **Un componente puede attachearse a un componente de OTRO actor** (`AttachComponentToComponent(Body, MotionController del pawn, Snap/Snap/KeepWorld)`): así `BP_Sensor_Soul` pone `Body` en una mano y `Twin` en la otra **sin spawnear** un segundo actor. La escala se escribe con `SetWorldScale3D` cada tick, así no importa que el padre esté a 1,5.
181. 🔴 **`SetActorLocation`/`SetActorRotation`/`CallFunction|<propia>` sobre el PROPIO actor: el primer posicional se mapea al pin `self`.** `(Transformation|SetActorLocation (<vector>))` falla con *"Could not connect pin ReturnValue to self"* — el DSL no salta el target aunque sea opcional. Ir por keyword: `:NewLocation`, `:NewRotation`, `:DT`. ⚠ Contradice el ejemplo de `dsl.md` ("Sobre el propio actor: OMITIR el target") — eso vale para GETTERS puros (`GetActorLocation`); en los SETTERS con más de un pin de datos, keyword.
182. 🔴🔴 **El envelope follower de un `AudioComponent` se congela EN EL PLAY: bindear `OnAudioSingleEnvelopeValue` después de `SpawnSound2D` = callbacks que NUNCA llegan, sin error.** El ActiveSound copia `bUpdateSingleEnvelopeValue` cuando el sonido arranca; `SpawnSound2D` auto-reproduce, así que el `Assign` posterior bindea un delegate que el mixer jamás va a llamar. Receta que anda (verificada por control positivo en log): **`CreateSound2D` (no reproduce; `bAutoDestroy=true`) → set attack/release → `Assign` del delegate → `Play`**. Y el evento tipado del Assign sale de **`create_node`**, no del DSL (§176: el DSL lo genera SIN los parámetros — el bind conecta y el callback llega vacío). Extra: `SetEnvelopeFollowerAttackTime` es un SETTER de propiedad — primer posicional = VALOR, target segundo.
183. 🔴🔴 **En el Construction Script, leer una propiedad de un COMPONENTE devuelve el valor del CDO, no el de la instancia.** Medido el 2026-08-21: `GetCylinderArcAngle()` sobre el `WidgetComponent` devolvió **180** (el del archetype) en una instancia cuyo valor real es **30** — el vidrio procedural salió con radio 611 en vez de 3667. Los overrides por-instancia de componentes se aplican en un momento distinto al de la ejecución del CS, así que **el CS no puede confiar en ellos**. ✅ **Patrón correcto: la propiedad se declara como VARIABLE del actor (instance-editable) y el CS se la EMPUJA al componente** (`SetCylinderArcAngle(Panel, ArcAngle)`). Así hay una sola fuente de verdad, el dato se ve en el panel de detalles junto al resto, y de paso es imposible que componente y geometría derivada se desincronicen. Es primo de §146/§164: **lo de la instancia y lo del CDO no son lo mismo, y el CS vive del lado del CDO.**
184. 🎨 **Un material que NO obedece al fundido global se delata como un "glitch de color" al cargar la sala.** Beltrán vio un destello de color al entrar a Attracting: era el vidrio nuevo de las instrucciones (`M_InstrGlass`), que tenía su propio emisivo y **no leía `MPC_Room.RoomLight`** — así que aparecía a pleno mientras el resto del mundo estaba en negro. ✅ **Regla: TODO material que viva dentro de un sublevel de sala debe multiplicar su emisivo (y su opacidad, si es translúcido) por el escalar `RoomLight` de la colección.** Es una expresión `CollectionParameter` y dos `Multiply`. Sin eso, cualquier material nuevo reintroduce el destello del primer frame que el sistema de fundido existe para evitar.
185. 🔴🔴🔴 **EL BUG HISTÓRICO DE "el material animado se va glitcheando a lo largo de la experiencia": es el nodo `Time` SIN período, en precisión por defecto.** Diagnosticado el 2026-08-21 con el reporte de Beltrán (*"al final, cuando mi ameba está al frente, se ve pixelada y el material se mueve a muy bajos frames — sólo el material"*). Medido: `M_ProtoSoul` y `M_Alma` tenían **`floatPrecisionMode = MFPM_Default`** (= fp16 en el renderer móvil) y **`Time.period = 0`** (el tiempo crece sin límite). Después de ~15 min, `Time` es tan grande que la mantisa ya no tiene bits para la parte fraccionaria: los senos avanzan **a saltos discretos** (parece bajo framerate aunque el juego corra a 72) y los degradados se **cuantizan** (parece pixelado). **Sólo afecta al material** — de ahí que el resto se vea fluido.
    ✅ **El arreglo, en TODO material animado del proyecto**: `floatPrecisionMode = MFPM_Full_MaterialExpressionOnly` **y** en cada nodo `Time`: `bOverride_Period = true`, `period = 300`. Con el período el tiempo hace wrap cada 5 min y nunca crece. `M_SoulRibbon_SC` ya lo tenía (por eso los anillos nunca se degradaron) — era la pista que estuvo ahí todo el tiempo.
    👉 **Checklist para cualquier material nuevo con `Time`: precisión Full + período.** Aplicado a `M_ProtoSoul`, `M_Alma`, `M_LightShaft` y `M_InstrGlass`.
186. 🔊 **Un `SoundWave` con `loadingBehavior = Inherited` se carga BAJO DEMANDA en Android → hitch al reproducirlo.** Síntoma de Beltrán: *"cortes cada vez que aparecía Alma al entrar a las salas"* — el corte no era la aparición, era el **VO que empezaba en ese mismo instante**. ✅ Fix: `loadingBehavior = ForceInline` en los clips que suenan en momentos sensibles (los 32 VO + los 7 SFX cortos de la obra). Quedan residentes en memoria (~3 MB) y no tocan disco al sonar. Para música larga sí conviene el streaming.
187. ✨ **El destello de "un frame con otro material/color" al cargar una sala es el FALLBACK del PSO precaching.** Cuando un material entra en escena y su PSO todavía se está compilando, UE dibuja ese frame con el material por defecto. ✅ El arreglo es que el proxy **espere** a tener su PSO listo: el objeto aparece unos ms más tarde, pero sin destello. Es el complemento obligatorio de `r.PSOPrecaching=1`.
🔴 **Corrección 2026-08-21: `r.PSOPrecache.ProxyCreationWhenPSOReady` está DEPRECADO en 5.8** (lo avisa el propio log del device). El reemplazo es **`r.PSOPrecache.ProxyCreationStrategy=1`**, que ya es el default pero conviene dejar explícito.

188. 🔴 **`remove_function_graph` NO libera el nombre hasta compilar — y el `add` siguiente devuelve `<Nombre>_0` sin avisar.** Pagado el 2026-08-21 rehaciendo `DebugBoot`: borrar el grafo y volver a crearlo en la misma tanda dio `DebugBoot_0`. **Por qué es peligroso y no sólo feo:** si a esa función la llama un `SetTimerByFunctionName`, la llamada es **por string**, así que no hay error de compilación — el timer simplemente **no dispara nunca** y el sistema queda muerto en silencio. ✅ Secuencia correcta: `remove_function_graph` → **`compile_blueprint`** → `add_function_graph`. Y verificar el `refPath` que devuelve el `add`.

189. 🔎 **El `read_graph_dsl` renombra llamadas a la CLASE EQUIVOCADA cuando dos clases comparten el nombre de la función — pero el grafo está bien.** Lo escrito como `Class|BPSensorSoul|Appear` y `Class|BPProtoSoulSC|MoveTo` vuelve del read como `Class|BPAlmaSC|Appear` / `Class|BPAlmaSC|MoveTo`; una llamada a la función propia `Next` vuelve como `Media|MediaPlayer|Next`. **Es del lector, no del grafo.** ✅ **El discriminante barato: compilar.** Si el nodo fuera realmente de la otra clase, pasarle esa referencia daria un error de tipo (*"self is not a X_C"*) — que es exactamente cómo se cazó §175. Compila limpio ⇒ el nodo apunta bien. **No "arreglar" lo que el read muestra raro sin comprobar antes que compile mal**: en este proyecto ya había un `OnChosenBody` verificado en obra que el read mostraba con `Media|MediaPlayer|Next`.

190. 🧪 **Al medir un sistema que sigue corriendo, la lectura tardía miente igual que la temprana.** Verificando el salto de debug a la sala 3, las propiedades leídas dieron `Room=4`, `RoomIndex=4`, `LegIndex=7` y la sala cargada era Attracting, no Loving — todo coherente con un off-by-one **que no existía**: la obra simplemente había seguido sola durante los ~50 s que tardé en encadenar consultas. ✅ Antes de declarar un bug por un valor "corrido", **mirar el log CON TIMESTAMPS y ubicar la lectura en la línea de tiempo**. Es la cara opuesta de [[verificar-estado-estable-no-spawn]] (medir en el frame del spawn): los dos errores son el mismo, **medir fuera de la ventana en que el valor significa lo que uno cree**.

191. ⏱️ **Para enganchar algo al instante dramático de una transición, poll de la FASE, no un delay.** El salto de debug arrancaba el guión con un delay fijo y caía 2,4 s después de que la sala ya estaba encendida. Y el delay no puede acertar: **la misma carga midió 0,58 s y 1,67 s en dos corridas seguidas** (casi 3×), porque depende del streaming. ✅ Reagendarse cada 0,1 s hasta que `BP_Director_Rooms.Phase >= 3` (= empieza a subir la luz desde el negro) entra siempre en el mismo momento de la obra, sin importar lo que tarde el disco. Regla general del proyecto: **los delays fijos sólo sirven para esperar algo cuya duracion uno controla.**

192. 🔁 **Una función de "animar" con UN SOLO slot de estado no se puede llamar en bucle: la segunda llamada pisa a la primera y la primera queda a medio camino PARA SIEMPRE.** `BP_ProtoSoul_SC.DrawRing(Index)` escribe `DrawIndex = Index` y `RingReveal[Index] = 0`, y el `StepRings` del Tick anima **solo** el anillo que este en `DrawIndex`. Sembrar dos anillos en el mismo frame dejaba el primero en `Reveal = 0` = **invisible**, y el sintoma que reporto Beltran fue justamente "veo uno y el otro no". ✅ **Antes de llamar en bucle a algo que "reproduce", mirar si su estado es un slot unico o una lista.** Si es un slot, hace falta un setter aparte que escriba el estado FINAL (aca `SeedRings(Count)`: `RingReveal[i] = 1.05` + push del material, sin tocar `DrawIndex`). Vale para reveals, timelines, tweens y cualquier `Current*` que el Tick consuma.

193. 🚚 **Una herramienta de debug que TELETRANSPORTA es, sin quererlo, un test de estres de las suposiciones temporales del proyecto.** El salto por sala destapo en el acto un bug viejo de [[BP_Door_SC]]: `BeginPlay` agenda la creacion de los materiales dinamicos a 0,3 s, pero el `Tick` los lee desde el frame 1. En la obra normal jamas se veia, porque a la puerta se llega **caminando** bastante despues; con el salto el pawn nace pegado a la puerta y salta la catarata de `Accessed None`. ✅ **Corolario util: cuando se agregue un salto/teleport, esperar que aparezcan errores en sitios no relacionados — y tratarlos como bugs reales recien expuestos, no como daño de la herramienta.** El patron a auditar es siempre el mismo: `BeginPlay → SetTimer(Init, X)` conviviendo con un `Tick` que usa lo que ese Init crea.

194. 🎯 **En VR, COPIAR la transform de un ancla en el Tick deja el objeto UN FRAME ATRAS de la cabeza — y se percibe como "lazy follow" aunque el codigo sea un snap duro.** Diagnosticado en `BP_ProtoSoul_SC`: `AnchorStep` hacia `SetActorLocation(GetActorLocation(TargetRef))`, sin ninguna interpolacion, y Beltran seguia viendo rezago con la ameba anclada a su cabeza. La pista que descarta la interpolacion: **un snap no puede producir un rezago suave; solo el orden de ejecucion puede.** El HMD actualiza su pose en un *late update*, al final del frame, DESPUES de los Ticks de Blueprint: lo attacheado hereda esa pose, lo que la copio se quedo con la del frame anterior. ✅ **Regla: todo lo que deba ir head-locked se ATTACHEA, no se copia.** Es lo mismo que ya hacian `BP_SoulHUD` (attach directo a la camara) y la vineta de `BP_Director_Movement`. Reglas: `SnapToTarget` en location/rotation y **`KeepWorld` en escala** si el objeto ya gobierna su tamano por otra via (si no, la escala del padre se multiplica con la propia). ⚠ Y la guarda del "ya estoy attacheado" tiene que comparar contra el **destino vigente**, no contra "tengo padre": si una funcion cambia el destino sin pasar por el camino que suelta el ancla, el objeto queda pegado al anterior.

195. 🧮 **Antes de declarar un bug por dos posiciones que no coinciden, verificar contra QUE deberian coincidir.** Verificando el anclaje, la ameba y el punto de la cara daban 4 m de diferencia — parecia que el attach no funcionaba. No habia bug: el guion ya habia mandado la ameba a **otro** punto (`soul_pick_3`), asi que la comparacion era contra el ancla equivocada. Leyendo su `TargetRef` **vigente** y comparando contra ese, la coincidencia fue **exacta hasta el ultimo decimal**. ✅ Cuando el objetivo de un seguidor es una variable, **leer la variable primero y comparar contra lo que apunta**, nunca contra lo que uno supone que apunta. Hermano de §190: los dos errores son medir fuera de la ventana en que el dato significa lo que uno cree.

196. 🔴🔴 **CORRECCION de §194 — attachearse al ancla NO alcanza si el ancla no esta attacheada a la cabeza.** Segunda pasada del mismo problema: tras attachear la ameba a `TP_soul_face`, Beltran seguia viendo movimiento en el visor (*"debe quedar attached fijo fijo fijo a la cabeza"*). **La medicion que lo resolvio en una sola llamada:** `SceneTools.find_actors(root=<pawn>)` devuelve la jerarquia de attachment colgada del pawn. Salieron `BP_Director_Movement` (por su vineta) y `BP_FaceAnchor_SC`, **pero NO el TargetPoint `soul_face`** — o sea que ese punto nunca estuvo pegado a la cabeza y algo lo movia por otra via, con su propio retraso, que la ameba heredaba.
✅ **Regla dura: para head-lock, attachear a la `CameraComponent` DEL PAWN, no a un punto intermedio.** La camara *es*, por definicion, la pose del HMD ya late-updated; cualquier eslabon intermedio hay que demostrarlo. Receta que conserva la pose autoral: **(1)** `SetActorLocation/Rotation` a la del TargetPoint (la pose que diseño el autor) → **(2)** `AttachActorToComponent(camera, KeepWorld/KeepWorld/KeepWorld)`, que congela ese offset y lo vuelve rigido. `KeepWorld` en los tres, no `SnapToTarget`: con Snap el objeto se iria al centro del ojo.
⚠ **Y hay que sacar la escritura per-frame de la transform**: si el Tick sigue haciendo `SetActorLocation(punto.location)`, cada frame re-referencia el objeto contra el punto rezagado y **reintroduce el lag aunque el attach sea correcto.** En `AnchorStep` quedaron solo el tamaño y la llamada al anclaje.
🔬 **La prueba de que un head-lock esta bien hecho es perceptual y contraintuitiva:** si esta rigido, al vibrar la cabeza el objeto se ve **quieto** (los ojos vibran con el). Si se ve moverse cuando la cabeza vibra, **no** esta rigido — no importa cuanto diga el codigo que hace snap.

197. 🪟 **Para que algo se comporte como el HUD de OVR Metrics (que las manos NO lo tapen) alcanza con `Disable Depth Test` del material — y SI corre en el renderer movil.** Pedido de Beltran (2026-08-21): *"el grafico de OVR esta superpuesto a lo que veo... mis manos nunca quedan por delante"*. [SRC] `MobileBasePass.cpp:647` → `if (Material.ShouldDisableDepthTest())` aplica `TStaticDepthStencilState<false, CF_Always>`: test de profundidad en **Always** y sin escribir profundidad ⇒ dibuja siempre, sin importar que haya delante. **Solo aplica a materiales translucidos/aditivos.**
🔴 **`DisableDepthTest` NO se puede sobrescribir por INSTANCIA de material** — no esta en `MaterialInstanceBasePropertyOverrides.h` (que solo cubre OpacityMaskClipValue, BlendMode, ShadingModel, DitheredLODTransition, CastDynamicShadowAsMasked, TwoSided, IsThinSurface, OutputTranslucentVelocity, HasPixelAnimation, Tessellation, Displacement*, MaxWorldPositionOffsetDisplacement, CompatibleWithLumenCardSharing). Si hace falta encenderlo **solo a veces**, la unica via es **DUPLICAR el material maestro** y cambiarselo al componente en runtime.
⚠ **Al cambiar el material se PIERDE el MID y sus parametros**: hay que re-empujar los que no reponga nadie (aca `CoreColor`, que solo lo escribe `Configure`; `RimColor`/`EdgeIntensity`/`FresnelPower` los repone `PushHoverLook` en cada tick). Verificar leyendo `vectorParameterValues` del MID nuevo.
⚠ **Confort VR:** un objeto dibujado por encima pero a una distancia estereo real genera **conflicto de profundidad** (los ojos convergen en la mano a 20 cm y la ameba a 30 cm la pinta encima). Con una forma chica y difusa se tolera bien —es lo que hace cualquier HUD— pero se juzga en visor.
🔴 **Lo que NO se puede imitar barato: la NITIDEZ del compositor.** OVR Metrics es una capa del compositor (se dibuja despues del frame de la app, a su propia resolucion, reproyectada aparte). La `StereoLayer` de UE toma una **textura** sobre quad/cilindro, **no geometria 3D**: meter una malla animada ahi exige renderizarla a un RenderTarget con un SceneCapture — un render extra de escena por frame en Quest — y encima queda **plana** (se pierde el estereo y el WPO se lee como calcomania). Para un objeto organico que debe sentirse presente, mal negocio.

198. 🎨 **Cambiar el material de un componente TIRA el MID y con el TODOS los parametros autorados por instancia.** Al swappear `M_ProtoSoul` por su variante HUD, la ameba perdio los 22 parametros que su Construction Script empuja (deformacion, opacidades, gradiente, borde, flotar…) y quedo con los defaults del maestro. Beltran lo vio al instante: *"debe tomar los parametros que ya tienen mis amebas en el editor"*.
✅ **Regla: si se cambia un material en runtime, hay que RE-EMPUJAR todo lo que lo definia** — no alcanza con el parametro que uno recuerda (el color). La lista canonica suele estar en el **Construction Script**; conviene leerla entera y replicarla.
🔎 **El que se escapa siempre es el parametro que NO esta en el Construction Script.** Aca era `FloatScale`, que lo empuja `ApplyRingScale` **solo cuando el valor cambia** (guarda `RingScaleLast`): tras el swap no se reponia nunca. **Buscar tambien los push condicionales o cacheados**, no solo el bloque de inicializacion — son invisibles en una lectura rapida y su sintoma (el flotar a escala equivocada) no se parece a "perdi un material".
🔧 Empujar con **`Set{Scalar,Color}ParameterValueOnMaterials`** (target = el COMPONENTE, crea y reusa el MID internamente): asi no hay que recrear ni re-cachear la variable `MID`, y se esquiva la colision de nombres del §142.

199. 📡 **UE 5.8 NO tiene encoder de video para Android: no se puede mandar video desde el Quest sin escribir el backend a mano.** Verificado en el motor (2026-08-21), no asumido: los backends de codec que trae son `NVCodecs` (NVENC, Win64/Linux), `AMFCodecs` (AMD), `WMFCodecs` (Windows), `VTCodecs` (Apple) y `LibVpxCodecs` (VP8/VP9 **por software**). `AVCodecs/AVCodecsCore` trae el framework y las *configuraciones* de H264/H265/VP8/VP9/AV1 pero **ningun backend de Android**: `grep MediaCodec` sobre todo el plugin da **cero**. En Quest la unica via seria VP8 por software en la CPU.
⚠️ **El falso positivo que hay que esquivar:** `PixelStreaming2.uplugin` **si lista `Android`** en su `PlatformAllowList` (el `PixelStreaming` v1 es solo Win64/Linux/Mac). Eso significa que el modulo **compila** en Android, **no** que exista con que codificar. Comprobar siempre el backend, no la lista de plataformas del plugin.
👉 **Por eso el cast de Meta existe y funciona**: usa el encoder de hardware del sistema, que Unreal no expone. Si hace falta la imagen literal del visor, la via es `adb`/`scrcpy` sobre WiFi, **fuera de Unreal**.
✅ **Para un espectador en PC, la arquitectura correcta es transmitir ESTADO, no pixeles** (pose de cabeza/manos + indice del guion) y re-renderizar en la PC con el mismo proyecto. Detalle y limites en `docs/PENDIENTE-espectador-pc.md`. Bonus: una camara extra a 1080p seria ademas un render de escena COMPLETO adicional sobre una app que ya es fill-rate bound.

200. 🪟 **Un `WidgetComponent` "por encima de todo" = material propio en `overrideMaterials[0]`, y sus parámetros NO son libres.** El truco de `Disable Depth Test` (§197) no se puede aplicar por instancia de material, así que hay que darle al componente un maestro propio. 🔴 **`UWidgetComponent::UpdateMaterialInstanceParameters` escribe tres parámetros con nombre fijo** sobre el MID que crea de `GetMaterial(0)`: **`SlateUI`** (Texture2D = el render target del widget), **`TintColorAndOpacity`** (Vector) y **`OpacityFromTexture`** (Scalar). Si el material no los expone con ESOS nombres, el widget sale en blanco o no sale. Réplica mínima del passthrough del motor: `Emissive = SlateUI.RGB * Tint.RGB`, `Opacity = lerp(1, SlateUI.A, OpacityFromTexture) * Tint.A`, con `BLEND_Translucent` + `MSM_Unlit` + `twoSided` + `bDisableDepthTest`. Se asigna con `ObjectTools.set_properties` → `{"overrideMaterials":[{"refPath":"..."}]}` (no hay tool de material para componentes). Caso real: `M_HudWidget_SC` de [[BP_SoulHUD_SC]].

201. 🔴🔴 **`PreConstruct` de un UserWidget NO corre en el preview de editor de un `WidgetComponent` — sí corre en PIE.** Costó media hora de diagnóstico falso con el gráfico EEG de [[BP_SoulHUD_SC]]: la onda no aparecía en el viewport y la hipótesis obvia ("`DrawLines` no dibuja / el override `OnPaint` no quedó bien") era **falsa**. Medido con `PrintString`: en el editor el seed de `PreConstruct` **nunca se ejecuta** ⇒ el buffer de puntos está vacío ⇒ `OnPaint` dibuja una polilínea de cero puntos. En PIE el mismo código imprime `seed puntos=48` y la onda dibuja. 👉 **Si algo del widget tiene que verse en el editor, sembralo desde el Construction Script del ACTOR** (`GetUserWidgetObject` + cast + llamar a la función del widget), no desde `PreConstruct`.

⚠ **CORRECCIÓN (2026-08-24, misma jornada, medido después):** el enunciado de arriba es demasiado fuerte. Lo que está comprobado es que **la ONDA no se dibuja en el preview del nivel** y que **el `PrintString` del seed no apareció en el log del editor**. Pero un `Image` común del mismo widget **sí** se ve en el preview del nivel, así que el widget se construye. La explicación que encaja con todo es que **el `OnPaint` de Blueprint se saltea en design time** (`SObjectWidget::OnPaint` no llama a `NativePaint` cuando el widget es design-time), no que `PreConstruct` no corra.
⚠ Y un corolario propio: **`Widget|SetRenderOpacity` llamado desde `PreConstruct` NO se sostiene** — se probó encender/apagar un marco según `IsDesignTime` y el marco quedó visible en PIE con las DOS órdenes del `select`, o sea que el valor puesto ahí lo pisa el layout posterior. Para prender/apagar algo del widget, usar la propiedad del Designer, no `PreConstruct`.
✅ En cualquier caso la receta práctica no cambia: **lo que tenga que verse en el editor se siembra desde el Construction Script del ACTOR**.

202. 📸 **Para ver PÍXELES de PIE, `CaptureViewport` no sirve: usá `EditorAppToolset.CaptureEditorImage()`.** `CaptureViewport` captura el viewport del **editor** aunque PIE esté corriendo (ya estaba anotado, se volvió a pagar el 2026-08-24): devuelve el mundo de edición, con los actores en su pose autoral y no en la de juego. `CaptureEditorImage()` saca **la ventana entera del editor**, con el PIE adentro — es la única forma de verificar a ojo qué renderiza el juego sin pedirle al usuario que mire. Bonus: el resultado viene en base64 y suele pasarse del límite de tokens, así que **volcalo a PNG desde el archivo persistido** (`re.search(r'[A-Za-z0-9+/=]{5000,}')` + `base64.b64decode`) y leelo como imagen.

203. 🌀 **`WidgetComponent` con `GeometryMode = Cylinder` NO dibuja si el componente está a escala chica.** Medido el 2026-08-24 aislando una variable por vez sobre la misma instancia y el mismo widget (HUD de [[BP_SoulHUD_SC]]): `Plane` + escala 0.04 → **dibuja**; `Cylinder` + escala 0.04 **con** material propio → **nada**; `Cylinder` + escala 0.04 **sin** material propio (el del motor) → **nada**; `Cylinder` + **escala 1** → **dibuja**. O sea: el cilindro anda, lo que lo rompe es la escala. El motor deriva el radio del arco de `DrawSize` y `CylinderArcAngle` (R = ancho / arco en radianes) y a escala chica la malla degenera; se ve también en los bounds, que en modo `Cylinder` reportan ~2,5 m para un widget de 40 cm. ⚠ El corolario que mata la idea para un HUD: a escala 1 (1 px = 1 cm) un radio de 30 cm exige un `DrawSize` de ~40 px de ancho — resolución inservible. **Cilindro y widget cerca del ojo son incompatibles con este componente.**

204. 🔴🔴 **Agregar un componente a un Blueprint que YA tiene instancias colocadas deja la instancia con los defaults del MOTOR** — y `set_properties` sobre esa instancia **devuelve `true` sin aplicar nada**. Caso real: se agregó un `WidgetComponent` al BP, se configuró el CDO entero (widgetClass, drawSize, escala, material) y la instancia del nivel seguía con `widgetClass = None`, `drawSize 500×500`, escala 1. El síntoma se leyó como *"el geometry cilíndrico no renderiza"* y no era eso: **la instancia no tenía widget**. Es la misma familia que "lo de la INSTANCIA le gana al Blueprint". ✅ **La salida limpia es borrar la instancia y volver a colocarla desde el asset** (se reconstruye del CDO). Y verificar SIEMPRE con `get_properties` sobre el componente **de la instancia**, no del CDO.
⚠ Bonus de la misma jornada: **en una instancia, `set_properties` con varias propiedades a la vez aplica sólo la PRIMERA** (`geometryMode` entró, `relativeLocation` no). Mandarlas en llamadas separadas y releer.

205. 📐 **Para ubicar algo dibujado por `OnPaint` respecto de un widget del lienzo, leé el SLOT, no la geometría cacheada — y anclá el widget arriba-izquierda.** Tres intentos sobre el gráfico EEG de [[BP_SoulHUD_SC]], con el síntoma siempre igual (el trazo se dibujaba en el rincón superior izquierdo del lienzo, en el Designer **y** en Play):
  1. ❌ **Geometría cacheada** (`GetCachedGeometry` del marco y de la ventana + `LocalToAbsolute`/`AbsoluteToLocal`): el top-left sale **(0,0)** porque la geometría todavía no está resuelta cuando corre la función. El tamaño sí sale bien, así que el guard "si el ancho > 4" **no atrapa el error** — es la trampa.
  2. ❌ **Slot + centro del lienzo** (`SlotAsCanvasSlot` → `GetPosition`, sumando `CanvasSize/2` porque el widget estaba anclado al centro): correcto sólo mientras la variable `CanvasSize` coincida con el `DrawSize` real del `WidgetComponent`. En cuanto el `DrawSize` cambió (1000×400 → 1920×1080) la onda se fue de nuevo al rincón. **Toda constante que duplique un dato del componente es una bomba de tiempo.**
  3. ✅ **Slot + anclaje arriba-izquierda** (anchors `(0,0)`–`(0,0)`, alignment `(0,0)`): ahí `GetPosition` **ya es** la coordenada dentro del canvas y `GetSize` el tamaño, sin necesidad de saber cuánto mide el lienzo. `RightX = pos.x + size.x − Pad`, `BaseY = pos.y + size.y − Pad`. Independiente del `DrawSize`.
⚠ Costo del anclaje a (0,0): al cambiar el `DrawSize` los elementos **no se recentran**, mantienen su posición absoluta en píxeles. Es predecible, pero hay que decidirlo a conciencia.

206. 🎯 **`AttachActorToComponent` con `SnapToTarget` DESCARTA la pose que autoraste en el world — y es justo lo que rompe "lo ajusto desde el viewport".** Pasó con [[BP_SoulHUD_SC]]: Beltrán movía el actor en el nivel para acomodar el HUD frente a la cara y en Play no cambiaba nada, porque el attach a la cámara del pawn con `SnapToTarget` pone la relativa en identidad y se lleva puesto el offset. ✅ **La receta para que el world sea el control:** antes de attachear, medir la pose del actor **relativa a un ancla del nivel** que represente la cabeza (acá `BP_FaceAnchor_SC`, el doble del HMD) con `InverseTransformLocation` / `InverseTransformRotation` sobre la transform del ancla; attachear con `SnapToTarget`; y **acto seguido** aplicar ese offset con `SetActorRelativeLocation` / `SetActorRelativeRotation`.
⚠ Corolario: **el componente que dibuja tiene que quedar en (0,0,0)**. Si conserva su propio offset, se suma al del world y quedan dos controles peleando por la misma pose — el síntoma es "lo muevo un poco y se va al doble".

⚠ **Segunda mitad de la lección (pagada el mismo día): el ancla contra la que medís puede NO estar en su pose de editor cuando corre el juego.** `BP_FaceAnchor_SC` cuelga del pawn, así que en Play se mueve con él: medir el offset en `BeginPlay` daba `Z = 104,458`, que es la **Z del mundo del propio actor** (el ancla aportaba 0). ✅ **Hornear el offset en el CONSTRUCTION SCRIPT**, donde los dos actores sí están en su pose autoral, y en runtime sólo aplicarlo. Con eso el número del editor `(34,9 · 0 · −15,5)` es literalmente el que llega a PIE.
🔎 **Y el método que lo resolvió en un round:** un `PrintString` del offset. Dos hipótesis visuales ("no se ve") no distinguían nada; el número sí — ver `workflow.md` sobre medir en vez de teorizar.
207. 🖼️ **El CONTORNO de un brush `RoundedBox` no respeta `SetRenderOpacity` — ni el del widget ni el del padre.** Costó dos intentos con el HUD de [[BP_SoulHUD_SC]]: el marco del `GraphArea` seguía visible (una línea fina de esquinas redondeadas) con la opacidad en 0 puesta primero sobre el propio `Image` y después sobre el `CanvasPanel` raíz. El relleno del brush sí se funde; el contorno se dibuja por otro camino, con su `OutlineSettings.Color`, y sobrevive. (Existe `OutlineSettings.bUseBrushTransparency`, pero engancha el contorno al **tinte** del brush, no a la opacidad de render — y si el tinte está en alfa 0 para no tener fondo, apagás también el contorno.)
✅ **La salida limpia es `SetVisibility(Hidden)`**, que no admite discusión. Y si el elemento es una **ayuda de autoría** (un marco para poder arrastrar algo en el Designer), conviene apagarlo desde una función que **solo corra en runtime**: así sigue visible donde hace falta para autorar y nunca aparece en el juego. `Hidden` conserva el layout; `Collapsed` no.
💡 Regla general que se llevó la jornada: **fundir el árbol desde el padre** (`SetRenderOpacity` sobre el `CanvasPanel` raíz) en vez de elemento por elemento — se hereda multiplicativamente, no hay que acordarse de agregar cada widget nuevo a la lista, y es un set por frame en vez de N. Las excepciones son las dos de arriba: lo que dibuja `OnPaint` y los contornos de `RoundedBox`.

208. 🎨 **`(* LinearColor escalar)` en el DSL multiplica el RGB pero NO el alfa — el float se promueve a `(v,v,v,1)`.** O sea que "fundir un color multiplicándolo por 0" no lo vuelve transparente: lo vuelve **negro opaco**. Pasó fundiendo el trazo del EEG de [[BP_SoulHUD_SC]]: con el factor en 0 aparecía una línea negra bien visible. Si hace falta fundir un color, hay que armarlo con `MakeLinearColor` y multiplicar el alfa aparte — o, casi siempre mejor, **no dibujar el elemento** (en este caso, no generar los puntos).
⚠ Y el bug ten\u00eda una segunda mitad que explicaba *dónde* aparecía: cuando un guard del estilo `if (ancho > X)` no entra, las variables de geometría **se quedan con los defaults del CDO**, que suelen mapear a una esquina del lienzo. Un guard que "no hace nada" no deja el dibujo quieto: lo deja en la última geometría válida, que al arrancar es la de fábrica.

209. 🔢 **Antes de insertar un paso nuevo en un director por pasos (`Sub`), mirá dónde ARRANCA el siguiente bloque.** Al agregar el quinto anillo de [[BP_ProtoSoul_SC]] la salida obvia era poner `RingIndex[5] = 4` para que Surrounding dibujara su anillo por el camino normal. **Habría roto el final:** ese `−1` es lo que enruta la última sala a `BeginEnding`, y **`RunEnding` empieza en el sub 6** — pasar por el camino del anillo consume un sub y el bloque del final habría arrancado en el 7, sin entrar por ninguna rama. ✅ La salida fue **no tocar la numeración**: meter el `DrawRing` dentro de `BeginEnding` y retrasar el cierre de la sala con un timer, para que el anillo tenga su tiempo antes del fundido.
⚠ Y el número que hay que mirar es el del FUNDIDO: `FadeOutTime` era 1,2 s y el anillo tarda 2,5 s — sin el retraso el anillo se cortaba a la mitad y parecía un bug del anillo, no del timing.
🔴 **Corolario de la §209, pagado acto seguido: al sumar un elemento a una serie, hay que extender TODOS los arrays paralelos, no sólo el obvio.** El quinto anillo se creó con su componente, su transform y su color (`RingColors` de 5)… y salía **invisible**. Faltaba **`RingReveal`**, el array de progreso que `PushRingMat` lee para el parámetro `Reveal` del material: con 4 entradas, el índice 4 cae fuera de rango y devuelve **0**, o sea "no dibujado". El síntoma engaña — parece que el componente no se creó, cuando en realidad está entero pero con opacidad 0.
👉 Regla: ante "el elemento nuevo no se ve", listá **todos** los arrays indexados por ese mismo índice y verificá su longitud, antes de sospechar de la geometría.

210. 🔎 **`get_node_type_pins` INSTANCIA un nodo real en el grafo para inspeccionarlo — y lo deja ahí.** El `refPath` que devuelve (`...EventGraph.K2Node_CallFunction_5`) no es un ejemplo: es un nodo suelto recién creado en TU grafo. Hay que `delete_node` de ese refPath después de leer los pins, o queda un nodo huérfano sin conectar (2026-08-24, mordió en `BP_Sensor_Soul`).

211. 🏷️ **Dos type_ids que el `read` imprime y el `write` rechaza (2026-08-24):** `Utilities|Name|Equal(Name)` no existe como escribible — para comparar Names en el DSL va el operador **`==`** (promotable, resuelve Name==Name bien; la advertencia de "== no sirve para strings" es del tipo String, no de Name). Y **`switch int` nace con cases 0-2**: un `(:4 ...)` falla con *"Unknown exec output 4"* — o `add_node_pin` por cirugía, o directamente `if/elif` con `==`, que además acepta cualquier valor.

212. 🔴🔴 **Variables instance-editable NUEVAS sobre un BP con instancia YA COLOCADA: la instancia nace con TODO en CERO — los 25 knobs a la vez.** Recaída medida de [[instance-editable-nace-en-cero]] (2026-08-24, `BP_Sensor_Soul`): los defaults se escribieron en el CDO, verificados por `get_properties`… y la instancia colocada en `L_SoulCharger` tenía los 25 en 0. Síntoma delator: la calibración de respiración "calibró" en 17 ms (`CalHold=0`). **Receta:** tras agregar knobs a un BP colocado → `get_properties` de la INSTANCIA (no del CDO) → `set_properties` con los valores → guardar el **NIVEL** (`save_actor` falla con "not an external actor"; va `save_assets` del mapa). Alternativa: NO marcar instance-editable lo que no necesite ajuste por instancia (así heredan del CDO, como `MechTimeout` del director, verificado en la misma sesión).

213. 🔴🔴 **Un `(bind _x (Get<Var>))` de un getter PURO no es un SNAPSHOT — se evalúa cuando se CONSUME.** El patrón de flanco `bind _was (GetWasActive)` → `SetWasActive _active` → `(if (xor _active _was) ...)` compila perfecto y **nunca dispara**: el getter bindeado es un nodo puro que se evalúa recién cuando el `xor` corre, o sea DESPUÉS del Set — compara el valor consigo mismo. Medido 2026-08-24 en `BP_BreathOrb_SC` (el log de flanco no salía) y el mismo bug estaba en el apagado del háptico de `BP_Sensor_Soul` (el zumbido habría quedado prendido para siempre al salir del umbral). ✅ **El patrón correcto: actualizar el estado SOLO dentro del flanco** — `(if (xor _active (GetWas)) (SetWas _active) (…efectos del flanco…))` — así el Get se consume antes de cualquier Set. Regla general: si un valor se lee y se escribe en la misma función, ordená los consumidores ANTES del Set o mové el Set adentro de la rama; un `bind` NO congela nada.

214. 🔴🔴 **Bordes con diente de sierra y "línea negra" en un `WidgetComponent` = `BlendMode` en `Masked`.** Es el default de fábrica y da **alfa de 1 bit**: no hay antialiasing posible en el borde, los píxeles semi-transparentes se recortan y por el corte se ve el fondo oscuro del render target — se lee como un contorno negro finito y escalonado, aunque el brush no tenga ningún outline. **Subir `DrawSize` NO lo arregla** (más resolución = escalones más chicos, pero siguen siendo duros); es exactamente el síntoma que reportó Beltrán en `BP_StageIntro_SC` después de haber duplicado la resolución él mismo. ✅ **Fix: `BlendMode = Transparent`** en el componente (CDO **y** en la instancia colocada, que puede tener override propio). Es la 2ª vez que este proyecto se lo come: en [[BP_InstructionsPanel_SC]] el mismo `Masked` hacía que el alfa 0,55 del fondo se dibujara opaco, y ahí se resolvió sacando el fondo del widget a geometría. 👉 **Regla: cualquier `WidgetComponent` de esta obra que tenga bordes redondeados, transparencias o fundidos va en `Transparent`, no en `Masked`.**
⚠ Y el hallazgo lateral que salió al arreglarlo: **la instancia colocada tenía `DrawSize` y `relativeScale3D` propios** (1920×1920 · 0,06, autorados por Beltrán) distintos de los del CDO (1040×1240 · 0,05). Antes de "corregir" la resolución de un widget, **leer la INSTANCIA**: el CDO puede no ser lo que corre.

215. ⏱️ **Una ventana de animación corta NO se verifica muestreando propiedades por MCP — se verifica LOGUEANDO desde adentro del grafo.** Para comprobar que la salida por opacidad de `WBP_StageIntro_SC` hacía lo pedido había que ver 0,6 s de fundido que empiezan ~18 s después del disparo. **Cuatro intentos de poll con `get_properties` en bucle volvieron vacíos**: cada llamada MCP cuesta ~0,3 s de ida y vuelta, así que el muestreo es grueso, irregular y cae fácil fuera de la ventana; además cualquier excepción intermedia corta el bucle en silencio. ✅ **Lo que sí funciona: una función de diagnóstico temporal** (acá `LogExit`, un `if bExiting → PrintString` colgado del final de `StepPills`), correr PIE una vez, dormir el total y leer con `GetLogEntries` — dio **210 muestras a frame-rate** con el valor exacto de las tres variables; después se borra la función y se barre. Regla: **el motor muestrea a 72 Hz gratis; el MCP a ~3 Hz y caro.** Todo lo que dure menos de unos segundos se mide por log, no por poll.
⚠ Corolario del DSL: un `if` o un `for` **cierran la lista de statements**, así que un print condicional NO se intercala en medio de una función existente — va en su **propia función**, llamada al final de la cadena (una línea de alta y una de baja, sin tocar la lógica que se está verificando).

216. 🔴🔴 **El `read_graph_dsl` imprime type_ids que el `write` NO acepta — cuatro formas exactas, medidas a golpes (2026-08-25).** Amplía la §211. Al reescribir `ApplyRingScale`, `SpawnSoul` e `IntroOutro` el read daba texto que el write rechazaba una y otra vez. Las reglas que salieron, todas verificadas con `create_node`:
   - **Variables propias:** el read imprime `(|GetSoulRef)` pero el write/`create_node` exigen **`Variables|<CategoríaSinEspacios>|GetSoulRef`** (`Z - Estado interno` → `Z-Estadointerno`). El prefijo vacío no existe.
   - **Booleanos `bAlgo`: el getter PIERDE la `b`.** `Variables|Z-Estadointerno|GetbAppearing` **no existe**; la buena es **`GetAppearing`**. (El read imprime `GetbAppearing`.)
   - **Miembros de OTRA clase: hay que nombrar la clase por la que está TIPADA la referencia, no la que lo declara.** `AppearTime` vive en `BP_Alma_SC`, pero `SoulRef` es un `BP_ProtoSoul_SC` → `Class|BPAlmaSC|SetAppearTime` **crea el nodo pero no conecta** (*"Could not connect pin SoulRef to self"*: el MCP no hace upcast implícito hijo→padre). Con **`Class|BPProtoSoulSC|SetAppearTime`** entra a la primera. El read, para colmo, lo imprime siempre como la clase declarante.
   - **`Math|Interpolation|Ease` tiene 4 pines al crearse** (`Function, Alpha, A, B`) aunque el read imprima 5: el `BlendExp` está oculto hasta que la Function tiene valor. Pasarle 5 args falla.
   ⚠ Y un límite del `select`: sus `Option` son wildcard y **no aceptan la salida de un nodo** si el tipo aún no se resolvió (*"Could not connect pin Result to Option 1"*); con literales anda. Si el factor sale de un cálculo, reformulá la expresión en vez de pelearte con el select.
   👉 **Método barato para no adivinar:** `create_node` con el type_id candidato → si devuelve refPath, existe (y lo borrás); si no, probá la variante. Cuatro sondas en una llamada cuestan nada y ahorran cinco writes fallidos.

217. 🔴🔴 **Dos formas de romper algo mientras lo verificás (2026-08-25).**
   - **El valor de instancia de una variable nueva se lo come el SIGUIENTE recompilado del Blueprint.** Es la §212 con un añadido caro: escribir el override en la instancia y verificarlo **no alcanza** si después vas a volver a compilar el BP — al reconstruirse el actor el override se pierde (medido: `IntroInTime` puesto en 1,2 y verificado, y tres compilaciones después valía 0,6). ✅ **Orden correcto: terminar TODOS los cambios del Blueprint → compilar por última vez → recién ahí escribir los valores de instancia → guardar el NIVEL.** Y verificar el valor en una corrida real, no sólo con `get_properties`.
   - **Borrar un nodo de diagnóstico INTERCALADO deja la cadena cortada.** Si insertaste `A → log → B`, el `delete_node` del log te deja `A → (nada)` y `B` colgando; el compilador **no se queja** porque `B` sigue siendo un nodo válido. Pasó con `ApplyRingScale → StepRings` en el Tick de la ameba: los anillos no se habrían animado nunca más. ✅ **Al sacar un nodo intercalado, re-empalmar siempre**, y confirmarlo leyendo el pin de salida del predecesor. 💡 Preferible: colgar el diagnóstico **al final de una cadena** (donde no hay sucesor que reconectar) en vez de intercalarlo.

218. ⏳ **Una captura sacada justo después de `MaterialTools.recompile` NO es evidencia: el shader todavía está compilando.** Al probar `BLEND_Translucent` en `M_SoulRibbon_SC` la captura inmediata mostró **los anillos desaparecidos**, y estuvo a punto de quedar escrito en el tracker que el translucent no servía para ese material — una conclusión falsa que habría cerrado el único camino que resolvía el pedido. **Con 4 segundos de espera antes de capturar, el mismo cambio se ve perfecto.** 👉 Regla: después de cambiar `blendMode`, `shadingModel` o cualquier cosa que dispare recompilación de shaders, **dormir unos segundos antes de mirar**; y si el resultado es "no se ve nada", **sospechar del timing antes que del cambio** (el síntoma de un shader a medio compilar y el de un material roto son idénticos en una imagen).
⚠ Emparentado con §202 y con [[debugging-instrumento-sin-validar]]: **un instrumento sin validar produce diagnósticos falsos con total confianza**. El control positivo barato acá era volver al modo anterior y comprobar que la captura sí muestra los anillos.


## 🌾 Cosecha 2026-08-25 (construyendo `BP_BreathRing_SC`, el temporizador de respiración)

219. 🔴🔴 **LOS NOMBRES DE FUNCIÓN CHOCAN ENTRE BLUEPRINTS Y EL DSL RESUELVE AL EQUIVOCADO — EN SILENCIO, Y COMPILANDO.**
La trampa más cara del día, y es de la misma familia que §"los literales string de una función propia se pierden": **compila, corre, y miente.**
Escribiendo `(CallFunction|Apply :Time ...)` para llamar a **mi propia** función `Apply`, el DSL cableó
`Class|BPInstructionsPanelSC|Apply` — la función homónima de **otro** Blueprint — y le enchufó un float en el pin de target.
Tres rondas del mismo bug en una sola sesión:
- `Apply`   → `Class|BPInstructionsPanelSC|Apply`
- `Advance` → `Class|BPBell|Advance`
- `RingApply` / `RingAdvance` → `Class|BPProtoSoul|RingApply` / `RingAdvance` (¡el segundo intento de renombrar también chocó!)

**Cómo se detecta:** **leyendo el grafo después de escribirlo**. Si aparece `Class|OtroBP|MiFuncion` donde escribiste
`CallFunction|MiFuncion`, es esto. `compile_blueprint` **no lo detecta** (el grafo es válido, sólo llama a otra cosa).
**Cómo se evita:** antes de nombrar una función, `find_node_types(graph, "MiNombre", [])` y mirar que **no** haya
`Class|...|MiNombre`. Un nombre libre devuelve `[]`. Es una llamada barata contra media hora de reescritura.
⚠ **Los event dispatchers tienen el mismo problema, pero ahí sí falla la compilación**: `Default|CallOnFinished` resolvió
al `OnFinished` de `BP_InstructionsPanel_SC` y el compilador tiró *"This blueprint (self) is not a BP_InstructionsPanel_SC_C"*.
Ese error, molesto como es, es **el caso afortunado**: avisa. Con las funciones no avisa nadie.
👉 Es la generalización de la lección de `BP_BreathPacer` ("todo lo del pacer lleva prefijo `Pacer*`"): **no es cosmética,
es corrección**. En un proyecto con 80 Blueprints, `Apply`, `Advance`, `Step`, `Layout`, `Update` y `Init` están todos tomados.

220. **Las variables se referencian por su CATEGORÍA, no por `Variables|Default|`.** En cuanto le ponés categoría a una
variable con `set_variable_category`, su `type_id` pasa a ser `Variables|<Categoria-sin-espacios>|Get<Nombre>` — p.ej.
categoría `"A - Ritmo"` → **`Variables|A-Ritmo|GetDivisions`**. `Variables|Default|` queda **sólo para los componentes**.
Combinado con la normalización rara de mayúsculas y la `b` que se cae, un `bScaleToCycleTime` en la categoría `A - Ritmo`
se escribe **`Variables|A-Ritmo|GetScaletoCycleTime`** (sin `b`, y con la "to" en minúscula).
✅ La forma barata de obtener la lista exacta: `find_node_types(graph, "Variables|A-Ritmo|", [])`.

221. **`add_variable` quiere los tipos en MINÚSCULA.** `bool`, `int`, `float`, `byte`, `name`, `string`, `text`, y
`Vector`/`Rotator`/`Transform`/`Vector2D`/`LinearColor`. `"Boolean"` e `"Integer"` fallan con *Unknown type*.
⚠ Y el error de `execute_tool_script` **sale agregado al final** aunque cada llamada esté envuelta en `try/except`:
las variables que sí se pudieron crear **quedan creadas**. Re-listar antes de reintentar, o se duplican.

222. **`get_actor_bounds` devuelve un cubo fijo de 256 cm** para los actores de BP de este proyecto (verificado en
`BP_BreathRing_SC`, `BP_BreathOrb_SC` y `BP_InstructionsPanel_SC`: los tres dan exactamente ±128 alrededor de su posición).
**No sirve para medir tamaños ni para decidir encuadres.** Casi dispara una cacería de un bug inexistente ("el anillo mide
2,5 m"). Para medir de verdad: leer `relativeScale3D`/`relativeLocation` de los componentes.

223. **`ActorTools.set_actor_transform` SÍ funciona** sobre un actor ya colocado (contra lo que decía `toolsets.md`), y en
cambio `ObjectTools.set_properties` sobre su **root component se aplicó a medias**: tomó la X e ignoró la Z, devolviendo
éxito. Es "declarado ≠ aplicado" otra vez. 👉 Para actores del nivel: **`set_actor_transform` y verificar con
`get_actor_transform`**; si los dos no coinciden, volver a setear hasta que coincidan.

224. **El `WidgetComponent` RECREA su widget en cada reconstrucción del actor.** Se ve en el log por el nombre de instancia:
tres cambios de propiedad seguidos produjeron `WBP_..._C_90`, `_158`, `_92`, `_95`, `_98`. Consecuencia práctica: **todo lo que
el Construction Script le meta al widget por código (hijos, texto) se pierde**, y por eso **el contenido dinámico de un widget
no se previsualiza en el viewport del editor** — aunque sí se construya en Play (medido: 20 letras).
👉 Corolario de diseño: **lo que Beltrán tiene que autorar mirando no puede vivir en un widget**. En `BP_BreathRing_SC` los
anillos, divisores y marcador son componentes reales (se ven en vivo) y sólo los textos son widget (se ven en Play).
💡 Truco de diagnóstico que lo destapó: loguear `GetChildrenCount` **antes** del `ClearChildren` — si siempre da 0, el widget
es otro. Y loguearlo **después** de construir mide cuántos hijos quedaron de verdad, sin depender de una captura.

225. ✅ **`select` es la salida a la regla "un solo multi-exec y va al final".** `Layout` necesitaba tres bucles y varias
ramas seguidas; se escribió **completamente desenrollada** (4 divisiones como máximo → 4 bloques explícitos) y con `select`
en vez de `if`. Resultado: un grafo plano, sin un solo bucle, sin acumuladores y sin funciones auxiliares de una sola línea.
Cuando el tamaño del problema está acotado y es chico, **desenrollar sale más barato que pelearse con el parser**.

226. 🔴 **El signo del PITCH: `pitch positivo LEVANTA el +X`.** `Ry(+90)` manda **+X→+Z (arriba)** y **+Z→−X**;
`Ry(−90)` manda **+X→−Z (abajo)**. Lo tuve al revés armando el marco de `BP_BreathRing_SC` y el resultado fue un
reloj que **giraba al revés**: con `Pitch −90` el eje local que yo usaba como "arriba" apuntaba abajo, así que
`(cos θ, sin θ)` recorría el círculo en antihorario. **Compila, se ve bien en una captura estática, y sólo se nota
cuando algo se mueve** — lo cachó Beltrán mirando, no yo midiendo, porque mis mediciones eran de coordenadas
**locales** (correctas) y el bug estaba en el mapeo local→mundo.
👉 **Regla:** cuando un componente-marco define un sistema de coordenadas 2D (un reloj, un dial, un tablero),
**asertar el sentido con un valor asimétrico**: poner el indicador a 1/8 de vuelta y confirmar que cae en el cuadrante
esperado. Con 4 marcas simétricas a 0/90/180/270 **una captura no distingue horario de antihorario**.
💡 Y la palanca queda barata: el sentido de giro entero se invierte cambiando **ese solo número** (±90), sin tocar fórmulas.

227. **Una forma orientada en UV no se acomoda probando signos: hay que saber QUÉ EJE es.** El medio disco de
`M_BreathDot_SC` se cortaba con `CutDir`. Probar (0,1,0) y después (0,−1,0) dio "mal" las dos veces, porque **ambos son
el eje tangencial**: cambiaba de un tangente al otro, nunca a radial. El correcto era **(−1,0,0)** — el eje U del `Plane`,
que es el que el `Yaw = θ` del componente alinea con el radio. ⚠ En una captura chica los dos valores equivocados
"parecen casi bien", que es justo lo que hace perder la ronda. **Razonar el eje primero, elegir el signo después.**

228. 🔴🔴 **`set_properties` con varias propiedades juntas puede aplicar unas y NO otras, devolviendo éxito.**
Creando los planos de palabra de `BP_BreathRing_SC` mandé `staticMesh` + `overrideMaterials` + flags de sombra en
**una sola llamada**: entró todo menos **`staticMesh`, que quedó en `None`**. El síntoma fue de manual del terror:
planos **invisibles** cuyo material, escala, rotación y visibilidad **leídos daban todos correctos**. Depuré el
material, la textura, el alpha, el blend y el mapeo UV antes de mirar lo único que no había verificado.
👉 **El mesh va en su propia llamada, y se verifica componente por componente.** En la misma tanda yo sí había
verificado `RingFixed` y `Mark` — **la regla aplicada a medias no protege**: hay que verificar TODOS.
⚠ Segunda capa: la **instancia ya colocada guarda su propio override**, así que arreglar el CDO **no la cura**;
hubo que reponer el actor. Y ⚠ tercera: un `SetStaticMesh` por código con la **ruta entre comillas no resuelve**
(el literal no se convierte en referencia de asset) — si hace falta por código, va por **variable de objeto**.

229. ✅ **Cómo averiguar el mapeo UV de un mesh sin adivinar: la prueba de la "F".**
Necesitaba saber cómo cae una textura sobre un `Plane` rotado, y había **ocho** combinaciones posibles
(4 rotaciones × espejo). En vez de probarlas de a una, horneé una textura con una **"F" grande y asimétrica**
en una posición conocida y la miré una sola vez: **dónde cae** da la traslación/rotación y **cómo se ve**
(espejada o no) da el determinante. Con eso el mapeo queda determinado y la corrección se calcula, no se tantea.
💡 Resultado para `/Engine/BasicShapes/Plane` girado por `Yaw` bajo un marco con `Pitch +90`: el eje **U es el
radial** y el **V el tangencial**; una textura pensada "arriba y leyendo a la derecha" entra **rotada 90° horario**.
⚠ Y ojo: **un espejo no se arregla con un offset de yaw**, sólo con rehornear o invertir la UV.

230. **Para un material ADITIVO conviene texto blanco sobre fondo NEGRO, no alpha.** El primer horneado fue blanco
con fondo transparente y usé el canal A: no se vio nada. Con fondo negro y usando el **RGB**, el negro no suma y
el problema del alpha (compresión, premultiplicado, `sRGB`) desaparece de la ecuación. Es un nodo menos y una
fuente de fallo silencioso menos.

231. **`TextureTools.import_file` NO sobrescribe**: si el asset existe, falla con *"already exists"*. Hay que
`AssetTools.delete` primero. ⚠ Y borrar la textura **rompe el default del `TextureSampleParameter2D`** del material
que la usaba (*"Found NULL, requires Texture2D"* al recompilar) — después de reimportar hay que **volver a setear
el default del nodo** y los parámetros de las instancias.

232. 🔴 **Si un material remapea la UV, la textura necesita `TA_Clamp` — si no, aparecen COPIAS.** En
`M_BreathWord_SC` la palabra se escala reescalando la UV alrededor de su centro. En cuanto el autor achicó el
texto, el muestreo se salió de [0,1] y el **`TA_Wrap` de fábrica** trajo la palabra de vuelta **rotada 180°** al
otro lado del anillo (wrap en U y en V a la vez = giro de media vuelta).
👉 **Dos capas, y conviene poner las dos:** un **`Saturate` sobre la UV** en el material (protege aunque cambien
la textura) y **`addressX`/`addressY` = `TA_Clamp`** en el asset. Funciona porque el borde de la textura es negro
y el material es aditivo: lo que se sale no suma nada.
⚠ Yo había **previsto este riesgo** al descartar la versión polar por "copias fantasma al achicar"… y después no
lo apliqué a la versión cartesiana, que tiene el mismo problema por otra vía. **Un riesgo identificado y no
mitigado es un bug con aviso previo.**

233. 🔴 **Un componente agregado al CDO DESPUÉS de que la instancia existe nace SIN su `staticMesh` en esa instancia.**
Agregué `RingAnim2`/`RingAnim3` al CDO de `BP_BreathRing_SC` con malla y material **verificados en el CDO**, y en
el actor ya colocado los dos aparecieron con `staticMesh = None` (invisibles), aunque el material y la escala sí
llegaron. Es la misma familia que §228 pero por otra puerta: no es que la llamada falle, es que la instancia
**no adopta** ese campo para componentes nuevos.
✅ **Reparación sin reponer el actor** (importante cuando la instancia tiene ajustes a mano que no se pueden
perder): setear `staticMesh` **en el componente de la instancia** y confirmar que **sobrevive una reconstrucción**
(forzarla escribiendo una propiedad con su MISMO valor, para no alterar nada del autor). En este caso sobrevivió.
👉 Regla: después de agregar un componente con malla al CDO, **verificar la INSTANCIA, no sólo el CDO**.

234. 🔴 **Los nombres de EVENTO CUSTOM colisionan igual que los de función — y los buenos ya están tomados.**
Llamando desde `BP_Director_Story` a los eventos `Appear` y `Play` de `BP_BreathRing_SC`, el DSL cableó
**`Class|BPAlmaSC|Appear`** y **`Components|Animation|Play`**, con el anillo como target y compilando sin chistar.
Es la §219 aplicada a eventos. 👉 **La API pública de un BP también necesita prefijo propio** (`BRingShow`,
`BRingGo`, …). ⚠ Y ojo: `find_node_types` **no lista los eventos custom recién creados** desde otro BP, pero
`write_graph_dsl` **sí los crea** con el id armado a mano (`Class|BPMiClase|MiEvento`) — la ausencia en el
listado no significa que no se pueda llamar.

235. 🔴 **`set_pin_value` sobre un `CallFunction`: el primer argumento es el índice 2, no el 1.**
Los pines de entrada son `0 = execute`, `1 = self` (oculto para funciones propias), `2 = primer parámetro`.
Escribir en el 1 **no da error** y el argumento se queda en su default. Me dejó dos llamadas con `Mode = 0`
cuando debían ser 1 y 2. 👉 **Leer los pines con `get_node_infos` antes de escribir**, siempre.

236. 🔴 **Una condición de "apagate" hay que probarla con el caso de ARRANQUE, no con el de cierre.**
`OrbRetire` destruía el orbe en el primer frame porque la condición (`Mode == -1 && RevealT < 0.02`) **ya era
verdadera antes de que la etapa empezara** — el sensor está en −1 mientras no haya `SetStage`. Lo delató el log
de PIE. 👉 Toda lógica de auto-destrucción necesita un flag de **"esto llegó a ocurrir"** (acá `bEverShown`),
no sólo de "ya terminó". ⚠ Y la lección de método: yo había **identificado** el riesgo y lo descarté razonando.
**Un riesgo identificado se mitiga o se verifica; no se argumenta.**

237. ✅ **Para cerrar una etapa desde un BP nuevo, reusar la función de cierre que el director YA tiene.**
`BP_Director_Story.StepTimeDone()` trae adentro la guarda `WaitFor == "time"`. Llamarla desde afuera sale gratis
y además **conserva el cortafuegos por tiempo**: cierra el que llegue primero y el segundo aviso se ignora solo,
sin coordinación ni banderas nuevas. Buscar siempre ese punto de entrada antes de inventar un handshake.

238. ⚠ **Un `bool` instance-editable nuevo es el peor caso del "nace en cero": cero = `false` = APAGADO.**
Con un float, nacer en 0 suele dar algo raro pero visible; con un bool de tipo `bShowX`, la instancia vieja
arranca con **todo invisible**, que parece que el Blueprint se rompió. 👉 Dos salidas: (a) inicializar la
instancia a mano al agregar la variable — y avisarle al autor que se tocó sólo eso; o (b) **invertir el nombre**
(`bHideX`), donde `false` = comportamiento de siempre y el default del motor ya es el correcto.
Acá se eligió (a) porque "activar/desactivar" en positivo se lee mejor en el panel, pero (b) es la opción
a prueba de olvidos si nadie va a inicializar la instancia.

## §220 — `create_node` de operadores promotables (`Utilities|Operators|Divide/Add/...`) resuelve a la sobrecarga EQUIVOCADA (2026-08-25)
Un `create_node` con `Utilities|Operators|Divide` creó un nodo cuyo `type_id` efectivo fue
`Utilities|TimeManagement|FrameNumber/FrameNumber` (pines Wildcard); ídem `Add` →
`FrameNumber+Int`. Nacidos así ANTES de conectar nada, quedan resueltos mal y hay que borrarlos.
Contraste: `Utilities|Operators|Multiply` creado y CONECTADO a floats promovió bien a
`Math|Float|float*float` — la promoción depende del orden y no es confiable.
👉 Regla práctica (BP_Elevator_SC, ElvStep): para aritmética por cirugía **preferir las funciones
tipadas del catálogo** (`Math|Float|SafeDivide`, `Math|Float|Max(Float)`, `Math|Float|Min(Float)`,
`Math|Float|Sqrt`, `Math|Float|Lerp` — todas verificadas) y, si se usa un promotable, leer el
`type_id` con `get_node_infos` DESPUÉS de conectar; si dice FrameNumber, borrar y rehacer.
Los ids `Math|Float|float*float` / `float-float` que muestran los reads NO existen para `create_node`.

## 🌾 Cosecha 2026-08-25 (noche) — la red neuronal de Loving (`NS_NeuralWeb_SC`): Niagara y materiales por MCP

### §221 🔴🔴 `connect_expressions`/`connect_to_output` NO recompilan el material — el shader queda CONGELADO en el grafo anterior
Construir un material entero por MCP (crear → set BlendMode/ShadingModel → agregar expresiones → conectar) deja el **shader compilado del estado en que estaba en el último PostEditChange** — para un material recién creado, el grafo VACÍO. Un unlit aditivo vacío = negro = **invisible sin ningún error**: compila, el thumbnail renderiza, `bUsedWithNiagaraSprites` está en true… y la partícula no dibuja NADA. Costó ~1 hora y 12 capturas.
- **Síntoma de diagnóstico:** el emitter dibuja con `DefaultSpriteMaterial` y con el material propio no.
- **Fix:** al TERMINAR el grafo, forzar PostEditChange tocando cualquier propiedad real: `ObjectTools.set_properties {"TwoSided": false}` (y de vuelta si hace falta). `set_properties` sí recompila; las tools de grafo de `MaterialTools` no.
- **Regla:** después de CUALQUIER edición de expresiones/conexiones de un material → un `set_properties` de sacrificio antes de juzgar el resultado.

### §222 🔴 Un módulo Set Parameters NO puede leer un atributo que él mismo escribe
Todos los Map Get de un `AddSetParametersModule` se evalúan ANTES que todos sus writes. Encadenar entradas dentro del mismo módulo (`Particles.PosA ← f(Particles.IdxA)` con IdxA escrito arriba en el mismo módulo) da:
`Variable Particles.IdxA was read before being set. It's default mode is "Fail If Previously Not Set"`.
**Fix: partir en módulos consecutivos** (uno por "nivel" de dependencia: índices → posiciones → derivados). `AddSetParametersModule` agrega **al final** del script → crearlos en orden y borrar el combinado con `RemoveModule` (param: `moduleToRemove`). Verificar el orden con `GetScriptStackTopology`.

### §223 🔴 EmitterState `Once` + partículas inmortales = el sistema MUERE a los 2 s, sin error
`SpawnBurst` + `Kill Particles When Lifetime Has Elapsed = false` no alcanza para un efecto permanente: con `Loop Behavior = Once` y `Loop Duration = 2` (los defaults de `SimpleSpriteBurst`), el loop termina, el emitter completa (`Inactive Response = Complete`) y **se lleva las partículas inmortales**. Nada en logs. **Fix: `Loop Duration Mode = Infinite`** (`ENiagara_InfiniteLoopDuration::NewEnumerator1`) en cada emitter persistente.

### §224 Recetas verificadas de autoría Niagara por MCP (las que faltaban en `toolsets.md`)
- **Crear sistema:** `CreateNiagaraSystem {assetName, assetPath, templateSystem: "/Niagara/DefaultAssets/DefaultSystem.DefaultSystem"}` → ⚠ **trae un emitter `Fountain` de regalo: `RemoveEmitter`**. Emitters: `AddEmitter {system, templateEmitter, emitterName}` — plantillas útiles en `/Niagara/DefaultAssets/Templates/Emitters/` (`SimpleSpriteBurst` = burst+initialize+state+sprite, ideal base).
- **User var de DATA INTERFACE** (`AddUserVariables`): `type.underlyingType = 1` (Class) y el default va como `{"struct": {"refPath": "/Script/NiagaraEditor.NiagaraExt_VariableValue_DataInterface"}, "value": {"dataInterfaceClass": {"refPath": "/Script/Niagara.NiagaraDataInterfaceArrayFloat3"}}}` (sin `dataInterface`, se crea solo). Con structs normales el default `{"struct": <tipo>, "value": {...}}` de siempre.
- **Asignar un dynamic input a un stack input:** `SetStackInputData` con `{"struct": ".../NiagaraExt_StackInputData_DynamicInput", "value": {"dynamicInputAsset": {"refPath": "/Niagara/DynamicInputs/..."}}}`; sus hijos se direccionan EXTENDIENDO `inputNameStack` (p.ej. `["Particles.Position", "Input Position", "A"]`) y se descubren con `GetDynamicInputChain`. Enumerar qué dynamic inputs existen para un tipo: `GetAvailableDynamicInputs {type}`.
- **Muestrear un array User por índice SIN Scratch Pad** (la llave del plexus): dynamic input `SelectVectorFromArray`/`SelectIntFromArray` → hijo `Array Sampling Mode` = `ENiagaraArraySamplingMode::NewEnumerator1` ("Direct Set"), hijo `Vector/Int Selection Array` = Linked al User DI, hijo `Direct Array Index` = `ReturnExecIndex` o Linked a un atributo int. Piezas hermanas verificadas: `ConvertVectorToPosition` (hijo `Input Position`), `Lerp_Vector` (A/B/Alpha), `Subtract_Vector` (A/B = A−B), `NormalizeVector` (hijo `Vector To Normalize`), `VectorLength` (hijo `Vector`), `MakeVector2D` (X/Y), `Vector2DFromFloat` (hijo `Value`), `Multiply_Float`/`RandomRangeFloat` (Minimum/Maximum).
- **Renderer:** `SetRendererData {renderer, rendererData.propertyValues}` acepta JSON PARCIAL (`Material`, `Alignment: "CustomAlignment"`, `FacingMode: "FaceCameraPosition"`, `bCastShadows`). `SetEmitterData {emitter, emitterData.propertyValues}` ídem (`{"bLocalSpace": true}`).
- **Set de propiedades con arrays que crecen** (`Inputs` del Custom material node): el tool rechaza cambiar tamaño y contenido a la vez ("insertion points are ambiguous") → **primero crecer el array replicando el elemento existente tal cual, después setear los valores** en una segunda llamada.
- **Verificar sin visor:** `StartPIE {options:{bSimulate:true, playMode:"PlayMode_Simulate", warmupSeconds}}` (Simulate SÍ avanza Niagara; el viewport quieto NO) + captura a disco. Y **control positivo**: un Niagara probado colocado al lado separa "el efecto no dibuja" de "mi instrumento no ve" — fue lo que destrabó §221.


### §225 🔴🔴 `set_properties` con el MISMO valor NO recompila el material — y un Custom node roto usa el Default Material
Ampliación de §221, pagada de nuevo el 2026-08-26. Dos capas:
1. **Forzar la recompilación exige un cambio REAL de valor.** Poner `{"TwoSided": true}` en un material que YA estaba en `true` no dispara PostEditChange: el shader sigue congelado. Hay que **alternar** (false → true) o tocar otra propiedad.
2. **Si el HLSL del Custom node no compila, Unreal cae al Default Material** (gris opaco) y lo dice SOLO en el log: `Failed to compile Material ... Default Material will be used in game`. El síntoma en pantalla es "las partículas se ven negras/grises opacas". 🔎 **Ante cualquier rareza visual de un material tocado por MCP, el primer llamado es `GetLogEntries(pattern:"<Material>.*Failed to compile")`.**
⚠ Un Custom node con MUCHOS inputs (13, con nombres como `UV`/`Cam`/`Dx`) falló a compilar sin decir por qué; el mismo código con 6 inputs compiló. Si hay que pasar muchos datos, preferir menos inputs (o Collection Parameters) antes que engordar el nodo.

### §226 🔴 `ReturnExecIndex` NO es válido en Particle **Update** — colapsa todas las partículas en el índice 0
Sirve en Particle **Spawn** (da el índice de la partícula que nace). En Update devuelve lo mismo para todas → si se usa para indexar un array de posiciones, **las N partículas se apilan en una sola posición** (síntoma: "de 120 puntos veo uno solo").
**Receta:** guardar el índice en un atributo propio durante el Spawn (`Particles.MiIdx = ReturnExecIndex`) y en Update leer **ese atributo**. Es el mismo patrón que ya usaban `IdxA`/`IdxB` y por eso las líneas no sufrían el bug.

### §227 🔴🔴 `ObjectPositionWS` significa cosas DISTINTAS en Sprite vs Mesh renderer
- **Sprite renderer**: devuelve la posición del **componente** (el centro del sistema). ✓ es lo que uno espera.
- **Mesh renderer**: devuelve la posición de **esa instancia** (la partícula misma).
Consecuencia real (2026-08-26, `NS_NeuralWeb_SC`): un WPO que colapsaba todo hacia `(P - C)` funcionaba en los puntos (sprites) y **no hacía nada en las líneas** (meshes), porque cada línea se colapsaba sobre su propio centro. Síntoma: "los puntos se achican pero las líneas quedan grandes".
**Solución:** no depender de `ObjectPositionWS` cuando hay meshes — pasar el centro explícitamente por un **VectorParameter del MPC** que el BP escribe con `GetActorLocation`.
💡 Para crear el VectorParameter por MCP: si el array está vacío, `set_properties` con la lista completa de un elemento funciona; si ya tiene elementos, primero **crecerlo replicando** y después renombrar (ArrayAdd no acepta cambio de tamaño + contenido a la vez). Las claves del struct son **camelCase**: `parameterName`, `defaultValue`, `id` (dar un `id` GUID distinto al duplicar).

### §228 Ciclo de vida de partículas que indexan un catálogo: el orden de módulos y el índice compartido
Para que las conexiones "nazcan y mueran tomando pares nuevos" (efecto plexus vivo) sin Scratch Pad:
`EmitterUpdate`: **desactivar** `SpawnBurst_Instantaneous` y agregar `/Niagara/Modules/Emitter/SpawnRate` con el rate linkeado a un user param. · `ParticleState`: `Kill Particles When Lifetime Has Elapsed = true`. · `InitializeParticle`: `Lifetime Mode = Random` (`ENiagara_LifetimeMode::NewEnumerator1`) + Min/Max linkeados. · Fade: `RampInOut` con **`Mode = 2`** (In+Out) sobre `Particles.NormalizedAge`, multiplicando el color.
🔴 **El índice del par tiene que ser UNO SOLO compartido**: si A y B sortean por separado, se conectan nodos de pares distintos y se pierde el filtro de distancia. Guardar `Particles.PairIdx = RandomRangeInt(0, LinkCount-1)` en un módulo **anterior** al que lee A y B.
⚠ Y como `AddSetParametersModule` **siempre agrega al final**, la única forma de reordenar es **borrar y recrear en orden** (`RemoveModule` param: `moduleToRemove`). Verificar el orden con `GetScriptStackTopology` antes de dar por bueno.

### §229 El `Plexus` de Epic (Content Examples) NO corre en un proyecto mobile
`/Game/ExampleContent/Niagara/NeighborGrid3D/Plexus` es exactamente el efecto de referencia (GPU, NeighborGrid3D, curl+vortex+attraction), pero **falla a compilar acá**: su módulo `Collision` usa **Distance Fields**, cuya query GPU exige SM5+ y Quest corre en ES3.1 (ya estaba verificado en `niagara-quest.md`). Duplicarlo y desactivar `Collision` **no alcanza**: el compilador se queda colgado (timeout de 120 s en `GetSystemCompileState`).
👉 Lo aprovechable del ejemplo es la **receta**, no el asset: nodos como mesh (esferas), líneas como sprite alineado, y fuerzas reales en el Particle Update.
🎁 De paso quedaron localizados módulos de librería que evitan el Scratch Pad: **`/Niagara/Modules/Debug/SpriteBasedLine`** (dibuja una línea entre dos puntos resolviendo el alignment por dentro — es lo que hay que usar si se vuelve a sprites) y la familia **`NeighborQuery`** / `Update/Neighbor/{CalculateNeighbors,SampleNeighbors}`.

### §230 GPU sim de Niagara en Quest: matiz importante sobre lo que decía la doc
`niagara-quest.md` §1 afirma (correctamente, por código) que el GPU sim **está permitido**: los 3 cvars vienen en `1`/`true`. Pero eso es **necesario y no suficiente**. Del hilo oficial de Epic (*Niagara GPU particles Sim on Meta Quest 2/3*):
- Un moderador afirma que *"Quest standalone no soporta GPU particles, solo CPU"*.
- Varios usuarios **lo hicieron funcionar en Quest 3** vía config del engine; uno confirma *"It does work!"* (con cautela para producción).
- Un dev de Epic da la clave: hay que declarar **`quest3` en el metadata de packaging del APK**, o el visor arranca en **modo compatibilidad Quest 2** y el GPU sim no corre.
- No hay evidencia de que funcione en Quest 2.
👉 Regla práctica: **CPU por defecto**; GPU solo si se mide en device y con el device profile bien declarado. La duda se resuelve empaquetando, no discutiendo.

### §231 🔴🔴🔴 TODO el `execute_tool_script` es UNA transacción — y una excepción de PYTHON no atrapada la revierte ENTERA (y puede comerse un actor ajeno)
Cosecha 2026-08-26 (construcción de Attracting). El `try/except BaseException` alrededor de cada `execute_tool` (la plantilla `safe_script.py`) **no protege de los errores del PROPIO script**: un `TypeError` de Python (un `%s` de formato chocando con el `%` del DSL en el mismo string) escapó, el script terminó en excepción y el plugin disparó su Undo. Dos consecuencias medidas:
1. **El lote entero se revirtió**: ~20 `write_graph_dsl` que ya habían salido bien quedaron en grafos vacíos (verificado por longitud de `read`). Todo lo que hace un script vive en UNA transacción.
2. **El mismo Undo se comió el actor `Director_Story` del persistente** — el único actor perdido (diff de nombres contra el `.umap` de HEAD), y un `save_assets([])` posterior lo grabó así. Se repuso a mano con sus valores conocidos.
👉 Reglas: (a) **nada de formateo `%` de Python** en scripts que contengan DSL — concatenar strings; (b) tras CUALQUIER script que termine en error, **diff de actores contra HEAD** (`grep -aoE 'BP_[A-Za-z0-9_]+_C_[0-9]+' | sort -u` sobre los dos `.umap`), no solo contar; (c) commitear antes de una tanda sigue siendo la única red real.

### §232 El `%` NO es operador del DSL — el módulo es `Math|Integer|%(Integer)`
`(% a b)` falla con `Utilities|Operators|Modulo does not exist`. Los demás operadores (`+ - * /`, comparaciones, `select`) sí existen.

### §233 🔴 `FadeIn`/`FadeOut`/`AdjustVolume` de AudioComponent: el DSL agarra el overload de SynthComponent
Mismo mecanismo que el §de los Fades de 2026-07-29, ahora medido también en `AdjustVolume` ("Could not connect pin PadAudio to self"). `Play` y `SetSound` en cambio resuelven bien. Salida: `create_node` con `declaring_class=/Script/Engine.AudioComponent` y cablear a mano.

### §234 `(Variables|X|SetMiObjeto)` SIN argumento escribe NULL — es la forma de limpiar refs por DSL
Compila y funciona (verificado: el read lo muestra como `(SetOccupant 0)`). Vale para pins de objeto de setters propios y cross-class (`(Class|BPSeqSlotSC|SetOccupant :self slot)` sin `:Occupant` → null).

### §235 §147 también muerde en ACTORES del nivel: `RelativeLocation` por `set_properties` aplica SOLO el primer campo
Colocando los 23 actores de Attracting: `{"RelativeLocation": {x,y,z}}` dejó todo con la X bien y **Y=0, Z=0** (y la rotación ni se aplicó). Fix: **una llamada por campo** (`{x}`, luego `{y}`, luego `{z}`, luego `{Pitch}`) y verificar con `get_actor_transform`.

### §236 `(for e arr ...)` del DSL: verificado que ADMITE statements después del loop y un multi-exec al final del cuerpo
No es terminal como el `if`. Con eso los barridos (`ShowSlots`, `HideSlots`, cacheos por `SetArrayElem`) caben en una sola función sin helpers de más. El `arr` puede ser el resultado bindeado de un nodo impuro (`GetAllActorsOfClass`).

### §237 `Class|SoundBase|GetDuration` se materializa como LECTURA DE PROPIEDAD `Duration`
El nodo que queda es un `K2Node_VariableGet` de la propiedad `Duration` (float) con target SoundBase — más barato que la función. ⚠ El `read` lo etiqueta `Components|GeometryCache|GetDuration` (colisión del lector); `get_node_infos` muestra la verdad.

### §238 🔴🔴 EL MURO de las salas RoomBase tenía colisión SÓLIDA — todo line-trace lanzado DENTRO de una sala pegaba a distancia CERO
`Asset/RoomBase/Cylinder_001` (el anillo de muro, compartido por las 6 salas de MapsV2) venía con `CollisionTraceFlag = CTF_UseDefault` → colisión simple = **casco convexo que llena todo el interior de la sala**. Cualquier `LineTraceByChannel` lanzado desde adentro nacía "dentro" del muro → hit inmediato en el punto de partida (`HitLoc == Start`, `bBlockingHit` true, largo 0). Síntoma real: **el beam de Attracting era invisible en visor** (mesh escalado a largo 0) — y era el PRIMER trace dentro de una sala RoomBase, por eso ningún otro sistema lo había delatado.
✅ **Fix: `CTF_UseComplexAsSimple` en el BodySetup** (`ObjectTools.set_properties` sobre `Cylinder_001:BodySetup_0`) → los traces pegan en la superficie real del anillo. Vale para las 6 salas; acá no hay física que necesite la colisión simple. ⚠ Requiere reiniciar PIE para que el estado físico se recocine.
👉 Diagnóstico que lo encontró (patrón reusable): publicar `BeamHitActor` desde el `BreakHitResult` y **posar la mano por MCP** (`set_properties` de `RelativeLocation`/`RelativeRotation` sobre el `MotionControllerComponent` del pawn en PIE — el truco de BP_Robot) → el hit dijo el nombre del culpable en una llamada.

### §231b El sandbox de `execute_tool_script` usa `_StrictDict`: `.get(k, default)` NO existe — y ese crash repite el incidente del §231
`einfo[0].get('output_pins', [])` tiró `TypeError: _StrictDict.get() does not support a default value` → excepción no atrapada → Undo → **el lote entero revertido y el actor `Sensor_Soul` comido del persistente** (segunda víctima tras `Director_Story`; repuesto con sus 28 knobs verificados contra el tracker — el CDO los tenía todos). Reglas que se suman al §231: (a) **acceso directo `d['k']`** o `try/except` alrededor, nunca `.get` con default; (b) mejor: NO hacer introspección de dicts dentro del script — leer los pines ANTES con `get_node_infos` desde afuera y pasar refs duras; (c) tras cada script fallido, diff de actores contra HEAD **en todos los mapas tocados**.

### §239 🔴🔴 TODO lo que viaja pegado al pawn/cámara debe nacer `NoCollision` — y NADA lo era (la saga de los colisionadores fantasma, 2026-08-26)
El beam de Attracting se cortaba "con algo cerca mío" y el izquierdo era invisible. Fueron CUATRO colisionadores distintos, todos con defaults del motor, todos pegados al usuario: la **esfera de la viñeta** (`BP_Director_Movement.Vignette`, QueryAndPhysics — la viñeta original decía "sin colisión para no tapar los line traces" y el duplicado lo perdió) · la **proto ameba de la cara + sus 5 anillos ProceduralMesh** (BlockAll — el `BP_ProtoSoul` viejo era sin colisión POR DISEÑO) · los **visualizadores de los mandos** (`XRDeviceVisualization*`, BlockAllDynamic) · y el definitivo: **el `WidgetComponent` del HUD** (`BP_SoulHUD_SC.Hud`, §54 — un widget de 40×16 cm frente a la vista que bloqueaba Visibility).
👉 **Regla**: al crear cualquier cosa que se attachee al pawn o a la cámara (viñetas, HUDs, amebas, anillos, meshes de beam, visualizadores), poner `NoCollision` EXPLÍCITO en el momento de crearla — en el template Y verificado en la instancia (§294 muerde acá con ganas).
👉 **Método que cerró la saga en UNA pasada** (después de 3 de hipótesis): un print con flanco `BEAM corto contra: <GetDisplayName(HitActor)>` cuando el trace pega a <40 cm. El log del visor de Beltrán escupió `SoulHUD_SC` cientos de veces. **Ante "choca con algo", instrumentar el NOMBRE del hit vale más que cualquier teoría.**

### §240 🔴🔴 Un componente NUEVO en un BP con instancias YA COLOCADAS llega a la instancia con las propiedades PELADAS
Mordió DOS veces el mismo día (2026-08-26, Attracting): se agregó `BeamMeshL` al sensor (instancia ya colocada) y la instancia lo recibió con **`StaticMesh=None`** (mesh invisible, costó dos pasadas de visor); se agregaron los `BeamFxR/L` (Niagara) y llegaron con **`Asset=None` y `bAutoActivate=true`** (ambos distintos del template). Es la §294 en su forma más venenosa: no es un default que no llega — es el componente entero degradado.
👉 **Regla: después de agregar un componente a un BP con instancias colocadas, leer EN LA INSTANCIA el asset/mesh y las props clave y reescribirlas si llegaron vacías.** Los actores SPAWNEADOS no sufren esto (copian el CDO).

### §241 `Deactivate` de un Niagara con partículas de vida ~infinita deja el efecto CONGELADO en el aire
El ribbon del beam (`LineTrace`, `User.Life` enorme) al desactivarse solo corta el spawn: las partículas vivas quedan dibujadas donde estaban. Síntoma: "los beams se quedaron pegados donde estaban" al cerrar la etapa. ✅ Acompañar la activación con **`SetVisibility`** del componente (mismo bool) — esconde al instante y al reactivar vuelve. (`DeactivateImmediate` es la alternativa si se quiere matar la simulación.)


---

## 🔴🔴 `MinOfFloatArray` / `MaxOfFloatArray` entran por un `ToFloat(Integer)` y TRUNCAN (2026-08-27)
Construyendo la normalización de las curvas de [[BP_Portrait_SC]]. Escrito por DSL:
```
(bind _lo (Math|Float|MinOfFloatArray In))
(bind _hi (Math|Float|MaxOfFloatArray In))
(bind _span (Math|Float|Max(Float) (- _hi _lo) 0.0001))
```
El `read_graph_dsl` devolvió esto:
```
(Math|Float|Max(Float) (Math|Conversions|ToFloat(Integer) (- (MaxOfFloatArray In) (MinOfFloatArray In))) 0.0001)
```
🔴 **El escritor mete un `ToFloat(Integer)` en el medio** — o sea que la resta se compiló como
**entera**. Con una serie de calma en 0..1 eso deja `hi - lo = 0`, el span se va al piso de `0.0001`, y la
curva sale **plana pegada al borde inferior**, con las 180 muestras en el mismo Y exacto.

**Compila limpio con `warnings_as_errors`. No hay ningún aviso.**

- **Cómo se detectó**: un `PrintString` en `Rebuild` con **el primer punto, el del medio y el último**
  de la curva ya construida. Los tres con `Y = 316.000` → no es "se ve raro", es una medición.
  La curva de `SeedDemo` (que escribe el array directo, sin normalizar) se veía bien: eso acotó el
  problema a la función de normalizado en un solo paso.
- **El arreglo**: no usar esos dos nodos. Mínimo y máximo **a mano**, con `Math|Float|Min(Float)` /
  `Max(Float)` contra el elemento del `for` (que sí llega como double), y después
  **`Math|Float|MapRangeClamped`**, que hace la normalización entera en un nodo y **sin ninguna resta**.
- 👉 **La regla general**: después de escribir aritmética por DSL, **releer el grafo y buscar
  `ToFloat(Integer)` que no escribiste**. Es la firma de una promoción a entero, y siempre es un bug.
  Vale para cualquier operador (`+ - * /`) entre valores que vengan de nodos que devuelven `float`
  single-precision.

## 🔴 `write_graph_dsl` sobre una FUNCIÓN: la lógica queda bien, pero DEJA HUÉRFANOS — 2026-08-27
La regla de oro dice "no re-`write_graph_dsl` un grafo que ya existe → lo DUPLICA". Precisión medida:
sobre un **grafo de FUNCIÓN** el `write` **sí reemplaza la cadena viva** (el `read_graph_dsl` posterior
muestra exactamente lo escrito, sin lógica duplicada) — **pero puede dejar el cuerpo anterior como isla
huérfana**, y el `read` **no la muestra**.

⚠ **Y no siempre**: de siete funciones reescritas la misma tarde, dos dejaron basura y cinco no.
`BP_Portrait_SC:Show` quedó en **19 nodos con 11 huérfanos** y `WBP_Portrait_SC:Normalize` en
**45 con 28**. Las otras cinco, limpias. O sea: **no se puede razonar sobre si quedó limpio — hay que
medirlo.**

- **Cómo se ve**: `find_nodes` devuelve muchos más nodos que los que imprime el `read`. Un
  `get_node_infos` sobre ellos muestra la misma llamada repetida N veces (una por reescritura).
- **El arreglo**: correr **`scripts/clean_orphans.py` tal cual** (dry=True primero). En este caso borró
  39 nodos con `identical: true` en los dos grafos — el DSL vivo byte por byte igual antes y después.
- 👉 **Regla: después de reescribir una función por DSL, barrer huérfanos.** No es opcional aunque el
  `read` se vea perfecto.

⚠ Lo que **no** se puede es `remove_function_graph` + `add_function_graph` con el mismo nombre en la misma
tanda: devuelve `Nombre_0`. Hay que **compilar en el medio**. Y si la función tiene llamadores, borrarla les
rompe el nodo → mejor reescribirla y barrer.
⚠ Lo que **no** se puede es `remove_function_graph` + `add_function_graph` con el mismo nombre en la misma
tanda: devuelve `Nombre_0`. Hay que **compilar en el medio**. Y si la función tiene llamadores, borrarla les
rompe el nodo → mejor reescribirla.


## 🔴🔴 Las variables instance-editable NUEVAS nacen en CERO en los actores YA COLOCADOS — otra vez (2026-08-27)
Ya está en la memoria como "lo de la INSTANCIA le gana al Blueprint", pero mordió **tres veces en una sola
jornada** y conviene el recordatorio operativo: **agregar una variable instance-editable a un Blueprint que
ya tiene instancias en el nivel deja esas instancias con el valor CERO/vacío**, aunque el CDO tenga el
default correcto.

Los tres casos del día:
1. `BP_Director_Story.PortraitHold` — CDO 20 s, instancia **0** → el retrato no habría esperado nada.
2. `BP_Portrait_SC.MelodySteps/Spacing/Step/Scale/Offset` — CDO poblado, instancia **todo 0** →
   `BuildMelody` redimensionó el array a 1 y **sembró 0 esferas** de 4. Compilaba, corría, y no decía nada.
3. `BP_Portrait_SC.MelodySounds` — CDO con los 20 clips, instancia **array vacío**.

👉 **Checklist**: después de `add_variable` + `set_variable_instance_editable` + escribir el default en el
CDO, **escribirlo TAMBIÉN en cada instancia colocada** y verificar con `get_properties` **sobre la instancia**.
El síntoma típico es "la función corre pero no hace nada": lo delató un log que contaba cuántas esferas
había sembrado (`sembradas = 0` con la melodía bien parseada), no una hipótesis.

## 💡 Colisiones de `GetDuration`: hay 16, y el DSL agarra la de GeometryCache
`find_node_types(graph, "GetDuration")` devuelve **dieciséis** ids distintos. Escribir
`Components|GeometryCache|GetDuration` sobre un `SoundBase` falla con *"Could not connect pin PadSound to
self"* — el mensaje **nombra el pin de destino**, que es la pista de qué sobrecarga agarró.
El de sonido es **`Class|SoundBase|GetDuration`**.
⚠ Y ojo: el `read_graph_dsl` de `BP_Sequencer_SC.Boot` **imprime** `Components|GeometryCache|GetDuration`
sobre su `PadSound` — es el mismo mislabel de siempre. **Copiar un id desde un `read` es cómo se hereda
el bug.** Confirmar con `find_node_types` antes de escribir.


## 🔴 `SetActorLocation` sobre el PROPIO actor: el `read` lo muestra sin target, pero el target es POSICIONAL
El `read_graph_dsl` de `BP_ProtoSoul_SC.CarryBody` imprimía:
```
(Transformation|SetActorLocation (Math|Interpolation|VInterpTo ...))
```
— **un solo argumento**. Escribir eso falla con *"Could not connect pin **ReturnValue** to **self**"*:
`SetActorLocation` tiene `self` (Actor) como **primer pin posicional**, y el read lo omite porque es el
propio actor. La forma escribible es con keywords:
```
(Transformation|SetActorLocation :self self :NewLocation (...))
```
👉 Ojo con la asimetría: los **getters** sobre sí mismo sí se escriben pelados
(`(Transformation|GetActorLocation)`, `(Transformation|GetActorTransform)`). Son los **setters** los que
piden el target. **El nombre del pin en el mensaje de error dice exactamente qué se conectó mal.**

## 💡 `select` no puede elegir entre dos componentes de clases HERMANAS
`(select flag camara controladorDerecho)` falla con *"Could not connect pin MotionControllerRightAim to
**Option 0**"*: el nodo `Select` se tipa con la primera opción conectada, y `CameraComponent` y
`MotionControllerComponent` son hermanas, no compatibles. **Con dos controladores (misma clase) sí
funciona** — así elige mano derecha/izquierda `CarryBody`.
✅ La salida: **ramificar** (`if` con `else`) en vez de `select`, y llamar a la misma función desde las
dos ramas.

## ⚠ Un array del CDO puede NO poder escribirse en la instancia
`StepTimes` de [[BP_Director_Story]]: `set_properties` sobre el actor colocado devuelve
*"the following properties could not be set: StepTimes"* — con `StepTimes`, con `stepTimes`, con floats
explicitos. Se escribe en **`Default__BP_Director_Story_C`** y la instancia lo lee de ahí
(verificado: el `get_properties` de la instancia devuelve el valor nuevo).
👉 O sea: **si un `set_properties` sobre una instancia rebota, probar el CDO** — y después **leer la
instancia** para confirmar que efectivamente lo heredó. Es el caso inverso del gotcha habitual
("lo de la instancia le gana al Blueprint"): acá la instancia **no tenía override** y hereda.


## Cosecha 2026-08-27 (F4/F5 del cierre: constelación y exploración)

242. 🔴🔴 **Un `bind` de un getter de VARIABLE no es una foto: el getter se RE-EJECUTA en cada
     consumidor.** El compilador **copia el bytecode del nodo puro una vez por consumidor**
     (`bp-lean-construction` §g, `KismetCompiler.cpp:2898`), y un *Get Variable* es un nodo puro. Si entre
     dos consumidores hay un **`Set`** de esa misma variable, el segundo consumidor lee **el valor nuevo**.
     ```
     (bind _c (GetCursor))
     (SetCursor (+ _c 1))        ; <-- acá cambia la variable
     (CallFunction|SpawnStar _c) ; <-- _c NO es el viejo: re-lee y da Cursor+1
     ```
     **El caso:** `BP_Constellation_SC.GradualOne` se salteó la entrada 0 y pidió la 20 de un array de 20.
     **La firma en el log:** `Attempted to access index 20 from array 'Variants' of length 20` **y una serie
     de datos corrida un lugar** (los anillos arrancaban en la entrada 1 en vez de la 0). Compiló limpio
     con `warnings_as_errors`.
     ✅ **Regla: primero la llamada que LEE, después el `Set`.** Si de verdad hace falta una foto, guardala
     en otra variable antes de tocar la original.
     💡 Y el corolario de diagnóstico: **un off-by-one se confirma con los DATOS, no con la ausencia del
     warning** — acá lo que lo probó fue que la lista de anillos empezara en el valor equivocado.

243. ⚠ **Cambiar la CATEGORÍA de una variable cambia su path en el DSL.** `AimConeDeg` en `Default` es
     `Variables|Default|GetAimConeDeg`; movida a `A - Constelacion` pasa a ser
     `Variables|A-Constelacion|GetAimConeDeg`, y la vieja **deja de existir** ("does not exist").
     ✅ **Escribí los grafos primero y categorizá al final** (los nodos ya creados no se rompen), o usá la
     categoría definitiva desde el principio.

244. ⚠ **Los bools con prefijo `b` se ESCRIBEN distinto de como los IMPRIME el read.** El read muestra
     `(|SetbSkipMine true)` / `(|GetbDrawing)`; el **write** necesita
     **`Variables|<Categoria>|SetSkipMine`** — sin la `b`, con la categoría real, y con la normalización
     rara de mayúsculas: `bDebugBuildOnPlay` → **`SetDebugBuildonPlay`** (la `O` de "On" queda minúscula).
     ✅ Para averiguar el nombre exacto: `find_node_types` con el filtro `Variables|<Categoria>|Set`.
     (Corrige el §74, que decía que no se podían escribir: **sí se puede**, con el nombre real.)

245. ⚠ **`CallFunction|X` con parámetros va con KEYWORDS.** Posicional, el primer argumento se enchufa al
     pin **`self`**: *"Could not connect pin VOEnd1 to self"*. Y el keyword tiene que ser el **nombre real
     del pin**, que el propio error lista: `BP_SoulPicker_SC.Rearm` lo llama **`NewTag`**, no `ChosenTag`.

246. ⚠ **`add_to_scene_from_asset` no sirve para clases nativas** (`TargetPoint`, `PointLight`…):
     *"Could not load asset at path /Script/Engine.TargetPoint"*. Es **`add_to_scene_from_class`** con
     `actor_type`. El transform sigue sin aplicarse → setearlo después en el `rootComponent`
     (`relativeLocation` + `relativeScale3D`), como dice el bloque de transforms de `toolsets.md`.

247. ⚠ **`_StrictDict.get()` no acepta default.** `info.get('output_pins', [])` levanta
     `TypeError` — y esa excepción **dispara el Undo del editor** (§60). Usar siempre
     `d[k] if k in d else X`. (Ya estaba en el header de `clean_orphans.py`; volvió a morder al escribir
     una cirugía de nodos a mano.)

248. 💡 **Para reconstruir un trazo entero en UN frame hay que desarmar los filtros de tiempo.**
     `BP_DrawCanvas.AddPoint` exige `GetGameTimeInSeconds() - LastTime >= MinTime`; en una reconstrucción
     todos los puntos llegan en el mismo frame, así que con `MinTime > 0` **se caen todos menos los dos
     primeros**. `RebuildFrom` guarda `MinTime`, lo pone en 0 y lo restaura.
     🔑 Y el mismo truco sirve de **candado**: poniendo `SaveMaxPoints = 0` durante la reconstrucción,
     el `RecordPoint` que cuelga de `StorePoint` no entra → el dibujo del vecino **no pisa** la firma
     propia. Cero cambios en `RecordPoint`.

249. 💡 **Para meter trabajo por frame en un BP frágil, no toques su Tick: llamalo desde el Tick del
     OTRO.** El sensor tenía una cadena de `if` anidados por `Mode` en `TickMech` que no convenía tocar.
     En vez de agregarle un modo, `BP_Constellation_SC` llama a `Sensor.AimBeams()` desde **su propio**
     `EventTick` mientras explora. Mismo resultado por frame, cero cirugía sobre lo delicado — y de yapa
     el sensor queda con `Mode = -1`, así que su gatillo (`BeamGrabTry`) no se activa por accidente.

250. ⚠ **`remove_function_graph` → `add_function_graph` sin `compile_blueprint` en el medio devuelve
     `Nombre_0`.** Ya estaba anotado, pero falta la mitad importante: **el compile del medio FALLA**
     ("Could not find a function named X") porque los llamadores quedaron colgados. **Ese error es
     esperado y hay que dejarlo pasar**; al re-agregar la función con el nombre correcto, los nodos de
     llamada **se re-resuelven solos** (verificado en `GradualOne`, `AimBeamsBody` y `RunEnding`).

251. 🔴🔴 **`bStartAsleep` del CDO se aplica a todo lo que SPAWNEES, y el log no se entera.**
     `BP_ProtoSoul_SC` tiene `bStartAsleep = true` en el CDO (para que las 5 candidatas colocadas a mano
     nazcan dormidas). Cada ameba **spawneada** corre `Sleep()` en su `BeginPlay` → `bAppearing=false` y
     **escala del Body = 0**. Como `EnableHover(false)` deja a `ApplyHoverScale` sin escribir y
     `StepAppear` sólo corre con `bAppearing`, **nadie vuelve a tocar la escala: quedan invisibles para
     siempre**.
     💣 La constelación corrió **tres veces** logueando `cielo completo, estrellas = 20` con las 20 en
     escala 0. Todos los contadores daban bien porque contaban *actores*, no *píxeles*.
     ✅ **La regla es la de siempre (`verificar-estado-estable-no-spawn`), aplicada a lo visual: si el
     resultado es que algo SE VEA, la aserción tiene que medir el TAMAÑO, no la cantidad.** Quedó
     permanente en `BP_Constellation_SC.Report`:
     `(.x (Transformation|GetWorldScale (Class|BPProtoSoulSC|GetBody primera)))`.
     ⚠ Y el instrumento también hay que validarlo: el primer intento usó
     `Collision|GetActorBounds`, que en su forma de un solo valor devuelve **`Origin`** (una coordenada
     del mundo), no `BoxExtent`. Reportó "tamaño = 8015,1" — que es la X del punto. Los dos pines son
     `Origin` y `BoxExtent`; hay que sacarlos con el bind múltiple.

252. ⚠ **`SpawnActorFromClass` + un sistema de anclaje que lee la escala del destino = escala al
     CUADRADO.** Spawnear con `GetActorTransform(punto)` mete la escala del punto en el ACTOR; después
     `AnchorStep` escribe `Size` desde **ese mismo** `Scale3D` y lo aplica al `Body`. Resultado: escala
     0,35 pedida → **0,1225** real; escala 1,2 pedida → **1,44**.
     ✅ **Spawnear con `MakeTransform(location, rotation, VectorOne)`** y dejar que `Size` sea el único
     dueño del tamaño. Así "lo que escalo en el viewport es lo que veo", que es la regla de autoría de
     Beltrán.
     💡 Y el corolario de composición: en `BP_ProtoSoul_SC` el **anillo mide
     `RingRadius × (Size / RingSizeRef)`** = **83 cm × escala** de radio. Antes de repartir N amebas en
     el espacio hay que comparar ESO contra la separación, no el diámetro del cuerpo: 20 estrellas con
     escala 1,2 son anillos de **2 m** — con 80 cm de separación, un muro.

253. 🔴🔴 **Esconder un `WidgetComponent` NO libera su render target.** `SetVisibility(false)` deja de
     dibujarlo, pero la textura sigue reservada. Un panel de 1600×900 son **5,8 MB**; veinte, **115 MB** —
     inviable en el renderer móvil. La creencia contraria ("con una sola visible no se paga") es el
     supuesto natural y es falsa.
     ✅ **El patrón que sí funciona**: el componente vive en las N con **`WidgetClass = None`**, y el
     widget se crea al mostrar (`UserInterface|CreateWidget` + `UserInterface|SetWidget`) y se suelta al
     ocultar (`SetWidget` con el pin `Widget` vacío). **Un solo render target vivo, garantizado.**
     💡 Y la contracara que justifica quedarse en UMG: **el render target se paga cuando se REDIBUJA**,
     no por existir. Una tarjeta estática ya dibujada es un quad translúcido y nada más — no hace falta
     rehacerla con mallas (y rehacerla costaría el Designer, que es donde se autora mirando).

254. ⚠ **`Widget|SetText` es el de `RichTextBlock`.** El de un `TextBlock` común es
     **`Widget|SetText(Text)`** (con el sufijo). Escribir el primero contra un TextBlock falla al
     conectar el pin `self`.
     ⚠ Y las variables del **árbol de un Widget Blueprint** viven bajo **`Variables|<NombreDelWBP>|`**
     (`Variables|WBP_Portrait_SC|GetTitle`), **no** bajo `Variables|Default|`. `find_node_types` con el
     filtro `Variables|` las lista todas.

255. ⚠ **Cambiar la firma de una función y escribir su cuerpo en la MISMA tanda rompe a los llamadores.**
     `add_function_param` + `write_graph_dsl` seguidos dan
     *"Could not find a pin for the parameter X of F on F"* al compilar: el nodo de llamada todavía tiene
     la firma vieja. **`compile_blueprint` entre el cambio de firma y la escritura**, y otro después.
     (Es la misma familia del §511: la cirugía de firmas termina en compile explícito o queda muerta.)

256. ⚠ **`add_to_scene_from_class` / `add_to_scene_from_asset` fallan con PIE corriendo**:
     *"Cannot create actors while PIE is active"*. Como los `T()` envueltos lo tragan, el script sigue y
     el resto **sí** se aplica — hay que releer el estado antes de reintentar, o se duplican variables y
     grafos ("Param already exists!").

## 📸 Sacar capturas de lo que RENDERIZA el juego (receta, 2026-08-27)
El `CaptureViewport` de `EditorAppToolset` captura el **viewport del editor**, no la vista de PIE. Para
ver lo que ve el jugador:
```
1. StartPIE (PlayMode_InViewPort)
2. EditorAppToolset.CaptureEditorImage()      -> {mimeType, data:<PNG en base64>}
3. AssetTools.write_file(<ruta ABSOLUTA bajo VR_Test/Saved>/shot.txt, data)
4. base64.b64decode en local -> PNG
```
⚠ `write_file` sólo acepta **`.csv .html .json .md .py .txt`** y rutas dentro de
`VR_Test/Content` o `VR_Test/Saved` — de ahí el `.txt` con base64 adentro.
🔴 **El viewport de PIE tiene un FOV vertical de ~41°, contra los ~96° del visor.** Lo que en gafas cae
cómodo dentro del campo visual se sale del cuadro en PIE. **No rediseñes una composición espacial por lo
que se ve en la captura** — medí la posición en el mundo y calculá el ángulo.

## Cosecha 2026-08-28 — el paquete de la ameba

257. 🔴🔴 **Una composición espacial que se arma UNA VEZ se arma en el instante equivocado.**
     `BP_Portrait_SC.Show` arranca un viaje de 4 s (`PlaceSoul`) y **en el mismo frame** coloca el dibujo
     (`PlaceDraw`). O sea que todo se medía con el `Size` de ANTES del viaje: 0,02 (la ameba del HUD) en
     vez de 1,0. Los dos síntomas que reportó Beltrán — *"el dibujo se ve enano"* y *"la ameba se
     agranda"* — eran **el mismo bug visto desde los dos lados**.
     👉 **La cura no es colocar más tarde** (siempre hay otro momento en que el tamaño cambia): es que la
     composición sea **proporcional y se recalcule sola**. Anclas que llevan la escala del objeto +
     `AttachActorToComponent` = los offsets y los tamaños quedan **constantes en espacio local** y todo el
     conjunto sigue al padre sin recalcular nada.

258. ⚠ **`SetX` de una variable de OTRO Blueprint lleva el VALOR primero y el target segundo.**
     `(Class|BPSoundOrbSC|SetPlaced _orb true)` → *"Could not connect pin AsBP Sound Orb SC to Placed"*.
     Lo correcto es `(Class|BPSoundOrbSC|SetPlaced true _orb)`. Es **al revés** que una función normal
     (`Setup`), donde el `self` va primero. Y el read etiquetaba el nodo con la clase equivocada
     (`Class|BPIntroSequence|SetPlaced`, colisión de nombres): el id bueno lo da `find_node_types`.

259. ⚠ **`set_properties` sobre una instancia falla para las variables que NO son instance-editable**
     (*"the following properties could not be set"*). No es un bug: heredan del CDO, que es lo correcto.
     Al escribir valores en los actores colocados, setear **sólo** las editables — si el lote entero va en
     una llamada, una sola no-editable tumba las demás.

260. 💡 **Al reemplazar una interpolación exponencial por una temporizada, no hace falta una rama para
     "ya llegué".** Un `Lerp(desde, objetivoActual, smootherstep(t))` con `t → 1` devuelve exactamente el
     objetivo, así que **el mismo nodo hace el viaje y después el seguimiento rígido**. Es lo que resolvió
     el *"se viene muy rápido"* del gesto al corazón sin tocar el resto de `CarryBody`.

261. 🗑 **Una perilla que quedó sin lectores es una trampa, no un resto inofensivo.** Al pasar `CarryBody`
     a `CatchTime`, `CarrySpeed` dejó de leerse: Beltrán la habría buscado para ajustar la velocidad y no
     habría pasado nada. Antes de borrarla, **`grep -rl CarrySpeed` sobre `Content/`** (2 s) confirmó que
     sólo la nombraban el propio BP y el `.umap`.

262. 🔬🔬 **CON PIE CORRIENDO, `find_actors` devuelve los actores del MUNDO DE PIE** — el refPath trae
     `UEDPIE_0_` delante del nombre del mapa
     (`/Game/.../UEDPIE_0_L_SoulCharger.L_SoulCharger:PersistentLevel.BP_BioHub_C_0`). Y sobre ese actor,
     **`ObjectTools.get_properties` lee los valores VIVOS**.
     👉 Esto cambia el método de verificación: **para leer un valor en runtime ya no hace falta sembrar un
     `PrintString`, recompilar y filtrar el log.** Se arranca PIE, se listan los actores y se leen las
     variables — y se puede **muestrear en el tiempo** (varias lecturas con `time.sleep` dentro de un
     `execute_tool_script`) para distinguir un dato que **fluye** de uno **pegado**, que es justo lo que un
     print de una sola línea no distingue.
     Caso real: se confirmó la llegada del OSC del sensor real (`Calm` subiendo 0,344 → 0,445, `Heart`
     ~76 bpm, `SinceLastMsg = 0`) **sin tocar un solo nodo**.

263. 🔬🔬🔬 **EL LOG DEL VISOR SE BAJA CON `adb pull` — dejá de adivinar qué pasó en gafas.**
     El APK de Development escribe el log completo en el dispositivo:
     ```
     adb pull /sdcard/Android/data/<packageid>/files/UnrealGame/<Proyecto>/<Proyecto>/Saved/Logs/<Proyecto>.log
     ```
     (`adb shell ls` en esa carpeta lista además los `-backup-` de las corridas anteriores, con fecha.)
     Caso real: Beltrán reportó *"llegué al final y nunca reinició"*. El log traía el instante exacto —
     `STORY: step game time de 300.0` justo después del último VO — y con eso la causa quedó cerrada en
     dos minutos, **sin reproducir nada**.
     👉 Va **antes** de cualquier hipótesis sobre un bug de visor. Es el equivalente en device del
     `GetLogEntries` de PIE, y responde lo mismo: *dónde se quedó*, no *qué me imagino que pasó*.

264. ⏱ **No reuses el reloj de una etapa para un beat de transición.** El sub 12 del final llamaba a
     `StartStepTime()` — que toma `StepTimes[Room]`, y en la última sala eso son **300 s** — sólo para
     esperar un momento antes del fundido. De paso, esa función también hacía `SetStage(Sensor, Room)`,
     rearmando el modo dibujo en pleno cierre. **Un beat de transición quiere su propio timer y su propia
     perilla**, aunque parezca duplicación.

265. 🎯 **`ResetOrientationAndPosition` no se llama solo.** Con `SetTrackingOrigin(Stage)` el origen es el
     centro del Guardian, así que **el usuario aparece donde esté su cuerpo**, no en el PlayerStart — y al
     recargar el nivel dentro de la misma sesión de app eso no se corrige. En una obra sentada que se
     reinicia sola para el próximo usuario, el recentrado en el arranque **es parte del ciclo**, no un
     lujo. Y va **con un retardo**: en el frame del BeginPlay la pose del HMD puede no ser válida todavía.
     Pista para detectarlo sin gafas: si el proyecto tiene un botón "Reset Orientation" en un menú, es que
     alguien ya lo necesitó a mano.


## 🔁 Nunca gatear un filtro con su propia salida (2026-09-01, `BP_Sensor_Soul.UpdateLevel`)
Para que la esfera de la respiracion no se desinflara al sostener el aire, se freno la linea de base del
band-pass **cuando la senal estaba lejos del centro** — usando `|HorizBP|`, que **es la salida de ese mismo
band-pass**. Resultado: lazo de realimentacion positiva. Lejos del centro → base lenta → sigue lejos del
centro → la base sigue lenta. El sistema se **traba** en el regimen lento; el sintoma que reporto Beltran
fue *"ya no se achica, pero perdio sensibilidad... quedo un poco mas terco"*.

**El arreglo fue cambiar la ENTRADA del gate, no sus numeros:** la condicion pasa a ser el **movimiento**
(`|GeomHoriz − HFast|`, que solo depende del EMA rapido, aguas arriba del filtro modulado). Sin lazo.

👉 **Dos reglas que quedan:**
1. **La condicion que modula un filtro tiene que venir de aguas ARRIBA de ese filtro.** Si sale de su
   salida, hay lazo — compila, corre, y se manifiesta como "quedo terco" o "se traba", no como un error.
2. **Un umbral sobre una magnitud fisica del usuario va relativo a esa magnitud, no en unidades absolutas.**
   Acá el umbral de "quieto" es `MovAvg × K` (el movimiento tipico del propio usuario) en vez de un valor en
   cm. Es la misma leccion de `MinHAmp` (§ *"un umbral sobre un estadistico derivado se fija midiendo ESE
   estadistico"*), llevada un paso mas: cuando se puede, **eliminar el numero magico** en vez de medirlo.


## 🌫️ Un BP de marketplace puede re-crear su Material Dinamico CADA TICK (2026-09-01, `BP_EasyFog`)
Revisando `BP_EasyFog` (asset de Fab, usado en `/Game/TestMeshes`) para llevarlo a Quest, el hallazgo caro no
estaba en el material sino en el **EventGraph**:

```
(event EventTick (DeltaSeconds)
  (SetActorTickInterval ...) (SetActorTickEnabled ...)
  (|Raster_Translucency))          ; <-- y esta funcion hace:
                                   ;     CreateDynamicMaterialInstance(FogCard, 0, M_BP_EasyFog)
                                   ;     + ~25 Set*ParameterValue
```
O sea: **un MID nuevo por actor y por tick** (a `systemTickRatePerSecond` 60 = 60 MIDs/s por card), mas 25
seteos de parametros que **nunca cambian**. Es el patron tipico de un asset pensado para **editar en vivo en
el editor**: comodo ahi, basura pura en runtime — y en Quest se paga en CPU y en churn de memoria.

✅ **El arreglo no toca el BP ni el material**: poner **`systemTickRatePerSecond = 0`** en la instancia. El
propio grafo hace `SetActorTickEnabled(rate != 0)`, y `EventBeginPlay` + el ConstructionScript ya aplican todo
una vez. Cero cambio visual.

👉 **Regla:** ante cualquier BP de marketplace que se vaya al APK, **leer su `EventTick` antes de colocarlo**.
Buscar `CreateDynamicMaterialInstance`, `SpawnActor`, `GetAllActorsOfClass` y cadenas largas de
`Set*ParameterValue`: los assets de tienda los ponen en Tick para que el panel de detalles responda en vivo.

### Y lo que SI es del material, para Quest
- `M_BP_EasyFog` es **`BLEND_Translucent` + `MSM_DefaultLit` + `TLM_VolumetricDirectional`**. En movil no hay
  volumenes de iluminacion translucida, y una escena sin direccional ni skylight no le aporta **nada** al lado
  lit → en el dispositivo el fog se ve **solo por su Emissive** (que si esta cableado, via el param
  `Emissive Intensity`). 👉 Si hace falta bajar costo, **`MSM_Unlit` es casi gratis visualmente** y quita el
  sombreado translucido, que es lo mas caro que se puede poner en pantalla completa. **No se aplico**: cuando
  el objetivo es *juzgar el efecto*, cambiarle el shading model es hacerle juzgar otro efecto.
- ✅ **`floatPrecisionMode = MFPM_Full_MaterialExpressionOnly`** SI se aplico: el material anima con `Time`
  (wind + flowmap) y en fp16 el movimiento se corta a los minutos (ver la seccion de degradados animados de
  `materials-vr.md`). Cero cambio visual, protege la sesion larga.
- ⚠ Lo que domina el costo no es el shading model sino el **overdraw**: cards translucidos grandes en pantalla.
  Meta mide *"translucent rendering adds almost 80% more GPU time per frame vs masked"*. Presupuestar por
  **capas superpuestas**, no por cantidad de actores.


## 📺 "Estatica de lineas" en VR = una textura SIN MIPMAPS (2026-09-01, `T_mountainFog_01_mask`)
Beltran probo `BP_EasyFog` en el visor: *"veo como algo de estatica de lineas al mirar al fog. No se si sera
la textura."* Era la textura, y el defecto venia **del asset de fabrica**:

| | `T_mountainFog_01_mask` (Opacity) | `T_normalProxy_N` y `T_Flowmap_01_Directional` |
|---|---|---|
| `MipGenSettings` | 🔴 **`TMGS_NoMipmaps`** | `TMGS_FromTextureGroup` |
| `NeverStream` | 🔴 **true** | false |
| `CompressionSettings` | `TC_EditorIcon` (sin comprimir) | `TC_Normalmap` / `TC_VectorDisplacementmap` |

**La de opacidad era la unica sin mips de las tres** — o sea un descuido del vendor, no una decision de arte.

**Por que se lee como estatica y no como aliasing comun:** sin mips, una textura grande minificada sobre un
card a angulo rasante samplea un texel distinto por pixel, sin filtrar. En un monitor eso titila; en VR
**repta con cada micro-movimiento de cabeza Y cada ojo samplea distinto**, asi que el patron no fusiona y el
cerebro lo lee como ruido de television.

✅ **Arreglo:** `MipGenSettings = TMGS_FromTextureGroup` + `NeverStream = false`.
🔴 **Lo que NO se toco, a proposito:** `CompressionSettings` y `SRGB`. En una mascara de opacidad esos dos
definen **la curva de densidad** del efecto: cambiarlos "para dejarlo prolijo" le cambia el look al artista.
(Y sin comprimir es lo mejor contra el bandeo de 8 bits en un degradado suave — ver la seccion de degradados
animados de `materials-vr.md`.)

⚠ **Costo aceptado:** con mips el efecto se ablanda a distancia. Ese es el intercambio del antialiasing.

👉 **Regla al traer cualquier asset de tienda a Quest: auditar las texturas ANTES de culpar al material o al
shader.** El chequeo barato es comparar las texturas del MISMO asset entre si — la que difiere del resto es
la sospechosa. `MipGenSettings`, `NeverStream`, `LODGroup` y `CompressionSettings` en una sola llamada de
`get_properties`.

💡 **Si la estatica sobrevive a los mips**, las dos palancas siguientes, en orden:
1. **`View Angle Fade`** (parametro de `BP_EasyFog`, hoy en 0): desvanece el card a medida que se pone de
   canto — que es justo donde un fog card muestra su propia geometria y peor aliasea.
2. **Dither**, si al mirarlo de cerca son **bandas anchas y suaves** en vez de ruido fino: ahi el problema es
   cuantizacion a 8 bits, no sampleo, y la receta esta en `materials-vr.md` (secuencia R2, ~6 instrucciones,
   sin textura). Son diagnosticos distintos con la misma queja: **ruido fino = sampleo · bandas anchas = bits.**

---

## Orientar un mesh nuevo: la silueta MIENTE sobre la palma (2026-09-02)

Al montar `Hand_Low` en el pawn hubo que calcular la rotacion que lleva el marco local del mesh
nuevo al del que ya estaba bien (`SKM_MannyXR_*`). El metodo fue: colocar cada mesh en el nivel,
fotografiarlo con `CaptureViewport` desde ejes conocidos, leer de ahi **direccion de los dedos**,
**normal de la palma** y **lado del pulgar**, y componer las matrices.

**El eje de los dedos salio bien. La normal de la palma salio al reves, y la mano quedo con el
pulgar hacia abajo.** Lo cazo Beltran en un segundo mirando el editor.

🔴 **La causa:** los meshes se fotografiaron **en negro contra el cielo** (una malla dinamica lejos
de cualquier volumen de lightmass recibe una muestra de luz negra). Y **una silueta no tiene
profundidad**: la palma y el dorso de una mano dan **exactamente el mismo contorno**. Todo lo que
se dedujo del "lado hacia donde sobresale el pulgar" era una interpretacion de una imagen que no
contenia ese dato.

✅ **El metodo que si funciona, y cuesta lo mismo:**
1. Poner **el mesh nuevo y el que ya esta bien** en el nivel, con **la misma rotacion que van a
   tener en su componente**.
2. Ponerles a los dos **un material que deje ver el volumen** (unlit emisivo sirve: no depende de
   que haya luces). Con siluetas negras no se puede.
3. Mirar **donde cae el pulgar** en cada uno. Si coinciden, la rotacion es correcta.

👉 **La silueta sirve para el eje longitudinal (dedos, largo, "hacia donde apunta") y para nada mas.**
Cualquier eje que dependa de saber que cara estamos viendo necesita sombreado.

💡 Y el corolario de composicion: cuando la orientacion sale girada **180° sobre el eje largo**, la
correccion es **un giro de 180° sobre ese eje ANTES del align** (para una mano: `Yaw 180` local, que
mueve palma y pulgar juntos). No se arregla tocando el Roll final — eso tambien gira los dedos.

### 🔴 Y la lateralidad tampoco se lee mirando: se MIDE
La segunda pasada tambien salio mal — con el pulgar arriba, pero **las dos manos cambiadas de
lado**: `Hand_Low` era una mano **DERECHA** y se la habia dado por izquierda. Mirandola no se
resolvia, porque una vez que alineas los dedos y el pulgar de un mesh de quiralidad equivocada,
lo unico que delata el error es **la palma**, que es justo lo que peor se ve.

✅ **Se mide con el producto mixto de tres vectores del propio esqueleto** (en un frame
**right-handed**: Blender sirve, Unreal NO — es left-handed y el signo se invierte):
```
f = punta_del_medio − palma          (direccion de los dedos)
w = nudillo_menique → nudillo_indice (a lo ancho, hacia el lado del pulgar)
t = punta_del_pulgar − palma
det[f, w, t] = f · (w × t)        →   NEGATIVO = mano DERECHA · POSITIVO = izquierda
```
🔴 **Correr siempre un control positivo primero** (una mano sintetica de lateralidad conocida,
tres vectores a mano), porque el signo depende de la convencion del frame y equivocarse es gratis:
```
control DERECHA   det = −0.2000
control IZQUIERDA det = +0.2000
Hand_Low          det = −1.13e−07   → DERECHA
```
Los huesos se leen sin tocar la sesion del usuario: `blender.exe --background --factory-startup
--python <script>` sobre el FBX de origen, imprimiendo `armature.matrix_world @ bone.head_local`.
⚠ El MCP de Blender tiene una variante `_for_cli`, pero **falla si `BLENDER_PATH` no esta seteado**
(el caso de esta maquina) — invocar el `.exe` directo desde Bash sale igual y es mas controlable.

⚠ **Y ojo con transferir angulos de Blender a Unreal:** los dos importadores de FBX aplican
conversiones de ejes distintas, asi que el marco local **no coincide**. Lo unico que sobrevive el
viaje es la **quiralidad** (ningun importador espeja la geometria). Medi la lateralidad en Blender;
los angulos, en Unreal.

## 🔴🔴 Cosecha 2026-09-03 — cuatro errores de cirugía que COMPILAN LIMPIO (banco de pruebas de mandos)
Una jornada entera perdida; ninguno de los cuatro dio error ni warning. El patrón común: **el `read_graph_dsl` los muestra como si estuvieran bien.**

### §A. Un argumento posicional en una función MIEMBRO cae en el pin `self`
`(Input|EnableInput pc)` → el PlayerController quedó en el pin **`self`** (que espera el *Actor*) y el pin `PlayerController` **vacío**. Tipa porque un PlayerController *es* un Actor. Efecto: el actor nunca entra en la pila de input, y el gatillo no llega jamás.
→ La regla del DSL *"sobre el propio actor: OMITIR el target"* **no aplica cuando la función tiene su propio parámetro de objeto**. Para estos casos, escribir el target explícito: `(Input|EnableInput self pc)`, como hace `BP_Sensor_Soul.EnsureInput`.

### §B. Un pin de exec de ENTRADA acepta varias conexiones — reconectar no desconecta
Al mover una llamada de lugar dejé el cable viejo puesto y el `BeginPlay` se cerró en **bucle infinito** (cada 0,2 s por el Delay que tenía en medio). El `read_graph_dsl` lo imprimió como una **cadena lineal**. Se vio en el log: el print de init repitiéndose ~5 veces por segundo, y cada vuelta re-spawneaba el actor que el init crea.
→ Al reubicar un nodo en una cadena: `break_pins` del cable viejo **explícito**, y después `get_node_infos` de los dos extremos. Un `connect_pins` sobre un exec de entrada **suma**, no reemplaza. (Sobre un pin de DATOS sí reemplaza — son reglas distintas.)

### §C. En una llamada a función propia, el pin 1 es `self`: el primer parámetro es el **2**
`set_pin_value(index 1)` escribió sobre `self` y el parámetro quedó en su default. El síntoma fue una compuerta por mano que nunca se abría.
→ Nunca adivinar el índice: `get_node_infos` del nodo creado y leer el `name` de cada pin.

### §D. El `read_graph_dsl` atribuye funciones PROPIAS a otros Blueprints
Mostró `Class|BPSensorSoul|DrawPress` y `Spline|AddPoint` para llamadas locales perfectamente correctas (`self` = *Self Object Reference*). Es el gemelo benigno de la colisión real de nombres (§ colisión de nombres de función) — y obliga a chequear: **el que decide es el TIPO del pin `self`**, no la etiqueta del read.

### ➕ Y dos sobre INSTANCIAS del nivel (complementan la regla del struct)
- Sobre un **componente** de una instancia, un struct completo aplica **solo el primer campo** (`relativeScale3D` quedó en `(0.02, 1, 1)`: 2 cm de ancho, 1 m de alto). Campo por campo.
- Sobre una **variable del actor**, campo por campo **CORROMPE** el struct (`LinearColor` con `b = -nan`). Ahí va el struct **completo de una vez**.
- **`BodyInstance.collisionEnabled` no entra por ninguna de las dos vías en una instancia** (devuelve éxito, sigue en `QueryAndPhysics`). La salida limpia y de un solo nodo: **`SetActorEnableCollision(false)` en el `BeginPlay`**, que además cubre todos los componentes del actor — útil para cumplir §239 (todo lo que viaja pegado al pawn nace `NoCollision`).


## Cosecha 2026-09-03 — templates SCS vs instancias (nació de hornear los offsets de BP_ControllerRig)
- **Escribir el template de un componente del BP SÍ funciona y persiste** (`ObjectTools.set_properties` sobre `/Game/BP_X.BP_X_C:<Comp>_GEN_VARIABLE`, sobrevive al compile). Es LA vía para que un valor autorado pase a ser default de fábrica.
- 🔴 **Pero una instancia YA COLOCADA captura los valores del template en el momento del spawn**: cambiar el template después no la actualiza, y `reset_properties` sobre la instancia vuelve a **lo capturado al colocarse**, no al template nuevo. Para que una instancia adopte el template actualizado: **reemplazar el actor** (borrar el propio y re-colocarlo — jamás borrar actores de Beltrán sin preguntar).
- 🔴 **`set_properties` multi-campo sobre el componente de una INSTANCIA registra el delta a medias**: escribimos loc+rot completos y tras el rerun del Construction Script solo sobrevivió la `x`. Offsets de instancia se autoran con el gizmo (el editor sí registra bien), o se hornean en template/CS.
- **El literal de un pin Rotator es "Pitch, Yaw, Roll"** (verificado con el espejo del rig: "90, 10, 0" → pitch 90, yaw 10).

### ➕ Cosecha 2026-09-03 bis — semántica real de execute_tool_script + transform de actores BP (sesión de light shafts)
- 🔴 **Un error de TOOL dentro de `execute_tool_script` NO es atrapable con `try/except BaseException`** — el wrapper de `safe_script.py` solo atrapa errores de PYTHON. Medido: un `connect_expressions` con pin inexistente hizo que el resultado entero del script se reemplazara por ese error… pero **el script siguió corriendo hasta el final** (los materiales creados DESPUÉS del error existían). Consecuencias: (a) un script "fallido" puede haber hecho TODO su trabajo → **inspeccionar el estado antes de re-correrlo**, o se duplica; (b) el `ERRS` del wrapper nunca llega si falla un tool → verificar por lecturas separadas; (c) los errores de VALIDACIÓN de parámetros (p.ej. refPath sin `.Nombre`) también matan el reporte. Un error de Python (p.ej. `.get()` con default, que el sandbox no soporta) SÍ corta la ejecución en esa línea.
- ✅ **`ActorTools.set_actor_transform` SÍ funciona sobre instancias de Blueprint** (verificado 2026-09-03 con read-back de los 9 valores). La nota del 2026-08-11 ("devuelve true y no mueve nada") se midió sobre StaticMeshActors crudos. Para actores BP es LA vía limpia de poner el transform completo — y esquiva la trampa del struct multi-campo sobre el root component (que en un actor BP aplica solo el primer campo: loc `(x, 0, 0)`, scale `(x, 1, 1)`).
- 💡 **Escribir una variable instance-editable de una instancia con `set_properties` SÍ re-corre el Construction Script** (verificado: `BeamColor` y `WobbleAmount` de `BP_LightShaft_SC` cambiaron el render en la captura siguiente). Es la forma barata de ajustar knobs de instancias colocadas — el struct de la variable va COMPLETO de una vez (regla de la cosecha anterior).

### ➕ Cosecha 2026-09-03 ter — sesión de light shafts v7 (DSL, overloads, MPC)
- 🔴 **CORRECCIÓN de la cosecha bis:** el `try/except BaseException` del wrapper SÍ atrapa los errores de tool y la ejecución SÍ continúa — lo que pasa es que **el plugin REEMPLAZA el resultado del script con el primer error de tool aunque Python lo haya atrapado**. Consecuencias prácticas iguales (el `ERRS` nunca se ve si hubo error; el trabajo se hizo; inspeccionar antes de re-correr), pero los `if not ok` de fallback SÍ funcionan.
- 🔴 **`remove_function_graph` + `add_function_graph` del MISMO nombre devuelve `Nombre_0` si el nodo de llamada sigue vivo** — y a veces incluso sin él. Receta que funciona: `delete_node` del CallFunction en el UCS → `remove_function_graph` → **`compile_blueprint` (purga el nombre)** → `add_function_graph` → nombre limpio. Sin el compile intermedio puede volver sufijado.
- **Los `elif` del DSL se ENCADENAN ANIDADOS**, no como hermanos: `(if c0 s0 (elif c1 s1 (elif c2 s2)))`. Dos elif hermanos fallan con *"(elif) must be the last form"*.
- ✅ **El overload exacto de una función duplicada SÍ sale con `create_node` + `declaring_class`** (la salida que promete la trampa #3 del DSL, ahora VERIFICADA): `create_node {type_id: 'Rendering|Material|SetScalarParameterValue', declaring_class: '/Script/Engine.KismetMaterialLibrary'}` crea el **K2Node_CallMaterialParameterCollectionFunction** correcto (pins: Collection/ParameterName/ParameterValue). El pin `Collection` se llena con `set_pin_value` y el path del asset. Así se construyó `PushMPC` de [[BP_LightShaft_SC]]. ⚠ El write DSL elige overload al azar entre los dos ids idénticos — para MPC siempre cirugía.
- ✅ **Los parámetros de un MaterialParameterCollection se escriben por `ObjectTools.set_properties`** con los arrays completos: `{"scalarParameters": [{"parameterName": ..., "defaultValue": ...}]}` y `vectorParameters` (defaultValue = LinearColor). Verificado leyendo de vuelta (los GUID los pone el motor).
- 🎨 **Un emisivo aditivo MUY sobresaturado vira a ROSA/violeta en el tonemapper** (color cálido (1.5, 0.8, 0.4) × brightness 5 → los canales clipean desparejo). Si un disco/glow cálido sale rosa, la palanca es BAJAR la intensidad, no tocar el color. Rango sano del `SourceGlowIntensity` del haz: ≤0,8.
- 🐚 **PowerShell 5.1: `$r` como nombre de variable dentro de un bloque con arrays se corrompió a Object[]** en un script de generación de OBJ (op_Multiply sobre array). No se diagnosticó; la salida fue reescribirlo en Python (`python` 3.12 SÍ está en el PATH de esta máquina). Para generar mallas por OBJ: `scratchpad/gen_shaftbox.py` es la plantilla (28 puntos × 21 anillos, vn suaves, vt con costura).
- 🌀 **`MaterialExpressionSine` multiplica la entrada por 2π** (su `period` default = 1 significa "un ciclo por unidad de entrada", NO radianes). Toda frecuencia calculada en rad/cm sale ~6,28× más rápida: un anillo láser procedural se rompió en PUNTITOS/dientes por esto (el síntoma engaña — parece precisión o aliasing). Fix: `period = 6.283185` en el nodo y las entradas quedan en radianes. Vale para Sine y Cosine.
- 💡 **La línea de láser sobre un objeto receptor = distancia al CASCO del cono, no banda de altura**: `|d_radial − r(t)| < ancho` dibuja la curva de intersección sobre CUALQUIER superficie (tapa, cara, piso) con la perspectiva correcta gratis — la banda por world-Z solo sirve para el plano del piso. Implementado en `M_BeamReceiver_SC` con wobble propio (2 senos world-space, `RingWidth/RingWobble/RingFreq`).
- 🧱 **Un line trace que NACE dentro de un basic shape del motor devuelve el punto de arranque** (el colisionador simple es una CAJA SÓLIDA — un "cuarto" hecho de un cubo escala 60× tiene todo su interior como overlap inicial). Fix: **`bTraceComplex=true`** — traza contra los triángulos del render mesh y el interior queda hueco. Medido 2× en `ResolveFloor` de [[BP_LightShaft_SC]] (primero pescó el techo a 650, después el arranque a 602).
- 🔁 **Para re-correr el Construction Script de una instancia por MCP: toggle de un bool instance-editable** (`set_properties` false → true). Setear el MISMO valor no dispara el rerun; mover OTRO actor tampoco.
- 🪞 **El importador de OBJ ESPEJA el eje Y: las normales `vn` llegan con la Y invertida.** Un tubo con normales analíticas outward llegó con caras negras — y el culpable río abajo es que **el nodo Fresnel SATURA el dot ANTES del 1−x**: con la normal volteada, dot<0 → saturate→0 → 1−0=1 → OneMinus=0 EXACTO, y un Abs posterior no rescata nada (la información murió en el saturate). Fix en el origen: emitir el OBJ con `vn (nx, −ny, nz)`. Verificado A/B con dos variantes importadas lado a lado (la de −nx quedó con normales totalmente hacia adentro = confirma espejo Y, no X).
- 🧵 **Malla para haz con caras planas: SUBDIVIDIR los flats.** Sin vértices intermedios en las caras, el WPO del wobble solo dobla en las esquinas (pliegue negro duro entre caras) — la sección del `SM_ShaftBox` v2 lleva 6 segmentos por lado + 31 anillos. En Quest los polígonos extra son gratis (fill-bound).
- ℹ️ **Precisión sobre los errores de tool en `execute_tool_script`**: "Unknown tool" (y otros errores de RESOLUCIÓN) sí llegan al `except` y al `ERRS`; los errores de EJECUCIÓN del tool (pin inexistente, refPath malo) son los que pisan el reporte. Distinguirlos: si `errores` volvió poblado, el reporte es confiable.
- 🚫 **No hay tool para metadata de variables BP (UIMin/UIMax/sliders)** — `set_variable_metadata` no existe en BlueprintTools. Los rangos de sliders se fijan a mano en el editor; documentarlos en el tracker del BP.

### ➕ Cosecha 2026-09-04 — MIDs rancios, capturas rancias y noise post-WPO
- 🔴🔴🔴 **Un MID creado ANTES de que su material ganara un parámetro NUNCA lo honra.** `SetScalarParameterValueOnMaterials` (y `SetScalarParameterValue`) guardan el valor en `scalarParameterValues` del MID —**se lee de vuelta perfecto**— pero el render proxy lo ignora, porque el set de expresiones cacheado del MID es el que tenía el padre en el momento de crearse. `CreateDynamicMaterialInstance` **reutiliza** el MID existente en cada rerun del Construction Script, así que el toggle de un bool NO lo renueva. Síntoma exacto: *"el BP empuja el valor correcto, el MID lo tiene, y en pantalla no cambia nada"*, mientras que **un actor recién colocado SÍ funciona**. Diagnóstico barato: colocar un actor de prueba nuevo — si en él funciona, es esto. **Fix: recargar el nivel (`SceneTools.load_level`) o reabrir el editor.** Costó media sesión con `AspectX`/`BoxAngle` de `M_ApertureGlow_SC`.
- 🔴 **`CaptureViewport` con `captureTransform: false` devuelve un FRAME RANCIO**: `SetCameraTransform` + capturar da la imagen ANTERIOR (dos encuadres distintos salieron píxel-idénticos). **Pasar el transform DENTRO de `captureTransform`** (`{location, rotation, scale}`) y ahí sí redibuja. Tras `load_level` hay que esperar (~25 s) o la captura sale negra/marrón uniforme (shaders compilando).
- ⚠ **`CaptureAssetImage` devuelve `{data, mimeType}` en la raíz**, no `{image: {data}}` como `CaptureViewport`.
- 🔴 **`read_graph_dsl` imprime los getters de bool sin categoría y con la `b`: `(|GetbFloorFollowsBeam)` — pero el type_id que acepta `write_graph_dsl` es `Variables|D-Piso|GetFloorFollowsBeam`** (con categoría y SIN la `b`). Copiar el token del read falla con *"El nodo no pudo crearse / X does not exist"*. Confirmarlo siempre con `find_node_types`.
- 💡 **Agregar una función nueva + un solo `create_node` al final de la cadena del UCS es MUCHO más barato que rehacer una función existente** (`write_graph_dsl` duplica; el ciclo remove/compile/add es frágil). Si el cambio es *aditivo*, escribirlo en un grafo nuevo y engancharlo al `then` del último nodo.
- 🌊 **En el pixel shader `WorldPosition` es POST-WPO.** Un material que desplaza por `noise(WorldPosition)` y además colorea por el mismo `noise(WorldPosition)` está coloreando en la posición YA desplazada → el campo de color se pliega y aparecen **parches/pliegues con borde duro** en las pendientes. Fix: **`VertexInterpolator`** entre el noise y el consumo de píxel — mismo valor que usó el vértice, interpolado suave, y de paso el noise pasa a ser **por-vértice** (regalo enorme en Quest). El `DepthFade` de la opacidad tiene que quedarse por píxel.
- ⚠ **`find_node_types` con filtros genéricos (`"Max"`) devuelve MILES de líneas** — un solo filtro flojo se comió ~18k tokens. Filtrar por el nombre exacto o por prefijo de categoría.
- ⚠ **`bHiddenEdTemporary` no es escribible por `set_properties`.** Para sacar un actor de en medio en una captura sin tocar el nivel, apagarlo por un parámetro suyo (p.ej. `Density = 0` en la nube) y restaurarlo en el mismo script.
- ⚠ **`mcp__unreal__call_tool` usa el campo `arguments`** (recordatorio: con `parameters` la llamada llega VACÍA y el error parece un problema de schema del tool destino).
- 🔴🔴 **Nunca identificar actores por substring de su NOMBRE DE CLASE.** `add_to_scene_from_asset(name=...)` NO nombra el actor: el nombre interno queda `StaticMeshActor_N` (con índices reciclados de actores borrados), y el `name` que se pasó va al **label**. Filtrar por `"StaticMeshActor" in refPath` para "encontrar mis cubos de prueba" agarró también los del usuario y les movió el transform. **La identificación segura es `ActorTools.get_label`** (o guardar el refPath que devolvió el spawn, que es lo más seguro de todo). Pasó el 2026-09-04 y desplazó un actor de Beltrán.
- 🔴 **`SceneTools.load_level` se NIEGA si el nivel tiene cambios sin guardar** (*"the level has unsaved changes"*) y **no existe ningún tool de Undo** (probados `Undo`/`UndoTransaction`/`EditorUndo`/`ExecuteConsoleCommand`: ninguno existe). O sea: **por MCP no hay forma de revertir un cambio de nivel.** El único remedio es que el usuario reabra el nivel descartando cambios, o Ctrl+Z a mano. Corolario práctico: **guardar los ASSETS por ruta explícita apenas estén listos** — así, si hay que descartar el nivel entero, el trabajo de materiales/BPs sobrevive.

## Cosecha 2026-09-04 ter — las firmas del MCP que costaron cinco round-trips (galería de efectos)

266. 🔴🔴🔴 **`ObjectTools.set_properties` es `(instance, values)` y `values` es un STRING JSON. `get_properties` es `(instance, properties)` con `properties` una LISTA de nombres.** Los dos toolsets NO comparten nomenclatura, y este archivo tenía documentado `set_properties(<objeto>, '{...}')` sin nombrar el parámetro — así que se asumió `object`/`properties` y **las ~40 llamadas de un material entero fallaron**.
    🚩 **Lo venenoso es cómo se ve el fallo:** el material compiló igual (con los defaults de fábrica), y el error que llegó fue *"Arithmetic between types float3 and float2 are undefined"* — un error de **grafo**. Se pierde el tiempo revisando el cableado, que estaba perfecto: lo que faltaba eran los `ComponentMask` (quedaron en su default RG = float2) y el `blendMode`.
    ✅ **La verificación que lo cazó en una llamada:** leer de vuelta tres cosas cualesquiera que se creía haber seteado (`get_properties` del material, de una máscara y de un parámetro escalar). Salieron `MSM_DefaultLit`, `r:true,g:true` y `parameterName:"Param"` — o sea, **nada se había aplicado**. Es la regla "declarado ≠ aplicado" otra vez, y el costo de saltearla fueron dos ciclos de compilación en falso.
    💡 Ante la duda sobre una firma, **mandá la llamada mal a propósito una vez**: el error del plugin imprime el **schema JSON completo** de la función, con los nombres y tipos exactos. Es la forma más barata de averiguarla.

267. 🔴🔴 **`execute_tool_script` devuelve los errores acumulados EN LUGAR de tu `return`, pero el script SÍ corrió hasta el final.** Un `<error>` de vuelta **no significa** "no pasó nada": significa "alguna llamada falló y encima perdiste tu valor de retorno".
    Caso real: la tanda que creaba 73 expresiones devolvió 74 líneas de error (una por nodo) y pareció un fracaso total; la corrida siguiente devolvió *"already exists"* y también pareció fallar — pero `get_expressions` mostró **73 nodos ya creados**. Sin ese chequeo se habrían duplicado.
    ✅ **Regla: después de todo `execute_tool_script` que vuelva con `<error>`, correr un script SOLO DE LECTURA que cuente lo que se creó, antes de reintentar nada.** Reintentar a ciegas duplica.
    ✅ Y el corolario para el `try/except`: sirve para que el script **siga** (y no dispare el Undo de §163), no para ver el resultado.

268. ⚠ **`add_expression` quiere la ruta de clase COMPLETA**: `/Script/Engine.MaterialExpressionMultiply`, no `MaterialExpressionMultiply`. El error es explícito (*"is not a valid object path"*) pero llega una vez por nodo.
    ⚠ Nombres de pin de expresiones, verificados con `get_expression_input_names`: los **unarios se llaman `"None"`** (`OneMinus`, `Abs`, `Saturate`, `Floor`, `Frac`, `Sine`, `ComponentMask`), `Power` es `Base`/`Exp` (no "Exponent"), `DepthFade` es `Opacity`/`FadeDistance`, `LinearInterpolate` es `A`/`B`/`Alpha`. La **salida** de casi todo es `""`; `LocalPosition` da `XYZ`/`XY`/`Z` y un `VectorParameter` da `RGB`/`R`/`G`/`B`/`A`/`RGBA`.
    ⚠ `bUseFullPrecision` **no es escribible**: la propiedad viva es **`floatPrecisionMode`** = `MFPM_Full_MaterialExpressionOnly`.
    ⚠ `collisionEnabled` tampoco se setea directo en un componente (vive en `BodyInstance`).

269. ⚠ **Spawnear y mover: `SceneTools.add_to_scene_from_asset(asset_path, name, xform)`** (no existe `spawn_actor`, ni `get_all_actors` — para contar actores es `find_actors(name='', tag='', collision_channels=[])`), y **`ActorTools.set_actor_transform` usa `xform`**, no `transform` (que sí es el nombre en `EditorAppToolset.SetCameraTransform`). `AssetTools.write_file` usa **`file_path`** + `content`.

270. 💡 **Cambiar una variable del CDO no re-corre el Construction Script de los actores ya colocados.** Para ver un default nuevo en el mundo: `remove_from_scene` + `add_to_scene_from_asset`. Es instantáneo y mantiene el canario de actores en cero — pero **solo con actores propios**, nunca con los del usuario (§ regla de no tocar el world).

271. 🔴🔴 **El `BeginPlay` de OTRO actor puede pisar lo que vos le hiciste desde el tuyo.** `BP_GalleryDirector_SC` armaba sus dos `BP_MenuButton` en su propio `BeginPlay`; el resultado medido en PIE fue `bArmed = true` **y `bHidden = true`** — armados e invisibles. Motivo: **el `EventBeginPlay` de `BP_MenuButton` termina con `SetActorHiddenInGame true`** (en la obra el botón no existe hasta que la intro lo arma), y corría *después* del director.
    ✅ **Lo que sobrevive va en el PRIMER TICK, no en `BeginPlay`** — un one-shot con un bool (`bArmedOnce`) no depende del orden de inicialización entre actores ni de adivinar un `Delay`.
    💡 Lo que lo cazó en una sola corrida fue **leer las dos banderas juntas**: `bArmed` sola decía "todo bien", `bHidden` sola decía "está escondido"; el par decía "alguien lo escondió DESPUÉS de que lo armé", que es el diagnóstico completo.

272. ⚠ **Un test que no mueve nada no prueba que algo se mueva.** La primera verificación de la galería midió los botones en la estación 0 — que es justo donde estaban colocados, así que no distinguía "viajan con el director" de "están quietos ahí". La prueba real necesitó una perilla `StartAt` para arrancar en la estación 3 y ver los botones a 90 m de distancia. 🚩 Regla: **antes de festejar una medición, preguntarse qué valor daría si el sistema estuviera roto.** Si da lo mismo, la medición no dice nada.

273. 🔴🔴🔴 **Rearmar un botón en el mismo frame en que disparó = repetición infinita mientras el gatillo siga apretado.** `BP_MenuButton` con `HoldTime = 0` dispara **el primer frame con gatillo + mano cerca**; si el consumidor limpia `bDone` y llama `Arm` enseguida, vuelve a disparar al frame siguiente. En la galería eso fue **una estación por frame**: *"si mantengo el trigger cambio infinito de lugares y queda la cagada"*.
    ✅ **Toda acción disparada por un botón sostenible necesita un gate de SOLTAR**, no un cooldown por tiempo: un bool `bWaitRelease` que se prende al disparar y solo se apaga cuando `bTrigHeld` está en false en los dos botones. Y arrancar en `true`, por si la sesión empieza con el gatillo apretado.
    ⚠ Antes de gatear con una bandera de otro Blueprint, **verificar que esa bandera se siga actualizando en el estado en que lo dejás**. Acá se leyó el grafo de `BP_MenuButton` y se confirmó que `IA_Shoot_*` escribe `bTrigHeld` **directo** (`Started`→true, `Completed`→false) sin pasar por `bArmed`. Si hubiera pasado por `bArmed`, desarmar habría congelado `bTrigHeld` en true y el sistema quedaba **trabado para siempre** — un bug peor que el original.
    🚩 La forma general: **si una entrada es sostenible, "disparó" y "puede volver a disparar" son dos estados distintos.** Un solo bool `bDone` no alcanza.

274. 🔴🔴🔴 **`GetActorOfClass` + `IsValid` = una dependencia de nivel INVISIBLE. Es la causa raíz de "lo llevo a otro nivel y no funciona".**
    `BP_MenuButton` resuelve su audio y su háptica con `GetActorOfClass(BP_AudioHub)` / `GetActorOfClass(BP_HapticHub)` en `BeginPlay`, y después envuelve el uso en `IsValid`. En un nivel sin esos actores **no crashea, no loguea, no avisa: se calla**. El botón se ve, hoverea, dispara — y le faltan la mitad de sus sentidos. Lo mismo con `CastToBP_VRPawn_SC(GetPlayerPawn(0))` para sacar las manos: con otro pawn, `HandL`/`HandR` quedan nulos y el botón no detecta nada, sin un solo error.
    🚩 **Es el patrón, no un caso.** Beltrán (2026-09-04): *"es como si hubieran quedado encadenados y funcionaron de milagro en el persistent de Soul Charger"*. Soul Charger es la v1 de 30 experiencias: si un BP no se puede mudar, no hay serie.
    ✅ **La regla que lo corta: todo Blueprint reusable declara sus REQUISITOS DE NIVEL en su tracker** — qué actores singleton busca, qué clase de pawn asume, qué IMC necesita — y **al mudarlo, lo primero es leer en PIE las referencias que cacheó** (`get_properties` de `AudioRef`/`HapticRef`/`HandL`/`HandR`). Cuatro lecturas contra horas de adivinar.
    ✅ **La verificación positiva primero, la mecánica después.** Antes de probar una mecánica en un nivel limpio: PIE, leer las refs cacheadas, confirmar que ninguna es nula. Si alguna lo es, falta un actor en el nivel — no hay bug que arreglar.

275. 🔴🔴 **Dos mecánicas que escuchan el MISMO input se disparan JUNTAS, y el síntoma aparece lejos de la causa.** En `/Game/TestMeshes` convivían los botones de la galería y `BP_ControllerRig` (la mecánica de dibujo): ambos usan el gatillo. Cada apretada de NEXT **también empezaba un trazo**, y como el pawn se teletransporta 300 m en medio del trazo, la cinta procedural se estiraba de una estación a la otra — se veía como **un láser azul recto saliendo por detrás del botón**, que no se parece en nada a "estoy dibujando".
    ⚠ Me costó dos diagnósticos equivocados (el teleport trace del VRTemplate, después el componente `Ring` del botón) hasta que Beltrán dijo *"está activada la mecánica de dibujo, eso es el láser"*. **El dueño del proyecto sabe qué hay en su nivel; preguntar "¿qué más está activo acá?" hubiera sido el primer paso, no el último.**
    ✅ Antes de traer una mecánica a un nivel que ya tiene otra: **enumerar quién más escucha ese input**. Y preferir apagar con una perilla del propio BP (`bCanDraw = false`) antes que borrar actores — reversible con una casilla.

276. 🔴🔴 **Dos translúcidos NO se ordenan por profundidad de píxel: se ordenan por ACTOR.** Con la misma `TranslucencySortPriority` el motor decide por la distancia al **origen de los bounds**, así que una malla enorme centrada cerca de la cámara (el océano de nubes, escala 65) le gana a una losa que está objetivamente **mucho más lejos**. No es un bug del material ni del `DepthFade`: es el orden de dibujo.
    ✅ El lever es **`TranslucencySortPriority`** en el componente (más alto = se dibuja después = va encima). Expuesto como variable `SortPriority` en `BP_FogSlab_SC` (cat. *I - Orden*) y en `BP_CloudPlane_SC` (cat. *B - Orden*), empujada desde el Construction Script.
    🚩 Si algo translúcido "aparece delante de lo que no corresponde", **la perilla es esta, no el material**. Vale para velos, haces, nube y losa.

277. 🔴 **No resolver un pedido con una solución más "elegante" que la pedida.** Beltrán pidió que la losa de niebla se viera sobre el océano; yo empecé a meterle la niebla **adentro del material del océano** razonando que "siempre la va a querer". Su respuesta: *"nono, quiero que sean objetos distintos, porque quiero poder mezclar el fogslab con el oceano. No asumas porfa"*. Tenía razón: objetos separados = puede combinarlos, moverlos y apagarlos por separado; fundirlos en un material le sacaba esa libertad.
    ✅ Se revirtió el material a sus 179 expresiones originales (reconectar `MP_EmissiveColor`/`MP_Opacity` a sus alimentadores y borrar las 15 expresiones agregadas). **Revertir de verdad, no dejar el agregado "inerte con el default en 0"** — eso es justo la basura que después nadie entiende.

278. 💡 **Para animar un campo procedural de celdas, el desplazamiento va ANTES del `floor`/`frac`, no después.** En `M_VoidDots_SC` la deriva se suma a `TexCoord × Tiling` y recién ahí se parte en celda + fracción: así viaja **el campo entero**. Si se sumara después del `frac`, cada punto rebotaría dentro de su propia casilla y el conjunto quedaría quieto — parece animación y no lo es.
    💡 Y para que varias capas no se sincronicen nunca: razones y ángulos **no enteros** entre ellas (×1 / ×0,62 / ×0,38 y 0° / 137° / 251°). La capa cercana más rápida que las lejanas, como el paralaje real.
    ✅ **Verificar animación exige un control positivo**: con el resto de la animación APAGADA, dos capturas seguidas tienen que salir **byte a byte idénticas** con la velocidad en 0, y distintas con la velocidad alta. Sin apagar el centelleo, las capturas ya diferían solas y el test no probaba nada.

279. 🔴🔴 **Un patrón procedural sobre UV siempre delata la forma de la malla: en un cubo se ve la ESQUINA, en una esfera UV se ven los POLOS.** No hay que elegir entre los dos males — **la salida es no usar UV**: calcular el patrón sobre `normalize(LocalPosition) × Tiling`, o sea una grilla de celdas **en 3D** muestreada por la superficie. Sin polos, sin costuras, sin esquinas, y la distribución sale uniforme sola porque una esfera corta una grilla 3D de forma pareja.
    💡 De regalo, el tamaño aparente de cada punto varía solo según qué tan cerca de su centro de celda pasa la superficie — variación orgánica gratis.
    ⚠ **Dos costos que hay que pagar y conviene saber de antemano:**
    - Los puntos **se achican** (la intersección de una bola 3D con una superficie es menor que un disco 2D del mismo radio): en `M_VoidDots_SC` hubo que subir `DotSize` 0,098 → 0,16 y `Density` 0,266 → 0,45.
    - 🔴 **La malla tiene que ser densa.** Con el `Sphere` del motor aparecieron **facetas triangulares y anillos concéntricos**: la grilla 3D revela la teselación. Con `SM_GanzShell` (96×48, 9k tris) desaparecen.
