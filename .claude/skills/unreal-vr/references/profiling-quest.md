# Profiling y optimización de performance — Quest 3 STANDALONE (UE 5.8)

> **Target: Meta Quest 3 standalone (APK Android), renderer MÓVIL.** Obra sentada, 15 min, single-user, estética Turrell. Presupuesto: **72 fps = 13.9 ms**. Sospecha de partida: **fill-rate bound, no geometry bound** — este documento existe para poder *demostrarlo*, no asumirlo.
> **Regla de fuentes:** tres niveles. **[DOC]** documentación oficial de Epic o Meta, con URL + cita textual · **[SRC]** código de UE 5.8 en `C:\Program Files\Epic Games\UE_5.8` (archivo:línea) · **[FOLCLORE]** creencia sin fuente oficial, aunque sea de sentido común. Investigado 17/07/2026.

---

# 🔴 PROCEDIMIENTO PASO A PASO

## 0. Empaquetar en **Development**, no Shipping
🔴 Bloqueante para casi todo lo demás. [DOC] RenderDoc Meta Fork: *"apps used with this tool must be development builds"* — [RenderDoc Meta Fork](https://developers.meta.com/horizon/documentation/unreal/ts-renderdoc-for-oculus/). Unreal Insights también asume tracing activo, que **[DOC]** está *"on by default"* en un build de desarrollo — [Unreal Insights en Quest](https://developers.meta.com/horizon/documentation/unreal/ts-unreal-insights-ue5/). **Empaquetar Development durante todo el ciclo de optimización; recién pasar a Shipping para la build de tienda final.**

## 1. Primera pasada, sin cables: **OVR Metrics Tool**
Instalar desde la Meta Store en el propio casco (o `adb shell am start omms://app`), activar el overlay HUD mientras jugás la obra puesta. Te da de entrada: fps, **GPU time**, **CPU utilization por core**, GPU/CPU throttle level, temperatura, stale/tearing frames, foveation level — [OVR Metrics Tool Stats Guide](https://developers.meta.com/horizon/documentation/native/android/ts-ovrstats/). **Es el veredicto de "¿estamos cerca de 13.9 ms o no?" en 5 minutos, sin USB.**

## 2. Aislar CPU-bound vs GPU-bound (método OFICIAL de Meta)
> [DOC] *"One way to determine if an app is CPU or GPU bound is to simply render nothing at all. This can be done by turning off the render camera and letting the app continue to run."* · *"If the app's performance is not affected or affected very little when not rendering anything, the app is likely CPU bound. If performance improves significantly, the app is likely GPU bound."*
> — [Meta: Performance Optimization for Mobile (Unreal)](https://developers.meta.com/horizon/documentation/unreal/po-perf-opt-mobile/)

**Hazlo así:** un actor/nivel de prueba con la cámara de renderizado apagada (o `r.SceneCaptureSourceOverride`-style toggle / mover la cámara fuera del mundo). Medí fps con OVR Metrics antes y después. Si casi no cambia → CPU-bound (poco probable en esta obra: casi sin lógica, sin IA, sin física). Si mejora fuerte → GPU-bound.

## 3. Si es GPU-bound, aislar fill-rate vs vertex (el número que buscás)
> [DOC] *"This can be done by setting the app's render scale to something small, like 0.01."* · *"If performance is not affected, the app is likely vertex-bound. If performance improves, the app is likely fragment-bound."*
> — misma fuente que arriba.

**Hazlo así:** con la cámara prendida, bajá `xr.SecondaryScreenPercentage.HMDRenderTarget` (UE 5.5+) a un valor mínimo (ej. 10) o el pixel density del plugin a 0.01 y volvé a medir. Si fps sube fuerte → **confirmado fill-rate/fragment-bound**, que es la hipótesis de partida de este proyecto. Si no cambia → el cuello está en geometría (vértices) o en CPU de render (draw calls), no en overdraw.

## 4. Detalle por draw call / tile: **RenderDoc Meta Fork**
Development build + [instalador Windows/Mac](https://developers.meta.com/horizon/downloads/package/renderdoc-oculus/) (desinstalar primero cualquier RenderDoc-for-Oculus viejo). Capturá un frame → **Tile Timeline** (la GPU de Quest 3 es tile-based; ahí ves bins/etapas reales) + **hasta 48 métricas por draw call** + shader stats vía `KHR_pipeline_executable_properties` (Vulkan). — [DOC fuente arriba]. **Es la única herramienta oficial que te da overdraw/fill real por primitiva** (ver §2 más abajo: no existe view mode de overdraw en el dispositivo).

## 5. Detalle por frame/hilo: **Unreal Insights sobre Android**
```
adb reverse tcp:1980 tcp:1980
```
Crear `UECommandLine.txt` en el device con la línea de trace, ej.:
```
../../../<ProjectName>/<ProjectName>.uproject -tracehost=127.0.0.1 -trace=Bookmark,Frame,CPU,GPU,LoadTime,File -statnamedevents
```
Pushearlo con **UAFT** (Unreal Android File Tool) al directorio del build, lanzar la app, abrir `Engine/Binaries/.../UnrealInsights.exe` y conectar a la sesión **LIVE**. — [Meta: Unreal Insights en Quest para UE5](https://developers.meta.com/horizon/documentation/unreal/ts-unreal-insights-ue5/) + [Epic: How to Use Unreal Insights to Profile Android Games](https://dev.epicgames.com/documentation/unreal-engine/how-to-use-unreal-insights-to-profile-android-games-for-unreal-engine?lang=en-US). Da tracks separados de CPU (por hilo) y GPU con ancho = tiempo — la mejor fuente para saber **qué pase de render específico** se come el frame.

## 6. Comandos `stat`/cvars en vivo sobre el APK: adb broadcast
```
adb shell "am broadcast -a android.intent.action.RUN -e cmd 'stat unit'"
```
🔴 [SRC] Comentario **textual** en el código de UE 5.8, `Engine\Build\Android\Java\src\com\epicgames\unreal\ConsoleCmdReceiver.java:43`:
```java
// example usage
// adb shell "am broadcast -a android.intent.action.RUN -e cmd 'stat fps'"
```
Confirmado: el mecanismo sigue vivo en 5.8. Sirve para `stat unit`, `stat rhi`, `stat gpu`, cualquier cvar. Ver §3 para el detalle de qué requiere de build.

## 7. Antes de tocar Dynamic Resolution: **Foveated Rendering**
> [DOC] *"Dynamic foveation is a better option than using a static FFR level, and this should be used instead of Unreal Engine's Dynamic Resolution feature."*
> — [Meta: Fixed Foveated Rendering (FFR)](https://developers.meta.com/horizon/documentation/unreal/os-fixed-foveated-rendering/)

Setealo con el Blueprint node **Set Foveated Rendering Level** (`isDynamic=true`, nivel Off/Low/Medium/High/HighTop) **antes** de meterte con `r.Oculus.DynamicResolution.*`. Ver §4.

## 8. Verificar contra el requisito real de tienda antes de dar por óptimo
No es "72 fps mínimo". Es **60 fps de rendering rate** + **72 Hz de refresh** como piso de Hz soportado, y **85% de render scale** la mayoría del tiempo. Ver §5 — folclore vivo hasta en documentación oficial de Epic/Meta.

---

# 1. Flujo oficial de profiling — comparación

| Herramienta | ¿Funciona en 5.8? | Conexión | Qué mide QUE OTRAS NO | Costo de setup |
|---|---|---|---|---|
| **OVR Metrics Tool** | Sí, agnóstica de motor (corre en el sistema, no instrumenta el engine) | Store del casco / `adb shell am start omms://app` | Throttle level de CPU/GPU, **stale frames**, tearing, foveation level activo, batería/temperatura — datos de **sistema**, no de engine | 🟢 mínimo — sin cables si usas el HUD puesto |
| **Meta Quest Developer Hub → Performance Analyzer** | Sí — [DOC] confirma soporte explícito: *"Commercial game engines such as Unity and Unreal Engine only emit ATrace instrumentation"* y pide el package name en **ATrace Apps** — [Performance Analyzer and Metrics](https://developers.meta.com/horizon/documentation/unity/ts-mqdh-logs-metrics/) | USB + MQDH desktop app | Traza **Perfetto** completa: CPU freq por core, GPU bandwidth de lectura/escritura, logcat sincronizado con los gráficos | 🟡 medio — instalar MQDH, cablear |
| **Unreal Insights sobre Android** | Sí — guía dedicada [Meta](https://developers.meta.com/horizon/documentation/unreal/ts-unreal-insights-ue5/) y [Epic](https://dev.epicgames.com/documentation/unreal-engine/how-to-use-unreal-insights-to-profile-android-games-for-unreal-engine?lang=en-US) para UE5 | `adb reverse` + UECommandLine.txt vía UAFT + `UnrealInsights.exe` | **Timeline por hilo** dentro del engine: qué función/pase específico ocupa cada ms — nadie más te da esto | 🔴 alto — push de archivo, host de trace, sesión live |
| **RenderDoc Meta Fork** | Sí, específico Quest — [Meta doc](https://developers.meta.com/horizon/documentation/unreal/ts-renderdoc-for-oculus/) | Instalador desktop + captura de frame (USB/wifi) | **Tile Timeline** (arquitectura tile-based real) + 48 métricas por draw call + shader stats Vulkan — el único con **overdraw real por primitiva** | 🟡 medio — requiere Development build |
| **`stat` vía adb broadcast** | Sí — [SRC] `ConsoleCmdReceiver.java:43` | `adb shell am broadcast ...` | Nada nuevo que no den los otros, pero es **gratis** y no requiere instalar nada adicional | 🟢 mínimo |

## Veredicto: por dónde empezar
**OVR Metrics Tool primero** (paso 1) — responde "¿estamos en presupuesto?" en minutos y sin tocar cables. Si la respuesta es "no", usar el **test oficial de Meta de cámara apagada + render scale 0.01** (pasos 2-3) para clavar si es CPU/GPU/fill-rate **con un experimento, no una corazonada**. Solo bajar a **RenderDoc Meta Fork** cuando ya sabes que es fill-rate y necesitas saber *qué draw call específico* sangra. **Unreal Insights** es el complemento para el lado CPU/game-thread y para correlacionar con el timeline de Blueprints — más setup, úsalo cuando el problema no es obviamente GPU.

---

# 2. CPU-bound vs GPU-bound vs fill-rate-bound

## El test oficial (repetido de arriba, es el corazón de la pregunta)
[DOC Meta, misma fuente]: cámara apagada → CPU vs GPU. Render scale 0.01 → vertex vs fragment/fill. **No hay ambigüedad de fuente: es Meta describiendo exactamente cómo aislar fill-rate.**

## ⚠️ La heurística de `stat unit` (Game/Draw/GPU) es folclore, no doc de Epic
Es la explicación que vas a encontrar en *todos lados* ("si Frame≈Game, CPU-bound; si Frame≈GPU, GPU-bound") — **verificado que NO está en la documentación oficial de Epic**. Se buscó explícitamente en [Timing Insights in Unreal Engine 5](https://dev.epicgames.com/documentation/unreal-engine/timing-insights-in-unreal-engine-5?lang=en-US) y en [Introduction to Performance Profiling](https://dev.epicgames.com/documentation/unreal-engine/introduction-to-performance-profiling-and-configuration-in-unreal-engine): ninguna trae esa explicación en prosa. Es correcta (es como funciona el pipeline), pero **[FOLCLORE]** en términos de esta regla de fuentes — la fuente real de "cómo aislar" es el test de Meta de arriba, no `stat unit`.
Lo que **sí** dice Epic de forma oficial sobre `stat`: *"Stats refers to a series of console commands you can use within a running UE application to output statistics to the screen"*, cubriendo "Memory tracking, GPU and CPU load, Gameplay ticks, UI, Animations" — [Introduction to Performance Profiling](https://dev.epicgames.com/documentation/unreal-engine/introduction-to-performance-profiling-and-configuration-in-unreal-engine). Sin desglose de qué threshold indica qué.

## 🔴 No existe view mode oficial de overdraw EN EL DISPOSITIVO
Quad Overdraw / Shader Complexity son view modes gateados a **SM5** [SRC `DebugViewModeRendering.cpp:254`: `IsFeatureLevelSupported(Parameters.Platform, ERHIFeatureLevel::SM5)`]. Quest corre `VULKAN_ES3_1_ANDROID` — no alcanza SM5, por lo tanto **el view mode de overdraw del editor no aplica en Quest** (confirmado también por reportes de la comunidad — foros de Epic, sin doc oficial que lo contradiga). La única fuente oficial de overdraw real por-draw-call en el dispositivo es **RenderDoc Meta Fork** (§1). El editor con Preview Rendering Level → Android Vulkan (ver `materials-vr.md`) tampoco resucita este view mode: es un feature-level gate, no un tema de preview.

## Qué número mirar en OVR Metrics para GPU timing
[DOC] Lista de métricas expuestas: *"frame rate, heat, GPU and CPU throttling, and the number of screen tears and stale frames per second"*, más **GPU time**, **CPU utilization per core**, **foveation level** — [Monitor Performance with OVR Metrics Tool](https://developers.meta.com/horizon/documentation/native/android/ts-ovrmetricstool/) / [Stats Definition Guide](https://developers.meta.com/horizon/documentation/native/android/ts-ovrstats/). **GPU time** directo es el número — no hace falta inferirlo de `stat unit`.

---

# 3. Consola y `stat` en un APK empaquetado

## 🔴 El gesto de "4 dedos" NO sirve en el headset — es para tablets/teléfonos
> [SRC] `Engine\Source\Runtime\Launch\Private\Android\LaunchAndroid.cpp:1354-1358`:
> ```cpp
> #if !UE_BUILD_SHIPPING
> if ((pointerCount >= 4) && (type == TouchBegan))
> {
>     bool bShowConsole = true;
>     GConfig->GetBool(TEXT("/Script/Engine.InputSettings"), TEXT("bShowConsoleOnFourFingerTap"), bShowConsole, GInputIni);
>     ...
> ```
Este gesto depende de **eventos de pantalla táctil** (`AMotionEvent`) — es el mecanismo genérico de "Android Development Basics" pensado para teléfonos/tablets Android. **El Quest 3 no tiene pantalla táctil expuesta al usuario dentro del casco**: no hay superficie para dar el toque de 4 dedos mientras estás jugando la obra puesta. **Es folclore transplantado de Android mobile en general, inaplicable a un headset standalone.** También está compilado fuera (`#if !UE_BUILD_SHIPPING`) — doble motivo por el que no sirve para verificar nada en la build de tienda.

## ✅ El mecanismo real: adb broadcast intent
[SRC confirmado arriba, `ConsoleCmdReceiver.java`] — es la vía documentada también por Meta en un blog de desarrollo (no doc formal, marcar como **B/blog oficial de Meta, no doc de referencia**): *"adb shell "am broadcast -a android.intent.action.RUN -e cmd 'CONSOLE COMMAND GOES HERE'""* — [Meta: Logging and Console Commands for Mobile VR](https://developers.meta.com/horizon/blog/developer-perspective-ue4-logging-and-console-commands-for-mobile-vr/) (es blog UE4, pero **el código fuente de 5.8 confirma que el receiver sigue existiendo tal cual**).

## ⚠️ Matiz fino leído directo del código: qué está gateado por Shipping y qué no
[SRC] `LaunchAndroid.cpp:2038-2062`, función `nativeConsoleCommand` (la que ejecuta el intent broadcast):
```cpp
void JNICALL UE::Jni::FGameActivity::nativeConsoleCommand(...)
{
#if !UE_BUILD_SHIPPING
    GDebugConsoleOpen = false;   // <- SOLO esto está gateado
#endif
    FString Command = FJavaHelper::FStringFromParam(jenv, commandString);
#if !USE_ANDROID_STANDALONE
    ...
    GEngine->DeferredCommands.Add(Command);   // <- el DESPACHO del comando NO está en el #if
    ...
#else
    IssueConsoleCommand(Command);
#endif
}
```
Lo único gateado por `UE_BUILD_SHIPPING` es la bandera visual del popup de consola en pantalla (`GDebugConsoleOpen`, que de todas formas es irrelevante en VR — no hay pantalla táctil para verla). **El despacho real del comando (`DeferredCommands.Add` / `IssueConsoleCommand`) no está protegido por ese `#if` en este archivo.** No es una garantía de que *cualquier* cvar se ejecute en Shipping (`FConsoleManager` y cvars individuales pueden tener sus propios gates — no verificado exhaustivamente acá), pero **la vía de entrada del comando por broadcast intent en sí misma no depende de estar en Development.** Aun así: **recomendación operativa es Development durante todo el ciclo de optimización** — es lo único que garantiza también RenderDoc e Insights, así que no hay motivo práctico para arriesgarse en Shipping.

## UECommandLine.txt: pasar comandos AL LANZAR (no en vivo)
Mismo mecanismo que usa Insights (§1 paso 5): agregar `-ExecCmds="stat unit, stat gpu"` a la línea del `UECommandLine.txt` pusheado por UAFT, para que el comando corra desde el arranque sin depender del broadcast en vivo.

---

# 4. Resolución dinámica y Foveated Rendering

## Fixed / Dynamic Foveated Rendering — la palanca recomendada primero
> [DOC] *"enables the edges of an application-generated frame to be rendered at a lower resolution than the center portion of the frame"* · *"can improve framerate in applications with GPU fill bottlenecks, reduce power consumption and heat"*
> — [Meta: Fixed Foveated Rendering (FFR)](https://developers.meta.com/horizon/documentation/unreal/os-fixed-foveated-rendering/)

Niveles vía Blueprint **Set/Get Foveated Rendering Level** — `EOculusXRFoveatedRenderingLevel`: **Off (0, default)**, Low (1), Medium (2), High (3), HighTop (4) — [Set Foveated Rendering Level](https://developers.meta.com/horizon/documentation/unreal/unreal-blueprints-get-foveated-rendering-level/). Benchmark propio de Meta en apps ALU-bound: *"a 6.5% performance improvement from the low setting, 11.5% improvement from medium setting, and a 21% improvement from the high setting"* — y para apps pixel-intensivas, *"FFR can result in a 25% gain in performance"*. Contra-caso honesto: *"applications with very simple shaders, which are not bound on GPU fill, will likely not see a significant improvement from FFR"*.

> [DOC] **Dynamic FFR > Dynamic Resolution nativo de UE:** *"In most cases, dynamic foveation is a better option than using a static FFR level, and this should be used instead of Unreal Engine's Dynamic Resolution feature."* — [Adaptive Pixel Density](https://developers.meta.com/horizon/documentation/unreal/unreal-adaptive-viewport/) / [FFR doc arriba].

**Para un proyecto fill-rate bound como este: sí, FFR (dinámico) es la primera palanca**, antes que tocar `r.Oculus.DynamicResolution.*`. Es exactamente el escenario para el que Meta la diseñó ("GPU fill bottlenecks").

## Cvars de Dynamic Resolution / pixel density
| Cvar | Qué hace | Default |
|---|---|---|
| `r.Oculus.DynamicResolution.PixelDensity` | Fuerza una densidad manual (0 = deja control al runtime) | 0 |
| `r.Oculus.DynamicResolution.PixelDensityMin` / `...Max` | Rango del dynamic resolution | [DOC] *"never go below 0.8x default eyebuffer size, or above 1.2x"* |
| `vr.PixelDensity` | Control de render scale — **UE < 5.5** | — |
| `xr.SecondaryScreenPercentage.HMDRenderTarget` | Reemplaza a `vr.PixelDensity` — **UE 5.5 y superior** (estamos en 5.8 → **este es el que corresponde**) | — |
> [DOC] *"For Unreal Engine below 5.5, use the vr.PixelDensity console variable; for Unreal Engine 5.5 and up, use the xr.SecondaryScreenPercentage.HMDRenderTarget console variable instead."* — [Meta: Render Scale](https://developers.meta.com/horizon/documentation/unreal/os-render-scale/) / [Dynamic Resolution](https://developers.meta.com/horizon/documentation/unreal/dynamic-resolution-unreal/)
> [DOC] Compatibilidad: *"If dynamic foveation is also enabled, the runtime may increase the foveated rendering level to reclaim GPU headroom before scaling the resolution down"* — pueden convivir, FFR actúa primero.

---

# 5. Qué exige REALMENTE la tienda — VRC.Quest.Performance

## 🔴 El propio doc de Meta para Unreal dice "72 FPS mínimo" — y es una simplificación que confunde fps con Hz
> [DOC, textual] *"All Meta Quest apps require a minimum of 72 FPS to satisfy Virtual Reality Check (VRC) requirements."*
> — [Meta: Performance Optimization for Mobile (Unreal)](https://developers.meta.com/horizon/documentation/unreal/po-perf-opt-mobile/)

Comparado con el texto **literal del requisito mismo**:
> [DOC, textual] **VRC.Quest.Performance.1** — *"Apps must maintain a rendering rate of at least 60 fps"* · interactivas: *"must use a refresh rate of 72 Hz, 80 Hz, 90 Hz, 96 Hz, 100 Hz or 120 Hz"* · con Application SpaceWarp: *"may use a rendering rate (fps) of half the refresh rate (such as 30 fps for 60 Hz, 36 fps for 72 Hz)"* · testeo: *"The application should not experience extended periods of rendering rate below 60 fps, or when using Application SpaceWarp, 30 fps"*, medido con OVR Metrics Tool.
> — [VRC.Quest.Performance.1](https://developers.meta.com/horizon/resources/vrc-quest-performance-1/)

**Son dos números distintos, y el propio doc de Unreal de Meta los mezcla en una sola cifra.** El piso real de **rendering rate** (fps de la app) es **60**. El piso de **refresh rate** (Hz de la pantalla) es **72**. **No hace falta perseguir "72 fps"** — con 60 fps sostenidos a un refresh de 72 Hz el requisito se cumple (aunque implica reproyección/duplicado de frames en el compositor, ver §6).

## Otros VRC de performance relevantes
- **VRC.Quest.Performance.3** — *"The app must either display head-tracked graphics in the headset within 4 seconds of launch or provide a loading indicator in VR."*
- **VRC.Quest.Performance.4** — render scaling: *"should run at no less than 85% render scaling for the majority of the experience"* — presupuesto extra a respetar si FFR/dynamic res están activos.

---

# 6. `t.MaxFPS`, frame pacing, y qué pasa cuando se pierde un frame

## `t.MaxFPS` — confirmado en fuente
> [SRC] `Engine\Source\Runtime\Engine\Private\UnrealEngine.cpp:12136-12138`:
> ```cpp
> static TAutoConsoleVariable<float> CVarMaxFPS(
>     TEXT("t.MaxFPS"),0.f,
>     TEXT("Caps FPS to the given value.  Set to <= 0 to be uncapped."));
> ```
Sin fuente oficial de Epic/Meta que recomiende un valor específico para Quest — en VR normalmente se deja sin capear y el compositor de OpenXR/VrApi es quien impone el ritmo real vía vsync al refresh del casco; capear con `t.MaxFPS` por debajo del refresh es contraproducente salvo debugging puntual. **[FOLCLORE]** cualquier valor numérico recomendado acá.

## No hay "ASW" en Quest standalone salvo que lo actives explícitamente — y el fallback automático es reproyección de rotación solamente
- **Asynchronous TimeWarp (rotación)** está *"enabled in every Quest application"* [DOC/blog Meta sobre TimeWarp histórico] — es el piso automático, siempre activo, sin que el desarrollador haga nada.
- **Positional TimeWarp** (corrección también de traslación, no solo rotación) depende de que la app envíe **depth buffer**; TimeWarp *"did not know how far away pixels were"* hasta que se sometieron depth buffers — [Meta: Introducing Application SpaceWarp](https://developers.meta.com/horizon/blog/introducing-application-spacewarp/).
- **System Positional TimeWarp (SysPTW)** — llegó como **feature experimental** en Horizon OS v83: *"uses real-time scene depth to reduce visual judder and lag when apps drop frames"*, *"automatically activates when needed and works across all apps, with no impact on regular performance"*. **Es automático a nivel sistema, no requiere trabajo del desarrollador — pero es experimental, no garantizado en toda versión de Horizon OS.**

## Application SpaceWarp / Frame Synthesis — SÍ está nativo en el motor 5.8, no hace falta fork
🔴 Hallazgo directo de fuente, contradice cualquier folclore de "hace falta el fork de Meta para esto":
> [SRC] `Engine\Plugins\Runtime\OpenXR\Source\OpenXRHMD\Private\OpenXRHMD.cpp:175-181`:
> ```cpp
> static TAutoConsoleVariable<bool> CVarOpenXRFrameSynthesis(
>     TEXT("xr.OpenXRFrameSynthesis"),
>     0,
>     TEXT("If true and supported via XR_EXT_frame_synthesis or XR_FB_space_warp, write to and submit motion vector ")
>     TEXT("and motion vector depth swapchains for frame synthesis.\n")
>     TEXT("Currently only supported when using the Vulkan mobile renderer, using mobile multi-view, ")
>     TEXT("and r.Velocity.DirectlyRenderOpenXRMotionVectors=True.\n")
>     TEXT("Because normal velocity rendering is disabled when r.Velocity.DirectlyRenderOpenXRMotionVectors=True, ")
>     TEXT("temporal anti-aliasing and motion blur will be automatically disabled."),
>     ECVF_RenderThreadSafe);
> ```
> `Engine\Plugins\Runtime\OpenXR\Source\OpenXRHMD\Private\OpenXRHMDModule.cpp:44-48`:
> ```cpp
> static TAutoConsoleVariable<bool> CVarPreferFBSpaceWarp(
>     TEXT("xr.PreferFBSpaceWarp"), false,
>     TEXT("If true, OpenXR will use XR_FB_space_warp rather than XR_EXT_frame_synthesis ")
>     TEXT("to provide frame synthesis when both extensions are available."),
>     ECVF_ReadOnly);
> ```
**Default: `false`/`0` — apagado.** Requiere Vulkan móvil + Multi-View + `r.Velocity.DirectlyRenderOpenXRMotionVectors=True`, y **apaga automáticamente TAA y motion blur** (efecto colateral leído directo del comentario del cvar). El plugin OpenXR vanilla de UE 5.8 soporta **tanto** la extensión cross-vendor `XR_EXT_frame_synthesis` como la de Meta `XR_FB_space_warp`; `xr.PreferFBSpaceWarp` decide cuál usar si ambas están disponibles. Confirmado también por [Meta: Application SpaceWarp Developer Guide (Unreal)](https://developers.meta.com/horizon/documentation/unreal/unreal-asw/): *"For UE 5.7 and later"* usar `xr.OpenXRFrameSynthesis=True` en vez del cvar viejo `r.Mobile.Oculus.SpaceWarp.Enable` (deprecado, ese sí ligado al fork y no presente en este install vanilla).

## El modo de falla real que vería el usuario
**Sin AppSW activado** (nuestro caso probable — agrega motion vectors, apaga TAA/motion blur, complejidad no trivial para un piso Ganzfeld translúcido): si se pierde un frame, el compositor reproyecta el último frame renderizado con **ATW rotacional** (siempre activo) y, si hay SysPTW disponible y activo, corrección posicional por profundidad de escena. **Lo que ve el usuario: judder/deslizamiento de paralaje en la traslación de cabeza durante ese frame, NO pantalla negra ni un frame congelado sin reproyectar** — la rotación se sigue corrigiendo siempre. Para una obra sentada con movimiento de cabeza principalmente rotacional (mirar alrededor desde una posición fija), el ATW base ya cubre gran parte del caso de uso — el riesgo real de "romper la ilusión" es más bajo que en una obra con locomoción activa.

**Recomendación para este proyecto:** no invertir en AppSW (costo de implementación + artefactos de motion vectors sobre contenido translúcido/aditivo Turrell) — en su lugar, **proteger el presupuesto de 13.9 ms con margen** (apuntar a dejar headroom, no a los 13.9 ms exactos) para que la reproyección automática rara vez tenga que entrar en juego.

---

# ❌ FOLCLORE — tabla

| Creencia | Realidad | Fuente |
|---|---|---|
| "Quest exige 72 fps mínimo" | El requisito de **rendering rate** es **60 fps**; 72 Hz es el piso de **refresh rate**, un número distinto | [VRC.Quest.Performance.1](https://developers.meta.com/horizon/resources/vrc-quest-performance-1/) — y el propio doc de Meta para Unreal lo mezcla mal |
| "4 dedos en pantalla abre la consola en el Quest" | Ese gesto depende de touch events de Android; **el Quest no tiene pantalla táctil expuesta durante el uso** — inaplicable en headset | [SRC] `LaunchAndroid.cpp:1354-1358` |
| "`stat unit` (Game/Draw/GPU) es el método oficial para diagnosticar CPU/GPU-bound" | Es folclore extendido y **correcto en la práctica**, pero **no está en la doc de Epic** en esos términos. El método que SÍ es oficial (Meta) es apagar cámara + bajar render scale a 0.01 | Búsqueda directa en [Timing Insights](https://dev.epicgames.com/documentation/unreal-engine/timing-insights-in-unreal-engine-5?lang=en-US) — no está |
| "Se puede ver overdraw con un view mode en el Quest, como en el editor" | Quad Overdraw/Shader Complexity están gateados a **SM5**; Quest corre ES3.1/Vulkan móvil, no llega. Usar RenderDoc Meta Fork | [SRC] `DebugViewModeRendering.cpp:254` |
| "Hace falta el fork de Meta de UE para tener Application SpaceWarp" | Falso para 5.7+: `xr.OpenXRFrameSynthesis` está **nativo** en el plugin OpenXR vanilla | [SRC] `OpenXRHMD.cpp:175-181` |
| "Hay que estar en Shipping para que la consola por adb funcione" | Al revés: el despacho del comando (`DeferredCommands.Add`) no está gateado por `UE_BUILD_SHIPPING` en el código revisado — pero Development es la recomendación operativa igual, por RenderDoc/Insights | [SRC] `LaunchAndroid.cpp:2038-2062` |
| "OVR Metrics Tool es solo para Unity" | La documentación indexada es Unity-céntrica, pero la app en sí corre a nivel Android/sistema — no instrumenta el motor. Meta Quest Developer Hub sí confirma soporte explícito de Unreal vía ATrace | [MQDH Performance Analyzer](https://developers.meta.com/horizon/documentation/unity/ts-mqdh-logs-metrics/) |

---

# 🔴 Donde Epic/Meta están en silencio (o se contradicen)
1. **El propio ecosistema Epic/Meta mezcla fps y Hz** en la página de optimización mobile para Unreal — ver §5. Confiar en el texto literal de `VRC.Quest.Performance.1`, no en el resumen.
2. **`stat unit`, `stat rhi` — sin doc oficial en prosa** de qué threshold indica qué. El único método con fuente oficial para aislar fill-rate es el de cámara-apagada + render-scale-0.01 (§2).
3. **Overdraw en dispositivo** — ninguna doc de Epic ni Meta ofrece un view mode; hay que inferirlo de RenderDoc Meta Fork.
4. **`t.MaxFPS` en VR** — sin recomendación oficial de valor para Quest.
5. **Umbral exacto de "extended periods" en VRC.Quest.Performance.1** — Meta no define cuántos segundos/frames constituyen un período extendido por debajo de 60 fps; solo dice "revisar el gráfico de FPS con OVR Metrics".
6. **SysPTW** — experimental a partir de Horizon OS v83; sin fecha ni compromiso de Meta de cuándo (o si) sale de experimental.
