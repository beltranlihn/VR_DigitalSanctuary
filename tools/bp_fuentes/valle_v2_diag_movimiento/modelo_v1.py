# -*- coding: utf-8 -*-
"""modelo_v1.py - modelo numpy VECTORIZADO de la altura del valle v1 (spec §3 y ValleyHeightVS.hlsl).

Solo lectura del codigo del repo: este archivo reescribe las formulas para poder evaluarlas sobre
millones de puntos. Se valida contra los valores de control de la §12 de la spec antes de usarlo
(control positivo: si no reproduce la tabla, ninguna medicion posterior vale).

Unidades: cm y s. Ejes UE: X adelante, Y derecha, Z arriba. Ojos en (0, 0, 120).
"""
import math

import numpy as np

# defaults de la §7.1 (lo que tiene la MI en Unreal: valley_build.json coincide)
P = dict(ValleyX=350.0, ValleyA=950.0, ValleyB=600.0, SeatIn=60.0, SeatOut=250.0,
         RimHeight=380.0, RimCrest=3.0, RimBack=4.0, DuneAmp=520.0, DuneRise=1.6,
         DuneLow=-0.35, DuneHigh=1.2, DuneScale=1.0, DuneSeed=0.0, DuneShiftX=0.0, DuneShiftY=0.0,
         MorphAmt=0.45, MorphSpeed=1.0, MorphNear=800.0, MorphFar=3000.0)

# dunas: (angulo deg, lambda cm, peso, fase rad, periodo s, fase temporal rad)  - spec §3.3
DUNAS = ((18.0, 3000.0, 1.00, 0.0, 53.0, 0.0),
         (101.0, 2200.0, 0.75, 1.7, 67.0, 2.1),
         (143.0, 1650.0, 0.55, 4.1, 41.0, 4.4),
         (232.0, 1250.0, 0.35, 2.9, 83.0, 1.3))
SUMA_A = 2.65
OJO_Z = 120.0


def ss(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def partes(x, y, q=None):
    """Todo lo que NO depende del tiempo. Devuelve un dict con B, env, S0, s_i, Mt, r.
    h(t) = B + DuneAmp * env * smoothstep(DuneLow, DuneHigh, S0 + Mt * sum_i m_i(t) * s_i)."""
    q = dict(P, **(q or {}))
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    r = np.sqrt(x * x + y * y)
    ex = (x - q["ValleyX"]) / max(q["ValleyA"], 1.0)
    ey = y / max(q["ValleyB"], 1.0)
    e = np.sqrt(ex * ex + ey * ey)
    E1 = max(q["RimCrest"], 1.01)
    E2 = max(q["RimBack"], E1 + 0.01)
    u2 = ss(E1, E2, e)
    B = q["RimHeight"] * ss(1.0, E1, e) * (1.0 - u2)
    Mt = q["MorphAmt"] * ss(q["MorphNear"], max(q["MorphFar"], q["MorphNear"] + 1.0), r)
    xd = x + q["DuneShiftX"]
    yd = y + q["DuneShiftY"]
    ks = 2.0 * math.pi / max(q["DuneScale"], 0.05)
    s = []
    for al, lam, a, ph, _, _ in DUNAS:
        ang = math.radians(q["DuneSeed"] + al)
        g = ks / lam * (math.cos(ang) * xd + math.sin(ang) * yd) + ph
        s.append(a * np.sin(g) / SUMA_A)
    S0 = s[0] + s[1] + s[2] + s[3]
    env = ss(1.0, max(q["DuneRise"], 1.01), e) * (1.0 - u2) * ss(q["SeatIn"], max(q["SeatOut"], q["SeatIn"] + 1.0), r)
    return dict(B=B, env=env, S0=S0, s=s, Mt=Mt, r=r, e=e, u2=u2, q=q)


def m_de_t(t, q=None):
    q = dict(P, **(q or {}))
    w = 2.0 * math.pi * q["MorphSpeed"] * t
    return [math.sin(w / T + ps) for (_, _, _, _, T, ps) in DUNAS]


def h_de(pt, t):
    """altura en t a partir de las partes precalculadas."""
    q = pt["q"]
    m = m_de_t(t, q)
    sig = pt["S0"] + pt["Mt"] * (m[0] * pt["s"][0] + m[1] * pt["s"][1] + m[2] * pt["s"][2] + m[3] * pt["s"][3])
    f = ss(q["DuneLow"], max(q["DuneHigh"], q["DuneLow"] + 0.01), sig)
    return pt["B"] + q["DuneAmp"] * pt["env"] * f


def h(x, y, t, q=None):
    return h_de(partes(x, y, q), t)


def grad_fd(x, y, t, q=None, d=0.5):
    hx = (h(x + d, y, t, q) - h(x - d, y, t, q)) / (2 * d)
    hy = (h(x, y + d, t, q) - h(x, y - d, t, q)) / (2 * d)
    return hx, hy


def radios_malla(dA=30.0, rmax=4400.0, S=192):
    """radios de SM_BreathValley_SC (spec §2 / gen_breath_valley.radios), en cm."""
    qg = 1.0 + 2.0 * math.pi / S
    ra = dA / (qg - 1.0)
    na = int(math.floor(ra / dA + 1e-9))
    rs = [dA * j for j in range(1, na + 1)]
    r = rs[-1]
    while True:
        r = r * qg
        if r >= rmax:
            break
        rs.append(r)
    if rmax - rs[-1] < 0.5 * rs[-1] * (qg - 1.0):
        rs[-1] = rmax
    else:
        rs.append(rmax)
    return np.array(rs)


def vertices_malla(S=192, **kw):
    rs = radios_malla(S=S, **kw)
    th = 2.0 * math.pi * np.arange(S) / S
    R, TH = np.meshgrid(rs, th, indexing="ij")
    x = np.concatenate([[0.0], (R * np.cos(TH)).ravel()])
    y = np.concatenate([[0.0], (R * np.sin(TH)).ravel()])
    return x, y, rs


# ---------------- sombreado del suelo (spec §4, sin sombra del metaball: esta lejos) ----------------
def D(az, el):
    az, el = math.radians(az), math.radians(el)
    return np.array([math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)])


LOOK = dict(LightDir=D(20, 25), Wrap=0.3, ShadeFloor=0.0, SlopeDark=1.2,
            ColLit=np.array([0.434, 0.527, 0.855]), ColShadow=np.array([0.061, 0.117, 0.352]),
            ColSheen=np.array([0.855, 0.761, 0.913]), Sheen=0.4, SheenPow=4.0, SheenBack=0.35, CrestLight=0.2,
            SkyZenith=np.array([0.216, 0.328, 0.597]), SkyHorizon=np.array([0.597, 0.624, 0.839]),
            SkyGlow=np.array([0.831, 0.68, 0.855]), SkyGradTop=0.7, GlowDir=D(20, 2), GlowPow=2.0,
            GlowHeight=0.45, GlowAmt=0.8, FogStart=1000.0, FogDist=5000.0, FogMax=0.6)


def color_suelo(x, y, hh, hx, hy, hf, ojo=(0.0, 0.0, OJO_Z), L=LOOK):
    """ValleyPS Part 0 vectorizado (sin dither ni sombra). Devuelve color lineal (N,3)."""
    x, y, hh, hx, hy, hf = (np.asarray(a, dtype=np.float64) for a in (x, y, hh, hx, hy, hf))
    cam = np.asarray(ojo, dtype=np.float64)
    P3 = np.stack([x, y, hh], -1)
    CamL = cam - P3
    Dist = np.linalg.norm(CamL, axis=-1)
    V = CamL / Dist[:, None]
    dv = -V
    N = np.stack([-hx, -hy, np.ones_like(hx)], -1)
    N /= np.linalg.norm(N, axis=-1)[:, None]
    Ld = L["LightDir"]
    wrap = np.clip((N @ Ld + L["Wrap"]) / (1 + L["Wrap"]), 0, 1)
    k = (L["ShadeFloor"] + (1 - L["ShadeFloor"]) * wrap) * np.clip(1 - L["SlopeDark"] * (1 - N[:, 2]), 0, 1)
    col = L["ColShadow"] + (L["ColLit"] - L["ColShadow"]) * k[:, None]
    col = col + (L["ColLit"] - col) * (L["CrestLight"] * hf * hf)[:, None]
    fres = np.power(np.maximum(1 - np.clip(np.sum(N * V, -1), 0, 1), 1e-6), L["SheenPow"])
    fwd = np.clip(0.5 + 0.5 * (dv @ Ld), 0, 1)
    a = np.clip(L["Sheen"] * fres * (L["SheenBack"] + (1 - L["SheenBack"]) * fwd), 0, 1)
    col = col + (L["ColSheen"] - col) * a[:, None]
    sky = L["SkyHorizon"] + (L["SkyZenith"] - L["SkyHorizon"]) * ss(0.0, L["SkyGradTop"], dv[:, 2])[:, None]
    hz = dv[:, :2] / np.maximum(np.linalg.norm(dv[:, :2], axis=-1), 1e-4)[:, None]
    gh = L["GlowDir"][:2] / np.linalg.norm(L["GlowDir"][:2])
    gaz = np.power(np.maximum(hz @ gh, 1e-6), L["GlowPow"])
    gel = 1 - ss(0.0, L["GlowHeight"], np.abs(dv[:, 2] - L["GlowDir"][2]))
    sky = sky + (L["SkyGlow"] - sky) * np.clip(L["GlowAmt"] * gaz * gel, 0, 1)[:, None]
    fog = L["FogMax"] * (1 - np.exp(-np.maximum(Dist - L["FogStart"], 0) / L["FogDist"]))
    return col + (sky - col) * fog[:, None]


def srgb8(c):
    c = np.clip(c, 0, 1)
    return 255.0 * np.where(c <= 0.0031308, 12.92 * c, 1.055 * np.power(c, 1 / 2.4) - 0.055)


# ---------------- control positivo contra la §12 de la spec ----------------
CONTROL_H = [((0, 0), 0, 0.000, 0.0, 0.0, 0.0), ((380, 0), 0, 0.000, 0.0, 0.0, 0.0),
             ((900, -700), 0, 89.005, 0.187877, -0.337869, 0.126090),
             ((1500, 800), 0, 280.513, -0.146126, -0.204076, 0.281756),
             ((2200, -1500), 20, 481.552, -0.912999, 0.638918, 0.250821),
             ((3200, 0), 45.5, 460.192, -0.050322, 0.369692, 0.154215),
             ((-1800, 1200), 90, 383.565, -0.033267, 0.083878, 0.007741),
             ((2600, 2600), 300, 0.000, 0.0, 0.0, 0.0)]


def control():
    peor_h = peor_g = 0.0
    for (x, y), t, hh, gx, gy, _ in CONTROL_H:
        v = float(h(np.array([x], float), np.array([y], float), t)[0])
        fx, fy = grad_fd(np.array([x], float), np.array([y], float), t, d=0.01)
        peor_h = max(peor_h, abs(v - hh))
        peor_g = max(peor_g, abs(float(fx[0]) - gx), abs(float(fy[0]) - gy))
    ok = peor_h < 0.002 and peor_g < 1e-4
    print("CONTROL §12: max |dh| = %.2e cm, max |dgrad| = %.2e -> %s" % (peor_h, peor_g, "OK" if ok else "FALLA"))
    return ok


if __name__ == "__main__":
    control()
    x, y, rs = vertices_malla()
    print("malla: %d anillos, %d vertices" % (len(rs), len(x)))
