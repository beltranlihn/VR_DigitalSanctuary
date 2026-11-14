# build_ic.py - crea/ajusta la ESTRUCTURA de los Blueprints de Inner Canvas desde ic_spec.json (lo arma ic_spec.py):
# BP nuevos, funciones y variables que sobran (de la demo), variables nuevas, funciones con sus parametros, componentes en el CDO.
# Idempotente, nunca levanta (gotcha 60). Los grafos van aparte (writer) y los valores del CDO tambien (cdo_ic.py).
# Correr con un nivel NEUTRO abierto (Test_QuestCtrl): reinstanciar un BP colocado en el nivel abierto se lo lleva (gotcha 402).
import json
BT = 'editor_toolset.toolsets.blueprint.BlueprintTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
AT = 'editor_toolset.toolsets.actor.ActorTools.'
OT = 'editor_toolset.toolsets.object.ObjectTools.'
SPEC = 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/InnerCanvas/ic_spec.json'
LOG = []
STRUCTS = {'Vector': '/Script/CoreUObject.Vector', 'LinearColor': '/Script/CoreUObject.LinearColor', 'Rotator': '/Script/CoreUObject.Rotator'}


def T(name, payload):
    try:
        return True, execute_tool(name, json.dumps(payload))['returnValue']
    except BaseException as e:
        LOG.append(name.split('.')[-1] + ' :: ' + str(e)[:200])
        return False, None


def S(ref, vals):
    return T(OT + 'set_properties', {'instance': {'refPath': ref}, 'values': json.dumps(vals)})[0]


def nm(x):
    return x['name'] if isinstance(x, dict) else str(x)


def build(b):
    out = {}
    path = b['path']
    name = b['name']
    BPR = path + '.' + name
    BPo = {'refPath': BPR}
    ok, ex = T(AS + 'exists', {'path': path})
    if not ex and b.get('create'):
        folder = path.rsplit('/', 1)[0]
        T(BT + 'create', {'folder_path': folder, 'asset_name': name, 'asset_type': {'refPath': '/Script/Engine.Actor'}})
        out['creado'] = True
    ok, gr = T(BT + 'list_graphs', {'blueprint': BPo})
    gnames = set([(g['refPath'] if isinstance(g, dict) else str(g)).split(':')[-1] for g in (gr or [])])
    rf = 0
    for f in b.get('remove_funcs', []):
        if f in gnames:
            rf += T(BT + 'remove_function_graph', {'blueprint': BPo, 'graph_name': f})[0]
    out['funcs_borradas'] = rf
    ok, have = T(BT + 'list_variables', {'blueprint': BPo})
    have = set([nm(h) for h in (have or [])])
    rv = 0
    for vname in b.get('remove_vars', []):
        if vname in have:
            rv += T(BT + 'remove_variable', {'blueprint': BPo, 'name': vname})[0]
            have.discard(vname)
    out['vars_borradas'] = rv
    added = 0
    for vname, t, cat, ed, arr in b['vars']:
        if vname not in have:
            args = {'blueprint': BPo, 'name': vname}
            if arr:
                args['container_type'] = 'Array'
            if t.startswith('obj:'):
                args['object_class'] = {'refPath': t[4:]}
                ok, _ = T(BT + 'add_object_variable', args)
            elif t.startswith('struct:'):
                args['struct_type'] = {'refPath': t[7:]}
                ok, _ = T(BT + 'add_struct_variable', args)
            elif t in STRUCTS and arr:
                args['struct_type'] = {'refPath': STRUCTS[t]}
                ok, _ = T(BT + 'add_struct_variable', args)
            else:
                args['type_name'] = t
                ok, _ = T(BT + 'add_variable', args)
            added += 1 if ok else 0
        if ed:
            T(BT + 'set_variable_instance_editable', {'blueprint': BPo, 'variable_name': vname, 'instance_editable': True})
    out['vars_nuevas'] = added
    fadded = 0
    for fn, params in b['funcs']:
        if fn in gnames:
            continue
        ok, _ = T(BT + 'add_function_graph', {'blueprint': BPo, 'graph_name': fn})
        if not ok:
            continue
        fadded += 1
        g = {'refPath': BPR + ':' + fn}
        for pn, pt, inp in params:
            if pt.startswith('obj:'):
                T(BT + 'add_object_function_param', {'graph': g, 'param_name': pn, 'object_class': {'refPath': pt[4:]}, 'input_param': inp})
            elif pt in STRUCTS:
                T(BT + 'add_struct_function_param', {'graph': g, 'param_name': pn, 'struct_type': {'refPath': STRUCTS[pt]}, 'input_param': inp})
            else:
                T(BT + 'add_function_param', {'graph': g, 'param_name': pn, 'param_type': pt, 'input_param': inp})
    out['funcs_nuevas'] = fadded
    ok, cdo = T(BT + 'get_default_object', {'blueprint': BPo})
    cdor = cdo['refPath'] if ok and isinstance(cdo, dict) else None
    nc = 0
    if cdor and b.get('comps'):
        ok, comps = T(AT + 'get_components', {'actor': {'refPath': cdor}})
        cnames = set([(c['refPath'] if isinstance(c, dict) else str(c)).split(':')[-1].replace('_GEN_VARIABLE', '') for c in (comps or [])])
        for c in b['comps']:
            if c['name'] in cnames:
                continue
            ok, r = T(AT + 'add_component', {'owner': {'refPath': cdor}, 'component_type': {'refPath': '/Script/Engine.StaticMeshComponent'}, 'name': c['name']})
            if not ok:
                continue
            ref = r['refPath'] if isinstance(r, dict) else str(r)
            nc += 1
            vals = {'StaticMesh': {'refPath': c['mesh']}, 'CastShadow': False,
                    'relativeLocation': '(X=%f,Y=%f,Z=%f)' % tuple(c['loc']), 'relativeRotation': c['rot'],
                    'relativeScale3D': '(X=%f,Y=%f,Z=%f)' % tuple(c['scale'])}
            if c.get('mat'):
                vals['OverrideMaterials'] = [{'refPath': c['mat']}]
            S(ref, vals)
            if c.get('coll'):
                S(ref, {'BodyInstance': {'objectType': 'ECC_Destructible', 'collisionEnabled': 'QueryOnly', 'collisionProfileName': 'Custom',
                                         'collisionResponses': {'responseArray': [{'channel': ch, 'response': 'ECR_Overlap'} for ch in
                                                                                  ['WorldStatic', 'WorldDynamic', 'Pawn', 'Visibility', 'Camera', 'PhysicsBody', 'Vehicle', 'Destructible']]}}})
            else:
                S(ref, {'BodyInstance': {'collisionEnabled': 'NoCollision', 'collisionProfileName': 'NoCollision'}})
            if c.get('hidden'):
                S(ref, {'bHiddenInGame': True})
        if b.get('tags'):
            S(cdor, {'Tags': b['tags']})
    out['comps_nuevos'] = nc
    ok, cr = T(BT + 'compile_blueprint', {'blueprint': BPo})
    out['compile'] = str(cr)[:300]
    return out


def run():
    try:
        ok, txt = T(AS + 'read_file', {'file_path': SPEC})
        spec = json.loads(txt)
        res = {}
        for b in spec['bps']:
            res[b['name']] = build(b)
        res['log'] = LOG[:40]
        return res
    except BaseException as e:
        return {'err': str(e)[:300], 'log': LOG[:40]}
