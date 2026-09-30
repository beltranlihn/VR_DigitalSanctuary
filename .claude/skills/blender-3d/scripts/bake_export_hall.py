# bake_export_hall.py - hornea la LUZ de la escena de render_hall (Cycles) en colores de vertice de la cascara
# y exporta los FBX para Unreal (la obra es unlit: el material de Unreal multiplica esta luz por el albedo).
#   SM_HallShell_SC.fbx       cascara + las dos pieles negras (estatico)   color de vertice = irradiancia/escala
#   SM_HallDoorLeaf_R/L_SC    hojas de la puerta Este (la Oeste es la misma malla girada 180 en Z)
# Uso: blender --background <SM_HallShell_SC.blend> --python bake_export_hall.py
import importlib.util
import math
import os
import traceback

import bpy

AQUI = os.path.dirname(os.path.abspath(__file__))
os.environ["HALL_NO_RENDER"] = "1"
spec = importlib.util.spec_from_file_location("render_hall", os.path.join(AQUI, "render_hall.py"))
rh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rh)

BAKE_SAMPLES = 4096
SMOOTH_ITERS = 12     # suavizado de la luz entre vecinos (la luz es de baja frecuencia; el ruido no)
PERCENTIL = 0.80      # percentil de la luz INTERIOR que queda en 1 (el labio del oculo recibe ~30x y satura)


def main():
    rh.setup()
    scn = bpy.context.scene
    for nm in ("FogInterior", "HazeExterior"):     # el horneado es de superficie: sin niebla
        bpy.data.objects[nm].hide_render = True
    shell = bpy.data.objects["SM_HallShell_SC"]
    # juntar las pieles negras a la cascara (estaticas, mismo material negro)
    bpy.ops.object.select_all(action='DESELECT')
    for nm in ("SM_HallDoorMask_E", "SM_HallDoorMask_W"):
        bpy.data.objects[nm].select_set(True)
    shell.select_set(True)
    bpy.context.view_layer.objects.active = shell
    bpy.ops.object.join()
    me = shell.data
    ca = me.color_attributes.new("Light", 'FLOAT_COLOR', 'POINT')
    me.color_attributes.active_color = ca
    scn.cycles.samples = BAKE_SAMPLES
    scn.render.bake.target = 'VERTEX_COLORS'
    bpy.ops.object.select_all(action='DESELECT')
    shell.select_set(True)
    bpy.context.view_layer.objects.active = shell
    bpy.ops.object.bake(type='DIFFUSE', pass_filter={'DIRECT', 'INDIRECT'}, target='VERTEX_COLORS')
    # suavizado laplaciano de la irradiancia (sin cruzar de la cara interior a la exterior: la exterior es 0)
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    cols = [list(c.color[:3]) for c in ca.data]
    nbr = [[e.other_vert(v).index for e in v.link_edges] for v in bm.verts]
    bm.free()
    for _ in range(SMOOTH_ITERS):
        new = []
        for i, ns in enumerate(nbr):
            acc = cols[i][:]
            for k in ns:
                for ch in range(3):
                    acc[ch] += cols[k][ch]
            n = len(ns) + 1
            new.append([acc[0] / n, acc[1] / n, acc[2] / n])
        cols = new
    for c, v in zip(ca.data, cols):
        c.color = (v[0], v[1], v[2], 1.0)
    # normalizar a [0,1] y pasar a byte para el FBX
    vals = [max(c.color[0], c.color[1], c.color[2]) for c in ca.data]
    s = sorted(vals)
    print("PERCENTILES", {q: round(s[int(len(s) * q)], 4) for q in (0.05, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99, 0.995)})
    lit = sorted(v for v in vals if v > 0.02)          # solo lo que recibe luz (el exterior queda en 0)
    print("PERC_LIT", {q: round(lit[int(len(lit) * q)], 3) for q in (0.1, 0.25, 0.5, 0.75, 0.8, 0.85, 0.9, 0.95)})
    scale = max(lit[int(len(lit) * PERCENTIL)], 1e-6)  # el labio del oculo satura: es lo mas brillante igual
    # 🔴 la luz va en CANALES DE UV, no en color de vertice: el importador de Unreal descarto los colores
    # de vertice (medido: pared uniforme con LightScale 1 y 0,3). UV = float (sin recorte, sin sRGB).
    #   UV1 = copia de UV0 (Unreal lo pisa con el lightmap generado)
    #   UV2 = (R, G)   UV3 = (B, 0)      -> ojo: Unreal invierte la V al importar: G llega como 1 - G
    uv0 = me.uv_layers["UVMap"]
    lm = me.uv_layers.new(name="Lightmap")
    l2 = me.uv_layers.new(name="LightRG")
    l3 = me.uv_layers.new(name="LightB")
    for poly in me.polygons:
        for li in poly.loop_indices:
            c = ca.data[me.loops[li].vertex_index].color
            lm.data[li].uv = uv0.data[li].uv
            l2.data[li].uv = (c[0] / scale, c[1] / scale)
            l3.data[li].uv = (c[2] / scale, 0.0)
    me.color_attributes.remove(ca)
    me.uv_layers.active = uv0
    destino = os.path.dirname(bpy.data.filepath)

    def export(obs, name):
        bpy.ops.object.select_all(action='DESELECT')
        for o in obs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = obs[0]
        path = os.path.join(destino, name + ".fbx")
        bpy.ops.export_scene.fbx(filepath=path, use_selection=True, apply_unit_scale=True, global_scale=1.0,
                                 apply_scale_options='FBX_SCALE_NONE', object_types={'MESH'},
                                 mesh_smooth_type='FACE', use_tspace=True, use_mesh_modifiers=True,
                                 colors_type='NONE', add_leaf_bones=False, bake_anim=False, path_mode='STRIP')
        return path
    out = [export([shell], "SM_HallShell_SC")]
    for side in ("R", "L"):
        leaf = bpy.data.objects["SM_HallDoorLeaf_E_%s" % side]
        leaf.name = "SM_HallDoorLeaf_%s_SC" % side
        out.append(export([leaf], leaf.name))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(destino, "SM_HallShell_SC_baked.blend"))
    print("EXPORT_OK", {"escala_luz": round(scale, 4), "fbx": [os.path.basename(p) for p in out]})


try:
    main()
except BaseException as e:
    print("EXPORT_FALLO", type(e).__name__, e)
    traceback.print_exc()
