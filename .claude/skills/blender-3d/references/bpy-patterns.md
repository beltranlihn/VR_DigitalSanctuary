# Patrones seguros de `bpy` — data vs ops, contexto, bmesh, performance

Fuentes: doc oficial del API (mejores prácticas), las instrucciones del propio servidor MCP, y skills de agentes publicadas para Blender. Regla madre: **los scripts corren en un Blender con la UI de Beltrán abierta — nada de asumir contexto.**

## 1. La plantilla segura (SIEMPRE)

Todo `execute_blender_code` va envuelto así — el error vuelve como DATO, nunca como excepción sin capturar:

```python
import bpy, traceback
result = {"ok": False}
try:
    # ... trabajo ...
    result = {"ok": True, "resumen": "<qué se hizo, en 1-3 líneas>"}
except BaseException as e:
    result = {"ok": False, "error": f"{type(e).__name__}: {e}",
              "trace": traceback.format_exc(limit=3)}
print(result)
```

- Salida **CHICA**: resúmenes y conteos, jamás `print(list(bpy.data.objects))` de una escena grande ni volcados de mallas.
- Al terminar, dejar la escena en **Object Mode** y sin selecciones raras — Beltrán sigue trabajando ahí.

## 2. `bpy.data` vs `bpy.ops`

- **`bpy.data` (API de datos) para construcción precisa**: crear mallas (`bpy.data.meshes.new` + `from_pydata`), materiales, colecciones, parenting, propiedades. No depende de contexto, no tiene efectos colaterales.
- **`bpy.ops` (operators) solo para acciones estándar** donde el operator resuelve trabajo real (add primitive con defaults, aplicar modificador, smart UV project). Y con el terreno preparado:
  1. **Modo correcto primero** (`bpy.ops.object.mode_set(mode='OBJECT')`) — un operator en el modo equivocado falla o **no hace nada en silencio**.
  2. **Selección Y activo explícitos** — son cosas distintas y muchos operators exigen ambas:
     ```python
     bpy.ops.object.select_all(action='DESELECT')
     obj.select_set(True)
     bpy.context.view_layer.objects.active = obj
     ```
  3. **Los operators CAMBIAN la selección/activo como efecto colateral** → re-preparar entre operators encadenados sobre objetos distintos.
- No asumir válidos `bpy.context.object`, `selected_objects`, área activa ni modo. Si un operator exige contexto de UI (raro en modelado), usar `bpy.context.temp_override(**override)` como context manager — no confiar en el contexto implícito.

## 3. `bmesh` — edición de malla confiable

- **En Object Mode** (lo normal para scripts):
  ```python
  bm = bmesh.new(); bm.from_mesh(obj.data)
  # ... bmesh.ops.* ...
  bm.to_mesh(obj.data); obj.data.update(); bm.free()
  ```
- **En Edit Mode** (solo si hay que interoperar con la sesión de edición): `bmesh.from_edit_mesh(me)` + `bmesh.update_edit_mesh(me)`. 🔴 En Edit Mode **NO usar el API regular de malla** (`me.vertices...`) — está desincronizado del bmesh.
- Tras borrar/crear elementos, refrescar las tablas antes de indexar: `bm.verts.ensure_lookup_table()` (ídem edges/faces).
- Preferir `bmesh.ops.*` (extrude, inset, bevel, spin, solidify…) sobre reimplementar geometría a mano — están en la doc local (`data/api/bmesh.ops.rst`).

## 4. Depsgraph — leer lo EVALUADO, no lo original

Modificadores, constraints y geometry nodes viven en la **versión evaluada**. Para leer resultados computados (malla final, world matrix tras constraint):

```python
deps = bpy.context.evaluated_depsgraph_get()
obj_eval = obj.evaluated_get(deps)
me_final = obj_eval.to_mesh()   # malla CON modificadores
# ... leer ... y después:
obj_eval.to_mesh_clear()
```

Tras cambiar datos por script, `bpy.context.view_layer.update()` antes de leer `matrix_world` u otros derivados — si no, se leen valores viejos (el "declarado ≠ aplicado" local).

## 5. Performance en mallas grandes

- **Crear**: `mesh.from_pydata(verts, edges, faces)` con listas completas — nunca vértice por vértice con operators.
- **Leer/escribir atributos en masa**: `foreach_get`/`foreach_set` sobre buffers planos (p. ej. `me.vertices.foreach_set("co", flat_list)` + `me.update()`).
- Evitar `bpy.ops` dentro de loops (cada llamada re-evalúa escena y undo) — un `bmesh` batch hace en milisegundos lo que cien operators hacen en segundos.

## 6. Higiene

- Nombrar **objeto y datablock**: `obj.name = "SM_Bell_Body"; obj.data.name = "SM_Bell_Body"`.
- Un asset = una **colección**; partes emparentadas a un objeto raíz (o al cuerpo principal).
- Los datablocks huérfanos (mallas de intentos borrados) quedan en el archivo — al cerrar un asset: purgar (`bpy.data.orphans_purge()`), con cuidado de no llevarse material ajeno de la escena de Beltrán.
- Aplicar escala/rotación (`bpy.ops.object.transform_apply`) ANTES de medir, de bevels/solidify (los modificadores actúan en espacio local) y siempre antes de exportar.
