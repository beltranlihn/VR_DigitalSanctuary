# Generadores de la cirugía del 2026-10-02 (reordenamiento 2)

Scripts de Python que **escriben** scripts para `ProgrammaticToolset.execute_tool_script` (el MCP de Unreal no tiene `exec`: cada job se pega entero). Con ellos se hizo la Partitura y el cierre único de etapa. Ya corrieron: **no se vuelven a correr tal cual** (re-escribir un grafo existente lo duplica). Quedan como referencia y como base para la próxima cirugía.

| Archivo | Qué generó |
|---|---|
| `bp_tpl.py` | Plantilla común: helper `G()`, escritura del resultado a json en `Saved/`, prueba en seco en un grafo `_tmp_` con sus parámetros |
| `surg_lib.py` | Motor de cirugía de literales: encuentra el nodo por tipo + valor literal + filtros de origen, crea el getter `Variables|Partitura|GetX` y lo conecta; si el conteo no es el esperado, no toca nada |
| `gen_partitura_da.py` | `BP_Partitura_SC` + `DA_Partitura_Obra` desde `tools/unreal/partitura_def.py` |
| `gen_obra_part.py` | `LoadPartitura` en `BP_Obra_SC` y la conexión de los 63 literales |
| `gen_cortes2.py` | `EtapaCortes` + `RequestEnd(K)` + el `SimCut` nuevo en la Obra |
| `gen_runner.py` | `RLoadPartitura`, `RRequestEnd`, `RCortes`, `RAlmaIn` en `BP_StageRunner_SC` |
| `gen_seqfix.py` | `StageRequestEnd` + `ReqHasMelody` en `BP_Sequencer_SC` |
| `gen_obraorden.py` | Categorías de las variables de la Obra y borrado de las que no se usaban |
| `gen_smoke.py` | `ObraCmdLine` + `SmokeTick` (prueba de humo) |

Rutas: son las de **antes** del reordenamiento de carpetas (`/Game/SoulCharger/Obra/BP_Obra_SC`, ahora en `Obra/Blueprints/`). Pasarlas por `tools/unreal/reorden_contenido_2026-10-02.json` antes de reusar.
