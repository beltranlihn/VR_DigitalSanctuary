# clock_precision.py - error del reloj fp32 (View.GameTime es float en el uniform: SceneView.cpp:2891, SceneView.h:974)
# en las fases del oleaje y de la respiracion, EMULANDO la cuenta del shader en float32 contra la exacta en float64.
# Se mira: (1) error absoluto de fase, (2) irregularidad cuadro a cuadro (paso de tiempo cuantizado = "trabado"),
# (3) su efecto en la silueta a 470 m, en grados y px. Compara con la cuenta SIN frac de la v1 (sin(2 pi t / T)).
import numpy as np, json
from pathlib import Path

OUT = Path(__file__).resolve().parent
f32 = np.float32
TS = {"15 min": 900.0, "2 h": 7200.0, "18,2 h (2^16 s)": 65536.0, "3 dias": 259200.0, "1 semana": 604800.0}
PER = (42.0, 36.0, 31.0, 46.0)          # oleaje
WJ = (1.00, 0.85, 0.70, 0.40)
LAMB = (9000.0, 7000.0, 5500.0, 4000.0)
A470 = 2193.0                            # cm, amplitud del oleaje a 470 m (spec 3.4)
R = 47000.0
PXDEG = (16.4, 25.0)                     # px/grado: eye buffer 125 % en el centro / panel (el del constructor)
DT = 1.0 / 72.0
res = {}
for lab, T0 in TS.items():
    n = 4000
    t64 = T0 + DT * np.arange(n)          # el motor acumula en double y castea a float por cuadro
    t32 = t64.astype(f32)
    ulp = float(np.spacing(f32(T0)))
    worst_phase = 0.0; worst_jit = 0.0; worst_v1 = 0.0
    for T in PER:
        # v2: frac(SwellSpeed * Tt / T) en float32 (SwellSpeed = 1)
        ph32 = (f32(1.0) * t32 / f32(T)).astype(f32)
        ph32 = ph32 - np.floor(ph32)
        ph64 = np.mod(t64 / T, 1.0)
        d = np.abs(((ph32.astype(np.float64) - ph64 + 0.5) % 1.0) - 0.5)
        worst_phase = max(worst_phase, float(d.max()))
        # irregularidad del paso: incremento por cuadro contra el nominal DT/T (en vueltas)
        inc = np.diff(ph32.astype(np.float64)); inc = (inc + 0.5) % 1.0 - 0.5
        jit = np.abs(inc - DT / T).max()
        worst_jit = max(worst_jit, float(jit))
        # v1 (sin frac): sin(2 pi * Tt / T) con el argumento en float32 -> error de fase en rad
        a32 = (f32(6.2831853) * t32).astype(f32) / f32(T)
        a64 = 2 * np.pi * t64 / T
        worst_v1 = max(worst_v1, float(np.abs(a32.astype(np.float64) - a64).max()) / (2 * np.pi))
    # efecto en la altura a 470 m: dh = A * (w/2.95) * 2 pi * dvueltas ; peor ola = la de mayor peso
    dh = A470 * (1.0 / 2.95) * 2 * np.pi * worst_phase
    djit = A470 * (1.0 / 2.95) * 2 * np.pi * worst_jit
    deg = np.degrees(dh / R); degj = np.degrees(djit / R)
    # el patron viaja: la cresta mas rapida a 470 m se mueve ~0,65 grados/s (spec 3.8): corrimiento por el error de TIEMPO
    tq = ulp / 2
    res[lab] = dict(T=T0, ulp_s=ulp, cuantizacion_s=tq, frac_cuadro=tq / DT,
                    fase_err_vueltas=worst_phase, jitter_vueltas=worst_jit, v1_fase_err_vueltas=worst_v1,
                    dh_470_cm=dh, jitter_dh_470_cm=djit, deg=deg, jitter_deg=degj,
                    px=[deg * p for p in PXDEG], jitter_px=[degj * p for p in PXDEG],
                    patron_px_por_tiempo=[0.65 * tq * p for p in PXDEG])
    print("%-16s ulp %.2e s (%.1f %% de un cuadro) | fase v2 err %.1e vueltas, trabado %.1e vueltas/cuadro"
          " -> silueta 470 m: %.4f px (err) / %.4f px (trabado) @25px/grado | v1 sin frac: %.1e vueltas"
          % (lab, ulp, 100 * (ulp / 2) / DT, worst_phase, worst_jit, deg * 25, degj * 25, worst_v1))
(OUT / "clock_precision.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
