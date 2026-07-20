# Quest 3 STANDALONE — config de proyecto, iluminación y materiales

> **Target real: Meta Quest 3 standalone (APK Android). NO es PC VR.** Confirmado por el usuario y por `bPackageForMetaQuest=True`. Corre el **renderer MÓVIL** (`r.Mobile.ShadingPath=0`), no el de escritorio.
> **Regla:** cada afirmación con fuente. Tres niveles: **[DOC]** doc oficial · **[SRC]** código de UE 5.8 en `C:\Program Files\Epic Games\UE_5.8` (es lo que ejecuta, pero Epic no lo comprometió por escrito) · **[FOLCLORE]** sin fuente. Investigado 16/07/2026.

---

# 🔴 EL HALLAZGO PRINCIPAL: `r.MobileHDR=False` está borrando el look, y no hace falta

## "Mobile HDR" NO es HDR. Es el interruptor maestro del post-procesado.
El campo interno se llama **`bMobilePostProcessing`** [SRC `RendererSettings.h:1158`]. Ese nombre engaña a todo el mundo: suena a una feature de pantallas HDR prescindible, y es **todo tu pipeline de color**.
> [DOC] "If true, mobile pipelines include a full post-processing pass with **tonemapping**." — [Rendering Settings](https://dev.epicgames.com/documentation/unreal-engine/rendering-settings-in-the-unreal-engine-project-settings)

Con `False` el motor entra en lo que el propio código llama **"GammaLDR mode"**. Lo que se pierde, cada uno verificado en fuente:
| Feature | Gate [SRC] | Con HDR=False |
|---|---|---|
| **Curva filmica (tonemapper)** | `PostProcessing.cpp:3545` `bool bDoGammaOnly = !IsMobileHDR();` | **muere** — solo encode gamma |
| **Color grading / LUT** | `:3549` `if (... && !bDoGammaOnly) ColorGradingTexture = AddCombineLUTPass(...)` | **muere** |
| **Todo el post móvil** (bloom, viñeta, DOF) | `:287` `... && IsMobileHDR();` | **muere** |
| **Eye adaptation** | `PostProcessMobile.cpp:55` | **muere** |
| **Local Exposure** | SM5-gated **Y** MobileHDR-gated | **muere** |
| **FXAA/TAA** | `SceneUtils.cpp:83` *"Disable antialiasing in GammaLDR mode"* | forzado a None (queda MSAA) |

Lo que **sobrevive**, lista completa [DOC matriz móvil 5.8]: **exposición manual, translucidez Raster, MSAA.** Nada más.
**"Plano, lavado, opaco" es la firma exacta de un tonemapper ausente.** Para una obra de degradados suaves en un vacío oscuro es el peor caso posible: una rampa lineal→sRGB quema las altas y aplasta los negros.

## ⚠️ El compromiso NO EXISTE en 5.8 — es folclore de UE4
**"Mobile Multi-View requiere MobileHDR apagado" es FALSO.** No existe ninguna compuerta así en el código de 5.8. Rastro del mito: [Gear VR Best Practices (4.27)](https://dev.epicgames.com/documentation/unreal-engine/samsung-gear-vr-best-practices?application_version=4.27) — **era de UE4, específico de Gear VR, superado.**
> [DOC] "Multi-View requires **the Vulkan graphics API**" — [Meta Multi-View](https://developers.meta.com/horizon/documentation/unreal/unreal-multi-view/) — **ese es el único requisito.** No menciona Mobile HDR.

## ✅ Y mejor: el Multi-View ENCIENDE SOLO el tonemapper barato
**[SRC — leído y verificado directamente, `Engine/Source/Runtime/Engine/Private/SceneUtils.cpp`]:**
```cpp
ENGINE_API bool IsMobileTonemapSubpassEnabled(EShaderPlatform Platform, bool bMultiViewRendering)
{
    static auto* MobileTonemapSubpassPathCvar = ...FindTConsoleVariableDataInt(TEXT("r.Mobile.TonemapSubpass"));
    return ((MobileTonemapSubpassPathCvar && (...GetValueOnAnyThread() == 1)) || bMultiViewRendering)
           && IsMobileHDR() && !IsMobileDeferredShadingEnabled(Platform);
}
```
Dos lecturas críticas:
1. **`bMultiViewRendering` SOLO satisface la primera cláusula** → con Multi-View + MobileHDR=True el subpass se activa **sin tocar el cvar**.
2. 🔴 **`&& IsMobileHDR()`** → **`r.Mobile.TonemapSubpass=1` con `MobileHDR=False` NO HACE NADA.** El cvar queda seteado y la función devuelve `false` igual. *(Este es un error real que cometió una de las investigaciones: recomendaba exactamente esa combinación inútil. Se resolvió leyendo el motor.)*

> [DOC] "approximately **600 microseconds** of additional render time" · soporta "**Color Grading (includes LUT), Filmic Tonemapping, Vignette**" · usa "Vulkan subpasses instead of … an additional render pass" · "**not compatible with mobile deferred shading**" (estamos en forward ✅) · "Enabling … may cause a visible increase in **color saturation**" (es esperado: es la curva que faltaba)
> — [Meta: Tone Mapping in Unreal](https://developers.meta.com/horizon/documentation/unreal/unreal-tonemapping/) · funciona en **UE stock + Meta XR Plugin**, no hace falta el fork.

**600 µs sobre un presupuesto de 13.9 ms (72 fps) = 4.3%.** No es un compromiso, es una ganga.

## `bPackageForMetaQuest` te encendió algo sin avisar
> [SRC `AndroidRuntimeSettings.cpp:71`] `const bool SupportssRGB = bPackageForMetaQuest || bPackageForOpenXRImmersive;` → fuerza `r.Mobile.UseHWsRGBEncoding`.
> [SRC] `IsMobileColorsRGB()` = `!IsMobileHDR() && bMobileUseHWsRGBEncoding` — **verificado leyendo el código.**

Con eso activo, `PostProcessing.cpp:2839` **saltea el pase de tonemap ENTERO** y deja que el hardware escriba sRGB por función fija. Es la ruta más despojada del motor. **Es lo que está borrando físicamente el look — y se apaga solo al poner `MobileHDR=True`.** No hay que tocarlo (y `bPackageForMetaQuest` lo va a reescribir igual).

---

# 🔴 Por qué el editor MIENTE
## La VR Preview por Link NO SIRVE para juzgar color
> [DOC] "Link causes your device to behave like a **PC VR headset**." · "The visual appearance and performance characteristics of an app running over Link **may differ** from running it on a Meta Quest headset."
> — [Meta: Use Link for App Development](https://developers.meta.com/horizon/documentation/unreal/unreal-link/)

Por Link el **PC renderiza con el renderer de escritorio** y streamea video. **Nunca toca la ruta móvil.** "En el editor se ve súper" es un dato sin valor para color.

## ✅ La solución: Preview Rendering Level → Android Vulkan
> Project Settings → Platforms → activar **Android Vulkan** · luego **Settings → Preview Rendering Level → Android Vulkan**
> [DOC] "recompiles materials to best emulate the look and feature set of the renderer preview that you selected" — carga también el device profile y la escalabilidad de la plataforma. Verificar que el viewport diga `Feature Level: Android Vulkan ES31`.
> ⚠ [DOC] "The Mobile Previewer is intended to match mobile devices as closely as possible but **it may not always be indicative**."
> — [Using Preview Platform](https://dev.epicgames.com/documentation/en-us/unreal-engine/using-the-mobile-previewer-in-unreal-engine)

**Reproduce el bug en el monitor en 10 minutos, sin cocinar.** Es la mejora de flujo de trabajo más grande disponible.

## Local Exposure: desajuste GARANTIZADO editor↔dispositivo (bug de la plantilla de Epic)
`r.DefaultFeature.LocalExposure.{Highlight,Shadow}ContrastScale=0.8` está **bloqueado dos veces en Quest** [SRC `PostProcessLocalExposure.cpp:87` → `IsFeatureLevelSupported(..., ERHIFeatureLevel::SM5)`, y además tras `IsPostProcessingEnabled`]. **En el editor (SM6) SÍ aplica; en Quest NO.**
⚠ La plantilla `TP_VirtualRealityBP` de Epic setea `r.MobileHDR=False` **Y** Local Exposure `0.8` — valores que su propio MobileHDR garantiza inertes. Y **duplica cada línea** (por eso aparecen 3 veces). **La config heredada no es culpa del usuario.**

## Device profiles: existe uno de Quest 3, pero NO es el culpable
[SRC `Engine/Config/BaseDeviceProfiles.ini`] `[Meta_Quest_3 DeviceProfile]` → `ForceSymmetric=1`, `OcclusionFeedback.Enable=0`, `AdrenoOcclusionMode=1`, `UseChunkedPSOCache=0`; padre `Android_OpenXR` → `sg.ShadowQuality=2`. **Nada toca tonemapping, exposición ni color.** (El mecanismo es real y es un clásico de "empaquetado se ve peor" — acá no aplica.)

---

# 🎯 CONFIG RECOMENDADA
```ini
[/Script/Engine.RendererSettings]
; --- La ruta que REALMENTE corre en Quest ---
r.Mobile.ShadingPath=0             ; forward [DOC] (0=forward, 1=deferred)
r.MobileHDR=True                   ; 🔴 EL CAMBIO. Devuelve tonemapper+grading. Reinicio + rebuild
r.Mobile.AntiAliasing=3            ; MSAA (el entero es INFERIDO — Epic no publica los enteros)
r.MSAACount=4                      ; AGREGAR — Meta recomienda 4x
vr.MobileMultiView=True            ; requiere Vulkan; enciende el tonemap subpass solo
vr.InstancedStereo=True            ; ruta desktop; inofensivo, mantiene honesto el preview
r.AllowStaticLighting=True         ; hornear todo lo posible
r.Mobile.AllowFramebufferFetch=1   ; [sin doc oficial] default de plantilla
r.DefaultFeature.AutoExposure=False
r.DefaultFeature.AmbientOcclusion=False
r.DefaultFeature.MotionBlur=False

; --- BORRAR: no corren en Android o cuestan de gratis ---
; r.ForwardShading            → [DOC] "forward shading on DESKTOP platforms. Requires SM5" — INERTE en Quest
; r.Substrate                 → Beta; SIN doc de Epic ni Meta sobre Quest; "mobile don't support diffusion models"
; r.RayTracing                → desktop deferred only; ADEMÁS arrastra SkinCache ([DOC] "requires this to be enabled")
; r.RayTracing.RayTracingProxies.ProjectEnabled → sin doc
; r.Shadow.Virtual.Enable     → [DOC] necesita SM6.6/DX12 + acoplado a Nanite
; r.GenerateMeshDistanceFields → 🔴 [DOC] "you will still have increased memory usage EVEN IF you are not
;                                using any Distance Field features" — el ÚNICO que cuesta HOY
; r.SkinCache.CompileShaders  → solo existía por el ray tracing
; r.AntiAliasingMethod=3      → desktop; en móvil manda r.Mobile.AntiAliasing
; r.Mobile.PropagateAlpha     → solo passthrough/MR. Nuestra obra es un vacío cerrado. [DOC] "~30% cost to the accumulation"
; r.DefaultFeature.LocalExposure.* → SM5-only: activo en el EDITOR, inerte en Quest = mentira pura
r.DynamicGlobalIlluminationMethod=0  ; Lumen: [DOC] "does not currently support Virtual Reality (VR) systems"
r.ReflectionMethod=0                 ; [DOC] 0 NO es "sin reflejos": "Reflections can still come from
                                     ; Reflection Captures, Planar Reflections or a Skylight"

[/Script/AndroidRuntimeSettings.AndroidRuntimeSettings]
bPackageForMetaQuest=True
MinSDKVersion=32                   ; correcto
TargetSDKVersion=34                ; 🚨 CAMBIAR — 32 BLOQUEA la subida a la tienda
; verificar que bSupportsVulkan=True esté presente (ES3.1 off + Vulkan no-on = build sin RHI)
```
**Después: correr el Meta XR Project Setup Tool.** [DOC] Meta **se niega a enumerar** los ajustes en su doc y responde "corré el PST": *"checks your project settings against a set of predefined rules"*. **Ninguna página enumera las reglas** → el PST es la única lista completa autoritativa.

## 🚨 `TargetSDKVersion=32` bloquea la tienda HOY
> [DOC] "Starting **March 1, 2026**, all new Meta Horizon apps … are required to target **Android 14 (API level 34)**." · "**API level 34 will be enforced during binary upload**" · minSdk 32 sigue bien.
> — [Meta: Android 14 requirement](https://developers.meta.com/horizon/blog/meta-quest-apps-android-14-march-1/)

Esa fecha **ya pasó hace 4 meses**. El "target 32" viene del mandato Android 12L, superado.

## Vulkan sí; ES3.1 no
> [DOC] "Vulkan is the **recommended** API for both mobile VR and PC VR applications on Meta headsets." · "OpenGL ES is now considered a **legacy** graphics API." · "enable Support Vulkan, and **disable Support OpenGL ES3.1**."
> — [Meta: Vulkan and OpenGL](https://developers.meta.com/horizon/documentation/unreal/os-vulkan-opengl/)

**`bBuildForES31=False` es exactamente lo que Meta manda hacer.** ⚠ El nombre de la clave está viejo: Epic renombró a "Support OpenGL **ES3.2**"; `bBuildForES31` es la clave legacy de UE4.

## Mobile deferred (`r.Mobile.ShadingPath=1`): NUNCA para esta obra
- [DOC] "Deferred rendering can **not** support MSAA due to the amount of space it would need in GBuffer" — y MSAA es lo que Meta recomienda para Quest (en VR importa más: el micro-movimiento de cabeza hace crawlear el aliasing).
- [SRC] el tonemap subpass exige `!IsMobileDeferredShadingEnabled` → **perderías el tonemapper barato**.
- Lo que ofrece deferred es "muchas luces dinámicas". Queremos pocas. **Quedarse en 0.**

---

# 🔴 Volumetric Fog: OFICIALMENTE NO en Quest
> [DOC] Matriz móvil 5.8 — columna literal **"Mobile Forward w/ HDR Disabled (Head-mounted Mobile XR)"**: **Volumetric Fog = No** en las 3 columnas. Volumetric Clouds = No.
> — [Mobile Rendering Features Reference](https://dev.epicgames.com/documentation/en-us/unreal-engine/rendering-features-reference?application_version=5.8)

⚠ **Pero el motor SÍ lo implementa en móvil** [SRC `MobileShadingRenderer.cpp:608`, `MobileFogRendering.cpp`, `VolumetricFog.cpp:1866` con branch móvil mantenido]. La compuerta real es **`r.Mobile.EarlyZPass=1`** (default 0), que fuerza un **depth prepass completo**.
**NO construir arte encima.** Razones: (a) Epic tabula tu config exacta y escribe No; (b) el precio es re-renderizar toda la geometría opaca en una GPU de tile que **ya hace descarte por hardware**; (c) [SRC `MobileBasePassVertexShader.usf:120`] **no aplica a la translucidez en móvil** → los volúmenes aditivos ni la recibirían.

---

# ✅ EL TOOLKIT TURRELL EN QUEST (todo "Yes" en tu columna)
> *"El medio de Turrell es luz en el aire, no vidrio."* Y él tampoco post-procesa la luz: construye aperturas y velos y deja que el falloff trabaje.

1. **Unlit + Emissive — el instrumento principal.** [DOC] Yes/Yes/Yes. *"Make sure all of your Materials have their shading model set to Unlit for maximum performance."* El degradado se construye **en el material**: falloff radial, Fresnel, distancia a cámara. ALU barata, cero samplers, cero luces.
2. **Local Fog Volumes — el sustituto OFICIAL del volumetric fog.** [DOC] **"Works on all platforms"** (vs. "Does not work on all platforms" del Volumetric Fog) · *"across low-end and high-end platforms with multiple scalability levels"* · ruta de media resolución específica de móvil, confirmada [SRC `RenderLocalFogVolumeHalfResMobile`, `MobileShadingRenderer.cpp:1789`]. Costo: *"similar to dynamic lights … related to the extent of the space on screen"*. Son esferas con falloff radial, sin sombreado volumétrico → **para los Ganzfeld eso es casi todo el vocabulario**. ⚠ LFV **no aparece en la matriz móvil** → soporte afirmado por su página + el cvar móvil, no por la tabla. Testear en dispositivo.
3. **Exponential Height Fog** — [DOC] Yes/Yes/Yes, y **per-pixel por defecto en móvil** [SRC `FogRendering.cpp:57`, `r.Mobile.PixelFogQuality=1`]. **Directional Inscattering** = halo de color alrededor de la direccional.
4. **Sky Atmosphere** — [DOC] Yes/Yes/Yes. Degradado de cielo físico sin geometría ni luces. **Los Skyspace de Turrell son literalmente eso.**
5. **Additive** — [DOC] Yes/Yes/Yes. ⚠ **La trampa:** *"Translucent primitives are blended **in gamma space**. In most cases, this will require you to author your translucent textures and Materials **differently**."* → **autorar EN EL DISPOSITIVO desde el día uno.**

## 🔴 La restricción de arte que ningún ajuste arregla
> [DOC] "**LCD limitations prevent them from meaningfully differentiating brightness levels below 13 out of 255** for 8-bit sRGB or 0.0015 out of 1.0 max for linear-RGB shader output values" · "it is recommended to **author content in a higher brightness range** as much as possible."
> — [Meta: Color and Brightness Mastering Guide](https://developers.meta.com/horizon/resources/color-brightness-mastering/)

**El Quest no distingue NADA por debajo de 13/255.** Todo el rango de sombras sutiles colapsa a negro plano. Hay que **subir el piso de luminancia** y trabajar los degradados más arriba que en un monitor.
> [DOC] Los cascos vienen **calibrados de fábrica** → **cualquier consejo de "aplicá una corrección de gamma" está mal.**

## Lo que va a matar el frame: OVERDRAW
> [DOC Epic] "The total GPU time of a frame can be **doubled or more** by having overdraw." · "Use masked and transparent Materials **sparingly**. Only use them in places where they cover a **small part of the screen**."
> [DOC Meta] "translucent rendering adds almost **80% more GPU time** per frame when compared to masked rendering" — [Translucent vs Masked](https://developers.meta.com/horizon/blog/translucent-vs-masked-rendering-in-real-time-applications/)
> [DOC Epic, ejemplo propio] "the translucent volumetric sheets are very expensive… I asked to have the translucent sheets should be removed."

**Preferir pocas mallas grandes OPACAS Unlit con el degradado en el material, antes que muchas capas aditivas apiladas.** Cada capa extra multiplica fill rate sobre una superficie que llena la pantalla. Meta además avisa: con MSAA los bordes translúcidos **"bleed"**.
**Presupuestar por CAPAS, no por materiales.** En VR se paga dos veces (dos ojos).

---

# Iluminación en Quest
- [DOC matriz] **"1 directional light of any type"** — repetido para static, stationary y movable. **Es el único número duro que Epic publica.**
- Static: Point/Spot/Rect **Yes**. Stationary/Movable: **Rect Light No**.
- 🔴 **Sombras dinámicas: Point Light = No, en TODAS las movilidades.** Directional Yes; Spot Yes (stationary spot = No con HDR disabled); Sky Light No.
- **Cantidad de luces dinámicas: Epic NO publica número en 5.8.** ⚠ El famoso **"hasta 4"** es **solo de 4.27**. Meta tampoco publica: su único número duro ("hard limit of eight lights per draw call") es del **fork**, en una ruta **no-default**. **[FOLCLORE]** cualquier número que circule.
- [DOC Meta] *"Using real-time lights **sparingly** as they are resource-intensive. **Bake lighting whenever possible**."*
- **Horneado:** Precomputed Lighting / GI / IBL / Visibility = **Yes/Yes/Yes**. [DOC] *"For projects that use precomputed lighting, we **strongly recommend** using Mobile Forward shading."* ✅
- ⚠ **Volumetric Lightmap degradado en móvil:** [DOC] *"On mobile, interpolation is done on the **CPU at the center of each object's bounds**"* → por objeto, no por píxel. Mallas dinámicas chicas, o indirecta plana.
- **Indirect Lighting Cache: deprecado** engine-wide → Volumetric Lightmaps lo reemplazan.

# Materiales en móvil
- 🔴 **El límite de 16 texture samplers SÍ aplica en Quest. Vulkan NO lo levanta.** [SRC] `DataDrivenShaderPlatformInfo.cpp:163` default `MaxSamplers = 16`; Windows lo sobrescribe a 32; **Android NO tiene override** → 16 en `VULKAN_ES3_1_ANDROID` y en OpenGL. `bBuildForES31=False` es irrelevante para esto. [DOC] confirma: *"The exception being ES3.1 (mobile), which still has a hard limit … (16)"*. **Para un proyecto Unlit/emisivo/procedural, 16 no es restricción real.**
- ⚠ **"You have five texture samplers available"** sigue vivo en la página de 5.8 → **fósil de la era ES2. Son 16.**
- **Instrucciones: Epic NO publica ningún número objetivo.** Solo *"Materials should use as few texture lookups and instructions as possible."*
- **No soportado en móvil:** Two Sided Foliage, Hair, Cloth, Eye, **Thin Translucent**; Anisotropy, Tangent, Fuzz Color, Backlit; **Volume material domain** (→ sin materiales de volumen raymarcheado).
- **Reflexiones:** Reflection Captures (Box/Sphere), Planar, Scene Capture, HDR Cubemap = Yes. ⚠ **La matriz dice SSR="Yes" y está MAL** — el post está gateado por `IsMobileHDR()` en código. Para un proyecto Unlit las reflexiones son casi irrelevantes: sin capturas ni luces locales dinámicas, Meta mide **~0.14 ms** ahorrados.

# Presupuesto (números de Meta, Quest 3)
| | |
|---|---|
| Refresh | 72 (**default**), 80, 90, 120 Hz |
| **72 fps = 13.9 ms** · 90 fps = 11.1 ms · 120 fps = 8.3 ms | [DOC](https://developers.meta.com/horizon/documentation/unreal/po-perf-opt-mobile/) |
| Draw calls (Light Simulation) | **700–1000** |
| Triángulos | **1.3M–1.8M** |
| [DOC] *"Any app logic that takes longer than **two milliseconds** can probably be optimized."* | |

⚠ Los rangos de draw calls vienen hedgeados: *"internally-recommended ranges, but results may vary"*. **Nuestra obra es "Light Simulation"** → **estamos limitados por FILL RATE, no por geometría.** Gastar polígonos en superficies suaves sin miedo; gastar overdraw con cuidado.
⚠ **Epic 5.8 sigue diciendo "draw calls <=700 / triangles <=500k"** benchmarkeado contra **un iPad 4 (2012) a 30 fps**. **Ignorar. Usar los de Meta.**
⚠ **"Quest exige 72 fps mínimo" es FOLCLORE** — el [VRC.Quest.Performance-1](https://developers.meta.com/horizon/resources/vrc-quest-performance-1/) dice **60 fps**. **Objetivo: 72 Hz / 13.9 ms.** No perseguir 90.

# ⚠️ La integración de Meta NO soporta 5.8
> [DOC] [Matriz de compatibilidad](https://developers.meta.com/horizon/documentation/unreal/unreal-compatibility-matrix/): la última integración es **v85.0, forkeada de UE 5.6.1**, y hay issue conocido de que la resolución dinámica ya se rompe en 5.7.

→ Estamos en **UE vanilla + Meta XR Plugin**: **sin** optimizaciones de LightGrid del fork, sin ETFR, sin occlusion culling por software, sin los cvars `r.Mobile.UniformLocalLights.*`. No es fatal (Epic tiene `xr.OpenXRFrameSynthesis` nativo desde 5.7, equivalente a AppSW), **pero no planificar sobre features del fork.**

---

# ❌ FOLCLORE sin fuente oficial
| Creencia | Realidad |
|---|---|
| **"MobileHDR debe estar off para Multi-View"** | ❌ **FALSO en 5.8.** No existe la compuerta. Viene de Gear VR 4.27. **Es el mito que configuró este proyecto** |
| "Hasta 4 luces dinámicas en móvil" | Solo 4.27. 5.8 no lo repite |
| "8 luces en Quest" | Es del **fork**, **por draw call**, ruta no-default |
| "50–100 draw calls / 750k tris" | Era Quest 1. Sin fuente actual |
| "Quest exige 72 fps" | El VRC dice **60** |
| "Solo Default y Unlit en móvil" | ❌ 4.27. En 5.8 Subsurface, Clear Coat, etc. son Yes |
| "5 texture samplers" | Fósil de ES2. **Son 16** |
| "Flipear UseHWsRGBEncoding arregla el color" | Sin fuente; e **inerte** con MobileHDR=True |
| "El Quest aplica una gamma distinta al editor" | Sin fuente, y **calibración de fábrica lo contradice** |
| "El ray tracing cuesta permutaciones aunque esté inerte" | Sin fuente Epic. Las razones verificadas para sacarlo son otras |
| "r.SkinCache.CompileShaders causa permutaciones" | Sin doc. El cvar documentado es `SkipCompilingGPUSkinVF` |

# 🔴 Donde Epic/Meta están EN SILENCIO
1. `r.Mobile.UseHWsRGBEncoding` — **sin doc en prosa** (solo tabla de cvars). Comportamiento solo por [SRC].
2. `r.Mobile.PropagateAlpha` — **sin doc de Epic**. Propósito inferido de la doc de passthrough de Meta.
3. `r.Mobile.AllowFramebufferFetch` — sin doc.
4. **Los enteros de `r.Mobile.AntiAliasing`** — Epic publica las etiquetas, **nunca los números**. `3=MSAA` es inferencia (consistente con el enum desktop). **Verificar en la UI del editor.**
5. **Substrate en Quest** — nunca abordado por Epic ni Meta.
6. **Lista de reglas del PST de Meta** — mecanismo documentado, reglas no.
7. **Escalabilidad / device profiles para Quest** — ninguna guía de ningún vendor.
8. **Local Exposure en móvil/SM5** — solo [SRC].
9. **Volumetric fog bajo MobileHDR=False** — sin compuerta encontrada, pero el composite es en **espacio gamma** y el fog produce scattering lineal HDR. **Epic casi seguro nunca lo testeó.**

---

# ✅ CHECKLIST (en orden)
1. **Preview Rendering Level → Android Vulkan.** 10 min, reproduce el bug en el monitor. **Dejar de juzgar color por Link.**
2. **Build Lighting Only** — descartar el banner de lighting sin construir.
3. **`r.MobileHDR=True`** + reiniciar editor + rebuild (cvar read-only, define permutaciones). El subpass se activa solo por Multi-View.
4. **Limpiar** las líneas muertas (arriba) + de-duplicar lo que dejó la plantilla.
5. **`TargetSDKVersion=34`** — bloqueante de tienda.
6. **Re-tunear exposición DESPUÉS** de recuperar el tonemapper, no antes. (`ExtendDefaultLuminanceRange` está deprecado-como-off; **on** es el estado soportado → tratar exposición como EV100.)
7. **APK real en el casco.** Es el único nivel que ninguna doc desmiente: Epic desmiente el previewer, Meta desmiente Link, y el XR Simulator emula **la API, no la pantalla**.
8. **Si ahora se ve sobresaturado** → mirar color space (Meta XR Plugin → Color Space; el default es **P3** y los paneles cubren **sRGB**). Preferir regradear antes que apagar la curva recién recuperada.
9. **Autorar contra el panel, no contra el monitor** (piso de 13/255).
