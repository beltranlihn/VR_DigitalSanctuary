# -*- coding: utf-8 -*-
"""Estudio de las constantes del lobulo gaussiano angular de la envoltura exterior.

Lobulo: e(th) = P * exp((cos th - 1) / sg), con P = D + Rt (centroide a D del centro, esfera acotante Rt).
1) Esfera: minimo c tal que sg = c * Rt / D contiene la esfera (centro a D, radio Rt) para x = Rt/D en (0, 0.95).
2) Lente (hebra con curl): puntos (z, y) con y = Y * w((z - a)/(b - a)), z en [a, b]. Minimo sg exacto =
   sup_z (1 - cos th) / ln(P / rho). Se compara con la formula sin log  sgL = Y^2 P / (2 zc^2 (P - zc)).
"""
import numpy as np

# ---- 1) esfera ------------------------------------------------------------------------------
print("== esfera: c minimo (sg = c*x) ==")
worst = 0.0
for x in np.linspace(0.01, 0.95, 400):
    th_max = np.arcsin(min(x, 0.999999))
    th = np.linspace(0.0, th_max, 4000)[1:]
    rhs = np.cos(th) + np.sqrt(np.maximum(x * x - np.sin(th) ** 2, 0.0))   # salida del rayo (D = 1)
    P = 1.0 + x
    # e >= rhs  <=>  sg >= (1 - cos th) / ln(P / rhs)
    sg_need = np.max((1.0 - np.cos(th)) / np.log(P / rhs))
    c = sg_need / x
    worst = max(worst, c)
    if abs(x - round(x, 1)) < 0.0012:
        print("  x=%.2f  c_min=%.4f" % (x, c))
print("  c_min sup = %.4f" % worst)

# ---- 2) lente ------------------------------------------------------------------------------
print("\n== lente: sg exacto / formula sin log ==")
rng = np.random.default_rng(3)
def win_cur(q):
    return 64.0 * (q * (1.0 - q)) ** 3
def win_broad(q):
    return np.sin(np.pi * q)          # ventana MUCHO mas ancha (por si StrandCurl la cambia)
for nombre, win in (("64q3(1-q)3 (actual)", win_cur), ("sin(pi q) (ancha)", win_broad)):
    ratios = []
    for _ in range(20000):
        D = rng.uniform(30.0, 100.0)
        Rc = rng.uniform(12.0, 24.0)
        Rt = rng.uniform(6.0, 35.0)
        a = Rc + rng.uniform(3.0, 10.0)                 # zW0 >= Rc + ~3,7
        b = D - rng.uniform(0.6, 1.0) * Rt              # zW1 = D - (alcance + filetes) ~ D - Rt
        if b <= a + 2.0:
            continue
        Lw = D - Rc                                      # cota usada en el shader (Lw real <= esto)
        Y = rng.uniform(0.0, 0.45) * Lw + rng.uniform(1.0, 10.0)
        P = D + Rt
        z = np.linspace(a, b, 600)
        q = (z - a) / (b - a)
        y = Y * win(q)
        rho = np.sqrt(z * z + y * y)
        cth = z / rho
        need = np.max((1.0 - cth) / np.log(P / rho))
        zc = max(0.5 * (Rc + D - Rt), 1.0)
        f = Y * Y * P / (2.0 * zc * zc * (P - zc))
        ratios.append(need / f)
    ratios = np.array(ratios)
    print("  %-22s n=%d  ratio max=%.3f  p99=%.3f  mediana=%.3f" % (nombre, len(ratios), ratios.max(),
          np.percentile(ratios, 99), np.median(ratios)))
