# Paleta de dibujo DE FRENTE, 1024x1024, fondo transparente. Reusa setup() de render_draw_palette.py (sin su main).
# Uso: blender --background <copia>/SM_DrawPalette_SC.blend --python render_paleta_frente.py -- <salida.png>
import os
import sys
import traceback

import bpy

SKILL = r"C:\Users\beltr\Desktop\Alma Digital Studio\Projects\VR Unreal\.claude\skills\blender-3d\scripts"
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import fit_cam  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = argv[0]

try:
    src = open(os.path.join(SKILL, "render_draw_palette.py"), encoding="utf-8").read()
    src = src[:src.rindex("\ntry:\n    main()")]
    ns = {"__file__": os.path.join(SKILL, "render_draw_palette.py"), "__name__": "rdp"}
    sys_argv = sys.argv
    sys.argv = [sys.argv[0]]          # que el modulo no lea nuestros argumentos como los suyos
    exec(compile(src, "render_draw_palette.py", "exec"), ns)
    sys.argv = sys_argv
    cam = ns["setup"]()
    scn = bpy.context.scene
    scn.render.resolution_x = scn.render.resolution_y = 1024
    scn.render.resolution_percentage = 100
    scn.render.film_transparent = True
    scn.render.image_settings.file_format = 'PNG'
    scn.render.image_settings.color_mode = 'RGBA'
    scn.cycles.samples = 256
    objs = [o for o in scn.objects if o.type == 'MESH' and not o.hide_render]
    print("OBJS", sorted(o.name for o in objs))
    dist = fit_cam.fit(cam, objs, (0.0, -0.002, 1.0), lens=85.0, fill=0.88)
    print("DIST", round(dist, 3), "CAM", [round(x, 4) for x in cam.location])
    scn.render.filepath = OUT
    bpy.ops.render.render(write_still=True)
    print("RENDER_OK", OUT)
except BaseException as e:
    print("RENDER_FALLO", type(e).__name__, e)
    traceback.print_exc()
