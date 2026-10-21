# Los cuadros de experiencia del menú de la DEMO: `SM_DemoCard_{Base,Plate,Slider,Trace}_SC`

**Encargo de la sesión Director (2026-10-16), para la Barcelona Design Week (miércoles 2026-10-21).** La demo es corta: un menú en el ambiente del Hall donde se elige entre dos experiencias de ~3 min, **ENTERING** (Breath) y **SURROUNDING** (Draw).
- Interacción: **láser + gatillo**, la misma de los botones SHARE / DON'T SHARE ([share-button.md](share-button.md), `BP_ShareButton_SC`).
- Cada cuadro es **el SHARE a 300 × 190 mm**: mismas partes, slots, ejes y origen, así que el Blueprint duplicado **solo cambia las mallas** (y la textura del texto).

**Estado:** 🟢 modelado + vista previa (`democard_sheet.png`) · ⬜ Unreal (lo importa la sesión Director) · ⬜ visor (legibilidad a 1,5-2 m).

## Medidas (mm; FBX = el marco de Unreal)
| | |
|---|---|
| Contorno exterior | **300 × 190** (semiejes A 150, B 95), esquinas **r 36** (el SHARE: 220 × 70, r 22) |
| Sección | **idéntica** al SAVE / SHARE: borde de 15 mm (canto r 3,5 / 3,0), pared de 4,8, canal de 5,4 con la cinta de luz (fondo a 6, paredes hasta 10), placa desplazada −10,2 con tope a 17,7 |
| Placa (tope plano) | 279,6 × 169,6 mm de UV (el tope visible, descontando el redondeo de 2,5, es un poco menor) |
| Recorrido | hover **+1 mm**, press **−4 mm** (los del SHARE, no cambian) |
| Slider | aro plano transparente de 5 a 9 mm hacia afuera, 3 mm de espesor |
| Trazo | cinta de ±7 mm a la boca del canal (z 15), sigue el contorno a −7,5 mm |

**Cajas en el marco de Unreal (cm, X = profundidad / cara, Y = ancho, Z = alto):**
| Malla | X | Y | Z |
|---|---|---|---|
| `Base` | 0 … 1,5 | ±15,0 | ±9,5 |
| `Plate` (en reposo) | 1,05 … 1,77 | ±13,98 | ±8,48 |
| `Slider` | 0 … 0,3 | ±15,9 | ±10,4 |
| `Trace` | 1,5 (plano) | ±14,95 | ±9,45 |

- **Para el `Hit`** (BoxComponent del láser, como el SHARE: extensión = semicaja + 0,2 cm): centro (0,9, 0, 0), extensión **(0,95, 15,2, 9,7) cm**.
- `AppearLuz`: igual que el SHARE (FaceAxis (1,0,0), PivotDepth 1,5, Duration 1,5).

## Partes, slots y triángulos
| Malla | Slots (en orden) | Tris |
|---|---|---|
| `SM_DemoCard_Base_SC` | 0 `Body` · 1 `Ring` (fondo y pared baja del canal: la luz) | 2.588 |
| `SM_DemoCard_Plate_SC` | 0 `PlateSide` · **1 `PlateTop`** (UV1 `TextUV`) | 1.292 |
| `SM_DemoCard_Slider_SC` | 0 `Slider` | 1.836 |
| `SM_DemoCard_Trace_SC` | 0 `Trace` (cinta abierta a propósito) | 216 |
| **Total** | | **5.932** (presupuesto ≤ 8.000) |

- Nombres de material en el FBX: `M_DemoCard_{Body,Ring,PlateSide,PlateTop,Slider,Trace}` (los del SHARE con otro prefijo).
- Controles: 0 abiertas (salvo la cinta del trazo), 0 degeneradas, 0 dadas vuelta, volumen con signo > 0. **0 astillas < 0,01 mm²** (las que Unreal descarta en silencio, gotcha 19), contado leyendo los FBX de vuelta en otro Blender.
- Cada malla tiene UV0 (`UVMap`); la placa suma UV1 `TextUV`. El slider lleva `UV0.x` = fracción del perímetro, horario desde arriba al centro (`Progress` 0-1 da la vuelta completa, con la misma cuenta sin costura del SAVE, gotcha 36).
- Los tramos rectos **no se subdividen** (12 tramos por esquina): el cuadro es plano y todo lo que se le hace es afín.

## Ejes y origen (idénticos al SHARE; verificado leyendo ambos FBX de vuelta)
- **FBX**: PARADO, cara hacia **+X**, arriba **+Z**, el ancho va por **Y**. Origen = **centro de la ESPALDA**. Escala 1, unidades en metros (`apply_unit_scale`, `FBX_SCALE_NONE`, igual que el FBX del SHARE). La placa se mueve en X.
- **`.blend`**: parado (cara −Y de Blender = +Z de glTF, arriba +Y de glTF), objetos `Base`, `Plate`, `Slider`, `Trace`.
- La confirmación, el hover y los tiempos son los del SHARE ([tabla de estados](share-button.md#estados-los-del-save)).

## Texto: máscaras por UV1 `TextUV`
Una textura por cuadro, blanco sobre negro, **2048 × 1242** (la placa a 7,33 px/mm), **sin voltear** (gotcha 34). Se usan igual que `T_Share_Text` (mismo parámetro de textura de `MI_ShareButton_PlateTop*`, sin sRGB, mismo Ink / InkGlow).

| Archivo | Qué lleva |
|---|---|
| `T_DemoCard_Entering_Text.png` | **el contrato**: "ENTERING" sola, centrada. Avenir Book, mayúscula de **18 mm**, espaciado +8 % (como el SHARE). Tinta ≈ 135 mm de ancho |
| `T_DemoCard_Surrounding_Text.png` | "SURROUNDING" sola, centrada, igual. Tinta ≈ 202 mm de ancho (cabe holgado en los 279,6) |
| `T_DemoCard_Entering_Full.png` · `T_DemoCard_Surrounding_Full.png` | **opcional**, mismo UV y mismo parámetro: **ícono** arriba (ondas que se abren desde un punto / un trazo con bucle que termina en la punta del pincel) + título + **subtítulo** (mayúscula de 9 mm, +10 %, al 78 % de intensidad). Textos de ejemplo: "BREATHE WITH THE LIGHT" y "DRAW IN THE AIR" — **a confirmar por Beltrán** |

**¿Conviene el ícono/subtítulo? Propuesta:** el título solo ya identifica la experiencia y es lo más legible a distancia; el Full vale si quieren que el visitante entienda qué hace cada una antes de elegir. Se resolvió **sin geometría ni slots nuevos**: el mismo tope de la placa, con otra máscara (se cambia la textura de la instancia de material y listo). Si prefieren un ícono con su propio color/animación, se puede agregar después una malla `SM_DemoCard_Art_SC` aparte; no se hizo para no sumar draw calls ni translúcidos.

Legibilidad (Quest 3 ≈ 25 px/°): el título de 18 mm a 2 m son ~13 px de alto de mayúscula; el subtítulo de 9 mm, ~6 px a 2 m y ~8,5 px a 1,5 m. **Poner el menú a ≤ 1,5-2 m**; si el subtítulo se usa, preferible ≤ 1,5 m.

## Cómo regenerar (scripts en `blender-3d/scripts/`)
```
# 1) máscaras (Python del sistema, PIL; Blender no trae PIL)
python gen_demo_card.py --text <dir_salida>
# 2) mallas, 4 FBX y .blend (headless)
blender --background --python gen_demo_card.py -- <dir_salida>
# 3) vista previa (4 vistas) y hoja
blender --background <dir>/SM_DemoCard_SC.blend --python render_demo_card.py -- <dir> <dir_temp>/dc.png
python sheet_demo_card.py <dir_temp>/dc <dir>/democard_sheet.png
```
- Paths **absolutos y de Windows** (gotcha 40). Salida: `VR_Test/Saved/ClaudeScripts/DemoCard/` (4 FBX, `SM_DemoCard_SC.blend`, 4 PNG de máscara, `democard_sheet.png`).
- Perillas arriba de `gen_demo_card.py`: `A, B, RC` (tamaño y esquina), `TITLE_CAP_MM`, `SUB_CAP_MM`, `FULL_*_Y`, `LABELS` (títulos y subtítulos).
- Si cambia el ancho de la placa (`A + PLATE_D`), las máscaras se regeneran solas con el layout correcto para esa UV.
- Vista previa: `democard_sheet.png` = reposo · hover en ENTERING · ENTERING apretado (la luz dando la vuelta, `Progress` 0,6) · variante Full. Mismo sombreado falso del SAVE/SHARE aprobados.

## Pendientes
- [ ] Unreal: importar los 4 FBX, duplicar `BP_ShareButton_SC` → cambiar las mallas y crear `MI_DemoCard_PlateTop*` con las dos máscaras (Director).
- [ ] Visor: legibilidad a la distancia real del menú; decidir Text vs Full y confirmar los subtítulos.
- [ ] GLB para la web, si el prototipo web debe seguir al menú (no se hizo: no estaba en el encargo).
