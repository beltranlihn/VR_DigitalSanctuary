# BP_BreathStage_SC — la etapa Entering portable (orquestador)

**Ruta:** `/Game/SoulCharger/Mechanics/Breath/BP_BreathStage_SC`
**Colocado en:** `/Game/Test_Entering` como `Entering_Stage`
**Nació:** 2026-09-27 · **Estado:** 🟢 flujo completo verificado en PIE y Simulate · ⬜ visor

## Qué es
El único BP que conoce a los otros tres: [[BP_BreathRig_SC]] (controller), [[BP_BreathBlob_SC]] (metaball) y [[BP_Pacer_SC]] (guía). Los encuentra solo por clase (`StageFind`, `GetActorOfClass`: uno de cada uno por nivel). Rig, metaball y pacer no se conocen entre sí.

## Flujo (máquina de fases en `StageTick`, sondeo — sin bindear dispatchers)
| Fase | Qué pasa | Sale cuando |
|---|---|---|
| 0 | espera | `bAutoStart` y `StartDelay` (1,5 s) → `StageStart()` |
| 1 | `Rig.SetRigActive(true)` + `Blob.BlobAppear()` | `PacerDelay` (2 s) → `Pacer.PacerPlay()` |
| 2 | el pacer corre sus `Cycles` | `Pacer.bRunning` pasa a false (su `PacerWrap` lo apaga al completar y el pacer se achica solo) |
| 3 | pausa | `BlobOutDelay` (0,6 s) → `Blob.BlobDisappear()` |
| 4 | el metaball se achica | `Blob.EnvT ≤ 0` → `Rig.Retire()` + **`OnBreathStageDone`** + log `BREATHSTAGE: fin de la etapa` |
| 5 | terminado | — |

🆕 **2026-09-27 (2ª) — fases rehechas para las pausas del pacer:** 0 espera → 1 `StageStart` (rig + metaball) → tras `PacerDelay` `PacerPlay` (el pacer aparece y hace su **pausa de entrada**) → 2 espera `Pacer.bRunning` → 3 espera `Pacer.EnvT < 0,999` (= terminó los ciclos, hizo su **pausa de salida** y empezó a achicarse) → 4 tras `BlobOutDelay` sale el metaball → 5 metaball en 0 → `Retire` + `OnBreathStageDone` → 6. `StageEnd` (forzado, fases 1-3) llama `PacerStop` (que ahora lleva al pacer a su pausa de salida) y salta a 3. Usa `GetRunning`/`GetEnvT` porque el catálogo no ve los miembros nuevos del pacer (gotcha 436).

**Enganche con la obra:** `bAutoStart = false`, el director llama `StageStart()` y escucha `OnBreathStageDone`. `StageEnd()` = cierre forzado (para el pacer → sigue el cierre normal).

## 🚶 Contrato TOUR (2026-09-29, para `Test_Recorrido`)
`Test_Recorrido` carga `Test_Entering` entero con `LoadLevelInstance`. Con un actor tagueado `TOUR` en el mundo la etapa nace **dormida**; sin él (el `Test_Entering` de siempre) **nada cambia** (verificado en PIE: ninguna línea Tour, mismo flujo). Plan de origen: `VR_Test/Saved/ClaudeScripts/tour/PLAN-TOUR-ENTERING.md` (se simplificó de 9 a 7 funciones).

**Estado real de la etapa:** lo que ya había. `Phase` y `PhaseTimer` (categoría `Z-Estado`, sin espacios → `Variables|Z-Estado|…`), refs `Rig`/`Blob`/`Pacer`. `StageStart` ya llama `StageFind` y fija fase 1 + reloj 0, sin guarda. La fase 6 es inerte (el `switch` no tiene caso 6). **Dormida = Tick apagado** (cero variables nuevas); "corriendo" = fase 1-5.

| Función | Pública | Qué hace |
|---|---|---|
| `TourCheck()` | (la llama `BeginPlay`, último nodo después de `StageFind`) | `GetAllActorsWithTag("TOUR")` > 0 → log `hay un actor TOUR…` + `TourSleep` |
| **`TourSleep()`** | ✅ sin parámetros | `StageLife(false)` → `TourCut` → `Phase` 6 → `SetActorTickEnabled(false)` → log `TourSleep (dormida hasta TourWake)`. Idempotente. **No dispara `OnBreathStageDone`** (dormir no es terminar) |
| `TourCut()` | interna | solo si fase 1-5: log `TourSleep corta la etapa…` · `Rig.Retire()` · `StageHush(Pacer)` · si fase ≤ 4 `Blob.BlobDisappear()` (en la 5 ya está saliendo) · si fase 2-3 `Pacer.PacerStop()` (solo cuando el pacer ya fue lanzado y todavía no sale) |
| **`TourWake()`** | ✅ sin parámetros | si NO está en fase 1-5: `SetActorTickEnabled(true)` · `StageLife(true)` · `StageStart()` · log `TourWake (arranca desde cero)`. Idempotente (corriendo no hace nada); re-arrancable después de `TourSleep` o del fin natural (fase 6) |
| `StageLife(Awake)` | interna | `GetActorOfClass(BP_ValleyLife_SC)`, `IsValid`: `bVida` = Awake · `Wait` = `FirstGap` (si no, al despertar sale una ráfaga en el acto: `Wait` se descuenta aunque `bVida` esté en false) · `StageHush(vida)` (corta el `GustAudio` de una ráfaga en curso; su parte visual termina en silencio a propósito) |
| `StageHush(Target)` | interna | `for` sobre `GetComponentsByClass(Target, AudioComponent)` → `StageHushOne` |
| `StageHushOne(Comp)` | interna | `AudioComponent.FadeOut(0,25 s, 0)` — **por cirugía** (`create_node` + `declaring_class` `/Script/Engine.AudioComponent`): `FadeOut` está duplicado con `SynthComponent` |

**Qué hace dormir:** control apagado (rig inactivo, `RevealT` → 0 en 0,6 s, manos del pawn devueltas, háptica cortada, `MPC_Breath` a 0 → aire y valle a neutro solos) · metaball afuera (`BlobDisappear`, 2 s) · pacer quieto (`PacerStop`: reloj y sonidos nuevos cortados al instante, visible en su pausa de salida ~3 s y se achica en 0,6 s) · sonidos del pacer y de la vida con fundido de 0,25 s · vida con `bVida` false (el polvo se va con `GlobTau`, no salen ráfagas nuevas).
**Qué hace despertar:** arranca desde cero como en `Test_Entering`: rig + metaball (`StageStart`), `PacerDelay` 2 s → `PacerPlay` (resetea ciclos), vida con `bVida` true y la primera ráfaga a `FirstGap` s.

**Reglas para el director del recorrido:**
- Llamar **solo** `TourWake()`/`TourSleep()`. **No tocar el Tick de la etapa** (es su estado de dormida).
- Llamar `TourWake()` **después** del `BeginPlay` de la instancia (no hay guarda: `HasActorBegunPlay` no está expuesto a Blueprint; un `TourWake` antes del `BeginPlay` arrancaría y el `BeginPlay` la volvería a dormir).
- Después de `TourSleep`, esperar **≥ 4 s** antes de congelar/ocultar rig, metaball o pacer (sus salidas duran 0,6 / 2 / ~3,6 s y necesitan su Tick).
- `bVida` de la vida lo pisa la etapa: para apagar la vida en el recorrido usar `VidaAmount` 0.
- 🔴 La etapa depende de la clase `BP_ValleyLife_SC` (en `StageLife`). Portar Entering sin la vida = vaciar `StageLife`.

**Verificado 2026-09-29 (PIE):** (a) sin TOUR: `VIDA: lista` → `BREATHRIG: montado` → `activo` → `BLOB: entra` → `BREATHSTAGE: inicio` → `pacer aparece` → `pacer en marcha`, cero líneas Tour, cero `Accessed None`; vida `Glob` 1, ráfaga a los ~14 s (`bGusting` true, `Front` avanzando, `GustAudio.Sound` = `SND_VidaGustA`). (b) con tag `TOUR` temporal en `PlayerStart_0`: `hay un actor TOUR…` + `TourSleep (dormida…)`, ningún `inicio`/`activo`/`BLOB: entra` en 26 s; `Phase` 6, `PhaseTimer` 0 (Tick apagado), rig `bEnabled` false / `RevealT` 0, metaball `EnvT` 0, pacer `EnvT` 0 / `bRunning` false, vida `bVida` false / `Glob` 0 / sin ráfaga pasados los 14 s.
⬜ **Sin verificar: `TourWake` y el corte de `TourSleep` con la etapa corriendo** — el MCP no manda comandos de consola a PIE (gotcha 441), así que `ke * TourWake` no se pudo probar. Se prueba con el director de `Test_Recorrido` o por consola a mano en PIE (`ke * TourWake`, `ke * TourSleep`).

## 🎬 Contrato de etapa de la Obra (2026-09-30 noche, pedido de Narrativa/Beltrán) — 🟢 PIE · ⬜ visor
Plan: `docs/PLAN-NOCHE-2026-09-30.md`. Los stubs los creó Narrativa; los llenó Breath. DSL completo: `VR_Test/Saved/ClaudeScripts/usertool/stage_contract.dsl`.
| Función | Qué hace |
|---|---|
| `StageEnv()` | solo la capa de vida (`StageLife(true)`): la Obra la llama al encender la celda, detrás del velo |
| `StageIntro()` | despierta la etapa (`SetActorTickEnabled(true)`, `StageFind`, vida) · `bStageDone` false · fase **10** · `Blob.BlobAppear()` (morfeo 4 s) + `BlobInSound` · a los `ToolDelay` 1,5 s `StageTool` → `BP_UserTool_SC.ToSensor(SensorColor)` (azulado) |
| `StageBegin()` | `Rig.SetRigActive(true)` · fase **11** (exploración libre `ExploreTime` 20 s) → **12**: `CountSound` = `VO_12c` "Three… two… one…" (2,83 s, voz de Alma, `Mechanics/Breath/Audio/`) → `CountTime` 3 s → `PacerPlay` y fase 2 (el flujo de siempre). El pacer arranca respire o no |
| `bStageDone` | al terminar los ciclos (fase 4 del flujo viejo) → fase **13** + `OnBreathStageDone`. El metaball NO sale solo |
| `StageOutro()` | fase **14**: `Blob.BlobDisappear()` (2,5 s) + `BlobOutSound` · `Rig.SetRigActive(false)` · `StageHush(Pacer)` y `PacerStop` si corría (cortafuegos) · **el sensor queda en la mano** · al llegar el metaball a 0 → fase 6 |
| `ContractStep(DT)` | en el Tick DESPUÉS de `StageTick` (cirugía en el EventGraph); `dt = min(DT, 1/30)`; mueve las fases 10-14 (el switch viejo no tiene casos para ellas: quedan inertes allí) |
| `ContractTest(DT)` | `bContractTest` (instance-editable; **true en Test_Entering**): Intro a 1,5 s → Begin 8 s después → Outro al `bStageDone`. Con un actor `TOUR` en el mundo se apaga solo (`TestStage` 99) |
Perillas `0-Contrato`: `bContractTest` · `ExploreTime` 20 · `CountTime` 3 · `ToolDelay` 1,5 · `SensorColor` (0,35, 0,7, 1) · `CountSound` · `BlobInSound` (VR_shep_scale_up_01) · `BlobOutSound` (VR_shep_scale_down_02). Estado `Z-Estado`: `ContractTimer`, `TestClock`, `TestStage`, `bContract`, `bToolDone`.
- 🔴 **La Obra NO llama `TourWake`** (arranca la etapa vieja entera: rig + metaball + pacer). `TourSleep` sigue sirviendo para dormirla después de `StageOutro`.
- `TourWake`/`TourSleep`/`bAutoStart` (flujo viejo) intactos: `Test_Recorrido` sigue igual (sin mando visible: el rig ya no dibuja el suyo).
- Verificado en PIE (bContractTest, exploración 4 s y 1 ciclo solo en el mundo de PIE): log en orden `StageIntro`/`BLOB: entra` → +1,48 s `ToSensor` → +8 s `StageBegin`/`BREATHRIG: activo` → `three, two, one` → +3 s `arranca el pacer` → `bStageDone` → `StageOutro`/`BLOB: sale` → +2,5 s `salida terminada`; cero `Accessed None`.
- 🐛 Pagado al escribir: `(Actor|Tick|SetActorTickEnabled true)` sin target escribió `bEnabled` = **false** (el literal fue al pin `self`); se corrigió con `set_pin_value`. Leer siempre el grafo después de escribir.
- 🟢 **`CycleScores`** (float[], `Y-Publicado`, lo lee el cuadro de resultados: `BP_JourneyContent_SC.SetBreathScores` después de `bStageDone`): un valor 0..1 por ciclo = clamp(Pearson(P, S)). **P** = la guía del pacer desde SU reloj (`T`, `InhaleTime`/`Hold1Time`/`ExhaleTime`: inhala −1→+1 · sostiene +1 · exhala +1→−1 · sostiene −1; lineal, el MID del pacer no conecta con `GetScalarParameterValue` desde el DSL) · **S** = `BreathFollow` del rig (lo que va a `MPC_Breath.Signed`). `ScoreStep(DT)` en el Tick después de `ContractStep`: muestrea solo en fase 3 con el pacer corriendo (`ScoreSample`, sumas `ScN/ScP/ScS/ScPP/ScSS/ScPS`); cierra el ciclo cuando la guía vuelve a subir desde el fondo (−0,95 → −0,9) y el último cuando el pacer para (`ScoreFinish` + `ScoreReset`, mínimo 30 muestras); `ScoreClear` en la fase 10; si `BreathOn` nunca pasó de 0,5 (`bSawOn`), el array queda vacío en la fase 13. Log `BREATHSTAGE: puntaje del ciclo …`. DSL: `Saved/ClaudeScripts/usertool/score.dsl`.
  - Verificado en PIE (2 ciclos, respiración falsa de 12 s): `[0,956, 0,288]`. El segundo bajo es del INSTRUMENTO: bajo el sondeo del MCP el PIE corre a < 30 fps y el paso limitado a 1/30 atrasa al pacer (12 s de pacer = 14 s reales) contra la respiración falsa en tiempo real. A 72 fps el límite no actúa.
- Flags de test **en false al guardar** (regla de Narrativa): `bContractTest` y `Entering_UserTool.bShowMandoOnBegin`. Para probar el contrato suelto en Test_Entering, tildarlos y destildarlos antes de guardar (con los dos en false, Play corre el flujo viejo sin sensor visible).
## Perillas `0 - Etapa`
`bAutoStart` true · `StartDelay` 1,5 · `PacerDelay` 2 · `BlobOutDelay` 0,6. Los ciclos y tiempos de respiración se autoran **en el pacer** (Preset 1 = 6-0-6-0, `Cycles` 5 en el nivel de test).

## Trampas de esta construcción
- 🔴 El dispatcher se llamaba `OnStageFinished` y **ya existe en otros 2 BPs**: `Default|CallOnStageFinished` se resolvió contra `BP_Sequencer_SC` (*"self is not a BP_Sequencer_SC_C"*). Renombrado a `OnBreathStageDone` (único).
- `Utilities|IsValid` en el DSL es **siempre la macro con ramas**, aun dentro de un `select` → "Unreachable code". Por eso `StageFind` no tiene fallback por instancia.
- El read rotula `Retire`/`SetRigActive` como `Class|BPSeqRigSC|…` y el `GetEnvT` del metaball como del pacer: **es la etiqueta**; `get_node_infos` confirmó la clase del pin `self` de cada llamada.

## 📦 APK de prueba + banco de medición (2026-09-27)
`Test_Entering` empaquetado (Development ASTC, `com.almadigital.entering`, "Soul Charger Entering") e **instalado en la Quest**. El nivel lleva además `Perf_Entering` ([[BP_PerfEntering_SC]], carpeta `Debug`), que apaga/prende metaball y pacer por consola para medir cuánto pesa cada uno con `scripts/quest_entering_perf.ps1`. La etapa no sabe que existe: durante la medición el pacer queda en ciclos infinitos (`PerfELoop`) y al final vuelve a sus ciclos, así que el cierre (pacer → metaball → `OnBreathStageDone`) es el de siempre.

## Verificado (2026-09-27, `bFakeBreath` + pacer 1-0-1-0 × 2)
Log en orden: `BREATHRIG: montado` → `activo` → `BLOB: entra` → `BREATHSTAGE: inicio` → manos escondidas → `BREATH: listo` → `pacer en marcha` → `el pacer termino sus ciclos` → `BLOB: sale` → `BLOB: salida terminada` → `BREATHRIG: inactivo` → `fin de la etapa` → manos devueltas. Cero `Accessed None` en PIE y en Simulate.

## ⏱ 2026-09-30 (tarde) — agilidad (decisiones de Narrativa, pedido de Beltrán)
- `ExploreTime` 20 → **12** · `ToolDelay` 1,5 → **0,8** (CDO e instancia de Test_Entering, antes → después).
- **El pacer aparece CON el "three, two, one"**: cirugía de exec en `ContractStep` — `PacerPlay` pasó de la rama fase 12→2 al final de la rama 11→12 (después del print `three, two, one`). La pausa de entrada del pacer (`LeadIn` 3 s) corre durante la cuenta (`CountTime` 3 s) y la respiración arranca al terminar "one". El print de la rama 12→2 ahora dice `fin de la cuenta (el pacer ya aparecio con ella)`. La fase 2 espera `Pacer.bRunning` como siempre.
- Medido en PIE: `three, two, one` 17:17:34,28 → `pacer en marcha` 17:17:37,30 (antes: +6 s). Desde `StageBegin` hasta `bStageDone`: 12 + 3 + 70 (4-3-4-3 × 5) + 3 (`LeadOut`) ≈ **88 s** (antes 99).
- ⚠ Instrumento: con scripts MCP corriendo durante el PIE el editor se traba y el `Dt` recortado a 1/30 alarga los temporizadores (la exploración midió 21 s con `ExploreTime` 12 leído en el mundo de PIE). No es de la etapa.
- La Obra encuentra al sensor con `GetActorOfClass(BP_UserTool_SC)` en `StageTool`: el de Test_Entering es `TestOnly` (lo destruye la Obra) y el que queda es `UserTool_Obra` del persistente (valores = CDO = los de Test_Entering, verificado).
- 🔴 **Sensor que no aparecía en la Obra con StageBegin temprano (arreglado):** la conversión mando → sensor (`StageTool` a los `ToolDelay`) exigía `Phase == 10`; en la Obra a `Speed` 8 `StageBegin` llegó a los 0,75 s (antes de 0,8) y el sensor no aparecía nunca. Cirugía: el `==` (`K2Node_PromotableOperator_4`) pasó a **`>=` 10** → si `StageBegin` llega antes, el sensor aparece a los `ToolDelay` del reinicio del reloj de exploración. Verificado en la Obra (PIE, Speed 8): `StageIntro` → `StageBegin` +0,75 s → `UserTool.ToSensor (azulado)` +0,80 s → `mode 2`, `LightColor` (0,35, 0,7, 1), `bMounted`, visible → cuenta → pacer en marcha +3 s.
