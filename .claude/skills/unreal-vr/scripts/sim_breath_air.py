# -*- coding: utf-8 -*-
"""sim_breath_air.py - simula el ALIENTO VISIBLE con la cadena completa (rig -> MPC -> BP del aire -> VS), mide
confort y costo, y dibuja las previsualizaciones SIN Unreal. Todo sale del modelo verificado contra el HLSL
(breath_air_model.py; hlsl/BreathAir_check.py prueba que es la misma cuenta que BreathAirVS/PS).

Cadena simulada, cuadro a cuadro a 72 Hz:
  usuario siguiendo al pacer (belly_target, con 0,4 s de retardo)
  -> RigFollower (el FollowBreath del rig: frenada fisica, 3 s)          = MPC_Breath.Signed
  -> AirBP.step (BP_BreathAir_SC.AirStep: v = dS/dt, transporte, envolventes, ritmo, marco con retardo)
  -> AirBP.push (los 8 vectores en local de la camara)
  -> vs() por ojo (CamL = (0, +-3,2, 0))

Rev. 2 (2026-09-28, revisiones de codigo y de costo/confort): ademas la SENAL REAL (am.BellyNoisy: ruido OU del
mando + deriva del sostenido: pausa quieta, pluma con el aire retenido, alternancias, ritmo), el GIRO de cabeza
(velocidad de las motas visibles respecto del MUNDO contra su movimiento propio), la LEGIBILIDAD de la inhalacion
(vertical contra lateral), las DISTANCIAS (vergencia), la PLUMA sobre el metaball, la MIRADA ABAJO y los PIXELES.

Salidas en VR_Test/Saved/ClaudeScripts/aliento/:
  sim_aliento_resultados.txt   numeros de confort / senal real / ritmo / giro / legibilidad / costo
  aliento_primera_persona.png  vista del usuario (camara de preview_breath_valley: ojos a 120 cm, pitch -2, HFOV 90)
                               en inhalar / retener / exhalar / pausa + recortes x2 de la banda baja
  aliento_lateral.png          vista de costado con una cabeza de referencia, en los mismos 4 instantes
  aliento_geometria.png        caminos de lado y en planta + giro de 30 grados (lo inhalado entra igual)
  aliento_ciclo.gif            un ciclo 4-3-4-3 (14 s, 8 cuadros/s): primera persona (banda baja) + costado
Uso: python sim_breath_air.py [--sin-imagenes | --solo-imagenes]
"""
import math
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import breath_air_model as am  # noqa: E402

RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", "..", ".."))
SAL = os.path.join(RAIZ, "VR_Test", "Saved", "ClaudeScripts", "aliento")
IDEAS = os.path.join(RAIZ, "VR_Test", "Saved", "ClaudeScripts", "ideas_respiracion")
FPS = 72.0
DT = 1.0 / FPS
EYE0 = np.array([0.0, 0.0, 120.0])
PPD_Q3 = 25.0
Q3_PX = 2064 * 2208
EYES = (-am.IPD / 2.0, am.IPD / 2.0)


def ss(a, b, x):
    return float(am.smoothstep(a, b, x))


def head(t, events=True):
    """Pose de la cabeza (mundo): balanceo natural chico + tres pruebas (como en la propuesta): giro de 30 grados
    en plena inhalacion del ciclo 3, mirada al sensor (pitch -35) en plena exhalacion del ciclo 4, inclinacion de
    8 cm hacia adelante en el ciclo 5."""
    yaw = 0.6 * math.sin(2 * math.pi * 0.13 * t)
    pitch = -2.0 + 0.4 * math.sin(2 * math.pi * 0.21 * t)
    eye = EYE0 + np.array([0.4 * math.sin(2 * math.pi * 0.09 * t), 0.3 * math.sin(2 * math.pi * 0.17 * t),
                           0.2 * math.sin(2 * math.pi * 0.11 * t)])
    moving = False
    if events:
        yaw += 30.0 * (ss(30.0, 30.6, t) - ss(33.6, 34.6, t))
        pitch += -33.0 * (ss(50.0, 50.8, t) - ss(52.8, 53.6, t))
        eye = eye + np.array([8.0, 0.0, -3.0]) * (ss(57.0, 58.0, t) - ss(60.0, 61.0, t))
        moving = (29.9 <= t <= 34.8) or (49.9 <= t <= 53.8) or (56.9 <= t <= 61.2)
    return eye, yaw, pitch, moving


def run(total, pacer=(4.0, 3.0, 4.0, 3.0), events=True, bp=None, keep=(), metrics=True, lag=0.4, rates=False):
    sd = am.seeds()
    n_in = sd["n_in"]
    eye, yaw, pitch, _ = head(0.0, events)
    air = am.AirBP(eye, yaw, pitch, bp)
    rig = am.RigFollower(s0=-1.0)
    rec = dict(t=[], S=[], v=[], Ein=[], Eout=[], glob=[], vin=[], vout=[], cov=[], alsum=[], mind=1e9, maxel=-90.0,
               spd=[], jump=0.0, lagmax=0.0, ph=[], rate=[])
    snaps = {}
    prev = None
    n = int(total * FPS)
    for k in range(n):
        t = k * DT
        tgt, ph = am.belly_target(t, *pacer, lag=lag)
        S = rig.step(tgt, DT)
        eye, yaw, pitch, moving = head(t, events)
        v = air.step(DT, S, 1.0, eye, yaw, pitch)
        pv = air.push(eye, yaw, pitch)
        rec["t"].append(t); rec["S"].append(S); rec["v"].append(v); rec["ph"].append(ph)
        rec["Ein"].append(air.Ein); rec["Eout"].append(air.Eout); rec["glob"].append(air.Glob); rec["rate"].append(air.RateBpm)
        rec["lagmax"] = max(rec["lagmax"], abs(am.normalize_axis(yaw - air.YawLag)))
        want = any(abs(t - kt) < DT / 2 for kt in keep)
        if not metrics and not want:
            continue
        per_eye = [am.vs(sd, pv, (0.0, ey, 0.0)) for ey in EYES]
        al = np.maximum(per_eye[0]["al"], per_eye[1]["al"])
        vis = al > 0.02
        cov = 0.0
        for m in per_eye:
            vi = m["al"] > 0.02
            if vi.any():
                rec["mind"] = min(rec["mind"], float(m["dist"][vi].min()))
                rec["maxel"] = max(rec["maxel"], float(np.degrees(np.arcsin(np.clip(m["sinEl"][vi], -1, 1))).max()))
            P = m["P"]
            inview = vi & (P[:, 0] > 0) & (np.abs(np.degrees(np.arctan2(P[:, 1], P[:, 0]))) < 52.0)
            cov += float(np.sum(np.pi * np.degrees(m["hsz"][inview] / m["dist"][inview]) ** 2) * PPD_Q3 ** 2) / Q3_PX
        rec["cov"].append(cov / 2.0)
        vis10 = al > 0.1
        rec["vin"].append(int(vis10[:n_in].sum()))
        rec["vout"].append(int(vis10[n_in:].sum()))
        rec["alsum"].append(float(al.sum()))
        mc = am.vs(sd, pv, (0.0, 0.0, 0.0))
        Pw = am.to_world_pt(mc["P"], eye, yaw, pitch)
        if prev is not None:
            pPw, ps_, pvis, pmov = prev
            ok = vis & pvis & (mc["s"] >= ps_)
            if ok.any():
                rec["jump"] = max(rec["jump"], float(np.linalg.norm(Pw[ok] - pPw[ok], axis=1).max()))
                if not moving and not pmov:
                    d1 = pPw[ok] - eye
                    d2 = Pw[ok] - eye
                    c = np.sum(d1 * d2, 1) / (np.linalg.norm(d1, axis=1) * np.linalg.norm(d2, axis=1))
                    w = np.degrees(np.arccos(np.clip(c, -1, 1))) * FPS
                    rec["spd"].extend(w[al[ok] > 0.1].tolist())
        prev = (Pw, mc["s"].copy(), vis, moving)
        if want:
            kt = min(keep, key=lambda x: abs(x - t))
            snaps[kt] = dict(pv=pv, eye=eye.copy(), yaw=yaw, pitch=pitch, S=S, ph=ph, Ein=air.Ein, Eout=air.Eout,
                             Fout=air.Fout, glob=air.Glob, m=mc, sd=sd)
    for k in ("t", "S", "v", "Ein", "Eout", "glob", "vin", "vout", "cov", "alsum", "ph", "rate"):
        rec[k] = np.array(rec[k])
    return rec, snaps


def latencias(rec, cycle, lag, start_cycle=1):
    """Desde que el USUARIO empieza a inhalar (t = ciclo + lag) hasta 20 motas de inhalar con alfa > 0,1; idem
    exhalar."""
    t = rec["t"]
    out = []
    for nombre, clave, t0 in (("inhalar", "vin", start_cycle * cycle[0] + lag),
                              ("exhalar", "vout", start_cycle * cycle[0] + lag + cycle[1] + cycle[2])):
        idx = np.where((t >= t0) & (rec[clave] >= 20))[0]
        out.append((nombre, (t[idx[0]] - t0) if len(idx) else float("nan")))
    return out


def _pv_estado(Tin, Tout, Ein, Eout, rin, rout, yaw=0.0, pitch=0.0, eye=np.zeros(3), glob=1.0):
    st = am.AirBP(eye, yaw, pitch)
    st.Tin, st.Tout, st.Fout, st.Ein, st.Eout, st.InRate, st.OutRate, st.Glob = Tin, Tout, 1.5, Ein, Eout, rin, rout, glob
    return st.push(eye, yaw, pitch)


def _ang(P):
    az = np.degrees(np.arctan2(P[:, 1], P[:, 0]))
    el = np.degrees(np.arctan2(P[:, 2], np.hypot(P[:, 0], P[:, 1])))
    return az, el


def ruido_y_pausas(sig, dr, pacer=(4.0, 3.0, 4.0, 3.0), ciclos=8, seeds=(1, 2, 3)):
    """La senal REAL (BellyNoisy: ruido OU del mando + deriva del sostenido) por el seguidor del rig y el BP."""
    res = dict(quieto=[], eout=[], cambios=[], rate=[], lat_in=[], lat_out=[])
    T = sum(pacer)
    for sd_ in seeds:
        air = am.AirBP(EYE0, 0.0, -2.0)
        rig = am.RigFollower(s0=-1.0)
        src = am.BellyNoisy(sig, dr, pacer=pacer, seed=sd_)
        t_, fl, rin, rout, ein, eout = [], [], [], [], [], []
        for k in range(int(ciclos * T * FPS)):
            t = k * DT
            y, _ = src(t, DT)
            air.step(DT, rig.step(y, DT), 1.0, EYE0, 0.0, -2.0)
            t_.append(t); fl.append(air.Flow); rin.append(air.InRate); rout.append(air.OutRate)
            ein.append(air.Ein); eout.append(air.Eout)
        t_, fl, rin, rout, ein, eout = map(np.array, (t_, fl, rin, rout, ein, eout))
        for c in range(2, ciclos):
            t0 = c * T + 0.4
            for ini, dur, arriba in ((pacer[0], pacer[1], True), (pacer[0] + pacer[1] + pacer[2], pacer[3], False)):
                if dur <= 0:
                    continue
                m = (t_ >= t0 + ini + dur / 2) & (t_ < t0 + ini + dur)
                res["quieto"].append(1.0 - float(((rin[m] > 0) | (rout[m] > 0)).mean()))
                m = (t_ >= t0 + ini + 0.5) & (t_ < t0 + ini + dur)
                res["cambios"].append(int(np.sum(np.diff(fl[m]) != 0)))
                if arriba:
                    res["eout"].append(float(eout[m].max()))
            k = np.where((t_ >= t0) & (ein > 0.5))[0]
            if len(k):
                res["lat_in"].append(t_[k[0]] - t0)
            k = np.where((t_ >= t0 + pacer[0] + pacer[1]) & (eout > 0.5))[0]
            if len(k):
                res["lat_out"].append(t_[k[0]] - t0 - pacer[0] - pacer[1])
        res["rate"].append(air.RateBpm)
    return {k: np.array(v) for k, v in res.items()}


def giro(grados, t_giro, sd):
    """Giro de yaw de 'grados' en 0,8 s (coseno). Velocidad de las motas visibles (alfa > 0,1, ojo central) RESPECTO
    DEL MUNDO: p90 en la ventana del giro (y los 2 s siguientes) contra el p90 del segundo anterior (su movimiento
    propio). Devuelve (p90 base, p90 max en el giro, s hasta volver a 50 motas visibles)."""
    air = am.AirBP(EYE0, 0.0, -2.0)
    rig = am.RigFollower(s0=-1.0)
    prev, filas, vis_t = None, [], []
    for k in range(int((t_giro + 3.0) * FPS)):
        t = k * DT
        y, _ = am.belly_target(t)
        S = rig.step(y, DT)
        p = min(max((t - t_giro) / 0.8, 0.0), 1.0)
        yaw = grados * 0.5 * (1 - math.cos(math.pi * p))
        air.step(DT, S, 1.0, EYE0, yaw, -2.0)
        if t < t_giro - 1.2:
            continue
        m = am.vs(sd, air.push(EYE0, yaw, -2.0))
        Pw = am.to_world_pt(m["P"], EYE0, yaw, -2.0)
        vis = m["al"] > 0.1
        vis_t.append((t - t_giro, int(vis.sum())))
        if prev is not None:
            ok = vis & prev[1]
            if ok.sum() > 5:
                d0, d1 = prev[0][ok] - EYE0, Pw[ok] - EYE0
                c = np.sum(d0 * d1, 1) / (np.linalg.norm(d0, axis=1) * np.linalg.norm(d1, axis=1))
                filas.append((t - t_giro, np.percentile(np.degrees(np.arccos(np.clip(c, -1, 1))) * FPS, 90)))
        prev = (Pw, vis)
    f = np.array(filas)
    vt = np.array(vis_t)
    base = f[f[:, 0] < 0.0, 1].max()
    giro_ = f[(f[:, 0] >= 0.0) & (f[:, 0] < 2.8), 1].max()
    vuelta = vt[(vt[:, 0] > 0.8) & (vt[:, 1] >= 50)]
    return base, giro_, (vuelta[0, 0] if len(vuelta) else float("nan"))


def legibilidad(sd):
    """Movimiento que ve el usuario en plena corriente (cabeza quieta, ojo central, alfa > 0,1)."""
    out = {}
    for nombre, flag, rin, rout, Ein, Eout in (("inhalar", 0, 0.225, 0.0, 1.0, 0.0), ("exhalar", 1, 0.0, 0.2, 0.0, 1.0)):
        ve, va = [], []
        for T0 in np.linspace(0, 1, 40, endpoint=False):
            a = am.vs(sd, _pv_estado(T0, T0, Ein, Eout, rin, rout))
            b = am.vs(sd, _pv_estado(T0 + rin * DT, T0 + rout * DT, Ein, Eout, rin, rout))
            m = (sd["flag"] == flag) & (a["al"] > 0.1) & (b["al"] > 0.1) & (b["s"] > a["s"])
            az0, el0 = _ang(a["P"][m])
            az1, el1 = _ang(b["P"][m])
            ve += ((el1 - el0) / DT).tolist()
            va += ((np.abs(az1) - np.abs(az0)) / DT).tolist()
        ve, va = np.array(ve), np.array(va)
        om = np.hypot(ve, va)
        out[nombre] = dict(el=np.median(ve), baja=100 * np.mean(ve < 0), lat=np.median(va),
                           cociente=abs(np.median(ve)) / max(abs(np.median(va)), 1e-6),
                           p50=np.median(om), p90=np.percentile(om, 90), p99=np.percentile(om, 99))
    return out


def distancias(sd):
    out = {}
    for nombre, flag, Ein, Eout in (("inhalar", 0, 1, 0), ("exhalar", 1, 0, 1)):
        ds, ws = [], []
        for T0 in np.linspace(0, 1, 40, endpoint=False):
            r = am.vs(sd, _pv_estado(T0, T0, Ein, Eout, 0.0, 0.0))
            m = (sd["flag"] == flag) & (r["al"] > 0.002)
            ds += r["dist"][m].tolist()
            ws += r["al"][m].tolist()
        ds, ws = np.array(ds), np.array(ws)
        o = np.argsort(ds)
        cw = np.cumsum(ws[o]) / ws.sum()
        out[nombre] = dict(m40=100 * ws[ds < 40].sum() / ws.sum(), m50=100 * ws[ds < 50].sum() / ws.sum(),
                           med=ds[o][np.searchsorted(cw, 0.5)])
    return out


def pluma_sobre_metaball(sd, radio=16.8):
    """Alfa de la pluma dentro del disco angular del metaball (centro (380, 0, 125), radio angular 16,8 grados)."""
    MB = np.array([380.0, 0.0, 125.0]) - EYE0
    mbd = MB / np.linalg.norm(MB)
    tot = den = 0.0
    for T0 in np.linspace(0, 1, 40, endpoint=False):
        r = am.vs(sd, _pv_estado(T0, T0, 0.0, 1.0, 0.0, 0.0, pitch=-2.0, eye=EYE0))
        m = sd["flag"] == 1
        P = am.to_world_pt(r["P"][m], EYE0, 0.0, -2.0) - EYE0
        c = (P @ mbd) / np.linalg.norm(P, axis=1)
        dentro = np.degrees(np.arccos(np.clip(c, -1, 1))) < radio
        tot += r["al"][m].sum()
        den += r["al"][m][dentro].sum()
    return 100 * den / tot


def mirada_abajo(sd):
    out = []
    for pitch in (0.0, -10.0, -20.0, -35.0):
        fila = []
        for pb in (0.8, -0.8):
            tot = 0.0
            for T in np.linspace(0.02, 0.98, 12):
                b = am.AirBP(np.zeros(3), 0.0, pitch)
                b.Tin = b.Tout = T
                b.Fout, b.Ein, b.Eout, b.Glob = 1.5, max(pb, 0), max(-pb, 0), 1.0
                b.YawLag, b.PitchLag = 0.0, pitch
                tot += am.vs(sd, b.push(np.zeros(3), 0.0, pitch), camL=np.array([0.0, -3.2, 0.0]))["al"].sum()
            fila.append(tot / 12)
        out.append((pitch, fila[0], fila[1]))
    return out


def pixeles(sd):
    out = []
    for ppd in (20.0, 25.0):
        for nombre, flag, Ein, Eout in (("inhalar", 0, 1, 0), ("exhalar", 1, 0, 1)):
            fw, w = [], []
            for T in np.linspace(0, 1, 40, endpoint=False):
                r = am.vs(sd, _pv_estado(T, T, Ein, Eout, 0.0, 0.0))
                m = (sd["flag"] == flag) & (r["al"] > 0.05)
                fw += (0.54 * np.degrees(2 * r["hsz"][m] / r["dist"][m]) * ppd).tolist()
                w += r["al"][m].tolist()
            fw, w = np.array(fw), np.array(w)
            out.append((ppd, nombre, np.median(fw), np.percentile(fw, 10), 100 * w[fw < 2].sum() / w.sum()))
    return out


def texto_resultados():
    lines = []
    T = 14.0
    sd = am.seeds()
    rec, _ = run(5 * T + 2.0)
    spd = np.array(rec["spd"]) if rec["spd"] else np.zeros(1)
    lines.append("SIM aliento visible rev. 2 (cadena completa rig -> MPC -> BP -> VS), 5 ciclos 4-3-4-3 a 72 Hz, con giro de 30 grados "
                 "(ciclo 3), mirada al sensor pitch -35 (ciclo 4) e inclinacion de 8 cm (ciclo 5)")
    lines.append("  mota visible (alfa > 0,02) mas cercana a un ojo: %.1f cm   (NearMin %g, NearFull %g)" % (rec["mind"], am.MAT["NearMin"], am.MAT["NearFull"]))
    lines.append("  elevacion maxima de una mota visible respecto de la mirada: %.2f grados   (ElevMax %g)" % (rec["maxel"], am.MAT["ElevMax"]))
    lines.append("  motas con alfa > 0,1: inhalar max %d, exhalar max %d" % (rec["vin"].max(), rec["vout"].max()))
    lines.append("  cobertura de pantalla (25 px/grado, quad entero, por ojo): media %.3f %%, max %.3f %%"
                 % (100 * rec["cov"].mean(), 100 * rec["cov"].max()))
    lines.append("  velocidad angular de las motas con alfa > 0,1, cabeza quieta, todo el ciclo (grados/s): p50 %.1f  p90 %.1f  p99 %.1f  max %.1f"
                 % (np.median(spd), np.percentile(spd, 90), np.percentile(spd, 99), spd.max()))
    lines.append("  salto maximo de una mota visible entre cuadros (mundo): %.2f cm" % rec["jump"])
    lines.append("  retraso maximo del marco del aire respecto de la cabeza (yaw): %.1f grados" % rec["lagmax"])
    for nombre, lat in latencias(rec, (T, 4.0, 3.0), 0.4, start_cycle=1):
        lines.append("  latencia %s (ciclo 2): 20 motas con alfa > 0,1 a los %.2f s de que el usuario empieza" % (nombre, lat))
    t = rec["t"]
    k_hold_end = np.argmin(np.abs(t - (T + 0.4 + 4.0 + 3.0)))
    k_hold_start = np.argmin(np.abs(t - (T + 0.4 + 4.0 + 0.3)))
    lines.append("  retener: Ein %.2f al empezar -> %.2f a los 3 s (suspendidas, se apagan con HoldTau %.1f s)"
                 % (rec["Ein"][k_hold_start], rec["Ein"][k_hold_end], am.BP["HoldTau"]))
    lines.append("")
    lines.append("SENAL REAL (revision costo/confort): belly ideal + ruido OU del mando (tau 0,4 s) + deriva del sostenido, 4-3-4-3, 3 semillas")
    lines.append("  %-26s %9s %9s %9s %9s %8s %8s" % ("caso", "quieto2a%", "Eout_arr", "cambios", "resp/min", "latIn", "latOut"))
    for nombre, sg, dr in (("ideal", 0.0, 0.0), ("ruido 0,03 + deriva 0,2", 0.03, 0.2), ("ruido 0,05 + deriva 0,15", 0.05, 0.15),
                           ("ruido 0,06 + deriva 0,15", 0.06, 0.15), ("ruido 0,08 + deriva 0,2", 0.08, 0.2)):
        r = ruido_y_pausas(sg, dr)
        lines.append("  %-26s %9.1f %9.2f %9.2f %9.2f %8.2f %8.2f" % (nombre, 100 * r["quieto"].mean(), r["eout"].max(), r["cambios"].mean(),
                                                                    r["rate"].mean(), r["lat_in"].mean(), r["lat_out"].mean()))
    lines.append("  (quieto2a = % de la 2a mitad de las pausas con la cinta quieta, meta >= 98; Eout_arr = la pluma con el aire")
    lines.append("   retenido ARRIBA, meta < 0,1; cambios = alternancias del modo por pausa, meta < 2; real 4,29 resp/min;")
    lines.append("   latIn / latOut = Ein / Eout > 0,5 desde que el usuario empieza)")
    lines.append("")
    for calm in (True, False):
        vals, rates = [], []
        for bpm in (4.3, 6.0, 10.0, 15.0, 20.0):
            per = 60.0 / bpm
            cyc = (per * 0.5, 0.0, per * 0.5, 0.0) if bpm > 4.5 else (4.0, 3.0, 4.0, 3.0)
            bp = None if calm else dict(FastFloor=1.0)
            r, _ = run(max(6 * per, 40.0), pacer=cyc, events=False, bp=bp, rates=True)
            m = r["t"] > 3 * per
            vals.append("%g: %.0f" % (bpm, r["alsum"][m].mean()))
            rates.append("%g -> %.1f" % (bpm, r["rate"][-1]))
        lines.append("  ritmo: suma media de alfa visible por respiraciones/min (%s RateCalm): %s" % ("con" if calm else "SIN", " · ".join(vals)))
    lines.append("  ritmo medido por el BP (RateBpm al final, real -> medido): %s" % " · ".join(rates))
    lines.append("")
    lines.append("GIRO DE CABEZA (yaw en 0,8 s, coseno): p90 de la velocidad de las motas visibles RESPECTO DEL MUNDO")
    for grados in (30.0, 90.0):
        for fase, tg in (("exhalando", 14.0 + 0.4 + 4.0 + 3.0 + 1.0), ("inhalando", 14.0 + 0.4 + 1.0)):
            b, g, v = giro(grados, tg, sd)
            lines.append("  %3.0f grados %s: movimiento propio antes del giro p90 %.1f -> durante y despues p90 max %.1f grados/s (arrastre %+.1f); "
                         "vuelve a 50 motas visibles a los %.2f s" % (grados, fase, b, g, g - b, v))
    lines.append("")
    lg = legibilidad(sd)
    for nombre in ("inhalar", "exhalar"):
        x = lg[nombre]
        lines.append("LEGIBILIDAD %s (plena corriente, cabeza quieta): elevacion mediana %+.2f grados/s (%.0f %% bajando), azimut hacia el "
                     "centro %+.2f grados/s, |vertical|/|lateral| %.1f; velocidad angular p50 %.1f p90 %.1f p99 %.1f grados/s"
                     % (nombre.upper(), x["el"], x["baja"], x["lat"], x["cociente"], x["p50"], x["p90"], x["p99"]))
    ds = distancias(sd)
    for nombre in ("inhalar", "exhalar"):
        x = ds[nombre]
        lines.append("DISTANCIA %s: alfa visible a < 40 cm %.0f %%, a < 50 cm %.0f %%, mediana ponderada %.0f cm" % (nombre.upper(), x["m40"], x["m50"], x["med"]))
    lines.append("PLUMA SOBRE EL METABALL: %.0f %% del alfa de la pluma dentro del disco angular del metaball (radio 16,8 grados; OutTilt %g)"
                 % (pluma_sobre_metaball(sd), am.MAT["OutTilt"]))
    lines.append("MIRADA ABAJO (marco asentado; PitchFollow %g), alfa total medio inhala / exhala: %s" % (am.BP["PitchFollow"], " · ".join(
        "pitch %+.0f: %.0f / %.0f" % x for x in mirada_abajo(sd))))
    lines.append("PIXELES (FWHM del punto = 0,54 x lado; MinDeg %g con alfa x (fisico/dibujado)^2): %s" % (am.K["MinDeg"], " · ".join(
        "PPD %.0f %s med %.2f p10 %.2f (%.0f %% del alfa < 2 px)" % x for x in pixeles(sd))))
    lines.append("")
    nq = am.N_IN + am.N_OUT
    lines.append("  costo estimado VS: %d quads x 4 vertices x 2 vistas x ~280 op-eq (+ binning) = %.1f M op-eq -> %.3f-%.3f ms "
                 "(x2 si Unreal compila el Custom dos veces, WPO + interpolador)"
                 % (nq, nq * 8 * 280 / 1e6, nq * 8 * 280 / 1e6 * 0.0055, nq * 8 * 280 / 1e6 * 0.011))
    lines.append("  costo estimado PS: cobertura media %.3f %% x ~12 op-eq x 3 (quads chicos) = %.4f ms a 150 op-eq/px por ms"
                 % (100 * rec["cov"].mean(), rec["cov"].mean() * 12 * 3 / 150.0))
    r6, _ = run(4 * 12.0 + 2.0, pacer=(6.0, 0.0, 6.0, 0.0), events=False)
    sp6 = np.array(r6["spd"]) if r6["spd"] else np.zeros(1)
    lines.append("  ritmo 6-0-6-0: motas alfa>0,1 inhalar max %d, exhalar max %d; velocidad p99 %.1f grados/s; cobertura max %.3f %%"
                 % (r6["vin"].max(), r6["vout"].max(), np.percentile(sp6, 99), 100 * r6["cov"].max()))
    return lines, rec


# ---------------------------------------------------------------------------------------------
# Dibujo
# ---------------------------------------------------------------------------------------------
W, H = 1052, 862
FPX = (W / 2) / math.tan(math.radians(45.0))


def to_lin(a):
    return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)


def to_srgb(a):
    a = np.clip(a, 0, 1)
    return np.where(a <= 0.0031308, 12.92 * a, 1.055 * a ** (1 / 2.4) - 0.055)


def load_bg(tag):
    from PIL import Image
    for ruta in (os.path.join(SAL, "preview_valle_t0_%s.png" % tag), os.path.join(IDEAS, "preview_valle_t0_%s.png" % tag)):
        if os.path.exists(ruta):
            return to_lin(np.asarray(Image.open(ruta).convert("RGB")).astype(np.float64) / 255.0), ruta
    return np.ones((H, W, 3)) * np.array([0.5, 0.52, 0.75]), "(fondo liso)"


def bg_for(S, bgs):
    neu, inh, exh = bgs
    return neu + (inh - neu) * S if S >= 0 else neu + (exh - neu) * (-S)


def splat_fp(img, m, zoom=1.0, x0=0.0, y0=0.0, gain=1.0):
    """Motas en primera persona (camara = la cabeza; local de la camara = ejes de la vista). Perfil del PS
    (1 - r^2)^2 x alfa, compuesto premultiplicado en lineal, de atras hacia adelante."""
    P = m["P"]
    x = P[:, 0]
    ok = (x > 1.0) & (m["al"] > 0.004)
    h, w = img.shape[:2]
    col_in, col_out = np.array(am.MAT["InColor"]), np.array(am.MAT["OutColor"])
    for k in np.where(ok)[0][np.argsort(-x[ok])]:
        cx = (W / 2 + FPX * P[k, 1] / x[k] - x0) * zoom
        cy = (H / 2 - FPX * P[k, 2] / x[k] - y0) * zoom
        r = max(FPX * m["hsz"][k] / x[k] * zoom, 0.35)
        ext = int(math.ceil(r)) + 1
        xa, xb, ya, yb = int(cx) - ext, int(cx) + ext + 1, int(cy) - ext, int(cy) + ext + 1
        if xb < 0 or yb < 0 or xa >= w or ya >= h:
            continue
        xa, ya, xb, yb = max(xa, 0), max(ya, 0), min(xb, w), min(yb, h)
        gx, gy = np.meshgrid(np.arange(xa, xb) + 0.5, np.arange(ya, yb) + 0.5)
        d2 = ((gx - cx) ** 2 + (gy - cy) ** 2) / (r * r)
        prof = np.clip(1.0 - d2, 0.0, 1.0) ** 2
        if r < 1.2:                                  # subpixel: conservar la energia (el MSAA la promedia igual)
            prof = prof * (1.2 / r) ** 2 * 0.5
        al = np.clip(prof * m["al"][k] * gain, 0, 1)[..., None]
        col = col_out if m["isOut"][k] > 0.5 else col_in
        img[ya:yb, xa:xb] = img[ya:yb, xa:xb] * (1 - al) + col[None, None, :] * al
    return img


def pil(lin):
    from PIL import Image
    return Image.fromarray((to_srgb(lin) * 255.0 + 0.5).astype(np.uint8))


def font(sz):
    from PIL import ImageFont
    for f in ("C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf"):
        if os.path.exists(f):
            return ImageFont.truetype(f, sz)
    return ImageFont.load_default()


def label(im, text, sub=None, pos=(12, 8), sz=24):
    from PIL import ImageDraw
    d = ImageDraw.Draw(im)
    f1, f2 = font(sz), font(int(sz * 0.7))
    wmax = max(d.textlength(text, font=f1), d.textlength(sub or "", font=f2))
    d.rectangle([pos[0] - 6, pos[1] - 4, pos[0] + 10 + wmax, pos[1] + (int(sz * 2.2) if sub else int(sz * 1.35))],
                fill=(20, 22, 40))
    d.text(pos, text, fill=(240, 240, 250), font=f1)
    if sub:
        d.text((pos[0], pos[1] + int(sz * 1.25)), sub, fill=(200, 200, 220), font=f2)
    return im


# ---- vista de costado con cabeza de referencia (mundo, plano XZ; la cabeza mira a +X) ----
SX0, SX1, SZ0, SZ1 = -32.0, 150.0, 52.0, 160.0


def side_view(snap, scale=4.0, title=None, sub=None):
    from PIL import Image, ImageDraw
    Wd, Hd = int((SX1 - SX0) * scale), int((SZ1 - SZ0) * scale)
    img = np.zeros((Hd, Wd, 3))
    gz = np.linspace(1, 0, Hd)[:, None, None]
    img[:] = to_lin(np.array([0.56, 0.60, 0.82])) * (0.75 + 0.25 * gz)
    eye, yaw, pitch = snap["eye"], snap["yaw"], snap["pitch"]
    X = lambda x: (x - SX0) * scale
    Z = lambda z: (SZ1 - z) * scale
    m = snap["m"]
    Pw = am.to_world_pt(m["P"], eye, yaw, pitch)
    order = np.argsort(Pw[:, 1])
    col_in, col_out = np.array(am.MAT["InColor"]), np.array(am.MAT["OutColor"])
    for k in order:
        a = m["al"][k]
        if a < 0.01:
            continue
        cx, cy = X(Pw[k, 0]), Z(Pw[k, 2])
        r = 1.6
        xa, xb, ya, yb = int(cx - 3), int(cx + 4), int(cy - 3), int(cy + 4)
        if xb < 0 or yb < 0 or xa >= Wd or ya >= Hd:
            continue
        xa, ya, xb, yb = max(xa, 0), max(ya, 0), min(xb, Wd), min(yb, Hd)
        gx, gy = np.meshgrid(np.arange(xa, xb) + 0.5, np.arange(ya, yb) + 0.5)
        prof = np.clip(1.0 - ((gx - cx) ** 2 + (gy - cy) ** 2) / (r * r), 0, 1) ** 2
        al = np.clip(prof * min(1.0, a * 1.6), 0, 1)[..., None]
        col = col_out if m["isOut"][k] > 0.5 else col_in
        img[ya:yb, xa:xb] = img[ya:yb, xa:xb] * (1 - al) + col * al
    im = pil(img)
    d = ImageDraw.Draw(im, "RGBA")
    F, R, U = am.head_basis(yaw, pitch)
    # limites de confort alrededor del ojo
    for rad, dash in ((am.MAT["NearMin"], (255, 90, 90, 150)), (am.MAT["NearFull"], (255, 160, 120, 110))):
        d.ellipse([X(eye[0] - rad), Z(eye[2] + rad), X(eye[0] + rad), Z(eye[2] - rad)], outline=dash, width=2)
    # mirada y tope de elevacion
    g = eye + F * 180.0
    d.line([X(eye[0]), Z(eye[2]), X(g[0]), Z(g[2])], fill=(20, 20, 40, 160), width=1)
    el = math.radians(am.MAT["ElevMax"])
    Fe = F * math.cos(el) + U * math.sin(el)
    ge = eye + Fe * 180.0
    d.line([X(eye[0]), Z(eye[2]), X(ge[0]), Z(ge[2])], fill=(220, 60, 60, 170), width=2)
    # cabeza de referencia (perfil simple, cm respecto de los ojos): craneo, frente, nariz, labios, menton, cuello.
    # La "boca" del modelo (MouthFwd, MouthDown) es el punto de SALIDA del aliento, apenas delante de los labios.
    def P2(fw, up):
        q = eye + F * fw + U * up
        return (X(q[0]), Z(q[2]))
    c = eye - F * 8.5 + U * 2.5
    d.ellipse([X(c[0] - 10.5), Z(c[2] + 11.5), X(c[0] + 10.5), Z(c[2] - 11.5)], fill=(40, 42, 70, 235))
    perfil = [(-6, 9), (0.5, 6), (1.5, 2), (1.0, 0.5), (1.8, -1.0), (4.3, -4.2), (2.4, -5.4), (3.4, -6.6),
              (2.6, -7.6), (3.2, -8.6), (2.0, -9.6), (2.6, -11.8), (0.5, -13.0), (-4.5, -12.5), (-8, -9)]
    d.polygon([P2(a, b) for a, b in perfil], fill=(40, 42, 70, 235))
    d.polygon([P2(-9.5, -9), P2(-2.0, -12.5), P2(-2.5, -40), P2(-10.0, -40)], fill=(40, 42, 70, 235))
    mo = eye + F * am.BP["MouthFwd"] - U * am.BP["MouthDown"]
    d.rectangle([X(mo[0]) - 4, Z(mo[2]) - 2, X(mo[0]) + 4, Z(mo[2]) + 2], fill=(235, 150, 150, 255))
    f = font(15)
    d.text((X(eye[0]) - 30, Z(eye[2]) - 26), "ojos", fill=(250, 250, 255), font=f)
    d.text((X(mo[0]) + 8, Z(mo[2]) - 4), "boca (salida del aliento)", fill=(255, 210, 210), font=f)
    d.text((X(g[0]) - 140, Z(g[2]) - 20), "mirada", fill=(20, 20, 40), font=f)
    d.text((X(ge[0]) - 180, Z(ge[2]) + 2), "tope %g grados" % am.MAT["ElevMax"], fill=(200, 40, 40), font=f)
    d.text((X(eye[0] + am.MAT["NearFull"]) + 4, Z(eye[2]) + 4), "%g / %g cm" % (am.MAT["NearMin"], am.MAT["NearFull"]), fill=(200, 60, 60), font=f)
    d.text((Wd - 150, 10), "metaball a 3,8 m ->", fill=(20, 20, 40), font=f)
    if title:
        label(im, title, sub, pos=(10, Hd - 58), sz=22)
    return im


def main():
    os.makedirs(SAL, exist_ok=True)
    if "--solo-imagenes" in sys.argv:
        return imagenes()
    lines, rec = texto_resultados()
    with open(os.path.join(SAL, "sim_aliento_resultados.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    if "--sin-imagenes" in sys.argv:
        return
    imagenes()


def imagenes():
    from PIL import Image
    bgs, rutas = [], []
    for tag in ("neutro", "inhala", "exhala"):
        b, r = load_bg(tag)
        bgs.append(b)
        rutas.append(r)
    print("fondos:", rutas)
    T, lag = 14.0, 0.4
    c = T + lag                                  # ciclo 2, cabeza quieta
    inst = [("Inhala (2,5 s de 4)", c + 2.5), ("Retiene (1,5 s de 3)", c + 5.5),
            ("Exhala (2,0 s de 4)", c + 9.0), ("Pausa (1,5 s de 3)", c + 12.5)]
    _, snaps = run(2 * T + 1.0, events=False, keep=[t for _, t in inst], metrics=False)
    # ---- primera persona: fila entera + recortes x2 de la banda baja ----
    tw, th = 700, int(H * 700 / W)
    x0, y0, cw, ch = 176, 470, 700, 392
    fila, recortes = [], []
    for txt, t in inst:
        sn = snaps[t]
        bg = bg_for(sn["S"], bgs)
        sub = "S %+.2f · E_in %.2f · E_out %.2f · frente %.2f" % (sn["S"], sn["Ein"], sn["Eout"], min(sn["Fout"], 1.0))
        full = splat_fp(bg.copy(), sn["m"])
        fila.append(label(pil(full).resize((tw, th), Image.LANCZOS), txt, sub))
        cr = np.kron(bg[y0:y0 + ch, x0:x0 + cw], np.ones((2, 2, 1)))
        cr = splat_fp(cr, sn["m"], zoom=2.0, x0=x0, y0=y0)
        recortes.append(label(pil(cr).resize((tw, int(tw * ch / cw)), Image.LANCZOS), txt + " · banda baja x2",
                              "tamano angular real; la Quest tiene ~2,7x mas pixeles por grado"))
    rh = recortes[0].size[1]
    canvas = Image.new("RGB", (4 * tw, th + 6 + rh), (14, 15, 26))
    for i, im in enumerate(fila):
        canvas.paste(im, (i * tw, 0))
    for i, im in enumerate(recortes):
        canvas.paste(im, (i * tw, th + 6))
    canvas.save(os.path.join(SAL, "aliento_primera_persona.png"))
    # ---- costado ----
    sv = [side_view(snaps[t], 4.0, txt, "S %+.2f · E_in %.2f · E_out %.2f" % (snaps[t]["S"], snaps[t]["Ein"], snaps[t]["Eout"]))
          for txt, t in inst]
    sw, sh = sv[0].size
    canvas = Image.new("RGB", (2 * sw + 6, 2 * sh + 6), (14, 15, 26))
    for i, im in enumerate(sv):
        canvas.paste(im, ((i % 2) * (sw + 6), (i // 2) * (sh + 6)))
    canvas.save(os.path.join(SAL, "aliento_lateral.png"))
    # ---- GIF de un ciclo ----
    fps_gif = 8
    tiempos = [c + k / fps_gif for k in range(int(T * fps_gif))]
    _, sg = run(c + T + 0.5, events=False, keep=tiempos, metrics=False)
    frames = []
    for t in tiempos:
        sn = sg[min(sg.keys(), key=lambda x: abs(x - t))]
        bg = bg_for(sn["S"], bgs)
        cr = splat_fp(bg[y0 - 60:y0 + ch, x0 - 60:x0 + cw + 60].copy(), sn["m"], zoom=1.0, x0=x0 - 60, y0=y0 - 60)
        fp = pil(cr).resize((560, int(560 * (ch + 60) / (cw + 120))), Image.LANCZOS)
        fase = ("INHALA", "RETIENE", "EXHALA", "PAUSA")[sn["ph"]]
        label(fp, "Primera persona · %s" % fase, "S %+.2f · t %.1f s" % (sn["S"], t - c), sz=18)
        sd_ = side_view(sn, 2.6)
        sd_ = sd_.resize((int(sd_.size[0] * fp.size[1] / sd_.size[1]), fp.size[1]), Image.LANCZOS)
        fr = Image.new("RGB", (fp.size[0] + sd_.size[0] + 4, fp.size[1]), (14, 15, 26))
        fr.paste(fp, (0, 0))
        fr.paste(sd_, (fp.size[0] + 4, 0))
        frames.append(fr.convert("P", palette=Image.ADAPTIVE, colors=160))
    frames[0].save(os.path.join(SAL, "aliento_ciclo.gif"), save_all=True, append_images=frames[1:],
                   duration=int(1000 / fps_gif), loop=0, optimize=True)
    # ---- estelas: 1,2 s de movimiento en un cuadro (la direccion del flujo, que el cuadro quieto no muestra) ----
    estelas(bgs, c, x0, y0, cw, ch)
    # ---- geometria (matplotlib) ----
    geometria()
    print("IMAGENES LISTAS en", SAL)


def estelas(bgs, c, x0, y0, cw, ch):
    """Primera persona, banda baja x2: cada mota dibujada en 12 instantes de una ventana de 1,2 s, del mas viejo
    (tenue) al actual (pleno). Se lee hacia donde va el aire: al inhalar converge hacia abajo y al centro (la boca,
    fuera de cuadro); al exhalar nace abajo y se abre hacia el metaball."""
    from PIL import Image
    ventanas = [("Inhala: estela de 1,2 s (1,2 a 2,4 s de 4)", c + 1.2, c + 2.4, "inhala"),
                ("Exhala: estela de 1,2 s (0,6 a 1,8 s de 4)", c + 7.6, c + 8.8, "exhala")]
    tiles = []
    for txt, ta, tb, tag in ventanas:
        ts = list(np.linspace(ta, tb, 12))
        _, sn = run(tb + 0.1, events=False, keep=ts, metrics=False)
        bg = bgs[1] if tag == "inhala" else bgs[2]
        cr = np.kron(bg[y0:y0 + ch, x0:x0 + cw], np.ones((2, 2, 1)))
        for j, t in enumerate(ts):
            m = dict(sn[min(sn.keys(), key=lambda x: abs(x - t))]["m"])
            cr = splat_fp(cr, m, zoom=2.0, x0=x0, y0=y0, gain=0.25 + 0.75 * (j / (len(ts) - 1)) ** 2)
        tiles.append(label(pil(cr).resize((1000, int(1000 * ch / cw)), Image.LANCZOS), txt,
                           "cada mota en 12 instantes: tenue = antes, pleno = ahora (cabeza quieta)"))
    can = Image.new("RGB", (2000 + 6, tiles[0].size[1]), (14, 15, 26))
    can.paste(tiles[0], (0, 0))
    can.paste(tiles[1], (1006, 0))
    can.save(os.path.join(SAL, "aliento_estelas.png"))


def geometria():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    sd = am.seeds()
    rng = np.random.default_rng(2)
    idx_in = rng.choice(sd["n_in"], 30, replace=False)
    idx_out = sd["n_in"] + rng.choice(sd["n_out"], 30, replace=False)
    eye = EYE0

    def caminos(air, idx, yaw, pitch, n=80):
        ss_ = np.linspace(0.001, 0.999, n)
        P = np.zeros((len(idx), n, 3))
        A = np.zeros((len(idx), n))
        sub = {k: (v[idx] if isinstance(v, np.ndarray) else v) for k, v in sd.items()}
        for j, s in enumerate(ss_):
            pv = air.push(eye, yaw, pitch)
            T = (s - sub["e"]) % 1.0
            for kk in range(len(idx)):
                pv2 = dict(pv)
                pv2["AirT"] = np.array([T[kk], T[kk], 1.5, 1.0])
                one = {k: (v[kk:kk + 1] if isinstance(v, np.ndarray) else v) for k, v in sub.items()}
                m = am.vs(one, pv2, (0.0, 0.0, 0.0))
                P[kk, j] = am.to_world_pt(m["P"][0], eye, yaw, pitch)
                A[kk, j] = m["al"][0]
        return P, A

    def estado(yaw_head, yaw_lag, pitch=-2.0):
        air = am.AirBP(eye, yaw_lag, pitch)
        air.YawLag, air.PitchLag = yaw_lag, pitch
        air.MouthW = air.mouth_world(eye, yaw_lag, pitch)
        air.Ein = air.Eout = 1.0
        air.Fout = 1.5
        air.InRate = air.OutRate = 0.12
        air.Glob = 1.0
        return air

    fig, axs = plt.subplots(1, 3, figsize=(21, 7))
    for ax, plano, (yh, yl), titulo in ((axs[0], "lado", (0, 0), "De lado (cm). Azul: inhalar, llega a la boca · Rojo: exhalar, sale de la boca\ntrazo grueso = tramo visible (alfa > 0,02); fino = oculto"),
                                         (axs[1], "planta", (0, 0), "En planta (cm), cabeza quieta. Arriba = derecha del usuario"),
                                         (axs[2], "planta", (30, 6), "Giro de 30 grados en plena inhalacion: el marco del aire va atras\n(mundo) y lo inhalado igual termina en la boca ACTUAL")):
        air = estado(yh, yl)
        for idx, col in ((idx_in, "#5577ff"), (idx_out, "#dd5544")):
            P, A = caminos(air, idx, yh, -2.0)
            a, b = (0, 2) if plano == "lado" else (0, 1)
            for k in range(P.shape[0]):
                ax.plot(P[k, :, a], P[k, :, b], color=col, lw=0.5, alpha=0.2)
                for j in range(P.shape[1] - 1):
                    if A[k, j] > 0.02:
                        ax.plot(P[k, j:j + 2, a], P[k, j:j + 2, b], color=col, lw=1.6, alpha=min(1.0, A[k, j] * 1.8))
        F, R, U = am.head_basis(yh, -2.0)
        mo = eye + F * am.BP["MouthFwd"] - U * am.BP["MouthDown"]
        if plano == "lado":
            for rr, ls in ((am.MAT["NearMin"], "-"), (am.MAT["NearFull"], "--")):
                ax.add_patch(plt.Circle((eye[0], eye[2]), rr, fill=False, ls=ls, color="k", lw=0.8))
            ax.plot([eye[0], 140], [eye[2], eye[2] - 140 * math.tan(math.radians(2))], "k:", lw=0.8)
            ax.plot([eye[0], 140], [eye[2], eye[2] - 140 * math.tan(math.radians(6))], "r:", lw=1.0)
            ax.text(90, eye[2] - 5, "tope %g grados de la mirada" % am.MAT["ElevMax"], color="r", fontsize=9)
            ax.plot(eye[0], eye[2], "ko")
            ax.plot(mo[0], mo[2], "ks")
            tf = math.radians(am.MAT["FocusTilt"] + 2.0)
            fo = mo + am.MAT["FocusDist"] * np.array([math.cos(tf), 0.0, -math.sin(tf)])
            ax.plot(fo[0], fo[2], marker="o", mfc="none", mec="#2244cc", ms=9)
            ax.text(fo[0] + 3, fo[2] - 6, "foco (InFocus %g)" % am.MAT["InFocus"], color="#2244cc", fontsize=9)
            ax.text(-12, eye[2] + 4, "ojos")
            ax.text(mo[0] - 14, mo[2] - 7, "boca")
            ax.set_ylim(40, 162)
        else:
            ax.plot(0, 0, "ko")
            ax.plot(mo[0] - eye[0], mo[1], "ks")
            if yh:
                ax.annotate("", xy=(105 * math.cos(math.radians(yh)), 105 * math.sin(math.radians(yh))), xytext=(0, 0),
                            arrowprops=dict(arrowstyle="->", color="k"))
                ax.text(100 * math.cos(math.radians(yh)) + 3, 100 * math.sin(math.radians(yh)), "cabeza (30)")
                ax.annotate("", xy=(115 * math.cos(math.radians(yl)), 115 * math.sin(math.radians(yl))), xytext=(0, 0),
                            arrowprops=dict(arrowstyle="->", color="#c22"))
                ax.text(118 * math.cos(math.radians(yl)), 118 * math.sin(math.radians(yl)) - 6, "marco del aire (6, con retardo)", color="#c22")
            ax.set_ylim(-80, 80)
        ax.set_xlim(-20, 145)
        ax.set_aspect("equal")
        ax.grid(alpha=0.25)
        ax.set_title(titulo, fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(SAL, "aliento_geometria.png"), dpi=110)
    plt.close(fig)


if __name__ == "__main__":
    main()
