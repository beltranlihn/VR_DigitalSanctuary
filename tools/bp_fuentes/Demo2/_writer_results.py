PATH = r"C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/Demo2/results_dsl_codes.json"
import json
BT = 'editor_toolset.toolsets.blueprint.BlueprintTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
LOG = []
def T(name, payload):
    try:
        return True, execute_tool(name, json.dumps(payload))['returnValue']
    except BaseException as e:
        LOG.append(name.split('.')[-1] + ' :: ' + str(e)[:400])
        return False, None
def rp(x):
    return x['refPath'] if isinstance(x, dict) and 'refPath' in x else str(x)
def clear(g):
    ok, ns = T(BT + 'find_nodes', {'graph': {'refPath': g}, 'title': ''})
    for n in (ns or []):
        r = rp(n)
        if 'FunctionEntry' not in r:
            T(BT + 'delete_node', {'node': {'refPath': r}})
def run():
    out = {}
    ok, txt = T(AS + 'read_file', {'file_path': PATH})
    d = json.loads(txt if isinstance(txt, str) else txt['content'])
    BP = d['bp']
    wr = {}
    for n in d['order']:
        clear(BP + ':' + n)
        n0 = len(LOG)
        ok, w = T(BT + 'write_graph_dsl', {'graph': {'refPath': BP + ':' + n}, 'code': d['codes'][n]})
        wr[n] = 'ok' if ok else LOG[n0:n0 + 1]
    if d.get('evg'):
        clear(BP + ':EventGraph')
        n0 = len(LOG)
        ok, w = T(BT + 'write_graph_dsl', {'graph': {'refPath': BP + ':EventGraph'}, 'code': d['evg']})
        wr['EventGraph'] = 'ok' if ok else LOG[n0:n0 + 1]
    n0 = len(LOG)
    ok, c = T(BT + 'compile_blueprint', {'blueprint': {'refPath': BP}})
    out['compile'] = str(c)[:1500] if ok else LOG[n0:]
    out['writes'] = wr
    return out
