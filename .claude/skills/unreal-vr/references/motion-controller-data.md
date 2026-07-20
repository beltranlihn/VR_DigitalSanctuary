# Datos de un motion controller (Meta Quest 3 Touch) en UE 5.8 / OpenXR

Target: Quest 3 standalone, OpenXR, backend NativeOpenXR, renderer móvil. Contexto: BP_BreathProbe — mando apoyado plano sobre el abdomen, detección de micro-inclinaciones de respiración. Ver también `motion-detection-thresholds.md` (filtros/umbrales) y `nodes.md` sección "XR / mandos" (catálogo de nodos ya verificados en el editor).

**Clasificación de fuentes:** **(A)** doc oficial Epic/Meta con URL. **(B)** código del motor UE 5.8, archivo:línea. **(C)** spec OpenXR (Khronos, fuente de las specs en GitHub `KhronosGroup/OpenXR-Docs`, texto normativo idéntico al de `registry.khronos.org` que bloquea fetch automatizado con 403/CAPTCHA — se citó vía el repo fuente). **(D)** folclore/foros, sin fuente verificable — marcado explícitamente.

---

## Tabla resumen: dato → nodo → unidad → marco de referencia

| Dato | Nodo Blueprint | Clase / origen | Unidad | Marco de referencia | Disponible en Quest 3 OpenXR |
|---|---|---|---|---|---|
| Posición | `MotionControllerComponent` → `GetComponentTransform` / `GetRelativeTransform`, o `Input\|XRTracking\|GetMotionControllerState`→`ControllerLocation` | `UMotionControllerComponent` (pose se aplica a `SetRelativeLocationAndRotation` cada Tick) | cm (world) | Unreal World Space (tras `TrackingToWorldTransform`) o `XRTrackingSpace` según `EXRSpaceType` | Sí |
| Orientación | igual — `GetComponentTransform().GetRotation()` / `ControllerRotation` (Quat) | igual | Quat / Rotator | igual | Sí |
| Velocidad lineal | `MotionControllerUpdate\|GetLinearVelocity` | `UMotionControllerComponent::GetLinearVelocity` | cm/s | World space (rotado por `TrackingToWorldTransform`, **NO** late-updated) | Sí, vía `XR_SPACE_VELOCITY` |
| Velocidad angular | `MotionControllerUpdate\|GetAngularVelocity` | `UMotionControllerComponent::GetAngularVelocity` | Rotator, °/s (internamente eje+magnitud en rad/s) | World space, **no** late-updated | Sí, vía `XR_SPACE_VELOCITY` |
| Aceleración lineal | `MotionControllerUpdate\|GetLinearAcceleration` | `UMotionControllerComponent::GetLinearAcceleration` | cm/s² | World space | 🔴 **NO** — requiere `XR_EPIC_space_acceleration`, extensión propietaria de Epic no anunciada por el runtime de Meta |
| Aceleración angular | — (no existe función Blueprint equivalente) | — | — | — | 🔴 No expuesta ni por el motor |
| Tracking válido (bool) | `MotionControllerComponent::IsTracked` (BlueprintPure) / `TrackingStatus`(`ETrackingStatus`) / `GetMotionControllerState`→`bValid`+`TrackingStatus` | `UMotionControllerComponent` | bool / enum(`NotTracked`,`InertialOnly`,`Tracked`) | — | Sí |
| Pose Aim/Grip/Palm por separado | `Input\|XRTracking\|GetMotionControllerState` (`ControllerPoseType` = Aim/Grip/Palm) | `FOpenXRHMD::GetMotionControllerState` (override) | Vector+Quat | Unreal World o XR Tracking Space | Sí (Aim y Grip siempre; Palm si `XR_EXT_palm_pose` o `grip_surface` OpenXR 1.1) |
| Datos crudos IMU (accel/gyro) | `GetRawSensorData` | Meta XR Plugin (OVRPlugin legacy) | m/s², rad/s | — | 🔴 **NO implementado en NativeOpenXR** (confirmado por Meta) |

---

## 1. Qué expone OpenXR/UE 5.8 para un motion controller

**Pose (posición + orientación).** `FOpenXRHMD::GetPoseForTime` llama `xrLocateSpace(DeviceSpace.Space, TrackingSpace, TargetTime, &DeviceLocation)` y solo acepta el resultado si `XR_SPACE_LOCATION_ORIENTATION_VALID_BIT` y `XR_SPACE_LOCATION_POSITION_VALID_BIT` están seteados **(B)** `Engine\Plugins\Runtime\OpenXR\Source\OpenXRHMD\Private\OpenXRHMD.cpp:795-843`.

**Velocidad lineal/angular.** Mismo `xrLocateSpace`, encadenando una `XrSpaceVelocity` al `XrSpaceLocation`. Se toma si el bit correspondiente está en `velocityFlags` **(B)** `OpenXRHMD.cpp:830-858`:
```cpp
XrSpaceVelocity DeviceVelocity { XR_TYPE_SPACE_VELOCITY, DeviceAccelerationPtr };
XrSpaceLocation DeviceLocation { XR_TYPE_SPACE_LOCATION, &DeviceVelocity };
XR_ENSURE(xrLocateSpace(DeviceSpace.Space, PipelineState.TrackingSpace->Handle, TargetTime, &DeviceLocation));
...
if (DeviceVelocity.velocityFlags & XR_SPACE_VELOCITY_LINEAR_VALID_BIT) { bProvidedLinearVelocity = true; LinearVelocity = ToFVector(...); }
if (DeviceVelocity.velocityFlags & XR_SPACE_VELOCITY_ANGULAR_VALID_BIT) { bProvidedAngularVelocity = true; AngularVelocityAsAxisAndLength = -ToFVector(DeviceVelocity.angularVelocity); }
```
Spec **(C)**, `spaces.adoc`: `linearVelocity` = *"relative linear velocity of the origin of `space` with respect to and expressed in the reference frame of `baseSpace`, in units of meters per second"*; `angularVelocity` = *"relative angular velocity of `space` with respect to `baseSpace`... in radians per second... follows the right-hand rule"*.

**Aceleración.** Encadenada como `XrSpaceAccelerationEPIC` (extensión propietaria de Epic), solo si `bSpaceAccelerationSupported` **(B)** `OpenXRHMD.cpp:830-831,860-864`, y ese flag se calcula así:
```cpp
bSpaceAccelerationSupported = IsExtensionEnabled(XR_EPIC_SPACE_ACCELERATION_NAME); // OpenXRHMD.cpp:1689
```
🔴 Confirmado en `Epic_openxr.h:24-40` (`#define XR_EPIC_space_acceleration 1`) — es un header interno de Epic, no del registro Khronos, y el runtime de Meta en Quest 3 no la anuncia. Coincide con lo ya sabido: sin esta extensión, `bProvidedLinearAcceleration` queda `false` siempre y `GetLinearAcceleration` devuelve `false` con el vector sin tocar.

**Tracking state.** `ETrackingStatus{NotTracked, InertialOnly, Tracked}` **(B)** `Engine\Source\Runtime\HeadMountedDisplay\Public\IMotionController.h:14-20`. `IsTracked()` en el componente simplemente devuelve el `bTracked` cacheado del último Tick **(B)** `MotionControllerComponent.h:39-43`.

🔴 **Hallazgo importante — "válido" ≠ "activamente trackeado":** el gate que usa UE (`ORIENTATION_VALID_BIT`/`POSITION_VALID_BIT`) es distinto del par `ORIENTATION_TRACKED_BIT`/`POSITION_TRACKED_BIT` que define la spec. Spec **(C)** `spaces.adoc`: *"indicates that the pose field's orientation field represents an **actively tracked** orientation"* (bit TRACKED) vs *"...contains valid data"* (bit VALID); y explícitamente: *"When a space location loses tracking, runtimes should continue to provide valid but untracked position values that are inferred or last-known, e.g. based on... inertial dead reckoning... so long as it's still meaningful for the application to use that position."* UE **solo** revisa los bits VALID, nunca los TRACKED (`OpenXRHMD.cpp:839-841`). Consecuencia para el detector: `IsTracked()`/`bValid` pueden seguir en `true` durante un micro-dropout de tracking mientras el runtime entrega una pose extrapolada/dead-reckoned — el booleano de validez del motor **no** garantiza que cada muestra sea una observación óptica real, sólo que el runtime tiene *algún* valor razonable que ofrecer.

---

## 2. Aim pose vs Grip pose

Definiciones oficiales Epic **(A)**, [OpenXR Input in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/openxr-input-in-unreal-engine):
- **Grip**: *"Represents the position and orientation of the user's closed hand in order to hold a virtual object."*
- **Aim**: *"Represents a ray from the user's hand or controller used to point at a target."*

Definición normativa + convención de ejes, spec **(C)** `semantic_paths.adoc`:
- **grip**: *"A pose that allows applications to reliably render a virtual object held in the user's hand, whether it is tracked directly or by a motion controller."* Ejes locales: *"+X axis: ... the ray that is normal to the user's palm"*; *"-Z axis: ... the ray that goes through the center of the tube formed by your non-thumb fingers"*; *"+Y axis: orthogonal to +Z and +X using the right-hand rule"*.
- **aim**: *"A pose that allows applications to point in the world using the input source... The ray that follows platform conventions for how the user targets objects in the world with the motion controller, with **+Y up, +X to the right, and -Z forward**."*

**Diferencia clave para nuestro caso:** el **aim** pose tiene una convención de ejes fija y "intuitiva" (arriba/derecha/adelante explícitos, igual que una cámara), mientras el **grip** pose está anclado anatómicamente a la mano (normal de la palma, tubo de los dedos) — su "forward"/"up" locales no son arriba/adelante del mundo, son relativos a cómo se sostendría el controller con la mano. Para un mando **apoyado plano sobre el abdomen** (nadie lo está empuñando), esa definición anatómica del grip pierde sentido físico pero el offset grip↔aim sigue siendo una rotación fija de fábrica por perfil de interacción — ambas poses rotan solidariamente con el chasis físico del controller. **Recomendación:** usar **Aim** por la convención de ejes explícita (+Y up / -Z forward), que hace más directa la lectura de `Up.Z` como inclinación; es también el default del nodo ya verificado en el proyecto (`ControllerPoseType` default = `Aim`, ver `nodes.md:60`). Si se prefiere Grip por estabilidad percibida, es la misma pose física rotada por un offset constante — el ruido/jitter no cambia entre una y otra, sólo el marco local.

Grip "surface" (`grip_surface`, promovido en OpenXR 1.1 core desde la extensión `XR_EXT_palm_pose`) también existe como Motion Source **(B)** `OpenXRInput.cpp:282-283,510-534`: `bGripSurfacePoseSupported = OpenXRHMD->IsOpenXRAPIVersionMet(EOpenXRAPIVersion::V_1_1)`, con fallback a `bPalmPoseSupported` (extensión `XR_EXT_palm_pose`) y luego a Grip normal si ninguna está. Definición **(D, no confirmada contra spec 1.1 directamente, solo referencia de terceros)**: orientado con -Z paralelo al índice extendido — más parecido a "la palma apoyada sobre algo" que Grip o Aim. Motion source Blueprint: `LeftPalm`/`RightPalm`.

---

## 3. Nodos concretos — firmas verificadas en código

### `UMotionControllerComponent` (`Engine\Source\Runtime\HeadMountedDisplay\Public\MotionControllerComponent.h`)
- `MotionSource` (`FName`, editable) — determina qué pose sigue: `Left`/`Right` (legacy = Grip), `LeftGrip`/`RightGrip`, `LeftAim`/`RightAim`, `LeftPalm`/`RightPalm`, `AnyHand`, `HMDSourceId`/`HeadSourceId`. Lista completa de motion sources soportados por OpenXR **(B)** `OpenXRInput.cpp:40-45,1473-1478`.
- `bool IsTracked() const` — BlueprintPure, `MotionControllerComponent.h:39-43`.
- `ETrackingStatus CurrentTrackingStatus` — BlueprintReadOnly, `:36`.
- `bool GetLinearVelocity(FVector& OutLinearVelocity) const` — **BlueprintPure**, `MotionControllerComponent.h:93-95`. Doc del propio header: *"the vector will be that velocity in cm/s in unreal world space and the function will return true. If velocity is unavailable it will return false."* Implementación **(B)** `MotionControllerComponent.cpp:492-499`: transforma `LinearVelocity` (cacheado en tracking space) por `TrackingToWorldTransform` y devuelve `bProvidedLinearVelocity`.
- `bool GetAngularVelocity(FRotator& OutAngularVelocity) const` — **BlueprintPure**, `:97-99`. Doc: *"OutAngularVelocity will be that velocity in deg/s in unreal world space... Note that it is not difficult to rotate a controller at more than 0.5 or 1 rotation per second briefly and some mathematical operations (such as conversion to quaternion) lose rotations beyond 180 degrees or 360 degrees."* Internamente se guarda como eje+magnitud (`AngularVelocityAsAxisAndLength`, en rad/s) precisamente para no perder revoluciones >180°/s al convertir a Rotator — implementación `:502-510`.
- `bool GetLinearAcceleration(FVector& OutLinearAcceleration) const` — **BlueprintPure**, `:101-103`. Existe la función pero en Quest 3/OpenXR siempre devuelve `false` (ver sección 1).
- ⚠ **Importante:** `GetLinearVelocity`/`GetAngularVelocity`/`GetLinearAcceleration` leen variables miembro cacheadas (`LinearVelocity`, `AngularVelocityAsAxisAndLength`, `LinearAcceleration`) que se actualizan una vez por `TickComponent` (`TG_PrePhysics`, `bCanEverTick=true`, `MotionControllerComponent.cpp:58-61,97-129`). **No** requieren estar dentro del evento `OnMotionControllerUpdated` — a diferencia de `GetParameterValue`/`GetHandJointPosition`, que sí necesitan `InUseMotionController` válido y solo son válidas durante ese evento (`:465-489`). Son seguras de leer en cualquier `EventTick` del actor dueño.
- 🔴 **No se late-updatean**: comentario explícito en el header, `MotionControllerComponent.h:118-120`: *"Note: these values are in tracking space... Also we do not late-update these values."* El late-update (`FLateUpdateManager`, controlado por `vr.EnableMotionControllerLateUpdate`, default 1) corrige la transform del componente justo antes de renderizar para reducir latencia visual, pero **no** toca las velocidades cacheadas ni la transform game-thread que lee Blueprint — por lo tanto pose y velocidad leídas desde Blueprint en el mismo Tick son consistentes entre sí (mismo poll), aunque el rendering pueda usar una posición ligeramente más reciente.

### `HeadMountedDisplayFunctionLibrary::GetMotionControllerState` (nodo Blueprint `Input|XRTracking|GetMotionControllerState`)
Firma **(B)** `Engine\Plugins\Runtime\XRBase\Source\XRBase\Public\HeadMountedDisplayFunctionLibrary.h:340-341`:
```cpp
static void GetMotionControllerState(UObject* WorldContext, const EXRSpaceType XRSpaceType, const EControllerHand Hand, const EXRControllerPoseType ControllerPoseType, FXRMotionControllerState& MotionControllerState);
```
`FXRMotionControllerState` **(B)** `Engine\Source\Runtime\HeadMountedDisplay\Public\HeadMountedDisplayTypes.h:361-398`: `bValid`, `DeviceName`, `ApplicationInstanceID`, `XRSpaceType`, `Hand`, `TrackingStatus`, `XRControllerPoseType`, `ControllerLocation`(Vector), `ControllerRotation`(**Quat**, no Rotator). **No incluye velocidad ni aceleración** — solo pose. `EXRControllerPoseType{Aim, Grip, Palm}` y `EXRSpaceType{UnrealWorldSpace, XRTrackingSpace}` — `:317-338`.

🔴 **Contradicción doc/código latente (mitigada en OpenXR):** la implementación base `FXRTrackingSystemBase::GetMotionControllerState` (usada por backends genéricos) tiene el comentario explícito *"NOTE: XRTrackingSystemBase ignores XRControllerPoseType, all the controller poses will be the same"* **(B)** `Engine\Plugins\Runtime\XRBase\Source\XRBase\Private\XRTrackingSystemBase.cpp:127-176`, línea 163. **Pero** `FOpenXRHMD::GetMotionControllerState` (usada en Quest 3) **sobreescribe** este comportamiento con soporte real de Aim/Grip/Palm vía `MotionController->GetControllerOrientationAndPosition(0, MotionSource, ...)` **(B)** `OpenXRHMD.cpp:282-390` — en el pipeline de este proyecto (NativeOpenXR) el pin `ControllerPoseType` sí funciona como se espera; el comentario de `XRTrackingSystemBase` solo aplicaría a un backend hipotético sin override propio.

### Velocidad/tracking a más bajo nivel (para entender el dato, no para usar directo en BP)
`FOpenXRInputPlugin::FOpenXRInput::GetControllerOrientationAndPositionForTime(...)` **(B)** `Engine\Plugins\Runtime\OpenXR\Source\OpenXRInput\Private\OpenXRInput.cpp:1348-1405` — resuelve el `MotionSource` a una `XrAction` de pose (`xrGetActionStatePose`) y delega en `OpenXRHMD->GetPoseForTime(...)`. `GetControllerTrackingStatus` — `:1407+` — usa el mismo camino de acción.

### Orientación → ejes (Forward/Right/Up)
- Sobre un `SceneComponent`: `Transformation|GetForwardVector`/`GetRightVector`/`GetUpVector` (in: `self`; out: Vector) — ya verificado en `nodes.md:68`.
- Sobre un Rotator/Quat suelto: `Math|Vector|Get*Vector` toman el Rotator directamente.
- El `Up.Z`/`Forward.Z`/`Right.Z` que ya usa el proyecto es literalmente el coseno del ángulo entre ese eje del controller y el eje mundial +Z (gravedad, ver sección 4) — es la proyección correcta para medir inclinación sin pasar por Euler (evita gimbal/wrap).

---

## 4. Marco de referencia y gravedad

**Posición**: depende del `TrackingOrigin`/`EXRSpaceType` — Stage vs Local cambia dónde está el (0,0,0), pero no la orientación.

**Orientación — sí está referenciada a la gravedad, independiente del tracking origin.** Spec **(C)** `spaces.adoc`, `XR_REFERENCE_SPACE_TYPE_LOCAL`: *"establishes a world-locked origin, **gravity-aligned to exclude pitch and roll**, with +Y up, +X to the right, and -Z forward."* `XR_REFERENCE_SPACE_TYPE_STAGE`: *"The origin is on the floor at the center of the rectangle, with +Y up..."* — ambos espacios de referencia estándar de OpenXR fijan su eje "up" (+Y en OpenXR, que UE mapea a +Z tras la conversión de coordenadas) alineado con la gravedad real, no con ningún eje arbitrario del hardware. Esto confirma lo que el proyecto ya asumía: **`Up.Z` (o el componente Z del eje que se use) es directamente la inclinación respecto de la gravedad**, y el tracking origin elegido (Stage/Local) no lo afecta — solo mueve el origen de posición.

---

## 5. Timing / frecuencia de actualización

- `UMotionControllerComponent` tickea todos los frames (`bCanEverTick=true`, `TG_PrePhysics`) **(B)** `MotionControllerComponent.cpp:58-61`. En Quest 3 eso es una vez por frame de aplicación (72/90/120 Hz según refresh rate configurado) — no hay un tickrate de controller independiente expuesto a Blueprint.
- **La pose que se lee en Tick ya viene predicha, no es la muestra IMU cruda "de ahora".** Cuando se pide con `Time=0` (caso normal de polling en Tick), UE resuelve el tiempo objetivo así **(B)** `OpenXRHMD.cpp:809-822` → `TargetTime = GetDisplayTime()`, y:
  ```cpp
  XrTime FOpenXRHMD::GetDisplayTime() const {
      ...
      return PipelineState.bXrFrameStateUpdated ? PipelineState.FrameState.predictedDisplayTime : 0;
  }
  ```
  `OpenXRHMD.cpp:2599-2604`. `predictedDisplayTime` es el campo que devuelve `xrWaitFrame` — el runtime **extrapola** la pose hasta el instante en que el frame efectivamente se va a mostrar (motion-to-photon). Guía Khronos (no normativa, pero mantenida por el mismo grupo) **(C)**: *"predictedDisplayTime returned by xrWaitFrame is the time the frame is predicted it will be displayed"*, *"sometimes called photon time or mid-photon time"*; y el motivo: *"ensures the runtime is providing the right amount of extrapolation into the future to best predict the pose that the space will be in at the time it is shown."*
- Consecuencia directa: la velocidad que entrega `XR_SPACE_VELOCITY` (y por tanto `GetLinearVelocity`/`GetAngularVelocity`) **también** está evaluada en ese mismo instante predicho, no medida instantáneamente — es la derivada que el runtime reporta para ese `XrTime`, generada por su propio filtro/fusión interna (no documentado por Meta qué tan agresiva es esa predicción).
- **Late-update adicional**: `FLateUpdateManager` (controlado por `vr.EnableMotionControllerLateUpdate`, default 1) vuelve a pollear la pose en el render thread justo antes de renderizar, para acortar aún más la ventana de latencia visual — pero, como ya se dijo, esto **no** afecta lo que Blueprint puede leer en Tick (transform game-thread + velocidades cacheadas quedan fijas desde el poll de ese Tick).
- Leer en Tick es confiable en el sentido de "una muestra fresca por frame, consistente entre pose y velocidad"; no es confiable como "muestra IMU cruda sin filtrar" — ya viene pasada por la fusión sensorial + predicción del runtime de Meta antes de llegar a UE.

---

## 6. Ruido y estabilidad — 🔴 mayormente folclore

No se encontró ninguna cifra oficial (Meta o Khronos) de piso de ruido/jitter angular para un Touch controller quieto. Lo que hay:
- **(D)** Foro Meta: usuario reportando ~70 Hz de muestreo logrado consultando IMU cruda vía `hello_xr` — anécdota, no spec.
- **(D)** Prensa (uploadvr.com, análisis de firmware filtrado): Touch Plus/Touch Pro usarían un IMU TDK serie ICM-426xx, descrito como "premium performance", con reducción de ruido de accel/gyro respecto al modelo anterior — sin cifras concretas, sin confirmación oficial de Meta.
- **(D)** Foro/community: valor suelto de "50 Hz" para el IMU del Touch v2 (generación anterior a Quest 3) — sin fuente primaria verificada.
- No hay declaración pública de Meta sobre el ruido angular en reposo de Touch (Quest 3). **Conclusión accionable:** no hay piso de ruido de catálogo con el que dimensionar analíticamente el filtro — la calibración empírica (medir en el propio Quest 3, como ya se documentó en `motion-detection-thresholds.md`) sigue siendo la única fuente confiable.

---

## 7. Haptics

Confirmado en código, coincide con lo ya sabido: `APlayerController::SetHapticsByValue(Frequency, Amplitude, Hand)` **(B)** `Engine\Source\Runtime\Engine\Private\PlayerController.cpp:4522-4565` construye un `FHapticFeedbackValues(Frequency, Amplitude)` cuyo constructor clampea ambos a `[0,1]` **(B)** `Engine\Source\Runtime\ApplicationCore\Public\GenericPlatform\IInputInterface.h:84-90`:
```cpp
Frequency = (InFrequency < 0.f) ? 0.f : ((InFrequency > 1.f) ? 1.f : InFrequency);
Amplitude = (InAmplitude < 0.f) ? 0.f : ((InAmplitude > 1.f) ? 1.f : InAmplitude);
```
Nota adicional no mencionada antes: el parámetro llamado "Frequency" en esta API no es una frecuencia física en Hz sino un valor normalizado `[0,1]` que cada plataforma mapea internamente a su propio rango de Hz soportado — el clamp `[0,1]` no es un límite de "1 Hz", es un límite de rango normalizado. `HapticFeedbackEffect_Curve` (asset, no esta función) sí puede especificar una curva de frecuencia con su propio rango, evitando esta normalización — coincide con lo que ya se sabía.

---

## Resumen accionable para el detector

1. **Usar `GetLinearVelocity`/`GetAngularVelocity` de `MotionControllerComponent` en `EventTick`** — no hace falta estar dentro de `OnMotionControllerUpdated`; son BlueprintPure y leen el último poll cacheado.
2. **Orientación vía `Aim` pose** (`Input|XRTracking|GetMotionControllerState`, `ControllerPoseType=Aim`, o `MotionSource="RightAim"`/`"LeftAim"` en el componente) — convención de ejes explícita (+Y up, -Z forward) más predecible que Grip para extraer inclinación.
3. **`Up.Z` como inclinación respecto de gravedad está justificado**: los reference spaces de OpenXR (Local/Stage) son gravity-aligned por spec — no depende del tracking origin elegido.
4. **No hay aceleración lineal/angular disponible** (confirmado: falta `XR_EPIC_space_acceleration` en el runtime de Meta) — el pipeline de detección debe trabajar solo con pose + velocidad.
5. **La pose/velocidad ya vienen predichas** (`predictedDisplayTime`), no son muestras crudas — cualquier textura de "ruido" que se mida incluye el comportamiento del predictor de Meta, no solo el IMU físico.
6. 🔴 **`bTracked`/`bValid` no distinguen "tracking activo" de "última posición conocida"** — un dropout corto puede pasar desapercibido como `Tracked=true` con datos extrapolados. Si el detector necesita distinguir esto con precisión, no hay forma de hacerlo desde Blueprint estándar (UE no expone los bits TRACKED, solo VALID) — sería necesario un plugin nativo que llame `xrLocateSpace` directamente y lea `XR_SPACE_LOCATION_ORIENTATION_TRACKED_BIT`.
