# -*- coding: utf-8 -*-
"""vida_model.py - MODELO DE REFERENCIA de la CAPA DE VIDA del valle de Entering (2026-09-28).

Plan: docs/PLAN-VIDA-VALLE-2026-09-28.md. Es la cuenta EXACTA que hacen:
  - el vertex shader  scripts/hlsl/DustVS.hlsl      (cada mota de polvo, sin estado)
  - el pixel shader   scripts/hlsl/DustPS.hlsl      (punto suave premultiplicado, frio/tibio segun la luz)
  - el vertex shader  scripts/hlsl/GustLeanVS.hlsl  (la franja de luz de la rafaga en el llano: se suma al
                                                     gradiente de ValleyGradVS antes del interpolador)
  - el Blueprint      BP_ValleyLife_SC (UN reloj de rafagas: agenda irregular, frente que avanza, eco de la
                      exhalacion, meandro integrado, presencia) -> scripts/vida.dsl es la traduccion de VidaBP.
Lo usan: hlsl/Vida_check.py, gen_valley_dust.py, vida_dsl_sim.py, sim_vida.py, render_vida_valle.py.

EJES Y ESPACIOS (Unreal: X adelante, Y derecha, Z arriba, cm).
  - El actor BP_ValleyLife_SC se coloca en los OJOS del usuario sentado (0, 0, 120), sin rotar (o solo en yaw): el
    espacio LOCAL del componente de polvo es el del actor. Las motas viven en el MUNDO (no cuelgan de la cabeza): la
    malla ES la nube (cada quad en su lugar), el VS le suma el meandro y el remolino de la rafaga.
  - La RAFAGA vive en el plano del piso: un FRENTE recto (perpendicular a la direccion de avance d) que avanza por una
    TRAYECTORIA que pasa por el punto O. Para un punto p: x = (p - O).d (a lo largo del camino), eta = |(p - O).d_perp|
    (a lo largo del frente). El frente esta en x = s (s lo integra el BP). Todo es invariante a traslaciones y giros
    en yaw: s, e0, e1, W, Lf0, Lf1 valen igual en el espacio del polvo, del valle y del mundo.
  - Funciones de la rafaga (las mismas en el polvo, el valle y el BP):
      A(x)   = S5((x - e0)/ramp) * (1 - S5((x - (e1 - ramp))/ramp))   envolvente a lo largo del camino (0 fuera de [e0,e1])
      h(eta) = 1 - S5((eta - Lf0)/(Lf1 - Lf0))                         el frente es finito
      u      = (s - x)/W,  t = saturate((u + 2)/4)
      P(u)   = S5(t)            fraccion del paso del frente (0 antes, 1 despues)
      bell   = 16 t^2 (1 - t)^2  actividad (1 cuando el frente esta encima)
    El frente arranca en s0 = e0 - 2W y termina en s1 = e1 + 2W: en el primer cuadro P = 0 para todo punto con A > 0 y en
    el ultimo P = 1 -> el remolino de cada mota es un LAZO CERRADO (vuelve exacto a su lugar): nada salta al empezar ni
    al terminar, y la rafaga siguiente arranca del mismo estado.

SEMILLAS EN LA MALLA, INVARIANTES A LA V INVERTIDA (gotcha 302: el importador FBX entrega V como 1 - V) y a las UV en
MEDIA PRECISION (las UV de una StaticMesh se guardan en fp16: enteros exactos hasta 2048, uniformes con paso 1/2048):
    posicion  = LocalPosition menos el desplazamiento de su esquina (fp32 exacto; la esquina sale de la U)
    UV0 = (esquina k 0..3, 0.5)     la esquina en U: la V invertida no la toca (0,5 -> 0,5)
    UV1 = (n 0..1023, ph1)          juego de frecuencias del meandro y del titileo (entero, en U); fase uniforme (V)
    UV2 = (f 0..3, ph2)             bits: 1 = mota SOLO de rafaga, 2 = sentido del remolino (entero, en U); fase (V)
    UV3 = (b, ph3)                  brillo/tamano/radio (uniforme, en U); fase (V)
  Con la V invertida las fases son 1 - ph: otra muestra uniforme (las estadisticas no cambian; Vida_check.py lo prueba).

Sin Unreal: numpy puro (corre tambien dentro del Python de Blender).
"""
import math

import numpy as np

# ---------------------------------------------------------------------------------------------
# Perillas del MATERIAL del polvo (M_ValleyDust_SC / MI_ValleyDust_SC). Defaults = tabla 5.2 del plan.
# ---------------------------------------------------------------------------------------------
MAT = dict(
    # 1 - Polvo  (rev. 2: el juego VISIBLE es el default; el SUTIL de la rev. 1 esta en PRESET_SUTIL)
    DustAlpha=1.0, DustSizeDeg=0.24, SizeVar=0.3, DistTilt=0.3, MeanderCm=7.0, MeanderFar=10.0, Twinkle=0.35,
    # 2 - Luz (el polvo brilla contra el sol bajo del valle: dispersion hacia adelante, Henyey-Greenstein)
    SunAz=20.0, SunEl=10.0, SunG=0.55, SunBase=0.5,
    # 3 - Rafaga (como responde el polvo al frente)
    EddyCm=10.0, EddyNear=250.0, Lift=1.2, GustDustAlpha=0.6, DriftCm=40.0, DriftFar=3.0,
    # 4 - Confort (no bajar sin probar en el visor). NearMin/NearFull 120/180: el polvo queda FUERA del volumen del
    # aliento (inhalar 40-95 cm, pluma hasta 110 cm): no se confunde con el y no le quita la lectura causal.
    NearMin=120.0, NearFull=180.0, FarFade0=8000.0, FarFade1=11000.0, SpeedFade0=6.0, SpeedFade1=12.0,
    SoulMargin0=2.0, SoulMargin1=8.0,
    # 5 - Color (van al pixel shader; lineal). Vocabulario PROPIO, distinto del aliento (frio azul InColor / tibio rosa
    # OutColor): polvo dorado contra la luz, blanco lavanda apagado en sombra (sin el azul saturado del aliento;
    # mas claro que el aire para que se lea: vida_legibilidad.py).
    ColLit=(1.00, 0.93, 0.74), ColDim=(0.92, 0.90, 0.96),
)
# El juego SUTIL (rev. 1): para bajar desde lo visible si en el visor ensucia (tabla 5.3 del plan).
PRESET_SUTIL = dict(DustAlpha=0.7, DustSizeDeg=0.22, DistTilt=0.35, SunBase=0.35, GustDustAlpha=0.5, DriftCm=20.0,
                    ColDim=(0.80, 0.78, 0.86))
# Grupo de cada parametro en el material (el orden de la tabla 5.2 del plan)
GRUPOS = dict(
    DustAlpha="1 - Polvo", DustSizeDeg="1 - Polvo", SizeVar="1 - Polvo", DistTilt="1 - Polvo", MeanderCm="1 - Polvo",
    MeanderFar="1 - Polvo", Twinkle="1 - Polvo", SunAz="2 - Luz", SunEl="2 - Luz", SunG="2 - Luz", SunBase="2 - Luz",
    EddyCm="3 - Rafaga", EddyNear="3 - Rafaga", Lift="3 - Rafaga", GustDustAlpha="3 - Rafaga", DriftCm="3 - Rafaga",
    DriftFar="3 - Rafaga", NearMin="4 - Confort", NearFull="4 - Confort",
    FarFade0="4 - Confort", FarFade1="4 - Confort", SpeedFade0="4 - Confort", SpeedFade1="4 - Confort",
    SoulMargin0="4 - Confort", SoulMargin1="4 - Confort", ColLit="5 - Color", ColDim="5 - Color",
    VidaT="9 - Interno", VidaG="9 - Interno", VidaS="9 - Interno", VidaE="9 - Interno", VidaF="9 - Interno",
    VidaSoul="9 - Interno", VidaC="9 - Interno")
GRUPO_VALLE = "10 - Rafaga"
# 9 - Interno (los empuja el BP). Defaults del material: todo apagado (VidaT.z = Glob = 0 -> nada dibujado).
#   VidaE.w = Hold (1 durante la rafaga, vuelve a 0 en la relajacion: la deriva a favor del viento), VidaF.z = dHold/dt.
#   VidaC = el punto CICLOPEO (entre los ojos, espacio del actor) y w = 1 valido; w = 0 -> cada ojo usa su camara.
MAT_INTERNO = dict(VidaT=(0.0, 1.0, 0.0, 0.0), VidaG=(0.0, 0.0, 0.0, 1.0), VidaS=(0.0, 800.0, 0.0, 0.0),
                   VidaE=(0.0, 0.0, 1000.0, 0.0), VidaF=(3000.0, 5500.0, 0.0, 0.0), VidaSoul=(380.0, 0.0, 5.0, 0.0),
                   VidaC=(0.0, 0.0, 0.0, 0.0))

# Parametros NUEVOS del material del VALLE (M_BreathValley_SC), grupo "10 - Rafaga": los empuja el BP. Con GustK = 0
# (el default) GustLeanVS devuelve el gradiente de ValleyGradVS SIN TOCAR (el valle es la v2 + capa viva bit a bit).
GUST_MAT = dict(GustP=(0.0, 0.0, 0.0, 1.0), GustQ=(0.0, 800.0, 0.0, 0.0), GustR=(1000.0, 3000.0, 5500.0, 1500.0),
                GustK=(0.0, 0.0, 0.0, 0.0), GustS=(0.0, 0.0, 0.0, 0.0))

# constantes fijas del shader (cambiarlas = cambiar el HLSL y este modelo)
K = dict(Corner=0.2, WinT=1800.0, KBase=24.0, MinDeg=0.2, AlphaCut=0.002, AlphaMax=0.95, OffsGuard=400.0,
         DistRef=100.0, DistMin=30.0, MeanderRef=300.0)

# ---------------------------------------------------------------------------------------------
# Perillas del BLUEPRINT (BP_ValleyLife_SC). Defaults = tabla 5.4 del plan (rev. 2: el juego VISIBLE).
# ---------------------------------------------------------------------------------------------
BP = dict(
    # A-Vida
    bVida=True, VidaAmount=1.0, MeanderRate=1.0, GlobTau=1.0, SoulR=150.0,
    # B-Rafagas (laterales: cruzan el valle y pasan por el usuario). Rev. 2: la franja mas lejos y mas larga (llega a
    # -1/-2 grados de elevacion, a los costados del metaball), mas clara y el frente mas ancho; la rafaga existe en
    # +-40 m de camino (antes +-22: se apagaba justo cuando salia de detras del metaball).
    bGusts=True, GustAmount=1.0, FirstGap=14.0, GapMin=20.0, GapMax=40.0, GustLife=28.0,
    PathHalf=4000.0, GustW=900.0, GustRamp=1500.0, FrontHalf0=4000.0, FrontHalf1=7000.0,
    OffsetMin=1500.0, OffsetMax=4000.0, JitterDeg=25.0, GustStir=2.0, DriftRelax=25.0,
    GustLight=2.8, GustLean=0.12, LeanAz=20.0, GustRuffle=0.0, GustNear=2500.0,
    # C-Soplo (un solo aire: una de cada BreathEvery rafagas espera una exhalacion y sale del usuario hacia adelante)
    bBreathGusts=True, BreathEvery=2.0, BreathWait=15.0, BreathLife=18.0, BreathLen=6000.0, BreathW=400.0,
    BreathRamp=300.0, BreathHalf0=2500.0, BreathHalf1=4500.0, BreathJitter=15.0,
    # D-Sonido
    GustVolume=0.8, SndLen=28.0, BreathSndLen=18.0, SndFwd=800.0,
    # E-Prueba
    PreviewGust=0.0, PreviewKind=0.0, PreviewDir=1.0,
)
# El juego SUTIL de la franja y la agenda (rev. 1), para bajar desde lo visible (tabla 5.3 del plan).
PRESET_SUTIL_BP = dict(GustLight=1.6, GustLean=0.08, GustW=700.0, OffsetMin=500.0, OffsetMax=3000.0,
                       FrontHalf0=3000.0, FrontHalf1=5500.0)
GATE_ON = 0.05          # MPC_Breath.On por debajo: la senal no significa nada
BREATH = dict(VelTau=0.15, VelEnter=0.10, VelStay=0.04, VelMax=2.0, InhMin=0.6)   # detector de exhalacion (= aliento)
PHI = (0.618034, 0.7548777, 0.5698403, 0.4142136)   # secuencias de baja discrepancia (gotcha 355: nada de hash)
PITCH_MIN, PITCH_MAX = 0.75, 1.33
PROBE_FWD = 200.0       # cm: donde el BP mide la actividad de la rafaga "en el usuario" (meandro que se agita)

# Geometria de la escena (Test_Entering)
ACTOR = np.array([0.0, 0.0, 120.0])          # BP_ValleyLife_SC: los ojos del usuario sentado (mundo, cm)
VALLE_Z = -90.4                              # Entering_Valle en Z -90,4 (el piso del valle, mundo)
FLOOR_REL = VALLE_Z - ACTOR[2]               # el piso en el espacio del actor (-210,4 cm)
SOUL_W = np.array([380.0, 0.0, 125.0])       # el metaball (mundo)
IPD = 6.4

N_BASE, N_GUST = 5120, 1024  # rev. 3 (2026-09-29, Beltran en visor: "muy pocas, que lleguen mas lejos"); antes 1536, 512
R_BASE_MIN = 130.0      # cm: rev. 2, la nube de base empieza fuera del volumen del aliento (NearMin 120)
R_BASE_MAX = 11000.0    # cm: rev. 3, la nube de base llega a 110 m (antes 36 m); FarFade0/1 8000/11000 en la MI
R_GUST_MAX = 6000.0     # cm: rev. 3, el polvo de rafaga llega a 60 m (antes 36 m)


# ---------------------------------------------------------------------------------------------
# utilidades identicas a HLSL
# ---------------------------------------------------------------------------------------------
def sat(x):
    return np.clip(x, 0.0, 1.0)


def s5t(t):
    t = sat(t)
    return t * t * t * (t * (6.0 * t - 15.0) + 10.0)


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


def sstep1(a, b, x):
    t = min(max((x - a) / (b - a), 0.0), 1.0)
    return t * t * (3.0 - 2.0 * t)


def s51(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * t * (t * (6.0 * t - 15.0) + 10.0)


# ---------------------------------------------------------------------------------------------
# Las funciones de la rafaga (escalares, las del BP; el HLSL las repite vectorizadas)
# ---------------------------------------------------------------------------------------------
def gust_env(x, e0, e1, ramp):
    rp = max(ramp, 1.0)
    return s51((x - e0) / rp) * (1.0 - s51((x - (e1 - rp)) / rp))


def gust_front(eta, lf0, lf1):
    return 1.0 - s51((abs(eta) - lf0) / max(lf1 - lf0, 1.0))


def gust_t(s, x, W):
    return min(max(((s - x) / max(W, 1.0) + 2.0) * 0.25, 0.0), 1.0)


def gust_act(pxy, g):
    """actividad de la rafaga en un punto del plano (mundo o local, da igual): A(x) h(eta) bell(u) * Amp."""
    if g["Amp"] <= 0.0:
        return 0.0
    rel = np.asarray(pxy, float) - np.asarray(g["O"][:2], float)
    d = np.asarray(g["d"][:2], float)
    x = float(rel @ d)
    eta = float(rel[0] * -d[1] + rel[1] * d[0])
    t = gust_t(g["S"], x, g["W"])
    return g["Amp"] * gust_env(x, g["E0"], g["E1"], g["Ramp"]) * gust_front(eta, g["Lf0"], g["Lf1"]) * 16.0 * t * t * (1 - t) * (1 - t)


# ---------------------------------------------------------------------------------------------
# Semillas y la nube (la malla SM_ValleyDust_SC)
# ---------------------------------------------------------------------------------------------
def seeds(n_base=N_BASE, n_gust=N_GUST, seed=20260928, floor_rel=FLOOR_REL):
    """P0 (posicion de cada mota en el espacio del actor, cm), n, flags, b, fases. Primero las de base, despues las
    de rafaga (los [branch] del VS no dependen de eso, pero ordena la malla).
      base:   radio log-uniforme 1,3 - 36 m (la primera octava a la mitad: menos motas cerca), en todas
              direcciones por encima del piso; lejos de 3 m no mas de 50 grados arriba del horizonte (el cielo es
              brillante: ahi no se ven). Fuera del metaball.
      rafaga: radio log-uniforme 1,5 - 36 m, cerca del piso (hasta 6 m de altura): el polvo que levanta el frente."""
    rng = np.random.default_rng(seed)
    soul_rel = SOUL_W - ACTOR

    def nube(n, r0, r1, alto_max, primera_mitad):
        pts = []
        while len(pts) < n:
            m = 4 * n
            r = r0 * (r1 / r0) ** rng.random(m)
            z = rng.uniform(-1.0, 1.0, m)
            th = rng.uniform(0.0, 2.0 * np.pi, m)
            rr = np.sqrt(1.0 - z * z)
            p = np.stack([r * rr * np.cos(th), r * rr * np.sin(th), r * z], 1)
            ok = p[:, 2] > floor_rel + 15.0
            if alto_max is not None:
                ok &= p[:, 2] < floor_rel + alto_max
            else:
                el = np.degrees(np.arcsin(np.clip(z, -1, 1)))
                ok &= ~((r > 300.0) & (el > 50.0))
            ok &= _norm(p - soul_rel[None, :]) > 150.0
            if primera_mitad:
                ok &= ~((r < 2.0 * r0) & (rng.random(m) < 0.5))
            pts.extend(p[ok].tolist())
        return np.array(pts[:n])

    pb = nube(n_base, R_BASE_MIN, R_BASE_MAX, None, True)
    pg = nube(n_gust, 150.0, R_GUST_MAX, 600.0, False)
    n = n_base + n_gust
    out = dict(P0=np.concatenate([pb, pg]))
    out["n"] = rng.integers(0, 1024, n).astype(np.float64)
    gbit = np.concatenate([np.zeros(n_base), np.ones(n_gust)])
    sbit = rng.integers(0, 2, n).astype(np.float64)
    out["f"] = gbit + 2.0 * sbit
    out["b"] = rng.random(n)
    out["ph1"], out["ph2"], out["ph3"] = rng.random(n), rng.random(n), rng.random(n)
    out["n_base"], out["n_gust"] = n_base, n_gust
    return out


CORNERS = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))    # esquina k -> (cx, cy)


def corner_xy(k):
    k = np.floor(np.asarray(k, float) + 0.5)
    cx = step(0.5, k) * step(k, 2.5)
    cy = step(1.5, k)
    return cx, cy


def encode(sd):
    """Lo que se escribe en la malla, por VERTICE (4 por mota, en el orden de CORNERS): LP (cm, espacio del actor),
    UV0..UV3. Devuelve arreglos (4n, ...)."""
    n = sd["P0"].shape[0]
    k = np.tile(np.arange(4.0), n)
    idx = np.repeat(np.arange(n), 4)
    cx, cy = corner_xy(k)
    LP = sd["P0"][idx] + np.stack([np.zeros(4 * n), (2 * cx - 1) * K["Corner"], (2 * cy - 1) * K["Corner"]], 1)
    return dict(LP=LP, UV0=np.stack([k, np.full(4 * n, 0.5)], 1),
                UV1=np.stack([sd["n"][idx], sd["ph1"][idx]], 1),
                UV2=np.stack([sd["f"][idx], sd["ph2"][idx]], 1),
                UV3=np.stack([sd["b"][idx], sd["ph3"][idx]], 1), idx=idx)


def flip_v(enc):
    out = dict(enc)
    for c in ("UV0", "UV1", "UV2", "UV3"):
        out[c] = np.stack([enc[c][:, 0], 1.0 - enc[c][:, 1]], 1)
    return out


def half_uv(enc):
    """Las UV como las guarda una StaticMesh sin 'Use Full Precision UVs' (fp16)."""
    out = dict(enc)
    for c in ("UV0", "UV1", "UV2", "UV3"):
        out[c] = enc[c].astype(np.float16).astype(np.float64)
    return out


# ---------------------------------------------------------------------------------------------
# VERTEX SHADER del polvo (vectorizado por vertice): lo mismo que DustVS.hlsl
# ---------------------------------------------------------------------------------------------
def dust_vs(enc, pv, camL=(0.0, 0.0, 0.0), mat=None, game_time=0.0):
    """enc = encode(seeds()) (o un subconjunto con las mismas claves); pv = lo que empuja el BP (VidaT, VidaG, VidaS,
    VidaE, VidaF, VidaSoul, VidaC: 4 floats cada uno, espacio del actor); camL = camara del ojo en el espacio del actor.
    Devuelve un dict con todo lo intermedio (por vertice).
    Rev. 2: (a) el meandro crece con la distancia (la velocidad angular propia no cae en las lejanas); (b) la rafaga
    deja una DERIVA neta a favor del viento (Hold: se relaja a 0 exacto despues del paso); (c) todo lo que decide el
    ALFA (luz, caida, confort) se calcula desde el punto CICLOPEO VidaC (igual en los dos ojos: sin rivalidad
    binocular); el sprite y su tamano siguen con la camara de cada ojo."""
    q = dict(MAT)
    if mat:
        q.update(mat)
    q.update({k: v for k, v in MAT_INTERNO.items() if k not in q})
    VT, VG, VS, VE, VF, VSo, VC = (np.asarray(pv.get(k, MAT_INTERNO[k]), float) for k in
                                   ("VidaT", "VidaG", "VidaS", "VidaE", "VidaF", "VidaSoul", "VidaC"))
    LP = np.asarray(enc["LP"], float)
    nv = LP.shape[0]
    camL = np.broadcast_to(np.asarray(camL, float), (nv, 3))
    cyc = float(VC[3] >= 0.5)
    camC = camL + (VC[0:3][None, :] - camL) * cyc
    kc = np.floor(enc["UV0"][:, 0] + 0.5)
    cx = step(0.5, kc) * step(kc, 2.5)
    cy = step(1.5, kc)
    P0 = LP - np.stack([np.zeros(nv), (2.0 * cx - 1.0) * K["Corner"], (2.0 * cy - 1.0) * K["Corner"]], 1)
    n = np.floor(enc["UV1"][:, 0] + 0.5)
    f = np.floor(enc["UV2"][:, 0] + 0.5)
    ph1, ph2, ph3 = enc["UV1"][:, 1], enc["UV2"][:, 1], enc["UV3"][:, 1]
    bi = enc["UV3"][:, 0]
    isG = step(0.5, f - 2.0 * np.floor(f / 2.0))
    sgn = 2.0 * step(0.5, np.floor(f / 2.0) - 2.0 * np.floor(f / 4.0)) - 1.0
    live = float(VT[3] >= 0.5)
    Tm = VT[0] * live + game_time * VT[1] * (1.0 - live)
    r0 = _norm(P0)
    # meandro: 3 senos con un numero ENTERO de vueltas por ventana de 1800 s (el BP envuelve Tm en 1800: continuo)
    nq = np.floor(n / 32.0)
    nr = n - 32.0 * nq
    k1 = K["KBase"] + nr
    k2 = K["KBase"] + nq
    m5 = n * 5.0 + nq
    k3 = K["KBase"] + (m5 - 32.0 * np.floor(m5 / 32.0))
    WT = K["WinT"]
    a1 = 2 * np.pi * frac(k1 * Tm / WT + ph1)
    a2 = 2 * np.pi * frac(k2 * Tm / WT + ph2)
    a3 = 2 * np.pi * frac(k3 * Tm / WT + ph3)
    mA = (q["MeanderCm"] * (0.6 + 0.8 * frac(ph1 * 3.7 + ph2))
          * np.clip(r0 / K["MeanderRef"], 1.0, max(q["MeanderFar"], 1.0)))
    M = mA[:, None] * np.stack([np.sin(a1), np.sin(a2), 0.6 * np.sin(a3)], 1)
    w0 = 0.0034906585            # 2 pi / 1800, el literal del HLSL
    Mv = (mA * w0 * VT[1])[:, None] * np.stack([k1 * np.cos(a1), k2 * np.cos(a2), 0.6 * k3 * np.cos(a3)], 1)
    # rafaga
    G = np.zeros((nv, 3))
    Gv = np.zeros((nv, 3))
    act = np.zeros(nv)
    if VS[3] > 0.0:
        dd = VG[2:4]
        rel = P0[:, 0:2] - VG[0:2][None, :]
        xg = rel @ dd
        eta = np.abs(rel[:, 0] * -dd[1] + rel[:, 1] * dd[0])
        rp = max(VE[2], 1.0)
        Ax = s5t((xg - VE[0]) / rp) * (1.0 - s5t((xg - (VE[1] - rp)) / rp))
        hx = 1.0 - s5t((eta - VF[0]) / max(VF[1] - VF[0], 1.0))
        Wd = max(VS[1], 1.0)
        tu = sat(((VS[0] - xg) / Wd + 2.0) * 0.25)
        Pu = tu * tu * tu * (tu * (6.0 * tu - 15.0) + 10.0)
        bl = 16.0 * tu * tu * (1.0 - tu) * (1.0 - tu)
        dP = 7.5 * tu * tu * (1.0 - tu) * (1.0 - tu)
        Ae = VS[3] * Ax * hx
        be = 2 * np.pi * (frac(ph3 * 5.3 + ph1) - 0.5) * 0.333
        e1 = np.array([dd[0], dd[1], 0.0])[None, :]
        e2 = sgn[:, None] * (np.cos(be)[:, None] * np.array([0.0, 0.0, 1.0])[None, :]
                             + np.sin(be)[:, None] * np.array([-dd[1], dd[0], 0.0])[None, :])
        Rr = q["EddyCm"] * (0.5 + bi) * np.clip(r0 / max(q["EddyNear"], 1.0), 0.3, 1.0)
        # el lazo, POLINOMICO: (lx, ly) = (0,6 x 6 raiz 3 P (1-P)(1-2P), 32 P^2 (1-P)^2): 0 exacto en P = 0 y P = 1
        Pc = 1.0 - Pu
        lx = 6.235383 * Pu * Pc * (1.0 - 2.0 * Pu)
        ly = 32.0 * Pu * Pu * Pc * Pc
        dlx = 6.235383 * (1.0 - 6.0 * Pu + 6.0 * Pu * Pu)
        dly = 64.0 * Pu * Pc * (1.0 - 2.0 * Pu)
        # la DERIVA a favor del viento: Rd x Ae x P x Hold (Hold = 1 durante la rafaga; despues vuelve a 0 EXACTO)
        Rd = q["DriftCm"] * (0.5 + bi) * np.clip(r0 / max(q["EddyNear"], 1.0), 0.3, max(q["DriftFar"], 0.3))
        Hd, HdV = VE[3], VF[2]
        G = (Rr * Ae)[:, None] * (lx[:, None] * e1 + ly[:, None] * e2) + (Rd * Ae * Pu * Hd)[:, None] * e1
        Gv = ((Rr * Ae * dP * VS[2] / Wd)[:, None] * (dlx[:, None] * e1 + dly[:, None] * e2)
              + (Rd * Ae * (dP * VS[2] / Wd * Hd + Pu * HdV))[:, None] * e1)
        act = Ae * bl
    P = P0 + M + G
    V = Mv + Gv
    # ---- el sprite, con la camara de ESTE ojo
    D = P - camL
    dist = np.maximum(_norm(D), 1.0e-3)
    # ---- el alfa, desde el punto ciclopeo (igual en los dos ojos)
    DC = P - camC
    distC = np.maximum(_norm(DC), 1.0e-3)
    DnC = DC / distC[:, None]
    sa, ca = math.sin(math.radians(q["SunAz"])), math.cos(math.radians(q["SunAz"]))
    se, ce = math.sin(math.radians(q["SunEl"])), math.cos(math.radians(q["SunEl"]))
    Ls = np.array([ce * ca, ce * sa, se])
    mu = DnC @ Ls
    g = min(max(q["SunG"], 0.0), 0.95)
    hgd = np.maximum(1.0 + g * g - 2.0 * g * mu, 1.0e-4)
    hgn = np.power((1.0 - g) * (1.0 - g) / hgd, 1.5)
    lit = q["SunBase"] + (1.0 - q["SunBase"]) * hgn
    br = 0.55 + 0.45 * frac(bi * 7.0 + ph2)
    m7 = n * 7.0
    ktw = 180.0 + (m7 - 271.0 * np.floor(m7 / 271.0))
    tw = 1.0 - q["Twinkle"] * 0.5 * (1.0 + np.sin(2 * np.pi * frac(ktw * Tm / WT + frac(ph1 + 0.618034 * ph3))))
    dfall = np.power(K["DistRef"] / np.maximum(distC, K["DistMin"]), q["DistTilt"])
    nearF = smoothstep(q["NearMin"], q["NearFull"], distC)
    farF = 1.0 - smoothstep(q["FarFade0"], q["FarFade1"], distC)
    SD = VSo[0:3][None, :] - camC
    sdl = np.maximum(_norm(SD), 1.0)
    ra = np.degrees(np.arcsin(sat(VSo[3] / sdl)))
    ang = np.degrees(np.arccos(np.clip(_dot(DnC, SD / sdl[:, None]), -1.0, 1.0)))
    soul = 1.0 + (smoothstep(ra + q["SoulMargin0"], ra + q["SoulMargin1"], ang) - 1.0) * float(VSo[3] >= 0.5)
    om = np.degrees(_norm(np.cross(V, DnC)) / distC)
    spf = 1.0 - smoothstep(q["SpeedFade0"], q["SpeedFade1"], om)
    aBase = q["DustAlpha"] * br * lit * dfall * tw * (1.0 + q["Lift"] * act)
    aGust = q["GustDustAlpha"] * br * lit * dfall * act
    al = (aBase + (aGust - aBase) * isG) * nearF * farF * soul * spf * VT[2]
    al = np.minimum(al, K["AlphaMax"])
    sdeg = np.maximum(q["DustSizeDeg"] * (1.0 + q["SizeVar"] * (2.0 * frac(bi * 3.1 + ph3) - 1.0)), K["MinDeg"])
    hsz = 0.5 * dist * np.tan(np.radians(sdeg)) * step(K["AlphaCut"], al)
    fw = _normalize(camL - P + np.array([1.0e-4, 0.0, 0.0])[None, :])
    rt = _normalize(np.cross(np.array([0.0, 0.0, 1.0])[None, :], fw) + np.array([0.0, 1.0e-4, 0.0])[None, :])
    up = np.cross(fw, rt)
    c = np.stack([cx, cy], 1) * 2.0 - 1.0
    dst = P + (rt * c[:, 0:1] + up * c[:, 1:2]) * hsz[:, None]
    DustV = np.stack([c[:, 0], c[:, 1], al, sat(hgn)], 1)
    offs = dst - LP
    bad = ~(_dot(offs, offs) < K["OffsGuard"] ** 2)
    offs[bad] = 0.0
    return dict(P0=P0, P=P, V=V, al=al, hsz=hsz, dist=dist, distC=distC, Dn=DnC, om=om, act=act, isG=isG, hgn=hgn,
                lit=lit, dst=dst, DustV=DustV, offs=offs, sdeg=sdeg, G=G, Gv=Gv, M=M)


def dust_ps(DustV, mat=None):
    q = dict(MAT)
    if mat:
        q.update(mat)
    DustV = np.asarray(DustV, float)
    c = DustV[..., 0:2]
    m = sat(1.0 - _dot(c, c))
    m = m * m
    a = sat(m * DustV[..., 2])
    col = np.asarray(q["ColDim"]) + (np.asarray(q["ColLit"]) - np.asarray(q["ColDim"])) * sat(DustV[..., 3])[..., None]
    return col * a[..., None], a


# ---------------------------------------------------------------------------------------------
# GustLeanVS (el valle): lo mismo que el HLSL. G = salida de ValleyGradVS (dh/dx, dh/dy, h, hf); LP en el espacio
# del valle; pv = GustP, GustQ, GustR, GustK, GustS.
# ---------------------------------------------------------------------------------------------
def gust_lean_vs(G, LP, Part=0.0, pv=None):
    q = dict(GUST_MAT)
    if pv:
        q.update(pv)
    G = np.array(G, dtype=np.float64, ndmin=2)
    LP = np.array(LP, dtype=np.float64, ndmin=2)
    GP, GQ, GR, GK, GS = (np.asarray(q[k], float) for k in ("GustP", "GustQ", "GustR", "GustK", "GustS"))
    ox, oy, oz, ow = G[:, 0].copy(), G[:, 1].copy(), G[:, 2].copy(), G[:, 3].copy()
    if Part < 0.5 and np.abs(GK).sum() > 0.0:
        dd = GP[2:4]
        rel = LP[:, 0:2] - GP[0:2][None, :]
        xg = rel @ dd
        eta = np.abs(rel[:, 1] * dd[0] - rel[:, 0] * dd[1])
        rp = max(GR[0], 1.0)
        Ax = s5t((xg - GQ[2]) / rp) * (1.0 - s5t((xg - (GQ[3] - rp)) / rp))
        hx = 1.0 - s5t((eta - GR[1]) / max(GR[2] - GR[1], 1.0))
        tu = sat(((GQ[0] - xg) / max(GQ[1], 1.0) + 2.0) * 0.25)
        bl = 16.0 * tu * tu * (1.0 - tu) * (1.0 - tu)
        sv = LP[:, 0:2] - GS[0:2][None, :]
        rs = np.sqrt((sv * sv).sum(1))
        nf = s5t((rs - GR[3]) / max(GR[3], 1.0))
        a = Ax * hx * bl * nf
        tvx = -sv[:, 0] / np.maximum(rs, 1.0)
        tvy = -sv[:, 1] / np.maximum(rs, 1.0)
        ox = G[:, 0] - a * (GK[1] + GK[3] * tvx)
        oy = G[:, 1] - a * (GK[2] + GK[3] * tvy)
        gl = a * GK[0]
        ow = np.where(gl > 0.0, np.sqrt(G[:, 3] * G[:, 3] + gl), G[:, 3])
    return np.stack([ox, oy, oz, ow], 1)


# ---------------------------------------------------------------------------------------------
# Transform de un actor sin escala (loc, yaw): mundo <-> local
# ---------------------------------------------------------------------------------------------
class Xf:
    def __init__(self, loc, yaw=0.0):
        self.loc = np.asarray(loc, float)
        self.yaw = float(yaw)

    def axes(self):
        y = math.radians(self.yaw)
        return (np.array([math.cos(y), math.sin(y), 0.0]), np.array([-math.sin(y), math.cos(y), 0.0]),
                np.array([0.0, 0.0, 1.0]))

    def inv_loc(self, p):
        F, R, U = self.axes()
        d = np.asarray(p, float) - self.loc
        return np.array([d @ F, d @ R, d @ U])

    def inv_dir(self, v):
        F, R, U = self.axes()
        v = np.asarray(v, float)
        return np.array([v @ F, v @ R, v @ U])

    def loc_to_world(self, p):
        F, R, U = self.axes()
        p = np.asarray(p, float)
        return self.loc + p[..., 0:1] * F + p[..., 1:2] * R + p[..., 2:3] * U


def ex(dt, tau):
    return 1.0 - math.exp(-dt / max(tau, 1.0e-4))


# ---------------------------------------------------------------------------------------------
# BLUEPRINT: BP_ValleyLife_SC (un solo reloj de rafagas). Traduccion 1:1 en scripts/vida.dsl.
# ---------------------------------------------------------------------------------------------
class VidaBP:
    """Estado de BP_ValleyLife_SC (variables Z-Vida) y su paso por cuadro. Todo en el MUNDO; el empuje convierte al
    espacio del polvo y del valle.
    Rev. 2: la rafaga deja una DERIVA a favor del viento que se RELAJA despues del paso (Hold 1 -> 0, fase integrada,
    dura min(DriftRelax, la calma que sigue): nunca atrasa la agenda); bVida / VidaAmount 0 tambien cortan las rafagas
    nuevas; 'GustNow' (bForce) lanza una lateral apenas se puede (acelera la relajacion, no espera el soplo); PerfMode 3 =
    banco sin rafagas (PerfE0..E4); el punto ciclopeo sale de la camara del rig (VidaC)."""

    def __init__(self, actor=Xf(ACTOR), valley=Xf((0.0, 0.0, VALLE_Z)), bp=None, soul=SOUL_W, with_valley=True,
                 n_gust_snd=3, n_breath_snd=1, soul_scale=1.0, cam=None):
        self.q = dict(BP)
        if bp:
            self.q.update(bp)
        self.actor, self.valley = actor, (valley if with_valley else None)
        self.soul = None if soul is None else np.asarray(soul, float)
        self.soul_scale = soul_scale
        self.cam = None if cam is None else np.asarray(cam, float)     # camara del rig (mundo) o None (sin rig / editor)
        self.n_gust_snd, self.n_breath_snd = n_gust_snd, n_breath_snd
        self.reset()

    # ---- VidaReset (BeginPlay) = VidaZero
    def reset(self):
        q = self.q
        self.Clock = 0.0
        self.Wait = q["FirstGap"]
        self.bGustOn = False
        self.GustIdx = 0.0
        self.GustKind = 0.0
        self.S = self.S0 = self.S1 = self.Sdot = 0.0
        self.W, self.E0, self.E1, self.Ramp, self.Lf0, self.Lf1 = 700.0, 0.0, 0.0, 1000.0, 3000.0, 5500.0
        self.OrgW = np.zeros(3)
        self.DirW = np.array([0.0, 1.0, 0.0])
        self.SndOffW = np.zeros(3)
        self.SndMin = -1.0e6
        self.Amp = 0.0
        self.Hold = self.HoldPh = self.HoldV = 0.0
        self.HoldRate = 1.0
        self.bForce = False
        self.Tm = 0.0
        self.Rate = q["MeanderRate"]
        self.GlobBase = 0.0
        self.Glob = 0.0
        self.ActUser = 0.0
        self.VSig = self.VGate = 0.0
        self.Sprev = 0.0
        self.bPrimed = False
        self.Vel = self.VelF = self.Flow = self.InhHold = 0.0
        self.bExhOnset = False
        self.Life = 22.0
        self.PerfMode = 0
        self.bSndWarned = False
        self.log = []
        self.sounds = []       # (t, kind, variante, pitch, volumen, posicion)

    def _fwd(self):
        return self.actor.axes()[0]

    def gust(self):
        return dict(O=self.OrgW, d=self.DirW, S=self.S, W=self.W, E0=self.E0, E1=self.E1, Ramp=self.Ramp,
                    Lf0=self.Lf0, Lf1=self.Lf1, Amp=self.Amp)

    # ---- VidaBreath: el detector de exhalacion (misma cuenta que el aliento: velocidad filtrada + histeresis + latch)
    def breath(self, dt):
        b = BREATH
        raw = (self.VSig - self.Sprev) / dt if (self.bPrimed and self.VGate > GATE_ON) else 0.0
        self.Vel = min(max(raw, -b["VelMax"]), b["VelMax"])
        self.Sprev = self.VSig
        self.bPrimed = True
        self.VelF += (self.Vel - self.VelF) * ex(dt, b["VelTau"])
        vf, old = self.VelF, self.Flow
        if old > 0.5:
            new = 1.0 if vf > b["VelStay"] else 0.0
        elif old < -0.5:
            new = -1.0 if vf < -b["VelStay"] else 0.0
        else:
            new = 1.0 if vf > b["VelEnter"] else (-1.0 if vf < -b["VelEnter"] else 0.0)
        self.bExhOnset = (new < -0.5) and (old > -0.5) and (self.InhHold >= b["InhMin"])
        if self.bExhOnset:
            self.InhHold = 0.0
        elif new > 0.5:
            self.InhHold += dt
        elif self.InhHold < b["InhMin"]:
            self.InhHold = 0.0
        self.Flow = new

    # ---- VidaStartLat / VidaStartBreath (SOLO la geometria de la rafaga) + VidaGo (lo comun)
    def _start_common(self, kind, O, d, E0, E1, ramp, W, lf0, lf1, life, snd_off, snd_min):
        self.GustKind = kind
        self.OrgW, self.DirW = np.asarray(O, float), np.asarray(d, float)
        self.E0, self.E1, self.Ramp, self.W, self.Lf0, self.Lf1 = E0, E1, ramp, W, lf0, lf1
        self.Life = life
        self.SndOffW, self.SndMin = np.asarray(snd_off, float), snd_min
        # VidaGo
        self.S0 = E0 - 2.0 * W
        self.S1 = E1 + 2.0 * W
        self.S = self.S0
        self.Sdot = (self.S1 - self.S0) / max(self.Life, 1.0)
        self.bGustOn = True
        self.Amp = self.q["GustAmount"]
        self.Hold, self.HoldPh, self.HoldV = 1.0, 0.0, 0.0
        self.bForce = False

    def start_lateral(self, sign=0.0):
        q, k = self.q, self.GustIdx
        yaw = self.actor.yaw
        if sign == 0.0:
            sign = 1.0 if frac(k * PHI[1] + 0.25) < 0.5 else -1.0
        jit = q["JitterDeg"] * (2.0 * frac(k * PHI[3] + 0.1) - 1.0)
        ang = math.radians(yaw + 90.0 * sign + jit)
        d = np.array([math.cos(ang), math.sin(ang), 0.0])
        m = q["OffsetMin"] + (q["OffsetMax"] - q["OffsetMin"]) * frac(k * PHI[2] + 0.3)
        F = self._fwd()
        O = np.array([self.actor.loc[0], self.actor.loc[1], 0.0]) + F * m
        self._start_common(0.0, O, d, -q["PathHalf"], q["PathHalf"], q["GustRamp"], q["GustW"], q["FrontHalf0"],
                           q["FrontHalf1"], q["GustLife"], F * (q["SndFwd"] - m), -1.0e6)

    def launch_lateral(self):
        """VidaLaunchLat: la geometria + el sonido + el indice (el sonido usa el indice ANTES de sumarlo)."""
        q = self.q
        self.start_lateral(0.0)
        self._play(0, min(max(q["SndLen"] / max(q["GustLife"], 1.0), PITCH_MIN), PITCH_MAX))
        self.GustIdx += 1.0

    def start_breath(self):
        q, k = self.q, self.GustIdx
        jit = q["BreathJitter"] * (2.0 * frac(k * PHI[3] + 0.1) - 1.0)
        ang = math.radians(self.actor.yaw + jit)
        d = np.array([math.cos(ang), math.sin(ang), 0.0])
        O = np.array([self.actor.loc[0], self.actor.loc[1], 0.0])
        self._start_common(1.0, O, d, 0.0, q["BreathLen"], q["BreathRamp"], q["BreathW"], q["BreathHalf0"],
                           q["BreathHalf1"], q["BreathLife"], np.zeros(3), 150.0)

    def launch_breath(self):
        """VidaLaunchBreath: el soplo (sale del usuario hacia adelante) + su sonido + el indice."""
        q = self.q
        self.start_breath()
        self._play(1, min(max(q["BreathSndLen"] / max(q["BreathLife"], 1.0), PITCH_MIN), PITCH_MAX))
        self.GustIdx += 1.0

    def _play(self, kind, pitch):
        n = self.n_gust_snd if kind == 0 else self.n_breath_snd
        if n > 0:
            var = int(self.GustIdx) % n
            self.sounds.append((self.Clock, kind, var, pitch, self.q["GustVolume"], tuple(self.sound_pos())))
        elif not self.bSndWarned:
            self.bSndWarned = True
            self.log.append("VIDA: la rafaga no tiene sonido (GustSounds / BreathSounds vacios)")

    def next_gap(self):
        q = self.q
        return q["GapMin"] + (q["GapMax"] - q["GapMin"]) * frac(self.GustIdx * PHI[0] + 0.5)

    def gust_now(self):
        """'ke * GustNow': una lateral apenas se pueda (sin esperar la calma ni el soplo)."""
        self.bForce = True

    # ---- VidaRelax: la deriva vuelve a 0 (fase integrada; con bForce se acelera a 3 s: continuo, sin salto)
    def relax(self, dt):
        if self.Hold <= 0.0:
            return
        r = max(self.HoldRate, 1.0 / 3.0) if self.bForce else self.HoldRate
        self.HoldPh = min(self.HoldPh + r * dt, 1.0)
        p = self.HoldPh
        self.Hold = 1.0 - p * p * p * (p * (6.0 * p - 15.0) + 10.0)
        self.HoldV = -(30.0 * (p * p * ((1.0 - p) * (1.0 - p)))) * r
        if self.HoldPh >= 1.0:
            self.Hold = 0.0
            self.HoldV = 0.0
            self.Amp = 0.0

    # ---- VidaSchedule: el reloj de rafagas
    def schedule(self, dt):
        q = self.q
        if self.bGustOn:
            self.S = min(self.S + self.Sdot * dt, self.S1)
            if self.S >= self.S1:                                    # VidaEnd
                self.bGustOn = False
                self.Wait = self.next_gap()
                self.HoldRate = 1.0 / max(min(q["DriftRelax"], self.Wait), 1.0)
                self.HoldPh = 0.0
            return
        self.Wait -= dt
        self.relax(dt)
        # VidaMaybe
        f = self.bForce
        ok = (self.Hold <= 0.0 and (self.Wait <= 0.0 or f) and (q["bVida"] and q["VidaAmount"] > 0.0)
              and (q["bGusts"] or f) and self.PerfMode != 3)
        if not ok:
            return
        # VidaDue
        every = max(q["BreathEvery"], 1.0)
        turno = every * frac(self.GustIdx / every) > every - 1.5
        quiere = q["bBreathGusts"] and self.VGate > 0.5 and turno and not f
        if not quiere:
            self.launch_lateral()
            return
        if self.bExhOnset:
            self.launch_breath()
            return
        if self.Wait < -q["BreathWait"]:
            self.launch_lateral()

    # ---- VidaStep: meandro integrado (se agita con la rafaga), presencia
    def step_state(self, dt):
        q = self.q
        F = self._fwd()
        probe = self.actor.loc + F * PROBE_FWD
        self.ActUser = gust_act(probe[:2], self.gust())
        self.Rate = q["MeanderRate"] * (1.0 + q["GustStir"] * self.ActUser)
        WT = K["WinT"]
        self.Tm = float(frac((self.Tm + self.Rate * dt) / WT) * WT)
        amt = q["VidaAmount"] if q["bVida"] else 0.0
        self.GlobBase += (amt - self.GlobBase) * ex(dt, q["GlobTau"])
        self.Glob = self.GlobBase

    def perf(self):
        """VidaPerf. 2 = lleno (el polvo pleno y una rafaga lateral quieta en la mitad, s = 0); 1 = sin vida (polvo
        oculto, la franja apagada: Amp 0); 3 = banco sin rafagas (polvo normal, Amp 0, ninguna rafaga nueva)."""
        if self.PerfMode == 2:
            self.Glob = 1.0
            if self.bGustOn:
                self.S = 0.0
        if self.PerfMode == 1 or self.PerfMode == 3:
            self.Amp = 0.0

    def bench_full(self):
        """VidaBenchFull (PerfE5 / PerfV2): modo 2 y, si no hay rafaga, una lateral (solo la geometria)."""
        self.PerfMode = 2
        if not self.bGustOn:
            self.start_lateral(1.0)

    def step(self, dt, S=0.0, On=0.0):
        dt = max(dt, 1.0e-4)
        self.Clock += dt
        self.VSig, self.VGate = S, On
        self.breath(dt)
        self.schedule(dt)
        self.step_state(dt)
        self.perf()

    # ---- VidaPushDust / VidaPushValley: lo que ve cada material
    def push_dust(self, live=1.0):
        a = self.actor
        O = a.inv_loc(np.array([self.OrgW[0], self.OrgW[1], 0.0]))
        d = a.inv_dir(np.array([self.DirW[0], self.DirW[1], 0.0]))
        soul = ((a.inv_loc(self.soul).tolist() + [self.q["SoulR"] * min(max(self.soul_scale, 0.0), 1.0)])
                if self.soul is not None else [0.0, 0.0, 0.0, 0.0])
        cam = (a.inv_loc(self.cam).tolist() + [1.0]) if (self.cam is not None and live > 0.5) else [0.0, 0.0, 0.0, 0.0]
        return dict(VidaT=np.array([self.Tm, self.Rate, self.Glob, live]),
                    VidaG=np.array([O[0], O[1], d[0], d[1]]),
                    VidaS=np.array([self.S, self.W, self.Sdot, self.Amp]),
                    VidaE=np.array([self.E0, self.E1, self.Ramp, self.Hold]),
                    VidaF=np.array([self.Lf0, self.Lf1, self.HoldV, 0.0]),
                    VidaSoul=np.array(soul),
                    VidaC=np.array(cam))

    def push_valley(self):
        if self.valley is None:
            return None
        q, v = self.q, self.valley
        O = v.inv_loc(np.array([self.OrgW[0], self.OrgW[1], 0.0]))
        d = v.inv_dir(np.array([self.DirW[0], self.DirW[1], 0.0]))
        seat = v.inv_loc(self.actor.loc)
        la = math.radians(q["LeanAz"])
        ln = v.inv_dir(np.array([math.cos(la), math.sin(la), 0.0]) * q["GustLean"])
        A = self.Amp if self.bGustOn else 0.0        # en la relajacion el frente ya paso: la franja no hace nada
        return dict(GustP=np.array([O[0], O[1], d[0], d[1]]),
                    GustQ=np.array([self.S, self.W, self.E0, self.E1]),
                    GustR=np.array([self.Ramp, self.Lf0, self.Lf1, q["GustNear"]]),
                    GustK=np.array([A * q["GustLight"], A * ln[0], A * ln[1], A * q["GustRuffle"]]),
                    GustS=np.array([seat[0], seat[1], 0.0, 0.0]))

    def sound_pos(self):
        """VidaAudio: la fuente del soplo va con el frente (lateral: por una linea paralela a la trayectoria, a SndFwd
        delante del usuario; soplo: sobre la trayectoria, desde 1,5 m), a la altura de los oidos."""
        return (self.OrgW + self.SndOffW + self.DirW * max(self.S, self.SndMin)
                + np.array([0.0, 0.0, self.actor.loc[2]]))

    # ---- PreviewVida (Construction Script): una rafaga de muestra congelada en PreviewGust (0 = ninguna)
    def preview(self):
        q = self.q
        self.reset()
        pg = min(max(q["PreviewGust"], 0.0), 1.0)
        if q["PreviewKind"] > 0.5:
            self.start_breath()
        else:
            self.start_lateral(1.0 if q["PreviewDir"] >= 0.0 else -1.0)
        self.S = self.S0 + (self.S1 - self.S0) * pg
        self.Amp = q["GustAmount"] if pg > 0.0 else 0.0
        self.Rate = q["MeanderRate"]
        self.Tm = 0.0
        self.Glob = q["VidaAmount"] if q["bVida"] else 0.0
        return self.push_dust(live=0.0), self.push_valley()


# ---------------------------------------------------------------------------------------------
# Senales de prueba (la respiracion del usuario, como en el aliento)
# ---------------------------------------------------------------------------------------------
def belly(t, tin=4.0, h1=3.0, tout=4.0, h2=3.0, lag=0.4):
    """MPC_Breath.Signed idealizada (despues del seguidor del rig): sube en la inhalacion, baja en la exhalacion."""
    T = tin + h1 + tout + h2
    tt = (t - lag) % T
    if tt < tin:
        return -1.0 + (1.0 - math.cos(math.pi * tt / tin))
    if tt < tin + h1:
        return 1.0
    if tt < tin + h1 + tout:
        p = (tt - tin - h1) / tout
        return 1.0 - (1.0 - math.cos(math.pi * p))
    return -1.0
