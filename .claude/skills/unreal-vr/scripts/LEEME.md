# scripts/ — qué es cada cosa (clasificado el 2026-11-14)

Los archivos no se movieron de lugar, porque trackers, gotchas y memorias los nombran por esta ruta. Este índice dice cuáles son
**herramientas que se reusan** y cuáles son **la fuente de un asset o de un grafo ya construido** (se usan solo para rehacerlo).

## 🔧 Herramientas que se reusan (empezar por acá)
| Script | Para qué |
|---|---|
| `safe_script.py` | 🔴 **plantilla obligatoria** de todo `execute_tool_script`: nunca deja escapar una excepción (si no, el Undo global se come trabajo ajeno) + canario de actores |
| `clean_orphans.py` | borra nodos huérfanos de un BP por vitalidad dirigida y compara el DSL antes/después. ⚠ Al usarlo: agregar `EdGraphNode_Comment` a lo protegido y envolver `run()` en `try/except BaseException` (así se usó el 11-14) |
| `auto_layout.py` | ordena visualmente un grafo grande |
| `chk_isvalid.py` | gotcha 590: marca sentencias del DSL que terminan dentro de un `IsValid` y se comen lo que sigue |
| `dsl_sim.py` | ejecuta un `.dsl` sin Unreal y lo compara con un modelo de referencia (lo usan `*_sim.py`) |
| `dryrun_material_script.py` | corre un script de armado de material (`apply_*.py`) contra un editor simulado, sin Unreal |
| `memcap.py` | corre un script de Python con tope de memoria (gotcha 492) |
| `reskin_to_skeleton.py` | re-skinea una malla ajena al esqueleto de otra (Blender headless) |
| `rename_package.py` | renombra los artefactos de un archive de Android |

## 📏 Medir rendimiento en el Quest
`quest_*.ps1` (cada uno lanza una sesión de medición: A/B, modos, fases, borde, sesión larga, por etapa) + `resumen_*.py` (resume
cada sesión) + `read_csv_perf.py` (CsvProfiler). Cómo se usan: `references/profiling-quest.md`. Para medir rápido sin esto, ver la
gotcha 642 (FPS por adb filtrando por el proceso de la app, carga de la GPU por `gpubusy`).

## 🧬 Fuentes de grafos (DSL) ya construidos
Se escribieron con `write_graph_dsl` una vez. 🔴 **No se re-escriben sobre un grafo existente: lo duplican** (regla de oro 2).
Sirven para leer qué hace un grafo o rehacerlo desde cero.
- **Entering (respiración):** `breath_air.dsl` (el aliento), `valley_live.dsl` (la capa viva del valle), `vida.dsl` (polvo y
  ráfagas).
- **Loving:**
  - `BP_FluidMedium_SC`: `fluid_*.dsl` (fluido, manos, viaje, activación).
  - `BP_LovingCell_SC`: `loving_*.dsl` (fases de vida, intro, contrato, tick).
- **Surrounding (dibujo):** `draw_sea.dsl` (el océano), `tb_contract.dsl` / `tb_tour.dsl` (contratos de `BP_TBDirector_NC`).
- **Final:** `journey_content*.dsl` (contenido del cuadro de resultados).
- **Generadores de DSL:** `appear_luz_applyt_dsl.py`, `hud_entry_dsl.py`, `results_entry_dsl.py`, `share_button_dsl.py`.
- Lo que vino después (demo, Inner Canvas, Hall, arpa, Focus, Thoughts…) vive en `VR_Test/Saved/ClaudeScripts/<tema>/`. La copia
  está en `tools/bp_fuentes/`.

## 🎨 Generadores de mallas, materiales y sonidos (cada uno hizo un asset de la Obra, septiembre-octubre)
Patrón: `*_model.py` (modelo de referencia en numpy) → `gen_*.py` (malla o textura) → `plan_*.py` (plan del material en JSON) →
`apply_*.py` (lo arma en el editor) → `sim_*` / `*_dryrun.py` / `preview_*` / `render_*` (verificar sin Unreal).
- **Entering:**
  - el aliento: `breath_air_*`, `gen_breath_air`, `sim_breath_air`;
  - el valle: `valley_model`, `gen_breath_valley`, `plan_/apply_valley_material_*`, `preview_breath_valley`;
  - la capa de vida: `vida_*`, `gen_valley_dust`, `plan_vida_materials`, `apply_vida_*`, `rollback_vida_gust_valley`,
    `render_vida_valle`, `make_vida_sounds`.
- **Recognizing:** `heart_dust_model`, `gen_heart_dust` (+ `_demo`), `plan_/apply_heart_dust_*`, `gen_heart_membrane`,
  `gen_heart_orb` (+ `_lo`).
- **Loving:** `gen_loving_canvases`, `compose_loving` + `check_loving_hlsl` (los Custom HLSL), `gen_fluid_canvases`,
  `make_mind_sounds`.
- **Attracting:** `gen_blob_orb`, `gen_blob_tube`; el salar: `gen_chladni_material`, `apply_chladni_material`, `gen_salt_cells`,
  `gen_sand_texture`.
- **Surrounding:** `draw_sea_model`, `gen_draw_sea` (+ `_hlsl`), `plan_/apply_draw_sea_*`, `dryrun_draw_sea`, `draw_sea_sim`.
- **Alma y la familia de objetos:** `alma_aura_model`, `gen_alma_aura`, `plan_/apply_alma_aura_*`, `plan_/apply_sc_materials`
  (timbre, SAVE, sensor), `plan_results_materials`.

## 📁 Carpetas
`attract/`, `feed/`, `focus/`, `harp/`, `thoughts/` (experimentos de octubre-noviembre), `ghost/` (fantasmas), `credits/` (créditos),
`hlsl/` + `hlsl_backups/` (Custom HLSL de los materiales), `loving_amoeba/`, `loving_outer/` (la célula de Loving). `tb_appear_plan.md`
= plan de la aparición de la paleta.
