# -*- coding: utf-8 -*-
"""fastvalley.py - evaluador RAPIDO de h, grad y hf sobre una grilla FIJA (x, y): precalcula las partes espaciales
(senos de las dunas, fase espacial de las olas) y en cada instante solo combina. Misma cuenta que ValleyHeightVS /
ValleyGradVS v2 (se verifica contra h_hlsl y contra valley_model.valley_grad en cada uso)."""
import math

import numpy as np

from h_hlsl import D, q5, sat

DUNAS = ((18.0, 3000.0, 1.00, 0.0, 53.0, 0.0), (101.0, 2200.0, 0.75, 1.7, 67.0, 2.1),
         (143.0, 1650.0, 0.55, 4.1, 41.0, 4.4), (232.0, 1250.0, 0.35, 2.9, 83.0, 1.3))
OLAS = ((20.0, 9000.0, 42.0, 1.00, 0.00), (175.0, 7000.0, 36.0, 0.85, 0.37),
        (255.0, 5500.0, 31.0, 0.70, 0.73), (95.0, 4000.0, 46.0, 0.40, 0.18))


def dq5(t, w):
    return 30.0 * t * t * (1.0 - t) * (1.0 - t) / w


class Grid:
    def __init__(self, x, y, p=None):
        self.p = p = dict(D if p is None else p)
        self.x = x = np.asarray(x, dtype=np.float64)
        self.y = y = np.asarray(y, dtype=np.float64)
        self.r = r = np.sqrt(x * x + y * y)
        rs = np.maximum(r, 1.0)
        self.ux, self.uy = x / rs, y / rs
        FC = max(p["FarCrest"], p["FarIn"] + 1.0)
        FB = max(p["FarBack"], FC + 1.0)
        self.FC, self.FB = FC, FB
        # envolventes
        wA = max(p["HillFull"] - p["HillNear"], 1.0)
        wB = max(p["HillEnd"] - p["HillFade"], 1.0)
        ta = sat((r - p["HillNear"]) / wA)
        tb = sat((r - p["HillFade"]) / wB)
        m1 = (r > p["HillNear"]) & (r < p["HillEnd"])
        self.env1 = np.where(m1, q5(ta) * (1 - q5(tb)), 0.0)
        self.denv1 = np.where(m1, dq5(ta, wA) * (1 - q5(tb)) - q5(ta) * dq5(tb, wB), 0.0)
        m2 = (r > p["FarIn"]) & (r < FB)
        wR = FC - p["FarIn"]
        wE = max(p["FarFull"] - p["FarIn"], 1.0)
        tr = sat((r - p["FarIn"]) / wR)
        te = sat((r - p["FarIn"]) / wE)
        self.ring = np.where(m2, q5(tr), 0.0)
        self.dring = np.where(m2, dq5(tr, wR), 0.0)
        self.envF = np.where(m2, q5(te), 0.0)
        self.denvF = np.where(m2, dq5(te, wE), 0.0)
        m3 = (r > p["SwellNear"]) & (r < FB)
        SF = max(p["SwellFar"], p["SwellNear"] + 1.0)
        wQ = SF - p["SwellNear"]
        tq = sat((r - p["SwellNear"]) / wQ)
        self.A = np.where(m3, p["SwellAmp"] * q5(tq) * r / SF, 0.0)
        self.dA = np.where(m3, p["SwellAmp"] * (dq5(tq, wQ) * r + q5(tq)) / SF, 0.0)
        tk = sat((r - FC) / (FB - FC))
        self.back = 1.0 - q5(tk)
        self.dback = -dq5(tk, FB - FC)

        # dunas (espacial)
        def campo(scale, seed):
            k = 2 * math.pi / max(scale, 0.05)
            S, Cx, Cy = [], [], []
            for (ang, lam, amp, fase, per, psi) in DUNAS:
                a = math.radians(seed + ang)
                kx, ky = k / lam * math.cos(a), k / lam * math.sin(a)
                g = kx * x + ky * y + fase
                S.append(np.sin(g))
                c = np.cos(g)
                Cx.append(c * kx)
                Cy.append(c * ky)
            return S, Cx, Cy
        self.S1, self.C1x, self.C1y = campo(p["HillScale"], p["HillSeed"])
        self.S2, self.C2x, self.C2y = campo(p["FarScale"], p["FarSeed"])
        # olas (espacial)
        iq = 1.0 / max(p["SwellScale"], 0.05)
        self.Ws = []
        for (ang, lam, per, w, c0) in OLAS:
            a = math.radians(p["SwellSeed"] + ang)
            dx, dy = math.cos(a), math.sin(a)
            ph = 2 * math.pi * ((dx * x + dy * y) * iq / lam + c0)
            kk = 2 * math.pi * iq / lam
            self.Ws.append((np.sin(ph), np.cos(ph), w, per, kk * dx, kk * dy))

    def eval(self, t, grad=True):
        p = self.p
        ms = [amp * (1.0 + p["MorphAmt"] * math.sin(2 * math.pi * ((p["MorphSpeed"] * t / per) % 1.0) + psi))
              for (_, _, amp, _, per, psi) in DUNAS]
        sig1 = sum(m * s for m, s in zip(ms, self.S1)) / 2.65
        sig2 = sum(m * s for m, s in zip(ms, self.S2)) / 2.65
        wD = max(p["DuneHigh"] - p["DuneLow"], 0.01)
        tf = sat((sig1 - p["DuneLow"]) / wD)
        tl = sat((sig2 + 0.7) / 1.9)
        f1, f2 = q5(tf), q5(tl)
        s = 0.0
        sx = 0.0
        sy = 0.0
        for (sp, cp, w, per, kx, ky) in self.Ws:
            tau = 2 * math.pi * ((p["SwellSpeed"] * t / per) % 1.0)
            ct, st = math.cos(tau), math.sin(tau)
            sn = sp * ct - cp * st          # sin(ph - tau)
            s = s + w * sn
            if grad:
                cs = cp * ct + sp * st      # cos(ph - tau)
                sx = sx + w * cs * kx
                sy = sy + w * cs * ky
        s = s / 2.95
        H = p["HillAmp"] * self.env1 * f1 + p["FarBase"] * self.ring + p["FarAmp"] * self.envF * f2 + self.A * s
        h = self.back * H
        if not grad:
            return h
        df1 = np.where((tf > 0) & (tf < 1), dq5(tf, wD), 0.0)
        df2 = np.where((tl > 0) & (tl < 1), dq5(tl, 1.9), 0.0)
        s1x = sum(m * c for m, c in zip(ms, self.C1x)) / 2.65
        s1y = sum(m * c for m, c in zip(ms, self.C1y)) / 2.65
        s2x = sum(m * c for m, c in zip(ms, self.C2x)) / 2.65
        s2y = sum(m * c for m, c in zip(ms, self.C2y)) / 2.65
        gr = p["HillAmp"] * self.denv1 * f1 + p["FarBase"] * self.dring + p["FarAmp"] * self.denvF * f2 + self.dA * s
        gx = p["HillAmp"] * self.env1 * df1 * s1x + p["FarAmp"] * self.envF * df2 * s2x + self.A * sx / 2.95
        gy = p["HillAmp"] * self.env1 * df1 * s1y + p["FarAmp"] * self.envF * df2 * s2y + self.A * sy / 2.95
        gxo = self.back * (gx + gr * self.ux) + self.dback * H * self.ux
        gyo = self.back * (gy + gr * self.uy) + self.dback * H * self.uy
        hf = sat(self.back * (self.env1 * f1 + self.envF * f2))
        return gxo, gyo, h, hf
