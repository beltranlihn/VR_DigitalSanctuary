# Calibracion del instrumento: render por pixel del v1 contra la captura REAL de Unreal (vista lateral, pitch 0).
import time, numpy as np
from PIL import Image
import vrender as vr
W, H = 1052, 862
az, sl, f = vr.camara(W, H, 90.0, 90.0, 0.0)
for cual in ("v1", "v2"):
    for z0 in (0.0, -90.4):
        m = vr.Modelo(cual)
        eye = np.array([380.0, -700.0, 70.0 - z0])
        t0 = time.time()
        img, dist, hh = vr.render_cols(m, eye, az, sl, 0.0, J=5000)
        tag = "%s_z%d" % (cual, int(round(z0)))
        vr.guardar("r_lado_%s.png" % tag, img)
        np.save("r_lado_%s_Y.npy" % tag, vr.Y(img))
        np.save("r_lado_%s_dist.npy" % tag, dist)
        print(tag, "%.1fs" % (time.time() - t0), "cielo %.1f%%" % (100 * np.isinf(dist).mean()))
