> Anexo de la auditoría de herramientas del 2026-10-01 (revisión: acciones y Agregar). Lo que manda es [PLAN-EDITOR-OBRA-2026-10-01.md](../PLAN-EDITOR-OBRA-2026-10-01.md).

## Veredicto por herramienta

Abreviaturas (rutas desde la raíz del repo):
- `MOCK` = `web/editor-obra/mockup/src-body.html`
- `PLAN` = `docs/editor-obra/PLAN-EDITOR-OBRA-2026-10-01.md`
- `TRK/` = `.claude/skills/unreal-vr/blueprints/`
- `REF/` = `.claude/skills/unreal-vr/references/`
- `DUMP` = `VR_Test/Saved/ClaudeScripts/obra/dump/obra_all_now.txt`. Es el volcado de las 13:07, así que `GhostTick` y `HandTick` no aparecen.

| Herramienta | Estado | Evidencia (qué lo hace hoy en Unreal) | Qué cambiar |
|---|---|---|---|
| **Empty sound + Load WAV** | Corregir / Falta en Unreal | La carpeta destino no existe: PLAN:145 y MOCK:448 dicen `Content/SoulCharger/Audio`. Los FX están en `Content/SoulCharger/Obra/Audio/Placeholder/` (10 `FX_*`) y en `Core/Audio/Sounds/` (Bell, DoorOpen, ProtoSelect…).<br>El MCP no tiene herramienta de audio. Se importa copiando el `.wav` dentro de `Content/` y dejando que el editor lo importe solo (REF/gotchas.md:2693; `VR_Test/Saved/ClaudeScripts/vo_final/importar_mezcla.py:1-2,14-17`). Esa opción está activada solo en la máquina de Beltrán (`VR_Test/Saved/Config/WindowsEditor/EditorPerProjectUserSettings.ini:78,83`).<br>Nada lo dispararía: `BP_ScorePlayer_SC` y la tabla de cues no existen (PLAN:262-272, F4 en PLAN:317).<br>Falta el "dónde suena": un sonido de objeto necesita `ATT_Objeto_SC` + `PlaySoundAtLocation` (docs/MAPA-DE-AJUSTES.md:96-98; REF/audio-quest.md:192-193). | Destino `Obra/Audio/FX/` (o `Placeholder/` con chip "temp").<br>Campo **Plays at: 2D \| rol (tag)** en lugar de "Bus" (MOCK:446).<br>`accept=".wav"` (MOCK:197). Validar PCM a 48 kHz (VR_Test/Config/DefaultEngine.ini:92) y mono si es de objeto (REF/assets-existentes.md:159).<br>Que el push fije `bLooping=false` (gotchas.md:726) y `ForceInline` (gotchas.md:995).<br>Insignia "preview only" hasta F4. |
| **Appear · light first** | Corregir | Es `BPC_AppearLuz_SC.Appear()/Vanish()`: `Duration` 1,5, `NoTrace`, `FaceAxis`, `PivotDepth`, `MoverHide`, `AppearSound/VanishSound` (TRK/BPC_AppearLuz_SC.md:12-15,29-35).<br>Solo anima mallas con los tags `Appear*` (:16-26). Lo usan timbre, SAVE, sensor (UserTool), cuadro (2,0 s), paleta, HUD y botones (:63-68; TRK/BP_UserTool_SC.md:14,19).<br>Alma no lo usa: aparece con `AppearAt` en 1,2 s (TRK/BP_Alma_SC.md:75,87). El metaball usa `BlobAppear` de 4 s (TRK/BP_BreathStage_SC.md:57).<br>Las perillas son datos; cuándo se llama está cableado. MOCK:283 dibuja "Light first · Alma". | Acción **Appear** con el verbo y la duración propios de cada rol, sacados de la cosecha.<br>Ocultar "light first" en los roles que no tienen el componente. Borrar AP1 (MOCK:283). |
| **Disappear** | Corregir | La duración cambia según el rol:<br>• `Vanish` 1,5 s (BPC:12)<br>• Alma `Disappear()` 0,6 s (Alma.md:75,89)<br>• `BlobDisappear` 2,5 s (BreathStage.md:60)<br>• fantasma `Stop()` 0,6 s (TRK/BP_GhostPlayer_SC.md:88,108)<br>• `UserTool.Release()` (UserTool.md:16)<br>Nada se destruye: se oculta. | Duración por rol, no 1,5 fijo (MOCK:330). Ver hallazgo 4. |
| **Move to mark** | Falta en Unreal (salvo Alma) | Solo existe `Alma.MoveTo(PointTag)`: `TravelTime` 3 s, EaseInOut, mueve solo la posición (Alma.md:76,88,130). La escala la pone la Obra (TRK/BP_Obra_SC.md:232).<br>El resto de los objetos los coloca la Obra por código, con corrección de altura (BP_Obra_SC.md:186-193). El TargetPoint tiene que estar cargado (Alma.md:97). | Habilitarla para Alma (y el pez, `ShareSwim`, BP_Obra_SC.md:113). Para el resto, propuesta de TargetPoint y "preview only". |
| **Change parameter (Ramp)** | Falta en Unreal / Riesgo | No hay una rampa genérica. Cada BP escribe sus parámetros en su Tick: Alma (Alma.md:161) y el velo (BP_Obra_SC.md:70). Una rampa externa pelearía con ese dueño (Alma.md:150). | Solo sobre perillas con un único dueño declarado. Si no, que sea propuesta de perilla, no rampa en vivo. |
| **Title** | Corregir | Hay 4 sistemas:<br>• título de etapa: componente `Title` de la Obra, con Reveal 0,5→1,8, Out 4,6→5,6 y visible hasta 5,7 (DUMP:466-468);<br>• título del inicio: `BP_IntroTitle_SC`, 3→6,5 / 10→12,5 (TRK/BP_IntroTitle_SC.md:18-21);<br>• `BP_HallTitle_SC` y los nombres sobre las baldosas (TRK/BP_HallDirector_SC.md:37,76);<br>• el título del runner, con otros tiempos (TRK/BP_StageRunner_SC.md:15).<br>El texto es una **textura** (`Content/SoulCharger/Tour/T_Title_*`, `Obra/Titles/`). Todo cableado. MOCK:271 usa 0→3,5 / 6→9. | El texto no se puede editar: cambiarlo es hacer una textura nueva.<br>Mostrar los tiempos de Unreal. El aviso "min 3 s" marcaría el título de la Obra (lectura plena 2,8 s).<br>Depende de la decisión abierta #5 (PLAN:346). |
| **Veil** | Corregir / Riesgo | Esfera `Veil` + `M_TourVeil_SC` (BP_Obra_SC.md:15,71). Abre de 1 a 4 s y cierra de 69 a 71,5 s (DUMP:444,462), con más casos en `FlowVeil` (DUMP:1281-1333).<br>Los colores son datos (`CTops/CHors`, BP_Obra_SC.md:90); los tiempos son literales.<br>Lo escriben dos grafos en cada cuadro y gana el último (BP_Obra_SC.md:70). MOCK:281 lo abre de −4 a 1,5. | Usar los tiempos de Unreal. Al migrar, una bandera `bLegacy` tiene que cortar a los dos escritores (PLAN:276). |
| **Walk** | Falta en Unreal (fuera del Hall) | Solo existe `HallWalk` del Hall: trapecio con `AccelTime`/`BrakeTime`, tramos `JourneyTime`/`EnterTime`/`OutTime`/`ReturnTime`/`ExitTime`, paradas `Stop*` y pasos en 2D según el paso (HallDirector.md:30-31,54,82-83,180,184).<br>A las etapas se llega por teletransporte (`EnterStage`, DUMP:116-124), y la caminata se corta al cruzar la puerta (BP_Obra_SC.md:286-287).<br>"Arrives at stop sc0" (MOCK:284) no existe. | Walk solo en el Hall, con duración y pasos sí/no como perillas. En las etapas: "Arrive (teleport under veil)". |
| **Wait** | Corregir | En el Hall: `bGate` + `FW_Bell` 25, `FW_Tool` 20, `FW_Choose` 25 y `BellHold` 3 (instancia ≠ CDO, HallDirector.md:33-34,56,111).<br>En las etapas: cortafuegos **literal** 180/120/240 (DUMP:501). SHARE: `ShareFW` 30.<br>El R4 de Entering **no es una espera**: `bZone` solo apaga el fantasma y condiciona VO_11h; la exploración va por reloj (BreathStage.md:58,86,103; BP_Obra_SC.md:325).<br>Los valores 6/12/25 de MOCK:259,460-464 no existen en Unreal. | Cosechar los `FW_*` de la instancia.<br>Que la condición sea un menú cerrado de banderas reales (`bZone`, `bHeartZone`, `Phase`, `InkUsed`, `b*Live`).<br>G_BREATH, "preview only". |
| **Reaction** | Falta en Unreal | Lo más parecido son `StageCues/CueAttract/CueDraw`, con condiciones y tiempos literales (DUMP:1978-2050; BP_Obra_SC.md:224), y `GhostFirst` (:321-328).<br>Las etapas no emiten eventos con nombre (`MECH.*`, PLAN:249). | Pasar a F5. Requiere eventos `OnMark` por etapa. |
| **Branch** | Cableado | `FlowShare`, estados 0-8. Al cortafuegos `ShareFW` 30 elige DON'T SHARE, pero con `bSimulated` elige SHARE (BP_Obra_SC.md:103-115). La elección de alma del Hall cae en la del centro (HallDirector.md:124-131). | Mostrar que la opción por defecto depende de `bSimulated`. Pasar a F5. |
| **Demo ghost** | OK con cambios | `BP_GhostPlayer_SC` colocado en cada celda (`Ghost_<ID>`, `Take` = `DA_Ghost_*`), con `Play(Mirror)/Stop()`, `PlayRate` 1,25, `LoopGap` 0,4 y `LoopEnd`. Va **mudo y sin texto** (GhostPlayer.md:17-27,33,37-47,86-97).<br>Lo enciende `GhostTick` con un mapa cableado (BP_Obra_SC.md:310-331).<br>Las tomas de Loving, Save y Share están vacías (GhostPlayer.md:13). | No ofrecerlo para LOVING/SAVE/SHARE.<br>El inicio es la bandera o la fase 6 (`S<K>.P6`), no un ancla libre. |
| **Alma VO** | Corregir | `Alma.SayClip` (Alma.md:158), llamado desde tres lugares:<br>• la Obra, con `ObraSay` / `ObraSayLater(Clip, 1.5)` (DUMP:965-977,1866-1871,1964-1969);<br>• el Hall, con `HallSay(I)` **por índice** (HallDirector.md:46,57; `VR_Test/Saved/ClaudeScripts/Hall/dsl/HallEnterIntro.dsl:33-74`);<br>• Breath, con `StageSay` (BreathStage.md:102).<br>Suena **en 2D** (Alma.md:142), no "Alma (3D)" como dice MOCK:470.<br>El volumen es único para todas las voces (`VOVolume`). | "From: Alma (2D, reacciona)".<br>El volumen por clip queda como previs o se hornea en el WAV.<br>El Lead-in de 1,5 s es literal en Unreal. |
| **Omnipresent VO** | Corregir | `ObraVO2D` = `PlaySound2D`, sin manija (DUMP:1873-1876). No se puede fundir: `FadeVoice` solo opera sobre la voz de Alma (Alma.md:171). | Marcarla "no interrumpible" y desactivar el "If early". |
| **Help for a wait** | Corregir | Cada etapa tiene su regla, cableada:<br>• VO_11h: `HelpAfter` 4 s después de VO_11b, si `!bZone` (BreathStage.md:103-105);<br>• VO_16h: a los 15 s (TRK/BP_HeartManager_SC.md:175-176);<br>• VO_27h: 20 s sin esferas; VO_32h: 15 s sin tinta (BP_Obra_SC.md:224);<br>• VO_01h y VO_03h del Hall: sin cablear (HallDirector.md:7).<br>MOCK:269 usa "inicio de G_BREATH + 12". | "Help after" con una referencia explícita (fin de VO X / inicio de la espera) y una condición. |
| **Empty voice clip…** (MOCK:511) | Riesgo | Las VO salen de la mezcla de Beltrán, fuera del repo (importar_mezcla.py:7), y se copian a todas las carpetas donde ya existe ese nombre (:14-17). | Solo como "temp", para reemplazar con la mezcla. |
| **Template · Demonstrated interaction** | Corregir | El guion V5 pide fantasma + línea de texto + botón que brilla + `HAP_TICK` + `FX_GHOST*` + ayuda a los 2 bucles + cortafuegos de 25 s (GUION-V5:442,469-474).<br>Unreal hoy: fantasma mudo y sin texto (GhostPlayer.md:16,47), timbre sin VO (BP_Obra_SC.md:214) y sin ayuda, sin la lógica de los 2 bucles. | Redefinir los ítems con lo aprobado (ver hallazgo 5). |
| **Template · Layered reveal** | Cableado | Las capas son las fases: 0 (entorno y título) → 4 (Alma) → 5 (`StageIntro`) → 6 (`StageBegin`) (DUMP:470-506). Dentro de Breath, `ToolDelay` de 0,8 s (BreathStage.md:57,86). | Que la plantilla sea una vista de las fases reales.<br>Escalonar el ejemplo: sensor y pacer aparecen juntos a los 24 s (MOCK:277,279). |
| **Template · Stage mold R1-R9** | Falta en Unreal (como creación) | El molde es el `switch` de `RunObra` + el contrato de etapa, con un switch por clase (BP_Obra_SC.md:18-38). Las celdas son fijas, 0-5 (:12). | Solo como vista o previs. Nunca "crear etapa" con alcance a Unreal. |
| **Marker** | OK (solo web), con riesgo de nombre | "Marca" ya es el nombre de las anclas que emite Unreal (PLAN:249). | Renombrarlo "Bookmark". |
| **Note** | OK (solo web) | `notes/*` (PLAN:229). | — |

## Hallazgos importantes

1. **No hay un mapa id → asset, y casi ningún `FX_` de la web existe en Unreal.**
   - `web/prototipo-narrativo/guion.js` usa 87 ids `FX_`. En Unreal hay 10 assets `FX_*`, todos en `Obra/Audio/Placeholder/`, y solo 8 coinciden de nombre: DISCLAIMER, RINGVANISH, SHAREAPPEAR, SHARESELECT, SOULDETACH, SOULJOIN, SOULSWIM y SOULVANISH.
   - Unreal suena con nombres sin prefijo. Están en `Core/Audio/Sounds/` (Bell, DoorOpen, ProtoSelect, SBubbleHoverOn/Out, Charge1, ChargeFinal, Pasos, BreathCount, HeartBeat), en `VR_Test/Saved/ClaudeScripts/obra/spawn/sounds_used.json` y como `SND_Pacer*` (TRK/BP_Pacer_SC.md:85,122).
   - La maqueta marca como "real" `FX_BELLRING`, `FX_TOOLAPPEAR_BREATH` y `FX_BREATHCOUNT` (MOCK:329,500). Pero el sensor real suena con `ProtoSelect` (UserTool.md:14).
   - El resto de los prefijos:
     - `HAP_`: 8 ids en la web, 0 en Unreal.
     - `VFX_`: 24 menciones en la web, 0 en Unreal.
     - `G_`: no existe como entidad.
     - `AMB_0N` equivale a `AmbClips[N−1]` = `Ambient_Clip_N_-_*` solo por posición (BP_Obra_SC.md:200), y ya divergen: en Attracting la web usa `PAD_M1` y Unreal el clip 8 (guion.js:287; BP_Obra_SC.md:375).
     - `GHOST_` sí coincide (`.claude/skills/unreal-vr/scripts/ghost/ghost_spec.json:130-234`). Pero la v2 reproduce el `Take` de la instancia, no busca por id (GhostPlayer.md:87,99-100).
   - **Corrección:** una tabla versionada `obra/score/assets.json` con {id → rutas, tipo, estado real/temp/missing}, alimentada por la cosecha. Con alias para los nombres heredados (por ejemplo, `FX_BELLRING` → `/Game/SoulCharger/Core/Audio/Sounds/Bell`). El chip "in Unreal" solo cuando la ruta existe.

2. **"Empty sound → Unreal" promete un camino que hoy no existe de punta a punta.** El camino real sería:
   1. El WAV sube a los assets del artifact. Hace falta rol Editor (anexos/09-critica.md:161-164).
   2. Una sesión, en su turno, lo baja a disco y valida nombre, 48 kHz y mono.
   3. Lo copia a `VR_Test/Content/SoulCharger/Obra/Audio/FX/FX_X.wav` con el editor abierto. El editor lo importa solo en unos 3 s (gotchas.md:2693). El MCP no puede escribir `.wav`: `write_file` solo acepta texto (REF/toolsets.md:243).
   4. Por MCP le fija `bLooping=false`, `loadingBehavior=ForceInline` y, si es de objeto, `attenuationSettings=ATT_Objeto_SC`. Asignar la atenuación por MCP está por verificar.
   5. Una fila de cues con una columna `SoundBase` (referencia firme). Así se cocina, porque la Obra no está en `MapsToCook` y el mapa por defecto es Test_Sequencer (VR_Test/Config/DefaultGame.ini:112-137; DefaultEngine.ini:7).
   6. `BP_ScorePlayer_SC` la toca en Mark + Offset, con `PlaySoundAtLocation` sobre el actor del rol (por tag) o en 2D. El largo del archivo no se usa (regla de tiempos).
   - Hoy faltan los pasos 5 y 6. La única vía es la cirugía de grafos (el patrón de `sfx_swap.py`, BP_Obra_SC.md:203).
   - "Replace WAV" de un sonido existente solo reimporta si el `.wav` fuente vive al lado del asset. En `Core/Audio/Sounds/` solo pasa con Charge1 y ChargeFinal.

3. **Los datos de ejemplo de Entering en la maqueta salen de `guion.js`, no de Unreal**, y en eso Beltrán decide la interfaz.

   | Qué | Maqueta | Unreal |
   |---|---|---|
   | G_BREATH | espera con cortafuegos de 25 s (MOCK:259) | no existe |
   | VO_11b | después de "Done" (MOCK:266,464) | suena en el `StageBegin` |
   | VO_11h | inicio de G_BREATH + 12 (MOCK:269) | 4 s después de VO_11b, si `!bZone` |
   | Título | 0→3,5 (MOCK:271) | 0,5→1,8 (DUMP:466) |
   | Velo | −4→1,5 (MOCK:281) | 1→4 (DUMP:462) |
   | Alma | aparece a 8,5 (MOCK:274) | a T ≥ 5,8, y la VO entra 1,5 s después (DUMP:473,968) |
   | Ambiente | `AMB_05` en Entering (MOCK:288) | 4 (BP_Obra_SC.md:372); la web también usa `AMB_04` (guion.js:269) |
   | Largos de VO | 7,4 / 4,9 / 6,3 / 4,6 / 3,1 | mezcla final 8,50 / 5,84 / 7,45 / 5,24 / 3,40 (`vo_final/duraciones_mezcla.txt:16-20`) |

   **Corrección:** regenerar el ejemplo desde la cosecha, o rotularlo "previs (guion.js)".

4. **"Spawn/Destroy" (PLAN:271) choca con lo construido.**
   - Alma no se spawnea por decisión de diseño (Alma.md:93).
   - El timbre, el sensor y los objetos del final están colocados y ocultos (HallDirector.md:160; BP_Obra_SC.md:178-184). Los fantasmas también están colocados (GhostPlayer.md:17).
   - Las 6 celdas se cargan todas al arrancar y se apagan (BP_Obra_SC.md:12-13). Es justo el patrón que la regla "cargar por etapa" de Beltrán pide abandonar.
   - **Corrección:** la unidad de carga es la celda, y eso es dominio de Unreal y queda pendiente de diseño. La acción del editor es Appear/Disappear con el verbo propio de cada rol. Quien spawnea algo lo destruye.

5. **Unreal no cumple hoy dos reglas que el editor va a hacer cumplir.**
   - El timbre se demuestra sin voz y sin ayuda: VO_01d se quitó (BP_Obra_SC.md:214) y VO_01h no está cableado (HallDirector.md:7).
   - El R4 de Entering no tiene cortafuegos.
   - Cortar la voz cuando el usuario se adelanta solo existe en el Hall (HallDirector.md:139). Breath y Heart no lo hacen.
   - **Corrección:** decidir si el editor refleja Unreal o propone cambios. Las plantillas tienen que reflejar lo aprobado después del guion V5: fantasma mudo y sin texto (GhostPlayer.md:16,47), voz de instrucción de Alma, `_h` y cortafuegos.

6. **VO.**
   - La voz de Alma es 2D, no 3D (MOCK:470 contra Alma.md:142).
   - Las VO omnipresentes no se pueden interrumpir (DUMP:1875).
   - El Hall referencia las VO por índice (`HallSay :I n`). Hace falta un mapa id → índice, leído de la instancia.
   - Hay VO duplicadas en dos carpetas: `VO_12c` está en `Mechanics/Breath/Audio` y en `Obra/Audio` (importar_mezcla.py:14-17).
   - **Bug de la maqueta:** `cleanId` pasa todo a mayúsculas (MOCK:304). "VO_11h" queda "VO_11H", lo que rompe `VO_nn[a-z|h]` (anexos/04-guion-taxonomia.md:148) y la llave en JS. Hay que preservar el sufijo en minúscula y rechazar `HAP_` como nombre de WAV.

7. **Háptica.**
   - `HAP_*` no existe en Unreal. Cada háptico lo maneja su mecánica:
     - `BreathHaptic` (TRK/BP_BreathManager_SC.md:79);
     - el Hall;
     - `ChargeFx.MuteFeel`;
     - `HandsTick`, que lo pone en 0 en las fases 10-15 (BP_Obra_SC.md:228).
   - Si dos BPs mandan sobre el mismo mando, pelean (TRK/BP_PulseField_SC.md:230). MOCK:289 dibuja `HAP_PULSE_SOFT` y `HAP_BREATH_HUM` como clips.
   - **Corrección:** HAP como "preview only". Si se migra, un hub con un solo dueño por mano (precedente `BP_HapticHub`, TRK/_INDEX.md:300). El zumbido de la respiración es una perilla de la mecánica, no un cue.

8. **Buses y ducking no existen.** No hay SoundClass ni Submix en `Content/`, y MAPA-DE-AJUSTES.md:94-98 no los menciona. MOCK:446,472 muestran "Bus FX" y "ducks under voice".
   - **Corrección:** quitarlos o marcarlos "Falta en Unreal". El orden VO > FX > AMB (anexos/04:153) sería una tarea en Unreal, en configuración compartida.

9. **Los sonidos del pacer están horneados a 4-3-4-3** (Pacer.md:86; MAPA-DE-AJUSTES.md:176,193). La perilla Rhythm (MOCK:246) cambiaría los tiempos sin cambiar los sonidos.
   - **Corrección:** candado y aviso "regenerar sonidos".

10. **Que un rol se resuelva por tag (PLAN:240) depende de tags que casi no hay.** Existen en el Hall y en el final (`hall_bell`, `hall_sensor`, `soul_pick`, `hall_intro_title`, `share_yes/no`, `ObraChargeTarget`). En Entering no consta ninguno. Además, con las 6 celdas cargadas a la vez, los tags tienen que ser únicos (BP_Obra_SC.md:346).

11. **El catálogo es más grande de lo acordado.** La maqueta trae 15 acciones y plantillas (MOCK:330); el plan dice 10 como máximo al principio (PLAN:329).
    - **MVP sugerido:** Appear, Disappear, Alma VO, Omnipresent VO, Sound, Ambience, Title, Veil, Wait (en lectura) y Demo ghost. El resto, previs.

12. **Detalles menores.**
    - `BellPressDepth`/`BellPressTime` son variables de `BP_HallDirector_SC` (HallDirector.md:107), no de `BP_BellArt_SC` (MOCK:242).
    - "Marker" choca con el nombre "Marca" (ver la tabla).

## Lo que hay que verificar en vivo en Unreal

Todo es de solo lectura, en el turno de la cola.

1. **Test_Hall · `HallDirector`** (`BP_HallDirector_SC_C_0`):
   - el array `VO`: las 21 rutas, en orden, para armar el mapa id → índice;
   - el grafo `HallEnterIntro`, caso 6: ¿sigue `HallSay :I 3` (VO_01d)?;
   - `FW_Bell`, `FW_Tool`, `FW_Choose`, `BellHold`, `BellPressDepth`, `BellPressTime` y `VOAir`, en la instancia y en el CDO.
2. **Test_Hall · `Timbre`** (`BP_BellArt_SC`): `Appear.AppearSound`, `Appear.VanishSound`, `Appear.Duration` y `Tags`. El CDO no tiene sonidos (`sounds_used.json`).
3. **L_SoulCharger_Obra · `BP_Obra_SC_C_0`:** `AmbClips[0..8]` (asset y orden), `AmbVolumes`, `AmbFadeIn/Out`, `bGhostsOn`, `ShareFW` y `bSimulated`.
4. **Volcado nuevo de `BP_Obra_SC`**, grafos:
   - `AlmaSpeak`: el delay de `ObraSayLater` y si `AlmaTime` es `VODur` + 3,5 (DUMP) o + 3 (BP_Obra_SC.md:296);
   - `StageTimes`;
   - `GhostTick`: el mapa Take → bandera, y si usa `LoopCount` para la ayuda;
   - `CueAttract`, `CueDraw` y `StageCues`;
   - la lista de llamadas a `ObraVO2D`.
5. **Cada celda · `Ghost_<ID>`:** `Take`, `PlayRate`, `LoopGap`, `LoopEnd`, `bShowText`, `AppearSound`, `VanishSound` y `FollowTag`.
6. **Test_Entering · `Entering_Stage`** (`BP_BreathStage_SC`): `ExploreTime`, `ToolDelay`, `HelpAfter`, `SayAfterTool`, `SayGap`, `ClipInstr/Explore/Help/Ready` y `CountSound`. En `BP_BreathRig_SC`, si `bZone` tiene un tiempo de permanencia.
7. **Test_Entering · `Entering_Pacer`, el metaball y el `BP_UserTool_SC`:** `Tags` (para el mapa rol → tag) y `Appear.AppearSound` del UserTool (se espera ProtoSelect).
8. **Test_Heart · `HeartManager`:** qué variable fija VO_16h a los 15 s y cuál fija el latido de respaldo.
9. **Los 10 assets `/Game/SoulCharger/Obra/Audio/Placeholder/FX_*`:** `bLooping`, `loadingBehavior`, `attenuationSettings`, `numChannels` y `duration`. Y en `/Game/SoulCharger/Core/Audio/Sounds/Bell`, `AssetImportData` (la ruta fuente), para saber si "Replace WAV" reimporta.
10. **Prueba sobre una copia de un SoundWave:** `ObjectTools.set_properties` con `attenuationSettings` = `/Game/SoulCharger/Core/Audio/ATT_Objeto_SC` y `loadingBehavior` = ForceInline. Confirma si el MCP permite el paso 4 del flujo.
11. **`BP_Alma_SC`, instancia de la Obra:** `VOVolume` y `VODelayIn/Out`. En el grafo `SayClip`, si respeta `VODelayIn`.