# gen_demo_card.py - el "cuadro de experiencia" del menu de la DEMO (Barcelona Design Week, 2026-10-21): dos cuadros,
# ENTERING (Breath) y SURROUNDING (Draw), que se apuntan con el laser y se aprietan con el gatillo.
# Es el SHARE (gen_share_button.py) con el contorno de 300 x 190 mm y la MISMA seccion, partes, slots, ejes y origen:
# el Blueprint duplicado del SHARE solo cambia las mallas.
#   SM_DemoCard_Base_SC    borde redondeado + CANAL alrededor de la placa cuyo fondo es la CINTA DE LUZ. Body · Ring
#   SM_DemoCard_Plate_SC   la placa con el nombre de la experiencia: +1 mm con el hover, -4 mm al apretar.
#                          PlateSide · PlateTop (slot 1). UV1 "TextUV" = planar sobre el tope: mascara de texto
#   SM_DemoCard_Slider_SC  aro plano TRANSPARENTE abajo y afuera: la confirmacion da la vuelta al perimetro. Slider
#   SM_DemoCard_Trace_SC   el trazo de luz de la aparicion "luz primero" (M_AppearTrace_SC)
#   T_DemoCard_<X>_Text.png  mascara con SOLO el titulo, centrado (el contrato, como T_Share_Text)
#   T_DemoCard_<X>_Full.png  OPCIONAL, mismo UV y misma textura de parametro: icono arriba + titulo + subtitulo
# Ejes: construccion acostado (cara +Z, +Y = arriba del texto, mm), como el SHARE.
#   FBX (Unreal)  PARADO, cara hacia +X, arriba +Z; origen = centro de la ESPALDA; el ancho va por Y; la placa se mueve en X
#   .blend        parado, cara hacia -Y de Blender = +Z de glTF, arriba +Y de glTF (como el .blend del SHARE)
# Uso: blender --background --python gen_demo_card.py -- <dir_salida> [--v2]  (mallas, FBX y .blend; --v2 = 360 x 300 con descripcion)
#      python gen_demo_card.py --text <dir_salida>                           (Python del SISTEMA: las mascaras PNG)
import math
import os
import sys
import traceback

A, B, RC = 150.0, 95.0, 36.0         # semiejes y radio de esquina del contorno exterior (mm): 300 x 190
H_RIM = 15.0                         # --- la misma seccion que el SAVE MELODY / el SHARE ---
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
N_ARC = 12                           # tramos por esquina; los tramos rectos NO se subdividen (todo lo que se le hace es afin)
TITLE_CAP_MM = 18.0                  # mayuscula del titulo (el SHARE: 11 mm en una placa de 49,6; aca la placa es 169,6)
TITLE_TRACK = 0.08
SUB_CAP_MM = 9.0                     # subtitulo de la variante Full
SUB_TRACK = 0.10
# variante Full: posiciones (mm desde el centro de la placa, +y = arriba)
FULL_ICON_Y, FULL_TITLE_Y, FULL_SUB_Y = 31.0, -17.0, -55.0
LABELS = {"Entering": ("ENTERING", "BREATHE WITH THE LIGHT"), "Surrounding": ("SURROUNDING", "DRAW IN THE AIR"),
          "Recognizing": ("RECOGNIZING", "LISTEN TO YOUR HEART")}   # 2026-10-20: la tercera experiencia (Heart)
FONT = r"C:/Users/beltr/AppData/Local/Microsoft/Windows/Fonts/Avenir Book.ttf"

# --- v2 (2026-10-20 tarde, pedido de Beltran: "los cuadros mas grandes y con un pequeno texto explicativo; el tamano de los textos
# esta bien"): --v2 = 360 x 300 mm, mismas letras (titulo 18 mm, subtitulo 9 mm) + 3 lineas de descripcion de 8 mm.
# Mallas SM_DemoCard2_*, mascaras T_DemoCard2_<X>_Full.png. La v1 (300 x 190) queda igual sin --v2.
# --v3 (2026-10-20 noche, Beltran: "texto demasiado pequeno para la explicacion; quizas cuadros mas verticales"):
# 300 x 420 mm, misma letra de titulo y subtitulo, descripcion de 12,5 mm (era 8). Mallas SM_DemoCard3_*, mascaras T_DemoCard3_*.
V3 = "--v3" in sys.argv
V2 = "--v2" in sys.argv or V3
PREFIX = "SM_DemoCard3_" if V3 else ("SM_DemoCard2_" if V2 else "SM_DemoCard_")
TPREFIX = "T_DemoCard3_" if V3 else ("T_DemoCard2_" if V2 else "T_DemoCard_")
TEX_W = 1536 if V3 else 2048
DESC_CAP_MM, DESC_STEP_MM, DESC_Y0, DESC_SIDE_MM = 8.0, 14.5, -58.0, 26.0
SEP_Y = -40.0
if V2 and not V3:
    A, B, RC = 180.0, 150.0, 40.0
    FULL_ICON_Y, FULL_TITLE_Y, FULL_SUB_Y = 54.0, 4.0, -24.0
if V3:
    A, B, RC = 150.0, 210.0, 40.0
    # dos tamanos de letra como maximo (Beltran): titulo 18 mm; subtitulo y descripcion, los dos de 11,5 mm
    FULL_ICON_Y, FULL_TITLE_Y, FULL_SUB_Y = 92.0, 36.0, 6.0
    SEP_Y = -15.0
    DESC_CAP_MM, DESC_STEP_MM, DESC_Y0, DESC_SIDE_MM = 11.5, 20.0, -42.0, 20.0
    SUB_CAP_MM, SUB_TRACK = 11.5, 0.05
DESC = {"Entering": "Rest a sensor on your belly and breathe slowly. A light in front of you moves with every breath.",
        "Recognizing": "Hold a sensor to your chest and stay still. Every heartbeat becomes a pulse of light and sound around you.",
        "Surrounding": "Paint with light in the space around you, while we gently listen to your heart and your mind."}


# ------------------------------------------------------------------------------------------ mascaras (Python del sistema)
def make_masks(out):
    """Mascaras blanco sobre negro sobre el tope COMPLETO de la placa (0..1 = el tope). SIN voltear (ver save-melody.md)."""
    from PIL import Image, ImageChops, ImageDraw, ImageFont
    ap, bp = A + PLATE_D, B + PLATE_D
    W = TEX_W
    H = int(round(W * bp / ap))
    pxmm = W / (2 * ap)
    report = {}

    def font_for(cap_mm):
        target = cap_mm * pxmm
        best = None
        for s in range(20, 400):
            f = ImageFont.truetype(FONT, s)
            cap = -f.getbbox("H", anchor="ls")[1]
            if best is None or abs(cap - target) < best[0]:
                best = (abs(cap - target), f, cap)
        return best[1], best[2]

    def line(dr, text, cap_mm, y_mm, track, fill=255):
        """Texto centrado en x; y_mm = centro de la mayuscula (+y arriba). Devuelve el ancho en mm."""
        f, cap = font_for(cap_mm)
        tr = f.size * track
        widths = [dr.textlength(c, font=f) for c in text]
        total = sum(widths) + tr * (len(text) - 1)
        x = (W - total) / 2
        base = H / 2 - y_mm * pxmm + cap / 2
        for c, w in zip(text, widths):
            dr.text((x, base), c, font=f, fill=fill, anchor="ls")
            x += w + tr
        return round(total / pxmm, 1)

    def paste_icon(img, kind, y_mm):
        S = 3                                                   # supersample local
        pw, ph = 110.0, 66.0                                    # mm del parche
        wpx, hpx = int(pw * pxmm), int(ph * pxmm)
        big = Image.new("L", (wpx * S, hpx * S), 0)
        d = ImageDraw.Draw(big)
        c = (wpx * S / 2, hpx * S / 2)
        k = pxmm * S                                            # px por mm en el parche grande

        def disc(x, y, r, v=255):
            d.ellipse((c[0] + (x - r) * k, c[1] - (y + r) * k, c[0] + (x + r) * k, c[1] - (y - r) * k), fill=v)

        def ring(r, wmm, v):
            d.ellipse((c[0] - r * k, c[1] - r * k, c[0] + r * k, c[1] + r * k), outline=v, width=int(wmm * k))

        if kind == "Recognizing":                               # la linea del pulso: un latido entre dos tramos quietos
            pts = [(-30, 0), (-11, 0), (-7, 5), (-4, 0), (-1, 0), (2, -11), (6, 17), (10, -7), (13, 0), (17, 0), (20, 4), (23, 0), (30, 0)]
            for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
                n = max(2, int(math.hypot(x1 - x0, y1 - y0) * 4))
                for i in range(n + 1):
                    t = i / n
                    disc(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, 1.05)
            disc(30, 0, 2.6)
        elif kind == "Entering":                                # ondas que se abren desde un punto: el soplo
            disc(0, 0, 2.6)
            for r, v in ((9.5, 235), (17.5, 165), (25.5, 105)):
                ring(r, 1.3, v)
        else:                                                   # un trazo con bucle (cursiva) que termina en la punta del pincel
            n = 420
            t0, t1 = -1.1 * math.pi, 1.3 * math.pi
            rr, dd, fy = 6.0, 15.0, 0.60                        # cicloide prolata: x = rr·t − dd·sin t, y = −fy·dd·cos t
            pts = []
            for i in range(n + 1):
                t = t0 + (t1 - t0) * i / n
                pts.append((rr * t - dd * math.sin(t), -fy * dd * math.cos(t)))
            cx = (min(q[0] for q in pts) + max(q[0] for q in pts)) / 2
            cy = (min(q[1] for q in pts) + max(q[1] for q in pts)) / 2
            for i, (x, y) in enumerate(pts):
                disc(x - cx, y - cy, 0.5 + 0.8 * i / n)
            disc(pts[-1][0] - cx, pts[-1][1] - cy, 2.6)
        small = big.resize((wpx, hpx), Image.LANCZOS)
        px = int(W / 2 - wpx / 2)
        py = int(H / 2 - y_mm * pxmm - hpx / 2)
        region = Image.new("L", (W, H), 0)
        region.paste(small, (px, py))
        return ImageChops.lighter(img, region)

    def wrap(dr, text, cap_mm, max_mm):
        """Corta en lineas que entren en max_mm (sin tracking: es texto corrido)."""
        f, cap = font_for(cap_mm)
        lines, cur = [], ""
        for w in text.split():
            t = (cur + " " + w).strip()
            if dr.textlength(t, font=f) / pxmm <= max_mm or not cur:
                cur = t
            else:
                lines.append(cur); cur = w
        if cur:
            lines.append(cur)
        return lines

    for key, (title, sub) in LABELS.items():
        img = Image.new("L", (W, H), 0)
        w_t = line(ImageDraw.Draw(img), title, TITLE_CAP_MM, 0.0, TITLE_TRACK)
        img.save(os.path.join(out, TPREFIX + "%s_Text.png" % key))
        full = Image.new("L", (W, H), 0)
        dr = ImageDraw.Draw(full)
        line(dr, title, TITLE_CAP_MM, FULL_TITLE_Y, TITLE_TRACK)
        w_s = line(dr, sub, SUB_CAP_MM, FULL_SUB_Y, SUB_TRACK, fill=200)
        desc = []
        if V2:
            sw = 34.0 * pxmm                                    # un filo corto entre el subtitulo y la descripcion
            y = H / 2 - SEP_Y * pxmm
            dr.rectangle((W / 2 - sw / 2, y - 0.35 * pxmm, W / 2 + sw / 2, y + 0.35 * pxmm), fill=110)
            desc = wrap(dr, DESC[key], DESC_CAP_MM, 2 * (A + PLATE_D) - 2 * DESC_SIDE_MM)
            for i, ln in enumerate(desc):
                line(dr, ln, DESC_CAP_MM, DESC_Y0 - i * DESC_STEP_MM, 0.0, fill=215)
        full = paste_icon(full, key, FULL_ICON_Y)
        full.save(os.path.join(out, TPREFIX + "%s_Full.png" % key))
        if desc:
            report[key + "_desc"] = desc
        report[key] = {"png": [W, H], "titulo_ancho_mm": w_t, "subtitulo_ancho_mm": w_s,
                       "bbox_titulo_px": img.getbbox()}
    return report


if "--text" in sys.argv:                                  # Python del sistema: solo las mascaras
    out = sys.argv[sys.argv.index("--text") + 1]
    os.makedirs(out, exist_ok=True)
    print("TEXTO_OK", make_masks(out), "placa_mm", [round(2 * (A + PLATE_D), 1), round(2 * (B + PLATE_D), 1)])
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
    specs = ((PREFIX + "Base_SC", base_profile(), ("Body", "Ring"), False, ("first", "last"), ("Body", "Ring")),
             (PREFIX + "Plate_SC", plate_profile(), ("PlateSide", "PlateTop"), False, ("first", "last"), ("PlateSide", "PlateTop")),
             (PREFIX + "Slider_SC", slider_profile(), ("Slider",), True, (), ()))
    for name, prof, parts, closed, caps, cap_parts in specs:
        me, flips = sweep_rrect(name, prof, parts, A, B, RC, closed=closed, caps=caps, cap_parts=cap_parts)
        if name.endswith("Slider_SC"):
            slider_uv(me)
        if name.endswith("Plate_SC"):
            text_uv(me, parts)
        for p in parts:
            me.materials.append(bpy.data.materials.new("M_DemoCard_" + p))
        info[name] = checks(me, len(parts))
        info[name]["dadas_vuelta"] = flips
        if not closed or True:
            info[name]["volumen_mm3"] = round(signed_volume(me) * 1e9)
        meshes.append(me)
    cfg = {"path": [(p[0], p[1]) for p in rrect_outline(A, B, RC, -7.5)], "z": H_RIM, "hw": 7.0, "face": 1.0}
    tr = LZ.trace_mesh(cfg, PREFIX + "Trace_SC")
    tr.materials.append(bpy.data.materials.new("M_DemoCard_Trace"))
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
        ob = bpy.data.objects.new(me.name.replace(PREFIX, "").replace("_SC", ""), me)
        col.objects.link(ob)
        ob.matrix_world = R_WEB.copy()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, PREFIX + "SC.blend"))
    tot = sum(v["tris"] for v in info.values())
    print("DEMOCARD_OK", info, "tris_total", tot, "recorrido_mm", TRAVEL, "hover_mm", HOVER)


if __name__ == "__main__":
    try:
        main()
    except BaseException as e:
        print("DEMOCARD_FALLO", type(e).__name__, e)
        traceback.print_exc()
