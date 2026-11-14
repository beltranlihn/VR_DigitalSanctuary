# -*- coding: utf-8 -*-
"""preview_breath_valley.py - previsualiza la COMPOSICION del valle de la respiracion (Entering)
en Blender headless, SIN Unreal. Especificacion: docs/PLAN-VALLE-ENTERING-2026-09-27.md.

QUE HACE
  1. Construye la malla real (reusa construir() de gen_breath_valley.py: misma topologia, mismos
     radios) y le aplica la FUNCION DE ALTURA de la especificacion (seccion 3) en numpy, en t = 0
     y en t = T1 (por defecto 41,5 s = medio periodo de la duna mas lenta, 83 s).
  2. Colorea cada vertice con el sombreado de ValleyPS (seccion 4, suelo) evaluado para la camara
     fija en los ojos del usuario, con la sombra falsa del metaball (seccion 5) y la niebla. El
     cielo es una esfera con el color de ValleyPS (seccion 6, cielo: degradado, resplandor y luna)
     por vertice. Es el material mate lavanda de la especificacion, no uno inventado.
  3. Pone una esfera blanca de 1,1 m de radio en el lugar del metaball (380, 0, 125 cm) con un
     sombreado envolvente simple (solo para ubicar la masa: NO es el metaball real).
  4. Renderiza con Workbench (luz FLAT + color de vertice, vista 'Standard' = sin tonemapper,
     como el APK: lo que se escribe es lo que se ve).
  5. Antes de renderizar CONTROLA el port contra los valores de la seccion 12 (altura, gradiente,
     color del suelo y del cielo) y mide la composicion: silueta minima sobre el horizonte en
     720 azimuts, margen del borde de la malla, piso bajo el usuario y el metaball, primer punto
     con h > 20 cm. Todo se imprime con el prefijo PREVIEW.

EJES. La especificacion usa los ejes de Unreal (X adelante, Y DERECHA, Z arriba; mano izquierda).
Blender es de mano derecha: mirando a +X con Z arriba, la derecha de la imagen es -Y. Para que la
imagen NO salga espejada, un punto UE (x, y, z) cm va a Blender como (x, -y, z)/100 m. Todas las
cuentas se hacen en coordenadas UE; la conversion es solo al escribir la escena.

SALIDAS (VR_Test/Saved/ClaudeScripts/):
  preview_valle_t0<tag>.png, preview_valle_t1<tag>.png  - 1280x720, vista del usuario al metaball, HFOV 90
  preview_valle_vuelta_t0<tag>.png                      - 1920x360, 4 vistas de 90 (atras, izq, frente, der)
  preview_valle_cenital_t0<tag>.png                     - 1024x1024, planta ortografica coloreada por altura

USO (headless, no toca la sesion de Blender del usuario):
  "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" --background --factory-startup --python preview_breath_valley.py
  Perillas: despues de "--", pares clave=valor que pisan los defaults de la seccion 7.1 (los
  vectores van como 0.4,0.5,0.8), mas estas opciones de escena:
    tag=<sufijo>   sufijo de los archivos            t1=<s>      segundo instante (41,5 por defecto)
    solo=principal sin vuelta ni cenital             mbR=<cm>    radio de la esfera de referencia (110)
    valleZ=<cm>    altura del ACTOR del valle (-50 = el piso baja 50 cm; ojos y metaball quedan
                   donde estan, asi que en local suben y ShadowCenter local sube con ellos)
  Ej.: ... --python preview_breath_valley.py -- valleZ=-50 ValleyA=750 ValleyB=450 ShadowStrength=2.4 tag=_propuesta
  Con perillas pisadas, los controles de la seccion 12 se saltean (valen solo con los defaults).

RESULTADO 2026-09-27 (defaults vs propuesta _propuesta de arriba), para la revision del plan:
  defaults : silueta min 4,79 deg en 10 min, borde oculto (margen 6,39), piso 0 bajo usuario y
             metaball; pero una esfera de 2,2 m centrada a 125 cm queda a 15 cm del piso: casi no
             se lee flotando, y las colinas (6-15 m) quedan bajas: se lee como llanura.
  propuesta: base de la esfera a 65 cm del piso, sombra separada de la masa (pico 0,46 con
             ShadowStrength 2,4), laderas a 4,5 m que enmarcan el metaball, silueta min 4,71 deg.
"""
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Vector

AQUI = os.path.dirname(os.path.abspath(__file__))
if AQUI not in sys.path:
    sys.path.insert(0, AQUI)
import gen_breath_valley as gen  # noqa: E402  (misma malla que el FBX)

SALIDA = os.path.abspath(os.path.join(AQUI, "..", "..", "..", "..", "VR_Test", "Saved", "ClaudeScripts"))

# ---------------------------------------------------------------------------------------------
# Parametros: defaults de la seccion 7.1 (la estetica verificada del plan).
# ---------------------------------------------------------------------------------------------
P = dict(
    ValleyX=350.0, ValleyA=950.0, ValleyB=600.0, SeatIn=60.0, SeatOut=250.0,
    RimHeight=380.0, RimCrest=3.0, RimBack=4.0, DuneAmp=520.0, DuneRise=1.6,
    DuneLow=-0.35, DuneHigh=1.2, DuneScale=1.0, DuneSeed=0.0, DuneShiftX=0.0, DuneShiftY=0.0,
    MorphAmt=0.45, MorphSpeed=1.0, MorphNear=800.0, MorphFar=3000.0,
    LightAz=20.0, LightEl=25.0, Wrap=0.3, ShadeFloor=0.0, SlopeDark=1.2,
    ColLit=(0.434, 0.527, 0.855), ColShadow=(0.061, 0.117, 0.352), ColSheen=(0.855, 0.761, 0.913),
    Sheen=0.4, SheenPow=4.0, SheenBack=0.35, CrestLight=0.2,
    ShadowSoft=0.8, ShadowTint=(0.305, 0.352, 0.68), ShadowMax=0.8,
    SkyZenith=(0.216, 0.328, 0.597), SkyHorizon=(0.597, 0.624, 0.839), SkyGlow=(0.831, 0.68, 0.855),
    SkyGradTop=0.7, GlowAz=20.0, GlowEl=2.0, GlowPow=2.0, GlowHeight=0.45, GlowAmt=0.8,
    MoonAz=-40.0, MoonEl=7.0, MoonRadius=9.0, MoonEdge=0.03, MoonColor=(0.73, 0.644, 0.839),
    MoonOpacity=0.55, MoonFill=0.2, MoonRim=1.0,
    FogStart=1000.0, FogDist=5000.0, FogMax=0.6,
    ShadowCenter=(380.0, 0.0, 125.0), ShadowRadius=85.0, ShadowStrength=1.5,
)
OJOS_DEF = np.array([0.0, 0.0, 120.0])      # cm, usuario sentado en el origen (camara de la seccion 12)
OJOS = OJOS_DEF.copy()                      # en coordenadas LOCALES del valle (cambia con valleZ)
METABALL = np.array([380.0, 0.0, 125.0])    # cm, centro del metaball (local)
METABALL_RADIO = 110.0                      # cm, esfera de referencia (~2,2 m de tamano)
T1_DEFECTO = 41.5                           # s, medio periodo de la duna mas lenta (83 s)

# Dunas: constantes del codigo (seccion 3.3), identicas en todas las implementaciones.
DUNAS = (  # (angulo deg, lambda cm, peso, fase rad, periodo s, fase temporal rad)
    (18.0, 3000.0, 1.00, 0.0, 53.0, 0.0),
    (101.0, 2200.0, 0.75, 1.7, 67.0, 2.1),
    (143.0, 1650.0, 0.55, 4.1, 41.0, 4.4),
    (232.0, 1250.0, 0.35, 2.9, 83.0, 1.3),
)


OPCIONES_ESCENA = ("tag", "t1", "solo", "valleZ", "mbR")


def leer_argumentos():
    """valleZ = altura del ACTOR del valle en cm (negativo = el piso baja; los ojos y el metaball
    no se mueven: en local suben). mbR = radio de la esfera de referencia en cm."""
    opts = {"tag": "", "t1": T1_DEFECTO, "solo": "", "valleZ": 0.0, "mbR": METABALL_RADIO}
    if "--" not in sys.argv:
        return opts
    for par in sys.argv[sys.argv.index("--") + 1:]:
        if "=" not in par:
            continue
        k, v = par.split("=", 1)
        if k in opts:
            opts[k] = v if k in ("tag", "solo") else float(v)
            print("PREVIEW opcion %s = %s" % (k, opts[k]))
        elif k in P:
            if isinstance(P[k], tuple):
                P[k] = tuple(float(c) for c in v.split(","))
            else:
                P[k] = float(v)
            print("PREVIEW perilla %s = %s" % (k, P[k]))
        else:
            print("PREVIEW (ignorado) %s" % par)
    return opts


# ---------------------------------------------------------------------------------------------
# Port numpy del HLSL de la seccion 7.2 (ValleyGradVS + ValleyPS). float64.
# ---------------------------------------------------------------------------------------------
def sat(x):
    return np.clip(x, 0.0, 1.0)


def smoothstep(a, b, x):
    t = sat((x - a) / (b - a))
    return t * t * (3.0 - 2.0 * t)


def dir_d(az, el):
    """D(az, el) de la seccion 1: azimut desde +X hacia +Y (derecha), elevacion sobre la horizontal."""
    a, e = math.radians(az), math.radians(el)
    return np.array([math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)])


def valley_grad(x, y, t):
    """ValleyGradVS: devuelve (dh/dx, dh/dy, h, hf). x, y en cm (arreglos), t en s."""
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    r = np.sqrt(x * x + y * y)
    rs = np.maximum(r, 1.0)
    VA = max(P["ValleyA"], 1.0)
    VB = max(P["ValleyB"], 1.0)
    ex = (x - P["ValleyX"]) / VA
    ey = y / VB
    e = np.sqrt(ex * ex + ey * ey)
    es = np.maximum(e, 1e-4)
    dex = ex / (VA * es)
    dey = ey / (VB * es)
    E1 = max(P["RimCrest"], 1.01)
    E2 = max(P["RimBack"], E1 + 0.01)
    t1 = sat((e - 1.0) / (E1 - 1.0))
    u1 = t1 * t1 * (3.0 - 2.0 * t1)
    du1 = 6.0 * t1 * (1.0 - t1) / (E1 - 1.0)
    t2 = sat((e - E1) / (E2 - E1))
    u2 = t2 * t2 * (3.0 - 2.0 * t2)
    du2 = 6.0 * t2 * (1.0 - t2) / (E2 - E1)
    B = P["RimHeight"] * u1 * (1.0 - u2)
    dB = P["RimHeight"] * (du1 * (1.0 - u2) - u1 * du2)
    MF = max(P["MorphFar"], P["MorphNear"] + 1.0)
    tg = sat((r - P["MorphNear"]) / (MF - P["MorphNear"]))
    Mt = P["MorphAmt"] * tg * tg * (3.0 - 2.0 * tg)
    dMt = P["MorphAmt"] * 6.0 * tg * (1.0 - tg) / (MF - P["MorphNear"])
    w = 2.0 * math.pi * P["MorphSpeed"] * t
    xd = x + P["DuneShiftX"]
    yd = y + P["DuneShiftY"]
    ks = 2.0 * math.pi / max(P["DuneScale"], 0.05)
    sig = 0.0
    sm = 0.0
    gsx = 0.0
    gsy = 0.0
    for (ang, lam, amp, fase, per, psi) in DUNAS:     # desenrollado en el HLSL
        a = math.radians(P["DuneSeed"] + ang)
        kx = ks / lam * math.cos(a)
        ky = ks / lam * math.sin(a)
        g = kx * xd + ky * yd + fase
        s, c = np.sin(g), np.cos(g)
        m = math.sin(w / per + psi)
        q = amp * (1.0 + Mt * m)
        sig = sig + q * s
        sm = sm + amp * m * s
        gsx = gsx + q * c * kx
        gsy = gsy + q * c * ky
    sig = sig / 2.65
    sm = sm / 2.65
    gsx = gsx / 2.65 + dMt * sm * x / rs
    gsy = gsy / 2.65 + dMt * sm * y / rs
    DL = P["DuneLow"]
    DH = max(P["DuneHigh"], DL + 0.01)
    tf = sat((sig - DL) / (DH - DL))
    f = tf * tf * (3.0 - 2.0 * tf)
    df = 6.0 * tf * (1.0 - tf) / (DH - DL)
    SI = P["SeatIn"]
    SO = max(P["SeatOut"], SI + 1.0)
    ts = sat((r - SI) / (SO - SI))
    seat = ts * ts * (3.0 - 2.0 * ts)
    dseat = 6.0 * ts * (1.0 - ts) / (SO - SI)
    ED = max(P["DuneRise"], 1.01)
    td = sat((e - 1.0) / (ED - 1.0))
    Ea = td * td * (3.0 - 2.0 * td)
    dEa = 6.0 * td * (1.0 - td) / (ED - 1.0)
    envE = Ea * (1.0 - u2)
    denvE = dEa * (1.0 - u2) - Ea * du2
    env = envE * seat
    h = B + P["DuneAmp"] * env * f
    gex = seat * denvE * dex + envE * dseat * x / rs
    gey = seat * denvE * dey + envE * dseat * y / rs
    gx = dB * dex + P["DuneAmp"] * (gex * f + env * df * gsx)
    gy = dB * dey + P["DuneAmp"] * (gey * f + env * df * gsy)
    return gx, gy, h, env * f


def direcciones():
    return (dir_d(P["LightAz"], P["LightEl"]), dir_d(P["GlowAz"], P["GlowEl"]),
            dir_d(P["MoonAz"], P["MoonEl"]), math.cos(math.radians(P["MoonRadius"])))


def lerp(a, b, t):
    return a + (b - a) * t


def cielo(dv, con_luna):
    """ValleyPS, la parte del cielo. dv (N,3) = direccion de la mirada (normalizada). Sin dither."""
    _, G, M, cosR = direcciones()
    Hz, Ze, Gl = (np.array(P[k]) for k in ("SkyHorizon", "SkyZenith", "SkyGlow"))
    sky = lerp(Hz, Ze, smoothstep(0.0, max(P["SkyGradTop"], 0.01), dv[:, 2])[:, None])
    hz = dv[:, :2] / np.maximum(np.linalg.norm(dv[:, :2], axis=1), 1e-4)[:, None]
    gh = G[:2] / max(np.linalg.norm(G[:2]), 1e-4)
    gaz = np.power(np.maximum(hz @ gh, 1e-6), max(P["GlowPow"], 0.1))
    gel = 1.0 - smoothstep(0.0, max(P["GlowHeight"], 0.001), np.abs(dv[:, 2] - G[2]))
    sky = lerp(sky, Gl, sat(P["GlowAmt"] * gaz * gel)[:, None])
    if not con_luna:
        return sky
    cosA = dv @ M
    rho = np.sqrt(np.maximum(1.0 - cosA, 0.0) / max(1.0 - cosR, 1e-6))
    me = max(P["MoonEdge"], 0.001)
    k = rho < 1.0 + me
    if np.any(k):
        d = dv[k]
        disc = 1.0 - smoothstep(1.0 - me, 1.0 + me, rho[k])
        o = d - M[None, :] * cosA[k][:, None]
        gm = G - M * np.dot(G, M)
        side = 0.5 + 0.5 * (o @ gm) / np.sqrt(np.maximum(np.sum(o * o, axis=1), 1e-10)) \
            / math.sqrt(max(np.dot(gm, gm), 1e-10))
        rim = smoothstep(0.6, 1.0, rho[k]) * side * side
        a = sat(P["MoonOpacity"] * disc * (P["MoonFill"] + P["MoonRim"] * rim))
        sky[k] = lerp(sky[k], np.array(P["MoonColor"]), a[:, None])
    return sky


def suelo(x, y, t, cam):
    """ValleyPS, la parte del suelo, evaluada en los puntos (x, y, h) vistos desde cam. Sin dither.
    Devuelve (color (N,3), h, O)."""
    L, _, _, _ = direcciones()
    gx, gy, h, hf = valley_grad(x, y, t)
    pos = np.stack([x, y, h], axis=1)
    camL = cam[None, :] - pos
    dist = np.linalg.norm(camL, axis=1)
    V = camL / np.maximum(dist, 1e-6)[:, None]
    dv = -V
    N = np.stack([-gx, -gy, np.ones_like(gx)], axis=1)
    N = N / np.linalg.norm(N, axis=1)[:, None]
    CL, CS, CH = (np.array(P[k]) for k in ("ColLit", "ColShadow", "ColSheen"))
    wrap = sat((N @ L + P["Wrap"]) / (1.0 + P["Wrap"]))
    k = lerp(P["ShadeFloor"], 1.0, wrap) * sat(1.0 - P["SlopeDark"] * (1.0 - N[:, 2]))
    col = lerp(CS, CL, k[:, None])
    col = lerp(col, CL, (P["CrestLight"] * hf * hf)[:, None])
    fres = np.power(np.maximum(1.0 - sat(np.sum(N * V, axis=1)), 1e-6), max(P["SheenPow"], 0.5))
    fwd = sat(0.5 + 0.5 * (dv @ L))
    col = lerp(col, CH, sat(P["Sheen"] * fres * lerp(P["SheenBack"], 1.0, fwd))[:, None])
    # sombra falsa del metaball (seccion 5)
    C = np.array(P["ShadowCenter"])
    Hs = np.maximum(C[2] - h, 1.0)
    Rs = max(P["ShadowRadius"], 1.0)
    peak = P["ShadowStrength"] * Rs * Rs / (Rs * Rs + Hs * Hs)
    ws = np.maximum(P["ShadowSoft"] * Hs, 1.0)
    qs = 1.0 + ((x - C[0]) ** 2 + (y - C[1]) ** 2) / (ws * ws)
    O = np.minimum(sat(peak / (np.sqrt(qs) * qs)), P["ShadowMax"])
    col = col * (1.0 - O[:, None] * (1.0 - np.array(P["ShadowTint"])))
    # niebla por distancia real hacia el cielo (sin luna) en esa direccion
    fog = P["FogMax"] * (1.0 - np.exp(-np.maximum(dist - P["FogStart"], 0.0) / max(P["FogDist"], 1.0)))
    col = lerp(col, cielo(dv, con_luna=False), fog[:, None])
    return col, h, O


# ---------------------------------------------------------------------------------------------
# Controles
# ---------------------------------------------------------------------------------------------
CONTROL_ALTURA = (  # seccion 12: (x, y, t, h, dh/dx, dh/dy, hf)
    (0, 0, 0, 0.000, 0.000000, 0.000000, 0.000000),
    (380, 0, 0, 0.000, 0.000000, 0.000000, 0.000000),
    (900, -700, 0, 89.005, 0.187877, -0.337869, 0.126090),
    (1500, 800, 0, 280.513, -0.146126, -0.204076, 0.281756),
    (2200, -1500, 20, 481.552, -0.912999, 0.638918, 0.250821),
    (3200, 0, 45.5, 460.192, -0.050322, 0.369692, 0.154215),
    (-1800, 1200, 90, 383.565, -0.033267, 0.083878, 0.007741),
    (2600, 2600, 300, 0.000, 0.000000, 0.000000, 0.000000),
)
CONTROL_SUELO = (  # (x, y, t, color lineal, O)
    (380, 0, 0, (0.2136, 0.2636, 0.5562), 0.4743),
    (250, -150, 0, (0.2869, 0.3542, 0.6358), 0.0432),
    (1500, 800, 0, (0.5424, 0.5454, 0.7814), 0.0),
    (3200, 0, 45.5, (0.5291, 0.5166, 0.7369), 0.0),
    (-1800, 1200, 90, (0.4117, 0.4519, 0.7056), 0.0),
)
CONTROL_CIELO = (  # (az, el, color lineal)
    (0, 0, (0.7595, 0.6629, 0.8501)),
    (0, 45, (0.2160, 0.3280, 0.5970)),
    (20, 3, (0.7821, 0.6676, 0.8510)),
    (180, 10, (0.5383, 0.5784, 0.8017)),
    (-40, 7, (0.6269, 0.6178, 0.8274)),
    (-33, 12, (0.6578, 0.6158, 0.8209)),
    (0, 90, (0.2160, 0.3280, 0.5970)),
)


def controles_seccion12(con_perillas):
    """Compara el port con la seccion 12. Solo tiene sentido con los defaults."""
    if con_perillas:
        print("PREVIEW controles seccion 12: SALTEADOS (hay perillas pisadas)")
        return True
    eh = eg = ec = eo = es = 0.0
    for (x, y, t, h0, gx0, gy0, hf0) in CONTROL_ALTURA:
        gx, gy, h, hf = valley_grad(np.array([x], float), np.array([y], float), t)
        eh = max(eh, abs(h[0] - h0))
        eg = max(eg, abs(gx[0] - gx0), abs(gy[0] - gy0), abs(hf[0] - hf0))
    for (x, y, t, c0, o0) in CONTROL_SUELO:
        c, _, O = suelo(np.array([x], float), np.array([y], float), t, OJOS_DEF)
        ec = max(ec, float(np.max(np.abs(c[0] - np.array(c0)))))
        eo = max(eo, abs(O[0] - o0))
    for (az, el, c0) in CONTROL_CIELO:
        c = cielo(dir_d(az, el)[None, :], con_luna=True)
        es = max(es, float(np.max(np.abs(c[0] - np.array(c0)))))
    ok = eh <= 0.01 and eg <= 2e-6 and ec <= 1e-3 and eo <= 1e-3 and es <= 1e-3
    print("PREVIEW controles seccion 12: %s  |dh|max=%.2e cm  |grad,hf|max=%.2e  |color suelo|max=%.2e"
          "  |O|max=%.2e  |color cielo|max=%.2e"
          % ("OK" if ok else "FALLA", eh, eg, ec, eo, es))
    return ok


def medir_composicion(t, etiqueta):
    """Silueta sobre el horizonte vista desde los ojos, en 720 azimuts, con el terreno continuo."""
    az = np.radians(np.arange(720) * 0.5)
    rr = np.linspace(40.0, gen.R_MAX * 100.0, 1400)
    X = np.cos(az)[:, None] * rr[None, :]
    Y = np.sin(az)[:, None] * rr[None, :]
    _, _, H, _ = valley_grad(X.ravel(), Y.ravel(), t)
    H = H.reshape(X.shape)
    elev = np.degrees(np.arctan2(H - OJOS[2], rr[None, :]))
    sil = elev.max(axis=1)                               # silueta por azimut
    borde = math.degrees(math.atan2(-OJOS[2], gen.R_MAX * 100.0))
    i_min = int(np.argmin(sil))
    # primer punto con h > 20 cm (distancia al usuario)
    alto = H > 20.0
    r_primero = np.where(alto.any(axis=1), rr[np.argmax(alto, axis=1)], np.inf)
    # piso bajo el usuario y el metaball (x 0..700, |y| <= 300) y en toda la elipse del valle
    gx_, gy_ = np.meshgrid(np.linspace(0, 700, 71), np.linspace(-300, 300, 61))
    _, _, Hz, _ = valley_grad(gx_.ravel(), gy_.ravel(), t)
    print("PREVIEW %s t=%.1f s  silueta min %.2f deg (az %+.1f)  mediana %.2f  max %.2f  |  "
          "borde de malla a %.2f deg -> margen %.2f deg  |  primer h>20cm a %.1f m (az %+.1f)  |  "
          "h max bajo usuario+metaball = %.4f cm  |  h max del terreno %.0f cm"
          % (etiqueta, t, sil[i_min], _az_ue(np.degrees(az[i_min])), float(np.median(sil)), float(sil.max()),
             borde, sil[i_min] - borde, r_primero.min() / 100.0,
             _az_ue(np.degrees(az[int(np.argmin(r_primero))])), float(np.abs(Hz).max()), float(H.max())))
    return sil


def _az_ue(a):
    return (a + 180.0) % 360.0 - 180.0


def barrido_temporal():
    """Silueta minima cada 10 s durante 10 min (el plan dice >= 4,8 deg)."""
    peor = (1e9, 0.0)
    az = np.radians(np.arange(720) * 0.5)
    rr = np.linspace(40.0, gen.R_MAX * 100.0, 700)
    X = (np.cos(az)[:, None] * rr[None, :]).ravel()
    Y = (np.sin(az)[:, None] * rr[None, :]).ravel()
    for t in np.arange(0.0, 600.1, 10.0):
        _, _, H, _ = valley_grad(X, Y, t)
        sil = np.degrees(np.arctan2(H.reshape(720, -1) - OJOS[2], rr[None, :])).max(axis=1)
        if sil.min() < peor[0]:
            peor = (float(sil.min()), float(t))
    print("PREVIEW barrido 0-600 s (cada 10 s): silueta minima %.2f deg en t=%.0f s" % peor)


# ---------------------------------------------------------------------------------------------
# Escena Blender
# ---------------------------------------------------------------------------------------------
def ue_a_blender(p):
    """cm UE (x, y derecha, z) -> m Blender (x, -y, z): la imagen sale sin espejar."""
    p = np.asarray(p, dtype=np.float64)
    return np.stack([p[..., 0], -p[..., 1], p[..., 2]], axis=-1) / 100.0


def blender_a_ue(p):
    p = np.asarray(p, dtype=np.float64) * 100.0
    return np.stack([p[..., 0], -p[..., 1], p[..., 2]], axis=-1)


def poner_color(me, nombre, rgb):
    """Atributo de color por vertice (lineal, FLOAT_COLOR) y lo deja activo para Workbench."""
    attr = me.color_attributes.get(nombre)
    if attr is None:
        attr = me.color_attributes.new(name=nombre, type='FLOAT_COLOR', domain='POINT')
    rgba = np.ones((len(me.vertices), 4), dtype=np.float32)
    rgba[:, :3] = np.clip(rgb, 0.0, 1.0)
    attr.data.foreach_set("color", rgba.ravel())
    activar_color(me, nombre)


def activar_color(me, nombre):
    ca = me.color_attributes
    for k in range(len(ca)):
        if ca[k].name == nombre:
            try:
                ca.active_color_index = k
            except Exception:  # noqa: BLE001
                pass
            try:
                ca.render_color_index = k
            except Exception:  # noqa: BLE001
                pass
    try:
        ca.active_color_name = nombre
    except Exception:  # noqa: BLE001
        pass


def material_color_vertice(nombre, attr):
    """Emision del color de vertice: si se cambia a Eevee, se ve igual que en Workbench FLAT."""
    mat = bpy.data.materials.new(nombre)
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    a = nt.nodes.new("ShaderNodeAttribute")
    a.attribute_name = attr
    em = nt.nodes.new("ShaderNodeEmission")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(a.outputs["Color"], em.inputs["Color"])
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return mat


def preparar_render():
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading
    sh.light = 'FLAT'
    sh.color_type = 'VERTEX'
    for prop, val in (("show_cavity", False), ("show_object_outline", False),
                      ("show_specular_highlight", False), ("show_shadows", False),
                      ("show_backface_culling", False), ("show_xray", False)):
        try:
            setattr(sh, prop, val)
        except Exception:  # noqa: BLE001
            pass
    try:
        sc.display.render_aa = '16'
    except Exception:  # noqa: BLE001
        pass
    sc.view_settings.view_transform = 'Standard'     # sin tonemapper, como el APK
    sc.view_settings.look = 'None'
    sc.view_settings.exposure = 0.0
    sc.view_settings.gamma = 1.0
    sc.display_settings.display_device = 'sRGB'
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGB'
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False


def camara_nueva():
    cd = bpy.data.cameras.new("CamUsuario")
    cd.lens_unit = 'FOV'
    cd.sensor_fit = 'HORIZONTAL'
    cd.clip_start = 0.05
    cd.clip_end = 1000.0
    cam = bpy.data.objects.new("CamUsuario", cd)
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    return cam


def apuntar(cam, origen_ue, objetivo_ue):
    o = Vector(ue_a_blender(origen_ue).tolist())
    d = Vector(ue_a_blender(objetivo_ue).tolist()) - o
    cam.location = o
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def render(ruta, w, h):
    sc = bpy.context.scene
    sc.render.resolution_x = w
    sc.render.resolution_y = h
    sc.render.filepath = ruta
    bpy.ops.render.render(write_still=True)
    print("PREVIEW render -> %s (%dx%d)" % (ruta, w, h))


def pegar_horizontal(rutas, destino):
    """Une PNGs del mismo alto en una tira (izquierda -> derecha)."""
    partes = []
    for r in rutas:
        im = bpy.data.images.load(r)
        w, h = im.size
        px = np.empty(w * h * 4, dtype=np.float32)
        im.pixels.foreach_get(px)
        partes.append(px.reshape(h, w, 4))
        bpy.data.images.remove(im)
    tira = np.concatenate(partes, axis=1)
    h, w = tira.shape[:2]
    out = bpy.data.images.new("tira", w, h, alpha=False)
    out.pixels.foreach_set(tira.ravel())
    out.filepath_raw = destino
    out.file_format = 'PNG'
    out.save()
    for r in rutas:
        try:
            os.remove(r)
        except OSError:
            pass
    print("PREVIEW render -> %s (%dx%d, de izquierda a derecha: atras, izquierda, frente, derecha)"
          % (destino, w, h))


def main():
    global OJOS, METABALL
    opts = leer_argumentos()
    con_perillas = any(("=" in a and a.split("=", 1)[0] in P)
                       for a in (sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []))
    tag = opts["tag"]
    t1 = float(opts["t1"])
    os.makedirs(SALIDA, exist_ok=True)

    # Controles de la seccion 12 ANTES de mover nada (usan la camara y la sombra por defecto).
    ok = controles_seccion12(con_perillas)

    # valleZ: el actor del valle baja; en SU espacio local los ojos y el metaball suben. La
    # sombra usa ShadowCenter local (el BP lo convierte con InverseTransformLocation).
    z0 = float(opts["valleZ"])
    OJOS = OJOS_DEF - np.array([0.0, 0.0, z0])
    METABALL = METABALL - np.array([0.0, 0.0, z0])
    if "ShadowCenter" not in " ".join(sys.argv):
        P["ShadowCenter"] = tuple(METABALL.tolist())
    mb_r = float(opts["mbR"])
    print("PREVIEW escena local: ojos z=%.0f cm  metaball z=%.0f cm (radio %.0f -> base a %.0f cm del piso)"
          % (OJOS[2], METABALL[2], mb_r, METABALL[2] - mb_r))

    for (t, et) in ((0.0, "t0"), (t1, "t1")):
        medir_composicion(t, et)
    barrido_temporal()
    if not ok:
        print("PREVIEW AVISO: el port no reproduce la seccion 12; las imagenes no son confiables")

    # --- escena ---
    gen.limpiar_escena()
    base, _, _ = gen.construir()
    base.hide_render = True                               # la malla plana queda como original
    valle = base.copy()
    valle.data = base.data.copy()
    valle.name = "Valle_preview"
    bpy.context.collection.objects.link(valle)
    valle.hide_render = False
    me = valle.data
    nv = len(me.vertices)
    co_b = np.empty(nv * 3, dtype=np.float64)
    base.data.vertices.foreach_get("co", co_b)
    co_b = co_b.reshape(nv, 3)
    ue = blender_a_ue(co_b)                               # (x, y) UE en cm de cada vertice
    valle.data.materials.append(material_color_vertice("M_ValleVertice", "Col"))

    # cielo: esfera centrada en los ojos, color de ValleyPS (Part 1) por vertice
    ojos_b = ue_a_blender(OJOS)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=720, ring_count=360, radius=150.0,
                                         location=tuple(ojos_b.tolist()))
    sky = bpy.context.active_object
    sky.name = "Cielo_preview"
    sme = sky.data
    ns = len(sme.vertices)
    sco = np.empty(ns * 3, dtype=np.float64)
    sme.vertices.foreach_get("co", sco)
    sdir_b = sco.reshape(ns, 3)                           # coordenadas locales = direccion * radio
    sdir = blender_a_ue(sdir_b)
    sdir = sdir / np.linalg.norm(sdir, axis=1)[:, None]
    poner_color(sme, "Col", cielo(sdir, con_luna=True))
    sme.materials.append(material_color_vertice("M_CieloVertice", "Col"))

    # metaball de referencia: esfera blanca con sombreado envolvente simple
    mb_b = ue_a_blender(METABALL)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=mb_r / 100.0,
                                         location=tuple(mb_b.tolist()))
    mb = bpy.context.active_object
    mb.name = "Metaball_referencia"
    mme = mb.data
    try:
        mme.shade_smooth()
    except AttributeError:
        pass
    nm = len(mme.vertices)
    mco = np.empty(nm * 3, dtype=np.float64)
    mme.vertices.foreach_get("co", mco)
    mn = blender_a_ue(mco.reshape(nm, 3))
    mn = mn / np.linalg.norm(mn, axis=1)[:, None]
    # Luz propia del sustituto, de arriba y del lado del usuario (como en la referencia): la luz
    # del suelo viene de atras del metaball y lo dejaria gris. NO es el sombreado del metaball real.
    Lm = np.array([-0.45, -0.25, 0.86])
    Lm = Lm / np.linalg.norm(Lm)
    wr = sat((mn @ Lm + 0.8) / 1.8)
    claro = np.array([0.92, 0.945, 1.0])                 # lado claro del metaball segun el plan
    indigo = np.array([0.45, 0.50, 0.80])
    poner_color(mme, "Col", lerp(indigo, claro, np.sqrt(wr)[:, None]))
    mme.materials.append(material_color_vertice("M_MetaballRef", "Col"))

    preparar_render()
    cam = camara_nueva()
    cam.data.angle = math.radians(90.0)

    def aplicar_tiempo(t):
        col, h, _ = suelo(ue[:, 0], ue[:, 1], t, OJOS)
        nuevo = co_b.copy()
        nuevo[:, 2] = h / 100.0
        me.vertices.foreach_set("co", nuevo.ravel())
        me.update()
        poner_color(me, "Col", col)
        return h

    h_prev = None
    for (t, et) in ((0.0, "t0"), (t1, "t1")):
        h = aplicar_tiempo(t)
        print("PREVIEW %s: h de los vertices 0..%.0f cm" % (et, h.max()))
        if h_prev is not None:
            dh = np.abs(h - h_prev)
            rv = np.hypot(ue[:, 0], ue[:, 1])
            i = int(np.argmax(dh))
            print("PREVIEW cambio t0 -> %s: max %.0f cm (a %.1f m del usuario); a menos de 8 m: max %.2f cm"
                  % (et, dh[i], rv[i] / 100.0, float(dh[rv < 800.0].max())))
        h_prev = h
        apuntar(cam, OJOS, METABALL)
        render(os.path.join(SALIDA, "preview_valle_%s%s.png" % (et, tag)), 1280, 720)
        if opts["solo"] == "principal":
            continue
        if et != "t0":
            continue
        # vuelta completa: 4 vistas de 90 deg a la altura de los ojos
        rutas = []
        for az in (180.0, -90.0, 0.0, 90.0):
            d = dir_d(az, 0.0)
            apuntar(cam, OJOS, OJOS + 1000.0 * d)
            r = os.path.join(SALIDA, "_vuelta_%d.png" % int(az))
            render(r, 480, 360)
            rutas.append(r)
        pegar_horizontal(rutas, os.path.join(SALIDA, "preview_valle_vuelta_t0%s.png" % tag))
        # planta: color por altura (azul oscuro = piso 0, blanco = 8 m)
        hn = np.clip(h / 800.0, 0.0, 1.0)[:, None]
        plano = np.where((h <= 1e-6)[:, None], np.array([[0.02, 0.05, 0.16]]),
                         lerp(np.array([0.10, 0.20, 0.45]), np.array([1.0, 1.0, 1.0]), hn))
        poner_color(me, "Alt", plano)
        sky.hide_render = True
        cam.data.type = 'ORTHO'
        cam.data.ortho_scale = 2.0 * gen.R_MAX + 2.0
        cam.location = (0.0, 0.0, 200.0)
        cam.rotation_euler = (0.0, 0.0, -math.pi / 2.0)   # adelante (+X) hacia arriba de la imagen
        render(os.path.join(SALIDA, "preview_valle_cenital_t0%s.png" % tag), 1024, 1024)
        cam.data.type = 'PERSP'
        cam.data.angle = math.radians(90.0)
        sky.hide_render = False
        activar_color(me, "Col")
    print("PREVIEW LISTO")


if __name__ == "__main__":
    main()
