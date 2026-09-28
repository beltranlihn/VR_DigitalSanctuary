# -*- coding: utf-8 -*-
"""draw_sea_sim.py - EJECUTA draw_sea.dsl (los grafos de BP_DrawSea_SC) sin Unreal, con el interprete de dsl_sim.py, y
lo compara con draw_sea_model.py. Tambien es la UNICA fuente de la tabla de variables del BP (VARS): el armado en
Unreal (apply_draw_sea_bp.py) la lee del JSON que escribe este script.

Verifica:
  - Construction Script con los defaults y con 3 juegos de perillas al azar: W/V/E 0..5 escritos en el MAR = los de
    wave_constants (el hash con el frac de GLSL, aunque el Fraction de Unreal conserve el signo);
  - cada parametro de M_DrawSea_SC / M_DrawDust_SC que no es interno llega a su componente con el valor de su perilla
    (mar y cielo iguales salvo Part 0/1; polvo con SeaZ = Z del actor);
  - los eventos del banco PerfDS0..4 (PerfMode y polvo);
  - cada getter del DSL usa la CATEGORIA de la tabla (el DSL real falla con otra), sin impuros inline (lint de dsl_sim);
  - control negativo: sin la correccion del Fraction, los V (fases) NO coinciden.
Uso:  python draw_sea_sim.py        (escribe VR_Test/Saved/ClaudeScripts/oceano/draw_sea_bp.json)
"""
import json
import math
import os
import re
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import draw_sea_model as dm  # noqa: E402
import dsl_sim as ds  # noqa: E402

RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", "..", ".."))
SALIDA = os.path.join(RAIZ, "VR_Test", "Saved", "ClaudeScripts", "oceano", "draw_sea_bp.json")
CARPETA = "/Game/SoulCharger/Mechanics/Drawing/Scape"
DSL = os.path.join(AQUI, "draw_sea.dsl")

# (nombre, categoria, tipo, default, editable). Tipos: float, bool, LinearColor, MaterialInterface.
D = dm.DEF
VARS = [
    ("SwellAmp", "1-Oleaje", "float", D["SwellAmp"], True),
    ("SwellLenMax", "1-Oleaje", "float", D["SwellLenMax"], True),
    ("SwellLenMin", "1-Oleaje", "float", D["SwellLenMin"], True),
    ("SwellDir", "1-Oleaje", "float", D["SwellDir"], True),
    ("SwellSpread", "1-Oleaje", "float", D["SwellSpread"], True),
    ("Tempo", "1-Oleaje", "float", D["Tempo"], True),
    ("GroupAmt", "2-Grupos", "float", D["GroupAmt"], True),
    ("GroupLen", "2-Grupos", "float", D["GroupLen"], True),
    ("Warp", "2-Grupos", "float", D["Warp"], True),
    ("WarpScale", "2-Grupos", "float", D["WarpScale"], True),
    ("Advance", "3-Avance", "float", D["Advance"], True),
    ("CalmR", "4-CercaLejos", "float", D["CalmR"], True),
    ("CalmMin", "4-CercaLejos", "float", D["CalmMin"], True),
    ("LodNear", "4-CercaLejos", "float", D["LodNear"], True),
    ("LodFar", "4-CercaLejos", "float", D["LodFar"], True),
    ("DeepColor", "5-Superficie", "LinearColor", D["DeepColor"], True),
    ("SurfColor", "5-Superficie", "LinearColor", D["SurfColor"], True),
    ("CrestColor", "5-Superficie", "LinearColor", D["CrestColor"], True),
    ("CrestAmt", "5-Superficie", "float", D["CrestAmt"], True),
    ("LightAz", "5-Superficie", "float", D["LightAz"], True),
    ("LightEl", "5-Superficie", "float", D["LightEl"], True),
    ("WrapPow", "5-Superficie", "float", D["WrapPow"], True),
    ("ZenithColor", "6-CieloNiebla", "LinearColor", D["ZenithColor"], True),
    ("HorizonColor", "6-CieloNiebla", "LinearColor", D["HorizonColor"], True),
    ("SkyPow", "6-CieloNiebla", "float", D["SkyPow"], True),
    ("GlowColor", "6-CieloNiebla", "LinearColor", D["GlowColor"], True),
    ("GlowAmt", "6-CieloNiebla", "float", D["GlowAmt"], True),
    ("GlowPow", "6-CieloNiebla", "float", D["GlowPow"], True),
    ("FogStart", "6-CieloNiebla", "float", D["FogStart"], True),
    ("FogDensity", "6-CieloNiebla", "float", D["FogDensity"], True),
    ("Dither", "6-CieloNiebla", "float", D["Dither"], True),
    ("bShowDust", "7-Polvo", "bool", True, True),
    ("DustColor", "7-Polvo", "LinearColor", D["DustColor"], True),
    ("DustAmt", "7-Polvo", "float", D["DustAmt"], True),
    ("DustSize", "7-Polvo", "float", D["DustSize"], True),
    ("DustBox", "7-Polvo", "float", D["DustBox"], True),
    ("DustFollow", "7-Polvo", "float", D["DustFollow"], True),
    ("DustRise", "7-Polvo", "float", D["DustRise"], True),
    ("DustWobble", "7-Polvo", "float", D["DustWobble"], True),
    ("DustNear", "7-Polvo", "float", D["DustNear"], True),
    ("DustBG", "7-Polvo", "LinearColor", D["DustBG"], True),
    ("SeaMI", "8-Material", "MaterialInterface", CARPETA + "/MI_DrawSea_SC.MI_DrawSea_SC", True),
    ("DustMI", "8-Material", "MaterialInterface", CARPETA + "/MI_DrawDust_SC.MI_DrawDust_SC", True),
    ("Wc", "Z-Interno", "LinearColor", (0.0, 0.0, 0.0, 0.0), False),
    ("Vc", "Z-Interno", "LinearColor", (0.0, 0.0, 0.0, 0.0), False),
    ("Ec", "Z-Interno", "LinearColor", (0.0, 0.0, 0.0, 0.0), False),
    ("PerfMode", "Z-Interno", "float", 0.0, False),
    ("bPerfNoDust", "Z-Interno", "bool", False, False),
]
COMPONENTES = ["Sea", "Sky", "Dust"]
FUNCIONES = [("Wave", [("I", "float"), ("Off", "float")]), ("WaveConstants", []),
             ("LookSea", [("C", "/Script/Engine.MeshComponent")]), ("LookDust", []), ("ApplyLook", []), ("ApplyPerf", [])]

# ---- nodos que dsl_sim todavia no tiene (registrados aca, sin tocar el interprete compartido)
ds._n("Math|Float|Power")(lambda bp, a, b: a ** b)
ds._n("Math|Float|Sqrt")(lambda bp, x: math.sqrt(x))
ds._n("Math|Trig|DegreesToRadians")(lambda bp, x: math.radians(x))
ds._n("Math|Trig|Sin(Radians)")(lambda bp, x: math.sin(x))
ds._n("Math|Trig|Cos(Radians)")(lambda bp, x: math.cos(x))
ds._n("Math|Float|%(Float)")(lambda bp, a, b: math.fmod(a, b))
# el Fraction de UNREAL (UKismetMathLibrary::Fraction = FMath::Fractional = x - trunc x): conserva el signo
ds._n("Math|Float|Fraction")(lambda bp, x: x - math.trunc(x))
ds._n("Transformation|GetActorLocation")(lambda bp: bp.extern["_loc"])


@ds._n("Rendering|Material|SetMaterial")
def _smat(bp, c, idx, mat):
    c.material = (int(idx), mat)


fallas = []


def chk(lbl, ok, info=""):
    print(("OK    " if ok else "FALLA ") + lbl + ("  " + info if info else ""))
    if not ok:
        fallas.append(lbl)


def nuevo_bp(texto, P, loc=(-315.0, 0.0, -120.0)):
    v = {}
    for n, cat, t, d, ed in VARS:
        key = n[1:] if (t == "bool" and n.startswith("b")) else n
        src = P.get(key, P.get(n, d)) if ed else d
        if t == "LinearColor":
            src = np.array(list(src) + [1.0] * (4 - len(src)), float)
        v[n] = src
    comps = {c: ds.Obj(c, params={}, visible=True, collision=None, material=None) for c in COMPONENTES}
    return ds.BP(texto, v, comps, extern={"_loc": np.array(loc, float)})


def perillas_azar(rng):
    P = dict(dm.DEF)
    P.update(SwellAmp=rng.uniform(5, 80), SwellLenMax=rng.uniform(1500, 6000), SwellLenMin=rng.uniform(150, 900),
             SwellDir=rng.uniform(-180, 360), SwellSpread=rng.uniform(0, 140), Tempo=rng.uniform(0.1, 1.0),
             LodNear=rng.uniform(2, 8), LodFar=rng.uniform(1, 15), GroupAmt=rng.uniform(0, 1), Advance=rng.uniform(0, 40),
             DustAmt=rng.uniform(0, 1), FogStart=rng.uniform(0, 3000), DeepColor=tuple(rng.uniform(0, 0.02, 3)))
    return P


def main():
    texto = open(DSL, encoding="utf-8").read()
    tabla = {n: cat for n, cat, t, d, ed in VARS}
    # 1. categorias y nombres de los getters/setters
    malos = []
    for m in re.finditer(r"Variables\|([\w\-]+)\|(Get|Set)(\w+)", texto):
        cat, _, name = m.groups()
        if cat == "Default":
            if name not in COMPONENTES:
                malos.append("Default|" + name)
            continue
        real = name if name in tabla else ("b" + name if "b" + name in tabla else None)
        if real is None or tabla[real] != cat:
            malos.append("%s|%s (tabla: %s)" % (cat, name, tabla.get(real)))
    chk("DSL: cada getter/setter usa la categoria de la tabla VARS", not malos, str(malos))
    usadas = set(re.findall(r"\|(?:Get|Set)(\w+)", texto))
    sin_uso = [n for n, cat, t, d, ed in VARS if (n[1:] if t == "bool" and n.startswith("b") else n) not in usadas]
    chk("DSL: ninguna variable de la tabla sobra", not sin_uso, str(sin_uso))
    chk("DSL: sin funciones impuras inline como dato (lint de dsl_sim)", not ds.lint_impuros(texto), str(ds.lint_impuros(texto)))
    # 2. Construction Script contra el modelo
    build = json.load(open(os.path.join(RAIZ, "VR_Test", "Saved", "ClaudeScripts", "oceano", "draw_sea_build.json"), encoding="utf-8"))
    mats = {m["material"].rsplit("/", 1)[1]: m for m in build["materials"]}
    internos = {"Part", "PerfMode", "SeaZ"} | {"%s%d" % (c, i) for c in "WVE" for i in range(6)}
    rng = np.random.default_rng(11)
    juegos = [("defaults", dict(dm.DEF))] + [("azar%d" % k, perillas_azar(rng)) for k in (1, 2, 3)]
    for nombre, P in juegos:
        bp = nuevo_bp(texto, P)
        bp.run_fn("ConstructionScript")
        W, V, E = dm.wave_constants(P)
        peor = 0.0
        for i in range(6):
            for c, ref in (("W", W), ("V", V), ("E", E)):
                got = bp.comps["Sea"].params["%s%d" % (c, i)]
                peor = max(peor, float(np.max(np.abs(got - np.array(ref[i])) / (np.abs(np.array(ref[i])) + 1e-9))))
        chk("CS %s: W/V/E 0..5 en el mar = wave_constants del modelo" % nombre, peor < 1e-12, "max err rel %.1e" % peor)
        fallos = []
        for comp, mat, part in (("Sea", "M_DrawSea_SC", 0.0), ("Sky", "M_DrawSea_SC", 1.0), ("Dust", "M_DrawDust_SC", None)):
            pr = bp.comps[comp].params
            for p in mats[mat]["params"]:
                n = p["name"]
                if n in ("Part",):
                    if pr.get("Part") != part:
                        fallos.append("%s.Part=%s" % (comp, pr.get("Part")))
                    continue
                if n == "SeaZ":
                    if pr.get("SeaZ") != -120.0:
                        fallos.append("%s.SeaZ=%s" % (comp, pr.get("SeaZ")))
                    continue
                if n == "PerfMode":
                    if pr.get("PerfMode") != 0.0:
                        fallos.append("%s.PerfMode" % comp)
                    continue
                if n in internos:
                    if comp != "Sea" and n not in pr:
                        continue
                    continue
                if n not in pr:
                    fallos.append("%s sin %s" % (comp, n))
                    continue
                want = np.atleast_1d(np.asarray(P[n], float))
                got = np.atleast_1d(np.asarray(pr[n], float))[:want.shape[0]]
                if float(np.max(np.abs(got - want))) > 0.0:
                    fallos.append("%s.%s" % (comp, n))
        chk("CS %s: cada parametro no interno llega a mar / cielo / polvo con su perilla (Part 0/1, SeaZ = Z del actor)" % nombre,
            not fallos, str(fallos[:8]))
        mats_ok = (bp.comps["Sea"].material == (0, bp.v["SeaMI"]) and bp.comps["Sky"].material == (0, bp.v["SeaMI"])
                   and bp.comps["Dust"].material == (0, bp.v["DustMI"]))
        chk("CS %s: MI por perilla y sin colision en los 3 componentes" % nombre,
            mats_ok and all(bp.comps[c].collision == "NoCollision" for c in COMPONENTES))
    # 3. banco
    bp = nuevo_bp(texto, dict(dm.DEF))
    bp.run_fn("ConstructionScript")
    esperado = {"PerfDS0": (0.0, True), "PerfDS1": (1.0, True), "PerfDS2": (2.0, True), "PerfDS3": (3.0, True), "PerfDS4": (0.0, False)}
    malos = []
    for ev, (pm, vis) in esperado.items():
        bp.run_event("Custom|" + ev)
        if not (bp.comps["Sea"].params["PerfMode"] == pm and bp.comps["Sky"].params["PerfMode"] == pm and bp.comps["Dust"].visible == vis):
            malos.append(ev)
    chk("banco PerfDS0..4: PerfMode en mar y cielo, polvo oculto solo en el 4", not malos, str(malos) + " " + str(bp.log[-5:]))
    bp.run_event("EventBeginPlay")
    chk("BeginPlay vuelve a aplicar todo (ApplyLook)", bp.calls.get("ApplyLook") == 2 and bp.comps["Dust"].visible is False,
        "con el ultimo banco (4) el polvo sigue oculto: %s" % bp.comps["Dust"].visible)
    # 4. control negativo: sin la correccion del signo del Fraction, las fases no coinciden
    malo = texto.replace("(select (< _h1 0.0) 1.0 0.0)", "0.0").replace("(select (< _h3 0.0) 1.0 0.0)", "0.0")
    bp = nuevo_bp(malo, dict(dm.DEF))
    bp.run_fn("ConstructionScript")
    W, V, E = dm.wave_constants(dm.DEF)
    difs = sum(1 for i in range(6) for j in (1, 3) if abs(bp.comps["Sea"].params["V%d" % i][j] - V[i][j]) > 1e-9)
    chk("control negativo: sin corregir el Fraction de Unreal, %d de 12 fases cambian" % difs, difs > 0)
    # 5. la tabla para el armado en Unreal
    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    with open(SALIDA, "w", encoding="utf-8") as f:
        json.dump({"blueprint": CARPETA + "/BP_DrawSea_SC",
                   "vars": [{"name": n, "category": c, "type": t, "default": (list(d) if isinstance(d, tuple) else d), "editable": e}
                            for n, c, t, d, e in VARS],
                   "components": COMPONENTES,
                   "functions": [{"name": n, "params": [{"name": a, "type": b} for a, b in ps]} for n, ps in FUNCIONES]},
                  f, ensure_ascii=True, indent=1)
    print("escrito: " + SALIDA)
    print("\n%s" % ("TODO OK" if not fallas else "%d FALLAS: %s" % (len(fallas), fallas)))
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
