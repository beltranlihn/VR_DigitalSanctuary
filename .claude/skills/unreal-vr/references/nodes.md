# Verified node catalog (grows with use)

Only nodes we've confirmed live (exact `type_id` + pins). For anything else: `find_node_types(graph, "<specific filter>", [])` → `get_node_type_pins(graph, type_id)`. Add new verified nodes here after using them.

Pin notation: `in`/`out`; exec pins are `execute`/`then`. Output data pins auto-bind in DSL as `_lowercasedname`.

## Flow / utility
- **`Actor|GetActorOfClass`** — in: `ActorClass`(class-ref); out: `ReturnValue`(Actor). Impure (has exec).
- **`Utilities|Casting|CastTo<ClassName>`** — in: `Object`; multi-exec `(:then …)`/`(:CastFailed)`; cast result auto-var. E.g. `Utilities|Casting|CastToBP_OSCReceiver` (keeps the underscore).
- **`Utilities|IsValid`** — in: object; multi-exec `(:"Is Valid" …)`/`(:"Is Not Valid" …)`.
- **`EventDispatchers|CreateEvent`** — in: `self`(Object); out: `OutputDelegate`(Delegate). Function is a node PROPERTY → set via `set_create_event_function` (needs the delegate pin connected first).
- Switch aliases: `int`→`Utilities|FlowControl|Switch|SwitchOnInt`, `string`→`…SwitchOnString`, `name`→`…SwitchOnName`. String-switch outputs are `Case_0/1/…`+`Default` (match strings not settable via API).

## Math / transform
- **`Math|Vector|MakeVector`** — in `:X :Y :Z`(float); out `ReturnValue`(Vector).
- **`Transformation|SetRelativeScale3D`** — in: `self`(SceneComponent target, pin index 1), `NewScale3D`(Vector, index 2); out `then`. Positional: `(Transformation|SetRelativeScale3D <component> <vector>)`.

## Variables
- On self: `(Variables|Default|Get<Var>)` / `(Variables|Default|Set<Var> value)`.
- Component getter (auto-created): `Variables|Default|Get<ComponentName>` (e.g. `GetSphere`).
- On another object: `Class|<ClassNoUnderscore>|Get<Var>` with target as arg — e.g. `(Class|BPOSCReceiver|GetScale osc)`. ⚠ DSL may fuzzy-match to a same-named node of another class; verify with `get_node_infos` (a correct read is a K2Node_VariableGet whose `self` pin type is your class ref).

## OSC plugin (`/Script/OSC`) — category `Audio|OSC`
Server lifecycle:
- **`Audio|OSC|CreateOSCServer`** — in: `ReceiveIPAddress`(string, "0.0.0.0"=any), `Port`(int), `bMulticastLoopback`(bool), `bStartListening`(bool), `ServerName`(string), `Outer`(object?); out: `ReturnValue`(OSCServer). Store in a member var so it isn't GC'd.
- **`Audio|OSC|AssignOnOscMessageReceived`** — in: `execute`, `self`(OSCServer target, index 1), `Delegate`(index 2, auto-wired to a generated event); out `then`. **Creating this node auto-generates a correctly-typed custom event `OnOscMessageReceived_Event (Message, IPAddress, Port)`** — write your handler body into that event. This is the reliable way to bind the delegate.
- (`Audio|OSC|BindEventtoOnOscMessageReceived` is the raw bind — needs a CreateEvent; prefer Assign.)
- **`Audio|OSC|Stop`** / **`Audio|OSC|Listen`** / **`Audio|OSC|SetMulticastLoopback`** / **`Audio|OSC|GetPort`** / **`Audio|OSC|GetIpAddress`**.

Message parsing (Message is `OSCMessage` struct, `/Script/OSC.OSCMessage`, by-ref):
- **`Audio|OSC|GetOSCMessageAddress`** — in `Message`; out `ReturnValue`(OSCAddress struct).
- **`Audio|OSC|ConvertOSCAddressToString`** — in `Address`(OSCAddress); out `ReturnValue`(string).
- **`Audio|OSC|GetOSCMessageFloatAtIndex`** — in `Message`, `Index`(int, def 0); out `Value`(float), `ReturnValue`(bool success).
- Also: `GetOSCMessageIntegeratIndex`, `GetOSCMessageBoolAtIndex`, `GetOSCMessageStringatIndex`, and array forms `GetOSCMessageFloats`/`GetOSCMessageIntegers`/`GetOSCMessageStrings`/`GetOSCMessageBools`.
- Delegate signature `FOSCReceivedMessageEvent(const FOSCMessage& Message, const FString& IPAddress, int32 Port)`.

## Components
- Add primitives via `PrimitiveTools.add_*` on the CDO (see toolsets.md). Getter node: `Variables|Default|Get<Name>`.
- **Material de un componente**: `ObjectTools.set_properties` sobre el componente del CDO → `{"OverrideMaterials": ["/Game/.../M_X.M_X"], "CastShadow": false}`. Verificar con `get_properties`.

## Niveles
- **Crear un nivel**: no hay tool de "New Level" → **duplicar** `/Engine/Maps/Templates/Template_Default` (el Basic: floor, sky, luz, fog, nubes, PlayerStart) con `AssetTools.duplicate`, **guardarlo** (`save_assets` — si no, `load_level` falla con "unsaved changes"), y luego vaciarlo/poblarlo con `SceneTools.remove_from_scene` / `add_to_scene_from_asset`.
- Otros templates disponibles: `/Engine/Maps/Templates/VR-Basic`, `OpenWorld`, `TimeOfDay_Default`.

## Materiales
- **Flags del material** (TwoSided, BlendMode, ShadingModel) NO son nodos, son propiedades → `ObjectTools.set_properties` con `{"TwoSided": true, "BlendMode": "BLEND_Translucent", "ShadingModel": "MSM_Unlit"}`. Verificado.
- **Parámetros**: `MaterialTools.add_expression` con `/Script/Engine.MaterialExpressionScalarParameter` o `...VectorParameter`; nombrarlos con `set_properties` → `{"ParameterName": "X", "DefaultValue": …}` (LinearColor = `{"R":0,"G":0,"B":0,"A":1}`).
- Salidas: VectorParameter = `RGB/R/G/B/A/RGBA`; ScalarParameter = `""` (cadena vacía).
- Conectar: `connect_to_output(expr, output_name, "MP_EmissiveColor" | "MP_Opacity" | …)`. Verificar con `get_property_input`. Cerrar con `recompile`.

## Nodos verificados (fade / runtime)
- **`Rendering|Material|CreateDynamicMaterialInstance`** — in: `self`(PrimitiveComponent), `ElementIndex`(int), `SourceMaterial`, `OptionalName`; out: MID.
- **`Rendering|Material|SetScalarParameterValue`** / **`SetVectorParameterValue`** — target = el MID. ⚠ hay varios homónimos; verificar el nodo creado.
- **`Actor|GetComponentByClass`** — in: actor, class path quoteado (ej. `"/Script/Engine.CameraComponent"`).
- **`Transformation|AttachActorToComponent`** — in: `self`(Actor), `Parent`(SceneComponent), `SocketName`, `LocationRule`/`RotationRule`/`ScaleRule` (`"SnapToTarget"`/`"KeepRelative"`/`"KeepWorld"`), `bWeldSimulatedBodies`.
- **`Math|Float|Clamp(Float)`** — `Value`, `Min`(def 0.0), `Max`(def 1.0) · **`Math|Float|Lerp`** · **`Math|Float|Max(Float)`**.
- ⚠ **No existen**: `Math|Float|max` (minúscula), `FInterpConstantTo`, `FInterpTo`. Sí existe `Math|Float|FInterpEaseinOut`.

## XR / mandos — pose, velocidad, háptico (verificados)
- **`Input|XRTracking|GetMotionControllerState`** — in: `WorldContext`, `XRSpaceType`(def `UnrealWorldSpace`), `Hand`(EControllerHand), `ControllerPoseType`(def `Aim`); out: `MotionControllerState`. Break con **`Utilities|Struct|BreakXRMotionControllerState`** → `bValid`, `DeviceName`, `XRSpaceType`, `Hand`, `TrackingStatus`, `XRControllerPoseType`, `ControllerLocation`(Vector), `ControllerRotation`(**Quat**). Impuro.
- ⚠ **No existe `GetMotionControllerData`** (el nombre de los docs de Epic). Es `GetMotionControllerState`.
- **Vía más simple si el pawn ya tiene los componentes**: cast a `BP_VRPawn_SC` → **`Class|BPVRPawnSC|GetMotionController{Left,Right}{Grip,Aim}`** → devuelve el `MotionControllerComponent`. Grip = donde está la mano; Aim = el rayo para punteros.
- **`MotionControllerUpdate|GetLinearVelocity`** — in: `self`(**MotionControllerComponent**); out: `OutLinearVelocity`(Vector, cm/s), `ReturnValue`(bool). **PURO.**
- **`MotionControllerUpdate|GetAngularVelocity`** — igual pero out `OutAngularVelocity` es un **Rotator** (°/s), no un Vector. Para magnitud: `MakeVector(.roll, .pitch, .yaw)` → `VectorLength`.
  - Vienen del runtime OpenXR (IMU) → **mejor que derivar la pose por diferencia finita** entre dos frames ruidosos.
- **`Game|Feedback|SetHapticsByValue`** — ⚠ `find_node_types` lo lista como `SetHapticsbyValue` (b minúscula) pero el **type_id real es con B mayúscula**. in: `self`(**PlayerController**, NO el pawn), `Frequency`(float 0-1), `Amplitude`(float 0-1), `Hand`(EControllerHand, default `"Left"`). Es **continuo** → para un pulso: encender → `Utilities|FlowControl|Delay` → apagar con 0/0, dentro de un custom event (nunca un Delay en Tick).
- También: `Game|Feedback|PlayHapticEffect` (necesita un asset HapticFeedbackEffect_*), `StopHapticEffect`, `SetDisableHaptics`.
- **`Transformation|GetForwardVector` / `GetRightVector` / `GetUpVector`** — in: `self`(**SceneComponent**); out: Vector. (Los `Math|Vector|Get*Vector` son los que toman un Rotator.)

## Math verificados (extra)
- **`Math|Float|Absolute(Float)`** (NO `Math|Float|Abs`) · **`Math|Vector|VectorLength`** (NO `VSize`) · `VectorLengthSquared`, `VectorLengthXY`.
- **`Math|Vector|BreakVector`** · `Math|Rotator|BreakRotator`.
- **El DSL resuelve `+ - *` sobre Vectors** → `Math|Vector|vector+vector`, `vector-vector`, `vector*vector`. Y `Vector * float` funciona. Permite hacer un pipeline de 3 ejes con **una** cadena de nodos en vez de triplicar la lógica.
- Strings: **`Utilities|String|ToString(Float)`** / `ToString(Vector)` / `ToString(Integer)` / `ToString(Boolean)` · `Utilities|String|Append` es binario (A,B) → anidar para concatenar más.

---
### Validated snippets

Runtime cross-BP pull (receiver caches ref, reads a var each tick):
```
(event EventBeginPlay
  (bind found (Actor|GetActorOfClass :ActorClass "/Game/OSC/BP_OSCReceiver.BP_OSCReceiver_C"))
  (bind osc (Utilities|Casting|CastToBP_OSCReceiver :Object found)
    (:then (Variables|Default|SetOSCRef osc))
    (:CastFailed)))

(event EventTick (DeltaSeconds)
  (bind osc (Variables|Default|GetOSCRef))
  (Utilities|IsValid osc
    (:"Is Valid"
      (bind s (Class|BPOSCReceiver|GetScale osc))
      (Transformation|SetRelativeScale3D (Variables|Default|GetSphere)
        (Math|Vector|MakeVector :X s :Y s :Z s)))
    (:"Is Not Valid")))
```

OSC server + handler (write handler body into the Assign-generated event, NOT via a fresh switch if one exists):
```
(event EventBeginPlay
  (bind srv (Audio|OSC|CreateOSCServer :ReceiveIPAddress "0.0.0.0" :Port 8000
             :bMulticastLoopback false :bStartListening true :ServerName "Srv"))
  (Variables|Default|SetOSCServer srv)
  (Audio|OSC|AssignOnOscMessageReceived srv (AddEvent|Custom|OnOscMessageReceived_Event)))

(event Custom|OnOscMessageReceived_Event (Message IPAddress Port)
  (bind addr (Audio|OSC|GetOSCMessageAddress Message))
  (bind s (Audio|OSC|ConvertOSCAddressToString addr))
  (switch Utilities|FlowControl|Switch|SwitchonString s
    (:Case_0 …)))   ; set the case match string ("/muse" etc.) in the editor Details panel
```
