import json
# ensayo_export.py - Unreal -> web. Lee de los 5 niveles de test el PlayerStart, los TargetPoints sc<K>_* y los valores del
# BP_StageRunner_SC, y escribe Saved/ClaudeScripts/Obra/ensayo_export.json (posiciones en cm relativas al PlayerStart:
# fwd / side (derecha +) / up (sobre los ojos = PlayerStart.z + EyeRef)). Solo lectura. Vuelve a abrir la Obra al final.
SC = 'editor_toolset.toolsets.scene.SceneTools.'
AT = 'editor_toolset.toolsets.actor.ActorTools.'
OT = 'editor_toolset.toolsets.object.ObjectTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
OUT = 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/Obra/ensayo_export.json'
LVS = ['/Game/Test_Entering', '/Game/Test_Heart', '/Game/Test_Fluid', '/Game/Test_Sequencer', '/Game/NeuralCanvas/Maps/L_TBTest_SC']
LOG = []
def T(name, payload):
    try:
        return True, execute_tool(name, json.dumps(payload))['returnValue']
    except BaseException as e:
        LOG.append(name.split('.')[-1] + ' :: ' + str(e)[:200])
        return False, None
def rp(x):
    return x['refPath'] if isinstance(x, dict) and 'refPath' in x else str(x)
def xfm(ref):
    ok, t = T(AT + 'get_actor_transform', {'actor': {'refPath': ref}})
    try:
        l = t['location'] if 'location' in t else t['translation']
        r = t.get('rotation', {})
        s = t.get('scale', t.get('scale3D', {'x': 1}))
        return [float(l['x']), float(l['y']), float(l['z'])], float(r.get('yaw', 0.0)), float(s.get('x', 1.0))
    except BaseException:
        LOG.append('xf raro ' + str(t)[:160])
        return None, 0.0, 1.0
def first(tag):
    ok, a = T(SC + 'find_actors', {'name': '', 'tag': tag, 'collision_channels': []})
    return rp(a[0]) if a else None
def run():
  try:
    res = {'stages': []}
    for K, lv in enumerate(LVS):
        T(SC + 'load_level', {'level_path': lv})
        ok, ps = T(SC + 'find_actors', {'name': 'PlayerStart', 'tag': '', 'collision_channels': []})
        P, yaw, _ = xfm(rp(ps[0])) if ps else ([0, 0, 0], 0.0, 1.0)
        ok, rn = T(SC + 'find_actors', {'name': 'StageRunner', 'tag': '', 'collision_channels': []})
        vals = {}
        if rn:
            ok, g = T(OT + 'get_properties', {'instance': {'refPath': rp(rn[0])}, 'properties': ['AlmaTime', 'InstrTime', 'OutroTime', 'ChargeTime', 'TimeoutS', 'EyeRef', 'CTop', 'CHor']})
            vals = g if isinstance(g, dict) else json.loads(g)
        eye = float(vals.get('EyeRef', 120.0))
        # coseno/seno del yaw del PlayerStart por serie (sin math en el sandbox)
        a = yaw * 3.141592653589793 / 180.0
        c = 1.0 - a * a / 2 + a ** 4 / 24 - a ** 6 / 720 + a ** 8 / 40320
        s = a - a ** 3 / 6 + a ** 5 / 120 - a ** 7 / 5040 + a ** 9 / 362880
        pts = {}
        for nm in ['alma_in', 'alma_side', 'charge', 'title']:
            r = first('sc%d_%s' % (K, nm))
            if not r:
                continue
            L, ty, sc = xfm(r)
            if L is None:
                continue
            dx, dy, dz = L[0] - P[0], L[1] - P[1], L[2] - P[2]
            pts[nm] = {'fwd': round(dx * c + dy * s, 1), 'side': round(-dx * s + dy * c, 1), 'up': round(dz - eye, 1), 'yaw': round(ty - yaw, 1), 'scale': round(sc, 3)}
        res['stages'].append({'k': K, 'level': lv, 'playerStart': [round(v, 1) for v in P], 'yaw': yaw, 'points': pts, 'values': vals})
    T(SC + 'load_level', {'level_path': '/Game/SoulCharger/Obra/L_SoulCharger_Obra'})
    T(AS + 'write_file', {'file_path': OUT, 'content': json.dumps(res, indent=1)})
    return {'ok': len(res['stages']), 'first': str(res['stages'][0])[:500], 'log': LOG[:10]}
  except BaseException as e:
    return {'err': str(e)[:300], 'log': LOG}
