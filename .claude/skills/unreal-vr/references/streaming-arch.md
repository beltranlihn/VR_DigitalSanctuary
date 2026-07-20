# Streaming, GameInstance y arquitectura — UE 5.8 / Quest standalone

> **[DOC]** oficial · **[SRC]** código UE 5.8 en `C:\Program Files\Epic Games\UE_5.8` · **[FOLCLORE]** sin fuente. Investigado 17/07/2026.
> 🔴 **En este tema el código NO es un fallback: es la fuente primaria.** Epic no documenta casi nada, y **por eso el folclore prolifera** — no había texto oficial que lo contradijera.

---

# 🔴 1. EL GAMEPLAY MESSAGE ROUTER **NO EXISTE EN EL MOTOR**
> [SRC] `find UE_5.8/Engine -iname "*GameplayMessage*"` → **solo** `AsyncMessageSystem/.../AsyncGameplayMessageSystem.cpp`. **No hay `GameplayMessageRouter` ni `UGameplayMessageSubsystem` en 5.8 (ni en 5.5/5.6).**

**Es un plugin del PROYECTO Lyra, no del motor.** Adoptarlo = vendorizar código del sample, con **cero documentación de Epic y cero soporte**. (La investigación anterior dijo "no tiene página de doc" — se quedó corta: **tampoco se distribuye**.)

**La alternativa que Epic sí embarca:** `AsyncMessageSystem` — direccionado por tags, desacoplado, con nodos BP (*Start Listening for Async Message*, *Queue Async Message for Broadcast*). Pero:
> [SRC] `AsyncMessageSystem.uplugin`: `"VersionName": "0.1"`, `"IsExperimentalVersion": true`, `"EnabledByDefault": false`, `"DocsURL": ""`
**Versión 0.1, Experimental, sin URL de docs.** Para una obra que tiene que estrenar, mala apuesta.

**Lo único documentado:** [Blueprint Communications](https://dev.epicgames.com/documentation/unreal-engine/blueprint-communications-in-unreal-engine) — Direct, Casting, **Event Dispatchers**, Interfaces.
⚠ **Honestidad:** los dispatchers son *"a one to many relationship"* pero **NO son un bus** — el listener igual necesita una referencia al emisor. **Epic no documenta NINGÚN bus de eventos global desacoplado.** Ese hueco es real, y es exactamente por eso que el router de Lyra proliferó.

**→ DECISIÓN: cortar el router.** Tenemos **un** FlowDirector y **9** beats. Un bus global resuelve un problema que no tenemos. **Dispatchers multicast en el FlowDirector del nivel persistente**; todo lo demás ya puede alcanzarlo.

---

# 🔴 2. Level Instances: nuestra premisa era FALSA (pero la decisión se salva)
**Lo que creíamos:** *"no están garantizados cargados en BeginPlay en builds empaquetados — funciona en PIE y falla silencioso al empaquetar"*.

**Refutado en las dos mitades:**
- **"Falla al empaquetar"** → [SRC] `LevelInstanceActorImpl.cpp:82-90`: en build cocinado `IsLoadingEnabled()` devuelve `return true;` **incondicionalmente**. El issue tracker de Epic ([UE-295514](https://issues.unrealengine.com/issue/UE-295514)) apunta al revés: PIE roto, *"It also works correctly in Stand Alone."*
- **"No cargado en BeginPlay"** → **TRUE, pero en TODOS los builds, PIE incluido.** [SRC] `LevelInstanceSubsystem.cpp:210` `RequestLoadLevelInstance` solo **encola**; se drena desde `UWorld::Tick` ([SRC] `World.cpp:4893`, `LevelTick.cpp:1865`). **El contenido aparece frames DESPUÉS del BeginPlay, siempre. Es diseño, no bug.**

## 🔥 Y el remate: rechazamos el envoltorio y nos quedamos con el mismo motor
> [SRC] `LevelInstanceLevelStreaming.cpp:432`:
> ```cpp
> ULevelStreamingLevelInstance* LevelStreaming =
>     Cast<ULevelStreamingLevelInstance>(ULevelStreamingDynamic::LoadLevelInstance(Params, bOutSuccess));
> ```
**`ALevelInstance` carga su nivel llamando exactamente al mismo `LoadLevelInstance` que elegimos en su lugar. Son la misma ruta de código.** El razonamiento "los Level Instances son async e inseguros en BeginPlay, así que uso LoadLevelInstance" **se refuta solo**: `LoadLevelInstance` es *más* async, no menos.

⚠ **De dónde viene el folclore:** Unreal llama **"Level Instance" a dos cosas sin relación** — el actor `ALevelInstance` y el nodo de streaming `LoadLevelInstance`.

## ✅ La razón REAL y defendible para no usar `ALevelInstance`: encaje, no fiabilidad
1. **Nuestro mundo no es World Partition.** [SRC] `LevelInstanceActor.cpp:32` `DesiredRuntimeBehavior` default `Partitioned` y es `#if WITH_EDITORONLY_DATA`; toda la resolución `Partitioned` vive en el sistema ActorDesc, **que solo existe en mundos WP**.
   > [DOC] "Level instances **do not automatically have streaming management** or streaming strategies **outside of a World Partition main world**." — [Level Instancing](https://dev.epicgames.com/documentation/en-us/unreal-engine/level-instancing-in-unreal-engine)
2. [DOC] Los Level Instances están pensados para **repetición** ("repeated across your world"). Nueve espacios únicos hechos a mano son lo contrario.
3. Queremos transiciones **explícitas, ordenadas, dirigidas**. `ALevelInstance` da carga por colocación.

**→ Mantener la decisión. Cambiar el argumento.**

---

# 🔴 3. `LoadStreamLevel`: el fallo silencioso, confirmado en el código
> [SRC] `LevelStreaming.cpp:252-255` — si el nivel no está registrado:
> ```cpp
> else { Response.FinishAndTriggerIf(true, LatentInfo.ExecutionFunction, ...); }
> ```
> **Dispara el pin "Completed" como si hubiera funcionado.** `FindAndCacheLevelStreamingObject` devuelve null **sin ningún warning** (`:271-296`); `ActivateLevel` **no tiene rama else** (`:330`). **Ningún log, a ninguna verbosidad.**

**Nuestro diagnóstico de aquella noche era exactamente correcto.**

## Pero `LoadLevelInstance` tiene dos costos que no sabíamos
> [DOC] "The level to be loaded **does not have to be in the persistent map's Levels list**" · ⚠ "to ensure that the .umap **does get packaged**, please be sure to **include the .umap in your Packaging Settings**" — [API](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Engine/ULevelStreamingDynamic/LoadLevelInstance)

🚨 **ACCIÓN: registrar los 9 mapas en Project Settings → Packaging → *List of Maps to Include in a Packaged Build*.** Sin registro **nada más los mete en el APK**. **Este es el fallo-silencioso-al-empaquetar REAL** — la verdad detrás del folclore del punto 2.

**1. Nunca puede bloquear.** [SRC] `LevelStreaming.cpp:2782` `bShouldBlockOnLoad = false` **hardcodeado**. Bueno para VR, pero **hay que manejar las transiciones por eventos de completado, nunca asumir "después de N frames"**.
> [SRC] `LevelStreaming.h:633-647` delegates `BlueprintAssignable`. 🎯 **Usar `OnLevelShown`** ("added to the world and is **visible**") como señal de fade-in — **NO `OnLevelLoaded`** (paquete cargado ≠ visible).

**2. 🔴 Cada llamada crea un PAQUETE NUEVO.**
> [SRC] `LevelStreaming.cpp:2828-2831`:
> ```cpp
> LevelPackageNameStrBuilder.Append(TEXT("_LevelInstance_"));
> LevelPackageNameStrBuilder.Append(FString::FromInt(++UniqueLevelInstanceId));
> ```
> `UniqueLevelInstanceId` es un static que **nunca se resetea** (`:189`).
**Llamarlo dos veces sobre `hub` → `hub_LevelInstance_1` Y `hub_LevelInstance_2`, dos copias vivas. Volver al hub varias veces LEAKEA niveles.**

🚨 **ACCIÓN: pasar SIEMPRE `OptionalLevelNameOverride`** (ej. `"Stage3_Inst"`). Solo entonces corre el test de unicidad ([SRC] `:2715` `bNeedsUniqueTest = Params.OptionalLevelNameOverride != nullptr`) → nombres deterministas, reuso seguro, y un **`UE_LOG(..., Error, "LoadLevelInstance called with a name that already exists...")`** ruidoso ([SRC] `:2757`) en vez de duplicación silenciosa. Además es lo que `UnloadStreamLevel` usa como clave.
**Y usar rutas de paquete completas** — [DOC] los nombres cortos *"will force very slow search on disk"*.
**Descargar con** `SetIsRequestingUnloadAndRemoval(true)` [SRC] `LevelStreaming.h:488` (`BlueprintCallable`).

---

# 🔴 4. El hitch de descarga ES un GC forzado, y viene ENCENDIDO
> [SRC] `CoreSettings.cpp:25` `int32 GLevelStreamingForceGCAfterLevelStreamedOut = 1;`
> [SRC] `:128-133` descripción de Epic: *"Whether to force a GC after levels are streamed out to instantly reclaim the memory **at the expensive of a hitch**."* → consumido en `World.cpp:5185` → `ForceGarbageCollection(true)`.

**Ese cvar contesta "¿se libera la memoria?" y "¿por qué hitchea?" a la vez: descargar SÍ libera pronto PORQUE el motor fuerza un GC — y ese GC ES el hitch. Es un dial entre las dos cosas; no se pueden tener ambas.**
⚠ **Epic NUNCA publica su default.** No está en la Console Variables Reference. **[SRC] es la única forma de saber que es `1`.**
⚠ Apagarlo trae resurrección de actores: [DOC Actor Lifecycle] *"if `s.ForceGCAfterLevelStreamedOut` is false and a sublevel is quickly reloaded then an Actor's EndPlay would be called, but the actor may be **'resurrected'**… along with its local variables that were **not re-initialized**"* — clase de bug horrible para una obra donde se puede repetir una etapa.

## 🔴 El número que más nos importa
> [SRC] `Engine/Config/BaseEngine.ini:1710-1755`:
> ```ini
> [/Script/Engine.StreamingSettings]
> s.UseBackgroundLevelStreaming=True
> s.LevelStreamingActorsUpdateTimeLimit = 5.0
> s.LevelStreamingComponentsRegistrationGranularity = 10
> s.UnregisterComponentsTimeLimit = 1.0
> s.AsyncLoadingThreadEnabled=True
> [/Script/Engine.GarbageCollectionSettings]
> gc.TimeBetweenPurgingPendingKillObjects=61.1
> ```

**5.0 ms de registro de actores por frame, contra un presupuesto de 13.9 ms = 36% del frame, por defecto.** Es un frame perdido garantizado en Quest. **Epic embarca ese default para juegos de pantalla a 30/60 fps; nadie lo tuneó para VR, y Epic no publica guía de VR sobre esto.**
→ **Bajarlo a 1–2 ms** y aceptar más frames de carga — igual la estamos escondiendo detrás del fade. `s.UnregisterComponentsTimeLimit = 1.0` es el gemelo del lado de descarga.
→ `gc.TimeBetweenPurgingPendingKillObjects=61.1` = un GC periódico **cada minuto pase lo que pase** → ~15 en nuestros 15 min.
⚠ **`s.UseBackgroundLevelStreaming`**: [SRC] `CoreSettings.cpp:44` *"If this is 0, **all level loading will block the game thread**"*. **Dejarlo True.**

⚠ **El tutorial de Epic nos manda hacer lo incorrecto para VR:** [DOC] *"Toggle **Make Visible After Load** and **Should Block on Load** to true"* — sin ninguna discusión de hitch. Es conveniencia de tutorial. **Toda** la documentación oficial de block-on-load es el comentario de la propiedad ([SRC] `LevelStreaming.h:304` *"Whether we want to force a blocking load"*). El costo **nunca se cuantifica en ningún lado**.

⚠ **El GC incremental es la cura que Epic te dice que no uses:** [DOC](https://dev.epicgames.com/documentation/unreal-engine/incremental-garbage-collection-in-unreal-engine) *"We recommend enabling incremental reachability in **single-threaded builds only** (for example, dedicated servers)."* · *"Incremental reachability is **not fully thread safe**…can result in the object being **garbage collected prematurely**."* **No tocar.**

## Esconder el hitch: bendecido, con una ventaja que el fade sphere no tiene
> [DOC] "you can use a texture as a **loading screen** to ease transitions between levels in XR experiences" — [OpenXR Loading Screens 5.8](https://dev.epicgames.com/documentation/en-us/unreal-engine/openxr-loading-screens-in-unreal-engine) (nodos BP *Set/Show/Hide Loading Screen*, demostrado **con level streaming**). ⚠ "Media playback through Media Framework is **not** currently supported with Loading Screens in XR."
> [DOC Meta] "The engine splash screen is **Blueprint-enabled** and intended to **mask loading levels**… that temporarily suspend rendering head-tracked graphics." — [Splash Screen](https://developers.meta.com/horizon/documentation/unreal/unreal-loading-screens/)

**Nuestro fade sphere es correcto** y el razonamiento del hueco estéreo también. **Pero un loading screen de compositor mantiene el head tracking vivo AUNQUE la app deje de enviar frames. Un fade sphere es un actor del mundo: si el game thread se traba, se traba con todo.**
→ **Considerar los dos: fade sphere para la transición artística, OpenXR loading screen como red de seguridad para el pico del GC forzado.**

---

# 🔴 5. Subsystems en Blueprint: NUESTRA PREMISA ERA CORRECTA
> [SRC] grep de `Blueprintable` en `Runtime/Engine/Public/Subsystems/` → **cero matches**. `USubsystem` = `UCLASS(Abstract, MinimalAPI)`; `UGameInstanceSubsystem` = `UCLASS(Abstract, Within=GameInstance, MinimalAPI)`.
> [SRC] `Kismet2.cpp:1080` — el gate autoritativo:
> ```cpp
> const bool bIsValidClass = Class->GetBoolMetaDataHierarchical(FBlueprintMetadata::MD_IsBlueprintBase)
>     || (Class == UObject::StaticClass()) || (Class == USceneComponent::StaticClass() || ...) || bIsBPGC;
> ```
> `MD_IsBlueprintBase` viene de `Blueprintable`; **ningún subsystem lo setea**. Y el escape de `UObject` es **igualdad exacta**, no `IsChildOf` → "podés hacer un Blueprint de Object" **NO se propaga** a `UGameInstanceSubsystem`.

**Blueprint solo consume:** `SubsystemBlueprintLibrary.h` expone `GetGameInstanceSubsystem` como `BlueprintPure`.
⚠ **Epic no lo dice en ningún lado.** La página de Programming Subsystems solo dice *"Subsystems are automatically exposed to Blueprints"* — eso es **acceso, no creación**.

## ✅ Y el GameInstance es la respuesta DOCUMENTADA, no un parche
> [SRC] `GameInstance.h:150` `UCLASS(config=Game, transient, BlueprintType, **Blueprintable**, MinimalAPI)`
> [DOC] **"Anything that you want to persist between level loads should live in the game instance."** · *"The game instance is instantiated on engine launch and remains active until the engine shuts down."* — [Gameplay Framework](https://dev.epicgames.com/documentation/en-us/unreal-engine/gameplay-framework-in-unreal-engine)

**CurrentStage, flags, el retrato de datos y el UObject del OSC van ahí por el libro.**
> [SRC] `OSC.uplugin`: sin restricciones de plataforma, v2.0, **no beta** → compila para Android.

---

# 6. World Partition vs streaming tradicional
**Usar streaming tradicional. Pero el argumento habitual es un no-sequitur.**
⚠ **"World Composition está deprecado → usá WP en vez de sublevels" es FALSO**: **World Composition ≠ Level Streaming.** Solo el primero está deprecado. La página de Level Streaming está viva y vigente para 5.8.
⚠ **WP en móvil/Quest: Epic está en silencio en las dos direcciones.** Las docs de WP nunca mencionan móvil/Android/Quest; las de móvil nunca mencionan WP. **Nadie puede decir honestamente que Epic soporta o prohíbe WP en Quest.** El caso en contra para 9 espacios curados es **inferencia del propósito**, no una prohibición documentada. Decirlo así si alguien lo cuestiona.
⚠ **No hay ruta documentada para des-convertir un mapa de WP.** Solo `Convert Level` hacia WP. **Si queremos un persistente genuinamente no-WP, crearlo así — no intentar despojarlo.**

---

# 7. Persistente vs sublevels: qué va dónde
🔴 **Casi todo INDOCUMENTADO — el hueco más grande de esta investigación.**
La **única** regla dura que Epic enuncia: > [DOC] "All **Level Streaming Volumes** must exist in the persistent Level." (no los usamos).
**Todo lo demás es solo por ejemplo.** ⚠ **El consejo universal "poné el pawn/GameMode/managers en el persistente" es FOLCLORE — Epic nunca lo dice.** Nuestro layout (pawn + fade sphere + FlowDirector) coincide con ese folclore y casi seguro está bien; **pero no se puede citar a Epic**.
⚠ **Bandera de versión:** el texto de Always Loaded / persistente es **byte-idéntico** entre la página de 4.27 y la de "5.8". El badge es un re-tag, no una reescritura. Y [Managing Multiple Levels](https://dev.epicgames.com/documentation/en-us/unreal-engine/managing-multiple-levels-in-unreal-engine) se auto-identifica como para *"Unreal Engine 4 legacy projects"*. **Estamos en una ruta soportada pero documentada como legacy.** Aceptable, sabiéndolo.

## 🔴 La regla práctica que sí sale del código
> [SRC] `Actor.cpp:755-761` `ClearCrossLevelReferences()` — si el root está attacheado a un actor de **otro nivel**, hace `DetachFromComponent`. Llamado desde `ULevel::PreSave` ([SRC] `Level.cpp:1322`).

**→ NUNCA attachear un actor de sublevel al pawn/cámara VR. Se desattachea solo al guardar.** Nuestro fade sphere vive en el persistente attacheado a una cámara del persistente → **está bien**. **El contenido de etapa le PREGUNTA al FlowDirector, nunca al revés.**
> [DOC] Por qué las refs muertas no crashean: *"When an AActor… is destroyed…, all references to it that are **visible to the reflection system** … are automatically nulled."* — **solo** para refs marcadas `UPROPERTY` (automático en BP). **→ null-check siempre al cruzar un borde de nivel.**
⚠ Que las refs duras entre niveles sean problemáticas: **Epic no lo documenta en ningún lado** (revisadas 5 páginas). Es folclore.

---

# 8. Data Asset para el flujo
> [DOC] "A **Data Asset** is an asset that stores data related to a particular system in an instance of its class." · "A **Primary** Data Asset … has asset bundle support, which allows it to be manually loaded/unloaded from the Asset Manager."
⚠ **Epic no publica comparación Data Asset vs Data Table, ni guía de usar Data Assets para declarar un flujo.** Ese patrón es folclore — bueno, pero sin cita.
**→ `UDataAsset` plano (subclase BP) con un array ordenado de structs de beat. NO hace falta PrimaryDataAsset** — su valor es el load/unload de bundles por Asset Manager, y nosotros cargamos niveles explícitamente por nombre.

🚨 **Lo crítico:** los 9 mapas van como **`TSoftObjectPtr<UWorld>`**, NO como refs duras.
> [DOC] "as objects are loaded and instantiated **the hard referenced assets are loaded too**. Careful consideration needs to happen or your **memory footprint can balloon**."
**Una ref dura del asset de flujo a las 9 etapas mete TODAS las etapas en RAM a la vez** — exactamente el fallo de 5.75 GiB que queremos evitar. Usar `LoadLevelInstanceBySoftObjectPtr`.

---

# 9. Gameplay Tags — sí, y sin GAS
> [SRC] `GameplayTags` es un **módulo Runtime del core** (`Engine/Source/Runtime/GameplayTags`), **no un plugin**. `GameplayTags.Build.cs` deps: Core, CoreUObject, Engine, DeveloperSettings, Projects, NetCore, Json, JsonUtilities — **cero referencia a GAS**. (La dependencia va al revés: GAS depende de Tags.)
> [DOC] "**Gameplay Tags** are user-defined strings that function as conceptual, **hierarchical** labels."
**Para 9 beats + flags: Project Settings** (→ `DefaultGameplayTags.ini`). Las Tag Tables se ganan su lugar con sets grandes manejados por diseñadores en planilla. No es nuestro caso.

## 🔴 CORRECCIÓN: teníamos la dirección del matching al revés
> [DOC] `MatchesTag`: *"expanding out parent tags — **`"A.1".MatchesTag("A")` will return True, `"A".MatchesTag("A.1")` will return False**"*

**El matching se expande hacia los PADRES.** `Flow.Stage.Three`.MatchesTag(`Flow.Stage`) → **True**. `Flow.Stage`.MatchesTag(`Flow.Stage.Three`) → **False**.
**→ Diseñar la jerarquía para que el tag ESPECÍFICO sea el que se testea.**
**El valor real de los tags no es el router (que no existe): es que dejan al FlowDirector despachar sin un switch monolítico.**

---

# 10. Seamless travel / OpenLevel
**Ni considerarlo. Mantener streaming.**
- [DOC] La descripción **entera** de `OpenLevel` son cuatro palabras: *"Travel to another level"*. Nada sobre qué persiste.
- **Seamless travel está documentado SOLO como feature de multiplayer.** En esa página las palabras "standalone", "single-player" y "OpenLevel" **no aparecen**. Si aplica a single-player standalone: 🔴 **indocumentado**.
- **Por qué el streaming gana igual:** OpenLevel destruye y reconstruye el mundo → **el pawn VR, el fade sphere y el tracking origin mueren y respawnean**. En VR eso es un frame negro y una discontinuidad de tracking en medio de la obra. **El streaming mantiene el pawn continuo, que es todo el punto del diseño con nivel persistente.**

---

# ⚠️ Meta no dice NADA sobre level streaming en Unreal
Ausencia verificada: **ni una** doc de Unreal sobre streaming, estrategia de memoria ni World Partition.
🚨 **Trampa fácil:** la tentadora guía *"Open World Games and Asset Streaming"* de Meta está en `/documentation/**unity**/po-assetstreaming/`. **La ruta de Unreal 404ea** (verificado). **Aparece en búsquedas de Unreal y es guía de Unity. No aplicarla.**
⚠ El blog *"Getting a Handle on Meta Quest Memory Usage"* (abril 2022) **es anterior al Quest 3**, cita RAM física en vez del presupuesto de app, y **contradice** la tabla actual. Usar solo [po-memory-ram](https://developers.meta.com/horizon/documentation/unreal/po-memory-ram/): **Quest 3/3S = 5.75 GiB**, contra **PSS**. Fallo = *"Low Memory Kill"*; en dev, *"recording logcat output and searching for the `lowmemorykiller` tag"*.
**LLM funciona en Android** [SRC] `LowLevelMemTracker.h:10-19` (`PLATFORM_SUPPORTS_LLM` default 1, sin override de Android) → build Development con `-LLM`. ⚠ `LLM_ENABLED_ON_PLATFORM` fue deprecado en 5.7.

---

# ✅ VEREDICTO SOBRE LA ARQUITECTURA DECIDIDA
| Decisión | Veredicto |
|---|---|
| Persistente: pawn + fade sphere + FlowDirector | ✅ **Mantener.** Coincide con el folclore; Epic no documenta regla. **Agregar OpenXR loading screen como red** |
| 9 sublevels streameados, sin World Partition | ✅ **Mantener.** ⚠ pero el argumento "WC deprecado → usá WP" es un no-sequitur, y **Epic calla sobre WP en Quest** |
| `LoadLevelInstance` sobre `LoadStreamLevel` | ✅ **Mantener.** Premisa **confirmada en el código**. 🚨 **Pasar `OptionalLevelNameOverride` + rutas completas + registrar los 9 mapas en Packaging** |
| Level Instances rechazados | ✅ **Decisión correcta, razón equivocada.** "Falla al empaquetar" **refutado**; `ALevelInstance` llama al **mismo** `LoadLevelInstance`. Razón real: mundo no-WP → sin gestión automática de streaming |
| GameInstance de Blueprint como autoridad | ✅ **Mantener.** El claim de los subsystems es **TRUE** ([SRC] `Kismet2.cpp:1080`), y el GameInstance es la respuesta **documentada** de Epic |
| Flujo en Data Asset | ✅ **Mantener**, `UDataAsset` plano. 🚨 **`TSoftObjectPtr<UWorld>` para los mapas** o explota la RAM. Saltar PrimaryDataAsset |
| Gameplay Tags | ✅ **Mantener.** Cero dependencia de GAS (verificado). 🔴 **La dirección del matching estaba al revés** |
| **Gameplay Message Router (Lyra)** | 🔴 **CORTAR. No existe en el motor.** Dispatchers en el FlowDirector. AsyncMessageSystem es v0.1 Experimental |

## 🚨 Las 3 acciones
1. **Registrar los 9 mapas** en Packaging Settings → *List of Maps to Include*. **Este es el riesgo real de fallo silencioso al empaquetar.**
2. **`OptionalLevelNameOverride` en cada `LoadLevelInstance`**, y disparar las transiciones desde **`OnLevelShown`**.
3. **Bajar `s.LevelStreamingActorsUpdateTimeLimit` de 5.0 a ~1–2 ms** y perfilar el GC forzado en cada descarga con OVR Metrics Tool. **El default es 36% de nuestro frame y nadie lo tuneó para VR.**
