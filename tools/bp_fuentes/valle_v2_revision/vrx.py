# -*- coding: utf-8 -*-
"""vrender.py - render POR PIXEL (independiente del preview Gouraud de Blender) del valle v1 y v2.

Metodo: por columna de pixeles (camara con pitch 0 o proyeccion cilindrica) el rayo recorre un perfil RADIAL del
campo de alturas continuo; el primer cruce de la pendiente del rayo con s(rho) = (h - ez)/rho da el punto visto.
Ahi se evalua el sombreado del modelo (v2: valley_model.suelo; v1: port numpy de la v1 del respaldo) con el gradiente
continuo -> es lo que hace el GPU por pixel (salvo la interpolacion del gradiente entre vertices).
Solo lee los modelos; escribe solo en esta carpeta.
"""
import importlib.util
import math
import os
import sys
import types

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
REPO = "C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal"
SCRIPTS = os.path.join(REPO, ".claude", "skills", "unreal-vr", "scripts")
V1DIR = os.path.join(REPO, "VR_Test", "Saved", "ClaudeScripts", "valle_v1_backup")

sys.path.insert(0, SCRIPTS)
sys.path.insert(0, AQUI)
import vexp as vm  # noqa: E402


def _cargar_v1():
    # stubs de bpy/mathutils: solo usamos las funciones numpy del preview v1
    bpy = types.ModuleType("bpy")
    mu = types.ModuleType("mathutils")
    mu.Vector = object
    mu.Euler = object
    sys.modules.setdefault("bpy", bpy)
    sys.modules.setdefault("mathutils", mu)
    spec_g = importlib.util.spec_from_file_location("gen_breath_valley_v1", os.path.join(V1DIR, "gen_breath_valley.py"))
    g = importlib.util.module_from_spec(spec_g)
    spec_g.loader.exec_module(g)
    sys.modules["gen_breath_valley"] = g          # el preview v1 hace "import gen_breath_valley as gen"
    spec = importlib.util.spec_from_file_location("preview_v1", os.path.join(V1DIR, "preview_breath_valley.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    del sys.modules["gen_breath_valley"]
    return m, g


V1, G1 = _cargar_v1()


class Modelo:
    def __init__(self, cual, q=None):
        self.cual = cual
        if cual == "v1":
            self.rmax = G1.R_MAX * 100.0
        else:
            self.rmax = 64000.0
            self.q = vm.params() if q is None else q

    def h(self, x, y, t):
        if self.cual == "v1":
            return V1.valley_grad(x, y, t)[2]
        return vm.valley_grad(x, y, t, self.q)[2]

    def color_suelo(self, x, y, t, cam):
        if self.cual == "v1":
            c, h, O = V1.suelo(x.ravel(), y.ravel(), t, np.asarray(cam, float))
            return c, h
        gx, gy, h, hf = vm.valley_grad(x, y, t, self.q)
        return vm.suelo(x, y, gx, gy, h, hf, cam, self.q), h

    def color_cielo(self, dv):
        if self.cual == "v1":
            return V1.cielo(dv.reshape(-1, 3), True)
        return vm.cielo(dv, self.q)


def srgb(c):
    c = np.clip(c, 0.0, 1.0)
    return np.where(c <= 0.0031308, 12.92 * c, 1.055 * np.power(c, 1.0 / 2.4) - 0.055)


def render_cols(mod, eye, az_cols, slopes, t, rho_min=5.0, J=4000, chunk=96, esfera=None):
    """az_cols: (W,) azimut UE en grados de cada columna; slopes: (H, W) pendiente dz/drho de cada pixel.
    Devuelve color lineal (H, W, 3), distancia horizontal al punto visto (H, W) (inf = cielo) y h del punto."""
    Hh, W = slopes.shape
    out = np.zeros((Hh, W, 3))
    dist = np.full((Hh, W), np.inf)
    hh = np.zeros((Hh, W))
    # distancia horizontal maxima: hasta salir del disco de la malla (el ojo puede no estar en el centro)
    rho = rho_min * np.power((mod.rmax + np.hypot(eye[0], eye[1]) + 10.0) / rho_min, np.arange(J) / (J - 1.0))
    for c0 in range(0, W, chunk):
        az = np.radians(az_cols[c0:c0 + chunk])
        X = eye[0] + rho[:, None] * np.cos(az)[None, :]
        Y = eye[1] + rho[:, None] * np.sin(az)[None, :]
        Hs = mod.h(X, Y, t)
        fuera = np.hypot(X, Y) > mod.rmax
        s = np.where(fuera, -np.inf, (Hs - eye[2]) / rho[:, None])
        M = np.maximum.accumulate(s, axis=0)
        for k in range(az.size):
            m = slopes[:, c0 + k]
            j = np.searchsorted(M[:, k], m, side="left")
            hit = j < J
            jj = np.clip(j, 1, J - 1)
            s0 = s[jj - 1, k]
            s1 = s[jj, k]
            fr = np.where(np.isfinite(s0) & (s1 > s0), (m - s0) / np.where(s1 > s0, s1 - s0, 1.0), 1.0)
            fr = np.clip(fr, 0.0, 1.0)
            rh = rho[jj - 1] + fr * (rho[jj] - rho[jj - 1])
            rh = np.where(j == 0, rho[0], rh)
            dist[hit, c0 + k] = rh[hit]
    # sombreado del suelo por pixel
    AZ = np.broadcast_to(np.radians(az_cols)[None, :], (Hh, W))
    suelo = np.isfinite(dist)
    xs = eye[0] + dist[suelo] * np.cos(AZ[suelo])
    ys = eye[1] + dist[suelo] * np.sin(AZ[suelo])
    for i0 in range(0, xs.size, 400000):
        c, h = mod.color_suelo(xs[i0:i0 + 400000], ys[i0:i0 + 400000], t, eye)
        idx = np.flatnonzero(suelo.ravel())[i0:i0 + 400000]
        out.reshape(-1, 3)[idx] = c.reshape(-1, 3)
        hh.reshape(-1)[idx] = np.asarray(h).ravel()
    # cielo
    cielo = ~suelo
    el = np.arctan(slopes[cielo])
    dv = np.stack([np.cos(el) * np.cos(AZ[cielo]), np.cos(el) * np.sin(AZ[cielo]), np.sin(el)], -1)
    out[cielo] = mod.color_cielo(dv).reshape(-1, 3)
    # esfera de referencia del preview (opcional)
    if esfera is not None:
        C, R = np.asarray(esfera[0], float), float(esfera[1])
        el_all = np.arctan(slopes)
        D = np.stack([np.cos(el_all) * np.cos(AZ), np.cos(el_all) * np.sin(AZ), np.sin(el_all)], -1)
        oc = eye - C
        b = (D * oc).sum(-1)
        cc = (oc * oc).sum() - R * R
        disc = b * b - cc
        tt = -b - np.sqrt(np.maximum(disc, 0.0))
        horiz = tt * np.cos(el_all)
        ok = (disc > 0) & (tt > 0) & (horiz < dist)
        P = eye + D[ok] * tt[ok][:, None]
        n = (P - C) / R
        Lm = np.array([-0.45, -0.25, 0.86])   # igual que el preview (ya en ejes UE)
        Lm = Lm / np.linalg.norm(Lm)
        wr = np.clip((n @ Lm + 0.8) / 1.8, 0, 1)
        out[ok] = vm.lerp(np.array([0.45, 0.50, 0.80]), np.array([0.92, 0.945, 1.0]), np.sqrt(wr)[:, None])
        dist[ok] = horiz[ok]
    return out, dist, hh


def camara(W, Hh, hfov, yaw, pitch=0.0):
    """Camara pinhole con pitch 0 (exacto) -> azimut por columna y pendiente por pixel."""
    f = (W / 2.0) / math.tan(math.radians(hfov / 2.0))
    a = (np.arange(W) + 0.5 - W / 2.0) / f
    b = (Hh / 2.0 - (np.arange(Hh) + 0.5)) / f
    alpha = np.degrees(np.arctan(a))
    # pitch pequeno: aproximacion (rota la pendiente); pitch 0 es exacto
    pb = math.radians(pitch)
    bb = (b[:, None] * math.cos(pb) + math.sin(pb)) / (math.cos(pb) - b[:, None] * math.sin(pb))
    slopes = bb * np.cos(np.radians(alpha))[None, :]
    return yaw + alpha, slopes, f


def cilindrica(az0, az1, el0, el1, ppd):
    W = int(round((az1 - az0) * ppd))
    Hh = int(round((el1 - el0) * ppd))
    az = az0 + (np.arange(W) + 0.5) / ppd
    el = el1 - (np.arange(Hh) + 0.5) / ppd
    slopes = np.broadcast_to(np.tan(np.radians(el))[:, None], (Hh, W)).copy()
    return az, slopes, el


def guardar(ruta, lin):
    from PIL import Image
    Image.fromarray(np.round(255.0 * srgb(lin)).astype(np.uint8)).save(ruta)


def Y(lin):
    return 0.2126 * lin[..., 0] + 0.7152 * lin[..., 1] + 0.0722 * lin[..., 2]
