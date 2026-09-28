# -*- coding: utf-8 -*-
"""dryrun_material_script.py - corre un script de armado de material (apply_*.py) SIN Unreal, contra un editor
SIMULADO, y verifica lo que dejaria cableado. Es el control que queda cuando el editor no esta (gotcha 473 aplicada a
los scripts de material).

Simula MaterialTools / ObjectTools / AssetTools / MaterialInstanceTools con las reglas que ya costaron (gotchas 446,
447, 453): nombres de pin por clase (Custom con salidas adicionales -> "return"; VectorParameter RGB/RGBA;
LocalPosition XYZ; VertexInterpolator VS/PS; Transform "None"), conectar a un pin inexistente FALLA, y un
set_properties de 'Inputs' suelta las conexiones de entrada del Custom.
Despues EVALUA el grafo resultante con los defaults (y con otros valores) para cada entrada de cada Custom y lo compara
con lo que el plan dice que tiene que llegar.

Uso:
  python dryrun_material_script.py valle   -> apply_valley_material_A.py + B (dos veces cada uno: idempotencia)
                                              desde un material VACIO y desde el material v2 ya aplicado
  python dryrun_material_script.py rollback -> con la capa viva aplicada, las copias de aliento/rollback_valle_v2/
                                              (plan del respaldo) vuelven cada entrada a la v2 exacta
  python dryrun_material_script.py aliento -> apply_breath_air_material.py (dos veces)
"""
import json
import math
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", "..", ".."))
sys.path.insert(0, AQUI)

OUTS = {"ScalarParameter": [""], "VectorParameter": ["", "R", "G", "B", "A", "RGB", "RGBA"],
        "Multiply": [""], "Add": [""], "Subtract": [""], "Sine": [""], "Cosine": [""], "AppendVector": [""],
        "LocalPosition": ["XYZ"], "VertexInterpolator": ["PS"], "Transform": [""], "TransformPosition": [""],
        "CameraVectorWS": [""], "WorldPosition": ["", "XYZ", "XY", "Z"], "CameraPositionWS": [""], "Distance": [""],
        "TextureCoordinate": ["", "U", "V"]}
INS = {"Multiply": ["A", "B"], "Add": ["A", "B"], "Subtract": ["A", "B"], "AppendVector": ["A", "B"],
       "Distance": ["A", "B"], "Sine": ["Input"], "Cosine": ["Input"], "Transform": ["None"],
       "TransformPosition": ["Input"], "VertexInterpolator": ["VS"]}
MP_OK = {"MP_WorldPositionOffset", "MP_EmissiveColor", "MP_Opacity"}


class Editor:
    def __init__(self):
        self.assets = {}      # asset path -> kind
        self.ex = {}          # refPath -> dict(cls, props, links={input: (from, out)})
        self.n = 0
        self.outputs = {}     # (mat, MP) -> (ref, out)
        self.calls = 0
        self.file_reads = []

    def _cls(self, ref):
        return self.ex[ref]["cls"]

    def outs(self, ref):
        c = self._cls(ref)
        if c == "Custom":
            ao = self.ex[ref]["props"].get("AdditionalOutputs") or []
            return (["return"] + [a["outputName"] for a in ao]) if ao else [""]
        return OUTS[c]

    def ins(self, ref):
        c = self._cls(ref)
        if c == "Custom":
            return [i["inputName"] for i in (self.ex[ref]["props"].get("Inputs") or [])]
        return INS.get(c, [])

    def call(self, name, payload):
        self.calls += 1
        p = json.loads(payload)
        tool = name.split(".")[-1]
        f = getattr(self, "t_" + tool, None)
        if f is None:
            raise RuntimeError("tool no simulada: " + name)
        return {"returnValue": f(**p)}

    # ---- AssetTools
    def t_read_file(self, file_path):
        self.file_reads.append(file_path)
        return open(file_path, encoding="utf-8").read()

    def t_exists(self, path):
        # el MCP real exige 'path' (verificado 2026-09-28: 'asset_path' falla)
        return path in self.assets

    # ---- MaterialTools
    def t_create_material(self, folder_path, asset_name):
        p = folder_path + "/" + asset_name
        if p in self.assets:
            raise RuntimeError("ya existe")
        self.assets[p] = "material"
        return {"refPath": p + "." + asset_name}

    def t_get_expressions(self, material_or_function):
        m = material_or_function["refPath"]
        return [{"refPath": r} for r in self.ex if r.startswith(m + ":")]

    def t_add_expression(self, material_or_function, expression_class, x=0, y=0):
        cls = expression_class["refPath"].split(".")[-1].replace("MaterialExpression", "")
        if cls not in OUTS and cls != "Custom":
            raise RuntimeError("clase no simulada " + cls)
        self.n += 1
        ref = "%s:MaterialExpression%s_%d" % (material_or_function["refPath"], cls, self.n)
        self.ex[ref] = dict(cls=cls, props={}, links={})
        return {"refPath": ref}

    def t_get_expression_input_names(self, material_or_function, expression):
        return self.ins(expression["refPath"])

    def t_get_expression_output_names(self, material_or_function, expression):
        return self.outs(expression["refPath"])

    def t_connect_expressions(self, from_expression, from_output_name, to_expression, to_input_name):
        a, b = from_expression["refPath"], to_expression["refPath"]
        if a not in self.ex or b not in self.ex:
            raise RuntimeError("expresion inexistente")
        if from_output_name not in self.outs(a):
            raise RuntimeError("salida %r no existe en %s (%s)" % (from_output_name, self._cls(a), self.outs(a)))
        if to_input_name not in self.ins(b):
            raise RuntimeError("entrada %r no existe en %s" % (to_input_name, self._cls(b)))
        self.ex[b]["links"][to_input_name] = (a, from_output_name)
        return True

    def t_connect_to_output(self, expression, output_name, material_property):
        a = expression["refPath"]
        if output_name not in self.outs(a):
            raise RuntimeError("salida %r no existe" % output_name)
        if material_property not in MP_OK:
            raise RuntimeError("propiedad no simulada " + material_property)
        self.outputs[(a.split(":")[0], material_property)] = (a, output_name)
        return True

    # ---- ObjectTools
    def t_set_properties(self, instance, values):
        r = instance["refPath"]
        v = json.loads(values)
        if r in self.ex:
            pr = self.ex[r]["props"]
            for k, val in v.items():
                if k in ("Inputs", "AdditionalOutputs"):
                    old = pr.get(k) or []
                    if old and val and len(old) != len(val):
                        raise RuntimeError("ArrayAdd: elements changed alongside the size change (gotcha 446/453)")
                    if k == "Inputs":
                        self.ex[r]["links"] = {}          # resetear inputs suelta las conexiones de entrada
                pr[k] = val
        else:
            self.assets.setdefault(r.split(".")[0], "material")
            self.assets[r.split(".")[0] + "#props"] = dict(self.assets.get(r.split(".")[0] + "#props", {}), **v)
        return True

    def t_get_properties(self, instance, properties):
        r = instance["refPath"]
        if r in self.ex:
            pr = self.ex[r]["props"]
            return json.dumps({k: pr[k] for k in properties if k in pr})
        pr = self.assets.get(r.split(".")[0] + "#props", {})
        return json.dumps({k: pr[k] for k in properties if k in pr})

    # ---- MaterialInstanceTools
    def t_create(self, folder_path, asset_name, parent):
        p = folder_path + "/" + asset_name
        if p in self.assets:
            raise RuntimeError("ya existe")
        self.assets[p] = "mi:" + parent["refPath"]
        return {"refPath": p + "." + asset_name}

    # ---- evaluacion del grafo con valores
    def value(self, ref, out, vals):
        e = self.ex[ref]
        c, pr = e["cls"], e["props"]
        # Add / Subtract / Multiply con una entrada SIN conectar usan ConstA / ConstB (defaults de Unreal: Add 0 / 1,
        # Subtract 1 / 1, Multiply 0 / 1)
        CONST = {"Add": (0.0, 1.0), "Subtract": (1.0, 1.0), "Multiply": (0.0, 1.0)}.get(c, (0.0, 0.0))
        L = lambda k: (self.value(*e["links"][k], vals) if k in e["links"]
                       else float(pr.get("Const" + k, CONST[0] if k == "A" else CONST[1])))
        if c == "ScalarParameter":
            return float(vals.get(pr["ParameterName"], pr["DefaultValue"]))
        if c == "VectorParameter":
            d = pr["DefaultValue"]
            v = vals.get(pr["ParameterName"], (d["r"], d["g"], d["b"], d["a"]))
            v = np.array(list(v) + [1.0] * (4 - len(v)), float)
            return {"": v, "RGBA": v, "RGB": v[:3], "R": v[0], "G": v[1], "B": v[2], "A": v[3]}[out]
        if c == "Multiply":
            return np.asarray(L("A")) * np.asarray(L("B"))
        if c == "Add":
            return np.asarray(L("A")) + np.asarray(L("B"))
        if c == "Subtract":
            return np.asarray(L("A")) - np.asarray(L("B"))
        if c == "Sine":
            return math.sin(2 * math.pi * L("Input") / pr.get("Period", 1.0))
        if c == "Cosine":
            return math.cos(2 * math.pi * L("Input") / pr.get("Period", 1.0))
        if c == "AppendVector":
            return np.concatenate([np.atleast_1d(L("A")), np.atleast_1d(L("B"))])
        return ("SIN_VALOR", c, pr.get("Desc"), out)


def exec_script(ed, ruta):
    code = open(ruta, encoding="utf-8").read()
    ns = {"execute_tool": ed.call}
    exec(compile(code, ruta, "exec"), ns)
    return ns["result"]


def resumen(r):
    return json.dumps({k: v for k, v in r.items() if k != "log"}, ensure_ascii=False)[:900] + ("  LOG=%s" % r.get("log") if r.get("log") else "")


fallas = []


def chk(lbl, ok, info=""):
    print(("OK    " if ok else "FALLA ") + lbl + ("  " + info if info else ""))
    if not ok:
        fallas.append(lbl)


def valle():
    import valley_model as vm
    build = json.load(open(os.path.join(RAIZ, "VR_Test", "Saved", "ClaudeScripts", "valley_build.json"), encoding="utf-8"))
    for origen in ("vacio", "v2"):
        ed = Editor()
        if origen == "v2":
            # el material que hoy esta en Unreal: se arma con el plan del RESPALDO de la v2 aplicada
            v2 = os.path.join(RAIZ, "VR_Test", "Saved", "ClaudeScripts", "valle_v2_aplicada_backup", "valley_build.json")
            real = os.path.join(RAIZ, "VR_Test", "Saved", "ClaudeScripts", "valley_build.json")
            orig = ed.t_read_file

            def leer_v2(file_path, _o=orig):
                return _o(v2 if file_path.endswith("valley_build.json") else file_path)
            ed.t_read_file = leer_v2
            ed.assets["/Game/SoulCharger/Mechanics/Breath/Valley/M_BreathValley_SC"] = "material"
            exec_script(ed, os.path.join(AQUI, "apply_valley_material_A.py"))
            exec_script(ed, os.path.join(AQUI, "apply_valley_material_B.py"))
            ed.t_read_file = orig
            n_v2 = len(ed.ex)
        else:
            ed.assets["/Game/SoulCharger/Mechanics/Breath/Valley/M_BreathValley_SC"] = "material"
            n_v2 = 0
        rs = []
        for vuelta in (1, 2):
            ra = exec_script(ed, os.path.join(AQUI, "apply_valley_material_A.py"))
            rb = exec_script(ed, os.path.join(AQUI, "apply_valley_material_B.py"))
            rs.append((ra, rb, len(ed.ex)))
        ra, rb, n = rs[-1]
        chk("valle desde %s: A sin errores (2 vueltas)" % origen, "err" not in ra and not ra.get("log"), resumen(ra))
        chk("valle desde %s: B sin errores (2 vueltas)" % origen, "err" not in rb and not rb.get("log"), resumen(rb))
        okc = all(v["conectadas"] == v["entradas"] and not v["fallos"] for v in rb["customs"].values())
        chk("valle desde %s: todas las entradas de los 3 Custom conectadas" % origen, okc, json.dumps(rb["customs"]))
        chk("valle desde %s: idempotente (misma cantidad de expresiones en la 2a vuelta: %d)" % (origen, n),
            rs[0][2] == rs[1][2], "%d -> %d (v2 tenia %d)" % (rs[0][2], rs[1][2], n_v2))
        if origen == "v2":
            chk("valle desde v2: expresiones nuevas = 11 parametros + 7 Mul + 3 del Mix + 4 del Tint = 25", n - n_v2 == 25, "%d" % (n - n_v2))
            chk("valle desde v2: ningun helper sobrante", not ra.get("helpers_sobrantes"), str(ra.get("helpers_sobrantes")))
        # evaluar cada entrada del PS con valores: neutro = v2 exacto; con Live al azar = modelo efectivos()
        ps = [r for r, e in ed.ex.items() if e["cls"] == "Custom" and e["props"].get("Description") == "ValleyPS"][0]
        rng = np.random.default_rng(3)
        for caso in ("neutro", "vivo"):
            vals = {}
            q = vm.params()
            if caso == "vivo":
                S = rng.uniform(-1, 1)
                q.update(vm.live_desde_S(S, Fog=1.3, Glow=0.7, Shadow=1.1, Warm=1.5))
                for k in q:
                    if k.startswith("Live"):
                        vals[k] = q[k]
            ef = vm.efectivos(q)
            peor, nomal = 0.0, []
            for e in build["customs"][2]["inputs"]:
                s = e["src"]
                if s["kind"] not in ("param", "mul", "mix", "tint"):
                    continue
                lk = ed.ex[ps]["links"].get(e["name"])
                v = ed.value(*lk, vals)
                if isinstance(v, tuple):
                    nomal.append(e["name"])
                    continue
                ref = np.atleast_1d(np.asarray(ef[e["name"]], float))
                v = np.atleast_1d(np.asarray(v, float))[:ref.shape[0]]
                d = float(np.abs(v - ref).max())
                if caso == "neutro":
                    b = np.atleast_1d(np.asarray(vm.P[e["name"]], float))
                    d = max(d, float(np.abs(v - b).max()))
                peor = max(peor, d)
            chk("valle desde %s, %s: cada entrada del PS evaluada en el grafo = %s" % (origen, caso, "la v2 EXACTA" if caso == "neutro" else "efectivos() del modelo"),
                peor == 0.0 if caso == "neutro" else peor < 1e-9, "max |dif| %.2e %s" % (peor, nomal))


def rollback():
    """Rollback a la v2 (plan 10): con la capa viva aplicada, las copias de rollback_valle_v2/ (el mismo script con el
    plan del respaldo) reconectan cada entrada a su parametro y listan lo que hay que borrar."""
    import valley_model as vm
    rb = os.path.join(RAIZ, "VR_Test", "Saved", "ClaudeScripts", "aliento", "rollback_valle_v2")
    bk = json.load(open(os.path.join(RAIZ, "VR_Test", "Saved", "ClaudeScripts", "valle_v2_aplicada_backup", "valley_build.json"), encoding="utf-8"))
    ed = Editor()
    ed.assets["/Game/SoulCharger/Mechanics/Breath/Valley/M_BreathValley_SC"] = "material"
    exec_script(ed, os.path.join(AQUI, "apply_valley_material_A.py"))
    exec_script(ed, os.path.join(AQUI, "apply_valley_material_B.py"))
    ra = exec_script(ed, os.path.join(rb, "apply_valley_material_A_v2.py"))
    rbb = exec_script(ed, os.path.join(rb, "apply_valley_material_B_v2.py"))
    lee = [f for f in ed.file_reads if f.endswith("valley_build.json")]
    chk("rollback: las copias leen el plan del RESPALDO", lee[-2:] and all("valle_v2_aplicada_backup" in f for f in lee[-2:]), str(lee[-2:]))
    okc = all(v["conectadas"] == v["entradas"] and not v["fallos"] for v in rbb["customs"].values())
    chk("rollback: sin errores y todas las entradas conectadas", "err" not in ra and not ra.get("log") and okc and not rbb.get("log"), resumen(rbb))
    ps = [r for r, e in ed.ex.items() if e["cls"] == "Custom" and e["props"].get("Description") == "ValleyPS"][0]
    vals = dict(vm.live_desde_S(-1.0, Fog=2.0, Glow=2.0, Shadow=2.0, Warm=2.0))      # respirando a fondo: no tiene que llegar
    peor = 0.0
    for e in bk["customs"][2]["inputs"]:
        if e["src"]["kind"] != "param":
            continue
        v = np.atleast_1d(np.asarray(ed.value(*ed.ex[ps]["links"][e["name"]], vals), float))
        ref = np.atleast_1d(np.asarray(vm.P[e["name"]], float))
        peor = max(peor, float(np.abs(v[:ref.shape[0]] - ref).max()))
    chk("rollback: cada entrada del PS vale la v2 EXACTA aunque los Live* sigan respirando", peor == 0.0, "max |dif| %.1e" % peor)
    nuevos = sorted(set(vm.P) - {p["name"] for p in bk["params"]})
    chk("rollback: el A lista los 11 parametros y los 14 helpers de la capa viva para borrar",
        ra.get("sobrantes") == nuevos and len(ra.get("helpers_sobrantes", [])) == 14,
        "sobrantes %s helpers %s" % (ra.get("sobrantes"), ra.get("helpers_sobrantes")))


def aliento():
    import breath_air_model as am
    build = json.load(open(os.path.join(RAIZ, "VR_Test", "Saved", "ClaudeScripts", "aliento", "breath_air_build.json"), encoding="utf-8"))
    ed = Editor()
    rs = []
    for vuelta in (1, 2):
        r = exec_script(ed, os.path.join(AQUI, "apply_breath_air_material.py"))
        rs.append((r, len(ed.ex)))
    r, n = rs[-1]
    chk("aliento: sin errores (2 vueltas)", "err" not in r and not r.get("log"), resumen(r))
    chk("aliento: idempotente", rs[0][1] == rs[1][1], "%d -> %d expresiones" % (rs[0][1], rs[1][1]))
    okc = all(isinstance(v, dict) and v["conectadas"] == v["entradas"] and not v["fallos"] for v in r["customs"].values())
    chk("aliento: todas las entradas de los 2 Custom conectadas", okc, json.dumps(r["customs"]))
    chk("aliento: WPO / Emissive / Opacity + VS->VI y VS->WPO", r["internas_y_salidas_ok"] == "5 de 5", r["internas_y_salidas_ok"])
    mat = build["material"]
    m = mat + "." + mat.rsplit("/", 1)[1]
    wpo = ed.outputs.get((m, "MP_WorldPositionOffset"))
    em = ed.outputs.get((m, "MP_EmissiveColor"))
    op = ed.outputs.get((m, "MP_Opacity"))
    vs = [x for x, e in ed.ex.items() if e["cls"] == "Custom" and e["props"].get("Description") == "BreathAirVS"][0]
    ps = [x for x, e in ed.ex.items() if e["cls"] == "Custom" and e["props"].get("Description") == "BreathAirPS"][0]
    ok = (wpo and ed.ex[wpo[0]]["cls"] == "Transform" and ed.ex[wpo[0]]["links"]["None"] == (vs, "return")
          and em == (ps, "return") and op == (ps, "Alpha"))
    vi = ed.ex[ps]["links"]["AirV"]
    ok = ok and ed.ex[vi[0]]["cls"] == "VertexInterpolator" and ed.ex[vi[0]]["links"]["VS"] == (vs, "AirV")
    chk("aliento: VS.return -> Transform(Local->World) -> WPO; VS.AirV -> VI -> PS.AirV; PS -> Emissive/Opacity", bool(ok))
    tr = ed.ex[ed.ex[vs]["links"]["CamL"][0]]
    chk("aliento: CamL = TransformPosition World->Local de CameraPositionWS",
        tr["cls"] == "TransformPosition" and tr["props"].get("TransformType") == "TRANSFORMPOSSOURCE_Local"
        and ed.ex[tr["links"]["Input"][0]]["cls"] == "CameraPositionWS")
    uvs = [ed.ex[ed.ex[vs]["links"][n_][0]]["props"].get("CoordinateIndex") for n_ in ("Crn", "Sa", "Sb", "Sc")]
    chk("aliento: Crn/Sa/Sb/Sc = TexCoord 0/1/2/3", uvs == [0, 1, 2, 3], str(uvs))
    peor, n_esc = 0.0, 0
    for e in build["customs"][0]["inputs"]:
        if e["src"]["kind"] != "param" or e["type"] != "float":
            continue
        v = ed.value(*ed.ex[vs]["links"][e["name"]], {})
        peor = max(peor, abs(v - am.MAT[e["name"]]))
        n_esc += 1
    chk("aliento: los %d escalares llegan con el default del modelo" % n_esc, peor < 1e-12 and n_esc == 31, "max |dif| %.1e" % peor)
    chk("aliento: 41 parametros (31 escalares + 2 colores + 8 internos), ninguno sobrante",
        r["params"]["total"] == 41 and not r["params"]["sobrantes"], str(r["params"]))
    g = ed.value(*ed.ex[vs]["links"]["AirT"], {})
    chk("aliento: AirT por defecto (sin BP) tiene Glob 0 -> no se dibuja nada", float(np.asarray(g)[3]) == 0.0, str(g))
    chk("aliento: MI_BreathAir_SC creada con el material de padre", ed.assets.get(build["instance"], "").startswith("mi:" + m))
    print("      (%d llamadas a tools simuladas)" % ed.calls)


if __name__ == "__main__":
    que = sys.argv[1:] or ["valle", "rollback", "aliento"]
    if "valle" in que:
        valle()
    if "rollback" in que:
        rollback()
    if "aliento" in que:
        aliento()
    print("\n%s" % ("TODO OK" if not fallas else "%d FALLAS: %s" % (len(fallas), fallas)))
    sys.exit(1 if fallas else 0)
