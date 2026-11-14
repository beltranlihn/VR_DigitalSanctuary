# -*- coding: utf-8 -*-
"""diag_escala.py - mide la ESCALA percibida del valle v1 y del candidato v2 (modelo_valle.py).

Metricas, todas desde los ojos del usuario (0, 0, 120) cm:
  - silueta por azimut (720 azimuts x 13 instantes en 10 min): elevacion, distancia, altura.
  - base de las colinas: primer punto con h > 20 cm; su DECLINACION bajo el horizonte (Ooi, Wu y He 2001).
  - razon de horizonte: alto de la silueta / alto de ojos (Sedgwick; Wraga 1999).
  - disparidad estereo contra el infinito (IPD 6,3 cm) y paralaje por un balanceo de cabeza de 5 cm, en PIXELES
    del Quest 3 (25 PPD).
  - niebla en la silueta y en la base.
  - borde de la malla: margen angular entre la silueta y el punto (R_MAX, 0).
  - piso quieto: max |h| a 10 m del usuario y del metaball en todo el tiempo.
  - malla: anillos, vertices y ERROR DE SILUETA de la malla contra la funcion continua (px), por esquema.
Uso: python diag_escala.py [solo=v1|v2] [renders=0|1]
"""
import math
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import modelo_valle as mv  # noqa: E402

EYE = np.array([0.0, 0.0, 120.0])
IPD = 6.3
SWAY = 5.0
PPD = 25.0
TIEMPOS = np.linspace(0.0, 600.0, 13)


def px(rad):
    return np.degrees(rad) * PPD


def silueta(hfun, P, t, naz=720, J=4000, rho_min=40.0, az=None):
    if az is None:
        az = np.radians(np.arange(naz) * 360.0 / naz - 180.0)
    rho = rho_min * np.power(P["R_MAX"] / rho_min, np.arange(J) / (J - 1.0))
    X = rho[:, None] * np.cos(az)[None, :]
    Y = rho[:, None] * np.sin(az)[None, :]
    h, _ = hfun(X, Y, t, P)
    el = np.arctan2(h - EYE[2], rho[:, None])
    j = np.argmax(el, axis=0)
    k = np.arange(az.size)
    base = np.argmax(h > 20.0, axis=0)
    hasb = (h > 20.0).any(axis=0)
    return dict(az=az, el=el[j, k], rho=rho[j], h=h[j, k], rbase=np.where(hasb, rho[base], np.nan))


def resumen(nombre, v):
    q = lambda a: np.nanpercentile(a, [0, 10, 50, 90, 100])  # noqa: E731
    fmt = lambda a, f="%.2f": " / ".join(f % x for x in a)  # noqa: E731
    print("  %-38s min / p10 / med / p90 / max = %s" % (nombre, fmt(q(v))))


def medir(tag, hfun, P, fogfun):
    print("\n=================== %s ===================" % tag)
    S_all = [silueta(hfun, P, t) for t in TIEMPOS]
    el = np.array([s["el"] for s in S_all])
    rho = np.array([s["rho"] for s in S_all])
    hh = np.array([s["h"] for s in S_all])
    rb = np.array([s["rbase"] for s in S_all])
    frente = np.abs(np.degrees(S_all[0]["az"])) <= 55.0
    print("SILUETA (720 azimuts x %d instantes en 10 min)" % len(TIEMPOS))
    resumen("elevacion de la silueta (deg)", np.degrees(el))
    resumen("  ... solo el frente +-55 (deg)", np.degrees(el[:, frente]))
    resumen("distancia de la silueta (m)", rho / 100.0)
    resumen("alto de la silueta (m)", hh / 100.0)
    resumen("razon de horizonte = alto/ojos", hh / EYE[2])
    resumen("base: primer h>20 cm (m)", rb / 100.0)
    resumen("declinacion de la base (deg)", np.degrees(np.arctan2(EYE[2], rb)))
    resumen("disparidad vs infinito, silueta (px)", px(IPD / rho))
    resumen("paralaje 5 cm de cabeza, silueta (px)", px(SWAY / rho))
    D = np.sqrt(rho ** 2 + (hh - EYE[2]) ** 2)
    resumen("niebla en la silueta", fogfun(D, hh, EYE[2], P))
    Db = np.sqrt(rb ** 2 + EYE[2] ** 2)
    resumen("niebla en la base", fogfun(Db, np.zeros_like(Db), EYE[2], P))
    edge = math.atan2(-EYE[2], P["R_MAX"])
    marg = np.degrees(el.min() - edge)
    print("  borde de la malla: el(R_MAX, 0) = %.3f deg; silueta min = %.2f deg -> margen %.2f deg" % (
        math.degrees(edge), np.degrees(el.min()), marg))
    # piso quieto
    worst = 0.0
    for t in TIEMPOS:
        for cx in (0.0, 380.0):
            a = np.radians(np.arange(0, 360, 2))
            rr = np.linspace(0, 1000, 101)
            X = cx + rr[:, None] * np.cos(a)[None, :]
            Y = rr[:, None] * np.sin(a)[None, :]
            h, _ = hfun(X, Y, t, P)
            worst = max(worst, float(np.abs(h).max()))
    print("  piso quieto: max |h| a <= 10 m del usuario y del metaball, 10 min = %.4f cm" % worst)
    return dict(el=el, rho=rho, h=hh)


def error_malla(hfun, P, S, rings, t=0.0, sub=12, span=(-180.0, 180.0)):
    """Silueta de la MALLA (vertices + interpolacion lineal entre sectores) contra la continua. En px."""
    s0 = np.arange(S)
    phi_v = 2.0 * math.pi * s0 / S
    X = rings[:, None] * np.cos(phi_v)[None, :]
    Y = rings[:, None] * np.sin(phi_v)[None, :]
    h, _ = hfun(X, Y, t, P)
    elv = np.arctan2(h - EYE[2], rings[:, None])  # (anillos, sectores)
    w = (np.arange(sub) + 0.5) / sub
    phi = (phi_v[:, None] + w[None, :] * 2.0 * math.pi / S).ravel()
    e0 = np.repeat(elv, sub, axis=1)
    e1 = np.repeat(np.roll(elv, -1, axis=1), sub, axis=1)
    wt = np.tile(w, S)
    elm = (e0 * (1 - wt) + e1 * wt).max(axis=0)
    az = np.where(phi > math.pi, phi - 2 * math.pi, phi)
    st = silueta(hfun, P, t, az=az, J=6000)
    err = px(np.abs(st["el"] - elm))
    m = (np.degrees(az) >= span[0]) & (np.degrees(az) <= span[1])
    return float(err[m].max()), float(np.percentile(err[m], 99)), float(np.median(err[m]))


def mallas(hfun, P, esquemas, tiempos=(0.0, 41.5)):
    print("MALLA (error de silueta de la malla contra la funcion continua; 1 px = 0,04 deg)")
    for nombre, S, rings in esquemas:
        nv = 1 + S * len(rings)
        errs = [error_malla(hfun, P, S, rings, t=t) for t in tiempos]
        ef = [error_malla(hfun, P, S, rings, t=t, span=(-60.0, 60.0)) for t in tiempos]
        print("  %-44s S=%3d anillos=%3d verts=%6d  err max/p99/med = %.2f / %.2f / %.2f px  (frente +-60: max %.2f)" % (
            nombre, S, len(rings), nv, max(e[0] for e in errs), max(e[1] for e in errs), max(e[2] for e in errs),
            max(e[0] for e in ef)))


def capas(hfun, P, fogfun, corte=28000.0):
    """Separa la silueta por capa (media < corte <= lejana) y da tamano angular, estereo, niebla y velocidad."""
    print("CAPAS de la silueta (corte %.0f m), 720 azimuts x %d instantes" % (corte / 100, len(TIEMPOS)))
    S_all = [silueta(hfun, P, t) for t in TIEMPOS]
    el = np.array([s["el"] for s in S_all]).ravel()
    rho = np.array([s["rho"] for s in S_all]).ravel()
    hh = np.array([s["h"] for s in S_all]).ravel()
    for nom, m in (("MEDIA", rho < corte), ("LEJANA", rho >= corte)):
        if not m.any():
            continue
        print(" capa %s: %.0f %% de los azimuts" % (nom, 100.0 * m.mean()))
        resumen("  distancia (m)", rho[m] / 100)
        resumen("  alto (m)", hh[m] / 100)
        resumen("  elevacion (deg)", np.degrees(el[m]))
        resumen("  disparidad (px)", px(IPD / rho[m]))
        D = np.sqrt(rho[m] ** 2 + (hh[m] - EYE[2]) ** 2)
        resumen("  niebla en la cima", fogfun(D, hh[m], EYE[2], P))
    # velocidad vertical angular en la silueta (diferencia de 1 s)
    s0 = silueta(hfun, P, 0.0)
    vmax = 0.0
    for t in np.linspace(0.0, 120.0, 25):
        X = s0["rho"] * np.cos(s0["az"])
        Y = s0["rho"] * np.sin(s0["az"])
        h0, _ = hfun(X, Y, t, P)
        h1, _ = hfun(X, Y, t + 1.0, P)
        vmax = max(vmax, float(np.degrees(np.abs(h1 - h0) / s0["rho"]).max()))
    print("  velocidad angular vertical maxima en la silueta (2 min): %.3f deg/s" % vmax)


def bandas_llano(esquemas, r0=3000.0, r1=9000.0):
    """Alto en pantalla (px) de cada franja entre anillos del LLANO visible al frente (z = 0, ojos a 120 cm)."""
    print("LLANO al frente (%.0f-%.0f m): alto en pantalla de cada franja entre anillos (px, 25 PPD)" % (r0 / 100, r1 / 100))
    for nombre, S, rings in esquemas:
        r = rings[(rings >= r0) & (rings <= r1)]
        th = np.arctan2(EYE[2], r)
        band = px(-np.diff(th))
        print("  %-44s anillos=%3d  franja min/med/max = %.2f / %.2f / %.2f px  (<1 px: %d)" % (
            nombre, r.size, band.min(), np.median(band), band.max(), int((band < 1.0).sum())))


def tabla_niebla():
    print("\nNIEBLA a la altura del piso (z = 0) y en una cima (z = alto indicado), camara a 120 cm")
    heart = dict(FogStart=663.0, FogDist=5514.0, FogMax=1.0)  # derivado de "62 % a 60 m, 97 % a 200 m"
    print("  dist (m) |  v1   | Heart |  v2 piso | v2 cima 20 m | v2 cima 60 m")
    for dm in (5, 10, 15, 20, 30, 44, 60, 100, 150, 200, 300, 400, 470, 600):
        D = np.array([dm * 100.0])
        z0 = np.zeros(1)
        v1 = mv.fog_v1(D, z0, 120.0)[0] if dm <= 44 else float("nan")
        he = heart["FogMax"] * (1 - math.exp(-max(dm * 100 - heart["FogStart"], 0) / heart["FogDist"]))
        v2 = mv.fog_v2(D, z0, 120.0)[0]
        v2c = mv.fog_v2(D, np.array([2000.0]), 120.0)[0]
        v2m = mv.fog_v2(D, np.array([6000.0]), 120.0)[0]
        print("  %7d  | %5.3f | %5.3f |  %5.3f   |    %5.3f     |    %5.3f" % (dm, v1, he, v2, v2c, v2m))


if __name__ == "__main__":
    args = dict(a.split("=", 1) for a in sys.argv[1:] if "=" in a)
    solo = args.get("solo", "")
    tabla_niebla()
    if solo in ("", "v1"):
        medir("v1 (spec, defaults)", mv.h_v1, mv.P1, mv.fog_v1)
        capas(mv.h_v1, mv.P1, mv.fog_v1, corte=1e9)
        if args.get("mallas", "1") == "1":
            mallas(mv.h_v1, mv.P1, [("v1 (spec 2)", 192, mv.anillos_v1())])
    if solo in ("", "v2"):
        medir("v2 (candidato de escala)", mv.h_v2, mv.P2, mv.fog_v2)
        esq = [
            ("v2-a: S192, cuadradas hasta 590 m", 192, mv.anillos_v2(S=192)),
            ("v2-b: S192, aspecto 1,6 desde 60 m", 192, mv.anillos_v2(S=192, aspecto=((0.0, 1.0), (6000.0, 1.6)))),
            ("v2-c: S160, aspecto 1,5 desde 60 m", 160, mv.anillos_v2(S=160, aspecto=((0.0, 1.0), (6000.0, 1.5)))),
            ("v2-d: S160, aspecto 1,25 desde 60 m", 160, mv.anillos_v2(S=160, aspecto=((0.0, 1.0), (6000.0, 1.25)))),
            ("v2-e: S224, aspecto 2 desde 60 m", 224, mv.anillos_v2(S=224, aspecto=((0.0, 1.0), (6000.0, 2.0)))),
            ("v2-f: S192, aspecto 1,3 desde 30 m, 2 desde 120 m", 192,
             mv.anillos_v2(S=192, aspecto=((0.0, 1.0), (3000.0, 1.3), (12000.0, 2.0)))),
        ]
        capas(mv.h_v2, mv.P2, mv.fog_v2)
        bandas_llano([("v1 (spec 2)", 192, mv.anillos_v1())] + esq, r0=1500.0, r1=4400.0)
        bandas_llano(esq)
        if args.get("mallas", "1") == "1":
            mallas(mv.h_v2, mv.P2, esq)
