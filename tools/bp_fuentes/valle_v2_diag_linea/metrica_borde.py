# -*- coding: utf-8 -*-
"""metrica_borde.py - la metrica de propuesta.py (G rampa y Q quiebre, en % por grado) medida SOLO en una
ventana de +-1,5 grados alrededor del borde del piso plano (v1: e = 1; v2: rho = CalmR), desde los ojos
(0, 0, 120), azimuts -40..40 cada 8 al frente (yaw 0) y al costado (yaw 90). Referencia: el mismo tramo
angular sobre un piso plano INFINITO con el mismo sombreado (lo que la metrica mide sin ningun borde).
Uso: python metrica_borde.py
"""
import math
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import modelo_v1 as M  # noqa: E402
from propuesta import VARS, campo, suelo, trazar  # noqa: E402

EYE = np.array([0.0, 0.0, 120.0])
DT = 0.02


def q_de(th, Y):
    dl = np.gradient(np.log(Y), DT) * 100
    w = int(round(0.25 / DT))
    c = np.convolve(dl, np.ones(w) / w, mode="valid")
    return np.abs(c).max(), np.abs(c[w:] - c[:-w]).max()


def plano(p, az, th):
    """piso plano infinito (h = 0) con el sombreado de p: la linea de base de la metrica."""
    el = np.radians(th)
    s = EYE[2] / np.tan(-el)
    x, y = s * math.cos(az), s * math.sin(az)
    hit = np.stack([x, y, np.zeros_like(x)], -1)
    z = np.zeros_like(x)
    return M.luma(suelo(hit, z, z, z, z, EYE, p))


def main(nombres=("v1", "v1_C2", "v1_x3", "v2", "v2_sinGate")):
    for nombre in nombres:
        p = VARS[nombre]
        filas = []
        for vista, yaw in (("frente", 0.0), ("costado", 90.0)):
            for a in range(-40, 41, 8):
                az = math.radians(yaw + a)
                # elevacion del borde: primer punto (desde los pies) con e >= 1 / rho >= CalmR sobre el piso
                s = np.linspace(100, 40000, 40000)
                x, y = s * math.cos(az), s * math.sin(az)
                if p["kind"] == "v1":
                    e = np.sqrt(((x - p["ValleyX"]) / p["ValleyA"]) ** 2 + (y / p["ValleyB"]) ** 2)
                else:
                    e = np.hypot(x - p["CalmX"], y) / p["CalmR"]
                sb = s[np.argmax(e >= 1.0)]
                te = -math.degrees(math.atan2(EYE[2], sb))
                th = np.arange(te - 1.5, te + 1.5, DT)
                el = np.radians(th)
                d = np.stack([np.cos(el) * math.cos(az), np.cos(el) * math.sin(az), np.sin(el)], -1)
                col, dist, hit = trazar(p, EYE, d)
                G, Q = q_de(th, M.luma(col))
                thp = th[th < -0.3]
                Gp, Qp = q_de(thp, plano(p, az, thp))
                filas.append((vista, a, sb, te, G, Q, Gp, Qp))
        A = np.array([f[4:] for f in filas])
        print("%-11s borde a %4.0f-%4.0f m | G max %6.1f med %6.1f | Q max %6.1f med %6.1f || piso infinito: G max %5.1f  Q max %5.1f" % (
            nombre, min(f[2] for f in filas) / 100, max(f[2] for f in filas) / 100, A[:, 0].max(), np.median(A[:, 0]),
            A[:, 1].max(), np.median(A[:, 1]), A[:, 2].max(), A[:, 3].max()))
        for f in filas:
            if f[1] in (-40, 0, 40):
                print("      %-7s az%+3d: borde a %5.1f m (%.2f deg)  G %6.1f  Q %6.1f   (piso infinito G %4.1f Q %4.1f)" % (
                    f[0], f[1], f[2] / 100, f[3], f[4], f[5], f[6], f[7]))


if __name__ == "__main__":
    main()
