# -*- coding: utf-8 -*-
# BreathAir_check.py - verificacion de BreathAirVS / BreathAirPS (el aliento visible, 2026-09-28) SIN Unreal.
# Uso:  python BreathAir_check.py          (desde cualquier carpeta; no escribe nada en el repo)
#
# 1. Estatico: la tabla de ENTRADAS de la cabecera coincide con el codigo (toda entrada se usa), sin bucles, sin
#    arreglos, sin half; OutputType; el default escrito en la cabecera de cada ScalarParameter = el modelo
#    (breath_air_model.MAT) = la tabla 5.3 del plan (docs/PLAN-RESPIRACION-ENTORNO-2026-09-28.md).
# 2. Compila un wrapper que imita la funcion que Unreal genera para un Custom con salidas adicionales (inout):
#    dxc SM6 (-WX), fxc SM5, glslc HLSL -> SPIR-V Vulkan 1.1 (-Werror) + spirv-val (el camino de la Quest) y el PS
#    tambien con las ENTRADAS en half (-enable-16bit-types; asi las entrega la Quest; salidas en float como en
#    check_loving_hlsl.py). Cuenta [branch] -> DontFlatten en el SPIR-V.
# 3. Traduce MECANICAMENTE el HLSL a Python y lo compara con el modelo numpy (breath_air_model.vs / ps) en miles de
#    vertices con estados al azar (marcos girados, ojos, perillas no default).
# 4. Controles de comportamiento (en el HLSL traducido): neutro = nada dibujado; la cinta salta con alfa 0; lo
#    inhalado termina en la boca EXACTA; la pluma nace cerca de la boca; nada visible a < NearMin del ojo ni por
#    encima de ElevMax.
# 5. CONTROL NEGATIVO: copias mutadas del HLSL TIENEN que fallar la equivalencia; si no fallan, el verificador no
#    mide lo que dice.
# 6. V INVERTIDA (gotcha 302: el importador FBX de Unreal entrega V como 1 - V): las semillas codificadas como las
#    escribe gen_breath_air.py (encode_uv) y decodificadas como el VS, con la V invertida, dan las MISMAS estadisticas
#    (corrientes, disco centrado, alfa total, elevacion media). Control negativo: la codificacion de la v1 (b crudo en
#    V, bandera en V) con la V invertida SI cambia todo.
import glob, math, os, re, subprocess, sys, tempfile
from pathlib import Path

import numpy as np

HL = Path(__file__).resolve().parent
ROOT = HL.parents[4]
PLAN = ROOT / "docs" / "PLAN-RESPIRACION-ENTORNO-2026-09-28.md"
sys.path.insert(0, str(HL.parent))
import breath_air_model as am  # noqa: E402

FILES = {"BreathAirVS": ("vs", "float3", [("AirV", "float4")]), "BreathAirPS": ("ps", "float3", [("Alpha", "float")])}
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

# defaults de la cabecera = modelo = tabla del plan
hdr = {}
for name in FILES:
    for n, s in PARSED[name][2]:
        m = re.match(r"ScalarParameter (\w+) ([\-\d.]+)$", s)
        if m:
            hdr[m.group(1)] = float(m.group(2))
malos = [k for k, v in hdr.items() if k not in am.MAT or abs(am.MAT[k] - v) > 1e-12]
faltan = [k for k, v in am.MAT.items() if not isinstance(v, tuple) and k not in hdr]
chk("defaults de las cabeceras = breath_air_model.MAT (%d escalares)" % len(hdr), not malos and not faltan,
    "distintos %s; sin entrada %s" % (malos, faltan))


def num(t):
    return float(t.strip().replace("−", "-").replace(",", "."))


def tabla(seccion):
    """Filas de una tabla del plan: {nombre: (grupo, tipo, valor)}."""
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
                val = tuple(num(p) for p in re.split(r",\s+", m.group(1)))
            elif tipo.startswith("bool"):
                val = dflt.strip().lower() == "true"
            else:
                val = num(re.match(r"\s*([−\-]?[\d.,]+)", dflt).group(1))
            out[nom] = (grupo, tipo, val)
    return out


def compara_tabla(t, ref, ignorar_grupo=None):
    malos = []
    for k, v in ref.items():
        if k not in t:
            malos.append("%s falta en la tabla" % k)
        elif isinstance(v, tuple):
            if not np.allclose(v, t[k][2], atol=1e-9):
                malos.append("%s modelo %s tabla %s" % (k, v, t[k][2]))
        elif isinstance(v, bool) or isinstance(t[k][2], bool):
            if v != t[k][2]:
                malos.append("%s modelo %s tabla %s" % (k, v, t[k][2]))
        elif abs(t[k][2] - v) > 1e-9:
            malos.append("%s modelo %g tabla %g" % (k, v, t[k][2]))
    sobran = [k for k, (g, _, _) in t.items() if k not in ref and g != ignorar_grupo]
    return malos, sobran


if PLAN.exists() and "### 5.3" in PLAN.read_text(encoding="utf-8"):
    T53 = tabla("5.3")
    malos, sobran = compara_tabla(T53, am.MAT, ignorar_grupo="9 - Interno")
    chk("tabla 5.3 del plan = breath_air_model.MAT (%d parametros de autoria)" % len(am.MAT), not malos and not sobran,
        "; ".join(malos) + ("; sobran %s" % sobran if sobran else ""))
    internos = [k for k, (g, _, _) in T53.items() if g == "9 - Interno"]
    vsin = [n for n, s in PARSED["BreathAirVS"][2] if s.startswith("VectorParameter")]
    chk("los vectores 9 - Interno de la tabla = los VectorParameter del VS", sorted(internos) == sorted(vsin),
        "tabla %s / VS %s" % (sorted(internos), sorted(vsin)))
    T54 = tabla("5.4")
    malos, sobran = compara_tabla(T54, am.BP)
    chk("tabla 5.4 del plan = breath_air_model.BP (%d perillas del BP)" % len(am.BP), not malos and not sobran,
        "; ".join(malos) + ("; sobran %s" % sobran if sobran else ""))
else:
    print("--    tabla 5.3 del plan todavia no existe: se saltea")


# ============================ 2. compilacion ============================
def wrapper(name, half_ps=False):
    kind, ret, extra = FILES[name]
    _, ins, _, _, body, _ = PARSED[name]
    tp = (lambda t: t.replace("float", "half")) if half_ps else (lambda t: t)
    cb = "\n".join("  %s cb_%s;" % (t, n) for n, t in ins)
    args = ["cb_" + n for n, _ in ins]
    outs = ", ".join("inout %s %s" % (t, n) for n, t in extra)
    decl = "".join("  %s o_%s = (%s)0;\n" % (t, n, t) for n, t in extra)
    oargs = "".join(", o_%s" % n for n, _ in extra)
    osum = " + ".join("dot(o_%s, o_%s)" % (n, n) for n, _ in extra)
    params = ", ".join("%s %s" % (tp(t), n) for n, t in ins)
    if kind == "vs":
        args[0] = "inLP"
        entry = ("float4 main(float3 inLP : POSITION) : SV_Position\n{\n  FMaterialVertexParameters P; P.Dummy = inLP;\n%s"
                 "  %s o = CustomExpression0(P, %s%s);\n  return float4(inLP + o.xyz, 1.0 + %s);\n}\n"
                 % (decl, ret, ", ".join(args), oargs, osum))
        pstruct, ptype = "struct FMaterialVertexParameters { float3 Dummy; };", "FMaterialVertexParameters"
    else:
        args = ["(%s)%s" % (tp(t), a) for a, (n, t) in zip(args, ins)]
        args[0] = "(%s)inAirV" % tp("float4")
        entry = ("float4 main(float4 sv : SV_Position, float4 inAirV : TEXCOORD0) : SV_Target\n{\n  FMaterialPixelParameters P; P.SvPosition = sv;\n%s"
                 "  %s r = CustomExpression0(P, %s%s);\n  return float4(r, 1.0 + %s);\n}\n"
                 % (decl, ret, ", ".join(args), oargs, osum))
        pstruct, ptype = "struct FMaterialPixelParameters { float4 SvPosition; };", "FMaterialPixelParameters"
        # half: solo las ENTRADAS (asi las entrega la Quest); salidas y retorno en float, como check_loving_hlsl.py
    return ("cbuffer MatCB : register(b1)\n{\n%s\n};\n%s\n%s CustomExpression0(%s Parameters, %s, %s)\n{\n%s\n}\n\n%s"
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


tmp = Path(tempfile.mkdtemp(prefix="breathair_check_"))
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


ENV = dict(float2=_mk, float3=_mk, float4=_mk, sqrt=_f1(np.sqrt), sin=_f1(np.sin), cos=_f1(np.cos), tan=_f1(np.tan),
           exp=_f1(np.exp), floor=_f1(np.floor), abs=_f1(np.abs), radians=_f1(np.radians), degrees=_f1(np.degrees),
           frac=_f1(lambda x: x - np.floor(x)), saturate=_f1(lambda x: np.clip(x, 0.0, 1.0)), pow=_f2(np.power),
           max=_f2(np.maximum), min=_f2(np.minimum), smoothstep=_ss,
           step=lambda e, x: _w((np.asarray(_u(x)) >= _u(e)).astype(np.float64)),
           clamp=lambda x, a, b: _w(np.clip(_u(x), _u(a), _u(b))),
           lerp=lambda a, b, t: _w(_u(a) + (_u(b) - _u(a)) * _u(t)),
           dot=lambda a, b: float(np.dot(a.a, b.a)), length=lambda a: float(np.linalg.norm(a.a)),
           normalize=lambda a: Vec(a.a / np.linalg.norm(a.a)), cross=lambda a, b: Vec(np.cross(a.a, b.a)))


def translate_text(txt, ins, name, extra):
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
    exec(compile("def F(Parameters, %s):\n%s\n" % (", ".join(n for n, _ in ins), "\n".join(py)), name, "exec"), ns)
    return ns["F"]


VSF = translate_text(PARSED["BreathAirVS"][0], PARSED["BreathAirVS"][1], "BreathAirVS", FILES["BreathAirVS"][2])
PSF = translate_text(PARSED["BreathAirPS"][0], PARSED["BreathAirPS"][1], "BreathAirPS", FILES["BreathAirPS"][2])
VS_IN = [n for n, _ in PARSED["BreathAirVS"][1]]


def rot_frame(rng, tilt_deg=40.0):
    """un marco ortonormal girado al azar (como lo empujaria el BP con la cabeza girada)."""
    yaw, pitch, roll = (rng.uniform(-tilt_deg, tilt_deg) for _ in range(3))
    F, R, U = am.head_basis(yaw, pitch)
    rr = math.radians(roll)
    R2 = math.cos(rr) * R + math.sin(rr) * U
    U2 = math.cos(rr) * U - math.sin(rr) * R
    return F, R2, U2


def random_state(rng, full=False):
    A, R, U = rot_frame(rng)
    up = np.array(rot_frame(rng, 25.0)[2])
    pv = dict(AirT=np.array([rng.random(), rng.random(), rng.uniform(0.0, 1.5), rng.uniform(0.3, 1.0)]),
              AirE=np.array([rng.random(), rng.random(), rng.uniform(0.0, 0.8), rng.uniform(0.0, 0.8)]),
              MouthL=np.array([rng.uniform(4, 8), rng.uniform(-1, 1), -rng.uniform(7, 11)]),
              LagM=np.array([rng.uniform(0, 12), rng.uniform(-8, 8), -rng.uniform(4, 14)]),
              LagA=A, LagR=R, LagU=U, UpL=up)
    if full:
        pv["AirT"][3] = 1.0
        pv["AirE"][0] = pv["AirE"][1] = 1.0
    return pv


def mat_random(rng):
    q = dict(am.MAT)
    for k, v in q.items():
        if isinstance(v, tuple):
            continue
        q[k] = v * rng.uniform(0.8, 1.25) if v != 0 else v
    q["NearFull"] = max(q["NearFull"], q["NearMin"] + 5.0)
    q["SpeedFade1"] = max(q["SpeedFade1"], q["SpeedFade0"] + 5.0)
    return q


def eval_hlsl(fn, sd, k, corner, LP, pv, camL, q):
    # el HLSL recibe las semillas COMO ESTAN EN LA MALLA (encode_uv); el modelo, las semillas decodificadas
    uv = am.encode_uv({kk: (vv[k:k + 1] if isinstance(vv, np.ndarray) else vv) for kk, vv in sd.items()})
    args = dict(LP=Vec(LP), Crn=Vec(corner), Sa=Vec(uv["UV1"][0]), Sb=Vec(uv["UV2"][0]),
                Sc=Vec(uv["UV3"][0]), CamL=Vec(camL),
                AirT=Vec(pv["AirT"]), AirE=Vec(pv["AirE"]), MouthL=Vec(pv["MouthL"]), LagM=Vec(pv["LagM"]),
                LagA=Vec(pv["LagA"]), LagR=Vec(pv["LagR"]), LagU=Vec(pv["LagU"]), UpL=Vec(pv["UpL"]))
    for n in VS_IN:
        if n not in args:
            args[n] = q[n]
    r, loc = fn(None, **{n: args[n] for n in VS_IN})
    return r.a, loc["AirV"].a, loc


def compara(fn, n_states=12, per=160, seed=5, mats=True):
    rng = np.random.default_rng(seed)
    sd = am.seeds()
    N = sd["e"].shape[0]
    eo = ea = eh = 0.0
    nvis = 0
    for st in range(n_states):
        pv = random_state(rng, full=(st % 3 == 0))
        q = mat_random(rng) if (mats and st % 2 == 1) else dict(am.MAT)
        camL = np.array([rng.uniform(-3, 3), rng.choice([-3.2, 3.2]), rng.uniform(-2, 2)])
        ks = rng.choice(N, per, replace=False)
        corner = rng.integers(0, 2, (per, 2)).astype(float)
        LP = rng.uniform(-150, 150, (per, 3))
        sub = {k: v[ks] if isinstance(v, np.ndarray) else v for k, v in sd.items()}
        m = am.vs(sub, pv, camL, q, corner=corner, LP=LP)
        for j, k in enumerate(ks):
            off, airv, loc = eval_hlsl(fn, sd, k, corner[j], LP[j], pv, camL, q)
            eo = max(eo, float(np.abs(off - m["offs"][j]).max()))
            ea = max(ea, float(np.abs(airv - m["AirV"][j]).max()))
            eh = max(eh, abs(loc["hsz"] - m["hsz"][j]))
            nvis += int(m["al"][j] > 0.02)
    return eo, ea, eh, nvis


eo, ea, eh, nvis = compara(VSF)
chk("VS traducido = modelo numpy (12 estados al azar x 160 vertices, marcos girados, perillas no default)",
    eo < 1e-6 and ea < 1e-9 and eh < 1e-9 and nvis > 50,
    "|offset| %.1e cm  |AirV| %.1e  |medio lado| %.1e  (%d vertices con alfa > 0,02)" % (eo, ea, eh, nvis))

# PS
rng = np.random.default_rng(11)
ep = 0.0
for _ in range(400):
    airv = np.array([rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(0, 1), float(rng.integers(0, 2))])
    q = mat_random(rng)
    col, loc = PSF(None, AirV=Vec(airv), InColor=Vec(q["InColor"]), OutColor=Vec(q["OutColor"]))
    cm, am_ = am.ps(airv, q)
    ep = max(ep, float(np.abs(col.a - cm).max()), abs(loc["Alpha"] - float(am_)))
chk("PS traducido = modelo numpy (400 muestras)", ep < 1e-12, "max |dif| %.1e" % ep)


# ============================ 4. controles de comportamiento (HLSL traducido) ============================
sd = am.seeds()
N = sd["e"].shape[0]
base_pv = am.AirBP(np.zeros(3), 0.0, -2.0).push(np.zeros(3), 0.0, -2.0)


def hlsl_all(pv, camL=(0.0, 3.2, 0.0), q=None, idx=None):
    q = q or dict(am.MAT)
    idx = range(N) if idx is None else idx
    out = []
    for k in idx:
        off, airv, loc = eval_hlsl(VSF, sd, k, (1.0, 1.0), (0.0, 0.0, 0.0), pv, camL, q)
        out.append((loc["P"].a, float(loc["al"]), float(loc["hsz"]), float(loc["dist"]), float(loc["Dn"].a[2])))
    return out


sub_idx = list(range(0, N, 7))
# neutro: Glob 0 -> ningun quad con tamano
pv0 = dict(base_pv)
pv0["AirT"] = np.array([0.3, 0.6, 1.5, 0.0])
pv0["AirE"] = np.array([1.0, 1.0, 0.4, 0.4])
r = hlsl_all(pv0, idx=sub_idx)
chk("neutro: Glob = 0 -> todos los quads colapsados (0 pixeles)", all(h == 0.0 for _, _, h, _, _ in r))
pv0 = dict(base_pv)
pv0["AirT"] = np.array([0.3, 0.6, 1.5, 1.0])
pv0["AirE"] = np.array([0.0, 0.0, 0.4, 0.4])
r = hlsl_all(pv0, idx=sub_idx)
chk("neutro: Ein = Eout = 0 (PreviewBreath 0) -> todos los quads colapsados", all(h == 0.0 for _, _, h, _, _ in r))

# control positivo: con las envolventes llenas SI se dibuja algo, arriba y abajo de la cinta
pvf = dict(base_pv)
pvf["AirT"] = np.array([0.35, 0.35, 1.5, 1.0])
pvf["AirE"] = np.array([1.0, 1.0, 0.0, 0.0])
r = hlsl_all(pvf, idx=sub_idx)
vis = [x for x in r if x[1] > 0.02]
chk("control positivo: con Ein = Eout = 1 hay motas visibles", len(vis) > 60, "%d de %d" % (len(vis), len(r)))
# confort: ninguna visible cerca del ojo ni por encima de ElevMax
q = am.MAT
dmin = min(x[3] for x in vis)
elmax = max(math.degrees(math.asin(x[4])) for x in vis)
chk("confort: mota visible mas cercana al ojo >= NearMin (%g cm)" % q["NearMin"], dmin >= q["NearMin"], "%.1f cm" % dmin)
chk("confort: elevacion maxima de una mota visible <= ElevMax (%g grados)" % q["ElevMax"], elmax <= q["ElevMax"] + 1e-9,
    "%.2f grados" % elmax)

# lo inhalado termina en la boca EXACTA (s -> 1) aunque el marco con retardo este girado 30 grados
pvt = dict(pvf)
F30, R30, U30 = am.head_basis(30.0, -1.0)
pvt["LagA"], pvt["LagR"], pvt["LagU"] = F30, R30, U30
pvt["LagM"] = np.array([2.0, 3.0, -8.0])
ends = []
for k in range(0, sd["n_in"], 37):
    pv_k = dict(pvt)
    pv_k["AirT"] = np.array([(0.9995 - sd["e"][k]) % 1.0, 0.0, 1.5, 1.0])
    _, _, loc = eval_hlsl(VSF, sd, k, (1.0, 1.0), (0, 0, 0), pv_k, (0, 3.2, 0), dict(am.MAT))
    ends.append(float(np.linalg.norm(loc["P"].a - pv_k["MouthL"])))
chk("lo inhalado llega a la boca EXACTA con el marco girado 30 grados (s = 0,9995)", max(ends) < 2.0,
    "distancia maxima a la boca %.2f cm (jitter de llegada <= 1,7 cm)" % max(ends))
# la pluma nace a OutStart de la boca exacta (s = 0)
starts = []
for k in range(sd["n_in"], N, 53):
    pv_k = dict(pvt)
    pv_k["AirT"] = np.array([0.0, (1.0 - sd["e"][k]) % 1.0, 1.5, 1.0])
    _, _, loc = eval_hlsl(VSF, sd, k, (1.0, 1.0), (0, 0, 0), pv_k, (0, 3.2, 0), dict(am.MAT))
    starts.append(float(np.linalg.norm(loc["P"].a - pv_k["MouthL"])))
chk("la pluma nace a ~OutStart de la boca exacta (s = 0)", max(starts) < q["OutStart"] + 1.5 + 0.1 and min(starts) > q["OutStart"] - 0.1,
    "%.1f .. %.1f cm" % (min(starts), max(starts)))
# la cinta salta con alfa 0: alfa en s ~ 0 y s ~ 1
am_s0 = []
for s_probe in (0.0005, 0.9995):
    for k in list(range(0, sd["n_in"], 29)) + list(range(sd["n_in"], N, 41)):
        pv_k = dict(pvf)
        t = (s_probe - sd["e"][k]) % 1.0
        pv_k["AirT"] = np.array([t, t, 1.5, 1.0])
        _, airv, _ = eval_hlsl(VSF, sd, k, (1.0, 1.0), (0, 0, 0), pv_k, (0, 3.2, 0), dict(am.MAT))
        am_s0.append(airv[2])
chk("la cinta salta con alfa ~0 (s = 0,0005 y 0,9995, las dos corrientes)", max(am_s0) < 0.01, "alfa max %.4f" % max(am_s0))


# ============================ 5. control negativo: mutaciones ============================
MUT = [
    ("la inhalacion usa Tout", "float s = frac(e + AirT.x);", "float s = frac(e + AirT.y);", 1),
    ("b sin decodificar (2 v - 1)", "float2 ab = float2(Sb.x, 2.0 * Sb.y - 1.0);", "float2 ab = Sb.xy;", 1),
    ("la bandera de corriente leida de V", "float isOut = step(0.5, Sc.x);", "float isOut = step(0.5, Sc.y);", 1),
    ("sin el foco de la inhalacion", "(fp - 0.5 * (st + en)) * InFocus;", "(fp - 0.5 * (st + en)) * 0.0;", 1),
    ("sin compensar el alfa del tamano minimo", "al = al * kq * kq;", "al = al * 1.0;", 1),
    ("sin el fundido por elevacion", "al = al * (1.0 - smoothstep(se0, se1, Dn.z));", "al = al * 1.0;", 1),
    ("tilt con el signo cambiado", "float3 Ai = cos(ti) * A0 - sin(ti) * U0;", "float3 Ai = cos(ti) * A0 + sin(ti) * U0;", 1),
    ("NearMin/NearFull invertidos", "smoothstep(NearMin, NearFull, dist)", "smoothstep(NearFull, NearMin, dist)", 1),
    ("el volumen nace en la boca exacta y no en el marco con retardo", "float3 st = Mg + Ai", "float3 st = Mx + Ai", 1),
    ("sin el Glob", "al = al * AirT.w;", "al = al * 1.0;", 1),
    ("la pluma sin frente", "float fr = saturate((AirT.z - s) / 0.08);", "float fr = 1.0;", 1),
    ("billboard con el eje equivocado", "float3 up = cross(f, rt);", "float3 up = cross(rt, f);", 1),
    ("el remolino gira todo hacia el mismo lado", "* w * (2.0 * step(0.5, ph) - 1.0);", "* w;", 1),
]
txt0 = PARSED["BreathAirVS"][0]
for lbl, a, b, _ in MUT:
    assert a in txt0, "mutacion no aplicable: " + lbl
    fnm = translate_text(txt0.replace(a, b, 1), PARSED["BreathAirVS"][1], "mut", FILES["BreathAirVS"][2])
    eo2, ea2, eh2, _ = compara(fnm, n_states=6, per=120, seed=9)
    chk("mutacion detectada: " + lbl, eo2 > 1e-3 or ea2 > 1e-6 or eh2 > 1e-6,
        "|offset| %.1e  |AirV| %.1e" % (eo2, ea2))

# ============================ 6. V invertida del importador FBX ============================
def estad(sd_):
    """corrientes, disco y lo que se ve con PreviewBreath +-0,8 en 12 posiciones de la cinta (ojo izquierdo)."""
    out = dict(n_in=int(np.sum(sd_["flag"] < 0.5)), b_media=float(np.mean(sd_["b"])),
               b_rango=(float(sd_["b"].min()), float(sd_["b"].max())))
    for pb in (0.8, -0.8):
        tot, el, w = 0.0, 0.0, 0.0
        for T in np.linspace(0.04, 0.96, 12):
            pv = am.preview_push({"PreviewBreath": pb, "PreviewAirT": T})
            r = am.vs(sd_, pv, camL=np.array([0.0, -3.2, 0.0]))
            tot += float(r["al"].sum())
            el += float(np.sum(r["al"] * np.degrees(np.arcsin(np.clip(r["sinEl"], -1, 1)))))
            w += float(r["al"].sum())
        out["alfa%+.1f" % pb] = tot / 12
        out["elev%+.1f" % pb] = el / max(w, 1e-9)
    return out


def _r(d):
    return {k: (round(v, 2) if isinstance(v, float) else v) for k, v in d.items()}


sd0 = am.seeds()
ref6 = estad(am.decode_uv(am.encode_uv(sd0)))
flp = estad(am.decode_uv(am.flip_v(am.encode_uv(sd0))))
difs = [flp["n_in"] == ref6["n_in"], abs(flp["b_media"]) < 0.03, flp["b_rango"][0] < -0.95 and flp["b_rango"][1] > 0.95]
for kk in ("alfa+0.8", "alfa-0.8"):
    difs.append(abs(flp[kk] - ref6[kk]) < 0.06 * ref6[kk])
for kk in ("elev+0.8", "elev-0.8"):
    difs.append(abs(flp[kk] - ref6[kk]) < 1.0)
chk("V invertida (importador FBX): las estadisticas no cambian (corrientes, disco centrado, alfa total +-6 %, "
    "elevacion media +-1 grado)", all(difs), "sin invertir %s | invertida %s" % (_r(ref6), _r(flp)))
# control negativo: la codificacion de la v1 (b crudo en V, bandera en V) con la V invertida
v1 = dict(sd0)
v1["u"], v1["b"], v1["flag"] = 1.0 - sd0["u"], 1.0 - sd0["b"], 1.0 - sd0["flag"]
mal = estad(v1)
chk("control negativo: con la codificacion de la v1 la V invertida SI cambia todo (el chequeo de arriba lo veria)",
    mal["n_in"] != ref6["n_in"] and abs(mal["b_media"]) > 0.5 and abs(mal["alfa-0.8"] - ref6["alfa-0.8"]) > 0.3 * ref6["alfa-0.8"],
    "v1 invertida: inhalar %d (de %d), b medio %.2f, alfa de la pluma %.0f (de %.0f)"
    % (mal["n_in"], ref6["n_in"], mal["b_media"], mal["alfa-0.8"], ref6["alfa-0.8"]))

print("\n%s" % ("TODO OK" if not fails else "%d FALLAS: %s" % (len(fails), fails)))
sys.exit(1 if fails else 0)
