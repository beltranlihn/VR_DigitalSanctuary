# -*- coding: utf-8 -*-
"""render_lado.py - la vista de costado de cap_reposo_lado.png (camara (380,-700,70), yaw 90, pitch 0, HFOV 90):
captura real | modelo v1 | candidato v2."""
import os, sys
import numpy as np
from PIL import Image
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, AQUI)
import modelo_valle as mv, render_valle as rv
cam = (380.0, -700.0, 70.0)
ims = [Image.open(os.path.join(AQUI, "..", "cap_reposo_lado.png")).convert("RGB")]
for hf, P, fg in ((mv.h_v1, mv.P1, mv.fog_v1), (mv.h_v2, mv.P2, mv.fog_v2)):
    img, _, _ = rv.render_persp(hf, P, fg, yaw=90.0, shift_deg=0.0, cam=cam)
    ims.append(Image.fromarray((mv.srgb(img) * 255 + 0.5).astype(np.uint8)))
W, H = ims[0].size
out = Image.new("RGB", (3 * W + 12, H), (20, 20, 20))
for i, (im, t) in enumerate(zip(ims, ("CAPTURA UNREAL v1 (costado)", "MODELO v1", "CANDIDATO v2"))):
    out.paste(im, (i * (W + 6), 0)); rv.etiqueta(out, t, (i * (W + 6) + 12, 10))
out.resize((out.width // 2, out.height // 2)).save(os.path.join(AQUI, "lado_costado_cap_v1_v2.png"))
print("listo")
