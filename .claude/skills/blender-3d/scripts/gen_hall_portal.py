# -*- coding: utf-8 -*-
"""gen_hall_portal.py - la arquitectura del HALL DE ENTRADA: el pabellon-portal circular.

Planos de Beltran (Escritorio: Planta/Corte/Elevacionl/Puerta.pdf, cotas en cm) + correcciones:
  - Cilindro de 14,6 m de diametro exterior, muro de 30 cm, muro a 5,6 m y boveda muy rebajada
    hasta 6,5 m, con un oculo de 2,4 m en la cima.
  - Dos puertas CIRCULARES COMPLETAS de 3,5 m, enfrentadas, levantadas del piso.
  - Cada puerta: dos medias lunas de vidrio esmerilado que CORREN SOBRE LA CARA EXTERIOR CURVA del
    muro. Se modelan aparte, con el pivote en el eje del edificio: abrir = girarlas en Z.
  - Todo organico: cada union es una curva grande, ninguna arista viva.

Construccion (todo analitico, todo quads, SIN booleanos):
  - La cascara es UN perfil (r, z) revolucionado: piso interior -> cove -> muro -> cove de boveda ->
    boveda -> labio del oculo -> boveda exterior -> ... -> fondo exterior. El exterior es el interior
    desplazado 30 cm por su normal (los redondeos exteriores son los interiores + 30 cm).
  - Cada vano de puerta reemplaza un rectangulo de celdas del muro por una malla "circulo dentro de un
    cuadrado": anillos que van del borde del rectangulo al circulo, luego el redondeo del canto y el
    vano atravesando el muro. Se proyecta horizontal sobre el cilindro -> en elevacion es un circulo
    perfecto, igual que en los planos.
  - UV0 por zonas, en METROS, islas sin solapar (piso, muro, boveda, vanos; interior y exterior).

Uso: "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" --background --python gen_hall_portal.py
Salida: VR_Test/Saved/ClaudeScripts/Hall/ (SM_HallShell_SC.blend + FBX)
"""
import math
import os
import traceback

import bmesh
import bpy

# ---------------- PARAMETROS (metros) ----------------
R_IN = 7.0            # radio interior del muro (exterior 7,3 -> 14,6 m)
T = 0.30              # espesor de muro, piso y boveda
FLOOR_Z = 0.30        # piso interior (el fondo exterior queda en z = 0)
C_FLOOR = 0.25        # redondeo interior piso -> muro
RIM_OUT = 5.60        # altura exterior del muro (vertice virtual con la boveda)
APEX_OUT = 6.50       # cima exterior de la boveda
C_DOME = 1.00         # redondeo interior muro -> boveda (el "cove" organico)
OCULUS_R = 1.20       # radio libre del oculo (2,4 m)

DOOR_R = 1.75         # radio del vano (3,5 m)
DOOR_ZC = 2.45        # centro del vano -> borde inferior a 0,70 (40 cm sobre el piso interior)
DOOR_FIL_IN = 0.12    # redondeo del canto del vano, cara interior
DOOR_FIL_OUT = 0.05   # idem, cara exterior (negra, casi no se ve)
DOOR_HALF_W = 2.25    # medio ancho del rectangulo de muro que se remalla alrededor del vano
DOOR_ANGLES = (0.0, 180.0)   # puertas enfrentadas (Este / Oeste)

LEAF_R = 1.85         # radio de cada hoja (10 cm mas que el vano: tapa el canto)
LEAF_GAP = 0.02       # separacion hoja-muro
LEAF_T = 0.03         # espesor del vidrio
LEAF_SPLIT = 0.004    # media junta entre las dos hojas
LEAF_OPEN_DEG = 16.5  # giro alrededor del eje del edificio para abrir del todo

# resolucion
NCOL = 192            # columnas de la revolucion (1,875 grados; 23 cm en el muro)
ROW_STEP = 0.15       # paso de filas en el muro (define la resolucion del circulo de la puerta)
N_FLOOR = 8           # anillos del piso
N_COVE_F = 6          # segmentos del cove de piso
N_COVE_D = 10         # segmentos del cove de boveda
N_DOME = 16           # segmentos de la boveda
N_LIP = 8             # segmentos del labio del oculo
DOOR_RINGS = 6        # anillos entre el rectangulo y el circulo
DOOR_FIL_SEGS = 6     # segmentos del redondeo del canto

NOMBRE = "SM_HallShell_SC"


# ---------------- PERFIL ----------------
def build_profile():
    """Lista de (r, z, region, superficie) de la cascara, en orden, sin los centros de los polos.
    region: floor | wall | dome   superficie: in | out"""
    R_OUT = R_IN + T
    h = APEX_OUT - RIM_OUT
    Rs_out = (R_OUT ** 2 + h ** 2) / (2 * h)
    zs = APEX_OUT - Rs_out
    Rs_in = Rs_out - T
    # cove de boveda: tangente al muro (vertical) y a la esfera interior
    cr = R_IN - C_DOME
    zcc = zs + math.sqrt((Rs_in - C_DOME) ** 2 - cr ** 2)
    dr, dz = cr / (Rs_in - C_DOME), (zcc - zs) / (Rs_in - C_DOME)   # direccion centro esfera -> centro cove
    a_end = math.atan2(dz, dr)
    r_tan_sphere = cr + C_DOME * dr
    psi0 = math.asin(r_tan_sphere / Rs_in)
    r_lip = OCULUS_R + T * 0.5
    psi1_in = math.asin(r_lip / Rs_in)
    psi1_out = math.asin(r_lip / Rs_out)
    fz_c = FLOOR_Z + C_FLOOR           # centro del cove de piso (z)
    fr_c = R_IN - C_FLOOR

    inn = []
    for k in range(1, N_FLOOR + 1):                      # piso
        inn.append((fr_c * k / N_FLOOR, FLOOR_Z, "floor"))
    for k in range(1, N_COVE_F + 1):                     # cove de piso (-90 -> 0 grados)
        a = -0.5 * math.pi + 0.5 * math.pi * k / N_COVE_F
        inn.append((fr_c + C_FLOOR * math.cos(a), fz_c + C_FLOOR * math.sin(a), "floor"))
    z0, z1 = fz_c, zcc                                   # muro recto
    nw = max(2, round((z1 - z0) / ROW_STEP))
    for k in range(1, nw + 1):
        inn.append((R_IN, z0 + (z1 - z0) * k / nw, "wall"))
    for k in range(1, N_COVE_D + 1):                     # cove de boveda (0 -> a_end)
        a = a_end * k / N_COVE_D
        inn.append((cr + C_DOME * math.cos(a), zcc + C_DOME * math.sin(a), "dome"))
    for k in range(1, N_DOME + 1):                       # boveda interior
        p = psi0 + (psi1_in - psi0) * k / N_DOME
        inn.append((Rs_in * math.sin(p), zs + Rs_in * math.cos(p), "dome"))
    z_in = zs + Rs_in * math.cos(psi1_in)
    z_out = zs + Rs_out * math.cos(psi1_out)
    rho = (z_out - z_in) * 0.5
    zm = (z_in + z_out) * 0.5
    lip = []
    for k in range(1, N_LIP):                            # labio: semicirculo hacia el eje
        a = math.pi * k / N_LIP
        lip.append((r_lip - rho * math.sin(a), zm - rho * math.cos(a), "dome"))
    out = []                                             # exterior: desplazar el interior 30 cm
    out.append((r_lip, z_out, "dome"))
    for k in range(N_DOME - 1, -1, -1):
        p = psi0 + (psi1_out - psi0) * k / N_DOME
        out.append((Rs_out * math.sin(p), zs + Rs_out * math.cos(p), "dome"))
    for k in range(N_COVE_D - 1, -1, -1):
        a = a_end * k / N_COVE_D
        out.append((cr + (C_DOME + T) * math.cos(a), zcc + (C_DOME + T) * math.sin(a), "dome" if k > 0 else "wall"))
    for k in range(nw - 1, 0, -1):
        out.append((R_IN + T, z0 + (z1 - z0) * k / nw, "wall"))
    for k in range(N_COVE_F, -1, -1):
        a = -0.5 * math.pi + 0.5 * math.pi * k / N_COVE_F
        out.append((fr_c + (C_FLOOR + T) * math.cos(a), fz_c + (C_FLOOR + T) * math.sin(a), "floor" if k < N_COVE_F else "wall"))
    for k in range(N_FLOOR - 1, 0, -1):
        out.append((fr_c * k / N_FLOOR, 0.0, "floor"))
    prof = [(r, z, g, "in") for (r, z, g) in inn] + [(r, z, g, "in") for (r, z, g) in lip] + \
           [(r, z, g, "out") for (r, z, g) in out]
    info = {"Rs_out": Rs_out, "zs": zs, "wall_z": (z0, z1), "n_wall": nw, "r_lip": r_lip}
    return prof, info


def arc_lengths(prof, idxs):
    s, acc, prev = {}, 0.0, None
    for j in idxs:
        r, z = prof[j][0], prof[j][1]
        if prev is not None:
            acc += math.hypot(r - prev[0], z - prev[1])
        s[j] = acc
        prev = (r, z)
    return s


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scn = bpy.context.scene
    scn.unit_settings.system = 'METRIC'
    R_OUT = R_IN + T
    prof, info = build_profile()
    NP = len(prof)
    dth = 2 * math.pi / NCOL
    z0, z1 = info["wall_z"]

    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    V = [[bm.verts.new((prof[j][0] * math.cos(c * dth), prof[j][0] * math.sin(c * dth), prof[j][1]))
          for c in range(NCOL)] for j in range(NP)]
    c_in = bm.verts.new((0.0, 0.0, FLOOR_Z))
    c_out = bm.verts.new((0.0, 0.0, 0.0))

    # filas del muro recto (interior y exterior)
    wall_in = [j for j in range(NP) if prof[j][3] == "in" and prof[j][2] == "wall"]
    wall_out = [j for j in range(NP) if prof[j][3] == "out" and abs(prof[j][0] - R_OUT) < 1e-6
                and z0 - 1e-6 <= prof[j][1] <= z1 + 1e-6]
    jin0, jin1 = wall_in[0] - 1, wall_in[-1]          # incluye la fila del final del cove (z0)
    jo_top, jo_bot = wall_out[0], wall_out[-1]         # la exterior va de arriba hacia abajo (incluye z1 y z0)
    HW = round(math.asin(DOOR_HALF_W / R_IN) / dth)
    door_cols = {}
    for da in DOOR_ANGLES:
        cc = round(math.radians(da) / dth)
        door_cols[da] = [(cc + k) % NCOL for k in range(-HW, HW + 1)]

    def cell_in_door(j, c):
        for da, cols in door_cols.items():
            if c in cols[:-1]:
                if jin0 <= j < jin1 or jo_top <= j < jo_bot:
                    return True
        return False

    region_of = {}
    faces_meta = []   # (face, region, surface)

    def add_face(vs, region, surf):
        f = bm.faces.new(vs)
        faces_meta.append((f, region, surf))
        return f

    # grilla de revolucion
    for j in range(NP - 1):
        if prof[j][3] != prof[j + 1][3] and not (prof[j][3] == "in" and prof[j + 1][3] == "out"):
            pass
        for c in range(NCOL):
            if cell_in_door(j, c):
                continue
            c2 = (c + 1) % NCOL
            reg = prof[j][2] if prof[j][2] == prof[j + 1][2] else ("wall" if "wall" in (prof[j][2], prof[j + 1][2]) and prof[j][2] != "dome" and prof[j + 1][2] != "dome" else prof[j + 1][2])
            surf = "out" if prof[j][3] == "out" and prof[j + 1][3] == "out" else "in"
            add_face((V[j][c], V[j][c2], V[j + 1][c2], V[j + 1][c]), reg, surf)
    for c in range(NCOL):   # polos
        c2 = (c + 1) % NCOL
        add_face((c_in, V[0][c2], V[0][c]), "floor", "in")
        add_face((c_out, V[NP - 1][c], V[NP - 1][c2]), "floor", "out")

    # ---- vanos de puerta: circulo dentro del rectangulo ----
    reveal_meta = []
    for da in DOOR_ANGLES:
        th = math.radians(da)
        n = (math.cos(th), math.sin(th))
        t = (-math.sin(th), math.cos(th))
        cols = door_cols[da]

        def uz(v):
            p = v.co
            return p.x * t[0] + p.y * t[1], p.z

        def boundary(jlo, jhi):
            ring = set()
            for j in range(min(jlo, jhi), max(jlo, jhi) + 1):
                ring.add(V[j][cols[0]])
                ring.add(V[j][cols[-1]])
            for c in cols:
                ring.add(V[jlo][c])
                ring.add(V[jhi][c])
            return sorted(ring, key=lambda v: math.atan2(uz(v)[1] - DOOR_ZC, uz(v)[0]))

        B_in = boundary(jin0, jin1)
        B_out = boundary(jo_top, jo_bot)
        assert len(B_in) == len(B_out), (len(B_in), len(B_out))
        M = len(B_in)
        phis = [math.atan2(uz(v)[1] - DOOR_ZC, uz(v)[0]) for v in B_in]

        def place(u, z, R, depth_sign, depth):
            x = math.sqrt(R * R - u * u) + depth_sign * depth
            return (n[0] * x + t[0] * u, n[1] * x + t[1] * u, z)

        def surface_rings(B, R, fil, sgn):
            rings = [B]
            for k in range(1, DOOR_RINGS + 1):
                s = k / DOOR_RINGS
                ring = []
                for i, v in enumerate(B):
                    bu, bz = uz(v)
                    cu = (DOOR_R + fil) * math.cos(phis[i])
                    cz = DOOR_ZC + (DOOR_R + fil) * math.sin(phis[i])
                    u, z = bu + (cu - bu) * s, bz + (cz - bz) * s
                    ring.append(bm.verts.new(place(u, z, R, 0, 0)))
                rings.append(ring)
            fil_rings = []
            for k in range(1, DOOR_FIL_SEGS + 1):
                a = 0.5 * math.pi * k / DOOR_FIL_SEGS
                rho = DOOR_R + fil * (1 - math.sin(a))
                d = fil * (1 - math.cos(a))
                ring = [bm.verts.new(place(rho * math.cos(phis[i]), DOOR_ZC + rho * math.sin(phis[i]), R, sgn, d))
                        for i in range(M)]
                fil_rings.append(ring)
            return rings, fil_rings

        rin, fin = surface_rings(B_in, R_IN, DOOR_FIL_IN, +1)
        rout, fout = surface_rings(B_out, R_OUT, DOOR_FIL_OUT, -1)
        for rings, surf in ((rin, "in"), (rout, "out")):
            for k in range(len(rings) - 1):
                a, b = rings[k], rings[k + 1]
                for i in range(M):
                    i2 = (i + 1) % M
                    add_face((a[i], a[i2], b[i2], b[i]), "wall", surf)
        chain_in = [rin[-1]] + fin
        chain_out = [rout[-1]] + fout
        chain = chain_in + list(reversed(chain_out))      # de la cara interior a la exterior
        for k in range(len(chain) - 1):
            a, b = chain[k], chain[k + 1]
            surf = "in" if k < len(chain_in) - 1 or k == len(chain_in) - 1 else "out"
            if k >= len(chain_in):
                surf = "out"
            for i in range(M):
                i2 = (i + 1) % M
                f = add_face((a[i], a[i2], b[i2], b[i]), "reveal", surf)
                reveal_meta.append((f, da, k))

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    # ---- UV0 por zonas, en metros ----
    # arco del perfil para piso (desde el centro) y boveda (desde el labio)
    floor_in = [j for j in range(NP) if prof[j][3] == "in" and prof[j][2] == "floor"]
    floor_out = [j for j in range(NP) if prof[j][3] == "out" and prof[j][2] == "floor"]
    s_fin = arc_lengths(prof, floor_in)
    s_fout = arc_lengths(prof, list(reversed(floor_out)))
    dome_in = [j for j in range(NP) if prof[j][3] == "in" and prof[j][2] == "dome"]
    dome_out = [j for j in range(NP) if prof[j][3] == "out" and prof[j][2] == "dome"]
    s_din = arc_lengths(prof, list(reversed(dome_in)))    # desde el labio hacia el muro
    s_dout = arc_lengths(prof, dome_out)
    first_floor_r = prof[floor_in[0]][0]
    vrow = {}
    for j in range(NP):
        for c in range(NCOL):
            vrow[V[j][c]] = j

    # islas (desplazamientos para que no se solapen)
    OFF = {("floor", "in"): (0.0, 0.0), ("dome", "in"): (17.0, 0.0), ("wall", "in"): (-2.0, 19.0),
           ("floor", "out"): (0.0, 45.0), ("dome", "out"): (17.0, 45.0), ("wall", "out"): (-2.0, 64.0),
           ("reveal", 0.0): (40.0, 0.0), ("reveal", 180.0): (40.0, 8.0)}

    def polar_uv(v, s, rad0):
        th = math.atan2(v.co.y, v.co.x)
        return (rad0 + s) * math.cos(th), (rad0 + s) * math.sin(th)

    reveal_of = {f: (da, k) for (f, da, k) in reveal_meta}
    for (f, reg, surf) in faces_meta:
        uvs = []
        if reg == "floor":
            s_map = s_fin if surf == "in" else s_fout
            for lp in f.loops:
                v = lp.vert
                if v in (c_in, c_out):
                    uvs.append((0.0, 0.0))
                else:
                    j = vrow[v]
                    uvs.append(polar_uv(v, s_map[j] + first_floor_r, 0.0))
        elif reg == "dome":
            s_map = s_din if surf == "in" else s_dout
            for lp in f.loops:
                j = vrow[lp.vert]
                s = s_map.get(j)
                if s is None:   # fila del labio: radio menor que el oculo
                    rr, zz = prof[j][0], prof[j][1]
                    s = -math.hypot(rr - info["r_lip"], 0) - 0.0
                uvs.append(polar_uv(lp.vert, s, OCULUS_R))
        elif reg == "wall":
            R = R_IN if surf == "in" else R_OUT
            ths = []
            for lp in f.loops:
                a = (math.atan2(lp.vert.co.y, lp.vert.co.x) - math.pi / 2) % (2 * math.pi)
                ths.append(a)
            if max(ths) - min(ths) > math.pi:
                ths = [a + 2 * math.pi if a < math.pi else a for a in ths]
            uvs = [(a * R, lp.vert.co.z) for a, lp in zip(ths, f.loops)]
        else:   # reveal: (angulo alrededor de la puerta, distancia a traves del muro)
            da, k = reveal_of[f]
            th = math.radians(da)
            t = (-math.sin(th), math.cos(th))
            phs, dep = [], []
            for lp in f.loops:
                p = lp.vert.co
                u = p.x * t[0] + p.y * t[1]
                phs.append(math.atan2(p.z - DOOR_ZC, u) % (2 * math.pi))
                dep.append(p.x * math.cos(th) + p.y * math.sin(th))
            if max(phs) - min(phs) > math.pi:
                phs = [a + 2 * math.pi if a < math.pi else a for a in phs]
            uvs = [(a * DOOR_R, d) for a, d in zip(phs, dep)]
        key = (reg, surf) if reg != "reveal" else ("reveal", reveal_of[f][0])
        ox, oy = OFF[key]
        if reg in ("floor", "dome"):
            ox, oy = ox + 8.0, oy + 8.0
        for lp, (u, v) in zip(f.loops, uvs):
            lp[uvl].uv = (u + ox, v + oy)

    me = bpy.data.meshes.new(NOMBRE)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(NOMBRE, me)
    col = bpy.data.collections.new("HallPortal")
    scn.collection.children.link(col)
    col.objects.link(ob)

    # materiales: interior (hormigon fino) / exterior (negro)
    m_in = bpy.data.materials.new("M_Hall_Interior")
    m_out = bpy.data.materials.new("M_Hall_Exterior")
    me.materials.append(m_in)
    me.materials.append(m_out)
    surf_list = [s for (_, _, s) in faces_meta]
    for p, s in zip(me.polygons, surf_list):
        p.material_index = 1 if s == "out" else 0

    # ---- hojas de vidrio + la piel negra que las esconde (idea de Beltran) ----
    leaves = build_leaves(col)
    masks = build_masks(col, m_out)

    # controles
    bmc = bmesh.new()
    bmc.from_mesh(me)
    nonman = sum(1 for e in bmc.edges if not e.is_manifold)
    bmc.free()
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    aqui = os.path.dirname(os.path.abspath(__file__))
    destino = os.path.abspath(os.path.join(aqui, "..", "..", "..", "..", "VR_Test", "Saved", "ClaudeScripts", "Hall"))
    os.makedirs(destino, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(destino, NOMBRE + ".blend"))
    print("LISTO", {"tris": tris, "verts": len(me.vertices), "no_manifold": nonman,
                    "hojas": leaves, "mascaras": masks, "dims_m": [round(d, 3) for d in ob.dimensions],
                    "muro_z": [round(z0, 3), round(z1, 3)]})


MASK_GAP = 0.01       # hoja -> mascara
MASK_T = 0.02         # espesor de la piel negra
MASK_HALF_W = 4.30    # cubre todo el recorrido de la hoja abierta (~3,9 m del eje de la puerta)
MASK_HALF_H = 2.05    # un poco mas que la hoja (1,85)


def build_masks(col, m_black):
    """La piel negra con el agujero circular: las hojas corren ENTRE el muro y esta piel, asi desde
    afuera solo se ve el circulo (cerrado u abierto) y nunca el recorrido de las hojas."""
    R_OUT = R_IN + T
    R1 = R_OUT + LEAF_GAP + LEAF_T + MASK_GAP
    R2 = R1 + MASK_T
    M, NR = 128, 6
    made = []
    for da in DOOR_ANGLES:
        th = math.radians(da)
        n = (math.cos(th), math.sin(th))
        t = (-math.sin(th), math.cos(th))
        bm = bmesh.new()
        uvl = bm.loops.layers.uv.new("UVMap")
        phis = [2 * math.pi * i / M for i in range(M)]

        def rect(ph):   # interseccion del rayo con el rectangulo
            cu, cz = math.cos(ph), math.sin(ph)
            s = min(MASK_HALF_W / abs(cu) if abs(cu) > 1e-9 else 1e9, MASK_HALF_H / abs(cz) if abs(cz) > 1e-9 else 1e9)
            return s * cu, s * cz

        def P(u, v, R):
            x = math.sqrt(R * R - u * u)
            return (n[0] * x + t[0] * u, n[1] * x + t[1] * u, DOOR_ZC + v)

        layers = []
        for R in (R1, R2):
            rings = []
            for k in range(NR + 1):
                s = k / NR
                ring = []
                for ph in phis:
                    bu, bv = rect(ph)
                    cu, cv = DOOR_R * math.cos(ph), DOOR_R * math.sin(ph)
                    ring.append(bm.verts.new(P(bu + (cu - bu) * s, bv + (cv - bv) * s, R)))
                rings.append(ring)
            layers.append(rings)
        for li, rings in enumerate(layers):
            for k in range(NR):
                for i in range(M):
                    i2 = (i + 1) % M
                    q = (rings[k][i], rings[k][i2], rings[k + 1][i2], rings[k + 1][i])
                    bm.faces.new(q if li else q[::-1])
        for k in (0, NR):   # borde exterior y borde del agujero
            a, b = layers[0][k], layers[1][k]
            for i in range(M):
                i2 = (i + 1) % M
                bm.faces.new((a[i], a[i2], b[i2], b[i]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        for f in bm.faces:
            for lp in f.loops:
                p = lp.vert.co
                lp[uvl].uv = (p.x * t[0] + p.y * t[1] + 5.0, p.z)
        nm = "SM_HallDoorMask_%s" % ("E" if da == 0.0 else "W")
        me = bpy.data.meshes.new(nm)
        bm.to_mesh(me)
        bm.free()
        for p in me.polygons:
            p.use_smooth = True
        me.materials.append(m_black)
        ob = bpy.data.objects.new(nm, me)
        col.objects.link(ob)
        made.append(nm)
    return made


def build_leaves(col):
    """Cuatro hojas (media luna curva sobre el cilindro exterior), pivote en el eje del edificio."""
    R_OUT = R_IN + T
    NRL, NPH = 8, 48
    made = []
    m_glass = bpy.data.materials.new("M_Hall_Glass")
    for da in DOOR_ANGLES:
        th = math.radians(da)
        n = (math.cos(th), math.sin(th))
        t = (-math.sin(th), math.cos(th))
        for side, sgn in (("R", 1.0), ("L", -1.0)):
            bm = bmesh.new()
            uvl = bm.loops.layers.uv.new("UVMap")

            def P(rho, phi, R):
                u = sgn * (LEAF_SPLIT + rho * math.cos(phi))
                z = DOOR_ZC + rho * math.sin(phi)
                x = math.sqrt(R * R - u * u)
                return (n[0] * x + t[0] * u, n[1] * x + t[1] * u, z)

            phis = [-0.5 * math.pi + math.pi * m / NPH for m in range(NPH + 1)]
            layers = []
            for R in (R_OUT + LEAF_GAP, R_OUT + LEAF_GAP + LEAF_T):
                cen = bm.verts.new(P(0.0, 0.0, R))
                rings = [[bm.verts.new(P(LEAF_R * k / NRL, ph, R)) for ph in phis] for k in range(1, NRL + 1)]
                layers.append((cen, rings))
            for li, (cen, rings) in enumerate(layers):
                flip = li == 0
                for m in range(NPH):
                    tri = (cen, rings[0][m], rings[0][m + 1])
                    bm.faces.new(tri[::-1] if flip else tri)
                for k in range(NRL - 1):
                    for m in range(NPH):
                        q = (rings[k][m], rings[k + 1][m], rings[k + 1][m + 1], rings[k][m + 1])
                        bm.faces.new(q[::-1] if flip else q)

            def loop_of(cen, rings):
                arc = rings[-1][:]                                   # borde curvo (-90 -> 90)
                top = [rings[k][-1] for k in range(NRL - 2, -1, -1)]  # radio de +90 hacia el centro
                bot = [rings[k][0] for k in range(0, NRL - 1)]        # radio de -90 desde el centro
                return arc + top + [cen] + bot
            la, lb = loop_of(*layers[0]), loop_of(*layers[1])
            L = len(la)
            for i in range(L):
                i2 = (i + 1) % L
                bm.faces.new((la[i], la[i2], lb[i2], lb[i]))
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            for f in bm.faces:              # UV: proyeccion en elevacion, metros
                for lp in f.loops:
                    p = lp.vert.co
                    lp[uvl].uv = (p.x * t[0] + p.y * t[1] + 2.0, p.z)
            nm = "SM_HallDoorLeaf_%s_%s" % ("E" if da == 0.0 else "W", side)
            me = bpy.data.meshes.new(nm)
            bm.to_mesh(me)
            bm.free()
            for p in me.polygons:
                p.use_smooth = True
            me.materials.append(m_glass)
            ob = bpy.data.objects.new(nm, me)
            ob["open_deg"] = LEAF_OPEN_DEG * sgn     # giro en Z (pivote = eje del edificio) para abrir
            col.objects.link(ob)
            bv = ob.modifiers.new("Bisel", 'BEVEL')
            bv.width = 0.006
            bv.segments = 2
            bv.limit_method = 'ANGLE'
            bv.angle_limit = math.radians(40)
            wn = ob.modifiers.new("Normales", 'WEIGHTED_NORMAL')
            wn.keep_sharp = True
            made.append(nm)
    return made


try:
    main()
except BaseException as e:
    print("FALLO:", type(e).__name__, e)
    traceback.print_exc()
