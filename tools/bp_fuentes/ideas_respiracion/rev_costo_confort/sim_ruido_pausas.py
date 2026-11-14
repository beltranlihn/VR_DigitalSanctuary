# -*- coding: utf-8 -*-
"""Revision escéptica (costo y confort) del plan PLAN-RESPIRACION-ENTORNO-2026-09-28.
Pregunta: con una senal REAL (ruido del mando filtrado por TauFast 0,4 s y la deriva del sostenido), las pausas
del aliento siguen quietas? El sim del plan (sim_breath_air.py) alimenta al seguidor con belly_target IDEAL:
sostenidos exactos en +-1 y cero ruido.

Cadena: n_pre (belly ideal des-aplastado) + ruido OU(tau 0,4 s) + deriva del sostenido -> clamp -> n(2-|n|)
        -> RigFollower (el FollowBreath del rig) -> AirBP.step (el BP del aire, sin cambios).
Metricas en los sostenidos (desde 0,5 s despues de empezar hasta el final):
  - fraccion de cuadros con |v| > VelGate (el aire se cree que se respira)
  - avance de la cinta Tin + Tout durante el sostenido (en caminos; una inhalacion completa = 0,9)
  - Ein al final del sostenido de arriba (ideal ~0,39: suspendidas y apagandose) y Eout max en ese sostenido
    (la pluma apareciendo mientras se retiene el aire)
  - cambios de estado inh/exh/quieto por sostenido
Y en la inhalacion activa: fraccion de cuadros con exh = true (pluma parpadeando al inhalar).
"""
import math
import os
import sys

import numpy as np

RAIZ = r"C:\Users\beltr\Desktop\Alma Digital Studio\Projects\VR Unreal"
sys.path.insert(0, os.path.join(RAIZ, ".claude", "skills", "unreal-vr", "scripts"))
import breath_air_model as am  # noqa: E402

FPS = 72.0
DT = 1.0 / FPS
EYE = np.array([0.0, 0.0, 120.0])


def unsquash(y):
    y = max(min(y, 1.0), -1.0)
    return math.copysign(1.0 - math.sqrt(max(1.0 - abs(y), 0.0)), y)


def squash(n):
    n = max(min(n, 1.0), -1.0)
    return n * (2.0 - abs(n))


def run(sigma, drift, pacer=(4.0, 3.0, 4.0, 3.0), ciclos=8, seed=1, velgate=None):
    rng = np.random.default_rng(seed)
    bp = None if velgate is None else dict(VelGate=velgate)
    air = am.AirBP(EYE, 0.0, -2.0, bp)
    rig = am.RigFollower(s0=-1.0)
    T = sum(pacer)
    N = int(ciclos * T * FPS)
    ou = 0.0
    a = DT / 0.4
    # OU con varianza estacionaria sigma^2 (EMA de ruido blanco)
    kw = sigma * math.sqrt((2.0 - a) / a) if sigma > 0 else 0.0
    rec = dict(t=[], ph=[], v=[], inh=[], exh=[], Ein=[], Eout=[], Tin=[], Tout=[], S=[], rate=[])
    hold_t = 0.0
    for k in range(N):
        t = k * DT
        y, ph = am.belly_target(t, *pacer, lag=0.4)
        n = unsquash(y)
        # deriva del sostenido: el band-pass y el freno HoldSlow dejan caer el nivel sostenido
        if ph in (1, 3):
            hold_t += DT
            n = n - math.copysign(drift * min(hold_t / max(pacer[1], 1e-3), 1.0), n)
        else:
            hold_t = 0.0
        ou += a * (rng.standard_normal() * kw - ou)
        tgt = squash(n + ou)
        S = rig.step(tgt, DT)
        v = air.step(DT, S, 1.0, EYE, 0.0, -2.0)
        g = air.q["VelGate"]
        rec["t"].append(t); rec["ph"].append(ph); rec["v"].append(v)
        rec["inh"].append(v > g); rec["exh"].append(v < -g)
        rec["Ein"].append(air.Ein); rec["Eout"].append(air.Eout)
        rec["Tin"].append(air.Tin); rec["Tout"].append(air.Tout); rec["S"].append(S)
        rec["rate"].append(air.RateBpm)
    for kk in rec:
        rec[kk] = np.array(rec[kk])
    return rec, T


def unwrap_adv(x):
    d = np.diff(x)
    d = np.where(d < -0.5, d + 1.0, d)
    return float(np.sum(np.maximum(d, 0.0)))


def metricas(rec, T, pacer=(4.0, 3.0, 4.0, 3.0)):
    t, ph = rec["t"], rec["ph"]
    out = dict(movil=[], adv=[], ein_fin=[], eout_max=[], cambios=[], exh_en_inh=[], eout_en_inh=[])
    ncic = int(round(t[-1] / T))
    for c in range(2, ncic):            # descartar los 2 primeros ciclos (arranque)
        t0 = c * T + 0.4
        # sostenido de arriba (fase 1) y de abajo (fase 3)
        for fase, ini, dur in ((1, pacer[0], pacer[1]), (3, pacer[0] + pacer[1] + pacer[2], pacer[3])):
            if dur <= 0:
                continue
            m = (t >= t0 + ini + 0.5) & (t < t0 + ini + dur)
            if m.sum() < 5:
                continue
            mov = rec["inh"][m] | rec["exh"][m]
            out["movil"].append(float(mov.mean()))
            out["adv"].append(unwrap_adv(rec["Tin"][m]) + unwrap_adv(rec["Tout"][m]))
            estado = rec["inh"][m].astype(int) - rec["exh"][m].astype(int)
            out["cambios"].append(int(np.sum(np.diff(estado) != 0)))
            if fase == 1:
                out["ein_fin"].append(float(rec["Ein"][m][-1]))
                out["eout_max"].append(float(rec["Eout"][m].max()))
        # inhalacion activa (fase 0), el tramo central
        m = (t >= t0 + 0.8) & (t < t0 + pacer[0] - 0.4)
        out["exh_en_inh"].append(float(rec["exh"][m].mean()))
        out["eout_en_inh"].append(float(rec["Eout"][m].max()))
    return {k: np.array(v) for k, v in out.items()}


def main():
    lineas = []
    lineas.append("SIM ruido y pausas del aliento (revisor costo/confort). 4-3-4-3, 8 ciclos, 72 Hz, 3 semillas por caso.")
    lineas.append("sigma = ruido de n ANTES del aplastado (unidades del rango normalizado; 0,02 = 1 %% del rango total de 2),")
    lineas.append("OU tau 0,4 s (el TauFast del rig). deriva = cuanto cae |n| a lo largo del sostenido (band-pass + HoldSlow).")
    lineas.append("")
    cab = "%-26s %8s %8s %9s %9s %8s %9s %9s %8s" % ("caso", "movil%", "avance", "Ein_fin", "Eout_max", "cambios",
                                                    "exh@inh%", "Eout@inh", "resp/min")
    lineas.append(cab)
    casos = [("ideal (el sim del plan)", 0.0, 0.0, None),
             ("ruido 0,005", 0.005, 0.0, None),
             ("ruido 0,01", 0.01, 0.0, None),
             ("ruido 0,02", 0.02, 0.0, None),
             ("ruido 0,04", 0.04, 0.0, None),
             ("deriva 0,10", 0.0, 0.10, None),
             ("deriva 0,20", 0.0, 0.20, None),
             ("ruido 0,02 + deriva 0,15", 0.02, 0.15, None),
             ("ruido 0,04 + deriva 0,15", 0.04, 0.15, None),
             ("r0,02+d0,15 VelGate 0,12", 0.02, 0.15, 0.12),
             ("r0,04+d0,15 VelGate 0,12", 0.04, 0.15, 0.12)]
    for nombre, sg, dr, vg in casos:
        acc = []
        rates = []
        for sd in (1, 2, 3):
            rec, T = run(sg, dr, seed=sd, velgate=vg)
            acc.append(metricas(rec, T))
            rates.append(rec["rate"][-1])
        mm = {k: np.concatenate([a[k] for a in acc]) for k in acc[0]}
        lineas.append("%-26s %8.1f %8.3f %9.2f %9.2f %8.1f %9.1f %9.2f %8.1f" % (
            nombre, 100 * mm["movil"].mean(), mm["adv"].mean(), mm["ein_fin"].mean(), mm["eout_max"].mean(),
            mm["cambios"].mean(), 100 * mm["exh_en_inh"].mean(), mm["eout_en_inh"].max(), float(np.mean(rates))))
    lineas.append("")
    lineas.append("Lectura: 'movil%' = % del sostenido en que el aire se cree respirado (ideal 0). 'avance' = caminos que")
    lineas.append("avanza la cinta durante el sostenido (una inhalacion completa = 0,9). 'Ein_fin' ideal ~0,39 (se apaga);")
    lineas.append("si queda cerca de 1 las motas NO se apagan en la retencion. 'Eout_max' = pluma apareciendo con el aire")
    lineas.append("retenido arriba (ideal 0). 'cambios' = alternancias inh/quieto/exh por sostenido (parpadeo de corrientes).")
    lineas.append("'resp/min' = RateBpm final del BP (real 60/14 = 4,3): si sube, RateCalm apaga el aire sin motivo.")
    txt = "\n".join(lineas)
    print(txt)
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sim_ruido_pausas_resultados.txt"), "w",
              encoding="utf-8") as f:
        f.write(txt + "\n")


if __name__ == "__main__":
    main()
