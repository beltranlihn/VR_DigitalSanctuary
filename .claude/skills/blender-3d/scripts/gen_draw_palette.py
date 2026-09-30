# gen_draw_palette.py - la PALETA de la etapa de dibujo (pedido de Beltran 2026-09-29, plano Escritorio/Drawing1-Model.pdf).
# Paleta redonda de hormigon suave pulido (calido, poco saturado) con una RANURA-ANILLO hundida e iluminada,
# 4 botones de COLOR a la derecha y 4 de PINCEL a la izquierda (cunas encastradas en bolsillos), UNDO/REDO flotando a
# la izquierda, SLIDER de grosor en arco flotando abajo con su bolita, y al centro un CASQUETE de esfera que muestra el
# color y la textura del pincel. Todo con bevel suave. Los botones seleccionados suben KEY_SEL_UP.
#
# Medidas: el plano no trae cotas -> se midio en pixeles (vista en planta, centro (1032, 787), radio exterior 451,5 px)
# y se escala a R. Todas las constantes estan en PIXELES DEL PLANO; u() las pasa a metros.
# Mallas (todas con el ORIGEN EN EL CENTRO DE LA PALETA: colocar = rotar en Z; el slider mueve la bolita girandola):
#   SM_DrawPalette_Base_SC     cuerpo + ranura (slot 1 = luz) + bolsillos
#   SM_DrawPalette_Key_SC      una cuna (centrada en 0 grados); las 8 son esta malla girada (+-20, +-60, 180+-20, 180+-60)
#   SM_DrawPalette_SideKey_SC  undo (centrado en 166 grados); redo = misma malla girada +28 grados (194)
#   SM_DrawPalette_Slider_SC   tubo en arco 227..313 grados
#   SM_DrawPalette_Knob_SC     bolita del slider (en 270 grados)
#   SM_DrawPalette_Swatch_SC   casquete central (UV0 plana 0..1 para el color/textura del pincel)
# Ejes: la paleta acostada en XY con la cara hacia +Z; +X = derecha del plano (colores), +Y = arriba del plano.
# ⚠ Al importar en Unreal la Y se espeja (Blender +Y -> Unreal -Y): el BP que la monte decide la orientacion.
# Uso: blender --background --python gen_draw_palette.py [-- render]
import math
import os
import sys
import traceback

import bmesh
import bpy

R = 0.20              # radio exterior en metros (paleta de 40 cm, pedido de Beltran)
PX = 451.5            # radio exterior en pixeles del plano


def u(px):
    return px / PX * R


# --- cuerpo (pixeles; z = 0 en el borde superior) ---
R_OUT = 451.5
GROOVE_OUT = 418.5
GROOVE_IN = 391.5
Z_PLATE = -20.0
Z_GROOVE = -38.0
Z_BOTTOM = -71.0
CAP_R = 92.0
CAP_POCKET_R = 95.0   # 0,6 mm de luz alrededor del casquete
Z_CAP_POCKET = -38.0
CAP_TOP = -15.0       # el casquete asoma 5 px sobre el plato
# --- cunas ---
KEY_R1, KEY_R2 = 128.0, 335.0
KEY_HALF = 12.5       # grados (25 de ancho, juntas de 15)
KEY_FIL = 22.0
KEY_ROUND = 12.0      # radio del canto redondeado de arriba (2,4 mm)
KEY_CLEAR = 6.0       # luz del bolsillo alrededor de la cuna (1,2 mm)
Z_KEY_POCKET = -35.0
KEY_SEL_UP = 15.0     # cuanto sube una seleccionada (3 mm)
KEY_ANGLES = {"Color": (60.0, 20.0, -20.0, -60.0), "Brush": (120.0, 160.0, 200.0, 240.0)}
# --- flotantes ---
SIDE_R1, SIDE_R2 = 484.0, 567.0
SIDE_CENTER, SIDE_HALF, SIDE_FIL = 166.0, 12.0, 25.0
SIDE_H, SIDE_ROUND = 33.0, 12.0
Z_FLOAT = -38.5       # centro en altura de lo que flota (el del undo en el corte)
SLIDER_R, SLIDER_TUBE = 490.5, 7.5
SLIDER_A0, SLIDER_A1 = 227.0, 313.0
KNOB_R, KNOB_ANGLE = 19.0, 270.0
SLIDER_W, SLIDER_T = 15.0, 6.0   # banda PLANA translucida: ancho y espesor (px)
KNOB_T = 10.0                    # la bolita es un DISCO plano (radio KNOB_R); el BP la escala: izquierda chica, derecha grande
LABEL_W, LABEL_H = 200.0, 50.0   # cuadro de la etiqueta UNDO/REDO en la pieza lateral (UV1 "LabelUV"; textura de texto)
ICON_PX = 120.0                  # lado del cuadro del icono de pincel en la cuna (UV1 "IconUV"; el icono = textura T_Ico_*)
FONT = r"C:/Users/beltr/AppData/Local/Microsoft/Windows/Fonts/Avenir Book.ttf"
BRUSHES = ("TaperedMarker", "OilPaint", "Light", "WetPaint")   # BrushIds [0, 5, 3, 6] de BP_TBPalette (iconos T_Ico_0/5/3/6)

# densidad de los contornos: a 18 cm, puntos cada 2-3 mm. Mas denso (0,4-1 mm) = 'orejas' de 3 puntos casi colineales
# al triangular las caras planas (0,004 mm2): Unreal las descarta y avisa tangentes degeneradas.
N_LINE, N_FIL, N_ARC_OUT, N_ARC_IN = 4, 6, 12, 6
SPIN = 160
NOMBRE = "SM_DrawPalette"
AQUI = os.path.dirname(os.path.abspath(__file__))
DESTINO = os.path.abspath(os.path.join(AQUI, "..", "..", "..", "..", "VR_Test", "Saved", "ClaudeScripts", "DrawPalette"))


# ---------------------------------------------------------------- utilidades 2D
def arc(c, r, a0, a1, n):
    return [(c[0] + r * math.cos(a0 + (a1 - a0) * k / n), c[1] + r * math.sin(a0 + (a1 - a0) * k / n)) for k in range(n)]


def short(a0, a1):
    d = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
    return a0, a0 + d


def wedge(ac_deg, half_deg, R1, R2, off, fil, n_line=N_LINE):
    """Contorno CCW de una cuna: sector de anillo R1..R2 entre dos lados PARALELOS a los radios en ac +- half, corridos
    'off' hacia adentro (off < 0 = hacia afuera: bolsillo), esquinas con filete tangente 'fil'. Unidades libres.
    Misma cantidad de puntos para cualquier (R1, R2, off, fil) -> los anillos concentricos se unen en quads."""
    ac, hh = math.radians(ac_deg), math.radians(half_deg)
    a0, a1 = ac - hh, ac + hh
    d0, d1 = (math.cos(a0), math.sin(a0)), (math.cos(a1), math.sin(a1))
    n0 = (-d0[1], d0[0])
    n1 = (d1[1], -d1[0])
    h = off + fil

    def center(d, n, Rc):
        t = math.sqrt(max(Rc * Rc - h * h, 1e-12))
        return (t * d[0] + h * n[0], t * d[1] + h * n[1])
    O0, O1 = center(d0, n0, R2 - fil), center(d1, n1, R2 - fil)
    I0, I1 = center(d0, n0, R1 + fil), center(d1, n1, R1 + fil)

    def on_line(c, n):
        return (c[0] - fil * n[0], c[1] - fil * n[1])

    def on_circ(c, Rr):
        m = math.hypot(*c)
        return (c[0] * Rr / m, c[1] * Rr / m)

    def ang(c, p):
        return math.atan2(p[1] - c[1], p[0] - c[0])

    def seg(p, q, n):
        return [(p[0] + (q[0] - p[0]) * k / n, p[1] + (q[1] - p[1]) * k / n) for k in range(n)]
    pts = []
    pI0L, pO0L = on_line(I0, n0), on_line(O0, n0)
    pts += seg(pI0L, pO0L, n_line)
    pO0C = on_circ(O0, R2)
    pts += arc(O0, fil, *short(ang(O0, pO0L), ang(O0, pO0C)), N_FIL)
    pO1C = on_circ(O1, R2)
    pts += arc((0, 0), R2, *short(math.atan2(pO0C[1], pO0C[0]), math.atan2(pO1C[1], pO1C[0])), N_ARC_OUT)
    pO1L = on_line(O1, n1)
    pts += arc(O1, fil, *short(ang(O1, pO1C), ang(O1, pO1L)), N_FIL)
    pI1L = on_line(I1, n1)
    pts += seg(pO1L, pI1L, n_line)
    pI1C = on_circ(I1, R1)
    pts += arc(I1, fil, *short(ang(I1, pI1L), ang(I1, pI1C)), N_FIL)
    pI0C = on_circ(I0, R1)
    pts += arc((0, 0), R1, *short(math.atan2(pI1C[1], pI1C[0]), math.atan2(pI0C[1], pI0C[0])), N_ARC_IN)
    pts += arc(I0, fil, *short(ang(I0, pI0C), ang(I0, pI0L)), N_FIL)
    area = sum(pts[k][0] * pts[(k + 1) % len(pts)][1] - pts[(k + 1) % len(pts)][0] * pts[k][1] for k in range(len(pts)))
    return pts if area > 0 else pts[::-1]


def filleted(P, segs=5):
    """Perfil cerrado (r, z, radio) -> cada esquina de 90 grados reemplazada por un arco."""
    out = []
    n = len(P)
    for i in range(n):
        px, pz, rf = P[i]
        if rf <= 0:
            out.append((px, pz))
            continue
        ax, az, _ = P[i - 1]
        bx, bz, _ = P[(i + 1) % n]
        l1, l2 = math.hypot(px - ax, pz - az), math.hypot(bx - px, bz - pz)
        d1 = ((px - ax) / l1, (pz - az) / l1)
        d2 = ((bx - px) / l2, (bz - pz) / l2)
        cx, cz = px - d1[0] * rf + d2[0] * rf, pz - d1[1] * rf + d2[1] * rf
        for s in range(segs + 1):
            a = 0.5 * math.pi * s / segs
            out.append((cx + rf * (-d2[0] * math.cos(a) + d1[0] * math.sin(a)),
                        cz + rf * (-d2[1] * math.cos(a) + d1[1] * math.sin(a))))
    return out


# ---------------------------------------------------------------- mallas
def rings_mesh(name, rings, cap_top=True, cap_bottom=True):
    """rings = [(pts_2d_en_px, z_px)] de abajo hacia arriba, todos con la misma cantidad de puntos -> quads.
    Las tapas se cierran con POKE (abanico al centroide: sin triangulos de area cero por puntos colineales)."""
    bm = bmesh.new()
    vs = [[bm.verts.new((u(x), u(y), u(z))) for x, y in pts] for pts, z in rings]
    n = len(vs[0])
    assert all(len(v) == n for v in vs), [len(v) for v in vs]
    for a, b in zip(vs[:-1], vs[1:]):
        for j in range(n):
            bm.faces.new((a[j], a[(j + 1) % n], b[(j + 1) % n], b[j]))
    # tapas: triangle_fill (scanfill: cóncavos y arcos bien). 🔴 poke al centroide ROMPE la banda del slider (el
    # centroide de un arco cae FUERA de la forma) y beautify_fill puede dar vuelta triangulos en contornos concavos.
    for ring, want, on in ((vs[0], -1.0, cap_bottom), (vs[-1], 1.0, cap_top)):
        if not on:
            continue
        es = [bm.edges.get((ring[j], ring[(j + 1) % n])) for j in range(n)]
        bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=es, normal=(0.0, 0.0, want))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me


def offset_rings(fn, z_levels_px, round_px, top_offsets_px, z_top, bottom=None):
    """Anillos de una pieza extruida con canto superior redondeado (cuarto de circulo radio round_px).
    fn(o) = contorno desplazado o px hacia adentro. bottom = (z_bottom, round_bottom_px | 0)."""
    rings = []
    zb, rb = bottom
    if rb > 0:
        for o in reversed(top_offsets_px):
            rings.append((fn(rb + o), zb))
        for k in range(5):
            th = 0.5 * math.pi * (1 - k / 4)
            rings.append((fn(rb * (1 - math.cos(th))), zb + rb - rb * math.sin(th)))
    else:
        rings.append((fn(0.0), zb))
    for k in range(5):
        th = 0.5 * math.pi * k / 4
        rings.append((fn(round_px * (1 - math.cos(th))), z_top - round_px + round_px * math.sin(th)))
    for o in top_offsets_px:
        rings.append((fn(round_px + o), z_top))
    return rings


def key_rings(ang, z_top):
    fn = lambda o: wedge(ang, KEY_HALF, KEY_R1 + o, KEY_R2 - o, o, max(KEY_FIL - o, 14.0))
    # 🔴 en la punta angosta la cuna solo admite desplazar ~17 px ((R1+o)*sin(12,5) > o + filete): mas adentro los lados
    # se CRUZAN (anillo autointersecado = rayas negras en render). Canto 12 + un anillo de 3 y se cierra la tapa.
    return offset_rings(fn, None, KEY_ROUND, (3.0,), z_top, bottom=(Z_KEY_POCKET, 0.0))


def side_rings(center=SIDE_CENTER):
    fn = lambda o: wedge(center, SIDE_HALF, SIDE_R1 + o, SIDE_R2 - o, o, max(SIDE_FIL - o, 14.0))
    zt, zb = Z_FLOAT + SIDE_H / 2, Z_FLOAT - SIDE_H / 2
    return offset_rings(fn, None, SIDE_ROUND, (8.0, 18.0), zt, bottom=(zb, SIDE_ROUND))


def band(o, n_arc=64, n_cap=10):
    """Contorno CCW de la banda del slider desplazado o px hacia adentro: arco exterior, punta semicircular,
    arco interior, punta semicircular. (wedge() no sirve: en una banda de 15 px y 86 grados se deformaba.)"""
    a0, a1 = math.radians(SLIDER_A0), math.radians(SLIDER_A1)
    hw = SLIDER_W / 2 - o
    pts = []
    for k in range(n_arc):
        a = a0 + (a1 - a0) * k / n_arc
        pts.append(((SLIDER_R + hw) * math.cos(a), (SLIDER_R + hw) * math.sin(a)))
    for end, sgn in ((a1, 1), (a0, -1)):
        cx, cy = SLIDER_R * math.cos(end), SLIDER_R * math.sin(end)
        rx, ry = math.cos(end), math.sin(end)          # radial
        tx, ty = -math.sin(end) * sgn, math.cos(end) * sgn   # hacia afuera de la punta
        for k in range(n_cap):
            ph = math.pi * k / n_cap if sgn == 1 else math.pi * (1 - k / n_cap)   # a1: afuera->adentro; a0: adentro->afuera
            pts.append((cx + hw * (rx * math.cos(ph) + tx * math.sin(ph)), cy + hw * (ry * math.cos(ph) + ty * math.sin(ph))))
        if sgn == 1:
            for k in range(n_arc):
                a = a1 - (a1 - a0) * k / n_arc
                pts.append(((SLIDER_R - hw) * math.cos(a), (SLIDER_R - hw) * math.sin(a)))
    area = sum(pts[k][0] * pts[(k + 1) % len(pts)][1] - pts[(k + 1) % len(pts)][0] * pts[k][1] for k in range(len(pts)))
    return pts if area > 0 else pts[::-1]


def slider_mesh():
    """Banda PLANA en arco (translucida en el material), puntas redondeadas y cantos suaves."""
    rings = offset_rings(band, None, 2.5, (), Z_FLOAT + SLIDER_T / 2, bottom=(Z_FLOAT - SLIDER_T / 2, 2.5))
    return rings_mesh(NOMBRE + "_Slider_SC", rings)


def knob_mesh():
    """Disco plano con canto redondeado, ORIGEN EN SU CENTRO (el BP lo ubica sobre el arco y lo escala)."""
    circ = lambda o: [((KNOB_R - o) * math.cos(2 * math.pi * k / 48), (KNOB_R - o) * math.sin(2 * math.pi * k / 48)) for k in range(48)]
    rings = offset_rings(circ, None, 4.0, (6.0,), KNOB_T / 2, bottom=(-KNOB_T / 2, 4.0))
    return rings_mesh(NOMBRE + "_Knob_SC", rings)


def swatch_mesh():
    """Casquete de esfera: base de radio CAP_R en el piso del bolsillo, cima en CAP_TOP; canto de la base redondeado."""
    h = CAP_TOP - Z_CAP_POCKET
    Rs = (CAP_R ** 2 + h ** 2) / (2 * h)
    zc = CAP_TOP - Rs
    bm = bmesh.new()
    NA, NR = 64, 14
    pole = bm.verts.new((0, 0, u(CAP_TOP)))
    amax = math.asin(CAP_R / Rs)
    rings = []
    for i in range(1, NR + 1):
        t = amax * i / NR
        rr, zz = Rs * math.sin(t), zc + Rs * math.cos(t)
        rings.append([bm.verts.new((u(rr * math.cos(2 * math.pi * k / NA)), u(rr * math.sin(2 * math.pi * k / NA)), u(zz)))
                      for k in range(NA)])
    for k in range(NA):
        bm.faces.new((pole, rings[0][k], rings[0][(k + 1) % NA]))
    for a, b in zip(rings[:-1], rings[1:]):
        for k in range(NA):
            bm.faces.new((a[k], b[k], b[(k + 1) % NA], a[(k + 1) % NA]))
    base = bm.faces.new(list(reversed(rings[-1])))
    bmesh.ops.poke(bm, faces=[base])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(NOMBRE + "_Swatch_SC")
    bm.to_mesh(me)
    bm.free()
    return me


def base_mesh():
    P = [(0.0, Z_CAP_POCKET, 0), (CAP_POCKET_R, Z_CAP_POCKET, 3), (CAP_POCKET_R, Z_PLATE, 4),
         (GROOVE_IN, Z_PLATE, 5), (GROOVE_IN, Z_GROOVE, 3), (GROOVE_OUT, Z_GROOVE, 3), (GROOVE_OUT, 0.0, 5),
         (R_OUT, 0.0, 16), (R_OUT, Z_BOTTOM, 10), (0.0, Z_BOTTOM, 0)]
    prof = filleted(P)
    bm = bmesh.new()
    vs = [bm.verts.new((u(r), 0.0, u(z))) for r, z in prof]
    es = [bm.edges.new((vs[i], vs[i + 1])) for i in range(len(vs) - 1)]
    bmesh.ops.spin(bm, geom=vs + es, cent=(0, 0, 0), axis=(0, 0, 1), angle=2 * math.pi, steps=SPIN, use_merge=True)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(NOMBRE + "_Base_src")
    bm.to_mesh(me)
    bm.free()
    return me


def pocket_cutter():
    bm = bmesh.new()
    for grp in KEY_ANGLES.values():
        for ang in grp:
            pts = wedge(ang, KEY_HALF, KEY_R1 - KEY_CLEAR, KEY_R2 + KEY_CLEAR, -KEY_CLEAR, KEY_FIL + KEY_CLEAR, n_line=1)
            bot = [bm.verts.new((u(x), u(y), u(Z_KEY_POCKET))) for x, y in pts]
            top = [bm.verts.new((u(x), u(y), u(10.0))) for x, y in pts]
            n = len(pts)
            for j in range(n):
                bm.faces.new((bot[j], bot[(j + 1) % n], top[(j + 1) % n], top[j]))
            bm.faces.new(list(reversed(bot)))
            bm.faces.new(top)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(NOMBRE + "_cutter")
    bm.to_mesh(me)
    bm.free()
    return me


def mesh_from(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    return me


def planar_uv(me, z_top_m):
    """UV0 en metros: planar XY con un ESTIRAMIENTO RADIAL segun la profundidad (1 + dz/1 cm): continuo en todo el
    solido y sin area cero en las paredes verticales. (Correr por la normal saltaba en los filetes casi horizontales.)"""
    uv = me.uv_layers[0] if me.uv_layers else me.uv_layers.new(name="UVMap")
    uv.name = "UVMap"
    for li, loop in enumerate(me.loops):
        co = me.vertices[loop.vertex_index].co
        k = 1.0 + (z_top_m - co.z) / 0.01
        uv.data[li].uv = (co.x * k, co.y * k)


def checks(me):
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    uvl = bm.loops.layers.uv.active
    tiny = sum(1 for f in bm.faces if f.calc_area() < 1e-8)
    deg_uv = 0
    for f in bm.faces:
        a, b, c = [l[uvl].uv for l in f.loops]
        if abs((b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)) < 1e-12:
            deg_uv += 1
    tris = len(bm.faces)
    nm = sum(1 for e in bm.edges if not e.is_manifold)
    bm.free()
    return {"tris": tris, "astillas": tiny, "uv_degeneradas": deg_uv, "no_manifold": nm}


# ---------------------------------------------------------------- escena
def set_normals(me):
    """Normales custom: en las caras PLANAS horizontales la normal exacta de la cara; en el resto, el promedio por area
    de las caras NO planas del vertice. 🔴 Reemplaza a WEIGHTED_NORMAL, que aplicado sobre triangulos chicos (abanicos,
    rellenos) dejaba la tapa de la cuna inclinada 7,8 grados cerca del borde (gotcha 21): pliegue oscuro en render."""
    me.update()
    acc = [[0.0, 0.0, 0.0] for _ in me.vertices]
    flat = [abs(p.normal.z) > 0.999 for p in me.polygons]
    for p, f in zip(me.polygons, flat):
        if not f:
            for vi in p.vertices:
                for c in range(3):
                    acc[vi][c] += p.normal[c] * p.area
    nrm = [None] * len(me.loops)
    for p, f in zip(me.polygons, flat):
        for li in p.loop_indices:
            if f:
                nrm[li] = tuple(p.normal)
            else:
                a = acc[me.loops[li].vertex_index]
                m = math.sqrt(a[0] ** 2 + a[1] ** 2 + a[2] ** 2)
                nrm[li] = (a[0] / m, a[1] / m, a[2] / m) if m > 1e-12 else tuple(p.normal)
    for p in me.polygons:
        p.use_smooth = True
    me.normals_split_custom_set(nrm)


def refill_flats(me):
    """Rehace la triangulacion de cada nivel PLANO horizontal con triangle_fill (maneja huecos): CLIP dio vuelta
    3 triangulos del plato de la base (linea oscura en render)."""
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.normal_update()
    levels = {}
    for f in bm.faces:
        if abs(f.normal.z) > 0.999:
            levels.setdefault(round(f.calc_center_median().z * 1e5), []).append(f)
    for zk, faces in levels.items():
        # el sentido del nivel lo decide la MAYORIA por area: los triangulos que CLIP dio vuelta son minoria
        sgn = 1 if sum(f.normal.z * f.calc_area() for f in faces) > 0 else -1
        fs = set(faces)
        mats = faces[0].material_index
        border = [e for e in {e for f in faces for e in f.edges} if sum(1 for lf in e.link_faces if lf in fs) == 1]
        bmesh.ops.delete(bm, geom=faces, context='FACES_KEEP_BOUNDARY')   # FACES_ONLY dejaba las aristas interiores sueltas
        res = bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=border, normal=(0.0, 0.0, float(sgn)))
        for f in res["geom"]:
            if isinstance(f, bmesh.types.BMFace):
                f.material_index = mats
                f.normal_update()
                if f.normal.z * sgn < 0:
                    f.normal_flip()
    bm.to_mesh(me)
    bm.free()


def finish(col, me, mat):
    """Objeto + normales custom (plano exacto) + material + UV0."""
    ob = bpy.data.objects.new(me.name, me)
    col.objects.link(ob)
    set_normals(me)
    me.materials.append(mat)
    planar_uv(me, max(v.co.z for v in me.vertices))
    return ob


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scn = bpy.context.scene
    col = bpy.data.collections.new(NOMBRE)
    scn.collection.children.link(col)
    out = {}
    m_body = bpy.data.materials.new("M_DrawPalette_Body")
    m_light = bpy.data.materials.new("M_DrawPalette_Groove")
    # --- base: revolucion + bolsillos (booleano) + limpieza + bisel de los cantos del bolsillo ---
    src = bpy.data.objects.new(NOMBRE + "_Base_src", base_mesh())
    cut = bpy.data.objects.new(NOMBRE + "_cutter", pocket_cutter())
    col.objects.link(src)
    col.objects.link(cut)
    bo = src.modifiers.new("Bolsillos", 'BOOLEAN')
    bo.operation, bo.solver, bo.object = 'DIFFERENCE', 'EXACT', cut
    me0 = mesh_from(src)
    src.modifiers.clear()
    bm = bmesh.new()
    bm.from_mesh(me0)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=u(0.5))
    zp = u(Z_PLATE)
    on_plate = lambda v: abs(v.co.z - zp) < 1e-7
    es = [e for e in bm.edges if on_plate(e.verts[0]) and on_plate(e.verts[1])]
    bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(0.5), use_dissolve_boundaries=False,
                             verts=list({v for e in es for v in e.verts}), edges=es)
    bm.to_mesh(me0)
    bm.free()
    old = src.data
    src.data = me0
    bpy.data.meshes.remove(old)
    bpy.data.objects.remove(cut)
    for p in me0.polygons:
        p.use_smooth = True
    bv = src.modifiers.new("Bisel", 'BEVEL')
    bv.width, bv.segments, bv.profile = u(5.0), 2, 0.5
    bv.limit_method, bv.angle_limit = 'ANGLE', math.radians(40)
    bv.use_clamp_overlap, bv.miter_outer = False, 'MITER_SHARP'
    tr = src.modifiers.new("Tri", 'TRIANGULATE')
    tr.min_vertices, tr.quad_method, tr.ngon_method = 5, 'FIXED', 'CLIP'
    meb = mesh_from(src)
    refill_flats(meb)
    meb.name = NOMBRE + "_Base_SC"
    base = bpy.data.objects.new(NOMBRE + "_Base_SC", meb)
    col.objects.link(base)
    bpy.data.objects.remove(src)
    meb.materials.clear()   # 🔴 new_from_object hereda un slot VACIO del objeto fuente: sin esto quedaba [None, Body, Groove]
    meb.materials.append(m_body)
    meb.materials.append(m_light)
    zg = u(Z_GROOVE)
    for p in meb.polygons:
        rr = math.hypot(p.center.x, p.center.y)
        p.material_index = 1 if (abs(p.center.z - zg) < u(1.0) and u(GROOVE_IN) < rr < u(GROOVE_OUT) and p.normal.z > 0.9) else 0
    set_normals(meb)
    planar_uv(meb, 0.0)
    out["Base"] = checks(meb)
    # --- piezas por anillos ---
    # --- cuna (una malla para las 8) + UV1 "IconUV": marco local de la cuna, cuadro ICON_PX centrado a media altura,
    #     arriba del icono = hacia afuera (radial). El material de Unreal lo gira por instancia para dejarlo derecho.
    me = rings_mesh(NOMBRE + "_Key_SC", key_rings(0.0, 0.0))
    me = finish(col, me, m_body).data
    rc = 0.5 * (KEY_R1 + KEY_R2)
    iuv = me.uv_layers.new(name="IconUV")
    for li, loop in enumerate(me.loops):
        co = me.vertices[loop.vertex_index].co
        iuv.data[li].uv = (0.5 + (co.y / u(1.0)) / ICON_PX, 0.5 + (co.x / u(1.0) - rc) / ICON_PX)
    out["Key"] = checks(me)
    # --- undo / redo: UNA pieza lateral (redo = la misma girada +28). El texto lo pone el material (textura
    #     T_DrawPalette_Undo/Redo) por UV1 "LabelUV": u a lo largo del arco (se lee de abajo hacia arriba),
    #     v hacia afuera (cabeza de las letras hacia afuera), cuadro LABEL_W x LABEL_H centrado en la pieza.
    me = rings_mesh(NOMBRE + "_SideKey_SC", side_rings())
    me = finish(col, me, m_body).data
    r0 = 0.5 * (SIDE_R1 + SIDE_R2)
    luv = me.uv_layers.new(name="LabelUV")
    for li, loop in enumerate(me.loops):
        co = me.vertices[loop.vertex_index].co
        th = math.atan2(co.y, co.x)
        dth = (math.radians(SIDE_CENTER) - th + math.pi) % (2 * math.pi) - math.pi
        rr = math.hypot(co.x, co.y) / u(1.0)
        luv.data[li].uv = (0.5 + dth * r0 / LABEL_W, 0.5 + (rr - r0) / LABEL_H)
    out["SideKey"] = checks(me)
    for nm, me in (("Slider", slider_mesh()), ("Knob", knob_mesh()), ("Swatch", swatch_mesh())):
        ob = bpy.data.objects.new(me.name, me)
        col.objects.link(ob)
        set_normals(me)
        me.materials.append(m_body)
        if nm == "Swatch":
            uv = me.uv_layers.new(name="UVMap")
            for li, loop in enumerate(me.loops):
                co = me.vertices[loop.vertex_index].co
                uv.data[li].uv = (co.x / (2 * u(CAP_R)) + 0.5, co.y / (2 * u(CAP_R)) + 0.5)
        else:
            planar_uv(me, max(v.co.z for v in me.vertices))
        out[nm] = checks(me)
    return out


def export_all():
    os.makedirs(DESTINO, exist_ok=True)
    paths = []
    for ob in [o for o in bpy.data.objects if o.type == 'MESH' and o.name.endswith("_SC")]:
        bpy.ops.object.select_all(action='DESELECT')
        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob
        p = os.path.join(DESTINO, ob.name + ".fbx")
        bpy.ops.export_scene.fbx(filepath=p, use_selection=True, apply_unit_scale=True, global_scale=1.0,
                                 apply_scale_options='FBX_SCALE_NONE', object_types={'MESH'}, mesh_smooth_type='FACE',
                                 use_tspace=True, colors_type='NONE', add_leaf_bones=False, bake_anim=False, path_mode='STRIP')
        paths.append(os.path.basename(p))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(DESTINO, NOMBRE + "_SC.blend"))
    return paths


if __name__ == "__main__":
    try:
        info = build()
        fb = export_all()
        print("PALETA_OK", info, fb)
    except BaseException as e:
        print("PALETA_FALLO", type(e).__name__, e)
        traceback.print_exc()
