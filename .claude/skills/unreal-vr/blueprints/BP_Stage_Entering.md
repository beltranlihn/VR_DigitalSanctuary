# BP_Stage_Entering — la primera etapa REAL (Core/Stages/)

## Purpose
Paso 4 del §10: la primera subclase de [[BP_StageBase]] con mecánica de verdad — **la respiración de Breath integrada al ciclo de salas**. No reinventa nada: spawnea la cadena PROBADA EN VISOR de `Stages/Breath/` (`BP_Instructions` → widget de 5 páginas → `BP_BreathSensor_V2` → `Box_Breath`) y espera a que el sensor complete sus respiraciones para pedir el cierre por el camino real (`StageDone` → `FinishStage` → `ForceComplete`).

Pedido de Beltrán (2026-08-13): *"en la de breath ya tenemos el sensor, simplemente habría que integrarlo a la etapa, y habría que integrar el widget con las instrucciones... deja la etapa funcional con algún objeto que reaccione a la respiración, por ahora puedes dejar un cubo"* — el objeto reactivo es `Box_Breath`, que ya existía.

## Status
🟡 Construida y verificada por log en el ciclo completo (2026-08-13). 🆕 **2026-08-14: REWORK del guión — la etapa ya NO cierra por conteo de respiraciones, cierra por el RITMO GUIADO.** ⬜ La respiración real necesita visor.

## 🔧🔧 2026-08-14 — el rework del Acto 4 (guión)
Lo que pedía el guión: *"la mecánica ya NO cierra por conteo: aparece el objeto + radial slider de timing (4 inhala / 4 aguanta / 4 exhala × 5) … el usuario controla el objeto en tiempo real; el timing avanza solo"* + *"auto-avance de página a los 20 s (cortafuego)"*.

### 1. El cierre lo decide [[BP_BreathPacer]], no el contador
```
CheckBreathDone (poll 0,5 s)  →  esconde el sensor (sigue igual)  →  CheckBreathHit(S)
CheckBreathHit:  si el sensor tiene bCountingEnabled (= terminaron las instrucciones) → EnsurePacer
EnsurePacer:     si PacerRef no es válido → SpawnPacer  (una sola vez, el ref es el candado)
SpawnPacer:      TargetPoint tag PacerSpawn → SpawnPacerAt → guarda PacerRef
   … el pacer corre solo 5 ciclos de 12 s y al terminar llama …
PacerFinished()  →  BreathComplete  →  StageDone  →  FinishStage  →  ForceComplete
```
- **`CheckBreathHit` cambió de `bStageComplete` a `bCountingEnabled`**: ya no pregunta *"¿terminó de respirar?"* sino *"¿arrancó el ejercicio?"*.
- **`PacerRef` es un `Actor` pelado, sin cast** — no hace falta más que `IsValid` + `DestroyActor`, y así se esquiva que `CastToBP_BreathPacer` no exista en el registro (ver la trampa en el tracker del pacer).
- **`CleanupPacer`** se sumó al final de `CleanupEntering`: instrucciones + sensor + caja + **pacer**, cero residuos.
- 🔴 **Si falta el `TP_PacerSpawn`**, se loguea `ENTERING: FALTA el TargetPoint PacerSpawn en la sala - sin ritmo guiado` y la etapa **igual cierra** por el cortafuegos de 240 s. Sin callejón sin salida.

### 2. El auto-cierre del sensor quedó APAGADO (no borrado)
`BP_BreathSensor_V2.UpdateBreathCount` llamaba `CompleteBreathStage()` al llegar a `MaxBreathCount` — eso **escondía el sensor y lo apagaba**, que es justo lo que el guión ya no quiere. Ahora llama **`MaybeCompleteBreath()`**, gateada por la variable nueva **`bAutoComplete` (default `false`)**.
👉 El conteo **sigue vivo** (el log `SN 3: Respiracion N/5` y el pulso háptico por respiración sostenida son buen feedback), pero **ya no cierra nada**. Con `bAutoComplete=true` vuelve el comportamiento viejo, para el test aislado de Breath.
⚠ `MaxBreathCount` estaba en **1** en el CDO (no en 5 como decía este tracker) — corregido a 5, que ahora es sólo el denominador del log.

### 3. Cortafuegos de página en [[BP_Instructions]]: 20 s
- Variables nuevas: **`PageT`** (reloj de la página, reseteado en `GotoPage`) y **`PageTimeout`** (20 s).
- **`PageFirewall(Δ)`** se insertó en el Tick **entre `SetTriggerProgress` y el switch de páginas** (cirugía, sin tocar la lógica existente) → al pasar el timeout llama **`ForcePage`**, que replica el salto normal de cada página (0→2 · 1→2 · 2→3 · 3→4 · 4→`ForceEndPages`).
- ⚠ **La página 2 es la calibración**: forzarla deja el sensor SIN calibrar, así que el umbral puede no engancharse y el objeto no reaccione. Es deliberado — 20 s atascado y seguir es mejor que atascado para siempre — pero **es la página donde el cortafuegos más se nota**; si en visor se dispara seguido, subir su timeout antes que bajar `CalHold`.
- 🐛 **Trampa pagada:** los literales enteros de `(CallFunction|GotoPage 2)` **se perdieron en el write** y las 4 ramas quedaron en `GotoPage(0)` — el cortafuegos habría devuelto al usuario a la primera página para siempre. **Lo cazó el `read_graph_dsl`**; arreglado por `set_pin_value`. Es la trampa #4 de `dsl.md` (que estaba documentada para strings) **también con enteros**.

## Cómo corre (el ciclo)
```
DIRECTOR SpawnStage → (índice 1) → SpawnEnteringOrBase → SpawnEnteringStage
BeginStage (heredado) → timer RunStage a InstructionsTime
EventRunStage (override por add_event) → EnteringRunBody:
    · ExtendTimeout(director, EnteringTimeout)   ← 🔴 el cortafuegos del director pasa de ~20 s a 240 s
    · SpawnInstructions (TargetPoint tag WidgetSpawn)
    · timer CheckBreathDone 0.5 s LOOP
BP_Instructions (autónomo, probado en visor):
    5 páginas → P2 spawnea BP_BreathSensor_V2 (tag SensorSpawn) → P5: StartBreathStage + SpawnBox (tag BoxSpawn) + self-destroy
CheckBreathDone → sensor válido → CheckBreathHit → bStageComplete → BreathComplete:
    ClearTimer + StageDone (heredado) → carga → FinishStage → ForceComplete
DIRECTOR KillStage → EventDestroyed → CleanupEntering (instrucciones + sensor + caja, con IsValid cada uno)
```
🔴 **El override de RunStage NO llama al parent** — a propósito: el RunStage base agenda `StageDone` por tiempo, y acá el cierre lo decide la respiración (o el cortafuegos).

## Registro de variables
| Variable | Default (CDO) | Rol |
|---|---|---|
| `EnteringTimeout` | **240 s** | A cuánto se extiende el cortafuegos del director (`ExtendTimeout`). La etapa real no entra en los ~20 s del placeholder: páginas (~30-60 s) + calibración (4.5 s) + 5 respiraciones sostenidas de 4 s. Subir si a Beltrán le falta tiempo. |
| `InstructionsRef` | — | El `BP_Instructions` spawneado (para el cleanup). El sensor y la caja se buscan por `GetActorOfClass` (los spawnea el widget, no la etapa). |

## Datos que gobiernan la mecánica (viven en OTROS assets)
- **`BP_BreathSensor_V2` CDO**: `MaxBreathCount` = **5** (🔴 estaba en **999** por las sesiones de captura de datos — la etapa jamás habría completado; corregido 2026-08-13). `ContinuousInhaleTime` = 4 s. `bCalibLog` = **false** (estaba true: spameaba una línea CSV por frame).
- **TargetPoints en `L_Persistent`**: `TP_BreathWidget` (**1350**,0,130 yaw180, tag `WidgetSpawn`) · `TP_BreathBox` (**1300**,0,120, tag `BoxSpawn`) — 🔴 **corregidos el 2026-08-13**: estaban en X=150/100 (coordenadas del modelo viejo con las salas apiladas en el origen) y la sala Entering vive en la parada X=1200 → **el widget nacía 10 m detrás del pawn y por eso Beltrán nunca lo vio en visor**. Ahora están 1.5 m / 1 m delante del centro de la sala. ⚠ Son anchors en mundo: si se arrastra la parada de Entering, moverlos con ella. · `TP_Sensor` (45,0,155, tag `SensorSpawn`) quedó en el Hall — es el sensor de mano del Hall; el de respiración ya no usa TargetPoint (se attachea a la mano, ver [[BP_BreathSensor_V2]] `ForceAttachToHand`).
- **Director**: `ExtendTimeout(Seconds)` = resetea el timer por nombre `"EndStage"` (los timers por nombre se RESETEAN al re-agendar con el mismo nombre). `SpawnStage` ramifica por índice vía `SpawnEnteringOrBase` (0=Hall, 1=Entering, resto=Base).

## Verificado por log (2026-08-13, run automático completo)
Entering spawnea instrucciones+timer, extiende el cortafuegos, el run (sin manos) queda en la página 1, el cortafuegos cierra a los 240 s con `CleanupEntering` limpio y la obra sigue hasta la disolución. Cero errores en el barrido doble.

## TODO
- [ ] 🔴 Test en visor (Beltrán): páginas con trigger → tomar el sensor de respiración → calibrar → 5 respiraciones → la etapa cierra SOLA por el camino real y se pasa a Recognizing.
- [ ] El sensor de respiración convive con los 2 `BP_Sensor` de mano del Hall (dos objetos en la mano). Unificarlos es trabajo futuro (§9.3: "la etapa le dice en qué convertirse").
- [ ] Reemplazar `Box_Breath` por el arte real de la sala Entering (anillos §3).
- [ ] Los textos del widget ya están en inglés ✓; el VO de Alma para esta sala, cuando exista.

## Relacionados
- [[BP_StageBase]] · [[BP_StageDirector]] (`ExtendTimeout`/`SpawnEnteringOrBase`) · `BP_BreathSensor_V2` · `Box_Breath` · memoria `instructions-widget`
