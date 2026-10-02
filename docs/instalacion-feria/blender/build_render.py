"""Cúpula Soul Charger: escena para Cycles, misma geometría que el visor web.
Uso: blender --background --python build_render.py -- <salida.png> <ancho> <muestras> [camara]
Coordenadas: se construye en coordenadas del visor (x, y arriba, z hacia el público) y se pasa a Blender (x, -z, y)."""
import bpy, bmesh, math, json, base64, struct, sys, os
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = argv[0] if argv else os.path.join(HERE, 'render.png')
RES_X = int(argv[1]) if len(argv) > 1 else 960
SAMPLES = int(argv[2]) if len(argv) > 2 else 64
CAM = argv[3] if len(argv) > 3 else 'hero'

P = dict(R=1.70, H0=0.50, N=5, PS=75, W=0.10, F=6, T=0.018, lip=0.06, portal=0.05, portalDepth=0.12)
LED = (0.38, 0.56, 1.0)          # #8fb4ff, un poco más saturado que el visor para que tiña
LED_LIN = tuple(c ** 2.2 for c in LED)

def tb(x, y, z):
    return Vector((x, -z, y))

# ---------------- escena limpia ----------------
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

# ---------------- materiales ----------------
def mat(name, color, rough=0.8, emit=None, strength=0.0, sheen=0.0, img=None, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if sheen:
        b.inputs['Sheen Weight'].default_value = sheen
        b.inputs['Sheen Roughness'].default_value = 0.5
    if emit:
        b.inputs['Emission Color'].default_value = (*emit, 1)
        b.inputs['Emission Strength'].default_value = strength
    if img:
        t = nt.nodes.new('ShaderNodeTexImage')
        t.image = bpy.data.images.load(img)
        nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
        nt.links.new(t.outputs['Color'], b.inputs['Emission Color'])
        b.inputs['Emission Strength'].default_value = strength
    return m

def srgb(h):
    h = h.lstrip('#')
    return tuple((int(h[i:i + 2], 16) / 255) ** 2.2 for i in (0, 2, 4))

M = dict(
    wood=mat('Madera', srgb('#caa77b'), 0.7),
    white=mat('Blanco mate', srgb('#eeebe5'), 0.75),
    skin=mat('Piel interior', srgb('#f4f4f2'), 0.95),
    dark=mat('Base oscura', srgb('#1c1d22'), 0.6),
    tv=mat('TV', srgb('#101114'), 0.35),
    sofa=mat('Tela sillón', srgb('#d9d1c5'), 1.0, sheen=0.8),
    gear=mat('Plástico blanco', srgb('#ecece9'), 0.45),
    floor=mat('Piso sala', srgb('#1b1c21'), 0.65),
    led=mat('Cinta LED', (0, 0, 0), 1.0, emit=LED_LIN, strength=0.0),
    eeg=mat('Pantalla EEG', (0, 0, 0), 0.4, img=os.path.join(HERE, 'screen_eeg.png'), strength=1.6),
    brand=mat('Pantalla marca', (0, 0, 0), 0.4, img=os.path.join(HERE, 'screen_brand.png'), strength=1.6),
)

# ---------------- utilidades de malla ----------------
class Part:
    def __init__(self, name):
        self.name = name; self.bm = bmesh.new(); self.uv = []
    def poly(self, pts3, uvs=None):
        vs = [self.bm.verts.new(tb(*p)) for p in pts3]
        f = self.bm.faces.new(vs)
        if uvs: self.uv.extend(zip(vs, uvs))
        return f
    def solid(self, polys, d, skip_x0=False):
        keys, pts = {}, []
        def idx(p):
            k = (round(p[0], 5), round(p[1], 5), round(p[2], 5))
            if k not in keys: keys[k] = len(pts); pts.append(p)
            return keys[k]
        F = [[idx(p) for p in q] for q in polys]
        A = [self.bm.verts.new(tb(*p)) for p in pts]
        B = [self.bm.verts.new(tb(p[0] + d[0], p[1] + d[1], p[2] + d[2])) for p in pts]
        ec = {}
        for f in F:
            self.bm.faces.new([A[i] for i in f]); self.bm.faces.new([B[i] for i in reversed(f)])
            for i in range(len(f)):
                e = (f[i], f[(i + 1) % len(f)]); ec.setdefault(tuple(sorted(e)), []).append(e)
        for lst in ec.values():
            if len(lst) == 1:
                a, b = lst[0]
                if skip_x0 and abs(pts[a][0]) < 1e-4 and abs(pts[b][0]) < 1e-4: continue
                self.bm.faces.new([A[b], A[a], B[a], B[b]])
    def obj(self, material, bevel=None, mirror=False, smooth=True, cam=True, merge=False, inward=False):
        bm = self.bm
        if inward:
            # piel: caras sueltas, se orientan una por una hacia el interior de la cúpula
            for f in bm.faces:
                c = f.calc_center_median(); n = f.normal
                if abs(n.y) > 0.99: want = Vector((0, -1, 0))
                elif c.z < H0 - 1e-4: want = Vector((-c.x, 0, 0))
                else: want = Vector((0, 0, H0)) - c
                if n.dot(want) < 0: f.normal_flip()
        else:
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        me = bpy.data.meshes.new(self.name)
        if self.uv:
            lay = bm.loops.layers.uv.new('UVMap')
            vuv = {v: uv for v, uv in self.uv}
            for f in bm.faces:
                for l in f.loops:
                    if l.vert in vuv: l[lay].uv = vuv[l.vert]
        bm.to_mesh(me); bm.free()
        me.polygons.foreach_set('use_smooth', [smooth] * len(me.polygons))
        o = bpy.data.objects.new(self.name, me); sc.collection.objects.link(o)
        o.data.materials.append(material)
        if mirror and merge:
            m = o.modifiers.new('Espejo', 'MIRROR'); m.use_axis[0] = True; m.use_mirror_merge = True; m.merge_threshold = 0.0005
        if bevel:
            b = o.modifiers.new('Bisel', 'BEVEL')
            b.width, b.segments = bevel
            b.limit_method = 'ANGLE'; b.angle_limit = math.radians(30)
            b.harden_normals = True; b.profile = 0.5
        if mirror and not merge:
            m = o.modifiers.new('Espejo', 'MIRROR'); m.use_axis[0] = True; m.use_mirror_merge = False
        o.visible_camera = cam
        return o

def half_frame(r, w, h0, z0, n=48):
    q = [[(r, 0, z0), (r + w, 0, z0), (r + w, h0, z0), (r, h0, z0)]]
    for i in range(n):
        a0, a1 = math.pi / 2 * i / n, math.pi / 2 * (i + 1) / n
        q.append([(r * math.cos(a0), h0 + r * math.sin(a0), z0), ((r + w) * math.cos(a0), h0 + (r + w) * math.sin(a0), z0),
                  ((r + w) * math.cos(a1), h0 + (r + w) * math.sin(a1), z0), (r * math.cos(a1), h0 + r * math.sin(a1), z0)])
    return q

def slab(part, q, n, th):
    h = [c * th / 2 for c in n]
    part.solid([[(p[0] - h[0], p[1] - h[1], p[2] - h[2]) for p in q]], [c * th for c in n])

# ---------------- cúpula ----------------
R, H0, W, T, N = P['R'], P['H0'], P['W'], P['T'], P['N']
fr = [(-R * math.sin(math.radians(P['PS'] * i / N)), R * math.cos(math.radians(P['PS'] * i / N))) for i in range(N + 1)]
ribs, skin, leds = Part('Costillas y aletas'), Part('Piel interior'), Part('Cintas LED')
off = 0.004
for k in range(N):
    (az, ar), (bz, br) = fr[k], fr[k + 1]
    rs = lambda z: ar + (br - ar) * ((az - z) / (az - bz))
    ribs.solid(half_frame(ar, W, H0, az - T), (0, 0, T))
    rb = rs(bz + T) + 0.002
    ribs.solid(half_frame(rb, br + W - rb, H0, bz), (0, 0, T))
    ri = 0.006
    for j in range(P['F']):
        th = math.pi / 2 * j / (P['F'] - 1); c, s = math.cos(th), math.sin(th)
        za, zb = az - T, bz + T
        ia, ib = rs(za) + ri, rs(zb) + ri
        q = [(ia * c, H0 + ia * s, za), ((ar + W) * c, H0 + (ar + W) * s, za), ((br + W) * c, H0 + (br + W) * s, zb), (ib * c, H0 + ib * s, zb)]
        if j == P['F'] - 1: q = [(max(p[0], T / 2 + 0.001), p[1], p[2]) for p in q]
        slab(ribs, q, (-s, c, 0), T)
    slab(ribs, [(rs(az - T) + ri, T / 2, az - T), (ar + W, T / 2, az - T), (br + W, T / 2, bz + T), (rs(bz + T) + ri, T / 2, bz + T)], (0, 1, 0), T)
    # piel: banda cónica + pata
    nu, nv = 40, 6
    G = [[None] * (nv + 1) for _ in range(nu + 1)]
    for i in range(nu + 1):
        for j in range(nv + 1):
            u, v = i / nu, j / nv; th = u * math.pi / 2
            r = ar + (br - ar) * v - off; z = az + (bz - az) * v
            G[i][j] = (r * math.cos(th), H0 + r * math.sin(th), z)
    for i in range(nu):
        for j in range(nv):
            skin.poly([G[i][j], G[i][j + 1], G[i + 1][j + 1], G[i + 1][j]])
    for j in range(nv):
        v0, v1 = j / nv, (j + 1) / nv
        r0, z0 = ar + (br - ar) * v0 - off, az + (bz - az) * v0
        r1, z1 = ar + (br - ar) * v1 - off, az + (bz - az) * v1
        skin.poly([(r0, 0, z0), (r1, 0, z1), (r1, H0, z1), (r0, H0, z0)])
    # cinta LED a ras de piso (invisible a cámara: solo aporta luz)
    slab(leds, [(ar - 0.035, 0.012, az), (ar - 0.02, 0.012, az), (br - 0.02, 0.012, bz), (br - 0.035, 0.012, bz)], (0, 1, 0), 0.012)
# tapa trasera
bz, br = fr[N]
zb = bz - 0.001
n = 24
for i in range(n):
    a0, a1 = math.pi / 2 * i / n, math.pi / 2 * (i + 1) / n
    skin.poly([(0, H0, zb), (br * math.cos(a0), H0 + br * math.sin(a0), zb), (br * math.cos(a1), H0 + br * math.sin(a1), zb)])
skin.poly([(0, 0, zb), (br, 0, zb), (br, H0, zb), (0, H0, zb)])
slab(leds, [(0, 0.012, zb + 0.035), (br - 0.03, 0.012, zb + 0.035), (br - 0.03, 0.012, zb + 0.02), (0, 0.012, zb + 0.02)], (0, 1, 0), 0.012)

# portal (blanco) + cinta detrás del labio
portal = Part('Arco portal')
portal.solid(half_frame(R - P['lip'], W + P['portal'] + P['lip'], H0, 0.0), (0, 0, P['portalDepth']), skip_x0=True)
for i in range(40):
    a0, a1 = math.pi / 2 * i / 40, math.pi / 2 * (i + 1) / 40
    rr = R - 0.035
    slab(leds, [(rr * math.cos(a0), H0 + rr * math.sin(a0), -0.025), (rr * math.cos(a1), H0 + rr * math.sin(a1), -0.025),
                (rr * math.cos(a1), H0 + rr * math.sin(a1), -0.010), (rr * math.cos(a0), H0 + rr * math.sin(a0), -0.010)],
         (math.cos((a0 + a1) / 2), math.sin((a0 + a1) / 2), 0), 0.01)
slab(leds, [(R - 0.035, 0.02, -0.025), (R - 0.035, H0, -0.025), (R - 0.035, H0, -0.01), (R - 0.035, 0.02, -0.01)], (1, 0, 0), 0.01)

ribs.obj(M['wood'], bevel=(0.004, 3), mirror=True)
# piel: cara interior pintada de blanco, dorso de contrachapado crudo
_nt = M['skin'].node_tree; _b = _nt.nodes['Principled BSDF']
_geo = _nt.nodes.new('ShaderNodeNewGeometry'); _mix = _nt.nodes.new('ShaderNodeMix'); _mix.data_type = 'RGBA'
_mix.inputs[6].default_value = (*srgb('#c9ad86'), 1); _mix.inputs[7].default_value = (*srgb('#f4f4f2'), 1)
_nt.links.new(_geo.outputs['Backfacing'], _mix.inputs[0]); _nt.links.new(_mix.outputs[2], _b.inputs['Base Color'])
if os.environ.get('SKIN_FLIP') == '1':
    _mix.inputs[6].default_value, _mix.inputs[7].default_value = (*srgb('#f4f4f2'), 1), (*srgb('#c9ad86'), 1)
skin.obj(M['skin'], mirror=True, merge=True, inward=True)
portal.obj(M['white'], bevel=(0.012, 4), mirror=True, merge=True)
led_obj = leds.obj(M['led'], mirror=True, smooth=False, cam=False)

# ---------------- tótems ----------------
def xf(p, pos, rot):
    c, s = math.cos(rot), math.sin(rot)
    x, y, z = p
    return (pos[0] + x * c + z * s, pos[1] + y, pos[2] - x * s + z * c)

def totem(name, pos, rot, screen_mat, plate):
    w, h, th, cy, cr = 0.45, 1.80, 0.035, 1.10, 0.385
    def inside(x, y):
        if y < 0 or y > h: return False
        if y <= h - w: return abs(x) <= w
        return x * x + (y - (h - w)) ** 2 <= w * w
    n = 192; outer, inner = [], []
    for i in range(n):
        a = 2 * math.pi * i / n; dx, dy = math.cos(a), math.sin(a)
        lo, hi = cr, 3.0
        for _ in range(40):
            mid = (lo + hi) / 2
            if inside(dx * mid, cy + dy * mid): lo = mid
            else: hi = mid
        outer.append((dx * lo, cy + dy * lo)); inner.append((dx * cr, cy + dy * cr))
    pnl = Part(name + ' panel')
    quads = []
    for i in range(n):
        j = (i + 1) % n
        quads.append([xf((inner[i][0], inner[i][1], 0), pos, rot), xf((outer[i][0], outer[i][1], 0), pos, rot),
                      xf((outer[j][0], outer[j][1], 0), pos, rot), xf((inner[j][0], inner[j][1], 0), pos, rot)])
    dz = xf((0, 0, -th), (0, 0, 0), rot)
    pnl.solid(quads, dz)
    pnl.obj(M['white'], bevel=(0.008, 4))
    tv = Part(name + ' TV')
    tv.solid([[xf((-0.41, cy - 0.41, -th - 0.015), pos, rot), xf((0.41, cy - 0.41, -th - 0.015), pos, rot),
               xf((0.41, cy + 0.41, -th - 0.015), pos, rot), xf((-0.41, cy + 0.41, -th - 0.015), pos, rot)]], xf((0, 0, -0.06), (0, 0, 0), rot))
    tv.obj(M['tv'], bevel=(0.004, 2))
    scr = Part(name + ' pantalla')
    m = 96; ctr = xf((0, cy, -th - 0.012), pos, rot)
    for i in range(m):
        a0, a1 = 2 * math.pi * i / m, 2 * math.pi * (i + 1) / m
        p0 = xf(((cr + 0.01) * math.cos(a0), cy + (cr + 0.01) * math.sin(a0), -th - 0.012), pos, rot)
        p1 = xf(((cr + 0.01) * math.cos(a1), cy + (cr + 0.01) * math.sin(a1), -th - 0.012), pos, rot)
        scr.poly([ctr, p0, p1], uvs=[(0.5, 0.5), (0.5 + 0.5 * math.cos(a0), 0.5 + 0.5 * math.sin(a0)), (0.5 + 0.5 * math.cos(a1), 0.5 + 0.5 * math.sin(a1))])
    scr.obj(screen_mat, smooth=False)
    ft = Part(name + ' pie')
    if plate:
        ft.solid([[xf((-0.45, 0, 0.12), pos, rot), xf((0.45, 0, 0.12), pos, rot), xf((0.45, 0, -0.33), pos, rot), xf((-0.45, 0, -0.33), pos, rot)]], (0, 0.02, 0))
        ft.obj(M['white'], bevel=(0.004, 3))
    else:
        ft.solid([[xf((-0.25, 0, -0.03), pos, rot), xf((0.25, 0, -0.03), pos, rot), xf((0.25, 0, -0.38), pos, rot), xf((-0.25, 0, -0.38), pos, rot)]], (0, 0.03, 0))
        ft.obj(M['dark'], bevel=(0.004, 2))

totem('Tótem interior', (0, 0, -0.85), 0.0, M['eeg'], False)
totem('Tótem recepción', (2.33, 0, 1.40), -0.38, M['brand'], True)

def stadium(L, D, n=40):
    r = D / 2; pts = []
    for i in range(n + 1):
        a = -math.pi / 2 + math.pi * i / n; pts.append((L / 2 - r + r * math.cos(a), r * math.sin(a)))
    for i in range(n + 1):
        a = math.pi / 2 + math.pi * i / n; pts.append((-L / 2 + r + r * math.cos(a), r * math.sin(a)))
    return pts

def prism(name, pts2, y0, hgt, cx, cz, material, bevel, rot=0.0, cam=True):
    p = Part(name)
    ring = [xf((x, y0, z), (cx, 0, cz), rot) for x, z in pts2]
    c = xf((0, y0, 0), (cx, 0, cz), rot)
    tris = [[c, ring[(i + 1) % len(ring)], ring[i]] for i in range(len(ring))]
    p.solid(tris, (0, hgt, 0))
    return p.obj(material, bevel=bevel)

# mesa del tótem (estadio con luz por debajo)
zc = -0.85 + 0.20 + 0.005
prism('Mesa tótem', stadium(0.70, 0.40), 0.07, 0.27, 0, zc, M['white'], (0.025, 5))
prism('Mesa tótem base', stadium(0.60, 0.30), 0.0, 0.07, 0, zc, M['dark'], (0.005, 2))
glow = Part('Luz bajo la mesa')
st = stadium(0.62, 0.32)
glow.solid([[(x, 0.004, zc - z) for x, z in st]], (0, 0.004, 0))
glow.obj(M['led'], smooth=False, cam=False)

def circle(r, n=64):
    return [(r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n)) for i in range(n)]

# mesa de recepción, blanca, 68 cm
RX, RZ, RH = 1.95, 2.05, 0.68
prism('Recepción tapa', circle(0.40), RH - 0.03, 0.03, RX, RZ, M['white'], (0.008, 3))
prism('Recepción pie', circle(0.03, 24), 0.02, RH - 0.05, RX, RZ, M['white'], None)
prism('Recepción base', circle(0.25), 0.0, 0.02, RX, RZ, M['white'], (0.005, 3))

# ---------------- modelos (sillón, gafas, mandos) ----------------
J = json.load(open(os.path.join(HERE, '..', 'models.json')))
def model(key, material, pos, rot, mirror_x=False, weld=0.004):
    raw = base64.b64decode(J[key]['pos']); ix = base64.b64decode(J[key]['idx'])
    P3 = struct.unpack('<%df' % (len(raw) // 4), raw); I = struct.unpack('<%dI' % (len(ix) // 4), ix)
    bm = bmesh.new()
    vs = []
    for i in range(0, len(P3), 3):
        x, y, z = P3[i], P3[i + 1], P3[i + 2]
        if mirror_x: x = -x
        vs.append(bm.verts.new(tb(*xf((x, y, z), pos, rot))))
    for i in range(0, len(I), 3):
        try:
            f = (vs[I[i]], vs[I[i + 1]], vs[I[i + 2]])
            bm.faces.new(f if not mirror_x else f[::-1])
        except ValueError:
            pass
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=weld)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(key); bm.to_mesh(me); bm.free()
    me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    o = bpy.data.objects.new(key, me); sc.collection.objects.link(o); o.data.materials.append(material)
    return o

ca = math.radians(45)
for sx in (1, -1):
    model('sofa', M['sofa'], (sx * 1.0, 0, -0.50), sx * (-math.pi / 2 + ca))
top = 0.07 + 0.27 + 0.025
for sx in (-1, 1):
    model('headset', M['gear'], (sx * 0.24, top, zc + 0.01), 0.0, weld=0.0006)
for x in (-0.12, -0.04, 0.04, 0.12):
    model('ctrl', M['gear'], (x, top, zc + 0.02), 0.3 if x < 0 else -0.3, mirror_x=x < 0, weld=0.0006)

# ---------------- sala, luz y cámara ----------------
fl = Part('Piso'); fl.poly([(-15, 0, -15), (15, 0, -15), (15, 0, 15), (-15, 0, 15)]); fl.obj(M['floor'], smooth=False)
world = bpy.data.worlds.new('Sala'); sc.world = world; world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.004, 0.0045, 0.006, 1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value = 1.0
amb = bpy.data.lights.new('Luz de sala', 'AREA'); amb.energy = 300; amb.size = 6; amb.color = (1.0, 0.97, 0.93)
ao = bpy.data.objects.new('Luz de sala', amb); sc.collection.objects.link(ao); ao.location = tb(1.5, 4.5, 3.5); ao.rotation_euler = (math.radians(40), 0, math.radians(15))

LED_STRENGTH = float(os.environ.get('LED_STRENGTH', '60'))
M['led'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = LED_STRENGTH

cams = {
    'hero': ((-1.3, 1.65, 5.3), (0.75, 0.95, -0.2), 42),
    'front': ((0.0, 1.35, 5.6), (0.2, 1.05, -0.4), 40),
    'inside': ((1.15, 1.25, 0.9), (-0.4, 1.05, -0.9), 55),
    'brandzoom': ((2.0, 1.15, 2.6), (2.33, 1.10, 1.40), 25),
    'frente': ((0.75, 1.3, 7.6), (0.75, 1.0, 0.0), 30),
    'madera': ((4.6, 1.5, -1.6), (0.2, 1.05, -0.55), 38),
    'atras': ((-3.9, 2.4, -4.4), (0.0, 0.95, -0.7), 36),
    'cupula': ((0.35, 0.85, 0.55), (-0.15, 1.75, -1.1), 72),
    'recepcion': ((4.6, 1.3, 5.2), (1.3, 0.95, 0.3), 36),
    'aerea': ((3.9, 5.9, 5.6), (0.5, 0.35, 0.0), 38),
    'mesa': ((0.05, 1.2, 0.3), (0.0, 0.42, -0.66), 40),
    'salida': ((-0.95, 1.05, -0.95), (1.2, 0.95, 1.6), 56),
}
cp, ct, fov = cams[CAM]
cd = bpy.data.cameras.new('Cam'); cd.sensor_fit = 'VERTICAL'; cd.angle_y = math.radians(fov) * (9 / 16) / (9 / 16)
co = bpy.data.objects.new('Cam', cd); sc.collection.objects.link(co); sc.camera = co
co.location = tb(*cp)
d = tb(*ct) - tb(*cp)
co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()

fill = bpy.data.lights.new('Luz de sala 2', 'AREA'); fill.energy = 260; fill.size = 5; fill.color = (0.95, 0.97, 1.0)
fo = bpy.data.objects.new('Luz de sala 2', fill); sc.collection.objects.link(fo); fo.location = tb(4.5, 3.2, -3.5)
fo.rotation_euler = (tb(0, 1.0, -0.7) - fo.location).to_track_quat('-Z', 'Y').to_euler()
# ---------------- render ----------------
sc.render.engine = 'CYCLES'
prefs = bpy.context.preferences.addons['cycles'].preferences
for dev in ('OPTIX', 'CUDA'):
    try:
        prefs.compute_device_type = dev; prefs.get_devices()
        if any(d.type == dev for d in prefs.devices):
            for d in prefs.devices: d.use = True
            sc.cycles.device = 'GPU'; break
    except Exception:
        pass
sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = os.environ.get('DENOISE','1')=='1'
sc.render.resolution_x = RES_X; sc.render.resolution_y = int(RES_X * 9 / 16); sc.render.resolution_percentage = 100
sc.view_settings.view_transform = 'AgX'
sc.view_settings.look = 'AgX - Base Contrast'
sc.view_settings.exposure = float(os.environ.get('EXPOSURE', '0'))
sc.render.filepath = OUT
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'cupula_soul_charger.blend'))
bpy.ops.render.render(write_still=True)
print('RENDER_OK', OUT, sc.cycles.device)
