# SC_Sequencer — el secuenciador musical de Soul Charger, como plugin

La mecánica de la etapa Attracting entera: orbes de sonido que se atraen, slots, la cadena de metaballs, los mandos con láser, el salar de Chladni y el botón de guardar la melodía. El proyecto la usa desde `/SC_Sequencer/`.

## Qué tiene
| Pieza | Qué hace | Tracker |
|---|---|---|
| `Blueprints/BP_Sequencer_SC` | El director de la mecánica. Implementa el **contrato de etapa** (`StageIntro`, `StageBegin`, `StageRequestEnd`, `StageOutro`, `bStageDone`): si hay melodía al pedido de cierre, la guarda; si no, cierra | `BP_Sequencer_SC.md` |
| `BP_SeqRig_SC` | Los mandos y el láser | `BP_SeqRig_SC.md` |
| `BP_OrbDirector_SC`, `BP_SoundOrb_SC`, `BP_SeqSlot_SC`, `BP_BlobChain_SC` | Orbes, slots y la cadena | `BP_OrbDirector_SC.md`, `BP_BlobChain_SC.md` |
| `BP_ChladniFloor_SC` | El salar de Chladni (a 72 fps) | `BP_ChladniFloor_SC.md` |
| `BP_SaveMelody_SC` + `BP_SaveMelodyArt_SC` | El botón SAVE MELODY (lógica y arte) | |
| `Materials/`, `Meshes/`, `Audio/`, `Textures/`, `VFX/` | Todo lo que usan (los Niagara `NS_OrbAttract_SC` y `NS_OrbHalo_SC` incluidos) | |

## Qué necesita el proyecto que lo use
1. El plugin **`SC_Base`**: sonidos de interfaz, puntero láser, ancla, esfera, la malla de la membrana para el Chladni y el MPC de rendimiento.
2. **XRFramework** (plantilla VR de Unreal 5.8): el input `IA_Shoot_L/R`, `IA_Hand_IndexCurl_L/R`, `IMC_Weapon_L/R` y la háptica `GrabHapticEffect`.
3. Los plugins del motor **Niagara** y **EnhancedInput** (declarados en el `.uplugin`).

## Cómo llevarlo a otro proyecto
Copiar `Plugins/SC_Base/` y `Plugins/SC_Sequencer/` a `Plugins/` del otro proyecto, activarlos y armar el nivel como `Test_Sequencer`: el director, el rig, los slots y el piso. Sin un director de obra, la mecánica arranca sola. Con la etiqueta `TOUR` en un actor del nivel, espera a que la llamen.

## Qué NO está acá (es de la obra)
El nivel `Test_Sequencer` (con el ensayo, Alma, los fantasmas de instrucción y el título), en `/Game/SoulCharger/Mechanics/Sequencer/Maps/`.

Regla: nada de este plugin apunta a `/Game/SoulCharger/` → `python tools/unreal/verificar_plugins.py`. Mapa de rutas: `tools/unreal/plugin_sequencer_2026-10-02.json`.
