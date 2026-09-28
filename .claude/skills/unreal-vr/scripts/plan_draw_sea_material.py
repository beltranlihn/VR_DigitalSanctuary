# -*- coding: utf-8 -*-
"""plan_draw_sea_material.py - arma el PLAN de los dos materiales del oceano del dibujo (M_DrawSea_SC y M_DrawDust_SC)
desde los HLSL generados (scripts/hlsl/DrawSea*.hlsl, DrawDust*.hlsl) y los defaults del modelo (draw_sea_model.DEF).

Escribe VR_Test/Saved/ClaudeScripts/oceano/draw_sea_build.json, que lee apply_draw_sea_material.py en Unreal.
Plan: docs/PLAN-OCEANO-DIBUJO-2026-09-28.md. Receta copiada de plan_breath_air_material.py (el pipeline probado).

Uso:  python gen_draw_sea_hlsl.py && python plan_draw_sea_material.py && python dryrun_draw_sea.py
"""
import json
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import draw_sea_model as dm  # noqa: E402

RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", "..", ".."))
HLSL = os.path.join(AQUI, "hlsl")
SALIDA = os.path.join(RAIZ, "VR_Test", "Saved", "ClaudeScripts", "oceano", "draw_sea_build.json")
CARPETA = "/Game/SoulCharger/Mechanics/Drawing/Scape"

# grupo de cada parametro en la MI (los mismos del actor y del prototipo)
GRUPOS = {
    "SwellAmp": "1 - Oleaje",
    "GroupAmt": "2 - Grupos y morphing", "GroupLen": "2 - Grupos y morphing", "Warp": "2 - Grupos y morphing",
    "WarpScale": "2 - Grupos y morphing",
    "Advance": "3 - Avance",
    "CalmR": "4 - Cerca y lejos", "CalmMin": "4 - Cerca y lejos",
    "DeepColor": "5 - Superficie", "SurfColor": "5 - Superficie", "CrestColor": "5 - Superficie", "CrestAmt": "5 - Superficie",
    "LightAz": "5 - Superficie", "LightEl": "5 - Superficie", "WrapPow": "5 - Superficie",
    "ZenithColor": "6 - Cielo y niebla", "HorizonColor": "6 - Cielo y niebla", "SkyPow": "6 - Cielo y niebla",
    "GlowColor": "6 - Cielo y niebla", "GlowAmt": "6 - Cielo y niebla", "GlowPow": "6 - Cielo y niebla",
    "FogStart": "6 - Cielo y niebla", "FogDensity": "6 - Cielo y niebla", "Dither": "6 - Cielo y niebla",
    "DustColor": "7 - Polvo", "DustAmt": "7 - Polvo", "DustSize": "7 - Polvo", "DustBox": "7 - Polvo",
    "DustFollow": "7 - Polvo", "DustRise": "7 - Polvo", "DustWobble": "7 - Polvo", "DustNear": "7 - Polvo",
    "DustBG": "7 - Polvo",
}
INTERNO = "9 - Internos (los escribe BP_DrawSea_SC)"
# defaults que no estan en DEF: los internos. W/V/E salen de wave_constants(DEF) para que la MI anime sola.
W, V, E = dm.wave_constants(dm.DEF)
EXTRA = {"Part": 0.0, "PerfMode": 0.0, "SeaZ": -120.0}
for i in range(6):
    EXTRA["W%d" % i] = list(W[i])
    EXTRA["V%d" % i] = list(V[i])
    EXTRA["E%d" % i] = list(E[i])

MATERIALES = [
    {"material": CARPETA + "/M_DrawSea_SC", "instance": CARPETA + "/MI_DrawSea_SC",
     "flags": {"shadingModel": "MSM_Unlit", "blendMode": "BLEND_Opaque", "twoSided": True,
               "floatPrecisionMode": "MFPM_Full_MaterialExpressionOnly"},
     # (Custom, salida del material). El VS de altura va por Transform Local->World; el de gradiente por el VI.
     "customs": [("DrawSeaHeightVS", "wpo_local"), ("DrawSeaGradVS", "vi"), ("DrawSeaPS", "emissive")]},
    {"material": CARPETA + "/M_DrawDust_SC", "instance": CARPETA + "/MI_DrawDust_SC",
     "flags": {"shadingModel": "MSM_Unlit", "blendMode": "BLEND_Additive", "twoSided": True,
               "bUseTranslucencyVertexFog": False, "floatPrecisionMode": "MFPM_Full_MaterialExpressionOnly"},
     "customs": [("DrawDustVS", "wpo_world"), ("DrawDustAlphaVS", "vi"), ("DrawDustPS", "emissive")]},
]


def fuente(t, tipo):
    t = t.strip()
    m = re.match(r"(Scalar|Vector)Parameter (\w+)$", t)
    if m:
        pin = "" if m.group(1) == "Scalar" else ("RGBA" if tipo == "float4" else "RGB")
        return {"kind": "param", "param": m.group(2), "vector": m.group(1) == "Vector", "pin": pin}
    if t.startswith("LocalPosition"):
        return {"kind": "localpos"}
    m = re.match(r"TexCoord (\d)$", t)
    if m:
        return {"kind": "texcoord", "index": int(m.group(1))}
    if t == "CameraPositionWS":
        return {"kind": "campos"}
    if t.startswith("WorldPosition - CameraPositionWS"):
        return {"kind": "relcam"}
    if t.startswith("VertexInterpolator_0 (pin PS)"):
        return {"kind": "vi"}
    raise SystemExit("fuente desconocida: " + t)


def leer_custom(nombre):
    codigo = open(os.path.join(HLSL, nombre + ".hlsl"), encoding="ascii").read().replace("\r\n", "\n")
    m = re.search(r'OutputType (CMOT_Float\d)', codigo)
    entradas = []
    for mm in re.finditer(r"^//\s+(\d+)\s+(\w+)\s+(float[234]?)\s+(.+?)\s+\|", codigo, re.M):
        entradas.append({"name": mm.group(2), "type": mm.group(3), "src": fuente(mm.group(4), mm.group(3))})
    if not entradas:
        raise SystemExit(nombre + ": sin entradas en la cabecera")
    return codigo, m.group(1), entradas


def default_de(nombre, tipo):
    v = EXTRA[nombre] if nombre in EXTRA else dm.DEF[nombre]
    if tipo == "scalar":
        return float(v)
    v = [float(x) for x in v]
    return v + [1.0] * (4 - len(v))


def main():
    mats = []
    for M in MATERIALES:
        customs, params, vistos = [], [], {}
        for nombre, salida in M["customs"]:
            codigo, cmot, entradas = leer_custom(nombre)
            customs.append({"desc": nombre, "outputType": cmot, "output": salida, "code": codigo, "inputs": entradas})
            for e in entradas:
                s = e["src"]
                if s["kind"] != "param":
                    continue
                kind = "vector" if s["vector"] else "scalar"
                if s["param"] in vistos and vistos[s["param"]] != kind:
                    raise SystemExit("%s: el parametro %s aparece como escalar y como vector" % (nombre, s["param"]))
                if s["param"] not in vistos:
                    vistos[s["param"]] = kind
                    params.append({"name": s["param"], "kind": kind, "default": default_de(s["param"], kind),
                                   "group": GRUPOS.get(s["param"], INTERNO)})
        mats.append({"material": M["material"], "instance": M["instance"], "flags": M["flags"],
                     "params": params, "customs": customs})
    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    with open(SALIDA, "w", encoding="utf-8") as f:
        json.dump({"materials": mats}, f, ensure_ascii=True, indent=1)
    for m in mats:
        print("%s: %d parametros (%d vectores)" % (m["material"].rsplit("/", 1)[1], len(m["params"]),
                                                  sum(p["kind"] == "vector" for p in m["params"])))
        for c in m["customs"]:
            print("   %-16s %-11s -> %-9s %2d entradas, %5d caracteres" % (c["desc"], c["outputType"], c["output"],
                                                                         len(c["inputs"]), len(c["code"])))
    print("escrito: " + SALIDA)
    return 0


if __name__ == "__main__":
    sys.exit(main())
