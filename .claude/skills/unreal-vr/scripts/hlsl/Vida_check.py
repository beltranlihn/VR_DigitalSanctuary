# -*- coding: utf-8 -*-
# Vida_check.py - verificacion de DustVS / DustPS / GustLeanVS (la capa de vida del valle, 2026-09-28) SIN Unreal.
# Uso:  python Vida_check.py          (desde cualquier carpeta; no escribe nada en el repo)
#
# 1. Estatico: la tabla de ENTRADAS de cada cabecera coincide con el codigo (toda entrada se usa), sin bucles, sin
#    arreglos, sin half; OutputType; las salidas adicionales se escriben; el default de cada ScalarParameter de la
#    cabecera = vida_model.MAT = la tabla 5.2 del plan (docs/PLAN-VIDA-VALLE-2026-09-28.md), y los parametros del
#    valle = la tabla 6.3.
# 2. Compila un wrapper que imita la funcion que Unreal genera para un Custom (con salidas adicionales como inout):
#    dxc SM6 (-WX), fxc SM5, glslc HLSL -> SPIR-V Vulkan 1.1 (-Werror) + spirv-val (el camino de la Quest); el PS
#    tambien con las ENTRADAS en half. Cuenta [branch] -> DontFlatten en el SPIR-V.
# 3. Traduce MECANICAMENTE el HLSL a Python y lo compara con el modelo numpy (vida_model.dust_vs / dust_ps /
#    gust_lean_vs) en miles de vertices con estados de rafaga al azar, los dos ojos y perillas no default.
# 4. Controles (en el HLSL traducido): el VALLE NEUTRO (GustK = 0) devuelve el gradiente de ValleyGradVS bit a bit (y
#    el cielo tambien, y el suelo fuera del frente aunque haya rafaga); sin presencia (Glob 0) el polvo no dibuja; el
#    remolino es un LAZO CERRADO (desplazamiento 0 exacto al empezar y al terminar la rafaga); continuidad cuadro a
#    cuadro; confort (nada visible a < NearMin de un ojo ni dentro del disco del metaball; tamano >= 0,2 grados); el
#    polvo de rafaga no existe sin rafaga; la franja no llega a menos de GustNear del usuario.
# 5. CONTROL NEGATIVO: copias mutadas del HLSL TIENEN que fallar la equivalencia; si no fallan, el verificador no
#    mide lo que dice.
# (rev. 2) Ademas: el polvo fuera del volumen del aliento (< 110 cm de un ojo: 0 motas visibles); el alfa IGUAL en los
#    dos ojos con el punto ciclopeo (y distinto sin el: control); la DERIVA vuelve a 0 exacto al terminar la relajacion;
#    la velocidad analitica V (la que apaga lo rapido) = la derivada numerica de la posicion, en la rafaga y en la
#    relajacion; continuidad con el BP del modelo (rafaga + relajacion + la siguiente).
# 6. V INVERTIDA + UV EN FP16 (gotcha 302 y el guardado de la StaticMesh): las semillas como las escribe
#    gen_valley_dust.py, en half y con la V invertida, dan las MISMAS estadisticas (motas, polvo de rafaga, posiciones
#    exactas, alfa total). Control negativo: una codificacion con la esquina y los bits en V SI rompe.
import glob, math, os, re, subprocess, sys, tempfile
from pathlib import Path

import numpy as np

HL = Path(__file__).resolve().parent
ROOT = HL.parents[4]
PLAN = ROOT / "docs" / "PLAN-VIDA-VALLE-2026-09-28.md"
sys.path.insert(0, str(HL.parent))
import vida_model as vm  # noqa: E402

FILES = {"DustVS": ("vs", "float3", [("DustV", "float4")]), "DustPS": ("ps", "float3", [("Alpha", "float")]),
         "GustLeanVS": ("vs", "float4", [])}
fails = []


def chk(label, ok, info=""):
    print(("OK    " if ok else "FALLA ") + label + ("  " + info if info else ""))
    if not ok:
        fails.append(label)


# ============================ 1. estatico ============================
def parse_text(txt, name):
    txt = txt.replace("\r\n", "\n")
    ins = re.findall(r"^//\s+(\d+)\s+(\w+)\s+(float[234]?)\s+(.+?)(?:\s{2,}.*)?$", txt, re.M)
    ins = [(int(i), n, t, s.strip()) for i, n, t, s in ins]
    assert [i for i, _, _, _ in ins] == list(range(1, len(ins) + 1)), name
    cmot = re.search(r"OutputType (CMOT_Float\d)", txt).group(1)
    decl = int(re.search(r"ENTRADAS \((\d+)", txt).group(1))
    body = "\n".join(l for l in txt.split("\n") if not l.lstrip().startswith("//"))
    return txt, [(n, t) for _, n, t, _ in ins], [(n, s) for _, n, _, s in ins], cmot, body, decl


def parse(name):
    return parse_text((HL / (name + ".hlsl")).read_text(encoding="ascii"), name)


PARSED = {n: parse(n) for n in FILES}
for name, (kind, ret, extra) in FILES.items():
    txt, ins, srcs, cmot, body, decl = PARSED[name]
    probs = ["entrada sin uso: " + n for n, _ in ins if not re.search(r"\b%s\b" % n, body)]
    if decl != len(ins): probs.append("la cabecera dice %d entradas y lista %d" % (decl, len(ins)))
    if re.search(r"\b(for|while|do)\b", body): probs.append("bucle")
    if re.search(r"\w\s*\[", re.sub(r"\[(branch|flatten)\]", "", body)): probs.append("arreglo")
    if re.search(r"\bhalf\b|\bmin16float\b", body): probs.append("media precision explicita")
    if cmot != "CMOT_Float" + ret[-1]: probs.append("OutputType %s no coincide con %s" % (cmot, ret))
    for on, _ in extra:
        if not re.search(r"^%s = " % on, body, re.M): probs.append("la salida adicional %s no se escribe" % on)
    chk("estatico %s (%d entradas, %s, salidas extra %s)" % (name, len(ins), cmot, [e[0] for e in extra]), not probs,
        "; ".join(probs))

hdr = {}
for name in ("DustVS", "DustPS"):
    for n, s in PARSED[name][2]:
        m = re.match(r"ScalarParameter (\w+) ([\-\d.]+)$", s)
        if m:
            hdr[m.group(1)] = float(m.group(2))
malos = [k for k, v in hdr.items() if k not in vm.MAT or abs(vm.MAT[k] - v) > 1e-12]
faltan = [k for k, v in vm.MAT.items() if not isinstance(v, tuple) and k not in hdr]
chk("defaults de las cabeceras del polvo = vida_model.MAT (%d escalares)" % len(hdr), not malos and not faltan,
    "distintos %s; sin entrada %s" % (malos, faltan))
vs_vec = sorted(n for n, s in PARSED["DustVS"][2] if s.startswith("VectorParameter"))
chk("los vectores del DustVS = los internos del modelo (VidaT, VidaG, VidaS, VidaE, VidaF, VidaSoul)",
    vs_vec == sorted(vm.MAT_INTERNO), "%s" % vs_vec)
gl_vec = sorted(n for n, s in PARSED["GustLeanVS"][2] if s.startswith("VectorParameter"))
chk("los vectores del GustLeanVS = GUST_MAT del modelo", gl_vec == sorted(vm.GUST_MAT), "%s" % gl_vec)


def num(t):
    return float(t.strip().replace("−", "-").replace(",", "."))


def tabla(seccion):
    out = {}
    en = False
    for linea in PLAN.read_text(encoding="utf-8").splitlines():
        if linea.startswith("### " + seccion):
            en = True
            continue
        if en and linea.startswith("### "):
            break
        if en and linea.startswith("| `"):
            cols = [c.strip() for c in linea.strip().strip("|").split("|")]
            grupo, nom, tipo, dflt = cols[0].strip("`"), cols[1].strip("`"), cols[2], cols[3]
            if tipo.startswith("vector"):
                m = re.search(r"\(([^)]*)\)", dflt)
                val = tuple(num(p) for p in re.split(r";\s+|,\s+(?=[\-−\d])", m.group(1)))
            elif tipo.startswith("bool"):
                val = dflt.strip().lower() == "true"
            elif tipo.startswith("sonidos"):
                continue
            else:
                val = num(re.match(r"\s*([−\-]?[\d.,]+)", dflt).group(1))
            out[nom] = (grupo, tipo, val)
    return out


def compara_tabla(t, ref, ignorar=()):
    malos = []
    for k, v in ref.items():
        if k in ignorar:
            continue
        if k not in t:
            malos.append("%s falta en la tabla" % k)
        elif isinstance(v, tuple):
            if len(v) != len(t[k][2]) or not np.allclose(v, t[k][2], atol=1e-9):
                malos.append("%s modelo %s tabla %s" % (k, v, t[k][2]))
        elif isinstance(v, bool) or isinstance(t[k][2], bool):
            if v != t[k][2]:
                malos.append("%s modelo %s tabla %s" % (k, v, t[k][2]))
        elif abs(t[k][2] - v) > 1e-9:
            malos.append("%s modelo %g tabla %g" % (k, v, t[k][2]))
    sobran = [k for k in t if k not in ref]
    return malos, sobran


if PLAN.exists() and "### 5.2" in PLAN.read_text(encoding="utf-8"):
    ref52 = dict(vm.MAT)
    ref52.update(vm.MAT_INTERNO)
    malos, sobran = compara_tabla(tabla("5.2"), ref52)
    chk("tabla 5.2 del plan = vida_model.MAT + MAT_INTERNO (%d parametros del polvo)" % len(ref52), not malos and not sobran,
        "; ".join(malos) + ("; sobran %s" % sobran if sobran else ""))
    malos, sobran = compara_tabla(tabla("5.4"), vm.BP)
    chk("tabla 5.4 del plan = vida_model.BP (%d perillas del BP)" % len(vm.BP), not malos and not sobran,
        "; ".join(malos) + ("; sobran %s" % sobran if sobran else ""))
    malos, sobran = compara_tabla(tabla("6.3"), vm.GUST_MAT)
    chk("tabla 6.3 del plan = vida_model.GUST_MAT (5 vectores del valle)", not malos and not sobran,
        "; ".join(malos) + ("; sobran %s" % sobran if sobran else ""))
else:
    print("--    el plan todavia no tiene las tablas 5.2/5.4/6.3: se saltea la comparacion")


# ============================ 2. compilacion ============================
def wrapper(name, half_ps=False):
    kind, ret, extra = FILES[name]
    _, ins, _, _, body, _ = PARSED[name]
    tp = (lambda t: t.replace("float", "half")) if half_ps else (lambda t: t)
    cb = "\n".join("  %s cb_%s;" % (t, n) for n, t in ins)
    args = ["cb_" + n for n, _ in ins]
    outs = "".join(", inout %s %s" % (t, n) for n, t in extra)
    decl = "".join("  %s o_%s = (%s)0;\n" % (t, n, t) for n, t in extra)
    oargs = "".join(", o_%s" % n for n, _ in extra)
    osum = " + ".join(["dot(o_%s, o_%s)" % (n, n) for n, _ in extra] or ["0.0"])
    params = ", ".join("%s %s" % (tp(t), n) for n, t in ins)
    if kind == "vs":
        lp = [i for i, (n, _) in enumerate(ins) if n == "LP"][0]
        args[lp] = "inLP"
        rx = "o.xyz" if ret != "float" else "o"
        rw = "o.w" if ret == "float4" else "0.0"
        entry = ("float4 main(float3 inLP : POSITION) : SV_Position\n{\n  FMaterialVertexParameters P; P.Dummy = inLP;\n%s"
                 "  %s o = CustomExpression0(P, %s%s);\n  return float4(inLP + %s, 1.0 + %s + %s);\n}\n"
                 % (decl, ret, ", ".join(args), oargs, rx, rw, osum))
        pstruct, ptype = "struct FMaterialVertexParameters { float3 Dummy; };", "FMaterialVertexParameters"
    else:
        args = ["(%s)%s" % (tp(t), a) for a, (n, t) in zip(args, ins)]
        args[0] = "(%s)inDustV" % tp("float4")
        entry = ("float4 main(float4 sv : SV_Position, float4 inDustV : TEXCOORD0) : SV_Target\n{\n  FMaterialPixelParameters P; P.SvPosition = sv;\n%s"
                 "  %s r = CustomExpression0(P, %s%s);\n  return float4(r, 1.0 + %s);\n}\n"
                 % (decl, ret, ", ".join(args), oargs, osum))
        pstruct, ptype = "struct FMaterialPixelParameters { float4 SvPosition; };", "FMaterialPixelParameters"
    return ("struct FViewStub { float GameTime; };\ncbuffer ViewCB : register(b0) { FViewStub View; };\n"
            "cbuffer MatCB : register(b1)\n{\n%s\n};\n%s\n%s CustomExpression0(%s Parameters, %s%s)\n{\n%s\n}\n\n%s"
            % (cb, pstruct, ret, ptype, params, outs, body, entry))


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


tmp = Path(tempfile.mkdtemp(prefix="vida_check_"))
for name, (kind, _, _) in FILES.items():
    variantes = [("fp32", False)] + ([("half", True)] if kind == "ps" else [])
    for tag, half in variantes:
        src = tmp / ("wrap_%s_%s.hlsl" % (name, tag))
        src.write_text(wrapper(name, half), encoding="ascii")
        if DXC:
            cmd = [DXC, "-nologo", "-T", kind + ("_6_2" if half else "_6_0"), "-E", "main", "-WX", "-O3", "-Fo",
                   str(tmp / (name + tag + ".dxil")), str(src)] + (["-enable-16bit-types"] if half else [])
            rc, out = run(cmd)
            chk("dxc %s -WX  %s (%s)" % (kind, name, tag), rc == 0, out[-400:] if rc else "")
        else:
            print("--    dxc no encontrado (Windows SDK)")
        if half:
            continue
        if FXC:
            rc, out = run([FXC, "/nologo", "/T", kind + "_5_0", "/E", "main", "/O3", "/Fo", str(tmp / (name + ".dxbc")), str(src)])
            warns = sorted(set(re.findall(r"warning (X\d+)", out)))
            chk("fxc %s_5_0      %s" % (kind, name), rc == 0 and not warns, (out[-400:] if rc or warns else ""))
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
            chk("glslc HLSL->SPIR-V + spirv-val  %s" % name, ok, out[-400:] if not ok else "")
            if ok and SPVDIS:
                rc3, dis = run([SPVDIS, str(spv)])
                nb = len(re.findall(r"^\s*\[branch\]\s*$", PARSED[name][4], re.M))
                nd = len(re.findall(r"OpSelectionMerge %\w+ DontFlatten", dis))
                chk("[branch] -> DontFlatten en el SPIR-V  %s" % name, rc3 == 0 and nd >= nb,
                    "%d [branch] en el codigo, %d DontFlatten en el SPIR-V" % (nb, nd))
        else:
            print("--    glslc no encontrado (Android NDK)")
print("      (wrappers en %s)" % tmp)


# ============================ 3. traduccion a Python ============================
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
    t = np.clip((_u(x) - _u(a)) / (_u(b) - _u(a)), 0.0, 1.0)
    return _w(t * t * (3.0 - 2.0 * t))


class ViewStub:
    GameTime = 0.0


ENV = dict(float2=_mk, float3=_mk, float4=_mk, sqrt=_f1(np.sqrt), sin=_f1(np.sin), cos=_f1(np.cos), tan=_f1(np.tan),
           asin=_f1(np.arcsin), acos=_f1(np.arccos), exp=_f1(np.exp), floor=_f1(np.floor), abs=_f1(np.abs),
           radians=_f1(np.radians), degrees=_f1(np.degrees),
           frac=_f1(lambda x: x - np.floor(x)), saturate=_f1(lambda x: np.clip(x, 0.0, 1.0)), pow=_f2(np.power),
           max=_f2(np.maximum), min=_f2(np.minimum), smoothstep=_ss,
           step=lambda e, x: _w((np.asarray(_u(x)) >= _u(e)).astype(np.float64)),
           clamp=lambda x, a, b: _w(np.clip(_u(x), _u(a), _u(b))),
           lerp=lambda a, b, t: _w(_u(a) + (_u(b) - _u(a)) * _u(t)),
           dot=lambda a, b: float(np.dot(a.a, b.a)), length=lambda a: float(np.linalg.norm(a.a)),
           normalize=lambda a: Vec(a.a / np.linalg.norm(a.a)), cross=lambda a, b: Vec(np.cross(a.a, b.a)))


def translate_text(txt, ins, name):
    py, ind, pend = [], 1, False
    ex = lambda e: re.sub(r"!\(", "not (", e.replace("||", " or ").replace("&&", " and "))
    body = "\n".join(l for l in txt.split("\n") if not l.lstrip().startswith("//"))
    for raw in body.split("\n"):
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
        elif re.match(r"^if \((.*)\) \{ (\w+) = (.*); \}$", l):
            m = re.match(r"^if \((.*)\) \{ (\w+) = (.*); \}$", l)
            py += [pad + "if %s:" % ex(m.group(1)), pad + "    %s = %s" % (m.group(2), ex(m.group(3)))]
        elif re.match(r"^if \((.*)\)$", l):
            py.append(pad + "if %s:" % ex(re.match(r"^if \((.*)\)$", l).group(1)))
            pend = True
        elif re.match(r"^return (.*);$", l):
            py.append(pad + "return (%s), dict(locals())" % ex(re.match(r"^return (.*);$", l).group(1)))
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
    return ns["F"]


VSF = translate_text(PARSED["DustVS"][0], PARSED["DustVS"][1], "DustVS")
PSF = translate_text(PARSED["DustPS"][0], PARSED["DustPS"][1], "DustPS")
GLF = translate_text(PARSED["GustLeanVS"][0], PARSED["GustLeanVS"][1], "GustLeanVS")
VS_IN = [n for n, _ in PARSED["DustVS"][1]]
GL_IN = [n for n, _ in PARSED["GustLeanVS"][1]]

SD = vm.seeds()
ENC = vm.encode(SD)
NV = ENC["LP"].shape[0]


def sub(enc, ix):
    return {k: (v[ix] if isinstance(v, np.ndarray) and v.shape[0] == NV else v) for k, v in enc.items()}


def eval_dust(fn, enc, j, pv, camL, q, gt=0.0):
    view = ViewStub()
    view.GameTime = gt
    args = dict(LP=Vec(enc["LP"][j]), Crn=Vec(enc["UV0"][j]), Sa=Vec(enc["UV1"][j]), Sb=Vec(enc["UV2"][j]),
                Sc=Vec(enc["UV3"][j]), CamL=Vec(camL))
    for k in vm.MAT_INTERNO:
        args[k] = Vec(pv.get(k, vm.MAT_INTERNO[k]))
    for n in VS_IN:
        if n not in args:
            args[n] = q[n]
    r, loc = fn(None, view, **{n: args[n] for n in VS_IN})
    return r.a, loc["DustV"].a, loc


def estado_rafaga(rng, lateral=True, s_frac=None):
    """Un estado del BP al azar: rafaga lateral o de soplo, frente en cualquier punto, presencia y meandro."""
    bp = vm.VidaBP(bp=dict(GustLife=rng.uniform(14, 30), GustW=rng.uniform(400, 1000), PathHalf=rng.uniform(1500, 3000)))
    bp.GustIdx = float(rng.integers(0, 20))
    if lateral:
        bp.start_lateral()
    else:
        bp.start_breath()
    fr = rng.random() if s_frac is None else s_frac
    bp.S = bp.S0 + (bp.S1 - bp.S0) * fr
    bp.Tm = rng.uniform(0.0, 1800.0)
    bp.Rate = rng.uniform(0.5, 3.0)
    bp.Glob = rng.uniform(0.4, 1.0)
    bp.Amp = rng.uniform(0.5, 1.0)
    bp.Hold = float(rng.choice([1.0, rng.uniform(0.0, 1.0)]))        # rafaga (1) o relajacion (0..1)
    bp.HoldV = -rng.uniform(0.0, 0.12) if bp.Hold < 1.0 else 0.0
    if rng.random() < 0.6:                                             # con punto ciclopeo (la cabeza, no el actor)
        bp.cam = bp.actor.loc + np.array([rng.uniform(-10, 10), rng.uniform(-6, 6), rng.uniform(-5, 5)])
    return bp


def mat_random(rng):
    q = dict(vm.MAT)
    for k, v in q.items():
        if isinstance(v, tuple):
            continue
        q[k] = v * rng.uniform(0.8, 1.25) if v != 0 else v
    q["NearFull"] = max(q["NearFull"], q["NearMin"] + 5.0)
    q["FarFade1"] = max(q["FarFade1"], q["FarFade0"] + 50.0)
    q["SpeedFade1"] = max(q["SpeedFade1"], q["SpeedFade0"] + 2.0)
    q["SoulMargin1"] = max(q["SoulMargin1"], q["SoulMargin0"] + 1.0)
    q["SunG"] = min(q["SunG"], 0.9)
    return q


def compara_dust(fn, n_states=14, per=140, seed=5, mats=True):
    rng = np.random.default_rng(seed)
    eo = ea = 0.0
    nvis = 0
    for st in range(n_states):
        bp = estado_rafaga(rng, lateral=(st % 3 != 2))
        pv = bp.push_dust(live=float(st % 4 != 3))
        if st % 5 == 4:
            pv["VidaS"][3] = 0.0            # sin rafaga
        q = mat_random(rng) if (mats and st % 2 == 1) else dict(vm.MAT)
        camL = np.array([rng.uniform(-8, 8), rng.choice([-3.2, 3.2]), rng.uniform(-6, 6)])
        ix = rng.choice(NV, per, replace=False)
        e = sub(ENC, ix)
        gt = rng.uniform(0.0, 5000.0)
        m = vm.dust_vs(e, pv, camL, q, game_time=gt)
        for j in range(per):
            off, dv, loc = eval_dust(fn, e, j, pv, camL, q, gt)
            eo = max(eo, float(np.abs(off - m["offs"][j]).max()))
            ea = max(ea, float(np.abs(dv - m["DustV"][j]).max()))
            nvis += int(m["al"][j] > 0.02)
    return eo, ea, nvis


eo, ea, nvis = compara_dust(VSF)
chk("DustVS traducido = modelo numpy (14 estados: rafagas laterales y de soplo, editor y juego, perillas no default)",
    eo < 1e-6 and ea < 1e-7 and nvis > 100, "|offset| %.1e cm  |DustV| %.1e  (%d vertices con alfa > 0,02)" % (eo, ea, nvis))

rng = np.random.default_rng(11)
ep = 0.0
for _ in range(400):
    dv = np.array([rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(0, 1), rng.uniform(0, 1)])
    q = mat_random(rng)
    col, loc = PSF(None, ViewStub(), DustV=Vec(dv), ColLit=Vec(q["ColLit"]), ColDim=Vec(q["ColDim"]))
    cm, am_ = vm.dust_ps(dv, q)
    ep = max(ep, float(np.abs(col.a - cm).max()), abs(loc["Alpha"] - float(am_)))
chk("DustPS traducido = modelo numpy (400 muestras)", ep < 1e-12, "max |dif| %.1e" % ep)


def eval_gl(fn, G, LP, part, pv):
    args = dict(G=Vec(G), LP=Vec(LP), Part=part)
    for k in vm.GUST_MAT:
        args[k] = Vec(pv.get(k, vm.GUST_MAT[k]))
    r, loc = fn(None, ViewStub(), **{n: args[n] for n in GL_IN})
    return r.a, loc


def puntos_valle(rng, n):
    r = 100.0 * np.exp(rng.uniform(math.log(5.0), math.log(600.0), n))
    th = rng.uniform(0, 2 * np.pi, n)
    LP = np.stack([r * np.cos(th), r * np.sin(th), np.zeros(n)], 1)
    G = np.stack([rng.normal(0, 0.1, n), rng.normal(0, 0.1, n), rng.uniform(0, 3000, n), rng.uniform(0, 1, n)], 1)
    G[rng.random(n) < 0.4, 3] = 0.0
    return LP, G


rng = np.random.default_rng(21)
eg = 0.0
nact = 0
for st in range(12):
    bp = estado_rafaga(rng, lateral=(st % 3 != 2))
    bp.q.update(GustLight=rng.uniform(0.5, 3.0), GustLean=rng.uniform(0.0, 0.2), GustRuffle=rng.uniform(0.0, 0.2),
                LeanAz=rng.uniform(-180, 180), GustNear=rng.uniform(800, 2500))
    bp.valley = vm.Xf((rng.uniform(-300, 300), rng.uniform(-300, 300), vm.VALLE_Z), rng.uniform(-40, 40))
    pv = bp.push_valley()
    LP, G = puntos_valle(rng, 400)
    m = vm.gust_lean_vs(G, LP, 0.0, pv)
    for j in range(len(LP)):
        o, loc = eval_gl(GLF, G[j], LP[j], 0.0, pv)
        eg = max(eg, float(np.abs(o - m[j]).max()))
        nact += int(np.abs(o - G[j]).max() > 1e-4)
chk("GustLeanVS traducido = modelo numpy (12 estados x 400 vertices del valle, valle girado, perillas al azar)",
    eg < 1e-9 and nact > 150, "max |dif| %.1e  (%d vertices tocados por la rafaga)" % (eg, nact))


# ============================ 4. controles (HLSL traducido) ============================
# ---- el VALLE NEUTRO: bit a bit
rng = np.random.default_rng(3)
LP, G = puntos_valle(rng, 600)
neutro = dict(vm.GUST_MAT)
iguales = all(np.array_equal(eval_gl(GLF, G[j], LP[j], 0.0, neutro)[0], G[j]) for j in range(len(LP)))
chk("valle NEUTRO (GustK = 0, el default del material): GustLeanVS devuelve el gradiente de ValleyGradVS BIT A BIT (600 vertices)",
    iguales)
bp = estado_rafaga(np.random.default_rng(4))
bp.S = 0.0
pvA = bp.push_valley()
cielo = all(np.array_equal(eval_gl(GLF, G[j], LP[j], 1.0, pvA)[0], G[j]) for j in range(200))
chk("cielo (Part 1) con una rafaga en pleno: sin cambios, bit a bit", cielo)
lejos = []
for j in range(len(LP)):
    o, loc = eval_gl(GLF, G[j], LP[j], 0.0, pvA)
    if loc.get("a", 1.0) == 0.0:
        lejos.append(np.array_equal(o, G[j]))
chk("suelo fuera del frente con una rafaga en pleno: sin cambios, bit a bit (%d vertices)" % len(lejos), len(lejos) > 50 and all(lejos))
# la franja no llega a menos de GustNear del usuario
near_ok = True
for rr in np.linspace(0.0, vm.BP["GustNear"] - 10.0, 60):
    for th in np.linspace(0, 2 * np.pi, 24, endpoint=False):
        p = pvA["GustS"][:2] + rr * np.array([math.cos(th), math.sin(th)])
        o, _ = eval_gl(GLF, np.array([0.01, -0.02, 0.0, 0.3]), np.array([p[0], p[1], 0.0]), 0.0, pvA)
        near_ok &= np.array_equal(o, np.array([0.01, -0.02, 0.0, 0.3]))
chk("la franja no toca el piso a menos de GustNear (%g cm) del usuario: el piso cercano queda quieto" % vm.BP["GustNear"], near_ok)

# ---- polvo: sin presencia no dibuja
IXS = np.arange(0, NV, 5)
ES = sub(ENC, IXS)


def todos(pv, camL=(0.0, 3.2, 0.0), q=None, gt=0.0):
    q = q or dict(vm.MAT)
    out = []
    for j in range(len(IXS)):
        off, dv, loc = eval_dust(VSF, ES, j, pv, camL, q, gt)
        out.append(loc)
    return out


bp = vm.VidaBP()
pv0 = bp.push_dust()
pv0["VidaT"][2] = 0.0
r = todos(pv0)
chk("sin presencia (Glob 0): todos los quads colapsados (0 pixeles)", all(x["hsz"] == 0.0 for x in r))
bp.Glob = 1.0
pvc = bp.push_dust()
r = todos(pvc)
vis = [x for x in r if x["al"] > 0.02]
gvis = [x for x in r if x["al"] > 0.002 and x["isG"] > 0.5]
chk("control positivo: en calma hay polvo visible", len(vis) > 150, "%d de %d" % (len(vis), len(r)))
chk("en calma el polvo de rafaga NO existe (alfa 0)", len(gvis) == 0, "%d visibles" % len(gvis))
dmin = min(x["dist"] for x in vis)
chk("confort: la mota visible mas cercana al ojo esta a >= NearMin (%g cm)" % vm.MAT["NearMin"], dmin >= vm.MAT["NearMin"],
    "%.1f cm" % dmin)
soul_l = vm.SOUL_W - vm.ACTOR
en_disco = 0
for x in vis:
    SDv = soul_l - np.array([0.0, 3.2, 0.0])
    ang = math.degrees(math.acos(np.clip(np.dot(x["DnC"].a, SDv / np.linalg.norm(SDv)), -1, 1)))
    ra = math.degrees(math.asin(min(vm.BP["SoulR"] / np.linalg.norm(SDv), 1.0)))
    en_disco += int(ang < ra + vm.MAT["SoulMargin0"])
chk("el disco del metaball (+ margen) queda sin polvo visible", en_disco == 0, "%d motas adentro" % en_disco)
szmin = min(x["sdeg"] for x in r)
chk("tamano angular >= 0,2 grados (no centellea)", szmin >= 0.2 - 1e-12, "%.3f" % szmin)

# ---- el remolino es un LAZO CERRADO: al empezar y al terminar la rafaga, desplazamiento 0 EXACTO y actividad 0
for lateral in (True, False):
    for cuando in ("inicio", "final, deriva relajada (Hold 0)"):
        bp = vm.VidaBP()
        bp.Glob = 1.0
        (bp.start_lateral if lateral else bp.start_breath)()
        bp.S = bp.S0 if cuando == "inicio" else bp.S1
        if cuando != "inicio":
            bp.Hold = 0.0
        pv = bp.push_dust()
        r = todos(pv)
        gmax = max(float(np.abs(x["G"].a).max()) for x in r)
        amax = max(x["act"] for x in r)
        chk("lazo cerrado (%s, %s): desplazamiento de la rafaga %.1e cm y actividad %.1e"
            % ("lateral" if lateral else "soplo", cuando, gmax, amax), gmax == 0.0 and amax == 0.0)
    # al terminar el frente (Hold 1) el remolino ya cerro: queda SOLO la deriva, horizontal y a favor del viento
    bp = vm.VidaBP()
    bp.Glob = 1.0
    (bp.start_lateral if lateral else bp.start_breath)()
    bp.S = bp.S1
    pv = bp.push_dust()
    r = todos(pv)
    dvec = np.array([pv["VidaG"][2], pv["VidaG"][3], 0.0])
    lateral_err = max(float(np.linalg.norm(x["G"].a - np.dot(x["G"].a, dvec) * dvec)) for x in r)
    a_favor = min(float(np.dot(x["G"].a, dvec)) for x in r)
    gmx = max(float(np.linalg.norm(x["G"].a)) for x in r)
    chk("al terminar el frente (%s) queda SOLO la deriva: a favor del viento (>= 0), horizontal, nada de lazo (%.1e cm fuera "
        "de la direccion; hasta %.0f cm corridas)" % ("lateral" if lateral else "soplo", lateral_err, gmx),
        lateral_err < 1e-9 and a_favor >= 0.0 and gmx > 20.0)

# ---- continuidad: una rafaga lateral entera a 72 Hz, el salto maximo de una mota visible por cuadro
ixc = np.arange(0, NV, 4)[::3]
ec = sub(ENC, ixc)
dt = 1.0 / 72.0
salto = 0.0
salto_ang = 0.0
vmax_err = 0.0
nv_err = 0
for per in (None, dict(GapMin=40.0, GapMax=40.0)):
    bp = vm.VidaBP(bp=dict(per or {}, FirstGap=1.0), cam=vm.ACTOR + np.array([3.0, -2.0, 1.0]))
    bp.GlobBase = 1.0
    prev = None
    fase = []
    for i in range(int(95.0 / dt)):
        bp.step(dt, 0.0, 0.0)
        tomar = (i % 90 == 0) or (i % 90 == 1)
        if not tomar:
            prev = None
            continue
        m = vm.dust_vs(ec, bp.push_dust(), (0.0, 3.2, 0.0))
        if prev is not None:
            vis = (m["al"] > 0.02) | (prev["al"] > 0.02)
            if vis.any():
                # un SALTO es lo que la velocidad no explica: |dP - V dt| (un movimiento rapido pero continuo no cuenta)
                resto = np.linalg.norm((m["P"] - prev["P"]) - 0.5 * (m["V"] + prev["V"]) * dt, axis=1)
                salto = max(salto, float(resto[vis].max()))
                u1 = (m["P"] - np.array([0.0, 3.2, 0.0])) / m["dist"][:, None]
                u0 = (prev["P"] - np.array([0.0, 3.2, 0.0])) / prev["dist"][:, None]
                ang = np.degrees(np.arccos(np.clip((u1 * u0).sum(1), -1.0, 1.0)))
                salto_ang = max(salto_ang, float(ang[vis & (m["al"] > 0.2)].max()) if (vis & (m["al"] > 0.2)).any() else 0.0)
            # la velocidad analitica contra la derivada numerica (solo donde algo se mueve de verdad)
            vnum = (m["P"] - prev["P"]) / dt
            van = 0.5 * (m["V"] + prev["V"])
            mov = np.linalg.norm(vnum, axis=1) > 1.0
            if mov.any():
                e = np.linalg.norm(vnum - van, axis=1)[mov] / np.maximum(np.linalg.norm(vnum, axis=1)[mov], 1.0)
                vmax_err = max(vmax_err, float(np.percentile(e, 99)))
                nv_err += int(mov.sum())
        prev = m
chk("continuidad con el BP del modelo (rafaga + deriva + relajacion + la siguiente, 2 agendas): ninguna mota visible SALTA "
    "(lo que la velocidad no explica, |dP - V dt| < 0,01 cm por cuadro); las bien visibles (alfa > 0,2) no pasan de "
    "0,1 grados por cuadro (7 grados/s: lo rapido ya se esta apagando)", salto < 0.01 and salto_ang < 0.1,
    "salto %.1e cm, %.4f grados por cuadro" % (salto, salto_ang))
chk("la velocidad analitica del VS (la que apaga lo rapido y mide el confort) = la derivada numerica de la posicion, "
    "tambien en la relajacion (p99 del error relativo < 2 %)", vmax_err < 0.02 and nv_err > 1000,
    "p99 %.2e (%d muestras)" % (vmax_err, nv_err))

# ---- el polvo FUERA del volumen del aliento (inhalar 40-95 cm, pluma hasta 110 cm): 0 motas visibles a < 110 cm de un
# ojo, en calma, en el pico de una rafaga lateral, en el soplo pasando por el usuario y en la relajacion
CEN = sub(ENC, np.arange(0, NV, 4))
ojos = (np.array([0.0, -vm.IPD / 2, 0.0]), np.array([0.0, vm.IPD / 2, 0.0]))
cerca = 0
for estado in ("calma", "lateral", "soplo", "relajacion"):
    bp = vm.VidaBP(cam=vm.ACTOR)
    bp.Glob = 1.0
    if estado == "lateral":
        bp.start_lateral(1.0)
        bp.S = 0.0
    elif estado == "soplo":
        bp.start_breath()
        bp.S = 150.0
    elif estado == "relajacion":
        bp.start_lateral(1.0)
        bp.S = bp.S1
        bp.Hold = 0.5
    for tm in (0.0, 300.0, 900.0):
        bp.Tm = tm
        pv = bp.push_dust()
        for ojo in ojos:
            m = vm.dust_vs(CEN, pv, ojo)
            cerca += int(((m["al"] > 0.002) & (m["dist"] < 110.0)).sum())
chk("el polvo no entra al volumen del aliento: 0 motas visibles a < 110 cm de un ojo (calma, rafaga, soplo, relajacion)",
    cerca == 0 and vm.MAT["NearMin"] >= 110.0, "%d motas" % cerca)

# ---- el alfa IGUAL en los dos ojos con el punto ciclopeo (HLSL traducido); sin el, distinto (control)
bp = vm.VidaBP(cam=vm.ACTOR)
bp.Glob = 1.0
bp.start_lateral(1.0)
bp.S = 0.0
pvc = bp.push_dust()
pvn = dict(pvc)
pvn["VidaC"] = np.zeros(4)
ixb = np.arange(0, NV, 4)[::2]
eb = sub(ENC, ixb)
dif_c = dif_n = 0.0
for j in range(len(ixb)):
    aL = eval_dust(VSF, eb, j, pvc, ojos[0], dict(vm.MAT))[1][2]
    aR = eval_dust(VSF, eb, j, pvc, ojos[1], dict(vm.MAT))[1][2]
    dif_c = max(dif_c, abs(aL - aR))
    nL = eval_dust(VSF, eb, j, pvn, ojos[0], dict(vm.MAT))[1][2]
    nR = eval_dust(VSF, eb, j, pvn, ojos[1], dict(vm.MAT))[1][2]
    dif_n = max(dif_n, abs(nL - nR))
chk("binocular: con el punto ciclopeo el alfa de cada mota es IDENTICO en los dos ojos (%d motas; sin el, la diferencia "
    "llega a %.2f: el control ve el problema)" % (len(ixb), dif_n), dif_c == 0.0 and dif_n > 0.01, "dif %.1e" % dif_c)
# (la equivalencia del HLSL con el modelo en estos mismos estados la cubre la seccion 3)


# ============================ 5. control negativo: mutaciones ============================
MUT_VS = [
    ("el polvo no se enciende al paso del frente (sin Lift)", "(1.0 + Lift * act)", "(1.0 + 0.0 * act)", 1),
    ("la esquina decodificada de la V", "float kc = floor(Crn.x + 0.5);", "float kc = floor(Crn.y * 4.0);", 1),
    ("sin restar el desplazamiento de la esquina", "float3 P0 = LP - float3(", "float3 P0 = LP + 0.0 * float3(", 1),
    ("el bit de solo-rafaga leido del bit 2", "float isG = step(0.5, f - 2.0 * floor(f / 2.0));", "float isG = step(0.5, floor(f / 2.0) - 2.0 * floor(f / 4.0));", 1),
    ("el lazo abierto (ly sin el ultimo (1 - P))", "float ly = 32.0 * Pu * Pu * Pc * Pc;", "float ly = 32.0 * Pu * Pu * Pc;", 1),
    ("el frente con el signo cambiado", "float tu = saturate(((VidaS.x - xg) / Wd + 2.0) * 0.25);", "float tu = saturate(((xg - VidaS.x) / Wd + 2.0) * 0.25);", 1),
    ("sin el despeje del metaball", "float al = (aBase + (aGust - aBase) * isG) * nearF * farF * soul", "float al = (aBase + (aGust - aBase) * isG) * nearF * farF * 1.0", 1),
    ("NearMin/NearFull invertidos", "smoothstep(NearMin, NearFull, distC)", "smoothstep(NearFull, NearMin, distC)", 1),
    ("sin el Glob", "* spf * VidaT.z;", "* spf * 1.0;", 1),
    ("la luz del lado contrario", "float mu = dot(DnC, Ls);", "float mu = -dot(DnC, Ls);", 1),
    ("el editor usa el reloj del BP", "float Tm = VidaT.x * live + Tt * VidaT.y * (1.0 - live);", "float Tm = VidaT.x;", 1),
    ("billboard con el eje equivocado", "float3 up = cross(fw, rt);", "float3 up = cross(rt, fw);", 1),
    ("el remolino no se achica cerca", "clamp(r0 / max(EddyNear, 1.0), 0.3, 1.0);", "1.0;", 1),
    ("la deriva no vuelve (sin Hold)", "Rd * Ae * Pu * VidaE.w * e1;", "Rd * Ae * Pu * e1;", 1),
    ("la deriva en contra del viento", "+ Rd * Ae * Pu * VidaE.w * e1;", "- Rd * Ae * Pu * VidaE.w * e1;", 1),
    ("el alfa con la camara de cada ojo (sin el ciclopeo)", "float3 CamC = CamL + (VidaC.xyz - CamL) * cyc;", "float3 CamC = CamL;", 1),
    ("el meandro no crece lejos", "clamp(r0 / 300.0, 1.0, max(MeanderFar, 1.0))", "1.0", 1),
    ("el confort cercano con la camara del ojo", "float nearF = smoothstep(NearMin, NearFull, distC);", "float nearF = smoothstep(NearMin, NearFull, dist);", 1),
]
MUT_GL = [
    ("la franja sin el despeje cercano", "float a = Ax * hx * bl * nf;", "float a = Ax * hx * bl;", 1),
    ("la inclinacion con el signo cambiado", "ox = G.x - a * (GustK.y + GustK.w * tvx);", "ox = G.x + a * (GustK.y + GustK.w * tvx);", 1),
    ("la luz sumada a h en vez de hf", "return float4(ox, oy, G.z, ow);", "return float4(ox, oy, G.z + ow - G.w, G.w);", 1),
    ("el frente a lo largo en vez de a lo ancho", "float eta = abs(rel.y * dd.x - rel.x * dd.y);", "float eta = abs(rel.x * dd.x + rel.y * dd.y);", 1),
]
txt0 = PARSED["DustVS"][0]
for lbl, a, b, _ in MUT_VS:
    assert a in txt0, "mutacion no aplicable: " + lbl
    fnm = translate_text(txt0.replace(a, b, 1), PARSED["DustVS"][1], "mut")
    eo2, ea2, _ = compara_dust(fnm, n_states=6, per=90, seed=9)
    chk("mutacion detectada (DustVS): " + lbl, eo2 > 1e-3 or ea2 > 1e-6, "|offset| %.1e  |DustV| %.1e" % (eo2, ea2))
txtg = PARSED["GustLeanVS"][0]
rng = np.random.default_rng(31)
bpm = estado_rafaga(rng)
bpm.S = 0.0
bpm.q.update(GustLean=0.1, GustRuffle=0.05)
pvm = bpm.push_valley()
LPm, Gm = puntos_valle(rng, 400)
for lbl, a, b, _ in MUT_GL:
    assert a in txtg, "mutacion no aplicable: " + lbl
    fnm = translate_text(txtg.replace(a, b, 1), PARSED["GustLeanVS"][1], "mut")
    d = max(float(np.abs(eval_gl(fnm, Gm[j], LPm[j], 0.0, pvm)[0] - vm.gust_lean_vs(Gm[j], LPm[j], 0.0, pvm)[0]).max())
            for j in range(len(LPm)))
    chk("mutacion detectada (GustLeanVS): " + lbl, d > 1e-6, "max |dif| %.1e" % d)


# ============================ 6. V invertida + UV en fp16 ============================
def estad(enc):
    bp = vm.VidaBP()
    bp.Glob = 1.0
    out = {}
    for tag, gust in (("calma", False), ("rafaga", True)):
        if gust:
            bp.start_lateral(sign=1.0)
            bp.S = 0.0
        r = vm.dust_vs(enc, bp.push_dust(), (0.0, -3.2, 0.0))
        c = r["al"][::4]
        out[tag] = dict(alfa=float(c.sum()), vis=int((c > 0.02).sum()), rafaga=int(((r["isG"][::4] > 0.5) & (c > 0.02)).sum()))
    out["P0"] = r["P0"]
    return out


ref6 = estad(ENC)
hv = estad(vm.flip_v(vm.half_uv(ENC)))
dP = float(np.abs(hv["P0"] - ref6["P0"]).max())
ok6 = dP < 1e-9
for tag in ("calma", "rafaga"):
    a, b = ref6[tag], hv[tag]
    ok6 &= abs(a["alfa"] - b["alfa"]) < 0.06 * a["alfa"] and abs(a["vis"] - b["vis"]) < 0.06 * a["vis"] and \
        abs(a["rafaga"] - b["rafaga"]) <= max(3, 0.1 * a["rafaga"])
chk("V invertida + UV en fp16: posiciones exactas y mismas estadisticas (alfa total +-6 %, visibles +-6 %, polvo de "
    "rafaga +-10 %)", ok6, "sin invertir %s | invertida %s | |P0| %.1e"
    % ({k: v for k, v in ref6.items() if k != "P0"}, {k: v for k, v in hv.items() if k != "P0"}, dP))
# control negativo: la esquina y los bits en V (lo que NO se hizo) con la V invertida rompe todo
mal = dict(ENC)
mal["UV0"] = np.stack([np.full(NV, 0.5), ENC["UV0"][:, 0] / 4.0 + 0.125], 1)
mal["UV2"] = np.stack([ENC["UV2"][:, 1], ENC["UV2"][:, 0] / 4.0 + 0.125], 1)


def decod_mal(enc):
    e = dict(enc)
    e["UV0"] = np.stack([np.floor(enc["UV0"][:, 1] * 4.0), enc["UV0"][:, 0]], 1)
    e["UV2"] = np.stack([np.floor(enc["UV2"][:, 1] * 4.0), enc["UV2"][:, 0]], 1)
    return e


m_ok = estad(decod_mal(mal))
m_fl = estad(decod_mal(vm.flip_v(mal)))
rompe = (float(np.abs(m_fl["P0"] - m_ok["P0"]).max()) > 0.1) or abs(m_fl["rafaga"]["rafaga"] - m_ok["rafaga"]["rafaga"]) > 20
chk("control negativo: con la esquina y los bits en V, la V invertida SI rompe (el chequeo de arriba lo veria)", rompe,
    "|P0| %.2f cm; polvo de rafaga %d -> %d" % (float(np.abs(m_fl["P0"] - m_ok["P0"]).max()), m_ok["rafaga"]["rafaga"],
                                              m_fl["rafaga"]["rafaga"]))

print("\n%s" % ("TODO OK" if not fails else "%d FALLAS: %s" % (len(fails), fails)))
sys.exit(1 if fails else 0)
