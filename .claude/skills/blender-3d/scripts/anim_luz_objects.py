# anim_luz_objects.py - la aparicion "LUZ PRIMERO" (aprobada por Beltran sobre la paleta, 2026-09-30: "el primero me
# gusta... arma algo similar para el timbre, el boton de save y el sensor de breath") aplicada a los otros tres objetos
# de la familia. La misma coreografia para los tres (t de 0 a 1 = 1,5 s; la SALIDA es la misma al reves):
#   0,00-0,30  una semilla de luz dibuja el contorno de la ranura en el aire (TRAZO: malla aditiva SM_<X>_Trace_SC)
#   0,24-0,56  el cuerpo nace como una RENDIJA de luz de canto a la vista y se abre como un parpado, toma espesor
#              y la luz se enfria en hormigon (Flash 1 -> 0)
#   0,42-0,60  relevo: la ranura real se enciende y el trazo se apaga
#   0,52-0,80  la pieza movil ASOMA desde adentro con un "clac" (timbre: boton; SAVE: placa; sensor: el boton de la panza)
#   0,70-0,95  las luces propias (texto del SAVE, punta del sensor y ondas)
#   0,86-1,00  la ranura exhala una vez (brillo 1 -> 1,25 -> 1)
# Genera ademas el TRAZO de cada objeto como FBX (UV0.x = fraccion del contorno desde arriba en sentido antihorario
# visto desde la cara; UV0.y = 0..1 a lo ancho) para Unreal.
# Uso: blender --background --python anim_luz_objects.py -- <bell|save|sensor> <dir_cuadros> [cuadros "0,10,20"]
import math
import os
import sys
import traceback

import bmesh
import bpy
from mathutils import Matrix, Vector

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import anim_palette_base as P   # noqa: E402  (curvas + materiales de sombreado falso)
from revolve_lib import rrect_outline   # noqa: E402

CS = os.path.abspath(os.path.join(AQUI, "..", "..", "..", "..", "VR_Test", "Saved", "ClaudeScripts"))
LIGHT = (1.0, 0.72, 0.45)
SH = {"Ambient": 0.30, "Diffuse": 0.55, "Wrap": 0.4, "Fill": 0.25}     # el juego de luz de sus renders aprobados
S, seg, lerp = P.smooth, P.seg, P.lerp


def bump(x):
    return math.sin(math.pi * P.clamp01(x))


def circle(r_mm, n=360):
    return [(r_mm * math.cos(2 * math.pi * k / n), r_mm * math.sin(2 * math.pi * k / n)) for k in range(n)]


# ---------------------------------------------------------------- los tres objetos (medidas de sus generadores, mm)
_gi, _go = 95.0 - 0.138 * 190 - 0.069 * 190, 95.0 - 0.138 * 190      # sensor: cinta de luz (gen_bio_sensor dims())
OBJ = {
    "bell": {
        "dir": "Bell", "prefix": "SM_Bell",
        "meshes": {"Base": "SM_Bell_Base_SC", "Mover": "SM_Bell_Button_SC"},
        "path": circle((108.5 + 124.4) / 2), "z": 44.1, "hw": 14.0, "face": 1.0,
        "hide_move": -19.0,           # el boton arranca hundido en el bolsillo (tapado por el destello del bolsillo)
        "rest_glow": {"Ring": 0.7},
        "cam": ((0.18, -0.55, 1.0), (0, 0, 0.035), 0.95, 55),
    },
    "save": {
        "dir": "SaveMelody", "prefix": "SM_SaveMelody",
        "meshes": {"Base": "SM_SaveMelody_Base_SC", "Mover": "SM_SaveMelody_Plate_SC"},
        "path": [(p[0], p[1]) for p in rrect_outline(75.0, 30.0, 19.0, -7.5, n_arc=24, step=1.5)], "z": 15.0, "hw": 7.0, "face": 1.0,
        "hide_move": -12.0,           # la placa arranca debajo del fondo del canal (adentro del cuerpo cerrado)
        "rest_glow": {"Ring": 0.7},
        "cam": ((0.18, -0.55, 1.0), (0, 0, 0.010), 0.42, 55),
    },
    "sensor": {
        "dir": "BioSensor", "prefix": "SM_BioSensor",
        "meshes": {"Base": "SM_BioSensor_SC", "Mover": "SM_BioSensor_Button_SC", "Waves": "SM_BioSensorWaves_SC"},
        "path": circle((_gi + _go) / 2), "z": -0.032 * 190, "hw": 10.0, "face": -1.0,
        "hide_move": 17.0,            # el boton arranca adentro del cuerpo, detras de su tapa
        "rest_glow": {"Ring": 1.0, "BackRing": 0.9, "TipLight": 1.0},
        "cam": ((0.35, -0.60, -0.85), (0, 0, -0.02), 0.56, 55),
    },
}
# anillo de carga: su eje es X (la cara mira al forward del actor en Unreal). FACE lleva el marco "de cara" (x, y, z) al
# del objeto: (x, y, z)_cara -> (z, x, y)_objeto, es decir la normal de cara +Z pasa a +X y "arriba" (+Y de cara) a +Z.
FACE_X = Matrix(((0.0, 0.0, 1.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)))
STAGE = [(0.10, 0.35, 1.0), (1.0, 0.12, 0.12), (0.55, 0.15, 1.0), (1.0, 0.42, 0.06), (0.15, 1.0, 0.45)]   # RingColors
RING_REST_CHARGE = 2.5      # para la vista previa: Entering y Recognizing llenas, Loving a la mitad
OBJ["ring"] = {
    "dir": "", "prefix": "SM_ChargeRing",
    "meshes": {"Base": "SM_ChargeRing_SC"},
    "path": circle(0.74 * 230.0), "z": 0.0, "hw": 16.0, "face": 1.0, "frame": FACE_X,
    "rest_glow": {"Light": 1.0},
    "cam": ((1.0, -0.40, 0.28), (0, 0, 0), 1.45, 55),
    # Beltran: "este lo haria sin aro de luz, porque no tiene" -> sin trazo: la luz nace como la RENDIJA del propio
    # anillo (un punto que se estira en linea), se abre como parpado, se enfria y se llenan las cavidades
    "no_trace": True, "slit_flash": 1.6,
    "T": {"slit": (0.00, 0.20), "open": (0.12, 0.46), "thick": (0.18, 0.48), "cool": (0.14, 0.56),
          "groove_in": (0.34, 0.50), "fill": (0.40, 0.86), "fill_off": (0.76, 0.92), "exhale": (0.84, 1.00)},
}
COLS = {"Body": (0.62, 0.56, 0.48), "Face": (0.55, 0.50, 0.43), "Pocket": (0.06, 0.06, 0.065),
        "ButtonSide": (0.70, 0.64, 0.55), "ButtonTop": (0.74, 0.68, 0.58), "PlateSide": (0.70, 0.64, 0.55),
        "PlateTop": (0.56, 0.51, 0.45), "Button": (0.70, 0.64, 0.55), "Grip": (0.05, 0.05, 0.055)}
LIGHTS = ("Ring", "BackRing", "TipLight")


# ---------------------------------------------------------------- materiales
def light_mat(name, glow):
    m, nt, out = P._base(name)
    g = P._value(nt, "Glow", glow)
    col = P._vm(nt, 'SCALE', LIGHT, scale=g)
    em = P._n(nt, "ShaderNodeEmission")
    P._link(nt, col, em.inputs["Color"])
    P._link(nt, em.outputs[0], out.inputs["Surface"])
    return m


def ring_light_mat():
    """= M_ChargeRing_Light_SC con la carga global Charge (0..5) y Glow (encendido del vidrio tintado)."""
    m, nt, out = P._base("Light")
    _m = P._m
    uv = P._n(nt, "ShaderNodeUVMap", uv_map="UVMap")
    sep = P._n(nt, "ShaderNodeSeparateXYZ")
    P._link(nt, uv.outputs["UV"], sep.inputs[0])
    fl = _m(nt, 'FLOOR', sep.outputs["X"])
    t = _m(nt, 'SUBTRACT', sep.outputs["X"], fl)
    ramp = P._n(nt, "ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = 'CONSTANT'
    els = ramp.color_ramp.elements
    while len(els) < 5:
        els.new(0.5)
    for i, c in enumerate(STAGE):
        els[i].position = i * 0.2
        els[i].color = tuple(x + (1.0 - x) * 0.30 for x in c) + (1.0,)
    P._link(nt, _m(nt, 'MULTIPLY_ADD', fl, 0.2, 0.1), ramp.inputs["Fac"])
    ch = P._value(nt, "Charge", RING_REST_CHARGE)
    d = _m(nt, 'SUBTRACT', _m(nt, 'SUBTRACT', ch, fl), t)
    lit = _m(nt, 'DIVIDE', _m(nt, 'ADD', d, 0.012), 0.024, clamp=True)
    front = P._value(nt, "Front", 0.0)          # brillo del frente de carga durante la aparicion
    fb = _m(nt, 'MULTIPLY', _m(nt, 'EXPONENT', _m(nt, 'MULTIPLY', _m(nt, 'POWER', _m(nt, 'DIVIDE', d, 0.05), 2.0), -1.0)), front)
    lvl = _m(nt, 'ADD', _m(nt, 'ADD', 0.12, _m(nt, 'MULTIPLY', lit, 0.78)), fb)
    g = P._value(nt, "Glow", 1.0)
    col = P._vm(nt, 'SCALE', ramp.outputs["Color"], scale=_m(nt, 'MULTIPLY', lvl, g))
    em = P._n(nt, "ShaderNodeEmission")
    P._link(nt, col, em.inputs["Color"])
    P._link(nt, em.outputs[0], out.inputs["Surface"])
    return m


def trace_mat():
    """= M_AppearTrace_SC: cinta gaussiana a lo ancho (UV.y) + halo; encendida hasta Sweep con cabeza brillante."""
    m, nt, out = P._base("Trace")
    _m = P._m
    uv = P._n(nt, "ShaderNodeUVMap", uv_map="UVMap")
    sep = P._n(nt, "ShaderNodeSeparateXYZ")
    P._link(nt, uv.outputs["UV"], sep.inputs[0])
    u, v = sep.outputs["X"], sep.outputs["Y"]
    dv = _m(nt, 'SUBTRACT', v, 0.5)

    def gauss(x, w):
        q = _m(nt, 'DIVIDE', x, w)
        return _m(nt, 'EXPONENT', _m(nt, 'MULTIPLY', _m(nt, 'MULTIPLY', q, q), -1.0))

    halo = P._value(nt, "Halo", 0.30)
    prof = _m(nt, 'ADD', gauss(dv, 0.09), _m(nt, 'MULTIPLY', gauss(dv, 0.28), halo))
    sw, soft = P._value(nt, "Sweep", 0.0), P._value(nt, "Soft", 0.05)
    head, glow = P._value(nt, "Head", 0.0), P._value(nt, "Glow", 1.0)
    front = _m(nt, 'MULTIPLY', sw, _m(nt, 'ADD', soft, 1.0))
    lit = _m(nt, 'DIVIDE', _m(nt, 'SUBTRACT', front, u), _m(nt, 'MAXIMUM', soft, 1e-4), clamp=True)
    hc = _m(nt, 'SUBTRACT', front, _m(nt, 'MULTIPLY', soft, 0.5))
    dd = _m(nt, 'SUBTRACT', _m(nt, 'FLOORED_MODULO', _m(nt, 'ADD', _m(nt, 'SUBTRACT', u, hc), 0.5), 1.0), 0.5)
    k = _m(nt, 'ADD', _m(nt, 'MULTIPLY', lit, glow), _m(nt, 'MULTIPLY', gauss(dd, 0.028), head))
    col = P._vm(nt, 'SCALE', LIGHT, scale=_m(nt, 'MULTIPLY', k, prof))
    em = P._n(nt, "ShaderNodeEmission")
    P._link(nt, col, em.inputs["Color"])
    tr = P._n(nt, "ShaderNodeBsdfTransparent")
    add = P._n(nt, "ShaderNodeAddShader")
    P._link(nt, em.outputs[0], add.inputs[0])
    P._link(nt, tr.outputs[0], add.inputs[1])
    P._link(nt, add.outputs[0], out.inputs["Surface"])
    return m


def waves_mat():
    """= M_BioSensorWaves_SC (HLSL v3) con Active (0 = apagadas) y Phase (el tiempo)."""
    m, nt, out = P._base("Waves")
    _m = P._m
    uv = P._n(nt, "ShaderNodeUVMap", uv_map="UVMap")
    sep = P._n(nt, "ShaderNodeSeparateXYZ")
    P._link(nt, uv.outputs["UV"], sep.inputs[0])
    v = sep.outputs["Y"]
    ph0 = P._value(nt, "Phase", 0.0)
    act = P._value(nt, "Active", 1.0)
    uu = _m(nt, 'POWER', v, 2.0)
    ph = _m(nt, 'FRACT', _m(nt, 'SUBTRACT', _m(nt, 'MULTIPLY', uu, 5.0), ph0))
    dudv = _m(nt, 'MAXIMUM', _m(nt, 'MULTIPLY', _m(nt, 'MAXIMUM', v, 0.001), 2.0), 0.1)
    d = _m(nt, 'DIVIDE', _m(nt, 'SUBTRACT', ph, 0.5), _m(nt, 'MULTIPLY', dudv, 0.055))
    band = _m(nt, 'EXPONENT', _m(nt, 'MULTIPLY', _m(nt, 'MULTIPLY', d, d), -1.0))
    fin = P._n(nt, "ShaderNodeMapRange", interpolation_type='SMOOTHSTEP')
    fin.inputs["From Min"].default_value, fin.inputs["From Max"].default_value = 0.0, 0.35
    P._link(nt, v, fin.inputs["Value"])
    fout = P._n(nt, "ShaderNodeMapRange", interpolation_type='SMOOTHSTEP')
    fout.inputs["From Min"].default_value, fout.inputs["From Max"].default_value = 0.45, 1.0
    fout.inputs["To Min"].default_value, fout.inputs["To Max"].default_value = 1.0, 0.0
    P._link(nt, v, fout.inputs["Value"])
    a = _m(nt, 'MULTIPLY', _m(nt, 'MULTIPLY', band, _m(nt, 'MULTIPLY', fin.outputs["Result"], fout.outputs["Result"])), act)
    col = P._vm(nt, 'SCALE', LIGHT, scale=a)
    em = P._n(nt, "ShaderNodeEmission")
    P._link(nt, col, em.inputs["Color"])
    tr = P._n(nt, "ShaderNodeBsdfTransparent")
    add = P._n(nt, "ShaderNodeAddShader")
    P._link(nt, em.outputs[0], add.inputs[0])
    P._link(nt, tr.outputs[0], add.inputs[1])
    P._link(nt, add.outputs[0], out.inputs["Surface"])
    return m


# ---------------------------------------------------------------- trazo (malla + FBX)
def trace_mesh(cfg, name):
    """Cinta plana a lo largo del contorno de la ranura, a la altura de su boca. Arranca ARRIBA (+Y) y gira antihorario
    visto desde la cara (face = +1: desde +Z; -1: desde -Z)."""
    pts = [Vector((x, y)) for x, y in cfg["path"]]
    area = sum(a.x * b.y - b.x * a.y for a, b in zip(pts, pts[1:] + pts[:1]))
    if (area > 0) != (cfg["face"] > 0):
        pts.reverse()
    k0 = max(range(len(pts)), key=lambda i: pts[i].y - 0.001 * abs(pts[i].x))
    pts = pts[k0:] + pts[:k0]
    L = [0.0]
    for a, b in zip(pts, pts[1:] + pts[:1]):
        L.append(L[-1] + (b - a).length)
    tot = L[-1]
    n = len(pts)
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    z = cfg["z"] / 1000.0
    rows = []
    for i in range(n + 1):                    # la costura se DUPLICA (u 0 y 1)
        p = pts[i % n]
        a, b = pts[(i - 1) % n], pts[(i + 1) % n]
        tng = (b - a).normalized()
        nrm = Vector((tng.y, -tng.x))
        c = p + Vector((0.0, 0.0))
        if (c + nrm).length < c.length:        # normal hacia afuera del contorno
            nrm = -nrm
        rows.append([bm.verts.new(((p.x + nrm.x * w) / 1000.0, (p.y + nrm.y * w) / 1000.0, z))
                     for w in (-cfg["hw"], 0.0, cfg["hw"])])
    for i in range(n):
        u0, u1 = L[i] / tot, L[i + 1] / tot
        for j in range(2):
            vs = (rows[i][j], rows[i + 1][j], rows[i + 1][j + 1], rows[i][j + 1])
            if cfg["face"] > 0:
                vs = vs[::-1]
            f = bm.faces.new(vs)
            uvs = {rows[i][j]: (u0, j / 2), rows[i + 1][j]: (u1, j / 2), rows[i + 1][j + 1]: (u1, (j + 1) / 2),
                   rows[i][j + 1]: (u0, (j + 1) / 2)}
            for lp in f.loops:
                lp[uvl].uv = uvs[lp.vert]
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if "frame" in cfg:
        me.transform(cfg["frame"].to_4x4())
    return me


def export_fbx(ob, path):
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, apply_unit_scale=True, global_scale=1.0,
                             apply_scale_options='FBX_SCALE_NONE', object_types={'MESH'}, mesh_smooth_type='FACE',
                             use_tspace=False, colors_type='NONE', add_leaf_bones=False, bake_anim=False, path_mode='STRIP')


# ---------------------------------------------------------------- escena
class Scene:
    pass


def setup(key):
    cfg = OBJ[key]
    d = os.path.join(CS, cfg["dir"])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = Scene()
    sc.cfg, sc.key, sc.obs, sc.mats = cfg, key, {}, {}
    for role, nm in cfg["meshes"].items():
        bpy.ops.import_scene.fbx(filepath=os.path.join(d, nm + ".fbx"))
        ob = [o for o in bpy.context.selected_objects if o.type == 'MESH'][0]
        sc.obs[role] = ob
    for role, ob in sc.obs.items():
        for s in ob.material_slots:
            part = s.name.split(".")[0].split("_")[-1]
            if part in sc.mats:
                s.material = sc.mats[part]
                continue
            if part in LIGHTS:
                m = light_mat(part, cfg["rest_glow"].get(part, 1.0))
            elif part == "Waves":
                m = waves_mat()
            elif part == "Light":
                m = ring_light_mat()
            elif part == "Frame":
                m = P.fake_mat(part, (0.075, 0.075, 0.085), self_glow=0.12, mottle=0.04, grain=0.04,
                               sh={"Ambient": 0.45, "Diffuse": 0.85, "Wrap": 0.4, "Fill": 0.55})
            elif part == "PlateTop":
                m = P.fake_mat(part, COLS[part], self_glow=0.10, mask=os.path.join(d, "T_SaveMelody_Text.png"),
                               mask_uv="TextUV", ink=(0.93, 0.91, 0.87), ink_glow=0.35, mottle=0.08, grain=0.06, sh=SH)
            else:
                m = P.fake_mat(part, COLS.get(part, COLS["Body"]), self_glow=0.10, mottle=0.08, grain=0.06, sh=SH)
            sc.mats[part] = m
            s.material = m
    me = trace_mesh(cfg, cfg["prefix"] + "_Trace_SC")
    tr = bpy.data.objects.new(me.name, me)
    bpy.context.scene.collection.objects.link(tr)
    if not cfg.get("no_trace"):
        export_fbx(tr, os.path.join(d, me.name + ".fbx"))
    sc.mats["Trace"] = trace_mat()
    me.materials.append(sc.mats["Trace"])
    sc.obs["Trace"] = tr
    sc.rest = {r: o.matrix_world.copy() for r, o in sc.obs.items()}
    sc.defaults = {(mn, n.name): n.outputs[0].default_value for mn, m in sc.mats.items() for n in m.node_tree.nodes if n.type == 'VALUE'}
    scn = bpy.context.scene
    w = bpy.data.worlds.new("Negro")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)
    scn.world = w
    scn.render.engine = 'CYCLES'
    scn.cycles.samples = 16
    scn.cycles.use_denoising = False
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
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    scn.collection.objects.link(cam)
    scn.camera = cam
    cam.data.clip_start = 0.005
    dv, c0, dist, lens = cfg["cam"]
    c0 = Vector(c0)
    cam.location = c0 + Vector(dv).normalized() * dist
    cam.rotation_euler = (c0 - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = lens
    bpy.context.view_layer.update()          # matrix_world de la camara al dia (si no, sale identidad)
    sc.cam = cam
    # parpado: giro que deja el plano de la ranura DE CANTO para el ojo (lo mismo calcula el BP en Unreal al empezar)
    z0 = cfg["z"] / 1000.0
    sc.F = cfg.get("frame", Matrix.Identity(3)).to_4x4()
    # En el marco de cara (normal n = +Z, pivote en el plano de la ranura): la rendija es HORIZONTAL en la vista
    # (eje X' = el "derecha" de la camara proyectado en el plano) y el giro alrededor de X' deja el plano de canto
    # para el ojo (contiene al vector pivote -> ojo). Lo mismo hace el BP en Unreal con la camara del jugador.
    Fi = sc.F.inverted()
    n = Vector((0, 0, 1))
    pv = Vector((0, 0, z0))
    e = (Fi @ cam.location) - pv
    right = Fi.to_3x3() @ (cam.matrix_world.to_3x3() @ Vector((1, 0, 0)))
    ax = (right - right.dot(n) * n).normalized()
    n2 = ax.cross(e).normalized()
    if n2.dot(n) < 0:
        n2 = -n2
    sc.axis = ax
    sc.th = math.atan2(n.cross(n2).dot(ax), n.dot(n2))
    sc.B = Matrix((ax, n.cross(ax), n)).transposed().to_4x4()      # columnas: X', Y', n
    sc.z0 = z0
    sc.psi = math.atan2(ax.y, ax.x)
    return sc


def reset(sc):
    for r, o in sc.obs.items():
        o.matrix_world = sc.rest[r]
        o.hide_render = False
    for (mn, nn), v in sc.defaults.items():
        sc.mats[mn].node_tree.nodes[nn].outputs[0].default_value = v


def setv(sc, mat, **vals):
    if mat not in sc.mats:
        return
    for k, v in vals.items():
        sc.mats[mat].node_tree.nodes[k].outputs[0].default_value = v


# ---------------------------------------------------------------- la coreografia (los MISMOS numeros van al BP de Unreal)
TIMES = {"seed": (0.00, 0.05), "enso": (0.02, 0.30), "head_off": (0.28, 0.38), "flare": (0.26, 0.42),
     "slit": (0.24, 0.34), "open": (0.30, 0.54), "thick": (0.36, 0.56), "cool": (0.30, 0.60),
     "groove_in": (0.42, 0.56), "trace_out": (0.46, 0.60), "rise": (0.52, 0.80), "rise_flash": (0.60, 0.86),
     "cover": (0.48, 0.62), "tip": (0.70, 0.86), "ink": (0.74, 0.95), "waves": (0.80, 1.00), "exhale": (0.86, 1.00),
     "fill": (0.52, 0.90), "fill_off": (0.80, 0.94)}


def pose(sc, t):
    cfg = sc.cfg
    T = dict(TIMES, **cfg.get("T", {}))
    # 1. el trazo de luz
    sweep = P.ease_in_out_cubic(seg(t, *T["enso"]))
    head = 3.2 * S(seg(t, *T["seed"])) * (1 - S(seg(t, *T["head_off"])))
    flare = 0.5 * bump(seg(t, *T["flare"]))
    tglow = (1 + flare) * (1 - S(seg(t, *T["trace_out"])))
    setv(sc, "Trace", Sweep=sweep, Head=head, Glow=tglow)
    sc.obs["Trace"].hide_render = cfg.get("no_trace", False) or tglow < 1e-4 and head < 1e-4 or (sweep < 1e-4 and head < 1e-4)
    # 2. el cuerpo: rendija de canto -> parpado
    base = sc.obs["Base"]
    if t < T["slit"][0]:
        base.hide_render = True
    else:
        sx = max(P.ease_out_cubic(seg(t, *T["slit"])), 1e-3)
        o = P.ease_in_out_cubic(seg(t, *T["open"]))
        sz = lerp(0.05, 1.0, P.ease_in_out_cubic(seg(t, *T["thick"])))
        pv = Vector((0, 0, sc.z0))
        R = Matrix.Rotation(sc.th * (1 - o), 4, sc.axis)
        Sm = sc.B @ Matrix.Diagonal((sx, sx, sz, 1.0)) @ sc.B.inverted()      # nace de un punto (de canto: una linea que se alarga) y toma espesor
        M = Matrix.Translation(pv) @ R @ Sm @ Matrix.Translation(-pv)
        base.matrix_world = sc.F @ M @ sc.F.inverted() @ sc.rest["Base"]
        cool = 1 - S(seg(t, *T["cool"]))
        for part in ("Body", "Face", "Pocket", "Grip", "Frame"):
            setv(sc, part, Flash=cfg.get("slit_flash", 1.0) * cool)
    # 3. relevo de luces: la ranura real se enciende, con una exhalacion al final
    g_in = S(seg(t, *T["groove_in"]))
    ex = 1 + 0.25 * bump(seg(t, *T["exhale"])) ** 2
    for part in ("Ring", "BackRing"):
        if part in sc.mats:
            setv(sc, part, Glow=cfg["rest_glow"][part] * g_in * ex)
    if sc.key == "bell":           # el bolsillo se llena de luz y tapa el nacimiento del boton
        setv(sc, "Pocket", Flash=0.8 * bump(seg(t, *T["cover"])))
    # 4. la pieza movil asoma desde adentro con un clac
    if sc.key == "ring":           # sin pieza movil: el vidrio se enciende y las cavidades se llenan en orden
        setv(sc, "Light", Glow=g_in * ex)
        f = P.ease_in_out_cubic(seg(t, *T["fill"]))
        setv(sc, "Light", Charge=min(RING_REST_CHARGE, 5.0 * f),
             Front=1.2 * S(seg(t, T["fill"][0], T["fill"][0] + 0.06)) * (1 - S(seg(t, *T["fill_off"]))))
        return
    mv = sc.obs["Mover"]
    u = seg(t, *T["rise"])
    if u <= 0.0:
        mv.hide_render = True
    else:
        k = P.ease_out_back(u, 1.2)
        mv.matrix_world = Matrix.Translation((0, 0, cfg["hide_move"] / 1000.0 * (1 - k))) @ sc.rest["Mover"]
        fl = 0.35 * (1 - S(seg(t, *T["rise_flash"])))
        for part in ("ButtonSide", "ButtonTop", "PlateSide", "PlateTop", "Button"):
            setv(sc, part, Flash=fl)
    # 5. luces propias
    if sc.key == "save":
        setv(sc, "PlateTop", InkGlow=0.35 * S(seg(t, *T["ink"])) + 0.9 * bump(seg(t, *T["ink"])))
    if sc.key == "sensor":
        tp = seg(t, *T["tip"])
        setv(sc, "TipLight", Glow=cfg["rest_glow"]["TipLight"] * S(tp) + 1.6 * bump(tp))
        setv(sc, "Waves", Active=S(seg(t, *T["waves"])), Phase=t * 0.9)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    key, out = argv[0], argv[1]
    only = [int(x) for x in argv[2].split(",")] if len(argv) > 2 else None
    sc = setup(key)
    os.makedirs(out, exist_ok=True)
    scn = bpy.context.scene
    scn.render.resolution_x, scn.render.resolution_y = 720, 540
    reset(sc)
    if "Waves" in sc.mats:
        setv(sc, "Waves", Phase=0.9)
    setv(sc, "Trace", Glow=0.0, Head=0.0, Sweep=0.0)
    sc.obs["Trace"].hide_render = True
    scn.render.filepath = os.path.join(out, "rest.png")
    bpy.ops.render.render(write_still=True)
    N = 46
    for f in range(N):
        if only is not None and f not in only:
            continue
        reset(sc)
        pose(sc, f / (N - 1))
        scn.render.filepath = os.path.join(out, "f_%03d.png" % f)
        bpy.ops.render.render(write_still=True)
    print("LUZ_OK", key, out, "eje %.1f th %.1f" % (math.degrees(sc.psi), math.degrees(sc.th)))


if __name__ == "__main__":
    try:
        main()
    except BaseException as e:
        print("LUZ_FALLO", type(e).__name__, e)
        traceback.print_exc()
