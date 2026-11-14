# -*- coding: utf-8 -*-
"""render_valle.py - render por COLUMNAS (tecnica "voxel space") del campo de altura del valle, con el
sombreado de ValleyPS portado a numpy (modelo_valle.py, controlado contra la seccion 12 de la spec).

Cada columna de pixeles es un plano vertical que pasa por el ojo; se marcha la distancia horizontal de cerca a
lejos y cada muestra pinta las filas que todavia no estaban tapadas (oclusion exacta del campo de altura).
Camara sin pitch pero con DESPLAZAMIENTO de lente (las verticales quedan verticales): shift -2 deg equivale al
pitch -2 de cap_valle_frente.png. El metaball es una esfera de referencia (no el raymarch real).

Uso:  python render_valle.py            -> genera las imagenes del diagnostico en esta carpeta
"""
import math
import os
import sys

import numpy as np
from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import modelo_valle as mv  # noqa: E402

MB_C = np.array([380.0, 0.0, 125.0])
MB_R = 110.0
MB_LIGHT = (0.92, 0.945, 1.0)
MB_SHADOW = (0.026, 0.013, 0.12)
MB_L = np.array([0.42, -0.57, 0.71]) / np.linalg.norm([0.42, -0.57, 0.71])


def _columnas(hfun, P, fogfun, az_cols, cam, t, J, rho_min, row_of, H, xform_cos):
    """az_cols: azimut (rad) de cada columna. row_of(h_rel, rho, c) -> fila (float). Devuelve (idx, colores)."""
    W = az_cols.size
    rho = rho_min * np.power(P["R_MAX"] / rho_min, np.arange(J) / (J - 1.0))  # geometrico, ~0,3 % por paso
    ca, sa = np.cos(az_cols), np.sin(az_cols)
    X = cam[0] + rho[:, None] * ca[None, :]
    Y = cam[1] + rho[:, None] * sa[None, :]
    inside = np.hypot(X, Y) <= P["R_MAX"]
    h, hf = hfun(X, Y, t, P)
    gx, gy = mv.grad_fd(hfun, X, Y, t, P, d=0.5)
    rows = row_of(h - cam[2], rho[:, None], xform_cos[None, :])
    rows = np.where(inside, rows, np.inf)
    cov = np.minimum.accumulate(np.ceil(rows), axis=0)  # fila mas alta cubierta hasta la muestra j
    col = mv.ground_color(X, Y, h, gx, gy, hf, cam, lambda D, z, cz: fogfun(D, z, cz, P))
    idx = np.full((H, W), J, dtype=np.int64)
    prow = np.arange(H, dtype=np.float64)
    for u in range(W):
        idx[:, u] = np.searchsorted(-cov[:, u], -prow, side="left")
    return idx, col


def render_persp(hfun, P, fogfun, W=1052, H=862, hfov=90.0, shift_deg=-2.0, yaw=0.0, cam=(0.0, 0.0, 120.0),
                 t=0.0, J=2600, metaball=True):
    cam = np.asarray(cam, dtype=np.float64)
    f = (W / 2.0) / math.tan(math.radians(hfov / 2.0))
    cyh = H / 2.0 + f * math.tan(math.radians(shift_deg))  # fila del horizonte (shift negativo = mira abajo)
    u = np.arange(W) + 0.5 - W / 2.0
    azr = np.arctan2(u, f)
    az = math.radians(yaw) + azr
    cosr = np.cos(azr)

    def row_of(hrel, rho, c):
        return cyh - f * hrel / (rho * c) - 0.5

    idx, col = _columnas(hfun, P, fogfun, az, cam, t, J, 30.0, row_of, H, cosr)
    img = np.zeros((H, W, 3))
    # rayos por pixel (para cielo y metaball)
    fw = np.array([math.cos(math.radians(yaw)), math.sin(math.radians(yaw)), 0.0])
    rt = np.array([-math.sin(math.radians(yaw)), math.cos(math.radians(yaw)), 0.0])
    up = np.array([0.0, 0.0, 1.0])
    pu = (np.arange(W) + 0.5 - W / 2.0)[None, :, None]
    pv = (cyh - (np.arange(H) + 0.5))[:, None, None]
    d = fw * f + rt * pu + up * pv
    d = d / np.linalg.norm(d, axis=-1, keepdims=True)
    sky = mv.sky_color(d)
    ground = idx < col.shape[0]
    jj = np.minimum(idx, col.shape[0] - 1)
    gcol = col[jj, np.arange(W)[None, :]]
    img = np.where(ground[..., None], gcol, sky)
    kind = np.where(ground, 1, 0)
    if metaball:
        oc = cam - MB_C
        b = (d * oc).sum(-1)
        c = float(oc @ oc) - MB_R * MB_R
        disc = b * b - c
        hit = disc > 0
        tt = -b - np.sqrt(np.maximum(disc, 0))
        p = cam + d * tt[..., None]
        n = (p - MB_C) / MB_R
        k = mv.sat((n * MB_L).sum(-1) * 0.5 + 0.5)
        mcol = mv.lerp(np.array(MB_SHADOW), np.array(MB_LIGHT), k[..., None])
        img = np.where(hit[..., None], mcol, img)
        kind = np.where(hit, 2, kind)
    return img, kind, idx


def render_pano(hfun, P, fogfun, px_per_deg=6.0, el_top=22.0, el_bot=-14.0, cam=(0.0, 0.0, 120.0), t=0.0, J=2600):
    """Panorama CILINDRICO de 360 grados (columna = azimut -180..180, fila = tan(elevacion))."""
    cam = np.asarray(cam, dtype=np.float64)
    W = int(360 * px_per_deg)
    fp = px_per_deg * 180.0 / math.pi
    ytop = fp * math.tan(math.radians(el_top))
    H = int(ytop + fp * math.tan(math.radians(-el_bot)))
    az = np.radians(np.arange(W) / px_per_deg - 180.0 + 0.5 / px_per_deg)

    def row_of(hrel, rho, c):
        return ytop - fp * hrel / rho - 0.5

    idx, col = _columnas(hfun, P, fogfun, az, cam, t, J, 30.0, row_of, H, np.ones_like(az))
    el = np.arctan((ytop - (np.arange(H) + 0.5)) / fp)
    d = np.stack([np.cos(el)[:, None] * np.cos(az)[None, :], np.cos(el)[:, None] * np.sin(az)[None, :],
                  np.broadcast_to(np.sin(el)[:, None], (H, W))], -1)
    sky = mv.sky_color(d)
    ground = idx < col.shape[0]
    jj = np.minimum(idx, col.shape[0] - 1)
    img = np.where(ground[..., None], col[jj, np.arange(W)[None, :]], sky)
    return img, ytop, fp


def to_png(img, path):
    Image.fromarray((mv.srgb(img) * 255.0 + 0.5).astype(np.uint8)).save(path)


def etiqueta(im, texto, xy=(12, 10)):
    from PIL import ImageDraw
    dr = ImageDraw.Draw(im)
    x, y = xy
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            dr.text((x + dx, y + dy), texto, fill=(40, 40, 60))
    dr.text((x, y), texto, fill=(255, 255, 255))
    return im


if __name__ == "__main__":
    salida = AQUI
    # 1) CONTROL: v1 con la camara de cap_valle_frente.png, lado a lado con la captura real
    img1, kind1, _ = render_persp(mv.h_v1, mv.P1, mv.fog_v1)
    to_png(img1, os.path.join(salida, "r_v1_frente.png"))
    cap = Image.open(os.path.join(salida, "..", "cap_valle_frente.png")).convert("RGB")
    r1 = Image.open(os.path.join(salida, "r_v1_frente.png"))
    lado = Image.new("RGB", (cap.width + r1.width + 8, max(cap.height, r1.height)), (20, 20, 20))
    lado.paste(cap, (0, 0))
    lado.paste(r1, (cap.width + 8, 0))
    etiqueta(lado, "CAPTURA UNREAL (v1)", (12, 10))
    etiqueta(lado, "MODELO NUMPY (v1), misma camara", (cap.width + 20, 10))
    lado.save(os.path.join(salida, "ctl_v1_captura_vs_modelo.png"))
    print("RENDER control listo")
