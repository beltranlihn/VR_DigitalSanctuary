"""gen_keyatlas_ic.py - el atlas de las teclas de Inner Canvas (2048 x 2048, celdas de 256 px, canal R = letra blanca).

  python tools/innercanvas/gen_keyatlas_ic.py

Quicksand Bold (la fuente de la obra). Celdas (columna, fila, ancho): A..Z y la N con tilde en las filas 0-3 (8 por fila);
SPACE (0,4,4) y ESPACIO (4,4,4); DELETE (0,5,2), BORRAR (2,5,2), OK (4,5,2). El material M_ICKey_IC dibuja la placa y toma la
letra de la celda conservando su proporcion. El layout es el de VR_Test/Saved/ClaudeScripts/InnerCanvas/ic_kb_layout.py.
Salida: VR_Test/Saved/ClaudeScripts/InnerCanvas/tex/T_ICKeyAtlas.png
"""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
OUT = os.path.join(ROOT, 'VR_Test', 'Saved', 'ClaudeScripts', 'InnerCanvas', 'tex', 'T_ICKeyAtlas.png')
FONT = os.path.expanduser(r'~\AppData\Local\Microsoft\Windows\Fonts\Quicksand-Bold.ttf')
N, C = 2048, 256
LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' + 'Ñ'
WORDS = [('SPACE', 0, 4, 4), ('ESPACIO', 4, 4, 4), ('DELETE', 0, 5, 2), ('BORRAR', 2, 5, 2), ('OK', 4, 5, 2)]


def put(d, text, col, row, w, cap, maxw, ref=None):
    size = 40
    while True:
        f = ImageFont.truetype(FONT, size + 2)
        bb = d.textbbox((0, 0), ref or text, font=f)
        if (bb[3] - bb[1]) > cap or (bb[2] - bb[0]) > maxw:
            break
        size += 2
    f = ImageFont.truetype(FONT, size)
    cx = col * C + w * C / 2.0
    cy = row * C + C / 2.0
    d.text((cx, cy), text, font=f, fill=255, anchor='mm')


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    im = Image.new('L', (N, N), 0)
    d = ImageDraw.Draw(im)
    for i, ch in enumerate(LETTERS):
        put(d, ch, i % 8, i // 8, 1, 118, 200, ref='H')   # todas las letras al mismo tamano (el de la H)
    for text, col, row, w in WORDS:
        put(d, text, col, row, w, 84, w * C - 90)
    z = Image.new('L', (N, N), 0)
    Image.merge('RGBA', (im, z, z, Image.new('L', (N, N), 255))).save(OUT)
    print('ok', OUT)


if __name__ == '__main__':
    main()
