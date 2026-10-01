# Turno de los FANTASMAS v2: pasos en orden (2026-10-01)

Plan: `docs/PLAN-FANTASMAS-V2-2026-10-01.md`. Datos: `v2_datos.md`. La v1 queda en git (`80a03c9`), que hace de respaldo de los assets de `Mechanics/Ghost/`.

## Preparado fuera del editor
- **Fuentes**:
  - `ghost_player.dsl`: 89 grafos.
  - `ghost_recorder.dsl`: 45 grafos.
  - `make_spec.py` → `ghost_spec.json` (v2).
  - `lint_dsl.py`: 0 errores en los dos. v2 además detecta literales a funciones propias, la cantidad de argumentos y las llamadas a `Class|BPGhost*`.
  - `python make_spec.py && python split_ghost.py` regenera en `VR_Test/Saved/ClaudeScripts/ghost/`:
    - `ghost_spec.json`;
    - `ghost_player_graphs.json`;
    - `ghost_recorder_graphs.json`;
    - `node_ids.json`.
- **Scripts del turno** (todos con `T()` que atrapa todo; ninguno levanta excepción):
  - `ghost_material.py`;
  - `ghost_build.py` (`clear` / `take` / `player` / `recorder`);
  - `ghost_nodecheck.py` (solo lectura);
  - `ghost_write.py` (sin cambios de v1);
  - `ghost_merge.py`;
  - `ghost_studio.py`;
  - `ghost_synth.py`;
  - `ghost_show.py`, con `ghost_png.py` del lado local;
  - `ghost_dump.py`.

## Reglas del turno
- Una llamada MCP por vez.
- Canario de actores antes y después de cada tanda.
- Guardar con rutas explícitas.
- PIE detenido antes de compilar.
- `save_assets` antes de cada `StartPIE`.
- Recompilar el material SIN MIDs vivas.
- No tocar Test_Hall, Test_Sequencer ni L_TBTest_SC (solo lectura).
- Al soltar, avisar a Narrativa.

## 0. Arranque
1. `SceneTools.get_current_level`. Lo deja Narrativa: la Obra o Test_Results, guardado y sin PIE.
2. 💡 Si está abierta `L_SoulCharger_Obra`, sus 6 niveles de test están cargados como subniveles.
   - Leer **solo lectura** las transforms reales de `Timbre`, `Sensor` y `HallSoul_0..4`. Corregir `STATIONS` de `ghost_studio.py` si difieren de 48/28.
   - Si no está abierta, seguir con `v2_datos.md`.
3. `SceneTools.load_level(/Game/SoulCharger/Mechanics/Ghost/L_GhostRec_SC)`. Canario: anotar la cuenta de actores.

## 1. Material (antes de que exista cualquier vista previa con MIDs)
1. `execute_tool_script(ghost_material.py)`. Mirar:
   - `flags`: translúcido, con instanced y skeletal;
   - `inst`;
   - `emisivo_entradas` 3/3;
   - `opacidad_entradas` 8/8.
2. `MaterialTools.recompile(M_Ghost_SC)` APARTE → leer el log → `save_assets([M_Ghost_SC])`.

## 2. Armado
1. `ghost_build.py` con `PARTE='clear'`, **una sola vez**. Mirar los nodos borrados y las funciones quitadas: 33 del grabador y 43 del reproductor.
2. `PARTE='take'`. Mirar:
   - `vars_quitadas` = `bUseRight`, `bUseLeft`;
   - `das` 10 ok;
   - `da_attract`: Stride 34, HoldL 4, Extra 1, DemoTime 12.
3. `PARTE='player'`. Mirar:
   - `vars_quitadas`: 23, entre ellas **BeamR y BeamL ANTES** de crear los componentes;
   - `componentes`: 14 creados;
   - `HandR_copia` y `HandL_copia` ok;
   - `vectores`: `HandXfR` "del pawn";
   - `cdo_no_escritas` vacío.
   - ⚠ Si `add_component` no cuelga los componentes de la raíz o no acepta el nombre: mirar `ActorTools.get_components(CDO)` y corregir a mano.
4. `PARTE='recorder'`: `vars_quitadas` 9 y `funciones_nuevas` 44.
5. `compile_blueprint` de los dos. Los grafos están vacíos, así que tiene que compilar.

## 3. Nombres de nodo
1. `ghost_nodecheck.py` (solo lectura): `ok` / `total` y `faltan` con candidatos.
2. Corregir en el `.dsl` → `python lint_dsl.py …` + `python split_ghost.py` → volver a correr nodecheck hasta `faltan` = {}.
   - Los más dudosos (`;;?`): `ClearInstances`, `SetNumCustomDataFloats`, `SetCustomDataValue`, `UpdateInstanceTransform`, `AddInstance`, `GetNumMaterials`, `VectorLength`, `VInterpTo`, `MakeRotfromZ`, `GetAllActorswithTag`, `SetActorLocation`, `FindLookatRotation`.
   - Para el ORDEN de pines de los de ISM (`AddInstances`, `UpdateInstanceTransform`, `SetCustomDataValue`): `get_node_type_pins` en una función de descarte (gotcha 551: crea nodos), o pasar todo por palabra clave.

## 4. Escritura
1. `ghost_write.py` con `CUAL='ghost_player'`: repetir hasta que `hechos` cubra los 90 grafos. Si escapa un error, ver qué grafo falló, corregir el DSL y volver a correr: es idempotente (gotcha 557).
2. `compile_blueprint(BP_GhostPlayer_SC, warnings_as_errors=True)`.
3. Leer `read_graph_dsl` de `GhInstData`, `GhEchoInst` y `GhPlaceIsm`: los pines de ISM. Leer también una llamada con argumento cableado (`GhJump`) para descartar el bug de los literales.
4. Lo mismo con `CUAL='ghost_recorder'`. Compilar y leer `RcCapture`: son 34 floats.
5. `save_assets` de los dos BP.

## 5. Mallas fundidas y estudio (en L_GhostRec_SC)
1. `ghost_merge.py`:
   - `piezas` completas, `merge` ok;
   - bounds del sensor, el SAVE y la paleta centrados cerca de (0, 0, z);
   - `cdo_*` ok;
   - actores antes = después.
   - Si un fundido sale corrido de pivote, corregir `SaveXf`/`PaletteXf`/`SensorXf` o volver a la malla principal.
2. `ghost_studio.py`:
   - `ojos`;
   - 7 estaciones con `pos` True;
   - `grabador_ghosts` 7;
   - actores después ≥ antes;
   - `guardado` True.

## 6. Prueba sin visor
1. `ghost_synth.py CUAL='bell'` → `ghost_show.py LABEL='Ghost_BELL'` → localmente `python ghost_png.py Ghost_BELL` → mirar los PNG:
   - la mano llega al timbre;
   - los puntos del recorrido;
   - el texto debajo.
2. Lo mismo con `CUAL='attract'` (`LABEL='Ghost_ATTRACT'`: la esfera y el haz) y con `CUAL='draw'` (`LABEL='Ghost_DRAW'`: el trazo y la paleta).
3. PIE (Simulate) con `bAutoPlay` en `Ghost_BELL`:
   - `get_properties` del actor de PIE: `State` 1 → 2 → 3 → 2, `StepIdx` avanza, `LoopCount` sube;
   - `GetLogEntries` "Accessed None" (category "").
   - Después StopPIE y `bAutoPlay` false.
4. **Restaurar** los 3 DA: `ghost_synth.py RESTAURAR=True` con cada `CUAL`.
5. Guardar con rutas explícitas: los 3 DA, los 2 BP, el material, las 3 mallas fundidas y `L_GhostRec_SC`.

## 7. Primera prueba con Beltrán (Quest Link)
1. Él: visor, PIE en VR en `L_GhostRec_SC`, sentado y recentrado. `GHOST_BELL` (1/7) → mira `REC`:
   - 3 · 2 · 1 en el timbre;
   - bip del "ya";
   - la mano al timbre;
   - bip del final.
2. En el visor ve al instante la vista previa. `OK` o `REDO`.
3. Durante la sesión, cada 2 o 3 gestos: `ghost_dump.py` con `SOLO_RESPALDO=True`, con el PIE abierto. Solo escribe JSON.
4. Él para el Play. Yo:
   - `ghost_dump.py` con `SOLO_RESPALDO=False`;
   - `ghost_show.py LABEL='Ghost_BELL'` → `ghost_png.py` → le mando las capturas (SendUserFile).
   - Él también lo ve en su viewport: slider `PreviewTime`, o Simulate con `bAutoPlay`.
5. Ajustes mirando: `GhostColor`, `TriggerColor`/`TriggerGlow`, `EchoAlpha` (`[1]` = gif puro), `StepHz`, `bShowText`.

## 8. Al cerrar
- Avisar a Narrativa: nivel abierto, guardado y sin PIE.
- Actualizar `blueprints/BP_GhostPlayer_SC.md` + `_INDEX.md` y la memoria.
- Copiar los `*_take.json` a `scripts/ghost/takes/`.
