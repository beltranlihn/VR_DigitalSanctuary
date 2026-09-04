# Gotchas — trampas ya pagadas (crece con el uso)

## Setup del MCP (2026-09-01, costaron tiempo real — no repetir)

1. **`mcp[cli]` hay que pinearlo `<2`** en el venv (`C:\Users\beltr\.blender-mcp\venv`). El `pyproject.toml` upstream declara `mcp[cli]>=1.2.0` sin tope; el SDK 2.x rompe con `No module named 'mcp.server.fastmcp'`. Si algo se reinstala, repetir el pin.
2. **El add-on exige Blender ≥ 5.1** (`blender_version_min` del manifiesto). Por eso se actualizó a 5.2.1 LTS. No lo corras en un 4.x.
3. **"Online access must be enabled"**: el add-on declara permiso de red y Blender 5.x lo bloquea con Online Access apagado. Quedó activado en preferencias (decisión de Beltrán); alternativa: lanzar Blender con `--online-mode`.
4. **Puerto 8000 = el del MCP de `unreal`.** El server de Blender usa stdio, así que hoy no chocan — **no cambiar a transporte HTTP** sin mover el puerto.
5. El repo embebe el manual → clonar en Windows requiere `-c core.longpaths=true` y ruta base corta.

## Operación

6. **El servidor ejecuta el código sin guardas** (advertencia textual de Blender Foundation). Regla adoptada: trabajar sobre **copias** de los `.blend`; backup pre-5.2 en `Soul Charger VR\Modelos 3D _BACKUP_pre-Blender52`.
7. **Blender tiene que estar abierto ANTES de arrancar Claude** — igual que Unreal. Sin editor corriendo, las tools `blender` no existen y no se re-attachan solas.
8. **El MCP oficial está orientado a inspeccionar** (summaries, docs, screenshots); la potencia constructiva es `execute_blender_code`. No buscar una tool dedicada de "crear malla": no existe, se hace por Python.
9. **Un script que revienta puede dejar la escena a medio hacer** (objetos huérfanos, modo raro, selección rota). La plantilla try/except de [bpy-patterns.md](bpy-patterns.md) §1 + dejar siempre Object Mode al salir. Ante un fallo: inspeccionar qué quedó (`get_objects_summary`) antes del siguiente intento, no re-correr a ciegas.
10. **Blender 5.x renombró cosas del API vs lo que sabe el modelo** (herencia de 4.x). Ante `AttributeError`/`TypeError` en llamadas que "deberían andar": Grep en `C:\Users\beltr\.blender-mcp\src\mcp\blmcp\data\api\` — es la doc de la versión instalada.

11. **`render_viewport_to_path` IGNORA la ruta pedida** (2026-09-01): escribe en su propio temp (`%TEMP%\blender_XXXXXX\blender_mcp\<nombre>.png`) y devuelve la ruta real en el resultado — leer SIEMPRE del `filepath` devuelto, no de la ruta que se pasó.
12. **Para verificar solo la GEOMETRÍA, screenshot del viewport, no render** (2026-09-01, pedido de Beltrán): `get_screenshot_of_area_as_image(VIEW_3D)` en sólido muestra silueta y cantos sin armar cámara/luces, y además es la misma vista que él está mirando. Orientar su viewport con `view3d.view_axis`/`view_orbit` + `view_selected` bajo `temp_override` funciona. Reservar el rig de render para cuando importe el material/brillo — y si se arma, desarmarlo al terminar.
13. **Medir la referencia en píxeles antes de modelar** (2026-09-01): las proporciones "a ojo" fallaron dos veces (alturas y tamaño del grabado); la razón px→metros sobre la foto lateral las clavó a la primera. Anotar las medidas en el tracker del asset.
14. **`ob.parent = X` por Python NO compensa el transform del padre** (2026-09-01): deja `matrix_parent_inverse` en identidad → el hijo salta a `padre.matrix_world @ local` (un anillo apareció 2.1 m arriba). Fix: `transform_apply(location=True)` del padre ANTES de emparentar (además deja el origen donde corresponde para el export), o setear `child.matrix_parent_inverse = parent.matrix_world.inverted()`.
15. **El bevel de una caja redondeada también curva la esquina del PISO** (2026-09-01): un volumen-vacío para interiores queda con labio en la base. Fix: hacerlo más alto hundiéndolo bajo z=0 y truncarlo con un boolean (`cut_below`). Y **verificar los rangos de cada void contra los planos de muro** antes del union — un void que se pasa de largo se funde con el vecino y el corte esperado no existe (el portal v1 quedó flotando sin muro que cortar).

16. 🔴🔴 **"Relleno un agujero y se ve como un plano" casi nunca es la geometría: son las NORMALES** (2026-09-01, mando de Quest importado de FBX). Dos causas que se suman y ninguna se arregla con Fill/Grid Fill:
    - **`mesh.has_custom_normals == True`** (todo FBX de terceros los trae): las caras nuevas nacen fuera de esos datos y sombrean como isla plana **por perfecta que sea la malla**. Fix: `bpy.ops.mesh.customdata_custom_splitnormals_clear()` (las aristas Sharp que queden siguen dando los cantos duros).
    - **Aristas marcadas Sharp en el contorno del agujero** (eran el canto del alojamiento del botón): una Sharp **parte el sombreado** → queda el círculo fantasma. Fix: `e.smooth = True` en las aristas del entorno.
    **Diagnóstico en 2 líneas antes de tocar geometría:** `me.has_custom_normals` y contar aristas con `e.smooth == False` cerca del parche.
17. **Rellenar con continuidad de curvatura: interpolar, NUNCA extrapolar** (misma sesión). `fill_grid(use_interp_simple=False)` da el parche en quads usando las tangentes del contorno. Si aún falta bombeo, **relajación laplaciana con el borde FIJADO** (30 iteraciones, factor 0.6, promedio de vecinos) — converge a una membrana suave y **por construcción no puede sobrepasar** la superficie vecina. ⚠ Ajustar una **cuadrática al anillo vecino y extrapolar al centro produce "cuernos"** (probado: +1.85 mm de bulto en un agujero de r=8 mm), y el filtro por radio se come vértices que no son del parche. Un círculo cortado sobre una cúpula **es plano por naturaleza** (como un paralelo en una esfera): que el borde sea plano NO significa que haya que borrar el anillo.

<!-- Agregar acá cada trampa nueva con fecha, síntoma y arreglo. -->
