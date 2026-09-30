# gen_quest_controller.py - mandos de la obra a partir del Meta Quest Touch Plus oficial (paquete de arte de Meta,
# Descargas/oculus-controller-art-v1.8; la licencia permite usarlo para representar el producto en la experiencia VR).
# Pedido de Beltran (2026-09-29): "como el de Meta Quest, dos colores (cuerpo y tapa)", SIN botones (solo el gatillo,
# que se mueve y cambia de material al apretar), invertido: cuerpo NEGRO y tapa GRIS-BLANCA; la cascara CONTINUA,
# sin aberturas de botones.
# Como el FBX oficial es un armado de cascaras abiertas (845 aristas de borde), no se tapan agujeros a mano: se juntan
# cuerpo + tapa (sin botones), se rellenan todas las aberturas y se REMALLA POR VOXELES -> un solido cerrado y liso;
# despues se decima al presupuesto de Quest. La division cuerpo/tapa se transfiere como MASCARA en UV1 (x = 1 tapa)
# desde la tapa original (BVH), para que el material pinte el borde limpio. El gatillo: igual, solido aparte, con el
# ORIGEN EN SU BISAGRA (el BP lo gira en X al apretar).
# Marco: el del FBX importado (= /Game/NeuralCanvas/Mesh/Controller en Unreal). Unidades: metros.
# Uso: blender --background --python gen_quest_controller.py [-- R|L]
import math
import os
import sys
import traceback
from collections import Counter

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

SRC = r"C:/Users/beltr/Downloads/oculus-controller-art-v1.8/Meta Quest Touch Plus"
AQUI = os.path.dirname(os.path.abspath(__file__))
DESTINO = os.path.abspath(os.path.join(AQUI, "..", "..", "..", "..", "VR_Test", "Saved", "ClaudeScripts", "QuestController"))
VOXEL = 0.0010          # 1 mm: el grip y los botones desaparecen, los cantos quedan nitidos
BODY_TRIS = 9000
TRIG_TRIS = 1200
SMOOTH_ITERS = 4


def classify(o, side):
    me = o.data
    img = bpy.data.images.load(os.path.join(SRC, "textures", "MetaQuestTouchPlus_%s_BaseColor.png" % ("right" if side == "R" else "Left")))
    W, H = img.size
    px = list(img.pixels)
    uv = me.uv_layers[0]
    names = {g.index: g.name for g in o.vertex_groups}
    out = []
    for p in me.polygons:
        gs = Counter()
        for vi in p.vertices:
            v = me.vertices[vi]
            if v.groups:
                gs[names[max(v.groups, key=lambda g: g.weight).group]] += 1
        g = gs.most_common(1)[0][0] if gs else "(none)"
        if g.endswith("trigger_front"):
            out.append("trigger")
        elif not g.endswith("controller_world"):
            out.append("btn")
        else:
            u_ = sum(uv.data[li].uv[0] for li in p.loop_indices) / p.loop_total
            v_ = sum(uv.data[li].uv[1] for li in p.loop_indices) / p.loop_total
            x = min(W - 1, max(0, int(u_ % 1.0 * W)))
            y = min(H - 1, max(0, int(v_ % 1.0 * H)))
            i = (y * W + x) * 4
            out.append("cap" if 0.3 * px[i] + 0.59 * px[i + 1] + 0.11 * px[i + 2] < 0.35 else "body")
    return out


def solid_from(faces_bm_builder, name):
    """bmesh (cascara abierta) -> rellenar aberturas -> objeto -> remallado por voxeles -> suavizado -> decimado."""
    bm = faces_bm_builder()
    bnd = [e for e in bm.edges if e.is_boundary]
    bmesh.ops.holes_fill(bm, edges=bnd, sides=0)
    me = bpy.data.meshes.new(name + "_src")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    rm = ob.modifiers.new("Voxel", 'REMESH')
    rm.mode, rm.voxel_size, rm.use_smooth_shade = 'VOXEL', VOXEL, True
    sm = ob.modifiers.new("Suave", 'CORRECTIVE_SMOOTH')
    sm.iterations, sm.factor, sm.use_only_smooth = SMOOTH_ITERS, 0.5, False
    bpy.context.view_layer.objects.active = ob
    for m in ("Voxel", "Suave"):
        bpy.ops.object.modifier_apply(modifier=m)
    return ob


def decimate(ob, target):
    n = sum(len(p.vertices) - 2 for p in ob.data.polygons)   # en TRIANGULOS (el remallado deja quads)
    if n > target:
        d = ob.modifiers.new("Dec", 'DECIMATE')
        d.ratio = target / n
        d.use_collapse_triangulate = True
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.modifier_apply(modifier="Dec")
    for p in ob.data.polygons:
        p.use_smooth = True


def smart_uv(ob):
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.01)
    bpy.ops.object.mode_set(mode='OBJECT')
    ob.data.uv_layers[0].name = "UVMap"


def build(side):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.fbx_import(filepath=os.path.join(SRC, "models", "MetaQuestTouchPlus_%s.fbx" % ("Right" if side == "R" else "Left")))
    o = [x for x in bpy.data.objects if x.type == 'MESH' and "controller" in x.name.lower() and "battery" not in x.name.lower()][0]
    laser = [x for x in bpy.data.objects if x.name.endswith("laser_begin")]
    laser_pos = laser[0].matrix_world.translation.copy() if laser else None
    for m in list(o.modifiers):
        o.modifiers.remove(m)
    cls = classify(o, side)
    mw = o.matrix_world.copy()
    src = o.data

    def shell(keep):
        def f():
            bm = bmesh.new()
            bm.from_mesh(src)
            bm.transform(mw)
            bm.faces.ensure_lookup_table()
            bmesh.ops.delete(bm, geom=[fc for fc in bm.faces if cls[fc.index] not in keep], context='FACES')
            return bm
        return f
    # BVH de la tapa y del cuerpo originales (para transferir la mascara)
    bmr = bmesh.new()
    bmr.from_mesh(src)
    bmr.transform(mw)
    bmr.faces.ensure_lookup_table()
    ref_cls = [cls[f.index] for f in bmr.faces]
    bvh = BVHTree.FromBMesh(bmr)
    body = solid_from(shell({"body", "cap"}), "SM_QuestCtrl_Body_%s_SC" % side)
    trig = solid_from(shell({"trigger"}), "SM_QuestCtrl_Trigger_%s_SC" % side)
    for ob in list(bpy.data.objects):
        if ob not in (body, trig):
            bpy.data.objects.remove(ob)
    decimate(body, BODY_TRIS)
    decimate(trig, TRIG_TRIS)
    # mascara tapa (UV1 "CapMask"): por vertice, la clase de la cara original mas cercana
    me = body.data
    mask = []
    for v in me.vertices:
        loc, nrm, idx, dist = bvh.find_nearest(v.co)
        mask.append(1.0 if (idx is not None and ref_cls[idx] in ("cap", "btn")) else 0.0)
    # suavizar un paso entre vecinos para que el borde no sea escalonado
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    nb = [[e.other_vert(v).index for e in v.link_edges] for v in bm.verts]
    bm.free()
    for _ in range(2):
        mask = [(mask[i] + sum(mask[k] for k in ns)) / (len(ns) + 1) for i, ns in enumerate(nb)]
    smart_uv(body)
    smart_uv(trig)
    cm = me.uv_layers.new(name="CapMask")
    for li, loop in enumerate(me.loops):
        cm.data[li].uv = (mask[loop.vertex_index], 0.0)
    # gatillo: origen en la bisagra (arriba del gatillo, pegado al cuerpo)
    tv = [v.co.copy() for v in trig.data.vertices]
    ztop = max(p.z for p in tv)
    top = [p for p in tv if p.z > ztop - 0.004]
    piv = sum(top, Vector()) / len(top)
    trig.data.transform(__import__('mathutils').Matrix.Translation(-piv))
    trig.location = piv
    m_body = bpy.data.materials.new("M_QuestCtrl_Body")
    m_trig = bpy.data.materials.new("M_QuestCtrl_Trigger")
    body.data.materials.append(m_body)
    trig.data.materials.append(m_trig)
    info = {"body_tris": sum(len(p.vertices) - 2 for p in body.data.polygons), "trig_tris": sum(len(p.vertices) - 2 for p in trig.data.polygons),
            "body_nonmanifold": sum(1 for e in body.data.edges if False), "pivot_cm": [round(x * 100, 2) for x in piv],
            "laser_cm": [round(x * 100, 2) for x in laser_pos] if laser_pos else None,
            "cap_frac": round(sum(mask) / len(mask), 3)}
    bm = bmesh.new()
    bm.from_mesh(body.data)
    info["body_boundary_edges"] = sum(1 for e in bm.edges if e.is_boundary)
    info["body_nonmanifold"] = sum(1 for e in bm.edges if not e.is_manifold)
    bm.free()
    os.makedirs(DESTINO, exist_ok=True)
    for ob in (body, trig):
        bpy.ops.object.select_all(action='DESELECT')
        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob
        bpy.ops.export_scene.fbx(filepath=os.path.join(DESTINO, ob.name + ".fbx"), use_selection=True, apply_unit_scale=True,
                                 global_scale=1.0, apply_scale_options='FBX_SCALE_NONE', object_types={'MESH'},
                                 mesh_smooth_type='FACE', use_tspace=True, colors_type='NONE', add_leaf_bones=False,
                                 bake_anim=False, path_mode='STRIP')
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(DESTINO, "QuestCtrl_%s.blend" % side))
    return info


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["R", "L"]
    for side in argv:
        try:
            print("QCTRL_OK", side, build(side))
        except BaseException as e:
            print("QCTRL_FALLO", side, type(e).__name__, e)
            traceback.print_exc()
