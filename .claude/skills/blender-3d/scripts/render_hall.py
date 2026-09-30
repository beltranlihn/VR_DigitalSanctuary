# render_hall.py - presentacion del hall-portal (Cycles/OptiX): hormigon fino, exterior negro, vidrio esmerilado,
# niebla interior + bruma exterior (los haces que salen de lo iluminado), 5 vistas.
# Uso: blender --background <SM_HallShell_SC.blend> --python render_hall.py -- <outdir> [vistas,separadas,por,coma]
import math
import os
import sys
import traceback

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else os.path.dirname(os.path.abspath(__file__))
ONLY = argv[1].split(",") if len(argv) > 1 else None
RES = (1280, 720)
SAMPLES = 128


def inp(node, *names):
    for n in names:
        if n in node.inputs:
            return node.inputs[n]
    raise KeyError(f"{node.name}: {names}")


def new_nt(m):
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    return nt, nt.nodes.new("ShaderNodeOutputMaterial")


def mat_interior(m):
    """Hormigon muy fino y liso, calido: grano de granito fino por ruido 3D (sin UV)."""
    nt, out = new_nt(m)
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    grain = nt.nodes.new("ShaderNodeTexVoronoi")          # granos finos
    inp(grain, "Scale").default_value = 260.0
    nt.links.new(tc.outputs["Object"], grain.inputs["Vector"])
    mott = nt.nodes.new("ShaderNodeTexNoise")              # manchado suave
    inp(mott, "Scale").default_value = 1.2
    inp(mott, "Detail").default_value = 6.0
    nt.links.new(tc.outputs["Object"], mott.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.46, 0.34, 0.21, 1)
    ramp.color_ramp.elements[1].color = (0.60, 0.46, 0.30, 1)
    nt.links.new(mott.outputs["Fac"], ramp.inputs["Fac"])
    gr = nt.nodes.new("ShaderNodeMapRange")
    inp(gr, "To Min").default_value = 0.93
    inp(gr, "To Max").default_value = 1.05
    nt.links.new(grain.outputs["Distance"], gr.inputs["Value"])
    mul = nt.nodes.new("ShaderNodeVectorMath"); mul.operation = 'SCALE'
    nt.links.new(ramp.outputs["Color"], mul.inputs[0])
    nt.links.new(gr.outputs["Result"], inp(mul, "Scale"))
    nt.links.new(mul.outputs["Vector"], inp(bs, "Base Color"))
    inp(bs, "Roughness").default_value = 0.82
    bump = nt.nodes.new("ShaderNodeBump")
    inp(bump, "Strength").default_value = 0.04
    inp(bump, "Distance").default_value = 0.002
    nt.links.new(grain.outputs["Distance"], inp(bump, "Height"))
    nt.links.new(bump.outputs["Normal"], inp(bs, "Normal"))
    nt.links.new(bs.outputs["BSDF"], out.inputs["Surface"])


def mat_black(m):
    nt, out = new_nt(m)
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    inp(bs, "Base Color").default_value = (0.0, 0.0, 0.0, 1)
    inp(bs, "Roughness").default_value = 1.0
    inp(bs, "Specular IOR Level").default_value = 0.0
    nt.links.new(bs.outputs["BSDF"], out.inputs["Surface"])


def mat_glass(m):
    nt, out = new_nt(m)
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    inp(bs, "Base Color").default_value = (0.96, 0.93, 0.89, 1)
    inp(bs, "Transmission Weight").default_value = 1.0
    inp(bs, "Roughness").default_value = 0.5
    inp(bs, "IOR").default_value = 1.45
    nt.links.new(bs.outputs["BSDF"], out.inputs["Surface"])


def volume_obj(name, mesh_op, density, color, aniso, col):
    mesh_op()
    ob = bpy.context.active_object
    ob.name = name
    m = bpy.data.materials.new(name)
    nt, out = new_nt(m)
    pv = nt.nodes.new("ShaderNodeVolumePrincipled")
    inp(pv, "Density").default_value = density
    inp(pv, "Color").default_value = color + (1,)
    inp(pv, "Anisotropy").default_value = aniso
    nt.links.new(pv.outputs["Volume"], out.inputs["Volume"])
    ob.data.materials.append(m)
    for c in ob.users_collection:
        c.objects.unlink(ob)
    col.objects.link(ob)
    return ob


def setup():
    scn = bpy.context.scene
    col = bpy.data.collections.new("Preview")
    scn.collection.children.link(col)
    mat_interior(bpy.data.materials["M_Hall_Interior"])
    mat_black(bpy.data.materials["M_Hall_Exterior"])
    mat_glass(bpy.data.materials["M_Hall_Glass"])
    # luz interior "sin fuente": esfera calida invisible a camara
    L = bpy.data.lights.new("Glow", 'POINT')
    L.energy = 350
    L.shadow_soft_size = 2.0
    L.color = (1.0, 0.70, 0.42)
    g = bpy.data.objects.new("Glow", L)
    g.location = (0, 0, 3.4)
    g.visible_camera = False
    col.objects.link(g)
    # cielo del oculo: disco emisivo con nubes
    bpy.ops.mesh.primitive_circle_add(vertices=64, radius=1.6, fill_type='NGON', location=(0, 0, 6.95))
    sky = bpy.context.active_object
    sky.name = "Sky"
    for c in sky.users_collection:
        c.objects.unlink(sky)
    col.objects.link(sky)
    m = bpy.data.materials.new("Sky")
    nt, out = new_nt(m)
    em = nt.nodes.new("ShaderNodeEmission")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    inp(nz, "Scale").default_value = 2.0
    inp(nz, "Detail").default_value = 4.0
    mr = nt.nodes.new("ShaderNodeMapRange")
    inp(mr, "To Min").default_value = 22.0
    inp(mr, "To Max").default_value = 55.0
    nt.links.new(nz.outputs["Fac"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], inp(em, "Strength"))
    inp(em, "Color").default_value = (1.0, 0.80, 0.58, 1)
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    sky.data.materials.append(m)
    # niebla interior y bruma exterior (haces)
    volume_obj("FogInterior", lambda: bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=6.95, depth=5.9, location=(0, 0, 3.26)),
               0.005, (1.0, 0.84, 0.66), 0.5, col)
    volume_obj("HazeExterior", lambda: bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 10), scale=(70, 70, 36)),
               0.008, (1.0, 0.85, 0.70), 0.7, col)
    w = bpy.data.worlds.new("Void")
    w.use_nodes = True
    inp(w.node_tree.nodes["Background"], "Color").default_value = (0, 0, 0, 1)
    scn.world = w
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    col.objects.link(cam)
    scn.camera = cam
    scn.render.engine = 'CYCLES'
    scn.cycles.samples = SAMPLES
    scn.cycles.use_denoising = True
    scn.cycles.volume_bounces = 0
    scn.cycles.volume_step_rate = 2.0
    scn.render.resolution_x, scn.render.resolution_y = RES
    scn.view_settings.view_transform = 'AgX'
    scn.view_settings.exposure = -0.3
    scn.view_settings.look = 'AgX - Medium High Contrast' if 'AgX - Medium High Contrast' in [
        e.identifier for e in scn.view_settings.bl_rna.properties['look'].enum_items] else 'None'
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = 'OPTIX'
        prefs.get_devices()
        for d in prefs.devices:
            d.use = d.type == 'OPTIX'
        scn.cycles.device = 'GPU'
    except Exception:
        pass
    return cam, sky


def leaves_open(on):
    for ob in bpy.data.objects:
        if ob.name.startswith("SM_HallDoorLeaf_"):
            ob.rotation_euler.z = math.radians(ob["open_deg"]) if on else 0.0


def shoot(cam, name, loc, target, lens, open_doors=False, sky_visible=True):
    cam.data.lens = lens
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    leaves_open(open_doors)
    bpy.context.scene.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
    return name


VIEWS = {
    "ext_cerrada": ((19.0, 0.0, 2.6), (7.3, 0.0, 2.45), 35, False),
    "ext_abierta": ((19.0, 0.0, 2.6), (7.3, 0.0, 2.45), 35, True),
    "ext_aereo": ((20.0, -16.0, 13.0), (0.0, 0.0, 3.0), 35, True),
    "int_puerta": ((-5.2, 1.2, 1.65), (7.0, 0.0, 2.9), 20, False),
    "int_oculo": ((0.0, -3.2, 1.6), (0.0, -0.3, 6.5), 16, False),
}

if __name__ == "__main__" and not os.environ.get("HALL_NO_RENDER"):
    try:
        cam, sky = setup()
        done = []
        for k, (loc, tgt, lens, op) in VIEWS.items():
            if ONLY and k not in ONLY:
                continue
            done.append(shoot(cam, k, loc, tgt, lens, op))
        print("RENDER_OK", done)
    except BaseException as ex:
        print("RENDER_FALLO", type(ex).__name__, ex)
        traceback.print_exc()
