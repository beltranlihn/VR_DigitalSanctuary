import json
# turno4_ambience.py - BP_HallAmbience_SC: EventGraph reescrito EN VACIO (borra todos sus nodos y escribe AmbEventGraph_v2):
# el "snap" de arranque (onda y motas) vale también en el paso de arranque del ENSAYO (bTestIntro y Step == TestFromStep).
# Requiere TestFromStep YA en BP_HallDirector_SC. Nada estructural. Sin `result = run()`.
BT = 'editor_toolset.toolsets.blueprint.BlueprintTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
BP = '/Game/SoulCharger/Mechanics/Hall/BP_HallAmbience_SC.BP_HallAmbience_SC'
F = 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/Hall/dsl_txt/AmbEventGraph_v2.txt'
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
        LOG.append(name.split('.')[-1] + ' :: ' + str(e)[:400])
        return False, None
def rp(x):
    return x['refPath'] if isinstance(x, dict) and 'refPath' in x else str(x)
def run():
  try:
    out = {}
    ok, code = T(AS + 'read_file', {'file_path': F})
    code = str(code) if ok else ''
    if not code.startswith('(event EventBeginPlay') or 'GetTestfromStep' not in code:
        return {'err': 'no pude leer el dsl: no toco', 'log': LOG}
    EG = {'refPath': BP + ':EventGraph'}
    ok, ns = T(BT + 'find_nodes', {'graph': EG, 'title': ''})
    refs = [rp(n) for n in (ns or [])]
    out['antes'] = len(refs)
    for r in refs:
        T(BT + 'delete_node', {'node': {'refPath': r}})
    ok, left = T(BT + 'find_nodes', {'graph': EG, 'title': ''})
    if len(left or []) != 0:
        out['err'] = 'quedaron nodos: no escribo'
        out['log'] = LOG[:6]
        return out
    out['escrito'] = T(BT + 'write_graph_dsl', {'graph': EG, 'code': code})[0]
    ok, now = T(BT + 'find_nodes', {'graph': EG, 'title': ''})
    out['despues'] = len(now or [])
    T(BT + 'compile_blueprint', {'blueprint': {'refPath': BP}})
    out['log'] = LOG[:8]
    return out
  except BaseException as e:
    return {'err': 'run :: ' + str(e)[:300], 'log': LOG}
