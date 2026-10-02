# SC_Breath — el sistema de respiración de Soul Charger, como plugin

La respiración de la etapa Entering empaquetada para usarla en otro proyecto. El proyecto la usa desde `/SC_Breath/`. Son tres piezas que **no se conocen entre sí**; las une quien las hospeda (en la obra, `BP_BreathStage_SC`).

## Qué tiene
| Pieza | Qué hace | Tracker |
|---|---|---|
| `Blueprints/BP_BreathRig_SC` | El sensor: el mando apoyado en la panza detecta la respiración (umbral con la orientación del sensor, vibración, seguidor con frenada física). Validado en visor. | `BP_BreathRig_SC.md` |
| `Blueprints/BP_BreathBlob_SC` + `Materials/M_BreathBlob_SC` | El metaball que respira con el usuario | `BP_BreathBlob_SC.md` |
| `Blueprints/BP_Pacer_SC` + `Materials/M_Pacer_SC`, `MI_Pacer_SC` | La guía de respiración (reloj de fases, 3 estéticas) y sus sonidos en `Audio/` | `BP_Pacer_SC.md` |
| `Materials/MPC_Breath` | Los valores de la respiración para cualquier material (el valle, el aliento y los haces de luz de la obra lo leen) | |
| `Meshes/BreathL`, `BreathR`, `Materials/M_BreathCtrl_SC` | Los mandos de respiración | |

## Qué necesita el proyecto que lo use
1. El plugin **`SC_Base`** (copiarlo junto con este).
2. **XRFramework y XRMannequins** (la plantilla VR de Unreal 5.8): el sensor usa la háptica `GrabHapticEffect` y las manos `SKM_MannyXR_left/right`.

## Cómo llevarlo a otro proyecto
Copiar `Plugins/SC_Base/` y `Plugins/SC_Breath/` a la carpeta `Plugins/` del otro proyecto, activarlos, poner `BP_BreathRig_SC`, `BP_BreathBlob_SC` y `BP_Pacer_SC` en el nivel. Para unirlos, hace falta un orquestador propio, o copiar la lógica de `BP_BreathStage_SC`, que los encuentra por clase (`GetActorOfClass`).

## Qué NO está acá (es de la obra)
La etapa Entering (`/Game/SoulCharger/Mechanics/Breath/`): el orquestador con las voces de Alma (`BP_BreathStage_SC`), el valle, el aliento visible y la capa de vida, y el nivel `Test_Breath`.

Regla: nada de este plugin apunta a `/Game/SoulCharger/` → `python tools/unreal/verificar_plugins.py`. Mapa de rutas: `tools/unreal/plugin_breath_2026-10-02.json`.
