import json
# runner_build.py - crea BP_StageRunner_SC (Obra): componentes, variables, parametros y grafos desde runner.json. IDEMPOTENTE.
BT = 'editor_toolset.toolsets.blueprint.BlueprintTools.'
AT = 'editor_toolset.toolsets.actor.ActorTools.'
OT = 'editor_toolset.toolsets.object.ObjectTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
PKG = '/Game/SoulCharger/Obra/BP_StageRunner_SC'
BP = PKG + '.BP_StageRunner_SC'
SRC = 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/Obra/runner.json'
LOG = []
def T(name, payload):
    try:
        return True, execute_tool(name, json.dumps(payload))['returnValue']
    except BaseException as e:
        LOG.append(name.split('.')[-1] + ' :: ' + str(e)[:300])
        return False, None
def rp(x):
    return x['refPath'] if isinstance(x, dict) and 'refPath' in x else str(x)
def S(ref, vals):
    return T(OT + 'set_properties', {'instance': {'refPath': ref}, 'values': json.dumps(vals)})[0]
VARS = [('StageK', 'int', 1), ('Loop', 'bool', 1), ('Speed', 'float', 1), ('AlmaTime', 'float', 1), ('InstrTime', 'float', 1),
        ('OutroTime', 'float', 1), ('TimeoutS', 'float', 1), ('ChargeTime', 'float', 1), ('EyeRef', 'float', 1),
        ('CTop', 'LinearColor', 1), ('CHor', 'LinearColor', 1), ('LevelName', 'name', 1), ('TagIn', 'name', 1),
        ('TagSide', 'name', 1), ('TagCharge', 'name', 1), ('TagTitle', 'name', 1),
        ('IsObra', 'bool', 0), ('RPhase', 'int', 0), ('RT', 'float', 0), ('PT', 'float', 0), ('RDone', 'bool', 0),
        ('ByeSt', 'int', 0), ('PStart', 'Vector', 0), ('PYaw', 'float', 0)]
PARAMS = {'RAdjust': [('Tag', 'name')], 'RSay': [('Bye', 'int')], 'RGhost': [('On', 'bool')], 'RGo': [('P', 'int')], 'RStep': [('Dt', 'float')]}
ORDER = ['RGo', 'RAdjust', 'RSay', 'RWake', 'RIntro', 'RBegin', 'ROutro', 'RRead', 'RGhost', 'RPlaceTitle', 'RVeil', 'RAlmaIn', 'RBoot', 'RStep']
def run():
  try:
    out = {}
    ok, ex = T(AS + 'exists', {'path': PKG})
    if not ex:
        out['create'] = T(BT + 'create', {'folder_path': '/Game/SoulCharger/Obra', 'asset_name': 'BP_StageRunner_SC', 'asset_type': {'refPath': '/Script/Engine.Actor'}})[0]
    B = {'refPath': BP}
    ok, cdo = T(BT + 'get_default_object', {'blueprint': B})
    cdor = rp(cdo)
    ok, cs = T(AT + 'get_components', {'actor': {'refPath': cdor}})
    have = [rp(c).split(':')[-1].replace('_GEN_VARIABLE', '') for c in (cs or [])]
    for n in ['Veil', 'Title', 'Ghost']:
        if n not in have:
            T(AT + 'add_component', {'owner': {'refPath': cdor}, 'component_type': {'refPath': '/Script/Engine.StaticMeshComponent'}, 'name': n})
    ok, cs = T(AT + 'get_components', {'actor': {'refPath': cdor}})
    cref = {}
    for c in (cs or []):
        cref[rp(c).split(':')[-1].replace('_GEN_VARIABLE', '')] = rp(c)
    out['comps'] = list(cref.keys())
    spec = {'Veil': ('/Engine/BasicShapes/Sphere.Sphere', '/Game/SoulCharger/Tour/M_TourVeil_SC.M_TourVeil_SC', (0, 0, 0), (0, 0, 0), (100, 100, 100), 32600),
            'Title': ('/Engine/BasicShapes/Plane.Plane', '/Game/SoulCharger/Tour/MI_TourTitle_ENTERING.MI_TourTitle_ENTERING', (300, 0, 0), (0, 90, 90), (4, 1, 1), 32700),
            'Ghost': ('/Game/SoulCharger/Mechanics/ChargeRing/SM_ChargeRing_SC.SM_ChargeRing_SC', None, (0, 0, 0), (0, 0, 0), (1, 1, 1), 200)}
    for n, (mesh, mat, loc, rot, sc, sort) in spec.items():
        r = cref.get(n)
        if not r:
            LOG.append('sin componente ' + n)
            continue
        S(r, {'StaticMesh': mesh})
        if mat:
            S(r, {'OverrideMaterials': [mat]})
        S(r, {'CastShadow': False})
        S(r, {'TranslucencySortPriority': sort})
        S(r, {'BodyInstance': {'collisionEnabled': 'NoCollision'}})
        S(r, {'relativeLocation': '(X=%.3f,Y=%.3f,Z=%.3f)' % loc})
        S(r, {'relativeRotation': '(Pitch=%.3f,Yaw=%.3f,Roll=%.3f)' % rot})
        S(r, {'relativeScale3D': '(X=%.3f,Y=%.3f,Z=%.3f)' % sc})
    ok, vs = T(BT + 'list_variables', {'blueprint': B})
    ya = str(vs)
    nv = 0
    for n, t, ed in VARS:
        if ("'" + n + "'") in ya or ('"' + n + '"') in ya:
            continue
        if T(BT + 'add_variable', {'blueprint': B, 'name': n, 'type_name': t})[0]:
            nv += 1
    if "'TitleMI'" not in ya and '"TitleMI"' not in ya:
        T(BT + 'add_object_variable', {'blueprint': B, 'name': 'TitleMI', 'object_class': {'refPath': '/Script/Engine.MaterialInterface'}})
        nv += 1
    out['vars_new'] = nv
    for n, t, ed in VARS + [('TitleMI', 'obj', 1)]:
        if ed:
            T(BT + 'set_variable_instance_editable', {'blueprint': B, 'variable_name': n, 'instance_editable': True})
            T(BT + 'set_variable_category', {'blueprint': B, 'variable_name': n, 'category': 'Ensayo'})
    T(BT + 'compile_blueprint', {'blueprint': B})
    ok, src = T(AS + 'read_file', {'file_path': SRC})
    d = src if isinstance(src, dict) else json.loads(src)
    ok, gs = T(BT + 'list_graphs', {'blueprint': B})
    gstr = str(gs)
    wr = {}
    for g in ORDER:
        if (':' + g + "'") not in gstr and (':' + g + '"') not in gstr:
            T(BT + 'add_function_graph', {'blueprint': B, 'graph_name': g})
            for pn, pt in PARAMS.get(g, []):
                T(BT + 'add_function_param', {'graph': {'refPath': BP + ':' + g}, 'param_name': pn, 'param_type': pt, 'input_param': True})
    for g in ORDER:
        G = {'refPath': BP + ':' + g}
        ok, ns = T(BT + 'find_nodes', {'graph': G, 'title': ''})
        if len(ns or []) <= 1:
            wr[g] = T(BT + 'write_graph_dsl', {'graph': G, 'code': d[g]})[0]
        else:
            wr[g] = 'ya tiene ' + str(len(ns))
    EG = {'refPath': BP + ':EventGraph'}
    ok, ns = T(BT + 'find_nodes', {'graph': EG, 'title': ''})
    conn = 0
    for n in (ns or []):
        pass
    refs = [rp(n) for n in (ns or [])]
    if all('K2Node_Event' in r for r in refs):
        for r in refs:
            T(BT + 'delete_node', {'node': {'refPath': r}})
        wr['EventGraph'] = T(BT + 'write_graph_dsl', {'graph': EG, 'code': d['EventGraph']})[0]
    else:
        wr['EventGraph'] = 'no vacio: ' + str(len(refs))
    out['write'] = wr
    ok, r = T(BT + 'compile_blueprint', {'blueprint': B})
    out['compile'] = str(r)[:300]
    out['log'] = LOG[:25]
    return out
  except BaseException as e:
    return {'err': 'run :: ' + str(e)[:300], 'log': LOG}
