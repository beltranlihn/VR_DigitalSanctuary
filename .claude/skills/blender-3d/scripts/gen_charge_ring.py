# -*- coding: utf-8 -*-
"""gen_charge_ring.py - genera SM_ChargeRing_SC: el anillo contenedor de la proto ameba.

Anillo metalico con 5 cavidades de luz (una por etapa) y un vacio central donde flota la ameba.
SIMETRICO: se ve igual por ambas caras (pedido de Beltran). Eje del anillo = X (en Unreal la
cara mira al forward del actor).

Forma:
  - Solido de revolucion: NUCLEO central (mas ancho, sobresale por fuera y por dentro) entre dos
    PLACAS de cara -> el canto escalonado de la referencia, repetido en las dos caras.
  - En cada cara, 5 CAVIDADES (sectores de corona) separadas por 5 barras de lados paralelos,
    una barra arriba al centro. El piso de cada cavidad lleva el material de luz.
  - Bisel redondeado en TODAS las aristas (angulo > 30 grados) + normales ponderadas.

Materiales (2 slots = 2 secciones en Unreal):
  0  M_ChargeRing_Frame  - el metal
  1  M_ChargeRing_Light  - los pisos de las cavidades
UV0 en los pisos de luz (el contrato con el material de Unreal):
  U = indice_de_etapa + t   (0..5). Etapa 0 = Entering, arriba a la izquierda; las siguientes en
      sentido ANTIHORARIO (DIRECTION), en el orden de la obra. t va de 0 a 1 en ese mismo sentido
      a lo largo de la cavidad, normalizado por radio: t=0 y t=1 caen justo sobre el borde de las barras.
  V = 0 en el borde interior de la cavidad, 1 en el exterior.
  Las dos caras comparten U para el mismo punto fisico (vista de atras, el sentido se invierte).

Uso: "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" --background --python gen_charge_ring.py
Salida: VR_Test/Saved/ClaudeScripts/SM_ChargeRing_SC.fbx y .blend (junto al fbx)
"""
import math
import os
import traceback

import bmesh
import bpy

NOMBRE = "SM_ChargeRing_SC"
R = 0.23            # radio exterior del nucleo, metros (46 cm de diametro; se escala en Unreal)

# --- Planta (fracciones de R), medida en px sobre la vista frontal de la referencia ---
HOLE_CORE = 0.445   # radio del vacio en el nucleo (labio interior que sobresale)
HOLE_FACE = 0.490   # radio del vacio en las placas de cara
SLOT_IN = 0.644     # borde interior de las cavidades
SLOT_OUT = 0.837    # borde exterior de las cavidades
FACE_OUT = 0.955    # radio de las placas de cara
CORE_OUT = 1.000    # radio del nucleo (el canto que sobresale)
SEP_WIDTH = 0.120   # ancho de las barras separadoras (lados paralelos)
N_SLOTS = 5
TOP_BAR_DEG = 90.0  # una barra arriba al centro
DIRECTION = 1.0     # +1 = antihorario (orden de la referencia: Entering arriba-izq, Recognizing, Loving,
                    #      Attracting, Surrounding arriba-der), -1 = horario

# --- Espesor (fracciones de R) ---
THICK = 0.22        # cara a cara
CORE_FRAC = 0.34    # espesor del nucleo / espesor total
POCKET = 0.040      # profundidad de la cavidad de luz en cada cara

# --- Redondeos del perfil (fracciones de R): son los cantos grandes de la silueta ---
FILLET_FACE = 0.028   # cara -> canto exterior y cara -> vacio central
FILLET_STEP = 0.012   # rincon concavo placa -> nucleo
FILLET_CORE = 0.016   # canto del nucleo
FILLET_SEGS = 4

# --- Bisel de las cavidades y resolucion ---
BEVEL = 0.012       # ancho del bisel de las cavidades (fraccion de R)
BEVEL_SEGS = 3
BEVEL_ANGLE_DEG = 30.0
WELD_BEFORE_BEVEL = 0.002   # fraccion de R (0,46 mm): vertices del booleano mas cerca que esto se funden
SEGMENTS = 96       # revolucion (a 1 m el facetado de la silueta es 0,1 mm)
ARC_SAMPLES = 18    # tramos por arco de cavidad (~ la misma densidad que la revolucion)


def filleted(P):
    """Perfil cerrado de esquinas a 90 grados -> cada esquina reemplazada por un arco de radio propio.
    P = [(x, r, radio_del_redondeo)], todo en metros."""
    out = []
    n = len(P)
    for i in range(n):
        px, pr, rf = P[i]
        ax, ar, _ = P[i - 1]
        bx, br, _ = P[(i + 1) % n]
        l1 = math.hypot(px - ax, pr - ar)
        l2 = math.hypot(bx - px, br - pr)
        d1 = ((px - ax) / l1, (pr - ar) / l1)
        d2 = ((bx - px) / l2, (br - pr) / l2)
        cx, cr = px - d1[0] * rf + d2[0] * rf, pr - d1[1] * rf + d2[1] * rf
        for s in range(FILLET_SEGS + 1):
            a = 0.5 * math.pi * s / FILLET_SEGS
            out.append((cx + rf * (-d2[0] * math.cos(a) + d1[0] * math.sin(a)),
                        cr + rf * (-d2[1] * math.cos(a) + d1[1] * math.sin(a))))
    return out


def build_body(h, hc):
    """Solido de revolucion alrededor de X: nucleo + dos placas, con los cantos ya redondeados."""
    f, s, c = FILLET_FACE * R, FILLET_STEP * R, FILLET_CORE * R
    P = [(h, HOLE_FACE * R, f), (h, FACE_OUT * R, f), (hc, FACE_OUT * R, s), (hc, CORE_OUT * R, c),
         (-hc, CORE_OUT * R, c), (-hc, FACE_OUT * R, s), (-h, FACE_OUT * R, f), (-h, HOLE_FACE * R, f),
         (-hc, HOLE_FACE * R, s), (-hc, HOLE_CORE * R, c), (hc, HOLE_CORE * R, c), (hc, HOLE_FACE * R, s)]
    bm = bmesh.new()
    vs = [bm.verts.new((x, 0.0, r)) for (x, r) in filleted(P)]
    es = [bm.edges.new((vs[i], vs[(i + 1) % len(vs)])) for i in range(len(vs))]
    bmesh.ops.spin(bm, geom=vs + es, cent=(0, 0, 0), axis=(1, 0, 0), angle=2 * math.pi,
                   steps=SEGMENTS, use_merge=True)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(NOMBRE + "_src")
    bm.to_mesh(me)
    bm.free()
    return me


def bar_angles():
    """Angulos (grados) de las barras en el sentido de avance, empezando por la de arriba."""
    step = 360.0 / N_SLOTS
    return [TOP_BAR_DEG + DIRECTION * k * step for k in range(N_SLOTS + 1)]


def slot_span(j, r_frac):
    """(angulo_inicio, angulo_fin) en grados de la cavidad j a radio r_frac, en el sentido de avance."""
    b = bar_angles()
    d = math.degrees(math.asin((SEP_WIDTH * 0.5) / r_frac))
    return b[j] + DIRECTION * d, b[j + 1] - DIRECTION * d


def build_cutter(h):
    """Prismas de las cavidades (5 por cara, 2 caras) en una sola malla."""
    bm = bmesh.new()
    x_floor = h - POCKET * R
    x_out = h + 0.05 * R
    for side in (1.0, -1.0):
        for j in range(N_SLOTS):
            a0i, a1i = slot_span(j, SLOT_IN)
            a0o, a1o = slot_span(j, SLOT_OUT)
            rings = []
            for x in (side * x_floor, side * x_out):
                inner, outer = [], []
                for k in range(ARC_SAMPLES + 1):
                    t = k / ARC_SAMPLES
                    ai = math.radians(a0i + (a1i - a0i) * t)
                    ao = math.radians(a0o + (a1o - a0o) * t)
                    inner.append(bm.verts.new((x, SLOT_IN * R * math.cos(ai), SLOT_IN * R * math.sin(ai))))
                    outer.append(bm.verts.new((x, SLOT_OUT * R * math.cos(ao), SLOT_OUT * R * math.sin(ao))))
                rings.append((inner, outer))
            (ib, ob), (it, ot) = rings
            n = ARC_SAMPLES
            for k in range(n):
                bm.faces.new((ib[k], ib[k + 1], ob[k + 1], ob[k]))      # piso
                bm.faces.new((it[k], ot[k], ot[k + 1], it[k + 1]))      # tapa
                bm.faces.new((ib[k], it[k], it[k + 1], ib[k + 1]))      # pared interior
                bm.faces.new((ob[k], ob[k + 1], ot[k + 1], ot[k]))      # pared exterior
            bm.faces.new((ib[0], ob[0], ot[0], it[0]))                  # extremos
            bm.faces.new((ib[n], it[n], ot[n], ob[n]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(NOMBRE + "_cutter")
    bm.to_mesh(me)
    bm.free()
    return me


def slot_uv(y, z, j):
    r = math.hypot(y, z)
    rf = min(max(r / R, SLOT_IN + 1e-4), SLOT_OUT - 1e-4)
    a0, a1 = slot_span(j, rf)
    ang = math.degrees(math.atan2(z, y))
    while ang > a0 + 180.0:
        ang -= 360.0
    while ang < a0 - 180.0:
        ang += 360.0
    t = (ang - a0) / (a1 - a0)
    v = (r / R - SLOT_IN) / (SLOT_OUT - SLOT_IN)
    return j + min(max(t, 0.0), 1.0), min(max(v, 0.0), 1.0)


def slot_of_angle(ang_deg):
    s = (DIRECTION * (ang_deg - TOP_BAR_DEG)) % 360.0
    return min(int(s // (360.0 / N_SLOTS)), N_SLOTS - 1)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scn = bpy.context.scene
    scn.unit_settings.system = 'METRIC'
    scn.unit_settings.scale_length = 1.0

    h = THICK * R * 0.5
    hc = h * CORE_FRAC

    col = bpy.data.collections.new(NOMBRE)
    scn.collection.children.link(col)

    src = bpy.data.objects.new(NOMBRE + "_src", build_body(h, hc))
    cut = bpy.data.objects.new(NOMBRE + "_cutter", build_cutter(h))
    col.objects.link(src)
    col.objects.link(cut)
    for o in (src, cut):
        for p in o.data.polygons:
            p.use_smooth = True
    cut.hide_render = True
    cut.hide_set(True)

    m_frame = bpy.data.materials.new("M_ChargeRing_Frame")
    m_light = bpy.data.materials.new("M_ChargeRing_Light")
    src.data.materials.append(m_frame)
    src.data.materials.append(m_light)

    bo = src.modifiers.new("Cavidades", 'BOOLEAN')
    bo.operation = 'DIFFERENCE'
    bo.solver = 'EXACT'
    bo.object = cut
    dg = bpy.context.evaluated_depsgraph_get()
    me0 = bpy.data.meshes.new_from_object(src.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    src.modifiers.clear()
    old = src.data
    src.data = me0
    bpy.data.meshes.remove(old)
    # 🔴 LIMPIEZA ANTES DEL BISEL: donde una arista radial de la revolucion cruza el borde de una
    # cavidad cerca de un vertice del cortador, el booleano deja dos vertices a MICRONES. El bisel con
    # clamp_overlap se achica al largo de esa arista -> en muchos tramos del borde el bisel media
    # micrones (~6.000 "astillas" que Unreal descarta). Soldarlos DESPUES del bisel no sirve: aplasta
    # esos tramos en canto vivo y tuerce las normales (medido: desvio p95 38 grados en caras planas).
    bm = bmesh.new()
    bm.from_mesh(me0)
    n0 = len(bm.verts)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=WELD_BEFORE_BEVEL * R)
    soldados = n0 - len(bm.verts)
    # Y se disuelven las aristas radiales de la revolucion en el PLANO DE LA CARA: sin clamp_overlap,
    # el desplazamiento del bisel en las esquinas de las cavidades se pasaba de la tira radial vecina y
    # plegaba el poligono (4 triangulos invertidos, medido). Las normales no sufren: se ponderan sobre
    # los n-gons y se triangula despues conservandolas.
    on_face = lambda v: abs(abs(v.co.x) - h) < 1e-7
    es = [e for e in bm.edges if on_face(e.verts[0]) and on_face(e.verts[1])]
    vs = list({v for e in es for v in e.verts})
    bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(0.5), use_dissolve_boundaries=False,
                             verts=vs, edges=es)
    bm.to_mesh(me0)
    bm.free()
    for p in me0.polygons:
        p.use_smooth = True
    bv = src.modifiers.new("Bisel", 'BEVEL')
    bv.width = BEVEL * R
    bv.segments = BEVEL_SEGS
    bv.limit_method = 'ANGLE'
    bv.angle_limit = math.radians(BEVEL_ANGLE_DEG)
    bv.use_clamp_overlap = False   # con True, cualquier arista corta del booleano achica el bisel del borde entero
    bv.miter_outer = 'MITER_SHARP'   # ARC mete un micro-parche en CADA vertice de un borde curvo
    bv.profile = 0.5
    # 🔴 ORDEN: normales ponderadas sobre los n-gons y RECIEN DESPUES triangular conservandolas.
    # Al reves, el area de cada cara plana se reparte en triangulos chicos, el redondeo gana el
    # promedio y la cara sale con dientes de sierra (probado y revertido).
    wn = src.modifiers.new("Normales", 'WEIGHTED_NORMAL')
    wn.mode = 'FACE_AREA'
    wn.weight = 50
    wn.keep_sharp = True
    # los n-gons concavos que quedan se triangulan aca, con control, y no en el importador
    tr = src.modifiers.new("Triangular_ngons", 'TRIANGULATE')
    tr.min_vertices = 5
    tr.quad_method = 'FIXED'
    tr.ngon_method = 'CLIP'      # BEAUTY invertia 4 triangulos en n-gons concavos (medido)
    tr.keep_custom_normals = True

    for name in os.environ.get("CR_SKIP", "").split(","):   # diagnostico: CR_SKIP=Bisel,Triangular_ngons
        if name and name in src.modifiers:
            src.modifiers.remove(src.modifiers[name])
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(src.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    me.name = NOMBRE
    ob = bpy.data.objects.new(NOMBRE, me)
    col.objects.link(ob)
    bpy.data.objects.remove(src)
    bpy.data.objects.remove(cut)

    # --- materiales por geometria: pisos de las cavidades = luz ---
    x_floor = h - POCKET * R
    n_light = 0
    for p in me.polygons:
        c = p.center
        rr = math.hypot(c.y, c.z) / R
        if abs(p.normal.x) > 0.999 and abs(abs(c.x) - x_floor) < 1e-5 and SLOT_IN - 0.01 < rr < SLOT_OUT + 0.01:
            p.material_index = 1
            n_light += 1
        else:
            p.material_index = 0

    # --- UV0: contrato de carga en los pisos; proyeccion plana en el metal ---
    uv = me.uv_layers[0] if me.uv_layers else me.uv_layers.new(name="UVMap")
    uv.name = "UVMap"
    for p in me.polygons:
        if p.material_index == 1:
            j = slot_of_angle(math.degrees(math.atan2(p.center.z, p.center.y)))
            for li in p.loop_indices:
                co = me.vertices[me.loops[li].vertex_index].co
                uv.data[li].uv = slot_uv(co.y, co.z, j)
        else:
            for li in p.loop_indices:
                co = me.vertices[me.loops[li].vertex_index].co
                uv.data[li].uv = (co.y / (2 * R) + 0.5, co.z / (2 * R) + 0.5)

    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    astillas = sum(1 for f in bm.faces if f.calc_area() < 1e-8)   # < 0,01 mm2: Unreal las descarta
    bm.free()
    # CONTROLES (el LISTO los imprime; valores sanos: invertidas 0, desvio max < 2, astillas <= 1):
    # en las caras planas la normal de cada esquina debe ser la de la cara, y ninguna cara al reves
    dev = []
    for p in me.polygons:
        if abs(p.normal.x) > 0.9999 and abs(abs(p.center.x) - h) < 1e-6:
            for li in p.loop_indices:
                dev.append(math.degrees(me.corner_normals[li].vector.angle(p.normal, 0.0)))
    dev.sort()
    invertidas = sum(1 for p in me.polygons
                     if abs(p.normal.x) > 0.99 and abs(abs(p.center.x) - h) < 1e-6 and p.normal.x * p.center.x < 0)
    info_dev = {"invertidas": invertidas, "desvio_caras_planas_max": round(dev[-1], 2) if dev else None,
                "desvio_p95": round(dev[int(len(dev) * 0.95)], 2) if dev else None}
    info = {**info_dev, "soldados_pre_bisel": soldados, "verts": len(me.vertices), "tris": tris, "astillas": astillas, "light_faces": n_light,
            "custom_normals": me.has_custom_normals,
            "dims_cm": [round(d * 100, 2) for d in ob.dimensions]}

    aqui = os.path.dirname(os.path.abspath(__file__))
    destino = os.path.abspath(os.path.join(aqui, "..", "..", "..", "..", "VR_Test", "Saved", "ClaudeScripts"))
    os.makedirs(destino, exist_ok=True)
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    fbx = os.path.join(destino, NOMBRE + ".fbx")
    bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True, apply_unit_scale=True, global_scale=1.0,
                             apply_scale_options='FBX_SCALE_NONE', object_types={'MESH'},
                             mesh_smooth_type='FACE', use_tspace=True, add_leaf_bones=False,
                             bake_anim=False, path_mode='STRIP')
    blend = os.path.join(destino, NOMBRE + ".blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend)
    print("LISTO", NOMBRE, info, "->", fbx)


try:
    main()
except BaseException as e:
    print("FALLO:", type(e).__name__, e)
    traceback.print_exc()
