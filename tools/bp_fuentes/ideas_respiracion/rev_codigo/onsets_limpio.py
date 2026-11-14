import sys, math
sys.path.insert(0, r"C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/.claude/skills/unreal-vr/scripts")
import numpy as np
import breath_air_model as m
dt = 1.0/72.0
rig = m.RigFollower(s0=-1.0); bp = m.AirBP(np.zeros(3), 0.0, 0.0)
t = 0.0; prev = False; last=None
while t < 45.0:
    tgt, fase = m.belly_target(t)
    S = rig.step(tgt, dt)
    ro = bp.RateBpm
    v = bp.step(dt, S, 1.0, np.zeros(3), 0.0, 0.0)
    exh = v < -bp.q["VelGate"]
    if exh != prev:
        print("t=%6.2f fase=%d %s v=%+.3f S=%+.3f tgt=%+.3f RateBpm %.2f->%.2f" % (t, fase, "EXH ON " if exh else "exh off", v, S, tgt, ro, bp.RateBpm))
    prev = exh
    t += dt
