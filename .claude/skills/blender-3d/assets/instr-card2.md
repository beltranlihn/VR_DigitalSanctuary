# El panel de instrucciones v2 de la DEMO: `SM_InstrCard2_{Base,Plate,Slider,Trace}_SC`

**Encargo de la sesión Director (2026-10-19), con el guion nuevo de Beltrán para la Barcelona Design Week (mié 2026-10-21).** Reemplaza al panel v1 ([instr-card.md](instr-card.md), que queda intacto): **imagen cuadrada a la izquierda, texto a la derecha, 16:9 y curvo hacia el usuario.** Cada experiencia (Breath, Draw) abre con estas páginas y termina con el cuadro de resultados ([demo-results.md](demo-results.md)).
- Misma familia y **misma sección** que el cuadro de experiencia y el SHARE (marco + canal con cinta de luz + placa). El panel entero es el botón.
- Cada página es **una máscara blanco/negro del tope** (UV1 `TextUV`, como el v1); la imagen es **otro slot de la placa** (`PlateImage`, UV0). Cambiar de página = cambiar las dos texturas de la instancia de material.

**Estado:** 🟢 modelado + 6 páginas + 6 imágenes de muestra + hoja de vista previa · ⬜ Unreal (Director) · ⬜ visor (curva, legibilidad a ~1,5 m).

## Medidas (mm; FBX = el marco de Unreal)
| | |
|---|---|
| Contorno exterior | **800 × 450** (semiejes A 400, B 225), esquinas **r 64**. La proporción es 16:9 exacta (el v1: 640 × 400) |
| Sección | **idéntica** a toda la familia (borde de 15 mm, canto r 3,5 / 3,0, pared de 4,8, canal de 5,4 con la cinta, placa desplazada −10,2 con tope a 17,7). El grosor no escala |
| Tope de la placa (extensión de `TextUV`) | **779,6 × 429,6 mm** (la placa plana) |
| **Ventana de la imagen** | cuadrado de **330 × 330 mm** (`WIN_S`; el encargo pedía 300-330 y el texto cabe con 330), esquinas **r 16**, centrada en alto, borde izquierdo a **40 mm** del borde izquierdo del tope. Centro (−184,8 ; 0) mm sobre la placa plana |
| Imagen | superficie **hundida 1,5 mm** bajo el tope (z 16,2); el hueco tiene un **borde fino** al ras (2,4 mm), un **canal con la cinta de luz** de 4,0 mm (piso z 12,2) y el muro del lecho de la imagen |
| Zona de texto | desde **40 mm a la derecha de la ventana** hasta **40 mm antes del borde derecho** del tope: **329,6 mm de ancho**; 30 mm de margen arriba y abajo (369,6 mm de alto) |
| Recorrido | hover **+1 mm**, press **−4 mm** (los del SHARE), medidos por el eje de la placa en reposo |
| Slider / Trazo | aro plano transparente de 5 a 9 mm hacia afuera, 3 mm de espesor / cinta de ±7 mm a la boca del canal (z 15) |

### 🔴 La curva (`CURVE_R`, en `gen_instr_card2.py`; **default 1500 mm**, 0 = plano)
Toda la geometría (Base, Plate con su ventana, Slider, Trace) está **doblada alrededor del eje vertical (Z de Unreal), con los extremos hacia el usuario (+X)**. Pedido de Beltrán: "como la del HUD".
- Con el radio de la **cara de la placa** (profundidad 17,7 mm): `r = R + 17,7 − z` · `x' = r·sin(x/R)` · `z' = (R + 17,7) − r·cos(x/R)`. **El origen (centro de la espalda) no se mueve**; la sección se dobla entera (cara y espalda paralelas) y las normales se giran con la misma transformación (sombreado exacto).
- **Centro de la curva = el ojo**: a **151,77 cm** (R + 1,77) delante del origen, en Y = 0. A esa distancia la cara de la placa queda a 150 cm del ojo en todo su ancho.
- **Las UV se calcularon ANTES de doblar**, sobre la placa plana: las máscaras de texto y la imagen siguen valiendo. Como el radio es el de la cara de la placa, el arco conserva el largo en el tope (la imagen y el texto no se estiran).
- Los tramos rectos horizontales se subdividen para seguir la curva: la placa se corta con planos cada 72 mm (desvío ≤ 0,43 mm), la base y el slider llevan tramos de 84 mm (≤ 0,59 mm) y el trazo de 48 mm; los verticales no se subdividen (son generatrices del cilindro). El hover/press mueve la placa por X (traslación): en los extremos el hueco con la base cambia ~3 % del recorrido (< 0,15 mm), despreciable.
- Para otro radio: cambiar `CURVE_R` y regenerar (el resto de la ficha, en cm, hay que recalcularlo: sale impreso en `INSTRCARD2_PUNTOS`).

## Cajas en el marco de Unreal (cm, ya dobladas; X = profundidad / cara, Y = ancho, Z = alto)
| Malla | X | Y | Z |
|---|---|---|---|
| `Base` | 0 … 6,76 | ±39,93 | ±22,50 |
| `Plate` (en reposo) | 1,05 … 6,75 | ±38,70 | ±21,48 |
| `Slider` | 0 … 5,87 | ±40,85 | ±23,40 |
| `Trace` | 1,50 … 6,80 | ±39,55 | ±22,45 |

- **Para el `Hit`** (el láser; semicaja + 0,2 cm): centro **(3,38 ; 0 ; 0)**, extensión **(3,58 ; 40,13 ; 22,70) cm**. El centro del tope está en X = 1,77 cm; los extremos del tope, en X ≈ 6,75 cm.
- `AppearLuz`: igual que el SHARE (FaceAxis (1,0,0), PivotDepth 1,5, Duration 1,5); el trazo ya viene doblado (su centro en X = 1,5 cm).

## 🔴 Rectángulos exactos para colocar el contenido (cm, marco de Unreal, placa en reposo, YA DOBLADOS)
⚠ **Unreal espeja la Y**: `Y_UE = −(derecha del espectador)`. **La ventana de la imagen queda a la IZQUIERDA del espectador, o sea en Y_UE POSITIVA**; el texto, a la derecha, en Y_UE negativa. Control de un vistazo al importar: la imagen tiene que verse a la izquierda mirando el panel de frente.

| Elemento | Y_UE (cm) | Z (cm) | X de la superficie (cm) |
|---|---|---|---|
| **Imagen** (`PlateImage`, 330 × 330 mm) | **+1,98 … +34,70** | **−16,50 … +16,50** | 1,63 (borde de Y 1,98) · **2,76 (centro, Y +18,45)** · 5,68 (borde de Y 34,70) |
| **Zona de texto** (sobre `PlateTop`, 329,6 × 369,6 mm) | **−34,66 … −2,02** | **−18,48 … +18,48** | 1,78 (borde de Y −2,02) · **2,91 (centro, Y −18,45)** · 5,83 (borde de Y −34,66) |
| Tope plano de la placa (todo `TextUV`) | −38,70 … +38,70 | −21,48 … +21,48 | 1,77 en el centro |

- El **centro de la imagen** está en (X 2,76 ; Y +18,45 ; Z 0) y el **centro de la zona de texto** en (X 2,91 ; Y −18,45 ; Z 0): simétricos respecto del eje del panel (la imagen y la zona de texto tienen 40 mm de aire hacia el borde y 40 mm entre las dos).
- **No hace falta poner quads**: la imagen entra por el slot `PlateImage` (UV0) y el texto por la máscara (`PlateTop`, UV1). Los rectángulos son para verificar y por si algo se superpone (ojo: un quad plano sobre la imagen se despega hasta 9 mm del arco; un contenido encima tiene que curvarse igual).
- **En coordenadas de la placa PLANA (las de las texturas)**, mm desde el centro, +y arriba: imagen x −349,8 … −19,8, y ±165; zona de texto x +20,2 … +349,8, y ±184,8; en píxeles de la máscara de 2048 × 1129 (2,627 px/mm): zona de texto x 1077 … 1943, y 79 … 1050; ventana x 105 … 972, y 131 … 998.

## Partes, slots y triángulos
| Malla | Slots (en orden) | Tris |
|---|---|---|
| `SM_InstrCard2_Base_SC` | 0 `Body` · 1 `Ring` (fondo y pared baja del canal: la luz) | 3.100 |
| `SM_InstrCard2_Plate_SC` | 0 `PlateSide` · **1 `PlateTop`** (UV1 `TextUV`) · **2 `PlateImage`** (UV0 = 0..1 sobre el cuadrado) · **3 `WinRing`** (la cinta de luz del marquito) | 2.732 |
| `SM_InstrCard2_Slider_SC` | 0 `Slider` (UV0.x = fracción del perímetro, horario desde arriba) | 1.700 |
| `SM_InstrCard2_Trace_SC` | 0 `Trace` (cinta abierta a propósito) | 248 |
| **Total** | | **7.780** (el v1: 5.932; la curva exige cortes y la ventana suma geometría) |

- Materiales en el FBX: `M_InstrCard2_{Body,Ring,PlateSide,PlateTop,PlateImage,WinRing,Slider,Trace}`.
- **`WinRing` es una segunda cinta de luz**: mismo material que `Ring` (emisivo, mismo `Glow`/hover); va aparte para poder encenderla distinto. `PlateImage` es una textura RGB normal (sRGB), emisiva o unlit.
- **La `Base` es un anillo cerrado, sin tapas** (el v1 tenía tapas planas bajo la placa, que no se ven; con la curva habrían exigido cortes y triángulos de más). Misma sección visible.
- La placa es un sólido cerrado con tres tapas planas **cortadas** a la curva: tope (con el hueco de la ventana), fondo e imagen.
- Controles (leyendo los FBX de vuelta en otro Blender): **0 abiertas** (salvo la cinta del trazo), **0 degeneradas**, **0 dadas vuelta**, volumen con signo > 0, **0 astillas < 0,01 mm²** (área mínima 0,41 mm² en la base, 0,96 en la placa, 3,5 en el slider, 34 en el trazo). UV leídas de vuelta: `PlateImage` 0..1 exacto, `TextUV` del tope 0,003..0,997, UV0.x del slider 0..1.
- 8 tramos por esquina del contorno (el v1: 12; con 8 la cuerda se aparta 0,3 mm y las normales son exactas) y 6 en la ventana.

## Ejes y origen (idénticos al SHARE y al v1)
- **FBX**: PARADO, cara hacia **+X**, arriba **+Z**, ancho por **Y**; origen = **centro de la ESPALDA**; escala 1, metros. La placa se mueve en X.
- **`.blend`**: parado (cara −Y de Blender = +Z de glTF), objetos `Base`, `Plate`, `Slider`, `Trace`.

## Las 6 páginas (`T_Instr2_<Breath|Draw>_P<n>.png`)
Blanco sobre negro, **2048 × 1129** (L, 2,627 px/mm), **SIN voltear** (gotcha 34), UV1 `TextUV` = el tope entero (0..1). Mismo parámetro que `T_Instr_*` / `T_Share_Text`: sin sRGB, mismo Ink / InkGlow. **Solo hay texto a la derecha**; la ventana y lo que la rodea van en negro. **Sin íconos** (el ícono es la imagen).

| Elemento | Medida / valor |
|---|---|
| **Cuerpo** | Avenir Book, mayúscula de **22,5 mm** (≥ 22 pedido), interlineado 1,28, **centrado en la zona** (x = +185,0 mm), reparto parejo (el menor ancho que mantiene las mismas líneas), intensidad 255. Centrado en vertical en la banda libre |
| **Pie** | Avenir Book, mayúscula de **14,5 mm** (≥ 14 pedido), centrado, intensidad 200, pegado al fondo de la zona |
| Apóstrofo | "You’ll" con el de imprenta (’), que Avenir trae |

Textos de Beltrán, tal cual, y su reparto real (mm de tinta desde el centro de la placa; la zona es x 20,2 … 349,8):
| Página | Cuerpo | Líneas cuerpo | Pie | Tinta x | Tinta y |
|---|---|---|---|---|---|
| Breath P1 | Pick up the sensor in front of you with your dominant hand. | 3 | — | 39,2 … 327,8 | −58,4 … 52,3 |
| Breath P2 | Rest the sensor on your belly, just below your ribs. Breathe normally. | 3 | — | 23,6 … 349,1 | −58,4 … 52,3 |
| Breath P3 | Breathe in and out slowly. The circle follows your belly. | 3 | — | 57,9 … 314,0 | −58,4 … 52,3 |
| Breath P4 | You’ll breathe in a steady cycle: inhale, hold, exhale. Follow the guide without forcing it. | 5 | Point at START and press the trigger. (2 líneas) | 45,3 … 323,6 | −184,4 … 125,4 |
| Draw P1 | Pick up the brush with your dominant hand. | 2 | — | 33,9 … 336,1 | −38,6 … 32,2 |
| Draw P2 | Your palette is in your other hand. Point at a color to choose it, hold the trigger to draw. Try a first stroke. | 5 | The experience begins after your first stroke. (2 líneas) | 27,8 … 339,9 | −183,3 … 125,4 |

Legibilidad (Quest 3 ≈ 25 px/°) a **1,5 m**: la mayúscula del cuerpo da ~22 px y la del pie ~14 px; a 1,3 m, ~25 y ~16. Breath P2 llega a 0,7 mm del límite derecho de la zona (y Breath P4 / Draw P2 usan 5 líneas de cuerpo + 2 de pie): no hay aire para un renglón más largo. Si Beltrán cambia un texto, se edita `PAGES` en el script y se vuelve a correr `--text`; el script avisa (`cabe`) si ya no entra.

## Las 6 imágenes de muestra (`T_DemoInstrImg_<Breath|Draw>_<n>.png`)
PNG **RGB 1024 × 1024**, fondo azul noche muy oscuro con un degradado y estrellas casi invisibles, dibujo lineal claro (blanco azulado) con acentos cálidos (la luz), el estilo de los íconos del v1 más grande. **Son de muestra: Beltrán las reemplaza por fotos** (cuadradas; basta con guardarlas con los mismos nombres o cambiar la textura de la instancia).
| Archivo | Dibuja |
|---|---|
| `Breath_1` | el sensor flotando (disco con domo y aro de luz, con su sombra) frente a una mano abierta |
| `Breath_2` | silueta sentada de perfil con el sensor contra la panza, flecha ↕ |
| `Breath_3` | la misma silueta y un círculo que crece (aros concéntricos con rayos) unido a la panza |
| `Breath_4` | los aros del pacer y el rótulo "inhale · hold · exhale" |
| `Draw_1` | el mando de Quest (empuñadura, aro de seguimiento con sus LED, palanca y botones) con la punta brillante y un trazo de luz |
| `Draw_2` | la paleta circular (4 colores llenos + 4 pinceles huecos, una tecla encendida) sobre una mano abierta y el trazo de luz que sale de la tecla |

**Orientación**: UV0 de `PlateImage` = (x, y de la placa plana − esquina de la ventana) / 330, con +v hacia arriba, la **misma convención que `TextUV`**: un PNG guardado sin voltear se lee derecho en Unreal (gotcha 34). Verificado en el render: las imágenes y el rótulo se leen derechos.

## Cómo regenerar (scripts en `blender-3d/scripts/`; todo en `gen_instr_card2.py`)
```
# 1) las 6 máscaras y las 6 imágenes (Python del sistema, PIL + scipy)
python gen_instr_card2.py --text   <dir_salida>          # [--win 300..330 para otro lado de ventana]
python gen_instr_card2.py --images <dir_salida>
# 2) mallas, 4 FBX y .blend (headless)
blender --background --python gen_instr_card2.py -- <dir_salida> build
# 3) control: lee los 4 FBX de vuelta (aberturas, astillas, dadas vuelta, volumen, UV, cajas)
blender --background --python gen_instr_card2.py -- <dir_salida> qc
# 4) vistas (6 páginas + hover + desde arriba) y hoja
blender --background <dir>/SM_InstrCard2_SC.blend --python gen_instr_card2.py -- <dir> render <dir_temp>/ic2
python gen_instr_card2.py --sheet <dir_temp>/ic2 <dir>/instr2_sheet.png
```
- Paths **absolutos y de Windows** (gotcha 40). Salida: `VR_Test/Saved/ClaudeScripts/Demo2/Modelos/` (`SM_InstrCard2_*_SC.fbx`, `SM_InstrCard2_SC.blend`, `T_Instr2_*`, `T_DemoInstrImg_*`, `instr2_sheet.png`).
- Perillas: `CURVE_R`, `A, B, RC`, `WIN_S`, `WIN_MARGIN`, `IMG_SINK`, `RIB_W`, `BORDER_W`, `BODY_CAP_MM`, `FOOT_CAP_MM`, `TEXT_GAP`, `TEXT_SIDE`, `TEXT_VMARGIN`, `STEP_X`, `N_ARC`. `GIC2_DEBUG=1` imprime las aberturas por etapa de la placa.
- La vista previa usa la opción **B** del contraste del v1 (placa oscura, tinta hueso): es la recomendada; la decisión se toma en el visor con los valores de la instancia, no con las mallas.

## Notas de construcción (para no repetir los tropiezos)
- 🔴 La placa del v1 se barre solo hasta 61 mm hacia adentro y la **tapa** cierra el centro: con la ventana de 330 el hueco se sale de esa banda y pisa el barrido (61 aristas abiertas). Aquí el barrido llega a 14,2 mm del contorno y el centro lo cubren las tapas. `triangle_fill` **sí** calza huecos si el contorno interior queda dentro del exterior.
- Una tapa plana de 700 mm no sigue una curva de 1.500 mm (flecha de 41 mm): se corta TODO el sólido con planos `x = k·72 mm` (`bisect_plane` sobre todo el bmesh, sin T en las costuras). El script elige la grilla cuyos planos quedan más lejos de los vértices existentes (astillas) y las normales exactas viajan en una capa de vértices (`float_vector`), que `bisect_plane` interpola.
- Las normales se doblan con la inversa transpuesta del jacobiano de la curva (una rotación de −θ con una compresión de r/R ≤ 1,2 %).

## Pendientes
- [ ] Unreal: importar los 4 FBX, duplicar el BP del panel v1 / cuadro → `BP_InstrCard2_SC`; una instancia de material con las dos texturas (`MaskTex` de la página y la imagen) y `WinRing` con el mismo `Glow` que `Ring` (Director).
- [ ] Visor: la curva (¿incomoda o ayuda?), la legibilidad del cuerpo y del pie a ~1,5 m, el tamaño de la imagen.
- [ ] Beltrán: reemplazar las 6 imágenes de muestra por fotos cuadradas.
