# revolve_lib.py - piezas de revolucion con bevel y normales EXACTAS (familia paleta / sensor / timbre).
# Un perfil (r, h, radio_filete, parte) en mm, con h hacia el FRENTE (+Z). Cada esquina con radio > 0 se reemplaza por
# un arco tangente; se gira alrededor de Z; cada vertice lleva la normal del perfil girada a su angulo (sombreado
# perfecto); cada tramo va al slot de material de su parte (la del punto donde arranca). Polos con abanico (el de
# arranque en orden inverso: si no, anillo de caras dadas vuelta).
import math

import bmesh
import bpy

ARC_STEP = math.radians(15.0)


def fillet_poly(P, arc_step=ARC_STEP):
    out = []
    n = len(P)
    for i in range(n):
        r, z, rf, part = P[i]
        if rf <= 0 or i == 0 or i == n - 1:
            out.append((r, z, part))
            continue
        a, b = P[i - 1], P[i + 1]
        d1 = (r - a[0], z - a[1])
        d2 = (b[0] - r, b[1] - z)
        l1, l2 = math.hypot(*d1), math.hypot(*d2)
        d1 = (d1[0] / l1, d1[1] / l1)
        d2 = (d2[0] / l2, d2[1] / l2)
        turn = math.atan2(d1[0] * d2[1] - d1[1] * d2[0], d1[0] * d2[0] + d1[1] * d2[1])
        if abs(turn) < 1e-6:
            out.append((r, z, part))
            continue
        # el tramo se reparte a medias si el vecino tambien tiene filete; si no, puede usar casi todo
        k1 = 0.49 if (i - 1 > 0 and P[i - 1][2] > 0) else 0.98
        k2 = 0.49 if (i + 1 < n - 1 and P[i + 1][2] > 0) else 0.98
        t = min(rf * math.tan(abs(turn) / 2), k1 * l1, k2 * l2)
        rr = t / math.tan(abs(turn) / 2)
        T1 = (r - d1[0] * t, z - d1[1] * t)
        sgn = 1.0 if turn > 0 else -1.0
        nrm = (-d1[1] * sgn, d1[0] * sgn)
        C = (T1[0] + nrm[0] * rr, T1[1] + nrm[1] * rr)
        a0 = math.atan2(T1[1] - C[1], T1[0] - C[0])
        steps = max(2, int(math.ceil(abs(turn) / arc_step * min(1.0, max(0.35, rr / 3.0)))))
        for s in range(steps + 1):
            ang = a0 + turn * s / steps
            out.append((C[0] + rr * math.cos(ang), C[1] + rr * math.sin(ang), part))
    return out


def normals2d(pts, closed=False):
    out = []
    n = len(pts)
    for i in range(n):
        a = pts[(i - 1) % n] if closed else pts[max(i - 1, 0)]
        b = pts[(i + 1) % n] if closed else pts[min(i + 1, n - 1)]
        tr, tz = b[0] - a[0], b[1] - a[1]
        m = math.hypot(tr, tz)
        out.append((tz / m, -tr / m))
    return out


def revolve(name, pts, parts, nseg, outward_sign=1.0, closed=False):
    """pts: (r, h, parte) en mm. closed=True: perfil cerrado (anillo, sin polos; el ultimo punto NO repite el primero).
    Devuelve (mesh, caras_dadas_vuelta). UV0: (angulo, largo de arco)."""
    nrm2 = normals2d(pts, closed)
    s = [0.0]
    for i in range(1, len(pts)):
        s.append(s[-1] + math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))
    if closed:
        s.append(s[-1] + math.hypot(pts[0][0] - pts[-1][0], pts[0][1] - pts[-1][1]))
    L = s[-1]
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    rows, vnorm = [], []
    for i, (r, z, _) in enumerate(pts):
        nr, nz = nrm2[i][0] * outward_sign, nrm2[i][1] * outward_sign
        if r < 1e-9:
            rows.append([bm.verts.new((0.0, 0.0, z / 1000.0))])
            vnorm.append((0.0, 0.0, 1.0 if nz > 0 else -1.0))
        else:
            row = []
            for j in range(nseg):
                th = 2 * math.pi * j / nseg
                row.append(bm.verts.new((r * math.cos(th) / 1000.0, r * math.sin(th) / 1000.0, z / 1000.0)))
                vnorm.append((nr * math.cos(th), nr * math.sin(th), nz))
            rows.append(row)
    for i in range(len(pts) if closed else len(pts) - 1):
        mi = parts.index(pts[i][2])
        A, B = rows[i], rows[(i + 1) % len(pts)]
        for j in range(nseg):
            j2 = (j + 1) % nseg
            u0, u1 = j / nseg, (j + 1) / nseg
            if len(A) == 1:
                vs, uv = (A[0], B[j2], B[j]), ((u0 + 0.5 / nseg, s[i] / L), (u1, s[i + 1] / L), (u0, s[i + 1] / L))
            elif len(B) == 1:
                vs, uv = (A[j], A[j2], B[0]), ((u0, s[i] / L), (u1, s[i] / L), (u0 + 0.5 / nseg, s[i + 1] / L))
            else:
                vs, uv = (A[j], A[j2], B[j2], B[j]), ((u0, s[i] / L), (u1, s[i] / L), (u1, s[i + 1] / L), (u0, s[i + 1] / L))
            f = bm.faces.new(vs)
            f.material_index = mi
            for lp, t in zip(f.loops, uv):
                lp[uvl].uv = t
    bm.normal_update()
    bm.verts.index_update()
    flips = sum(1 for f in bm.faces
                if sum(f.normal[k] * sum(vnorm[v.index][k] for v in f.verts) for k in range(3)) < 0)
    if flips > len(bm.faces) / 2:
        bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
        flips = len(bm.faces) - flips
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.normals_split_custom_set_from_vertices(vnorm)
    return me, flips


def checks(me, nparts):
    bm = bmesh.new()
    bm.from_mesh(me)
    r = {"tris": sum(len(f.verts) - 2 for f in bm.faces), "abiertas": sum(1 for e in bm.edges if not e.is_manifold),
         "degeneradas": sum(1 for f in bm.faces if f.calc_area() < 1e-10),
         "por_slot": [sum(1 for f in bm.faces if f.material_index == k) for k in range(nparts)]}
    bm.free()
    return r


def export_fbx(ob, path):
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, apply_unit_scale=True, global_scale=1.0,
                             apply_scale_options='FBX_SCALE_NONE', object_types={'MESH'}, mesh_smooth_type='FACE',
                             use_tspace=True, colors_type='NONE', add_leaf_bones=False, bake_anim=False, path_mode='STRIP')


# ---------------------------------------------------------------- barrido a lo largo de un rectangulo redondeado
def rrect_outline(a, b, rc, d, n_arc=10, step=4.0):
    """Contorno de un rectangulo redondeado (semiejes a, b, radio de esquina rc, en mm) desplazado d hacia afuera.
    Arranca ARRIBA AL CENTRO y va en sentido HORARIO visto de frente (+Z). Misma cantidad de puntos para cualquier d
    (los tramos rectos se reparten con la cuenta del contorno base). Devuelve [(x, y, nx, ny)] con la normal hacia afuera."""
    ex, ey = a - rc, b - rc                      # centros de las esquinas
    R = rc + d
    ns_top = max(1, int(round(ex / step)))
    ns_side = max(1, int(round(2 * ey / step)))
    pts = []

    def line(p0, p1, n, nx, ny, include_end=False):
        for k in range(n + (1 if include_end else 0)):
            t = k / n
            pts.append((p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t, nx, ny))

    def arc(cx, cy, a0, a1):
        for k in range(n_arc):
            t = math.radians(a0 + (a1 - a0) * k / n_arc)
            pts.append((cx + R * math.cos(t), cy + R * math.sin(t), math.cos(t), math.sin(t)))
    line((0.0, ey + R), (ex, ey + R), ns_top, 0.0, 1.0)
    arc(ex, ey, 90, 0)
    line((ex + R, ey), (ex + R, -ey), ns_side, 1.0, 0.0)
    arc(ex, -ey, 0, -90)
    line((ex, -ey - R), (-ex, -ey - R), 2 * ns_top, 0.0, -1.0)
    arc(-ex, -ey, -90, -180)
    line((-ex - R, -ey), (-ex - R, ey), ns_side, -1.0, 0.0)
    arc(-ex, ey, 180, 90)
    line((-ex, ey + R), (0.0, ey + R), ns_top, 0.0, 1.0)
    return pts


def sweep_rrect(name, prof, parts, a, b, rc, closed=False, caps=(), cap_parts=()):
    """Barre el perfil (d, h, parte) en mm a lo largo del rectangulo redondeado: cada punto del perfil es el contorno
    desplazado d a la altura h. Normales EXACTAS (normal del perfil combinada con la del contorno). caps: indices de
    fila ('first'/'last') que se cierran con una tapa plana (triangle_fill) con la parte de cap_parts."""
    nrm2 = normals2d(prof, closed)
    rows, vnorm = [], []
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    for i, (d, h, _) in enumerate(prof):
        nr, nz = nrm2[i]
        row = []
        for (x, y, nx, ny) in rrect_outline(a, b, rc, d):
            row.append(bm.verts.new((x / 1000.0, y / 1000.0, h / 1000.0)))
            vnorm.append((nr * nx, nr * ny, nz))
        rows.append(row)
    m = len(rows[0])
    for i in range(len(prof) if closed else len(prof) - 1):
        mi = parts.index(prof[i][2])
        A, B = rows[i], rows[(i + 1) % len(prof)]
        for j in range(m):
            j2 = (j + 1) % m
            # el contorno va en sentido HORARIO (al reves que revolve): orden invertido para que la cara mire afuera
            f = bm.faces.new((A[j], B[j], B[j2], A[j2]))
            f.material_index = mi
            for lp, t in zip(f.loops, ((j / m, i), (j / m, i + 1), ((j + 1) / m, i + 1), ((j + 1) / m, i))):
                lp[uvl].uv = (t[0], t[1] / max(len(prof) - 1, 1))
    bm.normal_update()
    for which, part in zip(caps, cap_parts):
        row = rows[0] if which == "first" else rows[-1]
        h = prof[0][1] if which == "first" else prof[-1][1]
        nz = nrm2[0][1] if which == "first" else nrm2[-1][1]
        es = [bm.edges.get((row[j], row[(j + 1) % m])) for j in range(m)]
        res = bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=es, normal=(0.0, 0.0, 1.0 if nz > 0 else -1.0))
        for f in res["geom"]:
            if isinstance(f, bmesh.types.BMFace):
                f.material_index = parts.index(part)
                f.normal_update()
                if f.normal.z * nz < 0:
                    f.normal_flip()
                for lp in f.loops:
                    lp[uvl].uv = (lp.vert.co.x * 10.0, lp.vert.co.y * 10.0)
    bm.normal_update()
    bm.verts.index_update()
    flips = sum(1 for f in bm.faces if len(f.verts) == 4 and
                sum(f.normal[k] * sum(vnorm[v.index][k] for v in f.verts) for k in range(3)) < 0)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    # normales por esquina: en las tapas la normal plana; en el resto la exacta del perfil
    cn = []
    for p in me.polygons:
        for li in p.loop_indices:
            vi = me.loops[li].vertex_index
            cn.append(tuple(p.normal) if len(p.vertices) == 3 else vnorm[vi])
    for p in me.polygons:
        p.use_smooth = True
    me.normals_split_custom_set(cn)
    return me, flips
