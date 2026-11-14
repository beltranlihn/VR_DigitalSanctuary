# -*- coding: utf-8 -*-
"""air_model.py - modelo de referencia del ALIENTO VISIBLE (propuesta 2026-09-28, docs/IDEAS-RESPIRACION-ENTORNO-2026-09-28.md).

Es la cuenta que harian el BP (paso por cuadro: transporte integrado, frente, envolventes, marco con retardo) y el
vertex shader (posicion de cada mota, sin estado). Sirve para: (1) dibujar las motas sobre los renders del valle,
(2) medir confort y costo ANTES de construir nada (distancia a los ojos, elevacion, velocidad angular, cobertura).

Ejes UE: X adelante, Y derecha, Z arriba, cm. Sin Unreal: es Python puro (numpy).
"""
import math

import numpy as np

AIR = dict(
    # boca respecto de la camara (ejes de la cabeza)
    MouthDown=9.0, MouthFwd=6.0,
    # marco del aire con retardo (el origen de lo inhalado y el destino de lo exhalado viven aqui)
    LagPos=0.30, LagRot=0.80, HoldLagMul=3.0, PitchFollow=0.5, PitchMin=-35.0, PitchMax=10.0,
    # inhalar: motas que convergen a la boca desde un volumen frente a la cara
    NIn=768, InTilt=18.0, InNear=30.0, InFar=85.0, InSpreadH=30.0, InSpreadV=12.0, InAccel=1.35, InSwirl=35.0,
    InAlpha=0.45, InSizeCm=0.22, InColor=(0.80, 0.85, 1.00), TravelIn=0.9,
    # exhalar: pluma que sale de la boca, frena, se abre, sube apenas y se desvanece
    NOut=1280, OutTilt=12.0, PlumeLen=110.0, OutDecel=1.8, OutSpread=16.0, OutFlat=0.6, OutR0=1.5, Buoy=10.0,
    Turb=3.0, OutAlpha=0.50, OutSizeCm=0.28, OutGrow=0.8, OutColor=(1.00, 0.84, 0.80), TravelOut=0.8,
    FrontSoft=0.08, OutEmerge0=0.02, OutEmerge1=0.12, OutStart=15.0, FrontLead=1.6,
    # confort (valen para las dos corrientes)
    NearMin=22.0, NearFull=36.0, ElevMax=-4.0, ElevSoft=6.0, MinDeg=0.12, MaxDeg=0.40, MaxDegOut=0.55, SpeedFade0=20.0, SpeedFade1=40.0,
    # envolventes (BP)
    RiseTau=0.30, HoldTau=2.5, CrossTau=0.5, VOn=0.05,
)


def sat(x):
    return np.clip(x, 0.0, 1.0)


def smoothstep(a, b, x):
    t = sat((np.asarray(x, dtype=np.float64) - a) / (b - a))
    return t * t * (3.0 - 2.0 * t)


def frac(x):
    return x - np.floor(x)


def head_basis(yaw, pitch):
    """F, R, U de una cabeza con yaw/pitch en grados (roll 0)."""
    y, p = math.radians(yaw), math.radians(pitch)
    F = np.array([math.cos(p) * math.cos(y), math.cos(p) * math.sin(y), math.sin(p)])
    R = np.array([-math.sin(y), math.cos(y), 0.0])
    U = np.array([-math.sin(p) * math.cos(y), -math.sin(p) * math.sin(y), math.cos(p)])
    return F, R, U


def mouth(eye, yaw, pitch, q=AIR):
    F, R, U = head_basis(yaw, pitch)
    return eye + F * q["MouthFwd"] - U * q["MouthDown"]


class Seeds:
    """Los numeros al azar de cada quad (en Unreal van en UV1/UV2 de la malla)."""

    def __init__(self, q=AIR, seed=7):
        rng = np.random.default_rng(seed)
        self.nin, self.nout = int(q["NIn"]), int(q["NOut"])
        n = self.nin + self.nout
        self.e = rng.random(n)                       # desfase en la cinta
        v = rng.random(n)
        w = rng.random(n)
        r = np.sqrt(v)
        self.a = r * np.cos(2 * np.pi * w)           # disco unitario
        self.b = r * np.sin(2 * np.pi * w)
        self.u = rng.random(n)                       # profundidad (inhalar)
        self.ph = rng.random((n, 3))                 # fases de la turbulencia
        self.j = rng.normal(0.0, 1.0, (n, 3))        # llegada a la boca (jitter)


class BPState:
    """Lo que el BP integra por cuadro y empuja al MID (4 float4, una sola funcion, el mismo cuadro)."""

    def __init__(self, eye, yaw, pitch, q=AIR):
        self.q = q
        self.Tin = 0.0
        self.Tout = 0.0
        self.Fout = 0.0
        self.Ein = 0.0
        self.Eout = 0.0
        self.Mlag = mouth(eye, yaw, pitch, q)
        self.yawLag = yaw
        self.pitchLag = pitch

    def step(self, dt, dS, eye, yaw, pitch, on=1.0):
        q = self.q
        inh = dS > q["VOn"]
        exh = dS < -q["VOn"]
        still = not (inh or exh)
        self.rateIn = 0.5 * q["TravelIn"] * max(dS, 0.0)
        self.rateOut = 0.5 * q["TravelOut"] * max(-dS, 0.0)
        self.Tin = (self.Tin + self.rateIn * dt) % 1.0
        dOut = 0.5 * q["TravelOut"] * max(-dS, 0.0) * dt
        self.Tout = (self.Tout + dOut) % 1.0
        self.Fout = min(self.Fout + q["FrontLead"] * dOut, 1.5)

        def env(E, active, crossing):
            if active:
                tgt, tau = 1.0, q["RiseTau"]
            elif crossing:
                tgt, tau = 0.0, q["CrossTau"]
            else:
                tgt, tau = 0.0, q["HoldTau"]
            return E + (tgt - E) * (1.0 - math.exp(-dt / tau))

        self.Ein = env(self.Ein, inh, exh) * 1.0
        self.Eout = env(self.Eout, exh, inh) * 1.0
        if self.Eout < 0.01 and not exh:
            self.Fout = 0.0                           # el frente se reinicia solo cuando la pluma es invisible
        M = mouth(eye, yaw, pitch, q)
        self.Mlag = self.Mlag + (M - self.Mlag) * (1.0 - math.exp(-dt / q["LagPos"]))
        tr = q["LagRot"] * (q["HoldLagMul"] if still else 1.0)
        k = 1.0 - math.exp(-dt / tr)
        dy = (yaw - self.yawLag + 180.0) % 360.0 - 180.0
        self.yawLag += dy * k
        self.pitchLag += (pitch - self.pitchLag) * k
        self.on = on


def _axis(yaw, pitch):
    y, p = math.radians(yaw), math.radians(pitch)
    A = np.array([math.cos(p) * math.cos(y), math.cos(p) * math.sin(y), math.sin(p)])
    Rh = np.array([-math.sin(y), math.cos(y), 0.0])
    Uh = np.cross(A, Rh) * -1.0                       # perpendicular "arriba" del eje (mano izquierda de UE)
    if Uh[2] < 0:
        Uh = -Uh
    return A, Rh, Uh


def motes(st, sd, eye, yaw, pitch, q=AIR):
    """Posicion, alfa, tamano angular (grados) y color de cada mota: lo que calcularia el vertex shader."""
    on = getattr(st, "on", 1.0)
    F, R, U = head_basis(yaw, pitch)
    Mx = mouth(eye, yaw, pitch, q)
    pa = float(np.clip(q["PitchFollow"] * st.pitchLag, q["PitchMin"], q["PitchMax"]))
    n_in = sd.nin
    P = np.zeros((sd.nin + sd.nout, 3))
    alpha = np.zeros(sd.nin + sd.nout)
    size = np.zeros(sd.nin + sd.nout)
    grow = np.zeros(sd.nin + sd.nout)
    s_all = np.zeros(sd.nin + sd.nout)

    # --- inhalar: cinta que va del volumen de adelante (marco con retardo) a la boca EXACTA ---
    i = slice(0, n_in)
    A, Rh, Uh = _axis(st.yawLag, pa - q["InTilt"])
    s = frac(sd.e[i] + st.Tin)
    d0 = q["InNear"] + (q["InFar"] - q["InNear"]) * np.power(sd.u[i], 0.8)
    w = np.power(s, q["InAccel"])
    ang = np.radians(q["InSwirl"]) * w
    ca, sa = np.cos(ang), np.sin(ang)
    a2 = sd.a[i] * ca - sd.b[i] * sa
    b2 = sd.a[i] * sa + sd.b[i] * ca
    start = (st.Mlag[None, :] + A[None, :] * d0[:, None]
             + Rh[None, :] * (d0 * math.tan(math.radians(q["InSpreadH"])) * a2)[:, None]
             + Uh[None, :] * (d0 * math.tan(math.radians(q["InSpreadV"])) * b2)[:, None])
    end = Mx[None, :] + sd.j[i] * 1.0
    P[i] = start + (end - start) * w[:, None]
    tan_i = end - start
    vlen_i = np.linalg.norm(tan_i, axis=1) * q["InAccel"] * np.power(np.maximum(s, 1e-4), q["InAccel"] - 1.0)         * getattr(st, "rateIn", 0.0)
    tan_i = tan_i / np.maximum(np.linalg.norm(tan_i, axis=1), 1e-6)[:, None]
    alpha[i] = q["InAlpha"] * smoothstep(0.0, 0.2, s) * st.Ein * on
    size[i] = q["InSizeCm"]
    s_all[i] = s

    # --- exhalar: pluma que sale de la boca EXACTA y se abre en el marco con retardo ---
    o = slice(n_in, None)
    A, Rh, Uh = _axis(st.yawLag, pa - q["OutTilt"])
    s = frac(sd.e[o] + st.Tout)
    x = q["OutStart"] + (q["PlumeLen"] - q["OutStart"]) * (1.0 - np.power(1.0 - s, q["OutDecel"]))
    rad = q["OutR0"] + x * math.tan(math.radians(q["OutSpread"]))
    base = Mx[None, :] + (st.Mlag - Mx)[None, :] * smoothstep(0.0, 0.6, s)[:, None]
    tu = st.Tout
    turb = q["Turb"] * s[:, None] * np.stack([
        np.sin(2 * np.pi * (3.0 * tu + sd.ph[o, 0])),
        np.sin(2 * np.pi * (2.0 * tu + sd.ph[o, 1])),
        np.sin(2 * np.pi * (3.0 * tu + sd.ph[o, 2]))], axis=1)
    P[o] = (base + A[None, :] * x[:, None] + Rh[None, :] * (rad * sd.a[o])[:, None]
            + Uh[None, :] * (rad * q["OutFlat"] * sd.b[o])[:, None]
            + np.array([0.0, 0.0, 1.0])[None, :] * (q["Buoy"] * s * s)[:, None] + turb)
    vlen_o = (q["PlumeLen"] - q["OutStart"]) * q["OutDecel"] * np.power(1.0 - s, q["OutDecel"] - 1.0)         * getattr(st, "rateOut", 0.0)
    front = sat((st.Fout - s) / q["FrontSoft"])
    alpha[o] = (q["OutAlpha"] * front * smoothstep(q["OutEmerge0"], q["OutEmerge1"], s)
                * (1.0 - smoothstep(0.5, 1.0, s)) * st.Eout * on)
    size[o] = q["OutSizeCm"] * (1.0 + q["OutGrow"] * s)
    grow[o] = 1.0
    s_all[o] = s

    # --- confort: nada cerca de los ojos, nada por encima de la banda baja ---
    D = P - eye[None, :]
    dist = np.linalg.norm(D, axis=1)
    alpha *= smoothstep(q["NearMin"], q["NearFull"], dist)
    sin_el = (D @ U) / np.maximum(dist, 1e-6)
    el = np.degrees(np.arcsin(np.clip(sin_el, -1, 1)))
    alpha *= 1.0 - smoothstep(q["ElevMax"] - q["ElevSoft"], q["ElevMax"], el)
    # velocidad angular transversal estimada (analitica: la tangente del camino x la tasa del BP); lo rapido se apaga
    Dn = D / np.maximum(dist, 1e-6)[:, None]
    tang = np.zeros_like(P)
    tang[:n_in] = tan_i
    tsp = math.tan(math.radians(q["OutSpread"]))
    tang[n_in:] = (A[None, :] + tsp * (sd.a[o][:, None] * Rh[None, :] + q["OutFlat"] * sd.b[o][:, None] * Uh[None, :]))
    # (la subida 2*Buoy*s y la turbulencia son lentas frente al chorro: se ignoran en la estimacion)
    vlen = np.concatenate([vlen_i, vlen_o])
    tl = np.linalg.norm(tang, axis=1)
    vlen = vlen * tl
    tang = tang / np.maximum(tl, 1e-6)[:, None]
    omega = np.degrees(vlen * np.linalg.norm(np.cross(tang, Dn), axis=1) / np.maximum(dist, 1e-6))
    alpha *= 1.0 - smoothstep(q["SpeedFade0"], q["SpeedFade1"], omega)
    angdeg = np.degrees(2.0 * np.arctan(0.5 * size / np.maximum(dist, 1e-6)))
    maxd = np.where(grow > 0, q["MaxDegOut"], q["MaxDeg"])
    angdeg = np.clip(angdeg, q["MinDeg"], maxd)
    col = np.zeros((P.shape[0], 3))
    col[:n_in] = np.array(q["InColor"])
    col[n_in:] = np.array(q["OutColor"])
    return dict(P=P, alpha=alpha, ang=angdeg, col=col, dist=dist, el=el, s=s_all, n_in=n_in)


# ---------------------------------------------------------------------------------------------
# Respiracion sintetica: pacer 4-3-4-3 seguido por el usuario, con la llegada suave del seguidor
# ---------------------------------------------------------------------------------------------
def breath_S(t, tin=4.0, h1=3.0, tout=4.0, h2=3.0, lag=0.4):
    """S en [-1, 1] (+1 = tope de la inhalacion) y la fase del pacer (0 in, 1 h1, 2 out, 3 h2) en t.
    Perfil fisiologico: inhalacion de medio coseno (flujo maximo a la mitad); exhalacion pasiva con el flujo maximo al
    principio (decae exponencial). Suavizado en los bordes para imitar la llegada del seguidor del rig."""
    T = tin + h1 + tout + h2
    tt = (t - lag) % T

    def ss5(p):
        p = min(max(p, 0.0), 1.0)
        return p * p * p * (p * (6 * p - 15) + 10)

    def exh(p):
        p = min(max(p, 0.0), 1.0)
        a = 3.0
        base = (1.0 - math.exp(-a * p)) / (1.0 - math.exp(-a))
        on = ss5(p / 0.12) if p < 0.12 else 1.0      # arranque del seguidor (~0,5 s)
        return base * on + ss5(p) * (1.0 - on)
    if tt < tin:
        return -1.0 + (1.0 - math.cos(math.pi * ss5(tt / tin) * 0.5 + math.pi * (tt / tin) * 0.5)), 0
    if tt < tin + h1:
        return 1.0, 1
    if tt < tin + h1 + tout:
        return 1.0 - 2.0 * exh((tt - tin - h1) / tout), 2
    return -1.0, 3
