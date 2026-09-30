# render_quest_controller_unlit.py - vista previa del mando COMO SE VA A VER EN LA OBRA: sin luces (unlit), con el
# sombreado falso del material de Unreal (el de la paleta: ambiente por hemisferio + luz envolvente + relleno de
# camara + brillo propio) y un borde de luz (fresnel) para que el cuerpo negro no se pierda en un nivel oscuro.
# Lee los FBX exportados (de paso valida que se leen bien: triangulos, UVs, mascara de la tapa, pivote del gatillo).
# Uso: blender --background --python render_quest_controller_unlit.py -- <dir> <salida> [apretar_grados]
import json
import math
import os
import sys

import bpy
from mathutils import Quaternion, Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
D = argv[0]
OUT = argv[1]
PRESS = float(argv[2]) if len(argv) > 2 else 14.0
P = {"Ambient": 0.30, "Diffuse": 0.55, "Wrap": 0.4, "Fill": 0.25, "SelfGlow": 0.10, "Rim": 0.10, "RimPow": 3.0,
     "Body": (0.035, 0.035, 0.038), "Cap": (0.78, 0.77, 0.74), "Pressed": (1.0, 0.72, 0.45), "PressedGlow": 0.35,
     "RimColor": (1.0, 0.92, 0.82), "L": Vector((-0.35, -0.30, 0.88)).normalized()}


def node(nt, kind, **kw):
    n = nt.nodes.new(kind)
    for k, v in kw.items():
        setattr(n, k, v)
    return n


def math_(nt, op, a, b=None, clamp=False):
    n = node(nt, "ShaderNodeMath", operation=op, use_clamp=clamp)
    for i, x in enumerate((a, b)):
        if x is None:
            continue
        if isinstance(x, (int, float)):
            n.inputs[i].default_value = x
        else:
            nt.links.new(x, n.inputs[i])
    return n.outputs[0]


def unlit_material(name, with_cap, pressed=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = node(nt, "ShaderNodeOutputMaterial")
    em = node(nt, "ShaderNodeEmission")
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    geo = node(nt, "ShaderNodeNewGeometry")
    dl = node(nt, "ShaderNodeVectorMath", operation='DOT_PRODUCT')
    nt.links.new(geo.outputs["Normal"], dl.inputs[0])
    dl.inputs[1].default_value = P["L"]
    key = math_(nt, 'DIVIDE', math_(nt, 'ADD', dl.outputs["Value"], P["Wrap"]), 1.0 + P["Wrap"], clamp=True)
    dv = node(nt, "ShaderNodeVectorMath", operation='DOT_PRODUCT')
    nt.links.new(geo.outputs["Normal"], dv.inputs[0])
    nt.links.new(geo.outputs["Incoming"], dv.inputs[1])
    fill = math_(nt, 'MAXIMUM', dv.outputs["Value"], 0.0)
    sep = node(nt, "ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Normal"], sep.inputs[0])
    hemi = math_(nt, 'MULTIPLY_ADD', sep.outputs["Z"], 0.5)
    hemi.node.inputs[2].default_value = 0.5
    shade = math_(nt, 'ADD', math_(nt, 'ADD', math_(nt, 'MULTIPLY', hemi, P["Ambient"]), math_(nt, 'MULTIPLY', key, P["Diffuse"])),
                  math_(nt, 'ADD', math_(nt, 'MULTIPLY', fill, P["Fill"]), P["SelfGlow"]))
    rim = math_(nt, 'MULTIPLY', math_(nt, 'POWER', math_(nt, 'SUBTRACT', 1.0, fill, clamp=True), P["RimPow"]), P["Rim"])
    if with_cap:
        uv = node(nt, "ShaderNodeUVMap", uv_map="CapMask")
        sx = node(nt, "ShaderNodeSeparateXYZ")
        nt.links.new(uv.outputs["UV"], sx.inputs[0])
        mr = node(nt, "ShaderNodeMapRange", interpolation_type='SMOOTHSTEP')
        mr.inputs["From Min"].default_value = -0.15
        mr.inputs["From Max"].default_value = 0.15
        nt.links.new(sx.outputs["X"], mr.inputs["Value"])
        mix = node(nt, "ShaderNodeMix", data_type='RGBA')
        mix.inputs["A"].default_value = P["Body"] + (1,)
        mix.inputs["B"].default_value = P["Cap"] + (1,)
        nt.links.new(mr.outputs["Result"], mix.inputs["Factor"])
        alb = mix.outputs["Result"]
    else:
        mix = node(nt, "ShaderNodeMix", data_type='RGBA')
        mix.inputs["A"].default_value = P["Cap"] + (1,)
        mix.inputs["B"].default_value = P["Pressed"] + (1,)
        mix.inputs["Factor"].default_value = pressed
        alb = mix.outputs["Result"]
    col = node(nt, "ShaderNodeMix", data_type='RGBA', blend_type='MULTIPLY')
    col.inputs["Factor"].default_value = 1.0
    nt.links.new(alb, col.inputs["A"])
    sh = node(nt, "ShaderNodeCombineXYZ")
    for k in range(3):
        nt.links.new(math_(nt, 'ADD', shade, P["PressedGlow"] * pressed), sh.inputs[k])
    nt.links.new(sh.outputs[0], col.inputs["B"])
    rimc = node(nt, "ShaderNodeMix", data_type='RGBA', blend_type='ADD')
    nt.links.new(rim, rimc.inputs["Factor"])
    nt.links.new(col.outputs["Result"], rimc.inputs["A"])
    rimc.inputs["B"].default_value = P["RimColor"] + (1,)
    nt.links.new(rimc.outputs["Result"], em.inputs["Color"])
    return m


bpy.ops.wm.read_factory_settings(use_empty=True)
obs = {}
for nm in ("SM_QuestCtrl_Body_R_SC", "SM_QuestCtrl_Trigger_R_SC"):
    bpy.ops.import_scene.fbx(filepath=os.path.join(D, nm + ".fbx"))
    ob = [o for o in bpy.context.selected_objects if o.type == 'MESH'][0]
    obs[nm] = ob
    me = ob.data
    print("FBX", nm, "tris", sum(len(p.vertices) - 2 for p in me.polygons), "uv", [u.name for u in me.uv_layers],
          "origen_cm", [round(x * 100, 3) for x in ob.matrix_world.translation], "custom_normals", me.has_custom_normals)
body, trig = obs["SM_QuestCtrl_Body_R_SC"], obs["SM_QuestCtrl_Trigger_R_SC"]
hinge = json.load(open(os.path.join(D, "qc_trigger_hinge.json")))
ax = Vector(hinge["axis"]) * hinge["press_sign"]
body.data.materials.clear()
body.data.materials.append(unlit_material("Body", True))
m_rest = unlit_material("TrigRest", False, 0.0)
m_press = unlit_material("TrigPress", False, 1.0)
scn = bpy.context.scene
w = bpy.data.worlds.new("W")
w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.0, 0.0, 0.0, 1)
scn.world = w
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
scn.collection.objects.link(cam)
scn.camera = cam
scn.render.engine = 'CYCLES'
scn.cycles.samples = 32
scn.cycles.use_denoising = False
scn.render.resolution_x = scn.render.resolution_y = 700
scn.view_settings.view_transform = 'Standard'
c = Vector((0.005, 0.015, -0.03))
V = {"lado": (1, 0.05, 0.15), "lado_int": (-1, 0.05, 0.15), "frente": (0.2, -1, 0.3), "arriba": (0.05, 0.1, 1),
     "tres_cuartos": (0.7, -0.6, 0.5), "mano": (0.35, 0.55, 0.75), "apretado": (1, 0.05, 0.15)}
trig.rotation_mode = 'QUATERNION'
for nm, d in V.items():
    pr = nm == "apretado"
    trig.rotation_quaternion = Quaternion(ax, math.radians(PRESS)) if pr else Quaternion()
    trig.data.materials.clear()
    trig.data.materials.append(m_press if pr else m_rest)
    dv = Vector(d).normalized()
    cam.location = c + dv * 0.34
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = 70
    scn.render.filepath = os.path.join(OUT, "unlit_" + nm + ".png")
    bpy.ops.render.render(write_still=True)
print("UNLIT_OK")
