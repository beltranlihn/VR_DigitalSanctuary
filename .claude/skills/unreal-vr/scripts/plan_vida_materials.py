# -*- coding: utf-8 -*-
"""plan_vida_materials.py - arma el PLAN de construccion de los materiales de la CAPA DE VIDA en JSON (2026-09-28).

Lee:
  - los Custom (scripts/hlsl/DustVS.hlsl, DustPS.hlsl, GustLeanVS.hlsl): el CODIGO entero, la tabla ENTRADAS de la
    cabecera (nombre, tipo y de donde sale cada entrada) y las salidas adicionales;
  - los parametros y sus grupos de scripts/vida_model.py (MAT, MAT_INTERNO, GRUPOS, GUST_MAT). Vida_check.py verifica
    que las tablas 5.2 y 6.3 del plan (docs/PLAN-VIDA-VALLE-2026-09-28.md) sean exactamente estas.
Escribe VR_Test/Saved/ClaudeScripts/vida/vida_build.json, que leen dentro de Unreal (AssetTools.read_file):
  - apply_vida_dust_material.py   (arma M_ValleyDust_SC + MI_ValleyDust_SC: seccion "dust")
  - apply_vida_gust_valley.py     (agrega GustLeanVS y 5 parametros a M_BreathValley_SC: seccion "valley")
Fuentes de una entrada: LocalPosition · TexCoord N · CameraPositionWS -> TransformPosition (World -> Local) ·
VectorParameter X, pin RGB|RGBA · ScalarParameter X · VertexInterpolator, pin PS · Custom <Description>.
Uso:  python plan_vida_materials.py
"""
import json
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import vida_model as vm  # noqa: E402

REPO = os.path.abspath(os.path.join(AQUI, "..", "..", "..", ".."))
HLSL = os.path.join(AQUI, "hlsl")
SALIDA = os.path.join(REPO, "VR_Test", "Saved", "ClaudeScripts", "vida", "vida_build.json")
CARPETA = "/Game/SoulCharger/Mechanics/Breath/Life"
VALLE = "/Game/SoulCharger/Mechanics/Breath/Valley/M_BreathValley_SC"


def fuente(t):
    t = t.strip()
    m = re.match(r"(Scalar|Vector)Parameter (\w+)(?:, pin (RGBA|RGB|XYZ))?", t)
    if m:
        return {"kind": "param", "param": m.group(2), "vector": m.group(1) == "Vector", "pin": m.group(3) or ""}
    if t.startswith("LocalPosition"):
        return {"kind": "localpos"}
    m = re.match(r"TexCoord (\d)", t)
    if m:
        return {"kind": "texcoord", "index": int(m.group(1))}
    if t.startswith("CameraPositionWS -> TransformPosition (World -> Local)"):
        return {"kind": "campos_local"}
    if t.startswith("VertexInterpolator, pin PS"):
        return {"kind": "vi"}
    m = re.match(r"Custom (\w+)", t)
    if m:
        return {"kind": "custom", "desc": m.group(1)}
    raise SystemExit("fuente desconocida: " + t)


def leer_custom(nombre):
    codigo = open(os.path.join(HLSL, nombre + ".hlsl"), encoding="utf-8").read().replace("\r\n", "\n")
    entradas = []
    for m in re.finditer(r"^//\s+(\d+)\s+(\w+)\s+(float[234]?)\s+(.+?)(?:\s{2,}.*)?$", codigo, re.M):
        entradas.append({"name": m.group(2), "type": m.group(3), "src": fuente(m.group(4))})
    extra = []
    m = re.search(r"additionalOutputs: (\w+) (CMOT_Float\d)", codigo)
    if m:
        extra.append({"outputName": m.group(1), "outputType": m.group(2)})
    cmot = re.search(r"OutputType (CMOT_Float\d)", codigo).group(1)
    return {"desc": nombre, "outputType": cmot, "additionalOutputs": extra, "code": codigo, "inputs": entradas}


def param(nombre, valor, grupo):
    if isinstance(valor, tuple):
        v = list(valor) + [1.0] * (4 - len(valor))
        return {"name": nombre, "kind": "vector", "default": v, "group": grupo}
    return {"name": nombre, "kind": "scalar", "default": float(valor), "group": grupo}


def main():
    dparams = [param(k, v, vm.GRUPOS[k]) for k, v in vm.MAT.items()]
    dparams += [param(k, v, vm.GRUPOS[k]) for k, v in vm.MAT_INTERNO.items()]
    dcustoms = [leer_custom("DustVS"), leer_custom("DustPS")]
    vparams = [param(k, v, vm.GRUPO_VALLE) for k, v in vm.GUST_MAT.items()]
    vcustom = leer_custom("GustLeanVS")
    nombres = {p["name"] for p in dparams}
    usados = {e["src"]["param"] for c in dcustoms for e in c["inputs"] if e["src"]["kind"] == "param"}
    if nombres != usados:
        raise SystemExit("parametros del polvo sin uso %s / usados sin declarar %s" % (sorted(nombres - usados), sorted(usados - nombres)))
    vnombres = {p["name"] for p in vparams}
    vusados = {e["src"]["param"] for e in vcustom["inputs"] if e["src"]["kind"] == "param"}
    if not vnombres <= vusados or vusados - vnombres != {"Part"}:
        raise SystemExit("parametros del valle: declarados %s usados %s" % (sorted(vnombres), sorted(vusados)))
    plan = {
        "dust": {
            "material": CARPETA + "/M_ValleyDust_SC",
            "instance": CARPETA + "/MI_ValleyDust_SC",
            "mesh": CARPETA + "/SM_ValleyDust_SC",
            "flags": {"shadingModel": "MSM_Unlit", "blendMode": "BLEND_AlphaComposite", "twoSided": True,
                      "bUseTranslucencyVertexFog": False},
            "params": dparams,
            "customs": dcustoms,
        },
        "valley": {
            "material": VALLE,
            "params": vparams,
            "custom": vcustom,
            "vi_desc": "V_VI0",
            "grad_desc": "ValleyGradVS",
            "lp_desc": "V_LP",
        },
    }
    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    with open(SALIDA, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=True, indent=1)
    print("polvo: %d parametros (%d escalares, %d vectores)" % (len(dparams), sum(p["kind"] == "scalar" for p in dparams),
                                                                sum(p["kind"] == "vector" for p in dparams)))
    for c in dcustoms + [vcustom]:
        print("%s: %d entradas, salidas extra %s, %d caracteres de codigo"
              % (c["desc"], len(c["inputs"]), [x["outputName"] for x in c["additionalOutputs"]], len(c["code"])))
    print("valle: %d parametros nuevos (grupo %s)" % (len(vparams), vm.GRUPO_VALLE))
    print("escrito: " + SALIDA)
    return 0


if __name__ == "__main__":
    sys.exit(main())
