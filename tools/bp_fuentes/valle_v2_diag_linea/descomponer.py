# -*- coding: utf-8 -*-
"""descomponer.py - (1) de que esta hecho el salto de luminancia en el borde del piso (e = 1) y
(2) que clase de continuidad tiene la altura ahi (C0/C1/C2) y cuan cerrada es la curva.

(1) Contrafactuales: para los pixeles de la ladera, a 0,25 / 0,5 / 1 grado por encima de la linea, se
    recalcula el color CONGELANDO un termino del sombreado en su valor del piso en el borde (sheen,
    wrap, oscurecimiento por pendiente, aclarado de cimas, niebla). La parte del salto que desaparece
    es la contribucion de ese termino.
(2) A lo largo del borde e = 1 (360 puntos): f de la duna, salto de h'' al cruzar el borde en la
    direccion normal a la elipse (cm^-1), radio de curvatura 1/h'', distancia hasta 10/20/30 grados de
    pendiente, y el tamano ANGULAR (vista del usuario) de la franja donde la pendiente pasa de 0 a 20 grados.
Uso: python descomponer.py
"""
import math
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import modelo_v1 as M  # noqa: E402

P = M.P
T = 0.0


def color_congelado(hit, gx, gy, h, hf, cam, ref, freeze):
    """Repite ValleyPS Part 0 con un termino fijado al valor 'ref' (dict del piso en el borde)."""
    L = M.D(P["LightAz"], P["LightEl"])
    d = cam - hit
    Dist = np.linalg.norm(d, axis=-1)
    V = d / Dist[..., None]
    dv = -V
    N = np.stack([-gx, -gy, np.ones_like(gx)], -1)
    N = N / np.linalg.norm(N, axis=-1)[..., None]
    wrap = M.sat(((N * L).sum(-1) + P["Wrap"]) / (1 + P["Wrap"]))
    slopek = M.sat(1 - P["SlopeDark"] * (1 - N[..., 2]))
    if "wrap" in freeze:
        wrap = np.full_like(wrap, ref["wrap"])
    if "slopek" in freeze:
        slopek = np.full_like(slopek, ref["slopek"])
    k = wrap * slopek
    CL, CS, CH = (np.array(P[c]) for c in ("ColLit", "ColShadow", "ColSheen"))
    col = CS + (CL - CS) * k[..., None]
    hfv = np.zeros_like(hf) if "crest" in freeze else hf
    col = col + (CL - col) * (P["CrestLight"] * hfv * hfv)[..., None]
    fres = np.power(np.maximum(1 - M.sat((N * V).sum(-1)), 1e-6), P["SheenPow"])
    fwd = M.sat(0.5 + 0.5 * (dv * L).sum(-1))
    sh = M.sat(P["Sheen"] * fres * (P["SheenBack"] + (1 - P["SheenBack"]) * fwd))
    if "sheen" in freeze:
        sh = np.full_like(sh, ref["sheen"])
    col = col + (CH - col) * sh[..., None]
    fog = P["FogMax"] * (1 - np.exp(-np.maximum(Dist - P["FogStart"], 0) / P["FogDist"]))
    if "fog" in freeze:
        fog = np.full_like(fog, ref["fog"])
    sky = M.cielo(dv, P)
    return col + (sky - col) * fog[..., None]


def parte1():
    print("=" * 100)
    print("(1) CONTRAFACTUALES: salto de luminancia Y (lineal) entre el piso en el borde y la ladera por encima")
    vistas = [("usuario al frente (cap_valle_frente)", np.array([0.0, 0.0, 120.0]), 0.0, -2.0, [200, 330, 700, 980]),
              ("editor de costado (cap_reposo_lado)", np.array([380.0, -700.0, 70.0]), 90.0, 0.0, [60, 200, 330, 526])]
    W, H = 1052, 862
    fpx = (W / 2) / math.tan(math.radians(45))
    tot = {k: [] for k in ("sheen", "wrap", "slopek", "crest", "fog")}
    for nombre, o, yaw, pitch, cols in vistas:
        print("-- " + nombre)
        for c in cols:
            filas = np.arange(420, H)
            d = M.rayos(yaw, pitch, W, H, 90.0, filas=filas, cols=[c])[:, 0, :]
            s = M.raycast(o, d, T)
            hp = o + d * s[:, None]
            h, gx, gy, hf, tm = M.campo(hp[:, 0], hp[:, 1], T, terms=True)
            hp[:, 2] = h
            e = tm["e"]
            idx = np.where((e[:-1] >= 1.0) & (e[1:] < 1.0))[0]
            if not idx.size:
                continue
            kf = idx[-1] + 1                      # primer pixel de PISO bajo la linea
            col, pp = M.suelo(hp, gx, gy, h, hf, o, parts=True)
            ref = {k: pp[k][kf] for k in ("wrap", "slopek", "sheen", "fog")}
            Yf = M.luma(col[kf])
            linea = []
            for deg in (0.25, 0.5, 1.0):
                kh = kf - int(round(deg * fpx * math.pi / 180))
                Yh = M.luma(col[kh])
                fila = "   col %4d  %.2f deg arriba (fila %d): Y piso %.3f -> ladera %.3f  (Weber %+.0f %%)" % (
                    c, deg, filas[kh], Yf, Yh, 100 * (Yh - Yf) / Yf)
                partes = []
                for term in ("sheen", "wrap", "slopek", "crest", "fog"):
                    cc = color_congelado(hp[kh:kh + 1], gx[kh:kh + 1], gy[kh:kh + 1], h[kh:kh + 1], hf[kh:kh + 1], o, ref, {term})
                    Yc = M.luma(cc[0])
                    share = (Yc - Yh) / (Yf - Yh) if abs(Yf - Yh) > 1e-9 else 0.0
                    partes.append("%s %.0f%%" % (term, 100 * share))
                    if deg == 1.0:
                        tot[term].append(share)
                linea.append(fila + "  | parte del salto que explica cada termino: " + ", ".join(partes))
            print("\n".join(linea))
    print("   PROMEDIO a 1 grado: " + ", ".join("%s %.0f%%" % (k, 100 * np.mean(v)) for k, v in tot.items()))


def parte2():
    print("=" * 100)
    print("(2) CONTINUIDAD EN EL BORDE e = 1 (360 puntos, t = 0 y t = 41,5)")
    VX, VA, VB = P["ValleyX"], P["ValleyA"], P["ValleyB"]
    for t in (0.0, 41.5):
        rows = []
        for k in range(360):
            th = math.radians(k + 0.5)
            # punto del borde y normal exterior de la elipse
            bx, by = VX + VA * math.cos(th), VB * math.sin(th)
            nx, ny = math.cos(th) / VA, math.sin(th) / VB
            nn = math.hypot(nx, ny)
            nx, ny = nx / nn, ny / nn
            sgrid = np.linspace(-200.0, 600.0, 8001)          # cm a lo largo de la normal
            x, y = bx + nx * sgrid, by + ny * sgrid
            h, gx, gy, hf, tm = M.campo(x, y, t, terms=True)
            ds = sgrid[1] - sgrid[0]
            slope = gx * nx + gy * ny                         # dh/ds
            i0 = np.searchsorted(sgrid, 0.0)
            # h'' por diferencias finitas a +-(2..6) cm del borde
            dd = np.gradient(slope, ds)
            h2_in = dd[i0 - 40:i0 - 5].mean()
            h2_out = dd[i0 + 5:i0 + 40].mean()
            ang = np.degrees(np.arctan(np.abs(np.hypot(gx, gy))))
            def dist_a(a):
                j = np.where((sgrid > 0) & (ang >= a))[0]
                return sgrid[j[0]] if j.size else np.nan
            # tamano angular desde los ojos del usuario de la franja 0 -> 20 grados
            s20 = dist_a(20.0)
            p0 = np.array([bx, by, 0.0])
            ang_franja = np.nan
            if not np.isnan(s20):
                j = np.searchsorted(sgrid, s20)
                p1 = np.array([x[j], y[j], h[j]])
                eye = np.array([0.0, 0.0, 120.0])
                def elev(p):
                    v = p - eye
                    return math.degrees(math.atan2(v[2], math.hypot(v[0], v[1])))
                ang_franja = elev(p1) - elev(p0)
            fb = tm["f"][i0]
            rows.append((k, fb, h2_in, h2_out, 1 / max(h2_out, 1e-12), dist_a(10.0), dist_a(20.0), dist_a(30.0), ang_franja,
                         math.hypot(bx, by)))
        a = np.array(rows, float)
        print("-- t = %g s" % t)
        print("   f en el borde: min %.2f  mediana %.2f  max %.2f  (f = 0: pasillo plano; solo sube el anillo)" % (
            a[:, 1].min(), np.median(a[:, 1]), a[:, 1].max()))
        print("   h'' justo ADENTRO del borde: max |%.1e| cm^-1  (el piso es plano: 0)" % np.abs(a[:, 2]).max())
        print("   h'' justo AFUERA: min %.2e  mediana %.2e  max %.2e cm^-1  -> SALTO de h'': es C1, NO C2" % (
            a[:, 3].min(), np.median(a[:, 3]), a[:, 3].max()))
        print("   radio de curvatura del pliegue (1/h''): min %.0f  mediana %.0f  max %.0f cm" % (
            a[:, 4].min(), np.median(a[:, 4]), a[:, 4].max()))
        for col, lbl in ((5, 10), (6, 20), (7, 30)):
            v = a[:, col]
            v = v[~np.isnan(v)]
            print("   distancia desde el borde hasta %2d grados de pendiente: min %.0f  mediana %.0f  p90 %.0f cm  (%d/360 lo alcanzan)" % (
                lbl, v.min(), np.median(v), np.percentile(v, 90), v.size))
        v = a[:, 8]
        v = v[~np.isnan(v)]
        print("   franja 0 -> 20 grados vista desde los ojos del usuario: mediana %.2f deg, min %.2f deg (a %.0f-%.0f cm del usuario)" % (
            np.median(v), v.min(), a[:, 9].min(), a[:, 9].max()))
    # expresion analitica del salto (derivada segunda de smoothstep en 0 = 6/(b-a)^2)
    print("-- analitico: h'' afuera = [RimHeight*6/(RimCrest-1)^2 + DuneAmp*f*6/(DuneRise-1)^2] * |grad e|^2")
    for lbl, g in (("frente (|grad e| = 1/ValleyA)", 1 / VA), ("costado (1/ValleyB)", 1 / VB)):
        for f in (0.0, 0.3, 0.6):
            h2 = (P["RimHeight"] * 6 / (P["RimCrest"] - 1) ** 2 + P["DuneAmp"] * f * 6 / (P["DuneRise"] - 1) ** 2) * g * g
            print("   %-30s f=%.1f: h'' = %.2e cm^-1, radio %.0f cm, 20 grados a %.0f cm del borde" % (
                lbl, f, h2, 1 / h2, math.tan(math.radians(20)) / h2))


if __name__ == "__main__":
    parte1()
    parte2()
