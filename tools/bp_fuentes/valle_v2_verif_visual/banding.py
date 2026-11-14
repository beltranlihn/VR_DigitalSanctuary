# Banding: ancho de cada escalon de 8 bits (en px del Quest, 25 px/grado) y residuo del cuantizado con el dither del
# shader (+-0,5/255 en LINEAL, antes de la codificacion sRGB del hardware) vs sin dither vs dither correcto en sRGB.
import numpy as np, vrender as vr
from scipy.ndimage import gaussian_filter
tag = "v2_t0_p25"
lin = np.load("pano_%s_lin.npy" % tag).astype(np.float64)
dist = np.load("pano_%s_dist.npy" % tag).astype(np.float64)
Hh, W = dist.shape
el = 14.0 - (np.arange(Hh) + 0.5) / 25.0
yy, xx = np.mgrid[0:Hh, 0:W].astype(np.float64)
def hashd(x, y):
    p = np.stack([x, y, x], -1) * 0.1031
    p = p - np.floor(p)
    p = p + (p * (p[..., [1, 2, 0]] + 33.33)).sum(-1, keepdims=True)
    v = (p[..., 0] + p[..., 1]) * p[..., 2]
    return v - np.floor(v) - 0.5
dith = hashd(xx + 0.5, yy + 0.5)
s = 255.0 * vr.srgb(lin)
q0 = np.round(s)
q1 = np.round(255.0 * vr.srgb(lin + dith[..., None] / 255.0))
q2 = np.round(s + dith[..., None])
# derivada sRGB por nivel lineal
d = 0.4396 * np.power(np.maximum(lin, 1e-3), -0.5833)
print("amplitud del dither del shader en LSB sRGB (pico, canal G): p10 %.2f p50 %.2f p90 %.2f  (hace falta >= 0,5 para romper un escalon)"
      % tuple(np.percentile(0.5 * d[..., 1], [10, 50, 90])))
regiones = {"cielo (el 1..14)": (el > 1.0), "piso (el -12..-2)": (el < -2.0)}
esf = np.isfinite(dist) & (dist < 700)
for nom, rm in regiones.items():
    m = rm[:, None] & ~esf
    for nq, q in (("sin dither", q0), ("dither del shader", q1), ("dither en sRGB", q2)):
        e = gaussian_filter((q - s)[..., 1], 3.0)
        e = np.where(m, e, 0.0)
        # amplitud de contornos: p99 de |error suavizado|
        print("  %-18s %-18s |residuo suavizado (sigma 3 px)| p50 %.2f p99 %.2f LSB" % (nom, nq, np.median(np.abs(e[m])), np.percentile(np.abs(e[m]), 99)))
# ancho de los escalones: grados por nivel (canal G) a lo largo de la elevacion
g = np.abs(np.gradient(s[..., 1], axis=0)) * 25.0   # niveles por grado
for nom, rm in regiones.items():
    m = rm[:, None] & ~esf & (np.abs(np.gradient(dist, axis=0)) < 50)
    gg = g[m]
    print("  %-18s gradiente vertical: p10 %.2f p50 %.2f niveles/grado -> escalon de %.1f / %.1f px del Quest" % (nom, np.percentile(gg, 10), np.median(gg), 25.0 / max(np.percentile(gg, 10), 1e-3), 25.0 / max(np.median(gg), 1e-3)))
