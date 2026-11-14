# HUD de Inner Canvas (BP_ICHudKit_IC sobre BP_SoulHUD3D_SC): la pildora del HUD de la obra (render_hud.py: borde, marco,
# nido y asiento translucidos, lamina) SIN anillo ni ameba; a la izquierda el circulo de TINTA verde (InkColor), al centro
# el NOMBRE (Quicksand Bold, blanco, como el teclado) y a la derecha el RELOJ m:ss. De frente, fondo transparente.
# Uso: blender --background <copia>/SM_HUD_SC.blend --python render_hud_ic.py -- <salida.png> [NOMBRE] [m:ss] [ancho alto]
import importlib.util
import os
import sys
import traceback

import bpy
from mathutils import Vector

SKILL = r"C:\Users\beltr\Desktop\Alma Digital Studio\Projects\VR Unreal\.claude\skills\blender-3d\scripts"
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, SKILL)
import fit_cam  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = argv[0]
NAME = argv[1] if len(argv) > 1 else "SOFIA"
TIME = argv[2] if len(argv) > 2 else "5:00"
RW = int(argv[3]) if len(argv) > 3 else 2048
RH = int(argv[4]) if len(argv) > 4 else 512
FONT = os.path.expanduser(r"~\AppData\Local\Microsoft\Windows\Fonts\Quicksand-Bold.ttf")
INK = (0.45, 1.0, 0.62)          # InkColor de BP_ICHudKit_IC


def load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(SKILL, name + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def emit_mat(name, color, strength=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = tuple(color) + (1,)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    return m


def ink_mat():
    """Disco de tinta: centro claro -> verde de la tinta -> borde suave (alfa), como el halo M_ChargeHalo_SC lleno."""
    m = bpy.data.materials.new("Ink")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    grad = nt.nodes.new("ShaderNodeTexGradient")
    grad.gradient_type = 'SPHERICAL'
    nt.links.new(tc.outputs["Object"], grad.inputs["Vector"])
    # el disco mide 1 de radio en coordenadas de objeto (se escala): SPHERICAL = 1 - r
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    e = ramp.color_ramp.elements
    e[0].position, e[0].color = 0.0, INK + (1,)
    e[1].position, e[1].color = 0.75, (0.80, 1.0, 0.86, 1)
    mid = e.new(0.25)
    mid.color = tuple(c * 0.9 for c in INK) + (1,)
    nt.links.new(grad.outputs["Fac"], ramp.inputs["Fac"])
    a = nt.nodes.new("ShaderNodeMapRange")
    a.inputs["From Min"].default_value, a.inputs["From Max"].default_value = 0.0, 0.06
    nt.links.new(grad.outputs["Fac"], a.inputs["Value"])
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(ramp.outputs["Color"], em.inputs["Color"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(a.outputs["Result"], mx.inputs[0])
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(em.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    return m


def text(body, cap, loc, max_w=None):
    """Texto centrado con ALTO DE MAYUSCULA cap (m), como lo dibuja el visor; se achica si pasa max_w."""
    cu = bpy.data.curves.new("T_" + body, 'FONT')
    cu.body = body
    cu.font = bpy.data.fonts.load(FONT)
    cu.align_x, cu.align_y = 'CENTER', 'CENTER'
    cu.size = 0.01
    ob = bpy.data.objects.new("T_" + body, cu)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    cu.materials.append(emit_mat("Txt_" + body, (1.0, 1.0, 1.0), 1.0))
    bpy.context.view_layer.update()
    cu.size = 0.01 * cap / ob.dimensions.y
    bpy.context.view_layer.update()
    if max_w and ob.dimensions.x > max_w:
        cu.size *= max_w / ob.dimensions.x
    bpy.context.view_layer.update()
    return ob


try:
    RH_ = load("render_hud")
    H = RH_.H
    fr = RH_.rim_mat("Frame")
    bpy.data.objects["SM_HUDBezel_SC"].data.materials[0] = fr
    cup = bpy.data.objects["Nest"].data
    cup.materials[0] = fr
    cup.materials[1] = RH_.glass_mat()               # en el visor el fondo del nido y del asiento deja ver el mundo
    bpy.data.objects["SM_HUDRim_SC"].data.materials[0] = RH_.rim_mat()
    bpy.data.objects["SM_HUDGlass_SC"].data.materials[0] = RH_.glass_mat()
    for nm in ("SM_HUDPulse_SC",):                      # la ameba: en Inner Canvas va escondida (escala 0,0001)
        bpy.data.objects[nm].hide_render = True
    cam = RH_.render_settings()
    scn = bpy.context.scene
    print("OBJS", sorted((o.name, o.type, o.hide_render) for o in scn.objects))
    mm = 0.001
    # tinta a la izquierda (asiento de la hermana), reloj a la derecha (nido del anillo), nombre en la ventana del EEG
    bpy.ops.mesh.primitive_circle_add(vertices=96, radius=1.0, fill_type='NGON', location=(-H.END_X * mm, 0, 0.3 * mm))
    ink = bpy.context.active_object
    ink.name = "InkDisc"
    ink.scale = (21.5 * mm, 21.5 * mm, 1)
    ink.data.materials.append(ink_mat())
    t_name = text(NAME, 20.0 * mm, (0, 0, 0.6 * mm), max_w=2 * (H.EEG_A - 9.0) * mm)   # 75 % del alto de la ventana
    t_time = text(TIME, 16.0 * mm, (H.END_X * mm, 0, 0.6 * mm), max_w=34.0 * mm)   # 70 % del ancho del nido
    scn.render.resolution_x, scn.render.resolution_y = RW, RH
    scn.render.resolution_percentage = 100
    scn.render.film_transparent = True
    scn.render.image_settings.file_format = 'PNG'
    scn.render.image_settings.color_mode = 'RGBA'
    scn.cycles.samples = 128
    bpy.context.view_layer.update()
    fit_objs = [bpy.data.objects["SM_HUDRim_SC"]]
    dist = fit_cam.fit(cam, fit_objs, (0.0, -0.05, 1.0), lens=85.0, fill=0.92)
    print("DIST", round(dist, 3), "NAME", NAME, [round(x / mm, 1) for x in t_name.dimensions[:2]], "TIME", TIME, [round(x / mm, 1) for x in t_time.dimensions[:2]])
    scn.render.filepath = OUT
    bpy.ops.render.render(write_still=True)
    print("RENDER_OK", OUT)
except BaseException as e:
    print("RENDER_FALLO", type(e).__name__, e)
    traceback.print_exc()
