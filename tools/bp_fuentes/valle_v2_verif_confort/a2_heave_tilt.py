# -*- coding: utf-8 -*-
"""a2_heave_tilt.py - de skyline_E.npy (parte A): componentes COHERENTES de la silueta dentro de un campo de 90 grados
(el campo del usuario) para cada yaw cada 15 grados: sube-y-baja medio (heave, deg/s) e inclinacion (roll aparente:
pendiente de la regresion lineal E(az), deg de diferencia entre bordes y su velocidad)."""
import numpy as np
E = np.load("skyline_E.npy")          # (8, 81, 1440), DT 0.25, az 0..360 cada 0.25
DT = 0.25
AZ = np.arange(0, 360, 0.25)
res = []
for yaw in range(0, 360, 15):
    rel = ((AZ - yaw + 180) % 360) - 180
    m = np.abs(rel) <= 45
    x = rel[m]
    Ef = E[:, :, m]
    heave = Ef.mean(2)                               # (8, 81)
    vh = np.gradient(heave, DT, axis=1)
    babs = np.abs(np.gradient(Ef, DT, axis=1)).mean(2)
    # inclinacion: pendiente * 90 = diferencia de altura entre los bordes del campo
    xm = x - x.mean()
    slope = (Ef * xm).sum(2) / (xm * xm).sum()
    tilt = slope * 90.0
    vt = np.gradient(tilt, DT, axis=1)
    res.append((yaw, np.abs(vh).max(), np.median(np.abs(vh) / (babs + 1e-9)), np.ptp(tilt, axis=1).max(),
                np.abs(vt).max(), np.abs(tilt).max()))
res = np.array(res)
print("yaw | heave max deg/s | heave/|dE/dt| mediana | rango de inclinacion en 20 s (deg) | vel. inclinacion max deg/s | |incl| max")
for r in res:
    print("%3d | %.3f | %.2f | %.2f | %.3f | %.2f" % tuple(r))
print("PEOR: heave %.3f deg/s, incl. vel %.3f deg/s, rango incl. %.2f deg en 20 s" % (res[:,1].max(), res[:,4].max(), res[:,3].max()))
