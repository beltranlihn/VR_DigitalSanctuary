# -*- coding: utf-8 -*-
"""ajuste_sheen.py - con el lobulo de tope plano, que Sheen/SheenW/SheenP conservan el ASPECTO del piso de la spec
(color sRGB del piso plano a 3-60 m al frente, con niebla P2) y a la vez mantienen la linea en el nivel del piso.
Uso: python ajuste_sheen.py"""
import numpy as np
import transicion as T

azs = list(range(-60, 61, 10)) + [80, 90, 100, 180]
ds = np.array([3, 4, 5, 6, 8, 10, 13, 20, 30, 60.0]) * 100
P = T.P2_LEY_OL
casos = [("spec  Sheen 0,4 (1-NV)^4", dict(T.L0), 0)]
for sh in (0.4, 0.33, 0.28):
    for w, pp in ((0.3, 4.0), (0.35, 3.0), (0.3, 3.0)):
        casos.append(("lob   Sheen %.2f w %.2f p %g" % (sh, w, pp), dict(T.L0, Sheen=sh, SheenW=w, SheenP=pp), 1))
print("piso plano al frente (az 0), sRGB G; distancias %s m" % "/".join("%g" % (d / 100) for d in ds))
for nombre, L, sm in casos:
    x = ds.copy(); y = np.zeros_like(x); h = np.zeros_like(x)
    col = T.suelo(x, y, h, np.zeros_like(x), np.zeros_like(x), np.zeros_like(x), P, L, sm, T.mv.fog_v2)
    g = (T.mv.srgb(col) * 255 + 0.5).astype(int)[:, 1]
    v = T.V(lambda xx, yy, tt: T.h_capas(xx, yy, tt, P, T.s5), P, T.mv.fog_v2, L, sm)
    GB, QB, G, Q = [], [], [], []
    for az in azs:
        rho, hh, el, Y, _ = T.columna(v, az)
        a, b, *_ = T.metrica(rho, el, Y)
        c, d, _ = T.metrica_borde(P, rho, el, Y, az)
        G.append(a); Q.append(b); GB.append(c); QB.append(d)
    print("  %-30s piso G: %s | BORDE G %4.1f/%4.1f Q %4.1f/%4.1f | TRAMO G %4.1f/%4.1f Q %4.1f/%4.1f  (max/med)" % (
        nombre, " ".join("%3d" % k for k in g), max(GB), np.median(GB), max(QB), np.median(QB),
        max(G), np.median(G), max(Q), np.median(Q)))
