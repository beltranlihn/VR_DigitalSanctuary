---
name: blender-3d
description: Modeling 3D assets for Soul Charger through the official Blender MCP server (the "blender" MCP, Blender 5.2 LTS). Use this whenever a task touches Blender, 3D modeling, meshes, bpy/Python scripting in Blender, procedural geometry, UVs, or exporting models to Unreal — creating or editing an asset, inspecting a .blend scene, writing bpy code, rendering previews, optimizing polycount for Quest 3, or preparing/executing an FBX export to the UE project. Consult it even when the user doesn't say "MCP" or "skill" — if the work happens inside Blender or produces geometry for the project, this skill carries the modeling loop, the safe bpy patterns, the Quest budgets, the export checklist, and the setup traps already paid for.
---

# Blender 5.2 via MCP — guía operativa de modelado

Manejamos Blender con el **MCP oficial de Blender Foundation** (server **`blender`**, stdio → TCP 127.0.0.1:9876 → add-on dentro de Blender). Herramientas `mcp__blender__*`.

> ## 🔴 Contexto del proyecto — lo que cambia todas las respuestas
> Los assets son para **Soul Charger: Meta Quest 3 STANDALONE, renderer móvil, todo horneado**. Estética Turrell: luz de color en el aire, vacíos oscuros, **casi sin geometría** — acá un buen asset es SIMPLE. Los materiales finales se autoran **en Unreal** (emisivos/unlit del proyecto); el entregable de Blender es **geometría limpia + UVs (incluido el canal de lightmap)**. Presupuestos y export: [quest-budgets.md](references/quest-budgets.md) y [export-unreal.md](references/export-unreal.md).

## Arranque de sesión
- **Blender tiene que estar ABIERTO antes de arrancar Claude** (igual que el MCP `unreal`). El add-on auto-levanta el servidor al abrir Blender (`use_autostart=True`). Si Blender no corría al iniciar, las tools no existen → reiniciar Claude con Blender abierto.
- Verificación barata del link: `get_objects_summary` (o `get_blendfile_summary_path_info`).
- 🔴 **Trabajar sobre COPIAS de los `.blend`, nunca sobre originales sin respaldo.** El propio servidor ejecuta código generado sin guardas (advertencia textual de Blender Foundation). Los modelos del proyecto viven fuera de este repo (carpeta `Soul Charger VR\Modelos 3D` en el escritorio; hay backup pre-5.2 al lado).

## 🔴 Reglas de oro
1. **Verificar MIRANDO, no asumiendo.** Después de cada bloque de construcción: render (`render_viewport_to_path` al scratchpad) → `Read` de la imagen → crítica contra el objetivo. El código que corre sin error NO prueba que la geometría esté bien — el equivalente local de "declarado ≠ aplicado". El bucle completo: [modeling-loop.md](references/modeling-loop.md).
2. **Edición INCREMENTAL, nunca regenerar desde cero.** Un rehacer completo produce un asset visualmente distinto y pierde los ajustes previos. Editar los objetos existentes por nombre; conservar el script de construcción como fuente editable.
3. **Todo script `execute_blender_code` envuelto en `try/except BaseException`**, devolviendo el error como dato (mismo espíritu que `safe_script.py` de unreal-vr). Y salida CHICA: imprimir resúmenes, jamás volcar la escena entera al contexto.
4. **`bpy.data` para construir con precisión; `bpy.ops` solo con modo/selección/activo puestos explícitamente antes.** Los operators dependen del contexto y fallan o hacen otra cosa en silencio. Patrones completos: [bpy-patterns.md](references/bpy-patterns.md).
5. **No adivinar el API: consultarlo.** `search_api_docs` / `get_python_api_docs`, o Grep directo sobre los RST locales (`C:\Users\beltr\.blender-mcp\src\mcp\blmcp\data\api\` y `...\data\manual\`) — son de la versión instalada, le ganan a la memoria y a internet (los nombres de parámetros cambian entre versiones).
6. **Beltrán autora mirando**: después de construir o mover algo, encuadrarlo en su viewport (`jump_to_view3d_object_by_name`) para que lo vea. No tocar sus escenas abiertas más allá de lo pedido; nombrar TODO (objetos, mallas, colecciones) con nombres descriptivos.
7. **Antes de modelar algo nuevo: ¿ya existe?** Revisar la escena (`get_objects_summary`) y los `.blend` del proyecto antes de construir desde cero — la misma regla que en Unreal.

## El bucle de modelado (resumen — detalle en [modeling-loop.md](references/modeling-loop.md))
1. **Plan**: descomponer el asset en PARTES nombradas antes de la primera línea de código; parámetros descriptivos arriba del script (`leg_height`, no `h`).
2. **Construir por partes**: una función por parte, jerarquía padre-hijo, colección propia.
3. **Render multi-vista** → leer las imágenes → criticar (¿partes conectadas? ¿proporciones? ¿faltan detalles?).
4. **Arreglos localizados** sobre lo que existe. Repetir 3-4 hasta que coincida.
5. **Chequeo Quest** (polys, materiales, n-gons) → **export** con el checklist.

## Roster de tools (verificar la firma en vivo la primera vez)
| Tool | Para qué |
|---|---|
| `execute_blender_code` | La palanca principal: correr Python (`bpy`) en el Blender abierto. Siempre con la plantilla segura. |
| `get_objects_summary` / `get_object_detail_summary` | Inspección barata de la escena / de un objeto (transform, mallas, modificadores). Antes que cualquier print casero. |
| `get_blendfile_summary_*` | Radiografía de un `.blend`: datablocks, librerías linkeadas, archivos faltantes, uso. Variantes `_for_cli` para archivos sin abrir Blender. |
| `render_viewport_to_path` / `render_thumbnail_to_path` | El bucle visual: renderizar al scratchpad y leer la imagen. |
| `get_screenshot_of_window/area_*` | Ver la UI de Blender (para diagnosticar estado del editor, no geometría). |
| `jump_to_view3d_object_by_name` / `jump_to_tab_*` | Encuadrar un objeto / navegar la UI en el Blender de Beltrán. |
| `search_api_docs` / `search_manual_docs` / `get_python_api_docs` | Documentación local de la versión instalada. |

## Referencias (se cargan a demanda — cuestan 0 hasta leerlas)
- [references/modeling-loop.md](references/modeling-loop.md) — **el método**: descomposición en partes, parámetros expuestos, verificación visual multi-vista, crítica y arreglo localizado, los 4 modos de falla típicos de modelar por código y cómo se cazan. Destilado del sistema LL3M (threedle) + práctica.
- [references/bpy-patterns.md](references/bpy-patterns.md) — **patrones seguros de `bpy`**: data vs ops, contexto/modo/selección, `temp_override`, reglas de `bmesh`, depsgraph, performance (`from_pydata`/`foreach_set`), y la plantilla de script segura.
- [references/export-unreal.md](references/export-unreal.md) — **checklist completo Blender → UE 5.8**: unidades/escala, transforms aplicados, settings FBX exactos, colisiones `UCX_`, UVs de lightmap (acá SÍ, todo es horneado), naming `SM_`, materiales, síntomas de fallas y sus arreglos.
- [references/quest-budgets.md](references/quest-budgets.md) — **presupuestos de geometría para Quest 3**: triángulos por tipo de asset, qué cuesta de verdad (draw calls y fill-rate, no polys), transparencia, y el cruce con `unreal-vr/references/materials-vr.md`.
- [references/gotchas.md](references/gotchas.md) — trampas ya pagadas (setup del MCP, Blender 5.x) — crece con el uso.

## Tracker por asset
Igual que `unreal-vr/blueprints/`: al construir un asset con historia (parámetros, decisiones, estado), dejar un tracker en `assets/<nombre>.md` y su fila en [assets/_INDEX.md](assets/_INDEX.md). Al retocarlo, leer el tracker antes y actualizarlo después.
