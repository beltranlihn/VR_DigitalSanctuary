# SC_Base — las piezas base de las mecánicas de Soul Charger

Lo que comparten las mecánicas portables. Cada plugin de mecánica (`SC_Draw`, y en el futuro `SC_Breath`, `SC_Heart`, `SC_Mind` y `SC_Sequencer`) depende de este.

## Qué tiene
| Carpeta | Contenido |
|---|---|
| `Blueprints/` | `BP_QuestCtrl_SC` (el mando de la obra: visual pasivo, `SetTrigger(0..1)`), `BPC_AppearLuz_SC` (la aparición "luz primero": `Appear()` / `Vanish()`) |
| `Materials/` | familia `M_SCObject_SC` / `M_SCLight_SC` / `M_SCGlass_SC` / `M_SCObjectTrans_SC` / `M_SCChargeSlider_SC`, la traza de aparición, los mandos, el pedestal, `MPC_HUD_SC` |
| `Meshes/` | mandos nuevos (`SM_QuestCtrl_*`) y viejos (`ControllerL/R`), pedestal `SM_DrawPalette_Base_SC` |
| `Audio/` | sonidos de interfaz (`VR_click1/2`, `VR_shep_scale_*`) y la atenuación `ATT_Objeto_SC` |

Detalle: `.claude/skills/unreal-vr/blueprints/BP_QuestCtrl_SC.md` y `BPC_AppearLuz_SC.md`.

## Reglas
- **No depende de nada de afuera.** Ni de `/Game/SoulCharger/` ni de XRFramework. Así se mantiene: verificación con `python tools/unreal/verificar_plugins.py`.
- Entra acá solo lo que usan **dos mecánicas o más** y no es propio de la obra. No van Alma, las voces, la Partitura, el Hall ni los resultados, que son de la obra.
- Para usarlo en otro proyecto: copiar `Plugins/SC_Base/` a la carpeta `Plugins/` del otro proyecto (ver `SC_Draw/LEEME.md`).
