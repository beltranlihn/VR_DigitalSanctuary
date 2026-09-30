# anim_hud.py - propuesta de ENTRADA del HUD 3D por piezas (Beltran, 2026-09-30: "piensalo en piezas para poder animar
# su transformacion de entrada"), en la familia "luz primero". t de 0 a 1 = 1,5 s; la SALIDA es la misma al reves.
#   0,00-0,30  la luz dibuja el contorno de la pildora (trazo, como el timbre)
#   0,24-0,56  el BORDE nace como rendija de canto y se abre como parpado (Flash 1 -> 0)
#   0,40-0,62  el MARCO DEL EEG se abre desde el centro (a lo largo) con un destello
#   0,48-0,74  la LAMINA se extiende desde el centro hacia los extremos
#   0,50-0,78  los dos NIDOS salen de los extremos del marco del EEG y viajan a su lugar (clac: ease_out_back)
#   0,62-0,90  el ANILLO se da vuelta en su nido (de canto a frente) y sus cavidades se llenan; el alma aparece adentro
#   0,66-0,88  la linea del EEG se enciende
#   0,72-1,00  la AMEBA cae en su asiento y late una vez
# Uso: blender --background <SM_HUD_SC.blend> --python anim_hud.py -- <dir_cuadros> [cuadros]
import math
import os
import sys
import traceback

import bpy
from mathutils import Matrix, Vector

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import anim_palette_base as P   # noqa: E402
import anim_luz_objects as LZ   # noqa: E402
import gen_hud as H             # noqa: E402
import render_hud as RH         # noqa: E402

S, seg, lerp, bump = P.smooth, P.seg, P.lerp, LZ.bump
TM = {"seed": (0.00, 0.05), "enso": (0.02, 0.30), "head_off": (0.28, 0.38), "flare": (0.26, 0.42), "trace_out": (0.46, 0.60),
      "slit": (0.24, 0.34), "open": (0.30, 0.54), "thick": (0.36, 0.56), "cool": (0.30, 0.60),
      "bezel": (0.40, 0.62), "glass": (0.48, 0.74), "cups": (0.50, 0.78), "ring": (0.62, 0.90), "fill": (0.70, 0.95),
      "eeg": (0.66, 0.88), "pulse": (0.72, 0.92), "beat": (0.90, 1.00)}


def wrap_glow(mat):
    """Inserta un nodo de valor 'AnimGlow' que multiplica la emision (para encender el EEG)."""
    nt = mat.node_tree
    em = [n for n in nt.nodes if n.type == 'EMISSION'][0]
    src = em.inputs["Color"].links[0].from_socket
    g = P._value(nt, "AnimGlow", 1.0)
    P._link(nt, P._vm(nt, 'SCALE', src, scale=g), em.inputs["Color"])


def setv(mat, **vals):
    for k, v in vals.items():
        mat.node_tree.nodes[k].outputs[0].default_value = v


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    out = argv[0]
    only = [int(x) for x in argv[1].split(",")] if len(argv) > 1 else None
    cam = RH.setup_scene()
    ob = bpy.data.objects
    M = bpy.data.materials
    wrap_glow(M["EEGLine"])
    cfg = {"path": [(p[0], p[1]) for p in H.RL.rrect_outline(H.A, H.B, H.RC, -H.RIM_W / 2)], "z": H.T / 2 + 0.3, "hw": 6.0, "face": 1.0}
    tme = LZ.trace_mesh(cfg, "SM_HUD_Trace_SC")
    tr = bpy.data.objects.new(tme.name, tme)
    bpy.context.scene.collection.objects.link(tr)
    LZ.export_fbx(tr, os.path.join(LZ.CS, "HUD", tme.name + ".fbx"))     # H.OUT lee el argv de ESTE script
    tmat = LZ.trace_mat()
    tme.materials.append(tmat)
    names = ["SM_HUDRim_SC", "SM_HUDBezel_SC", "SM_HUDGlass_SC", "SM_HUDPulse_SC", "Nest", "Seat", "Ring", "Alma", "EEG", tr.name]
    bpy.context.view_layer.update()
    rest = {n: ob[n].matrix_world.copy() for n in names}
    mats = {m.name: m for m in M}
    defaults = {(m.name, n.name): n.outputs[0].default_value for m in M if m.node_tree for n in m.node_tree.nodes if n.type == 'VALUE'}
    # camara: de frente, un poco desde abajo (el HUD va inclinado hacia el ojo)
    tg = Vector((0, 0, 0))
    cam.location = tg + Vector((0.0, -0.30, 1.0)).normalized() * 0.52
    cam.rotation_euler = (tg - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = 50
    scn = bpy.context.scene
    scn.render.resolution_x, scn.render.resolution_y = 900, 450
    scn.cycles.samples = 20
    bpy.context.view_layer.update()
    # parpado del borde (misma cuenta que anim_luz_objects: eje = derecha de la camara en el plano, de canto al ojo)
    n = Vector((0, 0, 1))
    z0 = 0.0
    e = cam.location - Vector((0, 0, z0))
    right = cam.matrix_world.to_3x3() @ Vector((1, 0, 0))
    ax = (right - right.dot(n) * n).normalized()
    n2 = ax.cross(e).normalized()
    if n2.dot(n) < 0:
        n2 = -n2
    th = math.atan2(n.cross(n2).dot(ax), n.dot(n2))
    Bm = Matrix((ax, n.cross(ax), n)).transposed().to_4x4()
    ring_rest_charge = LZ.RING_REST_CHARGE

    def reset():
        for k in names:
            ob[k].matrix_world = rest[k]
            ob[k].hide_render = False
        for (mn, nn), v in defaults.items():
            mats[mn].node_tree.nodes[nn].outputs[0].default_value = v

    def pose(t):
        # 1. trazo
        sweep = P.ease_in_out_cubic(seg(t, *TM["enso"]))
        head = 3.2 * S(seg(t, *TM["seed"])) * (1 - S(seg(t, *TM["head_off"])))
        tglow = (1 + 0.5 * bump(seg(t, *TM["flare"]))) * (1 - S(seg(t, *TM["trace_out"])))
        setv(tmat, Sweep=sweep, Head=head, Glow=tglow)
        tr.hide_render = (sweep < 1e-4 and head < 1e-4) or (tglow < 1e-4 and head < 1e-4)
        # 2. borde: rendija -> parpado
        rim = ob["SM_HUDRim_SC"]
        if t < TM["slit"][0]:
            rim.hide_render = True
        else:
            sx = max(P.ease_out_cubic(seg(t, *TM["slit"])), 1e-3)
            o = P.ease_in_out_cubic(seg(t, *TM["open"]))
            sz = lerp(0.05, 1.0, P.ease_in_out_cubic(seg(t, *TM["thick"])))
            Mx = Matrix.Rotation(th * (1 - o), 4, ax) @ Bm @ Matrix.Diagonal((sx, sx, sz, 1.0)) @ Bm.inverted()
            rim.matrix_world = Mx @ rest["SM_HUDRim_SC"]
            setv(mats["Rim"], Flash=1.2 * (1 - S(seg(t, *TM["cool"]))))
        # 3. marco del EEG: se abre a lo largo desde el centro
        bz = ob["SM_HUDBezel_SC"]
        u = seg(t, *TM["bezel"])
        if u <= 0:
            bz.hide_render = True
        else:
            k = P.ease_out_cubic(u)
            bz.matrix_world = Matrix.Diagonal((max(k, 1e-3), lerp(0.15, 1.0, P.ease_out_cubic(seg(u, 0.3, 1.0))), 1.0, 1.0)) @ rest["SM_HUDBezel_SC"]
        setv(mats["Frame"], Flash=0.6 * bump(seg(t, TM["bezel"][0], TM["cups"][1])) * (1 - S(seg(t, 0.70, 0.80))))
        # 4. lamina: desde el centro hacia los extremos
        gl = ob["SM_HUDGlass_SC"]
        u = seg(t, *TM["glass"])
        if u <= 0:
            gl.hide_render = True
        else:
            gl.matrix_world = Matrix.Diagonal((max(P.ease_in_out_cubic(u), 1e-3), 1.0, 1.0, 1.0)) @ rest["SM_HUDGlass_SC"]
        # 5. nidos: salen de las puntas del marco del EEG y viajan a su lugar
        u = seg(t, *TM["cups"])
        for nm, sgn in (("Nest", 1), ("Seat", -1)):
            c = ob[nm]
            if u <= 0:
                c.hide_render = True
                continue
            k = P.ease_out_back(u, 1.1)
            x = lerp(sgn * H.EEG_A / 1000, sgn * H.END_X / 1000, k)
            s = lerp(0.25, 1.0, P.ease_out_cubic(u))
            c.matrix_world = Matrix.Translation((x, 0, 0)) @ Matrix.Diagonal((s, s, s, 1.0))
        # 6. anillo: se da vuelta de canto a frente en su nido; el alma aparece adentro
        rg, al = ob["Ring"], ob["Alma"]
        u = seg(t, *TM["ring"])
        if u <= 0:
            rg.hide_render = al.hide_render = True
        else:
            k = P.ease_out_back(u, 1.0)
            ang = math.radians(90) * (1 - k)
            piv = Vector((H.END_X / 1000, 0, 0))
            R = Matrix.Translation(piv) @ Matrix.Rotation(ang, 4, 'Y') @ Matrix.Translation(-piv)
            rg.matrix_world = R @ rest["Ring"]
            sa = max(P.ease_out_back(seg(u, 0.4, 1.0), 1.4), 1e-3)
            al.matrix_world = Matrix.Translation(piv) @ Matrix.Diagonal((sa, sa, sa, 1.0)) @ Matrix.Translation(-piv) @ rest["Alma"]
            setv(mats["RingFrame"], Flash=0.8 * (1 - S(u)))
        f = P.ease_in_out_cubic(seg(t, *TM["fill"]))
        setv(mats["Light"], Charge=min(ring_rest_charge, 5.0 * f), Glow=S(seg(t, *TM["ring"])),
             Front=1.2 * S(seg(t, TM["fill"][0], TM["fill"][0] + 0.05)) * (1 - S(seg(t, 0.86, 0.97))))
        # 7. EEG
        setv(mats["EEGLine"], AnimGlow=S(seg(t, *TM["eeg"])))
        # 8. ameba: cae en su asiento y late una vez
        pu = ob["SM_HUDPulse_SC"]
        u = seg(t, *TM["pulse"])
        if u <= 0:
            pu.hide_render = True
        else:
            k = P.ease_out_back(u, 1.3)
            beat = 1 + 0.12 * bump(seg(t, *TM["beat"]))
            s = lerp(0.3, 1.0, P.ease_out_cubic(u)) * beat
            c = rest["SM_HUDPulse_SC"].to_translation()
            pu.matrix_world = Matrix.Translation(c + Vector((0, 0, 0.012 * (1 - k)))) @ Matrix.Diagonal((s, s, s, 1.0))
            setv(mats["Pulse"], Flash=0.6 * (1 - S(u)))

    os.makedirs(out, exist_ok=True)
    reset()
    tr.hide_render = True
    setv(tmat, Glow=0.0)
    scn.render.filepath = os.path.join(out, "rest.png")
    bpy.ops.render.render(write_still=True)
    N = 46
    for fr in range(N):
        if only is not None and fr not in only:
            continue
        reset()
        pose(fr / (N - 1))
        scn.render.filepath = os.path.join(out, "f_%03d.png" % fr)
        bpy.ops.render.render(write_still=True)
    print("HUD_ANIM_OK", out)


try:
    main()
except BaseException as e:
    print("HUD_ANIM_FALLO", type(e).__name__, e)
    traceback.print_exc()
