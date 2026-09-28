# Índice de assets 3D — mapa de lo modelado en Blender

Mismo rol que `unreal-vr/blueprints/_INDEX.md`: una fila por asset, con estado y link a su tracker. **Leer antes de modelar algo nuevo** (¿ya existe?); actualizar al crear o retocar.

Estados: ⚪ planificado · 🟡 en progreso · 🟢 modelado · ✅ exportado e importado en Unreal · 👁 validado en visor

| Asset | Qué es | .blend | Estado | Tracker |
|---|---|---|---|---|
| `SM_Button_Base` + `SM_Button_Cap` | El botón VR de la obra (base con ranura de luz + cap clickeable, 2 mallas) | ⚠ sin guardar aún (sesión 2026-09-01) | 🟢 modelado, validado en viewport | [soul-button.md](soul-button.md) |
| `SM_ChargeRing_SC` (+ `M_`/`MI_ChargeRing_{Frame,Light}_SC`) | Anillo contenedor de la proto ameba: metal mate, 5 cavidades de luz (una por etapa) que se cargan, vacío central; igual por ambas caras | Headless: `VR_Test/Saved/ClaudeScripts/SM_ChargeRing_SC.blend` (lo regenera `scripts/gen_charge_ring.py`) | ✅ importado en Unreal con materiales · ⬜ veredicto y visor | [charge-ring.md](charge-ring.md) |
| `SM_PortalRoom_Shell` + `SM_PortalRoom_Ring` | Interior Turrell: sala abovedada + nicho en arco + portal circular con anillo de luz | ⚠ sin guardar aún (sesión 2026-09-01) | 🟡 modelado, falta veredicto | [portal-room.md](portal-room.md) |

## Convenciones
- Los `.blend` de trabajo viven fuera del repo (`Soul Charger VR\Modelos 3D\`); acá se versiona el **conocimiento** (tracker con parámetros, decisiones y el script de construcción), no el binario.
- Tracker por asset en `assets/<nombre>.md`: Propósito / Estado / Parámetros (las perillas) / Script de construcción o pasos / Export (settings usados, ruta en Content/) / Log de sesiones.
