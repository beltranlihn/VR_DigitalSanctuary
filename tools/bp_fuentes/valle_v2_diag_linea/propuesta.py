# -*- coding: utf-8 -*-
"""propuesta.py - mide la "linea del borde del piso" en v1 y en las alternativas, con la MISMA metrica,
desde los ojos del usuario (0, 0, 120), HFOV 90, a la resolucion angular del visor.

Variantes:
  v1         el valle actual (defaults de la spec).
  v1_C2      v1 con TODOS los smoothstep de la altura cambiados por S5 (quintica, C2). Misma escala.
             Aisla el efecto de la continuidad.
  v1_x3      v1 con todas las distancias x3 (escala sola, sin tocar la forma). Aisla el efecto de la escala.
  v2         la propuesta: claro circular plano + CUENCO C2 ancho + dunas C2 lejos + niebla + sheen
             con compuerta de pendiente. Escala grande.
  v2_sinGate v2 sin la compuerta del sheen (para ver cuanto aporta cada parte).

Metrica (por columna, perfil vertical de luminancia Y lineal, angulo th en grados):
  se toma el tramo CONECTADO al piso: desde abajo hasta el primer salto de distancia > 15 % entre
  muestras (una silueta, que es otra cosa). En ese tramo:
    G = max |d ln Y / d th|           (% por grado)   rampa de luminancia
    Q = max | pendiente media en [th, th+0.25] - en [th-0.25, th] |  (% por grado)  QUIEBRE (banda de Mach)
  Muestreo 0,02 grados; Q con ventanas de 0,25 grados (~5 px del visor).
Salidas: propuesta_salida.txt (via tee) y render_<variante>_<vista>.png (1/2 res, 526x431).
Uso: python propuesta.py [render]
"""
import math
import os
import sys

import numpy as np
from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import modelo_v1 as M  # noqa: E402

DUNAS = M.DUNAS


def sat(x):
    return np.clip(x, 0.0, 1.0)


def st3(a, b, x):  # smoothstep (C1) y su derivada
    t = sat((x - a) / (b - a))
    return t * t * (3 - 2 * t), 6 * t * (1 - t) / (b - a)


def st5(a, b, x):  # S5 = t^3 (10 - 15 t + 6 t^2) (C2) y su derivada 30 t^2 (1 - t)^2
    t = sat((x - a) / (b - a))
    return t * t * t * (10 + t * (6 * t - 15)), 30 * t * t * (1 - t) * (1 - t) / (b - a)


# ------------------------------------------------------------------ v1 generalizado (paso C1 o C2)
def campo_v1(x, y, t, p, st):
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    r = np.sqrt(x * x + y * y)
    rs = np.maximum(r, 1.0)
    VA, VB = p["ValleyA"], p["ValleyB"]
    ex, ey = (x - p["ValleyX"]) / VA, y / VB
    e = np.sqrt(ex * ex + ey * ey)
    es = np.maximum(e, 1e-4)
    dex, dey = ex / (VA * es), ey / (VB * es)
    E1, E2 = p["RimCrest"], p["RimBack"]
    u1, du1 = st(1.0, E1, e)
    u2, du2 = st(E1, E2, e)
    B = p["RimHeight"] * u1 * (1 - u2)
    dB = p["RimHeight"] * (du1 * (1 - u2) - u1 * du2)
    Mt, dMt = st(p["MorphNear"], p["MorphFar"], r)
    Mt, dMt = p["MorphAmt"] * Mt, p["MorphAmt"] * dMt
    sig, sm, gsx, gsy = campo_sigma(x, y, t, p, Mt)
    gsx = gsx + dMt * sm * x / rs
    gsy = gsy + dMt * sm * y / rs
    f, df = st(p["DuneLow"], p["DuneHigh"], sig)
    seat, dseat = st(p["SeatIn"], p["SeatOut"], r)
    Ea, dEa = st(1.0, p["DuneRise"], e)
    envE = Ea * (1 - u2)
    denvE = dEa * (1 - u2) - Ea * du2
    env = envE * seat
    h = B + p["DuneAmp"] * env * f
    gex = seat * denvE * dex + envE * dseat * x / rs
    gey = seat * denvE * dey + envE * dseat * y / rs
    gx = dB * dex + p["DuneAmp"] * (gex * f + env * df * gsx)
    gy = dB * dey + p["DuneAmp"] * (gey * f + env * df * gsy)
    return h, gx, gy, env * f, dict(e=e, f=f, env=env)


def campo_sigma(x, y, t, p, Mt):
    w = 2 * math.pi * p["MorphSpeed"] * t
    xd, yd = x + p["DuneShiftX"], y + p["DuneShiftY"]
    ks = 2 * math.pi / p["DuneScale"]
    sig = sm = gsx = gsy = 0.0
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
    return sig, sm, gsx, gsy


# ------------------------------------------------------------------ v2 (la propuesta)
def campo_v2(x, y, t, p):
    """Claro plano circular + cuenco C2 + dunas C2 que nacen lejos + retiro C2 antes del borde de la malla.
    Todo con S5. h = BowlH*Sb(rho) + DuneAmp*Ed(rho)*Kb(rho)*F(sigma)."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    dx, dy = x - p["CalmX"], y
    rho = np.sqrt(dx * dx + dy * dy)
    rs = np.maximum(rho, 1.0)
    nx, ny = dx / rs, dy / rs
    Sb, dSb = st5(p["CalmR"], p["CalmR"] + p["BowlW"], rho)
    Ed, dEd = st5(p["DuneIn"], p["DuneIn"] + p["DuneW"], rho)
    Kt, dKt = st5(p["BackIn"], p["BackIn"] + p["BackW"], rho)
    Kb, dKb = 1 - Kt, -dKt
    env = Ed * Kb
    denv = dEd * Kb + Ed * dKb
    r = np.sqrt(x * x + y * y)
    rr = np.maximum(r, 1.0)
    Mt, dMt = st5(p["MorphNear"], p["MorphFar"], r)
    Mt, dMt = p["MorphAmt"] * Mt, p["MorphAmt"] * dMt
    sig, sm, gsx, gsy = campo_sigma(x, y, t, p, Mt)
    gsx = gsx + dMt * sm * x / rr
    gsy = gsy + dMt * sm * y / rr
    F, dF = st5(p["DuneLow"], p["DuneHigh"], sig)
    h = p["BowlH"] * Sb + p["DuneAmp"] * env * F
    gx = p["BowlH"] * dSb * nx + p["DuneAmp"] * (denv * nx * F + env * dF * gsx)
    gy = p["BowlH"] * dSb * ny + p["DuneAmp"] * (denv * ny * F + env * dF * gsy)
    return h, gx, gy, env * F, dict(e=rho / p["CalmR"], f=F, env=env)


# ------------------------------------------------------------------ sombreado (ValleyPS + compuerta opcional del sheen)
def suelo(hit, gx, gy, h, hf, cam, p):
    L = M.D(p["LightAz"], p["LightEl"])
    d = cam - hit
    Dist = np.linalg.norm(d, axis=-1)
    V = d / Dist[..., None]
    dv = -V
    N = np.stack([-gx, -gy, np.ones_like(gx)], -1)
    N = N / np.linalg.norm(N, axis=-1)[..., None]
    wrap = sat(((N * L).sum(-1) + p["Wrap"]) / (1 + p["Wrap"]))
    k = wrap * sat(1 - p["SlopeDark"] * (1 - N[..., 2]))
    CL, CS, CH = (np.array(p[c]) for c in ("ColLit", "ColShadow", "ColSheen"))
    col = CS + (CL - CS) * k[..., None]
    col = col + (CL - col) * (p["CrestLight"] * hf * hf)[..., None]
    fres = np.power(np.maximum(1 - sat((N * V).sum(-1)), 1e-6), p["SheenPow"])
    fwd = sat(0.5 + 0.5 * (dv * L).sum(-1))
    sh = sat(p["Sheen"] * fres * (p["SheenBack"] + (1 - p["SheenBack"]) * fwd))
    if p.get("SheenGate", 0.0) > 0:
        # el brillo rasante solo donde el suelo se INCLINA: en el piso plano no hay "rasante" que encender.
        # S5 de (1 - N.z) de 0 a SheenGate (1 - cos 20 grados = 0.06): C2 en N -> C1 en pantalla con normal C1.
        g5, _ = st5(0.0, p["SheenGate"], 1 - N[..., 2])
        sh = sh * (p.get("SheenFlat", 0.0) + (1 - p.get("SheenFlat", 0.0)) * g5)
    col = col + (CH - col) * sh[..., None]
    SC = np.array(p["ShadowCenter"])
    Hs = np.maximum(SC[2] - h, 1.0)
    Rs = p["ShadowRadius"]
    peak = p["ShadowStrength"] * Rs * Rs / (Rs * Rs + Hs * Hs)
    ws = np.maximum(p["ShadowSoft"] * Hs, 1.0)
    qs = 1 + ((hit[..., 0] - SC[0]) ** 2 + (hit[..., 1] - SC[1]) ** 2) / (ws * ws)
    O = np.minimum(sat(peak * qs ** -1.5), p["ShadowMax"])
    col = col * (1 - O[..., None] * (1 - np.array(p["ShadowTint"])))
    wd = np.maximum(Dist - p["FogStart"], 0)
    if p.get("FogSoft", 0.0) > 0:
        # arranque C1 de la niebla: v = w^2/(w + 2K) (v = 0 y v' = 0 en w = 0; lejos v ~ w - 2K)
        wd = wd * wd / (wd + 2 * p["FogSoft"])
    fog = p["FogMax"] * (1 - np.exp(-wd / p["FogDist"]))
    sky = M.cielo(dv, p)
    return col + (sky - col) * fog[..., None]


# ------------------------------------------------------------------ variantes
BASE = dict(M.P)
V1 = dict(BASE, kind="v1", st=st3)
V1_C2 = dict(BASE, kind="v1", st=st5)
V1_X3 = dict(BASE, kind="v1", st=st3)
for k in ("ValleyX", "ValleyA", "ValleyB", "DuneAmp", "RimHeight", "DuneScale", "MorphNear", "MorphFar",
          "FogStart", "FogDist", "R_MAX"):
    V1_X3[k] = BASE[k] * 3.0
V2 = dict(BASE, kind="v2",
          CalmX=190.0, CalmR=1200.0,            # claro plano: 10,1 m libres alrededor del usuario y del metaball
          BowlW=6000.0, BowlH=700.0,            # cuenco: sube 7 m entre 12 y 72 m; pendiente max 12,5 grados
          DuneIn=3000.0, DuneW=6000.0,          # dunas: nacen a 30 m, plenas a 90 m
          DuneAmp=1200.0, DuneScale=4.0,        # lomas de 12 m, longitudes de onda 50-120 m
          BackIn=24000.0, BackW=5000.0,         # retiro de las dunas antes del borde (R_MAX 30000)
          MorphNear=2500.0, MorphFar=9000.0,
          FogStart=1200.0, FogDist=8000.0, FogMax=0.85,
          SheenGate=0.06, SheenFlat=0.0, R_MAX=30000.0)
V2_SINGATE = dict(V2, SheenGate=0.0)
VARS = {"v1": V1, "v1_C2": V1_C2, "v1_x3": V1_X3, "v2": V2, "v2_sinGate": V2_SINGATE}


def campo(p, t):
    if p["kind"] == "v1":
        return lambda x, y: campo_v1(x, y, t, p, p["st"])
    return lambda x, y: campo_v2(x, y, t, p)


def trazar(p, o, dirs, t=0.0):
    cf = campo(p, t)
    shp = dirs.shape[:-1]
    d = dirs.reshape(-1, 3)
    smax = max(20000.0, 1.3 * p["R_MAX"])
    s = M.raycast(o, d, t, p, hfn=lambda x, y: cf(x, y)[0], smax=smax, zmax=6000.0, rmax=p["R_MAX"])
    hit = ~np.isnan(s)
    col = M.cielo_luna(d, p)
    dist = np.full(d.shape[0], np.nan)
    if hit.any():
        hp = o + d[hit] * s[hit][:, None]
        h, gx, gy, hf, _ = cf(hp[:, 0], hp[:, 1])
        hp[:, 2] = h
        col[hit] = suelo(hp, gx, gy, h, hf, o, p)
        dist[hit] = np.linalg.norm(hp - o, axis=-1)
    return col.reshape(shp + (3,)), dist.reshape(shp), hit.reshape(shp)


def metricas(p, yaw, o=np.array([0.0, 0.0, 120.0]), azs=None, t=0.0):
    """Perfil vertical fino en varias columnas (azimut relativo -40..40)."""
    azs = np.arange(-40, 41, 8) if azs is None else azs
    th = np.arange(-30.0, 8.0, 0.02)
    res = []
    for a in azs:
        az = math.radians(yaw + a)
        el = np.radians(th)
        d = np.stack([np.cos(el) * math.cos(az), np.cos(el) * math.sin(az), np.sin(el)], -1)
        col, dist, hit = trazar(p, o, d, t)
        Y = M.luma(col)
        # tramo conectado al piso: desde abajo hasta la primera silueta (salto de distancia > 15 %) o el cielo
        j = 0
        while j + 1 < len(th) and hit[j + 1] and abs(dist[j + 1] - dist[j]) < 0.15 * dist[j]:
            j += 1
        seg = slice(0, j + 1)
        lY = np.log(Y[seg])
        dl = np.gradient(lY, 0.02) * 100.0                       # % por grado
        w = int(round(0.25 / 0.02))
        c = np.convolve(dl, np.ones(w) / w, mode="valid")        # pendiente media en ventanas de 0,25 grados
        Q = np.abs(c[w:] - c[:-w]).max() if c.size > w else 0.0
        kq = int(np.argmax(np.abs(c[w:] - c[:-w]))) + w if c.size > w else 0
        G = np.abs(c).max() if c.size else 0.0
        res.append((a, G, Q, th[min(kq, j)], dist[min(kq, j)], th[j]))
    return res


def main(render=False):
    vistas = (("frente", 0.0), ("costado", 90.0))
    print("Metrica: G = rampa max (%/grado), Q = quiebre max (%/grado de cambio de rampa en 0,25 grados).")
    print("Tramo medido: del suelo bajo los pies hasta la primera silueta (no se mide la silueta).")
    resumen = {}
    for nombre, p in VARS.items():
        for vn, yaw in vistas:
            r = metricas(p, yaw)
            a = np.array([[x[1], x[2]] for x in r])
            resumen[(nombre, vn)] = (a[:, 0].max(), np.median(a[:, 0]), a[:, 1].max(), np.median(a[:, 1]))
            print("%-11s %-8s  G max %6.1f  mediana %6.1f   |  Q max %6.1f  mediana %6.1f   (%s)" % (
                nombre, vn, a[:, 0].max(), np.median(a[:, 0]), a[:, 1].max(), np.median(a[:, 1]),
                "; ".join("az%+d: Q %.0f en %.1f deg/%.0f m" % (x[0], x[2], x[3], x[4] / 100) for x in r[::2])))
    if render:
        o = np.array([0.0, 0.0, 120.0])
        W, H = 526, 431
        for nombre in ("v1", "v1_C2", "v1_x3", "v2"):
            p = VARS[nombre]
            for vn, yaw in vistas:
                d = M.rayos(yaw, -2.0, W, H, 90.0)
                col, _, _ = trazar(p, o, d)
                Image.fromarray(np.round(M.srgb(col) * 255).astype(np.uint8)).save(
                    os.path.join(AQUI, "render_%s_%s.png" % (nombre, vn)))
                print("render_%s_%s.png" % (nombre, vn))


if __name__ == "__main__":
    main(render="render" in sys.argv)
