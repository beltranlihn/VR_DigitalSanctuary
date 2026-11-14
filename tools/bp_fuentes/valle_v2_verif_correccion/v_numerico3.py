# v_numerico3.py - tercera pasada: F2' separado por duracion de sesion, H1' con palancas, y el PS (color) con el traductor propio.
import math
from pathlib import Path
import numpy as np
AQUI = Path(__file__).resolve().parent
src = (AQUI / "v_numerico.py").read_text(encoding="utf-8")
ns = {"__file__": str(AQUI / "v_numerico.py"), "__name__": "vn"}
exec(compile(src[:src.index("rng = np.random.default_rng")], "vn", "exec"), ns)
vs, mi_h, DEF, TR, Vec, NS, vm = (ns[k] for k in ("vs", "mi_h", "DEF", "TR", "Vec", "NS", "vm"))
rng = np.random.default_rng(11)

# F2'' : fp32 vs fp64 cuadro a cuadro, por duracion de sesion
for T0s in ((42.0, 36.0, 31.0 * 30, 46.0 * 80, 53.0 * 20, 67.0 * 7, 83.0 * 3, 900.0), (3600.0, 7200.0 + 83.0 * 3), (36000.0,)):
    peor = 0.0
    for T0w in T0s:
        for _ in range(40):
            r = rng.uniform(1600, 58000); a = rng.uniform(-math.pi, math.pi)
            x32, y32 = np.float32(r * math.cos(a)), np.float32(r * math.sin(a))
            ts = np.float32(T0w) + np.arange(-6, 7, dtype=np.float32) / np.float32(72)
            h32 = np.array([float(vs("ValleyHeightVS", x32, y32, float(tv), dt=np.float32)[2]) for tv in ts])
            h64 = np.array([vs("ValleyHeightVS", float(x32), float(y32), float(tv)) [2] for tv in ts])
            peor = max(peor, float(np.abs(np.diff(h32) - np.diff(h64)).max()))
    print("F2''  t en %s s: max |dh32 - dh64| por cuadro = %.4f cm" % (T0s, peor))

# PS con el traductor propio: seccion 12 (suelo y cielo) y contra valley_model en puntos al azar
F, ins = TR[("ValleyPS", np.float64)]
def D(az, el): return Vec(vm.dir_d(az, el), np.float64)
def psq(q, **k):
    kw = {}
    for n in ins:
        if n in k: kw[n] = k[n]
        elif n == "LightDir": kw[n] = D(q["LightAz"], q["LightEl"])
        elif n == "GlowDir": kw[n] = D(q["GlowAz"], q["GlowEl"])
        elif n == "MoonDir": kw[n] = D(q["MoonAz"], q["MoonEl"])
        elif n == "MoonCosR": kw[n] = math.cos(math.radians(q["MoonRadius"]))
        else:
            v = q[n]
            kw[n] = Vec(list(v), np.float64) if isinstance(v, tuple) else float(v)
    return F(NS(SvPosition=Vec([10.5, 20.5, 0.5, 1.0], np.float64)), NS(GameTime=0.0), **kw).a
q0 = dict(DEF, DitherAmt=0.0)
CAM = np.array([0.0, 0.0, 120.0])
def suelo(x, y, t, q=q0, cam=CAM):
    g = vs("ValleyGradVS", x, y, t, q)
    d = cam - np.array([x, y, g[2]])
    return psq(q, VI1=Vec(g, np.float64), LPi=Vec([x, y, 0.0], np.float64), CamL=Vec(d, np.float64), Dist=float(np.linalg.norm(d)), Part=0.0)
tab = [((380, 0), 0, (0.2157, 0.2651, 0.5575)), ((250, -150), 0, (0.2698, 0.3420, 0.6275)), ((3000, 1200), 0, (0.4369, 0.4620, 0.7102)),
       ((-9000, 6000), 45.5, (0.4019, 0.4632, 0.7341)), ((15000, 5000), 90, (0.4973, 0.4844, 0.7141)), ((46000, 9000), 600, (0.6118, 0.5615, 0.7760))]
e = max(float(np.abs(suelo(x, y, t) - np.array(c)).max()) for (x, y), t, c in tab)
cie = [((0, 0), (0.7595, 0.6629, 0.8501)), ((0, 45), (0.2160, 0.3280, 0.5970)), ((20, 3), (0.7821, 0.6676, 0.8510)), ((180, 10), (0.5383, 0.5784, 0.8017)),
       ((-40, 7), (0.6269, 0.6178, 0.8274)), ((-33, 12), (0.6578, 0.6158, 0.8209)), ((0, 90), (0.2160, 0.3280, 0.5970))]
ec = max(float(np.abs(psq(q0, VI1=Vec([0, 0, 0, 0], np.float64), LPi=Vec([0, 0, 0], np.float64), CamL=-D(az, el), Dist=1e5, Part=1.0) - np.array(c)).max()) for (az, el), c in cie)
print("%s PS seccion 12 (traductor propio): suelo max %.1e, cielo max %.1e (tolerancia 1e-3)" % ("OK   " if max(e, ec) <= 1e-3 else "FALLA", e, ec))
em = 0.0
for _ in range(1500):
    r = 64000 * rng.uniform() ** 2; a = rng.uniform(-math.pi, math.pi); t = rng.uniform(0, 1800)
    x, y = r * math.cos(a), r * math.sin(a)
    cam = np.array([rng.uniform(-30, 30), rng.uniform(-30, 30), rng.uniform(90, 230)])
    c = suelo(x, y, t, cam=cam)
    gx, gy, h, hf = vm.valley_grad(np.array([x]), np.array([y]), t, q0)
    cm = vm.suelo(np.array([x]), np.array([y]), gx, gy, h, hf, cam, q0)[0]
    em = max(em, float(np.abs(c - cm).max()))
print("%s PS suelo (traductor propio) = valley_model.suelo, 1500 puntos, camara movida +-30 cm y a 90-230 cm de alto: max %.1e" % ("OK   " if em < 1e-6 else "FALLA", em))

# H1'' : que palanca deja el maximo <= 0,5 grados/s (busqueda con muchos arranques)
from scipy.optimize import minimize
def vel(p, q):
    r, az, t = p
    xx, yy = r * math.cos(az), r * math.sin(az)
    e1 = math.atan2(float(mi_h(xx, yy, t + 0.002, q)[0]) - 120.0, r)
    e0 = math.atan2(float(mi_h(xx, yy, t - 0.002, q)[0]) - 120.0, r)
    return math.degrees(abs(e1 - e0) / 0.004)
def vmaxq(q, nt=120):
    c = []
    for t in rng.uniform(0, 3600, nt):
        r = rng.uniform(1500, 59000, 40000); az = rng.uniform(-math.pi, math.pi, 40000)
        xx, yy = r * np.cos(az), r * np.sin(az)
        v = np.degrees(np.abs(np.arctan2(mi_h(xx, yy, t + 0.002, q)[0] - 120, r) - np.arctan2(mi_h(xx, yy, t - 0.002, q)[0] - 120, r)) / 0.004)
        i = np.argsort(v)[-2:]
        c += [(float(v[k]), float(r[k]), float(az[k]), float(t)) for k in i]
    c.sort(reverse=True)
    b = c[0][0]
    for v0, r0, a0, t0 in c[:12]:
        res = minimize(lambda p: -vel(p, q), [r0, a0, t0], method="Nelder-Mead", options=dict(xatol=1e-4, fatol=1e-9, maxiter=3000))
        if 1500 <= res.x[0] <= 59000: b = max(b, -res.fun)
    return b
for nm, over in (("defaults", {}), ("MorphAmt 0.10", dict(MorphAmt=0.10)), ("MorphAmt 0.05", dict(MorphAmt=0.05)),
                 ("SwellAmp 520", dict(SwellAmp=520.0)), ("SwellAmp 500", dict(SwellAmp=500.0))):
    print("H1''  %-14s max vel. vertical angular = %.4f grados/s" % (nm, vmaxq(dict(DEF, **over))))
