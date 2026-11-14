# render_hang.py - vista previa del HANG como en la obra (sin luces, fondo negro, sombreado falso de la paleta de Drawing):
# cuerpo de hormigon calido, pads del tono de los botones de pincel, ranura de luz con el color de cada nota.
# Abre SM_Hang_SC.blend (lo deja gen_hang.py con los 9 pads en su lugar).
# Uso: blender --background --python render_hang.py -- <dir> <salida> [pad_apretado]
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
D, OUT = argv[0], argv[1]
PRESSED = argv[2] if len(argv) > 2 else "pad3"
TRAVEL = 0.005
L = Vector((-0.35, -0.30, 0.88)).normalized()
SH = {"Ambient": 0.30, "Diffuse": 0.55, "Wrap": 0.4, "Fill": 0.25, "SelfGlow": 0.10}
COL = {"Body": (0.62, 0.56, 0.48), "Pocket": (0.07, 0.065, 0.06), "PadTop": (0.42, 0.39, 0.35)}
GROOVE = (1.0, 0.72, 0.45)
# colores de nota (los de NoteColor del BP: tono 35 - 150 * (nota mod 12)/12, sat 0,55) para Re hexatonica
NOTE_PC = [2, 4, 6, 9, 11, 1, 2, 4, 6]


def hsv(h, s, v):
    h = (h % 360) / 60.0
    i = int(h)
    f = h - i
    p, q, t = v * (1 - s), v * (1 - s * f), v * (1 - s * (1 - f))
    return [(v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q)][i % 6]


def N(nt, kind, **kw):
    n = nt.nodes.new(kind)
    for k, v in kw.items():
        setattr(n, k, v)
    return n


def M(nt, op, a, b=None, c=None, clamp=False):
    n = N(nt, "ShaderNodeMath", operation=op, use_clamp=clamp)
    for i, x in enumerate((a, b, c)):
        if x is None:
            continue
        if isinstance(x, (int, float)):
            n.inputs[i].default_value = x
        else:
            nt.links.new(x, n.inputs[i])
    return n.outputs[0]


def base(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    return m, nt, N(nt, "ShaderNodeOutputMaterial")


def shaded(name, albedo, flash=(0, 0, 0), flash_k=0.0):
    m, nt, out = base(name)
    em = N(nt, "ShaderNodeEmission")
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    geo = N(nt, "ShaderNodeNewGeometry")
    dl = N(nt, "ShaderNodeVectorMath", operation='DOT_PRODUCT')
    nt.links.new(geo.outputs["Normal"], dl.inputs[0])
    dl.inputs[1].default_value = L
    key = M(nt, 'DIVIDE', M(nt, 'ADD', dl.outputs["Value"], SH["Wrap"]), 1 + SH["Wrap"], clamp=True)
    dv = N(nt, "ShaderNodeVectorMath", operation='DOT_PRODUCT')
    nt.links.new(geo.outputs["Normal"], dv.inputs[0])
    nt.links.new(geo.outputs["Incoming"], dv.inputs[1])
    fill = M(nt, 'MAXIMUM', dv.outputs["Value"], 0.0)
    sep = N(nt, "ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Normal"], sep.inputs[0])
    hemi = M(nt, 'MULTIPLY_ADD', sep.outputs["Z"], 0.5, 0.5)
    shade = M(nt, 'ADD', M(nt, 'ADD', M(nt, 'MULTIPLY', hemi, SH["Ambient"]), M(nt, 'MULTIPLY', key, SH["Diffuse"])),
              M(nt, 'ADD', M(nt, 'MULTIPLY', fill, SH["Fill"]), SH["SelfGlow"]))
    tex = N(nt, "ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value = 300.0
    k = M(nt, 'MULTIPLY', shade, M(nt, 'MULTIPLY_ADD', tex.outputs["Fac"], 0.12, 0.94))
    comb = N(nt, "ShaderNodeCombineXYZ")
    for i in range(3):
        nt.links.new(M(nt, 'ADD', M(nt, 'MULTIPLY', k, albedo[i]), flash[i] * flash_k), comb.inputs[i])
    nt.links.new(comb.outputs[0], em.inputs["Color"])
    return m


def light(name, col, gain):
    m, nt, out = base(name)
    em = N(nt, "ShaderNodeEmission")
    em.inputs["Color"].default_value = (col[0], col[1], col[2], 1)
    em.inputs["Strength"].default_value = gain
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    return m


bpy.ops.wm.open_mainfile(filepath=os.path.join(D, "SM_Hang_SC.blend"))
scn = bpy.context.scene
for nm in ("SM_Hang_Pad_SC", "SM_Hang_Ding_SC"):
    bpy.data.objects[nm].hide_render = True
body = bpy.data.objects["SM_Hang_Body_SC"]
body.data.materials[0] = shaded("Body", COL["Body"])
body.data.materials[1] = shaded("Pocket", COL["Pocket"])
body.data.materials[2] = light("Groove", GROOVE, 0.35)
order = ["ding"] + ["pad%d" % k for k in range(1, 9)]
for i, nm in enumerate(order):
    ob = bpy.data.objects["Hang_" + nm]
    ob.data = ob.data.copy()
    c = hsv(35 - 150 * NOTE_PC[i] / 12.0, 0.55, 1.0)
    hot = (nm == PRESSED)
    ob.data.materials[0] = shaded("Top_" + nm, COL["PadTop"], c, 0.35 if hot else 0.0)
    ob.data.materials[1] = light("Side_" + nm, c, 3.0 if hot else 0.9)
    if hot:
        ob.matrix_world = ob.matrix_world @ Matrix.Translation((0, 0, -TRAVEL))
w = bpy.data.worlds.new("W")
w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)
scn.world = w
scn.render.engine = 'CYCLES'
scn.cycles.samples = 48
scn.render.resolution_x, scn.render.resolution_y = 1000, 760
scn.view_settings.view_transform = 'Standard'
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
scn.collection.objects.link(cam)
scn.camera = cam
c0 = Vector((0, 0, 0.11))
V = {"jugador": ((-1.0, 0.0, 0.85), 1.15), "tres_cuartos": ((-0.7, -0.6, 0.6), 1.25), "arriba": ((0.0, -0.001, 1.0), 1.2),
     "canto": ((0.0, -1.0, 0.08), 1.2), "cerca": ((-0.75, 0.25, 0.55), 0.55)}
for nm, (d, dist) in V.items():
    dv = Vector(d).normalized()
    cam.location = c0 + dv * dist
    cam.rotation_euler = (c0 - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = 50
    scn.render.filepath = os.path.join(OUT, "hang_" + nm + ".png")
    bpy.ops.render.render(write_still=True)
print("HANG_RENDER_OK")
