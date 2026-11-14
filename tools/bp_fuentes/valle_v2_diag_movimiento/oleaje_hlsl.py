# -*- coding: utf-8 -*-
"""oleaje_hlsl.py - arma y VERIFICA el oleaje en HLSL, sin tocar el repo.

1. Lee scripts/hlsl/ValleyHeightVS.hlsl y ValleyGradVS.hlsl del repo (solo lectura), les agrega 6 entradas
   (24-29: SwellAmp, SwellNear, SwellFar, SwellScale, SwellSpeed, SwellSeed) y el bloque del oleaje antes
   del return, y escribe ValleyHeightVS_oleaje.hlsl / ValleyGradVS_oleaje.hlsl en ESTA carpeta.
2. Compila cada uno con dxc (vs_6_0, -WX) y, si esta el NDK, glslc HLSL -> SPIR-V + spirv-val, con el mismo
   envoltorio que usa Valley_check.py (funcion CustomExpression0 + View.GameTime en un cbuffer).
3. Traduce los .hlsl a Python linea por linea y compara h y gradiente contra el modelo numpy
   (modelo_v1 + oleaje.ola), con la base v1 y con la base x5, y el gradiente contra diferencias finitas.
"""
import glob
import math
import os
import re
import subprocess
import tempfile

import numpy as np

import modelo_v1 as M
import oleaje as O

AQUI = os.path.dirname(os.path.abspath(__file__))
HL = os.path.abspath(os.path.join(AQUI, "..", "..", "..", "..", ".claude", "skills", "unreal-vr", "scripts", "hlsl"))
fails = []


def chk(lbl, ok, info=""):
    print(("OK    " if ok else "FALLA ") + lbl + ("  " + info if info else ""))
    if not ok:
        fails.append(lbl)


CAB = """//  24  SwellAmp    float   ScalarParameter SwellAmp    600 cm   (oleaje: amplitud maxima, lejos)
//  25  SwellNear   float   ScalarParameter SwellNear   1500 cm  (oleaje: 0 exacto a menos de esto)
//  26  SwellFar    float   ScalarParameter SwellFar    15000 cm (oleaje: amplitud plena desde aca)
//  27  SwellScale  float   ScalarParameter SwellScale  1        (multiplica las longitudes de onda)
//  28  SwellSpeed  float   ScalarParameter SwellSpeed  1        (multiplica la frecuencia: 1 = periodos 31-46 s)
//  29  SwellSeed   float   ScalarParameter SwellSeed   0 (grados; gira las 4 direcciones)"""

COMUN = """// ---- OLEAJE (propuesta v2): 4 ondas planas viajeras escritas una por una (sin bucles ni arreglos).
// 0 exacto a menos de SwellNear y detras de la cresta (1 - u2). El reloj se reduce con frac ANTES del sin.
float SWn = 1.0 / 2.95;
float kq = 6.2831853 / max(SwellScale, 0.05);
float tq = saturate((r - SwellNear) / max(SwellFar - SwellNear, 1.0));
float Wq = tq * tq * (3.0 - 2.0 * tq);
float Asw = SwellAmp * Wq * (1.0 - u2);
float oS, oC;
sincos(radians(SwellSeed), oS, oC);
float d0x = 0.93969262 * oC - 0.34202014 * oS;
float d0y = 0.93969262 * oS + 0.34202014 * oC;
float d1x = -0.99619470 * oC - 0.08715574 * oS;
float d1y = -0.99619470 * oS + 0.08715574 * oC;
float d2x = -0.25881905 * oC + 0.96592583 * oS;
float d2y = -0.25881905 * oS - 0.96592583 * oC;
float d3x = -0.08715574 * oC - 0.99619470 * oS;
float d3y = -0.08715574 * oS + 0.99619470 * oC;
float o0 = kq / 9000.0 * (d0x * x + d0y * y) + 0.0 - 6.2831853 * frac(SwellSpeed * Tt / 42.0);
float o1 = kq / 7000.0 * (d1x * x + d1y * y) + 2.3 - 6.2831853 * frac(SwellSpeed * Tt / 36.0);
float o2 = kq / 5500.0 * (d2x * x + d2y * y) + 4.6 - 6.2831853 * frac(SwellSpeed * Tt / 31.0);
float o3 = kq / 4000.0 * (d3x * x + d3y * y) + 1.1 - 6.2831853 * frac(SwellSpeed * Tt / 46.0);
"""
ALTURA = COMUN + """h += Asw * (1.00 * sin(o0) + 0.85 * sin(o1) + 0.70 * sin(o2) + 0.40 * sin(o3)) * SWn;
"""
GRAD = COMUN + """float so0, co0, so1, co1, so2, co2, so3, co3;
sincos(o0, so0, co0);
sincos(o1, so1, co1);
sincos(o2, so2, co2);
sincos(o3, so3, co3);
float sw = (1.00 * so0 + 0.85 * so1 + 0.70 * so2 + 0.40 * so3) * SWn;
float gwx = (1.00 / 9000.0 * co0 * d0x + 0.85 / 7000.0 * co1 * d1x + 0.70 / 5500.0 * co2 * d2x + 0.40 / 4000.0 * co3 * d3x) * kq * SWn;
float gwy = (1.00 / 9000.0 * co0 * d0y + 0.85 / 7000.0 * co1 * d1y + 0.70 / 5500.0 * co2 * d2y + 0.40 / 4000.0 * co3 * d3y) * kq * SWn;
float dWq = 6.0 * tq * (1.0 - tq) / max(SwellFar - SwellNear, 1.0);
h += Asw * sw;
gx += Asw * gwx + sw * SwellAmp * ((1.0 - u2) * dWq * x / rs - Wq * du2 * dex);
gy += Asw * gwy + sw * SwellAmp * ((1.0 - u2) * dWq * y / rs - Wq * du2 * dey);
"""


def armar(nombre, bloque, ret):
    src = open(os.path.join(HL, nombre + ".hlsl"), encoding="ascii").read().replace("\r\n", "\n")
    src = src.replace("ENTRADAS (23, en este orden", "ENTRADAS (29, en este orden")
    lin = [l for l in src.split("\n") if re.match(r"^//\s+23\s+MorphFar", l)]
    assert len(lin) == 1
    src = src.replace(lin[0], lin[0] + "\n" + CAB)
    assert src.count(ret) == 1, nombre
    src = src.replace(ret, bloque + ret)
    dst = os.path.join(AQUI, nombre + "_oleaje.hlsl")
    open(dst, "w", encoding="ascii", newline="\n").write(src)
    return src


SRC = {"ValleyHeightVS": armar("ValleyHeightVS", ALTURA, "return float3(0.0, 0.0, h);"),
       "ValleyGradVS": armar("ValleyGradVS", GRAD, "return float4(gx, gy, h, env * f);")}


def parse(txt):
    ins = re.findall(r"^//\s+(\d+)\s+(\w+)\s+(float[234]?)\s", txt, re.M)
    assert [int(i) for i, _, _ in ins] == list(range(1, len(ins) + 1))
    body = "\n".join(l for l in txt.split("\n") if not l.lstrip().startswith("//"))
    return [(n, t) for _, n, t in ins], body


# ---------------- estatico + compilacion
for name, txt in SRC.items():
    ins, body = parse(txt)
    probs = [n for n, _ in ins if not re.search(r"\b%s\b" % n, body)]
    if re.search(r"\b(for|while|do)\b", body): probs.append("bucle")
    if re.search(r"\w\s*\[", body): probs.append("arreglo")
    chk("estatico %s (%d entradas)" % (name, len(ins)), not probs, str(probs))
    ret = "float3" if name == "ValleyHeightVS" else "float4"
    cb = "\n".join("  %s cb_%s;" % (t, n) for n, t in ins)
    args = ["inLP"] + ["cb_" + n for n, _ in ins[1:]]
    wrap = ("struct FViewStub { float GameTime; };\ncbuffer ViewCB : register(b0) { FViewStub View; };\n"
            "cbuffer MatCB : register(b1)\n{\n%s\n};\nstruct FMaterialVertexParameters { float3 Dummy; };\n"
            "%s CustomExpression0(FMaterialVertexParameters Parameters, %s)\n{\n%s\n}\n\n"
            "float4 main(float3 inLP : POSITION) : SV_Position\n{\n  FMaterialVertexParameters P; P.Dummy = inLP;\n"
            "  %s o = CustomExpression0(P, %s);\n  return float4(inLP + o.xyz, 1.0 + %s);\n}\n"
            % (cb, ret, ", ".join("%s %s" % (t, n) for n, t in ins), body, ret, ", ".join(args),
               "o.w" if ret == "float4" else "0.0"))
    tmp = tempfile.mkdtemp(prefix="oleaje_")
    p = os.path.join(tmp, name + ".hlsl")
    open(p, "w", encoding="ascii").write(wrap)
    dxc = sorted(glob.glob(r"C:\Program Files (x86)\Windows Kits\10\bin\*\x64\dxc.exe"))
    if dxc:
        pr = subprocess.run([dxc[-1], "-nologo", "-T", "vs_6_0", "-E", "main", "-WX", "-O3", "-Fo", p + ".dxil", p],
                            capture_output=True, text=True)
        chk("dxc vs_6_0 -WX %s" % name, pr.returncode == 0, (pr.stdout + pr.stderr)[-300:] if pr.returncode else "")
    ndk = os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Android\Sdk\ndk\*\shader-tools\windows-x86_64")
    gl = sorted(glob.glob(os.path.join(ndk, "glslc.exe")))
    sv = sorted(glob.glob(os.path.join(ndk, "spirv-val.exe")))
    if gl:
        pr = subprocess.run([gl[-1], "-x", "hlsl", "-fshader-stage=vert", "-fentry-point=main", "--target-env=vulkan1.1",
                             "-O", "-Werror", "-o", p + ".spv", p], capture_output=True, text=True)
        ok = pr.returncode == 0
        out = pr.stdout + pr.stderr
        if ok and sv:
            pr = subprocess.run([sv[-1], "--target-env", "vulkan1.1", p + ".spv"], capture_output=True, text=True)
            ok, out = pr.returncode == 0, pr.stdout + pr.stderr
        chk("glslc HLSL->SPIR-V + spirv-val %s" % name, ok, out[-300:] if not ok else "")
    else:
        print("--    glslc no encontrado (Android NDK)")


# ---------------- traduccion a Python (escalares float64)
def ss(a, b, x):
    t = min(max((x - a) / (b - a), 0.0), 1.0)
    return t * t * (3 - 2 * t)


ENV = dict(sqrt=math.sqrt, sin=math.sin, cos=math.cos, floor=math.floor, radians=math.radians, max=max, min=min,
           saturate=lambda v: min(max(v, 0.0), 1.0), smoothstep=ss, frac=lambda v: v - math.floor(v),
           float3=lambda *a: a, float4=lambda *a: a)


def traducir(txt):
    ins, _ = parse(txt)
    py = []
    for raw in txt.split("\n"):
        l = raw.split("//")[0].strip()
        if not l:
            continue
        m = re.match(r"^if \((.*)\) \{ return (.*); \}$", l)
        if m:
            py += ["    if %s:" % m.group(1).replace("||", " or "), "        return %s" % m.group(2)]
            continue
        m = re.match(r"^sincos\((.*), (\w+), (\w+)\);$", l)
        if m:
            py.append("    %s, %s = sin(%s), cos(%s)" % (m.group(2), m.group(3), m.group(1), m.group(1)))
            continue
        if re.match(r"^float[234]? \w+(, \w+)+;$", l):
            continue
        m = re.match(r"^float[234]? (\w+) = (.*);$", l)
        if m:
            py.append("    %s = %s" % (m.group(1), m.group(2)))
            continue
        m = re.match(r"^(\w+) ([\+\-\*/]?=) (.*);$", l)
        if m:
            py.append("    %s %s %s" % m.groups())
            continue
        m = re.match(r"^return (.*);$", l)
        if m:
            py.append("    return %s" % m.group(1))
            continue
        raise SyntaxError(raw)
    ns = dict(ENV)
    exec("def F(View, %s):\n%s\n" % (", ".join(n for n, _ in ins), "\n".join(py)), ns)
    return ns["F"], [n for n, _ in ins]


class V:
    def __init__(self, **k): self.__dict__.update(k)


FH, NOMBRES = traducir(SRC["ValleyHeightVS"])
FG, _ = traducir(SRC["ValleyGradVS"])
rng = np.random.default_rng(11)
for base_lbl, base in (("base v1", {}), ("base x5", O.BASE_Q)):
    par = dict(M.P, **base)
    par.update(O.Q)
    par.update(Part=0.0, PerfMode=0.0)
    if base_lbl == "base v1":           # con la base chica, el oleaje a escala chica (para ejercitar todo)
        par.update(SwellNear=300.0, SwellFar=2500.0, SwellScale=0.25, SwellAmp=150.0)
    qol = {k: par[k] for k in O.Q}
    eh = eg = 0.0
    R = 4400.0 if base_lbl == "base v1" else 22000.0
    for _ in range(400):
        x, y, t = rng.uniform(-R, R), rng.uniform(-R, R), rng.uniform(0, 5000)
        for seed in (0.0, 37.0):
            par["SwellSeed"] = seed
            qol["SwellSeed"] = seed
            kw = {n: par[n] for n in NOMBRES[1:]}
            hh = FH(V(GameTime=t), V(x=x, y=y, z=0.0), **kw)[2]
            g = FG(V(GameTime=t), V(x=x, y=y, z=0.0), **kw)
            ref = float(M.h(np.array([x]), np.array([y]), t, base)[0] + O.ola(np.array([x]), np.array([y]), t, base, qol)[0])
            d = 0.01
            fx = (FH(V(GameTime=t), V(x=x + d, y=y, z=0.0), **kw)[2] - FH(V(GameTime=t), V(x=x - d, y=y, z=0.0), **kw)[2]) / (2 * d)
            fy = (FH(V(GameTime=t), V(x=x, y=y + d, z=0.0), **kw)[2] - FH(V(GameTime=t), V(x=x, y=y - d, z=0.0), **kw)[2]) / (2 * d)
            eh = max(eh, abs(hh - ref), abs(g[2] - hh))
            eg = max(eg, abs(fx - g[0]), abs(fy - g[1]))
    chk("HLSL traducido = numpy (%s, 800 puntos, t hasta 5000 s, SwellSeed 0 y 37)" % base_lbl, eh < 1e-3, "max |dh| %.1e cm (constantes de 8 cifras, como el HLSL del repo; tolerancia 1e-3 cm)" % eh)
    chk("gradiente HLSL = diferencias finitas (%s)" % base_lbl, eg < 2e-4, "max %.1e" % eg)
print("\nRESULTADO: " + ("TODO OK" if not fails else "FALLAS: %s" % fails))
