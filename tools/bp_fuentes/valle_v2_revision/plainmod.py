import sys, json, numpy as np, vexp as vm
over = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
q = vm.params(**over)
az = np.radians(np.arange(-180, 180, 0.5))
eye = np.array([0.0, 0.0, 120.0])
def luma(c):
    L = 255 * vm.srgb(c); return 0.2126 * L[..., 0] + 0.7152 * L[..., 1] + 0.0722 * L[..., 2]
for d in (2000, 3000, 4500, 6000, 9000, 14000, 20000):
    x = d * np.cos(az); y = d * np.sin(az)
    res = []
    for t in (0.0, 5.0):
        gx, gy, h, hf = vm.valley_grad(x, y, t, q)
        res.append(luma(vm.suelo(x, y, gx, gy, h, hf, eye, q)))
    L0, L5 = res
    print("d %5.0f m: luma media %.1f, std en azimut %.2f, rango %.1f | cambio en 5 s: mediana %.2f p90 %.2f niv" % (d/100, L0.mean(), L0.std(), np.ptp(L0), np.median(np.abs(L5-L0)), np.percentile(np.abs(L5-L0), 90)))
