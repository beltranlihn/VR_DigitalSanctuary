# -*- coding: utf-8 -*-
"""gen_blob_tube.py - genera SM_BlobTube_SC: el lienzo de desplazamiento del enfoque C.

QUE ES. Un tubo RECTO unitario (eje Y de -1 a 1, radio 1) bien teselado, sin tapas.
No tiene forma propia a proposito: es un lienzo. Toda la forma de la cadena de gotas
la pone el VERTEX SHADER de M_BlobMesh_SC a partir de los mismos C0..C7 / Rad0..2 que
el BP ya empuja hoy — el arco, el perfil de radios, la respiracion y el flotar.

POR QUE RECTO Y UNITARIO (y no siguiendo el arco, como el proxy de raymarch):
  1. La malla queda GENERICA: sirve para cualquier largo, cualquier cantidad de gotas y
     cualquier recorrido, porque el recorrido es matematica del material.
  2. El espejado en Y que mete el export FBX (RH -> LH) deja de importar: un tubo recto
     es simetrico en Y. Con el proxy hubo que razonar sobre la asimetria del arco.
  3. Una sola fuente de verdad para la forma. Si la malla tambien la definiera, habria
     dos definiciones del mismo recorrido que se pueden desincronizar.

LA DENSIDAD. Rings a lo largo tiene que resolver las CUENTAS, no el tubo: con 8 gotas
sobre el largo, ~12 anillos por gota = 96 anillos. Sides = 20 da una seccion circular
limpia. Total ~2000 vertices. Somos fill-rate bound, no geometry bound (el proyecto ya
regala 20-32k tris en otras piezas), asi que esto es ruido.

LAS PUNTAS NO SE TAPAN. El perfil de radio es sqrt(max(Rj^2 - dz^2, 0)), que llega a 0
solo mas alla de la ultima gota: el tubo se cierra por si mismo. Los anillos de los
extremos colapsan a un punto (triangulos degenerados, inofensivos) y por eso el UV.u
llega hasta el borde exacto.

UVs: u = a lo largo del eje (0 en -Y, 1 en +Y) -> es el parametro axial que el material
usa para ubicar cada anillo. v = alrededor. La NORMAL de cada vertice es la direccion
RADIAL (el tubo es recto), que es justo lo que el material necesita para empujar hacia
afuera sin recalcular nada.

Uso (headless, no necesita la sesion de Blender del usuario):
  "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" --background --python gen_blob_tube.py
Salida: <carpeta del script>/../../../../VR_Test/Saved/ClaudeScripts/SM_BlobTube_SC.fbx
"""
import math
import os
import sys

import bpy

RINGS = 96      # anillos a lo largo del eje Y
SIDES = 20      # lados de la seccion
NOMBRE = "SM_BlobTube_SC"


def limpiar_escena():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def construir():
    verts = []
    faces = []
    uvs_por_loop = []

    # Anillos: y de -1 a 1. El vertice del "cierre" NO se duplica en la malla (la costura
    # UV se resuelve al exportar); se prefiere una malla soldada para que las normales
    # radiales queden continuas alrededor.
    for i in range(RINGS + 1):
        t = i / RINGS
        y = -1.0 + 2.0 * t
        for j in range(SIDES):
            a = 2.0 * math.pi * j / SIDES
            verts.append((math.cos(a), y, math.sin(a)))

    def idx(i, j):
        return i * SIDES + (j % SIDES)

    for i in range(RINGS):
        for j in range(SIDES):
            a = idx(i, j)
            b = idx(i, j + 1)
            c = idx(i + 1, j + 1)
            d = idx(i + 1, j)
            faces.append((a, b, c, d))
            # UV por loop, en el mismo orden que los vertices de la cara
            u0 = i / RINGS
            u1 = (i + 1) / RINGS
            v0 = j / SIDES
            v1 = (j + 1) / SIDES
            uvs_por_loop.extend([(u0, v0), (u0, v1), (u1, v1), (u1, v0)])

    me = bpy.data.meshes.new(NOMBRE)
    me.from_pydata(verts, [], faces)
    me.validate()

    uv = me.uv_layers.new(name="UV0")
    for k, co in enumerate(uvs_por_loop):
        uv.data[k].uv = co

    # Sombreado suave: la normal de cada vertice queda radial, que es lo que el material
    # lee para empujar hacia afuera.
    for poly in me.polygons:
        poly.use_smooth = True

    ob = bpy.data.objects.new(NOMBRE, me)
    bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    return ob


def exportar(ob):
    aqui = os.path.dirname(os.path.abspath(__file__))
    destino_dir = os.path.abspath(os.path.join(
        aqui, "..", "..", "..", "..", "VR_Test", "Saved", "ClaudeScripts"))
    os.makedirs(destino_dir, exist_ok=True)
    ruta = os.path.join(destino_dir, NOMBRE + ".fbx")
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
    limpiar_escena()
    ob = construir()
    ruta = exportar(ob)
    me = ob.data
    print("LISTO %s  verts=%d  polys=%d  ->  %s"
          % (NOMBRE, len(me.vertices), len(me.polygons), ruta))


if __name__ == "__main__":
    main()
