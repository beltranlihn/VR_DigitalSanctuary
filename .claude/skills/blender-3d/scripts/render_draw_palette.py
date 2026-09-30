# render_draw_palette.py - presentacion de la paleta de dibujo (Cycles): arma la paleta completa con las mallas de
# gen_draw_palette.py (8 cunas = la misma malla girada, redo = undo girado +28), hormigon pulido calido, ranura
# encendida, un color y un pincel SELECCIONADOS (suben KEY_SEL_UP). Vistas en <outdir>/pal_<vista>.png
# Uso: blender --background SM_DrawPalette_SC.blend --python render_draw_palette.py -- <outdir> [vistas]
import importlib.util
import math
import os
import sys
import traceback

import bpy
from mathutils import Vector

AQUI = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("gdp", os.path.join(AQUI, "gen_draw_palette.py"))
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else AQUI
ONLY = argv[1].split(",") if len(argv) > 1 else None
COLORS = [(0.78, 0.40, 0.30), (0.82, 0.63, 0.32), (0.47, 0.60, 0.46), (0.40, 0.52, 0.70)]   # terracota, ocre, salvia, azul
SEL_COLOR, SEL_BRUSH = 1, 1
# iconos A LO LARGO de cada boton (pedido de Beltran): en el marco de la cuna (IconUV: arriba = radial afuera) el
# icono, que viene en diagonal (~45 grados), se gira -45 para quedar radial; y se agranda para ocupar el largo.
ICON_ROT, ICON_SCALE = -45.0, 1.3


def concrete(name, color, rough=0.95, glow=0.0, mask=None, mask_uv=None, mask_rot=0.0, ink=(0.96, 0.94, 0.90), alpha=1.0, mask_glow=0.8, mask_scale=1.0):
    """Hormigon MATE (pedido de Beltran: nada de reflexiones, materiales rugosos): especular 0, rugosidad alta,
    manchado + grano. mask = imagen blanco/negro (icono o texto) impresa en tono ink por el UV mask_uv, girada mask_rot."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mott = nt.nodes.new("ShaderNodeTexNoise")
    mott.inputs["Scale"].default_value = 9.0
    mott.inputs["Detail"].default_value = 5.0
    nt.links.new(tc.outputs["Object"], mott.inputs["Vector"])
    grain = nt.nodes.new("ShaderNodeTexVoronoi")
    grain.inputs["Scale"].default_value = 420.0
    nt.links.new(tc.outputs["Object"], grain.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = tuple(x * 0.84 for x in color) + (1,)
    ramp.color_ramp.elements[1].color = tuple(color) + (1,)
    nt.links.new(mott.outputs["Fac"], ramp.inputs["Fac"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["To Min"].default_value = 0.90
    mr.inputs["To Max"].default_value = 1.05
    nt.links.new(grain.outputs["Distance"], mr.inputs["Value"])
    mul = nt.nodes.new("ShaderNodeVectorMath")
    mul.operation = 'SCALE'
    nt.links.new(ramp.outputs["Color"], mul.inputs[0])
    nt.links.new(mr.outputs["Result"], mul.inputs["Scale"])
    col_out = mul.outputs["Vector"]
    if mask:
        uvn = nt.nodes.new("ShaderNodeUVMap")
        uvn.uv_map = mask_uv
        sub = nt.nodes.new("ShaderNodeVectorMath")
        sub.operation = 'SUBTRACT'
        sub.inputs[1].default_value = (0.5, 0.5, 0.0)
        nt.links.new(uvn.outputs["UV"], sub.inputs[0])
        rot = nt.nodes.new("ShaderNodeVectorRotate")
        rot.rotation_type = 'Z_AXIS'
        rot.inputs["Angle"].default_value = mask_rot
        nt.links.new(sub.outputs["Vector"], rot.inputs["Vector"])
        scl = nt.nodes.new("ShaderNodeVectorMath")
        scl.operation = 'SCALE'
        scl.inputs["Scale"].default_value = 1.0 / mask_scale
        nt.links.new(rot.outputs["Vector"], scl.inputs[0])
        add = nt.nodes.new("ShaderNodeVectorMath")
        add.operation = 'ADD'
        add.inputs[1].default_value = (0.5, 0.5, 0.0)
        nt.links.new(scl.outputs["Vector"], add.inputs[0])
        img = nt.nodes.new("ShaderNodeTexImage")
        img.image = bpy.data.images.load(mask, check_existing=True)
        img.extension = 'CLIP'
        nt.links.new(add.outputs["Vector"], img.inputs["Vector"])
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = 'RGBA'
        nt.links.new(img.outputs["Color"], mix.inputs["Factor"])
        nt.links.new(col_out, mix.inputs["A"])
        mix.inputs["B"].default_value = tuple(ink) + (1,)
        col_out = mix.outputs["Result"]
        if mask_glow > 0:   # iconos y textos BLANCOS (pedido de Beltran) con un poco de emision solo en el dibujo
            gm = nt.nodes.new("ShaderNodeMath")
            gm.operation = 'MULTIPLY'
            gm.inputs[1].default_value = mask_glow
            nt.links.new(img.outputs["Color"], gm.inputs[0])
            bs.inputs["Emission Color"].default_value = tuple(ink) + (1,)
            nt.links.new(gm.outputs["Value"], bs.inputs["Emission Strength"])
    nt.links.new(col_out, bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = rough
    bs.inputs["Specular IOR Level"].default_value = 0.0
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.08
    bump.inputs["Distance"].default_value = 0.0008
    nt.links.new(grain.outputs["Distance"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bs.inputs["Normal"])
    if glow > 0:
        bs.inputs["Emission Color"].default_value = tuple(color) + (1,)
        bs.inputs["Emission Strength"].default_value = glow
    if alpha < 1.0:
        bs.inputs["Alpha"].default_value = alpha
    nt.links.new(bs.outputs["BSDF"], out.inputs["Surface"])
    return m


def emission(name, color, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = tuple(color) + (1,)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return m


def place(mesh_name, name, rot_deg, dz_px=0.0, mat=None, loc=None):
    me = bpy.data.objects[mesh_name].data
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.rotation_euler.z = math.radians(rot_deg)
    ob.location.z = g.u(dz_px)
    if loc:
        ob.location = loc
    if mat:
        ob.material_slots[0].link = 'OBJECT'
        ob.material_slots[0].material = mat
    return ob


def setup():
    scn = bpy.context.scene
    here = os.path.dirname(bpy.data.filepath)
    body = concrete("Body", (0.62, 0.56, 0.48))
    groove = emission("Groove", (1.0, 0.72, 0.42), 14.0)
    base = bpy.data.objects["SM_DrawPalette_Base_SC"]
    base.data.materials[0] = body
    base.data.materials[1] = groove
    bpy.data.objects["SM_DrawPalette_Slider_SC"].data.materials[0] = concrete("Slider", (0.95, 0.88, 0.78), alpha=0.35)
    sw = concrete("Swatch", COLORS[SEL_COLOR], rough=0.9, glow=0.3)
    bpy.data.objects["SM_DrawPalette_Swatch_SC"].data.materials[0] = sw
    for nm in ("SM_DrawPalette_Key_SC", "SM_DrawPalette_SideKey_SC", "SM_DrawPalette_Knob_SC"):
        bpy.data.objects[nm].hide_render = True
    for i, a in enumerate(g.KEY_ANGLES["Color"]):
        place("SM_DrawPalette_Key_SC", "Color_%d" % i, a, g.KEY_SEL_UP if i == SEL_COLOR else 0.0,
              concrete("Color_%d" % i, COLORS[i]))
    for i, a in enumerate(g.KEY_ANGLES["Brush"]):
        ico = os.path.join(here, "icon_%s.png" % g.BRUSHES[i])
        mat = concrete("Brush_%d" % i, (0.56, 0.51, 0.45), mask=ico if os.path.exists(ico) else None,
                       mask_uv="IconUV", mask_rot=math.radians(ICON_ROT), mask_scale=ICON_SCALE)
        place("SM_DrawPalette_Key_SC", "Brush_%d" % i, a, g.KEY_SEL_UP if i == SEL_BRUSH else 0.0, mat)
    for nm, rot in (("Undo", 0.0), ("Redo", 28.0)):
        mat = concrete(nm, (0.52, 0.47, 0.41), mask=os.path.join(here, "T_DrawPalette_%s.png" % nm), mask_uv="LabelUV")
        place("SM_DrawPalette_SideKey_SC", nm, rot, 0.0, mat)
    a = math.radians(g.KNOB_ANGLE)
    place("SM_DrawPalette_Knob_SC", "Knob", 0.0, 0.0, concrete("Knob", (0.93, 0.84, 0.72), glow=0.2),
          loc=(g.u(g.SLIDER_R * math.cos(a)), g.u(g.SLIDER_R * math.sin(a)), g.u(g.Z_FLOAT)))
    w = bpy.data.worlds.new("W")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.012, 0.010, 0.009, 1)
    scn.world = w
    k = 2.22
    for nm, loc, energy, size, col in (("Key", (-0.25, 0.30, 0.45), 7, 0.35, (1.0, 0.90, 0.78)),
                                       ("Fill", (0.35, -0.20, 0.25), 1.5, 0.5, (0.85, 0.88, 1.0)),
                                       ("Rim", (0.10, 0.40, 0.05), 2.5, 0.2, (1.0, 0.80, 0.60))):
        L = bpy.data.lights.new(nm, 'AREA')
        L.energy, L.size, L.color = energy * k * k, size * k, col
        o = bpy.data.objects.new(nm, L)
        scn.collection.objects.link(o)
        o.location = tuple(c * k for c in loc)
        d = Vector((0, 0, -0.02)) - o.location
        o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    scn.collection.objects.link(cam)
    scn.camera = cam
    scn.render.engine = 'CYCLES'
    scn.cycles.samples = 160
    scn.cycles.use_denoising = True
    scn.render.resolution_x, scn.render.resolution_y = 1400, 1050
    scn.view_settings.view_transform = 'AgX'
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = 'OPTIX'
        prefs.get_devices()
        for d in prefs.devices:
            d.use = d.type == 'OPTIX'
        scn.cycles.device = 'GPU'
    except Exception:
        pass
    return cam


VIEWS = {   # a 40 cm (x2,22 de la primera version)
    "tres_cuartos": ((0.11, -0.67, 0.60), (0.0, -0.01, -0.02), 50),
    "planta": ((0.0, -0.002, 1.02), (0.0, 0.0, 0.0), 50),
    "rasante": ((0.44, -0.44, 0.155), (0.0, 0.0, -0.01), 55),
    "detalle": ((-0.12, -0.20, 0.20), (-0.10, 0.02, -0.01), 55),
}


def main():
    cam = setup()
    os.makedirs(OUT, exist_ok=True)
    for nm, (loc, tgt, lens) in VIEWS.items():
        if ONLY and nm not in ONLY:
            continue
        cam.location = loc
        cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        cam.data.lens = lens
        cam.data.clip_start = 0.005
        bpy.context.scene.render.filepath = os.path.join(OUT, "pal_" + nm + ".png")
        bpy.ops.render.render(write_still=True)
        print("VISTA_OK", nm)


try:
    main()
except BaseException as e:
    print("RENDER_FALLO", type(e).__name__, e)
    traceback.print_exc()
