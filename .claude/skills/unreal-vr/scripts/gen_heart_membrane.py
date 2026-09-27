# -*- coding: utf-8 -*-
"""gen_heart_membrane.py - genera SM_HeartMembrane_SC: el lienzo de la membrana del latido.

QUE ES. Un disco PLANO (z = 0, normales +Z) en malla POLAR, centrado en el origen, que es
donde late la esfera central. No tiene forma propia: todo el relieve (anillos del latido,
pozo bajo la esfera, oleaje, bultos de salida) lo pone el VERTEX SHADER de
M_HeartMembrane_SC. Plan: docs/PLAN-MEMBRANA-DEL-LATIDO-2026-09-27.md.

POR QUE POLAR Y CON ESPACIADO GEOMETRICO (y no la grilla uniforme de SM_CloudPlane):
  1. Radios r_j = R_MIN * q^j con q = 1 + 2*pi/SECTORES: cada celda queda casi CUADRADA
     (su ancho radial es igual a su ancho tangencial). Son los triangulos "gordos" que Meta
     pide para GPUs por tiles, donde el vertex shader se re-ejecuta por tile.
  2. La densidad cae como 1/r, al mismo ritmo al que se ensanchan las ondas al viajar
     (Spread): cerca de la esfera hay detalle de centimetros, lejos no se gasta nada.
     Funciona como un LOD continuo sin tener LODs.
  3. El centro es exacto: el pozo y el borde de donde nace la onda son circulares de
     verdad, sin el serrucho que da una grilla cartesiana cerca del origen.

EL FALDON. Pasado R_ONDAS (donde las ondas ya se apagaron) quedan unos pocos anillos
cada vez mas espaciados hasta R_FALDON: la niebla del shader los lleva al color del
cielo, asi el borde de la malla nunca se ve.

UNIDADES. Se construye en METROS; el export FBX con apply_unit_scale lo lleva a cm en
Unreal (60 m -> 6000 uu). Verificar con StaticMeshTools.get_bounds despues de importar.

UVs: planares (u = x, v = y normalizados a R_ONDAS), sin costura. El material no las usa.

Uso (headless, no toca la sesion de Blender del usuario):
  "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" --background --python gen_heart_membrane.py
Salida: <carpeta del script>/../../../../VR_Test/Saved/ClaudeScripts/SM_HeartMembrane_SC.fbx
"""
import math
import os
import sys

import bpy

SECTORES = 256          # divisiones alrededor
R_MIN = 0.04            # m - primer anillo (queda tapado por la esfera)
R_ONDAS = 60.0          # m - hasta donde viajan las ondas con detalle
R_FALDON = (80.0, 120.0, 200.0, 350.0, 600.0)   # m - anillos de relleno para la niebla
R_CENTRO = ()           # m - anillos uniformes antes del primero geometrico (vacio = sin ellos)
NOMBRE = "SM_HeartMembrane_SC"

# "-- lite" (v3, 2026-09-27): MEDIDO en la Quest que el costo esta en los VERTICES (5,4 ms de
# 15,9). La v1 ponia el 43 % de los vertices dentro del metro central, tapado por la esfera.
# 192 sectores + 5 anillos uniformes de 6 cm hasta 30 cm + geometrico desde 36 cm: ~32k vertices.
if "--" in sys.argv and "lite" in sys.argv[sys.argv.index("--") + 1:]:
    SECTORES = 192
    R_CENTRO = (0.06, 0.12, 0.18, 0.24, 0.30)
    R_MIN = 0.36
    NOMBRE = "SM_HeartMembraneLite_SC"

# "-- preview": disco chico de 8 m sin faldon, solo para verificar el material en la
# miniatura del asset (la malla real encuadra 1,2 km y las ondas no se ven).
if "--" in sys.argv and "preview" in sys.argv[sys.argv.index("--") + 1:]:
    SECTORES = 128
    R_ONDAS = 8.0
    R_FALDON = ()
    NOMBRE = "SM_HeartMembranePreview_SC"


def limpiar_escena():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def radios():
    q = 1.0 + 2.0 * math.pi / SECTORES
    rs = list(R_CENTRO)
    r = R_MIN
    while r < R_ONDAS:
        rs.append(r)
        r *= q
    rs.append(R_ONDAS)
    rs.extend(R_FALDON)
    return rs


def construir():
    rs = radios()
    verts = [(0.0, 0.0, 0.0)]                      # 0 = centro
    for r in rs:
        for s in range(SECTORES):
            a = 2.0 * math.pi * s / SECTORES
            verts.append((r * math.cos(a), r * math.sin(a), 0.0))

    def idx(i, s):                                  # i = anillo, s = sector
        return 1 + i * SECTORES + (s % SECTORES)

    faces = []
    for s in range(SECTORES):                       # abanico central
        faces.append((0, idx(0, s), idx(0, s + 1)))
    for i in range(len(rs) - 1):
        for s in range(SECTORES):
            faces.append((idx(i, s), idx(i + 1, s), idx(i + 1, s + 1), idx(i, s + 1)))

    me = bpy.data.meshes.new(NOMBRE)
    me.from_pydata(verts, [], faces)
    me.validate()

    uv = me.uv_layers.new(name="UV0")
    for poly in me.polygons:
        poly.use_smooth = True
        for li in poly.loop_indices:
            x, y, _ = verts[me.loops[li].vertex_index]
            uv.data[li].uv = (x / (2.0 * R_ONDAS) + 0.5, y / (2.0 * R_ONDAS) + 0.5)

    # Normales hacia +Z: el abanico y los quads se armaron en sentido antihorario visto
    # desde arriba; si Blender los invirtiera, recalcular hacia afuera lo corrige.
    ob = bpy.data.objects.new(NOMBRE, me)
    bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    n_up = sum(1 for p in me.polygons if p.normal.z > 0.0)
    if n_up < len(me.polygons) // 2:
        for p in me.polygons:
            p.flip()
        me.update()
    return ob, len(rs)


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
    ob, n_anillos = construir()
    ruta = exportar(ob)
    me = ob.data
    n_tris = sum(len(p.vertices) - 2 for p in me.polygons)
    up = sum(1 for p in me.polygons if p.normal.z > 0.0)
    print("LISTO %s  anillos=%d  verts=%d  tris=%d  caras_arriba=%d/%d  ->  %s"
          % (NOMBRE, n_anillos, len(me.vertices), n_tris, up, len(me.polygons), ruta))


if __name__ == "__main__":
    main()
