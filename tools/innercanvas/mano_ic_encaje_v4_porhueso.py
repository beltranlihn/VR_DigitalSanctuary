# mano_ic_encaje.py - pone la mano "Free Pack - VR Hands (Rigged)" (PolyOne Studio, CC-BY 4.0) sobre el esqueleto de la mano
# de Unreal (SK_MannequinsXR), para que ABP_MannequinsXR la anime sin tocar un nodo. Blender en segundo plano:
#   "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background --factory-startup --python mano_ic_encaje.py -- [--render] [--export]
#
# Metodo (corrige lo que fallo el 2026-09-03, ver blueprints/BP_VRPawn_SC.md):
#   - NO se toca el esqueleto de Unreal: la malla nueva se lleva a la pose de reposo de Manny.
#   - Por cada hueso de la mano nueva se arma un MARCO COMPLETO (x = direccion del segmento, y = normal de la palma proyectada,
#     z = x * y) y el de Manny igual; la matriz D = marcoManny * Escala(x) * marcoNuevo^-1 controla el GIRO del dedo (la causa
#     del fallo de septiembre) y ESTIRA el segmento (no lo traslada) para que cada nudillo caiga en el de Manny.
#   - Los vertices se mueven con skinning lineal a mano usando los PESOS ORIGINALES de la mano nueva (los del artista).
#   - Despues se renombran los grupos a los huesos de Manny y se cuelga del armature de Manny.
#   - --render: prueba de flexion (reposo, puno, apuntar) de la nueva al lado de la de Manny, ANTES de importar nada.
import bpy, json, sys, math, os
import numpy as np
from mathutils import Matrix, Vector

ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
NEW_FBX = r"C:/Users/beltr/Desktop/vr-hand/Hands VR.fbx"
MANNY_FBX = r"C:/Users/beltr/Desktop/vr-hand/SKM_MannyXR_right.FBX"
OUT = r"C:/Users/beltr/Desktop/vr-hand/"
S = 'r'
log = {}
bpy.ops.wm.read_factory_settings(use_empty=True)

# ---------------- Manny ----------------
bpy.ops.import_scene.fbx(filepath=MANNY_FBX)
A = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
MM = [o for o in bpy.data.objects if o.type == 'MESH'][0]
A.data.pose_position = 'REST'
bpy.context.view_layer.update()
mh = lambda n: (A.matrix_world @ A.data.bones[n].head_local).copy()

def manny_tip(bone):
    # punta = el vertice de Manny con peso > 0.5 en ese hueso mas lejos de su cabeza
    g = MM.vertex_groups.get(bone)
    h = mh(bone); best = None; bd = -1
    for v in MM.data.vertices:
        for ge in v.groups:
            if ge.group == g.index and ge.weight > 0.5:
                p = MM.matrix_world @ v.co
                d = (p - h).length
                if d > bd: bd, best = d, p
    return best.copy()

FING = ['thumb', 'index', 'middle', 'ring', 'pinky']
TJ = {}  # destino: f -> [cabeza01, cabeza02, cabeza03, punta]
for f in FING:
    TJ[f] = [mh('%s_0%d_%s' % (f, i, S)) for i in (1, 2, 3)] + [manny_tip('%s_03_%s' % (f, S))]
TW = mh('hand_' + S)

# ---------------- mano nueva ----------------
before = set(o.name for o in bpy.data.objects)
bpy.ops.import_scene.fbx(filepath=NEW_FBX)
new = [o for o in bpy.data.objects if o.name not in before]
AH = [o for o in new if o.type == 'ARMATURE'][0]
MH = [o for o in new if o.type == 'MESH'][0]
AH.data.pose_position = 'REST'
bpy.context.view_layer.update()
# la malla viene partida en las costuras de UV (vertices duplicados): se fusionan ANTES de moverla, si no cada copia se
# desplaza por su lado y la superficie queda con manchas y grietas (las "geometrias raras" que vio Beltran)
import bmesh
_bm = bmesh.new(); _bm.from_mesh(MH.data)
_n0 = len(_bm.verts)
bmesh.ops.remove_doubles(_bm, verts=_bm.verts, dist=0.0005)
_bm.to_mesh(MH.data); _bm.free(); MH.data.update()
log['fusionados'] = _n0 - len(MH.data.vertices)
nh = lambda n: (AH.matrix_world @ AH.data.bones[n].head_local).copy()
SRCN = {'thumb': 'Thumb', 'index': 'Index', 'middle': 'Middle', 'ring': 'Ring', 'pinky': 'Pinky'}

def src_tip(bone):
    # misma definicion que en Manny: el vertice mas lejano (piel de la yema), no el hueso final
    g = MH.vertex_groups.get(bone)
    h = nh(bone); best = None; bd = -1
    for v in MH.data.vertices:
        for ge in v.groups:
            if ge.group == g.index and ge.weight > 0.5:
                p = MH.matrix_world @ v.co
                d = (p - h).length
                if d > bd: bd, best = d, p
    return best.copy()

def src_joints(side):
    J = {f: [nh('J_%s_Hand%s%d' % (side, SRCN[f], i)) for i in (1, 2, 3)] + [src_tip('J_%s_Hand%s3' % (side, SRCN[f]))] for f in FING}
    return nh('J_%s_Hand' % side), J

def umeyama(P, Q):
    P = np.array(P); Q = np.array(Q)
    mp, mq = P.mean(0), Q.mean(0); Pc, Qc = P - mp, Q - mq
    U, Sv, Vt = np.linalg.svd(Pc.T @ Qc / len(P))
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    R = Vt.T @ np.diag([1, 1, d]) @ U.T
    return float(d)

# quiralidad: cual de las dos manos nuevas es una mano derecha como la de Manny
lm_t = [list(TW)] + [list(TJ[f][0]) for f in FING]
dets = {}
for side in ('Right', 'Left'):
    w, J = src_joints(side)
    dets[side] = umeyama([list(w)] + [list(J[f][0]) for f in FING], lm_t)
SIDE = 'Right' if dets['Right'] > 0 else 'Left'
log['det'] = dets; log['lado_usado'] = SIDE
SW, SJ = src_joints(SIDE)

def palm_n(w, J):
    return (J['index'][0] - w).cross(J['pinky'][0] - w).normalized()
n_s = palm_n(SW, SJ); n_t = palm_n(TW, TJ)

def frame(o, x, n):
    x = x.normalized(); y = (n - n.dot(x) * x).normalized(); z = x.cross(y)
    M = Matrix.Identity(4)
    for i in range(3):
        M[i][0], M[i][1], M[i][2], M[i][3] = x[i], y[i], z[i], o[i]
    return M

def scale_m(sx, sy=1.0, sz=1.0):
    M = Matrix.Identity(4); M[0][0], M[1][1], M[2][2] = sx, sy, sz
    return M

D = {}
# palma (v2, 2026-11-12 noche): AFIN por minimos cuadrados sobre la muneca y las 5 bases de los dedos (+ 2 puntos fuera del plano
# para fijar el espesor), asi la palma lleva cada base de dedo casi a la de Manny y la union palma-dedo no se tuerce
# (v1 = solo largo y ancho: Beltran vio el indice "corrido" y un pliegue raro entre pulgar e indice).
xs = SJ['middle'][0] - SW; xt = TJ['middle'][0] - TW
ws_ = (SJ['index'][0] - SJ['pinky'][0]).length; wt_ = (TJ['index'][0] - TJ['pinky'][0]).length
kx = xt.length / xs.length; kw = wt_ / ws_
P = [SW] + [SJ[f][0] for f in FING]; Q = [TW] + [TJ[f][0] for f in FING]
P += [SW + n_s * 0.02, SJ['middle'][0] + n_s * 0.02]; Q += [TW + n_t * 0.02 * kw, TJ['middle'][0] + n_t * 0.02 * kw]
Pm = np.array([list(p) + [1.0] for p in P]); Qm = np.array([list(q) for q in Q])
X, *_ = np.linalg.lstsq(Pm, Qm, rcond=None)   # 4x3
AF = Matrix.Identity(4)
for i in range(3):
    for j in range(3): AF[i][j] = X[j][i]
    AF[i][3] = X[3][i]
D['hand'] = AF
log['palma_k'] = [round(kx, 3), round(kw, 3)]
log['palma_resid_mm'] = [round((AF @ p - q).length * 1000, 1) for p, q in zip(P[:6], Q[:6])]
for f in FING:
    for i in range(3):
        hs, cs = SJ[f][i], SJ[f][i + 1]; ht, ct = TJ[f][i], TJ[f][i + 1]
        k = (ct - ht).length / (cs - hs).length
        D['%s%d' % (f, i + 1)] = frame(ht, ct - ht, n_t) @ scale_m(k) @ frame(hs, cs - hs, n_s).inverted()
log['k_dedos'] = {f: [round((TJ[f][i + 1] - TJ[f][i]).length / (SJ[f][i + 1] - SJ[f][i]).length, 3) for i in range(3)] for f in FING}

# grupos de la mano nueva -> clave de D y nombre de Manny
GMAP = {'Root': 'hand', 'J_%s' % SIDE: 'hand', 'J_%s_Hand' % SIDE: 'hand'}
MNAME = {'hand': 'hand_' + S}
for f in FING:
    for i in (1, 2, 3):
        GMAP['J_%s_Hand%s%d' % (SIDE, SRCN[f], i)] = '%s%d' % (f, i)
        MNAME['%s%d' % (f, i)] = '%s_0%d_%s' % (f, i, S)

# vertices de esta mano: los que tienen todo su peso en grupos de este lado (Root solo cuenta si no hay otro)
gname = {g.index: g.name for g in MH.vertex_groups}
keep, newpos, wts = [], {}, {}
other = 'J_%s' % ('Left' if SIDE == 'Right' else 'Right')
for v in MH.data.vertices:
    gs = [(gname[g.group], g.weight) for g in v.groups if g.weight > 1e-5]
    if any(n.startswith(other) for n, w in gs):
        continue
    acc = {}
    for n, w in gs:
        key = GMAP.get(n)
        if key: acc[key] = acc.get(key, 0.0) + w
    if not acc:
        continue
    tot = sum(acc.values())
    p = MH.matrix_world @ v.co
    q = Vector((0, 0, 0))
    for key, w in acc.items():
        q += (D[key] @ p) * (w / tot)
    keep.append(v.index); newpos[v.index] = q; wts[v.index] = {MNAME[k]: w / tot for k, w in acc.items()}
log['verts_mano'] = len(keep)

# suavizado del DESPLAZAMIENTO solo en las uniones (vertices con pesos mezclados): reparte la diferencia entre la palma y el dedo
keepset = set(keep)
nbr = {vi: set() for vi in keep}
for e in MH.data.edges:
    a, b = e.vertices
    if a in keepset and b in keepset: nbr[a].add(b); nbr[b].add(a)
orig = {vi: (MH.matrix_world @ MH.data.vertices[vi].co).copy() for vi in keep}
disp = {vi: newpos[vi] - orig[vi] for vi in keep}
mixed = [vi for vi in keep if max(wts[vi].values()) < 0.97]
# la zona de union crece un anillo para que el suavizado tenga de donde tirar
ring = set(mixed)
for vi in mixed: ring |= nbr[vi]
for it in range(12):
    nd = {}
    for vi in ring:
        if nbr[vi]:
            m = Vector((0, 0, 0))
            for u in nbr[vi]: m += disp[u]
            nd[vi] = disp[vi] * 0.5 + (m / len(nbr[vi])) * 0.5
    disp.update(nd)
for vi in keep: newpos[vi] = orig[vi] + disp[vi]
log['union_verts'] = len(ring)

# NORMALES PERSONALIZADAS: la malla es de pocos poligonos y el artista la suaviza con normales hechas a mano; sin ellas salen
# manchas (comprobado: la original sin sus normales se ve igual de manchada). Se rotan con la mezcla de las D de cada vertice.
def corner_normals(me):
    try:
        return [Vector(c.vector) for c in me.corner_normals]
    except Exception:
        return [Vector(l.normal) for l in me.loops]
CN = corner_normals(MH.data)
NW = MH.matrix_world.to_3x3().inverted().transposed()
DN = {k: m.to_3x3().inverted().transposed() for k, m in D.items()}
KEY = {v: k for k, v in MNAME.items()}
def loop_normal_world(li, vi):
    n = (NW @ CN[li]).normalized()
    q = Vector((0, 0, 0))
    for mname, w in wts[vi].items():
        q += (DN[KEY[mname]] @ n) * w
    return q.normalized()

# continuidad: cada articulacion destino tiene que salir igual desde el hueso padre y desde el hijo
cont = {}
for f in FING:
    errs = []
    for i in range(2):
        a = D['%s%d' % (f, i + 1)] @ SJ[f][i + 1]; b = D['%s%d' % (f, i + 2)] @ SJ[f][i + 1]
        errs.append(round((a - b).length * 1000, 2))
    cont[f] = errs
log['continuidad_mm'] = cont

# ---------------- armar la malla final sobre el armature de Manny ----------------
me = bpy.data.meshes.new('SKM_ICHand_R')
remap = {vi: k for k, vi in enumerate(keep)}
Minv = A.matrix_world.inverted()
verts = [list(Minv @ newpos[vi]) for vi in keep]
faces, uvs, lnor = [], [], []
uvl = MH.data.uv_layers.active
AT = A.matrix_world.to_3x3().transposed()   # normal mundo -> espacio del armature
for p in MH.data.polygons:
    if all(vi in remap for vi in p.vertices):
        faces.append([remap[vi] for vi in p.vertices])
        uvs.append([tuple(uvl.data[li].uv) for li in p.loop_indices] if uvl else None)
        for li, vi in zip(p.loop_indices, p.vertices):
            lnor.append((AT @ loop_normal_world(li, vi)).normalized())
me.from_pydata(verts, [], faces)
me.update()
me.normals_split_custom_set([tuple(n) for n in lnor])
log['normales_custom'] = len(lnor)
if uvl:
    ul = me.uv_layers.new(name='UVMap')
    li = 0
    for pi, p in enumerate(me.polygons):
        for j, l in enumerate(p.loop_indices):
            ul.data[l].uv = uvs[pi][j]
for p in me.polygons: p.use_smooth = True
mat = bpy.data.materials.new('M_ICHand'); me.materials.append(mat)
R = bpy.data.objects.new('SKM_ICHand_R', me); bpy.context.collection.objects.link(R)
R.parent = A; R.matrix_parent_inverse = Matrix.Identity(4); R.matrix_world = A.matrix_world.copy()
groups = {}
for vi in keep:
    for n, w in wts[vi].items():
        if n not in groups: groups[n] = R.vertex_groups.new(name=n)
        groups[n].add([remap[vi]], w, 'REPLACE')
mod = R.modifiers.new('Armature', 'ARMATURE'); mod.object = A
log['tris'] = sum(len(p.vertices) - 2 for p in me.polygons)

bpy.data.objects.remove(AH, do_unlink=True); bpy.data.objects.remove(MH, do_unlink=True)

# izquierda = espejo exacto en X del espacio del armature (hand_l y hand_r son espejos en X)
L = R.copy(); L.data = R.data.copy(); bpy.context.collection.objects.link(L)
L.name = 'SKM_ICHand_L'; L.data.name = 'SKM_ICHand_L'
# normales de esquina de la derecha por (poligono, vertice), espejadas en X; flip_normals no maneja normales personalizadas
_rcn = corner_normals(R.data)
_rmap = {}
for p in R.data.polygons:
    for li, vi in zip(p.loop_indices, p.vertices):
        n = _rcn[li]; _rmap[(p.index, vi)] = (-n.x, n.y, n.z)
for v in L.data.vertices: v.co.x = -v.co.x
L.data.flip_normals()
L.data.update()
_ln = []
for p in L.data.polygons:
    for vi in p.vertices:
        _ln.append(_rmap[(p.index, vi)])
L.data.normals_split_custom_set(_ln)
for g in L.vertex_groups:
    if g.name.endswith('_r'): g.name = g.name[:-2] + '_l'
L.parent = A; L.matrix_parent_inverse = Matrix.Identity(4); L.matrix_world = A.matrix_world.copy()
for m in L.modifiers:
    if m.type == 'ARMATURE': m.object = A
mirror_err = max((mh(b.replace('_r', '_l')) - Vector((-mh(b).x, mh(b).y, mh(b).z))).length for b in ['hand_r', 'index_01_r', 'thumb_03_r']) if False else None

# ---------------- prueba de flexion ----------------
def palm_side():
    s = (TJ['thumb'][3] - TW).dot(n_t)
    return n_t * (1 if s > 0 else -1)

def pose(kind):
    A.data.pose_position = 'POSE'
    bpy.context.view_layer.objects.active = A
    bpy.ops.object.mode_set(mode='POSE')
    for pb in A.pose.bones: pb.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    ps = palm_side()
    ang = {'rest': {}, 'fist': {f: [70, 85, 60] for f in ['index', 'middle', 'ring', 'pinky']},
           'point': {f: [80, 90, 60] for f in ['middle', 'ring', 'pinky']}}[kind]
    if kind == 'fist': ang['thumb'] = [15, 40, 40]
    if kind == 'point': ang['thumb'] = [15, 40, 40]
    for f, a3 in ang.items():
        for i in range(3):
            pb = A.pose.bones['%s_0%d_%s' % (f, i + 1, S)]
            h = (A.matrix_world @ pb.head).copy()
            nxt = A.pose.bones['%s_0%d_%s' % (f, i + 2, S)] if i < 2 else None
            t = (A.matrix_world @ nxt.head) if nxt else (A.matrix_world @ pb.tail)
            x = (t - h).normalized()
            axis = x.cross(ps).normalized()
            Rw = Matrix.Translation(h) @ Matrix.Rotation(math.radians(a3[i]), 4, axis) @ Matrix.Translation(-h)
            pb.matrix = A.matrix_world.inverted() @ Rw @ A.matrix_world @ pb.matrix
            bpy.context.view_layer.update()
    bpy.ops.object.mode_set(mode='OBJECT')

def render_set(tag):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'SINGLE'
    sc.render.resolution_x = 520; sc.render.resolution_y = 520
    sc.world = bpy.data.worlds.new('w') if not sc.world else sc.world
    cam = bpy.data.objects.get('CAM')
    if not cam:
        cam = bpy.data.objects.new('CAM', bpy.data.cameras.new('CAM')); sc.collection.objects.link(cam); sc.camera = cam
        cam.data.lens = 50
    c = TW + (TJ['middle'][0] - TW) * 0.9
    side = (TJ['index'][0] - TJ['pinky'][0]).normalized()
    imgs = []
    for kind in ('rest', 'fist', 'point'):
        pose(kind)
        for vname, dirv in (('lado', side), ('palma', palm_side())):
            cam.location = c + dirv * 0.45
            cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
            for who in ('nueva', 'manny'):
                R.hide_render = who != 'nueva'; L.hide_render = True; MM.hide_render = who != 'manny'
                path = OUT + 'flex_%s_%s_%s.png' % (kind, vname, who)
                sc.render.filepath = path
                bpy.ops.render.render(write_still=True)
                imgs.append(path)
    A.data.pose_position = 'REST'
    return imgs

if '--render' in ARGS:
    log['render'] = render_set('a')

if '--export' in ARGS:
    MM.hide_set(False)
    bpy.data.objects.remove(MM, do_unlink=True)
    A.data.pose_position = 'REST'
    for pb in A.pose.bones: pb.matrix_basis = Matrix.Identity(4)
    for ob, path in ((R, OUT + 'SKM_ICHand_R.fbx'), (L, OUT + 'SKM_ICHand_L.fbx')):
        bpy.ops.object.select_all(action='DESELECT')
        ob.select_set(True); A.select_set(True)
        bpy.context.view_layer.objects.active = A
        bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False,
                                 bake_anim=False, global_scale=1.0, apply_scale_options='FBX_SCALE_NONE', mesh_smooth_type='FACE')
    log['exportado'] = True
    bpy.ops.wm.save_as_mainfile(filepath=OUT + 'mano_ic.blend')

print('###JSON###' + json.dumps(log) + '###END###')
