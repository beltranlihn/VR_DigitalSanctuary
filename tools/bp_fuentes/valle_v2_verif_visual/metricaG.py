# G = rampa maxima de ln(Y lineal) por grado de elevacion, en la banda del piso bajo el horizonte (terreno solo).
# A 25 px/grado, un escalon dentro de un pixel da G = dlnY / 0,04 grados. Se mide tambien sobre 0,2 grados (5 px)
# para no premiar el suavizado de un solo pixel.
import sys, numpy as np, vrender as vr
for tag in sys.argv[1:]:
    lin = np.load("pano_%s_lin.npy" % tag).astype(np.float64)
    dist = np.load("pano_%s_dist.npy" % tag).astype(np.float64)
    Hh, W = dist.shape
    el = 14.0 - (np.arange(Hh) + 0.5) / 25.0
    ok = np.isfinite(dist) & ~((dist < 700.0) & (el[:, None] > -9.0))
    lnY = np.log(np.maximum(vr.Y(lin), 1e-4))
    band = (el < -0.25) & (el > -8.0)
    res = {}
    for k in (1, 5):
        d = np.abs(lnY[k:] - lnY[:-k]) / (k / 25.0) * 100.0
        v = ok[k:] & ok[:-k] & band[k:, None] & band[:-k, None]
        d = np.where(v, d, 0.0)
        g = d.max(0)
        res[k] = g
        print("%s  G sobre %.2f grados: mediana por azimut %.0f %%/grado, p90 %.0f, max %.0f; azimuts con G > 50: %.1f %%, > 100: %.1f %%"
              % (tag, k / 25.0, np.median(g), np.percentile(g, 90), g.max(), 100 * (g > 50).mean(), 100 * (g > 100).mean()))
