# CLAUDE.md — Soul Charger (VR Quest 3) · contexto maestro para Claude Code

> Este archivo lo **auto-carga Claude Code** al abrir el proyecto. Es el punto de entrada: qué es la obra, cómo está armada, cómo se trabaja y qué NO romper. Lo técnico-operativo profundo vive en la **skill `unreal-vr`** (se auto-activa). Léelo entero una vez; después consulta los punteros a demanda.

---

## 1. Qué es Soul Charger
Obra de **VR inmersiva de sanación/meditación** para **Meta Quest 3**. Experiencia **sentada, single-user, ~15 min**, estética tipo **James Turrell** (luz de color en el aire, vacíos oscuros, casi sin geometría). El usuario pasa por un Hall y **5 etapas** — Entering (respiración), Recognizing (latido), Loving (mente/EEG), Attracting (secuenciador musical), Surrounding (dibujo 3D) — y un final con resultados, compartir y constelación. No es un juego: es una experiencia contemplativa guiada por **Alma**.

🔴 **Documento maestro de la obra:** [`docs/OBRA-SOUL-CHARGER.md`](docs/OBRA-SOUL-CHARGER.md) y el guion vigente [`docs/GUION-V5-2026-09-29.md`](docs/GUION-V5-2026-09-29.md). Los design docs de la raíz (`Soul-Charger-*.md`) son previos al pivote a Quest: donde choquen con esto o con la skill, **gana la skill**.

🔴 **Idioma de los textos in-headset: INGLÉS.** Todo lo que ve el usuario dentro de la obra va en inglés.

## 2. 🔴 Target técnico — cambia TODAS las respuestas
**Meta Quest 3 STANDALONE (APK Android). NO es PC VR.** Renderer **móvil, forward, todo horneado.** Lumen/Nanite/Virtual Shadow Maps/Distance Fields **no corren**. Presupuesto **72 Hz** (~13,9 ms), **fill-rate bound**.
- Antes de tocar config, materiales o luces → `skills/unreal-vr/references/materials-vr.md` y `lighting-quest.md`.
- Empaquetar en **Development** (Shipping recorta logs y cambia rutas de guardado).

## 3. 🎬 ESTADO ACTUAL (desde 2026-09-30): la OBRA
🔴 **El nivel de trabajo y del APK es `/Game/SoulCharger/Obra/L_SoulCharger_Obra`.** El editor arranca ahí.
- **El director** es `BP_Obra_SC`: lleva el reloj y las fases (Hall → 5 etapas → final → créditos).
- **Las celdas son los niveles de test** de cada etapa (`Test_Entering`, `Test_Heart`, `Test_Fluid`, `Test_Sequencer`, `L_TBTest_SC`, `Test_Hall`), cargados con `LoadLevelInstance`. Lo que se ajusta en un nivel de test es lo que se ve en la Obra. Los actores con tag `TestOnly` se descartan al arrancar.
- **Cada nivel de test tiene su ensayo** (`BP_StageRunner_SC`): Play en el nivel y la etapa corre como en la Obra, con los mismos tiempos.

🧭 **Cómo se administra la obra (qué se cambia dónde, cómo probar, checklist de público): [`docs/GUIA-DE-DIRECCION.md`](docs/GUIA-DE-DIRECCION.md).** Resumen de las cuatro preguntas:
| Pregunta | Dónde |
|---|---|
| **¿Cuándo?** (todos los tiempos narrativos) | `DA_Partitura_Obra` → [`docs/PARTITURA.md`](docs/PARTITURA.md) |
| **¿Dónde?** (Alma, la carga, el título de cada etapa) | TargetPoints `sc<K>_*` en el nivel de test de la etapa |
| **¿Cómo se ve y se siente una mecánica?** | sus perillas, en su nivel de test → [`docs/PERILLAS.md`](docs/PERILLAS.md) |
| **¿Color del velo de cada etapa?** | `CTop`/`CHor` del ensayo de su nivel |

**El contrato de etapa** (el director nunca fuerza el final, lo pide): `StageIntro()` · `StageBegin()` · **`StageRequestEnd()`** (a `Etapa_Tope`: la etapa cierra por su propio camino) · `bStageDone` · `StageOutro()`. Detalle en la guía §4.

**Antes de cada commit grande o APK: `python tools/unreal/smoke_obra.py`** (prueba de humo de la obra entera, sin visor, ≈9 min). Tiene que dar OK.

| Etapa | Estado (2026-10-02) |
|---|---|
| Hall (inicio, regreso, salida) | 🟢 en la Obra; visor ✓ |
| Entering (respiración) | 🟢 en la Obra; visor ✓ |
| Recognizing (latido) | 🟢 en la Obra; latido de respaldo sin sensor |
| Loving (mente) | 🟢 en la Obra |
| Attracting (secuenciador) | 🟢 en la Obra; SAVE al pedido de cierre |
| Surrounding (dibujo) | 🟢 en la Obra; corte con presentación (arreglo 10-02, falta visor) |
| Final: resultados, SHARE, constelación, créditos | 🟢 en la Obra |

La historia (V1 `Maps/L_Persistent`, V2 `MapsV2`, V3 `MapsV3`, la galería, calibración, Touch) **ya no está en el proyecto**: quedó en `_Deprecated/Content-2026-10-02/` y en el tag `respaldo-pre-reorden-2026-10-02`. Ver [`docs/AUDITORIA-ESTRUCTURA-2026-10-02.md`](docs/AUDITORIA-ESTRUCTURA-2026-10-02.md).

## 4. Cómo se trabaja acá — la skill es la biblia
Todo lo operativo de Unreal está en la skill **`unreal-vr`** (`.claude/skills/unreal-vr/`), que **se auto-activa** cuando la tarea toca Unreal:
- **`SKILL.md`** — guía operativa corta (empieza por acá): cómo llamar al MCP, el workflow de Blueprints, las golden rules.
- **`references/`** — se cargan a demanda: materials-vr, lighting-quest, dsl, toolsets, workflow, gotchas, etc.
- **`blueprints/`** — 🗺️ **`_INDEX.md` = mapa de los Blueprints vivos** + un **tracker por Blueprint**. 🔴 Lee el tracker del BP **antes** de tocarlo y actualízalo **después**.
- 🔴 **[`docs/REGLAS-DE-ORO.md`](docs/REGLAS-DE-ORO.md)**: las reglas cortas que muerden a cualquiera (las 580 gotchas completas quedan como archivo de consulta).

**Skill hermana `blender-3d`** (`.claude/skills/blender-3d/`): opera Blender por el MCP `blender` para crear los assets de la obra.

### 🔴 Reglas de oro del MCP
1. **Tokens: nunca traigas un output MCP gigante al contexto.** Filtra siempre (`type_id_filter`, `node_class`). Volcados largos → a un archivo con `AssetTools.write_file` y Grep.
2. **No re-`write_graph_dsl` un grafo que ya existe → lo DUPLICA.** Grafo nuevo/vacío = `write_graph_dsl`. Grafo existente = cirugía de nodos. Lee el grafo antes de tocarlo.
3. **Cambios de estructura de un BP (variables, funciones) con un nivel neutro abierto** (`Test_QuestCtrl`), nunca con el nivel donde está colocado (gotcha 402: el reinstanciado se lleva el actor).
4. **Un tiempo de la obra no se escribe como número en un grafo**: va a la Partitura (guía §7).

## 5. MCP `unreal` — setup mínimo
Plugin nativo **ModelContextProtocol** (server `unreal`, HTTP `localhost:8000/mcp`). Setup en [`docs/ONBOARDING.md`](docs/ONBOARDING.md).
- Unreal tiene que estar abierto. Si el editor se reinicia, el MCP vuelve a conectar solo; si el puerto 8000 no abre, revisar `bAutoStartServer=True` en `VR_Test/Saved/Config/WindowsEditor/EditorPerProjectUserSettings.ini` (un proceso `-game` o un cocinado puede dejarlo en False).
- Verifica la conexión barato: `SceneTools.get_current_level`.
- `toolset_name` exige el **path completo** (`editor_toolset.toolsets.blueprint.BlueprintTools`, etc.); `tool_name` va corto. Firmas en `references/toolsets.md`.

## 6. Estructura de carpetas
```
VR Unreal/                      ← raíz del repo
├─ CLAUDE.md                    ← este archivo
├─ docs/                        ← GUIA-DE-DIRECCION, PARTITURA, PERILLAS, REGLAS-DE-ORO, WORKFLOW-EQUIPO, guion, auditorías
├─ tools/unreal/                ← prueba de humo, probar un nivel, empaquetar, instalar en el Quest, dependencias, archivo
├─ .claude/skills/unreal-vr/    ← la biblia técnica (se auto-activa)
├─ web/                         ← prototipo narrativo web y editor de la obra
├─ Recursos/                    ← material de trabajo y referencias (no se versiona lo pesado)
├─ _Deprecated/                 ← assets archivados fuera del proyecto (local, ignorado por git)
└─ VR_Test/                     ← EL PROYECTO UNREAL (UE 5.8)
   ├─ Config/                   ← Default{Engine,Game,Input}.ini (el APK cocina solo la Obra y sus celdas)
   └─ Content/
      ├─ SoulCharger/Obra/      ← director, Partitura, nivel final, ensayos, títulos, voces
      ├─ SoulCharger/Mechanics/ ← una carpeta por mecánica, con su nivel de test
      ├─ SoulCharger/Core/      ← piezas compartidas vivas (Alma, pawn, alma del usuario, BioHub, audio, luz) → coordinar
      ├─ NeuralCanvas/          ← el dibujo (autocontenido) + L_TBTest_SC
      ├─ Test_Entering/Heart/Fluid/Sequencer.umap ← celdas de 4 etapas (raíz por historia; la Obra las carga por ruta)
      └─ XRFramework/, XRMannequins/ ← base VR (GameMode, input, manos)
```

## 7. 🔴 Qué NO tocar sin cuidado
- **Los grafos de `BP_Obra_SC`**: para ajustar tiempos está la Partitura. Si hay que tocarlos, leer el tracker y correr la prueba de humo después.
- **`Core/`** (pawn, Alma, alma del usuario) y **`VR_Test/Config/`**: compartidos → coordinar antes de tocar. El pawn queda liviano: cada mecánica en su propio BP.
- **`.uasset`/`.umap` son binarios**: no se mergean. Nunca dos personas en el mismo `.uasset` a la vez.
- **Colocar actores sí; sacarlos se pregunta.** Contar actores antes y después de cada tanda de scripts.

## 7.b 🔴🔴 Dos reglas de proceso que ya costaron tiempo real
1. **El proyecto SIEMPRE completo en el árbol de trabajo.** La rama de trabajo contiene el proyecto entero; si hay que traer trabajo de otra rama, se mergea. Para mergear/cambiar de rama hay que **cerrar Unreal** (los `.uasset` abiertos quedan bloqueados).
2. **Antes de construir una interacción, buscar si ya existe**: [`references/assets-existentes.md`](.claude/skills/unreal-vr/references/assets-existentes.md), `blueprints/_INDEX.md` y [`docs/MECANICAS-PORTABLES.md`](docs/MECANICAS-PORTABLES.md). Si se construye algo nuevo, se copia la configuración del que ya anda, no los valores por defecto.

## 8. Git, deploy y trabajo en equipo
Reglas completas en [`docs/WORKFLOW-EQUIPO.md`](docs/WORKFLOW-EQUIPO.md). Resumen:
- **Repo:** `github.com/beltranlihn/VR_DigitalSanctuary`. Rama de trabajo: `core/esqueleto`.
- **Commitear hitos**, con la prueba de humo en OK. **Save All en Unreal antes de commitear.** Mini-skill: `/commit`.
- **APK:** `python tools/unreal/empaquetar_obra.py [--variante v2]` → `powershell -File tools/unreal/instalar_quest.ps1 [-Variante v2]`. Antes, el checklist de público de la guía §6.

## 9. Conocimiento y memoria — repo = canónico compartido
- El conocimiento compartido vive en el **repo** (esta doc, `docs/`, la skill). Cuando descubras algo reusable, va acá.
- La memoria de Claude Code es **local por usuario**: notas de sesión y preferencias, no conocimiento de equipo.
- Al terminar de trabajar un BP: actualiza su tracker en `blueprints/`.

## 10. Arranque de sesión — checklist
1. Unreal abierto (proyecto `VR_Test`).
2. `SceneTools.get_current_level` para confirmar el MCP.
3. `git branch` / `git status` para saber dónde estás.
4. Tarea nueva → `/clear`. Corte dentro de la misma tarea → `/compact`.
5. Antes de tocar un BP → su tracker. Después de tocarlo → prueba de humo.
