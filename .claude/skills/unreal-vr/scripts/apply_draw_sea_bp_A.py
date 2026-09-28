import json
# apply_draw_sea_bp_A.py - esqueleto de BP_DrawSea_SC desde oceano/draw_sea_bp.json (lo escribe draw_sea_sim.py):
# crea el BP (Actor), los 3 StaticMeshComponent (Sea, Sky, Dust) y las variables con su categoria y editable.
# Se pega ENTERO como `script` de execute_tool_script. IDEMPOTENTE (gotcha 489, corre dos veces): lista antes de crear.
# Nunca levanta excepcion (gotchas 60/418/231). Despues: compile_blueprint (llamada directa) y apply_draw_sea_bp_B.py.
# Las funciones y sus parametros NO van aca: add_function_graph + add_function_param por llamada directa (gotcha 304).
BT = 'editor_toolset.toolsets.blueprint.BlueprintTools.'
AT = 'editor_toolset.toolsets.actor.ActorTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
PLAN = 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/oceano/draw_sea_bp.json'
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
    BPR = BPP + '.' + NAME
    BPo = {'refPath': BPR}
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
    out['componentes_antes'] = ya
    creados = []
    for c in plan['components']:
        if c in ya:
            continue
        ok, r = T(AT + 'add_component', {'owner': {'refPath': cdor}, 'component_type': {'refPath': '/Script/Engine.StaticMeshComponent'}, 'name': c})
        if ok:
            creados.append(c)
    out['componentes_creados'] = creados
    ok, vs = T(BT + 'list_variables', {'blueprint': BPo})
    ya = nombres(vs)
    nuevas, cat_ok, ed_ok = [], 0, 0
    for v in plan['vars']:
        n = v['name']
        if n not in ya:
            if v['type'] == 'MaterialInterface':
                ok, r = T(BT + 'add_object_variable', {'blueprint': BPo, 'name': n, 'object_class': {'refPath': '/Script/Engine.MaterialInterface'}})
            else:
                ok, r = T(BT + 'add_variable', {'blueprint': BPo, 'name': n, 'type_name': v['type']})
            if not ok:
                continue
            nuevas.append(n)
        cat_ok += T(BT + 'set_variable_category', {'blueprint': BPo, 'variable_name': n, 'category': v['category']})[0]
        ed_ok += T(BT + 'set_variable_instance_editable', {'blueprint': BPo, 'variable_name': n, 'instance_editable': v['editable']})[0]
    out['variables_nuevas'] = len(nuevas)
    out['categorias_ok'] = '%d de %d' % (cat_ok, len(plan['vars']))
    out['editable_ok'] = '%d de %d' % (ed_ok, len(plan['vars']))
    ok, vs = T(BT + 'list_variables', {'blueprint': BPo})
    fin = nombres(vs)
    out['variables_total'] = len(fin)
    out['faltan'] = [v['name'] for v in plan['vars'] if v['name'] not in fin]
    out['duplicadas_0'] = [n for n in fin if n.endswith('_0')]
    out['log'] = LOG[:30]
    return out
  except BaseException as e:
    return {'err': 'run :: ' + str(e)[:300], 'log': LOG}
# Solo para el ensayo offline (dryrun lee `result`). AL PEGAR en execute_tool_script, QUITAR esta linea (gotcha 493).
result = run()
