# -*- coding: utf-8 -*-
"""vida_dryrun.py - corre los scripts de armado de material de la CAPA DE VIDA contra el editor SIMULADO de
dryrun_material_script.py (NO lo modifica: importa su Editor y exec_script) y verifica lo que dejarian cableado.

Uso:
  python vida_dryrun.py polvo     -> apply_vida_dust_material.py (dos veces: idempotencia) sobre un material vacio
  python vida_dryrun.py valle     -> el valle de hoy (apply_valley_material_A/B, v2 + capa viva) + apply_vida_gust_valley.py
                                     (dos veces), re-aplicar el valle (la franja se apaga, neutro) + volver a aplicar la
                                     franja, y el rollback
  (sin argumentos: las dos)
"""
import json
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", "..", ".."))
sys.path.insert(0, AQUI)
import dryrun_material_script as dr  # noqa: E402
import vida_model as vm  # noqa: E402

BUILD = os.path.join(RAIZ, "VR_Test", "Saved", "ClaudeScripts", "vida", "vida_build.json")
fallas = []


def chk(lbl, ok, info=""):
    print(("OK    " if ok else "FALLA ") + lbl + ("  " + info if info else ""))
    if not ok:
        fallas.append(lbl)


def custom(ed, desc):
    r = [x for x, e in ed.ex.items() if e["cls"] == "Custom" and e["props"].get("Description") == desc]
    return r[0] if r else None


def por_desc(ed, desc):
    r = [x for x, e in ed.ex.items() if e["props"].get("Desc") == desc]
    return r[0] if r else None


def por_param(ed, nombre):
    r = [x for x, e in ed.ex.items() if e["cls"] in ("ScalarParameter", "VectorParameter") and e["props"].get("ParameterName") == nombre]
    return r[0] if r else None


def polvo():
    build = json.load(open(BUILD, encoding="utf-8"))["dust"]
    ed = dr.Editor()
    rs = []
    for vuelta in (1, 2):
        r = dr.exec_script(ed, os.path.join(AQUI, "apply_vida_dust_material.py"))
        rs.append((r, len(ed.ex)))
    r, n = rs[-1]
    chk("polvo: sin errores (2 vueltas)", "err" not in r and not r.get("log"), dr.resumen(r))
    chk("polvo: idempotente", rs[0][1] == rs[1][1], "%d -> %d expresiones" % (rs[0][1], rs[1][1]))
    okc = all(isinstance(v, dict) and v["conectadas"] == v["entradas"] and not v["fallos"] for v in r["customs"].values())
    chk("polvo: todas las entradas de los 2 Custom conectadas (38 + 3)", okc and r["customs"]["DustVS"]["entradas"] == 38,
        json.dumps(r["customs"]))
    chk("polvo: WPO / Emissive / Opacity + VS->VI y VS->WPO", r["internas_y_salidas_ok"] == "5 de 5", r["internas_y_salidas_ok"])
    mat = build["material"]
    m = mat + "." + mat.rsplit("/", 1)[1]
    wpo = ed.outputs.get((m, "MP_WorldPositionOffset"))
    em = ed.outputs.get((m, "MP_EmissiveColor"))
    op = ed.outputs.get((m, "MP_Opacity"))
    vs, ps = custom(ed, "DustVS"), custom(ed, "DustPS")
    ok = (wpo and ed.ex[wpo[0]]["cls"] == "Transform" and ed.ex[wpo[0]]["links"]["None"] == (vs, "return")
          and em == (ps, "return") and op == (ps, "Alpha"))
    vi = ed.ex[ps]["links"]["DustV"]
    ok = ok and ed.ex[vi[0]]["cls"] == "VertexInterpolator" and ed.ex[vi[0]]["links"]["VS"] == (vs, "DustV")
    chk("polvo: VS.return -> Transform(Local->World) -> WPO; VS.DustV -> VI -> PS.DustV; PS -> Emissive/Opacity", bool(ok))
    tr = ed.ex[ed.ex[vs]["links"]["CamL"][0]]
    chk("polvo: CamL = TransformPosition World->Local de CameraPositionWS",
        tr["cls"] == "TransformPosition" and tr["props"].get("TransformType") == "TRANSFORMPOSSOURCE_Local"
        and ed.ex[tr["links"]["Input"][0]]["cls"] == "CameraPositionWS")
    uvs = [ed.ex[ed.ex[vs]["links"][n_][0]]["props"].get("CoordinateIndex") for n_ in ("Crn", "Sa", "Sb", "Sc")]
    chk("polvo: Crn/Sa/Sb/Sc = TexCoord 0/1/2/3", uvs == [0, 1, 2, 3], str(uvs))
    chk("polvo: LP = LocalPosition (XYZ)", ed.ex[ed.ex[vs]["links"]["LP"][0]]["cls"] == "LocalPosition"
        and ed.ex[vs]["links"]["LP"][1] == "XYZ")
    peor, n_esc = 0.0, 0
    for e in build["customs"][0]["inputs"]:
        if e["src"]["kind"] != "param" or e["type"] != "float":
            continue
        v = ed.value(*ed.ex[vs]["links"][e["name"]], {})
        peor = max(peor, abs(v - vm.MAT[e["name"]]))
        n_esc += 1
    chk("polvo: los %d escalares llegan con el default del modelo" % n_esc, peor < 1e-12 and n_esc == 25, "max |dif| %.1e" % peor)
    chk("polvo: 34 parametros (25 escalares + 2 colores + 7 internos), ninguno sobrante",
        r["params"]["total"] == 34 and not r["params"]["sobrantes"], str(r["params"]))
    t = ed.value(*ed.ex[vs]["links"]["VidaT"], {})
    chk("polvo: VidaT por defecto (sin BP) tiene Glob 0 -> no se dibuja nada", float(np.asarray(t)[2]) == 0.0, str(t))
    chk("polvo: MI_ValleyDust_SC creada con el material de padre", ed.assets.get(build["instance"], "").startswith("mi:" + m))
    fl = r.get("flags") or {}
    chk("polvo: flags Unlit / AlphaComposite / two-sided / sin niebla de translucidos",
        fl == {"shadingModel": "MSM_Unlit", "blendMode": "BLEND_AlphaComposite", "twoSided": True, "bUseTranslucencyVertexFog": False},
        str(fl))
    print("      (%d llamadas a tools simuladas)" % ed.calls)


def enlaces(ed, excepto=()):
    """todas las conexiones del grafo (entrada -> (expresion, salida)), por Desc/Description/ParameterName."""
    def nom(ref):
        e = ed.ex[ref]
        return e["props"].get("Description") or e["props"].get("Desc") or e["props"].get("ParameterName") or ref
    out = {}
    for ref, e in ed.ex.items():
        for inp, (frm, o) in e["links"].items():
            if (nom(ref), inp) in excepto:
                continue
            out[(nom(ref), inp)] = (nom(frm), o)
    return out


def valle():
    build = json.load(open(BUILD, encoding="utf-8"))["valley"]
    ed = dr.Editor()
    ed.assets["/Game/SoulCharger/Mechanics/Breath/Valley/M_BreathValley_SC"] = "material"
    dr.exec_script(ed, os.path.join(AQUI, "apply_valley_material_A.py"))
    rb = dr.exec_script(ed, os.path.join(AQUI, "apply_valley_material_B.py"))
    chk("valle de hoy armado (apply_valley_material_A/B, v2 + capa viva)", "err" not in rb and not rb.get("log"), dr.resumen(rb))
    antes = enlaces(ed)
    n0 = len(ed.ex)
    vi0, grad, lp = por_desc(ed, "V_VI0"), custom(ed, "ValleyGradVS"), por_desc(ed, "V_LP")
    chk("control: antes de la franja V_VI0.VS <- ValleyGradVS", ed.ex[vi0]["links"].get("VS") == (grad, ""))
    rs = []
    for vuelta in (1, 2):
        r = dr.exec_script(ed, os.path.join(AQUI, "apply_vida_gust_valley.py"))
        rs.append((r, len(ed.ex)))
    r, n = rs[-1]
    chk("franja: sin errores (2 vueltas)", "err" not in r and not r.get("log"), dr.resumen(r))
    chk("franja: idempotente (%d expresiones nuevas: 5 parametros + 1 Custom)" % (n - n0), rs[0][1] == rs[1][1] and n - n0 == 6,
        "%d -> %d -> %d" % (n0, rs[0][1], rs[1][1]))
    gl = custom(ed, "GustLeanVS")
    chk("franja: GustLeanVS con sus 8 entradas conectadas", r["custom"]["conectadas"] == 8 and not r["custom"]["fallos"],
        json.dumps(r["custom"]))
    L = ed.ex[gl]["links"]
    ok = (L.get("G") == (grad, "") and L.get("LP") == (lp, "XYZ") and L.get("Part") == (por_param(ed, "Part"), "")
          and all(L.get(k) == (por_param(ed, k), "RGBA") for k in ("GustP", "GustQ", "GustR", "GustK", "GustS")))
    chk("franja: G <- ValleyGradVS, LP <- V_LP.XYZ, Part <- Part, Gust* <- sus parametros (RGBA)", ok)
    chk("franja: V_VI0.VS <- GustLeanVS", ed.ex[vi0]["links"].get("VS") == (gl, ""))
    despues = enlaces(ed)
    cambios = sorted(k for k in set(antes) | set(despues) if antes.get(k) != despues.get(k) and k[0] != "GustLeanVS")
    chk("franja: el UNICO cambio del grafo del valle (fuera del Custom nuevo) es la entrada VS de V_VI0", cambios == [("V_VI0", "VS")],
        str(cambios))
    for k in ("GustP", "GustQ", "GustR", "GustK", "GustS"):
        v = ed.value(por_param(ed, k), "", {})
        if not np.allclose(v, vm.GUST_MAT[k]):
            chk("franja: default de %s" % k, False, str(v))
    gk = ed.value(por_param(ed, "GustK"), "", {})
    chk("franja: GustK por defecto = (0, 0, 0, 0) -> GustLeanVS devuelve ValleyGradVS bit a bit (Vida_check.py): NEUTRO",
        np.array_equal(np.asarray(gk), np.zeros(4)), str(gk))
    # re-aplicar el valle (lo que haria otra sesion) apaga la franja sin romper nada; volver a pegar la franja la repone
    ra = dr.exec_script(ed, os.path.join(AQUI, "apply_valley_material_A.py"))
    rb = dr.exec_script(ed, os.path.join(AQUI, "apply_valley_material_B.py"))
    chk("re-aplicar el valle: V_VI0.VS vuelve a ValleyGradVS (la franja queda apagada: neutro) y el A lista los Gust* como sobrantes",
        ed.ex[vi0]["links"].get("VS") == (grad, "") and "err" not in rb and
        set(ra.get("sobrantes", [])) == {"GustP", "GustQ", "GustR", "GustK", "GustS"}, str(ra.get("sobrantes")))
    r2 = dr.exec_script(ed, os.path.join(AQUI, "apply_vida_gust_valley.py"))
    chk("volver a pegar la franja la repone (V_VI0.VS <- GustLeanVS, 8/8)", ed.ex[vi0]["links"].get("VS") == (gl, "")
        and r2["custom"]["conectadas"] == 8)
    # rollback
    rr = dr.exec_script(ed, os.path.join(AQUI, "rollback_vida_gust_valley.py"))
    fin = enlaces(ed, excepto={("GustLeanVS", k) for k in L})
    base = {k: v for k, v in antes.items()}
    chk("rollback: V_VI0.VS <- ValleyGradVS y el resto del grafo igual al de antes de la franja",
        ed.ex[vi0]["links"].get("VS") == (grad, "") and fin == base and rr.get("vi0_a_valleygradvs"),
        "diferencias %s" % sorted(k for k in set(fin) | set(base) if fin.get(k) != base.get(k)))
    chk("rollback: lista para borrar el Custom y los 5 parametros (sueltos: no se compilan)", len(rr.get("para_borrar", [])) == 6,
        str(rr.get("para_borrar")))
    # si falta algo del valle, el script no toca nada
    ed2 = dr.Editor()
    ed2.assets["/Game/SoulCharger/Mechanics/Breath/Valley/M_BreathValley_SC"] = "material"
    dr.exec_script(ed2, os.path.join(AQUI, "apply_valley_material_A.py"))
    n2 = len(ed2.ex)
    r3 = dr.exec_script(ed2, os.path.join(AQUI, "apply_vida_gust_valley.py"))
    chk("control negativo: sobre un valle sin ValleyGradVS el script aborta sin crear nada", "err" in r3 and len(ed2.ex) == n2,
        str(r3.get("err")))
    print("      (%d llamadas a tools simuladas)" % (ed.calls + ed2.calls))


if __name__ == "__main__":
    que = sys.argv[1:] or ["polvo", "valle"]
    if "polvo" in que:
        polvo()
    if "valle" in que:
        valle()
    print("\n%s" % ("TODO OK" if not fallas else "%d FALLAS: %s" % (len(fallas), fallas)))
    sys.exit(1 if fallas else 0)
