# CLAUDE.md — Soul Charger (VR Quest 3) · contexto maestro para Claude Code

> Este archivo lo **auto-carga Claude Code** al abrir el proyecto. Es el punto de entrada: qué es la obra, hacia dónde va, cómo se trabaja acá y qué NO romper. Lo técnico-operativo profundo vive en la **skill `unreal-vr`** (se auto-activa). Leé esto entero una vez; después consultá los punteros a demanda.

---

## 1. Qué es Soul Charger
Obra de **VR inmersiva de sanación/meditación** para **Meta Quest 3**. Experiencia **sentada, single-user, ~15 min**, estética tipo **James Turrell** (luz de color en el aire, vacíos oscuros, casi sin geometría). El usuario atraviesa **stages** (etapas) sensoriales — respiración, latido, movimiento, etc. — cada una una mini-mecánica de biofeedback/interacción corporal. No es un juego: es una experiencia contemplativa guiada.

**Objetivos de diseño:** presencia, calma, que el cuerpo del usuario (respiración, latido, gesto) **maneje** lo que ve/siente. Cada mecánica se construye para que el input físico sutil (inclinar un mando ~1°, respirar, sostener un control en el pecho) module luz/sonido/escala.

🔴 **Documento maestro de la obra: [`docs/OBRA-SOUL-CHARGER.md`](docs/OBRA-SOUL-CHARGER.md)** (revisión completa de guión, 2026-08-06). Narrativa escena por escena, las 5 etapas con sus mecánicas, las **reglas transversales** (capa autoral + capa viva, cero callejones sin salida, el arco del gesto, medir como parte de la obra), estética, arquitectura de Blueprints y orden de construcción. **Es la fuente autoritativa de QUÉ es la obra** — lo reemplaza el design doc de la raíz.

Otros documentos de diseño (raíz): [`Soul-Charger-Design.md`](Soul-Charger-Design.md) (superado), [`Soul-Charger-Plan-Reconstruccion.md`](Soul-Charger-Plan-Reconstruccion.md), [`Soul-Charger-Variables-Respiracion.md`](Soul-Charger-Variables-Respiracion.md).
> ⚠️ **El design doc es previo al pivote a Quest** y en partes está desactualizado: dice/asume **PC VR** (falso, ver §2) y referencia el *Gameplay Message Router* de Lyra (no existe en 5.8, ver `skills/unreal-vr/references/streaming-arch.md`). Donde el design doc choque con lo de abajo o con la skill, **gana la skill**.

## 2. 🔴 Target técnico — cambia TODAS las respuestas
**Meta Quest 3 STANDALONE (APK Android). NO es PC VR.** Corre el **renderer MÓVIL, forward, todo horneado.** Lumen/Nanite/Virtual Shadow Maps/Distance Fields **NO corren**. Presupuesto **72 Hz de refresh / 60 fps de render objetivo (~13.9 ms)**, **fill-rate bound**. Mitad de lo que se lee en internet asume deferred+PC y no aplica.
- **Antes de tocar config, materiales o luces** → `skills/unreal-vr/references/materials-vr.md` y `lighting-quest.md`.
- Empaquetar en **Development** para los builds de trabajo/data (Shipping recorta logs y cambia rutas de guardado).

## 2.b 🧼 ETAPA ACTUAL (desde 2026-08-17): la versión LIMPIA en `MapsV2`
🔴 **El nivel de trabajo es `/Game/SoulCharger/MapsV2/L_SoulCharger`** (persistente nuevo) con sus 6 sublevels en `MapsV2/RoomsV2/`. La etapa consiste en **rehacer las mecánicas de forma limpia y ordenada en un nivel nuevo**; el esqueleto viejo (`Maps/L_Persistent` y sus BPs) **no se toca** y queda como referencia de lo ya probado.

Rehecho hasta ahora: **`BP_Director_Movement`** (recorrido + caminata + pasos + viñeta en un solo BP), **`BP_Director_Music`** (ambientes con crossfade), **`BP_Door_SC`** (puerta con el arte real, una por sublevel) **`BP_Director_Rooms`** (carga/descarga de sublevels con fundido por material), **`BP_Alma_SC`** (la guía, con toda su vida en el material), **`BP_ProtoSoul_SC`** (el alma del usuario: malla intercambiable, hover, y puntos que dan posición **y tamaño**) **`BP_SoulPicker_SC`** (la pantalla de "Start experience": siembra las 5 candidatas y resuelve la elección por hover + gatillo) y **`BP_SoulHUD_SC`** (el HUD: barra de carga, gráfico EEG y punto del latido en **un solo widget** sobre un lienzo holgado, con material de Disable Depth Test como la ameba) y **`BP_BreathRing_SC`** (el temporizador de respiración de Entering: dos anillos, divisores, marcador y nombres en arco, **configurable a 2/3/4 divisiones** — cambiás los tiempos y se reacomoda solo en el viewport). Detalle y estado: [`blueprints/_INDEX.md`](.claude/skills/unreal-vr/blueprints/_INDEX.md), sección "ETAPA ACTUAL".

⚠ **Dos reglas de trabajo que salieron de esta etapa** (`references/gotchas.md` §114-118): **colocar actores sí, sacarlos se pregunta**; y **contar actores antes/después de cada tanda de scripts, guardando siempre con rutas explícitas** — un `execute_tool_script` que falla dispara un Undo que se lleva trabajo del nivel.

## 3. Estado de los stages (actualizar al avanzar)
Carpetas en `VR_Test/Content/SoulCharger/Stages/`: **Breath · Heart · Mind · Movement · Touch · Inicio · Centro · Salida**. Detalle vivo en [`docs/ESTADO-STAGES.md`](docs/ESTADO-STAGES.md).

| Stage | Estado | Nota |
|---|---|---|
| **Breath** | 🟢 Completo end-to-end | **Plantilla arquitectónica** de la obra. Copiar su patrón. |
| **Heart** | 🟡 En progreso | Sensor de latido por OSC + visualizador de zona segura (debug). |
| **Calibration** (herramienta) | 🟢 Pipeline listo, falta test en visor | Nivel de captura de datos multi-usuario (`Content/SoulCharger/Calibration/`). No es un stage de la obra: es tooling de investigación. |
| **Movement** ("Surrounding", dibujo 3D) | 🟡 En progreso | `BP_DrawCanvas` (motor de geometría) + `BP_BrushTool` (la herramienta) construidos y compilando, colocados en `L_Test_Movement`. **Falta el test en visor.** Plan: [`docs/stages/movement-surrounding.md`](docs/stages/movement-surrounding.md). |
| Mind, Touch, Inicio, Centro, Salida | ⚪ Vacíos | Sin empezar (Touch tiene plan y scaffold). |

**Regla al arrancar un stage nuevo:** usar **Breath como plantilla** (sensor/consumidor/manager separados, widget de instrucciones si aplica, cierre por manager + fade + transición) y crear su tracker en `skills/unreal-vr/blueprints/` desde el día 1.

🔴 **Idioma de los textos in-headset: INGLÉS.** Todas las instrucciones y textos que ve el usuario dentro de los stages van en inglés. La única excepción es **`Calibration`**, que quedó en español por ser herramienta interna de investigación, no parte de la obra.

## 4. Cómo se trabaja acá — la skill es la biblia
Todo lo operativo de Unreal está en la skill **`unreal-vr`** (`.claude/skills/unreal-vr/`), que **se auto-activa** cuando la tarea toca Unreal. No la reinventes. Estructura:
- **`SKILL.md`** — guía operativa corta (empezá por acá): cómo llamar al MCP, el workflow de Blueprints, las golden rules.
- **`references/`** (25 archivos, se cargan **a demanda, cuestan 0 hasta leerlos**) — materiales-vr, lighting-quest, dsl, nodes, toolsets, workflow, bp-practices, bp-lean-construction, bp-layout, vr, vr-pawn, input, widgets-vr, niagara-quest, audio-quest, packaging-pso, profiling-quest, motion-controller-data, motion-detection-thresholds, movement-3d-drawing, streaming-arch, gotchas, meta-quest-resources.
- **`blueprints/`** — 🗺️ **`_INDEX.md` = mapa de TODOS los Blueprints** (qué es cada uno, dónde, para qué, estado) + un **tracker por Blueprint** con el detalle (variables, estructura de grafos, qué palanca ajusta qué). 🔴 **Obligatorio: leé el índice para ubicarte y el tracker del BP ANTES de tocarlo; actualizá ambos DESPUÉS.** Modelo de tracker: `BP_BreathSensor_V2.md`.
- **`scripts/clean_orphans.py`** — limpieza de nodos huérfanos.

**Para modelado 3D existe la skill hermana `blender-3d`** (`.claude/skills/blender-3d/`): opera Blender 5.2 por el MCP oficial (server `blender`) para crear los assets de la obra — el bucle plan→partes→render→crítica, los patrones seguros de `bpy`, los presupuestos de geometría Quest y el checklist de export FBX a Unreal. ⚠ El MCP `blender` está registrado a nivel usuario (path absoluto de la máquina de Beltrán); la skill en sí es conocimiento compartido.

### 🔴 Dos reglas de oro (de la skill, no olvidar)
1. **Tokens: nunca traigas un output MCP gigante al contexto.** `describe_toolset`=72k, `find_nodes` sin filtro=146k, `get_connected_subgraph`=1.7M. Filtrá siempre (`type_id_filter`, `node_class`). Si ya está en archivo → PowerShell/Grep. Si hay que leerlo entero → subagente. Detalle en `references/workflow.md`.
2. **No re-`write_graph_dsl` un grafo que ya existe → lo DUPLICA.** Grafo nuevo/vacío = `write_graph_dsl`. Grafo existente = cirugía de nodos (`create_node`/`connect_pins`/`set_pin_value`). Y **leé el grafo antes de tocarlo.**

## 5. MCP `unreal` — setup mínimo
Manejamos Unreal por el plugin nativo **ModelContextProtocol** (server `unreal`, HTTP `localhost:8000/mcp`). Setup en [`docs/ONBOARDING.md`](docs/ONBOARDING.md). Lo esencial:
- **Unreal tiene que estar ABIERTO antes de arrancar Claude** (el MCP se conecta al inicio; si el editor no corre, las tools `unreal` no existen). Si el editor se cierra a mitad de sesión, se pierde el MCP → reiniciar Claude, dejar Unreal abierto.
- Verificá la conexión barato: `SceneTools.get_current_level`.
- `toolset_name` exige el **path completo** (`editor_toolset.toolsets.blueprint.BlueprintTools`, etc.); `tool_name` va corto. Firmas destiladas en `references/toolsets.md` (NO uses `describe_toolset`).

## 6. Estructura de carpetas
```
VR Unreal/                      ← raíz del repo (abrí Claude Code acá)
├─ CLAUDE.md                    ← este archivo
├─ README.md                    ← setup para humanos
├─ GUIA-RAPIDA.md               ← tips de usuario para gastar menos tokens
├─ Soul-Charger-*.md            ← docs de diseño (ver caveat §1)
├─ docs/                        ← contexto de equipo (onboarding, workflow, estado)
├─ .claude/skills/unreal-vr/    ← la biblia técnica (se auto-activa)
├─ .claude/skills/commit/       ← mini-skill de commit a GitHub
├─ Recursos/                    ← proyectos VR de referencia (NO se tocan, son consulta)
└─ VR_Test/                     ← EL PROYECTO UNREAL
   ├─ VR_Test.uproject          ← UE 5.8
   ├─ Config/                   ← Default{Engine,Game,Input}.ini
   └─ Content/SoulCharger/
      ├─ Stages/<Stage>/        ← un stage por carpeta
      ├─ Calibration/           ← herramienta de captura de datos
      ├─ Core/                  ← pawn, UI compartida, fades (COMPARTIDO → coordinar)
      └─ Maps/                  ← niveles (Tests/, y el hub cuando exista)
```

## 7. 🔴 Qué NO tocar sin cuidado
- **`Step` de `BP_BreathSensor_V2` / `BP_CalibProbe`**: pipeline de detección frágil, **no reescribir desde el read (es lossy)** — solo cirugía de nodos. Ver su tracker.
- **`VR_Test/Content/SoulCharger/Core/`** (pawn VR, fades, UI compartida) y **`VR_Test/Config/`**: son **compartidos entre stages** → coordinar antes de tocar (ver §8). No metas lógica de un stage en el pawn (regla del proyecto: cada mecánica en su propio BP, pawn liviano).
- **`Recursos/`**: proyectos de terceros para consulta/copia de nodos; **no se migran assets** (arrastran dependencias del VRTemplate).
- **`.uasset`/`.umap` son binarios**: no se mergean. Ver §8.

## 7.b 🔴🔴 Dos reglas de proceso que ya nos costaron tiempo real

### 1. El proyecto SIEMPRE completo en el árbol de trabajo — nunca una rama que esconda stages
**Beltrán es el dev principal y trabaja a diario, muchas veces sin Claude.** Necesita **todo** el proyecto disponible: materiales, referencias, assets y Blueprints de *todos* los stages, siempre. Una rama por stage que deje las demás carpetas vacías en disco **no sirve** para este flujo — pasó el 2026-08-03 y dejó `Stages/Movement/` vacía mientras se trabajaba Touch.

**Cómo se trabaja entonces:**
- La rama de trabajo **contiene el proyecto entero**. Si hay que traer trabajo de otra rama, se **mergea** (los stages tocan `.uasset` distintos → sin conflictos binarios; los choques son de texto y se resuelven **conservando ambas versiones**).
- **Nico solo toca Touch**, y **siempre parte de la última versión nuestra**. Nunca dos personas en el mismo stage a la vez.
- ⚠ Para mergear/cambiar de rama hay que **cerrar Unreal**: con el editor abierto los `.uasset` quedan bloqueados y git falla con `unable to unlink ... Invalid argument`, dejando el merge a medio aplicar.

### 2. ANTES de construir una interacción, buscar si ya existe en el proyecto
**Para eso está la biblia de Blueprints** (`blueprints/_INDEX.md` + trackers) y las `references/`. Repetidamente se construyó desde cero algo que ya estaba resuelto y **probado en visor** en otro BP:
- Trigger sostenido: **ya funcionaba** en Breath/Calibration (`IA_Continue` + `IMC_Continue`). Se armó uno nuevo con los **defaults** y no andaba — el que funciona usa `Priority=1000` + `bIgnoreAllPressedKeysUntilRelease=False` + `bForceImmediately=True`. Los defaults **suprimen el input**.
- Pointer láser: **ya existía** `NS_MenuLaser` (XRFramework), manejado por `User.PointArray` índice 0/1. Reusarlo salió gratis.

**El paso obligatorio:** ante "necesito un trigger / un puntero / un grab / un fade / un widget", **primero** [`references/assets-existentes.md`](.claude/skills/unreal-vr/references/assets-existentes.md) y `blueprints/_INDEX.md`, después construir. Y si algo se construye nuevo, **copiar la configuración del que ya anda**, no los valores por defecto.

🗺️ **`references/assets-existentes.md` = el inventario de lo que YA EXISTE y es reusable** (input, audio, VFX, materiales, accesores del pawn, persistencia), con el estado de cada cosa: qué está probado en visor y qué no. El `_INDEX.md` mapea Blueprints; ese archivo mapea **assets**, que es justo lo que faltaba. **Mantenerlo vivo:** cuando descubras algo reusable o valides algo en visor, agregalo ahí.

## 8. Git, deploy y trabajo en paralelo (2 devs)
Reglas completas en [`docs/WORKFLOW-EQUIPO.md`](docs/WORKFLOW-EQUIPO.md). Resumen:
- **Repo:** `github.com/beltranlihn/VR_DigitalSanctuary`, rama base `main`.
- **Cada dev trabaja en su propio stage, en su propia rama** (`stage/heart`, `stage/movement`…). Merge a `main` por PR al cerrar un hito. **Nunca dos personas editan el mismo `.uasset` a la vez** (son binarios, no se mergean → gana uno y se pierde el otro).
- **Assets compartidos** (`Core/`, pawn, `Config/`): avisar antes de tocar, serializar el trabajo.
- **Commitear HITOS, no micro-cambios** (`.uasset` binarios pesan). **Save All en Unreal ANTES de commitear** (git ve el disco, no el editor sin guardar). Mini-skill: `/commit`.
- **Empaquetar (deploy APK):** Development para trabajo/data; solo cuando una mecánica está lista para probar en device. No empaquetar por cada cambio.

## 9. Conocimiento y memoria — repo = canónico compartido
- **El conocimiento COMPARTIDO del equipo vive en el REPO** (esta doc + `docs/` + la skill `references/`/`blueprints/`). Es lo versionado y lo que ve el Claude de cualquiera. **Cuando descubras algo reusable, va acá** (PR a la skill o a `docs/`), no solo en tu memoria local.
- **La memoria de Claude Code es LOCAL por-usuario** (`~/.claude/...`): úsala para tus notas personales de sesión y preferencias. NO es el lugar del conocimiento de equipo (el otro dev no la ve).
- Al terminar de trabajar un stage/BP: **actualizá su tracker** en `blueprints/` y, si cambió el estado general, [`docs/ESTADO-STAGES.md`](docs/ESTADO-STAGES.md).

## 10. Arranque de sesión — checklist
1. Unreal abierto (proyecto `VR_Test`) **antes** de abrir Claude.
2. `SceneTools.get_current_level` para confirmar el MCP.
3. Estás en tu rama de stage (`git branch`).
4. Tarea nueva → `/clear`. Corte dentro de la misma tarea → `/compact`.
5. Antes de tocar un BP → leer su tracker en `blueprints/`.
