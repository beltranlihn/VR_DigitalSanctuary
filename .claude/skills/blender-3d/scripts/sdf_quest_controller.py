# sdf_quest_controller.py - el mando de la obra MODELADO DESDE CERO (pedido de Beltran 2026-09-29: el remallado del
# Touch Plus oficial quedaba deformado; "modelalo desde cero"). Campo de distancia (SDF) con union suave -> superficie
# por marching cubes (skimage, Python del sistema) -> OBJ. Lo termina gen_quest_controller2.py en Blender (decimado,
# normales, UV, mascara de tapa, export).
# Forma y medidas tomadas del Touch Plus (solo como REFERENCIA de proporciones y agarre, en su mismo marco, cm):
#   cabeza = disco redondeado (tapa arriba, inclinada) · mango = cono-capsula eliptico que baja hacia atras (+Y, -Z)
#   union suave entre ambos (cuello organico) · SIN botones · gatillo = paleta curva aparte, adelante (-Y) bajo la cabeza.
# Uso: python sdf_quest_controller.py <outdir>
import sys

import numpy as np
from skimage import measure

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
RES = 0.05                                     # cm (0,5 mm)

# --- cabeza ---
HEAD_C = np.array([0.70, 0.05, -0.40])
HEAD_N = np.array([0.06, 0.19, 0.98]); HEAD_N /= np.linalg.norm(HEAD_N)
HEAD_R, HEAD_HH, HEAD_RE = 3.25, 0.80, 0.70   # radio, media altura, redondeo del canto
HEAD_DOME = 0.18                               # abombado de la tapa
# --- mango: tubo CURVO (bezier cuadratica) de seccion eliptica que se afina ---
GRIP_P0 = np.array([0.40, 0.30, -1.70])        # arranque (dentro de la cabeza)
GRIP_P1 = np.array([0.30, 3.60, -3.10])        # control (curva el mango hacia atras)
GRIP_P2 = np.array([-0.95, 6.35, -6.05])       # centro de la punta
GRIP_RA, GRIP_RB = 1.72, 1.22                  # radios arriba / punta
GRIP_SX = 0.95                                 # achatado lateral
GRIP_N = 16                                    # tramos de la curva
BLEND = 1.9                                    # union suave cabeza-mango (cuello organico)
# --- menton: volumen bajo el frente de la cabeza, detras del gatillo ---
CHIN_C = np.array([1.05, -0.95, -2.05])
CHIN_R = np.array([1.35, 1.05, 1.25])          # semiejes del elipsoide
CHIN_BLEND = 1.2
# --- gatillo ---
TRIG_C = np.array([1.15, -2.20, -1.95])        # centro
TRIG_W, TRIG_H, TRIG_T = 1.15, 1.55, 0.40      # medio ancho (X), media altura, medio espesor
TRIG_BEND = 3.0                                # radio de curvatura (alrededor de X)
TRIG_TILT = np.radians(24.0)                   # inclinacion: la cara mira adelante-abajo
TRIG_RE = 0.34


def frame(n):
    a = np.array([1.0, 0, 0]) if abs(n[0]) < 0.9 else np.array([0, 1.0, 0])
    u = np.cross(n, a); u /= np.linalg.norm(u)
    return u, np.cross(n, u)


def sd_head(P):
    u, v = frame(HEAD_N)
    d = P - HEAD_C
    z = d @ HEAD_N
    x, y = d @ u, d @ v
    r = np.sqrt(x * x + y * y)
    z = z - HEAD_DOME * (1.0 - np.clip(r / HEAD_R, 0, 1) ** 2)          # tapa abombada
    qx = r - HEAD_R + HEAD_RE
    qz = np.abs(z) - HEAD_HH + HEAD_RE
    return np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qz, 0) ** 2) + np.minimum(np.maximum(qx, qz), 0) - HEAD_RE


def sd_grip(P):
    """Tubo sobre una bezier cuadratica: minimo sobre GRIP_N tramos de capsula con radio interpolado."""
    ts = np.linspace(0, 1, GRIP_N + 1)
    C = [(1 - t) ** 2 * GRIP_P0 + 2 * (1 - t) * t * GRIP_P1 + t * t * GRIP_P2 for t in ts]
    R = [GRIP_RA + (GRIP_RB - GRIP_RA) * t ** 1.4 for t in ts]
    Q = P.copy()
    Q[:, 0] = (P[:, 0] - GRIP_P1[0]) / GRIP_SX + GRIP_P1[0]          # seccion eliptica
    best = np.full(len(P), 1e9, np.float32)
    for i in range(GRIP_N):
        a, b = C[i].copy(), C[i + 1].copy()
        a[0] = (a[0] - GRIP_P1[0]) / GRIP_SX + GRIP_P1[0]
        b[0] = (b[0] - GRIP_P1[0]) / GRIP_SX + GRIP_P1[0]
        ab = b - a
        h = np.clip(((Q - a) @ ab) / (ab @ ab), 0, 1)
        d = np.linalg.norm(Q - a - np.outer(h, ab), axis=1) - (R[i] + (R[i + 1] - R[i]) * h)
        best = np.minimum(best, d)
    return best


def sd_chin(P):
    q = (P - CHIN_C) / CHIN_R
    k0 = np.linalg.norm(q, axis=1)
    k1 = np.linalg.norm(q / CHIN_R, axis=1)
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-6)


def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b + (a - b) * h - k * h * (1 - h)


def sd_trigger(P):
    d = P - TRIG_C
    # rotar por la inclinacion alrededor de X
    c, s = np.cos(TRIG_TILT), np.sin(TRIG_TILT)
    y = d[:, 1] * c - d[:, 2] * s
    z = d[:, 1] * s + d[:, 2] * c
    x = d[:, 0]
    # doblar la paleta alrededor de un eje X a TRIG_BEND detras de la cara
    yb = y - TRIG_BEND
    rr = np.sqrt(yb * yb + z * z)
    ang = np.arctan2(z, -yb)
    yy = TRIG_BEND - rr                      # espesor radial
    zz = ang * TRIG_BEND                     # largo sobre el arco
    qx = np.abs(x) - TRIG_W + TRIG_RE
    qy = np.abs(yy) - TRIG_T + min(TRIG_RE, TRIG_T * 0.9)
    qz = np.abs(zz) - TRIG_H + TRIG_RE
    re = min(TRIG_RE, TRIG_T * 0.9)
    q = np.stack([np.maximum(qx, 0), np.maximum(qy, 0), np.maximum(qz, 0)], 1)
    return np.linalg.norm(q, axis=1) + np.minimum(np.maximum(np.maximum(qx, qy), qz), 0) - re


def march(fn, lo, hi, name):
    xs = np.arange(lo[0], hi[0], RES); ys = np.arange(lo[1], hi[1], RES); zs = np.arange(lo[2], hi[2], RES)
    G = np.stack(np.meshgrid(xs, ys, zs, indexing='ij'), -1).reshape(-1, 3)
    D = np.empty(len(G), np.float32)
    for i in range(0, len(G), 2_000_000):
        D[i:i + 2_000_000] = fn(G[i:i + 2_000_000])
    D = D.reshape(len(xs), len(ys), len(zs))
    v, f, n, _ = measure.marching_cubes(D, 0.0, spacing=(RES, RES, RES), gradient_direction='ascent')
    v += lo
    with open(f"{OUT}/{name}.obj", "w") as fh:
        for p in v:
            fh.write("v %.5f %.5f %.5f\n" % (p[0] / 100, p[1] / 100, p[2] / 100))     # a metros
        for t in f:
            fh.write("f %d %d %d\n" % (t[0] + 1, t[2] + 1, t[1] + 1))
    print("SDF_OK", name, "verts", len(v), "tris", len(f), "bbox_cm", v.min(0).round(2), v.max(0).round(2))


body = lambda P: smin(smin(sd_head(P), sd_grip(P), BLEND), sd_chin(P), CHIN_BLEND)
march(body, np.array([-3.4, -4.0, -8.0]), np.array([4.8, 8.2, 1.9]), "qc_body_R")
march(sd_trigger, np.array([-0.6, -4.2, -4.4]), np.array([3.0, 0.2, 0.8]), "qc_trigger_R")
