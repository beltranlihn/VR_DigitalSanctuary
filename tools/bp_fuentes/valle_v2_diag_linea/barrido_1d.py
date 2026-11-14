# -*- coding: utf-8 -*-
"""barrido_1d.py - regla de diseno: que ancho y que pendiente hacen falta para que el paso piso -> cuenco
NO se lea como linea, independiente de la escala. Perfil radial SIN dunas (solo el cuenco), visto desde
los ojos (0, 0, 120) en tres azimuts (0 = contraluz, 90 = costado, 180 = de frente a la luz).
Como el cuenco es monotono no hay oclusion: cada punto del suelo cae en una sola elevacion de la mirada.
Metrica = la de propuesta.py: G (rampa, %/grado) y Q (quiebre, %/grado de cambio de rampa en 0,25 grados).
Referencia de "suave": el cielo (degradado horizonte -> cenit) y el piso de v1 lejos del borde.
Uso: python barrido_1d.py
"""
import math
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import modelo_v1 as M  # noqa: E402
from propuesta import V2, st3, st5, suelo  # noqa: E402

EYE = np.array([0.0, 0.0, 120.0])


def perfil(p, az, CalmR, W, Hb, st, gate, fog):
    q = dict(p, SheenGate=0.06 if gate else 0.0)
    if not fog:
        q.update(FogMax=0.0)
    a = math.radians(az)
    s = np.concatenate([np.linspace(150, CalmR, 400, endpoint=False), np.geomspace(CalmR, CalmR + 3 * W, 6000)])
    S, dS = st(CalmR, CalmR + W, s)
    h = Hb * S
    g = Hb * dS
    x, y = s * math.cos(a), s * math.sin(a)
    hit = np.stack([x, y, h], -1)
    col = suelo(hit, g * math.cos(a), g * math.sin(a), h, np.zeros_like(h), EYE, q)
    el = np.degrees(np.arctan2(h - EYE[2], s))
    ok = np.concatenate([[True], np.diff(el) > 0])        # solo la parte visible (sin oclusion)
    el, Y = el[ok], M.luma(col[ok])
    th = np.arange(el.min() + 0.3, el.max() - 0.3, 0.02)
    lY = np.log(np.interp(th, el, Y))
    dl = np.gradient(lY, 0.02) * 100
    w = int(round(0.25 / 0.02))
    c = np.convolve(dl, np.ones(w) / w, mode="valid")
    return np.abs(c).max(), np.abs(c[w:] - c[:-w]).max()


def main():
    p = dict(V2)
    print("Referencia: cielo de 0 a 30 grados -> G %.1f %%/grado" % (
        np.abs(np.gradient(np.log(M.luma(M.cielo(np.stack([np.zeros(300), np.zeros(300) + 0.0, np.sin(np.radians(np.linspace(0, 30, 300)))], -1) * 0 + np.stack([np.cos(np.radians(np.linspace(0, 30, 300))), np.zeros(300), np.sin(np.radians(np.linspace(0, 30, 300)))], -1)))), 0.1)).max() * 100))
    print("%-7s %-6s %-6s %-5s %-4s %-4s | %s" % ("CalmR", "W/R", "pend", "paso", "comp", "nieb",
                                                  "  G az0  Q az0 |  G az90 Q az90 | G az180 Q az180"))
    filas = []
    for CalmR in (1200.0, 3000.0):
        for WR in (0.5, 1.0, 2.0, 5.0):
            W = WR * CalmR
            for slope in (8.0, 12.0, 20.0, 30.0):
                Hb = math.tan(math.radians(slope)) * W / 1.875
                for st, stn in ((st3, "C1"), (st5, "C2")):
                    for gate in (False, True):
                        for fog in (False, True):
                            if (not fog) and gate:
                                continue
                            r = [perfil(p, az, CalmR, W, Hb, st, gate, fog) for az in (0.0, 90.0, 180.0)]
                            filas.append((CalmR, WR, slope, stn, gate, fog, r))
                            print("%-7.0f %-6.1f %-6.0f %-5s %-4s %-4s | %6.1f %6.1f | %6.1f %6.1f | %6.1f %6.1f" % (
                                CalmR, WR, slope, stn, "si" if gate else "no", "si" if fog else "no",
                                r[0][0], r[0][1], r[1][0], r[1][1], r[2][0], r[2][1]))


if __name__ == "__main__":
    main()
