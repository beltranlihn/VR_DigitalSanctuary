"""gen_texts_ic.py - los textos del recorrido v2 de Inner Canvas en un atlas (2026-11-12 noche, PDF de Beltran).

  python tools/innercanvas/gen_texts_ic.py

T_ICTexts.png (2048 x 2048, canal R = letra blanca, fondo negro): cada texto en su celda (alto de fila = 1,45 x el cuerpo de la
letra). Lo usa M_ICText_IC (Rect = u0, v0, us; VS = alto de la celda en UV). Imprime y guarda texts_rects.json:
{clave: [u0, v0, us, vs, aspecto]} (aspecto = ancho / alto de la celda en pixeles: el plano va con ese aspecto).
Claves: hdr, lab0..lab5, sel, cl, cr, warn, hname con sufijo _en / _es; hlang_en y hlang_es (las dos lineas bilingues bajo los
botones de idioma); dot (circulo) y white (bloque para las lineas).
Salida: VR_Test/Content/InnerCanvas/Textures/T_ICTexts.png (Unreal la importa sola) y
VR_Test/Saved/ClaudeScripts/InnerCanvas/texts_rects.json.
"""
import json, os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
OUT = os.path.join(ROOT, 'VR_Test', 'Content', 'InnerCanvas', 'Textures')
RECTS = os.path.join(ROOT, 'VR_Test', 'Saved', 'ClaudeScripts', 'InnerCanvas', 'texts_rects.json')
FONT = os.path.expanduser(r'~\AppData\Local\Microsoft\Windows\Fonts\Avenir Book.ttf')
N = 2048
PAD = 24

TEXTS = [
    ('hdr', 'Instructions', 'Instrucciones', 112),
    ('lab0', 'Color', 'Color', 96),
    ('lab1', 'Brush Type', 'Tipo de pincel', 96),
    ('lab2', 'Brush Size', 'Grosor', 96),
    ('lab3', 'Undo', 'Deshacer', 96),
    ('lab4', 'Redo', 'Rehacer', 96),
    ('lab5', 'Draw', 'Dibujar', 96),
    ('sel', 'Select your dominant hand', 'Elige tu mano dominante', 96),
    ('cl', 'Left handed', 'Mano izquierda', 96),
    ('cr', 'Right handed', 'Mano derecha', 96),
    ('warn', 'Step back into the drawing area', 'Vuelve a la zona de dibujo', 100),
    ('hname', 'Point and press the trigger to write your name', 'Apunta y presiona el gatillo para escribir tu nombre', 76),
]
HLANG = [('hlang_en', 'Point and press the trigger to select a language', 76),
         ('hlang_es', 'Apunta y presiona el gatillo para seleccionar el idioma', 76)]


def main():
    im = Image.new('L', (N, N), 0)
    d = ImageDraw.Draw(im)
    items = []
    for key, en, es, size in TEXTS:
        items.append((key + '_en', en, size))
        items.append((key + '_es', es, size))
    items += HLANG
    rects = {}
    x, y, rowh = 0, 0, 0
    for key, txt, size in items:
        f = ImageFont.truetype(FONT, size)
        asc, desc = f.getmetrics()
        h = int(round(size * 1.45))
        w = int(d.textlength(txt, font=f)) + 2 * PAD
        if x + w > N:
            x, y, rowh = 0, y + rowh + 8, 0
        top = y + (h - (asc + desc)) // 2
        d.text((x + PAD, top), txt, fill=255, font=f)
        rects[key] = [round(x / N, 6), round(y / N, 6), round(w / N, 6), round(h / N, 6), round(w / float(h), 5)]
        x += w + 8
        rowh = max(rowh, h)
    # punto (circulo lleno, suave) y bloque blanco para las lineas
    y += rowh + 8
    c = 128
    big = Image.new('L', (c * 4, c * 4), 0)
    ImageDraw.Draw(big).ellipse((16, 16, c * 4 - 16, c * 4 - 16), fill=255)
    im.paste(big.resize((c, c), Image.LANCZOS), (0, y))
    rects['dot'] = [0.0, round(y / N, 6), round(c / N, 6), round(c / N, 6), 1.0]
    d.rectangle((c + 16, y, c + 16 + 63, y + 63), fill=255)
    rects['white'] = [round((c + 16 + 16) / N, 6), round((y + 16) / N, 6), round(32 / N, 6), round(32 / N, 6), 1.0]
    print('alto usado: %d px de %d' % (y + c, N))
    os.makedirs(OUT, exist_ok=True)
    im.save(os.path.join(OUT, 'T_ICTexts.png'))
    json.dump(rects, open(RECTS, 'w', encoding='utf-8'), indent=1)
    print(json.dumps(rects))


if __name__ == '__main__':
    main()
