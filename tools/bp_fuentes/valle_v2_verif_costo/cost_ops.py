# cost_ops.py - verificador de costo (independiente) del valle v2 contra la v1.
# Cuenta instrucciones por CAMINO de cada Custom: especializa las ramas (if -> true/false), compila con
# dxc -O3 (DXIL) y cuenta en el listado: SFU (sin, cos, exp, log, sqrt, rsqrt, fdiv->rcp) y ALU (el resto).
# Tambien cuenta con glslc -O (SPIR-V) como segundo compilador. No toca el repo: todo va a esta carpeta.
import glob, os, re, subprocess, sys, json
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
HL2 = ROOT / ".claude" / "skills" / "unreal-vr" / "scripts" / "hlsl"
HL1 = ROOT / "VR_Test" / "Saved" / "ClaudeScripts" / "valle_v1_backup"
KITS = r"C:\Program Files (x86)\Windows Kits\10\bin\*\x64"
DXC = sorted(glob.glob(os.path.join(KITS, "dxc.exe")))[-1]
NDK = os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Android\Sdk\ndk\*\shader-tools\windows-x86_64")
GLSLC = (sorted(glob.glob(os.path.join(NDK, "glslc.exe"))) or [None])[-1]
SPVDIS = (sorted(glob.glob(os.path.join(NDK, "spirv-dis.exe"))) or [None])[-1]


def parse(path):
    txt = path.read_text(encoding="ascii", errors="replace").replace("\r\n", "\n")
    ins = re.findall(r"^//\s+(\d+)\s+(\w+)\s+(float[234]?)\s", txt, re.M)
    body = "\n".join(l for l in txt.split("\n") if not l.lstrip().startswith("//"))
    return [(n, t) for _, n, t in ins], body


def wrapper(ins, body, kind, ret):
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


SFU_OPS = {12: "cos", 13: "sin", 21: "exp", 23: "log", 24: "sqrt", 25: "rsqrt"}


def count_dxil(listing):
    sfu = {}
    alu = 0
    for line in listing.split("\n"):
        m = re.search(r"call float @dx\.op\.unary\.f32\(i32 (\d+)", line)
        if m:
            op = int(m.group(1))
            if op in SFU_OPS:
                sfu[SFU_OPS[op]] = sfu.get(SFU_OPS[op], 0) + 1
            else:
                alu += 1
            continue
        if re.search(r"= fdiv ", line):
            sfu["rcp"] = sfu.get("rcp", 0) + 1
            alu += 1
            continue
        if re.search(r"= (fadd|fsub|fmul|fcmp|select|fptosi|sitofp|and|or|xor|icmp|fneg) ", line):
            alu += 1
            continue
        if re.search(r"call float @dx\.op\.(binary|tertiary)\.f32", line):
            alu += 1
            continue
        if re.search(r"call float @dx\.op\.dot[234]\.f32", line):
            n = int(re.search(r"dot(\d)", line).group(1))
            alu += n
            continue
    return sfu, alu


def compile_count(src_text, kind, tag):
    src = OUT / "wrap" / (tag + ".hlsl")
    src.parent.mkdir(exist_ok=True)
    src.write_text(src_text, encoding="ascii")
    lst = OUT / "wrap" / (tag + ".ll")
    p = subprocess.run([DXC, "-nologo", "-T", kind + "_6_0", "-E", "main", "-O3", "-Fc", str(lst), str(src)],
                       capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(tag + ": " + p.stdout + p.stderr)
    sfu, alu = count_dxil(lst.read_text(errors="replace"))
    spv_n = None
    if GLSLC and SPVDIS:
        spv = OUT / "wrap" / (tag + ".spv")
        p2 = subprocess.run([GLSLC, "-x", "hlsl", "-fshader-stage=" + ("vert" if kind == "vs" else "frag"),
                             "-fentry-point=main", "--target-env=vulkan1.1", "-O", "-o", str(spv), str(src)],
                            capture_output=True, text=True)
        if p2.returncode == 0:
            d = subprocess.run([SPVDIS, str(spv)], capture_output=True, text=True).stdout
            ext = re.findall(r"OpExtInst %\w+ %\w+ (\w+)", d)
            arith = len(re.findall(r"= Op(FAdd|FSub|FMul|FDiv|FNegate|Dot|FOrd\w+|FUnord\w+|Select|VectorTimesScalar|ExtInst)\b", d))
            trans = sum(1 for e in ext if e in ("Sin", "Cos", "Exp", "Exp2", "Log", "Log2", "Sqrt", "InverseSqrt", "Pow"))
            spv_n = {"arith_ops": arith, "transc_extinst": trans,
                     "pow": ext.count("Pow"), "fdiv": len(re.findall(r"= OpFDiv\b", d))}
    return sfu, alu, spv_n


def specialize(body, repl):
    for pat, val in repl:
        n = len(re.findall(re.escape(pat), body))
        if n != 1:
            raise RuntimeError("patron %r aparece %d veces" % (pat, n))
        body = body.replace(pat, val)
    return body


ROWS = []


def run(label, path, kind, ret, repl):
    ins, body = parse(path)
    b = specialize(body, repl)
    sfu, alu, spv = compile_count(wrapper(ins, b, kind, ret), kind, label)
    nsfu = sum(sfu.values())
    ROWS.append({"camino": label, "sfu": nsfu, "sfu_detalle": sfu, "alu": alu, "spirv": spv})
    print("%-34s SFU %3d  ALU %4d   %s   spirv %s" % (label, nsfu, alu, json.dumps(sfu, sort_keys=True), spv))


OFF_VS = ("if (Part > 0.5 || pm == 1.0 || pm == 3.0)", "if (false)")
H = "if (r > HillNear && r < HillEnd)"
F = "if (r > FarIn && r < FB)"
S = "if (r > SwellNear && r < FB)"
for vs, ret in (("ValleyHeightVS", "float3"), ("ValleyGradVS", "float4")):
    p = HL2 / (vs + ".hlsl")
    run("v2 %s ninguna" % vs, p, "vs", ret, [OFF_VS, (H, "if (false)"), (F, "if (false)"), (S, "if (false)")])
    run("v2 %s oleaje" % vs, p, "vs", ret, [OFF_VS, (H, "if (false)"), (F, "if (false)"), (S, "if (true)")])
    run("v2 %s colinas+oleaje" % vs, p, "vs", ret, [OFF_VS, (H, "if (true)"), (F, "if (false)"), (S, "if (true)")])
    run("v2 %s lejos+oleaje" % vs, p, "vs", ret, [OFF_VS, (H, "if (false)"), (F, "if (true)"), (S, "if (true)")])
    run("v2 %s TODAS (peor)" % vs, p, "vs", ret, [OFF_VS, (H, "if (true)"), (F, "if (true)"), (S, "if (true)")])
    run("v1 %s" % vs, HL1 / (vs + ".hlsl"), "vs", ret, [OFF_VS])

P2 = [("if (pm >= 2.0 && Part > 0.5)", "if (false)"), ("if (pm >= 2.0)", "if (false)")]
FOG = "if (Part < 0.5 && Dist > FogStart)"
DZ = "if (abs(dz) > 1.0)"
SKY = "if (Part > 0.5 || fog > 0.0)"
PART = "if (Part > 0.5)\n{\n  float cosA"
MOON = "if (rho < 1.0 + me)"
p = HL2 / "ValleyPS.hlsl"
run("v2 PS suelo cercano", p, "ps", "float3", P2 + [(FOG, "if (false)"), (DZ, "if (true)"), (SKY, "if (false)"), (PART, "if (false)\n{\n  float cosA"), (MOON, "if (false)")])
run("v2 PS suelo lejano", p, "ps", "float3", P2 + [(FOG, "if (true)"), (DZ, "if (true)"), (SKY, "if (true)"), (PART, "if (false)\n{\n  float cosA"), (MOON, "if (false)")])
run("v2 PS cielo", p, "ps", "float3", P2 + [(FOG, "if (false)"), (DZ, "if (true)"), (SKY, "if (true)"), (PART, "if (true)\n{\n  float cosA"), (MOON, "if (false)")])
run("v2 PS cielo+luna", p, "ps", "float3", P2 + [(FOG, "if (false)"), (DZ, "if (true)"), (SKY, "if (true)"), (PART, "if (true)\n{\n  float cosA"), (MOON, "if (true)")])
p1 = HL1 / "ValleyPS.hlsl"
FOG1 = "if (Part < 0.5)\n{\n  fog"
run("v1 PS suelo (con niebla)", p1, "ps", "float3", P2 + [(FOG1, "if (true)\n{\n  fog"), (SKY, "if (true)"), (PART, "if (false)\n{\n  float cosA"), (MOON, "if (false)")])
run("v1 PS cielo", p1, "ps", "float3", P2 + [(FOG1, "if (false)\n{\n  fog"), (SKY, "if (true)"), (PART, "if (true)\n{\n  float cosA"), (MOON, "if (false)")])
(OUT / "cost_ops.json").write_text(json.dumps(ROWS, indent=1), encoding="utf-8")
print("escrito", OUT / "cost_ops.json")
