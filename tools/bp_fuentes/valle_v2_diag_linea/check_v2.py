# -*- coding: utf-8 -*-
"""check_v2.py - que la propuesta v2 (propuesta.py) no rompa lo que v1 garantizaba:
  - horizonte tapado: elevacion de la silueta desde los ojos (0,0,120) en 360 azimuts, 6 instantes;
  - borde de la malla oculto: elevacion del terreno en R_MAX contra la silueta de delante;
  - piso quieto: h = 0 y dh/dt = 0 a <= 10 m del usuario y del metaball;
  - velocidad vertical maxima por anillo de distancia;
  - continuidad: salto de h'' al cruzar rho = CalmR (debe ser 0) y en v1 (debe ser > 0).
Uso: python check_v2.py
"""
import math
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from propuesta import V1, V2, campo  # noqa: E402

p = V2
eye = np.array([0.0, 0.0, 120.0])
R = p["R_MAX"]
s = np.concatenate([np.arange(50, 3000, 10.0), np.geomspace(3000, R, 1500)])
print("== horizonte y borde (v2) ==")
peor = 90.0
peor_margen = 90.0
for t in (0.0, 30.0, 77.0, 150.0, 300.0, 600.0):
    cf = campo(p, t)
    for k in range(360):
        a = math.radians(k + 0.5)
        x, y = s * math.cos(a), s * math.sin(a)
        h = cf(x, y)[0]
        el = np.degrees(np.arctan2(h - eye[2], s))
        sil = el[:-1].max()
        peor = min(peor, sil)
        peor_margen = min(peor_margen, sil - el[-1])
print("   silueta minima sobre el horizonte: %.2f deg (v1: 4,8)" % peor)
print("   borde de la malla oculto con margen minimo %.2f deg (v1: 6,3)" % peor_margen)

print("== piso quieto (v2) ==")
for c in ((0.0, 0.0), (380.0, 0.0)):
    ang = np.linspace(0, 2 * np.pi, 720)
    rr = np.linspace(0, 1000, 201)
    A, RR = np.meshgrid(ang, rr)
    x, y = c[0] + RR * np.cos(A), c[1] + RR * np.sin(A)
    hm = max(np.abs(campo(p, t)(x, y)[0]).max() for t in (0, 20, 41.5, 77, 300))
    print("   |h| max a <= 10 m de %s: %.3g cm" % (c, hm))

print("== velocidad vertical (v2, 10 min, dt 0,5 s) ==")
rng = np.random.default_rng(1)
ang = rng.uniform(0, 2 * np.pi, 20000)
for a0, a1 in ((0, 1200), (1200, 2500), (2500, 5000), (5000, 10000), (10000, 30000)):
    rr = np.sqrt(rng.uniform(a0 ** 2, a1 ** 2, 20000))
    x, y = p["CalmX"] + rr * np.cos(ang), rr * np.sin(ang)
    vmax = 0.0
    vs = []
    for t in np.arange(0, 600, 7.3):
        v = np.abs(campo(p, t + 0.5)(x, y)[0] - campo(p, t)(x, y)[0]) / 0.5
        vmax = max(vmax, v.max())
        vs.append(np.percentile(v, 99))
    print("   rho %5d-%5d cm: p99 %.1f cm/s, max %.1f cm/s" % (a0, a1, max(vs), vmax))

print("== continuidad en el borde del piso ==")
for nombre, q, r0 in (("v1 (frente, x = ValleyX + ValleyA)", V1, V1["ValleyX"] + V1["ValleyA"]),
                      ("v2 (frente, rho = CalmR)", V2, V2["CalmX"] + V2["CalmR"])):
    cf = campo(q, 0.0)
    for dy in (0.0, 300.0, -300.0):
        xs = r0 + np.array([-4.0, -2.0, 0.0, 2.0, 4.0]) * 5.0
        def hpp(xc):
            e = 1.0
            return (cf(np.array([xc + e]), np.array([dy]))[0] - 2 * cf(np.array([xc]), np.array([dy]))[0]
                    + cf(np.array([xc - e]), np.array([dy]))[0])[0] / e ** 2
        izq, der = hpp(r0 - 3.0), hpp(r0 + 3.0)
        print("   %-38s y=%+5.0f: h'' a -3 cm %.2e, a +3 cm %.2e cm^-1" % (nombre, dy, izq, der))
