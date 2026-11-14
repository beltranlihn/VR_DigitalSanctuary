# Uso: python flow_exp.py '<json>'  -> flujo optico por bloques (metodo del verificador de confort, b2_flow.bloques).
# Flujo optico por bloques (el metodo del verificador de confort, b2_flow.bloques) sobre cuadros del modelo vexp.
import sys, json, math, time
import numpy as np
sys.path.insert(0, "C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/valle_v2_verif_confort")
import vexp as vm
import b2_flow as bf

W, H, SS = 1052, 862, 4
F = 526.0; CX, CY = 526.0, 431.0
EYE = np.array([0.0, 0.0, 120.0])
NS = 2200
SAMP = np.geomspace(80.0, 64000.0, NS)
uprime = (np.arange(W) + 0.5) - CX
AZREL = np.degrees(np.arctan(uprime / F))
HYP = np.sqrt(F * F + uprime * uprime)
VSUB = (np.arange(H * SS) + 0.5) / SS
TROW = (CY - VSUB)[None, :] / HYP[:, None]

def render(q, yaw, t, sky_cache={}):
    az = np.radians(yaw + AZREL)[:, None]
    X = SAMP[None, :] * np.cos(az); Y = SAMP[None, :] * np.sin(az)
    gx, gy, h, hf = vm.valley_grad(X, Y, t, q)
    col = vm.suelo(X, Y, gx, gy, h, hf, EYE, q)
    key = yaw
    if key not in sky_cache:
        e = np.arctan(TROW)
        dv = np.stack([np.cos(e) * np.cos(az), np.cos(e) * np.sin(az), np.sin(e)], -1)
        sky_cache[key] = vm.cielo(dv.reshape(-1, 3), q, con_luna=True).reshape(W, H * SS, 3)
    skyc = sky_cache[key]
    te = (h - EYE[2]) / SAMP[None, :]
    M = np.maximum.accumulate(te, axis=1)
    img = np.empty((W, H * SS, 3)); idxs = np.empty((W, H * SS), dtype=np.int64)
    for c in range(W):
        idx = np.searchsorted(M[c], TROW[c], side="left"); idxs[c] = idx
        sky = idx >= NS; ii = np.minimum(idx, NS - 1)
        img[c] = np.where(sky[:, None], skyc[c], col[c, ii])
    img = img.reshape(W, H, SS, 3).mean(2).transpose(1, 0, 2)
    dist = np.where(idxs >= NS, np.inf, SAMP[np.minimum(idxs, NS - 1)]).reshape(W, H, SS)[:, :, SS // 2].T
    s = 255.0 * vm.srgb(img)
    return 0.2126 * s[..., 0] + 0.7152 * s[..., 1] + 0.0722 * s[..., 2], dist

over = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
q = vm.params(**over)
rng = np.random.default_rng(11)
T0S = [float(v) for v in rng.uniform(0, 900, 3)]
allb = []
d5s = {}
t00 = time.time()
for yaw in (0.0, 90.0, 180.0, 270.0):
    for t0 in T0S:
        L0, D = render(q, yaw, t0)
        L05, _ = render(q, yaw, t0 + 0.5)
        fl = bf.bloques(L0, L05, 0.5, bf.row_of_el(16.0), bf.row_of_el(-4.8))
        if len(fl):
            dd = D[fl[:, 0].astype(int), fl[:, 1].astype(int)]
            allb.append(np.column_stack([fl, dd]))
A = np.concatenate(allb)
vn = A[:, 4]; dd = A[:, 10] / 100.0
m2 = A[:, 7] >= 0.15
sp2 = np.hypot(A[m2, 2], A[m2, 3])
print("GLOBAL n %d  vn med %.3f p90 %.3f p99 %.3f max %.2f | 2D med %.3f p90 %.3f max %.2f | frac vn>1 %.2f%% >2.5 %.2f%%" % (
    len(A), np.median(vn), np.percentile(vn, 90), np.percentile(vn, 99), vn.max(), np.median(sp2), np.percentile(sp2, 90), sp2.max(), 100*np.mean(vn>1), 100*np.mean(vn>2.5)))
for a, b in ((15, 45), (45, 100), (100, 250), (250, 700)):
    m = (dd >= a) & (dd < b)
    if m.any():
        print("  %3d-%3d m: n %4d vn med %.3f p90 %.3f max %.2f | std bloque med %.2f | >2.5: %.2f%%" % (a, b, m.sum(), np.median(vn[m]), np.percentile(vn[m], 90), vn[m].max(), np.median(A[m, 6]), 100*np.mean(vn[m] > 2.5)))
print("(%.0f s)" % (time.time() - t00))
