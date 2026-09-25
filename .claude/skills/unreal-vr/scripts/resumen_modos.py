# -*- coding: utf-8 -*-
"""Resume las fases de quest_perfmodes.ps1 y saca la cuenta que decide.

Uso:  python resumen_modos.py <carpeta con los CSV>

Cada modo se mide DOS veces (ida y vuelta) para que una deriva termica progresiva no
se le cargue entera a la ultima fase. Aca se promedian las dos y ademas se imprime la
separacion entre ellas: **esa separacion es la resolucion real del instrumento**, y
cualquier diferencia entre modos menor que ella no significa nada (gotcha 379).
"""
import csv
import os
import re
import statistics as st
import sys

PRESUPUESTO = 13.9  # ms para 72 Hz


def mediana_frame(path):
    with open(path, newline="", encoding="utf-8", errors="ignore") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return None, 0
    col = None
    for c in rows[0].keys():
        if c and c.strip().lower() == "frametime":
            col = c
            break
    if col is None:
        return None, 0
    vals = []
    for r in rows:
        try:
            vals.append(float(r[col]))
        except Exception:
            pass
    if not vals:
        return None, 0, 0.0
    # % de cuadros pegados al cap de 72 Hz: si es alto, el vsync esta tapando
    # el costo real y la mediana NO se puede leer como "lo que cuesta el cuadro".
    cap = sum(1 for v in vals if 13.4 < v < 14.4) * 100.0 / len(vals)
    return st.median(vals), len(vals), cap


def main():
    carpeta = sys.argv[1] if len(sys.argv) > 1 else "."
    archivos = [f for f in os.listdir(carpeta) if re.match(r"^modo\d_.*_p\d+\.csv$", f)]
    if not archivos:
        print("No encontre CSV de fases (modoN_*_pK.csv) en " + carpeta)
        return 1

    por_modo = {}
    for f in sorted(archivos):
        m = re.match(r"^(modo\d)_([a-z]+)_p(\d+)\.csv$", f)
        med, n, cap = mediana_frame(os.path.join(carpeta, f))
        if med is None:
            print("  (sin datos) " + f)
            continue
        clave = m.group(1) + " " + m.group(2)
        por_modo.setdefault(clave, []).append((int(m.group(3)), med, n, cap))

    print("")
    print("=== fases, en el orden en que se grabaron ===")
    todas = []
    for clave in por_modo:
        for p, med, n, cap in por_modo[clave]:
            todas.append((p, clave, med, n, cap))
    for p, clave, med, n, cap in sorted(todas):
        marca = "   <- %.0f%% de cuadros en el cap de 72 Hz" % cap if cap > 20 else ""
        print("  fase %-2d  %-14s  %6.2f ms   (%d cuadros)%s" % (p, clave, med, n, marca))

    print("")
    print("=== por modo (promedio de sus dos pasadas) ===")
    resumen = {}
    for clave in sorted(por_modo):
        meds = [x[1] for x in por_modo[clave]]
        prom = sum(meds) / len(meds)
        sep = (max(meds) - min(meds)) if len(meds) > 1 else 0.0
        resumen[clave] = (prom, sep)
        print("  %-14s  %6.2f ms   (las dos pasadas separadas por %.2f ms)" % (clave, prom, sep))

    seps = sorted([v[1] for v in resumen.values()])
    peor_sep = st.median(seps) if seps else 0.0
    print("")
    print("  >> RESOLUCION DEL INSTRUMENTO en esta sesion: %.2f ms" % peor_sep)
    print("     (mediana de las separaciones; una diferencia entre modos menor que eso")
    print("      no significa nada). Separaciones: %s" % ", ".join("%.2f" % x for x in seps))
    for clave in sorted(resumen):
        if resumen[clave][1] > peor_sep * 3 + 0.5:
            print("     ATENCION: %s tiene %.2f ms entre sus dos pasadas -- muy por encima"
                  % (clave, resumen[clave][1]))
            print("     del resto. Eso NO es ruido del instrumento: es que en una de las dos")
            print("     se miro otra cosa. Ese modo hay que volver a medirlo.")

    actual = None
    gratis = None
    for clave in resumen:
        if clave.startswith("modo0"):
            actual = resumen[clave][0]
        if clave.startswith("modo3"):
            gratis = resumen[clave][0]

    if actual is not None and gratis is not None:
        cuesta = actual - gratis
        print("")
        print("=== LA CUENTA QUE DECIDE ===")
        print("  material de blobs tal como esta : %6.2f ms" % actual)
        print("  el mismo cuadro sin dibujarlos  : %6.2f ms" % gratis)
        print("  --------------------------------------------")
        print("  cuesta TODA la tecnica          : %6.2f ms" % cuesta)
        print("  presupuesto para 72 Hz          : %6.2f ms" % PRESUPUESTO)
        print("")
        if cuesta < peor_sep:
            print("  VEREDICTO: la tecnica NO se distingue del ruido. El coste esta")
            print("  en otro lado -- no tiene sentido seguir optimizando este material.")
        elif gratis > PRESUPUESTO + 1.0:
            falta = gratis - PRESUPUESTO
            print("  VEREDICTO: aunque los blobs fueran GRATIS el cuadro seguiria en")
            print("  %.2f ms, o sea %.2f ms por encima del presupuesto." % (gratis, falta))
            print("  Cambiar de tecnica NO alcanza por si solo: hay otro costo de fondo.")
        else:
            print("  VEREDICTO: sin los blobs la escena ENTRA EN PRESUPUESTO.")
            print("  OJO al leer el %.2f ms del modo 3: esta pegado al cap de 72 Hz, asi" % gratis)
            print("  que el costo real es ESE O MENOR -- el vsync no deja ver cuanto menos.")
            print("  O sea: la tecnica de blobs ES el problema, y el resto de la escena no.")
            print("  Presupuesto que tiene que respetar el reemplazo: MENOS de %.2f ms." % cuesta)
    else:
        print("")
        print("  Faltan el modo0 o el modo3, que son los que arman la cuenta.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
