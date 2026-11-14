import json
# turnB2_build.py - Turno B (compartir): BP_SoulFish_SC (halo), BP_Obra_SC (FlowShare y compania), BP_StageRunner_SC (SayClip).
# Corre con OTRO nivel abierto (Test_Results) para no reinstanciar actores colocados. Idempotente por grafos/variables.
BT = 'editor_toolset.toolsets.blueprint.BlueprintTools.'
AT = 'editor_toolset.toolsets.actor.ActorTools.'
OT = 'editor_toolset.toolsets.object.ObjectTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
SC = 'editor_toolset.toolsets.scene.SceneTools.'
DIR = 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/Obra/'
FISH = '/Game/SoulCharger/Obra/BP_SoulFish_SC.BP_SoulFish_SC'
OBRA = '/Game/SoulCharger/Obra/BP_Obra_SC.BP_Obra_SC'
RUN = '/Game/SoulCharger/Obra/BP_StageRunner_SC.BP_StageRunner_SC'
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
def src(f):
    ok, s = T(AS + 'read_file', {'file_path': DIR + f})
    return s if isinstance(s, dict) else json.loads(s)
def clear(g):
    ok, ns = T(BT + 'find_nodes', {'graph': g, 'title': ''})
    k = 0
    for n in (ns or []):
        r = rp(n)
        if 'FunctionEntry' in r:
            continue
        if T(BT + 'delete_node', {'node': {'refPath': r}})[0]:
            k += 1
    return k
def ensure_graph(bp, g, params, gstr):
    if (':' + g + "'") not in gstr:
        T(BT + 'add_function_graph', {'blueprint': {'refPath': bp}, 'graph_name': g})
        for pn, pt in params:
            T(BT + 'add_function_param', {'graph': {'refPath': bp + ':' + g}, 'param_name': pn, 'param_type': pt, 'input_param': True})
def write(bp, g, code):
    G = {'refPath': bp + ':' + g}
    dl = clear(G)
    return [dl, T(BT + 'write_graph_dsl', {'graph': G, 'code': code})[0]]
def add_vars(bp, vars_):
    B = {'refPath': bp}
    ok, vs = T(BT + 'list_variables', {'blueprint': B})
    ya = str(vs)
    nv = []
    for n, t, ed in vars_:
        if ("'" + n + "'") in ya:
            continue
        if T(BT + 'add_variable', {'blueprint': B, 'name': n, 'type_name': t})[0]:
            nv.append(n)
        if ed:
            T(BT + 'set_variable_instance_editable', {'blueprint': B, 'variable_name': n, 'instance_editable': True})
    return nv
def run():
  try:
    out = {}
    ok, cur = T(SC + 'get_current_level', {})
    if 'Obra' in str(cur) or 'Test_' in str(cur) and 'Results' not in str(cur):
        T(SC + 'load_level', {'level_path': '/Game/SoulCharger/Mechanics/Results/Test_Results'})
    ok, cur = T(SC + 'get_current_level', {})
    out['nivel'] = cur
    if 'Results' not in str(cur):
        return {'err': 'no pude abrir Test_Results', 'log': LOG}
    # ---------- A. el pez: halo
    B = {'refPath': FISH}
    ok, cdo = T(BT + 'get_default_object', {'blueprint': B})
    cdor = rp(cdo)
    ok, cs = T(AT + 'get_components', {'actor': {'refPath': cdor}})
    if 'Halo_GEN_VARIABLE' not in str(cs):
        T(AT + 'add_component', {'owner': {'refPath': cdor}, 'component_type': {'refPath': '/Script/Engine.StaticMeshComponent'}, 'name': 'Halo'})
        ok, cs = T(AT + 'get_components', {'actor': {'refPath': cdor}})
    href = [rp(c) for c in (cs or []) if 'Halo_GEN_VARIABLE' in rp(c)]
    if href:
        h = href[0]
        S(h, {'StaticMesh': '/Engine/BasicShapes/Plane.Plane'})
        S(h, {'OverrideMaterials': ['/Game/SoulCharger/Obra/MI_FishSpark_SC.MI_FishSpark_SC']})
        S(h, {'CastShadow': False})
        S(h, {'TranslucencySortPriority': 64})
        S(h, {'BodyInstance': {'collisionEnabled': 'NoCollision'}})
        S(h, {'bVisible': False})
        S(h, {'relativeScale3D': '(X=0.300,Y=0.300,Z=0.300)'})
    out['fish_vars'] = add_vars(FISH, [('HaloOn', 'bool', 0), ('HaloAmt', 'float', 1), ('HaloSize', 'float', 1)])
    T(BT + 'compile_blueprint', {'blueprint': B})
    ok, cdo = T(BT + 'get_default_object', {'blueprint': B})
    S(rp(cdo), {'HaloAmt': 0.55})
    S(rp(cdo), {'HaloSize': 0.3})
    f3 = src('fish3.json')
    ok, gs = T(BT + 'list_graphs', {'blueprint': B})
    ensure_graph(FISH, 'FishHalo', [], str(gs))
    out['fish_w'] = {'FishHalo': write(FISH, 'FishHalo', f3['FishHalo']), 'FishSparks': write(FISH, 'FishSparks', f3['FishSparks'])}
    ok, r = T(BT + 'compile_blueprint', {'blueprint': B})
    # ---------- B. la Obra
    B = {'refPath': OBRA}
    out['obra_vars'] = add_vars(OBRA, [('ShareSt', 'int', 0), ('Shared', 'bool', 0), ('SharePick', 'int', 0), ('ShareT', 'float', 0), ('LastPressN', 'int', 0),
        ('ExploreT', 'float', 1), ('ShareFW', 'float', 1), ('ShareDrop', 'float', 1), ('SwimTime', 'float', 1), ('AwayTime', 'float', 1),
        ('ShVO', 'bool', 0), ('ShFree', 'bool', 0), ('ShDoor', 'bool', 0), ('ShFade', 'bool', 0), ('ConstOn', 'bool', 0), ('ConstVO', 'bool', 0), ('ConstVO2', 'bool', 0),
        ('DoorPt', 'Vector', 0), ('AwayPt', 'Vector', 0), ('SwimFrom', 'Vector', 0), ('DebugShare', 'int', 1)])
    T(BT + 'compile_blueprint', {'blueprint': B})
    ok, cdo = T(BT + 'get_default_object', {'blueprint': B})
    c = rp(cdo)
    for k, v in [('ExploreT', 25.0), ('ShareFW', 30.0), ('ShareDrop', 64.0), ('SwimTime', 4.0), ('AwayTime', 3.0), ('DebugShare', -1), ('ResultsTime', 150.0)]:
        if not S(c, {k: v}):
            LOG.append('cdo ' + k)
    d = src('turnB2.json')
    ok, gs = T(BT + 'list_graphs', {'blueprint': B})
    gstr = str(gs)
    newg = [('FlowShare', []), ('ShareGo', [('S', 'int')]), ('SharePickStep', []), ('SharePick', [('P', 'int')]), ('ShareAnswer', []), ('ShareFree', []),
            ('ShareSwim', [('T', 'float')]), ('SharePlace', []), ('FlowConst', []), ('AlmaResults', []), ('ShareResOut', []), ('ShareExit', [])]
    for g, ps in newg:
        ensure_graph(OBRA, g, ps, gstr)
    order = ['ShareGo', 'ShareSwim', 'ShareFree', 'ShareExit', 'ShareResOut', 'AlmaResults', 'SharePlace', 'SharePick', 'SharePickStep', 'ShareAnswer', 'FlowShare', 'FlowConst', 'AlmaSpeak', 'FlowBye', 'ExitCheck', 'FinalFlow']
    wr = {}
    for g in order:
        wr[g] = write(OBRA, g, d[g])
    out['obra_w'] = wr
    ok, r = T(BT + 'compile_blueprint', {'blueprint': B})
    out['obra_compile'] = str(r)[:200]
    # ---------- C. el runner: SayClip
    rj = src('runner.json')
    out['run_w'] = write(RUN, 'RSay', rj['RSay'].replace('Class|BPAlmaSC|PlayClip', 'Class|BPAlmaSC|SayClip'))
    T(BT + 'compile_blueprint', {'blueprint': {'refPath': RUN}})
    out['save'] = T(AS + 'save_assets', {'asset_paths': ['/Game/SoulCharger/Obra/BP_SoulFish_SC', '/Game/SoulCharger/Obra/BP_Obra_SC', '/Game/SoulCharger/Obra/BP_StageRunner_SC']})[0]
    out['log'] = LOG[:25]
    return out
  except BaseException as e:
    return {'err': 'run :: ' + str(e)[:300], 'log': LOG}
