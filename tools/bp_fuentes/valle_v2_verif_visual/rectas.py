# Tramos continuos de borde de oclusion (escalon >= 3 niveles): largo en grados de azimut, rango de elevacion y
# pendiente media (una linea "recta horizontal" tiene rango de elevacion chico en un tramo largo).
import numpy as np
from PIL import Image
import vrender as vr
for tag in ("v2_t0_p25", "v2_t20_p25", "v2_t40_p25"):
    best = np.load("bordes_%s_best.npy" % tag); elb = np.load("bordes_%s_el.npy" % tag)
    on = best >= 3
    W = on.size
    # recorrer tramos con continuidad de elevacion (salto < 0,2 grados entre columnas vecinas)
    tramos = []
    i = 0
    while i < W:
        if not on[i]:
            i += 1; continue
        j = i
        while j + 1 < W and on[j + 1] and abs(elb[j + 1] - elb[j]) < 0.2:
            j += 1
        tramos.append((i, j))
        i = j + 1
    info = []
    for (a, b) in tramos:
        n = b - a + 1
        if n < 25: continue
        e = elb[a:b + 1]
        info.append((n / 25.0, -180 + a / 25.0, -180 + b / 25.0, e.min(), e.max(), np.median(best[a:b + 1])))
    info.sort(reverse=True)
    print("== %s: %d tramos de >= 1 grado; los 6 mas largos:" % (tag, len(info)))
    for (L, a0, a1, e0, e1, st) in info[:6]:
        print("   %5.1f grados (az %+6.1f .. %+6.1f)  elevacion %.2f .. %.2f deg  escalon mediano %.1f niveles" % (L, a0, a1, e0, e1, st))
    # imagen: bordes marcados en rojo sobre la panorama (banda -4..+10 grados)
    im = np.asarray(Image.open("pano_%s.png" % tag)).copy()
    rows = np.round((14.0 - elb) * 25.0 - 0.5).astype(int)
    for c in np.flatnonzero(on):
        r = rows[c]
        im[max(r - 2, 0):r + 3, c] = (255, 30, 20)
    Image.fromarray(im[100:475]).resize((W // 4, 375 // 4 * 2), Image.BILINEAR).save("bordes_marcados_%s.png" % tag)
