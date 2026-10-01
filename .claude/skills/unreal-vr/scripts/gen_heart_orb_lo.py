# -*- coding: utf-8 -*-
"""gen_heart_orb.py - genera SM_HeartOrb_SC: la malla de las esferas que emergen con cada latido.

Icoesfera de RADIO 50 cm (0,5 m en Blender; el export FBX con apply_unit_scale la lleva a cm,
igual que gen_heart_membrane.py). Es un lienzo: el vertex shader de M_HeartScape_SC (Part 3)
la reduce al tamano de cada esfera, la lleva a su punto de salida, la hace subir y, si es
ameba, la deforma. Subdivision 4 (Blender 5.2) = 642 vertices: 24 esferas = 15k vertices, poco al lado de
la membrana (32k), y el costo por vertice importa aca (gotcha 454).

Uso: "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" --background --python gen_heart_orb.py
Salida: <carpeta del script>/../../../../VR_Test/Saved/ClaudeScripts/SM_HeartOrb_SC.fbx
"""
import os

import bpy

SUBDIV = 3   # 162 vertices: la version LOW POLY (2026-10-01, 120 lunas; Beltran: "mas low poly si es necesario")
RADIO_M = 0.5
NOMBRE = "SM_HeartOrbLo_SC"


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=SUBDIV, radius=RADIO_M, location=(0.0, 0.0, 0.0))
    ob = bpy.context.active_object
    ob.name = NOMBRE
    ob.data.name = NOMBRE
    for p in ob.data.polygons:
        p.use_smooth = True
    ob.select_set(True)
    aqui = os.path.dirname(os.path.abspath(__file__))
    destino = os.path.abspath(os.path.join(aqui, "..", "..", "..", "..", "VR_Test", "Saved", "ClaudeScripts"))
    os.makedirs(destino, exist_ok=True)
    ruta = os.path.join(destino, NOMBRE + ".fbx")
    bpy.ops.export_scene.fbx(filepath=ruta, use_selection=True, apply_unit_scale=True, global_scale=1.0,
                             apply_scale_options='FBX_SCALE_NONE', object_types={'MESH'},
                             mesh_smooth_type='FACE', add_leaf_bones=False, bake_anim=False, path_mode='STRIP')
    print("LISTO %s  verts=%d  polys=%d  ->  %s" % (NOMBRE, len(ob.data.vertices), len(ob.data.polygons), ruta))


if __name__ == "__main__":
    main()
