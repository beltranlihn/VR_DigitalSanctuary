# anim_palette_luz.py - coreografia "LUZ PRIMERO" (Turrell) para la aparicion de la paleta de dibujo.
# Primero nace la LUZ, despues la materia. Salida = la misma curva al reves (t de 1 a 0).
#
# Uso: blender --background --python anim_palette_luz.py -- <dir_salida> [cuadros separados por coma]
#
# LINEA DE TIEMPO (t en [0,1] = 1,5 s; 46 cuadros a 30 fps; "u" = tiempo local del tramo)
#  pieza            tramo t        que hace                                                  curva
#  LightRing (+)    0.00-0.05      semilla: un punto de luz arriba (90 grados)               Head 0->3.2 smooth
#   (malla aditiva) 0.02-0.32      ENSO: la cabeza dibuja el circulo en sentido antihorario  Sweep 0->1 ease_in_out
#                   0.28-0.42      cierre: la cabeza se apaga, destello suave del circulo    Glow 1->1.5->1
#                   0.50-0.68      relevo: el anillo se apaga y se enciende la ranura real   Glow 1->0 / Groove 0->1
#                   0.50-0.70      2a cabeza (H2): baja por la izquierda de 90 a 227 grados  H2Pos 0->0.381, H2 0->2.6->0
#  Base (disco)     0.25-0.36      nace como RENDIJA de luz de canto (plano que pasa por el  escala X 0->1 ease_out_cubic
#                                  ojo), crece desde el centro
#                   0.33-0.58      la rendija se abre como un parpado: gira sobre X (pivote  giro X -th->0 ease_in_out_cubic
#                                  en el centro, plano de la ranura) y toma espesor          espesor 0.05->1 ease_out_cubic
#                   0.33-0.62      la luz se enfria en hormigon                              Flash 1.1->0 smooth
#  Swatch           0.52-0.72      el pozo central se LLENA: sube desde el piso del pozo     mover z -h->0 ease_out_cubic
#                                  (nace adentro de la base) como luz y vira al ocre         Flash 1.6->0, SelfGlow 0.6->0.3
#  Cunas (8)        0.50+i*0.02    PETALOS: brotan en la bisagra interior, paradas a 64-70   escala 0->1 (bisagra) ease_out
#                   dur 0.26       grados, y se abren hasta caer planas en su bolsillo;      giro Y -70->0 ease_in_out
#                                  orden antihorario desde Brush0 (sigue a la luz)           Flash 1.1->0
#  Color1/Brush1    0.84-0.97      la elegida sube a su altura de seleccion (el "clac")      mover z -0.9 cm->0 ease_out_back
#  Undo / Redo      cuando pasa H2 alas: nacen bajo el disco, salen por debajo del borde y   mover (-2.2 cm rad, -3 cm z)->0
#                   dur 0.26       se despliegan hacia arriba (bisagra interior)             giro Y +90->0 ease_in_out
#  Slider           0.66-0.92      barrido de vidrio de izquierda a derecha                  Sweep 0->1, Head 2.2->0
#  Knob             0.66-0.84      viaja en la cabeza del barrido de 227 a 270 grados y se   angulo ease_out_back, escala
#                                  suelta ahi; nace chico dentro de la cabeza                0.1->1 en el primer 30 %
#  Groove           0.86-1.00      exhalacion final de la ranura                             Glow 1->1.25->1
import math
import os
import sys
import traceback

sys.path.insert(0, r"C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/.claude/skills/blender-3d/scripts")
import anim_palette_base as P  # noqa: E402
import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Quaternion, Vector  # noqa: E402

G = P.g
Z_RING = G.u(G.Z_GROOVE) + 0.0004            # piso de la ranura (+0,4 mm)
R_RING = G.u((G.GROOVE_IN + G.GROOVE_OUT) / 2)
R_SLIDER = G.u(G.SLIDER_R)
Z_FLOAT = G.u(G.Z_FLOAT)
PETAL_ORDER = ["Brush0", "Brush1", "Brush2", "Brush3", "Color3", "Color2", "Color1", "Color0"]   # antihorario desde 120
SELECTED = ("Color1", "Brush1")
FR_UNDO = (166.0 - 90.0) / 360.0
FR_REDO = (194.0 - 90.0) / 360.0
FR_SLIDER = (227.0 - 90.0) / 360.0

S = P.smooth
seg = P.seg
lerp = P.lerp


# ---------------------------------------------------------------- malla aditiva: el anillo de luz
def ring_mat():
    m, nt, out = P._base("LightRing")
    _m, _n = P._m, P._n
    tc = _n(nt, "ShaderNodeTexCoord")
    sep = _n(nt, "ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    x, y = sep.outputs["X"], sep.outputs["Y"]
    r = _m(nt, 'SQRT', _m(nt, 'ADD', _m(nt, 'MULTIPLY', x, x), _m(nt, 'MULTIPLY', y, y)))
    dr = _m(nt, 'SUBTRACT', r, R_RING)

    def gauss(v, w):
        q = _m(nt, 'DIVIDE', v, w)
        return _m(nt, 'EXPONENT', _m(nt, 'MULTIPLY', _m(nt, 'MULTIPLY', q, q), -1.0))

    halo = P._value(nt, "Halo", 0.30)
    prof = _m(nt, 'ADD', gauss(dr, 0.0055), _m(nt, 'MULTIPLY', gauss(dr, 0.016), halo))
    fr = P._angle_frac(nt, 90.0, 360.0, 1.0)                  # antihorario visto desde arriba, desde el fondo (90)
    sw = P._value(nt, "Sweep", 0.0)
    soft = P._value(nt, "Soft", 0.05)
    head = P._value(nt, "Head", 0.0)
    glow = P._value(nt, "Glow", 1.0)
    h2p = P._value(nt, "H2Pos", 0.0)
    h2 = P._value(nt, "H2", 0.0)
    hw = P._value(nt, "HW", 0.028)
    front = _m(nt, 'MULTIPLY', sw, _m(nt, 'ADD', soft, 1.0))
    lit = _m(nt, 'DIVIDE', _m(nt, 'SUBTRACT', front, fr), _m(nt, 'MAXIMUM', soft, 1e-4), clamp=True)
    hc = _m(nt, 'SUBTRACT', front, _m(nt, 'MULTIPLY', soft, 0.5))

    def bell(center, amp):
        dd = _m(nt, 'SUBTRACT', _m(nt, 'FLOORED_MODULO', _m(nt, 'ADD', _m(nt, 'SUBTRACT', fr, center), 0.5), 1.0), 0.5)
        return _m(nt, 'MULTIPLY', gauss(dd, hw), amp)

    k = _m(nt, 'ADD', _m(nt, 'ADD', _m(nt, 'MULTIPLY', lit, glow), bell(hc, head)), bell(h2p, h2))
    col = P._vm(nt, 'SCALE', tuple(P.LIGHT), scale=_m(nt, 'MULTIPLY', k, prof))
    em = _n(nt, "ShaderNodeEmission")
    nt.links.new(col, em.inputs["Color"])
    tr = _n(nt, "ShaderNodeBsdfTransparent")
    add = _n(nt, "ShaderNodeAddShader")
    nt.links.new(em.outputs[0], add.inputs[0])
    nt.links.new(tr.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], out.inputs["Surface"])
    return m


def build_ring(api):
    bm = bmesh.new()
    NA = 360
    radii = [R_RING + d for d in (-0.030, -0.018, -0.010, -0.005, -0.002, 0.0, 0.002, 0.005, 0.010, 0.018, 0.030)]
    rings = [[bm.verts.new((r * math.cos(2 * math.pi * k / NA), r * math.sin(2 * math.pi * k / NA), Z_RING))
              for k in range(NA)] for r in radii]
    for a, b in zip(rings[:-1], rings[1:]):
        for k in range(NA):
            bm.faces.new((a[k], a[(k + 1) % NA], b[(k + 1) % NA], b[k]))
    me = bpy.data.meshes.new("LightRing")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("LightRing", me)
    bpy.context.scene.collection.objects.link(ob)
    mat = ring_mat()
    me.materials.append(mat)
    api.mats["LightRing"] = mat
    api.add_object("LightRing", ob)
    return ob


def ring(api, **vals):
    base = {"Sweep": 0.0, "Soft": 0.05, "Head": 0.0, "Glow": 1.0, "H2Pos": 0.0, "H2": 0.0, "Halo": 0.30}
    base.update(vals)
    api.mat("LightRing", **base)
    on = (base["Glow"] > 1e-4 and base["Sweep"] > 1e-4) or base["Head"] > 1e-4 or base["H2"] > 1e-4
    api.extra["LightRing"].hide_render = not on

# ---------------------------------------------------------------- coreografia
# Tiempos (t en [0,1]); se leen desde aca para que la tabla de Unreal salga de los mismos numeros.
T = {
    "seed": (0.00, 0.05), "enso": (0.02, 0.30), "flare": (0.26, 0.42),
    "slit": (0.24, 0.34), "open": (0.30, 0.54), "thick": (0.36, 0.56), "cool": (0.30, 0.60),
    "groove_in": (0.42, 0.56), "ring_out": (0.46, 0.60), "h2": (0.52, 0.70), "h2_amp": (0.52, 0.56, 0.64, 0.72),
    "swatch": (0.50, 0.68), "swatch_col": (0.56, 0.78),
    "petal0": 0.52, "petal_step": 0.018, "petal_dur": 0.24,
    "wing_dur": 0.24, "slider": (0.68, 0.92), "select": (0.84, 0.96), "exhale": (0.86, 1.00),
}
PETAL_PAIRS = [("Color0", "Brush0"), ("Color1", "Brush1"), ("Color2", "Brush2"), ("Color3", "Brush3")]  # de atras hacia el frente
STAND = 55.0          # grados: los petalos brotan parados a 55 (mas de ~65 y los vecinos se cruzan: cunas en cuna)
SLIDER_SOFT = 0.06    # Soft por defecto del material del slider


def edge_on(api):
    """(giro X, giro Z) que deja el plano de la ranura DE CANTO para la camara: primero se tuerce psi para que el eje de
    la rendija quede horizontal en la vista, despues se inclina th sobre ese eje hasta que el plano contiene al ojo."""
    c = api.cam.location
    psi = math.atan2(c.x, -c.y)
    th = -math.atan2(c.z - Z_RING, math.hypot(c.x, c.y))
    return th, psi


def arc_pos(deg, r=R_SLIDER, z=Z_FLOAT):
    a = math.radians(deg)
    return Vector((r * math.cos(a), r * math.sin(a), z))


def bump(x):
    """0 -> 1 -> 0 suave (seno), para destellos que empiezan y terminan en cero."""
    return math.sin(math.pi * P.clamp01(x))


def slider_sweep(t):
    return P.ease_in_out_cubic(seg(t, *T["slider"]))


def knob_frac(t):
    """El disco va en la cabeza del barrido del slider y se suelta al llegar a la mitad (270 grados): acercamiento
    exponencial C1 (sin rebote) y cierre exacto en 0,5."""
    f = slider_sweep(t) * (1 + SLIDER_SOFT) - SLIDER_SOFT * 0.5
    kf = f if f < 0.4 else 0.5 - 0.1 * math.exp(-(f - 0.4) / 0.1)
    return lerp(kf, 0.5, S(seg(t, 0.90, 0.97)))


def pose(api, t):
    th, psi = api.EDGE
    # ---- 1. la luz: semilla + enso + cierre + relevo + segunda cabeza
    seed = S(seg(t, *T["seed"]))
    sweep = P.ease_in_out_cubic(seg(t, *T["enso"]))
    head = 3.2 * seed * (1 - S(seg(t, 0.28, 0.38)))
    flare = 0.5 * bump(seg(t, *T["flare"]))
    ring_out = S(seg(t, *T["ring_out"]))
    groove_in = S(seg(t, *T["groove_in"]))
    exhale = 0.25 * bump(seg(t, *T["exhale"])) ** 2
    h2pos = FR_SLIDER * P.ease_in_out_cubic(seg(t, *T["h2"]))
    a0, a1, a2, a3 = T["h2_amp"]
    h2 = 2.6 * S(seg(t, a0, a1)) * (1 - S(seg(t, a2, a3)))
    ring(api, Sweep=sweep, Head=head, Glow=(1 + flare) * (1 - ring_out), H2Pos=h2pos, H2=h2)
    api.groove(Glow=groove_in + exhale)
    # ---- 2. la base: rendija de luz de canto -> se abre como un parpado y se atornilla en su lugar
    if t < T["slit"][0]:
        api.hide("Base")
    else:
        sx = max(P.ease_out_cubic(seg(t, *T["slit"])), 1e-3)
        o = P.ease_in_out_cubic(seg(t, *T["open"]))
        sz = lerp(0.05, 1.0, P.ease_in_out_cubic(seg(t, *T["thick"])))
        api.pose("Base", rot_part=(th * (1 - o), 0, psi * (1 - o)), pivot=(0, 0, Z_RING), scale=(sx, 1.0, sz))
        api.mat("Base", Flash=1.0 * (1 - S(seg(t, *T["cool"]))))
    # ---- 3. casquete: el pozo central se llena de luz que vira al ocre
    if t < T["swatch"][0]:
        api.hide("Swatch")
    else:
        f = P.ease_out_cubic(seg(t, *T["swatch"]))
        api.pose("Swatch", move=(0, 0, -api.SW_SINK * (1 - f)))
        c = S(seg(t, *T["swatch_col"]))
        api.mat("Swatch", Flash=1.2 * (1 - c), SelfGlow=lerp(0.5, 0.3, c))
    # ---- 4. petalos: brotan de a pares simetricos, de atras hacia el frente, y se abren a sus bolsillos
    for k, pair in enumerate(PETAL_PAIRS):
        t0 = T["petal0"] + T["petal_step"] * k
        for nm in pair:
            p = api.parts[nm]
            u = seg(t, t0, t0 + T["petal_dur"])
            if u <= 0.0:
                api.hide(nm)
                continue
            s = P.ease_out_cubic(seg(u, 0.0, 0.45))
            beta = math.radians(STAND) * (1 - P.ease_in_out_cubic(seg(u, 0.20, 1.0)))
            lift = P.ease_out_back(seg(t, *T["select"]), 1.2) if nm in SELECTED else 1.0
            api.pose(nm, rot_part=(0, -beta, 0), pivot=p.hinge_in, scale=max(s, 1e-3),
                     move=(0, 0, -P.KEY_LIFT * (1 - lift)))
            vals = {"Flash": 0.6 * (1 - S(seg(u, 0.15, 0.85)))}
            if nm in SELECTED:
                vals["SelfGlow"] = 0.28 * S(seg(t, *T["select"]))
            if nm.startswith("Brush"):
                vals["InkGlow"] = 0.35 * S(seg(u, 0.7, 1.0)) + 0.45 * bump(seg(u, 0.7, 1.0))
            api.mat(nm, **vals)
    # ---- 5. undo / redo: cuando pasa la segunda cabeza salen de debajo del borde (cajon) y suben a su lugar (clac)
    for nm in ("Undo", "Redo"):
        p = api.parts[nm]
        t0 = api.T_PASS[nm] - 0.02
        u = seg(t, t0, t0 + T["wing_dur"])
        if u <= 0.0:
            api.hide(nm)
            continue
        out = P.ease_in_out_cubic(seg(u, 0.0, 0.45))
        up = P.ease_out_back(seg(u, 0.35, 1.0), 0.9)
        phi = math.radians(20.0) * (1 - P.ease_in_out_cubic(seg(u, 0.35, 1.0)))
        mv = p.radial * (-0.024 * (1 - out)) + Vector((0, 0, -0.030 * (1 - up)))
        api.pose(nm, rot_part=(0, phi, 0), pivot=p.hinge_in, move=mv)
        api.mat(nm, Flash=0.6 * (1 - S(seg(u, 0.3, 0.9))),
                InkGlow=0.35 * S(seg(u, 0.75, 1.0)) + 0.45 * bump(seg(u, 0.75, 1.0)))
    # ---- 6. slider (barrido de vidrio izq -> der) y su disco, que viaja en la cabeza y se suelta en 270
    ss = seg(t, *T["slider"])
    api.slider(Sweep=slider_sweep(t), Head=2.4 * S(seg(ss, 0.0, 0.08)) * (1 - S(seg(ss, 0.75, 1.0))))
    kf = knob_frac(t)
    if ss <= 0.0 or kf <= 0.0:
        api.hide("Knob")
    else:
        a = G.SLIDER_A0 + (G.SLIDER_A1 - G.SLIDER_A0) * kf
        sc = lerp(0.1, 1.0, P.ease_out_cubic(seg(kf, 0.0, 0.25)))
        api.pose("Knob", move=arc_pos(a) - arc_pos(270.0), scale=sc)
        api.mat("Knob", Flash=1.0 * (1 - S(seg(kf, 0.1, 0.5))) + 0.4 * bump(seg(t, 0.84, 0.94)))


def setup_extra(api):
    build_ring(api)
    api.EDGE = edge_on(api)
    sw = api.parts["Swatch"]
    api.SW_SINK = sw.top - G.u(G.Z_CAP_POCKET) + 0.0003
    # cuando pasa la 2a cabeza por cada ala (invirtiendo la curva de H2Pos)
    api.T_PASS = {}
    for nm, frp in (("Undo", FR_UNDO), ("Redo", FR_REDO)):
        best = min(range(1001), key=lambda k: abs(FR_SLIDER * P.ease_in_out_cubic(seg(k / 1000, *T["h2"])) - frp))
        api.T_PASS[nm] = best / 1000
    print("INFO th=%.2f psi=%.2f sw_sink=%.4f pass=%s" % (math.degrees(api.EDGE[0]), math.degrees(api.EDGE[1]),
                                                          api.SW_SINK, api.T_PASS))


if __name__ == "__main__":
    try:
        out_dir = sys.argv[sys.argv.index("--") + 1]
        only = None
        if len(sys.argv) > sys.argv.index("--") + 2:
            only = [int(x) for x in sys.argv[sys.argv.index("--") + 2].split(",")]
        api = P.setup()
        setup_extra(api)
        # reset() no toca los objetos extra: se apaga el anillo y pose() lo re-escribe entero en cada cuadro
        orig_reset = api.reset

        def reset_all():
            orig_reset()
            ring(api, Glow=0.0)
        api.reset = reset_all
        api.render_anim(pose, out_dir, only=only)
    except BaseException as e:
        print("FALLO", type(e).__name__, e)
        traceback.print_exc()
