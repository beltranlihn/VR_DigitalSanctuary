# reskin_to_skeleton.py — re-skinear una malla ajena al esqueleto de otra (Blender headless)
#
# Nacio el 2026-09-02 para meter la mano nueva (`hand_final.fbx`, rig de Maya) en
# `SK_MannequinsXR`, de modo que `ABP_MannequinsXR` la anime SIN tocar un solo nodo del pawn.
# Ver `blueprints/BP_VRPawn_SC.md` para el caso completo.
#
# COMO SE CORRE (el MCP de Blender falla si BLENDER_PATH no esta seteado -> invocar el exe):
#   "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background \
#       --factory-startup --python reskin_to_skeleton.py -- --export
#
# EL METODO, en cuatro pasos. Los tres primeros se VERIFICAN con numeros antes de exportar:
#   1. Ajuste global (Umeyama: escala + rotacion + traslacion) sobre 6 landmarks —
#      munieca y los cinco nudillos. 🔴 El `det` del resultado ES la prueba de quiralidad:
#      +1 = misma mano, -1 = son manos opuestas y hay que espejar antes.
#   2. Retarget hueso a hueso: por cada falange, TRASLADAR la articulacion a la de destino
#      y despues APUNTAR el segmento a la siguiente. Las dos cosas.
#      ⚠ Apuntar solo no alcanza (los huesos tienen largos distintos: quedaba 17 mm de error
#      en el pulgar), y escalar el hueso NO funciona: `pose_bone.matrix` ignora la escala
#      al asignarse. Trasladar + apuntar deja los 20 puntos en 0.0 mm.
#   3. Hornear la pose en la geometria (`modifier_apply` del Armature) y remapear los grupos
#      de vertices a los nombres del esqueleto destino, SUMANDO los que colapsan
#      (p. ej. INDEX_TOP + INDEX_UP_TOP -> index_03).
#   4. Llevar la malla al ESPACIO DEL ESQUELETO antes de exportar:
#      `v.co = A.matrix_world.inverted() @ (M.matrix_world @ v.co)` y `M.matrix_world = A.matrix_world`.
#      🔴 Sin esto las unidades del FBX salen mal y la malla entra a Unreal 100x chica.
#      Y el espejo se hace negando `v.co.x` + `mesh.flip_normals()`, NUNCA con escala negativa
#      y `transform_apply` sobre un objeto emparentado (heredaba la escala del padre y las dos
#      manos salieron a tamanios distintos).
#
# En Unreal se importa con `SkeletalMeshTools.import_file(..., skeleton=<el esqueleto destino>)`.
# Si el esqueleto encaja, el asset queda apuntando a el y las animaciones existentes lo deforman.

import bpy, json, sys
import numpy as np
from mathutils import Matrix, Vector

DO_EXPORT = "--export" in sys.argv
S = "r"
log = {}
bpy.ops.wm.read_factory_settings(use_empty=True)

bpy.ops.import_scene.fbx(filepath=r"C:\Users\beltr\Desktop\vr-hand\source\SKM_MannyXR_right.FBX")
A = [o for o in bpy.data.objects if o.type=='ARMATURE'][0]
M_manny = [o for o in bpy.data.objects if o.type=='MESH'][0]
bhead = lambda n: A.matrix_world @ A.data.bones[n].head_local
btail = lambda n: A.matrix_world @ A.data.bones[n].tail_local

before = set(o.name for o in bpy.data.objects)
bpy.ops.import_scene.fbx(filepath=r"C:\Users\beltr\Desktop\vr-hand\source\hand_final.fbx")
new = [o for o in bpy.data.objects if o.name not in before]
A_h = [o for o in new if o.type=='ARMATURE'][0]
M_h = [o for o in new if o.type=='MESH'][0]
for o in list(new):
    if o not in (A_h, M_h): bpy.data.objects.remove(o, do_unlink=True)
hhead = lambda n: A_h.matrix_world @ A_h.data.bones[n].head_local

PAIRS=[("HANDPALM_joint","hand_"+S),("INDEX_BASE_joint","index_01_"+S),
       ("MIDDLE_F_BASE_joint","middle_01_"+S),("RING_BASE_joint","ring_01_"+S),
       ("PINK_BASE_joint","pinky_01_"+S),("THUMB_BASE_joint","thumb_01_"+S)]
P=np.array([list(hhead(a)) for a,b in PAIRS]); Q=np.array([list(bhead(b)) for a,b in PAIRS])
mp,mq=P.mean(0),Q.mean(0); Pc,Qc=P-mp,Q-mq
U,Sv,Vt=np.linalg.svd(Pc.T@Qc/len(P)); d=np.sign(np.linalg.det(Vt.T@U.T))
R=Vt.T@np.diag([1,1,d])@U.T
sc=float((Sv*np.array([1,1,d])).sum()/(Pc**2).sum()*len(P)); t=mq-sc*(R@mp)
log["scale"]=round(sc,4); log["det"]=round(float(np.linalg.det(R)),3)
T=Matrix.Identity(4)
for i in range(3):
    for j in range(3): T[i][j]=sc*R[i,j]
    T[i][3]=t[i]

M_h.parent=None
for ob,mat in ((M_h,T@M_h.matrix_world),(A_h,T@A_h.matrix_world)):
    ob.matrix_world=mat
    bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True)
    bpy.context.view_layer.objects.active=ob
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
bpy.context.view_layer.update()

CHAINS={"INDEX":("index",["INDEX_BASE_joint","INDEX_MID_joint","INDEX_TOP_joint","INDEX_UP_TOP_joint"]),
        "MIDDLE":("middle",["MIDDLE_F_BASE_joint","MIDDLE_F_MID_joint","MIDDLE_F_TOP_joint","MIDDLE_F_UP_TOP_joint"]),
        "RING":("ring",["RING_BASE_joint","RING_MID_joint","RING_TOP_joint","RING_UP_TOP_joint"]),
        "PINK":("pinky",["PINK_BASE_joint","PINK_MID_joint","PINK_TOP_joint","PINK_UP_TOP_joint"]),
        "THUMB":("thumb",["THUMB_BASE_joint","THUMB_MID_joint","THUMB_TOP_joint","THUMB_UP_TOP_joint"])}

bpy.ops.object.select_all(action='DESELECT'); A_h.select_set(True)
bpy.context.view_layer.objects.active=A_h
bpy.ops.object.mode_set(mode='EDIT')
for eb in A_h.data.edit_bones: eb.use_connect=False
bpy.ops.object.mode_set(mode='POSE')
PB=A_h.pose.bones

def targets(pref):
    return [bhead(pref+"_01_"+S), bhead(pref+"_02_"+S), bhead(pref+"_03_"+S), btail(pref+"_03_"+S)]

for name,(pref,chain) in CHAINS.items():
    tg=targets(pref)
    for i in range(len(chain)):
        pb=PB[chain[i]]
        # 1) llevar esta articulacion exactamente a la de Manny
        pb.matrix=Matrix.Translation(tg[i]-pb.head)@pb.matrix
        bpy.context.view_layer.update()
        # 2) orientar el segmento hacia la articulacion siguiente
        if i+1 < len(chain):
            cur=PB[chain[i+1]].head-pb.head
            tgt=tg[i+1]-pb.head
            if cur.length>1e-9 and tgt.length>1e-9:
                q=cur.normalized().rotation_difference(tgt.normalized())
                h=pb.head.copy()
                pb.matrix=(Matrix.Translation(h)@q.to_matrix().to_4x4()@Matrix.Translation(-h))@pb.matrix
                bpy.context.view_layer.update()

err={}
for name,(pref,chain) in CHAINS.items():
    tg=targets(pref)
    err[name]=[round((PB[chain[i]].head-tg[i]).length*1000,2) for i in range(4)]
log["error_mm_por_falange"]=err
bpy.ops.object.mode_set(mode='OBJECT')
print("###JSON###"+json.dumps(log)+"###END###")

# ================= hornear la pose en la geometria =================
bpy.ops.object.select_all(action='DESELECT'); M_h.select_set(True)
bpy.context.view_layer.objects.active=M_h
for m in list(M_h.modifiers):
    if m.type=='ARMATURE': bpy.ops.object.modifier_apply(modifier=m.name)

# ================= remapear los grupos de vertices =================
MAP={"Root_joint":"hand_","HANDPALM_joint":"hand_",
 "INDEX_BASE_joint":"index_01_","INDEX_MID_joint":"index_02_","INDEX_TOP_joint":"index_03_","INDEX_UP_TOP_joint":"index_03_",
 "MIDDLE_F_BASE_joint":"middle_01_","MIDDLE_F_MID_joint":"middle_02_","MIDDLE_F_TOP_joint":"middle_03_","MIDDLE_F_UP_TOP_joint":"middle_03_",
 "RING_BASE_joint":"ring_01_","RING_MID_joint":"ring_02_","RING_TOP_joint":"ring_03_","RING_UP_TOP_joint":"ring_03_",
 "PINK_BASE_joint":"pinky_01_","PINK_MID_joint":"pinky_02_","PINK_TOP_joint":"pinky_03_","PINK_UP_TOP_joint":"pinky_03_",
 "THUMB_BASE_joint":"thumb_01_","THUMB_MID_joint":"thumb_02_","THUMB_TOP_joint":"thumb_03_","THUMB_UP_TOP_joint":"thumb_03_"}
old={g.index:g.name for g in M_h.vertex_groups}
acc=[]
for v in M_h.data.vertices:
    d={}
    for ge in v.groups:
        t=MAP.get(old.get(ge.group))
        if t: d[t+S]=d.get(t+S,0.0)+ge.weight
    acc.append(d)
for g in list(M_h.vertex_groups): M_h.vertex_groups.remove(g)
newg={n+S:M_h.vertex_groups.new(name=n+S) for n in sorted(set(MAP.values()))}
for i,d in enumerate(acc):
    for n,w in d.items():
        if w>1e-5: newg[n].add([i],min(w,1.0),'REPLACE')
log["grupos"]=len(M_h.vertex_groups); log["verts_sin_peso"]=sum(1 for d in acc if not d)

# ===== llevar la malla al ESPACIO DEL ESQUELETO (mismo object matrix que la malla de Manny) =====
Minv=A.matrix_world.inverted()
W=M_h.matrix_world.copy()
for v in M_h.data.vertices: v.co = Minv @ (W @ v.co)
M_h.matrix_world = A.matrix_world.copy()

bpy.data.objects.remove(A_h, do_unlink=True)
bpy.data.objects.remove(M_manny, do_unlink=True)
M_h.name="SKM_Hand_R"; M_h.data.name="SKM_Hand_R"
M_h.parent=A
M_h.matrix_parent_inverse=Matrix.Identity(4)
M_h.matrix_world=A.matrix_world.copy()
mod=M_h.modifiers.new(name="Armature",type='ARMATURE'); mod.object=A

# ===== espejo exacto en x=0 (hand_l y hand_r son espejos exactos en X) =====
M_l=M_h.copy(); M_l.data=M_h.data.copy(); bpy.context.collection.objects.link(M_l)
M_l.name="SKM_Hand_L"; M_l.data.name="SKM_Hand_L"
for v in M_l.data.vertices: v.co.x = -v.co.x
M_l.data.flip_normals()
for g in M_l.vertex_groups:
    if g.name.endswith("_r"): g.name=g.name[:-2]+"_l"
M_l.parent=A; M_l.matrix_parent_inverse=Matrix.Identity(4)
M_l.matrix_world=A.matrix_world.copy()
for m in M_l.modifiers:
    if m.type=='ARMATURE': m.object=A

def bbox(o):
    ws=[o.matrix_world @ v.co for v in o.data.vertices]
    return [round(max(v[i] for v in ws)-min(v[i] for v in ws),4) for i in range(3)]
log["bbox_R"]=bbox(M_h); log["bbox_L"]=bbox(M_l)

if DO_EXPORT:
    for ob,path in ((M_h,r"C:\Users\beltr\Desktop\vr-hand\source\SKM_Hand_R.fbx"),
                    (M_l,r"C:\Users\beltr\Desktop\vr-hand\source\SKM_Hand_L.fbx")):
        bpy.ops.object.select_all(action='DESELECT')
        ob.select_set(True); A.select_set(True)
        bpy.context.view_layer.objects.active=A
        bpy.ops.export_scene.fbx(filepath=path, use_selection=True,
            object_types={'ARMATURE','MESH'}, add_leaf_bones=False, bake_anim=False,
            global_scale=1.0, apply_scale_options='FBX_SCALE_NONE', mesh_smooth_type='FACE')
    log["exportado"]=True
print("###JSON###"+json.dumps(log)+"###END###")
