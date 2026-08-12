# BP_Stage_Hall — la etapa del Hall (Core/Stages/, hijo de BP_StageBase)

## Purpose
§3 escena 3: **Alma te recibe y eliges tu Proto Soul.** Primera subclase real de [[BP_StageBase]] (paso 4 del §10): sobreescribe `RunStage` y demuestra el patrón que van a seguir las 5 etapas. Acá **nacen** los objetos persistentes que antes vivían colocados: el **HUD ProtoSoul**, los **2 sensores** y la **elección** — nada existe antes de su momento (§9.1.b).

## Status
🟡 **Recorrido completo verificado por log (2026-08-12)**: HUD + 2 sensores + 3 candidatas spawneados al entrar, cierre por cortafuegos con limpieza total. ⬜ Falta el camino de ELECCIÓN real en visor (necesita manos) y el test de que el HUD siga la mirada.

## 🔴 El override de RunStage — cómo se hace por MCP
`add_function_graph("RunStage")` **falla**: *"inherited event-shape function; must be placed as an event node"*. La receta: **`add_event(blueprint, "RunStage")`** crea el nodo de evento override en el EventGraph, y su cuerpo va en una función (`HallRunBody`) conectada por cirugía (1 `connect_pins`). El timer `"RunStage"` de `BeginStage` (por nombre) **resuelve al override del hijo** — polimorfismo por `SetTimerByFunctionName` verificado.

## Ciclo de vida (v2, 2026-08-12 — LA NARRATIVA DEL GUION, pedida por Beltrán)
*"Al entrar al hall nos recibe Alma, nos explica con voiceover, nos escanea, y nos invita a elegir. Aparecen 5 protosouls alrededor; la que toquemos nos sigue en el HUD."*
```
RunStage (override) → HallRunBody:
    "entras al hall - Alma te recibe" · SpawnAlma (BP_Alma en TP_Alma, tag AlmaSpawn, (170,0,130))
    "ALMA: bienvenida + explica la experiencia (VO placeholder)" · timer HallScan a WelcomeTime (4 s)
HallScan:   "ALMA: te escanea (placeholder)" · nacen los 2 sensores (TP_SensorL/R) · timer HallInvite a ScanTime (4 s)
HallInvite: "ALMA: elige tu Proto Soul" · SpawnChoice → 5 candidatas en ARCO (TP_Soul1..5, radio 65 cm, ±70°) · poll CheckChoice
CheckChoice → bChosen → ChoiceDone: ClearTimer · "nace tu HUD" · SpawnHudSoul (el HUD nace RECIÉN al elegir y adopta
             la identidad desde el GameInstance vía AdoptFromState en su BeginPlay) · CleanupChoice · StageDone()
EventDestroyed → CleanupChoice   ← el CORTAFUEGOS (timeout): destruye elección + candidatas + Alma
CleanupChoice → CleanupAlma (incondicional) · IsValid(choice) → KillCandidates · DestroyActor(choice)
```
- `WelcomeTime`/`ScanTime` instance-editable (4 s placeholder de VO; el tempo real llega con la grabación).
- `HallDuration` del director subió a **30 s** (cortafuegos a 36 s) para dar tiempo de elegir en visor.
- Las **5 variantes** son datos en el CDO de `BP_SoulChoice`: colores teal/ámbar/violeta/rosa/cian, meshes y materiales nulos (llegan con el arte).
- 🔴 **El HUD y los 2 sensores NO se destruyen**: persistentes de §9.3. El HUD ya no existe antes de elegir — nace CON la elección.
- **BP_Alma** (Core/Amoeba/): placeholder — esfera unlit cálida de 35 cm (M_ProtoSoul, SoulColor (1, .82, .55)), sin colisión. La entidad real llega con arte + VO.

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
