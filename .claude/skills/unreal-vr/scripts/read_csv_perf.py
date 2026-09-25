"""Resume uno o dos CSV del CsvProfiler traidos de la Quest.

Con dos archivos hace la comparacion A/B del test oficial de Meta
(references/profiling-quest.md §2-3): A a resolucion normal, B a resolucion baja.
  - si B mejora fuerte  -> fill-rate / fragment bound  -> el cuello es el shader y el overdraw
  - si B no cambia      -> CPU bound                   -> el cuello es el GameThread

🔴 NO inventa un filtro de "visor puesto": no hay ninguna columna que lo diga.
`MaxFrameTime` es constante y NO sirve para eso (costo un diagnostico equivocado).
La ventana valida la garantiza el script que graba, que arranca despues de la cuenta
regresiva. Aca solo se recortan los primeros segundos por las dudas.

Uso:
    python read_csv_perf.py perf/A.csv
    python read_csv_perf.py perf/A.csv perf/B.csv
"""
import csv
import io
import statistics as st
import sys

PRESUPUESTO_MS = 13.9  # 72 Hz
RECORTE = 60           # cuadros descartados al principio (arranque/acomodo)


def leer(ruta):
    filas = list(csv.DictReader(io.open(ruta, encoding="utf-8", errors="replace")))
    return filas[RECORTE:] if len(filas) > RECORTE * 3 else filas


def col(filas, nombre):
    out = []
    for f in filas:
        try:
            v = float(f.get(nombre, ""))
        except (TypeError, ValueError):
            continue
        if v > 0:
            out.append(v)
    return out


def stats(v):
    if len(v) < 20:
        return None
    v = sorted(v)
    return st.median(v), v[int(len(v) * 0.95)], v[-1]


def resumen(ruta, etiqueta):
    filas = leer(ruta)
    print(f"--- {etiqueta}: {ruta}  ({len(filas)} cuadros) ---")

    # CONTROL del experimento: si la resolucion cambio de verdad, cambia el tamanio
    # del pool de render targets. Sin esto, "B no mejoro" puede significar
    # "no es fill-rate" o "la cvar no hizo nada", y son cosas distintas.
    rt = col(filas, "RenderTargetPoolSize")
    if rt:
        print(f"    RenderTargetPoolSize: {st.median(rt):.1f} MB   <- control de resolucion")

    print(f"    {'metrica':<16}{'mediana':>9}{'p95':>9}{'max':>9}")
    salida = {}
    for c, nombre in [("FrameTime", "Frame"), ("GameThreadTime", "Game"),
                      ("RenderThreadTime", "Render"), ("RHIThreadTime", "RHI"),
                      ("GPUTime", "GPU")]:
        r = stats(col(filas, c))
        if r:
            salida[c] = r[0]
            print(f"    {nombre:<16}{r[0]:>9.2f}{r[1]:>9.2f}{r[2]:>9.2f}")

    ft = col(filas, "FrameTime")
    if ft:
        fuera = [x for x in ft if x > PRESUPUESTO_MS]
        print(f"    fps a la mediana: {1000.0 / st.median(ft):.1f}"
              f"   ·  cuadros sobre 13,9 ms: {100.0 * len(fuera) / len(ft):.0f}%")

    # Los mas caros del GameThread, que es donde se decide que optimizar.
    gt = [c for c in (filas[0].keys() if filas else []) if c and c.startswith("Exclusive/GameThread/")]
    rank = []
    for c in gt:
        v = col(filas, c)
        if len(v) >= 50:
            rank.append((st.median(v), c.split("/")[-1]))
    rank.sort(reverse=True)
    if rank:
        print("    GameThread, lo mas caro:")
        for m, n in rank[:5]:
            print(f"        {m:>8.2f} ms  {n}")
    print()
    return salida


def main(rutas):
    if not rutas:
        sys.exit("uso: read_csv_perf.py A.csv [B.csv]")

    a = resumen(rutas[0], "A  resolucion normal" if len(rutas) > 1 else "captura")
    if len(rutas) < 2:
        return
    b = resumen(rutas[1], "B  resolucion BAJA")

    fa, fb = a.get("FrameTime"), b.get("FrameTime")
    if not (fa and fb):
        return
    mejora = 100.0 * (fa - fb) / fa
    print("=" * 58)
    print(f"A {fa:.2f} ms  ->  B {fb:.2f} ms   ({mejora:+.0f}%)")
    if mejora > 25:
        print("VEREDICTO: FILL-RATE BOUND. Bajar resolucion lo arregla, asi que el")
        print("cuello son los pixeles: shader caro y/o overdraw de translucidos.")
    elif mejora < 10:
        print("VEREDICTO: CPU BOUND. Los pixeles no son el problema — mirar el")
        print("GameThread de arriba (ticks de Blueprint, cantidad de actores).")
    else:
        print("VEREDICTO: mixto. Mejora parcial: hay costo de pixeles Y de CPU.")
    print("=" * 58)


if __name__ == "__main__":
    main(sys.argv[1:])
