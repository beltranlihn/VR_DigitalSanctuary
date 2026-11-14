# -*- coding: utf-8 -*-
"""render_transicion.py - imagenes de control de la propuesta, con el render por columnas de la tarea de escala
(valle_v2_diag_escala/render_valle.py, importado SOLO PARA LEER; el sombreado se sustituye en tiempo de ejecucion
por transicion.suelo, sin tocar ese archivo).
Vistas: frente (ojos, yaw 0, lente -2 grados, HFOV 90) y costado (ojos, yaw 90). Casos:
  A  escala P2 tal cual (C1, brillo rasante de la spec)
  B  P2 + ley de transicion + oleaje, C2, brillo de la spec
  C  P2 + ley + oleaje, C2, lobulo de tope plano exp(-(N.V/0,3)^4), Sheen 0,28   <- la propuesta
Salidas: rt_<vista>.png (tres paneles apilados) y rt_<vista>_zoom.png (recorte x2 alrededor del horizonte).
Tambien imprime el color del piso plano a 3-30 m (spec contra lobulo) para medir el cambio de aspecto."""
import math
import os
import sys

import numpy as np
from PIL import Image

import transicion as T

sys.path.insert(0, T.ESC)
import render_valle as rv  # noqa: E402  (solo lectura)

LOB = dict(T.L0, Sheen=0.28, SheenW=0.3, SheenP=4.0)
CASOS = [
    ("A  escala P2 tal cual (C1, sheen spec)", T.P2, T.ss3, T.L0, 0),
    ("B  P2 + ley + oleaje, C2, sheen spec", T.P2_LEY_OL, T.s5, T.L0, 0),
    ("C  P2 + ley + oleaje, C2, lobulo exp(-(NV/0,3)^4), Sheen 0,28", T.P2_LEY_OL, T.s5, LOB, 1),
]


def correr(P, st, L, sm, yaw):
    orig = T.mv.ground_color

    def gc(px, py, h, gx, gy, hf, cam, fogfun, L_=None, return_parts=False):
        return T.suelo(px, py, h, gx, gy, hf, P, L, sm, lambda D, z, cz, PP: fogfun(D, z, cz), cam=cam)
    T.mv.ground_color = gc
    try:
        img, kind, _ = rv.render_persp(lambda X, Y, t, PP: T.h_capas(X, Y, t, P, st), P, T.mv.fog_v2,
                                       yaw=yaw, shift_deg=-2.0 if yaw == 0 else 0.0, metaball=(yaw == 0))
    finally:
        T.mv.ground_color = orig
    return img


def main():
    AQ = T.AQUI
    for vista, yaw in (("frente", 0.0), ("costado", 90.0)):
        tiles, zooms = [], []
        for nombre, P, st, L, sm in CASOS:
            img = correr(P, st, L, sm, yaw)
            im = Image.fromarray((T.mv.srgb(img) * 255 + 0.5).astype(np.uint8))
            tiles.append(rv.etiqueta(im.copy(), nombre))
            z = im.crop((0, 330, 1052, 560)).resize((2104, 460), Image.LANCZOS)
            zooms.append(rv.etiqueta(z, nombre + "  (recorte x2, filas 330-560)"))
            if yaw == 0:
                f = 526.0
                cyh = 431 + f * math.tan(math.radians(-2.0))
                vals = []
                for d in (300, 500, 800, 1000, 1300, 2000, 3000):
                    row = int(round(cyh + f * 120.0 / d))
                    vals.append("%g m %s" % (d / 100, tuple(int(v) for v in np.asarray(im)[row, 300])))
                print("%-52s piso (col 300): %s" % (nombre, " | ".join(vals)))
        for lst, suf in ((tiles, ""), (zooms, "_zoom")):
            W = lst[0].width
            Hh = sum(t.height for t in lst) + 6 * (len(lst) - 1)
            out = Image.new("RGB", (W, Hh), (20, 20, 20))
            y = 0
            for t in lst:
                out.paste(t, (0, y))
                y += t.height + 6
            p = os.path.join(AQ, "rt_%s%s.png" % (vista, suf))
            out.save(p)
            print(p)


if __name__ == "__main__":
    main()
