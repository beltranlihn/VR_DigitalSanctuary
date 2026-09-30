# render_results.py - vista previa del CUADRO DE RESULTADOS (gen_results.py) como en la obra: PARADO a 2 m, con el
# centro 2 cm sobre el ojo (world.js: front(p, 2.0, .02)), sobre un fondo tipo Hall. Sombreado falso de la familia:
# marco, contornos y cajita translucidos como el HUD (0,45); la lamina ahumada; el vidrio oscuro de las ventanas; y los
# CONTENIDOS DE MUESTRA (make_results_sample_tex.py: los reales los pone Narrativa).
#   stills: frente, tres cuartos, detalle del bisel, detalle de una ventana (con la cajita abierta: "CALM")
#   anim:   la ENTRADA por piezas (cuadros f_###.png + rest.png para compose_anim.py; la salida = la misma al reves)
# Coreografia (t 0..1 = Duration del componente; la propuesta: 2,0 s):
#   0,00-0,30 trazo: la luz dibuja el contorno del panel            (BPC_AppearLuz_SC, AppearTrace)
#   0,24-0,56 marco: rendija de canto -> parpado, se enfria         (BPC_AppearLuz_SC, AppearBody)
#   0,42-0,66 lamina: se abre desde el centro hacia arriba y abajo  (PoseResults)
#   0,48-0,88 ventanas en CASCADA de arriba abajo (calma 0,48 · latido 0,54 · respiracion 0,60 · melodia 0,66; 0,22 c/u):
#             se abren a lo ancho desde el centro, con destello   (PoseResults)
#   0,56-0,80 titulo · cada contenido: desde (fin de su ventana - 0,06) durante 0,14   (Narrativa, leyendo AppearT)
#   la cajita NO entra con el panel: se abre al apuntar (TipShow/TipHide) y se cierra antes de la salida
# Uso: blender --background <SM_Results_SC.blend> --python render_results.py -- <dir_salida> <stills|anim> [cuadros]
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
import gen_results as G         # noqa: E402

S, seg, lerp, bump = P.smooth, P.seg, P.lerp, LZ.bump
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else "."
MODE = argv[1] if len(argv) > 1 else "stills"
ONLY = [int(x) for x in argv[2].split(",")] if len(argv) > 2 else None
TEX = os.path.join(os.path.dirname(bpy.data.filepath), "tex")
RIM_ALPHA = 0.55      # marco grande y cajita: la opacidad de la web (rim .55); los contornos de las ventanas 0,45
FRAME_ALPHA = 0.45
TM = {"seed": (0.00, 0.05), "enso": (0.02, 0.30), "head_off": (0.28, 0.38), "flare": (0.26, 0.42), "trace_out": (0.46, 0.60),
      "slit": (0.24, 0.34), "open": (0.30, 0.54), "thick": (0.36, 0.56), "cool": (0.30, 0.60),
      "glass": (0.42, 0.66), "title": (0.56, 0.80)}
WIN_T = {"Calm": (0.48, 0.70), "Heart": (0.54, 0.76), "Breath": (0.60, 0.82), "Melody": (0.66, 0.88)}
EYE = Vector((0.0, -2.0, -0.02))


def eoc(x):
    x = P.clamp01(x)
    return 1 - (1 - x) ** 3


def translucent(m, alpha):
    nt = m.node_tree
    out = [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'][0]
    em = out.inputs["Surface"].links[0].from_node
    tr = P._n(nt, "ShaderNodeBsdfTransparent")
    mx = P._n(nt, "ShaderNodeMixShader")
    mx.inputs[0].default_value = alpha
    P._link(nt, tr.outputs[0], mx.inputs[1])
    P._link(nt, em.outputs[0], mx.inputs[2])
    P._link(nt, mx.outputs[0], out.inputs["Surface"])
    return m


def concrete(name, alpha=RIM_ALPHA):
    """El hormigon de la familia, translucido como el borde del HUD (MI_HUD_Rim_SC: Base 0,66/0,60/0,52, SelfGlow 0,14)."""
    return translucent(P.fake_mat(name, (0.66, 0.60, 0.52), self_glow=0.14, mottle=0.06, grain=0.05, sh=LZ.SH), alpha)


def smoke(name, col, alpha, rim=1.2):
    """Vidrio ahumado: emision oscura + un poco de fresnel, mezclada con transparente (= M_SCPanelGlass_SC)."""
    m, nt, out = P._base(name)
    geo = P._n(nt, "ShaderNodeNewGeometry")
    fr = P._m(nt, 'SUBTRACT', 1.0, P._m(nt, 'MAXIMUM', P._vm(nt, 'DOT_PRODUCT', geo.outputs["Normal"], geo.outputs["Incoming"]), 0.0))
    em = P._n(nt, "ShaderNodeEmission")
    P._link(nt, P._vm(nt, 'SCALE', col, scale=P._m(nt, 'ADD', 1.0, P._m(nt, 'MULTIPLY', fr, rim))), em.inputs["Color"])
    tr = P._n(nt, "ShaderNodeBsdfTransparent")
    mx = P._n(nt, "ShaderNodeMixShader")
    mx.inputs[0].default_value = alpha
    P._link(nt, tr.outputs[0], mx.inputs[1])
    P._link(nt, em.outputs[0], mx.inputs[2])
    P._link(nt, mx.outputs[0], out.inputs["Surface"])
    return m


def content_plane(name, png, w_mm, h_mm, y_mm, z_mm):
    """Contenido de muestra: plano con la imagen RGBA (emision * alfa * AnimGlow)."""
    me = bpy.data.meshes.new(name)
    w, h, z = w_mm / 2000, h_mm / 2000, z_mm / 1000
    me.from_pydata([(-w, -h, z), (w, -h, z), (w, h, z), (-w, h, z)], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new(name="UVMap")
    for i, t in enumerate(((0, 0), (1, 0), (1, 1), (0, 1))):
        uv.data[i].uv = t
    m, nt, out = P._base(name)
    img = P._n(nt, "ShaderNodeTexImage")
    img.image = bpy.data.images.load(os.path.join(TEX, png + ".png"), check_existing=True)
    g = P._value(nt, "AnimGlow", 1.0)
    em = P._n(nt, "ShaderNodeEmission")
    P._link(nt, P._vm(nt, 'SCALE', img.outputs["Color"], scale=1.0), em.inputs["Color"])
    tr = P._n(nt, "ShaderNodeBsdfTransparent")
    mx = P._n(nt, "ShaderNodeMixShader")
    P._link(nt, P._m(nt, 'MULTIPLY', img.outputs["Alpha"], g), mx.inputs[0])
    P._link(nt, tr.outputs[0], mx.inputs[1])
    P._link(nt, em.outputs[0], mx.inputs[2])
    P._link(nt, mx.outputs[0], out.inputs["Surface"])
    me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.matrix_world = G.R_WEB @ Matrix.Translation((0.0, y_mm / 1000, 0.0))
    return ob


def world():
    w = bpy.data.worlds.new("Hall")
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes["Background"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 3.0
    nt.links.new(tc.outputs["Generated"], nz.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.07, 0.065, 0.06, 1)
    ramp.color_ramp.elements[1].color = (0.36, 0.34, 0.31, 1)
    mathn = nt.nodes.new("ShaderNodeMath")
    mathn.operation = 'MULTIPLY_ADD'
    nt.links.new(sep.outputs["Z"], mathn.inputs[0])
    mathn.inputs[1].default_value = 0.9
    mathn.inputs[2].default_value = 0.45
    add = nt.nodes.new("ShaderNodeMath")
    add.operation = 'MULTIPLY_ADD'
    nt.links.new(nz.outputs["Fac"], add.inputs[0])
    add.inputs[1].default_value = 0.35
    nt.links.new(mathn.outputs[0], add.inputs[2])
    nt.links.new(add.outputs[0], ramp.inputs[0])
    nt.links.new(ramp.outputs[0], bg.inputs["Color"])
    bpy.context.scene.world = w


def setup():
    scn = bpy.context.scene
    ob = bpy.data.objects
    ob["Rim"].data.materials[0] = concrete("Rim")
    for nm, _, _ in G.ROWS:                       # cada ventana con SU material (destello propio, como las MID de Unreal)
        o = ob["Win" + nm]
        o.material_slots[0].link = 'OBJECT'
        o.material_slots[0].material = concrete("Frame" + nm, FRAME_ALPHA)
        o.material_slots[1].link = 'OBJECT'
        o.material_slots[1].material = smoke("Pane" + nm, (0.030, 0.034, 0.050), 0.30, rim=0.6)   # sobre la lamina
    ob["Glass"].data.materials[0] = smoke("Glass", (0.055, 0.060, 0.085), 0.55)
    ob["Tip"].data.materials[0] = concrete("TipFrame")
    ob["Tip"].data.materials[1] = smoke("TipGlass", (0.045, 0.050, 0.070), 0.74)
    tmat = LZ.trace_mat()
    ob["Trace"].data.materials[0] = tmat
    content_plane("C_Title", "res_title", 1030.0, 95.0, G.TITLE_Y, -1.0)
    for nm, cy, h in G.ROWS:
        content_plane("C_" + nm, "res_" + nm.lower(), G.WIN_W - 2 * G.WIN_FW, h - 2 * G.WIN_FW, cy, -1.0)
    content_plane("C_Tip", "res_tip", G.TIP_W - 14.0, G.TIP_H - 14.0, G.TIP_Y, 0.0)
    world()
    scn.render.engine = 'CYCLES'
    scn.cycles.samples = 48
    scn.cycles.transparent_max_bounces = 24
    scn.view_settings.view_transform = 'Standard'
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = 'OPTIX'
        prefs.get_devices()
        for dv in prefs.devices:
            dv.use = dv.type == 'OPTIX'
        scn.cycles.device = 'GPU'
    except Exception:
        pass
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    scn.collection.objects.link(cam)
    scn.camera = cam
    cam.data.clip_start = 0.01
    return cam, tmat


def aim(cam, loc, tg, lens):
    cam.location = Vector(loc)
    cam.rotation_euler = (Vector(tg) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = lens
    bpy.context.view_layer.update()


def stills(cam, tmat):
    scn = bpy.context.scene
    bpy.data.objects["Trace"].hide_render = True
    V = {"frente": (EYE, (0, 0, 0.09), 44, (1100, 1100)),
         "tres_cuartos": ((-1.15, -1.62, 0.12), (0.02, 0, 0.06), 46, (1200, 1000)),
         "bisel": ((-0.30, -0.50, 0.66), (-0.49, 0, 0.44), 60, (1100, 800)),
         "ventana": ((0.22, -0.55, 0.36), (0.44, 0, 0.25), 55, (1100, 800))}
    for nm, (loc, tg, lens, res) in V.items():
        scn.render.resolution_x, scn.render.resolution_y = res
        aim(cam, loc, tg, lens)
        scn.render.filepath = os.path.join(OUT, "results_" + nm + ".png")
        bpy.ops.render.render(write_still=True)


def anim(cam, tmat):
    scn = bpy.context.scene
    ob = bpy.data.objects
    scn.render.resolution_x, scn.render.resolution_y = 820, 820
    scn.cycles.samples = 20
    aim(cam, EYE, (0, 0, 0.09), 44)
    ob["Tip"].hide_render = ob["C_Tip"].hide_render = True
    names = ["Rim", "Glass", "Trace", "C_Title"] + ["Win" + n for n, _, _ in G.ROWS] + ["C_" + n for n, _, _ in G.ROWS]
    rest = {n: ob[n].matrix_world.copy() for n in names}
    M = bpy.data.materials
    defaults = {(m.name, n.name): n.outputs[0].default_value for m in M if m.node_tree for n in m.node_tree.nodes if n.type == 'VALUE'}
    # parpado del marco (la cuenta de BPC_AppearLuz_SC.CaptureEye): eje = derecha de la camara en el plano de la cara
    n = Vector((0, -1, 0))
    e = cam.location - Vector((0, 0, 0))
    right = cam.matrix_world.to_3x3() @ Vector((1, 0, 0))
    ax = (right - right.dot(n) * n).normalized()
    n2 = ax.cross(e).normalized()
    if n2.dot(n) < 0:
        n2 = -n2
    th = math.atan2(n.cross(n2).dot(ax), n.dot(n2))
    Bm = Matrix((ax, n.cross(ax), n)).transposed().to_4x4()
    print("PARPADO th_grados", round(math.degrees(th), 1), "eje", tuple(round(c, 3) for c in ax))

    def setv(mat, **vals):
        for k, v in vals.items():
            mat.node_tree.nodes[k].outputs[0].default_value = v

    def reset():
        for k in names:
            ob[k].matrix_world = rest[k]
            ob[k].hide_render = False
        for (mn, nn), v in defaults.items():
            M[mn].node_tree.nodes[nn].outputs[0].default_value = v

    def pose(t):
        # 1. trazo
        sweep = P.ease_in_out_cubic(seg(t, *TM["enso"]))
        head = 3.2 * S(seg(t, *TM["seed"])) * (1 - S(seg(t, *TM["head_off"])))
        tglow = (1 + 0.5 * bump(seg(t, *TM["flare"]))) * (1 - S(seg(t, *TM["trace_out"])))
        setv(tmat, Sweep=sweep, Head=head, Glow=tglow)
        ob["Trace"].hide_render = (sweep < 1e-4 and head < 1e-4) or (tglow < 1e-4 and head < 1e-4)
        # 2. marco: rendija -> parpado
        rim = ob["Rim"]
        if t < TM["slit"][0]:
            rim.hide_render = True
        else:
            sx = max(P.ease_out_cubic(seg(t, *TM["slit"])), 1e-3)
            o = P.ease_in_out_cubic(seg(t, *TM["open"]))
            sz = lerp(0.05, 1.0, P.ease_in_out_cubic(seg(t, *TM["thick"])))
            Mx = Matrix.Rotation(th * (1 - o), 4, ax) @ Bm @ Matrix.Diagonal((sx, sx, sz, 1.0)) @ Bm.inverted()
            rim.matrix_world = Mx @ rest["Rim"]
            setv(M["Rim"], Flash=1.2 * (1 - S(seg(t, *TM["cool"]))))
        # 3. lamina: desde el centro hacia arriba y abajo
        u = seg(t, *TM["glass"])
        if u <= 0:
            ob["Glass"].hide_render = True
        else:
            ob["Glass"].matrix_world = rest["Glass"] @ Matrix.Diagonal((1.0, max(P.ease_in_out_cubic(u), 1e-3), 1.0, 1.0))
        # 4. ventanas en cascada: a lo ancho desde el centro (escala X), el alto de 0,15 a 1; destello propio
        for nm, _, _ in G.ROWS:
            w = ob["Win" + nm]
            u = seg(t, *WIN_T[nm])
            if u <= 0:
                w.hide_render = True
            else:
                w.matrix_world = rest["Win" + nm] @ Matrix.Diagonal((max(eoc(u), 1e-3), lerp(0.15, 1.0, eoc(seg(u, 0.3, 1.0))), 1.0, 1.0))
            setv(M["Frame" + nm], Flash=0.6 * math.sin(math.pi * u))
            c0 = WIN_T[nm][1] - 0.06
            setv(M["C_" + nm], AnimGlow=S(seg(t, c0, c0 + 0.14)))
        setv(M["C_Title"], AnimGlow=S(seg(t, *TM["title"])))

    os.makedirs(OUT, exist_ok=True)
    reset()
    ob["Trace"].hide_render = True
    setv(tmat, Glow=0.0)
    scn.render.filepath = os.path.join(OUT, "rest.png")
    bpy.ops.render.render(write_still=True)
    N = 61                                          # 2,0 s a 30 cuadros
    for fr in range(N):
        if ONLY is not None and fr not in ONLY:
            continue
        reset()
        pose(fr / (N - 1))
        scn.render.filepath = os.path.join(OUT, "f_%03d.png" % fr)
        bpy.ops.render.render(write_still=True)


def main():
    cam, tmat = setup()
    os.makedirs(OUT, exist_ok=True)
    if MODE == "anim":
        anim(cam, tmat)
    else:
        stills(cam, tmat)
    print("RESULTS_RENDER_OK", MODE, OUT)


try:
    main()
except BaseException as e:
    print("RESULTS_RENDER_FALLO", type(e).__name__, e)
    traceback.print_exc()
