# -*- coding: utf-8 -*-
"""control_v1.py - CONTROL POSITIVO del instrumento: el modelo numpy (modelo_valle.py) tiene que reproducir
los valores de control de la spec (seccion 12) antes de usarlo para medir nada."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import modelo_valle as mv  # noqa: E402

CAM = np.array([0.0, 0.0, 120.0])
ok = True

print("== altura y gradiente (spec 12)")
H = [((0, 0), 0, 0.000, 0.0, 0.0, 0.0), ((380, 0), 0, 0.000, 0.0, 0.0, 0.0),
     ((900, -700), 0, 89.005, 0.187877, -0.337869, 0.126090),
     ((1500, 800), 0, 280.513, -0.146126, -0.204076, 0.281756),
     ((2200, -1500), 20, 481.552, -0.912999, 0.638918, 0.250821),
     ((3200, 0), 45.5, 460.192, -0.050322, 0.369692, 0.154215),
     ((-1800, 1200), 90, 383.565, -0.033267, 0.083878, 0.007741),
     ((2600, 2600), 300, 0.000, 0.0, 0.0, 0.0)]
for (x, y), t, h0, gx0, gy0, hf0 in H:
    h, hf = mv.h_v1(np.array([x], float), np.array([y], float), t)
    gx, gy = mv.grad_fd(mv.h_v1, np.array([x], float), np.array([y], float), t, mv.P1, d=0.01)
    e = max(abs(h[0] - h0), 100 * abs(gx[0] - gx0), 100 * abs(gy[0] - gy0), 100 * abs(hf[0] - hf0))
    ok &= e < 0.02
    print("  (%6d,%6d) t=%5.1f  h=%9.3f (%9.3f)  g=(%9.6f,%9.6f) (%9.6f,%9.6f)  hf=%.6f  %s" % (
        x, y, t, h[0], h0, gx[0], gy[0], gx0, gy0, hf[0], "OK" if e < 0.02 else "FALLA"))

print("== color del suelo (spec 12, camara (0,0,120), dither 0)")
C = [((380, 0), 0, (0.2136, 0.2636, 0.5562), 0.4743), ((250, -150), 0, (0.2869, 0.3542, 0.6358), 0.0432),
     ((1500, 800), 0, (0.5424, 0.5454, 0.7814), 0.0), ((3200, 0), 45.5, (0.5291, 0.5166, 0.7369), 0.0),
     ((-1800, 1200), 90, (0.4117, 0.4519, 0.7056), 0.0)]
for (x, y), t, c0, O0 in C:
    X, Y = np.array([x], float), np.array([y], float)
    h, hf = mv.h_v1(X, Y, t)
    gx, gy = mv.grad_fd(mv.h_v1, X, Y, t, mv.P1, d=0.01)
    col, _, _, fog, O = mv.ground_color(X, Y, h, gx, gy, hf, CAM, mv.fog_v1, return_parts=True)
    e = float(np.abs(col[0] - np.array(c0)).max())
    ok &= e < 0.0015
    print("  (%6d,%6d) t=%5.1f  col=(%.4f,%.4f,%.4f) ref=(%.4f,%.4f,%.4f)  O=%.4f (%.4f)  %s" % (
        x, y, t, *col[0], *c0, O[0], O0, "OK" if e < 0.0015 else "FALLA"))

print("== color del cielo (spec 12)")
S = [(0, 0, (0.7595, 0.6629, 0.8501)), (0, 45, (0.2160, 0.3280, 0.5970)), (20, 3, (0.7821, 0.6676, 0.8510)),
     (180, 10, (0.5383, 0.5784, 0.8017)), (-40, 7, (0.6269, 0.6178, 0.8274)), (-33, 12, (0.6578, 0.6158, 0.8209)),
     (0, 90, (0.2160, 0.3280, 0.5970))]
for az, el, c0 in S:
    d = mv.dir_d(az, el)
    if el == 90:
        d = np.array([1e-7, 0.0, 1.0])
    col = mv.sky_color(d[None, :])[0]
    e = float(np.abs(col - np.array(c0)).max())
    ok &= e < 0.0015
    print("  az %4d el %3d  col=(%.4f,%.4f,%.4f) ref=(%.4f,%.4f,%.4f)  %s" % (az, el, *col, *c0, "OK" if e < 0.0015 else "FALLA"))

rs = mv.anillos_v1()
print("== malla v1: anillos=%d verts=%d (spec: 79 / 15169)" % (len(rs), 1 + len(rs) * 192))
ok &= len(rs) == 79
print("CONTROL", "OK" if ok else "FALLA")
