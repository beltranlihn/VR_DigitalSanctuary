# BP_AimBeam — progress tracker

Beam de apuntado del stage Touch (Fase 1 del brief [`docs/stages/touch-attracting.md`](../../../../docs/stages/touch-attracting.md)). Actor del lado del mando (NO en el pawn): line-trace desde la pose *aim*, láser, y hover/unhover sobre objetos apuntables.

- **refPath**: `/Game/SoulCharger/Stages/Touch/BP_AimBeam.BP_AimBeam`  ·  **parent**: Actor  ·  **in level**: **2 instancias** en `L_Touch` — `AimBeam_Right` (`bIsRight`=true, `MotionSource`=RightAim) y `AimBeam_Left` (`bIsRight`=false, `MotionSource`=LeftAim). Se **attachean al pawn en BeginPlay**, no viven en el origen del mundo. (2026-08-03)
- **Status**: 🟢 **PROBADO EN VISOR (2026-08-03)** — apunta con las dos manos, hover, y far-grab con trigger sostenido. Falta fine tuning.

## ✅ Lo que hizo que funcionara (2026-08-03) — los 3 arreglos
1. **Tracking:** el beam **no tiene MotionControllerComponent propio** (uno en un actor del nivel **nunca trackea**: solo consulta si su actor tiene *local net owner*, cosa que se cumple en el Pawn). `CacheAimSource()` toma el `MotionControllerRightAim`/`LeftAim` **del pawn** según `bIsRight`.
2. **Input:** con **`IA_Shoot_Right`/`IA_Shoot_Left` del XRFramework** — `Triggered` → `TryGrab`, `Completed` → `TryRelease`. Inventar `IA_Attract_*` + `IMC_Touch` propios **no disparó nunca** pese a registrarse bien. Ver `assets-existentes.md`. ⚠ `Triggered` corre cada frame → `TryGrab` lleva guard `IsValid(GrabbedBubble)`.
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
**`TryRelease()`:** si `GrabbedBubble` válido → `it.SetGrabbed(false)`, limpia `GrabbedBubble`.
El seguimiento lo hace la burbuja (su Tick, leyendo `MC_RightAim` + `GrabHoldDistance` del beam). Ver `BP_SoundBubble.md`.

## Session log
- 2026-07-28: creado el esqueleto (componentes MC_RightAim+Laser, vars TraceDistance/CurrentHovered, dispatchers OnHoverBegin/End, funciones SetHover/ClearHover vacías). Compila. Cableado bloqueado por editor localizado → usuario decide pasar a inglés.
- 2026-07-29: editor pasado a inglés (DSL desbloqueado). **`SetHover` + `EventTick` cableados por DSL** (aprendizajes: los auto-vars `_pin` no siempre existen → bindear salidas explícito; `LineTraceByChannel` bind único = OutHit, usar `bBlockingHit` del break como bool de impacto; llamada a función self usa `:NewTarget` keyword o conecta al `self`). Compila. Colocado en `L_Touch` (origen) + cubo de test `AimTarget_TestCube` (tag "Aimable") a (150,0,120). DrawDebug del trace ON para verificación visual. Todo guardado. (Un `BP_AimBeam` se coló primero en `L_Test_Breath` por reapertura del mapa tras el reinicio → removido; ese nivel quedó sin cambios.)
