# BP_SoulChoice — la elección de Proto Soul (Core/Amoeba/)

## Purpose
§3 escena 3 (Hall): **las Proto Souls aparecen frente al usuario y la que elige es la que queda.** Este actor spawnea las candidatas, detecta la elección y la **persiste**.

Pedido textual de Beltrán (2026-08-11): *"Los proto soul aparecen con target point frente al usuario, y la que elija el usuario es la que queda. Así que tienen que quedar armados para poder visualizarlos con distinto mesh y material."*

## Status
🟡 **Construido y spawneando** (2026-08-11), con **1 bug conocido sin arreglar en disco** (ver abajo). ⬜ Sin test en visor, sin higiene de nodos.

## 🔴 Composición por TargetPoint: se autora en el viewport, no en Blueprint
Patrón copiado de `BP_AttractDirector` (Touch), que ya lo tenía probado: `GetAllActorsOfClassWithTag(TargetPoint, "SoulSpawn")` → una candidata por punto.
👉 **Para cambiar cuántas hay o dónde flotan se mueven o duplican TargetPoints. No se toca ningún Blueprint.**
Hoy hay 3 en `L_Persistent` en `(45, ±30, 100)`, puestos a ojo **para que las manos lleguen sentado** (el gesto es por proximidad, así que el alcance del brazo es la restricción real). Su lugar definitivo es el Hall.

## Las variantes son DATOS: 3 arrays paralelos
| Variable | Default | Rol |
|---|---|---|
| `VariantMeshes` | 3 nulos | Un mesh por variante. **Nulo = queda la esfera** de `BP_ProtoSoul` (su `ApplyVariant` guarda con `IsValid`), así que un placeholder nunca desaparece. |
| `VariantMaterials` | 3 nulos | Ídem con el material. |
| `VariantColors` | teal / ámbar / violeta | 🔴 **Es el array que manda:** `IsValidIndex` sobre **este** decide si la candidata se configura. Hoy las 3 se distinguen **sólo por color**. |
| `PickRadius` | 18 cm | Qué tan cerca hay que poner la mano. Menor que la separación entre candidatas (30 cm) **a propósito**, o las zonas se pisan. |
| `bSpawnOnBeginPlay` | true (CDO) · **false en la instancia** | 🆕 Gate para **apagar la elección mientras se prueba la caminata**. Las candidatas viven en el nivel persistente y todas las salas están en el origen, así que aparecen en **todas** las salas y ensucian el test del paso 1. Prenderlo en el actor de `L_Persistent` para probar la elección. |

⚠ **Los 3 arrays tienen que tener el mismo largo.** `ConfigureFrom` indexa los tres con el mismo índice y sólo chequea el de colores; si `VariantMeshes` queda más corto, el `Get` se va de rango (log de error + null).

## Estructura de grafos
- **`BeginPlay`** — `CacheHud` · `CacheHands` · `SpawnCandidates`.
- **`CacheHud`** → recorre todas las `BP_ProtoSoul` y se queda con la que tiene **`bIsHUD`**. 🔴 **No es `GetActorOfClass`**: después del spawn hay 4 amebas en el mundo y "la primera" puede ser una candidata.
- **`CacheHands`** → castea el pawn y toma **los dos** motion controllers (pose *Grip*), con los accesores que ya expone `BP_VRPawn_SC`. No hay que tocar `Core/Pawn/`.
- **`SpawnCandidates`** → ForEach sobre los TargetPoints → `SpawnOne`.
- **`SpawnOne`** → spawnea, castea, `ConfigureSpawned(soul, idx)`.
- **`ConfigureSpawned`** → la agrega a `Candidates` y, si el índice es válido, `ConfigureFrom`.
- **`ConfigureFrom`** → llama **`ConfigureVariant` de la candidata** (mesh + material + color + `VariantId`).
- **`Tick`** → si no hay elección → `TryPick`.
- **`TryPick`** → si `HandR` es válida → `ScanCandidates`; si no, **reintenta `CacheHands`** (en Simulate no hay pawn, así que no hace nada y no ensucia el log).
- **`CheckHand(C, H)`** → **distancia al cuadrado contra radio al cuadrado** (misma receta que `BP_Sensor`). Se llama dos veces por candidata, una por mano.
- **`Choose(C)`** → 🔴 **guarda contra doble elección**: las dos manos pueden entrar en el mismo frame, así que `Choose` chequea `bChosen` y sólo la primera pasa a `DoChoose`.
- **`DoChoose(C)`** → `SaveChoice` (al GameInstance) → `TellHud` → `DestroyCandidates` → log. **En ese orden**: el HUD tiene que poder leer el estado ya escrito.
- **`SaveChoice` / `SaveStep`** → castea el GameInstance a [[BP_SoulState]] y le pasa el `VariantId`, el mesh, el material y el color de la elegida.
- **`TellHud`** → `AdoptFromState` sobre la ameba HUD. 💡 **La elegida no se convierte en el HUD: el HUD ADOPTA su identidad** y las 3 candidatas se destruyen. Así hay **un solo** actor de HUD en toda la obra (el del lazy-follow), y la elección sobrevive a los cambios de nivel por el GameInstance.

## 🐛 ✅ ARREGLADO (2026-08-12) — off-by-one en `SpawnOne`
`SpawnIndex` se incrementaba **antes** de usarse. Y como el getter es un **nodo puro que se evalúa en el momento de cada consumidor**, `ConfigureSpawned` recibe **1, 2, 3** en vez de 0, 1, 2 → la tercera candidata no se configura (`IsValidIndex` de un array de 3 falla en el 3) y **queda sin color**.
**Síntoma en el log:** 3 `SOUL: ameba lista` pero sólo **2** `SOULCHOICE: candidata configurada`.
**Arreglo aplicado (2 `connect_pins`):** `Entry.then → SpawnActor.execute` y `ConfigureSpawned.then → SetSpawnIndex.execute` — el incremento quedó **al final**. Conectar a un input ya conectado lo **reemplaza**, así que eso solo desarmó la cadena vieja.

🔴 **La lección general, que es más grande que este bug:** `(bind _x (Variables|Default|GetAlgo))` **no saca una foto** — nombra el nodo, y el valor se lee cuando cada consumidor lo pide. Si la variable cambia en el medio de la función, los consumidores de después ven el valor **nuevo**. Para un contador, o se incrementa al final, o se copia a una variable local.

## TODO
- [x] ~~El off-by-one~~ · ~~higiene de nodos~~ · ~~`CacheSoul` de `BP_SelfTest` agarrando una candidata en vez del HUD~~ (2026-08-12: ahora filtra por `bIsHUD`, igual que `CacheHud`).
- [ ] Aserciones en [[BP_SelfTest]]: 3 candidatas con `VariantId` distintos. ⚠ Van con `Skip` si `bSpawnOnBeginPlay` está apagado.
- [ ] Test en visor: prender `bSpawnOnBeginPlay` y acercar la mano a menos de 18 cm de una de las tres.
- [ ] Mover los TargetPoints al Hall cuando exista.
- [ ] Los meshes y materiales reales por variante (hoy sólo cambia el color).
- [ ] Que la elección tenga **retorno sensorial** (§3): hoy la candidata desaparece y listo.

## Relacionados
- [[BP_ProtoSoul]] (`ConfigureVariant` / `AdoptFromState`) · [[BP_SoulState]] (donde se guarda) · `BP_AttractDirector` (el patrón de spawn por TargetPoint) · [[BP_Sensor]] (la receta de detección por distancia)
