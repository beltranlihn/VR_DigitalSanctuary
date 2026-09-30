# gen_bell.py - EL TIMBRE del Soul Charger Center (pedido de Beltran, 2026-09-30; plano C:/Users/beltr/Desktop/ButtonBell.pdf).
# "Es de la misma onda" que el sensor (la obra pide que timbre y sensor RIMEN: docs/OBRA-SOUL-CHARGER.md, "El timbre es el
# tutorial"): una base con borde redondeado y un AR0 DE LUZ en hendidura, el plano a la altura del borde y un BOTON
# central con una hendidura suave hacia adentro, que SE MUEVE al apretarlo (su cuerpo entra en un bolsillo de la base,
# como la linea punteada del plano). + un SLIDER RADIAL PLANO alrededor que se carga de 0 a 100 mientras se aprieta.
# Medidas: las del PDF, leidas de sus vectores (unidades del plano tomadas como mm: timbre de 32 cm, boton de 16 cm,
# donde cabe la palma; cambiar SCALE si es otro tamano).
# Tres mallas con el MISMO origen (centro de la cara trasera de la base, frente hacia +Z):
#   SM_Bell_Base_SC   slots 0 Body (borde, canto, espalda)  1 Face (plano)  2 Ring (fondo de la hendidura: luz)  3 Pocket
#   SM_Bell_Button_SC slots 0 ButtonSide  1 ButtonTop (la hendidura suave)  -> el BP lo baja TRAVEL mm en -Z al apretar
#   SM_Bell_Slider_SC slot 0 Slider (anillo plano; UV0.x = fraccion angular HORARIA desde +Y visto de frente, UV0.y radial)
# Uso: blender --background --python gen_bell.py -- <dir_salida>
import math
import os
import sys
import traceback

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from revolve_lib import checks, export_fbx, fillet_poly, revolve   # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else "."
SCALE = 1.0          # mm por unidad del plano
X0, Y0 = 65.8, 425.0  # cara trasera y eje del corte en el PDF


def u(v):
    return v * SCALE


# ---- base (del corte del PDF) ----
R = u(159.3)
F_OUT = u(12.8)           # redondeo del canto (arriba y abajo)
H_TOP = u(109.9 - X0)     # 44,1: borde y plano a la misma altura
R_GO = u(Y0 - 300.6)      # 124,4: pared exterior de la hendidura
R_GI = u(Y0 - 316.5)      # 108,5: pared interior
H_GB = u(91.8 - X0)       # 26,0: fondo de la hendidura
F_G = u(7.7)              # redondeos de la boca de la hendidura
H_LIGHT = u(34.0)         # la luz: de aca para abajo en la hendidura
# ---- boton ----
R_B = u(92.0)             # Beltran 2026-09-30: "el boton mas ancho" (el PDF: 80,5)
H_BT = u(127.9 - X0)      # 62,1: canto de arriba del boton
F_BT = u(13.3)            # redondeo del canto de arriba
R_DISH = R_B - u(13.7)    # donde empieza la hendidura suave (el PDF: 66,8 con boton 80,5)
DISH_D = u(4.1) * R_B / u(80.5)   # hendidura suave, proporcional al ancho (4,1 en el PDF)
H_BB = H_GB               # el cuerpo del boton baja hasta el nivel del fondo de la hendidura (linea punteada)
TRAVEL = u(10.0)          # recorrido al apretar
CLEAR = u(1.0)            # luz radial entre boton y bolsillo
H_POCKET = H_BB - TRAVEL - u(2.0)
# ---- slider radial plano ----
S_IN, S_OUT, S_T, S_F = u(164.0), u(184.0), u(3.0), u(1.2)
S_LOW = True              # Beltran: "el slider va en el margen inferior": al ras de la ESPALDA (apoyado en la pared)
SEG = 96


def base_profile():
    rp = R_B + CLEAR
    P = [(0.0, H_POCKET, 0.0, "Pocket"), (rp, H_POCKET, u(1.5), "Pocket"), (rp, H_TOP, u(1.5), "Face"),
         (R_GI, H_TOP, F_G, "Face"), (R_GI, H_LIGHT, 0.0, "Ring"), (R_GI, H_GB, u(1.0), "Ring"),
         (R_GO, H_GB, u(1.0), "Ring"), (R_GO, H_LIGHT, 0.0, "Body"), (R_GO, H_TOP, F_G, "Body"),
         (R, H_TOP, F_OUT, "Body"), (R, 0.0, F_OUT, "Body"), (0.0, 0.0, 0.0, "Body")]
    pts = fillet_poly(P)
    return pts[::-1]          # del eje de la espalda hacia afuera, por el frente, hasta el eje del bolsillo


def button_profile():
    P = []
    n = 10
    for k in range(n):        # hendidura suave: parabola desde el centro hasta R_DISH
        r = R_DISH * k / n
        P.append((r, H_BT - DISH_D * (1 - (r / R_DISH) ** 2), 0.0, "ButtonTop"))
    P += [(R_DISH, H_BT, 0.0, "ButtonSide"), (R_B, H_BT, F_BT, "ButtonSide"), (R_B, H_BB, u(1.5), "ButtonSide"),
          (0.0, H_BB, 0.0, "ButtonSide")]
    # 2026-09-30 (Beltran en Unreal: "la cara del boton quedo abierta"): el perfil iba en sentido HORARIO (de arriba hacia
    # afuera y abajo) y la malla salia DADA VUELTA ENTERA (volumen negativo; el control de revolve no lo ve porque compara
    # contra normales del mismo perfil). Blender la mostraba bien (emision de las dos caras); Unreal descarta la cara de
    # atras. Se invierte como el de la base: del eje de abajo hacia afuera, por el canto, hasta el centro de la hendidura.
    pts = fillet_poly(P)[::-1]
    return [(r, h, pts[i + 1][2] if i + 1 < len(pts) else p) for i, (r, h, p) in enumerate(pts)]


def slider_profile():
    """Seccion del anillo plano: rectangulo con esquinas redondeadas, CERRADO (sin repetir el primer punto)."""
    z0, z1 = (0.0, S_T) if S_LOW else (H_TOP - S_T, H_TOP)
    mid = (S_IN + S_OUT) / 2
    P = [(mid, z0, 0.0, "Slider"), (S_OUT, z0, S_F, "Slider"), (S_OUT, z1, S_F, "Slider"), (S_IN, z1, S_F, "Slider"),
         (S_IN, z0, S_F, "Slider"), (mid, z0, 0.0, "Slider")]
    return fillet_poly(P)[:-1]


def slider_uv(me):
    """UV0.x = fraccion angular HORARIA desde +Y visto de frente (+Z): el material llena el anillo con Progress."""
    uv = me.uv_layers["UVMap"]
    for p in me.polygons:
        us = []
        for li in p.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            a = (math.atan2(co.x, co.y)) / (2 * math.pi)   # 0 arriba, crece hacia la derecha (horario visto de frente)
            us.append(a % 1.0)
        if max(us) - min(us) > 0.5:
            us = [x + 1.0 if x < 0.5 else x for x in us]
        for li, x in zip(p.loop_indices, us):
            co = me.vertices[me.loops[li].vertex_index].co
            rr = math.hypot(co.x, co.y) * 1000.0
            uv.data[li].uv = (x, (rr - S_IN) / (S_OUT - S_IN))


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    info, obs = {}, []
    for name, prof, parts in (("SM_Bell_Base_SC", base_profile(), ("Body", "Face", "Ring", "Pocket")),
                              ("SM_Bell_Button_SC", button_profile(), ("ButtonSide", "ButtonTop")),
                              ("SM_Bell_Slider_SC", slider_profile(), ("Slider",))):
        me, flips = revolve(name, prof, parts, SEG, closed=(name == "SM_Bell_Slider_SC"))
        if name == "SM_Bell_Slider_SC":
            slider_uv(me)
        ob = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(ob)
        for p in parts:
            me.materials.append(bpy.data.materials.new("M_Bell_" + p))
        info[name] = checks(me, len(parts))
        info[name]["dadas_vuelta"] = flips
        xs = [v.co for v in me.vertices]
        info[name]["caja_cm"] = [[round(min(c[k] for c in xs) * 100, 2) for k in range(3)], [round(max(c[k] for c in xs) * 100, 2) for k in range(3)]]
        obs.append(ob)
    os.makedirs(OUT, exist_ok=True)
    for ob in obs:
        export_fbx(ob, os.path.join(OUT, ob.name + ".fbx"))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "SM_Bell_SC.blend"))
    print("BELL_OK", info, "recorrido_mm", TRAVEL)


try:
    main()
except BaseException as e:
    print("BELL_FALLO", type(e).__name__, e)
    traceback.print_exc()
