# -*- coding: utf-8 -*-
"""Resume una sesion de quest_chladni_perf.ps1: que parte del SALAR DE CHLADNI (M_ChladniFloor_SC, entorno de
Attracting en Test_Sequencer) se come el presupuesto, y cuanto rinde la version con gradiente analitico.

Uso:  python resumen_chladni.py <carpeta de la sesion | sesion.log>

Reusa el parser de resumen_entering.py (telemetria VrApi: App = tiempo de GPU de la app por cuadro, que NO queda
clavado en 13,9 ms por el vsync). Todas las fases corren con PerfForce = 1: las 8 figuras del mandala talladas
(peor caso fijo, no depende de lo que haya en la mesa).

Modos (PerfMode del material, eventos ChladniPerf0..6 del actor):
  0 actual          3 evaluaciones del campo por pixel (diferencias finitas). La referencia
  1 analitico       UNA evaluacion con gradiente analitico: el candidato (mismo look)
  2 sin mandala PS  el relieve del mandala no se calcula en pixeles
  3 sin WPO         el vertex shader devuelve 0
  4 piso plano      el piso sale de un color apenas pasa el cielo
  5 cielo plano     el cielo sale de un color
  6 sin acabado     piso sin poligonos, arena, manchas, agua ni bruma
"""
import os
import re
import statistics as st
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import resumen_entering as R  # noqa: E402

R.RE_MODO = re.compile(r"PERF: chladni modo (\d)")
R.MARCAS = []
DESC = {0: "OBRA", 1: "sin arena", 2: "sin mandala PS", 3: "sin WPO", 4: "piso plano", 5: "cielo plano", 6: "sin acabado",
        7: "sin poligonos", 8: "sin agua", 9: "sin bruma"}


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "."
    path = os.path.join(arg, "sesion.log") if os.path.isdir(arg) else arg
    carpeta = os.path.dirname(os.path.abspath(path))
    if not os.path.exists(path):
        print("No encuentro " + path)
        return 1
    sys.stdout = R.Tee(os.path.join(carpeta, "resumen.txt"))
    vr, modos, _ = R.leer(path)
    if not vr:
        print("La sesion no tiene lineas VrApi con App>0: no hay nada que medir.")
        return 1
    import datetime as dt
    fin = vr[-1][0] + dt.timedelta(seconds=1)
    ventanas = []
    for i, (t, m) in enumerate(modos):
        hasta = modos[i + 1][0] if i + 1 < len(modos) else fin
        ms = R.entre(vr, t + dt.timedelta(seconds=R.SETTLE), hasta)
        if len(ms) >= R.MIN_MUESTRAS:
            ventanas.append((m, R.resumen_muestras(ms)))
    if not ventanas:
        todo = R.resumen_muestras(vr)
        print("Sin fases A/B. Sesion entera: App %.2f ms (mediana), FPS %.0f." % (todo["app"], todo["fps"]))
        return 0

    print("")
    print("=== fases en el orden en que se grabaron ===")
    por = {}
    for k, (m, r) in enumerate(ventanas, 1):
        por.setdefault(m, []).append(r)
        print("  fase %-2d modo %d %-15s App %6.2f ms   FPS %3.0f   GPU %4.0f MHz   (%d s)"
              % (k, m, DESC.get(m, "?"), r["app"], r["fps"], r["mhz"], r["n"]))
    print("")
    print("=== por modo (promedio de sus pasadas) ===")
    prom, seps = {}, []
    for m in sorted(por):
        apps = [r["app"] for r in por[m]]
        p = sum(apps) / len(apps)
        prom[m] = (p, sum(r["mhz"] for r in por[m]) / len(por[m]), min(r["fps"] for r in por[m]))
        if len(apps) > 1:
            seps.append(max(apps) - min(apps))
        print("  modo %d %-15s %6.2f ms   FPS %3.0f   GPU %4.0f MHz" % (m, DESC.get(m, "?"), p, prom[m][2], prom[m][1]))
    res = st.median(seps) if seps else 0.0
    print("")
    print("  >> RESOLUCION del instrumento: %.2f ms (separacion mediana entre pasadas de un modo)" % res)

    def d(a, b):
        return (prom[a][0] - prom[b][0]) if (a in prom and b in prom) else None

    print("")
    print("=== LO QUE PESA CADA COSA (GPU por cuadro, presupuesto %.1f ms) ===" % R.PRESUPUESTO)
    for et, v in (("arena/granito/manchas (m0 - m1)", d(0, 1)),
                  ("poligonos          (m0 - m7)", d(0, 7)),
                  ("agua               (m0 - m8)", d(0, 8)),
                  ("bruma              (m0 - m9)", d(0, 9)),
                  ("mandala en pixeles (m0 - m2)", d(0, 2)),
                  ("WPO / vertices     (m0 - m3)", d(0, 3)),
                  ("piso entero PS     (m0 - m4)", d(0, 4)),
                  ("cielo              (m0 - m5)", d(0, 5)),
                  ("acabado del piso   (m0 - m6)", d(0, 6))):
        if v is not None:
            marca = "" if abs(v) > res else "   <- dentro del ruido"
            print("  %-30s %6.2f ms  (%3.0f%% del presupuesto)%s" % (et, v, v * 100 / R.PRESUPUESTO, marca))
    for m, et in ((0, "OBRA optimizada"),):
        if m in prom:
            a = prom[m][0]
            print("")
            print("  Etapa %s: App %.2f ms, FPS %.0f -> %s" % (et, a, prom[m][2],
                  "ENTRA en 72 Hz" if a <= R.PRESUPUESTO - 1.0 else ("justo en el borde" if a <= R.PRESUPUESTO else "NO entra")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
