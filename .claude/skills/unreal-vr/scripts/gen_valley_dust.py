# -*- coding: utf-8 -*-
"""gen_valley_dust.py - genera SM_ValleyDust_SC, la malla del POLVO SUSPENDIDO de la capa de vida (Entering, 2026-09-28).

QUE ES. La nube de polvo: 2048 quads diminutos (la receta de SM_LovingDust_SC y del aliento, gotcha 477), CADA UNO EN
SU LUGAR (espacio del actor BP_ValleyLife_SC = los ojos del usuario sentado): 1536 motas de base (1,3 m - 36 m, log-
uniforme) y 512 de rafaga (1,5 - 36 m, cerca del piso: solo se ven cuando pasa el frente). El vertex shader
(scripts/hlsl/DustVS.hlsl) les suma el meandro y el remolino y decide alfa y tamano. Las semillas salen de
vida_model.seeds() y se escriben con vida_model.encode() (las mismas funciones que usan el modelo y el verificador),
INVARIANTES a la V invertida del importador FBX (gotcha 302) y a las UV en fp16:
  posicion = centro de la mota + esquina (0, +-0,2, +-0,2) cm      el VS resta la esquina (la saca de la U de UV0)
  UV0 = (esquina k 0..3, 0.5)   UV1 = (n 0..1023, ph1)   UV2 = (bits 0..3, ph2)   UV3 = (b, ph3)
Orden de las esquinas: k = 0 (-,-), 1 (+,-), 2 (+,+), 3 (-,+) en (Y, Z) -> un quad real en el plano YZ (mira a +X).

CONVENCION (la de gen_breath_air.py): 1 unidad de Blender = 100 uu; un punto UE (x, y, z) va a Blender como
(x, -y, z)/100 (mano derecha); export FBX con apply_unit_scale.

Uso (headless, no toca la sesion de Blender del usuario):
  "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" --background --factory-startup --python gen_valley_dust.py
Salida: VR_Test/Saved/ClaudeScripts/vida/SM_ValleyDust_SC.fbx + verificacion por reimportacion (imprime VERIF).
"""
import os
import sys

import bpy

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import vida_model as vm  # noqa: E402


def limpiar():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def nube(nombre, enc):
    nv = enc["LP"].shape[0]
    verts = [(p[0] / 100.0, -p[1] / 100.0, p[2] / 100.0) for p in enc["LP"]]
    faces = [(4 * i, 4 * i + 1, 4 * i + 2, 4 * i + 3) for i in range(nv // 4)]
    me = bpy.data.meshes.new(nombre)
    me.from_pydata(verts, [], faces)
    me.validate()
    for nom in ("UV0", "UV1", "UV2", "UV3"):
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
    """Reimporta el FBX y compara cantidades, capas de UV, valores (contra la codificacion) y posiciones: el centro de
    cada mota que va a recuperar el VS (posicion - esquina) = la semilla, dentro de 1e-3 cm."""
    import numpy as np
    limpiar()
    bpy.ops.import_scene.fbx(filepath=ruta)
    ob = [o for o in bpy.data.objects if o.type == 'MESH'][0]
    me = ob.data
    nv = enc["LP"].shape[0]
    capas = [l.name for l in me.uv_layers]
    ok = len(me.vertices) == nv and len(me.polygons) == nv // 4 and len(capas) == 4
    peor_uv = 0.0
    k_uv = {}
    for li, loop in enumerate(me.loops):
        v = loop.vertex_index
        for c, nom in zip(capas, ("UV0", "UV1", "UV2", "UV3")):
            u, w = me.uv_layers[c].data[li].uv
            peor_uv = max(peor_uv, abs(u - enc[nom][v, 0]), abs(w - enc[nom][v, 1]))
            if nom == "UV0":
                k_uv[v] = u
    esc = ob.matrix_world.to_scale()[0]
    co = np.array([vv.co[:] for vv in me.vertices]) * esc
    ue = np.stack([co[:, 0], -co[:, 1], co[:, 2]], 1) * 100.0
    k = np.array([k_uv[i] for i in range(nv)])
    cx, cy = vm.corner_xy(k)
    P0 = ue - np.stack([np.zeros(nv), (2 * cx - 1) * vm.K["Corner"], (2 * cy - 1) * vm.K["Corner"]], 1)
    idx = np.arange(nv) // 4
    peor_p = float(np.abs(P0 - sd["P0"][idx]).max())
    # los 4 vertices de un quad recuperan el MISMO centro
    grp = P0.reshape(-1, 4, 3)
    disp = float(np.abs(grp - grp[:, :1, :]).max())
    lo, hi = ue.min(0), ue.max(0)
    ok = ok and peor_uv < 1e-6 and peor_p < 1e-3 and disp < 1e-3
    print("VERIF verts=%d polys=%d capasUV=%s |UV - codificada| max=%.2e |centro - semilla| max=%.2e cm  |4 esquinas| %.1e cm"
          "  caja UE min=%s max=%s -> %s" % (len(me.vertices), len(me.polygons), capas, peor_uv, peor_p, disp,
                                              np.round(lo, 1), np.round(hi, 1), "OK" if ok else "FALLA"))


def main():
    carpeta = os.path.abspath(os.path.join(AQUI, "..", "..", "..", "..", "VR_Test", "Saved", "ClaudeScripts", "vida"))
    os.makedirs(carpeta, exist_ok=True)
    sd = vm.seeds()
    enc = vm.encode(sd)
    limpiar()
    ob = nube("SM_ValleyDust_SC", enc)
    ruta = exportar(ob, carpeta)
    print("LISTO %s verts=%d polys=%d (base %d, rafaga %d) -> %s"
          % (ob.name, len(ob.data.vertices), len(ob.data.polygons), sd["n_base"], sd["n_gust"], ruta))
    verificar(ruta, enc, sd)


if __name__ == "__main__":
    main()
