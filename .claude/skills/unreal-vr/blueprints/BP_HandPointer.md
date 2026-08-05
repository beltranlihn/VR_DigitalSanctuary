# BP_HandPointer — progress tracker

Puntero de mano del stage Touch. **Arranque limpio (2026-08-05)**: se abandonó el intento de arreglar el visual de `BP_AimBeam` y se empezó de cero con un Blueprint mínimo, de una sola responsabilidad — **un line trace por canal que sale de la mano** — para tener una base sana sobre la que montar el beam después.

- **refPath**: `/Game/SoulCharger/Stages/Touch/BP_HandPointer.BP_HandPointer` · **parent**: Actor
- **in level**: **2 instancias** en `L_Touch` — `HandPointer_Right` (`BP_HandPointer_C_0`, `bIsRight=true`) y `HandPointer_Left` (`BP_HandPointer_C_1`, `bIsRight=false`). Valores efectivos verificados con `get_properties`.
- **Status**: 🟢 **El line trace FUNCIONA (verificado por el usuario, 2026-08-05).** 🟡 Falta verificar el mapeo del END del beam.

## 🔴 Quién dibuja: el pointer TRAZA, el sensor DIBUJA
El visual **no vive acá**. El usuario metió el Niagara dentro de **[`BP_TouchSensor`](BP_TouchSensor.md)** (componente `LineTrace`) y, como ese actor se attachea a la mano, **el START del beam sale solo de la transform del componente** — no hay que escribir ningún parámetro de inicio. Este BP aporta la **geometría**: publica `HitLocation`, que el sensor lee cada frame y escribe en `Beam_End`.
> ⚠ Corolario para el futuro: si alguna vez el beam se muda acá, el patrón que funciona es **componente Niagara attacheado a la mano + escribir solo `Beam_End`**. No perseguir `Beam_Starts`: es un user parameter muerto del asset y no hace falta.

## Por qué existe (y por qué NO se siguió con BP_AimBeam)
`BP_AimBeam` funciona como **lógica** (apuntado, hover, far-grab, probado en visor el 2026-08-03), pero su visual Niagara nunca se pudo hacer ver. El asset `LineTrace` quedó dañado tras una tanda de ediciones (ver `BP_AimBeam.md` y `niagara-quest.md`). Este BP separa el problema: **primero el rayo geométrico correcto y visible por debug**, después el visual encima.

## Componentes
- Solo `DefaultSceneRoot`. **Sin MotionControllerComponent propio** — un MC en un actor del nivel **nunca trackea** (solo consulta si su actor tiene *local net owner*, cosa que solo cumple el Pawn). El actor se **attachea** al componente aim del pawn. Es la lección #1 de `BP_AimBeam.md`, respetada desde el día uno.

## Variables
- `bIsRight : bool` · **instance-editable**, default `true` — de qué mano es este puntero.
- `TraceDistance : float = 800` · instance-editable — largo del trace en cm.
- `AimSource : MotionControllerComponent` — el `MotionControllerRightAim`/`LeftAim` **del pawn**, cacheado en BeginPlay.
- `TraceStart : Vector` / `TraceEnd : Vector` — extremos del rayo de este frame. **Son la entrada natural del visual** que venga después.
- `bBlockingHit : bool` — hubo impacto este frame.
- `HitLocation : Vector` — punto de impacto si pegó; si no, `TraceEnd`. Así el consumidor tiene **siempre** un punto final válido sin ramificar.

## Grafos
- **EventBeginPlay** → `CacheAimSource()`.
- **EventTick** → `IsValid(AimSource)` → `DoTrace()`. El guard evita el `Accessed None` por frame si el cast falla.
- **`CacheAimSource()`**: `CastToBP_VRPawn_SC(GetPlayerPawn 0)` → según `bIsRight`, `AimSource = pawn.MotionControllerRightAim` o `MotionControllerLeftAim` → `AttachActorToComponent(AimSource, "None", Snap/Snap/KeepWorld, bWeld=false)`.
- **`DoTrace()`**:
  ```
  _src   = AimSource
  _start = GetWorldLocation(_src)
  _end   = _start + GetForwardVector(_src) * TraceDistance
  TraceStart = _start ; TraceEnd = _end
  (_outhit, _ret) = LineTraceByChannel(_start, _end, Visibility, DrawDebugType="ForOneFrame", bIgnoreSelf=true)
  bBlockingHit = _ret
  HitLocation  = select(_ret, BreakHitResult(_outhit).Location, _end)
  ```
  🔴 `DrawDebugType = ForOneFrame` es **lo que lo hace visible hoy**. Rojo = sin impacto, verde = con impacto (colores por defecto del nodo). **Al montar el visual definitivo hay que ponerlo en `None`** — el debug draw no se empaqueta bien y cuesta en Quest.

## ⚠ Trampas ya mordidas al construirlo
- 🔴 **`create_node("CallFunction|CacheAimSource")` agarró la función de OTRO Blueprint** (`BP_AimBeam` tiene una función con el mismo nombre) y creó un `Class|BPAimBeam|CacheAimSource`. **Fix: pasar `declaring_class` con la clase propia** (`.../BP_HandPointer.BP_HandPointer_C`). Verificar después con `get_node_infos`: el `type_id` real tiene que ser `|CacheAimSource` y el pin de target `Self Object Reference`. ⚠ `read_graph_dsl` **igual lo muestra como `Class|BPAimBeam|CacheAimSource`** aunque esté bien — es artefacto del read lossy, no confiar en esa etiqueta.
- **Una variable `bIsRight` genera los accesores `GetIsRight`/`SetIsRight`** (sin la `b`). El `(|GetbIsRight)` que imprime el read **no existe como type_id** para escribir.
- **`Math|Vector|vector*vector` / `vector+vector` no se pueden crear por type_id** (`find_node_types` no los devuelve). Usar el azúcar del DSL: `(* a b)` y `(+ a b)`, que resuelven a los `K2Node_PromotableOperator` correctos.
- **El EventGraph de un BP nuevo YA trae `EventBeginPlay`/`EventTick`/`ActorBeginOverlap` vacíos** → `write_graph_dsl` los DUPLICA. Se hizo cirugía de nodos sobre los existentes y se borró el `ActorBeginOverlap` que no se usa.
- **`BreakHitResult` no expone sus salidas por nombre en el DSL**: hay que destructurar en orden con `(bind (a b c d e) ...)`. El orden es `bBlockingHit, bInitialOverlap, Time, Distance, Location, …` → `Location` es el **índice 4**. Verificado leyendo la conexión real con `get_node_infos`.

## TODO / next
1. 🔴 **Test en visor**: la línea de debug tiene que salir de cada mano y seguirla; roja al aire, verde al pegarle a una burbuja.
2. Ajustar `TraceDistance` para el alcance sentado.
3. **Montar el visual encima** usando `TraceStart`/`HitLocation` como entradas. Antes de elegir Niagara, leer el historial de `BP_AimBeam.md` y el bloque de arriba de `niagara-quest.md` — el asset `LineTrace` está dañado y hay que reconstruirlo o reimportarlo limpio.
4. Cuando haya visual: `DrawDebugType = None`.
5. Decidir si este BP **absorbe** el rol de `BP_AimBeam` (hover + far-grab) o si queda solo como el rayo y `BP_AimBeam` lo consume.

## Session log
- **2026-08-05:** creado desde cero. Variables, `CacheAimSource`, `DoTrace` y el EventGraph por cirugía. Compila sin errores, guardado, 2 instancias colocadas en `L_Touch` con su `bIsRight` verificado.
