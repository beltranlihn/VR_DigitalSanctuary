# -*- coding: utf-8 -*-
"""Imagen comparativa rotulada de la capa viva del valle (reposo / inhala-retiene / exhala / mapa de cambio) y numeros
por region. Lee los renders de render_valle_live.py (misma carpeta)."""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
AQUI = os.path.dirname(os.path.abspath(__file__))
def load(t):
    return np.asarray(Image.open(os.path.join(AQUI, "preview_valle_t0_%s.png" % t)).convert("RGB")).astype(np.float64)
neu, inh, exh = load("neutro"), load("inhala"), load("exhala")
H, W = neu.shape[:2]
def font(sz):
    for f in ("C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf"):
        if os.path.exists(f):
            return ImageFont.truetype(f, sz)
def label(im, a, b):
    d = ImageDraw.Draw(im)
    f1, f2 = font(26), font(18)
    w = max(d.textlength(a, font=f1), d.textlength(b, font=f2))
    d.rectangle([6, 4, 20 + w, 66], fill=(20, 22, 40))
    d.text((14, 8), a, fill=(240, 240, 250), font=f1)
    d.text((14, 40), b, fill=(200, 200, 220), font=f2)
    return im
d = np.abs(inh - exh).mean(2)
k = np.clip(d * 10.0 / 255.0, 0, 1)[..., None]
gris = neu.mean(2, keepdims=True) * 0.35
mapa = gris * (1 - k) + k * np.array([255.0, 140.0, 50.0])
tiles = [label(Image.fromarray(neu.astype(np.uint8)), "Reposo (S 0) = look actual exacto", "capa viva neutra: 0 pixeles distintos"),
         label(Image.fromarray(inh.astype(np.uint8)), "Inhala / retiene (S +1)", "bruma abre, resplandor sube y se afina, sombra se recoge (mas densa)"),
         label(Image.fromarray(exh.astype(np.uint8)), "Exhala (S -1)", "bruma cierra y entibia, resplandor baja, sombra se abre y se ablanda"),
         label(Image.fromarray(mapa.astype(np.uint8)), "Inhala vs exhala (x10)", "donde cambia el valle (naranja)")]
tw, th = 700, int(H * 700 / W)
can = Image.new("RGB", (4 * tw, th), (14, 15, 26))
for i, t in enumerate(tiles):
    can.paste(t.resize((tw, th), Image.LANCZOS), (i * tw, 0))
can.save(os.path.join(AQUI, "valle_capa_viva_comparacion.png"))
# numeros por region (vista del usuario: horizonte ~ fila 40-55 %, cielo alto < 30 %, piso cercano > 85 %)
reg = {"cielo alto": (0.00, 0.30), "horizonte y colinas": (0.38, 0.56), "piso medio": (0.60, 0.80), "piso cercano (sombra)": (0.85, 1.00)}
lum = lambda im: 0.2126 * im[..., 0] + 0.7152 * im[..., 1] + 0.0722 * im[..., 2]
for n, (a, b) in reg.items():
    sl = slice(int(a * H), int(b * H))
    dd = np.abs(inh[sl] - exh[sl]).mean(2)
    print("%-22s cambio medio %.1f  p90 %.1f  | luma inhala-exhala %+.1f | R-B exhala-inhala %+.1f (8 bits)"
          % (n, dd.mean(), np.percentile(dd, 90), (lum(inh[sl]) - lum(exh[sl])).mean(),
             ((exh[sl][..., 0] - exh[sl][..., 2]) - (inh[sl][..., 0] - inh[sl][..., 2])).mean()))
print("reposo vs inhala: cambio medio %.2f, vs exhala %.2f" % (np.abs(neu - inh).mean(), np.abs(neu - exh).mean()))
