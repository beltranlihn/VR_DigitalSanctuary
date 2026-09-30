# Los botones SHARE / DON'T SHARE del cuadro de resultados: `SM_ShareButton_{Base,Plate,Slider,Trace}_SC`

**Encargo de Narrativa, pedido de Beltrán (2026-09-30).** Después de explorar el cuadro de resultados, Alma pregunta si el usuario quiere compartir su experiencia:
- **SHARE**: el alma sale nadando a la constelación;
- **DON'T SHARE**: el alma se desvanece con los demás elementos.

Pedidos de diseño:
- *"Misma estética que el botón SAVE y las teclas de la paleta"*.
- Se eligen con láser (hover) + gatillo.
- ~22 × 7 cm cada uno, bajo el cuadro, separados ~30 cm (los coloca Narrativa desde la Obra).

**Estado:**
- 🟢 aprobado por Narrativa en vista previa: `Saved/ClaudeScripts/ShareButton/share_sheet.png` (reposo / hover / confirmación).
- 🟢 GLB en la web.
- ⬜ Unreal: preparado, espera turno.
- ⬜ visor.

## Forma: el SAVE MELODY a 220 × 70 mm (esquinas r 22) con la MISMA sección
Ver [save-melody.md](save-melody.md).
- **Base**: borde de hormigón redondeado + **canal** con la **cinta de luz** cálida (slots Body · Ring).
- **Placa-botón**: lleva el texto (slots PlateSide · PlateTop, UV1 `TextUV`).
  - Hover: **+1 mm**.
  - Press: **−4 mm**.
- **Slider**: aro plano transparente abajo y afuera. En la confirmación la luz **da la vuelta al perímetro**.
- **Trazo**: `SM_ShareButton_Trace_SC`, para la aparición "luz primero".
- **Textos**: una máscara por etiqueta, **Avenir Book como el SAVE** (Narrativa confirmó que no hace falta Michroma).
  - `T_Share_Text.png`: "SHARE", 52,7 mm de ancho.
  - `T_DontShare_Text.png`: "DON'T SHARE", 112,5 mm.
  - Mayúscula de 11 mm y espaciado +8 %, sobre una placa de 199,6 × 49,6 mm.
- **Tramos rectos sin subdividir** (el SAVE los partía cada 4 mm), con 12 tramos por esquina.
  - Todo lo que se le hace al botón es afín: párpado, escalas y UV lineal.
  - De 16.000 a **6.370 tris por botón**: Base 2.780, Plate 1.388, Slider 1.972, Trace 232.
- 0 abiertas (salvo la cinta del trazo), 0 degeneradas, 0 dadas vuelta.

## Ejes
- Construcción acostada (cara +Z, +Y = arriba del texto, mm), como el SAVE.
- **FBX para Unreal**: PARADO, cara hacia **+X**, arriba **+Z**, como el cuadro de resultados. Origen en el centro de la ESPALDA.
- **GLB para la web**: cara **+Z de glTF**, arriba +Y (sin rotar).
  - Nodos `Base`, `Plate`, `Slider`, con materiales `M_ShareButton_{Body,Ring,PlateSide,PlateTop,Slider}`.
  - UV1 (`TEXCOORD_1`) = `TextUV` para la máscara del texto.

## Estados (los del SAVE)
| Estado | Placa | Cinta (`Glow`) | Texto | Slider |
|---|---|---|---|---|
| Reposo | 0 | 0,7 | blanco hueso (`InkGlow` 0,35) | nada |
| Hover (0,12 s de ida, 0,18 de vuelta) | +1 mm | 1,0 | luz cálida (`InkGlow` 1,2, `Ink` → 1,25 × la luz) | nada |
| Press = confirmación (0,45 s) | −4 mm (ease out) | 1,4 | luz cálida | `Progress` 0 → 1 (ease in-out): la luz da la vuelta |
| Después | → `OnConfirmed` → `Vanish()` ("luz primero" al revés) | | | |

## Scripts
- `scripts/gen_share_button.py`: mallas, FBX y `.blend`. Con `--text <dir>` y el Python del sistema, las dos texturas.
- `scripts/render_share_button.py`: vista previa con el sombreado del SAVE aprobado.
- `scripts/export_results_glb.py -- SM_ShareButton_SC.glb Base Plate Slider`: el GLB de la web.
- Unreal: `unreal-vr/scripts/share_button_dsl.py` (grafos) y `unreal-vr/blueprints/BP_ShareButton_SC.md`.

## Para la web (descripción para Narrativa)
- Dos pastillas de **hormigón claro cálido** de 22 × 7 cm (esquinas redondeadas).
- Un **canal fino de luz cálida** (#ffb873 aprox.) rodea la placa central. La placa es un poco más clara y lleva el texto en **mayúsculas finas y espaciadas** (Avenir Book, blanco hueso).
- **Hover**: la placa sube 1 mm, y el canal y el texto se encienden en luz cálida.
- **Press**: la placa se hunde 4 mm y una línea de luz cálida da la vuelta al contorno por fuera en 0,45 s. Después el botón se va con la aparición al revés.
