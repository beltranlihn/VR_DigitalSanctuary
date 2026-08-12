# BP_Stage_Hall — la etapa del Hall (Core/Stages/, hijo de BP_StageBase)

## Purpose
§3 escena 3: **Alma te recibe y eliges tu Proto Soul.** Primera subclase real de [[BP_StageBase]] (paso 4 del §10): sobreescribe `RunStage` y demuestra el patrón que van a seguir las 5 etapas. Acá **nacen** los objetos persistentes que antes vivían colocados: el **HUD ProtoSoul**, los **2 sensores** y la **elección** — nada existe antes de su momento (§9.1.b).

## Status
🟡 **Recorrido completo verificado por log (2026-08-12)**: HUD + 2 sensores + 3 candidatas spawneados al entrar, cierre por cortafuegos con limpieza total. ⬜ Falta el camino de ELECCIÓN real en visor (necesita manos) y el test de que el HUD siga la mirada.

## 🔴 El override de RunStage — cómo se hace por MCP
`add_function_graph("RunStage")` **falla**: *"inherited event-shape function; must be placed as an event node"*. La receta: **`add_event(blueprint, "RunStage")`** crea el nodo de evento override en el EventGraph, y su cuerpo va en una función (`HallRunBody`) conectada por cirugía (1 `connect_pins`). El timer `"RunStage"` de `BeginStage` (por nombre) **resuelve al override del hijo** — polimorfismo por `SetTimerByFunctionName` verificado.

## Ciclo de vida
```
RunStage (override) → HallRunBody:
    print "Alma te recibe" · SpawnHallActors · timer CheckChoice 0.3s LOOP
SpawnHallActors → SpawnHudSoul (BP_ProtoSoul + SetIsHUD=true post-spawn: bIsHUD solo gatea el Tick, llega a tiempo)
               → SpawnSensorAt("SensorSpawnL", false) · SpawnSensorAt("SensorSpawnR", true)   ← TargetPoints TP_SensorL/R en (60, ∓25, 95)
               → SpawnChoice (BP_SoulChoice en el origen; su BeginPlay cachea el HUD recién nacido y spawnea las 3 candidatas)
CheckChoice (poll) → si ChoiceRef.bChosen → ChoiceDone: ClearTimer · CleanupChoice · StageDone() (heredado: carga → ForceComplete → autodestrucción)
EventDestroyed → CleanupChoice   ← cubre el CORTAFUEGOS del director (timeout sin elección): destruye la elección y sus candidatas
CleanupChoice → IsValid(ChoiceRef) → KillCandidates (ForEach GetCandidates → DestroyOne) · DestroyActor(choice)
```
🔴 **El HUD y los 2 sensores NO se destruyen**: son los persistentes de §9.3 — nacen acá y acompañan el resto de la obra.

## Verificado por log (2026-08-12, run 16:24)
Entrada al Hall → HUD nacido + 3× `candidata configurada` **en el mismo segundo** → sin elección (PIE sin manos) → cortafuegos a los 16 s (`CurDuration 10 + TimeoutMargin 6`) → `eleccion y candidatas destruidas - cero residuos` → la obra siguió las 5 etapas hasta la disolución. Cero `Accessed None`.

## 🔴🔴 El bug que costó dos congeladas de editor de ~5 min
El primer run del Hall congeló el editor: **~300.000 ProtoSouls spawneados en un frame** + 4 `Runaway loop detected`. No era de este BP: era un **ciclo de exec en `BP_SoulChoice.SpawnOne`** dejado por una cirugía anterior (los pines exec aceptan **fan-in**; el cable viejo nunca se rompió). Ver el gotcha nuevo en `gotchas.md` y el tracker de [[BP_SoulChoice]].

## TODO
- [ ] 🔴 Test en visor: elegir con la mano (camino `ChoiceDone` → `StageDone`), el HUD siguiendo la mirada, tomar los sensores.
- [ ] Alma (la guía) — actor propio `BP_Alma`, pendiente de diseño/VO.
- [ ] La calibración narrativa del Hall (baseline ya se toma en el corredor).
- [ ] Cuando exista la elección real en visor: aserciones de candidatas en `BP_SelfTest` (3 con `VariantId` distintos, con Skip si la obra no llegó al Hall).

## Relacionados
- [[BP_StageBase]] · [[BP_SoulChoice]] · [[BP_ProtoSoul]] · [[BP_Sensor]] · [[BP_StageDirector]] (`SpawnStage` ramifica: índice 0 → esta clase)
