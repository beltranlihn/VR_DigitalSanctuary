# -*- coding: utf-8 -*-
"""prueba_sheen.py - la franja clara del horizonte: v1 y v2 con Sheen 0,4 (spec) contra Sheen 0; recorte x2."""
import os, sys
import numpy as np
from PIL import Image
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, AQUI)
import modelo_valle as mv, render_valle as rv
tiles = []
for nom, hf, P, fg in (("v1", mv.h_v1, mv.P1, mv.fog_v1), ("v2", mv.h_v2, mv.P2, mv.fog_v2)):
    for sh in (0.4, 0.0):
        mv.LOOK["Sheen"] = sh
        img, kind, _ = rv.render_persp(hf, P, fg, metaball=False)
        im = Image.fromarray((mv.srgb(img) * 255 + 0.5).astype(np.uint8)).crop((560, 300, 1052, 560)).resize((984, 520))
        rv.etiqueta(im, "%s  Sheen %.1f" % (nom, sh))
        tiles.append(im)
        L = mv.lum(img)[:, 700:1000].mean(axis=1)
        print(nom, "Sheen", sh, "luminancia media por fila (400..520 de a 10):", " ".join("%.3f" % L[r] for r in range(400, 521, 10)))
mv.LOOK["Sheen"] = 0.4
W, H = tiles[0].size
out = Image.new("RGB", (2 * W + 6, 2 * H + 6), (20, 20, 20))
for i, t in enumerate(tiles):
    out.paste(t, ((i % 2) * (W + 6), (i // 2) * (H + 6)))
out.save(os.path.join(AQUI, "prueba_sheen_franja.png"))
