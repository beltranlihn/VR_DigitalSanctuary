import json
# turno4_graphs.py - BP_HallDirector_SC: reescribe EN VACIO HallEnterIntro, HallEnterReturn y HallEnterExit con los tiempos agiles (dsl_v2 → dsl_txt).
# entrada y escribe el .dsl de dsl_txt/). Nada estructural. Canario. Sin `result = run()`. Compilar aparte, sin PIE.
SC = 'editor_toolset.toolsets.scene.SceneTools.'
BT = 'editor_toolset.toolsets.blueprint.BlueprintTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
BP = '/Game/SoulCharger/Mechanics/Hall/BP_HallDirector_SC.BP_HallDirector_SC'
DIR = 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/Hall/dsl_txt/'
GRAPHS = ['HallEnterIntro', 'HallEnterReturn', 'HallEnterExit', 'HallSpawnBell', 'HallTickTouch', 'HallTickLead']
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
def n_act():
    ok, a = T(SC + 'find_actors', {'name': '', 'tag': '', 'collision_channels': []})
    return len(a or [])
def run():
  try:
    out = {'canario_antes': n_act()}
    for g in GRAPHS:
        ok, code = T(AS + 'read_file', {'file_path': DIR + g + '.txt'})
        code = str(code) if ok else ''
        if not code.startswith('(fn ' + g):
            out[g] = 'no pude leer el dsl: no toco'
            continue
        G = {'refPath': BP + ':' + g}
        ok, ns = T(BT + 'find_nodes', {'graph': G, 'title': ''})
        refs = [rp(n) for n in (ns or [])]
        ent = [r for r in refs if 'K2Node_FunctionEntry' in r]
        if len(ent) != 1:
            out[g] = 'entrada rara: ' + str(ent)[:200]
            continue
        dele = 0
        for r in refs:
            if r not in ent:
                if T(BT + 'delete_node', {'node': {'refPath': r}})[0]:
                    dele += 1
        ok, left = T(BT + 'find_nodes', {'graph': G, 'title': ''})
        nl = len(left or [])
        if nl != 1:
            out[g] = 'quedaron ' + str(nl) + ' nodos: no escribo'
            continue
        ok, r = T(BT + 'write_graph_dsl', {'graph': G, 'code': code})
        ok2, now = T(BT + 'find_nodes', {'graph': G, 'title': ''})
        out[g] = {'antes': len(refs), 'borrados': dele, 'escrito': ok, 'despues': len(now or []), 'r': str(r)[:200]}
    out['canario_despues'] = n_act()
    out['log'] = LOG[:10]
    return out
  except BaseException as e:
    return {'err': 'run :: ' + str(e)[:300], 'log': LOG}
