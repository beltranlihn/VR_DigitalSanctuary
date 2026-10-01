import json
import math
# ghost_synth.py (v2, 2026-10-01) - TOMA SINTETICA para probar el reproductor SIN visor: la vista previa del editor y el
# PIE con bAutoPlay. Stride 34 (ver ghost_player.dsl). CUAL elige la toma:
#   'bell'    -> DA_Ghost_Bell: la mano se acerca al timbre (ancla = el timbre) y se queda apoyada.
#   'attract' -> DA_Ghost_Attract: el mando apunta a la esfera (OrbRest 350,120,80), aprieta, la lleva a un slot, suelta y
#                aprieta sobre el SAVE de la mano izquierda (ancla = los ojos).
#   'draw'    -> DA_Ghost_Draw: la punta toca la paleta (sin gatillo) y dibuja una curva con el gatillo (ancla = los ojos).
# RESTAURAR = True deja ESE DA vacio (Frames 0, Data []): una toma de prueba NO puede quedar como grabacion real.
# Se pega ENTERO como `script` de execute_tool_script. Nunca levanta excepcion.
CUAL = 'bell'
RESTAURAR = False
DAS = {'bell': 'DA_Ghost_Bell', 'attract': 'DA_Ghost_Attract', 'draw': 'DA_Ghost_Draw'}
OT = 'editor_toolset.toolsets.object.ObjectTools.'


def lerp(a, b, t):
    return [a[i] + (b[i] - a[i]) * t for i in range(len(a))]


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def aim_to(src, dst):
    dx, dy, dz = dst[0] - src[0], dst[1] - src[1], dst[2] - src[2]
    yaw = math.degrees(math.atan2(dy, dx))
    pitch = math.degrees(math.atan2(dz, math.hypot(dx, dy)))
    return [pitch, yaw, 0.0]


def pack(gr, rr, gl, rl, ar, al, tr, tl, head, arl, all_):
    return gr + rr + gl + rl + ar + al + [tr, tl, 0.0, 0.0] + head + arl + all_


def f_bell(t):
    # ancla = el timbre (x se aleja del usuario): la mano viene de cerca del usuario y se apoya arriba del timbre
    k = ease(t / 0.6)
    g = lerp([-35.0, 12.0, 18.0], [-4.0, 0.0, 4.0], k)
    r = [-30.0 + 10.0 * k, 0.0, 90.0]
    head = [-48.0, 0.0, 28.0, 0.0, 0.0, 0.0]
    return pack(g, r, [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [r[0] - 40.0, 0.0, 0.0], [0.0, 0.0, 0.0], 0.0, 0.0, head, g, [0.0, 0.0, 0.0])


ORB = [350.0, 120.0, 80.0]
SLOT = [99.0, -11.0, -40.0]
SAVE_L = [32.0, -20.0, -34.0]


def f_attract(t):
    gl = SAVE_L
    rl = [-10.0, 20.0, -60.0]
    if t < 0.15:                                  # muestra el gatillo de costado
        g = [38.0, 16.0, -30.0]
        a = aim_to(g, [g[0] + 40.0, g[1] + 90.0, g[2] - 10.0])   # de costado, lejos de la esfera: no la agarra
        tr = 1.0 if 0.05 < t < 0.1 else 0.0
    elif t < 0.55:                                # apunta, agarra y arrastra al slot
        k = ease((t - 0.25) / 0.3)
        g = lerp([38.0, 16.0, -30.0], [55.0, 0.0, -32.0], k)
        dst = lerp(ORB, SLOT, k)
        a = aim_to(g, dst)
        tr = 1.0 if t > 0.2 else 0.0
    elif t < 0.75:                                # suelta y gira hacia la mano izquierda
        k = ease((t - 0.55) / 0.2)
        g = lerp([55.0, 0.0, -32.0], [44.0, 6.0, -26.0], k)
        a = aim_to(g, lerp(SLOT, SAVE_L, k))
        tr = 0.0
    else:                                         # aprieta sobre el SAVE
        g = [44.0, 6.0, -26.0]
        a = aim_to(g, SAVE_L)
        tr = 1.0 if t > 0.82 else 0.0
    r = [a[0] - 30.0, a[1], 0.0]
    return pack(g, r, gl, rl, a, [0.0, 0.0, 0.0], tr, 0.0, [0.0] * 6, [g[0] + 3.0, g[1], g[2] + 1.0], gl)


def f_draw(t):
    gl = [34.0, -22.0, -36.0]
    rl = [10.0, 30.0, -50.0]
    if t < 0.3:                                   # la punta va a la paleta (sin gatillo)
        k = ease(t / 0.3)
        g = lerp([40.0, 15.0, -30.0], [36.0, -14.0, -30.0], k)
        tr = 0.0
    else:                                         # dibuja una curva con el gatillo
        k = (t - 0.35) / 0.5
        g = [48.0 + 6.0 * math.sin(k * 3.14), -10.0 + 30.0 * max(0.0, min(1.0, k)), -18.0 + 12.0 * math.sin(k * 6.28)]
        tr = 1.0 if 0.35 < t < 0.85 else 0.0
    r = [-20.0, -10.0, 0.0]
    return pack(g, r, gl, rl, [-35.0, -10.0, 0.0], [0.0, 0.0, 0.0], tr, 0.0, [0.0] * 6, [g[0] + 3.0, g[1], g[2] + 1.0], gl)


def run():
    try:
        da = '/Game/SoulCharger/Mechanics/Ghost/Takes/' + DAS[CUAL] + '.' + DAS[CUAL]
        if RESTAURAR:
            vals = {'Frames': 0, 'Data': [], 'Note': ''}
        else:
            fn = {'bell': f_bell, 'attract': f_attract, 'draw': f_draw}[CUAL]
            n = 120
            data = []
            for i in range(n):
                fr = fn(i / float(n - 1))
                if len(fr) != 34:
                    return {'err': 'cuadro de %d floats' % len(fr)}
                data += fr
            vals = {'Frames': n, 'Hz': 30.0, 'Stride': 34, 'Data': data, 'Note': 'SINTETICA de prueba: restaurar'}
        execute_tool(OT + 'set_properties', json.dumps({'instance': {'refPath': da}, 'values': json.dumps(vals)}))
        v = execute_tool(OT + 'get_properties', json.dumps({'instance': {'refPath': da}, 'properties': ['Frames', 'Stride', 'Note']}))
        return {'cual': CUAL, 'restaurar': RESTAURAR, 'da': str(v)[:200]}
    except BaseException as e:
        return {'err': str(e)[:300]}
