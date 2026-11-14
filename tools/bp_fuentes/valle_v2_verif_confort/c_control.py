# -*- coding: utf-8 -*-
"""c_control.py - controles del instrumento de flujo (b2_flow.bloques):
POSITIVO: misma escena y mismo instante, camara girada 0.5 deg a la derecha -> la imagen se corre 0.5 deg a la
izquierda: con dt = 0.5 s el instrumento tiene que dar vx = -1.00 deg/s, vy = 0, coherencia ~1.
NEGATIVO: el mismo cuadro dos veces -> 0."""
import numpy as np
import b_render_flow as b
import b2_flow as f
t = 115.7
I0 = b.luma8(b.Vista(0.0).render(t)[0])
I1 = b.luma8(b.Vista(0.5).render(t)[0])
fl = f.bloques(I0, I1, 0.5, f.row_of_el(16.0), f.row_of_el(-4.8))
m2 = fl[:, 7] >= 0.15
print("POSITIVO: bloques %d (2D %d); vx 2D mediana %.3f (p10 %.3f, p90 %.3f) deg/s; vy 2D mediana %.3f; "
      "vn mediana %.3f; coherencia 2D %.2f" % (len(fl), m2.sum(), np.median(fl[m2, 2]), np.percentile(fl[m2, 2], 10),
                                             np.percentile(fl[m2, 2], 90), np.median(fl[m2, 3]), np.median(fl[:, 4]),
                                             np.hypot(fl[m2, 2].mean(), fl[m2, 3].mean()) / np.hypot(fl[m2, 2], fl[m2, 3]).mean()))
print("   todos los bloques (sin filtro de apertura): vx mediana %.3f, p10 %.3f, p90 %.3f" % (
    np.median(fl[:, 2]), np.percentile(fl[:, 2], 10), np.percentile(fl[:, 2], 90)))
fl0 = f.bloques(I0, I0, 0.5, f.row_of_el(16.0), f.row_of_el(-4.8))
print("NEGATIVO: bloques %d; |v| max %.4f deg/s" % (len(fl0), np.hypot(fl0[:, 2], fl0[:, 3]).max()))
m2 = fl0[:, 7] >= 0.15
print("NEGATIVO: vn max %.4f deg/s; 2D |v| max %.4f deg/s; vn p99 %.4f" % (
    fl0[:, 4].max(), np.hypot(fl0[m2, 2], fl0[m2, 3]).max() if m2.any() else 0, np.percentile(fl0[:, 4], 99)))
m2p = fl[:, 7] >= 0.15
# en el positivo, error de la componente normal contra la esperada (proyeccion de (-1, 0) sobre e1 no se guarda):
print("POSITIVO: bloques 2D con |vx+1| > 0.3: %d de %d" % (np.sum(np.abs(fl[m2p, 2] + 1) > 0.3), m2p.sum()))
