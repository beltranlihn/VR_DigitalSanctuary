# -*- coding: utf-8 -*-
"""plan_valley_material.py - arma el PLAN de construccion de M_BreathValley_SC en JSON.

Lee:
  - los tres Custom (scripts/hlsl/ValleyHeightVS.hlsl, ValleyGradVS.hlsl, ValleyPS.hlsl): el CODIGO
    entero y la tabla "ENTRADAS" del encabezado (nombre, tipo y de donde sale cada entrada);
  - la tabla de parametros 7.1 de docs/PLAN-VALLE-ENTERING-2026-09-27.md (nombre, tipo, default, grupo).
Fuentes de una entrada (cabecera de cada .hlsl): ScalarParameter / VectorParameter (param), LocalPosition,
VertexInterpolator_N, CameraVector (camlocal), Distance(...), preshader D(az, el), preshader Cosine(p) y, desde la
capa viva (2026-09-28), preshader Mul(A, B), preshader Mix(A, B, T) y preshader Tint(A, B, T) (ver fuente()).
Escribe VR_Test/Saved/ClaudeScripts/valley_build.json, que el script de Unreal lee con
AssetTools.read_file (solo lee archivos dentro de Saved/). Asi el material se arma sin tipear a mano
ni el codigo ni los parametros (68 en la v2), y se puede re-correr despues de cualquier cambio del HLSL.

Uso:  python plan_valley_material.py
"""
import json
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(AQUI, "..", "..", "..", ".."))
HLSL = os.path.join(AQUI, "hlsl")
SPEC = os.path.join(REPO, "docs", "PLAN-VALLE-ENTERING-2026-09-27.md")
SALIDA = os.path.join(REPO, "VR_Test", "Saved", "ClaudeScripts", "valley_build.json")

CUSTOMS = [("ValleyHeightVS", "CMOT_Float3"), ("ValleyGradVS", "CMOT_Float4"), ("ValleyPS", "CMOT_Float3")]


def num(s):
    s = s.strip().replace("−", "-").replace(",", ".")
    return float(s)


def leer_parametros():
    params = []
    en_tabla = False
    for linea in open(SPEC, encoding="utf-8"):
        if linea.startswith("### 7.1"):
            en_tabla = True
            continue
        if en_tabla and linea.startswith("### "):
            break
        if not en_tabla or not linea.startswith("| `"):
            continue
        cols = [c.strip() for c in linea.strip().strip("|").split("|")]
        grupo = cols[0].strip("`")
        nombre = cols[1].strip("`")
        tipo = cols[2]
        dflt = cols[3]
        if tipo.startswith("vector"):
            m = re.search(r"\(([^)]*)\)", dflt)
            partes = re.split(r",\s+", m.group(1))
            valor = [num(p) for p in partes]
            params.append({"name": nombre, "kind": "vector", "default": valor, "group": grupo})
        else:
            m = re.match(r"\s*([−\-]?[\d.,]+)", dflt)
            params.append({"name": nombre, "kind": "scalar", "default": num(m.group(1)), "group": grupo})
    return params


def fuente(texto):
    t = texto.strip()
    m = re.match(r"(Scalar|Vector)Parameter (\w+)", t)
    if m:
        return {"kind": "param", "param": m.group(2), "vector": m.group(1) == "Vector"}
    if t.startswith("LocalPosition"):
        return {"kind": "localpos"}
    m = re.match(r"VertexInterpolator_(\d)", t)
    if m:
        return {"kind": "vi", "index": int(m.group(1))}
    if t.startswith("CameraVector"):
        return {"kind": "camlocal"}
    if t.startswith("Distance("):
        return {"kind": "dist"}
    m = re.match(r"preshader D\((\w+), (\w+)\)", t)
    if m:
        return {"kind": "dir", "az": m.group(1), "el": m.group(2)}
    m = re.match(r"preshader Cosine\((\w+)\)", t)
    if m:
        return {"kind": "cos", "param": m.group(1)}
    # CAPA VIVA (2026-09-28): cuentas de uniformes que Unreal pliega en el preshader (costo 0 por pixel)
    #   Mul(A, B)    -> A * B              (helper M_<entrada>: un Multiply)
    #   Mix(A, B, T) -> A + (B - A) * T    (helpers X_<entrada>_d Subtract, X_<entrada>_m Multiply, X_<entrada> Add)
    #   Tint(A, B, T) -> A * (1 + (B - 1) * T)  tinte RELATIVO (rev. 2: SkyHorizon es perilla del BP). Helpers
    #                   T_<entrada>_d Subtract(B, ConstB 1), T_<entrada>_m Multiply(d, T), T_<entrada>_o Add(m, ConstB 1),
    #                   T_<entrada> Multiply(A, o). Con T = 0: A * 1 exacto.
    m = re.match(r"preshader Mul\((\w+), (\w+)\)", t)
    if m:
        return {"kind": "mul", "a": m.group(1), "b": m.group(2)}
    m = re.match(r"preshader Mix\((\w+), (\w+), (\w+)\)", t)
    if m:
        return {"kind": "mix", "a": m.group(1), "b": m.group(2), "t": m.group(3)}
    m = re.match(r"preshader Tint\((\w+), (\w+), (\w+)\)", t)
    if m:
        return {"kind": "tint", "a": m.group(1), "b": m.group(2), "t": m.group(3)}
    raise SystemExit("fuente desconocida: " + t)


def leer_custom(nombre):
    codigo = open(os.path.join(HLSL, nombre + ".hlsl"), encoding="utf-8").read()
    entradas = []
    en = False
    for linea in codigo.splitlines():
        if "ENTRADAS" in linea and linea.startswith("//"):
            en = True
            continue
        if en:
            m = re.match(r"//\s+(\d+)\s+(\w+)\s+(float[234]?)\s+(.+?)(\s{2,}.*)?$", linea)
            if not m:
                if entradas:
                    break
                continue
            entradas.append({"name": m.group(2), "type": m.group(3), "src": fuente(m.group(4))})
    return codigo, entradas


def main():
    params = leer_parametros()
    nombres = {p["name"] for p in params}
    customs = []
    for nombre, salida in CUSTOMS:
        codigo, entradas = leer_custom(nombre)
        for e in entradas:
            s = e["src"]
            for clave in ("param", "az", "el", "a", "b", "t"):
                if clave in s and s[clave] not in nombres:
                    raise SystemExit("%s: la entrada %s usa el parametro %s, que no esta en la tabla 7.1" % (nombre, e["name"], s[clave]))
        customs.append({"desc": nombre, "outputType": salida, "code": codigo, "inputs": entradas})
    plan = {"material": "/Game/SoulCharger/Mechanics/Breath/Valley/M_BreathValley_SC", "params": params, "customs": customs}
    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    with open(SALIDA, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=True, indent=1)
    print("params: %d (%d escalares, %d vectores)" % (len(params), sum(p["kind"] == "scalar" for p in params), sum(p["kind"] == "vector" for p in params)))
    for c in customs:
        print("%s: %d entradas, %d caracteres de codigo" % (c["desc"], len(c["inputs"]), len(c["code"])))
    print("escrito: " + SALIDA)
    return 0


if __name__ == "__main__":
    sys.exit(main())
