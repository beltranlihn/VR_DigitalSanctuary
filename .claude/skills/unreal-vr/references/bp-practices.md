# Buenas prácticas de Blueprints — lo que Epic dice OFICIALMENTE

> **Regla de este archivo:** cada afirmación lleva fuente. Lo que NO tiene fuente oficial va marcado como **folclore**, aunque "todo el mundo lo diga". Investigado 16/07/2026 sobre docs de UE 5.7/5.8.
>
> ⚠️ **Trampa de versiones:** el documento más concreto que Epic escribió sobre esto — **"Balancing Blueprint and C++"** — solo existe **fijado a 4.27**. Su reemplazo en UE5 ("Coding in Unreal Engine: Blueprint vs. C++") **eliminó** las afirmaciones concretas sobre costo de nodos, tick y dependencias de carga. El mecanismo del motor no cambió; **la documentación sí retrocedió**. Al citarlo, marcar la versión.

---

## 🔴 Nodos PUROS: Epic lo documenta (y nos costó 2 bugs no saberlo)
> **"This means that a Pure Function will be called one time for each node it is connected to."**
> — [Functions in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/functions-in-unreal-engine) · **UE5-actual**

> "Nodes with execution pins store the values of their output pins when they execute, while nodes without execution pins reevaluate their outputs every time a node connected to their outputs executes."

**Oficial:** el mecanismo. **Folclore:** el remedio — Epic **NO publica** la regla "cachea el puro en una variable local". Se deduce, no se cita.
→ Ver [gotchas.md](gotchas.md) para el bug real que produjo dos veces en este proyecto.

## Tick — la creencia de "el Tick es malo" es FALSA (Epic la contradice)
> "the event-driven approach can be **less optimal** depending on how often the condition changes. If an event is fired multiple times per frame … then it can be **more efficient to use Tick**."
> — [Common Memory and CPU Performance Considerations](https://dev.epicgames.com/documentation/en-us/unreal-engine/common-memory-and-cpu-performance-considerations-in-unreal-engine)

> "The Tick event … is useful for handling **realtime movement**. However, using Tick for routines that are **occasional rather than continuous** can result in wasteful CPU usage."

**Para este proyecto:** el pipeline de respiración es señal continua por frame = la categoría *realtime* que Epic exceptúa. **NO moverlo a timers** (además aliasaría los filtros EMA). Lo que sí aplica: cuidar *qué* corre adentro del Tick, no que esté en Tick.
- Control: `SetActorTickEnabled` / `SetComponentTickEnabled`; intervalos vía `Set Actor/Component Tick Interval`. ⚠ **"Will not enable a disabled tick function"** — el intervalo NO enciende el tick.
- Componentes: **no tickean por defecto** → `PrimaryComponentTick.bCanEverTick = true`.
- ❌ **Epic NUNCA define "muchas instancias"**. Cualquier número que circule ("más de 100 actores") es folclore.

## 🔴 El ORDEN de tick DENTRO de un grupo NO está garantizado
> "Each tick group will finish ticking every actor and component **before the next tick group begins**."
> "The reason to use this over a tick group is that **many actors can be updated in parallel** if they're in the same group."
> — [Actor Ticking](https://dev.epicgames.com/documentation/en-us/unreal-engine/actor-ticking-in-unreal-engine)

Garantía **solo entre grupos**. Adentro de un grupo hay paralelismo → **el orden es indefinido**. (Epic no lo dice con esas palabras; la garantía simplemente **no existe**.)
**Consecuencia real:** un consumidor que hace polling de una variable de otro actor/componente en su Tick puede leer **el valor de este frame o el del anterior, de forma no determinista**. → Argumento de **CORRECCIÓN** (no de prolijidad) para usar dispatchers en vez de polling.
Determinismo explícito, si hace falta: `AddTickPrerequisiteActor` / `AddTickPrerequisiteComponent`.

## Estructura del grafo
> **"If you find yourself using the same set of nodes more than twice in a graph, consider making it a function or a macro."**
> — [Blueprint Best Practices](https://dev.epicgames.com/documentation/en-us/unreal-engine/blueprint-best-practices-in-unreal-engine)

> "Keep things tidy from the get go! It's much harder to clean up after you've made a bunch of code than to work clean as you go."

| | Oficial |
|---|---|
| **Function** | Se llama de verdad. Permite override en hijas. Comunicación entre BPs. **No admite nodos latentes** (Delay). Un solo exec in/out. |
| **Macro** | "Macros take the nodes from the macro graph, and actually **replace the macro node with a copy** of all those nodes" → inline en compilación. **Sí admite latentes** y múltiples exec pins. |
| **Collapsed graph** | Puramente organizativo. Sin reuso fuera del grafo. |
| **Function Library** | "Functions … are **static** … best for **general-purpose logic that operates on inputs and returns a result**." |

**Función vs macro en performance:** ❌ **folclore**. Epic documenta el mecanismo (inline vs llamada), **nunca** dice que uno sea más rápido.
**Para este proyecto:** las etapas del filtro (EMA, band-pass) son matemática pura sobre inputs sin estado de instancia → **Blueprint Function Library** es el encaje textual según Epic. Bonus: saca esos nodos del .uasset del actor.

## ❌ Tamaño de grafo / cantidad de nodos: Epic NO dice NADA
Buscado específicamente. **No existe**: ni máximo de nodos, ni máximo de tamaño de asset, ni afirmación de que un grafo grande cargue más lento, ni que partirlo en funciones mejore el **runtime**.
> "Large C++ files are easier to modify than large Blueprint graphs." — mantenibilidad, no performance.

**Conclusión honesta:** partir un grafo gigante está bien respaldado como **mantenibilidad**; **no esperar ganancia de frame**. Son los mismos nodos y los mismos despachos, reorganizados (y una función agrega su propio costo de llamada). Hacerlo por cordura, no por el frame budget.

## Blueprint vs C++ — la posición ACTUAL
> "Fundamentally, C++ is more performant … **However, Blueprint and C++ performance differences are usually insignificant and depend on context.**"
> — [Coding in Unreal Engine: Blueprint vs. C++](https://dev.epicgames.com/documentation/en-us/unreal-engine/coding-in-unreal-engine-blueprint-vs-cplusplus) · **UE5-actual**

Contextos donde SÍ importa (lista textual): infraestructura de bajo nivel · loops apretados con I/O · sistemas que procesan grandes datasets · **"Tick-dependent classes with many instances"** · multi-threading (BP no lo soporta).

> **"If you use Blueprint and have performance issues, profile your project with Unreal Insights and optimize the most significant bottlenecks before considering converting your Blueprint to C++."**

El dato clave, **de la página 4.27** (⚠ versión):
> "executing each **individual node** in a Blueprint is slower than executing a line of C++ code, but **once execution is inside a node, it's just as fast** as if it had been called from C++"

→ El costo es el **despacho por nodo**, no el trabajo adentro. Un grafo de N nodos en Tick paga N despachos/frame. A 90 Hz el presupuesto es **11.1 ms**.

🚩 **Blueprint Nativization: ELIMINADA en UE5.** "Blueprint Nativization will not exist in UE5 … developers will need to take other optimization approaches" — [UE5 Migration Guide](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-5-migration-guide). **No la reemplazó ninguna feature**, solo consejos. Todo consejo de "nativizalo" es UE4 muerto.

---

## Componentes
> "ActorComponent is the base class for components that define **reusable behavior that can be added to different types of Actors**." — [UActorComponent API](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Engine/UActorComponent)

> "Actor Components are most useful for **abstract behaviors** such as movement, inventory or attribute management, and other **non-physical concepts**."
> "Scene Components support **location-based** behaviors that do not require a geometric representation."
> — [Components](https://dev.epicgames.com/documentation/en-us/unreal-engine/components-in-unreal-engine)

Principio de desacople (⚠ scope: Game Feature Plugins, no es regla general):
> "The Component(s) should handle **all program logic and data storage** related to your feature."
> "When you keep the required interaction with the project's Actor subclass to a **minimum**, it is easier to implement your feature in another project."
> — [Game Features and Modular Gameplay](https://dev.epicgames.com/documentation/en-us/unreal-engine/game-features-and-modular-gameplay-in-unreal-engine)

⚠ **No existe** una doc general de Epic que diga "preferí componentes sobre actores monolíticos". El principio es real y de Epic, pero el enunciado universal es extrapolación.

## Comunicación entre Blueprints — Epic la plantea como SEMÁNTICA, no como optimización
[Blueprint Communication Usage](https://dev.epicgames.com/documentation/en-us/unreal-engine/blueprint-communication-usage-in-unreal-engine)

| Método | Textual | Cuándo (Epic) |
|---|---|---|
| **Direct** | "the **most common** method of sharing information between Actors" | un switch abre una puerta específica |
| **Casting** | "are you a special version of that object" | acceder a una versión especializada |
| **Event Dispatcher** | "best suited for telling other **'listening'** Blueprints that an event has happened" | **uno → muchos**; el notificador no conoce a los oyentes |
| **Interface** | "a common method of interacting with **multiple types of objects** that all share some specific functionality" | "similar en varios BPs pero **ejecuta distinto**" (puerta/luz/item responden a "usar") |

**El casting es NORMAL y recomendado** para su caso de uso. "Nunca castees, usá interfaces siempre" es **folclore distorsionado**.

**Interfaces — limitaciones oficiales:** no pueden agregar variables, ni editar grafos, ni agregar componentes.
⚠ **Interfaces NO son la herramienta para un flujo uno→muchos hacia afuera.** Epic las plantea como **polimorfismo** (muchos tipos, un mismo mensaje, hacia adentro). Para "un productor avisa a N consumidores" → **dispatchers**.

## 🔴 Referencias duras — el argumento fuerte para separar pipeline de efecto
> "a **hard reference** where object A refers to object B and **causes object B to be loaded when object A is loaded**"
> "Careful consideration needs to happen or your **memory footprint can balloon**."
> — [Referencing Assets](https://dev.epicgames.com/documentation/en-us/unreal-engine/referencing-assets-in-unreal-engine)

> "Whenever you cast to a Blueprint class BP_A **(or declare it as a variable type on a function or other Blueprint)** from BP_B it creates a **load dependency**."
> "if BP_A references four large Static Meshes and 20 sounds, every time you load BP_B it will have to load four large Static Meshes and 20 sounds, **even if the cast would fail**."
> — [Balancing Blueprint and C++](https://dev.epicgames.com/documentation/en-us/unreal-engine/balancing-blueprint-and-cplusplus?application_version=4.27) · ⚠ **solo 4.27**

⚠⚠ **Lo crítico: declarar una variable tipada cuesta LO MISMO que castear.** Cambiar un Cast por una variable tipada **no compra nada**. La culpa no es del nodo Cast, es de **la referencia al tipo**.
⚠ La página *Referencing Assets* **NO menciona nodos Cast** (es toda C++). No citarla para eso.

**Mitigaciones oficiales:** castear a **clases base baratas** ("define functions and variables at the most base level") · **soft pointers** (`TSoftObjectPtr`/`FSoftObjectPath`) · Asset Manager · evitar refs de asset en constructores.
❌ **Folclore (sin fuente Epic):** "usá Interfaces para romper referencias duras" · "usá Tags para evitar hard refs". Funcionan, pero Epic **no las documenta como tal**.

**Herramientas oficiales:** [Reference Viewer](https://dev.epicgames.com/documentation/en-us/unreal-engine/reference-viewer-in-unreal-engine) (teclas **S**/**H** para soft/hard) y **Size Map** (click derecho en el Content Browser). ⚠ "In-editor memory size can be substantially different from a shipped product's disk space usage."

## Dispatchers
> "By **binding** one or more events to an Event Dispatcher, you can cause all of those events to fire once the Event Dispatcher is called." — [Event Dispatchers](https://dev.epicgames.com/documentation/en-us/unreal-engine/event-dispatchers-in-unreal-engine)
> "Each event can be bound **only once**, even if the Bind Event node is executed multiple times." — [Binding and Unbinding](https://dev.epicgames.com/documentation/en-us/unreal-engine/binding-and-unbinding-events-in-unreal-engine)

> "To improve performance, use **timers or delegates** to schedule work in Blueprints instead of using Tick." — [Blueprint vs C++](https://dev.epicgames.com/documentation/en-us/unreal-engine/coding-in-unreal-engine-blueprint-vs-cplusplus) · UE5-actual

Anti-polling (⚠ **scope UMG**, la lógica transfiere pero no es cita para gameplay):
> "Whenever possible, you should **avoid using On Tick or On Paint** to run logic in your UI."
> "the UI only changes **on the frame when the value changes** instead of each frame."
> — [Optimization Guidelines for UMG](https://dev.epicgames.com/documentation/en-us/unreal-engine/optimization-guidelines-for-umg-in-unreal-engine)

❌ **"Desbindear siempre en EndPlay" = FOLCLORE.** Epic **no menciona** lifetime, GC ni referencias colgantes de dispatchers en NINGUNA de sus tres páginas del tema. Adoptarlo como estilo de casa si se quiere, pero **no atribuírselo a Epic**.

## ⚠️ Lyra y el Gameplay Message Subsystem — SIN documentación oficial
**No existe ninguna página de Epic** para el Gameplay Message Subsystem / GameplayMessageRouter. Existe en el código de Lyra, pero **Epic no lo documenta ni lo recomienda**. Todo lo que circula presentándolo como "el patrón bendecido de Epic" es **interpretación de la comunidad sobre código de ejemplo**.
Lo único oficial de Lyra es genérico: *"Its architecture is designed to be modular, including a core system and plugins"* — [Lyra Sample Game](https://dev.epicgames.com/documentation/en-us/unreal-engine/lyra-sample-game-in-unreal-engine). "Tour of Lyra" **no** tiene contenido de arquitectura (es un paseo de menús).
Adyacente y **Experimental** (evitar para producción): [Async Message System](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Plugins/AsyncMessageSystem).
→ **Toda la maquinaria modular de Epic apunta a proyectos multiplayer grandes con fronteras de plugins.** Para un componente y unos pocos actores de efecto, los **Event Dispatchers** son lo documentado y lo proporcionado.

## Data Assets para valores de tuning
> "A Data Asset is an asset that stores data related to a particular system in an instance of its class." — [Data Assets](https://dev.epicgames.com/documentation/en-us/unreal-engine/data-assets-in-unreal-engine)

❌ **Epic NO publica ninguna comparación** entre "tuning en Data Asset" vs "tuning como variables del BP". Los beneficios que se citan son reales pero **la recomendación es folclore**.
**Criterio pragmático:** un Data Asset se gana su lugar cuando querés **presets intercambiables** o que alguien ajuste sin abrir un grafo. Para un set de valores que tocás mientras iterás, variables expuestas en el componente son más simples y Epic no dice lo contrario.

---

## Resumen: folclore que NO tiene fuente oficial
| Creencia | Realidad |
|---|---|
| "El Tick es malo / nunca uses Tick" | ❌ **Contradicho** por Epic |
| "Nunca castees, usá interfaces" | ⚠ Distorsión. Epic solo advierte de castear a BPs **caros** |
| "Interfaces / Tags rompen hard refs" | ❌ Sin fuente Epic |
| "Los macros son más rápidos que las funciones" | ❌ Sin fuente Epic |
| "Máximo N nodos por función" | ❌ No existe ningún número |
| "Los BP grandes cargan más lento" | ❌ Sin fuente Epic |
| "Partir en funciones mejora el runtime" | ❌ Sin fuente Epic (es mantenibilidad) |
| "Desbindear en EndPlay" | ❌ Sin fuente Epic |
| "El Gameplay Message Subsystem es el patrón de Epic" | ❌ **Ni siquiera tiene página** |
| "BP es 10x más lento que C++" | ❌ Ningún número oficial existe |
| "Cachear puros en variable local" | ⚠ Mecanismo oficial, **remedio no** |

## Aplicado a Soul Charger
1. **El Tick del pipeline es legítimo.** No tocarlo.
2. **El split a componente es correcto** — pero por arquitectura, reuso, **el orden de tick no determinista**, y matar el fan-out de referencias duras. **No** por frame time.
3. **Dispatchers, no interfaces**, para `Level` → N efectos.
4. **Antes de reescribir nada en C++: Unreal Insights.** Es instrucción literal de Epic.
5. Presupuesto: **11.1 ms/frame a 90 Hz** — el único número VR que Epic da que toque este diseño. ([XR Best Practices](https://dev.epicgames.com/documentation/en-us/unreal-engine/xr-best-practices-in-unreal-engine) no tiene NADA de Blueprints/CPU; es todo render.)
