# -*- coding: utf-8 -*-
"""valley_model.py - MODELO NUMPY DE REFERENCIA del valle de la respiracion (Entering), v2.

Especificacion: docs/PLAN-VALLE-ENTERING-2026-09-27.md (seccion "v2" arriba de todo, y secciones 2-7 y 12).
Es la misma cuenta que los tres Custom (scripts/hlsl/ValleyHeightVS.hlsl, ValleyGradVS.hlsl, ValleyPS.hlsl),
escrita VECTORIZADA en numpy (float64). Solo numpy: no importa bpy ni Unreal.

Quien lo usa:
  - hlsl/Valley_check.py        compara la traduccion MECANICA de los .hlsl contra este modelo y contra la seccion 12.
  - preview_breath_valley.py    colorea la malla en Blender headless con este modelo.
  - las mediciones de la v2      (escala, linea del piso, movimiento) de la spec.

Convenciones (spec, seccion 1): cm y s, ejes de Unreal (X adelante, Y DERECHA, Z arriba), azimut desde +X hacia +Y.
El usuario esta en el origen con los ojos en (0, 0, 120); el metaball en (380, 0, 125).

LA ALTURA v2 (todo radial en r = |p|, todas las rampas con la quintica S5, que es C2):
  S5(a, b, x) = t^3 (t (6 t - 15) + 10),  t = saturate((x - a)/(b - a));  S5' = 30 t^2 (1 - t)^2 / (b - a)
  capa 1, colinas medias:  HillAmp * envH(r) * S5(DuneLow, DuneHigh, sigmaH)
                           envH = S5(HillNear, HillFull, r) * (1 - S5(HillFade, HillEnd, r))
  capa 2, lejos:           FarBase * S5(FarIn, FarCrest, r) + FarAmp * S5(FarIn, FarFull, r) * S5(FAR_LOW, FAR_HIGH, sigmaF)
  capa 3, oleaje viajero:  SwellAmp * S5(SwellNear, SwellFar, r) * (r / SwellFar) * s(p, t)
                           (amplitud ANGULAR constante SwellAmp/SwellFar desde SwellFar: A crece con r)
  total:                   h = back(r) * (capa 1 + capa 2 + capa 3),  back = 1 - S5(FarCrest, FarBack, r)
  sigma = sum_i a_i (1 + MorphAmt m_i(t)) sin(k_i . p + phi_i) / 2.65   (las 4 dunas de la v1, escaladas y giradas)
  s     = sum_j w_j sin(2 pi frac((d_j . p)/(lambda_j SwellScale) + c_j - frac(SwellSpeed t / T_j))) / 2.95
"""
import math

import numpy as np

# ---------------------------------------------------------------------------------------------
# Constantes del codigo (identicas en el HLSL; se escriben una por una, sin arreglos)
# ---------------------------------------------------------------------------------------------
# Dunas (spec 3.3, las mismas de la v1): (angulo deg, lambda cm, peso, fase rad, periodo s, fase temporal rad)
DUNAS = (
    (18.0, 3000.0, 1.00, 0.0, 53.0, 0.0),
    (101.0, 2200.0, 0.75, 1.7, 67.0, 2.1),
    (143.0, 1650.0, 0.55, 4.1, 41.0, 4.4),
    (232.0, 1250.0, 0.35, 2.9, 83.0, 1.3),
)
SA = 2.65                      # suma de los pesos de las dunas
# Oleaje (4 ondas planas viajeras): (angulo deg, lambda cm, periodo s, peso, fase EN VUELTAS)
# Direcciones repartidas: la suma de w*c*d da una deriva neta de ~0,5 % (no simula que el usuario se traslade)
OLAS = (
    (20.0, 9000.0, 42.0, 1.00, 0.00),
    (175.0, 7000.0, 36.0, 0.85, 0.37),
    (255.0, 5500.0, 31.0, 0.70, 0.73),
    (95.0, 4000.0, 46.0, 0.40, 0.18),
)
SW = 2.95                      # suma de los pesos de las olas
FAR_LOW, FAR_HIGH = -0.7, 1.2  # umbral de las colinas lejanas (constantes: las perillas lejanas son FarAmp/FarScale)
EYE = np.array([0.0, 0.0, 120.0])
METABALL = np.array([380.0, 0.0, 125.0])

# ---------------------------------------------------------------------------------------------
# Parametros: defaults de la tabla 7.1 v2
# ---------------------------------------------------------------------------------------------
P = dict(
    Part=0.0, PerfMode=0.0,
    # 1 - Colinas (capa 1, colinas medias)
    HillAmp=2200.0, HillScale=8.0, HillSeed=63.0,
    HillNear=4500.0, HillFull=12000.0, HillFade=19000.0, HillEnd=26000.0,
    DuneLow=-0.35, DuneHigh=1.2,
    # 2 - Lejos (capa 2, anillo + colinas lejanas; garantia del horizonte y retiro detras de la cresta)
    FarBase=2600.0, FarAmp=5500.0, FarScale=22.0, FarSeed=151.0,
    FarIn=28000.0, FarFull=40000.0, FarCrest=47000.0, FarBack=59000.0,
    # 3 - Movimiento (oleaje viajero + respiracion de las colinas)
    SwellAmp=560.0, SwellNear=1500.0, SwellFar=12000.0, SwellScale=2.5, SwellSpeed=1.0, SwellSeed=0.0,
    MorphAmt=0.15, MorphSpeed=1.0,
    # 4 - Luz y superficie
    LightAz=20.0, LightEl=25.0, Wrap=0.3, ShadeFloor=0.0, SlopeDark=1.2,
    ColLit=(0.434, 0.527, 0.855), ColShadow=(0.061, 0.117, 0.352), ColSheen=(0.855, 0.761, 0.913),
    Sheen=0.28, SheenW=0.3, SheenBack=0.35, CrestLight=0.2,
    # 5 - Sombra
    ShadowSoft=0.8, ShadowTint=(0.305, 0.352, 0.68), ShadowMax=0.8,
    # 6 - Cielo
    SkyZenith=(0.216, 0.328, 0.597), SkyHorizon=(0.597, 0.624, 0.839), SkyGlow=(0.831, 0.68, 0.855),
    SkyGradTop=0.7, GlowAz=20.0, GlowEl=2.0, GlowPow=2.0, GlowHeight=0.45, GlowAmt=0.8,
    # 7 - Luna
    MoonAz=-40.0, MoonEl=7.0, MoonRadius=9.0, MoonEdge=0.03, MoonColor=(0.73, 0.644, 0.839),
    MoonOpacity=0.55, MoonFill=0.2, MoonRim=1.0,
    # 8 - Niebla (por distancia + de altura, integrada a lo largo del rayo)
    FogStart=1500.0, FogDist=45000.0, FogMax=0.9, HFogDist=60000.0, HFogFall=1500.0, DitherAmt=1.0,
    # 9 - Interno (los escribe el BP)
    ShadowCenter=(380.0, 0.0, 125.0), ShadowRadius=85.0, ShadowStrength=1.5,
)


def params(**over):
    q = dict(P)
    q.update(over)
    return q


# ---------------------------------------------------------------------------------------------
# utilidades (identicas a HLSL)
# ---------------------------------------------------------------------------------------------
def sat(x):
    return np.clip(x, 0.0, 1.0)


def s5(a, b, x):
    """Quintica S5 (C2) y su derivada. Con b - a >= 1 garantizado por quien llama."""
    t = sat((np.asarray(x, dtype=np.float64) - a) / (b - a))
    return t * t * t * (t * (6.0 * t - 15.0) + 10.0), 30.0 * t * t * (1.0 - t) * (1.0 - t) / (b - a)


def smoothstep(a, b, x):
    t = sat((np.asarray(x, dtype=np.float64) - a) / (b - a))
    return t * t * (3.0 - 2.0 * t)


def lerp(a, b, t):
    return a + (b - a) * t


def frac(x):
    return x - np.floor(x)


def dir_d(az, el):
    """D(az, el) de la seccion 1: azimut desde +X hacia +Y (derecha), elevacion sobre la horizontal."""
    a, e = math.radians(az), math.radians(el)
    return np.array([math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)])


def srgb(c):
    c = np.clip(c, 0.0, 1.0)
    return np.where(c <= 0.0031308, 12.92 * c, 1.055 * np.power(c, 1.0 / 2.4) - 0.055)


def srgb8(c):
    return tuple(int(v) for v in np.round(255.0 * srgb(np.asarray(c, dtype=np.float64))))


def lum(c):
    c = np.asarray(c)
    return 0.2126 * c[..., 0] + 0.7152 * c[..., 1] + 0.0722 * c[..., 2]


# ---------------------------------------------------------------------------------------------
# Altura
# ---------------------------------------------------------------------------------------------
def _sigma(x, y, t, scale, seed, q):
    """Campo de dunas escalado y girado; la amplitud de cada seno respira (MorphAmt). Devuelve sigma y su gradiente."""
    ks = 2.0 * math.pi / max(scale, 0.05)
    w = 2.0 * math.pi * q["MorphSpeed"] * t
    sig = 0.0
    gx = 0.0
    gy = 0.0
    for (ang, lam, amp, fase, per, psi) in DUNAS:
        a = math.radians(seed + ang)
        kx = ks / lam * math.cos(a)
        ky = ks / lam * math.sin(a)
        g = kx * x + ky * y + fase
        m = math.sin(w / per + psi)
        c = amp * (1.0 + q["MorphAmt"] * m)
        sig = sig + c * np.sin(g)
        cg = c * np.cos(g)
        gx = gx + cg * kx
        gy = gy + cg * ky
    return sig / SA, gx / SA, gy / SA


def _oleaje(x, y, t, q):
    """s(p, t) en [-1, 1], su gradiente y ds/dt. Fase en vueltas con frac (como el HLSL)."""
    isc = 1.0 / max(q["SwellScale"], 0.05)
    s = 0.0
    gx = 0.0
    gy = 0.0
    st = 0.0
    for (ang, lam, per, wgt, c0) in OLAS:
        a = math.radians(q["SwellSeed"] + ang)
        dx, dy = math.cos(a), math.sin(a)
        tau = frac(q["SwellSpeed"] * t / per)
        g = 2.0 * math.pi * frac((dx * x + dy * y) * (isc / lam) + c0 - tau)
        sg, cg = np.sin(g), np.cos(g)
        s = s + wgt * sg
        kk = 2.0 * math.pi * isc / lam
        gx = gx + wgt * cg * kk * dx
        gy = gy + wgt * cg * kk * dy
        st = st - wgt * cg * 2.0 * math.pi * q["SwellSpeed"] / per
    return s / SW, gx / SW, gy / SW, st / SW


def valley_grad(x, y, t, q=None, capas=(1, 2, 3), con_dt=False):
    """ValleyGradVS: devuelve (dh/dx, dh/dy, h, hf) (y dh/dt si con_dt). x, y en cm (arreglos), t en s.
    capas: que capas sumar (para aislar cada una en las mediciones; el HLSL suma las tres)."""
    q = P if q is None else q
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    r = np.sqrt(x * x + y * y)
    rs = np.maximum(r, 1.0)
    h = np.zeros_like(r)
    gr = np.zeros_like(r)      # d/dr de las envolventes radiales (se multiplica por p/r)
    gx = np.zeros_like(r)
    gy = np.zeros_like(r)
    hf = np.zeros_like(r)
    ht = np.zeros_like(r)
    if 1 in capas:
        a, da = s5(q["HillNear"], max(q["HillFull"], q["HillNear"] + 1.0), r)
        b, db = s5(q["HillFade"], max(q["HillEnd"], q["HillFade"] + 1.0), r)
        env = a * (1.0 - b)
        denv = da * (1.0 - b) - a * db
        sig, sx, sy = _sigma(x, y, t, q["HillScale"], q["HillSeed"], q)
        f, df = s5(q["DuneLow"], max(q["DuneHigh"], q["DuneLow"] + 0.01), sig)
        h = h + q["HillAmp"] * env * f
        gr = gr + q["HillAmp"] * denv * f
        gx = gx + q["HillAmp"] * env * df * sx
        gy = gy + q["HillAmp"] * env * df * sy
        hf = hf + env * f
        if con_dt:
            ht = ht + q["HillAmp"] * env * df * _dsig_dt(x, y, t, q["HillScale"], q["HillSeed"], q)
    FC = max(q["FarCrest"], q["FarIn"] + 1.0)
    FB = max(q["FarBack"], FC + 1.0)
    if 2 in capas:
        ring, dring = s5(q["FarIn"], FC, r)
        envF, denvF = s5(q["FarIn"], max(q["FarFull"], q["FarIn"] + 1.0), r)
        sig, sx, sy = _sigma(x, y, t, q["FarScale"], q["FarSeed"], q)
        f, df = s5(FAR_LOW, FAR_HIGH, sig)
        h = h + q["FarBase"] * ring + q["FarAmp"] * envF * f
        gr = gr + q["FarBase"] * dring + q["FarAmp"] * denvF * f
        gx = gx + q["FarAmp"] * envF * df * sx
        gy = gy + q["FarAmp"] * envF * df * sy
        hf = hf + envF * f
        if con_dt:
            ht = ht + q["FarAmp"] * envF * df * _dsig_dt(x, y, t, q["FarScale"], q["FarSeed"], q)
    if 3 in capas:
        SF = max(q["SwellFar"], q["SwellNear"] + 1.0)
        wq, dwq = s5(q["SwellNear"], SF, r)
        dwq = dwq * r / SF + wq / SF              # amplitud ANGULAR constante desde SwellFar: A = SwellAmp*S5*r/SwellFar
        wq = wq * r / SF
        s, sx, sy, st = _oleaje(x, y, t, q)
        h = h + q["SwellAmp"] * wq * s
        gr = gr + q["SwellAmp"] * dwq * s
        gx = gx + q["SwellAmp"] * wq * sx
        gy = gy + q["SwellAmp"] * wq * sy
        if con_dt:
            ht = ht + q["SwellAmp"] * wq * st
    tb, dtb = s5(FC, FB, r)
    back = 1.0 - tb
    gxo = back * (gx + gr * x / rs) - dtb * h * x / rs
    gyo = back * (gy + gr * y / rs) - dtb * h * y / rs
    out = (gxo, gyo, back * h, sat(back * hf))
    if con_dt:
        return out + (back * ht,)
    return out


def _dsig_dt(x, y, t, scale, seed, q):
    ks = 2.0 * math.pi / max(scale, 0.05)
    w = 2.0 * math.pi * q["MorphSpeed"] * t
    dw = 2.0 * math.pi * q["MorphSpeed"]
    acc = 0.0
    for (ang, lam, amp, fase, per, psi) in DUNAS:
        a = math.radians(seed + ang)
        g = ks / lam * (math.cos(a) * x + math.sin(a) * y) + fase
        acc = acc + amp * q["MorphAmt"] * math.cos(w / per + psi) * (dw / per) * np.sin(g)
    return acc / SA


def valley_h(x, y, t, q=None, capas=(1, 2, 3)):
    return valley_grad(x, y, t, q, capas)[2]


# ---------------------------------------------------------------------------------------------
# Sombreado (ValleyPS)
# ---------------------------------------------------------------------------------------------
def direcciones(q=None):
    q = P if q is None else q
    return (dir_d(q["LightAz"], q["LightEl"]), dir_d(q["GlowAz"], q["GlowEl"]),
            dir_d(q["MoonAz"], q["MoonEl"]), math.cos(math.radians(q["MoonRadius"])))


def cielo(dv, q=None, con_luna=True):
    """ValleyPS, cielo. dv (..., 3) = direccion de la mirada, unitaria. Sin dither."""
    q = P if q is None else q
    _, G, M, cosR = direcciones(q)
    dv = np.asarray(dv, dtype=np.float64)
    Hz, Ze, Gl = (np.array(q[k], dtype=np.float64) for k in ("SkyHorizon", "SkyZenith", "SkyGlow"))
    sky = lerp(Hz, Ze, smoothstep(0.0, max(q["SkyGradTop"], 0.01), dv[..., 2])[..., None])
    hxy = dv[..., :2]
    hz = hxy / np.sqrt(np.maximum((hxy * hxy).sum(-1), 1e-8))[..., None]
    gh = G[:2] / math.sqrt(max(float(G[0] ** 2 + G[1] ** 2), 1e-8))
    gaz = np.power(np.maximum((hz * gh).sum(-1), 1e-6), max(q["GlowPow"], 0.1))
    gel = 1.0 - smoothstep(0.0, max(q["GlowHeight"], 0.001), np.abs(dv[..., 2] - G[2]))
    sky = lerp(sky, Gl, sat(q["GlowAmt"] * gaz * gel)[..., None])
    if not con_luna:
        return sky
    cosA = (dv * M).sum(-1)
    rho = np.sqrt(np.maximum(1.0 - cosA, 0.0) / max(1.0 - cosR, 1e-6))
    me = max(q["MoonEdge"], 0.001)
    disc = 1.0 - smoothstep(1.0 - me, 1.0 + me, rho)
    o = dv - M * cosA[..., None]
    gm = G - M * float(np.dot(G, M))
    side = 0.5 + 0.5 * (o * gm).sum(-1) / np.sqrt(np.maximum((o * o).sum(-1), 1e-10)) \
        / math.sqrt(max(float(np.dot(gm, gm)), 1e-10))
    rim = smoothstep(0.6, 1.0, rho) * side * side
    a = sat(q["MoonOpacity"] * disc * (q["MoonFill"] + q["MoonRim"] * rim))
    a = np.where(rho < 1.0 + me, a, 0.0)
    return lerp(sky, np.array(q["MoonColor"], dtype=np.float64), a[..., None])


def niebla(dist, z_pix, z_cam, q=None):
    """Niebla por distancia + de altura exponencial integrada a lo largo del rayo (densidad
    1/FogDist + exp(-z/HFogFall)/HFogDist), sobre max(Dist - FogStart, 0)."""
    q = P if q is None else q
    z1 = np.maximum(z_pix, 0.0)
    z0 = np.maximum(z_cam, 0.0)
    Hf = max(q["HFogFall"], 1.0)
    dz = z1 - z0
    e0 = np.exp(-z0 / Hf)
    grande = np.abs(dz) > 1.0
    F = np.where(grande, Hf * (e0 - np.exp(-z1 / Hf)) / np.where(grande, dz, 1.0), e0)
    tau = np.maximum(dist - q["FogStart"], 0.0) * (1.0 / max(q["FogDist"], 1.0) + F / max(q["HFogDist"], 1.0))
    return q["FogMax"] * (1.0 - np.exp(-tau))


def suelo(x, y, gx, gy, h, hf, cam, q=None, partes=False):
    """ValleyPS, suelo (Part 0), sin dither. x, y, h: punto del suelo (cm); cam: ojos en local (cm)."""
    q = P if q is None else q
    L, _, _, _ = direcciones(q)
    x = np.asarray(x, dtype=np.float64)
    pos = np.stack([x, np.asarray(y, dtype=np.float64), np.asarray(h, dtype=np.float64)], -1)
    cv = np.asarray(cam, dtype=np.float64) - pos
    dist = np.sqrt((cv * cv).sum(-1))
    V = cv / np.maximum(dist, 1e-6)[..., None]
    dv = -V
    fog = niebla(dist, pos[..., 2], pos[..., 2] + V[..., 2] * dist, q)
    N = np.stack([-np.asarray(gx), -np.asarray(gy), np.ones_like(x)], -1)
    N = N / np.sqrt((N * N).sum(-1))[..., None]
    CL, CS, CH = (np.array(q[k], dtype=np.float64) for k in ("ColLit", "ColShadow", "ColSheen"))
    wrap = sat(((N * L).sum(-1) + q["Wrap"]) / (1.0 + q["Wrap"]))
    k = lerp(q["ShadeFloor"], 1.0, wrap) * sat(1.0 - q["SlopeDark"] * (1.0 - N[..., 2]))
    col = lerp(CS, CL, k[..., None])
    col = lerp(col, CL, (q["CrestLight"] * hf * hf)[..., None])
    xs = sat((N * V).sum(-1)) / max(q["SheenW"], 0.05)
    x2 = xs * xs
    fres = np.exp(-x2 * x2)
    fwd = sat(0.5 + 0.5 * (dv * L).sum(-1))
    col = lerp(col, CH, sat(q["Sheen"] * fres * lerp(q["SheenBack"], 1.0, fwd) * (1.0 - fog))[..., None])
    C = np.array(q["ShadowCenter"], dtype=np.float64)
    Hs = np.maximum(C[2] - pos[..., 2], 1.0)
    Rs = max(q["ShadowRadius"], 1.0)
    peak = q["ShadowStrength"] * Rs * Rs / (Rs * Rs + Hs * Hs)
    ws = np.maximum(q["ShadowSoft"] * Hs, 1.0)
    qs = 1.0 + ((x - C[0]) ** 2 + (pos[..., 1] - C[1]) ** 2) / (ws * ws)
    O = np.minimum(sat(peak / (np.sqrt(qs) * qs)), q["ShadowMax"])
    col = col * (1.0 - O[..., None] * (1.0 - np.array(q["ShadowTint"], dtype=np.float64)))
    sky = cielo(dv, q, con_luna=False)
    out = lerp(col, sky, fog[..., None])
    if partes:
        return out, dict(O=O, fog=fog, dist=dist, fres=fres)
    return out


# ---------------------------------------------------------------------------------------------
# Numeros derivados que la spec cita (cotas cerradas)
# ---------------------------------------------------------------------------------------------
def cota_vel_vertical_deg(q=None, r=None):
    """Cota superior de la velocidad angular VERTICAL del oleaje vista desde los ojos (grados/s), en funcion de r:
    |dh/dt| <= SwellAmp * S5 * (r/SwellFar) * SwellSpeed * sum_j w_j 2 pi / T_j / 2.95 ; angulo ~ dh / r.
    Desde SwellFar vale 0,1676 * SwellSpeed * SwellAmp / SwellFar rad/s (constante)."""
    q = P if q is None else q
    r = np.linspace(q["SwellNear"], q["FarBack"], 20000) if r is None else r
    k = sum(w * 2.0 * math.pi / T for (_, _, T, w, _) in OLAS) / SW
    SF = max(q["SwellFar"], q["SwellNear"] + 1.0)
    wq, _ = s5(q["SwellNear"], SF, r)
    wq = wq * r / SF
    FC = max(q["FarCrest"], q["FarIn"] + 1.0)
    tb, _ = s5(FC, max(q["FarBack"], FC + 1.0), r)
    v = q["SwellAmp"] * q["SwellSpeed"] * k * wq * (1.0 - tb) / r
    i = int(np.argmax(v))
    return math.degrees(v[i]), float(r[i])


def deriva_neta(q=None):
    q = P if q is None else q
    v = np.zeros(2)
    tot = 0.0
    for (ang, lam, per, w, _) in OLAS:
        c = lam * q["SwellScale"] * q["SwellSpeed"] / per
        a = math.radians(ang + q["SwellSeed"])
        v += w * c * np.array([math.cos(a), math.sin(a)])
        tot += w * c
    return float(np.linalg.norm(v) / tot)
