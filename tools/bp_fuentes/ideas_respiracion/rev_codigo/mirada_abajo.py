# Revisor: cuanto aire queda visible si el usuario mira hacia abajo (al sensor) de forma sostenida.
import sys
sys.path.insert(0, r"C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/.claude/skills/unreal-vr/scripts")
import numpy as np
import breath_air_model as m
sd = m.seeds()
eye = np.zeros(3)
for pitch in (0.0, -10.0, -20.0, -35.0):
    for pb in (0.8, -0.8):
        tot = 0.0; vis = 0
        for T in np.linspace(0.02, 0.98, 12):
            bp = m.AirBP(eye, 0.0, pitch)
            bp.Tin = bp.Tout = T; bp.Fout = 1.5; bp.Ein = max(pb, 0); bp.Eout = max(-pb, 0); bp.Glob = 1.0
            bp.YawLag, bp.PitchLag = 0.0, pitch   # marco ya asentado (PitchFollow lo multiplica en push)
            pv = bp.push(eye, 0.0, pitch)
            r = m.vs(sd, pv, camL=np.array([0.0, -3.2, 0.0]))
            al = np.asarray(r["al"]); tot += al.sum(); vis += (al > 0.02).sum()
        print("pitch %+5.0f  %s: alfa total medio %6.1f   motas visibles medio %5.0f" % (pitch, "inhala" if pb > 0 else "exhala", tot / 12, vis / 12))
