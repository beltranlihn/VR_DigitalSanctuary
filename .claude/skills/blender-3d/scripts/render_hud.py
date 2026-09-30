# render_hud.py - vista previa del HUD 3D (gen_hud.py) como en la obra: sin luces, fondo negro, sombreado falso de la
# familia; con el anillo SM_ChargeRing_SC escalado a 45 mm en su nido (con un alma celeste adentro), la ameba rosada en su
# asiento, la lamina translucida y un EEG DE MUESTRA en la ventana (solo para el render: el real es el widget).
# Uso: blender --background <SM_HUD_SC.blend> --python render_hud.py -- <salida_dir>
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
import gen_hud as H             # noqa: E402

OUT = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "."
SH = LZ.SH


def glass_mat():
    m, nt, out = P._base("Glass")
    geo = P._n(nt, "ShaderNodeNewGeometry")
    fr = P._m(nt, 'SUBTRACT', 1.0, P._m(nt, 'MAXIMUM', P._vm(nt, 'DOT_PRODUCT', geo.outputs["Normal"], geo.outputs["Incoming"]), 0.0))
    em = P._n(nt, "ShaderNodeEmission")
    P._link(nt, P._vm(nt, 'SCALE', (0.80, 0.84, 0.90), scale=P._m(nt, 'ADD', 0.10, P._m(nt, 'MULTIPLY', fr, 0.25))), em.inputs["Color"])
    tr = P._n(nt, "ShaderNodeBsdfTransparent")
    mx = P._n(nt, "ShaderNodeMixShader")
    mx.inputs[0].default_value = 0.30
    P._link(nt, tr.outputs[0], mx.inputs[1])
    P._link(nt, em.outputs[0], mx.inputs[2])
    P._link(nt, mx.outputs[0], out.inputs["Surface"])
    return m


def rim_mat(name="Rim"):
    """Borde y contornos: el hormigon de la familia pero TRANSLUCIDO (Beltran v2-v3): opacidad RIM_ALPHA."""
    m = P.fake_mat(name, (0.66, 0.60, 0.52), self_glow=0.14, mottle=0.06, grain=0.05, sh=SH)
    nt = m.node_tree
    out = [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'][0]
    em = out.inputs["Surface"].links[0].from_node
    tr = P._n(nt, "ShaderNodeBsdfTransparent")
    mx = P._n(nt, "ShaderNodeMixShader")
    mx.inputs[0].default_value = RIM_ALPHA
    P._link(nt, tr.outputs[0], mx.inputs[1])
    P._link(nt, em.outputs[0], mx.inputs[2])
    P._link(nt, mx.outputs[0], out.inputs["Surface"])
    return m


RIM_ALPHA = 0.45


def eeg_plane():
    """Solo para el render: una linea de EEG en la ventana (el real es el widget con OnPaint)."""
    me = bpy.data.meshes.new("EEG")
    w, h = H.EEG_A * 2 / 1000, H.EEG_B * 2 / 1000
    me.from_pydata([(-w / 2, -h / 2, 0), (w / 2, -h / 2, 0), (w / 2, h / 2, 0), (-w / 2, h / 2, 0)], [], [(0, 1, 2, 3)])
    me.uv_layers.new(name="UVMap")
    for i, uv in enumerate(((0, 0), (1, 0), (1, 1), (0, 1))):
        me.uv_layers[0].data[i].uv = uv
    ob = bpy.data.objects.new("EEG", me)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = (0, 0, -0.0008)
    m, nt, out = P._base("EEGLine")
    uv = P._n(nt, "ShaderNodeUVMap", uv_map="UVMap")
    sep = P._n(nt, "ShaderNodeSeparateXYZ")
    P._link(nt, uv.outputs["UV"], sep.inputs[0])
    x, y = sep.outputs["X"], sep.outputs["Y"]
    wave = P._m(nt, 'ADD', P._m(nt, 'ADD', P._m(nt, 'MULTIPLY', P._m(nt, 'SINE', P._m(nt, 'MULTIPLY', x, 37.0)), 0.16),
                                P._m(nt, 'MULTIPLY', P._m(nt, 'SINE', P._m(nt, 'MULTIPLY', x, 91.0)), 0.07)),
                P._m(nt, 'MULTIPLY', P._m(nt, 'SINE', P._m(nt, 'MULTIPLY', x, 13.0)), 0.10))
    d = P._m(nt, 'DIVIDE', P._m(nt, 'SUBTRACT', y, P._m(nt, 'ADD', wave, 0.5)), 0.022)
    line = P._m(nt, 'EXPONENT', P._m(nt, 'MULTIPLY', P._m(nt, 'MULTIPLY', d, d), -1.0))
    em = P._n(nt, "ShaderNodeEmission")
    P._link(nt, P._vm(nt, 'SCALE', (0.70, 0.90, 1.0), scale=P._m(nt, 'ADD', line, 0.015)), em.inputs["Color"])
    P._link(nt, em.outputs[0], out.inputs["Surface"])
    me.materials.append(m)


def ring_and_soul():
    d = LZ.CS
    bpy.ops.import_scene.fbx(filepath=os.path.join(d, "SM_ChargeRing_SC.fbx"))
    ring = [o for o in bpy.context.selected_objects if o.type == 'MESH'][0]
    ring.name = "Ring"
    for s in ring.material_slots:
        part = s.name.split(".")[0].split("_")[-1]
        s.material = LZ.ring_light_mat() if part == "Light" else P.fake_mat(
            "RingFrame", (0.075, 0.075, 0.085), self_glow=0.12, mottle=0.04, grain=0.04,
            sh={"Ambient": 0.45, "Diffuse": 0.85, "Wrap": 0.4, "Fill": 0.55})
    bpy.context.view_layer.update()
    ext = max(max(abs((ring.matrix_world @ v.co)[k]) for v in ring.data.vertices) for k in (1, 2))
    s = 0.0225 / ext
    ring.matrix_world = Matrix.Translation((H.END_X / 1000, 0, 0.0)) @ Matrix.Rotation(math.radians(-90), 4, 'Z') @ \
        Matrix.Rotation(math.radians(-90), 4, 'Y') @ Matrix.Diagonal((s, s, s, 1.0))
    soul = bpy.data.objects.new("Alma", bpy.data.objects["SM_HUDPulse_SC"].data)
    bpy.context.scene.collection.objects.link(soul)
    soul.material_slots[0].link = 'OBJECT'
    soul.material_slots[0].material = P.fake_mat("Soul", (0.55, 0.80, 1.0), self_glow=0.45, mottle=0.0, grain=0.0, sh=SH)
    soul.matrix_world = Matrix.Translation((H.END_X / 1000, 0, 0.0005)) @ Matrix.Diagonal((0.5, 0.5, 0.5, 1.0))


def setup_scene():
    """Materiales + EEG de muestra + anillo y alma. Devuelve el dict de objetos y materiales."""
    fr = rim_mat("Frame")            # marco del EEG y collares: translucidos como el borde
    bpy.data.objects["SM_HUDBezel_SC"].data.materials[0] = fr
    cup = bpy.data.objects["Nest"].data
    cup.materials[0] = fr
    cup.materials[1] = P.fake_mat("Seat", (0.30, 0.28, 0.25), self_glow=0.05, mottle=0.06, grain=0.06, sh=SH)
    bpy.data.objects["SM_HUDRim_SC"].data.materials[0] = rim_mat()
    bpy.data.objects["SM_HUDGlass_SC"].data.materials[0] = glass_mat()
    bpy.data.objects["SM_HUDPulse_SC"].data.materials[0] = P.fake_mat("Pulse", (0.95, 0.55, 0.62), self_glow=0.35,
                                                                       mottle=0.0, grain=0.0, sh=SH)
    eeg_plane()
    ring_and_soul()
    return render_settings()


def render_settings():
    scn = bpy.context.scene
    w = bpy.data.worlds.new("Negro")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)
    scn.world = w
    scn.render.engine = 'CYCLES'
    scn.cycles.samples = 32
    scn.cycles.transparent_max_bounces = 16
    scn.view_settings.view_transform = 'Standard'
    scn.render.resolution_x, scn.render.resolution_y = 1400, 700
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = 'OPTIX'
        prefs.get_devices()
        for dv in prefs.devices:
            dv.use = dv.type == 'OPTIX'
        scn.cycles.device = 'GPU'
    except Exception:
        pass
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    scn.collection.objects.link(cam)
    scn.camera = cam
    cam.data.clip_start = 0.005
    return cam


def main():
    cam = setup_scene()
    scn = bpy.context.scene
    os.makedirs(OUT, exist_ok=True)
    # "ojo": a 55 cm sobre la normal (el HUD va inclinado hacia el ojo); los otros para leer el volumen
    V = {"ojo": ((0.0, -0.05, 1.0), (0, 0, 0), 0.55, 50), "tres_cuartos": ((0.35, -0.55, 0.75), (0, 0, 0), 0.45, 50),
         "detalle_nido": ((0.25, -0.45, 0.8), (0.085, 0, 0), 0.20, 50), "detalle_ameba": ((-0.25, -0.45, 0.8), (-0.085, 0, 0), 0.20, 50)}
    for nm, (d, tg, dist, lens) in V.items():
        tg = Vector(tg)
        cam.location = tg + Vector(d).normalized() * dist
        cam.rotation_euler = (tg - cam.location).to_track_quat('-Z', 'Y').to_euler()
        cam.data.lens = lens
        scn.render.filepath = os.path.join(OUT, "hud_" + nm + ".png")
        bpy.ops.render.render(write_still=True)
    print("HUD_RENDER_OK")


if __name__ == "__main__":
    try:
        main()
    except BaseException as e:
        print("HUD_RENDER_FALLO", type(e).__name__, e)
        traceback.print_exc()
