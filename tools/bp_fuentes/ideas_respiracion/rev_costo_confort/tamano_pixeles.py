# -*- coding: utf-8 -*-
"""Revisor: tamano en PIXELES de las motas visibles en la Quest 3 (centelleo sub-pixel).
El PS dibuja (1 - r^2)^2 en el quad: el ancho a media altura (FWHM) es 0,54 x el lado del quad. Si el FWHM queda por
debajo de ~2 px, el brillo pico de la mota depende de donde cae el centro respecto de los pixeles (el PS se evalua
UNA vez por pixel; el MSAA 4x suaviza el borde del quad, no el sombreado interior) -> centelleo al moverse."""
import os, sys
import numpy as np
sys.path.insert(0, r"C:\Users\beltr\Desktop\Alma Digital Studio\Projects\VR Unreal\.claude\skills\unreal-vr\scripts")
import breath_air_model as am
sd = am.seeds(); eye = np.zeros(3)
def pv(T, Ein, Eout):
    st = am.AirBP(eye, 0.0, 0.0)
    st.Tin, st.Tout, st.Fout, st.Ein, st.Eout, st.Glob = T, T, 1.5, Ein, Eout, 1.0
    return st.push(eye, 0.0, 0.0)
lines = []
for ppd in (20.0, 25.0):
    for nombre, flag, Ein, Eout in (("inhalar", 0, 1, 0), ("exhalar", 1, 0, 1)):
        fw, w = [], []
        for T in np.linspace(0, 1, 40, endpoint=False):
            r = am.vs(sd, pv(T, Ein, Eout))
            m = (sd["flag"] == flag) & (r["al"] > 0.05)
            lado = np.degrees(2 * r["hsz"][m] / r["dist"][m]) * ppd
            fw += (0.54 * lado).tolist(); w += r["al"][m].tolist()
        fw, w = np.array(fw), np.array(w)
        # variacion del pico muestreado: centro a medio pixel en x e y -> r^2 = 2*(0,5/(lado/2))^2
        lado = fw / 0.54
        r2 = 2 * (0.5 / (lado / 2)) ** 2
        pico_min = np.clip(1 - r2, 0, 1) ** 2
        lines.append("PPD %.0f %s: FWHM del punto (px) mediana %.2f p10 %.2f p90 %.2f | %% del alfa con FWHM < 2 px: %.0f%% | "
                     "brillo pico peor caso / mejor caso (centro a medio pixel): mediana %.2f (p10 %.2f)"
                     % (ppd, nombre, np.median(fw), np.percentile(fw, 10), np.percentile(fw, 90),
                        100 * w[fw < 2].sum() / w.sum(), np.median(pico_min), np.percentile(pico_min, 10)))
txt = "\n".join(lines); print(txt)
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tamano_pixeles_resultados.txt"), "w", encoding="utf-8").write(txt + "\n")
