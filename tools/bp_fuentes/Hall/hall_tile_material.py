import json
# hall_tile_material.py - M_Hall_Tile_SC gana Lift (WPO en Z, cm) y TileGlow (emisivo extra = TileColor.RGB x TileGlow,
# sumado DESPUES de lo que hoy entra al emisivo). Los MI de Beltran no se tocan (parametros nuevos, default 0 = igual que hoy).
# MODO 'leer' -> devuelve expresiones de parametro + lo que alimenta al emisivo (para saber su salida). 'aplicar' -> edita.
# Idempotente por parameterName. Sin `result = run()`. Recompilar aparte, SIN PIE (y sin MID vivas: no hay en editor).
MODO = 'leer'
EMIS_OUT = ''          # nombre de la salida de la expresion que hoy alimenta al emisivo (lo da el modo leer)
M = '/Game/SoulCharger/Mechanics/Hall/M_Hall_Tile_SC.M_Hall_Tile_SC'
MT = 'editor_toolset.toolsets.material.MaterialTools.'
OT = 'editor_toolset.toolsets.object.ObjectTools.'
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
def S(ref, vals):
    return T(OT + 'set_properties', {'instance': {'refPath': ref}, 'values': json.dumps(vals)})[0]
def G(ref, props):
    ok, v = T(OT + 'get_properties', {'instance': {'refPath': ref}, 'properties': props})
    if not ok or v is None:
        return None
    try:
        return json.loads(v) if isinstance(v, str) else v
    except BaseException:
        return None
def rp(x):
    return x['refPath'] if isinstance(x, dict) and 'refPath' in x else str(x)
def add(cls, x, y):
    ok, e = T(MT + 'add_expression', {'material_or_function': {'refPath': M}, 'expression_class': {'refPath': '/Script/Engine.' + cls}, 'x': x, 'y': y})
    return rp(e) if ok else None
def run():
  try:
    out = {}
    ok, ex = T(MT + 'get_expressions', {'material_or_function': {'refPath': M}})
    refs = [rp(e) for e in (ex or [])]
    params = {}
    for r in refs:
        n = r.split(':')[-1]
        if n.startswith('MaterialExpressionScalarParameter') or n.startswith('MaterialExpressionVectorParameter'):
            g = G(r, ['parameterName'])
            if g and 'parameterName' in g:
                params[str(g['parameterName'])] = r
    out['n_expr'] = len(refs)
    out['params'] = sorted(params.keys())
    ok, em = T(MT + 'get_property_input', {'material': {'refPath': M}, 'material_property': 'MP_EmissiveColor'})
    out['emisivo'] = em
    ok, wp = T(MT + 'get_property_input', {'material': {'refPath': M}, 'material_property': 'MP_WorldPositionOffset'})
    out['wpo'] = wp
    if MODO != 'aplicar':
        out['log'] = LOG[:20]
        return out
    src = None
    if isinstance(em, dict):
        for k in ('expression', 'Expression', 'refPath'):
            if k in em:
                src = rp(em[k]) if k != 'refPath' else em[k]
                break
    hechos = []
    if 'Lift' not in params:
        lift = add('MaterialExpressionScalarParameter', -900, 900)
        S(lift, {'parameterName': 'Lift', 'defaultValue': 0.0})
        up = add('MaterialExpressionConstant3Vector', -900, 1000)
        S(up, {'constant': {'r': 0.0, 'g': 0.0, 'b': 1.0, 'a': 0.0}})
        mul = add('MaterialExpressionMultiply', -650, 950)
        T(MT + 'connect_expressions', {'from_expression': {'refPath': up}, 'from_output_name': '', 'to_expression': {'refPath': mul}, 'to_input_name': 'A'})
        T(MT + 'connect_expressions', {'from_expression': {'refPath': lift}, 'from_output_name': '', 'to_expression': {'refPath': mul}, 'to_input_name': 'B'})
        T(MT + 'connect_to_output', {'expression': {'refPath': mul}, 'output_name': '', 'material_property': 'MP_WorldPositionOffset'})
        hechos.append('Lift -> WPO')
    if 'TileGlow' not in params and src and 'TileColor' in params:
        tg = add('MaterialExpressionScalarParameter', -900, 700)
        S(tg, {'parameterName': 'TileGlow', 'defaultValue': 0.0})
        m2 = add('MaterialExpressionMultiply', -650, 700)
        T(MT + 'connect_expressions', {'from_expression': {'refPath': params['TileColor']}, 'from_output_name': 'RGB', 'to_expression': {'refPath': m2}, 'to_input_name': 'A'})
        T(MT + 'connect_expressions', {'from_expression': {'refPath': tg}, 'from_output_name': '', 'to_expression': {'refPath': m2}, 'to_input_name': 'B'})
        ad = add('MaterialExpressionAdd', -300, 650)
        T(MT + 'connect_expressions', {'from_expression': {'refPath': src}, 'from_output_name': EMIS_OUT, 'to_expression': {'refPath': ad}, 'to_input_name': 'A'})
        T(MT + 'connect_expressions', {'from_expression': {'refPath': m2}, 'from_output_name': '', 'to_expression': {'refPath': ad}, 'to_input_name': 'B'})
        T(MT + 'connect_to_output', {'expression': {'refPath': ad}, 'output_name': '', 'material_property': 'MP_EmissiveColor'})
        hechos.append('TileGlow -> emisivo (sumado a ' + src.split(':')[-1] + ')')
    out['hechos'] = hechos
    ok, em2 = T(MT + 'get_property_input', {'material': {'refPath': M}, 'material_property': 'MP_EmissiveColor'})
    ok, wp2 = T(MT + 'get_property_input', {'material': {'refPath': M}, 'material_property': 'MP_WorldPositionOffset'})
    out['emisivo_despues'] = em2
    out['wpo_despues'] = wp2
    out['log'] = LOG[:20]
    return out
  except BaseException as e:
    return {'err': 'run :: ' + str(e)[:300], 'log': LOG}
