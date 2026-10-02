> Anexo de la auditoría de herramientas del 2026-10-01 (revisión: comunicación con Unreal). Lo que manda es [PLAN-EDITOR-OBRA-2026-10-01.md](../PLAN-EDITOR-OBRA-2026-10-01.md).

## Informe: auditoría de la comunicación del editor con Unreal

**Raíz:** `C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/`

**Abreviaturas:**
- `PLAN` = `docs/editor-obra/PLAN-EDITOR-OBRA-2026-10-01.md`
- `MQ` = `web/editor-obra/mockup/src-body.html`
- `TRK/` = `.claude/skills/unreal-vr/blueprints/`
- `REF/` = `.claude/skills/unreal-vr/references/`
- `DUMP` = `VR_Test/Saved/ClaudeScripts/obra/dump/obra_all_now.txt` (de las 13:07)
- `VOF/` = `VR_Test/Saved/ClaudeScripts/vo_final/`
- `MAPA` = `docs/MAPA-DE-AJUSTES.md`
- `WF` = `docs/WORKFLOW-EQUIPO.md`

Trabajé solo leyendo archivos. No usé el MCP `unreal`.

## Veredicto por herramienta

| Herramienta | Estado | Evidencia | Qué cambiar |
|---|---|---|---|
| Partitura en el repo y datos que vienen de Unreal | Corregir | `.gitignore:10` ignora `Saved/`. Quedan fuera del repo `VOF/duraciones_mezcla.txt`, el `DUMP`, `obra/ensayo_export.py` y `turnB2.json`/`step5.json`. | En el plan (§3.1): `harvest_score.py`, lo que produce y la tabla de IDs van versionados en `tools/unreal/` y `obra/unreal/`. Nada canónico en `Saved/`. |
| `compile.mjs` | Riesgo | Node v25.8.1 está instalado en esta PC (comprobado). `GATE.*.late` y `VO.*.end` no existen como estado en Unreal (`anexos/09-critica.md:61`). Las VO internas de Entering las dispara `StepStageVO` de `BP_BreathStage_SC`, no la Obra (`TRK/BP_BreathStage_SC.md:103`). | Compilar solo contra una lista cerrada y versionada de marcas que Unreal emite hoy. Todo lo demás sale como *preview only*. |
| Structs + DataTable | Falta en Unreal | El MCP no crea structs (`REF/gotchas.md:305`, `:670`). `DataTableTools.set_rows`/`get_rows` existen (`REF/toolsets.md:208-210`), pero ningún script del proyecto los usó nunca (grep: solo aparecen en `toolsets.md`). | Probar `set_rows` con una tabla de juguete antes de F4. La columna `Asset` tiene que ser una referencia tipada a SoundBase, nunca un string: si es texto, el sonido no se cocina. |
| Plan B: DataAsset | OK, con un precedente a medias | `BP_GhostTake_SC` y los 10 `DA_Ghost_*` se escribieron por MCP (`TRK/BP_GhostPlayer_SC.md:69-70`; `scripts/ghost/ghost_build.py:19,53`). Todavía no viajaron en un APK: se colocaron la noche del 10-01 (`TRK/BP_Obra_SC.md:334`), después del APK de las 10:01 (`docs/INFORME-NOCHE-2026-10-01.md:6`). | Pasarlo a camino preferido (no necesita a Beltrán). Validar la cocción en el próximo APK. |
| "La tabla se cocina sola" | OK, con condiciones | El APK se arma con `-map=` y el cooker ignora `MapsToCook` (`WF:149`). La Obra no está en `MapsToCook` (`VR_Test/Config/DefaultGame.ini:131-137`) ni es `GameDefaultMap` (`DefaultEngine.ini:7`). La Obra más sus 6 celdas son 1351 paquetes (`docs/PLAN-NOCHE-2026-09-30.md:270`). | Es cierto si `BP_ScorePlayer_SC` queda colocado en `L_SoulCharger_Obra` (o en una celda del `-map=`) con referencia de objeto. Falta versionar la receta `-map=` de la Obra: no tiene fila en la tabla de `WF:154-160`. |
| `BP_ScorePlayer_SC` | Falta en Unreal | Ya existe `ScoreStep` en BreathStage (`TRK/BP_BreathStage_SC.md:95`). El DSL resuelve nombres repetidos hacia otra clase (`TRK/BP_Obra_SC.md:64`). Los directores recortan `Dt` a 1/30 (`TRK/BP_HallDirector_SC.md:13`). | Nombres únicos. Reloj igual al de los directores: `Dt` recortado × `Speed`. Crear todas sus variables antes de colocarlo (gotcha 402). |
| `OnMark` (dispatcher en la Obra) | Riesgo | `add_event_dispatcher` existe (`REF/toolsets.md:74`), pero agregarlo es un cambio estructural de `BP_Obra_SC` (`REF/gotchas.md:2586`; `TRK/BP_Obra_SC.md:98`). `SetPhase` aparece 22 veces en 15 grafos del DUMP. Los pasos del Hall viven en otro BP. | U1 sin tocar Unreal: tomar las marcas de los `PrintString "OBRA: …"` que ya existen (`DUMP:490`, `:496`, `:504`, `:680`, `:704`). `OnMark` entra después, en la tanda estructural. |
| Acciones Spawn/Destroy | Riesgo | Hoy los objetos son actores colocados y ocultos, y se autoran moviéndolos en el viewport (`MAPA:66-67`; `TRK/BP_Obra_SC.md:175-181`). Lo spawneado nace con los valores de la CDO y se pierden las perillas de instancia. No hay spawn diferido (`REF/gotchas.md:907`). | Spawn sobre una marca (TP), con `Configure` después del spawn, y solo en el negro del velo. Hasta tener eso, las acciones de rol son *preview only*. |
| `ScoreApply` (tres vías en runtime) | Corregir | `PLAN:274`. La decisión 1 la aplica a `Pace*`, `FW_*`, `BellPress*` (`PLAN:342`), que viven en otros BP. | Las perillas de instancia se cambian por propuesta aplicada en el editor. En runtime, solo los literales promovidos (hallazgo 4). |
| `bLegacy<Familia>` | Corregir | Un bool nuevo nace en `false` en la instancia ya colocada (`REF/gotchas.md:1254`, `:1438`). | Polaridad segura: `bScore<Familia>`, donde `false` = camino viejo. También hace falta en `BP_BreathStage_SC` (`StepStageVO`) y en el Hall (`HallSay`, `TRK/BP_HallDirector_SC.md:46`). |
| `harvest_score.py` | Verificar en vivo | Hoy `ensayo_export.py` hace `load_level` (`obra/ensayo_export.py:37`, `:61`). Las celdas son subniveles del persistente (`MAPA:23`), pero la Obra lee el `.umap` guardado, no lo que hay en el editor (`MAPA:116`). Hay HUD, Alma y PlayerStart repetidos entre celdas (`MAPA:28`). | Condición previa: el nivel abierto es la Obra. Si no, abortar (no cargarla). Marcar cada valor con `is_dirty` de su paquete. Usar nivel + etiqueta como clave. Excluir `TestOnly`, salvo lo que la Obra copia del `StageRunner`. |
| Duración de la VO (`GetDuration`) | OK | Se usa en la Obra (`TRK/BP_Obra_SC.md:211`), en el Hall (`TRK/BP_HallDirector_SC.md:46`) y en Entering (`TRK/BP_BreathStage_SC.md:102`). Se lee sin abrir ningún nivel: es la `duration` del SoundWave (`VOF/vo_props_despues.json:2-5`). | Leer cada asset por su ruta completa: `VO_12c` existe en dos carpetas (`vo_props_despues.json:2` y `:127`). `duraciones_mezcla.txt` queda solo como respaldo. |
| Propuestas de perilla (web → Unreal) | OK, se puede hoy | `set_properties`/`get_properties` (`REF/toolsets.md:163`). La CDO no se propaga a la instancia (`TRK/BP_HallDirector_SC.md:111`). | Cada propuesta lleva `{nivel, actor, propiedad, ámbito instancia/CDO/componente, base, valor}`. Se aplica solo si el valor actual = base, y después se guarda el `.umap` de su celda. |
| "Empty sound" + WAV | Corregir | `Content/SoulCharger/Audio` no existe (comprobado). El precedente es `Obra/Audio` (`VOF/importar_mezcla.py:14`), con auto-import (`REF/gotchas.md:2693`). Para sonar en 3D tiene que ser mono (`REF/audio-quest.md:115`), a 48 kHz (`:132`), ADPCM en sonidos cortos (`:146`, `:188`). `Obra/Audio` no se cocina por carpeta (`DefaultGame.ini:138`). | Ruta `/Game/SoulCharger/Obra/Audio/`. Validar mono y 48 kHz al subir el WAV. La sesión baja el archivo del artifact, lo copia, verifica el SoundWave y fija la compresión. Estado visible "en Content, no en el APK" hasta que una cue lo referencie. Afecta `MQ:448` y `PLAN:145`. |
| Perillas de los roles (`MQ:240-250`) | Corregir | Ver hallazgo 3. | Dueño real (nivel, actor, propiedad) y valor real en cada perilla. |
| Espera `G_BREATH` (`MQ:259`, `:461`) | Falta en Unreal | Unreal no tiene una espera con cortafuegos de 25 s ni ayuda a los 12 s. `VO_11h` sale `HelpAfter` (4 s) después, y solo si `Rig.bZone` es falso; la exploración dura `ExploreTime` desde `StageBegin` (`TRK/BP_BreathStage_SC.md:103-105`). | Marcarla *preview only* o dibujar el modelo real. |
| Píldora "3 differences" y revisiones (`MQ:320`, `:322`, `:369`) | Corregir | Son textos fijos y la píldora no abre nada. Solo en el tramo de ejemplo hay al menos 12 diferencias (hallazgo 1). | Popover con las diferencias por tipo, la antigüedad de la cosecha y tres revisiones (hallazgo 7). |
| Insignia de alcance / "142 of 592" (`PLAN:280`) | Corregir | Ningún clip de MQ lleva insignia, y la Biblioteca solo cuenta "592" (`MQ:339`). El 142 es un ejemplo, no un cálculo: hoy llegan 0. | Insignia por clip y "0 of 592 reach Unreal" hasta F4. |
| Traza `SCORE\|…` en logcat | Falta en Unreal | `PrintString` sigue escribiendo al log aunque los mensajes en pantalla estén apagados (`DefaultEngine.ini:217-219`). En Development se lee por logcat (`REF/gotchas.md:2433`, `:2493`). | Al arrancar, `SCORE\|rev\|<rev>\|<hash>\|<n>`. Por cada cue, `SCORE\|t\|marca\|cue`. |
| "Probar desde aquí" (`ProbeStart`) | Riesgo | El MCP no puede marcar una variable como `Transient`: solo maneja instance-editable, categoría y replicación (`REF/toolsets.md:61-64`). | Si no puede ser Transient: que no esté en el nivel, o que la sesión la devuelva a −1 antes de guardar. |
| Override JSON en el APK (F6) | Verificar en vivo | AndroidFileServer está apagado (`VR_Test.uproject:33-34`). JsonBlueprintUtilities viene apagado de fábrica (`Engine/Plugins/JsonBlueprintUtilities/JsonBlueprintUtilities.uplugin:17`). | AndroidFileServer no hace falta para un `adb push` a `Saved` del paquete (es la ruta que usa Calibración, `WF:156`). El bloqueo real es JsonBlueprintUtilities. |
| Ambientes como primera familia (`PLAN:344`) | Riesgo | Qué ambiente suena y cuándo es un literal de `AmbPick` (`TRK/BP_Obra_SC.md:367-378`). Solo `AmbClips`, `AmbVolumes` y `AmbFadeIn`/`AmbFadeOut` son perillas (`:200`). El volcado de `AmbPick` ya no es el vigente (`dump/ambpick_live.txt:1-63`, contra "reescrito sin bind" en `:367`). | Mover un ambiente en el tiempo exige cirugía en `AmbPick`: no es el camino mínimo. Además `MQ:288` pone AMB_05 en Entering, y Unreal toca el 4 (Breath, `TRK/BP_Obra_SC.md:372`). |

## Hallazgos importantes

1. **Grave: el tramo de ejemplo de la maqueta no es la obra que corre en Unreal, y aun así la píldora dice "3 differences".** Diferencias en Entering:
   - **Duraciones de VO:** la maqueta tiene 7,4 / 4,9 / 6,3 / 3,1 / 4,6 / 2,4 s para VO_10 / VO_11 / VO_11b / VO_11h / VO_12 / VO_12c (`MQ:264-269`). La mezcla final dice 8,50 / 5,84 / 7,45 / 3,40 / 5,24 / 3,56 s (`VOF/duraciones_mezcla.txt:16-21`). Además, el texto de VO_12c ya es "Three… two… one… inhale." (`TRK/BP_BreathStage_SC.md:94`).
   - **La espera `G_BREATH` no existe.** En Unreal:
     - VO_11 sale a `ToolDelay + SayAfterTool` (0,8 + 1 s) después de `StageIntro`;
     - VO_11b sale con `StageBegin`;
     - VO_12 sale a `ExploreTime − duración − 0,4` (`TRK/BP_BreathStage_SC.md:103-105`).
     - En el PIE, de `StageBegin` al pacer pasaron 17,3 s (11,59 → 28,90; `:107`). La maqueta encadena unos 26 s y su Biblioteca dice "≈18 s" solo para la exploración libre (`MQ:326`).
   - **Cuenta del pacer:** `CountTime` 3,0 en la maqueta (`MQ:246`), 3,6 en Unreal (`TRK/BP_BreathStage_SC.md:95`).
   - **Alma:** en la maqueta aparece a los 8,5 s y habla 1,2 s después (`MQ:274`, `:264`). En Unreal la fase 0 termina con T ≥ 4,7 (`TRK/BP_Obra_SC.md:206`) y la bienvenida espera 1,5 s (`DUMP:968`).
   - **Título:** 0→3,5 s y 6→9 s en la maqueta (`MQ:271`), contra 0,5→2,3 s y 3,3→4,5 s en Unreal (`TRK/BP_Obra_SC.md:206`).
   - **Ambiente:** la maqueta pone AMB_05 en Entering (`MQ:288`); Unreal toca el 4 (`TRK/BP_Obra_SC.md:372`).
   - **Agacharse bajo la voz:** el bus "AMB (ducks under voice)" (`MQ:472`) no existe en Unreal; no encontré ducking ni SoundMix en el tracker de la Obra, en `audio-quest.md` ni en `MAPA`.
   - **Lead-in de 1,5 s en toda VO** (`MQ:470`): solo lo tiene la bienvenida. Las VO internas de la etapa salen sin espera (`TRK/BP_BreathStage_SC.md:102`).
   - **VO_35a:** la maqueta la marca "unused · orphan" (`MQ:329`), pero suena en `ShareExit` (`DUMP:1696`).

   **Corrección:** sembrar el tramo de ejemplo con la cosecha y los trackers, no con `guion.js`, y que la píldora se calcule en vez de estar escrita.

2. **Grave: el plan no define un primer cambio que se pueda verificar en el APK. Este es el camino mínimo (prioridad 4).** Los ambientes no sirven para empezar: cuándo cambian depende de un literal de `AmbPick`, en un grafo de la Obra. En cambio, **la cadena de VO de Entering ya está hecha entera con perillas de instancia** de `Entering_Stage` en Test_Entering: `ToolDelay`, `SayAfterTool`, `SayGap`, `HelpAfter`, `ExploreTime` (`TRK/BP_BreathStage_SC.md:86`, `:105`). Pasos:
   1. **En la web:** el inicio de VO_11 queda atado a `S0.INTRO` + (`ToolDelay` + `SayAfterTool`). Arrastrar el clip no mueve segundos libres: genera la propuesta `{level:/Game/Test_Entering, actor:Entering_Stage, prop:SayAfterTool, base:1.0, value:1.5, scoreRev}`.
   2. **En el turno de la cola**, con la Obra abierta:
      - `get_properties`: si el valor actual no es la base, hay conflicto y no se aplica;
      - `set_properties` y releer el valor;
      - guardar con `save_assets(['/Game/Test_Entering'])` y contar actores antes y después;
      - commit del `.umap`.
   3. **Empaque** en Development con el `-map=` de la Obra (`WF:149`).
   4. **Verificación sin tocar Blueprints:** en logcat, el tiempo entre `OBRA: StageIntro` (`DUMP:490`) y el siguiente `ALMA: SayClip` (`TRK/BP_Alma_SC.md:158`) tiene que ser `ToolDelay + SayAfterTool`. Hoy da 1,8 s (PIE en `TRK/BP_BreathStage_SC.md:107`).

   Costo: un turno de cola y un empaque. Cero cambios estructurales, cero structs.

   Riesgo: si Alma no está visible, `StageSay` cae a sonido 2D y no se escribe `ALMA: SayClip` (`:102`). Por eso hay que hacer antes un control positivo en PIE.

   Siguiente escalón: cambiar un literal de `BP_Obra_SC` con `set_pin_value`, que no es estructural. Por ejemplo, el 1,5 de `ObraSayLater` (`DUMP:968-976`).

3. **Alta: varias perillas de los roles tienen el dueño o el valor equivocado (`MQ:240-250`).**
   - **Timbre:** `BellPressDepth` y `BellPressTime` son de `HallDirector` (`TRK/BP_HallDirector_SC.md:107`), no de `BP_BellArt_SC`. "Appear" es `Appear.Duration`, un componente del actor `Timbre` en Test_Hall (`MAPA:66`; `TRK/BPC_AppearLuz_SC.md:29`).
   - **Sensor:** en la Obra manda `UserTool_Obra`; `Entering_UserTool` es TestOnly y se descarta (`MAPA:192`; `TRK/BP_UserTool_SC.md:14`, `:27`).
   - **Pacer:**
     - "Rhythm" no es una variable: son `InhaleTime`, `Hold1Time`, `ExhaleTime`, `Hold2Time`, y si `Preset` ≠ 0 los pisa (`TRK/BP_Pacer_SC.md:43`; `MAPA:176`).
     - El tracker dice que la instancia tiene `Preset` 1 (`TRK/BP_Pacer_SC.md:72`); hay que verificarlo.
     - Los sonidos están horneados para 4-3-4-3 (`:86`), así que el ritmo va con candado.
   - **Alma:**
     - En la Obra, el tamaño real depende también de la escala del TP de la etapa (`TRK/BP_Obra_SC.md:232`).
     - "Stays VO + 3" es un literal, no una perilla (`:296`).
   - **Aviso:** `DiscTime` existe solo en la CDO y va acoplado a un literal de `BP_Disclaimer_SC.DiscStep` (`TRK/BP_Obra_SC.md:383-384`). El editor tiene que tratarlos como un par.

4. **Alta: `ScoreApply` con tres vías en runtime es caro y no hace falta para las perillas de instancia.**
   - No encontré un nodo genérico "Set por nombre" en la paleta. Las `Set*PropertyByName` de KismetSystemLibrary son de uso interno; hay que confirmarlo con `find_node_types`.
   - Sin ese nodo, cada perilla necesita su rama, su cast y su setter en otro BP.
   - Propuesta:
     - **Perillas de instancia:** propuesta aplicada en el editor (hallazgo 2).
     - **Literales promovidos:** el runtime los lee de la tabla a arrays paralelos (`KnobNames[]`, `KnobValues[]`, el mismo patrón que `DA_Ghost`), y si falta el dato usa el literal actual.
   - Así se evitan unas 30 variables nuevas en la Obra (`anexos/03-unreal-orquestacion.md:199`) y el problema de que nazcan en 0.

5. **Alta: el doble disparo no es solo de la Obra.**
   - Las VO de etapa las disparan los BP de cada etapa (`StepStageVO`, `TRK/BP_BreathStage_SC.md:103`) y el Hall (`HallSay`).
   - Si `BP_ScorePlayer_SC` dispara VO_11, va a sonar dos veces, salvo que haya un corte en `BP_BreathStage_SC`, que es un binario de otra sesión.
   - El corte tiene que ser de polaridad segura (tabla, fila `bLegacy`).

6. **Alta: la cosecha sin `load_level` depende de condiciones que nadie garantiza.**
   - Las sesiones abren otros niveles a propósito para hacer cambios estructurales (`TRK/BP_Obra_SC.md:98`; `TRK/BP_BreathStage_SC.md:98`).
   - La cosecha lee lo que hay en memoria, que puede no estar guardado, mientras la Obra lee el `.umap` (`MAPA:116`).
   - **`ImportedRev`:** el plan lo pone entre lo que trae la cosecha (`PLAN:286`), pero el anexo 07 solo lo escribe al log en el BeginPlay (`anexos/07-propuesta-arquitectura.md:134`). Sin PIE, el editor no lo puede leer.
   - **Corrección:** guardar rev y hash como una fila (o un campo) del asset de la tabla. La cosecha lo lee con `get_rows` y el APK lo imprime al arrancar.

7. **Media: hay tres revisiones distintas, y la maqueta muestra una sola ("Unreal rev 41").**
   - Las tres son: la de la partitura, la del asset en el editor (lo que trae la cosecha) y la del APK (solo por logcat).
   - **Hasta que exista la traza:** un registro `obra/score/builds.json` con `{apk, fecha, commit, scoreRev}`, que escribe quien empaqueta. La identidad del APK se confirma con `aapt2 dump badging` (`WF:115`) y la fecha del archivo.
   - **Lectura del logcat:** `adb logcat -v time | Select-String "SCORE\||OBRA:"`. Sin `logcat -c` si otro script está volcando el log (memoria `noche-2026-10-01-correcciones-y-apk.md:25`).
   - **De dónde sale cada diferencia de la píldora:**
     - perillas: valor cosechado contra la base de la partitura;
     - VO: duración del SoundWave contra la que tiene guardada el editor;
     - poses de TP: con tolerancia;
     - literales: solo con un volcado DSL nuevo. El DUMP es anterior a `AmbPick` v2, a `IntroTitle` +5 y a `DiscTime` 19 (`TRK/BP_Obra_SC.md:367-387`); hasta tenerlo, mostrar "not checked".
   - Las propuestas pendientes no son diferencias. Los elementos sin contraparte en Unreal (G_BREATH, HAP_*) cuentan para el alcance, no para la píldora.

8. **Media: los IDs de la web no coinciden con los assets de Unreal.**
   - `FX_BELLRING`, `FX_TOOLAPPEAR_BREATH`, `FX_BREATHCOUNT` no existen. Lo que hay es `Core/Audio/Sounds/Bell`, `BreathCount`, `Mechanics/Pacer/Audio/SND_Pacer*`, y el sensor aparece con el sonido ProtoSelect (`TRK/BP_UserTool_SC.md:14`).
   - Para los ambientes, la correspondencia es AMB_0K = `AmbClips[K−1]` = `Core/Audio/AmbientClips/Ambient_Clip_K_-_*`, pero Attracting usa el 8 (`TRK/BP_Obra_SC.md:375`).
   - No hay assets HAP_*, y OpenXR no reproduce una forma de onda háptica (`REF/audio-quest.md:158`).
   - **Corrección:** que la cosecha escriba `obra/unreal/idmap.json`. Sin ese mapa, el alcance no se puede calcular.

9. **Media: un solo escritor para el asset de la tabla.**
   - `PLAN:263` y `anexos/07:166` permiten "Reimport de Beltrán o MCP", es decir, dos personas escribiendo el mismo binario.
   - "Beltrán reimporta solo" es dudoso: igual necesita pasar de la base al repo, compilar, reimportar, guardar, hacer commit y empaquetar.
   - **Recomendación:** DataAsset escrito solo por MCP, en el turno de la cola.

10. **Media: el reloj de `BP_ScorePlayer_SC`.**
    - `FinalFlow` corre unas 1,5 veces por cuadro y el reloj de `FlowBye` va a 1,5× (`TRK/BP_Obra_SC.md:207`).
    - El Hall recorta `Dt` a 1/30 (`TRK/BP_HallDirector_SC.md:13`).
    - Si el player usa el reloj del mundo, en un tirón dispara antes que el director.
    - La traza tiene que llevar los dos relojes: el del director y el real.

11. **Baja: la documentación se contradice. "score v0" tiene que salir de una lectura en vivo, no de los trackers.**
    - Cortafuegos de Recognizing: 150 s (`TRK/BP_Obra_SC.md:26`) o 180 s (`:226`; `DUMP:501`).
    - `DiscTime`: 5 (`:218`), 9 (`:227`) o 19 (`:383`).
    - Título: `:206` contra `:226`.
    - `DebugStart`: 3 (`:347`) o −1 (`:386`).
    - El plan sigue diciendo "aviso 20 contra 9" (`PLAN:57`).
    - `gotchas.md` repite números: hay dos 402 (`:2565`, `:2586`) y dos 383 (`:2442`, `:2493`). Conviene citar por línea.

## Lo que hay que verificar en vivo en Unreal

Para la sesión que tenga el turno, solo lectura salvo el punto 13:

1. **`SceneTools.get_current_level`.** Tiene que ser `/Game/SoulCharger/Obra/L_SoulCharger_Obra`. Anotar qué subniveles están cargados: `/Game/Test_Entering`, `/Game/Test_Heart`, `/Game/Test_Fluid`, `/Game/Test_Sequencer`, `/Game/NeuralCanvas/Maps/L_TBTest_SC`, `/Game/SoulCharger/Mechanics/Hall/Test_Hall`.
2. **`AssetTools.is_dirty`** de esos 7 paquetes.
3. **`BP_Obra_SC_C_0`** (L_SoulCharger_Obra): `DebugStart`, `Speed`, `bSimulated`, `bDisclaimer`, `bGhostsOn`, `AmbClips`, `AmbVolumes`, `AmbFadeIn`, `AmbFadeOut`, `ChargeTimes`, `InstrTime`, `OutroTime`. En `Default__BP_Obra_SC_C`: `DiscTime`.
4. **Volcado DSL nuevo de `BP_Obra_SC`**, por subagente y filtrado:
   - `RunObra`: literales del título, salida de la fase 0, cortafuegos 180/120/240;
   - `AmbPick`: la tabla de K;
   - `StageTimes`: el +3;
   - `AlmaSpeak`: el 1,5 de `ObraSayLater`, y que el clip esté en el pin `Clip` y no en `self`;
   - `IntroTitle`;
   - `BP_Disclaimer_SC.DiscStep`: el literal de `Out`.
5. **`Entering_Stage`** (Test_Entering): `bContract`, `ToolDelay`, `SayAfterTool`, `SayGap`, `HelpAfter`, `ExploreTime`, `CountTime`, `InhaleCueAt`, `CueLead`, `ClipInstr`, `ClipExplore`, `ClipHelp`, `ClipReady`, `CountSound`.
6. **`Entering_Pacer`** (Test_Entering): `Preset`, `InhaleTime`, `Hold1Time`, `ExhaleTime`, `Hold2Time`, `Cycles`, `LeadIn`, `LeadOut`.
7. **`HallDirector`** (Test_Hall): `BellHold`, `FW_Bell`, `FW_Tool`, `FW_Choose`, `BellPressDepth`, `BellPressTime`, `VOAir`, `IntroHold`, `bTestIntro`, `TestFromStep`.
8. **Componentes de aparición:** `Timbre` (Test_Hall), componente `Appear`, propiedad `Duration`. `UserTool_Obra` (Obra): `MorphTime` y `Appear.Duration`.
9. **Alma de la Obra** (la que no es TestOnly): `Size`, `Brightness`. Escala de los TP `sc0_alma_in` y `sc0_alma_side` en Test_Entering.
10. **SoundWaves**, con `get_properties` (`duration`, canales, compresión):
    - `/Game/SoulCharger/Obra/Audio/VO_10`, `VO_11`, `VO_11b`, `VO_11h`, `VO_12`;
    - las dos `VO_12c` (`Mechanics/Breath/Audio` y `Obra/Audio`), más `AssetTools.get_referencers` de cada una;
    - un placeholder (`Obra/Audio/Placeholder/FX_SHAREAPPEAR`), para ver la compresión y los canales que deja el auto-import.
11. **`DataTableTools.search_row_structs("*Score*")`**, para saber si los structs ya existen.
12. **`find_node_types`** con filtro `SetFloatPropertyByName` / `SetDoublePropertyByName` en un grafo de prueba. Decide si `ScoreApply` puede ser genérico.
13. **Control positivo del camino mínimo en PIE.** Con permiso de Beltrán para `DebugStart` 11, porque es su palanca; sin guardar el nivel después. Leer `LogsToolset.GetLogEntries("OBRA: StageIntro|USERTOOL|ALMA: SayClip")`; el intervalo esperado es ~1,8 s. Después, en el APK actual, comprobar con `adb logcat | Select-String "OBRA: StageIntro|ALMA: SayClip"` que esas líneas salen en Development.
14. **Pedirle a Narrativa la línea exacta de `BuildCookRun -map=…`** del APK de la Obra del 10-01 y versionarla en `WF`.