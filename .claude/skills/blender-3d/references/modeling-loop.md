# El bucle de modelado — plan → partes → render → crítica → arreglo

Destilado de **LL3M** (*Large Language 3D Modelers*, threedle, arXiv 2508.08228 — un sistema multi-agente que modela escribiendo `bpy` y llegó a assets complejos) más la práctica del proyecto. La idea central: **el código no se juzga leyéndolo, se juzga renderizando el resultado**.

## 1. Plan: descomponer ANTES de la primera línea

- Partir el asset en **partes con nombre** (silla → patas, asiento, respaldo; campana → cuerpo, badajo, soporte). Cada parte = un bloque/función de código propio.
- Los **detalles se planifican como subtareas explícitas** — si no están en el plan, no van a aparecer ("jarrón sin asas, piano sin teclas" es el modo de falla n.º 3 documentado en LL3M).
- **Parámetros expuestos arriba del script** con nombres descriptivos (`num_ribs = 8`, `bell_height = 0.4`) — son las perillas que Beltrán o una iteración futura van a querer girar sin releer el código.
- Elegir la técnica por parte: primitiva + modificadores para lo simple, `bmesh` para geometría a medida, spin/screw/curve para revoluciones y perfiles. **No apilar cubos donde corresponde un perfil revolucionado** (modo de falla n.º 2).

## 2. Construir por partes, con estructura

- Una **colección** para el asset; jerarquía **padre-hijo** explícita entre partes (mover el padre mueve el todo).
- Nombrar objeto Y datablock de malla (`obj.name` y `obj.data.name`).
- Cada bloque de código recibe lo ya construido y **agrega o edita — no rehace**. En LL3M medido: sin el código previo a la vista, el agente reescribe desde cero y produce un asset visualmente distinto; con él, los cambios quedan localizados.
- Guardar el script de construcción completo en el tracker del asset (`assets/<nombre>.md`) — es la fuente editable para la próxima sesión.

## 3. Verificación visual multi-vista (el corazón del bucle)

Después de cada fase (no solo al final):

1. `render_viewport_to_path` (o `render_thumbnail_to_path`) al **scratchpad**, desde **varias vistas** — mínimo frente, 3/4 y arriba. Una sola vista esconde huecos y desalineaciones.
2. `Read` de las imágenes.
3. **Crítica explícita contra el objetivo**, con estas preguntas fijas:
   - ¿Las partes están **conectadas** o hay huecos/flotantes? (modo de falla n.º 1, el más frecuente — se arregla moviendo en el eje que corresponda, no rehaciendo)
   - ¿Las **proporciones** son las pedidas?
   - ¿Falta algún **detalle** del plan?
   - ¿Las **normales** apuntan afuera? (caras negras/invertidas en el render)
4. Cada problema → **un arreglo localizado** sobre el objeto existente → re-render de esa vista → confirmar que el arreglo entró (verificación del arreglo, no solo del error).

Complemento no visual: `get_object_detail_summary` para números exactos (dimensiones, transform, conteo de polys) cuando el ojo no alcanza — p. ej. confirmar que dos partes comparten el plano de contacto.

## 4. Consultar la documentación en vez de adivinar

En LL3M, darle al agente acceso a documentación (RAG) multiplicó ×5.86 el uso de operaciones avanzadas y bajó los errores por generación de 3.29 a 2.43. Acá el equivalente:

- `search_api_docs` / `get_python_api_docs` / `search_manual_docs`, o Grep sobre `C:\Users\beltr\.blender-mcp\src\mcp\blmcp\data\{api,manual}\`.
- **Los nombres de parámetros cambian entre versiones** (ejemplo real: "Specular" → "Specular IOR Level" en el Principled BSDF de 4.x). La doc local ES de la versión instalada (5.2): le gana a la memoria y a cualquier tutorial de internet.
- Ante un error de ejecución: buscar el mensaje en la doc local ANTES del segundo intento a ciegas.

## 5. Criterio de corte

- Si un arreglo **falla 2 veces**, parar de iterar sobre la misma hipótesis: re-renderizar desde otra vista, pedir los números (`get_object_detail_summary`) y replantear — el bug suele estar en otra parte (contexto/modo, no la geometría).
- El bucle converge rápido cuando los arreglos son chicos; si cada iteración toca medio script, la descomposición del paso 1 quedó corta — volver a partirlo.

## 6. Cierre

1. Chequeo Quest ([quest-budgets.md](quest-budgets.md)): triángulos, materiales por malla, sin n-gons.
2. UVs: canal 0 (texturas) + canal 1 (lightmap, sin solapes) — ver [export-unreal.md](export-unreal.md).
3. Escena en Object Mode, transforms aplicados, todo nombrado.
4. Tracker del asset actualizado + encuadre final para Beltrán (`jump_to_view3d_object_by_name`).
