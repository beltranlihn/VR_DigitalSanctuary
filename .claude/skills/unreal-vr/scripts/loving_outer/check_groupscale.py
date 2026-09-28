# -*- coding: utf-8 -*-
"""check_groupscale.py - GroupScale evaluado de todas las formas en que lo evalua la cadena (revision 2026-09-28).

LovingOuterVS pasa el indice del grupo LITERAL (el compilador pliega la cuenta en el host) y las bolsas lo leen de
GI.w en el GPU; el BP calcula en doble. Con el Hash caotico (x 43758) esas evaluaciones diferian hasta 0,96 en
GroupScale (SV = 1). La secuencia frac(0,41421356 idx + 0,33) difiere < 1e-6 en fp32/FMA/ulp y < 1,3e-3 en half.
Uso: python check_groupscale.py
"""
import numpy as np
f32, f16 = np.float32, np.float16
def frac(x): return x - np.floor(x)
worst = 0.0; rows = []
for idx in range(10):
    ex = frac(0.41421356 * idx + 0.33)
    a = frac(f32(f32(f32(idx) * f32(0.41421356)) + f32(0.33)))
    b = frac(f32(np.float64(f32(idx)) * np.float64(f32(0.41421356)) + np.float64(f32(0.33))))
    c = frac(f32(f32(np.nextafter(f32(idx), f32(100))) * f32(0.41421356)) + f32(0.33))
    h = frac(np.float64(f16(f16(f16(idx) * f16(0.41421356)) + f16(0.33))))
    vals = [ex, a, b, c]
    d32 = max(abs(v - ex) for v in vals)
    worst = max(worst, d32)
    rows.append((idx, ex, 1 + 1.2 * ex - 0.4, d32, abs(h - ex), min(ex, 1 - ex)))
for r in rows:
    print('idx %d  h %.6f  GS(SV=1) %.4f | desvio fp32/FMA/ulp %.1e | desvio half %.1e | distancia al salto de frac %.3f' % r)
print('desvio maximo de GroupScale (SV = 1) entre evaluaciones fp32/fp64/FMA/ulp: %.1e  (con el Hash viejo: 0,96)' % (1.2 * worst))
print('con 5 grupos, SV 0,5: %s' % ', '.join('%.3f' % (1 + 0.5 * (1.2 * frac(0.41421356 * i + 0.33) - 0.4)) for i in range(5)))
print('con 5 grupos, SV 1  : %s' % ', '.join('%.3f' % (1 + 1.0 * (1.2 * frac(0.41421356 * i + 0.33) - 0.4)) for i in range(5)))
g = np.array([frac(0.618034 * i + 0.2) for i in range(10)]); hh = np.array([frac(0.41421356 * i + 0.33) for i in range(10)])
print('correlacion con la secuencia _g del BP (10 grupos): %.2f' % np.corrcoef(g, hh)[0, 1])

# el Hash viejo, para comparar (debe dar desvios GRANDES: control del instrumento)
def old(idx, var):
    n = f32(idx) + f32(0.93)
    if var == 0: return frac(np.sin(float(idx + 0.93) * 12.9898 + 4.1414) * 43758.5453)
    a = f32(f32(n * f32(12.9898)) + f32(4.1414))
    return float(frac(f32(f32(np.sin(np.float64(a))) * f32(43758.5453))))
dv = max(abs(old(i, 0) - old(i, 1)) for i in range(10))
print('control: Hash viejo, float64 contra fp32 mul+add: desvio de GroupScale (SV = 1) %.2f' % (1.2 * dv))
