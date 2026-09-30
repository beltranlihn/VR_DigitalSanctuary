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

## Booleano + bisel + export (2026-09-27, `SM_ChargeRing_SC` — 5 vueltas antes de la receta)

18. **Sin el GUI de Blender abierto no hay MCP, pero hay headless**: `blender.exe --background --python script.py` construye, exporta y hasta renderiza con Cycles/OptiX (8 s por vista a 1000 px en la RTX 4060). Para un asset paramétrico el **script ES la fuente** (regenerar es determinista). Validar la malla leyendo el FBX de vuelta en otro headless, no confiando en el que la escribió.
19. 🔴 **Unreal DESCARTA en silencio los triángulos de menos de ~0,01 mm²** al construir el Static Mesh. Síntoma: `get_triangle_count` da menos que Blender (14.064 contra 21.920). No es la triangulación de n-gons (triangular en Blender no cambió nada): son astillas. **Contarlas antes de exportar** (área < 1e-8 m² tras triangular) y buscar DÓNDE están por posición antes de adivinar la causa.
20. 🔴🔴 **Bisel con `use_clamp_overlap = True` sobre un booleano: el bisel se achica al largo de la arista MÁS CORTA de la cadena.** El booleano deja pares de vértices a micrones donde una arista de la malla cruza el borde cortado cerca de un vértice del cortador; con clamp, el borde entero de la cavidad quedó con bisel de ~1 micrón (visto de lejos: canto vivo; contado: 7.600 astillas). **Receta**: aplicar el booleano → `remove_doubles` con umbral de medio milímetro → disolver (`dissolve_limit`, 0,5°) las aristas coplanares del plano cortado → bisel **sin** clamp.
    - ⚠ **Sin clamp, el desplazamiento del bisel se pasa de la arista vecina y PLIEGA el polígono** si hay aristas cruzando cerca de las esquinas del corte (4 triángulos invertidos, medido con un detector de cruces de aristas en el n-gon). Por eso la disolución de las aristas coplanares es parte de la receta, no un extra.
    - ❌ **Soldar DESPUÉS del bisel (`WELD`) no arregla nada**: aplasta esos tramos en canto vivo y tuerce las normales (desvío p95 de 38° en caras planas). Tampoco `miter_outer`: no era el inglete.
21. 🔴 **Orden de la pila: `WEIGHTED_NORMAL` ANTES de `TRIANGULATE` (con `keep_custom_normals`).** Al revés, el área de cada cara plana se reparte en triángulos chicos, el redondeo "gana" el promedio y la cara sale con dientes de sierra. Y para n-gons cóncavos, `ngon_method='CLIP'`.
22. 💡 **Control de sombreado numérico, sin render**: en las caras que deben ser planas, el ángulo entre la normal de cada esquina (`me.corner_normals`) y la normal de la cara. Sano: máx. < 2°. Más la cuenta de caras "al revés" (normal.x con signo opuesto al lado). Los dos números separan en segundos lo que en render parecen "estrías" o "sierra" sin causa.

## Luz horneada para la obra unlit (2026-09-29, `SM_HallShell_SC`)

23. 🔴 **El import de FBX por MCP (`StaticMeshTools.import_file`) DESCARTA los colores de vértice** (el FBX los traía: verificado leyéndolo de vuelta). Síntoma: el material ve blanco uniforme. **Controlarlo con una perilla que escale solo esa entrada** (si todo el cuadro cambia parejo, el dato no llegó). Arreglo: pasar el dato por **canales de UV** (float, sin sRGB, sin recorte): UV2 = (R,G), UV3 = (B,0), UV1 libre para el lightmap. Recordar que Unreal invierte la V.
24. **Horneado a vértices en Cycles (`bake target VERTEX_COLORS`)**: cada vértice es una muestra aislada → manchas de ruido aunque haya 256 muestras. Receta: **4096 muestras + suavizado laplaciano** de la irradiancia (12 pasadas por vecinos); la luz es de baja frecuencia, el ruido no. Y **normalizar contra la luz que importa** (percentil de lo iluminado), no contra el máximo: un punto pegado al emisor (el labio del óculo, 30×) aplasta todo lo demás a negro.

25. 🔴 **`bmesh.ops.inset_region` y `bevel` sobre una forma CÓNCAVA (sector de anillo) se cruzan consigo mismos** (2026-09-29, baldosas del hall): en Unreal se veían triángulos en punta encimados. Arreglo: construir los anillos a mano, **el mismo contorno analítico desplazado** (R1+o, R2−o, junta+2o, filete−o) con la **misma cantidad de puntos** → tiras de quads limpias; el canto redondeado se hace igual (cuarto de círculo de anillos).
26. **Horneado a vértices de una pieza chica apoyada sobre una superficie ya horneada: COPIAR la luz de abajo** (KDTree + distancia inversa) en vez de hornearla. El horneado propio de las baldosas dio 20× más oscuro que el piso vecino (con la malla rota de la trampa 25, pero no se volvió a probar); copiar garantiza que encaje y no tiene ruido.
27. **Un contorno generado con `atan2` puede salir en sentido horario** → las caras nacen mirando a −Z y `recalc_face_normals` en un sólido abierto puede elegir mal. Orientar por **área con signo** del contorno antes de crear caras.

28. 🔴 **"has degenerate tangent bases / nearly zero tangents / bi-normals" al importar en Unreal = UV0 con triángulos de área CERO** (2026-09-29, baldosas). Dos causas, las dos medibles en Blender antes de exportar (área UV y área 3D por triángulo): (a) **UV planar XY en caras verticales** (costados, canto) → toda la columna comparte UV. Arreglo: correr la UV hacia afuera según lo que baja, `uv = xy + n_horiz·(ztop − z)`. (b) **`TRIANGULATE` CLIP sobre un n-gon con tramos rectos** toma 3 vértices colineales como oreja → triángulo de área cero (Unreal además lo descarta: 8.160 → 8.152). Arreglo: `bmesh.ops.beautify_fill` sobre la cara plana después de triangular. Resultado: 0 y 0, sin advertencias, 8.160 = 8.160.

## Superficie de subdivisión calculada sobre un modelo de referencia (2026-09-29, mando `SM_QuestCtrl_*_SC`)

29. 🔴🔴 **Un modelo de producto "de juego" (paneles separados + mapa de normales) NO se arregla: se MIDE.** El Touch Plus oficial son 25 paneles abiertos, piezas internas y juntas cuyos bordes se curvan hacia adentro. Remallar, fundir por campo de distancia o Poisson, o parchar agujeros siempre dejó juntas, escalones o parches (7 vueltas). Lo que funciona: **jaula de subdivisión (QuadriFlow) + ajuste ICP punto-plano** de sus puntos de control a los datos, **sin** botones, juntas ni 1,2 mm de borde de pieza. La superficie no puede reproducir lo que es más chico que la jaula, y el resto queda a centésimas de mm. Receta y scripts: `assets/quest-controller.md`.
30. **QuadriFlow cancela con "The mesh needs to be manifold and have face normals that point in a consistent direction"** aunque la malla sea perfecta: además toma como *arista de largo cero* toda arista < 1e-4 **unidades**, y en metros eso es 0,1 mm. Fix: `me.transform(Matrix.Scale(1000, 4))` antes y 0,001 después.
31. **Puntitos blancos/grises en Cycles sobre una malla de marching cubes = triángulos degenerados** (normales NaN). `bmesh.ops.dissolve_degenerate` antes de renderizar o exportar (la malla MC de skimage trae cientos).
32. **Poisson (sin "screening") en un hueco grande sin datos se HUNDE como membrana**: sirve para cerrar rendijas de 1 a 2 mm, no para rehacer una zona de 2 cm.
33. **Espejo para el lado contrario: validarlo contra el modelo oficial del otro lado**, no suponerlo. Mediana de distancia en sus vértices: 0,18 mm → el espejo vale.

## Barridos y texturas de texto (2026-09-30, botón `SM_SaveMelody_*_SC`)

34. **Un PNG de texto va SIN voltear.** Blender pone la fila de arriba del archivo en V=1, y el FBX invierte V al pasar a Unreal (V=0 = fila de arriba), así que el mismo PNG se lee derecho en los dos. Voltearlo "porque V crece hacia arriba" dejó el texto cabeza abajo.
35. **Un barrido sobre un contorno en sentido HORARIO da vuelta TODAS las caras laterales.** El chequeo de normales las cuenta: si da el 100 %, es el orden del quad y no la geometría. En `sweep_rrect`: `(A[j], B[j], B[j2], A[j2])`.
36. **Un llenado por UV sobre un aro cerrado deja una marquita en 0 % y una ranura en 100 % en la costura** (x = 0/1) si el borde suave está centrado en `Progress`. Hay que usar el progreso efectivo `Progress · (1 + 2e)` y el borde `smoothstep(0, 2e, pe − x)`.
37. **El Python de Blender no trae PIL**: la textura se hace con el Python del sistema y un script aparte que lee las medidas del generador por `ast` (`gen_save_melody_text.py`).

38. 🔴 **Una malla de revolución puede salir DADA VUELTA ENTERA y el control de `revolve` no lo ve** (2026-09-30, botón del timbre). El control compara cada cara con las normales del MISMO perfil, así que si el perfil va en sentido horario, las dos cosas quedan hacia adentro y coinciden.
    - Blender la muestra bien, porque la emisión se ve de los dos lados. Unreal descarta la cara de atrás y el botón se vio "con la cara abierta".
    - ✅ Control nuevo: el **volumen con signo** de toda malla cerrada, `Σ a·(b×c)/6` sobre los triángulos, tiene que dar > 0.
    - Arreglo: dar vuelta el perfil (`pts[::-1]`, corriendo la parte de cada tramo a su punto de arranque).
39. 🔴 **Unreal INVIERTE la V del FBX.** Un material de Unreal que lee `UV.y` como "0 en el origen" tiene que usar `1 − UV.y` si la vista previa de Blender usaba `UV.y` directo.
    - Pasó con los aros del sensor: en Blender salían del sensor hacia afuera y en Unreal viajaban hacia adentro.
    - Revisar todo material que dependa del SENTIDO de V. Si V solo se usa para un perfil simétrico a lo ancho (el trazo), da igual.

40. ⚠ **Blender headless desde Git Bash: los paths de salida van ABSOLUTOS y en formato Windows** (2026-09-30, `render_hall_tiles_check.py`).
    - Con `-- check_v3` (relativo), el render imprimió OK y no escribió nada: el `render.filepath` relativo no resuelve contra el directorio de la terminal.
    - Pasar `"$(cygpath -w "$PWD/check_v3")"` y citar cada path en un arreglo de bash (`FILES+=("$(cygpath -w …)")`): la ruta del proyecto tiene espacios y un `$FILES` sin comillas la parte.
41. 💡 **`Mesh.transform(M)` en Blender 5.2 SÍ gira las normales a medida** (atributo `custom_normal`; verificado con una normal (0,6, 0, 0,8) que salió (0,8, 0,6, 0)).
    - Con eso se puede construir en el marco cómodo de los helpers (acostado, cara +Z) y exportar girado a los ejes finales, sin rehacer las normales. Lo usa `gen_results.py`: cara +X para Unreal, cara +Z de glTF para la web.
42. 🎨 **Una lámina translúcida CALADA muestra sus huecos durante una entrada por piezas** (2026-09-30, cuadro de resultados).
    - Las ventanas llegaban después que la lámina, y los agujeros se leían como ranuras claras.
    - Solución: lámina ENTERA + el vidrio de cada ventana apoyado encima, con la opacidad compensada: 1 − (1 − 0,55)(1 − a) = el oscuro que tenía la ventana sola.
    - Cuesta una capa translúcida más; se justifica en una pantalla sin mecánica corriendo.
    - La regla del HUD ("la lámina no se mete debajo de un contorno translúcido") sigue valiendo para los CONTORNOS: ahí la superposición parcial sí se ve como un escalón.

<!-- Agregar acá cada trampa nueva con fecha, síntoma y arreglo. -->
