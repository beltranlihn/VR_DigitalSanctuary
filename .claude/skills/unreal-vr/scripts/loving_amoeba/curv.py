import numpy as np
from proto import *

def principal_curv(fn, u, eps=2e-3):
    """curvaturas principales de P(u) = r(u) u (positiva = convexa), por diferencias finitas."""
    a = np.where(np.abs(u[:, 2:3]) < 0.9, np.array([[0, 0, 1.0]]), np.array([[1.0, 0, 0]]))
    e1 = np.cross(u, a); e1 /= np.linalg.norm(e1, axis=1, keepdims=True)
    e2 = np.cross(u, e1)
    def P(s, t):
        v = u + s * e1 + t * e2
        v /= np.linalg.norm(v, axis=1, keepdims=True)
        r, _ = fn(v)
        return v * r[:, None]
    h = eps
    P00 = P(0, 0)
    Pp0, Pm0, P0p, P0m = P(h, 0), P(-h, 0), P(0, h), P(0, -h)
    Ppp, Pmm, Ppm, Pmp = P(h, h), P(-h, -h), P(h, -h), P(-h, h)
    Ps = (Pp0 - Pm0) / (2 * h); Pt = (P0p - P0m) / (2 * h)
    Pss = (Pp0 - 2 * P00 + Pm0) / h**2; Ptt = (P0p - 2 * P00 + P0m) / h**2
    Pst = (Ppp - Ppm - Pmp + Pmm) / (4 * h * h)
    n = np.cross(Ps, Pt); n /= np.linalg.norm(n, axis=1, keepdims=True)
    n *= np.sign(np.sum(n * u, 1))[:, None]           # hacia afuera
    E = np.sum(Ps * Ps, 1); F = np.sum(Ps * Pt, 1); G = np.sum(Pt * Pt, 1)
    L = -np.sum(Pss * n, 1); M = -np.sum(Pst * n, 1); N = -np.sum(Ptt * n, 1)   # convexo > 0
    det = E * G - F * F
    K = (L * N - M * M) / det
    Hm = (E * N - 2 * F * M + G * L) / (2 * det)
    disc = np.sqrt(np.maximum(Hm * Hm - K, 0))
    return Hm + disc, Hm - disc, n

if __name__ == "__main__":
    # control: esfera de radio 16 -> k1 = k2 = 1/16
    k1, k2, _ = principal_curv(lambda v: (np.full(v.shape[0], 16.0), None), fib_sphere(1000))
    print("control esfera: k*Rc =", k1.mean() * 16, k2.mean() * 16)
