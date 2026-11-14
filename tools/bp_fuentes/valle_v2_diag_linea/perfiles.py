# -*- coding: utf-8 -*-
"""perfiles.py - figura de evidencia: la linea en la captura real, en el modelo v1 y como queda con la propuesta.
Panel 1: luminancia (sRGB 8 bits, canal G) vs angulo bajo el horizonte, columna col 700 de cap_valle_frente
         (azimut +20,6 grados): captura real y modelo v1 superpuestos, con la fila donde e = 1.
Panel 2: mismo perfil (azimut +20,6, ojos del usuario) para v1, v1_C2, v1_x3 y v2.
Panel 3: corte del terreno h(distancia) en ese azimut, v1 vs v2 (con escala de pendiente).
Salida: perfiles_linea.png
"""
import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import modelo_v1 as M  # noqa: E402
from propuesta import VARS, campo, trazar  # noqa: E402

W, H = 1052, 862
f = (W / 2) / math.tan(math.radians(45))
img = np.asarray(Image.open(os.path.join(os.path.dirname(AQUI), "cap_valle_frente.png")).convert("RGB")).astype(float)
c = 700
o = np.array([0.0, 0.0, 120.0])
filas = np.arange(420, 560)
d = M.rayos(0.0, -2.0, W, H, 90.0, filas=filas, cols=[c])[:, 0, :]
el = np.degrees(np.arcsin(d[:, 2]))
az = math.degrees(math.atan2(d[0, 1], d[0, 0]))
col, info = M.render(o, d[:, None, :], 0.0)
Gm = np.round(M.srgb(col[:, 0])[:, 1] * 255)
Gc = img[filas, c, 1]
e = info["e"][:, 0]
k1 = np.where((e[:-1] >= 1) & (e[1:] < 1))[0][-1]

fig, ax = plt.subplots(1, 3, figsize=(17, 5))
ax[0].plot(el, Gc, "k.-", lw=1, ms=3, label="captura real (col 700)")
ax[0].plot(el, Gm, "r-", lw=1, label="modelo v1 (port del HLSL)")
ax[0].axvline(el[k1] - 0.05, color="b", ls="--", lw=1, label="e = 1 (borde del piso)")
ax[0].set_xlabel("elevacion de la mirada (grados; 0 = horizonte)")
ax[0].set_ylabel("sRGB G (0-255)")
ax[0].set_title("La linea = el borde del piso plano (e = 1)")
ax[0].legend(fontsize=8)
ax[0].invert_xaxis()

th = np.arange(-25.0, 6.0, 0.02)
azr = math.radians(az)
dd = np.stack([np.cos(np.radians(th)) * math.cos(azr), np.cos(np.radians(th)) * math.sin(azr), np.sin(np.radians(th))], -1)
for nombre, st in (("v1", "r-"), ("v1_C2", "m--"), ("v1_x3", "g-"), ("v2", "b-")):
    colv, dist, hit = trazar(VARS[nombre], o, dd)
    G = np.round(M.srgb(colv)[:, 1] * 255)
    ax[1].plot(th, G, st, lw=1.2, label=nombre)
ax[1].set_xlabel("elevacion de la mirada (grados)")
ax[1].set_ylabel("sRGB G")
ax[1].set_title("Perfil desde los ojos, azimut %+.1f grados" % az)
ax[1].legend(fontsize=8)
ax[1].invert_xaxis()

s = np.linspace(0, 12000, 6001)
for nombre, st in (("v1", "r-"), ("v2", "b-")):
    cf = campo(VARS[nombre], 0.0)
    hh = cf(s * math.cos(azr), s * math.sin(azr))[0]
    ax[2].plot(s / 100, hh / 100, st, lw=1.2, label=nombre)
ax[2].plot([0, 120], [1.2, 1.2], "k:", lw=0.8, label="ojos (1,2 m)")
ax[2].set_xlabel("distancia al usuario (m)")
ax[2].set_ylabel("h (m)")
ax[2].set_title("Corte del terreno en ese azimut (t = 0)")
ax[2].set_aspect("auto")
ax[2].legend(fontsize=8)
fig.tight_layout()
fig.savefig(os.path.join(AQUI, "perfiles_linea.png"), dpi=90)
print("perfiles_linea.png")
