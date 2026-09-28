# -*- coding: utf-8 -*-
"""breath_air_model.py - MODELO DE REFERENCIA del ALIENTO VISIBLE (Entering, 2026-09-28, rev. 2).

Plan: docs/PLAN-RESPIRACION-ENTORNO-2026-09-28.md. Es la cuenta EXACTA que hacen:
  - el vertex shader  scripts/hlsl/BreathAirVS.hlsl  (posicion, alfa y tamano de cada mota; sin estado)
  - el pixel shader   scripts/hlsl/BreathAirPS.hlsl  (punto suave premultiplicado)
  - el Blueprint      BP_BreathAir_SC (AirStep: velocidad filtrada, modo con histeresis, transporte integrado, frente,
                      envolventes, ritmo con latch, marco con retardo, apagado al girar la cabeza, presencia suavizada)
                      -> scripts/breath_air.dsl es la traduccion de AirBP.step() linea a linea.
Lo usan: hlsl/BreathAir_check.py (HLSL = este modelo, confort, mutaciones, V invertida), gen_breath_air.py (las
semillas de la malla salen de seeds() y se codifican con encode_uv()), sim_breath_air.py y dsl_sim.py.

EJES Y ESPACIOS (los de Unreal: X adelante, Y derecha, Z arriba, cm).
  - El componente AirMesh cuelga de la CAMARA del pawn con transform relativo identidad: su espacio LOCAL es el
    espacio de la camara (X = hacia donde mira, Z = arriba de la cabeza). El vertex shader trabaja todo en ese espacio.
  - El BP integra en el MUNDO (la boca con retardo y el giro con retardo tienen que quedarse en el mundo) y empuja
    al material todo convertido a local de la camara (InverseTransformLocation / InverseTransformDirection).
  - CamL = la camara de CADA ojo en local (Transform Position World->Local de CameraPositionWS): en multiview el
    VS corre una vez por ojo. En este modelo, (0, +-IPD/2, 0).

SEMILLAS EN LA MALLA, INVARIANTES A LA V INVERTIDA (gotcha 302: el importador FBX de Unreal entrega V como 1 - V).
  Todo lo que no es simetrico va en U; en V solo van numeros uniformes independientes o valores codificados como
  (x + 1) / 2 de algo simetrico: con la V invertida llega 1 - v, que es otra muestra de la MISMA distribucion.
    UV1 = (e, u)                 e estratificado (U); u uniforme (V: 1 - u es uniforme)
    UV2 = (a, (b + 1) / 2)       el VS decodifica b = 2 v - 1: con la V invertida llega -b (el disco es simetrico)
    UV3 = (corriente, ph)        la bandera en U (0 inhalar / 1 exhalar); ph uniforme en V
  decode_uv() es la misma cuenta que el VS; BreathAir_check.py prueba que con la V invertida las estadisticas no cambian.

Sin Unreal: numpy puro (corre tambien dentro del Python de Blender).
"""
import math

import numpy as np

# ---------------------------------------------------------------------------------------------
# Perillas del MATERIAL (M_BreathAir_SC / MI_BreathAir_SC). Defaults = tabla del plan (seccion 5.3).
# ---------------------------------------------------------------------------------------------
MAT = dict(
    # 1 - Inhalar: motas que convergen hacia un FOCO visible en la parte baja de la vista y de ahi a la boca
    InTilt=24.0, InNear=40.0, InFar=95.0, InSpreadH=30.0, InSpreadV=12.0, InAccel=1.35, InSwirl=35.0,
    InAlpha=0.45, InSizeCm=0.22, InFocus=0.8, FocusDist=34.0, FocusTilt=16.0,
    # 2 - Exhalar: pluma que sale de la boca, frena, se abre, sube apenas y se apaga (por debajo del metaball)
    OutTilt=18.0, PlumeLen=110.0, OutStart=15.0, OutDecel=1.8, OutSpread=16.0, OutFlat=0.6, Buoy=10.0, Turb=3.0,
    OutAlpha=0.50, OutSizeCm=0.28, OutGrow=0.8,
    # 3 - Confort (no bajar sin probar en el visor)
    NearMin=22.0, NearFull=45.0, ElevMax=-4.0, ElevSoft=6.0, MaxDeg=0.40, MaxDegOut=0.55,
    SpeedFade0=20.0, SpeedFade1=40.0,
    # 4 - Color (van al pixel shader)
    InColor=(0.80, 0.85, 1.00), OutColor=(1.00, 0.84, 0.80),
)

# constantes fijas del shader (no son perillas: cambiarlas es cambiar el HLSL y este modelo)
# MinDeg: tamano angular minimo del quad (grados). Debajo, el punto centellea (el PS se evalua una vez por pixel y la
# foveacion baja la densidad en la periferia): se agranda hasta MinDeg y el alfa baja por (fisico / dibujado)^2,
# asi la energia de la mota no cambia.
K = dict(OutR0=1.5, MinDeg=0.20, FrontSoft=0.08, Emerge0=0.02, Emerge1=0.12, InFade=0.2, OutFade0=0.5,
         DepthPow=0.8, AlphaCut=0.002)

# ---------------------------------------------------------------------------------------------
# Perillas del BLUEPRINT (BP_BreathAir_SC). Defaults = tabla del plan (seccion 5.4).
# ---------------------------------------------------------------------------------------------
# Nombres elegidos para el DSL: sin palabras que Unreal pasa a minuscula en el nombre visible (In, On, To, Of, At,
# By, For, From, With, And, Or, A, The) salvo como PRIMERA palabra: "RateIn" daria el getter "GetRatein" (gotcha del
# bWasInZone -> GetWasinZone). Por eso InTravel / OutTravel / InRate / OutRate / VelEnter / VelStay (no "GateOn").
BP = dict(
    bAir=True, AirAmount=1.0,
    MouthFwd=6.0, MouthDown=9.0,
    InTravel=0.9, OutTravel=0.8, FrontLead=1.6,
    LagPos=0.30, LagRot=0.80, HoldLagMul=3.0, PitchFollow=0.75, PitchMin=-35.0, PitchMax=10.0,
    RiseTau=0.30, HoldTau=2.5, CrossTau=0.5,
    VelTau=0.15, VelEnter=0.10, VelStay=0.04, VelMax=2.0, InhMin=0.6,
    FastFloor=0.5, CalmRate=10.0, FastRate=16.0,
    GlobTau=0.5, TurnFade0=6.0, TurnFade1=20.0, TurnBack=0.6, TurnCatch=0.25,
    PreviewBreath=0.0, PreviewAirT=0.35,
)
GATE_ON = 0.05         # AirGate (MPC_Breath.On) por debajo de esto: la senal no significa nada, no hay transporte

N_IN, N_OUT = 768, 1280
IPD = 6.4


# ---------------------------------------------------------------------------------------------
# utilidades identicas a HLSL
# ---------------------------------------------------------------------------------------------
def sat(x):
    return np.clip(x, 0.0, 1.0)


def smoothstep(a, b, x):
    t = sat((np.asarray(x, dtype=np.float64) - a) / (b - a))
    return t * t * (3.0 - 2.0 * t)


def frac(x):
    return x - np.floor(x)


def step(edge, x):
    return (np.asarray(x) >= edge).astype(np.float64)


def _dot(a, b):
    return np.sum(a * b, axis=-1)


def _norm(a):
    return np.sqrt(_dot(a, a))


def _normalize(a):
    return a / _norm(a)[..., None]


def _cross(a, b):
    return np.cross(a, b)


def sstep1(a, b, x):
    """smoothstep escalar (float)."""
    t = min(max((x - a) / (b - a), 0.0), 1.0)
    return t * t * (3.0 - 2.0 * t)


# ---------------------------------------------------------------------------------------------
# Semillas de cada quad
# ---------------------------------------------------------------------------------------------
def seeds(n_in=N_IN, n_out=N_OUT, seed=20260928):
    """e ESTRATIFICADO por corriente (las motas quedan parejas a lo largo del camino: sin huecos que se lean como
    pulsos), u / fase al azar, (a, b) uniforme en el disco unitario. Orden: primero las de inhalar."""
    rng = np.random.default_rng(seed)
    out = {}
    e = []
    for n in (n_in, n_out):
        k = (np.arange(n) + rng.random(n)) / n
        e.append(k[rng.permutation(n)])
    n = n_in + n_out
    out["e"] = np.concatenate(e)
    out["u"] = rng.random(n)
    r = np.sqrt(rng.random(n))
    th = 2.0 * np.pi * rng.random(n)
    out["a"] = r * np.cos(th)
    out["b"] = r * np.sin(th)
    out["ph"] = rng.random(n)
    out["flag"] = np.concatenate([np.zeros(n_in), np.ones(n_out)])
    out["n_in"], out["n_out"] = n_in, n_out
    return out


def encode_uv(sd):
    """Las 3 capas de semillas COMO SE ESCRIBEN en la malla (gen_breath_air.py): UV1, UV2, UV3 (n, 2)."""
    return dict(UV1=np.stack([sd["e"], sd["u"]], 1),
                UV2=np.stack([sd["a"], 0.5 * (sd["b"] + 1.0)], 1),
                UV3=np.stack([sd["flag"], sd["ph"]], 1))


def flip_v(uv):
    """Lo que hace el importador FBX de Unreal con cada capa: V -> 1 - V (gotcha 302)."""
    return {k: np.stack([v[:, 0], 1.0 - v[:, 1]], 1) for k, v in uv.items()}


def decode_uv(uv, n_in=None):
    """La MISMA cuenta que el VS: (e, u) = UV1; (a, b) = (UV2.x, 2 UV2.y - 1); corriente = UV3.x; ph = UV3.y."""
    sd = dict(e=uv["UV1"][:, 0].copy(), u=uv["UV1"][:, 1].copy(), a=uv["UV2"][:, 0].copy(),
              b=2.0 * uv["UV2"][:, 1] - 1.0, flag=uv["UV3"][:, 0].copy(), ph=uv["UV3"][:, 1].copy())
    sd["n_in"] = int(np.sum(sd["flag"] < 0.5)) if n_in is None else n_in
    sd["n_out"] = sd["e"].shape[0] - sd["n_in"]
    return sd


# ---------------------------------------------------------------------------------------------
# VERTEX SHADER (vectorizado): lo mismo que BreathAirVS.hlsl
# ---------------------------------------------------------------------------------------------
def vs(sd, pv, camL=(0.0, 0.0, 0.0), mat=None, corner=None, LP=None):
    """sd = seeds() (o decode_uv de lo que llega en la malla); pv = parametros empujados por el BP (AirT, AirE: 4
    floats; MouthL, LagM, LagA, LagR, LagU, UpL: 3 floats, en local de la camara). camL = camara del ojo en local.
    corner = (n, 2) esquinas 0/1 (None = solo el centro). Devuelve un dict con todo lo intermedio."""
    q = dict(MAT)
    if mat:
        q.update(mat)
    n = sd["e"].shape[0]
    AirT, AirE = np.asarray(pv["AirT"], float), np.asarray(pv["AirE"], float)
    Mx = np.asarray(pv["MouthL"], float)[None, :]
    Mg = np.asarray(pv["LagM"], float)[None, :]
    A0 = np.asarray(pv["LagA"], float)[None, :]
    R0 = np.asarray(pv["LagR"], float)[None, :]
    U0 = np.asarray(pv["LagU"], float)[None, :]
    UpL = np.asarray(pv["UpL"], float)[None, :]
    camL = np.asarray(camL, float)[None, :]
    e, u, a, b, ph = sd["e"], sd["u"], sd["a"], sd["b"], sd["ph"]
    isOut = step(0.5, sd["flag"])
    P = np.zeros((n, 3))
    tg = np.zeros((n, 3))
    spd = np.zeros(n)
    al = np.zeros(n)
    sz = np.zeros(n)
    mxd = np.full(n, q["MaxDeg"])
    s_all = np.zeros(n)
    i = isOut < 0.5
    o = ~i
    # ---- inhalar: del volumen de adelante (marco con retardo) a la boca EXACTA, pasando cerca de un FOCO visible ----
    # Curva de Bezier cuadratica st -> cp -> en. cp = lerp(punto medio, foco, InFocus): con InFocus 0 es la recta
    # st -> en de antes; con InFocus 1 las motas se juntan de costado MIENTRAS se acercan (el desvio lateral decae
    # como (1 - w)^2) y recien despues del foco bajan a la boca, cuando ya las apago el confort de cercania.
    ti = math.radians(q["InTilt"])
    Ai = math.cos(ti) * A0 - math.sin(ti) * U0
    Ui = math.cos(ti) * U0 + math.sin(ti) * A0
    s = frac(e[i] + AirT[0])
    d0 = q["InNear"] + (q["InFar"] - q["InNear"]) * np.power(np.maximum(u[i], 1.0e-4), K["DepthPow"])
    w = np.power(np.maximum(s, 1.0e-4), q["InAccel"])
    # remolino: la mitad de las motas gira hacia cada lado (sin rotacion neta del campo: nada de vection de giro)
    sw = math.radians(q["InSwirl"]) * w * (2.0 * step(0.5, ph[i]) - 1.0)
    ca, sa = np.cos(sw), np.sin(sw)
    a2 = a[i] * ca - b[i] * sa
    b2 = a[i] * sa + b[i] * ca
    st = (Mg + Ai * d0[:, None] + R0 * (d0 * math.tan(math.radians(q["InSpreadH"])) * a2)[:, None]
          + Ui * (d0 * math.tan(math.radians(q["InSpreadV"])) * b2)[:, None])
    en = Mx + np.stack([a[i], b[i], 2.0 * u[i] - 1.0], axis=1)
    tf = math.radians(q["FocusTilt"])
    fp = Mg + (math.cos(tf) * A0 - math.sin(tf) * U0) * q["FocusDist"]
    cp = 0.5 * (st + en) + (fp - 0.5 * (st + en)) * q["InFocus"]
    iw = 1.0 - w
    P[i] = (iw * iw)[:, None] * st + (2.0 * iw * w)[:, None] * cp + (w * w)[:, None] * en
    tg[i] = (2.0 * iw)[:, None] * (cp - st) + (2.0 * w)[:, None] * (en - cp)
    spd[i] = _norm(tg[i]) * q["InAccel"] * np.power(np.maximum(s, 1.0e-4), q["InAccel"] - 1.0) * AirE[2]
    al[i] = q["InAlpha"] * smoothstep(0.0, K["InFade"], s) * AirE[0]
    sz[i] = q["InSizeCm"]
    s_all[i] = s
    # ---- exhalar: pluma que sale de la boca EXACTA y se abre en el marco con retardo ----
    to = math.radians(q["OutTilt"])
    Ao = math.cos(to) * A0 - math.sin(to) * U0
    Uo = math.cos(to) * U0 + math.sin(to) * A0
    s = frac(e[o] + AirT[1])
    kk = 1.0 - np.power(np.maximum(1.0 - s, 1.0e-4), q["OutDecel"])
    x = q["OutStart"] + (q["PlumeLen"] - q["OutStart"]) * kk
    tsp = math.tan(math.radians(q["OutSpread"]))
    rad = K["OutR0"] + x * tsp
    bs = Mx + (Mg - Mx) * smoothstep(0.0, 0.6, s)[:, None]
    tu = 6.2831853 * AirT[1]
    tb = q["Turb"] * s[:, None] * np.stack([
        np.sin(3.0 * tu + 6.2831853 * ph[o]),
        np.sin(2.0 * tu + 6.2831853 * frac(ph[o] * 7.13 + 0.37)),
        np.sin(3.0 * tu + 6.2831853 * frac(ph[o] * 13.7 + 0.71))], axis=1)
    P[o] = (bs + Ao * x[:, None] + R0 * (rad * a[o])[:, None] + Uo * (rad * q["OutFlat"] * b[o])[:, None]
            + UpL * (q["Buoy"] * s * s)[:, None] + tb)
    tg[o] = Ao + tsp * (R0 * a[o][:, None] + Uo * (q["OutFlat"] * b[o])[:, None])
    spd[o] = (_norm(tg[o]) * (q["PlumeLen"] - q["OutStart"]) * q["OutDecel"]
              * np.power(np.maximum(1.0 - s, 1.0e-4), q["OutDecel"] - 1.0) * AirE[3])
    fr = sat((AirT[2] - s) / K["FrontSoft"])
    al[o] = (q["OutAlpha"] * fr * smoothstep(K["Emerge0"], K["Emerge1"], s)
             * (1.0 - smoothstep(K["OutFade0"], 1.0, s)) * AirE[1])
    sz[o] = q["OutSizeCm"] * (1.0 + q["OutGrow"] * s)
    mxd[o] = q["MaxDegOut"]
    s_all[o] = s
    # ---- confort + tamano (las dos corrientes) ----
    D = P - camL
    dist = np.maximum(_norm(D), 1.0e-3)
    Dn = D / dist[:, None]
    al = al * smoothstep(q["NearMin"], q["NearFull"], dist)
    se0 = math.sin(math.radians(q["ElevMax"] - q["ElevSoft"]))
    se1 = math.sin(math.radians(q["ElevMax"]))
    al = al * (1.0 - smoothstep(se0, se1, Dn[:, 2]))
    tl = np.maximum(_norm(tg), 1.0e-4)
    om = np.degrees(spd * _norm(_cross(tg / tl[:, None], Dn)) / dist)
    al = al * (1.0 - smoothstep(q["SpeedFade0"], q["SpeedFade1"], om))
    al = al * AirT[3]
    szn = dist * math.tan(math.radians(K["MinDeg"]))
    kq = sat(sz / szn)
    al = al * kq * kq                      # energia constante: lo que se agranda hasta MinDeg baja de alfa
    szw = np.clip(sz, szn, dist * np.tan(np.radians(mxd)))
    hsz = 0.5 * szw * step(K["AlphaCut"], al)
    out = dict(P=P, al=al, hsz=hsz, szw=szw, dist=dist, sinEl=Dn[:, 2], om=om, s=s_all, isOut=isOut,
               n_in=int(np.sum(i)))
    if corner is not None:
        f = _normalize(camL - P + np.array([1.0e-4, 0.0, 0.0])[None, :])
        rt = _normalize(_cross(np.array([0.0, 0.0, 1.0])[None, :], f) + np.array([0.0, 1.0e-4, 0.0])[None, :])
        up = _cross(f, rt)
        c = np.asarray(corner, float) * 2.0 - 1.0
        dst = P + (rt * c[:, 0:1] + up * c[:, 1:2]) * hsz[:, None]
        out["dst"] = dst
        out["AirV"] = np.stack([c[:, 0], c[:, 1], al, isOut], axis=1)
        if LP is not None:
            offs = dst - np.asarray(LP, float)
            bad = ~(_dot(offs, offs) < 1.0e8)
            offs[bad] = 0.0
            out["offs"] = offs
    return out


def ps(AirV, mat=None):
    """BreathAirPS: devuelve (color premultiplicado, alfa)."""
    q = dict(MAT)
    if mat:
        q.update(mat)
    AirV = np.asarray(AirV, float)
    c = AirV[..., 0:2]
    m = sat(1.0 - _dot(c, c))
    m = m * m
    a = sat(m * AirV[..., 2])
    col = np.asarray(q["InColor"]) + (np.asarray(q["OutColor"]) - np.asarray(q["InColor"])) * sat(AirV[..., 3])[..., None]
    return col * a[..., None], a


# ---------------------------------------------------------------------------------------------
# Cabeza: base de la camara en el mundo (yaw, pitch en grados; roll 0)
# ---------------------------------------------------------------------------------------------
def head_basis(yaw, pitch):
    y, p = math.radians(yaw), math.radians(pitch)
    F = np.array([math.cos(p) * math.cos(y), math.cos(p) * math.sin(y), math.sin(p)])
    R = np.array([-math.sin(y), math.cos(y), 0.0])
    U = np.array([-math.sin(p) * math.cos(y), -math.sin(p) * math.sin(y), math.cos(p)])
    return F, R, U


def to_local_pt(Pw, eye, yaw, pitch):
    F, R, U = head_basis(yaw, pitch)
    D = np.asarray(Pw, float) - eye
    return np.stack([D @ F, D @ R, D @ U], axis=-1)


def to_local_dir(Vw, yaw, pitch):
    F, R, U = head_basis(yaw, pitch)
    V = np.asarray(Vw, float)
    return np.stack([V @ F, V @ R, V @ U], axis=-1)


def to_world_pt(Pl, eye, yaw, pitch):
    F, R, U = head_basis(yaw, pitch)
    Pl = np.asarray(Pl, float)
    return eye + Pl[..., 0:1] * F + Pl[..., 1:2] * R + Pl[..., 2:3] * U


def normalize_axis(a):
    """UKismetMathLibrary::NormalizeAxis: (-180, 180]."""
    a = math.fmod(a, 360.0)
    if a < 0.0:
        a += 360.0
    if a > 180.0:
        a -= 360.0
    return a


def ex(dt, tau):
    """1 - exp(-dt / tau): el paso de un filtro de primer orden (lo mismo que escribe el DSL)."""
    return 1.0 - math.exp(-dt / tau)


# ---------------------------------------------------------------------------------------------
# BLUEPRINT: AirStep (una llamada por Tick). Traduccion 1:1 en scripts/breath_air.dsl.
# ---------------------------------------------------------------------------------------------
class AirBP:
    """Estado de BP_BreathAir_SC (variables Z-Aliento) y su paso por cuadro. Integra en el MUNDO."""

    def __init__(self, eye, yaw, pitch, bp=None):
        self.q = dict(BP)
        if bp:
            self.q.update(bp)
        q = self.q
        self.Tin = 0.0
        self.Tout = 0.0
        self.Fout = 0.0
        self.Ein = 0.0
        self.Eout = 0.0
        self.InRate = 0.0
        self.OutRate = 0.0
        self.Vel = 0.0
        self.VelF = 0.0
        self.Flow = 0.0                # +1 inhalando, -1 exhalando, 0 quieto (con histeresis)
        self.InhHold = 0.0             # s de inhalacion sostenida desde el ultimo inicio de exhalacion contado
        self.Sprev = 0.0
        self.bPrimed = False
        self.MouthW = self.mouth_world(eye, yaw, pitch)
        self.YawLag = yaw
        self.PitchLag = pitch
        self.YawPrev = yaw
        self.PitchPrev = pitch
        self.TurnRate = 0.0
        self.MoveFade = 1.0
        self.Clock = 0.0
        self.LastOnset = -1.0
        self.Per = 0.0
        self.bOnset = False
        self.RateBpm = q["CalmRate"] * 0.6          # arranca en calma (6 resp/min)
        self.RateCalm = 1.0
        self.GlobBase = 0.0
        self.Glob = 0.0
        self.bLagInit = False          # False = el proximo paso inicializa el marco (como AirMountCam en el BP)

    def mouth_world(self, eye, yaw, pitch):
        F, R, U = head_basis(yaw, pitch)
        return eye + F * self.q["MouthFwd"] - U * self.q["MouthDown"]

    def step(self, dt, S, on, eye, yaw, pitch, mounted=True):
        """S = MPC_Breath.Signed (-1 exhalado .. +1 inhalado), on = MPC_Breath.On. Devuelve la velocidad filtrada.
        Con bLagInit False (el primer paso, o recien montado en la camara) el marco con retardo y la cabeza previa
        se inicializan en la cabeza actual."""
        lag_init = self.bLagInit
        q = self.q
        dt = max(dt, 1.0e-4)
        # 1. velocidad: dS/dt con tope (un escalon de Signed, p. ej. el Retire del rig, no dispara la cinta) y SOLO
        #    con respiracion detectada (On < 0,05: la senal no significa nada); despues un pasabajos (VelTau)
        raw = (S - self.Sprev) / dt if (self.bPrimed and on > GATE_ON) else 0.0
        self.Vel = min(max(raw, -q["VelMax"]), q["VelMax"])
        self.Sprev = S
        self.bPrimed = True
        self.Clock += dt
        self.VelF += (self.Vel - self.VelF) * ex(dt, q["VelTau"])
        vf = self.VelF
        # 2. modo con HISTERESIS: entra con |vf| > VelEnter, sigue mientras |vf| > VelStay (el ruido y la deriva del
        #    sostenido no lo prenden y apagan). Se decide con el modo VIEJO.
        old = self.Flow
        if old > 0.5:
            new = 1.0 if vf > q["VelStay"] else 0.0
        elif old < -0.5:
            new = -1.0 if vf < -q["VelStay"] else 0.0
        else:
            new = 1.0 if vf > q["VelEnter"] else (-1.0 if vf < -q["VelEnter"] else 0.0)
        inh = new > 0.5
        exh = new < -0.5
        # 3. ritmo: un inicio de exhalacion CUENTA solo si antes hubo una inhalacion sostenida (latch InhMin): el
        #    reingreso al final de la exhalacion o el ruido de una pausa no lo duplican.
        self.bOnset = exh and old > -0.5 and self.InhHold >= q["InhMin"]
        self.Per = self.Clock - self.LastOnset
        if self.bOnset and self.LastOnset >= 0.0 and 2.0 < self.Per < 30.0:
            self.RateBpm += (60.0 / max(self.Per, 0.01) - self.RateBpm) * 0.5
        if self.bOnset:
            self.LastOnset = self.Clock
        if self.bOnset:
            self.InhHold = 0.0
        elif inh:
            self.InhHold += dt
        elif self.InhHold < q["InhMin"]:
            self.InhHold = 0.0
        self.Flow = new
        rt = min(max((self.RateBpm - q["CalmRate"]) / max(q["FastRate"] - q["CalmRate"], 0.01), 0.0), 1.0)
        self.RateCalm = q["FastFloor"] + (1.0 - q["FastFloor"]) * (1.0 - rt * rt * (3.0 - 2.0 * rt))
        # 4. transporte integrado SOLO en su modo (nunca una velocidad en caliente: gotcha 329). En las pausas la cinta
        #    no avanza: las motas quedan suspendidas.
        self.InRate = 0.5 * q["InTravel"] * max(vf, 0.0) if inh else 0.0
        self.OutRate = 0.5 * q["OutTravel"] * max(-vf, 0.0) if exh else 0.0
        self.Tin = float(frac(self.Tin + self.InRate * dt))
        self.Tout = float(frac(self.Tout + self.OutRate * dt))
        self.Fout = min(self.Fout + q["FrontLead"] * self.OutRate * dt, 1.5)
        # 5. envolventes: sube con la corriente activa; se cruza rapido; queda SUSPENDIDA en las pausas
        tin_tgt, tin_tau = (1.0, q["RiseTau"]) if inh else ((0.0, q["CrossTau"]) if exh else (0.0, q["HoldTau"]))
        tout_tgt, tout_tau = (1.0, q["RiseTau"]) if exh else ((0.0, q["CrossTau"]) if inh else (0.0, q["HoldTau"]))
        self.Ein += (tin_tgt - self.Ein) * ex(dt, tin_tau)
        self.Eout += (tout_tgt - self.Eout) * ex(dt, tout_tau)
        if self.Eout < 0.01 and not exh:
            self.Fout = 0.0
        # 6. marco del aire con retardo (en el MUNDO) + giro de la cabeza. Mientras el aire esta apagado por el giro
        #    (MoveFade < 1), el marco alcanza a la cabeza mas rapido (TurnCatch): reaparece en su lugar.
        still = not (inh or exh)
        catch = q["TurnCatch"] + (1.0 - q["TurnCatch"]) * self.MoveFade
        k = ex(dt, q["LagRot"] * (q["HoldLagMul"] if still else 1.0) * catch)
        if lag_init:
            dyh = normalize_axis(yaw - self.YawPrev)
            dph = pitch - self.PitchPrev
            dyl = normalize_axis(yaw - self.YawLag) * k
            dpl = q["PitchFollow"] * (pitch - self.PitchLag) * k
            self.TurnRate = max(max(abs(dyh), abs(dph)), max(abs(dyl), abs(dpl))) / dt
        else:
            self.TurnRate = 0.0
        # baja EN EL MISMO CUADRO (sigue a una senal continua: la velocidad de la cabeza) y vuelve con TurnBack
        ft = 1.0 - sstep1(q["TurnFade0"], q["TurnFade1"], self.TurnRate)
        self.MoveFade = ft if ft < self.MoveFade else self.MoveFade + (ft - self.MoveFade) * ex(dt, q["TurnBack"])
        M = self.mouth_world(eye, yaw, pitch)
        if lag_init:
            self.MouthW = self.MouthW + (M - self.MouthW) * ex(dt, q["LagPos"])
            self.YawLag = normalize_axis(self.YawLag + normalize_axis(yaw - self.YawLag) * k)
            self.PitchLag += (pitch - self.PitchLag) * k
        else:
            self.MouthW = M
            self.YawLag = yaw
            self.PitchLag = pitch
        self.YawPrev = yaw
        self.PitchPrev = pitch
        self.bLagInit = True
        # 7. presencia: deteccion x perilla x ritmo x montado, SUAVIZADA (GlobTau: un escalon de On -el Retire del
        #    rig- no apaga el aire en un cuadro), x el apagado por giro
        amt = q["AirAmount"] if q["bAir"] else 0.0
        gt = min(max(on, 0.0), 1.0) * amt * self.RateCalm * (1.0 if mounted else 0.0)
        self.GlobBase += (gt - self.GlobBase) * ex(dt, q["GlobTau"])
        self.Glob = self.GlobBase * self.MoveFade
        return vf

    def push(self, eye, yaw, pitch):
        """PushAir: los 8 vectores del cuadro, en local de la camara (una sola funcion, el mismo cuadro)."""
        q = self.q
        pa = min(max(q["PitchFollow"] * self.PitchLag, q["PitchMin"]), q["PitchMax"])
        yl = math.radians(self.YawLag)
        pr = math.radians(pa)
        A0 = np.array([math.cos(pr) * math.cos(yl), math.cos(pr) * math.sin(yl), math.sin(pr)])
        R0 = np.array([-math.sin(yl), math.cos(yl), 0.0])
        U0 = np.array([-math.sin(pr) * math.cos(yl), -math.sin(pr) * math.sin(yl), math.cos(pr)])
        return dict(
            AirT=np.array([self.Tin, self.Tout, self.Fout, self.Glob]),
            AirE=np.array([self.Ein, self.Eout, self.InRate, self.OutRate]),
            MouthL=np.array([q["MouthFwd"], 0.0, -q["MouthDown"]]),
            LagM=to_local_pt(self.MouthW, eye, yaw, pitch),
            LagA=to_local_dir(A0, yaw, pitch), LagR=to_local_dir(R0, yaw, pitch), LagU=to_local_dir(U0, yaw, pitch),
            UpL=to_local_dir(np.array([0.0, 0.0, 1.0]), yaw, pitch))


def preview_push(bp=None, yaw=0.0, pitch=0.0):
    """PreviewAir (Construction Script, sin Play): la cabeza es el actor colocado; PreviewBreath elige la corriente
    (> 0 inhalar con Ein = PreviewBreath, < 0 la pluma con Eout = -PreviewBreath) y PreviewAirT arrastra la cinta.
    Con PreviewBreath 0 todo queda en alfa 0: el componente no dibuja nada (neutro)."""
    q = dict(BP)
    if bp:
        q.update(bp)
    pb = min(max(q["PreviewBreath"], -1.0), 1.0)
    st = AirBP(np.zeros(3), yaw, pitch, q)
    st.Tin = st.Tout = q["PreviewAirT"]
    st.Fout = 1.5
    st.Ein = max(pb, 0.0)
    st.Eout = max(-pb, 0.0)
    st.Glob = (q["AirAmount"] if q["bAir"] else 0.0)
    return st.push(np.zeros(3), yaw, pitch)


# ---------------------------------------------------------------------------------------------
# El RIG (BP_BreathRig_SC): el seguidor con frenada fisica que escribe MPC_Breath.Signed
# ---------------------------------------------------------------------------------------------
def finterp_to(cur, tgt, dt, speed):
    if speed <= 0.0:
        return tgt
    d = tgt - cur
    if d * d < 1.0e-8:
        return tgt
    return cur + d * min(max(dt * speed, 0.0), 1.0)


class RigFollower:
    """FollowBreath del rig (tracker: 'FRENADA FISICA'): v* = sign(d) k sqrt|d|, k = 2 sqrt2 / FollowTime;
    vel = FInterpTo(vel, v*, 1/Attack); S += vel dt sin pasarse de la meta."""

    def __init__(self, s0=-1.0, follow_time=3.0, attack=0.12):
        self.S = s0
        self.vel = 0.0
        self.k = 2.0 * math.sqrt(2.0) / follow_time
        self.att = attack

    def step(self, target, dt):
        d = target - self.S
        vstar = math.copysign(self.k * math.sqrt(abs(d)), d)
        self.vel = finterp_to(self.vel, vstar, dt, 1.0 / self.att if self.att > 0 else 0.0)
        stp = self.vel * dt
        if (d > 0 and stp > d) or (d < 0 and stp < d):
            self.S = target
        else:
            self.S += stp
        return self.S


def belly_target(t, tin=4.0, h1=3.0, tout=4.0, h2=3.0, lag=0.4):
    """Senal normalizada ANTES del seguidor (NormRange -> n(2-|n|)): el usuario sigue al pacer con ~0,4 s de
    retardo; inhalacion de medio coseno, exhalacion pasiva (flujo maximo al principio). Devuelve (n, fase)."""
    T = tin + h1 + tout + h2
    tt = (t - lag) % T
    if tt < tin:
        p = tt / tin
        return -1.0 + (1.0 - math.cos(math.pi * p)), 0
    if tt < tin + h1:
        return 1.0, 1
    if tt < tin + h1 + tout:
        p = (tt - tin - h1) / tout
        a = 3.2
        return 1.0 - 2.0 * (1.0 - math.exp(-a * p)) / (1.0 - math.exp(-a)), 2
    return -1.0, 3


def _unsquash(y):
    y = max(min(y, 1.0), -1.0)
    return math.copysign(1.0 - math.sqrt(max(1.0 - abs(y), 0.0)), y)


def _squash(n):
    n = max(min(n, 1.0), -1.0)
    return n * (2.0 - abs(n))


class BellyNoisy:
    """La senal REAL que ve el seguidor (revision costo/confort 2026-09-28): la ideal des-aplastada + ruido OU del
    mando (tau 0,4 s = TauFast del rig; sigma en unidades del rango normalizado) + la DERIVA del sostenido (el
    band-pass y HoldSlow dejan caer |n| a lo largo de la pausa) -> clamp -> n(2 - |n|). Con sigma 0 y deriva 0 es
    belly_target exacto."""

    def __init__(self, sigma=0.0, drift=0.0, pacer=(4.0, 3.0, 4.0, 3.0), lag=0.4, seed=1, dt=1.0 / 72.0):
        self.sigma, self.drift, self.pacer, self.lag = sigma, drift, pacer, lag
        self.rng = np.random.default_rng(seed)
        self.ou = 0.0
        self.hold = 0.0
        self.a = dt / 0.4
        self.kw = sigma * math.sqrt((2.0 - self.a) / self.a) if sigma > 0 else 0.0

    def __call__(self, t, dt):
        y, ph = belly_target(t, *self.pacer, lag=self.lag)
        if self.sigma == 0.0 and self.drift == 0.0:
            return y, ph
        n = _unsquash(y)
        if ph in (1, 3):
            self.hold += dt
            n = n - math.copysign(self.drift * min(self.hold / max(self.pacer[1 if ph == 1 else 3], 1e-3), 1.0), n)
        else:
            self.hold = 0.0
        self.ou += self.a * (self.rng.standard_normal() * self.kw - self.ou)
        return _squash(n + self.ou), ph
