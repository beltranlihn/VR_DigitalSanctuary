# -*- coding: utf-8 -*-
"""transicion.py - la "linea donde se acaba el plano" sobre la ESCALA GRANDE (candidato v2 de la tarea de escala,
valle_v2_diag_escala/modelo_valle.py, que se importa SOLO PARA LEER) y la ley de transicion propuesta.

Geometrias (todas con las capas y los numeros de P2; solo cambia el PASO y los anchos):
  E0  P2 tal cual: smoothstep (C1) en todas las envolventes y umbrales.
  E1  P2 con S5 (quintica, C2) en lugar de smoothstep. Mismos anchos.
  E2  E1 + la ley de transicion (anchos y alturas de la llanura, pie de las colinas medias; ver LEY).
Sombreados:
  SH0 el de la spec (ValleyPS).
  SH1 brillo rasante con lobulo de tope plano en N.V = 0 (sin ganancia en el rasante): fres = exp(-(N.V/SheenW)^2).
Metrica (perfil vertical desde los ojos (0, 0, 120), por azimut; luminancia Y lineal contra la elevacion de la
mirada; solo el tramo CONECTADO al piso, hasta la primera silueta):
  G = max |d ln Y/d el| (%/grado, ventanas de 0,25 grados) y Q = quiebre = max cambio de G entre ventanas vecinas.
  Se informa donde cae Q (distancia y elevacion).
Uso: python transicion.py [render]
"""
import math
import os
import sys

import numpy as np
from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
ESC = os.path.join(os.path.dirname(AQUI), "valle_v2_diag_escala")
sys.path.insert(0, ESC)
import modelo_valle as mv  # noqa: E402  (solo lectura)

EYE = np.array([0.0, 0.0, 120.0])
L0 = dict(mv.LOOK)


def ss3(a, b, x):
    t = np.clip((np.asarray(x, float) - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def s5(a, b, x):
    t = np.clip((np.asarray(x, float) - a) / (b - a), 0.0, 1.0)
    return t * t * t * (10.0 + t * (6.0 * t - 15.0))


# ---------------------------------------------------------------------------------------------- altura
def h_capas(x, y, t, P, st):
    """Las capas de P2 (llanura, colinas medias, anillo y colinas lejanas) con el paso st (ss3 o s5)."""
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    r = np.hypot(x, y)
    e = np.hypot((x - P["ValleyX"]) / P["ValleyA"], y / P["ValleyB"])
    # llanura: arranca en e = 1 (borde del piso quieto)
    envP = st(1.0, P["PlainRise"], e) * (1.0 - st(P["PlainFade0"], P["PlainFade1"], r))
    sigP = mv.sigma(x, y, t, P["PlainScale"], P["PlainSeed"], 0.0, 0.0, 0.0, 0.0)
    h = P["PlainAmp"] * envP * sigP
    # colinas medias
    envM = st(P["MidIn0"], P["MidIn1"], r) * (1.0 - st(P["MidOut0"], P["MidOut1"], r))
    sigM = mv.sigma(x, y, t, P["MidScale"], P["MidSeed"], 0.0, 0.0, P["MorphAmt"], P["MorphSpeed"])
    fM = st(P["MidLow"], P["MidHigh"], sigM)
    h = h + P["MidAmp"] * envM * fM
    # anillo + colinas lejanas
    back = 1.0 - st(P["FarCrest"], P["FarBack"], r)
    ring = P["FarBase"] * st(P["FarIn0"], P["FarCrest"], r) * back
    envF = st(P["FarIn0"], P["FarIn1"], r) * back
    sigF = mv.sigma(x, y, t, P["FarScale"], P["FarSeed"], 0.0, 0.0, P["MorphAmt"], P["MorphSpeed"])
    fF = st(P["FarLow"], P["FarHigh"], sigF)
    h = h + ring + P["FarAmp"] * envF * fF
    if P.get("SwellAmp", 0.0) > 0.0:
        h = h + oleaje(x, y, t, P, st, r, back)
    return h, np.clip(envM * fM + envF * fF, 0.0, 1.0)


def oleaje(x, y, t, P, st, r, back):
    """Port de la propuesta de la tarea de movimiento (valle_v2_diag_movimiento/ValleyHeightVS_oleaje.hlsl),
    SwellSeed 0. El paso de su envolvente se toma con st (ss3 como la escribio esa tarea, o s5)."""
    Wq = st(P["SwellNear"], P["SwellFar"], r)
    A = P["SwellAmp"] * Wq * back
    kq = 2.0 * math.pi / P["SwellScale"]
    ondas = ((9000.0, 0.93969262, 0.34202014, 0.0, 42.0, 1.00), (7000.0, -0.99619470, 0.08715574, 2.3, 36.0, 0.85),
             (5500.0, -0.25881905, -0.96592583, 4.6, 31.0, 0.70), (4000.0, -0.08715574, 0.99619470, 1.1, 46.0, 0.40))
    acc = 0.0
    for lam, dx, dy, ph, T, wgt in ondas:
        o = kq / lam * (dx * x + dy * y) + ph - 2.0 * math.pi * ((P["SwellSpeed"] * t / T) % 1.0)
        acc = acc + wgt * np.sin(o)
    return A * acc / 2.95


# ---------------------------------------------------------------------------------------------- sombreado
def suelo(px, py, h, gx, gy, hf, P, L, sheen_mode, fogfun, cam=EYE):
    pos = np.stack([px, py, h], -1)
    cv = np.asarray(cam, float) - pos
    Dist = np.sqrt((cv * cv).sum(-1))
    V = cv / Dist[..., None]
    dv = -V
    Ld = mv.dir_d(L["LightAz"], L["LightEl"])
    N = np.stack([-gx, -gy, np.ones_like(gx)], -1)
    N = N / np.sqrt((N * N).sum(-1))[..., None]
    wrap = mv.sat(((N * Ld).sum(-1) + L["Wrap"]) / (1.0 + L["Wrap"]))
    k = mv.lerp(L["ShadeFloor"], 1.0, wrap) * mv.sat(1.0 - L["SlopeDark"] * (1.0 - N[..., 2]))
    col = mv.lerp(mv._v3(L["ColShadow"]), mv._v3(L["ColLit"]), k[..., None])
    col = mv.lerp(col, mv._v3(L["ColLit"]), (L["CrestLight"] * hf * hf)[..., None])
    nv = mv.sat((N * V).sum(-1))
    if sheen_mode == 0:
        fres = np.power(np.maximum(1.0 - nv, 1e-6), L["SheenPow"])
    else:
        fres = np.exp(-(nv / L["SheenW"]) ** L.get("SheenP", 2.0))
    fwd = mv.sat(0.5 + 0.5 * (dv * Ld).sum(-1))
    col = mv.lerp(col, mv._v3(L["ColSheen"]), mv.sat(L["Sheen"] * fres * mv.lerp(L["SheenBack"], 1.0, fwd))[..., None])
    SC = mv._v3(L["ShadowCenter"])
    Hs = np.maximum(SC[2] - h, 1.0)
    Rs = L["ShadowRadius"]
    peak = L["ShadowStrength"] * Rs * Rs / (Rs * Rs + Hs * Hs)
    ws = np.maximum(L["ShadowSoft"] * Hs, 1.0)
    qs = 1.0 + ((px - SC[0]) ** 2 + (py - SC[1]) ** 2) / (ws * ws)
    O = np.minimum(mv.sat(peak * qs ** -1.5), L["ShadowMax"])
    col = col * (1.0 - O[..., None] * (1.0 - mv._v3(L["ShadowTint"])))
    fog = fogfun(Dist, h, float(np.asarray(cam)[2]), P)
    sky = mv.sky_color(dv, L, moon=False)
    return mv.lerp(col, sky, fog[..., None])


# ---------------------------------------------------------------------------------------------- variantes
P2 = dict(mv.P2)
# LEY (E2): la llanura entra como un oleaje que CRECE con la distancia, no como un borde:
#   ancho de la entrada >= 2 veces su distancia al usuario (e de 1 a 3: 19 -> 49 m al frente, 12,5 -> 37,5 m al
#   costado); el pie de las colinas medias arranca antes y mas ancho (45 -> 120 m) para que no haya un
#   contorno cerrado donde "cambia el regimen".
P2_LEY = dict(P2, PlainRise=3.0, MidIn0=4500.0, MidIn1=12000.0)
OLEAJE = dict(SwellAmp=600.0, SwellNear=1500.0, SwellFar=15000.0, SwellScale=1.0, SwellSpeed=1.0)
P2_LEY_OL = dict(P2_LEY, **OLEAJE)
L_SH1 = dict(L0, SheenW=0.35)
P1 = dict(mv.P1)


def V(hfun, P, fogfun, L, sm):
    return dict(hfun=hfun, P=P, fog=fogfun, L=L, sm=sm)


VARS = {
    "V1_spec": V(lambda x, y, t: mv.h_v1(x, y, t, P1), P1, mv.fog_v1, L0, 0),
    "E0_C1": V(lambda x, y, t: h_capas(x, y, t, P2, ss3), P2, mv.fog_v2, L0, 0),
    "E1_C2": V(lambda x, y, t: h_capas(x, y, t, P2, s5), P2, mv.fog_v2, L0, 0),
    "E2_ley": V(lambda x, y, t: h_capas(x, y, t, P2_LEY, s5), P2_LEY, mv.fog_v2, L0, 0),
    "E2_ley_SH1": V(lambda x, y, t: h_capas(x, y, t, P2_LEY, s5), P2_LEY, mv.fog_v2, L_SH1, 1),
    "E0_C1_SH1": V(lambda x, y, t: h_capas(x, y, t, P2, ss3), P2, mv.fog_v2, L_SH1, 1),
    "E2_ley_oleaje": V(lambda x, y, t: h_capas(x, y, t, P2_LEY_OL, s5), P2_LEY_OL, mv.fog_v2, L0, 0),
    "E2_ley_oleaje_SH1": V(lambda x, y, t: h_capas(x, y, t, P2_LEY_OL, s5), P2_LEY_OL, mv.fog_v2, L_SH1, 1),
}


def columna(v, az_deg, t=0.0, J=9000, rho0=100.0):
    P, hfun = v["P"], v["hfun"]
    a = math.radians(az_deg)
    rho = rho0 * np.power(P["R_MAX"] / rho0, np.arange(J) / (J - 1.0))
    x, y = rho * math.cos(a), rho * math.sin(a)
    h, hf = hfun(x, y, t)
    d = 0.5
    gx = (hfun(x + d, y, t)[0] - hfun(x - d, y, t)[0]) / (2 * d)
    gy = (hfun(x, y + d, t)[0] - hfun(x, y - d, t)[0]) / (2 * d)
    col = suelo(x, y, h, gx, gy, hf, P, v["L"], v["sm"], v["fog"])
    el = np.degrees(np.arctan2(h - EYE[2], rho))
    return rho, h, el, mv.lum(col), gx * math.cos(a) + gy * math.sin(a)


def metrica(rho, el, Y, dth=0.02, win=0.25):
    """Tramo conectado al piso: mientras la elevacion crezca (sin oclusion)."""
    j = 1
    while j < el.size and el[j] > el[j - 1]:
        j += 1
    e, yy, rr = el[:j], Y[:j], rho[:j]
    th = np.arange(max(e.min(), -25.0) + 0.3, e.max() - 0.05, dth)
    if th.size < 40:
        return 0.0, 0.0, 0.0, 0.0, e.max(), rr[-1]
    lY = np.log(np.interp(th, e, yy))
    dl = np.gradient(lY, dth) * 100.0
    w = int(round(win / dth))
    c = np.convolve(dl, np.ones(w) / w, mode="valid")
    tc = th[w // 2: w // 2 + c.size]
    q = np.abs(c[w:] - c[:-w])
    k = int(np.argmax(q))
    kq_th = tc[k + w // 2] if k + w // 2 < tc.size else tc[-1]
    kq_rho = np.interp(kq_th, e, rr)
    return np.abs(c).max(), q.max(), kq_th, kq_rho, e.max(), rr[-1]


def d_borde(P, az_deg):
    a = math.radians(az_deg)
    c, sn = math.cos(a), math.sin(a)
    # rayo horizontal desde el origen: ((s c - X)/A)^2 + (s sn/B)^2 = 1, raiz positiva
    A, B, X = P["ValleyA"], P["ValleyB"], P["ValleyX"]
    qa = (c / A) ** 2 + (sn / B) ** 2
    qb = -2.0 * X * c / A ** 2
    qc = (X / A) ** 2 - 1.0
    return (-qb + math.sqrt(qb * qb - 4 * qa * qc)) / (2 * qa)


def metrica_borde(P, rho, el, Y, az):
    """G y Q solo entre 0,6 y 2,5 veces la distancia al borde e = 1 (y antes de la primera silueta)."""
    db = d_borde(P, az)
    j = 1
    while j < el.size and el[j] > el[j - 1]:
        j += 1
    m = (rho[:j] >= 0.6 * db) & (rho[:j] <= 2.5 * db)
    if m.sum() < 20:
        return 0.0, 0.0, db
    G, Q, _, _, _, _ = metrica(rho[:j][m], el[:j][m], Y[:j][m])
    return G, Q, db


def main(render=False):
    lines = []
    azs = list(range(-60, 61, 10)) + [80, 90, 100, 180]
    lines.append("Metrica: G = rampa max, Q = quiebre max (%/grado); 'donde' = elevacion (grados) y distancia (m) del quiebre;")
    lines.append("'fin' = elevacion y distancia donde termina el tramo conectado al piso (primera silueta).")
    for nombre, v in VARS.items():
        P = v["P"]
        Gs, Qs, GBs, QBs, rows = [], [], [], [], []
        for az in azs:
            rho, h, el, Y, sl = columna(v, az)
            G, Q, qth, qrho, efin, rfin = metrica(rho, el, Y)
            Gb, Qb, db = metrica_borde(P, rho, el, Y, az)
            Gs.append(G)
            Qs.append(Q)
            GBs.append(Gb)
            QBs.append(Qb)
            rows.append("az%+4d: BORDE (%4.1f m) G %5.1f Q %5.1f || tramo: G %5.1f Q %5.1f en %+5.2f deg / %5.0f m"
                        " (fin %+5.2f deg, %4.0f m)" % (az, db / 100, Gb, Qb, G, Q, qth, qrho / 100, efin, rfin / 100))
        lines.append("%-16s BORDE: G max %5.1f med %5.1f  Q max %5.1f med %5.1f || TRAMO: G max %5.1f med %5.1f"
                     "  Q max %5.1f med %5.1f" % (nombre, max(GBs), np.median(GBs), max(QBs), np.median(QBs),
                                                 max(Gs), np.median(Gs), max(Qs), np.median(Qs)))
        for r in rows:
            lines.append("      " + r)
    txt = "\n".join(lines)
    print(txt)
    with open(os.path.join(AQUI, "transicion_salida.txt"), "w", encoding="utf-8") as fh:
        fh.write(txt + "\n")


if __name__ == "__main__":
    main(render="render" in sys.argv)
