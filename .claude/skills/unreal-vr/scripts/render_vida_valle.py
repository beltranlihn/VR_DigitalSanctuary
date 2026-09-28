# -*- coding: utf-8 -*-
"""render_vida_valle.py - dibuja el VALLE de Entering con la FRANJA de la rafaga, cuadro por cuadro, en Blender headless
(2026-09-28). NO modifica preview_breath_valley.py: importa sus piezas (la malla real, el cielo, la esfera de referencia
del metaball, la camara y el render Workbench sin tonemapper) y cambia solo el color de los vertices del suelo:
    gradiente del valle (valley_model.valley_grad) -> GustLeanVS (vida_model.gust_lean_vs) -> sombreado (valley_model.suelo)
con el LOOK ACTUAL de Test_Entering (las perillas de ApplyLook y el valle en Z -90,4) y la capa viva en su neutro.
Lee VR_Test/Saved/ClaudeScripts/vida/preview/timeline.json (lo escribe sim_vida.py linea) y escribe <id>.png al lado.

Uso:
  "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" --background --factory-startup --python render_vida_valle.py
"""
import json
import math
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
if AQUI not in sys.path:
    sys.path.insert(0, AQUI)
import preview_breath_valley as pbv  # noqa: E402
import vida_model as vida  # noqa: E402

gen, vm = pbv.gen, pbv.vm
PREV = os.path.abspath(os.path.join(AQUI, "..", "..", "..", "..", "VR_Test", "Saved", "ClaudeScripts", "vida", "preview"))


def main():
    import bpy
    tl = json.load(open(os.path.join(PREV, "timeline.json")))
    P = pbv.P
    P.update(tl["look"])
    z0 = float(tl["valleZ"])
    ojos = pbv.OJOS_DEF - np.array([0.0, 0.0, z0])
    meta = np.array([380.0, 0.0, 125.0]) - np.array([0.0, 0.0, z0])
    P["ShadowCenter"] = tuple(meta.tolist())
    gen.limpiar_escena()
    base, _, _ = gen.construir()
    base.hide_render = True
    valle = base.copy()
    valle.data = base.data.copy()
    bpy.context.collection.objects.link(valle)
    valle.hide_render = False
    me = valle.data
    nv = len(me.vertices)
    co_b = np.empty(nv * 3, dtype=np.float64)
    base.data.vertices.foreach_get("co", co_b)
    co_b = co_b.reshape(nv, 3)
    ue = pbv.blender_a_ue(co_b)
    LP = np.stack([ue[:, 0], ue[:, 1], np.zeros(nv)], 1)
    valle.data.materials.append(pbv.material_color_vertice("M_ValleVertice", "Col"))
    ojos_b = pbv.ue_a_blender(ojos)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=720, ring_count=360, radius=pbv.CIELO_RADIO / 100.0, location=tuple(ojos_b.tolist()))
    sky = bpy.context.active_object
    sme = sky.data
    ns = len(sme.vertices)
    sco = np.empty(ns * 3, dtype=np.float64)
    sme.vertices.foreach_get("co", sco)
    sdir = pbv.blender_a_ue(sco.reshape(ns, 3))
    sdir = sdir / np.linalg.norm(sdir, axis=1)[:, None]
    pbv.poner_color(sme, "Col", vm.cielo(sdir, P))
    sme.materials.append(pbv.material_color_vertice("M_CieloVertice", "Col"))
    bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=pbv.METABALL_RADIO / 100.0,
                                         location=tuple(pbv.ue_a_blender(meta).tolist()))
    mb = bpy.context.active_object
    mme = mb.data
    try:
        mme.shade_smooth()
    except AttributeError:
        pass
    nm = len(mme.vertices)
    mco = np.empty(nm * 3, dtype=np.float64)
    mme.vertices.foreach_get("co", mco)
    mn = pbv.blender_a_ue(mco.reshape(nm, 3))
    mn = mn / np.linalg.norm(mn, axis=1)[:, None]
    Lm = np.array([-0.45, -0.25, 0.86])
    Lm = Lm / np.linalg.norm(Lm)
    wr = vm.sat((mn @ Lm + 0.8) / 1.8)
    pbv.poner_color(mme, "Col", vm.lerp(np.array([0.45, 0.50, 0.80]), np.array([0.92, 0.945, 1.0]), np.sqrt(wr)[:, None]))
    mme.materials.append(pbv.material_color_vertice("M_MetaballRef", "Col"))
    pbv.preparar_render()
    cam = pbv.camara_nueva()
    cache = {}
    hechos = 0
    for f in tl["frames"]:
        ruta = os.path.join(PREV, f["id"] + ".png")
        t = round(float(f["t"]), 3)
        if t not in cache:
            cache.clear()
            cache[t] = vm.valley_grad(ue[:, 0], ue[:, 1], t, P)
        gx, gy, h, hf = cache[t]
        nuevo = co_b.copy()
        nuevo[:, 2] = h / 100.0
        me.vertices.foreach_set("co", nuevo.ravel())
        me.update()
        G = np.stack([gx, gy, h, hf], 1)
        pv = {k: np.asarray(v, float) for k, v in f["pv"].items()}
        G2 = vida.gust_lean_vs(G, LP, 0.0, pv)
        pbv.poner_color(me, "Col", vm.suelo(ue[:, 0], ue[:, 1], G2[:, 0], G2[:, 1], G2[:, 2], G2[:, 3], ojos, P))
        c = f["cam"]
        cam.data.angle = math.radians(c["hfov"])
        pbv.orientar(cam, ojos, c["yaw"], c["pitch"])
        pbv.render(ruta, c["w"], c["h"])
        hechos += 1
    print("VIDA render: %d cuadros en %s" % (hechos, PREV))


if __name__ == "__main__":
    main()
