# Compara la geometria final del mismo trazo sintetico (paso fijo) construida por el camino NUEVO (A, RebuildInc) y el
# VIEJO (B, FramePass+EmitPass). Uso: python compare.py A.txt B.txt
import json, sys
import numpy as np
A = json.load(open(sys.argv[1])); B = json.load(open(sys.argv[2]))
def arr(v):
    if not v: return np.zeros((0,))
    e = v[0]
    if isinstance(e, dict):
        keys = [k for k in ('x', 'y', 'z', 'r', 'g', 'b', 'a') if k in e]
        return np.array([[d[k] for k in keys] for d in v], float)
    return np.array(v, float)
print('bIncRebuild A/B:', A.get('bIncRebuild'), B.get('bIncRebuild'))
for k in ['K_Pos', 'K_SmoothPress', 'K_Size', 'K_Right', 'K_Surface', 'K_Arc', 'V_Pos', 'V_Normal', 'V_UV1', 'V_UV2', 'V_Color', 'V_Tri']:
    a, b = arr(A.get(k)), arr(B.get(k))
    if a.shape != b.shape:
        print('%-14s FORMA distinta %s vs %s' % (k, a.shape, b.shape)); continue
    d = np.abs(a - b)
    print('%-14s n=%5d  max|dif|=%.3g  medio=%.3g  (escala %.3g)' % (k, len(a), d.max() if d.size else 0, d.mean() if d.size else 0, np.abs(b).max() if b.size else 0))
# U: el viejo la escribe en V_UV.x (K_U normalizado); el nuevo la calcula el material = UV1.x / StrokeLen (TipCm 0)
uo = arr(B['V_UV'])[:, 0]; u1 = arr(A['V_UV1'])[:, 0]; L = arr(A['K_Arc'])[-1]
print('U material(TipCm=0) vs U vieja: max|dif|=%.3g' % np.abs(u1 / max(L, 0.01) - uo).max())
print('V atlas igual:', np.abs(arr(A['V_UV'])[:, 1] - arr(B['V_UV'])[:, 1]).max())
