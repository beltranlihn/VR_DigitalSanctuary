# BP_Stage_Entering — la primera etapa REAL (Core/Stages/)

## Purpose
Paso 4 del §10: la primera subclase de [[BP_StageBase]] con mecánica de verdad — **la respiración de Breath integrada al ciclo de salas**. No reinventa nada: spawnea la cadena PROBADA EN VISOR de `Stages/Breath/` (`BP_Instructions` → widget de 5 páginas → `BP_BreathSensor_V2` → `Box_Breath`) y espera a que el sensor complete sus respiraciones para pedir el cierre por el camino real (`StageDone` → `FinishStage` → `ForceComplete`).

Pedido de Beltrán (2026-08-13): *"en la de breath ya tenemos el sensor, simplemente habría que integrarlo a la etapa, y habría que integrar el widget con las instrucciones... deja la etapa funcional con algún objeto que reaccione a la respiración, por ahora puedes dejar un cubo"* — el objeto reactivo es `Box_Breath`, que ya existía.

## Status
🟡 Construida y verificada por log en el ciclo completo (2026-08-13). ⬜ La respiración real necesita visor (el run automático no respira: cierra por cortafuegos extendido con limpieza total — verificado).

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
