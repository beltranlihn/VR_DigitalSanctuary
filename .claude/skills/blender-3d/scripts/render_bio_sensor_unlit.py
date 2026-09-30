# render_bio_sensor_unlit.py - vista previa del sensor de respiracion/latido COMO EN LA OBRA: sin luces, fondo negro,
# sombreado falso del material de la paleta (hemisferio + luz envolvente + relleno de camara + brillo propio), anillo
# luminoso en la cara de contacto y las ONDAS que salen hacia la panza (bandas suaves que viajan y se apagan).
# Lee los FBX exportados (los valida). Uso: blender --background --python render_bio_sensor_unlit.py -- <dir> <salida> [fase]
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
D, OUT = argv[0], argv[1]
PHASE = float(argv[2]) if len(argv) > 2 else 0.35
ANIM = int(argv[3]) if len(argv) > 3 else 0      # > 0: cuadros de un ciclo de los aros (vistas lado y usuario)
L = Vector((-0.35, -0.30, 0.88)).normalized()
SH = {"Ambient": 0.30, "Diffuse": 0.55, "Wrap": 0.4, "Fill": 0.25, "SelfGlow": 0.10}
COL = {"Body": (0.62, 0.56, 0.48), "Face": (0.52, 0.47, 0.41), "Button": (0.70, 0.64, 0.55), "Grip": (0.05, 0.05, 0.055)}   # la media esfera: OTRO material (grafito, como el mando)
RING = (1.0, 0.72, 0.45)
WAVES = {"count": 5.0, "width": 0.055, "gain": 1.0, "fade_in": 0.35, "fade_out": 0.45, "squeeze": 2.0}


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
    out = N(nt, "ShaderNodeOutputMaterial")
    return m, nt, out


def shaded(name, albedo, grain=0.06):
    """Hormigon unlit con sombreado falso (el de la paleta) + un poco de grano."""
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
    g = M(nt, 'MULTIPLY_ADD', tex.outputs["Fac"], 2 * grain, 1 - grain)
    k = M(nt, 'MULTIPLY', shade, g)
    comb = N(nt, "ShaderNodeCombineXYZ")
    for i in range(3):
        nt.links.new(M(nt, 'MULTIPLY', k, albedo[i]), comb.inputs[i])
    nt.links.new(comb.outputs[0], em.inputs["Color"])
    return m


def light_mat(name, gain=1.0):
    """Luz pareja (aro de atras, circulo de la punta)."""
    m, nt, out = base(name)
    em = N(nt, "ShaderNodeEmission")
    em.inputs["Color"].default_value = (RING[0] * gain, RING[1] * gain, RING[2] * gain, 1.0)
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    return m


def ring_mat():
    """Aro luminoso: brilla mas donde mira a la panza (-Z del sensor)."""
    m, nt, out = base("Ring")
    em = N(nt, "ShaderNodeEmission")
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    geo = N(nt, "ShaderNodeNewGeometry")
    sep = N(nt, "ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Normal"], sep.inputs[0])
    f = M(nt, 'MULTIPLY_ADD', M(nt, 'MAXIMUM', M(nt, 'MULTIPLY', sep.outputs["Z"], -1.0), 0.0), 0.35, 0.75)
    comb = N(nt, "ShaderNodeCombineXYZ")
    for i in range(3):
        nt.links.new(M(nt, 'MULTIPLY', f, RING[i]), comb.inputs[i])
    nt.links.new(comb.outputs[0], em.inputs["Color"])
    return m


def waves_mat():
    """Ondas: bandas gaussianas en V que viajan hacia afuera (fase), se apagan lejos; suma sobre lo de atras."""
    m, nt, out = base("Waves")
    add = N(nt, "ShaderNodeAddShader")
    tr = N(nt, "ShaderNodeBsdfTransparent")
    em = N(nt, "ShaderNodeEmission")
    nt.links.new(tr.outputs[0], add.inputs[0])
    nt.links.new(em.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], out.inputs["Surface"])
    uv = N(nt, "ShaderNodeUVMap", uv_map="UVMap")
    sep = N(nt, "ShaderNodeSeparateXYZ")
    nt.links.new(uv.outputs["UV"], sep.inputs[0])
    v = sep.outputs["Y"]
    p = WAVES["squeeze"]
    vs = M(nt, 'POWER', v, p)                   # u = v^2: los aros FRENAN y se juntan al alejarse (como el boceto)
    phase = N(nt, "ShaderNodeValue", name="Phase")
    phase.outputs[0].default_value = PHASE
    ph = M(nt, 'FRACT', M(nt, 'SUBTRACT', M(nt, 'MULTIPLY', vs, WAVES["count"]), phase.outputs[0]))
    dudv = M(nt, 'MAXIMUM', M(nt, 'MULTIPLY', M(nt, 'POWER', M(nt, 'MAXIMUM', v, 0.001), p - 1.0), p), 0.1)
    d = M(nt, 'DIVIDE', M(nt, 'SUBTRACT', ph, 0.5), M(nt, 'MULTIPLY', dudv, WAVES["width"]))   # grosor parejo en V
    band = M(nt, 'EXPONENT', M(nt, 'MULTIPLY', M(nt, 'MULTIPLY', d, d), -1.0))
    fin = N(nt, "ShaderNodeMapRange", interpolation_type='SMOOTHSTEP')      # nace invisible y sube a su color
    fin.inputs["From Min"].default_value, fin.inputs["From Max"].default_value = 0.0, WAVES["fade_in"]
    nt.links.new(v, fin.inputs["Value"])
    fout = N(nt, "ShaderNodeMapRange", interpolation_type='SMOOTHSTEP')     # y se desvanece antes del final
    fout.inputs["From Min"].default_value, fout.inputs["From Max"].default_value = WAVES["fade_out"], 1.0
    fout.inputs["To Min"].default_value, fout.inputs["To Max"].default_value = 1.0, 0.0
    nt.links.new(v, fout.inputs["Value"])
    fade = M(nt, 'MULTIPLY', fin.outputs["Result"], fout.outputs["Result"])
    a = M(nt, 'MULTIPLY', M(nt, 'MULTIPLY', band, fade), WAVES["gain"])
    comb = N(nt, "ShaderNodeCombineXYZ")
    for i in range(3):
        nt.links.new(M(nt, 'MULTIPLY', a, RING[i]), comb.inputs[i])
    nt.links.new(comb.outputs[0], em.inputs["Color"])
    return m


bpy.ops.wm.read_factory_settings(use_empty=True)
obs = {}
for nm in ("SM_BioSensor_SC", "SM_BioSensorWaves_SC"):
    bpy.ops.import_scene.fbx(filepath=os.path.join(D, nm + ".fbx"))
    ob = [o for o in bpy.context.selected_objects if o.type == 'MESH'][0]
    obs[nm] = ob
    print("FBX", nm, "tris", sum(len(p.vertices) - 2 for p in ob.data.polygons), "slots", [s.name for s in ob.material_slots],
          "custom_normals", ob.data.has_custom_normals)
body, waves = obs["SM_BioSensor_SC"], obs["SM_BioSensorWaves_SC"]
mats = {k: shaded(k, c) for k, c in COL.items()}
mats["Ring"] = ring_mat()
mats["BackRing"] = light_mat("BackRing", 0.9)
mats["TipLight"] = light_mat("TipLight", 1.0)
for i, s in enumerate(body.material_slots):
    key = s.name.replace("M_BioSensor_", "").split(".")[0]
    body.material_slots[i].material = mats.get(key, mats["Body"])
waves.material_slots[0].material = waves_mat()
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
V = {"dorso": ((0.55, -0.75, 0.75), Vector((0, 0, 0.010)), 0.46), "cara": ((0.45, -0.65, -0.8), Vector((0, 0, -0.005)), 0.46),
     "corte": ((0.0, -1.0, 0.0), Vector((0, 0, 0.012)), 0.60), "lado_ondas": ((1.0, -0.2, -0.35), Vector((0, 0, -0.03)), 0.62),
     "mirando_la_panza": ((0.25, -0.55, 0.9), Vector((0, 0, -0.02)), 0.56)}
wmat = waves.material_slots[0].material
if ANIM:
    scn.render.resolution_x = scn.render.resolution_y = 520
    scn.cycles.samples = 24
    for nm in ("corte", "mirando_la_panza"):
        d, c, dist = V[nm]
        dv = Vector(d).normalized()
        cam.location = c + dv * dist
        cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        cam.data.lens = 60
        flip = nm == "corte"
        for o in (body, waves):
            o.rotation_euler = (math.pi if flip else 0.0, 0.0, 0.0)
        waves.hide_render = False
        for f in range(ANIM):
            wmat.node_tree.nodes["Phase"].outputs[0].default_value = f / ANIM
            scn.render.filepath = os.path.join(OUT, "anim_%s_%03d.png" % (nm, f))
            bpy.ops.render.render(write_still=True)
    print("BIO_ANIM_OK")
    raise SystemExit
for nm, (d, c, dist) in V.items():
    dv = Vector(d).normalized()
    cam.location = c + dv * dist
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = 60
    waves.hide_render = nm in ("dorso", "cara")
    flip = nm == "corte"          # el corte con la cara de la panza ARRIBA, como el boceto
    for o in (body, waves):
        o.rotation_euler = (math.pi if flip else 0.0, 0.0, 0.0)
    scn.render.filepath = os.path.join(OUT, "bio_" + nm + ".png")
    bpy.ops.render.render(write_still=True)
print("BIO_RENDER_OK")
