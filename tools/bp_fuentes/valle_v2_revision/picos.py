# Uso: python picos.py  -> velocidad lateral de los picos del oleaje geometrico (capa lejana), seguidos en planta.
# velocidad de los PICOS del oleaje geometrico (modelo final): maximos locales de A*s, seguidos entre t y t+0,5 s
import numpy as np, vexp as vm
from scipy.ndimage import maximum_filter
xs = np.arange(-60000, 60001, 100.0)
X, Y = np.meshgrid(xs, xs, indexing="xy")
R = np.hypot(X, Y)
q = vm.params()
rng = np.random.default_rng(3)
DTP = 0.5
def refina(h, a, b):
    dx = 0.5 * (h[a, b - 1] - h[a, b + 1]) / (h[a, b - 1] - 2 * h[a, b] + h[a, b + 1] + 1e-12)
    dy = 0.5 * (h[a - 1, b] - h[a + 1, b]) / (h[a - 1, b] - 2 * h[a, b] + h[a + 1, b] + 1e-12)
    return X[a, b] + 100.0 * dx, Y[a, b] + 100.0 * dy
lims = {"280-400": (28000, 40000), "400-590": (40000, 59000)}
res = {k: [] for k in lims}
inner = (np.abs(np.arange(len(xs))[None, :] - 600) < 598) & (np.abs(np.arange(len(xs))[:, None] - 600) < 598)
for t in rng.uniform(0, 900, 16):
    h0 = vm.valley_grad(X, Y, t, q, capas=(3,))[2]; h1 = vm.valley_grad(X, Y, t + DTP, q, capas=(3,))[2]
    pk0 = (h0 == maximum_filter(h0, size=9)) & (h0 > 0) & (R > 28000) & (R < 59000) & inner
    pk1 = (h1 == maximum_filter(h1, size=9)) & (h1 > 0) & (R > 28000) & (R < 59000) & inner
    i1 = np.argwhere(pk1); P1 = np.array([refina(h1, a, b) for (a, b) in i1])
    for (a, b) in np.argwhere(pk0):
        x0, y0 = refina(h0, a, b)
        d = np.hypot(P1[:, 0] - x0, P1[:, 1] - y0); j = np.argmin(d)
        if d[j] > 1500: continue
        vx, vy = (P1[j, 0] - x0) / DTP, (P1[j, 1] - y0) / DTP
        r = np.hypot(x0, y0); vt = abs(vx * (-y0 / r) + vy * (x0 / r))
        for k, (lo, hi) in lims.items():
            if lo <= r < hi: res[k].append((np.degrees(vt / r), np.hypot(vx, vy) / 100.0))
for k, v in res.items():
    v = np.array(v)
    print("%s m: picos %d | vel. angular tangencial mediana %.2f p90 %.2f max %.2f deg/s | >2,5: %.1f%% >1: %.1f%% | en planta mediana %.1f p90 %.1f max %.1f m/s" % (
        k, len(v), np.median(v[:, 0]), np.percentile(v[:, 0], 90), v[:, 0].max(), 100*np.mean(v[:, 0] > 2.5), 100*np.mean(v[:, 0] > 1), np.median(v[:, 1]), np.percentile(v[:, 1], 90), v[:, 1].max()))
