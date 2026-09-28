# -*- coding: utf-8 -*-
"""verify_amoeba.py - verificacion numerica de la ameba del nucleo V4 (2026-09-28). Correr desde esta carpeta (~4 min).

Corre sobre el PORT LITERAL del HLSL (amoeba_hlsl_port.py). Chequea:
  (0) control positivo del instrumento (esfera, gradiente de una funcion conocida)
  (a) gradiente tangencial analitico vs diferencias finitas (error relativo < 1e-3) + la normal
  (b) cotas EXACTAS [WMIN, 1] del campo normalizado: certificado (malla densa + Lipschitz) y
      muestreo al azar de (u, T); condicion del brazo (Rcm) y del BP (RMin)
  (c) longitud de onda minima: analitica (polinomio de grado 10) + FFT sobre circulos maximos
  (d) curvaturas principales (sin picos ni pliegues) vieja vs nueva
  (e) cuanto "menos esfera": r_max/r_min y desviacion RMS, vieja vs nueva
  (f) el port literal coincide con el prototipo independiente (clase PairDoG)
"""
import numpy as np
import sys, os
from scipy.optimize import minimize
from scipy.spatial import cKDTree
import amoeba_hlsl_port as H
from proto import fib_sphere, PairDoG
from curv import principal_curv

rng = np.random.default_rng(20260928)
OK = True


def check(cond, msg):
    global OK
    print(("  OK   " if cond else "  FALLA ") + msg)
    OK &= bool(cond)


def rand_unit(n):
    v = rng.normal(size=(n, 3))
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def rand_tangent(u):
    t = rng.normal(size=u.shape)
    t -= u * np.sum(u * t, 1, keepdims=True)
    return t / np.linalg.norm(t, axis=1, keepdims=True)


def states(n, NAmax=2.0):
    S = rng.uniform(0, 1, n); Ag = rng.uniform(0, 1, n); NA = rng.uniform(0, NAmax, n)
    ph = rng.uniform(0, 2 * np.pi, n)
    LV1 = np.stack([S, ph, Ag, np.zeros(n)], -1)
    LV3 = np.stack([np.ones(n), np.ones(n), NA, np.ones(n)], -1)
    Rc = 16.0 * (1 + 0.12 * rng.uniform(0, 1, n))
    T = rng.uniform(0, 8000, n)
    return LV1, LV3, Rc, T


# ------------------------------------------------------------------------------------------
print("(0) CONTROL POSITIVO del instrumento")
u = rand_unit(2000); t = rand_tangent(u); eps = 1e-5
F = np.array([0.3, -0.5, 0.8])
f = lambda v: np.sin(2.0 * (v @ F))
fd = (f((u + eps * t) / np.linalg.norm(u + eps * t, axis=1, keepdims=True)) - f((u - eps * t) / np.linalg.norm(u - eps * t, axis=1, keepdims=True))) / (2 * eps)
an = np.sum((2.0 * np.cos(2.0 * (u @ F)))[:, None] * F * t, 1)
check(np.max(np.abs(fd - an)) < 1e-8, "derivada direccional de sin(2 u.F): error max %.2e" % np.max(np.abs(fd - an)))
# control NEGATIVO: un gradiente deliberadamente mal (x1.01) tiene que FALLAR el umbral 1e-3
bad = 1.01 * an
rel = np.abs(fd - bad) / np.maximum(np.abs(bad), 1e-9)
check(np.median(rel) > 1e-3, "control negativo (gradiente x1,01) detectado: error relativo mediano %.2e > 1e-3" % np.median(rel))

# ------------------------------------------------------------------------------------------
print("\n(f) el PORT literal del HLSL == el prototipo independiente (PairDoG)")
proto = PairDoG(gam=[1, 1, 1, 1, 0, 0], D=[tuple(H.D0), tuple(H.D1), tuple(H.D2), tuple(H.D3), tuple(H.D4), tuple(H.D5)],
                m=[10, 10, 10, 10, 6, 6], H=[1.0, 0.9, 0.85, 0.8, 0.6, 0.6], pairs=[(0, 3), (1, 2), (4, 5)],
                om=list(H.OM), ph=list(H.PH), floor=0.1, axis=np.array([0, 0, 1.0]), orot=H.ROT, A0=H.A0, norm=H.WN, amax=H.AMAX)
n = 20000; u = rand_unit(n); LV1, LV3, Rc, T = states(n)
r1, g1 = H.CentreR(u, Rc, LV1, LV3, T)
# el prototipo usa (1 - calmK*Calm) con calmK = 0.5 y agK = 0.4, igual que el HLSL
A = proto.amp(LV1[:, 0], LV1[:, 2], LV3[:, 2])
up = proto.rot(u, proto.orot * T, -1.0); w, gp = proto.raw(up, proto.heights(T)); gw = proto.rot(gp, proto.orot * T, +1.0)
r2 = Rc * (1 + A * H.WN * w); g2 = (Rc * A * H.WN)[:, None] * gw; g2 -= u * np.sum(u * g2, 1, keepdims=True)
check(np.max(np.abs(r1 - r2)) < 1e-6 and np.max(np.abs(g1 - g2)) < 1e-6,
      "radio y gradiente coinciden: |dr| max %.2e cm, |dg| max %.2e" % (np.max(np.abs(r1 - r2)), np.max(np.abs(g1 - g2))))

# ------------------------------------------------------------------------------------------
print("\n(a) GRADIENTE tangencial analitico vs diferencias finitas (central, eps = 1e-5 rad)")
n = 200000; u = rand_unit(n); LV1, LV3, Rc, T = states(n)
r, gT = H.CentreR(u, Rc, LV1, LV3, T)
errs = []
for _ in range(2):
    t = rand_tangent(u)
    up_ = (u + eps * t); up_ /= np.linalg.norm(up_, axis=1, keepdims=True)
    um_ = (u - eps * t); um_ /= np.linalg.norm(um_, axis=1, keepdims=True)
    fd = (H.CentreR(up_, Rc, LV1, LV3, T)[0] - H.CentreR(um_, Rc, LV1, LV3, T)[0]) / (2 * eps)
    an = np.sum(gT * t, 1)
    errs.append(np.abs(fd - an))
err = np.maximum(errs[0], errs[1])
gn = np.linalg.norm(gT, axis=1)
sel = gn > 1e-3 * Rc * H.CoreWob(LV1, LV3)[:, 0] + 1e-9     # fuera de los extremos exactos (gradiente ~0)
rel = err[sel] / gn[sel]
check(rel.max() < 1e-3, "error relativo max %.2e (mediana %.2e) en %d puntos; error absoluto max %.2e cm/rad"
      % (rel.max(), np.median(rel), sel.sum(), err.max()))
check(np.all(np.abs(np.sum(gT * u, 1)) < 1e-9), "gT es tangente (|gT.u| max %.1e)" % np.abs(np.sum(gT * u, 1)).max())
# la normal n = normalize(u - gT/r) vs la de la superficie P = r u por diferencias finitas
t1 = rand_tangent(u); t2 = np.cross(u, t1)
def P(v):
    v = v / np.linalg.norm(v, axis=1, keepdims=True)
    return v * H.CentreR(v, Rc, LV1, LV3, T)[0][:, None]
e = 1e-5
d1 = (P(u + e * t1) - P(u - e * t1)) / (2 * e); d2 = (P(u + e * t2) - P(u - e * t2)) / (2 * e)
nfd = np.cross(d1, d2); nfd /= np.linalg.norm(nfd, axis=1, keepdims=True); nfd *= np.sign(np.sum(nfd * u, 1))[:, None]
nan_ = u - gT / r[:, None]; nan_ /= np.linalg.norm(nan_, axis=1, keepdims=True)
ang = np.degrees(np.arccos(np.clip(np.sum(nfd * nan_, 1), -1, 1)))
check(ang.max() < 0.01, "normal analitica vs normal de la superficie: angulo max %.2e grados" % ang.max())
check(np.all(np.isfinite(r)) and np.all(np.isfinite(gT)), "sin NaN/Inf en 200k estados al azar (NoiseAmount 0-2, T 0-8000 s)")

# ------------------------------------------------------------------------------------------
print("\n(b) COTAS del campo normalizado wn = (r/Rc - 1)/A")
from bounds_bnb import bnb
box = H.box
res = {}
for sgn, name in ((+1, "max"), (-1, "min")):
    best, cert, it, mc = bnb(sgn)
    res[name] = (best, cert)
WMAXr, WMAXc = res["max"]; WMINr, WMINc = res["min"]
print("  campo CRUDO (ramificacion y poda de 2o orden, cobertura + Taylor con cota del hessiano):")
print("    max alcanzado %.9f  certificado <= %.9f" % (WMAXr, WMAXc))
print("    min alcanzado %.9f  certificado >= %.9f" % (WMINr, WMINc))
check(H.WN * WMAXc <= 1.0, "maximo normalizado CERTIFICADO = WN*WMAX = %.7f <= 1 (alcanzado %.7f)" % (H.WN * WMAXc, H.WN * WMAXr))
check(H.WN * WMINc >= H.WMIN, "minimo normalizado CERTIFICADO = %.7f >= WMIN = %.4f (alcanzado %.7f)" % (H.WN * WMINc, H.WMIN, H.WN * WMINr))
print("  -> campo normalizado en [%.5f, %.5f]; constantes del HLSL: WN = %.4f, WMIN = %.4f"
      % (H.WN * WMINr, H.WN * WMAXr, H.WN, H.WMIN))
# muestreo al azar (u, T): tiene que quedar DENTRO y acercarse a los extremos (cotas ajustadas, no holgadas)
n = 3_000_000
u = rand_unit(n); T = rng.uniform(0, 20000, n)
w, _ = H.raw_field(u, T); wn = H.WN * w
check(wn.max() <= 1.0 and wn.min() >= H.WMIN, "3M (u,T) al azar: wn en [%.5f, %.5f]" % (wn.min(), wn.max()))
# la cota se ALCANZA en el tiempo: buscar el instante mas cercano al extremo (malla gruesa de u x 200k instantes)
Ts = np.linspace(0, 200000, 400001)
s0 = np.sin(H.OM[0] * Ts + H.PH[0]); s1 = np.sin(H.OM[1] * Ts + H.PH[1]); s2 = np.sin(H.OM[2] * Ts + H.PH[2])
print("  alcance en el tiempo: max de |sin| simultaneos en 200 000 s: "
      "min(|s0|,|s1|,|s2|) llega a %.4f (1 = los tres pares en su extremo a la vez)" % np.max(np.minimum(np.minimum(np.abs(s0), np.abs(s1)), np.abs(s2))))
# condicion del BRAZO: Rcm = Rc(1 + A*WMIN) + 0.3 gC debajo de la membrana minima Rc(1 + A*wn_min) + gC
n = 200000; LV1, LV3, Rc, T = states(n, NAmax=3.0)
Wob = H.CoreWob(LV1, LV3); A = Wob[:, 0]
S = LV1[:, 0]; gC = Rc * (0.12 + 0.06 * S) * np.maximum(1.0, 0.3) * 1.0
memb_min = Rc * (1 + A * H.WN * WMINc) + gC          # minimo CERTIFICADO, sin abultamientos (>= 0): peor caso
Rcm = Rc * (1 + A * Wob[:, 1]) + 0.3 * gC
check(np.all(memb_min - Rcm >= 0.7 * gC - 1e-9), "Rcm siempre >= 0,7 gC debajo de la membrana (holgura min %.3f cm)" % (memb_min - Rcm).min())
# y con el muestreo REAL (no la cota): membrana en 400 direcciones x cada estado
uu = fib_sphere(400)
worst = 1e9
for i in range(0, 4000):
    rr_, _ = H.CentreR(uu, np.full(400, Rc[i]), np.repeat(LV1[i:i + 1], 400, 0), np.repeat(LV3[i:i + 1], 400, 0), np.full(400, T[i]))
    worst = min(worst, (rr_ + gC[i]).min() - Rcm[i])
check(worst > 0, "muestreo real (4000 estados x 400 direcciones): membrana - Rcm >= %.3f cm" % worst)
# condicion del BP (RMin): excursion maxima hacia afuera <= _rc*0.75*NA*(1+0.4ag)*(1-0.5Coh)
Coh = H.Calm(LV1)
bp = Rc * 0.75 * LV3[:, 2] * (1 + 0.4 * LV1[:, 2]) * (1 - 0.5 * Coh)
exc = Rc * A * H.WN * WMAXc
check(np.all(exc <= bp + 1e-9), "excursion maxima <= la del BP (RMin) en 200k estados (sobra max %.4f cm)" % (bp - exc).max())

# ------------------------------------------------------------------------------------------
print("\n(c) LONGITUD DE ONDA minima")
print("  analitica: el campo es un POLINOMIO de grado 10 en u (2q^10 - q^5, q lineal en u; la rotacion es")
print("  lineal) -> banda limitada a armonicos esfericos l <= 10 -> lambda_min = 2 pi/sqrt(10*11) = %.1f grados"
      % np.degrees(2 * np.pi / np.sqrt(10 * 11)))
vert = 2.15
nC = 3000; M = 4096
th = np.linspace(0, 2 * np.pi, M, endpoint=False)
a = rand_unit(nC); b = rand_tangent(a)
Tc = rng.uniform(0, 5000, nC)
hi_energy = 0.0; k99s = []
for i in range(nC):
    v = np.cos(th)[:, None] * a[i] + np.sin(th)[:, None] * b[i]
    w, _ = H.raw_field(v, np.full(M, Tc[i]))
    Fw = np.abs(np.fft.rfft(w - w.mean())) ** 2
    tot = Fw.sum()
    hi_energy = max(hi_energy, Fw[11:].sum() / tot)
    cum = np.cumsum(Fw) / tot
    k99s.append(np.searchsorted(cum, 0.99))
k99s = np.array(k99s)
check(hi_energy < 1e-20, "FFT sobre %d circulos maximos: energia en armonicos > 10 = %.1e (cero de maquina)" % (nC, hi_energy))
print("  99%% de la energia hasta el armonico k = %d (peor circulo), mediana %d -> longitud de onda efectiva >= %.0f grados = %.0f separaciones de vertice (%.2f grados)"
      % (k99s.max(), np.median(k99s), 360.0 / k99s.max(), 360.0 / k99s.max() / vert, vert))
# ancho del pseudopodo: FWHM de 2q^10 - q^5
tt = np.linspace(0, np.pi, 200001); q = np.cos(tt / 2) ** 2; ph_ = 2 * q ** 10 - q ** 5
half = tt[np.argmax(ph_ < 0.5)]
ring = tt[np.argmin(ph_)]
print("  pseudopodo: ancho a media altura %.1f grados (%.0f separaciones), anillo del cuello a %.1f grados del eje (hondo %.3f)"
      % (2 * np.degrees(half), 2 * np.degrees(half) / vert, np.degrees(ring), ph_.min()))
check(360.0 / k99s.max() >= 18.0 and np.degrees(2 * np.pi / np.sqrt(10 * 11)) >= 18.0, "longitud de onda >= 18 grados (8 separaciones)")

# ------------------------------------------------------------------------------------------
print("\n(d) CURVATURAS principales (x Rc; esfera = 1). Peor estado: S = 0, Agitation = 1, NoiseAmount = 1 (y 1,5)")
def curv_stats(fn, NAv, nT=40, Ag=1.0):
    kmax, kmin = [], []
    uu = fib_sphere(60000)
    for T in np.linspace(0, 600, nT):
        n_ = uu.shape[0]
        LV1 = np.tile([0.0, 0.0, Ag, 0.0], (n_, 1)); LV3 = np.tile([1.0, 1.0, NAv, 1.0], (n_, 1))
        k1, k2, _ = principal_curv(lambda v: fn(v, np.full(n_, 16.0), LV1, LV3, np.full(n_, T)), uu)
        kmax.append(k1.max() * 16); kmin.append(k2.min() * 16)
    return max(kmax), min(kmin)
for NAv in (1.0, 1.5):
    kx_n, kn_n = curv_stats(H.CentreR, NAv)
    kx_o, kn_o = curv_stats(H.CentreR_old, NAv)
    print("  NoiseAmount %.1f  NUEVA: k_convexa max %.2f (radio min %.2f Rc) · k_concava min %.2f (radio min %.2f Rc)"
          % (NAv, kx_n, 1 / kx_n, kn_n, (1 / -kn_n) if kn_n < 0 else np.inf))
    print("                   VIEJA: k_convexa max %.2f (radio min %.2f Rc) · k_concava min %.2f"
          % (kx_o, 1 / kx_o, kn_o))
    if NAv == 1.0:
        # V4b (2026-09-28): umbrales RELAJADOS a proposito (Beltran pidio "una ameba, no una pelota"; A 0,75 con
        # tope 0,85). Antes 0,3 / 0,33 Rc. Criterio nuevo del valle: abarcar >= 2 ARISTAS de SM_LovingCentre_SC
        # (10242: arista 0,038 rad -> radio >= 0,076 Rc), asi la normal por vertice gira <= 30 grados por arista
        # en el valle. Medido con A 0,85: 0,0896 Rc = 1,43 cm (2,4 aristas). La membrana es un corrimiento RADIAL
        # (r + gC): no se pliega nunca.
        # puntas: radio >= 0,2 Rc = 5 aristas (3,2 cm con Rc 16): se leen redondeadas, no como espinas. Medido 0,25 Rc.
        check(1 / kx_n >= 0.2, "sin picos: el radio de curvatura convexo nunca baja de 0,2 Rc (%.2f Rc = %.1f cm con Rc 16)" % (1 / kx_n, 16 / kx_n))
        check(kn_n > -1.0 / 0.076, "sin pliegues: la concavidad mas cerrada tiene radio >= 0,076 Rc = 2 aristas (%.3f Rc)" % ((1 / -kn_n) if kn_n < 0 else np.inf))

# ------------------------------------------------------------------------------------------
print("\n(e) CUANTO MENOS ESFERA (S = 0, Agitation 0, NoiseAmount 1; 300 instantes)")
uu = fib_sphere(20000); n_ = uu.shape[0]
for lab, fn in (("VIEJA", H.CentreR_old), ("NUEVA", H.CentreR)):
    for S, Ag, name in ((0.0, 0.0, "S=0"), (0.0, 1.0, "S=0 Ag=1"), (1.0, 0.0, "S=1 calma")):
        ratio, rms, mx = [], [], []
        for T in np.linspace(0, 3000, 300):
            LV1 = np.tile([S, 0.0, Ag, 0.0], (n_, 1)); LV3 = np.tile([1.0, 1.0, 1.0, 1.0], (n_, 1))
            r, _ = fn(uu, np.full(n_, 16.0), LV1, LV3, np.full(n_, T))
            ratio.append(r.max() / r.min()); rms.append(np.sqrt(np.mean((r / 16.0 - r.mean() / 16.0) ** 2))); mx.append(r.max() / 16 - 1)
        print("  %s %-10s r_max/r_min mediana %.3f (min %.3f, max %.3f) · desviacion RMS %.1f %% · excursion max tipica %+.1f %%"
              % (lab, name, np.median(ratio), np.min(ratio), np.max(ratio), 100 * np.median(rms), 100 * np.median(mx)))


# ------------------------------------------------------------------------------------------
print("\n(g) ANCLAJE del ensanche del brazo (AP5.x) contra la membrana en el eje del brazo")
n = 200000; LV1, LV3, Rc, T = states(n, NAmax=1.0); LV3[:, 2] = 1.0
ax = rand_unit(n)
rA, _ = H.CentreR(ax, Rc, LV1, LV3, T)
stub_fixed = Rc - rA
print("  zCs FIJO (hoy): la ameba en el eje queda entre %.2f y %.2f cm respecto del ancla nominal (Rc)"
      % ((rA - Rc).min(), (rA - Rc).max()))
print("  -> un munon de radio rEnd (~2 cm) asoma hasta %.2f cm donde el eje cae en un hundimiento" % stub_fixed.max())
ro, _ = H.CentreR_old(ax, Rc, LV1, LV3, T)
print("  con la ameba VIEJA el munon maximo era %.2f cm" % (Rc - ro).max())
print("  zCs = CentreR(eje) + gC + 0,8 MH: 0,2 MH debajo de la membrana SOLO EN EL EJE; fuera del eje, con pendiente,")
print("  el borde del cilindro asomaba hasta ~1,1 cm. El ancla final se INCLINA con la membrana y baja rEnd^2/rAx:")
print("  se verifica en ../loving_outer/verify_flare.py (pared max <= 0,25 cm, con control negativo)")

print("\n(h) NoiseAmount = 0 -> esfera EXACTA")
n = 1000; u = rand_unit(n); LV1, LV3, Rc, T = states(n); LV3[:, 2] = 0.0
r, gT = H.CentreR(u, Rc, LV1, LV3, T)
check(np.max(np.abs(r - Rc)) == 0.0 and np.max(np.abs(gT)) == 0.0, "r = Rc y gT = 0 exactos")

print("\n%s" % ("TODO OK" if OK else "HAY FALLAS"))
sys.exit(0 if OK else 1)
