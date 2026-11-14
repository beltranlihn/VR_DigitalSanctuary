# -*- coding: utf-8 -*-
"""Revisor: prueba de un arreglo barato para el gate del aliento (en disco, NO toca el repo).
 A) histeresis: entra a inhalar/exhalar con |v| > GateOn (0,10) y sigue mientras |v| > GateOff (0,04)
 B) onset de exhalacion solo si hubo una inhalacion de >= 0,6 s desde el ultimo onset (latch) -> RateBpm correcto
Compara contra el BP del plan con las mismas senales (ideal / ruido / deriva)."""
import math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim_ruido_pausas as s
import breath_air_model as am

class AirHist(am.AirBP):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.mode = 0; self.inh_t = 0.0; self.latch = False
    def step(self, dt, S, on, eye, yaw, pitch, mounted=True):
        on_g, off_g = 0.10, 0.04
        v = (S - self.Sprev) / max(dt, 1e-4) if self.bPrimed else 0.0
        # decidir el modo con histeresis y reinyectar como v "limpia" para reusar el paso del plan
        if self.mode == 1 and v < off_g: self.mode = 0
        if self.mode == -1 and v > -off_g: self.mode = 0
        if self.mode == 0:
            if v > on_g: self.mode = 1
            elif v < -on_g: self.mode = -1
        self.inh_t = self.inh_t + dt if self.mode == 1 else 0.0
        if self.inh_t > 0.6: self.latch = True
        g = self.q["VelGate"]
        # truco: el paso original decide inh/exh con VelGate; forzamos su decision con un VelGate efectivo
        self.q["VelGate"] = 1e9 if self.mode == 0 else (abs(v) * 0.5 if abs(v) > 0 else 1e-9)
        was = self.bWasExh; last = self.LastOnset; rate = self.RateBpm
        vv = super().step(dt, S, on, eye, yaw, pitch, mounted)
        self.q["VelGate"] = g
        # onset con latch: deshacer el conteo si no hubo inhalacion desde el ultimo
        if self.mode == -1 and not was:
            if not self.latch:
                self.LastOnset, self.RateBpm = last, rate
            else:
                self.latch = False
        return vv

def run(sig, dr, cls, seed=1, pacer=(4.0, 3.0, 4.0, 3.0), ciclos=8):
    orig = am.AirBP
    am.AirBP = cls
    try:
        return s.run(sig, dr, pacer=pacer, ciclos=ciclos, seed=seed)
    finally:
        am.AirBP = orig

lines = ["caso                        | BP del plan: movil% Eout_max resp/min | histeresis+latch: movil% Eout_max resp/min Ein>0,5 (s)"]
for nombre, sg, dr in (("ideal", 0, 0), ("ruido 0,03 + deriva 0,2", 0.03, 0.2), ("ruido 0,04 + deriva 0,2", 0.04, 0.2),
                       ("ruido 0,06 + deriva 0,15", 0.06, 0.15), ("ruido 0,08 + deriva 0,2", 0.08, 0.2)):
    res = []
    for cls in (am.AirBP, AirHist):
        mv, eo, rt, lat = [], [], [], []
        for sd in (1, 2, 3):
            rec, T = run(sg, dr, cls, seed=sd)
            m = s.metricas(rec, T)
            mv.append(m["movil"].mean()); eo.append(m["eout_max"].mean()); rt.append(rec["rate"][-1])
            t = rec["t"]
            for c in range(2, 7):
                t0 = c * T + 0.4
                k = (t >= t0) & (rec["Ein"] > 0.5)
                if k.any(): lat.append(t[k][0] - t0)
        res.append((100 * np.mean(mv), np.mean(eo), np.mean(rt), np.mean(lat)))
    lines.append("%-27s | %6.1f %8.2f %8.1f | %6.1f %8.2f %8.1f %6.2f" % (nombre, res[0][0], res[0][1], res[0][2], res[1][0], res[1][1], res[1][2], res[1][3]))
lines.append("(Ein>0,5 del BP del plan en ideal: ver sim_ruido_pausas_resultados.txt, 0,41 s)")
txt = "\n".join(lines); print(txt)
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "arreglo_histeresis_resultados.txt"), "w", encoding="utf-8").write(txt + "\n")
