# -*- coding: utf-8 -*-
"""Envoltorio de preview_breath_valley.py (NO lo modifica): mismas perillas por argv (clave=valor despues de "--"),
pero escribe en esta carpeta, renderiza solo la vista del usuario en t0 y se saltea las mediciones largas.
Uso: blender --background --factory-startup --python render_valle_respira.py -- tag=_inhala FogDist=54000 ...
"""
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.abspath(os.path.join(AQUI, "..", "..", "..", "..", ".claude", "skills", "unreal-vr", "scripts"))
sys.path.insert(0, SCRIPTS)
import preview_breath_valley as pbv  # noqa: E402

pbv.SALIDA = AQUI
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
if "solo=principal" not in " ".join(sys.argv):
    sys.argv.append("solo=principal")
pbv.main()
