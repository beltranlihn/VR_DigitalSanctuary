# render_quest_controller.py - vista previa (Cycles) de los mandos: cuerpo NEGRO + tapa GRIS-BLANCA (mascara UV1
# "CapMask"), gatillo gris-blanco; vistas + una con el gatillo apretado (gira en X alrededor de su bisagra).
# Uso: blender --background QuestCtrl_R.blend --python render_quest_controller.py -- <outdir>
import math, os, sys
import bpy
from mathutils import Vector
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else os.path.dirname(bpy.data.filepath)
PRESS_DEG = 14.0


def mat(name, body_col, cap_col=None, rough=0.75):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bs = nt.nodes["Principled BSDF"]
    bs.inputs["Roughness"].default_value = rough
    bs.inputs["Specular IOR Level"].default_value = 0.25
    if cap_col is None:
        bs.inputs["Base Color"].default_value = body_col + (1,)
        return m
    uv = nt.nodes.new("ShaderNodeUVMap"); uv.uv_map = "CapMask"
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(uv.outputs["UV"], sep.inputs[0])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = -0.02   # CapMask.x = distancia con signo al plano de la tapa (cm)
    mr.inputs["From Max"].default_value = 0.02
    nt.links.new(sep.outputs["X"], mr.inputs["Value"])
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = 'RGBA'
    mix.inputs["A"].default_value = body_col + (1,)
    mix.inputs["B"].default_value = cap_col + (1,)
    nt.links.new(mr.outputs["Result"], mix.inputs["Factor"])
    nt.links.new(mix.outputs["Result"], bs.inputs["Base Color"])
    return m


scn = bpy.context.scene
body = [o for o in bpy.data.objects if "Body_R" in o.name][0]
trig = [o for o in bpy.data.objects if "Trigger_R" in o.name][0]
for o in bpy.data.objects:
    if o.type == 'MESH' and o not in (body, trig):
        o.hide_render = True
body.data.materials[0] = mat("Body", (0.018, 0.018, 0.02), (0.78, 0.77, 0.74))
trig.data.materials[0] = mat("Trig", (0.78, 0.77, 0.74))
w = bpy.data.worlds.new("W"); w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.35, 0.35, 0.37, 1)
scn.world = w
for nm, loc, e in (("Key", (-0.25, -0.2, 0.35), 40), ("Rim", (0.3, 0.25, 0.1), 25)):
    L = bpy.data.lights.new(nm, 'AREA'); L.energy, L.size = e, 0.3
    ob = bpy.data.objects.new(nm, L); scn.collection.objects.link(ob); ob.location = loc
    ob.rotation_euler = (Vector((0, 0, -0.02)) - ob.location).to_track_quat('-Z', 'Y').to_euler()
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")); scn.collection.objects.link(cam); scn.camera = cam
scn.render.engine = 'CYCLES'; scn.cycles.samples = 96; scn.cycles.use_denoising = True
scn.render.resolution_x = scn.render.resolution_y = 900
scn.view_settings.view_transform = 'AgX'
try:
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = 'OPTIX'; prefs.get_devices()
    for d in prefs.devices: d.use = d.type == 'OPTIX'
    scn.cycles.device = 'GPU'
except Exception:
    pass
c = Vector((0.005, 0.015, -0.03))
V = {"lado": (1, 0.05, 0.15), "lado_int": (-1, 0.05, 0.15), "frente": (0.2, -1, 0.3), "arriba": (0.05, 0.1, 1), "tres_cuartos": (0.7, -0.6, 0.5)}
for nm, d in list(V.items()) + [("apretado", (1, 0.05, 0.15))]:
    trig.rotation_euler.x = math.radians(PRESS_DEG) if nm == "apretado" else 0.0
    dv = Vector(d).normalized()
    cam.location = c + dv * 0.34
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = 70
    scn.render.filepath = os.path.join(OUT, "qc_" + nm + ".png")
    bpy.ops.render.render(write_still=True)
    print("VISTA_OK", nm)
