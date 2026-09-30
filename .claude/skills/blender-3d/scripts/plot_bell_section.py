# plot_bell_section.py - dibuja el CORTE del timbre (perfiles reales de gen_bell.py: base, boton y slider) con las partes
# en color, para compararlo lado a lado con el PDF. Uso: python plot_bell_section.py <salida.png> [apretado 0..1]
import ast
import math
import os
import sys

from PIL import Image, ImageDraw

AQUI = os.path.dirname(os.path.abspath(__file__))
ns = {"math": math}
lib = ast.parse(open(os.path.join(AQUI, "revolve_lib.py"), encoding="utf-8").read())
keep = [n for n in lib.body if isinstance(n, ast.FunctionDef) and n.name == "fillet_poly"
        or isinstance(n, ast.Assign) and any(getattr(t, "id", "") == "ARC_STEP" for t in n.targets)]
exec(compile(ast.Module(body=keep, type_ignores=[]), "lib", "exec"), ns)
src = ast.parse(open(os.path.join(AQUI, "gen_bell.py"), encoding="utf-8").read())
keep = []
for node in src.body:
    if isinstance(node, ast.Assign) and all(isinstance(t, (ast.Name, ast.Tuple)) for t in node.targets):
        names = [getattr(t, "id", "") for t in node.targets]
        if any(n in ("argv", "OUT") for n in names):
            continue
        keep.append(node)
    elif isinstance(node, ast.FunctionDef) and node.name in ("u", "base_profile", "button_profile", "slider_profile"):
        keep.append(node)
exec(compile(ast.Module(body=keep, type_ignores=[]), "bell", "exec"), ns)
press = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
S = 1000.0 / (2 * ns["S_OUT"] + 20)
W, H = 1100, 520
cx, cy = W // 2, 380
img = Image.new("RGB", (W, H), (245, 244, 240))
dr = ImageDraw.Draw(img)
COL = {"Ring": (235, 150, 40), "Slider": (70, 140, 220), "Pocket": (120, 120, 125), "ButtonTop": (200, 60, 60)}


def P(r, h):
    return (cx + r * S, cy - h * S)


def draw(pts, dz=0.0, closed=False):
    seq = list(zip(pts, pts[1:] + ([pts[0]] if closed else [])))
    for sgn in (1, -1):
        for (r0, h0, p0), (r1, h1, _) in seq:
            dr.line([P(sgn * r0, h0 + dz), P(sgn * r1, h1 + dz)], fill=COL.get(p0, (20, 20, 20)), width=5 if p0 in COL else 3)


draw(ns["base_profile"]())
draw(ns["button_profile"](), dz=-ns["TRAVEL"] * press)
draw(ns["slider_profile"](), closed=True)
dr.text((20, 16), "corte del modelo - D %.0f mm - naranjo: luz, azul: slider, rojo: hendidura del boton, gris: bolsillo" % (2 * ns["R"]), fill=(40, 40, 40))
img.save(sys.argv[1] if len(sys.argv) > 1 else "corte_timbre.png")
print("CORTE_OK")
