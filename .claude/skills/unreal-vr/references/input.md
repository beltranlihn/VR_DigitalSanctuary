# Enhanced Input + motion controllers (operational depth) — UE 5.8, OpenXR/PICO

Deep reference for building ALL interaction on BP_XRPawn. Names are exact Blueprint display names; `[verify]` = confirm live before relying on it. Companion to vr.md (project map) and nodes.md (verified type_ids).

## 1. Input Action (IA_) anatomy
Value Types (`EInputActionValueType`):
| Value Type | VR mapping |
|---|---|
| Digital (bool) | Buttons A/B/X/Y, Menu, trigger/grip *click*, stick click |
| Axis1D (float) | Trigger pull (analog), grip squeeze (analog) |
| Axis2D (Vector2D) | Thumbstick 2D |
| Axis3D (Vector) | Rare (3D device data) |

Bool key → Axis IA reads 0/1; axis key → Digital IA is true past actuation threshold. Key properties:
- **Consume Input** (default true) — higher-priority IMC mapping of the same key swallows it for lower ones. THE mechanism behind context layering.
- **Trigger when Paused**; **Reserve All Mappings** (don't let higher-priority contexts override); **Accumulation Behavior** (multiple keys → same IA: Take Highest Abs / Cumulative).
- Triggers/Modifiers exist at TWO levels: per-mapping (IMC row) runs first, then action-level [verify order in 5.8].

## 2. Triggers → event firing (critical table)
States: `None → Ongoing → Triggered`. Events from transitions:
| Transition | Events |
|---|---|
| None→Ongoing | Started |
| None→Triggered | Started + Triggered (same frame) |
| Ongoing→Ongoing | Ongoing |
| Ongoing→Triggered | Triggered |
| Triggered→None | Completed |
| Ongoing→None | **Canceled** |

Per-trigger (no trigger = implicit **Down**):
- **Down**: Triggered every tick while actuated; Completed on release.
- **Pressed**: Triggered once on press; Completed on release.
- **Released**: Triggered on release (Started on press, Ongoing held).
- **Hold** (HoldTimeThreshold, bIsOneShot): Triggered after threshold (once or per-tick); **Canceled** if released early.
- **Hold And Release**: Triggered on release only if held ≥ threshold; else Canceled.
- **Tap** (TapReleaseTimeThreshold): Triggered on quick release; Canceled if held too long.
- **Pulse** (Interval, bTriggerOnStart, TriggerLimit): Triggered per interval while held.
- **Chorded Action** (implicit): only fires while its ChordAction IA is Triggered — modifier-key pattern.
- **Combo**: IA sequence in time windows.

Practical VR picks: grab = Pressed/Released pair (o Down) en grip · hold-to-charge = Hold · teleport = stick Axis2D con Started(comenzar arco)/Completed(ejecutar) · snap turn = Pressed en eje del stick con Dead Zone.
Gotcha: con trigger Pressed, usá Started para "press", Triggered para continuo, Completed para release — mezclar Triggered+Completed aparenta doble disparo.

## 3. Modifiers (orden importa: top-to-bottom; Dead Zone antes de curvas/escalar)
- **Dead Zone** (Lower 0.2 / Upper 1.0; Type **Radial** para sticks 2D, Axial por eje) — obligatorio en IA_Move/IA_Turn.
- **Negate** (por eje) — invertir stick.
- **Swizzle Input Axis Values** (Order YXZ…) — mapear key 1D al eje Y de un Axis2D.
- **Scalar** — sensibilidad. **Scale By Delta Time** — smooth turn frame-independiente.
- **Smooth** / **Smooth Delta** [verify 5.8] — suavizar analógicos ruidosos.
- **Response Curve - Exponential / User Defined** — control fino cerca del centro.
- FOV Scaling / To World Space / Modifier Collection — raros en VR.

## 4. Input Mapping Contexts (IMC_)
- Priority int en `Add Mapping Context`; mayor = se evalúa primero. Mismo key en varios contexts: gana el de mayor prioridad SI su IA consume (Consume Input true); si no, pasa hacia abajo. Keys distintos coexisten.
- Nodos runtime (target **Enhanced Input Local Player Subsystem**): **Add Mapping Context** (IMC, Priority, Options), **Remove Mapping Context**, **Clear All Mappings**, **Query Keys Mapped to Action**.
- `Options` (FModifyContextOptions): **Ignore All Pressed Keys Until Release** (default TRUE — un key ya presionado al agregar el context no dispara hasta soltarse y re-presionar: importa al swapear IMC_Weapon con grip sostenido), **Force Immediately**, **Notify User Settings**.
- Patrón de capas del proyecto: `IMC_Default` (prio 0, siempre) · `IMC_Hands` · `IMC_Menu` agregado con prioridad ALTA al abrir menú (stick scrollea UI, consume) · `IMC_Weapon_L/R` agregado al agarrar arma en esa mano, removido al soltar.

## 5. Wiring en Blueprints
- Habilitar: **Get Player Controller** → **Get Enhanced Input Local Player Subsystem** → **Add Mapping Context**.
- Evento por acción: **EnhancedInputAction IA_X** — exec: Triggered/Started/Ongoing/Completed/Canceled; data: **Action Value** (tipado al Value Type), Elapsed Seconds, Triggered Seconds [verify pin set].
- Poll: **Get Bound Action Value** (Enhanced Input Component) [verify exposición BP].
- Testing sin casco: **Inject Input for Action** / **Inject Input Vector for Action**; consola `Input.+key <KeyName>` / `Input.-key`.
- ⚠ **Timing de posesión**: en pawn BeginPlay el controller puede no estar asignado → Add Mapping Context falla silencioso. Robusto: hacerlo en **Event Possessed** (cast New Controller a PlayerController), o en PlayerController BeginPlay, o BeginPlay con cast validado a Get Controller.

## 6. Motion controllers y haptics
- `MotionControllerComponent.Motion Source`: `Left`/`Right` (= grip), `LeftGrip`/`RightGrip`, `LeftAim`/`RightAim` (+ `Enumerate Motion Sources`; Palm [verify en PICO]). **Grip** = pose de mano cerrada (attach de objetos sostenidos) · **Aim** = rayo de apuntado (UI, arco de teleport, dirección de cañón).
- **Get Motion Controller Data** (input Hand) → **Break XRMotionControllerData**: bValid, TrackingStatus, GripPosition/Rotation, AimPosition/Rotation, HandKeyPositions/Rotations/Radii, bIsGrasped [verify campos 5.8]. Nota: struct deprecado desde 5.5 a favor de **Get Motion Controller State** / **Get Hand Tracking State** [verify] — ambos deberían existir en 5.8.
- **Haptics** (target Player Controller): **Play Haptic Effect** (efecto, Hand, Scale, Loop), **Stop Haptic Effect**, **Set Haptics by Value** (Frequency, Amplitude, Hand — rumble continuo). Assets: Haptic Feedback Effect **Curve** / **Buffer** / **SoundWave**. El GrabComponent expone `OnGrabHapticEffect`.
- **Velocidad para lanzar**: XRMotionControllerData NO trae velocity; `Get Component Velocity` del MotionController no es confiable [verify]. Patrón estándar: ring buffer de posiciones grip por tick → al soltar, **Set Physics Linear Velocity** = delta promedio / dt (últimos ~3–5 frames); ídem angular.

## 7. Debug de input
- Consola: **`showdebug enhancedinput`** (IMCs activos, valores, estados de trigger en vivo) · `showdebug devices`.
- "No dispara", causas en orden VR: 1) IMC nunca agregado (o corrió antes de posesión) · 2) controller equivocado / pawn sin poseer · 3) key consumido por IMC de mayor prioridad · 4) Input Mode UI Only / foco de widget se lo traga (usar Set Input Mode Game and UI) · 5) pin equivocado para el trigger (esperar Triggered de un Hold antes del umbral) · 6) Dead Zone come valores chicos · 7) el runtime no provee ese key en el interaction profile activo — en PICO: mapear TODAS las acciones de un profile o el runtime puede negarse a emular (bindings parciales bloquean emulación OpenXR).

## 8. Específicos del template (BP_XRPawn = VRPawn renombrado en 5.6+)
- IMCs se agregan vía subsystem al inicio [verify evento exacto en nuestro asset]; IMC_Menu / IMC_Weapon_* se agregan/quitan contextualmente.
- Flujo de grab documentado: IA_Grab_* **Started** → `GetGrabComponentNearMotionController` (Sphere Trace de objetos `PhysicsActor` alrededor del grip; el GrabComponent pone ese collision profile en su parent al BeginPlay) → `TryGrab` (attach al MotionController de esa mano + haptic) · IA **Completed** → `TryRelease`. `GrabType`: Free (mantiene transform relativo) / Snap (alinea fijo) / Custom (solo dispara eventos). Interfaz **VRInteraction BPI** [verify — nuestro map vio `BPI_PawnAnim`] evita casts por clase.
- Teleport: stick derecho — Started inicia traza/arco, dirección del stick fija orientación de aterrizaje, Completed ejecuta; restringido a NavMesh (`NavModifier_NoTeleport`). Snap turn: stick izq X con Dead Zone → rotación fija por actuación.
- ⚠ La fuente autoritativa de esta sección son LOS ASSETS del proyecto (abrir IMC_* y el grafo de BP_XRPawn) — pendiente el deep-map en vivo.

## Fuentes
Enhanced Input (5.8): https://dev.epicgames.com/documentation/en-us/unreal-engine/enhanced-input-in-unreal-engine · Triggers/Modifiers: https://unrealdirective.com/articles/enhanced-input-what-you-need-to-know/ · OpenXR input (grip/aim, profiles): https://dev.epicgames.com/documentation/en-us/unreal-engine/openxr-input-in-unreal-engine · Motion Controller setup: https://dev.epicgames.com/documentation/unreal-engine/motion-controller-component-setup-in-unreal-engine · VR Template: https://dev.epicgames.com/documentation/en-us/unreal-engine/vr-template-in-unreal-engine
