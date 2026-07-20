# Toolset reference (distilled) — use instead of `describe_toolset`

Call any tool via `mcp__unreal__call_tool {toolset_name, tool_name (SHORT), arguments}`. Refs are `{"refPath": "/Game/..."}` or `/Script/Module.Class`. `?` = optional. Re-`describe_toolset` live only if a tool isn't here.

Toolsets: BlueprintTools, SceneTools, ActorTools, ObjectTools, AssetTools, PrimitiveTools, StaticMeshTools, MaterialTools, MaterialInstanceTools, TextureTools, SkeletalMeshTools, DataTableTools, DataAssetTools, CurveTableTools, StringTableTools, EditorAppToolset, LogsToolset, ProgrammaticToolset, AgentSkillToolset.

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
- **add_variable**(blueprint, name, type_name, graph?, container_type?) — prims + Vector/Rotator/Transform/Vector2D/LinearColor.
- **add_object_variable**(blueprint, name, object_class, graph?, container_type?) / **add_struct_variable**(blueprint, name, struct_type, graph?, container_type?).
- **list_variables**(blueprint) / **remove_variable**(blueprint, name).
- **set_variable_instance_editable**(…) / **set/get_variable_category** / **set/get_variable_replication**.

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

## PrimitiveTools (`editor_toolset.toolsets.primitive.PrimitiveTools`)
Add StaticMeshComponent primitives to an actor — pass the BP's **CDO** (get_default_object) as `actor`, not the asset. Returns the component.
- **add_sphere**(actor, name, radius?=50, local_transform?).
- **add_cube**(actor, name, dimensions?={100,100,100}, local_transform?).
- **add_cylinder**(actor, name, radius?=50, height?=100, local_transform?).
- **add_cone**(actor, name, radius?=50, height?=100, local_transform?).

## ActorTools (`editor_toolset.toolsets.actor.ActorTools`)
- **add_component**(owner, component_type: ref, name) / **remove_component**(component) / **get_components**(actor, component_type?).
- **get_root_component**(actor) / **get_component_actor**(component) / **get_parent_component**(component) / **set_parent_component**(component, parent?) (null detaches/promotes root).
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
- **create_material**(folder_path, asset_name) / **create_function**(…) / **create_parameter_collection**(…).
- **add_expression**(mat_or_fn, expression_class: ref, x?, y?) / **delete_expression** / **get_expressions** / **list_expression_classes**(…, search).
- **connect_expressions**(from_expr, from_output_name, to_expr, to_input_name) / **disconnect_expressions**(to_expr, to_input_name).
- **connect_to_output**(expr, output_name, material_property: enum e.g. MP_BaseColor) / **disconnect_from_output**(mat, material_property).
- **get_expression_input_names/output_names**(expr) / **get_expression_inputs** / **get_property_input**(mat, property).
- **list/rename/delete_parameter_group** / **layout_expressions** / **delete_unused_expressions** / **recompile**(mat_or_fn) (once when done).

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

## LogsToolset (`EditorToolset.LogsToolset`)
- **GetLogEntries**(pattern, category?, maxEntries?) / **GetLogCategories**(filter) / **GetVerbosity**(category?) / **SetVerbosity**(verbosity, category?).

## ProgrammaticToolset (`editor_toolset.toolsets.programmatic.ProgrammaticToolset`)
Batch several toolset calls in one sandboxed Python `run()->dict` script to cut round-trips (not general Python). **get_execution_environment**() once first, then **execute_tool_script**(script).

## AgentSkillToolset (`ToolsetRegistry.AgentSkillToolset`)
List/read/create/update Unreal **Agent Skills** (project-side). Not used for BP building.
