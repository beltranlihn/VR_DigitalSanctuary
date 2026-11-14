"""gen_tutor_tex_ic.py - texturas del tutorial y del cierre de Inner Canvas (2026-11-12).

  python tools/innercanvas/gen_tutor_tex_ic.py

1) T_ICLabels.png (2048 x 2048, canal R = letra blanca): las etiquetas del tutorial para M_ICKey_IC. Fila k (256 px de alto) =
   etiqueta k; columna izquierda (0..1023) en ingles, derecha (1024..2047) en espanol. Imprime los Rect (u0, v0, us) de cada una.
   Orden: 0 COLOR, 1 BRUSH, 2 SIZE, 3 UNDO, 4 REDO, 5 TRIGGER. La fila 7 queda vacia (las lineas usan esa celda: placa sin letra).
2) T_ICReset_Text.png (2048 x 509, gris): RESET para la tapa del boton (mismo formato que T_English_Text de la demo).
Salida: VR_Test/Content/InnerCanvas/Textures/ (Unreal las importa solo al aparecer el archivo).
"""
import json, os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
OUT = os.path.join(ROOT, 'VR_Test', 'Content', 'InnerCanvas', 'Textures')
FONT = os.path.expanduser(r'~\AppData\Local\Microsoft\Windows\Fonts\Quicksand-Bold.ttf')
EN = ['COLOR', 'BRUSH', 'SIZE', 'UNDO', 'REDO', 'TRIGGER']
ES = ['COLOR', 'PINCEL', 'TAMAÑO', 'DESHACER', 'REHACER', 'GATILLO']
N, C = 2048, 256


def atlas():
    im = Image.new('L', (N, N), 0)
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FONT, 132)
    rects = {'en': [], 'es': []}
    for k in range(6):
        for col, words in ((0, EN), (1, ES)):
            w = words[k]
            bb = d.textbbox((0, 0), w, font=f)
            tw = bb[2] - bb[0]
            x0 = col * 1024 + 24
            y = k * C + (C - (bb[3] - bb[1])) // 2 - bb[1]
            d.text((x0 - bb[0], y), w, fill=255, font=f)
            us = (tw + 48) / float(N)
            rects['en' if col == 0 else 'es'].append([round((x0 - 24) / float(N), 5), round(k * C / float(N), 5), round(us, 5)])
    im.save(os.path.join(OUT, 'T_ICLabels.png'))
    return rects


def reset():
    im = Image.new('L', (2048, 509), 0)
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FONT, 150)
    bb = d.textbbox((0, 0), 'RESET', font=f)
    x = (2048 - (bb[2] - bb[0])) // 2 - bb[0]
    y = 190 + (115 - (bb[3] - bb[1])) // 2 - bb[1]
    d.text((x, y), 'RESET', fill=255, font=f)
    im.save(os.path.join(OUT, 'T_ICReset_Text.png'))


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    r = atlas()
    reset()
    print(json.dumps(r))
