# -*- coding: utf-8 -*-
"""cortar_clips.py (tools/demo, 2026-10-23; antes de cortar: grabar_pasada.py menu/breath/heart/draw) - corta los clips de cada sonido de docs/demo/SONIDOS-DEMO.md desde los cuadros de rec_nivel.py.
Cada clip: 15 fps, 640 px, H.264 liviano, con el numero y nombre del sonido arriba, un reloj abajo y la marca EVENTO en el
instante en que tiene que arrancar el sonido (el evento del log)."""
import os, re, subprocess, sys

SP = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'VR_Test', 'Saved', 'ClaudeScripts', 'clips')  # cuadros y logs (no se versionan)
os.makedirs(SP, exist_ok=True)
DEST = os.path.join(os.path.expanduser('~'), 'Desktop', 'Soul Charger Demo - Sonidos', 'Videos por sonido')
FPS = 15
FONT = 'C\\:/Windows/Fonts/arial.ttf'

# (numero, nombre, pasada, marcador del log (regex), desde s, hasta s)  -- desde/hasta relativos al evento
CORTES = [
    ('1.1a', 'Menu - aparece el titulo', 'menu', r'DEMO: menu arranca', 0.0, 14.0),
    ('1.1b', 'Menu - entra START (0.3 entrada de boton)', 'menu', r'DEMO: START visible', -0.8, 4.0),
    ('1.2', 'Menu - sale el titulo al apretar START', 'menu', r'DEMO: START$', -0.8, 4.5),
    ('1.3', 'Menu - entran BACK y los 3 cuadros', 'menu', r'DEMO: experiencias visibles', -0.8, 4.5),
    ('1.5', 'Menu - se van los cuadros, BACK y los laseres', 'menu', r'DEMO: elegida la experiencia', -0.8, 6.0),
    ('1.6', 'Menu - viaje (arranque)', 'menu', r'DEMO: viaje por el espacio', -0.8, 14.0),
    ('1.7', 'Menu - el HUD se instala (0.11)', 'menu', r'HUDKIT: aparece el HUD', -0.8, 5.5),
    ('1.8', 'Menu - cierre al velo azul', 'menu', r'DEMO: abre la experiencia', -7.5, 1.0),
    ('2.1-2.2', 'Entrada a la experiencia - abre el velo y titulo', 'breath', r'DEMOFLOW: arranca la experiencia', 0.0, 10.0),
    ('0.5-0.8', 'Entra el panel de instrucciones y el objeto que flota', 'breath', r'DEMOFLOW: panel y objeto al frente', -0.8, 4.0),
    ('0.10', 'Tomar el objeto (sensor)', 'breath', r'DEMOFLOW: tomado con la mano', -0.8, 3.0),
    ('0.6', 'Pasar pagina del panel', 'breath', r'DEMOFLOW: pagina 2', -0.8, 2.5),
    ('0.7', 'Sale el panel de instrucciones', 'breath', r'termino la ultima instruccion', -0.8, 3.5),
    ('3.4', 'Breath - nace la metaball', 'breath', r'BLOB: entra', -0.8, 6.0),
    ('3.5', 'Breath - el mando se convierte en el sensor', 'breath', r'UserTool.ToSensor', -0.8, 3.5),
    ('3.6', 'Breath - exploracion libre', 'breath', r'StageBegin \(exploracion libre\)', 0.0, 10.0),
    ('3.7-3.8', 'Breath - cuenta y aparece el pacer', 'breath', r'pacer lanzado con la cuenta', -0.8, 5.5),
    ('3.9-3.13', 'Breath - un ciclo (inhala 5 s, sostiene 3 s, exhala 8 s)', 'breath', r'BREATHSTAGE: pacer en marcha', -0.8, 17.5),
    ('3.9-3.13b', 'Breath - parte final (inhala 5, sostiene 3, exhala 10, pulmones vacios 5)', 'breath', r'parte final: exhalacion larga', -0.8, 24.5),
    ('3.11c', 'Breath - ultimo ciclo (inhala 5, exhala con suspiro 6)', 'breath', r'ultimo ciclo: suspiro', -0.8, 12.5),
    ('6.0-3.15-3.16', 'Breath - termina la mecanica (se van el pacer y la metaball)', 'breath2', r'el pacer termino y se va', -1.5, 6.0),
    ('4.1-4.2', 'Heart - tomar el sensor (se tine de rojo)', 'heart', r'DEMOFLOW: tomado con la mano', -0.8, 3.5),
    ('4.3-4.4', 'Heart - umbral del pecho y primeros latidos', 'heart', r'HEART: (UMBRAL IN|latido)', -0.8, 6.0),
    ('4.5', 'Heart - sale el panel', 'heart', r'tres pulsos: se va el panel', -0.8, 3.5),
    ('4.6', 'Heart - sube la esfera', 'heart', r'la esfera sube', -0.8, 5.5),
    ('4.4b', 'Heart - latidos durante la etapa', 'heart', r'la esfera arriba: vuelve el latido', 0.0, 10.0),
    ('4.7', 'Heart - el mar empieza a girar', 'heart', r'el mar empieza la vuelta', 0.0, 14.0),
    ('6.0b', 'Heart - termina la etapa', 'heart', r'DEMOFLOW: la etapa termino', -1.0, 4.0),
    ('3.17-4.8', 'Se va el sensor de la mano y vuelven las manos', 'heart', r'se fueron los mandos', -2.5, 2.5),
    ('6.1', 'Final - el HUD tiembla y hace pop', 'heart', r'HUDKIT: el HUD tiembla', -0.8, 4.0),
    ('6.2', 'Final - aparece el cuadro de resultados', 'heart', r'RESULTADOS: aparece el cuadro', -0.8, 4.0),
    ('6.4b', 'Final - aparece el boton FINISH', 'heart', r'aparece FINISH', -0.8, 3.5),
    ('6.4-6.4d', 'Final - se van el cuadro y FINISH', 'draw', r'RESULTADOS: se va el cuadro', -0.8, 4.0),
    ('6.5', 'Final - cierre a negro', 'draw', r'DEMOFLOW: negro', -0.8, 6.0),
    ('5.1-5.2', 'Draw - tomar el pincel y aparece la paleta', 'draw', r'DEMOFLOW: tomado con la mano', -0.8, 5.0),
    ('5.3', 'Draw - trazo de practica (pincel marcador)', 'draw', r'a dibujar \(trazo de practica\)', 0.0, 8.0),
    ('5.13-5.14', 'Draw - se borra el trazo de practica y arranca el reloj', 'draw', r'se fue el trazo de practica', -1.5, 3.0),
    ('5.3b', 'Draw - dibujando', 'draw', r'se fue el trazo de practica', 6.0, 18.0),
    ('5.15', 'Draw - ultimos 10 s del reloj', 'draw', r'se acabo el tiempo', -11.0, 1.5),
    ('5.16', 'Draw - se acaba el tiempo', 'draw', r'se acabo el tiempo', -0.8, 3.0),
    ('5.17', 'Draw - se guarda y se presenta el dibujo', 'draw', r'el dibujo se guarda y se presenta', -0.8, 15.5),
    ('5.18', 'Draw - el dibujo se corre a la derecha', 'draw', r'el dibujo se corre a la derecha', -0.8, 4.0),
    ('5.19', 'Draw - se van la paleta y el pincel', 'draw', r'se fueron los mandos', -2.5, 2.5),
]


def eventos(tag):
    """[(cuadro absoluto, mensaje)] del log de la pasada. El contador del log va modulo 1000 y puede pasar mas de un minuto
    sin lineas (el dibujo sintetico): cada vuelta se decide con el reloj del log (cuadros ~ segundos x ritmo de la pasada)."""
    import datetime
    d = os.path.join(SP, 'rec_' + tag)
    total = len([x for x in os.listdir(d) if x.endswith('.png')])
    rows = []
    for l in open(os.path.join(SP, 'rec_%s.log' % tag), encoding='utf-8', errors='ignore'):
        m = re.match(r'\[(\d{4})\.(\d\d)\.(\d\d)-(\d\d)\.(\d\d)\.(\d\d):(\d{3})\]\[\s*(\d+)\]', l)
        if not m:
            continue
        g = [int(x) for x in m.groups()]
        t = datetime.datetime(g[0], g[1], g[2], g[3], g[4], g[5], g[6] * 1000).timestamp()
        msg = l.split('LogBlueprintUserMessages: ')[-1].strip() if 'LogBlueprintUserMessages' in l else None
        rows.append((t, g[7], msg))
    if not rows:
        return []
    rate = total / max(rows[-1][0] - rows[0][0], 1.0)   # cuadros por segundo de reloj en esta pasada
    out, prev_abs, prev_t = [], rows[0][1], rows[0][0]
    for t, f, msg in rows:
        exp = prev_abs + (t - prev_t) * rate
        best = None
        for k in range(0, 40):
            cand = (prev_abs // 1000 + k) * 1000 + f
            if cand < prev_abs:
                continue
            if best is None or abs(cand - exp) < abs(best - exp):
                best = cand
        prev_abs, prev_t = best, t
        if msg is not None:
            out.append((best, msg))
    return out


def main():
    os.makedirs(DEST, exist_ok=True)
    cache, hechos, faltan = {}, [], []
    for num, nombre, tag, rx, a, b in CORTES:
        d = os.path.join(SP, 'rec_' + tag)
        if not os.path.isdir(d):
            faltan.append((num, nombre, 'sin pasada ' + tag)); continue
        if tag not in cache:
            cache[tag] = eventos(tag)
        n_frames = len([x for x in os.listdir(d) if x.endswith('.png')])
        ev = [f for f, msg in cache[tag] if re.search(rx, msg)]
        if not ev:
            faltan.append((num, nombre, 'no paso en la grabacion')); continue
        f0 = max(0, ev[0] + int(round(a * FPS)))
        f1 = min(n_frames - 1, ev[0] + int(round(b * FPS)))
        if f1 - f0 < 5:
            faltan.append((num, nombre, 'fuera de la grabacion')); continue
        lead = (ev[0] - f0) / FPS
        out = os.path.join(DEST, '%s %s.mp4' % (num, nombre))
        titulo = ('%s  %s' % (num, nombre)).replace(':', '\\:').replace("'", '')
        vf = ("scale=640:-2,"
              "drawbox=x=0:y=0:w=iw:h=30:color=black@0.55:t=fill,"
              "drawtext=fontfile='%s':text='%s':x=10:y=7:fontsize=17:fontcolor=white,"
              "drawtext=fontfile='%s':text='%%{pts\\:hms}':x=w-tw-10:y=h-th-10:fontsize=18:fontcolor=white:box=1:boxcolor=black@0.5,"
              "drawtext=fontfile='%s':text='EVENTO':x=10:y=h-th-10:fontsize=22:fontcolor=yellow:box=1:boxcolor=black@0.6:"
              "enable='between(t\\,%.3f\\,%.3f)'") % (FONT, titulo, FONT, FONT, lead, lead + 0.8)
        cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-framerate', str(FPS), '-start_number', str(f0),
               '-i', os.path.join(d, 'MovieFrame%05d.png'), '-frames:v', str(f1 - f0 + 1), '-vf', vf,
               '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '30', '-pix_fmt', 'yuv420p', out]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            faltan.append((num, nombre, 'ffmpeg: ' + r.stderr[-200:])); continue
        hechos.append((num, nombre, (f1 - f0 + 1) / FPS, lead))
    for h in hechos:
        print('OK  %-14s %-75s %5.1f s  (evento a los %.1f s)' % h)
    for f in faltan:
        print('--  %-14s %-75s %s' % f)


if __name__ == '__main__':
    main()
