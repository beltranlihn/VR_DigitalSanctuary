# BP_Sensor — uno por mano, persistente (Core/Sensor/)

## Purpose
§9.3: **uno por mano, persistente.** Estado + malla que **se reconfigura por etapa**.
§9.7 define el refactor: *"`BP_TouchSensor` → `BP_Sensor` persistente. **No se toma en cada etapa; la etapa le dice en qué convertirse.**"*

🔴 **Ese es el cambio conceptual respecto de `BP_TouchSensor`.** El de Touch se toma una vez y se queda; este vive en el **nivel persistente**, sobrevive a las transiciones, y cada etapa lo **reconfigura** con `SetMode(n)`.

## Status
🟡 **Construido, compilando y verificado por el arnés** (2026-08-11): 2 sensores, exactamente 1 derecho, y los 2 cachearon su mano. ⬜ Falta test en visor y los meshes/materiales reales por modo.

## 🔴 Lo que se hereda de BP_TouchSensor (probado en visor, no reinventar)
Sacado de su tracker, que documenta 5 cosas que ya costaron tiempo:
1. **Emparejamiento por mano, y cada sensor responde SOLO a la suya.** No es "el primero que toca gana". Acá se resuelve leyendo el motion controller correspondiente del pawn.
2. **Detección por DISTANCIA, no por colisión.** Ponerle colliders a las manos obligaría a tocar el pawn, que es un asset compartido (regla §7 del `CLAUDE.md`: pawn liviano). Cuesta 2 distancias por frame.
3. 🔴 **Distancia AL CUADRADO contra radio al cuadrado.** Evita la raíz **y** esquiva `Math|Vector|Distance(Vector)`. Se usa `Math|Vector|VectorLengthSquared`.
4. 🔴 **`collisionEnabled = NoCollision` explícito.** Setear `collisionProfileName` **no aplica el perfil** — caso de manual de "declarado ≠ aplicado". Y es obligatorio: pegado a la mano, el sensor se interpone en el propio line-trace del puntero.
5. 🔴 **Los valores de las INSTANCIAS no heredan defaults nuevos del CDO.** Verificado acá con `get_properties`: `_C_0.bIsRight = true`, `_C_1.bIsRight = false`.
   ⚠ No existe **`Math|Boolean|Equal(Boolean)`**: si alguna vez hace falta comparar bools, es `NOT(XOR a b)`.

## 🔴 "La etapa le dice en qué convertirse" = DATOS, no código
| Variable | Tipo | Rol |
|---|---|---|
| `Mode` | int | El modo actual. **Índice** en los dos arrays de abajo. |
| `ModeMeshes` | Array&lt;StaticMesh&gt; | Un mesh por modo. |
| `ModeMaterials` | Array&lt;MaterialInterface&gt; | Un material por modo. |

**`SetMode(n)`** es la única API pública: guarda el modo y aplica mesh + material del índice. Agregar una etapa nueva es **agregar una entrada a los arrays**, no tocar el grafo.

🔴 **Ambos `Apply` chequean `IsValidIndex` antes de tocar nada.** Un modo sin entrada en el array **deja el mesh anterior** en lugar de dejar el sensor invisible. Es la misma decisión que en `BP_ProtoSoul`: un dato faltante no puede hacer desaparecer el objeto.

⚠ **`Mode` es un `int`, y §9.3 pide un ENUM.** No hay tool del MCP para crear un `UserDefinedEnum` (igual que con los structs), así que queda como int hasta que se cree el enum a mano en el editor. **Valores previstos:** 0 = libre/neutro, y después uno por etapa. Cuando exista el enum, cambiar el tipo y los arrays siguen sirviendo igual.

## Registro de variables (resto)
| Variable | Default | Rol |
|---|---|---|
| `bIsRight` | true | De qué mano es. 🔴 **Verificar por instancia.** |
| `TakeRadius` | 12 cm | Qué tan exigente es el gesto de tomarlo. |
| `bTakeEnabled` | true | Gate: la etapa puede deshabilitar que se tome. |
| `bTaken` | false | Ya está en la mano; apaga el chequeo. |
| `HandRef` | — | El `MotionControllerComponent` **de su propia mano**, cacheado del pawn. |

## 🆕 Modo CUALQUIER MANO — la mano hábil del §7 (2026-08-12, pedido de Beltrán)
*"La persona lo agarra con su mano hábil. Al tomarlo se pone en esa mano, y en la otra aparece el otro sensor automáticamente."*
- **`bAnyHand`** (instance-editable, false): en true, el sensor responde a **las dos manos**. `TickTake` ahora es un dispatcher: `bAnyHand → TickTakeAny` (cachea ambas manos vía `CacheBoth` + `CheckTakeHand(H, IsRightHand)` por mano) · si no → `TickTakeOwn` (el comportamiento clásico por `bIsRight`).
- Al tomar en modo any-hand: `HandRef = la mano que tocó`, **`bTookRight`** registra cuál fue, `bIsRight` se alinea, y `Take()` attachea. Log: `SENSOR: tomado con la DERECHA/IZQUIERDA - mano habil registrada`.
- El flujo completo vive en [[BP_Stage_Hall]]: spawn de UNO en `TP_Sensor` (tag `SensorSpawn`) → poll `bTaken` → al tomarlo, **el segundo se spawnea y se attachea a la otra mano** (`SetIsRight(!TookRight)` → `CacheHand()` → `Take()`, "cerrado y dormido") y **`bRightHanded` se persiste en el GameInstance** (`BP_SoulState`).
- ⚠ Guion §7 pendiente: *"si nadie toma nada en N segundos, se asigna la derecha y se sigue"* — hoy el sensor no tomado simplemente **se destruye** al cerrar el Hall (cero residuos). El auto-asignar va con las etapas reales.

## Estructura de grafos
- **`BeginPlay`** — `CacheHand()` · `SetMode(Mode)` (aplica el modo autoral de entrada).
- **`Tick`** — si `bTakeEnabled` **y** no `bTaken` → `TickTake()`.
- **`CacheHand`** → castea el pawn a `BP_VRPawn_SC` y delega en `PickHand`.
- **`PickHand(Pawn)`** — `if bIsRight → GetMotionControllerRightGrip, else Left`. 💡 Usa los **accesores que ya existen** en el pawn (`references/assets-existentes.md`), así **no hay que tocar `Core/Pawn/`**.
  ⚠ Se usa la pose **Grip** (dónde está la mano), no **Aim** (el rayo). Para un objeto que se agarra, Grip es la correcta.
- **`TickTake`** — `IsValid(HandRef)` → `TryTake()`, y si no, **reintenta cachear**. Cubre el caso de que el pawn no exista todavía al BeginPlay, y en Simulate no hace nada ni ensucia el log.
- **`TryTake`** — distancia al cuadrado contra radio al cuadrado → `Take()`.
- **`Take`** — `bTaken = true` + `AttachActorToComponent(HandRef, Snap/Snap/KeepWorld)`.
- **`Release`** — 🆕 el camino inverso, que `BP_TouchSensor` **no tenía** (su tracker lo marca como pendiente). Acá es obligatorio: siendo persistente, entre etapas hay que poder soltarlo.

## Verificado por el arnés (`BP_SelfTest`, 2026-08-11)
```
TEST PASS: Sensor: hay exactamente 2 (uno por mano)
TEST PASS: Sensor: exactamente 1 es derecho (no los dos iguales)
TEST PASS: Sensor: los 2 cachearon su mano del pawn
```
💡 **La segunda es la que vale.** "Los dos quedaron con el mismo `bIsRight`" es el bug exacto que el tracker de Touch marca en rojo, y es invisible mirando el nivel. Ahora una corrida de PIE lo detecta.

## TODO
- [ ] 🔴 **Test en visor:** que cada mano tome **solo** su sensor, y que tocar el derecho con la izquierda **no haga nada**.
- [ ] Posición y `TakeRadius` **sentado**. Hoy están en `(−460, ±22, 95)` a ojo, sobre el umbral de entrada. Deberían quedar en el Hall, donde se toman por primera vez.
- [ ] Los **meshes y materiales por modo**. Hoy los arrays están vacíos, así que queda la esfera placeholder en todos los modos — que es el comportamiento correcto, no un bug.
- [ ] Crear el **`UserDefinedEnum`** a mano y cambiar `Mode` de int a ese tipo.
- [ ] 🔴 **El timbre del Center tiene que PARECERSE a esto** (§3): apoyar la mano para que te escanee es la misma gramática que tomar el sensor, y la rima solo se lee si se parecen visualmente.
- [ ] Que `BP_StageDirector` llame `SetMode` al entrar a cada etapa, y `Release` al cerrarla.

## Relacionados
- `BP_TouchSensor` (de donde sale el refactor, **probado en visor** — leer su tracker antes de tocar esto) · `BP_VRPawn_SC` (los accesores de mano) · [[BP_SelfTest]] · [[BP_StageDirector]]
