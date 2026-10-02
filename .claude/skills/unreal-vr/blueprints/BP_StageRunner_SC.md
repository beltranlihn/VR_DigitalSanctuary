# BP_StageRunner_SC — el ENSAYO de una etapa en su nivel de test

- **refPath**: `/Game/SoulCharger/Obra/BP_StageRunner_SC.BP_StageRunner_SC` · parent Actor · creado 2026-09-30 (Narrativa, pedido de Beltrán: "Ensayo de etapa primero").
- **Instancias** (label `StageRunner`, tags **`TestOnly` + `TOUR`**): una en cada nivel de test — Test_Entering (K 0), Test_Heart (1), Test_Fluid (2), Test_Sequencer (3), L_TBTest_SC (4). Con cada una: `Alma_Ensayo` (BP_Alma_SC, TestOnly) y 4 TargetPoints **sin TestOnly** `TP_sc<K>_alma_in / _alma_side / _charge / _title` (tag = el nombre sin `TP_`).
- Fuentes: `VR_Test/Saved/ClaudeScripts/Obra/runner.json` (DSL), `runner_build.py`, `ensayo_place*.py` (colocación, idempotente), `ensayo_export.py` (Unreal → web).

## 🔴 Estado vigente (2026-10-02, reordenamiento)
- **Lee la misma Partitura que la Obra**: `RLoadPartitura` (al arrancar) copia `DA_Partitura_Obra` a sus variables de la categoría Partitura. `AlmaTime/InstrTime/OutroTime/TimeoutS/ChargeTime` **ya no son instance-editables** y se calculan de la Partitura: `RAlmaIn` hace `AlmaTime = Duration(VOEntrada[StageK]) + AlmaTrasVoz` y el tope es `EtapaTopeRun = EtapaTope[K] + CorteEspera`. Hay 9 pines conectados a la Partitura. En la instancia quedan solo `StageK`, `Loop`, `Speed`, `EyeRef`, `CTop/CHor`, `TitleMI`, `LevelName` y los tags.
- **Mismo cierre que la Obra**: `RCortes` pide el cierre con `RRequestEnd` (`StageRequestEnd` del BP de la etapa) al llegar a `EtapaTope[K]` y marca `RCortePedido`. El ensayo y la obra terminan las etapas de la misma forma, con los mismos tiempos.
- Variable nueva `VOEntrada` (SoundBase[5], la VO de bienvenida de cada etapa): `CurrentVO` era un int y no servía para medir.
- `LevelName` se usa en `OpenLevel(byName)` cuando `Loop` reinicia el ensayo: tiene que coincidir con el nombre del nivel.

## Status
🟢 **Probado en PIE en Test_Entering (2026-09-30 18:00), sin errores y con reinicio en bucle**: StageEnv → Alma recibe (VO_10, envelope activo) → StageIntro (Alma al costado) → StageBegin → cuenta + pacer, 5 ciclos → StageOutro por fin propio → vista previa del anillo → despedida (VO_13 + VO_14) → velo cierra → `OpenLevel` → arranca de nuevo.
🟢 **Test_Sequencer (2026-10-01 00:06)**: PIE hasta StageBegin sin errores (Alma a 5,5 s, StageIntro a ~15 s, StageBegin a ~21 s).
⬜ Visor. ⬜ PIE de Test_Heart, Test_Fluid y L_TBTest_SC (colocados y guardados, sin correr).
- **2026-10-01: `Title`, `Veil` y `Ghost` nacen OCULTOS** (`bVisible` false en el CDO). Antes nacían visibles y, dentro de la Obra, el título (sort 32700) se veía por encima del velo negro entre que la celda se registraba y su BeginPlay: eran los "textos de las transiciones" al dar Play. `RBoot`/`RStep`/`RGhost` ya los prenden cuando corresponde.

## Qué hace (la misma coreografía que la Obra)
| Fase `RPhase` | Qué | Sale con |
|---|---|---|
| 0 | velo abre 1 → 5 s (`M_TourVeil_SC`, CTop/CHor del runner), título (`TitleMI`) revela 1 → 5,5 y sale 9 → 12,5 en tiempo de título (salta 5,5 → 9 como la Obra); `RWake` a los 0,1 s (Breath `StageEnv`, Loving `TourWake`) | RT ≥ 5,5 → `RAlmaIn` |
| 1 | Alma `AppearAt(TagIn)` + VO de bienvenida (`Alma.PlayClip`) | PT ≥ `AlmaTime` → `MoveTo(TagSide)` + `StageIntro` |
| 2 | instrucciones | PT ≥ `InstrTime` → `StageBegin` |
| 3 | la mecánica | `bStageDone` o PT ≥ `TimeoutS` → `StageOutro` + Alma `Disappear` |
| 4 | salida | PT ≥ `OutroTime` → vista previa del anillo (`Ghost`, SM_ChargeRing_SC en `TagCharge` con su escala, mirando a la cámara) |
| 5 | carga (vista previa) | PT ≥ `ChargeTime` + 1 → K < 4: Alma `AppearAt(TagIn)` → 6; K = 4: → 7 |
| 6 | despedida: VO de la luz a 0,9 s, invitación 0,5 s después de terminar, Alma se va 0,4 s después | → 7 |
| 7 | velo cierra 0 → 6 s | PT ≥ 7 y `Loop` → `OpenLevel(LevelName)` |

**Alturas**: todo punto se lee relativo a los ojos: z en runtime = z del TP + (cámara.z − (PlayerStart.z + `EyeRef`)). `EyeRef` 120 = el mismo supuesto que la Obra (velo a PlayerStart + 120). Así lo que Beltrán sube 20 cm en el editor sube 20 cm en el visor, con cualquier altura de cabeza. El pawn sale del **PlayerStart** del nivel (la Obra teletransporta al mismo PlayerStart).

## Variables de autor (categoría **Ensayo**, instance-editable) — 🔴 la instancia es la fuente
`StageK` · `Loop` (true) · `Speed` (1; sube solo el reloj del ensayo, no el de la etapa) · `AlmaTime` (10,5 / 11,3 / 7,2 / 9,4 / 15 = largo de la VO + ~2 s) · `InstrTime` 6 · `OutroTime` 2,5 · `TimeoutS` (240 / 150 / 120 / 240 / 240, = RunObra) · `ChargeTime` (4, la última 6) · `EyeRef` 120 · `CTop`/`CHor` (velo de la etapa, = CTops/CHors de la Obra) · `TitleMI` (MI_TourTitle_<ETAPA>) · `LevelName` · `TagIn/TagSide/TagCharge/TagTitle` (`sc<K>_*`).
Runtime: `IsObra`, `RPhase`, `RT`, `PT`, `RDone`, `ByeSt`, `PStart`, `PYaw`.

## Cómo lo usa la Obra (`BP_Obra_SC`)
Los niveles de test son las celdas de la Obra, así que runners y TPs llegan solos. `DestroyTestOnly` llama primero a **`ReadRunners`**, que copia de cada runner CTop/CHor → `CTops[K]`/`CHors[K]` y AlmaTime/InstrTime/OutroTime → `StAlma/StInstr/StOutro[K]`; recién después destruye los TestOnly (runners y Alma_Ensayo). En la Obra, el runner ve un BP_Obra_SC en `RBoot` (`IsObra`) y no tickea.
- `AlmaIn(K)` → `TPOverA/TPOverB(K)` ponen ObraAlmaA/B en los TP `TpIn/TpSide[K]` (con la corrección de altura) y `StageTimes(K)` pisa AlmaTime/InstrTime/OutroTime.
- `ChargeStart(K)` → `ChargeTP(K)` (insertado por cirugía entre SetActorScale3D y SetTargetRef) mueve ObraChargeTarget al TP `TpCharge[K]` con su escala.
- `FinalFlow` → `TitleTP()` (fase 0, T < 0,4): el actor de la Obra se ubica 3 m detrás del TP `TpTitle[K]` (el título es un componente a +300).
- Log al arrancar: `OBRA: ensayos de etapa leidos = 5` + `OBRA: TP de ensayo sc0_alma_in = 1`.

## Web (ida y vuelta)
`ensayo_export.py` (execute_tool_script, solo lectura, abre los 5 niveles y vuelve a la Obra) → `Saved/ClaudeScripts/Obra/ensayo_export.json` → `python scratchpad/obra/gen_ensayo_js.py` → `web/prototipo-narrativo/ensayo.js` → publicar. La web aplica el **desplazamiento** de cada TP respecto de la base (220/0/+5, 140/−300/+20, 253/0/+37 × 2,115, 300/0/0), el velo, `CHARGE_T` y la pausa de Alma (AlmaTime − largo de la VO). Web → Unreal: cambiar la instancia del runner o el TP en su nivel de test y volver a exportar.

## 🔴 Trampas
1. Las variables con **categoría** cambian su ruta en el DSL: `Variables|Ensayo|GetStageK`, no `Variables|Default|…` ("does not exist"). Las de otra clase siguen siendo `Class|BPStageRunnerSC|GetX`.
2. `get_actor_transform` devuelve un `_StrictDict`: `t['rotation']['yaw']`, nunca `.get(k, default)`.
3. El sandbox de `execute_tool_script` no tiene `exec` ni `math`: coseno/seno por serie o precalculados.
4. Cambiar `BP_Obra_SC` con **otro nivel abierto** evita el reinstanciado de su instancia (gotcha 402): la Obra se abre después y toma la clase nueva.
