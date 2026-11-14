# -*- coding: utf-8 -*-
"""a_checks_skyline.py - verificador de confort v2 (parte A).
1) Transcripcion independiente del HLSL (h_hlsl.py) contra valley_model.valley_h.
2) Zona cercana: h = 0 exacto a r <= 15 m (y 10 m alrededor del metaball), tiempos al azar hasta 1 h.
3) Silueta (skyline) en 360 grados: desplazamiento en 5 s (px a 1052 px HFOV 90), velocidad vertical,
   velocidad LATERAL del patron (correlacion cruzada por ventanas de azimut) y su coherencia.
Solo lee los scripts del repo; escribe en esta carpeta."""
import json
import math
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(AQUI, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, ".claude", "skills", "unreal-vr", "scripts"))
sys.path.insert(0, AQUI)
import valley_model as vm  # noqa: E402
from h_hlsl import h_hlsl  # noqa: E402

F_PX = 526.0                     # px de focal: 1052 px, HFOV 90
PX_DEG = F_PX * math.tan(math.radians(1.0))   # px por grado en el centro (9,18)
QUEST_PPD = 25.0                 # px por grado del Quest 3 (aprox.)
EYE_Z = 120.0
out = {}
rng = np.random.default_rng(7)

# ---------------------------------------------------------------- 1) HLSL vs modelo
x = rng.uniform(-64000, 64000, 20000)
y = rng.uniform(-64000, 64000, 20000)
t = rng.uniform(0, 3600, 20000)
hm = np.array([vm.valley_h(x[i:i + 1], y[i:i + 1], t[i])[0] for i in range(0, 20000, 10)])
hh = np.array([h_hlsl(x[i:i + 1], y[i:i + 1], t[i])[0] for i in range(0, 20000, 10)])
out["hlsl_vs_modelo_max_cm"] = float(np.max(np.abs(hm - hh)))
print("1) |h_hlsl - h_modelo| max = %.3e cm (2000 puntos, t hasta 1 h)" % out["hlsl_vs_modelo_max_cm"])

# ---------------------------------------------------------------- 2) zona cercana
r = np.sqrt(rng.uniform(0, 1500.0 ** 2, 200000))
a = rng.uniform(0, 2 * np.pi, 200000)
xs, ys = r * np.cos(a), r * np.sin(a)
mx = 0.0
for tt in rng.uniform(0, 3600, 40):
    mx = max(mx, float(np.max(np.abs(h_hlsl(xs, ys, tt)))))
out["zona_15m_max_abs_cm"] = mx
# primer radio donde algo se mueve de forma medible (>0.5 cm de rango en 60 s)
radios = np.arange(1500, 12001, 250.0)
rango = []
for rr in radios:
    aa = np.linspace(0, 2 * np.pi, 720, endpoint=False)
    hs = np.stack([h_hlsl(rr * np.cos(aa), rr * np.sin(aa), tt) for tt in np.arange(0, 60, 1.0)])
    rango.append(float(np.max(hs.max(0) - hs.min(0))))
out["rango_h_60s_por_radio_cm"] = {str(int(rr / 100)): round(v, 2) for rr, v in zip(radios, rango)}
print("2) zona r<=15 m: max|h| = %.3g cm; rango de h en 60 s por radio (m: cm):" % mx)
print("   " + ", ".join("%d:%.1f" % (int(rr / 100), v) for rr, v in zip(radios, rango) if int(rr) % 1000 == 0))
dep = math.degrees(math.atan(EYE_Z / 1500.0))
out["angulo_zona_quieta_deg"] = -dep
print("   todo lo que se ve por debajo de %.2f deg de elevacion es el piso quieto" % -dep)


# ---------------------------------------------------------------- 3) silueta 360
from fastvalley import Grid
SS = np.geomspace(1500.0, 64000.0, 1600)
_GR = {}


def skyline(az_deg, tt, s=SS):
    key = (len(az_deg), float(az_deg[0]), float(az_deg[-1]))
    if key not in _GR:
        az = np.radians(az_deg)[:, None]
        _GR[key] = Grid(s[None, :] * np.cos(az), s[None, :] * np.sin(az))
    h = _GR[key].eval(tt, grad=False)
    te = (h - EYE_Z) / s[None, :]
    i = np.argmax(te, axis=1)
    return np.degrees(np.arctan(te[np.arange(len(az_deg)), i])), s[i]


AZ = np.arange(0, 360, 0.25)
T0S = rng.uniform(0, 900, 8)
DT = 0.25
NT = int(round(20.0 / DT)) + 1           # 20 s por serie
E = np.zeros((len(T0S), NT, len(AZ)))
S = np.zeros_like(E)
for k, t0 in enumerate(T0S):
    for j in range(NT):
        E[k, j], S[k, j] = skyline(AZ, t0 + j * DT)
np.save(os.path.join(AQUI, "skyline_E.npy"), E)

# desplazamiento en 5 s
n5 = int(round(5.0 / DT))
d5 = np.abs(E[:, n5:, :] - E[:, :-n5, :])            # grados
d5px = d5 * PX_DEG
front = (np.abs(((AZ + 180) % 360) - 180) <= 45)
out["skyline_5s"] = dict(
    mediana_deg=float(np.median(d5)), p90_deg=float(np.percentile(d5, 90)), max_deg=float(d5.max()),
    mediana_px1052=float(np.median(d5px)), p90_px1052=float(np.percentile(d5px, 90)),
    frac_azimuts_mayor_1px=float(np.mean(d5px > 1.0)), frac_mayor_3px=float(np.mean(d5px > 3.0)),
    frente90_max_px_por_instante_mediana=float(np.median(d5px[:, :, front].max(axis=2))),
    frente90_max_px_por_instante_min=float(np.min(d5px[:, :, front].max(axis=2))),
)
print("3a) silueta, cambio en 5 s: mediana %.3f deg = %.2f px (1052); p90 %.2f px; max %.2f deg; "
      "%.0f %% de los azimuts > 1 px, %.0f %% > 3 px" % (
          np.median(d5), np.median(d5px), np.percentile(d5px, 90), d5.max(),
          100 * np.mean(d5px > 1), 100 * np.mean(d5px > 3)))
print("    en el frente (+-45 deg): el azimut que mas cambia, mediana %.1f px, minimo %.1f px por ventana de 5 s" % (
    out["skyline_5s"]["frente90_max_px_por_instante_mediana"], out["skyline_5s"]["frente90_max_px_por_instante_min"]))

# velocidad vertical (diferencias centradas)
vv = np.abs(E[:, 2:, :] - E[:, :-2, :]) / (2 * DT)
out["skyline_vel_vertical"] = dict(mediana=float(np.median(vv)), p90=float(np.percentile(vv, 90)),
                                   p99=float(np.percentile(vv, 99)), max=float(vv.max()),
                                   frac_mayor_0p1=float(np.mean(vv > 0.1)))
print("3b) silueta, |dE/dt|: mediana %.3f, p90 %.3f, p99 %.3f, max %.3f deg/s; %.0f %% > 0.1 deg/s" % (
    np.median(vv), np.percentile(vv, 90), np.percentile(vv, 99), vv.max(), 100 * np.mean(vv > 0.1)))
# saltos (la silueta cambia de dueno: distancia del punto de silueta salta)
js = np.abs(np.diff(E, axis=1)) / DT
out["skyline_saltos_mayor_2deg_s_frac"] = float(np.mean(js > 2.0))

# velocidad LATERAL: correlacion cruzada del perfil E(az) entre t y t+LAG en ventanas de 30 deg
LAG = 2.0
nl = int(round(LAG / DT))
W = 120                                   # 30 deg a 0.25 deg
lat = []
NW = len(AZ) // (W // 2)
LAGS = np.arange(-40, 41)
for k in range(len(T0S)):
    for j in range(0, NT - nl, 4):
        a0 = E[k, j]
        a1 = E[k, j + nl]
        fila = []
        for c0 in range(0, len(AZ), W // 2):
            idx = (np.arange(c0, c0 + W)) % len(AZ)
            p = a0[idx] - a0[idx].mean()
            Q = a1[(idx[None, :] + LAGS[:, None]) % len(AZ)]
            Q = Q - Q.mean(axis=1, keepdims=True)
            cs = (Q * p[None, :]).sum(1) / (np.sqrt((Q * Q).sum(1) * (p * p).sum()) + 1e-12)
            i = int(np.argmax(cs))
            if 0 < i < len(cs) - 1:
                y0, y1, y2 = cs[i - 1], cs[i], cs[i + 1]
                d = 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2 + 1e-12)
            else:
                d = 0.0
            fila.append(((LAGS[i] + d) * 0.25 / LAG, cs[i], float(np.std(p))))
        lat.append(fila)
lat = np.array(lat)            # (muestras, ventanas, 3): vel deg/s, pico ncc, std perfil
ok = (lat[..., 1] > 0.8) & (lat[..., 2] > 0.05)
v = lat[..., 0]
cent = (np.arange(lat.shape[1]) * (W // 2) + W // 2) * 0.25 % 360
fr = np.abs(((cent + 180) % 360) - 180) <= 45
out["skyline_lateral"] = dict(
    ventanas_validas_frac=float(ok.mean()),
    abs_mediana=float(np.median(np.abs(v[ok]))), abs_p90=float(np.percentile(np.abs(v[ok]), 90)),
    abs_max=float(np.abs(v[ok]).max()),
    media_firmada_360=float(np.mean([np.mean(v[i][ok[i]]) for i in range(len(v)) if ok[i].any()])),
    media_firmada_frente_por_muestra=[float(np.mean(v[i][ok[i] & fr])) for i in range(len(v)) if (ok[i] & fr).any()],
)
cf = np.array(out["skyline_lateral"]["media_firmada_frente_por_muestra"])
print("3c) silueta, velocidad LATERAL del patron (ventanas de 30 deg, lag 2 s): |v| mediana %.3f, p90 %.3f, "
      "max %.3f deg/s; media firmada 360 = %+.3f deg/s; frente: media firmada por instante de %+.3f a %+.3f "
      "(|media| mediana %.3f)" % (out["skyline_lateral"]["abs_mediana"], out["skyline_lateral"]["abs_p90"],
                                  out["skyline_lateral"]["abs_max"], out["skyline_lateral"]["media_firmada_360"],
                                  cf.min(), cf.max(), np.median(np.abs(cf))))

# distancia de la silueta y cuanto de ella es oleaje
out["skyline_dist_m"] = dict(p10=float(np.percentile(S, 10) / 100), mediana=float(np.median(S) / 100),
                             p90=float(np.percentile(S, 90) / 100))
print("    distancia del punto de silueta: p10 %.0f m, mediana %.0f m, p90 %.0f m" % (
    out["skyline_dist_m"]["p10"], out["skyline_dist_m"]["mediana"], out["skyline_dist_m"]["p90"]))

# kimografo de la silueta (frente +-45, 60 s) para ver direccion del flujo
t0 = 100.0
AZf = np.arange(-60, 60.01, 0.1)
K = np.stack([skyline(AZf, t0 + j * 0.25)[0] for j in range(240)])
np.save(os.path.join(AQUI, "kimo_frente.npy"), K)
with open(os.path.join(AQUI, "a_resultados.json"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1)
print("OK -> a_resultados.json")
