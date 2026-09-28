# -*- coding: utf-8 -*-
"""Port LITERAL (linea a linea) del HLSL propuesto para CoreWob / AmPod / AmBody / CentreR.
Si se toca una constante en el HLSL, se toca aca y se vuelve a correr verify_amoeba.py.
Vectorizado en numpy (float64); u: (N,3) unitarios; LV1, LV3: (N,4); T: (N,)."""
import numpy as np

# ---- constantes del HLSL (copiadas tal cual) ----
A0, AGK, CALM_LO = 0.75, 0.4, 0.5
AMAX = 0.85           # tope de la amplitud (V4b): min(A, 0,85)
WN   = 1.2074          # floor(1/WMAX certificado, 4 dec) -> maximo normalizado <= 0.99994 (bounds_bnb.py)
WMIN = -0.4374         # floor(WN * WMIN certificado, 4 dec) -> cota segura (certificado -0.43732)
ROT  = 0.0503
OM   = (0.1713, 0.2291, 0.1307)
PH   = (0.4, 2.1, 4.3)
D0 = np.array([0.5412, 0.4388, 0.7174]);  D3 = np.array([-0.1572, 0.6399, 0.7522])
D1 = np.array([0.6578, 0.5251, -0.5400]); D2 = np.array([-0.5148, 0.8567, 0.0322])
D4 = np.array([-0.1029, -0.7544, -0.6483]); D5 = np.array([-0.2722, -0.1838, -0.9445])
MU_POD, MU_BODY = 0.015151515, 0.14285714


def saturate(x):
    return np.clip(x, 0.0, 1.0)


def SS(a, b, x):
    t = saturate((x - a) / (b - a))
    return t * t * (3.0 - 2.0 * t)


def Calm(LV1):
    return SS(0.5, 0.9, saturate(LV1[:, 0])) * (1.0 - 0.7 * saturate(LV1[:, 2]))


def CoreWob(LV1, LV3):
    A = np.minimum(A0 * np.maximum(LV3[:, 2], 0.0) * (1.0 + AGK * saturate(LV1[:, 2])) * (1.0 + (CALM_LO - 1.0) * Calm(LV1)), AMAX)
    return np.stack([A, np.full_like(A, WMIN), np.zeros_like(A), np.zeros_like(A)], -1)


def AmPod(u, D, h, g):
    q = 0.5 + 0.5 * (u @ D)
    q2 = q * q; q4 = q2 * q2; q5 = q4 * q
    g += (h * (10.0 * q5 * q4 - 2.5 * q4))[:, None] * D
    return h * (2.0 * q5 * q5 - q5 - MU_POD)


def AmBody(u, D, h, g):
    q = 0.5 + 0.5 * (u @ D)
    q2 = q * q; q3 = q2 * q
    g += (h * 3.0 * q3 * q2)[:, None] * D
    return h * (q3 * q3 - MU_BODY)


def raw_field(u, T):
    """w crudo (sin normalizar) y su gradiente en R3, EXACTAMENTE como CentreR (para las cotas)."""
    cr = np.cos(ROT * T); sr = np.sin(ROT * T)
    v = np.stack([cr * u[:, 0] + sr * u[:, 1], cr * u[:, 1] - sr * u[:, 0], u[:, 2]], -1)
    s0 = 0.45 * np.sin(OM[0] * T + PH[0])
    s1 = 0.45 * np.sin(OM[1] * T + PH[1])
    s2 = 0.45 * np.sin(OM[2] * T + PH[2])
    gv = np.zeros_like(u)
    w  = AmPod(v, D0, (0.55 + s0), gv)
    w += AmPod(v, D3, 0.80 * (0.55 - s0), gv)
    w += AmPod(v, D1, 0.90 * (0.55 + s1), gv)
    w += AmPod(v, D2, 0.85 * (0.55 - s1), gv)
    w += AmBody(v, D4, 0.60 * (0.55 + s2), gv)
    w += AmBody(v, D5, 0.60 * (0.55 - s2), gv)
    gw = np.stack([cr * gv[:, 0] - sr * gv[:, 1], cr * gv[:, 1] + sr * gv[:, 0], gv[:, 2]], -1)
    return w, gw


def CentreR(u, Rc, LV1, LV3, T):
    Wob = CoreWob(LV1, LV3)
    w, gw = raw_field(u, T)
    k = Rc * Wob[:, 0] * WN
    g = k[:, None] * gw
    gT = g - u * np.sum(u * g, -1, keepdims=True)
    return Rc + k * w, gT


# ---- la VIEJA (para comparar) ----
def CentreR_old(u, Rc, LV1, LV3, T):
    A = 0.05 * LV3[:, 2] * (1.0 + 0.4 * saturate(LV1[:, 2])) * (1.0 - 0.4 * Calm(LV1))
    F1 = np.array([0.577, 0.331, 0.747]); F2 = np.array([-0.431, 0.794, 0.428])
    f = 2.2
    a1 = (u @ F1) * f + T * 0.35
    a2 = (u @ F2) * f * 1.37 - T * 0.27
    a3 = a1 * 1.9 + a2 * 0.7 + 1.3
    w = np.sin(a1) * np.sin(a2) + 0.35 * np.sin(a3)
    gw = ((np.cos(a1) * np.sin(a2) + 0.665 * np.cos(a3)) * f)[:, None] * F1 \
       + ((np.sin(a1) * np.cos(a2) + 0.245 * np.cos(a3)) * f * 1.37)[:, None] * F2
    r = Rc * (1.0 + A * w)
    g = (Rc * A)[:, None] * gw
    gT = g - u * np.sum(u * g, -1, keepdims=True)
    return r, gT


# ---- descomposicion por lobulo (para las cotas): (direccion, H, signo en el par, par, tipo) ----
LOBES = [(D0, 1.00, +1, 0, 'P'), (D3, 0.80, -1, 0, 'P'), (D1, 0.90, +1, 1, 'P'), (D2, 0.85, -1, 1, 'P'),
         (D4, 0.60, +1, 2, 'B'), (D5, 0.60, -1, 2, 'B')]
SAMP = 0.45     # s_j = 0.45 sin(...) in [-0.45, 0.45]


def phi_c(kind, q):
    """phi - media (el valor que multiplica la altura)"""
    if kind == 'P':
        q5 = q ** 5
        return 2.0 * q5 * q5 - q5 - MU_POD
    q3 = q ** 3
    return q3 * q3 - MU_BODY


def dphi_dq(kind, q):
    return (20.0 * q ** 9 - 5.0 * q ** 4) if kind == 'P' else 6.0 * q ** 5


def cvals(v):
    return np.stack([phi_c(kind, 0.5 + 0.5 * (v @ D)) for D, Hk, sg, j, kind in LOBES], -1)


def box(v):
    """max y min EXACTOS del campo crudo sobre TODAS las alturas alcanzables, para cada v (marco de
    los lobulos; la rotacion es rigida y no cambia el conjunto de valores). Cada par es LINEAL en
    s in [-0.45, 0.45] -> el extremo esta en s = +-0.45."""
    c = cvals(v); hi = 0.0; lo = 0.0
    for j in range(3):
        vals = []
        for s in (SAMP, -SAMP):
            tot = 0.0
            for k, (D, Hk, sg, jj, kind) in enumerate(LOBES):
                if jj == j:
                    tot = tot + Hk * (0.55 + sg * s) * c[..., k]
            vals.append(tot)
        hi = hi + np.maximum(vals[0], vals[1]); lo = lo + np.minimum(vals[0], vals[1])
    return hi, lo


def lipschitz():
    """Cota RIGUROSA del gradiente esferico de cualquier rama: sum_k H_k * max_theta |dphi/dtheta|,
    con |dphi/dtheta| = |dphi/dq| * 0.5 sin(theta) (phi es zonal alrededor de D). La altura
    relativa maxima es 0.55 + 0.45 = 1."""
    th = np.linspace(0.0, np.pi, 4_000_001)
    q = 0.5 + 0.5 * np.cos(th)
    L = 0.0
    for D, Hk, sg, j, kind in LOBES:
        L += Hk * np.max(np.abs(dphi_dq(kind, q)) * 0.5 * np.sin(th))
    return L * 1.001     # margen por la discretizacion 1D (la funcion es suave; paso 8e-7 rad)
