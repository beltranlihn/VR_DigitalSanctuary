import json
# ghost_build.py (v2, 2026-10-01) - arma lo que describe ghost_spec.json. NO escribe grafos (eso es ghost_write.py).
# Se pega ENTERO como `script` de execute_tool_script. Nunca levanta excepcion (T() atrapa todo, gotcha 231/557).
# PARTE (cambiar la linea de abajo antes de cada corrida; una parte por llamada):
#   'clear'    -> UNA SOLA VEZ: vacia EventGraph y Construction Script y quita TODAS las funciones del grabador y del
#                 reproductor (el grabador primero: llama funciones del reproductor). Despues de esto los grafos v2 se
#                 escriben en grafos vacios (nunca se reescribe un grafo con cuerpo).
#   'take'     -> clase BP_GhostTake_SC (quita bUseRight/Left, agrega los campos nuevos) + valores de los 10 DA.
#   'player'   -> BP_GhostPlayer_SC: quita las variables de v1 (BeamR/BeamL ANTES de crear los componentes del mismo
#                 nombre), componentes fijos, variables, funciones con parametros, defaults del CDO, mano copiada del pawn.
#   'recorder' -> BP_GhostRecorder_SC: igual, sin componentes.
# Idempotente salvo 'clear'. Re-correr una parte que se corto es seguro.
PARTE = 'clear'
SPEC = 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/ghost/ghost_spec.json'
BT = 'editor_toolset.toolsets.blueprint.BlueprintTools.'
OT = 'editor_toolset.toolsets.object.ObjectTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
AT = 'editor_toolset.toolsets.actor.ActorTools.'
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


def refp(x):
    return str(gv(x, 'refPath') if isinstance(x, dict) else x)


def jval(v):
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
    keys = ['x', 'y', 'z'] if v['type'] == 'vector' else ['r', 'g', 'b', 'a']
    try:
        return all(abs(float(got[k]) - float(w)) < 1e-3 for k, w in zip(keys, want))
    except BaseException:
        return False


def setvec(CDO, v):
    """Vector / LinearColor (o arreglo): JSON de campos, relee; si no quedo, formato de TEXTO (gotcha 519)."""
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


def graphs(B):
    ok, gs = T(BT + 'list_graphs', {'blueprint': B})
    return [refp(g) for g in (gs or [])]


def nodes(g):
    ok, v = T(BT + 'find_nodes', {'graph': g, 'title': ''})
    return v or []


def clear_bp(B, out):
    """EventGraph y Construction Script vacios (la entrada del CS queda) y TODAS las funciones afuera."""
    borr, fns = 0, 0
    for g in graphs(B):
        name = g.split(':')[-1]
        if name in ('EventGraph', 'UserConstructionScript'):
            for x in nodes(g):
                r = refp(x)
                if 'FunctionEntry' in r:
                    continue
                borr += 1 if T(BT + 'delete_node', {'node': {'refPath': r}})[0] else 0
        else:
            fns += 1 if T(BT + 'remove_function_graph', {'blueprint': B, 'graph_name': name})[0] else 0
    out[B.split('.')[-1]] = {'nodos_borrados': borr, 'funciones_quitadas': fns}


def var_names(B):
    ok, have = T(BT + 'list_variables', {'blueprint': B})
    return set((gv(x, 'name') if isinstance(x, dict) else str(x)) for x in (have or []))


def comp_map(CDO):
    ok, cs = T(AT + 'get_components', {'actor': {'refPath': CDO}})
    m = {}
    for c in (cs or []):
        r = refp(c)
        n = r.split('.')[-1].split(':')[-1].replace('_GEN_VARIABLE', '')
        m[n] = r
    return m


def find_pawn_cdo():
    ok, r = T(AS + 'find_assets', {'folder_path': '/Game/SoulCharger', 'name': 'BP_VRPawn_SC'})
    for a in (r or []):
        p = refp(a).split('.')[0]
        if p.endswith('/BP_VRPawn_SC'):
            return p + '.Default__BP_VRPawn_SC_C'
    return None


def make_components(sp, B, CDO, out):
    if not gv(sp, 'components'):
        return {}
    have = comp_map(CDO)
    pawn = find_pawn_cdo()
    pmap = comp_map(pawn) if pawn else {}
    hand_xf, res = {}, {}
    for c in sp['components']:
        n = c['name']
        if n not in have:
            ok, r = T(AT + 'add_component', {'owner': {'refPath': CDO}, 'component_type': {'refPath': c['class']}, 'name': n})
            res[n] = 'creado' if ok else 'NO'
            have = comp_map(CDO)
        ref = have[n] if n in have else None
        if not ref:
            continue
        props = gv(c, 'props')
        if props:
            S(ref, props)
        src = gv(c, 'copy_from_pawn')
        if src and src in pmap:
            pv = G(pmap[src], ['SkeletalMeshAsset', 'AnimClass', 'AnimationMode', 'RelativeLocation', 'RelativeRotation', 'RelativeScale3D'])
            if pv:
                cp = {}
                for k in ('SkeletalMeshAsset', 'AnimClass', 'AnimationMode'):
                    if k in pv and pv[k] not in (None, ''):
                        cp[k] = pv[k]
                res[n + '_copia'] = S(ref, cp) if cp else 'nada que copiar'
                hand_xf[n] = pv
    out['componentes'] = res
    out['pawn'] = pawn
    return hand_xf


def make_bp(sp, out):
    path = sp['path']
    folder, name = path.rsplit('/', 1)
    B = path + '.' + name
    CDO = folder + '/' + name + '.Default__' + name + '_C'
    ok, ex = T(AS + 'exists', {'path': path})
    if not ex:
        ok, r = T(BT + 'create', {'folder_path': folder, 'asset_name': name, 'asset_type': {'refPath': sp['parent']}})
        out['creado'] = ok
    # 1. variables de v1 que sobran (ANTES de los componentes: BeamR/BeamL cambian de variable a componente)
    names = var_names(B)
    quitadas = []
    for n in (gv(sp, 'remove') or []):
        if n in names:
            if T(BT + 'remove_variable', {'blueprint': B, 'name': n})[0]:
                quitadas.append(n)
    out['vars_quitadas'] = quitadas
    T(BT + 'compile_blueprint', {'blueprint': B})
    # 2. componentes fijos (el Construction Script no puede crear componentes)
    hand_xf = make_components(sp, B, CDO, out)
    # 3. variables nuevas
    names = var_names(B)
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
    # 4. funciones con sus parametros (las que faltan)
    fn_nuevas = 0
    gnames = set(g.split(':')[-1] for g in graphs(B))
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
    # 5. defaults del CDO
    malos, vec = [], {}
    for v in sp['vars']:
        val = jval(v)
        if val is None:
            continue
        if v['type'] in ('vector', 'linearcolor'):
            vec[v['name']] = setvec(CDO, v)
            continue
        if not S(CDO, {v['name']: val}):
            malos.append(v['name'])
    # la mano del fantasma = la del pawn (malla, AnimBP y transform relativa al grip)
    for comp, var in (('HandR', 'HandXfR'), ('HandL', 'HandXfL')):
        pv = gv(hand_xf, comp)
        if pv and ('RelativeLocation' in pv) and ('RelativeRotation' in pv):
            ok = S(CDO, {var: {'location': pv['RelativeLocation'], 'rotation': pv['RelativeRotation'],
                               'scale': gv(pv, 'RelativeScale3D') or {'x': 1, 'y': 1, 'z': 1}}})
            vec[var] = 'del pawn' if ok else 'NO'
    out['cdo_no_escritas'] = malos
    out['vectores'] = vec
    T(BT + 'compile_blueprint', {'blueprint': B})
    chk = [v['name'] for v in sp['vars'] if gv(v, 'default') not in (None, [], '') and v['type'] in ('float', 'int', 'vector', 'transform')][:8]
    out['cdo_lectura'] = G(CDO, chk)
    return B


def run():
    try:
        return run2()
    except BaseException as e:
        return {'err': 'run :: ' + str(e)[:300], 'log': LOG}


def run2():
    ok, t = T(AS + 'read_file', {'file_path': SPEC})
    if not ok:
        return {'err': 'no pude leer la spec', 'log': LOG}
    spec = json.loads(t)
    if gv(spec, 'version') != 2:
        return {'err': 'la spec no es v2: correr make_spec.py + split_ghost.py', 'log': LOG}
    out = {'parte': PARTE}
    if PARTE == 'clear':
        for bp in ('BP_GhostRecorder_SC', 'BP_GhostPlayer_SC'):
            path = spec[bp]['path']
            clear_bp(path + '.' + path.rsplit('/', 1)[1], out)
        for bp in ('BP_GhostRecorder_SC', 'BP_GhostPlayer_SC'):
            path = spec[bp]['path']
            T(BT + 'compile_blueprint', {'blueprint': path + '.' + path.rsplit('/', 1)[1]})
    elif PARTE == 'take':
        make_bp(spec['BP_GhostTake_SC'], out)
        cls = spec['BP_GhostTake_SC']['path'] + '.BP_GhostTake_SC_C'
        das = {}
        for it in spec['DA']['items']:
            path = spec['DA']['folder'] + '/' + it['asset']
            ok, ex = T(AS + 'exists', {'path': path})
            if not ex:
                ok, r = T(DA + 'create', {'folder_path': spec['DA']['folder'], 'asset_name': it['asset'], 'asset_type': {'refPath': cls}})
            ref = path + '.' + it['asset']
            vals = {'Id': it['id'], 'Text': it['text'], 'Hz': 30.0, 'Stride': 34, 'HoldR': it['HoldR'],
                    'HoldL': it['HoldL'], 'bBeamRight': it['BR'], 'bBeamLeft': it['BL'], 'bHeadAnchor': it['Head'],
                    'Extra': it['Extra'], 'DemoTime': it['DemoTime']}
            das[it['asset']] = 'ok' if S(ref, vals) else 'NO'
        out['das'] = das
        first = spec['DA']['folder'] + '/' + spec['DA']['items'][6]['asset'] + '.' + spec['DA']['items'][6]['asset']
        out['da_attract'] = G(first, ['Id', 'Text', 'Stride', 'HoldR', 'HoldL', 'bBeamRight', 'bHeadAnchor', 'Extra', 'DemoTime', 'Frames'])
    elif PARTE == 'player':
        make_bp(spec['BP_GhostPlayer_SC'], out)
    elif PARTE == 'recorder':
        make_bp(spec['BP_GhostRecorder_SC'], out)
    out['log'] = LOG[:40]
    return out
