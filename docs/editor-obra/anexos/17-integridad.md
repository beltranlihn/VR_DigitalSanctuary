> Anexo: sistema de integridad del editor (2026-10-01). Lo que manda es [PLAN-EDITOR-OBRA-2026-10-01.md](../PLAN-EDITOR-OBRA-2026-10-01.md).

# Sistema de integridad del editor de la obra

**Idea central:** cada gesto del editor pasa por un verificador, una función pura que recibe la partitura de antes, la operación, la partitura de después y el contexto, y devuelve una lista de problemas. Cada problema tiene una gravedad, una capa, la evidencia y las reparaciones posibles.

Lo que hoy rompe la obra casi nunca está en la partitura: está **cableado en grafos de Unreal**. Por eso la pieza clave es un **catálogo de contrato** (`obra/unreal/contract.json`) que marca cada elemento, valor o id con una bandera `hw` (dueño, grafo, evidencia). La cosecha lo mantiene al día.

"Seguir igual" siempre se puede, salvo con los invariantes del modelo de datos. Cuando lo haces queda registrado con autor, motivo y fecha. Si el APK va a hacer algo distinto de lo que muestra el editor, el elemento queda marcado **≠ APK** hasta que la cosecha pruebe que alguien lo conectó.

**Abreviaturas** (raíz `VR Unreal/`):

| Abreviatura | Archivo |
|---|---|
| DUMP | `VR_Test/Saved/ClaudeScripts/obra/dump/obra_all_now.txt` (13:07) |
| HDUMP | `…/obra/dump/hall.txt` |
| HDSL | `VR_Test/Saved/ClaudeScripts/Hall/dsl/HallEnterIntro.dsl` |
| OBRA / HALL / BS | `.claude/skills/unreal-vr/blueprints/BP_Obra_SC.md` / `BP_HallDirector_SC.md` / `BP_BreathStage_SC.md` |
| TRK/ | `.claude/skills/unreal-vr/blueprints/` |
| REF/ | `.claude/skills/unreal-vr/references/` |
| TAX | `docs/editor-obra/anexos/04-guion-taxonomia.md` |
| CRIT | `docs/editor-obra/anexos/09-critica.md` |
| GUION | `docs/GUION-V5-2026-09-29.md` |
| MOCK | `web/editor-obra/mockup/src-body.html` |
| ISP | `…/Immersive Studio Pro/index.html` y `app.js` |
| SINT | `sintesis.md` de la auditoría (scratchpad `audit2/`) |

---

## 1. Modelo

### 1.1 Capas de chequeo

| Capa | Qué protege | Fuente | Ejemplo |
|---|---|---|---|
| **Invariantes** (no es una capa de problemas: el gesto no se aplica) | Que la partitura se pueda calcular | Esquema 2 | ciclo de anclas, ancla colgando, solape en Típico, VO más corta que su audio, borrar una sub-pista con clips |
| **C1 · Estructura de la partitura** | Coherencia interna | Partitura + personas | dependientes, ramas con lectores, anclas que cruzan un velo, choques que aparecen solo en Slow/Idle (CRIT:145-148) |
| **C2 · Reglas de la obra** | El guion y las lecciones del 10-01 | `obra/score/rules.json` (umbrales) | Alma habla ≥ aparición + 1,5 s (TAX:124,149); toda espera tiene ayuda < tope (GUION:121-124); nada aparece de golpe; música continua; háptico con final (TAX:129); título ≥ 3 s (TAX:21); inglés in-headset; créditos bloqueados (TAX:159); total Típico ≤ 15:00 |
| **C3 · Contrato con Unreal** | Que el APK haga lo que muestra el editor | `contract.json` + cosecha + `idmap.json` | literal en grafo, asset por ruta, VO por índice, tag leído por nombre, índice de etapa, audio horneado, punto de sincronía, dueño de la perilla, vocabulario de marcas |
| **C4 · Rendimiento Quest** | 72 Hz / 13,9 ms (REF/profiling-quest.md:3) | Partitura + catálogo | nunca dos apariciones en el mismo cuadro (GUION:33); nada arranca en el cuadro en que se enciende una celda (CRIT:55; OBRA:13,72); lotes de 2 piezas por cuadro (commit 8f1a1fa); audio de objeto mono a 48 kHz (REF/audio-quest.md:115,132) |

### 1.2 Gravedad y qué significa "seguir igual"

| Nivel | Significa | "Proceed anyway" | Registro | Push / APK |
|---|---|---|---|---|
| **BLOQUEA** | Rompe la experiencia (espera sin salida, voz que falta o sobra) o el APK hace otra cosa | **Motivo obligatorio** (≥ 12 caracteres) y campo "Will connect / Why" con opción "Create Unreal task" | `problems/<fingerprint>`: autor (`user.id()`), fecha, motivo, tarea vinculada | Push: solo si está **Accepted**. APK: con un C3 aceptado sin conectar, **firma de Beltrán** ("Ship with N known divergences") |
| **AVISA** | Degrada, o contradice una regla que admite excepción | Motivo opcional, con atajos ("Intentional", "Temporary", "Will connect in Unreal"). **Obligatorio si la perilla tiene candado** (PLAN:178) | Igual | No bloquea; se lista en el manifiesto y en el informe del build |
| **INFORMA** | Consecuencia esperable: propuesta generada, reflujo por un audio nuevo, alcance "preview only" | No hay tarjeta: solo la barra de estado | Solo en Problems (filtro Info), se resuelve sola | Nada |

- **Quién acepta:** Beltrán y el socio. **Quién firma el APK:** solo Beltrán. Las palancas `DebugStart` y `bSimulated` son de Beltrán (memoria `no-tocar-flags-debug`).
- **Huella del problema** = regla + ids de los elementos + parámetro clave. Un problema aceptado sigue aceptado mientras la huella no cambie. Si cambia (otro valor, otro elemento), se **reabre**.

### 1.3 Override de contrato: el estado ≠ APK

Aceptar un problema de C3 lo deja en **Accepted · diverges**:
1. En el clip: borde ámbar discontinuo y chip `≠ APK` (ámbar = anulado, ISP index.html:47).
2. En el inspector, una línea **"In the APK today:"** con lo que hace Unreal (por ejemplo, "VO_10 at Alma appear + 1.5 s · BP_Obra_SC › AlmaSpeak").
3. Con **View ▸ Show APK ghosts**, un fantasma gris fino en la misma sub-pista muestra dónde ocurre en el APK.
4. La píldora de sincronía separa la **deriva** (Unreal cambió) de las **rupturas aceptadas** (las cambiaste a propósito).
5. Se genera una **tarea** en `proposals/*`, de tipo `graph-task`, con texto listo para la sesión que tenga el turno de la cola. Ejemplo: "RunObra: literal 180.0 (stage 1) → 150.0, set_pin_value · evidence DUMP:501".

**Para pasar a Resolved · connected**, la cosecha o el volcado tienen que mostrar el valor nuevo. No se cierra a mano: el cierre manual es **Waived**, solo para Beltrán y con motivo.

---

## 2. Catálogo de rupturas por acción

Cada acción lista entre paréntesis los chequeos que corre. "INV" = invariante: no hay "Proceed anyway", solo Cancel y las reparaciones.

| Acción | Qué se rompe (ejemplo real · evidencia) | Gravedad | Tarjeta (EN) | Reparación |
|---|---|---|---|---|
| **Borrar** (C1 dependientes y ramas · C2 cobertura · C3 `hw`) | VO_10: `AlmaSpeak` la llama por ruta, y `AlmaTime` = VODur + 3,5 (DUMP:968,977). El APK la sigue diciendo | C3 · BLOQUEA | "VO_10 is wired in BP_Obra_SC › AlmaSpeak. Deleting it here won't silence it in the APK." | Unreal task "remove call K=0" · Keep as preview-only removal |
| | Elemento con anclados (VO_11h depende de VO_11b + `HelpAfter`, BS:103) | INV | "3 cues are anchored to this clip." | Re-anchor to its parent (keep times) · Delete with family |
| | `GHOST_BELL`: es la única ayuda del timbre (VO_01h sin cablear, HALL:7, OBRA:216), y `GhostTick` lo enciende por toma (OBRA:310-319) | C2 + C3 · BLOQUEA | "The bell wait would have no help. Unreal still plays this ghost." | Add help VO · Unreal task |
| | Ambiente de un tramo: deja un hueco de música (TAX:122), y en Unreal lo decide `AmbPick` (OBRA:367-378) | C2 AVISA + C3 BLOQUEA | "Music gap of 12 s. AmbPick still plays AMB_04 here." | Extend the previous ambience |
| | El final de un háptico continuo (lección TAX:129) | C2 · BLOQUEA | "HAP_BREATH_HUM has no end." | End at the parent's end |
| **Mover en el tiempo** (INV solape · C1 personas y velo · C2 · C3 ancla→perilla · C4) | VO_11, anclada a `S0.INTRO` + `ToolDelay` + `SayAfterTool` (BS:103,105) | C3 · INFORMA | "Becomes a proposal: SayAfterTool 1.0 → 1.5 s (Entering_Stage)." | — |
| | VO_11 antes de `ToolDelay` (0,8): la perilla quedaría negativa | C3 · BLOQUEA | "Out of range: SayAfterTool would be −0.3 s." | Clamp to 0 |
| | Título de etapa: literales 0,5→1,8 / 4,6→5,6 (DUMP:466-468) | C3 · BLOQUEA | "Stage title times are literals in RunObra." | Unreal task (set_pin_value) |
| | Título más allá de 5,7 s: choca con Alma, que entra a 5,8 (DUMP:468,473; regla en OBRA:205) | C2 · BLOQUEA | "Title would overlap Alma (rule: never together)." | Snap out to 5.6 s |
| | VO de Alma antes de fin de aparición + 1,5 s (DUMP:968; TAX:124) | C2 · BLOQUEA | "Alma would speak before she has appeared." | Snap to appear end + 1.5 s |
| | Cambio de ambiente: literal de `AmbPick` (OBRA:367-378) | C3 · BLOQUEA | "Ambience changes are decided in AmbPick." | Unreal task |
| | Pacer: anclado a `VO_12c.start + InhaleCueAt` 3,48, el "inhale" de la grabación (BS:94-97) | C3 · AVISA | "The pacer is synced to 'inhale' inside VO_12c." | Move via InhaleCueAt (proposal) |
| | Aparición a ±13,9 ms de otra (GUION:33) | C4 · AVISA | "Two reveals in the same frame." | Stagger 0.4 s |
| | Choque que aparece solo en Slow o Idle (CRIT:145-148) | C1 · AVISA | "Collides with VO_12 for the Idle user." | Show in Idle |
| **Recortar** (INV tipo de duración · C2 · C3 rango y acople) | Una VO: dura su audio (PLAN:247) | INV | "A voice lasts its audio — replace the audio instead." | — |
| | Última carga (`ChargeTimes[4]` 6): acoplada a `FlowVeil` 9,5→11,5 y `ReadCharge` 5,6 + C (OBRA:268-270), y al golpe de `ChargeFinal` a 10,5 s (OBRA:217) | C3 · BLOQUEA | "3 literals assume a 6 s final charge." | Unreal task with Δ |
| | Loving por debajo de `VO23At` 42 + VO_23 (TRK/BP_LovingCell_SC.md:67-69,73) | C3 · AVISA | "VO_23 would run into the outro." | Pull VO23At |
| | Título < 3 s (TAX:21) | C2 · AVISA | "Below readable minimum (3 s)." | — |
| | Aparición < 0,3 s (TAX:150; `Appear.Duration` 1,5, TRK/BPC_AppearLuz_SC.md:29) | C2 · AVISA | "Would pop in." | Set 1.5 s |
| | Un fantasma: elástico, dura hasta el gesto (OBRA:321-328) | INV | "Ghosts last until the user's first action." | — |
| **Cambiar sub-pista o grupo** | Otra sub-pista: nunca cambia el comportamiento (PLAN:240); si está ocupada, el clip no cae (MOCK:364) | INFORMA / INV | — | Slot below |
| | De Voice (`SayClip`, interrumpible) a "omnipresent" (`PlaySound2D` sin manija, DUMP:1872-1875) | C3 · BLOQUEA si `hw`, si no AVISA | "Omnipresent voice can't be interrupted; 'If early' off." | Convert… |
| | Grupo de otro tipo (VO → Haptics) | INV | — | Convert… |
| **Re-anclar** (INV ciclo y ref · C3 marcas · C2) | A `GATE.*.late` o `VO.*.end`, que no existen; `FadeVoice` no dispara `OnVOFinished` (SINT:298; TRK/BP_Alma_SC.md:171) | C3 · BLOQUEA | "Unreal never emits this mark. Preview only." | Use VO.start + duration |
| | VO_11h fuera de "VO_11b + HelpAfter": el ancla está codificada en `StepStageVO` (BS:103) | C3 · BLOQUEA | "This anchor is implemented by a graph; only the offset maps to HelpAfter." | Keep anchor, edit offset |
| | Algo autoral anclado a una acción del usuario (TAX:144) | C2 · AVISA | "Authored content would wait for the user." | — |
| | Ciclo | INV | "Circular anchor." | — |
| **Cambiar perilla** (C3 dueño, ámbito, rango, candado, acople, nace en 0 · C2 derivadas) | Perilla con candado: valor final de test (TAX:158) | AVISA, motivo obligatorio | "Final test value. Reason required." | — |
| | `Inhale/Hold1/Exhale/Hold2Time`: audio horneado a 4-3-4-3 (TRK/BP_Pacer_SC.md:86). `Preset` ≠ 0 pisa los cuatro tiempos (:43) | C3 BLOQUEA / AVISA | "Pads and plucks are baked at 4-3-4-3." | Task: `make_pacer_sounds.py` |
| | `DiscTime` 19 (CDO) ↔ `DiscStep` `Out` 17,6-18,7 (OBRA:383-384) | C3 · BLOQUEA | "DiscStep text-out is a literal tied to DiscTime." | Shift by Δ (task) |
| | `IntroHold` 17 ↔ `IntroTitle` `Out` 17-19,5 y oculto a los 20 (OBRA:385-387) | C3 · BLOQUEA | Ídem | Ídem |
| | `ChargeTimes[0..3]`: el golpe de `Charge1` cae a 9,37 s, cuando se va el anillo (OBRA:217) | C3 · AVISA | "Charge1 hit no longer lands on ring exit." | — |
| | `bGhostsOn` false: las 3 esperas del Hall se quedan sin ayuda (HALL:7; OBRA:331) | C2 · BLOQUEA | "3 waits lose their only help." | — |
| | Un literal presentado como perilla ("Stays VO + 3"; evidencia en conflicto: +3,5 en DUMP:977 contra +3 en OBRA:296) | C3 · BLOQUEA (unverified) | "Graph literal, not a knob. Evidence conflicts — verify." | Task: promote literal |
| | Dueño equivocado (`BellPressDepth` es de `HallDirector`, no de `BellArt`; HALL:107) | C3 · BLOQUEA | "This knob belongs to HallDirector." | Re-target |
| **Renombrar id** (INV formato · C3) | La key visible: el ULID es la llave (PLAN:248) | INFORMA | — | — |
| | Asset de una VO: hay rutas en grafos (DUMP:968-976,1696), e `importar_mezcla.py` busca por nombre de archivo (:14-17) | C3 · BLOQUEA | "Graphs reference this path; the next mix import would duplicate it." | — |
| | VO del Hall: van por índice, `HallSay :I n` (HDSL:33-68; HALL:57) | C3 · BLOQUEA | "Hall voices are played by array index." | — |
| | Tag de TP o de rol (`sc0_alma_side`, `hall_bell`): se leen por tag (DUMP:1439-1485; HALL:160) | C3 · BLOQUEA | "BP_Obra_SC finds this point by tag." | — |
| | Toma `DA_Ghost_*`: `GhostTick` decide por el nombre de la toma (OBRA:310) | C3 · BLOQUEA | Ídem | — |
| | Formato: `VO_11h` pasaría a `VO_11H` (MOCK:304; TAX:148) | INV | — | Keep suffix lowercase |
| **Reemplazar o borrar audio** | VO más larga: todo lo anclado se corre | INFORMA (con diff) | "7 cues shift +1.1 s." | — |
| | Si el tope del Hall cuenta desde el inicio del paso con la VO adentro (HDUMP:419-425) y la VO pasa a ser más larga que el tope | C2 · BLOQUEA | "The bell would fill itself before the voice ends." | Raise FW_Bell |
| | VO_12c: punto "inhale" a 3,48 s (BS:94,97) | C3 · AVISA | "Re-mark the 'inhale' point." | Set sync → InhaleCueAt |
| | VO_12c tiene dos copias en `Content` (`importar_mezcla.py:14-17`) | C3 · AVISA | "2 copies in Content." | — |
| | WAV referenciado por ruta (VO_35a, DUMP:1696) | C3 · BLOQUEA | "Referenced by ShareExit." | — |
| | Borrar el `.wav` fuente: `bAutoDeleteAssets=True` borra también el asset (`EditorPerProjectUserSettings.ini:81`) | C3 · BLOQUEA | "Unreal would delete the asset too." | — |
| | WAV estéreo o que no está a 48 kHz, para un sonido de objeto | C4 · AVISA | "Stereo won't spatialize." | — |
| **Espera, tope o ayuda** | Topes de etapa 180/120/240: literales en `RunObra` (DUMP:501) | C3 · BLOQUEA | "Stage timeouts are literals." | Task |
| | `FW_Bell`/`Tool`/`Choose`: de instancia (HALL:56) | INFORMA (+candado) | "Proposal on HallDirector." | — |
| | Ayuda ≥ tope, o sin ayuda (GUION:121-124) | C2 · BLOQUEA | "Help would never play." | Help at 1/3 |
| | "On timeout = real ending" en una etapa: el tope llama `CallOutro` sin SAVE ni coda (DUMP:501-505; TRK/BP_Sequencer_SC.md:516-517) | C2 · BLOQUEA (ya existe) | "Timeout skips SAVE and coda." | Accept · task |
| | "If early" en una etapa: solo existe en el Hall (HALL:139) | C3 · BLOQUEA | "Voice-cut exists only in the Hall." | — |
| | Total Típico > 15:00 | C2 · AVISA | "Typical 15:42 (> 15:00)." | — |
| **Rama** | Borrar SHARE: `Shared` se lee hasta la fase 14 (DUMP:1565,1636,1648) | C2 · BLOQUEA (TAX:156) | "Downstream reads 'Shared'." | — |
| | Opción por defecto al tope: `select(bSimulated)` (DUMP:1553) | C3 · BLOQUEA | "Default is wired to bSimulated." | Task |
| | Quitar VO_35a de una toma: suena en ambas (DUMP:1696) | C1 · AVISA | "Shared by both takes." | — |
| **Borrar sub-pista o momento** | Sub-pista con clips (PLAN:157) | INV | — | — |
| | Momento que es una fase de Unreal (`S<K>.INTRO`…, SINT:311) | C3 · BLOQUEA | "This moment is a phase in BP_Obra_SC." | Empty it, keep it |
| **Mover un punto espacial** | TP de etapa: es una propuesta; la escala es el tamaño de Alma (OBRA:232) | INFORMA | "Alma will be 0.60 m here." | — |
| | Paradas `Stop*`: `HallExitEarly` en x ≥ 760 (OBRA:230), sonido de puertas (HALL:169), guía (HALL:69) | C3 · BLOQUEA | "3 Hall literals assume this stop." | Task |
| | `ObraAlmaA/B`, `ObraChargeTarget`: se reescriben en cada etapa (DUMP:1440-1442,1474-1479) | C3 · BLOQUEA | "Rewritten at runtime — no effect." | Edit the stage TP |
| | Actor TestOnly: se descarta en la Obra (OBRA:381) | C3 · BLOQUEA | "Not present in the Obra." | — |
| | Alma al costado fuera de ±60° (hoy 65°, `audit2/espacio.md`:9) · dos objetos en la misma zona a la vez (TAX:127) | C2 · AVISA | "Outside comfortable view." | — |
| **Orden de etapas** | Todo va indexado por K: celdas 0-4 (OBRA:12), topes (DUMP:501), `AmbPick` (OBRA:367-378), `ChargeTimes`/`CavNames`/`StageCols` (OBRA:42), K = 4 con `HoldTime` 9999 y `SpinDeg` −1440 (DUMP:674-676), VO por K (DUMP:966-976), `CueAttract`/`CueDraw` (OBRA:224), `bInstrReady` = etapa < 3 (OBRA:225), fantasmas (OBRA:321-328), mano por etapa (OBRA:303-305) | C3 · BLOQUEA | "Stage order is compiled into 11 places in BP_Obra_SC." | Open as design proposal |
| **Aplicar plantilla** | Demonstrated en Loving, Save o Share: no tienen toma (TRK/BP_GhostPlayer_SC.md:13). Los fantasmas van mudos y sin texto (:16,47) | C3 · BLOQUEA | "No ghost take exists for Loving." | — |
| | Stage mold como etapa nueva: las celdas son fijas | C3 · BLOQUEA | "New stages are preview only." | — |
| | Cualquier plantilla nace "preview only"; Layered escalona sola | INFORMA / C4 | — | Auto-stagger |
| **Empujar a Unreal** | Ver §5 | — | — | — |

---

## 3. La lista negra (catálogo de contrato)

### 3.1 Qué contiene (v0, armado a mano desde la evidencia)

| Id | Qué | Tipo | Evidencia | Acoplado con | Se edita por |
|---|---|---|---|---|---|
| fw.stage | Topes 180/120/240 → `CallOutro` | literal | DUMP:501-505 | camino de salida sin SAVE (TRK/BP_Sequencer_SC.md:517) | tarea |
| title.stage | 0,5→1,8 · 4,6→5,6 · visible < 5,7 | literal | DUMP:466-468 | Alma ≥ 5,8 (DUMP:473) | tarea |
| veil | abre 1→4 · cierra 69→71,5 · `AdvanceStage` 71,5 | literal | DUMP:444,462,481 | salto de `FlowVeil` | tarea |
| alma.speak | lead-in 1,5 · `AlmaTime` VODur + 3,5 (¿o + 3?) | literal | DUMP:968-977; OBRA:296 | `StageTimes` | tarea (sin verificar) |
| amb.pick | K por momento | literal | OBRA:367-378 | `AmbClips` (perilla, OBRA:200) | tarea |
| disc | `DiscTime` 19 ↔ `Out` 17,6-18,7 | par | OBRA:383-384 | — | perilla CDO + tarea |
| intro | `IntroHold` 17 ↔ `IntroTitle` 17-19,5 / 20 | par | OBRA:385-387 | — | perilla + tarea |
| charge.last | llenado 2,47→8,47 · velo 9,5→11,5 · `ReadCharge` 5,6 + C | par | OBRA:268-270 | `ChargeFinal` golpe 10,5 (OBRA:217) | tarea |
| charge.hold | `HoldTime` 2/9999 · `SpinDeg` | literal | DUMP:674-676 | K = 4 | tarea |
| cues.34 | VO_27h 20 s, VO_32h 15 s, umbrales de tinta | literal | OBRA:224 | — | tarea |
| hall.exit | x ≥ 760 | literal | OBRA:230 | `Stop*` (HALL:30) | tarea |
| hall.bell | autollenado tras `FW_Bell`, descarga −2/s | literal | HDUMP:425 | `BellHold` | tarea |
| hall.cut | corte de voz 0,3 | literal | HALL:139 | — | tarea |
| share.def | default = `bSimulated` · `DebugShare` | literal | DUMP:1550-1553 | `Shared` (DUMP:1648) | tarea |
| vo.paths | VO por ruta | asset | DUMP:968-976,1696 | mezcla por nombre (`importar_mezcla.py:14-17`) | ninguna |
| hall.vo | VO por índice | índice | HDSL:33-68; HALL:57 | array `VO` | ninguna |
| tp.tags | `sc<K>_*` leídos por tag | tag | DUMP:1439-1485 | escala = tamaño (OBRA:232) | punto |
| role.tags | `hall_bell`/`hall_sensor`, `ObraAlmaA/B`, `ObraChargeTarget` | tag / runtime | HALL:160; DUMP:1440,1474 | — | ninguna |
| ghost.take | `DA_Ghost_*` por nombre | nombre | OBRA:310-328 | banderas | ninguna |
| stage.k | índices de etapa | índice | OBRA:12,42,224-225,303-305 | todo lo anterior | ninguna |
| pacer.baked | audio a 4-3-4-3 | horneado | TRK/BP_Pacer_SC.md:86 | 4 perillas | tarea de audio |
| sync.inhale | "inhale" a 3,48 s dentro de VO_12c | sincronía | BS:94,97 | `InhaleCueAt` | perilla |
| sync.charge1 | golpe a 6,9 s → 9,37 | sincronía | OBRA:217 | `ChargeTimes` | — |
| marks | no existen `GATE.late` ni `VO.end` | vocabulario | SINT:298; TRK/BP_Alma_SC.md:171 | — | — |
| alma.nospawn | Alma no se spawnea | diseño | TRK/BP_Alma_SC.md:93 | — | — |
| testonly | actores que se descartan en la Obra | config | OBRA:381 | — | — |
| apk.debug | `DebugStart` −1 antes del APK | config | OBRA:347,386 | — | Beltrán |
| autodelete | `bAutoDeleteAssets` | config | `EditorPerProjectUserSettings.ini:81` | — | — |

### 3.2 Cómo se representa

**En la partitura**, cada elemento afectado lleva `hw`:

```json
"hw": [{ "c": "fw.stage", "role": "value", "owner": "BP_Obra_SC", "graph": "RunObra",
         "ev": "DUMP:501", "edit": "task", "state": "verified|stale|conflict" }]
```

- **En el timeline:** un glifo `ICO('wire')` en color `--ink-3` (nunca cian: el cian es solo "vivo", CRIT:222). Es distinto del candado.
- **En el inspector:** "Wired in Unreal · BP_Obra_SC › RunObra · literal 180 s".

**En `obra/unreal/contract.json`** (versionado, nada en `Saved/`), cada entrada lleva:
- `id`, `kind`, `owner`, `graph`;
- `match`: el patrón DSL que la identifica, por ejemplo `"180.0 (select (== _stage 2) 120.0 240.0)"`;
- `binds`: ids de elementos o nombres de perillas;
- `couples`, `edit`, `verifiedAt`, `dumpHash`.

### 3.3 Cómo se refresca con la cosecha

1. **`harvest_score.py`** trae instancias, tags, TPs y duraciones.
2. **Cosecha de contrato:** `read_graph_dsl` filtrado de una lista fija de unos 14 grafos (`RunObra`, `AlmaSpeak`, `StageTimes`, `AmbPick`, `FlowVeil`, `FlowShare`, `StageCues`, `GhostTick`, `IntroTitle`, `DiscStep`, `ChargeStart`, `HallEnterIntro`, `HallExitEarly`, `HallTickTouch`). Lo hace un subagente, en el turno de la cola. Después se aplica `grep` de cada `match`.
3. Los resultados posibles:
   - **El patrón coincide:** la entrada queda *verified*.
   - **El patrón cambió:** problema "Contract changed in Unreal" (INFORMA para la entrada, AVISA para los elementos que la usan). Si el valor nuevo es el de la partitura, resuelve los ≠ APK.
   - **El volcado es anterior al último commit del `.uasset`:** la entrada queda *stale* ("not checked", SINT:218) y **se sigue aplicando**: un riesgo identificado se verifica, no se apaga.
   - **La evidencia se contradice** (AlmaTime, `StopCard` 300/396,45, SINT:25-27): *conflict*. El problema sale como BLOQUEA (unverified) hasta la verificación en vivo.

---

## 4. UX

### 4.1 Tarjeta de impacto

Usa el andamiaje de ISP: `_dialogBase` con `.overlay`, `.modal`, `togbtn2`, `ovTop` y Esc = cancelar (ISP app.js:5687-5740), con el orden de 3 botones de `appConfirm3` (app.js:5744).

El cuerpo **no puede ser el `message` escapado** (R312·A5): necesita un renderizador propio, con 410 px de ancho y z 360.

```
Move · VO_10 "Welcome, take a breath…"   −2.0 s
● Breaks · Wired in Unreal                          BP_Obra_SC › AlmaSpeak · DUMP:968
  The APK keeps VO_10 at Alma appear + 1.5 s. Your new time is preview only.
● Breaks · Alma speaks before she appears          rule A3
  Appear ends 7.0 s; the voice would start at 5.5 s.
○ Warns · Two reveals in one frame (sensor, pacer)
· Also: 2 cues follow it (+0 s).
Repairs  [✓] Snap voice to appear end + 1.5 s   [ ] Create Unreal task
Reason (required to proceed anyway) [______________________]
                      [Cancel]  [Proceed anyway]  [Proceed and repair]
```

- **Orden de las secciones:** Breaks (●, `--danger`) → Warns (○, anillo `--danger`) → Also (`--ink-3`).
- Cada línea muestra el dueño en Unreal y la evidencia (un clic copia el `archivo:línea`).
- **Botones:**
  - *Proceed and repair* es el primario y solo aparece si hay reparaciones. Aplica la operación y las reparaciones como **un solo paso de deshacer**.
  - *Proceed anyway* usa el estilo oscuro de "Discard". Queda deshabilitado hasta escribir el motivo si hay un BLOQUEA. Si hay un C3, despliega "Will connect: [who] [what]".
  - Con invariantes, solo aparecen Cancel y las reparaciones.
- **Foco por defecto:** Proceed and repair, o Cancel si no hay reparaciones. **Nunca** Proceed anyway.
- **Una sola tarjeta por gesto:** junta todos los problemas nuevos, nunca una por regla. Los problemas que ya existían y no cambian no se muestran.

### 4.2 Durante el arrastre

- **Invariante:** fantasma rojo sólido que no cae (el actual `.ghost`, MOCK:104-105).
- **BLOQUEA:** fantasma rojo con borde discontinuo y "1 break" en su banda. Cae, y al soltar abre la tarjeta.
- **AVISA:** fantasma normal con un anillo rojo.
- **La familia se mueve con él:** cada hijo que choca se pinta igual.
- **Barra de estado:** `.statinfo.why` (ámbar, ISP index.html:1199), como en MOCK:364. Ejemplo:
  `VO_10 → wired in AlmaSpeak · APK keeps +1.5 s · 1 break · 1 warning · release to review`.
- **Costo por cuadro:** solo invariantes, la bandera `hw` y el chequeo de mismo cuadro (< 2 ms). Las reglas por persona corren al soltar.

### 4.3 Panel Problems (al estilo del Message Log o el Map Check de Unreal)

- **Dónde vive:** un cajón inferior con el patrón `.curvedrawer` de 188 px (ISP index.html:392; CRIT:220).
- **Cómo se abre:** con el contador de la barra de estado ("2 blocking · 5 warnings · 3 accepted"), con Window ▸ Problems o con **Experience ▸ Check obra** (todo × 4 personas).
- **Atajos:** F8 / Shift+F8 van al siguiente o al anterior.
- **Columnas:** severidad · capa · regla (`C3.HW.LITERAL`) · mensaje · elemento (clic: selecciona, centra y lleva el cabezal) · dueño en Unreal · evidencia · estado (**Open / Accepted / Resolved / Waived**) · autor · motivo · fecha · bandera ≠ APK.
- **Filtros:** severidad, capa, estado, "Affects APK", "Only mine", acto actual o toda la obra, persona.
- **Agrupar:** por elemento o por regla.
- **Acciones por fila:** Go to · Repair… · Accept… · Reopen · Copy Unreal task.

### 4.4 Cómo se ve en el timeline

| Estado | Marca |
|---|---|
| BLOQUEA abierto | contorno `--danger` de 1,5 px + punto lleno en la banda de título |
| AVISA abierto | anillo `--danger` |
| Aceptado | punto ámbar `#E5B567`; además, si es C3, contorno ámbar discontinuo + chip `≠ APK` + fantasma APK opcional |
| INFORMA | sin marca en el clip |

- **Regla de tiempo:** muescas rojas o ámbar sobre la regla, como un minimapa, para ver dónde se juntan los problemas.
- **Grupo plegado:** la fila resumen suma los puntos.
- **Presupuesto de color:** dos acentos más el de peligro, como pide ISP.

---

## 5. Cómo se calcula

**Datos que necesita:**
- la partitura (esquema 2) con su persona de referencia (Típico) y las tablas por espera;
- `obra/unreal/harvest.json` (instancias, tags, TPs, duraciones, `is_dirty`, rev y fecha);
- `obra/unreal/contract.json` + `idmap.json`;
- `obra/score/rules.json` (umbrales: 1/72 s, 0,3 s, 1,5 s, 3 s, 1 s de hueco de música, 15:00);
- `problems/*` (un documento por huella, sin superar 256 KiB, CRIT:22-24).

**Cuándo corre:**

| Momento | Qué corre | Efecto |
|---|---|---|
| Durante el arrastre | invariantes + `hw` + mismo cuadro | el gesto cae o no |
| Al soltar o aplicar | todo, sobre la clausura de dependientes × 4 personas | tarjeta si hay BLOQUEA o AVISA nuevos |
| Al abrir o al llegar una cosecha | todo | entran problemas de autor `harvest`, sin tarjeta |
| Push a Unreal | todo + precondiciones | regla de abajo |
| Empaquetar | todo + compuertas del APK | regla de abajo |

**Regla de push.**

Precondiciones que no admiten override:
- turno de la cola;
- nivel abierto `L_SoulCharger_Obra`, con los 6 subniveles cargados;
- `is_dirty` false en los paquetes destino, y sin PIE corriendo;
- la rev de la cosecha es igual a la base de cada propuesta;
- por perilla, el valor actual es igual a la base (si no, es un **conflicto**, no un problema);
- el dueño resuelve a un solo actor que no es TestOnly;
- para lo espacial se usa `set_properties` sobre el root y se relee (`set_actor_transform` no mueve nada, REF/toolsets.md:121);
- se cuentan los actores antes y después, y se guarda solo el subnivel tocado (CLAUDE.md §2.b);
- ninguna variable nueva en 0 (REF/gotchas.md:1438).

Después:
- **Cualquier BLOQUEA abierto dentro del alcance bloquea el push.** Los AVISA no bloquean.
- Los C3 aceptados viajan como `graph-task` en el manifiesto, en la sección "Will NOT be reproduced by Unreal". El elemento sigue ≠ APK.

**Regla del APK.**
- Bloquean: cualquier BLOQUEA abierto en toda la obra; `DebugStart` ≠ −1 (OBRA:386); `bSimulated` true en el perfil Festival (cambia SHARE, DUMP:1553); una cosecha anterior al último commit de los `.umap`; o la falta de la receta `-map=` versionada (`audit2/sincronia.md`:125).
- Los C3 aceptados sin conectar exigen la firma de Beltrán, que se registra en `obra/score/builds.json` con la lista de divergencias.
- Los AVISA van en el informe del build.

---

## 6. Las 10 reglas MVP

1. **Bandera `hw` + tarjeta en borrar, mover, recortar y renombrar.** Sale del catálogo v0 de §3, escrito a mano, sin cosecha. Es lo que más protege: cubre topes, título, velo, `AmbPick`, `AlmaSpeak`, VO del Hall y tomas.
2. **Pares acoplados y sincronías:** `DiscTime`↔`DiscStep`, `IntroHold`↔`IntroTitle`, `ChargeTimes[4]`↔`FlowVeil`/`ReadCharge`, `Stop*`↔760, ritmo↔audio horneado, VO_12c↔`InhaleCueAt`. La tarjeta muestra la otra mitad del par y crea la tarea.
3. **Dependientes al borrar o re-anclar** (invariante + "Re-anchor to parent"). Cierra el hueco de CRIT:143.
4. **Vocabulario cerrado de marcas:** solo se ancla a marcas que Unreal emite. Si no, el elemento queda "preview only".
5. **Perillas con dueño, rango, ámbito y candado:** motivo obligatorio con candado, y el chequeo "no en 0" al empujar.
6. **Alma habla después de aparecer + 1,5 s, y el título nunca coincide con Alma.**
7. **Toda espera tiene ayuda antes del tope, y el tope es mayor que la VO del paso más el mínimo físico** (`BellHold` 3).
8. **Nunca dos apariciones en el mismo cuadro, y nada aparece en menos de 0,3 s.**
9. **Háptico o bucle con final explícito, y música sin huecos de más de 1 s** para las 4 personas.
10. **Compuertas de push y APK:** conflicto de tres vías, cosecha al día, `DebugStart` −1 y ningún BLOQUEA abierto, más el estado ≠ APK y la firma de Beltrán.

**Sin verificar todavía.** Estos valores tienen evidencia contradictoria en el repo: `AlmaTime` (+3 o +3,5), `StopCard`/`StopInside` y el giro del sensor. El catálogo los marca *conflict* hasta que se verifiquen en vivo (lista de SINT:315-338).

**Archivos fuente:** el plan del editor (`docs/editor-obra/PLAN-EDITOR-OBRA-2026-10-01.md`), los anexos `04-guion-taxonomia.md` y `09-critica.md`, y la auditoría en `…\scratchpad\audit2\`. No escribí ningún archivo ni usé el MCP `unreal`.