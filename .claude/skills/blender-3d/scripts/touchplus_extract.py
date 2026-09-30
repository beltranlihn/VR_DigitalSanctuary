# touchplus_extract.py - paso 1 del mando de la obra (3a version, 2026-09-29): toma el Meta Quest Touch Plus OFICIAL
# (paquete de arte de Meta, la licencia permite usarlo para representar el producto en la experiencia VR) y exporta
# lo que necesita el paso 2 (touchplus_sdf.py) para rehacerlo como UNA cascara continua y lisa:
#   - los paneles que forman el cuerpo (sin botones A/B/Meta ni stick; CON la pieza del boton de grip, que queda
#     fundida al mango), en triangulos, con sus normales suaves por esquina (las que dibujo el artista)
#   - los agujeros a tapar (4 de la tapa, la ranura del gatillo, el ojal de la correa) con su anillo de vecinos
#   - el gatillo aparte, su abertura, y el hueso del gatillo (pivote y ejes de la bisagra)
#   - el contorno de la tapa (parting line entre la tapa negra y el cuerpo blanco del original)
# Por que no remallar por voxeles ni modelar a mano: la malla oficial son 25 paneles SEPARADOS (845 aristas de borde,
# no se sueldan a 0,01 mm) y low-poly (5.609 tris) con un mapa de normales; el remallado directo la deformaba y el
# modelado desde cero no se parecia. El paso 2 funde los paneles por campo de distancia sobre su superficie suavizada.
# Uso: blender --background --python touchplus_extract.py
import json
import os
import traceback
from collections import Counter

import bmesh
import bpy
import numpy as np
from mathutils import Vector

SRC = r"C:/Users/beltr/Downloads/oculus-controller-art-v1.8/Meta Quest Touch Plus"
AQUI = os.path.dirname(os.path.abspath(__file__))
D = os.path.abspath(os.path.join(AQUI, "..", "..", "..", "..", "VR_Test", "Saved", "ClaudeScripts", "QuestController"))
DROP = ("b_button_a", "b_button_b", "right_b_button_oculus", "right_b_thumbstick")
TRIGGER = "right_b_trigger_front"


def comps(faces):
    fs = set(faces)
    seen, out = set(), []
    for f in faces:
        if f in seen:
            continue
        stack, cur = [f], []
        seen.add(f)
        while stack:
            g = stack.pop()
            cur.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h in fs and h not in seen:
                        seen.add(h)
                        stack.append(h)
        out.append(cur)
    return out


def loops_of(faces):
    """Aristas de borde del conjunto -> lazos ordenados de vertices."""
    fs = set(faces)
    bnd = {e for f in faces for e in f.edges if sum(1 for g in e.link_faces if g in fs) == 1}
    out = []
    while bnd:
        e0 = bnd.pop()
        vs = [e0.verts[0], e0.verts[1]]
        es = [e0]
        while True:
            nxt = [e for e in vs[-1].link_edges if e in bnd]
            if not nxt:
                break
            e = nxt[0]
            bnd.discard(e)
            es.append(e)
            w = e.other_vert(vs[-1])
            if w == vs[0]:
                break
            vs.append(w)
        out.append((vs, es))
    return out


def ring(loop_vs, faces, depth):
    fs = set(faces)
    seen = set(loop_vs)
    front = list(loop_vs)
    for _ in range(depth):
        nf = []
        for v in front:
            for e in v.link_edges:
                if not any(f in fs for f in e.link_faces):
                    continue
                w = e.other_vert(v)
                if w not in seen:
                    seen.add(w)
                    nf.append(w)
        front = nf
    return [v for v in seen if v not in set(loop_vs)]


def tri_arrays(bm, faces, cnl, cl):
    b2 = bm.copy()
    keep = {f.index for f in faces}
    b2.faces.ensure_lookup_table()
    bmesh.ops.delete(b2, geom=[f for f in b2.faces if f.index not in keep], context='FACES')
    bmesh.ops.triangulate(b2, faces=b2.faces[:], quad_method='BEAUTY', ngon_method='BEAUTY')
    cn2 = b2.loops.layers.float_vector.get("cn")
    c2 = b2.faces.layers.int.get("comp")
    P = np.array([[l.vert.co[:] for l in f.loops] for f in b2.faces], np.float64)
    N = np.array([[l[cn2][:] for l in f.loops] for f in b2.faces], np.float64)
    C = np.array([f[c2] for f in b2.faces], np.int32)
    b2.free()
    return P, N, C


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.fbx_import(filepath=os.path.join(SRC, "models", "MetaQuestTouchPlus_Right.fbx"))
    arm = [x for x in bpy.data.objects if x.type == 'ARMATURE'][0]
    o = [x for x in bpy.data.objects if x.type == 'MESH' and "controller" in x.name.lower() and "battery" not in x.name.lower()][0]
    for m in list(o.modifiers):
        o.modifiers.remove(m)
    me = o.data
    mw = o.matrix_world.copy()
    rot = mw.to_3x3().normalized()
    cn = np.empty(len(me.loops) * 3, np.float32)
    me.corner_normals.foreach_get("vector", cn)
    cn = cn.reshape(-1, 3)
    R = np.array(rot, np.float64)
    cnw = cn @ R.T
    cnw /= np.linalg.norm(cnw, axis=1, keepdims=True)
    # esquinas vs cara: si todas coinciden la malla vino plana (sin normales del artista)
    fnw = np.array([p.normal[:] for p in me.polygons]) @ R.T
    lp_face = np.repeat(np.arange(len(me.polygons)), [p.loop_total for p in me.polygons])
    ang = np.degrees(np.arccos(np.clip(np.sum(cnw * fnw[lp_face], 1), -1, 1)))
    print("NORMALES esquina-vs-cara deg: media %.2f p95 %.2f" % (ang.mean(), np.percentile(ang, 95)))
    img = bpy.data.images.load(os.path.join(SRC, "textures", "MetaQuestTouchPlus_right_BaseColor.png"))
    W, H = img.size
    px = np.empty(W * H * 4, np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(H, W, 4)
    names = {g.index: g.name for g in o.vertex_groups}
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.transform(mw)
    bm.normal_update()
    bm.faces.ensure_lookup_table()
    dl = bm.verts.layers.deform.active
    uvl = bm.loops.layers.uv[0]
    cnl = bm.loops.layers.float_vector.new("cn")
    cl = bm.faces.layers.int.new("comp")
    for f in bm.faces:
        ls = me.polygons[f.index].loop_start
        for k, l in enumerate(f.loops):
            l[cnl] = Vector(cnw[ls + k])
    cs = sorted(comps(list(bm.faces)), key=len, reverse=True)
    grp, lum = {}, {}
    for k, c in enumerate(cs):
        vg = Counter()
        for f in c:
            f[cl] = k
            for v in f.verts:
                if v[dl]:
                    vg[names[max(v[dl].items(), key=lambda t: t[1])[0]]] += 1
        grp[k] = vg.most_common(1)[0][0]
        f = c[0]
        u = sum(l[uvl].uv.x for l in f.loops) / len(f.loops)
        w = sum(l[uvl].uv.y for l in f.loops) / len(f.loops)
        p = px[min(H - 1, max(0, int(w % 1.0 * H))), min(W - 1, max(0, int(u % 1.0 * W)))]
        lum[k] = float(0.3 * p[0] + 0.59 * p[1] + 0.11 * p[2])
    sizes = [len(c) for c in cs]
    assert sizes[:3] == [610, 545, 422] and sizes[12] == 32 and sizes[14] == 21, sizes
    # orientacion (solo informe): los paneles grandes miran afuera; las tiras chicas las orienta el paso 2 por vecindad
    allv = [v.co for v in bm.verts]
    C = sum(allv, Vector()) / len(allv)
    for k, c in enumerate(cs):
        cc = sum((f.calc_center_median() for f in c), Vector()) / len(c)
        ref = C if grp[k] != TRIGGER else cc
        out = sum(l[cnl].dot(l.vert.co - ref) for f in c for l in f.loops)
        geo = sum(l[cnl].dot(f.normal) for f in c for l in f.loops) / sum(len(f.loops) for f in c)
        print("PANEL", k, grp[k][-14:], len(c), "lum %.2f" % lum[k], "afuera %.4f" % out, "esq_vs_cara %.2f" % geo)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bm.faces.ensure_lookup_table()
    # comp 14 = bolsillo oscuro de la ranura del gatillo: se conserva (sella la ranura; el gatillo entra ahi)
    body = [f for f in bm.faces if grp[f[cl]] not in DROP and grp[f[cl]] != TRIGGER]
    trig = [f for f in bm.faces if grp[f[cl]] == TRIGGER]
    fills, cap_outline = [], None
    for vs, es in loops_of(body):
        adj = Counter(f[cl] for e in es for f in e.link_faces if f in set(body))
        cen = sum((v.co for v in vs), Vector()) / len(vs)
        rad = max((v.co - cen).length for v in vs)
        a = set(adj)
        kind = None
        if a == {1} and rad < 0.010:
            kind = "tapa"
        elif a == {1}:
            cap_outline = [v.co[:] for v in vs]
        elif a == {0} and len(es) == 32 and rad < 0.025:
            kind = "ranura"
        elif a == {6}:
            kind = "grip"          # contorno del boton de grip: el paso 2 lo reemplaza por la superficie del mango
        elif a == {10} and rad < 0.006:
            kind = "ojal"          # agujero de la correa (el paso 2 lo cierra en abanico)
        if kind:
            nrm = sum((f.normal for e in es for f in e.link_faces if f in set(body)), Vector()).normalized()
            rg = ring(vs, body, 3)
            fills.append({"kind": kind, "loop": [v.co[:] for v in vs], "ring": [v.co[:] for v in rg], "hint": nrm[:]})
            print("RELLENO", kind, len(vs), "rad_cm %.2f" % (rad * 100), "anillo", len(rg))
    for vs, es in loops_of(trig):
        nrm = sum((f.normal for e in es for f in e.link_faces), Vector()).normalized()
        rg = ring(vs, trig, 3)
        fills.append({"kind": "gatillo", "loop": [v.co[:] for v in vs], "ring": [v.co[:] for v in rg], "hint": nrm[:]})
        print("RELLENO gatillo", len(vs), "anillo", len(rg))
    Pb, Nb, Cb = tri_arrays(bm, body, cnl, cl)
    Pt, Nt, Ct = tri_arrays(bm, trig, cnl, cl)
    # hueso del gatillo: pivote y ejes de la bisagra (en el mundo, metros)
    bones = {}
    for b in arm.data.bones:
        m = arm.matrix_world @ b.matrix_local
        bones[b.name] = {"head": (arm.matrix_world @ b.head_local)[:], "tail": (arm.matrix_world @ b.tail_local)[:],
                         "x": m.to_3x3().normalized().col[0][:], "y": m.to_3x3().normalized().col[1][:],
                         "z": m.to_3x3().normalized().col[2][:]}
    tb = [k for k in bones if k.endswith("trigger_front")]
    print("HUESO", tb, {k: [round(x * 100, 2) for x in bones[k]["head"]] for k in tb})
    laser = [x for x in bpy.data.objects if x.name.endswith("laser_begin")]
    np.savez(os.path.join(D, "tp_src.npz"), Pb=Pb, Nb=Nb, Cb=Cb, Pt=Pt, Nt=Nt, Ct=Ct)
    with open(os.path.join(D, "tp_src.json"), "w") as fh:
        json.dump({"fills": fills, "cap_outline": cap_outline, "bones": bones, "lum": lum, "grp": grp,
                   "laser": laser[0].matrix_world.translation[:] if laser else None}, fh)
    print("EXTRACT_OK cuerpo_tris", len(Pb), "gatillo_tris", len(Pt), "rellenos", len(fills),
          "contorno_tapa", len(cap_outline) if cap_outline else None)


try:
    main()
except BaseException as e:
    print("EXTRACT_FALLO", type(e).__name__, e)
    traceback.print_exc()
