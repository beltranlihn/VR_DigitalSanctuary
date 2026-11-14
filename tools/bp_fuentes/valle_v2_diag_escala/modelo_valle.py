# -*- coding: utf-8 -*-
"""modelo_valle.py - modelo numpy del valle de Entering (v1 de la spec y candidato v2 de ESCALA).

Solo numpy. No toca Unreal, ni la spec, ni los HLSL. Lo usan diag_escala.py (metricas) y render_valle.py
(imagenes). Convenciones de la spec (docs/PLAN-VALLE-ENTERING-2026-09-27.md, seccion 1): cm, s, ejes de
Unreal (X adelante, Y DERECHA, Z arriba), azimut desde +X hacia +Y.

v1  = la spec tal cual (seccion 3 altura, seccion 4 suelo, seccion 6 cielo). Se controla contra la seccion 12.
v2  = candidato de ESCALA de este diagnostico: piso quieto mas grande, llanura con ondas suaves, colinas medias
      a 80-230 m, colinas lejanas + anillo a 300-600 m, malla hasta 640 m, niebla por distancia + niebla de altura.
      Todas las cuentas usan el MISMO campo de 4 dunas de la spec (constantes DUNAS), escalado y girado por capa.
"""
import math

import numpy as np

# ------------------------------------------------------------------------------------------------
# utilidades (identicas a HLSL)
# ------------------------------------------------------------------------------------------------
def sat(x):
    return np.clip(x, 0.0, 1.0)


def ss(a, b, x):
    t = sat((np.asarray(x, dtype=np.float64) - a) / (b - a))
    return t * t * (3.0 - 2.0 * t)


def lerp(a, b, t):
    return a + (b - a) * t


def srgb(c):
    c = np.clip(c, 0.0, 1.0)
    return np.where(c <= 0.0031308, 12.92 * c, 1.055 * np.power(c, 1.0 / 2.4) - 0.055)


def lum(c):
    c = np.asarray(c)
    return 0.2126 * c[..., 0] + 0.7152 * c[..., 1] + 0.0722 * c[..., 2]


def dir_d(az, el):
    a, e = math.radians(az), math.radians(el)
    return np.array([math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)])


# Dunas: constantes del codigo (spec 3.3): (angulo deg, lambda cm, peso, fase rad, periodo s, fase temporal rad)
DUNAS = (
    (18.0, 3000.0, 1.00, 0.0, 53.0, 0.0),
    (101.0, 2200.0, 0.75, 1.7, 67.0, 2.1),
    (143.0, 1650.0, 0.55, 4.1, 41.0, 4.4),
    (232.0, 1250.0, 0.35, 2.9, 83.0, 1.3),
)


def sigma(x, y, t, scale, seed, shx, shy, Mt, speed):
    """Campo de dunas de la spec (3.3) con escala/giro/corrimiento. |sigma| <= 1 + Mt."""
    s = 0.0
    for (a, lam, w, ph, T, ps) in DUNAS:
        ar = math.radians(a + seed)
        k = 2.0 * math.pi / (lam * scale)
        g = k * (math.cos(ar) * (x + shx) + math.sin(ar) * (y + shy)) + ph
        m = math.sin(2.0 * math.pi * speed * t / T + ps)
        s = s + w * (1.0 + Mt * m) * np.sin(g)
    return s / 2.65


# ------------------------------------------------------------------------------------------------
# Parametros de sombreado y cielo (spec 7.1): comunes a v1 y v2
# ------------------------------------------------------------------------------------------------
LOOK = dict(
    LightAz=20.0, LightEl=25.0, Wrap=0.3, ShadeFloor=0.0, SlopeDark=1.2,
    ColLit=(0.434, 0.527, 0.855), ColShadow=(0.061, 0.117, 0.352), ColSheen=(0.855, 0.761, 0.913),
    Sheen=0.4, SheenPow=4.0, SheenBack=0.35, CrestLight=0.2,
    ShadowSoft=0.8, ShadowTint=(0.305, 0.352, 0.68), ShadowMax=0.8,
    SkyZenith=(0.216, 0.328, 0.597), SkyHorizon=(0.597, 0.624, 0.839), SkyGlow=(0.831, 0.68, 0.855),
    SkyGradTop=0.7, GlowAz=20.0, GlowEl=2.0, GlowPow=2.0, GlowHeight=0.45, GlowAmt=0.8,
    MoonAz=-40.0, MoonEl=7.0, MoonRadius=9.0, MoonEdge=0.03, MoonColor=(0.73, 0.644, 0.839),
    MoonOpacity=0.55, MoonFill=0.2, MoonRim=1.0,
    ShadowCenter=(380.0, 0.0, 125.0), ShadowRadius=85.0, ShadowStrength=1.5,
)

# ------------------------------------------------------------------------------------------------
# v1: la spec (seccion 3), defaults de 7.1
# ------------------------------------------------------------------------------------------------
P1 = dict(
    ValleyX=350.0, ValleyA=950.0, ValleyB=600.0, SeatIn=60.0, SeatOut=250.0,
    RimHeight=380.0, RimCrest=3.0, RimBack=4.0, DuneAmp=520.0, DuneRise=1.6,
    DuneLow=-0.35, DuneHigh=1.2, DuneScale=1.0, DuneSeed=0.0, DuneShiftX=0.0, DuneShiftY=0.0,
    MorphAmt=0.45, MorphSpeed=1.0, MorphNear=800.0, MorphFar=3000.0,
    FogStart=1000.0, FogDist=5000.0, FogMax=0.6,
    R_MAX=4400.0,
)


def h_v1(x, y, t, P=P1):
    """(h, hf) de la spec 3.6. x, y en cm (arrays)."""
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    r = np.hypot(x, y)
    e = np.hypot((x - P["ValleyX"]) / P["ValleyA"], y / P["ValleyB"])
    E1 = max(P["RimCrest"], 1.01)
    E2 = max(P["RimBack"], E1 + 0.01)
    u2 = ss(E1, E2, e)
    h = P["RimHeight"] * ss(1.0, E1, e) * (1.0 - u2)
    Mt = P["MorphAmt"] * ss(P["MorphNear"], max(P["MorphFar"], P["MorphNear"] + 1.0), r)
    sig = sigma(x, y, t, P["DuneScale"], P["DuneSeed"], P["DuneShiftX"], P["DuneShiftY"], Mt, P["MorphSpeed"])
    f = ss(P["DuneLow"], max(P["DuneHigh"], P["DuneLow"] + 0.01), sig)
    env = ss(1.0, max(P["DuneRise"], 1.01), e) * (1.0 - u2) * ss(P["SeatIn"], max(P["SeatOut"], P["SeatIn"] + 1.0), r)
    return h + P["DuneAmp"] * env * f, env * f


def fog_v1(Dist, pz, camz, P=P1):
    return P["FogMax"] * (1.0 - np.exp(-np.maximum(Dist - P["FogStart"], 0.0) / max(P["FogDist"], 1.0)))


# ------------------------------------------------------------------------------------------------
# v2: candidato de ESCALA (este diagnostico). Todo en cm.
# ------------------------------------------------------------------------------------------------
P2 = dict(
    # capa 0 - piso quieto (z = 0 exacto): elipse; usuario en e = 0,27 y metaball en e = 0,01
    ValleyX=400.0, ValleyA=1500.0, ValleyB=1250.0,
    # capa 1 - llanura: ondas suaves y simetricas (la "ondulacion" la disena otra tarea; aca solo la escala)
    PlainAmp=90.0, PlainRise=2.2, PlainScale=1.6, PlainSeed=37.0, PlainFade0=20000.0, PlainFade1=30000.0,
    # capa 2 - colinas medias: banda polar 55-260 m, lambda 100-240 m (DunaScale 8), alto hasta ~0,9*MidAmp
    MidAmp=2200.0, MidScale=8.0, MidSeed=63.0, MidLow=-0.35, MidHigh=1.2,
    MidIn0=5500.0, MidIn1=10000.0, MidOut0=19000.0, MidOut1=26000.0,
    # capa 3 - colinas lejanas sobre un anillo (garantia del horizonte y borde oculto)
    FarBase=2600.0, FarAmp=5500.0, FarScale=22.0, FarSeed=151.0, FarLow=-0.7, FarHigh=1.2,
    FarIn0=28000.0, FarIn1=40000.0, FarCrest=47000.0, FarBack=59000.0,
    # transformacion (como v1: la amplitud respira; solo capas 2 y 3 aca)
    MorphAmt=0.45, MorphSpeed=1.0,
    # niebla: distancia + altura (tau = d * (1/FogDist + F(z0, z1)/HFogDist))
    # ronda 1 (demasiado lavada, silueta lejana 0,78): FogStart 1200, FogDist 30000, FogMax 0,92, HFogDist 25000
    FogStart=1500.0, FogDist=45000.0, FogMax=0.9, HFogDist=60000.0, HFogFall=1500.0,
    R_MAX=64000.0,
)


def h_v2(x, y, t, P=P2):
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    r = np.hypot(x, y)
    e = np.hypot((x - P["ValleyX"]) / P["ValleyA"], y / P["ValleyB"])
    # capa 1: llanura (simetrica, sin umbral), fuera del piso quieto, se apaga bajo las colinas lejanas
    envP = ss(1.0, P["PlainRise"], e) * (1.0 - ss(P["PlainFade0"], P["PlainFade1"], r))
    sigP = sigma(x, y, t, P["PlainScale"], P["PlainSeed"], 0.0, 0.0, 0.0, 0.0)
    h = P["PlainAmp"] * envP * sigP
    # capa 2: colinas medias (dunas con umbral, como v1)
    envM = ss(P["MidIn0"], P["MidIn1"], r) * (1.0 - ss(P["MidOut0"], P["MidOut1"], r))
    sigM = sigma(x, y, t, P["MidScale"], P["MidSeed"], 0.0, 0.0, P["MorphAmt"], P["MorphSpeed"])
    fM = ss(P["MidLow"], P["MidHigh"], sigM)
    h = h + P["MidAmp"] * envM * fM
    # capa 3: anillo + colinas lejanas; todo vale 0 desde FarBack (el borde de la malla queda detras)
    back = 1.0 - ss(P["FarCrest"], P["FarBack"], r)
    ring = P["FarBase"] * ss(P["FarIn0"], P["FarCrest"], r) * back
    envF = ss(P["FarIn0"], P["FarIn1"], r) * back
    sigF = sigma(x, y, t, P["FarScale"], P["FarSeed"], 0.0, 0.0, P["MorphAmt"], P["MorphSpeed"])
    fF = ss(P["FarLow"], P["FarHigh"], sigF)
    h = h + ring + P["FarAmp"] * envF * fF
    hf = np.clip(envM * fM + envF * fF, 0.0, 1.0)
    return h, hf


def fog_v2(Dist, pz, camz, P=P2):
    """Niebla por distancia + niebla de altura exponencial INTEGRADA a lo largo del rayo (Quilez):
    densidad rho(z) = exp(-z/H)/HFogDist; profundidad optica = d * H (e^(-z0/H) - e^(-z1/H)) / (z1 - z0)."""
    d = np.maximum(Dist - P["FogStart"], 0.0)
    H = P["HFogFall"]
    z0 = np.maximum(camz, 0.0)
    z1 = np.maximum(pz, 0.0)
    dz = z1 - z0
    safe = np.where(np.abs(dz) > 1.0, dz, 1.0)
    F = np.where(np.abs(dz) > 1.0, H * (np.exp(-z0 / H) - np.exp(-z1 / H)) / safe, np.exp(-z0 / H))
    tau = d * (1.0 / P["FogDist"] + F / P["HFogDist"])
    return P["FogMax"] * (1.0 - np.exp(-tau))


# ------------------------------------------------------------------------------------------------
# Sombreado (port de ValleyPS; spec 4-6)
# ------------------------------------------------------------------------------------------------
def _v3(t):
    return np.array(t, dtype=np.float64)


def sky_color(dv, L=LOOK, moon=True):
    """dv: (..., 3) unitario (direccion de la mirada)."""
    dv = np.asarray(dv, dtype=np.float64)
    GlowDir = dir_d(L["GlowAz"], L["GlowEl"])
    MoonDir = dir_d(L["MoonAz"], L["MoonEl"])
    MoonCosR = math.cos(math.radians(L["MoonRadius"]))
    s = ss(0.0, max(L["SkyGradTop"], 0.01), dv[..., 2])[..., None]
    sky = lerp(_v3(L["SkyHorizon"]), _v3(L["SkyZenith"]), s)
    hxy = dv[..., :2]
    hz = hxy / np.sqrt(np.maximum((hxy * hxy).sum(-1), 1e-8))[..., None]
    gh = GlowDir[:2] / np.linalg.norm(GlowDir[:2])
    gaz = np.power(np.maximum((hz * gh).sum(-1), 1e-6), max(L["GlowPow"], 0.1))
    gel = 1.0 - ss(0.0, max(L["GlowHeight"], 0.001), np.abs(dv[..., 2] - GlowDir[2]))
    sky = lerp(sky, _v3(L["SkyGlow"]), sat(L["GlowAmt"] * gaz * gel)[..., None])
    if moon:
        cosA = (dv * MoonDir).sum(-1)
        rho = np.sqrt(np.maximum(1.0 - cosA, 0.0) / max(1.0 - MoonCosR, 1e-6))
        me = max(L["MoonEdge"], 0.001)
        disc = 1.0 - ss(1.0 - me, 1.0 + me, rho)
        o = dv - MoonDir * cosA[..., None]
        gm = GlowDir - MoonDir * float(np.dot(GlowDir, MoonDir))
        side = 0.5 + 0.5 * (o * gm).sum(-1) / np.sqrt(np.maximum((o * o).sum(-1), 1e-10)) / math.sqrt(max(float(np.dot(gm, gm)), 1e-10))
        rim = ss(0.6, 1.0, rho) * side * side
        a = sat(L["MoonOpacity"] * disc * (L["MoonFill"] + L["MoonRim"] * rim))
        a = np.where(rho < 1.0 + me, a, 0.0)
        sky = lerp(sky, _v3(L["MoonColor"]), a[..., None])
    return sky


def ground_color(px, py, h, gx, gy, hf, cam, fogfun, L=LOOK, return_parts=False):
    """Color del suelo (Part 0) para puntos (px, py) con altura h y gradiente (gx, gy); cam en local (cm)."""
    pos = np.stack([px, py, h], -1)
    cv = np.asarray(cam, dtype=np.float64) - pos
    Dist = np.sqrt((cv * cv).sum(-1))
    V = cv / np.maximum(Dist, 1e-6)[..., None]
    dv = -V
    LightDir = dir_d(L["LightAz"], L["LightEl"])
    N = np.stack([-gx, -gy, np.ones_like(gx)], -1)
    N = N / np.sqrt((N * N).sum(-1))[..., None]
    wrap = sat(((N * LightDir).sum(-1) + L["Wrap"]) / (1.0 + L["Wrap"]))
    k = lerp(L["ShadeFloor"], 1.0, wrap) * sat(1.0 - L["SlopeDark"] * (1.0 - N[..., 2]))
    col = lerp(_v3(L["ColShadow"]), _v3(L["ColLit"]), k[..., None])
    col = lerp(col, _v3(L["ColLit"]), (L["CrestLight"] * hf * hf)[..., None])
    fres = np.power(np.maximum(1.0 - sat((N * V).sum(-1)), 1e-6), max(L["SheenPow"], 0.5))
    fwd = sat(0.5 + 0.5 * (dv * LightDir).sum(-1))
    col = lerp(col, _v3(L["ColSheen"]), sat(L["Sheen"] * fres * lerp(L["SheenBack"], 1.0, fwd))[..., None])
    SC = _v3(L["ShadowCenter"])
    Hs = np.maximum(SC[2] - h, 1.0)
    Rs = max(L["ShadowRadius"], 1.0)
    peak = L["ShadowStrength"] * Rs * Rs / (Rs * Rs + Hs * Hs)
    ws = np.maximum(L["ShadowSoft"] * Hs, 1.0)
    qs = 1.0 + ((px - SC[0]) ** 2 + (py - SC[1]) ** 2) / (ws * ws)
    O = np.minimum(sat(peak * qs ** -1.5), L["ShadowMax"])
    col = col * (1.0 - O[..., None] * (1.0 - _v3(L["ShadowTint"])))
    fog = fogfun(Dist, h, float(cam[2]))
    sky = sky_color(dv, L, moon=False)
    out = lerp(col, sky, fog[..., None])
    if return_parts:
        return out, col, sky, fog, O
    return out


def grad_fd(hfun, x, y, t, P, d=0.5):
    hx1, _ = hfun(x + d, y, t, P)
    hx0, _ = hfun(x - d, y, t, P)
    hy1, _ = hfun(x, y + d, t, P)
    hy0, _ = hfun(x, y - d, t, P)
    return (hx1 - hx0) / (2 * d), (hy1 - hy0) / (2 * d)


# ------------------------------------------------------------------------------------------------
# Anillos de la malla
# ------------------------------------------------------------------------------------------------
def anillos_v1(S=192, dA=30.0, R=4400.0):
    q = 1.0 + 2.0 * math.pi / S
    ra = dA / (q - 1.0)
    na = int(math.floor(ra / dA + 1e-9))
    rs = [dA * j for j in range(1, na + 1)]
    r = rs[-1]
    while True:
        r *= q
        if r >= R:
            break
        rs.append(r)
    if R - rs[-1] < 0.5 * rs[-1] * (q - 1.0):
        rs[-1] = R
    else:
        rs.append(R)
    return np.array(rs)


def anillos_v2(S=192, dA=60.0, rA=1100.0, aspecto=((0.0, 1.0),), R=64000.0, atras=(59000.0, 4)):
    """Zona A uniforme (piso quieto, plano: la densidad no hace nada, se ahorra) hasta rA; despues geometrica
    con celdas de aspecto variable (radial = aspecto * tangencial) segun tramos [(r_desde, aspecto), ...];
    detras de la cresta (atras = (r0, n)) solo n anillos hasta R (todo vale 0 y queda oculto)."""
    rs = list(np.arange(dA, rA + 0.5 * dA, dA))
    r = rs[-1]
    r_back, n_back = atras
    while r < r_back:
        asp = 1.0
        for (r0, a) in aspecto:
            if r >= r0:
                asp = a
        r = r * (1.0 + asp * 2.0 * math.pi / S)
        if r >= r_back:
            break
        rs.append(r)
    rs.append(r_back)
    for j in range(1, n_back + 1):
        rs.append(r_back + (R - r_back) * j / n_back)
    return np.array(rs)
