# -*- coding: utf-8 -*-
"""Lente de la hebra v3 (con el CUERPO y el lobulo de la bolsa): solo cuentan los puntos de la lente que quedan
FUERA del cuerpo rB; se pide max(sg_bolsa, kappa * sgL) >= necesario. Reporta el kappa minimo."""
import numpy as np
rng = np.random.default_rng(4)
def win_cur(q): return 64.0 * (q * (1.0 - q)) ** 3
def win_broad(q): return np.sin(np.pi * q)
for nombre, win in (("64q3(1-q)3 (actual)", win_cur), ("sin(pi q) (ancha)", win_broad)):
    kap = []
    for _ in range(40000):
        D = rng.uniform(30.0, 110.0)
        Rc = rng.uniform(12.0, 24.0); gC = rng.uniform(0.04, 0.3) * Rc
        m = rng.uniform(3.0, 10.0)
        Rt = rng.uniform(4.0, 30.0) + m
        a = Rc + gC + rng.uniform(3.7, 8.0)
        b = D - rng.uniform(0.35, 0.9) * (Rt - m) - 1.5
        if b <= a + 1.0:
            continue
        bt = a + (b - a) * rng.uniform(0.4, 1.0)
        Ac = rng.uniform(0.0, 0.40)
        sp = rng.uniform(0.2, 2.5) + m
        rB = 0.93 * Rc + gC + m                               # cuerpo con OuterBody = 0 y el valle de la ameba
        P = D + Rt
        z = np.linspace(a, bt, 800)
        q = (z - a) / (bt - a)
        y = Ac * (bt - a) * win(q) + sp
        rho = np.sqrt(z * z + y * y)
        out = rho > rB
        if not out.any():
            continue
        need = np.max(((1.0 - z / rho) / np.log(P / rho))[out])
        sgb = 1.15 * Rt / D
        if need <= sgb:
            continue
        Y = Ac * (b - a) + sp
        zc = 0.5 * (a + b)
        f = Y * Y * P / (2.0 * zc * zc * max(P - zc, 1.0))
        kap.append(need / f)
    kap = np.array(kap)
    print("  %-22s casos donde la bolsa no alcanza: %d  kappa min necesario: max=%.3f p99=%.3f" % (
        nombre, len(kap), kap.max() if len(kap) else 0, np.percentile(kap, 99) if len(kap) else 0))
