# v_compila.py - verificador independiente (lente: correccion tecnica). Compila los tres Custom del valle v2
# con un envoltorio que imita la funcion que genera Unreal para un MaterialExpressionCustom
# (MaterialFloatN, FMaterialVertex/PixelParameters, View como ConstantBuffer<struct>), con:
#   - dxc del Windows SDK (DXIL, SM 6.0), HLSL 2018 y 2021, -WX
#   - dxc con el dxcompiler.dll de UE 5.8 (ShaderConductor) -> SPIR-V (el camino Vulkan de la Quest) + spirv-val
# No toca el repo: todo se escribe en esta carpeta.
import os, re, subprocess, sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
REPO = AQUI.parents[3]
HL = REPO / ".claude" / "skills" / "unreal-vr" / "scripts" / "hlsl"
SDK_DXC = r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64\dxc.exe"
UE_DXC = str(AQUI / "uedxc" / "dxc.exe")
SPVVAL = os.path.join(os.environ["LOCALAPPDATA"], r"Android\Sdk\ndk\27.2.12479018\shader-tools\windows-x86_64\spirv-val.exe")
FILES = {"ValleyHeightVS": ("vs", "float3"), "ValleyGradVS": ("vs", "float4"), "ValleyPS": ("ps", "float3")}
TMP = AQUI / "compila"
TMP.mkdir(exist_ok=True)


def entradas(txt):
    return re.findall(r"^//\s+\d+\s+(\w+)\s+(float[234]?)\s", txt, re.M)


def envoltorio(name):
    kind, ret = FILES[name]
    txt = (HL / (name + ".hlsl")).read_text(encoding="ascii")
    ins = entradas(txt)
    mf = {"float": "MaterialFloat", "float2": "MaterialFloat2", "float3": "MaterialFloat3", "float4": "MaterialFloat4"}
    head = ("#define MaterialFloat float\n#define MaterialFloat2 float2\n#define MaterialFloat3 float3\n"
            "#define MaterialFloat4 float4\n"
            "struct FViewUB { float4 Pad0; float GameTime; float PrevFrameGameTime; float2 Pad1; };\n"
            "ConstantBuffer<FViewUB> View : register(b0);\n")
    # parametros del material: uniformes (un cbuffer), como el Material uniform buffer
    uni = [(n, t) for n, t in ins if not ((kind == "vs" and n == "LP") or (kind == "ps" and n in ("VI1", "LPi", "CamL", "Dist")))]
    head += "cbuffer MaterialCB : register(b1)\n{\n" + "".join("  %s M_%s;\n" % (t, n) for n, t in uni) + "};\n"
    if kind == "vs":
        head += "struct FMaterialVertexParameters { float3 WorldPosition; float4 VertexColor; };\n"
        ptype = "FMaterialVertexParameters"
    else:
        head += "struct FMaterialPixelParameters { float4 SvPosition; float3 WorldPosition; };\n"
        ptype = "FMaterialPixelParameters"
    sig = ", ".join("%s %s" % (mf[t], n) for n, t in ins)
    fn = "%s CustomExpression0(%s Parameters, %s)\n{\n%s\n}\n" % (mf[ret], ptype, sig, txt)
    args = []
    for n, t in ins:
        if kind == "vs" and n == "LP":
            args.append("inLP")
        elif kind == "ps" and n in ("VI1", "LPi", "CamL", "Dist"):
            args.append("in" + n)
        else:
            args.append("M_" + n)
    if kind == "vs":
        main = ("float4 main(float3 inLP : ATTRIBUTE0, out float4 oVI : TEXCOORD0) : SV_Position\n{\n"
                "  FMaterialVertexParameters P = (FMaterialVertexParameters)0; P.WorldPosition = inLP;\n"
                "  %s o = CustomExpression0(P, %s);\n  oVI = %s;\n  return float4(inLP + o.xyz, 1.0);\n}\n"
                % (ret, ", ".join(args), "o" if ret == "float4" else "float4(o, 0.0)"))
    else:
        main = ("float4 main(float4 sv : SV_Position, float4 inVI1 : TEXCOORD0, float3 inLPi : TEXCOORD1, "
                "float3 inCamL : TEXCOORD2, float inDist : TEXCOORD3) : SV_Target0\n{\n"
                "  FMaterialPixelParameters P = (FMaterialPixelParameters)0; P.SvPosition = sv;\n"
                "  return float4(CustomExpression0(P, %s), 1.0);\n}\n" % ", ".join(args))
    return head + fn + main


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr).strip()


fallas = 0
for name, (kind, _) in FILES.items():
    src = TMP / ("ue_%s.hlsl" % name)
    src.write_text(envoltorio(name), encoding="ascii")
    for hv in ("2018", "2021"):
        rc, out = run([SDK_DXC, "-nologo", "-T", kind + "_6_0", "-E", "main", "-HV", hv, "-WX", "-O3",
                       "-Fo", str(TMP / ("%s_%s.dxil" % (name, hv))), str(src)])
        print(("OK    " if rc == 0 else "FALLA ") + "dxc SDK DXIL %s_6_0 HV%s -WX  %s" % (kind, hv, name) + ("" if rc == 0 else "\n" + out[-800:]))
        fallas += rc != 0
        spv = TMP / ("%s_%s.spv" % (name, hv))
        rc, out = run([UE_DXC, "-nologo", "-T", kind + "_6_0", "-E", "main", "-HV", hv, "-WX", "-O3", "-spirv",
                       "-fspv-target-env=vulkan1.1", "-Fo", str(spv), str(src)])
        ok = rc == 0
        msg = out[-800:] if not ok else ""
        if ok:
            rc2, out2 = run([SPVVAL, "--target-env", "vulkan1.1", str(spv)])
            ok, msg = rc2 == 0, out2[-800:]
        print(("OK    " if ok else "FALLA ") + "dxc UE5.8 -> SPIR-V vulkan1.1 HV%s -WX + spirv-val  %s" % (hv, name) + ("" if ok else "\n" + msg))
        fallas += not ok
    # desensamblado SPIR-V: buscar acceso dinamico a arreglos (OpAccessChain sobre variables Function de tipo array)
    rc, dis = run([SPVVAL.replace("spirv-val", "spirv-dis"), str(TMP / ("%s_2021.spv" % name))])
    arr = re.findall(r"OpTypeArray", dis)
    print("INFO  %s SPIR-V: OpTypeArray=%d  OpLoopMerge=%d  OpAccessChain=%d" % (
        name, len(arr), len(re.findall(r"OpLoopMerge", dis)), len(re.findall(r"OpAccessChain", dis))))
    (TMP / ("%s_2021.spvasm" % name)).write_text(dis, encoding="utf-8")
print("RESULTADO compilacion: " + ("TODO OK" if not fallas else "%d FALLAS" % fallas))
