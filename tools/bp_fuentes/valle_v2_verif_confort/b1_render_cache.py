# -*- coding: utf-8 -*-
"""b1_render_cache.py - renderiza y GUARDA los cuadros (luma sRGB 8 bits en float, distancia) para el analisis de
flujo: yaw 0/90/180/270, 3 instantes, dt 0 / 0.25 / 0.5 / 5 s. Usa el trazador de b_render_flow.py."""
import os
import numpy as np
from PIL import Image
import b_render_flow as b
AQUI = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(11)
T0S = [float(v) for v in rng.uniform(0, 900, 3)]
DTS = (0.0, 0.25, 0.5, 5.0)
for yaw in (0.0, 90.0, 180.0, 270.0):
    vis = b.Vista(yaw)
    L = np.zeros((len(T0S), len(DTS), b.H, b.W), np.float32)
    Dm = np.zeros((len(T0S), b.H, b.W), np.float32)
    for i, t0 in enumerate(T0S):
        for j, dt in enumerate(DTS):
            img, dist = vis.render(t0 + dt)
            L[i, j] = b.luma8(img)
            if j == 0:
                Dm[i] = dist
                if i == 0:
                    Image.fromarray(np.clip(np.round(255 * b.vm.srgb(img)), 0, 255).astype(np.uint8)).save(
                        os.path.join(AQUI, "c_vista_yaw%d_t0.png" % int(yaw)))
        print("yaw", yaw, "t0", t0, "ok", flush=True)
    np.savez_compressed(os.path.join(AQUI, "frames_yaw%d.npz" % int(yaw)), L=L, D=Dm, t0s=np.array(T0S), dts=np.array(DTS))
print("LISTO")
