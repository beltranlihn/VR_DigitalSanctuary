# -*- coding: utf-8 -*-
"""lvport.py - port a numpy de LovingLib.ush (lo necesario para verificar la envoltura exterior).

V4 INTEGRADO (2026-09-28): ameba del nucleo con pseudopodos (CoreWob/AmPod/AmBody/CentreR), ArmSetup
con Rcm = Rc(1 + A WMIN) + 0,3 gC y el ancla del ensanche en la ameba REAL (AP5.x = CentreR(eje) + gC +
0,8 MoundH), StrandCurl v4 (una comba, ventana sin^2), particulas de la hebra que se deslizan por el eje
(manga 0,35 off, deriva x0,15) y OuterEnv con Win.x = zW0 MINIMO (Rc(1 + A WMIN) + ...).
REVISION ADVERSARIAL (2026-09-28, mismo dia): GroupScale por secuencia de razon de plata (no Hash: el indice
literal de LovingOuterVS se pliega en el host y difiere del GPU), ancla del ensanche INCLINADA con la membrana
(AP2.xyz = gAx rEnd/rAx, AP5.x baja rEnd^2/rAx; aca AP['tilt']), ArmWindow arranca despues de |tilt|,
Win.x con el descuento rEm^2/rAm, suavidad p = lerp(8, 3, OuterSoftness) y tempo del curl 0,6 swr.

Espejo LITERAL de las funciones HLSL (mismos nombres, mismas constantes). Vectorizado sobre el primer eje
cuando tiene sentido (direcciones u, anillos del brazo). Los vectores LV se pasan como np.array de 4.
Tambien trae el espejo de las funciones de la envoltura exterior (CurlEnv, OuterEnv, OuterLobe, OuterWob) y de
los wrappers LovingOuterVS: `outer_r(u, ...)` devuelve radio, normal, y los terminos por separado.
"""
import numpy as np

TAU = 6.2831853


def sat(x):
    return np.clip(x, 0.0, 1.0)


def SS(a, b, x):
    t = sat((x - a) / (b - a))
    return t * t * (3.0 - 2.0 * t)


def frac(x):
    return x - np.floor(x)


def Hash(n):
    return frac(np.sin(n * 12.9898 + 4.1414) * 43758.5453)


def lerp(a, b, t):
    return a + (b - a) * t


def step(a, x):          # HLSL step(a, x) = x >= a
    return (np.asarray(x) >= a).astype(float)


def nrm(v):
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-12)


def SminS(d, ds, k, w):
    kk = max(k, 0.01) if np.isscalar(k) else np.maximum(k, 0.01)
    h = sat(0.5 + 0.5 * (d - ds) / kk) * w
    return lerp(d, ds, h) - kk * h * (1.0 - h)


# ------------------------------------------------------------------------------------------------
def Shape(LV0, LV1, LV2, LV3):
    S = sat(LV1[0]); ph = LV1[1]
    wIn, wStr, wCon, wFuse = SS(0, 0.3, S), SS(0.3, 0.6, S), SS(0.6, 0.8, S), SS(0.8, 1.0, S)
    GSz = max(LV2[0], 0.05); CA = LV2[2]; CS = max(LV2[3], 0.0); MT = max(LV3[0], 0.0)
    d = {}
    d['Rc'] = LV0[3] * (1.0 + 0.12 * (0.4 * wCon + 0.6 * wFuse) * CA) * (1.0 + 0.025 * np.sin(ph))
    rb = 3.4 * GSz * (1.0 + 0.02 * np.sin(ph - 0.8))
    gap = rb * (0.3 + MT * (0.12 + 0.15 * wStr + 0.2 * wFuse)) * (1.0 + 0.15 * np.sin(ph - 1.1))
    Renv = 1.6 * rb + gap
    d.update(rb=rb, gap=gap, Renv=Renv)
    d['rMid'] = CS * (0.3 + 0.3 * S)
    d['rEnd'] = Renv * lerp(0.3, 0.42, S)
    d['lam'] = lerp(1.5, 2.8, S)
    d['kC'] = lerp(1.2, 2.2, SS(0.3, 1.0, S))
    d['kN'] = Renv * lerp(0.28, 0.36, S)
    d['kE'] = 0.9 * rb
    d['Ratt'] = 0.25 * Renv * wStr * (1.0 - 0.5 * wFuse)
    d['MoundH'] = CA * 0.08 * d['Rc'] * wStr
    d['kBall'] = 0.3 * rb * (1.0 + 0.5 * wFuse)
    d['WobA'] = 0.75 * LV3[2]
    return d


def GroupScale(idx, LV5):
    """V4 revisado: secuencia de razon de plata (robusta al redondeo), NO Hash (caotico: el indice literal de
    LovingOuterVS se pliega en el host y difiere del GI.w evaluado en el GPU)."""
    return 1.0 + max(LV5[0], 0.0) * (1.2 * frac(0.41421356 * idx + 0.33) - 0.4)


def Calm(LV1):
    return SS(0.5, 0.9, sat(LV1[0])) * (1.0 - 0.7 * sat(LV1[2]))


def CoreWob(LV1, LV3):
    return np.array([min(0.75 * max(LV3[2], 0.0) * (1.0 + 0.4 * sat(LV1[2])) * lerp(1.0, 0.5, Calm(LV1)), 0.85), -0.4374, 0.0, 0.0])


def NeckBreath(LV1, idx):
    c = Calm(LV1)
    return 1.0 + (0.08 + 0.04 * c) * np.sin(LV1[1] - 0.4 - TAU * Hash(idx + 0.19) * (1.0 - c))


def CentreGap(LV1, LV3, Rc):
    S = sat(LV1[0])
    return Rc * (0.12 + 0.06 * S) * max(LV3[0], 0.3) * (1.0 + 0.15 * np.sin(LV1[1] - 1.1))


def BallsLayout(idx, rb, toC, wStr, CA, T, OM, LV1):
    Coh = Calm(LV1); Ag = sat(LV1[2])
    Rr = OM * (1.0 - 0.6 * Coh) * (1.0 + 0.5 * Ag)
    a1 = Hash(idx + 0.31) * TAU + 0.35 * Rr * np.sin(0.11 * T + TAU * Hash(idx + 0.47))
    cz = Hash(idx + 0.77) * 2.0 - 1.0
    sz = np.sqrt(sat(1.0 - cz * cz))
    nr = np.array([sz * np.cos(a1), sz * np.sin(a1), cz])
    hlp = np.array([0.0, 0.0, 1.0]) if abs(nr[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    tA0 = nrm(np.cross(nr, hlp)); tB0 = np.cross(nr, tA0)
    phi = Rr * (0.8 * np.sin(0.19 * T + TAU * Hash(idx + 0.13)) + 0.5 * np.sin(0.33 * T + TAU * Hash(idx + 0.29)))
    cp, sp = np.cos(phi), np.sin(phi)
    tA = cp * tA0 + sp * tB0
    tB = cp * tB0 - sp * tA0
    three = float(Hash(idx + 0.53) >= 0.3)
    dd = rb * lerp(0.75, 0.8, three)
    d0 = tA
    d1 = lerp(-tA, -0.5 * tA + 0.866 * tB, three)
    d2 = -0.5 * tA - 0.866 * tB
    Ab = 0.16 * OM * (1.0 - 0.35 * Coh) * (1.0 + 0.3 * Ag)
    r0 = rb * (1.0 + 0.24 * (Hash(idx + 0.11) - 0.5))
    r1 = rb * (1.0 + 0.24 * (Hash(idx + 0.23) - 0.5))
    r2 = rb * (1.0 + 0.24 * (Hash(idx + 0.41) - 0.5)) * three
    ph = LV1[1]
    r0 *= 1.0 + Ab * ((1.0 - Coh) * np.sin(T * (0.62 + 0.3 * Hash(idx + 0.61)) + TAU * Hash(idx + 0.71)) + Coh * np.sin(ph - 0.8))
    r1 *= 1.0 + Ab * ((1.0 - Coh) * np.sin(T * (0.55 + 0.3 * Hash(idx + 0.63)) + TAU * Hash(idx + 0.83)) + Coh * np.sin(ph - 2.1))
    r2 *= 1.0 + Ab * ((1.0 - Coh) * np.sin(T * (0.69 + 0.3 * Hash(idx + 0.67)) + TAU * Hash(idx + 0.97)) + Coh * np.sin(ph - 3.4))
    w = 0.08 * rb * OM
    att = toC * (0.25 * CA * wStr * rb)
    o0 = d0 * dd + att + w * np.array([np.sin(T * 0.53 + idx * 1.7), np.sin(T * 0.41 + idx * 2.3), np.sin(T * 0.37 + idx * 3.1)])
    o1 = d1 * dd + att + w * np.array([np.sin(T * 0.47 + idx * 2.9), np.sin(T * 0.59 + idx * 1.3), np.sin(T * 0.43 + idx * 3.7)])
    o2 = d2 * dd + att + w * np.array([np.sin(T * 0.39 + idx * 3.3), np.sin(T * 0.51 + idx * 2.1), np.sin(T * 0.61 + idx * 1.1)])
    o0 = o0 * min(1.0, 0.85 * r0 / max(np.linalg.norm(o0), 1e-4))
    o1 = o1 * min(1.0, 0.85 * r1 / max(np.linalg.norm(o1), 1e-4))
    o2 = o2 * min(1.0, 0.85 * max(r2, 1e-3) / max(np.linalg.norm(o2), 1e-4))
    return [np.append(o0, r0), np.append(o1, r1), np.append(o2, r2)]


def ArmSetup(G, idx, LV0, LV1, LV2, LV3, LV4, LV5, T):
    LV2g = np.array([LV2[0] * GroupScale(idx, LV5), LV2[1], LV2[2], LV2[3]])
    sh = Shape(LV0, LV1, LV2g, LV3)
    S = sat(LV1[0]); C = LV0[:3]
    toC = nrm(C - G + np.array([1e-4, 0, 0]))
    B = BallsLayout(idx, sh['rb'], toC, SS(0.3, 0.6, S), LV2[2], T, LV3[3], LV1)
    Rc = sh['Rc']
    gC = CentreGap(LV1, LV3, Rc)
    Wob = CoreWob(LV1, LV3)
    Rcm = Rc * (1.0 + Wob[0] * Wob[1]) + 0.3 * gC
    rm = sh['rMid'] * NeckBreath(LV1, idx)
    rAx, gAx = CentreR((-toC)[None, :], Rc, LV1, LV3, T)    # ancla del ensanche en la ameba REAL (V4)
    rAx = float(rAx[0]); gAx = gAx[0]
    iAx = sh['rEnd'] / max(rAx, 1.0)                        # ancla INCLINADA (revision 2026-09-28)
    AP = dict(Pc=C, Rcm=Rcm, G=G, gap=sh['gap'], Uref=LV4[:3], hug=LV4[3], tilt=gAx * iAx,
              AP3=np.array([rm, sh['rEnd'], sh['lam'], sh['kN']]),
              AP4=np.array([sh['kC'], sh['kE'], sh['Ratt'], 0.5 * sh['Renv']]),
              AP5=np.array([rAx - sh['rEnd'] * max(iAx, 2.7 * Wob[0] * sh['rEnd'] / Rc) + gC + 0.8 * sh['MoundH'], sh['lam'], lerp(0.35, 0.22, S), 0.62]),
              AP6=np.array([Rc + gC, sh['MoundH'], 0.55, Rc]), sh=sh)
    return AP, B


def AmPod(u, D, h, g):
    q = 0.5 + 0.5 * (u @ D)
    q2 = q * q; q4 = q2 * q2; q5 = q4 * q
    g += (h * (10.0 * q5 * q4 - 2.5 * q4))[:, None] * D
    return h * (2.0 * q5 * q5 - q5 - 0.015151515)


def AmBody(u, D, h, g):
    q = 0.5 + 0.5 * (u @ D)
    q2 = q * q; q3 = q2 * q
    g += (h * 3.0 * q3 * q2)[:, None] * D
    return h * (q3 * q3 - 0.14285714)


def CentreR(u, Rc, LV1, LV3, T):
    """espejo literal de LVLib::CentreR V4 (u: (n,3) unitarios) -> r, gT"""
    Wob = CoreWob(LV1, LV3)
    cr, sr = np.cos(0.0503 * T), np.sin(0.0503 * T)
    v = np.stack([cr * u[:, 0] + sr * u[:, 1], cr * u[:, 1] - sr * u[:, 0], u[:, 2]], 1)
    s0 = 0.45 * np.sin(0.1713 * T + 0.4)
    s1 = 0.45 * np.sin(0.2291 * T + 2.1)
    s2 = 0.45 * np.sin(0.1307 * T + 4.3)
    gv = np.zeros_like(u)
    w = AmPod(v, np.array([0.5412, 0.4388, 0.7174]), (0.55 + s0), gv)
    w = w + AmPod(v, np.array([-0.1572, 0.6399, 0.7522]), 0.80 * (0.55 - s0), gv)
    w = w + AmPod(v, np.array([0.6578, 0.5251, -0.5400]), 0.90 * (0.55 + s1), gv)
    w = w + AmPod(v, np.array([-0.5148, 0.8567, 0.0322]), 0.85 * (0.55 - s1), gv)
    w = w + AmBody(v, np.array([-0.1029, -0.7544, -0.6483]), 0.60 * (0.55 + s2), gv)
    w = w + AmBody(v, np.array([-0.2722, -0.1838, -0.9445]), 0.60 * (0.55 - s2), gv)
    gw = np.stack([cr * gv[:, 0] - sr * gv[:, 1], cr * gv[:, 1] + sr * gv[:, 0], gv[:, 2]], 1)
    k = Rc * Wob[0] * 1.2074
    g = k * gw
    gT = g - u * np.sum(u * g, axis=1, keepdims=True)
    return Rc + k * w, gT


def Mound(u, q, h, c0, gm):
    s = 1.0 / max(1.0 - c0, 1e-3)
    x = sat((u @ q - c0) * s)
    gm += (h * 6.0 * x * (1.0 - x) * s)[:, None] * q
    return h * x * x * (3.0 - 2.0 * x)


def Surr(B, ax, nn, gap, hug):
    a = B[:3] @ ax
    v = B[:3] - ax * a
    R = B[3] + gap + (1.0 - hug) * np.linalg.norm(v)
    q = v * hug
    p = nn @ q
    Q = q @ q
    e = p + np.sqrt(np.maximum(R * R - Q + p * p, 0.0))
    x = np.sqrt(max(R * R - Q, 0.0))
    A = float(B[3] >= 1e-3)
    return a, e, x, A


def StrandR(z, zCs, zEs, AP3, lamC):
    eC = np.exp(-np.maximum(z - zCs, 0.0) / max(lamC, 0.1))
    eE = np.exp(-np.maximum(zEs - z, 0.0) / max(AP3[2], 0.1))
    return AP3[0] + (AP3[1] - AP3[0]) * sat(eC + eE)


def ArmRay(m, z0, sa, Rcm, pr, kC, D, re, Aw, DA, Ratt, kAt, Aat, kE, kN):
    mm = m * m
    F = np.sqrt(np.maximum(mm + 2.0 * z0 * sa * m + z0 * z0, 0.0)) - Rcm
    F = SminS(F, m - pr, kC, 1.0)
    E = np.full_like(m, 1e5)
    for j in range(3):
        E = SminS(E, np.sqrt(np.maximum(mm + 2.0 * D[j] * sa * m + D[j] * D[j], 0.0)) - re[j], kE, Aw[j])
    E = SminS(E, np.sqrt(np.maximum(mm + 2.0 * DA * sa * m + DA * DA, 0.0)) - Ratt, kAt, Aat)
    return SminS(F, E, kN, 1.0)


def ArmWindow(AP, B, Lx):
    gap = AP['gap']
    Ebc = max(float(Bi[3] >= 1e-3) * (Bi[3] + gap + np.linalg.norm(Bi[:3])) for Bi in B)
    zW0 = AP['AP5'][0] + np.linalg.norm(AP['tilt']) + AP['AP4'][0] + AP['AP5'][1] + 1.0
    zW1 = Lx - Ebc - AP['AP3'][3] - AP['AP3'][2]
    return zW0, zW1


CURL_V4 = True    # True = StrandCurl v4 (el integrado: ventana sin^2, una comba k = pi, amplitud 0,10); False = v3


def StrandCurl(p, Pc, ax, U, Vb, zW0, zW1, S, Ag, K, idx, T):
    if CURL_V4:
        return StrandCurl_v4(p, Pc, ax, U, Vb, zW0, zW1, S, Ag, K, idx, T)
    return StrandCurl_v3(p, Pc, ax, U, Vb, zW0, zW1, S, Ag, K, idx, T)


def StrandCurl_v4(p, Pc, ax, U, Vb, zW0, zW1, S, Ag, K, idx, T):
    """espejo de LVLib::StrandCurl (v4, la integrada)"""
    Lw = max(zW1 - zW0, 1.0)
    zt = sat(((p - Pc) @ ax - zW0) / Lw)
    sw = np.sin(np.pi * zt)
    win = sw * sw
    swr = 0.75 + 0.5 * Hash(idx + 0.2)
    gust = 0.6 + 0.4 * np.sin(0.19 * T + TAU * Hash(idx + 0.83))
    As = max(K, 0.0) * 0.10 * Lw * SS(3.0, 10.0, Lw) * (1.0 - 0.75 * SS(0.3, 0.9, S)) * gust * (1.0 + 0.4 * Ag)
    be = 0.45 * (2.0 * Hash(idx + 0.37) - 1.0) + 0.35 * np.sin(0.047 * T + TAU * Hash(idx + 0.43))
    cb, sb = np.cos(be), np.sin(be)
    dA = Vb * cb + U * sb
    dB = U * cb - Vb * sb
    p1 = np.pi * zt - (0.6 * swr * T + TAU * Hash(idx + 0.61))
    s1 = np.sin(p1)
    sway = 0.55 * np.sin(0.23 * swr * T + TAU * Hash(idx + 0.87))
    shp = s1[:, None] * dA + sway * dB
    return (As * win)[:, None] * shp


def StrandCurl_v3(p, Pc, ax, U, Vb, zW0, zW1, S, Ag, K, idx, T):
    Lw = max(zW1 - zW0, 1.0)
    zt = sat(((p - Pc) @ ax - zW0) / Lw)
    qz = zt * (1.0 - zt)
    win = 64.0 * qz * qz * qz
    swr = 0.6 * (0.75 + 0.5 * Hash(idx + 0.2))
    gust = 0.6 + 0.4 * np.sin(0.19 * T + TAU * Hash(idx + 0.83))
    As = max(K, 0.0) * 0.12 * Lw * SS(3.0, 10.0, Lw) * (1.0 - 0.75 * SS(0.3, 0.9, S)) * gust * (1.0 + 0.4 * Ag)
    k1, k2 = 4.712389, 7.853982
    p1 = k1 * zt - (T * swr + TAU * Hash(idx + 0.61))
    p2 = k2 * zt - (1.37 * T * swr + TAU * Hash(idx + 0.87))
    shp = np.sin(p1)[:, None] * Vb + 0.6 * np.sin(p2)[:, None] * U
    return (As * win)[:, None] * shp


def RayExit(d, B, gap):
    R = B[3] + gap
    b = d @ B[:3]
    return float(B[3] >= 1e-3) * (b + np.sqrt(np.maximum(R * R - B[:3] @ B[:3] + b * b, 0.0)))


# ------------------------------------------------------------------------------------------------
# Superficies que dibuja la celula (muestras)
# ------------------------------------------------------------------------------------------------
def arm_surface(G, idx, LV0, LV1, LV2, LV3, LV4, LV5, T, rings=104, sides=36, iters=7):
    """Espejo de LovingArmVS: vertices del tubo (rings+1) x sides -> posicion final (con curl)."""
    AP, B = ArmSetup(G, idx, LV0, LV1, LV2, LV3, LV4, LV5, T)
    ys = np.linspace(-100.0, 100.0, rings + 1)
    angs = 2 * np.pi * np.arange(sides) / sides
    Y, Aa = np.meshgrid(ys, angs, indexing='ij')
    t = sat((Y.ravel() + 100.0) * 0.005)
    rc = np.stack([np.cos(Aa.ravel()), np.sin(Aa.ravel())], 1)
    Pc = AP['Pc']; Rcm = AP['Rcm']
    ax = G - Pc; Lx = max(np.linalg.norm(ax), 1.0); ax = ax / Lx
    U = nrm(AP['Uref'] - ax * (AP['Uref'] @ ax) + np.array([0, 0, 1e-5]))
    Vb = np.cross(ax, U)
    n = rc[:, :1] * U + rc[:, 1:] * Vb
    gap = AP['gap']; hug = sat(AP['hug'])
    S_ = [Surr(Bi, ax, n, gap, hug) for Bi in B]
    a_ = [s[0] for s in S_]; e_ = [s[1] for s in S_]; x_ = [s[2] for s in S_]; A_ = [s[3] for s in S_]
    Enear = np.max([A_[j] * (x_[j] - a_[j]) for j in range(3)])
    Emax = np.max(np.stack([A_[j] * (e_[j] + abs(a_[j])) for j in range(3)]), axis=0)
    zEs = Lx - Enear
    AP3, AP4, AP5 = AP['AP3'], AP['AP4'], AP['AP5']
    t1, t2 = AP5[2], AP5[3]
    zS = 0.8 * Rcm
    zN = max(zEs - 2.0 * AP3[2], zS + 0.5)
    zA = lerp(zS, zN, 0.5 - 0.5 * np.cos(np.pi * sat(t / max(t1, 1e-3))))
    zB = lerp(zN, Lx, sat((t - t1) / max(t2 - t1, 1e-3)))
    z0 = lerp(lerp(zA, zB, step(t1, t)), Lx, step(t2, t))
    al = sat((t - t2) / max(1.0 - t2, 1e-3)) * 1.5707963
    sa, ca = np.sin(al), np.cos(al); s2 = sa * sa
    pr = StrandR(z0, AP5[0] + n @ AP['tilt'], zEs, AP3, AP5[1])
    D = [z0 - (Lx + a_[j]) for j in range(3)]
    re = [lerp(e_[j], x_[j], s2) for j in range(3)]
    kC, kE, Ratt = AP4[0], AP4[1], AP4[2]; kN = AP3[3]
    DA = z0 - (Lx - AP4[3])
    kAt = max(kE * sat(Ratt / 2.0), 0.05); Aat = float(Ratt >= 1e-3)
    rmax = np.maximum(Rcm + kC, Emax + kE) + AP3[1] + kN + 2.0
    f = lambda m: ArmRay(m, z0, sa, Rcm, pr, kC, D, re, A_, DA, Ratt, kAt, Aat, kE, kN)
    f0 = f(np.zeros_like(z0)); fhi = f(rmax)
    lo = np.zeros_like(z0); hi = rmax.copy(); flo = f0.copy()
    for _ in range(iters):
        mr = 0.5 * (lo + hi)
        fm = f(mr)
        in0 = (fm <= 0.0).astype(float)
        lo = lerp(lo, mr, in0); flo = lerp(flo, fm, in0)
        hi = lerp(mr, hi, in0); fhi = lerp(fm, fhi, in0)
    rr = (lo + (hi - lo) * sat(flo / np.minimum(flo - fhi, -1e-4))) * (f0 <= 0.0)
    dst = Pc + (z0 + rr * sa)[:, None] * ax + (rr * ca)[:, None] * n
    zW0, zW1 = ArmWindow(AP, B, Lx)
    dst = dst + StrandCurl(dst, Pc, ax, U, Vb, zW0, zW1, sat(LV1[0]), sat(LV1[2]), LV5[1], idx, T)
    return dst, AP, B, (zW0, zW1, Lx)


def core_film_r(u, LV0, LV1, LV2, LV3, Ms, T):
    """Radio de la membrana del nucleo (= LovingCentreFilmVS) y su gradiente tangencial."""
    sh = Shape(LV0, LV1, LV2, LV3)
    C = LV0[:3]
    gC = CentreGap(LV1, LV3, sh['Rc'])
    r, gT = CentreR(u, sh['Rc'], LV1, LV3, T)
    gm = np.zeros_like(u)
    for M in Ms:
        q = nrm(M[:3] - C + np.array([1e-4, 0, 0]))
        r = r + Mound(u, q, sh['MoundH'] * M[3], 0.55, gm)
    gT = gT + gm - u * np.sum(u * gm, axis=1, keepdims=True)
    return r + gC, gT, sh


def dust_points(LV0, LV1, LV2, LV3, LV4, LV5, Ms, T, DustK, CamL, n=2400, rng=None):
    """Espejo de LovingDustVS: las 4 esquinas de cada particula visible."""
    rng = rng or np.random.default_rng(0)
    sh = Shape(LV0, LV1, LV2, LV3)
    C = LV0[:3]
    UVa = rng.random((n, 2)); UVb = rng.random((n, 2))
    zd = 2.0 * UVa[:, 0] - 1.0; phd = TAU * UVa[:, 1]; rsd = np.sqrt(sat(1 - zd * zd))
    d = np.stack([rsd * np.cos(phd), rsd * np.sin(phd), zd], 1)
    sel, e = UVb[:, 0], UVb[:, 1]
    off = max(DustK[3], 0.0) * (0.35 + 0.65 * frac(e * 7.31))
    rC, _, _ = core_film_r(d, LV0, LV1, LV2, LV3, Ms, T)
    Pcore = C + d * (rC + off)[:, None]
    Np = sum(float(M[3] >= 0.5) for M in Ms)
    kf = np.floor(sat((sel - 0.34) / 0.66) * max(Np, 1.0) * 0.9999)
    out = np.zeros((n, 3)); vis = np.zeros(n); isStrA = np.zeros(n)
    isCore = sel <= 0.34
    # por grupo
    for k in range(10):
        mask = (kf == k)
        if not mask.any():
            continue
        Gs = Ms[k]
        AP, B = ArmSetup(Gs[:3], float(k), LV0, LV1, LV2, LV3, LV4, LV5, T)
        dd = d[mask]
        envR = np.max(np.stack([RayExit(dd, Bi, AP['gap']) for Bi in B]), axis=0)
        Penv = Gs[:3] + dd * (envR + off[mask])[:, None]
        Pc = AP['Pc']; ax = Gs[:3] - Pc; Lx = max(np.linalg.norm(ax), 1.0); ax = ax / Lx
        U = nrm(AP['Uref'] - ax * (AP['Uref'] @ ax) + np.array([0, 0, 1e-5])); Vb = np.cross(ax, U)
        zW0, zW1 = ArmWindow(AP, B, Lx)
        zs = np.clip(lerp(zW0, max(zW1, zW0), UVa[mask, 0]) + 1.5 * DustK[2] * np.sin(T * 0.29 + TAU * e[mask]), zW0, max(zW1, zW0))
        qd = nrm(dd - np.outer(dd @ ax, ax) + np.array([1e-4, 0, 0]))
        Pstr = Pc + zs[:, None] * ax + qd * (AP['AP3'][0] + 0.35 * off[mask])[:, None]
        Pstr = Pstr + StrandCurl(Pstr, Pc, ax, U, Vb, zW0, zW1, sat(LV1[0]), sat(LV1[2]), LV5[1], float(k), T)
        isEnv = np.maximum((e[mask] <= 0.62).astype(float), 1.0 - SS(4.0, 12.0, zW1 - zW0))
        P = lerp(Pstr, Penv, isEnv[:, None])
        out[mask] = P
        isStrA[mask] = 1.0 - isEnv
        vis[mask] = float(Gs[3] >= 0.5)
    out[isCore] = Pcore[isCore]; vis[isCore] = 1.0; isStrA[isCore] = 0.0
    P = out + (DustK[2] * (1.0 - 0.85 * isStrA))[:, None] * np.stack([np.sin(T * 0.31 + 44.7 * UVa[:, 0]), np.sin(T * 0.27 + 31.3 * UVa[:, 1]),
                                   np.sin(T * 0.23 + 23.9 * e)], 1)
    f = nrm(CamL - P + np.array([1e-4, 0, 0]))
    rgt = nrm(np.cross(np.array([0, 0, 1.0]), f) + np.array([1e-4, 0, 0]))
    upv = np.cross(f, rgt)
    sz = max(DustK[0], 0.0) * (0.6 + 0.8 * frac(e * 3.7)) * vis
    corners = []
    for cx, cy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        corners.append(P + (rgt * cx + upv * cy) * sz[:, None])
    pts = np.concatenate(corners, 0)
    v4 = np.concatenate([vis] * 4)
    return pts[v4 > 0.5]


def balls_points(G, idx, LV0, LV1, LV2, LV3, LV4, LV5, T, n=400):
    """Superficie de las bolas opacas: puntos sobre cada esfera (superconjunto de la union)."""
    AP, B = ArmSetup(G, idx, LV0, LV1, LV2, LV3, LV4, LV5, T)
    k = np.arange(n) + 0.5
    zz = 1 - 2 * k / n; rr = np.sqrt(1 - zz * zz); ph = np.pi * (1 + 5 ** 0.5) * k
    d = np.stack([rr * np.cos(ph), rr * np.sin(ph), zz], 1)
    pts = [G + Bi[:3] + d * Bi[3] for Bi in B if Bi[3] >= 1e-3]
    return np.concatenate(pts, 0)


def fib_sphere(n):
    k = np.arange(n) + 0.5
    zz = 1 - 2 * k / n; rr = np.sqrt(1 - zz * zz); ph = np.pi * (1 + 5 ** 0.5) * k
    return np.stack([rr * np.cos(ph), rr * np.sin(ph), zz], 1)


# ================================================================================================
# PISTA C — espejo de las funciones nuevas (CurlEnv, OuterEnv, OuterLobe, OuterWob) + LovingOuterVS
# ================================================================================================
RN = 100.0            # escala de normalizacion de la norma p (cm): evita desbordes en fp32
KAPPA = 1.0           # lente de la hebra (study_sigma3: 0,79 ventana actual, 0,81 ventana sin(pi q))
CSIG = 1.15           # lobulo vs esfera acotante (umbral exacto = 1,0, study_sigma)


def CurlEnv(S, Ag, K):
    return 1.1662 * 0.12 * max(K, 0.0) * (1.0 - 0.75 * SS(0.3, 0.9, S)) * (1.0 + 0.4 * Ag)


def OuterEnv(sh, gC, LV1, LV3, LV4, LV5, OuterK):
    """espejo de LVLib::OuterEnv -> (Env, Win)"""
    rb, gap, Rc = sh['rb'], sh['gap'], sh['Rc']
    Coh = Calm(LV1); Ag = sat(LV1[2]); OM = max(LV3[3], 0.0); S = sat(LV1[0])
    Ab = 0.16 * OM * (1.0 - 0.35 * Coh) * (1.0 + 0.3 * Ag)
    R1 = rb * (1.12 * (1.0 + 0.85 * (1.414 - 0.414 * sat(LV4[3]))) * (1.0 + Ab) + 0.09) + gap
    Ac = CurlEnv(S, Ag, LV5[1])
    live = min(max(LV3[2], 0.0) * (1.0 + 0.4 * Ag) * (1.0 - 0.5 * Coh) * max(OuterK[3], 0.0), 2.5)
    Env = np.array([R1, Ac, 0.5 * live, 0.09 * live])
    Q1 = 0.88 * (1.0 - Ab) * rb + gap + sh['kN']
    Wob = CoreWob(LV1, LV3)
    rAm = max(Rc * (1.0 + Wob[0] * Wob[1]), 1.0)
    rEm = (1.0 + 0.8 * max(LV5[0], 0.0)) * sh['rEnd']
    zW0 = rAm - rEm * rEm * max(1.0 / rAm, 2.7 * Wob[0] / Rc) + gC + 0.8 * sh['MoundH'] + sh['kC'] + sh['lam'] + 1.0
    Win = np.array([zW0, Q1, sh['lam'], 1.12 * sh['rMid']])
    return Env, Win


def GroupScale_h(h, SV):
    return 1.0 + max(SV, 0.0) * (1.2 * h - 0.4)


def outer_r(u, LV0, LV1, LV2, LV3, LV5, Ms, OuterK, T, parts=False, LV4=None):
    """Espejo de LovingOuterVS. u: (n,3) unitarios. Devuelve r (n,), N (n,3) [, dict de terminos]."""
    sh = Shape(LV0, LV1, LV2, LV3)
    Rc = sh['Rc']; C = LV0[:3]
    gC = CentreGap(LV1, LV3, Rc)
    m = max(OuterK[0], 0.0)
    p = lerp(8.0, 3.0, sat(OuterK[2]))
    LV4 = np.array([0.0, 0.0, 1.0, 0.8]) if LV4 is None else LV4
    Env, Win = OuterEnv(sh, gC, LV1, LV3, LV4, LV5, OuterK)
    Coh = Calm(LV1)
    rcm, gTc, _ = core_film_r(u, LV0, LV1, LV2, LV3, Ms, T)      # incluye CentreGap
    rB = rcm + m + max(OuterK[1], 0.0)
    E0 = np.exp2(p * np.log2(rB / RN))
    sE = E0.copy()
    gE = E0[:, None] * gTc / rB[:, None]
    lobes = []
    for k, M in enumerate(Ms):
        idx = float(k)
        v = M[:3] - C
        D = max(np.linalg.norm(v), 1.0)
        q = nrm(v + np.array([1e-4, 0.0, 0.0]))
        t = u @ q
        h = Hash(idx + 0.93)                 # solo el ritmo del estiramiento
        gs = GroupScale(idx, LV5)
        Rt = gs * Env[0] + m
        zW1 = D - gs * Win[1] - Win[2]
        Lw = max(zW1 - Win[0], 0.0)
        Y = Env[1] * Lw * SS(3.0, 10.0, Lw) + Win[3] + m
        zc = max(0.5 * (Win[0] + max(zW1, Win[0])), 1.0)
        P = D + Rt
        sg = max(CSIG * Rt / D, KAPPA * Y * Y * P / (2.0 * zc * zc * max(P - zc, 1.0)), 0.04)
        mx = (1.0 - Coh) * np.sin(T * (0.21 + 0.08 * frac(h * 5.3)) + TAU * frac(h * 13.7)) + Coh * np.sin(LV1[1] - 1.6)
        P = P + Env[2] * Rt * (0.5 + 0.5 * mx)
        wP = max(sat(M[3]) * P, 0.01)
        E = np.exp2(p * (np.log2(wP / RN) + (t - 1.0) * 1.442695 / sg))
        sE += E
        gE += (E / sg)[:, None] * q
        lobes.append((D, Rt, sg, P))
    r = RN * np.exp2(np.log2(sE) / p)
    G = gE / sE[:, None]
    # ondulacion POSITIVA (nunca achica)
    Wv, gW = OuterWob(u, T)
    fac = 1.0 + Env[3] * Wv
    r = r * fac
    G = G + (Env[3] / fac)[:, None] * gW
    Gt = G - u * np.sum(u * G, axis=1, keepdims=True)
    N = nrm(u - Gt)
    if parts:
        return r, N, dict(rB=rB, rcm=rcm, lobes=lobes, Env=Env, Win=Win, p=p, m=m, Rc=Rc)
    return r, N


def OuterWob(u, T):
    F3 = np.array([0.662, -0.419, 0.621]); F4 = np.array([0.286, 0.911, -0.297])
    fw = 3.0
    a1 = u @ F3 * fw + T * 0.16
    a2 = u @ F4 * fw * 1.31 - T * 0.12
    a3 = a1 * 1.7 + a2 * 0.6 + 2.1
    w = np.sin(a1) * np.sin(a2) + 0.35 * np.sin(a3)
    W = 0.5 + w / 2.7
    gw = ((np.cos(a1) * np.sin(a2) + 0.595 * np.cos(a3)) * fw / 2.7)[:, None] * F3        + ((np.sin(a1) * np.cos(a2) + 0.21 * np.cos(a3)) * fw * 1.31 / 2.7)[:, None] * F4
    return W, gw
