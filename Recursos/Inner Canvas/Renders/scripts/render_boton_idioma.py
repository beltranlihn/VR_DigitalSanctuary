# Botones de idioma de Inner Canvas (BP_ShareButton_SC con T_English_Text / T_Espanol_Text), de frente, en reposo.
# Materiales = los del SAVE (render_save_melody_unlit.py: shaded/text_top/light/slider_mat), sin luces, fondo transparente.
# Uso: blender --background --python render_boton_idioma.py -- <dir_fbx_share> <png_texto> <salida.png> [ancho alto]
import os
import sys
import traceback

import bpy

SKILL = r"C:\Users\beltr\Desktop\Alma Digital Studio\Projects\VR Unreal\.claude\skills\blender-3d\scripts"
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import fit_cam  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
D, TXT, OUT = argv[0], argv[1], argv[2]
RW = int(argv[3]) if len(argv) > 3 else 1024
RH = int(argv[4]) if len(argv) > 4 else 1024

try:
    src = open(os.path.join(SKILL, "render_save_melody_unlit.py"), encoding="utf-8").read()
    src = src[:src.index("bpy.ops.wm.read_factory_settings")]
    ns = {"__name__": "rsm"}
    sa = sys.argv
    sys.argv = [sys.argv[0], "--", D, OUT, "0.0"]
    exec(compile(src, "render_save_melody_unlit.py", "exec"), ns)
    sys.argv = sa
    bpy.ops.wm.read_factory_settings(use_empty=True)
    obs = []
    for nm in ("SM_ShareButton_Base_SC", "SM_ShareButton_Plate_SC", "SM_ShareButton_Slider_SC"):
        bpy.ops.import_scene.fbx(filepath=os.path.join(D, nm + ".fbx"))
        ob = [o for o in bpy.context.selected_objects if o.type == 'MESH'][0]
        obs.append(ob)
        print("FBX", nm, "slots", [s.name for s in ob.material_slots], "uv", [u.name for u in ob.data.uv_layers])
    mats = {k: ns["shaded"](k, c) for k, c in ns["COL"].items()}
    mats["Ring"] = ns["light"]("Ring", 0.7)
    mats["PlateTop"] = ns["text_top"]("PlateTop", TXT)
    mats["Slider"] = ns["slider_mat"]()
    for ob in obs:
        for s in ob.material_slots:
            key = s.name.split(".")[0].replace("M_ShareButton_", "").replace("MI_ShareButton_", "")
            key = "PlateTop" if key.startswith("PlateTop") else key
            s.material = mats[key]
    scn = bpy.context.scene
    w = bpy.data.worlds.new("W")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)
    scn.world = w
    scn.render.engine = 'CYCLES'
    scn.cycles.samples = 96
    scn.cycles.transparent_max_bounces = 16
    scn.view_settings.view_transform = 'Standard'
    scn.render.resolution_x, scn.render.resolution_y = RW, RH
    scn.render.resolution_percentage = 100
    scn.render.film_transparent = True
    scn.render.image_settings.file_format = 'PNG'
    scn.render.image_settings.color_mode = 'RGBA'
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    scn.collection.objects.link(cam)
    scn.camera = cam
    bpy.context.view_layer.update()
    # FBX parado: cara hacia +X, arriba +Z. Un poco desde arriba, como lo ve el usuario (los botones van bajo los ojos)
    dist = fit_cam.fit(cam, obs[:2], (1.0, 0.0, 0.12), lens=85.0, fill=0.90)
    print("DIST", round(dist, 3))
    scn.render.filepath = OUT
    bpy.ops.render.render(write_still=True)
    print("RENDER_OK", OUT)
except BaseException as e:
    print("RENDER_FALLO", type(e).__name__, e)
    traceback.print_exc()
