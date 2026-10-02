import json
BT = 'editor_toolset.toolsets.blueprint.BlueprintTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
OT = 'editor_toolset.toolsets.object.ObjectTools.'
ST = 'editor_toolset.toolsets.scene.SceneTools.'
DUMP = 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/Obra/dump/__TAG___out.json'
__DATA__
# JOBS = [{'bp': '/Game/..BP.BP', 'pkg': '/Game/..BP', 'cdo': '/Game/..Default__BP_C',
#          'vars': [(name, type, default, category)], 'graphs': [(name, code)], 'write': True}]
LOG = []
def G(d, k, dv=None):
    return d[k] if k in d else dv
def T(name, payload):
    try:
        return True, execute_tool(name, json.dumps(payload))['returnValue']
    except BaseException as e:
        LOG.append(name.split('.')[-1] + ' :: ' + str(e)[:400])
        return False, None
def graphs_of(bp):
    ok, gs = T(BT + 'list_graphs', {'blueprint': {'refPath': bp}})
    return [g['refPath'].split(':')[-1] for g in (gs or [])]
def mk(bp, name):
    if name not in graphs_of(bp):
        T(BT + 'add_function_graph', {'blueprint': {'refPath': bp}, 'graph_name': name})
def clear(g):
    ok, ns = T(BT + 'find_nodes', {'graph': {'refPath': g}, 'title': ''})
    for n in (ns or []):
        r = n['refPath'] if isinstance(n, dict) else str(n)
        if 'FunctionEntry' not in r and 'FunctionResult' not in r:
            T(BT + 'delete_node', {'node': {'refPath': r}})
def dry(bp, name, code, params=()):
    tmp = '_tmp_' + name
    before = set(graphs_of(bp))
    mk(bp, tmp)
    for (pn, pt) in params:
        T(BT + 'add_function_param', {'graph': {'refPath': bp + ':' + tmp}, 'param_name': pn, 'param_type': pt, 'input_param': True})
    T(BT + 'compile_blueprint', {'blueprint': {'refPath': bp}})
    n0 = len(LOG)
    okd, w = T(BT + 'write_graph_dsl', {'graph': {'refPath': bp + ':' + tmp}, 'code': code.replace('(fn ' + name + ' ', '(fn ' + tmp + ' ', 1)})
    err = LOG[n0:]
    T(BT + 'remove_function_graph', {'blueprint': {'refPath': bp}, 'graph_name': tmp})
    left = [g for g in graphs_of(bp) if g not in before]
    for g in left:
        T(BT + 'remove_function_graph', {'blueprint': {'refPath': bp}, 'graph_name': g})
    return okd and not err, [e[:400] for e in err[:2]]
def pin(info, direction, name):
    for p in G(info, 'input_pins' if direction == 'in' else 'output_pins', []):
        if p['name'] == name:
            return p
    return None
def insert_first(g, fn):
    ok, ns = T(BT + 'find_nodes', {'graph': {'refPath': g}, 'title': ''})
    ent = [n for n in (ns or []) if 'FunctionEntry' in n['refPath']]
    if len(ent) != 1:
        return 'no entry'
    ok, inf = T(BT + 'get_node_infos', {'nodes': ent})
    then = pin(inf[0], 'out', 'then')
    nxt = then['connected_pins'][0] if then and then['connected_pins'] else None
    if nxt and fn in str(nxt):
        return 'already'
    ok, inf2 = T(BT + 'get_node_infos', {'nodes': [nxt['node']]}) if nxt else (False, None)
    if inf2 and ('CallFunction' in nxt['node']['refPath']):
        pass
    ok, nn = T(BT + 'create_node', {'graph': {'refPath': g}, 'type_id': 'CallFunction|' + fn, 'pos': {'x': 0, 'y': -200}})
    if not ok:
        return 'create fail'
    nref = nn['refPath'] if isinstance(nn, dict) and 'refPath' in nn else (nn['node']['refPath'] if isinstance(nn, dict) and 'node' in nn else str(nn))
    ok, ninf = T(BT + 'get_node_infos', {'nodes': [{'refPath': nref}]})
    ex = pin(ninf[0], 'in', 'execute'); th = pin(ninf[0], 'out', 'then')
    T(BT + 'connect_pins', {'output_pin': then['pin_id'], 'input_pin': ex['pin_id']})
    if nxt:
        T(BT + 'connect_pins', {'output_pin': th['pin_id'], 'input_pin': nxt})
    ok, chk = T(BT + 'get_node_infos', {'nodes': ent + [{'refPath': nref}]})
    return {'node': nref, 'entry_to': str(pin(chk[0], 'out', 'then')['connected_pins'])[:200], 'new_to': str(pin(chk[1], 'out', 'then')['connected_pins'])[:200]}
def bypass(nref):
    ok, inf = T(BT + 'get_node_infos', {'nodes': [{'refPath': nref}]})
    if not ok:
        return 'no node'
    ex = pin(inf[0], 'in', 'execute'); th = pin(inf[0], 'out', 'then')
    srcs = ex['connected_pins'] if ex else []
    dst = th['connected_pins'][0] if th and th['connected_pins'] else None
    T(BT + 'delete_node', {'node': {'refPath': nref}})
    if dst:
        for sp in srcs:
            T(BT + 'connect_pins', {'output_pin': sp, 'input_pin': dst})
    return {'srcs': len(srcs), 'dst': str(dst)[-60:]}
def compile_ok(bp):
    n0 = len(LOG)
    ok, r = T(BT + 'compile_blueprint', {'blueprint': {'refPath': bp}})
    return ok and len(LOG) == n0
def run():
    out = {}
    try:
        ok, pie = T('EditorToolset.EditorAppToolset.IsPIERunning', {})
        if pie:
            return {'err': 'PIE'}
        if LOADLEVEL:
            T(ST + 'load_level', {'level_path': LOADLEVEL})
        ok, lv = T(ST + 'get_current_level', {})
        out['level'] = lv
        for j in JOBS:
            bp = j['bp']; k = bp.split('.')[-1]; r = {}
            if G(j, 'vars'):
                ok, vs = T(BT + 'list_variables', {'blueprint': {'refPath': bp}})
                have = str(vs)
                added = []
                for (n, t, d, cat) in j['vars']:
                    if ("'" + n + "'") not in have:
                        if t.startswith('obj:'):
                            T(BT + 'add_object_variable', {'blueprint': {'refPath': bp}, 'name': n, 'object_class': {'refPath': t[4:]}})
                        elif t.startswith('arr:'):
                            T(BT + 'add_variable', {'blueprint': {'refPath': bp}, 'name': n, 'type_name': t[4:], 'container_type': 'Array'})
                        else:
                            T(BT + 'add_variable', {'blueprint': {'refPath': bp}, 'name': n, 'type_name': t})
                        added.append(n)
                    if cat:
                        T(BT + 'set_variable_category', {'blueprint': {'refPath': bp}, 'variable_name': n, 'category': cat})
                r['added'] = added
                T(BT + 'compile_blueprint', {'blueprint': {'refPath': bp}})
                vals = {n: d for (n, t, d, cat) in j['vars'] if d is not None}
                if vals:
                    r['cdo'] = T(OT + 'set_properties', {'instance': {'refPath': j['cdo']}, 'values': json.dumps(vals)})[0]
            res = []
            allok = True
            for gt in G(j, 'graphs', []):
                gname = gt[0]; code = gt[1]; params = gt[2] if len(gt) > 2 else ()
                d = dry(bp, gname, code, params)
                if not d[0]:
                    allok = False
                    res.append((gname, 'DRY FAIL', d[1]))
                    continue
                if G(j, 'write', True):
                    newg = gname not in graphs_of(bp)
                    mk(bp, gname)
                    if newg:
                        for (pn, pt) in params:
                            T(BT + 'add_function_param', {'graph': {'refPath': bp + ':' + gname}, 'param_name': pn, 'param_type': pt, 'input_param': True})
                    clear(bp + ':' + gname)
                    w = T(BT + 'write_graph_dsl', {'graph': {'refPath': bp + ':' + gname}, 'code': code})[0]
                    res.append((gname, 'WROTE' if w else 'WRITE FAIL'))
                    allok = allok and w
                else:
                    res.append((gname, 'DRY OK'))
            r['graphs'] = res
            for nref in G(j, 'bypass', []):
                r['byp'] = G(r, 'byp', []) + [bypass(nref)]
            for nref in G(j, 'delete_nodes', []):
                r['del'] = G(r, 'del', []) + [T(BT + 'delete_node', {'node': {'refPath': nref}})[0]]
            if G(j, 'remove_vars'):
                T(BT + 'compile_blueprint', {'blueprint': {'refPath': bp}})
                for vn in j['remove_vars']:
                    r['rmv'] = G(r, 'rmv', []) + [(vn, T(BT + 'remove_variable', {'blueprint': {'refPath': bp}, 'name': vn})[0])]
            if allok:
                T(BT + 'compile_blueprint', {'blueprint': {'refPath': bp}})
                for (g, fn) in G(j, 'insert_first', []):
                    r['ins'] = G(r, 'ins', []) + [insert_first(bp + ':' + g, fn)]
            r['compiled'] = compile_ok(bp)
            if r['compiled'] and allok and G(j, 'save', True):
                r['saved'] = T(AS + 'save_assets', {'asset_paths': [j['pkg']]})[0]
            if G(j, 'deps_check'):
                ok, dd = T(AS + 'get_dependencies', {'asset_path': j['pkg']})
                r['deps_bad'] = [x for x in (dd or []) if any(b in str(x) for b in j['deps_check'])]
            if G(j, 'read'):
                r['read'] = {g: str(T(BT + 'read_graph_dsl', {'graph': {'refPath': bp + ':' + g}})[1]) for g in j['read']}
            out[k] = r
    except BaseException as e:
        LOG.append('run ' + str(e)[:300])
    out['log'] = [l[:400] for l in LOG[:12]]
    T(AS + 'write_file', {'file_path': DUMP, 'content': json.dumps(out)})
    return {k: ({kk: vv for kk, vv in v.items() if kk != 'read'} if isinstance(v, dict) else v) for k, v in out.items()}
