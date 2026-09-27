# -*- coding: utf-8 -*-
"""Resume una sesion de quest_heart_perf.ps1: cuanto pesan los VERTICES y los PIXELES de la
membrana del latido (BP_HeartScape_SC / M_HeartScape_SC).

Uso:  python resumen_heart.py <carpeta de la sesion | sesion.log>

Reusa el parser de resumen_entering.py (misma telemetria VrApi: App = tiempo de GPU de la app
por cuadro, que NO queda clavado en 13,9 ms por el vsync). Solo cambian los ecos y las cuentas.

Modos (PerfMode del material, eventos Perf0..Perf3 del actor):
  0 todo              la escena tal como esta autorada (referencia)
  1 vertices baratos  sin ondas: WPO, gradiente y crestas en cero (los pixeles siguen igual)
  2 pixeles baratos   la membrana y la esfera se pintan de un color plano (los vertices siguen)
  3 ambos baratos     el piso: cielo + geometria sin trabajo
Cuentas:  vertices = m0 - m1  |  pixeles = m0 - m2  |  piso = m3  |  interaccion = m0 - m1 - m2 + m3
"""
import os
import re
import statistics as st
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import resumen_entering as R  # noqa: E402

R.RE_MODO = re.compile(r"PERF: heart modo (\d)")
R.MARCAS = []
DESC = {0: "todo", 1: "vert. baratos", 2: "pix. baratos", 3: "ambos (piso)"}


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
        print("  fase %-2d modo %d %-14s App %6.2f ms   FPS %3.0f   GPU %4.0f MHz   (%d s)"
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
        print("  modo %d %-14s %6.2f ms   FPS %3.0f   GPU %4.0f MHz" % (m, DESC.get(m, "?"), p, prom[m][2], prom[m][1]))
    res = st.median(seps) if seps else 0.0
    print("")
    print("  >> RESOLUCION del instrumento: %.2f ms (separacion mediana entre pasadas de un modo)" % res)

    def d(a, b):
        return (prom[a][0] - prom[b][0]) if (a in prom and b in prom) else None

    print("")
    print("=== LO QUE PESA CADA COSA (GPU por cuadro, presupuesto %.1f ms) ===" % R.PRESUPUESTO)
    for et, v in (("VERTICES   (m0 - m1)", d(0, 1)), ("PIXELES    (m0 - m2)", d(0, 2))):
        if v is not None:
            marca = "" if abs(v) > res else "   <- dentro del ruido"
            print("  %-22s %6.2f ms  (%3.0f%% del presupuesto)%s" % (et, v, v * 100 / R.PRESUPUESTO, marca))
    if 3 in prom:
        print("  %-22s %6.2f ms  (cielo + geometria sin trabajo)" % ("piso       (m3)", prom[3][0]))
    if all(m in prom for m in (0, 1, 2, 3)):
        print("  %-22s %6.2f ms" % ("interaccion", prom[0][0] - prom[1][0] - prom[2][0] + prom[3][0]))
    if 0 in prom:
        app0 = prom[0][0]
        print("")
        print("  La escena completa: App %.2f ms, FPS %.0f -> %s"
              % (app0, prom[0][2], "ENTRA en 72 Hz" if app0 <= R.PRESUPUESTO - 1.0 else
                 ("justo en el borde" if app0 <= R.PRESUPUESTO else "NO entra")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
