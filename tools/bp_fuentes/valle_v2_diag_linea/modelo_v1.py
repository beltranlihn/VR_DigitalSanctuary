# -*- coding: utf-8 -*-
"""modelo_v1.py - port numpy VECTORIZADO del valle v1 (ValleyGradVS + ValleyPS, Part 0 y 1), mas un
raycast de campo de alturas para reproducir las capturas del editor. Solo lectura del repo.

Fuente: .claude/skills/unreal-vr/scripts/hlsl/ValleyGradVS.hlsl y ValleyPS.hlsl (identicos al respaldo v1).
Unidades cm y s, ejes de Unreal (X adelante, Y derecha, Z arriba).
"""
import math

import numpy as np

P = dict(ValleyX=350.0, ValleyA=950.0, ValleyB=600.0, SeatIn=60.0, SeatOut=250.0,
         RimHeight=380.0, RimCrest=3.0, RimBack=4.0, DuneAmp=520.0, DuneRise=1.6,
         DuneLow=-0.35, DuneHigh=1.2, DuneScale=1.0, DuneSeed=0.0, DuneShiftX=0.0, DuneShiftY=0.0,
         MorphAmt=0.45, MorphSpeed=1.0, MorphNear=800.0, MorphFar=3000.0,
         LightAz=20.0, LightEl=25.0, Wrap=0.3, ShadeFloor=0.0, SlopeDark=1.2,
         ColLit=(0.434, 0.527, 0.855), ColShadow=(0.061, 0.117, 0.352), ColSheen=(0.855, 0.761, 0.913),
         Sheen=0.4, SheenPow=4.0, SheenBack=0.35, CrestLight=0.2,
         ShadowSoft=0.8, ShadowTint=(0.305, 0.352, 0.68), ShadowMax=0.8,
         SkyZenith=(0.216, 0.328, 0.597), SkyHorizon=(0.597, 0.624, 0.839), SkyGlow=(0.831, 0.68, 0.855),
         SkyGradTop=0.7, GlowAz=20.0, GlowEl=2.0, GlowPow=2.0, GlowHeight=0.45, GlowAmt=0.8,
         MoonAz=-40.0, MoonEl=7.0, MoonRadius=9.0, MoonEdge=0.03, MoonColor=(0.73, 0.644, 0.839),
         MoonOpacity=0.55, MoonFill=0.2, MoonRim=1.0,
         FogStart=1000.0, FogDist=5000.0, FogMax=0.6,
         ShadowCenter=(380.0, 0.0, 125.0), ShadowRadius=85.0, ShadowStrength=1.5, R_MAX=4400.0)
DUNAS = ((18.0, 3000.0, 1.00, 0.0, 53.0, 0.0), (101.0, 2200.0, 0.75, 1.7, 67.0, 2.1),
         (143.0, 1650.0, 0.55, 4.1, 41.0, 4.4), (232.0, 1250.0, 0.35, 2.9, 83.0, 1.3))


def sat(x):
    return np.clip(x, 0.0, 1.0)


def ss(a, b, x):
    t = sat((x - a) / (b - a))
    return t * t * (3.0 - 2.0 * t)


def dss(a, b, x):
    t = sat((x - a) / (b - a))
    return 6.0 * t * (1.0 - t) / (b - a)


def D(az, el):
    a, e = math.radians(az), math.radians(el)
    return np.array([math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)])


def campo(x, y, t, p=P, terms=False):
    """ValleyGradVS: devuelve h, gx, gy, hf (y, si terms, los intermedios e, env, f, B)."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    r = np.sqrt(x * x + y * y)
    rs = np.maximum(r, 1.0)
    VA, VB = max(p["ValleyA"], 1.0), max(p["ValleyB"], 1.0)
    ex, ey = (x - p["ValleyX"]) / VA, y / VB
    e = np.sqrt(ex * ex + ey * ey)
    es = np.maximum(e, 1e-4)
    dex, dey = ex / (VA * es), ey / (VB * es)
    E1 = max(p["RimCrest"], 1.01)
    E2 = max(p["RimBack"], E1 + 0.01)
    u1, du1 = ss(1.0, E1, e), dss(1.0, E1, e)
    u2, du2 = ss(E1, E2, e), dss(E1, E2, e)
    B = p["RimHeight"] * u1 * (1 - u2)
    dB = p["RimHeight"] * (du1 * (1 - u2) - u1 * du2)
    MF = max(p["MorphFar"], p["MorphNear"] + 1.0)
    Mt = p["MorphAmt"] * ss(p["MorphNear"], MF, r)
    dMt = p["MorphAmt"] * dss(p["MorphNear"], MF, r)
    w = 2 * math.pi * p["MorphSpeed"] * t
    xd, yd = x + p["DuneShiftX"], y + p["DuneShiftY"]
    ks = 2 * math.pi / max(p["DuneScale"], 0.05)
    sig = 0.0
    sm = 0.0
    gsx = 0.0
    gsy = 0.0
    for al, lam, a, ph, T, ps in DUNAS:
        ang = math.radians(p["DuneSeed"] + al)
        kx, ky = ks / lam * math.cos(ang), ks / lam * math.sin(ang)
        g = kx * xd + ky * yd + ph
        s, c = np.sin(g), np.cos(g)
        m = math.sin(w / T + ps)
        q = a * (1 + Mt * m)
        sig = sig + q * s / 2.65
        sm = sm + a * m * s / 2.65
        gsx = gsx + q * c * kx / 2.65
        gsy = gsy + q * c * ky / 2.65
    gsx = gsx + dMt * sm * x / rs
    gsy = gsy + dMt * sm * y / rs
    DH = max(p["DuneHigh"], p["DuneLow"] + 0.01)
    f, df = ss(p["DuneLow"], DH, sig), dss(p["DuneLow"], DH, sig)
    SO = max(p["SeatOut"], p["SeatIn"] + 1.0)
    seat, dseat = ss(p["SeatIn"], SO, r), dss(p["SeatIn"], SO, r)
    ED = max(p["DuneRise"], 1.01)
    Ea, dEa = ss(1.0, ED, e), dss(1.0, ED, e)
    envE = Ea * (1 - u2)
    denvE = dEa * (1 - u2) - Ea * du2
    env = envE * seat
    h = B + p["DuneAmp"] * env * f
    gex = seat * denvE * dex + envE * dseat * x / rs
    gey = seat * denvE * dey + envE * dseat * y / rs
    gx = dB * dex + p["DuneAmp"] * (gex * f + env * df * gsx)
    gy = dB * dey + p["DuneAmp"] * (gey * f + env * df * gsy)
    if terms:
        return h, gx, gy, env * f, dict(e=e, env=env, f=f, B=B, sig=sig, r=r)
    return h, gx, gy, env * f


def altura(x, y, t, p=P):
    return campo(x, y, t, p)[0]


def cielo(dv, p=P):
    """ValleyPS Part 1 sin dither (dv: (...,3) unitarios)."""
    SH, SZ, SG = (np.array(p[k]) for k in ("SkyHorizon", "SkyZenith", "SkyGlow"))
    GD = D(p["GlowAz"], p["GlowEl"])
    sky = SH + (SZ - SH) * ss(0.0, max(p["SkyGradTop"], 0.01), dv[..., 2])[..., None]
    hz = dv[..., :2] / np.sqrt(np.maximum((dv[..., :2] ** 2).sum(-1), 1e-8))[..., None]
    gh = GD[:2] / np.linalg.norm(GD[:2])
    gaz = np.power(np.maximum((hz * gh).sum(-1), 1e-6), max(p["GlowPow"], 0.1))
    gel = 1.0 - ss(0.0, max(p["GlowHeight"], 0.001), np.abs(dv[..., 2] - GD[2]))
    sky = sky + (SG - sky) * sat(p["GlowAmt"] * gaz * gel)[..., None]
    return sky


def cielo_luna(dv, p=P):
    sky = cielo(dv, p)
    MD, GD = D(p["MoonAz"], p["MoonEl"]), D(p["GlowAz"], p["GlowEl"])
    cosA = (dv * MD).sum(-1)
    rho = np.sqrt(np.maximum(1 - cosA, 0) / max(1 - math.cos(math.radians(p["MoonRadius"])), 1e-6))
    me = max(p["MoonEdge"], 0.001)
    disc = 1 - ss(1 - me, 1 + me, rho)
    o = dv - MD * cosA[..., None]
    gm = GD - MD * np.dot(GD, MD)
    side = 0.5 + 0.5 * (o * gm).sum(-1) / np.sqrt(np.maximum((o * o).sum(-1), 1e-10)) / np.linalg.norm(gm)
    rim = ss(0.6, 1.0, rho) * side * side
    a = sat(p["MoonOpacity"] * disc * (p["MoonFill"] + p["MoonRim"] * rim)) * (rho < 1 + me)
    return sky + (np.array(p["MoonColor"]) - sky) * a[..., None]


def suelo(hit, gx, gy, h, hf, cam, p=P, parts=False):
    """ValleyPS Part 0 sin dither. hit (...,3) posicion con WPO (para Dist y CamL); LPi = hit.xy."""
    L = D(p["LightAz"], p["LightEl"])
    d = cam - hit
    Dist = np.linalg.norm(d, axis=-1)
    V = d / Dist[..., None]
    dv = -V
    N = np.stack([-gx, -gy, np.ones_like(gx)], -1)
    N = N / np.linalg.norm(N, axis=-1)[..., None]
    NL = (N * L).sum(-1)
    wrap = sat((NL + p["Wrap"]) / (1 + p["Wrap"]))
    slopek = sat(1 - p["SlopeDark"] * (1 - N[..., 2]))
    k = (p["ShadeFloor"] + (1 - p["ShadeFloor"]) * wrap) * slopek
    CL, CS, CH = (np.array(p[c]) for c in ("ColLit", "ColShadow", "ColSheen"))
    col = CS + (CL - CS) * k[..., None]
    col = col + (CL - col) * (p["CrestLight"] * hf * hf)[..., None]
    fres = np.power(np.maximum(1 - sat((N * V).sum(-1)), 1e-6), max(p["SheenPow"], 0.5))
    fwd = sat(0.5 + 0.5 * (dv * L).sum(-1))
    sh = sat(p["Sheen"] * fres * (p["SheenBack"] + (1 - p["SheenBack"]) * fwd))
    col = col + (CH - col) * sh[..., None]
    SC = np.array(p["ShadowCenter"])
    Hs = np.maximum(SC[2] - h, 1.0)
    Rs = max(p["ShadowRadius"], 1.0)
    peak = p["ShadowStrength"] * Rs * Rs / (Rs * Rs + Hs * Hs)
    ws = np.maximum(p["ShadowSoft"] * Hs, 1.0)
    ds2 = (hit[..., 0] - SC[0]) ** 2 + (hit[..., 1] - SC[1]) ** 2
    qs = 1 + ds2 / (ws * ws)
    O = np.minimum(sat(peak * qs ** -1.5), p["ShadowMax"])
    col = col * (1 - O[..., None] * (1 - np.array(p["ShadowTint"])))
    fog = p["FogMax"] * (1 - np.exp(-np.maximum(Dist - p["FogStart"], 0) / max(p["FogDist"], 1)))
    sky = cielo(dv, p)
    out = col + (sky - col) * fog[..., None]
    if parts:
        return out, dict(NL=NL, wrap=wrap, slopek=slopek, k=k, fres=fres, sheen=sh, O=O, fog=fog, Nz=N[..., 2],
                         NV=(N * V).sum(-1), Dist=Dist)
    return out


def srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, 12.92 * c, 1.055 * np.power(c, 1 / 2.4) - 0.055)


def lin(s8):
    c = np.asarray(s8, float) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def luma(linrgb):
    return linrgb[..., 0] * 0.2126 + linrgb[..., 1] * 0.7152 + linrgb[..., 2] * 0.0722


def rayos(cam_yaw, cam_pitch, W, H, hfov=90.0, filas=None, cols=None):
    """Direcciones de rayo por pixel (centros en .5). Devuelve (len(filas), len(cols), 3)."""
    f = (W / 2) / math.tan(math.radians(hfov / 2))
    y, p = math.radians(cam_yaw), math.radians(cam_pitch)
    F = np.array([math.cos(p) * math.cos(y), math.cos(p) * math.sin(y), math.sin(p)])
    R = np.array([-math.sin(y), math.cos(y), 0.0])
    U = np.array([-math.sin(p) * math.cos(y), -math.sin(p) * math.sin(y), math.cos(p)])
    filas = np.arange(H) if filas is None else np.asarray(filas)
    cols = np.arange(W) if cols is None else np.asarray(cols)
    jj, ii = np.meshgrid(cols + 0.5 - W / 2, filas + 0.5 - H / 2)
    d = F + (jj / f)[..., None] * R - (ii / f)[..., None] * U
    return d / np.linalg.norm(d, axis=-1)[..., None]


def raycast(o, d, t, p=P, hfn=None, smax=20000.0, zmax=None, rmax=None):
    """Primer cruce rayo / campo de alturas (paso 0,25 % de la distancia, >= 2 cm) + biseccion.
    d (N,3). Devuelve s (N,) con NaN si no pega (cielo)."""
    hfn = hfn or (lambda x, y: altura(x, y, t, p))
    rmax = p["R_MAX"] if rmax is None else rmax
    N = d.shape[0]
    s = np.full(N, 5.0)
    out = np.full(N, np.nan)
    act = np.arange(N)
    prev = s.copy()
    while act.size:
        sa = s[act]
        pts = o + d[act] * sa[:, None]
        rr = np.hypot(pts[:, 0], pts[:, 1])
        inside = rr <= rmax
        hh = np.where(inside, hfn(pts[:, 0], pts[:, 1]), -1e9)
        below = pts[:, 2] <= hh
        if below.any():
            idx = act[below]
            lo, hi = prev[idx].copy(), s[idx].copy()
            for _ in range(30):
                mid = 0.5 * (lo + hi)
                pm = o + d[idx] * mid[:, None]
                bm = pm[:, 2] <= hfn(pm[:, 0], pm[:, 1])
                hi = np.where(bm, mid, hi)
                lo = np.where(bm, lo, mid)
            out[idx] = hi
        done = below | (sa > smax) | ((rr > rmax) & ((pts[:, :2] * d[act, :2]).sum(-1) > 0))
        if zmax is not None:
            done |= (pts[:, 2] > zmax) & (d[act, 2] > 0)
        prev[act] = sa
        s[act] = sa + np.maximum(2.0, 0.0025 * sa)
        act = act[~done]
    return out


def render(o, dirs, t, p=P, hfn=None, gfn=None, parts=False, zmax=2000.0):
    """dirs (...,3). Color lineal por rayo (suelo o cielo con luna) + mapas utiles."""
    shp = dirs.shape[:-1]
    d = dirs.reshape(-1, 3)
    s = raycast(o, d, t, p, hfn=hfn, zmax=zmax)
    hitm = ~np.isnan(s)
    col = cielo_luna(d, p)
    info = {k: np.full(d.shape[0], np.nan) for k in ("e", "h", "slope", "dist", "x", "y", "hf", "f", "env")}
    pp = {}
    if hitm.any():
        hp = o + d[hitm] * s[hitm][:, None]
        if gfn is None:
            h, gx, gy, hf, tm = campo(hp[:, 0], hp[:, 1], t, p, terms=True)
        else:
            h, gx, gy, hf, tm = gfn(hp[:, 0], hp[:, 1])
        hp[:, 2] = h
        c, pp0 = suelo(hp, gx, gy, h, hf, o, p, parts=True)
        col[hitm] = c
        info["e"][hitm] = tm.get("e", np.nan)
        info["f"][hitm] = tm.get("f", np.nan)
        info["env"][hitm] = tm.get("env", np.nan)
        info["h"][hitm] = h
        info["hf"][hitm] = hf
        info["slope"][hitm] = np.degrees(np.arctan(np.hypot(gx, gy)))
        info["dist"][hitm] = np.linalg.norm(hp - o, axis=-1)
        info["x"][hitm] = hp[:, 0]
        info["y"][hitm] = hp[:, 1]
        for k, v in pp0.items():
            a = np.full(d.shape[0], np.nan)
            a[hitm] = v
            pp[k] = a.reshape(shp)
    info = {k: v.reshape(shp) for k, v in info.items()}
    info["hit"] = hitm.reshape(shp)
    col = col.reshape(shp + (3,))
    return (col, info, pp) if parts else (col, info)
