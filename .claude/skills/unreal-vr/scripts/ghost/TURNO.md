# Turno de los FANTASMAS (+ dibujo en el cuadro): pasos en orden

> ✅ **Pasos 0-5 HECHOS el 2026-09-30** (tracker: `blueprints/BP_GhostPlayer_SC.md`). Lo que cambió en el camino:
> - `sketch_fx.dsl`: el sonido va en línea (sin parámetro objeto) y hay una `SketchFxApply` compartida (interrupción sin salto).
> - `M_Ghost_SC`: la salida del Custom es `''` (gotcha 560).
> - Sonidos del reproductor: default vacío, porque los WAV no estaban importados (gotcha 563).
> - Nombres corregidos: `%(Integer)`, `CombineRotators`, `DotProduct`, `ToRotator(Quat)`, `…onMaterials` (gotcha 558). `BreakXRMotionControllerState` tiene 9 salidas (gotcha 559).
> - `RcDebug` arreglado (bind puro).
> - Paso 6 (sonidos) → Narrativa.
>
> Falta la **sesión de grabación** (§6).

Todo preparado y probado fuera del editor:
- `lint_dsl.py`: 0 errores en los dos DSL contra la spec. Control positivo: detecta las 9 fallas plantadas.
- `dryrun_ghost.py`: build, write, material y dump contra un editor simulado, dos y tres veces cada uno (idempotentes). Reintento de vectores OK; retoma después de un error del DSL que escapa.
- Archivos en `VR_Test/Saved/ClaudeScripts/ghost/`: `ghost_spec.json`, `ghost_player_graphs.json`, `ghost_recorder_graphs.json`. Se regeneran con `python split_ghost.py`.
- Reglas del turno:
  - una llamada al MCP por vez;
  - contar actores antes y después de cada tanda;
  - guardar con rutas explícitas;
  - PIE detenido antes de compilar;
  - al final, avisar a Narrativa.

## 0. Nivel propio primero (aísla el Undo de los scripts: un script fallido no puede deshacer lo de otra sesión)
1. `SceneTools.get_current_level`. Anotar cuál es; si tiene cambios sin guardar, **no** tocarlo y avisar.
2. `AssetTools.duplicate(/Game/SoulCharger/Shared/QuestController/Test_QuestCtrl → /Game/SoulCharger/Shared/Ghost/Maps/L_GhostRec_SC)`
   → `save_assets([L_GhostRec_SC])` → `SceneTools.load_level(L_GhostRec_SC)`. Canario: 4 `BP_QuestCtrl_SC` más lo del template.

## 1. Encargo chico: `SketchAppear` / `SketchVanish` (~15 min)
1. `read_graph_dsl` de `BPC_TBTool_NC`: `SketchStep2` y las funciones de las fases 1 y 3 → función que escribe el `Reveal` de todos los trazos, y los nombres de `ShowTime`/`HideTime`/`ShowSound`/`HideSound`/`SfxVol`.
   `read_graph_dsl` de `PlaceSketch` y `SketchArchive`: ¿quedan ocultos los trazos?
2. Completar `sketch_fx.dsl` (los `TURNO`).
3. Variables `Z-SketchFx` (`FxT`, `FxDir`, `bFxBusy`), `add_function_graph` × 5 + parámetros (`SketchFxSound(Snd)`, `SketchVis(On)`).
4. `write_graph_dsl` uno por uno (llamada directa) → `compile_blueprint`.
5. **Sin PIE de la Obra**: la prueba es en `Test_Draw` si hay tiempo (dibujar no se puede sin visor: probar con el `SketchSet` vacío = sin errores). Si no hay tiempo, queda probado en el turno de Narrativa.

## 2. Assets de datos y material (~10 min)
1. `execute_tool_script(ghost_build.py)` con `PARTE = 'take'` → clase `BP_GhostTake_SC`, 11 variables y los 10 DA con Id, Text y banderas. Mirar `das` y `da0`.
2. `execute_tool_script(ghost_material.py)` → `M_Ghost_SC`. Mirar `entradas_conectadas` 9 de 9 y `emisivo`. Recompile aparte y **leer el log**.

## 3. Reproductor (~15 min)
1. `ghost_build.py` con `PARTE = 'player'` → `vectores` (json/texto) y `cdo_no_escritas` vacío.
2. **Verificar antes de escribir** los `;;?` de los dos DSL: **una sola corrida de `ghost_nodecheck.py`** (solo lectura), que devuelve los `type_id` que existen para cada filtro:
   - `SetActorHiddenInGame`, `SetWorldSize`, `SetHorizontalAlignment`, `SetVerticalAlignment`, `ToText(String)`;
   - `ToColor(LinearColor)` (si no existe: `Utilities|Struct|MakeColor` con bytes), `RotatorFromAxisAndAngle`;
   - `Rotator|GetForwardVector`, `ComposeRotators`, `TransformRotation`, `Class|BPGhostTakeSC|Get*`.
   Corregir en el `.dsl`, `python lint_dsl.py …` + `python split_ghost.py`.
3. `ghost_write.py` con `CUAL = 'ghost_player'`: repetir hasta `hechos` = todo. Si escapa un error, leer cuál es el grafo, corregirlo y volver a correr.
4. `compile_blueprint` (warnings as errors). `read_graph_dsl` de `GhPose` y `GhAlphaHand` (select anidados) para ver el cableado.

## 4. Grabador + nivel (~15 min)
1. `ghost_build.py` con `PARTE = 'recorder'`. Verificar los `;;?` de `ghost_recorder.dsl`:
   - `EnableInput`, `GetForwardVector`, `Normalize`, `Dot`, `SetRelativeScale3D`, `ToString(Name)`;
   - `BreakXRMotionControllerState` (**orden de salidas**, `get_node_type_pins`), `Quat → Rotator`, `InverseTransformRotation`;
   - `IA_Hand_IndexCurl_*` / `IA_Hand_Grasp_*` en `Input|EnhancedActionValues|`, `Class|BPGhostPlayerSC|PreviewData`/`Stop`.
2. `ghost_write.py` con `CUAL = 'ghost_recorder'` → compile.
3. Colocar en `L_GhostRec_SC` (canario antes y después):
   - `BP_GhostPlayer_SC` (`GhostPreview`) y `BP_GhostRecorder_SC` (`GhostRecorder`), los dos con tag `TestOnly`;
   - `Player` del grabador = el reproductor;
   - posición con el formato de TEXTO en `relativeLocation`, y releer.
4. Guardar: `M_Ghost_SC`, `BP_GhostTake_SC`, los 10 DA, `BP_GhostPlayer_SC`, `BP_GhostRecorder_SC`, `L_GhostRec_SC`.

## 5. Prueba sin visor (~10 min)
1. **Reproductor:** toma sintética (un arco de 3 s del mando derecho, con dos pulsos de gatillo) escrita en `DA_Ghost_Bell` con un script. `AutoPlayId` = `GHOST_BELL` en la instancia → PIE.
   - A los 3 s: `State` 2, `StepIdx` avanzando, `Ages` con 0..3, `LoopCount` sube después de 4 s.
   - Captura del viewport: los ecos.
   - Log sin errores.
2. **Grabador:** en PIE, `DebugPress` = 2 (REC) → a los 3 s `State` 2 → a los 6 s `State` 3 (vista previa) → `DebugPress` = 3 (OK).
   - El DA tiene `Frames` ≈ 180 (poses en 0 sin visor).
   - Después: `ghost_dump.py` y restaurar `DA_Ghost_Bell` (`Frames` 0, `Data` []), para que la toma de prueba no quede como real.
3. Todo a su estado final:
   - `AutoPlayId` None; PIE detenido;
   - guardar con rutas explícitas; canario;
   - avisar a Narrativa → sesión de grabación con Beltrán (Quest Link).

## 6. Sesión de grabación (Beltrán + yo con el editor)
- Beltrán: visor puesto, sentado mirando al frente, **recentrar** (mantener el botón Oculus). PIE en VR por Link en `L_GhostRec_SC`.
- Por gesto: mirar `<`/`>` → mirar `REC` → 3-2-1 → gesto → vista previa → mirar `OK` (o `REDO`).
- Cada 2-3 gestos: yo corro `ghost_dump.py` con `SOLO_RESPALDO = True` **con el PIE abierto**: solo el JSON, porque guardar assets en PIE falla. Si el editor se cae, las tomas se reponen desde esos JSON.
- Al terminar la sesión: se detiene el PIE → `ghost_dump.py` con `SOLO_RESPALDO = False` (marca, guarda con ruta explícita y reescribe los JSON).
- Al terminar: copiar `Saved/ClaudeScripts/ghost/*_take.json` al repo (`scripts/ghost/takes/`).
