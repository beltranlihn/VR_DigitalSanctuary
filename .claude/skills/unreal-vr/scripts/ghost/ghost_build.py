import json
# ghost_build.py - crea (idempotente) lo que describe ghost_spec.json: BP_GhostTake_SC + los 10 DA, BP_GhostPlayer_SC y
# BP_GhostRecorder_SC (variables con categoria, instance-editable y default en el CDO; funciones con sus parametros).
# NO escribe grafos (eso es ghost_write.py). Se pega ENTERO como `script` de execute_tool_script.
# PARTE = 'take' | 'player' | 'recorder' : cambiar la linea de abajo antes de cada corrida (una parte por llamada).
PARTE = 'take'
SPEC = 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/ghost/ghost_spec.json'
BT = 'editor_toolset.toolsets.blueprint.BlueprintTools.'
OT = 'editor_toolset.toolsets.object.ObjectTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
DA = 'editor_toolset.toolsets.data_asset.DataAssetTools.'
LOG = []
def gv(d, k):
    """d[k] o None, sin dict.get (el sandbox falla con .get(k, default))."""
    return d[k] if isinstance(d, dict) and (k in d) else None


PRIM = {'float': 'float', 'int': 'int', 'bool': 'bool', 'string': 'string', 'name': 'name',
        'vector': 'Vector', 'rotator': 'Rotator', 'transform': 'Transform', 'linearcolor': 'LinearColor'}


def T(name, payload):
    try:
        r = execute_tool(name, json.dumps(payload))
        v = r['returnValue'] if isinstance(r, dict) and ('returnValue' in r) else r
        return True, v
    except BaseException as e:
        LOG.append(name.split('.')[-1] + ' :: ' + str(e)[:180])
        return False, None


def G(ref, props):
    ok, v = T(OT + 'get_properties', {'instance': {'refPath': ref}, 'properties': props})
    if not ok or v is None:
        return None
    try:
        return json.loads(v) if isinstance(v, str) else v
    except BaseException:
        return None


def S(ref, vals):
    return T(OT + 'set_properties', {'instance': {'refPath': ref}, 'values': json.dumps(vals)})[0]


def jval(v):
    """default de la spec -> JSON de set_properties."""
    t, d = v['type'], gv(v, 'default')
    if d is None:
        return None
    arr = gv(v, 'container') == 'array'
    def one(x):
        if t == 'object':
            return {'refPath': x} if x else None
        if t == 'vector':
            return {'x': x[0], 'y': x[1], 'z': x[2]}
        if t == 'linearcolor':
            return {'r': x[0], 'g': x[1], 'b': x[2], 'a': x[3]}
        return x
    if arr:
        return [one(x) for x in d]
    return one(d)


def txt(v, x):
    if v['type'] == 'vector':
        return '(X=%f,Y=%f,Z=%f)' % (x[0], x[1], x[2])
    return '(R=%f,G=%f,B=%f,A=%f)' % (x[0], x[1], x[2], x[3])


def same(v, got, want):
    """compara lo leido (dict x/y/z o r/g/b/a) con la spec."""
    keys = ['x', 'y', 'z'] if v['type'] == 'vector' else ['r', 'g', 'b', 'a']
    try:
        return all(abs(float(got[k]) - float(w)) < 1e-3 for k, w in zip(keys, want))
    except BaseException:
        return False


def setvec(CDO, v):
    """Vector / LinearColor (o arreglo): prueba el JSON de campos, relee; si no quedo, el formato de TEXTO de Unreal.
    (Transform de SceneComponent solo acepta texto; un Transform de BP solo acepta JSON: gotchas 519 y toolsets.)"""
    d = v['default']
    arr = gv(v, 'container') == 'array'
    items = d if arr else [d]
    for modo in ('json', 'texto'):
        vals = [jval({'type': v['type'], 'default': x}) if modo == 'json' else txt(v, x) for x in items]
        S(CDO, {v['name']: vals if arr else vals[0]})
        got = G(CDO, [v['name']])
        g = got[v['name']] if got and (v['name'] in got) else None
        gl = g if arr else [g]
        if g is not None and len(gl) == len(items) and all(same(v, a, b) for a, b in zip(gl, items)):
            return modo
    return 'NO'


def make_bp(sp, out):
    path = sp['path']
    folder, name = path.rsplit('/', 1)
    B = path + '.' + name
    ok, ex = T(AS + 'exists', {'path': path})
    if not ex:
        ok, r = T(BT + 'create', {'folder_path': folder, 'asset_name': name, 'asset_type': {'refPath': sp['parent']}})
        out['creado'] = ok
    ok, have = T(BT + 'list_variables', {'blueprint': B})
    names = set()
    for x in (have or []):
        names.add(gv(x, 'name') if isinstance(x, dict) else str(x))
    nuevas = 0
    for v in sp['vars']:
        if v['name'] in names:
            continue
        cont = {'container_type': 'Array'} if gv(v, 'container') == 'array' else {}
        if v['type'] == 'object':
            p = {'blueprint': B, 'name': v['name'], 'object_class': v['class']}
            p.update(cont)
            ok, r = T(BT + 'add_object_variable', p)
        else:
            p = {'blueprint': B, 'name': v['name'], 'type_name': PRIM[v['type']]}
            p.update(cont)
            ok, r = T(BT + 'add_variable', p)
            if not ok and v['type'] in ('string', 'name'):
                p['type_name'] = PRIM[v['type']].capitalize()
                ok, r = T(BT + 'add_variable', p)
        nuevas += 1 if ok else 0
        T(BT + 'set_variable_category', {'blueprint': B, 'variable_name': v['name'], 'category': v['cat']})
        if gv(v, 'edit'):
            T(BT + 'set_variable_instance_editable', {'blueprint': B, 'variable_name': v['name'], 'instance_editable': True})
    out['vars_nuevas'] = nuevas
    fn_nuevas = 0
    ok, graphs = T(BT + 'list_graphs', {'blueprint': B})
    gnames = set(str(gv(g, 'refPath') if isinstance(g, dict) else g).split(':')[-1] for g in (graphs or []))
    for fn, params in sp['functions'].items():
        if fn in gnames:
            continue
        ok, r = T(BT + 'add_function_graph', {'blueprint': B, 'graph_name': fn})
        if not ok:
            continue
        fn_nuevas += 1
        GR = B + ':' + fn
        for pa in params:
            cont = {'container_type': 'Array'} if gv(pa, 'container') == 'array' else {}
            if pa['type'] == 'object':
                q = {'graph': GR, 'param_name': pa['name'], 'object_class': pa['class'], 'input_param': True}
                q.update(cont)
                T(BT + 'add_object_function_param', q)
            elif pa['type'] == 'transform':
                T(BT + 'add_struct_function_param', {'graph': GR, 'param_name': pa['name'], 'struct_type': '/Script/CoreUObject.Transform', 'input_param': True})
            else:
                q = {'graph': GR, 'param_name': pa['name'], 'param_type': PRIM[pa['type']], 'input_param': True}
                q.update(cont)
                ok2, r2 = T(BT + 'add_function_param', q)
                if not ok2 and pa['type'] in ('string', 'name'):
                    q['param_type'] = PRIM[pa['type']].capitalize()
                    T(BT + 'add_function_param', q)
    out['funciones_nuevas'] = fn_nuevas
    T(BT + 'compile_blueprint', {'blueprint': B})
    CDO = folder + '/' + name + '.Default__' + name + '_C'
    malos, vec = [], {}
    for v in sp['vars']:
        val = jval(v)
        if val is None or (isinstance(val, str) and val.startswith('TURNO')):
            continue
        if v['type'] in ('vector', 'linearcolor'):
            vec[v['name']] = setvec(CDO, v)
            continue
        if not S(CDO, {v['name']: val}):
            malos.append(v['name'])
    out['cdo_no_escritas'] = malos
    out['vectores'] = vec
    T(BT + 'compile_blueprint', {'blueprint': B})
    chk = [v['name'] for v in sp['vars'] if gv(v, 'default') not in (None, [], '') and v['type'] in ('float', 'int', 'vector')][:6]
    out['cdo_lectura'] = G(CDO, chk)
    return B


def run():
    try:
        return run2()
    except BaseException as e:
        return {'err': 'run :: ' + str(e)[:300], 'log': LOG}


def run2():
    ok, txt = T(AS + 'read_file', {'file_path': SPEC})
    if not ok:
        return {'err': 'no pude leer la spec', 'log': LOG}
    spec = json.loads(txt)
    out = {'parte': PARTE}
    T(AS + 'create_folder', {'path': '/Game/SoulCharger/Mechanics/Ghost'})
    T(AS + 'create_folder', {'path': '/Game/SoulCharger/Mechanics/Ghost/Takes'})
    if PARTE == 'take':
        make_bp(spec['BP_GhostTake_SC'], out)
        cls = spec['BP_GhostTake_SC']['path'] + '.BP_GhostTake_SC_C'
        das = {}
        for it in spec['DA']['items']:
            path = spec['DA']['folder'] + '/' + it['asset']
            ok, ex = T(AS + 'exists', {'path': path})
            if not ex:
                ok, r = T(DA + 'create', {'folder_path': spec['DA']['folder'], 'asset_name': it['asset'], 'asset_type': {'refPath': cls}})
            ref = path + '.' + it['asset']
            vals = {'Id': it['id'], 'Text': it['text'], 'Hz': 30.0, 'Stride': 28,
                    'bUseRight': it['R'], 'bUseLeft': it['L'], 'bBeamRight': it['BR'], 'bBeamLeft': it['BL']}
            okw = S(ref, vals)
            das[it['asset']] = 'ok' if okw else 'NO'
        out['das'] = das
        first = spec['DA']['folder'] + '/' + spec['DA']['items'][0]['asset'] + '.' + spec['DA']['items'][0]['asset']
        out['da0'] = G(first, ['Id', 'Text', 'Hz', 'Stride', 'bUseRight', 'Frames'])
    elif PARTE == 'player':
        make_bp(spec['BP_GhostPlayer_SC'], out)
    elif PARTE == 'recorder':
        make_bp(spec['BP_GhostRecorder_SC'], out)
    out['log'] = LOG[:40]
    return out
