# El panel de instrucciones de la DEMO: `SM_InstrCard_{Base,Plate,Slider,Trace}_SC`

**Encargo de la sesión Director (2026-10-16), tras aprobar Beltrán los cuadros de experiencia ([demo-card.md](demo-card.md)) y elegir la variante Full.** Reemplaza al widget de Calibration como PANEL DE INSTRUCCIONES de ENTERING y SURROUNDING. Beltrán: *"me gusta esta estética de marco con una cinta de luz, es más fácil de ver y entender"*.
- Misma familia y **misma estructura** que el cuadro de experiencia y el SHARE ([share-button.md](share-button.md)): marco + canal con cinta de luz + placa. El panel entero es el botón ("apuntá al panel y apretá el gatillo").
- **Cada página es UNA máscara** blanco/negro que cubre el tope entero de la placa (UV1 `TextUV`), con el mismo parámetro `MaskTex`. Cambiar de página = cambiar la textura de la instancia de material.

**Estado:** 🟢 modelado + 6 páginas + hoja de vista previa · ⬜ Unreal (Director) · ⬜ visor (legibilidad a 1,3 m y contraste del material).

## Medidas (mm; FBX = el marco de Unreal)
| | |
|---|---|
| Contorno exterior | **640 × 400** (semiejes A 320, B 200), esquinas **r 64** (el cuadro: 300 × 190, r 36; el SHARE: 220 × 70, r 22) |
| Sección | **idéntica** a toda la familia: borde de 15 mm (canto r 3,5 / 3,0), pared de 4,8, canal de 5,4 con la cinta (fondo a 6, paredes hasta 10), placa desplazada −10,2 con tope a 17,7. El grosor no escala: a 1,3 m el canal sigue dando ~6 px |
| Placa (tope plano) | **619,6 × 379,6 mm de UV** (el tope visible, descontando el redondeo de 2,5, es un poco menor) |
| Recorrido | hover **+1 mm**, press **−4 mm** (los del SHARE) |
| Slider / Trazo | aro plano transparente de 5 a 9 mm hacia afuera, 3 mm de espesor / cinta de ±7 mm a la boca del canal (z 15) |

**Cajas en el marco de Unreal (cm; X = profundidad / cara, Y = ancho, Z = alto):**
| Malla | X | Y | Z |
|---|---|---|---|
| `Base` | 0 … 1,5 | ±32,0 | ±20,0 |
| `Plate` (en reposo) | 1,05 … 1,77 | ±30,98 | ±18,98 |
| `Slider` | 0 … 0,3 | ±32,9 | ±20,9 |
| `Trace` | 1,5 (plano) | ±31,95 | ±19,95 |

- **Para el `Hit`** (el láser; como el SHARE: semicaja + 0,2 cm): centro **(0,9, 0, 0)**, extensión **(0,95, 32,2, 20,2) cm**.
- `AppearLuz`: igual que el SHARE (FaceAxis (1,0,0), PivotDepth 1,5, Duration 1,5).

## Partes, slots y triángulos
| Malla | Slots (en orden) | Tris |
|---|---|---|
| `SM_InstrCard_Base_SC` | 0 `Body` · 1 `Ring` (fondo y pared baja del canal: la luz) | 2.588 |
| `SM_InstrCard_Plate_SC` | 0 `PlateSide` · **1 `PlateTop`** (UV1 `TextUV`) | 1.292 |
| `SM_InstrCard_Slider_SC` | 0 `Slider` (UV0.x = fracción del perímetro, horario desde arriba) | 1.836 |
| `SM_InstrCard_Trace_SC` | 0 `Trace` (cinta abierta a propósito) | 216 |
| **Total** | | **5.932** (presupuesto ≤ 8.000) |

- Materiales en el FBX: `M_InstrCard_{Body,Ring,PlateSide,PlateTop,Slider,Trace}`.
- Mismos controles que el cuadro: 0 abiertas (salvo la cinta del trazo), 0 degeneradas, 0 dadas vuelta, volumen con signo > 0, **0 astillas < 0,01 mm²** (leyendo los FBX de vuelta en otro Blender). Tramos rectos sin subdividir, 12 tramos por esquina (la misma cuenta de puntos que el cuadro).

## Ejes y origen (idénticos al SHARE y al cuadro)
- **FBX**: PARADO, cara hacia **+X**, arriba **+Z**, ancho por **Y**; origen = **centro de la ESPALDA**; escala 1, metros. La placa se mueve en X.
- **`.blend`**: parado (cara −Y de Blender = +Z de glTF), objetos `Base`, `Plate`, `Slider`, `Trace`.

## Las 6 páginas (`T_Instr_<Entering|Surrounding>_P1..P3.png`)
Blanco sobre negro, **2048 × 1255** (3,3 px/mm), **SIN voltear** (gotcha 34), UV1 `TextUV` = el tope entero (0..1). Mismo parámetro que `T_Share_Text`: sin sRGB, mismo Ink / InkGlow.

| Elemento | Medida / valor |
|---|---|
| **Cuerpo** | Avenir Book, mayúscula de **23 mm** (≥ 22 pedido), interlineado 1,30, **centrado**, reparto parejo (el menor ancho que mantiene las mismas líneas), intensidad 255. Textos FINALES de `docs/demo/INSTRUCCIONES-DEMO.md`, tal cual (incluida "Rest the sensor" en ENTERING p2) |
| **Pie** | Avenir Book, mayúscula de **14,5 mm** (≥ 14 pedido), centrado, intensidad 200. Va abajo: su ÚLTIMA línea está a y = −156 mm del centro. Las páginas 3 no tienen pie |
| **Ícono** | centro en y = **+108 mm** (banda de ~100 mm), trazo ≥ 2,6 mm, intensidades graduadas 55-255 (lo tenue se enciende menos) |
| El guion largo "—" | se pega a la palabra anterior: nunca abre un renglón |

Líneas y anchos reales (mm de tinta; la placa tiene 619,6):
| Página | Líneas cuerpo | Ancho máx. cuerpo | Líneas pie | Ancho máx. pie |
|---|---|---|---|---|
| ENTERING p1 | 3 | 477 | 2 | 300 |
| ENTERING p2 | 4 | 449 | 1 | 262 |
| ENTERING p3 | 4 | 526 | — | — |
| SURROUNDING p1 | 3 | 490 | 2 | 300 |
| SURROUNDING p2 | 4 | 450 | 1 | 262 |
| SURROUNDING p3 | 4 | 534 | — | — |

Íconos (lineales, propios de cada página):
| Página | Ícono |
|---|---|
| ENTERING p1 | esfera de luz difusa con tres ondas tenues (la que respira) |
| ENTERING p2 | silueta sentada de perfil, el sensor de canto contra la panza bajo las costillas, flecha ↕ |
| ENTERING p3 | aros concéntricos luminosos con un punto, el último apenas insinuado (los del pacer) |
| SURROUNDING p1 | trazo de luz con bucle que se afina hacia atrás y termina en la punta brillante |
| SURROUNDING p2 | paleta circular (4 colores llenos + 4 pinceles huecos), el mando con la punta brillante tocando una tecla |
| SURROUNDING p3 | empuñadura con el gatillo hundido (flecha de presión) y un trazo que engrosa |

Legibilidad (Quest 3 ≈ 25 px/°): a **1,3 m** la mayúscula del cuerpo da ~25 px y la del pie ~16 px; el ícono ocupa unos 110 px.

## ⚠ Contraste del material: decisión para el visor
El look de reposo de la familia (tinta **hueso** sobre la placa **beige**) tiene poco contraste: era suficiente para "SHARE" o un título de 18 mm, pero **un párrafo de 4 líneas se lee flojo**. Las máscaras son las mismas; solo cambia el material del tope. La hoja (`instr_sheet.png`, última fila) muestra dos alternativas con SURROUNDING p2:
- **A. Tinta oscura sobre la placa clara** (Ink ≈ (0,12, 0,09, 0,07)): máximo contraste, pierde "el texto es luz".
- **B. Placa oscura, tinta hueso** (albedo del tope ≈ (0,17, 0,15, 0,13)): **recomendada**; conserva el hover del texto en luz cálida (`InkGlow`) y el marco claro con la cinta.
Se resuelve con valores de la instancia (`MI_InstrCard_PlateTop`), no con las mallas. Definir en el visor.

## Cómo regenerar (scripts en `blender-3d/scripts/`)
```
# 1) las 6 máscaras (Python del sistema, PIL)
python gen_instr_card.py --text <dir_salida>
# 2) mallas, 4 FBX y .blend (headless)
blender --background --python gen_instr_card.py -- <dir_salida>
# 3) vistas (6 páginas + hover + apretado + 2 alternativas de contraste) y hoja
blender --background <dir>/SM_InstrCard_SC.blend --python render_instr_card.py -- <dir> <dir_temp>/ic.png
python sheet_instr_card.py <dir_temp>/ic <dir>/instr_sheet.png
```
- Paths **absolutos y de Windows** (gotcha 40). Salida: `VR_Test/Saved/ClaudeScripts/InstrCard/`.
- Los textos viven en `PAGES` (arriba de `gen_instr_card.py`, copiados de `docs/demo/INSTRUCCIONES-DEMO.md`): si cambian, se editan ahí y se vuelve a correr el paso 1. La variante corta de 2 páginas se obtiene con otra entrada de `PAGES`.
- Perillas: `A, B, RC`, `BODY_CAP_MM`, `FOOT_CAP_MM`, `TEXT_MAX_W`, `ICON_Y`, `BODY_Y0`, `FOOT_LAST_Y`. Los íconos son funciones `icon_*` (`Patch`: disco, círculo, línea con taper, bezier, cápsula, glow, flecha; zoom por ícono en `ICONS`).
- Hoja: `instr_sheet.png` = 6 páginas sobre la placa (ENTERING | SURROUNDING × P1..P3) + hover y apretado de ENTERING p1 + las dos alternativas de contraste.

## Pendientes
- [ ] Unreal: importar los 4 FBX, duplicar el BP del cuadro/SHARE → `BP_InstrCard_SC`, una `MI_InstrCard_PlateTop` por página (o un solo parámetro `MaskTex` que cambia de página) (Director).
- [ ] Visor: tamaño a 1,3 m, contraste (A/B) y si los íconos se entienden sin el texto.
- [ ] Si la tinta cierra la experiencia: sumar la línea opcional de tinta de INSTRUCCIONES-DEMO.md §2 a SURROUNDING p2 (hoy son 4 líneas + pie; una más ya no entra con el pie: pasaría a una página extra).
