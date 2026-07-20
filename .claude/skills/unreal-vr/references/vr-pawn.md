# VR Pawn — anatomía, incorporación y configuración (UE 5.8, Quest 3 STANDALONE)

> **Target: Meta Quest 3 standalone, OpenXR backend NativeOpenXR, renderer móvil, obra SENTADA de 15 min, single-user.** Este proyecto usa **XRFramework** (VR Template extendido) y ya tiene `BP_VRPawn_SC` derivado de esa base; el hub de comportamiento es `BP_XRPawn` (`/Game/XRFramework/Blueprints/BP_XRPawn`). Complementa a [vr.md](vr.md) (mapa del proyecto) e [input.md](input.md) (Enhanced Input).
>
> **Convención de fuentes:** **(A)** doc oficial Epic/Meta con URL · **(B)** código del motor UE 5.8 en `C:\Program Files\Epic Games\UE_5.8` con archivo:línea (verificado en ESTA instalación) · **(C)** fuente técnica seria · **(D)** folclore sin fuente (marcado). `⚠ no verificado en 5.8` = no se pudo confirmar en código ni doc oficial de esta versión.

---

## 0. CHECKLIST — incorporar un pawn VR a un nivel nuevo / etapa

Pasos mínimos, en orden. Cada uno enlaza a su sección.

1. **GameMode → `DefaultPawnClass`.** El GameMode del nivel (o `BP_XRGameMode`) debe tener `DefaultPawnClass = BP_VRPawn_SC`. ⚠ Tras setear el CDO por MCP: **`compile_blueprint` SIEMPRE** antes de `save_assets`, o en runtime spawnea `DefaultPawn` aunque `get_properties` mienta devolviendo el valor correcto (ver [gotchas.md](gotchas.md) §"set_properties sobre un CDO"). §4.
2. **`PlayerStart` al nivel del PISO (Z ≈ 0).** No a la altura de la cápsula (~88) ni del pecho. En este pawn el **RootComponent ES el `VROrigin`**; con Stage la cámara queda en `VROrigin.Z + altura real`, así que un PlayerStart elevado hace flotar al usuario. §1, §4, y [vr.md](vr.md) §tracking.
3. **Tracking origin = `Stage`.** `SetTrackingOrigin("Stage")` en el pawn. Stage NO era el error histórico: **solo elige el espacio, no posiciona**. §5.
4. **Recentrado con Delay.** `HideLoadingScreen` → **`Delay 0.5`** → `ResetOrientationAndPosition(Yaw=0, OrientationAndPosition)`. El Delay **no es opcional**: sin pose XR válida, `Recenter()` aborta con solo un warning. §5.
5. **Enhanced Input tras posesión, NO en BeginPlay del pawn.** `Add Mapping Context` en **`Event Possessed`** o en el PlayerController. En BeginPlay del pawn el controller es `null` y falla en silencio. §4, §6.
6. **Quitar lo de escritorio/locomoción para obra sentada** (teleport, snap turn, smooth move, spectator, menú si no se usa). §8.
7. **Config de Quest (proyecto, NO pawn):** Mobile Multi-View, FFR, comodidad. §9.
8. **Verificar:** PIE / VR Preview solo para lógica; **el color y el tracking reales solo en el APK**. Ver [materials-vr.md](materials-vr.md).

---

## 1. Anatomía del VR Pawn estándar (VR Template) — jerarquía de componentes

**(A)** La página del VR Template **NO itemiza** la jerarquía; solo dice abrir el Blueprint `VRPawn` en `Content > VRTemplate > Blueprints`. — https://dev.epicgames.com/documentation/en-us/unreal-engine/vr-template-in-unreal-engine

**(B)** **No existe ninguna clase C++ `AVRPawn` ni `VROrigin`** en `Engine\Source` (grep = 0 matches). El pawn del template es **Blueprint puro**. El template en disco es `Templates\TP_VirtualRealityBP\`; su `Config\DefaultEngine.ini` fija `GlobalDefaultGameMode=/Game/XRFramework/Blueprints/BP_XRGameMode.BP_XRGameMode_C` y `EditorStartupMap=.../L_XRTemplate`. El contenido `.uasset` (los componentes reales del pawn) **no viene extraíble en esta instalación** (el `.upack` de 139 KB solo trae input mappings) → los nombres de componente de abajo salen del mapa vivo del proyecto en [vr.md](vr.md), no del código.

**Jerarquía típica (VR Template / XRFramework), confirmar contra el asset vivo:**

```
BP_VRPawn_SC (Pawn)
└─ VROrigin  (SceneComponent) ← ROOT en este pawn (verificado en proyecto)
   ├─ Camera  (CameraComponent)         ← el HMD; bLockToHmd=true, bUsePawnControlRotation=false
   ├─ MotionControllerLeft   (MotionControllerComponent, MotionSource="Left")
   │  ├─ (XRDeviceVisualizationComponent  o  StaticMesh de mando/mano)
   │  └─ (WidgetInteractionComponent / MotionControllerAim para láser de UI)
   └─ MotionControllerRight  (MotionControllerComponent, MotionSource="Right")
      └─ (idem)
```

Rol de cada uno:
- **VROrigin** — punto de anclaje del espacio de tracking (el "piso" del jugador). Todo lo demás cuelga de acá para moverse en bloque (teleport/snap turn mueven el pawn/VROrigin, no la cámara). En este pawn es el **RootComponent** (verificado por MCP en el proyecto).
- **Camera** — representa el casco. Se mueve sola cada frame por el HMD (§2). NO se le aplica control rotation.
- **MotionControllerLeft/Right** — se auto-posicionan cada frame con la pose del mando (§3).
- **Mallas de mano/mando** — hijas del MotionController para que lo sigan. **(A)** "the Static Mesh Component is a child of the Motion Controller Component otherwise the Static Mesh will not follow along." — Motion Controller Setup.
- **WidgetInteraction / puntero aim** — rayo para UI diegética; usa la pose **Aim** (§3).

---

## 2. La Camera y el HMD — `bLockToHmd`, y por qué NO `bUsePawnControlRotation`

**(B)** `CameraComponent.h:196-198`:
```
/** True if the camera's orientation and position should be locked to the HMD */
uint8 bLockToHmd : 1;
```
Default **`true`** (`CameraComponent.cpp:96` `bLockToHmd = true;`). Consumo en `HandleXRCamera()` (llamado desde `GetCameraView`, `CameraComponent.cpp:420-422`): si `bLockToHmd`, llama `XRCamera->UpdatePlayerCamera(Orientation, Position, DeltaTime)` y aplica `SetRelativeTransform(FTransform(Orientation, Position))` (`CameraComponent.cpp:401-413`). **Ese es el mecanismo por el que la cámara sigue al casco**: cada frame la pose del HMD se escribe como transform RELATIVO de la cámara respecto del VROrigin. Por eso mover el pawn mueve al jugador y girar la cabeza mueve solo la cámara.

**(B)** `bUsePawnControlRotation` — `CameraComponent.h:200-205`: "If this camera component is placed on a pawn, should it use the view/control rotation of the pawn where possible?". Se consume en `GetCameraView` (`CameraComponent.cpp:425+`): si es `true`, aplica `SetWorldRotation(PawnViewRotation)` **DESPUÉS** de que `HandleXRCamera` ya escribió la rotación del HMD (línea 407). **Las dos ramas son flags independientes — nada impide que disparen las dos.** Resultado si ambas están `true`: la control rotation del pawn se compone ENCIMA de la orientación del HMD ya horneada → **doble rotación** (la vista gira con el mando/mouse Y con la cabeza).

> **⚠ Matiz honesto (contra folclore):** **NO hay ningún comentario en el código que advierta de esto** — el "double rotation" se INFIERE del orden de ejecución, no está documentado como gotcha ni en (A) ni en (B). La regla práctica "en VR la cámara va con `bUsePawnControlRotation=false`" es correcta y así viene el template, pero preséntala como consecuencia del orden de ejecución, no como cita.

**Altura del jugador (sentado vs de pie) y recentrado:** se maneja por el tracking origin (§5), no por la cámara. **(A)** XR Best Practices: para sentado, "call the Set Tracking Origin function, with Origin set to 'Eye Level'" y "artificially raise the camera origin to the desired player height"; para de pie, "Origin ... set to Floor Level" y "camera origin ... set to 0, relative to the pawn's root." — https://dev.epicgames.com/documentation/unreal-engine/xr-best-practices-in-unreal-engine
> 🔴 **Contradicción doc vs práctica verificada del proyecto (ver §5).** Esta recomendación de Epic (Eye Level/elevar cámara para sentado) **NO es lo que este proyecto verificó como correcto** en OpenXR/Quest. Aquí Stage + Recenter conserva la altura REAL del usuario (`OpenXRHMD.cpp:938-945`), que es lo que se quiere para una obra sentada. Seguir [vr.md](vr.md), no la letra de XR Best Practices.

---

## 3. Motion controllers en el pawn

**(B)** `MotionControllerComponent.h` vive en el módulo **`HeadMountedDisplay`** (`Engine\Source\Runtime\HeadMountedDisplay\Public\MotionControllerComponent.h`), no en un plugin aparte.
- **`MotionSource`** (`h:26-28`): "Defines which pose this component should receive from the OpenXR Runtime. **Left/Right MotionSource is the same as LeftGrip/RightGrip.** See OpenXR specification for details on poses." → `FName MotionSource;`. **Grip** = pose de la mano cerrada (attach de objetos sostenidos); **Aim** = rayo de apuntado (láser de UI, arco de teleport, dirección de cañón). Fuentes válidas: `Left`/`Right`/`LeftGrip`/`RightGrip`/`LeftAim`/`RightAim`.
- **`PlayerIndex`** (`h:22-24`): "Which player index this motion controller should automatically follow".
- **Legacy `Hand`/`EControllerHand`: ya no existe como propiedad.** Solo quedan accesores deprecados `SetTrackingSource`/`GetTrackingSource` con `DeprecationMessage = "Please use the Motion Source property instead of Hand"` (`h:45-49`). → **Bindear por `MotionSource`, nunca por Hand.**
- **Cómo obtiene el transform cada frame:** `TickComponent` (`cpp:97`) → `PollControllerState_GameThread` (`cpp:106`) → `MotionController->GetControllerOrientationAndPosition(PlayerIndex, MotionSource, ...)` (`cpp:320`), vía la interfaz `IMotionController` resuelta por el registro de modular features (NO `IXRTrackingSystem` directo). Auto-tracked, sin código de usuario.

**Malla del mando/mano — `XRDeviceVisualizationComponent` (UE5.1+):**
**(B)** `Engine\Plugins\Runtime\XRBase\Source\XRBase\Public\XRDeviceVisualizationComponent.h`. Clase `UXRDeviceVisualizationComponent : public UStaticMeshComponent` (`h:18`). Propiedades: `bIsVisualizationActive` (`h:22-24`), `DisplayModelSource` (FName, `h:30-31`: "By default, the active XR system(s) will be queried and (if available) will provide a model for the associated device"), `CustomDisplayMesh` (`h:37-39`: "A mesh override that'll be displayed attached to this MotionController"), `DisplayMeshMaterialOverrides` (`h:44-46`), `MotionSource` (`h:57`).
> 🔴 **Hallazgo (B):** `bDisplayDeviceModel` / `DisplayModelSource` / `CustomDisplayMesh` **YA NO existen en `MotionControllerComponent`** en 5.8 (grep en todo el módulo `HeadMountedDisplay` = 0 matches). No están "deprecados en su lugar" — están **removidos**. El display del modelo migró por completo a `UXRDeviceVisualizationComponent`, que se engancha al MotionController padre por el delegate `OnActivateVisualizationComponent` (`MotionControllerComponent.h:70-71`). → **Para mostrar el mando/mano en 5.8: agregar un `XRDeviceVisualizationComponent` como hijo del MotionController.** El viejo checkbox "Display Device Model" del componente ya no está.

**(A)** La doc de Motion Controller Setup **todavía describe el flujo viejo** ("Display Device Model – Used to automatically render a model") y **no nombra** `XRDeviceVisualizationComponent`. → **doc desactualizada vs código.** — https://dev.epicgames.com/documentation/unreal-engine/motion-controller-component-setup-in-unreal-engine

**Pose/hand data:** `Get Motion Controller Data` → `Break XRMotionControllerData` (Grip/Aim Position/Rotation, arrays de dedos). ⚠ struct deprecado desde 5.5 a favor de `Get Motion Controller State`/`Get Hand Tracking State` — `⚠ verificar exposición BP en 5.8`. Detalle en [input.md](input.md) §6.

---

## 4. Spawn del pawn — GameMode, PlayerStart, y el timing de posesión

**(B)** `Engine\Source\Runtime\Engine\Private\GameModeBase.cpp`, orden verificado:
1. `RestartPlayerAtTransform` → `SpawnDefaultPawnAtTransform(NewPlayer, SpawnTransform)` (`cpp:1340`) → `GetWorld()->SpawnActor<APawn>(...)`. `SpawnActor` estándar (no diferido) corre construcción **y `BeginPlay`** de forma síncrona si el mundo ya empezó.
2. `NewPlayer->SetPawn(NewPawn)` (`cpp:1343`).
3. Recién después: `FinishRestartPlayer` → **`NewPlayer->Possess(NewPlayer->GetPawn())`** (`cpp:1364`).

> 🔴 **Confirmado en código: el `BeginPlay` del pawn corre ANTES de `Controller->Possess(Pawn)`.** Por eso `Add Mapping Context` en el BeginPlay del pawn se ejecuta con `GetController() == null` y **falla en silencio**. La solución robusta es hacerlo en **`Event Possessed`** (castear `New Controller` a PlayerController) o en el PlayerController. Ver §6 e [input.md](input.md) §5.

**`DefaultPawnClass` + `PlayerStart`:** el GameMode spawnea en el `PlayerStart` con `SpawnDefaultPawnAtTransform`. **(A)** no hay una sola página que fije el orden possession-vs-BeginPlay (la de Game Mode/Game State solo confirma que `HandleMatchHasStarted` dispara `BeginPlay` en todos los actores) → el orden autoritativo es **(B)**, arriba. **No hace falta tocar índices** de PlayerController ni de Pawn; el problema del "aparezco en cualquier lado" nunca fue de índices (ver [vr.md](vr.md)).

**PlayerStart Z:** al piso (Z≈0). Un PlayerStart arrastrado a mano queda ~88 (altura de cápsula por defecto) → **para pawn de VR eso está mal** porque con Stage la cámara ya suma la altura real sobre el VROrigin.

---

## 5. Tracking origin y recentrado (el corazón del setup)

**(B)** `Engine\Plugins\Runtime\OpenXR\Source\OpenXRHMD\Private\OpenXRHMD.cpp`:
- **`SetTrackingOrigin`** (`cpp:992+`) **solo muta `TrackingSpaceType`** (p. ej. `cpp:1020` `TrackingSpaceType = XR_REFERENCE_SPACE_TYPE_LOCAL_FLOOR;`). **No llama** `SetBasePosition`/`SetBaseOrientation`/`Recenter` → **elige el espacio de referencia, NO posiciona.** Probar Local/Stage/LocalFloor no puede arreglar la posición.
- **`ResetOrientationAndPosition`** → `Recenter(...)`. `Recenter` (`cpp:893`): `const XrTime TargetTime = GetDisplayTime();` y `cpp:896-900`:
```
if (TargetTime == 0)
{
    UE_LOGF(LogHMD, Warning, "Could not retrieve a valid head pose for recentering.");
    return;
}
```
→ **Sin pose XR válida se rinde con solo un warning.** En un BeginPlay puro la sesión suele no tener pose todavía → **el recentrado no ocurre y no falla visiblemente.** De ahí el **`Delay 0.5`** obligatorio antes de `ResetOrientationAndPosition`.
- El recentrado real aplica un OFFSET: `SetBasePosition` (`cpp:946`) + `SetBaseOrientation` (`cpp:953`), que mutan `BasePosition`/`BaseOrientation`. **Recentrar es un offset, no un teleport del pawn.**
- La diferencia que decide el setup (`cpp:938-945`): con **LOCAL** el recenter también recentra la altura (`NewPosition.Z = CurrentPosition.Z`); con **STAGE / LOCAL_FLOOR** conserva la altura real (`NewPosition.Z = 0.0f`).

**Receta del proyecto (en `BP_VRPawn_SC`):** `SetTrackingOrigin("Stage")` → `HideLoadingScreen` → `Delay 0.5` → `ResetOrientationAndPosition(Yaw=0)`. **Stage + Recenter = X/Y/yaw clavados al VROrigin y altura real conservada = lo correcto para obra sentada.** Detalle completo en [vr.md](vr.md).

**(A)** El enum de origen: `LOCAL_FLOOR` "For standing stationary experiences ... Z 0 set to match the floor"; `LOCAL` "For seated experiences ... centered around the HMDs initial position"; `STAGE` "For walking-around experiences ... within a defined play area." — HMDTrackingOrigin Python API (5.4). ⚠ `LOCAL_FLOOR` requiere `XR_EXT_local_floor`; si no está soportado **cae a STAGE en silencio** (`OpenXRHMD.cpp:1026`).
> 🔴 **Contradicción (A) vs proyecto:** la doc de Epic asocia "seated → LOCAL/Eye Level". Este proyecto verificó que **Stage** (no Local) es lo correcto para sentado en Quest, porque Local recentra también la Z e impone una altura fija a todos. Confiar en la verificación del proyecto.

---

## 6. Enhanced Input en el pawn VR (resumen — detalle en input.md)

Patrón del template: `Get Player Controller` → `Get Enhanced Input Local Player Subsystem` → **`Add Mapping Context`** (IMC, Priority). Por acción, un evento **`EnhancedInputAction IA_X`** (Triggered/Started/Ongoing/Completed/Canceled + Action Value tipado). IMCs del proyecto: `IMC_Default` (siempre), `IMC_Hands`, `IMC_Menu`, `IMC_Weapon_L/R` (por capas).
**(A)** El sample oficial "Enhanced Input in Parrot" agrega el mapping context **en el PlayerController**, no en el pawn: "Off of the `BeginPlay` node we add mapping context for `IMC_Gameplay`". — https://dev.epicgames.com/documentation/en-us/unreal-engine/enhanced-input-in-parrot-for-unreal-engine
**(D)** El "IMC on pawn BeginPlay falla silencioso" **no aparece en doc oficial**, solo en foros — PERO el mecanismo está **probado en (B)** (§4: BeginPlay antes de Possess). → hacerlo en `Event Possessed`. **No dupliques input.md** para el resto (tabla de triggers, modifiers, prioridades, haptics, debug).

---

## 7. Locomoción (obra SENTADA — probablemente NO se usa)

**(A)** El VR Template trae: **teleport** (stick derecho: dirección para elegir, soltar para teleportar), **snap turn** (stick izquierdo en la dirección de giro), **grab** (botón Grip + Sphere Trace, tres `GrabType`: Free/Snap/Custom), **menú** (botón menu, UMG). — VR Template page.
Para una obra sentada single-user donde el usuario no se desplaza: **teleport, snap turn y smooth move no aportan y son riesgo de comodidad.** Qué son (por si acaso): teleport = `Predict Projectile Path` → `Project Point to Navigation` → visual → `Teleport`; snap turn = input Axis1D → `AddActorWorldRotation` por incremento fijo (`SnapTurnDegrees`), gateado a un giro por flick. En `BP_XRPawn` viven como funciones (`StartTeleportTrace`/…/`TryTeleport`, `SnapTurn`) — ver [vr.md](vr.md).

---

## 8. Qué QUITAR para una obra sentada simple

Para simplificar `BP_VRPawn_SC` (o su padre) en una experiencia sentada, contemplativa, sin desplazamiento:
- **Teleport completo**: vars `ProjectedTeleportLocation`, `bValidTeleportLocation`, `bTeleportTraceActive`, `TeleportTracePathPositions`, `TeleportVisualizerReference`, y funciones `StartTeleportTrace`/`TeleportTrace`/`IsValidTeleportLocation`/`EndTeleportTrace`/`TryTeleport`. Quitar el `IA_Move`/`IA_Turn` de los IMC o no mapearlos.
- **Snap/smooth turn**: `SnapTurn`, `SnapTurnDegrees`, el binding de `IA_Turn`.
- **Grab** si no hay objetos que agarrar: `HeldComponentLeft/Right`, `GetGrabComponentNearMotionController`, `TryGrab`/`TryRelease`, los `IA_Grab_*`.
- **Menú láser** si la UI es diegética: `BP_Menu`, `WBP_Menu`, `IMC_Menu`, `ToggleMenu`, `MenuReference`, el `WidgetInteractionComponent`.
- **VR Spectator**: **(A)** "VR Spectator is not compatible with Mobile VR devices, such as Oculus Quest." → **quitarlo sí o sí** en Quest standalone.
- **NavMesh** del nivel si no hay teleport (no hace falta `RecastNavMesh`/`NavModifier_NoTeleport`).
Lo que **se queda:** VROrigin, Camera, los dos MotionController (aunque no haya grab, dan presencia de manos), el `SetTrackingOrigin` + `Delay` + `ResetOrientationAndPosition`, y el mínimo de Enhanced Input que uses (o ninguno).

---

## 9. Trampas de Quest standalone (móvil, no escritorio)

- **Nada del pawn es "de escritorio" per se**, pero SÍ hay que quitar **VR Spectator** (incompatible con Quest, (A)) y evitar features que asumen deferred/PC. El renderer es **móvil** — ver [materials-vr.md](materials-vr.md).
- **Mobile Multi-View:** **(A)** el VR Template recomienda habilitar **Project Settings > Rendering > VR > Mobile Multi-View** para VR móvil. Es **config de proyecto, no del pawn.** (El "compromiso de Multi-View" es folclore de UE4 — no aplica en 5.8, ver [materials-vr.md](materials-vr.md).)
- **Fixed Foveated Rendering — dónde se configura:**
  - **(B)** En **OpenXR base** es **cvar de config/startup, NO nodo de Blueprint**: `xr.OpenXRFBFoveationLevel` (`FBFoveationImageGenerator.cpp:9-14`, flag `ECVF_ReadOnly` → **no settable en runtime**), `xr.OpenXRFBFoveationDynamic`, `xr.OpenXRFBFoveationVerticalOffset`; y `xr.VRS.FoveationLevel` (`FoveatedImageGenerator.cpp:19-22`). **No hay ningún nodo `BlueprintCallable` de foveation en `Engine\Source`/OpenXR** (grep = 0).
  - **(A)** El **plugin Meta XR (OculusXR)** SÍ expone un nodo **`Set Foveated Rendering Level`** (`EOculusXRFoveatedRenderingLevel`: Off/Low/Medium/High/HighTop) además del Project Setting. — https://developers.meta.com/horizon/documentation/unreal/unreal-ffr/
  > 🔴 **La diferencia importa según qué plugin use el proyecto:** con **OpenXR nativo → FFR es config/cvar** (no lo pongas en el pawn). Con **Meta XR plugin → hay nodo BP**. Verificar cuál está activo antes de decidir. En cualquier caso NO es una propiedad del pawn. (Ver también [profiling-quest.md](profiling-quest.md) para FFR nativo `Set Foveated Rendering Level` y por qué va antes que Dynamic Resolution.)
- **Comodidad / vignette de locomoción:** **(B)** **NO existe ningún componente/clase de vignette de confort VR en el motor** (todos los `Vignette` en `Engine\Source` son el post-process cinematográfico genérico; no hay `VRComfort` ni toggle de confort). Confirmado ausente, no es adivinanza. **(A)** Meta recomienda vignette al moverse ("Use vignettes to darken or occlude screen edges during movement") pero es guía **agnóstica de motor**, no una feature lista de Epic. → En una obra **sentada sin locomoción, el vignette de confort no aplica**; si algún día hay movimiento, hay que construirlo (post-process radial gateado por velocidad), no viene hecho. — https://developers.meta.com/horizon/design/locomotion-comfort-usability/
- **`bLockToHmd` + late update:** el HMD hace **late update** de la cámara (`SetupLateUpdate`, `CameraComponent.cpp:399`). No metas lógica que dependa de leer la pose de la cámara "temprano" en el frame; en Quest el timing de frame es ajustado (72 fps = 13.9 ms).
- **Timing de possession/HMD/recenter** (resumen de las tres trampas): BeginPlay corre antes de Possess (§4) → input en `Event Possessed`; la pose XR no está lista en BeginPlay (§5) → recenter tras `Delay`; Stage no posiciona (§5) → el que posiciona es `ResetOrientationAndPosition`.

---

## Fuentes
**(A)** VR Template https://dev.epicgames.com/documentation/en-us/unreal-engine/vr-template-in-unreal-engine · Motion Controller Setup https://dev.epicgames.com/documentation/unreal-engine/motion-controller-component-setup-in-unreal-engine · XR Best Practices https://dev.epicgames.com/documentation/unreal-engine/xr-best-practices-in-unreal-engine · HMDTrackingOrigin (Python API) https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/HMDTrackingOrigin · Enhanced Input in Parrot https://dev.epicgames.com/documentation/en-us/unreal-engine/enhanced-input-in-parrot-for-unreal-engine · Meta FFR (Unreal) https://developers.meta.com/horizon/documentation/unreal/unreal-ffr/ · Meta Locomotion Comfort https://developers.meta.com/horizon/design/locomotion-comfort-usability/
**(B)** `Engine\Source\Runtime\Engine\Classes\Camera\CameraComponent.h` · `...\Private\Camera\CameraComponent.cpp` · `Engine\Source\Runtime\HeadMountedDisplay\Public\MotionControllerComponent.h` · `Engine\Plugins\Runtime\XRBase\Source\XRBase\Public\XRDeviceVisualizationComponent.h` · `Engine\Source\Runtime\Engine\Private\GameModeBase.cpp` · `Engine\Plugins\Runtime\OpenXR\Source\OpenXRHMD\Private\OpenXRHMD.cpp` · `Engine\Plugins\Runtime\OpenXR\Source\OpenXRHMD\Private\FBFoveationImageGenerator.cpp` · `Engine\Source\Runtime\Renderer\Private\VariableRateShading\FoveatedImageGenerator.cpp` (todos en `C:\Program Files\Epic Games\UE_5.8`, verificados en esta instalación).
