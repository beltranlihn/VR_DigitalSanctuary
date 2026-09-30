# gen_bake_hall_tiles.py - las 5 BALDOSAS de las etapas en el centro del hall (pedido de Beltran 2026-09-29:
# "cinco baldosas con su color respectivo, separadas una de otra, que se sienta la separacion entre el piso y la
# baldosa, todo muy curvo, con bordes con bevel, organico"). Reemplaza la idea de la alfombra.
# Forma: anillo R1..R2 partido por 5 JUNTAS de ancho constante centradas en los meridianos (las mismas lineas que las
# hendiduras de HallGroovesPS: la junta continua la hendidura), esquinas con filete TILE_FIL (analitico, tangente).
# La baldosa asoma TILE_UP sobre el piso y su canto redondeado (bevel) baja hasta hundirse: la junta oscura la pone el
# shader del piso (HallGroovesPS, mismo SDF -> constantes COMPARTIDAS, cambiar en los dos lados).
# Luz: horneada en Cycles con la escena de render_hall y la MISMA escala que la cascara -> encaja con el piso.
# v3 (2026-09-30, Beltran via Narrativa + sesion del Hall): las baldosas SUBEN hasta 3 cm (WPO Lift del material, un
# slot = una baldosa) y "al subir no deben verse cantos rectos" -> bisel redondo de 3,5 cm (TILE_UP + Lift) en 7
# tramos y faldon de 7 cm (fondo a -6,5 cm: al subir 3 cm sigue hundido). En reposo el canto corta el piso 1,7 cm
# ADENTRO del contorno (v2: 0,4): la sesion del Hall corre el arranque de la junta de HallGroovesPS a -1,7 cm.
# Uso: blender --background <SM_HallShell_SC_baked.blend> --python gen_bake_hall_tiles.py
import importlib.util
import math
import os
import traceback

import bmesh
import bpy

AQUI = os.path.dirname(os.path.abspath(__file__))
os.environ["HALL_NO_RENDER"] = "1"
spec = importlib.util.spec_from_file_location("render_hall", os.path.join(AQUI, "render_hall.py"))
rh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rh)

# --- forma (metros) · 🔴 compartidas con HallGroovesPS.hlsl (TILE_*) ---
TILE_R1 = 1.00        # radio interior
TILE_R2 = 2.50        # radio exterior (el anillo de la alfombra/CarpetRingR queda en 2,90)
TILE_GAP = 0.22       # ancho de la junta entre baldosas
TILE_FIL = 0.20       # filete de las esquinas
FLOOR_Z = 0.30
TILE_UP = 0.005       # cuanto asoma sobre el piso
TILE_T = 0.070        # espesor (el fondo queda hundido en el piso). v3: 0,035 -> 0,070 (sube 3 cm y no asoma el fondo)
BEVEL = 0.035         # radio del canto redondeado de arriba. v3: 0,015 -> 0,035 = TILE_UP + Lift maximo (3 cm)
BEVEL_SEGS = 7
TOP_RINGS = (0.07, 0.14, 0.24, 0.36)   # anillos de la tapa (offset hacia adentro, m): puntos de muestreo de la luz
#   v3: corridos con el bisel (el primero a 3,5 cm del fin del canto, como en la v2)
# Etapa -> angulo en UNREAL (grados; Unreal = Blender con Y espejada: a_UE = -a_Blender). Entrada por la puerta
# Oeste (PlayerStart en x -350 mirando a +X): Entering en 180, la mas cercana; el resto en sentido antihorario
# visto desde arriba (angulo UE decreciente).
STAGES = [("Entering", 180.0), ("Recognizing", 108.0), ("Loving", 36.0), ("Attracting", 324.0), ("Surrounding", 252.0)]
BAKE_SAMPLES = 4096
SMOOTH_ITERS = 6
LIGHT_SCALE = 1.2956  # 🔴 la escala con la que se normalizo la cascara (bake_export_hall.py, EXPORT_OK escala_luz)
N_OUT, N_IN, N_FIL, N_LINE = 28, 14, 8, 6


def arc(c, r, a0, a1, n):
    return [(c[0] + r * math.cos(a0 + (a1 - a0) * k / n), c[1] + r * math.sin(a0 + (a1 - a0) * k / n)) for k in range(n)]


def short(a0, a1):
    d = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
    return a0, a0 + d


def outline(ac, R1=TILE_R1, R2=TILE_R2, gap=TILE_GAP, fil=TILE_FIL):
    """Contorno de la baldosa centrada en el angulo ac (rad, Blender), SIEMPRE con la misma cantidad de puntos:
    los anillos interiores son el mismo contorno desplazado (R1+o, R2-o, gap+2o, fil-o) -> tiras de quads."""
    a0, a1 = ac - math.radians(36), ac + math.radians(36)
    d0, d1 = (math.cos(a0), math.sin(a0)), (math.cos(a1), math.sin(a1))
    n0 = (-d0[1], d0[0])            # hacia la baldosa (angulo creciente)
    n1 = (d1[1], -d1[0])            # hacia la baldosa (angulo decreciente)
    h = gap / 2 + fil

    def center(d, n, R):
        t = math.sqrt(R * R - h * h)
        return (t * d[0] + h * n[0], t * d[1] + h * n[1])
    O0, O1 = center(d0, n0, R2 - fil), center(d1, n1, R2 - fil)
    I0, I1 = center(d0, n0, R1 + fil), center(d1, n1, R1 + fil)

    def on_line(c, n):
        return (c[0] - fil * n[0], c[1] - fil * n[1])

    def on_circ(c, R):
        m = math.hypot(*c)
        return (c[0] * R / m, c[1] * R / m)

    def ang(c, p):
        return math.atan2(p[1] - c[1], p[0] - c[0])
    pts = []
    pI0L, pO0L = on_line(I0, n0), on_line(O0, n0)
    pts += [(pI0L[0] + (pO0L[0] - pI0L[0]) * k / N_LINE, pI0L[1] + (pO0L[1] - pI0L[1]) * k / N_LINE) for k in range(N_LINE)]
    pO0C = on_circ(O0, R2)
    pts += arc(O0, fil, *short(ang(O0, pO0L), ang(O0, pO0C)), N_FIL)
    pO1C = on_circ(O1, R2)
    b0, b1 = math.atan2(pO0C[1], pO0C[0]), math.atan2(pO1C[1], pO1C[0])
    pts += arc((0, 0), R2, *short(b0, b1), N_OUT)
    pO1L = on_line(O1, n1)
    pts += arc(O1, fil, *short(ang(O1, pO1C), ang(O1, pO1L)), N_FIL)
    pI1L = on_line(I1, n1)
    pts += [(pO1L[0] + (pI1L[0] - pO1L[0]) * k / N_LINE, pO1L[1] + (pI1L[1] - pO1L[1]) * k / N_LINE) for k in range(N_LINE)]
    pI1C = on_circ(I1, R1)
    pts += arc(I1, fil, *short(ang(I1, pI1L), ang(I1, pI1C)), N_FIL)
    pI0C = on_circ(I0, R1)
    c0, c1 = math.atan2(pI1C[1], pI1C[0]), math.atan2(pI0C[1], pI0C[0])
    pts += arc((0, 0), R1, *short(c0, c1), N_IN)
    pts += arc(I0, fil, *short(ang(I0, pI0C), ang(I0, pI0L)), N_FIL)
    # orientacion CCW (area con signo positiva) -> las caras nacen mirando a +Z sin recalcular
    area = sum(pts[k][0] * pts[(k + 1) % len(pts)][1] - pts[(k + 1) % len(pts)][0] * pts[k][1] for k in range(len(pts)))
    return pts if area > 0 else pts[::-1]


def rings(ac):
    """Anillos (lista de (pts, z)) de afuera hacia adentro: pie del costado, canto redondeado (cuarto de circulo)
    y los anillos de la tapa. v2: SIN bevel ni inset de bmesh (en la forma concava se cruzaban: triangulos en punta)."""
    ztop, zbot = FLOOR_Z + TILE_UP, FLOOR_Z + TILE_UP - TILE_T
    out = [(outline(ac), zbot)]
    for k in range(BEVEL_SEGS + 1):                      # cuarto de circulo: costado (o=0) -> tapa (o=BEVEL)
        th = 0.5 * math.pi * k / BEVEL_SEGS
        o = BEVEL * (1 - math.cos(th))
        z = ztop - BEVEL + BEVEL * math.sin(th)
        out.append((outline(ac, TILE_R1 + o, TILE_R2 - o, TILE_GAP + 2 * o, max(TILE_FIL - o, 0.01)), z))
    for o in TOP_RINGS:   # anillos de muestreo: filete minimo 6 cm (con 1 cm dejaba astillas que Unreal descarta)
        out.append((outline(ac, TILE_R1 + o, TILE_R2 - o, TILE_GAP + 2 * o, max(TILE_FIL - o, 0.06)), ztop))
    return out


def build_tiles():
    me = bpy.data.meshes.new("SM_HallTiles_SC")
    ob = bpy.data.objects.new("SM_HallTiles_SC", me)
    bpy.context.scene.collection.objects.link(ob)
    bm = bmesh.new()
    for i, (stage, a_ue) in enumerate(STAGES):
        m = bpy.data.materials.new("M_Hall_Tile_" + stage)
        me.materials.append(m)
        rr = rings(math.radians(-a_ue))
        vs = [[bm.verts.new((x, y, z)) for x, y in pts] for pts, z in rr]
        n = len(vs[0])
        assert all(len(v) == n for v in vs), [len(v) for v in vs]
        for a, b in zip(vs[:-1], vs[1:]):                 # a = anillo de afuera/abajo, b = el siguiente
            for j in range(n):
                f = bm.faces.new((a[j], a[(j + 1) % n], b[(j + 1) % n], b[j]))
                f.material_index = i
                f.smooth = True
        f = bm.faces.new(vs[-1])                          # centro de la tapa
        f.material_index = i
        f.smooth = True
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    # UV0: planar en metros en la tapa; en el costado y el canto se CORRE hacia afuera segun lo que baja
    # (u,v) = xy + n_horizontal * (ztop - z). 🔴 Planar puro dejaba los costados con UV de area cero ->
    # "degenerate tangent bases" en Unreal (MikkTSpace).
    ztop = FLOOR_Z + TILE_UP
    uv = me.uv_layers.new(name="UVMap")
    for li, loop in enumerate(me.loops):
        v = me.vertices[loop.vertex_index]
        nx, ny = v.normal.x, v.normal.y
        m = math.hypot(nx, ny)
        k = (ztop - v.co.z) / m if m > 1e-3 else 0.0
        uv.data[li].uv = (v.co.x + nx * k, v.co.y + ny * k)
    tr = ob.modifiers.new("TRI", 'TRIANGULATE')
    tr.ngon_method = 'CLIP'
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.modifier_apply(modifier="TRI")
    me = ob.data
    # 🔴 CLIP toma 3 vertices COLINEALES de un tramo recto como oreja -> triangulos de area cero en la tapa (Unreal
    # los descarta y MikkTSpace avisa "degenerate tangent bases"). beautify_fill gira esas aristas (la tapa es plana).
    bm = bmesh.new()
    bm.from_mesh(me)
    ztop = FLOOR_Z + TILE_UP
    tapa = [f for f in bm.faces if all(abs(v.co.z - ztop) < 1e-6 for v in f.verts)]
    ts = set(tapa)
    ed = [e for e in bm.edges if len(e.link_faces) == 2 and all(f in ts for f in e.link_faces)]
    bmesh.ops.beautify_fill(bm, faces=tapa, edges=ed)
    bm.to_mesh(me)
    bm.free()
    down = sum(1 for p in me.polygons if p.normal.z < -0.5)
    print("TILES_GEOM", {"caras_hacia_abajo": down, "polys": len(me.polygons), "astillas": sum(1 for p in me.polygons if p.area < 1e-8)})
    return ob


def main():
    # 🔴 v2: la luz NO se hornea en Cycles: se COPIA del piso horneado que esta justo debajo (KDTree sobre los
    # vertices del piso de SM_HallShell_SC_baked.blend, que ya trae LightRG/LightB normalizados). El horneado propio
    # dio tapas 20x mas oscuras que el piso vecino sin causa clara; copiar garantiza que la baldosa encaje con el piso.
    from mathutils import kdtree
    shell = bpy.data.objects["SM_HallShell_SC"]
    sm = shell.data
    s2, s3 = sm.uv_layers["LightRG"], sm.uv_layers["LightB"]
    luz = {}
    for poly in sm.polygons:
        if poly.normal.z > 0.99 and abs(poly.center.z - FLOOR_Z) < 0.005:
            for li in poly.loop_indices:
                vi = sm.loops[li].vertex_index
                luz[vi] = (s2.data[li].uv[0], s2.data[li].uv[1], s3.data[li].uv[0])
    kd = kdtree.KDTree(len(luz))
    for vi in luz:
        kd.insert(sm.vertices[vi].co, vi)
    kd.balance()
    ob = build_tiles()
    me = ob.data
    cols = []
    for v in me.vertices:
        near = kd.find_n((v.co.x, v.co.y, FLOOR_Z), 4)          # interpolacion por distancia inversa
        w = [1.0 / max(d, 1e-4) for (_, _, d) in near]
        c = [sum(wi * luz[i][ch] for wi, (_, i, _) in zip(w, near)) / sum(w) for ch in range(3)]
        cols.append(c)
    vals = sorted(max(c) for c in cols)
    print("TILE_LIGHT", {q: round(vals[int(len(vals) * q)], 3) for q in (0.05, 0.5, 0.95)})
    lm = me.uv_layers.new(name="Lightmap")
    l2 = me.uv_layers.new(name="LightRG")
    l3 = me.uv_layers.new(name="LightB")
    uv0 = me.uv_layers["UVMap"]
    for poly in me.polygons:
        for li in poly.loop_indices:
            c = cols[me.loops[li].vertex_index]
            lm.data[li].uv = uv0.data[li].uv
            l2.data[li].uv = (c[0], c[1])
            l3.data[li].uv = (c[2], 0.0)
    me.uv_layers.active = uv0
    destino = os.path.join(os.path.dirname(bpy.data.filepath))
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    path = os.path.join(destino, "SM_HallTiles_SC.fbx")
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, apply_unit_scale=True, global_scale=1.0,
                             apply_scale_options='FBX_SCALE_NONE', object_types={'MESH'},
                             mesh_smooth_type='FACE', use_tspace=True, use_mesh_modifiers=True,
                             colors_type='NONE', add_leaf_bones=False, bake_anim=False, path_mode='STRIP')
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(destino, "SM_HallTiles_SC.blend"))
    print("TILES_OK", {"tris": tris, "verts": len(me.vertices), "slots": [m.name for m in me.materials], "fbx": path})


try:
    main()
except BaseException as e:
    print("TILES_FALLO", type(e).__name__, e)
    traceback.print_exc()
