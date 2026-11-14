# SM_Hang_* — el HANG (handpan) del instrumento de BP_Harp_SC

## Propósito
Pedido de Beltrán (2026-10-28), con fotos de un handpan electrónico de madera de 9 pads negros (8 alrededor + el *ding* central): *"cambiar el tipo de instrumento dentro del BP; mismos sintes, otro formato. Modelarlo en 3D con cada botón como mesh independiente para hacerlo pulsar con cada toque"*. Y después: *"debe ser de la estética de los meshes de Soul Charger, como la paleta de Drawing"*.
Por eso no es madera: lleva el **hormigón de la paleta** (`M_DrawPalette_SC`) y la **luz en la hendidura del timbre** (`gen_bell.py`). Cada pad es un botón con hendidura suave dentro de su bolsillo, y por la ranura de 3,5 mm se ve su costado, que brilla con el color de su nota.

## Estado
✅ Modelado, importado (`/Game/SoulCharger/Mechanics/Harp/Meshes/`) y montado en `BP_Harp_SC` (`InstrumentType` = 1). ⬜ Veredicto de Beltrán · ⬜ visor.

## Medidas (mm; constantes al principio de `scripts/gen_hang.py`)
| | |
|---|---|
| Cuerpo | Ø 524 (cuenco R 258 + labio-junta de 4 × 12), alto 175 después del bolsillo del ding (180 sin él). Cuenco = superellipse n 2,6 de 104 mm; cúpula = casquete esférico de 63 mm (R esfera 552) |
| Pads | 8 de Ø 94 a 175 mm del eje (22,5° + 45°·k), con el eje según la normal de la cúpula (16-18°); ding Ø 144 en la cima con cupulita central (R 30, +5,5) y anillo hundido |
| Pad | asoma 3,5 sobre la cúpula y entra 9 debajo; canto r 4; hendidura parabólica de 3 mm hasta 0,74 R |
| Bolsillo | R + 3,5 mm (la ranura), 16 de fondo por el eje del pad; boca redondeada r 1,6. Recorrido del pad en el BP: hasta 5 mm |

## Mallas
- `SM_Hang_Body_SC` (17,6 k tris): origen en el centro del piso. Slots `M_Hang_Body` · `M_Hang_Pocket` (paredes) · `M_Hang_Groove` (fondo).
- `SM_Hang_Pad_SC` / `SM_Hang_Ding_SC` (2,1 k tris cada uno): **origen = el punto de la cúpula en su eje, +Z = la normal**. Hundirlo = moverlo en −Z local. Slots `M_Hang_PadTop` (hormigón) · `M_Hang_PadSide` (la luz, de la superficie hacia abajo).
- `hang_pads.json`: transformada de cada pad en cm y en ejes de **Unreal (Y espejada)**, en orden ding, pad1..pad8 (por ángulo). El BP la tiene copiada en `PadLoc` / `PadUp` / `PadRad`.

## Trampas de este asset
- 🔴 **El booleano EXACTO con `material_mode = 'TRANSFER'` no pasó los slots del cortador** (todas las caras quedaron en el slot 0). Arreglo: clasificar cada cara por geometría en el marco de su pad (radio < R + ranura y debajo de la superficie → `Pocket`; z ≈ −fondo → `Groove`).
- Normales: promedio por área **dentro de cada slot** (`smooth_by_part`): la cúpula lisa sin arrastrar el canto del bolsillo.
- Rutas del render: **absolutas** (con una relativa, Blender guardó los PNG en otro lado).

## Scripts
`scripts/gen_hang.py` (malla + FBX + .blend + json) · `scripts/render_hang.py` (Cycles sin luces, sombreado falso de la paleta, un pad apretado y encendido). Salida: `VR_Test/Saved/ClaudeScripts/Hang/`.

## Log
- **2026-10-28** — v1: forma de la foto en la familia paleta/timbre, densidad bajada a ~36 k tris en total, boca del bolsillo redondeada, pads más al ras. Importado + materiales + BP.
