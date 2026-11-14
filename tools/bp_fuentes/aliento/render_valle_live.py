# -*- coding: utf-8 -*-
"""Envoltorio de preview_breath_valley.py (NO lo modifica): renderiza solo la vista del usuario en t0, con la capa
viva (respira=S) y el valle en Z -90,4 como en Test_Entering, en esta carpeta; se saltea t5 y las mediciones largas.
Uso: blender --background --factory-startup --python render_valle_live.py -- tag=_inhala respira=1 valleZ=-90.4
"""
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.abspath(os.path.join(AQUI, "..", "..", "..", "..", ".claude", "skills", "unreal-vr", "scripts"))
sys.path.insert(0, SCRIPTS)
import preview_breath_valley as pbv  # noqa: E402

_render = pbv.render


def _solo_t0(ruta, w, h):
    if "_t5" in os.path.basename(ruta):
        print("PREVIEW (salteado) %s" % ruta)
        return
    _render(ruta, w, h)


pbv.render = _solo_t0
pbv.diferencia = lambda *a, **k: None
pbv.medir_movimiento = lambda *a, **k: None
pbv.medir_malla = lambda *a, **k: None
sys.argv += ["solo=principal", "carpeta=" + AQUI]
pbv.main()
