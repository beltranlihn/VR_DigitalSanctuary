# CLAUDE.md — Soul Charger (VR Quest 3) · contexto maestro para Claude Code

> Este archivo lo **auto-carga Claude Code** al abrir el proyecto. Es el punto de entrada: qué es la obra, hacia dónde va, cómo se trabaja acá y qué NO romper. Lo técnico-operativo profundo vive en la **skill `unreal-vr`** (se auto-activa). Leé esto entero una vez; después consultá los punteros a demanda.

---

## 1. Qué es Soul Charger
Obra de **VR inmersiva de sanación/meditación** para **Meta Quest 3**. Experiencia **sentada, single-user, ~15 min**, estética tipo **James Turrell** (luz de color en el aire, vacíos oscuros, casi sin geometría). El usuario atraviesa **stages** (etapas) sensoriales — respiración, latido, movimiento, etc. — cada una una mini-mecánica de biofeedback/interacción corporal. No es un juego: es una experiencia contemplativa guiada.

**Objetivos de diseño:** presencia, calma, que el cuerpo del usuario (respiración, latido, gesto) **maneje** lo que ve/siente. Cada mecánica se construye para que el input físico sutil (inclinar un mando ~1°, respirar, sostener un control en el pecho) module luz/sonido/escala.

Documentos de diseño (raíz): [`Soul-Charger-Design.md`](Soul-Charger-Design.md) (visión completa), [`Soul-Charger-Plan-Reconstruccion.md`](Soul-Charger-Plan-Reconstruccion.md), [`Soul-Charger-Variables-Respiracion.md`](Soul-Charger-Variables-Respiracion.md).
> ⚠️ **El design doc es previo al pivote a Quest** y en partes está desactualizado: dice/asume **PC VR** (falso, ver §2) y referencia el *Gameplay Message Router* de Lyra (no existe en 5.8, ver `skills/unreal-vr/references/streaming-arch.md`). Donde el design doc choque con lo de abajo o con la skill, **gana la skill**.

## 2. 🔴 Target técnico — cambia TODAS las respuestas
**Meta Quest 3 STANDALONE (APK Android). NO es PC VR.** Corre el **renderer MÓVIL, forward, todo horneado.** Lumen/Nanite/Virtual Shadow Maps/Distance Fields **NO corren**. Presupuesto **72 Hz de refresh / 60 fps de render objetivo (~13.9 ms)**, **fill-rate bound**. Mitad de lo que se lee en internet asume deferred+PC y no aplica.
- **Antes de tocar config, materiales o luces** → `skills/unreal-vr/references/materials-vr.md` y `lighting-quest.md`.
- Empaquetar en **Development** para los builds de trabajo/data (Shipping recorta logs y cambia rutas de guardado).

## 3. Estado de los stages (actualizar al avanzar)
Carpetas en `VR_Test/Content/SoulCharger/Stages/`: **Breath · Heart · Mind · Movement · Touch · Inicio · Centro · Salida**. Detalle vivo en [`docs/ESTADO-STAGES.md`](docs/ESTADO-STAGES.md).

| Stage | Estado | Nota |
|---|---|---|
| **Breath** | 🟢 Completo end-to-end | **Plantilla arquitectónica** de la obra. Copiar su patrón. |
| **Heart** | 🟡 En progreso | Sensor de latido por OSC + visualizador de zona segura (debug). |
| **Calibration** (herramienta) | 🟢 Pipeline listo, falta test en visor | Nivel de captura de datos multi-usuario (`Content/SoulCharger/Calibration/`). No es un stage de la obra: es tooling de investigación. |
| Mind, Movement, Touch, Inicio, Centro, Salida | ⚪ Vacíos | Sin empezar. |

**Regla al arrancar un stage nuevo:** usar **Breath como plantilla** (sensor/consumidor/manager separados, widget de instrucciones si aplica, cierre por manager + fade + transición) y crear su tracker en `skills/unreal-vr/blueprints/` desde el día 1.

## 4. Cómo se trabaja acá — la skill es la biblia
Todo lo operativo de Unreal está en la skill **`unreal-vr`** (`.claude/skills/unreal-vr/`), que **se auto-activa** cuando la tarea toca Unreal. No la reinventes. Estructura:
- **`SKILL.md`** — guía operativa corta (empezá por acá): cómo llamar al MCP, el workflow de Blueprints, las golden rules.
- **`references/`** (25 archivos, se cargan **a demanda, cuestan 0 hasta leerlos**) — materiales-vr, lighting-quest, dsl, nodes, toolsets, workflow, bp-practices, bp-lean-construction, bp-layout, vr, vr-pawn, input, widgets-vr, niagara-quest, audio-quest, packaging-pso, profiling-quest, motion-controller-data, motion-detection-thresholds, movement-3d-drawing, streaming-arch, gotchas, meta-quest-resources.
- **`blueprints/`** — 🗺️ **`_INDEX.md` = mapa de TODOS los Blueprints** (qué es cada uno, dónde, para qué, estado) + un **tracker por Blueprint** con el detalle (variables, estructura de grafos, qué palanca ajusta qué). 🔴 **Obligatorio: leé el índice para ubicarte y el tracker del BP ANTES de tocarlo; actualizá ambos DESPUÉS.** Modelo de tracker: `BP_BreathSensor_V2.md`.
- **`scripts/clean_orphans.py`** — limpieza de nodos huérfanos.

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
