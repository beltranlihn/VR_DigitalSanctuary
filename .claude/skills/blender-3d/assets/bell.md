# El timbre del Soul Charger Center: `SM_Bell_{Base,Button,Slider}_SC`

**Pedido de Beltrán (2026-09-30):**
- Plano `C:/Users/beltr/Desktop/ButtonBell.pdf`. *"Es de la misma onda"* que el sensor, y la obra pide que timbre y sensor RIMEN (`docs/OBRA-SOUL-CHARGER.md`, "El timbre es el tutorial").
- Una base y un aro de luz.
- Un **slider radial plano alrededor** que se carga de 0 a 100 mientras se aprieta.
- Un **botón central** con una hendidura suave hacia adentro, que **se mueve al apretarlo**.

Estado: 🟡 v2 enviada · ⬜ OK final · ⬜ Unreal.
- **v2 (2026-09-30, Beltrán: "va bien; el slider va en el margen inferior; el botón más ancho")**:
  - botón R 80,5 → **92 mm** (queda un borde de plano de ~8 mm antes de la cinta), con la hendidura proporcional (4,7 mm);
  - slider **al ras de la ESPALDA** (`S_LOW`, h 0-3), de r 164 a 184: un aro plano sobre la pared alrededor de la base.
  - Lectura de "margen inferior": abajo en altura. Si quería decir un arco en la parte baja de la vista de frente, se cambia.
- **v3 (misma tarde)**:
  - *"el slider debe ser transparente; solo se va marcando la carga"* → sin pista: el material solo emite donde `UV.x < Progress` (borde suave).
  - *"cuando apretamos, el emissive del aro también debe iluminarse más"* → el aro sube su brillo con el apretado: `Glow = 0,7 + 0,9 · Press`, del reposo tenue al apretado intenso. En Unreal lo maneja el BP con la misma curva del botón.

## Del PDF (leído de sus VECTORES con PyMuPDF, no a ojo)

- El PDF es un dibujo CAD de 48 trazos: vista de frente con 4 círculos y un corte.
- `page.get_drawings()` da las medidas exactas: corte vertical con eje en y = 425 y espalda en x = 65,8.
- Unidades tomadas como **mm** → Ø 318,6 mm, botón Ø 161, base de 44,1 mm y el botón sale 18 mm. `SCALE` en `gen_bell.py` si es otro tamaño.
- **Base**:
  - canto con radio 12,8 arriba y abajo;
  - borde y plano a la MISMA altura (44,1);
  - hendidura de r 108,5 a 124,4 y 18 mm de fondo, con la boca redondeada a 7,7.
  - La luz va solo en la parte baja de la hendidura (slot `Ring`).
- **Botón**:
  - canto de arriba con radio 13,3;
  - hendidura suave parabólica de 4,1 mm hasta r 66,8;
  - el cuerpo baja hasta el nivel del fondo de la hendidura (la línea punteada del plano) y entra en un bolsillo de la base con 1 mm de luz;
  - **recorrido 10 mm** (bolsillo 2 mm más hondo).
- **Slider** (NO está en el PDF; propuesta):
  - anillo plano de r 172 a 190, de 3 mm, al ras del borde, flotando alrededor de la base (la mano tapa el centro al apretar).
  - UV0.x = fracción angular HORARIA desde +Y visto de frente → el material lo llena con `Progress`.

## Mallas (`scripts/gen_bell.py`, usa `scripts/revolve_lib.py`)

- Mismo origen para las tres: centro de la espalda de la base, frente hacia +Z. El BP baja el botón `Press · 10 mm` en −Z.
- `SM_Bell_Base_SC`: 8.832 tris, slots Body · Face · Ring (luz) · Pocket.
- `SM_Bell_Button_SC`: 4.032 tris, slots ButtonSide · ButtonTop.
- `SM_Bell_Slider_SC`: 3.264 tris, slot Slider.
- Todas cerradas, 0 degeneradas, normales exactas del perfil.
- `revolve_lib.py` = perfil con filetes + giro + normales exactas + polos. Admite **perfil cerrado** (`closed=True`, anillos sin polos como el slider) y reparte el largo de un tramo entre filetes vecinos.
- Vista previa: `render_bell_unlit.py` (el 4.º argumento = cuadros de la animación apretar → cargar → soltar) y `plot_bell_section.py` (corte real en colores, para comparar con el PDF).
