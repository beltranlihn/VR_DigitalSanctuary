# SM_DrawPalette_* — la paleta de la etapa de dibujo

## Propósito
La paleta que sostiene el usuario en la etapa de dibujo (pedido de Beltrán 2026-09-29, plano `Escritorio/Drawing1-Model.pdf`). Redonda, de **hormigón suave pulido, cálido y poco saturado**, con una **ranura-anillo hundida e iluminada**, **4 botones de color a la derecha** y **4 de pincel a la izquierda** (cuñas que sobresalen), **undo/redo flotando** a la izquierda, **slider de grosor en arco flotando** abajo con su bolita, y al centro un **casquete de esfera** que muestra el color elegido y la textura del pincel. Todo con bevel suave. **Los botones seleccionados quedan más elevados.**

## Estado
🟡 **Modelado y renderizado en Blender (headless), sin importar a Unreal** (el editor estaba tomado por otras sesiones). Sin veredicto de Beltrán todavía.

## Medidas (el plano no trae cotas)
Se midió en píxeles (planta: centro (1032, 787), radio 451,5 px) y se escaló a **Ø 18 cm** (la paleta actual `BP_TBPalette` tiene undo a 6,5 cm del centro). Constantes en píxeles del plano en el script; `u()` las pasa a metros; `R` cambia el tamaño de todo.
| | px | cm |
|---|---|---|
| Radio exterior / espesor | 451,5 / 71 | 9,0 / 1,42 |
| Ranura (anillo) | r 391,5–418,5, fondo −38 | 0,54 de ancho, 0,76 de profundidad |
| Plato (rebajado bajo el borde) | −20 | −0,4 |
| Cuñas | r 128–335, 25° de ancho, juntas 15° (centros ±20, ±60 / 180±20, 180±60) | r 2,6–6,7 |
| Botón: altura / sube al seleccionar | llega al borde (0) / +15 | 0,7 / +0,3 |
| Casquete | base r 92, asoma 5 sobre el plato | r 1,8 |
| Undo/redo | r 484–567, 154–178° y 182–206°, 33 de alto | hasta 11,3 |
| Slider / bolita | r 490,5, 227–313°, tubo 7,5 / bolita 19 | — |

## Mallas (`VR_Test/Saved/ClaudeScripts/DrawPalette/`), todas con **origen en el centro de la paleta**
- `SM_DrawPalette_Base_SC` — perfil revolucionado con filetes (borde, ranura, plato, bolsillo del casquete) − 8 bolsillos (único booleano) → receta del anillo (soldar + disolver coplanares + bisel sin clamp + normales ponderadas + triangular). Slot 1 = piso de la ranura (luz).
- `SM_DrawPalette_Key_SC` — UNA cuña centrada en 0°; las 8 = esta malla girada en Z. Seleccionar = subir Z.
- `SM_DrawPalette_SideKey_SC` — undo (166°); redo = la misma girada +28°.
- `SM_DrawPalette_Slider_SC` (tubo con puntas esféricas) · `SM_DrawPalette_Knob_SC` (en 270°: el grosor se mueve GIRANDO la bolita alrededor del centro).
- `SM_DrawPalette_Swatch_SC` — casquete, UV0 plana 0..1 para color/textura del pincel.
Ejes: acostada en XY, cara a +Z, +X = colores. ⚠ Unreal espeja la Y.

## Scripts
`scripts/gen_draw_palette.py` (malla + FBX + .blend) · `scripts/render_draw_palette.py` (Cycles: arma la paleta completa, 4 vistas).

## Pendientes
- [ ] 38 astillas (< 0,01 mm²) en la base, en los bordes de los bolsillos (orejas casi colineales al triangular caras planas de arcos). 1 UV degenerada en undo/redo y 3 puntitos oscuros en su tapa.
- [ ] Ondulación leve en los costados de algunas cuñas (normales ponderadas sobre tiras finas).
- [ ] Iconos de los pinceles y de undo/redo (en el material, como la paleta actual).
- [ ] Importar a Unreal + material (hormigón unlit con luz falsa, ranura emisiva) + BP que la monte sobre `BP_TBPalette`.

## v2 (2026-09-29, pedidos de Beltrán sobre la v1)
- **Ø 40 cm** (`R = 0.20`). De paso las astillas de la base bajaron a 2 (a 18 cm eran 38).
- **Materiales rugosos, sin reflejos**. En Unreal: nivel SIN luz direccional → material unlit con **emisión + sombreado propio** (luz falsa en el shader) para que se lea en 3D.
- **Íconos de pincel = las texturas `T_Ico_*` de la paleta de Drawing** (`NeuralCanvas/TB/Icons`, máscaras blanco/negro), por UV1 **`IconUV`** de la cuña (cuadro `ICON_PX` 120 px, arriba = radial afuera; el material lo gira por instancia para dejarlo derecho). Render de Blender con los `buttonimage.png` de open-brush (falta WetPaint en el clon: se exporta de `T_Ico_6`).
- **UNDO / REDO = texto impreso** (no relieve, Beltrán lo pidió así): UV1 **`LabelUV`** de la pieza lateral + texturas `T_DrawPalette_Undo/Redo.png` (Avenir Book, generadas con PIL, en la carpeta de salida). Se lee de abajo hacia arriba, la cabeza de las letras hacia afuera.
- **Slider = banda PLANA translúcida** (contorno propio `band()`: la cuña se deformaba en 86°). **Bolita = DISCO plano** con origen en SU centro: el BP la ubica sobre el arco y la **escala (izquierda chica, derecha grande)**.
- Robustez: tapas con `triangle_fill` (poke rompía la banda: el centroide de un arco cae afuera), niveles planos de la base **re-rellenados** (CLIP daba vuelta 3 triángulos del plato), y **normales propias** (plano = normal exacta; resto = promedio por área de las caras curvas) en vez de `WEIGHTED_NORMAL` (inclinaba la tapa de la cuña 7,8°). Controles finales: 0 desvíos, 0 invertidas, 0 no-manifold.

- **Íconos y textos BLANCOS** con un poco de emisión solo en el dibujo; cuñas de pincel y undo/redo algo más oscuras para contraste. Los 4 íconos se sacaron de Unreal (`CaptureAssetImage` de `T_Ico_0/5/3/6` → `icon_<Pincel>.png` en la carpeta de salida).
- **Íconos A LO LARGO de cada botón**: en el marco de la cuña (`IconUV`) se giran **−45°** (vienen en diagonal) y se agrandan ×1,3 (`ICON_ROT`, `ICON_SCALE` en `render_draw_palette.py`; replicar en el material de Unreal).

## Log
- **2026-09-29** — plano medido, generador analítico, 2 correcciones (densidad de contornos: astillas 122 → 38; anillos de la tapa de la cuña se cruzaban en la punta angosta: rayas negras) + renders.
