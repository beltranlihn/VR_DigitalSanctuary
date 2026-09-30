import json
import math
# ghost_synth.py - TOMA SINTETICA para probar el reproductor sin visor (TURNO.md §5). Escribe en un DA un arco del mando
# derecho (3 s a 30 Hz) con dos pulsos de gatillo. RESTAURAR = True deja el DA vacio otra vez (Frames 0, Data []): la
# toma de prueba NO puede quedar como grabacion real. Se pega ENTERO como `script` de execute_tool_script.
RESTAURAR = False
DA = '/Game/SoulCharger/Mechanics/Ghost/Takes/DA_Ghost_Bell.DA_Ghost_Bell'
OT = 'editor_toolset.toolsets.object.ObjectTools.'


def frame(i, n):
    t = i / float(n - 1)
    a = math.sin(t * math.pi)                       # sube y baja
    x, y, z = 42.0 + 6.0 * a, -18.0 + 36.0 * t, -32.0 + 10.0 * a
    pitch, yaw, roll = -25.0 + 15.0 * a, -20.0 + 40.0 * t, 10.0 * math.sin(t * 6.28)
    trig = 1.0 if (0.33 < t < 0.43) or (0.66 < t < 0.76) else 0.0
    r = [x, y, z, pitch, yaw, roll]                 # grip R
    l = [38.0, -22.0, -36.0, -20.0, 15.0, -60.0]    # grip L (quieto)
    aim = [pitch - 40.0, yaw, roll, -60.0, 15.0, -60.0]
    btn = [trig, 0.0, 0.0, 0.0]
    head = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    return r + l + aim + btn + head


def run():
    try:
        if RESTAURAR:
            vals = {'Frames': 0, 'Data': [], 'Note': ''}
        else:
            n = 90
            data = []
            for i in range(n):
                data += frame(i, n)
            vals = {'Frames': n, 'Hz': 30.0, 'Stride': 28, 'Data': data, 'Note': 'SINTETICA de prueba: restaurar'}
        execute_tool(OT + 'set_properties', json.dumps({'instance': {'refPath': DA}, 'values': json.dumps(vals)}))
        v = execute_tool(OT + 'get_properties', json.dumps({'instance': {'refPath': DA}, 'properties': ['Frames', 'Note']}))
        return {'restaurar': RESTAURAR, 'da': str(v)[:200]}
    except BaseException as e:
        return {'err': str(e)[:300]}
