# Valley_check.py - verificacion de ValleyHeightVS / ValleyGradVS / ValleyPS (v2, revision 2026-09-28) SIN Unreal.
# Uso:  python Valley_check.py        (desde cualquier carpeta; no escribe nada en el repo)
#
# 1. Estatico: la lista de entradas de la CABECERA de cada .hlsl coincide con el codigo (toda entrada se usa),
#    sin bucles, sin arreglos, sin half; la lista de ValleyHeightVS es el COMIENZO de la de ValleyGradVS (mismo
#    orden); OutputType coincide con el return; el default escrito en la cabecera de cada ScalarParameter es el de la
#    tabla 7.1 del plan (la cabecera viaja dentro del Custom: no puede decir otro numero).
# 2. Compila un wrapper que imita la funcion que Unreal genera para un MaterialExpressionCustom:
#    dxc SM6 (-WX), fxc SM5 y glslc HLSL -> SPIR-V Vulkan 1.1 (-Werror) + spirv-val (el camino de la Quest).
#    Herramientas: Windows SDK (dxc/fxc) y Android NDK (glslc/spirv-val). Si falta alguna, se saltea.
#    Verifica ademas que las ramas [branch] lleguen al SPIR-V como SelectionControl DontFlatten.
# 3. Traduce MECANICAMENTE los .hlsl a Python y:
#    a) reproduce los valores de control de la seccion 12 del plan (docs/PLAN-VALLE-ENTERING-2026-09-27.md);
#    b) los compara con el MODELO NUMPY de referencia (scripts/valley_model.py) en miles de puntos al azar,
#       con los defaults y con dos juegos de perillas no default (uno con HillEnd < HillFade);
#    c) controles cruzados: h identica en las dos VS; gradiente contra diferencias finitas (sin el termino de
#       sombreado del oleaje, que no es gradiente de h); piso = 0 exacto a <= 10 m del usuario y del metaball; la
#       geometria del oleaje vale 0 antes de SwellIn; continuidad de h donde la v2 tenia un acantilado; COTA RIGUROSA
#       de la velocidad vertical (oleaje + respiracion) <= 0,5 grados/s y BUSQUEDA del maximo (optimizacion local
#       desde los mejores candidatos, confirmada en el HLSL) por debajo de la cota; rotaciones; PerfMode; dither;
#       ramas (el piso cercano no calcula niebla, cielo ni sombra lejana);
#    d) CONTROL NEGATIVO automatico: copias mutadas de los .hlsl TIENEN que fallar; si no fallan, el verificador no
#       mide lo que dice.
# 4. Si el plan esta en el repo: el codigo de cada archivo es IDENTICO al bloque de la seccion 7.2 (solo difiere
#    la cabecera de interfaz, entre las dos lineas de guiones).
import glob, math, os, re, subprocess, sys, tempfile
from pathlib import Path

import numpy as np

HL = Path(__file__).resolve().parent
ROOT = HL.parents[4]
PLAN = ROOT / "docs" / "PLAN-VALLE-ENTERING-2026-09-27.md"
sys.path.insert(0, str(HL.parent))
import valley_model as vm  # noqa: E402

RULE = "// " + "-" * 104
FILES = {"ValleyHeightVS": ("vs", "float3"), "ValleyGradVS": ("vs", "float4"), "ValleyPS": ("ps", "float3")}
fails = []


def chk(label, ok, info=""):
    print(("OK    " if ok else "FALLA ") + label + ("  " + info if info else ""))
    if not ok:
        fails.append(label)


# ============================ 1. estatico ============================
def parse_text(txt, name):
    txt = txt.replace("\r\n", "\n")
    ins = re.findall(r"^//\s+(\d+)\s+(\w+)\s+(float[234]?)\s", txt, re.M)
    assert [int(i) for i, _, _ in ins] == list(range(1, len(ins) + 1)), name
    cmot = re.search(r"OutputType (CMOT_Float\d)", txt).group(1)
    body = "\n".join(l for l in txt.split("\n") if not l.lstrip().startswith("//"))
    return txt, [(n, t) for _, n, t in ins], cmot, body


def parse(name):
    return parse_text((HL / (name + ".hlsl")).read_text(encoding="ascii"), name)


PARSED = {n: parse(n) for n in FILES}
for name, (kind, ret) in FILES.items():
    txt, ins, cmot, body = PARSED[name]
    probs = ["entrada sin uso: " + n for n, _ in ins if not re.search(r"\b%s\b" % n, body)]
    if re.search(r"\b(for|while|do)\b", body): probs.append("bucle")
    if re.search(r"\w\s*\[", re.sub(r"\[(branch|flatten)\]", "", body)): probs.append("arreglo")
    if re.search(r"\bhalf\b|\bmin16float\b", body): probs.append("media precision explicita")
    if kind == "vs" and "View.GameTime" not in body: probs.append("el VS no lee View.GameTime")
    if cmot != "CMOT_Float" + ret[-1]: probs.append("OutputType %s no coincide con %s" % (cmot, ret))
    chk("estatico %s (%d entradas, %s)" % (name, len(ins), cmot), not probs, "; ".join(probs))
HIN, GIN = PARSED["ValleyHeightVS"][1], PARSED["ValleyGradVS"][1]
chk("la lista de ValleyHeightVS es el comienzo de la de ValleyGradVS (mismo orden)", GIN[:len(HIN)] == HIN,
    "Height %d, Grad %d; Grad agrega %s" % (len(HIN), len(GIN), [n for n, _ in GIN[len(HIN):]]))


def tabla_71():
    """Defaults escalares de la tabla 7.1 del plan (mismo parser que plan_valley_material.py)."""
    out = {}
    en = False
    for linea in PLAN.read_text(encoding="utf-8").split("\n"):
        if linea.startswith("### 7.1"):
            en = True
            continue
        if en and linea.startswith("### "):
            break
        if en and linea.startswith("| `"):
            cols = [c.strip() for c in linea.strip().strip("|").split("|")]
            if cols[2].startswith("escalar"):
                m = re.match(r"\s*([\u2212\-]?[\d.,]+)", cols[3])
                out[cols[1].strip("`")] = float(m.group(1).replace("\u2212", "-").replace(",", "."))
    return out


if PLAN.exists():
    T71 = tabla_71()
    malos = []
    for name in FILES:
        for m in re.finditer(r"^//\s+\d+\s+(\w+)\s+float\s+ScalarParameter (\w+)\s+([\-\d.]+)", PARSED[name][0], re.M):
            pn, val = m.group(2), float(m.group(3))
            if pn not in T71 or abs(T71[pn] - val) > 1e-9:
                malos.append("%s.%s cabecera %g, tabla %s" % (name, pn, val, T71.get(pn)))
    chk("defaults de las cabeceras = tabla 7.1 del plan (ScalarParameter)", not malos, "; ".join(malos))


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
SPVDIS = newest(os.path.join(NDK, "spirv-dis.exe"))


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
        if ok and SPVDIS:
            rc3, dis = run([SPVDIS, str(spv)])
            nb = len(re.findall(r"^\s*\[branch\]\s*$", PARSED[name][3], re.M))
            nd = len(re.findall(r"OpSelectionMerge %\w+ DontFlatten", dis))
            chk("[branch] -> SelectionControl DontFlatten en el SPIR-V  %s" % name, rc3 == 0 and nd >= nb,
                "%d [branch] en el codigo, %d DontFlatten en el SPIR-V" % (nb, nd))
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


def translate_text(txt, ins, name):
    py, ind, pend = [], 1, False
    ex = lambda e: e.replace("||", " or ").replace("&&", " and ")
    for raw in txt.split("\n"):
        l = raw.split("//")[0].strip()
        if not l or l in ("[branch]", "[flatten]"):
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


def translate(name):
    txt, ins, _, _ = PARSED[name]
    return translate_text(txt, ins, name)


class O:
    def __init__(self, **k): self.__dict__.update(k)


HVS, H_IN = translate("ValleyHeightVS")
GVS, G_IN = translate("ValleyGradVS")
PS, PS_IN = translate("ValleyPS")


def D(az, el):
    return Vec(vm.dir_d(az, el))


def base_params(**over):
    q = vm.params(**over)
    q["DitherAmt"] = over.get("DitherAmt", 0.0)
    for k in ("ColLit", "ColShadow", "ColSheen", "ShadowCenter", "ShadowTint", "SkyZenith", "SkyHorizon", "SkyGlow", "MoonColor"):
        q[k] = Vec(list(q[k]))
    q["LightDir"] = D(q["LightAz"], q["LightEl"])
    q["GlowDir"] = D(q["GlowAz"], q["GlowEl"])
    q["MoonDir"] = D(q["MoonAz"], q["MoonEl"])
    q["MoonCosR"] = math.cos(math.radians(q["MoonRadius"]))
    return q


P = base_params()


def vsl(fn, x, y, t, q=None):
    q = P if q is None else q
    q = dict(q)
    q["LP"] = Vec([x, y, 0.0])
    ins = H_IN if fn is HVS or getattr(fn, "_height", False) else G_IN
    return fn(O(), O(GameTime=t), **{n: q[n] for n in ins})


def vs(fn, x, y, t, q=None):
    return vsl(fn, x, y, t, q)[0]


def ps(sv=(123.5, 456.5), q=None, fn=None, **k):
    q = dict(P if q is None else q)
    q.update(k)
    return (fn or PS)(O(SvPosition=Vec([sv[0], sv[1], 0.5, 1.0])), O(GameTime=0.0), **{n: q[n] for n in PS_IN})


def model_params(q):
    """dict del modelo a partir del dict del check (vuelve los Vec a tuplas)."""
    return {k: (tuple(v.a) if isinstance(v, Vec) else v) for k, v in q.items()}


for lbl, v, ref in (("LightDir", P["LightDir"].a, [0.851651, 0.309976, 0.422618]),
                    ("GlowDir", P["GlowDir"].a, [0.939120, 0.341812, 0.034899]),
                    ("MoonDir", P["MoonDir"].a, [0.760334, -0.637996, 0.121869]), ("MoonCosR", P["MoonCosR"], 0.987688)):
    chk("preshader %s" % lbl, np.allclose(v, ref, atol=1e-6))

# ---- a) seccion 12: altura y gradiente (x, y), t, h, dh/dx, dh/dy, hf
H = [((0, 0), 0, 0.000, 0.0, 0.0, 0.0),
     ((380, 0), 0, 0.000, 0.0, 0.0, 0.0),
     ((1300, -700), 30, 0.000, 0.0, 0.0, 0.0),
     ((3000, 1200), 0, 0.000, 0.025176, 0.048426, 0.000000),
     ((6000, -2500), 20, 4.966, 0.089937, -0.151754, 0.002257),
     ((-9000, 6000), 45.5, 374.301, -0.345389, 0.087435, 0.170137),
     ((15000, 5000), 90, 497.366, 0.099869, -0.040502, 0.226075),
     ((21000, -12000), 120, 0.000, 0.033414, 0.085065, 0.000000),
     ((26400, 23800), 120, -124.940, 0.030688, 0.014694, 0.007105),
     ((-30000, -20000), 300, 2001.182, -0.201757, -0.451845, 0.177124),
     ((46000, 9000), 600, 3524.110, -0.008876, -0.579483, 0.324981),
     ((0, 56000), 30, 786.380, -0.004620, -0.654901, 0.100584),
     ((60000, 10000), 0, 0.000, 0.0, 0.0, 0.0)]
for (x, y), t, h, gx, gy, hf in H:
    g, hh = vs(GVS, x, y, t).a, vs(HVS, x, y, t).a
    ok = (abs(g[2] - h) <= 0.0015 and abs(hh[2] - h) <= 0.0015 and hh[0] == 0 and hh[1] == 0
          and max(abs(g[0] - gx), abs(g[1] - gy), abs(g[3] - hf)) <= 2e-6)
    chk("altura (%d, %d) t=%g" % (x, y, t), ok, "h=%.4f dh=(%.6f, %.6f) hf=%.6f" % (g[2], g[0], g[1], g[3]))

CAM = np.array([0.0, 0.0, 120.0])


def ps_suelo(x, y, t, q=None, fn=None, gfn=None):
    q = P if q is None else q
    vi = vs(gfn or GVS, x, y, t, q)
    d = CAM - np.array([x, y, vi.a[2]])
    return ps(q=q, fn=fn, VI1=vi, LPi=Vec([x, y, 0.0]), CamL=Vec(d), Dist=float(np.linalg.norm(d)), Part=0.0)


for (x, y), t, lin, s8, o in [((380, 0), 0, (0.2157, 0.2651, 0.5575), (128, 141, 197), 0.4743),
                              ((250, -150), 0, (0.2698, 0.3420, 0.6275), (142, 158, 208), 0.0432),
                              ((3000, 1200), 0, (0.4296, 0.4542, 0.7010), (175, 180, 218), 0.0),
                              ((-9000, 6000), 45.5, (0.4044, 0.4663, 0.7386), (170, 182, 223), 0.0),
                              ((15000, 5000), 90, (0.5085, 0.4959, 0.7275), (189, 187, 222), 0.0),
                              ((46000, 9000), 600, (0.6155, 0.5655, 0.7810), (206, 198, 229), 0.0)]:
    c, loc = ps_suelo(x, y, t)
    chk("suelo (%d, %d) t=%g" % (x, y, t), np.allclose(c.a, lin, atol=1e-3) and vm.srgb8(c.a) == s8 and abs(loc.get("O", 0.0) - o) <= 1e-4,
        "lin=%s sRGB=%s O=%.4f fog=%.4f" % (c, vm.srgb8(c.a), loc.get("O", 0.0), loc["fog"]))

for (az, el), lin, s8 in [((0, 0), (0.7595, 0.6629, 0.8501), (226, 213, 237)), ((0, 45), (0.2160, 0.3280, 0.5970), (128, 155, 203)),
                          ((20, 3), (0.7821, 0.6676, 0.8510), (229, 213, 238)), ((180, 10), (0.5383, 0.5784, 0.8017), (194, 200, 231)),
                          ((-40, 7), (0.6269, 0.6178, 0.8274), (207, 206, 235)), ((-33, 12), (0.6578, 0.6158, 0.8209), (212, 206, 234)),
                          ((0, 90), (0.2160, 0.3280, 0.5970), (128, 155, 203))]:
    c, _ = ps(VI1=Vec([0, 0, 0, 0]), LPi=Vec([0, 0, 0]), CamL=-D(az, el), Dist=100000.0, Part=1.0)
    chk("cielo az=%d el=%d" % (az, el), np.allclose(c.a, lin, atol=1e-3) and vm.srgb8(c.a) == s8, "lin=%s sRGB=%s" % (c, vm.srgb8(c.a)))

# ---- b) HLSL traducido contra el MODELO NUMPY (valley_model.py), defaults y perillas NO default
rng = np.random.default_rng(7)
# perillas que ponen las tres capas encimadas, con semillas y escalas distintas, para ejercitar cada termino
KN = base_params(HillNear=2000.0, HillFull=9000.0, HillFade=12000.0, HillEnd=30000.0, HillSeed=17.0, HillScale=5.0,
                 FarIn=8000.0, FarFull=20000.0, FarCrest=26000.0, FarBack=31000.0, FarSeed=-40.0, FarScale=9.0,
                 SwellNear=500.0, SwellIn=3000.0, SwellFar=6000.0, SwellSeed=33.0, SwellScale=1.3, SwellSpeed=1.7,
                 SwellShade=700.0, SwellShadeFull=2500.0, MorphAmt=0.4, MorphSpeed=2.3, DuneLow=-0.1, DuneHigh=0.9)
# rampas invertidas (la v2 tenia un acantilado con HillEnd < HillFade) y SwellIn < SwellNear (manda SwellNear)
KN2 = base_params(HillFade=19000.0, HillEnd=18000.0, SwellIn=900.0, SwellNear=1500.0, SwellShadeFull=1000.0,
                  FarCrest=27000.0, FarBack=26000.0)


def compara_vs(q, n, rmax, hvs=HVS, gvs=GVS):
    qm = model_params(q)
    eh = eg = ehh = 0.0
    for _ in range(n):
        r, a, t = rmax * math.sqrt(rng.uniform()), rng.uniform(-math.pi, math.pi), rng.uniform(0, 1800)
        x, y = r * math.cos(a), r * math.sin(a)
        g, hh = vs(gvs, x, y, t, q).a, vs(hvs, x, y, t, q).a
        mx, my, mh, mf = (float(v[0]) for v in vm.valley_grad(np.array([x]), np.array([y]), t, qm))
        eh = max(eh, abs(g[2] - mh), abs(hh[2] - mh))
        eg = max(eg, abs(g[0] - mx), abs(g[1] - my), abs(g[3] - mf))
        ehh = max(ehh, abs(g[2] - hh[2]))
    return eh, eg, ehh


eh, eg, ehh = compara_vs(P, 3000, 64000.0)
# tolerancias: el HLSL escribe las direcciones con constantes de 8 cifras y el modelo las calcula; la diferencia es
# ~3e-4 cm en h a 640 m (y ~1e-7 en pendiente): por debajo de la tolerancia de la seccion 12
chk("VS traducido = modelo numpy, defaults (3000 puntos hasta 640 m, t hasta 1800 s)", eh < 2e-3 and eg < 2e-6 and ehh < 1e-9,
    "|h| %.1e cm  |grad,hf| %.1e  |h Height - h Grad| %.1e" % (eh, eg, ehh))
eh2, eg2, ehh2 = compara_vs(KN, 2000, 32000.0)
chk("VS traducido = modelo numpy, perillas NO default (capas encimadas, semillas, escalas)", eh2 < 2e-3 and eg2 < 2e-6 and ehh2 < 1e-9,
    "|h| %.1e cm  |grad,hf| %.1e  |h Height - h Grad| %.1e" % (eh2, eg2, ehh2))
eh3, eg3, ehh3 = compara_vs(KN2, 2000, 30000.0)
chk("VS traducido = modelo numpy, rampas invertidas (HillEnd < HillFade, FarBack < FarCrest, SwellIn < SwellNear)",
    eh3 < 2e-3 and eg3 < 2e-6 and ehh3 < 1e-9, "|h| %.1e cm  |grad,hf| %.1e  |h Height - h Grad| %.1e" % (eh3, eg3, ehh3))
# el caso concreto de la revision: HillEnd 18000 < HillFade 19000, az 0,3, t 0: h continua en r = 18000
qc = base_params(HillEnd=18000.0)
hs = [vs(HVS, r * math.cos(0.3), r * math.sin(0.3), 0.0, qc).a[2] for r in (17999.0, 18001.0)]
chk("sin acantilado con HillEnd < HillFade (h a 17.999 y 18.001 cm, az 0,3)", abs(hs[1] - hs[0]) < 1.0,
    "h = %.1f / %.1f cm" % tuple(hs))


def compara_ps(q, n, fn=None):
    qm = model_params(q)
    ec = 0.0
    for _ in range(n):
        r, a, t = 64000.0 * rng.uniform() ** 2, rng.uniform(-math.pi, math.pi), rng.uniform(0, 900)
        x, y = r * math.cos(a), r * math.sin(a)
        c, _ = ps_suelo(x, y, t, q, fn)
        gx, gy, h, hf = vm.valley_grad(np.array([x]), np.array([y]), t, qm)
        cm = vm.suelo(np.array([x]), np.array([y]), gx, gy, h, hf, CAM, qm)[0]
        ec = max(ec, float(np.abs(c.a - cm).max()))
    for _ in range(n // 3):
        r, a = 1500.0 * rng.uniform() ** 0.5, rng.uniform(-math.pi, math.pi)   # alrededor del metaball (sombra)
        x, y = 380.0 + r * math.cos(a), r * math.sin(a)
        c, _ = ps_suelo(x, y, 0.0, q, fn)
        gx, gy, h, hf = vm.valley_grad(np.array([x]), np.array([y]), 0.0, qm)
        cm = vm.suelo(np.array([x]), np.array([y]), gx, gy, h, hf, CAM, qm)[0]
        ec = max(ec, float(np.abs(c.a - cm).max()))
    for _ in range(n // 3):
        az, el = rng.uniform(-180, 180), rng.uniform(-5, 90)
        c, _ = ps(q=q, fn=fn, VI1=Vec([0, 0, 0, 0]), LPi=Vec([0, 0, 0]), CamL=-D(az, el), Dist=100000.0, Part=1.0)
        cm = vm.cielo(vm.dir_d(az, el)[None, :], qm)[0]
        ec = max(ec, float(np.abs(c.a - cm).max()))
    return ec


ec = compara_ps(P, 900)
chk("PS traducido = modelo numpy (900 puntos de suelo, 300 junto al metaball y 300 de cielo)", ec < 1e-6, "|color| %.1e" % ec)

# ---- c) controles cruzados
# gradiente exacto: sin el termino de sombreado del oleaje (SwellShade 0) el gradiente es el de h
eg = 0.0
for q, rmax in ((base_params(SwellShade=0.0), 64000.0), (base_params(**{**model_params(KN), "SwellShade": 0.0}), 32000.0)):
    for _ in range(1500):
        r, a, t = rmax * math.sqrt(rng.uniform()), rng.uniform(-math.pi, math.pi), rng.uniform(0, 900)
        x, y = r * math.cos(a), r * math.sin(a)
        g = vs(GVS, x, y, t, q).a
        fx = (vs(HVS, x + 0.01, y, t, q).a[2] - vs(HVS, x - 0.01, y, t, q).a[2]) / 0.02
        fy = (vs(HVS, x, y + 0.01, t, q).a[2] - vs(HVS, x, y - 0.01, t, q).a[2]) / 0.02
        eg = max(eg, abs(fx - g[0]), abs(fy - g[1]))
chk("gradiente analitico = diferencias finitas de ValleyHeightVS con SwellShade 0 (defaults y perillas no default)", eg < 2e-5, "max %.1e" % eg)
# el termino de sombreado es EXACTAMENTE back * Av * grad(s) (modelo con y sin sombreado)
es = 0.0
for _ in range(1500):
    r, a, t = 64000.0 * math.sqrt(rng.uniform()), rng.uniform(-math.pi, math.pi), rng.uniform(0, 900)
    x, y = np.array([r * math.cos(a)]), np.array([r * math.sin(a)])
    g1 = vm.valley_grad(x, y, t)
    g0 = vm.valley_grad(x, y, t, sombreado=False)
    s, sx, sy, _ = vm._oleaje(x, y, t, vm.P)
    wv, _ = vm.s5(vm.P["SwellNear"], vm.P["SwellShadeFull"], r)
    tb, _ = vm.s5(vm.P["FarCrest"], vm.P["FarBack"], r)
    es = max(es, float(np.max(np.abs(g1[0] - g0[0] - (1 - tb) * vm.P["SwellShade"] * wv * sx))),
             float(np.max(np.abs(g1[1] - g0[1] - (1 - tb) * vm.P["SwellShade"] * wv * sy))),
             float(np.max(np.abs(g1[2] - g0[2]))), float(np.max(np.abs(g1[3] - g0[3]))))
chk("sombreado del oleaje = back * Av * grad(s) y no toca h ni hf (modelo, 1500 puntos)", es < 1e-12, "max %.1e" % es)

zmax = 0.0
for _ in range(3000):
    c = (0.0, 0.0) if rng.uniform() < 0.5 else (380.0, 0.0)
    rr, aa = 1000.0 * math.sqrt(rng.uniform()), rng.uniform(-math.pi, math.pi)
    g = vs(GVS, c[0] + rr * math.cos(aa), c[1] + rr * math.sin(aa), rng.uniform(0, 3600)).a
    zmax = max(zmax, abs(g[2]), abs(g[0]), abs(g[1]))
chk("piso = 0 exacto (h y gradiente) a <= 10 m del usuario y del metaball (3000 puntos, t hasta 1 h)", zmax == 0.0, "max %.1e" % zmax)

qg = base_params(HillAmp=0.0, FarBase=0.0, FarAmp=0.0)
hmax = max(abs(vs(HVS, r * math.cos(a), r * math.sin(a), t, qg).a[2]) for r, a, t in
           zip(rng.uniform(0.0, 28000.0, 2000), rng.uniform(-math.pi, math.pi, 2000), rng.uniform(0, 3600, 2000)))
chk("la geometria del oleaje vale 0 exacto antes de SwellIn (280 m): el llano no se mueve (2000 puntos)", hmax == 0.0, "max %.1e cm" % hmax)

# velocidad vertical: COTA RIGUROSA (oleaje + respiracion, cada termino en su peor fase) y BUSQUEDA del maximo
cota, rcota, c_ole, c_res = vm.cota_vel_vertical_deg(model_params(P), partes=True)
chk("cota rigurosa de la velocidad vertical (oleaje + respiracion) <= 0,5 grados/s", cota <= 0.5,
    "%.3f grados/s en r = %.0f m (maximo del oleaje %.3f, de la respiracion %.3f)" % (cota, rcota / 100.0, c_ole, c_res))


def vel_modelo(x, y, t):
    """grados/s de la velocidad vertical (dh/dt analitica del modelo, t escalar)."""
    r = np.hypot(x, y)
    return np.degrees(np.abs(vm.valley_grad(x, y, float(t), con_dt=True)[4]) / np.maximum(r, 1.0))


# 200.000 muestras al azar (400 instantes x 500 puntos, en area x tiempo) y optimizacion local (Nelder-Mead en
# (r, az, t)) desde las 12 mejores
rr = rng.uniform(1500.0, 64000.0, (400, 500))
aa = rng.uniform(-math.pi, math.pi, (400, 500))
tt = np.repeat(rng.uniform(0.0, 3600.0, (400, 1)), 500, axis=1)
vv = np.concatenate([vel_modelo(rr[i] * np.cos(aa[i]), rr[i] * np.sin(aa[i]), tt[i, 0]) for i in range(400)])
rr, aa, tt = rr.ravel(), aa.ravel(), tt.ravel()
mejores = np.argsort(vv)[-12:]
vbest, pbest = float(vv.max()), None


def menos_v(p):
    return -float(vel_modelo(np.array([p[0] * math.cos(p[1])]), np.array([p[0] * math.sin(p[1])]), p[2])[0])


for i in mejores:
    p = np.array([rr[i], aa[i], tt[i]])
    simplex = np.array([p, p + [300.0, 0, 0], p + [0, 0.01, 0], p + [0, 0, 1.0]])
    fs = np.array([menos_v(s) for s in simplex])
    for _ in range(200):                                  # Nelder-Mead minimo (sin scipy)
        o = np.argsort(fs); simplex, fs = simplex[o], fs[o]
        c = simplex[:-1].mean(0)
        xr = c + (c - simplex[-1]); fr = menos_v(xr)
        if fr < fs[0]:
            xe = c + 2 * (c - simplex[-1]); fe = menos_v(xe)
            simplex[-1], fs[-1] = (xe, fe) if fe < fr else (xr, fr)
        elif fr < fs[-2]:
            simplex[-1], fs[-1] = xr, fr
        else:
            xc = c + 0.5 * (simplex[-1] - c); fc = menos_v(xc)
            if fc < fs[-1]:
                simplex[-1], fs[-1] = xc, fc
            else:
                simplex[1:] = simplex[0] + 0.5 * (simplex[1:] - simplex[0]); fs[1:] = [menos_v(s) for s in simplex[1:]]
    if -fs.min() > vbest:
        vbest, pbest = -float(fs.min()), simplex[np.argmin(fs)]
if pbest is None:
    i = int(np.argmax(vv)); pbest = np.array([rr[i], aa[i], tt[i]])
xb, yb, tb_ = pbest[0] * math.cos(pbest[1]), pbest[0] * math.sin(pbest[1]), pbest[2]
dh = (vs(HVS, xb, yb, tb_ + 0.001).a[2] - vs(HVS, xb, yb, tb_ - 0.001).a[2]) / 0.002
vh = math.degrees(abs(dh) / pbest[0])
chk("velocidad vertical: el maximo BUSCADO (200.000 muestras + optimizacion local, confirmado en el HLSL) <= cota",
    vbest <= cota + 1e-6 and abs(vh - vbest) < 2e-3 and vh <= 0.5,
    "maximo buscado %.3f grados/s en r = %.0f m, t = %.1f s (HLSL %.3f); cota %.3f" % (vbest, pbest[0] / 100.0, tb_, vh, cota))

for pm in (1.0, 3.0):
    chk("VS PerfMode %d -> 0" % pm, not vs(HVS, 15000, 5000, 20, base_params(PerfMode=pm)).a.any()
        and not vs(GVS, 15000, 5000, 20, base_params(PerfMode=pm)).a.any())
chk("VS Part 1 (cielo) -> 0", not vs(HVS, 15000, 5000, 20, base_params(Part=1.0)).a.any()
    and not vs(GVS, 15000, 5000, 20, base_params(Part=1.0)).a.any())
vi = vs(GVS, 15000, 5000, 0)
kw = dict(VI1=vi, LPi=Vec([15000, 5000, 0]), CamL=Vec(CAM - [15000, 5000, vi.a[2]]), Dist=15800.0)
chk("PS suelo PerfMode 2 -> ColLit", np.allclose(ps(PerfMode=2.0, Part=0.0, **kw)[0].a, P["ColLit"].a))
chk("PS cielo PerfMode 2 -> SkyHorizon", np.allclose(ps(PerfMode=2.0, Part=1.0, **kw)[0].a, P["SkyHorizon"].a))
dd = np.array([ps(sv=(rng.integers(0, 1680) + 0.5, rng.integers(0, 1760) + 0.5), DitherAmt=1.5, VI1=Vec([0, 0, 0, 0]),
                  LPi=Vec([0, 0, 0]), CamL=-D(0, 45), Dist=1.0, Part=1.0)[1]["dith"] for _ in range(3000)]) * 255
chk("dither DitherAmt 1,5 en [-0,75, 0,75] LSB, media ~0", dd.min() >= -0.75 and dd.max() <= 0.75 and abs(dd.mean()) < 0.05,
    "min %.3f max %.3f media %.4f" % (dd.min(), dd.max(), dd.mean()))

# rotaciones: las direcciones salen de UN sincos de la semilla rotando las constantes de cada capa
er = 0.0
for seed in (0.0, 37.0, 90.0, 181.5, 359.0, -45.0):
    q = base_params(HillSeed=seed, FarSeed=seed, SwellSeed=seed, HillNear=100.0, HillFull=200.0, FarIn=300.0,
                    FarFull=400.0, FarCrest=500.0, FarBack=90000.0, HillEnd=90000.0)
    _, loc = vsl(GVS, 50000.0, 3000.0, 0.0, q)
    kh = 2 * math.pi / q["HillScale"]
    kf = 2 * math.pi / q["FarScale"]
    for i, (al, lam, _, _, _, _) in enumerate(vm.DUNAS):
        a = math.radians(seed + al)
        er = max(er, abs(loc["ax%d" % i] * lam / kh - math.cos(a)), abs(loc["ay%d" % i] * lam / kh - math.sin(a)),
                 abs(loc["bx%d" % i] * lam / kf - math.cos(a)), abs(loc["by%d" % i] * lam / kf - math.sin(a)))
    for j, (al, _, _, _, _) in enumerate(vm.OLAS):
        a = math.radians(seed + al)
        er = max(er, abs(loc["d%dx" % j] - math.cos(a)), abs(loc["d%dy" % j] - math.sin(a)))
chk("rotacion de las direcciones = cos/sin(semilla + alfa) en las tres capas, 6 semillas", er < 2e-8, "max %.1e" % er)

# Banco: PerfMode 2/3 tiene que salir ANTES de toda cuenta (si no, m0 - m2 no mide el pixel entero).
for part in (0.0, 1.0):
    for pm in (2.0, 3.0):
        _, loc = ps(PerfMode=pm, Part=part, **kw)
        chk("PS Part %d PerfMode %d sale antes de toda cuenta" % (part, pm), not ({"V", "sky", "fog", "gaz"} & set(loc)))

# Ramas del PS: el piso a menos de FogStart no calcula ni la niebla ni el cielo; el suelo lejano, si. La sombra
# solo cerca del metaball.
_, loc_near = ps_suelo(380, 0, 0)
_, loc_far = ps_suelo(15000, 5000, 0)
chk("suelo a < FogStart no calcula ni la niebla ni el cielo; suelo lejano si",
    "gaz" not in loc_near and "e0" not in loc_near and loc_near["fog"] == 0.0 and "gaz" in loc_far and loc_far["fog"] > 0.0)
chk("la sombra del metaball se calcula cerca de el y no en el suelo lejano", "O" in loc_near and "O" not in loc_far)
# Ramas del VS: fuera de su banda cada capa no se evalua (costo) y el resultado igual coincide con el modelo (arriba)
_, l1 = vsl(GVS, 1000.0, 0.0, 0.0)
_, l2 = vsl(GVS, 3000.0, 0.0, 0.0)
_, l3 = vsl(GVS, 30000.0, 0.0, 0.0)
_, h2 = vsl(HVS, 3000.0, 0.0, 0.0)
_, h3 = vsl(HVS, 20000.0, 0.0, 0.0)
_, h4 = vsl(HVS, 30000.0, 0.0, 0.0)
chk("ramas del VS: a 10 m nada; a 30 m Grad solo el oleaje (sombreado) y Height nada; a 200 m Height solo colinas; "
    "a 300 m lejos + oleaje en las dos",
    not ({"sig", "sgF", "s"} & set(l1)) and "s" in l2 and not ({"sig", "sgF"} & set(l2))
    and {"sgF", "s"} <= set(l3) and "sig" not in l3 and not ({"sig", "sgF", "o0"} & set(h2))
    and "sig" in h3 and not ({"sgF", "o0"} & set(h3)) and {"sgF", "o0"} <= set(h4))

# ---- d) CONTROL NEGATIVO: copias mutadas TIENEN que fallar
MUT = [("ValleyHeightVS", "0.85 * sin(o1)", "0.86 * sin(o1)", "peso de una ola solo en Height", P),
       ("ValleyGradVS", "float dee = 30.0 * te", "float dee = 29.0 * te", "derivada de la envolvente lejana", P),
       ("ValleyGradVS", "+ 0.37 - frac(SwellSpeed * Tt / 36.0)), z1, k1);", "+ 0.38 - frac(SwellSpeed * Tt / 36.0)), z1, k1);", "fase de una ola solo en Grad", P),
       ("ValleyGradVS", "gx += (A + Av) * sx;", "gx += A * sx;", "el sombreado del oleaje", P),
       ("ValleyHeightVS", "if (r > HillNear && r < HE)", "if (r > HillNear && r < HillEnd)", "el acantilado de HillEnd < HillFade", KN2),
       ("ValleyPS", "Fh / max(HFogDist, 1.0)", "Fh / max(HFogDist * 1.01, 1.0)", "niebla de altura", P),
       ("ValleyPS", "* (1.0 - fog)));", "));", "el sheen ya no se apaga con la niebla", P),
       ("ValleyPS", "if (d2 < 144.0 * ws * ws)", "if (d2 < 4.0 * ws * ws)", "la rama de la sombra corta demasiado cerca", P)]
for name, a, b, lbl, qmut in MUT:
    txt, ins, _, _ = PARSED[name]
    assert a in txt, (name, a)
    fn, _ = translate_text(txt.replace(a, b, 1), ins, name + "_mut")
    if name == "ValleyPS":
        detect = compara_ps(qmut, 300, fn=fn) > 1e-4
    else:
        fn._height = name == "ValleyHeightVS"
        hv, gv = (fn, GVS) if name == "ValleyHeightVS" else (HVS, fn)
        e1, e2, e3 = compara_vs(qmut, 400, 64000.0 if qmut is P else 30000.0, hvs=hv, gvs=gv)
        detect = e1 > 1e-3 or e2 > 1e-6 or e3 > 1e-3
    chk("control negativo detectado: %s (%s)" % (lbl, name), detect)

# Trascendentes por evaluacion (texto, sin bucles: es el conteo real). Informativo; el presupuesto esta en el plan.
for name in FILES:
    b = PARSED[name][3]
    n = {k: len(re.findall(p, b)) for k, p in (("trig", r"\b(?:sin|cos)\("), ("sincos", r"\bsincos\("),
                                                ("sqrt/rsqrt/normalize/length", r"\b(?:r?sqrt|normalize|length)\("),
                                                ("pow", r"\bpow\("), ("exp", r"\bexp2?\("), ("if", r"\bif \("))}
    print("INFO  %-15s %s" % (name, "  ".join("%s=%d" % kv for kv in n.items())))

# ============================ 3e. CAPA VIVA (2026-09-28) ============================
# La respiracion llega por PRESHADER (Mul / Mix / Tint de uniformes) a 9 entradas de ValleyPS (rev. 2: ShadowRadius y
# GlowHeight ya NO respiran). Reglas que se verifican:
#   - ninguna entrada de los VS viene de la capa viva (la geometria NO respira: confort, plan del valle 14.3);
#   - neutro (Live* = 1 / 0): los valores efectivos y el color del PS son IDENTICOS bit a bit a la v2;
#   - con Live* al azar: el PS con los efectivos = el modelo (suelo y cielo) con efectivos();
#   - el plan de armado (valley_build.json) solo cambia esas 9 fuentes respecto del respaldo de la v2 aplicada.
PSRC = dict(PARSED["ValleyPS"][1])
LIVE_SRC = {}
for line in PARSED["ValleyPS"][0].split("\n"):
    m = re.match(r"^//\s+\d+\s+(\w+)\s+float[234]?\s+preshader (Mul|Mix|Tint)\((\w+), (\w+)(?:, (\w+))?\)", line)
    if m:
        LIVE_SRC[m.group(1)] = (m.group(2), m.group(3), m.group(4), m.group(5))
vs_vivas = [l for n in ("ValleyHeightVS", "ValleyGradVS") for l in PARSED[n][0].split("\n")
            if "preshader Mul" in l or "preshader Mix" in l or "preshader Tint" in l]
chk("capa viva: 9 entradas del PS por preshader Mul/Mix/Tint, NINGUNA en los VS (la geometria no respira)",
    len(LIVE_SRC) == 9 and not vs_vivas and all(k == a for k, (_, a, _, _) in LIVE_SRC.items()),
    "%s" % sorted(LIVE_SRC))
chk("capa viva: las fuentes del HLSL = las del modelo (LIVE_MUL / LIVE_MIX / LIVE_TINT); ShadowRadius y GlowHeight fuera",
    {(a, b) for a, (k, _, b, t) in LIVE_SRC.items() if k == "Mul"} == set(vm.LIVE_MUL)
    and {(a, b, t) for a, (k, _, b, t) in LIVE_SRC.items() if k == "Mix"} == set(vm.LIVE_MIX)
    and {(a, b, t) for a, (k, _, b, t) in LIVE_SRC.items() if k == "Tint"} == set(vm.LIVE_TINT)
    and "ShadowRadius" not in LIVE_SRC and "GlowHeight" not in LIVE_SRC)
qn = vm.params()
qe = vm.efectivos(qn)
chk("capa viva, neutro: efectivos() devuelve la v2 bit a bit (%d parametros)" % len(qn),
    all(qe[k] == qn[k] for k in qn) and all(vm.live_desde_S(0.0)[k] == qn[k] for k in vm.live_desde_S(0.0)))


def params_check(qm):
    """dict del check desde un dict del modelo (sin dither, como P: el dither se prueba aparte)."""
    return base_params(**{k: v for k, v in qm.items() if k != "DitherAmt"})


ediff = 0.0
for _ in range(200):
    r_, a_ = 64000.0 * rng.uniform() ** 2, rng.uniform(-math.pi, math.pi)
    x_, y_ = 380.0 + r_ * math.cos(a_), r_ * math.sin(a_)
    c1, _ = ps_suelo(x_, y_, 0.0, P)
    c2, _ = ps_suelo(x_, y_, 0.0, params_check(qe))
    ediff = max(ediff, float(np.abs(c1.a - c2.a).max()))
chk("capa viva, neutro: el PS con los efectivos da el MISMO color que la v2 (200 pixeles de suelo)", ediff == 0.0,
    "max |dif| %.1e" % ediff)
ev = 0.0
for S_ in (-1.0, -0.4, 0.3, 1.0):
    qv = vm.params(**vm.live_desde_S(S_, Fog=1.2, Glow=0.8, Shadow=1.1, Warm=1.3))
    qve = vm.efectivos(qv)
    q_hl = params_check(qve)
    qm_ = model_params(q_hl)
    for _ in range(60):
        r_, a_ = 64000.0 * rng.uniform() ** 2, rng.uniform(-math.pi, math.pi)
        x_, y_ = 380.0 + r_ * math.cos(a_), r_ * math.sin(a_)
        c, _ = ps_suelo(x_, y_, 0.0, q_hl)
        gx, gy, h, hf = vm.valley_grad(np.array([x_]), np.array([y_]), 0.0, qm_)
        cm = vm.suelo(np.array([x_]), np.array([y_]), gx, gy, h, hf, CAM, qm_)[0]
        ev = max(ev, float(np.abs(c.a - cm).max()))
    for az_, el_ in ((0, 1), (20, 3), (-40, 7), (180, 30)):
        c, _ = ps(q=q_hl, VI1=Vec([0, 0, 0, 0]), LPi=Vec([0, 0, 0]), CamL=-D(az_, el_), Dist=100000.0, Part=1.0)
        cm = vm.cielo(np.array([vm.dir_d(az_, el_)]), qm_)[0]
        ev = max(ev, float(np.abs(c.a - cm).max()))
chk("capa viva, respirando (S -1 .. +1, familias no default): PS traducido = modelo con efectivos() (suelo y cielo)",
    ev < 1e-4, "max |dif| %.1e" % ev)
BUILD = ROOT / "VR_Test" / "Saved" / "ClaudeScripts" / "valley_build.json"
BK = ROOT / "VR_Test" / "Saved" / "ClaudeScripts" / "valle_v2_aplicada_backup" / "valley_build.json"
if BUILD.exists() and BK.exists():
    import json as _json
    bn, bo = _json.loads(BUILD.read_text(encoding="utf-8")), _json.loads(BK.read_text(encoding="utf-8"))
    cambios = []
    for cn, co in zip(bn["customs"], bo["customs"]):
        sin_com = lambda c: [l for l in c.replace("\r\n", "\n").split("\n") if not l.lstrip().startswith("//")]
        if sin_com(cn["code"]) != sin_com(co["code"]):
            cambios.append(cn["desc"] + ": codigo")
        for a_, b_ in zip(cn["inputs"], co["inputs"]):
            if a_ != b_:
                cambios.append("%s.%s" % (cn["desc"], a_["name"]))
    pn = {p["name"] for p in bn["params"]} - {p["name"] for p in bo["params"]}
    viejos_iguales = all(p in bn["params"] for p in bo["params"])
    chk("capa viva: valley_build.json = respaldo de la v2 aplicada + 11 parametros + 9 fuentes del PS (codigo igual)",
        sorted(cambios) == sorted("ValleyPS." + k for k in LIVE_SRC) and len(pn) == 11 and viejos_iguales,
        "cambios %d, parametros nuevos %d" % (len(cambios), len(pn)))
else:
    print("--    valley_build.json o su respaldo no estan: se saltea la comparacion del plan de armado")


# ============================ 4. identico al plan ============================
if PLAN.exists():
    blocks = re.findall(r"```hlsl\n(.*?)```", PLAN.read_text(encoding="utf-8"), re.S)
    vistos = set()
    for b in blocks:
        name = b.split()[1]
        if name not in FILES:
            continue
        vistos.add(name)
        L = PARSED[name][0].rstrip("\n").split("\n")
        k = [i for i, l in enumerate(L) if l == RULE]
        chk("codigo de %s identico a la seccion 7.2 del plan" % name, len(k) == 2 and L[:k[0]] + L[k[1] + 1:] == b.rstrip("\n").split("\n"))
    chk("la seccion 7.2 del plan trae los tres bloques", vistos == set(FILES), "encontrados: %s" % sorted(vistos))
else:
    print("--    plan no encontrado: no se compara con la seccion 7.2")

print("\nRESULTADO: " + ("TODO OK" if not fails else "FALLAS: %s" % fails))
sys.exit(1 if fails else 0)
