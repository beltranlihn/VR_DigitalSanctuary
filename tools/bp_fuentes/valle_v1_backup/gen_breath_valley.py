# -*- coding: utf-8 -*-
"""gen_breath_valley.py - genera SM_BreathValley_SC: el lienzo del valle de la respiracion (Entering).

QUE ES. Un disco PLANO (z = 0, normales +Z) en malla POLAR, centrado en el USUARIO (el origen).
No tiene forma propia: todo el relieve (el valle, las lomas tipo duna, el anillo lejano que
tapa el horizonte) lo pone el VERTEX SHADER de M_BreathValley_SC.
Especificacion: docs/PLAN-VALLE-ENTERING-2026-09-27.md, seccion 2 (esta es su implementacion).
Patron copiado de gen_heart_membrane.py (que NO se toca).

LOS ANILLOS, EN DOS ZONAS:
  1. Zona uniforme (el piso del valle, plano): un anillo cada DELTA_A = 30 cm. Es donde se
     mira hacia abajo (la sombra del metaball cae a ~4 m) y el piso tiene que verse liso.
  2. Zona geometrica (las lomas): cada radio es el anterior por q = 1 + 2*pi/SECTORES. Cada
     celda queda casi CUADRADA (triangulos "gordos", buenos para GPUs por tiles) y su tamano
     angular visto desde el usuario es constante: un LOD continuo sin LODs, como en Heart.
  La zona uniforme llega hasta donde su paso iguala al geometrico: r_A = DELTA_A / (q - 1).

TOPOLOGIA (identica a la del prototipo three.js; ver la especificacion):
  - Vertice 0 = centro. Vertice 1 + i*S + s = anillo i, sector s, en (r_i cos(2 pi s/S), r_i sin(2 pi s/S), 0).
  - Abanico central (0, idx(0,s), idx(0,s+1)).
  - Entre anillos, DOS TRIANGULOS EXPLICITOS (a,b,c) y (a,c,d), con a = idx(i,s), b = idx(i+1,s),
    c = idx(i+1,s+1), d = idx(i,s+1): la diagonal queda fija y es la misma en todas las
    implementaciones (con quads, cada importador elige la suya).
  - Vistos desde +Z giran antihorario: normal +Z. El material es two-sided de todas formas.
  - Sin faldon: detras de la cresta el terreno vale 0 y queda oculto (el borde nunca se ve).

UNIDADES. Se construye en METROS; el export FBX con apply_unit_scale lo lleva a cm en Unreal
(44 m -> 4400 uu). OJO: con FBX_SCALE_NONE la geometria del archivo queda en +-44 y el x100
(y el giro Z-up -> Y-up) viaja en el transform del nodo Model (Lcl Scaling = 100); el
importador de Unreal lo hornea en los vertices. Este script relee el FBX exportado y verifica
unidad, escala del nodo, radio efectivo y cantidad de vertices y triangulos antes del LISTO.

UVs: planares (u = x/(2 R_MAX) + 0.5, v = y/(2 R_MAX) + 0.5), sin costura. El material no las usa.

EJES. El FBX sale con los ejes por defecto (como Heart). El disco es simetrico y el shader solo
lee la posicion local, asi que el espejo de Y que hace el importador de Unreal no importa.

IMPORT EN UNREAL (especificacion, seccion 2): /Game/SoulCharger/Mechanics/Breath/Valley/SM_BreathValley_SC,
sin colision, sin UV de lightmap, sin Nanite; get_bounds -> X e Y en +-4400, 15169 vertices;
y en el ASSET: PositiveBoundsExtension = (0, 0, 2000), NegativeBoundsExtension = (0, 0, 100)
(la malla es plana: BoundsScale no sirve, gotcha 134).

Uso (headless, no toca la sesion de Blender del usuario):
  "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" --background --python gen_breath_valley.py
Salida: <carpeta del script>/../../../../VR_Test/Saved/ClaudeScripts/SM_BreathValley_SC.fbx
Imprime: LISTO SM_BreathValley_SC  anillos=79  verts=15169  tris=30144 ...
"""
import math
import os

import bpy

SECTORES = 192          # divisiones alrededor (como Heart lite: silueta sin facetas)
DELTA_A = 0.30          # m - paso de la zona uniforme (piso del valle)
R_MAX = 44.0            # m - borde; la regla del plan: ValleyX + ValleyA*RimBack <= R_MAX - 1 m
NOMBRE = "SM_BreathValley_SC"

# Lo que la especificacion dice que tiene que salir (seccion 2 y seccion 12).
ESPERADO_ANILLOS = 79
ESPERADO_VERTS = 15169
ESPERADO_TRIS = 30144


def limpiar_escena():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def radios():
    """Radios de los anillos en metros, exactamente como el pseudocodigo de la seccion 2."""
    q = 1.0 + 2.0 * math.pi / SECTORES
    r_a = DELTA_A / (q - 1.0)
    n_a = int(math.floor(r_a / DELTA_A + 1e-9))
    rs = [DELTA_A * j for j in range(1, n_a + 1)]
    r = rs[-1]
    while True:
        r *= q
        if r >= R_MAX:
            break
        rs.append(r)
    if R_MAX - rs[-1] < 0.5 * rs[-1] * (q - 1.0):
        rs[-1] = R_MAX                          # evita un anillo astilla
    else:
        rs.append(R_MAX)
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
        # Con FBX_SCALE_NONE la geometria queda en metros y el x100 (y el giro Z-up -> Y-up)
        # va en el transform del nodo Model; el importador de Unreal lo hornea en los vertices.
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


def main():
    limpiar_escena()
    ob, rs, n_a = construir()
    ruta = exportar(ob)
    me = ob.data
    n_tris = sum(len(p.vertices) - 2 for p in me.polygons)
    up = sum(1 for p in me.polygons if p.normal.z > 0.0)

    # Radios contra la especificacion (en cm, como los escribe el plan).
    rs_cm = [r * 100.0 for r in rs]
    hasta = {m: sum(1 for r in rs if r <= m + 1e-9) for m in (6.0, 10.0, 20.0, 40.0)}
    print("RADIOS  uniformes=%d (%.0f..%.0f cm)  primer_geometrico=%.2f cm  ultimos=%s cm"
          % (n_a, rs_cm[0], rs_cm[n_a - 1], rs_cm[n_a],
             ", ".join("%.1f" % r for r in rs_cm[-4:])))
    print("RADIOS  anillos hasta 6 m=%d  10 m=%d  20 m=%d  40 m=%d   (plan: 20 / 33 / 54 / 76)"
          % (hasta[6.0], hasta[10.0], hasta[20.0], hasta[40.0]))

    info = verificar_fbx(ruta)
    print("FBX     %s" % (info,))

    ok = (len(rs) == ESPERADO_ANILLOS and len(me.vertices) == ESPERADO_VERTS
          and n_tris == ESPERADO_TRIS and up == len(me.polygons))
    if "verts" in info:
        ok = ok and info["verts"] == ESPERADO_VERTS and info.get("poligonos") == ESPERADO_TRIS
        # Radio efectivo en cm (unidad del archivo x escala del nodo): tiene que dar 4400.
        esc = info.get("Lcl Scaling", (1.0, 1.0, 1.0))
        unidad = float(info.get("UnitScaleFactor", 1.0))
        r_geo = max(abs(c) for par in info["alcance"] for c in par)
        r_cm = r_geo * max(abs(e) for e in esc) * unidad
        print("FBX     radio efectivo en Unreal = %.1f cm  (geometria %.3f x Lcl Scaling %s x UnitScaleFactor %.3g)"
              % (r_cm, r_geo, esc, unidad))
        ok = ok and abs(r_cm - R_MAX * 100.0) < 0.5
    estado = "LISTO" if ok else "REVISAR (no coincide con la especificacion)"
    print("%s %s  anillos=%d  verts=%d  tris=%d  caras_arriba=%d/%d  ->  %s"
          % (estado, NOMBRE, len(rs), len(me.vertices), n_tris, up, len(me.polygons), ruta))


if __name__ == "__main__":
    main()
