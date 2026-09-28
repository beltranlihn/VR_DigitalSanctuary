# -*- coding: utf-8 -*-
"""Prototipo de la ameba del nucleo (V4, 2026-09-28). Render por splat de puntos con la normal ANALITICA."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os, sys

OUT = os.path.dirname(os.path.abspath(__file__))

def SS(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)

def calm(S, Ag):
    return SS(0.5, 0.9, np.clip(S, 0, 1)) * (1 - 0.7 * np.clip(Ag, 0, 1))

# ---------------- VIEJA (port exacto) ----------------
def centre_old(u, Rc, S, Ag, NA, T):
    A = 0.05 * NA * (1 + 0.4 * np.clip(Ag, 0, 1)) * (1 - 0.4 * calm(S, Ag))
    F1 = np.array([0.577, 0.331, 0.747]); F2 = np.array([-0.431, 0.794, 0.428])
    f = 2.2
    a1 = u @ F1 * f + T * 0.35
    a2 = u @ F2 * f * 1.37 - T * 0.27
    a3 = a1 * 1.9 + a2 * 0.7 + 1.3
    w = np.sin(a1) * np.sin(a2) + 0.35 * np.sin(a3)
    gw = ((np.cos(a1) * np.sin(a2) + 0.665 * np.cos(a3)) * f)[..., None] * F1 \
       + ((np.sin(a1) * np.cos(a2) + 0.245 * np.cos(a3)) * f * 1.37)[..., None] * F2
    r = Rc * (1 + A * w)
    g = Rc * A * gw
    gT = g - u * np.sum(u * g, -1, keepdims=True)
    return r, gT

# ---------------- NUEVA (parametrizable) ----------------
class Design:
    def __init__(self, D, m, H, om, ph, floor, axis, orot, A0, calmK=0.5, agK=0.4, norm=None, amax=None):
        self.amax = amax
        self.D = np.array(D, float); self.m = list(m); self.H = np.array(H, float)
        self.om = np.array(om, float); self.ph = np.array(ph, float)
        self.floor = floor; self.axis = np.array(axis, float); self.orot = orot
        self.A0 = A0; self.calmK = calmK; self.agK = agK
        self.norm = norm  # 1/WMAX

    def raw(self, up, h):
        """w crudo en el marco rotado: sum h_k (q^m - 1/(m+1)); gradiente respecto de up."""
        w = 0.0; g = 0.0
        for k in range(len(self.m)):
            q = 0.5 + 0.5 * (up @ self.D[k])
            mk = self.m[k]
            w = w + h[..., k] * (q ** mk - 1.0 / (mk + 1))
            g = g + (h[..., k] * 0.5 * mk * q ** (mk - 1))[..., None] * self.D[k]
        return w, g

    def heights(self, T):
        s = 0.5 + 0.5 * np.sin(self.om * np.asarray(T)[..., None] + self.ph)
        return self.H * (self.floor + (1 - self.floor) * s * s)

    def rot(self, v, th, sign):
        a = self.axis; c = np.cos(th)[..., None]; s = (np.sin(th) * sign)[..., None]
        return v * c + np.cross(a, v) * s + a * (v @ a)[..., None] * (1 - c)

    def amp(self, S, Ag, NA):
        a = self.A0 * NA * (1 + self.agK * np.clip(Ag, 0, 1)) * (1 - self.calmK * calm(S, Ag))
        return a if self.amax is None else np.minimum(a, self.amax)

    def centre(self, u, Rc, S, Ag, NA, T):
        T = np.asarray(T, float) * np.ones(u.shape[:-1])
        th = self.orot * T
        up = self.rot(u, th, -1.0)            # R^T u
        h = self.heights(T)
        w, gp = self.raw(up, h)
        g = self.rot(gp, th, +1.0)            # R g'
        A = self.amp(S, Ag, NA)
        r = Rc * (1 + A * self.norm * w)
        g = Rc * A * self.norm * g
        gT = g - u * np.sum(u * g, -1, keepdims=True)
        return r, gT

def fib_sphere(n):
    i = np.arange(n) + 0.5
    z = 1 - 2 * i / n
    phi = i * np.pi * (3 - np.sqrt(5))
    rr = np.sqrt(1 - z * z)
    return np.stack([rr * np.cos(phi), rr * np.sin(phi), z], -1)

def render(fn, ax, title, res=360, n=1_200_000):
    u = fib_sphere(n)
    r, gT = fn(u)
    P = u * r[:, None]
    N = u - gT / r[:, None]
    N /= np.linalg.norm(N, axis=1, keepdims=True)
    # camara en +X mirando a -X; imagen: derecha = -Y (mano derecha del usuario), arriba = +Z
    x_img = -P[:, 1]; y_img = P[:, 2]; depth = P[:, 0]
    ext = 26.0
    ix = ((x_img + ext) / (2 * ext) * res).astype(int)
    iy = ((ext - y_img) / (2 * ext) * res).astype(int)
    ok = (ix >= 0) & (ix < res) & (iy >= 0) & (iy < res)
    ix, iy, depth, N = ix[ok], iy[ok], depth[ok], N[ok]
    order = np.argsort(depth)          # los de adelante al final: sobrescriben
    img = np.full((res, res, 3), 0.08)
    L = np.array([0.55, 0.45, 0.70]); L /= np.linalg.norm(L)
    V = np.array([1.0, 0, 0])
    ndl = N @ L
    wr = np.clip((ndl + 0.3) / 1.3, 0, 1); dif = wr * wr * (3 - 2 * wr)
    Hh = (L + V); Hh /= np.linalg.norm(Hh)
    sp = np.clip(N @ Hh, 0, 1) ** 40
    amb = 0.25 + 0.15 * N[:, 2]
    base = np.array([0.95, 0.62, 0.55])
    col = base[None] * (amb + 0.8 * dif)[:, None] + 0.25 * sp[:, None]
    col = np.clip(col, 0, 1)
    img[iy[order], ix[order]] = col[order]
    ax.imshow(img); ax.set_title(title, fontsize=8); ax.axis("off")

# ---------------- NUEVA con PARES (el citoplasma fluye de un lobulo a su pareja) ----------------
class PairDesign(Design):
    """pairs = [(a,b),...]; om/ph por PAR. h_a = H_a (f + (1-f) t), h_b = H_b (f + (1-f)(1-t)),
    t = 0.5 + 0.5 sin(om T + ph)."""
    def __init__(self, D, m, H, pairs, om, ph, floor, axis, orot, A0, calmK=0.5, agK=0.4, norm=None, amax=None):
        super().__init__(D, m, H, om, ph, floor, axis, orot, A0, calmK, agK, norm, amax)
        self.pairs = pairs

    def heights(self, T):
        T = np.asarray(T, float)
        h = np.zeros(T.shape + (len(self.m),))
        f = self.floor
        for j, (a, b) in enumerate(self.pairs):
            t = 0.5 + 0.5 * np.sin(self.om[j] * T + self.ph[j])
            h[..., a] = self.H[a] * (f + (1 - f) * t)
            h[..., b] = self.H[b] * (f + (1 - f) * (1 - t))
        return h

    def cvals(self, u):
        return np.stack([(0.5 + 0.5 * (u @ self.D[k])) ** self.m[k] - 1.0 / (self.m[k] + 1) for k in range(len(self.m))], -1)

    def box(self, c):
        """max y min EXACTOS sobre el conjunto alcanzable de alturas, para cada u (c = phi - mu)."""
        f = self.floor; H = self.H
        hi = 0.0; lo = 0.0
        for (a, b) in self.pairs:
            v0 = H[a] * f * c[..., a] + H[b] * c[..., b]          # t = 0
            v1 = H[a] * c[..., a] + H[b] * f * c[..., b]          # t = 1
            hi = hi + np.maximum(v0, v1); lo = lo + np.minimum(v0, v1)
        return hi, lo

def exact_bounds(des, n=2_000_000):
    from scipy.optimize import minimize
    u = fib_sphere(n)
    hi, lo = des.box(des.cvals(u))
    out = []
    for arr, sign in ((hi, +1), (lo, -1)):
        u0 = u[(arr * sign).argmax()]
        def fobj(x):
            v = np.array([np.cos(x[1]) * np.cos(x[0]), np.cos(x[1]) * np.sin(x[0]), np.sin(x[1])])
            h_, l_ = des.box(des.cvals(v[None]))
            return -sign * (h_ if sign > 0 else l_)[0]
        x0 = [np.arctan2(u0[1], u0[0]), np.arcsin(np.clip(u0[2], -1, 1))]
        r = minimize(fobj, x0, method="Nelder-Mead", options=dict(xatol=1e-11, fatol=1e-14, maxiter=5000))
        out.append((-sign * r.fun, (arr * sign).max() * sign, u0))
    return out

class PairDesignSq(PairDesign):
    """Perfil cuadratico: h_a = H_a (f + (1-f) t^2), h_b = H_b (f + (1-f)(1-t)^2): un lobulo domina."""
    def heights(self, T):
        T = np.asarray(T, float)
        h = np.zeros(T.shape + (len(self.m),))
        f = self.floor
        for j, (a, b) in enumerate(self.pairs):
            t = 0.5 + 0.5 * np.sin(self.om[j] * T + self.ph[j])
            h[..., a] = self.H[a] * (f + (1 - f) * t * t)
            h[..., b] = self.H[b] * (f + (1 - f) * (1 - t) ** 2)
        return h

    def box(self, c):
        f = self.floor; H = self.H
        hi = 0.0; lo = 0.0
        for (a, b) in self.pairs:
            A_ = H[a] * c[..., a]; B_ = H[b] * c[..., b]
            def val(t):
                return A_ * (f + (1 - f) * t * t) + B_ * (f + (1 - f) * (1 - t) ** 2)
            den = A_ + B_
            ts = np.clip(np.where(np.abs(den) > 1e-12, B_ / np.where(np.abs(den) > 1e-12, den, 1.0), 0.0), 0, 1)
            v0, v1, vs = val(0.0), val(1.0), val(ts)
            hi = hi + np.maximum(np.maximum(v0, v1), vs); lo = lo + np.minimum(np.minimum(v0, v1), vs)
        return hi, lo

def render_views(fn, axs, title, res=260, n=600_000):
    """frente (+X), costado (+Y) y arriba (+Z)"""
    for ax, R, lab in zip(axs, [np.eye(3), np.array([[0, 1, 0], [-1, 0, 0], [0, 0, 1.0]]), np.array([[0, 0, 1], [0, 1, 0], [-1, 0, 0.0]])], ["frente", "costado", "arriba"]):
        def g(u, R=R):
            r, gT = fn(u @ R)          # evaluar en el marco rotado = girar el objeto
            return r, gT @ R.T
        render(g, ax, "%s %s" % (title, lab), res=res, n=n)

class PairDoG(PairDesign):
    """Lobulo con CUELLO: phi = (1+g) q^m - g q^(m/2) (sombrero mexicano esferico); media exacta restada."""
    def __init__(self, gam, **kw):
        super().__init__(**kw)
        self.gam = list(gam)

    def phi(self, k, q):
        m = self.m[k]; g = self.gam[k]
        return (1 + g) * q ** m - g * q ** (m // 2)

    def dphi(self, k, q):
        m = self.m[k]; g = self.gam[k]
        return (1 + g) * m * q ** (m - 1) - g * (m // 2) * q ** (m // 2 - 1)

    def mu(self, k):
        m = self.m[k]; g = self.gam[k]
        return (1 + g) / (m + 1) - g / (m // 2 + 1)

    def raw(self, up, h):
        w = 0.0; gg = 0.0
        for k in range(len(self.m)):
            q = 0.5 + 0.5 * (up @ self.D[k])
            w = w + h[..., k] * (self.phi(k, q) - self.mu(k))
            gg = gg + (h[..., k] * 0.5 * self.dphi(k, q))[..., None] * self.D[k]
        return w, gg

    def cvals(self, u):
        return np.stack([self.phi(k, 0.5 + 0.5 * (u @ self.D[k])) - self.mu(k) for k in range(len(self.m))], -1)
