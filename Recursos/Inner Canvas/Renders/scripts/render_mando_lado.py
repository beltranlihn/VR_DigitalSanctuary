# Mando (SM_QuestCtrl_*_R_SC) DE LADO, 1024x1024, fondo transparente, con el sombreado de la obra (unlit).
# Reusa unlit_material() de render_quest_controller_unlit.py (sin su bucle de vistas).
# Uso: blender --background --python render_mando_lado.py -- <dir_fbx> <salida.png> [dx,dy,dz]
import os
import sys
import traceback

import bpy

SKILL = r"C:\Users\beltr\Desktop\Alma Digital Studio\Projects\VR Unreal\.claude\skills\blender-3d\scripts"
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import fit_cam  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
D, OUT = argv[0], argv[1]
DIR = tuple(float(x) for x in argv[2].split(",")) if len(argv) > 2 else (1.0, 0.0, 0.0)
ROLL = float(argv[3]) if len(argv) > 3 else 0.0

try:
    src = open(os.path.join(SKILL, "render_quest_controller_unlit.py"), encoding="utf-8").read()
    src = src[:src.index("bpy.ops.wm.read_factory_settings")]
    ns = {"__name__": "rqc"}
    sys_argv = sys.argv
    sys.argv = [sys.argv[0], "--", D, OUT]
    exec(compile(src, "render_quest_controller_unlit.py", "exec"), ns)
    sys.argv = sys_argv
    bpy.ops.wm.read_factory_settings(use_empty=True)
    objs = []
    for nm, mat in (("SM_QuestCtrl_Body_R_SC", ns["unlit_material"]("Body", True)),
                    ("SM_QuestCtrl_Trigger_R_SC", ns["unlit_material"]("TrigRest", False, 0.0))):
        bpy.ops.import_scene.fbx(filepath=os.path.join(D, nm + ".fbx"))
        ob = [o for o in bpy.context.selected_objects if o.type == 'MESH'][0]
        ob.data.materials.clear()
        ob.data.materials.append(mat)
        objs.append(ob)
        vs = [ob.matrix_world @ v.co for v in ob.data.vertices]
        print("BBOX", nm, "loc_cm", [round(x * 100, 3) for x in ob.location],
              "min_cm", [round(min(p[i] for p in vs) * 100, 2) for i in range(3)],
              "max_cm", [round(max(p[i] for p in vs) * 100, 2) for i in range(3)])
    # el gatillo se exporto con el origen EN LA BISAGRA (Unreal lo ubica en el pivote): aca hay que llevarlo al pivote
    import json
    hinge = json.load(open(os.path.join(D, "qc_trigger_hinge.json")))
    trig = objs[1]
    if trig.location.length < 1e-4:
        trig.location = [x / 1000.0 for x in hinge["pivot_mm"]]
        print("TRIG_AL_PIVOTE_cm", [round(x * 100, 3) for x in trig.location])
    scn = bpy.context.scene
    w = bpy.data.worlds.new("W")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.0, 0.0, 0.0, 1)
    scn.world = w
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    scn.collection.objects.link(cam)
    scn.camera = cam
    scn.render.engine = 'CYCLES'
    scn.cycles.samples = 96
    scn.cycles.use_denoising = False
    scn.view_settings.view_transform = 'Standard'
    scn.render.resolution_x = scn.render.resolution_y = 1024
    scn.render.resolution_percentage = 100
    scn.render.film_transparent = True
    scn.render.image_settings.file_format = 'PNG'
    scn.render.image_settings.color_mode = 'RGBA'
    bpy.context.view_layer.update()
    dist = fit_cam.fit(cam, objs, DIR, lens=85.0, fill=0.86, roll=ROLL)
    print("DIST", round(dist, 3), "CAM", [round(x, 4) for x in cam.location])
    scn.render.filepath = OUT
    bpy.ops.render.render(write_still=True)
    print("RENDER_OK", OUT)
except BaseException as e:
    print("RENDER_FALLO", type(e).__name__, e)
    traceback.print_exc()
