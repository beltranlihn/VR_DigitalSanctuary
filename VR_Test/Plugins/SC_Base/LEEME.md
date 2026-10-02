# SC_Base — las piezas base de las mecánicas de Soul Charger

Lo que comparten las mecánicas portables. `SC_Draw`, `SC_Breath` y `SC_Sequencer` dependen de este, y lo mismo va a pasar con `SC_Heart` y `SC_Mind`. **Siempre se copia junto con cualquiera de ellos.**

## Qué tiene
| Carpeta | Contenido |
|---|---|
| `Blueprints/` | `BP_QuestCtrl_SC` (el mando de la obra: visual pasivo, `SetTrigger(0..1)`), `BPC_AppearLuz_SC` (la aparición "luz primero": `Appear()` / `Vanish()`), `BP_Anchor` (punto con etiqueta, oculto en juego) |
| `Materials/` | familia `M_SCObject_SC` / `M_SCLight_SC` / `M_SCGlass_SC` / `M_SCObjectTrans_SC` / `M_SCChargeSlider_SC`, la traza de aparición, el puntero láser (`M_Beam_SC`, `M_Pointer_SC`, `M_PointerDot_SC`), los mandos, el pedestal, la membrana (`M_HeartScape_SC`), `M_TextUnlit`, `M_ProtoSoul_Amoeba`, `MI_Ghost`, `MPC_HUD_SC`, `MPC_Perf_SC` |
| `Meshes/` | mandos nuevos (`SM_QuestCtrl_*`) y viejos (`ControllerL/R`), pedestal `SM_DrawPalette_Base_SC`, la esfera `SM_AlmaSphere`, la membrana `SM_HeartMembraneLite_SC` |
| `Audio/` | sonidos de interfaz (`VR_click1/2`, `VR_shep_scale_*`, `Charge1`, `ChargeFinal`, `ProtoHover`, `ProtoSelect`, `SBubbleHoverOn/Out`) y la atenuación `ATT_Objeto_SC` |

## Reglas
- **No depende de nada de afuera**, ni de `/Game/SoulCharger/` ni de la plantilla VR. Verificación: `python tools/unreal/verificar_plugins.py`.
- Entra acá solo lo que usan **dos mecánicas o más** y no es propio de la obra. No entran Alma (el BP), las voces, la Partitura, el Hall ni los resultados. La esfera de Alma sí entró, porque es solo la malla.
- Historia de lo que entró: `tools/unreal/plugin_draw_2026-10-02.json` y `plugin_base2_2026-10-02.json`.
