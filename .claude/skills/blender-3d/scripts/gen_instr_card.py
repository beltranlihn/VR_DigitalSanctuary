# gen_instr_card.py - el PANEL DE INSTRUCCIONES de cada experiencia de la demo (Barcelona Design Week, 2026-10-21): reemplaza
# al widget de Calibration. Misma familia y MISMA estructura que el cuadro de experiencia (gen_demo_card.py) y el SHARE
# (gen_share_button.py): marco + canal con cinta de luz + placa; el panel entero es el boton ("apunta y aprieta el gatillo").
# ~640 x 400 mm (se lee a ~1,3 m), esquinas en proporcion, misma seccion.
#   SM_InstrCard_Base_SC    borde redondeado + CANAL cuyo fondo es la CINTA DE LUZ. Body · Ring
#   SM_InstrCard_Plate_SC   la placa: +1 mm con el hover, -4 mm al apretar. PlateSide · PlateTop (slot 1)
#                           UV1 "TextUV" = planar sobre el tope ENTERO: la pagina entera es UNA mascara blanco/negro
#   SM_InstrCard_Slider_SC  aro plano TRANSPARENTE abajo y afuera (Progress 0-1 da la vuelta al perimetro). Slider
#   SM_InstrCard_Trace_SC   el trazo de luz de la aparicion "luz primero" (M_AppearTrace_SC)
#   T_Instr_<Entering|Surrounding>_P1..P3.png   las 6 paginas: icono lineal arriba + texto (centrado) + pie chico abajo
# Ejes: construccion acostado (cara +Z, +Y = arriba del texto, mm); FBX (Unreal) PARADO, cara +X, arriba +Z, ancho por Y,
#   origen = centro de la ESPALDA; .blend parado como el del SHARE.
# Uso: blender --background --python gen_instr_card.py -- <dir_salida>        (mallas, FBX y .blend)
#      python gen_instr_card.py --text <dir_salida>                           (Python del SISTEMA: las 6 mascaras PNG)
import math
import os
import sys
import traceback

A, B, RC = 320.0, 200.0, 64.0        # semiejes y radio de esquina del contorno exterior (mm): 640 x 400
H_RIM = 15.0                         # --- la misma seccion que el SAVE MELODY / SHARE / cuadro de experiencia ---
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
N_ARC = 12                           # tramos por esquina; los tramos rectos NO se subdividen
FONT = r"C:/Users/beltr/AppData/Local/Microsoft/Windows/Fonts/Avenir Book.ttf"
# ---- la pagina (mm desde el centro de la placa, +y = arriba). Quest 3 a 1,3 m: texto >= 22 mm de mayuscula, pie >= 14 mm
BODY_CAP_MM, FOOT_CAP_MM = 23.0, 14.5
BODY_LEAD, FOOT_LEAD = 1.30, 1.30    # interlineado (x el cuerpo del tipo)
TEXT_MAX_W = 540.0                   # ancho maximo del bloque (la placa tiene 619,6)
ICON_Y = 108.0                       # centro del icono (banda de ~100 mm)
BODY_Y0 = 24.0                       # centro de la mayuscula de la primera linea del cuerpo
FOOT_LAST_Y = -156.0                 # centro de la mayuscula de la ULTIMA linea del pie
BODY_V, FOOT_V = 255, 200            # intensidad de la mascara
# Textos FINALES: docs/demo/INSTRUCCIONES-DEMO.md (copiados tal cual). Pie = None en la ultima pagina.
FOOT_1 = "Point and press the trigger under your index finger to continue."
FOOT_2 = "Press the trigger to continue."
PAGES = {
    ("Entering", 1): ("Settle in. For the next few minutes, your breath leads. Light, air and space will move with you.", FOOT_1, "orb"),
    ("Entering", 2): ("Rest the sensor just below your ribs, flat side against your belly. Stay still and breathe slowly. "
                      "Feel it rise and fall with you.", FOOT_2, "belly"),
    ("Entering", 3): ("Soft rings of light will guide your rhythm. There is nothing to get right \u2014 just breathe. "
                      "Point at this panel and press the trigger to begin.", None, "rings"),
    ("Surrounding", 1): ("The air around you is your canvas. For the next few minutes, draw what you carry inside \u2014 with light.",
                         FOOT_1, "swoop"),
    ("Surrounding", 2): ("Your brush is the glowing tip of your controller. Touch a color or brush on the palette floating at "
                         "your other hand to choose it.", FOOT_2, "palette"),
    ("Surrounding", 3): ("Hold the trigger and move your hand to draw \u2014 the harder you press, the bolder the line. "
                         "Point at this panel and press the trigger to begin.", None, "trigger"),
}


# ------------------------------------------------------------------------------------------ mascaras (Python del sistema)
def make_masks(out):
    """Mascaras blanco sobre negro sobre el tope COMPLETO de la placa (0..1 = el tope). SIN voltear (ver save-melody.md)."""
    from PIL import Image, ImageChops, ImageDraw, ImageFont
    ap, bp = A + PLATE_D, B + PLATE_D
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
        for w in text.split():                                  # el guion largo se pega a la palabra anterior
            if w == "\u2014" and words:
                words[-1] += " " + w
            else:
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

    def put_lines(dr, lines, cap_mm, y_first_mm, lead, fill):
        """Lineas centradas en x; y_first_mm = centro de la mayuscula de la primera (+y arriba). Devuelve (anchos_mm, ys)."""
        f, cap = font_for(cap_mm)
        pitch = f.size * lead
        ws, ys = [], []
        for k, ln in enumerate(lines):
            base = H / 2 - y_first_mm * pxmm + cap / 2 + k * pitch
            dr.text((W / 2, base), ln, font=f, fill=fill, anchor="ms")
            ws.append(round(probe.textlength(ln, font=f) / pxmm, 1))
            ys.append(round(y_first_mm - k * pitch / pxmm, 1))
        return ws, ys, pitch / pxmm

    # ---------------------------------------------------------------- iconos (lineales, trazo >= 2,6 mm: se leen a 1,3 m)
    class Patch:
        """Lienzo local de iconos con supersample 3x. Coordenadas en mm desde el centro del icono, +y arriba."""
        S = 3

        def __init__(self, pw=280.0, ph=130.0, zoom=1.0):
            self.pw, self.ph, self.z = pw, ph, zoom
            self.wpx, self.hpx = int(pw * pxmm), int(ph * pxmm)
            self.img = Image.new("L", (self.wpx * self.S, self.hpx * self.S), 0)
            self.k = pxmm * self.S

        def _xy(self, x, y):
            return (self.wpx * self.S / 2 + x * self.z * self.k, self.hpx * self.S / 2 - y * self.z * self.k)

        def _lay(self, fn):
            t = Image.new("L", self.img.size, 0)
            fn(ImageDraw.Draw(t))
            self.img = ImageChops.lighter(self.img, t)

        def disc(self, x, y, r, v=255):
            cx, cy = self._xy(x, y)
            r = r * self.z
            self._lay(lambda d: d.ellipse((cx - r * self.k, cy - r * self.k, cx + r * self.k, cy + r * self.k), fill=v))

        def circle(self, x, y, r, w=2.8, v=255):
            cx, cy = self._xy(x, y)
            r, w = r * self.z, w * self.z
            self._lay(lambda d: d.ellipse((cx - r * self.k, cy - r * self.k, cx + r * self.k, cy + r * self.k),
                                          outline=v, width=max(1, int(w * self.k))))

        def glow(self, x, y, r, v=255, power=1.8, steps=48):
            cx, cy = self._xy(x, y)
            r = r * self.z

            def fn(d):
                for i in range(steps):                        # de afuera (tenue) hacia adentro (brillante)
                    t = i / (steps - 1)
                    rr = r * (1 - t)
                    d.ellipse((cx - rr * self.k, cy - rr * self.k, cx + rr * self.k, cy + rr * self.k), fill=int(v * t ** power))
            self._lay(fn)

        def line(self, pts, w=2.8, v=255, taper=None):
            """Polilinea con puntas redondas; taper=(w0, w1) cambia el grosor a lo largo."""
            n = len(pts)
            w = w * self.z
            if taper is None:
                p = [self._xy(*q) for q in pts]
                hw = w * self.k / 2

                def fn(d):
                    d.line(p, fill=v, width=max(1, int(w * self.k)), joint="curve")
                    for a, b in (p[0], p[-1]):
                        d.ellipse((a - hw, b - hw, a + hw, b + hw), fill=v)
                self._lay(fn)
            else:
                for i, q in enumerate(pts):
                    self.disc(q[0], q[1], (taper[0] + (taper[1] - taper[0]) * i / max(n - 1, 1)) / 2, v)

        def bez(self, p0, p1, p2, p3, n=60):
            out = []
            for i in range(n + 1):
                t = i / n
                a = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
                out.append((sum(a[j] * q[0] for j, q in enumerate((p0, p1, p2, p3))), sum(a[j] * q[1] for j, q in enumerate((p0, p1, p2, p3)))))
            return out

        def capsule(self, p, q, w, wline=2.8, v=255, fill=None):
            """Capsula (rectangulo de puntas redondas) de eje p-q y ancho w; contorno (o relleno si fill)."""
            dx, dy = q[0] - p[0], q[1] - p[1]
            L = math.hypot(dx, dy)
            ux, uy = dx / L, dy / L
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
            if fill is not None:
                pp = [self._xy(*t) for t in pts]
                self._lay(lambda d: d.polygon(pp, fill=fill))
            else:
                self.line(pts + [pts[0]], wline, v)

        def arrowhead(self, tip, direction, size=7.0, w=2.8, v=255):
            ang = math.atan2(direction[1], direction[0])
            for s in (+1, -1):
                a = ang + math.pi + s * math.radians(35)
                self.line([tip, (tip[0] + size * math.cos(a), tip[1] + size * math.sin(a))], w, v)

        def small(self):
            return self.img.resize((self.wpx, self.hpx), Image.LANCZOS)

    def icon_orb(c):                                           # esfera de luz que se infla y se desinfla: disco difuso + ondas
        c.glow(0, 0, 40, 255, power=0.9)
        c.circle(0, 0, 41, 2.6, 190)
        c.circle(0, 0, 51, 2.4, 120)
        c.circle(0, 0, 60, 2.2, 70)

    def icon_belly(c):                                         # sentado de perfil, el sensor plano bajo las costillas
        c.circle(-6, 40, 9.5, 3.0, 235)                          # cabeza
        c.line(c.bez((-13, 30), (-27, 18), (-25, -5), (-19, -24)), 3.0, 235)                  # espalda
        c.line(c.bez((3, 31), (12, 18), (13, 5), (12, -7)) + c.bez((12, -7), (14, -14), (9, -20), (3, -24))[1:], 3.0, 235)   # pecho y panza
        c.line([(-19, -24), (38, -27), (38, -50)], 3.0, 235)                                     # muslo y pierna
        c.capsule((17.5, -12), (17.5, 10), 6.5, fill=255)                                        # el sensor, de canto, contra la panza
        c.line([(37, -12), (37, 14)], 2.6, 190)                                                  # sube y baja
        c.arrowhead((37, 14), (0, 1), 6.5, 2.6, 190)
        c.arrowhead((37, -12), (0, -1), 6.5, 2.6, 190)

    def icon_rings(c):                                         # los aros del pacer: uno abriendose
        c.disc(0, 0, 4.0, 255)
        for r, v in ((14, 255), (27, 215), (40, 160), (53, 100)):
            c.circle(0, 0, r, 3.0, v)
        c.circle(0, 0, 63, 2.4, 55)

    def icon_swoop(c):                                         # un trazo de luz suspendido en la oscuridad, con la punta brillante
        n = 420
        t0, t1 = -1.1 * math.pi, 1.3 * math.pi
        rr, dd, fy = 8.6, 21.0, 0.58
        pts = [(rr * (t0 + (t1 - t0) * i / n) - dd * math.sin(t0 + (t1 - t0) * i / n),
                -fy * dd * math.cos(t0 + (t1 - t0) * i / n)) for i in range(n + 1)]
        cx = (min(q[0] for q in pts) + max(q[0] for q in pts)) / 2
        cy = (min(q[1] for q in pts) + max(q[1] for q in pts)) / 2
        pts = [(x - cx, y - cy) for x, y in pts]
        c.line(pts, taper=(1.2, 4.2), v=255)
        c.glow(pts[-1][0], pts[-1][1], 15, 150, power=1.2)
        c.disc(pts[-1][0], pts[-1][1], 4.6, 255)

    def icon_palette(c):                                       # el mando con la punta brillante toca una tecla de la paleta
        px, py, R = -34.0, -6.0, 38.0
        c.circle(px, py, R, 3.0, 215)
        c.circle(px, py, 12, 2.4, 130)
        touched = None
        for k in range(8):
            a = math.radians(90 - 45 * k + 22.5)
            x, y = px + 26 * math.cos(a), py + 26 * math.sin(a)
            if k == 1:
                touched = (x, y)
                c.disc(x, y, 6.0, 255)
            elif k % 2 == 0:
                c.disc(x, y, 4.8, 170)
            else:
                c.circle(x, y, 5.0, 2.4, 170)
        tx, ty = touched
        ux, uy = math.cos(math.radians(26)), math.sin(math.radians(26))
        c.capsule((tx + 9 * ux, ty + 9 * uy), (tx + 66 * ux, ty + 66 * uy), 11.0, 3.0, 235)      # el mando
        c.circle(tx + 73 * ux, ty + 73 * uy, 10.0, 2.8, 150)                                       # su aro
        c.glow(tx, ty, 13, 200, power=1.2)
        c.disc(tx, ty, 4.0, 255)

    def icon_trigger(c):                                       # gatillo apretado y un trazo que engrosa
        c.capsule((-62, -30), (-50, 24), 21.0, 3.0, 235)                                         # la empunadura
        c.line(c.bez((-38, 20), (-27, 11), (-27, -6), (-36, -14)), 4.2, 255)                     # el gatillo, hundido
        c.line([(-10, -2), (-24, -2)], 2.8, 190)                                                 # la presion: lo empuja
        c.arrowhead((-24, -2), (-1, 0), 7.0, 2.8, 190)
        pts = c.bez((-42, 36), (-10, 66), (22, -34), (88, 18), n=300)
        c.line(pts, taper=(1.2, 10.0), v=255)
        c.glow(pts[0][0], pts[0][1], 12, 150, power=1.2)

    ICONS = {"orb": (icon_orb, 0.85), "belly": (icon_belly, 1.1), "rings": (icon_rings, 0.9), "swoop": (icon_swoop, 1.5),
             "palette": (icon_palette, 1.0), "trigger": (icon_trigger, 1.15)}

    for (key, pg), (body, foot, icon) in PAGES.items():
        img = Image.new("L", (W, H), 0)
        dr = ImageDraw.Draw(img)
        fb, _ = font_for(BODY_CAP_MM)
        lines = balanced(body, fb, TEXT_MAX_W)
        bw, by, _ = put_lines(dr, lines, BODY_CAP_MM, BODY_Y0, BODY_LEAD, BODY_V)
        fw = []
        if foot:
            ff, _ = font_for(FOOT_CAP_MM)
            flines = balanced(foot, ff, TEXT_MAX_W)
            pitch_mm = ff.size * FOOT_LEAD / pxmm
            fw, fy, _ = put_lines(dr, flines, FOOT_CAP_MM, FOOT_LAST_Y + (len(flines) - 1) * pitch_mm, FOOT_LEAD, FOOT_V)
        fn, zoom = ICONS[icon]
        c = Patch(zoom=zoom)
        fn(c)
        small = c.small()
        region = Image.new("L", (W, H), 0)
        region.paste(small, (int(W / 2 - c.wpx / 2), int(H / 2 - ICON_Y * pxmm - c.hpx / 2)))
        img = ImageChops.lighter(img, region)
        img.save(os.path.join(out, "T_Instr_%s_P%d.png" % (key, pg)))
        report["%s_P%d" % (key, pg)] = {"lineas_cuerpo": len(lines), "ancho_max_cuerpo_mm": max(bw), "lineas_pie": len(fw),
                                        "ancho_max_pie_mm": max(fw) if fw else None, "y_ultima_linea_cuerpo_mm": by[-1]}
    report["png"] = [W, H]
    return report


if "--text" in sys.argv:                                  # Python del sistema: solo las mascaras
    out = sys.argv[sys.argv.index("--text") + 1]
    os.makedirs(out, exist_ok=True)
    rep = make_masks(out)
    for k, v in rep.items():
        print("TEXTO_OK", k, v)
    print("placa_mm", [round(2 * (A + PLATE_D), 1), round(2 * (B + PLATE_D), 1)])
    sys.exit(0)

import bpy                                                # noqa: E402
from mathutils import Matrix                              # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import functools                                          # noqa: E402
import revolve_lib as RL                                  # noqa: E402
RL.rrect_outline = functools.partial(RL.rrect_outline, n_arc=N_ARC, step=1.0e6)   # rectos sin subdividir
from revolve_lib import checks, export_fbx, fillet_poly, sweep_rrect   # noqa: E402
rrect_outline = RL.rrect_outline
import anim_luz_objects as LZ                             # noqa: E402  (trace_mesh)

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else "."
R_UE = Matrix(((0.0, 0.0, 1.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0))).to_4x4()    # cara +Z -> +X, arriba +Y -> +Z
R_WEB = Matrix(((1.0, 0.0, 0.0), (0.0, 0.0, -1.0), (0.0, 1.0, 0.0))).to_4x4()  # cara +Z -> -Y, arriba +Y -> +Z


def base_profile():
    P = [(-8.0, 0.0, 0.0, "Body"), (0.0, 0.0, F_OUT_BOT, "Body"), (0.0, H_RIM, F_OUT_TOP, "Body"),
         (-RIM_W, H_RIM, F_RIM_IN, "Body"), (-RIM_W, H_LIGHT, 0.0, "Ring"), (-RIM_W, H_FLOOR, 1.0, "Ring"),
         (-(RC - 8.0), H_FLOOR, 0.0, "Ring")]
    return fillet_poly(P)


def plate_profile():
    d0 = -(RC - 3.0)
    P = [(d0, H_PLATE_BOT, 0.0, "PlateSide"), (PLATE_D, H_PLATE_BOT, 1.0, "PlateSide"),
         (PLATE_D, H_PLATE_TOP, F_PLATE, "PlateSide"), (d0, H_PLATE_TOP, 0.0, "PlateTop")]
    pts = fillet_poly(P)
    return [(d, h, "PlateTop" if (h >= H_PLATE_TOP - 1e-6) else p) for d, h, p in pts]


def slider_profile():
    mid = (S_IN + S_OUT) / 2
    P = [(mid, 0.0, 0.0, "Slider"), (S_OUT, 0.0, S_F, "Slider"), (S_OUT, S_T, S_F, "Slider"), (S_IN, S_T, S_F, "Slider"),
         (S_IN, 0.0, S_F, "Slider"), (mid, 0.0, 0.0, "Slider")]
    return fillet_poly(P)[:-1]


def slider_uv(me):
    """UV0.x = fraccion del perimetro (horario desde arriba al centro, visto de frente en Blender)."""
    ring = rrect_outline(A, B, RC, (S_IN + S_OUT) / 2)
    L = [0.0]
    for p, q in zip(ring, ring[1:] + ring[:1]):
        L.append(L[-1] + math.hypot(q[0] - p[0], q[1] - p[1]))
    tot = L[-1]
    m = len(ring)
    uv = me.uv_layers["UVMap"]
    for p in me.polygons:
        vals = [L[me.loops[li].vertex_index % m] / tot for li in p.loop_indices]
        if max(vals) - min(vals) > 0.5:
            vals = [x + 1.0 if x < 0.5 else x for x in vals]
        for li, x in zip(p.loop_indices, vals):
            uv.data[li].uv = (x, uv.data[li].uv[1])


def text_uv(me, parts):
    """UV1 'TextUV': planar sobre el tope de la placa (0..1 = el tope completo); el resto afuera (-1)."""
    ap, bp = A + PLATE_D, B + PLATE_D
    tu = me.uv_layers.new(name="TextUV")
    top = parts.index("PlateTop")
    for p in me.polygons:
        for li in p.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co * 1000.0
            tu.data[li].uv = ((co.x + ap) / (2 * ap), (co.y + bp) / (2 * bp)) if p.material_index == top else (-1.0, -1.0)


def export_ue(me, path, tspace=True):
    m2 = me.copy()
    m2.transform(R_UE)
    ob = bpy.data.objects.new(me.name, m2)
    bpy.context.scene.collection.objects.link(ob)
    (export_fbx if tspace else LZ.export_fbx)(ob, path)
    bpy.data.objects.remove(ob)
    bpy.data.meshes.remove(m2)


def signed_volume(me):
    me.calc_loop_triangles()
    s = 0.0
    for t in me.loop_triangles:
        a, b, c = (me.vertices[i].co for i in t.vertices)
        s += a.dot(b.cross(c)) / 6.0
    return s


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    info, meshes = {}, []
    specs = (("SM_InstrCard_Base_SC", base_profile(), ("Body", "Ring"), False, ("first", "last"), ("Body", "Ring")),
             ("SM_InstrCard_Plate_SC", plate_profile(), ("PlateSide", "PlateTop"), False, ("first", "last"), ("PlateSide", "PlateTop")),
             ("SM_InstrCard_Slider_SC", slider_profile(), ("Slider",), True, (), ()))
    for name, prof, parts, closed, caps, cap_parts in specs:
        me, flips = sweep_rrect(name, prof, parts, A, B, RC, closed=closed, caps=caps, cap_parts=cap_parts)
        if name.endswith("Slider_SC"):
            slider_uv(me)
        if name.endswith("Plate_SC"):
            text_uv(me, parts)
        for p in parts:
            me.materials.append(bpy.data.materials.new("M_InstrCard_" + p))
        info[name] = checks(me, len(parts))
        info[name]["dadas_vuelta"] = flips
        if not closed or True:
            info[name]["volumen_mm3"] = round(signed_volume(me) * 1e9)
        meshes.append(me)
    cfg = {"path": [(p[0], p[1]) for p in rrect_outline(A, B, RC, -7.5)], "z": H_RIM, "hw": 7.0, "face": 1.0}
    tr = LZ.trace_mesh(cfg, "SM_InstrCard_Trace_SC")
    tr.materials.append(bpy.data.materials.new("M_InstrCard_Trace"))
    meshes.append(tr)
    info[tr.name] = checks(tr, 1)
    os.makedirs(OUT, exist_ok=True)
    for me in meshes:
        export_ue(me, os.path.join(OUT, me.name + ".fbx"), tspace=me is not tr)
        m2 = me.copy()
        m2.transform(R_UE)
        xs = [v.co for v in m2.vertices]
        info[me.name]["caja_UE_cm_min"] = [round(min(c[k] for c in xs) * 100, 3) for k in range(3)]
        info[me.name]["caja_UE_cm_max"] = [round(max(c[k] for c in xs) * 100, 3) for k in range(3)]
        bpy.data.meshes.remove(m2)
    col = bpy.context.scene.collection
    for me in meshes:                                  # .blend armado PARADO, en la orientacion de la web
        ob = bpy.data.objects.new(me.name.replace("SM_InstrCard_", "").replace("_SC", ""), me)
        col.objects.link(ob)
        ob.matrix_world = R_WEB.copy()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "SM_InstrCard_SC.blend"))
    tot = sum(v["tris"] for v in info.values())
    print("INSTRCARD_OK", info, "tris_total", tot, "recorrido_mm", TRAVEL, "hover_mm", HOVER)


if __name__ == "__main__":
    try:
        main()
    except BaseException as e:
        print("INSTRCARD_FALLO", type(e).__name__, e)
        traceback.print_exc()
