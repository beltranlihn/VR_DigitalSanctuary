# PSO cache, compilación de shaders y hitches de packaging — UE 5.8 / Quest 3 standalone

> **[DOC]** oficial · **[SRC]** código UE 5.8 en `C:\Program Files\Epic Games\UE_5.8` · **[META]** doc oficial de Meta · **[FOLCLORE]** sin fuente oficial, marcado explícitamente.
> Investigado 17/07/2026 para "Soul Charger" (obra sentada, 15 min, single-user, Quest 3 standalone, 9 mapas con level streaming, materiales madre + instances horneadas).
> ⚠ Casi todo lo escrito sobre PSO cache en internet es de UE4 o asume DX12/desktop. Este documento verifica cada claim contra Vulkan móvil en 5.8, y contra el código real, no contra suposiciones.

---

# 🔴 VEREDICTO ACCIONABLE (leer esto primero)

## 1. ¿Hace falta el PSO cache para nuestro proyecto? SÍ — y el motor mismo ya lo está diciendo.
El VR Template de Epic (base de este proyecto — nuestro `Config/Android/AndroidEngine.ini` es **copia textual** del template) trae de fábrica:

> **[SRC]** `Templates\TP_VirtualRealityBP\Config\Android\AndroidEngine.ini:9-12` (idéntico en nuestro `VR_Test\Config\Android\AndroidEngine.ini:9-12`):
> ```ini
> ; PSO precaching is extremely slow on first launch for standlone XR devices.
> ; Projects are recommended to use Bundled PSO Caches to avoid stuttering.
> ; Alternatively, re-enable PSO precaching and conceal it with a loading screen by querying FShaderPipelineCache::NumPrecompilesRemaining().
> r.PSOPrecaching=0
> ```

Esto **no es folclore ni un dato viejo de UE4**: es un comentario de Epic, en un archivo de configuración que Epic distribuye con 5.8, específicamente para el caso "XR standalone". Ya lo tenemos activo sin haberlo pedido — heredado del template al crear el proyecto.

**Traducción a nuestro caso:** el sistema automático nuevo de UE5 (PSO Precaching, ver más abajo) existe y funciona en Vulkan/Android, pero Epic mismo lo desactiva por defecto en XR standalone porque el primer arranque se vuelve inaceptablemente lento, y en su lugar recomienda la ruta manual: **Bundled PSO Cache** (`.upipelinecache`/`.spc`, jugar y recolectar).

🚨 **No reactivar `r.PSOPrecaching=1` sin plan.** Si se reactiva, debe ir detrás de una pantalla de carga que consulte el contador de PSOs pendientes (hay que elegir el contador correcto — ver sección 6, es una trampa).

## 2. Regla concreta de qué genera un PSO nuevo (pregunta 4 — la más importante)
Confirmado en `MaterialInstance.cpp`, no en documentación (Epic no lo explica en ningún artículo de materiales):

- **Cambiar parámetros escalares, vectoriales o de textura en una Material Instance → NO genera shader ni PSO nuevo.** La instance sigue usando el `FMaterialResource`/shader map del material padre.
- **Lo que SÍ crea un `FMaterialResource` propio** (`bHasStaticPermutationResource = true`, **[SRC]** `MaterialInstance.cpp:2406`), y por lo tanto shaders y PSOs nuevos, propios de esa instance:
  1. **Cualquier Static Switch Parameter, Static Component Mask Parameter, o Material Layers/Blends** que la instance tenga fijado distinto del set vacío — `HasStaticParameters()`, **[SRC]** `MaterialInstance.cpp:5441-5455`.
  2. **Override de cualquiera de estas "base properties"** respecto del padre — `HasOverridenBaseProperties()`, **[SRC]** `MaterialInstance.cpp:5157-5178`, cita literal del código:
     ```cpp
     return
         GetBlendMode() != Parent->GetBlendMode() ||
         GetShadingModels() != Parent->GetShadingModels() ||
         IsTwoSided() != Parent->IsTwoSided() ||
         IsThinSurface() != Parent->IsThinSurface() ||
         IsDitheredLODTransition() != Parent->IsDitheredLODTransition() ||
         GetCastDynamicShadowAsMasked() != Parent->GetCastDynamicShadowAsMasked() ||
         IsTranslucencyWritingVelocity() != Parent->IsTranslucencyWritingVelocity() ||
         HasPixelAnimation() != Parent->HasPixelAnimation() ||
         IsTessellationEnabled() != Parent->IsTessellationEnabled() ||
         !FMath::IsNearlyEqual(GetOpacityMaskClipValue(), Parent->GetOpacityMaskClipValue()) ||
         GetUsageFlags() != Parent->GetUsageFlags();
     ```

**Implicación directa para Soul Charger:** el plan de "pocos materiales madre + muchas instances" para la estética Turrell es exactamente lo correcto **siempre que las instances solo toquen color, intensidad, textura y parámetros escalares de gradiente**. Eso comparte PSO gratis. Pero:
- Si dentro del mismo material madre se necesitan variantes **opaca/translúcida/masked** (Blend Mode distinto) → cada variante es, a efectos de compilación, un material distinto. Mejor resolverlo con materiales madre separados por Blend Mode, no como "una instance que cambia el blend mode".
- Un **Static Switch** (ej. "usar textura de gradiente sí/no") multiplica shaders: cada combinación de switches usada por al menos una instance activa **es una permutación compilada aparte**. Con pocos switches esto es manejable; no agregar switches "por las dudas".
- **Two Sided** e **Is Masked** (vía Opacity Mask Clip Value) son swaps comunes en instances y **ambos generan PSO nuevo** — vigilar esto en la biblioteca de materiales.

## 3. Level streaming: no hay "warm up" oficial, es automático pero sin garantías
Cada `UPrimitiveComponent` pide su propio PSO precache al registrarse (típicamente en `PostLoad`/registro del componente — confirmado con sitios de llamada en `StaticMeshComponent.cpp`, `SkinnedMeshComponent.cpp`, `LightComponent.cpp`, `DecalComponent.cpp`, `MaterialBillboardComponent.cpp`, `ParticleSystemComponent.cpp`). Esto significa que **al streamear un mapa nuevo, los componentes activan su precache automáticamente, en paralelo, sin que el diseñador tenga que hacer nada** — pero es asíncrono y **no hay garantía de que termine antes del primer draw**. El único control es `r.PSOPrecache.ProxyCreationDelayStrategy` (saltar el render del primitive o sustituir un material default hasta que el PSO real esté listo) — esto evita mostrar un frame roto, **no evita el hitch de CPU/GPU en sí**.
No existe una API de "esperar a que termine el precache de este streaming level" a nivel Blueprint; lo más cercano es `PipelineStateCache::NumActivePrecacheRequests()` (ver sección 6, motor puro, sin exponer a BP).

## 4. Por qué "en el editor anda bien y en el APK se rompe" — está en el código
> **[SRC]** `PSOPrecache.cpp:139-142`:
> ```cpp
> bool IsComponentPSOPrecachingEnabled()
> {
>     return FApp::CanEverRender() && (PipelineStateCache::IsPSOPrecachingEnabled() || IsPSOShaderPreloadingEnabled()) && GPSOPrecacheComponents && !GIsEditor;
> }
> ```
**El precaching automático por componente está apagado por completo en el Editor y en PIE** (`&& !GIsEditor`). No es un efecto secundario ni una casualidad de perf del editor: el sistema literalmente no corre ahí. **PIE nunca va a exhibir el timing real de compilación de shaders/PSO de un build empaquetado.** Esto confirma y explica el síntoma que ya veníamos observando. Cualquier test de hitching tiene que hacerse en el dispositivo (o al menos `-game` standalone), nunca en PIE.

## 5. Config de packaging: qué tocar y qué no
- `bShareMaterialShaderCode` → **ya está en `True` por defecto del motor** (**[SRC]** `Engine\Config\BaseGame.ini:116`) y nuestro `VR_Test\Config\DefaultGame.ini` **no lo overridea** (confirmado leyendo el archivo). No hace falta tocarlo, pero es un prerequisito real: sin esto, el cooker ni siquiera arma la Shader Code Library (**[SRC]** `ShaderLibraryCooking.cpp:73-77`, `IsUsingShaderCodeLibrary()` depende de este flag), y sin shader code library el flujo de Bundled PSO Cache no tiene de dónde recuperar el bytecode.
- `bSharedMaterialNativeLibraries` → default `False` (**[SRC]** `BaseGame.ini:115`). Opcional: reduce tamaño de paquete usando el formato nativo de la plataforma; el propio header dice que **puede aumentar el tiempo de carga** (**[SRC]** `ProjectPackagingSettings.h:426-432`). No hay evidencia de que sea necesario para PSO caching en Android — dejarlo como está salvo que el tamaño de APK sea un problema real.
- `r.CreateShadersOnLoad` → default `0` (**[SRC]** `ShaderCompiler.cpp:532-536`, comentario literal: *"can reduce hitching, but use more memory"*). El motor lo fuerza a `1` temporalmente solo para global shaders al arrancar (**[SRC]** líneas 4582, 5731). No activarlo para contenido de juego sin medir memoria — en un Quest 3 con presupuesto de RAM ajustado (5.75 GiB PSS, ver `streaming-arch.md`) esto compite directamente con el streaming de niveles.
- Shipping vs Development → no encontramos ninguna rama de código que desactive el sistema de PSO precaching o el file cache en Shipping específicamente; el gate real es `GIsEditor`, no la configuración de build. Tomarlo con pinza: no se auditó cada `#if !UE_BUILD_SHIPPING` del subsistema completo, pero no apareció ninguno relevante en los archivos centrales revisados (`PSOPrecache.cpp`, `PipelineStateCache.cpp`, `ShaderPipelineCache.cpp`).

---

# 1. Qué es el PSO cache en 5.8 y cómo se genera — dos sistemas distintos, y hay que saberlo

UE5 tiene **dos sistemas que coexisten**, con nombres parecidos que se prestan a confusión:

### A) `FShaderPipelineCache` (RenderCore) — el sistema "clásico", heredado de UE4
Archivo de un solo lote: **[SRC]** `RenderCore\Private\ShaderPipelineCache.cpp`. Flujo textual de la doc oficial:
> **[DOC]** "Play the game." → "Log what is actually drawn." → "Include this information in the build." — [Optimizing Rendering With PSO Caches](https://dev.epicgames.com/documentation/en-us/unreal-engine/optimizing-rendering-with-pso-caches-in-unreal-engine)

Cvars reales confirmados en código (los nombres y defaults abajo son del `.cpp`, no de la doc, que en varios casos es más vaga o dice otra cosa — ver sección 6):
| Cvar | Default | Fuente |
|---|---|---|
| `r.ShaderPipelineCache.Enabled` | — (requerido =1 para el flujo manual) | [DOC] |
| `r.ShaderPipelineCache.StartupMode` | `1` (Fast) | **[SRC]** `ShaderPipelineCache.cpp:55-64` — **solo 3 modos: 0 Paused, 1 Fast, 2 Background.** Un artículo comunitario menciona un modo "3: Precompile" que **no existe en el `.cpp` de 5.8** — folclore o versión vieja, ver tabla de folclore. |
| `r.ShaderPipelineCache.BatchSize` | `50` | **[SRC]** `:72-77` |
| `r.ShaderPipelineCache.BackgroundBatchSize` | `1` | **[SRC]** `:66-71` |
| `r.ShaderPipelineCache.SaveAfterPSOsLogged` | `0` | **[SRC]** `:114-119`, comentario literal: *"0 will disable automatic saving (which is the default now, as **automatic saving is found to be broken**)."* — confirma por qué el flujo manual usa `-logPSO` + commandlet en vez de autosave. |
| `r.PSO.RuntimeCreationHitchThreshold` | `20` (ms) | **[SRC]** `RHI\Private\PipelineStateCache.cpp:195-200` |

Workflow manual, verificado contra doc oficial (**[DOC]** [Manually Creating Bundled PSO Caches](https://dev.epicgames.com/documentation/en-us/unreal-engine/manually-creating-bundled-pso-caches-in-unreal-engine)):
1. `DefaultEngine.ini` → `[DevOptions.Shaders] NeedsShaderStableKeys=true` (función real en código: **[SRC]** `ShaderCodeLibrary.cpp:1538`, `FShaderLibraryCooker::NeedsShaderStableKeys` en `ShaderLibraryCooking.cpp:2622` — no es solo un flag de ini decorativo, el cooker lo consulta).
2. Empaquetar, correr con `-logPSO`, jugar toda la obra → `.rec.upipelinecache` en `Saved/CollectedPSOs`.
3. Commandlet `ShaderPipelineCacheTools expand` combina el `.rec.upipelinecache` + `.shk` (shader keys, de `Saved/Cooked/.../Metadata/PipelineCaches`) → produce un `.spc`.
4. El `.spc` va a `Build/[Platform]/PipelineCaches/`, con nombre exacto `[Prefijo][ProyectoName][ShaderFormat].spc` (ej. `CL1_SoulCharger_SF_VULKAN_ES31_ANDROID.spc` — el shader format tiene que matchear literal).
5. Repackage. Verificar en log: "Wrote N binary PSOs (graphics:...)" con N > 0, y que **no** aparezca "Encountered a new graphics PSO" en un segundo run con el mismo contenido.

🔴 Dato de plataforma que Epic sí documenta y es fácil de pasar por alto: **[DOC]** *"If you ship an application on Android with both GLES and Vulkan, you need to collect and include two separate cache files, one for each RHI."* Nosotros solo shippeamos Vulkan (confirmar en Project Settings → Android), así que un solo `.spc` alcanza — pero si algún día se agrega GLES como fallback, hace falta el segundo cache.

### B) `PSOPrecache` (Engine, nuevo en UE5) — automático, por componente
Archivos: **[SRC]** `Engine\Public\PSOPrecache.h`, `PSOPrecacheMaterial.h`, `Engine\Private\PSOPrecache.cpp`. Introducido en 5.1 (dato de la doc de Tom Looman, comunitaria — no verificado contra changelog de Epic, marcar como razonablemente confiable pero no oficial). Funciona así:
- Cada `UPrimitiveComponent` (y `UDecalComponent`, `ULightComponent`, `UParticleSystemComponent`, etc.) llama a `PrecachePSOs()` al registrarse — sitios de llamada confirmados en `StaticMeshComponent.cpp:883/901/2273/2401/2534/3335`, `SkinnedMeshComponent.cpp`, `LightComponent.cpp`, `DecalComponent.cpp`, `MaterialBillboardComponent.cpp`, `ParticleSystemComponent.cpp`, `TextRenderComponent.cpp`.
- Cvars: `r.PSOPrecaching` (default `1`, **[SRC]** `PipelineStateCache.cpp:211-218`), `r.PSOPrecache.Mode` (0=Full PSO / 1=Preload shaders only, default 0, **[SRC]** `PSOPrecache.cpp:110-117`), `r.PSOPrecache.ProxyCreationDelayStrategy`, `r.pso.PrecompileThreadPoolPercentOfHardwareThreads` (**[DOC]**, no reverificado en código).
- **Gate crítico:** `IsComponentPSOPrecachingEnabled()` exige `!GIsEditor` — ver veredicto punto 4.

**Diferencia con UE4:** en UE4 solo existía el sistema A (bundled cache manual). El sistema B es exclusivo de UE5 y busca eventualmente reemplazar el flujo manual — pero, como dice el propio comentario del VR Template, **en XR standalone todavía no está listo para reemplazarlo del todo** (arranque lento).

---

# 2. ¿Es necesario para Vulkan en Quest, o lo maneja el motor/driver solo?

**Veredicto: no lo maneja solo. Hace falta intervención explícita, y Epic lo dice en su propio template.**

Evidencia de que Vulkan/Android SÍ está soportado por el sistema de precaching (para que quede claro que no es una limitación técnica de Vulkan):
> **[SRC]** `VulkanRHI.cpp:462-464`:
> ```cpp
> GRHISupportsPSOPrecaching = CVarAllowVulkanPSOPrecache.GetValueOnAnyThread();
> GRHISupportsPipelineFileCache = !GRHISupportsPSOPrecaching || CVarEnableVulkanPSOFileCacheWhenPrecachingActive.GetValueOnAnyThread();
> ```
> con `r.Vulkan.AllowPSOPrecaching` default `true` (**[SRC]** `VulkanRHI.cpp:95-100`).

Android tiene, además, infraestructura **exclusiva de esa plataforma** que no existe en desktop, pensada específicamente para no bloquear el hilo de render con la compilación:
> **[SRC]** `VulkanAndroidPlatform.cpp:2148-2167`, `PostInitGPU`: si `r.Vulkan.UseChunkedPSOCache` (default `PLATFORM_ANDROID`, es decir **ON por defecto en Android** — **[SRC]** `VulkanChunkedPipelineCache.cpp:67`) y `r.PSOPrecaching` y `r.Vulkan.AllowPSOPrecaching` están todos activos, arranca **procesos externos** (`Android.Vulkan.NumRemoteProgramCompileServices`, default `6` — **[SRC]** `VulkanPipeline.cpp:600-609`, aunque el comentario del propio cvar dice *"4 default"*, inconsistencia del comentario contra el valor real, verificado literal) que compilan PSOs de Vulkan **en procesos separados del proceso principal de la app**.

Esto confirma que **Epic construyó infraestructura seria y específica para Android/Quest** — no es una feature de escritorio portada sin pensar a móvil. Pero la existencia de la infraestructura no significa que esté lista para usarse sin cache bundled: el propio template la desactiva (`r.PSOPrecaching=0`) para XR.

## Meta — qué dice oficialmente
> **[META]** *"Many graphics-intense apps, particularly those built with Unreal Engine or Unity, have to pause on startup for several seconds — up to a few minutes, in some cases — to compile and cache shaders."* — [Shader Compilation, Meta Horizon OS Developers](https://developers.meta.com/horizon/documentation/unity/ps-shader-compilation/)
>
> Sobre su feature de Shader Binary Cache (SBC) preloading (pre-cachear shaders del lado del backend de Meta y bajarlos al headset): **[META]** *"At the present time, games built with Unity and Unreal Engine may be processed by the system, but this is not guaranteed as we are still in the process of ramping up support for this feature."*

**Veredicto sobre SBC de Meta: no contar con esto.** Es explícitamente "no garantizado" para Unreal a la fecha de esta investigación. No es una mitigación en la que basar el plan de shipping — a lo sumo un bonus si algún día se activa. Nota: la página de SBC está bajo la URL `/documentation/unity/` de Meta (verificado) — otra señal de que el soporte a Unreal es secundario/tardío en esa feature.

---

# 3. Para un proyecto chico, ¿vale la pena el esfuerzo?

**Sí, y el esfuerzo real es menor de lo que suena.** Con pocos materiales madre + instances (sin static switches por instance, blend mode consistente dentro de cada madre — ver punto 2 del veredicto), el número total de PSOs distintos en toda la obra va a ser bajo — decenas, no miles. El flujo manual (sección 1-A) para un proyecto así es:
1. Un playthrough completo grabado con `-logPSO` (los 15 minutos de la obra, recorriendo los 9 mapas).
2. Un `expand` con el commandlet.
3. Copiar el `.spc` a `Build/Android/PipelineCaches/`.

Eso es. No hace falta infraestructura de recolección continua ni de equipo — con una sola persona jugando la obra completa una vez alcanza para cubrir el 100% del contenido (a diferencia de un juego con contenido generado o ramas de gameplay amplias, donde el bundled cache nunca cubre todo).

**Mitigación más barata que NO alcanza sola:** dejar `r.PSOPrecaching=1` (el default del motor) confiando en el sistema automático. El propio template de Epic dice que esto es "extremely slow on first launch" en XR — y "lento en el primer arranque" para una pieza de museo/instalación (spectator entra, se pone el headset, tiene que empezar) es un problema real de experiencia, no solo un hitch a mitad de obra.

**Conclusión: sí vale la pena.** Es la ruta que Epic mismo recomienda para exactamente este escenario (XR standalone), el volumen de contenido es chico, y el costo de no hacerlo es un hitch de compilación en VR — que por el propio presupuesto del proyecto (13.9 ms/frame, obra de presencia) es catastrófico, no cosmético.

---

# 4. Material instances vs materiales distintos — ver veredicto punto 2 (con las citas de código completas ahí arriba). No se repite acá.

---

# 5. Level streaming e hitches — detalle adicional al veredicto

Cuando se streamea un mapa nuevo:
1. Los actores del sublevel se cargan (paquete), después se registran sus componentes.
2. Cada componente dispara `PrecachePSOs()` en su propio registro — async, en paralelo entre sí.
3. Si el material/vertex-factory/pass ya fue visto antes en la sesión (mismo `FMaterialResource`, mismo hash) → el PSO ya existe en el `PipelineStateCache` en memoria (RHI-level, no es el `.spc` — el `.spc`/bundled cache es lo que evita que ese "ya visto antes" tenga que compilar desde cero la primera vez).
4. Si es la primera vez en toda la sesión que se usa esa combinación → se compila. Con Bundled PSO Cache bien armado, "primera vez en la sesión" debería casi no pasar más allá del primer nivel, porque el cache ya trae compilado todo lo que se vio en el playthrough de grabación.

No hay "warm up" oficial de streaming en el sentido de una función tipo `PreloadLevelShaders(LevelName)`. Lo más cercano documentado es la recomendación genérica de loading screen:
> **[DOC]** *"We highly recommend setting up your initial loading screen with PSO Precache requests in mind."* — [PSO Precaching for Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/pso-precaching-for-unreal-engine)

que habla del arranque inicial, no de transiciones entre sublevels streameados a mitad de obra. Para transiciones a mitad de obra, la única red de seguridad realista con el contenido ya bundleado en el `.spc` es que **ya no haya nada nuevo que compilar** — el Bundled PSO Cache cubre esto directamente si el playthrough de grabación pasó por los 9 mapas. La combinación con el fade sphere / loading screen OpenXR ya documentada en `streaming-arch.md` (sección "Esconder el hitch") sigue siendo la red de seguridad para lo que se escape.

---

# 6. Trampa de nombres: dos contadores de "PSOs pendientes", no confundirlos

La doc oficial menciona `FShaderPipelineCache::NumPrecompilesRemaining()` para gatear la loading screen. **Ese contador pertenece al sistema A (bundled cache clásico)**, calculado a partir de `FShaderPipelineCacheTask::TotalPrecompileTasks` (**[SRC]** `ShaderPipelineCache.cpp:864-874`).

**Existe un segundo contador, para el sistema B (precaching automático nuevo), que la doc no menciona en el mismo lugar:**
> **[SRC]** `PipelineStateCache.cpp:5167-5175`:
> ```cpp
> uint32 PipelineStateCache::NumActivePrecacheRequests()
> {
>     if (!IsPSOPrecachingEnabled()) { return 0; }
>     return GPrecacheGraphicsPipelineCache->NumActivePrecacheRequests() + GPrecacheComputePipelineCache->NumActivePrecacheRequests();
> }
> ```

Si en algún momento se decide reactivar `r.PSOPrecaching=1` (sistema B) detrás de una loading screen — como sugiere el propio comentario del template — **hay que consultar `PipelineStateCache::NumActivePrecacheRequests()`, no `FShaderPipelineCache::NumPrecompilesRemaining()`**, porque son sistemas distintos con contadores distintos. Ninguna de las dos está expuesta a Blueprint por defecto; requeriría un nodo de función C++/plugin fino para consultarlas desde el FlowDirector.

---

# Tabla de folclore

| Creencia | Verdad | Fuente / por qué |
|---|---|---|
| "El PSO cache es cosa de UE4/DX12, en Vulkan/Android no aplica" | **Falso.** Vulkan tiene su propio soporte de precaching (`r.Vulkan.AllowPSOPrecaching`) y Android tiene infraestructura propia (chunked cache + remote compile services) que no existe en desktop. | **[SRC]** `VulkanRHI.cpp:95-100,462-464`; `VulkanAndroidPlatform.cpp:2148-2167`; `VulkanChunkedPipelineCache.cpp:67` |
| "El sistema automático de PSO precaching de UE5 alcanza, no hace falta cache manual" | **Falso para XR standalone específicamente.** Epic mismo lo desactiva por defecto en su VR Template para Android por ser "extremely slow on first launch" y recomienda Bundled PSO Cache. | **[SRC]** `TP_VirtualRealityBP\Config\Android\AndroidEngine.ini:9-12` (verbatim de Epic) |
| "Si funciona bien en el editor/PIE, va a andar bien en el build" | **Falso, y no es una casualidad de perf — está hardcodeado.** `IsComponentPSOPrecachingEnabled()` retorna `false` si `GIsEditor` es `true`. El sistema automático simplemente no corre en el editor. | **[SRC]** `PSOPrecache.cpp:139-142` |
| "Cambiar cualquier parámetro en una Material Instance puede generar un shader nuevo" | **Falso** para parámetros dinámicos (scalar/vector/texture) — esos comparten el shader map del padre siempre. **Verdadero** solo para static switches, static component masks, material layers, y un set específico de "base properties" (blend mode, shading model, two sided, usage flags, etc.). | **[SRC]** `MaterialInstance.cpp:2406,5157-5178,5441-5455` |
| "El PSO cache de Android necesita el mismo `.spc` que Windows/PC VR" | **Falso.** Es específico por plataforma Y por shader format — Android con Vulkan y GLES simultáneos necesita **dos** caches separados; nunca se comparte un `.spc` entre shader formats. | **[DOC]** Manually Creating Bundled PSO Caches |
| "`r.ShaderPipelineCache.StartupMode` tiene 4 modos, incluyendo un modo 3 'Precompile'" | **Dudoso/folclore para 5.8.** El `.cpp` de 5.8 solo define 3 modos (0 Paused, 1 Fast, 2 Background) en el texto del cvar. Puede ser un resabio de doc de otra versión o un artículo desactualizado. | **[SRC]** `ShaderPipelineCache.cpp:55-64` contradice al menos un resumen de doc/tercero que mencionaba un 4to modo |
| "El autosave del PSO cache recolectado guarda solo lo necesario, se puede confiar en dejarlo prendido" | **Falso — está roto y apagado por defecto, según el propio comentario de Epic en el código.** | **[SRC]** `ShaderPipelineCache.cpp:114-119`, *"automatic saving is found to be broken"* |
| "Meta precachea los shaders de mi juego Unreal automáticamente vía Shader Binary Cache" | **No garantizado.** Meta lo dice explícitamente: el soporte para Unreal (y Unity) "is not guaranteed" a la fecha de esta investigación. No planificar shipping asumiendo esto. | **[META]** Shader Compilation, Meta Horizon OS Developers |
| "`bShareMaterialShaderCode` hay que activarlo a mano para que el PSO cache funcione" | **Falso para este proyecto — ya viene en `True` por defecto del motor**, y no está overrideado en `DefaultGame.ini`. Sí es un prerequisito real (sin él no hay shader code library), pero no requiere acción nuestra. | **[SRC]** `BaseGame.ini:116`; `VR_Test\Config\DefaultGame.ini` (leído, sin override) |

---

# Fuentes citadas

**[DOC] Documentación oficial:**
- [Optimizing Rendering With PSO Caches in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/optimizing-rendering-with-pso-caches-in-unreal-engine)
- [Manually Creating Bundled PSO Caches in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/manually-creating-bundled-pso-caches-in-unreal-engine)
- [PSO Precaching for Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/pso-precaching-for-unreal-engine)
- [Using the Android Vulkan Mobile Renderer in Unreal Engine](https://dev.epicgames.com/documentation/unreal-engine/using-the-android-vulkan-mobile-renderer-in-unreal-engine)

**[META] Meta oficial:**
- [Shader Compilation — Meta Horizon OS Developers](https://developers.meta.com/horizon/documentation/unity/ps-shader-compilation/) (nota: URL bajo `/unity/`, aplicación a Unreal explícitamente "no garantizada")

**[SRC] Código del motor (todo en `C:\Program Files\Epic Games\UE_5.8`):**
- `Templates\TP_VirtualRealityBP\Config\Android\AndroidEngine.ini`
- `Engine\Config\BaseGame.ini`
- `Engine\Source\Runtime\RenderCore\Private\ShaderPipelineCache.cpp`
- `Engine\Source\Runtime\RHI\Private\PipelineStateCache.cpp`
- `Engine\Source\Runtime\Engine\Private\PSOPrecache.cpp`
- `Engine\Source\Runtime\Engine\Public\PSOPrecache.h`, `PSOPrecacheMaterial.h`
- `Engine\Source\Runtime\Engine\Private\Materials\MaterialInstance.cpp`
- `Engine\Source\Runtime\Engine\Private\ShaderCompiler\ShaderCompiler.cpp`
- `Engine\Source\Runtime\VulkanRHI\Private\VulkanRHI.cpp`, `VulkanPipeline.cpp`, `VulkanChunkedPipelineCache.cpp`, `Android\VulkanAndroidPlatform.cpp`
- `Engine\Source\Runtime\RenderCore\Private\ShaderLibrary\ShaderCodeLibrary.cpp`
- `Engine\Source\Editor\UnrealEd\Private\Cooker\ShaderLibraryCooking.cpp`
- `Engine\Source\Developer\DeveloperToolSettings\Classes\Settings\ProjectPackagingSettings.h`

**Archivos del proyecto verificados (no son fuente de Epic, pero confirman el estado real heredado):**
- `VR_Test\Config\Android\AndroidEngine.ini` — confirma que `r.PSOPrecaching=0` ya está activo, copiado del template
- `VR_Test\Config\DefaultGame.ini` — confirma que no hay override de `bShareMaterialShaderCode`

**[FOLCLORE] comunitario (marcado, no citado como verdad):**
- [PSO Caching in Unreal Engine — Vermilion (blog)](https://blog.rime.red/pso-caching-in-unreal-engine/) — no usado como fuente de ningún claim de este documento
- [Setting up PSO Precaching & Bundled PSOs — Tom Looman](https://tomlooman.com/unreal-engine-psocaching/) — usado solo para el dato "introducido en 5.1" y "insuficiente solo hasta 5.3, mejorado en 5.6", marcado explícitamente como no verificado contra código/changelog oficial
