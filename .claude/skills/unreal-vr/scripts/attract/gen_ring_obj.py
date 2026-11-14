# gen_ring_obj.py (2026-11-04) - anillo plano para las ondas de Attracting (BP_AttractCall_SC). Corona de radio 0,99..1,01
# en el plano XY (Z-up), N segmentos; UV.x = fraccion del angulo, UV.y = 0 adentro / 1 afuera. El material
# (M_AttractRing_SC) pone cada vertice en radio R +- W/2 por WPO, asi el ancho queda en cm de mundo al crecer.
import math, sys
N = int(sys.argv[1]) if len(sys.argv) > 1 else 160
L = ['# attract ring: %d segments, radius 0.99..1.01, Z-up' % N]
for i in range(N + 1):
    a = 2 * math.pi * i / N
    for r in (0.99, 1.01):
        L.append('v %.6f %.6f 0.000000' % (r * math.cos(a), r * math.sin(a)))
for i in range(N + 1):
    for v in (0, 1):
        L.append('vt %.6f %d.000000' % (i / N, v))
for i in range(N + 1):
    for _ in range(2):
        L.append('vn 0.000000 0.000000 1.000000')
for i in range(N):
    a, b, c, d = 2 * i + 1, 2 * i + 2, 2 * i + 4, 2 * i + 3
    L.append('f %d/%d/%d %d/%d/%d %d/%d/%d' % (a, a, a, b, b, b, c, c, c))
    L.append('f %d/%d/%d %d/%d/%d %d/%d/%d' % (a, a, a, c, c, c, d, d, d))
open('SM_AttractRing_SC.obj', 'w').write('\n'.join(L) + '\n')
print('ok', N, 'segments', 2 * (N + 1), 'verts', 2 * N, 'tris')
