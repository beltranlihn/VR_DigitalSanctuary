# Toolset reference (distilled) — use instead of `describe_toolset`

Call any tool via `mcp__unreal__call_tool {toolset_name, tool_name (SHORT), arguments}`. Refs are `{"refPath": "/Game/..."}` or `/Script/Module.Class`. `?` = optional. Re-`describe_toolset` live only if a tool isn't here.

Toolsets: BlueprintTools, SceneTools, ActorTools, ObjectTools, AssetTools, PrimitiveTools, StaticMeshTools, MaterialTools, MaterialInstanceTools, TextureTools, SkeletalMeshTools, DataTableTools, DataAssetTools, CurveTableTools, StringTableTools, EditorAppToolset, LogsToolset, ProgrammaticToolset, AgentSkillToolset.

🔴 **ESTA LISTA ESTABA INCOMPLETA y costó una sesión entera** (2026-08-04): se afirmó "el MCP no puede inspeccionar Niagara" basándose en ella. **Falso.** `list_toolsets` en vivo devuelve ~45 toolsets. Los que faltaban acá y son relevantes:
**NiagaraToolsets** (`NiagaraToolset_System`, `_Component`, `_Blueprint`, `_Info`, `_Assets`) · **UMGToolSet** · **ConfigSettingsToolset** · **SlateInspectorToolset** (automatización de la UI del editor) · **SemanticSearchToolset** · **AutomationTestToolset** · **PhysicsAssetToolset** · **PluginToolset** · **GameplayTagsToolset** · **GameFeaturesToolset** · **PCGToolset** · GASToolsets · Sequencer/ControlRig (`animation_toolset.*`) · StateTree / BehaviorTree / Conversation / DataRegistry / Dataflow / WorldConditions.
👉 **Ante la duda, corré `list_toolsets` (es barato) en vez de confiar en este archivo.**

## NiagaraToolsets.NiagaraToolset_System (`NiagaraToolsets.NiagaraToolset_System`)
⛔ `describe_toolset` = **278k chars**. Firmas destiladas acá; si falta una, extraé nombres con python/grep sobre el archivo volcado, no lo leas entero.
**Inspección (leer antes de tocar):**
- **GetSystemSummary**(system) — nombre, **user variables con tipo y default**, emitters (bEnabled, simTarget, renderers). **Empezá por acá.**
- **GetEmitterTopology**(emitterRef) — 🗺️ **el mapa completo**: todos los scripts (EmitterSpawn/EmitterUpdate/ParticleSpawn/ParticleUpdate), **cada módulo con `enabled`**, y todos sus inputs con nombre y tipo. Es el equivalente a `read_graph_dsl` para Niagara.
- **GetModuleInputValues**(moduleRef) — los **valores efectivos** de los inputs de un módulo (enums con `displayName` legible). Así se leen `Loop Behavior`, `Life Cycle Mode`, `Lifetime`, etc.
- **GetSystemCompileState**(system) — `bHasErrors`/`bHasWarnings` por script. · **GetStackIssues**(system) — errores/warnings/infos con su ubicación exacta.
- **GetScriptStackTopology**(scriptRef) — los módulos de UN script. Para el nivel sistema: `emitterName:""`, `scriptName:"SystemUpdateScript"`.
- También: GetUserVariables, GetSystemData/Schema, GetEmitterSummary/Data/Schema/InputValues, GetRendererData/Schema, GetStackInputData/Schema/Topology, GetModuleTopology/Schema, GetDynamicInputChain/Schema, GetAvailableDynamicInputs, GetSystemDependencies.

**Modificación:** **SetModuleEnabled**(moduleRef, bEnabled) · SetStackInputData(stackInputRef, inputData) · SetSystemData / SetEmitterData / SetRendererData · AddModule / RemoveModule · AddEmitter / RemoveEmitter · AddRenderer / RemoveRenderer · AddUserVariables / RemoveUserVariables · AddSetParametersModule / AddSetParameterEntry / RemoveSetParameterEntry · CreateNiagaraSystem · ApplyStackIssueFix.

🔴 **`moduleRef` / `scriptRef` / `emitterRef` = `NiagaraExt_StackItemReference` y exige TODOS los campos**, aunque no apliquen:
```json
{"system":{"refPath":"/Game/..."},"emitterName":"MiEmitter","scriptName":"ParticleUpdateScript",
 "moduleName":"MiModulo","rendererIndex":-1,"inputNameStack":[]}
```
Mandar solo `{system, emitterName}` **falla** pidiendo el ref completo. Nombres de script verificados: `EmitterSpawnScript`, `EmitterUpdateScript`, `ParticleSpawnScript`, `ParticleUpdateScript`, `SystemUpdateScript` (este último con `emitterName:""`).

**Recetas verificadas 2026-08-04** (para llegar a un input del stack se usa `inputNameStack:["Beam Start"]` sobre el `moduleRef`):
```json
// linkear un input del módulo a un user parameter
SetStackInputData(stackInputRef, {"struct":{"refPath":"/Script/NiagaraEditor.NiagaraExt_StackInputData_Linked"},
  "value":{"linkedVariable":{"name":"User.Beam_Start","type":{"classStructOrEnum":{"refPath":"/Script/Niagara.NiagaraPosition"}}}}})
// crear un user parameter — underlyingType: 0=None 1=Class 2=Struct 3=Enum · flags:0
AddUserVariables(system, [{"name":"User.Beam_Start","description":"...",
  "type":{"classStructOrEnum":{"refPath":"/Script/Niagara.NiagaraPosition"},"underlyingType":2,"flags":0},
  "defaultValue":{"struct":{"refPath":"/Script/Niagara.NiagaraPosition"},"value":{"x":0,"y":0,"z":0}}}])
```
- Modos de valor que devuelve `GetModuleInputValues`: `StackInputData_Linked` (link a un parámetro) · `_DynamicInput` (cadena → `GetDynamicInputChain`) · `_Enum` · el struct pelado (valor local) · **`_Unsupported`**. Los inputs con `bIsVisible:false` salen `_Unsupported` porque están tapados por un static switch — **pero un `_Unsupported` en un input VISIBLE y EDITABLE es sospechoso**, ahí escondía un valor local sin conectar.
- ⚠ **`NiagaraToolset_Component.SetVariable` no soporta `Vector3f`** — su lista de tipos tiene `Vector` (FVector double), `NiagaraPosition`, floats, etc., pero no `Vector3f`; setear uno **falla en silencio**. Y **leer** un `NiagaraPosition` devuelve `value:{}` (hueco del serializador), así que no sirve para verificar.
- ⚠ **`AddUserVariables`/`RemoveUserVariables` reconstruyen el override store de los componentes ya colocados** → los valores que habías seteado en las instancias **se pierden**. Volvé a setearlos después de tocar el set de parámetros.

---

## BlueprintTools (`editor_toolset.toolsets.blueprint.BlueprintTools`)
**Asset / graphs**
- **create**(folder_path, asset_name, asset_type: class-ref) — new Blueprint (Actor = `/Script/Engine.Actor`).
- **list_graphs**(blueprint) — returns `:EventGraph`, `:UserConstructionScript`, function graphs.
- **get_graph**(blueprint, graph_name) / **list_functions**(blueprint) / **list_events**(blueprint).
- **get_default_object**(blueprint) — the CDO (`/Game/.../Default__X_C`); needed to add components.
- **compile_blueprint**(blueprint, warnings_as_errors?=false).
- **get_parent**(blueprint) / **set_parent**(blueprint, parent_class).

**DSL**
- **read_graph_dsl**(graph) / **write_graph_dsl**(graph, code) / **get_graph_dsl_docs**() — see dsl.md. write DUPLICATES existing events → only for new/empty graphs.

**Variables**
- **add_variable**(blueprint, name, type_name, graph?, container_type?) — prims + Vector/Rotator/Transform/Vector2D/LinearColor. ✅ **`Text` también funciona.**
- **add_object_variable**(blueprint, name, object_class, graph?, container_type?) / **add_struct_variable**(blueprint, name, struct_type, graph?, container_type?). Para una clase de BP el `object_class` es el **`_C`**: `/Game/.../BP_X.BP_X_C`.
- **list_variables**(blueprint) / **remove_variable**(blueprint, name).
- **set_variable_instance_editable**(blueprint, **`variable_name`**, instance_editable) — 🔴 el parámetro es **`variable_name`**, NO `name` (a diferencia de `add_variable`/`remove_variable`, que sí usan `name`). / **set/get_variable_category** / **set/get_variable_replication**.

🔴 **Después de `add_variable` hay que `compile_blueprint` ANTES de poder escribir su default en el CDO.** Si no, `set_properties` sobre el `Default__X_C` falla con *"the following properties could not be set"* — el CDO todavía no tiene el campo. Orden correcto: `add_variable` → `compile_blueprint` → `set_properties` sobre el CDO → `get_properties` para verificar → `compile_blueprint`.

**Functions / events / dispatchers**
- **add_function_graph**(blueprint, graph_name) / **remove_function_graph**(blueprint, graph_name).
- **add_function_param**(graph, param_name, param_type, input_param, container_type?) — prims + basic structs.
- **add_object_function_param**(…, object_class, input_param) / **add_struct_function_param**(…, struct_type, input_param) — any struct.
- **remove_function_param**(graph, param_name).
- **add_event**(blueprint, event_name, position?) — override inherited OR create custom event (no typed params via API).
- **add_event_dispatcher** / **list_event_dispatchers**.

**Nodes — discovery**
- **find_node_types**(graph, type_id_filter, context_pins:[]) — be SPECIFIC; trailing `|` lists a category.
- **get_node_type_pins**(graph, type_id) — exact pin names/types/indices.
- **find_node_categories**(graph, …) / **find_nodes**(graph, title (required, "" = all), node_class?, entry_points_only?) / **get_node_infos**(nodes[]) / **get_connected_subgraph**(…).

**Nodes — editing**
- **create_node**(graph, type_id, pos, declaring_class?) — type_id like `Development|PrintString`, `AddEvent|EventBeginPlay`, `AddEvent|Custom|MyEvent`.
- **delete_node**(node) / **set_node_position**(node,pos) / **arrange_nodes**(…) / **retarget_node_class**(…).
- **connect_pins**(output_pin: PinID, input_pin: PinID) / **break_pins**(…). PinID = `{direction: EGPD_Input|EGPD_Output, index_id, node:{refPath}}`. Connecting to an already-connected input REPLACES it.
- **get_pin_value**(pin) / **set_pin_value**(pin, value) — input pins with default values only.
- **add_node_pin**(node) / **remove_node_pin**(node, pin) — Switch/Sequence/Make Array/commutative ops (auto-named).

**Delegates / bound events**
- **add_component_bound_event**(component, event_name, graph) / **list_component_events**(component) — component delegates only.
- **list_compatible_event_functions**(node) / **set_create_event_function**(node, function_name) / **get_create_event_function**(node) — for CreateEvent (K2Node_CreateDelegate) nodes.

## SceneTools (`editor_toolset.toolsets.scene.SceneTools`)
- **get_current_level**() / **load_level**(level_path).
- **find_actors**(name, tag, collision_channels[], root?, actor_type?, bounds?) — search the level.
- **add_to_scene_from_asset**(asset_path, name, xform, parent?, snap_to_ground?=false) — spawn a BP/asset actor.
- **add_to_scene_from_class**(actor_type: class-ref, name, xform, parent?, snap_to_ground?) — spawn from a class.
- **remove_from_scene**(actor) / **save_actor**(actor) / **can_edit**(actor) / **is_checked_out**(actor).
- **trace_world**(start: Vector, end: Vector) — distance to first hit.
- **merge_actors**(actors[], output_path, name?, destroy_source_actors?) — merge StaticMeshActors.
- **create_level_instance** / **edit_level_instance** / **commit_level_instance**(…, discard?).
- Outliner: **get_folders**() / **get_actors_in_folder**(folder_path, recursive?) / **set_actor_folder**(actor, folder_path) / **rename_folder** / **delete_folder**.
- **get_collision_channels**().

## AssetTools (`editor_toolset.toolsets.asset.AssetTools`)
- **save_assets**(asset_paths[]) — [] saves all dirty. **load_asset**(asset_path) / **is_dirty**(asset_path).
- **find_assets**(folder_path, name, asset_type?, recursive?=true, tags?) / **exists**(path) / **get_asset_class**(asset_path).
- **move**(path, new_path) / **duplicate**(path, new_path) / **delete**(path).
- **list_folders**(root_path, recursive?) / **create_folder**(path).
- **get_dependencies**(asset_path) / **get_referencers**(asset_path).
- **read_file**(file_path) / **write_file**(file_path, content) — text files under /Game/, plugin Content/, or Saved/.
- **get/update_metadata_tags** / **get_asset_tags** / **can_edit_asset** / **is_checked_out**.

## 🔴🔴 LOS TRANSFORMS NO SE APLICAN AL COLOCAR — hay que setearlos después, SIEMPRE
Medido el 2026-08-11 construyendo el esqueleto. **Tres tools aceptan un transform, devuelven éxito, y NO lo aplican:**

| Tool | Qué ignora | Qué sí aplica |
|---|---|---|
| `PrimitiveTools.add_*` | el `local_transform` **entero** | la escala derivada de `radius`/`height`/`dimensions` |
| `SceneTools.add_to_scene_from_asset` | el `xform` | — |
| `ActorTools.set_actor_transform` | **todo** (devuelve `true` y no mueve nada) | — |

✅ **La vía que SÍ funciona, para componentes y para actores del nivel:**
```
ObjectTools.set_properties(<componente o rootComponent>, '{"relativeLocation":{"x":..,"y":..,"z":..}}')
```
Para un actor del nivel: `ActorTools.get_root_component(actor)` y setearle `relativeLocation` a ese componente.
🔴 **Y verificar siempre después** con `get_properties` (componentes) o `get_actor_transform` (actores). Es el caso de libro de "declarado ≠ aplicado": los tres devuelven éxito.

⚠ Los **basic shapes del motor están centrados en su origen** (bounds −50..+50, verificado en `/Engine/BasicShapes/Cylinder`). Para apoyar algo en Z=0 hay que compensar media altura a mano.

## PrimitiveTools (`editor_toolset.toolsets.primitive.PrimitiveTools`)
Add StaticMeshComponent primitives to an actor — pass the BP's **CDO** (get_default_object) as `actor`, not the asset. Returns the component.
- `dimensions` (cubo) se pasa en **cm** y se traduce a escala sobre el cubo de 100³ — cómodo, pero ver el bloque de transforms de arriba.
- **add_sphere**(actor, name, radius?=50, local_transform?).
- **add_cube**(actor, name, dimensions?={100,100,100}, local_transform?).
- **add_cylinder**(actor, name, radius?=50, height?=100, local_transform?).
- **add_cone**(actor, name, radius?=50, height?=100, local_transform?).

## ActorTools (`editor_toolset.toolsets.actor.ActorTools`)
- **add_component**(owner, component_type: ref, name) / **remove_component**(component) / **get_components**(actor, component_type?).
- **get_root_component**(actor) / **get_component_actor**(component) / **get_parent_component**(component) / **set_parent_component**(component, parent?) (null detaches/promotes root).
  - 🔴 **SÍ se pueden reparentar componentes por MCP — no lo niegues sin leer esta línea.** El 2026-08-16 se afirmó "reparentar es lo único que no puedo hacer por MCP" y era falso; lo corrigió Beltrán. Funciona sobre el **CDO** del Blueprint (`get_default_object`), con los nombres `<Comp>_GEN_VARIABLE`, y devuelve `True` por componente. Caso real: `Ring0…Ring4` colgaban de `Body` y heredaban su pulso; se movieron al `DefaultSceneRoot` en una llamada.
  - ⚠ **Reparentar cambia la base de la escala relativa.** Si el padre viejo tenía escala ≠ 1, hay que compensar o el hijo cambia de tamaño. En ese caso `Body` estaba a 0,15, así que los anillos pasaron de `RingBaseScale` 2 → 0,30 y `RingScaleStep` 0,35 → 0,0525 para verse igual. **Calculá el factor ANTES de mover.**
  - 💡 `get_parent_component` es la forma de **leer** la jerarquía: `AttachParent` NO se puede leer con `ObjectTools.get_properties` sobre el template del CDO (falla con "could not be read").
- **get_actor_transform**(actor) / **set_actor_transform**(actor, xform: Transform, worldspace?) / **get_actor_bounds**(actor) / **look_at**(actor, target: Vector).
- **get_label/set_label**(actor[, label]) / **get_tags/has_tag/add_tag/remove_tag**(actor[, tag]).

## ObjectTools (`editor_toolset.toolsets.object.ObjectTools`)
- **list_properties**(instance) / **get_properties**(instance, properties[]) → JSON / **set_properties**(instance, values: JSON-string) / **reset_properties**(instance, properties[]).
- **get_class**(instance) / **search_subclasses**(base_class, class_name substring) — discover classes/subclasses.

## StaticMeshTools (`editor_toolset.toolsets.static_mesh.StaticMeshTools`)
- **import_file**(folder_path, asset_name, source_file, import_materials?=false, import_textures?=false, combine_meshes?=true) → ref[] (first = primary).
- **set_material**(mesh, slot_name, material) / **get_material**(mesh, slot_name) / **get_material_slots**(mesh).
- **get_bounds** / **get_vertex_count**(mesh, lod?) / **get_triangle_count**(mesh, lod?) / **get_lod_count**(mesh).
- **generate_lods**(mesh, triangle_percents[]) / **remove_lods** / **set/get_lod_thresholds**.
- **set/is_nanite_enabled**(mesh[, enabled]) / **remove_collisions** / **generate_convex_collisions**(mesh, hull_count?, max_hull_verts?, hull_precision?).

## MaterialTools (`editor_toolset.toolsets.material.MaterialTools`)
🔴 **Los nombres de parámetro van COMPLETOS — este archivo los tuvo abreviados y cada uno costó un round-trip** (corregido 2026-08-11): es **`material_or_function`** (NO `mat_or_fn`), **`from_expression`/`to_expression`** (NO `from_expr`/`to_expr`), **`expression`**, **`material`**. El error que devuelve es claro (`input param "X" is required ... but is missing`), así que se detecta rápido, pero no hay razón para pagarlo.
- **create_material**(folder_path, asset_name) / **create_function**(…) / **create_parameter_collection**(…).
- **add_expression**(**material_or_function**, expression_class: ref, x?, y?) / **delete_expression**(**material_or_function**, expression) / **get_expressions** / **list_expression_classes**(**material_or_function**, search).
- **connect_expressions**(**from_expression**, from_output_name, **to_expression**, to_input_name) / **disconnect_expressions**(to_expression, to_input_name).
- **connect_to_output**(expression, output_name, material_property: enum e.g. MP_BaseColor) / **disconnect_from_output**(mat, material_property).
- **get_expression_input_names/output_names**(expression) / **get_expression_inputs** / **get_property_input**(**material**, material_property).
- **list/rename/delete_parameter_group** / **recompile**(**material_or_function**) (once when done).
- 🔴 **`layout_expressions` y `delete_unused_expressions` NO usan `material_or_function`: su parámetro es `material`** (verificado 2026-08-17 — el error es explícito, pero el script fallido dispara un Undo que se comió un actor del nivel, así que sale caro. Ver gotchas §60/§103).

⛔ **NO corras `ObjectTools.list_properties` sobre un Material: son ~10k chars.** Los flags que se usan de verdad son `shadingModel` (`MSM_Unlit`), `blendMode` (`BLEND_Opaque`/`BLEND_Translucent`), `twoSided`, `bFullyRough`, `bDisableDepthTest`, `bUsedWithStaticLighting`. Verificá con `get_properties` pidiendo solo esos.

✅ **Cómo verificar un material de una sola llamada:** `MaterialInstanceTools.list_parameters(<el MATERIAL, no una instancia>)` devuelve los parámetros que el material **compilado** expone, con tipo y nombre. Si el nombre que esperabas está ahí, quedó bien puesto Y el material compiló. Cerrá con `get_property_input` para confirmar qué expresión alimenta el output.

⚠ **`MaterialExpressionWorldPosition` ya trae salidas `XYZ` / `XY` / `Z`** — no hace falta un `ComponentMask` para sacar el plano o la altura.
⚠ Nombres de propiedades de expresiones (para `set_properties`): Scalar/VectorParameter = `parameterName` + `defaultValue`; `MaterialExpressionConstant` = `r`; `Constant3Vector` = `constant`; `ComponentMask` = `r`/`g`/`b`/`a`.
⚠ **El material de un COMPONENTE no se setea con `StaticMeshTools.set_material`** (esa tool exige un asset StaticMesh) → va por `ObjectTools.set_properties` con `{"overrideMaterials":[{"refPath":"..."}]}`.

## MaterialInstanceTools (`editor_toolset.toolsets.material_instance.MaterialInstanceTools`)
- **create**(folder_path, asset_name, parent) / **set_parent**(instance, parent) / **list_parameters**(material).
- **set/get_scalar_parameter**(instance, name[, value]) / **set/get_vector_parameter**(…, LinearColor) / **set/get_texture_parameter**(…, ref) / **set/get_static_switch_parameter**(…, bool) (recompiles).
- **set_parameter_override**(instance, name, override) / **clear_parameters**(instance).

## TextureTools (`editor_toolset.toolsets.texture.TextureTools`)
- **get_size**(texture) → IntPoint / **import_file**(folder_path, asset_name, source_file) → ref[].

## SkeletalMeshTools (`editor_toolset.toolsets.skeletal_mesh.SkeletalMeshTools`)
- **import_file**(folder_path, asset_name, source_file, skeleton?, import_materials?, import_textures?, import_animations?, create_physics_asset?).
- **get_skeleton/get_bounds/get_lod_count/get_vertex_count/get_section_count**(mesh[, lod]).
- Bones: **get_bone_names/get_bone_parent/get_bone_children**(mesh[, bone]).
- Sockets: **get_socket_names/add_socket/rename_socket/remove_socket/get_socket_bone/get_socket_transform/set_socket_transform**.
- **get_morph_target_names** / **get_material_slots** / **get/set_material** / **get/assign_physics_asset**.

## DataTableTools (`editor_toolset.toolsets.data_table.DataTableTools`)
- **create**(folder_path, asset_name, schema: struct-ref) / **import_file**(…, source_file, schema) / **search_row_structs**(struct_name?="*").
- **get_schema** / **list_rows** / **add_rows**(dt, names[]) / **remove_rows** / **rename_rows**(dt, {old:new}) / **get_rows**(dt, names[]) / **set_rows**(dt, JSON-string).

## DataAssetTools (`editor_toolset.toolsets.data_asset.DataAssetTools`)
- **create**(folder_path, asset_name, asset_type: class-ref).

## CurveTableTools (`editor_toolset.toolsets.curve_table.CurveTableTools`)
- **create** / **import_file**(…, interp_mode: RCIM_Linear|RCIM_Constant|RCIM_Cubic|RCIM_None) / **list_rows** / **add_row**(ct, name, default?) / **remove_row** / **rename_row** / **get_keys** / **add_key**(ct, row, {time,value}) / **set_keys**.

## StringTableTools (`editor_toolset.toolsets.string_table.StringTableTools`)
- **create** / **import_file**(…, source_file: Key+SourceString) / **list_keys** / **get_entry** / **set_entry**(st, key, value) / **remove_entry** / **get_namespace** / **get_table_id**.

## EditorAppToolset (`EditorToolset.EditorAppToolset`)
- PIE: **StartPIE**({bSimulate, playMode, warmupSeconds, startTransform?}) / **StopPIE**() / **IsPIERunning**().
- Capture: **CaptureViewport**(captureTransform?, annotations?, bShowUI?) / **CaptureEditorImage**() / **CaptureAssetImage**(assetPath).
- Camera: **GetCameraTransform** / **SetCameraTransform** / **FocusOnActors**(actors[]).
- Selection: **GetVisibleActors** / **GetSelectedActors** / **SelectActors**(actors[]) / **GetSelectedAssets** / **SelectAssets**(paths[]) / **GetOpenAssets** / **OpenEditorForAsset**(assetPath).
- Content browser: **GetContentBrowserPath** / **SetContentBrowserPath**(path).
- **SearchCVars**(name) / **WorldPosToScreenCoords**(pos) / **ScreenCoordsToWorld**(coords, traceDistance?).

🔴 **CICLO DE DEBUGGING AUTÓNOMO (descubierto 2026-08-04 — no depender del usuario para cada prueba):**
```
LogsToolset.SetVerbosity("Verbose","LogNiagara")      ← hacer hablar al subsistema
EditorAppToolset.StartPIE({bSimulate,playMode,warmupSeconds})
LogsToolset.GetLogEntries(pattern, category, maxEntries)   ← leer los PrintString y los logs del motor
EditorAppToolset.StopPIE()
```
Con esto se corre PIE, se leen los logs y se cierra **sin pedirle al usuario que se ponga el visor**. Combinado con `PrintString` de estado, es el bucle de diagnóstico más rápido que tenemos.
- ⚠ **`StartPIE` y `CaptureViewport` exigen TODOS sus campos** (`options` completo; `captureTransform` + `bShowUI` + `annotations`), aunque el schema los muestre opcionales.
- ⚠ **`CaptureViewport` captura el viewport del EDITOR, no la vista de PIE** (se ven los billboards de iconos que PIE oculta). Sirve para inspeccionar el nivel, **no** para ver qué renderiza el juego.
- ⚠ Devuelve el PNG en **base64 dentro del JSON (~373-700k chars)**. 🔴 **NUNCA lo traigas al contexto principal.**

🔴 **CICLO DE DEBUGGING VISUAL AUTÓNOMO (2026-08-04) — "ver" el viewport sin gastar contexto**
La forma barata de sacar la captura es que **Unreal mismo escriba el PNG a disco**, con `ProgrammaticToolset.execute_tool_script`: adentro del script llamás a `CaptureViewport` y volcás `returnValue.image.data` con `AssetTools.write_file`.
- 🔴 La ruta de `write_file` tiene que ser **ABSOLUTA y dentro de `VR_Test/Saved/`** — las relativas se resuelven contra el binario del engine y fallan en silencio. Su parámetro es **`content`** (singular) y **rechaza extensiones** fuera de `.csv/.html/.json/.md/.py/.txt` → volcá el base64 a un `.txt`.
- 🔴 `mcp__unreal__call_tool` usa el campo **`arguments`**, NO `parameters`. Con el nombre equivocado la llamada llega vacía y el error **parece** un problema de schema del tool destino: se pierde tiempo depurando el tool equivocado.
- 🔴🔴 **El viewport del editor NO es un oráculo confiable para VFX.** 13 capturas dijeron "el beam no se dibuja" mientras el usuario, mirando su propio viewport, veía el mismo asset dibujando sin problema. Antes de sacar cualquier conclusión de una captura, **validala contra algo que ya sabés que se ve**; y ante una contradicción entre la captura y lo que reporta el usuario, **gana el usuario**. Para VFX el oráculo real es el visor.
- Después: `base64.b64decode` con Python local → `.png` → **`Read`** (la herramienta Read muestra imágenes).
- Encuadre reproducible: `EditorAppToolset.SetCameraTransform({transform:{location,rotation,scale}})` y **`WorldPosToScreenCoords`** para convertir puntos del mundo a píxeles → así se **mide** dónde cae de verdad lo dibujado, en vez de opinar sobre la imagen. Fue lo que probó que el beam salía del origen del mundo.
- 👉 Si la captura es grande igual, **delegá el ciclo entero a un subagente** y pedile solo el veredicto en texto: el base64 se come SU contexto, no el tuyo.

## LogsToolset (`EditorToolset.LogsToolset`)
- **GetLogEntries**(pattern, category?, maxEntries?) / **GetLogCategories**(filter) / **GetVerbosity**(category?) / **SetVerbosity**(verbosity, category?).

## ProgrammaticToolset (`editor_toolset.toolsets.programmatic.ProgrammaticToolset`)
Batch several toolset calls in one sandboxed Python `run()->dict` script to cut round-trips (not general Python). **get_execution_environment**() once first, then **execute_tool_script**(script).

## AgentSkillToolset (`ToolsetRegistry.AgentSkillToolset`)
List/read/create/update Unreal **Agent Skills** (project-side). Not used for BP building.
