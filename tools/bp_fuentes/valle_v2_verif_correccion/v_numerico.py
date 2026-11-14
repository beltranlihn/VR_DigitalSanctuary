# v_numerico.py - verificador independiente del valle v2 (lente: correccion tecnica). SIN Unreal.
# 1. Traduce los .hlsl a Python con un traductor PROPIO (no el de Valley_check.py), en fp64 y en fp32 emulado.
# 2. Escribe un modelo PROPIO de la altura a partir del TEXTO de la spec (seccion 3), sin mirar valley_model.py.
# 3. Compara: HLSL vs seccion 12, HLSL vs modelo propio vs valley_model.py, gradiente analitico vs diferencias
#    finitas (en las transiciones de cada rampa y en varios t), continuidad C2 en los bordes de rampa, piso = 0
#    exacto y quieto, fp32 vs fp64 y continuidad temporal en fp32, cotas de h para los bounds.
# Todo se escribe en esta carpeta; el repo no se toca.
import math, re, sys, time
from pathlib import Path

import numpy as np

np._set_promotion_state("weak")   # los literales de Python no suben un float32 a float64 (emulacion fp32)

AQUI = Path(__file__).resolve().parent
REPO = AQUI.parents[3]
HL = REPO / ".claude" / "skills" / "unreal-vr" / "scripts" / "hlsl"
sys.path.insert(0, str(HL.parent))
import valley_model as vm  # solo para compararlo, no para derivar nada

fallas = []


def chk(lbl, ok, info=""):
    print(("OK    " if ok else "FALLA ") + lbl + ("  " + info if info else ""), flush=True)
    if not ok:
        fallas.append(lbl)


# =============================== traductor propio HLSL -> Python ===============================
class Vec:
    SW = {"x": 0, "y": 1, "z": 2, "w": 3, "r": 0, "g": 1, "b": 2, "a": 3}

    def __init__(self, a, dt):
        self.dt = dt
        self.a = np.array(a, dtype=dt)

    def __getattr__(self, n):
        if n.startswith("_") or n in ("a", "dt"):
            raise AttributeError(n)
        if all(c in Vec.SW for c in n):
            v = self.a[[Vec.SW[c] for c in n]]
            return v[0] if len(n) == 1 else Vec(v, self.dt)
        raise AttributeError(n)

    def _v(self, o):
        return o.a if isinstance(o, Vec) else o

    def __add__(s, o): return Vec(s.a + s._v(o), s.dt)
    def __radd__(s, o): return Vec(s._v(o) + s.a, s.dt)
    def __sub__(s, o): return Vec(s.a - s._v(o), s.dt)
    def __rsub__(s, o): return Vec(s._v(o) - s.a, s.dt)
    def __mul__(s, o): return Vec(s.a * s._v(o), s.dt)
    def __rmul__(s, o): return Vec(s._v(o) * s.a, s.dt)
    def __truediv__(s, o): return Vec(s.a / s._v(o), s.dt)
    def __neg__(s): return Vec(-s.a, s.dt)


def make_env(dt):
    def U(x): return x.a if isinstance(x, Vec) else x
    def W(x): return Vec(x, dt) if isinstance(x, np.ndarray) and x.ndim > 0 else dt(x)
    def f1(fn): return lambda x: W(fn(U(x)))
    def ctor(*args):
        out = []
        for a in args:
            out.extend(list(a.a) if isinstance(a, Vec) else [a])
        return Vec(out, dt)
    def ss(a, b, x):
        t = np.clip((U(x) - a) / (b - a), dt(0), dt(1))
        return W(t * t * (3 - 2 * t))
    return dict(float2=ctor, float3=ctor, float4=ctor,
                sqrt=f1(np.sqrt), sin=f1(np.sin), cos=f1(np.cos), exp=f1(np.exp), floor=f1(np.floor), abs=f1(np.abs),
                radians=f1(lambda v: v * dt(math.pi / 180.0)), frac=f1(lambda v: v - np.floor(v)),
                rsqrt=f1(lambda v: dt(1) / np.sqrt(v)), saturate=f1(lambda v: np.clip(v, dt(0), dt(1))),
                pow=lambda a, b: W(np.power(U(a), U(b))), max=lambda a, b: W(np.maximum(U(a), U(b))),
                min=lambda a, b: W(np.minimum(U(a), U(b))), smoothstep=ss,
                lerp=lambda a, b, t: W(U(a) + (U(b) - U(a)) * U(t)),
                dot=lambda a, b: dt(np.dot(a.a, b.a)), normalize=lambda a: Vec(a.a / np.sqrt(np.dot(a.a, a.a)), dt))


def traducir(name):
    txt = (HL / (name + ".hlsl")).read_text(encoding="ascii")
    ins = [n for n, _ in re.findall(r"^//\s+\d+\s+(\w+)\s+(float[234]?)\s", txt, re.M)]
    lines = [l.split("//")[0].strip() for l in txt.split("\n")]
    lines = [l for l in lines if l]
    py, ind, abre = [], 1, False
    bop = lambda e: e.replace("||", " or ").replace("&&", " and ")
    for l in lines:
        P = "    " * ind
        m = None
        if l == "{":
            assert abre, name
            abre = False
            ind += 1
            continue
        if l == "}":
            ind -= 1
            continue
        if (m := re.fullmatch(r"if \((.+)\) \{ return (.+); \}", l)):
            py += [P + "if %s:" % bop(m[1]), P + "    return %s" % m[2]]
        elif (m := re.fullmatch(r"if \((.+)\)", l)):
            py.append(P + "if %s:" % bop(m[1]))
            abre = True
        elif (m := re.fullmatch(r"return (.+);", l)):
            py.append(P + "return %s" % m[1])
        elif (m := re.fullmatch(r"sincos\((.+), (\w+), (\w+)\);", l)):
            py.append(P + "_a = %s; %s = sin(_a); %s = cos(_a)" % (m[1], m[2], m[3]))
        elif re.fullmatch(r"float[234]? \w+(, \w+)+;", l):
            continue
        elif (m := re.fullmatch(r"float[234]? (\w+) = (.+);", l)):
            py.append(P + "%s = %s" % (m[1], bop(m[2])))
        elif (m := re.fullmatch(r"(\w+) (\+=|-=|\*=|/=|=) (.+);", l)):
            py.append(P + "%s %s %s" % (m[1], m[2], bop(m[3])))
        else:
            raise SyntaxError(name + ": " + l)
    assert ind == 1
    src = "def F(Parameters, View, %s):\n%s\n" % (", ".join(ins), "\n".join(py))
    return src, ins


class NS:
    def __init__(self, **k): self.__dict__.update(k)


def compilar(name, dt):
    src, ins = traducir(name)
    env = make_env(dt)
    exec(compile(src, name, "exec"), env)
    return env["F"], ins


TR = {}
for dt in (np.float64, np.float32):
    for n in ("ValleyHeightVS", "ValleyGradVS", "ValleyPS"):
        TR[(n, dt)] = compilar(n, dt)

DEF = dict(vm.P)  # defaults de la tabla 7.1 (verificado aparte que coinciden con valley_build.json)


def vs(name, x, y, t, q=None, dt=np.float64):
    q = DEF if q is None else q
    F, ins = TR[(name, dt)]
    kw = {n: dt(q[n]) for n in ins if n != "LP"}
    out = F(NS(), NS(GameTime=dt(t)), LP=Vec([x, y, 0.0], dt), **kw)
    return out.a


# =============================== modelo PROPIO desde el texto de la spec (seccion 3) ===============================
DUNES = [(18, 3000, 1.00, 0.0, 53, 0.0), (101, 2200, 0.75, 1.7, 67, 2.1), (143, 1650, 0.55, 4.1, 41, 4.4), (232, 1250, 0.35, 2.9, 83, 1.3)]
WAVES = [(20, 9000, 42, 1.00, 0.00), (175, 7000, 36, 0.85, 0.37), (255, 5500, 31, 0.70, 0.73), (95, 4000, 46, 0.40, 0.18)]


def S5(a, b, x):
    b = max(b, a + 1e-9)
    t = np.clip((np.asarray(x, float) - a) / (b - a), 0, 1)
    return t ** 3 * (t * (6 * t - 15) + 10)


def fr(v): return v - np.floor(v)


def sigma(x, y, t, scale, seed, q):
    s = 0.0
    for al, lam, a, phi, T, psi in DUNES:
        k = 2 * math.pi / (lam * scale)
        ang = math.radians(al + seed)
        m = math.sin(2 * math.pi * fr(q["MorphSpeed"] * t / T) + psi)
        s = s + a * (1 + q["MorphAmt"] * m) * np.sin(k * (math.cos(ang) * x + math.sin(ang) * y) + phi)
    return s / 2.65


def oleaje(x, y, t, q):
    s = 0.0
    for al, lam, T, w, c in WAVES:
        ang = math.radians(al + q["SwellSeed"])
        g = 2 * math.pi * fr((math.cos(ang) * x + math.sin(ang) * y) / (lam * q["SwellScale"]) + c - fr(q["SwellSpeed"] * t / T))
        s = s + w * np.sin(g)
    return s / 2.95


def mi_h(x, y, t, q=None, partes=False):
    q = DEF if q is None else q
    x = np.asarray(x, float); y = np.asarray(y, float)
    r = np.hypot(x, y)
    envH = S5(q["HillNear"], q["HillFull"], r) * (1 - S5(q["HillFade"], q["HillEnd"], r))
    fH = S5(q["DuneLow"], max(q["DuneHigh"], q["DuneLow"] + 0.01), sigma(x, y, t, q["HillScale"], q["HillSeed"], q))
    h1 = q["HillAmp"] * envH * fH
    FC = max(q["FarCrest"], q["FarIn"] + 1); FB = max(q["FarBack"], FC + 1)
    ring = S5(q["FarIn"], FC, r)
    envF = S5(q["FarIn"], q["FarFull"], r)
    fF = S5(-0.7, 1.2, sigma(x, y, t, q["FarScale"], q["FarSeed"], q))
    h2 = q["FarBase"] * ring + q["FarAmp"] * envF * fF
    SF = max(q["SwellFar"], q["SwellNear"] + 1)
    A = q["SwellAmp"] * S5(q["SwellNear"], SF, r) * r / SF
    h3 = A * oleaje(x, y, t, q)
    back = 1 - S5(FC, FB, r)
    h = back * (h1 + h2 + h3)
    hf = np.clip(back * (envH * fH + envF * fF), 0, 1)
    if partes:
        return h, hf, dict(h1=h1, h2=h2, h3=h3, back=back, A=A)
    return h, hf


def fd_grad(fh, x, y, t, e=0.02):
    # diferencias centrales de 4o orden
    gx = (-fh(x + 2 * e, y, t) + 8 * fh(x + e, y, t) - 8 * fh(x - e, y, t) + fh(x - 2 * e, y, t)) / (12 * e)
    gy = (-fh(x, y + 2 * e, t) + 8 * fh(x, y + e, t) - 8 * fh(x, y - e, t) + fh(x, y - 2 * e, t)) / (12 * e)
    return gx, gy


rng = np.random.default_rng(20260928)
T0 = time.time()

# ---------------- A. seccion 12 ----------------
S12 = [((0, 0), 0, 0.000, 0.0, 0.0, 0.0), ((380, 0), 0, 0.000, 0.0, 0.0, 0.0), ((1300, -700), 30, 0.000, 0.0, 0.0, 0.0),
       ((3000, 1200), 0, 2.861, 0.005265, 0.002513, 0.000000), ((6000, -2500), 20, 0.786, 0.016807, -0.018130, 0.002257),
       ((-9000, 6000), 45.5, 91.673, -0.301002, 0.105920, 0.170137), ((15000, 5000), 90, 570.044, 0.152987, -0.005119, 0.226075),
       ((21000, -12000), 120, -250.853, 0.028709, 0.101160, 0.000000), ((-30000, -20000), 300, 1959.123, -0.200985, -0.397540, 0.165366),
       ((46000, 9000), 600, 3528.566, 0.090878, -0.483964, 0.324678), ((0, 56000), 30, 777.724, -0.005076, -0.652202, 0.098963),
       ((60000, 10000), 0, 0.000, 0.0, 0.0, 0.0)]
e_h = e_g = e_m = e_mg = 0.0
for (x, y), t, h, gx, gy, hf in S12:
    g = vs("ValleyGradVS", x, y, t); hh = vs("ValleyHeightVS", x, y, t)
    e_h = max(e_h, abs(g[2] - h), abs(hh[2] - h))
    e_g = max(e_g, abs(g[0] - gx), abs(g[1] - gy), abs(g[3] - hf))
    mh, mhf = mi_h(x, y, t)
    fx, fy = fd_grad(lambda a, b, c: mi_h(a, b, c)[0], x, y, t)
    e_m = max(e_m, abs(float(mh) - h), abs(float(mhf) - hf))
    e_mg = max(e_mg, abs(float(fx) - gx), abs(float(fy) - gy))
chk("A1 seccion 12: HLSL (traductor propio, fp64) h y (grad, hf)", e_h <= 0.002 and e_g <= 2e-6, "max |h| %.1e cm, max |grad,hf| %.1e" % (e_h, e_g))
chk("A2 seccion 12: modelo PROPIO desde el texto de la spec, h/hf y gradiente por diferencias finitas", e_m <= 0.002 and e_mg <= 2e-6,
    "max |h,hf| %.1e, max |grad FD| %.1e" % (e_m, e_mg))

# ---------------- B. HLSL vs modelo propio vs valley_model, muchos puntos ----------------
KNOBS = [dict(DEF),
         dict(DEF, HillAmp=3500.0, HillScale=5.0, HillSeed=200.0, HillNear=3000.0, HillFull=7000.0, HillFade=15000.0, HillEnd=21000.0,
              DuneLow=0.1, DuneHigh=0.8, FarBase=4000.0, FarAmp=7000.0, FarScale=13.0, FarSeed=17.0, FarIn=22000.0, FarFull=30000.0,
              FarCrest=40000.0, FarBack=52000.0, SwellAmp=300.0, SwellNear=2500.0, SwellFar=8000.0, SwellScale=3.3, SwellSpeed=1.4,
              SwellSeed=250.0, MorphAmt=0.3, MorphSpeed=1.8),
         # perillas raras (no deberian usarse, pero el codigo tiene que coincidir con la spec igual): rampas degeneradas
         dict(DEF, HillFull=4000.0, HillEnd=18000.0, FarCrest=20000.0, FarBack=10.0, SwellFar=100.0, DuneHigh=-0.4)]
for iq, q in enumerate(KNOBS):
    eh = ehf = evm = ehg = 0.0
    n = 2500 if iq < 2 else 800
    for _ in range(n):
        r = 64500 * math.sqrt(rng.uniform()); a = rng.uniform(-math.pi, math.pi); t = rng.uniform(0, 3600)
        x, y = r * math.cos(a), r * math.sin(a)
        g = vs("ValleyGradVS", x, y, t, q); hh = vs("ValleyHeightVS", x, y, t, q)
        mh, mhf = mi_h(x, y, t, q)
        eh = max(eh, abs(g[2] - mh), abs(hh[2] - mh)); ehf = max(ehf, abs(g[3] - mhf)); ehg = max(ehg, abs(g[2] - hh[2]))
        qv = {k: v for k, v in q.items()}
        vx, vy, vh, vf = (float(v[0]) for v in vm.valley_grad(np.array([x]), np.array([y]), t, qv))
        evm = max(evm, abs(vh - mh), abs(vx - g[0]), abs(vy - g[1]))
    tol = 3e-3
    chk("B%d HLSL = modelo propio (h, hf) y = valley_model (h, grad); %d puntos hasta 645 m, t hasta 1 h, perillas %s" % (
        iq + 1, n, ["default", "no default", "degeneradas"][iq]), eh < tol and ehf < 2e-6 and evm < tol and ehg < 1e-9,
        "|h| %.1e cm |hf| %.1e |valley_model| %.1e |hHeight-hGrad| %.1e" % (eh, ehf, evm, ehg))

# ---------------- C. gradiente analitico vs diferencias finitas EN LAS TRANSICIONES ----------------
def fdh(q):
    return lambda a, b, c: vs("ValleyHeightVS", a, b, c, q)[2]


worst = (0, None)
worst_rel = (0, None)
nprob = 0
for q in KNOBS[:2]:
    bordes = [q["SwellNear"], q["SwellFar"], q["HillNear"], q["HillFull"], q["HillFade"], q["HillEnd"], q["FarIn"], q["FarFull"],
              q["FarCrest"], q["FarBack"]]
    for R in bordes:
        for d in (-300.0, -20.0, -1.0, -0.1, 0.1, 1.0, 20.0, 300.0):
            for az in np.linspace(-math.pi, math.pi, 24, endpoint=False):
                for t in (0.0, 7.3, 123.4, 1799.9, 3599.95):
                    r = R + d
                    x, y = r * math.cos(az), r * math.sin(az)
                    g = vs("ValleyGradVS", x, y, t, q)
                    fx, fy = fd_grad(fdh(q), x, y, t, e=0.01)
                    err = max(abs(fx - g[0]), abs(fy - g[1]))
                    rel = err / max(1e-4, math.hypot(g[0], g[1]))
                    nprob += 1
                    if err > worst[0]: worst = (err, (R, d, az, t))
                    if rel > worst_rel[0]: worst_rel = (rel, (R, d, az, t))
chk("C1 gradiente analitico (ValleyGradVS) = diferencias finitas de ValleyHeightVS a +-0,1..300 cm de CADA borde de rampa, "
    "24 azimuts x 5 t, dos juegos de perillas (%d puntos)" % nprob, worst[0] < 1e-6,
    "max abs %.1e en %s; max rel %.1e" % (worst[0], worst[1], worst_rel[0]))
# umbrales de las dunas (tf y tl cerca de 0 y de 1): buscar puntos con sig ~ DuneLow / DuneHigh y sgF ~ -0.7 / 1.2
cnt = 0; werr = 0.0
F, ins = TR[("ValleyGradVS", np.float64)]
for _ in range(20000):
    r = rng.uniform(4600, 58500); a = rng.uniform(-math.pi, math.pi); t = rng.uniform(0, 900)
    x, y = r * math.cos(a), r * math.sin(a)
    sH = sigma(x, y, t, DEF["HillScale"], DEF["HillSeed"], DEF); sF = sigma(x, y, t, DEF["FarScale"], DEF["FarSeed"], DEF)
    cerca = min(abs(sH - DEF["DuneLow"]), abs(sH - DEF["DuneHigh"])) < 0.01 if r < 26000 else min(abs(sF + 0.7), abs(sF - 1.2)) < 0.01
    if not cerca or r < 28000 and r > 26000:
        continue
    cnt += 1
    g = vs("ValleyGradVS", x, y, t)
    fx, fy = fd_grad(fdh(DEF), x, y, t, e=0.01)
    werr = max(werr, abs(fx - g[0]), abs(fy - g[1]))
chk("C2 gradiente = FD tambien junto a los umbrales de las dunas (|sigma - umbral| < 0,01; %d puntos)" % cnt, cnt > 100 and werr < 1e-6, "max %.1e" % werr)

# ---------------- D. continuidad C2 en los bordes de rampa (salto de la segunda derivada radial) ----------------
# d2h/dr2 a cada lado del borde con el gradiente ANALITICO: (g(R+2e) - g(R+e))/e vs (g(R-e) - g(R-2e))/e, e -> 0.
# Control positivo: la misma medicion sobre una rampa smoothstep (C1) tiene que mostrar salto.
def grad_r(q, R, az, t):
    x, y = R * math.cos(az), R * math.sin(az)
    g = vs("ValleyGradVS", x, y, t, q)
    return g[0] * math.cos(az) + g[1] * math.sin(az)


def salto2(fr_, R, e):
    dr_mas = (fr_(R + 2 * e) - fr_(R + e)) / e
    dr_men = (fr_(R - e) - fr_(R - 2 * e)) / e
    return abs(dr_mas - dr_men)


peor = (0, None)
for R in [DEF[k] for k in ("SwellNear", "SwellFar", "HillNear", "HillFull", "HillFade", "HillEnd", "FarIn", "FarFull", "FarCrest", "FarBack")]:
    for az in np.linspace(-math.pi, math.pi, 12, endpoint=False):
        for t in (0.0, 311.1):
            s = salto2(lambda rr: grad_r(DEF, rr, az, t), R, 0.5)
            # escala: |d2h/dr2| tipico en esa zona
            tip = abs((grad_r(DEF, R + 400, az, t) - grad_r(DEF, R + 200, az, t)) / 200) + 1e-9
            if s > peor[0]:
                peor = (s, (R, round(az, 2), t, tip))
# control positivo: smoothstep (C1) en r con la misma amplitud del borde del oleaje
def g_ss(rr, a=1500.0, b=12000.0, A=560.0):
    t = min(max((rr - a) / (b - a), 0), 1)
    return A * 6 * t * (1 - t) / (b - a)
ctl = salto2(g_ss, 1500.0, 0.5)
chk("D1 altura C2 en TODOS los bordes de rampa: salto de d2h/dr2 a +-0,5 cm del borde (12 azimuts x 2 t)", peor[0] < 1e-7 and ctl > 1e-6,
    "max salto %.2e cm^-1 en %s; control positivo smoothstep: salto %.2e" % (peor[0], peor[1], ctl))

# ---------------- E. piso = 0 exacto y quieto ----------------
tt = [0.0, 1.0 / 72, 17.7, 900.0, 3600.0, 36000.0, 1e5, 1e6] + list(rng.uniform(0, 7200, 12))
zmax = 0.0; n = 0
for dt in (np.float64, np.float32):
    for t in tt:
        for c in ((0.0, 0.0), (380.0, 0.0)):
            for rr in np.linspace(0, 1000, 11):
                for az in np.linspace(-math.pi, math.pi, 16, endpoint=False):
                    x, y = c[0] + rr * math.cos(az), c[1] + rr * math.sin(az)
                    g = vs("ValleyGradVS", x, y, t, dt=dt); hh = vs("ValleyHeightVS", x, y, t, dt=dt)
                    zmax = max(zmax, float(np.abs(g).max()), float(np.abs(hh).max())); n += 1
chk("E1 piso = 0 EXACTO (h, grad, hf) a <= 10 m del usuario y del metaball, fp64 y fp32, t hasta 1e6 s (%d evaluaciones)" % n, zmax == 0.0, "max %.1e" % zmax)
# todo el disco r <= SwellNear (15 m), borde incluido
zmax = 0.0
for t in tt[:6]:
    for rr in np.linspace(0, 1500, 61):
        for az in np.linspace(-math.pi, math.pi, 36, endpoint=False):
            g = vs("ValleyGradVS", rr * math.cos(az), rr * math.sin(az), t, dt=np.float32)
            zmax = max(zmax, float(np.abs(g).max()))
chk("E2 piso = 0 EXACTO en todo r <= 15 m (fp32, 6 t)", zmax == 0.0, "max %.1e" % zmax)
# el primer punto que se mueve: |h| a 15,5 / 16 / 20 m (tiene que crecer desde 0 sin salto)
vals = []
for rr in (1501.0, 1550.0, 1600.0, 2000.0):
    vals.append(max(abs(vs("ValleyHeightVS", rr * math.cos(a), rr * math.sin(a), t)[2]) for a in np.linspace(0, 6.28, 36) for t in (0, 50)))
print("INFO  max |h| a 15,01 / 15,5 / 16 / 20 m: %s cm" % ", ".join("%.2e" % v for v in vals))

# ---------------- F. fp32 (lo que corre en la Quest) vs fp64 ----------------
eh32 = 0.0; eg32 = 0.0; wh = None
for t in (0.0, 300.0, 3600.0, 36000.0):
    for _ in range(600):
        r = 64000 * math.sqrt(rng.uniform()); a = rng.uniform(-math.pi, math.pi)
        x, y = r * math.cos(a), r * math.sin(a)
        g64 = vs("ValleyGradVS", x, y, t); g32 = vs("ValleyGradVS", np.float32(x), np.float32(y), t, dt=np.float32)
        h32 = vs("ValleyHeightVS", np.float32(x), np.float32(y), t, dt=np.float32)
        # la referencia fp64 con la MISMA posicion redondeada a fp32
        g64 = vs("ValleyGradVS", float(np.float32(x)), float(np.float32(y)), float(np.float32(t)))
        e = max(abs(float(g32[2]) - g64[2]), abs(float(h32[2]) - g64[2]))
        if e > eh32: eh32, wh = e, (round(r), t)
        eg32 = max(eg32, abs(float(g32[0]) - g64[0]), abs(float(g32[1]) - g64[1]))
chk("F1 fp32 vs fp64: h (cm) y gradiente, 2400 puntos, t hasta 10 h", eh32 < 2.0 and eg32 < 1e-3,
    "max |h| %.3f cm en r,t=%s; max |grad| %.1e" % (eh32, wh, eg32))
# continuidad temporal en fp32: cuadro a cuadro (72 Hz) cruzando los cambios de vuelta de frac(t/T) y en sesiones largas
peor_salto = 0.0
for T0w, per in ((42.0, 42.0), (36.0, 36.0), (31.0 * 30, 31.0), (46.0 * 80, 46.0), (53.0 * 20, 53.0), (3600.0, 1.0), (7200.0 + 83.0 * 3, 83.0)):
    for _ in range(40):
        r = rng.uniform(1600, 58000); a = rng.uniform(-math.pi, math.pi)
        x, y = np.float32(r * math.cos(a)), np.float32(r * math.sin(a))
        ts = np.float32(T0w) + np.arange(-6, 7, dtype=np.float32) / np.float32(72)
        hs = [float(vs("ValleyHeightVS", x, y, float(tv), dt=np.float32)[2]) for tv in ts]
        d = np.abs(np.diff(hs))
        # velocidad maxima fisica: |dh/dt| <= A*2pi*sum(w/T)/2.95 + morph; a 72 Hz, cota holgada 3 cm por cuadro a 590 m
        peor_salto = max(peor_salto, float(d.max()))
chk("F2 continuidad temporal en fp32 cuadro a cuadro alrededor de los cambios de vuelta de frac() y a t = 1-2 h",
    peor_salto < 3.0, "max |dh| por cuadro %.3f cm" % peor_salto)

# ---------------- G. cotas de h (bounds del asset) ----------------
# malla: radios reconstruidos desde el pseudocodigo de la seccion 2 (no desde gen_breath_valley.py)
S = 144
radii = [60.0 * j for j in range(1, 19)]
r_ = radii[-1]
while True:
    qg = (1 + 2 * math.pi / S) if r_ < 6000 else (1 + 0.6 * 2 * math.pi / S)
    rn = r_ * qg
    if rn >= 59000 - 0.5 * (rn - r_):
        break
    r_ = rn; radii.append(r_)
radii.append(59000.0); radii += [59000 + 5000 * j / 4 for j in range(1, 5)]
chk("G0 malla desde el pseudocodigo de la seccion 2: 150 anillos, 21601 vertices", len(radii) == 150 and 1 + 144 * len(radii) == 21601,
    "anillos %d, vertices %d, primero geometrico %.2f, ultimos %s" % (len(radii), 1 + 144 * len(radii), radii[18],
                                                                     ", ".join("%.1f" % v for v in radii[-7:])))
ang = 2 * np.pi * np.arange(S) / S
RR = np.array(radii)
X = (RR[:, None] * np.cos(ang)[None, :]).ravel(); Y = (RR[:, None] * np.sin(ang)[None, :]).ravel()
hmax, hmin = -1e9, 1e9
for t in np.arange(0.0, 3600.0, 1.7):
    h, _ = mi_h(X, Y, t)
    hmax = max(hmax, float(h.max())); hmin = min(hmin, float(h.min()))
# cota continua (todas las olas alineadas, dunas al tope): sup/inf sobre r
rr = np.linspace(0, 64000, 640001)
q = DEF
FC = q["FarCrest"]; FB = q["FarBack"]
back = 1 - S5(FC, FB, rr)
A = q["SwellAmp"] * S5(q["SwellNear"], q["SwellFar"], rr) * rr / q["SwellFar"]
envH = S5(q["HillNear"], q["HillFull"], rr) * (1 - S5(q["HillFade"], q["HillEnd"], rr))
sup = back * (q["HillAmp"] * envH + q["FarBase"] * S5(q["FarIn"], FC, rr) + q["FarAmp"] * S5(q["FarIn"], q["FarFull"], rr) + A)
inf = back * (q["FarBase"] * S5(q["FarIn"], FC, rr) - A)
chk("G1 bounds del asset (Positive 12000 / Negative 2000) cubren h en los vertices (cada 1,7 s durante 1 h) y la cota continua",
    hmax <= 12000 and -hmin <= 2000 and sup.max() <= 12000 and -inf.min() <= 2000,
    "vertices: %.0f .. %.0f cm; cota continua: %.0f (r=%.0f) .. %.0f (r=%.0f) cm; la spec dice cota 10293 y ~-1400"
    % (hmin, hmax, sup.max(), rr[sup.argmax()], inf.min(), rr[inf.argmin()]))
# con las perillas en el borde de los rangos sugeridos de la 7.1 (informativo: la extension es fija en el asset)
qx = dict(DEF, FarBase=5000.0, FarAmp=8000.0, SwellAmp=700.0, SwellFar=6000.0, HillAmp=4000.0)
A = qx["SwellAmp"] * S5(qx["SwellNear"], qx["SwellFar"], rr) * rr / qx["SwellFar"]
supx = back * (qx["HillAmp"] * envH + qx["FarBase"] * S5(qx["FarIn"], FC, rr) + qx["FarAmp"] * S5(qx["FarIn"], qx["FarFull"], rr) + A)
infx = back * (qx["FarBase"] * S5(qx["FarIn"], FC, rr) - A)
print("INFO  con perillas en el tope de los rangos sugeridos (FarBase 5000, FarAmp 8000, SwellAmp 700, SwellFar 6000, HillAmp 4000): "
      "h de %.0f a %.0f cm (bounds fijos: -2000 .. 12000)" % (infx.min(), supx.max()))

# ---------------- H. velocidad vertical angular: busqueda del maximo (no solo muestreo al azar) ----------------
def vang(p):
    r, az, t = p
    x, y = r * math.cos(az), r * math.sin(az)
    dh = (mi_h(x, y, t + 0.005)[0] - mi_h(x, y, t - 0.005)[0]) / 0.01
    return math.degrees(abs(float(dh)) / r)


best = []
# vectorizado por instante: para cada t, 40000 puntos
vmax = 0.0; arg = None
for t in rng.uniform(0, 3600, 150):
    r = rng.uniform(1500, 59000, 40000); az = rng.uniform(-math.pi, math.pi, 40000)
    x, y = r * np.cos(az), r * np.sin(az)
    dh = (mi_h(x, y, t + 0.005)[0] - mi_h(x, y, t - 0.005)[0]) / 0.01
    v = np.degrees(np.abs(dh) / r)
    i = int(v.argmax())
    if v[i] > vmax:
        vmax, arg = float(v[i]), (float(r[i]), float(az[i]), float(t))
    best.append((float(v[i]), float(r[i]), float(az[i]), float(t)))
best.sort(reverse=True)
try:
    from scipy.optimize import minimize
    for v0, r0, a0, t0 in best[:12]:
        res = minimize(lambda p: -vang(p), [r0, a0, t0], method="Nelder-Mead", options=dict(xatol=1e-3, fatol=1e-7, maxiter=3000))
        if -res.fun > vmax and 1500 <= res.x[0] <= 59000:
            vmax, arg = -res.fun, tuple(res.x)
except Exception as ex:
    print("INFO  sin scipy: %r" % ex)
chk("H1 velocidad vertical angular maxima (6 millones de muestras + optimizacion local) <= 0,5 grados/s", vmax <= 0.5,
    "max %.3f grados/s en r=%.0f cm, az=%.2f, t=%.1f s (la spec dice 0,487 medido / 'suma <= 0,49')" % (vmax, arg[0], arg[1], arg[2]))
# cota rigurosa (todas las fases alineadas): oleaje + respiracion de las colinas medias
rr2 = np.linspace(1500, 59000, 200000)
SFc = DEF["SwellFar"]
cw = sum(w * 2 * math.pi / T for _, _, T, w, _ in WAVES) / 2.95
A2 = DEF["SwellAmp"] * S5(DEF["SwellNear"], SFc, rr2) * rr2 / SFc
bk2 = 1 - S5(DEF["FarCrest"], DEF["FarBack"], rr2)
cm = DEF["MorphAmt"] * 2 * math.pi * DEF["MorphSpeed"] * sum(a / T for _, _, a, _, T, _ in DUNES) / 2.65
dfmax_h = 1.875 / (DEF["DuneHigh"] - DEF["DuneLow"]); dfmax_f = 1.875 / 1.9
envH2 = S5(DEF["HillNear"], DEF["HillFull"], rr2) * (1 - S5(DEF["HillFade"], DEF["HillEnd"], rr2))
envF2 = S5(DEF["FarIn"], DEF["FarFull"], rr2)
cota = bk2 * (A2 * cw + DEF["HillAmp"] * envH2 * dfmax_h * cm + DEF["FarAmp"] * envF2 * dfmax_f * cm) / rr2
print("INFO  cota RIGUROSA de la velocidad vertical angular (fases alineadas): %.3f grados/s en r = %.0f m "
      "(oleaje solo: %.3f)" % (math.degrees(cota.max()), rr2[cota.argmax()] / 100, math.degrees((bk2 * A2 * cw / rr2).max())))

print("\nRESULTADO numerico: " + ("TODO OK" if not fallas else "FALLAS: %s" % fallas) + "  (%.0f s)" % (time.time() - T0))
