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
