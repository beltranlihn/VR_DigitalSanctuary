# -*- coding: utf-8 -*-
"""Revisor: que hace el aire cuando la cabeza GIRA (el sim del plan mide la velocidad de las motas solo con la cabeza
quieta). Giro de yaw de GRADOS en 0,8 s (suave, cos) en plena exhalacion y en plena inhalacion. Para cada mota visible
(alfa > 0,1 en el ojo central): velocidad angular RESPECTO DEL MUNDO (lo que induce vection: contenido que se mueve en
el mundo) y respecto de la cabeza. El SpeedFade del VS solo mira el movimiento propio de la mota (InRate/OutRate), no
el arrastre del marco con retardo."""
import math, os, sys
import numpy as np
sys.path.insert(0, r"C:\Users\beltr\Desktop\Alma Digital Studio\Projects\VR Unreal\.claude\skills\unreal-vr\scripts")
import breath_air_model as am
FPS = 72.0; DT = 1 / FPS; EYE = np.array([0.0, 0.0, 120.0])
sd = am.seeds()
out = []
for grados in (30.0, 90.0):
    for fase_nombre, t_giro in (("exhalando", 14.0 + 0.4 + 4.0 + 3.0 + 1.0), ("inhalando", 14.0 + 0.4 + 1.0)):
        air = am.AirBP(EYE, 0.0, -2.0); rig = am.RigFollower(s0=-1.0)
        prevW = None; wv = []; hv = []; vis_n = []
        for k in range(int((t_giro + 4.0) * FPS)):
            t = k * DT
            y, _ = am.belly_target(t, 4.0, 3.0, 4.0, 3.0, lag=0.4)
            S = rig.step(y, DT)
            p = min(max((t - t_giro) / 0.8, 0.0), 1.0)
            yaw = grados * 0.5 * (1 - math.cos(math.pi * p))
            air.step(DT, S, 1.0, EYE, yaw, -2.0)
            pv = air.push(EYE, yaw, -2.0)
            if t < t_giro - 0.2:
                continue
            m = am.vs(sd, pv, (0.0, 0.0, 0.0))
            Pw = am.to_world_pt(m["P"], EYE, yaw, -2.0)
            vis = m["al"] > 0.1
            if prevW is not None:
                Pw0, vis0, yaw0 = prevW
                ok = vis & vis0
                if ok.any():
                    d0 = Pw0[ok] - EYE; d1 = Pw[ok] - EYE
                    c = np.sum(d0 * d1, 1) / (np.linalg.norm(d0, axis=1) * np.linalg.norm(d1, axis=1))
                    w = np.degrees(np.arccos(np.clip(c, -1, 1))) * FPS
                    wv.append((t - t_giro, np.percentile(w, 50), np.percentile(w, 90), int(ok.sum())))
                    # respecto de la cabeza: direccion en local de la camara
                    l0 = am.to_local_pt(Pw0[ok], EYE, yaw0, -2.0); l1 = m["P"][ok]
                    c2 = np.sum(l0 * l1, 1) / (np.linalg.norm(l0, axis=1) * np.linalg.norm(l1, axis=1))
                    hv.append(np.percentile(np.degrees(np.arccos(np.clip(c2, -1, 1))) * FPS, 50))
            prevW = (Pw, vis, yaw)
        wv = np.array(wv)
        pk = wv[np.argmax(wv[:, 2])]
        mov = wv[(wv[:, 0] > 0) & (wv[:, 0] < 3.0)]
        out.append("giro %3.0f grados en 0,8 s, %s: velocidad de las motas visibles RESPECTO DEL MUNDO: pico p50 %.0f / p90 %.0f grados/s "
                   "(a los %.2f s, %d motas); media de p50 en los 3 s siguientes %.0f grados/s; respecto de la cabeza p50 max %.0f grados/s"
                   % (grados, fase_nombre, wv[:, 1].max(), pk[2], pk[0], pk[3], mov[:, 1].mean(), max(hv)))
txt = "\n".join(out); print(txt)
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "giro_cabeza_resultados.txt"), "w", encoding="utf-8").write(txt + "\n")
