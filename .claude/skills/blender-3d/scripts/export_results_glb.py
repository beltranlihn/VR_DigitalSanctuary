# export_results_glb.py - el CUADRO DE RESULTADOS (SM_Results_SC.blend de gen_results.py) a GLB para el prototipo web:
# web/prototipo-narrativo/modelos/SM_Results_SC.glb (+ .glb.json, el envoltorio que lee world.js/loadGLB).
# Cada pieza con la rotacion HORNEADA en la malla: el nodo solo lleva traslacion, y los ejes locales de cada pieza son
# los de three.js: X = ancho, Y = alto (arriba), Z = la cara hacia el usuario. Asi la web la usa SIN rotar y anima las
# piezas como Unreal (ventanas: scale.x a lo ancho, scale.y a lo alto; lamina: scale.y).
# Nodos: Rim, Glass, WinCalm (y +0,26), WinHeart (+0,03), WinBreath (-0,18), WinMelody (-0,38), Tip (+0,625).
# Materiales (nombres para los regex de world.js): M_Results_Rim · M_Results_Glass · M_Results_Frame · M_Results_Pane ·
# M_Results_TipFrame · M_Results_TipGlass. Sin el trazo (la web usa su propia aparicion).
# Uso: blender -b <SM_Results_SC.blend> --python export_results_glb.py -- <salida.glb> [pieza1 pieza2 ...]
#   (sin piezas: las del cuadro. Tambien exporta los botones SHARE: -- SM_ShareButton_SC.glb Base Plate Slider)
import base64
import json
import os
import sys
import traceback

import bpy
from mathutils import Matrix

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
PIECES = ["Rim", "Glass", "WinCalm", "WinHeart", "WinBreath", "WinMelody", "Tip"]
R_WEB = Matrix(((1.0, 0.0, 0.0), (0.0, 0.0, -1.0), (0.0, 1.0, 0.0))).to_4x4()   # = gen_results.R_WEB


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    out = os.path.abspath(args[0])
    pieces = args[1:] or PIECES
    ob = bpy.data.objects
    baked = {}
    for nm in pieces:
        o = ob[nm]
        loc = o.matrix_world.to_translation()
        if o.data.name not in baked:                 # calma y latido comparten malla: se gira una sola vez
            me = o.data.copy()
            me.transform(R_WEB)
            baked[o.data.name] = me
        o.data = baked[o.data.name]
        o.matrix_world = Matrix.Translation(loc)
    for o in bpy.context.scene.objects:
        o.select_set(o.name in pieces)
    bpy.context.view_layer.objects.active = ob[pieces[0]]
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', use_selection=True, export_apply=True,
                              export_animations=False, export_cameras=False, export_lights=False, export_yup=True,
                              export_texcoords=True, export_normals=True, export_materials='EXPORT')
    for nm in pieces:
        o = ob[nm]
        vs = [o.matrix_world @ v.co for v in o.data.vertices]
        mn = [round(min(p[k] for p in vs), 4) for k in range(3)]
        mx = [round(max(p[k] for p in vs), 4) for k in range(3)]
        print("PIEZA", nm, "bbox Blender(xyz)", mn, mx, "mats", [s.material.name for s in o.material_slots])
    wrap = out + ".json"                             # los artifacts no sirven .glb: world.js lo desenvuelve
    json.dump({"format": "sc-glb-v1", "name": os.path.basename(out),
               "b64": base64.b64encode(open(out, "rb").read()).decode()}, open(wrap, "w"))
    print("GLB_OK", out, os.path.getsize(out), "bytes · envoltorio", wrap)


try:
    main()
except BaseException as e:
    print("GLB_FALLO", type(e).__name__, e)
    traceback.print_exc()
