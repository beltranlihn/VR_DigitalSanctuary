# debugstart_build.py (2026-10-01 ~00:20) - arranque de debug de la Obra (DebugStart / DebugSoul). IDEMPOTENTE en vars y grafos nuevos.
# Fuente: debugstart.json. No toca StartObra ni la rama bDebugEnding. Reescribe SimCut y StartDisc (fuente propia: turnB2/turnA2).
import json
BT = 'editor_toolset.toolsets.blueprint.BlueprintTools.'
OT = 'editor_toolset.toolsets.object.ObjectTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
SC = 'editor_toolset.toolsets.scene.SceneTools.'
BPP = '/Game/SoulCharger/Obra/BP_Obra_SC'
BP = BPP + '.BP_Obra_SC'
DIR = 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/Obra/'
ERRS = []
LOG = []
def T(n, p):
    try:
        return True, execute_tool(n, json.dumps(p))['returnValue']
    except BaseException as e:
        ERRS.append(n.split('.')[-1] + ' :: ' + str(e)[:300]); return False, None
def rp(x):
    return x['refPath'] if isinstance(x, dict) and 'refPath' in x else str(x)
def count():
    ok, a = T(SC + 'find_actors', {'name': '', 'tag': '', 'collision_channels': []})
    return len(a or [])
def clear(G):
    ok, ns = T(BT + 'find_nodes', {'graph': G, 'title': ''})
    k = 0
    for n in (ns or []):
        r = rp(n)
        if 'FunctionEntry' in r:
            continue
        if T(BT + 'delete_node', {'node': {'refPath': r}})[0]:
            k += 1
    return k
def nnodes(G):
    ok, ns = T(BT + 'find_nodes', {'graph': G, 'title': ''})
    return len(ns or [])
def run():
    out = {}
    try:
        ok, pie = T('EditorToolset.EditorAppToolset.IsPIERunning', {})
        if pie:
            return {'err': 'PIE corriendo: no compilo'}
        ok, cur = T(SC + 'get_current_level', {})
        out['nivel'] = str(cur)
        if 'Obra' in str(cur):
            return {'err': 'la Obra esta abierta: abrir otro nivel antes (gotcha 402)'}
        out['actores_antes'] = count()
        ok, s = T(AS + 'read_file', {'file_path': DIR + 'debugstart.json'})
        src = s if isinstance(s, dict) else json.loads(s)
        B = {'refPath': BP}
        ok, vs = T(BT + 'list_variables', {'blueprint': B})
        ya = str(vs)
        for n, t, ed in [('DebugStart', 'int', True), ('DebugSoul', 'int', True), ('DbgK', 'int', False), ('DbgS', 'int', False)]:
            if ("'" + n + "'") in ya:
                continue
            if T(BT + 'add_variable', {'blueprint': B, 'name': n, 'type_name': t})[0]:
                LOG.append('var ' + n)
            if ed:
                T(BT + 'set_variable_instance_editable', {'blueprint': B, 'variable_name': n, 'instance_editable': True})
                T(BT + 'set_variable_category', {'blueprint': B, 'variable_name': n, 'category': 'Debug'})
        T(BT + 'compile_blueprint', {'blueprint': B})
        ok, cdo = T(BT + 'get_default_object', {'blueprint': B})
        T(OT + 'set_properties', {'instance': {'refPath': rp(cdo)}, 'values': json.dumps({'DebugStart': -1, 'DebugSoul': 0, 'DbgK': -1, 'DbgS': 0})})
        ok, v = T(OT + 'get_properties', {'instance': {'refPath': rp(cdo)}, 'properties': ['DebugStart', 'DebugSoul', 'DbgK', 'DbgS']})
        out['cdo'] = str(v)
        ok, gs = T(BT + 'list_graphs', {'blueprint': B})
        gstr = str(gs)
        for g, params in [('ObraDbgPrep', [('K', 'int')]), ('ObraDbgFF', []), ('ObraDbgBoot', [])]:
            G = {'refPath': BP + ':' + g}
            if (':' + g + "'") not in gstr:
                T(BT + 'add_function_graph', {'blueprint': B, 'graph_name': g})
                for pn, pt in params:
                    T(BT + 'add_function_param', {'graph': G, 'param_name': pn, 'param_type': pt, 'input_param': True})
            if nnodes(G) <= 1:
                out['w_' + g] = T(BT + 'write_graph_dsl', {'graph': G, 'code': src[g]})[0]
            else:
                out['w_' + g] = 'ya tenia nodos: no escribo'
        for g in ['SimCut', 'StartDisc']:
            G = {'refPath': BP + ':' + g}
            k = clear(G)
            out['w_' + g] = [k, T(BT + 'write_graph_dsl', {'graph': G, 'code': src[g]})[0]]
        ok, r = T(BT + 'compile_blueprint', {'blueprint': B})
        out['compile'] = str(r)[:300]
        txt = ''
        tids = {}
        for g in ['ObraDbgPrep', 'ObraDbgFF', 'ObraDbgBoot', 'SimCut', 'StartDisc']:
            G = {'refPath': BP + ':' + g}
            ok, d = T(BT + 'read_graph_dsl', {'graph': G})
            txt += '\n===== ' + g + ' =====\n' + str(d)
            ok, ns = T(BT + 'find_nodes', {'graph': G, 'title': ''})
            ok, inf = T(BT + 'get_node_infos', {'nodes': ns or []})
            tids[g] = sorted(set([i['type_id'] for i in (inf or []) if i['type_id'].startswith('|') or 'Class|' in i['type_id'] or 'CallFunction' in i['type_id']]))
        T(AS + 'write_file', {'file_path': DIR + 'debugstart_read.txt', 'content': txt})
        out['tids'] = tids
        out['save'] = T(AS + 'save_assets', {'asset_paths': [BPP]})[0]
        out['actores_despues'] = count()
    except BaseException as e:
        ERRS.append('run :: ' + str(e)[:300])
    out['log'] = LOG
    out['errs'] = ERRS[:12]
    return out
