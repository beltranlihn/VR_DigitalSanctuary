# -*- coding: utf-8 -*-
"""Revisor costo/confort: que MOVIMIENTO ve el usuario en la inhalacion y en la exhalacion (modelo verificado = HLSL).
Para cada mota visible (alfa > 0,1, ojo central) en plena corriente, con la cabeza quieta: velocidad en la imagen
(elevacion y azimut, grados/s) y velocidad en profundidad (cm/s). Y el recorrido ANGULAR visible de cada mota a lo
largo de su vida (de s donde se enciende a s donde se apaga)."""
import math, os, sys
import numpy as np
sys.path.insert(0, r"C:\Users\beltr\Desktop\Alma Digital Studio\Projects\VR Unreal\.claude\skills\unreal-vr\scripts")
import breath_air_model as am

sd = am.seeds()
eye = np.zeros(3)
def pv(Tin, Tout, Ein, Eout, rin, rout):
    st = am.AirBP(eye, 0.0, 0.0)
    st.Tin, st.Tout, st.Fout, st.Ein, st.Eout, st.InRate, st.OutRate, st.Glob = Tin, Tout, 1.5, Ein, Eout, rin, rout, 1.0
    return st.push(eye, 0.0, 0.0)

def ang(P):
    az = np.degrees(np.arctan2(P[:, 1], P[:, 0])); el = np.degrees(np.arctan2(P[:, 2], np.hypot(P[:, 0], P[:, 1])))
    return az, el

lines = []
# inhalacion completa en 4 s (v media 0,5/s): InRate = 0,5*0,9*0,5 = 0,225 caminos/s
for nombre, flag, rin, rout, Ein, Eout in (("INHALAR", 0, 0.225, 0.0, 1.0, 0.0), ("EXHALAR", 1, 0.0, 0.2, 0.0, 1.0)):
    dt = 1.0 / 72
    vel_el, vel_az_c, vel_r, tot_el, tot_az, tot_ang, vis_s = [], [], [], [], [], [], []
    for T0 in np.linspace(0, 1, 40, endpoint=False):
        a = am.vs(sd, pv(T0, T0, Ein, Eout, rin, rout))
        b = am.vs(sd, pv(T0 + rin * dt, T0 + rout * dt, Ein, Eout, rin, rout))
        m = (sd["flag"] == flag) & (a["al"] > 0.1) & (b["al"] > 0.1) & (b["s"] > a["s"])
        az0, el0 = ang(a["P"][m]); az1, el1 = ang(b["P"][m])
        vel_el += ((el1 - el0) / dt).tolist()
        vel_az_c += ((np.abs(az1) - np.abs(az0)) / dt).tolist()      # < 0 = hacia el centro
        vel_r += ((np.linalg.norm(b["P"][m], axis=1) - np.linalg.norm(a["P"][m], axis=1)) / dt).tolist()
    vel_el, vel_az_c, vel_r = map(np.array, (vel_el, vel_az_c, vel_r))
    lines.append("%s (cabeza quieta, ojo central, motas con alfa > 0,1):" % nombre)
    lines.append("  vel. elevacion  (grados/s, + sube): mediana %+.2f  p10 %+.2f  p90 %+.2f  | %% bajando %.0f%%"
                 % (np.median(vel_el), np.percentile(vel_el, 10), np.percentile(vel_el, 90), 100 * np.mean(vel_el < 0)))
    lines.append("  vel. azimut hacia el centro (grados/s, - converge): mediana %+.2f  p10 %+.2f  p90 %+.2f"
                 % (np.median(vel_az_c), np.percentile(vel_az_c, 10), np.percentile(vel_az_c, 90)))
    lines.append("  vel. en profundidad (cm/s, - se acerca): mediana %+.1f  p10 %+.1f  p90 %+.1f"
                 % (np.median(vel_r), np.percentile(vel_r, 10), np.percentile(vel_r, 90)))
    # recorrido de cada mota a lo largo de su vida visible (en funcion de s)
    idx = np.where(sd["flag"] == flag)[0][:200]
    for k in idx:
        pts, als = [], []
        for s in np.linspace(0.0, 0.999, 400):
            T = (s - sd["e"][k]) % 1.0
            r = am.vs({kk: (vv[k:k + 1] if isinstance(vv, np.ndarray) else vv) for kk, vv in sd.items()},
                      pv(T, T, Ein, Eout, rin, rout))
            pts.append(r["P"][0]); als.append(r["al"][0])
        pts, als = np.array(pts), np.array(als)
        vm = als > 0.1
        if vm.sum() < 2:
            continue
        az, el = ang(pts[vm])
        tot_el.append(el[-1] - el[0]); tot_az.append(abs(az[-1]) - abs(az[0]))
        d = np.linalg.norm(pts[vm], axis=1)
        tot_ang.append(float(np.degrees(np.arccos(np.clip(np.dot(pts[vm][0], pts[vm][-1]) / (d[0] * d[-1]), -1, 1)))))
        vis_s.append((d[0], d[-1]))
    vis_s = np.array(vis_s)
    lines.append("  vida visible de una mota: recorrido angular total mediana %.1f grados (p90 %.1f); cambio de elevacion"
                 " mediana %+.1f; cambio de |azimut| mediana %+.1f; distancia al ojo al encenderse %.0f cm -> al apagarse %.0f cm"
                 % (np.median(tot_ang), np.percentile(tot_ang, 90), np.median(tot_el), np.median(tot_az),
                    np.median(vis_s[:, 0]), np.median(vis_s[:, 1])))
    lines.append("")
# distancia de lo visible (vergencia/acomodacion): fraccion del alfa visible a menos de 50 cm
for nombre, flag, Ein, Eout in (("INHALAR", 0, 1, 0), ("EXHALAR", 1, 0, 1)):
    ds, ws = [], []
    for T0 in np.linspace(0, 1, 40, endpoint=False):
        r = am.vs(sd, pv(T0, T0, Ein, Eout, 0.0, 0.0))
        m = (sd["flag"] == flag) & (r["al"] > 0.002)
        ds += r["dist"][m].tolist(); ws += r["al"][m].tolist()
    ds, ws = np.array(ds), np.array(ws)
    lines.append("%s: alfa visible ponderado por distancia al ojo: a < 40 cm %.0f%%, < 50 cm %.0f%%, < 60 cm %.0f%%, mediana %.0f cm"
                 % (nombre, 100 * ws[ds < 40].sum() / ws.sum(), 100 * ws[ds < 50].sum() / ws.sum(),
                    100 * ws[ds < 60].sum() / ws.sum(), float(np.median(np.repeat(ds, np.maximum((ws * 50).astype(int), 1))))))
txt = "\n".join(lines)
print(txt)
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "legibilidad_resultados.txt"), "w", encoding="utf-8").write(txt + "\n")
