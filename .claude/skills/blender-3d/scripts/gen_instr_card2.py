# gen_instr_card2.py - el PANEL DE INSTRUCCIONES v2 de la demo (Barcelona Design Week, 2026-10-21): imagen CUADRADA a la izquierda,
# texto a la derecha, 16:9 y CURVO hacia el usuario. Misma familia y MISMA seccion que gen_instr_card.py (marco + canal con cinta de
# luz + placa; el panel entero es el boton). El original queda intacto.
#   SM_InstrCard2_Base_SC    borde redondeado + CANAL con la CINTA DE LUZ. Body · Ring. Anillo CERRADO (sin tapas: la placa lo tapa)
#   SM_InstrCard2_Plate_SC   la placa (+1 mm hover, -4 mm al apretar): 0 PlateSide · 1 PlateTop (UV1 TextUV = tope entero) ·
#                            2 PlateImage (la ventana de la imagen, UV0 = 0..1 sobre el cuadrado) · 3 WinRing (cinta de luz del marquito)
#   SM_InstrCard2_Slider_SC  aro plano transparente abajo y afuera (UV0.x = fraccion del perimetro, horario desde arriba)
#   SM_InstrCard2_Trace_SC   el trazo de luz de la aparicion "luz primero" (M_AppearTrace_SC)
#   T_Instr2_<Breath|Draw>_P<n>.png      las 6 paginas (mascaras blanco/negro del tope; el texto va SOLO a la derecha de la ventana)
#   T_DemoInstrImg_<Breath|Draw>_<n>.png las 6 imagenes de muestra (RGB 1024 x 1024; Beltran las reemplaza por fotos)
# CURVATURA (CURVE_R, mm; 0 = plano): TODA la geometria se dobla alrededor del eje VERTICAL con los extremos hacia el usuario (+X de
# Unreal). El radio es el de la CARA de la placa (17,7 mm de profundidad): leer a esa distancia deja el panel a la misma distancia del
# ojo en todo su ancho y las mascaras/la imagen conservan su tamano. El origen (centro de la espalda) no se mueve. Las UV (TextUV, la de
# PlateImage, la del Slider) se calculan ANTES de doblar, sobre la placa plana.
# Ejes: construccion acostado (cara +Z, +Y = arriba del texto, mm); FBX (Unreal) PARADO, cara +X, arriba +Z, ancho por Y, origen = centro
#   de la ESPALDA; .blend parado como el del SHARE.
# Uso (Python del SISTEMA, PIL):  python gen_instr_card2.py --text <dir>      las 6 mascaras
#                                 python gen_instr_card2.py --images <dir>    las 6 imagenes de muestra
#                                 python gen_instr_card2.py --sheet <dir_vistas_prefijo> <salida.png>
# Uso (Blender headless): blender --background --python gen_instr_card2.py -- <dir> build     mallas, FBX y .blend
#                         blender --background --python gen_instr_card2.py -- <dir> qc        lee los FBX de vuelta y mide
#                         blender --background <dir>/SM_InstrCard2_SC.blend --python gen_instr_card2.py -- <dir> render <prefijo>
import functools
import math
import os
import sys
import traceback

CURVE_R = 1500.0                     # mm; radio de la cara de la placa. 0 = plano
A, B, RC = 400.0, 225.0, 64.0        # semiejes y radio de esquina del contorno exterior (mm): 800 x 450
H_RIM = 15.0                         # --- la misma seccion que el SAVE MELODY / SHARE / cuadro de experiencia / panel v1 ---
F_OUT_TOP, F_OUT_BOT = 3.5, 3.0
RIM_W = 4.8
F_RIM_IN = 1.5
H_FLOOR = 6.0
H_LIGHT = 10.0
PLATE_D = -10.2
H_PLATE_TOP = 17.7
H_PLATE_BOT = 10.5
F_PLATE = 2.5
TRAVEL = 4.0                         # cuanto se hunde al apretar
HOVER = 1.0                          # cuanto sube con el hover
S_IN, S_OUT, S_T, S_F = 5.0, 9.0, 3.0, 1.0
BASE_IN = 56.0                       # el anillo de la base llega hasta d = -56 (la placa lo tapa)
N_ARC = 8                            # tramos por esquina del contorno (v1: 12; con 8 la cuerda se aparta 0,3 mm y las normales son exactas)
N_ARC_WIN = 6                        # tramos por esquina de la ventana (r 16)
STEP_X = 90.0                        # paso de los tramos rectos HORIZONTALES (los que se doblan); los verticales no se subdividen
FONT = r"C:/Users/beltr/AppData/Local/Microsoft/Windows/Fonts/Avenir Book.ttf"
# ---- la ventana de la imagen (mm desde el centro de la placa, +y = arriba) ----
WIN_S = 330.0                        # lado del cuadrado (el encargo: 300 a 330)
WIN_RC = 16.0                        # esquinas
WIN_MARGIN = 40.0                    # del borde izquierdo del TOPE de la placa (extension de TextUV) a la ventana
IMG_SINK = 1.5                       # la imagen va hundida bajo el tope
RIB_W = 4.0                          # ancho de la cinta de luz del marquito
BORDER_W = 2.4                       # borde fino al ras del tope, por fuera de la cinta
Z_RIB = 12.2                         # fondo de la cinta de luz
# ---- la pagina. Quest 3 a ~1,5 m: mayuscula del cuerpo >= 22 mm, pie >= 14 mm ----
BODY_CAP_MM, FOOT_CAP_MM = 22.5, 14.5
BODY_LEAD, FOOT_LEAD = 1.28, 1.28
TEXT_GAP = 40.0                      # de la ventana al texto
TEXT_SIDE = 40.0                     # del texto al borde derecho del tope
TEXT_VMARGIN = 30.0                  # margen arriba/abajo de la zona de texto
BODY_V, FOOT_V = 255, 200            # intensidad de la mascara
FOOT_GAP_MIN = 20.0                  # aire minimo entre el cuerpo y el pie
# Textos del guion de Beltran (2026-10-19). Pie = None si no hay.
PAGES = {
    ("Breath", 1): ("Pick up the sensor in front of you with your dominant hand.", None),
    ("Breath", 2): ("Rest the sensor on your belly, just below your ribs. Breathe normally.", None),
    ("Breath", 3): ("Breathe in and out slowly. The circle follows your belly.", None),
    ("Breath", 4): ("You’ll breathe in a steady cycle: inhale, hold, exhale. Follow the guide without forcing it.", None),
    # 2026-10-20 tarde: sin START (pedido de Beltran): la ultima pagina es solo la instruccion, y la voz dice lo mismo
    ("Draw", 1): ("Pick up the brush with your dominant hand.", None),
    ("Draw", 2): ("Your palette is in your other hand. Point at a color to choose it, hold the trigger to draw. Try a first stroke.",
                  "The experience begins after your first stroke."),
    # 2026-10-20: la tercera experiencia de la demo (RECOGNIZING, el latido)
    ("Heart", 1): ("Pick up the sensor in front of you with your dominant hand.", None),
    ("Heart", 2): ("Place the sensor on your heart, on the left side of your chest. Then stay still for a moment.", None),
    ("Heart", 3): ("Each heartbeat becomes a pulse of light around you. Keep the sensor on your heart, and listen.", None),
}
# --only <Breath|Draw|Heart>: genera solo esas paginas / imagenes (las imagenes de muestra las reemplaza Beltran por fotos:
# regenerar todo las pisaria)
ONLY = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None


def want(key):
    return ONLY is None or key == ONLY


if "--win" in sys.argv:
    WIN_S = float(sys.argv[sys.argv.index("--win") + 1])


def dims():
    ap, bp = A + PLATE_D, B + PLATE_D
    d = {"ap": ap, "bp": bp}
    d["wx0"] = -ap + WIN_MARGIN
    d["wx1"] = d["wx0"] + WIN_S
    d["wcx"] = d["wx0"] + WIN_S / 2
    d["wcy"] = 0.0
    d["zx0"] = d["wx1"] + TEXT_GAP
    d["zx1"] = ap - TEXT_SIDE
    d["zy0"], d["zy1"] = -(bp - TEXT_VMARGIN), bp - TEXT_VMARGIN
    d["zcx"] = (d["zx0"] + d["zx1"]) / 2
    d["zw"] = d["zx1"] - d["zx0"]
    return d


# ------------------------------------------------------------------------------------------ mascaras (Python del sistema)
def make_masks(out):
    """Mascaras blanco sobre negro sobre el tope COMPLETO de la placa (0..1 = el tope). SIN voltear (gotcha 34)."""
    from PIL import Image, ImageDraw, ImageFont
    import numpy as np
    g = dims()
    ap, bp = g["ap"], g["bp"]
    W = 2048
    H = int(round(W * bp / ap))
    pxmm = W / (2 * ap)
    report = {}
    _fonts = {}

    def font_for(cap_mm):
        if cap_mm in _fonts:
            return _fonts[cap_mm]
        target = cap_mm * pxmm
        best = None
        for s in range(20, 400):
            f = ImageFont.truetype(FONT, s)
            cap = -f.getbbox("H", anchor="ls")[1]
            if best is None or abs(cap - target) < best[0]:
                best = (abs(cap - target), f, cap)
        _fonts[cap_mm] = (best[1], best[2])
        return _fonts[cap_mm]

    probe = ImageDraw.Draw(Image.new("L", (8, 8)))

    def wrap(text, f, maxw_px):
        words, lines, cur = [], [], ""
        for w in text.split():
            words.append(w)
        for w in words:
            t = (cur + " " + w).strip()
            if probe.textlength(t, font=f) <= maxw_px or not cur:
                cur = t
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
        return lines

    def balanced(text, f, maxw_mm):
        """Reparto parejo: el menor ancho que mantiene la misma cantidad de lineas que el voraz."""
        n = len(wrap(text, f, maxw_mm * pxmm))
        lo, hi = 40.0, maxw_mm
        for _ in range(24):
            mid = (lo + hi) / 2
            if len(wrap(text, f, mid * pxmm)) <= n:
                hi = mid
            else:
                lo = mid
        return wrap(text, f, hi * pxmm)

    cx_px = W / 2 + g["zcx"] * pxmm
    for (key, pg), (body, foot) in PAGES.items():
        if not want(key):
            continue
        img = Image.new("L", (W, H), 0)
        dr = ImageDraw.Draw(img)
        fb, capb = font_for(BODY_CAP_MM)
        lines = balanced(body, fb, g["zw"])
        pitch_b = fb.size * BODY_LEAD / pxmm                                  # mm
        h_body = (len(lines) - 1) * pitch_b + BODY_CAP_MM                     # de lo alto de la 1a mayuscula a la linea base de la ultima
        flines, pitch_f, h_foot = [], 0.0, 0.0
        if foot:
            ff, capf = font_for(FOOT_CAP_MM)
            flines = balanced(foot, ff, g["zw"])
            pitch_f = ff.size * FOOT_LEAD / pxmm
            h_foot = (len(flines) - 1) * pitch_f + FOOT_CAP_MM
            foot_base_last = g["zy0"] + 0.30 * ff.size / pxmm                   # linea base de la ultima linea del pie (aire para las colas)
            foot_top = foot_base_last + h_foot                                  # alto de la mayuscula de la 1a linea del pie
            band_lo, band_hi = foot_top + FOOT_GAP_MIN, g["zy1"]
        else:
            band_lo, band_hi = g["zy0"], g["zy1"]
        top_cap = (band_lo + band_hi) / 2 + h_body / 2                            # y de lo alto de la 1a mayuscula (centrado en la banda)
        fits = band_hi - band_lo >= h_body - 1e-6
        ink = []
        for k, ln in enumerate(lines):                                            # linea base de la linea k
            base_mm = top_cap - BODY_CAP_MM - k * pitch_b
            dr.text((cx_px, H / 2 - base_mm * pxmm), ln, font=fb, fill=BODY_V, anchor="ms")
        for k, ln in enumerate(flines):
            base_mm = foot_base_last + (len(flines) - 1 - k) * pitch_f
            dr.text((cx_px, H / 2 - base_mm * pxmm), ln, font=ff, fill=FOOT_V, anchor="ms")
        img.save(os.path.join(out, "T_Instr2_%s_P%d.png" % (key, pg)))
        a = np.asarray(img) > 40
        ys, xs = np.where(a)
        bbox = [round((xs.min() - W / 2) / pxmm, 1), round((xs.max() - W / 2) / pxmm, 1),
                round((H / 2 - ys.max()) / pxmm, 1), round((H / 2 - ys.min()) / pxmm, 1)]       # x0, x1, y0, y1 en mm
        inside = (bbox[0] >= g["zx0"] - 0.5 and bbox[1] <= g["zx1"] + 0.5 and bbox[2] >= g["zy0"] - 6 and bbox[3] <= g["zy1"] + 0.5)
        report["%s_P%d" % (key, pg)] = {"lineas_cuerpo": len(lines), "lineas_pie": len(flines), "tinta_mm_x0x1_y0y1": bbox,
                                        "centro_x_tinta": round((bbox[0] + bbox[1]) / 2, 1), "cabe": bool(fits and inside)}
    report["png"] = [W, H]
    return report


# ------------------------------------------------------------------------------------------ imagenes de muestra (Python del sistema)
def make_images(out):
    """6 imagenes cuadradas 1024 x 1024: azul noche, dibujo lineal claro con acentos calidos (el estilo de los iconos del panel v1)."""
    import numpy as np
    from PIL import Image, ImageChops, ImageDraw, ImageFont
    from scipy import ndimage
    PX, UN, SS = 1024, 256.0, 3
    N = PX * SS
    K = N / UN                                     # px por unidad (supersample)
    COL = {"line": (226, 236, 255), "warm": (255, 188, 116), "fill": (110, 140, 215)}

    class Art:
        def __init__(self):
            self.L = {k: Image.new("L", (N, N), 0) for k in COL}

        def xy(self, x, y):
            return (N / 2 + x * K, N / 2 - y * K)

        def _lay(self, layer, fn):
            t = Image.new("L", (N, N), 0)
            fn(ImageDraw.Draw(t))
            self.L[layer] = ImageChops.lighter(self.L[layer], t)

        def disc(self, p, r, v=255, layer="line"):
            cx, cy = self.xy(*p)
            self._lay(layer, lambda d: d.ellipse((cx - r * K, cy - r * K, cx + r * K, cy + r * K), fill=v))

        def circle(self, p, r, w=3.4, v=255, layer="line"):
            cx, cy = self.xy(*p)
            self._lay(layer, lambda d: d.ellipse((cx - r * K, cy - r * K, cx + r * K, cy + r * K), outline=v, width=max(1, int(w * K))))

        def glow(self, p, r, v=255, power=1.6, steps=56, layer="warm"):
            cx, cy = self.xy(*p)

            def fn(d):
                for i in range(steps):
                    t = i / (steps - 1)
                    rr = r * (1 - t)
                    d.ellipse((cx - rr * K, cy - rr * K, cx + rr * K, cy + rr * K), fill=int(v * t ** power))
            self._lay(layer, fn)

        def line(self, pts, w=3.4, v=255, layer="line", closed=False):
            p = [self.xy(*q) for q in pts]
            if closed:
                p = p + [p[0]]
            hw = w * K / 2

            def fn(d):
                d.line(p, fill=v, width=max(1, int(w * K)), joint="curve")
                for a, b in (p[0], p[-1]):
                    d.ellipse((a - hw, b - hw, a + hw, b + hw), fill=v)
            self._lay(layer, fn)

        def taper(self, pts, w0, w1, v=255, layer="line"):
            n = len(pts)
            for i, q in enumerate(pts):
                self.disc(q, (w0 + (w1 - w0) * i / max(n - 1, 1)) / 2, v, layer)

        def arrowhead(self, tip, direction, size=9.0, w=3.4, v=255, layer="line"):
            ang = math.atan2(direction[1], direction[0])
            for s in (+1, -1):
                a = ang + math.pi + s * math.radians(35)
                self.line([tip, (tip[0] + size * math.cos(a), tip[1] + size * math.sin(a))], w, v, layer)

        def capsule_pts(self, p, q, w):
            dx, dy = q[0] - p[0], q[1] - p[1]
            Ln = math.hypot(dx, dy)
            ux, uy = dx / Ln, dy / Ln
            nx, ny = -uy, ux
            r = w / 2
            pts = [(p[0] + nx * r, p[1] + ny * r), (q[0] + nx * r, q[1] + ny * r)]
            for i in range(1, 12):
                a = math.pi * i / 12
                pts.append((q[0] + r * (nx * math.cos(a) + ux * math.sin(a)), q[1] + r * (ny * math.cos(a) + uy * math.sin(a))))
            pts += [(q[0] - nx * r, q[1] - ny * r), (p[0] - nx * r, p[1] - ny * r)]
            for i in range(1, 12):
                a = math.pi * i / 12
                pts.append((p[0] - r * (nx * math.cos(a) + ux * math.sin(a)), p[1] - r * (ny * math.cos(a) + uy * math.sin(a))))
            return pts

        def capsule(self, p, q, w, wline=3.4, v=255, layer="line", fill=None):
            pts = self.capsule_pts(p, q, w)
            if fill is not None:
                pp = [self.xy(*t) for t in pts]
                self._lay(layer, lambda d: d.polygon(pp, fill=fill))
            else:
                self.line(pts, wline, v, layer, closed=True)

        def shape(self, polys, w, v_line=235, v_fill=26, layer="line"):
            """Union de poligonos rellenos -> contorno limpio (distancia al borde) + relleno tenue."""
            m = Image.new("L", (N, N), 0)
            d = ImageDraw.Draw(m)
            for poly in polys:
                d.polygon([self.xy(*q) for q in poly], fill=255)
            inside = np.asarray(m) > 127
            dist = ndimage.distance_transform_edt(inside)
            edge = Image.fromarray(((dist <= w * K) & inside).astype(np.uint8) * v_line)
            self.L[layer] = ImageChops.lighter(self.L[layer], edge)
            self.L["fill"] = ImageChops.lighter(self.L["fill"], Image.fromarray(inside.astype(np.uint8) * v_fill))

        def text(self, p, s, cap_units, tracking=0.05, v=235, layer="line"):
            size = int(round(cap_units * K / 0.72))
            f = ImageFont.truetype(FONT, size)
            w = sum(f.getlength(c) for c in s) + tracking * size * (len(s) - 1)
            cx, cy = self.xy(*p)
            x = cx - w / 2

            def fn(d):
                nonlocal x
                for c in s:
                    d.text((x, cy), c, font=f, fill=v, anchor="ls")
                    x += f.getlength(c) + tracking * size
            self._lay(layer, fn)

    def bez(p0, p1, p2, p3, n=80):
        out_ = []
        for i in range(n + 1):
            t = i / n
            a = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
            out_.append((sum(a[j] * q[0] for j, q in enumerate((p0, p1, p2, p3))), sum(a[j] * q[1] for j, q in enumerate((p0, p1, p2, p3)))))
        return out_

    def rot(pts, ang, c=(0, 0)):
        ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        return [(c[0] + (x - c[0]) * ca - (y - c[1]) * sa, c[1] + (x - c[0]) * sa + (y - c[1]) * ca) for x, y in pts]

    def ellipse_pts(c, rx, ry, ang=0.0, n=120):
        return rot([(c[0] + rx * math.cos(2 * math.pi * i / n), c[1] + ry * math.sin(2 * math.pi * i / n)) for i in range(n)], ang, c)

    def hand(art, ox, oy, s, ang):
        """Mano abierta (palma al frente, dedos hacia arriba), contorno unico. Local: centro de la palma en (0,0), unidades de arte."""
        def T(pts):
            return [(ox + s * q[0], oy + s * q[1]) for q in rot(pts, ang)]
        polys = []
        palm = []
        r_, x0, x1, y0, y1 = 18.0, -27.0, 27.0, -28.0, 22.0
        for cx_, cy_, a0 in ((x1 - r_, y1 - r_, 0), (x0 + r_, y1 - r_, 90), (x0 + r_, y0 + r_, 180), (x1 - r_, y0 + r_, 270)):
            for i in range(0, 91, 10):
                t = math.radians(a0 + i)
                palm.append((cx_ + r_ * math.cos(t), cy_ + r_ * math.sin(t)))
        polys.append(T(palm))
        for p, q, w in (((-20, 14), (-22, 70), 13.0), ((-6, 16), (-6, 79), 13.5), ((8, 15), (10, 72), 13.0), ((21, 10), (27, 56), 11.0),
                        ((-24, -6), (-54, 28), 14.0)):
            polys.append(T(art.capsule_pts(p, q, w)))
        polys.append(T([(-21, -20), (21, -20), (19, -95), (-19, -95)]))
        art.shape(polys, 3.2)

    def sit_figure(art, ox, oy, z, sensor=True, arrows=True, lw=3.4):
        P = lambda x, y: (ox + z * x, oy + z * y)

        def Lp(pts, w=lw, v=235, layer="line"):
            art.line([P(*q) for q in pts], w, v, layer)
        art.circle(P(-6, 40), 9.5 * z, lw, 235)
        Lp(bez((-13, 30), (-27, 18), (-25, -5), (-19, -24)))
        Lp(bez((3, 31), (12, 18), (13, 5), (12, -7)) + bez((12, -7), (14, -14), (9, -20), (3, -24))[1:])
        Lp([(-19, -24), (38, -27), (38, -50)])
        Lp([(-36, -54), (52, -54)], 2.6, 90)
        if sensor:
            art.capsule(P(17.5, -12), P(17.5, 10), 6.5 * z, fill=255, layer="warm")
            art.glow(P(17.5, -1), 14 * z, 120, 1.4)
        if arrows:
            Lp([(37, -12), (37, 14)], 2.8, 200, "warm")
            art.arrowhead(P(37, 14), (0, 1), 7.5, 2.8, 200, "warm")
            art.arrowhead(P(37, -12), (0, -1), 7.5, 2.8, 200, "warm")

    def sensor_disc(art, c, s=1.0):
        """El sensor (disco con domo y aro de luz), visto un poco de arriba."""
        art.glow((c[0], c[1]), 70 * s, 70, 1.8)
        art.line(ellipse_pts(c, 38 * s, 31 * s), 3.6, 235, "line", closed=True)
        art.line(ellipse_pts((c[0], c[1] + 3 * s), 25 * s, 19 * s), 3.0, 150, "line", closed=True)
        art.line(ellipse_pts(c, 32 * s, 25.5 * s), 3.4, 255, "warm", closed=True)
        art.glow(c, 22 * s, 90, 1.2)

    def compose(art, name):
        if not want(name.split("_")[2]):
            return
        yy, xx = np.mgrid[0:PX, 0:PX].astype(np.float32)
        rr = np.sqrt((xx - PX / 2) ** 2 + (yy - PX * 0.46) ** 2) / (PX * 0.72)
        t = np.clip(1.0 - rr, 0.0, 1.0)[..., None] ** 1.6
        bg0 = np.array((5, 8, 20), np.float32)
        bg1 = np.array((16, 26, 56), np.float32)
        img = bg0 + (bg1 - bg0) * t
        rng = np.random.default_rng(7)
        for _ in range(46):                                              # estrellas muy tenues
            x, y = rng.integers(20, PX - 20, 2)
            b = float(rng.uniform(18, 52))
            img[max(y - 1, 0):y + 2, max(x - 1, 0):x + 2] += b * 0.6
        for k, c in COL.items():
            a = np.asarray(art.L[k].resize((PX, PX), Image.LANCZOS), np.float32)[..., None] / 255.0
            img = img + a * np.array(c, np.float32) * (0.55 if k == "fill" else 1.0)
        Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").save(os.path.join(out, name))

    # ---- Breath 1: el sensor flotando frente a una mano abierta
    a = Art()
    hand(a, 52, -58, 1.12, -22)
    sensor_disc(a, (-30, 40), 1.25)
    for i, (w_, v) in enumerate(((70, 210), (48, 150), (28, 100))):          # la sombra que lo deja flotando
        a.line([(-30 - w_ / 2, -4 - i * 11), (-30 + w_ / 2, -4 - i * 11)], 2.8, v, "line")
    compose(a, "T_DemoInstrImg_Breath_1.png")

    # ---- Breath 2: sentado de perfil, el sensor en la panza, flecha arriba y abajo
    a = Art()
    sit_figure(a, -6, 0, 2.2)
    compose(a, "T_DemoInstrImg_Breath_2.png")

    # ---- Breath 3: la silueta respirando y un circulo que crece
    a = Art()
    sit_figure(a, -66, -4, 1.5, arrows=False)
    oc = (56, 24)
    a.line(bez((-66 + 1.5 * 24, -4 - 1.5), (-26, 6), (-12, 14), (oc[0] - 58, oc[1])), 2.6, 120, "line")
    for r, v in ((16, 255), (28, 175), (41, 110), (54, 60)):
        a.circle(oc, r, 3.4, v, "warm")
    a.glow(oc, 18, 150, 1.0)
    for ang in (35, 90, 145, 215, 270, 325):
        c, s_ = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        a.line([(oc[0] + 62 * c, oc[1] + 62 * s_), (oc[0] + 72 * c, oc[1] + 72 * s_)], 2.8, 140, "warm")
    compose(a, "T_DemoInstrImg_Breath_3.png")

    # ---- Breath 4: los aros del pacer y "inhale · hold · exhale"
    a = Art()
    a.disc((0, 22), 6.0, 255, "warm")
    a.glow((0, 22), 28, 140, 1.0)
    for r, v in ((16, 255), (32, 215), (50, 165), (70, 110), (92, 62)):
        a.circle((0, 22), r, 3.8, v, "line")
    a.text((0, -108), "inhale  ·  hold  ·  exhale", 11.0, 0.06, 235, "line")
    compose(a, "T_DemoInstrImg_Breath_4.png")

    # ---- Draw 1: el mando de Quest con la punta brillante
    a = Art()
    ANG, OFF = -14.0, (-6, -4)

    def Rq(pts):
        return [(OFF[0] + q[0], OFF[1] + q[1]) for q in rot(pts, ANG)]
    a.line(Rq(a.capsule_pts((-42, -96), (-14, -30), 36.0)), 3.6, 235, "line", closed=True)          # la empunadura
    ringc = Rq([(10, 32)])[0]
    a.circle(ringc, 40, 3.6, 235, "line")                                                               # el aro de seguimiento
    for k in range(9):
        t = math.radians(20 + k * 26)
        a.disc((ringc[0] + 40 * math.cos(t), ringc[1] + 40 * math.sin(t)), 3.0, 215, "line")
    for (cx_, cy_, r_, f_) in ((4, 26, 9, False), (26, 40, 4.2, True), (32, 24, 4.2, True)):          # palanca y botones
        pc_ = Rq([(cx_, cy_)])[0]
        (a.disc if f_ else a.circle)(pc_, r_, *( (190, "line") if f_ else (3.0, 190, "line")))
    tip = (ringc[0] + 40 * math.cos(math.radians(62)), ringc[1] + 40 * math.sin(math.radians(62)))
    a.glow(tip, 34, 190, 1.2)
    a.disc(tip, 6.5, 255, "warm")
    swoop = bez(tip, (tip[0] + 6, tip[1] + 34), (tip[0] + 54, tip[1] + 40), (tip[0] + 74, tip[1] + 6), 120)
    a.taper(swoop, 8.5, 1.6, 245, "warm")
    compose(a, "T_DemoInstrImg_Draw_1.png")

    # ---- Draw 2: la paleta circular en una mano y un trazo de luz
    a = Art()
    hand(a, -40, -104, 1.0, 12)
    pc, R = (-22, 44), 56.0
    a.circle(pc, R, 3.6, 235, "line")
    a.circle(pc, 17, 2.8, 130, "line")
    touched = None
    for k in range(8):
        t = math.radians(90 - 45 * k + 22.5)
        x, y = pc[0] + 37 * math.cos(t), pc[1] + 37 * math.sin(t)
        if k == 1:
            touched = (x, y)
            a.disc((x, y), 9.0, 255, "warm")
            a.glow((x, y), 22, 150, 1.1)
        elif k % 2 == 0:
            a.disc((x, y), 7.2, 190, "line")
        else:
            a.circle((x, y), 7.4, 3.0, 190, "line")
    st = bez(touched, (touched[0] + 26, touched[1] + 8), (touched[0] + 22, touched[1] - 52), (touched[0] + 66, touched[1] - 30), 140)
    a.taper(st, 2.0, 11.0, 245, "warm")
    a.glow(st[-1], 22, 170, 1.1)
    compose(a, "T_DemoInstrImg_Draw_2.png")

    # ---- Heart (2026-10-20): el mismo dibujo lineal, con el acento calido hacia el rojo del latido
    COL["warm"] = (255, 122, 108)
    # Heart 1: el sensor flotando frente a una mano abierta (como Breath 1)
    a = Art()
    hand(a, 52, -58, 1.12, -22)
    sensor_disc(a, (-30, 40), 1.25)
    for i, (w_, v) in enumerate(((70, 210), (48, 150), (28, 100))):
        a.line([(-30 - w_ / 2, -4 - i * 11), (-30 + w_ / 2, -4 - i * 11)], 2.8, v, "line")
    compose(a, "T_DemoInstrImg_Heart_1.png")
    # Heart 2: sentado de perfil, el sensor en el pecho (a la izquierda) y los pulsos que salen de ahi
    a = Art()
    sit_figure(a, -6, 0, 2.2, sensor=False, arrows=False)
    hc = (-6 + 2.2 * 14.0, 2.2 * 16.0)
    a.capsule((hc[0], hc[1] - 2.2 * 9), (hc[0], hc[1] + 2.2 * 9), 6.5 * 2.2, fill=255, layer="warm")
    a.glow(hc, 30, 130, 1.4)
    for r, v in ((26, 210), (40, 140), (55, 80)):
        a.circle((hc[0] + 4, hc[1]), r, 3.0, v, "warm")
    compose(a, "T_DemoInstrImg_Heart_2.png")
    # Heart 3: un punto que late, ondas que se abren y la linea del pulso abajo
    a = Art()
    oc = (0, 30)
    a.disc(oc, 7.0, 255, "warm")
    a.glow(oc, 30, 160, 1.0)
    for r, v in ((18, 255), (34, 200), (52, 140), (72, 85), (94, 45)):
        a.circle(oc, r, 3.6, v, "line")
    ecg = [(-108, -82), (-40, -82), (-30, -70), (-22, -82), (-12, -82), (-4, -112), (6, -44), (14, -96), (22, -82), (40, -82), (50, -74),
           (60, -82), (108, -82)]
    a.line(ecg, 3.4, 255, "warm")
    compose(a, "T_DemoInstrImg_Heart_3.png")
    return [n for n in ["T_DemoInstrImg_%s_%d.png" % (k, n) for k, n in (("Breath", 1), ("Breath", 2), ("Breath", 3), ("Breath", 4),
                                                                           ("Draw", 1), ("Draw", 2), ("Heart", 1), ("Heart", 2), ("Heart", 3))]]


# ------------------------------------------------------------------------------------------ hoja de vista previa (Python del sistema)
def make_sheet(pre, out):
    from PIL import Image, ImageDraw, ImageFont
    CW, LAB = 1000, 30
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 16)
    items = [("%s_Breath_P1.png" % pre, "BREATH p1"), ("%s_Breath_P2.png" % pre, "BREATH p2"),
             ("%s_Breath_P3.png" % pre, "BREATH p3"), ("%s_Breath_P4.png" % pre, "BREATH p4"),
             ("%s_Draw_P1.png" % pre, "DRAW p1"), ("%s_Draw_P2.png" % pre, "DRAW p2"),
             ("%s_hover.png" % pre, "hover (la placa +1 mm, cinta y texto encendidos)"),
             ("%s_curva.png" % pre, "vista desde arriba: la curva (CURVE_R %d mm)" % CURVE_R)]
    cells = []
    for p, lab in items:
        im = Image.open(p).convert("RGB")
        cells.append((im.resize((CW, int(CW * im.height / im.width)), Image.LANCZOS), lab))
    rows = [cells[i:i + 2] for i in range(0, len(cells), 2)]
    rh = [max(c[0].height for c in r) + LAB for r in rows]
    sheet = Image.new("RGB", (CW * 2 + 10, sum(rh)), (0, 0, 0))
    d = ImageDraw.Draw(sheet)
    y = 0
    for r, h in zip(rows, rh):
        for k, (im, lab) in enumerate(r):
            d.text((k * (CW + 10) + 10, y + 7), lab, font=font, fill=(235, 235, 235))
            sheet.paste(im, (k * (CW + 10), y + LAB))
        y += h
    sheet.save(out)
    print("SHEET_OK", sheet.size)


if "--text" in sys.argv and "--" not in sys.argv:
    out = sys.argv[sys.argv.index("--text") + 1]
    os.makedirs(out, exist_ok=True)
    for k, v in make_masks(out).items():
        print("TEXTO", k, v)
    g = dims()
    print("ventana x", g["wx0"], g["wx1"], "zona texto x", g["zx0"], g["zx1"], "y", g["zy0"], g["zy1"])
    sys.exit(0)
if "--images" in sys.argv and "--" not in sys.argv:
    out = sys.argv[sys.argv.index("--images") + 1]
    os.makedirs(out, exist_ok=True)
    print("IMAGENES_OK", make_images(out))
    sys.exit(0)
if "--sheet" in sys.argv and "--" not in sys.argv:
    i = sys.argv.index("--sheet")
    make_sheet(sys.argv[i + 1], sys.argv[i + 2])
    sys.exit(0)
if "bpy" not in sys.modules and "--" not in sys.argv:
    sys.exit(0)                                           # sin modo: nada que hacer

# ------------------------------------------------------------------------------------------ Blender
import bmesh                                              # noqa: E402
import bpy                                                # noqa: E402
from mathutils import Matrix, Vector                      # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import revolve_lib as RL                                  # noqa: E402
import anim_luz_objects as LZ                             # noqa: E402  (trace_mesh)

RR = RL.rrect_outline                                     # el original (sin partial)
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else "."
MODE = argv[1] if len(argv) > 1 else "build"
R_UE = Matrix(((0.0, 0.0, 1.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0))).to_4x4()    # cara +Z -> +X, arriba +Y -> +Z
R_WEB = Matrix(((1.0, 0.0, 0.0), (0.0, 0.0, -1.0), (0.0, 1.0, 0.0))).to_4x4()  # cara +Z -> -Y, arriba +Y -> +Z
ARC45 = math.radians(45.0)
PARTS_PLATE = ("PlateSide", "PlateTop", "PlateImage", "WinRing")


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


# ---- perfiles (d, h, filete, parte), mm
def base_profile():
    """Anillo CERRADO (sin tapas): borde + canal con la cinta + el piso hasta d = -56 (bajo la placa) y la pared interior."""
    P = [(-28.0, 0.0, 0.0, "Body"), (0.0, 0.0, F_OUT_BOT, "Body"), (0.0, H_RIM, F_OUT_TOP, "Body"),
         (-RIM_W, H_RIM, F_RIM_IN, "Body"), (-RIM_W, H_LIGHT, 0.0, "Ring"), (-RIM_W, H_FLOOR, 1.0, "Ring"),
         (-BASE_IN, H_FLOOR, 1.0, "Body"), (-BASE_IN, 0.0, 1.0, "Body"), (-28.0, 0.0, 0.0, "Body")]
    return RL.fillet_poly(P)[:-1]


def plate_profile():
    d0 = PLATE_D - F_PLATE - 1.5            # el barrido cubre solo el borde de la placa; el centro (con la ventana) lo cierran las tapas
    P = [(d0, H_PLATE_BOT, 0.0, "PlateSide"), (PLATE_D, H_PLATE_BOT, 1.0, "PlateSide"),
         (PLATE_D, H_PLATE_TOP, F_PLATE, "PlateSide"), (d0, H_PLATE_TOP, 0.0, "PlateTop")]
    pts = RL.fillet_poly(P)
    return [(d, h, "PlateTop" if (h >= H_PLATE_TOP - 1e-6) else p) for d, h, p in pts]


def pocket_profile():
    """La ventana de la imagen: d hacia AFUERA del borde de la imagen, de afuera hacia adentro. Borde fino al ras del tope, canal con la
    cinta de luz (piso Z_RIB y el pie de la pared), muro del lecho de la imagen y la imagen, hundida IMG_SINK bajo el tope."""
    zi = H_PLATE_TOP - IMG_SINK
    P = [(RIB_W + BORDER_W, H_PLATE_TOP, 0.0, "PlateSide"), (RIB_W, H_PLATE_TOP, 0.8, "PlateSide"),
         (RIB_W, Z_RIB + 2.0, 0.0, "WinRing"), (RIB_W, Z_RIB, 1.0, "WinRing"),
         (0.0, Z_RIB, 0.6, "PlateSide"), (0.0, zi, 0.8, "PlateImage"), (-3.0, zi, 0.0, "PlateImage")]
    return RL.fillet_poly(P, ARC45)


def slider_profile():
    mid = (S_IN + S_OUT) / 2
    P = [(mid, 0.0, 0.0, "Slider"), (S_OUT, 0.0, S_F, "Slider"), (S_OUT, S_T, S_F, "Slider"), (S_IN, S_T, S_F, "Slider"),
         (S_IN, 0.0, S_F, "Slider"), (mid, 0.0, 0.0, "Slider")]
    return RL.fillet_poly(P)[:-1]


# ---- la curva: doblar alrededor del eje vertical (y de construccion). s = x (lateral), w = z (profundidad)
def bend_xz(x, z):
    """(x, z) en mm -> (x', z', theta, q). Radio de la cara de la placa = CURVE_R; el origen (espalda, centro) no se mueve."""
    R = CURVE_R
    wn = H_PLATE_TOP
    th = x / R
    r = R + wn - z
    return r * math.sin(th), (R + wn) - r * math.cos(th), th, r / R


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
        if vnl is not None:
            v[vnl] = tuple(bend_normal(Vector(v[vnl]).normalized(), th, q))


# ---- construccion con bmesh
def new_bm():
    bm = bmesh.new()
    return bm, bm.loops.layers.uv.new("UVMap"), bm.verts.layers.float_vector.new("vn")


def sweep_bm(bm, uv0, vnl, prof, parts, a, b, rc, outline, cx=0.0, cy=0.0, closed=False, ufrac=None):
    """Barre el perfil a lo largo del rectangulo redondeado (como revolve_lib.sweep_rrect) dentro de un bmesh, con normales EXACTAS en la
    capa de vertices 'vn' (viajan con los cortes). ufrac = fraccion de perimetro por vertice del contorno (el Slider)."""
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
            u0, u1 = (ufrac[j], ufrac[j + 1] if j2 else 1.0) if ufrac else (j / m, (j + 1) / m)
            v0, v1 = i / max(npf - 1, 1), (i + 1) / max(npf - 1, 1)
            for lp, t in zip(f.loops, ((u0, v0), (u0, v1), (u1, v1), (u1, v0))):
                lp[uv0].uv = t
    return rows


def point_in_poly(x, y, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def fill_cap(bm, rows, holes, nz, mi):
    """Tapa plana (triangle_fill) de un contorno, con huecos opcionales; plana hacia nz (+1 / -1), slot mi."""
    es = []
    for row in [rows] + holes:
        m = len(row)
        for j in range(m):
            e = bm.edges.get((row[j], row[(j + 1) % m]))
            es.append(e if e else bm.edges.new((row[j], row[(j + 1) % m])))
    res = bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=es, normal=(0.0, 0.0, float(nz)))
    faces = [g for g in res["geom"] if isinstance(g, bmesh.types.BMFace)]
    polys = [[(v.co.x, v.co.y) for v in h] for h in holes]
    cut = [f for f in faces if any(point_in_poly(f.calc_center_median().x, f.calc_center_median().y, p) for p in polys)]
    if cut:
        bmesh.ops.delete(bm, geom=cut, context='FACES')
    for f in faces:
        if not f.is_valid:
            continue
        f.normal_update()
        if f.normal.z * nz < 0:
            f.normal_flip()
        f.material_index = mi
        f.smooth = True
    return len(faces) - len(cut)


def cut_planes(bm):
    """Planos x = const (mm) que parten TODO el solido de la placa para que las tapas planas sigan la curva. Se elige la grilla (corda
    de 70 a 100 mm) cuyos planos quedan mas lejos de los vertices existentes (para no dejar astillas)."""
    if CURVE_R <= 0:
        return []
    xs = sorted({round(v.co.x * 1000.0, 3) for v in bm.verts})
    best = None
    for G in [g * 0.5 for g in range(140, 201)]:                                  # 70 .. 100 mm
        for ph in (0.0, 0.5):
            pl = [(k + ph) * G for k in range(-12, 13) if abs((k + ph) * G) < A - 8.0]
            dmin = min((abs(p - x) for p in pl for x in xs if abs(p - x) > 1e-3), default=99.0)
            score = min(dmin, 3.0) - 0.02 * G
            if best is None or score > best[0]:
                best = (score, G, ph, pl, dmin)
    return best[3]


def _dbg(bm, tag):
    if os.environ.get("GIC2_DEBUG"):
        print("DBG", tag, "caras", len(bm.faces), "abiertas", sum(1 for e in bm.edges if not e.is_manifold))


def build_plate():
    g = dims()
    bm, uv0, vnl = new_bm()
    out_fn = functools.partial(RR, n_arc=N_ARC, step=1.0e6)
    win_fn = functools.partial(RR, n_arc=N_ARC_WIN, step=1.0e6)
    rows_o = sweep_bm(bm, uv0, vnl, plate_profile(), PARTS_PLATE, A, B, RC, out_fn)
    rows_w = sweep_bm(bm, uv0, vnl, pocket_profile(), PARTS_PLATE, WIN_S / 2, WIN_S / 2, WIN_RC, win_fn, cx=g["wcx"], cy=g["wcy"])
    _dbg(bm, "barridos")
    n_top = fill_cap(bm, rows_o[-1], [rows_w[0]], 1, 1)
    _dbg(bm, "tapa tope")
    n_bot = fill_cap(bm, rows_o[0], [], -1, 0)
    _dbg(bm, "tapa fondo")
    n_img = fill_cap(bm, rows_w[-1], [], 1, 2)
    _dbg(bm, "tapa imagen")
    bm.normal_update()
    planes = cut_planes(bm)
    for x in planes:                                                  # parte TODO el solido: nada de T en las costuras
        bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), dist=1e-7,
                               plane_co=(x / 1000.0, 0.0, 0.0), plane_no=(1.0, 0.0, 0.0))
    _dbg(bm, "cortes")
    big = [f for f in bm.faces if len(f.verts) > 4]
    if big:
        bmesh.ops.triangulate(bm, faces=big, quad_method='BEAUTY', ngon_method='BEAUTY')
    # UV ANTES de doblar, sobre la placa plana
    uv1 = bm.loops.layers.uv.new("TextUV")
    ap, bp = g["ap"], g["bp"]
    for f in bm.faces:
        mi = f.material_index
        for lp in f.loops:
            x, y = lp.vert.co.x * 1000.0, lp.vert.co.y * 1000.0
            lp[uv1].uv = ((x + ap) / (2 * ap), (y + bp) / (2 * bp)) if mi == 1 else (-1.0, -1.0)
            if mi == 2:
                lp[uv0].uv = ((x - g["wx0"]) / WIN_S, (y - (g["wcy"] - WIN_S / 2)) / WIN_S)
    bend_bm(bm, vnl)
    return finish_bm(bm, vnl, "SM_InstrCard2_Plate_SC", len(PARTS_PLATE)), {"tapas": [n_top, n_bot, n_img], "planos_mm": [round(p, 2) for p in planes]}


def finish_bm(bm, vnl, name, nparts):
    bm.normal_update()
    flips = sum(1 for f in bm.faces if f.normal.dot(sum((Vector(v[vnl]) for v in f.verts), Vector())) < 0)
    vns = [Vector(v[vnl]) for v in bm.verts]
    if any(n.length < 0.5 for n in vns):
        raise RuntimeError("normales sin interpolar en %s: %d" % (name, sum(1 for n in vns if n.length < 0.5)))
    vn_list = [tuple(n.normalized()) for n in vns]
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.normals_split_custom_set([vn_list[me.loops[li].vertex_index] for li in range(len(me.loops))])
    me["flips"] = flips
    return me


def build_ring(name, prof, parts, closed, ufrac=None, step_x=STEP_X):
    bm, uv0, vnl = new_bm()
    fn = functools.partial(outline_xy, n_arc=N_ARC, step_x=step_x if CURVE_R > 0 else 1.0e6)
    sweep_bm(bm, uv0, vnl, prof, parts, A, B, RC, fn, closed=closed, ufrac=ufrac)
    bend_bm(bm, vnl)
    return finish_bm(bm, vnl, name, len(parts))


def slider_ufrac():
    ring = outline_xy(A, B, RC, (S_IN + S_OUT) / 2, N_ARC, STEP_X if CURVE_R > 0 else 1.0e6)
    L = [0.0]
    for p, q in zip(ring, ring[1:] + ring[:1]):
        L.append(L[-1] + math.hypot(q[0] - p[0], q[1] - p[1]))
    return [x / L[-1] for x in L]


def build_trace():
    path = [(p[0], p[1]) for p in outline_xy(A, B, RC, -7.5, N_ARC, STEP_X / 2 if CURVE_R > 0 else 1.0e6)]
    me = LZ.trace_mesh({"path": path, "z": H_RIM, "hw": 7.0, "face": 1.0}, "SM_InstrCard2_Trace_SC")
    if CURVE_R > 0:
        for v in me.vertices:
            x, y, z = (c * 1000.0 for c in v.co)
            x2, z2, _, _ = bend_xz(x, z)
            v.co = (x2 / 1000.0, y / 1000.0, z2 / 1000.0)
    return me


def signed_volume(me):
    me.calc_loop_triangles()
    s = 0.0
    for t in me.loop_triangles:
        a, b, c = (me.vertices[i].co for i in t.vertices)
        s += a.dot(b.cross(c)) / 6.0
    return s


def stats(me, nparts):
    bm = bmesh.new()
    bm.from_mesh(me)
    r = {"tris": sum(len(f.verts) - 2 for f in bm.faces), "abiertas": sum(1 for e in bm.edges if not e.is_manifold),
         "degeneradas": sum(1 for f in bm.faces if f.calc_area() < 1e-10),
         "por_slot": [sum(1 for f in bm.faces if f.material_index == k) for k in range(nparts)]}
    bm.free()
    me.calc_loop_triangles()
    r["astillas_lt_0.01mm2"] = sum(1 for t in me.loop_triangles if t.area < 1e-8)
    r["volumen_mm3"] = round(signed_volume(me) * 1e9)
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


def corner_report(g):
    """Puntos clave de la placa ya DOBLADOS, en cm en el marco de Unreal: (X profundidad, Y_UE, Z). Y_UE = -(derecha del espectador)."""
    def pt(x, y, z):
        x2, z2, _, _ = bend_xz(x, z) if CURVE_R > 0 else (x, z, 0, 1)
        return [round(z2 / 10.0, 3), round(-x2 / 10.0, 3), round(y / 10.0, 3)]
    zi = H_PLATE_TOP - IMG_SINK
    return {
        "imagen_esquinas_sup_izq_inf_der(cm)": [pt(g["wx0"], g["wcy"] + WIN_S / 2, zi), pt(g["wx1"], g["wcy"] + WIN_S / 2, zi),
                                                pt(g["wx0"], g["wcy"] - WIN_S / 2, zi), pt(g["wx1"], g["wcy"] - WIN_S / 2, zi)],
        "imagen_centro(cm)": pt(g["wcx"], g["wcy"], zi),
        "texto_esquinas(cm)": [pt(g["zx0"], g["zy1"], H_PLATE_TOP), pt(g["zx1"], g["zy1"], H_PLATE_TOP),
                               pt(g["zx0"], g["zy0"], H_PLATE_TOP), pt(g["zx1"], g["zy0"], H_PLATE_TOP)],
        "texto_centro(cm)": pt(g["zcx"], (g["zy0"] + g["zy1"]) / 2, H_PLATE_TOP),
        "tope_centro(cm)": pt(0.0, 0.0, H_PLATE_TOP),
    }


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    g = dims()
    info, meshes = {}, []
    base = build_ring("SM_InstrCard2_Base_SC", base_profile(), ("Body", "Ring"), True)
    plate, plate_info = build_plate()
    slider = build_ring("SM_InstrCard2_Slider_SC", slider_profile(), ("Slider",), True, ufrac=slider_ufrac())
    trace = build_trace()
    for me, parts in ((base, ("Body", "Ring")), (plate, PARTS_PLATE), (slider, ("Slider",)), (trace, ("Trace",))):
        for p in parts:
            me.materials.append(bpy.data.materials.new("M_InstrCard2_" + p))
        info[me.name] = stats(me, len(parts))
        meshes.append(me)
    info["SM_InstrCard2_Plate_SC"].update(plate_info)
    os.makedirs(OUT, exist_ok=True)
    for me in meshes:
        export_ue(me, os.path.join(OUT, me.name + ".fbx"), tspace=me is not trace)
        m2 = me.copy()
        m2.transform(R_UE)
        xs = [v.co for v in m2.vertices]
        info[me.name]["caja_UE_cm_min"] = [round(min(c[k] for c in xs) * 100, 3) for k in range(3)]
        info[me.name]["caja_UE_cm_max"] = [round(max(c[k] for c in xs) * 100, 3) for k in range(3)]
        bpy.data.meshes.remove(m2)
    col = bpy.context.scene.collection
    for me in meshes:                                  # .blend armado PARADO, en la orientacion de la web
        ob = bpy.data.objects.new(me.name.replace("SM_InstrCard2_", "").replace("_SC", ""), me)
        col.objects.link(ob)
        ob.matrix_world = R_WEB.copy()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "SM_InstrCard2_SC.blend"))
    tot = sum(v["tris"] for v in info.values())
    print("INSTRCARD2_OK", info, "tris_total", tot, "CURVE_R", CURVE_R, "ventana", WIN_S)
    print("INSTRCARD2_PUNTOS", corner_report(g))
    print("INSTRCARD2_ZONAS_mm", {k: round(v, 2) for k, v in g.items()})


# ------------------------------------------------------------------------------------------ QC: lee los FBX de vuelta
def qc():
    res = {}
    for nm in ("Base", "Plate", "Slider", "Trace"):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        path = os.path.join(OUT, "SM_InstrCard2_%s_SC.fbx" % nm)
        bpy.ops.import_scene.fbx(filepath=path)
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
        res[nm] = {"tris": len(areas), "abiertas": sum(1 for e in bm.edges if not e.is_manifold),
                   "degeneradas(<1e-10m2)": sum(1 for a in areas if a < 1e-10), "astillas(<0.01mm2)": sum(1 for a in areas if a < 1e-8),
                   "area_min_mm2": round(min(areas) * 1e6, 4), "dadas_vuelta": flipped, "volumen_mm3": round(signed_volume(me) * 1e9),
                   "slots": [m.name for m in me.materials], "uv": [u.name for u in me.uv_layers],
                   "caja_cm": [[round(min(c[k] for c in xs) * 100, 2) for k in range(3)], [round(max(c[k] for c in xs) * 100, 2) for k in range(3)]]}
        bm.free()
        uvd = {u.name: u for u in me.uv_layers}
        if nm == "Slider":
            us = [uvd["UVMap"].data[i].uv[0] for i in range(len(me.loops))]
            res[nm]["uv0_u_min_max"] = [round(min(us), 4), round(max(us), 4)]
        if nm == "Plate":
            def rng(layer, mi):
                vals = [uvd[layer].data[li].uv for p in me.polygons if p.material_index == mi for li in p.loop_indices]
                return [[round(min(v[k] for v in vals), 4) for k in (0, 1)], [round(max(v[k] for v in vals), 4) for k in (0, 1)]]
            res[nm]["uv0_PlateImage_min_max"] = rng("UVMap", 2)
            res[nm]["uv1_TextUV_PlateTop_min_max"] = rng("TextUV", 1)
    print("INSTRCARD2_QC", res)


# ------------------------------------------------------------------------------------------ vista previa (render)
L_DIR = Vector((-0.35, -0.30, 0.88)).normalized()
SH = {"Ambient": 0.30, "Diffuse": 0.55, "Wrap": 0.4, "Fill": 0.25, "SelfGlow": 0.10}
LIGHT = (1.0, 0.72, 0.45)
COLS = {"Body": (0.62, 0.56, 0.48), "PlateSide": (0.70, 0.64, 0.55)}
TOP = (0.17, 0.15, 0.13)             # placa oscura + tinta hueso: la opcion B recomendada en el panel v1
INK = (0.93, 0.91, 0.87, 1)


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


def shaded(name, albedo):
    m, nt, out = base_mat(name)
    em = N_(nt, "ShaderNodeEmission")
    nt.links.new(em.outputs[0], out.inputs["Surface"])
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
    tex = N_(nt, "ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value = 400.0
    k = M_(nt, 'MULTIPLY', shade, M_(nt, 'MULTIPLY_ADD', tex.outputs["Fac"], 0.12, 0.94))
    comb = N_(nt, "ShaderNodeCombineXYZ")
    for i in range(3):
        nt.links.new(M_(nt, 'MULTIPLY', k, albedo[i]), comb.inputs[i])
    nt.links.new(comb.outputs[0], em.inputs["Color"])
    return m


def text_top(name, img_path):
    m = shaded(name, TOP)
    nt = m.node_tree
    em = [n for n in nt.nodes if n.type == 'EMISSION'][0]
    src = em.inputs["Color"].links[0].from_socket
    uv = N_(nt, "ShaderNodeUVMap", uv_map="TextUV")
    tex = N_(nt, "ShaderNodeTexImage")
    tex.image = bpy.data.images.load(img_path)
    tex.image.colorspace_settings.name = 'Non-Color'
    tex.extension = 'CLIP'
    nt.links.new(uv.outputs["UV"], tex.inputs["Vector"])
    mix = N_(nt, "ShaderNodeMix", data_type='RGBA')
    nt.links.new(tex.outputs["Color"], mix.inputs["Factor"])
    nt.links.new(src, mix.inputs["A"])
    tg = N_(nt, "ShaderNodeValue", name="TextGlow")
    tg.outputs[0].default_value = 0.0
    ink = N_(nt, "ShaderNodeMix", data_type='RGBA')
    nt.links.new(tg.outputs[0], ink.inputs["Factor"])
    ink.inputs["A"].default_value = INK
    ink.inputs["B"].default_value = (LIGHT[0] * 1.25, LIGHT[1] * 1.25, LIGHT[2] * 1.25, 1)
    nt.links.new(ink.outputs["Result"], mix.inputs["B"])
    nt.links.new(mix.outputs["Result"], em.inputs["Color"])
    return m


def image_mat(name, img_path):
    m, nt, out = base_mat(name)
    em = N_(nt, "ShaderNodeEmission")
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    uv = N_(nt, "ShaderNodeUVMap", uv_map="UVMap")
    tex = N_(nt, "ShaderNodeTexImage")
    tex.image = bpy.data.images.load(img_path)
    tex.extension = 'CLIP'
    nt.links.new(uv.outputs["UV"], tex.inputs["Vector"])
    nt.links.new(tex.outputs["Color"], em.inputs["Color"])
    return m


def light(name, gain=1.0):
    m, nt, out = base_mat(name)
    em = N_(nt, "ShaderNodeEmission")
    em.inputs["Color"].default_value = (LIGHT[0], LIGHT[1], LIGHT[2], 1)
    gv = N_(nt, "ShaderNodeValue", name="Glow")
    gv.outputs[0].default_value = gain
    nt.links.new(gv.outputs[0], em.inputs["Strength"])
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    return m


def slider_mat(name):
    m, nt, out = base_mat(name)
    add = N_(nt, "ShaderNodeAddShader")
    tr = N_(nt, "ShaderNodeBsdfTransparent")
    em = N_(nt, "ShaderNodeEmission")
    nt.links.new(tr.outputs[0], add.inputs[0])
    nt.links.new(em.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], out.inputs["Surface"])
    uv = N_(nt, "ShaderNodeUVMap", uv_map="UVMap")
    sep = N_(nt, "ShaderNodeSeparateXYZ")
    nt.links.new(uv.outputs["UV"], sep.inputs[0])
    prog = N_(nt, "ShaderNodeValue", name="Progress")
    prog.outputs[0].default_value = 0.0
    mr = N_(nt, "ShaderNodeMapRange", interpolation_type='SMOOTHSTEP')
    pe = M_(nt, 'MULTIPLY', prog.outputs[0], 1.008)
    nt.links.new(M_(nt, 'SUBTRACT', pe, sep.outputs["X"]), mr.inputs["Value"])
    mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = 0.0, 0.008
    lvl = M_(nt, 'MULTIPLY', mr.outputs["Result"], 0.58)
    comb = N_(nt, "ShaderNodeCombineXYZ")
    for i in range(3):
        nt.links.new(M_(nt, 'MULTIPLY', lvl, LIGHT[i]), comb.inputs[i])
    nt.links.new(comb.outputs[0], em.inputs["Color"])
    return m


def panel(tag, mask_png, img_png, x=0.0):
    src = {k: bpy.data.objects[k] for k in ("Base", "Plate", "Slider")}
    mats = {"Body": shaded(tag + "Body", COLS["Body"]), "PlateSide": shaded(tag + "PlateSide", COLS["PlateSide"]),
            "Ring": light(tag + "Ring", 0.7), "WinRing": light(tag + "WinRing", 0.7),
            "PlateTop": text_top(tag + "PlateTop", mask_png), "PlateImage": image_mat(tag + "PlateImage", img_png),
            "Slider": slider_mat(tag + "Slider")}
    obs = {}
    for k, o in src.items():
        ob = bpy.data.objects.new(tag + k, o.data)
        bpy.context.scene.collection.objects.link(ob)
        ob.matrix_world = Matrix.Translation((x, 0, 0))
        for i, s in enumerate(ob.material_slots):
            part = o.data.materials[i].name.replace("M_InstrCard2_", "").split(".")[0]
            s.link = 'OBJECT'
            s.material = mats[part]
        obs[k] = ob
    return obs, mats


def render():
    pre = argv[2]
    scn = bpy.context.scene
    for k in ("Base", "Plate", "Slider", "Trace"):
        bpy.data.objects[k].hide_render = True
    w = bpy.data.worlds.new("Negro")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)
    scn.world = w
    scn.render.engine = 'CYCLES'
    scn.cycles.samples = 48
    scn.cycles.transparent_max_bounces = 16
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
    scn.render.resolution_x, scn.render.resolution_y = 1600, 960
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    scn.collection.objects.link(cam)
    scn.camera = cam
    tg = Vector((0.0, 0.0, 0.03))
    cam.location = tg + Vector((0.0, -0.06, 1.0)).normalized() * 1.5
    cam.rotation_euler = (tg - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = 50
    outs = []

    def clear():
        for o in [o for o in bpy.data.objects if o.name[:2] == "P_"]:
            bpy.data.objects.remove(o)
    for (key, pg) in PAGES:
        clear()
        pn, ms = panel("P_", os.path.join(OUT, "T_Instr2_%s_P%d.png" % (key, pg)), os.path.join(OUT, "T_DemoInstrImg_%s_%d.png" % (key, pg)))
        p = "%s_%s_P%d.png" % (pre, key, pg)
        scn.render.filepath = p
        bpy.ops.render.render(write_still=True)
        outs.append(p)
    clear()
    pn, ms = panel("P_", os.path.join(OUT, "T_Instr2_Breath_P4.png"), os.path.join(OUT, "T_DemoInstrImg_Breath_4.png"))
    cam.data.type = 'ORTHO'                                                      # desde arriba (el eje de la curva), ortografica: se ve el arco
    cam.data.ortho_scale = 1.0
    cam.location = Vector((0.0, 2.0, 0.045))
    cam.rotation_euler = Vector((0.0, -1.0, 0.0)).to_track_quat('-Z', 'Y').to_euler()
    scn.render.resolution_x, scn.render.resolution_y = 1600, 560
    scn.render.filepath = pre + "_curva.png"
    bpy.ops.render.render(write_still=True)
    outs.append(scn.render.filepath)
    cam.data.type = 'PERSP'                                                      # hover: la placa +1 mm, cinta y texto encendidos
    cam.data.lens = 50
    scn.render.resolution_x, scn.render.resolution_y = 1600, 960
    cam.location = Vector((0.0, 0.0, 0.03)) + Vector((0.0, -0.06, 1.0)).normalized() * 1.5
    cam.rotation_euler = (Vector((0.0, 0.0, 0.03)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    pn["Plate"].matrix_world = Matrix.Translation((0.0, 0, HOVER / 1000.0))
    for k in ("Ring", "WinRing"):
        ms[k].node_tree.nodes["Glow"].outputs[0].default_value = 1.0
    ms["PlateTop"].node_tree.nodes["TextGlow"].outputs[0].default_value = 1.0
    scn.render.filepath = pre + "_hover.png"
    bpy.ops.render.render(write_still=True)
    outs.append(scn.render.filepath)
    print("INSTRCARD2_RENDER_OK", outs)


if __name__ == "__main__":
    try:
        {"build": main, "qc": qc, "render": render}[MODE]()
    except BaseException as e:
        print("INSTRCARD2_FALLO", type(e).__name__, e)
        traceback.print_exc()
