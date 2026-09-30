# render_save_melody_unlit.py - vista previa del boton SAVE MELODY como en la obra (sin luces, fondo negro, sombreado
# falso de la paleta): base con la cinta de luz en el canal, placa con el texto (mascara blanca), slider transparente.
# Estados: disponible / hover (luz sube, placa sube 1 mm) / gatillo (placa se hunde 4 mm, luz al maximo, carga 3 s).
# Uso: blender --background --python render_save_melody_unlit.py -- <dir> <salida> [progress] [cuadros_anim]
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
D, OUT = argv[0], argv[1]
PROGRESS = float(argv[2]) if len(argv) > 2 else 0.6
ANIM = int(argv[3]) if len(argv) > 3 else 0
TRAVEL = 0.004
HOVER_UP = 0.001
L = Vector((-0.35, -0.30, 0.88)).normalized()
SH = {"Ambient": 0.30, "Diffuse": 0.55, "Wrap": 0.4, "Fill": 0.25, "SelfGlow": 0.10}
COL = {"Body": (0.62, 0.56, 0.48), "PlateSide": (0.70, 0.64, 0.55)}
TOP = (0.56, 0.51, 0.45)
LIGHT = (1.0, 0.72, 0.45)


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


def shaded(name, albedo):
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
    tex.inputs["Scale"].default_value = 400.0
    k = M(nt, 'MULTIPLY', shade, M(nt, 'MULTIPLY_ADD', tex.outputs["Fac"], 0.12, 0.94))
    comb = N(nt, "ShaderNodeCombineXYZ")
    for i in range(3):
        nt.links.new(M(nt, 'MULTIPLY', k, albedo[i]), comb.inputs[i])
    nt.links.new(comb.outputs[0], em.inputs["Color"])
    return m


def text_top(name, img_path):
    """Hormigon del tope + texto blanco por mascara (UV1 TextUV), como UNDO/REDO de la paleta."""
    m = shaded(name, TOP)
    nt = m.node_tree
    em = [n for n in nt.nodes if n.type == 'EMISSION'][0]
    src = em.inputs["Color"].links[0].from_socket
    uv = N(nt, "ShaderNodeUVMap", uv_map="TextUV")
    tex = N(nt, "ShaderNodeTexImage")
    tex.image = bpy.data.images.load(img_path)
    tex.image.colorspace_settings.name = 'Non-Color'
    tex.extension = 'CLIP'
    nt.links.new(uv.outputs["UV"], tex.inputs["Vector"])
    mix = N(nt, "ShaderNodeMix", data_type='RGBA')
    nt.links.new(tex.outputs["Color"], mix.inputs["Factor"])
    nt.links.new(src, mix.inputs["A"])
    tg = N(nt, "ShaderNodeValue", name="TextGlow")
    tg.outputs[0].default_value = 0.0
    ink = N(nt, "ShaderNodeMix", data_type='RGBA')          # tinta: blanco hueso -> luz calida
    nt.links.new(tg.outputs[0], ink.inputs["Factor"])
    ink.inputs["A"].default_value = (0.93, 0.91, 0.87, 1)
    ink.inputs["B"].default_value = (LIGHT[0] * 1.25, LIGHT[1] * 1.25, LIGHT[2] * 1.25, 1)
    nt.links.new(ink.outputs["Result"], mix.inputs["B"])
    nt.links.new(mix.outputs["Result"], em.inputs["Color"])
    return m


def light(name, gain=1.0):
    """Luz con un nodo "Glow" (el BP en Unreal lo sube al apretar: reposo 0,7 -> apretado 1,6)."""
    m, nt, out = base(name)
    em = N(nt, "ShaderNodeEmission")
    em.inputs["Color"].default_value = (LIGHT[0], LIGHT[1], LIGHT[2], 1)
    g = N(nt, "ShaderNodeValue", name="Glow")
    g.outputs[0].default_value = gain
    nt.links.new(g.outputs[0], em.inputs["Strength"])
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    return m


def slider_mat():
    """Pista tenue + parte cargada (UV.x < Progress) con borde suave; translucido aditivo."""
    m, nt, out = base("Slider")
    add = N(nt, "ShaderNodeAddShader")
    tr = N(nt, "ShaderNodeBsdfTransparent")
    em = N(nt, "ShaderNodeEmission")
    nt.links.new(tr.outputs[0], add.inputs[0])
    nt.links.new(em.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], out.inputs["Surface"])
    uv = N(nt, "ShaderNodeUVMap", uv_map="UVMap")
    sep = N(nt, "ShaderNodeSeparateXYZ")
    nt.links.new(uv.outputs["UV"], sep.inputs[0])
    prog = N(nt, "ShaderNodeValue", name="Progress")
    prog.outputs[0].default_value = PROGRESS
    mr = N(nt, "ShaderNodeMapRange", interpolation_type='SMOOTHSTEP')
    # Progress efectivo = Progress*(1+2e) con borde suave [0, 2e]: en 0 no asoma nada y en 1 cierra la costura
    pe = M(nt, 'MULTIPLY', prog.outputs[0], 1.008)
    nt.links.new(M(nt, 'SUBTRACT', pe, sep.outputs["X"]), mr.inputs["Value"])
    mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = 0.0, 0.008
    lvl = M(nt, 'MULTIPLY', mr.outputs["Result"], 0.58)        # Beltran: el slider es TRANSPARENTE; solo se ve lo cargado
    comb = N(nt, "ShaderNodeCombineXYZ")
    for i in range(3):
        nt.links.new(M(nt, 'MULTIPLY', lvl, LIGHT[i]), comb.inputs[i])
    nt.links.new(comb.outputs[0], em.inputs["Color"])
    return m


bpy.ops.wm.read_factory_settings(use_empty=True)
obs = {}
for nm in ("SM_SaveMelody_Base_SC", "SM_SaveMelody_Plate_SC", "SM_SaveMelody_Slider_SC"):
    bpy.ops.import_scene.fbx(filepath=os.path.join(D, nm + ".fbx"))
    ob = [o for o in bpy.context.selected_objects if o.type == 'MESH'][0]
    obs[nm] = ob
    print("FBX", nm, "tris", sum(len(p.vertices) - 2 for p in ob.data.polygons), "slots", [s.name for s in ob.material_slots])
mats = {k: shaded(k, c) for k, c in COL.items()}
mats["Ring"] = light("Ring", 0.7)
mats["PlateTop"] = text_top("PlateTop", os.path.join(D, "T_SaveMelody_Text.png"))
mats["Slider"] = slider_mat()
for ob in obs.values():
    for s in ob.material_slots:
        key = s.name.replace("M_SaveMelody_", "").split(".")[0]
        s.material = mats[key]
button = obs["SM_SaveMelody_Plate_SC"]
scn = bpy.context.scene
w = bpy.data.worlds.new("W")
w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)
scn.world = w
scn.render.engine = 'CYCLES'
scn.cycles.samples = 48
scn.cycles.transparent_max_bounces = 16
scn.render.resolution_x = scn.render.resolution_y = 800
scn.view_settings.view_transform = 'Standard'
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
scn.collection.objects.link(cam)
scn.camera = cam
c0 = Vector((0, 0, 0.01))
V = {"frente": ((0.0, -0.18, 1.0), 0.42, 0.0), "hover": ((0.3, -0.7, 0.8), 0.42, -1.0),
     "apretado": ((0.3, -0.7, 0.8), 0.42, 1.0), "canto": ((0.0, -1.0, 0.15), 0.42, 0.0)}


def shot(nm, d, dist, press, path):
    """press: 0 disponible, -1 hover (sube 1 mm, luz media), 0..1 gatillo (se hunde, luz al maximo)."""
    hover = press < 0
    p = max(press, 0.0)
    button.location = (0, 0, HOVER_UP if hover else -TRAVEL * p)
    mats["Ring"].node_tree.nodes["Glow"].outputs[0].default_value = 1.0 if hover else 0.7 + 1.0 * p
    mats["PlateTop"].node_tree.nodes["TextGlow"].outputs[0].default_value = 1.0 if (hover or p > 0) else 0.0
    dv = Vector(d).normalized()
    cam.location = c0 + dv * dist
    cam.rotation_euler = (c0 - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = 60
    scn.render.filepath = path
    bpy.ops.render.render(write_still=True)


if ANIM:
    scn.render.resolution_x = scn.render.resolution_y = 520
    scn.cycles.samples = 24
    pn = mats["Slider"].node_tree.nodes["Progress"]
    for f in range(ANIM):
        t = f / ANIM          # disponible (0-0,1) -> hover (0,1-0,25) -> gatillo y carga (0,25-0,85) -> completo (0,85-1)
        if t < 0.1:
            press, prog = 0.0, 0.0
        elif t < 0.25:
            press, prog = -1.0, 0.0
        elif t < 0.85:
            press, prog = min(1.0, (t - 0.25) / 0.05), (t - 0.25) / 0.6
        else:
            press, prog = 1.0, 1.0
        pn.outputs[0].default_value = prog
        d, dist, _ = V["hover"]
        shot("anim", d, dist, press, os.path.join(OUT, "sm_anim_%03d.png" % f))
    print("SM_ANIM_OK")
    raise SystemExit
for nm, (d, dist, press) in V.items():
    shot(nm, d, dist, press, os.path.join(OUT, "sm_" + nm + ".png"))
print("SM_RENDER_OK")
