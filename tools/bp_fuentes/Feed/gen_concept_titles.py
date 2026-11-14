# gen_concept_titles.py (2026-10-29) - nombres de los conceptos de Test_Feed, horneados como los titulos de la Obra:
# Michroma, mismo tamano y tracking que T_Title_SOULCHARGER (ajuste por bbox, igual que T_Title_DIGITALSANCTUARY),
# R = letra nitida, G = resplandor (blur 10 x 1,4), 2048 x 512. Escribe titles/T_Concept_<NOMBRE>.png y titles.json (U0/U1 =
# el tramo horizontal de la palabra, para el barrido del material liquido).
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np, os, json, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
F = r"C:/Users/beltr/Desktop/Alma Digital Studio/Rito Digital Visual/TypeWriter/fonts/retro/Michroma.ttf"
WORDS = sys.argv[1:] or ['AWARENESS', 'LOVE', 'ATTRACTION', 'LIVE', 'DEEP', 'MIND']
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
best = None
for size in range(135, 170):
    for t in [i / 200 for i in range(0, 80)]:
        bb = render('SOUL CHARGER', size, t).getbbox()
        err = abs((bb[2] - bb[0]) - 1855) + abs((bb[3] - bb[1]) - 118) * 3 + abs(bb[1] - 192)
        if best is None or err < best[0]: best = (err, size, t, bb)
_, size, t, _ = best
meta = {'size': size, 'track': t, 'words': {}}
for w in WORDS:
    r = render(w, size, t)
    bb = r.getbbox()
    g = np.clip(np.array(r.filter(ImageFilter.GaussianBlur(10)), dtype=float) * 1.4, 0, 255).astype('uint8')
    Image.merge('RGBA', (r, Image.fromarray(g), Image.new('L', r.size, 0), Image.new('L', r.size, 255))).save('titles/T_Concept_%s.png' % w)
    meta['words'][w] = {'U0': round(bb[0] / 2048.0, 4), 'U1': round(bb[2] / 2048.0, 4), 'bbox': bb}
json.dump(meta, open('titles/titles.json', 'w'), indent=1)
print(json.dumps(meta))
