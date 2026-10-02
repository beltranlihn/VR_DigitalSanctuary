# obra/unreal/ — lo que Unreal publica para el editor web

Acuerdo entre la sesión del director (Unreal) y la del editor web, 2026-10-02.

## Quién manda
- **Los tiempos de la obra los manda `DA_Partitura_Obra`** (`/Game/SoulCharger/Obra/Partitura/`). Lo leen la Obra (`BP_Obra_SC.LoadPartitura`) y los ensayos de cada etapa (`BP_StageRunner_SC.RLoadPartitura`), así que en los dos se usan los mismos números.
- **El editor web nunca escribe `.uasset`.** Lo que proponga va a `partitura_propuesta.json` (en esta carpeta, con el mismo formato que `partitura.json` → `valores`, solo con las perillas que cambian). Una sesión con el editor de Unreal lo aplica al DA, corre la prueba de humo y vuelve a exportar.
- `web/editor-obra/.../guion.js` es la referencia visual del guion; no es la fuente de los tiempos.

## Archivos
| Archivo | Lo escribe | Qué es |
|---|---|---|
| `partitura.json` | `tools/unreal/partitura_export.py` (paso 1: `tools/unreal/mcp/partitura_export_job.py` con el MCP) | Los valores vivos del DA, con un `hash` corto para detectar cambios |
| `perillas.json` | idem (desde el volcado `Saved/ClaudeScripts/Obra/dump/perillas.json`) | Variables de los 22 BPs centrales: `[nombre, categoría, valor del CDO]` |
| `traza.json` | `python tools/unreal/smoke_obra.py --speed 1 --traza` | La secuencia real de fases de una pasada: `fase`, `etapa`, `reloj_obra_s` (TourT del director) y `speed` |
| `partitura_def.json`, `partitura_binding.json`, `partitura_drift.json`, `contract.json`, `roles.json` | sesión del editor web | Propios del editor (definición sincronizada, a qué elementos del score gobierna cada perilla, diferencias, contrato) |
| `partitura_propuesta.json` | editor web | Cambios propuestos al DA (ver arriba) |

## Respuestas a las preguntas del 2026-10-02
- **a. `Etapa_Tope` de Surrounding:** el DA tiene **205**. La copia por defecto en `BP_Obra_SC` decía 240 y ya está corregida, aunque igual la pisa `LoadPartitura` al arrancar. `Corte_Espera` = 30.
- **b. `Velo_CierreFinT`, `Final_NegroIniPT`, `Hall_VeloGuarda`, `Etapa_TopeK`:** son **derivadas o internas** del director (se calculan a partir de la Partitura o del estado). Están en la categoría `Interno` y no van al DA.
- **c. Dónde van los WAV nuevos:** voces de Alma en `/Game/SoulCharger/Obra/Audio/`, efectos provisorios en `/Game/SoulCharger/Obra/Audio/Placeholder/` y sonidos propios de una mecánica en `/Game/SoulCharger/Mechanics/<Mecánica>/Audio/`. La carpeta de la Obra no se movió.
- **d.** De acuerdo: manda el DA, la web propone con `partitura_propuesta.json` y `guion.js` queda como referencia visual.

## Ojo con `contract.json`
En el reordenamiento 2 se conectaron **63 pines literales** de `BP_Obra_SC` a las copias de la Partitura (categoría `Partitura`). Las entradas de `contract.json` de tipo `literal` que apuntan a tiempos del director ya no son literales: ahora son perillas del DA. Se pueden verificar contra `partitura.json`.
