# gen_hud.py - el HUD como OBJETO 3D (encargo de Narrativa aprobado por Beltran, 2026-09-30): UNA pildora horizontal
# con la ameba que late (izquierda), la ventana del grafico EEG (centro, 4:1 EXACTA, vacia: ahi se monta el widget) y el
# nido del anillo SM_ChargeRing_SC con el alma adentro (derecha). Familia timbre / paleta / sensor: hormigon mate,
# biseles redondeados, normales exactas del perfil.
# Mallas (salida en VR_Test/Saved/ClaudeScripts/HUD/):
#   SM_HUDFrame_SC  el marco: borde de la pildora + marco interior del EEG + collar del nido (anillo) + collar del asiento
#                   (ameba) + fondos opacos de nido y asiento. Slots: 0 Frame (hormigon) 1 Seat (fondos, mas oscuros)
#   SM_HUDGlass_SC  la lamina translucida: una sola cara hacia +Z que llena la pildora ENTRE los collares y con la
#                   ventana del EEG calada (area minima de translucido: sus bordes quedan escondidos bajo el marco)
#   SM_HUDPulse_SC  la ameba que late: gota organica achatada (icosfera 3 + lobulos), ORIGEN EN SU CENTRO (el material
#                   la infla con WPO por la normal). Va en el asiento: posicion en el marco = PULSE_AT
# Marco: pildora acostada en XY, CARA HACIA +Z (como el timbre y el SAVE), X a lo largo; origen = centro de la pildora
# (centro del volumen del borde). Medidas en mm.
# Uso: blender --background --python gen_hud.py -- [dir_salida] [render_dir]
import functools
import math
import os
import sys
import traceback

import bmesh
import bpy
from mathutils import Matrix, Vector

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import revolve_lib as RL   # noqa: E402

# --- la pildora ---
A, B = 128.0, 27.4            # semiejes: 256 x 54,8 (v3, Beltran: "borde y contornos mas delgados, con transparencia"; el nido del anillo de
RC = 26.9                     #   4,5 cm tenga pared). RC casi = B: extremos semicirculares (B exacto duplica puntos)
T = 5.0                       # espesor total (z de -2,5 a +2,5). Beltran v1: "muy grueso, debe ser mucho mas plano" (era 12)
RIM_W = 1.8                   # ancho del borde (TRANSLUCIDO: nada puede quedar escondido adentro de el)
# --- ventana del EEG (4:1 exacta) ---
EEG_A, EEG_B, EEG_RC = 60.0, 15.0, 1.5      # 120 x 30
BEZ_W, BEZ_Z = 1.6, 1.5                      # marco interior: ancho y medio alto (z de -1,5 a +1,5)
# --- nido del anillo (derecha) y asiento de la ameba (izquierda) ---
END_X = A - RC                # 99: centro de los extremos semicirculares (el nido es concentrico con el borde)
NEST_R = 23.5                 # abertura: anillo de 45 mm (r 22,5) + 1 mm de aire
SEAT_R = 23.5                 # abertura: ameba de 35 mm que late hasta 1,2x (r 21) + 2,5 mm de aire
COLLAR_W, COLLAR_Z = 1.4, 2.0              # el collar termina a 0,2 mm de la pared interna del borde (r 25,1)
BACK_Z = -2.0                 # fondos opacos del nido y del asiento
GLASS_Z = -1.2
PULSE_R, PULSE_FLAT = 17.5, 0.20      # ameba mas chata tambien (era 0,36)
PULSE_AT = (-END_X, 0.0, BACK_Z + PULSE_R * PULSE_FLAT + 0.4)
ARC = math.radians(45.0)      # filetes de 2 tramos (presupuesto Quest: a 55 cm los filetes de 1-1,6 mm los hacen las normales)

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else os.path.abspath(os.path.join(AQUI, "..", "..", "..", "..", "VR_Test", "Saved", "ClaudeScripts", "HUD"))
RENDER = argv[1] if len(argv) > 1 else None
# contornos del barrido menos densos que los de las piezas grandes (el largo del borde es recto)
_RR = RL.rrect_outline
RL.rrect_outline = functools.partial(_RR, n_arc=8, step=12.0)


def closed_rect(d0, d1, h0, h1, f_front, f_back, part):
    """Seccion cerrada (d, h) de un anillo: rectangulo con filetes (frente = h1)."""
    mid = (d0 + d1) / 2
    P = [(mid, h0, 0.0, part), (d1, h0, f_back, part), (d1, h1, f_front, part), (d0, h1, f_front, part),
         (d0, h0, f_back, part), (mid, h0, 0.0, part)]
    return RL.fillet_poly(P, ARC)[:-1]


def append(bm_dst, me, M=None):
    me = me.copy()
    if M is not None:
        me.transform(M)
    tmp = bmesh.new()
    tmp.from_mesh(me)
    off = len(bm_dst.verts)
    bpy.data.meshes.remove(me)
    return tmp, off


def join(name, parts, slots):
    """Junta mallas (con sus normales propias) en una sola, conservando slots y normales por esquina."""
    verts, faces, mats, cn, uvs = [], [], [], [], []
    for me, M, slot_map in parts:
        me.calc_loop_triangles()
        R = M.to_3x3().inverted().transposed() if M is not None else None
        base = len(verts)
        for v in me.vertices:
            verts.append((M @ v.co) if M is not None else v.co.copy())
        uvl = me.uv_layers.active
        for p in me.polygons:
            faces.append([base + i for i in p.vertices])
            mats.append(slot_map[p.material_index])
            for li in p.loop_indices:
                n = Vector(me.corner_normals[li].vector)
                cn.append((R @ n).normalized() if R is not None else n)
                uvs.append(tuple(uvl.data[li].uv) if uvl else (0.0, 0.0))
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    uv = me.uv_layers.new(name="UVMap")
    for i, t in enumerate(uvs):
        uv.data[i].uv = t
    for p, m in zip(me.polygons, mats):
        p.material_index = m
        p.use_smooth = True
    me.normals_split_custom_set([tuple(n) for n in cn])
    for s in slots:
        me.materials.append(bpy.data.materials.new(s))
    return me


def disc(name, r, z, n=40):
    bm = bmesh.new()
    c = bm.verts.new((0, 0, z / 1000))
    ring = [bm.verts.new((r * math.cos(2 * math.pi * k / n) / 1000, r * math.sin(2 * math.pi * k / n) / 1000, z / 1000)) for k in range(n)]
    for k in range(n):
        bm.faces.new((c, ring[k], ring[(k + 1) % n]))
    uvl = bm.loops.layers.uv.new("UVMap")
    for f in bm.faces:
        for lp in f.loops:
            lp[uvl].uv = (lp.vert.co.x * 10, lp.vert.co.y * 10)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.normals_split_custom_set_from_vertices([(0, 0, 1)] * len(me.vertices))
    return me


def piece_meshes():
    """Piezas separadas para animar la entrada (cada una con su origen propio):
    Rim (borde, translucido) · Bezel (marco del EEG) · Cup (collar + fondo: nido del anillo Y asiento de la ameba, la
    MISMA malla dos veces, origen en su centro)."""
    rim, f1 = RL.sweep_rrect("rim", closed_rect(-RIM_W, 0.0, -T / 2, T / 2, 0.8, 0.0, "Rim"), ("Rim",), A, B, RC, closed=True)
    RL.rrect_outline = functools.partial(_RR, n_arc=4, step=12.0)
    bez, f2 = RL.sweep_rrect("bez", closed_rect(0.0, BEZ_W, -BEZ_Z, BEZ_Z, 0.6, 0.0, "Frame"), ("Frame",), EEG_A, EEG_B, EEG_RC, closed=True)
    RL.rrect_outline = functools.partial(_RR, n_arc=8, step=12.0)
    col, f3 = RL.revolve("collar", closed_rect(NEST_R, NEST_R + COLLAR_W, -COLLAR_Z, COLLAR_Z, 0.6, 0.0, "Frame"), ("Frame",), 36, closed=True)
    back = disc("back", NEST_R + 0.6, BACK_Z, 36)
    out = {"SM_HUDRim_SC": join("SM_HUDRim_SC", [(rim, None, [0])], ("M_HUD_Rim",)),
           "SM_HUDBezel_SC": join("SM_HUDBezel_SC", [(bez, None, [0])], ("M_HUD_Frame",)),
           "SM_HUDCup_SC": join("SM_HUDCup_SC", [(col, None, [0]), (back, None, [1])], ("M_HUD_Frame", "M_HUD_Seat"))}
    for m in (rim, bez, col, back):
        bpy.data.meshes.remove(m)
    return out, {"rim": f1, "bezel": f2, "collar": f3}


def glass_mesh():
    """Lamina: el interior del borde (llega a su pared interna: el borde es translucido y se veria un borde escondido)
    con TRES agujeros: la ventana del EEG (bajo su marco) y los dos nidos (bajo el collar opaco)."""
    outer = [(x, y) for x, y, _, _ in RL.rrect_outline(A, B, RC, -RIM_W + 0.05)]
    hole = [(x, y) for x, y, _, _ in RL.rrect_outline(EEG_A, EEG_B, EEG_RC, BEZ_W + 0.05)]   # contornos translucidos: la lamina
    rc = NEST_R + COLLAR_W + 0.05                                                                #   llega a su pared, no se mete abajo
    cups = [[(cx + rc * math.cos(2 * math.pi * k / 36), rc * math.sin(2 * math.pi * k / 36)) for k in range(36)] for cx in (END_X, -END_X)]
    bm = bmesh.new()
    z = GLASS_Z / 1000
    es = []
    for loop in [outer, hole] + cups:
        vs = [bm.verts.new((x / 1000, y / 1000, z)) for x, y in loop]
        es += [bm.edges.new((vs[i], vs[(i + 1) % len(vs)])) for i in range(len(vs))]
    bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=es, normal=(0, 0, 1))
    def inside_hole(c):
        x, y = c.x * 1000, c.y * 1000
        if abs(x) < EEG_A + BEZ_W and abs(y) < EEG_B + BEZ_W:
            return True
        return any(math.hypot(x - cx, y) < rc - 0.1 for cx in (END_X, -END_X))
    cut = [f for f in bm.faces if inside_hole(f.calc_center_median())]
    bmesh.ops.delete(bm, geom=cut, context='FACES')
    for f in bm.faces:
        if f.normal.z < 0:
            f.normal_flip()
    uvl = bm.loops.layers.uv.new("UVMap")
    for f in bm.faces:
        for lp in f.loops:
            lp[uvl].uv = ((lp.vert.co.x * 1000 + A) / (2 * A), (lp.vert.co.y * 1000 + B) / (2 * B))
    me = bpy.data.meshes.new("SM_HUDGlass_SC")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(bpy.data.materials.new("M_HUD_Glass"))
    return me, len(cut)


def pulse_mesh():
    """Ameba: icosfera de 1280 tris con 3 lobulos suaves + asimetria de gota, achatada; origen en su centro."""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=4, radius=1.0)
    for v in bm.verts:
        d = v.co.normalized()
        a = math.atan2(d.y, d.x)
        r = 1 + 0.07 * math.sin(3 * a + 0.4) + 0.045 * math.sin(5 * a + 1.3) + 0.06 * math.cos(a - 0.5)
        r *= 1 - 0.08 * d.z * d.z
        v.co = Vector((d.x * r, d.y * r, d.z * PULSE_FLAT * (1 + 0.05 * math.sin(2 * a)))) * (PULSE_R / 1000)
    uvl = bm.loops.layers.uv.new("UVMap")
    for f in bm.faces:
        for lp in f.loops:
            lp[uvl].uv = (lp.vert.co.x * 1000 / (2 * PULSE_R) + 0.5, lp.vert.co.y * 1000 / (2 * PULSE_R) + 0.5)
    me = bpy.data.meshes.new("SM_HUDPulse_SC")
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(bpy.data.materials.new("M_HUD_Pulse"))
    return me


def stats(me):
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    r = {"tris": sum(len(f.verts) - 2 for f in bm.faces), "abiertas": sum(1 for e in bm.edges if not e.is_manifold),
         "degeneradas": sum(1 for f in bm.faces if f.calc_area() < 1e-10)}
    bm.free()
    xs = [v.co for v in me.vertices]
    r["caja_mm"] = [[round(min(c[k] for c in xs) * 1000, 1) for k in range(3)], [round(max(c[k] for c in xs) * 1000, 1) for k in range(3)]]
    return r


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    pieces, flips = piece_meshes()
    gl, cut = glass_mesh()
    pu = pulse_mesh()
    info, obs = {}, []
    for me in list(pieces.values()) + [gl, pu]:
        ob = bpy.data.objects.new(me.name, me)
        bpy.context.scene.collection.objects.link(ob)
        info[me.name] = stats(me)
        obs.append(ob)
    info["dadas_vuelta"] = flips
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):                       # la v1 (marco de una pieza) ya no existe
        if f == "SM_HUDFrame_SC.fbx":
            os.remove(os.path.join(OUT, f))
    for ob in obs:
        RL.export_fbx(ob, os.path.join(OUT, ob.name + ".fbx"))
    # en el .blend las piezas van armadas (en los FBX, cada una en su origen)
    cup = bpy.data.objects["SM_HUDCup_SC"]
    cup.name = "Nest"
    cup.location = (END_X / 1000, 0, 0)
    seat = bpy.data.objects.new("Seat", cup.data)
    bpy.context.scene.collection.objects.link(seat)
    seat.location = (-END_X / 1000, 0, 0)
    bpy.data.objects["SM_HUDPulse_SC"].location = Vector(PULSE_AT) / 1000
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "SM_HUD_SC.blend"))
    print("HUD_OK", info, "cup_en_mm", (END_X, 0, 0), "ameba_en_mm", PULSE_AT)


if __name__ == "__main__":
    try:
        main()
    except BaseException as e:
        print("HUD_FALLO", type(e).__name__, e)
        traceback.print_exc()
