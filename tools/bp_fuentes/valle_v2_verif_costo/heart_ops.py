# heart_ops.py - cuenta las instrucciones por vertice de la membrana de Heart SIN el corte por onda
# (aproximacion de la v2 medida: vertices ~5,4 ms con 78.849 vertices) para calibrar el costo de vertices
# del valle con la MISMA regla de conteo (dxc -O3, DXIL escalar). Solo LEE los .hlsl de Heart.
import re, subprocess, json
from pathlib import Path
import cost_ops as co   # reusa DXC, count_dxil (y corre sus conteos: no importa)

OUT = Path(__file__).resolve().parent
HL = co.HL2
KW = set("""float float2 float3 float4 int uint bool if else for while do return continue break true false
sin cos sincos exp exp2 log log2 sqrt rsqrt pow abs min max saturate clamp lerp step smoothstep frac floor ceil
fmod length normalize dot cross atan2 atan asin acos tan unroll loop""".split())
F4 = {"Beat", "BeatP", "OA", "OB"} | {"W%d" % i for i in range(8)} | {"B%d" % i for i in range(4)} | {"V%d" % i for i in range(4)}
F3 = {"LP"}


def inputs(body):
    code = re.sub(r"//.*", "", body)
    local = set(re.findall(r"\b(?:float[234]?|int)\s+(\w+)", code))
    local |= set(re.findall(r"\b(?:float[234]?|int)\s+\w+\s*,\s*(\w+)", code))
    for decl in re.findall(r"\bfloat[234]?\s+([\w\s,]+);", code):
        local |= set(w.strip() for w in decl.split(",") if re.fullmatch(r"\s*\w+\s*", w))
    ids = set(re.findall(r"(?<![\.\w])([A-Za-z_]\w*)\b", code))
    return sorted(i for i in ids - local - KW if i not in ("View", "Parameters"))


def wrap(body, ret):
    ins = inputs(body)
    typ = {n: ("float4" if n in F4 else "float3" if n in F3 else "float") for n in ins}
    cb = "\n".join("  %s cb_%s;" % (typ[n], n) for n in ins if n != "LP")
    args = ", ".join(("inLP" if n == "LP" else "cb_" + n) for n in ins)
    params = ", ".join("%s %s" % (typ[n], n) for n in ins)
    return ("struct FViewStub { float GameTime; };\ncbuffer ViewCB : register(b0) { FViewStub View; };\n"
            "cbuffer MatCB : register(b1)\n{\n%s\n};\nstruct FMaterialVertexParameters { float3 Dummy; };\n"
            "%s CustomExpression0(FMaterialVertexParameters Parameters, %s)\n{\n%s\n}\n"
            "float4 main(float3 inLP : POSITION) : SV_Position\n{\n  FMaterialVertexParameters P; P.Dummy = inLP;\n"
            "  %s o = CustomExpression0(P, %s);\n  return float4(inLP + o.xyz, 1.0 + %s);\n}\n"
            % (cb, ret, params, body, ret, args, "o.w" if ret == "float4" else "0.0"))


def spec(body, repl):
    for a, b in repl:
        n = body.count(a)
        assert n == 1, (a, n)
        body = body.replace(a, b)
    return body


CUT = "if (life < 0.001 || xa > 2.5 + Warp || xa < -2.5 * (1.0 + Tail) - Warp) { continue; }"
MEMB = [("if (Part > 2.5)", "if (false)"), ("if (Part > 1.5)", "if (false)"), ("if (Part > 0.5)", "if (false)"),
        ("if (pm == 1.0 || pm == 3.0)", "if (false)")]
rows = {}
for name, ret, repl in (
        ("HeartHeightVS", "float3", MEMB + [(CUT, "")]),
        ("HeartGradVS", "float4", MEMB + [(CUT, "")]),
        ("HeartHeightVS_con_corte", "float3", MEMB),
        ("HeartGradVS_con_corte", "float4", MEMB),
        ("HeartXVS", "float4", [("if (Part > 0.5 || pm == 1.0 || pm == 3.0)", "if (false)"), ("if (abs(xa) < 1.5 + Warp)", "if (true)")])):
    src_name = name.replace("_con_corte", "")
    body = (HL / (src_name + ".hlsl")).read_text(encoding="ascii", errors="replace")
    body = spec(body, repl)
    s, a, _ = co.compile_count(wrap(body, ret), "vs", "heart_" + name)
    rows[name] = {"sfu": sum(s.values()), "alu": a, "detalle": s}
    print("%-26s SFU %4d  ALU %5d  %s" % (name, sum(s.values()), a, s))
(OUT / "heart_ops.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
