# BP_DemoCard_SC — cuadro / panel de la familia SHARE con malla y color por variables

- **refPath**: `/Game/SoulCharger/Demo/Blueprints/BP_DemoCard_SC` · **parent `BP_ShareButton_SC`** (hereda Appear/Vanish/SetHover/Press/OnConfirmed, `bStay`, AppearLuz, sonidos) · creado 2026-10-16.
- **Por qué existe**: en `BP_ShareButton_SC` las ediciones de componentes por instancia no persisten (el CS los reconstruye). El hijo aplica todo desde **variables** en su Construction Script → se ve igual en el editor y en el juego, y el menú/panel lo siguen tratando como un `BP_ShareButton_SC`.

## Variables (cat. **Card**, instance-editable)
`CardBase` / `CardPlate` / `CardSlider` / `CardTrace` (StaticMesh) · `MatBody` / `MatRing` (slots 0/1 de Base) · `MatSide` (slot 0 de Plate; el slot 1 = `TopShare` heredado) · `MatSlider` · `HitExtent` (la caja del láser, en cm).
Default del CDO = el cuadro del menú (`SM_DemoCard_*`, 300 × 190 mm, Hit (0,95; 15,2; 9,7)) en azul Entering.

## Construction Script
`SetupButton` (el del padre) → `SetStaticMesh` ×4 → `SetMaterial` ×5 → `SetBoxExtent(Hit, HitExtent)`.

## Instancias
| Nivel | Actor / tag | Malla | Color | Etiqueta |
|---|---|---|---|---|
| `L_Demo_Menu` | `CardEntering` / `demo_a` | `SM_DemoCard_*` | Entering (azul) | `MI_DemoCard_PlateTopEntering_SC` (Full: ícono + título + subtítulo) |
| `L_Demo_Menu` | `CardSurrounding` / `demo_b` | `SM_DemoCard_*` | Surrounding (verde) | `MI_DemoCard_PlateTopSurrounding_SC` |
| `L_Demo_Breath` | `InstrCard` / `demo_instr`, `bStay` | `SM_InstrCard_*` (640 × 400 mm), Hit (0,95; 32,2; 20,2) | Entering | `MI_Instr_Entering_P1..3_SC` (las cambia `BP_DemoInstr_SC`) |
| `L_Demo_Draw` | `InstrCard` / `demo_instr`, `bStay` | `SM_InstrCard_*` | Surrounding | `MI_Instr_Surrounding_P1..3_SC` |

Colores por etapa: `MI_Demo_{Body,Ring,PlateSide,Slider}_{Entering,Surrounding}_SC` (Ring/Slider `Color` y `FlashColor` = luz de la etapa: azul 0,55/0,72/1 · verde 0,45/1/0,65). Páginas: placa oscura (`Base` 0,17/0,15/0,13) con tinta hueso (variante B de Blender). Arte: `blender-3d/assets/demo-card.md` e `instr-card.md`.
| `L_Demo_Menu` | `CardRecognizing` / `demo_c` (2026-10-20) | `SM_DemoCard_*` | Recognizing (rojo 1 / 0,45 / 0,40) | `MI_DemoCard_PlateTopRecognizing_SC` (línea de pulso + RECOGNIZING + LISTEN TO YOUR HEART) |
| `L_Demo_Heart` | `InstrCard` / `demo_instr` | `SM_InstrCard2_*` | Recognizing | `MI_Instr2_Heart_P1..3_SC` + `MI_DemoInstrImg_Heart_1..3_SC` |

## 2026-10-20 (noche) — cuadros verticales del menú
`L_Demo_Menu`: los tres cuadros usan `SM_DemoCard3_{Base,Plate,Slider,Trace}_SC` (300 × 420 mm, `gen_demo_card.py --v3`), `HitExtent` (0,95; 15,2; 21,2), Y ±35, Z 180. Etiquetas `T_DemoCard3_<X>_Full` (1536 × 2195, ícono + título 18 mm + subtítulo y explicación de 11,5 mm: dos tamaños de letra) en `MaskTex` de `MI_DemoCard_PlateTop*`. Quedaron sin uso `SM_DemoCard2_*` / `T_DemoCard2_*` (360 × 300, la prueba intermedia).
Canal de luz: `MI_Demo_Ring_*` con `AppearFloor` 0,4 (ver `M_SCLight_SC`): sin línea negra durante la aparición.
🔴 **Marcos negros al aparecer/desaparecer (arreglado 2026-10-20 noche):** las mallas importadas por MCP sin materiales (`SM_DemoCard2/3_*`, y las del panel `SM_InstrCard2_*` que hizo la otra sesión) tenían todos los slots en `WorldGridMaterial`. El CS del cuadro asigna cuerpo, canal, placa y aro, pero **no el trazo**: el `Trace` quedaba con el material por defecto (iluminado, sin luz en la escena = negro) y se veía como un contorno negro grueso en la fase "luz primero". Arreglo: material por defecto en las mallas como en `SM_DemoCard_*` (trazo `M_AppearTrace_SC`, aro `MI_ShareButton_Slider_SC`, cuerpo/canal/placa los del SHARE). Verificado con capturas en PIE: el trazo dibuja el contorno en luz dorada. **Al importar una malla nueva de esta familia, asignar sus materiales por defecto.**

