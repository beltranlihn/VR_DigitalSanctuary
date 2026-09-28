# -*- coding: utf-8 -*-
"""check_loving_hlsl.py - compila SIN el editor el codigo compuesto de cada Custom de Loving.

Envuelve cada VR_Test/Saved/ClaudeScripts/Loving/composed/<Custom>.hlsl como lo hace Unreal
(una funcion con las entradas del nodo y las salidas extra como `inout`; `ResolvedView` y
`Parameters.SvPosition` simulados) y lo compila con el DXC del Windows SDK:
  - DXIL (vs_6_0 / ps_6_0)            -> errores de sintaxis y de tipos
  - SPIR-V (-spirv, como el camino Vulkan del Quest) — solo si el DXC lo trae; el del Windows
    SDK NO (se omite con aviso). El de un release de DirectXShaderCompiler o del Vulkan SDK si.
  - con -enable-16bit-types y las entradas del PIXEL shader en half (el Quest las entrega asi)
No reemplaza al compilador de Unreal (MaterialTemplate, permutaciones mobile), pero atrapa
en segundos lo que antes costaba una ventana de editor.

Uso:  python check_loving_hlsl.py            (todos)
      python check_loving_hlsl.py LovingArmVS
Requiere haber corrido compose_loving.py antes.
"""
import glob
import os
import re
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", "..", ".."))
WRAP_DIR = os.path.join(RAIZ, "VR_Test", "Shaders", "Loving", "wrappers")
COMP_DIR = os.path.join(RAIZ, "VR_Test", "Saved", "ClaudeScripts", "Loving", "composed")
OUT_DIR = os.path.join(RAIZ, "VR_Test", "Saved", "ClaudeScripts", "Loving", "check")

TIPOS = {"Float1": "float", "Float2": "float2", "Float3": "float3", "Float4": "float4"}
FLOAT3_IN = {"LocalPos", "V", "Ld", "Nrm", "Misc", "Rel"}   # el resto de las entradas son float4
FLOAT2_IN = {"Misc2", "Aoc"}


def dxc():
    cands = sorted(glob.glob(r"C:\Program Files (x86)\Windows Kits\10\bin\*\x64\dxc.exe"))
    if not cands:
        raise SystemExit("no encuentro dxc.exe del Windows SDK")
    return cands[-1]


def cabecera(txt, clave):
    m = re.search(r"// @%s ([^\n]*)" % clave, txt)
    return [x.strip() for x in m.group(1).split(",")] if m else []


def tipo_in(n):
    return "float3" if n in FLOAT3_IN else ("float2" if n in FLOAT2_IN else "float4")


def arnes(nombre, half_ps):
    wrap = open(os.path.join(WRAP_DIR, nombre + ".hlsl"), encoding="utf-8").read()
    code = open(os.path.join(COMP_DIR, nombre + ".hlsl"), encoding="utf-8").read()
    ins = cabecera(wrap, "inputs")
    outs = [o.split(":") for o in cabecera(wrap, "outputs")]
    ret_t = TIPOS[[t for n, t in outs if n == "return"][0]]
    extra = [(n, TIPOS[t]) for n, t in outs if n != "return"]
    es_ps = nombre.endswith("PS")
    # el struct de la libreria va a nivel de archivo; el resto es el cuerpo de la funcion
    corte = code.index("};\n") + 3
    lib, cuerpo = code[:corte], code[corte:]
    tin = lambda n: (tipo_in(n).replace("float", "half") if (es_ps and half_ps) else tipo_in(n))
    params = ["FParams Parameters"] + ["%s %s" % (tin(n), n) for n in ins] + ["inout %s %s" % (t, n) for n, t in extra]
    h = []
    h.append("struct FResolvedView { float GameTime; };")
    h.append("cbuffer CB { FResolvedView ResolvedView; float4 Blob[64]; };")
    h.append("struct FParams { float4 SvPosition; };")
    h.append(lib)
    h.append("%s Custom(%s)\n{\n%s\n}" % (ret_t, ", ".join(params), cuerpo))
    # punto de entrada: las entradas salen del cbuffer para que nada se pliegue a constante
    args = []
    for i, n in enumerate(ins):
        t = tin(n)
        comp = {"float3": ".xyz", "float2": ".xy", "float4": "", "half3": ".xyz", "half2": ".xy", "half4": ""}[t]
        args.append("(%s)Blob[%d]%s" % (t, i, comp))
    decl = "".join("    %s o_%s = (%s)0;\n" % (t, n, t) for n, t in extra)
    call = "Custom(P, %s%s)" % (", ".join(args), "".join(", o_%s" % n for n, _ in extra))
    suma = "".join(" + dot(o_%s, o_%s)" % (n, n) for n, _ in extra)
    if es_ps:
        h.append("float4 main(float4 pos : SV_Position) : SV_Target\n{\n    FParams P; P.SvPosition = pos;\n%s    %s r = %s;\n    return float4(r.xyz%s, 1.0);\n}"
                 % (decl, ret_t, call, "" if not extra else " * (1.0" + suma + ")"))
    else:
        h.append("float4 main(float4 pos : POSITION) : SV_Position\n{\n    FParams P; P.SvPosition = pos;\n%s    %s r = %s;\n    return float4(pos.xyz + r%s, 1.0);\n}"
                 % (decl, ret_t, call, suma))
    return "\n".join(h), es_ps


def compilar(nombre, exe):
    os.makedirs(OUT_DIR, exist_ok=True)
    fallas = []
    for variante in ("fp32", "half_ps"):
        src, es_ps = arnes(nombre, variante == "half_ps")
        if variante == "half_ps" and not es_ps:
            continue
        ruta = os.path.join(OUT_DIR, "%s_%s.hlsl" % (nombre, variante))
        open(ruta, "w", encoding="utf-8").write(src)
        perfil = "ps_6_2" if es_ps else "vs_6_2"
        for extra in ([], ["-spirv"]):
            cmd = [exe, "-nologo", "-T", perfil, "-E", "main", "-HV", "2021", ruta, "-Fo", ruta + ".bin"] + extra
            if variante == "half_ps":
                cmd.append("-enable-16bit-types")
            p = subprocess.run(cmd, capture_output=True, text=True)
            tag = "%s %s %s" % (variante, perfil, "spirv" if extra else "dxil")
            if p.returncode != 0:
                msg = (p.stderr or p.stdout).strip()
                if "SPIR-V CodeGen not available" in msg:
                    print("  skip %-22s (el DXC del Windows SDK no trae SPIR-V)" % tag)
                    continue
                fallas.append((tag, msg))
            else:
                warn = [l for l in (p.stderr or "").splitlines() if "warning" in l]
                print("  ok   %-22s %s" % (tag, ("(%d warnings)" % len(warn)) if warn else ""))
    return fallas


def copia_caustic():
    """F5 (2026-09-28): LovingLib::Caustic es COPIA LITERAL de FluidLib::Caustic (la luz del agua sobre la celula
    tiene que ser la de las celulas medias). Si la libreria de estos wrappers trae un bloque Caustic, se compara
    su codigo sin comentarios con el de VR_Test/Shaders/Fluid/FluidLib.ush: distinto = FALLA."""
    lib = os.path.join(os.path.dirname(WRAP_DIR), "LovingLib.ush")
    flu = os.path.join(os.path.dirname(os.path.dirname(WRAP_DIR)), "Fluid", "FluidLib.ush")
    if not (os.path.isfile(lib) and os.path.isfile(flu)):
        return []

    def cuerpo(p):
        m = re.search(r"// @fn Caustic[^\n]*\n(.*?)// @end", open(p, encoding="utf-8").read(), re.S)
        if not m:
            return None
        return "\n".join(l.split("//")[0].rstrip() for l in m.group(1).splitlines()
                         if l.strip() and not l.strip().startswith("//"))

    a = cuerpo(lib)
    if a is None:
        return []
    if a != cuerpo(flu):
        return [("Caustic", "LovingLib::Caustic NO es copia literal de FluidLib::Caustic: cambiar las dos en el mismo commit")]
    print("Caustic: copia literal de FluidLib (ok)")
    return []


def _args():
    """--wrappers/--comp/--out opcionales (relativas a la raiz, como compose_loving.py); sin ellos = Loving."""
    global WRAP_DIR, COMP_DIR, OUT_DIR
    nombres, a = [], sys.argv[1:]
    i = 0
    while i < len(a):
        if a[i] in ("--wrappers", "--comp", "--out") and i + 1 < len(a):
            v = a[i + 1] if os.path.isabs(a[i + 1]) else os.path.join(RAIZ, a[i + 1])
            if a[i] == "--wrappers": WRAP_DIR = v
            elif a[i] == "--comp": COMP_DIR = v
            else: OUT_DIR = v
            i += 2
        else:
            nombres.append(a[i]); i += 1
    return nombres


def main():
    nombres = _args()
    exe = dxc()
    nombres = nombres or sorted(os.path.splitext(os.path.basename(f))[0] for f in glob.glob(os.path.join(WRAP_DIR, "*.hlsl")))
    total = 0
    for n in nombres:
        print(n)
        for tag, msg in compilar(n, exe):
            total += 1
            print("  FAIL %s\n%s" % (tag, "\n".join("       " + l for l in msg.splitlines()[:25])))
    for tag, msg in copia_caustic():
        total += 1
        print("  FAIL %s\n       %s" % (tag, msg))
    print("\n%s" % ("TODO COMPILA" if total == 0 else "%d FALLAS" % total))
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
