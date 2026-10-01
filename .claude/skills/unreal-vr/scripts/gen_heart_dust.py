# -*- coding: utf-8 -*-
"""gen_heart_dust.py - genera SM_HeartDust_SC, la malla del POLVO de la etapa del latido (2026-10-01).

4400 quads diminutos (receta de la gotcha 477, como SM_AlmaAura_SC): 3900 de polvo y 500 particulas, cada uno en su
lugar de reposo en el espacio LOCAL de BP_HeartScape_SC (origen = la esfera central, z = 0 el agua). Semillas y
codificacion: heart_dust_model.py (seeds/encode): UV0 = (esquina, 0.5), UV1 = (tipo, ph1), UV2 = (b, ph2).

CONVENCION (la de gen_valley_dust.py): 1 unidad de Blender = 100 uu; un punto UE (x, y, z) va a Blender como
(x, -y, z)/100 (mano derecha); export FBX con apply_unit_scale.

Uso (headless, no toca la sesion de Blender del usuario):
  "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" --background --factory-startup --python gen_alma_aura.py
Salida: VR_Test/Saved/ClaudeScripts/Alma/SM_AlmaAura_SC.fbx + verificacion por reimportacion (imprime VERIF).
"""
import os
import sys

import bpy

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import heart_dust_model as am  # noqa: E402

CAPAS = ("UV0", "UV1", "UV2")


def limpiar():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def nube(nombre, enc):
    nv = enc["LP"].shape[0]
    verts = [(p[0] / 100.0, -p[1] / 100.0, p[2] / 100.0) for p in enc["LP"]]
    faces = [(4 * i, 4 * i + 1, 4 * i + 2, 4 * i + 3) for i in range(nv // 4)]
    me = bpy.data.meshes.new(nombre)
    me.from_pydata(verts, [], faces)
    me.validate()
    for nom in CAPAS:
        lay = me.uv_layers.new(name=nom)
        datos = enc[nom]
        for li, loop in enumerate(me.loops):
            v = loop.vertex_index
            lay.data[li].uv = (float(datos[v, 0]), float(datos[v, 1]))
    ob = bpy.data.objects.new(nombre, me)
    bpy.context.collection.objects.link(ob)
    return ob


def exportar(ob, carpeta):
    ruta = os.path.join(carpeta, ob.name + ".fbx")
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.fbx(filepath=ruta, use_selection=True, apply_unit_scale=True, global_scale=1.0,
                             apply_scale_options='FBX_SCALE_NONE', object_types={'MESH'}, mesh_smooth_type='FACE',
                             use_mesh_modifiers=True, add_leaf_bones=False, bake_anim=False, path_mode='STRIP')
    return ruta


def verificar(ruta, enc, sd):
    import numpy as np
    limpiar()
    bpy.ops.import_scene.fbx(filepath=ruta)
    ob = [o for o in bpy.data.objects if o.type == 'MESH'][0]
    me = ob.data
    nv = enc["LP"].shape[0]
    capas = [l.name for l in me.uv_layers]
    ok = len(me.vertices) == nv and len(me.polygons) == nv // 4 and len(capas) == len(CAPAS)
    peor_uv = 0.0
    k_uv = {}
    for li, loop in enumerate(me.loops):
        v = loop.vertex_index
        for c, nom in zip(capas, CAPAS):
            u, w = me.uv_layers[c].data[li].uv
            peor_uv = max(peor_uv, abs(u - enc[nom][v, 0]), abs(w - enc[nom][v, 1]))
            if nom == "UV0":
                k_uv[v] = u
    esc = ob.matrix_world.to_scale()[0]
    co = np.array([vv.co[:] for vv in me.vertices]) * esc
    ue = np.stack([co[:, 0], -co[:, 1], co[:, 2]], 1) * 100.0
    k = np.array([k_uv[i] for i in range(nv)])
    cx, cy = am.corner_xy(k)
    P0 = ue - np.stack([np.zeros(nv), (2 * cx - 1) * am.K["Corner"], (2 * cy - 1) * am.K["Corner"]], 1)
    idx = np.arange(nv) // 4
    peor_p = float(np.abs(P0 - sd["P0"][idx]).max())
    grp = P0.reshape(-1, 4, 3)
    disp = float(np.abs(grp - grp[:, :1, :]).max())
    r = np.linalg.norm(grp[:, 0, :], axis=1)
    ok = ok and peor_uv < 1e-6 and peor_p < 1e-3 and disp < 1e-3
    print("VERIF verts=%d polys=%d capasUV=%s |UV - codificada| max=%.2e |centro - semilla| max=%.2e  |4 esquinas| %.1e"
          "  radio %.1f..%.1f -> %s" % (len(me.vertices), len(me.polygons), capas, peor_uv, peor_p, disp, r.min(), r.max(),
                                       "OK" if ok else "FALLA"))


def main():
    carpeta = os.path.abspath(os.path.join(AQUI, "..", "..", "..", "..", "VR_Test", "Saved", "ClaudeScripts", "Heart"))
    os.makedirs(carpeta, exist_ok=True)
    sd = am.seeds()
    enc = am.encode(sd)
    limpiar()
    ob = nube("SM_HeartDust_SC", enc)
    ruta = exportar(ob, carpeta)
    print("LISTO %s verts=%d polys=%d -> %s" % (ob.name, len(ob.data.vertices), len(ob.data.polygons), ruta))
    verificar(ruta, enc, sd)


if __name__ == "__main__":
    main()
