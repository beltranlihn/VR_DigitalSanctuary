# gen_share_button.py - los botones SHARE / DON'T SHARE del cuadro de resultados (encargo de Narrativa por Beltran,
# 2026-09-30): "misma estetica que el boton SAVE y las teclas de la paleta"; se eligen con laser (hover) + gatillo;
# ~22 x 7 cm cada uno; van bajo el cuadro, separados ~30 cm.
# Es el SAVE MELODY (gen_save_melody.py) con el contorno de 220 x 70 mm (esquinas r 22) y la MISMA seccion:
#   SM_ShareButton_Base_SC    borde redondeado + CANAL alrededor de la placa cuyo fondo es la CINTA DE LUZ. Body · Ring
#   SM_ShareButton_Plate_SC   la placa-boton con el texto: +1 mm con el hover, -4 mm al apretar. PlateSide · PlateTop
#                             (UV1 "TextUV" = planar sobre el tope: mascara del texto; una textura por etiqueta)
#   SM_ShareButton_Slider_SC  aro plano TRANSPARENTE abajo y afuera: la confirmacion da la vuelta al perimetro. Slider
#   SM_ShareButton_Trace_SC   el trazo de luz de la aparicion "luz primero" (M_AppearTrace_SC)
#   T_Share_Text.png / T_DontShare_Text.png   la mascara del texto (Avenir Book, como el SAVE): gen_share_button.py
#                             con el Python del SISTEMA (Blender no trae PIL): python gen_share_button.py --text <dir>
# Ejes: construccion acostado (cara +Z, +Y = arriba del texto, mm), como el SAVE.
#   FBX (Unreal)  PARADO, cara hacia +X, arriba +Z (como el cuadro de resultados, que mira al usuario por su +X);
#                 origen = centro de la ESPALDA; la placa se mueve en X.
#   .blend / GLB  parado, cara hacia -Y de Blender = +Z de glTF, arriba +Y de glTF (la web lo usa sin rotar)
# Uso: blender --background --python gen_share_button.py -- <dir_salida>
import math
import os
import sys
import traceback

A, B, RC = 110.0, 35.0, 22.0         # semiejes y radio de esquina del contorno exterior (mm): 220 x 70
H_RIM = 15.0                         # --- la misma seccion que el SAVE MELODY ---
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
CAP_MM = 11.0                        # altura de mayuscula del texto (el SAVE: 9,5 en una placa de 39,6; aca 49,6)
LABELS = {"T_Share_Text": "SHARE", "T_DontShare_Text": "DON'T SHARE"}
FONT = r"C:/Users/beltr/AppData/Local/Microsoft/Windows/Fonts/Avenir Book.ttf"


def text_texture(path, text):
    """Mascara blanco sobre negro sobre el tope de la placa (0..1 = el tope completo). SIN voltear (ver save-melody.md)."""
    from PIL import Image, ImageDraw, ImageFont
    ap, bp = A + PLATE_D, B + PLATE_D
    W = 2048
    H = int(round(W * bp / ap))
    img = Image.new("L", (W, H), 0)
    dr = ImageDraw.Draw(img)
    size = int(CAP_MM / (2 * bp) * H / 0.72)
    font = ImageFont.truetype(FONT, size)
    track = int(size * 0.08)
    widths = [dr.textlength(c, font=font) for c in text]
    total = sum(widths) + track * (len(text) - 1)
    x = (W - total) / 2
    for c, w in zip(text, widths):
        dr.text((x, H / 2), c, font=font, fill=255, anchor="lm")
        x += w + track
    img.save(path)
    return W, H, round(total / W * 2 * ap, 1)


if "--text" in sys.argv:                              # Python del sistema: solo las texturas
    out = sys.argv[sys.argv.index("--text") + 1]
    os.makedirs(out, exist_ok=True)
    for name, text in LABELS.items():
        print("TEXTO_OK", name, text_texture(os.path.join(out, name + ".png"), text), "(ancho del texto en mm al final)")
    sys.exit(0)

import bpy                                            # noqa: E402
from mathutils import Matrix                          # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import functools                                      # noqa: E402
import revolve_lib as RL                              # noqa: E402
# los tramos RECTOS sin subdividir (el SAVE los partia cada 4 mm): el boton es plano y todo lo que se le hace es afin
# (parpado, escalas, UV lineal del slider y del texto); las esquinas r 22 con 12 tramos
RL.rrect_outline = functools.partial(RL.rrect_outline, n_arc=12, step=40.0)
from revolve_lib import checks, export_fbx, fillet_poly, sweep_rrect   # noqa: E402
rrect_outline = RL.rrect_outline
import anim_luz_objects as LZ                         # noqa: E402  (trace_mesh)

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


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    info, meshes = {}, []
    specs = (("SM_ShareButton_Base_SC", base_profile(), ("Body", "Ring"), False, ("first", "last"), ("Body", "Ring")),
             ("SM_ShareButton_Plate_SC", plate_profile(), ("PlateSide", "PlateTop"), False, ("first", "last"), ("PlateSide", "PlateTop")),
             ("SM_ShareButton_Slider_SC", slider_profile(), ("Slider",), True, (), ()))
    for name, prof, parts, closed, caps, cap_parts in specs:
        me, flips = sweep_rrect(name, prof, parts, A, B, RC, closed=closed, caps=caps, cap_parts=cap_parts)
        if name.endswith("Slider_SC"):
            slider_uv(me)
        if name.endswith("Plate_SC"):
            text_uv(me, parts)
        for p in parts:
            me.materials.append(bpy.data.materials.new("M_ShareButton_" + p))
        info[name] = checks(me, len(parts))
        info[name]["dadas_vuelta"] = flips
        meshes.append(me)
    cfg = {"path": [(p[0], p[1]) for p in rrect_outline(A, B, RC, -7.5)], "z": H_RIM, "hw": 7.0, "face": 1.0}
    tr = LZ.trace_mesh(cfg, "SM_ShareButton_Trace_SC")
    tr.materials.append(bpy.data.materials.new("M_ShareButton_Trace"))
    meshes.append(tr)
    info[tr.name] = checks(tr, 1)
    os.makedirs(OUT, exist_ok=True)
    for me in meshes:
        export_ue(me, os.path.join(OUT, me.name + ".fbx"), tspace=me is not tr)
    col = bpy.context.scene.collection
    for me in meshes:                                  # .blend armado PARADO, en la orientacion de la web
        ob = bpy.data.objects.new(me.name.replace("SM_ShareButton_", "").replace("_SC", ""), me)
        col.objects.link(ob)
        ob.matrix_world = R_WEB.copy()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "SM_ShareButton_SC.blend"))
    print("SHARE_OK", info, "recorrido_mm", TRAVEL, "hover_mm", HOVER)


if __name__ == "__main__":
    try:
        main()
    except BaseException as e:
        print("SHARE_FALLO", type(e).__name__, e)
        traceback.print_exc()
