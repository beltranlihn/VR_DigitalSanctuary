# -*- coding: utf-8 -*-
"""Lee los tramos de quest_sesion_larga.ps1 y contesta QUE hipotesis sobrevive.

Uso:  python resumen_sesion_larga.py <carpeta de la sesion>

El test separa dos causas que producen el MISMO sintoma (material animado que se traba
mientras manos y mundo siguen fluidos):

  H1 - reloj en fp16   -> el frame time se queda PLANO y el trabado aparece igual.
  H2 - throttling      -> el frame time CRECE con los minutos (y la temperatura sube);
                          el runtime reproyecta, por eso las manos se ven bien.

Lo que decide es la PENDIENTE, no el valor absoluto. Y como la escena es fill-rate bound,
el ruido entre tramos es alto (el mismo build dio 21,65 y 24,85 ms segun hacia donde se
mirara, gotcha 379): por eso se compara el PRIMER TERCIO contra el ULTIMO, no tramo a
tramo, y se imprime la dispersion para poder decir si la diferencia significa algo.
"""
import csv
import os
import re
import statistics as st
import sys

PRESUPUESTO = 13.9  # ms para 72 Hz


def columnas(path):
    """Mediana de FrameTime y de GPUTime (si esta), y % de cuadros pegados al cap."""
    with open(path, newline="", encoding="utf-8", errors="ignore") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return None
    mapa = {}
    for c in rows[0].keys():
        if c:
            mapa[c.strip().lower()] = c
    out = {}
    for quiero in ("frametime", "gputime"):
        col = mapa.get(quiero)
        if not col:
            continue
        vals = []
        for r in rows:
            try:
                vals.append(float(r[col]))
            except Exception:
                pass
        if vals:
            out[quiero] = vals
    if "frametime" not in out:
        return None
    ft = out["frametime"]
    # Pegado al cap de 72 Hz = el vsync esta tapando el costo real: ahi la mediana no
    # se lee como "lo que cuesta el cuadro", y una subida se ve como caida del cap.
    cap = sum(1 for v in ft if 13.4 < v < 14.4) * 100.0 / len(ft)
    return {
        "frame": st.median(ft),
        "gpu": st.median(out["gputime"]) if "gputime" in out else None,
        "n": len(ft),
        "cap": cap,
    }


def temperaturas(carpeta):
    """{tramo: texto de zonas} de temperatura.csv, si existe."""
    path = os.path.join(carpeta, "temperatura.csv")
    if not os.path.exists(path):
        return {}
    out = {}
    with open(path, newline="", encoding="utf-8", errors="ignore") as f:
        for row in csv.reader(f):
            if len(row) >= 3 and row[0] != "segundo":
                out[row[1]] = row[2]
    return out


def pico(texto):
    """La temperatura mas alta de la linea de zonas (la placa mas caliente)."""
    vals = [float(x) for x in re.findall(r"=([0-9]+\.[0-9]+)", texto or "")]
    vals = [v for v in vals if 10.0 < v < 120.0]
    return max(vals) if vals else None


def main():
    carpeta = sys.argv[1] if len(sys.argv) > 1 else "."
    archivos = sorted(f for f in os.listdir(carpeta) if re.match(r"^tramo\d+\.csv$", f))
    if not archivos:
        print("No encontre CSV de tramos (tramoNN.csv) en " + carpeta)
        return 1

    temps = temperaturas(carpeta)
    filas = []
    for f in archivos:
        k = int(re.match(r"^tramo(\d+)\.csv$", f).group(1))
        d = columnas(os.path.join(carpeta, f))
        if d is None:
            print("  (sin datos) " + f)
            continue
        d["k"] = k
        d["temp"] = pico(temps.get(str(k)))
        filas.append(d)

    if len(filas) < 2:
        print("Hacen falta al menos 2 tramos con datos.")
        return 1

    print("")
    print("=== la sesion, tramo por tramo ===")
    print("  tramo  minuto   frame     GPU    en cap   temp")
    for d in filas:
        minuto = (d["k"] - 1)  # tramos de 60 s -> 1 tramo = 1 minuto
        gpu = ("%6.2f" % d["gpu"]) if d["gpu"] is not None else "     -"
        tmp = ("%5.1fC" % d["temp"]) if d["temp"] is not None else "    -"
        print("  %5d  %6d  %6.2f ms %s   %3.0f%%  %s"
              % (d["k"], minuto, d["frame"], gpu, d["cap"], tmp))

    n = len(filas)
    t = max(1, n // 3)
    ini = [d["frame"] for d in filas[:t]]
    fin = [d["frame"] for d in filas[-t:]]
    m_ini, m_fin = st.median(ini), st.median(fin)
    deriva = m_fin - m_ini
    # La dispersion DENTRO de cada tercio es la resolucion del instrumento: una deriva
    # menor que eso no se puede distinguir del ruido de hacia donde se estaba mirando.
    disp = max(
        (max(ini) - min(ini)) if len(ini) > 1 else 0.0,
        (max(fin) - min(fin)) if len(fin) > 1 else 0.0,
    )

    print("")
    print("=== la cuenta que decide ===")
    print("  primer tercio (tramos 1-%d):   %6.2f ms" % (t, m_ini))
    print("  ultimo tercio  (ultimos %d):    %6.2f ms" % (t, m_fin))
    print("  DERIVA:                        %+6.2f ms" % deriva)
    print("  dispersion dentro de un tercio: %6.2f ms  <- resolucion del instrumento"
          % disp)
    cap_ini = st.median([d["cap"] for d in filas[:t]])
    cap_fin = st.median([d["cap"] for d in filas[-t:]])
    print("  cuadros en el cap de 72 Hz:     %3.0f%% -> %3.0f%%" % (cap_ini, cap_fin))

    tt = [d["temp"] for d in filas if d["temp"] is not None]
    if len(tt) > 1:
        print("  temperatura:                   %5.1fC -> %5.1fC" % (tt[0], tt[-1]))

    print("")
    print("=== veredicto ===")
    if deriva > disp and deriva > 0.5:
        print("  El frame time SUBE con los minutos (%+.2f ms, por encima de la" % deriva)
        print("  resolucion de %.2f ms). Eso es H2: la GPU se esta apretando con el" % disp)
        print("  tiempo y lo que se ve trabado es reproyeccion, NO el reloj del shader.")
        print("  -> El fix de View.GameTime no es la causa del sintoma. Atacar carga")
        print("     y temperatura (A4 de poda, enfoque C de esferas, o FFR 1).")
    elif cap_fin < cap_ini - 20:
        print("  El frame time parece plano PERO se despego del cap de 72 Hz")
        print("  (%3.0f%% -> %3.0f%%): el vsync estaba tapando la subida. Leer como H2." % (cap_ini, cap_fin))
    else:
        print("  El frame time se mantiene PLANO (deriva %+.2f ms, dentro del ruido de" % deriva)
        print("  %.2f ms) y los cuadros siguen en el cap." % disp)
        print("  -> Si Beltran VIO el trabado en esta sesion, no es carga: es H1, el")
        print("     reloj, y hay que mirar que quedo animando en fp16 fuera del Custom.")
        print("  -> Si NO lo vio, el fix del reloj (o el tubo) resolvio el sintoma.")
    print("")
    print("  OJO: Este script mide el FRAMERATE, no el trabado. El dato que falta siempre")
    print("     lo aporta Beltran: si vio trabarse el material y en que minuto.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
