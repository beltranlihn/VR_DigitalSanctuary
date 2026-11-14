# -*- coding: utf-8 -*-
"""barrido_lobulo.py - forma del lobulo del brillo rasante: Fresnel de la spec (1 - N.V)^4 contra un lobulo de TOPE
PLANO exp(-(N.V/w)^p). Mide (a) la linea (G/Q en el borde y en el tramo) en la escala grande con la ley de
transicion + oleaje, y en v1; (b) cuanto cambia el aspecto del piso plano (luminancia a 2..60 m) y el de las
cimas (rasante a N.V = 0, igual por construccion). Uso: python barrido_lobulo.py"""
import math
import numpy as np
import transicion as T

azs = list(range(-60, 61, 10)) + [80, 90, 100, 180]
lob = [("spec (1-NV)^4", None)] + [("exp -(NV/%.2f)^%d" % (w, pp), (w, pp)) for pp in (2, 4) for w in (0.2, 0.25, 0.3, 0.35)]
geos = {"escala+ley+oleaje": (T.P2_LEY_OL, lambda x, y, t: T.h_capas(x, y, t, T.P2_LEY_OL, T.s5), T.mv.fog_v2),
        "v1 spec": (T.P1, lambda x, y, t: T.mv.h_v1(x, y, t, T.P1), T.mv.fog_v1)}
print("Piso PLANO (sin fog, sin sombra): luminancia Y a d metros, relativa al Fresnel de la spec")
ds = np.array([2, 3, 5, 8, 10, 13, 20, 40, 60.0]) * 100
nv = 120.0 / np.hypot(ds, 120.0)
L = T.L0
for nombre, par in lob:
    fres = (1 - nv) ** 4 if par is None else np.exp(-(nv / par[0]) ** par[1])
    fr0 = (1 - nv) ** 4
    print("  %-16s fres a %s m: %s   (spec: %s)" % (nombre, "/".join("%g" % (d / 100) for d in ds),
          " ".join("%.2f" % f for f in fres), " ".join("%.2f" % f for f in fr0)))
for gname, (P, hfun, fog) in geos.items():
    print("== %s" % gname)
    for nombre, par in lob:
        if par is None:
            v = T.V(hfun, P, fog, T.L0, 0)
        else:
            v = T.V(hfun, P, fog, dict(T.L0, SheenW=par[0], SheenP=par[1]), 1)
        GB, QB, G, Q = [], [], [], []
        for az in azs:
            rho, h, el, Y, _ = T.columna(v, az)
            g, q, *_ = T.metrica(rho, el, Y)
            gb, qb, _ = T.metrica_borde(P, rho, el, Y, az)
            GB.append(gb); QB.append(qb); G.append(g); Q.append(q)
        print("  %-16s BORDE G max %5.1f med %5.1f  Q max %5.1f med %5.1f || TRAMO G max %5.1f med %5.1f  Q max %5.1f med %5.1f" % (
            nombre, max(GB), np.median(GB), max(QB), np.median(QB), max(G), np.median(G), max(Q), np.median(Q)))
