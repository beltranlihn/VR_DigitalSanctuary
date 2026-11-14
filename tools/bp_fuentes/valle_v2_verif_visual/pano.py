# Panorama cilindrica desde los ojos a la resolucion angular del Quest 3 (25 px/grado), v1 y v2, por pixel.
import sys, time, numpy as np
import vrender as vr
ppd = float(sys.argv[1]) if len(sys.argv) > 1 else 25.0
ts = [float(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 else [0.0]
cuales = sys.argv[3].split(",") if len(sys.argv) > 3 else ["v2"]
eye = np.array([0.0, 0.0, 120.0])
az, sl, el = vr.cilindrica(-180.0, 180.0, -12.0, 14.0, ppd)
for cual in cuales:
    m = vr.Modelo(cual)
    for t in ts:
        t0 = time.time()
        img, dist, hh = vr.render_cols(m, eye, az, sl, t, rho_min=20.0, J=4000, chunk=64,
                                       esfera=((380.0, 0.0, 125.0), 110.0))
        tag = "%s_t%d_p%d" % (cual, int(t), int(ppd))
        vr.guardar("pano_%s.png" % tag, img)
        np.save("pano_%s_lin.npy" % tag, img.astype(np.float32))
        np.save("pano_%s_dist.npy" % tag, dist.astype(np.float32))
        print(tag, img.shape, "%.1fs" % (time.time() - t0))
