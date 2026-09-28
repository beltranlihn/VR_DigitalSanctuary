# -*- coding: utf-8 -*-
"""gen_loving_canvases.py - genera los 4 lienzos de la celula de Loving (BP_LovingCell_SC).

QUE SON. Mallas SIN forma propia, igual que SM_BlobTube_SC: toda la forma la pone el
VERTEX SHADER (World Position Offset) proyectando cada vertice sobre el campo smin que
el Blueprint empuja por parametros. La malla solo aporta DIRECCIONES y DENSIDAD.

  SM_LovingCentre_SC  icoesfera densa (~10k verts), radio 50 uu. El nucleo opaco: forma
                      cerrada (radio modulado por direccion), sin biseccion. Densa porque la
                      normal se calcula POR VERTICE (no por pixel: el nucleo es grande en
                      pantalla y el pixel shader tiene que ser barato).
  SM_LovingIco_SC     icoesfera (~2.5k verts), radio 50 uu. Un racimo de 2-4 bolas fundidas:
                      biseccion radial desde el centroide (la union es estrellada si cada bola
                      contiene al centroide).
  SM_LovingLimb_SC    tubo abierto a lo largo de Y en [-100, 100] uu, 104 anillos x 36 lados.
                      Un brazo de membrana: hebra + envoltura del grupo en UN solo lienzo.
  SM_LovingWeb_SC     tubo abierto, 64 anillos x 28 lados. Puente entre dos grupos vecinos.
  SM_LovingDust_SC    NUBE DE PUNTOS (2026-09-28): N quads diminutos, cada uno una particula de la
                      "segunda membrana". La posicion de la malla NO importa (el vertex shader la
                      reemplaza): cada quad lleva en sus UV sus numeros al azar. UV0 = esquina
                      (0/1, sprite) · UV1 = (a, b) direccion en la esfera · UV2 = (sel, e) a que
                      parte de la celula va (nucleo / envoltura / hebra) y fase/tamano.
                      Quads de 0,4 uu reales (no degenerados: el importador los borraria).
                      Solo la nube:  blender --background --python gen_loving_canvases.py -- dust

CONVENCION DE ESCALA (la misma de gen_blob_tube.py): 1 unidad de Blender = 100 uu en
Unreal (export FBX con apply_unit_scale). Por eso el tubo va de -1 a 1 (= -100..100 uu) y
las icoesferas tienen radio 0.5 (= 50 uu, la convencion de SM_AlmaSphere).

TUBOS: u = a lo largo (0 en -Y, 1 en +Y), v = alrededor. La normal de cada vertice es la
direccion radial. Los extremos NO se tapan: el shader colapsa/rota los anillos.

Uso (headless, no toca la sesion de Blender del usuario):
  "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" --background --python gen_loving_canvases.py
Salida: VR_Test/Saved/ClaudeScripts/Loving/<NOMBRE>.fbx
"""
import math
import os
import random
import sys

import bpy

ICO_CENTRE_VERTS = 10242   # objetivo de vertices del nucleo
ICO_CLUSTER_VERTS = 2562   # objetivo de vertices de cada racimo


def limpiar_escena():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def icoesfera(nombre, objetivo):
    """Sube la subdivision hasta alcanzar exactamente el conteo objetivo (10*4^n + 2)."""
    for sub in range(1, 9):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=0.5, location=(0, 0, 0))
        ob = bpy.context.active_object
        n = len(ob.data.vertices)
        if n >= objetivo:
            break
        bpy.data.objects.remove(ob, do_unlink=True)
    ob.name = nombre
    ob.data.name = nombre
    for poly in ob.data.polygons:
        poly.use_smooth = True
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    # Proyeccion CUBICA y no esferica: la esferica deja triangulos de UV degenerados en los
    # polos y la costura, que al importar dan 'nearly zero tangents' -> dialogo MODAL que
    # bloquea el MCP (gotcha 303). El material no usa UV: solo tiene que ser valida.
    bpy.ops.uv.cube_project(cube_size=1.0)
    bpy.ops.object.mode_set(mode='OBJECT')
    return ob


def tubo(nombre, rings, sides):
    verts, faces, uvs = [], [], []
    for i in range(rings + 1):
        y = -1.0 + 2.0 * i / rings
        for j in range(sides):
            a = 2.0 * math.pi * j / sides
            verts.append((math.cos(a), y, math.sin(a)))

    def idx(i, j):
        return i * sides + (j % sides)

    for i in range(rings):
        for j in range(sides):
            faces.append((idx(i, j), idx(i, j + 1), idx(i + 1, j + 1), idx(i + 1, j)))
            u0, u1 = i / rings, (i + 1) / rings
            v0, v1 = j / sides, (j + 1) / sides
            uvs.extend([(u0, v0), (u0, v1), (u1, v1), (u1, v0)])

    me = bpy.data.meshes.new(nombre)
    me.from_pydata(verts, [], faces)
    me.validate()
    uv = me.uv_layers.new(name="UV0")
    for k, co in enumerate(uvs):
        uv.data[k].uv = co
    for poly in me.polygons:
        poly.use_smooth = True
    ob = bpy.data.objects.new(nombre, me)
    bpy.context.collection.objects.link(ob)
    return ob


def polvo(nombre, n, semilla=7):
    rnd = random.Random(semilla)
    verts, faces, uv0, uv1, uv2 = [], [], [], [], []
    h = 0.002   # medio lado del quad en Blender (= 0,2 uu): real pero minusculo
    for k in range(n):
        # semilla dentro de la esfera de radio 0.5 (50 uu): solo sirve para los bounds
        while True:
            x, y, z = (rnd.uniform(-0.5, 0.5) for _ in range(3))
            if x * x + y * y + z * z <= 0.25:
                break
        a = (rnd.random(), rnd.random())
        b = (rnd.random(), rnd.random())
        base = len(verts)
        for cx, cz in ((0, 0), (1, 0), (1, 1), (0, 1)):
            verts.append((x + (2 * cx - 1) * h, y, z + (2 * cz - 1) * h))
        faces.append((base, base + 1, base + 2, base + 3))
        for cx, cz in ((0, 0), (1, 0), (1, 1), (0, 1)):
            uv0.append((cx, cz))
            uv1.append(a)
            uv2.append(b)
    me = bpy.data.meshes.new(nombre)
    me.from_pydata(verts, [], faces)
    me.validate()
    for nom, data in (("UV0", uv0), ("UV1", uv1), ("UV2", uv2)):
        lay = me.uv_layers.new(name=nom)
        for i, co in enumerate(data):
            lay.data[i].uv = co
    ob = bpy.data.objects.new(nombre, me)
    bpy.context.collection.objects.link(ob)
    return ob


def exportar(ob, destino_dir):
    ruta = os.path.join(destino_dir, ob.name + ".fbx")
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.fbx(
        filepath=ruta,
        use_selection=True,
        apply_unit_scale=True,
        global_scale=1.0,
        apply_scale_options='FBX_SCALE_NONE',
        object_types={'MESH'},
        mesh_smooth_type='FACE',
        use_mesh_modifiers=True,
        add_leaf_bones=False,
        bake_anim=False,
        path_mode='STRIP',
    )
    return ruta


def main():
    aqui = os.path.dirname(os.path.abspath(__file__))
    destino_dir = os.path.abspath(os.path.join(
        aqui, "..", "..", "..", "..", "VR_Test", "Saved", "ClaudeScripts", "Loving"))
    os.makedirs(destino_dir, exist_ok=True)
    limpiar_escena()
    pedidos = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if pedidos == ["dust"]:
        obs = [polvo("SM_LovingDust_SC", 2400)]
    else:
        obs = [
            icoesfera("SM_LovingCentre_SC", ICO_CENTRE_VERTS),
            icoesfera("SM_LovingIco_SC", ICO_CLUSTER_VERTS),
            tubo("SM_LovingLimb_SC", 104, 36),
            tubo("SM_LovingWeb_SC", 64, 28),
        ]
    for ob in obs:
        ruta = exportar(ob, destino_dir)
        me = ob.data
        print("LISTO %s  verts=%d  polys=%d  ->  %s" % (ob.name, len(me.vertices), len(me.polygons), ruta))


if __name__ == "__main__":
    main()
