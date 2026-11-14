# Frecuencia de bordes de oclusion bajo el horizonte en el FRENTE (az -60..60, fuera del metaball |az| > 17),
# 5 min cada 5 s, sin sombreado (solo geometria). Distancia vista salta > 1,25x entre filas vecinas (0,04 grados).
import numpy as np, vrender as vr
m = vr.Modelo("v2")
import sys
EZ = float(sys.argv[1])
eye = np.array([0.0, 0.0, EZ])
az = np.concatenate([np.arange(-60.0, -17.0, 0.5), np.arange(17.5, 60.01, 0.5)])
el = np.arange(0.5, -6.0, -0.04)
sl = np.broadcast_to(np.tan(np.radians(el))[:, None], (el.size, az.size)).copy()
J = 3000
rho = 20.0 * np.power(64100.0 / 20.0, np.arange(J) / (J - 1.0))
res = []
for t in np.arange(0.0, 300.0, 10.0):
    a = np.radians(az)
    X = rho[:, None] * np.cos(a)[None, :]; Y = rho[:, None] * np.sin(a)[None, :]
    s = (m.h(X, Y, t) - EZ) / rho[:, None]
    M = np.maximum.accumulate(s, axis=0)
    D = np.empty_like(sl)
    for k in range(az.size):
        j = np.searchsorted(M[:, k], sl[:, k]); D[:, k] = np.where(j < J, rho[np.clip(j, 0, J - 1)], np.inf)
    ok = np.isfinite(D[:-1]) & np.isfinite(D[1:])
    edge = ok & (D[:-1] / D[1:] > 1.25)
    res.append(edge.any(0))
res = np.array(res)
print("frente (|az| 17..60): fraccion azimut x tiempo con borde de oclusion bajo el horizonte: %.1f %%" % (100 * res.mean()))
print("instantes con al menos 10 grados de borde en el frente: %.0f %%" % (100 * (res.sum(1) * 0.5 >= 10).mean()))
print("grados de borde por instante: p10 %.1f p50 %.1f p90 %.1f max %.1f (de 86 grados visibles)" % tuple(np.percentile(res.sum(1) * 0.5, [10, 50, 90, 100])))
