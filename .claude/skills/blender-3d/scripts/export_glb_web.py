"""Exporta un .blend a GLB para el prototipo web narrativo (web/prototipo-narrativo/modelos/), más su envoltorio .glb.json.
Headless, no modifica el .blend. Uso:
  blender -b <archivo.blend> --python export_glb_web.py -- <salida.glb> [objeto1 objeto2 ...]
Sin nombres de objeto exporta todas las mallas visibles. Aplica modificadores, conserva materiales (nombres de slot),
UV0 y normales; sin animación ni cámaras/luces. Imprime el bounding box de cada malla (en metros, ejes glTF Y-arriba)."""
import bpy, sys, os
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
out = os.path.abspath(argv[0]); names = argv[1:]
bpy.ops.object.select_all(action='DESELECT')
objs = [o for o in bpy.context.scene.objects if o.type == 'MESH' and (not names or o.name in names) and o.visible_get()]
for o in objs: o.select_set(True)
if objs: bpy.context.view_layer.objects.active = objs[0]
os.makedirs(os.path.dirname(out), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', use_selection=True, export_apply=True, export_animations=False,
                          export_cameras=False, export_lights=False, export_yup=True, export_texcoords=True, export_normals=True,
                          export_materials='EXPORT')
for o in objs:
    bb = [o.matrix_world @ v.co for v in o.data.vertices]
    mn = [min(p[i] for p in bb) for i in range(3)]; mx = [max(p[i] for p in bb) for i in range(3)]
    print('MALLA', o.name, 'verts', len(o.data.vertices), 'bbox Blender(xyz)', [round(a, 4) for a in mn], [round(a, 4) for a in mx], 'mats', [s.material.name if s.material else None for s in o.material_slots])
import base64, json
wrap = out + '.json'  # los artifacts no sirven .glb: se publica envuelto en JSON (world.js lo desenvuelve)
json.dump({'format': 'sc-glb-v1', 'name': os.path.basename(out), 'b64': base64.b64encode(open(out, 'rb').read()).decode()}, open(wrap, 'w'))
print('GLB', out, os.path.getsize(out), 'bytes · envoltorio', wrap)
