# gen_results.py - EL CUADRO DE RESULTADOS del final (encargo de Narrativa 2026-09-30; propuesta aprobada por Beltran
# en la web, paso 9.4): "una version grande del HUD". Marco BISELADO + base translucida + ventanas enmarcadas (como la
# ventana del EEG del HUD) + la cajita del texto explicativo arriba. Familia del HUD (gen_hud.py): hormigon
# translucido, y ninguna lamina se mete debajo de un contorno translucido (llega a su pared).
# Medidas (m, visto a 2 m): panel 1,10 x 1,02, r 0,06 · franja del titulo y +0,4325, alto 0,095 (sin malla: es texto
# de Narrativa, va sobre la lamina) · ventanas de 1,03 de ancho, r 0,03: calma y +0,26 alto 0,21 · latido +0,03 / 0,21 ·
# respiracion -0,18 / 0,17 · melodia -0,38 / 0,19 · cajita 0,92 x 0,17, centro y +0,625 (r 0,026, la de la web).
# Piezas (cada una con SU origen, para la entrada 'luz primero' por piezas):
#   SM_ResultsRim_SC    marco biselado: labio redondeado arriba + CHAFLAN a 45 grados que baja hasta la lamina. Slot Rim
#   SM_ResultsGlass_SC  base translucida: una cara, ENTERA (llega a la pared interna del marco). Slot Glass
#   SM_ResultsWin21_SC  ventana 1,03 x 0,21 (calma Y latido: va dos veces) · SM_ResultsWin19_SC (melodia) ·
#   SM_ResultsWin17_SC  (respiracion). Slots Frame (contorno de 4 mm) + Pane (vidrio oscuro de la abertura, UV 0..1,
#                       apoyado SOBRE la lamina: la ventana = lamina + su vidrio, como en la web)
#   SM_ResultsTip_SC    la cajita del texto: marco biselado chico + su vidrio. Slots TipFrame + TipGlass
#   SM_Results_Trace_SC el trazo de luz de la entrada (M_AppearTrace_SC), sobre el labio del marco
# Ejes de CONSTRUCCION: acostado en XY, cara hacia +Z, +Y = arriba del panel (como el HUD); mm.
# Ejes de SALIDA (el panel va PARADO frente al usuario, no pegado a la cabeza como el HUD):
#   FBX (Unreal)  cara hacia +X, arriba +Z, ancho en Y (Unreal espeja Y: el panel es simetrico a lo ancho)
#   .blend / GLB  cara hacia -Y de Blender = +Z de glTF, arriba = +Y de glTF (world.js lo usa SIN rotar)
# Uso: blender --background --python gen_results.py -- [dir_salida]
import functools
import math
import os
import sys
import traceback

import bmesh
import bpy
from mathutils import Matrix, Vector

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import revolve_lib as RL   # noqa: E402
import gen_hud as H        # noqa: E402  (join, closed_rect; ojo: al importarse deja RL.rrect_outline con step 12)
import anim_luz_objects as LZ   # noqa: E402  (trace_mesh)

RR = H._RR                 # el rrect_outline original (sin partial)

# --- panel ---
A, B, RC = 550.0, 510.0, 60.0          # semiejes y radio de esquina
RIM_W, RIM_T, RIM_LIP = 11.0, 6.0, 5.0  # marco: huella 11 mm (la de la web), z -6..+6, labio de 5 + chaflan de 6 a 45
GLASS_Z = -2.5                          # la lamina corta la pared interna del marco (que baja de z 0 a -6)
# --- ventanas ---
WIN_W, WIN_RC = 1030.0, 30.0
WIN_FW = 4.0                            # contorno de la ventana (la web: 3,5): hacia ADENTRO del contorno exterior
WIN_Z0, WIN_Z1 = -2.5, 1.5              # el contorno se apoya en la lamina y asoma 4 mm
PANE_Z = -2.0                           # el vidrio de la abertura, 0,5 mm DELANTE de la lamina (los contenidos, desde -1,5)
ROWS = [("Calm", 260.0, 210.0), ("Heart", 30.0, 210.0), ("Breath", -180.0, 170.0), ("Melody", -380.0, 190.0)]
WIN_MESH = {210.0: "SM_ResultsWin21_SC", 190.0: "SM_ResultsWin19_SC", 170.0: "SM_ResultsWin17_SC"}
TITLE_Y, TITLE_H = 432.5, 95.0
# --- cajita del texto ---
TIP_W, TIP_H, TIP_RC, TIP_Y = 920.0, 170.0, 26.0, 625.0
TIP_RIM_W, TIP_T, TIP_LIP = 7.0, 4.0, 3.0
TIP_GLASS_Z = -1.5
# --- trazo ---
TRACE_HW = 16.0                         # medio ancho de la cinta (el del HUD, 6 a 55 cm, escalado a 2 m ~ 22)
ARC = math.radians(45.0)
STEP = 5000.0                           # tramos rectos SIN subdividir (el panel no se dobla: todo es afin)

R_UE = Matrix(((0.0, 0.0, 1.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0))).to_4x4()    # cara +Z -> +X, arriba +Y -> +Z
R_WEB = Matrix(((1.0, 0.0, 0.0), (0.0, 0.0, -1.0), (0.0, 1.0, 0.0))).to_4x4()  # cara +Z -> -Y, arriba +Y -> +Z

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else os.path.abspath(os.path.join(AQUI, "..", "..", "..", "..", "VR_Test", "Saved", "ClaudeScripts", "Results"))


def use_outline(n_arc):
    RL.rrect_outline = functools.partial(RR, n_arc=n_arc, step=STEP)


def bevel_profile(w, t, lip, fo, fi, part):
    """Seccion (d, h) del marco BISELADO, CCW como closed_rect: pared exterior (d 0), labio redondeado arriba (radio
    fo), chaflan a 45 hacia adentro que baja (w - lip) hasta d = -w, pared interna y dorso."""
    ch = w - lip
    P = [(-w / 2, -t, 0.0, part), (0.0, -t, 0.6, part), (0.0, t, fo, part), (-lip, t, fi, part),
         (-w, t - ch, 0.8 * fi, part), (-w, -t, 0.6, part), (-w / 2, -t, 0.0, part)]
    return RL.fillet_poly(P, ARC)[:-1]


def rr_sdf(x, y, a, b, rc):
    qx, qy = abs(x) - (a - rc), abs(y) - (b - rc)
    return math.hypot(max(qx, 0.0), max(qy, 0.0)) + min(max(qx, qy), 0.0) - rc


def rr_fill(name, a, b, rc, d, z, n_arc=8):
    """Cara plana hacia +Z que llena el rectangulo redondeado (a, b, rc) desplazado d; UV 0..1 sobre la cara."""
    pts = [(x, y) for x, y, _, _ in RR(a, b, rc, d, n_arc=n_arc, step=STEP)]
    bm = bmesh.new()
    vs = [bm.verts.new((x / 1000, y / 1000, z / 1000)) for x, y in pts]
    es = [bm.edges.new((vs[i], vs[(i + 1) % len(vs)])) for i in range(len(vs))]
    bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=es, normal=(0, 0, 1))
    for f in bm.faces:
        if f.normal.z < 0:
            f.normal_flip()
    ax, by = a + d, b + d
    uvl = bm.loops.layers.uv.new("UVMap")
    for f in bm.faces:
        for lp in f.loops:
            lp[uvl].uv = ((lp.vert.co.x * 1000 + ax) / (2 * ax), (lp.vert.co.y * 1000 + by) / (2 * by))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.normals_split_custom_set_from_vertices([(0, 0, 1)] * len(me.vertices))
    return me


def rim_mesh():
    use_outline(10)
    rim, flips = RL.sweep_rrect("rim", bevel_profile(RIM_W, RIM_T, RIM_LIP, 3.0, 1.5, "Rim"), ("Rim",), A, B, RC, closed=True)
    me = H.join("SM_ResultsRim_SC", [(rim, None, [0])], ("M_Results_Rim",))
    bpy.data.meshes.remove(rim)
    return me, flips


def window_mesh(h):
    use_outline(8)
    a, b = WIN_W / 2, h / 2
    fr, flips = RL.sweep_rrect("frame", H.closed_rect(-WIN_FW, 0.0, WIN_Z0, WIN_Z1, 1.2, 0.3, "Frame"), ("Frame",),
                               a, b, WIN_RC, closed=True)
    pane = rr_fill("pane", a, b, WIN_RC, -WIN_FW + 0.05, PANE_Z)
    me = H.join(WIN_MESH[h], [(fr, None, [0]), (pane, None, [1])], ("M_Results_Frame", "M_Results_Pane"))
    for m in (fr, pane):
        bpy.data.meshes.remove(m)
    return me, flips


def tip_mesh():
    use_outline(8)
    a, b = TIP_W / 2, TIP_H / 2
    fr, flips = RL.sweep_rrect("tipframe", bevel_profile(TIP_RIM_W, TIP_T, TIP_LIP, 1.6, 0.8, "TipFrame"), ("TipFrame",),
                               a, b, TIP_RC, closed=True)
    gl = rr_fill("tipglass", a, b, TIP_RC, -TIP_RIM_W + 0.05, TIP_GLASS_Z)
    me = H.join("SM_ResultsTip_SC", [(fr, None, [0]), (gl, None, [1])], ("M_Results_TipFrame", "M_Results_TipGlass"))
    for m in (fr, gl):
        bpy.data.meshes.remove(m)
    return me, flips


def glass_mesh():
    """La base: el interior del marco ENTERO (llega a su pared interna). v2: sin calar las ventanas. Calada, en la
    entrada los huecos se veian como ranuras claras antes de que llegaran las ventanas; entera, cada ventana apoya su
    vidrio oscuro (Pane, opacidad 0,3) ENCIMA, como en la web (lamina .55 + vidrio de la ventana .3). Cuesta una capa
    translucida mas en las ventanas (pantalla final, sin mecanica corriendo)."""
    me = rr_fill("SM_ResultsGlass_SC", A, B, RC, -RIM_W + 0.05, GLASS_Z, n_arc=10)
    me.materials.append(bpy.data.materials.new("M_Results_Glass"))
    return me, 0


def trace_mesh():
    use_outline(10)
    cfg = {"path": [(p[0], p[1]) for p in RR(A, B, RC, -RIM_W / 2, n_arc=10, step=STEP)], "z": RIM_T + 0.5,
           "hw": TRACE_HW, "face": 1.0}
    me = LZ.trace_mesh(cfg, "SM_Results_Trace_SC")
    me.materials.append(bpy.data.materials.new("M_Results_Trace"))
    return me


def share_materials(meshes):
    """H.join crea un material NUEVO por pieza: las ventanas quedaban con 'M_Results_Frame.001'... (en Unreal serian
    slots con otro nombre y en la web otro material). Un solo material por nombre base."""
    keep = {}
    for me in meshes:
        for i, m in enumerate(me.materials):
            base = m.name.split(".")[0]
            if base not in keep:
                keep[base] = m
            me.materials[i] = keep[base]
    for m in list(bpy.data.materials):
        if m.users == 0:
            bpy.data.materials.remove(m)
    for base, m in keep.items():
        m.name = base


def stats(me):
    s = H.stats(me)
    s["slots"] = [m.name for m in me.materials]
    return s


def export_ue(me, path, tspace=True):
    """FBX para Unreal: una copia de la malla girada a los ejes de Unreal (cara +X, arriba +Z)."""
    m2 = me.copy()
    m2.transform(R_UE)
    ob = bpy.data.objects.new(me.name, m2)
    bpy.context.scene.collection.objects.link(ob)
    if tspace:
        RL.export_fbx(ob, path)
    else:
        LZ.export_fbx(ob, path)
    bpy.data.objects.remove(ob)
    bpy.data.meshes.remove(m2)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    info, flips = {}, {}
    rim, flips["rim"] = rim_mesh()
    wins = {}
    for h in sorted(WIN_MESH):
        wins[h], flips[WIN_MESH[h]] = window_mesh(h)
    tip, flips["tip"] = tip_mesh()
    glass, cut = glass_mesh()
    trace = trace_mesh()
    meshes = [rim, glass] + [wins[h] for h in sorted(WIN_MESH)] + [tip, trace]
    share_materials(meshes)
    for me in meshes:
        info[me.name] = stats(me)
    info["dadas_vuelta"] = flips
    info["lamina_caras_caladas"] = cut
    os.makedirs(OUT, exist_ok=True)
    for me in meshes:
        export_ue(me, os.path.join(OUT, me.name + ".fbx"), tspace=me is not trace)
    # .blend armado PARADO (orientacion web): cada pieza en su lugar; las ventanas con el nombre de su fila
    col = bpy.context.scene.collection

    def place(name, me, y):
        ob = bpy.data.objects.new(name, me)
        col.objects.link(ob)
        ob.matrix_world = R_WEB @ Matrix.Translation((0.0, y / 1000.0, 0.0))
        return ob
    place("Rim", rim, 0.0)
    place("Glass", glass, 0.0)
    for nm, cy, h in ROWS:
        place("Win" + nm, wins[h], cy)
    place("Tip", tip, TIP_Y)
    place("Trace", trace, 0.0)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "SM_Results_SC.blend"))
    print("RESULTS_OK", info)
    print("RESULTS_POS_mm", {("Win" + nm): cy for nm, cy, _ in ROWS}, "Tip", TIP_Y)


if __name__ == "__main__":
    try:
        main()
    except BaseException as e:
        print("RESULTS_FALLO", type(e).__name__, e)
        traceback.print_exc()
