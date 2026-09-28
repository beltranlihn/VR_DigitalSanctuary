# -*- coding: utf-8 -*-
"""Resume una sesion de quest_entering_perf.ps1: cuanto pesa el metaball en Entering.

Uso:  python resumen_entering.py <carpeta de la sesion | sesion.log>

Lee el logcat completo de la sesion (sesion.log) y cruza dos cosas del MISMO reloj del
visor, asi que no hay desfasaje entre la PC y la Quest:
  - la telemetria VrApi (una linea por segundo): App = tiempo de GPU de la app por
    cuadro, FPS, GPU%, nivel y MHz de la GPU;
  - las marcas del Blueprint: los ecos 'PERF: entering modo N' de BP_PerfEntering_SC y
    los logs de la etapa (BLOB: entra, pacer en marcha, fin de la etapa...).

Por que App y no el FrameTime: el FrameTime queda clavado en 13,9 ms por el vsync cuando
la escena entra en 72 fps y entonces las restas entre modos son ruido (memoria
"instrumento saturado", 2026-09-26). App es trabajo de GPU: se puede restar igual.
La trampa que SI tiene: si la GPU baja de reloj en un modo liviano, ese modo mide de mas.
Por eso se imprime el MHz de cada fase y, si cambia, la cuenta normalizada por reloj.
"""
import csv
import datetime as dt
import os
import re
import statistics as st
import sys

PRESUPUESTO = 13.9  # ms por cuadro a 72 Hz
SETTLE = 3.0        # s que se descartan tras cada cambio de modo (la linea VrApi resume el segundo anterior)
MIN_MUESTRAS = 8    # ventanas mas cortas (los 2 s del control positivo) no cuentan como fase

RE_TS = re.compile(r"^(\d\d)-(\d\d) (\d\d):(\d\d):(\d\d)\.(\d{3})")
RE_VR = re.compile(r"VrApi.*?FPS=(\d+)/(\d+).*?GPU=(\d+)/(\d+),(\d+)/(\d+)MHz.*?App=([\d.]+)ms.*?GPU%=([\d.]+)")
RE_MODO = re.compile(r"PERF: entering modo (\d)")
RE_CPU = re.compile(r"CPU%=([\d.]+)\(W([\d.]+)\)")   # opcional: uso de CPU de la app y del PEOR nucleo (0..1)

DESC = {0: "todo", 1: "sin metaball", 2: "sin pacer", 3: "nada (piso)", 4: "sin fondo",
        5: "aire lleno", 6: "sin aire"}   # 5/6: BP_BreathAir_SC (PerfE5/PerfE6, plan de la respiracion 2026-09-28).
# BP_PerfEntering_SC no tiene PerfE5/E6: en 5 y 6 el fondo queda como en el modo anterior (en 0 4 5 6 6 5 4 0: oculto).

# marcas de la etapa (substring -> etiqueta). El orden no importa: se ordenan por tiempo.
MARCAS = [
    ("BREATHRIG: mandos y sensores montados", "mandos montados"),
    ("BLOB: entra", "metaball entra"),
    ("pacer en marcha", "pacer aparece (3 s de pausa de entrada)"),
    ("PERF: entering bucle", "pacer en bucle: arranca el A/B"),
    ("PERF: entering fin", "fin del A/B (todo visible)"),
    ("termino sus ciclos", "pacer termino sus ciclos"),
    ("BLOB: sale", "metaball sale"),
    ("BLOB: salida terminada", "metaball fuera"),
    ("BREATHSTAGE: fin de la etapa", "fin de la etapa (nivel vacio)"),
]


def ts(linea, anio):
    m = RE_TS.match(linea)
    if not m:
        return None
    mo, d, h, mi, s, ms = (int(x) for x in m.groups())
    return dt.datetime(anio, mo, d, h, mi, s, ms * 1000)


def leer(path):
    anio = dt.date.today().year
    vr, modos, marcas = [], [], []
    with open(path, encoding="utf-8", errors="ignore") as f:
        for linea in f:
            t = ts(linea, anio)
            if t is None:
                continue
            m = RE_VR.search(linea)
            if m:
                fps, _, _cpu_l, gpu_l, _cpu_mhz, gpu_mhz, app, gpup = m.groups()
                app = float(app)
                if app > 0.0:  # App=0 = la app no estaba dibujando (carga, menu del sistema)
                    mc = RE_CPU.search(linea)
                    cpuw = float(mc.group(2)) if mc else float("nan")
                    vr.append((t, app, int(fps), float(gpup), int(gpu_l), int(gpu_mhz), cpuw))
                continue
            m = RE_MODO.search(linea)
            if m:
                modos.append((t, int(m.group(1))))
                continue
            for sub, etiqueta in MARCAS:
                if sub in linea:
                    marcas.append((t, etiqueta))
                    break
    return vr, modos, marcas


def resumen_muestras(ms):
    if not ms:
        return None
    return {
        "app": st.median(x[1] for x in ms),
        "fps": st.median(x[2] for x in ms),
        "gpup": st.median(x[3] for x in ms),
        "lvl": st.mode([x[4] for x in ms]),
        "mhz": st.median(x[5] for x in ms),
        "cpuw": (st.median(x[6] for x in ms if x[6] == x[6]) if any(x[6] == x[6] for x in ms) else float("nan")),
        "n": len(ms),
    }


def entre(vr, a, b):
    return [x for x in vr if a <= x[0] < b]


class Tee(object):
    """Imprime en consola y a la vez escribe resumen.txt en UTF-8 (el Tee-Object de
    PowerShell 5.1 lo escribia en UTF-16 y se leia con espacios entre letras)."""

    def __init__(self, archivo):
        self.consola = sys.stdout
        self.f = open(archivo, "w", encoding="utf-8")

    def write(self, s):
        self.consola.write(s)
        self.f.write(s)

    def flush(self):
        self.consola.flush()
        self.f.flush()


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "."
    path = os.path.join(arg, "sesion.log") if os.path.isdir(arg) else arg
    carpeta = os.path.dirname(os.path.abspath(path))
    if not os.path.exists(path):
        print("No encuentro " + path)
        return 1
    sys.stdout = Tee(os.path.join(carpeta, "resumen.txt"))

    vr, modos, marcas = leer(path)
    if not vr:
        print("La sesion no tiene lineas VrApi con App>0: no hay nada que medir.")
        return 1
    t0 = vr[0][0]
    fin = vr[-1][0] + dt.timedelta(seconds=1)

    def rel(t):
        return (t - t0).total_seconds()

    # ---------------- ventanas del A/B ----------------
    ventanas = []
    for i, (t, m) in enumerate(modos):
        hasta = modos[i + 1][0] if i + 1 < len(modos) else fin
        for tm, et in marcas:
            if et.startswith("fin del A/B") and t < tm < hasta:
                hasta = tm
        ms = entre(vr, t + dt.timedelta(seconds=SETTLE), hasta)
        if len(ms) >= MIN_MUESTRAS:
            ventanas.append((t, hasta, m, resumen_muestras(ms), ms))

    # ---------------- linea de tiempo (marcas de la etapa) ----------------
    print("")
    print("=== LINEA DE TIEMPO de la sesion (App = tiempo de GPU por cuadro, mediana del tramo) ===")
    print("  %6s  %-40s %8s %6s %6s" % ("t (s)", "desde", "App ms", "FPS", "n"))
    hitos = sorted(marcas)
    bordes = [(t0, "arranque de la app")] + hitos + [(fin, "fin de la grabacion")]
    ab_ini = next((t for t, e in hitos if e.startswith("pacer en bucle")), None)
    ab_fin = next((t for t, e in hitos if e.startswith("fin del A/B")), None)
    for (ta, ea), (tb, _) in zip(bordes, bordes[1:]):
        r = resumen_muestras(entre(vr, ta, tb))
        if ab_ini and ab_fin and ta == ab_ini:
            print("  %6.0f  %-40s %8s %6s %6s" % (rel(ta), ea, "(A/B)", "", ""))
            continue
        if r:
            print("  %6.0f  %-40s %8.2f %6.0f %6d" % (rel(ta), ea, r["app"], r["fps"], r["n"]))
        else:
            print("  %6.0f  %-40s %8s %6s %6s" % (rel(ta), ea, "-", "-", "0"))

    # muestras crudas, por si hay que graficar
    with open(os.path.join(carpeta, "muestras.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t_s", "app_ms", "fps", "gpu_pct", "gpu_nivel", "gpu_mhz", "cpu_peor_nucleo", "modo"])
        for x in vr:
            modo = ""
            for (a, b, m, _, _) in ventanas:
                if a <= x[0] < b:
                    modo = m
            w.writerow(["%.1f" % rel(x[0]), x[1], x[2], x[3], x[4], x[5], x[6], modo])

    if not ventanas:
        print("")
        print("  (Sin fases A/B: sesion de solo mirar. El costo por tramo esta arriba.)")
        return 0

    # ---------------- A/B ----------------
    print("")
    print("=== A/B: fases en el orden en que se grabaron ===")
    por_modo = {}
    for k, (a, b, m, r, _) in enumerate(ventanas, 1):
        por_modo.setdefault(m, []).append(r)
        print("  fase %-2d modo %d %-13s  App %6.2f ms   FPS %3.0f   GPU%% %.2f   GPU nivel %d @ %4.0f MHz   CPU peor nucleo %s   (%d s)"
              % (k, m, DESC[m], r["app"], r["fps"], r["gpup"], r["lvl"], r["mhz"],
                 ("%.2f" % r["cpuw"]) if r["cpuw"] == r["cpuw"] else "-", r["n"]))

    print("")
    print("=== por modo (promedio de sus pasadas) ===")
    prom = {}
    seps = []
    for m in sorted(por_modo):
        rs = por_modo[m]
        apps = [r["app"] for r in rs]
        p = sum(apps) / len(apps)
        sep = (max(apps) - min(apps)) if len(apps) > 1 else None
        mhz = sum(r["mhz"] for r in rs) / len(rs)
        fps = min(r["fps"] for r in rs)
        prom[m] = (p, mhz, fps)
        if sep is not None:
            seps.append(sep)
        cw = [r["cpuw"] for r in rs if r["cpuw"] == r["cpuw"]]
        print("  modo %d %-13s  %6.2f ms   FPS %3.0f   GPU %4.0f MHz   CPU peor nucleo %s   %s"
              % (m, DESC[m], p, fps, mhz, ("%.2f" % (sum(cw) / len(cw))) if cw else "-",
                 ("(pasadas separadas por %.2f ms)" % sep) if sep is not None else "(UNA sola pasada)"))
    res = st.median(seps) if seps else None
    print("")
    if res is not None:
        print("  >> RESOLUCION del instrumento en esta sesion: %.2f ms" % res)
        print("     (mediana de las separaciones entre pasadas de un mismo modo: una diferencia")
        print("      entre modos menor que eso no significa nada)")
    else:
        print("  >> Sin segunda pasada no hay resolucion medida: tomar los numeros con pinzas.")
    res = res if res is not None else 0.0

    mhzs = [prom[m][1] for m in prom]
    reloj_cambia = (max(mhzs) - min(mhzs)) > 0.05 * max(mhzs)
    if reloj_cambia:
        print("")
        print("  OJO: la GPU cambio de reloj entre modos (%s MHz)." % ", ".join("%.0f" % x for x in mhzs))
        print("  Un modo liviano a menor reloj mide MAS ms de los que cuesta. Abajo se agrega la")
        print("  cuenta normalizada por reloj (ms equivalentes al reloj del modo 0).")

    def costo(a, b):
        if a not in prom or b not in prom:
            return None
        ms = prom[a][0] - prom[b][0]
        ref = prom[0][1] if 0 in prom else prom[a][1]
        norm = (prom[a][0] * prom[a][1] - prom[b][0] * prom[b][1]) / ref
        return ms, norm

    print("")
    print("=== LO QUE PESA CADA COSA (tiempo de GPU por cuadro) ===")
    total = prom[0][0] if 0 in prom else None
    filas = [
        ("METABALL  (m0 - m1)", costo(0, 1)),
        ("metaball  (m2 - m3, sin pacer)", costo(2, 3)),
        ("pacer     (m0 - m2)", costo(0, 2)),
        ("pacer     (m1 - m3, sin metaball)", costo(1, 3)),
        ("FONDO     (m0 - m4)", costo(0, 4)),
        ("AIRE      (m5 - m6, lleno vs oculto)", costo(5, 6)),
    ]
    for nombre, c in filas:
        if c is None:
            continue
        ms, norm = c
        extra = ""
        if total:
            extra = "  = %3.0f%% del cuadro con todo, %3.0f%% del presupuesto de 13,9" % (ms * 100 / total, ms * 100 / PRESUPUESTO)
        ruido = "   <- NO se distingue del ruido" if abs(ms) <= res else ""
        print("  %-34s %6.2f ms%s%s" % (nombre, ms, extra, ruido))
        if reloj_cambia:
            print("  %-34s %6.2f ms  (normalizado por reloj)" % ("", norm))
    if 3 in prom:
        queda = "fondo + mandos" if 4 in prom else "lo que queda"
        print("  %-34s %6.2f ms  (%s: sin metaball ni pacer)" % ("piso      (m3)", prom[3][0], queda))
    if all(m in prom for m in (0, 1, 2, 3)):
        inter = prom[0][0] - prom[1][0] - prom[2][0] + prom[3][0]
        print("  %-34s %6.2f ms  (si es grande, los costos no se suman: se tapan entre si)"
              % ("interaccion (m0-m1-m2+m3)", inter))

    # ---------------- veredicto ----------------
    print("")
    print("=== VEREDICTO ===")
    if 0 in prom and 1 in prom:
        c_meta = prom[0][0] - prom[1][0]
        app0, _, fps0 = prom[0]
        app1, _, fps1 = prom[1]
        if abs(c_meta) <= res:
            print("  El metaball no se distingue del ruido (%.2f ms contra %.2f de resolucion)." % (c_meta, res))
        else:
            print("  El metaball cuesta %.2f ms de GPU por cuadro: el %.0f%% de la etapa entera (%.2f ms)"
                  % (c_meta, c_meta * 100 / app0, app0))
            print("  y el %.0f%% del presupuesto de 72 Hz." % (c_meta * 100 / PRESUPUESTO))
        if app0 <= PRESUPUESTO and fps0 >= 71:
            print("  Con todo, la etapa ENTRA en 72 fps: sobran %.2f ms de GPU." % (PRESUPUESTO - app0))
        else:
            print("  Con todo, la etapa NO entra en 72 fps (App %.2f ms, FPS %.0f)." % (app0, fps0))
            if app1 <= PRESUPUESTO and fps1 >= 71:
                print("  Sin el metaball SI entra (App %.2f ms, FPS %.0f): el metaball es lo que la saca." % (app1, fps1))
            else:
                print("  Y sin el metaball tampoco entra (App %.2f ms): hay otro costo de fondo." % app1)
    else:
        print("  Faltan los modos 0 y 1, que son los que arman la cuenta del metaball.")
    if 0 in prom and 4 in prom:
        c_fondo = prom[0][0] - prom[4][0]
        if abs(c_fondo) <= res:
            print("  El fondo liquido no se distingue del ruido (%.2f ms contra %.2f de resolucion)." % (c_fondo, res))
        else:
            print("  El fondo liquido cuesta %.2f ms de GPU por cuadro (%.0f%% del presupuesto de 72 Hz)."
                  % (c_fondo, c_fondo * 100 / PRESUPUESTO))
    print("")
    print("  Muestras crudas: " + os.path.join(carpeta, "muestras.csv"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
