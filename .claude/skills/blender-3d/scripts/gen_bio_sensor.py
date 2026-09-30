# gen_bio_sensor.py - el "controller" de las etapas de RESPIRACION y LATIDO (pedido de Beltran, 2026-09-29): reemplaza al
# mando en esas etapas. v2 segun SU BOCETO (corte de la familia de la paleta), medido en pixeles por 3 lecturas
# independientes y combinado (workflow medir-boceto-sensor):
#   BORDE levantado -> RANURA hundida = CINTA DE LUZ -> PLANO -> BOTON central que sobresale hacia la panza
#   (indica que se apoya ahi) ; atras, MEDIA ESFERA que marca desde donde se agarra.
# El diametro (13,1 cm) es el del sensor de Beltran en Unreal (/Game/BreathR); las demas medidas salen del boceto como
# fraccion de ese diametro.
# Todo con bevel (filetes tangentes en el perfil) y NORMALES EXACTAS (las del perfil revolucionado). Slots (variables por
# parte en el material):  0 Body (borde y canto)  1 Face (plano)  2 Button (boton)  3 Ring (cinta de luz)  4 Grip (media esfera)
# + SM_BioSensorWaves_SC: cilindro abierto que sale de la cinta de luz hacia la panza; su material dibuja AROS suaves,
#   seguidos, que viajan y se apagan pronto. UV: U alrededor, V a lo largo (0 en el sensor, 1 lejos).
# Marco: eje = Z; la cara de la panza mira a -Z (el boton asoma hacia -Z); origen en el centro del PLANO.
# Uso: blender --background --python gen_bio_sensor.py -- <dir_salida>
import math
import os
import sys
import traceback

import bmesh
import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else "."
NAME = "SM_BioSensor_SC"
D = 190.0                       # mm: Beltran, 2026-09-29: "18-20 cm de diametro, no mas de 5 de profundidad" (todo el objeto)
# ---- proporciones del boceto (fraccion del diametro); ver bio-sensor.md ----
K = {                           # radiales: medianas de 3 lecturas del boceto; ALTURAS achicadas a pedido (total 4,8 cm con D 19 cm)
    "body_t": 0.116,            # espesor del cuerpo: tope del borde -> cara trasera
    "rim_up": 0.032,            # cuanto sube el borde (labio) sobre el plano
    "rim_w": 0.138,             # ancho radial del labio (reborde redondeado)
    "groove_w": 0.069,          # ancho de la ranura (cinta de luz): rectangular, fondo plano
    "groove_d": 0.032,          # profundidad de la ranura bajo el plano
    "btn_base": 0.248,          # diametro de la base del boton (flancos ~25 grados)
    "btn_top": 0.117,           # diametro del tope del boton
    "btn_h": 0.08,              # alto del boton sobre la loma central (Beltran: "que salga mas, para incrustarlo en el estomago")
    "plat_h": 0.047,            # la parte central (adentro de la cinta) sube en loma hasta la base del boton
    "dome_d": 0.32,            # diametro de la media esfera (paredes casi verticales al salir)
    "dome_h": 0.116,            # alto de la media esfera bajo la cara trasera (achatada: 0,85 del semiancho)
    "wave_len": 0.36,           # los aros llegan hasta 0,35 D del plano (no tan lejos)
    "wave_r_far": 1.0,          # suben casi como un cilindro, sin abrirse
}
F_RIM_OUT = 7.0                 # mm: el labio es un reborde REDONDEADO
F_BACK = 10.0                   # mm: canto de atras con radio grande (boceto ~0,08 D)
F_RIM_IN = 2.0                  # mm: labio hacia la ranura (casi vivo)
F_GROOVE = 0.6                  # mm: fondo de la ranura
F_PLANE = 1.0                   # mm: plano -> ranura
F_BTN_TOP = 3.0                 # mm: tope del boton
F_BTN_BASE = 2.5                # mm: base del boton (concavo)
F_DOME = 5.0                    # mm: media esfera -> cara trasera (concavo)
TIP_FRAC = 0.62                 # circulo de luz de la punta: fraccion del radio del tope del boton
TIP_D = 1.0                     # mm que se hunde el circulo de luz
F_TIP = 0.5
BACK_GAP = 4.0                  # mm entre la media esfera y el aro de luz de atras
BACK_W = 7.0                    # mm de ancho del aro de atras
BACK_D = 5.0                    # mm de profundidad del aro de atras
F_BACK_RING = 0.8
SEG = 72
ARC_STEP = math.radians(15.0)
WAVE_SEG, WAVE_ROWS = 64, 40


def dims():
    R = D / 2
    d = {k: v * D for k, v in K.items() if k not in ("wave_r_far",)}
    rim_top = d["rim_up"]                   # alturas h hacia la panza (+) ; plano en h = 0
    back = rim_top - d["body_t"]
    groove_out = R - d["rim_w"]
    groove_in = groove_out - d["groove_w"]
    return R, d, rim_top, back, groove_in, groove_out


def fillet_poly(P):
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
        t = min(rf * math.tan(abs(turn) / 2), 0.49 * l1, 0.49 * l2)
        rr = t / math.tan(abs(turn) / 2)
        T1 = (r - d1[0] * t, z - d1[1] * t)
        sgn = 1.0 if turn > 0 else -1.0
        nrm = (-d1[1] * sgn, d1[0] * sgn)
        C = (T1[0] + nrm[0] * rr, T1[1] + nrm[1] * rr)
        a0 = math.atan2(T1[1] - C[1], T1[0] - C[0])
        steps = max(2, int(math.ceil(abs(turn) / ARC_STEP * min(1.0, max(0.35, rr / 3.0)))))
        for s in range(steps + 1):
            ang = a0 + turn * s / steps
            out.append((C[0] + rr * math.cos(ang), C[1] + rr * math.sin(ang), part))
    return out


def profile():
    """Perfil (r, z, parte) en mm con z = -h (la panza hacia -Z): del centro del boton hacia afuera, borde, canto, cara
    trasera y media esfera de vuelta al eje."""
    R, d, rim_top, back, gi, go = dims()
    bt, bb, ph = d["btn_top"] / 2, d["btn_base"] / 2, d["plat_h"]
    base = rim_top                          # Beltran: el vertice que baja a la cinta queda A LA ALTURA DEL BORDE
    bh = base + ph + d["btn_h"]
    tr, td = bt * TIP_FRAC, TIP_D           # circulo de luz en la punta (disco apenas hundido)
    rd = d["dome_d"] / 2
    bgi = rd + BACK_GAP                     # aro de luz de atras: hendidura alrededor de la media esfera
    bgo = bgi + BACK_W
    P = [(0.0, -(bh - td), 0.0, "TipLight"), (tr, -(bh - td), F_TIP, "TipLight"), (tr, -bh, F_TIP, "Button"),
         (bt, -bh, F_BTN_TOP, "Button"), (bb, -(base + ph), F_BTN_BASE, "Face")]
    nl = 10
    for k in range(1, nl):                  # loma: de la base del boton (pendiente 0) al borde de la cinta
        t = k / nl
        P.append((bb + (gi - bb) * t, -(base + ph * (1 - t * t)), 0.0, "Face"))
    P += [(gi, -base, F_PLANE, "Face"), (gi, 0.0, 0.0, "Ring"),       # la luz: solo el fondo de la hendidura
          (gi, d["groove_d"], F_GROOVE, "Ring"), (go, d["groove_d"], F_GROOVE, "Ring"), (go, 0.0, 0.0, "Body"),
          (go, -rim_top, F_RIM_IN, "Body"), (R, -rim_top, F_RIM_OUT, "Body"), (R, -back, F_BACK, "Body"),
          (bgo, -back, F_BACK_RING, "BackRing"), (bgo, -back + BACK_D, F_GROOVE, "BackRing"),
          (bgi, -back + BACK_D, F_GROOVE, "BackRing"), (bgi, -back, F_BACK_RING, "Body"),
          (rd, -back, F_DOME, "Grip")]
    hd = d["dome_h"]
    n = 14
    for k in range(1, n + 1):
        a = (math.pi / 2) * k / n                      # media esfera (elipsoide rd x hd)
        P.append((rd * math.cos(a), -back + hd * math.sin(a), 0.0, "Grip"))
    pts = fillet_poly(P)
    pts[-1] = (0.0, pts[-1][1], "Grip")
    return pts


def normals2d(pts):
    out = []
    for i in range(len(pts)):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, len(pts) - 1)]
        tr, tz = b[0] - a[0], b[1] - a[1]
        m = math.hypot(tr, tz)
        out.append((tz / m, -tr / m))
    return out


def revolve(name, pts, parts, nseg):
    """Solido de revolucion: quads + abanicos en los polos, UV (angulo, largo de arco) y NORMALES EXACTAS: cada vertice
    sale de un punto del perfil, y su normal es la del perfil girada a su angulo."""
    nrm2 = normals2d(pts)
    s = [0.0]
    for i in range(1, len(pts)):
        s.append(s[-1] + math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))
    L = s[-1]
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    rows, vnorm = [], []
    for i, (r, z, _) in enumerate(pts):
        nr, nz = nrm2[i]
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
    for i in range(len(pts) - 1):
        mi = parts.index(pts[i][2])
        A, B = rows[i], rows[i + 1]
        for j in range(nseg):
            j2 = (j + 1) % nseg
            u0, u1 = j / nseg, (j + 1) / nseg
            if len(A) == 1:      # 🔴 polo de arranque: orden inverso al de los quads (si no, anillo de caras dadas vuelta)
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
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.normals_split_custom_set_from_vertices(vnorm)
    return me, flips


def waves_mesh():
    """Cilindro abierto desde la cinta de luz hacia la panza: V = 0 en el plano, 1 al final."""
    R, d, rim_top, back, gi, go = dims()
    r0 = (gi + go) / 2
    r1 = r0 * K["wave_r_far"]
    z0, z1 = -rim_top, -rim_top - d["wave_len"]
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    rows = []
    for i in range(WAVE_ROWS + 1):
        v = i / WAVE_ROWS
        r = r0 + (r1 - r0) * v
        z = z0 + (z1 - z0) * v
        rows.append([bm.verts.new((r * math.cos(2 * math.pi * j / WAVE_SEG) / 1000.0, r * math.sin(2 * math.pi * j / WAVE_SEG) / 1000.0, z / 1000.0))
                     for j in range(WAVE_SEG)])
    for i in range(WAVE_ROWS):
        for j in range(WAVE_SEG):
            j2 = (j + 1) % WAVE_SEG
            f = bm.faces.new((rows[i][j], rows[i][j2], rows[i + 1][j2], rows[i + 1][j]))
            for lp, t in zip(f.loops, ((j / WAVE_SEG, i / WAVE_ROWS), ((j + 1) / WAVE_SEG, i / WAVE_ROWS),
                                        ((j + 1) / WAVE_SEG, (i + 1) / WAVE_ROWS), (j / WAVE_SEG, (i + 1) / WAVE_ROWS))):
                lp[uvl].uv = t
    me = bpy.data.meshes.new(NAME.replace("BioSensor", "BioSensorWaves"))
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    return me


def export(ob, path):
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, apply_unit_scale=True, global_scale=1.0,
                             apply_scale_options='FBX_SCALE_NONE', object_types={'MESH'}, mesh_smooth_type='FACE',
                             use_tspace=True, colors_type='NONE', add_leaf_bones=False, bake_anim=False, path_mode='STRIP')


BODY_PARTS = ("Body", "Face", "Ring", "Grip", "BackRing")
BUTTON_PARTS = ("Button", "TipLight")


def split_profile(pts):
    """2026-09-30 (aparicion "luz primero"): el BOTON es una malla aparte para que asome desde adentro del cuerpo.
    Corte donde empieza la loma (primer punto "Face"): el boton es el perfil hasta ahi (abierto abajo) y el cuerpo arranca
    con una TAPA plana desde el eje (escondida adentro del boton en reposo) y sigue igual. En reposo se ve identico."""
    k = next(i for i, p in enumerate(pts) if p[2] == "Face")
    button = pts[:k + 1]
    body = [(0.0, pts[k][1], "Face")] + pts[k:]
    return body, button


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    body_pts, button_pts = split_profile(profile())
    obs, flips_all = [], {}
    for name, pts, parts in ((NAME, body_pts, BODY_PARTS), (NAME.replace("_SC", "_Button_SC"), button_pts, BUTTON_PARTS)):
        me, flips = revolve(name, pts, parts, SEG)
        ob = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(ob)
        for p in parts:
            me.materials.append(bpy.data.materials.new("M_BioSensor_" + p))
        obs.append((ob, parts))
        flips_all[name] = flips
    ob, parts = obs[0]
    me = ob.data
    flips = flips_all
    wm = waves_mesh()
    wm.materials.append(bpy.data.materials.new("M_BioSensor_Waves"))
    wo = bpy.data.objects.new(wm.name, wm)
    bpy.context.scene.collection.objects.link(wo)
    info = {}
    bo = obs[1][0]
    for o in (ob, bo, wo):
        bm = bmesh.new()
        bm.from_mesh(o.data)
        info[o.name] = {"tris": sum(len(f.verts) - 2 for f in bm.faces), "abiertas": sum(1 for e in bm.edges if not e.is_manifold),
                        "degeneradas": sum(1 for f in bm.faces if f.calc_area() < 1e-10)}
        pp = dict(obs).get(o)
        if pp:
            info[o.name]["por_parte"] = dict(zip(pp, [sum(1 for f in bm.faces if f.material_index == k) for k in range(len(pp))]))
        bm.free()
    info["dadas_vuelta"] = flips
    xs = [v.co for v in me.vertices]
    info["caja_cm"] = [[round(min(c[k] for c in xs) * 100, 2) for k in range(3)], [round(max(c[k] for c in xs) * 100, 2) for k in range(3)]]
    os.makedirs(OUT, exist_ok=True)
    for o in (ob, bo, wo):
        export(o, os.path.join(OUT, o.name + ".fbx"))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, NAME + ".blend"))
    print("BIOSENSOR_OK", info)


try:
    main()
except BaseException as e:
    print("BIOSENSOR_FALLO", type(e).__name__, e)
    traceback.print_exc()
