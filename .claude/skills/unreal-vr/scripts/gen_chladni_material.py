# -*- coding: utf-8 -*-
"""gen_chladni_material.py - genera el material del salar de Chladni (M_ChladniFloor_SC) desde UNA fuente.

Escribe:
  - scripts/hlsl/ChladniHeightVS.hlsl  (VS -> Transform Local->World -> WPO): la altura (relieve + ola)
  - scripts/hlsl/ChladniPS.hlsl        (PS -> Emissive): piso (relieve por pixel, poligonos, grano, granito,
                                        luz rasante, agua, bruma) y cielo (Part 1)
  - VR_Test/Saved/ClaudeScripts/chladni_build.json  (lo leen apply_chladni_A.py / apply_chladni_B.py en Unreal)
  - imprime la tabla de parametros en markdown (docs/PLAN-SALAR-CHLADNI-2026-09-28.md, seccion 7.1)

Por que un generador: Adreno miscompila los arreglos con indice dinamico en el VS (gotcha 399) y un Custom no
puede declarar funciones, asi que los 8 modos, las 3 evaluaciones del campo (valor + gradiente) y los hash se
escriben DESPLEGADOS. Escribirlos a mano es donde entran los errores; aca salen de una sola plantilla.
Matematica = la del prototipo web v6 (docs/prototipos/placa-chladni.html): modos con centro calmo (los petalos
NACEN a un radio, como Bessel J_n), deformacion organica fija, relieve exp(-(F/ReliefW)^2) sobre las lineas
nodales, ola de formacion con la curva de Heart (la calcula el BP y llega en V0..V7).

Uso:  python gen_chladni_material.py
"""
import json
import math
import os

AQUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(AQUI, "..", "..", "..", ".."))
HLSL = os.path.join(AQUI, "hlsl")
SALIDA = os.path.join(REPO, "VR_Test", "Saved", "ClaudeScripts", "chladni_build.json")
MATERIAL = "/Game/SoulCharger/Mechanics/Sequencer/Chladni/M_ChladniFloor_SC"
TEXTURA = "/Game/SoulCharger/Mechanics/Sequencer/Chladni/T_SaltCells_SC.T_SaltCells_SC"
ARENA = "/Game/SoulCharger/Mechanics/Sequencer/Chladni/T_SandGrain_SC.T_SandGrain_SC"
# La sombra y el reflejo del gusano (grupo "5 - Gusano", WS0..WS7) quedaron PREPARADOS el 2026-09-29 y se encienden
# con Beltran mirando. Con False no entran ni los parametros ni el codigo.
CON_GUSANO = False

# El mandala "recto" (Geometric > 0: ondas triangulares, pentagonos y rayos). Beltran lo descarto el 2026-09-28 ("el
# recto NO"): con False el shader no lo lleva (ni el camino viejo de 3 evaluaciones), lo que baja la presion de
# registros del PS. La perilla Geometric queda sin efecto. True = vuelve el codigo de la 4a pasada (3 evaluaciones).
CON_GEO = False

# BANCO DE MEDICION (2026-09-29, Attracting a 36 fps en el recorrido). PerfMode lo escriben los eventos ChladniPerfN
# del actor ('ke * ChladniPerfN', solo Development); PerfForce 1 = las 8 figuras encendidas (peor caso fijo).
# Ronda 1 (medida): 0 viejo 25,5 ms -> analitico 18,0; mandala 11,2; acabado 4,9; cielo 0,6; WPO 0,6.
# Ronda 2: el modo 0 ES la obra optimizada; los demas restan una parte para ver cuanto queda en cada una.
PERF_MODOS = ["obra", "sin arena", "sin mandala PS", "sin WPO", "piso plano", "cielo plano", "sin acabado",
              "sin poligonos", "sin agua", "sin bruma"]

# los 8 modos (uno por slot del secuenciador): multiplicador de la simetria, de los anillos, giro de medio
# lobulo y radio donde nacen los petalos (fraccion del radio de la placa). Iguales al prototipo.
MA = [1, 2, 1, 3, 2, 1, 3, 2]
MK = [1.0, 1.5, 2.0, 1.25, 2.5, 3.0, 1.75, 2.25]
MP = [0.0, 0.5, 0.5, 0.0, 0.5, 0.0, 0.5, 0.0]
MR = [0.34, 0.46, 0.30, 0.55, 0.40, 0.28, 0.50, 0.38]


def s2l(h):
    h = h.lstrip("#")
    out = []
    for i in (0, 2, 4):
        v = int(h[i:i + 2], 16) / 255.0
        out.append(round(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4, 4))
    return out


# (grupo, nombre, tipo, default, rango, que hace)
PARAMS = [
    ("1 - Figura", "Sym", "s", 5, "2 … 12", "Simetria radial (ejes). Todos los modos la comparten: la suma siempre es un mandala. 5 rima con Surrounding"),
    ("1 - Figura", "Kr", "s", 3.5, "1 … 10", "Anillos de la placa; los modos de cada slot son multiplos"),
    ("1 - Figura", "BaseW", "s", 0.3, "0 … 1,5", "Peso de los anillos base"),
    ("1 - Figura", "PlateR", "s", 720, "200 … 2000", "Radio del mandala (cm). Afuera, solo el salar"),
    ("1 - Figura", "CenterX", "s", 0, "-300 … 400", "Centro del mandala hacia adelante (cm, local). 0 = debajo del usuario"),
    ("1 - Figura", "Calm", "s", 160, "0 … 500", "Radio del centro calmo (cm): adentro solo anillos, los petalos nacen afuera"),
    ("1 - Figura", "Warp", "s", 0.4, "0 … 2", "Irregularidad organica fija de la placa"),
    ("1 - Figura", "Geo", "s", 0.0, "0 … 1", "Que tan GEOMETRICAS son las figuras: 0 = ondas de placa redonda, 1 = lineas rectas en 5 direcciones (estrellas y pentagonos, como los poligonos del salar)"),
    ("1 - Figura", "Round", "s", 0.12, "0,02 … 0,9", "Esquinas de las lineas geometricas: chico = rectas con esquina viva (se ve pixelado), grande = curvas"),
    ("1 - Figura", "GeoFreq", "s", 1.8, "0,5 … 4", "Frecuencia de las lineas geometricas: mas alto = celdas mas chicas (1,8 = celdas de ~2,5 m, cerca de los poligonos del salar)"),
    ("1 - Figura", "Sharp", "s", 1.6, "1 … 4", "Filo de las crestas: 1 = loma triangular, mas = mas puntuda. Una cresta con filo parte la luz en dos (lado al sol / lado en sombra) y se lee como RELIEVE, no como pintura"),
    ("1 - Figura", "ReliefH", "s", 4, "0 … 15", "Relieve de las LINEAS del mandala (cm, por pixel): crestas finas de sal sobre las lineas nodales"),
    ("1 - Figura", "ReliefW", "s", 3, "0,5 … 15", "Medio ancho de cada cresta (cm). Se mide por DISTANCIA real a la linea nodal: todas las crestas tienen el mismo ancho (sin manchones donde la figura es plana)"),
    ("1 - Figura", "SwellH", "s", 0.5, "0 … 10", "Loma suave de GEOMETRIA bajo cada linea (cm). La linea fina va por pixel: con vertices saldria facetada"),
    ("1 - Figura", "SwellW", "s", 0.3, "0,1 … 0,8", "Ancho de la loma de geometria"),
    ("1 - Figura", "EdgeIn", "s", 0.5, "0,1 … 1", "Donde empieza a apagarse el mandala (fraccion del radio). Borde ancho e irregular: sin costura con los poligonos"),
    ("1 - Figura", "VibAmp", "s", 8, "0 … 30", "Altura de la ola al cambiar el patron (cm)"),
    ("2 - Salar", "SaltLit", "v", s2l("#fff4ea"), "", "Sal al sol"),
    ("2 - Salar", "SaltShade", "v", s2l("#b7b0d0"), "", "Sal en sombra"),
    ("2 - Salar", "FlatTone", "s", 0.7, "0 … 1", "Tono del piso plano entre sombra (0) y sol (1)"),
    ("2 - Salar", "LightGain", "s", 2.2, "0,3 … 4", "Contraste de la luz rasante sobre el relieve"),
    ("2 - Salar", "PolyH", "s", 0.55, "0 … 3", "Crestas de los poligonos del salar (0 = desierto liso)"),
    ("2 - Salar", "PolyKeep", "s", 0.0, "0 … 1", "Cuanto de los poligonos queda DENTRO del mandala (0 = los borra del todo)"),
    ("2 - Salar", "PolyW", "s", 5, "1 … 20", "Ancho de las crestas de los poligonos (cm)"),
    ("2 - Salar", "CellSize", "s", 150, "40 … 400", "Tamano de los poligonos (cm)"),
    ("2 - Salar", "SaltNoise", "s", 0.3, "0 … 1", "Manchas suaves de la costra"),
    ("2 - Salar", "Wet", "s", 0.45, "0 … 1", "Agua: refleja el cielo en angulo rasante"),
    ("3 - Grano", "Grain", "s", 0.6, "0 … 1.5", "Contraste de la arena (textura T_SandGrain_SC, con mipmaps: de lejos se funde sola)"),
    ("3 - Grano", "GrainSize", "s", 80, "20 … 200", "Tamano del parche de arena (cm): mas chico = grano mas grande"),
    ("3 - Grano", "Granite", "s", 0.6, "0 … 1.5", "Granos sueltos oscuros y claros de la arena"),
    ("4 - Cielo", "SkyTop", "v", s2l("#8ea3cb"), "", "Cielo arriba"),
    ("4 - Cielo", "SkyMid", "v", s2l("#cbb3cc"), "", "Cielo al medio"),
    ("4 - Cielo", "SkyHor", "v", s2l("#f2cbb2"), "", "Horizonte"),
    ("4 - Cielo", "SunCol", "v", s2l("#ffd6b0"), "", "Sol"),
    ("4 - Cielo", "SunAz", "s", -24, "-180 … 180", "Direccion del sol (grados; 0 = adelante, negativo = izquierda)"),
    ("4 - Cielo", "SunEl", "s", 2.5, "-6 … 30", "Altura del sol (grados)"),
    ("4 - Cielo", "SunSize", "s", 7, "1 … 20", "Tamano del sol (grados)"),
    ("4 - Cielo", "SunGlow", "s", 0.55, "0 … 2", "Halo del sol"),
    ("4 - Cielo", "Haze", "s", 0.55, "0 … 1", "Bruma del horizonte"),
    ("4 - Cielo", "FogDist", "s", 2600, "300 … 8000", "Distancia de la bruma (cm)"),
    ("4 - Cielo", "Dither", "s", 1.0, "0 … 3", "Dither contra el banding (en 1/255)"),
]
GUSANO = [
    ("5 - Gusano", "WormShadow", "s", 0.35, "0 … 1", "Sombra larga del gusano sobre la sal, hacia el lado contrario al sol"),
    ("5 - Gusano", "ShadowElev", "s", 22, "5 … 60", "Altura del sol PARA la sombra (grados): mas bajo = sombra mas larga. Aparte de SunEl porque con el sol real a 2,5 grados la sombra mediria 10 m"),
    ("5 - Gusano", "ShadowSoft", "s", 1.0, "0,3 … 3", "Borde de la sombra: mas = mas nitido"),
    ("5 - Gusano", "WormGlow", "s", 0.2, "0 … 1", "Reflejo del color del gusano en la sal humeda, justo debajo"),
    ("5 - Gusano", "WormR", "s", 14, "4 … 40", "Radio del gusano para la sombra y el reflejo (cm)"),
    ("5 - Gusano", "WormCol", "v", s2l("#f0c9d6"), "", "Color del reflejo bajo el gusano"),
]
PARAMS = PARAMS + (GUSANO if CON_GUSANO else []) + [
    ("9 - Interno", "PerfMode", "s", 0, "0 … 9", "Banco de medicion: " + " · ".join("%d %s" % (i, n) for i, n in enumerate(PERF_MODOS)) + " (lo escriben los eventos ChladniPerfN)"),
    ("9 - Interno", "PerfForce", "s", 0, "0 / 1", "Banco: 1 = las 8 figuras encendidas, peor caso fijo (lo escriben los eventos ChladniPerfN)"),
    ("9 - Interno", "Part", "s", 0, "0 / 1", "0 piso, 1 cielo (lo pone el Construction Script)"),
    ("9 - Interno", "Order", "s", 0, "0 … 1", "Cuanto mandala hay tallado (lo escribe el actor)"),
] + [("9 - Interno", "W%d" % i, "s", 0, "0 … 1", "Cuanto esta tallada la figura del slot %d (lo escribe el actor)" % i) for i in range(8)] \
  + ([("9 - Interno", "WS%d" % i, "v", [0.0, 0.0, -1.0], "", "Posicion del slot %d del gusano (cm, local del piso; z < 0 = no hay). La escribe el actor" % i) for i in range(8)] if CON_GUSANO else []) \
  + [("9 - Interno", "V%d" % i, "s", 0, "0 … 1", "Ola de formacion del slot %d, curva de Heart (lo escribe el actor)" % i) for i in range(8)]

FIG = ["Sym", "Kr", "BaseW", "PlateR", "CenterX", "Calm", "Warp", "ReliefH", "ReliefW", "SwellH", "SwellW", "EdgeIn", "Geo", "GeoFreq", "Round", "Sharp", "VibAmp", "Order"] + ["W%d" % i for i in range(8)] + ["V%d" % i for i in range(8)] + ["PerfMode", "PerfForce"]


def modo(n):
    """Condicion uniforme 'PerfMode == n' (float que llega de un parametro)."""
    return "abs(PerfMode - %d.0) < 0.5" % n


def forzar():
    """Banco: con PerfForce las 8 figuras quedan talladas y quietas (peor caso fijo, sin depender de la mesa)."""
    return ["[branch] if (PerfForce > 0.5) { Order = 1.0; " + " ".join("W%d = 1.0; V%d = 0.0;" % (i, i) for i in range(8)) + " }"]


def analitico():
    """UNA evaluacion del campo curvo (Geo 0) con su gradiente ANALITICO (verificado contra diferencias finitas en
    grad_check: error 1e-8; las diferencias finitas de 2 cm del camino viejo tenian 3 %). Define FAo, gFo, gVo.
    Cadena: p -> q0 = (p - C)/R -> q = q0 + warp(q0) (jacobiano J) -> (r, th) -> modos.
    Ronda 2: ANGULOS MULTIPLES. Los anillos de los 8 modos son multiplos de PI*Kr*r/4 (MK*4 = 4..12) y las simetrias
    multiplos de Sym*th (MA = 1..3): un sincos de cada uno y el resto por recurrencia (suma de angulos / Chebyshev).
    2 sincos por pixel en vez de 17; identico en fp32 (la recurrencia acumula ~1e-6)."""
    L = ["float2 q0 = (p - float2(CenterX, 0.0)) * iR;",
         "float kw = Warp * 0.045;",
         "float s1, c1, s2, c2, s3, c3, s4, c4;",
         "sincos(q0.y * 4.1 + 1.3, s1, c1);",
         "sincos(q0.x * 7.3 - q0.y * 2.2 + 0.4, s2, c2);",
         "sincos(q0.x * 3.7 + 2.1, s3, c3);",
         "sincos(q0.y * 6.9 + q0.x * 2.6 + 1.7, s4, c4);",
         "float2 q = q0 + kw * float2(s1 + 0.6 * s2, s3 + 0.6 * s4);",
         "float Jxx = 1.0 + kw * 4.38 * c2;                 // dq.x/dq0.x",
         "float Jxy = kw * (4.1 * c1 - 1.32 * c2);          // dq.x/dq0.y",
         "float Jyx = kw * (3.7 * c3 + 1.56 * c4);          // dq.y/dq0.x",
         "float Jyy = 1.0 + kw * 4.14 * c4;                 // dq.y/dq0.y",
         "float r = max(length(q), 1e-5);",
         "float th = atan2(q.y, q.x);",
         "float onw = max(calm * 0.8, 1e-5);",
         "float ont = saturate((r - calm * 0.6) / onw);",
         "float on = ont * ont * (3.0 - 2.0 * ont);",
         "float don = 6.0 * ont * (1.0 - ont) / onw;",
         "// anillos: rk_n = PI*Kr*r*n/4, n = 1..12, por suma de angulos",
         "float ru = PI * Kr * 0.25;",
         "float rs1, rc1;",
         "sincos(ru * r, rs1, rc1);"]
    ks = sorted(set([4] + [int(round(m * 4)) for m in MK]))
    for n in range(2, max(ks) + 1):
        L.append("float rc%d = rc%d * rc1 - rs%d * rs1; float rs%d = rs%d * rc1 + rc%d * rs1;" % (n, n - 1, n - 1, n, n - 1, n - 1))
    L += ["// simetrias: Sym*th*m, m = 1..3 (Chebyshev)",
          "float as1, ac1;",
          "sincos(Sym * th, as1, ac1);",
          "float ac2 = 2.0 * ac1 * ac1 - 1.0; float as2 = 2.0 * as1 * ac1;",
          "float ac3 = ac1 * (4.0 * ac1 * ac1 - 3.0); float as3 = as1 * (3.0 - 4.0 * as1 * as1);",
          "float Fa = BaseW * rc4;",
          "float dFr = -BaseW * ru * 4.0 * rs4;",
          "float dFt = 0.0;",
          "float Va = 0.0;",
          "float dVr = 0.0;",
          "float dVt = 0.0;"]
    for i in range(8):
        a, b = MR[i] * 0.55, MR[i] * 1.3
        n = int(round(MK[i] * 4))
        m = MA[i]
        # fase MP*PI: 0 -> (cos, sin) de m*x ; PI/2 -> cos(mx + PI/2) = -sin(mx), sin(mx + PI/2) = cos(mx)
        cB, sB = ("ac%d" % m, "as%d" % m) if MP[i] == 0.0 else ("(-as%d)" % m, "ac%d" % m)
        L.append(("[branch] if (W%d > 0.001 || V%d > 0.001) { float t = saturate((r - %.4f) * %.5f); float S = t * t * (3.0 - 2.0 * t); "
                  "float dS = 6.0 * t * (1.0 - t) * %.5f; float env = S * on; float denv = dS * on + S * don; "
                  "float cA = rc%d; float sA = rs%d; float cB = %s; float sB = %s; "
                  "float m = cA * cB * env; float mr = (-ru * %d.0 * sA * env + cA * denv) * cB; float mt = -Sym * %d.0 * cA * sB * env; "
                  "Fa += W%d * m; dFr += W%d * mr; dFt += W%d * mt; Va += V%d * m; dVr += V%d * mr; dVt += V%d * mt; }")
                 % (i, i, a, 1.0 / (b - a), 1.0 / (b - a), n, n, cB, sB, n, m, i, i, i, i, i, i))
    L += ["float iws = 1.0 / ws;",
          "Fa *= iws; dFr *= iws; dFt *= iws;",
          "float ft = saturate((r - 0.85) * 5.0);",
          "float fade = 1.0 - ft * ft * (3.0 - 2.0 * ft);",
          "dVr = dVr * fade - Va * 30.0 * ft * (1.0 - ft);                 // d(1 - smoothstep(0.85, 1.05, r))/dr = -6 t (1 - t) / 0.2",
          "dVt *= fade;",
          "float ir = 1.0 / r;",
          "float ir2 = ir * ir;",
          "float2 gqF = float2(dFr * q.x * ir - dFt * q.y * ir2, dFr * q.y * ir + dFt * q.x * ir2);",
          "float2 gqV = float2(dVr * q.x * ir - dVt * q.y * ir2, dVr * q.y * ir + dVt * q.x * ir2);",
          "FAo = Fa;",
          "gFo = float2(Jxx * gqF.x + Jyx * gqF.y, Jxy * gqF.x + Jyy * gqF.y) * iR;",
          "gVo = float2(Jxx * gqV.x + Jyx * gqV.y, Jxy * gqV.x + Jyy * gqV.y) * iR;"]
    return L


def evaluar(P, s):
    """Una evaluacion del campo en el punto P (expresion float2): define F<s> (figura tallada, normalizada) y Vb<s> (ola)."""
    L = []
    L.append("float2 q0%s = (%s - float2(CenterX, 0.0)) * iR;" % (s, P))
    L.append("float2 q%s = q0%s + Warp * 0.045 * float2(sin(q0%s.y * 4.1 + 1.3) + 0.6 * sin(q0%s.x * 7.3 - q0%s.y * 2.2 + 0.4), sin(q0%s.x * 3.7 + 2.1) + 0.6 * sin(q0%s.y * 6.9 + q0%s.x * 2.6 + 1.7));" % ((s,) * 8))
    L.append("float r%s = length(q%s);" % (s, s))
    L.append("float th%s = atan2(q%s.y, q%s.x);" % (s, s, s))
    L.append("float on%s = smoothstep(calm * 0.6, calm * 1.4, r%s);" % (s, s))
    # radio PENTAGONAL (curvas de nivel = pentagonos) mezclado con el circular segun Geo
    dirs = [(math.cos(2 * math.pi * k / 5 + math.pi / 2), math.sin(2 * math.pi * k / 5 + math.pi / 2)) for k in range(5)]
    L.append("float rq%s = max(max(max(q%s.x * %.5f + q%s.y * %.5f, q%s.x * %.5f + q%s.y * %.5f), max(q%s.x * %.5f + q%s.y * %.5f, q%s.x * %.5f + q%s.y * %.5f)), q%s.x * %.5f + q%s.y * %.5f) * 1.23607;"
             % ((s, s, dirs[0][0], s, dirs[0][1], s, dirs[1][0], s, dirs[1][1], s, dirs[2][0], s, dirs[2][1], s, dirs[3][0], s, dirs[3][1], s, dirs[4][0], s, dirs[4][1])))
    if not CON_GEO:
        L.pop()                                         # rq: solo lo usa el recto
        L.append("float F%s = BaseW * cos(PI * Kr * r%s);" % (s, s))
        L.append("float Vb%s = 0.0;" % s)
        for i in range(8):
            L.append("[branch] if (W%d > 0.001 || V%d > 0.001) { float m = cos(PI * Kr * %.4f * r%s) * cos(Sym * %.1f * th%s + %.4f) * smoothstep(%.4f, %.4f, r%s) * on%s; F%s += W%d * m; Vb%s += V%d * m; }"
                     % (i, i, MK[i], s, MA[i], s, MP[i] * 3.14159265, MR[i] * 0.55, MR[i] * 1.3, s, s, s, i, s, i))
        L.append("F%s /= ws;" % s)
        L.append("Vb%s *= 1.0 - smoothstep(0.85, 1.05, r%s);" % (s, s))
        return L
    L.append("float rg%s = lerp(r%s, rq%s, Geo);" % (s, s, s))
    L.append("float F%s = BaseW * lerp(cos(PI * Kr * rg%s), asin(rk * cos(PI * Kr * rg%s)) * irk, Geo);" % (s, s, s))
    L.append("float Vb%s = 0.0;" % s)
    for i in range(8):
        # geometrico: 5 ondas TRIANGULARES (lineales a tramos: sus lineas nodales son rectas con esquinas) y anillos pentagonales
        rot = MP[i] * math.pi / 5.0 + i * 0.37
        K = "Kr * GeoFreq * %.4f * 0.5" % MK[i]      # en vueltas: tri(x) = |4 frac(x) - 2| - 1 tiene periodo 1 (cos(2 pi x))
        planas = " + ".join("asin(rk * cos(6.28318 * (%s * (q%s.x * %.5f + q%s.y * %.5f) + %.4f)))" % (K, s, math.cos(rot + 2 * math.pi * k / 5), s, math.sin(rot + 2 * math.pi * k / 5), MP[i] * 0.5) for k in range(5))
        L.append("[branch] if (W%d > 0.001 || V%d > 0.001) { float mc = cos(PI * Kr * %.4f * rg%s) * cos(Sym * %.1f * th%s + %.4f); float mg = 0.0; [branch] if (Geo > 0.001) { mg = (%s) * 0.2 * irk; } float m = lerp(mc, mg, Geo) * smoothstep(%.4f, %.4f, r%s) * on%s; F%s += W%d * m; Vb%s += V%d * m; }"
                 % (i, i, MK[i], s, MA[i], s, MP[i] * 3.14159265, planas, MR[i] * 0.55, MR[i] * 1.3, s, s, s, i, s, i))
    L.append("F%s /= ws;" % s)
    L.append("Vb%s *= 1.0 - smoothstep(0.85, 1.05, r%s);" % (s, s))
    return L


def geo_eval(P, s, lwv):
    """Mandala RECTO en el punto P: union de lineas rectas. Cada nota agrega pentagonos concentricos (su espaciado y
    su giro) y rayos desde el centro (su simetria). Define G<s> = altura de cresta 0..1 (perfil triangular ^ Sharp),
    con ancho uniforme lwv (cm): la distancia a cada linea es EXACTA (son rectas)."""
    L = ["float2 qg%s = (%s - float2(CenterX, 0.0)) * iR;" % (s, P),
         "float rg%s_ = length(qg%s);" % (s, s),
         "float tg%s = atan2(qg%s.y, qg%s.x);" % (s, s, s),
         "float og%s = smoothstep(calm * 0.6, calm * 1.4, rg%s_);" % (s, s),
         "float G%s = 0.0;" % s]
    for i in range(8):
        rot = MP[i] * math.pi / 5.0                     # 0 o 36 grados: pentagonos alternados
        dd = [(math.cos(rot + 2 * math.pi * k / 5 + math.pi / 2), math.sin(rot + 2 * math.pi * k / 5 + math.pi / 2)) for k in range(5)]
        dots = ["qg%s.x * %.5f + qg%s.y * %.5f" % (s, c, s, sn) for c, sn in dd]
        T = "(Kr * GeoFreq * %.4f * 0.5)" % MK[i]
        L.append(("[branch] if (W%d > 0.001) { float rq = max(max(max(%s, %s), max(%s, %s)), %s) * 1.23607; "
                  "float u = rq * %s; float dr = abs(u - round(u)) / %s * R; "
                  "float nA = Sym * %.1f; float a = abs(frac((tg%s - %.5f) * nA * 0.159155 + 0.5) - 0.5) * 6.28318 / nA; "
                  "float ds = rg%s_ * R * sin(a); "
                  "float c = pow(saturate(1.0 - min(dr, ds) / %s), Sharp) * W%d * smoothstep(%.4f, %.4f, rg%s_) * og%s; "
                  "G%s = max(G%s, c); }")
                 % (i, dots[0], dots[1], dots[2], dots[3], dots[4], T, T, MA[i], s, rot, s, lwv, i, MR[i] * 0.55, MR[i] * 1.3, s, s, s, s))
    return L


def cabecera_comun():
    return ["const float PI = 3.14159265;",
            "float R = max(PlateR, 1.0);",
            "float iR = 1.0 / R;",
            "float calm = Calm * iR;",
            "float ws = max(BaseW + W0 + W1 + W2 + W3 + W4 + W5 + W6 + W7, 0.001);",
            "float act = Order + V0 + V1 + V2 + V3 + V4 + V5 + V6 + V7;",
            "float rk = 1.0 - clamp(Round, 0.02, 0.9);              // triangular redondeada: 1 - Round",
            "float irk = 1.0 / asin(rk);"][:(8 if CON_GEO else 6)]


def hash_bloque(nombre, expr):
    """hash12 de Dave Hoskins (sin seno: gotcha 481) desplegado: define la variable <nombre> en 0..1."""
    return ["float3 %s_p = frac(float3((%s).xyx) * 0.1031);" % (nombre, expr),
            "%s_p += dot(%s_p, %s_p.yzx + 33.33);" % (nombre, nombre, nombre),
            "float %s = frac((%s_p.x + %s_p.y) * %s_p.z);" % (nombre, nombre, nombre, nombre)]


def cielo(dirv, out, e=None):
    """Color del cielo en la direccion dirv (float3 normalizado, mundo, Z arriba) -> float3 out.
    e = literal: elevacion fija (la bruma mira al horizonte: e = 0 y el compilador pliega las smoothstep y el exp)."""
    return ["float %s_e = %s;" % (out, e if e is not None else dirv + ".z"),
            "float3 %s = lerp(SkyMid, SkyTop, smoothstep(0.03, 0.75, %s_e));" % (out, out),
            "%s = lerp(SkyHor, %s, smoothstep(-0.03, 0.26, %s_e));" % (out, out, out),
            "float %s_a = acos(clamp(dot(%s, SunDir), -1.0, 1.0));" % (out, dirv),
            "%s += SunCol * exp(-%s_a / (sunR * 2.2)) * SunGlow * 0.3;" % (out, out),
            "%s = lerp(%s, SunCol, (1.0 - smoothstep(sunR * 0.9, sunR, %s_a)) * 0.92);" % (out, out, out),
            "%s = lerp(%s, SkyHor, exp(-abs(%s_e) / 0.03) * Haze * 0.7);" % (out, out, out)]


def vs():
    if CON_GEO:
        raise SystemExit("CON_GEO: el camino recto (3 evaluaciones) esta en el historial de git, commit 1c36d03")
    ent = [("LP", "float3", "LocalPosition, pin XYZ", "posicion del vertice (cm, espacio del actor)"),
           ("Part", "float", "ScalarParameter Part", "0 piso, 1 cielo")]
    ent += [(n, "float", "ScalarParameter " + n, "") for n in FIG]
    L = ["if (Part > 0.5) { return float3(0.0, 0.0, 0.0); }",
         "[branch] if (%s) { return float3(0.0, 0.0, 0.0); }   // banco: sin WPO" % modo(3)]
    L += forzar()
    L += cabecera_comun()
    L += ["[branch] if (act < 0.001) { return float3(0.0, 0.0, 0.0); }",
          "float2 p = LP.xy;",
          "float2 dq = (p - float2(CenterX, 0.0)) * iR;",
          "float rp = length(dq);",
          "float thp = atan2(dq.y, dq.x);",
          "float rpJ = rp + 0.07 * (sin(3.0 * thp + 1.2) + 0.6 * sin(7.0 * thp + 0.4));   // borde irregular",
          "[branch] if (rp > 1.3) { return float3(0.0, 0.0, 0.0); }"]
    L += evaluar("p", "A")
    L += ["float ordL = Order * (1.0 - smoothstep(EdgeIn, 1.08, rpJ)) * smoothstep(calm * 0.8, calm * 1.6, rp);   // centro calmo: sin mandala bajo el usuario",
          "float x = FA / max(SwellW, 0.02);",
          "float h = SwellH * ordL * exp(-x * x) + VibAmp * VbA;   // solo la loma SUAVE: la cresta fina va por pixel",
          "return float3(0.0, 0.0, h);"]
    return ent, L


def ps():
    """Ronda 2 (2026-09-29): una evaluacion analitica con angulos multiples, y cada capa del acabado se salta donde
    su aporte es menor que 1/512 (sin cambio visible). Los modos del banco (PerfMode) restan una capa cada uno."""
    ent = [("LPi", "float3", "VertexInterpolator_1", "posicion local interpolada (sin el WPO)"),
           ("CamVec", "float3", "CameraVector", "del punto hacia la camara (mundo)"),
           ("Dist", "float", "Distance(AbsoluteWorldPosition, CameraPositionWS)", "distancia real a la camara (cm)"),
           ("SunDir", "float3", "preshader D(SunAz, SunEl)", "hacia el sol (mundo)"),
           ("SaltTex", "texture", "TextureObjectParameter SaltTex", "poligonos del salar horneados (gen_salt_cells.py)"),
           ("SandTex", "texture", "TextureObjectParameter SandTex", "arena horneada (gen_sand_texture.py)"),
           ("Part", "float", "ScalarParameter Part", "")]
    otros = [p[1] for p in PARAMS if p[1] not in FIG and p[1] not in ("Part", "SunAz", "SunEl")]
    for n in FIG + otros:
        tipo = next(p[2] for p in PARAMS if p[1] == n)
        ent.append((n, "float3" if tipo == "v" else "float", ("VectorParameter " if tipo == "v" else "ScalarParameter ") + n, ""))
    L = ["float sunR = max(SunSize, 0.5) * 0.0174533;",
         "float3 Vw = -normalize(CamVec);                     // de la camara hacia el punto",
         "[branch] if (Part > 0.5) {",
         "  [branch] if (%s) { return SkyMid; }   // banco: cielo plano" % modo(5)]
    L += ["  " + l for l in cielo("Vw", "skyC")]
    L += ["  return skyC;", "}",
          "[branch] if (%s) { return lerp(SaltShade, SaltLit, FlatTone); }   // banco: piso plano" % modo(4)]
    L += forzar()
    L += cabecera_comun()
    L += ["float2 p = LPi.xy;",
          "float fp = length(fwidth(p));                        // cm por pixel (fuera de ramas)",
          "float2 slope = float2(0.0, 0.0);",
          "float crest = 0.0;",
          "float2 dq = (p - float2(CenterX, 0.0)) * iR;",
          "float rp = length(dq);",
          "float thp = atan2(dq.y, dq.x);",
          "float rpJ = rp + 0.07 * (sin(3.0 * thp + 1.2) + 0.6 * sin(7.0 * thp + 0.4));   // borde irregular",
          "float ordP = Order * (1.0 - smoothstep(EdgeIn, 1.08, rpJ));                 // donde hay mandala (centro calmo incluido): sin poligonos",
          "float ordL = ordP * smoothstep(calm * 0.8, calm * 1.6, rp);",
          "float vsum = V0 + V1 + V2 + V3 + V4 + V5 + V6 + V7;",
          "// relieve del mandala + ola: la MISMA altura que ChladniHeightVS, con su pendiente ANALITICA. Donde no hay",
          "// relieve (ordL 0: centro calmo y fuera del borde) y no hay ola, no aporta nada: no se evalua",
          "[branch] if (act > 0.001 && rp < 1.3 && (ordL > 0.0001 || vsum > 0.001) && !(%s)) {" % modo(2),
          "  float FAo = 0.0;",
          "  float2 gFo = float2(0.0, 0.0);",
          "  float2 gVo = float2(0.0, 0.0);"]
    L += ["  " + l for l in analitico()]
    L += ["  float FA = FAo;",
          "  float2 gF = gFo;",
          "  float2 gV = gVo;",
          "  float gl = max(length(gF), 1e-5);",
          "  float dcm = FA / gl;                                             // DISTANCIA a la linea nodal (cm): mismo ancho en todas",
          "  float lw = max(ReliefW, 0.3);",
          "  float x = dcm / lw;",
          "  float hs = max(saturate(1.0 - abs(x)), 1e-4);                   // perfil triangular: filo en la cresta",
          "  float hn = pow(hs, Sharp);",
          "  float dhdd = (abs(x) < 1.0) ? (-Sharp * pow(hs, Sharp - 1.0) * sign(dcm) / lw) : 0.0;",
          "  float thin = 1.0 - smoothstep(0.6, 2.5, fp / lw);                 // mas fina que un pixel: se apaga (sin parpadeo)",
          "  float sw = max(SwellW, 0.02);",
          "  float xs = FA / sw;",
          "  slope += ReliefH * ordL * thin * dhdd * (gF / gl) + SwellH * ordL * exp(-xs * xs) * (-2.0 * FA / (sw * sw)) * gF + VibAmp * gV;",
          "  crest += hn * ordL * thin;",
          "}",
          "[branch] if (%s) { float3 n6 = normalize(float3(-slope, 1.0)); return lerp(SaltShade, SaltLit, saturate(FlatTone + (dot(n6, SunDir) - SunDir.z) * LightGain)); }   // banco: sin acabado" % modo(6),
          "// poligonos del salar (textura periodica de 8 x 8 celdas): el mandala los va borrando y de lejos se apagan.",
          "// Donde su aporte es < 1/500 (dentro del mandala, a lo lejos) no se leen las 3 texturas",
          "float pw = max(PolyW, 0.5);",
          "float keep = (1.0 - ordP * (1.0 - PolyKeep)) * (1.0 - smoothstep(0.5, 2.5, fp / pw));",
          "[branch] if (keep * PolyH > 0.002 && !(%s)) {" % modo(7),
          "  float T8 = max(CellSize, 1.0) * 8.0;",
          "  float2 uvC = p / T8;",
          "  float tx = 1.0 / 1024.0;",
          "  float c0 = Texture2DSampleLevel(SaltTex, SaltTexSampler, uvC, 0.0).r;",
          "  float cx = Texture2DSampleLevel(SaltTex, SaltTexSampler, uvC + float2(tx, 0.0), 0.0).r;",
          "  float cy = Texture2DSampleLevel(SaltTex, SaltTexSampler, uvC + float2(0.0, tx), 0.0).r;",
          "  float dv = c0 * 0.5 * CellSize;",
          "  float2 gdv = float2(cx - c0, cy - c0) * (0.5 * CellSize) / (tx * T8);",
          "  float xv = dv / pw;",
          "  float hsv = max(saturate(1.0 - xv), 1e-4);                           // la cresta del poligono, tambien con filo",
          "  float hv = pow(hsv, Sharp) * keep;",
          "  float dhdv = (xv < 1.0) ? (-Sharp * pow(hsv, Sharp - 1.0) / pw) : 0.0;",
          "  slope += 3.5 * PolyH * keep * dhdv * gdv;",
          "  crest += hv * PolyH;",
          "}",
          "float3 n = normalize(float3(-slope, 1.0));",
          "// luz rasante: el plano queda en FlatTone; lo que mira al sol se entibia y lo demas se enfria",
          "float t = FlatTone + (dot(n, SunDir) - SunDir.z) * LightGain;",
          "float3 sA = float3(0.5, 0.0, 0.0);",
          "float3 sB = float3(0.5, 0.0, 0.0);",
          "[branch] if (!(%s)) {" % modo(1)]
    # manchas de la costra: ruido de valor de una octava (4 hash) a 38 cm; de lejos (fp > 12 cm) su peso es 0
    man = ["float2 nq = p / 38.0;", "float2 ni = floor(nq);", "float2 nf = frac(nq);", "nf = nf * nf * (3.0 - 2.0 * nf);"]
    man += hash_bloque("n00", "ni") + hash_bloque("n10", "ni + float2(1.0, 0.0)") + hash_bloque("n01", "ni + float2(0.0, 1.0)") + hash_bloque("n11", "ni + float2(1.0, 1.0)")
    man += ["t += (lerp(lerp(n00, n10, nf.x), lerp(n01, n11, nf.x), nf.y) - 0.5) * SaltNoise * (1.0 - smoothstep(3.0, 12.0, fp)) * 0.25;"]
    L += ["  [branch] if (fp < 12.0) {"] + ["    " + l for l in man] + ["  }"]
    L += ["  // arena: textura periodica con mipmaps (de lejos se promedia sola), dos lecturas a escalas y giros distintos",
          "  float st = max(GrainSize, 1.0);",
          "  sA = Texture2DSample(SandTex, SandTexSampler, p / st).rgb;",
          "  float2 pr = float2(p.x * 0.8 - p.y * 0.6, p.x * 0.6 + p.y * 0.8);",
          "  sB = Texture2DSample(SandTex, SandTexSampler, pr / (st * 2.37)).rgb;",
          "  t += ((sA.r - 0.5) * 0.65 + (sB.r - 0.5) * 0.35) * Grain * 1.8;",
          "}",
          "float3 col = lerp(SaltShade, SaltLit, saturate(t));"]
    if CON_GUSANO:
        L += ["// el gusano ASENTADO: sombra larga hacia el lado contrario al sol + reflejo de su color en la sal humeda",
              "float2 sdir = normalize(SunDir.xy + float2(1e-5, 0.0));",
              "float kS = 1.0 / tan(clamp(ShadowElev, 3.0, 80.0) * 0.0174533);",
              "float wr = max(WormR, 1.0);",
              "float shw = 0.0;",
              "float glw = 0.0;"]
        for i in range(8):
            L.append("[branch] if (WS%d.z > 0.0) { float hl = WS%d.z * kS * 0.5; float2 dd = p - (WS%d.xy - sdir * hl); float al = dot(dd, sdir); float ac = dd.x * sdir.y - dd.y * sdir.x; "
                     "float e = al * al / ((hl + wr) * (hl + wr)) + ac * ac / (wr * wr * 1.4); shw = max(shw, exp(-e * 2.0 * ShadowSoft) * saturate(1.0 - WS%d.z / 400.0)); "
                     "float2 dg = p - WS%d.xy; glw = max(glw, exp(-dot(dg, dg) / (wr * wr * 5.0))); }" % (i, i, i, i, i))
        L += ["col = lerp(col, SaltShade * 0.8, saturate(WormShadow * shw));",
              "col += WormCol * WormGlow * glw;"]
    L += ["col += SunCol * max(t - 0.85, 0.0) * 0.5;",
          "float dk = max(sA.g, sB.g * 0.7);",
          "float lt = sA.b;",
          "col = lerp(col, SaltShade * 0.6, dk * Granite * 0.8);",
          "col = lerp(col, SaltLit * 1.06, lt * Granite * 0.45);",
          "// agua: refleja el cielo en angulo rasante. Donde el Fresnel es < 1/500 (mirando hacia abajo) no se calcula",
          "float cosv = saturate(-Vw.z);",
          "float fres = pow(1.0 - cosv, 5.0) * Wet * (1.0 - min(crest, 1.0) * 0.8);",
          "[branch] if (fres > 0.002 && !(%s)) {" % modo(8),
          "  float3 Rw = reflect(Vw, normalize(lerp(float3(0.0, 0.0, 1.0), n, 0.35)));"]
    L += ["  " + l for l in cielo("Rw", "refC")]
    L += ["  col = lerp(col, refC, saturate(fres));",
          "}",
          "// bruma hacia el cielo del horizonte (distancia REAL: en VR la profundidad de pixel 'nada' al girar).",
          "// Mira al horizonte: elevacion 0 fija, el gradiente del cielo se pliega a constantes; queda el halo del sol",
          "[branch] if (!(%s)) {" % modo(9),
          "  float3 Hd = normalize(float3(Vw.xy, 0.0001));"]
    L += ["  " + l for l in cielo("Hd", "fogC", e="0.0")]
    L += ["  col = lerp(col, fogC, (1.0 - exp(-Dist / max(FogDist, 1.0))) * 0.85);",
          "}"]
    L += hash_bloque("dz", "floor(Parameters.SvPosition.xy)")
    L += ["col += (dz - 0.5) * Dither / 255.0;",
          "return col;"]
    return ent, L


def escribir(nombre, salida, ent, lineas, titulo):
    cab = ["// %s - M_ChladniFloor_SC. %s" % (nombre, titulo),
           "// GENERADO por scripts/gen_chladni_material.py: NO editar a mano (se pisa). Plan: docs/PLAN-SALAR-CHLADNI-2026-09-28.md",
           "// Modos DESPLEGADOS, sin arreglos ni bucles (gotcha 399); hash sin seno (gotcha 481). Cuerpo de un Custom: termina en return.",
           "// NODO  MaterialExpressionCustom  Description \"%s\"  OutputType %s" % (nombre, salida),
           "// ENTRADAS (%d, en este orden):" % len(ent)]
    for i, (n, t, src, d) in enumerate(ent, 1):
        cab.append("//  %2d  %-10s %-7s %s%s" % (i, n, t, src, ("  " + d) if d else ""))
    cab.append("// --------------------------------------------------------------------------------------------------------")
    txt = "\n".join(cab + lineas) + "\n"
    with open(os.path.join(HLSL, nombre + ".hlsl"), "w", encoding="utf-8") as f:
        f.write(txt)
    return txt


def fuente(src):
    if src.startswith("ScalarParameter ") or src.startswith("VectorParameter "):
        return {"kind": "param", "param": src.split()[1], "vector": src.startswith("Vector")}
    if src.startswith("LocalPosition"):
        return {"kind": "localpos"}
    if src.startswith("VertexInterpolator_"):
        return {"kind": "vi", "index": int(src[-1])}
    if src.startswith("CameraVector"):
        return {"kind": "camvec"}
    if src.startswith("Distance("):
        return {"kind": "dist"}
    if src.startswith("preshader D("):
        return {"kind": "dir", "az": "SunAz", "el": "SunEl"}
    if src.startswith("TextureObjectParameter"):
        return {"kind": "texobj", "param": src.split()[1]}
    raise SystemExit("fuente desconocida: " + src)


def main():
    ev, lv = vs()
    ep, lp = ps()
    cv = escribir("ChladniHeightVS", "CMOT_Float3", ev, lv, "VERTEX SHADER -> Transform (Local->World, vector) -> WPO. Salida (0, 0, h) en cm")
    cp = escribir("ChladniPS", "CMOT_Float3", ep, lp, "PIXEL SHADER -> Emissive Color (lineal; MobileHDR off: sin tonemapper)")
    params = []
    for g, n, t, d, rango, que in PARAMS:
        params.append({"name": n, "kind": "vector" if t == "v" else "scalar", "default": d, "group": g})
    params.append({"name": "SaltTex", "kind": "texture", "default": TEXTURA, "group": "2 - Salar", "sampler": "SAMPLERTYPE_LinearGrayscale"})
    params.append({"name": "SandTex", "kind": "texture", "default": ARENA, "group": "3 - Grano", "sampler": "SAMPLERTYPE_Masks"})
    # el codigo va en archivos APARTE: AssetTools.read_file no lee mas de 80 KB y el PS ya pasa ese tamano junto con el plan
    carpeta = os.path.dirname(SALIDA)
    for nombre, codigo in (("ChladniHeightVS", cv), ("ChladniPS", cp)):
        with open(os.path.join(carpeta, "chladni_code_%s.txt" % nombre), "w", encoding="utf-8") as f:
            f.write(codigo)
    customs = [{"desc": "ChladniHeightVS", "outputType": "CMOT_Float3", "code_file": "chladni_code_ChladniHeightVS.txt", "inputs": [{"name": n, "type": t, "src": fuente(s)} for n, t, s, _ in ev]},
               {"desc": "ChladniPS", "outputType": "CMOT_Float3", "code_file": "chladni_code_ChladniPS.txt", "inputs": [{"name": n, "type": t, "src": fuente(s)} for n, t, s, _ in ep]}]
    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    with open(SALIDA, "w", encoding="utf-8") as f:
        json.dump({"material": MATERIAL, "params": params, "customs": customs}, f, ensure_ascii=True, indent=1)
    print("ChladniHeightVS: %d entradas, %d lineas | ChladniPS: %d entradas, %d lineas | %d parametros" % (len(ev), len(lv), len(ep), len(lp), len(params)))
    print("escrito " + SALIDA)
    print()
    print("| Grupo | Parámetro | Tipo | Default | Rango sugerido | Qué hace |")
    print("|---|---|---|---|---|---|")
    for g, n, t, d, rango, que in PARAMS:
        dd = "(%s)" % ", ".join(str(x) for x in d) if t == "v" else str(d)
        print("| `%s` | `%s` | %s | %s | %s | %s |" % (g, n, "vector" if t == "v" else "escalar", dd, rango, que))


if __name__ == "__main__":
    main()
