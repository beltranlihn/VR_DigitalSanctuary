# -*- coding: utf-8 -*-
"""gen_draw_sea.py - genera las mallas del oceano del dibujo: SM_DrawSea_SC y SM_DrawDust_SC.
Plan: docs/PLAN-OCEANO-DIBUJO-2026-09-28.md. Base: gen_heart_membrane.py (misma receta, copiada).

SM_DrawSea_SC. Disco PLANO (z = 0, normales +Z) en malla POLAR centrada bajo los ojos. Todo el relieve lo
pone el vertex shader (DrawSeaHeightVS / DrawSeaGradVS).
  - CENTRO: anillos UNIFORMES cada 30 cm hasta 7,6 m. La ola mas corta (4,2 m) necesita ~1 vertice cada
    30 cm; mas denso no agrega forma y cuesta vertices (el latido midio que el costo esta en los VERTICES).
    El usuario esta 3,4 m sobre el agua: debajo suyo no se necesita detalle de centimetros.
  - AFUERA: espaciado GEOMETRICO r_j = R_GEO * q^j con q = 1 + 2*pi/SECTORES (celdas casi cuadradas),
    desde el radio donde el paso geometrico tambien es 30 cm (7,64 m con 160 sectores) hasta 250 m, donde
    la niebla ya es total. Sin faldon.
  - El paso de la malla a radio r es ~ 0,0393 r. El shader apaga cada oleaje donde la malla ya no lo puede
    dibujar (LodNear/LodFar ~ 4-6,5 largos de onda: >= 4 vertices por largo). Asi no titila y el corte
    por oleaje ahorra de verdad.
SM_DrawDust_SC. 1.200 quads de 1 mm (no degenerados: Unreal borra los degenerados al importar), cada uno
en su semilla * 1 m (solo para que los bounds sean una caja real). La SEMILLA va en las UV, igual en las 4
esquinas: UV1 = (x, y), UV2 = (z, w); UV0 = esquina (0..1). Semillas = el mismo generador que el prototipo.

UNIDADES: se construye en METROS; el FBX con apply_unit_scale lo lleva a cm (250 m -> 25000 uu).
Uso (headless, no toca la sesion de Blender del usuario):
  "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" --background --python gen_draw_sea.py [-- dust | -- preview]
Salida: VR_Test/Saved/ClaudeScripts/<NOMBRE>.fbx
"""
import math
import os
import sys

import bpy

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SECTORES = 160
PASO_CENTRO = 0.30            # m - separacion de los anillos uniformes del centro
R_GEO = PASO_CENTRO * SECTORES / (2.0 * math.pi)   # 7,64 m: ahi el paso geometrico tambien es 30 cm
R_MAX = 250.0                 # m
NOMBRE = "SM_DrawSea_SC"
DUST_N = 1200

if "preview" in ARGS:         # disco chico de 8 m, solo para verificar el material en la miniatura del asset
    SECTORES, PASO_CENTRO, R_MAX = 128, 0.10, 8.0
    R_GEO = PASO_CENTRO * SECTORES / (2.0 * math.pi)
    NOMBRE = "SM_DrawSeaPreview_SC"
if "dust" in ARGS:
    NOMBRE = "SM_DrawDust_SC"


def limpiar_escena():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def radios():
    rs = []
    r = PASO_CENTRO
    while r < R_GEO - 1e-6:
        rs.append(r)
        r += PASO_CENTRO
    q = 1.0 + 2.0 * math.pi / SECTORES
    r = R_GEO
    while r < R_MAX:
        rs.append(r)
        r *= q
    rs.append(R_MAX)
    return rs


def construir_mar():
    rs = radios()
    verts = [(0.0, 0.0, 0.0)]
    for r in rs:
        for s in range(SECTORES):
            a = 2.0 * math.pi * s / SECTORES
            verts.append((r * math.cos(a), r * math.sin(a), 0.0))

    def idx(i, s):
        return 1 + i * SECTORES + (s % SECTORES)

    faces = [(0, idx(0, s), idx(0, s + 1)) for s in range(SECTORES)]
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
            uv.data[li].uv = (x / (2.0 * R_MAX) + 0.5, y / (2.0 * R_MAX) + 0.5)
    return me, len(rs)


def semillas():
    s = 12345                      # el mismo LCG que el prototipo (Park-Miller)
    out = []
    for _ in range(DUST_N * 4):
        s = (s * 16807) % 2147483647
        out.append(s / 2147483647.0)
    return [tuple(out[i * 4:i * 4 + 4]) for i in range(DUST_N)]


def construir_polvo():
    verts, faces, seeds = [], [], semillas()
    h = 0.0005                     # 1 mm de lado
    for (x, y, z, w) in seeds:
        b = len(verts)
        cx, cy, cz = x, y, z       # 1 m de caja (solo bounds)
        verts += [(cx - h, cy, cz - h), (cx + h, cy, cz - h), (cx + h, cy, cz + h), (cx - h, cy, cz + h)]
        faces.append((b, b + 1, b + 2, b + 3))
    me = bpy.data.meshes.new(NOMBRE)
    me.from_pydata(verts, [], faces)
    me.validate()
    uv0 = me.uv_layers.new(name="UV0")
    uv1 = me.uv_layers.new(name="UV1")
    uv2 = me.uv_layers.new(name="UV2")
    corners = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    for fi, poly in enumerate(me.polygons):
        x, y, z, w = seeds[fi]
        for k, li in enumerate(poly.loop_indices):
            vi = me.loops[li].vertex_index - fi * 4
            uv0.data[li].uv = corners[vi]
            uv1.data[li].uv = (x, y)
            uv2.data[li].uv = (z, w)
    return me, DUST_N


def exportar(ob):
    aqui = os.path.dirname(os.path.abspath(__file__))
    destino_dir = os.path.abspath(os.path.join(aqui, "..", "..", "..", "..", "VR_Test", "Saved", "ClaudeScripts"))
    os.makedirs(destino_dir, exist_ok=True)
    ruta = os.path.join(destino_dir, NOMBRE + ".fbx")
    bpy.ops.export_scene.fbx(
        filepath=ruta, use_selection=True, apply_unit_scale=True, global_scale=1.0,
        apply_scale_options='FBX_SCALE_NONE', object_types={'MESH'}, mesh_smooth_type='FACE',
        use_mesh_modifiers=True, add_leaf_bones=False, bake_anim=False, path_mode='STRIP')
    return ruta


def main():
    limpiar_escena()
    me, n = construir_polvo() if "dust" in ARGS else construir_mar()
    ob = bpy.data.objects.new(NOMBRE, me)
    bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    if "dust" not in ARGS:
        if sum(1 for p in me.polygons if p.normal.z > 0.0) < len(me.polygons) // 2:
            for p in me.polygons:
                p.flip()
            me.update()
    ruta = exportar(ob)
    n_tris = sum(len(p.vertices) - 2 for p in me.polygons)
    up = sum(1 for p in me.polygons if p.normal.z > 0.0)
    print("LISTO %s  %s=%d  verts=%d  tris=%d  caras_arriba=%d/%d  ->  %s"
          % (NOMBRE, "motas" if "dust" in ARGS else "anillos", n, len(me.vertices), n_tris, up, len(me.polygons), ruta))


if __name__ == "__main__":
    main()
