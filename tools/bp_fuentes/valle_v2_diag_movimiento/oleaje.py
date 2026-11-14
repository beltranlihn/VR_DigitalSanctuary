# -*- coding: utf-8 -*-
"""oleaje.py - PROPUESTA (c): oleaje viajero lento que se SUMA a la altura estatica del valle.

    h_total(p, t) = h_colinas(p)  +  h_ola(p, t)

h_ola (cm, s; p = (x, y) local; r = |p|):
    Wq   = smoothstep(SwellNear, SwellFar, r)              # 0 en la zona quieta, 1 lejos
    Bk   = 1 - u2(e)                                        # la MISMA envolvente trasera del anillo: 0 detras de la cresta
    A    = SwellAmp * Wq * Bk
    g_j  = K_j * (d_j . p) + phi_j - 2*pi*frac(SwellSpeed * t / T_j)      j = 0..3, escritas una por una
           K_j = 2*pi / (lambda_j * SwellScale),  d_j = (cos(alpha_j + SwellSeed), sin(alpha_j + SwellSeed))
    s    = (w0 sin g0 + w1 sin g1 + w2 sin g2 + w3 sin g3) / (w0 + w1 + w2 + w3)     # |s| <= 1
    h_ola = A * s
Gradiente exacto:
    grad h_ola = A * sum_j w_j K_j cos(g_j) d_j / SW
               + s * SwellAmp * Bk * S'(SwellNear, SwellFar, r) * p / r
               - s * SwellAmp * Wq * S'(E1, E2, e) * grad e
Velocidad vertical:  dh/dt = -A * sum_j w_j (2 pi SwellSpeed / T_j) cos(g_j) / SW
Cada componente viaja en +d_j a c_j = lambda_j * SwellScale * SwellSpeed / T_j.
"""
import math

import numpy as np

import modelo_v1 as M

# ---- las 4 olas (constantes del codigo, como las dunas). Elegidas para:
#  - periodos 31-46 s en cada punto (0,022-0,032 Hz): 6-18 veces por debajo del pico de mareo visual 0,2-0,4 Hz
#  - longitudes 40-90 m: lomas de ola del tamano de las colinas nuevas
#  - direcciones repartidas y SUMA vectorial de (w_j * c_j * d_j) ~ 0: el oleaje no tiene deriva neta
#    (no simula que el usuario se traslade) y, por ser ondas planas, tampoco giro neto alrededor de el.
OLAS = (  # (alpha deg, lambda cm, T s, peso w, fase rad)
    (20.0, 9000.0, 42.0, 1.00, 0.0),
    (175.0, 7000.0, 36.0, 0.85, 2.3),
    (255.0, 5500.0, 31.0, 0.70, 4.6),
    (95.0, 4000.0, 46.0, 0.40, 1.1),
)
SW = sum(o[3] for o in OLAS)

Q = dict(SwellAmp=600.0, SwellNear=1500.0, SwellFar=15000.0, SwellScale=1.0, SwellSpeed=1.0, SwellSeed=0.0)


def deriva_neta(q=None):
    q = dict(Q, **(q or {}))
    v = np.zeros(2)
    tot = 0.0
    for al, lam, T, w, _ in OLAS:
        c = lam * q["SwellScale"] * q["SwellSpeed"] / T
        a = math.radians(al + q["SwellSeed"])
        v += w * c * np.array([math.cos(a), math.sin(a)])
        tot += w * c
    return v, tot


def ola(x, y, t, base_q, q=None, con_grad=False):
    """devuelve h_ola, y si con_grad: (h, dhdx, dhdy, dhdt). base_q = parametros del valle (para e y u2)."""
    q = dict(Q, **(q or {}))
    b = dict(M.P, **(base_q or {}))
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    r = np.sqrt(x * x + y * y)
    rs = np.maximum(r, 1.0)
    VA, VB = max(b["ValleyA"], 1.0), max(b["ValleyB"], 1.0)
    ex = (x - b["ValleyX"]) / VA
    ey = y / VB
    e = np.sqrt(ex * ex + ey * ey)
    es = np.maximum(e, 1e-4)
    E1 = max(b["RimCrest"], 1.01)
    E2 = max(b["RimBack"], E1 + 0.01)
    t2 = np.clip((e - E1) / (E2 - E1), 0, 1)
    u2 = t2 * t2 * (3 - 2 * t2)
    du2 = 6 * t2 * (1 - t2) / (E2 - E1)
    Bk = 1.0 - u2
    SF = max(q["SwellFar"], q["SwellNear"] + 1.0)
    tq = np.clip((r - q["SwellNear"]) / (SF - q["SwellNear"]), 0, 1)
    Wq = tq * tq * (3 - 2 * tq)
    dWq = 6 * tq * (1 - tq) / (SF - q["SwellNear"])
    A = q["SwellAmp"] * Wq * Bk
    s = np.zeros_like(x)
    cx = np.zeros_like(x)
    cy = np.zeros_like(x)
    ct = np.zeros_like(x)
    for al, lam, T, w, ph in OLAS:
        K = 2 * math.pi / (lam * max(q["SwellScale"], 0.05))
        a = math.radians(al + q["SwellSeed"])
        dx, dy = math.cos(a), math.sin(a)
        tau = (q["SwellSpeed"] * t / T) % 1.0                     # frac(): el reloj reducido ANTES del sin
        g = K * (dx * x + dy * y) + ph - 2 * math.pi * tau
        sg, cg = np.sin(g), np.cos(g)
        s += w * sg
        cx += w * K * cg * dx
        cy += w * K * cg * dy
        ct += w * (2 * math.pi * q["SwellSpeed"] / T) * cg
    s /= SW
    h = A * s
    if not con_grad:
        return h
    dex = ex / (VA * es)
    dey = ey / (VB * es)
    gx = A * cx / SW + s * q["SwellAmp"] * (Bk * dWq * x / rs - Wq * du2 * dex)
    gy = A * cy / SW + s * q["SwellAmp"] * (Bk * dWq * y / rs - Wq * du2 * dey)
    dhdt = -A * ct / SW
    return h, gx, gy, dhdt


# ---- base de prueba de la NUEVA escala: el valle v1 agrandado K = 5 veces (misma composicion angular,
#      colinas a 30-200 m, crestas de 19-40 m). Es un SUSTITUTO: la geometria v2 real la define otra tarea.
#      MorphAmt 0 para aislar el oleaje (todo lo que se mueve en las mediciones es la ola).
K = 5.0
BASE_Q = dict(ValleyX=350.0 * K, ValleyA=950.0 * K, ValleyB=600.0 * K, RimHeight=380.0 * K, DuneAmp=520.0 * K,
              DuneScale=1.0 * K, MorphAmt=0.0, MorphNear=800.0 * K, MorphFar=3000.0 * K)
