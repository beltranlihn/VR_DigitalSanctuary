# -*- coding: utf-8 -*-
"""d_picos_oleaje.py - velocidad de los PICOS del oleaje (maximos locales de la altura del oleaje A(r)*s) en planta:
la suma de 4 ondas planas tiene picos que pueden viajar MAS rapido que cualquier onda sola (interferencia).
Se siguen los picos entre t y t+0,1 s y se da su velocidad angular TANGENCIAL vista desde el usuario (deg/s), por
distancia. Solo la capa 3 (el oleaje), evaluada con fastvalley (misma cuenta del HLSL)."""
import numpy as np
from scipy.ndimage import maximum_filter
from fastvalley import Grid
from h_hlsl import D
xs = np.arange(-60000, 60001, 100.0)
X, Y = np.meshgrid(xs, xs, indexing="xy")
p = dict(D); p["HillAmp"] = 0.0; p["FarAmp"] = 0.0; p["FarBase"] = 0.0
g = Grid(X, Y, p)
R = np.hypot(X, Y)
rng = np.random.default_rng(3)
DTP = 0.5

def refina(h, a, b):
    dx = 0.5 * (h[a, b - 1] - h[a, b + 1]) / (h[a, b - 1] - 2 * h[a, b] + h[a, b + 1] + 1e-12)
    dy = 0.5 * (h[a - 1, b] - h[a + 1, b]) / (h[a - 1, b] - 2 * h[a, b] + h[a + 1, b] + 1e-12)
    return X[a, b] + 100.0 * dx, Y[a, b] + 100.0 * dy

res = {k: [] for k in ("40-60", "60-100", "100-150", "150-300", "300-590")}
lims = {"40-60": (4000, 6000), "60-100": (6000, 10000), "100-150": (10000, 15000), "150-300": (15000, 30000), "300-590": (30000, 59000)}
for t in rng.uniform(0, 900, 16):
    h0 = g.eval(t, grad=False); h1 = g.eval(t + DTP, grad=False)
    pk0 = (h0 == maximum_filter(h0, size=9)) & (h0 > 0) & (R > 3000) & (np.abs(np.arange(len(xs))[None, :] - 600) < 598) & (np.abs(np.arange(len(xs))[:, None] - 600) < 598) & (R < 59000)
    pk1 = (h1 == maximum_filter(h1, size=9)) & (h1 > 0) & (R > 3000) & (np.abs(np.arange(len(xs))[None, :] - 600) < 598) & (np.abs(np.arange(len(xs))[:, None] - 600) < 598) & (R < 59000)
    i0 = np.argwhere(pk0); i1 = np.argwhere(pk1)
    P1 = np.array([refina(h1, a, b) for (a, b) in i1])
    for (a, b) in i0:
        x0, y0 = refina(h0, a, b)
        d = np.hypot(P1[:, 0] - x0, P1[:, 1] - y0)
        j = np.argmin(d)
        if d[j] > 1500: continue                      # mas de 25 m/s: no es el mismo pico
        # refinamiento subpixel no hace falta: se usa el promedio de muchos picos con paso de 1 m en 0.1 s
        vx, vy = (P1[j, 0] - x0) / DTP, (P1[j, 1] - y0) / DTP
        r = np.hypot(x0, y0)
        vt = abs(vx * (-y0 / r) + vy * (x0 / r))       # componente tangencial cm/s
        for k, (lo, hi) in lims.items():
            if lo <= r < hi:
                res[k].append((np.degrees(vt / r), np.hypot(vx, vy) / 100.0, h0[a, b]))
for k, v in res.items():
    v = np.array(v)
    if len(v):
        print("%8s m: picos %4d | vel. angular tangencial mediana %.2f, p90 %.2f, max %.2f deg/s | vel. en planta mediana %.1f, p90 %.1f, max %.1f m/s | altura del pico mediana %.0f cm" % (
            k, len(v), np.median(v[:, 0]), np.percentile(v[:, 0], 90), v[:, 0].max(), np.median(v[:, 1]), np.percentile(v[:, 1], 90), v[:, 1].max(), np.median(v[:, 2])))
print("fraccion de picos con vel. angular tangencial > 2.5 deg/s y > 1 deg/s, por banda:")
for k, v in res.items():
    v = np.array(v)
    if len(v):
        print("  %8s m: n %4d  >2.5: %.1f%%  >1: %.1f%%  (vel. en planta > 5.4 m/s, la fase mas rapida: %.0f%%)" % (
            k, len(v), 100 * np.mean(v[:, 0] > 2.5), 100 * np.mean(v[:, 0] > 1), 100 * np.mean(v[:, 1] > 5.4)))
