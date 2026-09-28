# -*- coding: utf-8 -*-
"""plan_breath_air_material.py - arma el PLAN de construccion de M_BreathAir_SC (el aliento visible) en JSON.

Lee (como plan_valley_material.py para el valle):
  - los dos Custom (scripts/hlsl/BreathAirVS.hlsl, BreathAirPS.hlsl): el CODIGO entero, la tabla ENTRADAS de la
    cabecera (nombre, tipo y de donde sale cada entrada) y las salidas adicionales;
  - la tabla de parametros 5.3 de docs/PLAN-RESPIRACION-ENTORNO-2026-09-28.md (nombre, tipo, default, grupo).
Escribe VR_Test/Saved/ClaudeScripts/aliento/breath_air_build.json, que apply_breath_air_material.py lee con
AssetTools.read_file dentro de Unreal. Asi el material se arma sin tipear a mano ni el codigo ni los parametros.

Fuentes de una entrada: LocalPosition · TexCoord N · CameraPositionWS -> TransformPosition (World -> Local) ·
VectorParameter X, pin RGB|RGBA · ScalarParameter X · VertexInterpolator, pin PS.
Uso:  python plan_breath_air_material.py
"""
import json
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(AQUI, "..", "..", "..", ".."))
HLSL = os.path.join(AQUI, "hlsl")
SPEC = os.path.join(REPO, "docs", "PLAN-RESPIRACION-ENTORNO-2026-09-28.md")
SALIDA = os.path.join(REPO, "VR_Test", "Saved", "ClaudeScripts", "aliento", "breath_air_build.json")
CARPETA = "/Game/SoulCharger/Mechanics/Breath/Air"

CUSTOMS = [("BreathAirVS", "CMOT_Float3"), ("BreathAirPS", "CMOT_Float3")]


def num(s):
    return float(s.strip().replace("−", "-").replace(",", "."))


def leer_parametros():
    params = []
    en = False
    for linea in open(SPEC, encoding="utf-8"):
        if linea.startswith("### 5.3"):
            en = True
            continue
        if en and linea.startswith("### "):
            break
        if not en or not linea.startswith("| `"):
            continue
        cols = [c.strip() for c in linea.strip().strip("|").split("|")]
        grupo, nombre, tipo, dflt = cols[0].strip("`"), cols[1].strip("`"), cols[2], cols[3]
        if tipo.startswith("vector"):
            m = re.search(r"\(([^)]*)\)", dflt)
            valor = [num(p) for p in re.split(r",\s+", m.group(1))]
            if len(valor) == 3:
                valor.append(1.0)
            params.append({"name": nombre, "kind": "vector", "default": valor, "group": grupo})
        else:
            m = re.match(r"\s*([−\-]?[\d.,]+)", dflt)
            params.append({"name": nombre, "kind": "scalar", "default": num(m.group(1)), "group": grupo})
    return params


def fuente(t):
    t = t.strip()
    m = re.match(r"(Scalar|Vector)Parameter (\w+)(?:, pin (RGBA|RGB))?", t)
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
    return codigo, entradas, extra


def main():
    params = leer_parametros()
    nombres = {p["name"] for p in params}
    customs = []
    for nombre, salida in CUSTOMS:
        codigo, entradas, extra = leer_custom(nombre)
        for e in entradas:
            if e["src"]["kind"] == "param" and e["src"]["param"] not in nombres:
                raise SystemExit("%s: la entrada %s usa el parametro %s, que no esta en la tabla 5.3" % (nombre, e["name"], e["src"]["param"]))
        customs.append({"desc": nombre, "outputType": salida, "additionalOutputs": extra, "code": codigo, "inputs": entradas})
    usados = {e["src"]["param"] for c in customs for e in c["inputs"] if e["src"]["kind"] == "param"}
    sin_uso = sorted(nombres - usados)
    if sin_uso:
        raise SystemExit("parametros de la tabla 5.3 que ningun Custom usa: %s" % sin_uso)
    plan = {
        "material": CARPETA + "/M_BreathAir_SC",
        "instance": CARPETA + "/MI_BreathAir_SC",
        "mesh": CARPETA + "/SM_BreathAir_SC",
        "flags": {"shadingModel": "MSM_Unlit", "blendMode": "BLEND_AlphaComposite", "twoSided": True,
                  "bUseTranslucencyVertexFog": False},
        "params": params,
        "customs": customs,
    }
    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    with open(SALIDA, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=True, indent=1)
    print("params: %d (%d escalares, %d vectores)" % (len(params), sum(p["kind"] == "scalar" for p in params),
                                                     sum(p["kind"] == "vector" for p in params)))
    for c in customs:
        print("%s: %d entradas, salidas extra %s, %d caracteres de codigo"
              % (c["desc"], len(c["inputs"]), [x["outputName"] for x in c["additionalOutputs"]], len(c["code"])))
    print("escrito: " + SALIDA)
    return 0


if __name__ == "__main__":
    sys.exit(main())
