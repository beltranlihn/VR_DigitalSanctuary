# -*- coding: utf-8 -*-
"""gen_fluid_canvases.py - lienzos del FLUIDO CEREBRAL (BP_FluidMedium_SC), 2026-09-28.

Plan: docs/PLAN-FLUIDO-CEREBRAL.md. Referencia: docs/prototipos/fluido-cerebral.html.

Reusa polvo() de gen_loving_canvases.py (la nube de quads de SM_LovingDust_SC): N quads diminutos
con sus numeros al azar en las UV. La posicion de la malla no importa (el vertex shader la
reemplaza); solo sirve para los bounds, y en Unreal cada componente lleva BoundsScale grande.
  UV0 = esquina del quad (0/1) · UV1 = (semilla x, semilla y) · UV2 = (semilla z, fase/tamano)
  La V invertida al importar (gotcha 302) no cambia nada: son numeros al azar y una esquina simetrica.

Capas (cantidades del prototipo; en Unreal se pueden BAJAR con la opacidad, no subir):
  SM_FluidMotesNear_SC  600 quads   (cubo de 3,6 m alrededor de la cabeza)
  SM_FluidMotesMid_SC   2400 quads  (cubo de 12 m)
  SM_FluidMotesFar_SC   4000 quads  (cubo de 40 m)

Uso (headless):
  "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" --background --python gen_fluid_canvases.py
  Solo una parte: ... --python gen_fluid_canvases.py -- cells   (motes | cells | light)
Salida: VR_Test/Saved/ClaudeScripts/Fluid/*.fbx
"""
import os
import sys

import bpy

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import gen_loving_canvases as glc  # noqa: E402  (main() esta protegido por __name__)

CAPAS = [("SM_FluidMotesNear_SC", 600, 37), ("SM_FluidMotesMid_SC", 2400, 23), ("SM_FluidMotesFar_SC", 4000, 11)]

# F2/F3 (2026-09-28):
#   SM_FluidFarCells_SC   64 quads (polvo, semilla 71): siluetas de celulas lejanas
#   SM_FluidMidCells_SC   16 celulas x (nucleo icoesfera 642 + 5 satelites de 42) = 13 632 vertices.
#                         La POSICION es solo la direccion (radio 0,5 = 50 uu); UV0 = proyeccion cubica
#                         (valida: tangentes sin triangulos degenerados, gotcha 303); UV1.x = celula 0-15,
#                         UV2.x = pieza (0 nucleo, 1-5 satelites). Indices en U: la V se invierte al importar.
#   SM_FluidShafts8_SC    8 tiras de 9 filas x 2 (8 quads por haz; antes SM_FluidShafts_SC con 4). UV0.x = 0/1 a lo ancho; UV1.x = a lo largo
#                         (0 arriba, 1 abajo); UV2.x = haz 0-3.
#   SM_FluidVeils_SC      6 quads. UV0 = esquina; UV1.x = velo 0-5.
# Los quads son reales (no degenerados: el importador los borraria) pero diminutos; el VS los ubica.


def _uv_const(me, nombre, valor):
    lay = me.uv_layers.new(name=nombre)
    for i in range(len(lay.data)):
        lay.data[i].uv = valor
    return lay


def _unir(obs, nombre):
    bpy.ops.object.select_all(action='DESELECT')
    for ob in obs:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]
    bpy.ops.object.join()
    ob = bpy.context.active_object
    ob.name = nombre
    ob.data.name = nombre
    return ob


def celulas_medias(nombre, n_cel=16, n_sat=5):
    obs = []
    for ci in range(n_cel):
        for pk in range(n_sat + 1):
            ob = glc.icoesfera("tmp_%d_%d" % (ci, pk), 642 if pk == 0 else 42)
            me = ob.data
            me.uv_layers[0].name = "UV0"
            _uv_const(me, "UV1", (float(ci), 0.0))
            _uv_const(me, "UV2", (float(pk), 0.0))
            obs.append(ob)
    return _unir(obs, nombre)


def tiras_haces(nombre, n_haz=4, filas=8):
    verts, faces, uv0, uv1, uv2 = [], [], [], [], []
    for h in range(n_haz):
        base = len(verts)
        for j in range(filas + 1):
            y = j / filas
            for x in (0.0, 1.0):
                verts.append(((x - 0.5) * 0.02 + h * 0.05, 0.0, -y * 0.1))
        for j in range(filas):
            a = base + 2 * j
            faces.append((a, a + 1, a + 3, a + 2))
    me = bpy.data.meshes.new(nombre)
    me.from_pydata(verts, [], faces)
    me.validate()
    lay0 = me.uv_layers.new(name="UV0")
    lay1 = me.uv_layers.new(name="UV1")
    lay2 = me.uv_layers.new(name="UV2")
    for poly in me.polygons:
        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index
            h = vi // (2 * (filas + 1))
            r = vi % (2 * (filas + 1))
            x, y = float(r % 2), (r // 2) / filas
            lay0.data[li].uv = (x, y)
            lay1.data[li].uv = (y, 0.0)
            lay2.data[li].uv = (float(h), 0.0)
    ob = bpy.data.objects.new(nombre, me)
    bpy.context.collection.objects.link(ob)
    return ob


def quads_velos(nombre, n=6):
    verts, faces, uv0, uv1 = [], [], [], []
    h = 0.01
    for k in range(n):
        base = len(verts)
        for cx, cz in ((0, 0), (1, 0), (1, 1), (0, 1)):
            verts.append((k * 0.05 + (2 * cx - 1) * h, 0.0, (2 * cz - 1) * h))
            uv0.append((float(cx), float(cz)))
            uv1.append((float(k), 0.0))
        faces.append((base, base + 1, base + 2, base + 3))
    me = bpy.data.meshes.new(nombre)
    me.from_pydata(verts, [], faces)
    me.validate()
    for nom, data in (("UV0", uv0), ("UV1", uv1)):
        lay = me.uv_layers.new(name=nom)
        for i, co in enumerate(data):
            lay.data[i].uv = co
    ob = bpy.data.objects.new(nombre, me)
    bpy.context.collection.objects.link(ob)
    return ob


def main():
    destino = os.path.abspath(os.path.join(AQUI, "..", "..", "..", "..", "VR_Test", "Saved", "ClaudeScripts", "Fluid"))
    os.makedirs(destino, exist_ok=True)
    solo = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    glc.limpiar_escena()
    obs = []
    if not solo or "motes" in solo:
        for nombre, n, semilla in CAPAS:
            obs.append(glc.polvo(nombre, n, semilla))
    if not solo or "cells" in solo:
        obs.append(glc.polvo("SM_FluidFarCells_SC", 64, 71))
        obs.append(celulas_medias("SM_FluidMidCells_SC"))
    if not solo or "light" in solo:
        obs.append(tiras_haces("SM_FluidShafts8_SC", n_haz=8))   # 2026-09-28: 8 haces (antes SM_FluidShafts_SC, 4)
        obs.append(quads_velos("SM_FluidVeils_SC"))
    for ob in obs:
        ruta = glc.exportar(ob, destino)
        me = ob.data
        print("LISTO %s  verts=%d  polys=%d  uv=%s  ->  %s" % (ob.name, len(me.vertices), len(me.polygons), [l.name for l in me.uv_layers], ruta))


if __name__ == "__main__":
    main()
