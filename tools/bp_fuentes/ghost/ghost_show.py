import json
import math
# ghost_show.py (2026-10-01) - "mostrar al instante" despues de grabar (pedido de Beltran): con el PIE DETENIDO, refresca la
# vista previa del fantasma en el EDITOR (reescribir PreviewTime re-corre su Construction Script, que lee el DA) y saca
# capturas del viewport desde los OJOS del usuario sentado mirando la estacion, en varios PreviewTime.
# Cada captura se guarda como base64 en Saved/ClaudeScripts/ghost/cap_<label>_<t>.txt; afuera: python ghost_png.py.
# La primera captura se descarta (las capturas pueden salir rancias). Deja PreviewTime en DEJAR. Se pega ENTERO.
LABEL = 'Ghost_BELL'
TIEMPOS = [0.0, 0.35, 0.7, 1.0]
DEJAR = 0.5
SC = 'editor_toolset.toolsets.scene.SceneTools.'
AT = 'editor_toolset.toolsets.actor.ActorTools.'
OT = 'editor_toolset.toolsets.object.ObjectTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
EA = 'EditorToolset.EditorAppToolset.'
OUT = 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/ghost/'
LOG = []


def T(name, payload):
    try:
        r = execute_tool(name, json.dumps(payload))
        v = r['returnValue'] if isinstance(r, dict) and ('returnValue' in r) else r
        return True, v
    except BaseException as e:
        LOG.append(name.split('.')[-1] + ' :: ' + str(e)[:160])
        return False, None


def refp(x):
    return str(x['refPath'] if isinstance(x, dict) and ('refPath' in x) else x)


def by_label(want):
    ok, v = T(SC + 'find_actors', {'name': '', 'tag': '', 'collision_channels': []})
    for a in (v or []):
        r = refp(a)
        ok, l = T(AT + 'get_label', {'actor': {'refPath': r}})
        if ok and (want in str(l)):
            return r
    return None


def loc_yaw(actor):
    ok, xf = T(AT + 'get_actor_transform', {'actor': {'refPath': actor}})
    return (xf['location']['x'], xf['location']['y'], xf['location']['z']), xf['rotation']['yaw']


def look(cam, tgt):
    dx, dy, dz = tgt[0] - cam[0], tgt[1] - cam[1], tgt[2] - cam[2]
    return math.degrees(math.atan2(dz, math.hypot(dx, dy))), math.degrees(math.atan2(dy, dx))


def cap(name, cam, rot):
    xf = {'location': {'x': cam[0], 'y': cam[1], 'z': cam[2]}, 'rotation': {'pitch': rot[0], 'yaw': rot[1], 'roll': 0.0},
          'scale': {'x': 1, 'y': 1, 'z': 1}}
    ok, r = T(EA + 'CaptureViewport', {'captureTransform': xf, 'annotations': [], 'bShowUI': False})
    s = json.dumps(r) if not isinstance(r, str) else r
    T(AS + 'write_file', {'file_path': OUT + 'cap_' + name + '.txt', 'content': s})
    return len(s)


def run():
    try:
        return run2()
    except BaseException as e:
        return {'err': 'run :: ' + str(e)[:300], 'log': LOG}


def run2():
    g = by_label(LABEL)
    ps = by_label('PlayerStart')
    if not g or not ps:
        return {'err': 'no encontre %s o el PlayerStart' % LABEL}
    (pl, yaw) = loc_yaw(ps)
    eyes = (pl[0], pl[1], pl[2] + 120.0)
    gl, gyaw = loc_yaw(g)
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))

    def w(x, y, z):
        return (eyes[0] + x * c - y * s, eyes[1] + x * s + y * c, eyes[2] + z)
    head = abs(gl[0] - eyes[0]) + abs(gl[1] - eyes[1]) + abs(gl[2] - eyes[2]) < 2.0
    # de cabeza: un poco atras y a la derecha de los ojos, mirando al pecho; en el nivel: desde los ojos a la estacion
    cam = w(-25.0, 30.0, 8.0) if head else w(-8.0, 6.0, 4.0)
    tgt = w(35.0, 0.0, -35.0) if head else gl
    rot = look(cam, tgt)
    out = {'fantasma': g, 'de_cabeza': head, 'camara': [round(v, 1) for v in cam], 'rot': [round(v, 1) for v in rot]}
    cap('descartar', cam, rot)
    sizes = {}
    for t in TIEMPOS:
        T(OT + 'set_properties', {'instance': {'refPath': g}, 'values': json.dumps({'PreviewTime': t})})
        sizes['%s_%03d' % (LABEL, int(t * 100))] = cap('%s_%03d' % (LABEL, int(t * 100)), cam, rot)
    T(OT + 'set_properties', {'instance': {'refPath': g}, 'values': json.dumps({'PreviewTime': DEJAR})})
    out['capturas'] = sizes
    out['log'] = LOG[:10]
    return out
