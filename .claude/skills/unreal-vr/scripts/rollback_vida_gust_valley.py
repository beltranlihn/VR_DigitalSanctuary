import json
# rollback_vida_gust_valley.py - QUITA la franja de la rafaga de M_BreathValley_SC: vuelve a conectar ValleyGradVS a la
# entrada VS de V_VI0 (el cableado de la v2 + capa viva). Se pega ENTERO como `script` de execute_tool_script.
# Idempotente, nunca levanta excepcion, NO recompila y NO BORRA (gotcha 401: borrar expresiones en la misma tanda que
# conexiones + recompile colgo el editor). Despues de esto GustLeanVS y los 5 Gust* quedan sueltos (no se compilan: nada
# los usa). Si se quieren borrar: recompile, y RECIEN DESPUES, en llamadas sueltas, delete_expression de cada ref que
# este script lista en 'para_borrar', y otro recompile.
MT = 'editor_toolset.toolsets.material.MaterialTools.'
OT = 'editor_toolset.toolsets.object.ObjectTools.'
MATR = '/Game/SoulCharger/Mechanics/Breath/Valley/M_BreathValley_SC.M_BreathValley_SC'
MAT = {'refPath': MATR}
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
def G(ref, props):
    ok, v = T(OT + 'get_properties', {'instance': {'refPath': ref}, 'properties': props})
    if not ok or v is None:
        return None
    try:
        return json.loads(v) if isinstance(v, str) else v
    except BaseException:
        return None
def run():
  try:
    return run2()
  except BaseException as e:
    return {'err': 'run :: ' + str(e)[:300], 'log': LOG}
def run2():
    ok, exprs = T(MT + 'get_expressions', {'material_or_function': MAT})
    if not ok or not exprs:
        return {'err': 'no pude leer las expresiones del valle', 'log': LOG}
    cust, byDesc, gust = {}, {}, []
    for e in exprs:
        r = e['refPath']
        cls = r.split(':')[-1]
        if 'Parameter' in cls:
            v = G(r, ['ParameterName'])
            if v and v['ParameterName'] in ('GustP', 'GustQ', 'GustR', 'GustK', 'GustS'):
                gust.append(r)
        elif 'Custom' in cls:
            v = G(r, ['Description'])
            if v:
                cust[v['Description']] = r
        else:
            v = G(r, ['Desc'])
            if v and v.get('Desc'):
                byDesc[v['Desc']] = r
    if 'ValleyGradVS' not in cust or 'V_VI0' not in byDesc:
        return {'err': 'no encuentro ValleyGradVS o V_VI0', 'log': LOG}
    ok, _ = T(MT + 'connect_expressions', {'from_expression': {'refPath': cust['ValleyGradVS']}, 'from_output_name': '', 'to_expression': {'refPath': byDesc['V_VI0']}, 'to_input_name': 'VS'})
    borrar = ([cust['GustLeanVS']] if 'GustLeanVS' in cust else []) + gust
    return {'vi0_a_valleygradvs': ok, 'para_borrar': [r.split(':')[-1] for r in borrar], 'log': LOG[:20]}
result = run()
