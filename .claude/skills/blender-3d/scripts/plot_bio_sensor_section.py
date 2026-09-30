# plot_bio_sensor_section.py - dibuja el CORTE del sensor (perfil real del generador, espejado) con la cara de la panza
# hacia ARRIBA, como el boceto de Beltran, y las lineas de los aros encima. Sirve para comparar lado a lado con el boceto.
# Uso: python plot_bio_sensor_section.py <salida.png>   (importa las medidas de gen_bio_sensor.py sin ejecutar Blender)
import ast
import math
import os
import sys

from PIL import Image, ImageDraw

AQUI = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(AQUI, "gen_bio_sensor.py"), encoding="utf-8").read()
# ejecutar solo las definiciones puras (sin bpy): medidas + perfil + filetes
ns = {"math": math}
tree = ast.parse(src)
keep = []
for node in tree.body:
    if isinstance(node, ast.Assign) and all(isinstance(t, ast.Name) for t in node.targets):
        names = [t.id for t in node.targets]
        if any(n in ("argv", "OUT") for n in names):
            continue
        keep.append(node)
    elif isinstance(node, ast.FunctionDef) and node.name in ("dims", "fillet_poly", "profile"):
        keep.append(node)
exec(compile(ast.Module(body=keep, type_ignores=[]), "gen", "exec"), ns)
pts = ns["profile"]()
R, d, rim_top, back, gi, go = ns["dims"]()
K = ns["K"]
S = 800.0 / ns["D"]             # px por mm (el disco ocupa 800 px)
W, H = 1100, 900
cx, cy = W // 2, 470          # centro; la panza hacia ARRIBA (-z del sensor = arriba en la imagen)
img = Image.new("RGB", (W, H), (236, 232, 222))
dr = ImageDraw.Draw(img)


def P(r, z):
    return (cx + r * S, cy + z * S)        # z del sensor: -z (panza) queda arriba


LIGHT = ("Ring", "BackRing", "TipLight")
for sgn in (1, -1):
    for (r0_, z0_, p0_), (r1_, z1_, _) in zip(pts[:-1], pts[1:]):
        col = (235, 150, 40) if p0_ in LIGHT else ((90, 90, 95) if p0_ == "Grip" else (20, 20, 20))
        dr.line([P(sgn * r0_, z0_), P(sgn * r1_, z1_)], fill=col, width=6 if p0_ in LIGHT else 4)
# aros: lineas horizontales sobre la cinta, seguidas, que se apagan
r0 = (gi + go) / 2
n, squeeze, fade = 5, 2.0, 1.0          # como el material: u = v^2 (frenan y se juntan), fade (1 - v)
for k in range(n):
    v = ((k + 0.5) / n) ** (1 / squeeze)
    z = -(rim_top + d["wave_len"] * v)
    f = (1 - v) ** fade
    a = int(20 + 200 * (1 - f))
    dr.line([P(-r0, z), P(r0, z)], fill=(a, a - 5, a - 20), width=3)
dr.text((20, 20), "corte del modelo (cara de la panza arriba) - D %.0f mm - naranjo: luz, gris: media esfera" % ns["D"], fill=(40, 40, 40))
img.save(sys.argv[1] if len(sys.argv) > 1 else "corte.png")
print("CORTE_OK", len(pts), "puntos")
