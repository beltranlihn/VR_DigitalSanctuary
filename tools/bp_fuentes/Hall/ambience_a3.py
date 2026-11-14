import json
# ambience_a3.py - crea BP_HallAmbience_SC (Actor, Mechanics/Hall): variables + funcion ArchSet(FogA) + compila + defaults del CDO +
# verifica los tipos de nodo que usa el .dsl. NO lo coloca (la estructura se arma ANTES de colocar, gotcha 402). Sin `result = run()`.
BT = 'editor_toolset.toolsets.blueprint.BlueprintTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
OT = 'editor_toolset.toolsets.object.ObjectTools.'
H = '/Game/SoulCharger/Mechanics/Hall'
BPP = H + '/BP_HallAmbience_SC'
BPo = {'refPath': BPP + '.BP_HallAmbience_SC'}
VARS = [('Director', 'obj:' + H + '/BP_HallDirector_SC.BP_HallDirector_SC_C', None, False),
        ('Fog', 'obj:' + H + '/BP_HallFog_SC.BP_HallFog_SC_C', None, False),
        ('Front', 'float', 1.0, False), ('Dust', 'float', 0.0, False), ('bArchHidden', 'bool', False, False),
        ('EnterStepIntro', 'int', 9, True), ('LeaveStepIntro', 'int', 27, True), ('EnterStepReturn', 'int', 3, True),
        ('LeaveStepExit', 'int', 1, True), ('DustLastStep', 'int', 5, True), ('DustExitStep', 'int', 2, True),
        ('ArchLastStep', 'int', 3, True), ('InTime', 'float', 6.0, True), ('OutTime', 'float', 4.0, True),
        ('DustIn', 'float', 2.0, True), ('DustOut', 'float', 3.0, True), ('FrontMax', 'float', 2000.0, True)]
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
        LOG.append(name.split('.')[-1] + ' :: ' + str(e)[:300])
        return False, None
def nombres(x):
    out = []
    for i in (x or []):
        s = i['refPath'] if isinstance(i, dict) and 'refPath' in i else (i.get('name') if isinstance(i, dict) else str(i))
        out.append(str(s).split(':')[-1].split('.')[-1])
    return out
def run():
  try:
    out = {}
    ok, ex = T(AS + 'exists', {'path': BPP})
    if not ex:
        out['creado'] = T(BT + 'create', {'folder_path': H, 'asset_name': 'BP_HallAmbience_SC', 'asset_type': {'refPath': '/Script/Engine.Actor'}})[0]
    ok, vs = T(BT + 'list_variables', {'blueprint': BPo})
    ya = nombres(vs)
    for n, t, d, e in VARS:
        if n in ya:
            continue
        if t.startswith('obj:'):
            T(BT + 'add_object_variable', {'blueprint': BPo, 'name': n, 'object_class': {'refPath': t[4:]}})
        else:
            T(BT + 'add_variable', {'blueprint': BPo, 'name': n, 'type_name': t})
        if e:
            T(BT + 'set_variable_instance_editable', {'blueprint': BPo, 'variable_name': n, 'instance_editable': True})
    ok, gs = T(BT + 'list_graphs', {'blueprint': BPo})
    if 'ArchSet' not in nombres(gs):
        T(BT + 'add_function_graph', {'blueprint': BPo, 'graph_name': 'ArchSet'})
        T(BT + 'add_function_param', {'graph': {'refPath': BPP + '.BP_HallAmbience_SC:ArchSet'}, 'param_name': 'FogA', 'param_type': 'float', 'input_param': True})
    T(BT + 'compile_blueprint', {'blueprint': BPo})
    ok, cdo = T(BT + 'get_default_object', {'blueprint': BPo})
    cdor = cdo['refPath'] if isinstance(cdo, dict) and 'refPath' in cdo else str(cdo)
    for n, t, d, e in VARS:
        if d is not None:
            T(OT + 'set_properties', {'instance': {'refPath': cdor}, 'values': json.dumps({n: d})})
    ok, v = T(OT + 'get_properties', {'instance': {'refPath': cdor}, 'properties': ['Front', 'EnterStepIntro', 'ArchLastStep', 'FrontMax', 'DustOut']})
    out['cdo'] = v
    ok, vs = T(BT + 'list_variables', {'blueprint': BPo})
    out['vars'] = len(nombres(vs))
    ok, gs = T(BT + 'list_graphs', {'blueprint': BPo})
    out['grafos'] = nombres(gs)
    EG = {'refPath': BPP + '.BP_HallAmbience_SC:EventGraph'}
    chk = {}
    for f in ['Rendering|SetActorHiddenInGame', 'Class|BPHallFogSC|GetAmount', 'Class|BPHallDirectorSC|GetMode', 'Actor|GetAllActorswithTag']:
        ok, r = T(BT + 'find_node_types', {'graph': EG, 'type_id_filter': f, 'context_pins': []})
        chk[f] = str(r)[:160]
    out['tipos'] = chk
    ok, ns = T(BT + 'find_nodes', {'graph': EG, 'title': ''})
    out['eg_nodos'] = nombres(ns)
    out['log'] = LOG[:12]
    return out
  except BaseException as e:
    return {'err': 'run :: ' + str(e)[:300], 'log': LOG}
