# Revisor: el modelo del aliento con RUIDO del sensor en las pausas (el plan solo lo probo con pausas planas).
import sys, math, random
sys.path.insert(0, r"C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/.claude/skills/unreal-vr/scripts")
import numpy as np
import breath_air_model as m

def corre(sigma, tau_n=0.2, dur=70.0, seed=1):
    random.seed(seed)
    dt = 1.0 / 72.0
    rig = m.RigFollower(s0=-1.0)
    bp = m.AirBP(np.zeros(3), 0.0, 0.0)
    nz = 0.0
    a = 1.0 - math.exp(-dt / tau_n)
    t = 0.0
    ein_hold, eout_hold, onsets, flips = [], [], 0, 0
    prev_exh = False
    fases = []
    while t < dur:
        tgt, fase = m.belly_target(t)
        nz += (random.gauss(0.0, sigma * math.sqrt(2 * tau_n / dt)) - nz) * a  # ruido 1er orden, std ~ sigma
        S = rig.step(max(-1.0, min(1.0, tgt + nz)), dt)
        v = bp.step(dt, S, 1.0, np.zeros(3), 0.0, 0.0)
        exh = v < -bp.q["VelGate"]
        inh = v > bp.q["VelGate"]
        if t > 14.0 and fase in (1, 3):
            # pausa: medir cuanto se encienden las corrientes CONTRARIAS/nuevas (en la pausa todo deberia apagarse)
            ein_hold.append(bp.Ein if fase == 1 else bp.Ein)
            eout_hold.append(bp.Eout if fase == 3 else bp.Eout)
            if (inh or exh):
                flips += 1
        if exh and not prev_exh:
            onsets += 1
        prev_exh = exh
        t += dt
    return dict(sigma=sigma, frames_con_flujo_en_pausa=flips, onsets_exh=onsets, RateBpm=round(bp.RateBpm, 2),
                Ein_p99_pausa=round(float(np.percentile(ein_hold, 99)), 3), Eout_p99_pausa=round(float(np.percentile(eout_hold, 99)), 3))

ciclos = 70.0 / 14.0
print("ciclos reales ~%.1f (4-3-4-3, 4,3 resp/min)" % ciclos)
for s in (0.0, 0.003, 0.01, 0.02, 0.04):
    print(corre(s))
