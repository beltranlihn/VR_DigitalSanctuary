# VR Unreal — Alma Digital Studio

Un solo proyecto de Unreal Engine 5.8 (`VR_Test/`) con tres experiencias de VR standalone (Meta Quest; Inner Canvas también en PICO):

| Experiencia | Qué es | Entregada |
|---|---|---|
| **Soul Charger · la Obra** | VR de sanación sentada, ~15 min: Hall + 5 etapas (respiración, latido, mente, música, dibujo) guiadas por Alma | — |
| **Digital Sanctuary · la demo** | demo corta para ferias, bilingüe, con sensor Muse y una pantalla de Windows | `Projects/Packagings/Digital Sanctuary V1.0` (BCN Design Week, oct 2026) |
| **Inner Canvas** | dibujo de pie para varios visores a la vez + un PC que muestra los dibujos en vivo | `Projects/Packagings/Inner Canvas v1.0` (evento, 13-11-2026) |

> Producido por **Alma Digital Studio**. Repo privado `github.com/beltranlihn/VR_DigitalSanctuary`, rama `core/esqueleto`.

## Qué hay en esta carpeta

| Carpeta / archivo | Qué es |
|---|---|
| `CLAUDE.md` | el contexto que Claude Code lee al abrir el proyecto: qué es la obra, el target técnico, qué no romper. **Empezar acá** |
| `VR_Test/` | **el proyecto Unreal** (Content, Config, Plugins, `.uproject`). Mapa completo: [`docs/MAPA-DEL-PROYECTO.md`](docs/MAPA-DEL-PROYECTO.md) |
| `docs/` | documentación vigente (índice en [`docs/README.md`](docs/README.md)); `docs/historia/` = planes e informes viejos; `docs/investigacion/` = investigaciones |
| `tools/` | scripts: `unreal/` (prueba de humo, empaquetar, instalar, dependencias, archivar), `innercanvas/`, `demo/`, `editor/` + `score/` (editor web), `pieeg/` (sensor EEG), `bp_fuentes/` (fuentes de los Blueprints escritos por script) |
| `.claude/skills/` | las skills de Claude Code: `unreal-vr` (la biblia técnica de Unreal), `blender-3d`, `commit` |
| `web/` | **Veation VR Studio**, el editor web de los tiempos de la obra (`web/editor-obra`), y el prototipo narrativo web |
| `obra/` | la partitura de la obra que usa el editor web (`score/`), el mapa de sus sonidos (`audio/`) y su enlace con Unreal (`unreal/`) |
| `Recursos/` | material de trabajo: audio, música, marca, 3D, referencias, la instalación de feria y la última copia de cada build ([`Recursos/LEEME.md`](Recursos/LEEME.md)) |
| `EEG Alma Center/` | proyecto aparte con **su propio repo** (`github.com/beltranlihn/EEG_Alma_Center`); no es parte de este repo |
| `_Deprecated/` | lo archivado fuera del proyecto Unreal (assets sin uso, niveles viejos, mediciones de septiembre). Local, fuera de git; cada tanda tiene su manifiesto |
| `.mcp.json` | los servidores MCP del proyecto (Unreal, Blender) |

Fuera de esta carpeta, en `Projects/Packagings/`: las versiones entregadas (APK + build de Windows + LEEME).

## Empezar
1. Unreal Engine **5.8**, Claude Code y un Quest por USB con depuración.
2. Abrir `VR_Test/VR_Test.uproject` y dejarlo abierto (levanta el servidor MCP en `localhost:8000`).
3. Abrir Claude Code en esta carpeta: carga `CLAUDE.md` y la skill `unreal-vr`.

Guía detallada de la primera vez: [`docs/ONBOARDING.md`](docs/ONBOARDING.md). Git, ramas y empaquetado: [`docs/WORKFLOW-EQUIPO.md`](docs/WORKFLOW-EQUIPO.md).

## Reglas rápidas
- **Quest standalone**: renderer móvil, todo horneado; no es PC VR.
- `.uasset`/`.umap` son **binarios**: no se mergean. Nunca dos personas en el mismo asset.
- **Save All en Unreal y `python tools/unreal/smoke_obra.py` en OK antes de commitear un hito** (mini-skill `/commit`).
- Los builds no van al repo: las copias quedan en `Recursos/` y las versiones entregadas en `Projects/Packagings/`.
