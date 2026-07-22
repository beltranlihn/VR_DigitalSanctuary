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

## Cambio 2026-07-22 — escala 1↔2 + material emisivo/opacidad que pulsa con la respiración
- **Escala:** el pico de inhalación pasó de **3.0 → 2.0** (nodo `MakeLiteralFloat` que alimenta el `Select_0.Option1`, cambiado por `set_pin_value`). Ahora anima entre **1.0 (base) y 2.0 (inhalación)**.
- **Material nuevo `M_BreathSphere`** (`Stages/Breath/`): Translucent + **Unlit** + TwoSided (Quest-correcto, ver `references/materials-vr.md`). Params: `Color` (vector, default blanco) × `EmissiveIntensity` (scalar) → Emissive; `Opacity` (scalar) → Opacity. Asignado como override[0] del componente `Box`.
- **Vars nuevas:** `GlowT` (float, estado del interpolador 0→1) · `GlowInterpSpeed` (float, default 5.0).
- **Función `UpdateGlow(DT)`** (nueva): `target = bStageComplete ? 0 : (bBreathing AND bInhaling ? 1 : 0)` → `GlowT = FInterpTo(GlowT, target, DT, GlowInterpSpeed)` → setea en el material del `Box` (vía `SetScalarParameterValueOnMaterials`): **`Opacity = GlowT`** y **`EmissiveIntensity = GlowT × 20`**. Un solo interpolador maneja opacidad y emisividad. Inhalación → opaco+brilla (opacidad 1, emisivo 20); exhalación → invisible+apagado (0/0); suave por FInterpTo.
- **Cirugía en tick:** `CallFunction|UpdateGlow` insertado DESPUÉS de `SetRelativeScale3D` (su `then` estaba libre); `DT ← DeltaSeconds` del EventTick. El grafo de escala quedó intacto. Getters cross-BP del sensor = `Class|BPBreathSensorV2|GetStageComplete/GetInhaling/GetBreathing` (bool sin la 'b'; el `|Getb...` del reader NO es escribible).
- ⚠ **Glow real (halo/bloom) del emisivo 20 depende de `r.MobileHDR=True`** — con MobileHDR=False (default de plantilla) en el device se ve brillante pero sin halo (en editor/Link glowea porque usa renderer de escritorio). Config aparte.
- **Valores finales (ajustados por el usuario):** escala **0.5↔1.5**; `Color` = azul (0, 0.35, 1.0); **opacidad `= 0.2 + GlowT×0.8`** (piso 0.2, techo 1.0); **emisividad `= 1 + GlowT×19`** (piso 1, techo 20).

## Fase 2 (2026-07-22) — sistema Niagara de partículas por exhalación
- **`NS_BreathParticles`** (`Stages/Breath/`, creado por subagente): **CPU sim**, 1 emitter sprite. Esfera radio 30, velocidad radial **outward** 200 u/s, vida 1.5s con fade (ScaleColor del template Fountain). Material `DefaultSpriteMaterial` del engine (ajustable). Sin scalability High/Epic (corre en Low/Medium de Android). ⚠ El template Fountain trae **GravityForce/Drag** — si no querés que las partículas caigan, poné Gravity a 0 en ese módulo.
- **Spawn rate por User Parameter `User.SpawnRate`** (float, default 0). 🔴 Desde Blueprint hay que pasarlo **con el prefijo `User.`** (nombre exacto `"User.SpawnRate"`) o se crea un param fantasma silencioso.
- **Componente `BreathParticles`** (NiagaraComponent) agregado a Box_Breath, `Asset = NS_BreathParticles`. En el origen del actor (no adjunto al `Box` que escala).
- **Var nueva:** `SpawnRateMax` (float, default 60) — la intensidad de partículas en exhalación.
- **Función `UpdateParticles()`** (nueva, sin params): `active = bBreathing AND (NOT bInhaling) AND (NOT bStageComplete)` → `User.SpawnRate = active ? SpawnRateMax : 0` vía `Niagara|SetNiagaraVariable(Float)`. O sea: **exhalación dentro del umbral → partículas salen; inhalación / fuera de umbral / etapa completa → 0.** (Complementa el glow, que es al revés: brilla al inhalar.)
- **Cirugía en tick:** `CallFunction|UpdateParticles` insertado DESPUÉS de `UpdateGlow` (`UpdateGlow.then → UpdateParticles.execute`, sin params).

## Session log
- 2026-07-20: primer tracker de este BP + cambio de escala-a-0 al completar la etapa de respiración (ver `BP_BreathSensor_V2.md` / `BP_BreathStageManager.md`).
- 2026-07-22: escala 1↔2 + material emisivo/opacidad (`M_BreathSphere`) que pulsa con la respiración vía `UpdateGlow`.
