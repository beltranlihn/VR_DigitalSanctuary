# gen_save_melody.py - el boton SAVE MELODY del secuenciador (Beltran, 2026-09-30: "de esta misma onda" que el timbre;
# va en la mano; se apunta con el laser, se activa con hover y con el gatillo se carga; "mas rectangular con bordes
# curvos para tener el texto"; "como 15 cm de largo"). Propuesta aprobada: scratchpad/melody/propuesta_save_melody.png.
# Rectangulo redondeado 150 x 60 mm (esquinas r 19):
#   SM_SaveMelody_Base_SC   borde redondeado + CANAL alrededor de la placa cuyo fondo es la CINTA DE LUZ
#                           slots 0 Body  1 Ring (fondo y parte baja del canal: luz)
#   SM_SaveMelody_Plate_SC  la placa-boton con el texto, se HUNDE TRAVEL mm al apretar (el BP la mueve en -Z)
#                           slots 0 PlateSide  1 PlateTop (UV1 "TextUV" = planar sobre el tope: mascara del texto)
#   SM_SaveMelody_Slider_SC slider plano TRANSPARENTE abajo y afuera (como el timbre): solo se ve la carga
#                           UV0.x = fraccion del perimetro en sentido HORARIO desde arriba al centro, visto de frente
#   T_SaveMelody_Text.png   "SAVE MELODY" blanco sobre negro (mascara, como UNDO/REDO de la paleta):
#                           la genera gen_save_melody_text.py con el Python del sistema (Blender no trae PIL)
# Mismo origen para las tres: centro de la espalda, frente hacia +Z.
# Uso: blender --background --python gen_save_melody.py -- <dir_salida>
import math
import os
import sys
import traceback

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from revolve_lib import checks, export_fbx, fillet_poly, rrect_outline, sweep_rrect   # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else "."
A, B, RC = 75.0, 30.0, 19.0          # semiejes y radio de esquina del contorno exterior (mm)
H_RIM = 15.0                         # alto del borde
F_OUT_TOP, F_OUT_BOT = 3.5, 3.0      # redondeos del canto
RIM_W = 4.8                          # ancho del borde (hasta la pared del canal)
F_RIM_IN = 1.5
H_FLOOR = 6.0                        # fondo del canal (la luz)
H_LIGHT = 10.0                       # la luz sube por las paredes del canal hasta aca
PLATE_D = -10.2                      # la placa: contorno desplazado (canal de 5,4 mm entre borde y placa)
H_PLATE_TOP = 17.7                   # la placa asoma 2,7 mm sobre el borde
H_PLATE_BOT = 10.5
F_PLATE = 2.5
TRAVEL = 4.0                         # cuanto se hunde con el gatillo
S_IN, S_OUT, S_T, S_F = 5.0, 9.0, 3.0, 1.0   # slider: desplazado afuera de 5 a 9 mm, 3 mm de espesor, abajo
TEXT = "SAVE MELODY"
FONT = r"C:/Users/beltr/AppData/Local/Microsoft/Windows/Fonts/Avenir Book.ttf"


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
    # el tope plano (desde donde termina el redondeo) es PlateTop
    return [(d, h, "PlateTop" if (h >= H_PLATE_TOP - 1e-6) else p) for d, h, p in pts]


def slider_profile():
    mid = (S_IN + S_OUT) / 2
    P = [(mid, 0.0, 0.0, "Slider"), (S_OUT, 0.0, S_F, "Slider"), (S_OUT, S_T, S_F, "Slider"), (S_IN, S_T, S_F, "Slider"),
         (S_IN, 0.0, S_F, "Slider"), (mid, 0.0, 0.0, "Slider")]
    return fillet_poly(P)[:-1]


def slider_uv(me):
    """UV0.x = fraccion del perimetro (horario desde arriba al centro), por angulo de arco del contorno medio."""
    ring = rrect_outline(A, B, RC, (S_IN + S_OUT) / 2)
    L = [0.0]
    for p, q in zip(ring, ring[1:] + ring[:1]):
        L.append(L[-1] + math.hypot(q[0] - p[0], q[1] - p[1]))
    tot = L[-1]
    m = len(ring)
    uv = me.uv_layers["UVMap"]
    for p in me.polygons:
        vals = []
        for li in p.loop_indices:
            vi = me.loops[li].vertex_index
            vals.append(L[vi % m] / tot)
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


def text_texture(path):
    from PIL import Image, ImageDraw, ImageFont
    ap, bp = A + PLATE_D, B + PLATE_D
    W = 2048
    H = int(round(W * bp / ap))
    img = Image.new("L", (W, H), 0)
    dr = ImageDraw.Draw(img)
    cap_mm = 9.5
    size = int(cap_mm / (2 * bp) * H / 0.72)
    font = ImageFont.truetype(FONT, size)
    # un poco de espaciado entre letras (se lee mejor en el visor)
    track = int(size * 0.06)
    widths = [dr.textlength(c, font=font) for c in TEXT]
    total = sum(widths) + track * (len(TEXT) - 1)
    x = (W - total) / 2
    for c, w in zip(TEXT, widths):
        dr.text((x, H / 2), c, font=font, fill=255, anchor="lm")
        x += w + track
    # SIN voltear: Blender pone la fila de arriba del PNG en V=1 (TextUV crece hacia +Y = arriba del boton) y el FBX
    # invierte V al pasar a Unreal, donde V=0 es la fila de arriba: el mismo PNG se lee derecho en los dos
    img.save(path)
    return W, H


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    info, obs = {}, []
    specs = (("SM_SaveMelody_Base_SC", base_profile(), ("Body", "Ring"), False, ("first", "last"), ("Body", "Ring")),
             ("SM_SaveMelody_Plate_SC", plate_profile(), ("PlateSide", "PlateTop"), False, ("first", "last"), ("PlateSide", "PlateTop")),
             ("SM_SaveMelody_Slider_SC", slider_profile(), ("Slider",), True, (), ()))
    for name, prof, parts, closed, caps, cap_parts in specs:
        me, flips = sweep_rrect(name, prof, parts, A, B, RC, closed=closed, caps=caps, cap_parts=cap_parts)
        if name.endswith("Slider_SC"):
            slider_uv(me)
        if name.endswith("Plate_SC"):
            text_uv(me, parts)
        ob = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(ob)
        for p in parts:
            me.materials.append(bpy.data.materials.new("M_SaveMelody_" + p))
        info[name] = checks(me, len(parts))
        info[name]["dadas_vuelta"] = flips
        xs = [v.co for v in me.vertices]
        info[name]["caja_cm"] = [[round(min(c[k] for c in xs) * 100, 2) for k in range(3)], [round(max(c[k] for c in xs) * 100, 2) for k in range(3)]]
        obs.append(ob)
    os.makedirs(OUT, exist_ok=True)
    try:
        tw, th = text_texture(os.path.join(OUT, "T_SaveMelody_Text.png"))
    except ModuleNotFoundError:          # el Python de Blender no trae PIL: la textura la hace gen_save_melody_text.py
        tw, th = None, None
    for ob in obs:
        export_fbx(ob, os.path.join(OUT, ob.name + ".fbx"))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "SM_SaveMelody_SC.blend"))
    print("MELODY_OK", info, "texto", tw, th, "recorrido_mm", TRAVEL)


try:
    main()
except BaseException as e:
    print("MELODY_FALLO", type(e).__name__, e)
    traceback.print_exc()
