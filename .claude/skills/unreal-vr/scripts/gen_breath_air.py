# -*- coding: utf-8 -*-
"""gen_breath_air.py - genera SM_BreathAir_SC, la malla del ALIENTO VISIBLE (Entering, 2026-09-28).

QUE ES. Una nube de N quads diminutos (la receta de SM_LovingDust_SC, gotcha 477): cada quad es una mota y lleva en
sus UV sus numeros al azar; el vertex shader (scripts/hlsl/BreathAirVS.hlsl) REEMPLAZA la posicion. Las semillas
salen de breath_air_model.seeds() y se escriben con breath_air_model.encode_uv() (las mismas funciones que usan el
modelo y el verificador), INVARIANTES a la V invertida del importador FBX de Unreal (gotcha 302):
  UV0 = esquina del quad (0/1, 0/1)                  (simetrica: la V invertida da la otra esquina, el punto es igual)
  UV1 = (e, u)            desfase en la cinta (estratificado por corriente; en U), profundidad (uniforme; en V)
  UV2 = (a, (b + 1) / 2)  punto en el disco unitario; el VS decodifica b = 2 v - 1 (la V invertida da -b: disco igual)
  UV3 = (c, ph)           corriente (0 = inhalar, 1 = exhalar; en U), fase de la turbulencia (uniforme; en V)
Orden: primero las 768 de inhalar, despues las 1280 de exhalar (los [branch] del VS casi no divergen).
Quads REALES de 0,4 cm (degenerados los borra el importador). La posicion de cada quad solo sirve para los BOUNDS:
se reparten en una caja que cubre todo lo que el VS puede dibujar alrededor de la camara (X -40..170, Y -150..150,
Z -130..60 cm, en local de la camara), asi el componente no se recorta aunque el marco con retardo quede atras.

CONVENCION (la de gen_loving_canvases.py): 1 unidad de Blender = 100 uu; un punto UE (x, y, z) va a Blender como
(x, -y, z)/100 (mano derecha); export FBX con apply_unit_scale.

Uso (headless, no toca la sesion de Blender del usuario):
  "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" --background --factory-startup --python gen_breath_air.py
Salida: VR_Test/Saved/ClaudeScripts/aliento/SM_BreathAir_SC.fbx + verificacion por reimportacion (imprime VERIF).
"""
import os
import sys

import bpy

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import breath_air_model as am  # noqa: E402

CAJA = ((-40.0, 170.0), (-150.0, 150.0), (-130.0, 60.0))   # cm, local de la camara (ejes UE)
H = 0.2                                                   # cm: medio lado del quad (real, minusculo)


def limpiar():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def nube(nombre, sd):
    import numpy as np
    n = sd["e"].shape[0]
    rng = np.random.default_rng(4)
    base = np.stack([rng.uniform(lo, hi, n) for lo, hi in CAJA], axis=1)
    base[:2] = [[CAJA[0][0], CAJA[1][0], CAJA[2][0]], [CAJA[0][1], CAJA[1][1], CAJA[2][1]]]   # esquinas: bounds exactos
    enc = am.encode_uv(sd)
    verts, faces, uv = [], [], {k: [] for k in ("UV0", "UV1", "UV2", "UV3")}
    for k in range(n):
        x, y, z = base[k]
        b0 = len(verts)
        for cx, cz in ((0, 0), (1, 0), (1, 1), (0, 1)):
            ue = (x, y + (2 * cx - 1) * H, z + (2 * cz - 1) * H)          # quad en el plano YZ (mira a +X)
            verts.append((ue[0] / 100.0, -ue[1] / 100.0, ue[2] / 100.0))
            uv["UV0"].append((float(cx), float(cz)))
            for c in ("UV1", "UV2", "UV3"):
                uv[c].append((float(enc[c][k, 0]), float(enc[c][k, 1])))
        faces.append((b0, b0 + 1, b0 + 2, b0 + 3))
    me = bpy.data.meshes.new(nombre)
    me.from_pydata(verts, [], faces)
    me.validate()
    for nom in ("UV0", "UV1", "UV2", "UV3"):
        lay = me.uv_layers.new(name=nom)
        for li, loop in enumerate(me.loops):
            lay.data[li].uv = uv[nom][loop.vertex_index]
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


def verificar(ruta, sd):
    """Reimporta el FBX y compara cantidades, capas de UV y una muestra de valores contra las semillas CODIFICADAS.
    (Blender no invierte la V al importar: esto verifica lo que se escribio; la inversion de Unreal la cubre la
    codificacion invariante, probada en hlsl/BreathAir_check.py seccion 6.)"""
    import numpy as np
    enc = am.encode_uv(sd)
    limpiar()
    bpy.ops.import_scene.fbx(filepath=ruta)
    ob = [o for o in bpy.data.objects if o.type == 'MESH'][0]
    me = ob.data
    n = sd["e"].shape[0]
    capas = [l.name for l in me.uv_layers]
    ok = len(me.vertices) == 4 * n and len(me.polygons) == n and len(capas) == 4
    peor = 0.0
    for li, loop in enumerate(me.loops):
        if li % 97:
            continue
        k = loop.vertex_index // 4
        ref = [tuple(enc[c][k]) for c in ("UV1", "UV2", "UV3")]
        for c, (ru, rv) in zip(capas[1:], ref):
            u, v = me.uv_layers[c].data[li].uv
            peor = max(peor, abs(u - ru), abs(v - rv))
    co = np.array([v.co[:] for v in me.vertices]) * ob.matrix_world.to_scale()[0]
    print("VERIF verts=%d polys=%d capasUV=%s  |UV - semilla| max=%.2e  bbox Blender min=%s max=%s  -> %s"
          % (len(me.vertices), len(me.polygons), capas, peor, np.round(co.min(0), 3), np.round(co.max(0), 3),
             "OK" if ok and peor < 1e-6 else "FALLA"))


def main():
    carpeta = os.path.abspath(os.path.join(AQUI, "..", "..", "..", "..", "VR_Test", "Saved", "ClaudeScripts", "aliento"))
    os.makedirs(carpeta, exist_ok=True)
    sd = am.seeds()
    limpiar()
    ob = nube("SM_BreathAir_SC", sd)
    ruta = exportar(ob, carpeta)
    print("LISTO %s verts=%d polys=%d (inhalar %d, exhalar %d) -> %s"
          % (ob.name, len(ob.data.vertices), len(ob.data.polygons), sd["n_in"], sd["n_out"], ruta))
    verificar(ruta, sd)


if __name__ == "__main__":
    main()
