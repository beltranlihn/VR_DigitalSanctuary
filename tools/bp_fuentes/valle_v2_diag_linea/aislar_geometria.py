# -*- coding: utf-8 -*-
"""aislar_geometria.py - con el lobulo de tope plano ya puesto (exp(-(N.V/0.3)^4)), cuanto aporta la GEOMETRIA:
C1 contra C2 y la ley de anchos, en la escala grande, con y sin el oleaje de la tarea de movimiento, y en dos
instantes. Uso: python aislar_geometria.py"""
import numpy as np
import transicion as T

azs = list(range(-60, 61, 10)) + [80, 90, 100, 180]
LOB = dict(T.L0, SheenW=0.3, SheenP=4.0)
P_OL = dict(T.P2, **T.OLEAJE)
casos = [
    ("P2 C1 (escala tal cual)", T.P2, T.ss3),
    ("P2 C2", T.P2, T.s5),
    ("P2 ley C2", T.P2_LEY, T.s5),
    ("P2 + oleaje C1", P_OL, T.ss3),
    ("P2 + oleaje C2", P_OL, T.s5),
    ("P2 ley + oleaje C2", T.P2_LEY_OL, T.s5),
]
for sm, L, tag in ((0, T.L0, "SPEC"), (1, LOB, "LOBULO p4 w0,3")):
    print("== sombreado %s" % tag)
    for nombre, P, st in casos:
        for t in (0.0, 41.5):
            v = T.V(lambda x, y, tt, P=P, st=st: T.h_capas(x, y, tt, P, st), P, T.mv.fog_v2, L, sm)
            GB, QB, G, Q = [], [], [], []
            for az in azs:
                rho, h, el, Y, _ = T.columna(v, az, t=t)
                g, q, *_ = T.metrica(rho, el, Y)
                gb, qb, _ = T.metrica_borde(P, rho, el, Y, az)
                GB.append(gb); QB.append(qb); G.append(g); Q.append(q)
            print("  %-22s t=%4.1f  BORDE G max %5.1f med %5.1f  Q max %5.1f med %5.1f || TRAMO G max %5.1f med %5.1f  Q max %5.1f med %5.1f" % (
                nombre, t, max(GB), np.median(GB), max(QB), np.median(QB), max(G), np.median(G), max(Q), np.median(Q)))
