"""gen_title_ic.py - el titulo INNER CANVAS, horneado como los titulos de etapa de la Obra.

  python tools/innercanvas/gen_title_ic.py
  python tools/innercanvas/gen_title_ic.py "ENDES:YA PUEDES|QUITARTE LAS GAFAS" "ENDEN:YOU CAN NOW TAKE|OFF YOUR HEADSET"   (el cierre)

Michroma, mismo tamano y tracking que T_Title_SOULCHARGER (ajuste por bbox, igual que T_Title_DIGITALSANCTUARY y los
conceptos de Test_Feed: VR_Test/Saved/ClaudeScripts/Feed/gen_concept_titles.py). R = letra nitida, G = resplandor
(blur 10 x 1,4), 2048 x 512. Salida: VR_Test/Saved/ClaudeScripts/InnerCanvas/tex/T_Title_INNERCANVAS.png
(se importa a /Game/InnerCanvas/Textures con compresion TC_EditorIcon, sin mips raros: ver DEMO-BDW.md "Titulos").
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
OUT = os.path.join(ROOT, 'VR_Test', 'Saved', 'ClaudeScripts', 'InnerCanvas', 'tex')
F = r"C:/Users/beltr/Desktop/Alma Digital Studio/Rito Digital Visual/TypeWriter/fonts/retro/Michroma.ttf"


def render(text, size, track, W=2048, H=512, yc=251):
    f = ImageFont.truetype(F, size)
    im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im)
    ws = [d.textlength(c, font=f) for c in text]; tr = size * track
    total = sum(ws) + tr * (len(text) - 1)
    x = (W - total) / 2
    cap = -f.getbbox('H', anchor='ls')[1]
    base = yc + cap / 2
    for c, w in zip(text, ws):
        d.text((x, base), c, font=f, fill=255, anchor='ls'); x += w + tr
    return im


def main():
    os.makedirs(OUT, exist_ok=True)
    best = None
    for size in range(135, 170):
        for t in [i / 200 for i in range(0, 80)]:
            bb = render('SOUL CHARGER', size, t).getbbox()
            err = abs((bb[2] - bb[0]) - 1855) + abs((bb[3] - bb[1]) - 118) * 3 + abs(bb[1] - 192)
            if best is None or err < best[0]:
                best = (err, size, t)
    _, size, t = best
    for word in (sys.argv[1:] or ['INNER CANVAS']):
        if '|' in word:
            # mensaje de dos lineas (el cierre: "YA PUEDES|QUITARTE LAS GAFAS"): las dos con el mismo cuerpo, el mas grande que
            # entra en 1900 px; nombre = T_Title_ + la primera palabra de la etiqueta que va antes de ':' (p. ej. ENDES:YA PUEDES|...)
            tag, _, msg = word.partition(':')
            l1, l2 = msg.split('|')
            k = 1.0
            while max(render(l1, int(size * k), t).getbbox()[2] - render(l1, int(size * k), t).getbbox()[0],
                      render(l2, int(size * k), t).getbbox()[2] - render(l2, int(size * k), t).getbbox()[0]) > 1900:
                k -= 0.02
            sz = int(size * k)
            gap = int(sz * 0.62)
            a = render(l1, sz, t, yc=256 - gap); b = render(l2, sz, t, yc=256 + gap)
            r = Image.fromarray(np.maximum(np.array(a), np.array(b)))
            word = tag
        else:
            r = render(word, size, t)
        g = np.clip(np.array(r.filter(ImageFilter.GaussianBlur(10)), dtype=float) * 1.4, 0, 255).astype('uint8')
        name = 'T_Title_' + word.replace(' ', '')
        Image.merge('RGBA', (r, Image.fromarray(g), Image.new('L', r.size, 0), Image.new('L', r.size, 255))).save(os.path.join(OUT, name + '.png'))
        print(name, 'size', size, 'track', t, 'bbox', r.getbbox())


if __name__ == '__main__':
    main()
