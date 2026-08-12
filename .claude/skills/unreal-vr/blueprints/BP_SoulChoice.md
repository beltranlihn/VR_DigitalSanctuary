# BP_SoulChoice — la elección de Proto Soul (Core/Amoeba/)

## Purpose
§3 escena 3 (Hall): **las Proto Souls aparecen frente al usuario y la que elige es la que queda.** Este actor spawnea las candidatas, detecta la elección y la **persiste**.

Pedido textual de Beltrán (2026-08-11): *"Los proto soul aparecen con target point frente al usuario, y la que elija el usuario es la que queda. Así que tienen que quedar armados para poder visualizarlos con distinto mesh y material."*

## Status
🟡 **Reconstruida la cadena de elección (2026-08-13)** — ver el post-mortem de abajo: la cadena `CheckHand` NUNCA COMPILÓ desde la cirugía de capas del 2026-08-12, así que **la elección por toque jamás corrió en visor**. Arreglada + armado con manos despejadas + candidatas 1.6×. ⬜ Falta el test en visor del toque deliberado.

## 🔴 Composición por TargetPoint: se autora en el viewport, no en Blueprint
`GetAllActorsOfClassWithTag(TargetPoint, "SoulSpawn")` → una candidata por punto.
👉 **Para cambiar cuántas hay o dónde flotan se mueven o duplican TargetPoints. No se toca ningún Blueprint.**
**Arco actual (2026-08-13, movido para entrar en el FOV sentado):** radio **80 cm**, ángulos **0/±22/±44°**, z=105 — antes estaba a ±70° y las puntas quedaban al costado de los hombros, fuera de vista (fue el "no habían 5" del test de Beltrán). TargetPoint_0/_1/_2/_10/_11 en L_Persistent.

## Las variantes son DATOS: 3 arrays paralelos
| Variable | Default | Rol |
|---|---|---|
| `VariantMeshes` | 5 nulos | Un mesh por variante. Nulo = queda la esfera de `BP_ProtoSoul`. |
| `VariantMaterials` | 5 nulos | Ídem con el material. |
| `VariantColors` | teal/ámbar/violeta/rosa/cian | 🔴 **Es el array que manda:** `IsValidIndex` sobre **este** decide si la candidata se configura. |
| `PickRadius` | 18 cm | Qué tan cerca hay que poner la mano. |
| `bSpawnOnBeginPlay` | true (CDO) | El Hall spawnea este actor y las candidatas nacen del `MaybeSpawn` del BeginPlay. |
| `bPickArmed` | false al spawn | Gate de `TryPick`; lo arma `ArmPick`. |
| `bHandsNear` | — (transient) | Scratch del barrido de armado (`ArmScan`/`MarkNearBody`). |

⚠ **Los 3 arrays tienen que tener el mismo largo.**

## El ciclo de armado (2026-08-13) — manos despejadas o no se arma
`SpawnCandidates` → timer **`ArmPickTry`** a 1.2 s →
- `ArmPickTry`: si `HandR` no es válida (Simulate/auto-run) → `ArmPick` directo; si es válida → `ArmScan`.
- `ArmScan`: `bHandsNear=false` → `MarkIfNear` por candidata (IsValid → `MarkNearBody`: distancia² de CADA mano contra `(PickRadius²)·2.25` = radio ×1.5) → si alguna mano está adentro, **reintenta `ArmPickTry` a 0.3 s**; si están despejadas → `ArmPick`.
- `ArmPick`: `bPickArmed=true` + log `eleccion armada - ya se puede tocar`.
👉 Elimina ESTRUCTURALMENTE la elección accidental: no importa dónde estén los TargetPoints ni la mano, la elección solo se arma con las manos fuera de todas las zonas.
⚠ Al construirlo mordió el gotcha nuevo del DSL: **`(if cond A B)` salió encadenado** (then→SetTimer→ArmPick, else→nada) **y el read lo mostraba bien** — la rama false era un dead-end silencioso (ArmPickTry corría una vez y moría sin log). Fix por cirugía + regla en `gotchas.md`: verificar todo Branch escrito por DSL con `get_node_infos`. También hay un print de diagnóstico `ArmPickTry corre` que quedó a propósito (barato y delata el ciclo).

## Estructura de grafos (resto)
- **`BeginPlay`** — `CacheHud` · `CacheHands` · `MaybeSpawn` (el print duplicado de "buscando TargetPoints" se quitó el 2026-08-13).
- **`SpawnOne`** — spawn en el transform del TP → cast → **`SetActorScale3D(1.6)`** (2026-08-13: candidata 22 cm vs sensor 12 cm, para que no se confundan) → `ConfigureSpawned` → incremento del índice AL FINAL.
- **`Tick`** → `(not bChosen)` → `TryPick` → `(bPickArmed)` → `TryPickBody` → IsValid(HandR) → `ScanCandidates` → `CheckCandidate` (una llamada por mano) → `CheckHand` (¿bChosen? corta) → `CheckHandDist` (IsValid C) → `CheckHandHit` (dist² < r² → `Choose`).
- **`Choose(C)`** → guard `bChosen` → `DoChoose`: SetChosen → print VariantId → SaveChoice → TellHud → DestroyCandidates.

## 🐛🔴🔴 POST-MORTEM (2026-08-13): la cadena de elección NUNCA COMPILÓ — "tampoco pude elegir" era literal
La cirugía de capas del 2026-08-12 declaró los params `H` de `CheckHand/CheckHandDist/CheckHandHit` como **MotionControllerComponent**, pero las variables `HandR/HandL` son **SceneComponent** → 4 errores `Can't connect pins` → **el BP quedó sin compilar** y la elección por toque estuvo muerta en todos los tests de Beltrán. No se detectó porque:
1. El **run automático no tiene manos** → el camino muerto jamás se ejercitó.
2. 🔴 **Nunca se corrió `compile_blueprint` explícito después de la última cirugía de params** — la lección: **cirugía de params/tipos SIEMPRE termina en compile explícito**, no basta con que el run ande.
**Fix:** params retipados a SceneComponent. ⚠ Trampas del retipado que costaron ~10 llamadas:
- `remove_function_param` + `add_object_function_param "H"` → el nombre "H" queda RESERVADO para siempre y el param nuevo nace **"H1"**. No pelearlo: el nombre es cosmético.
- Los **nodos de llamada NO se reconstruyen** al cambiar la firma: conservan el pin viejo (tipo viejo) con sus conexiones → los errores persisten. El fix real es **borrar y recrear los 4 nodos de llamada** (`create_node "CallFunction|<Fn>"`) y recablear.

## 🐛 Historial (2026-08-12, ver git para el detalle)
- Off-by-one de `SpawnIndex` (getter puro se evalúa al consumir) → incremento al final.
- Ciclo de exec por FAN-IN (~300k spawns, editor congelado 5 min) → tras cirugía exec, verificar UNA entrada por `execute`.
- 3 pending-kill: CheckHand sobre candidatas destruidas (capas), print tras destroy (reordenado), elección accidental al spawn (bPickArmed 1.2 s — hoy reemplazado por el ciclo de manos despejadas).
- Barrido de errores: correr `"Accessed None"` **y** `"not valid"`.

## Por qué Beltrán "veía una sola proto ameba" (resuelto 2026-08-13)
1. El arco a ±70° dejaba 4 de las 5 fuera del FOV sentado → veía solo la central.
2. **El sensor usaba la MISMA esfera + `M_ProtoSoul`** (0.12 vs 0.14 de escala) → indistinguible de una ameba; la "ameba fijada al HUD" era el 2º sensor attacheado a su otra mano. Fix: **`MI_Sensor`** (Core/Sensor/, blanco tibio, Brightness 0.55, Agitation 0.06) + candidatas 1.6×.

## TODO
- [ ] 🔴 Test en visor: ver las 5 en el arco, tocar UNA deliberadamente tras `eleccion armada`, HUD naciendo con su color.
- [ ] Meshes/materiales reales por variante · retorno sensorial de la elección (§3).
- [ ] Mover los TargetPoints al Hall cuando exista su .umap con arte.

## Relacionados
- [[BP_ProtoSoul]] · [[BP_SoulState]] · [[BP_Sensor]] (MI_Sensor, la distinción visual) · [[BP_Stage_Hall]]
