# gen_demo_results.py - el CUADRO DE RESULTADOS de la DEMO (Barcelona Design Week, 2026-10-21): 1000 x 560 mm, visto a ~1,6 m, al final de
# cada experiencia (Breath, Draw). Misma familia que el cuadro de resultados de la Obra (gen_results.py, assets/results.md): LAMINA ENTERA
# translucida + el VIDRIO de cada ventana apoyado encima + ventanas enmarcadas como la del EEG, pero con el MARCO de la familia "marco con
# cinta de luz" (borde + canal con la cinta + labio), como los cuadros de la demo y el SHARE. Plano.
#   SM_DemoResults_Base_SC       marco: borde + CANAL con la CINTA DE LUZ + labio interior. Anillo CERRADO. Slots 0 Body · 1 Ring (la luz)
#   SM_DemoResults_Sheet_SC      la lamina: UNA cara entera (llega a la pared interior del marco), z 9. Slot 0 Sheet. UV 0..1 sobre la lamina
#   SM_DemoResults_Win{EEG,Pulse,Breath,Calm}_SC   las 4 ventanas, cada una YA EN SU LUGAR y doblada (origen = centro de la espalda del cuadro,
#                                como Base). Contorno de 4 mm hacia ADENTRO (z 9..13) + vidrio z 9,5. Slots 0 Frame · 1 Pane.
#                                UV0 del Pane = 0..1 sobre la ABERTURA, calculada ANTES de doblar, misma convencion que TextUV (+v arriba)
#   SM_DemoResults_Trace_SC      el trazo de luz de la aparicion "luz primero" (M_AppearTrace_SC). Slot 0 Trace (cinta abierta a proposito)
# Ventanas (mm desde el centro de la cara, +y arriba): EEG, pulso y respiracion = 600 x 150 en x -460..+140 (centro x -160), centros y +170, 0,
# -170; calma = 280 x 490 en x +180..+460 (centro x +320), centro y 0. Esquinas r 20.
# CURVATURA (CURVE_R, mm; default 1600; 0 = plano; --curve R en la linea de comandos): TODA la geometria se dobla alrededor del eje VERTICAL con los
# extremos hacia el usuario (+X de Unreal). R es el radio de la superficie del VIDRIO (z 9,5): el centro de la curva (el ojo) queda a R + 0,95 cm
# delante del origen, asi el vidrio queda a R del ojo en todo el ancho. El origen (centro de la espalda) no se mueve. Las UV se calculan ANTES de doblar.
# Ejes de CONSTRUCCION: acostado en XY, cara +Z, +Y = arriba, +X = derecha del espectador; mm. FBX (Unreal) PARADO, cara +X, arriba +Z, ancho por Y,
# origen = centro de la ESPALDA de la base. Unreal ESPEJA la Y: Y_UE = -(derecha).
# Uso (Python del SISTEMA, PIL): python gen_demo_results.py --tex <dir>                       contenidos DE MUESTRA (solo vista previa)
#                                python gen_demo_results.py --sheet <prefijo_vistas> <salida.png>
# Uso (Blender headless): blender --background --python gen_demo_results.py -- <dir> build
#                         blender --background --python gen_demo_results.py -- <dir> qc        lee los FBX de vuelta y mide
#                         blender --background <dir>/SM_DemoResults_SC.blend --python gen_demo_results.py -- <dir> render <prefijo> <dir_tex>
import functools
import math
import os
import sys
import traceback

A, B, RC = 500.0, 280.0, 60.0                 # semiejes y radio de esquina del contorno exterior: 1000 x 560
H_RIM = 15.0                                   # --- la misma seccion que toda la familia ---
F_OUT_TOP, F_OUT_BOT = 3.5, 3.0
RIM_W = 4.8
F_RIM_IN = 1.5
H_FLOOR = 6.0
H_LIGHT = 10.0
CH_IN = 10.2                                   # el canal llega a d = -10,2 (como la placa de los cuadros)
Z_LIP = 12.5                                   # altura del labio interior (la cinta queda hundida entre el borde y el labio)
LIP_W = 2.4
SHEET_Z = 9.0                                  # la lamina: bajo el labio (3,5 mm), sobre el piso del canal
SHEET_D = -(CH_IN + LIP_W) + 0.05              # llega a la pared interior del marco
WIN_RC, WIN_FW = 20.0, 4.0                     # esquinas de la ventana y contorno hacia ADENTRO (4 mm)
WIN_Z0, WIN_Z1 = SHEET_Z, SHEET_Z + 4.0        # el contorno se apoya en la lamina y asoma 4 mm
PANE_Z = SHEET_Z + 0.5                         # vidrio de la abertura, 0,5 mm sobre la lamina (los contenidos, desde SHEET_Z + 1)
CONTENT_Z = SHEET_Z + 1.0
WIDE = (600.0, 150.0)
TALL = (280.0, 490.0)
COLS = [("WinEEG", "wide", -160.0, 170.0), ("WinPulse", "wide", -160.0, 0.0), ("WinBreath", "wide", -160.0, -170.0),
        ("WinCalm", "tall", 320.0, 0.0)]       # (nombre, tamano, x del centro, y del centro) mm
N_ARC, N_ARC_WIN, STEP = 10, 8, 5000.0
STEP_X = 96.0                                   # paso de los tramos rectos HORIZONTALES (se doblan); los verticales no se subdividen
CURVE_R = 1600.0                                # mm; radio de la superficie del VIDRIO de las ventanas. 0 = plano
CURVE_Z = PANE_Z                                # profundidad (mm) de la superficie "neutra" de la curva
TRACE_D, TRACE_HW = -7.0, 6.5
ARC45, ARC30 = math.radians(45.0), math.radians(30.0)
if "--curve" in sys.argv:
    CURVE_R = float(sys.argv[sys.argv.index("--curve") + 1])
FONT = r"C:/Users/beltr/AppData/Local/Microsoft/Windows/Fonts/Avenir Book.ttf"
FONT_H = r"C:/Users/beltr/AppData/Local/Microsoft/Windows/Fonts/Avenir Heavy.ttf"


# ------------------------------------------------------------------------------------------ contenidos de muestra (Python del sistema)
def make_tex(out):
    """Contenidos DE MUESTRA, solo para la vista previa (RGBA, 2 px/mm de la abertura). El Director dibuja los reales."""
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
    PXMM = 2.0
    W1, H1 = int((WIDE[0] - 2 * WIN_FW) * PXMM), int((WIDE[1] - 2 * WIN_FW) * PXMM)
    W2, H2 = int((TALL[0] - 2 * WIN_FW) * PXMM), int((TALL[1] - 2 * WIN_FW) * PXMM)
    f_s = ImageFont.truetype(FONT, int(11 * PXMM / 0.72))
    f_b = ImageFont.truetype(FONT_H, int(150 * PXMM / 0.72))
    f_m = ImageFont.truetype(FONT, int(16 * PXMM / 0.72))

    def blur(im, r):
        return im.filter(ImageFilter.GaussianBlur(r))

    def glowline(base, pts, col, w):
        g = Image.new("RGBA", base.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(g)
        d.line(pts, fill=col + (255,), width=w, joint="curve")
        base.alpha_composite(blur(g, w * 2.2))
        base.alpha_composite(g)

    rng = np.random.default_rng(3)
    # EEG: cuatro trazas suaves en violeta
    im = Image.new("RGBA", (W1, H1), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((14, 8), "NEURAL ACTIVITY", font=f_s, fill=(190, 175, 235, 200))
    for k, col in enumerate(((170, 140, 255), (140, 120, 235), (200, 170, 255), (120, 150, 255))):
        x = np.linspace(0, 1, 400)
        y = sum(rng.uniform(0.2, 1.0) * np.sin(2 * math.pi * rng.uniform(1.2, 7) * x + rng.uniform(0, 6)) for _ in range(4)) / 4
        pts = [(int(xx * (W1 - 20) + 10), int(H1 * 0.58 + (yy * 0.30 + (k - 1.5) * 0.04) * H1)) for xx, yy in zip(x, y)]
        glowline(im, pts, col, 3)
    im.save(os.path.join(out, "S_eeg.png"))
    # pulso
    im = Image.new("RGBA", (W1, H1), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((14, 8), "PULSE", font=f_s, fill=(255, 175, 165, 200))
    pts = []
    for i in range(1200):
        t = (i / 1200) * 6.0
        ph = t % 1.0
        v = 0.0
        v += 0.12 * math.exp(-((ph - 0.20) / 0.05) ** 2) - 0.12 * math.exp(-((ph - 0.40) / 0.015) ** 2)
        v += 1.0 * math.exp(-((ph - 0.43) / 0.012) ** 2) - 0.25 * math.exp(-((ph - 0.47) / 0.015) ** 2)
        v += 0.22 * math.exp(-((ph - 0.70) / 0.06) ** 2)
        pts.append((int(10 + i / 1200 * (W1 - 20)), int(H1 * 0.78 - v * H1 * 0.55)))
    glowline(im, pts, (255, 120, 110), 3)
    im.save(os.path.join(out, "S_pulse.png"))
    # circulos por ciclo de respiracion
    im = Image.new("RGBA", (W1, H1), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((14, 8), "BREATH CYCLES", font=f_s, fill=(180, 235, 225, 200))
    n = 9
    for k in range(n):
        r = int(H1 * (0.13 + 0.10 * (0.5 + 0.5 * math.sin(k * 1.1 + 0.4))))
        cx, cy = int(W1 * (k + 0.5) / n), int(H1 * 0.62)
        g = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(g).ellipse((cx - r, cy - r, cx + r, cy + r), outline=(130, 235, 215, 255), width=4)
        im.alpha_composite(blur(g, 6))
        im.alpha_composite(g)
    im.save(os.path.join(out, "S_cycles.png"))
    # indice de calma
    im = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((W2 / 2, 40), "CALM INDEX", font=f_m, fill=(255, 215, 170, 230), anchor="mt")
    g = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(g).text((W2 / 2, H2 * 0.50), "82", font=f_b, fill=(255, 200, 140, 255), anchor="mm")
    im.alpha_composite(blur(g, 10))
    im.alpha_composite(g)
    d.rounded_rectangle((W2 * 0.18, H2 * 0.82, W2 * 0.82, H2 * 0.82 + 14), radius=7, fill=(255, 215, 170, 70))
    d.rounded_rectangle((W2 * 0.18, H2 * 0.82, W2 * (0.18 + 0.64 * 0.82), H2 * 0.82 + 14), radius=7, fill=(255, 200, 140, 255))
    im.save(os.path.join(out, "S_calm.png"))
    return ["S_eeg.png", "S_pulse.png", "S_cycles.png", "S_calm.png"]


def make_sheet(pre, out):
    from PIL import Image, ImageDraw, ImageFont
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 16)
    items = [("%s_frente.png" % pre, "de frente, a ~1,6 m (contenidos de muestra solo para la vista previa)"),
             ("%s_oblicua.png" % pre, "oblicua: el marco, la cinta de luz, la lamina y los vidrios de las ventanas"),
             ("%s_arriba.png" % pre, "vista desde arriba: la curva (CURVE_R %d mm; el centro de la curva esta en el ojo, a 1,6 m)" % CURVE_R),
             ("%s_vacio.png" % pre, "sin contenidos: las 4 ventanas vacias (lo que entrega Blender)")]
    cells = [(Image.open(p).convert("RGB"), lab) for p, lab in items]
    LAB = 30
    W = max(c.width for c, _ in cells)
    sheet = Image.new("RGB", (W, sum(c.height + LAB for c, _ in cells)), (0, 0, 0))
    d = ImageDraw.Draw(sheet)
    y = 0
    for im, lab in cells:
        d.text((10, y + 7), lab, font=font, fill=(235, 235, 235))
        sheet.paste(im, (0, y + LAB))
        y += im.height + LAB
    sheet.save(out)
    print("SHEET_OK", sheet.size)


if "--tex" in sys.argv and "--" not in sys.argv:
    d_ = sys.argv[sys.argv.index("--tex") + 1]
    os.makedirs(d_, exist_ok=True)
    print("TEX_OK", make_tex(d_))
    sys.exit(0)
if "--sheet" in sys.argv and "--" not in sys.argv:
    i = sys.argv.index("--sheet")
    make_sheet(sys.argv[i + 1], sys.argv[i + 2])
    sys.exit(0)
if "bpy" not in sys.modules and "--" not in sys.argv:
    sys.exit(0)

# ------------------------------------------------------------------------------------------ Blender
import bmesh                                              # noqa: E402
import bpy                                                # noqa: E402
from mathutils import Matrix, Vector                      # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import revolve_lib as RL                                  # noqa: E402
import anim_luz_objects as LZ                             # noqa: E402  (trace_mesh)

RR = RL.rrect_outline
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else "."
MODE = argv[1] if len(argv) > 1 else "build"
R_UE = Matrix(((0.0, 0.0, 1.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0))).to_4x4()    # cara +Z -> +X, arriba +Y -> +Z
R_WEB = Matrix(((1.0, 0.0, 0.0), (0.0, 0.0, -1.0), (0.0, 1.0, 0.0))).to_4x4()  # cara +Z -> -Y, arriba +Y -> +Z
MATS = {}


def base_profile():
    """Anillo CERRADO: borde + canal con la cinta (Ring) + labio interior + pared interior hasta la espalda."""
    P = [(-6.0, 0.0, 0.0, "Body"), (0.0, 0.0, F_OUT_BOT, "Body"), (0.0, H_RIM, F_OUT_TOP, "Body"),
         (-RIM_W, H_RIM, F_RIM_IN, "Body"), (-RIM_W, H_LIGHT, 0.0, "Ring"), (-RIM_W, H_FLOOR, 1.0, "Ring"),
         (-CH_IN, H_FLOOR, 0.7, "Ring"), (-CH_IN, Z_LIP, 1.0, "Body"), (-(CH_IN + LIP_W), Z_LIP, 0.8, "Body"),
         (-(CH_IN + LIP_W), 0.0, 0.8, "Body"), (-6.0, 0.0, 0.0, "Body")]
    return RL.fillet_poly(P, ARC30)[:-1]


def frame_profile():
    """Contorno de la ventana: anillo de 4 mm hacia ADENTRO, z WIN_Z0..WIN_Z1 (frente filete 1,2; dorso 0,3)."""
    mid = -WIN_FW / 2
    P = [(mid, WIN_Z0, 0.0, "Frame"), (0.0, WIN_Z0, 0.3, "Frame"), (0.0, WIN_Z1, 1.2, "Frame"), (-WIN_FW, WIN_Z1, 1.2, "Frame"),
         (-WIN_FW, WIN_Z0, 0.3, "Frame"), (mid, WIN_Z0, 0.0, "Frame")]
    return RL.fillet_poly(P, ARC45)[:-1]


def outline_xy(a, b, rc, d, n_arc=10, step_x=1.0e6, step_y=1.0e6):
    """Copia de revolve_lib.rrect_outline con paso propio por eje: los tramos HORIZONTALES se subdividen (se doblan), los verticales no."""
    ex, ey = a - rc, b - rc
    R = rc + d
    ns_top = max(1, int(round(ex / step_x)))
    ns_side = max(1, int(round(2 * ey / step_y)))
    pts = []

    def line(p0, p1, n, nx, ny):
        for k in range(n):
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


# ---- la curva: doblar alrededor del eje vertical (y de construccion). x = lateral, z = profundidad
def bend_xz(x, z):
    """(x, z) en mm -> (x', z', theta, q). Radio R en la superficie del vidrio (z = CURVE_Z); el origen (espalda, centro) no se mueve;
    el centro de la curva (el ojo) queda en z = R + CURVE_Z, x = 0."""
    R = CURVE_R
    th = x / R
    r = R + CURVE_Z - z
    return r * math.sin(th), (R + CURVE_Z) - r * math.cos(th), th, r / R


def bend_normal(n, th, q):
    nx, ny, nz = n
    a, b = nz, nx / q                                       # (profundidad, lateral)
    return Vector((-a * math.sin(th) + b * math.cos(th), ny, a * math.cos(th) + b * math.sin(th))).normalized()


def bend_bm(bm, vnl):
    if CURVE_R <= 0:
        return
    for v in bm.verts:
        x, y, z = (c * 1000.0 for c in v.co)
        x2, z2, th, q = bend_xz(x, z)
        v.co = (x2 / 1000.0, y / 1000.0, z2 / 1000.0)
        v[vnl] = tuple(bend_normal(Vector(v[vnl]).normalized(), th, q))


def new_bm():
    bm = bmesh.new()
    return bm, bm.loops.layers.uv.new("UVMap"), bm.verts.layers.float_vector.new("vn")


def sweep_bm(bm, uv0, vnl, prof, parts, a, b, rc, n_arc, cx=0.0, cy=0.0, closed=True):
    """Barre el perfil (d, h, parte) en mm a lo largo del rectangulo redondeado (centro cx, cy), con normales EXACTAS en la capa de
    vertices 'vn' (viajan con los cortes). Los tramos horizontales se subdividen cada STEP_X si hay curva."""
    outline = functools.partial(outline_xy, n_arc=n_arc, step_x=STEP_X if CURVE_R > 0 else 1.0e6)
    nrm2 = RL.normals2d(prof, closed)
    rows = []
    for i, (d, h, _) in enumerate(prof):
        nr, nz = nrm2[i]
        row = []
        for (x, y, nx, ny) in outline(a, b, rc, d):
            v = bm.verts.new(((x + cx) / 1000.0, (y + cy) / 1000.0, h / 1000.0))
            v[vnl] = (nr * nx, nr * ny, nz)
            row.append(v)
        rows.append(row)
    m, npf = len(rows[0]), len(prof)
    for i in range(npf if closed else npf - 1):
        mi = parts.index(prof[i][2])
        r0, r1 = rows[i], rows[(i + 1) % npf]
        for j in range(m):
            j2 = (j + 1) % m
            f = bm.faces.new((r0[j], r1[j], r1[j2], r0[j2]))
            f.material_index = mi
            f.smooth = True
            v0, v1 = i / max(npf - 1, 1), (i + 1) / max(npf - 1, 1)
            for lp, t in zip(f.loops, ((j / m, v0), (j / m, v1), ((j + 1) / m, v1), ((j + 1) / m, v0))):
                lp[uv0].uv = t
    return rows


def fill_face(bm, vnl, a, b, rc, d, z, mi, n_arc, cx=0.0, cy=0.0):
    """Cara plana hacia +Z que llena el rectangulo redondeado (a, b, rc) desplazado d, centrado en (cx, cy). Los tramos rectos NO se
    subdividen: se cortan despues con island_cut (las UV se ponen por posicion antes de doblar)."""
    vs = []
    for (x, y, _, _) in outline_xy(a, b, rc, d, n_arc):
        v = bm.verts.new(((x + cx) / 1000.0, (y + cy) / 1000.0, z / 1000.0))
        v[vnl] = (0.0, 0.0, 1.0)
        vs.append(v)
    es = [bm.edges.new((vs[i], vs[(i + 1) % len(vs)])) for i in range(len(vs))]
    res = bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=es, normal=(0.0, 0.0, 1.0))
    for f in [g for g in res["geom"] if isinstance(g, bmesh.types.BMFace)]:
        f.normal_update()
        if f.normal.z < 0:
            f.normal_flip()
        f.material_index = mi
        f.smooth = True


def island_cut(bm, mi):
    """Parte con planos x = const las caras del slot mi (una ISLA: no comparte aristas con otra malla del bmesh, asi no quedan T) para que
    la cara plana siga la curva. Elige la grilla (cuerda de 64 a 96 mm) cuyos planos quedan mas lejos de los vertices de la isla."""
    if CURVE_R <= 0:
        return []
    faces0 = [f for f in bm.faces if f.material_index == mi]
    xs = sorted({round(v.co.x * 1000.0, 3) for f in faces0 for v in f.verts})
    lo, hi = xs[0] + 1.0, xs[-1] - 1.0
    best = None
    for G in [g * 0.5 for g in range(128, 193)]:                                   # 64 .. 96 mm
        for ph in (0.0, 0.5):
            pl = [(k + ph) * G for k in range(-20, 21) if lo < (k + ph) * G < hi]
            dmin = min((abs(p - x) for p in pl for x in xs if abs(p - x) > 1e-3), default=99.0)
            score = min(dmin, 3.0) - 0.02 * G
            if best is None or score > best[0]:
                best = (score, pl)
    for x in best[1]:
        faces = [f for f in bm.faces if f.material_index == mi]
        edges = list({e for f in faces for e in f.edges})
        verts = list({v for f in faces for v in f.verts})
        bmesh.ops.bisect_plane(bm, geom=verts + edges + faces, dist=1e-7, plane_co=(x / 1000.0, 0.0, 0.0), plane_no=(1.0, 0.0, 0.0))
    big = [f for f in bm.faces if f.material_index == mi and len(f.verts) > 4]
    if big:
        bmesh.ops.triangulate(bm, faces=big, quad_method='BEAUTY', ngon_method='BEAUTY')
    return [round(p, 2) for p in best[1]]


def set_uv(bm, uv0, mi, x0, y0, w, h):
    """UV0 por posicion sobre la cara PLANA (antes de doblar): 0..1 sobre el rectangulo (x0, y0, w, h) mm; +v arriba."""
    for f in bm.faces:
        if f.material_index == mi:
            for lp in f.loops:
                lp[uv0].uv = ((lp.vert.co.x * 1000.0 - x0) / w, (lp.vert.co.y * 1000.0 - y0) / h)


def finish_bm(bm, vnl, name):
    bm.normal_update()
    flips = sum(1 for f in bm.faces if f.normal.dot(sum((Vector(v[vnl]) for v in f.verts), Vector())) < 0)
    vns = [Vector(v[vnl]) for v in bm.verts]
    if any(n.length < 0.5 for n in vns):
        raise RuntimeError("normales sin interpolar en %s" % name)
    vn_list = [tuple(n.normalized()) for n in vns]
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.normals_split_custom_set([vn_list[me.loops[li].vertex_index] for li in range(len(me.loops))])
    me["flips"] = flips
    return me


def build_base():
    bm, uv0, vnl = new_bm()
    sweep_bm(bm, uv0, vnl, base_profile(), ("Body", "Ring"), A, B, RC, N_ARC)
    bend_bm(bm, vnl)
    return finish_bm(bm, vnl, "SM_DemoResults_Base_SC")


def build_sheet():
    bm, uv0, vnl = new_bm()
    fill_face(bm, vnl, A, B, RC, SHEET_D, SHEET_Z, 0, N_ARC)
    planes = island_cut(bm, 0)
    ax, by = A + SHEET_D, B + SHEET_D
    set_uv(bm, uv0, 0, -ax, -by, 2 * ax, 2 * by)
    bend_bm(bm, vnl)
    me = finish_bm(bm, vnl, "SM_DemoResults_Sheet_SC")
    me["planos"] = str(planes)
    return me


def build_window(name, kind, cx, cy):
    """Una ventana YA EN SU LUGAR (centro cx, cy mm) y doblada: origen = centro de la espalda del cuadro. Slots 0 Frame . 1 Pane.
    UV0 del Pane = 0..1 sobre la ABERTURA (la ventana menos 4 mm por lado), calculada ANTES de doblar; +v arriba."""
    w, h = WIDE if kind == "wide" else TALL
    bm, uv0, vnl = new_bm()
    sweep_bm(bm, uv0, vnl, frame_profile(), ("Frame", "Pane"), w / 2, h / 2, WIN_RC, N_ARC_WIN, cx, cy)
    fill_face(bm, vnl, w / 2, h / 2, WIN_RC, -WIN_FW + 0.05, PANE_Z, 1, N_ARC_WIN, cx, cy)
    planes = island_cut(bm, 1)
    set_uv(bm, uv0, 1, cx - (w / 2 - WIN_FW), cy - (h / 2 - WIN_FW), w - 2 * WIN_FW, h - 2 * WIN_FW)
    bend_bm(bm, vnl)
    me = finish_bm(bm, vnl, "SM_DemoResults_%s_SC" % name)
    me["planos"] = str(planes)
    return me


def build_trace():
    path = [(p[0], p[1]) for p in outline_xy(A, B, RC, TRACE_D, N_ARC, STEP_X / 2 if CURVE_R > 0 else 1.0e6)]
    me = LZ.trace_mesh({"path": path, "z": H_RIM, "hw": TRACE_HW, "face": 1.0}, "SM_DemoResults_Trace_SC")
    if CURVE_R > 0:
        for v in me.vertices:
            x, y, z = (c * 1000.0 for c in v.co)
            x2, z2, _, _ = bend_xz(x, z)
            v.co = (x2 / 1000.0, y / 1000.0, z2 / 1000.0)
    return me
def signed_volume(me, skip=()):
    """Volumen con signo de los triangulos que NO estan en los slots skip (las caras abiertas por diseno no tienen volumen)."""
    me.calc_loop_triangles()
    s = 0.0
    for t in me.loop_triangles:
        if me.polygons[t.polygon_index].material_index in skip:
            continue
        a, b, c = (me.vertices[i].co for i in t.vertices)
        s += a.dot(b.cross(c)) / 6.0
    return s


def stats(me, nparts, open_ok_slots=()):
    bm = bmesh.new()
    bm.from_mesh(me)
    open_all = [e for e in bm.edges if not e.is_manifold]
    r = {"tris": sum(len(f.verts) - 2 for f in bm.faces),
         "abiertas": sum(1 for e in open_all if not all(f.material_index in open_ok_slots for f in e.link_faces)),
         "abiertas_por_diseno": sum(1 for e in open_all if all(f.material_index in open_ok_slots for f in e.link_faces)),
         "degeneradas": sum(1 for f in bm.faces if f.calc_area() < 1e-10),
         "por_slot": [sum(1 for f in bm.faces if f.material_index == k) for k in range(nparts)]}
    bm.free()
    me.calc_loop_triangles()
    r["astillas_lt_0.01mm2"] = sum(1 for t in me.loop_triangles if t.area < 1e-8)
    r["dadas_vuelta"] = int(me.get("flips", 0))
    return r


def export_ue(me, path, tspace=True):
    m2 = me.copy()
    m2.transform(R_UE)
    ob = bpy.data.objects.new(me.name, m2)
    bpy.context.scene.collection.objects.link(ob)
    (RL.export_fbx if tspace else LZ.export_fbx)(ob, path)
    bpy.data.objects.remove(ob)
    bpy.data.meshes.remove(m2)


def pt_cm(x, y, z):
    """Punto de construccion (x derecha, y arriba, z profundidad; mm) YA DOBLADO -> (X profundidad, Y_UE, Z) en cm del marco de Unreal."""
    if CURVE_R > 0:
        x, z, _, _ = bend_xz(x, z)
    return [round(z / 10.0, 3), round(-x / 10.0, 3), round(y / 10.0, 3)]


def rects_cm():
    """Por ventana (cm, marco de Unreal, YA DOBLADO, sobre la superficie del vidrio z = PANE_Z): centro de la abertura, X/Y_UE de sus bordes
    izquierdo y derecho DEL ESPECTADOR (a media altura) y su alto. Y_UE = -(derecha del espectador)."""
    out = {}
    for nm, kind, cx, cy in COLS:
        w, h = WIDE if kind == "wide" else TALL
        aw, ah = w - 2 * WIN_FW, h - 2 * WIN_FW
        out[nm] = {"centro_abertura_XYZ": pt_cm(cx, cy, PANE_Z),
                   "borde_izq_espectador_XY": pt_cm(cx - aw / 2, cy, PANE_Z)[:2], "borde_der_espectador_XY": pt_cm(cx + aw / 2, cy, PANE_Z)[:2],
                   "Z": [round((cy - ah / 2) / 10, 2), round((cy + ah / 2) / 10, 2)], "abertura_plana_cm": [round(aw / 10, 2), round(ah / 10, 2)],
                   "ventana_borde_izq_der_XY": [pt_cm(cx - w / 2, cy, WIN_Z1)[:2], pt_cm(cx + w / 2, cy, WIN_Z1)[:2]],
                   "ventana_Z": [round((cy - h / 2) / 10, 2), round((cy + h / 2) / 10, 2)]}
    return out


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    base, sheet = build_base(), build_sheet()
    wins = {nm: build_window(nm, kind, cx, cy) for nm, kind, cx, cy in COLS}
    trace = build_trace()
    spec = [(base, ("Body", "Ring"), ()), (sheet, ("Sheet",), (0,))] + [(wins[nm], ("Frame", "Pane"), (1,)) for nm, _, _, _ in COLS] + \
           [(trace, ("Trace",), (0,))]
    info, meshes = {}, []
    for me, parts, ok in spec:
        for p in parts:
            if p not in MATS:
                MATS[p] = bpy.data.materials.new("M_DemoResults_" + p)
            me.materials.append(MATS[p])
        info[me.name] = stats(me, len(parts), ok)
        info[me.name]["volumen_partes_cerradas_mm3"] = round(signed_volume(me, ok) * 1e9) if len(ok) < len(parts) else None
        if me.get("planos"):
            info[me.name]["planos_de_corte_mm"] = me["planos"]
        meshes.append(me)
    os.makedirs(OUT, exist_ok=True)
    lo, hi = [1e9] * 3, [-1e9] * 3
    for me in meshes:
        export_ue(me, os.path.join(OUT, me.name + ".fbx"), tspace=me is not trace)
        m2 = me.copy()
        m2.transform(R_UE)
        xs = [v.co for v in m2.vertices]
        mn = [round(min(c[k] for c in xs) * 100, 3) for k in range(3)]
        mx = [round(max(c[k] for c in xs) * 100, 3) for k in range(3)]
        mn[1], mx[1] = -mx[1], -mn[1]                                  # Unreal espeja la Y: Y_UE = -Y_Blender
        info[me.name]["caja_UE_cm_min"], info[me.name]["caja_UE_cm_max"] = mn, mx
        lo, hi = [min(a, b) for a, b in zip(lo, mn)], [max(a, b) for a, b in zip(hi, mx)]
        bpy.data.meshes.remove(m2)
    col = bpy.context.scene.collection
    for me in meshes:                                  # .blend armado PARADO (orientacion de la web); todo YA en su lugar (origen comun)
        ob = bpy.data.objects.new(me.name.replace("SM_DemoResults_", "").replace("_SC", ""), me)
        col.objects.link(ob)
        ob.matrix_world = R_WEB.copy()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "SM_DemoResults_SC.blend"))
    unicas = sum(v["tris"] for v in info.values())
    print("DEMORESULTS_OK", info, "tris_total", unicas, "CURVE_R", CURVE_R)
    print("DEMORESULTS_RECTS_cm", rects_cm())
    hit_c = [round((a + b) / 2, 2) for a, b in zip(lo, hi)]
    hit_e = [round((b - a) / 2 + 0.2, 2) for a, b in zip(lo, hi)]
    print("DEMORESULTS_HIT_cm", {"caja_total_min": lo, "caja_total_max": hi, "centro": hit_c, "extension(+0,2)": hit_e,
                                 "ojo_centro_de_la_curva_XYZ": [round((CURVE_R + CURVE_Z) / 10.0, 2), 0.0, 0.0] if CURVE_R > 0 else None})
# ------------------------------------------------------------------------------------------ QC: lee los FBX de vuelta
def qc():
    res = {}
    spec = [("Base", ()), ("Sheet", (0,))] + [(nm, (1,)) for nm, _, _, _ in COLS] + [("Trace", (0,))]
    for nm, ok in spec:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.fbx(filepath=os.path.join(OUT, "SM_DemoResults_%s_SC.fbx" % nm))
        ob = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
        me = ob.data
        me.calc_loop_triangles()
        bm = bmesh.new()
        bm.from_mesh(me)
        areas = [t.area for t in me.loop_triangles]
        cn = me.corner_normals
        flipped = 0
        for p in me.polygons:
            s = Vector()
            for li in p.loop_indices:
                s += Vector(cn[li].vector)
            if p.normal.dot(s) < 0:
                flipped += 1
        xs = [v.co for v in me.vertices]
        open_all = [e for e in bm.edges if not e.is_manifold]
        res[nm] = {"tris": len(areas),
                   "abiertas": sum(1 for e in open_all if not all(f.material_index in ok for f in e.link_faces)),
                   "abiertas_por_diseno": sum(1 for e in open_all if all(f.material_index in ok for f in e.link_faces)),
                   "degeneradas(<1e-10m2)": sum(1 for a in areas if a < 1e-10), "astillas(<0.01mm2)": sum(1 for a in areas if a < 1e-8),
                   "area_min_mm2": round(min(areas) * 1e6, 4), "dadas_vuelta": flipped,
                   "volumen_partes_cerradas_mm3": round(signed_volume(me, ok) * 1e9) if nm not in ("Sheet", "Trace") else None,
                   "slots": [m.name for m in me.materials], "uv": [u.name for u in me.uv_layers],
                   "caja_cm_Y_de_Blender": [[round(min(c[k] for c in xs) * 100, 2) for k in range(3)], [round(max(c[k] for c in xs) * 100, 2) for k in range(3)]]}
        if ok:
            uvl = me.uv_layers["UVMap"]
            vals = [uvl.data[li].uv for p in me.polygons if p.material_index == ok[0] for li in p.loop_indices]
            res[nm]["uv0_slot%d_min_max" % ok[0]] = [[round(min(v[k] for v in vals), 4) for k in (0, 1)], [round(max(v[k] for v in vals), 4) for k in (0, 1)]]
        bm.free()
    print("DEMORESULTS_QC", res)
# ------------------------------------------------------------------------------------------ vista previa (render)
L_DIR = Vector((-0.35, -0.30, 0.88)).normalized()
SH = {"Ambient": 0.30, "Diffuse": 0.55, "Wrap": 0.4, "Fill": 0.25, "SelfGlow": 0.10}
LIGHT = (1.0, 0.72, 0.45)


def N_(nt, kind, **kw):
    n = nt.nodes.new(kind)
    for k, v in kw.items():
        setattr(n, k, v)
    return n


def M_(nt, op, a, b=None, c=None, clamp=False):
    n = N_(nt, "ShaderNodeMath", operation=op, use_clamp=clamp)
    for i, x in enumerate((a, b, c)):
        if x is None:
            continue
        if isinstance(x, (int, float)):
            n.inputs[i].default_value = x
        else:
            nt.links.new(x, n.inputs[i])
    return n.outputs[0]


def base_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    return m, nt, N_(nt, "ShaderNodeOutputMaterial")


def to_translucent(nt, out, shader, alpha):
    mix = N_(nt, "ShaderNodeMixShader")
    tr = N_(nt, "ShaderNodeBsdfTransparent")
    mix.inputs[0].default_value = alpha
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(shader, mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])


def shaded(name, albedo, alpha=1.0):
    m, nt, out = base_mat(name)
    em = N_(nt, "ShaderNodeEmission")
    if alpha >= 1.0:
        nt.links.new(em.outputs[0], out.inputs["Surface"])
    else:
        to_translucent(nt, out, em.outputs[0], alpha)
    geo = N_(nt, "ShaderNodeNewGeometry")
    dl = N_(nt, "ShaderNodeVectorMath", operation='DOT_PRODUCT')
    nt.links.new(geo.outputs["Normal"], dl.inputs[0])
    dl.inputs[1].default_value = L_DIR
    key = M_(nt, 'DIVIDE', M_(nt, 'ADD', dl.outputs["Value"], SH["Wrap"]), 1 + SH["Wrap"], clamp=True)
    dv = N_(nt, "ShaderNodeVectorMath", operation='DOT_PRODUCT')
    nt.links.new(geo.outputs["Normal"], dv.inputs[0])
    nt.links.new(geo.outputs["Incoming"], dv.inputs[1])
    fill = M_(nt, 'MAXIMUM', dv.outputs["Value"], 0.0)
    sep = N_(nt, "ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Normal"], sep.inputs[0])
    hemi = M_(nt, 'MULTIPLY_ADD', sep.outputs["Z"], 0.5, 0.5)
    shade = M_(nt, 'ADD', M_(nt, 'ADD', M_(nt, 'MULTIPLY', hemi, SH["Ambient"]), M_(nt, 'MULTIPLY', key, SH["Diffuse"])),
               M_(nt, 'ADD', M_(nt, 'MULTIPLY', fill, SH["Fill"]), SH["SelfGlow"]))
    comb = N_(nt, "ShaderNodeCombineXYZ")
    for i in range(3):
        nt.links.new(M_(nt, 'MULTIPLY', shade, albedo[i]), comb.inputs[i])
    nt.links.new(comb.outputs[0], em.inputs["Color"])
    return m


def light(name, gain=0.7):
    m, nt, out = base_mat(name)
    em = N_(nt, "ShaderNodeEmission")
    em.inputs["Color"].default_value = (LIGHT[0], LIGHT[1], LIGHT[2], 1)
    em.inputs["Strength"].default_value = gain
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    return m


def flat_translucent(name, color, alpha):
    m, nt, out = base_mat(name)
    em = N_(nt, "ShaderNodeEmission")
    em.inputs["Color"].default_value = (color[0], color[1], color[2], 1)
    to_translucent(nt, out, em.outputs[0], alpha)
    return m


def content_mat(name, png):
    m, nt, out = base_mat(name)
    em = N_(nt, "ShaderNodeEmission")
    tex = N_(nt, "ShaderNodeTexImage")
    tex.image = bpy.data.images.load(png)
    tex.extension = 'CLIP'
    uv = N_(nt, "ShaderNodeUVMap", uv_map="UVMap")
    nt.links.new(uv.outputs["UV"], tex.inputs["Vector"])
    nt.links.new(tex.outputs["Color"], em.inputs["Color"])
    mix = N_(nt, "ShaderNodeMixShader")
    tr = N_(nt, "ShaderNodeBsdfTransparent")
    nt.links.new(tex.outputs["Alpha"], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return m


def backdrop():
    """Un fondo tipo Hall: degradado calido-oscuro, para que se vea la translucidez de la lamina."""
    me = bpy.data.meshes.new("Fondo")
    me.from_pydata([(-6.0, -4.0, -0.35), (6.0, -4.0, -0.35), (6.0, 4.0, -0.35), (-6.0, 4.0, -0.35)], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new(name="UVMap")
    for i, t in enumerate(((0, 0), (1, 0), (1, 1), (0, 1))):
        uv.data[i].uv = t
    ob = bpy.data.objects.new("Fondo", me)
    bpy.context.scene.collection.objects.link(ob)
    m, nt, out = base_mat("M_Fondo")
    em = N_(nt, "ShaderNodeEmission")
    ramp = N_(nt, "ShaderNodeValToRGB")
    uvn = N_(nt, "ShaderNodeUVMap", uv_map="UVMap")
    sep = N_(nt, "ShaderNodeSeparateXYZ")
    nt.links.new(uvn.outputs["UV"], sep.inputs[0])
    nt.links.new(M_(nt, 'ADD', M_(nt, 'MULTIPLY', sep.outputs["X"], 0.7), M_(nt, 'MULTIPLY', sep.outputs["Y"], 0.3)), ramp.inputs["Fac"])
    ramp.color_ramp.elements[0].color = (0.40, 0.34, 0.27, 1)
    ramp.color_ramp.elements[1].color = (0.05, 0.06, 0.09, 1)
    nt.links.new(ramp.outputs["Color"], em.inputs["Color"])
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    me.materials.append(m)


def content_quad(nm, cx, cy, w, h, png):
    """El contenido de muestra sobre la abertura, doblado como el vidrio (a CONTENT_Z), UV 0..1."""
    nx = max(2, int(w / 20))
    ww, hh = (w - 2 * WIN_FW) / 2, (h - 2 * WIN_FW) / 2
    verts, faces, uvs = [], [], []
    for i in range(nx + 1):
        x = cx - ww + 2 * ww * i / nx
        for y in (cy - hh, cy + hh):
            x2, z2 = (x, CONTENT_Z) if CURVE_R <= 0 else bend_xz(x, CONTENT_Z)[:2]
            verts.append((x2 / 1000.0, y / 1000.0, z2 / 1000.0))
            uvs.append((i / nx, 0.0 if y < cy else 1.0))
    for i in range(nx):
        faces.append((2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1))
    me = bpy.data.meshes.new("R_c_" + nm)
    me.from_pydata(verts, [], faces)
    uv = me.uv_layers.new(name="UVMap")
    for p in me.polygons:
        for li in p.loop_indices:
            uv.data[li].uv = uvs[me.loops[li].vertex_index]
    ob = bpy.data.objects.new("R_" + nm + "_content", me)
    bpy.context.scene.collection.objects.link(ob)
    me.materials.append(content_mat("R_tex_" + nm, png))


def build_scene(with_content, tex_dir):
    for o in [o for o in bpy.data.objects if o.name.startswith("R_")]:
        bpy.data.objects.remove(o)
    mats = {"Body": shaded("R_Body", (0.62, 0.56, 0.48)), "Ring": light("R_Ring", 0.8),
            "Sheet": flat_translucent("R_Sheet", (0.03, 0.04, 0.06), 0.62), "Frame": shaded("R_Frame", (0.62, 0.56, 0.48), 0.5),
            "Pane": flat_translucent("R_Pane", (0.01, 0.012, 0.02), 0.32)}
    texs = {"WinEEG": "S_eeg.png", "WinPulse": "S_pulse.png", "WinBreath": "S_cycles.png", "WinCalm": "S_calm.png"}

    def inst(name):
        o = bpy.data.objects[name]
        ob = bpy.data.objects.new("R_" + name, o.data)
        bpy.context.scene.collection.objects.link(ob)
        for i, s in enumerate(ob.material_slots):
            s.link = 'OBJECT'
            s.material = mats[o.data.materials[i].name.replace("M_DemoResults_", "").split(".")[0]]
    inst("Base")
    inst("Sheet")
    for nm, kind, cx, cy in COLS:
        inst(nm)
        if with_content:
            w, h = (WIDE if kind == "wide" else TALL)
            content_quad(nm, cx, cy, w, h, os.path.join(tex_dir, texs[nm]))


def render():
    pre, tex_dir = argv[2], argv[3]
    scn = bpy.context.scene
    for k in ["Base", "Sheet", "Trace"] + [c[0] for c in COLS]:
        bpy.data.objects[k].hide_render = True
    w = bpy.data.worlds.new("Negro")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)
    scn.world = w
    scn.render.engine = 'CYCLES'
    scn.cycles.samples = 64
    scn.cycles.transparent_max_bounces = 24
    scn.view_settings.view_transform = 'Standard'
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = 'OPTIX'
        prefs.get_devices()
        for dv in prefs.devices:
            dv.use = dv.type == 'OPTIX'
        scn.cycles.device = 'GPU'
    except Exception:
        pass
    backdrop()
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    scn.collection.objects.link(cam)
    scn.camera = cam
    cam.data.lens = 50
    outs = []
    eye_z = (CURVE_R + CURVE_Z) / 1000.0 if CURVE_R > 0 else 1.6                    # el ojo = el centro de la curva
    tgt = Vector((0.0, 0.0, 0.0105))

    def shot(path, loc, target, res, ortho=None):
        scn.render.resolution_x, scn.render.resolution_y = res
        cam.data.type = 'ORTHO' if ortho else 'PERSP'
        if ortho:
            cam.data.ortho_scale = ortho
        cam.location = loc
        cam.rotation_euler = (target - loc).to_track_quat('-Z', 'Y').to_euler()
        scn.render.filepath = path
        bpy.ops.render.render(write_still=True)
        outs.append(path)
    build_scene(True, tex_dir)
    shot(pre + "_frente.png", Vector((0.0, 0.0, eye_z)), tgt, (1600, 960))              # de frente, desde el ojo
    shot(pre + "_oblicua.png", Vector((0.55, -1.15, 1.05)), Vector((0.0, 0.0, 0.03)), (1600, 960))
    shot(pre + "_arriba.png", Vector((0.0, 2.0, 0.04)), Vector((0.0, 0.0, 0.04)), (1600, 460), ortho=1.25)   # desde arriba: el arco
    build_scene(False, tex_dir)
    shot(pre + "_vacio.png", Vector((0.0, 0.0, eye_z)), tgt, (1600, 960))
    print("DEMORESULTS_RENDER_OK", outs)


if __name__ == "__main__":
    try:
        {"build": main, "qc": qc, "render": render}[MODE]()
    except BaseException as e:
        print("DEMORESULTS_FALLO", type(e).__name__, e)
        traceback.print_exc()