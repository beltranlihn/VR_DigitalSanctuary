# BP_TouchSensor — progress tracker

Sensor flotante del stage Touch (fase **R3** del brief [`docs/stages/touch-attracting.md`](../../../../docs/stages/touch-attracting.md)). El usuario **lo toca con la mano** y el sensor se le pega al mando: su mesh pasa a ser la herramienta visible y **enciende el beam de esa mano**. Es el gesto de "entrada" a la mecánica, en la línea de `BP_BrushTool` (Movement) y del sensor de Breath.

- **refPath**: `/Game/SoulCharger/Stages/Touch/BP_TouchSensor.BP_TouchSensor` · **parent**: Actor
- **in level**: **2 instancias** en `L_Touch` — `TouchSensor_Right` (`BP_TouchSensor_C_0`, `bIsRight=true`, en `(40, 22, 95)`) y `TouchSensor_Left` (`BP_TouchSensor_C_1`, `bIsRight=false`, en `(40, -22, 95)`).
- **Status**: 🟢 **PROBADO EN VISOR (2026-08-04) — funciona.** Queda ajustar posiciones/alcance sentado y el mesh definitivo.

## 🔴 La regla: cada sensor responde SOLO a su mano
El sensor izquierdo **solo** se toma con la mano izquierda y el derecho **solo** con la derecha. Tocar el sensor derecho con la izquierda **no hace nada** — no es "el primero que toca gana". Se implementa emparejando por `bIsRight`: el sensor cachea **únicamente** el `BP_AimBeam` cuyo `bIsRight` coincide con el suyo, y mide distancia solo contra ese.

## 🆕 2026-08-05 — el sensor es el dueño del BEAM
El usuario metió el Niagara **adentro de este BP** (componente `LineTrace`, sistema `/Game/SoulCharger/Stages/Touch/VFX/LineTrace`) y **funciona**: como el sensor se attachea a la mano al ser tomado, **el START del beam sale del componente y sigue la mano solo**, sin escribir ningún parámetro. Lo único que había que mapear era el **END**.
- 🔴 **El `Beam Start` del asset NO hay que tocarlo.** Es un valor literal y así funciona — el inicio lo da la **transform del componente**. Toda la teoría de "sale del origen del mundo" era falsa; venía de capturas del viewport del editor que resultaron no ser confiables (ver `toolsets.md`). **`User.Beam_Starts` sigue sin consumirse y no importa.**
- **El END se escribe por frame** desde `UpdateBeamEnd()` con `SetNiagaraVariable(**Position**)` sobre `"Beam_End"` (sin prefijo `User.`).
- Valores del componente afinados por el usuario y **que funcionan**: `Life = 218982`, `Spawn = 25.3`. No resetearlos.
- La geometría del rayo viene de **[`BP_HandPointer`](BP_HandPointer.md)**, que hace el line trace y publica `HitLocation`. División de tareas: el pointer **traza**, el sensor **dibuja**.

## Componentes (CDO)
- `DefaultSceneRoot`.
- 🆕 `LineTrace` (NiagaraComponent, sistema `VFX/LineTrace`) — el beam. Su transform **es** el origen del rayo.
- `Mesh` (StaticMesh esfera, radio 6 = **placeholder**, falta el mesh real de la herramienta). 🔴 **`collisionEnabled = NoCollision`, verificado en el valor efectivo.** Es obligatorio: una vez tomado, el sensor queda pegado **justo en el origen del line-trace del beam** — con colisión, el rayo se choca contra su propia herramienta y el hover se rompe. `CastShadow` off (Quest).

## Variables
- `bIsRight : bool` · **instance-editable** — de qué mano es este sensor. ⚠ Ver la trampa de abajo.
- `TakeRadius : float = 12` · instance-editable — a qué distancia (cm) de la mano se considera "tocado". Es la palanca de qué tan exigente es el gesto.
- `bTaken : bool` — ya fue tomado; apaga el chequeo.
- `BeamRef : BP_AimBeam` — el beam **de su propia mano**, cacheado en BeginPlay.
- 🆕 `PointerRef : BP_HandPointer` — el pointer **de su propia mano**, cacheado en BeginPlay. De ahí sale el `HitLocation` que alimenta el END del beam.

## Grafos
- **EventBeginPlay**: `CacheBeam()` → `CachePointer()`.
- **EventTick**: `UpdateBeamEnd()` → `if not bTaken → TryTake()`. El update del beam va **antes** del branch, así corre siempre.
- 🆕 **`CachePointer()`**: mismo patrón que `CacheBeam` pero sobre `BP_HandPointer_C`, emparejando por `bIsRight`. ⚠ No existe `Math|Boolean|Equal(Boolean)` como type_id → la igualdad de bools se arma con **`NOTBoolean(XORBoolean a b)`**.
- 🆕 **`UpdateBeamEnd()`** — decide a dónde apunta la punta del beam, con **prioridad a la burbuja agarrada**:
  ```
  IsValid(BeamRef)?
    ├─ sí → IsValid(BeamRef.GrabbedBubble)?
    │        ├─ sí → Beam_End = GetActorLocation(bubble)     ← centro de la esfera
    │        └─ no → IsValid(PointerRef) → Beam_End = PointerRef.HitLocation
    └─ no → IsValid(PointerRef) → Beam_End = PointerRef.HitLocation
  ```
  El estado de agarre lo sigue teniendo `BP_AimBeam` (`GrabbedBubble`); el sensor solo lo **lee** y no duplica lógica de grab.
  - 🔴 **Por qué con ramas de exec y NO con un `select`:** un `select` evalúa **las dos** opciones, así que `GetActorLocation(bubble)` correría también sin burbuja → `Accessed None` cada frame. Es el mismo bug que ya mordió en el Tick de `BP_AimBeam` con un `AND`. Las ramas cuestan dos nodos setter, pero es la forma correcta.
  - Las dos ramas "Is Not Valid" **convergen en el mismo `IsValid(PointerRef)`**: un pin de exec de entrada admite varias conexiones de salida, así no se duplica la cola.
- **`CacheBeam()`**: `GetAllActorsOfClass(BP_AimBeam_C)` → for-each → **se queda con el que tiene el mismo `bIsRight` que yo** → `BeamRef`.
- **`TryTake()`**: `IsValid(BeamRef)` → si `VectorLengthSquared(beam.AimSource.WorldLocation − MiLocation) < TakeRadius²` → `Take()`. **Distancia al cuadrado contra radio al cuadrado**: evita la raíz cuadrada y esquiva los type_ids con paréntesis (`Math|Vector|Distance(Vector)`) que rompen el parser del DSL.
- **`Take()`**: `AttachActorToComponent(Parent = beam.AimSource, Snap/Snap/KeepWorld)` → `bTaken = true` → `Class|BPAimBeam|Equip(beam, true)` → log → 🆕 **`Activate(LineTrace, bReset=true)`**.

## 🆕 El beam arranca APAGADO y lo enciende `Take()` (2026-08-05)
El componente `LineTrace` tiene **`bAutoActivate = false`**, así el sensor flota sin beam hasta que el usuario lo toma.
- 🔴 **Se gatea con `Activate(bReset=true)` / `Deactivate`, NUNCA con `SetVisibility`.** `SetVisibility(false)` oculta pero **no detiene la simulación**: el sistema sigue corriendo invisible, se consume sus partículas, y al mostrarlo no hay nada que dibujar. Ver `niagara-quest.md`.
- 🔴 **`bReset = true` es obligatorio.** Sin el reset, `Activate` sobre un sistema que ya "corrió" no re-spawnea nada.
- 🔴🔴 **Hubo que apagar `bAutoActivate` en las DOS INSTANCIAS del nivel, no solo en el CDO.** Unreal no propaga el default nuevo a actores ya serializados: el CDO quedó en `false` y las dos instancias seguían en `true`. Verificado con `get_properties` sobre `...BP_TouchSensor_C_0.LineTrace` y `_C_1.LineTrace`. Es el mismo caso de manual de "declarado ≠ aplicado" que ya mordió con `bIsRight`. **Al duplicar o recolocar sensores, revisarlo de nuevo.**

## Por qué por DISTANCIA y no por colisión
Chequear distancia en el Tick del sensor cuesta **2 actores × 1 distancia por frame** y **no toca `Core/` ni el pawn** (regla §7 del `CLAUDE.md`: pawn liviano, assets compartidos intocados). Ponerle colliders a las manos del pawn habría obligado a modificar un asset compartido entre stages.

## ⚠ Trampas
- 🔴 **`bIsRight` de las INSTANCIAS, no del CDO.** Unreal no propaga el default nuevo a actores ya serializados. Al colocar/duplicar sensores, **verificar el valor efectivo de cada instancia** con `get_properties` — es exactamente el bug que ya mordió con `BP_AimBeam`. Verificado 2026-08-04: `_C_0`=true, `_C_1`=false.
- 🔴 **`CollisionProfileName` NO aplica el perfil.** Setear `BodyInstance.collisionProfileName="NoCollision"` dejó `collisionEnabled` en `QueryAndPhysics`. Hay que setear **`collisionEnabled`** explícito. Caso de manual de "declarado ≠ aplicado".
- **No se suelta.** Una vez tomado queda hasta el cierre de la etapa. Si alguna vez hace falta soltar, hay que agregar el camino inverso (`DetachFromActor` + `Equip(false)` + `bTaken=false`).

## TODO / next
1. 🔴 **Test en visor**: al empezar no hay láser; acercás la mano derecha al sensor derecho → se pega y **se enciende solo el beam derecho**; la izquierda sigue apagada; tocar el derecho con la izquierda no hace nada.
2. **Ajustar posición y `TakeRadius` sentado** — hoy están a ojo en `(40, ±22, 95)`. Verificar que se alcanzan cómodo sin estirarse.
3. **Mesh real** de la herramienta (hoy esfera placeholder) + material unlit emisivo (Quest, ver `materials-vr.md`).
4. Evaluar si conviene que el sensor **flote/gire** suave antes de ser tomado, para leerse como "agarrable".

## Session log
- **2026-08-04:** creado. Componente Mesh (esfera 6, NoCollision), vars `bIsRight`/`TakeRadius`/`bTaken`/`BeamRef`, grafos `CacheBeam`/`TryTake`/`Take` + BeginPlay/Tick. 2 instancias colocadas en `L_Touch` con su `bIsRight` verificado. Compila y guardado. ✅ `Class|BPAimBeam|Equip` **sí resolvió** desde este BP sin reiniciar el editor (el gotcha del registro de nodos no mordió: el BP consumidor se creó DESPUÉS de compilar la función nueva en el beam).
