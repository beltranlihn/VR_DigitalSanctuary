> Anexo de la auditoría de herramientas del 2026-10-01 (consolidación verificada de las 5 revisiones). Lo que manda es [PLAN-EDITOR-OBRA-2026-10-01.md](../PLAN-EDITOR-OBRA-2026-10-01.md).

## Resumen

Las herramientas del editor están bien pensadas, pero **hoy ninguna se comunica con Unreal**. El editor muestra datos de `guion.js` y no la obra que corre en Unreal.

1. **Datos de ejemplo:** el tramo de Entering de la maqueta tiene al menos 12 diferencias con Unreal (voces, título, velo, Alma, ambiente, metaball, cuenta). Aun así, la píldora dice "3 differences".
2. **Mecanismos que no existen en Unreal:**
   - La espera `G_BREATH` no existe: Entering corre por reloj y el usuario solo decide si suena `VO_11h`.
   - "On timeout = same as the real ending" es falso en las etapas: el cortafuegos llama `CallOutro` sin SAVE ni coda.
   - Fuera del Hall no existen Walk ni Move to mark (salvo Alma), ni la rampa, ni los buses, el ducking o los HAP.
3. **Perillas:** varias apuntan al BP equivocado. Las del timbre son del `HallDirector`, y la de exploración y la cuenta son de `Entering_Stage`. Otras son literales de grafo y no perillas ("Stays VO + 3"), o tienen valores viejos (`CountTime` 3 en vez de 3,6).
4. **Puente con Unreal:** el único camino que funciona hoy es proponer un valor de instancia (`set_properties` + guardar el subnivel). Lo demás está roto o no existe:
   - el parche espacial con `set_actor_transform` no mueve nada;
   - la cosecha actual cambia el nivel del editor compartido y puede leer mal sin avisar;
   - la vista 3D web usa otra base de posiciones que Unreal.
5. **Verificación:** re-verifiqué 26 afirmaciones de los 5 informes contra las fuentes. Se sostienen, salvo las contradicciones que resolví abajo. Dos quedan para verificar en vivo.

**Contradicciones resueltas**
- **Título de etapa:** Reveal 0,5→1,8 s · Out 4,6→5,6 s · visible si T < 5,7 · Alma a T ≥ 5,8 (DUMP:466-473; TRK/BP_Obra_SC.md:226). La versión "0,5→2,3 / 3,3→4,5" (TRK/BP_Obra_SC.md:206) es anterior. Además, en la fase 0 `FlowVeil` salta T de 5,5 a 9 (DUMP:1333-1334): Alma entra en la práctica a ~5,5 s.
- **Cortafuegos de Recognizing:** 180 s (DUMP:501). "150" en TRK/BP_Obra_SC.md:26, MAPA:401 y TRK/BP_HeartManager_SC.md:130 es viejo.
- **`Preset` del pacer:** la instancia tenía 0 (`VR_Test/Saved/ClaudeScripts/usertool/pacer_read.json:164`, 09-30 19:12). El "Preset 1" de TRK/BP_Pacer_SC.md:72 es del 09-27. El riesgo de que pise los tiempos queda descartado.
- **`IntroTime` del metaball:** 2,5 s (TRK/BP_BreathBlob_SC.md:83). El "morfeo 4 s" de TRK/BP_BreathStage_SC.md:57 es viejo.
- **Voz del Hall:** `HallSay` llama `Alma.SayClip`, o `PlaySound2D` si no hay Alma (HDUMP:259-267). La voz es **2D en toda la obra**. El "SpawnSoundAtLocation" de TRK/BP_HallDirector_SC.md:46 es viejo.
- **Alma de la Obra:** el CDO tiene Size 0,6 y Brightness 1; la instancia, 1 y 1,5 (`Obra/alma_diff.json:15-17,95-97`). El tracker dice 0,4 / 1,5 (TRK/BP_Alma_SC.md:69,71), y está mal.
- **Sin resolver (vivo):**
  - `AlmaTime`: DUMP:977 y 1459-1468 (volcado de las 13:07) dicen VODur + 3,5 con `StAlma`; TRK/BP_Obra_SC.md:296 ("tarde") dice + 3 sin `StAlma`.
  - `StopCard`: 300 (`Hall/director_overrides.json:2`) o 396,45 (TRK/BP_Obra_SC.md:178).
  - `StopInside`: −300 (TRK/BP_HallDirector_SC.md:30) o −450,5 (TRK/BP_Obra_SC.md:219).

Abreviaturas (raíz `C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/`):

| Abreviatura | Archivo |
|---|---|
| MOCK | `web/editor-obra/mockup/src-body.html` |
| PLAN | `docs/editor-obra/PLAN-EDITOR-OBRA-2026-10-01.md` |
| TRK/ | `.claude/skills/unreal-vr/blueprints/` |
| REF/ | `.claude/skills/unreal-vr/references/` |
| DUMP | `VR_Test/Saved/ClaudeScripts/obra/dump/obra_all_now.txt` (13:07) |
| HDUMP | `…/obra/dump/hall.txt` (07:52) |
| MAPA | `docs/MAPA-DE-AJUSTES.md` |
| MIX | `VR_Test/Saved/ClaudeScripts/vo_final/duraciones_mezcla.txt` |
| EXP | `VR_Test/Saved/ClaudeScripts/obra/ensayo_export.py` / `.json` |

## Tabla maestra

| Herramienta | Estado final | Evidencia | Corrección |
|---|---|---|---|
| Perillas · Timbre | Corregir | MOCK:241-242 dice "From BP_BellArt_SC", pero `BellPressDepth/Time`, `BellHold`, `FW_Bell` y `TouchRadius` son de `HallDirector` (TRK/BP_HallDirector_SC.md:56,107; HDUMP:425-426) | Un `owner` por perilla. Agregar `TouchRadius` 14 y la descarga −2/s (literal) |
| Perillas · Sensor | Corregir | `ToolDelay` es de `Entering_Stage` (TRK/BP_BreathStage_SC.md:86). Sensor del Hall (`BP_BioSensorArt_SC`) ≠ sensor en mano (`UserTool_Obra`) (TRK/BP_HallDirector_SC.md:160; TRK/BP_UserTool_SC.md:22,27) | Dos roles, y crear el rol "Stage · Entering" |
| Perillas · Pacer | Corregir | `CountTime` vale 3,6 en `Entering_Stage` (TRK/BP_BreathStage_SC.md:95). El ritmo son 4 variables más `Preset` (TRK/BP_Pacer_SC.md:43). Audio horneado a 4-3-4-3 (:86) | Ver la sección de la maqueta |
| Perillas · Alma | Corregir | `Size` = diámetro en m (TRK/BP_Alma_SC.md:69) × la escala del TP (TRK/BP_Obra_SC.md:232). "Stays" es un literal (DUMP:977) | Unidad "m" y tamaño efectivo. "Stays" en solo lectura |
| Perillas · Metaball | Corregir | La exploración es de la etapa. `IntroTime` 2,5 (TRK/BP_BreathBlob_SC.md:83). El tamaño es `SizeCM`, porque el CS pisa la escala (:23) | Moverlas a la etapa. BLOB_IN dura 2,5 s |
| Candado / origen del valor | Falta en la maqueta | `knobRows` no pasa `lock` (MOCK:432). "Expected" sí lleva candado (MOCK:461), y no es una variable de Unreal | Candado en las perillas de instancia de los tests. Origen: instancia / CDO / literal |
| Empty sound + WAV | Corregir · Falta en Unreal | `Content/SoulCharger/Audio` no existe (comprobado). Los FX están en `Obra/Audio/Placeholder/`. Auto-import por máquina, con `bAutoDeleteAssets=True` (`VR_Test/Saved/Config/WindowsEditor/EditorPerProjectUserSettings.ini:78,80`). No hay quien dispare el sonido | Destino `Obra/Audio/FX/`, validar 48 kHz y mono, insignia "preview only" |
| Appear · light first | Corregir | `BPC_AppearLuz_SC.Duration` 1,5 (TRK/BPC_AppearLuz_SC.md:29). Alma no lo usa: aparece por escala en 1,2 s (TRK/BP_Alma_SC.md:75,87) | Verbo y duración por rol. Borrar AP1 (MOCK:283) |
| Disappear | Corregir | Vanish 1,5 · Alma 0,6 (TRK/BP_Alma_SC.md:75,89) · metaball 2,5 · fantasma 0,6 | Duración por rol |
| Move to mark | Falta en Unreal | Solo existe `Alma.MoveTo(Tag)` (TRK/BP_Alma_SC.md:88) | Solo para Alma |
| Change parameter (Ramp) | Falta en Unreal · Riesgo | Cada BP escribe su material en su Tick (TRK/BP_Obra_SC.md:70) | Propuesta de perilla, no rampa |
| Title | Corregir | El texto es una textura. Tiempos en DUMP:466-468. MOCK:271 usa 0→3,5 / 6→9 | Tiempos reales. El texto no se edita. Decisión abierta #5 (PLAN:346) |
| Veil | Corregir | Abre 1→4 s, cierra 69→71,5 s (DUMP:462,474) y salta en `FlowVeil` (DUMP:1333). MOCK:281 usa −4→1,5 | Tiempos reales, en solo lectura |
| Walk | Falta en Unreal (fuera del Hall) | A las etapas se llega por teletransporte bajo el velo. "Arrives at stop sc0" (MOCK:284) no existe | "Teleport · PlayerStart Test_Entering" |
| Wait `G_BREATH` | Corregir | "El pacer arranca respire o no" (TRK/BP_BreathStage_SC.md:58). La cadena de VO (:103) | Pasarlo a "condición sin bloqueo" (ver hallazgo 1). Las esperas reales son las 3 del Hall y SHARE |
| Help after | Corregir | VO_11h: `HelpAfter` 4 s después de VO_11b, si `!bZone` (TRK/BP_BreathStage_SC.md:103,105). VO_16h a 15 s. VO_27h a 20 s, VO_32h a 15 s (TRK/BP_Obra_SC.md:224). Hall: sin ayuda por voz (TRK/BP_HallDirector_SC.md:7) | Ancla y condición propias |
| Timeout / On timeout | Corregir · Falta en Unreal | Etapas: 180/120/240 → `CallOutro` (DUMP:501-505), sin SAVE ni coda (TRK/BP_Sequencer_SC.md:517). Hall: el timbre se llena solo, 25 + 3 s (HDUMP:425) | El valor por espera sale de la cosecha |
| If early (0,3 s) | Riesgo | Solo en el Hall (HDUMP:434-438; TRK/BP_HallDirector_SC.md:139) | Apagado por defecto en las etapas |
| Outputs Done/Late/Timeout | Corregir | Late no existe (anexos/09-critica.md:61) | Done / Help / Timeout |
| Usuario simulado + total | Corregir | Un solo número para toda espera (MOCK:253,315). Falta el modo `bSimulated` (DUMP:1553,1727) | Percentil por espera. Perfil "APK autoplay" |
| Reaction / Branch | Falta en Unreal · cableado | `StageCues`/`CueAttract`/`CueDraw` y `FlowShare` (TRK/BP_Obra_SC.md:110,224) | A F5. El default de SHARE depende de `bSimulated` |
| Demo ghost | OK con cambios | Mudo y sin texto (TRK/BP_GhostPlayer_SC.md:16,47). Loving, Save y Share vacíos (:13). Arranca en la fase 6 (TRK/BP_Obra_SC.md:321-328) | Vuelta de ~4,3 s. No ofrecerlo en Loving, Save ni Share |
| Alma VO | Corregir | 2D (TRK/BP_Alma_SC.md:142; HDUMP:259-267). El lead-in de 1,5 s solo existe en `AlmaSpeak` (DUMP:966-976) | "From: Alma (2D)". Lead-in por punto de llamada |
| Omnipresent VO | Corregir | `PlaySound2D` sin manija (DUMP:1873-1876) | "No interrumpible" |
| Plantillas | Corregir | El guion pide ayuda por voz; Unreal tiene el fantasma mudo y sin VO_01h | Reflejar lo aprobado |
| Marker / Note | OK | Choca con "Marca" (PLAN:249) | Renombrar "Bookmark" |
| Place (gizmo, Front/Side/Height/Scale) | Corregir | Mismo bloque y números para todo (MOCK:471). La realidad: `alma_side` 140/−300/+20 (EXP.json:20-25). Hay 5 tipos de anclaje | Un esquema por ancla (hallazgo 4) |
| Vista 3D (`world.js`) | Riesgo alto | La web suma desplazamientos a sus propias bases (`web/prototipo-narrativo/guion.js:20-24`; `ensayo.js:288-292`) | Bases desde la cosecha antes de F1 |
| POV / cono | Corregir | Elipses decorativas (MOCK:555), cono fijo de ±30° (MOCK:540). Alma al costado queda a 65° y 3,3 m | Proyectar desde la cámara |
| Cosecha | Corregir · Verificar en vivo | `load_level` (EXP.py:37,61), `ps[0]` (:38-39), serie de Taylor (:47-49) | `harvest_score.py` (hallazgo 5) |
| Parche espacial | Corregir | `set_actor_transform` "devuelve true y no mueve nada" (REF/toolsets.md:121) | `set_properties` en formato texto + releer (REF/toolsets.md:127-141) |
| Propuesta de perilla | OK | `set_properties`/`get_properties` | Lleva `{nivel, actor, prop, ámbito, base, valor}` |
| Tabla compilada | Falta en Unreal | `DataTableTools.set_rows` nunca se usó en el proyecto (grep). El MCP no crea structs (REF/gotchas.md:670) | DataAsset como camino preferido (precedente `DA_Ghost_*`) |
| `BP_ScorePlayer_SC` + `OnMark` | Falta en Unreal · Riesgo | La fase se fija en ~19 lugares. El timer es de 0,011 s y `Dt` se recorta a 0,1 (DUMP:265,296) | U1: marcas tomadas de los `PrintString` que ya existen |
| `ScoreApply` (tres vías en runtime) | Corregir | PLAN:274 | La instancia se propone en el editor. En runtime solo van los literales promovidos |
| `bLegacy<Familia>` | Corregir | Un bool nuevo nace en false (REF/gotchas.md:1254) | `bScore<Familia>`, con false = camino viejo |
| Píldora, revisiones, alcance | Corregir | Texto fijo "3 differences" (MOCK:320); "Unreal rev 41" (MOCK:369); "592" (MOCK:339) | Calculadas. "0 of 592 reach Unreal" |
| IDs FX/HAP/AMB | Corregir | 10 `FX_*` en Unreal contra 109 menciones en la web. `FX_BELLRING`/`FX_BREATHCOUNT` no existen (Unreal tiene `Core/Audio/Sounds/Bell`, `BreathCount`) | Mapa `idmap.json` versionado |
| Háptica / buses / ducking | Falta en Unreal | Sin SoundClass ni Submix. OpenXR no reproduce formas de onda (REF/audio-quest.md:158) | "Preview only" |
| Traza `SCORE` en logcat | Falta en Unreal | Los PrintString siguen yendo al log aunque no se muestren (`VR_Test/Config/DefaultEngine.ini:217-220`) | Ver la sección de Unreal |
| Override JSON (F6) | Verificar | JsonBlueprintUtilities trae `EnabledByDefault` false (`UE_5.8/.../JsonBlueprintUtilities.uplugin:17`) | Activarlo o descartarlo |

## Correcciones a la MAQUETA (src-body.html)

1. **Timbre (MOCK:241-242):**
   - **Dueño:** `bp` = "BP_HallDirector_SC · HallDirector (Test_Hall)" para Press depth, Press time, Hold, Timeout y el radio nuevo. "Appear" queda en `Timbre.Appear.Duration`.
   - **Perillas nuevas:** `TouchRadius` 14 cm (TRK/BP_HallDirector_SC.md:56) y "Release drain −2/s · literal" (HDUMP:425).
   - **Timeout:** "25 s + 3 s auto-fill".
   - **Used:** solo "1.8 · The bell". Sacar "2.6 · Hall exit" (GUION-V5:329 es "Tu alma").
   - **Sounds:** `Bell` (al tocar, FadeOut 0,5; TRK/BP_HallDirector_SC.md:185). `FX_BELLAPPEAR/VANISH` como "not assigned".
2. **Bio sensor (MOCK:243-244):**
   - Partirlo en dos roles: "Sensor (Hall)", con `SpinDeg`/`OrbSize` y `FW_Tool` 20, y "Sensor (hand) · UserTool_Obra", con `MorphTime` 0,8, `ColorTime` 1,2 y `SensorXfR`.
   - Sacar `ToolDelay`.
   - Sonido real: `ProtoSelect` (TRK/BP_UserTool_SC.md:14), no `FX_TOOLAPPEAR_BREATH`.
3. **Pacer (MOCK:245-246):**
   - "Rhythm": cuatro perillas `InhaleTime` 4 / `Hold1Time` 3 / `ExhaleTime` 4 / `Hold2Time` 3, más `Preset` 0, con candado y el aviso "regenerate pads/plucks" (TRK/BP_Pacer_SC.md:86).
   - Agregar `LeadOut` 3 (`pacer_read.json:164`).
   - Count: pasa al rol de la etapa, con valor 3,6.
   - Sonidos: `SND_PacerPad*` y `SND_PacerPluck*` (TRK/BP_Pacer_SC.md:122-124), no `FX_BREATHCOUNT`.
4. **Alma (MOCK:247-248):**
   - Size "1.00 m (diameter) × point scale".
   - "Stays" en solo lectura: "literal in BP_Obra_SC: VO at +1.5 s; stays VODur+3.5 (verify)".
   - Sonido: no hay `FX_ALMAAPPEAR` en Unreal.
5. **Metaball (MOCK:249-250):** `SizeCM` 220, `IntroTime` 2,5, `OutroTime` 2,5, `Brightness`. Explore pasa a la etapa.
6. **Rol nuevo "Stage · Entering" (`Entering_Stage`):**

   | Perilla | Valor |
   |---|---|
   | `ExploreTime` (mínimo, elástica) | 12 |
   | `CountTime` | 3,6 |
   | `InhaleCueAt` | 3,48 |
   | `ToolDelay` | 0,8 |
   | `SayAfterTool` | 1 |
   | `SayGap` | 0,5 |
   | `HelpAfter` | 4 |
   | `SensorColor` | (0,35; 0,7; 1) |

   Fuente: TRK/BP_BreathStage_SC.md:86,95,97,105.
7. **Datos del tramo (MOCK:257-289), resembrarlos desde Unreal:**
   - Sacar `G_BREATH` como espera rayada. Pasa a una pista de condición `breath.zone` sin cortafuegos, y todo se ancla a `S0.BEGIN`.
   - **Duraciones de VO** (MIX:16-21):

     | VO | Valor |
     |---|---|
     | VO_10 | 8,50 |
     | VO_11 | 5,84 |
     | VO_11h | 3,40 |
     | VO_11b | 7,45 |
     | VO_12 | 5,24 |
     | VO_12c | 3,56 |

     El texto de VO_12c es "Three… two… one… inhale." (TRK/BP_BreathStage_SC.md:94).
   - **Cadena real:**
     - `StageIntro` → metaball (2,5 s) y sensor a +0,8 s;
     - VO_11 a +1,8 s;
     - `StageBegin` → VO_11b;
     - VO_11h a `HelpAfter` 4 s, si `!bZone`;
     - VO_12, y la cuenta espera a que la voz termine + 0,3 s;
     - pacer en `VO_12c.start` + 3,48 − `LeadIn`.
     - Medido en PIE: de `StageBegin` al pacer, 17,3 s (TRK/BP_BreathStage_SC.md:107).
   - **Título:** in 0,5→1,8, out 4,6→5,6 s. **Velo:** 1→4 s.
   - **Alma:** aparece a ~5,5-5,8 s, AL_IN dura 1,2 s y VO_10 entra 1,5 s después.
   - **Ambiente:** AMB_04 en todo el tramo, no AMB_05 (TRK/BP_Obra_SC.md:372).
   - **Borrar:** AP1, PACER_DIM (el pacer nace invisible, TRK/BP_Pacer_SC.md:35) y BIO_ON. BIO_ON solo vuelve si se verifica `Active` en vivo.
   - **Háptica (HAP1/HAP2/HUM):** insignia "preview only". El zumbido real es `HapticAmp` 0,25 mientras `bBreathing` (TRK/BP_BreathManager_SC.md:52,79).
8. **Inspector de espera (MOCK:460-464):**
   - Frase: `[breath.zone]` (instantánea) / `[breath.on]` (1,5 s). No "for 1 s".
   - "Expected" sin candado y rotulado "simulation".
   - Outputs: Done / Help / Timeout.
   - "On timeout": el valor real por espera.
   - "If early": por espera, con la etapa en off.
9. **Voz (MOCK:470):** "From: Alma (2D)". Volumen "global VOVolume". Lead-in por punto de llamada.
10. **Sonido (MOCK:446,472):** reemplazar "Bus" por "Plays at: 2D | role (tag)". Sacar "ducks under voice".
11. **Empty sound (MOCK:197,304,448):**
    - `accept=".wav"`.
    - `cleanId` no debe pasar el sufijo a mayúsculas: `VO_11h` sale `VO_11H` (MOCK:304).
    - Rechazar `HAP_` como nombre de WAV.
    - Destino `Content/SoulCharger/Obra/Audio/FX/`.
12. **Place (MOCK:471,543,560):**
    - Stop = "PlayerStart · Test_Entering".
    - Valores reales (EXP.json:13-40):

      | Ancla | Front / Side / Up | Escala |
      |---|---|---|
      | `alma_in` | 2,20 / 0 / +0,05 | — |
      | `alma_side` | 1,40 / −3,00 / +0,20 | 0,6 hoy |
      | `charge` | 2,53 / 0 / +0,37 | 2,115 |
      | `title` | 3,00 / 0 / 0 | — |

    - Agregar Yaw.
    - Rótulos "Side: + right" y "Height: above author eye (floor + 1.20 m)". Una sola convención (el gizmo dice "left" y el inspector "−").
13. **Biblioteca (MOCK:328-330):**
    - Roles por actor, BP o tag, no por mallas inexistentes (`SM_HUD_SC`, `SM_QuestCtrl_SC`, `SM_DrawPalette_SC`, `SM_Results_SC` no existen).
    - VO_35a **sí** se usa (DUMP:1696, `ShareExit`).
    - Duraciones de VO desde MIX.
    - "Disappear 1.5 s" cambia a "per role".
14. **Barra (MOCK:320,322,369):** píldora calculada, tres revisiones ("score · editor asset · APK") y "0 of 592 reach Unreal".
15. **Fantasma (MOCK:382):** vueltas de 4,87/1,25 + 0,4 ≈ 4,3 s (TRK/BP_GhostPlayer_SC.md:33,43). Desde `S0.BEGIN` hasta `bZone`.

## Correcciones al PLAN

- **§1.2:**
  - "aviso: 20 s contra 9 s" (PLAN:57) pasa a `DiscTime` 19 en el CDO, acoplado al literal `Out` 17,6-18,7 de `BP_Disclaimer_SC.DiscStep` (TRK/BP_Obra_SC.md:383-384).
  - Agregar: Entering no tiene espera bloqueante; los cortafuegos de las etapas son 180/120/240 sin coda.
- **§1.3 / reglas (PLAN:75):** "toda espera tiene ayuda" hoy marca las 3 esperas del Hall, porque VO_01h y VO_03h no están cableadas (TRK/BP_HallDirector_SC.md:7). Decisión de Beltrán.
- **§2.3 (PLAN:128, 145):**
  - Destino `Obra/Audio/FX/`.
  - Validar PCM, 48 kHz (`DefaultEngine.ini:92`) y mono si el sonido es de objeto (REF/audio-quest.md:115).
  - Estado "in Content, not in APK" hasta que una cue lo referencie.
  - No borrar el `.wav` fuente, porque `bAutoDeleteAssets=True` borraría el asset.
  - "Appear here con marca nueva" queda "preview only": la Obra solo lee sus tags fijos.
- **§2.4 (PLAN:164-178):**
  - Frase de espera con `breath.zone` / `breath.on`.
  - Salidas Done / Help / Timeout.
  - Perillas con `owner` y ámbito.
  - Ejemplos corregidos: timbre del `HallDirector`; Count 3,6 en `Entering_Stage`; Rhythm en 4 variables; Alma Size en m × escala del TP.
- **§2.5 (PLAN:184):** sacar "Late".
- **§2.6 (PLAN:191-192):**
  - "El gizmo edita la marca" vale solo para los TP de etapa y `final_*`. En `Timbre`, `Sensor`, `HallSoul_*`, `TituloInicio` y `Final_*` mueve el actor (TRK/BP_HallDirector_SC.md:160,165; TRK/BP_Obra_SC.md:178-184).
  - Las paradas `Stop*` van con candado.
  - Usar "Point" para lo espacial y "Mark" para lo temporal.
- **§3.2 (PLAN:249):** reemplazar la lista de marcas por el vocabulario v0 de abajo. Sacar `GATE.late` y `VO.end`.
- **§3.3:**
  - DataAsset como camino preferido, escrito solo por MCP (un solo escritor).
  - "Spawn/Destroy" (PLAN:271) pasa a Appear/Disappear con el verbo de cada rol: Alma no se spawnea por diseño (TRK/BP_Alma_SC.md:93) y los objetos están colocados.
  - `ScoreApply` solo para literales promovidos.
  - `bScore<Familia>` con polaridad segura, también en `BP_BreathStage_SC.StepStageVO` y en `HallSay`.
  - `ImportedRev` dentro del asset y no solo en el log.
  - Cosecha sin `load_level`, por `refPath` y con el aviso `is_dirty`.
- **§4 (PLAN:314-317):**
  - F1 exige reemplazar las bases de `world.js` y `guion.js` con la cosecha, o rotular la vista "previs, not Unreal positions".
  - F4: primera familia = **cadena de VO de Entering**, no ambientes. Cuándo suena cada ambiente lo decide un literal de `AmbPick` (TRK/BP_Obra_SC.md:367-378).
  - Agregar la fila de empaque de la Obra (`-map=`) en `docs/WORKFLOW-EQUIPO.md:154-160`.
- **§5 (PLAN:329):** MVP de 10 acciones: Appear, Disappear, Alma VO, Omnipresent VO, Sound, Ambience, Title, Veil, Wait (en lectura) y Demo ghost.
- **§6 (PLAN:342):** la decisión 1 queda "propuesta aplicada en el editor", no tres vías en runtime.

## Lo que falta construir en Unreal para que cada herramienta funcione

| Herramienta | Mínimo en Unreal | Costo |
|---|---|---|
| Perillas de instancia (todas) | Nada estructural. Turno de la cola: `get` → comparar con la base → `set` → releer → `save_assets` del subnivel → contar actores | Bajo |
| Cadena de VO de Entering (primer cambio verificable) | Ya existe: `SayAfterTool`/`SayGap`/`HelpAfter`/`ExploreTime`. Verificar por logcat de `OBRA: StageIntro` a `ALMA: SayClip` (DUMP:490; TRK/BP_Alma_SC.md:158) | Bajo |
| Marcas temporales | U1: leer los `PrintString` que ya existen. Después, un detector de flanco al final de `TickAll` y un nodo en `HallTickSteps` que llamen `Mark(Name)` | Medio |
| Traza `SCORE` | `PrintString "SCORE\|rev\|…"` en el BeginPlay del player y por cue | Bajo |
| Tabla de cues | DataAsset (BP con arrays paralelos, patrón `BP_GhostTake_SC`) + instancia escrita por MCP. Columna Asset tipada SoundBase | Medio |
| `BP_ScorePlayer_SC` | BP nuevo colocado en `L_SoulCharger_Obra`. Cursor por marca, `PlaySound2D`/`PlaySoundAtLocation` por tag, reloj con `Dt` recortado. Todas las variables creadas antes de colocarlo | Medio-alto |
| Corte del doble disparo | `bScore*` en `BP_Obra_SC`, `BP_BreathStage_SC` y `BP_HallDirector_SC` (tanda estructural con el nivel cerrado) | Medio |
| Empty sound → Unreal | Sesión: bajar el WAV, validar, copiarlo a `Obra/Audio/FX/` (auto-import), fijar `bLooping`/`ForceInline`/atenuación por MCP (verificar) y referenciarlo en la tabla | Medio |
| Help por voz en el Hall | Cablear VO_01h/VO_03h en `HallEnterIntro` con su temporizador | Medio |
| Timeout con SAVE forzado | En `CallOutro` de Attracting y Surrounding: SAVE y presentación antes del outro | Medio-alto |
| Move to mark (otros roles) | API `MoveTo(Tag)` por BP | Alto (fuera del MVP) |
| Rampa de parámetro | Un dueño por parámetro; si no, no se hace | Alto |
| Háptica HAP / buses / ducking | Hub háptico único (precedente `BP_HapticHub`, TRK/_INDEX.md:300) + SoundClass/Submix | Alto (config compartida) |
| Override JSON (F6) | Habilitar JsonBlueprintUtilities y leer de `Saved/` | Medio |
| Cosecha | `harvest_score.py` versionado en el repo (no en `Saved/`, ignorado por `.gitignore:10`) | Bajo-medio |

## Catálogo v0 de perillas por rol (consolidado, solo variables verificadas)

| Rol | Perilla (variable, valor, unidad) | Dueño (nivel · actor) | Ámbito | Evidencia |
|---|---|---|---|---|
| Timbre | `Appear.Duration` 1,5 s | Test_Hall · `Timbre` (componente) | componente | TRK/BPC_AppearLuz_SC.md:29 |
| Timbre | `BellPressDepth` 1 cm · `BellPressTime` 0,12 s · `BellHold` 3 s · `FW_Bell` 25 s (+3 de autollenado) · `TouchRadius` 14 cm · `SndBell`=Bell | Test_Hall · `HallDirector` | instancia | TRK/BP_HallDirector_SC.md:56,107,185; HDUMP:425 |
| Sensor (Hall) | `FW_Tool` 20 s | `HallDirector` | instancia | TRK/BP_HallDirector_SC.md:56 |
| Sensor (mano) | `MorphTime` 0,8 · `ColorTime` 1,2 · `SensorXfR` (4,325; −1,685; −2,335) roll 90 | Obra · `UserTool_Obra` | instancia | TRK/BP_UserTool_SC.md:22,27 |
| Candidatas | `FW_Choose` 25 s | `HallDirector` | instancia | TRK/BP_HallDirector_SC.md:56 |
| Puertas y baldosas | `DoorOpenDeg` 16,5 · `DoorTime` 3 · `TileLiftCm` 3 · `TileGlowMax` 0,35 · `TileTime` 1,5 · `ReturnGlow` 0,6 | `HallDirector` | instancia | TRK/BP_HallDirector_SC.md:55 |
| Caminata (Hall) | `OutTime` 8 · `ExitTime` 7 | `HallDirector` | instancia | TRK/BP_HallDirector_SC.md:184 |
| Stage · Entering | `ExploreTime` 12 (mín.) · `CountTime` 3,6 · `InhaleCueAt` 3,48 · `ToolDelay` 0,8 · `SayAfterTool` 1 · `SayGap` 0,5 · `HelpAfter` 4 | Test_Entering · `Entering_Stage` | instancia (`CountTime` hereda del CDO) | TRK/BP_BreathStage_SC.md:86,95,97,105 |
| Pacer | `Inhale/Hold1/Exhale/Hold2Time` 4/3/4/3 · `Preset` 0 · `Cycles` 5 · `LeadIn`/`LeadOut` 3 · `SizeCm` 350,6 | Test_Entering · `Entering_Pacer` | instancia | usertool/pacer_read.json:164 |
| Pacer | `IntroTime`/`OutroTime` 0,6 s | BP_Pacer_SC | CDO | TRK/BP_Pacer_SC.md:34 |
| Metaball | `IntroTime` 2,5 · `OutroTime` 2,5 s · tamaño = `SizeCM` | Test_Entering · `Entering_Blob` | instancia | TRK/BP_BreathBlob_SC.md:23,77,83 |
| Alma | `Size` 1 m (× escala del TP; laterales 0,6, `hall_alma_side` 0,5) · `Brightness` 1,5 | Obra · `BP_Alma_SC_C_0` | instancia + TP | Obra/alma_diff.json:15-17,95-97; TRK/BP_Obra_SC.md:232,360 |
| Alma | `AppearTime` 1,2 · `DisappearTime` 0,6 · `TravelTime` 3 s | BP_Alma_SC | CDO (instancia en vivo) | TRK/BP_Alma_SC.md:75-76 |
| Membrana | `BeatDiv` 2 · `StageBeats` 19 · `OrbitAtBeat` 8 · `BackupAfter` 30 s | Test_Heart · `HeartManager` | instancia + CDO | TRK/BP_HeartManager_SC.md:170,173 |
| Célula | `StageDuration` 60 · `IntroDelay` 2 · `VO22At` 15 · `VO23At` 42 · `VOWait` 8 s | Test_Fluid · `LovingCell` | instancia | TRK/BP_LovingCell_SC.md:65,73 |
| Final | `ShareFW` 30 s · `ResultsTime` 150 (CDO) · `SimStageMax` 90 | Obra · `BP_Obra_SC_C_0` | instancia/CDO | TRK/BP_Obra_SC.md:110,115,123 |
| Final (Alma) | `ResAlmaLeft` 45 · `ResAlmaScale` 0,7 | `BP_Obra_SC_C_0` | instancia | TRK/BP_Obra_SC.md:293 |
| Ambientes | `AmbClips[9]` · `AmbVolumes` 0,8 · `AmbFadeIn/Out` 3 s (cuándo suena cada uno = literal `AmbPick`) | `BP_Obra_SC_C_0` | instancia | TRK/BP_Obra_SC.md:200 |
| Aviso | `DiscTime` 19 (acoplado al literal `DiscStep`) | BP_Obra_SC | solo CDO | TRK/BP_Obra_SC.md:383-384 |
| Fantasmas | `PlayRate` 1,25 · `LoopGap` 0,4 · `bGhostsOn` | `Ghost_*` / Obra | CDO/instancia | TRK/BP_GhostPlayer_SC.md:33; TRK/BP_Obra_SC.md:331 |
| Literales (no son perillas) | lead-in de VO 1,5 · `AlmaTime` VODur + 3,5 (o + 3) · cortafuegos 180/120/240 · título/velo | `RunObra`/`AlmaSpeak`/`StageTimes` | literal | DUMP:466-501,966-977 |

Las esferas, la tinta, el HUD, los créditos y los transforms de `Final_*` quedan fuera hasta la cosecha: su única fuente es MAPA, que ya divergió (MAPA:228,233,242,277).

## Vocabulario v0 de condiciones de espera y de marcas

**Condiciones que existen:**

| Ámbito | Condición | Evidencia |
|---|---|---|
| Hall | `hall.bell.live` (`bBellLive`) | HDUMP:419-425 |
| Hall | `hall.bell.charged` (`BellCharge` ≥ 1) | HDUMP:419-425 |
| Hall | `hall.sensor.live` (`bSensorLive`; toma con la mano a menos de `TouchRadius`) | HDUMP:419-425 |
| Hall | `hall.soul.live` (`bPickLive`) | HDUMP:419-425 |
| Hall | `hall.fw` (`StepTime` > `FW_*`) | HDUMP:419-425 |
| Breath | `breath.zone` (`Rig.bZone`: zona + cara del sensor, instantánea; `FacingMin` 0,34) | TRK/BP_BreathRig_SC.md:59-61 |
| Breath | `breath.on` (`bBreathing`: zona ∧ quietud ∧ amplitud, 1,5/0,2 s) | TRK/BP_BreathManager_SC.md:44,78; duplicado en el Rig, TRK/BP_BreathRig_SC.md:9 |
| Breath | `pacer.running` (`Pacer.bRunning`) | — |
| Breath | `stage.done` (`bStageDone`) | — |
| Heart | `heart.zone` (`bHeartZone`) | TRK/BP_Obra_SC.md:326 |
| Heart | `heart.backup` (`NoBeatT` ≥ `BackupAfter`) | TRK/BP_HeartManager_SC.md:173 |
| Heart | `heart.pulse.n` (`BeatCount`) | — |
| Attracting | `attract.first` (`Sequencer.Phase` ≥ 2) | TRK/BP_Obra_SC.md:224,327 |
| Attracting | `attract.saved` (`Phase` ≥ 3) | TRK/BP_Obra_SC.md:224,327 |
| Attracting | `attract.orbs ≥ 3` | TRK/BP_Obra_SC.md:224,327 |
| Drawing | `draw.ink > x` (`InkUsed` > 0 / 0,3 / 0,6) | TRK/BP_Obra_SC.md:224,328 |
| Drawing | `draw.ink < 0.05` | TRK/BP_Obra_SC.md:224,328 |
| Final | `share.pick` (`ResPressN` + hover) | TRK/BP_Obra_SC.md:110 |
| Final | `share.fw` (`ShareFW`; el valor por defecto depende de `bSimulated`) | DUMP:1552-1553 |
| Global | `sim` (`bSimulated`) | — |

**No existen:** "for 1 s", `G_*` como entidad, `GATE.late` y `VO.end` (la voz 2D no avisa, y `FadeVoice` no dispara `OnVOFinished`, TRK/BP_Alma_SC.md:171).

**Marcas que se pueden emitir:**
- **Hoy, por log** (verificado):
  - `S<K>.INTRO`: `OBRA: StageIntro` (DUMP:490).
  - `S<K>.BEGIN`: `OBRA: StageBegin` (DUMP:496).
  - `S<K>.OUTRO.done|fw`: `OBRA: StageOutro, por fin propio =` (DUMP:504).
  - `S<K>.OUTRO.sim`: `OBRA: modo simulado` (DUMP:1729).
  - `HALL.VOICECUT`: `HALL: voz cortada` (HDUMP:437).
  - `HEART.BACKUP`: `HEART: latido de respaldo`.
  - `BREATH.ON|OFF`: `BREATH: UMBRAL IN/OUT`.
  - `VO.<clip>.start`: `ALMA: SayClip`, con la duración como dato.
- **Con el detector de flanco** (fases verificadas en DUMP:470-512):
  - `S<K>.OPEN` (0) → `S<K>.ALMA` (4) → `.INTRO` (5) → `.BEGIN` (6) → `.OUTRO` (7) → `.CHARGE` (8) → `.BYE` (2) → `.END`.
  - `HALL.<modo>.<paso>`.
  - `FINAL.*` y `SHARE.<estado>`: los números de fase son internos (TRK/BP_Obra_SC.md:52). Usar los nombres semánticos.

## Verificar en vivo (checklist para una sesión en su turno de la cola)

Todo es de solo lectura, sin `load_level`, con `L_SoulCharger_Obra` abierto.

| # | Nivel / actor | Propiedad o función | Qué se espera |
|---|---|---|---|
| 1 | Editor | `get_current_level`; subniveles cargados; `is_dirty` de los 7 paquetes | La Obra abierta, con sus 6 celdas cargadas |
| 2 | Obra · `BP_Obra_SC` | `read_graph_dsl` de `AlmaSpeak` y `StageTimes` | `AlmaTime` VODur + 3 o + 3,5; ¿sigue leyendo `StAlma`? |
| 3 | Obra · `BP_Obra_SC` | `RunObra` (fase 6) y `FlowVeil` | 180/120/240; salto de T 5,5 → 9 |
| 4 | Obra · `BP_Obra_SC_C_0` | `DebugStart`, `bSimulated`, `ShareFW`, `ResAlmaLeft`, `ResAlmaScale`, `AmbClips[0..8]` | `DebugStart` −1 antes del APK |
| 5 | Obra · `BP_Obra_SC` | Grafo `AlmaResults` | ¿Lee `final_alma` o `ResAlma*`? |
| 6 | Test_Hall · `HallDirector` | `BellPressDepth`, `BellPressTime`, `BellHold`, `FW_Bell/Tool/Choose`, `TouchRadius`, `VOAir`, `OutTime`, `ExitTime`; array `VO` | Que no estén en 0. Mapa id → índice de las VO |
| 7 | Test_Hall · `HallDirector` | `relativeLocation`/`Rotation` de `StopCard`, `StopInside`, `StopExit`, `StopReturn` | Resolver 300 / 396,45 y −300 / −450,5 |
| 8 | Test_Hall · `HallDirector` | `HallSensorSpin` y `HallSensorOrb.SpinDeg` | ¿Se suman los dos giros? |
| 9 | Test_Hall · `Timbre` | `Appear.Duration`, `AppearSound`, `VanishSound`, `Tags` | 1,5 s; tag `hall_bell` |
| 10 | Test_Entering · `Entering_Stage` | `ExploreTime`, `CountTime`, `InhaleCueAt`, `ToolDelay`, `SayAfterTool`, `SayGap`, `HelpAfter`; grafo `StepStageVO` | 12 / 3,6 / 3,48 / 0,8 / 1 / 0,5 / 4. ¿El ancla de VO_11h es el inicio o el fin de VO_11b? |
| 11 | Test_Entering · `Entering_Pacer` | `Preset`, los 4 tiempos, `LeadIn`, `LeadOut`, `Cycles` | 0; 4/3/4/3; 3; 3; 5 |
| 12 | Test_Entering · `Entering_Pacer` y `Entering_Blob` | Corrección por altura | ¿Se corrigen por altura de ojos? |
| 13 | Los 5 tests | `TP_sc<K>_alma_in/_alma_side/_charge/_title` | Posición, yaw, escala XYZ y claves del dict `rotation`; `alma_side` en escala 0,6 |
| 14 | Obra · `UserTool_Obra` en PIE | Parámetro `Active` del MID de `Waves`, con `bZone` true | ¿Existe "Rings on"? |
| 15 | Test_Heart · `HeartManager` / Test_Fluid · `LovingCell` | `BeatDiv`, `StageBeats`, `BackupAfter` / `StageDuration`, `IntroDelay` | 2 / 19 / 30 / 60 / 2 |
| 16 | `/Game/SoulCharger/Obra/Audio/Placeholder/FX_SHAREAPPEAR` y una copia de un SoundWave | Canales, compresión y `loadingBehavior`. Prueba de `set_properties` con `attenuationSettings` = `ATT_Objeto_SC` y `ForceInline` | ¿El MCP puede fijarlos? |
| 17 | Editor | `find_node_types("SetFloatPropertyByName")` | ¿Existe un `ScoreApply` genérico? |
| 18 | Narrativa | La línea `BuildCookRun -map=…` del APK de la Obra del 10-01 | Versionarla en `docs/WORKFLOW-EQUIPO.md` |