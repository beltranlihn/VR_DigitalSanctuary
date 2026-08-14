# Método de trabajo — eficiencia de tokens y de errores

> Fuentes: docs oficiales de Anthropic (code.claude.com/docs, anthropic.com/engineering) + medición directa en este proyecto. Investigado 17/07/2026.

---

# 🔴🔴🔴 0. CÓMO DEPURAR — la autopsia del beam invisible (2026-08-04/05)

> **Un día entero de trabajo no llegó a nada. Al día siguiente, lo mismo se resolvió en 20 minutos.** La diferencia no fue conocimiento técnico: fue **método**. Esta sección es la lección más cara del proyecto. Leerla antes de arrancar cualquier depuración larga.

**Qué pasó, en una línea:** se construyó un instrumento de medición (capturas del viewport del editor + medición de píxeles), **nunca se lo validó**, dio 13 negativos seguidos, y sobre esos negativos falsos se hicieron 8 ediciones destructivas a un asset sin versionar hasta arruinarlo. La solución real —mover el componente Niagara al actor que ya estaba pegado a la mano— nunca se consideró porque nadie se salió del marco "por qué no dibuja".

## Las 6 reglas que salen de ahí

### 1. 🔴 Un instrumento sin control positivo NO mide: un negativo suyo no es evidencia
Antes de creerle a **cualquier** aparato de medición (captura, log, parser, script), **hacelo detectar algo que sabés que está**. Si nunca produjo un verdadero positivo, **no puede distinguir "no está" de "estoy ciego"**.
- Acá: 13 capturas dijeron "no hay beam". El instrumento **jamás** había mostrado un beam que se supiera presente. Todo el razonamiento posterior se construyó sobre un sensor apagado.
- **Costo del control positivo: 1 iteración. Costo de omitirlo: un día.**

### 2. 🔴 La observación directa del usuario le GANA a mi tooling. Siempre.
El usuario dijo, textual y dos veces: *"El niagara claramente funciona, lo estoy probando en el world y en simulate"*. Se siguió confiando en las capturas.
- **Ante una contradicción entre lo que reporta el usuario y lo que dice mi herramienta: la herramienta está mal hasta que se demuestre lo contrario. PARAR y reconciliar. No seguir adelante con la hipótesis propia.**
- Corolario: el usuario tiene el visor. Para VFX/VR **el oráculo es el visor**, no el editor. Un test de 5 minutos con el visor puesto vale más que una hora de inferencia. **Pedirlo temprano no es molestar: es el camino corto.**

### 3. 🔴 NUNCA editar en cadena un asset binario sin versionar
`LineTrace.uasset` estaba `??` en git. Se le hicieron 8 ediciones seguidas sin línea base ni respaldo → cuando se quiso volver al estado bueno conocido, **ya no existía**. Un problema de diagnóstico se convirtió en uno de corrupción irreversible.
- **Antes de la PRIMERA edición: commitear, o al menos copiar el `.uasset` al scratchpad.** Cuesta 10 segundos.
- Si el asset no está trackeado, **decirlo y frenar** antes de tocarlo, no después.

### 4. 🔴 Un experimento = una variable
La captura 7 cambió el valor literal **y** el flag `Absolute` a la vez → resultado ininterpretable, ronda perdida. Con dos variables, un negativo no te dice cuál falló.

### 5. 🔴 Regla de parada + re-encuadre obligatorio
Si el mismo bucle falla **3 veces seguidas**, el problema no es el próximo intento: es el **marco**. Parar y preguntar explícitamente:
- ¿Estoy midiendo bien? (regla 1)
- ¿Esto tiene que vivir **acá**? ← **la que resolvió el caso.** El beam no había que arreglarlo en `BP_AimBeam`: había que ponerlo en el actor que **ya estaba attacheado a la mano**, y entonces el origen salía gratis de la transform del componente.
- ¿Hay un asset/patrón que ya funciona del que pueda copiar? (§7.b del `CLAUDE.md`)

### 6. 🔴 Distinguir MEDIDO de INFERIDO, y no reportar inferencias como hallazgos
Se anunció *"encontré la causa raíz"* sobre esta cadena: `Beam_Starts` no está conectado **[medido, cierto]** → entonces el beam sale del origen del mundo **[inferido, NUNCA verificado]** → por eso no se ve **[falso]**. La primera parte era verdad y aun así la conclusión estaba mal.
- Al reportar: **decir qué se midió y qué se dedujo.** Una inferencia sin verificar no se anuncia como causa raíz.

## Lo que SÍ funcionó (el patrón a repetir)
Cambio estructural pequeño → **test en visor** → confirmación del usuario → siguiente cambio. Cinco ajustes seguidos, cinco verificaciones, cero retrocesos. **El ciclo corto con oráculo real le gana por goleada al ciclo largo con oráculo dudoso.**

## 🌾 Las 4 reglas nuevas de la jornada 2026-08-13 (el negro que "arreglé" 3 veces)

### 7. 🔴 Un SÍNTOMA puede tener VARIAS fuentes apiladas — enumerarlas TODAS antes de declarar "arreglado"
"Se va a negro al llegar al centro" tenía **cuatro** fuentes simultáneas: el fade del GoBlack + la viñeta al máximo + el GC de la descarga + un `SetLight(0)` escondido dentro de `Configure`. Se arregló la primera plausible y se declaró éxito **tres veces**. El protocolo correcto: ante un síntoma visual, **listar por escrito todos los sistemas capaces de producirlo** (fades, viñeta, luz de sala, hitches/GC, materiales, streaming) y descartarlos uno a uno — el costo es 10 minutos; cada "arreglado" falso costó una iteración de visor de Beltrán.

### 8. 🔴 Leer el CUERPO de las funciones que la cadena llama — el nombre miente
`Configure(Nombre, Acento)` también **apagaba la luz** (llamaba `InitRoom` → `SetLight(InitialLight)`). El grafo que se auditó estaba "limpio" porque el apagón vivía un nivel más adentro. Al auditar una cadena, abrir las funciones llamadas (al menos las de los BPs propios) — son una llamada de `read_graph_dsl` cada una.

### 9. 🔴 Pedir VIDEO del visor al SEGUNDO diagnóstico fallido, no al tercero
Dos segundos de fotogramas (ffmpeg + Read de PNGs) resolvieron lo que tres corridas de log no pudieron: el video mostró QUÉ se oscurecía (la luz de la sala entera) y CUÁNDO (el frame exacto en que aparece Alma = EnterRoom). El log dice qué corrió; el video dice qué se VE. Receta: `ffmpeg -ss A -to B -i video.mp4 -vf "fps=8,scale=640:-1" frames/f_%03d.png` → Read.

### 10. 🔴 Integrar lo probado, no reconstruirlo — la violación se paga el mismo día (2 casos en una jornada)
(a) Se inventó una mesa-mesh y slots colocados cuando el modelo probado de `L_Touch` era TargetPoints+spawn; (b) se construyó un gate de quietud ciego cuando `BP_HeartSensor` ya tenía calibración+zona+feedback **probados en visor**. Ambos se tiraron y rehicieron. Ante CUALQUIER mecánica de etapa: la fuente es **el nivel de prueba del stage + su tracker** — el trabajo es migrar/integrar (patrón `ForceAttachToHand` + spawn por tags per-sublevel), no re-diseñar. Y toda mecánica corporal necesita **feedback visible desde el día 1** (la esfera de zona de Heart existe exactamente por eso — "no sucedió nada" = mecánica sin feedback, no mecánica rota).

---

# 🔴 1. LA REGLA #1: NUNCA traer una respuesta MCP gigante al contexto principal

**Medido en este proyecto:**
| Llamada | Devolvió |
|---|---|
| `describe_toolset` (BlueprintTools) | **72.000 chars** |
| `find_nodes` (un function graph) | **146.000 chars** |
| `get_connected_subgraph` | **1.713.000 chars** |

> [DOC] "Running tests, fetching documentation, or processing log files can consume significant context. **Delegate these to subagents so the verbose output stays in the subagent's context while only a summary returns**." — [costs.md](https://code.claude.com/docs/en/costs.md)

**Un subagente convierte 1.7M en 10k = 99% de ahorro.** Cada subagente tiene su propia ventana de 200k y **solo su mensaje final vuelve al padre**.

## Cómo evitarlo en la práctica (por orden de preferencia)
1. **NO llamar a la herramienta gigante.** Casi siempre hay una acotada:
   - ❌ `describe_toolset` → ✅ [toolsets.md](toolsets.md) (ya está destilado)
   - ❌ `find_node_types` con filtro amplio → ✅ filtro **específico**
   - ❌ `get_connected_subgraph` → ✅ `find_nodes` con `node_class` + `get_node_infos` de 2-3 nodos
   - ❌ `find_nodes(title:"")` sin `node_class` → ✅ siempre con `node_class`
2. **Si el output ya se volcó a un archivo**, procesarlo con **PowerShell/Grep**, no leerlo:
   ```powershell
   # contar sin leer
   $raw = Get-Content $f -Raw; ([regex]::Matches($raw, 'K2Node_VariableSet')).Count
   ```
   (Así medimos los nodos huérfanos sin gastar contexto.)
3. **Si hay que leerlo entero → subagente**, con instrucción explícita de qué devolver.

---

# 🔴 2. Prompt caching: es todo, y se rompe fácil
> [DOC] "the API prefix-matches your entire request against recently cached requests" → los tokens cacheados se cobran a **~10%**. — [prompt-caching.md](https://code.claude.com/docs/en/prompt-caching.md)

**El orden importa.** Capas de más estática a más dinámica: system prompt (tools) → CLAUDE.md/memoria → conversación → mensaje nuevo.

## ⚠ Rompe la caché (= un turno recomputado a precio completo)
- **Cambiar de modelo** (Opus ↔ Sonnet) — reconstruye TODO
- **Cambiar effort level** — cada nivel tiene su propia caché
- **Prender fast mode a mitad de sesión** (header nuevo en el cache key) → prenderlo al INICIO, no en medio
- **Que un servidor MCP se conecte/desconecte** SI sus tools están en el prefijo (las *deferred* —default— NO rompen). 🔴 Si el editor de Unreal cierra, el server `unreal` cae → **mantené Unreal abierto TODA la sesión.**
- **`/compact`** (por diseño) · **actualizar Claude Code** · **resumir una sesión vieja** (reprocesa todo) · agregar deny rule de una tool entera

## ✅ NO rompe la caché (se agregan al final)
- Editar/leer archivos · **invocar skills y `/commit`** · cambiar permission mode · `/recap` · **subagentes** (cache propia, no tocan la del padre)
- **`/rewind`** → vuelve a un cache ya caliente. Para **abandonar un camino** usalo en vez de `/compact` (más barato).

**→ Agrupar los cambios de config AL INICIO de la sesión, nunca a mitad.**
**→ Esta sesión ya usa TTL de 1 hora** (suscripción Claude). Con API key el default es 5 min y se activa con `ENABLE_PROMPT_CACHING_1H=1`.

---

# 3. `/clear` vs `/compact`
| | Cuándo | Costo | Gana |
|---|---|---|---|
| **`/clear`** | cambiar a una tarea **no relacionada** (otro Blueprint, otro subsistema) | reconstruye system+CLAUDE.md una vez | **borra lecturas irrelevantes, exploración y enfoques fallidos** |
| **`/compact`** | corte natural **dentro** de la misma tarea | un turno caro + invalida la conversación | mantiene CLAUDE.md cacheado, historia más corta |

> [DOC] "run `/compact` at a **natural break** in your work … instead of waiting for auto-compaction to trigger **mid-task**."

**→ Regla para este proyecto: `/clear` entre Blueprints distintos. No acumular.**
**→ Patrón de fallo a evitar:** corregir el mismo error una y otra vez. Tras **2 correcciones fallidas**, `/clear` + reescribir el prompt con lo aprendido. Sesión limpia + mejor prompt > sesión larga + correcciones apiladas.

---

# 4. Memoria y skills: presupuesto real
> [DOC] **MEMORY.md se carga como las primeras 200 líneas O 25KB**, lo que llegue primero. El resto **on demand**. — [memory.md](https://code.claude.com/docs/en/memory.md)
> [DOC] CLAUDE.md: objetivo **bajo 200 líneas**. "Every 100 lines above 200 reduces adherence because important rules get buried."

**Qué NO poner:** lo que se deduce del código · convenciones estándar · docs de API (linkear) · consejos obvios.
**Qué SÍ:** comandos de build/test · estándares que se desvían del default · decisiones de arquitectura · **gotchas**.

## ✅ Los skills SÍ hacen progressive disclosure (verificado en vivo)
⚠ **Corrección a una afirmación errónea que circula:** *"al invocarse un skill se carga el directorio entero"* → **FALSO.** **Verificado directamente en este proyecto**: al activarse `unreal-vr` entró **solo `SKILL.md`**; los `references/` se leyeron **uno por uno, a demanda**.
→ **La estructura actual (SKILL.md corto + references/ enlazados) es la correcta.** Mantenerla: cada referencia cuesta 0 hasta que se necesita.
→ **Corolario: agregar referencias es barato. Engordar SKILL.md es caro.**

---

# 5. Subagentes: cómo pedirlos bien
Lo aprendido a los golpes en este proyecto:
- 🔴 **El texto final del subagente ES el entregable.** Nada más de su corrida es visible. **Un agente devolvió "espero a los otros dos" tras 110k tokens de investigación real → entregó CERO.** Decírselo explícitamente en el prompt si hay riesgo.
- **Un subagente NO orquesta.** Si lanza sub-agentes propios, sus notificaciones llegan al padre y confunden. Pedir trabajo, no coordinación.
- **Exigir formato de salida**: qué tiers, qué citas, qué encabezar. Sin eso devuelven prosa inútil.
- **Exigir separación de evidencia**: `(a) doc oficial / (b) código fuente / (c) folclore no verificado`. **Esto resultó ser lo más valioso de todas las investigaciones** — media docena de "buenas prácticas" que todo el mundo repite no están escritas en ningún lado.
- **Pasarles el dato del código fuente local** (`C:\Program Files\Epic Games\UE_5.8`). Resolvió al menos 3 preguntas que la doc tenía **mal**.
- **Dos agentes pueden contradecirse.** Pasó: uno decía `MobileHDR=False + TonemapSubpass=1`, el otro `MobileHDR=True`. **Se resolvió leyendo el motor**, no eligiendo al que sonaba mejor.
- Subagentes usan TTL de caché de 5 min y auto-compactan solos.

---

# 6. Modelos
> [DOC] "Sonnet handles most coding tasks well and costs less than Opus. **Reserve Opus for complex architectural decisions or multi-step reasoning.**"

| Tarea | Modelo |
|---|---|
| ediciones simples, lint | Haiku |
| coding rutinario, debug | **Sonnet** |
| arquitectura, razonamiento multi-paso | Opus |

⚠ **Cambiar de modelo a mitad de sesión rompe la caché entera.** → decidirlo al inicio, o usar **`model:` por subagente** (que no toca la caché del padre).
**El modelo de trabajo acordado con el usuario ("Opus planea, Sonnet ejecuta") es correcto — pero implementarlo con `model:` en subagentes, no cambiando el modelo de la sesión.**

---

# 7. 🔴 EL PATRÓN OFICIAL PARA TRABAJO MULTI-SESIÓN
> [Anthropic Engineering: Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)

**Dos agentes:**
1. **Initializer (una vez):** repo git · lista de features (JSON) · `progress.txt` · commit.
2. **Coder (cada sesión):** lee `progress.txt` + `git log` → trabaja **una feature** → **verifica end-to-end** → commit descriptivo → deja estado limpio.

**Por qué escala:** el archivo de progreso es el puente entre sesiones, **y el historial de git es el contexto real, no la conversación acumulada**.
> [DOC] "Starting each session with **verification testing** catches undocumented bugs before implementing new features."

## 🚨 ESTE PROYECTO NO TIENE GIT
`Is a git repository: false`. Consecuencias:
- **No hay red de seguridad.** Horas de Blueprints, structs, config y niveles sin versionar. Un `write_graph_dsl` mal hecho no se puede revertir.
- **Falta la mitad del patrón oficial**: sin historial de git, cada sesión arranca sin el contexto barato que da `git log`.
- Los trackers por BP (`blueprints/*.md`) ya cubren la otra mitad y **funcionan** — pero cuentan la intención, no el diff.
→ **RECOMENDACIÓN FUERTE al usuario: `git init` + `.gitignore` de Unreal** (ignorar `Binaries/`, `Intermediate/`, `Saved/`, `DerivedDataCache/`). Es la mejora de seguridad y de eficiencia más grande disponible, y no cuesta nada.

---

# 8. Verificación: el bucle que cierra solo
> [DOC] "Once the check exists, Claude does the work, runs the check, reads the result, and **iterates until the check passes**."

**En este proyecto ya existe y funciona:** `Development|PrintString` → `LogsToolset.GetLogEntries {category:"", pattern, maxEntries}`. **El humano solo aprieta Play; el diagnóstico lo hago yo leyendo el log.** Sin transcripción manual.
**Reglas aprendidas:**
- Prefijos numerados (`BP 1:`, `SN 2:`) + **regex al leer** → nunca traer el log entero.
- Un bool `bDebug` + un `DebugInterval` (si no, spamea a 90 fps y el log es inservible).
- **Imprimir IDENTIDADES y NÚMEROS, no "OK".** "pawn OK" costó dos iteraciones: el pawn *era* válido, solo que era el equivocado.
- 🔴 **Un feedback que no depende del estado que querés verificar NO sirve para verificarlo.** El cubo escalaba aunque `bBreathing` fuese falso → ocultó dos tests seguidos que el estado nunca se activaba.
- **Un cambio sin probar a la vez.** Dos cambios = imposible atribuir el fallo.

---

# 9. Lo que NO se puede controlar (verificado)
Anthropic **no expone**: truncado del output de MCP · `maxTokens` por herramienta MCP · un "modo terso" para la verborragia de Claude · batching entre turnos (sí hay llamadas paralelas **dentro** de un turno) · búsqueda semántica en lectura de archivos.
→ **Por eso la regla #1 (no traer el output gigante) es la única defensa real.**

---

# ✅ CHECKLIST DE SESIÓN
**Al abrir:**
1. Unreal ABIERTO antes que Claude (si no, no existen las tools y no se pueden enganchar a mitad).
2. `SceneTools.get_current_level` para verificar el link — barato.
3. Si hay que cambiar modelo/effort/MCP: **ahora, no después**.
4. Leer el tracker del BP en el que se va a trabajar, **no re-derivar el grafo**.

**Trabajando:**
5. Filtros específicos. `node_class` siempre. Nunca la herramienta gigante.
6. Llamadas independientes → **en paralelo, en un solo mensaje**.
7. Compilar seguido (`compile_blueprint` **sí reporta errores** — verificado).
8. Pensar el grafo antes de escribirlo: **cada `write_graph_dsl` deja huérfanos permanentes** (ver [gotchas.md](gotchas.md)).

**Al cerrar:**
9. `save_assets` + actualizar el tracker del BP.
10. `/clear` antes de pasar a otro Blueprint.
