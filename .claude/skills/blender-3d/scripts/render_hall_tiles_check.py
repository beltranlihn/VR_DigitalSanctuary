# render_hall_tiles_check.py - control visual del canto de las baldosas del Hall (gen_bake_hall_tiles.py): la baldosa
# en REPOSO (asoma TILE_UP) y SUBIDA (Lift, como el WPO del material en Unreal), de cerca y rasante sobre el canto
# exterior de Entering y desde el ojo sentado en la entrada (solo Entering subida). Workbench: lee la FORMA (el canto,
# la cavidad, que no asome el faldon), no la luz. Pisos y muros en gris; cada baldosa con el color de su etapa.
# Uso: blender --background <SM_HallTiles_SC.blend> --python render_hall_tiles_check.py -- <dir_salida> [lift_m=0.03]
import math
import os
import sys
import traceback

import bmesh
import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else "."
LIFT = float(argv[1]) if len(argv) > 1 else 0.03
COLORS = ["#5d7fe0", "#e0566b", "#9a6ee6", "#e8a04e", "#4fc28f"]   # STAGES del prototipo web


def hexcol(h):
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (1, 3, 5)) + (1.0,)


def lift_slot(me0, slots, dz):
    """Copia de la malla con los vertices de los slots dados subidos dz (lo que hace el WPO Lift por baldosa)."""
    me = me0.copy()
    bm = bmesh.new()
    bm.from_mesh(me)
    vs = {v for f in bm.faces if f.material_index in slots for v in f.verts}
    for v in vs:
        v.co.z += dz
    bm.to_mesh(me)
    bm.free()
    return me


def main():
    scn = bpy.context.scene
    scn.render.engine = 'BLENDER_WORKBENCH'
    sh = scn.display.shading
    sh.light = 'STUDIO'
    sh.color_type = 'MATERIAL'
    sh.show_cavity = True
    sh.cavity_type = 'BOTH'
    sh.show_specular_highlight = True
    scn.render.resolution_x, scn.render.resolution_y = 1100, 620
    scn.display.render_aa = '16'
    for ob in scn.objects:
        if ob.type != 'MESH':
            ob.hide_render = True
    for ob in scn.objects:
        if ob.type == 'MESH' and ob.name != "SM_HallTiles_SC":
            ob.hide_render = not ob.name.startswith("SM_HallShell")
            for s in ob.material_slots:
                if s.material:
                    s.material.diffuse_color = (0.55, 0.53, 0.50, 1.0)
    tiles = bpy.data.objects["SM_HallTiles_SC"]
    for i, s in enumerate(tiles.material_slots):
        s.material.diffuse_color = hexcol(COLORS[i])
    me_rest = tiles.data
    me_all = lift_slot(me_rest, set(range(5)), LIFT)
    me_one = lift_slot(me_rest, {0}, LIFT)
    cam = bpy.data.objects.new("CamChk", bpy.data.cameras.new("CamChk"))
    scn.collection.objects.link(cam)
    scn.camera = cam
    cam.data.clip_start = 0.01
    views = [
        # canto exterior de Entering (Blender: angulo -180 -> x negativa), rasante y de cerca
        ("canto_reposo", me_rest, (-3.05, -0.42, 0.40), (-2.45, 0.0, 0.30), 50),
        ("canto_subida", me_all, (-3.05, -0.42, 0.40), (-2.45, 0.0, 0.30), 50),
        # la junta entre Entering y Recognizing (meridiano UE 144 -> Blender -144), mirando a lo largo de la junta
        ("junta_subida", me_all, (-2.95, -2.05, 0.55), (-1.25, -0.91, 0.30), 40),
        # ojo sentado en la entrada (PlayerStart x -3,5 m, ojo ~1,15 m sobre el piso)
        ("ojo_reposo", me_rest, (-3.5, 0.0, 1.45), (-1.2, 0.0, 0.30), 28),
        ("ojo_entering_sube", me_one, (-3.5, 0.0, 1.45), (-1.2, 0.0, 0.30), 28),
    ]
    os.makedirs(OUT, exist_ok=True)
    for name, me, loc, tg, lens in views:
        tiles.data = me
        cam.location = Vector(loc)
        cam.rotation_euler = (Vector(tg) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        cam.data.lens = lens
        scn.render.filepath = os.path.join(OUT, "tiles_" + name + ".png")
        bpy.ops.render.render(write_still=True)
    tiles.data = me_rest
    print("TILES_CHECK_OK", OUT, "lift", LIFT)


try:
    main()
except BaseException as e:
    print("TILES_CHECK_FALLO", type(e).__name__, e)
    traceback.print_exc()
