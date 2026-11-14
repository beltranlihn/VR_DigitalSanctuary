# Cuanto de la IMAGEN cambia en 1, 2 y 5 s (frente, az -60..60) por bandas de elevacion, v1 vs v2, render por pixel.
import numpy as np, vrender as vr
eye = np.array([0.0, 0.0, 120.0])
az, sl, el = vr.cilindrica(-60.0, 60.0, -14.0, 14.0, 12.5)
bandas = {"piso cercano (el < -3)": el < -3.0, "llano (-3..-0,4)": (el >= -3.0) & (el < -0.4), "horizonte y colinas (>= -0,4)": el >= -0.4}
for cual in ("v1", "v2"):
    m = vr.Modelo(cual)
    L = {}
    D = {}
    for t in (0.0, 1.0, 2.0, 5.0, 10.0):
        img, dist, _ = vr.render_cols(m, eye, az, sl, t, rho_min=20.0, J=3000, chunk=64)
        Lm = 255.0 * vr.srgb(img)
        L[t] = 0.2126 * Lm[..., 0] + 0.7152 * Lm[..., 1] + 0.0722 * Lm[..., 2]
        D[t] = np.isfinite(dist)
    print("==", cual)
    for dt in (1.0, 2.0, 5.0, 10.0):
        d = np.abs(L[dt] - L[0.0])
        linea = []
        for nb, b in bandas.items():
            sel = b[:, None] & (D[0.0] | D[dt])
            linea.append("%s: >=1 niv %.1f%%, >=3 niv %.1f%%" % (nb, 100 * (d[sel] >= 1).mean(), 100 * (d[sel] >= 3).mean()))
        print("  dt %2.0f s | " % dt + " | ".join(linea))
