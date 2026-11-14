# gen_hang.py - EL HANG (handpan electronico) del instrumento de cuerdas/pads de BP_Harp_SC (pedido de Beltran 2026-10-28,
# fotos de un handpan electronico de madera con 9 pads negros: 8 alrededor + el "ding" central). "Debe ser de la estetica
# de los meshes de Soul Charger, como la paleta de Drawing": hormigon calido mate (M_DrawPalette_SC) y la LUZ EN LA
# HENDIDURA del timbre (gen_bell.py): cada pad es un boton con hendidura suave que entra en su bolsillo, y por la ranura
# de 3,5 mm se ve su costado, que brilla con el color de su nota.
# Mallas (cada pad es un mesh aparte para hundirlo en SU eje):
#   SM_Hang_Body_SC  origen en el centro del piso. Slots 0 Body (hormigon) 1 Pocket (paredes del bolsillo) 2 Groove (fondo)
#   SM_Hang_Pad_SC   pad exterior; origen = punto de la cupula en su eje, +Z = normal de la cupula. Slots 0 PadTop 1 PadSide
#   SM_Hang_Ding_SC  el pad central, igual que el pad pero mas grande y con la cupulita del centro
# Ademas escribe hang_pads.json: la transformada de cada pad (cm, ejes de UNREAL: Y espejada) para el BP.
# Uso: blender --background --python gen_hang.py -- <dir_salida>
import json
import math
import os
import sys
import traceback

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from revolve_lib import checks, export_fbx, fillet_poly, revolve   # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else "."

# ---- cuerpo (mm) ----
SEG = 96                  # segmentos alrededor (presupuesto Quest: ~10 k tris el cuerpo)
R_RIM = 258.0             # radio del cuenco y de la cupula en la junta
H_BOWL = 104.0            # alto del cuenco (del piso a la junta)
LIP_OUT, LIP_H, LIP_F = 4.0, 12.0, 2.5   # el labio-junta: sobresale, alto, redondeo
H_TOP = 180.0             # alto total (centro de la cupula)
H_DOME0 = H_BOWL + LIP_H
CAP = H_TOP - H_DOME0
RS = (R_RIM ** 2 + CAP ** 2) / (2 * CAP)   # radio de la esfera de la cupula
ZC = H_TOP - RS                            # centro de esa esfera
BOWL_N = 2.6              # exponente de la superellipse del cuenco (2 = elipse; mas = fondo mas plano)
# ---- pads ----
N_OUT = 8
RHO = 175.0               # distancia horizontal del centro de cada pad exterior al eje
ANG0 = 22.5               # angulo del primer pad (grados, desde +X)
PAD_R, DING_R = 47.0, 72.0
GAP = 3.5                 # luz entre pad y bolsillo (la ranura iluminada)
POCKET_D = 16.0           # fondo del bolsillo bajo el pivote (por el eje del pad)
PAD_UP, PAD_DOWN = 3.5, 9.0   # el pad asoma / se mete bajo la superficie (mas al ras, como la foto)
RIM_F = 1.6               # redondeo de la boca del bolsillo
PAD_F = 4.0               # redondeo del canto
DISH_K, DISH_D = 0.74, 3.0    # hendidura suave: hasta DISH_K * R, de DISH_D mm
BUMP_R, BUMP_H = 30.0, 5.5    # ding: cupulita central
TRAVEL = 5.0              # recorrido al golpear (lo hace el BP; el bolsillo deja 2 mm de mas)
POCKET_SEG = 64


def body_profile():
    P = [(0.0, 0.0, 0.0, "Body")]
    n = 16
    for k in range(1, n + 1):            # cuenco: superellipse de (0,0) a (R_RIM, H_BOWL), vertical en la junta
        t = (math.pi / 2) * k / n
        c, s = math.cos(t), math.sin(t)
        r = R_RIM * (s ** (2.0 / BOWL_N) if s > 0 else 0.0)
        h = H_BOWL * (1 - (c ** (2.0 / BOWL_N) if c > 0 else 0.0))
        P.append((r, h, 0.0, "Body"))
    P[-1] = (R_RIM, H_BOWL, 2.0, "Body")
    P += [(R_RIM + LIP_OUT, H_BOWL, LIP_F, "Body"), (R_RIM + LIP_OUT, H_DOME0, LIP_F, "Body"),
          (R_RIM, H_DOME0, 3.0, "Body")]
    a0 = math.asin(R_RIM / RS)
    m = 22
    for k in range(1, m + 1):            # cupula: arco de la esfera hasta el eje
        a = a0 * (1 - k / m)
        P.append((RS * math.sin(a), ZC + RS * math.cos(a), 0.0, "Body"))
    return fillet_poly(P)


def pad_profile(R, ding):
    """Del eje de abajo hacia afuera, por el canto, hasta el centro de la cara. h = 0 es la superficie de la cupula.
    Debajo de h = 0 el costado es PadSide (la luz que se ve por la ranura); arriba, PadTop (hormigon)."""
    P = [(0.0, -PAD_DOWN, 0.0, "PadSide"), (R, -PAD_DOWN, 1.5, "PadSide"), (R, 0.0, 0.0, "PadTop"),
         (R, PAD_UP, PAD_F, "PadTop")]
    rd = R * DISH_K
    P.append((rd, PAD_UP, 0.0, "PadTop"))
    n = 10
    for k in range(1, n + 1):
        r = rd * (1 - k / n)
        if ding:
            # anillo hundido suave entre la cupulita y el borde + cupulita central
            if r > BUMP_R:
                x = (r - BUMP_R) / (rd - BUMP_R)
                h = PAD_UP - DISH_D * math.sin(math.pi * x)
            else:
                h = PAD_UP + BUMP_H * math.cos(0.5 * math.pi * r / BUMP_R) ** 2
        else:
            h = PAD_UP - DISH_D * (1 - (r / rd) ** 2)
        P.append((r, h, 0.0, "PadTop"))
    return fillet_poly(P)


def pad_frames():
    """(nombre, R, matriz) de cada pad en Blender: origen sobre la cupula, +Z por la normal. 0 = ding."""
    out = [("ding", DING_R, Matrix.Translation((0.0, 0.0, H_TOP / 1000.0)))]
    for k in range(N_OUT):
        th = math.radians(ANG0 + 45.0 * k)
        z = ZC + math.sqrt(RS ** 2 - RHO ** 2)
        p = Vector((RHO * math.cos(th), RHO * math.sin(th), z))
        nrm = (p - Vector((0.0, 0.0, ZC))).normalized()
        q = nrm.to_track_quat('Z', 'Y')
        out.append(("pad%d" % (k + 1), PAD_R, Matrix.Translation(p / 1000.0) @ q.to_matrix().to_4x4()))
    return out


def cutter_mesh(frames):
    """Un cilindro por pad (radio R + GAP, de -POCKET_D a +60 mm por su eje). Paredes = Pocket, fondo = Groove."""
    bm = bmesh.new()
    for _, R, M in frames:
        rc = (R + GAP) / 1000.0
        z0, z1 = -POCKET_D / 1000.0, 0.060
        bot = [bm.verts.new(M @ Vector((rc * math.cos(2 * math.pi * j / POCKET_SEG), rc * math.sin(2 * math.pi * j / POCKET_SEG), z0)))
               for j in range(POCKET_SEG)]
        top = [bm.verts.new(M @ Vector((rc * math.cos(2 * math.pi * j / POCKET_SEG), rc * math.sin(2 * math.pi * j / POCKET_SEG), z1)))
               for j in range(POCKET_SEG)]
        for j in range(POCKET_SEG):
            f = bm.faces.new((bot[j], bot[(j + 1) % POCKET_SEG], top[(j + 1) % POCKET_SEG], top[j]))
            f.material_index = 0
        fb = bm.faces.new(list(reversed(bot)))
        fb.material_index = 1
        ft = bm.faces.new(top)
        ft.material_index = 0
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("Hang_cutter")
    bm.to_mesh(me)
    bm.free()
    return me


def smooth_by_part(me):
    """Normales: promedio por area de las caras del MISMO slot (la cupula lisa, el bolsillo aparte, sin mezclar en el
    canto del bolsillo); el fondo plano del bolsillo queda con su normal exacta."""
    me.update()
    acc = {}
    for p in me.polygons:
        for vi in p.vertices:
            a = acc.setdefault((vi, p.material_index), [0.0, 0.0, 0.0])
            for c in range(3):
                a[c] += p.normal[c] * p.area
    nrm = [None] * len(me.loops)
    for p in me.polygons:
        for li in p.loop_indices:
            a = acc[(me.loops[li].vertex_index, p.material_index)]
            m = math.sqrt(a[0] ** 2 + a[1] ** 2 + a[2] ** 2)
            nrm[li] = (a[0] / m, a[1] / m, a[2] / m) if m > 1e-12 else tuple(p.normal)
    for p in me.polygons:
        p.use_smooth = True
    me.normals_split_custom_set(nrm)


def mesh_from(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    return bpy.data.meshes.new_from_object(ob.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scn = bpy.context.scene
    info = {}
    frames = pad_frames()
    # --- cuerpo: revolucion + 9 bolsillos (booleano exacto con transferencia de materiales) ---
    me, flips = revolve("SM_Hang_Body_SC_src", body_profile(), ("Body",), SEG)
    me.materials.append(bpy.data.materials.new("M_Hang_Body"))
    src = bpy.data.objects.new("SM_Hang_Body_SC_src", me)
    scn.collection.objects.link(src)
    cme = cutter_mesh(frames)
    cme.materials.append(bpy.data.materials.new("M_Hang_Pocket"))
    cme.materials.append(bpy.data.materials.new("M_Hang_Groove"))
    cut = bpy.data.objects.new("Hang_cutter", cme)
    scn.collection.objects.link(cut)
    bo = src.modifiers.new("Bolsillos", 'BOOLEAN')
    bo.operation, bo.solver, bo.object = 'DIFFERENCE', 'EXACT', cut
    bo.material_mode = 'TRANSFER'
    meb = mesh_from(src)
    names = [m.name if m else None for m in meb.materials]
    order = ["M_Hang_Body", "M_Hang_Pocket", "M_Hang_Groove"]
    meb.materials.clear()
    for nm in order:
        meb.materials.append(bpy.data.materials[nm])
    bm = bmesh.new()
    bm.from_mesh(meb)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=0.00005)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    # el booleano exacto no transfirio los slots del cortador: se clasifica cada cara por geometria, en el marco de su pad
    inv = [(R, M.inverted()) for _, R, M in frames]
    for f in bm.faces:
        c = f.calc_center_median()
        f.material_index = 0
        for R, Mi in inv:
            lc = Mi @ c
            rad = math.hypot(lc.x, lc.y) * 1000.0
            z = lc.z * 1000.0
            if rad < R + GAP + 0.3 and z < 0.5:
                f.material_index = 2 if abs(z + POCKET_D) < 0.3 else 1
                break
    # boca del bolsillo redondeada (la familia no tiene cantos vivos; el timbre: boca de la hendidura con radio)
    rim = [e for e in bm.edges if len(e.link_faces) == 2 and {e.link_faces[0].material_index, e.link_faces[1].material_index} == {0, 1}]
    if RIM_F > 0 and rim:
        bmesh.ops.bevel(bm, geom=rim, offset=RIM_F / 1000.0, offset_type='OFFSET', segments=3, profile=0.5,
                        affect='EDGES', clamp_overlap=True)
    bm.to_mesh(meb)
    bm.free()
    smooth_by_part(meb)
    meb.name = "SM_Hang_Body_SC"
    body = bpy.data.objects.new("SM_Hang_Body_SC", meb)
    scn.collection.objects.link(body)
    bpy.data.objects.remove(src)
    bpy.data.objects.remove(cut)
    info["SM_Hang_Body_SC"] = checks(meb, 3)
    info["SM_Hang_Body_SC"]["slots_booleano"] = names
    info["SM_Hang_Body_SC"]["revolve_dadas_vuelta"] = flips
    obs = [body]
    # --- pads ---
    for nm, R, ding in (("SM_Hang_Pad_SC", PAD_R, False), ("SM_Hang_Ding_SC", DING_R, True)):
        pme, pfl = revolve(nm, pad_profile(R, ding), ("PadTop", "PadSide"), 48)
        for part in ("PadTop", "PadSide"):
            pme.materials.append(bpy.data.materials.get("M_Hang_" + part) or bpy.data.materials.new("M_Hang_" + part))
        ob = bpy.data.objects.new(nm, pme)
        scn.collection.objects.link(ob)
        info[nm] = checks(pme, 2)
        info[nm]["dadas_vuelta"] = pfl
        obs.append(ob)
    xs = [v.co for v in meb.vertices]
    info["caja_cm"] = [[round(min(c[k] for c in xs) * 100, 1) for k in range(3)], [round(max(c[k] for c in xs) * 100, 1) for k in range(3)]]
    # --- transformadas para el BP (cm; Unreal espeja la Y del FBX) ---
    pads = []
    for nm, R, M in frames:
        loc, rot, _ = M.decompose()
        z = (rot.to_matrix() @ Vector((0, 0, 1)))
        pads.append({"name": nm, "R_cm": R / 10.0, "loc_cm": [round(loc.x * 100, 4), round(-loc.y * 100, 4), round(loc.z * 100, 4)],
                     "up": [round(z.x, 6), round(-z.y, 6), round(z.z, 6)]})
    os.makedirs(OUT, exist_ok=True)
    for ob in obs:
        export_fbx(ob, os.path.join(OUT, ob.name + ".fbx"))
    with open(os.path.join(OUT, "hang_pads.json"), "w") as f:
        json.dump({"pads": pads, "travel_cm": TRAVEL / 10.0, "pad_up_cm": PAD_UP / 10.0, "gap_cm": GAP / 10.0}, f, indent=1)
    # escena de vista previa: los pads en su lugar (para el .blend y el render)
    for nm, R, M in frames:
        src_ob = bpy.data.objects["SM_Hang_Ding_SC" if nm == "ding" else "SM_Hang_Pad_SC"]
        inst = bpy.data.objects.new("Hang_" + nm, src_ob.data)
        inst.matrix_world = M
        scn.collection.objects.link(inst)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "SM_Hang_SC.blend"))
    print("HANG_OK", json.dumps(info), "RS_mm", round(RS, 1), "ZC_mm", round(ZC, 1))


try:
    main()
except BaseException as e:
    print("HANG_FALLO", type(e).__name__, e)
    traceback.print_exc()
