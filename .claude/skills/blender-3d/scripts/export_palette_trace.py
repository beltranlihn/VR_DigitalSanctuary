# export_palette_trace.py - exporta SM_DrawPalette_Trace_SC (el trazo de luz de la aparicion "luz primero" de la paleta, para
# Drawing): cinta en la ranura (r y z de gen_draw_palette), UV0.x = fraccion del contorno desde arriba, antihorario visto
# desde la cara; UV0.y = 0..1 a lo ancho (60 mm). Uso: blender --background --python export_palette_trace.py
import sys, os, traceback
sys.path.insert(0, r"C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/.claude/skills/blender-3d/scripts")
try:
    import bpy
    import anim_luz_objects as LZ
    import anim_palette_base as P
    G = P.g
    bpy.ops.wm.read_factory_settings(use_empty=True)
    r = (G.GROOVE_IN + G.GROOVE_OUT) / 2 / G.PX * G.R * 1000
    z = (G.u(G.Z_GROOVE) + 0.0004) * 1000
    cfg = {"path": LZ.circle(r), "z": z, "hw": 30.0, "face": 1.0}
    me = LZ.trace_mesh(cfg, "SM_DrawPalette_Trace_SC")
    ob = bpy.data.objects.new(me.name, me)
    bpy.context.scene.collection.objects.link(ob)
    LZ.export_fbx(ob, os.path.join(P.DIR, me.name + ".fbx"))
    print("PAL_TRACE_OK r_mm %.2f z_mm %.2f tris %d" % (r, z, len(me.polygons) * 2))
except BaseException as e:
    print("FALLO", e); traceback.print_exc()
