# Box_Breath — progress tracker

- **refPath**: `/Game/SoulCharger/Stages/Breath/Box_Breath.Box_Breath`  ·  **parent**: Actor  ·  **en nivel**: no (lo spawnea `BP_Instructions.SpawnBox` al terminar la página 5, sobre `TargetPoint` tag `BoxSpawn`)
- **Propósito**: consumidor tonto — mira `BP_BreathSensor_V2.bBreathing`/`bInhaling` y anima la escala de su componente `Box` (visualmente la esfera) entre dos tamaños fijos. No tiene lógica de detección propia.
- **Estado**: 🟢 funcionando, extendido 2026-07-20 para el fin de etapa.

## Variables
- `Sensor` (object ref a `BP_BreathSensor_V2`, cacheado en `BeginPlay` por `GetActorOfClass`+cast).
- `CurrentScale` / `TargetScale` (float, estado del interpolador).
- `InterpSpeed` (float, editable).

## Grafo
- **`EventBeginPlay`**: cachea `Sensor`.
- **`EventTick(DeltaSeconds)`**: `Target = bStageComplete(Sensor) ? 0.0 : ((bBreathing AND bInhaling) ? 3.0 : 1.0)` → `CurrentScale = FInterpTo(CurrentScale, Target, DT, InterpSpeed)` → aplica a `Box.RelativeScale3D` (si `Sensor` es válido).

## Cambio 2026-07-20 — escala a 0 al completar la etapa
Se insertó un segundo `Select` (cirugía de nodos, no reescritura) ENTRE el select original (`bBreathing AND bInhaling` → 3.0/1.0) y sus dos consumidores (`SetTargetScale` y el `Target` de `FInterpTo`): `Select_2 = bStageComplete ? 0.0 : Select_1_original`. `bStageComplete` tiene prioridad — apenas el sensor completa la etapa, la esfera empieza a interpolar hacia 0 sin importar el estado de respiración.

## Session log
- 2026-07-20: primer tracker de este BP + cambio de escala-a-0 al completar la etapa de respiración (ver `BP_BreathSensor_V2.md` / `BP_BreathStageManager.md`).
