# -*- coding: utf-8 -*-
"""e_capa_viva.py - escenario de la decision abierta 14.3 de la spec: SwellAmp ligado a la respiracion del usuario
(k(t) = 1 + prof * sin(2 pi f t)). Mide la velocidad vertical maxima de la silueta y el sube-y-baja COHERENTE en un
campo de 90 grados, contra el limite de diseno de 0,5 deg/s. h = h_sin_oleaje + k(t) * h_oleaje (el retiro multiplica
a la suma, asi que es lineal en SwellAmp)."""
import math
import numpy as np
from fastvalley import Grid
from h_hlsl import D
AZ = np.arange(0, 360, 0.5)
s = np.geomspace(1500, 64000, 1400)
az = np.radians(AZ)[:, None]
X, Y = s * np.cos(az), s * np.sin(az)
p0 = dict(D); p0["SwellAmp"] = 0.0
p1 = dict(D); p1["HillAmp"] = 0.0; p1["FarAmp"] = 0.0; p1["FarBase"] = 0.0
g0, g1 = Grid(X, Y, p0), Grid(X, Y, p1)
front = np.abs(((AZ + 180) % 360) - 180) <= 45
for f, prof in ((0.0, 0.0), (0.1, 0.5), (0.1, 1.0), (0.2, 0.5), (0.25, 1.0)):
    T = np.arange(0, 40, 0.1)
    E = np.zeros((len(T), len(AZ)))
    for i, t in enumerate(T):
        k = 1.0 + prof * math.sin(2 * math.pi * f * t)
        h = g0.eval(t, grad=False) + k * g1.eval(t, grad=False)
        E[i] = np.degrees(np.arctan(((h - 120) / s).max(1)))
    v = np.abs(np.gradient(E, 0.1, axis=0))
    heave = np.abs(np.gradient(E[:, front].mean(1), 0.1))
    print("f %.2f Hz prof %.1f: |dE/dt| max %.2f deg/s (p99 %.2f), mediana %.3f; sube-y-baja medio del frente max %.3f deg/s" % (
        f, prof, v.max(), np.percentile(v, 99), np.median(v), heave.max()))
