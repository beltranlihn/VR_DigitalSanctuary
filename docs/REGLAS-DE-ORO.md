# Reglas de oro · lo que evita romper Soul Charger

> Una página. Es lo mínimo que tiene que saber cualquiera que toque Blueprints, materiales o niveles (persona o Claude).
> El detalle y la historia de cada regla están en `.claude/skills/unreal-vr/references/gotchas.md` (580+ entradas, de consulta).
> Para ubicar *dónde* se ajusta cada cosa: [GUIA-DE-DIRECCION.md](GUIA-DE-DIRECCION.md).

## A. Antes de tocar
1. **El target es Quest 3 standalone**: renderer móvil, forward, luz horneada, 72 Hz. Lumen, Nanite, VSM y Distance Fields no corren. Lo que diga internet para PC VR casi nunca aplica.
2. **Leer el tracker del BP** (`.claude/skills/unreal-vr/blueprints/`) **y el grafo** antes de cambiarlo. Si algo parecido ya funciona en otro BP, se copia su configuración, no los valores por defecto (ver `references/assets-existentes.md`).
3. **Un tiempo de la obra no se escribe en un grafo.** Va en `DA_Partitura_Obra` (receta en la guía §7.3). Un literal de tiempo suelto es un ajuste que mañana nadie encuentra.
4. **Los valores puestos en la instancia de un nivel de test son finales.** La instancia le gana al Blueprint: cambiar el default del BP no cambia nada si la instancia tiene su propio valor. No se pisan sin pedido.

## B. Mientras se toca
5. **Cambios de estructura** (variables, funciones, componentes) **con un nivel neutro abierto** (`Test_QuestCtrl`), nunca con el nivel donde está colocado el BP: el reinstanciado puede llevarse el actor o sus valores (gotcha 402).
6. **No compilar con PIE corriendo.** Primero se detiene PIE, después se compila y se guarda, y recién ahí se vuelve a arrancar PIE.
7. **Un escritor por estado.** Si dos funciones escriben la misma variable en el mismo cuadro (el velo, el reloj `T`, un parámetro del material), gana la última y el ajuste "no hace nada". Antes de agregar una capa, buscar quién más la escribe.
8. **Grafo que ya existe: cirugía de nodos**, no reescribirlo entero (con el DSL se duplica). Grafo nuevo o vacío: se escribe completo, primero en un grafo `_tmp_`.
9. **Actores: colocar sí, sacar se pregunta.** Antes y después de cada tanda de scripts se cuentan los actores del nivel y se guarda con rutas explícitas: un script que falla puede disparar un Undo que se lleva trabajo.
10. **Toda etapa cumple el contrato**: `StageIntro`, `StageBegin`, `StageRequestEnd` y `StageOutro`, más la bandera `bStageDone`. `StageRequestEnd` **siempre** termina en `bStageDone = true`, haya hecho algo el usuario o no. Una etapa que no cierra deja la obra colgada (guía §4).
11. **Textos dentro del visor, en inglés.** Documentos y comentarios, en español neutro.

## C. Después de tocar
12. **Compilar sin errores → guardar → `python tools/unreal/smoke_obra.py` OK → commit.** La prueba de humo recorre la obra entera sin visor y falla si falta una marca o aparece un error de Blueprint. Si no pasa, el cambio no está terminado.
13. **Verificar el estado estable, no el arranque.** Que un `PrintString` aparezca prueba que el evento corrió, no que tuvo efecto. Se mira el valor que de verdad quedó aplicado: el del material, la instancia o el actor en el cuadro 200, no en el 1.
14. **Actualizar el tracker del BP** y, si cambió un tiempo, `tools/unreal/partitura_def.py` → `gen_partitura_doc.py`.

## D. Git y archivos
15. **`.uasset` y `.umap` son binarios**: nunca dos personas en el mismo asset a la vez. Se commitean hitos, no micro-cambios, y siempre después de *Save All*.
16. **Para cambiar de rama, mergear o traer algo del archivo hay que cerrar Unreal**: con el editor abierto los assets quedan bloqueados y git o el script quedan a medias.
17. **Lo que no se usa no se borra: se archiva** con `tools/unreal/archive_unused.py`, que lo saca del proyecto con un manifiesto y lo puede devolver.

## E. Para Claude (MCP)
18. **Nunca traer un output gigante del MCP al contexto**: filtrar siempre por `type_id_filter` o `node_class`. Si el resultado es largo, va a un archivo en `Saved/` y se busca ahí.
19. **Con PIE corriendo, solo lecturas livianas.** Nada de `set_properties` sobre componentes ni lecturas de grafos (gotcha 582).
20. **Los scripts de `execute_tool_script`** van con `try/except BaseException` y escriben su resultado a un json, porque un error agregado se come el valor de retorno.
