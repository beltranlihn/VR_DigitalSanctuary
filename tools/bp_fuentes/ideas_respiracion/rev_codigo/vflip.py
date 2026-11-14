# Revisor: efecto de la V invertida del importador FBX de Unreal (gotcha 302) sobre las semillas de SM_BreathAir_SC.
import sys
sys.path.insert(0, r"C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/.claude/skills/unreal-vr/scripts")
import numpy as np
import breath_air_model as m
sd = m.seeds()
fl = dict(sd); fl["u"] = 1.0 - sd["u"]; fl["b"] = 1.0 - sd["b"]; fl["flag"] = 1.0 - sd["flag"]
print("n inhalar/exhalar: disenio %d/%d  -> en Unreal %d/%d" % ((sd["flag"] < .5).sum(), (sd["flag"] > .5).sum(), (fl["flag"] < .5).sum(), (fl["flag"] > .5).sum()))
print("b: disenio [%.2f, %.2f] media %.2f -> en Unreal [%.2f, %.2f] media %.2f" % (sd["b"].min(), sd["b"].max(), sd["b"].mean(), fl["b"].min(), fl["b"].max(), fl["b"].mean()))
eyes = [np.array([0.0, -3.2, 0.0]), np.array([0.0, 3.2, 0.0])]
for pb in (0.8, -0.8):
    for T in (0.1, 0.35, 0.6, 0.85):
        pv = m.preview_push({"PreviewBreath": pb, "PreviewAirT": T})
        for nom, s in (("disenio", sd), ("Unreal ", fl)):
            r = m.vs(s, pv, camL=eyes[0])
            al = np.asarray(r["al"]); P = np.asarray(r["P"])
            vis = al > 0.02
            D = P - eyes[0]; el = np.degrees(np.arcsin(D[:, 2] / np.linalg.norm(D, axis=1)))
            if T == 0.35:
                print("  %s PreviewBreath %+.1f T %.2f: motas visibles %4d  alfa total %6.1f  centro Z medio %+6.1f cm  Y medio %+5.1f cm  elev media %+5.1f" % (
                    nom, pb, T, vis.sum(), al.sum(), P[vis, 2].mean() if vis.any() else np.nan, P[vis, 1].mean() if vis.any() else np.nan, el[vis].mean() if vis.any() else np.nan))
