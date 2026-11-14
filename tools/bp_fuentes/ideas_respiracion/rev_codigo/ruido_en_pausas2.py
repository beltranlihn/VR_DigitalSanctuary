# Revisor: quietud en la SEGUNDA mitad de cada pausa (cuando el seguidor ya llego) con ruido del sensor.
import sys, math, random
sys.path.insert(0, r"C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/.claude/skills/unreal-vr/scripts")
import numpy as np
import breath_air_model as m
def corre(sigma, tau_n=0.2, dur=84.0, seed=3):
    random.seed(seed); dt = 1.0/72.0
    rig = m.RigFollower(s0=-1.0); bp = m.AirBP(np.zeros(3), 0.0, 0.0)
    nz = 0.0; a = 1.0 - math.exp(-dt / tau_n); t = 0.0
    fr = n = 0; emax = []; tin0=None; dtin=[]
    while t < dur:
        tgt, fase = m.belly_target(t)
        nz += (random.gauss(0.0, sigma * math.sqrt(2 * tau_n / dt)) - nz) * a
        S = rig.step(max(-1.0, min(1.0, tgt + nz)), dt)
        v = bp.step(dt, S, 1.0, np.zeros(3), 0.0, 0.0)
        tt = (t - 0.4) % 14.0
        # segunda mitad de las pausas: 5,5-7 s (tras inhalar) y 12,5-14 s (tras exhalar)
        if t > 14 and ((5.5 < tt < 7.0) or (12.5 < tt < 14.0)):
            n += 1
            if abs(v) > bp.q["VelGate"]: fr += 1
            emax.append(max(bp.Ein, bp.Eout) if False else (bp.Ein if tt < 7 else bp.Eout))
        t += dt
    return "sigma %.3f: cuadros con flujo en la 2a mitad de las pausas %d/%d (%.0f %%), RateBpm final %.1f (real 4,3)" % (sigma, fr, n, 100.0*fr/n, bp.RateBpm)
for s in (0.0, 0.005, 0.01, 0.02):
    print(corre(s))
