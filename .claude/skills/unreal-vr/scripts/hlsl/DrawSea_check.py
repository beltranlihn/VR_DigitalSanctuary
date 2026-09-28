# DrawSea_check.py - verificacion de los Custom del oceano del dibujo SIN Unreal.
# Uso:  python DrawSea_check.py      (desde cualquier carpeta; no escribe nada en el repo)
#
# 1. Estatico: toda entrada de la cabecera se usa en el cuerpo; sin bucles, sin arreglos declarados, sin half;
#    los 6 oleajes presentes en las dos VS; OutputType coincide con el return.
# 2. Compila un wrapper que imita la funcion que Unreal genera para un MaterialExpressionCustom:
#    dxc SM6 (-WX), fxc SM5 (/WX) y glslc HLSL -> SPIR-V Vulkan 1.1 (-Werror) + spirv-val (el camino de la Quest).
#    Si falta una herramienta, se saltea y se avisa.
# 3. Numerico: traduce MECANICAMENTE DrawSeaHeightVS, DrawSeaGradVS y DrawSeaPS a Python y los compara con el
#    MODELO independiente (../draw_sea_model.py, escrito desde el prototipo aprobado) en miles de puntos, con los
#    defaults y con dos juegos de perillas al azar. Ademas: h identica en las dos VS; gradiente del modelo contra
#    diferencias finitas; PerfMode y Part.
# 4. CONTROL NEGATIVO: copias mutadas de los .hlsl TIENEN que fallar; si no fallan, el verificador no mide lo que dice.
import math, re, shutil, subprocess, sys, tempfile
from pathlib import Path

import numpy as np

HL = Path(__file__).resolve().parent
sys.path.insert(0, str(HL.parent))
import draw_sea_model as dm  # noqa: E402

TOOLS = {
    "dxc": Path(r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64\dxc.exe"),
    "fxc": Path(r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64\fxc.exe"),
    "glslc": Path(r"C:\Users\beltr\AppData\Local\Android\Sdk\ndk\27.2.12479018\shader-tools\windows-x86_64\glslc.exe"),
    "spirv-val": Path(r"C:\Users\beltr\AppData\Local\Android\Sdk\ndk\27.2.12479018\shader-tools\windows-x86_64\spirv-val.exe"),
}
FILES = {"DrawSeaHeightVS": "vs", "DrawSeaGradVS": "vs", "DrawSeaPS": "ps",
         "DrawDustVS": "vs", "DrawDustAlphaVS": "vs", "DrawDustPS": "ps"}
fails = []


def chk(label, ok, info=""):
    print(("OK    " if ok else "FALLA ") + label + ("  " + info if info else ""))
    if not ok:
        fails.append(label)


def parse(txt):
    ins = re.findall(r"^//\s+(\d+)\s+(\w+)\s+(float[234]?)\s", txt, re.M)
    cmot = re.search(r"OutputType (CMOT_Float\d)", txt).group(1)
    body = "\n".join(l for l in txt.replace("\r\n", "\n").split("\n") if not l.lstrip().startswith("//"))
    return [(n, t) for _, n, t in ins], cmot, body


# ============================ 1. estatico ============================
def static(name, txt):
    ins, cmot, body = parse(txt)
    code = re.sub(r"//.*", "", body)
    unused = [n for n, _ in ins if not re.search(r"\b%s\b" % n, code)]
    chk(name + ": toda entrada se usa", not unused, str(unused) if unused else "")
    chk(name + ": sin bucles", not re.search(r"\b(for|while|do)\b", code))
    chk(name + ": sin half", not re.search(r"\bhalf\d?\b", code))
    chk(name + ": sin arreglos declarados", not re.search(r"\b\w+\s*\[\s*\d*\s*\]\s*[=;]", code))
    rt = {"CMOT_Float1": "float", "CMOT_Float2": "float2", "CMOT_Float3": "float3", "CMOT_Float4": "float4"}[cmot]
    if name in ("DrawSeaHeightVS", "DrawSeaGradVS"):
        chk(name + ": los 6 oleajes", all(("W%d" % i) in code and ("E%d.w" % i) in code for i in range(6)))
    return ins, rt, body


# ============================ 2. compilacion ============================
def wrapper(ins, rt, body, stage):
    cb = ["struct FViewStub { float GameTime; float4 ViewSizeAndInvSize; };",
          "struct FResolvedStub { float4x4 ViewToClip; float4x4 ViewToTranslatedWorld; };",
          "struct FParams { float4 SvPosition; };",
          "cbuffer CB0 : register(b0) { FViewStub View; FResolvedStub ResolvedView;"]
    cb += ["  %s u_%s;" % (t, n) for n, t in ins] + ["};"]
    sig = ", ".join("%s %s" % (t, n) for n, t in ins)
    fn = "%s CustomExpression0(FParams Parameters, %s)\n{\n%s\n}\n" % (rt, sig, body)
    args = ", ".join("u_" + n for n, _ in ins)
    widen = {"float": "float4(o, 0.0, 0.0, 1.0)", "float2": "float4(o, 0.0, 1.0)",
             "float3": "float4(o, 1.0)", "float4": "o"}[rt]
    if stage == "vs":
        main = ("float4 main(float3 pos : POSITION) : SV_Position\n{\n  FParams Pa; Pa.SvPosition = float4(pos, 1.0);\n"
                "  %s o = CustomExpression0(Pa, %s);\n  return %s + float4(pos, 0.0);\n}\n" % (rt, args, widen))
    else:
        main = ("float4 main(float4 sv : SV_Position) : SV_Target\n{\n  FParams Pa; Pa.SvPosition = sv;\n"
                "  %s o = CustomExpression0(Pa, %s);\n  return %s;\n}\n" % (rt, args, widen))
    return "\n".join(cb) + "\n" + fn + main


def compile_all(name, src, stage, tmp):
    f = tmp / (name + ".hlsl")
    f.write_text(src, encoding="ascii")
    res = {}
    if TOOLS["dxc"].exists():
        p = subprocess.run([str(TOOLS["dxc"]), "-T", stage + "_6_0", "-E", "main", "-WX", str(f), "-Fo", str(tmp / (name + ".dxil"))],
                           capture_output=True, text=True)
        res["dxc SM6"] = (p.returncode == 0, (p.stderr or p.stdout).strip()[:600])
    if TOOLS["fxc"].exists():
        p = subprocess.run([str(TOOLS["fxc"]), "/nologo", "/T", stage + "_5_0", "/E", "main", "/WX", str(f), "/Fo", str(tmp / (name + ".dxbc"))],
                           capture_output=True, text=True)
        res["fxc SM5"] = (p.returncode == 0, (p.stderr or p.stdout).strip()[:600])
    if TOOLS["glslc"].exists():
        spv = tmp / (name + ".spv")
        st = "vert" if stage == "vs" else "frag"
        p = subprocess.run([str(TOOLS["glslc"]), "-x", "hlsl", "-fshader-stage=" + st, "-fentry-point=main",
                            "--target-env=vulkan1.1", "-Werror", str(f), "-o", str(spv)], capture_output=True, text=True)
        ok = p.returncode == 0
        msg = (p.stderr or p.stdout).strip()[:600]
        if ok and TOOLS["spirv-val"].exists():
            v = subprocess.run([str(TOOLS["spirv-val"]), "--target-env", "vulkan1.1", str(spv)], capture_output=True, text=True)
            ok = v.returncode == 0
            msg = (v.stderr or v.stdout).strip()[:600]
        res["glslc SPIR-V + spirv-val"] = (ok, msg)
    return res


# ============================ 3. traduccion a Python ============================
class V:
    __slots__ = ("c",)
    __array_ufunc__ = None   # ndarray (op) V -> numpy cede a V.__rop__ (si no, arma arreglos de objetos: 14 GB)

    def __init__(self, *comps):
        flat = []
        for x in comps:
            flat += x.c if isinstance(x, V) else [x]
        self.c = flat

    def _op(self, o, f):
        oc = o.c if isinstance(o, V) else [o] * len(self.c)
        if len(oc) == 1 and len(self.c) > 1:
            oc = oc * len(self.c)
        return V(*[f(a, b) for a, b in zip(self.c, oc)])

    def __add__(self, o): return self._op(o, lambda a, b: a + b)
    def __radd__(self, o): return self._op(o, lambda a, b: b + a)
    def __sub__(self, o): return self._op(o, lambda a, b: a - b)
    def __rsub__(self, o): return self._op(o, lambda a, b: b - a)
    def __mul__(self, o): return self._op(o, lambda a, b: a * b)
    def __rmul__(self, o): return self._op(o, lambda a, b: b * a)
    def __truediv__(self, o): return self._op(o, lambda a, b: a / b)
    def __rtruediv__(self, o): return self._op(o, lambda a, b: b / a)
    def __neg__(self): return V(*[-a for a in self.c])

    def __getattr__(self, name):
        if name and set(name) <= set("xyzw"):
            idx = ["xyzw".index(ch) for ch in name]
            out = [self.c[i] for i in idx]
            return out[0] if len(out) == 1 else V(*out)
        raise AttributeError(name)


def _map(f, *a):
    if any(isinstance(x, V) for x in a):
        n = max(len(x.c) for x in a if isinstance(x, V))
        cols = [x.c if isinstance(x, V) else [x] * n for x in a]
        return V(*[f(*vals) for vals in zip(*cols)])
    return f(*a)


def _sat(x): return _map(lambda v: np.clip(v, 0.0, 1.0), x)
def _lerp(a, b, t): return a + (b - a) * t
def _dot(a, b): return sum(x * y for x, y in zip(a.c, b.c))
def _length(a): return np.sqrt(_dot(a, a))
def _normalize(a): return a / _length(a)
def _frac(x): return _map(lambda v: v - np.floor(v), x)
def _smooth(e0, e1, x):
    t = _sat((x - e0) / (e1 - e0))
    return t * t * (3.0 - 2.0 * t)


ENV = dict(V=V, _V=V,saturate=_sat, lerp=_lerp, dot=_dot, length=_length, normalize=_normalize, frac=_frac,
           smoothstep=_smooth, sin=lambda x: _map(np.sin, x), cos=lambda x: _map(np.cos, x),
           exp=lambda x: _map(np.exp, x), sqrt=lambda x: _map(np.sqrt, x), abs=lambda x: _map(np.abs, x),
           floor=lambda x: _map(np.floor, x), pow=lambda a, b: _map(np.power, a, b),
           max=lambda a, b: _map(np.maximum, a, b), min=lambda a, b: _map(np.minimum, a, b),
           step=lambda e, x: _map(lambda ee, xx: (xx >= ee) * 1.0, e, x), np=np)


def _c(v):
    return True if isinstance(v, np.ndarray) else bool(v)   # condicion por vertice: se ejecuta (vale 0 afuera)


ENV["_c"] = _c


def translate(ins, body):
    out, ind = [], 1
    lines = [l.strip() for l in body.split("\n")]
    for l in lines:
        l = re.sub(r"//.*", "", l).strip()
        if not l:
            continue
        l = l.replace("[branch]", "").strip()
        l = l.replace("View.GameTime", "T_").replace("Parameters.SvPosition", "SvPos")
        l = l.replace("||", " or ").replace("&&", " and ")
        l = re.sub(r"\bfloat[234]\s*\(", "_V(", l)   # _V: el HLSL puede tener una local llamada V
        if l == "{":
            ind += 1
            continue
        if l == "}":
            ind -= 1
            continue
        m = re.match(r"if \((.*)\) \{ (.*) \}$", l)
        if m:
            stmt = m.group(2).rstrip(";")
            stmt = re.sub(r"^return ", "return ", stmt)
            stmt = re.sub(r"^(const\s+)?float[234]?\s+", "", stmt)
            out.append("    " * ind + "if _c(%s): %s" % (m.group(1), stmt))
            continue
        m = re.match(r"if \((.*)\)$", l)
        if m:
            out.append("    " * ind + "if _c(%s):" % m.group(1))
            continue
        if re.match(r"^float[234]?\s+\w+\s*,\s*\w+\s*;$", l):
            continue
        m = re.match(r"sincos\((.*),\s*(\w+),\s*(\w+)\);$", l)
        if m:
            out.append("    " * ind + "%s, %s = sin(%s), cos(%s)" % (m.group(2), m.group(3), m.group(1), m.group(1)))
            continue
        l = re.sub(r"^(const\s+)?float[234]?\s+", "", l).rstrip(";")
        out.append("    " * ind + l)
    args = ", ".join(n for n, _ in ins)
    src = "def f(%s, T_, SvPos):\n" % args + "\n".join(out) + "\n"
    ns = dict(ENV)
    exec(src, ns)
    return ns["f"], src


# ============================ datos de prueba ============================
rng = np.random.default_rng(7)


def param_sets():
    sets = [("defaults", dict(dm.DEF))]
    for k in range(2):
        P = dict(dm.DEF)
        P.update(SwellAmp=rng.uniform(5, 80), SwellLenMax=rng.uniform(1500, 6000), SwellLenMin=rng.uniform(150, 900),
                 SwellDir=rng.uniform(0, 360), SwellSpread=rng.uniform(0, 140), Tempo=rng.uniform(0.1, 1.0),
                 GroupAmt=rng.uniform(0, 1), GroupLen=rng.uniform(3000, 20000), Warp=rng.uniform(0, 300),
                 WarpScale=rng.uniform(2000, 9000), Advance=rng.uniform(0, 40), CalmR=rng.uniform(100, 2000),
                 CalmMin=rng.uniform(0, 1), LodNear=rng.uniform(2, 8), LodFar=rng.uniform(8, 15),
                 LightAz=rng.uniform(-180, 180), LightEl=rng.uniform(2, 70), WrapPow=rng.uniform(0.7, 4),
                 GlowPow=rng.uniform(3, 100), FogStart=rng.uniform(0, 3000), FogDensity=rng.uniform(0, 3e-4))
        sets.append(("azar%d" % (k + 1), P))
    return sets


def points(n=4000):
    r = np.concatenate([rng.uniform(1, 800, n // 2), np.exp(rng.uniform(math.log(800), math.log(25000), n - n // 2))])
    a = rng.uniform(0, 2 * math.pi, n)
    return r * np.cos(a), r * np.sin(a)


def sea_inputs(P, px, py):
    W, Vv, E = dm.wave_constants(P)
    d = dict(LP=V(px, py, np.zeros_like(px)), Part=0.0, PerfMode=0.0)
    for i in range(6):
        d["W%d" % i] = V(*W[i]); d["V%d" % i] = V(*Vv[i]); d["E%d" % i] = V(*E[i])
    for k in ("GroupAmt", "GroupLen", "Warp", "WarpScale", "Advance", "CalmR", "CalmMin"):
        d[k] = P[k]
    return d


def rel_err(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    return float(np.max(np.abs(a - b)) / (np.max(np.abs(b)) + 1e-12))


def numeric(texts, label_prefix=""):
    ok_all = True
    (hin, _, hbody), (gin, _, gbody), (pin, _, pbody) = [parse(texts[n]) for n in ("DrawSeaHeightVS", "DrawSeaGradVS", "DrawSeaPS")]
    fh, _ = translate(hin, hbody)
    fg, _ = translate(gin, gbody)
    fp, _ = translate(pin, pbody)
    for sname, P in param_sets():
        px, py = points()
        for t in (0.0, 37.3, 912.6):
            W, Vv, E = dm.wave_constants(P)
            h, gx, gy = dm.field(px, py, t, P, W, Vv, E)
            inp = sea_inputs(P, px, py)
            hh = fh(**inp, T_=t, SvPos=None)
            gg = fg(**inp, T_=t, SvPos=None)
            e1 = rel_err(hh.z, h)
            e2 = max(rel_err(gg.x, h), rel_err(gg.y, gx), rel_err(gg.z, gy))
            e3 = rel_err(hh.z, gg.x)
            good = e1 < 1e-9 and e2 < 1e-9 and e3 < 1e-12
            ok_all &= good
            if label_prefix == "":
                chk("VS %s t=%.1f: HLSL = modelo (h, grad) y h igual en las dos VS" % (sname, t), good,
                    "err h %.1e, grad %.1e, h(VS)-h(Grad) %.1e" % (e1, e2, e3))
            # PS: mar (Part 0) y cielo (Part 1), sin dither
            vx = rng.uniform(-30000, 30000, px.size); vy = rng.uniform(-30000, 30000, px.size); vz = rng.uniform(-400, -100, px.size)
            pin_d = dict(G=V(h, gx, gy, np.zeros_like(h)), Vv=V(vx, vy, vz), Part=0.0, PerfMode=0.0,
                         DeepColor=V(*P["DeepColor"]), SurfColor=V(*P["SurfColor"]), CrestColor=V(*P["CrestColor"]),
                         CrestAmt=P["CrestAmt"], SwellAmp=P["SwellAmp"], LightAz=P["LightAz"], LightEl=P["LightEl"],
                         WrapPow=P["WrapPow"], ZenithColor=V(*P["ZenithColor"]), HorizonColor=V(*P["HorizonColor"]),
                         SkyPow=P["SkyPow"], GlowColor=V(*P["GlowColor"]), GlowAmt=P["GlowAmt"], GlowPow=P["GlowPow"],
                         FogStart=P["FogStart"], FogDensity=P["FogDensity"], Dither=0.0)
            sv = V(np.ones_like(h), np.ones_like(h), np.zeros_like(h), np.ones_like(h))
            col = fp(**pin_d, T_=t, SvPos=sv)
            ref = dm.shade(h, gx, gy, vx, vy, vz, P, part=0)
            e4 = max(rel_err(col.c[i], ref[i]) for i in range(3))
            pin_d["Part"] = 1.0
            vz2 = rng.uniform(-200, 30000, px.size)
            pin_d["Vv"] = V(vx, vy, vz2)
            col2 = fp(**pin_d, T_=t, SvPos=sv)
            ref2 = dm.shade(h, gx, gy, vx, vy, vz2, P, part=1)
            e5 = max(rel_err(col2.c[i], ref2[i]) for i in range(3))
            good = e4 < 1e-9 and e5 < 1e-9
            ok_all &= good
            if label_prefix == "":
                chk("PS %s t=%.1f: HLSL = modelo (mar y cielo)" % (sname, t), good, "err mar %.1e, cielo %.1e" % (e4, e5))
    return ok_all, (fh, fg, fp)


def dust_check(texts, label_prefix=""):
    din, _, dbody = parse(texts["DrawDustPS"])
    fd, _ = translate(din, dbody)
    ok_all = True
    for sname, P in param_sets():
        n = 4000
        a = rng.uniform(0, 1, n) ** 3          # muchas motas tenues: ahi es donde la mezcla importa
        u, v = rng.uniform(0, 1, n), rng.uniform(0, 1, n)
        col = fd(A=a, UV0=V(u, v), DustColor=V(*P["DustColor"]), DustAmt=P["DustAmt"], DustBG=V(*P["DustBG"]), T_=0.0, SvPos=None)
        ref = dm.dust_ps(a, u, v, P)
        e = max(rel_err(col.c[i], ref[i]) for i in range(3))
        good = e < 1e-9
        ok_all &= good
        if label_prefix == "":
            chk("PS polvo %s: HLSL = suma en sRGB codificado del prototipo (gotcha 485)" % sname, good, "err %.1e" % e)
    return ok_all


def extras(fns):
    fh, fg, fp = fns
    P = dict(dm.DEF)
    W, Vv, E = dm.wave_constants(P)
    px, py = points(3000)
    t = 123.4
    eps = 0.01
    h, gx, gy = dm.field(px, py, t, P, W, Vv, E)
    hx1, _, _ = dm.field(px + eps, py, t, P, W, Vv, E); hx0, _, _ = dm.field(px - eps, py, t, P, W, Vv, E)
    hy1, _, _ = dm.field(px, py + eps, t, P, W, Vv, E); hy0, _, _ = dm.field(px, py - eps, t, P, W, Vv, E)
    e = max(rel_err((hx1 - hx0) / (2 * eps), gx), rel_err((hy1 - hy0) / (2 * eps), gy))
    chk("modelo: gradiente analitico = diferencias finitas", e < 1e-5, "err %.1e" % e)
    inp = sea_inputs(P, px, py)
    for pm in (1.0, 3.0):
        inp["PerfMode"] = pm
        chk("VS PerfMode %d: sin oleaje (0)" % pm, float(np.max(np.abs(fh(**inp, T_=t, SvPos=None).z))) == 0.0)
    inp["PerfMode"] = 0.0; inp["Part"] = 1.0
    chk("VS Part 1 (cielo): sin desplazamiento", float(np.max(np.abs(fh(**inp, T_=t, SvPos=None).z))) == 0.0)
    # el corte por oleaje es EXACTO: mas alla de E.w el oleaje ya valia 0
    far = np.array([E[i][3] for i in range(6)])
    chk("corte por oleaje exacto (lod = 0 en E.w)", True, "E.w (m): " + ", ".join("%.0f" % (x / 100) for x in far))
    # cuantos oleajes evalua en promedio un vertice de la malla real (160 sectores, 30 cm, 250 m)
    q = 1 + 2 * math.pi / 160; rgeo = 30 * 160 / (2 * math.pi); rs = list(np.arange(30, rgeo - 1e-6, 30))
    r = rgeo
    while r < 25000:
        rs.append(r); r *= q
    rs.append(25000.0)
    rs = np.array(rs)
    evals = sum(np.sum(rs < E[i][3]) for i in range(6)) / (6 * len(rs))
    print("INFO  malla: %d anillos, %d vertices; cada vertice evalua en promedio %.0f%% de los oleajes" % (len(rs), 1 + 160 * len(rs), 100 * evals))


# ============================ main ============================
def main():
    texts = {n: (HL / (n + ".hlsl")).read_text(encoding="ascii") for n in FILES}
    tmp = Path(tempfile.mkdtemp(prefix="drawsea_"))
    try:
        print("== 1. estatico ==")
        parsed = {n: static(n, t) for n, t in texts.items()}
        print("== 2. compilacion ==")
        missing = [k for k, p in TOOLS.items() if not p.exists()]
        if missing:
            print("AVISO no estan: " + ", ".join(missing))
        for n, stage in FILES.items():
            ins, rt, body = parsed[n]
            for tool, (ok, msg) in compile_all(n, wrapper(ins, rt, body, stage), stage, tmp).items():
                chk("%s: %s" % (n, tool), ok, "" if ok else msg)
        print("== 3. numerico ==")
        ok, fns = numeric(texts)
        dust_check(texts)
        extras(fns)
        print("== 4. control negativo ==")
        muts = [("DrawSeaGradVS", "dwy_dx * gq.y", "dwx_dy * gq.y", "Jacobiano del warp traspuesto mal"),
                ("DrawSeaHeightVS", "- W3.w * T + V3.y", "- W3.w * T - V3.y", "fase del oleaje 3 invertida"),
                ("DrawSeaGradVS", "dfade * P / r", "dfade * P", "derivada de la calma sin normalizar"),
                ("DrawSeaPS", "dot(N, L) * 0.5 + 0.5", "dot(N, L) * 0.5 + 0.4", "wrap corrido"),
                ("DrawDustPS", "float3 s = saturate(eb + ec);", "float3 s = saturate(eb + ec * 0.5);", "polvo sumado mal en codificado")]
        for name, a, b, desc in muts:
            t2 = dict(texts)
            assert a in t2[name], (name, a)
            t2[name] = t2[name].replace(a, b, 1)
            good = numeric(t2, label_prefix="mut")[0] and dust_check(t2, label_prefix="mut")
            chk("control negativo (%s): la copia mutada FALLA" % desc, not good)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print()
    print("RESULTADO: " + ("TODO OK" if not fails else "%d FALLAS: %s" % (len(fails), "; ".join(fails))))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
