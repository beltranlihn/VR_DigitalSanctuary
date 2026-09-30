# render_share_button.py - vista previa de los botones SHARE / DON'T SHARE (gen_share_button.py) con el MISMO sombreado
# falso que el SAVE MELODY aprobado (funciones copiadas de render_save_melody_unlit.py, que corre al importarse):
# base de hormigon con la cinta de luz en el canal, placa con el texto (mascara), slider transparente.
# Tres estados, los dos botones a 30 cm (centro a centro), acostados de frente a la camara como las vistas del SAVE:
#   reposo (Glow 0,7, texto hueso) · hover en SHARE (placa +1 mm, Glow 1,0, texto de luz calida)
#   · confirmacion de SHARE (placa -4 mm, Glow 1,7, la luz da la vuelta al perimetro: Progress 0,6)
# Uso: blender --background <SM_ShareButton_SC.blend> --python render_share_button.py -- <dir_texturas> <salida.png>
import os
import sys

import bpy
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
D, OUT = argv[0], argv[1]
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
    ink = N(nt, "ShaderNodeMix", data_type='RGBA')
    nt.links.new(tg.outputs[0], ink.inputs["Factor"])
    ink.inputs["A"].default_value = (0.93, 0.91, 0.87, 1)
    ink.inputs["B"].default_value = (LIGHT[0] * 1.25, LIGHT[1] * 1.25, LIGHT[2] * 1.25, 1)
    nt.links.new(ink.outputs["Result"], mix.inputs["B"])
    nt.links.new(mix.outputs["Result"], em.inputs["Color"])
    return m


def light(name, gain=1.0):
    m, nt, out = base(name)
    em = N(nt, "ShaderNodeEmission")
    em.inputs["Color"].default_value = (LIGHT[0], LIGHT[1], LIGHT[2], 1)
    g = N(nt, "ShaderNodeValue", name="Glow")
    g.outputs[0].default_value = gain
    nt.links.new(g.outputs[0], em.inputs["Strength"])
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    return m


def slider_mat(name):
    m, nt, out = base(name)
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
    prog.outputs[0].default_value = 0.0
    mr = N(nt, "ShaderNodeMapRange", interpolation_type='SMOOTHSTEP')
    pe = M(nt, 'MULTIPLY', prog.outputs[0], 1.008)
    nt.links.new(M(nt, 'SUBTRACT', pe, sep.outputs["X"]), mr.inputs["Value"])
    mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = 0.0, 0.008
    lvl = M(nt, 'MULTIPLY', mr.outputs["Result"], 0.58)
    comb = N(nt, "ShaderNodeCombineXYZ")
    for i in range(3):
        nt.links.new(M(nt, 'MULTIPLY', lvl, LIGHT[i]), comb.inputs[i])
    nt.links.new(comb.outputs[0], em.inputs["Color"])
    return m


def button(tag, label_png, x):
    """Una copia del boton (acostado, cara +Z) en x; materiales propios (estado independiente)."""
    src = {k: bpy.data.objects[k] for k in ("Base", "Plate", "Slider")}
    mats = {"Body": shaded(tag + "Body", COL["Body"]), "PlateSide": shaded(tag + "PlateSide", COL["PlateSide"]),
            "Ring": light(tag + "Ring", 0.7), "PlateTop": text_top(tag + "PlateTop", os.path.join(D, label_png)),
            "Slider": slider_mat(tag + "Slider")}
    obs = {}
    for k, o in src.items():
        ob = bpy.data.objects.new(tag + k, o.data)
        bpy.context.scene.collection.objects.link(ob)
        ob.matrix_world = Matrix.Translation((x, 0, 0))
        for i, s in enumerate(ob.material_slots):
            part = o.data.materials[i].name.replace("M_ShareButton_", "").split(".")[0]
            s.link = 'OBJECT'
            s.material = mats[part]
        obs[k] = ob
    return obs, mats


def main():
    scn = bpy.context.scene
    for k in ("Base", "Plate", "Slider", "Trace"):
        bpy.data.objects[k].hide_render = True
    share, ms = button("S_", "T_Share_Text.png", -0.15)
    dont, md = button("D_", "T_DontShare_Text.png", 0.15)
    w = bpy.data.worlds.new("Negro")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)
    scn.world = w
    scn.render.engine = 'CYCLES'
    scn.cycles.samples = 48
    scn.cycles.transparent_max_bounces = 16
    scn.view_settings.view_transform = 'Standard'
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = 'OPTIX'
        prefs.get_devices()
        for dv in prefs.devices:
            dv.use = dv.type == 'OPTIX'
        scn.cycles.device = 'GPU'
    except Exception:
        pass
    scn.render.resolution_x, scn.render.resolution_y = 1400, 520
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    scn.collection.objects.link(cam)
    scn.camera = cam
    tg = Vector((0.0, 0.0, 0.01))
    cam.location = tg + Vector((0.0, -0.40, 1.0)).normalized() * 1.05
    cam.rotation_euler = (tg - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = 55
    states = [("reposo", 0.0, 0.7, 0.0, 0.0), ("hover", 0.001, 1.0, 1.0, 0.0), ("confirma", -0.004, 1.7, 1.0, 0.6)]
    outs = []
    for nm, dz, glow, tglow, prog in states:
        share["Plate"].matrix_world = Matrix.Translation((-0.15, 0, dz))
        ms["Ring"].node_tree.nodes["Glow"].outputs[0].default_value = glow
        ms["PlateTop"].node_tree.nodes["TextGlow"].outputs[0].default_value = tglow
        ms["Slider"].node_tree.nodes["Progress"].outputs[0].default_value = prog
        p = os.path.splitext(OUT)[0] + "_" + nm + ".png"
        scn.render.filepath = p
        bpy.ops.render.render(write_still=True)
        outs.append(p)
    print("SHARE_RENDER_OK", outs)


main()
