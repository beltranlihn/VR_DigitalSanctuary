# -*- coding: utf-8 -*-
"""renders_diag.py - imagenes del diagnostico de escala (v1 vs candidato v2), con render_valle.py.
Uso: python renders_diag.py [tag=_x] [clave=valor ...]   (claves de modelo_valle.P2 pisan el candidato)
Salidas: r_v2_frente<tag>.png, r_v2_frente_t41<tag>.png, pano_v1_v2<tag>.png, lado_v1_v2<tag>.png
"""
import math
import os
import sys

import numpy as np
from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import modelo_valle as mv  # noqa: E402
import render_valle as rv  # noqa: E402

args = dict(a.split("=", 1) for a in sys.argv[1:] if "=" in a)
tag = args.pop("tag", "")
for k, v in args.items():
    if k in mv.P2:
        mv.P2[k] = float(v)
        print("P2 %s = %s" % (k, v))

def contraste_metaball(img, kind, nombre):
    """Borde del metaball: luminancia 4 px ADENTRO contra 4 px AFUERA, en 360 angulos alrededor del disco.
    Relacion (L1 + 0,05)/(L2 + 0,05) (WCAG) y Weber |L1 - L2|/L2. Arriba = mitad superior (cielo detras)."""
    ys, xs = np.nonzero(kind == 2)
    cy, cx = ys.mean(), xs.mean()
    R = math.sqrt(ys.size / math.pi)
    th = np.radians(np.arange(360))
    L = mv.lum(img)
    res = {}
    for nom, sel in (("arriba (0-180)", (th > 0) & (th < math.pi)), ("abajo (180-360)", th > math.pi)):
        a = th[sel]
        yi = np.clip((cy - (R - 4) * np.sin(a)).astype(int), 0, img.shape[0] - 1)
        xi = np.clip((cx + (R - 4) * np.cos(a)).astype(int), 0, img.shape[1] - 1)
        yo = np.clip((cy - (R + 4) * np.sin(a)).astype(int), 0, img.shape[0] - 1)
        xo = np.clip((cx + (R + 4) * np.cos(a)).astype(int), 0, img.shape[1] - 1)
        Li, Lo = L[yi, xi], L[yo, xo]
        ratio = (np.maximum(Li, Lo) + 0.05) / (np.minimum(Li, Lo) + 0.05)
        web = np.abs(Li - Lo) / np.maximum(Lo, 1e-3)
        res[nom] = (float(ratio.min()), float(np.median(ratio)), float(web.min()), float(np.median(web)),
                    float(np.median(Lo)))
        print("CONTRASTE %-6s %-16s relacion min/med = %.2f / %.2f   Weber min/med = %.3f / %.3f   L fondo med = %.3f" % (
            nombre, nom, *res[nom]))
    return res


img2, kind2, _ = rv.render_persp(mv.h_v2, mv.P2, mv.fog_v2)
rv.to_png(img2, os.path.join(AQUI, "r_v2_frente%s.png" % tag))
img1, kind1, _ = rv.render_persp(mv.h_v1, mv.P1, mv.fog_v1)
contraste_metaball(img1, kind1, "v1")
contraste_metaball(img2, kind2, "v2" + tag)
img2b, _, _ = rv.render_persp(mv.h_v2, mv.P2, mv.fog_v2, t=41.5)
rv.to_png(img2b, os.path.join(AQUI, "r_v2_frente_t41%s.png" % tag))

r1 = Image.open(os.path.join(AQUI, "r_v1_frente.png"))
r2 = Image.open(os.path.join(AQUI, "r_v2_frente%s.png" % tag))
lado = Image.new("RGB", (r1.width + r2.width + 8, r1.height), (20, 20, 20))
lado.paste(r1, (0, 0))
lado.paste(r2, (r1.width + 8, 0))
rv.etiqueta(lado, "v1 (hoy): colinas a 10-44 m, 4-8 m de alto", (12, 10))
rv.etiqueta(lado, "v2 (candidato): piso quieto 12 m, colinas 80-230 m y 300-600 m, niebla + altura", (r1.width + 20, 10))
lado.save(os.path.join(AQUI, "lado_v1_v2%s.png" % tag))

p1, yt1, fp1 = rv.render_pano(mv.h_v1, mv.P1, mv.fog_v1)
p2, yt2, fp2 = rv.render_pano(mv.h_v2, mv.P2, mv.fog_v2)


def marcas(img, ytop, fp):
    im = Image.fromarray((mv.srgb(img) * 255 + 0.5).astype(np.uint8))
    from PIL import ImageDraw
    dr = ImageDraw.Draw(im)
    W = im.width
    yh = int(round(ytop))
    for x in range(0, W, 6):
        dr.point((x, yh), fill=(255, 255, 255))
    for az in range(-180, 181, 45):
        x = int((az + 180) * W / 360.0)
        dr.line([(x, 0), (x, 6)], fill=(255, 255, 255))
        dr.text((x + 2, 8), "%d" % az, fill=(255, 255, 255))
    for el in (5, 10, 15, 20):
        y = int(ytop - fp * math.tan(math.radians(el)))
        dr.line([(0, y), (8, y)], fill=(255, 255, 255))
        dr.text((10, y - 6), "%d" % el, fill=(255, 255, 255))
    return im


a = marcas(p1, yt1, fp1)
b = marcas(p2, yt2, fp2)
pano = Image.new("RGB", (a.width, a.height + b.height + 6), (20, 20, 20))
pano.paste(a, (0, 0))
pano.paste(b, (0, a.height + 6))
rv.etiqueta(pano, "v1 - 360 deg (az -180..180; linea punteada = horizonte; marcas = elevacion)", (60, 24))
rv.etiqueta(pano, "v2 candidato - 360 deg", (60, a.height + 30))
pano.save(os.path.join(AQUI, "pano_v1_v2%s.png" % tag))
print("RENDERS listos", tag)
