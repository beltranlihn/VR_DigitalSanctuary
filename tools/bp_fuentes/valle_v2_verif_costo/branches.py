# branches.py - las ramas por radio (VS) y por distancia/parte (PS) SOBREVIVEN al optimizador, o se aplanan?
# Compila los Custom COMPLETOS (sin especializar) con dxc -O3 y con glslc -O (SPIR-V) y cuenta saltos condicionales
# y los transcendentales que quedan en bloques condicionales. Si una rama se aplana (if-conversion), todos los
# vertices/pixeles pagan el cuerpo: el costo por camino del constructor dejaria de valer.
import re, subprocess
from pathlib import Path
import cost_ops as co

OUT = Path(__file__).resolve().parent
for name, kind, ret in (("ValleyHeightVS", "vs", "float3"), ("ValleyGradVS", "vs", "float4"), ("ValleyPS", "ps", "float3")):
    ins, body = co.parse(co.HL2 / (name + ".hlsl"))
    src = OUT / "wrap" / ("full_" + name + ".hlsl")
    src.write_text(co.wrapper(ins, body, kind, ret), encoding="ascii")
    ll = OUT / "wrap" / ("full_" + name + ".ll")
    subprocess.run([co.DXC, "-nologo", "-T", kind + "_6_0", "-E", "main", "-O3", "-Fc", str(ll), str(src)], check=True, capture_output=True)
    txt = ll.read_text(errors="replace")
    fn = txt[txt.find("define void @main"):]
    blocks = re.split(r"\n(?=\d+:|; <label>:\d+)", fn)
    nbr = len(re.findall(r"br i1 ", fn))
    sfu_total = len(re.findall(r"dx\.op\.unary\.f32\(i32 (?:12|13|21|23|24|25)", fn))
    # transcendentales en el primer bloque (incondicionales)
    first = blocks[0]
    sfu_first = len(re.findall(r"dx\.op\.unary\.f32\(i32 (?:12|13|21|23|24|25)", first))
    print("DXIL  %-15s bloques %2d | saltos condicionales %2d | SFU total %3d, en el bloque de entrada %d"
          % (name, len(blocks), nbr, sfu_total, sfu_first))
    if co.GLSLC and co.SPVDIS:
        spv = OUT / "wrap" / ("full_" + name + ".spv")
        subprocess.run([co.GLSLC, "-x", "hlsl", "-fshader-stage=" + ("vert" if kind == "vs" else "frag"), "-fentry-point=main",
                        "--target-env=vulkan1.1", "-O", "-o", str(spv), str(src)], check=True, capture_output=True)
        d = subprocess.run([co.SPVDIS, str(spv)], capture_output=True, text=True).stdout
        print("SPIRV %-15s OpBranchConditional %2d | OpSelectionMerge %2d (DontFlatten %d, Flatten %d)"
              % (name, len(re.findall(r"OpBranchConditional", d)), len(re.findall(r"OpSelectionMerge", d)),
                 len(re.findall(r"OpSelectionMerge %\w+ DontFlatten", d)), len(re.findall(r"OpSelectionMerge %\w+ Flatten", d))))
