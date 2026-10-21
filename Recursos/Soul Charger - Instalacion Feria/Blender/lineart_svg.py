"""Planos vectoriales (SVG, sin texto) desde la escena de la cúpula, con Line Art.
Uso: blender --background cupula_soul_charger.blend --python lineart_svg.py -- <salida.svg> <vista> [grueso] [fino]
Vistas: planta, alzado, lateral, axo, axo_atras. Contorno más grueso que las líneas interiores."""
import bpy, math, sys
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
OUT, VIEW = argv[0], argv[1]
THICK = float(argv[2]) if len(argv) > 2 else 0.006
THIN = float(argv[3]) if len(argv) > 3 else 0.0022
sc = bpy.context.scene

# fuera del dibujo: piso, emisores de luz
for o in sc.objects:
    if o.type == 'MESH' and o.name in ('Piso', 'Cintas LED', 'Luz bajo la mesa'):
        o.lineart.usage = 'EXCLUDE'

# cámara ortográfica
cam = sc.camera
cam.data.type = 'ORTHO'
cam.data.shift_x = cam.data.shift_y = 0
C = Vector((0.40, -0.35, 1.0))       # centro aproximado del conjunto (Blender)
if VIEW in ('escala_planta', 'escala_corte'):
    # misma cámara ortográfica y misma resolución: 5 m en 2000 px = 400 px por metro
    if VIEW == 'escala_planta':
        cam.location = (0.0, 0.8, 0.9); cam.rotation_euler = (0, 0, 0)
    else:
        cam.location = (0.0, 0.8, 1.25); cam.rotation_euler = (math.radians(90), 0, math.radians(90))
    cam.data.clip_start = 0.001; cam.data.ortho_scale = 5.0
    sc.render.resolution_x, sc.render.resolution_y = 2000, 2000
elif VIEW == 'planta' or VIEW.startswith('corte'):
    cam.location = (C.x, C.y, 12 if VIEW == 'planta' else int(VIEW[5:]) / 100); cam.rotation_euler = (0, 0, 0)
    cam.data.clip_start = 0.001
    cam.data.ortho_scale = 5.6; sc.render.resolution_x, sc.render.resolution_y = 1800, 1600
elif VIEW == 'seccion':
    cam.location = (0.0, 0.75, 1.25); cam.rotation_euler = (math.radians(90), 0, math.radians(90))
    cam.data.clip_start = 0.001; cam.data.ortho_scale = 4.0
    sc.render.resolution_x, sc.render.resolution_y = 2000, 1300
elif VIEW in ('alzado', 'lateral'):
    yaw = 0 if VIEW == 'alzado' else math.radians(90)
    d = Vector((math.sin(-yaw) * -1, 1, 0)) if VIEW == 'alzado' else Vector((-1, 0, 0))
    cam.location = Vector((C.x, C.y, 1.15)) - d * 20
    cam.rotation_euler = (math.radians(90), 0, yaw)
    cam.data.ortho_scale = 4.5 if VIEW == 'alzado' else 3.6
    sc.render.resolution_x, sc.render.resolution_y = 2000, 1000
else:
    yaw = math.radians(135) if VIEW == 'axo_atras' else math.radians(-45)
    if VIEW == 'axo_exp': C = Vector((0.0, 0.75, 1.0))
    tilt = math.radians(54.7356)
    cam.rotation_euler = (tilt, 0, yaw)
    look = cam.rotation_euler.to_matrix() @ Vector((0, 0, -1))
    cam.location = Vector((C.x, C.y, 0.9)) - look * 25
    cam.data.ortho_scale = 6.4 if VIEW == 'axo_exp' else 5.4
    sc.render.resolution_x, sc.render.resolution_y = 2000, 1500
cam.data.clip_end = 100

# objeto de líneas: dos capas (contorno grueso, interior fino)
gp = bpy.data.grease_pencils.new('Lineas')
ob = bpy.data.objects.new('Lineas', gp); sc.collection.objects.link(ob)
mat = bpy.data.materials.new('Linea negra'); bpy.data.materials.create_gpencil_data(mat)
mat.grease_pencil.color = (0, 0, 0, 1); gp.materials.append(mat)
for name in ('Contorno', 'Interior'):
    ly = gp.layers.new(name); ly.frames.new(sc.frame_current)

def lineart(name, layer, radius, contour):
    m = ob.modifiers.new(name, 'LINEART')
    m.source_type = 'SCENE'; m.target_layer = layer; m.target_material = mat
    m.radius = radius
    m.use_contour = True
    m.silhouette_filtering = 'GROUP' if contour else 'NONE'
    m.use_crease = not contour; m.use_intersection = False
    m.use_custom_camera = True; m.source_camera = cam
    m.use_clip_plane_boundaries = VIEW.startswith('corte') or VIEW in ('seccion', 'escala_planta', 'escala_corte')
    m.use_material = False; m.use_edge_mark = False; m.use_loose = False
    m.use_crease_on_smooth = True; m.use_crease_on_sharp = True
    m.crease_threshold = math.radians(120)
    return m

lineart('Contorno', 'Contorno', THICK, True)
lineart('Interior', 'Interior', THIN, False)

bpy.context.view_layer.update()
print('CAM', VIEW, sc.render.resolution_x, sc.render.resolution_y, cam.data.ortho_scale, tuple(round(v, 2) for v in cam.location), tuple(round(math.degrees(v), 1) for v in cam.rotation_euler), cam.data.type)
bpy.context.view_layer.objects.active = ob
for o in sc.objects: o.select_set(False)
ob.select_set(True)
with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob], selected_editable_objects=[ob]):
    bpy.ops.object.lineart_bake_strokes()
# proyección propia por la cámara ortográfica y SVG escrito a mano (sin texto)
from bpy_extras.object_utils import world_to_camera_view
Wpx, Hpx = sc.render.resolution_x, sc.render.resolution_y
WIDTH = {'Contorno': float(argv[4]) if len(argv) > 4 else 2.0, 'Interior': float(argv[5]) if len(argv) > 5 else 0.9}
dg = bpy.context.evaluated_depsgraph_get()
gpe = ob.evaluated_get(dg).data
out = []; n = 0
for name in ('Interior', 'Contorno'):
    ly = gpe.layers[name]
    dr = ly.frames[0].drawing
    paths = []
    for st in dr.strokes:
        pts = []
        for pt in st.points:
            v = world_to_camera_view(sc, cam, ob.matrix_world @ Vector(pt.position))
            pts.append((v.x * Wpx, (1 - v.y) * Hpx))
        if len(pts) < 2: continue
        # trazos parásitos: segmentos larguísimos o puntos fuera de la hoja
        if any(x < -5 or x > Wpx + 5 or y < -5 or y > Hpx + 5 for x, y in pts): continue
        if max(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)) > 0.22 * Wpx: continue
        d = 'M' + ' L'.join('%.2f %.2f' % p for p in pts)
        paths.append('<path d="%s"/>' % d); n += 1
    out.append('<g fill="none" stroke="#000" stroke-width="%.2f" stroke-linecap="round" stroke-linejoin="round">%s</g>' % (WIDTH[name], ''.join(paths)))
svg = '<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">%s</svg>' % (Wpx, Hpx, Wpx, Hpx, ''.join(out))
open(OUT, 'w', encoding='utf-8').write(svg)
print('SVG_OK', OUT, 'trazos', n)
