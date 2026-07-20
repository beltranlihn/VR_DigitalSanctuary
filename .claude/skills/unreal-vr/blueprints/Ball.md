# Ball — progress tracker

- **refPath**: `/Game/Asset/Ball.Ball` (class `Ball_C`)
- **parent**: Actor · **in level**: yes (`Ball_C_0` at (0,0,100) in L_XRTemplate)
- **Purpose**: A sphere whose scale is driven live by `BP_OSCReceiver.scale` — the cross-BP communication test.
- **Status**: 🟢 done (working)

## Components
- `Sphere` (StaticMeshComponent, engine sphere, radius 50) — added via PrimitiveTools on the CDO. Getter: `Variables|Default|GetSphere`.

## Variables
- `OSCRef` : BP_OSCReceiver ref — cached reference to the OSC actor. public.

## Graphs
- **EventBeginPlay**: `GetActorOfClass(BP_OSCReceiver_C)` → `CastToBP_OSCReceiver` → `SetOSCRef`.
- **EventTick(DeltaSeconds)**: `GetOSCRef` → `IsValid` → [Is Valid] → `GetScale(OSCRef)` → `SetRelativeScale3D(Sphere, MakeVector(s,s,s))`.

## Done ✅
- Sphere component + auto-find-and-cache of the OSC actor + live scale drive.

## TODO / next
- Optional: remap the raw float to a comfortable scale range (e.g. clamp / lerp) so scale 0 doesn't hide the sphere.
- Optional: give the sphere a material.

## Open questions / risks
- Pull model on Tick (Ball reads OSCRef each frame). Fine for one ball; if many, consider a push/event approach.

## Session log
- 2026-07-15: created in /Game/Asset; sphere on CDO; BeginPlay cache + Tick scale from OSCRef.scale; placed in level.
