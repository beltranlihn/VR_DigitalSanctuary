# Uso: python profile.py '<json>' ...  -> perfil medio de luminancia del llano (sesgo del sombreado del oleaje).
import sys, json, numpy as np, vexp as vm
eye = np.array([0.0, 0.0, 120.0])
def luma(c):
    L = 255 * vm.srgb(c); return 0.2126 * L[..., 0] + 0.7152 * L[..., 1] + 0.0722 * L[..., 2]
d = np.geomspace(1500, 30000, 120)
az = np.radians(np.arange(0, 360, 1.0))
X = d[:, None] * np.cos(az)[None, :]; Y = d[:, None] * np.sin(az)[None, :]
el = np.degrees(np.arctan2(-120.0, d))
base = None
for arg in sys.argv[1:]:
    q = vm.params(**json.loads(arg))
    Ls = []; ch = []
    for t in np.linspace(0, 400, 9):
        gx, gy, h, hf = vm.valley_grad(X, Y, t, q, capas=(3,))   # solo el llano: sin colinas (aislar el efecto)
        L = luma(vm.suelo(X, Y, gx, gy, h, hf, eye, q)); Ls.append(L)
        gx5, gy5, h5, hf5 = vm.valley_grad(X, Y, t + 5, q, capas=(3,))
        ch.append(np.abs(luma(vm.suelo(X, Y, gx5, gy5, h5, hf5, eye, q)) - L))
    Ls = np.array(Ls); ch = np.array(ch)
    prof = Ls.mean((0, 2)); std = Ls.std(2).mean(0); c5 = np.median(ch, axis=(0, 2)); c5p = np.percentile(ch, 90, axis=(0, 2))
    if base is None:
        base = prof
    dprof = prof - base
    # no monotonia: el perfil (con la elevacion creciente = d creciente) deberia crecer; caida maxima
    dif = np.diff(prof)
    drop = 0.0; run = 0.0
    for v in dif:
        run = min(0.0, run + v); drop = min(drop, run)
    print(arg)
    for dd in (15, 20, 25, 30, 40, 50, 60, 80, 100, 150, 200, 300):
        i = int(np.argmin(np.abs(d - dd * 100)))
        print("   %3d m (el %.2f): media %.1f (sesgo %+.2f) std az %.2f | cambio 5 s med %.2f p90 %.2f" % (dd, el[i], prof[i], dprof[i], std[i], c5[i], c5p[i]))
    print("   caida maxima del perfil medio al alejarse (banda oscura si < 0): %.2f niveles" % drop)
