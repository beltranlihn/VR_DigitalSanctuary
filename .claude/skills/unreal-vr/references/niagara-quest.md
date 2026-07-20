# Niagara / VFX en UE 5.8 para Meta Quest 3 standalone (Soul Charger)

Investigación con verificación en código fuente (`C:\Program Files\Epic Games\UE_5.8`) y documentación oficial. Contexto: obra fill-rate bound, todo horneado, sin Lumen/Nanite/VSM/Distance Fields, con un parámetro de respiración (float + fase) que llega desde Blueprint en tiempo real.

Clasificación de fuentes en cada punto:
- **(A)** Documentación oficial de Epic o Meta, con URL y cita verbatim.
- **(B)** Código del motor UE 5.8, con ruta de archivo y línea.
- **(C)** Folclore de comunidad, sin fuente oficial — marcado explícitamente como tal.
- **(D)** Medido por nosotros en un Quest real, con build empaquetado. Es la categoría de mayor autoridad de todas: gana sobre A, B y C cuando se contradicen.

---

## 0. Medido en dispositivo (D) — el codo real de Niagara en Quest

**Niagaras pesados corren sin problema en un packaging de Quest.** Probado directamente por el usuario en el dispositivo, en proyectos anteriores: sistemas pesados corren bien en general, **sobre todo sprites**. Con varios sistemas simultáneos aparece drop de frames, pero no colapso.

Esto es el complemento necesario de §2.4: **ni Epic ni Meta publican ningún límite numérico de partículas para Quest** — no existe la cifra que mucha gente cita. Lo que hay es un gradiente de fill-rate, y este dato ubica el codo: el problema no es *un* sistema pesado, es la **acumulación de sistemas superpuestos**. La consecuencia de diseño para Soul Charger: no hay razón para autocensurar la densidad de un sistema individual; la disciplina va en cuántos sistemas coexisten en pantalla y cuánta pantalla cubren.

⚠ No leas esto como "Niagara es gratis". Los bloqueadores reales encontrados en código siguen en pie y son ortogonales a esto: el Light Renderer apagado por defecto (§1) y el clamp de `fx.Niagara.QualityLevel` en Android (§1) fallan **en silencio**, no por costo.

---

## 1. Veredictos accionables

🔴 **El Niagara Light Renderer no hace nada en Quest si no tocas un cvar.** En mobile forward shading (el pipeline por defecto en Quest), las "simple lights" que genera el Light Renderer de Niagara están deshabilitadas por defecto: `bMobileForwardParticleLights = false` (B: `ReadOnlyCVARCache.cpp:28`), controlado por el cvar `r.Mobile.Forward.EnableParticleLights` (default `false`, ini-driven vía `FShaderPlatformCachedIniValue`, B: `ReadOnlyCVARCache.cpp:47-51`). Si quieres usar el Light Renderer para simular que las partículas iluminan el entorno, debes agregar explícitamente a `Config/DefaultEngine.ini` (sección `[/Script/Engine.RendererSettings]` o equivalente por device profile):
```
r.Mobile.Forward.EnableParticleLights=1
```
(`r.Mobile.Forward.EnableLocalLights` ya está en `1` por defecto — B: `ReadOnlyCVARCache.cpp:27`, así que las luces "normales" colocadas en el nivel sí funcionan; el problema es específico de las luces generadas por partículas). La alternativa —pasar a Mobile Deferred Shading (`r.Mobile.ShadingPath=1`), donde `bSupportsSimpleLights = bDeferredShading || MobileForwardEnableParticleLights(...)` siempre es `true` (B: `MobileShadingRenderer.cpp:407`)— no se recomienda para este proyecto: Mobile Deferred añade el costo completo de un GBuffer, que en un proyecto fill-rate bound es contraproducente.

🔴 **La colisión/consulta de Distance Field global en GPU está bloqueada por código en Quest, no solo por configuración.** El nodo `QueryMeshDistanceFieldGPU` de la Data Interface `Collision Query` (`NiagaraDataInterfaceCollisionQuery`) depende del Global SDF ray-march provider, que exige explícitamente feature level SM5+:
```cpp
// the GSDF sampling is only supported with SM5+
if (!IsFeatureLevelSupported(Parameters.Platform, ERHIFeatureLevel::SM5))
    return false;
```
(B: `NiagaraShader\Private\NiagaraAsyncGpuTraceProviderGsdf.cpp:46-47`, repetido en runtime en `NiagaraAsyncGpuTraceProviderGsdf.cpp:102-103`: `if (Dispatcher->GetSceneInterface()->GetFeatureLevel() < ERHIFeatureLevel::SM5) return false;`). Quest corre en `ERHIFeatureLevel::ES3_1` (mobile), por debajo de SM5 → esta función es inalcanzable en el dispositivo, con o sin `r.GenerateMeshDistanceFields` activado. Esto es consistente con el hecho ya establecido en el proyecto de que Distance Fields no corren en Quest, pero aquí queda confirmado también del lado de Niagara específicamente. La consulta de profundidad de escena (**Depth Buffer**, no Distance Field) de la misma Data Interface sí funciona en mobile: el `NiagaraGpuComputeDispatch` conecta explícitamente un `MobileSceneTexturesUniformParams` cuando el shading path es mobile (B: `NiagaraGpuComputeDispatch.cpp:1172-1174`).

🟢 **GPU sim de partículas SÍ corre en Quest**, sujeto a tres condiciones que ya vienen activadas por defecto:
```cpp
bool FNiagaraUtilities::AllowGPUParticles()
{
    return GNiagaraAllowGPUParticles && GNiagaraAllowComputeShaders && GRHISupportsDrawIndirect;
}
```
(B: `NiagaraCommon.cpp:1047-1050`), con `fx.NiagaraAllowGPUParticles=1` y `fx.NiagaraAllowComputeShaders=1` por defecto (B: `NiagaraCommon.cpp:42-48`, `34-40`). En Quest con RHI Vulkan mobile, `GRHISupportsDrawIndirect` es `true`, así que no hay bloqueo de plataforma. El pipeline de dispatch de cómputo de Niagara está efectivamente cableado al mobile shading path (uniform buffers de mobile scene textures, ver arriba), confirmando que esto no es solo "en teoría compila" sino que el motor lo integra activamente en el frame mobile.

🔴 **`fx.Niagara.QualityLevel` está capado en Android por config, no por hardware.** `Engine/Config/Android/AndroidEngine.ini:120-121`:
```ini
fx.Niagara.QualityLevel.Min=0
fx.Niagara.QualityLevel.Max=1
```
Esto significa que en cualquier build Android (incluido Quest), solo los Effect Types/Quality Levels 0 (Low) y 1 (Medium) de Niagara están permitidos — los niveles 2 (High) y 3 (Epic) quedan clampeados automáticamente, sin importar lo que digas en tu Scalability.ini de proyecto. **Si alguno de tus emitters de Soul Charger tiene Scalability overrides que solo lo activan en High/Epic, ese emitter nunca corre en el Quest**, sin ningún error visible en PIE si estás en Windows editor (donde el quality level no está clampeado). Hay que probar explícitamente con `fx.Niagara.QualityLevel=1` en el editor, o mejor, en el dispositivo, para no descubrir esto tarde.

🟡 **Los Data Interfaces de Grid (Grid2D/Grid3D Collection) y las Data Interfaces de mesh (Static/Skeletal) no tienen guardas explícitas de feature level en el código Niagara** (B: `grep` de `ERHIFeatureLevel::SM5|ES3_1` en `NiagaraDataInterfaceGrid2DCollection.cpp`, `NiagaraDataInterfaceGrid3DCollection.cpp`, `NiagaraDataInterfaceStaticMesh.cpp` → sin resultados). Esto significa que **no están bloqueadas por Epic para mobile**, pero tampoco hay garantía documentada de que su patrón de acceso (texturas RW / UAV en compute shaders) sea barato en la arquitectura tile-based de Adreno. No encontré fuente oficial que las prohíba ni que las avale para Quest — usarlas exige tu propio profiling en dispositivo. No las necesitas para el efecto de "luz en el aire" de Soul Charger de todos modos.

🟢 **Ribbon Renderer y Mesh Renderer no tienen ninguna restricción de plataforma en código**: ambos devuelven `IsSimTargetSupported() → true` incondicionalmente (B: `NiagaraRibbonRendererProperties.h:220`, `NiagaraMeshRendererProperties.h:154`). Cualquier limitación de rendimiento en ellos es de presupuesto de fill-rate/vértices, no un bloqueo de Epic.

**Veredicto Turrell:** Niagara sigue siendo la herramienta correcta para "luz de color en el aire" en Quest, pero solo si se usa como **pocos sprites translúcidos grandes con gradiente radial pre-horneado en la textura**, no como nubes de miles de partículas pequeñas. El costo de overdraw es función del área de pantalla cubierta × capas superpuestas, no de la cantidad de partículas — así que 5 sprites grandes con blend aditivo cuestan menos que 500 sprites chicos que cubren la misma área. El Light Renderer de Niagara (para que las partículas iluminen superficies reales) **no** es la herramienta indicada por defecto en Quest: está apagado (ver punto 🔴 arriba), y aunque lo actives, con presupuesto fill-rate-bound cada luz dinámica adicional compite directamente con tu overdraw. Para simular que la luz "toca" el entorno, la alternativa más barata es un material emissive en las superficies cercanas modulado por el mismo valor de respiración que maneja al Niagara, no una luz real.

---

## 2. Detalle por pregunta

### 2.1 Features de Niagara no soportadas / con guardas en mobile

| Feature | Estado en Quest (ES3_1/mobile) | Fuente |
|---|---|---|
| GPU compute sim | Soportado, gateado por 3 cvars todos en `1`/`true` por defecto | B: `NiagaraCommon.cpp:1047-1050` |
| Distance Field collision (GPU global SDF query) | **Bloqueado por código**: exige SM5+ | B: `NiagaraAsyncGpuTraceProviderGsdf.cpp:46-47,102-103` |
| Depth Buffer collision (misma DI, distinta función) | Soportado, cableado a `MobileSceneTexturesUniformParams` | B: `NiagaraGpuComputeDispatch.cpp:1172-1174` |
| Ribbon Renderer | Sin guarda de plataforma en código | B: `NiagaraRibbonRendererProperties.h:220` |
| Mesh Renderer | Sin guarda de plataforma; soporta instanced stereo vía `VF_INSTANCED_STEREO_DECLARE_INPUT_BLOCK()` | B: `NiagaraMeshRendererProperties.h:154`, `NiagaraVertexFactories\Private\NiagaraMeshVertexFactory.cpp` / `Shaders\Private\NiagaraMeshVertexFactory.ush:70` |
| Light Renderer | Sin guarda de plataforma en la clase, pero **funcionalmente muted por defecto** en mobile forward | B: `ReadOnlyCVARCache.cpp:28`, `MobileShadingRenderer.cpp:407` |
| Grid2D/Grid3D Collection DI | Sin guarda explícita encontrada | B: ausencia de match en grep — no hay cita positiva ni negativa |
| Static/Skeletal Mesh DI (GPU) | Sin guarda explícita encontrada | B: ausencia de match en grep |
| `fx.Niagara.QualityLevel` en Android | Clampeado a rango `[0,1]` (Low/Medium) por config, no por el hardware | B: `Engine\Config\Android\AndroidEngine.ini:120-121` |

Nota importante: la documentación oficial de Epic (`Optimizing Niagara`, `Scalability and Best Practices for Niagara`, `Measuring Performance in Niagara`) **no menciona mobile, Android ni Quest en ningún punto verificado** (A: páginas fetcheadas completas, sin resultados sobre mobile). Es decir, en la superficie pública de docs, Epic no documenta qué le pasa a Niagara en mobile — la única fuente confiable es el código y los `.ini` de configuración de plataforma.

### 2.2 CPU vs GPU sim en Quest

(A) Documentación oficial — *Scalability and Best Practices for Niagara* (https://dev.epicgames.com/documentation/en-us/unreal-engine/scalability-and-best-practices-for-niagara), sección "GPU vs CPU":
> "Particle scripts have the largest opportunity for parallelization, so they benefit the most from targeting the GPU, and in most cases GPU sims are more performant, and allow for a greater number of particles."

> "For emitters with a small number of particles a CPU sim may be better suited, as GPU resources cannot be divided as granularly."

> "This is especially common for platforms that have less GPU memory like mobile."

(B) Código — GPU sim está permitido en Quest si `fx.NiagaraAllowGPUParticles` (default `1`), `fx.NiagaraAllowComputeShaders` (default `1`) y `GRHISupportsDrawIndirect` (true en Vulkan mobile) se cumplen (`NiagaraCommon.cpp:34-50,1047-1050`).

**No se encontró ningún límite de partículas documentado oficialmente por Meta ni por Epic para Quest** — se buscó explícitamente en `developers.meta.com` y en la documentación de Epic sobre mobile/rendering/performance guidelines, sin resultado. Cualquier número que circule ("Quest soporta X mil partículas") es folclore sin fuente citable (C).

**Para Soul Charger específicamente** (pocos emitters grandes, dirigidos por un solo float de respiración, no miles de partículas): la ganancia de paralelismo del GPU sim no aplica — con pocas partículas "GPU resources cannot be divided as granularly" (cita arriba). Además, cada dispatch de cómputo GPU en una GPU tile-based (Adreno del Quest 3) implica una transición render→compute→render que puede forzar flush de tile, algo que no aparece cuantificado en ninguna fuente oficial que hayamos encontrado (C, razonamiento propio sobre arquitectura TBDR, no verificado con cifras). Dado que el proyecto es fill-rate bound y no particle-count bound, **CPU sim es la opción más simple y predecible** para los emitters "hero" de luz ambiental; reservar GPU sim solo si en el futuro se necesitan efectivamente miles de partículas (chispas, polvo), no para los volúmenes de luz Turrell.

### 2.3 Pasar el parámetro de respiración de Blueprint a Niagara

Mecanismo recomendado: `UNiagaraComponent::SetVariableFloat(FName, float)` (Blueprint-expuesto también como `SetNiagaraVariableFloat(FString, float)`).

(B) Implementación real (`NiagaraComponent.cpp:2864-2883`):
```cpp
void UNiagaraComponent::SetVariableFloat(FName InVariableName, float InValue)
{
    const FNiagaraVariable VariableDesc(FNiagaraTypeDefinition::GetFloatDef(), InVariableName);
    if (SystemInstanceController.IsValid())
    {
        SystemInstanceController->SetVariable_Deferred(InVariableName, InValue);
    }
    else
    {
        OverrideParameters.SetParameterValue(InValue, VariableDesc, true);
    }
    ...
}
```

Costo real: `FNiagaraParameterStore::SetParameterValue<T>` hace un `IndexOf(Param)` (lookup del offset del parámetro) y, si existe, un `FMemory::Memcpy` de `sizeof(T)` bytes (B: `NiagaraParameterStore.h:562-579`). Para un `float` esto es un lookup + copia de 4 bytes — trivialmente barato, se puede llamar todos los frames sin preocupación de presupuesto.

🔴 **Trampa verificada en código**: el parámetro `bAdd` se pasa como `true` en la llamada de `SetVariableFloat` (`NiagaraComponent.cpp:2873`: `OverrideParameters.SetParameterValue(InValue, VariableDesc, true)`). Mirando la implementación (`NiagaraParameterStore.h:572-589`): si `IndexOf(Param)` no encuentra el parámetro (por ejemplo, porque el nombre tiene un typo o no coincide exactamente con el User Parameter expuesto en el sistema Niagara, incluyendo el prefijo `User.`), y `bAdd == true`, el código **agrega un parámetro nuevo silenciosamente** en vez de fallar:
```cpp
int32 Offset = IndexOf(Param);
if (Offset != INDEX_NONE) { /* memcpy normal */ }
else if (bAdd) { AddParameter(Param, ...); /* memcpy al nuevo offset */ }
```
Esto significa que si tu Blueprint llama `SetNiagaraVariableFloat("BreathValue", X)` pero el User Parameter del sistema en realidad se llama `User.BreathValue`, no vas a ver ningún error ni warning — simplemente se crea un parámetro huérfano que nadie lee, y tu emitter nunca recibe el valor real. Verificar el nombre exacto (incluyendo el prefijo `User.`) contra el Parameters panel del sistema Niagara es la única defensa; no hay validación automática en este camino.

Nota de menor confianza (no verificado en profundidad): cuando el componente ya está activo, la llamada pasa por `SetVariable_Deferred` en lugar del camino inmediato de arriba — no se localizó la definición completa de ese método dentro del tiempo de esta investigación, así que no puedo confirmar con cita exacta si hay latencia de un frame entre la llamada desde Blueprint y que el valor se refleje en la simulación. Recomiendo verificarlo empíricamente (ej. con un `PrintString` del valor leído dentro del script de Niagara vs. el frame en que se llamó desde Blueprint) antes de asumir que es same-frame.

### 2.4 Fill-rate: reglas oficiales sobre overdraw de partículas

(A) Meta, *Basic Optimization Workflow for Apps* (https://developers.meta.com/horizon/documentation/unreal/po-perf-opt-mobile/) — método oficial para diagnosticar fill-bound:
> "This can be done by setting the app's render scale to something small, like 0.01. This will cause fewer fragments to be rendered, but retain the scene complexity."
> "If performance improves, the app is likely fragment-bound (also commonly called fill-bound)."
> "If an app is fill-bound, one or more of its shaders need to be optimized. Pixel complexity tends to be the main issue for fill-bound shaders."

(A) Meta, blog *Translucent vs Masked Rendering in Real-Time Applications* (https://developers.meta.com/horizon/blog/translucent-vs-masked-rendering-in-real-time-applications/):
> "The numbers in the table indicate that translucent rendering adds almost 80% more GPU time per frame when compared to masked rendering."

Este dato es del contexto de renderizado de avatares (Home 2.0), no de VFX, pero la razón estructural que da el artículo (paso de Custom Depth + paso de Translucencia + resolve de Scene Depth, contra un Early Z + Base Pass más simple para masked) es un argumento de arquitectura que se aplica igual a sprites translúcidos de Niagara: cada capa translúcida adicional repite el costo completo de shading, no hay early-out por profundidad.

(A) Herramienta oficial de Meta para medir overdraw real en el dispositivo: **RenderDoc Meta Fork** (https://developers.meta.com/horizon/documentation/unreal/ts-renderdoc-for-oculus/ y https://developers.meta.com/horizon/documentation/unreal/ts-renderdoc-renderstage/):
> "RenderDoc Meta Fork can perform a tile-level render stage trace for a single frame of an app on a connected Meta Quest, with results viewable in the Tile Timeline view. It can also perform a draw-call trace that collects up to 59 low-level metrics pertaining to each individual draw-call in the capture."

No encontré, en ninguna fuente oficial, una regla numérica específica de Epic o Meta tipo "no superar X% de overdraw" o "no más de Y partículas grandes en pantalla" — la guía oficial es cualitativa (probar con render scale bajo, medir con RenderDoc Meta Fork) más que prescriptiva con números fijos.

El modo `viewmode shadercomplexity` / quad overdraw del editor de Unreal existe (A parcial: confirmado en Unreal docs de viewport modes, aunque no verifiqué si funciona igual en mobile preview o en el dispositivo real) — para Quest, la fuente oficial y confiable es RenderDoc Meta Fork sobre hardware real, no el viewmode del editor.

### 2.5 Veredicto Turrell — ver sección 1 (resumen ejecutivo).

Complemento: dado que Volumetric Fog no está soportado en Quest (hecho ya establecido en el proyecto), y que el Light Renderer de Niagara está apagado por defecto en mobile forward (🔴 arriba), la única vía funcional y barata para "luz de color en el aire" con Niagara en Quest es:
1. Sprite Renderer con blend translúcido/aditivo, textura de gradiente radial pre-horneada (sin cálculo de falloff en shader).
2. Pocos emitters grandes en vez de muchos chicos — el costo es por área de pantalla cubierta, no por cantidad de partículas.
3. CPU sim (ver 2.2) para mantener el control determinístico sobre la respuesta a la respiración sin el overhead de un dispatch de cómputo GPU para un puñado de partículas.
4. Si se necesita que la luz "toque" superficies cercanas, resolverlo con material emissive baked/modulado por el mismo valor de respiración — no con el Light Renderer.

### 2.6 Instanced Stereo / Multi-View en móvil

(B) Los vertex factories de Niagara usan el mecanismo estándar del motor para instanced stereo:
- Mesh: declara explícitamente el bloque de instanced stereo — `VF_INSTANCED_STEREO_DECLARE_INPUT_BLOCK()` (`Shaders\Private\NiagaraMeshVertexFactory.ush:70`).
- Sprite: no declara el macro directamente, pero incluye `/Engine/Private/VertexFactoryCommon.ush` y `/Engine/Private/ParticleVertexFactoryCommon.ush` (`Shaders\Private\NiagaraSpriteVertexFactory.ush:8-9`), que es donde el motor resuelve instanced stereo/multi-view de forma genérica para cualquier vertex factory.

(B) Costo de duplicación por ojo — confirmado en el shader de generación de draw-indirect-args para GPU emitters:
```cpp
const bool bInstancedStereo = (Flags & FLAG_INSTANCED_STEREO) != 0;
...
if (bInstancedStereo)
{
    InstanceCount *= 2;
}
```
(B: `Shaders\Private\NiagaraDrawIndirectArgsGen.usf:37,50-53`). Es decir, el número de instancias del draw call se duplica explícitamente cuando el instanced stereo está activo — el costo de vértices/fragmentos se paga dos veces (una por ojo), igual que con cualquier geometría normal en un pipeline multi-view. No hay una "duplicación extra" propia de Niagara más allá de esto.

(B) La **simulación** (el compute dispatch que actualiza los buffers de partículas) **no se duplica por ojo**: usa solo la vista `[0]` para su view-uniform-buffer:
```cpp
DispatchParameters->View = SimulationSceneViews[0].ViewUniformBuffer;
```
(B: `NiagaraGpuComputeDispatch.cpp:1728`). Esto confirma que el update de partículas corre una sola vez por frame, independientemente de que haya 1 o 2 vistas — solo el paso de render (dibujado) se duplica vía instanced stereo/multi-view. No se encontró documentación oficial (A) que describa este comportamiento explícitamente para Niagara; es una confirmación exclusivamente de código.

---

## 3. Tabla de folclore

| Creencia común | Verdad verificada | Fuente |
|---|---|---|
| "GPU particles no corren en Quest / mobile" | Sí corren, siempre que `fx.NiagaraAllowGPUParticles=1` (default) y la RHI soporte draw indirect (Vulkan mobile: sí) | B: `NiagaraCommon.cpp:1047-1050` |
| "El Niagara Light Renderer sirve out-of-the-box para simular luz en el aire estilo Turrell en Quest" | Por defecto está desactivado en mobile forward: `r.Mobile.Forward.EnableParticleLights=false` | B: `ReadOnlyCVARCache.cpp:28`, `MobileShadingRenderer.cpp:407` |
| "Las Data Interfaces de Distance Field funcionan en cualquier lado si generás el DF" | El proveedor GPU de ray-march contra el SDF global exige SM5+ explícitamente; Quest corre en ES3_1, por debajo del umbral | B: `NiagaraAsyncGpuTraceProviderGsdf.cpp:46-47,102-103` |
| "El viewmode Shader Complexity / Quad Overdraw del editor te dice el overdraw real en el Quest" | No hay confirmación oficial de que replique el comportamiento del dispositivo; la herramienta oficial de Meta para medir overdraw real en hardware es RenderDoc Meta Fork (Tile Timeline) | C (primera mitad sin fuente) / A (RenderDoc Meta Fork sí documentado) |
| "Hay un número oficial de partículas máximas para Quest documentado por Epic o Meta" | No se encontró ningún límite numérico oficial en ninguna de las dos fuentes tras búsqueda dirigida | Ausencia de fuente — no citable como C tampoco, simplemente no existe |
| "Simular en GPU duplica el costo de simulación por cada ojo en VR" | Falso: la simulación corre una sola vez por frame usando `Views[0]`; solo el dibujado (vertex+fragment) se duplica vía instanced stereo | B: `NiagaraGpuComputeDispatch.cpp:1728`; `NiagaraDrawIndirectArgsGen.usf:50-53` |
| "El Quality Level de Niagara en Android es el mismo rango que en PC (0-3/4)" | Está clampeado por config a `[0,1]` (Low/Medium) en `AndroidEngine.ini`, independientemente de lo que definas en tu Scalability.ini de proyecto | B: `Engine\Config\Android\AndroidEngine.ini:120-121` |

---

## 4. Fuentes citadas

**(A) Documentación oficial:**
- Epic — Scalability and Best Practices for Niagara: https://dev.epicgames.com/documentation/en-us/unreal-engine/scalability-and-best-practices-for-niagara
- Epic — Optimizing Niagara: https://dev.epicgames.com/documentation/en-us/unreal-engine/optimizing-niagara (landing page, sin contenido específico de mobile verificable)
- Epic — Measuring Performance in Niagara: https://dev.epicgames.com/documentation/unreal-engine/measuring-performance-in-niagara
- Meta — Basic Optimization Workflow for Apps: https://developers.meta.com/horizon/documentation/unreal/po-perf-opt-mobile/
- Meta — Use RenderDoc Meta Fork for GPU Profiling: https://developers.meta.com/horizon/documentation/unreal/ts-renderdoc-for-oculus/
- Meta — Performing a Render Stage Trace: https://developers.meta.com/horizon/documentation/unreal/ts-renderdoc-renderstage/
- Meta — blog: Translucent vs Masked Rendering in Real-Time Applications: https://developers.meta.com/horizon/blog/translucent-vs-masked-rendering-in-real-time-applications/
- Meta — Performance Settings for Unreal Engine: https://developers.meta.com/horizon/documentation/unreal/unreal-sample-performance-settings/ (verificado: sin contenido de Niagara/VFX)

**(B) Código del motor (UE 5.8, `C:\Program Files\Epic Games\UE_5.8`):**
- `Engine\Plugins\FX\Niagara\Source\Niagara\Private\NiagaraCommon.cpp`
- `Engine\Plugins\FX\Niagara\Source\Niagara\Private\NiagaraGpuComputeDispatch.cpp`
- `Engine\Plugins\FX\Niagara\Source\Niagara\Private\NiagaraComponent.cpp`
- `Engine\Plugins\FX\Niagara\Source\Niagara\Public\NiagaraParameterStore.h`
- `Engine\Plugins\FX\Niagara\Source\Niagara\Private\NiagaraDataInterfaceCollisionQuery.cpp` / `Classes\NiagaraDataInterfaceCollisionQuery.h`
- `Engine\Plugins\FX\Niagara\Source\NiagaraShader\Private\NiagaraAsyncGpuTraceProviderGsdf.cpp`
- `Engine\Plugins\FX\Niagara\Source\Niagara\Public\NiagaraLightRendererProperties.h`
- `Engine\Plugins\FX\Niagara\Source\Niagara\Public\NiagaraRibbonRendererProperties.h`
- `Engine\Plugins\FX\Niagara\Source\Niagara\Public\NiagaraMeshRendererProperties.h`
- `Engine\Plugins\FX\Niagara\Shaders\Private\NiagaraMeshVertexFactory.ush`
- `Engine\Plugins\FX\Niagara\Shaders\Private\NiagaraSpriteVertexFactory.ush`
- `Engine\Plugins\FX\Niagara\Shaders\Private\NiagaraDrawIndirectArgsGen.usf`
- `Engine\Source\Runtime\RenderCore\Private\ReadOnlyCVARCache.cpp` / `Public\ReadOnlyCVARCache.h`
- `Engine\Source\Runtime\RenderCore\Public\RenderUtils.h`
- `Engine\Source\Runtime\Renderer\Private\MobileShadingRenderer.cpp`
- `Engine\Source\Runtime\Renderer\Private\MobileBasePass.cpp`
- `Engine\Config\Android\AndroidEngine.ini`
- `Engine\Config\BaseScalability.ini`
