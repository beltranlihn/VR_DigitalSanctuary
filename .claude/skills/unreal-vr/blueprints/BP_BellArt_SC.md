# BP_BellArt_SC · BP_SaveMelodyArt_SC · BP_BioSensorArt_SC — el ARTE del timbre, del botón SAVE MELODY y del sensor

- **Rutas**: `Mechanics/Bell/BP_BellArt_SC` · `Mechanics/SaveMelody/BP_SaveMelodyArt_SC` · `Mechanics/BioSensor/BP_BioSensorArt_SC`.
- **Estado**: 🟢 creados y guardados (2026-09-30) · ⬜ PIE · ⬜ visor · ⬜ integración a su lógica.
- **Son solo arte + aparición**. La lógica ya existe en otros BP: `BP_Bell` (Core/Doors), `BP_SaveMelody_SC` y los rigs de respiración y latido. La integración (apretar, cargar, en zona) se hace cuando la pidan.
- **Modelos**: `blender-3d/assets/bell.md`, `save-melody.md` y `bio-sensor.md`. La aparición está en `aparicion-luz.md`.

## Componentes (StaticMesh, sin sombra, sin colisión; todos colgados del DefaultSceneRoot)
| BP | Cuerpo (`AppearBody`) | Pieza que asoma (`AppearMover`) | Otros | Trazo (`AppearTrace`) |
|---|---|---|---|---|
| Timbre | `Base` = `SM_Bell_Base_SC` | `Button` = `SM_Bell_Button_SC` | `Slider` (sin tag) | `Trace` = `SM_Bell_Trace_SC` |
| SAVE | `Base` = `SM_SaveMelody_Base_SC` | `Plate` = `SM_SaveMelody_Plate_SC` | `Slider` (sin tag) | `Trace` = `SM_SaveMelody_Trace_SC` |
| Sensor | `Body` = `SM_BioSensor_SC` | `Button` = `SM_BioSensor_Button_SC` (punta de luz) | `Waves` = `SM_BioSensorWaves_SC` (`AppearLate`) | `Trace` = `SM_BioSensor_Trace_SC` |

Más `Appear` (`BPC_AppearLuz_SC`):

| BP | `FaceAxis` | `PivotDepth` (cm) | `MoverHide` (cm) |
|---|---|---|---|
| Timbre | (0,0,1) | 4,41 | (0,0,−1,9) |
| SAVE | (0,0,1) | 1,5 | (0,0,−1,2) |
| Sensor | (0,0,−1) | 0,608 | (0,0,1,7) |

## Materiales (`Mechanics/Appear/` + MI por objeto)
- `M_SCObject_SC`: hormigón de la familia.
  - Sombreado falso: `SCObjectShadePS` = `DrawPaletteShadePS` + `Flash` × `FlashColor`.
  - Máscara `MaskTex` por UV1: el texto del SAVE.
- `M_SCLight_SC`: cintas de luz, `Color` × `Glow` × `AppearGlow`.
  - `Glow` es el brillo de reposo del objeto; el BP lo sube al apretar.
  - `AppearGlow` es el de la aparición.
- `M_SCChargeSlider_SC`: el slider transparente (aditivo), con `Progress` 0..1.
- `M_AppearTrace_SC`: el trazo (aditivo, dos caras).
- `M_BioSensorWaves_SC` (en BioSensor/): los aros, con `Active` (el juego) y `AppearGlow` (la aparición).
- Instancias:
  - timbre: Body, Face, Pocket, ButtonSide, ButtonTop, Ring (Glow 0,7) y Slider;
  - SAVE: Body, PlateSide, PlateTop (con `T_SaveMelody_Text`), Ring (0,7) y Slider;
  - sensor: Body, Face, Grip, Button, Ring (1), BackRing (0,9) y TipLight (1).
- Fuente: `scripts/plan_sc_materials.py` → `apply_sc_materials.py`, idempotentes. El HLSL está en `scripts/hlsl/`.

## Pendientes
- [ ] Nivel de prueba y ver la aparición en PIE, antes de la integración.
- [ ] Sonidos: `Appear.AppearSound` / `VanishSound`, con los FX_* que pone Beltrán.
- [ ] El timbre al apretar: `Button` baja 10 mm, `Ring.Glow` = 0,7 + 0,9·press y `Slider.Progress` = la carga. Lo mismo para el SAVE (4 mm, texto encendido en hover).
- [ ] El destello del bolsillo del timbre que tapa el nacimiento del botón (está en Blender; acá falta el tag o un escalar).

## Correcciones (2026-09-30, Beltrán en el editor)
- **Botón del timbre "con la cara abierta"**: la malla salió dada vuelta entera, por un perfil en sentido horario (`blender-3d/references/gotchas.md` §38). Se corrigió en `gen_bell.py` y se reimportó.
  - 🔴 `StaticMeshTools.import_file` **no sobreescribe** (*"already exists"*). Receta que funcionó:
    1. importar con nombre temporal (`SM_Bell_ButtonNew_SC`) y asignarle los slots;
    2. apuntar el componente del BP a la malla nueva y guardar el BP;
    3. `get_referencers` de la vieja → vacío → `delete`;
    4. `move` de la nueva al nombre original. El BP la sigue.
- **Los aros del sensor iban hacia adentro**: Unreal invierte la V del FBX (§39). `BioSensorWavesPS` v5 usa `1 − UV.y`.
  - 🔴 `AssetTools.read_file` solo lee dentro de `VR_Test/Content` o `VR_Test/Saved` (y plugins); **no** de `.claude/skills`. Un `read_file` fallido dejó `Code` = None → el Custom quedó **vacío** y el material no compiló, sin Undo. Para pasar HLSL a un script: copiarlo a `Saved/ClaudeScripts/...` o escribirlo inline.


## 2026-09-30 (noche): el SAVE integrado a su lógica (sesión Secuencer)
- `BP_SaveMelody_SC` (la lógica que el rig monta en la mano no dominante) **spawnea en runtime** un `BP_SaveMelodyArt_SC` y se lo cuelga (`ArtEnsure`, sin agregar componentes al BP colocado — gotchas 164/320), le llama `Appear.Prepare()` y esconde el disco y el texto viejos (el disco queda como colisión invisible para el láser, 16 cm a escala 1).
- `ArtTick` (desde `ScaleLabel`, al final de `UpdateVisual`): `ArtFace` (el botón mira siempre a la cámara, escala `ArtScale` 1, giro extra `ArtRot`) · `ArtSmooth` (PressT/ProgT suavizados, Dt ≤ 1/30: sin saltos de un cuadro) · aparece/desaparece con `Appear()`/`Vanish()` · sonidos: aparición y hover `SBubbleHoverOn`, carga `Charge1` (se apaga en fundido con `ChargeVolume`), completo `ChargeFinal`, salida `SBubbleHoverOut` · `ArtPush`: `Base.Glow` 0,25-0,7 disponible / 1,0 hover / 1,7 apretado · `Plate.Ink` hueso→cálido e `InkGlow` 0,35→1 · `Slider.Progress` = la carga · `Plate` +1 mm hover / −4 mm apretado (solo con `AppearT` = 1, para no pelear con la aparición).
- ⬜ Visor: tamaño y orientación en la mano (perillas `ArtScale` / `ArtRot` en la instancia de `BP_SaveMelody_SC`).
