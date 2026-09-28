# -*- coding: utf-8 -*-
"""Alcance del sustituto de Surr desde G (una bola, sin filetes): rayos de la tapa desde G girando de perpendicular
(sa=0) a axial (sa=1) con re = lerp(e, x, sa^2), y rayos perpendiculares desde puntos del eje antes de G.
Devuelve max alcance / (|o| + r + gap) en funcion de hug, y el factor k(hug) tal que alcance <= k |o| + r + gap."""
import numpy as np
rs = np.linspace(0, 1, 11)
for hug in (0.0, 0.25, 0.5, 0.8, 1.0):
    kmax = 0.0
    for r in (1.0,):
        for gapf in (0.3, 0.6, 0.9):
            gap = gapf * r
            for o in np.linspace(0.05, 0.85, 17) * r:
                for phi in np.linspace(0, np.pi, 73):          # angulo del desfase respecto del eje
                    a = o * np.cos(phi); v = o * abs(np.sin(phi))
                    R = r + gap + (1 - hug) * v; Q = (hug * v) ** 2
                    for cosn in np.linspace(-1, 1, 41):          # azimut relativo al desfase: p = q . n
                        p = hug * v * cosn
                        e = p + np.sqrt(max(R * R - Q + p * p, 0))
                        x = np.sqrt(max(R * R - Q, 0))
                        sa = np.linspace(0, 1, 60); s2 = sa * sa; ca = np.sqrt(1 - s2)
                        re = e + (x - e) * s2
                        disc = re * re - a * a * ca * ca
                        m = a * sa + np.sqrt(np.maximum(disc, 0))
                        reach = np.max(np.where(disc >= 0, m, 0))
                        k = (reach - r - gap) / o
                        kmax = max(kmax, k)
    print("hug=%.2f  k_max=%.3f   (esfera exacta = 1, cota sqrt2 = 1.414)" % (hug, kmax))
