# -*- coding: utf-8 -*-
"""compose_loving.py - arma el codigo de cada nodo Custom de Loving desde UNA sola fuente.

FUENTE: VR_Test/Shaders/Loving/LovingLib.ush (la libreria, un struct LVLib con bloques
        '// @fn Nombre' ... '// @end') + VR_Test/Shaders/Loving/wrappers/<Custom>.hlsl
        (cabecera '// @uses A,B' / '// @inputs x,y' / '// @outputs return:Float3,Extra:Float2').

SALIDA: VR_Test/Saved/ClaudeScripts/Loving/composed/<Custom>.values.json — el string JSON
        listo para ObjectTools.set_properties sobre el MaterialExpressionCustom
        (code + outputType + additionalOutputs + description + inputs por nombre).

Por que existe: el HLSL no puede vivir escrito a mano en cada nodo (el brazo y los puentes
comparten el campo; dos copias editadas por MCP se desincronizan). Hasta que el editor se
reinicie y /Project monte VR_Test/Shaders, el texto se pega; despues, IncludeFilePaths.

Se copian SOLO las funciones que el wrapper declara en @uses, y sin las lineas que son solo
comentario (el nodo queda compacto; los comentarios viven en el repo).

Uso:  python compose_loving.py            (compone todos los wrappers)
      python compose_loving.py LovingBallsVS
      Otra libreria con el mismo formato (2026-09-28, el fluido cerebral):
      python compose_loving.py --lib VR_Test/Shaders/Fluid/FluidLib.ush --wrappers VR_Test/Shaders/Fluid/wrappers
                               --out VR_Test/Saved/ClaudeScripts/Fluid/composed [Nombres...]
      (rutas relativas a la raiz del repo; sin argumentos = Loving, identico a antes)
"""
import json
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", "..", ".."))
LIB = os.path.join(RAIZ, "VR_Test", "Shaders", "Loving", "LovingLib.ush")
WRAP_DIR = os.path.join(RAIZ, "VR_Test", "Shaders", "Loving", "wrappers")
OUT_DIR = os.path.join(RAIZ, "VR_Test", "Saved", "ClaudeScripts", "Loving", "composed")


def leer_bloques():
    txt = open(LIB, encoding="utf-8").read()
    bloques = {}
    for m in re.finditer(r"// @fn (\w+)[^\n]*\n(.*?)// @end", txt, re.S):
        bloques[m.group(1)] = m.group(2)
    return bloques


def sin_comentarios(code):
    out = []
    for ln in code.splitlines():
        s = ln.strip()
        if not s or s.startswith("//"):
            continue
        # comentario al final de linea (no hay strings en este HLSL)
        if "//" in ln:
            ln = ln[: ln.index("//")].rstrip()
        out.append(ln)
    return "\n".join(out)


def cabecera(wrap_txt, clave):
    m = re.search(r"// @%s ([^\n]*)" % clave, wrap_txt)
    return [x.strip() for x in m.group(1).split(",")] if m else []


def dependencias(bloques):
    """Para cada funcion, las OTRAS funciones de la libreria que llama (por nombre + '(')."""
    deps = {}
    for n, code in bloques.items():
        cuerpo = sin_comentarios(code)
        deps[n] = [m for m in bloques if m != n and re.search(r"\b%s\s*\(" % m, cuerpo)]
    return deps


def ordenar(usa, bloques, deps):
    """Cierre transitivo de @uses + orden topologico (cada funcion DESPUES de las que llama).
    En HLSL un metodo del struct debe estar definido antes de usarse; asi un @uses incompleto
    o desordenado ya no rompe la compilacion (antes faltaba SminH en un wrapper y nadie lo vio)."""
    orden, visto, en_curso = [], set(), set()

    def visitar(n):
        if n in visto:
            return
        if n in en_curso:
            raise SystemExit("dependencia circular en la libreria: %s" % n)
        en_curso.add(n)
        for d in deps[n]:
            visitar(d)
        en_curso.discard(n)
        visto.add(n)
        orden.append(n)

    for u in usa:
        visitar(u)
    agregadas = [n for n in orden if n not in usa]
    return orden, agregadas


def componer(nombre, bloques):
    wrap_txt = open(os.path.join(WRAP_DIR, nombre + ".hlsl"), encoding="utf-8").read()
    usa = cabecera(wrap_txt, "uses")
    faltan = [u for u in usa if u not in bloques]
    if faltan:
        raise SystemExit("%s usa funciones inexistentes: %s" % (nombre, faltan))
    # las que el CUERPO del wrapper llama (L.Nombre(...)) tambien entran, aunque falten en @uses
    llamadas = [m for m in bloques if re.search(r"\bL\.%s\s*\(" % m, sin_comentarios(wrap_txt))]
    no_decl = [m for m in llamadas if m not in usa]
    usa, agregadas = ordenar(usa + no_decl, bloques, dependencias(bloques))
    if agregadas or no_decl:
        print("  %s: agregadas por dependencia %s" % (nombre, sorted(set(agregadas) | set(no_decl))))
    cuerpo = "\n".join(sin_comentarios(bloques[u]) for u in usa)
    code = "struct LVLib\n{\n" + cuerpo + "\n};\n" + sin_comentarios(wrap_txt) + "\n"
    salidas = cabecera(wrap_txt, "outputs")
    main_t = "Float3"
    extra = []
    for s in salidas:
        n, t = s.split(":")
        if n == "return":
            main_t = t
        else:
            extra.append({"outputName": n, "outputType": "CMOT_" + t})
    values = {
        "code": code,
        "outputType": "CMOT_" + main_t,
        "description": nombre,
        "additionalOutputs": extra,
    }
    os.makedirs(OUT_DIR, exist_ok=True)
    ruta = os.path.join(OUT_DIR, nombre + ".values.json")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(json.dumps(json.dumps(values)))   # doble: el argumento 'values' es un STRING JSON
    with open(os.path.join(OUT_DIR, nombre + ".hlsl"), "w", encoding="utf-8") as f:
        f.write(code)
    return ruta, len(code), cabecera(wrap_txt, "inputs"), extra


def _args():
    """--lib/--wrappers/--out opcionales (relativas a la raiz); el resto son nombres de wrappers."""
    global LIB, WRAP_DIR, OUT_DIR
    nombres, a = [], sys.argv[1:]
    i = 0
    while i < len(a):
        if a[i] in ("--lib", "--wrappers", "--out") and i + 1 < len(a):
            v = a[i + 1] if os.path.isabs(a[i + 1]) else os.path.join(RAIZ, a[i + 1])
            if a[i] == "--lib": LIB = v
            elif a[i] == "--wrappers": WRAP_DIR = v
            else: OUT_DIR = v
            i += 2
        else:
            nombres.append(a[i]); i += 1
    return nombres


def main():
    nombres = _args()
    bloques = leer_bloques()
    nombres = nombres or sorted(os.path.splitext(f)[0] for f in os.listdir(WRAP_DIR) if f.endswith(".hlsl"))
    for n in nombres:
        ruta, largo, ins, extra = componer(n, bloques)
        print("%-18s %5d chars  inputs=%s  extra=%s" % (n, largo, ",".join(ins), [e["outputName"] for e in extra]))


if __name__ == "__main__":
    main()
