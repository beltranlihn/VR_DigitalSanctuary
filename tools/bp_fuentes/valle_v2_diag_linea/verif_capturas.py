# -*- coding: utf-8 -*-
"""verif_capturas.py - control INDEPENDIENTE de "que linea es" sobre las tres capturas reales.

No usa el raycast del modelo: solo geometria de camara (fila -> rayo -> cruce con el plano z = 0 -> e de la
elipse de la spec) y el perfil de luminancia de la captura.
Por columna:
  - fila_e1   : primera fila (subiendo desde abajo) cuyo rayo cae en el plano con e >= 1 (borde del piso).
  - fila_pico : el MAXIMO de luminancia del piso subiendo desde abajo (el piso se aclara hacia el borde por el
                brillo rasante y despues cae): primer maximo local con caida >= 8 % en los 12 px de arriba.
  - caida     : Y(pico) -> Y(pico - 1 grado) y -> Y(pico - 2 grados), en % (Weber, luminancia lineal).
  - rampa     : pendiente media de ln Y en %/grado, 2 grados DEBAJO del pico (piso) y 1 grado ENCIMA (ladera).
Se descartan columnas tapadas por el metaball o los iconos del editor (pixeles casi grises o casi blancos).
Uso: python verif_capturas.py  (escribe verif_capturas_salida.txt)
"""
import math
import os

import numpy as np
from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
CAPS = os.path.dirname(AQUI)
W, H = 1052, 862
F = (W / 2) / math.tan(math.radians(45.0))            # 526 px
PXDEG = F * math.tan(math.radians(1.0))               # ~9,18 px por grado en el centro
VX, VA, VB = 350.0, 950.0, 600.0

CAMS = {
    "cap_valle_frente": dict(o=(0.0, 0.0, 120.0), yaw=0.0, pitch=-2.0),
    "cap_reposo_lado": dict(o=(380.0, -700.0, 70.0), yaw=90.0, pitch=0.0),
    "cap_exhala_lado": dict(o=(380.0, -700.0, 70.0), yaw=90.0, pitch=0.0),
}


def lin(s8):
    c = np.asarray(s8, float) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def rayo(o, yaw, pitch, col, row):
    y, p = math.radians(yaw), math.radians(pitch)
    Fw = np.array([math.cos(p) * math.cos(y), math.cos(p) * math.sin(y), math.sin(p)])
    R = np.array([-math.sin(y), math.cos(y), 0.0])
    U = np.array([-math.sin(p) * math.cos(y), -math.sin(p) * math.sin(y), math.cos(p)])
    d = Fw + ((col + 0.5 - W / 2) / F) * R - ((row + 0.5 - H / 2) / F) * U
    return d / np.linalg.norm(d)


def e_plano(o, d):
    if d[2] >= -1e-6:
        return np.inf, np.inf
    s = -o[2] / d[2]
    x, y = o[0] + s * d[0], o[1] + s * d[1]
    return math.hypot((x - VX) / VA, y / VB), math.hypot(x - o[0], y - o[1])


def main():
    out = []
    for nombre, cam in CAMS.items():
        img = np.asarray(Image.open(os.path.join(CAPS, nombre + ".png")).convert("RGB")).astype(float)
        o = np.array(cam["o"])
        Y = lin(img) @ np.array([0.2126, 0.7152, 0.0722])
        sat = img.max(-1) - img.min(-1)                          # el suelo y el cielo son azulados (sat > 35)
        hz = H / 2 - F * math.tan(math.radians(-cam["pitch"])) if cam["pitch"] else H / 2
        out.append("=" * 100)
        out.append("%s  camara %s yaw %.0f pitch %.0f  (horizonte en la fila %.1f, %.2f px/grado)" % (
            nombre, cam["o"], cam["yaw"], cam["pitch"], hz, PXDEG))
        out.append("  col | fila_e1 fila_pico  d(fila) | dist borde  bajo horiz | Y pico  caida 1 grado  2 grados |"
                   " rampa piso  rampa ladera (%/grado)")
        difs, c1, c2, rp, rl = [], [], [], [], []
        for c in range(20, W - 20, 24):
            # fila del borde por geometria pura
            fe1, adentro = None, False                         # borde LEJANO: e pasa de < 1 a >= 1 subiendo
            for r in range(H - 1, int(hz), -1):
                e, dist = e_plano(o, rayo(o, cam["yaw"], cam["pitch"], c, r))
                if e < 1.0:
                    adentro = True
                elif adentro:
                    fe1, dborde = r, dist
                    break
            if fe1 is None:
                continue
            # perfil de la captura (suavizado 1-2-1), con mascara de iconos / metaball
            col = Y[:, c]
            ys = np.convolve(col, [0.25, 0.5, 0.25], mode="same")
            lo, hi = fe1 - 40, min(fe1 + 80, H - 3)
            if (sat[lo:hi, c] < 35).any():
                continue
            pico = None
            for r in range(hi, lo, -1):                          # subiendo desde abajo
                if ys[r] >= ys[r + 1] and ys[r] >= ys[r - 1]:
                    ventana = ys[max(r - 12, 0):r]
                    if ventana.size and (ys[r] - ventana.min()) / ys[r] >= 0.08:
                        pico = r
                        break
            if pico is None:
                continue
            k1, k2 = int(round(PXDEG)), int(round(2 * PXDEG))
            if (sat[pico - k2:pico + 1, c] < 35).any():
                continue
            caida1 = 100 * (ys[pico - k1] / ys[pico] - 1)
            caida2 = 100 * (ys[pico - k2] / ys[pico] - 1)
            lY = np.log(np.maximum(ys, 1e-6))
            rpiso = 100 * (lY[pico] - lY[pico + k2]) / 2.0        # sube hacia el borde (%/grado)
            rlad = 100 * (lY[pico - k1] - lY[pico]) / 1.0
            el = math.degrees(math.atan2(o[2], dborde))
            out.append("  %4d | %6d %8d %8d  | %7.1f m  %6.2f deg  | %.3f  %8.1f %%  %7.1f %% | %8.1f  %10.1f" % (
                c, fe1, pico, pico - fe1, dborde / 100, el, ys[pico], caida1, caida2, rpiso, rlad))
            difs.append(pico - fe1)
            c1.append(caida1)
            c2.append(caida2)
            rp.append(rpiso)
            rl.append(rlad)
        if difs:
            difs = np.array(difs)
            out.append("  RESUMEN %d columnas: pico - fila_e1 mediana %+.1f px (p10 %+.0f, p90 %+.0f) = %.2f grados;"
                       " caida en 1 grado mediana %.0f %% (min %.0f, max %.0f); en 2 grados %.0f %%" % (
                           difs.size, np.median(difs), np.percentile(difs, 10), np.percentile(difs, 90),
                           np.median(difs) / PXDEG, np.median(c1), np.max(c1), np.min(c1), np.median(c2)))
            out.append("           rampa del piso %.1f %%/grado (sube hacia el borde) vs ladera %.1f %%/grado:"
                       " QUIEBRE de %.0f %%/grado en la fila del borde" % (
                           np.median(rp), np.median(rl), np.median(np.array(rp) - np.array(rl))))
    txt = "\n".join(out)
    print(txt)
    with open(os.path.join(AQUI, "verif_capturas_salida.txt"), "w", encoding="utf-8") as fh:
        fh.write(txt + "\n")


if __name__ == "__main__":
    main()
