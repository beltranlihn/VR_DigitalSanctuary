# render_ring_family.py - comparacion del ANILLO DE CARGA (SM_ChargeRing_SC): el cuerpo de METAL oscuro de hoy contra
# el HORMIGON de la familia de botones (timbre / SAVE / sensor: M_SCObject_SC, base 0,62/0,56/0,48, sombreado falso
# con wrap + relleno de vista, manchado y grano). Pedido de Beltran (2026-09-30): "el material del anillo esta muy
# oscuro, debe ser mas de la onda de los otros botones". Las cavidades de luz igual en los dos (carga 2,5: Entering y
# Recognizing llenas, Loving a la mitad), con el alma provisoria adentro.
# Uso: blender --background --python render_ring_family.py -- <salida.png>
import math
import os
import sys
import traceback

import bpy
from mathutils import Matrix, Vector

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import anim_palette_base as P   # noqa: E402
import anim_luz_objects as LZ   # noqa: E402

OUT = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "ring_family.png"
FAMILY = (0.62, 0.56, 0.48)        # el cuerpo del timbre / SAVE / sensor (MI_*_Body)


def ring(name, frame_mat, x):
    bpy.ops.import_scene.fbx(filepath=os.path.join(LZ.CS, "SM_ChargeRing_SC.fbx"))
    ob = [o for o in bpy.context.selected_objects if o.type == 'MESH'][0]
    ob.name = name
    ob.data = ob.data.copy()
    for s in ob.material_slots:
        part = s.name.split(".")[0].split("_")[-1]
        s.material = LZ.ring_light_mat() if part == "Light" else frame_mat
    # el eje del anillo es su X: de frente a la camara (que mira hacia +Y desde -Y)
    ob.matrix_world = Matrix.Translation((x, 0, 0)) @ Matrix.Rotation(math.radians(-90), 4, 'Z')
    soul = bpy.data.objects.new(name + "_alma", bpy.data.meshes.new(name + "_alma"))
    bpy.context.scene.collection.objects.link(soul)
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=3, radius=0.075)
    bm.to_mesh(soul.data)
    bm.free()
    for p in soul.data.polygons:
        p.use_smooth = True
    soul.data.materials.append(P.fake_mat(name + "_Soul", (0.55, 0.80, 1.0), self_glow=0.45, mottle=0.0, grain=0.0, sh=LZ.SH))
    soul.matrix_world = Matrix.Translation((x, 0, 0)) @ Matrix.Diagonal((1.0, 0.55, 1.0, 1.0))
    return ob


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    metal = P.fake_mat("MetalHoy", (0.075, 0.075, 0.085), self_glow=0.12, mottle=0.04, grain=0.04,
                       sh={"Ambient": 0.45, "Diffuse": 0.85, "Wrap": 0.4, "Fill": 0.55})
    concrete = P.fake_mat("Hormigon", FAMILY, self_glow=0.10, mottle=0.08, grain=0.06, sh=LZ.SH)
    ring("AnilloHoy", metal, -0.30)
    ring("AnilloFamilia", concrete, 0.30)
    w = bpy.data.worlds.new("Fondo")                  # gris oscuro con degrade: el HUD y el Hall
    w.use_nodes = True
    nt = w.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.035, 0.034, 0.033, 1)
    ramp.color_ramp.elements[1].color = (0.20, 0.19, 0.18, 1)
    mp = nt.nodes.new("ShaderNodeMapRange")
    nt.links.new(sep.outputs["Z"], mp.inputs["Value"])
    mp.inputs["From Min"].default_value, mp.inputs["From Max"].default_value = -0.6, 0.8
    nt.links.new(mp.outputs["Result"], ramp.inputs[0])
    nt.links.new(ramp.outputs[0], nt.nodes["Background"].inputs["Color"])
    bpy.context.scene.world = w
    scn = bpy.context.scene
    scn.render.engine = 'CYCLES'
    scn.cycles.samples = 48
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
    scn.render.resolution_x, scn.render.resolution_y = 1500, 720
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    scn.collection.objects.link(cam)
    scn.camera = cam
    loc, tg = Vector((0.25, -1.55, 0.35)), Vector((0.0, 0.0, 0.0))
    cam.location = loc
    cam.rotation_euler = (tg - loc).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = 50
    scn.render.filepath = OUT
    bpy.ops.render.render(write_still=True)
    print("RING_FAMILY_OK", OUT)


try:
    main()
except BaseException as e:
    print("RING_FAMILY_FALLO", type(e).__name__, e)
    traceback.print_exc()
