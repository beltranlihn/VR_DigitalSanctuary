# draw_sea_model.py - MODELO DE REFERENCIA del oceano del dibujo (numpy), escrito desde el prototipo aprobado
# docs/prototipos/oceano-dibujo.html (v3). Plan: docs/PLAN-OCEANO-DIBUJO-2026-09-28.md.
# Es la segunda implementacion independiente contra la que DrawSea_check.py compara el HLSL generado.
# Tambien calcula las constantes por oleaje (W/V/E 0..5) que escribe ApplyLook del Blueprint: sirve para
# verificar en Unreal que el BP escribio los mismos numeros (python draw_sea_model.py las imprime).
import math

import numpy as np

TAU = 6.2831853
NW = 6
OFFS = [0.0, 0.85, -0.7, 0.35, -1.0, 0.55]

# defaults aprobados (v3 del prototipo) - los parametros del material, en sus unidades
DEF = dict(
    SwellAmp=22.0, SwellLenMax=2600.0, SwellLenMin=420.0, SwellDir=180.0, SwellSpread=95.0, Tempo=0.28,
    GroupAmt=0.75, GroupLen=9000.0, Warp=120.0, WarpScale=4500.0,
    Advance=5.0,
    CalmR=600.0, CalmMin=0.7, LodNear=4.0, LodFar=6.5,
    DeepColor=(0.0016, 0.0021, 0.0052), SurfColor=(0.0052, 0.0068, 0.0155), CrestColor=(0.006, 0.009, 0.017),
    CrestAmt=1.0, LightAz=40.0, LightEl=22.0, WrapPow=1.6,
    ZenithColor=(0.0006, 0.0008, 0.0022), HorizonColor=(0.0095, 0.011, 0.024), SkyPow=0.45,
    GlowColor=(0.55, 0.6, 0.75), GlowAmt=0.012, GlowPow=30.0,
    FogStart=500.0, FogDensity=0.00017, Dither=1.0,
    DustColor=(0.55, 0.62, 0.8), DustAmt=0.45, DustSize=0.9, DustBox=1400.0, DustFollow=1.0,
    DustRise=0.6, DustWobble=8.0, DustNear=35.0,
    DustBG=(0.0052, 0.0068, 0.0155),   # fondo tipico detras de las motas (= SurfColor); gotcha 485
)


def hash1(n):
    s = math.sin(n * 127.1) * 43758.5453
    return s - math.floor(s)


def wave_constants(P):
    """Lo mismo que waveConstants() del prototipo y que WaveConstants() del Blueprint."""
    W, V, E = [], [], []
    lmax = max(P["SwellLenMax"], 10.0)
    lmin = min(P["SwellLenMin"], lmax - 1.0)
    for i in range(NW):
        f = i / (NW - 1)
        lam = lmax * (lmin / lmax) ** f
        k = 2 * math.pi / lam
        ang = math.radians(P["SwellDir"] + P["SwellSpread"] * OFFS[i])
        d = (math.cos(ang), math.sin(ang))
        om = math.sqrt(981.0 * k) * P["Tempo"]
        A = P["SwellAmp"] * (lam / lmax) ** 0.6
        ph = 2 * math.pi * hash1(i + 1)
        cg = 0.5 * om / k
        ea = ang + (0.5 if i % 2 else -0.5)
        md = (math.cos(ea), math.sin(ea))
        W.append((d[0], d[1], k, om))
        V.append((A, ph, cg * (md[0] * d[0] + md[1] * d[1]), 2 * math.pi * hash1(i + 3)))
        E.append((md[0], md[1], lam * P["LodNear"], lam * max(P["LodFar"], P["LodNear"] + 1.0)))
    return W, V, E


def field(px, py, t, P, W, V, E):
    """h y grad(h) exactos, como SEA_VS del prototipo. px, py arrays (cm, locales)."""
    kw = TAU / P["WarpScale"]
    ax = py * kw + t * 0.071
    ay = px * kw * 1.31 + t * 0.053 + 1.7
    qx = px + P["Warp"] * np.sin(ax)
    qy = py + P["Warp"] * np.sin(ay)
    dwx_dy = P["Warp"] * kw * np.cos(ax)
    dwy_dx = P["Warp"] * kw * 1.31 * np.cos(ay)
    qax = qx + P["Advance"] * t
    qay = qy
    r = np.maximum(np.hypot(px, py), 1.0)
    kg = TAU / P["GroupLen"]
    S = np.zeros_like(px); gqx = np.zeros_like(px); gqy = np.zeros_like(px); gl = np.zeros_like(px)
    for i in range(NW):
        dx, dy, k, om = W[i]
        A, ph, vg, eph = V[i]
        mx, my, a0, a1 = E[i]
        ea = kg * (qax * mx + qay * my - vg * t) + eph
        m = 1 + P["GroupAmt"] * np.sin(ea)
        gmx = P["GroupAmt"] * np.cos(ea) * kg * mx
        gmy = P["GroupAmt"] * np.cos(ea) * kg * my
        x = np.clip((r - a0) / (a1 - a0), 0, 1)
        lod = 1 - x * x * (3 - 2 * x)
        dlod = -6 * x * (1 - x) / (a1 - a0)
        arg = k * (dx * qax + dy * qay) - om * t + ph
        s, c = np.sin(arg), np.cos(arg)
        S += A * lod * m * s
        gqx += A * lod * (m * k * c * dx + s * gmx)
        gqy += A * lod * (m * k * c * dy + s * gmy)
        gl += A * dlod * m * s
    gSx = gqx + dwy_dx * gqy + gl * px / r
    gSy = dwx_dy * gqx + gqy + gl * py / r
    xc = np.clip(r / P["CalmR"], 0, 1)
    fade = P["CalmMin"] + (1 - P["CalmMin"]) * xc * xc * (3 - 2 * xc)
    dfade = (1 - P["CalmMin"]) * 6 * xc * (1 - xc) / P["CalmR"]
    h = fade * S
    gx = fade * gSx + S * dfade * px / r
    gy = fade * gSy + S * dfade * py / r
    return h, gx, gy


def shade(h, gx, gy, vx, vy, vz, P, part=0):
    """Color lineal del PS (sin dither). v = WorldPosition - CameraPosition (cm)."""
    az, el = math.radians(P["LightAz"]), math.radians(P["LightEl"])
    L = np.array([math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)])
    dist = np.sqrt(vx * vx + vy * vy + vz * vz)

    def sky(dx, dy, dz):
        up = np.clip(dz, 0, 1)
        c = np.array(P["HorizonColor"])[:, None] * 1.0
        c = c + (np.array(P["ZenithColor"])[:, None] - c) * up ** P["SkyPow"]
        g = np.clip(dx * L[0] + dy * L[1] + dz * L[2], 0, 1) ** P["GlowPow"]
        return c + np.array(P["GlowColor"])[:, None] * P["GlowAmt"] * g

    if part == 1:
        return sky(vx / dist, vy / dist, vz / dist)
    n = np.sqrt(gx * gx + gy * gy + 1)
    nx, ny, nz = -gx / n, -gy / n, 1 / n
    diff = np.clip((nx * L[0] + ny * L[1] + nz * L[2]) * 0.5 + 0.5, 0, 1) ** P["WrapPow"]
    deep, surf = np.array(P["DeepColor"])[:, None], np.array(P["SurfColor"])[:, None]
    col = deep + (surf - deep) * diff
    crest = np.clip(h / (P["SwellAmp"] * 2) + 0.5, 0, 1)
    col = col + np.array(P["CrestColor"])[:, None] * P["CrestAmt"] * crest * crest
    fog = 1 - np.exp(-np.maximum(dist - P["FogStart"], 0) * P["FogDensity"])
    fx, fy = vx / dist, vy / dist
    fl = np.sqrt(fx * fx + fy * fy + 0.015 ** 2)
    col = col + (sky(fx / fl, fy / fl, 0.015 / fl) - col) * fog
    return col


def srgb_enc(c):
    c = np.maximum(c, 0.0)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)


def srgb_dec(s):
    return np.where(s <= 0.04045, s / 12.92, np.power((s + 0.055) / 1.055, 2.4))


def dust_ps(a, u, v, P):
    """Lo que SUMA una mota al fondo DustBG, como en el prototipo (suma en sRGB codificado). a = alpha del VS."""
    d = np.sqrt((u * 2 - 1) ** 2 + (v * 2 - 1) ** 2)
    t = np.clip((d - 0.35) / 0.65, 0, 1)
    k = P["DustAmt"] * a * (1 - t * t * (3 - 2 * t))
    c = np.array(P["DustColor"])[:, None] * k
    bg = np.array(P["DustBG"])[:, None] * np.ones_like(k)
    return np.maximum(srgb_dec(np.clip(srgb_enc(bg) + srgb_enc(c), 0, 1)) - bg, 0)


if __name__ == "__main__":
    W, V, E = wave_constants(DEF)
    print("Constantes por oleaje con los defaults aprobados (W = d.x, d.y, k, omega | V = A, fase, v_grupo, fase_grupo | E = dir_grupo.x, .y, LOD desde, LOD hasta):")
    for i in range(NW):
        print("W%d = (%.6f, %.6f, %.8f, %.6f)" % ((i,) + W[i]))
        print("V%d = (%.6f, %.6f, %.6f, %.6f)" % ((i,) + V[i]))
        print("E%d = (%.6f, %.6f, %.2f, %.2f)" % ((i,) + E[i]))
