# VR / XR — this project's framework + UE5 building blocks

⚠ Node/class NAMES below are from Epic docs + the live project map. Exact **`type_id`s must be confirmed live** (`find_node_types` → `get_node_type_pins`) the first time we use one. Add confirmed ones to nodes.md.

---

## 🔴 Tracking origin / "aparezco en cualquier lado" al dar Play (RESUELTO — leer antes de tocar `SetTrackingOrigin`)

**`SetTrackingOrigin` NO posiciona al jugador. Solo elige el espacio de referencia.** Probar Stage / Local / LocalFloor a ver cuál "funciona" **no puede** arreglar la posición — ninguno lo hace. Lo que posiciona es **`ResetOrientationAndPosition`**.

### Qué hace cada origen (verificado en `OpenXRHMD.cpp`)
| Origen | Dónde está el (0,0,0) del tracking | Consecuencia |
|---|---|---|
| **Stage** | el **centro del Guardian** del usuario | la cámara queda en `VROrigin + (dónde estás respecto del centro de TU Guardian)` → **aparece a metros del PlayerStart** |
| **Local** | dónde estaba el casco al arrancar / último recenter | también arbitrario |
| **LocalFloor** | como Local pero con Z en el piso | requiere `XR_EXT_local_floor`; **si no está soportado cae a STAGE en silencio** (`OpenXRHMD.cpp:1026`) |

### 🔴 La diferencia que decide todo el setup (`OpenXRHMD.cpp:938-945`)
```cpp
if (TrackingSpaceType == XR_REFERENCE_SPACE_TYPE_LOCAL)
    NewPosition.Z = CurrentPosition.Z;   // LOCAL: recentra también la ALTURA
else
    NewPosition.Z = 0.0f;                // STAGE/LOCAL_FLOOR: conserva la altura REAL sobre el piso
```
- **Stage + Recenter** → X, Y y yaw clavados al `VROrigin`; **la altura real se conserva** (una persona alta tiene los ojos más arriba). ✅ **Lo correcto para obra sentada.**
- **Local + Recenter** → recentra X, Y **y Z** → le impone una altura fija a todos. ❌

### La receta (aplicada en `BP_VRPawn_SC`)
1. `SetTrackingOrigin("Stage")` — **Stage no era el error.**
2. `HideLoadingScreen` → **`Delay 0.5`** → `ResetOrientationAndPosition(Yaw=0, OrientationAndPosition)`.
   ⚠ **El Delay NO es opcional.** `Recenter()` pide `GetDisplayTime()` y **se rinde en silencio** con solo un warning (*"Could not retrieve a valid head pose for recentering"*, `OpenXRHMD.cpp:898`) si la sesión XR todavía no tiene pose. En un BeginPlay puro suele no tenerla → **el recentrado no ocurre y no falla visiblemente**.
3. **El `PlayerStart` va al nivel del PISO (Z≈0)**, no a la altura del pecho. En este pawn **el RootComponent ES el `VROrigin`** (verificado), así que el pawn se planta donde va el VROrigin y con Stage la cámara queda en `VROrigin.Z + altura real`. Con el PlayerStart en Z=79.8 el usuario **flotaba 80 cm**. Un PlayerStart arrastrado a mano queda a la altura de la cápsula por defecto (~88) — **para un pawn de VR eso está mal**.

**No hace falta tocar el índice del PlayerController ni del Pawn.** El GameMode spawnea en el `PlayerStart` con `SpawnDefaultPawnAtTransform`; el problema nunca fue de índices.

### Cómo inspeccionar los componentes de un pawn por MCP
El CDO devuelve `None` para los componentes del SCS, y `...Default__X_C.VROrigin` no resuelve. **Truco que sí funciona:** `add_to_scene_from_asset` para colocar una instancia temporal → `get_properties` sobre `<actor>.VROrigin` / `.Camera` → `SceneTools.remove_from_scene` (**no** existen `delete_actor` ni `destroy_actor`).

---

## THIS PROJECT — `/Game/XRFramework` (build ON this, don't reinvent)
It's the **UE5 VR Template** (OpenXR) extended with a weapon module, targeting **PICO / standalone-Android** (plugins: OpenXR, OpenXREyeTracker, OpenXRHandTracking, PICOController). Level: `/Game/XRFramework/Levels/L_XRTemplate`. GameMode `BP_XRGameMode` → default pawn `BP_XRPawn`.

### BP_XRPawn — `/Game/XRFramework/Blueprints/BP_XRPawn.BP_XRPawn` (parent Pawn) — THE HUB
Owns locomotion, snap turn, teleport, grab, menu. Extend behavior HERE (add components/functions) rather than subclassing per hand.
- Grab vars: `HeldComponentLeft`, `HeldComponentRight` (BP_GrabComponent refs), `GrabRadiusFromGripPosition`.
- Teleport vars: `ProjectedTeleportLocation`, `bValidTeleportLocation`, `bTeleportTraceActive`, `TeleportTracePathPositions`, `TeleportProjectPointToNavigationQueryExtent`, `TeleportVisualizerReference`.
- Turn: `SnapTurnDegrees`. Menu: `MenuReference`.
- Functions: `StartTeleportTrace`/`TeleportTrace`/`IsValidTeleportLocation`/`EndTeleportTrace`/`TryTeleport`, `GetGrabComponentNearMotionController`, `SnapTurn`, `ToggleMenu`.
- Events: `ReceiveBeginPlay`, `HideUnhideHand` (implements interface `BPI_PawnAnim`). No Tick — trace driven by input latents/timers.
- Has (implied) two MotionController components + hand meshes.

### BP_GrabComponent — `.../BP_GrabComponent.BP_GrabComponent` (parent SceneComponent)
Grab handle carried by grabbable actors. Pawn finds nearest to a controller and calls TryGrab.
- Vars: `bIsHeld`, `MotionControllerRef`, `GrabType` (enum **E_GrabType** — free/snap/custom), `PrimaryGrabComponent`, `PrimaryGrabRelativeRotation`, `bSimulateOnDrop`.
- Dispatchers: **`OnGrabbed`**, **`OnDropped`**, `OnGrabHapticEffect` — the hooks for custom object logic.
- Functions: `TryGrab`, `TryRelease`, `SetShouldSimulateOnDrop`, `SetPrimitiveCompPhysics`, `GetHeldByHand`. Events: BeginPlay, Tick.

### Other BPs
- **BP_Grabbable_SmallCube** (Actor) — template grabbable = static mesh + a BP_GrabComponent. Copy for new grabbables.
- **BP_Pistol** (Actor) → **BP_Projectile** (Actor) — self-contained weapon module: adds its own `IMC_Weapon_*`, `IA_Shoot_*`, haptics, projectile spawn. **Pattern to copy for new interactive tools.**
- **BP_Menu** (Actor) + **WBP_Menu** (widget) — laser-pointer UI, `IMC_Menu`, toggled by pawn `ToggleMenu`.
- **BP_TeleportVisualizer** (Actor), **BP_Passthrough**, **BPI_PawnAnim** (interface: `HideUnhideHand`), enum **E_GrabType**.

### Input assets (Enhanced Input) — `/Game/XRFramework/Input/`
- IMCs: `IMC_Default`, `IMC_Hands`, `IMC_Menu`, `IMC_Weapon_Left`, `IMC_Weapon_Right` (layered — Default always on; others pushed contextually).
- IAs (`Input/Actions/`): `IA_Move`, `IA_Turn`, `IA_Grab_{Left,Right}_{Pressed,Released}`, `IA_Menu_Toggle_*`, `IA_Menu_Cursor_*`, `IA_Menu_Interact_*`, `IA_Shoot_{Left,Right}`.
- Hand finger poses (`Actions/Hands/`): `IA_Hand_{Grasp,IndexCurl,Point,ThumbUp}_{L,R}`.
- Modifier: `BP_InputModifier_XAxisPositiveOnly`.

### Extension recipes (how to build on it)
- **Make X grabbable**: add a `BP_GrabComponent` to the actor, set `GrabType`, bind `OnGrabbed`/`OnDropped` for custom logic. (Copy BP_Grabbable_SmallCube.)
- **New interactive tool**: copy the BP_Pistol pattern — grabbable actor that ships its own `IMC_*` + `IA_*`, pushes its context when grabbed, does its logic.
- **New locomotion/input on the pawn**: add the IA + map it in an IMC, add the `EnhancedInputAction IA_*` event in BP_XRPawn, wire to a new function there.

---

## UE5 VR BUILDING BLOCKS (general — confirm type_ids live on first use)

### Pawn & tracking origin
- VR Template pawn layout: `DefaultSceneRoot` → `VROrigin` (Scene Component = tracking origin/floor) → `Camera` (CameraComponent = HMD) + `MotionControllerLeft`/`Right` (+ hand meshes).
- **`Set Tracking Origin`** — ⚠ Epic's docs say `Local Floor` for standing, `Local` for seated, but **this project verified the opposite for its seated piece: use `Stage` + `ResetOrientationAndPosition` after a `Delay`** (Local also recenters height; see §tracking-origin above and vr-pawn.md §5). Related: `Get Tracking Origin`, `Reset Orientation and Position`.

### Enhanced Input (the current system — legacy Action/Axis mappings are gone)
→ **Deep reference in [input.md](input.md)** (trigger/event table, modifiers, IMC priorities, haptics, debug). This section is just the sketch.
- Assets: **Input Action** (`IA_`, value Digital/Axis1D/Axis2D/Axis3D) + **Input Mapping Context** (`IMC_`, maps keys→IAs with Modifiers & Triggers).
- Wire in pawn/controller: `Get Enhanced Input Local Player Subsystem` → **`Add Mapping Context`**(IMC, Priority) (pair: `Remove Mapping Context`).
- Per action: an **`EnhancedInputAction IA_Xxx`** event with pins Triggered/Started/Ongoing/Completed/Canceled + `Action Value` (bool/float/Vector2D), `Elapsed Seconds`, `Trigger Time`.
- ⚠ **Caveat**: `Add Mapping Context` in pawn `BeginPlay` often fails (possession not ready). Do it in the PlayerController, on `Event Possessed`, or after a Delay.

### Motion controllers
- Component **`MotionControllerComponent`** ("Motion Controller"), under VROrigin; auto-tracked each frame.
- Property **`Motion Source`** = `Left`/`Right` (also `LeftGrip`/`RightAim`/… — **grip pose** = where held, **aim pose** = pointing ray for lasers/UI).
- Visual: `Display Device Model` (auto-render controller), `Custom Display Mesh`.
- Pose/hand data: **`Get Motion Controller Data`** → **`XRMotionControllerData`** struct (`Break XRMotionControllerData`): `GripPosition/Rotation`, `AimPosition/Rotation`, and hand arrays `HandKeyPositions/Rotations/Radii` + validity.
- ⚠ Raw `MotionController (L/R)` key events were deprecated (4.24) — bind buttons via `IMC_`, not raw keys.

### Teleport & snap turn
- Teleport: `Predict Projectile Path By TraceChannel` (arc) → `Project Point to Navigation` (validate on NavMesh) → Niagara/spline visual → `Teleport`/`SetActorLocation` (often with camera fade). `NavModifier_NoTeleport` marks no-go.
- Snap turn: Axis1D input → `AddActorWorldRotation` by a fixed increment (e.g. `SnapTurnDegrees`), gated so one flick = one turn.

### Hand tracking / OpenXR (OpenXRHandTracking plugin — enabled)
- Access via the SAME `Get Motion Controller Data` → `XRMotionControllerData` with hand joint arrays; joints via enum **`EHandKeypoint`** (Wrist, ThumbTip, IndexTip, …).
- Debug: `XRVisualization` plugin → `Render Motion Controller`.
- Note: legacy "hand tracking not supported on OpenXR" is OUTDATED for UE5.8.

### PICO specifics
- Runs through **OpenXR**; `PICOController` plugin supplies PICO's interaction profile (`XR_BD_controller_interaction` / `XR_BD_ultra_controller_interaction`). Bind through Enhanced Input as usual; PICO key labels appear in the IMC dropdown once the profile is active. Standard inputs: Trigger (Axis1D), Grip (Axis1D), Thumbstick (Axis2D+click), A/B (right), X/Y (left), Menu, haptics. ⚠ Confirm 5.8 PICOController registers the profile.

### Docs
VR Template: https://dev.epicgames.com/documentation/en-us/unreal-engine/vr-template-in-unreal-engine · Motion Controller Setup: https://dev.epicgames.com/documentation/unreal-engine/motion-controller-component-setup-in-unreal-engine · Interactive XR: https://dev.epicgames.com/documentation/en-us/unreal-engine/making-interactive-xr-experiences-in-unreal-engine · PICO Unreal OpenXR: https://developer.picoxr.com/document/unreal-openxr/input-mappings/

### VR nodes to confirm live before first use
`Add Mapping Context`, `Get Enhanced Input Local Player Subsystem`, `EnhancedInputAction IA_*`, `Get Motion Controller Data`, `Break XRMotionControllerData`, `Set Tracking Origin`, `MotionControllerComponent`, `Predict Projectile Path By TraceChannel`, `Project Point to Navigation`, `SphereTraceForObjects`, `AddActorWorldRotation`, `EHandKeypoint`.
