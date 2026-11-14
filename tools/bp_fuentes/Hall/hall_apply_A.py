import json
# hall_apply_A.py - esqueleto de BP_HallDirector_SC desde hall_director_plan.json:
# crea el BP (Actor), las 7 flechas (paradas) + 5 planos de titulo, las variables (categoria Default, editable) y los
# grafos de funcion VACIOS (sin parametros: van en hall_apply_B.py, en OTRA llamada — gotcha 304).
# Se pega ENTERO como `script` de execute_tool_script. SIN `result = run()` (gotcha 493). IDEMPOTENTE. Nunca levanta.
BT = 'editor_toolset.toolsets.blueprint.BlueprintTools.'
AT = 'editor_toolset.toolsets.actor.ActorTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
PLAN = 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/Hall/hall_director_plan.json'
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
        LOG.append(name.split('.')[-1] + ' :: ' + str(e)[:220])
        return False, None
def nombres(lst):
    out = []
    for x in (lst or []):
        if isinstance(x, dict):
            n = x['name'] if 'name' in x else (x['Name'] if 'Name' in x else (x['refPath'] if 'refPath' in x else ''))
        else:
            n = str(x)
        out.append(n.split('.')[-1].split(':')[-1])
    return out
def run():
  try:
    ok, txt = T(AS + 'read_file', {'file_path': PLAN})
    if not ok:
        return {'err': 'no pude leer el plan', 'log': LOG}
    plan = json.loads(txt)
    out = {}
    BPP = plan['blueprint']
    folder, NAME = BPP.rsplit('/', 1)
    BPo = {'refPath': BPP + '.' + NAME}
    ok, ex = T(AS + 'exists', {'path': BPP})
    if not ex:
        ok, r = T(BT + 'create', {'folder_path': folder, 'asset_name': NAME, 'asset_type': {'refPath': '/Script/Engine.Actor'}})
        out['bp_creado'] = ok
        if not ok:
            out['log'] = LOG
            return out
    ok, cdo = T(BT + 'get_default_object', {'blueprint': BPo})
    cdor = cdo['refPath'] if isinstance(cdo, dict) and 'refPath' in cdo else cdo
    out['cdo'] = cdor
    ok, comps = T(AT + 'get_components', {'actor': {'refPath': cdor}})
    ya = [n.replace('_GEN_VARIABLE', '') for n in nombres(comps)]
    creados = []
    for a in plan['arrows']:
        if a['name'] not in ya:
            if T(AT + 'add_component', {'owner': {'refPath': cdor}, 'component_type': {'refPath': '/Script/Engine.ArrowComponent'}, 'name': a['name']})[0]:
                creados.append(a['name'])
    for t in plan['titles']:
        if t['name'] not in ya:
            if T(AT + 'add_component', {'owner': {'refPath': cdor}, 'component_type': {'refPath': '/Script/Engine.StaticMeshComponent'}, 'name': t['name']})[0]:
                creados.append(t['name'])
    out['componentes_creados'] = creados
    ok, vs = T(BT + 'list_variables', {'blueprint': BPo})
    ya = nombres(vs)
    nuevas = []
    for v in plan['vars']:
        n = v['name']
        if n in ya:
            continue
        cont = v['container'] if 'container' in v else None
        if v['type'].startswith('obj:'):
            args = {'blueprint': BPo, 'name': n, 'object_class': {'refPath': v['type'][4:]}}
            if cont:
                args['container_type'] = cont
            ok, r = T(BT + 'add_object_variable', args)
        else:
            args = {'blueprint': BPo, 'name': n, 'type_name': v['type']}
            if cont:
                args['container_type'] = cont
            ok, r = T(BT + 'add_variable', args)
        if ok:
            nuevas.append(n)
    ed = 0
    for v in plan['vars']:
        if v['editable']:
            ed += T(BT + 'set_variable_instance_editable', {'blueprint': BPo, 'variable_name': v['name'], 'instance_editable': True})[0]
    out['variables_nuevas'] = len(nuevas)
    out['editables'] = ed
    ok, gs = T(BT + 'list_graphs', {'blueprint': BPo})
    yag = nombres(gs)
    fn = []
    for f in plan['functions']:
        if f['name'] not in yag:
            if T(BT + 'add_function_graph', {'blueprint': BPo, 'graph_name': f['name']})[0]:
                fn.append(f['name'])
    out['funciones_creadas'] = len(fn)
    ok, vs = T(BT + 'list_variables', {'blueprint': BPo})
    fin = nombres(vs)
    out['variables_total'] = len(fin)
    out['faltan'] = [v['name'] for v in plan['vars'] if v['name'] not in fin]
    out['duplicadas_0'] = [n for n in fin if n.endswith('_0')]
    ok, gs = T(BT + 'list_graphs', {'blueprint': BPo})
    out['grafos'] = nombres(gs)
    out['log'] = LOG[:30]
    return out
  except BaseException as e:
    return {'err': 'run :: ' + str(e)[:300], 'log': LOG}
