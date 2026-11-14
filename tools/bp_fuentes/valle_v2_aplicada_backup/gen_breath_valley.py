# -*- coding: utf-8 -*-
"""gen_breath_valley.py - genera SM_BreathValley_SC: el lienzo del valle de la respiracion (Entering). v2.

QUE ES. Un disco PLANO (z = 0, normales +Z) en malla POLAR, centrado en el USUARIO (el origen), de 640 m de
radio. No tiene forma propia: todo el relieve (el oleaje, las colinas medias, el anillo y las colinas lejanas)
lo pone el VERTEX SHADER de M_BreathValley_SC.
Especificacion: docs/PLAN-VALLE-ENTERING-2026-09-27.md, seccion 2 (esta es su implementacion).
Patron copiado de gen_heart_membrane.py (que NO se toca).

LOS ANILLOS, EN CUATRO ZONAS (v2):
  A. Uniforme, el piso quieto (z = 0 exacto): un anillo cada DELTA_A = 60 cm hasta R_A = 10,8 m. Es plano:
     la densidad aqui no cambia la imagen (la sombra y la distancia se calculan por pixel), solo evita
     triangulos enormes bajo los pies.
  B. Geometrica de celdas CUADRADAS (q = 1 + 2 pi/S) hasta R_B = 60 m: el oleaje entra y el tamano angular de
     cada celda visto desde el usuario es constante (LOD continuo, como en Heart).
  C. Geometrica con ASPECTO 0,6 (celdas 40 % mas CORTAS en radio que en arco; q = 1 + 0,6 * 2 pi/S) hasta
     R_BACK = 590 m: las colinas y el horizonte. La mirada es radial: el error de la silueta lo pone el paso
     RADIAL (la cresta de una loma o de una ola cae entre dos anillos), no el numero de sectores. Medido
     (triangulos reales contra la funcion continua, px del Quest a 25 px/grado): S 160 aspecto 1,25 da p99
     8,6 px con el oleaje; S 144 aspecto 0,6 da p99 3,2 px y un temblor de facetas p99 0,9 px/s.
     El siguiente anillo geometrico que caeria a menos de medio paso de R_BACK no se agrega: se cierra en R_BACK
     (sin anillos astilla).
  D. Detras de la cresta: 4 anillos parejos hasta R_MAX = 640 m. Ahi el terreno vale 0 y queda oculto.

TOPOLOGIA (identica a la del prototipo three.js; ver la especificacion):
  - Vertice 0 = centro. Vertice 1 + i*S + s = anillo i, sector s, en (r_i cos(2 pi s/S), r_i sin(2 pi s/S), 0).
  - Abanico central (0, idx(0,s), idx(0,s+1)).
  - Entre anillos, DOS TRIANGULOS EXPLICITOS (a,b,c) y (a,c,d), con a = idx(i,s), b = idx(i+1,s),
    c = idx(i+1,s+1), d = idx(i,s+1): la diagonal queda fija y es la misma en todas las implementaciones.
  - Vistos desde +Z giran antihorario: normal +Z. El material es two-sided de todas formas.

UNIDADES. Se construye en METROS; el export FBX con apply_unit_scale lo lleva a cm en Unreal
(640 m -> 64000 uu). OJO: con FBX_SCALE_NONE la geometria del archivo queda en +-640 y el x100 (y el giro
Z-up -> Y-up) viaja en el transform del nodo Model (Lcl Scaling = 100); el importador de Unreal lo hornea en
los vertices. Este script relee el FBX exportado y verifica unidad, escala del nodo, radio efectivo y cantidad
de vertices y triangulos antes del LISTO.

LIMITES (BOUNDS). La malla es plana: el asset necesita PositiveBoundsExtension/NegativeBoundsExtension en Z
(BoundsScale no sirve, gotcha 134). Este script mide con el modelo de referencia (valley_model.py, defaults de la
seccion 7.1) el maximo y el minimo de h en los vertices durante 30 min, calcula la cota analitica con los defaults y
con el tope de los rangos sugeridos de la 7.1, e imprime la extension recomendada (la que cubre los rangos).

REVISION 2026-09-28: la geometria de la malla NO cambio (mismos 150 anillos). Cambio el material (el oleaje mueve la
geometria solo en la capa lejana) y, por eso, la linea BOUNDS.

UVs: planares (u = x/(2 R_MAX) + 0.5, v = y/(2 R_MAX) + 0.5), sin costura. El material no las usa.

Uso (headless, no toca la sesion de Blender del usuario):
  "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" --background --factory-startup --python gen_breath_valley.py
Salida: <carpeta del script>/../../../../VR_Test/Saved/ClaudeScripts/SM_BreathValley_SC.fbx
Imprime: LISTO SM_BreathValley_SC  anillos=...  verts=...  tris=...  y la linea BOUNDS.
"""
import math
import os
import sys

import bpy

SECTORES = 144          # divisiones alrededor (el error de silueta lo manda el paso RADIAL, no este)
DELTA_A = 0.60          # m - paso de la zona uniforme (piso quieto)
R_A = 10.8              # m - fin de la zona uniforme (18 anillos)
R_B = 60.0              # m - fin de las celdas cuadradas
ASPECTO_C = 0.6         # celdas de la zona C: radio = 0,6 x arco (anillos DENSOS: la cresta del oleaje cae entre anillos)
R_BACK = 590.0          # m - FarBack por defecto: detras, todo vale 0
N_ATRAS = 4             # anillos detras de la cresta
R_MAX = 640.0           # m - borde (regla: FarBack <= R_MAX - 5 m)
NOMBRE = "SM_BreathValley_SC"

# Lo que la especificacion dice que tiene que salir (seccion 2 y seccion 12).
ESPERADO_ANILLOS = 150
ESPERADO_VERTS = 21601
ESPERADO_TRIS = 43056


def limpiar_escena():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def radios():
    """Radios de los anillos en metros, exactamente como el pseudocodigo de la seccion 2."""
    n_a = int(round(R_A / DELTA_A))
    rs = [DELTA_A * j for j in range(1, n_a + 1)]
    q_b = 1.0 + 2.0 * math.pi / SECTORES
    q_c = 1.0 + ASPECTO_C * 2.0 * math.pi / SECTORES
    r = rs[-1]
    while True:
        q = q_b if r < R_B else q_c
        r_nuevo = r * q
        if r_nuevo >= R_BACK - 0.5 * (r_nuevo - r):   # el siguiente caeria en (o a menos de medio paso de) R_BACK
            break
        r = r_nuevo
        rs.append(r)
    rs.append(R_BACK)
    for j in range(1, N_ATRAS + 1):
        rs.append(R_BACK + (R_MAX - R_BACK) * j / N_ATRAS)
    return rs, n_a


def construir():
    rs, n_a = radios()
    verts = [(0.0, 0.0, 0.0)]                   # 0 = centro
    for r in rs:
        for s in range(SECTORES):
            a = 2.0 * math.pi * s / SECTORES
            verts.append((r * math.cos(a), r * math.sin(a), 0.0))

    def idx(i, s):                              # i = anillo, s = sector (modulo S)
        return 1 + i * SECTORES + (s % SECTORES)

    faces = []
    for s in range(SECTORES):                   # abanico central
        faces.append((0, idx(0, s), idx(0, s + 1)))
    for i in range(len(rs) - 1):                # dos triangulos explicitos por celda
        for s in range(SECTORES):
            a = idx(i, s)
            b = idx(i + 1, s)
            c = idx(i + 1, s + 1)
            d = idx(i, s + 1)
            faces.append((a, b, c))
            faces.append((a, c, d))

    me = bpy.data.meshes.new(NOMBRE)
    me.from_pydata(verts, [], faces)
    me.validate()

    # Normales suaves (+Z). En 5.x use_smooth por poligono puede no existir: shade_smooth() si.
    try:
        me.shade_smooth()
    except AttributeError:
        me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))

    # UV0 planar, sin costura.
    uv = me.uv_layers.new(name="UV0")
    n_loops = len(me.loops)
    vidx = [0] * n_loops
    me.loops.foreach_get("vertex_index", vidx)
    uvs = [0.0] * (2 * n_loops)
    for li, vi in enumerate(vidx):
        x, y, _ = verts[vi]
        uvs[2 * li] = x / (2.0 * R_MAX) + 0.5
        uvs[2 * li + 1] = y / (2.0 * R_MAX) + 0.5
    uv.data.foreach_set("uv", uvs)

    ob = bpy.data.objects.new(NOMBRE, me)
    bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    # Control: todas las caras tienen que mirar a +Z (el armado es antihorario visto desde arriba).
    n_up = sum(1 for p in me.polygons if p.normal.z > 0.0)
    if n_up < len(me.polygons) // 2:
        for p in me.polygons:
            p.flip()
        me.update()
    return ob, rs, n_a


def exportar(ob):
    aqui = os.path.dirname(os.path.abspath(__file__))
    destino_dir = os.path.abspath(os.path.join(
        aqui, "..", "..", "..", "..", "VR_Test", "Saved", "ClaudeScripts"))
    os.makedirs(destino_dir, exist_ok=True)
    ruta = os.path.join(destino_dir, NOMBRE + ".fbx")
    bpy.ops.export_scene.fbx(               # mismas opciones que gen_heart_membrane.py
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


def verificar_fbx(ruta):
    """Relee el FBX binario con el parser del propio exportador de Blender y devuelve lo que
    Unreal va a ver: factor de unidad, cantidad de vertices y triangulos, y el alcance por eje
    en unidades del archivo (cm con UnitScaleFactor = 1)."""
    try:
        from io_scene_fbx import parse_fbx
    except Exception as ex:                      # noqa: BLE001 - diagnostico, no debe romper el export
        return {"error": "sin parse_fbx: %r" % (ex,)}
    raiz, version = parse_fbx.parse(ruta)

    def hijos(elem, clave):
        return [e for e in elem.elems if e.id == clave]

    info = {"version": version}
    for gs in hijos(raiz, b"GlobalSettings"):
        for p70 in hijos(gs, b"Properties70"):
            for p in hijos(p70, b"P"):
                if p.props and p.props[0] in (b"UnitScaleFactor", b"OriginalUnitScaleFactor"):
                    info[p.props[0].decode()] = p.props[-1]
    for objs in hijos(raiz, b"Objects"):
        for mod in hijos(objs, b"Model"):
            for p70 in hijos(mod, b"Properties70"):
                for p in hijos(p70, b"P"):
                    if p.props and p.props[0] in (b"Lcl Scaling", b"Lcl Rotation", b"Lcl Translation"):
                        info[p.props[0].decode()] = tuple(round(float(c), 6) for c in p.props[-3:])
        for geo in hijos(objs, b"Geometry"):
            for v in hijos(geo, b"Vertices"):
                arr = list(v.props[0])
                xs, ys, zs = arr[0::3], arr[1::3], arr[2::3]
                info["verts"] = len(arr) // 3
                info["alcance"] = tuple((min(c), max(c)) for c in (xs, ys, zs))
            for pv in hijos(geo, b"PolygonVertexIndex"):
                arr = list(pv.props[0])
                n_pol = sum(1 for k in arr if k < 0)
                info["poligonos"] = n_pol
                info["indices"] = len(arr)
    return info


def bounds_necesarios(rs):
    """Max y min de h EN LOS VERTICES (lo que el GPU dibuja) con los defaults de la 7.1, cada 2 s durante 30 min, la
    cota ANALITICA con los defaults y con el tope de los rangos sugeridos, y la extension recomendada. Todo en cm."""
    aqui = os.path.dirname(os.path.abspath(__file__))
    if aqui not in sys.path:
        sys.path.insert(0, aqui)
    import numpy as np
    import valley_model as vm
    a = 2.0 * np.pi * np.arange(SECTORES) / SECTORES
    r = np.array(rs) * 100.0
    X = (r[:, None] * np.cos(a)[None, :]).ravel()
    Y = (r[:, None] * np.sin(a)[None, :]).ravel()
    hmax, hmin = 0.0, 0.0
    for t in np.arange(0.0, 1800.1, 2.0):
        h = vm.valley_h(X, Y, t)
        hmax, hmin = max(hmax, float(h.max())), min(hmin, float(h.min()))

    # cota ANALITICA, conservadora (las 4 olas alineadas, las dunas en su tope, el retiro sin descontar):
    # h <= max(HillAmp, FarBase + FarAmp + SwellAmp * FarBack / SwellFar) y h >= -SwellAmp * FarBack / SwellFar
    # (sin descontar el anillo). La amplitud del oleaje sigue creciendo con r detras de la cresta, por eso FarBack.
    def cota(q):
        amax = q["SwellAmp"] * q["FarBack"] / q["SwellFar"]
        return max(q["HillAmp"], q["FarBase"] + q["FarAmp"] + amax), amax
    pos_d, neg_d = cota(vm.P)
    # tope de los rangos sugeridos de la 7.1 (HillAmp 4000, FarBase 5000, FarAmp 8000, FarBack 63500) con la regla de
    # confort del oleaje (SwellAmp / SwellFar <= 0,047 con SwellSpeed 1)
    pos_r, neg_r = cota(vm.params(HillAmp=4000.0, FarBase=5000.0, FarAmp=8000.0, FarBack=63500.0,
                                  SwellAmp=0.047 * vm.P["SwellFar"]))
    pos = 1000.0 * math.ceil(1.15 * pos_r / 1000.0)
    neg = 1000.0 * math.ceil(1.15 * neg_r / 1000.0)
    return hmax, hmin, pos_d, neg_d, pos_r, neg_r, pos, neg


def main():
    limpiar_escena()
    ob, rs, n_a = construir()
    ruta = exportar(ob)
    me = ob.data
    n_tris = sum(len(p.vertices) - 2 for p in me.polygons)
    up = sum(1 for p in me.polygons if p.normal.z > 0.0)

    rs_cm = [r * 100.0 for r in rs]
    n_b = sum(1 for r in rs if R_A < r < R_B)
    n_c = sum(1 for r in rs if R_B <= r < R_BACK)
    hasta = {m: sum(1 for r in rs if r <= m + 1e-9) for m in (15.0, 60.0, 150.0, 300.0, 590.0)}
    print("RADIOS  zona A uniformes=%d (%.0f..%.0f cm)  zona B cuadradas=%d  zona C aspecto %.2f=%d  R_BACK + %d atras"
          % (n_a, rs_cm[0], rs_cm[n_a - 1], n_b, ASPECTO_C, n_c, N_ATRAS))
    print("RADIOS  primer geometrico=%.2f cm  ultimos=%s cm"
          % (rs_cm[n_a], ", ".join("%.1f" % r for r in rs_cm[-7:])))
    print("RADIOS  anillos hasta 15 m=%d  60 m=%d  150 m=%d  300 m=%d  590 m=%d"
          % tuple(hasta[m] for m in (15.0, 60.0, 150.0, 300.0, 590.0)))
    pasos = [rs[i + 1] - rs[i] for i in range(len(rs) - 1)]
    print("RADIOS  paso radial: min %.2f m, a 100 m %.2f m, a 470 m %.2f m, max %.2f m; arco por sector a 470 m %.2f m"
          % (min(pasos), min((abs(rs[i] - 100.0), pasos[i]) for i in range(len(pasos)))[1],
             min((abs(rs[i] - 470.0), pasos[i]) for i in range(len(pasos)))[1], max(pasos),
             2.0 * math.pi * 470.0 / SECTORES))

    info = verificar_fbx(ruta)
    print("FBX     %s" % (info,))

    ok = (len(rs) == ESPERADO_ANILLOS and len(me.vertices) == ESPERADO_VERTS
          and n_tris == ESPERADO_TRIS and up == len(me.polygons))
    if "verts" in info:
        ok = ok and info["verts"] == ESPERADO_VERTS and info.get("poligonos") == ESPERADO_TRIS
        esc = info.get("Lcl Scaling", (1.0, 1.0, 1.0))
        unidad = float(info.get("UnitScaleFactor", 1.0))
        r_geo = max(abs(c) for par in info["alcance"] for c in par)
        r_cm = r_geo * max(abs(e) for e in esc) * unidad
        print("FBX     radio efectivo en Unreal = %.1f cm  (geometria %.3f x Lcl Scaling %s x UnitScaleFactor %.3g)"
              % (r_cm, r_geo, esc, unidad))
        ok = ok and abs(r_cm - R_MAX * 100.0) < 0.5
    try:
        hmax, hmin, pos_d, neg_d, pos_r, neg_r, pos, neg = bounds_necesarios(rs)
        print("BOUNDS  h en los vertices (defaults, 30 min): max %.0f cm, min %.0f cm | cota analitica: defaults "
              "+%.0f / -%.0f cm, tope de los rangos sugeridos +%.0f / -%.0f cm  ->  (rangos + 15 %%) "
              "PositiveBoundsExtension = (0, 0, %.0f)  NegativeBoundsExtension = (0, 0, %.0f)"
              % (hmax, hmin, pos_d, neg_d, pos_r, neg_r, pos, neg))
    except Exception as ex:  # noqa: BLE001 - informativo
        print("BOUNDS  no se pudo calcular: %r" % (ex,))
    estado = "LISTO" if ok else "REVISAR (no coincide con la especificacion)"
    print("%s %s  anillos=%d  verts=%d  tris=%d  caras_arriba=%d/%d  ->  %s"
          % (estado, NOMBRE, len(rs), len(me.vertices), n_tris, up, len(me.polygons), ruta))


if __name__ == "__main__":
    main()
