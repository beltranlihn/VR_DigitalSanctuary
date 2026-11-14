import json
# hall_apply_C.py - defaults del CDO de BP_HallDirector_SC + plantillas de componentes (flechas y titulos), CON RELECTURA.
# Correr DESPUES de A + B + compile_blueprint, y ANTES de colocar el actor. Sin `result = run()`. Idempotente.
# STOP_Z = z del PlayerStart de Test_Hall RELATIVA al origen del hall (lo leo al empezar el turno y lo pego aca).
STOP_Z = 76.97
TITLE_Z = 70.0
OT = 'editor_toolset.toolsets.object.ObjectTools.'
AT = 'editor_toolset.toolsets.actor.ActorTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
BT = 'editor_toolset.toolsets.blueprint.BlueprintTools.'
PLAN = 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/Hall/hall_director_plan.json'
VO = ['VO_01a', 'VO_01b', 'VO_01c', 'VO_01d', 'VO_01h', 'VO_02', 'VO_03', 'VO_03h', 'VO_04', 'VO_04b', 'VO_05',
      'VO_06a', 'VO_06b', 'VO_06c', 'VO_06d', 'VO_06e', 'VO_06f', 'VO_06g', 'VO_07', 'VO_34a', 'VO_35a']
LOG = []
def T(name, payload):
    try:
        v = execute_tool(name, json.dumps(payload))['returnValue']
        try:
            v = json.loads(json.dumps(v))
        except BaseException:
            pass
        return True, v
    except BaseException as e:
        LOG.append(name.split('.')[-1] + ' :: ' + str(e)[:220])
        return False, None
def S(ref, vals):
    return T(OT + 'set_properties', {'instance': {'refPath': ref}, 'values': json.dumps(vals)})[0]
def G(ref, props):
    ok, v = T(OT + 'get_properties', {'instance': {'refPath': ref}, 'properties': props})
    if not ok or v is None:
        return None
    try:
        return json.loads(v) if isinstance(v, str) else v
    except BaseException:
        return None
def run():
  try:
    ok, txt = T(AS + 'read_file', {'file_path': PLAN})
    if not ok:
        return {'err': 'no pude leer el plan', 'log': LOG}
    plan = json.loads(txt)
    BPP = plan['blueprint']
    NAME = BPP.rsplit('/', 1)[1]
    CDO = BPP + '.Default__' + NAME + '_C'
    out = {}
    esc, malas = 0, []
    for v in plan['vars']:
        if 'default' not in v:
            continue
        d = v['default']
        if v['type'] == 'LinearColor':
            val = {'r': d[0], 'g': d[1], 'b': d[2], 'a': d[3]}
        else:
            val = d
        if S(CDO, {v['name']: val}):
            esc += 1
        else:
            malas.append(v['name'])
    vo = ['/Game/SoulCharger/Mechanics/Hall/Audio/%s.%s' % (n, n) for n in VO]
    out['vo_ok'] = S(CDO, {'VO': vo})
    lv = G(CDO, ['VO'])
    out['vo_leido'] = len(lv['VO']) if lv and 'VO' in lv and lv['VO'] else 0
    out['cdo'] = {'escritas': esc, 'fallaron': malas}
    ok, comps = T(AT + 'get_components', {'actor': {'refPath': CDO}})
    cref = {}
    for c in (comps or []):
        rp = c['refPath'] if isinstance(c, dict) and 'refPath' in c else str(c)
        cref[rp.split('.')[-1].split(':')[-1].replace('_GEN_VARIABLE', '')] = rp
    out['componentes'] = sorted(cref.keys())
    fl = []
    for a in plan['arrows']:
        r = cref[a['name']] if a['name'] in cref else None
        if not r:
            fl.append('sin ' + a['name'])
            continue
        S(r, {'relativeLocation': '(X=%.3f,Y=%.3f,Z=%.3f)' % (a['loc'][0], a['loc'][1], STOP_Z)})
        S(r, {'relativeRotation': '(Pitch=0.000000,Yaw=%.3f,Roll=0.000000)' % a['yaw']})
        S(r, {'ArrowSize': 2.0})
        g = G(r, ['relativeLocation', 'relativeRotation'])
        fl.append(a['name'] + ' ' + str(g)[:120])
    out['flechas'] = fl
    tl = []
    for t in plan['titles']:
        r = cref[t['name']] if t['name'] in cref else None
        if not r:
            tl.append('sin ' + t['name'])
            continue
        S(r, {'StaticMesh': '/Engine/BasicShapes/Plane.Plane'})
        S(r, {'OverrideMaterials': [t['mi']]})
        S(r, {'CastShadow': False})
        S(r, {'relativeLocation': '(X=%.3f,Y=%.3f,Z=%.3f)' % (t['loc'][0], t['loc'][1], TITLE_Z)})
        S(r, {'relativeRotation': '(Pitch=%.3f,Yaw=%.3f,Roll=%.3f)' % (t['rot'][0], t['rot'][1], t['rot'][2])})
        S(r, {'relativeScale3D': '(X=%.3f,Y=%.3f,Z=%.3f)' % (t['scale'][0], t['scale'][1], t['scale'][2])})
        g = G(r, ['StaticMesh', 'relativeLocation', 'relativeRotation', 'relativeScale3D'])
        tl.append(t['name'] + ' ' + str(g)[:200])
    out['titulos'] = tl
    out['log'] = LOG[:30]
    return out
  except BaseException as e:
    return {'err': 'run :: ' + str(e)[:300], 'log': LOG}
