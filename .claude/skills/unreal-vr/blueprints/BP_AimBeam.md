# BP_AimBeam — progress tracker

Beam de apuntado del stage Touch (Fase 1 del brief [`docs/stages/touch-attracting.md`](../../../../docs/stages/touch-attracting.md)). Actor del lado del mando (NO en el pawn): line-trace desde la pose *aim*, láser, y hover/unhover sobre objetos apuntables.

- **refPath**: `/Game/SoulCharger/Stages/Touch/BP_AimBeam.BP_AimBeam`  ·  **parent**: Actor  ·  **in level**: sí — `L_Touch` (`BP_AimBeam_C_0` en origen (0,0,0), alineado al PlayerStart)
- **Status**: 🟢 Fase 1 cableada y compila. Falta test en visor + material del láser. (Editor pasado a inglés → DSL desbloqueado.)

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

## Fase 3 (far-grab, input) — 2026-07-30
**Vars nuevas:** `GrabbedBubble` (BP_SoundBubble ref), `GrabHoldDistance`(25) — lo lee la burbuja para el punto de agarre.
**Input:** el beam hace `EnableInput(PlayerController)` en `BeginPlay` (actor no-pawn → sin esto no recibe Enhanced Input). Eventos `IA_Grab_Right_Pressed`.Triggered → `TryGrab`; `IA_Grab_Right_Released`.Triggered → `TryRelease`. 🔴 **Se usa el GRIP (`IA_Grab_Right`, en IMC_Default siempre activo), NO el trigger** que pide el brief: `IA_Shoot_Right` (trigger) vive en IMC_Weapon_Right (no activo) y un IMC propio arriesga el gotcha #7 de OpenXR. **Remap a trigger = pulido** (cambiar los 2 nodos de evento).
**`TryGrab()`:** castea `CurrentHovered` a BP_SoundBubble → si es burbuja: `GrabbedBubble = it`, `it.SetGrabbed(true)`.
**`TryRelease()`:** si `GrabbedBubble` válido → `it.SetGrabbed(false)`, limpia `GrabbedBubble`.
El seguimiento lo hace la burbuja (su Tick, leyendo `MC_RightAim` + `GrabHoldDistance` del beam). Ver `BP_SoundBubble.md`.

## Session log
- 2026-07-28: creado el esqueleto (componentes MC_RightAim+Laser, vars TraceDistance/CurrentHovered, dispatchers OnHoverBegin/End, funciones SetHover/ClearHover vacías). Compila. Cableado bloqueado por editor localizado → usuario decide pasar a inglés.
- 2026-07-29: editor pasado a inglés (DSL desbloqueado). **`SetHover` + `EventTick` cableados por DSL** (aprendizajes: los auto-vars `_pin` no siempre existen → bindear salidas explícito; `LineTraceByChannel` bind único = OutHit, usar `bBlockingHit` del break como bool de impacto; llamada a función self usa `:NewTarget` keyword o conecta al `self`). Compila. Colocado en `L_Touch` (origen) + cubo de test `AimTarget_TestCube` (tag "Aimable") a (150,0,120). DrawDebug del trace ON para verificación visual. Todo guardado. (Un `BP_AimBeam` se coló primero en `L_Test_Breath` por reapertura del mapa tras el reinicio → removido; ese nivel quedó sin cambios.)
