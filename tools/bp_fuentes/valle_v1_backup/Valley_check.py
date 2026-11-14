# Valley_check.py - verificacion de ValleyHeightVS / ValleyGradVS / ValleyPS SIN Unreal.
# Uso:  python Valley_check.py        (desde cualquier carpeta; no escribe nada en el repo)
#
# 1. Estatico: la lista de entradas de la CABECERA de cada .hlsl coincide con el codigo (toda entrada se usa),
#    sin bucles, sin arreglos, sin half; las dos VS tienen la misma lista; OutputType coincide con el return.
# 2. Compila un wrapper que imita la funcion que Unreal genera para un MaterialExpressionCustom:
#    dxc SM6 (-WX), fxc SM5 y glslc HLSL -> SPIR-V Vulkan 1.1 (-Werror) + spirv-val (el camino de la Quest).
#    Herramientas: Windows SDK (dxc/fxc) y Android NDK (glslc/spirv-val). Si falta alguna, se saltea.
#    fxc da X4000 ("potentially uninitialized variable") en ValleyPS: falso positivo de su analisis de flujo con
#    varios return; dxc y glslc compilan limpio con warnings como error. En Unreal no es error
#    (r.Shaders.WarningsAsErrors = 0 por defecto).
# 3. Traduce MECANICAMENTE los .hlsl a Python y reproduce los valores de control de la seccion 12 del plan
#    (docs/PLAN-VALLE-ENTERING-2026-09-27.md), mas controles cruzados (h igual en las dos VS, gradiente contra
#    diferencias finitas, h = 0 en la zona del usuario y del metaball, PerfMode, dither).
# 4. Si el plan esta en el repo: el codigo de cada archivo es IDENTICO al bloque de la seccion 7.2 (solo difiere
#    la cabecera de interfaz, entre las dos lineas de guiones).
import glob, math, os, re, subprocess, sys, tempfile
from pathlib import Path

import numpy as np

HL = Path(__file__).resolve().parent
ROOT = HL.parents[4]
PLAN = ROOT / "docs" / "PLAN-VALLE-ENTERING-2026-09-27.md"
RULE = "// " + "-" * 104
FILES = {"ValleyHeightVS": ("vs", "float3"), "ValleyGradVS": ("vs", "float4"), "ValleyPS": ("ps", "float3")}
fails = []


def chk(label, ok, info=""):
    print(("OK    " if ok else "FALLA ") + label + ("  " + info if info else ""))
    if not ok:
        fails.append(label)


# ============================ 1. estatico ============================
def parse(name):
    txt = (HL / (name + ".hlsl")).read_text(encoding="ascii").replace("\r\n", "\n")
    ins = re.findall(r"^//\s+(\d+)\s+(\w+)\s+(float[234]?)\s", txt, re.M)
    assert [int(i) for i, _, _ in ins] == list(range(1, len(ins) + 1)), name
    cmot = re.search(r"OutputType (CMOT_Float\d)", txt).group(1)
    body = "\n".join(l for l in txt.split("\n") if not l.lstrip().startswith("//"))
    return txt, [(n, t) for _, n, t in ins], cmot, body


PARSED = {n: parse(n) for n in FILES}
for name, (kind, ret) in FILES.items():
    txt, ins, cmot, body = PARSED[name]
    probs = ["entrada sin uso: " + n for n, _ in ins if not re.search(r"\b%s\b" % n, body)]
    if re.search(r"\b(for|while|do)\b", body): probs.append("bucle")
    if re.search(r"\w\s*\[", body): probs.append("arreglo")
    if re.search(r"\bhalf\b|\bmin16float\b", body): probs.append("media precision explicita")
    if kind == "vs" and "View.GameTime" not in body: probs.append("el VS no lee View.GameTime")
    if cmot != "CMOT_Float" + ret[-1]: probs.append("OutputType %s no coincide con %s" % (cmot, ret))
    chk("estatico %s (%d entradas, %s)" % (name, len(ins), cmot), not probs, "; ".join(probs))
chk("las dos VS tienen la misma lista de entradas", PARSED["ValleyHeightVS"][1] == PARSED["ValleyGradVS"][1])


# ============================ 2. compilacion ============================
def wrapper(name):
    kind, ret = FILES[name]
    _, ins, _, body = PARSED[name]
    cb = "\n".join("  %s cb_%s;" % (t, n) for n, t in ins)
    args = ["cb_" + n for n, _ in ins]
    if kind == "vs":
        args[0] = "inLP"
        entry = ("float4 main(float3 inLP : POSITION) : SV_Position\n{\n  FMaterialVertexParameters P; P.Dummy = inLP;\n"
                 "  %s o = CustomExpression0(P, %s);\n  return float4(inLP + o.xyz, 1.0 + %s);\n}\n"
                 % (ret, ", ".join(args), "o.w" if ret == "float4" else "0.0"))
        pstruct, ptype = "struct FMaterialVertexParameters { float3 Dummy; };", "FMaterialVertexParameters"
    else:
        vary = {"VI1": "TEXCOORD0", "LPi": "TEXCOORD1", "CamL": "TEXCOORD2", "Dist": "TEXCOORD3"}
        types = dict(ins)
        for i, (n, _) in enumerate(ins):
            if n in vary:
                args[i] = "in" + n
        sig = ", ".join("%s in%s : %s" % (types[n], n, s) for n, s in vary.items())
        entry = ("float4 main(float4 sv : SV_Position, %s) : SV_Target\n{\n  FMaterialPixelParameters P; P.SvPosition = sv;\n"
                 "  return float4(CustomExpression0(P, %s), 1.0);\n}\n" % (sig, ", ".join(args)))
        pstruct, ptype = "struct FMaterialPixelParameters { float4 SvPosition; };", "FMaterialPixelParameters"
    return ("struct FViewStub { float GameTime; };\ncbuffer ViewCB : register(b0) { FViewStub View; };\n"
            "cbuffer MatCB : register(b1)\n{\n%s\n};\n%s\n%s CustomExpression0(%s Parameters, %s)\n{\n%s\n}\n\n%s"
            % (cb, pstruct, ret, ptype, ", ".join("%s %s" % (t, n) for n, t in ins), body, entry))


def newest(pattern):
    c = sorted(glob.glob(pattern))
    return c[-1] if c else None


KITS = r"C:\Program Files (x86)\Windows Kits\10\bin\*\x64"
NDK = os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Android\Sdk\ndk\*\shader-tools\windows-x86_64")
DXC, FXC = newest(os.path.join(KITS, "dxc.exe")), newest(os.path.join(KITS, "fxc.exe"))
GLSLC, SPVVAL = newest(os.path.join(NDK, "glslc.exe")), newest(os.path.join(NDK, "spirv-val.exe"))


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr).strip()


tmp = Path(tempfile.mkdtemp(prefix="valley_check_"))
for name, (kind, _) in FILES.items():
    src = tmp / ("wrap_%s.hlsl" % name)
    src.write_text(wrapper(name), encoding="ascii")
    if DXC:
        rc, out = run([DXC, "-nologo", "-T", kind + "_6_0", "-E", "main", "-WX", "-O3", "-Fo", str(tmp / (name + ".dxil")), str(src)])
        chk("dxc %s_6_0 -WX  %s" % (kind, name), rc == 0, out[-300:] if rc else "")
    else:
        print("--    dxc no encontrado (Windows SDK)")
    if FXC:
        rc, out = run([FXC, "/nologo", "/T", kind + "_5_0", "/E", "main", "/O3", "/Fo", str(tmp / (name + ".dxbc")), str(src)])
        warns = sorted(set(re.findall(r"warning (X\d+)", out)))
        unknown = [w for w in warns if not (w == "X4000" and name == "ValleyPS")]
        chk("fxc %s_5_0      %s" % (kind, name), rc == 0 and not unknown,
            ("advertencias conocidas: %s" % warns) if warns and not unknown else (out[-300:] if rc or unknown else ""))
    else:
        print("--    fxc no encontrado (Windows SDK)")
    if GLSLC:
        spv = tmp / (name + ".spv")
        stage = "vert" if kind == "vs" else "frag"
        rc, out = run([GLSLC, "-x", "hlsl", "-fshader-stage=" + stage, "-fentry-point=main", "--target-env=vulkan1.1",
                       "-O", "-Werror", "-o", str(spv), str(src)])
        ok = rc == 0
        if ok and SPVVAL:
            rc2, out2 = run([SPVVAL, "--target-env", "vulkan1.1", str(spv)])
            ok, out = rc2 == 0, out2
        chk("glslc HLSL->SPIR-V + spirv-val  %s" % name, ok, out[-300:] if not ok else "")
    else:
        print("--    glslc no encontrado (Android NDK)")
print("      (wrappers en %s)" % tmp)


# ============================ 3. traduccion a Python y control numerico ============================
class Vec:
    __slots__ = ("a",)
    IDX = {"x": 0, "y": 1, "z": 2, "w": 3, "r": 0, "g": 1, "b": 2}

    def __init__(self, a): self.a = np.asarray(a, dtype=np.float64)

    def __getattr__(self, n):
        if n and all(c in Vec.IDX for c in n):
            v = [self.a[Vec.IDX[c]] for c in n]
            return float(v[0]) if len(v) == 1 else Vec(v)
        raise AttributeError(n)

    def _o(self, o): return o.a if isinstance(o, Vec) else o
    def __add__(s, o): return Vec(s.a + s._o(o))
    __radd__ = __add__
    def __sub__(s, o): return Vec(s.a - s._o(o))
    def __rsub__(s, o): return Vec(s._o(o) - s.a)
    def __mul__(s, o): return Vec(s.a * s._o(o))
    __rmul__ = __mul__
    def __truediv__(s, o): return Vec(s.a / s._o(o))
    def __rtruediv__(s, o): return Vec(s._o(o) / s.a)
    def __neg__(s): return Vec(-s.a)
    def __repr__(s): return np.array2string(s.a, precision=4)


def _u(x): return x.a if isinstance(x, Vec) else x
def _w(x): return Vec(x) if isinstance(x, np.ndarray) and x.ndim else float(x)
def _f1(fn): return lambda x: _w(fn(_u(x)))
def _f2(fn): return lambda x, y: _w(fn(_u(x), _u(y)))


def _mk(*args):
    out = []
    for a in args:
        out.extend(list(a.a) if isinstance(a, Vec) else [a])
    return Vec(out)


def _ss(a, b, x):
    t = np.clip((_u(x) - a) / (b - a), 0.0, 1.0)
    return _w(t * t * (3.0 - 2.0 * t))


ENV = dict(float2=_mk, float3=_mk, float4=_mk, sqrt=_f1(np.sqrt), sin=_f1(np.sin), cos=_f1(np.cos), exp=_f1(np.exp),
           floor=_f1(np.floor), abs=_f1(np.abs), radians=_f1(np.radians), frac=_f1(lambda x: x - np.floor(x)),
           rsqrt=_f1(lambda x: 1.0 / np.sqrt(x)), saturate=_f1(lambda x: np.clip(x, 0.0, 1.0)), pow=_f2(np.power),
           max=_f2(np.maximum), min=_f2(np.minimum), smoothstep=_ss,
           lerp=lambda a, b, t: _w(_u(a) + (_u(b) - _u(a)) * _u(t)),
           dot=lambda a, b: float(np.dot(a.a, b.a)), length=lambda a: float(np.linalg.norm(a.a)),
           normalize=lambda a: Vec(a.a / np.linalg.norm(a.a)))


def translate(name):
    txt, ins, _, _ = PARSED[name]
    py, ind, pend = [], 1, False
    ex = lambda e: e.replace("||", " or ").replace("&&", " and ")
    for raw in txt.split("\n"):
        l = raw.split("//")[0].strip()
        if not l:
            continue
        pad = "    " * ind
        if l == "{":
            assert pend, raw
            pend, ind = False, ind + 1
        elif l == "}":
            ind -= 1
        elif re.match(r"^if \((.*)\) \{ return (.*); \}$", l):
            m = re.match(r"^if \((.*)\) \{ return (.*); \}$", l)
            py += [pad + "if %s:" % ex(m.group(1)), pad + "    return (%s), dict(locals())" % ex(m.group(2))]
        elif re.match(r"^if \((.*)\)$", l):
            py.append(pad + "if %s:" % ex(re.match(r"^if \((.*)\)$", l).group(1)))
            pend = True
        elif re.match(r"^return (.*);$", l):
            py.append(pad + "return (%s), dict(locals())" % ex(re.match(r"^return (.*);$", l).group(1)))
        elif re.match(r"^sincos\((.*), (\w+), (\w+)\);$", l):
            m = re.match(r"^sincos\((.*), (\w+), (\w+)\);$", l)
            py.append(pad + "%s, %s = sin(%s), cos(%s)" % (m.group(2), m.group(3), m.group(1), m.group(1)))
        elif re.match(r"^float[234]? \w+(, \w+)+;$", l):
            pass
        elif re.match(r"^float[234]? (\w+) = (.*);$", l):
            m = re.match(r"^float[234]? (\w+) = (.*);$", l)
            py.append(pad + "%s = %s" % (m.group(1), ex(m.group(2))))
        elif re.match(r"^(\w+) ([\+\-\*/]?=) (.*);$", l):
            m = re.match(r"^(\w+) ([\+\-\*/]?=) (.*);$", l)
            py.append(pad + "%s %s %s" % (m.group(1), m.group(2), ex(m.group(3))))
        else:
            raise SyntaxError("%s: linea no traducida (ampliar el traductor): %s" % (name, raw))
    assert ind == 1, (name, "llaves desbalanceadas")
    ns = dict(ENV)
    exec(compile("def F(Parameters, View, %s):\n%s\n" % (", ".join(n for n, _ in ins), "\n".join(py)), name, "exec"), ns)
    return ns["F"], [n for n, _ in ins]


class O:
    def __init__(self, **k): self.__dict__.update(k)


HVS, VS_IN = translate("ValleyHeightVS")
GVS, _ = translate("ValleyGradVS")
PS, PS_IN = translate("ValleyPS")


def D(az, el):
    az, el = math.radians(az), math.radians(el)
    return Vec([math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)])


# defaults de la seccion 7.1 (DitherAmt 0 para los valores de control)
P = dict(Part=0.0, PerfMode=0.0, ValleyX=350.0, ValleyA=950.0, ValleyB=600.0, SeatIn=60.0, SeatOut=250.0,
         RimHeight=380.0, RimCrest=3.0, RimBack=4.0, DuneAmp=520.0, DuneRise=1.6, DuneLow=-0.35, DuneHigh=1.2,
         DuneScale=1.0, DuneSeed=0.0, DuneShiftX=0.0, DuneShiftY=0.0, MorphAmt=0.45, MorphSpeed=1.0,
         MorphNear=800.0, MorphFar=3000.0, Wrap=0.3, ShadeFloor=0.0, SlopeDark=1.2,
         ColLit=Vec([0.434, 0.527, 0.855]), ColShadow=Vec([0.061, 0.117, 0.352]), ColSheen=Vec([0.855, 0.761, 0.913]),
         Sheen=0.4, SheenPow=4.0, SheenBack=0.35, CrestLight=0.2, ShadowCenter=Vec([380.0, 0.0, 125.0]),
         ShadowRadius=85.0, ShadowStrength=1.5, ShadowSoft=0.8, ShadowTint=Vec([0.305, 0.352, 0.68]), ShadowMax=0.8,
         SkyZenith=Vec([0.216, 0.328, 0.597]), SkyHorizon=Vec([0.597, 0.624, 0.839]), SkyGlow=Vec([0.831, 0.68, 0.855]),
         SkyGradTop=0.7, GlowPow=2.0, GlowHeight=0.45, GlowAmt=0.8, MoonEdge=0.03, MoonColor=Vec([0.73, 0.644, 0.839]),
         MoonOpacity=0.55, MoonFill=0.2, MoonRim=1.0, FogStart=1000.0, FogDist=5000.0, FogMax=0.6, DitherAmt=0.0,
         LightDir=D(20, 25), GlowDir=D(20, 2), MoonDir=D(-40, 7), MoonCosR=math.cos(math.radians(9.0)))


def vs(fn, x, y, t, **over):
    q = dict(P, **over)
    q["LP"] = Vec([x, y, 0.0])
    return fn(O(), O(GameTime=t), **{n: q[n] for n in VS_IN})[0]


def ps(sv=(123.5, 456.5), **k):
    q = dict(P, **k)
    return PS(O(SvPosition=Vec([sv[0], sv[1], 0.5, 1.0])), O(GameTime=0.0), **{n: q[n] for n in PS_IN})


def srgb(c):
    c = np.clip(c, 0, 1)
    return tuple(int(v) for v in np.round(255 * np.where(c <= 0.0031308, 12.92 * c, 1.055 * np.power(c, 1 / 2.4) - 0.055)))


for lbl, v, ref in (("LightDir", P["LightDir"].a, [0.851651, 0.309976, 0.422618]),
                    ("GlowDir", P["GlowDir"].a, [0.939120, 0.341812, 0.034899]),
                    ("MoonDir", P["MoonDir"].a, [0.760334, -0.637996, 0.121869]), ("MoonCosR", P["MoonCosR"], 0.987688)):
    chk("preshader %s" % lbl, np.allclose(v, ref, atol=1e-6))

H = [((0, 0), 0, 0.000, 0.0, 0.0, 0.0), ((380, 0), 0, 0.000, 0.0, 0.0, 0.0),
     ((900, -700), 0, 89.005, 0.187877, -0.337869, 0.126090), ((1500, 800), 0, 280.513, -0.146126, -0.204076, 0.281756),
     ((2200, -1500), 20, 481.552, -0.912999, 0.638918, 0.250821), ((3200, 0), 45.5, 460.192, -0.050322, 0.369692, 0.154215),
     ((-1800, 1200), 90, 383.565, -0.033267, 0.083878, 0.007741), ((2600, 2600), 300, 0.000, 0.0, 0.0, 0.0)]
for (x, y), t, h, gx, gy, hf in H:
    g, hh = vs(GVS, x, y, t).a, vs(HVS, x, y, t).a
    ok = (abs(g[2] - h) <= 0.0015 and abs(hh[2] - h) <= 0.0015 and hh[0] == 0 and hh[1] == 0
          and max(abs(g[0] - gx), abs(g[1] - gy), abs(g[3] - hf)) <= 2e-6)
    chk("altura (%d, %d) t=%g" % (x, y, t), ok, "h=%.4f dh=(%.6f, %.6f) hf=%.6f" % (g[2], g[0], g[1], g[3]))

CAM = np.array([0.0, 0.0, 120.0])
for (x, y), t, lin, s8, o in [((380, 0), 0, (0.2136, 0.2636, 0.5562), (127, 140, 197), 0.4743),
                              ((250, -150), 0, (0.2869, 0.3542, 0.6358), (146, 161, 209), 0.0432),
                              ((1500, 800), 0, (0.5424, 0.5454, 0.7814), (194, 195, 229), 0.0),
                              ((3200, 0), 45.5, (0.5291, 0.5166, 0.7369), (192, 190, 223), 0.0),
                              ((-1800, 1200), 90, (0.4117, 0.4519, 0.7056), (172, 179, 219), 0.0)]:
    vi = vs(GVS, x, y, t)
    d = CAM - np.array([x, y, vi.a[2]])
    c, loc = ps(VI1=vi, LPi=Vec([x, y, 0.0]), CamL=Vec(d), Dist=float(np.linalg.norm(d)), Part=0.0)
    chk("suelo (%d, %d) t=%g" % (x, y, t), np.allclose(c.a, lin, atol=1e-3) and srgb(c.a) == s8 and abs(loc["O"] - o) <= 1e-4,
        "lin=%s sRGB=%s O=%.4f" % (c, srgb(c.a), loc["O"]))

for (az, el), lin, s8 in [((0, 0), (0.7595, 0.6629, 0.8501), (226, 213, 237)), ((0, 45), (0.2160, 0.3280, 0.5970), (128, 155, 203)),
                          ((20, 3), (0.7821, 0.6676, 0.8510), (229, 213, 238)), ((180, 10), (0.5383, 0.5784, 0.8017), (194, 200, 231)),
                          ((-40, 7), (0.6269, 0.6178, 0.8274), (207, 206, 235)), ((-33, 12), (0.6578, 0.6158, 0.8209), (212, 206, 234)),
                          ((0, 90), (0.2160, 0.3280, 0.5970), (128, 155, 203))]:
    c, _ = ps(VI1=Vec([0, 0, 0, 0]), LPi=Vec([0, 0, 0]), CamL=-D(az, el), Dist=20000.0, Part=1.0)
    chk("cielo az=%d el=%d" % (az, el), np.allclose(c.a, lin, atol=1e-3) and srgb(c.a) == s8, "lin=%s sRGB=%s" % (c, srgb(c.a)))

rng = np.random.default_rng(7)
eh = eg = 0.0
for _ in range(1000):
    x, y, t = rng.uniform(-4400, 4400), rng.uniform(-4400, 4400), rng.uniform(0, 900)
    g = vs(GVS, x, y, t).a
    eh = max(eh, abs(g[2] - vs(HVS, x, y, t).a[2]))
    fx = (vs(HVS, x + 0.01, y, t).a[2] - vs(HVS, x - 0.01, y, t).a[2]) / 0.02
    fy = (vs(HVS, x, y + 0.01, t).a[2] - vs(HVS, x, y - 0.01, t).a[2]) / 0.02
    eg = max(eg, abs(fx - g[0]), abs(fy - g[1]))
chk("h identica en las dos VS (1000 puntos)", eh < 1e-9, "max %.1e cm" % eh)
chk("gradiente analitico = diferencias finitas de ValleyHeightVS", eg < 1e-4, "max %.1e" % eg)
zmax = max(abs(vs(HVS, rng.uniform(0, 700), rng.uniform(-300, 300), rng.uniform(0, 900)).a[2]) for _ in range(2000))
chk("h = 0 en x 0-700, |y| <= 300 (2000 puntos, t al azar)", zmax == 0.0)
for pm in (1.0, 3.0):
    chk("VS PerfMode %d -> 0" % pm, not vs(HVS, 2200, -1500, 20, PerfMode=pm).a.any() and not vs(GVS, 2200, -1500, 20, PerfMode=pm).a.any())
chk("VS Part 1 (cielo) -> 0", not vs(HVS, 2200, -1500, 20, Part=1.0).a.any() and not vs(GVS, 2200, -1500, 20, Part=1.0).a.any())
vi = vs(GVS, 1500, 800, 0)
kw = dict(VI1=vi, LPi=Vec([1500, 800, 0]), CamL=Vec(CAM - [1500, 800, vi.a[2]]), Dist=1700.0)
chk("PS suelo PerfMode 2 -> ColLit", np.allclose(ps(PerfMode=2.0, Part=0.0, **kw)[0].a, P["ColLit"].a))
chk("PS cielo PerfMode 2 -> SkyHorizon", np.allclose(ps(PerfMode=2.0, Part=1.0, **kw)[0].a, P["SkyHorizon"].a))
dd = np.array([ps(sv=(rng.integers(0, 1680) + 0.5, rng.integers(0, 1760) + 0.5), DitherAmt=1.0, VI1=Vec([0, 0, 0, 0]),
                  LPi=Vec([0, 0, 0]), CamL=-D(0, 45), Dist=1.0, Part=1.0)[1]["dith"] for _ in range(3000)]) * 255
chk("dither DitherAmt 1 en [-0.5, 0.5] LSB, media ~0", dd.min() >= -0.5 and dd.max() <= 0.5 and abs(dd.mean()) < 0.03,
    "min %.3f max %.3f media %.4f" % (dd.min(), dd.max(), dd.mean()))


# ---- revision Quest (2026-09-27): terminos que los defaults no ejercitan, rotacion, banco y rama de niebla ----
def vsl(fn, x, y, t, **over):
    q = dict(P, **over)
    q["LP"] = Vec([x, y, 0.0])
    return fn(O(), O(GameTime=t), **{n: q[n] for n in VS_IN})


# Con los defaults el termino del asiento (envE * dseat) NUNCA actua: la rampa del asiento (60-250 cm) cae adentro
# del valle, donde envE = 0. Y DuneSeed/DuneShift valen 0. Estas perillas ponen el asiento, la transformacion y el
# anillo encimados, con el campo girado y corrido, para probar el gradiente termino por termino.
KN = dict(ValleyX=0.0, ValleyA=300.0, ValleyB=220.0, SeatIn=100.0, SeatOut=900.0, DuneSeed=37.0, DuneShiftX=123.0,
          DuneShiftY=-456.0, MorphNear=0.0, MorphFar=1500.0, MorphSpeed=2.3, DuneScale=0.7, DuneRise=2.2)
eg2 = eh2 = 0.0
seat_on = morph_on = 0
for _ in range(1500):
    x, y, t = rng.uniform(-1600, 1600), rng.uniform(-1600, 1600), rng.uniform(0, 900)
    g, loc = vsl(GVS, x, y, t, **KN)
    g = g.a
    seat_on += abs(loc["envE"] * loc["dseat"] * g[3]) > 0 or abs(loc["envE"] * loc["dseat"]) > 1e-6
    morph_on += abs(loc["dMt"] * loc["sm"]) > 1e-9
    eh2 = max(eh2, abs(g[2] - vs(HVS, x, y, t, **KN).a[2]))
    fx = (vs(HVS, x + 0.01, y, t, **KN).a[2] - vs(HVS, x - 0.01, y, t, **KN).a[2]) / 0.02
    fy = (vs(HVS, x, y + 0.01, t, **KN).a[2] - vs(HVS, x, y - 0.01, t, **KN).a[2]) / 0.02
    eg2 = max(eg2, abs(fx - g[0]), abs(fy - g[1]))
chk("gradiente con perillas NO default (asiento, transformacion, DuneSeed 37, corrimiento)",
    eg2 < 1e-4 and eh2 < 1e-9 and seat_on > 100 and morph_on > 100,
    "max %.1e  (h VS %.1e; puntos con termino de asiento %d, de transformacion %d)" % (eg2, eh2, seat_on, morph_on))

# Las direcciones salen de UN sincos de DuneSeed rotando las 4 constantes: tienen que ser cos/sin(DuneSeed + alfa).
er = 0.0
for seed in (0.0, 37.0, 90.0, 181.5, 359.0, -45.0):
    _, loc = vsl(GVS, 5000.0, 0.0, 0.0, DuneSeed=seed)
    ks = 2 * math.pi / P["DuneScale"]
    for i, (al, lam) in enumerate(((18, 3000), (101, 2200), (143, 1650), (232, 1250))):
        a = math.radians(seed + al)
        er = max(er, abs(loc["kx%d" % i] * lam / ks - math.cos(a)), abs(loc["ky%d" % i] * lam / ks - math.sin(a)))
chk("rotacion de las direcciones = cos/sin(DuneSeed + alfa), 6 semillas", er < 2e-8, "max %.1e" % er)

# Banco: PerfMode 2/3 tiene que salir ANTES de toda cuenta (si no, m1 - m3 no mide el pixel entero).
for part in (0.0, 1.0):
    for pm in (2.0, 3.0):
        _, loc = ps(PerfMode=pm, Part=part, **kw)
        chk("PS Part %d PerfMode %d sale antes de toda cuenta" % (part, pm), not ({"V", "sky", "fog", "gaz"} & set(loc)))

# Rama de niebla: el piso sin niebla no calcula el cielo; con niebla, si. Y el resultado es el mismo que sin la rama.
vi = vs(GVS, 380, 0, 0)
d = CAM - np.array([380.0, 0.0, vi.a[2]])
c_near, loc_near = ps(VI1=vi, LPi=Vec([380, 0, 0]), CamL=Vec(d), Dist=float(np.linalg.norm(d)), Part=0.0)
vi = vs(GVS, 1500, 800, 0)
d = CAM - np.array([1500.0, 800.0, vi.a[2]])
_, loc_far = ps(VI1=vi, LPi=Vec([1500, 800, 0]), CamL=Vec(d), Dist=float(np.linalg.norm(d)), Part=0.0)
chk("suelo a < FogStart no calcula el cielo; suelo lejano si",
    "gaz" not in loc_near and loc_near["fog"] == 0.0 and "gaz" in loc_far and loc_far["fog"] > 0.0)

# Trascendentes por evaluacion (texto, sin bucles: es el conteo real). Informativo; el presupuesto esta en el plan.
for name in FILES:
    b = PARSED[name][3]
    n = {k: len(re.findall(p, b)) for k, p in (("trig", r"\b(?:sin|cos)\("), ("sincos", r"\bsincos\("),
                                                ("sqrt/rsqrt/normalize/length", r"\b(?:r?sqrt|normalize|length)\("),
                                                ("pow", r"\bpow\("), ("exp", r"\bexp2?\("))}
    print("INFO  %-15s %s" % (name, "  ".join("%s=%d" % kv for kv in n.items())))

# ============================ 4. identico al plan ============================
if PLAN.exists():
    blocks = re.findall(r"```hlsl\n(.*?)```", PLAN.read_text(encoding="utf-8"), re.S)
    for b in blocks:
        name = b.split()[1]
        L = PARSED[name][0].rstrip("\n").split("\n")
        k = [i for i, l in enumerate(L) if l == RULE]
        chk("codigo de %s identico a la seccion 7.2 del plan" % name, len(k) == 2 and L[:k[0]] + L[k[1] + 1:] == b.rstrip("\n").split("\n"))
else:
    print("--    plan no encontrado: no se compara con la seccion 7.2")

print("\nRESULTADO: " + ("TODO OK" if not fails else "FALLAS: %s" % fails))
sys.exit(1 if fails else 0)
