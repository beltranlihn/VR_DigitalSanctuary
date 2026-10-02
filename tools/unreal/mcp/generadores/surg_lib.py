import json
BT = 'editor_toolset.toolsets.blueprint.BlueprintTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
OT = 'editor_toolset.toolsets.object.ObjectTools.'
ST = 'editor_toolset.toolsets.scene.SceneTools.'
LOG = []
REPORT = False
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
        r = n['refPath']
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
    for g in graphs_of(bp):
        if g not in before:
            T(BT + 'remove_function_graph', {'blueprint': {'refPath': bp}, 'graph_name': g})
    return okd and not err, [e[:400] for e in err[:2]]
def write_graph(bp, name, code, params=()):
    d = dry(bp, name, code, params)
    if not d[0]:
        return 'DRY FAIL ' + str(d[1])
    newg = name not in graphs_of(bp)
    mk(bp, name)
    if newg:
        for (pn, pt) in params:
            T(BT + 'add_function_param', {'graph': {'refPath': bp + ':' + name}, 'param_name': pn, 'param_type': pt, 'input_param': True})
    clear(bp + ':' + name)
    return 'WROTE' if T(BT + 'write_graph_dsl', {'graph': {'refPath': bp + ':' + name}, 'code': code})[0] else 'WRITE FAIL'
def pin(info, direction, name):
    for p in G(info, 'input_pins' if direction == 'in' else 'output_pins', []):
        if p['name'] == name:
            return p
    return None
def nref_of(nn):
    if isinstance(nn, dict) and 'refPath' in nn:
        return nn['refPath']
    if isinstance(nn, dict) and 'node' in nn:
        return nn['node']['refPath']
    return str(nn)
def insert_first(g, fn):
    ok, ns = T(BT + 'find_nodes', {'graph': {'refPath': g}, 'title': ''})
    ent = [n for n in (ns or []) if 'FunctionEntry' in n['refPath']]
    if len(ent) != 1:
        return 'no entry'
    ok, inf = T(BT + 'get_node_infos', {'nodes': ent})
    then = pin(inf[0], 'out', 'then')
    nxt = then['connected_pins'][0] if then and then['connected_pins'] else None
    if nxt:
        ok, ninf = T(BT + 'get_node_infos', {'nodes': [nxt['node']]})
        if ok and ninf[0]['type_id'] == '|' + fn:
            return 'already'
    ok, nn = T(BT + 'create_node', {'graph': {'refPath': g}, 'type_id': 'CallFunction|' + fn, 'pos': {'x': 0, 'y': -200}})
    if not ok:
        return 'create fail'
    nref = nref_of(nn)
    ok, ninf = T(BT + 'get_node_infos', {'nodes': [{'refPath': nref}]})
    ex = pin(ninf[0], 'in', 'execute'); th = pin(ninf[0], 'out', 'then')
    T(BT + 'connect_pins', {'output_pin': then['pin_id'], 'input_pin': ex['pin_id']})
    if nxt:
        T(BT + 'connect_pins', {'output_pin': th['pin_id'], 'input_pin': nxt})
    return 'inserted'
def node_map(g):
    ok, ns = T(BT + 'find_nodes', {'graph': {'refPath': g}, 'title': ''})
    M = {}
    ns = ns or []
    for i in range(0, len(ns), 30):
        ok, inf = T(BT + 'get_node_infos', {'nodes': ns[i:i + 30]})
        if ok:
            for n in inf:
                M[n['node']['refPath']] = n
        else:
            for n0 in ns[i:i + 30]:
                ok1, inf1 = T(BT + 'get_node_infos', {'nodes': [n0]})
                if ok1:
                    M[n0['refPath']] = inf1[0]
    return M
def fval(s):
    try:
        return float(s)
    except BaseException:
        return None
def srcnode(M, p):
    if not p['connected_pins']:
        return None
    r = p['connected_pins'][0]['node']['refPath']
    return M[r] if r in M else None
def lit(M, p):
    if p['connected_pins']:
        si = srcnode(M, p)
        if si and si['type_id'] == 'Math|Float|MakeLiteralFloat':
            q = pin(si, 'in', 'Value')
            return fval(q['value']) if q else None
        return None
    return fval(p['value'])
def tmatch(t, want):
    return t == want[1:] if want.startswith('=') else (want in t)
def surgery(bp, specs, prefix):
    res = []
    byg = {}
    for s in specs:
        byg[s['g']] = G(byg, s['g'], []) + [s]
    for g in byg:
        gp = bp + ':' + g
        M = node_map(gp)
        for s in byg[g]:
            cands = []
            for ref in M:
                n = M[ref]
                if n['type_id'] != s['t']:
                    continue
                tp = pin(n, 'in', s['pin'])
                if tp is None:
                    continue
                if 'v' in s:
                    v = lit(M, tp)
                    if v is None or abs(v - s['v']) > 1e-4:
                        continue
                if 'src' in s:
                    sn = srcnode(M, tp)
                    if not sn or not tmatch(sn['type_id'], s['src']):
                        continue
                okf = True
                for fp in G(s, 'f', {}):
                    q = pin(n, 'in', fp)
                    sn = srcnode(M, q) if q else None
                    if not sn or not tmatch(sn['type_id'], s['f'][fp]):
                        okf = False
                if okf:
                    cands.append((ref, tp, n['position']))
            want = s['n']
            if (want >= 0 and len(cands) != want) or (want < 0 and len(cands) == 0):
                res.append((g, s['var'], 'SKIP found %d expected %d' % (len(cands), want)))
                continue
            if REPORT:
                res.append((g, s['var'], 'WOULD %d' % len(cands)))
                continue
            done = 0
            for (ref, tp, pos) in cands:
                ok, nn = T(BT + 'create_node', {'graph': {'refPath': gp}, 'type_id': prefix + s['var'], 'pos': {'x': pos['x'] - 260, 'y': pos['y'] + 60}})
                if not ok:
                    break
                nref = nref_of(nn)
                ok, ni = T(BT + 'get_node_infos', {'nodes': [{'refPath': nref}]})
                outp = ni[0]['output_pins'][0]['pin_id']
                ok2, _ = T(BT + 'connect_pins', {'output_pin': outp, 'input_pin': tp['pin_id']})
                if ok2:
                    done += 1
            res.append((g, s['var'], 'OK %d/%d' % (done, len(cands))))
    return res
def add_vars(bp, cdo, vars_):
    ok, vs = T(BT + 'list_variables', {'blueprint': {'refPath': bp}})
    have = str(vs)
    added = []
    for (n, t, d, cat) in vars_:
        if ("'" + n + "'") not in have:
            if t.startswith('objarr:'):
                T(BT + 'add_object_variable', {'blueprint': {'refPath': bp}, 'name': n, 'object_class': {'refPath': t[7:]}, 'container_type': 'Array'})
            elif t.startswith('obj:'):
                T(BT + 'add_object_variable', {'blueprint': {'refPath': bp}, 'name': n, 'object_class': {'refPath': t[4:]}})
            elif t == 'a5':
                T(BT + 'add_variable', {'blueprint': {'refPath': bp}, 'name': n, 'type_name': 'float', 'container_type': 'Array'})
            elif t == 'f':
                T(BT + 'add_variable', {'blueprint': {'refPath': bp}, 'name': n, 'type_name': 'float'})
            else:
                T(BT + 'add_variable', {'blueprint': {'refPath': bp}, 'name': n, 'type_name': t})
            added.append(n)
        if cat:
            T(BT + 'set_variable_category', {'blueprint': {'refPath': bp}, 'variable_name': n, 'category': cat})
    T(BT + 'compile_blueprint', {'blueprint': {'refPath': bp}})
    vals = {}
    for (n, t, d, cat) in vars_:
        if d is not None:
            vals[n] = d
    okc = T(OT + 'set_properties', {'instance': {'refPath': cdo}, 'values': json.dumps(vals)})[0] if vals else True
    return added, okc
def compile_ok(bp):
    n0 = len(LOG)
    T(BT + 'compile_blueprint', {'blueprint': {'refPath': bp}})
    return len(LOG) == n0
