"""resumen_recorrido.py - FPS y tiempo de GPU POR ETAPA del APK de Test_Recorrido.

Lee el logcat de una sesion (sesion.log) y lo parte en tramos con las marcas que imprime
BP_StageTour_SC:
    TOUR: etapa <n> <NOMBRE> inicio      TOUR: etapa <n> <NOMBRE> fin
    TOUR: transicion <n>-><m> inicio     TOUR: transicion <n>-><m> fin
    TOUR: fin
Dentro de cada tramo resume las lineas VrApi que la Quest escribe una vez por segundo:
    FPS (entregados), App= (ms de GPU de la app: NO queda clavado en 13,9 por el vsync),
    GPU% y el CPU% del peor nucleo (W).

Uso:  python resumen_recorrido.py <carpeta de la sesion>
Escribe resumen.txt y tramos.csv en la misma carpeta y los muestra por pantalla.
"""
import os, re, sys, csv, statistics as st

RE_VR = re.compile(r"VrApi.*?FPS=(\d+)/(\d+).*?App=([\d.]+)ms.*?GPU%=([\d.]+)")
RE_CPU = re.compile(r"CPU%=([\d.]+)\(W([\d.]+)\)")
RE_FREE = re.compile(r"Free=(\d+)MB")
RE_ETAPA = re.compile(r"TOUR: etapa (\d) (\w+) (inicio|fin)")
RE_TRANS = re.compile(r"TOUR: transicion (\d)->(\d) (inicio|fin)")
RE_FIN = re.compile(r"TOUR: fin")


def pct(xs, p):
    if not xs:
        return float('nan')
    xs = sorted(xs)
    k = min(len(xs) - 1, max(0, int(round(p / 100.0 * (len(xs) - 1)))))
    return xs[k]


def main():
    if len(sys.argv) < 2:
        print(__doc__); return
    carpeta = sys.argv[1]
    path = os.path.join(carpeta, 'sesion.log')
    tramo = None           # nombre del tramo vigente
    orden = []
    datos = {}
    with open(path, encoding='utf-8', errors='replace') as f:
        for linea in f:
            m = RE_ETAPA.search(linea)
            if m:
                tramo = 'etapa %s %s' % (m.group(1), m.group(2)) if m.group(3) == 'inicio' else None
                if tramo and tramo not in datos:
                    datos[tramo] = []; orden.append(tramo)
                continue
            m = RE_TRANS.search(linea)
            if m:
                tramo = 'transicion %s->%s' % (m.group(1), m.group(2)) if m.group(3) == 'inicio' else None
                if tramo and tramo not in datos:
                    datos[tramo] = []; orden.append(tramo)
                continue
            if RE_FIN.search(linea):
                tramo = None; continue
            m = RE_VR.search(linea)
            if m and tramo:
                app = float(m.group(3))
                if app <= 0.0:          # la app no estaba dibujando (menu del sistema, carga)
                    continue
                c = RE_CPU.search(linea); fr = RE_FREE.search(linea)
                datos[tramo].append({'fps': int(m.group(1)), 'hz': int(m.group(2)), 'app': app,
                                     'gpu': float(m.group(4)), 'w': float(c.group(2)) if c else float('nan'), 'free': int(fr.group(1)) if fr else -1})

    filas = []
    for t in orden:
        s = datos[t]
        if not s:
            filas.append([t, 0] + [''] * 9); continue
        fps = [x['fps'] for x in s]; app = [x['app'] for x in s]; gpu = [x['gpu'] for x in s]
        w = [x['w'] for x in s if x['w'] == x['w']]
        bajo = sum(1 for x in s if x['fps'] < x['hz'] - 2)
        filas.append([t, len(s), round(st.median(fps), 1), min(fps), round(st.median(app), 2), round(pct(app, 90), 2),
                      round(max(app), 2), round(st.median(gpu) * 100, 0), round(st.median(w) * 100, 0) if w else '', bajo, min([x['free'] for x in s])])

    cab = ['tramo', 'seg', 'FPS med', 'FPS min', 'App med ms', 'App p90', 'App max', 'GPU% med', 'CPU peor nucleo %', 'seg bajo el refresco', 'RAM libre min MB']
    with open(os.path.join(carpeta, 'tramos.csv'), 'w', newline='', encoding='utf-8') as f:
        csv.writer(f).writerows([cab] + filas)
    lineas = ['Recorrido por etapas - ' + carpeta, '',
              'Presupuesto: 72 Hz = 13,9 ms. "App" es el tiempo de GPU de la app por cuadro.', '',
              '%-24s %5s %8s %8s %11s %8s %8s %9s %8s %8s %8s' % tuple(cab)]
    for r in filas:
        lineas.append('%-24s %5s %8s %8s %11s %8s %8s %9s %8s %8s %8s' % tuple(str(x) for x in r))
    txt = '\n'.join(lineas) + '\n'
    open(os.path.join(carpeta, 'resumen.txt'), 'w', encoding='utf-8').write(txt)
    print(txt)


if __name__ == '__main__':
    main()
