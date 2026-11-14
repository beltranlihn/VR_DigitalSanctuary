# v_numerico2.py - segunda pasada: re-mide con instrumento corregido las 5 "fallas" de v_numerico.py
# (C1, D1 y F2 eran de instrumento; B3 y H1 se aislan y se confirman o se descartan).
import math, sys
from pathlib import Path
import numpy as np

AQUI = Path(__file__).resolve().parent
src = (AQUI / "v_numerico.py").read_text(encoding="utf-8")
ns = {"__file__": str(AQUI / "v_numerico.py"), "__name__": "vn"}
exec(compile(src[:src.index("rng = np.random.default_rng")], "vn", "exec"), ns)
vs, fd_grad, mi_h, DEF, S5, WAVES, DUNES = (ns[k] for k in ("vs", "fd_grad", "mi_h", "DEF", "S5", "WAVES", "DUNES"))
vm = ns["vm"]
rng = np.random.default_rng(7)
fallas = []


def chk(lbl, ok, info=""):
    print(("OK    " if ok else "FALLA ") + lbl + ("  " + info if info else ""), flush=True)
    if not ok:
        fallas.append(lbl)


K1 = dict(DEF, HillAmp=3500.0, HillScale=5.0, HillSeed=200.0, HillNear=3000.0, HillFull=7000.0, HillFade=15000.0, HillEnd=21000.0,
          DuneLow=0.1, DuneHigh=0.8, FarBase=4000.0, FarAmp=7000.0, FarScale=13.0, FarSeed=17.0, FarIn=22000.0, FarFull=30000.0,
          FarCrest=40000.0, FarBack=52000.0, SwellAmp=300.0, SwellNear=2500.0, SwellFar=8000.0, SwellScale=3.3, SwellSpeed=1.4,
          SwellSeed=250.0, MorphAmt=0.3, MorphSpeed=1.8)

# ---- C1': la diferencia de C1 escala como 1/e (=> es un SALTO de h, no un error del gradiente). Se explica por el
# cambio de vuelta de frac() de la ola 0 (con SwellSeed 250 su direccion es (0, -1): su linea de cambio de vuelta pasa
# por y = 0 en t = 0) y 6.2831853 != 2 pi: sin(6.2831853 * (1 - eps)) = -7.2e-9, no 0.
x, y, t = 40300.0, 0.0, 0.0
g = vs("ValleyGradVS", x, y, t, K1)
f = lambda a, b, c: vs("ValleyHeightVS", a, b, c, K1)[2]
salto = f(x, 1e-7, t) - f(x, -1e-7, t)
A = K1["SwellAmp"] * x / K1["SwellFar"] * (1 - S5(K1["FarCrest"], K1["FarBack"], x))
print("INFO  C1': salto de h en y = 0 (x = 40300, t = 0, perillas K1): %.3e cm; prediccion A*w0*|sin(6.2831853)|/2.95 = %.3e cm"
      % (salto, A * abs(math.sin(6.2831853)) / 2.95))
# medicion corregida: azimuts que no caen en la linea de cambio de vuelta + escala en e
worst = 0.0; n = 0
for q in (DEF, K1):
    bordes = [q[k] for k in ("SwellNear", "SwellFar", "HillNear", "HillFull", "HillFade", "HillEnd", "FarIn", "FarFull", "FarCrest", "FarBack")]
    for R in bordes:
        for d in (-300.0, -20.0, -1.0, -0.1, 0.1, 1.0, 20.0, 300.0):
            for az in np.linspace(-math.pi, math.pi, 24, endpoint=False) + 0.0137:
                for t in (0.0, 7.3, 123.4, 1799.9, 3599.95):
                    r = R + d
                    xx, yy = r * math.cos(az), r * math.sin(az)
                    g = vs("ValleyGradVS", xx, yy, t, q)
                    fq = lambda a, b, c: vs("ValleyHeightVS", a, b, c, q)[2]
                    e1 = fd_grad(fq, xx, yy, t, e=0.05)
                    err = max(abs(e1[0] - g[0]), abs(e1[1] - g[1]))
                    if err > 1e-7:   # posible cambio de vuelta de frac entre las muestras: repetir con e 10 veces mas chico
                        e2 = fd_grad(fq, xx, yy, t, e=0.005)
                        err2 = max(abs(e2[0] - g[0]), abs(e2[1] - g[1]))
                        if err2 > 5 * err:      # escala 1/e: salto (frac), no error de pendiente
                            err = 0.0
                    worst = max(worst, err); n += 1
chk("C1' gradiente analitico = FD en los bordes de rampa (%d puntos, sin cruzar lineas de cambio de vuelta de frac)" % n, worst < 1e-7, "max %.1e" % worst)

# ---- D1': C2 en los bordes: el salto de d2h/dr2 tiene que ir a 0 LINEALMENTE con e (C2), no quedar constante (C1).
def grad_r(q, R, az, t):
    g = vs("ValleyGradVS", R * math.cos(az), R * math.sin(az), t, q)
    return g[0] * math.cos(az) + g[1] * math.sin(az)


def salto2(fr_, R, e):
    return abs((fr_(R + 2 * e) - fr_(R + e)) / e - (fr_(R - e) - fr_(R - 2 * e)) / e)


peor_ratio = 0.0; peor_abs = 0.0; info = None
for R in [DEF[k] for k in ("SwellNear", "SwellFar", "HillNear", "HillFull", "HillFade", "HillEnd", "FarIn", "FarFull", "FarCrest", "FarBack")]:
    for az in np.linspace(-math.pi, math.pi, 12, endpoint=False) + 0.0137:
        for t in (0.0, 311.1):
            fr_ = lambda rr: grad_r(DEF, rr, az, t)
            s1, s2 = salto2(fr_, R, 2.0), salto2(fr_, R, 0.2)
            ratio = s2 / max(s1, 1e-15)
            if s1 > 1e-10 and ratio > peor_ratio:
                peor_ratio, info = ratio, (R, round(az, 3), t, s1, s2)
            peor_abs = max(peor_abs, s2)
g_ss = lambda rr: 560.0 * 6 * min(max((rr - 1500) / 10500, 0), 1) * (1 - min(max((rr - 1500) / 10500, 0), 1)) / 10500
c1, c2 = salto2(g_ss, 1500.0, 2.0), salto2(g_ss, 1500.0, 0.2)
chk("D1' altura C2 en todos los bordes de rampa: el salto de d2h/dr2 baja ~10x al bajar e 10x (C1 no bajaria)",
    peor_ratio < 0.2 and c2 / c1 > 0.8,
    "peor cociente salto(e=0,2)/salto(e=2) = %.3f en %s; control positivo smoothstep C1: %.3f" % (peor_ratio, info, c2 / c1))

# ---- F2': continuidad temporal en fp32 = la del fp64 (sin saltos por los cambios de vuelta de frac en fp32)
peor = 0.0; wh = None
for T0w in (42.0, 36.0, 31.0 * 30, 46.0 * 80, 53.0 * 20, 67.0 * 7, 83.0 * 3, 3600.0, 7200.0 + 83.0 * 3, 36000.0):
    for _ in range(40):
        r = rng.uniform(1600, 58000); a = rng.uniform(-math.pi, math.pi)
        x32, y32 = np.float32(r * math.cos(a)), np.float32(r * math.sin(a))
        ts = np.float32(T0w) + np.arange(-6, 7, dtype=np.float32) / np.float32(72)
        h32 = np.array([float(vs("ValleyHeightVS", x32, y32, float(tv), dt=np.float32)[2]) for tv in ts])
        h64 = np.array([vs("ValleyHeightVS", float(x32), float(y32), float(tv))[2] for tv in ts])
        e = float(np.abs(np.diff(h32) - np.diff(h64)).max())
        if e > peor:
            peor, wh = e, (round(r), T0w)
chk("F2' fp32 cuadro a cuadro (72 Hz) = fp64 cuadro a cuadro, alrededor de los cambios de vuelta de frac y hasta 10 h",
    peor < 0.05, "max |dh32 - dh64| por cuadro %.4f cm en (r, t) = %s" % (peor, wh))

# ---- B3': que perilla degenerada separa el HLSL del modelo (y de valley_model)
casos = dict(HillFull_lt_HillNear=dict(HillFull=4000.0), HillEnd_lt_HillFade=dict(HillEnd=18000.0),
             FarCrest_lt_FarIn=dict(FarCrest=20000.0), FarBack_lt_FarCrest=dict(FarBack=10.0),
             SwellFar_lt_SwellNear=dict(SwellFar=100.0), DuneHigh_lt_DuneLow=dict(DuneHigh=-0.4),
             HillEnd_gt_FarIn=dict(HillEnd=33000.0), HillFade_lt_HillNear=dict(HillFade=3000.0, HillEnd=9000.0))
for nm, over in casos.items():
    q = dict(DEF, **over)
    e = 0.0; wr = None; evm = 0.0
    for _ in range(600):
        r = 64000 * math.sqrt(rng.uniform()); a = rng.uniform(-math.pi, math.pi); t = rng.uniform(0, 900)
        xx, yy = r * math.cos(a), r * math.sin(a)
        hh = vs("ValleyHeightVS", xx, yy, t, q)[2]
        mh = float(mi_h(xx, yy, t, q)[0])
        vh = float(vm.valley_grad(np.array([xx]), np.array([yy]), t, q)[2][0])
        if abs(hh - vh) > e:
            e, wr = abs(hh - vh), round(r)
        evm = max(evm, abs(vh - mh))
    print("INFO  B3' %-22s |HLSL - valley_model| max %.2e cm (r=%s)   |valley_model - modelo propio| %.1e" % (nm, e, wr, evm))
# el caso HillEnd < HillFade: perfil radial del HLSL y del modelo a lo largo de un azimut
q = dict(DEF, HillEnd=18000.0)
print("INFO  perfil con HillEnd 18000 < HillFade 19000 (az 0.3, t 0): r, h HLSL, h valley_model")
for r in (17000.0, 17900.0, 17999.0, 18001.0, 18500.0, 18999.0, 19001.0, 19500.0):
    xx, yy = r * math.cos(0.3), r * math.sin(0.3)
    print("        %7.0f  %9.2f  %9.2f" % (r, vs("ValleyHeightVS", xx, yy, 0.0, q)[2], float(vm.valley_h(np.array([xx]), np.array([yy]), 0.0, q)[0])))

# ---- H1': velocidad vertical angular con el HLSL y la geometria EXACTA desde los ojos (elevacion = atan2(h - 120, r))
def vel(p, q=DEF):
    r, az, t = p
    xx, yy = r * math.cos(az), r * math.sin(az)
    e1 = math.atan2(vs("ValleyHeightVS", xx, yy, t + 0.002, q)[2] - 120.0, r)
    e0 = math.atan2(vs("ValleyHeightVS", xx, yy, t - 0.002, q)[2] - 120.0, r)
    return math.degrees(abs(e1 - e0) / 0.004)


def vel_model(r, az, t):
    xx, yy = r * np.cos(az), r * np.sin(az)
    h1 = mi_h(xx, yy, t + 0.002)[0]; h0 = mi_h(xx, yy, t - 0.002)[0]
    return np.degrees(np.abs(np.arctan2(h1 - 120, r) - np.arctan2(h0 - 120, r)) / 0.004)


cands = []
for t in rng.uniform(0, 3600, 250):
    r = rng.uniform(1500, 59000, 40000); az = rng.uniform(-math.pi, math.pi, 40000)
    v = vel_model(r, az, t)
    i = np.argsort(v)[-3:]
    cands += [(float(v[k]), float(r[k]), float(az[k]), float(t)) for k in i]
cands.sort(reverse=True)
from scipy.optimize import minimize
best = (0, None)
for v0, r0, a0, t0 in cands[:25]:
    res = minimize(lambda p: -vel(p), [r0, a0, t0], method="Nelder-Mead", options=dict(xatol=1e-4, fatol=1e-9, maxiter=4000))
    if 1500 <= res.x[0] <= 59000 and -res.fun > best[0]:
        best = (-res.fun, tuple(res.x))
vbest, (rb, ab, tb) = best
# a que radio pertenece y cuanto aporta cada capa
xx, yy = rb * math.cos(ab), rb * math.sin(ab)
dparts = {}
for capas, nm in (((1,), "colinas medias (respiracion)"), ((2,), "lejos"), ((3,), "oleaje")):
    d = (vm.valley_grad(np.array([xx]), np.array([yy]), tb + 0.002, capas=capas)[2][0]
         - vm.valley_grad(np.array([xx]), np.array([yy]), tb - 0.002, capas=capas)[2][0]) / 0.004
    dparts[nm] = math.degrees(d / rb)
chk("H1' velocidad vertical angular maxima (10 millones de muestras + Nelder-Mead sobre el HLSL, geometria exacta) <= 0,5 grados/s",
    vbest <= 0.5, "max %.4f grados/s en r = %.0f cm, az = %.3f, t = %.2f s; aporte por capa (grados/s): %s"
    % (vbest, rb, ab, tb, ", ".join("%s %.3f" % kv for kv in dparts.items())))
# con MorphAmt 0 (la palanca de la spec) y con SwellAmp 540
for nm, q in (("MorphAmt 0", dict(DEF, MorphAmt=0.0)), ("SwellAmp 540", dict(DEF, SwellAmp=540.0))):
    b2 = 0.0
    for v0, r0, a0, t0 in cands[:15]:
        res = minimize(lambda p: -vel(p, q), [r0, a0, t0], method="Nelder-Mead", options=dict(xatol=1e-4, fatol=1e-9, maxiter=3000))
        if 1500 <= res.x[0] <= 59000:
            b2 = max(b2, -res.fun)
    print("INFO  H1' con %s: max local %.4f grados/s (mismos arranques)" % (nm, b2))
print("\nRESULTADO segunda pasada: " + ("TODO OK" if not fallas else "FALLAS: %s" % fallas))
