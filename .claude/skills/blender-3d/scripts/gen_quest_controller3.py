# gen_quest_controller3.py - termina el mando de la obra (4a version: superficie de subdivision calculada, qc_fit.py).
# Toma las mallas finales (quads del nivel 1 en posicion limite + normales de la superficie limite) y deja:
#   - normales propias (las de la superficie lisa, no las de las caras) y sombreado suave
#   - UV0 (proyeccion inteligente) y UV1 "CapMask": x = altura en mm sobre la linea de la tapa (> 0 tapa, < 0 cuerpo);
#     el material hace el borde con smoothstep/fwidth, limpio a cualquier distancia
#   - gatillo con ORIGEN EN SU BISAGRA (la del hueso del gatillo oficial); eje y sentido en qc_trigger_hinge.json
#   - izquierdo = derecho espejado en X (sin botones son iguales, pedido de Beltran)
#   - FBX SM_QuestCtrl_{Body,Trigger}_{R,L}_SC + QuestCtrl_SC.blend
# Uso: blender --background --python gen_quest_controller3.py -- <dir>
import json
import math
import os
import sys
import traceback

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
D = argv[0] if argv else "."


def load(name, nrm_file, cap=None):
    bpy.ops.wm.obj_import(filepath=os.path.join(D, name + ".obj"), forward_axis='Y', up_axis='Z')
    ob = bpy.context.selected_objects[0]
    me = ob.data
    N = np.load(os.path.join(D, nrm_file))
    assert len(N) == len(me.vertices), (len(N), len(me.vertices))
    for p in me.polygons:
        p.use_smooth = True
    me.normals_split_custom_set_from_vertices([tuple(n) for n in N])
    uv = me.uv_layers[0] if me.uv_layers else me.uv_layers.new(name="UVMap")
    uv.name = "UVMap"
    cm = me.uv_layers.new(name="CapMask")
    vals = cap if cap is not None else np.zeros(len(me.vertices), np.float32)
    for li, lp in enumerate(me.loops):
        cm.data[li].uv = (float(vals[lp.vertex_index]), 0.0)
    return ob, N, vals


def smart_uv(ob):
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    me = ob.data
    me.uv_layers.active = me.uv_layers["UVMap"]
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.01)
    bpy.ops.object.mode_set(mode='OBJECT')


def mirror(ob, N, vals, name):
    me = ob.data.copy()
    me.transform(Matrix.Scale(-1.0, 4, Vector((1, 0, 0))))
    me.flip_normals()
    Nm = N.copy()
    Nm[:, 0] *= -1
    me.normals_split_custom_set_from_vertices([tuple(n) for n in Nm])
    m2 = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(m2)
    m2.location = Vector((-ob.location.x, ob.location.y, ob.location.z))
    return m2


def checks(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    r = {"tris": sum(len(f.verts) - 2 for f in bm.faces), "abiertas": sum(1 for e in bm.edges if not e.is_manifold),
         "degeneradas": sum(1 for f in bm.faces if f.calc_area() < 1e-9)}
    bm.free()
    return r


def export(ob, path):
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, apply_unit_scale=True, global_scale=1.0,
                             apply_scale_options='FBX_SCALE_NONE', object_types={'MESH'}, mesh_smooth_type='FACE',
                             use_tspace=True, colors_type='NONE', add_leaf_bones=False, bake_anim=False, path_mode='STRIP')


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    hinge = json.load(open(os.path.join(D, "qc_trigger_hinge.json")))
    piv = Vector(hinge["pivot_mm"]) / 1000.0
    body, nb, cap = load("qc_body_R_final", "qc_body_R_final_nrm.npy", np.load(os.path.join(D, "qc_body_R_final_cap.npy")))
    trig, nt, _ = load("qc_trigger_R_final", "qc_trigger_R_final_nrm.npy")
    smart_uv(body)
    smart_uv(trig)
    trig.data.transform(Matrix.Translation(-piv))
    trig.location = piv
    for ob, mn in ((body, "M_QuestCtrl_Body"), (trig, "M_QuestCtrl_Trigger")):
        ob.data.materials.clear()
        ob.data.materials.append(bpy.data.materials.get(mn) or bpy.data.materials.new(mn))
    body.name, trig.name = "SM_QuestCtrl_Body_R_SC", "SM_QuestCtrl_Trigger_R_SC"
    body.data.name, trig.data.name = body.name, trig.name
    bodyL = mirror(body, nb, cap, "SM_QuestCtrl_Body_L_SC")
    trigL = mirror(trig, nt, None, "SM_QuestCtrl_Trigger_L_SC")
    info = {}
    for ob in (body, trig, bodyL, trigL):
        info[ob.name] = checks(ob)
        # el importador de Unreal HORNEA la posicion del objeto en los vertices: el gatillo se exporta en el origen
        # (su malla ya esta referida a la bisagra) para que en Unreal su pivote SEA la bisagra
        keep = ob.location.copy()
        if ob in (trig, trigL):
            ob.location = (0.0, 0.0, 0.0)
        export(ob, os.path.join(D, ob.name + ".fbx"))
        ob.location = keep
    ax = hinge["axis"]
    info["bisagra"] = {"pivote_cm_blender_R": [round(x * 100, 3) for x in piv], "eje_blender_R": [round(a, 4) for a in ax],
                       "apretar_signo_blender_R": hinge["press_sign"]}
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, "QuestCtrl_SC.blend"))
    print("QC3_OK", json.dumps(info))


try:
    main()
except BaseException as e:
    print("QC3_FALLO", type(e).__name__, e)
    traceback.print_exc()
