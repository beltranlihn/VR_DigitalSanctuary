# BP_AimBeam — progress tracker

Beam de apuntado del stage Touch (Fase 1 del brief [`docs/stages/touch-attracting.md`](../../../../docs/stages/touch-attracting.md)). Actor del lado del mando (NO en el pawn): line-trace desde la pose *aim*, láser, y hover/unhover sobre objetos apuntables.

- **refPath**: `/Game/SoulCharger/Stages/Touch/BP_AimBeam.BP_AimBeam`  ·  **parent**: Actor  ·  **in level**: **2 instancias** en `L_Touch` — `AimBeam_Right` (`bIsRight`=true, `MotionSource`=RightAim) y `AimBeam_Left` (`bIsRight`=false, `MotionSource`=LeftAim). Se **attachean al pawn en BeginPlay**, no viven en el origen del mundo. (2026-08-03)
- **Status**: 🟢 **PROBADO EN VISOR (2026-08-03)** — apunta con las dos manos, hover, y far-grab con trigger sostenido. Falta fine tuning.

## ✅ Lo que hizo que funcionara (2026-08-03) — los 3 arreglos
1. **Tracking:** el beam **no tiene MotionControllerComponent propio** (uno en un actor del nivel **nunca trackea**: solo consulta si su actor tiene *local net owner*, cosa que se cumple en el Pawn). `CacheAimSource()` toma el `MotionControllerRightAim`/`LeftAim` **del pawn** según `bIsRight`.
2. **Input:** con **`IA_Shoot_Right`/`IA_Shoot_Left` del XRFramework** — 🔴 **`Started` → `TryGrab`** (corregido 2026-08-05, ver abajo), `Completed` → `TryRelease`. Inventar `IA_Attract_*` + `IMC_Touch` propios **no disparó nunca** pese a registrarse bien. Ver `assets-existentes.md`.
3. **`Accessed None` del Tick:** el `AND` de Blueprint evalúa las dos ramas, así que `ActorHasTag(HitActor)` se ejecutaba sin impacto, cada frame. Reemplazado por `ResolveHover(bHit, HitActor)` con ramas anidadas + `IsValid`.

**Visual:** beam **Niagara** `NS_TouchBeam` (duplicado de `NS_MenuLaser`) manejado por `User.PointArray` índice 0 = origen, 1 = impacto; más un componente `Cursor` (esfera, `NoCollision`) que se posiciona en `BeamEnd` y se oculta sin impacto. El `StaticMesh` de largo fijo se eliminó.

## Componentes (CDO)
- `DefaultSceneRoot` (SceneComponent) — raíz.
- `MC_RightAim` (MotionControllerComponent) — **MotionSource="RightAim"**. Su `GetForwardVector` = dirección del rayo (aim pose, +Y up/−Z fwd, ver `motion-controller-data.md`). Hijo del root.
- `Laser` (StaticMesh cilindro) — hijo de `MC_RightAim`. RelativeRotation Pitch 90, Location X+400, Scale (0.1,0.1,8) → beam fino ~800u hacia adelante. CastShadow off. ⚠ **orientación puesta a ojo, verificar/nudgear en visor**; falta material unlit emisivo (Quest, ver `materials-vr.md`). El line-trace lo ignora solo (`bIgnoreSelf=true`).

## Variables
- `TraceDistance` : float = 800 · instance-editable — largo del trace.
- `CurrentHovered` : Actor ref — qué se está apuntando ahora (público, lo leen los consumidores).

## Dispatchers (event dispatchers, sin params)
- `OnHoverBegin` — se dispara cuando `CurrentHovered` pasa a un nuevo apuntable.
- `OnHoverEnd` — se dispara cuando se deja de apuntar el anterior (se llama ANTES de cambiar `CurrentHovered`, así el que terminó ve `CurrentHovered==self`).
- **Patrón de consumo:** cada objeto apuntable se suscribe a ambos y chequea `beam.CurrentHovered == self` para saber si es él. (Burbujas en Fase 2, botón en Fase 8.)

## Funciones
- `SetHover(NewTarget: Actor)` — ✅ hecha. `if NewTarget != CurrentHovered` (NotEqual Object) → `CallOnHoverEnd` (el viejo aún es `CurrentHovered`) → `SetCurrentHovered(NewTarget)` → `CallOnHoverBegin`. Se llama con `NewTarget=null` para limpiar el hover.
- `ClearHover()` — creada pero **sin usar** (se reemplazó por `SetHover(null)`). Borrar en limpieza.

## Grafos
- **EventTick**: ✅ hecho. `mc=GetMCRightAim`; `start=GetWorldLocation(mc)`; `end=start + GetForwardVector(mc)*TraceDistance`; `LineTraceByChannel(start,end)` canal Visibility (`DrawDebugType=ForOneFrame` para test visual); `BreakHitResult(OutHit)` → `bBlockingHit`(idx0)+`HitActor`(idx9); `if (bBlockingHit AND HitActor.ActorHasTag("Aimable"))` → `SetHover(HitActor)`, else → `SetHover(null)`. **La llamada a la función usa `:NewTarget` keyword** (el positional se conecta al pin `self`, no al param).

## 🔴 Gotcha descubierto (2026-07-28): editor localizado rompe el DSL
El editor estaba en **español** → registro de nodos localizado (`Variables|Predeterminado|Obtener…`, `Utilidades|ControlDeFlujo|Rama`, `Colisión|LineTraceByChannel`…). El **DSL de la skill asume ids en inglés** y su azúcar `if`/`switch`/`for` cablea `Utilities|FlowControl|Branch` (inexistente localizado) → **cualquier grafo con branch es inescribible por `write_graph_dsl`**. **Decisión (usuario, 2026-07-28): cambiar Editor Language a English** para alinear con la skill. → Proponer una línea en `references/gotchas.md`: "mantener el editor en inglés; si está localizado, el DSL (sugar de control de flujo + ids de nodo) no resuelve."

Type_ids localizados descubiertos (por si se sigue en español): trace `Colisión|LineTraceByChannel` (Start/End, out OutHit+ReturnValue, `bIgnoreSelf=true` default), `Colisión|BreakHitResult` (out `HitActor` idx9), `Transformación|GetWorldLocation` / `GetForwardVector` (target=componente), `Actor|ActorHasTag`, `Predeterminado|CallOnHoverBegin/End`, `Utilidades|Operadores|Desiguala(==)` (NotEqual promotable), `Utilidades|ControlDeFlujo|Rama` (Condition→then/else).

## TODO / next
1. **Test en visor (PIE/Link):** apuntar el mando derecho al cubo `AimTarget_TestCube` → el line-trace debug (verde al impactar) confirma el hover; `CurrentHovered` pasa a ser el cubo. Verificar que el láser sale del mando (alineación con PlayerStart en origen).
2. **Reacción visible del target:** en Fase 2 la burbuja (`BP_SoundBubble`) se suscribe a `OnHoverBegin`/`OnHoverEnd` y chequea `beam.CurrentHovered == self` para reaccionar (preview de sonido + visual). El patrón de dispatchers ya está listo.
3. Material **unlit emisivo** para el láser (Quest, `materials-vr.md`); verificar/ajustar orientación del cilindro en visor (se puso a ojo, Pitch 90).
4. Quitar el `DrawDebugType=ForOneFrame` (dev-only) y `ClearHover()` sin uso antes de cerrar el stage.
5. Alineación robusta: hoy el beam se co-ubica con el PlayerStart (origen). Si el pawn se recentra/mueve, evaluar attachearlo al mando del pawn en BeginPlay (sin meter lógica en el pawn).

## Dos manos + anclaje al pawn + trigger sostenido — 2026-08-03

**Anclaje (arreglo del bug del origen del mundo).** `BeginPlay` ahora hace `Transformation|AttachActorToActor(GetPlayerPawn(0), SnapToTarget/SnapToTarget)` después del `EnableInput`. El beam pasa a vivir en el espacio de tracking del pawn → sobrevive al recentrado del guardian. Antes estaba clavado en (0,0,0) y solo funcionaba de casualidad porque el PlayerStart también estaba ahí.

**Pose correcta — confirmado contra documentación (2026-08-03).** `MotionSource` Aim + `GetForwardVector` **es lo correcto**; no hay bug de ejes. Epic define aim como *"a ray from the user's hand or controller used to point at a target"*, y desde UE 4.27 el forward del motion controller **por defecto (grip) apunta casi hacia ARRIBA** — de ahí que haya que usar Aim ([hilo de Epic](https://forums.unrealengine.com/t/forward-vector-of-motioncontroller-component-in-unreal-engine-5/552275)). La nota vieja de este tracker sobre "−Z fwd / +Y up" describe la convención **nativa de OpenXR**, antes de que UE convierta la pose a sus ejes (X adelante, Z arriba); no significa usar −Z en Blueprint.

**Dos manos con un solo BP.** Var nueva `bIsRight : bool` **instance-editable**. Las dos instancias reciben los dos eventos de input (ambas hacen `EnableInput`), y cada una filtra por su mano con un Branch: la derecha sale por `True`, la izquierda por `False` del **mismo** branch — así no hace falta ningún nodo `Not` y la condición es **un único getter compartido** entre los 4 branches (patrón de `bp-lean-construction.md`).
⚠ **Al agregar `bIsRight`, la instancia que ya existía en el nivel quedó en `false`** aunque el CDO estaba en `true` — Unreal no propaga el default nuevo a instancias ya serializadas. **Revisar siempre las instancias del nivel después de agregar una variable a un BP ya colocado.**

**Input: trigger sostenido.** Assets propios en `Stages/Touch/Input/`: `IA_Attract_Left` / `IA_Attract_Right` (Boolean, trigger **Down**, duplicados de `IA_Continue` de Breath) + `IMC_Touch` (gatillo izq `Click`+`Axis` → acción izq; der → der). Lo registra **`BP_AttractDirector` en BeginPlay** con `AddMappingContext` prioridad **1** (por encima de `IMC_Default`).
🔴 Se usa **`Started` → `TryGrab`** y **`Completed` → `TryRelease`**, NO `Triggered`: con trigger Down, `Triggered` dispara **cada frame** mientras se sostiene el gatillo. Esto reemplaza el compromiso anterior de usar el grip.

**`SetHover` ahora avisa a las burbujas (modelo push).** Además de los dispatchers, castea el `CurrentHovered` viejo → `NotifyHoverEnd`, y el `NewTarget` → `NotifyHoverStart`. El pin **`CastFailed` del primer cast va también a `SetCurrentHovered`** para que apuntar algo que NO es burbuja no corte la cadena y deje el hover sin actualizar. `TryGrab` pasa **`self`** en el nuevo pin `Beam` de `SetGrabbed`, así la burbuja sabe qué mano la agarró.

## Fase 3 (far-grab, input) — 2026-07-30
**Vars nuevas:** `GrabbedBubble` (BP_SoundBubble ref), `GrabHoldDistance`(25) — lo lee la burbuja para el punto de agarre.
**Input:** el beam hace `EnableInput(PlayerController)` en `BeginPlay` (actor no-pawn → sin esto no recibe Enhanced Input). Eventos `IA_Grab_Right_Pressed`.Triggered → `TryGrab`; `IA_Grab_Right_Released`.Triggered → `TryRelease`. 🔴 **DESACTUALIZADO — ver la sección de 2026-08-03 arriba.** Se usaba el GRIP porque el trigger vivía en un IMC no activo; ahora hay `IA_Attract_*` + `IMC_Touch` propios y va por trigger sostenido. Además los eventos `IA_Grab_Right_Pressed/Released` **estaban vacíos**: existían en el grafo pero no llamaban a `TryGrab`/`TryRelease`, o sea que la Fase 3 nunca estuvo cableada pese a figurar como hecha. Fueron borrados.
**`TryGrab()`:** castea `CurrentHovered` a BP_SoundBubble → si es burbuja: `GrabbedBubble = it`, `it.SetGrabbed(true)`.

### 🔴 2026-08-05 — `TryGrab` va en `Started`, NUNCA en `Triggered`
**Bug reportado en visor:** apuntando con el **gatillo ya apretado**, apenas el rayo pasaba por encima de una esfera **la agarraba al instante**. El comportamiento correcto es: el gesto de agarre solo vale si el gatillo se aprieta **mientras** se apunta la esfera; si venía apretado de antes, solo hay hover y hay que **soltar y volver a apretar**.
**Causa:** el evento estaba cableado a **`Triggered`**. `IA_Shoot_Right`/`Left` usan un trigger **`InputTriggerDown`** (verificado en el asset), y con `Down` **`Triggered` dispara CADA FRAME** mientras el gatillo está abajo — o sea, cada frame reintentaba agarrar lo que estuviera hovereado.
**Fix:** mover la conexión de `Triggered` (pin 0) a **`Started`** (pin 1) en los DOS eventos (`IA_Shoot_Right` y `IA_Shoot_Left`). `Started` dispara **una sola vez, en el flanco de apretado**, que es exactamente la semántica pedida — y el "soltar y volver a apretar" sale gratis, sin ninguna variable de estado extra.
- ⚠ **`read_graph_dsl` NO muestra qué pin de exec está cableado** en un evento de Enhanced Input: los cuatro (`Triggered`/`Started`/`Ongoing`/`Completed`) se ven igual. Hay que mirarlo con **`get_node_infos`**. Es el gotcha "el read oculta pines" — este tracker afirmaba que ya usaba `Started` y era **falso**.
- ⚠ Para cambiar de pin hay que **`break_pins` primero**: un pin de exec de ENTRADA admite varias conexiones, así que `connect_pins` **suma** en vez de reemplazar y quedarían los dos cableados.

### 🆕 2026-08-05 — una burbuja agarrada queda BLOQUEADA para la otra mano
**Bug reportado en visor:** con una esfera tomada con la derecha, apuntarla y gatillar con la izquierda **se la robaba**, y quedaban **las dos manos apuntando el beam a la misma esfera** (la derecha nunca se enteraba de que la había perdido).
**Fix:** en `TryGrab`, entre el `Cast To BP_SoundBubble` y el `SetGrabbedBubble`, se insertó un **Branch con `NOT(bubble.bIsGrabbed)`**. Si la burbuja ya está agarrada por alguien, la rama muere ahí: **ni se setea `GrabbedBubble` ni se llama `SetGrabbed`**, así que el beam de esa mano sigue en modo trace normal.
- **El candado es `bIsGrabbed` de la BURBUJA, no un estado del beam.** La burbuja es el recurso disputado, así que el dueño del lock es ella. `TryRelease` ya lo baja al soltar, no hizo falta tocarlo.
- ⚠ El chequeo va **después** del cast (necesita el ref tipado) y **antes** de tocar cualquier estado — si se pusiera después, el beam ya se habría "quedado" con la burbuja.
**`TryRelease()`:** si `GrabbedBubble` válido → `it.SetGrabbed(false)`, limpia `GrabbedBubble`.
El seguimiento lo hace la burbuja (su Tick, leyendo `MC_RightAim` + `GrabHoldDistance` del beam). Ver `BP_SoundBubble.md`.

## ✅ El beam arranca APAGADO — CONSTRUIDO 2026-08-04 (falta test en visor)
Ver [`docs/stages/touch-attracting.md`](../../../../docs/stages/touch-attracting.md) §2.a y fase **R3**. El beam dejó de estar siempre encendido: lo enciende el **sensor flotante** ([`BP_TouchSensor`](BP_TouchSensor.md)) que el usuario toma con su mano.

- **Var nueva `bEquipped : bool` = `false`**.
- **Función `Equip(NewEquipped : bool)`** — setea `bEquipped` **y** la visibilidad de `BeamFX` (Niagara) y `Cursor`. La llama `BP_TouchSensor` con `Class|BPAimBeam|Equip`.
  ⚠ **Se llama `Equip` y NO `SetEquipped` a propósito:** la var `bEquipped` genera un setter llamado `SetEquipped` (el DSL le come la `b` inicial) → habría colisión de nombres.
- **`EventBeginPlay`**: al final llama `Equip(false)` → el láser y el cursor **arrancan ocultos**, sin depender de cómo esté la visibilidad por defecto de los componentes.
- **`EventTick`: early-out** — un `Branch(bEquipped)` insertado como primer nodo; el `False` no va a ningún lado. Sin sensor no hay `LineTraceByChannel`, ni `ResolveHover`, ni `UpdateBeamPoints`.
- **`TryGrab`: mismo guard** — `Branch(bEquipped)` al inicio, porque los eventos de Enhanced Input **siguen llegando** aunque el beam esté apagado. Sin esto, apretar el gatillo antes de tomar el sensor entraba al camino de grab con `CurrentHovered` nulo → `Accessed None` en cada apretón.
- ⚠ **Los eventos `IA_Shoot_*` NO se tocaron.** El `read_graph_dsl` los muestra vacíos (gotcha conocido: solo imprime el pin exec primario y estos van por `Started`/`Completed`) — no son código muerto.

✅ **Sensores PROBADOS EN VISOR (2026-08-04)** — el beam apagado y el emparejamiento por mano funcionan.

## ✅ Con una burbuja agarrada, el beam apunta a su CENTRO — 2026-08-04 (falta visor)
Mientras hay `GrabbedBubble`, el láser deja de trazar y **termina en el centro del objeto agarrado**; al soltar vuelve solo al modo normal. Estructura del `EventTick` ahora:

```
if bEquipped:
   EnsureInput                       ← siempre, aunque esté agarrando
   IsValid(GrabbedBubble)
     Is Valid     → PointAtGrabbed()          (sin trace)
     Is Not Valid → LineTrace → UpdateBeamPoints → ResolveHover
```

- **`PointAtGrabbed()`** reusa `UpdateBeamPoints` con `bHit=false`, `TStart` = pose *Aim*, `TEnd` = `GrabbedBubble.GetActorLocation`. El `bHit=false` es a propósito: **oculta el `Cursor`** (una esfera de cursor adentro de la burbuja es ruido visual) y hace que `SetBeamEnd` tome el `TEnd`, o sea el centro de la burbuja.
- **Mientras agarra NO se traza ni se resuelve hover** → `CurrentHovered` **queda congelado** en la burbuja agarrada. Efectos: el preview sigue sonando mientras la sostenés (deseado), no hay parpadeo si la burbuja se sale del eje durante el interp, y el Tick es **más barato** (un line-trace menos por mano).
- Al soltar, `TryRelease` limpia `GrabbedBubble` → el Tick siguiente vuelve solo a la rama normal. No hace falta restaurar nada.

## 🔴 El beam no se veía: ocultar un Niagara NO es lo mismo que apagarlo — 2026-08-04
Con el debug del trace apagado quedó a la vista que **el beam de Niagara no se veía**. La causa NO era el largo (el beam se dibuja entre **dos puntos**, `User.PointArray` [0]=origen [1]=fin, así que el largo se lo da el trace; alargar `TraceDistance` no habría hecho nada).

**Cómo se diagnosticó — comparando contra el original que SÍ funciona.** `BP_Menu` del XRFramework maneja `NS_MenuLaser` con **exactamente** los mismos dos `NiagaraSetVectorArrayValue` (`User.PointArray`, índices 0 y 1, `bSizeToFit=false`) → el código de manejo no era el problema. **La única diferencia: `BP_Menu` nunca oculta el componente y nosotros sí** (`Equip(false)` en BeginPlay).

**La causa:** `SetVisibility(false)` **oculta pero NO detiene la simulación**. El sistema arranca con `bAutoActivate=true`, spawnea sus partículas al principio, y para cuando el usuario toma el sensor (varios segundos después) **ya se consumieron / murieron**. Al volver a hacer visible el componente no hay nada que mostrar.

**El arreglo:** `Equip()` ahora, además de la visibilidad, **activa/desactiva el sistema**:
```
Equip(NewEquipped):
  bEquipped = NewEquipped
  BeamFX.SetVisibility(NewEquipped) ; Cursor.SetVisibility(NewEquipped)
  if NewEquipped → BeamFX.Activate(bReset = TRUE)      ← re-spawnea desde cero
  else           → BeamFX.Deactivate()
```
🔴 **`bReset=true` es lo que importa**: sin él, `Activate` sobre un sistema ya activo no re-spawnea nada. Y `Deactivate` cuando se desequipa además **deja de simular** en vez de simular invisible (gratis en Quest).

**Regla general para llevarse:** para prender/apagar un efecto de Niagara usar **`Activate(bReset)` / `Deactivate`**, no `SetVisibility`. La visibilidad sirve para esconder un frame, no para gatear un efecto en el tiempo.

## 🔴🔴 CAUSA RAÍZ ENCONTRADA: el sistema NO lee `User.PointArray` — 2026-08-04
Abierto `NS_MenuLaser` en el editor (el MCP no puede ver emitters), su emitter **`TeleportColor`** resultó ser un **Beam emitter** cuya geometría sale del módulo **`Beam Emitter Setup`**:
- **`Beam Start`** = binding a `Simulation Position`, *Absolute Beam Start* **tildado**.
- **`Beam End`** = vector **hardcodeado `(0,0,100)`**, *Absolute Beam End* **destildado** → **ese 100 es el largo fijo**, y es relativo al componente.
- Spawn: **`Spawn Burst Instantaneous`, 5 partículas, Spawn Time 0** → one-shot (confirma que `Activate(bReset=true)` hacía falta, aunque no era la causa).

**`User.PointArray` SÍ existe como parámetro de usuario** (tipo *Niagara Data Interface Array Float 3*) — **pero NADIE lo consume.** La geometría del beam nunca lo miró. O sea: nuestras dos escrituras eran válidas, exitosas… y completamente inertes. **Es peor que un nombre mal escrito**: no hay ni siquiera un parámetro fantasma que delate el problema, el parámetro está ahí y se escribe bien. Silencio absoluto.

🔴 **De dónde salió el error:** `assets-existentes.md` afirmaba "manejado por `User.PointArray` índice 0/1". **Estaba escrito de memoria y nunca verificado contra el asset.** Ya está corregido allá. **Lección: "ya existe y está probado" vale para el ASSET; la FORMA DE MANEJARLO hay que confirmarla en el asset.**

### ✅ RESUELTO — el contrato definitivo (2026-08-04)
**Lado Niagara (lo hizo el usuario en el editor, el MCP no puede):** en `NS_TouchBeam` → `Beam Emitter Setup`, `Beam Start` y `Beam End` pasaron a leer los **parámetros de usuario `BeamStart` / `BeamEnd`** a través de un `Convert Vector to Position` (*Passthrough as Non Large World Coordinate*), con **los dos "Absolute" TILDADOS** → se interpretan como **coordenadas de mundo**, que es justo lo que manda el Blueprint.
- 🔴 Por ir vía `Convert Vector to Position`, los parámetros son **`Vector`, NO `Position`** → el nodo correcto es **`Niagara|SetNiagaraVariable(Vector3)`**.

**Lado Blueprint:** `UpdateBeamPoints` dejó de escribir el array muerto:
```
SetNiagaraVariable(Vector3)  BeamFX  "User.BeamStart"  TStart
SetNiagaraVariable(Vector3)  BeamFX  "User.BeamEnd"    <fin resuelto>
```
El prefijo **`User.`** va sí o sí (aunque el panel de User Parameters los liste como `BeamStart`/`BeamEnd`) — misma convención que ya usaba `User.PointArray`.
`PointAtGrabbed` no necesitó cambios: **reusa `UpdateBeamPoints`**, así que el beam apuntado al objeto agarrado quedó arreglado por el mismo cambio.

⚠ **El componente había quedado apuntando a `NS_MenuLaser`** por la bisección; se devolvió a **`NS_TouchBeam`** (verificado). Confirmado por timestamp que el asset editado fue `NS_TouchBeam` (288 KB, 14:22 de hoy) y que **`NS_MenuLaser` del framework quedó intacto** (15-jul) — bien, no se tocó un asset de terceros.

**Alternativa descartada por ahora:** volver a un **StaticMesh cilindro** escalado entre los dos puntos (100% manejable por MCP, sin emitters ni clamps de scalability). Queda anotada por si el beam de Niagara da problemas en el APK.

## 🔴🔴 LA CAUSA REAL: DOS mecanismos de posición peleándose — 2026-08-04
Inspeccionando `NS_TouchBeam` **con `NiagaraToolset_System`** (que sí existe — ver abajo), apareció el cuadro completo. El emitter `TeleportColor` (CPUSim, **Ribbon renderer**) tiene:

| Script | Módulo | Qué hace |
|---|---|---|
| Emitter Update | `EmitterState` | `Loop Behavior = **Infinite**`, `Life Cycle Mode = System` |
| Emitter Update | `BeamEmitterSetup` | beam desde **`User.BeamStart` / `User.BeamEnd`** (los que escribimos) |
| Emitter Update | `SpawnBurst_Instantaneous` | 5 partículas en t=0 |
| Particle Spawn | `SpawnBeam`, `BeamWidth`, `InitializeParticle` | reparte las partículas a lo largo del beam |
| Particle Update | 🔴 **`PositionFromArray`** (módulo **scratch** propio) | **SOBRESCRIBE la posición de cada partícula desde `User.PointArray`** |

🔴 **`PositionFromArray` NO es un conflicto: ES el mecanismo que hace que el beam siga la mano.** Se desactivó por error y hubo que revertirlo. El flujo de datos real es:
- `BeamEmitterSetup` (Emitter Update) + `SpawnBeam` (Particle Spawn) → colocan las partículas a lo largo del beam **en el momento del spawn**. Quedan **horneadas** ahí.
- **`PositionFromArray` (Particle Update) es lo ÚNICO que corre por partícula y por frame** → sin él la cinta queda **congelada donde nació**.

**La causa original, entonces:** las escrituras a `User.PointArray` usaban **`bSizeToFit=false`**, que **descarta la escritura en silencio** si el array viene sin dimensionar. El array quedaba vacío, las partículas muestreaban basura → cinta invisible **desde el día uno**. Y explica el `act=false`: datos inválidos/NaN tumban el sistema.

🔴 **Y corrige DOS afirmaciones mías anteriores en este mismo tracker:**
1. **`User.PointArray` NO estaba sin consumir** — lo consume `PositionFromArray`. Era el mecanismo original de verdad; `BeamEmitterSetup` con su `(0,0,100)` hardcodeado era el que estaba de adorno.
2. **El emitter NO es one-shot**: `Loop Behavior` está en **Infinite** en el emitter **y** en el `SystemState`. El sistema **compila limpio** (`GetSystemCompileState`: 0 errores, 0 warnings).

**Estado aplicado (2026-08-04):** `PositionFromArray` **re-habilitado** (verificado `"enabled": true`) y `UpdateBeamPoints` escribe **las dos cosas**:
```
SetNiagaraVariable(Vector3)   "User.BeamStart" / "User.BeamEnd"   ← posiciones de SPAWN (BeamEmitterSetup)
NiagaraSetVectorArrayValue    "User.PointArray" idx 0 / idx 1  bSizeToFit=TRUE   ← posición POR FRAME
```
🔴 **`bSizeToFit=TRUE` es la corrección clave.** Con `false` la escritura **se descarta sin error** contra un array sin dimensionar.

## 🎯🎯 CAUSA RAÍZ DEFINITIVA: el módulo `BeamWidth` estaba DESACTIVADO — 2026-08-04
En `LineTrace`, `ParticleSpawnScript` → **`BeamWidth`: `"enabled": false`**. Es el único módulo que escribe `Particles.RibbonWidth`, y el renderer lo confirmaba: **`RibbonWidthBinding.bBindingExistsOnSource: false`**.

🔴 **Una cinta sin ancho no dibuja NADA** — aunque el sistema simule, el material esté asignado, el renderer habilitado y las posiciones lleguen perfectas. **Ese era exactamente nuestro síntoma desde el principio.**

**Fix aplicado:** `SetModuleEnabled(BeamWidth, true)`. ✅ **Verificado midiendo antes y después**: el binding pasó de `false` a `true`.

👉 **Método que lo encontró, y que hay que usar primero la próxima vez:** los `bBindingExistsOnSource` del `GetRendererData` son un **checklist de diagnóstico gratis** — cada `false` es un atributo que el renderer espera y que nadie produce. Está generalizado en `niagara-quest.md`.

## 🎯 EL BEAM AHORA USA `LineTrace` (migrado de Soul Charger) — 2026-08-04
Tras agotar `NS_TouchBeam`, el usuario **migró el asset que funciona** a `Stages/Touch/VFX/LineTrace`. Es un sistema **distinto**: emitter `DynamicBeam` (CPU, ribbon), parámetros `Beam_Starts` (Vector3) · `Beam_End` (Position) · `Life` · `Spawn`, **sin `PointArray`**.

**Los tres errores que se corrigieron, todos verificados contra el código real del pawn viejo (copiado como texto de Blueprint):**
1. 🔴🔴 **El prefijo `User.` NO va.** El pawn que funciona escribe `InVariableName="Beam_End"` y `"Life"`, **pelados**. Los nodos `Set Niagara Variable (…)` son métodos del **componente** y agregan `User.` solos → escribir `"User.Beam_End"` apunta a `User.User.Beam_End`: **parámetro fantasma, éxito reportado, efecto cero.** ⚠ Lo opuesto a la familia de **arrays**, que sí lleva el nombre completo. Ver `assets-existentes.md`.
2. 🔴 **`Life = 500`**, no 6. Es la vida de partícula del pawn que funciona.
3. 🔴 **El beam nace donde está el COMPONENTE.** El `Beam Start` del emitter no está bindeado a ningún parámetro: el origen es la posición del sistema. El pawn viejo lo resuelve con `SpawnSystemAttached` a la esfera de la mano; nosotros teníamos `BeamFX` en el origen del pawn (`fxLoc=(0,0,0)`) → el beam salía de los pies. **Ahora `UpdateBeamPoints` hace `SetWorldLocation(BeamFX, TStart)` cada frame.**

**Estado de `UpdateBeamPoints`:**
```
SetBeamStart / SetBeamEnd            (vars de debug)
SetWorldLocation(BeamFX, TStart)     ← el origen del beam sigue la mano
SetNiagaraVariable(Vector3) BeamFX "Beam_End" <fin>
SetWorldLocation(Cursor) / SetVisibility(Cursor)
```
**`SeedBeam`** (BeginPlay): `"Spawn"=30`, `"Life"=500`. **`Equip`**: visibilidad + `Activate(bReset=true)`, sin `Deactivate`.
⚠ El `LineTrace` venía en **`Loop Behavior = Once`** (4 s): **se pasó a `Infinite`** por MCP para que sirva de láser continuo.

🔴 **`act=false` ES UN FALSO POSITIVO — ignorarlo.** Da `false` también con `LineTrace`, un sistema sin nada en común con `NS_TouchBeam`. `IsActive()` en un `NiagaraComponent` **no indica lo que parece**; se persiguió varias rondas por nada. **No usarlo como señal de diagnóstico.**

## ✅✅ Diagnóstico previo sobre NS_TouchBeam (histórico) — comparando contra el beam que SÍ funciona (2026-08-04)
Se comparó contra el proyecto viejo **Soul Charger** (`Projects/Soul Charger VR/SoulCharger_VR V7 5.8/`), donde el beam **funciona**: FX `Content/Asset/FX/LineTrace.uasset`, manejado desde `Content/VRPawnSC.uasset`. Análisis por **grep binario del `.uasset`** (sin MCP).

| | Soul Charger (**funciona**) | Nosotros (**no funcionaba**) |
|---|---|---|
| Nodo que escribe el array | 🔴 **`SetNiagaraArrayVector`** (`NiagaraDataInterfaceArrayFunctionLibrary`) — escribe el **array ENTERO** de una | `NiagaraSetVectorArrayValue` — escribe **un índice por llamada** |
| Parámetro | `User.PointArray` (idéntico) | `User.PointArray` |
| `Deactivate` | **NUNCA aparece** | lo llamábamos en `Equip(false)` |
| `Activate` | **sí lo llama** | se había quitado |

**La cadena causal completa, por fin:**
1. `NiagaraSetVectorArrayValue` con `bSizeToFit=false` **descarta la escritura en silencio** contra un array sin dimensionar → `User.PointArray` **vacío**. (Y encima nuestro Tick **no escribe nada hasta equipar**, así que el array está vacío desde BeginPlay.)
2. **`PositionFromArray` muestrea un array vacío** → posiciones **NaN/basura** en cada partícula.
3. Niagara detecta datos inválidos y **MATA el sistema** → **`act=false`**. ← el hecho terco que nunca cerraba.
4. Cuando por fin se equipa y se escribe bien, **el sistema ya está muerto**, y sin `Activate` nada lo revive.

### 🔧 PLAN DE ARREGLO (aplicar apenas vuelva el MCP)
1. En `UpdateBeamPoints`: **borrar los dos `NiagaraSetVectorArrayValue`** y poner **UN `Niagara|NiagaraSetVectorArray`** (array entero) alimentado por un **`Make Array`** de 2 elementos `[TStart, <fin resuelto>]`. Es lo que hace el proyecto que funciona y **elimina toda la clase de falla por dimensionado**.
2. **El array NUNCA debe quedar vacío mientras el sistema simula.** Sembrarlo en `BeginPlay` con dos puntos válidos (p. ej. los dos en la pose *Aim* → beam de largo cero, invisible pero **sin NaN**).
3. **Re-agregar `Activate(bReset=true)` en `Equip(true)`**, y **NO volver a poner `Deactivate`** (el que funciona nunca lo llama).
4. Dejar `SetVisibility` como está (el que funciona también lo usa).
🔎 El sistema del proyecto viejo expone además `User.Sprites_Size` y `User.Trail_Lifetime` — no los necesitamos, pero confirman que es la misma familia de asset.

### 🟠 Historial: `act=false` era el hecho terco (2026-08-04)
Aun con `PointArray` escribiéndose bien (`bSizeToFit=true`), `PositionFromArray` habilitado y el sistema compilando limpio, el log sigue dando **`eq=true vis=true` con puntos correctos, pero `act=false`**.

**Último experimento aplicado:** se **eliminó por completo el ciclo `Activate`/`Deactivate` de `Equip()`** (que yo había introducido). Ahora `Equip` **solo** setea `bEquipped` + las dos visibilidades, y la activación queda **exclusivamente en manos de `bAutoActivate=true`** del componente. Es un experimento limpio:
- Si pasa a **`act=true`** → mi ciclo Deactivate→Activate era el que rompía (probable: `SystemState.Inactive Response = "Kill (System and Emitters Die Immediately)"` destruye la instancia y el re-Activate no la reconstruye).
- Si sigue en **`act=false` incluso antes de equipar** → el sistema se muere solo (datos/escalabilidad), no por nosotros.

**Plan B acordado con el usuario:** hay un **beam funcional en el proyecto viejo "Soul Charger"**. Migrar ese sistema Niagara a `VR_Test` y apuntarle el componente es aplicar la regla del proyecto (*reusar lo que ya anda con su configuración*) en vez de seguir depurando este. Lo que hay que traer/mirar: el asset del sistema, **cómo lo maneja el Blueprint** (nodo exacto, nombre de parámetro, `bSizeToFit`), el tipo de emitter/renderer, y el `Emitter State`.
ℹ `GetStackIssues` reporta 2 **Infos** (no errores) por la conversión Vector→Position del `Convert Vector to Position`: es lossy en Large World Coordinates. Esperable a nuestra escala; anotado por si algún día el nivel se aleja del origen.

## 🟠 Hipótesis descartada: "el emitter es one-shot" — 2026-08-04
Con `LogBeamPose` ampliado (equipped / IsActive / IsVisible / BeamStart / BeamEnd / world location del componente), el runtime dijo esto una vez equipado:

```
TCH|Beam R eq=true act=false vis=true S=X=28.9 Y=16.1 Z=94.3 E=X=768.8 Y=39.4 Z=397.8 fxLoc=X=0 Y=0 Z=0
```

- ✅ `eq=true`, `vis=true`, y **`S`/`E` llegan sanos, separados y siguiendo la mano** → el gateo por sensor, la visibilidad y el pipeline de parámetros **están todos bien**.
- 🔴 **`act=false`** → **el sistema de Niagara NO está simulando.** Es la causa.

**Mecanismo:** el emitter tiene `Spawn Burst Instantaneous` (one-shot). Hace el burst, las partículas mueren, el **sistema COMPLETA**, y al completar el `NiagaraComponent` **se auto-desactiva** (`OnSystemComplete` → `Deactivate`). Por eso `Activate(bReset=true)` prende el sistema un instante y al segundo ya está muerto — justo cuando el timer del log lo muestrea.

**El arreglo es asset-side (el MCP no llega):** en el emitter, módulo **`Emitter State`** → **`Loop Behavior = Infinite`** (y que el `Life Cycle Mode`/duración no lo hagan completar), o `Lifetime` de partícula lo bastante largo para que no mueran. **Criterio de éxito: que el log pase a `act=true` de forma sostenida.**

⚠ **Segundo problema latente en `fxLoc=(0,0,0)`:** el componente vive en el origen del mundo (el pawn está ahí) mientras el beam se dibuja en coordenadas **absolutas** a 30-770 unidades. Si el sistema calcula bounds dinámicos desde las partículas, no molesta; si alguna vez se cambia a bounds fijos o a sim GPU, **lo van a culear**. Red de seguridad disponible desde BP sin tocar el asset: **`Niagara|SetSystemFixedBounds`** (existe, verificado). No se aplicó todavía — un cambio por vez.

## 🟠 Historial del diagnóstico — 2026-08-04
🔴 **Reencuadre importante: es probable que este beam NUNCA se haya visto.** El "probado en visor" del 2026-08-03 validó apuntado, hover y far-grab — todo eso lo da el **line-trace**, no el visual — y el `DrawDebugType` estaba en `ForOneFrame`, así que **lo que se veía era la línea de debug**. Al apagar el debug quedó a la vista que no hay beam. **No es una regresión del gateo por sensor.**

**Descartado hasta ahora (verificado, no supuesto):**
- El **código de manejo es idéntico** al del `BP_Menu` del XRFramework que sí funciona (mismos dos `NiagaraSetVectorArrayValue`, `User.PointArray`, índices 0 y 1).
- El **duplicado no está vacío**: `NS_TouchBeam.uasset` = 285 KB contra 282 KB de `NS_MenuLaser.uasset`.
- El **componente está sano**: `RelativeScale3D` 1, `bVisible` true, `bHiddenInGame` false, `bAutoActivate` true, asset asignado.
- El actor `BP_AimBeam` en el nivel tiene **escala 1**.
- **Arreglado por el camino** (bug real, aunque no era la causa única): ocultar en vez de desactivar → ahora `Equip` hace `Activate(bReset=true)`/`Deactivate`. Ver la sección de arriba.

**Dos cambios aplicados como siguiente prueba (2026-08-04):**
1. 🔬 **Bisección: `BeamFX.Asset` apunta ahora a `NS_MenuLaser`** (el original que funciona en el framework) en vez de `NS_TouchBeam`. Es la prueba que parte el problema al medio — **si con el original se ve, el defecto está DENTRO de `NS_TouchBeam`; si tampoco se ve, el defecto está en cómo lo manejamos/ubicamos.** Revertir = volver a poner `NS_TouchBeam` en el `Asset` del componente.
2. **`bSizeToFit` de las dos escrituras: `false` → `true`.** Con `false`, si `User.PointArray` viene con menos de 2 entradas **las escrituras se descartan en silencio** y el beam queda sin puntos. Con `true` el array se redimensiona solo. Es estrictamente más seguro y elimina una clase entera de falla muda.

### 🔴 Si con `NS_MenuLaser` TAMPOCO se ve — checklist manual (el MCP no puede ver esto)
El MCP **no expone emitters, módulos, materiales ni parámetros de usuario** de un `NiagaraSystem`. Hay que abrirlo en el editor y mirar, en este orden:
1. **Scalability / Quality Level del emitter.** Si está en Medium/High/Epic y el **Preview Rendering Level** del editor está en Android, el emitter queda **muerto sin ningún error** — `fx.Niagara.QualityLevel` está clampeado a **[0,1]** en Android (ver `niagara-quest.md`). Es el sospechoso #1 en este proyecto.
2. **`User.PointArray` existe y su default tiene ≥2 entradas** (el nombre tiene que ser exacto: los setters de Niagara usan `bAdd=true`, así que **un nombre mal escrito crea un parámetro fantasma y no falla**).
3. **Local Space del emitter.** Le metemos coordenadas de **mundo**; si el emitter está en local space, la cinta se dibuja en el lugar equivocado.
4. **Fixed Bounds del sistema.** Un beam manejado por puntos de mundo necesita bounds que lo cubran, o lo culean.
5. **Material de la ribbon**: usage flag *Used with Niagara Ribbons*, y que sea válido en **mobile forward**.

## 🔎 Estado del visual del beam (verificado 2026-08-04)
**Las dos cosas están activas a la vez, y conviene saberlo:**
- **Niagara: SÍ está.** `BeamFX` tiene `NS_TouchBeam` asignado (`bAutoActivate=true`, visible) y `UpdateBeamPoints` le escribe `User.PointArray` [0]=origen / [1]=fin, más el `Cursor` en el impacto.
- **Debug: APAGADO desde 2026-08-04.** El `DrawDebugType` del `LineTraceByChannel` se puso en **`None`** (verificado con `get_pin_value`). Si hace falta volver a verlo para depurar: `K2Node_CallFunction_15`, pin `DrawDebugType` (índice 6) → `ForOneFrame`.
  ⚠ El `read_graph_dsl` del Tick **muestra el `LineTraceByChannel` DOS veces** (una hoisteada arriba con `_bblockinghit` y otra en la rama). **Es un solo nodo** — verificado con `find_nodes`. El read hoistea las dependencias de datos; no salgas a buscar un trace duplicado que no existe.
- **Motivo doble:** el gesto de tomar la herramienta es la "entrada" a la mecánica (continuidad con `BP_BrushTool` de Movement y el sensor de Breath), **y** se acaba el ruido visual de dos láseres permanentemente encendidos en una obra contemplativa.
- ⚠ Igual que pasó con `bIsRight`: **al agregar la variable, revisar las 2 instancias ya colocadas en `L_Touch`** — Unreal no propaga el default nuevo a instancias ya serializadas.
- El sensor **no lee el pawn**: pregunta la posición de la mano a cada beam, que ya cachea su motion controller (`CacheAimSource`). Así no se toca `Core/`.

## Session log
- 2026-07-28: creado el esqueleto (componentes MC_RightAim+Laser, vars TraceDistance/CurrentHovered, dispatchers OnHoverBegin/End, funciones SetHover/ClearHover vacías). Compila. Cableado bloqueado por editor localizado → usuario decide pasar a inglés.
- 2026-07-29: editor pasado a inglés (DSL desbloqueado). **`SetHover` + `EventTick` cableados por DSL** (aprendizajes: los auto-vars `_pin` no siempre existen → bindear salidas explícito; `LineTraceByChannel` bind único = OutHit, usar `bBlockingHit` del break como bool de impacto; llamada a función self usa `:NewTarget` keyword o conecta al `self`). Compila. Colocado en `L_Touch` (origen) + cubo de test `AimTarget_TestCube` (tag "Aimable") a (150,0,120). DrawDebug del trace ON para verificación visual. Todo guardado. (Un `BP_AimBeam` se coló primero en `L_Test_Breath` por reapertura del mapa tras el reinicio → removido; ese nivel quedó sin cambios.)
