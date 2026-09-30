# gen_quest_controller2.py - termina el mando modelado desde cero (sdf_quest_controller.py): decimado a presupuesto
# Quest, sombreado suave, UV0, mascara de TAPA en UV1 "CapMask" (x = distancia con signo, en cm, al plano que corta la
# tapa: > 0 tapa, < 0 cuerpo -> el material hace el borde limpio con smoothstep), gatillo con ORIGEN EN SU BISAGRA,
# y el IZQUIERDO = el derecho espejado en X (sin botones son iguales, pedido de Beltran). Export FBX + .blend.
# Uso: blender --background --python gen_quest_controller2.py   (lee los OBJ de VR_Test/Saved/ClaudeScripts/QuestController)
import importlib.util
import math
import os
import traceback

import bmesh
import bpy
from mathutils import Matrix, Vector

AQUI = os.path.dirname(os.path.abspath(__file__))
D = os.path.abspath(os.path.join(AQUI, "..", "..", "..", "..", "VR_Test", "Saved", "ClaudeScripts", "QuestController"))
spec = importlib.util.spec_from_file_location("sdf", os.path.join(AQUI, "sdf_quest_controller.py"))
BODY_TRIS, TRIG_TRIS = 9000, 1200
# plano de la tapa (mismo que la cabeza del SDF): la tapa es la cara de arriba + la mitad del canto redondeado
HEAD_C = Vector((0.70, 0.05, -0.40))
HEAD_N = Vector((0.06, 0.19, 0.98)).normalized()
CAP_H = 0.80 - 0.70 * 0.55          # HEAD_HH - HEAD_RE * 0.55 (cm sobre el centro de la cabeza)


def load(name):
    bpy.ops.wm.obj_import(filepath=os.path.join(D, name + ".obj"), forward_axis='Y', up_axis='Z')
    ob = bpy.context.selected_objects[0]
    ob.name = name
    return ob


def clean(ob, target):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()
    n = len(ob.data.polygons)
    dec = ob.modifiers.new("Dec", 'DECIMATE')
    dec.ratio = target / n
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
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.01)
    bpy.ops.object.mode_set(mode='OBJECT')
    ob.data.uv_layers[0].name = "UVMap"


def cap_mask(ob):
    me = ob.data
    cm = me.uv_layers.new(name="CapMask")
    for li, loop in enumerate(me.loops):
        p = me.vertices[loop.vertex_index].co * 100.0
        cm.data[li].uv = ((p - HEAD_C).dot(HEAD_N) - CAP_H, 0.0)


def export(ob, path):
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, apply_unit_scale=True, global_scale=1.0,
                             apply_scale_options='FBX_SCALE_NONE', object_types={'MESH'}, mesh_smooth_type='FACE',
                             use_tspace=True, colors_type='NONE', add_leaf_bones=False, bake_anim=False, path_mode='STRIP')


def mirror_copy(ob, name):
    me = ob.data.copy()
    me.transform(Matrix.Scale(-1.0, 4, Vector((1, 0, 0))))
    me.flip_normals()
    m2 = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(m2)
    m2.location = Vector((-ob.location.x, ob.location.y, ob.location.z))
    return m2


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    body = load("qc_body_R")
    trig = load("qc_trigger_R")
    clean(body, BODY_TRIS)
    clean(trig, TRIG_TRIS)
    smart_uv(body)
    smart_uv(trig)
    cap_mask(body)
    # gatillo: origen en la bisagra (lo mas alto del gatillo, pegado a la cabeza); el BP lo gira en X
    tv = [v.co.copy() for v in trig.data.vertices]
    zt = max(p.z for p in tv)
    top = [p for p in tv if p.z > zt - 0.003]
    piv = sum(top, Vector()) / len(top)
    trig.data.transform(Matrix.Translation(-piv))
    trig.location = piv
    m_body = bpy.data.materials.new("M_QuestCtrl_Body")
    m_trig = bpy.data.materials.new("M_QuestCtrl_Trigger")
    body.data.materials.append(m_body)
    trig.data.materials.append(m_trig)
    body.name, trig.name = "SM_QuestCtrl_Body_R_SC", "SM_QuestCtrl_Trigger_R_SC"
    bodyL = mirror_copy(body, "SM_QuestCtrl_Body_L_SC")
    trigL = mirror_copy(trig, "SM_QuestCtrl_Trigger_L_SC")
    info = {}
    for ob in (body, trig, bodyL, trigL):
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        info[ob.name] = {"tris": len(ob.data.polygons), "abiertas": sum(1 for e in bm.edges if not e.is_manifold),
                         "astillas": sum(1 for f in bm.faces if f.calc_area() < 1e-8)}
        bm.free()
        export(ob, os.path.join(D, ob.name + ".fbx"))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, "QuestCtrl_SC.blend"))
    print("QC2_OK", info, "pivote_cm", [round(x * 100, 2) for x in piv])


try:
    main()
except BaseException as e:
    print("QC2_FALLO", type(e).__name__, e)
    traceback.print_exc()
