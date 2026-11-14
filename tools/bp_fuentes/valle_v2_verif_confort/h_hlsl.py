# -*- coding: utf-8 -*-
"""h_hlsl.py - transcripcion INDEPENDIENTE (a mano, linea por linea) de ValleyHeightVS.hlsl v2 a numpy.
No importa valley_model.py: sirve para contrastar que el modelo del constructor dice lo mismo que el shader.
Las ramas if del HLSL se escriben como mascaras (fuera de la banda la capa vale 0)."""
import numpy as np

D = dict(HillAmp=2200.0, HillScale=8.0, HillSeed=63.0, HillNear=4500.0, HillFull=12000.0, HillFade=19000.0,
         HillEnd=26000.0, DuneLow=-0.35, DuneHigh=1.2, FarBase=2600.0, FarAmp=5500.0, FarScale=22.0,
         FarSeed=151.0, FarIn=28000.0, FarFull=40000.0, FarCrest=47000.0, FarBack=59000.0, SwellAmp=560.0,
         SwellNear=1500.0, SwellFar=12000.0, SwellScale=2.5, SwellSpeed=1.0, SwellSeed=0.0, MorphAmt=0.15,
         MorphSpeed=1.0)


def frac(x):
    return x - np.floor(x)


def q5(t):
    return t * t * t * (t * (6.0 * t - 15.0) + 10.0)


def sat(x):
    return np.clip(x, 0.0, 1.0)


def h_hlsl(x, y, Tt, p=None, capas=(1, 2, 3)):
    p = D if p is None else p
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    r = np.sqrt(x * x + y * y)
    h = np.zeros_like(r)
    FC = max(p["FarCrest"], p["FarIn"] + 1.0)
    FB = max(p["FarBack"], FC + 1.0)
    MA, MS = p["MorphAmt"], p["MorphSpeed"]
    m0 = 1.00 * (1.0 + MA * np.sin(6.2831853 * frac(MS * Tt / 53.0) + 0.0))
    m1 = 0.75 * (1.0 + MA * np.sin(6.2831853 * frac(MS * Tt / 67.0) + 2.1))
    m2 = 0.55 * (1.0 + MA * np.sin(6.2831853 * frac(MS * Tt / 41.0) + 4.4))
    m3 = 0.35 * (1.0 + MA * np.sin(6.2831853 * frac(MS * Tt / 83.0) + 1.3))

    def sigma(scale, seed):
        s, c = np.sin(np.radians(seed)), np.cos(np.radians(seed))
        k = 6.2831853 / max(scale, 0.05)
        ax0 = k / 3000.0 * (0.95105652 * c - 0.30901699 * s)
        ay0 = k / 3000.0 * (0.95105652 * s + 0.30901699 * c)
        ax1 = k / 2200.0 * (-0.19080900 * c - 0.98162718 * s)
        ay1 = k / 2200.0 * (-0.19080900 * s + 0.98162718 * c)
        ax2 = k / 1650.0 * (-0.79863551 * c - 0.60181502 * s)
        ay2 = k / 1650.0 * (-0.79863551 * s + 0.60181502 * c)
        ax3 = k / 1250.0 * (-0.61566148 * c + 0.78801075 * s)
        ay3 = k / 1250.0 * (-0.61566148 * s - 0.78801075 * c)
        return (m0 * np.sin(ax0 * x + ay0 * y + 0.0) + m1 * np.sin(ax1 * x + ay1 * y + 1.7)
                + m2 * np.sin(ax2 * x + ay2 * y + 4.1) + m3 * np.sin(ax3 * x + ay3 * y + 2.9)) / 2.65

    if 1 in capas:
        msk = (r > p["HillNear"]) & (r < p["HillEnd"])
        sig = sigma(p["HillScale"], p["HillSeed"])
        tf = sat((sig - p["DuneLow"]) / max(p["DuneHigh"] - p["DuneLow"], 0.01))
        ta = sat((r - p["HillNear"]) / max(p["HillFull"] - p["HillNear"], 1.0))
        tb = sat((r - p["HillFade"]) / max(p["HillEnd"] - p["HillFade"], 1.0))
        h = h + np.where(msk, p["HillAmp"] * q5(ta) * (1.0 - q5(tb)) * q5(tf), 0.0)
    if 2 in capas:
        msk = (r > p["FarIn"]) & (r < FB)
        sgF = sigma(p["FarScale"], p["FarSeed"])
        tl = sat((sgF + 0.7) / 1.9)
        tr = sat((r - p["FarIn"]) / (FC - p["FarIn"]))
        te = sat((r - p["FarIn"]) / max(p["FarFull"] - p["FarIn"], 1.0))
        h = h + np.where(msk, p["FarBase"] * q5(tr) + p["FarAmp"] * q5(te) * q5(tl), 0.0)
    if 3 in capas:
        msk = (r > p["SwellNear"]) & (r < FB)
        SF = max(p["SwellFar"], p["SwellNear"] + 1.0)
        tq = sat((r - p["SwellNear"]) / (SF - p["SwellNear"]))
        A = p["SwellAmp"] * q5(tq) * r / SF
        s, c = np.sin(np.radians(p["SwellSeed"])), np.cos(np.radians(p["SwellSeed"]))
        iq = 1.0 / max(p["SwellScale"], 0.05)
        d = [(0.93969262 * c - 0.34202014 * s, 0.93969262 * s + 0.34202014 * c),
             (-0.99619470 * c - 0.08715574 * s, -0.99619470 * s + 0.08715574 * c),
             (-0.25881905 * c + 0.96592583 * s, -0.25881905 * s - 0.96592583 * c),
             (-0.08715574 * c - 0.99619470 * s, -0.08715574 * s + 0.99619470 * c)]
        SS = p["SwellSpeed"]
        o0 = 6.2831853 * frac((d[0][0] * x + d[0][1] * y) * iq / 9000.0 + 0.00 - frac(SS * Tt / 42.0))
        o1 = 6.2831853 * frac((d[1][0] * x + d[1][1] * y) * iq / 7000.0 + 0.37 - frac(SS * Tt / 36.0))
        o2 = 6.2831853 * frac((d[2][0] * x + d[2][1] * y) * iq / 5500.0 + 0.73 - frac(SS * Tt / 31.0))
        o3 = 6.2831853 * frac((d[3][0] * x + d[3][1] * y) * iq / 4000.0 + 0.18 - frac(SS * Tt / 46.0))
        h = h + np.where(msk, A * (1.00 * np.sin(o0) + 0.85 * np.sin(o1) + 0.70 * np.sin(o2)
                                   + 0.40 * np.sin(o3)) / 2.95, 0.0)
    tk = sat((r - FC) / (FB - FC))
    return h * (1.0 - q5(tk))
