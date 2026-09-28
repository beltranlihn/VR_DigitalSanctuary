# -*- coding: utf-8 -*-
"""vida_legibilidad.py - cuantas motas de polvo se DISTINGUEN en la foto desde los ojos (rev. 2 de la capa de vida).

Compone el polvo (vida_model, tamano angular real, mezcla en lineal) sobre el cuadro 'clave_calma' del valle (el render de
render_vida_valle.py) y mide, por mota, el contraste de su pixel central contra el mismo pixel SIN polvo (niveles de 8
bits, promedio de los canales). Compara juegos de perillas: el visible (default), el sutil (rev. 1) y variantes.
La foto es 11,7 px/grado (el visor ~16, con estereo y paralaje): cuenta de MINIMA, no lo que se ve en el visor.
Uso:  python vida_legibilidad.py   (necesita vida/preview/clave_calma.png: sim_vida.py linea + render_vida_valle.py)
"""
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import sim_vida as sv  # noqa: E402
import vida_model as vm  # noqa: E402


def contar(mat, pausa=False):
    base = sv.cargar("clave_calma")
    img = base.copy()
    bp = vm.VidaBP()
    bp.Glob = 1.0
    old = dict(vm.MAT)
    vm.MAT.update(mat)
    try:
        r = sv.dust_centros(bp.push_dust(), (0.0, 0.0, 0.0), mat=mat)
        sv.dibujar_polvo(img, r, sv.CAM_KEY)
    finally:
        vm.MAT.clear()
        vm.MAT.update(old)
    x, y, z, f = sv.proyectar(r["P"], sv.CAM_KEY)
    h, w = img.shape[:2]
    a8 = np.round(sv.lin_a_srgb(img) * 255.0).mean(2)
    b8 = np.round(sv.lin_a_srgb(base) * 255.0).mean(2)
    d = np.abs(a8 - b8)
    vals = []
    for i in np.where((r["al"] > 0.002) & (z > 1.0))[0]:
        xi, yi = int(x[i]), int(y[i])
        if 0 <= xi < w and 0 <= yi < h:
            vals.append(d[yi, xi])
    vals = np.array(vals)
    return {k: int((vals >= k).sum()) for k in (2, 5, 10)}


def main():
    juegos = [("visible (default rev. 2)", {}),
              ("sutil (tabla 5.3)", dict(vm.PRESET_SUTIL)),
              ("rev. 1 (sutil + los colores del aliento)", dict(vm.PRESET_SUTIL, ColLit=(1.0, 0.9, 0.92), ColDim=(0.62, 0.66, 0.92))),
              ("visible con el ColDim gris (0,8 0,78 0,86)", dict(ColDim=(0.80, 0.78, 0.86), SunBase=0.45))]
    for nom, m in juegos:
        c = contar(m)
        print("%-44s motas que se distinguen en la foto: >= 2 niveles %4d | >= 5 %4d | >= 10 %4d" % (nom, c[2], c[5], c[10]))


if __name__ == "__main__":
    main()
