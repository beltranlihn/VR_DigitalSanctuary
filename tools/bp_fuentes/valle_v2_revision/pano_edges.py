# Uso: python pano_edges.py '<json>' <tag> <t> [ojos cm]  -> panorama con los bordes de oclusion marcados en rojo.
import sys, json, numpy as np, vexp as vm, vrx as vr, metrics as M
from PIL import Image
over = json.loads(sys.argv[1]); tag = sys.argv[2]; t = float(sys.argv[3]); ez = float(sys.argv[4]) if len(sys.argv) > 4 else 120.0
q = vm.params(**over)
q["ShadowCenter"] = (380.0, 0.0, 125.0 + ez - 120.0)
m = vr.Modelo("v2", q)
eye = np.array([0.0, 0.0, ez])
ppd = 8.0
az, sl, el = vr.cilindrica(-180.0, 180.0, -5.0, 9.0, ppd)
img, dist, _ = vr.render_cols(m, eye, az, sl, t, rho_min=20.0, J=3000, chunk=96, esfera=((380.0, 0.0, 125.0 + ez - 120.0), 110.0))
s = np.clip(np.round(255 * vr.srgb(img)), 0, 255).astype(np.uint8)
mk = s.copy()
# bordes de oclusion en una grilla FINA (0,02 grados) bajo el horizonte, marcados en la fila de la imagen
elf = np.arange(0.5, -5.0, -0.02)
Df = M.pano_geo(q, t, az, elf, ez)
ok = np.isfinite(Df[:-1]) & np.isfinite(Df[1:])
edge = ok & (Df[:-1] / Df[1:] > 1.25)
ys, xs = np.nonzero(edge)
for y, x in zip(ys, xs):
    if abs(az[x]) < 17 and Df[y + 1, x] < 700: continue
    r = int(round((9.0 - elf[y]) * ppd - 0.5))
    mk[max(r - 1, 0):r + 2, x] = (255, 30, 20)
out = np.concatenate([s, np.zeros((4, s.shape[1], 3), np.uint8), mk], 0)
Image.fromarray(out).save("pano_%s.png" % tag)
W = out.shape[1]
Image.fromarray(out[:, :W // 2]).save("pano_%s_a.png" % tag); Image.fromarray(out[:, W // 2:]).save("pano_%s_b.png" % tag)
print("ok", out.shape, "columnas con borde: %.1f%%" % (100 * edge.any(0).mean()))
