# Iluminación en Quest 3 standalone — UE 5.8

> **Target: Meta Quest 3 standalone (APK Android), renderer MÓVIL, todo horneado.**
> **Tres niveles de evidencia:** **[DOC]** doc oficial Epic/Meta · **[SRC]** código de UE 5.8 en `C:\Program Files\Epic Games\UE_5.8` (es lo que ejecuta; Epic no lo comprometió por escrito) · **[FOLCLORE]** sin fuente.
> ⚠️ **Las docs móviles de Epic están podridas de fósiles de UE4/ES2.** Varias páginas clave **404ean en 5.8** (`lighting-for-mobile-platforms`, `stationary-lights`, `use-cascaded-shadows`, `use-modulated-shadows`) — las features siguen vivas, sin prosa. **Cuando Epic calla o se contradice, manda el [SRC].**

---

# 🔴 1. EMISIVOS QUE ILUMINAN — el mecanismo Turrell

**Sí funciona: una superficie que brilla puede iluminar la sala sin ninguna luz colocada.** Y funciona en Quest, porque **es una feature de tiempo de horneado**: el APK solo recibe texturas de lightmap. Quest nunca se entera de que un emisivo las produjo.

> [DOC] "Emissive Materials can cast light into the level when you are using Static Lighting, however this functionality is **not enabled by default**." — [Using the Emissive Material Input](https://dev.epicgames.com/documentation/en-us/unreal-engine/using-the-emissive-material-input-in-unreal-engine)
> Se activa por malla: **Details → Lightmass Settings → Use Emissive for Static Lighting**.
> [SRC] `EngineTypes.h:2415` "If true, allow using the emissive for static lighting." · `:2452` default **`false`**.

## 🔴 Las tres trampas que no están en la prosa
1. **Los rebotes de emisivo los controla `NumSkyLightingBounces`, NO `NumIndirectLightingBounces`.**
   > [SRC] `WorldSettings.h:80` "Number of skylight **and emissive** bounces to simulate."
   **Default = 1** [SRC] `:213`. `NumIndirectLightingBounces` (default 3) es solo "point / spot / directional" [SRC] `:71`.
   → **En una obra donde las aperturas luminosas SON la luz, todo corre a un rebote por defecto.** Probablemente el ajuste de mayor palanca del proyecto. ⚠ Su costo es **proporcional** al número de rebotes (a diferencia de los indirectos).
2. **Un emisivo por debajo de 0.01 se descarta entero** (solo CPU Lightmass).
   > [SRC] `BaseLightmass.ini:65` comentario de Epic: "; Only emissive texels above .01 will be used to create mesh area lights" → `EmissiveIntensityThreshold=.01`
   > [SRC] `SceneExport.h:232` "Emissive intensities must be larger than this to contribute toward scene lighting."
   → **Trampa mortal para superficies suaves y tenues.** Si un panel se ve brillando pero no ilumina nada, ese es el primer sospechoso. Editable en `BaseLightmass.ini`, no en la UI.
3. **El `EmissiveBoost` de World Settings está MUERTO en 5.8.**
   > [SRC] `WorldSettings.h:113` "Scales the emissive contribution of all materials in the scene. **Currently disabled and should be removed with mesh area lights.**" — y está declarado como `UPROPERTY()` pelado, **sin `EditAnywhere`** → no existe en la UI.
   → **Todo tutorial que diga "subí el EmissiveBoost de World Settings a 10" es folclore de UE4.** El **`EmissiveBoost` por malla** es tu única palanca expuesta [SRC] `EngineTypes.h:2452`, default 1.0.

## Unlit sí sirve para hornear
> [SRC] `LightmassRender.cpp:1127` — Lightmass solo avisa "unsupported shading model" para modelos FUERA de este set, y **`MSM_Unlit` está en la lista aceptada**.
> [SRC] `LightmassRender.cpp:624` el renderer de Lightmass reporta `MSM_Unlit` al exportar (sin Substrate).

**[INFERENCIA]** Un emisor Unlit es *ideal* para Turrell: emite al horneado pero no tiene respuesta difusa, así que la apertura luminosa no re-recibe el rebote y se ensucia. Y se ahorra el costo de shader lit en Quest.
⚠ **No verificable:** si un emisor Unlit igual necesita UVs de lightmap válidas. **El solver de Lightmass NO se distribuye en la instalación binaria** (`Programs/UnrealLightmass/Private/` solo trae `LightmassCore`). **Resolver con un bake de prueba.**
⚠ Epic **nunca dice** si el emisivo horneado requiere Lit. Única señal indirecta, y va en contra: recomienda Default Lit *"if you want your emissive Material to illuminate the objects around it"*.

## Las mallas dinámicas SÍ ven los emisivos
> [SRC] `SceneExport.h:250` — `MeshAreaLightGeneratedDynamicLightSurfaceOffset=30`: "Distance along the average normal … to place a light to handle influencing dynamic objects."
→ Lightmass **spawnea una luz real** por mesh area light para los objetos dinámicos. No llega por el lightmap.

---

# 🔴 2. GPU LIGHTMASS vs CPU LIGHTMASS

## El target Android NO bloquea el GPU Lightmass
Verificado en fuente por tres vías independientes:
> [SRC] `GPULightmass.uplugin`: `"Modules": [{"Name":"GPULightmass","Type":"UncookedOnly","PlatformAllowList":["Win64"]}]` — `PlatformAllowList` es la plataforma donde **corre el módulo (tu editor)**, NO el target de cook. Ambos módulos son `UncookedOnly`/`Editor` → **nunca se cocinan al APK**, así que Android no puede "bloquearlos".
> [SRC] `RenderUtils.cpp:~838-905` — dentro de `#if WITH_EDITOR` la máscara de ray tracing itera **todas** las plataformas y **solo pone bits en true**. No hay ninguna ruta que limpie el bit de otra plataforma. Los `GRayTracingPlatformMask.Fill(false)` viven en la rama **`#else`** (runtime cocinado), que nunca corre en tu editor.
> [SRC] `AndroidTargetPlatformSettings.h:115` — Android lee **su propio** flag (`bEnableRayTracing`, false) → simplemente **no pone sus bits**. Nunca toca el de Win64/SM6.

## 🔴 EL BLOQUEADOR REAL: el Preview Rendering Level
> [SRC] `GPULightmassEditorModule.cpp:~147` — `RayTracingStatus = GetRayTracingDisabledReason(World->Scene->GetShaderPlatform());`

Se evalúa contra **el shader platform del mundo del editor**, o sea **tu Preview Rendering Level**. Si lo pones en Android/Vulkan móvil — que es exactamente lo que hay que hacer en un proyecto Quest para ver los colores bien — el GPULM se niega:
> [SRC] `LOCTEXT` verbatim: "GPU Lightmass requires hardware ray tracing which is disabled by some of your project settings (**an incompatible shader platform (eg. ES3.1) is enabled and active**, or disabled on your current target platform)."
> [SRC] razones enumeradas: `DISABLED_BY_PROJECT_SETTINGS` · `DISABLED_BY_TARGET_PLATFORM` · `INCOMPATIBLE_SHADER_PLATFORM` (eg. ES3.1) · `INCAPABLE_RHI` (eg. DX11) · `INCOMPATIBLE_PLUGIN` (**RenderDoc**) · `INCAPABLE_HARDWARE`

**→ Casi seguro este es el origen del folclore "el GPU Lightmass no anda en proyectos Android". No es el target: es el modo de preview.**
**Flujo correcto: Preview Rendering Level = SM6 → hornear → volver a Android Vulkan para inspeccionar.**

Checklist GPULM: **Support Hardware Ray Tracing = ON** (+ Compute Skin Cache) · **D3D12 + GPU RTX** · **Preview = SM6 al hornear** · **RenderDoc desactivado**.
> [DOC] Requisitos del host: "GPU Lightmass leverages Microsoft's DXR API … which requires DirectX 12" · "Windows 10" · "Ray Tracing-capable NVIDIA GPU" · **Beta**: "Learn to use this Beta feature, but use caution when shipping with it."
> ⚠ **SM6 NO se menciona** en la página de GPULM. No afirmar que lo requiere.

## 🔴 GPULM IGNORA todos los controles de emisivo
Grep de todo el plugin (60 archivos): **cero hits** de `bUseEmissiveForStaticLighting`, `EmissiveBoost`, `DiffuseBoost`, `NumIndirectLightingBounces`, `NumSkyLightingBounces`, `IndirectLightingQuality`, `IndirectLightingSmoothness`.
> [DOC] lo confirma: "The **Use Emissive for Static Lighting** setting is **not necessary** when baking lighting with GPU Lightmass." · "Light from Emissive Materials **automatically propagates** into the GPU Lightmass result."
> [SRC] `LightmapPathTracing.usf:132` `static const uint EnableEmissive = 1;` · `:358` `const bool bIncludeEmissive = EnableEmissive;` — **path tracer bruto: TODO emisivo contribuye, siempre, sin casilla, sin boost, y SIN el corte de 0.01.**

GPULM tiene su propio objeto de settings [SRC] `GPULightmassSettings.h`: `GISamples` **512** (32–65536) · `StationaryLightShadowSamples` 128 · `bUseIrradianceCaching` true · `IrradianceCacheQuality` 128 · `bUseIrradianceCacheBackfaceDetection` ("**Aggressive Leak Prevention**") **false** · `bUseFirstBounceRayGuiding` false · `VolumetricLightmapQualityMultiplier` 4 · `bCompressLightmaps` true · `Denoiser` IntelOIDN.

| | **CPU Lightmass** | **GPU Lightmass** |
|---|---|---|
| GI de emisivo | solo con la casilla, por malla | **siempre, path-traced** |
| `EmissiveBoost` | ✅ por malla | ❌ ignorado |
| Emisivo < 0.01 | ❌ **descartado** | ✅ contribuye |
| Control de rebotes | `NumSkyLightingBounces` | `GISamples` (fuerza bruta) |
| Método | photon mapping + irradiance cache | path tracing + denoise OIDN |
| Anti-leak | geometría/settings | `bUseIrradianceCacheBackfaceDetection` |
| Lightmass Portals | ✅ | ❌ **no soportados** (grep: cero hits de `Portal`) |
| Importance Volume | ✅ | ⚠ parcial (solo sizing) |
| Quality levels (Preview/…/Production) | ✅ | ❌ **ignorados** |
| Velocidad | lento | rápido + "Bake What You See" |
| Estado | shipping, **no deprecado** | **Beta** |

**[INFERENCIA] Para Turrell, GPULM encaja mejor**: emisivo path-traced sin umbral ni contabilidad por malla es exactamente el caso "degradado suave desde superficies tenues", y el photon mapping es históricamente el peor para manchas en superficies grandes suavemente iluminadas. El costo es perder `EmissiveBoost` como dial de arte → **hay que autorar la intensidad en el material**.
**CPU Lightmass NO está deprecado** [SRC] grep `lightmass.*deprecat` → cero hits; `UnrealLightmass-*.dll` presente y compilada. Congelado, no muerto. ⚠ [DOC Meta, blog 2023] "The Unreal Lightmass tool is **no longer built by default**" → en source builds, **verificar que Lightmass compile**.

---

# 3. World Settings → Lightmass (defaults reales, del [SRC])
Epic publica muy pocos números. `WorldSettings.h:210-238` (constructor) y `:60-208` (tooltips + `UIMin`/`UIMax`) sí.

| Ajuste | **Default** | Rango de Epic | Comentario de Epic |
|---|---|---|---|
| `StaticLightingLevelScale` | **1** | 1.0–4.0 | "For large levels it can drastically reduce build times to set this to 2 or 4." / "Warning: Setting this to less than 1 will greatly increase build times!" |
| `NumIndirectLightingBounces` | **3** | 1–10 | "Bounce 1 takes the most time … and contributes the most to visual quality" |
| **`NumSkyLightingBounces`** | **1** | 1–10 | **"skylight AND emissive bounces"** ← el nuestro |
| `IndirectLightingQuality` | **1** | 1–4 | "Warning: Setting this higher than 1 will greatly increase build times!" |
| `IndirectLightingSmoothness` | **1** | 0.5–6.0 | "Higher values like 3 smooth out the indirect lighting more, but at the cost of indirect shadows losing detail." |
| `DiffuseBoost` | **1.0** | 0.1–6.0 | |
| `EmissiveBoost` | 1.0 | — | ❌ **no editable — "Currently disabled"** |
| `bCompressLightmaps` | **true** | — | "Disabling … will reduce artifacts but increase memory and disk size by **4x**." |
| `VolumetricLightmapDetailCellSize` | **200** | 50–1000 | "Halving the DetailCellSize can increase memory by up to a factor of **8x**." |
| `VolumetricLightmapSphericalHarmonicSmoothing` | **.02** | 0–1 | "a ringing artifact occurs which manifests as **unexpected black areas on the opposite side**" |
| `bUseAmbientOcclusion` | **false** | — | |

**El único número de tuning que Epic publica:**
> [SRC] `WorldSettings.h:88` "It can be useful to **reduce IndirectLightingSmoothness somewhat (~.75)** when increasing quality to get defined indirect shadows."

🔴 **NO usar Environment Color para la atmósfera:**
> [SRC] `WorldSettings.h:103` "This light source **currently does not get bounced as indirect lighting** and causes reflection capture brightness to be incorrect. **Prefer using a Static Skylight instead.**"
→ La tentación de poner el color del vacío ahí es fuerte. **No rebota, que es todo el punto de la obra.**

⚠ **Epic no publica ningún valor recomendado** de `StaticLightingLevelScale`, `IndirectLightingQuality`, ni `VolumetricLightmapDetailCellSize` para VR ni móvil. Los `UIMin/UIMax` son **sliders, no recomendaciones**. Quien te dé "los valores de VR" se los está inventando.

## Quality levels (solo CPU Lightmass)
[SRC] `BaseLightmass.ini` — son **multiplicadores de escala**. **No existe sección `Preview`: Preview es la base sin escalar (1×).**
| | Preview | Medium (`:224`) | High (`:244`) | **Production (`:264`)** |
|---|---|---|---|---|
| `NumShadowRaysScale` | 1 | 2 | 4 | **8** |
| `NumHemisphereSamplesScale` | 1 | 2 | 4 | **8** |
| `NumIndirectPhotonsScale` | 1 | 2 | 4 | **8** |
| `NumPenumbraShadowRaysScale` | 1 | — | — | **32** |

Production además: `RecordRadiusScaleScale=.5625` · `IrradianceCacheSmoothFactor=.75` · `NumAdaptiveRefinementLevels=3` — **[INFERENCIA]** eso *es* el fix de manchas del irradiance cache. **Con CPU Lightmass, Production no es opcional para bakes finales.**
⚠ **GPULM ignora el dropdown de Lighting Quality por completo.**

---

# 🔴 4. LIGHTMAPS: el proyecto está forzado a LQ
> [SRC] `UnrealEngine.cpp:19111` —
> ```cpp
> bool AllowHighQualityLightmaps(const FStaticFeatureLevel FeatureLevel) {
>   return FPlatformProperties::SupportsHighQualityLightmaps()
>     && (FeatureLevel > ERHIFeatureLevel::ES3_1)   // ← Quest falla acá
>     && (CVarAllowHighQualityLightMaps.GetValueOnAnyThread() != 0)
>     && !IsMobilePlatform(...);                     // ← y acá
> }
> ```
**Dos cláusulas independientes excluyen Quest. NO es overrideable con `r.HighQualityLightMaps`** — el cvar es uno de cuatro AND.
> [SRC] `RendererSettings.h:1220` "**Note that the mobile renderer requires low quality lightmaps**, so disabling this setting is not recommended for mobile titles using static lighting."
> [SRC] `MobileBasePassRendering.cpp:172` — los ÚNICOS shaders de base pass con lightmap en móvil son `LMP_LQ_LIGHTMAP` y `LMP_MOBILE_DISTANCE_FIELD_SHADOWS_AND_LQ_LIGHTMAP`. **No existe ningún `LMP_MOBILE_*_HQ_LIGHTMAP`.**

🔴 **NUNCA desactivar `r.SupportLowQualityLightmaps`.** Vive en Project Settings bajo **"Shader Permutation Reduction"**, al lado de cosas que sí conviene apagar. Apagarlo **borra la iluminación horneada en el dispositivo, en silencio, mientras el editor se ve perfecto.**

**Diferencia semántica que importa:** [SRC] `r.HighQualityLightMaps` = "allow high quality lightmaps which **don't bake in direct lighting of stationary lights**" → **en móvil/LQ, la luz directa de las estacionarias SÍ se hornea.** Para un proyecto 100% horneado eso es bueno, pero significa que las estacionarias se comportan distinto a lo que dicen las docs de escritorio.
LQ y HQ tienen **los mismos 2 coeficientes** [SRC] `SceneManagement.h:351` — LQ **no** es menos texturas, es **menos precisión** (8 bits por canal, `FColor`).

## UVs — el fallo silencioso #1
> [DOC] "**Lightmap Coordinate Index** specifies which UV channel should be used … when Lightmass generates a lightmap texture" · "if you generate a lightmap UV after import … you'll need to **manually assign** the correct UV Channel"
**Si generas UVs al canal 1 pero el Lightmap Coordinate Index sigue en 0, horneas tus UVs de textura. No da error.** [SRC] defaults: `bGenerateLightmapUVs(true)`, `SrcLightmapIndex(0)`, `DstLightmapIndex(1)`, `MinLightmapResolution(64)` (`EngineTypes.h:3046`).

> [DOC] "no two triangles in the mesh can overlap in the 2D texture space" · "All UV coordinate values must fall between 0 and 1"
> [DOC] **Generar es re-empaquetar, NO desplegar:** "UE5 will **not split UV chart edges** to create separate UV islands. It only **repacks** the existing UV charts."

⚠ **`Min Lightmap Resolution` NO es una resolución — es un input de EMPAQUETADO.** [SRC] `MeshUtilities.cpp:2626` el packer apunta a **`Min - 2`**, reservando **1 texel de borde por lado**. → A resolución 64 tienes **62×62 usables**. Epic usa `1/62` en su propia fórmula de snapping, no `1/64`.
> [DOC] "Setting Light Map Resolution … **lower than the Min Lightmap Resolution** will cause seams and potential light leaks"
→ Poner `Min` en la resolución **más baja** que la malla vaya a usar nunca, no en la típica.

## Densidad
> [SRC] `BaseEngine.ini:326` `IdealLightMapDensity=0.2` · `MaxLightMapDensity=0.8` — **el único "recomendado" que Epic embarca**, y solo colorea un view mode.
> [SRC] `LightMapDensityShader.usf:126` `Density = TexelArea / WorldSpaceArea` → **texeles de lightmap por unidad² de mundo** (1 uu = 1 cm).
⚠ [SRC] `LightMapDensityRendering.cpp:203` — la escala **difiere entre HQ y LQ** → **el view mode colorea distinto en el editor de escritorio que en Quest. Hacer los pases de densidad en Mobile Preview (Android).**
**Usarlo para UNIFORMIDAD, no para un número absoluto.**

## ⚠ Epic/Meta NO publican
- Resolución de lightmap recomendada por malla → **ninguna**
- Presupuesto de memoria de lightmaps → **ninguno**, de Epic ni de Meta
- Presupuesto de memoria de texturas para Quest → **ninguno de Meta**. Solo RAM total: **Quest 3 = 5.75 GiB**, Quest 2/Pro = 4.4 GiB [DOC](https://developers.meta.com/horizon/documentation/unreal/po-memory-ram/)
- Block size de ASTC para lightmaps → **ninguno**
- Ajustes para degradados suaves → **ninguno**

---

# 🔴 5. BANDING — el riesgo central de esta obra
**Epic no documenta el banding de lightmaps. Ni Epic ni Meta.** Lo que sigue es mecanismo verificado + inferencia.

**Tres factores multiplicativos:**
1. **LQ forzado = 8 bits por canal** (§4). No overrideable.
2. **Compresión en bloques** → en Android **ASTC** [SRC] `BaseAndroidEngine.ini:35` `ASTCVersion=501`; tabla de remap ASTC→ETC2 en `AndroidTargetPlatformControls.cpp:310`. Un compresor de bloques interpola entre dos endpoints por bloque → **en un degradado suave es el peor caso**: escalones en el borde del bloque, no solo banding fino.
3. **El panel no lo puede tapar.** [DOC Meta] "LCD limitations prevent them from meaningfully differentiating brightness levels **below 13 out of 255** for 8-bit sRGB or **0.0015 out of 1.0** for linear-RGB shader output" — [Display design](https://developers.meta.com/horizon/design/display/) ⚠ es doc de **diseño/panel**, agnóstico de motor — no es guía de Unreal.

## Qué hacer, por palanca/costo
1. **Destildar `Compress Lightmaps`** en los niveles críticos de degradado. Ataca el factor (2), que es el error más grande y más "en bloques". **Es per-World Settings = POR NIVEL** → encaja perfecto con nuestros 9 sublevels. 4× de un número chico sigue siendo chico, y tenemos 5.75 GiB. **Máxima palanca.** ⚠ El "4×" es cálculo de Epic contra DXT — **medir con `stat streaming`**, no asumirlo para ASTC.
2. **Dithering / ruido en el material.** Rompe las bandas por debajo del umbral de discriminación del panel. **Cuesta cero memoria.** Ni Epic ni Meta lo documentan para lightmaps; es puro mecanismo. **Probarlo antes de gastar memoria.**
3. **🔴 La resolución es la palanca EQUIVOCADA.** El banding en un degradado suave es **cuantización en VALOR, no falta de detalle espacial**. Subir la resolución cuesta memoria **cuadráticamente** y hace las bandas **más anchas y suaves, no menos**. La intuición "más resolución arregla el banding" **es falsa para este modo de falla**. Subir resolución para arreglar **manchas**, no bandas.
4. **Manchas → subir calidad de Lightmass, no resolución.** Es ruido de muestreo del GI, no de texeles.
5. **Un solo chart por superficie de degradado.** Una costura en medio de un degradado es imperdonable.
6. **Verificar EN EL DISPOSITIVO.** El editor renderiza **HQ** en una GPU de escritorio. **Todo el riesgo (precisión LQ, bloques ASTC, piso del LCD) es estructuralmente invisible en el viewport.**

## Costuras: Epic dice explícitamente que la calidad NO las arregla
> [SRC] `WorldSettings.h:88` `IndirectLightingQuality`: "Note that this **can't affect compression artifacts, UV seams or other texture based artifacts**."
⚠ **La regla "4 texeles de padding porque DXT es 4x4" es de escritorio.** En Quest son **ASTC**, cuyo bloque es configurable (4x4, 6x6, 8x8…). El espíritu se mantiene (padear ≥ 1 bloque) pero **4 texeles es un piso, no una garantía**. Epic no publica regla de padding para ASTC.

---

# 🔴 6. EL LÍMITE DE 4 LUCES ESTACIONARIAS — no es un contador, es coloreo de grafos
> [DOC 5.8] "Only four or fewer Stationary Lights can overlap one another or any single piece of geometry" — [Stationary Light Mobility](https://dev.epicgames.com/documentation/en-us/unreal-engine/stationary-light-mobility-in-unreal-engine)
> [DOC 5.8] Al excederse: "only dynamic (or whole scene shadows) are used, which brings with it **considerable performance cost**" · "the light icon will change to one with a **Red X**"
> [SRC] `LightComponent.cpp:1933` string real del motor: "**Severe performance loss**: Failed to allocate shadowmap channel for stationary light due to overlap - light will fall back to dynamic shadows!"

**La luz NO se vuelve Movable.** Sigue Stationary y pierde solo su sombreado estático.
> [SRC] `DynamicShadowMapChannelBindingHelper.h:15` `// This is used in forward only` · `:21` `static const int32 CHANNEL_COUNT = 4;` — ⚠ **Epic nunca escribe "4 canales" en ninguna página de 5.8.** El número solo existe en el código.

**El mecanismo real** [SRC] `LightComponent.cpp:1877` `ReassignStationaryLightChannels()` es un **algoritmo de coloreo de grafos**, no un contador:
- [SRC] `:1840` el overlap se testea **bidireccionalmente**, con un `//@todo - more accurate spotlight <-> spotlight intersection` de Epic → **spot-vs-spot es cono contra ESFERA envolvente: conservador y pesimista.** Dos spots cuyos conos nunca se tocan pueden contarse como superpuestos.
- [SRC] `:1853` **las direccionales se insertan primero y SIEMPRE se llevan un canal.**
  > [DOC] "the Directional Light typically requires a channel from **the entire Level** it is in, even areas that may be underground or hidden"
- [SRC] `:1876` `//@todo - retry with different ordering heuristics when it fails` — **Epic admite que la asignación es imperfecta y depende del orden.**
> [DOC 4.27, la única página que lo explicó — **404ea en 5.8**]: "This is a **graph coloring problem**, so there are often **fewer than 4** overlapping allowed due to topology."

**Regla honesta: una estacionaria falla cuando los 4 canales ya están tomados por luces que la solapan. Puedes tener menos de 4 y fallar igual.**
🔴 **Trampa Turrell:** la estética son **lavados de color suaves y superpuestos** — que es exactamente la topología que rompe este asignador (radio grande, mutuamente superpuestas). El fallo es **silencioso hasta el build** (un `PerformanceWarning`, no un error) y termina en **sombras dinámicas de escena completa en Quest**, que no podemos pagar.
**Verificar con:** `View Mode > Optimization Viewmodes > Stationary Light Overlap` [SRC] `EditorViewportCommands.cpp:98`. ⚠ La página de Viewport Modes de 5.8 lista este modo **sin ningún texto descriptivo**.
**→ Presupuesto real: 3 estacionarias**, porque la direccional siempre se lleva una.

## Qué hornea cada movilidad
| | Sombra directa | Indirecta | Canal | Límite |
|---|---|---|---|---|
| **Static** | **en el lightmap** | lightmap | ninguno | **ninguno** |
| **Stationary** | **shadow mask de distance field, separado por luz** | lightmap | **1 de 4** | **sí** |
| **Movable** | dinámica | VLM | ninguno | — |

> [DOC] "Lightmass generates **distance field shadow maps** for Stationary Lights on Static objects" · "provide accurate shadow transitions, even at lower resolutions, and incur **very little runtime cost**"

Static hornea directa+indirecta **juntas** en un lightmap → **por eso no tiene límite ni canal**. Stationary las separa, y esa máscara aparte es lo que necesita canal.
> [DOC] costos: Static "medium quality, lowest mutability, **lowest performance cost**" · Stationary "**highest quality**, medium mutability, medium cost" · Movable "highest mutability, highest cost"
> [DOC] 🔴 contraintuitivo pero oficial: "**non-shadowing Movable lights are very inexpensive** to calculate, and carry a **lower cost than lights that are set to Static**"
> [DOC] trampa: "Each Movable object creates **two dynamic shadows** from a given Stationary Light" · "With enough Movable objects … it's actually **more efficient to use a light with its Mobility set to Movable**."

---

# 🔴 7. MALLAS DINÁMICAS EN ESCENA HORNEADA — una sola muestra plana
> [SRC] `PrimitiveSceneInfo.cpp:2529` —
> ```cpp
> if (Scene->GetFeatureLevel() < ERHIFeatureLevel::SM5   // Quest es ES3_1 → entra
>     && Scene->VolumetricLightmapSceneData.HasData()
>     && (Proxy->IsMovable() || ...))
> {
>     UpdateIndirectLightingCacheBuffer(..., Proxy->GetBounds().Origin, ...);  // UNA muestra
> }
> ```
> [DOC] lo confirma en una frase suelta: "**On mobile, interpolation is done on the CPU at the center of each object's bounds.**" — vs. escritorio: "interpolated efficiently on the **GPU per-pixel**". **Es una rama de plataforma, no un nivel de calidad.**

**El remate arquitectónico** [SRC] `LightMapRendering.cpp:737`: en móvil **el Volumetric Lightmap y el Indirect Lighting Cache NO son alternativas — el VLM alimenta la plomería del buffer del ILC.** Solo se reemplazó el generador de muestras. **Ninguna doc dice esto.**
→ **[FOLCLORE] "En móvil se usa el ILC en vez del VLM" es falso, y está invertido.**
→ **`ILCQ_Volume` (gradiente 5x5x5) no significa nada en Quest** — la rama `< SM5` saltea el `LightingAllocation` entero. **No esperar gradiente a través de una malla dinámica.**

**Consecuencias prácticas:**
1. **Una malla dinámica se ilumina como un punto.** No puede mostrar gradiente. **En una obra de degradados, un objeto móvil va a leerse plano y pegoteado.**
2. **Los bounds son la superficie de control.** Como la muestra sale de `GetBounds().Origin`, unos bounds grandes o mal centrados **traen luz del lugar equivocado** (p. ej. de dentro de una pared). **Bounds ajustados y bien centrados no son optimización: son CORRECCIÓN.**
3. **Costo de CPU real** [SRC] `RenderCore.h:75` stat dedicada `STAT_InterpolateVolumetricLightmapOnCPU` en `STATGROUP_InitViews`; `LightMapRendering.cpp:739` cachea por posición → **un objeto quieto cuesta un lookup; uno que se mueve re-interpola en CPU cada frame.** Medir con `stat InitViews`.
4. [SRC] `:750` `Parameters.DirectionalLightShadowing` viaja en esa misma muestra → **sí recibe sombreado direccional horneado, como un valor único para todo el objeto.**
5. > [DOC] fuera del Importance Volume: "Positions outside of the Importance Volume **reuse the border texels** of the Volumetric Lightmap (clamp addressing)" → **una malla dinámica fuera del volumen recibe datos de borde embarrados.**

**La palanca que las docs no señalan** [SRC] `EngineTypes.h:210` `ELightmapType::ForceVolumetric` — expuesto por componente. **Una malla ESTÁTICA puede optar por la ruta volumétrica** para matchear a una dinámica cercana.
> [SRC] caveat de Epic ahí mismo: "Volumetric Lightmaps have better directionality and no Lightmap UV seams, but are **much lower resolution** … and frequently have **self-occlusion and leaking problems**." · "Lightmass **currently requires valid lightmap UVs and sufficient lightmap resolution** to compute bounce lighting, even though the Volumetric Lightmap will be used at runtime."

**Parches negros en mallas dinámicas** → [SRC] `WorldSettings.h:170` `VolumetricLightmapSphericalHarmonicSmoothing` (default `.02`): "a **ringing artifact** occurs which manifests as **unexpected black areas on the opposite side**". **[INFERENCIA]** un brillo direccional fuerte desde una apertura hacia un vacío oscuro es **el peor caso para el ringing de SH**. Subirlo de .02.

---

# 8. LUCES DINÁMICAS EN QUEST — la ruta soportada
**Movable + Cast Shadows OFF, por el light grid del forward móvil.**
> [DOC] "non-shadowing Movable lights are very inexpensive"
> [SRC] `LightComponent.cpp:1793` — el asignador de canales solo mira luces con `HasStaticShadowing() && !HasStaticLighting()` (o sea, Stationary) → **una Movable NUNCA consume canal.**
> [DOC matriz] **Point light dynamic shadows = No en TODAS las movilidades** en móvil → no perdemos nada apagando sombras.

## 🔴 El límite real en Quest: 8, no 32
> [SRC] `LightGridInjection.cpp:123` default del motor: `GMaxCulledLightsPerCell = 32;`
> [SRC] **`Engine/Config/Android/AndroidEngine.ini:73`** — override que Epic embarca:
> ```ini
> ; Support Mali 64k texel buffer limitation, tuned for 1080p. If you target 2k-4k resolutions please also set the LightGridPixelSize to 128
> r.Forward.LightGridSizeZ = 8
> r.Forward.MaxCulledLightsPerCell = 8
> ```
**En un build Android el tope efectivo son 8 luces POR CELDA, no 32** — y el comentario de Epic avisa que **a 2K-4K conviene además `r.Forward.LightGridPixelSize = 128`**, que es exactamente Quest 3. **Este número no aparece en ninguna doc de Epic ni de Meta.**
⚠ Es **por celda**, no por escena. El total es ilimitado; lo que importa es **cuántas luces se superponen en el frustum de una celda**. Los lavados grandes y superpuestos de Turrell son otra vez el peor caso.

> [SRC] `ConsoleManager.cpp:4025` `r.Mobile.Forward.EnableLocalLights` default **1**. ⚠ **La doc de Epic y su propio comentario en el código dicen "(default)" en la línea del 0 — es un bug de comentario. El default registrado es 1.**
> [SRC] `EngineTypes.h:675` `LOCAL_LIGHTS_BUFFER UE_DEPRECATED(5.8, "...please use mobile deferred r.Mobile.ShadingPath=1")` — **deprecado en 5.8 y oculto de la UI.** (Y no podemos ir a deferred: perderíamos MSAA y el tonemap subpass.)

## 🔴 "1 luz direccional" es POR CANAL DE ILUMINACIÓN → hasta 3
> [SRC] `ScenePrivate.h:1896` `/** For the mobile renderer, the first directional light in each lighting channel. */ FLightSceneInfo* MobileDirectionalLights[NUM_LIGHTING_CHANNELS];`
> [SRC] `EngineTypes.h:560` `#define NUM_LIGHTING_CHANNELS 3` · `ScenePrivate.h:2655` `GetMobileDirectionalLightForView(int32 ChannelIdx, ...)`

**El "1 directional light of any type" de Epic es en realidad UNA POR CANAL DE ILUMINACIÓN, o sea hasta 3** — cada una afectando un set disjunto de mallas. **Epic no lo dice en ninguna parte.** ⚠ Derivado de [SRC] — **testear en dispositivo antes de diseñar encima.** Para Turrell es una herramienta genuina no publicitada: tres lavados direccionales de color independientes.

## Rect lights: se degradan a spot
> [SRC] `ConsoleManager.cpp:4032` `r.Mobile.Forward.RenderRectLightsAsSpotLights` default **1** → **una rect light se convierte en spot, en silencio.**
→ **Para las aperturas rectangulares de Turrell: NO esperar shaping de rect light. Construir la forma en geometría/emisivo.**

---

# 9. SOMBRAS EN MÓVIL
- 🔴 **`r.Mobile.EnableCSM` NO EXISTE en 5.8** [SRC] grep de todo el árbol → cero hits. **Folclore muerto de UE4.**
- Los cvars reales [SRC] `ConsoleManager.cpp`: `r.Mobile.EnableStaticAndCSMShadowReceivers` (default 1) · `r.Mobile.EnableMovableLightCSMShaderCulling` (1) · `r.Mobile.UseCSMShaderBranch` (0, **"only with r.AllowStaticLighting=0"** → no disponible para nosotros) · **`r.Mobile.AllowDistanceFieldShadows`** (1)
- 🔴 **`r.Mobile.AllowDistanceFieldShadows` NO tiene nada que ver con Mesh Distance Fields.** [SRC] "Generate shader permutations to render **distance field shadows from stationary directional lights**" → **es la máscara de sombra horneada de las estacionarias. NO desactivarlo mientras quitamos los Distance Fields.**
- 🔴 **En VR el presupuesto de cascadas se DIVIDE POR 2** [SRC] `MobileLightingCommon.ush:140` `#define MAX_MOBILE_SHADOWCASCADES 4u`; `SceneRendering.cpp:1085` `MaxMobileShadowCascadeCount = MAX_MOBILE_SHADOWCASCADES / (bCubeShareCascades ? 1 : Family->Views.Num())` → en estéreo hay 2 vistas → **techo de 2 cascadas.** ⚠ Solo [SRC], ninguna doc lo dice. **Verificar en dispositivo.**
- **`r.Mobile.EnableStaticAndCSMShadowReceivers=0`** [SRC] `RendererSettings.h:1400`, categoría literal **`MobileShaderPermutationReduction`**: "Disabling will **free a mobile texture sampler and reduce shader permutations**." Solo se necesita si una superficie debe recibir sombra horneada **Y** CSM dinámico a la vez. **Nosotros no → apagarlo.** Requiere reiniciar el editor.
- **Modulated shadows**: vivas pero sin ninguna prosa en 5.x (`use-modulated-shadows` 404ea). [SRC] `DirectionalLightComponent.h:247` — **solo direccionales + solo Stationary + solo móvil**, con `EditCondition` real. **[INFERENCIA] Para un vacío oscuro, modular oscuridad sobre oscuridad no hace nada visible. Saltar.**
- **[INFERENCIA] Para una obra sentada de 15 min: saltar CSM entero.** Es costo que no necesitamos.

# 10. SKYLIGHT
> [DOC] "A Sky Light set to **Static** will be baked completely into the lightmap … and therefore **costs nothing**."
> [DOC] matriz: Static/Stationary/Movable Sky Light = **Yes** en las 3 columnas móviles. ⚠ **Sky Light dynamic shadow casting = No** en todas.
- 🔴 **`r.Mobile.EnableStationarySkylight` NO EXISTE** [SRC] cero hits. **El real es `r.SupportStationarySkylight`, y no es mobile-scoped.**
  > [SRC] `SceneRendering.cpp:4485` comentario decisivo: `// For mobile EnableStationarySkylight has to be enabled in a projects with StaticLighting to support Stationary or Movable skylights`
  → **Con `r.AllowStaticLighting=True`, si el skylight es Stationary/Movable hay que dejar `r.SupportStationarySkylight=1`.** Un skylight **Static** no lo necesita.
  > [DOC] "It's recommended to **disable if your project does not require Stationary skylights**" → **[INFERENCIA] con skylight Static es una ganancia de perf gratis: base pass más barato.**
- **Real Time Capture**: [DOC] "Make sure the sky light real time capture is not run on platform where it is considered out of budget" — implica gating sin documentarlo. **Asumir fuera de presupuesto en Quest. No encender.**
- **[INFERENCIA] Un skylight Static con Specified Cubemap es el mejor valor**: ambiente omnidireccional de color, gratis, horneado, y llega a las mallas dinámicas por el VLM. **Pero NO produce gradiente espacial** — es de baja frecuencia por construcción. **Los degradados salen del lightmap + emisivo + material. El skylight es el piso ambiente que impide que el vacío se vaya a negro puro.**

# 11. Otros
- **Light Functions: NO en forward móvil, en ninguna movilidad** [DOC]. Fakearlo con emisivo o cookies horneadas.
- **IES**: soportado en forward móvil pero **OFF por defecto** [SRC] `ConsoleManager.cpp:4039` `r.Mobile.Forward.EnableIESProfiles` default **0**, `ECVF_ReadOnly | ECVF_MobileShaderChange` → ini + reinicio, y cuesta permutaciones.
- **Light shafts**: [SRC] `SceneVisibility.cpp:5688` en móvil son **solo bloom** — no hay ruta de LightShaftOcclusion. **[INFERENCIA] El light-shaft bloom es de las pocas herramientas atmosféricas que tenemos. Vale probarlo.**
- **Precomputed Visibility**: [DOC] "Make sure to use Precomputed Visibility" para móvil; requiere build de lighting y volúmenes **en el nivel persistente**. **[INFERENCIA] Probablemente NO vale la pena acá**: compra tiempo de render-thread culleando ocluidos, y un Turrell **casi no tiene oclusión** (esa es la estética). Revisar solo si el profiling dice render-thread bound.
- **`r.DistanceFields=0` ya es el default de Android** [SRC] `BaseAndroidEngine.ini:29` → quitar DFs no da trabajo, ya estaban apagados.

# 12. Streaming + lightmaps (encaja con nuestra arquitectura)
> [SRC] `Level.h:559` `TObjectPtr<UMapBuildDataRegistry> MapBuildData;` · `:623` `bIsMapBuildDataOwner` · `MapBuildDataRegistry.h:299` `LevelLightingQuality`

- **Los lightmaps son POR NIVEL**, en un paquete `_BuiltData` separado. **Cargan y descargan con su sublevel** → **pagamos por niveles residentes, no por los 9.** Exactamente lo correcto para la memoria de Quest.
- **Sí streamean** (mips) [SRC] `LightMap.cpp:146` `TEXTUREGROUP_Lightmap`; sin `NumStreamedMips` → default -1 = "all mips can stream". **Dos mecanismos independientes.**
- **Hornear con los sublevels cargados y visibles.** Un actor en un sublevel oculto al hornear no recibe datos válidos.
- `LevelLightingQuality` es por nivel → **[INFERENCIA] mantenerla uniforme**, o la discontinuidad se va a ver.
- ⚠ **Vigilar el pico de descarga**: si el nivel entrante carga antes de que el saliente libere, ambos sets de lightmaps están residentes a la vez.

# ✅ CHECKLIST DE ILUMINACIÓN
1. **Verificar `Lightmap Coordinate Index == Destination Lightmap Index` en TODAS las mallas.** Fallo silencioso #1.
2. **Subir `NumSkyLightingBounces`** (default 1) — controla los rebotes de emisivo. Mayor palanca.
3. **Preview = SM6 al hornear con GPULM**, volver a Android Vulkan para inspeccionar.
4. **Presupuesto: 3 estacionarias** (la direccional se lleva una). Vigilar `Stationary Light Overlap` y **el warning "Severe performance loss" en el log del build**.
5. **Static > Stationary** donde la luz nunca cambia. Sin canal, sin límite, sin costo.
6. **Luces dinámicas: Movable + Cast Shadows OFF.** ≤8 superpuestas por celda. `r.Forward.LightGridPixelSize=128`.
7. **Mallas dinámicas: bounds ajustados y centrados** (corrección, no optimización), dentro del Importance Volume, **sin esperar gradiente**.
8. **`r.Mobile.EnableStaticAndCSMShadowReceivers=0`** · **`r.Mobile.AllowDistanceFieldShadows=1`** (¡no confundir!) · skylight **Static** + `r.SupportStationarySkylight=0`.
9. **NUNCA tocar `r.SupportLowQualityLightmaps`.**
10. **Banding: destildar `Compress Lightmaps` por nivel + dithering en material. NO subir resolución.**
11. **Importance Volume ajustado** — [SRC] `Lights.cpp:409` su extensión **dimensiona los shadow depth maps**: uno grande **degrada** la resolución de sombras.
12. **Verificar en dispositivo.** El editor renderiza HQ en una GPU de escritorio: todo el riesgo real es invisible ahí.
