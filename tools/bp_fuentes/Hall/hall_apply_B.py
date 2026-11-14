import json
# hall_apply_B.py - parametros de entrada de las funciones de BP_HallDirector_SC (llamada SEPARADA de A: gotcha 304).
# Sin `result = run()` (gotcha 493). Un param que ya existe levanta "Param already exists!" -> T() lo atrapa (gotcha 70).
BT = 'editor_toolset.toolsets.blueprint.BlueprintTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
PLAN = 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/Hall/hall_director_plan.json'
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
def run():
  try:
    ok, txt = T(AS + 'read_file', {'file_path': PLAN})
    if not ok:
        return {'err': 'no pude leer el plan', 'log': LOG}
    plan = json.loads(txt)
    BPP = plan['blueprint']
    NAME = BPP.rsplit('/', 1)[1]
    BPo = {'refPath': BPP + '.' + NAME}
    ok, gs = T(BT + 'list_graphs', {'blueprint': BPo})
    refs = {}
    for g in (gs or []):
        rp = g['refPath'] if isinstance(g, dict) and 'refPath' in g else str(g)
        refs[rp.split(':')[-1].split('.')[-1]] = rp
    hechos = []
    for f in plan['functions']:
        if f['name'] not in refs:
            LOG.append('sin grafo: ' + f['name'])
            continue
        gref = {'refPath': refs[f['name']]}
        for pn, pt in f['params']:
            if pt.startswith('obj:'):
                ok, r = T(BT + 'add_object_function_param', {'graph': gref, 'param_name': pn, 'object_class': {'refPath': pt[4:]}, 'input_param': True})
            else:
                ok, r = T(BT + 'add_function_param', {'graph': gref, 'param_name': pn, 'param_type': pt, 'input_param': True})
            if ok:
                hechos.append(f['name'] + '.' + pn)
    return {'params': len(hechos), 'hechos': hechos, 'log': LOG[:30]}
  except BaseException as e:
    return {'err': 'run :: ' + str(e)[:300], 'log': LOG}
