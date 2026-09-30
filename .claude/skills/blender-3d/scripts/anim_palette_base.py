# anim_palette_base.py - base comun para PROBAR ANIMACIONES DE APARICION sobre la paleta de dibujo (pedido de Beltran,
# 2026-09-30: "en general estamos usando el super aburrido escala de 0 a 1... una animacion cul de aparicion, como los
# transformers... 1,5 segundos hasta tomar la forma; la misma animacion en reversa para la salida").
# Arma la paleta COMPLETA como en Unreal (BP_DrawPalette_SC v2: mate, color y pincel elegidos arriba, undo/redo al 80 %,
# disco del slider en el medio) con el SOMBREADO FALSO de M_DrawPalette_SC (unlit: hemisferio + luz principal con wrap +
# relleno desde la vista; sin luces de escena, fondo negro), y expone una API para posar cada pieza en el tiempo.
# Una coreografia = un script que importa esto y define pose(api, t) con t en [0, 1] (0 = no nacio, 1 = la paleta en
# reposo EXACTO). La salida es la misma curva al reves (t de 1 a 0).
#
# Uso desde una coreografia (blender --background --python anim_palette_<x>.py -- <dir_salida>):
#   import anim_palette_base as P
#   api = P.setup()
#   def pose(api, t): ...
#   api.render_anim(pose, out_dir)          # cuadros f_000.png... + rest.png (reposo, para comparar el ultimo cuadro)
# Despues, con el Python del sistema: python compose_anim.py <dir_salida>  (GIF ida + reversa y hoja de contacto)
#
# PIEZAS (api.parts[nombre]): Base, Swatch, Color0..3, Brush0..3, Undo, Redo, Slider, Knob.
#   Cada una: obj, kind (base/swatch/color/brush/side/slider/knob), angle_deg (angulo en la paleta, Blender: +X = colores,
#   undo a 166, slider abajo a 270), center (centro de su caja, en metros), radial / tangent (unitarios en XY),
#   hinge_in / hinge_out (puntos del canto interior / exterior sobre la cara de arriba: bisagras naturales), rest (Matrix).
#   Marco de la pieza ("part frame"): X = radial hacia afuera, Y = tangencial, Z = arriba (cara de la paleta).
# Ejes de la paleta: acostada en XY, cara a +Z, z = 0 en el canto de arriba del borde (casi todo queda entre 0 y -3 cm).
import importlib.util
import math
import os
import sys

import bpy
from mathutils import Matrix, Quaternion, Vector

AQUI = os.path.dirname(os.path.abspath(__file__))
if AQUI not in sys.path:
    sys.path.insert(0, AQUI)
_spec = importlib.util.spec_from_file_location("gdp", os.path.join(AQUI, "gen_draw_palette.py"))
g = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(g)

DIR = g.DESTINO
BLEND = os.path.join(DIR, "SM_DrawPalette_SC.blend")
LIGHT = (1.0, 0.72, 0.42)                       # la luz calida de la ranura (M_DrawPalette_Groove_SC)
COLORS = [(0.78, 0.40, 0.30), (0.82, 0.63, 0.32), (0.47, 0.60, 0.46), (0.40, 0.52, 0.70)]   # terracota, ocre, salvia, azul
KEY_GAIN = 0.7                                  # KeyColorGain de la v2
SEL_COLOR, SEL_BRUSH = 1, 1
KEY_LIFT = 0.009                                # KeyLift 0,9 cm
SIDE_SIZE = 0.8                                 # SideSize: undo/redo al 80 %, pegados al borde (pivote r 19,6 cm)
SH = {"Ambient": 0.14, "Diffuse": 0.38, "Wrap": 0.4, "Fill": 0.06}   # MI v2 (mate)
LDIR = Vector((-0.35, 0.30, 0.88)).normalized()
ICON_ROT, ICON_SCALE = -45.0, 1.3


# ---------------------------------------------------------------- tiempo y curvas (todas de [0,1] a [0,1] salvo back/spring)
def clamp01(x):
    return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x


def seg(t, a, b):
    """Tiempo local de un tramo: 0 antes de a, 1 despues de b."""
    return clamp01((t - a) / max(b - a, 1e-6))


def lerp(a, b, x):
    return a + (b - a) * x


def smooth(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)


def ease_out_cubic(x):
    x = clamp01(x)
    return 1 - (1 - x) ** 3


def ease_in_cubic(x):
    x = clamp01(x)
    return x ** 3


def ease_in_out_cubic(x):
    x = clamp01(x)
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def ease_out_quint(x):
    x = clamp01(x)
    return 1 - (1 - x) ** 5


def ease_out_back(x, s=1.4):
    """Pasa de largo (s = cuanto) y vuelve: el 'clac' de una pieza que encaja."""
    x = clamp01(x)
    return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2


def spring(x, zeta=0.45, cycles=1.6):
    """Resorte amortiguado normalizado: 0 -> 1 con rebote; en x = 1 vale EXACTO 1."""
    x = clamp01(x)
    if x >= 1.0:
        return 1.0
    w = 2 * math.pi * cycles
    wd = w * math.sqrt(max(1 - zeta * zeta, 1e-6))
    v = 1 - math.exp(-zeta * w * x) * (math.cos(wd * x) + zeta * w / wd * math.sin(wd * x))
    # se lleva suavemente a 1 en el ultimo 15 % para que el reposo sea exacto
    k = smooth((x - 0.85) / 0.15)
    return lerp(v, 1.0, k)


# ---------------------------------------------------------------- nodos
def _n(nt, kind, **kw):
    n = nt.nodes.new(kind)
    for k, v in kw.items():
        setattr(n, k, v)
    return n


def _link(nt, a, b):
    nt.links.new(a, b)


def _m(nt, op, a, b=None, c=None, clamp=False):
    n = _n(nt, "ShaderNodeMath", operation=op, use_clamp=clamp)
    for i, x in enumerate((a, b, c)):
        if x is None:
            continue
        if isinstance(x, (int, float)):
            n.inputs[i].default_value = x
        else:
            _link(nt, x, n.inputs[i])
    return n.outputs[0]


def _vm(nt, op, a, b=None, scale=None):
    n = _n(nt, "ShaderNodeVectorMath", operation=op)
    for i, x in enumerate((a, b)):
        if x is None:
            continue
        if isinstance(x, (tuple, list, Vector)):
            n.inputs[i].default_value = tuple(x)
        else:
            _link(nt, x, n.inputs[i])
    if scale is not None:
        s = n.inputs["Scale"]
        if isinstance(scale, (int, float)):
            s.default_value = scale
        else:
            _link(nt, scale, s)
    return n.outputs["Value"] if op in ('DOT_PRODUCT', 'LENGTH', 'DISTANCE') else n.outputs["Vector"]


def _sock(sockets, name, kind):
    for s in sockets:
        if s.name == name and s.type == kind:
            return s
    raise KeyError(name + "/" + kind)


def _mix_rgb(nt, fac, a, b):
    n = _n(nt, "ShaderNodeMix", data_type='RGBA')
    _link(nt, fac, _sock(n.inputs, "Factor", 'VALUE'))
    for nm, x in (("A", a), ("B", b)):
        s = _sock(n.inputs, nm, 'RGBA')
        if isinstance(x, (tuple, list)):
            s.default_value = tuple(x) + ((1.0,) if len(x) == 3 else ())
        else:
            _link(nt, x, s)
    return _sock(n.outputs, "Result", 'RGBA')


def _value(nt, name, v):
    n = _n(nt, "ShaderNodeValue", name=name, label=name)
    n.outputs[0].default_value = v
    return n.outputs[0]


def _base(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    return m, nt, _n(nt, "ShaderNodeOutputMaterial")


def _angle_frac(nt, start_deg, span_deg, direction):
    """Fraccion angular (0..1 dentro del tramo) de la posicion de OBJETO: para barridos de luz alrededor del centro."""
    tc = _n(nt, "ShaderNodeTexCoord")
    sep = _n(nt, "ShaderNodeSeparateXYZ")
    _link(nt, tc.outputs["Object"], sep.inputs[0])
    ang = _m(nt, 'ARCTAN2', sep.outputs["Y"], sep.outputs["X"])                      # radianes
    deg = _m(nt, 'MULTIPLY', ang, 180.0 / math.pi)
    rel = _m(nt, 'MULTIPLY', _m(nt, 'SUBTRACT', deg, start_deg), direction)
    return _m(nt, 'DIVIDE', _m(nt, 'FLOORED_MODULO', rel, 360.0), span_deg)


def fake_mat(name, base, self_glow=0.0, mask=None, mask_uv=None, mask_rot=0.0, mask_scale=1.0,
             ink=(0.96, 0.94, 0.90), ink_glow=0.35, mottle=0.16, grain=0.10, sh=None):
    """El sombreado de M_DrawPalette_SC (DrawPaletteShadePS) en emision pura. Nodos de valor para animar:
    SelfGlow (brillo propio, como el BP), Flash (suma LUZ calida: soldadura/destello), InkGlow (icono/texto)."""
    SH_ = sh or SH          # sh: otro juego de luz falsa (el timbre/sensor/SAVE usan el de sus renders aprobados)
    m, nt, out = _base(name)
    geo = _n(nt, "ShaderNodeNewGeometry")
    key = _m(nt, 'DIVIDE', _m(nt, 'ADD', _vm(nt, 'DOT_PRODUCT', geo.outputs["Normal"], tuple(LDIR)), SH_["Wrap"]),
             1 + SH_["Wrap"], clamp=True)
    fill = _m(nt, 'MAXIMUM', _vm(nt, 'DOT_PRODUCT', geo.outputs["Normal"], geo.outputs["Incoming"]), 0.0)
    sep = _n(nt, "ShaderNodeSeparateXYZ")
    _link(nt, geo.outputs["Normal"], sep.inputs[0])
    hemi = _m(nt, 'MULTIPLY_ADD', sep.outputs["Z"], 0.5, 0.5)
    shade = _m(nt, 'ADD', _m(nt, 'ADD', _m(nt, 'MULTIPLY', hemi, SH_["Ambient"]), _m(nt, 'MULTIPLY', key, SH_["Diffuse"])),
               _m(nt, 'MULTIPLY', fill, SH_["Fill"]))
    tc = _n(nt, "ShaderNodeTexCoord")
    mot = _n(nt, "ShaderNodeTexNoise")
    mot.inputs["Scale"].default_value = 30.0
    _link(nt, tc.outputs["Object"], mot.inputs["Vector"])
    grn = _n(nt, "ShaderNodeTexNoise")
    grn.inputs["Scale"].default_value = 900.0
    _link(nt, tc.outputs["Object"], grn.inputs["Vector"])
    tex = _m(nt, 'MULTIPLY', _m(nt, 'MULTIPLY_ADD', mot.outputs["Fac"], 2 * mottle, 1 - mottle),
             _m(nt, 'MULTIPLY_ADD', grn.outputs["Fac"], 2 * grain, 1 - grain))
    sg = _value(nt, "SelfGlow", self_glow)
    lvl = _m(nt, 'MULTIPLY', _m(nt, 'ADD', shade, sg), tex)
    col = _vm(nt, 'SCALE', tuple(base), scale=lvl)
    if mask:
        uvn = _n(nt, "ShaderNodeUVMap", uv_map=mask_uv)
        v = _vm(nt, 'SUBTRACT', uvn.outputs["UV"], (0.5, 0.5, 0.0))
        rot = _n(nt, "ShaderNodeVectorRotate", rotation_type='Z_AXIS')
        rot.inputs["Angle"].default_value = math.radians(mask_rot)
        _link(nt, v, rot.inputs["Vector"])
        v = _vm(nt, 'ADD', _vm(nt, 'SCALE', rot.outputs["Vector"], scale=1.0 / mask_scale), (0.5, 0.5, 0.0))
        img = _n(nt, "ShaderNodeTexImage", extension='CLIP')
        img.image = bpy.data.images.load(mask, check_existing=True)
        img.image.colorspace_settings.name = 'Non-Color'
        _link(nt, v, img.inputs["Vector"])
        ig = _value(nt, "InkGlow", ink_glow)
        ink_lvl = _m(nt, 'ADD', _m(nt, 'MULTIPLY', shade, 0.55), ig)
        ink_col = _vm(nt, 'SCALE', tuple(ink), scale=ink_lvl)
        bw = _n(nt, "ShaderNodeRGBToBW")
        _link(nt, img.outputs["Color"], bw.inputs[0])
        col = _mix_rgb(nt, bw.outputs[0], col, ink_col)
    fl = _value(nt, "Flash", 0.0)
    col = _vm(nt, 'ADD', col, _vm(nt, 'SCALE', tuple(LIGHT), scale=fl))
    em = _n(nt, "ShaderNodeEmission")
    _link(nt, col, em.inputs["Color"])
    _link(nt, em.outputs[0], out.inputs["Surface"])
    return m


def sweep_light_mat(name, color, glow, start_deg, span_deg, direction, alpha=None):
    """Luz (emision) con BARRIDO angular: Sweep 0..1 = cuanto del tramo esta encendido, con cabeza suave (Soft) y
    un brillo extra en la cabeza (Head). alpha: si se da, es translucida (Alpha = opacidad; el slider de vidrio)."""
    m, nt, out = _base(name)
    fr = _angle_frac(nt, start_deg, span_deg, direction)
    sw = _value(nt, "Sweep", 1.0)
    soft = _value(nt, "Soft", 0.06)
    head = _value(nt, "Head", 0.0)
    d = _m(nt, 'SUBTRACT', _m(nt, 'MULTIPLY', sw, _m(nt, 'ADD', soft, 1.0)), fr)       # >0 = encendido
    lit = _m(nt, 'DIVIDE', d, _m(nt, 'MAXIMUM', soft, 1e-4), clamp=True)
    # cabeza: campana justo en el frente del barrido (se apaga cuando Sweep llega a 1 para que el reposo sea exacto)
    hb = _m(nt, 'MULTIPLY', _m(nt, 'EXPONENT', _m(nt, 'MULTIPLY', _m(nt, 'POWER', _m(nt, 'DIVIDE', d, 0.05), 2.0), -1.0)), head)
    gl = _value(nt, "Glow", glow)
    k = _m(nt, 'MULTIPLY', _m(nt, 'ADD', lit, hb), gl)
    col = _vm(nt, 'SCALE', tuple(color), scale=k)
    em = _n(nt, "ShaderNodeEmission")
    _link(nt, col, em.inputs["Color"])
    if alpha is None:
        _link(nt, em.outputs[0], out.inputs["Surface"])
        return m
    al = _value(nt, "Alpha", alpha)
    tr = _n(nt, "ShaderNodeBsdfTransparent")
    mx = _n(nt, "ShaderNodeMixShader")
    _link(nt, _m(nt, 'MULTIPLY', al, lit), mx.inputs[0])
    _link(nt, tr.outputs[0], mx.inputs[1])
    _link(nt, em.outputs[0], mx.inputs[2])
    _link(nt, mx.outputs[0], out.inputs["Surface"])
    return m


# ---------------------------------------------------------------- escena
class Part:
    def __init__(self, name, obj, kind, angle_deg, hinge_r=None):
        self.name, self.obj, self.kind, self.angle_deg = name, obj, kind, angle_deg
        self.rest = obj.matrix_world.copy()
        a = math.radians(angle_deg)
        self.radial = Vector((math.cos(a), math.sin(a), 0.0))
        self.tangent = Vector((-math.sin(a), math.cos(a), 0.0))
        self.frame = Matrix.Rotation(a, 4, 'Z')
        ws = [self.rest @ v.co for v in obj.data.vertices]
        lo = Vector(tuple(min(w[i] for w in ws) for i in range(3)))
        hi = Vector(tuple(max(w[i] for w in ws) for i in range(3)))
        self.center, self.size, self.top = (lo + hi) / 2, hi - lo, hi.z
        rs = [w.xy.dot(self.radial.xy) for w in ws]
        self.r_in, self.r_out = min(rs), max(rs)
        self.hinge_in = self.radial * self.r_in + Vector((0, 0, self.top))
        self.hinge_out = self.radial * self.r_out + Vector((0, 0, self.top))


class Api:
    def __init__(self):
        self.parts, self.mats, self.defaults, self._root = {}, {}, {}, Matrix.Identity(4)
        self.cam = None
        self.extra = {}     # objetos agregados por la coreografia (luces, etc.): nombre -> obj

    # -- posar
    def reset(self):
        self._root = Matrix.Identity(4)
        for p in self.parts.values():
            p.obj.matrix_world = p.rest
            p.obj.hide_render = False
        for (mname, node), v in self.defaults.items():
            self.mats[mname].node_tree.nodes[node].outputs[0].default_value = v

    def pose(self, name, move=(0, 0, 0), rot=None, rot_part=None, pivot=None, scale=1.0):
        """Transforma la pieza desde su reposo: gira (rot = Quaternion en el marco de la paleta, o rot_part = (rx, ry,
        rz) en radianes en el marco de la pieza: X radial, Y tangencial, Z arriba) y escala (numero o (sr, st, sz) en el
        marco de la pieza) alrededor de pivot (Vector en metros; por defecto su centro), y despues la mueve move."""
        p = self.parts[name]
        pv = Vector(pivot) if pivot is not None else p.center
        R = Matrix.Identity(4)
        if rot is not None:
            R = rot.to_matrix().to_4x4()
        if rot_part is not None:
            rx, ry, rz = rot_part
            loc = (Matrix.Rotation(rz, 4, 'Z') @ Matrix.Rotation(ry, 4, 'Y') @ Matrix.Rotation(rx, 4, 'X'))
            R = R @ p.frame @ loc @ p.frame.inverted()
        if isinstance(scale, (int, float)):
            S = Matrix.Diagonal((scale, scale, scale, 1.0))
        else:
            S = p.frame @ Matrix.Diagonal((scale[0], scale[1], scale[2], 1.0)) @ p.frame.inverted()
        M = Matrix.Translation(Vector(move)) @ Matrix.Translation(pv) @ R @ S @ Matrix.Translation(-pv) @ p.rest
        p.obj.matrix_world = self._root @ M
        p._posed = True

    def hide(self, name, hidden=True):
        self.parts[name].obj.hide_render = hidden

    def root(self, move=(0, 0, 0), rot=None, scale=1.0, pivot=(0, 0, 0)):
        """Transforma TODA la paleta (se aplica despues de las poses; llamar ANTES de pose() en cada cuadro)."""
        pv = Vector(pivot)
        R = rot.to_matrix().to_4x4() if rot is not None else Matrix.Identity(4)
        S = Matrix.Diagonal((scale, scale, scale, 1.0)) if isinstance(scale, (int, float)) else Matrix.Diagonal(tuple(scale) + (1.0,))
        self._root = Matrix.Translation(Vector(move)) @ Matrix.Translation(pv) @ R @ S @ Matrix.Translation(-pv)
        for p in self.parts.values():
            p.obj.matrix_world = self._root @ p.rest

    # -- materiales
    def mat(self, name, **vals):
        """Nodos de valor de la pieza: SelfGlow, Flash, InkGlow (color/pincel/undo/redo/base/casquete/disco)."""
        m = self.mats[name]
        for k, v in vals.items():
            m.node_tree.nodes[k].outputs[0].default_value = v

    def groove(self, **vals):
        """La ranura de luz: Glow (1 = reposo), Sweep (0..1 del circulo, desde 90 grados = arriba, sentido horario visto
        de frente), Soft, Head (brillo extra en la cabeza del barrido)."""
        self.mat("Groove", **vals)

    def slider(self, **vals):
        """El slider de vidrio: Sweep (0..1 del arco, de izquierda a derecha), Alpha (0,35 reposo), Glow, Soft, Head."""
        self.mat("Slider", **vals)

    def add_object(self, name, obj):
        self.extra[name] = obj
        return obj

    # -- camara y render
    def camera(self, loc=(0.126, -0.77, 0.69), target=(0.0, -0.01, -0.02), lens=50):
        self.cam.location = Vector(loc)
        self.cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        self.cam.data.lens = lens

    def render_anim(self, pose_fn, out_dir, frames=46, size=(720, 540), samples=16, only=None):
        """Renderiza rest.png (reposo) y f_000..f_{frames-1}.png con t = f/(frames-1): 46 cuadros = 1,5 s a 30 fps.
        pose_fn(api, t) parte SIEMPRE del reposo (se llama reset() antes de cada cuadro)."""
        os.makedirs(out_dir, exist_ok=True)
        scn = bpy.context.scene
        scn.render.resolution_x, scn.render.resolution_y = size
        scn.cycles.samples = samples
        self.reset()
        scn.render.filepath = os.path.join(out_dir, "rest.png")
        bpy.ops.render.render(write_still=True)
        for f in range(frames):
            if only is not None and f not in only:
                continue
            t = f / (frames - 1)
            self.reset()
            pose_fn(self, t)
            scn.render.filepath = os.path.join(out_dir, "f_%03d.png" % f)
            bpy.ops.render.render(write_still=True)
        self.reset()
        print("ANIM_OK", out_dir, frames)


def _obj(nm):
    return bpy.data.objects["SM_DrawPalette_%s_SC" % nm]


def _clone(src, name):
    ob = bpy.data.objects.new(name, src.data)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def setup():
    if os.path.normcase(os.path.abspath(bpy.data.filepath or "")) != os.path.normcase(BLEND):
        bpy.ops.wm.open_mainfile(filepath=BLEND)
    scn = bpy.context.scene
    for ob in list(scn.objects):
        if ob.type != 'MESH':
            bpy.data.objects.remove(ob, do_unlink=True)
    api = Api()
    mats = api.mats
    body = (0.62, 0.56, 0.48)
    dark = (0.40, 0.37, 0.33)
    mats["Base"] = fake_mat("Base", body)
    mats["Groove"] = sweep_light_mat("Groove", LIGHT, 1.0, 90.0, 360.0, -1.0)
    mats["Swatch"] = fake_mat("Swatch", tuple(c * KEY_GAIN for c in COLORS[SEL_COLOR]), self_glow=0.3)
    mats["Knob"] = fake_mat("Knob", (0.93, 0.84, 0.72), self_glow=0.1)
    mats["Slider"] = sweep_light_mat("Slider", (0.95, 0.88, 0.78), 0.55, g.SLIDER_A0, g.SLIDER_A1 - g.SLIDER_A0, 1.0, alpha=0.35)
    base = _obj("Base")
    base.data.materials[0] = mats["Base"]
    base.data.materials[1] = mats["Groove"]
    _obj("Swatch").data.materials[0] = mats["Swatch"]
    _obj("Slider").data.materials[0] = mats["Slider"]
    for nm in ("Key", "SideKey", "Knob"):
        _obj(nm).hide_render = True
    api.parts["Base"] = Part("Base", base, "base", 0.0)
    api.parts["Swatch"] = Part("Swatch", _obj("Swatch"), "swatch", 0.0)
    api.parts["Slider"] = Part("Slider", _obj("Slider"), "slider", 270.0)

    def keyed(src, name, ang, mat, lift=0.0, scale_pivot=None, scale=1.0):
        ob = _clone(src, name)
        ob.material_slots[0].link = 'OBJECT'
        ob.material_slots[0].material = mat
        M = Matrix.Translation((0, 0, lift)) @ Matrix.Rotation(math.radians(ang), 4, 'Z')
        if scale_pivot is not None:
            pv = Vector(scale_pivot)
            M = Matrix.Translation(pv) @ Matrix.Diagonal((scale, scale, scale, 1.0)) @ Matrix.Translation(-pv) @ M
        ob.matrix_world = M
        return ob

    key = _obj("Key")
    for i, a in enumerate(g.KEY_ANGLES["Color"]):
        nm = "Color%d" % i
        mats[nm] = fake_mat(nm, tuple(c * KEY_GAIN for c in COLORS[i]), self_glow=0.28 if i == SEL_COLOR else 0.0)
        api.parts[nm] = Part(nm, keyed(key, nm, a, mats[nm], KEY_LIFT if i == SEL_COLOR else 0.0), "color", a)
    for i, a in enumerate(g.KEY_ANGLES["Brush"]):
        nm = "Brush%d" % i
        ico = os.path.join(DIR, "icon_%s.png" % g.BRUSHES[i])
        mats[nm] = fake_mat(nm, dark, self_glow=0.28 if i == SEL_BRUSH else 0.0, mask=ico if os.path.exists(ico) else None,
                            mask_uv="IconUV", mask_rot=ICON_ROT, mask_scale=ICON_SCALE)
        api.parts[nm] = Part(nm, keyed(key, nm, a, mats[nm], KEY_LIFT if i == SEL_BRUSH else 0.0), "brush", a)
    side = _obj("SideKey")
    for nm, rot in (("Undo", 0.0), ("Redo", 28.0)):
        mats[nm] = fake_mat(nm, dark, mask=os.path.join(DIR, "T_DrawPalette_%s.png" % nm), mask_uv="LabelUV")
        c = math.radians(g.SIDE_CENTER + rot)
        pv = (0.196 * math.cos(c), 0.196 * math.sin(c), g.u(g.Z_FLOAT))
        api.parts[nm] = Part(nm, keyed(side, nm, rot, mats[nm], 0.0, pv, SIDE_SIZE), "side", g.SIDE_CENTER + rot)
    a = math.radians(g.KNOB_ANGLE)
    kn = _clone(_obj("Knob"), "Knob")
    kn.material_slots[0].link = 'OBJECT'
    kn.material_slots[0].material = mats["Knob"]
    kn.matrix_world = Matrix.Translation((g.u(g.SLIDER_R * math.cos(a)), g.u(g.SLIDER_R * math.sin(a)), g.u(g.Z_FLOAT))) @ \
        Matrix.Diagonal((1.05, 1.05, 1.05, 1.0))
    api.parts["Knob"] = Part("Knob", kn, "knob", g.KNOB_ANGLE)
    for mname, m in mats.items():
        for n in m.node_tree.nodes:
            if n.type == 'VALUE':
                api.defaults[(mname, n.name)] = n.outputs[0].default_value
    # mundo negro, sin luces (como el nivel), Cycles solo emision -> pocas muestras
    w = bpy.data.worlds.new("Negro")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)
    scn.world = w
    scn.render.engine = 'CYCLES'
    scn.cycles.samples = 16
    scn.cycles.use_denoising = False
    scn.cycles.transparent_max_bounces = 16
    scn.view_settings.view_transform = 'Standard'
    scn.render.film_transparent = False
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = 'OPTIX'
        prefs.get_devices()
        for d in prefs.devices:
            d.use = d.type == 'OPTIX'
        scn.cycles.device = 'GPU'
    except Exception:
        pass
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    scn.collection.objects.link(cam)
    scn.camera = cam
    cam.data.clip_start = 0.005
    api.cam = cam
    api.camera()
    return api
