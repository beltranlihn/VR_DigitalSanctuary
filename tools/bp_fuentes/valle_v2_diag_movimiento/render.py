# -*- coding: utf-8 -*-
"""render.py - render por columnas (voxel space) de la vista del usuario, SIN Unreal ni Blender.

Camara: ojos (0, 0, 120), yaw 0, pitch -2, HFOV 90, 526 x 431 (mitad de la captura del editor 1052 x 862).
Por columna: se recorre el radio de adelante hacia atras y cada muestra pinta las filas que asoman por
encima de lo ya pintado (oclusion exacta por columna). Color = ValleyPS (modelo_v1.color_suelo). Cielo =
degradado + resplandor de la §6 (sin luna). En "control", esfera de 1,1 m en el lugar del metaball (solo
escala); en "tira" y "gif" no se dibuja, para ver el terreno entero.

Uso:
  python render.py control          -> render_v1_t0.png (comparar con cap_valle_frente.png)
  python render.py tira             -> tira_v1_vs_oleaje.png (t0, t0+5 s y |diferencia| x8, v1 arriba, oleaje abajo)
  python render.py gif [seg] [fps]  -> ondula_v1_vs_oleaje.gif (tiempo REAL: 1 s del gif = 1 s de la obra)
"""
import math
import os
import sys

import numpy as np
from PIL import Image

import modelo_v1 as M
import oleaje as O

AQUI = os.path.dirname(os.path.abspath(__file__))
W, H = 526, 431
F = 263.0
PITCH = math.radians(-2.0)
FWD = np.array([math.cos(PITCH), 0.0, math.sin(PITCH)])
UP = np.array([-math.sin(PITCH), 0.0, math.cos(PITCH)])
RIGHT = np.array([0.0, 1.0, 0.0])
OJO = np.array([0.0, 0.0, M.OJO_Z])
AZC = np.arctan((np.arange(W) + 0.5 - W / 2) / F)
T0 = 20.0

LOOK_V1 = dict(M.LOOK)
LOOK_K = dict(M.LOOK, FogStart=M.LOOK["FogStart"] * O.K, FogDist=M.LOOK["FogDist"] * O.K)


def altura(modelo, x, y, t):
    """h y hf (fraccion de loma, para el aclarado de cimas)."""
    if modelo == "v1":
        pt = M.partes(x, y)
        hh = M.h_de(pt, t)
        hf = (hh - pt["B"]) / M.P["DuneAmp"]
        return hh, hf
    pt = M.partes(x, y, O.BASE_Q)
    hb = M.h_de(pt, 0.0)
    hf = (hb - pt["B"]) / O.BASE_Q["DuneAmp"]
    return hb + O.ola(x, y, t, O.BASE_Q), hf


def cielo(L):
    rows = np.arange(H) + 0.5
    v = (H / 2 - rows)[:, None] / F
    u = (np.arange(W) + 0.5 - W / 2)[None, :] / F
    d = FWD[None, None, :] + u[..., None] * RIGHT[None, None, :] + v[..., None] * UP[None, None, :]
    d = d / np.linalg.norm(d, axis=-1, keepdims=True)
    sky = L["SkyHorizon"] + (L["SkyZenith"] - L["SkyHorizon"]) * M.ss(0.0, L["SkyGradTop"], d[..., 2])[..., None]
    hz = d[..., :2] / np.maximum(np.linalg.norm(d[..., :2], axis=-1, keepdims=True), 1e-4)
    gh = L["GlowDir"][:2] / np.linalg.norm(L["GlowDir"][:2])
    gaz = np.power(np.maximum(hz @ gh, 1e-6), L["GlowPow"])
    gel = 1 - M.ss(0.0, L["GlowHeight"], np.abs(d[..., 2] - L["GlowDir"][2]))
    return sky + (L["SkyGlow"] - sky) * np.clip(L["GlowAmt"] * gaz * gel, 0, 1)[..., None]


def fila(x, y, z):
    d = np.stack([x - OJO[0], y - OJO[1], z - OJO[2]], -1)
    return H / 2 - F * (d @ UP) / (d @ FWD)


def esfera(img):
    c = np.array([380.0, 0.0, 125.0])
    R = 110.0
    rows = np.arange(H) + 0.5
    cols = np.arange(W) + 0.5
    v = (H / 2 - rows)[:, None] / F
    u = (cols - W / 2)[None, :] / F
    d = FWD[None, None, :] + u[..., None] * RIGHT[None, None, :] + v[..., None] * UP[None, None, :]
    d = d / np.linalg.norm(d, axis=-1, keepdims=True)
    oc = OJO - c
    b = d @ oc
    disc = b * b - (oc @ oc - R * R)
    hit = disc > 0
    tt = -b - np.sqrt(np.maximum(disc, 0))
    P = OJO + d * tt[..., None]
    N = (P - c) / R
    k = np.clip((N @ M.LOOK["LightDir"] + 0.6) / 1.6, 0, 1)
    col = np.array([0.36, 0.30, 0.62]) + (np.array([0.92, 0.945, 1.0]) - np.array([0.36, 0.30, 0.62])) * k[..., None]
    img[hit] = col[hit]
    return img


def render(modelo, t, L=None, con_esfera=False):
    L = L or (LOOK_V1 if modelo == "v1" else LOOK_K)
    rend = 4400.0 if modelo == "v1" else 22000.0
    img = cielo(L).copy()
    ytop = np.full(W, H, dtype=np.int64)
    rows = np.arange(H)
    ca, sa = np.cos(AZC), np.sin(AZC)
    r = 100.0
    while r < rend:
        x, y = r * ca, r * sa
        hh, hf = altura(modelo, x, y, t)
        ri = np.ceil(fila(x, y, hh) - 0.5).astype(np.int64)
        ri = np.clip(ri, 0, H)
        if (ri < ytop).any():
            d = 0.5 if modelo == "v1" else 2.0
            gx = (altura(modelo, x + d, y, t)[0] - altura(modelo, x - d, y, t)[0]) / (2 * d)
            gy = (altura(modelo, x, y + d, t)[0] - altura(modelo, x, y - d, t)[0]) / (2 * d)
            col = M.color_suelo(x, y, hh, gx, gy, np.clip(hf, 0, 1), L=L)
            lo, hi = int(ri.min()), int(ytop.max())
            band = rows[lo:hi, None]
            mk = (band >= ri[None, :]) & (band < ytop[None, :])
            sub = img[lo:hi]
            sub[mk] = np.broadcast_to(col[None, :, :], sub.shape)[mk]
            ytop = np.minimum(ytop, ri)
        r *= 1.003
    if con_esfera:
        img = esfera(img)
    return M.srgb8(img).round().clip(0, 255).astype(np.uint8)


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "control"
    if modo == "control":
        Image.fromarray(render("v1", 0.0, con_esfera=True)).save(os.path.join(AQUI, "render_v1_t0.png"))
        Image.fromarray(render("ola", 0.0, con_esfera=True)).save(os.path.join(AQUI, "render_oleaje_t0.png"))
    elif modo == "tira":
        filas = []
        for mod in ("v1", "ola"):
            a = render(mod, T0).astype(np.float64)
            b = render(mod, T0 + 5.0).astype(np.float64)
            dif = np.clip(np.abs(b - a).max(axis=2) * 8.0, 0, 255)
            difc = np.stack([dif, dif, dif], -1)
            sep = np.full((H, 6, 3), 255.0)
            filas.append(np.concatenate([a, sep, b, sep, difc], axis=1))
            print("RENDER %s: diferencia media %.2f niveles, p99 %.1f, max %.0f; pixeles que cambian >2 niveles: %.1f%%"
                  % (mod, (np.abs(b - a).max(axis=2)).mean(), np.percentile(np.abs(b - a).max(axis=2), 99),
                     np.abs(b - a).max(), 100 * (np.abs(b - a).max(axis=2) > 2).mean()))
        sepv = np.full((6, filas[0].shape[1], 3), 255.0)
        Image.fromarray(np.concatenate([filas[0], sepv, filas[1]], axis=0).astype(np.uint8)).save(
            os.path.join(AQUI, "tira_v1_vs_oleaje.png"))
    elif modo == "gif":
        seg = float(sys.argv[2]) if len(sys.argv) > 2 else 10.0
        fps = float(sys.argv[3]) if len(sys.argv) > 3 else 5.0
        frames = []
        n = int(round(seg * fps))
        for i in range(n):
            t = T0 + i / fps
            a = render("v1", t)
            b = render("ola", t)
            sep = np.full((4, W, 3), 255, dtype=np.uint8)
            frames.append(Image.fromarray(np.concatenate([a, sep, b], axis=0)))
            print("cuadro %d/%d" % (i + 1, n), flush=True)
        frames[0].save(os.path.join(AQUI, "ondula_v1_vs_oleaje.gif"), save_all=True, append_images=frames[1:],
                       duration=int(round(1000 / fps)), loop=0, optimize=False)
