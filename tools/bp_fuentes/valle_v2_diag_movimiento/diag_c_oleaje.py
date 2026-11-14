# -*- coding: utf-8 -*-
"""diag_c_oleaje.py - verifica y mide la PROPUESTA de oleaje (oleaje.py) sobre la base sustituta
(valle v1 agrandado 5 veces, MorphAmt 0). Mismas medidas que diag_a_v1.py para comparar.

Uso: python diag_c_oleaje.py [SwellAmp=400 SwellSpeed=1 ...]    -> resultados_c<tag>.json
"""
import json
import math
import os
import sys

import numpy as np

import modelo_v1 as M
import oleaje as O

AQUI = os.path.dirname(os.path.abspath(__file__))
over = {}
tag = ""
for a in sys.argv[1:]:
    k, v = a.split("=", 1)
    if k == "tag":
        tag = v
    else:
        over[k] = float(v)
q = dict(O.Q, **over)
B = O.BASE_Q
res = {"perillas": q, "olas": O.OLAS}
rng = np.random.default_rng(3)

# ------------------------------------------------------------ 1. controles
x = rng.uniform(-22000, 22000, 4000)
y = rng.uniform(-22000, 22000, 4000)
t = rng.uniform(0, 3600, 4000)
_, gx, gy, gt = O.ola(x, y, t, B, q, con_grad=True)
d = 0.05
fx = (O.ola(x + d, y, t, B, q) - O.ola(x - d, y, t, B, q)) / (2 * d)
fy = (O.ola(x, y + d, t, B, q) - O.ola(x, y - d, t, B, q)) / (2 * d)
ft = (O.ola(x, y, t + 1e-3, B, q) - O.ola(x, y, t - 1e-3, B, q)) / 2e-3
res["control_gradiente_max_err"] = float(max(np.abs(fx - gx).max(), np.abs(fy - gy).max()))
res["control_dhdt_max_err_cm_s"] = float(np.abs(ft - gt).max())
# zona quieta: 10 m alrededor del usuario y del metaball (380, 0) => r <= 1380 cm < SwellNear
xq = rng.uniform(-1400, 1800, 200000)
yq = rng.uniform(-1400, 1400, 200000)
m = (np.hypot(xq, yq) <= 1000) | (np.hypot(xq - 380, yq) <= 1000)
tq = rng.uniform(0, 3600, m.sum())
res["zona_quieta_max_abs_cm"] = float(np.abs(O.ola(xq[m], yq[m], tq, B, q)).max())
# detras de la cresta: e >= RimBack -> 0
ang = rng.uniform(0, 2 * math.pi, 5000)
bq = dict(M.P, **B)
ee = rng.uniform(bq["RimBack"], bq["RimBack"] + 1, 5000)
xb = bq["ValleyX"] + ee * bq["ValleyA"] * np.cos(ang)
yb = ee * bq["ValleyB"] * np.sin(ang)
res["detras_cresta_max_abs_cm"] = float(np.abs(O.ola(xb, yb, rng.uniform(0, 3600, 5000), B, q)).max())
v, tot = O.deriva_neta(q)
res["deriva_neta_frac"] = float(np.linalg.norm(v) / tot)
res["frecuencias_hz"] = [q["SwellSpeed"] / o[2] for o in O.OLAS]
res["velocidades_fase_cm_s"] = [o[1] * q["SwellScale"] * q["SwellSpeed"] / o[2] for o in O.OLAS]
# velocidad angular tangencial del patron (c_j / r) y amplitud A(r) a varias distancias (frente)
tabla = []
for rr in (1500, 2000, 3000, 4000, 5000, 7000, 10000, 15000, 20000):
    Wq = M.ss(q["SwellNear"], q["SwellFar"], rr)
    tabla.append({"r_m": rr / 100, "A_cm": float(q["SwellAmp"] * Wq),
                  "patron_max_deg_s": float(math.degrees(max(res["velocidades_fase_cm_s"]) / rr)),
                  "vertical_max_deg_s": float(math.degrees(q["SwellAmp"] * Wq * sum(o[3] * 2 * math.pi * q["SwellSpeed"] / o[2] for o in O.OLAS) / O.SW / rr))})
res["por_distancia"] = tabla

# ------------------------------------------------------------ 2. vertices (malla polar de la escala nueva)
xv, yv, rsv = M.vertices_malla(rmax=22000.0)
pb = M.partes(xv, yv, B)
hb = M.h_de(pb, 0.0)
rv = pb["r"]
dt = 0.5
ts = np.arange(0.0, 600.0 + 10.0 + dt / 2, dt)
H = np.empty((len(ts), len(xv)))
for i, tt in enumerate(ts):
    H[i] = hb + O.ola(xv, yv, tt, B, q)
EL = np.degrees(np.arctan2(H - M.OJO_Z, rv[None, :]))
vel = np.abs(np.diff(H, axis=0)) / dt
velang = np.abs(np.diff(EL, axis=0)) / dt
n600 = int(round(600 / dt))
BANDAS = [(0, 1500), (1500, 3000), (3000, 5000), (5000, 8000), (8000, 12000), (12000, 16000), (16000, 22001)]
res["vertices"] = []
for a, b in BANDAS:
    mk = (rv >= a) & (rv < b)
    fila = {"banda_m": [a / 100, b / 100], "n": int(mk.sum()), "vel_max_cm_s": float(vel[:, mk].max()),
            "velang_max_deg_s": float(velang[:, mk].max())}
    for D in (1.0, 5.0, 10.0):
        k = int(round(D / dt))
        fila["dh_max_cm_%gs" % D] = float(np.abs(H[k:n600 + k, mk] - H[:n600, mk]).max())
        fila["del_max_deg_%gs" % D] = float(np.abs(EL[k:n600 + k, mk] - EL[:n600, mk]).max())
    res["vertices"].append(fila)

# ------------------------------------------------------------ 3. silueta
AZ = np.arange(-180.0, 180.0, 0.5)
RR = 1000.0 * np.power(1.005, np.arange(0, int(math.log(22.0) / math.log(1.005)) + 1))
AZg, RRg = np.meshgrid(np.radians(AZ), RR, indexing="ij")
Xs, Ys = RRg * np.cos(AZg), RRg * np.sin(AZg)
hbs = M.h_de(M.partes(Xs, Ys, B), 0.0)
# ola separada en parte espacial fija y fase temporal (misma cuenta que O.ola, mas rapida)
bq =dict(M.P, **B)
ex = (Xs - bq["ValleyX"]) / bq["ValleyA"]
ey = Ys / bq["ValleyB"]
e = np.sqrt(ex * ex + ey * ey)
A = q["SwellAmp"] * M.ss(q["SwellNear"], q["SwellFar"], RRg) * (1 - M.ss(bq["RimCrest"], bq["RimBack"], e))
SP = []
for al, lam, T, w, ph in O.OLAS:
    Kk = 2 * math.pi / (lam * q["SwellScale"])
    a = math.radians(al + q["SwellSeed"])
    gs = Kk * (math.cos(a) * Xs + math.sin(a) * Ys) + ph
    SP.append((w * np.sin(gs), w * np.cos(gs), T))
dt2 = 0.5
ts2 = np.arange(0.0, 600.0 + 10.0 + dt2 / 2, dt2)
SIL = np.empty((len(ts2), len(AZ)))
for i, tt in enumerate(ts2):
    s = np.zeros_like(Xs)
    for Sj, Cj, T in SP:
        b = 2 * math.pi * ((q["SwellSpeed"] * tt / T) % 1.0)
        s += Sj * math.cos(b) - Cj * math.sin(b)
    SIL[i] = np.degrees(np.arctan(((hbs + A * s / O.SW - M.OJO_Z) / RRg).max(axis=1)))
# control: la silueta rapida coincide con O.ola en un instante
chk_t = 37.0
hh = hbs + O.ola(Xs, Ys, chk_t, B, q)
res["control_silueta_rapida_err_deg"] = float(np.abs(np.degrees(np.arctan(((hh - M.OJO_Z) / RRg).max(axis=1))) - SIL[int(chk_t / dt2)]).max())

F_PX = 526.0
PITCH = math.radians(-2.0)


def fila_px(az_deg, el_deg):
    az, el = np.radians(az_deg), np.radians(el_deg)
    d = np.stack([np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)], -1)
    fwd = np.array([math.cos(PITCH), 0.0, math.sin(PITCH)])
    up = np.array([-math.sin(PITCH), 0.0, math.cos(PITCH)])
    return F_PX * (d @ up) / (d @ fwd)


fr = np.abs(AZ) <= 45
VPX = fila_px(AZ[None, fr], SIL[:, fr])
n6 = int(round(600 / dt2))
sil = {"elev_min_deg": float(SIL.min()), "elev_max_deg": float(SIL.max())}
for D in (1.0, 5.0, 10.0):
    k = int(round(D / dt2))
    dS = SIL[k:n6 + k] - SIL[:n6]
    dP = np.abs(VPX[k:n6 + k] - VPX[:n6])
    sil["%gs" % D] = {"max_deg_360": float(np.abs(dS).max()), "p90_deg_360": float(np.percentile(np.abs(dS), 90)),
                      "mediana_deg_360": float(np.median(np.abs(dS))),
                      "max_px_captura_frente": float(dP.max()), "p90_px_captura_frente": float(np.percentile(dP, 90)),
                      "mediana_px_captura_frente": float(np.median(dP)),
                      "mediana_px_quest": float(np.median(np.abs(dS)) * 25.0),
                      # coherencia vertical global: cuanto del cambio es un sube/baja de TODO el horizonte a la vez
                      "heave_frac": float(np.abs(dS.mean(axis=1)).mean() / np.abs(dS).mean())}
vs = np.abs(np.diff(SIL, axis=0)) / dt2
sil["vel_max_deg_s"] = float(vs.max())
sil["vel_p99_deg_s"] = float(np.percentile(vs, 99))
sil["vel_mediana_deg_s"] = float(np.median(vs))
for th in (0.05, 0.1, 0.2):
    sil["frac_vel_mayor_%g" % th] = float((vs > th).mean())
# giro neto: correlacion circular de la desviacion de la silueta entre t y t+1 s (desplazamiento en azimut)
dev = SIL - SIL.mean(axis=0)
lags = []
for i in range(0, n6, 4):
    a0 = dev[i] - dev[i].mean()
    a1 = dev[i + 2] - dev[i + 2].mean()
    cc = np.fft.ifft(np.fft.fft(a1) * np.conj(np.fft.fft(a0))).real
    L = int(np.argmax(cc))
    L = L - len(AZ) if L > len(AZ) // 2 else L
    lags.append(L * 0.5)
sil["giro_neto_deg_s_media"] = float(np.mean(lags))
sil["giro_neto_deg_s_mediana_abs"] = float(np.median(np.abs(lags)))
res["silueta"] = sil
np.save(os.path.join(AQUI, "sil_c%s.npy" % tag), SIL[:int(round(120 / dt2)) + 1].astype(np.float32))

with open(os.path.join(AQUI, "resultados_c%s.json" % tag), "w", encoding="utf-8") as fh:
    json.dump(res, fh, indent=1, ensure_ascii=False)
print(json.dumps(res, indent=1, ensure_ascii=False))
