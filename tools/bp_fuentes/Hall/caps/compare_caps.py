# compare_caps.py - decodifica caps/cap_*.txt a PNG y mide la diferencia media entre pares (0..255).
# Veredicto: base ~ g2000 (look intacto) y g0 != g2000 (la CollectionParameter RESUELVE). Si g0 == g2000: NO resolvió.
import json, base64, io, os, sys
from PIL import Image, ImageChops, ImageStat
D = os.path.dirname(os.path.abspath(__file__))
def load(n):
    p = os.path.join(D, 'cap_%s.txt' % n)
    if not os.path.exists(p):
        return None
    t = open(p, encoding='utf-8').read()
    try:
        j = json.loads(t)
        while isinstance(j, str):
            j = json.loads(j)
        data = j['image']['data'] if 'image' in j else j['returnValue']['image']['data']
    except Exception:
        data = t.split('"data": "')[1].split('"')[0]
    im = Image.open(io.BytesIO(base64.b64decode(data))).convert('RGB')
    im.save(os.path.join(D, 'cap_%s.png' % n))
    return im
ims = {n: load(n) for n in ['base', 'g2000', 'g0']}
def diff(a, b):
    if ims[a] is None or ims[b] is None:
        return None
    return round(sum(ImageStat.Stat(ImageChops.difference(ims[a], ims[b])).mean) / 3.0, 3)
print({'base~g2000': diff('base', 'g2000'), 'g2000~g0': diff('g2000', 'g0'),
       'mean': {n: (round(sum(ImageStat.Stat(i).mean) / 3.0, 2) if i else None) for n, i in ims.items()}})
