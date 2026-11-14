# hallrunner_build.py (2026-10-01 ~01:15) - crea BP_HallRunner_SC (ensayo del Hall en Test_Hall) desde hallrunner.json y lo coloca. IDEMPOTENTE.
import json
BT = 'editor_toolset.toolsets.blueprint.BlueprintTools.'
AT = 'editor_toolset.toolsets.actor.ActorTools.'
OT = 'editor_toolset.toolsets.object.ObjectTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
SC = 'editor_toolset.toolsets.scene.SceneTools.'
PKG = '/Game/SoulCharger/Obra/BP_HallRunner_SC'
BP = PKG + '.BP_HallRunner_SC'
LVL = '/Game/SoulCharger/Mechanics/Hall/Test_Hall'
SRC = 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/Obra/hallrunner.json'
XF0 = {'location': {'x': 0, 'y': 0, 'z': 0}, 'rotation': {'x': 0, 'y': 0, 'z': 0, 'w': 1}, 'scale': {'x': 1, 'y': 1, 'z': 1}}
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
VARS = [('DebugStart', 'int', 1), ('DebugSoul', 'int', 1), ('Loop', 'bool', 1), ('LevelName', 'name', 1), ('FakeBio', 'bool', 1), ('KeepChargeTest', 'bool', 1),
        ('IsObra', 'bool', 0), ('RT', 'float', 0), ('Called', 'bool', 0), ('TitleSt', 'int', 0), ('AmbNow', 'int', 0), ('HudDone', 'bool', 0),
        ('HudAt', 'float', 0), ('EEGDone', 'bool', 0), ('EndT', 'float', 0), ('Ended', 'bool', 0), ('JumpStep', 'int', 0)]
PARAMS = {'HRPrep': [('S', 'int')], 'HRStep': [('Dt', 'float')]}
ORDER = ['HRPrep', 'HRStartHall', 'HRTitle', 'HRAmb', 'HRHud', 'HRBoot', 'HRStep']
def count():
    ok, a = T(SC + 'find_actors', {'name': '', 'tag': '', 'collision_channels': []})
    return len(a or []), [rp(x) for x in (a or [])]
def run():
  out = {}
  try:
    ok, pie = T('EditorToolset.EditorAppToolset.IsPIERunning', {})
    if pie:
        return {'err': 'PIE corriendo'}
    ok, cur = T(SC + 'get_current_level', {})
    if 'Test_Hall' not in str(cur):
        return {'err': 'no estoy en Test_Hall: ' + str(cur)}
    n0, refs0 = count()
    out['actores_antes'] = n0
    ok, ex = T(AS + 'exists', {'path': PKG})
    if not ex:
        out['create'] = T(BT + 'create', {'folder_path': '/Game/SoulCharger/Obra', 'asset_name': 'BP_HallRunner_SC', 'asset_type': {'refPath': '/Script/Engine.Actor'}})[0]
    B = {'refPath': BP}
    ok, cdo = T(BT + 'get_default_object', {'blueprint': B})
    cdor = rp(cdo)
    ok, cs = T(AT + 'get_components', {'actor': {'refPath': cdor}})
    have = [rp(c).split(':')[-1].replace('_GEN_VARIABLE', '') for c in (cs or [])]
    if 'Veil' not in have:
        T(AT + 'add_component', {'owner': {'refPath': cdor}, 'component_type': {'refPath': '/Script/Engine.StaticMeshComponent'}, 'name': 'Veil'})
    ok, cs = T(AT + 'get_components', {'actor': {'refPath': cdor}})
    vr = None
    for c in (cs or []):
        if rp(c).split(':')[-1].replace('_GEN_VARIABLE', '') == 'Veil':
            vr = rp(c)
    if vr:
        S(vr, {'StaticMesh': '/Engine/BasicShapes/Sphere.Sphere'})
        S(vr, {'OverrideMaterials': ['/Game/SoulCharger/Tour/M_TourVeil_SC.M_TourVeil_SC']})
        S(vr, {'CastShadow': False})
        S(vr, {'TranslucencySortPriority': 32600})
        S(vr, {'BodyInstance': {'collisionEnabled': 'NoCollision'}})
        S(vr, {'relativeScale3D': '(X=0.600,Y=0.600,Z=0.600)'})
        S(vr, {'bVisible': False})
        ok, v = T(OT + 'get_properties', {'instance': {'refPath': vr}, 'properties': ['bVisible', 'TranslucencySortPriority']})
        out['veil'] = str(v)
    ok, vs = T(BT + 'list_variables', {'blueprint': B})
    ya = str(vs)
    for n, t, ed in VARS:
        if ("'" + n + "'") in ya or ('"' + n + '"') in ya:
            continue
        T(BT + 'add_variable', {'blueprint': B, 'name': n, 'type_name': t})
    if "'AmbCur'" not in ya and '"AmbCur"' not in ya:
        T(BT + 'add_object_variable', {'blueprint': B, 'name': 'AmbCur', 'object_class': {'refPath': '/Script/Engine.AudioComponent'}})
    for n, t, ed in VARS:
        if ed:
            T(BT + 'set_variable_instance_editable', {'blueprint': B, 'variable_name': n, 'instance_editable': True})
            T(BT + 'set_variable_category', {'blueprint': B, 'variable_name': n, 'category': 'Ensayo'})
    T(BT + 'compile_blueprint', {'blueprint': B})
    ok, cdo = T(BT + 'get_default_object', {'blueprint': B})
    S(rp(cdo), {'DebugStart': -1, 'DebugSoul': 0, 'Loop': True, 'LevelName': 'Test_Hall', 'FakeBio': True, 'KeepChargeTest': False, 'EndT': -1.0, 'HudAt': -1.0, 'AmbNow': -2})
    ok, v = T(OT + 'get_properties', {'instance': {'refPath': rp(cdo)}, 'properties': ['DebugStart', 'DebugSoul', 'Loop', 'LevelName', 'FakeBio', 'KeepChargeTest']})
    out['cdo'] = str(v)
    ok, s = T(AS + 'read_file', {'file_path': SRC})
    s = str(s)
    if s[:1] == '\ufeff':
        s = s[1:]
    d = json.loads(s)
    ok, gs = T(BT + 'list_graphs', {'blueprint': B})
    gstr = str(gs)
    for g in ORDER:
        if (':' + g + "'") not in gstr and (':' + g + '"') not in gstr:
            T(BT + 'add_function_graph', {'blueprint': B, 'graph_name': g})
            for pn, pt in PARAMS.get(g, []):
                T(BT + 'add_function_param', {'graph': {'refPath': BP + ':' + g}, 'param_name': pn, 'param_type': pt, 'input_param': True})
    wr = {}
    for g in ORDER:
        G = {'refPath': BP + ':' + g}
        ok, ns = T(BT + 'find_nodes', {'graph': G, 'title': ''})
        if len(ns or []) <= 1:
            wr[g] = T(BT + 'write_graph_dsl', {'graph': G, 'code': d[g]})[0]
        else:
            wr[g] = 'ya tiene ' + str(len(ns))
    EG = {'refPath': BP + ':EventGraph'}
    ok, ns = T(BT + 'find_nodes', {'graph': EG, 'title': ''})
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
    out['save_bp'] = T(AS + 'save_assets', {'asset_paths': [PKG]})[0]
    placed = [r for r in refs0 if 'BP_HallRunner_SC' in r]
    if not placed:
        ok, r = T(SC + 'add_to_scene_from_asset', {'asset_path': PKG, 'name': 'HallRunner', 'xform': XF0})
        ref = rp(r)
        T(AT + 'set_label', {'actor': {'refPath': ref}, 'label': 'HallRunner'})
        T(AT + 'add_tag', {'actor': {'refPath': ref}, 'tag': 'TestOnly'})
        out['placed'] = ref
    else:
        out['placed'] = 'ya estaba: ' + placed[0]
    n1, refs1 = count()
    out['actores_despues'] = n1
    out['save_lvl'] = T(AS + 'save_assets', {'asset_paths': [LVL]})[0]
  except BaseException as e:
    LOG.append('run :: ' + str(e)[:300])
  out['log'] = LOG[:20]
  return out
