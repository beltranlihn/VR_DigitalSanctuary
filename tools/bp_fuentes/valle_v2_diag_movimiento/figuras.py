# -*- coding: utf-8 -*-
"""figuras.py - kimografo de la silueta (v1 contra oleaje) y corte espacio-tiempo del gif.

fig_kimografo_silueta.png: elevacion de la silueta menos su media en el tiempo, azimut -90..90 (x) contra
  t = 0..120 s (y). Franjas VERTICALES = crece y se achica en su lugar (v1); franjas INCLINADAS = viaja (oleaje).
  Misma escala de color en los dos paneles (grados).
fig_corte_gif.png: una fila de pixeles justo bajo la silueta, apilada en el tiempo (10 s del gif, 5 cuadros/s).
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageSequence

AQUI = os.path.dirname(os.path.abspath(__file__))
AZ = np.arange(-180.0, 180.0, 0.5)
fr = np.abs(AZ) <= 90
s1 = np.load(os.path.join(AQUI, "sil_v1.npy")).astype(float)
s2 = np.load(os.path.join(AQUI, "sil_c.npy")).astype(float)
d1 = s1 - s1.mean(axis=0)
d2 = s2 - s2.mean(axis=0)
lim = max(np.abs(d1[:, fr]).max(), np.abs(d2[:, fr]).max())
fig, ax = plt.subplots(1, 2, figsize=(12, 5.2), sharey=True)
for a, d, tit in ((ax[0], d1, "v1 (morph de amplitud)"), (ax[1], d2, "propuesta: oleaje viajero (base x5)")):
    im = a.imshow(d[:, fr], aspect="auto", origin="lower", cmap="RdBu_r", vmin=-lim, vmax=lim,
                  extent=[-90, 90, 0, (d.shape[0] - 1) * 0.5])
    a.set_title(tit)
    a.set_xlabel("azimut (grados; 0 = al frente, + = derecha)")
    a.axvline(-45, color="k", lw=0.5, ls=":")
    a.axvline(45, color="k", lw=0.5, ls=":")
ax[0].set_ylabel("t (s)")
cb = fig.colorbar(im, ax=ax, shrink=0.9)
cb.set_label("elevacion de la silueta - su media (grados)")
fig.suptitle("Silueta de las colinas vista desde los ojos (0, 0, 120): 120 s. Punteado = captura del editor (HFOV 90)")
fig.savefig(os.path.join(AQUI, "fig_kimografo_silueta.png"), dpi=110)

gif = Image.open(os.path.join(AQUI, "ondula_v1_vs_oleaje.gif"))
fr_ = [np.asarray(f.convert("RGB")).astype(float) for f in ImageSequence.Iterator(gif)]
H = 431
fila_v1, fila_ola = 185, 4 + H + 200   # justo bajo la silueta en cada mitad (ver tira_v1_vs_oleaje.png)
c1 = np.stack([f[fila_v1] for f in fr_])
c2 = np.stack([f[fila_ola] for f in fr_])
fig, ax = plt.subplots(2, 1, figsize=(10, 5.5))
for a, c, tit in ((ax[0], c1, "v1: fila %d" % fila_v1), (ax[1], c2, "oleaje: fila %d" % (fila_ola - H - 4))):
    a.imshow(c.astype(np.uint8), aspect="auto", origin="lower", extent=[0, c.shape[1], 0, len(fr_) / 5.0])
    a.set_title(tit + " apilada en el tiempo (10 s reales)")
    a.set_ylabel("t (s)")
ax[1].set_xlabel("columna (px, 526 = HFOV 90)")
fig.tight_layout()
fig.savefig(os.path.join(AQUI, "fig_corte_gif.png"), dpi=110)
print("ok")
