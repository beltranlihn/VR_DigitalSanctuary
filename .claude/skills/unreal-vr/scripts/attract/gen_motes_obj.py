# gen_motes_obj.py (2026-11-04) - malla de las particulas de un chorro de Attracting (BP_AttractStreams_SC).
# K quads apilados en X: el quad k tiene sus 4 vertices en x = k (indice de la particula), y,z = +-1 (esquina).
# El material (M_AttractMote_SC) lee LocalPosition.x = k y la UV = esquina, y mueve cada quad a su lugar por WPO.
# Z-up, cm. UV con parametrizacion completa por quad (evita el aviso modal de tangentes nulas, gotcha 303).
import sys
K = int(sys.argv[1]) if len(sys.argv) > 1 else 256
L = ['# attract motes: %d quads, x = particle index, y/z = corner (+-1), Z-up' % K]
for k in range(K):
    for (y, z) in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        L.append('v %d.00000 %d.00000 %d.00000' % (k, y, z))
for k in range(K):
    for (u, v) in ((0, 0), (1, 0), (1, 1), (0, 1)):
        L.append('vt %d.00000 %d.00000' % (u, v))
for k in range(K):
    for _ in range(4):
        L.append('vn 1.00000 0.00000 0.00000')
for k in range(K):
    b = 4 * k + 1
    a, c, d, e = b, b + 1, b + 2, b + 3
    L.append('f %d/%d/%d %d/%d/%d %d/%d/%d' % (a, a, a, c, c, c, d, d, d))
    L.append('f %d/%d/%d %d/%d/%d %d/%d/%d' % (a, a, a, d, d, d, e, e, e))
open('SM_AttractMotes_SC.obj', 'w').write('\n'.join(L) + '\n')
print('ok', K, 'quads', 4 * K, 'verts', 2 * K, 'tris')
