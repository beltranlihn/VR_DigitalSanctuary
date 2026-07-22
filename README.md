# Soul Charger — VR de sanación para Meta Quest 3

Obra de **VR inmersiva de meditación/sanación** para **Meta Quest 3 standalone** (Unreal Engine 5.8). Experiencia sentada, single-user, ~15 min, estética Turrell. El usuario atraviesa *stages* sensoriales donde su propio cuerpo (respiración, latido, gesto) maneja luz, sonido y forma.

> Producido por **Alma Digital Studio**. Repo privado.

---

## 🚀 Empezar en 5 minutos (con Claude Code)

Este proyecto se desarrolla con **Claude Code + el MCP nativo de Unreal**. Casi todo el trabajo en Unreal (Blueprints, niveles, materiales) lo hace Claude conduciendo el editor por el MCP.

1. **Requisitos:** Unreal Engine **5.8**, la Quest 3 con Meta Quest Link (o build por USB), Claude Code instalado.
2. **Cloná el repo** y abrí `VR_Test/VR_Test.uproject` en Unreal 5.8.
3. **Dejá Unreal abierto** (arranca solo el server MCP en `localhost:8000`).
4. **Abrí Claude Code en la raíz del repo** (la carpeta que contiene este README). Claude carga solo el contexto (`CLAUDE.md`) y la skill `unreal-vr`.
5. Verificá que el MCP conecta pidiéndole a Claude algo simple (ej. "¿qué nivel está cargado?").

👉 **Guía de setup detallada (primera vez, incluye conectar el MCP):** [`docs/ONBOARDING.md`](docs/ONBOARDING.md)

## 🧭 Por dónde empezar a leer
| Si querés… | Leé |
|---|---|
| Entender la obra, el target y las reglas | [`CLAUDE.md`](CLAUDE.md) (Claude lo lee solo) |
| Instalar y conectar todo por primera vez | [`docs/ONBOARDING.md`](docs/ONBOARDING.md) |
| Trabajar en paralelo sin pisarnos (git, ramas, deploy) | [`docs/WORKFLOW-EQUIPO.md`](docs/WORKFLOW-EQUIPO.md) |
| Ver en qué está cada stage | [`docs/ESTADO-STAGES.md`](docs/ESTADO-STAGES.md) |
| Gastar menos tokens / que Claude rinda más | [`GUIA-RAPIDA.md`](GUIA-RAPIDA.md) |
| Lo técnico de Unreal/VR (Blueprints, materiales, VR) | `.claude/skills/unreal-vr/SKILL.md` |
| La visión de diseño completa | [`Soul-Charger-Design.md`](Soul-Charger-Design.md) ⚠️ ver caveat en CLAUDE.md §1 |

## 🗂️ Estructura
- `VR_Test/` — el proyecto Unreal 5.8 (Content, Config, .uproject).
- `.claude/skills/unreal-vr/` — la "biblia" técnica: cómo operar Unreal por MCP, patrones VR, trackers por Blueprint, gotchas. Se auto-activa en Claude Code.
- `docs/` — contexto de equipo (onboarding, workflow, estado de stages).
- `Recursos/` — proyectos VR de referencia (solo consulta).

## 🎯 Estado actual (resumen)
**Breath** completo y funcional (plantilla de la obra). **Heart** en progreso. **Calibration** (herramienta de captura de datos multi-usuario) con pipeline listo. Resto de stages sin empezar. Detalle: [`docs/ESTADO-STAGES.md`](docs/ESTADO-STAGES.md).

## ⚠️ Reglas rápidas que evitan dolores
- **Quest 3 standalone**, renderer móvil, todo horneado — no es PC VR (afecta materiales/luces/config).
- `.uasset`/`.umap` son **binarios**: no se mergean. Trabajá tu stage en tu rama; no edites el mismo asset que el otro dev.
- **Save All en Unreal antes de commitear.** Commiteá hitos, no micro-cambios.
