# render_charge_ring.py - presentacion de SM_ChargeRing_SC (Cycles, OptiX): materiales de preview, luces, ameba provisoria, 5 vistas.
# Uso: blender --background <SM_ChargeRing_SC.blend> --python render_charge_ring.py -- <outdir> [vistas]
#      ... -- <salida.blend>   -> modo PRESENTACION: guarda la escena lista para abrir (no renderiza)
import math
import os
import sys
import traceback

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else os.path.dirname(os.path.abspath(__file__))
ONLY = argv[1].split(",") if len(argv) > 1 else None
RES = 1000
SAMPLES = 160

# colores oficiales de las etapas (lineales, BP_ProtoSoul.RingColors), aclarados hacia el pastel de la referencia
STAGE = [(0.10, 0.35, 1.0), (1.0, 0.12, 0.12), (0.55, 0.15, 1.0), (1.0, 0.42, 0.06), (0.15, 1.0, 0.45)]
WHITEN = 0.30


def srgb(hx):
    hx = hx.lstrip("#")
    c = [int(hx[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return tuple((x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4) for x in c) + (1.0,)


def inp(node, *names):
    for n in names:
        if n in node.inputs:
            return node.inputs[n]
    raise KeyError(f"{node.name}: ninguna de {names}")


def mat_frame(m):
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    inp(bs, "Base Color").default_value = (0.030, 0.030, 0.033, 1)
    inp(bs, "Metallic").default_value = 1.0
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    inp(nz, "Scale").default_value = 900.0
    inp(nz, "Detail").default_value = 2.0
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    inp(mr, "To Min").default_value = 0.40
    inp(mr, "To Max").default_value = 0.58
    nt.links.new(nz.outputs["Fac"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], inp(bs, "Roughness"))
    bp = nt.nodes.new("ShaderNodeBump")
    inp(bp, "Strength").default_value = 0.06
    inp(bp, "Distance").default_value = 0.0003
    nt.links.new(nz.outputs["Fac"], inp(bp, "Height"))
    nt.links.new(bp.outputs["Normal"], inp(bs, "Normal"))
    nt.links.new(bs.outputs["BSDF"], out.inputs["Surface"])


def mat_light(m):
    """U = etapa + t. Carga global P (0..5): etapa j encendida hasta t < P - j."""
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    uvn = nt.nodes.new("ShaderNodeUVMap")
    uvn.uv_map = "UVMap"
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(uvn.outputs["UV"], sep.inputs["Vector"])
    fl = nt.nodes.new("ShaderNodeMath"); fl.operation = 'FLOOR'
    nt.links.new(sep.outputs["X"], fl.inputs[0])
    t = nt.nodes.new("ShaderNodeMath"); t.operation = 'SUBTRACT'
    nt.links.new(sep.outputs["X"], t.inputs[0]); nt.links.new(fl.outputs[0], t.inputs[1])
    # color por etapa: rampa constante sobre (j + 0.5) / 5
    cidx = nt.nodes.new("ShaderNodeMath"); cidx.operation = 'MULTIPLY_ADD'
    nt.links.new(fl.outputs[0], cidx.inputs[0]); cidx.inputs[1].default_value = 0.2; cidx.inputs[2].default_value = 0.1
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = 'CONSTANT'
    els = ramp.color_ramp.elements
    while len(els) < 5:
        els.new(0.5)
    for i, c in enumerate(STAGE):
        els[i].position = i * 0.2
        els[i].color = tuple(x + (1.0 - x) * WHITEN for x in c) + (1.0,)
    nt.links.new(cidx.outputs[0], ramp.inputs["Fac"])
    # carga: lit = smoothstep(t, P-j+e, P-j-e)
    val = nt.nodes.new("ShaderNodeValue"); val.name = "Charge"; val.label = "Charge"
    val.outputs[0].default_value = 5.0
    pj = nt.nodes.new("ShaderNodeMath"); pj.operation = 'SUBTRACT'
    nt.links.new(val.outputs[0], pj.inputs[0]); nt.links.new(fl.outputs[0], pj.inputs[1])
    d = nt.nodes.new("ShaderNodeMath"); d.operation = 'SUBTRACT'
    nt.links.new(pj.outputs[0], d.inputs[0]); nt.links.new(t.outputs[0], d.inputs[1])  # (P-j) - t
    lit = nt.nodes.new("ShaderNodeMapRange"); lit.interpolation_type = 'SMOOTHSTEP'
    inp(lit, "From Min").default_value = -0.012
    inp(lit, "From Max").default_value = 0.012
    nt.links.new(d.outputs[0], lit.inputs["Value"])
    strength = nt.nodes.new("ShaderNodeMapRange")
    inp(strength, "To Min").default_value = 0.0
    inp(strength, "To Max").default_value = 0.72
    nt.links.new(lit.outputs["Result"], strength.inputs["Value"])
    nt.links.new(ramp.outputs["Color"], inp(bs, "Base Color"))
    nt.links.new(ramp.outputs["Color"], inp(bs, "Emission Color"))
    nt.links.new(strength.outputs["Result"], inp(bs, "Emission Strength"))
    inp(bs, "Roughness").default_value = 0.6
    # base apagada: el color queda como vidrio mate oscuro cuando no hay carga
    dim = nt.nodes.new("ShaderNodeVectorMath"); dim.operation = 'SCALE'
    nt.links.new(ramp.outputs["Color"], dim.inputs[0])
    lv = nt.nodes.new("ShaderNodeMapRange")
    inp(lv, "To Min").default_value = 0.12
    inp(lv, "To Max").default_value = 0.18
    nt.links.new(lit.outputs["Result"], lv.inputs["Value"])
    nt.links.new(lv.outputs["Result"], inp(dim, "Scale"))
    nt.links.new(dim.outputs["Vector"], inp(bs, "Base Color"))
    nt.links.new(bs.outputs["BSDF"], out.inputs["Surface"])
    return val


def add_blob(col):
    import bmesh
    from mathutils import Matrix
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=5, radius=1.0)
    rot = Matrix.Rotation(math.radians(45), 3, 'X')
    for v in bm.verts:
        n = v.co.normalized()
        q = rot @ n
        f = q.x ** 4 + q.y ** 4 + q.z ** 4          # 1/3 en diagonales, 1 en ejes -> 6 lobulos
        v.co = n * 0.058 * (1.0 + 0.30 * (f - 0.55))
    me = bpy.data.meshes.new("Preview_Ameba")
    bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new("Preview_Ameba", me)
    ob.rotation_euler = (0.0, math.radians(20), math.radians(15))
    col.objects.link(ob)
    mb = me
    m = bpy.data.materials.new("Preview_Glass")
    m.use_nodes = True
    bs = m.node_tree.nodes["Principled BSDF"]
    inp(bs, "Base Color").default_value = (0.95, 0.97, 1.0, 1)
    inp(bs, "Transmission Weight", "Transmission").default_value = 1.0
    inp(bs, "Roughness").default_value = 0.04
    inp(bs, "IOR").default_value = 1.33
    try:
        inp(bs, "Thin Film Thickness").default_value = 480.0
        inp(bs, "Thin Film IOR").default_value = 1.4
    except KeyError:
        pass
    mb.materials.append(m)
    return ob


def area(col, name, loc, power, size, color=(1, 1, 1)):
    L = bpy.data.lights.new(name, 'AREA')
    L.energy = power
    L.size = size
    L.color = color
    o = bpy.data.objects.new(name, L)
    o.location = loc
    o.rotation_euler = (Vector((0, 0, 0)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    col.objects.link(o)
    return o


def setup():
    scn = bpy.context.scene
    col = bpy.data.collections.new("Preview")
    scn.collection.children.link(col)
    mat_frame(bpy.data.materials["M_ChargeRing_Frame"])
    charge = mat_light(bpy.data.materials["M_ChargeRing_Light"])
    add_blob(col)
    area(col, "Key", (1.0, -0.9, 1.1), 90, 0.9, (1.0, 0.97, 0.93))
    area(col, "Rim", (-0.9, 0.9, 0.7), 120, 0.6, (0.85, 0.9, 1.0))
    area(col, "Fill", (0.9, 1.0, -0.5), 25, 1.2)
    area(col, "Top", (0.1, 0.0, 1.3), 18, 1.5)
    w = bpy.data.worlds.new("Preview_World")
    w.use_nodes = True
    inp(w.node_tree.nodes["Background"], "Color").default_value = (0.004, 0.0045, 0.006, 1)
    scn.world = w
    cam = bpy.data.objects.new("Preview_Cam", bpy.data.cameras.new("Preview_Cam"))
    cam.data.lens = 70
    col.objects.link(cam)
    scn.camera = cam
    scn.render.engine = 'CYCLES'
    scn.cycles.samples = SAMPLES
    scn.cycles.use_denoising = True
    scn.render.resolution_x = scn.render.resolution_y = RES
    scn.render.image_settings.file_format = 'PNG'
    scn.view_settings.view_transform = 'Standard'
    scn.view_settings.look = 'None'
    dev = "CPU"
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        for t in ("OPTIX", "CUDA"):
            try:
                prefs.compute_device_type = t
                prefs.get_devices()
                gpus = [d for d in prefs.devices if d.type == t]
                if gpus:
                    for d in prefs.devices:
                        d.use = (d.type == t)
                    scn.cycles.device = 'GPU'
                    dev = t
                    break
            except Exception:
                pass
    except Exception:
        pass
    return cam, charge, dev


def shoot(cam, name, yaw, el, dist, charge_node, charge, lens=70):
    cam.data.lens = lens
    y, e = math.radians(yaw), math.radians(el)
    cam.location = (dist * math.cos(e) * math.cos(y), dist * math.cos(e) * math.sin(y), dist * math.sin(e))
    cam.rotation_euler = (Vector((0, 0, 0)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    charge_node.outputs[0].default_value = charge
    bpy.context.scene.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
    return name


VIEWS = {
    "ring_hero": (-34, 9, 1.35, 5.0, 70),
    "ring_front_carga": (0, 0, 1.30, 2.45, 70),
    "ring_back": (180 + 34, 9, 1.35, 5.0, 70),
    "ring_canto": (90, 4, 1.30, 5.0, 70),
    "ring_detalle": (-50, 22, 0.55, 5.0, 70),
}

def save_presentation(path, cam, charge_node):
    """Modo presentacion: escena lista para abrir en el GUI (camara 3/4, visor en render, propiedad
    'Carga' 0..5 en el anillo conectada al material por un driver sin Python)."""
    yaw, el, dist, ch, lens = VIEWS["ring_hero"]
    y, e = math.radians(yaw), math.radians(el)
    cam.location = (dist * math.cos(e) * math.cos(y), dist * math.cos(e) * math.sin(y), dist * math.sin(e))
    cam.rotation_euler = (Vector((0, 0, 0)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    ring = bpy.data.objects["SM_ChargeRing_SC"]
    ring["Carga"] = 5.0
    ui = ring.id_properties_ui("Carga")
    ui.update(min=0.0, max=5.0, soft_min=0.0, soft_max=5.0, step=1,
              description="Carga de las 5 etapas: 0 vacio, 1 = Entering llena, ... 5 = todo cargado")
    nt = bpy.data.materials["M_ChargeRing_Light"].node_tree
    fc = charge_node.outputs[0].driver_add("default_value")
    fc.driver.type = 'AVERAGE'
    var = fc.driver.variables.new()
    var.type = 'SINGLE_PROP'
    var.targets[0].id_type = 'OBJECT'
    var.targets[0].id = ring
    var.targets[0].data_path = '["Carga"]'
    scn = bpy.context.scene
    # EEVEE para girar en tiempo real: el Cycles de Beltran no tiene GPU configurada en preferencias
    # (compute_device_type NONE -> CPU) y no se tocan sus preferencias. F12 con Cycles sigue sirviendo.
    scn.render.engine = 'BLENDER_EEVEE'
    scn.eevee.use_raytracing = True
    scn.eevee.ray_tracing_method = 'SCREEN'
    bpy.data.materials["Preview_Glass"].use_raytrace_refraction = True
    for scr in bpy.data.screens:
        for area in scr.areas:
            if area.type == 'VIEW_3D':
                sp = area.spaces[0]
                sp.shading.type = 'RENDERED'
                sp.overlay.show_overlays = False
                sp.region_3d.view_perspective = 'CAMERA'
    for o in bpy.data.objects:
        o.select_set(False)
    ring.select_set(True)
    bpy.context.view_layer.objects.active = ring
    bpy.ops.wm.save_as_mainfile(filepath=path)
    return path


try:
    cam, charge_node, dev = setup()
    if OUT.lower().endswith(".blend"):
        print("PRESENTACION_OK", dev, save_presentation(OUT, cam, charge_node))
    else:
        done = []
        for k, (yaw, el, dist, ch, lens) in VIEWS.items():
            if ONLY and k not in ONLY:
                continue
            done.append(shoot(cam, k, yaw, el, dist, charge_node, ch, lens))
        print("RENDER_OK", dev, done)
except BaseException as ex:
    print("RENDER_FALLO", type(ex).__name__, ex)
    traceback.print_exc()
