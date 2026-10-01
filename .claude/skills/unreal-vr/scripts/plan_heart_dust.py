# -*- coding: utf-8 -*-
"""plan_heart_dust.py - PLAN (JSON) del material del POLVO del latido (M_HeartDust_SC + MI_HeartDust_SC), 2026-10-01.

Lee los Custom scripts/hlsl/AuraVS.hlsl y AuraPS.hlsl (codigo entero + la tabla ENTRADAS de la cabecera + salidas
adicionales) y los parametros/grupos de alma_aura_model.py (MAT, MAT_INTERNO, GRUPOS). Verifica que los parametros
declarados sean exactamente los que usan los Custom.
Escribe VR_Test/Saved/ClaudeScripts/Alma/alma_aura_build.json, que lee apply_alma_aura_material.py dentro de Unreal.
Es plan_vida_materials.py (seccion "dust", probada) con otra fuente.
Uso:  python plan_alma_aura.py
"""
import json
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import heart_dust_model as am  # noqa: E402

REPO = os.path.abspath(os.path.join(AQUI, "..", "..", "..", ".."))
HLSL = os.path.join(AQUI, "hlsl")
SALIDA = os.path.join(REPO, "VR_Test", "Saved", "ClaudeScripts", "Heart", "heart_dust_build.json")
CARPETA = "/Game/SoulCharger/Mechanics/Heart/Scape"


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
    params = [param(k, v, am.GRUPOS[k]) for k, v in am.MAT.items()]
    params += [param(k, v, am.GRUPOS[k]) for k, v in am.MAT_INTERNO.items()]
    customs = [leer_custom("HeartDustVS"), leer_custom("HeartDustPS")]
    nombres = {p["name"] for p in params}
    usados = {e["src"]["param"] for c in customs for e in c["inputs"] if e["src"]["kind"] == "param"}
    if nombres != usados:
        raise SystemExit("parametros sin uso %s / usados sin declarar %s" % (sorted(nombres - usados), sorted(usados - nombres)))
    if [len(c["inputs"]) for c in customs] != [17, 4]:
        raise SystemExit("entradas leidas: %s (esperaba 17 y 4)" % [len(c["inputs"]) for c in customs])
    plan = {"dust": {
        "material": CARPETA + "/M_HeartDust_SC",
        "instance": CARPETA + "/MI_HeartDust_SC",
        "mesh": CARPETA + "/SM_HeartDust_SC",
        "flags": {"shadingModel": "MSM_Unlit", "blendMode": "BLEND_AlphaComposite", "twoSided": True,
                  "bUseTranslucencyVertexFog": False, "floatPrecisionMode": "MFPM_Full_MaterialExpressionOnly"},
        "params": params,
        "customs": customs,
    }}
    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    with open(SALIDA, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=True, indent=1)
    for c in customs:
        print("%s: %d entradas, salidas extra %s, %d caracteres" % (c["desc"], len(c["inputs"]),
                                                                  [x["outputName"] for x in c["additionalOutputs"]], len(c["code"])))
    print("%d parametros -> %s" % (len(params), SALIDA))
    return 0


if __name__ == "__main__":
    sys.exit(main())
