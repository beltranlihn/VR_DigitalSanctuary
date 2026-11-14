# -*- coding: utf-8 -*-
"""diag_a_v1.py - (a) cuanto se mueve el valle v1 visto desde los ojos (0, 0, 120), en 1, 5 y 10 s.

Mide, con el modelo validado contra la §12 (modelo_v1.control()):
  1. Por vertice de la malla real (15.169): |h(t+D) - h(t)| maximo sobre t en [0, 1200] s y la
     velocidad vertical maxima, por banda de distancia al usuario.
  2. El angulo: cambio de elevacion de cada vertice visto desde los ojos y velocidad angular vertical.
  3. La SILUETA de las colinas contra el cielo: elevacion maxima por azimut (720 azimuts, radio cada
     10 cm) en t = 0..600 s cada 0,5 s. Desplazamiento en 1, 5 y 10 s en grados, en pixeles de la
     captura del editor (1052 px de ancho, HFOV 90, pitch -2) y en pixeles de la Quest 3 (~25 px/grado).
  4. El SOMBREADO: color sRGB 8 bits de cada vertice VISIBLE desde los ojos (oclusion por sector)
     en t y t+D: cambio maximo y percentil 99, en niveles de 0-255.
  5. Quietud: fraccion de la zona de colinas donde el morph no mueve nada (umbral de la loma, Mt = 0).
Salida: resultados_a.json + texto.
"""
import json
import math
import os

import numpy as np

import modelo_v1 as M

AQUI = os.path.dirname(os.path.abspath(__file__))
assert M.control(), "el modelo no reproduce la §12: no se mide nada"

BANDAS = [(0, 600), (600, 1000), (1000, 1500), (1500, 2000), (2000, 3000), (3000, 4401)]
DELTAS = (1.0, 5.0, 10.0)
F_PX = 526.0              # px: (1052/2)/tan(45 grados)
PITCH = math.radians(-2.0)
QUEST_PPD = 25.0          # px por grado de la Quest 3 en el centro (aprox.)
res = {}

# ------------------------------------------------------------------ 1-2. vertices
x, y, rs = M.vertices_malla()
pt = M.partes(x, y)
r = pt["r"]
dt = 0.5
ts = np.arange(0.0, 1200.0 + 10.0 + dt / 2, dt)
H = np.empty((len(ts), len(x)), dtype=np.float64)
for i, t in enumerate(ts):
    H[i] = M.h_de(pt, t)
EL = np.degrees(np.arctan2(H - M.OJO_Z, r[None, :]))
vel = np.abs(np.diff(H, axis=0)) / dt                      # cm/s (diferencia de 0,5 s)
velang = np.abs(np.diff(EL, axis=0)) / dt                   # grados/s
n1200 = int(round(1200.0 / dt))
res["vertices"] = []
for a, b in BANDAS:
    msk = (r >= a) & (r < b)
    fila = {"banda_cm": [a, b], "n": int(msk.sum()), "vel_max_cm_s": float(vel[:, msk].max()),
            "velang_max_deg_s": float(velang[:, msk].max())}
    for D in DELTAS:
        k = int(round(D / dt))
        dH = np.abs(H[k:n1200 + k, msk] - H[:n1200, msk])
        dE = np.abs(EL[k:n1200 + k, msk] - EL[:n1200, msk])
        fila["dh_max_cm_%gs" % D] = float(dH.max())
        fila["dh_p99_cm_%gs" % D] = float(np.percentile(dH.max(axis=0), 99))
        fila["del_max_deg_%gs" % D] = float(dE.max())
    res["vertices"].append(fila)
# quietud: vertices de colinas (env > 0.05) cuya h no cambia NUNCA en 1200 s
col = pt["env"] > 0.05
rango = H[:n1200].max(axis=0) - H[:n1200].min(axis=0)
res["colinas_sin_movimiento_frac"] = float(((rango < 0.5) & col).sum() / col.sum())
res["colinas_rango_mediana_cm"] = float(np.median(rango[col]))
res["colinas_rango_p90_cm"] = float(np.percentile(rango[col], 90))
res["colinas_rango_max_cm"] = float(rango[col].max())

# ------------------------------------------------------------------ 3. silueta
AZ = np.arange(-180.0, 180.0, 0.5)
RR = np.arange(600.0, 4400.0 + 1e-6, 10.0)
AZg, RRg = np.meshgrid(np.radians(AZ), RR, indexing="ij")
ps = M.partes(RRg * np.cos(AZg), RRg * np.sin(AZg))
ts2 = np.arange(0.0, 600.0 + 10.0 + dt / 2, dt)
SIL = np.empty((len(ts2), len(AZ)))
ARG = np.empty((len(ts2), len(AZ)), dtype=np.int32)
for i, t in enumerate(ts2):
    tan = (M.h_de(ps, t) - M.OJO_Z) / RRg
    ARG[i] = tan.argmax(axis=1)
    SIL[i] = np.degrees(np.arctan(tan.max(axis=1)))


def fila_px(az_deg, el_deg):
    """fila (px, positivo = arriba) de la direccion (az, el) en la captura 1052 px, HFOV 90, pitch -2."""
    az, el = np.radians(az_deg), np.radians(el_deg)
    d = np.stack([np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)], -1)
    fwd = np.array([math.cos(PITCH), 0.0, math.sin(PITCH)])
    up = np.array([-math.sin(PITCH), 0.0, math.cos(PITCH)])
    return F_PX * (d @ up) / (d @ fwd)


frente = np.abs(AZ) <= 45.0
VPX = fila_px(AZ[None, frente], SIL[:, frente])
n600 = int(round(600.0 / dt))
res["silueta"] = {"elev_min_deg": float(SIL.min()), "dist_silueta_frente_cm_mediana": float(np.median(RR[ARG[:, frente]])),
                  "dist_silueta_frente_cm_min": float(RR[ARG[:, frente]].min())}
for D in DELTAS:
    k = int(round(D / dt))
    dS = np.abs(SIL[k:n600 + k] - SIL[:n600])
    dP = np.abs(VPX[k:n600 + k] - VPX[:n600])
    res["silueta"]["%gs" % D] = {
        "max_deg_360": float(dS.max()), "p90_deg_360": float(np.percentile(dS, 90)), "mediana_deg_360": float(np.median(dS)),
        "max_px_captura_frente": float(dP.max()), "p90_px_captura_frente": float(np.percentile(dP, 90)),
        "mediana_px_captura_frente": float(np.median(dP)),
        "max_px_quest": float(dS.max() * QUEST_PPD), "mediana_px_quest": float(np.median(dS) * QUEST_PPD)}
vs = np.abs(np.diff(SIL, axis=0)) / dt
res["silueta"]["vel_max_deg_s"] = float(vs.max())
res["silueta"]["vel_p99_deg_s"] = float(np.percentile(vs, 99))
res["silueta"]["frac_azimuts_que_no_se_mueven_en_600s"] = float(((SIL[:n600].max(0) - SIL[:n600].min(0)) < 0.01).mean())
res["silueta"]["rango_600s_deg_mediana"] = float(np.median(SIL[:n600].max(0) - SIL[:n600].min(0)))
res["silueta"]["rango_600s_deg_max"] = float((SIL[:n600].max(0) - SIL[:n600].min(0)).max())
np.save(os.path.join(AQUI, "sil_v1.npy"), SIL[:int(round(120 / dt)) + 1].astype(np.float32))   # para las figuras

# ------------------------------------------------------------------ 4. sombreado de los vertices visibles
S = 192
nr = len(rs)


def visibles(hh):
    """oclusion por sector: el vertice se ve si su tangente de elevacion supera la de todos los anillos anteriores."""
    tan = (hh[1:].reshape(nr, S) - M.OJO_Z) / rs[:, None]
    prev = np.maximum.accumulate(np.vstack([np.full((1, S), -np.inf), tan[:-1]]), axis=0)
    return np.concatenate([[True], (tan >= prev - 1e-9).ravel()])


tc = np.arange(0.0, 600.0 + 10.0 + 0.5, 1.0)
C = np.empty((len(tc), len(x), 3))
VIS = np.empty((len(tc), len(x)), dtype=bool)
for i, t in enumerate(tc):
    hh = M.h_de(pt, t)
    gx, gy = M.grad_fd(x, y, t, d=0.5)
    hf = np.where(M.P["DuneAmp"] > 0, (hh - pt["B"]) / M.P["DuneAmp"], 0.0)
    C[i] = M.srgb8(M.color_suelo(x, y, hh, gx, gy, hf))
    VIS[i] = visibles(hh)
res["sombreado"] = {"vertices_visibles_frac": float(VIS.mean())}
lejos = r >= 600
for D in DELTAS:
    k = int(D)
    n = int(600)
    dC = np.abs(C[k:n + k] - C[:n]).max(axis=2)
    v = VIS[k:n + k] & VIS[:n] & lejos[None, :]
    res["sombreado"]["%gs" % D] = {"max_niveles": float(dC[v].max()), "p99_niveles": float(np.percentile(dC[v], 99)),
                                   "p90_niveles": float(np.percentile(dC[v], 90))}
    # tasa por segundo (pendiente de color) del peor vertice visible
res["sombreado"]["tasa_max_niveles_por_s"] = float((np.abs(np.diff(C, axis=0)).max(axis=2)[VIS[1:] & VIS[:-1] & lejos[None, :]]).max())

# ------------------------------------------------------------------ salida
with open(os.path.join(AQUI, "resultados_a.json"), "w", encoding="utf-8") as fh:
    json.dump(res, fh, indent=1, ensure_ascii=False)
print(json.dumps(res, indent=1, ensure_ascii=False))
