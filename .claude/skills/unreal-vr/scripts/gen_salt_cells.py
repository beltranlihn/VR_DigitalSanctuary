# -*- coding: utf-8 -*-
"""gen_salt_cells.py - textura de los poligonos del salar para M_ChladniFloor_SC.

Horneado (no en vivo) porque en la Quest un Voronoi por pixel cuesta 34 celdas por pixel: el prototipo web
(docs/prototipos/placa-chladni.html, saltCells) lo calcula en vivo; aca queda en una textura que TESELA.

Contenido: R = distancia al BORDE de la celda (en celdas, /0,5 -> 0..1), el mismo algoritmo de dos pasadas del
prototipo (Inigo Quilez: celda mas cercana y despues la distancia al bisector con cada vecina).
La textura cubre TILE x TILE celdas y es PERIODICA (los puntos se repiten con modulo TILE), asi que se repite
sin costura. En el material: uv = p / (CellSize * TILE); dv_cm = R * 0,5 * CellSize.

Uso:  python gen_salt_cells.py            -> VR_Test/Saved/ClaudeScripts/T_SaltCells_SC.png (1024, gris 8 bits)
"""
import os
import numpy as np
from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(AQUI, "..", "..", "..", ".."))
SALIDA = os.path.join(REPO, "VR_Test", "Saved", "ClaudeScripts", "T_SaltCells_SC.png")

RES = 1024
TILE = 8          # celdas por lado de la textura
JIT = 0.8         # irregularidad (igual que CellJitter del prototipo)
SEED = 7


def main():
    rng = np.random.default_rng(SEED)
    pts = 0.5 + (rng.random((TILE, TILE, 2)) - 0.5) * JIT          # punto de cada celda, en coordenadas de celda
    u = (np.arange(RES) + 0.5) / RES * TILE
    X, Y = np.meshgrid(u, u)                                         # X = columna, Y = fila
    n = np.stack([np.floor(X), np.floor(Y)], -1)
    f = np.stack([X, Y], -1) - n
    md = np.full(X.shape, 8.0)
    mr = np.zeros(X.shape + (2,))
    mg = np.zeros(X.shape + (2,))
    for j in (-1, 0, 1):
        for i in (-1, 0, 1):
            g = np.array([i, j], float)
            c = (n + g).astype(int) % TILE
            o = pts[c[..., 1], c[..., 0]]
            r = g + o - f
            d = (r * r).sum(-1)
            m = d < md
            md = np.where(m, d, md)
            mr = np.where(m[..., None], r, mr)
            mg = np.where(m[..., None], g, mg)
    md = np.full(X.shape, 8.0)
    for j in range(-2, 3):
        for i in range(-2, 3):
            g = mg + np.array([i, j], float)
            c = (n + g).astype(int) % TILE
            o = pts[c[..., 1], c[..., 0]]
            r = g + o - f
            dd = r - mr
            L = np.sqrt((dd * dd).sum(-1))
            ok = L > 1e-4
            nn = dd / np.maximum(L, 1e-9)[..., None]
            d = (0.5 * (mr + r) * nn).sum(-1)
            md = np.where(ok & (d < md), d, md)
    val = np.clip(md / 0.5, 0.0, 1.0)
    img = Image.fromarray(np.round(val * 255).astype(np.uint8), mode="L")
    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    img.save(SALIDA)
    print("escrito %s  (%dx%d, %d celdas por lado; borde medio %.3f, max %.3f)" % (SALIDA, RES, RES, TILE, val.mean(), val.max()))


if __name__ == "__main__":
    main()
