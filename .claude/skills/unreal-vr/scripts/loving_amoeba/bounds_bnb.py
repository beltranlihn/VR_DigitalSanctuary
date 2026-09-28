# -*- coding: utf-8 -*-
"""Cotas EXACTAS y CERTIFICADAS del campo crudo de la ameba: ramificacion y poda de SEGUNDO ORDEN.
Para cada casquete (centro v0, radio geodesico d) y cada rama B de cada par:
    max_casquete B <= B(v0) + |grad_S B(v0)| d + 0.5 K_B d^2
con K_B = sum_k H_k K_k, K_k = cota global de la derivada segunda de phi_k a lo largo de CUALQUIER
geodesica (autovalores del hessiano esferico de una funcion zonal: f''(theta) y f'(theta) cot(theta)).
El maximo del campo es sum_j max(B_j+, B_j-): cota = suma de las cotas. Igual para el minimo.
Cubrimiento: un casquete de radio d lo cubren 4 de radio 0,72 d con centros a (+-d/2, +-d/2)."""
import numpy as np, math
import amoeba_hlsl_port as H
from proto import fib_sphere
from scipy.spatial import cKDTree
from scipy.optimize import minimize

L_ = H.LOBES
def K_lobe(kind):
    th = np.linspace(0.0, np.pi, 2_000_001)
    q = 0.5 + 0.5 * np.cos(th)
    if kind == 'P':
        d1 = 20 * q ** 9 - 5 * q ** 4; d2 = 180 * q ** 8 - 20 * q ** 3
    else:
        d1 = 6 * q ** 5; d2 = 30 * q ** 4
    f2 = d2 * np.sin(th) ** 2 / 4 - d1 * np.cos(th) / 2      # f''(theta)
    fc = -d1 * np.cos(th) / 2                                   # f'(theta) cot(theta)
    return max(np.abs(f2).max(), np.abs(fc).max()) * 1.001
KL = [K_lobe(kind) for (_, _, _, _, kind) in L_]

def branches(v):
    """valor y |gradiente esferico| de las 6 ramas (3 pares x s = +-0.45); y K de cada rama."""
    vals, gns, Ks = [], [], []
    comps = []
    for k, (D, Hk, sg, j, kind) in enumerate(L_):
        q = 0.5 + 0.5 * (v @ D)
        c = H.phi_c(kind, q)
        gv = (H.dphi_dq(kind, q) * 0.5)[:, None] * (D[None] - v * (v @ D)[:, None])
        comps.append((j, sg, Hk, c, gv, KL[k]))
    for j in range(3):
        for s in (H.SAMP, -H.SAMP):
            val = 0.0; g = 0.0; K = 0.0
            for (jj, sg, Hk, c, gv, Kk) in comps:
                if jj == j:
                    a = Hk * (0.55 + sg * s)
                    val = val + a * c; g = g + a * gv; K += abs(a) * Kk
            vals.append(val); gns.append(np.linalg.norm(g, axis=1)); Ks.append(K)
    return vals, gns, Ks

def cap_bounds(v, d):
    vals, gns, Ks = branches(v)
    ub = 0.0; lb = 0.0; hi = 0.0; lo = 0.0
    for j in range(3):
        a, b = 2 * j, 2 * j + 1
        hi = hi + np.maximum(vals[a], vals[b]); lo = lo + np.minimum(vals[a], vals[b])
        ub = ub + np.maximum(vals[a] + gns[a] * d + 0.5 * Ks[a] * d * d, vals[b] + gns[b] * d + 0.5 * Ks[b] * d * d)
        lb = lb + np.minimum(vals[a] - gns[a] * d - 0.5 * Ks[a] * d * d, vals[b] - gns[b] * d - 0.5 * Ks[b] * d * d)
    return hi, lo, ub, lb

def refine(u0, sign):
    def fobj(x):
        v = np.array([[math.cos(x[1]) * math.cos(x[0]), math.cos(x[1]) * math.sin(x[0]), math.sin(x[1])]])
        hi, lo = H.box(v)
        return -sign * (hi if sign > 0 else lo)[0]
    x0 = [math.atan2(u0[1], u0[0]), math.asin(max(-1.0, min(1.0, u0[2])))]
    r = minimize(fobj, x0, method="Nelder-Mead", options=dict(xatol=1e-13, fatol=1e-16, maxiter=10000))
    return -sign * r.fun

def bnb(sign, N0=1_000_000, tol=5e-5, seed=1):
    rng = np.random.default_rng(seed)
    G = fib_sphere(N0)
    probe = rng.normal(size=(400000, 3)); probe /= np.linalg.norm(probe, axis=1, keepdims=True)
    d = cKDTree(G).query(probe)[0].max() * 1.5                    # radio de cobertura (margen x1,5)
    hi, lo, ub, lb = cap_bounds(G, d)
    val, bnd = (hi, ub) if sign > 0 else (lo, lb)
    best = refine(G[np.argmax(val * sign)], sign)
    best = sign * max(best * sign, (val * sign).max())
    C = G[bnd * sign >= best * sign]
    print('   inicial: d %.2e, vivos %d, mejor %.9f' % (d, len(C), best), flush=True)
    it, maxcells = 0, len(C)
    while True:
        a = np.where(np.abs(C[:, 2:3]) < 0.9, np.array([[0, 0, 1.0]]), np.array([[1.0, 0, 0]]))
        e1 = np.cross(C, a); e1 /= np.linalg.norm(e1, axis=1, keepdims=True); e2 = np.cross(C, e1)
        kids = [C + (0.5 * d) * (sx * e1 + sy * e2) for sx in (-1, 1) for sy in (-1, 1)]
        C = np.concatenate(kids); C /= np.linalg.norm(C, axis=1, keepdims=True)
        d *= 0.72
        hi, lo, ub, lb = cap_bounds(C, d)
        val, bnd = (hi, ub) if sign > 0 else (lo, lb)
        best = sign * max(best * sign, (val * sign).max())
        keep = bnd * sign >= best * sign
        C = C[keep]; it += 1; maxcells = max(maxcells, len(C))
        gap = (bnd[keep] * sign).max() - best * sign if keep.any() else 0.0
        print('   nivel %2d  d %.2e  vivos %8d  hueco %.2e' % (it, d, len(C), gap), flush=True)
        if gap < tol or it > 60 or len(C) == 0:
            return best, sign * (best * sign + max(gap, 0.0)), it, maxcells

if __name__ == "__main__":
    print("K (derivada segunda geodesica max) por lobulo:", np.round(KL, 3))
    res = {}
    for sign, name in ((+1, "max"), (-1, "min")):
        best, cert, it, mc = bnb(sign)
        res[name] = (best, cert)
        print("%s crudo: alcanzado %.9f  certificado %.9f  (%d niveles, max %d casquetes vivos)" % (name, best, cert, it, mc))
    WMAX, WMAXc = res["max"]; WMINr, WMINc = res["min"]
    WN = math.floor(1.0 / WMAXc * 1e4) / 1e4
    print("\nWN   = floor(1/WMAX_cert, 4 dec) = %.4f -> maximo normalizado: certificado %.7f, alcanzado %.7f" % (WN, WN * WMAXc, WN * WMAX))
    WMINn = math.floor(WN * WMINc * 1e4) / 1e4
    print("WMIN = floor(WN*WMIN_cert, 4 dec) = %.4f (minimo normalizado: certificado %.7f, alcanzado %.7f)" % (WMINn, WN * WMINc, WN * WMINr))
