# v_fbx.py - Blender headless: importa SM_BreathValley_SC.fbx (importador oficial, no el parser del generador) y mide
# vertices, triangulos, radios de los anillos, z, orientacion de las caras y alcance efectivo en cm (lo que ve Unreal).
import bpy, math, os, sys
from collections import Counter
FBX = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "SM_BreathValley_SC.fbx"))
bpy.ops.wm.read_factory_settings(use_empty=True)
print("VFBX archivo", FBX, os.path.getsize(FBX), "bytes")
bpy.ops.import_scene.fbx(filepath=FBX)
obs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
print("VFBX objetos malla", len(obs), [o.name for o in obs])
o = obs[0]
me = o.data
mw = o.matrix_world
print("VFBX matrix_world escala", tuple(round(s, 6) for s in mw.to_scale()), "rot", tuple(round(math.degrees(a), 3) for a in mw.to_euler()))
nv, nf = len(me.vertices), len(me.polygons)
ntri = sum(len(p.vertices) - 2 for p in me.polygons)
print("VFBX vertices", nv, "poligonos", nf, "triangulos", ntri, "todos triangulos", all(len(p.vertices) == 3 for p in me.polygons))
# en Blender el FBX de Unreal-cm: coordenadas mundo en m; el importador aplica la escala del nodo
ws = [mw @ v.co for v in me.vertices]
zs = [w.z for w in ws]
rad = [math.hypot(w.x, w.y) for w in ws]
print("VFBX z mundo min/max (m)", min(zs), max(zs))
print("VFBX radio max (m)", max(rad), "-> en Unreal (cm, x100)", max(rad) * 100)
rings = sorted(Counter(round(r, 3) for r in rad).items())
print("VFBX anillos distintos (sin el centro)", len([r for r, c in rings if r > 0]), "vertices por anillo", sorted(set(c for r, c in rings if r > 0)))
rs = [r for r, c in rings if r > 0]
print("VFBX primeros radios (m)", rs[:3], "radio 19", rs[18], "ultimos 7", rs[-7:])
# orientacion de las caras en mundo (+Z arriba en Blender)
up = 0
for p in me.polygons:
    a, b, c = (mw @ me.vertices[i].co for i in p.vertices)
    n = (b - a).cross(c - a)
    up += n.z > 0
print("VFBX caras con normal geometrica +Z (mundo)", up, "de", nf)
# duplicados
print("VFBX vertices duplicados", nv - len(set((round(w.x, 4), round(w.y, 4), round(w.z, 4)) for w in ws)))
print("VFBX uv layers", [l.name for l in me.uv_layers])
# agrupar radios con tolerancia relativa 1e-5 (el redondeo a mm parte algunos anillos)
rr = sorted(rad)
grupos = []
for r in rr:
    if r < 1e-6:
        continue
    if grupos and abs(r - grupos[-1][-1]) <= 1e-5 * max(r, 1.0):
        grupos[-1].append(r)
    else:
        grupos.append([r])
print("VFBX anillos (tolerancia rel 1e-5)", len(grupos), "tamanos", sorted(set(len(g) for g in grupos)))
