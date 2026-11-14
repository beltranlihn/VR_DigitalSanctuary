# -*- coding: utf-8 -*-
"""diag_capturas.py - que linea es la que se ve "muy marcada" en las capturas reales del editor.

Para cada captura (camara conocida, HFOV 90, 1052x862):
  1. perfil vertical de luminancia de la captura en varias columnas; ubica el QUIEBRE (fila donde el
     perfil pasa de meseta a rampa: maximo de la segunda diferencia) y el salto (dY por fila).
  2. raycast del modelo v1 en las mismas columnas (port exacto de ValleyGradVS/ValleyPS): fila donde el
     rayo pasa de e < 1 (piso plano) a e >= 1 (nacen las colinas), distancia, pendiente, terminos del
     sombreado a ambos lados.
  3. render del modelo a 1/2 resolucion al lado de la captura (comparacion visual) -> cmp_<captura>.png
Uso: python diag_capturas.py
"""
import math
import os
import sys

import numpy as np
from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from modelo_v1 import P, lin, luma, rayos, render, srgb  # noqa: E402

CAPS = os.path.dirname(AQUI)
W, H = 1052, 862
CAMS = {
    "cap_valle_frente": dict(o=np.array([0.0, 0.0, 120.0]), yaw=0.0, pitch=-2.0, cols=[200, 330, 526, 700, 980]),
    "cap_reposo_lado": dict(o=np.array([380.0, -700.0, 70.0]), yaw=90.0, pitch=0.0, cols=[60, 200, 330, 526, 980]),
}
T_EDITOR = 0.0


def perfil_captura(img, c):
    Y = luma(lin(img[:, c, :]))
    return Y


def quiebre(Y, r0, r1):
    """fila del quiebre: maximo de |segunda diferencia| entre r0 y r1 (perfil suavizado 1-2-1)."""
    Ys = np.convolve(Y, [0.25, 0.5, 0.25], mode="same")
    d2 = np.zeros_like(Ys)
    d2[1:-1] = Ys[2:] - 2 * Ys[1:-1] + Ys[:-2]
    k = r0 + int(np.argmax(np.abs(d2[r0:r1])))
    return k, d2


def main():
    for name, cam in CAMS.items():
        img = np.asarray(Image.open(os.path.join(CAPS, name + ".png")).convert("RGB")).astype(float)
        o = cam["o"]
        print("=" * 100)
        print("%s  camara %s yaw %g pitch %g" % (name, o, cam["yaw"], cam["pitch"]))
        f = (W / 2) / math.tan(math.radians(45))
        hor = H / 2 - f * math.tan(math.radians(-cam["pitch"])) if cam["pitch"] else H / 2
        print("  horizonte (el = 0) en la fila %.1f; %.2f px por grado en el centro" % (hor, f * math.pi / 180))
        for c in cam["cols"]:
            filas = np.arange(int(hor) + 2, H)
            d = rayos(cam["yaw"], cam["pitch"], W, H, 90.0, filas=filas, cols=[c])[:, 0, :]
            col, info, pp = render(o, d[:, None, :].reshape(-1, 1, 3), T_EDITOR, parts=True)
            col = col[:, 0]
            e = info["e"][:, 0]
            Ym = luma(col)
            Yc = perfil_captura(img, c)[filas]
            # fila (primera desde abajo) donde e cruza 1: e decrece hacia abajo
            idx = np.where((e[:-1] >= 1.0) & (e[1:] < 1.0))[0]
            if idx.size == 0:
                print("  col %d: el modelo no cruza e = 1 en esta columna" % c)
                continue
            ke = idx[-1]  # la ultima (la mas baja): borde del piso visto de frente
            r_e1 = filas[ke] + 0.5
            k_cap, d2 = quiebre(Yc, max(ke - 40, 0), min(ke + 40, len(Yc) - 2))
            dist = info["dist"][ke + 1, 0]
            dep = math.degrees(math.atan2(o[2] - 0.0, dist))
            print("  col %4d: modelo e=1 entre filas %d/%d (dist %.0f cm, %.2f deg bajo el horizonte, x %.0f y %.0f); "
                  "quiebre de la captura en la fila %d" % (c, filas[ke], filas[ke + 1], dist, dep,
                                                            info["x"][ke + 1, 0], info["y"][ke + 1, 0], filas[k_cap]))
            # tabla alrededor del borde: filas -12 .. +8
            print("     fila   e      h(cm)  pend(deg) dist(cm)  N.V   fres  sheen  wrap  slopek  fog  |  Y modelo  Y captura  | sRGB mod / cap")
            for k in range(max(ke - 14, 0), min(ke + 9, len(filas))):
                if not info["hit"][k, 0]:
                    continue
                sm = np.round(srgb(col[k]) * 255).astype(int)
                sc = img[filas[k], c].astype(int)
                print("     %4d  %5.3f %7.1f  %6.1f  %7.0f  %5.3f %5.3f %5.3f %5.3f %5.3f %5.3f | %8.4f  %8.4f  | %s / %s" % (
                    filas[k], e[k], info["h"][k, 0], info["slope"][k, 0], info["dist"][k, 0], pp["NV"][k, 0],
                    pp["fres"][k, 0], pp["sheen"][k, 0], pp["wrap"][k, 0], pp["slopek"][k, 0], pp["fog"][k, 0],
                    Ym[k], Yc[k], tuple(sm), tuple(sc)))
        # comparacion visual a 1/2 resolucion
        dd = rayos(cam["yaw"], cam["pitch"], W, H, 90.0, filas=np.arange(0, H, 2), cols=np.arange(0, W, 2))
        colm, _ = render(o, dd, T_EDITOR)
        mod8 = (np.round(srgb(colm) * 255)).astype(np.uint8)
        cap8 = img[::2, ::2].astype(np.uint8)
        both = np.concatenate([cap8, mod8], axis=1)
        Image.fromarray(both).save(os.path.join(AQUI, "cmp_%s.png" % name))
        print("  -> cmp_%s.png (izquierda captura, derecha modelo v1)" % name)


if __name__ == "__main__":
    main()
