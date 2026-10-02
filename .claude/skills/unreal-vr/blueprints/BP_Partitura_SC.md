# BP_Partitura_SC + DA_Partitura_Obra — los TIEMPOS de toda la obra en un solo lugar

- **refPath**: `/Game/SoulCharger/Obra/Partitura/BP_Partitura_SC.BP_Partitura_SC` (clase, `PrimaryDataAsset`) y el asset de datos `/Game/SoulCharger/Obra/Partitura/DA_Partitura_Obra.DA_Partitura_Obra`. Creados el 2026-10-02 (Narrativa) en el reordenamiento 2.
- **Para qué**: antes los tiempos estaban repartidos entre literales de los grafos de `BP_Obra_SC`, valores de instancia y copias en los runners de ensayo. Cada ajuste rompía otra cosa, porque la obra y el ensayo de una etapa terminaban con números distintos. Ahora hay **una sola fuente**: el DA.
- **Status**: 🟢 60 perillas. La leen `BP_Obra_SC.LoadPartitura` y `BP_StageRunner_SC.RLoadPartitura`. Prueba de humo OK con tiempos idénticos a los de antes del cambio.

## Cómo se usa
- **Cambiar un tiempo**: abrir `DA_Partitura_Obra` en el editor → cambiar el valor → guardar → `python tools/unreal/smoke_obra.py`. La descripción de cada perilla (tooltip) dice qué hace; la lista completa con valores está en `docs/PARTITURA.md`.
- **Agregar un tiempo nuevo** (receta en `docs/GUIA-DE-DIRECCION.md` §7.3): variable en `BP_Partitura_SC` (instance-editable, categoría del momento) → valor en el DA → copia en `BP_Obra_SC` (categoría Partitura) → línea en `LoadPartitura` → getter en el grafo. Y la entrada en `tools/unreal/partitura_def.py` → `python tools/unreal/gen_partitura_doc.py`.
- **Editor web**: `tools/unreal/mcp/partitura_export_job.py` (MCP) + `python tools/unreal/partitura_export.py` → `obra/unreal/partitura.json`. La web propone cambios en `obra/unreal/partitura_propuesta.json`; una sesión con el editor de Unreal los aplica al DA (ver `obra/unreal/LEEME.md`).

## Variables (categorías por momento)
`1 Inicio y Hall` · `2 Etapas` (arreglos de 5, uno por etapa: `Instr_Dur`, `Etapa_Tope` [240,180,120,240,205], `Salida_Dur`, `Carga_Dur`; y `Corte_Espera` 30, `Alma_Entra` 5,5, `Alma_TrasVoz`) · `3 Simulado` (`Sim_EtapaMax` 90) · `4 Final` (regreso, resultados, constelación, créditos, fundido). Detalle y descripciones: `tools/unreal/partitura_def.py`.

## 🔴 Trampas
1. **El DSL quita los guiones bajos**: `Instr_Dur` se lee `Variables|Partitura|GetInstrDur` en BP_Obra_SC y `Class|BPPartituraSC|GetInstrDur` sobre el DA.
2. **El valor del DA gana sobre la copia por defecto de BP_Obra_SC**, porque `LoadPartitura` la pisa al arrancar. Igual conviene que coincidan (pasó con `Etapa_Tope` de Surrounding: 205 en el DA, 240 en la copia).
3. **Derivados que no van al DA**: `Velo_CierreFinT`, `Final_NegroIniPT`, `Hall_VeloGuarda`, `Etapa_TopeK`. Se calculan de la Partitura y viven en la categoría Interno de la Obra.
