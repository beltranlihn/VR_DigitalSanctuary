# Uso: python margen.py '<json>'  -> margen de la silueta sobre el borde de la malla en 30 min, ojos de 1,0 a 2,1 m.
import math, sys, json, numpy as np, vexp as vm
over = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
q = vm.params(**over)
az = np.radians(np.arange(0, 360, 1.0))
J = 2400
rho = 3000.0 * np.power(64000.0 / 3000.0, np.arange(J) / (J - 1.0))
X = rho[:, None] * np.cos(az)[None, :]; Y = rho[:, None] * np.sin(az)[None, :]
res = {}
worst = (99, None)
for t in np.arange(0.0, 1800.01, 30.0):
    H = vm.valley_h(X, Y, t, q)
    for ez in (100.0, 120.0, 160.0, 200.0, 210.4):
        e = np.degrees(np.arctan2(H - ez, rho[:, None]))
        j = np.argmax(e, axis=0)
        sil = e[j, np.arange(az.size)]
        borde = math.degrees(math.atan2(-ez, 64000.0))
        m = float((sil - borde).min())
        dmax = float(rho[j].max()) / 100
        k = res.setdefault(ez, [99.0, 0.0])
        k[0] = min(k[0], m); k[1] = max(k[1], dmax)
        if m < worst[0]: worst = (m, (t, ez))
for ez, (m, d) in res.items():
    print("ojos %.1f cm: margen minimo de la silueta sobre el borde de la malla en 30 min %.2f grados; silueta mas lejana %.0f m" % (ez, m, d))
print("peor:", worst)
