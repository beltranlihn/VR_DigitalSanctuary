import json
# ambience_a4.py - escribe EventGraph (borrando antes los 3 eventos fantasma sin conectar) y ArchSet (vacio) de BP_HallAmbience_SC; compila.
BT = 'editor_toolset.toolsets.blueprint.BlueprintTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
BP = '/Game/SoulCharger/Mechanics/Hall/BP_HallAmbience_SC.BP_HallAmbience_SC'
DIR = 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/Hall/dsl_txt/'
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
        LOG.append(name.split('.')[-1] + ' :: ' + str(e)[:500])
        return False, None
def rp(x):
    return x['refPath'] if isinstance(x, dict) and 'refPath' in x else str(x)
def run():
  try:
    out = {}
    EG = {'refPath': BP + ':EventGraph'}
    ok, ns = T(BT + 'find_nodes', {'graph': EG, 'title': ''})
    refs = [rp(n) for n in (ns or [])]
    if len(refs) == 3 and all('K2Node_Event_' in r for r in refs):
        for r in refs:
            T(BT + 'delete_node', {'node': {'refPath': r}})
    ok, ns = T(BT + 'find_nodes', {'graph': EG, 'title': ''})
    if len(ns or []) == 0:
        ok, code = T(AS + 'read_file', {'file_path': DIR + 'AmbEventGraph.txt'})
        out['eg'] = T(BT + 'write_graph_dsl', {'graph': EG, 'code': str(code)})[0] if ok else 'no lei'
    else:
        out['eg'] = 'EventGraph no vacio (' + str(len(ns)) + '): no escribo'
    AG = {'refPath': BP + ':ArchSet'}
    ok, ns = T(BT + 'find_nodes', {'graph': AG, 'title': ''})
    if len(ns or []) == 1:
        ok, code = T(AS + 'read_file', {'file_path': DIR + 'AmbArchSet.txt'})
        out['arch'] = T(BT + 'write_graph_dsl', {'graph': AG, 'code': str(code)})[0] if ok else 'no lei'
    else:
        out['arch'] = 'ArchSet no vacio (' + str(len(ns or [])) + ')'
    ok, r = T(BT + 'compile_blueprint', {'blueprint': {'refPath': BP}})
    out['compile'] = str(r)[:300]
    ok, a = T(BT + 'read_graph_dsl', {'graph': AG})
    out['arch_read'] = str(a)[:1200]
    ok, ns = T(BT + 'find_nodes', {'graph': EG, 'title': ''})
    out['eg_nodos'] = len(ns or [])
    out['log'] = LOG[:10]
    return out
  except BaseException as e:
    return {'err': 'run :: ' + str(e)[:300], 'log': LOG}
