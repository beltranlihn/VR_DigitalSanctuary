# -*- coding: utf-8 -*-
"""dryrun_draw_sea.py - corre apply_draw_sea_material.py SIN Unreal, contra el editor SIMULADO de
dryrun_material_script.py (sus reglas de pines: gotchas 446, 447, 453, 482), y verifica lo que dejaria cableado.

  - dos vueltas (la tool corre el script dos veces, gotcha 489): sin errores e IDEMPOTENTE;
  - cada entrada de cada Custom conectada a la fuente que dice su cabecera HLSL (parametro con el pin correcto,
    TexCoord con su indice, WorldPosition - CameraPositionWS, VI);
  - salidas: mar = Height -> Transform(Local->World) -> WPO, Grad -> VI -> PS.G, PS -> Emissive;
             polvo = VS -> WPO directo (mundo), Alpha -> VI -> PS.A, PS -> Emissive;
  - cada parametro evaluado en el grafo = el default del modelo (draw_sea_model.DEF / wave_constants);
  - flags de cada material y las dos MI creadas con su padre.
Uso:  python dryrun_draw_sea.py
"""
import json
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import draw_sea_model as dm  # noqa: E402
import dryrun_material_script as dr  # noqa: E402

RAIZ = dr.RAIZ
BUILD = os.path.join(RAIZ, "VR_Test", "Saved", "ClaudeScripts", "oceano", "draw_sea_build.json")


def main():
    build = json.load(open(BUILD, encoding="utf-8"))
    ed = dr.Editor()
    rs = []
    for vuelta in (1, 2):
        r = dr.exec_script(ed, os.path.join(AQUI, "apply_draw_sea_material.py"))
        rs.append((r, len(ed.ex)))
    r, n = rs[-1]
    dr.chk("oceano: sin errores (2 vueltas)", "err" not in r and not r.get("log") and not rs[0][0].get("log"),
           dr.resumen(rs[0][0]) + " || " + dr.resumen(r))
    dr.chk("oceano: idempotente", rs[0][1] == rs[1][1], "%d -> %d expresiones" % (rs[0][1], rs[1][1]))
    W, V, E = dm.wave_constants(dm.DEF)
    for M in build["materials"]:
        name = M["material"].rsplit("/", 1)[1]
        R = r[name]
        okc = all(isinstance(v, dict) and v["conectadas"] == v["entradas"] and not v["fallos"] for v in R["customs"].values())
        dr.chk("%s: todas las entradas de los 3 Custom conectadas" % name, okc, json.dumps(R["customs"]))
        dr.chk("%s: salidas" % name, R["salidas_ok"] in ("4 de 4", "3 de 3"), R["salidas_ok"])
        dr.chk("%s: parametros = los del plan, ninguno sobrante" % name,
               R["params"]["total"] == len(M["params"]) and not R["params"]["sobrantes"], str(R["params"]))
        mref = M["material"] + "." + name
        flags = ed.assets.get(M["material"] + "#props", {})
        dr.chk("%s: flags" % name, all(flags.get(k) == v for k, v in M["flags"].items()), str(flags))
        dr.chk("%s: MI creada con el material de padre" % name, ed.assets.get(M["instance"], "") == "mi:" + mref)
        cus = {e["props"].get("Description"): x for x, e in ed.ex.items() if e["cls"] == "Custom" and x.startswith(mref + ":")}
        # fuente de cada entrada
        malos = []
        for c in M["customs"]:
            ref = cus[c["desc"]]
            lk = ed.ex[ref]["links"]
            if list(ed.ex[ref]["props"]["Inputs"]) != [{"inputName": e["name"]} for e in c["inputs"]]:
                malos.append(c["desc"] + ": orden de entradas")
            for e in c["inputs"]:
                s = e["src"]
                frm, fo = lk[e["name"]]
                fx = ed.ex[frm]
                if s["kind"] == "param":
                    ok = fx["props"].get("ParameterName") == s["param"] and fo == s["pin"]
                    ok = ok and fo == ("" if e["type"] == "float" else ("RGBA" if e["type"] == "float4" else "RGB"))
                elif s["kind"] == "texcoord":
                    ok = fx["cls"] == "TextureCoordinate" and fx["props"].get("CoordinateIndex") == s["index"]
                elif s["kind"] == "localpos":
                    ok = fx["cls"] == "LocalPosition" and fo == "XYZ"
                elif s["kind"] == "campos":
                    ok = fx["cls"] == "CameraPositionWS"
                elif s["kind"] == "relcam":
                    ok = (fx["cls"] == "Subtract" and ed.ex[fx["links"]["A"][0]]["cls"] == "WorldPosition"
                          and ed.ex[fx["links"]["B"][0]]["cls"] == "CameraPositionWS")
                elif s["kind"] == "vi":
                    src = [c2 for c2 in M["customs"] if c2["output"] == "vi"][0]["desc"]
                    ok = fx["cls"] == "VertexInterpolator" and fo == "PS" and fx["links"]["VS"] == (cus[src], "")
                else:
                    ok = False
                if not ok:
                    malos.append("%s.%s" % (c["desc"], e["name"]))
        dr.chk("%s: cada entrada viene de la fuente de su cabecera HLSL" % name, not malos, str(malos))
        # salidas del material
        wpo = ed.outputs.get((mref, "MP_WorldPositionOffset"))
        em = ed.outputs.get((mref, "MP_EmissiveColor"))
        byout = {c["output"]: cus[c["desc"]] for c in M["customs"]}
        if "wpo_local" in byout:
            okw = wpo and ed.ex[wpo[0]]["cls"] == "Transform" and ed.ex[wpo[0]]["links"]["None"] == (byout["wpo_local"], "") \
                and ed.ex[wpo[0]]["props"].get("TransformSourceType") == "TRANSFORMSOURCE_Local" \
                and ed.ex[wpo[0]]["props"].get("TransformType") == "TRANSFORM_World"
        else:
            okw = wpo == (byout["wpo_world"], "")
        dr.chk("%s: WPO (%s) y Emissive" % (name, "local->mundo" if "wpo_local" in byout else "mundo directo"),
               bool(okw) and em == (byout["emissive"], ""))
        # valores: cada parametro evaluado con sus defaults = el modelo
        peor = 0.0
        for p in M["params"]:
            ref = [x for x, e in ed.ex.items() if x.startswith(mref + ":") and e["props"].get("ParameterName") == p["name"]][0]
            v = np.atleast_1d(np.asarray(ed.value(ref, "RGBA" if p["kind"] == "vector" else "", {}), float))
            nm = p["name"]
            if nm[0] in "WVE" and nm[1:].isdigit():
                ref_v = {"W": W, "V": V, "E": E}[nm[0]][int(nm[1:])]
            elif nm in ("Part", "PerfMode"):
                ref_v = 0.0
            elif nm == "SeaZ":
                ref_v = -120.0
            else:
                ref_v = dm.DEF[nm]
            ref_v = np.atleast_1d(np.asarray(ref_v, float))
            peor = max(peor, float(np.abs(v[:ref_v.shape[0]] - ref_v).max()))
        dr.chk("%s: los %d parametros valen el default del modelo" % (name, len(M["params"])), peor < 1e-12, "max |dif| %.1e" % peor)
    print("      (%d llamadas a tools simuladas)" % ed.calls)
    print("\n%s" % ("TODO OK" if not dr.fallas else "%d FALLAS: %s" % (len(dr.fallas), dr.fallas)))
    return 1 if dr.fallas else 0


if __name__ == "__main__":
    sys.exit(main())
