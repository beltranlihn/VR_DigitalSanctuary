# SC_Draw — el sistema de dibujo de Soul Charger, como plugin

El dibujo estilo Tilt Brush de la etapa Surrounding, empaquetado para usarlo en otro proyecto **sin copiarlo dentro de su Content**. El proyecto lo usa desde `/SC_Draw/`.

## Qué tiene
| Carpeta | Contenido |
|---|---|
| `Blueprints/` | `BP_TBDirector_NC` (el director: el único actor que se arrastra al nivel; usa los motion controllers del pawn poseído), `BPC_TBTool_NC` (la herramienta), `BP_TBStroke` y `BP_TBTrail_NC` (el trazo), `BP_TBPalette` + `BP_DrawPalette_SC` (la paleta: lógica y arte), `BP_TBTable` |
| `Materials/` | los pinceles (`M_TB_*`, `MI_TB_*`, `MF_TB_*`), la rueda de color, la paleta |
| `Textures/` (+ `Icons/`) | texturas de pinceles e íconos de la paleta |
| `Meshes/`, `Audio/`, `Input/` | mallas de la paleta y los mandos, sonidos propios, input del dibujo (`IA_TB_Draw_L/R`, `IA_TB_Pressure_L/R`, `IMC_TB_Draw_L/R`) |

Detalle de cada BP: `.claude/skills/unreal-vr/blueprints/BP_TBStroke.md` y `BP_DrawPalette_SC.md`.

## Qué necesita el proyecto que lo use
1. **El plugin `SC_Base`** (mandos, aparición, sonidos de interfaz, pedestal). Hay que copiarlo junto con este.
2. **XRFramework** (la plantilla VR de Unreal 5.8): el director usa `IA_Shoot_L/R`, `IA_Hand_IndexCurl_L/R` e `IMC_Weapon_L/R` de `/Game/XRFramework/Input/`. Un proyecto creado desde la plantilla VR ya los tiene.
3. Los plugins del motor `ProceduralMeshComponent` y `EnhancedInput`. Están declarados en el `.uplugin`, así que se activan solos.

## Cómo llevarlo a otro proyecto
1. Copiar `VR_Test/Plugins/SC_Base/` y `VR_Test/Plugins/SC_Draw/` a la carpeta `Plugins/` del otro proyecto (crearla si no existe).
2. Abrir el proyecto. Si no aparecen activos: Edit → Plugins → "Soul Charger" → activar los dos → reiniciar.
3. Arrastrar `BP_TBDirector_NC` al nivel (con un pawn VR). Para cerrar la etapa desde afuera: `StageRequestEnd` (llama a `TimeUp`) y leer `bStageDone`.

## Qué NO está acá (es de la obra, no del dibujo)
- La etapa Surrounding dentro de la Obra: el nivel `Test_Draw` (con el ensayo, Alma, los fantasmas de instrucción, el título y el ambiente) y el océano `BP_DrawSea_SC`. Están en `/Game/SoulCharger/Mechanics/Draw/`.
- La voz de Alma y los tiempos (los pone la Obra con la Partitura).

## Reglas
- Lo que se agregue al dibujo va **acá**, por tipo. Si es algo que otra mecánica también va a usar, va a `SC_Base`.
- **Nada de este plugin puede apuntar a `/Game/SoulCharger/`**: eso lo ataría a la obra. Verificación: `python tools/unreal/verificar_plugins.py`.
- Historia: hasta el 2026-10-02 vivía en `/Game/NeuralCanvas/` y después en `/Game/SoulCharger/Mechanics/Draw/`. El mapa de rutas está en `tools/unreal/plugin_draw_2026-10-02.json`.
