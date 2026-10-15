> Anexo 19 · Diseño del lote 5, parte A: "la partitura habla el idioma de Unreal" (2026-10-02, noche). Lo que manda sobre este documento es el [ADR-001](../ADR-001-partitura-y-unreal.md); lo construido y verificado está en el [anexo 18](18-auditoria-app.md), "Estado del lote 5". La parte B es el [anexo 20](20-lote5-diseno-partitura.md).

**Qué es este documento.** Es el **diseño de ingeniería** del lote 5 (parte A) y está **en inglés**, como se escribió: es un documento interno y sus cifras salen de mediciones sobre copias de la partitura. Se conserva tal cual, como registro de lo que se decidió y por qué. Lo que sigue (en español) dice qué cambió entre este diseño y lo que se construyó; el resto no se reescribe.

**Reconciliación decidida al construirlo** (con la parte B):
1. **La referencia de "≠ APK" vive dentro de la partitura** (`baseline` en schema 3, `golden` en schema 2), no en `obra/score/baselines/f0.json`. El §6.7 se cumple por capas (lo que gobierna una perilla, `C3.PARTITURA`; las fases, `C3.TRACE.*`; el resto, la referencia de la partitura) y el paso 7 del §9 (`freeze_f0.mjs`, `baselines/f0.json`) no se construyó. La foto F0 completa quedó como copia congelada para las pruebas (`tools/score/fixtures/f0-score.json`).
2. **Una sola mejora a schema 3**: la del diseño B §10, que no mueve ningún tiempo del usuario típico. Los campos de este documento (`marks`, `bind`) llegan con un paso aparte y opcional, **Bind to Unreal** (`Edits.bindUnreal`, en **Experience ▸ Bind to Unreal…**: no existe un menú "Score"). Reemplaza a `migrate3` del §3.6; `Edits.validate3` del §3.5 quedó dentro de `Edits.validate`.
3. **Las decisiones del dueño marcadas [OWNER] no se tomaron.** Están en la lista del anexo 18 ("Decisiones que necesito de Beltrán") y el documento conserva su recomendación.

**Otras diferencias medidas al construirlo.**
- **Alcance (§0, §3.3).** La barra de estado dice hoy `69 · 71 · 0 · 452` (alcance por perilla · cableado · cue · previs) y no `70 · 82 · 12 · 428`, porque `bind_ids.mjs` pasó 12 voces a "no está en Unreal" (§7.1). Con el contrato del diseño, la misma regla da exactamente 70 · 82 · 428 + 12. Después de **Bind to Unreal** queda `69 · 80 · 18 · 425`: a los 12 sonidos se suman 6 movimientos de Alma que el catálogo del §3.2 marca como cue-capaces y que `BP_Obra_SC` ya hace con su propio grafo (decisión pendiente).
- **Contrato por id (§7).** `contract.json` guarda además `idKeys` (el nombre con que Unreal conoce a cada elemento) y un `excludeKeys` generado; sin ellos no se puede decir "T_INTRO was T_IN" ni volver a correr el generador después de un renombre. `vo.wired` pasa de 68 a 56 (no a 55: `VO_01h` también va a `vo.unused`) y el alcance de la regla de contrato de 174 a 175 elementos.
- **Renombrar (§7.3).** `vo.wired` avisa con un clic (`on.rename: warn`); las entradas `not-in-unreal` no dicen nada; y "Proceed anyway" vale para el verbo con que se aceptó (aceptar un renombre no acepta borrar).
- **`idmap` (§4.3).** Hoy son 185 assets, 1 ambiguo (`VO_12c`) y 0 redirectores (ya se limpiaron). De los sonidos de la partitura: 76 exactos, 19 por alias, 1 ambiguo y 63 sin asset (los 68 del diseño incluían 5 hápticos, que no se cuentan).
- **Perillas (§8.1).** `knobs.json` trae 60 `da:*`, 50 `inst:*`, 4 `lit:*` y 1203 `cdo:*`; los `cdo:*` dejan fuera también las variables de estado (`Z - Estado`…), no solo la categoría `Interno`.
- **Compilador (§5).** Dos rechazos más (`E_MARK_ELEMENT`, `E_NO_MARKS`), la opción `--roles`, y los empates entre marcas de fase son un aviso (`W_MARK_TIE`: hoy `S1.BEGIN`, `S2.BEGIN`, `S4.BEGIN`), no un rechazo.
- **Enlace (§3.4).** `bind` se escribe solo donde hay algo que decir (378 de 592 elementos) y `Edits.bindUnreal` recibe un sexto parámetro (`ctx`, con el motor).
- **Corrida de Unreal (§6).** Suma `C3.UNREADABLE` (información) para un archivo opcional que no se puede leer, y los umbrales suben solos con el ruido de dos pasadas (nunca bajan).
- **Orden de construcción (§9).** Las dos partes se construyeron entrelazadas y no en el orden de la tabla: primero las copias congeladas, las marcas y la corrida de Unreal; después el contrato por id, el motor, el schema 3, las reglas al guardar, la mejora, las ramas, las esperas, lo aceptado, el alcance, el enlace y la importación. El contenido de cada paso no cambió, salvo lo dicho arriba.

**Lo que pide a otros.** Las solicitudes al Director de §10 y las de los pasos posteriores están reunidas en [PEDIDOS-AL-DIRECTOR.md](../PEDIDOS-AL-DIRECTOR.md).

**Los scripts de medición.** Los que cita este documento (`l5a_*.cjs` y compañía, en la carpeta temporal de la sesión de diseño) no están en el repo. Las cifras que importan quedaron fijadas en las pruebas (`tools/score/*_test.mjs`, sobre copias congeladas); para recontarlas, esas pruebas son el camino.

---

# Lote 5 · part A — "the score speaks Unreal's language"

Design document (engineering, internal). Covers audit findings **D1** (binding layer / schema 3 / dry-run compiler), **D10** (contract bound to ids, rename), **D13** (machine-readable knobs + ADR), and the new real data **`obra/unreal/traza.json`** (calibration against a real run). Also touches D4 (the ≠ APK baseline) and D8 (persona-dependent offsets) where the design needs them.

Author: design agent, 2026-10-02 (night). Read-only on the repo; every number below was measured on copies in the scratch dir (scripts listed in Appendix A). Implementation is serial, by later agents, following §9.

Hard constraints honoured everywhere:
- The web editor **never writes `.uasset`** and never applies anything to Unreal. The only path web → Unreal stays **Send to Unreal → `obra/unreal/partitura_propuesta.json`**, applied by the Director on request (backup / smoke / restore, `obra/unreal/LEEME.md`).
- **`score.json` is never rewritten by a tool.** The schema 3 migration is an explicit, undoable in-app operation with a card that shows its effect; the user saves it.
- `web/prototipo-narrativo/` is read-only. `DA_Partitura_Obra` (`obra/unreal/partitura.json`) rules timing; `guion.js` is a visual reference.
- `compile.mjs` is a **dry run**: it reads, reports, refuses; it writes only its manifest, and refuses any output path under `obra/unreal/` or `VR_Test/`.

Items marked **[OWNER]** need Beltrán's decision; items marked **[DIRECTOR]** need the Unreal session (they touch `tools/unreal/*` or need the editor/MCP).

---

## 0. Summary (numbers first)

| Fact (measured 2026-10-02 on copies) | Value |
|---|---|
| Moments (beats) in the score | 73 |
| Beats whose **start is** an Unreal phase mark | **35** |
| Beats that **contain** a phase mark on one of their elements (`V1..V4` at `ENV_SWAP`) | **4** (+3 extra marks inside 3.R3, 5.R6, 9.7) |
| Beats inside a phase span whose offset is set by a **Partitura knob** | 4 (1.2, 1.3, 9.3, 9.5) |
| Beats inside a span addressed by a **sub-mark** Unreal logs but the trace does not carry yet (Hall steps, stage-internal, SHARE branch) | 27 (21 of them are the Hall) |
| Beats that are **preview-only** (inside a span, nothing in Unreal addresses their offset) | 3 (1.R3, 4.R3, 5.R3 "layers") |
| Phase marks in the trace (`traza.json`, speed 1, simulated) | 41 (phase 16, the disclaimer, is absent: the smoke runs without it) |
| Element offsets **invariant across the 4 simulated users** when measured from their governing mark | **446 / 592** (vs ~560/592 absolute starts that depend on the persona, audit D8) |
| Elements that reach Unreal **today** (via a Partitura knob + Send) | **70** |
| Elements Unreal decides by itself (contract: literal / wired / instance knob / not-blocking) | **82** |
| Preview-only elements (incl. 59 haptics), before cue candidates are counted | **386** (428 once the 54 sound candidates that fail the cue rules are added back) |
| Sound elements that would be **cue-ready** (mark + persona-invariant offset + asset in Content, unambiguous, not owned by contract/knob) | 22 elements (13 keys) |
| … of which **no Unreal asset references the sound** (no double fire if a cue player existed) | **12 elements** (FX_GHOSTAPPEAR, FX_SOULDETACH, FX_SOULJOIN) |
| Score sound ids → Content assets (`idmap` scan): exact / alias / ambiguous / missing | 76 / 19 / 1 (VO_12c) / 68 (59 FX placeholders not imported, 5 haptics, SILENCIO, VO_12b, VO_17b, VO_21) |
| Contract entries ↔ elements by today's key regex | 176 pairs, **174 distinct elements** (55 duplicated keys, 302 elements carry a duplicated key) |
| Voices the contract calls "wired" that `BP_Obra_SC` no longer calls (tracker list) | **10** (VO_01d, VO_01h, VO_04b, VO_06a, VO_24, VO_34c, VO_35c, VO_36, VO_36c, VO_36d) |
| Score vs last Unreal run, Hall → end (aligned at the Hall start) | score **995.0 s**, Unreal **1019.7 s** (−24.7 s) |
| Worst stage delta | **Recognizing −94.2 s** (anchor loop A12: 2.R4/2.R5 overlap in the score) |

Decision for D4/C6 (recommended, **[OWNER]** to confirm): the "≠ APK" baseline stops being the prototype golden for everything the trace and the Partitura can measure (phase marks, 70 knob-governed elements); the rest compares against a frozen F0 fixture labelled "vs F0 snapshot", moved out of the live score.

---

## 1. What Unreal really emits: the mark vocabulary v1

### 1.1 Phase enum of `BP_Obra_SC.RunObra` (source: `BP_Obra_SC.md` "Fases de RunObra", `GUIA-DE-DIRECCION.md` §5, confirmed by `traza.json`)

| `fase` | Meaning (director) | Exit | Mark name (v1) | In trace 10-02 |
|---|---|---|---|---|
| 16 | prototype disclaimer (only with `bDisclaimer`) | `HallStart` | `OBRA.DISC` | no (smoke runs without it) |
| 9 | Hall (`HallStart` … `HallLeave`) | `bHallDone` | `HALL.START` | yes (TourT 3.18) |
| 0 | stage K opens: colour veil + stage title; T jumps 5.5 → 9 | `AlmaIn` | `S<K>.OPEN` | yes ×5 |
| 4 | Alma receives (`AlmaSpeak`, AlmaTime = VODur + Alma_TrasVoz) | `AlmaAside` + `CallIntro` | `S<K>.ALMA` | yes ×5 |
| 5 | instructions (`Instr_Dur[K]`, Attracting waits voices ≤ `Instr_EsperaMax`) | `CallBegin` | `S<K>.INTRO` | yes ×5 |
| 6 | the mechanic (`StageBegin`; `Etapa_Tope[K]` asks to close; `Corte_Espera`; `Sim_EtapaMax` if simulated) | `bStageDone` → `CallOutro` + `AlmaOut` | `S<K>.BEGIN` | yes ×5 |
| 7 | stage outro + Alma's congratulation (VO_13/18/23b/29 before the charge) | `ChargeStart(K)` | `S<K>.OUTRO` | yes ×5 |
| 8 | ring charge (`Carga_Dur[K]`; K=4 = final charge) | `ReadCharge` | `S<K>.CHARGE` | yes ×5 |
| 2 | farewell (FlowBye: VO_14/19/25/30) + veil closes (`Velo_CierreDur`) | `AdvanceStage` | `S<K>.BYE` (K<4) | yes ×4 |
| 3 | legacy (`OpenLevel`) | — | none (unused) | no |
| 10 | final: HUD goes, to black | PT ≥ 3 → `HallBack` (0.32 s in the trace) | `FINAL.DARK` | yes |
| 11 | return through the dark to the Hall | `ReturnCheck` | `FINAL.RETURN` | yes |
| 12 | results + SHARE / DON'T SHARE (`FlowShare`) | `ShareExit` | `FINAL.RESULTS` | yes |
| 13 | Hall exit | `ExitCheck` | `FINAL.EXIT` | yes (1.3 s) |
| 14 | constellation + credits (`Creditos_Dur`) | → 15 | `FINAL.CREDITS` | yes |
| 15 | fade (`Fundido_Dur`) then `OpenLevel` (restart) | — | `FINAL.FADE` | yes |
| — | derived: `FINAL.FADE + Fundido_Dur` | — | `OBRA.END` | derived |

Phase numbers are internal (they were renumbered once so the DSL switch is consecutive): **the score and the editor only ever store mark names**, never phase numbers. The phase→name table lives in one pure module (`js/marks.js`, §9 step 2).

### 1.2 Sub-marks (emitted in the log today, not yet in `traza.json`)

| Sub-mark | Log line (source) | Use |
|---|---|---|
| `HALL.<mode>.<step>` (e.g. `HALL.1.6`) | `HALL: modo M paso N` (`BP_HallDirector_SC.HallTickSteps`) | the 25 Hall beats (steps 0-30 of `HallEnterIntro`) |
| `HALL.INTRO` | `OBRA: Hall - HallIntro` (`Hall_IntroA`) | 1.1 |
| `HALL.VOICECUT` | `HALL: voz cortada` | information only |
| `S<K>.REQEND` | `OBRA: se acabo el tiempo de la etapa K - se le pide que cierre…` | 4.coda, 5.close (the close path after `Etapa_Tope`) |
| `S<K>.OUTRO.done` / `.fw` | `OBRA: StageOutro, por fin propio = <bool>` | whether the stage ended by itself |
| `VO.<clip>` | `ALMA: SayClip` (with duration) | voice chain verification (Entering family, PLAN F4) |
| `SHARE.ASK`, `SHARE.YES`, `SHARE.NO` | not emitted yet (`FlowShare` states) **[DIRECTOR]** | 9.5, 9.5b and the D7 branches |

Vocabulary validation (pure, `Marks.isValid`):
```
^(OBRA\.(DISC|END)|HALL\.(START|INTRO)|HALL\.[123]\.\d{1,2}|S[0-4]\.(OPEN|ALMA|INTRO|BEGIN|OUTRO|CHARGE|BYE|REQEND)|FINAL\.(DARK|RETURN|RESULTS|EXIT|CREDITS|FADE)|SHARE\.(ASK|YES|NO))$
```
`S4.BYE` is invalid (the last stage has no farewell: phase 8 K=4 → phase 10). Canonical order (`Marks.rank`): `OBRA.DISC < HALL.START < HALL.1.* (by step) < S0.OPEN < S0.ALMA < S0.INTRO < S0.BEGIN < S0.REQEND < S0.OUTRO < S0.CHARGE < S0.BYE < S1.OPEN … < S4.CHARGE < FINAL.DARK < FINAL.RETURN < FINAL.RESULTS < SHARE.* < FINAL.EXIT < FINAL.CREDITS < FINAL.FADE < OBRA.END`. Annex 11's `GATE.*` and `VO.end` do not exist in Unreal and are not in the vocabulary.

---

## 2. The 73 moments mapped to marks

Relation codes:
- `start` — the beat starts when Unreal enters that phase.
- `el:<KEY>` — the mark falls on that element of the beat (start edge).
- `in` — inside the span of the mark; its offset is set by Partitura knobs (`by`).
- `sub` — inside the span; addressed by a sub-mark Unreal logs (§1.2) or by an instance knob of a stage/Hall BP.
- `preview` — inside the span; nothing in Unreal addresses it.

Counts: **start 35 · el 4 · in 4 · sub 27 · preview 3**. Plus three extra marks that fall on elements of beats already counted: `S2.BEGIN` inside 3.R3 (element **[OWNER]**), `FINAL.DARK` on `FINAL` (5.R6), `FINAL.FADE` on `NEGRO_FIN` (9.7).

| Beat | Title | t (typical) | Mark | Rel | Governed by / note |
|---|---|---|---|---|---|
| 0 | Negro | 0.0 | OBRA.DISC | start | phase 16 (only with bDisclaimer; Aviso_Dur) |
| 1.1 | La niebla azul | 23.0 | HALL.START | start | phase 9 |
| 1.2 | El título | 26.0 | HALL.START | in | Titulo_RevelaIni/Fin, Bajada_RevelaIni/Fin |
| 1.3 | Quietos con el título | 32.5 | HALL.START | in | Titulo_SaleIni (hold = reveal end → leave start) |
| 1.4 | El viaje | 39.5 | HALL.1.1 | sub | Hall step 1 (walk); VO_01a/b/c = steps 2-4 |
| 1.5 | Aparece el portal | 58.5 | HALL.1.5 | sub | step 5 |
| 1.6 | SOUL CHARGER CENTER | 64.5 | HALL.1.5 | sub | BP_HallTitle_SC reads Step |
| 1.7 | El timbre | 67.5 | HALL.1.6 | sub | step 6 |
| 1.8 | Cargar el timbre | 69.0 | HALL.1.6 | sub | step 6 gate (FW_Bell) |
| 1.9 | Se abren las puertas | 76.8 | HALL.1.7 | sub | steps 7-8 |
| 1.10 | Entrar al Hall | 81.3 | HALL.1.9 | sub | step 9 |
| 1.11 | Aparece Alma | 82.8 | HALL.1.10 | sub | steps 10-11 |
| 2.1 | Alma se corre | 107.7 | HALL.1.12 | sub | step 12 |
| 2.2 | El sensor | 110.7 | HALL.1.12 | sub | step 12 gate (FW_Tool) |
| 2.4 | Las cinco almas | 121.2 | HALL.1.14 | sub | step 14 |
| 2.5 | Elegir | 123.4 | HALL.1.14 | sub | step 14 gate (FW_Choose) |
| 2.6 | Tu alma | 138.9 | HALL.1.15 | sub | step 15 |
| 2.7 | Las cinco etapas | 148.9 | HALL.1.16 | sub | step 16 |
| 2.7a … 2.7f | Etapa 1 … Cada etapa carga una luz | 152.0 … 174.5 | HALL.1.17 … HALL.1.22 | sub | one step each (tiles) |
| 2.8 | Nace el HUD | 181.3 | HALL.1.24 | sub | steps 23-25 (tiles down, HUD, VO_07) |
| 2.9 | La puerta de salida | 191.1 | HALL.1.26 | sub | steps 26-30 (bHallDone) |
| 3.1 | Se enciende el primer mundo | 200.3 | S0.OPEN | start | phase 0 |
| 1.R2 | Entering: Alma | 206.0 | S0.ALMA | start | phase 4 |
| 1.R3 | R3 Capas | 214.1 | S0.ALMA | preview | stage layers: the stage BP decides (StageIntro), no knob |
| 1.R4 | Herramienta y demostración | 218.1 | S0.INTRO | start | phase 5 |
| 1.R5a | Exploración libre | 225.0 | S0.BEGIN | start | phase 6 |
| 1.R5b | El pacer | 245.1 | S0.BEGIN | sub | Entering_Stage ExploreTime/CountTime/Cycles (instance) · BREATH.* log |
| 1.R5x | Retirada | 331.0 | S0.OUTRO | start | phase 7 |
| 1.R6 | La carga | 333.0 | S0.CHARGE | start | phase 8 |
| 1.R8 | Despedida | 343.4 | S0.BYE | start | phase 2 |
| V1 | Velo 1→2 | 353.7 | S1.OPEN | el:ENV_SWAP | its VEIL_CLOSE is S0.BYE's tail (Velo_CierreDur) |
| 2.R2 | Recognizing: Alma | 363.7 | S1.ALMA | start | phase 4 |
| 2.R4 | Herramienta y demostración | 373.1 | S1.INTRO | start | phase 5 |
| 2.R5 | Mecánica viva | 373.1 | S1.BEGIN | start | phase 6 — today starts **with** 2.R4 (anchor loop A12) |
| 2.R5x / 2.R6 / 2.R8 | | 415.3 / 417.3 / 427.7 | S1.OUTRO / S1.CHARGE / S1.BYE | start | |
| V2 | Velo 2→3 | 437.5 | S2.OPEN | el:ENV_SWAP | |
| 3.R2 | Loving: Alma | 447.5 | S2.ALMA | start | |
| 3.R3 | Sin R4: la calma | 455.2 | S2.INTRO | start | **[OWNER]** which element is S2.BEGIN (phase 6) |
| 3.R5 | La espiral | 511.7 | S2.BEGIN | sub | LovingCell StageDuration 60 (instance) |
| 3.R5x / 3.R6 / 3.R8 | | 519.0 / 521.0 / 531.5 | S2.OUTRO / S2.CHARGE / S2.BYE | start | |
| V3 | Velo 3→4 | 542.6 | S3.OPEN | el:ENV_SWAP | |
| 4.R2 | Attracting: Alma | 552.6 | S3.ALMA | start | |
| 4.R3 | R3 Capas | 559.4 | S3.ALMA | preview | stage layers |
| 4.R4 | Herramienta y demostración | 563.0 | S3.INTRO | start | Instr_Dur[3] + Instr_EsperaMax |
| 4.R5 | Mecánica viva | 578.5 | S3.BEGIN | start | |
| 4.coda | La coda | 673.5 | S3.BEGIN | sub | close path after `S3.REQEND` (Etapa_Tope[3]); VO_28 = CueAttract Phase ≥ 3 |
| 4.R5x / 4.R6 / 4.R8 | | 684.2 / 686.2 / 696.7 | S3.OUTRO / S3.CHARGE / S3.BYE | start | |
| V4 | Velo 4→5 | 707.0 | S4.OPEN | el:ENV_SWAP | |
| 5.R2 | Surrounding: Alma | 717.0 | S4.ALMA | start | |
| 5.R3 | R3 Capas | 728.0 | S4.ALMA | preview | stage layers |
| 5.R4 | Herramienta y demostración | 731.0 | S4.INTRO | start | Instr_Dur[4] 0.6 |
| 5.R5 | Mecánica viva | 731.0 | S4.BEGIN | start | today starts **with** 5.R4 (anchor loop A12) |
| 5.close | Cierre del dibujo | 806.0 | S4.BEGIN | sub | presentation after `S4.REQEND` (Etapa_Tope[4]) |
| 5.release | Se van las herramientas | 811.5 | S4.OUTRO | start | |
| 5.R6 | La última carga | 813.5 | S4.CHARGE | start | + `FINAL.DARK` = el:FINAL |
| 9.1b | El alma sale nadando | 825.5 | FINAL.RETURN | start | phase 11 |
| 9.3 | El portal otra vez | 825.8 | FINAL.RETURN | in | Regreso_VeloIni/Fin, Regreso_PezA |
| 9.4 | Los resultados | 854.8 | FINAL.RESULTS | start | phase 12 |
| 9.5 | La invitación a compartir | 902.2 | FINAL.RESULTS | in | Res_* (FlowShare st2-st5); future `SHARE.ASK` |
| 9.5b | Tu respuesta | 926.3 | FINAL.RESULTS | sub | `SHARE.YES` / `SHARE.NO` (D7 branches; not emitted) |
| 9.6 | Salida del Hall | 934.5 | FINAL.EXIT | start | phase 13 |
| 9.7 | Constelación y créditos | 945.0 | FINAL.CREDITS | start | + `FINAL.FADE` = el:NEGRO_FIN |

The full machine table (beat key → mark, rel, note) was produced by `l5a_marks.cjs` and is the content of the seed file of §3.4 (`l5a_marktable.md` in the scratch dir).

How "preview-only" is decided: a beat is preview when it sits inside a span and its offset from the span's mark is decided by Unreal code the editor cannot address (no Partitura knob, no instance knob in `roles.json`, no sub-mark). Elements in such beats can still be **knob** or **wired** by their own contract (e.g. a VO inside), but their time inside the beat never reaches Unreal.

Ambiguities that need the owner **[OWNER]**:
1. **S2.BEGIN** (Loving mechanic start): inside 3.R3 ("la calma": CELL_IN, VO_21, VO_22, VO_23 …). In Unreal: phase 5 lasts `Instr_Dur[2]` 6 s after Alma goes aside, then 60 s of mechanic. Candidate: `CELL_IN` start (+0 s) or `VO_22` start. Recommendation: `el:CELL_IN` would make INTRO 0 s long in the score; better split 3.R3 into "3.R3 intro" (6 s) + "3.R3 calm" — that is an edit the owner makes, not the migration.
2. R3 "layers" (1.R3, 4.R3, 5.R3): preview (recommended) or `sub` of `S<K>.INTRO` (if the layers are the first thing `StageIntro` shows).
3. V<K>: the mark is at `ENV_SWAP` (binding origin `phase0` already says so). The `VEIL_CLOSE` part of V<K> belongs to the previous stage's BYE; the score keeps it in V<K> (fine: only the mark position matters).

---

## 3. Schema 3

### 3.1 What changes (and what deliberately does not)

Schema 3 adds **two fields** to the score. Everything else stays (acts, beats, groups, lanes, elements, markers, notes, accepted, propuestas…).

```jsonc
// beats[id]
"marks": [                                   // optional; [] or absent = "not bound yet" (compile refuses its cues)
  { "name": "S1.OPEN", "rel": "el", "el": "el_q9tu53khop", "edge": "start" },   // the mark is that element's edge
  { "name": "S0.ALMA", "rel": "start" },                                        // the beat starts at the mark
  { "name": "HALL.START", "rel": "in", "by": ["Titulo_SaleIni"] },              // inside; offset = Partitura knobs
  { "name": "HALL.1.6", "rel": "sub", "by": ["FW_Bell"] },                      // inside; sub-mark / instance knob
  { "name": "S3.ALMA", "rel": "preview", "why": "stage layers: the stage BP decides" }
]
// rules: at most one entry with rel start|in|sub|preview per beat (the beat's own relation, always marks[0]);
//        any number of rel 'el' entries (extra marks that fall on its elements: 5.R6 → FINAL.DARK at FINAL).

// elements[id]
"bind": {
  "action": "vo_alma",          // catalog §3.2, or null (= no Unreal action: preview)
  "target": "role:Alma",        // "role:<roles.json key>" | "tag:<actor tag>" | null
  "asset":  "VO_10",            // idmap key (obra/unreal/idmap.json), or null; NEVER derived from `key` after migration
  "branch": null                // reserved for D7 (part B): { "on": "share", "value": true|false }
}
```

Not in the score, by design:
- **Contract membership** (D10) and **knob ↔ element** links stay in the web-owned catalogs (`contract.json` `ids`, `partitura_binding.json` `ids`, §7). Reason: those catalogs are refreshed by harvest/tools, and a tool must never rewrite `score.json`. The score only says *who the element is in Unreal* (action, target, asset); the catalogs say *what Unreal does with it*.
- **`reach`**: computed on every `compute()`, never stored (same principle as "≠ APK", audit B6/C6).
- **Phase numbers**: never stored.
- `legacy.uid` stays as provenance (for D2 re-import matching, part B). It is not used for binding.

### 3.2 Action catalog v1 (annex 11 §5 MVP, named)

| action | Unreal counterpart | Needs | Cue-capable (F4) |
|---|---|---|---|
| `vo_alma` | `ObraSay` / `Alma.SayClip` (interruptible, Alma speaks) | asset (VO), target `role:Alma` | yes |
| `vo_2d` | `ObraVO2D` / `PlaySound2D` (VO_33, VO_35a … per tracker) | asset | yes |
| `sound` | `PlaySound2D` | asset | yes |
| `sound_at` | `PlaySoundAtLocation` (FX_SHAREAPPEAR at the results frame, FX_SOULVANISH at RingSpot…) | asset, target | yes |
| `appear` / `disappear` | the role's own verb (Alma `AppearAt`/`Disappear`, Appear component) | target | yes (roles with an API only) |
| `ghost` | `BP_GhostPlayer_SC` take `DA_Ghost_*` | asset (DA_Ghost_X), target | yes |
| `ambience` | `AmbPick` literal in `BP_Obra_SC` | asset | **no** (read: Unreal decides) |
| `title` | stage title (`Etapa_Titulo*` knobs) | — | no (read; knob channel) |
| `veil` | `M_TourVeil_SC` (`Etapa_VeloAbre*`, `Velo_CierreDur`) | — | no (read; knob channel) |
| `wait` | Hall `FW_*`, SHARE `Res_Cortafuegos`, stage `Etapa_Tope` | — | no (read) |
| `null` | nothing in Unreal (most `object`/`world`/`path`/`interaction`, all haptics) | — | no |

### 3.3 Reach (computed, `js/reach.js`, pure)

```
Reach.of(el, ctx) -> { reach: 'knob'|'wired'|'cue'|'preview', why: string, state?: 'no-player' }
ctx = { score, schedT, scheds (4 personas, lazily), contractIdx, gov, idmap, markTimes }
```
First rule that matches wins:
1. `el.isNew` → `preview` ("made in the editor: Unreal does not know it").
2. contract entry (by id, §7) of kind `not-in-unreal` → `preview` (its `msg`).
3. governed by a Partitura knob (`gov[id]`) or contract kind `partitura` → **`knob`** ("reaches Unreal when you send <knob>").
4. contract kind `literal` | `wired` | `knob` | `not-blocking` → **`wired`** ("Unreal decides: <owner › graph>").
5. schema 3 and all of: `bind.action` cue-capable; the beat's `marks[0].rel` ∈ {start, el} (or the element follows an `el` mark of its beat); offset from the governing mark identical for fast/typical/slow/idle (|spread| < 1/72 s); `bind.asset` resolved in idmap, unambiguous; the asset is **not referenced by any Unreal asset** (idmap `referencedBy` empty; otherwise `wired: "called by <BP>"` to avoid double fire); target resolved when needed → **`cue`** with `state: 'no-player'` while `BP_ScorePlayer_SC` does not exist.
6. otherwise `preview` with the first failing reason (`"beat not bound"`, `"depends on the user (after a wait)"`, `"no Unreal action"`, `"asset not in Content"`, `"asset ambiguous: …"`, `"haptics are not in Unreal"`).

Status bar (replaces "0 of N reach Unreal"): `70 reach Unreal (timing) · 82 wired · 12 cue-ready · 428 preview` (numbers measured; cue-ready shows only on schema 3).
Inspector, "Unreal" section: one line per element with reach + why, and for `cue` the compiled `{mark, offset, action, target, asset}`.

### 3.4 Seeding (what the migration fills, from what)

| Field | Source | Rule | Measured |
|---|---|---|---|
| `beats[].marks` | `obra/score/seed/marks-v1.json` (new, versioned, **keyed by beat id**, generated once from the table of §2 and reviewed by the owner) | copied verbatim; `el` keys resolved to element ids at generation time | 73 beats: 35 start, 4 el, 4 in, 27 sub, 3 preview; 3 extra `el` marks |
| `bind.asset` | element `sound` (or `key` for vo) → `idmap.aliases` → `idmap.assets` | only if resolved and unambiguous; else null | 99 exact + 29 alias elements of 320 with a sound |
| `bind.action` | type/group + contract + tracker | vo → `vo_alma` if wired and Alma speaks it (stage welcome/farewell, Hall `HallSay`), `vo_2d` for VO_33, VO_35a/b, VO_37 (tracker: "Las VO siguen en 2D"; **[DIRECTOR]** confirm list); sound → `sound`, or `sound_at` for FX_SHAREAPPEAR, FX_SHARESELECT, FX_SOULVANISH, FX_RINGVANISH (tracker trap list); ambience → `ambience`; T_IN/T_OUT/T1_* → `title`; VEIL_*/VEIL1_IN → `veil`; G_* → `wait`; GHOST_* → `ghost`; ALMA_IN/ALMA_BACK → `appear`, ALMA_OUT/ALMA_GONE → `disappear`; haptics and the rest → null | — |
| `bind.target` | `roles.json` roles `match` regex (13 roles, 88 elements) | `role:<RoleName>`; Alma VO → `role:Alma` | 88 + Alma voices |
| `bind.branch` | left null (D7 is part B; 16 elements carry the broken `when`) | — | — |

### 3.5 Validation (pure, shared by app, server and compile)

`Edits.validate` already guards schema 2 references. Add `Edits.validate3(score, vocab)` (pure, in `edits.js`):
- `marks` is an array; each `name` passes `Marks.isValid`; `rel` ∈ {start, el, in, sub, preview}; `el` refers to an element **of that beat**; `edge` ∈ {start, end}.
- every **phase** mark name (not `HALL.1.*`, not `SHARE.*`) appears **at most once** in the score.
- `bind.action` ∈ catalog or null; `bind.asset` is a string or null (existence in idmap is *not* a validation error, only a reach reason); `bind.target` matches `^(role|tag):.+$` or null.
Server (`check_score`): accept `schema` 2 or 3; for 3, the same shape checks (no idmap, no vocabulary order: the server stays dumb and fast).

### 3.6 Migration as an in-app operation

- Verb: `Act.upgradeSchema3()` (menu **Score ▸ Bind to Unreal (schema 3)…**). Pure work in `Edits.migrate3(score, seed, idmap, contract, roles) -> { next, report }`.
- Card (`UI.chooseCard`), English, sentence case:
  - title "Bind the score to Unreal"; body "Every moment gets the Unreal mark it corresponds to and every sound its Unreal asset. No time changes."; lines: "73 moments: 39 on an Unreal mark, 31 inside one, 3 preview only" · "128 sounds linked to Unreal assets, 1 ambiguous (VO_12c), 191 not in Unreal" · "the F0 snapshot moves out of the score (the APK comparison now uses the Unreal run)"; button "Bind" / "Cancel".
- `commit('Bind to Unreal', { type: 'migrate' }, n => Object.assign(n, migrate3(...).next))`; `migrate` is **not QUIET**, but `Integrity.effect` must report **0 changed, 0 shifted**: the migration refuses itself (toast, nothing applied) if any element time changes (assertion inside `migrate3`, re-checked by resolve on `next`).
- It removes `score.golden` (moved to `obra/score/baselines/f0.json`, created beforehand by step 7 from the current file; the card says so). Undo restores schema 2 byte-for-byte (JSON snapshot undo already does).
- Saved by the user with Ctrl+S, through the normal PUT with base rev/hash. The server accepts schema 3 after step 6.
- Idempotent: running it on a schema 3 score is disabled (menu greyed, "Already bound").

---

## 4. `obra/unreal/idmap.json`

### 4.1 Generator `tools/score/idmap.mjs` (node, no Unreal, read-only on `VR_Test/`)

```
node tools/score/idmap.mjs [--deps <deps.json>] [--out obra/unreal/idmap.json] [--check]
```
- Scans `VR_Test/Content` (mount `/Game`) and `VR_Test/Plugins/<P>/Content` (mount `/<P>`), skipping `_Deprecated`, `Developers`, `Collections`. Only files under an `Audio/` folder, plus `**/Ghost/Data/DA_Ghost_*` (for `ghost`).
- Class sniffing on the bytes (latin1): `ObjectRedirector` → recorded in `redirectors`, not an asset; `SoundWave` → SoundWave; `SoundCue` without SoundWave → SoundCue; `SoundAttenuation` and others skipped; `DA_Ghost_*` → GhostTake.
- Duplicated asset names in two live folders → `ambiguous[name] = [records]` and removed from `assets` (never guess).
- `referencedBy`: from `deps.json` produced by **`python tools/unreal/deps.py`** (existing Director tool, run with cwd = scratch; it already handles the FName `_<number>` split). Do **not** reimplement it (rule "no reimplementar los scripts de la skill"). `deps.py` covers `/Game` only: plugin sounds get `referencedBy: null` ("unknown"), which reach treats as referenced (safe side). **[DIRECTOR]** optional: extend `deps.py` to plugin mounts.
  - Measured pitfall: a naive byte search misses every package whose name ends in `_<digits>` (VO_10, VO_13…: 21 VOs appeared "unreferenced"). That is exactly what `deps.py` fixes.
- `--check`: exit 1 if the existing file differs from a fresh scan (for CI / the smoke checklist).
- Writes only `--out` (default `obra/unreal/idmap.json`, a web-owned file: add it to the LEEME table **[DIRECTOR]** ack).

### 4.2 Shape

```jsonc
{
  "generated": "2026-10-02T21:10:00Z",
  "source": "fs-scan",                       // a later "asset-registry" variant can come from the Director (MCP)
  "scanned": 185,
  "assets": {
    "VO_10":   { "path": "/Game/SoulCharger/Obra/Audio/VO_10.VO_10", "cls": "SoundWave", "bytes": 454475, "sha1": "c57d96942c05", "wav": true, "referencedBy": ["/Game/SoulCharger/Obra/Blueprints/BP_Obra_SC"] },
    "Charge1": { "path": "/SC_Base/Audio/Charge1.Charge1", "cls": "SoundWave", "bytes": 1348654, "sha1": "f86e96e2ddd2", "wav": true, "referencedBy": null }
  },
  "ambiguous": { "VO_12c": [ { "path": "/Game/SoulCharger/Mechanics/Breath/Audio/VO_12c.VO_12c", "...": "" }, { "path": "/Game/SoulCharger/Obra/Audio/VO_12c.VO_12c", "...": "" } ] },
  "redirectors": [ "/Game/SoulCharger/Mechanics/Pacer/Audio/SND_PacerPadExhale.SND_PacerPadExhale", "…" ],
  "aliasesFrom": "obra/unreal/idmap_aliases.json",
  "aliasesSha": "…"
}
```
`obra/unreal/idmap_aliases.json` (web-owned, hand-kept, reviewed by the Director): score sound id → asset name.
```json
{ "note": "score sound id → Unreal asset name; reviewed by the director",
  "aliases": { "FX_BELLRING": "Bell", "FX_WALK": "Pasos", "FX_DOOROPEN": "DoorOpen", "FX_PROTOSELECT": "ProtoSelect",
    "FX_CHARGE_1": "Charge1", "FX_CHARGE_2": "Charge1", "FX_CHARGE_3": "Charge1", "FX_CHARGE_4": "Charge1", "FX_CHARGEFINAL": "ChargeFinal",
    "AMB_01": "Ambient_Clip_1_-_Intro", "AMB_02": "Ambient_Clip_2_-_Start", "AMB_03": "Ambient_Clip_3_-_Hall", "AMB_04": "Ambient_Clip_4_-_Breath",
    "AMB_05": "Ambient_Clip_5_-_Heart", "AMB_06": "Ambient_Clip_6_-_Mind", "AMB_07": "Ambient_Clip_7_-_Surrounding", "AMB_08": "Ambient_Clip_8_-_Salida",
    "AMB_09": "Ambient_Clip_9_-_Credits", "PAD_M1": "PadM1" } }
```

### 4.3 Measured (scan of 2026-10-02 ~21:00, 0.5 s)

- 185 audio `.uasset` scanned → 175 assets, 7 redirectors (old `Mechanics/Pacer/Audio`), 1 ambiguous name (**VO_12c**: `Mechanics/Breath/Audio` and `Obra/Audio`, different bytes).
- Score: 164 distinct sound ids → **76 exact, 19 via alias, 1 ambiguous, 68 missing**. Missing = 59 `FX_*` placeholders that exist only in the prototype, 5 `HAP_*`, `SILENCIO` (an action, not an asset: `ambience` with `asset: null` = stop), and **VO_12b, VO_17b, VO_21** (in the score and in the contract as "wired", but no asset in Content) **[DIRECTOR]**: are they VO_12f1/VO_12f2 (Breath) or dropped?
- Unreal VOs absent from the score: **VO_35a** (Hall/Audio, played by `ShareExit`), VO_12f1, VO_12f2.
- The Content tree is moving (Breath assets were being moved into `Plugins/SC_Breath` during this measurement). The idmap is a snapshot: compile reports `idmap.generated` and the app shows its age; `--check` detects staleness.

---

## 5. `tools/score/compile.mjs` — dry-run compiler

### 5.1 CLI

```
node tools/score/compile.mjs [--score obra/score/score.json] [--idmap obra/unreal/idmap.json]
  [--contract obra/unreal/contract.json] [--def obra/unreal/partitura_def.json] [--live obra/unreal/partitura.json]
  [--binding obra/unreal/partitura_binding.json] [--trace obra/unreal/traza.json] [--seed obra/score/seed/marks-v1.json]
  [--out <file>|-]   (default "-": stdout)
exit 0 = compiled, nothing refused · 2 = compiled with refusals (manifest still printed) · 1 = bad input / unsafe --out
```
Safety: `--out` is resolved and **refused** (exit 1) if it is under `VR_Test/`, under `obra/unreal/`, or equals `obra/score/score.json`. It never writes anything else. It never imports anything from `tools/unreal/`. Pure core in `web/editor-obra/app/js/compile.js` (UMD, so the app can show the same manifest), CLI wrapper in `tools/score/compile.mjs`.

### 5.2 Algorithm

1. **Load + validate**: `Edits.validate` (schema 2/3 shape), `Edits.validate3` for schema 3. Input error → exit 1.
2. **Resolve** `Engine.resolve(score, typical)` and the 4 personas. **Refuse** (`E_CYCLE`, one item per beat in `cycles`) and (`E_DANGLING`, per `dangling`). Today: refuses `2.R4` and `5.R4` (A12: `2.R4.end ← BIO.end ← 2.R5x.start ← 2.R5 ← 2.R4.end`). No `--allow-cycles` switch: the owner fixes the anchors (decision 1 of annex 18, already offered in Problems ▸ "Fix the loop…").
3. **Marks**: schema 3 → `beats[].marks`; schema 2 → the seed file (so the dry run is useful before the migration; manifest says `"marksFrom": "seed"`). For each mark with rel `start` / `el`: `t(mark)` = beat start / element edge.
   - `E_MARK_UNKNOWN` (name fails the vocabulary), `E_MARK_DUP` (a phase mark twice), `E_MARK_ORDER` (phase marks not monotonic in score time with `Marks.rank`; ties allowed only between `INTRO`/`BEGIN` of K4 (`Instr_Dur[4]` 0.6) when the owner accepts it — see W below), `W_MARK_MISSING` (a vocabulary phase mark the score never places; `OBRA.DISC` is exempt when `bDisclaimer` off).
4. **Per element**: governing mark = the beat's own `start`/`el` mark, or the latest `start`/`el` mark at or before the element's start in act order (for `in`/`sub`/`preview` beats). `offset = t(el.start) − t(mark)` (typical). Persona spread = max−min of that offset over the 4 personas.
5. **Classify** with `Reach.of` (§3.3). The compiler and the app share the same function.
6. **Assets**: for `cue`-eligible elements, `E_ASSET_AMBIGUOUS` (refusal: lists the candidate paths), `asset not in Content` → preview (not a refusal: it is honest previs).
7. **Knob channel**: `Partitura.drift(score, schedT, def, live, binding)` rows with `diff ≠ 0` → `knobs[]` (what Send to Unreal could carry; compile never writes the proposal file).
8. **Trace** (optional): attach `Calib.compare` (§6) summary.
9. **Emit** the manifest, deterministic order (by typical start, then id), so two runs diff cleanly.

### 5.3 Manifest shape

```jsonc
{
  "compiler": "compile.mjs 1",
  "generated": "2026-10-02T21:30:00Z",
  "dryRun": true,
  "inputs": {
    "score":    { "schema": 2, "rev": 2, "sha12": "…", "marksFrom": "seed" },
    "idmap":    { "generated": "…", "sha12": "…" },
    "contract": { "sha12": "…" },
    "partitura":{ "hash": "54ef5a851e4b", "exported": "2026-10-02T18:06:10" },
    "trace":    { "generated": "20261002-185938", "speed": 1, "sim": null }
  },
  "ok": false,
  "refused": [
    { "code": "E_CYCLE", "id": "bt_1biqo7b1ib", "key": "2.R4", "msg": "2.R4 has an anchor loop: its end depends on 2.R5x, which follows it." },
    { "code": "E_CYCLE", "id": "bt_1wpzo78f07", "key": "5.R4", "msg": "…" }
  ],
  "summary": { "elements": 592, "reach": { "knob": 70, "wired": 82, "cue": 0, "cueReady": 12, "preview": 428 } },
  "marks":   [ { "name": "S0.OPEN", "beat": "bt_…", "key": "3.1", "t": 200.3 } ],
  "knobs":   [ { "knob": "Etapa_VeloAbreIni", "stage": 1, "score": 1.5, "live": 1, "diff": 0.5, "els": ["el_…"] } ],
  "cues":    [ { "id": "el_…", "key": "FX_SOULDETACH", "mark": "S0.CHARGE", "offset": 0, "action": "sound", "target": null,
                 "asset": "FX_SOULDETACH", "path": "/Game/SoulCharger/Obra/Audio/Placeholder/FX_SOULDETACH.FX_SOULDETACH", "state": "no-player" } ],
  "wired":   [ { "id": "el_…", "key": "VO_10", "contract": "vo.wired", "owner": "BP_Obra_SC · …", "why": "Unreal calls it by asset path" } ],
  "preview": [ { "id": "el_…", "key": "HAP_PULSE_SOFT", "why": "haptics are not in Unreal" } ],
  "trace":   { "offset": 19.82, "sections": [ { "name": "Recognizing", "score": 83.8, "unreal": 178.0, "d": -94.2 } ] }
}
```
`cues` is listed even though nothing consumes it: the state `no-player` says why. When `BP_ScorePlayer_SC` exists (F4, Director), the ADR (§8) decides how a manifest becomes Unreal data (DataAsset written by the Director's MCP job, on request) — still never by the web.

### 5.4 Tests (`tools/score/compile_test.mjs`)

- On the real score (read-only): exit code 2; `refused` contains exactly `E_CYCLE` for 2.R4 and 5.R4; summary reach knob 70 / wired 82.
- On a fixture copy with the two anchors fixed (fixture built inside the test in memory): `refused` empty, cueReady 12 (expected from the schema 2 projection; pin the measured value).
- `E_MARK_DUP`, `E_MARK_ORDER`, `E_MARK_UNKNOWN`, `E_ASSET_AMBIGUOUS` each from a minimal in-memory score.
- `--out VR_Test/x.json` and `--out obra/unreal/x.json` → exit 1, no file created.
- Determinism: two runs → identical bytes except `generated`.

---

## 6. Trace calibration (score vs the real Unreal run)

### 6.1 Data and alignment

`traza.json` (2026-10-02 18:59, `smoke_obra.py --speed 1 --traza`): 41 phase changes with `reloj_obra_s` (= `TourT`, real seconds since boot). The smoke runs **without disclaimer** and **simulated** (`-ObraSmoke`: fake signals; Attracting and Surrounding are asked to close at `Sim_EtapaMax` 90 s). Alignment: `HALL.START` (score beat 1.1 at 23.00 s, trace 3.18 s) → offset **19.82 s**. Score mark times from the §2 table (typical user); `S<K>.INTRO` measured at `ALMA_MOVE` (Alma goes aside = `AlmaAside` + `CallIntro`).

### 6.2 Measured — per segment (mark → next mark)

| Mark | score t | trace t (+19.82) | seg score | seg Unreal | Δ seg |
|---|---|---|---|---|---|
| HALL.START | 23.0 | 23.0 | 177.3 | 176.3 | +1.0 |
| S0.OPEN | 200.3 | 199.3 | 5.7 | 5.5 | +0.2 |
| S0.ALMA | 206.0 | 204.8 | 10.1 | 11.5 | −1.4 |
| S0.INTRO | 216.1 | 216.3 | 8.9 | 8.5 | +0.4 |
| S0.BEGIN | 225.0 | 224.8 | 106.0 | 89.1 | **+16.9** |
| S0.OUTRO | 331.0 | 313.9 | 2.0 | 6.8 | **−4.8** |
| S0.CHARGE | 333.0 | 320.6 | 10.4 | 10.8 | −0.3 |
| S0.BYE | 343.4 | 331.4 | 14.3 | 9.7 | **+4.6** |
| S1.OPEN | 357.7 | 341.1 | 6.0 | 5.5 | +0.5 |
| S1.ALMA | 363.7 | 346.6 | 11.3 | 6.7 | **+4.7** |
| S1.INTRO | 375.1 | 353.3 | −2.0 | 6.0 | **−8.0** |
| S1.BEGIN | 373.1 | 359.3 | 42.2 | 134.5 | **−92.3** |
| S1.OUTRO | 415.3 | 493.8 | 2.0 | 5.8 | −3.8 |
| S1.CHARGE | 417.3 | 499.5 | 10.4 | 10.8 | −0.3 |
| S1.BYE | 427.7 | 510.3 | 13.8 | 8.8 | +5.0 |
| S2.OPEN | 441.5 | 519.1 | 6.0 | 5.5 | +0.5 |
| S2.ALMA | 447.5 | 524.6 | 9.8 | 10.8 | −1.0 |
| S2.INTRO | 457.3 | 535.4 | −2.1 | 6.0 | −8.1 |
| S2.BEGIN | 455.2 | 541.4 | 63.8 | 60.0 | +3.8 |
| S2.OUTRO | 519.0 | 601.4 | 2.0 | 6.0 | −4.0 |
| S2.CHARGE | 521.0 | 607.4 | 10.4 | 10.8 | −0.3 |
| S2.BYE | 531.5 | 618.2 | 15.1 | 9.2 | +6.0 |
| S3.OPEN | 546.6 | 627.4 | 6.0 | 5.5 | +0.5 |
| S3.ALMA | 552.6 | 632.9 | 8.8 | 7.3 | +1.5 |
| S3.INTRO | 561.4 | 640.1 | 17.1 | 7.3 | **+9.8** |
| S3.BEGIN | 578.5 | 647.5 | 105.7 | 90.0 (sim) | **+15.7** |
| S3.OUTRO | 684.2 | 737.5 | 2.0 | 3.2 | −1.2 |
| S3.CHARGE | 686.2 | 740.7 | 10.4 | 10.8 | −0.3 |
| S3.BYE | 696.7 | 751.5 | 14.3 | 6.8 | **+7.5** |
| S4.OPEN | 711.0 | 758.3 | 6.0 | 5.5 | +0.5 |
| S4.ALMA | 717.0 | 763.8 | 13.0 | 13.3 | −0.3 |
| S4.INTRO | 730.0 | 777.1 | 1.0 | 0.6 | +0.4 |
| S4.BEGIN | 731.0 | 777.7 | 80.5 | 90.0 (sim) | **−9.5** |
| S4.OUTRO | 811.5 | 867.7 | 2.0 | 2.5 | −0.5 |
| S4.CHARGE | 813.5 | 870.2 | 8.5 | 11.6 | −3.1 |
| FINAL.DARK | 822.0 | 881.8 | 3.5 | 0.3 | +3.2 |
| FINAL.RETURN | 825.5 | 882.1 | 29.3 | 15.1 | **+14.2** |
| FINAL.RESULTS | 854.8 | 897.2 | 79.7 | 80.7 | −1.0 |
| FINAL.EXIT | 934.5 | 977.9 | 10.5 | 1.3 | **+9.2** |
| FINAL.CREDITS | 945.0 | 979.2 | 68.0 | 60.0 | **+8.0** |
| FINAL.FADE | 1013.0 | 1039.2 | 5.0 | 3.5 | +1.5 |

### 6.3 Measured — per section

| Section | from → to | score | Unreal run | Δ |
|---|---|---|---|---|
| Hall | HALL.START → S0.OPEN | 177.3 | 176.3 | +1.0 |
| Entering | S0.OPEN → S1.OPEN | 157.4 | 141.8 | **+15.6** |
| Recognizing | S1.OPEN → S2.OPEN | 83.8 | 178.0 | **−94.2** |
| Loving | S2.OPEN → S3.OPEN | 105.1 | 108.3 | −3.1 |
| Attracting | S3.OPEN → S4.OPEN | 164.3 | 130.9 | **+33.4** (sim cap) |
| Surrounding | S4.OPEN → FINAL.DARK | 111.0 | 123.5 | **−12.5** (sim cap) |
| Final | FINAL.DARK → OBRA.END | 196.0 | 160.9 | **+35.1** |
| **Hall → end** | | **995.0** | **1019.7** | **−24.7** |

With the idle persona the Hall would be +37.6 s: the smoke's Hall behaves like the **typical** user (1.0 s apart), so typical is the right comparison persona.

### 6.4 What the deltas mean (causes, so the editor can say them)

- **Knob-driven segments agree** within 0.5 s: OPEN is +0.5 in every stage K ≥ 1 (score 6.0 vs `Alma_Entra` 5.5: the same drift C3.PARTITURA already reports), CHARGE is −0.3 in K 0-3. The trace independently confirms the DA values and the binding. This is the calibration's control positive.
- **Structural difference, every stage**: OUTRO is 2.0 s in the score but 3.2-6.8 s in Unreal and BYE is 4.6-7.5 s longer in the score. Unreal plays Alma's congratulation (VO_13/18/23b/29) in the **outro, before the charge** (`AlmaCharge`, `OutroTime ≥ VODur + 0.6`); the score has it in R8, after the charge. Also the score's veil close is 4.0 s vs `Velo_CierreDur` 2.5.
- **Recognizing −94.2 s** is the anchor loop (A12): 2.R4 and 2.R5 start together, so the score's mechanic is 42.2 s vs 134.5 s in Unreal (heart stage ended by itself). Same loop on 5.R4/5.R5 (Surrounding).
- **Entering BEGIN +16.9 s**: score exploration 20 s + pacer 86 s; Unreal's breath stage closes by its own end at 89 s.
- **Attracting INTRO +9.8**: score 17.1 s vs `Instr_Dur[3]` 6 + voice wait → 7.3 s. **BEGIN +15.7 / Surrounding −9.5** are simulated (`Sim_EtapaMax` 90): not comparable to a real user; the editor must label them.
- **Final**: RETURN +14.2 (score 29.3 vs 15.1), EXIT +9.2 (10.5 vs 1.3: Unreal leaves the Hall exit almost at once in the simulated run), CREDITS +8.0 (68 vs `Creditos_Dur` 60), FADE +1.5 (5.0 vs `Fundido_Dur` 3.5).

### 6.5 Thresholds (proposal, **[OWNER]**)

- Section (stage) warn when |Δ| > **3 s** → today: Entering, Recognizing, Loving (−3.1, borderline), Attracting, Surrounding, Final; Hall passes.
- Segment info when |Δ| > **1 s** → today 25 of 41 segments.
- Noise is unknown with one run (rule "una línea de base son DOS pasadas"): **[DIRECTOR]** run `smoke_obra.py --speed 1 --traza` twice; set X_seg = max(1 s, 3σ) and X_stage = max(3 s, 3σ) from the two runs. Phase changes are logged once per frame (TourT), so a single segment carries ≤ 1 frame of quantisation (≈17-33 ms in `-game -nohmd`).
- Segments that end on `BEGIN` in a **simulated** trace are never warned (only shown hatched with "simulated: 90 s cap").

### 6.6 How the editor shows it

New pure module `js/calib.js`:
```
Calib.compare(scoreMarks, traceMarks, { align: 'HALL.START', live })
  -> { offset, rows: [{mark, score, trace, d, segScore, segTrace, dSeg, sim}], sections: [{name, from, to, score, trace, d}],
       missing: [mark], extra: [mark], stale: [reason] }
Calib.problems(cmp, opt = { xStage: 3, xSeg: 1 }) -> [problem]   // same shape as Integrity problems
Marks.traceMarks(traza, live) -> [{mark, t, fase, etapa}] (+ OBRA.END = FINAL.FADE + live.Fundido_Dur)
Marks.scoreMarks(score, sched, seed) -> { name: t }            // schema 3: beats[].marks; schema 2: seed
```
- **Ruler lane "Unreal run"** (12 px, under the moments band, in the ruler block; ISP look, `--ink-3` ticks, never cyan): one bar per trace segment, **drawn from the score time of its mark** with the Unreal duration, so each mark tick sits on the score's mark and the bar end shows how far Unreal goes. Overrun beyond the next score mark is hatched amber; underrun leaves an amber gap. Label on the bar: `S1 begin · 134.5 s (−92.3)` when |Δ| > X_seg; tooltip with both numbers and the cause line of §6.4 when known (the table of causes is data in `calib.js`, keyed by segment type: OUTRO/BYE "Alma's congratulation plays before the charge in Unreal"). Header text: `Unreal run · 2 Oct 18:59 · speed 1 · simulated`. Toggle in the lane menu: `Align each mark` (default) / `Align at Hall start` (absolute).
- **Problems** (Integrity shape; filter group "Unreal run"):
  - `C3.TRACE.STAGE` warn — "Recognizing runs 83.8 s here; the last Unreal run took 178.0 s (−94.2 s)." fp = `C3.TRACE.STAGE|S1|` + `Math.round(d)` (re-opens when Δ moves ≥ 1 s: audit A6/B5 parameter rule). Action: "Show in timeline" (selects the section).
  - `C3.TRACE.SEG` info, only in the lane and in Problems when the "Unreal run" filter is on (avoid alert fatigue, audit B2).
  - `C3.TRACE.STALE` info — trace older than `partitura.json` export, or (once the Director adds it) `trace.partitura_hash ≠ live.hash`; and "simulated run: Attracting and Surrounding are capped at 90 s".
  - `C3.TRACE.MISSING` info — a score phase mark not in the trace (`OBRA.DISC` is exempt when the run had no disclaimer).
- Status bar pill gains `Unreal run · −24.7 s` (sum Hall → end), click opens the lane.
- No "match the score to the Unreal run" verb in this lote **[OWNER]** (see §10, D-4).

### 6.7 Should "≠ APK" use trace + Partitura instead of the prototype golden? — yes, layered

Today `Integrity.divergent` compares Unreal-known elements against `score.golden` (prototype timing, F0). That is a poor proxy for the APK: Recognizing alone is 94 s off, and "Real voice lengths" mutates the golden in the live score (app.js 405-422) to keep the comparison meaningful — a baseline edited by an edit.

Proposal (`Integrity.divergent(score, sched, contract, gov, baseline)` with a new `baseline` object):
1. **Knob-governed elements (70)** → baseline = Partitura live value via `Partitura.measure` (already C3.PARTITURA; `divergent` stops double-reporting them).
2. **Beats with a `start`/`el` mark (39 + 3)** → baseline = the trace segment (C3.TRACE.*). Element-level "≠ APK" is not derived from the trace (the trace has no element times).
3. **Other wired elements** (VO chains inside a mark span, AmbPick…) → baseline = the frozen **F0 fixture** `obra/score/baselines/f0.json` (`{times, total, from: "score.json rev 2 golden", frozen: <date>}`), labelled "vs F0 snapshot" in the UI. The live score loses `golden` at the schema 3 migration.
4. When the Director adds `VO.<clip>` lines to the trace **[DIRECTOR]**, rule 3 upgrades to trace-based for voices.
Real voice lengths then need no golden patch: Unreal already plays the real lengths, so the trace is the right baseline for them.

### 6.8 Requests to the Director for the trace (**[DIRECTOR]**, `tools/unreal/smoke_obra.py`, Python only, no Blueprint change)

- Add `config` to `traza.json` from the `OBRA CONFIG:` line (bSimulated, bDisclaimer, Speed, DebugStart) and `partitura_hash` (the `hash` of `obra/unreal/partitura.json` at run time).
- Add `hall: [{mode, step, reloj_obra_s}]` from `HALL: modo M paso N` (needs the reloj; if the line has no TourT, use `pared_s`).
- Add `vo: [{clip, reloj_obra_s, dur}]` from `ALMA: SayClip`, and `marks: [{name:'S<K>.REQEND', …}]` from the "se le pide que cierre" line.
- Keep history: `obra/unreal/trazas/traza-<tag>.json` + `traza.json` = latest (so noise can be measured).

---

## 7. D10 — the contract binds by id; rename never escapes integrity

### 7.1 Data

`contract.json` (web-owned) entries keep `match` as the **rule** (documentation + new-element suggestion) and gain a generated, versioned **`ids`** list:
```jsonc
{ "id": "title.stage", "match": { "key": "^T_(IN|OUT)$" }, "ids": ["el_…", "…"], "idsFrom": { "score": "rev 2 sha12 …", "at": "2026-10-0x" }, … }
```
`partitura_binding.json` binds gain `ids` the same way, per stage (measured with today's key lookup, verified equal):
```jsonc
{ "knob": "Etapa_TituloRevelaIni", "perStage": true, "m": { … }, "ids": { "0": "el_…", "1": "el_…", "2": "el_…", "3": "el_…", "4": "el_…" } }
{ "knob": "Alma_VozRetardo", "perStage": true, "m": { "kind": "gap", … }, "ids": { "0": ["el_ALMA_IN…", "el_firstVO…"], … } }
```
For `@firstVO`/`@lastVO` measures the id is frozen too (if the owner later reorders voices, `C3.BINDING.STALE` says the frozen id is no longer the first voice).
Generator: `tools/score/bind_ids.mjs` (one-shot, re-runnable, writes only `contract.json` / `partitura_binding.json`, prints a diff summary). It is not a score writer.

Seeding corrections applied by the generator, from the trackers (**[DIRECTOR]** confirm):
- New entry `vo.unused` (kind `not-in-unreal`, msg "Unreal no longer plays this voice") with the 10 voices of the `BP_Obra_SC` tracker list (VO_01d, VO_01h, VO_04b, VO_06a, VO_24, VO_34c, VO_35c, VO_36, VO_36c, VO_36d); they leave `vo.wired`.
- VO_12b, VO_17b, VO_21: no asset in Content → `vo.noasset` (kind `not-in-unreal`, "no recording in Unreal") until the Director says otherwise.
- Measured today: 176 (entry, element) pairs over 174 distinct elements; after corrections `vo.wired` drops from 68 to 55.

### 7.2 Integrity

- `contractFor(el, contract)` → `contractFor(id, el, contract)`: an entry applies when `entry.ids` includes the id; entries without `ids` keep the regex behaviour (back-compat for hand-added entries). `el.isNew` still excludes.
- New info problem `C3.CONTRACT.RULE`: element in `ids` whose key no longer matches `match` (renamed), or element not in `ids` whose key matches (new/pasted) → "VO_10b matches the rule of 'vo.wired' but Unreal does not know it." / "T_INTRO was T_IN: Unreal still treats it as the stage title." No action writes `contract.json` from the app (the server has no endpoint for it, on purpose).
- `C3.CONTRACT.ORPHAN` info: an id in a catalog that no longer exists in the score (the element Unreal knows was deleted; mirrors "Deleting it here does not remove it from the APK").
- `Partitura.measure`: prefer `bind.ids[stage]` when the element exists and its beat still carries the expected mark (schema 3) or key (schema 2); otherwise fall back to the key lookup and emit `C3.BINDING.STALE` info.

### 7.3 Rename semantics

- `rename` leaves the QUIET set. `opItems` gets verb `rename` (`verbFor`): every contract entry of the element is checked with `on.rename` (default `info` when absent).
- What rename changes: `key` and `label` only. It **never** changes `sound` or `bind.asset` for an existing element (today `Act.rename` also renames `sound` when `sound === key`, which would silently detach a wired voice from its recording — fix). For `isNew` sounds (inbox WAV named by id) behaviour is unchanged.
- Card texts (English, sentence case, editing language):
  - wired voice, schema 3 (`bind.asset` set): info "The name changes in the score only; Unreal still plays VO_10."
  - wired voice, schema 2 (asset implied by key): warn "Unreal plays this voice by its file name (VO_10): renaming it here does not rename the recording."
  - knob-governed: info "Still governed by Etapa_TituloRevelaIni (Unreal timing knob)."
- Changing the asset is a separate verb (`Act.setAsset`, op `rebind`, schema 3 only) with `on.rebind` (default `warn` for wired, `info` otherwise).
- Duplicated keys stop mattering for integrity (55 today); the editor may still show `#n` in labels.

### 7.4 Tests (integrity_test.mjs / edits_test.mjs)

- Rename T_IN → T_INTRO (via the same mutate path as `Act.rename`), then move +2 s: card still has `C3.TITLE.STAGE` info and the Partitura C3 item (today: silent after rename).
- Rename G_BELL, set fw 60: `C3.DRIFT` still present (today disappears).
- Rename VO_10 → `sound` stays `VO_10`; `bind.asset` stays.
- Paste/duplicate (when lote 4 lands) a T_IN: the copy is not in `ids` → `C3.CONTRACT.RULE` info, no block.
- `bind_ids.mjs` on the real score: every entry's `ids` equals today's regex result (except the documented corrections); every binding `ids` equals `Partitura.measure(...).els` for all stages.

---

## 8. D13 — knobs a machine can read, and the ADR

### 8.1 `obra/unreal/knobs.json` (web-generated by `tools/score/knobs.mjs`, no Unreal access)

```jsonc
{
  "generated": "…",
  "sources": { "partitura": { "hash": "54ef5a851e4b", "exported": "2026-10-02T18:06:10" },
               "perillas": "2026-10-02T18:06:10", "roles": "2026-10-01" },
  "knobs": {
    "da:Etapa_Tope": { "scope": "da", "owner": "/Game/SoulCharger/Obra/Partitura/DA_Partitura_Obra", "var": "Etapa_Tope",
      "type": "a5", "unit": "s", "value": [240,180,120,240,205], "base": { "hash": "54ef5a851e4b" },
      "proposable": true, "lock": false, "category": "2 Cada etapa", "binding": "Etapa_Tope" },
    "inst:Test_Hall/HallDirector.FW_Bell": { "scope": "instance", "owner": "Test_Hall › HallDirector", "var": "FW_Bell",
      "unit": "s", "value": 25, "valueFrom": "roles.json (text; not harvested)", "base": null,
      "proposable": false, "lock": true, "elements": ["el_… (G_BELL)"] },
    "cdo:BP_Obra_SC.AmbVolumes": { "scope": "cdo", "owner": "/Game/SoulCharger/Obra/Blueprints/BP_Obra_SC", "var": "AmbVolumes",
      "value": "…", "valueFrom": "perillas.json", "proposable": false, "lock": false },
    "lit:BP_HallDirector_SC.HallTickSteps.release": { "scope": "literal", "owner": "HallDirector graph", "value": "−2 /s", "proposable": false }
  }
}
```
- `da:*` = the 60 knobs of `partitura_def.json` + live values of `partitura.json`; the only **proposable** ones.
- `inst:*` = parsed from `roles.json` rows (`row[5]` leading identifier = `var`, `row[1]` = value text → number when it parses, `row[6]` = lock; elements frozen from the role `match`). Read-only until an instance harvest exists **[DIRECTOR]** (instance values are not in `perillas.json`, which is the CDO).
- `cdo:*` = `perillas.json` (22 BPs, `[name, category, value]`), category `Interno` skipped.
- The app's Knobs inspector reads `knobs.json` (fallback: `roles.json` rows as today).

### 8.2 ADR text (to commit as `docs/editor-obra/ADR-001-partitura-y-unreal.md`, Spanish neutral)

> **ADR-001 · Cómo llegan los tiempos de la partitura a Unreal** (2026-10-02, propuesto; lo aprueba Beltrán)
>
> **Contexto.** El PLAN (§3.3, §4 F4, §6 decisión 1) pedía una DataTable con structs, una reconciliación de tres vías en runtime y un `ScoreApply` que escribiera perillas de instancia. El anexo 11 y el acuerdo con el Director del 2026-10-02 (`obra/unreal/LEEME.md`) dicen otra cosa, y el PLAN hace ganar al plan. Este ADR fija la decisión y deja sin efecto esas partes del PLAN.
>
> **Decisión.**
> 1. **Formato:** los tiempos narrativos viven en el DataAsset `DA_Partitura_Obra`. No hay DataTable ni structs nuevos. Unreal no lee la partitura web en runtime.
> 2. **Quién escribe:** el editor web nunca escribe `.uasset`. Propone con `obra/unreal/partitura_propuesta.json`, solo con Send to Unreal y la tarjeta de revisión.
> 3. **Quién aplica:** una sesión con Unreal abierto, solo cuando Beltrán lo pide: respaldo, aplicar, prueba de humo; si falla, restaurar. Nada se aplica porque un archivo apareció.
> 4. **Perillas de instancia** (`FW_*`, `ExploreTime`, etc.): solo lectura en la web hasta que exista una cosecha de instancias. No hay tres vías en runtime: si hace falta, la reconciliación ocurre al proponer (valor base cosechado contra valor vivo).
> 5. **La partitura (`score.json`)** es la fuente de la estructura y del previs. Ninguna herramienta la reescribe; las migraciones son operaciones de la app, con tarjeta y deshacer, y las guarda el usuario.
> 6. **Cues por marca** (`compile.mjs`): solo en seco. El manifiesto informa qué llegaría y por qué no; no se aplica. Si en F4 existe `BP_ScorePlayer_SC`, su tabla la escribe el Director a pedido, con el mismo respaldo y la misma prueba de humo.
> 7. `guion.js` es referencia visual. `traza.json` es la medición de lo que Unreal hace.
>
> **Consecuencias.** Se corrigen PLAN §3.3, §4 (F4) y §6 (decisión 1) con una nota que apunta a este ADR. El catálogo de perillas legible por máquina es `obra/unreal/knobs.json`. Los enlaces de contrato y de perillas se guardan por id de elemento (D10).

---

## 9. Implementation steps (serial; each one independently testable)

Every step ends with the four suites green: `node tools/score/edits_test.mjs`, `node tools/score/integrity_test.mjs`, `node tools/score/golden_test.mjs` (665/665), `python tools/editor/server_test.py`, plus the new tests it adds, and `node --check` on every touched JS. Browser checks follow the harness rules (undo every test edit, reload, no draft left).

| # | Step | Files | Tests | Risk |
|---|---|---|---|---|
| 1 | **ADR + PLAN pointers** (§8.2). PLAN §3.3/§4/§6 get a one-line "superseded by ADR-001" note. | `docs/editor-obra/ADR-001-partitura-y-unreal.md` (new), `docs/editor-obra/PLAN-EDITOR-OBRA-2026-10-01.md` | none (docs; Spanish neutral check) | low; owner approval needed before 6+ |
| 2 | **`js/marks.js`** (pure UMD): `PHASE`, `fromPhase`, `isValid`, `rank`, `traceMarks`, `scoreMarks` (schema 3 marks or seed). | `web/editor-obra/app/js/marks.js` (new), `tools/score/fixtures/traza-20261002.json` (copy of today's trace), `tools/score/marks_test.mjs` (new) | phase→name for all 16 codes; `S4.BYE` invalid; 41 trace marks + OBRA.END = 1022.885; rank monotonic on the fixture | low |
| 3 | **Seed file** `obra/score/seed/marks-v1.json` generated from the §2 table by `tools/score/seed_marks.mjs` (keyed by beat id; `el` resolved to element ids). Reviewed by the owner **[OWNER]**. | `tools/score/seed_marks.mjs`, `obra/score/seed/marks-v1.json` | test: 73 beats, counts 35/4/4/27/3, every `el` id belongs to its beat, every phase mark once | medium (owner review of 3.R3 / R3) |
| 4 | **`js/calib.js` + lane + Problems** (§6.6). App loads `traza.json` optionally (`opt()` like the others). | `js/calib.js` (new), `js/app.js` (load, compute → problems), `js/ui.js` (ruler lane, pill), `css/editor.css`, `index.html` (script tag), README tables | `tools/score/calib_test.mjs`: on the real score + fixture: offset 19.82, sections Hall +1.0, Entering +15.6, Recognizing −94.2, Loving −3.1, Attracting +33.4, Surrounding −12.5, Final +35.1, total −24.7; problems: 6 `C3.TRACE.STAGE` at X=3; fp carries `Math.round(d)`. Browser: lane visible, tooltip, no console errors | medium (ui.js is large; lane must not slow scroll: draw once per compute, not per frame) |
| 5 | **`integrity.js` UMD** (D12 overlap, prerequisite for compile): `})(typeof window !== 'undefined' ? window : globalThis)` + `module.exports`. | `js/integrity.js`, the two test files' loaders | `node -e "require('…/integrity.js')"` works; suites green | low |
| 6 | **Contract and binding ids** (§7): `tools/score/bind_ids.mjs` writes `ids` into `contract.json` and `partitura_binding.json` (+ `vo.unused`, `vo.noasset` entries **[DIRECTOR]** ack); `contractFor` by id; `C3.CONTRACT.RULE/ORPHAN`, `C3.BINDING.STALE`; `rename` leaves QUIET; `Act.rename` keeps `sound`. | `tools/score/bind_ids.mjs` (new), `obra/unreal/contract.json`, `obra/unreal/partitura_binding.json`, `js/integrity.js`, `js/partitura.js`, `js/app.js` | §7.4 list; integrity_test counts of open problems unchanged except the documented ones (vo.unused moves 10 voices to not-in-unreal) | medium (behaviour change in cards: run the B2 fatigue tests) |
| 7 | **F0 baseline out of the live score (D4)**: `tools/score/freeze_f0.mjs` creates `obra/score/baselines/f0.json` from the current `score.golden` (new file; `score.json` untouched). `golden_test.mjs` reads the fixture (`tools/score/fixtures/f0-score.json` = copy of today's score) so it stops depending on the live score. `divergent()` takes a `baseline` object (§6.7) with knob / trace / f0 layers; app reads `f0.json` when `score.golden` is absent. | `tools/score/freeze_f0.mjs`, `tools/score/fixtures/f0-score.json`, `tools/score/golden_test.mjs`, `obra/score/baselines/f0.json`, `js/integrity.js`, `js/app.js` (`compute`, real-voice-lengths no longer patches the golden on schema 3) | golden 665/665 on the fixture; divergent on the real score unchanged while `score.golden` exists; with golden removed in memory it reads f0 and yields the same set | medium |
| 8 | **`tools/score/idmap.mjs`** + `obra/unreal/idmap_aliases.json` + generated `obra/unreal/idmap.json` (uses `deps.py` output). | `tools/score/idmap.mjs`, `obra/unreal/idmap.json`, `obra/unreal/idmap_aliases.json`, `tools/score/idmap_test.mjs` | synthetic tree in a temp dir (files containing `SoundWave` / `ObjectRedirector` / duplicate names / plugin mount) → exact JSON; real run: 1 ambiguous (VO_12c, while it lasts), `--check` stable on two runs | low (Content is moving: test on the synthetic tree, not on counts of the real one) |
| 9 | **`js/reach.js`** (§3.3) + status bar + inspector "Unreal" section; on schema 2 it uses the seed for marks and the key for assets. | `js/reach.js` (new), `js/app.js`, `js/ui.js`, README | `tools/score/reach_test.mjs`: real score → knob 70, wired 82 (before step 6 corrections; after: recount and pin), preview rest; with a fixture where the A12 loops are fixed: cue-ready 12 elements (expected; pin what it measures); persona-spread rule demoted cases (e.g. VO_11h after G_BREATH) | medium |
| 10 | **Schema 3 validation + migration operation** (§3.5-3.6): `Edits.validate3`, `Edits.migrate3` (pure), `Act.upgradeSchema3` + card; server `check_score` accepts 3; Import/draft accept 3. | `js/edits.js`, `js/app.js`, `js/ui.js` (card text), `tools/editor/serve_editor.py`, `tools/editor/server_test.py`, `tools/score/edits_test.mjs`, README | edits_test: migrate3 on the real score copy → 0 time changes (resolve equal ±1e-9 for all 665), counts of §3.4, idempotence guard, validate3 rejects bad mark/rel/el-in-other-beat/dup phase mark; undo restores identical JSON; server_test: PUT schema 3 ok, malformed `marks` → 400. Browser: run the verb, see card, Cancel, run again, Bind, Ctrl+Z, reload: no draft | high (touches the save path: restart the 8767 server after the Python change; never PUT the real score in tests) |
| 11 | **`js/compile.js` + `tools/score/compile.mjs`** (§5). | `js/compile.js` (new, UMD), `tools/score/compile.mjs` (new), `tools/score/compile_test.mjs` (new) | §5.4 | low (pure; reuses steps 2, 8, 9) |
| 12 | **Knobs catalog** `tools/score/knobs.mjs` → `obra/unreal/knobs.json`; Knobs inspector reads it. | `tools/score/knobs.mjs`, `obra/unreal/knobs.json`, `js/ui.js` | test: 60 `da:*` with live values = partitura.json; roles rows parsed (FW_Bell 25, lock) ; no Interno CDO vars | low |

Order rationale: 2-4 deliver the trace calibration on schema 2 (value now, no migration); 5-7 are integrity hygiene needed by everything after; 8-9 make reach honest; 10 is the only step that changes the score format (after the owner approves the seed and the ADR); 11-12 close D1/D13. Steps 6 and 10 change `obra/unreal/*.json` web-owned files only; none touches `partitura.json`, `perillas.json`, `traza.json`, `LEEME.md`, `partitura_propuesta.json`.

README (`web/editor-obra/app/README.md`, Spanish neutral) gains: files `marks.js`, `calib.js`, `reach.js`, `compile.js`; tools `compile.mjs`, `idmap.mjs`, `bind_ids.mjs`, `knobs.mjs`, `seed_marks.mjs`, `freeze_f0.mjs`; the lane and the menu verb in the shortcut/feature tables.

---

## 10. Decisions and requests

### [OWNER] decisions (Beltrán)

| # | Question | Recommendation |
|---|---|---|
| D-1 | Anchors of 2.R4/2.R5 and 5.R4/5.R5 (A12). They block `compile` and cost −94 s in Recognizing. | Fix in Problems ▸ "Fix the loop…" before step 11; 2.R5 after 2.R4. |
| D-2 | Approve the beat → mark table (§2), especially S2.BEGIN in 3.R3 and the three "layers" beats as preview. | Approve; split 3.R3 into intro (6 s) + calm. |
| D-3 | Calibration thresholds and the "≠ APK" baseline. | X stage 3 s, X segment 1 s, refined with two runs; baseline = Partitura + trace + F0 fixture (§6.7). |
| D-4 | A "Match the score to the Unreal run" verb (like "Match the score to Unreal" for knobs)? | Not now. Later, only for segments set by knobs or clip lengths (OPEN, CHARGE, BYE), never for simulated mechanics. |
| D-5 | The 10 voices Unreal no longer plays and the 3 without recording: keep as preview or delete from the score? | Keep, marked "not in Unreal"; delete is the owner's edit. |
| D-6 | Approve ADR-001. | Approve (it matches LEEME and annex 11). |
| D-7 | When to migrate to schema 3. | After lote 4 lands and D-1/D-2 are decided. |
| D-8 | Structural difference: Alma's congratulation before (Unreal) or after (score) the charge. | Unreal is the piece (DA rules timing): move VO_13/18/23b/29 to R5x in the score; the calibration shows the before/after. |

### [DIRECTOR] requests (Unreal session, on its turn)

1. `smoke_obra.py --traza`: `config`, `partitura_hash`, `hall` steps, `vo` clips, `REQEND`, history folder (§6.8); run it twice at speed 1.
2. Confirm `vo.unused` (10) and `vo.noasset` (VO_12b, VO_17b, VO_21: VO_12f1/f2?), VO_12c duplicate (Breath vs Obra), and which voices are 2D (`vo_2d`).
3. Ack `idmap.json`, `idmap_aliases.json`, `knobs.json` as web-owned files in the LEEME table; optionally extend `deps.py` to plugin mounts.
4. Later (F4, not this lote): `SHARE.*` marks, an instance-knob harvest, and the decision whether `BP_ScorePlayer_SC` ever exists.

---

## Appendix A · Reproduce the numbers (scratch dir, read-only on the repo)

All in `C:/Users/beltr/AppData/Local/Temp/claude/C--Users-beltr-Desktop-Alma-Digital-Studio-Projects-VR-Unreal/c5fe4ce1-f688-4688-b3d0-60d97942b228/scratchpad/` (copies: `score_copy.json`, `traza.json`, `contract.json`, `partitura*.json`, `roles.json`):
- `node l5a_beats.cjs` — the 73 beats with typical times and anchors.
- `node l5a_calib.cjs typical|idle` — §6.2/6.3 tables (env `SCORE=` to try another copy).
- `node l5a_idmap.mjs idmap_proto.json` — §4.3 numbers; `node l5a_refs.mjs` — naive reference scan (shows the FName `_<n>` pitfall).
- `node l5a_marks.cjs` — §2 counts, reach projection, persona invariance (446/592), cue-ready (22 → 12 unreferenced); writes `l5a_marktable.md`, `l5a_map.json`.
