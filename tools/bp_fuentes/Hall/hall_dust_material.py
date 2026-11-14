import json
# hall_dust_material.py - M_HallDust_SC: HallLight -> max(HallLight, DustLight), así las motas se ven en el viaje a oscuras.
# MODO 'leer': devuelve las expresiones y las entradas de cada una (para encontrar a quién alimenta HallLight).
# MODO 'aplicar': agrega CollectionParameter(DustLight) + Max y reengancha el consumidor. Requiere DustLight YA en el MPC
# (hall_grooves_wave_material.py lo agrega junto con GrooveFront). Idempotente. Sin `result = run()`.
MODO = 'leer'
CONSUMER = ''        # refPath de la expresión que hoy recibe HallLight (lo da el modo leer)
CONS_INPUT = ''      # nombre de su entrada (A/B/...)
MPC = '/Game/SoulCharger/Mechanics/Hall/MPC_Hall_SC.MPC_Hall_SC'
M = '/Game/SoulCharger/Mechanics/Hall/M_HallDust_SC.M_HallDust_SC'
DID = 'F65416BF-23E0-4117-BC92-F37D8FB701B0'
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
        LOG.append(name.split('.')[-1] + ' :: ' + str(e)[:200])
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
def run():
  try:
    out = {}
    ok, ex = T(MT + 'get_expressions', {'material_or_function': {'refPath': M}})
    refs = [rp(e) for e in (ex or [])]
    hl, dl = None, None
    for r in refs:
        if r.split(':')[-1].startswith('MaterialExpressionCollectionParameter'):
            g = G(r, ['ParameterName'])
            n = str(g['ParameterName']) if g and 'ParameterName' in g else ''
            if n == 'HallLight':
                hl = r
            if n == 'DustLight':
                dl = r
    out['hl'] = hl
    out['dl'] = dl
    if MODO != 'aplicar':
        ins = {}
        for r in refs:
            ok, v = T(MT + 'get_expression_inputs', {'expression': {'refPath': r}})
            ins[r.split(':')[-1]] = str(v)[:300]
        out['inputs'] = ins
        ok, em = T(MT + 'get_property_input', {'material': {'refPath': M}, 'material_property': 'MP_EmissiveColor'})
        out['emisivo'] = em
        out['log'] = LOG[:20]
        return out
    if not hl or not CONSUMER:
        return {'err': 'falta HallLight o CONSUMER', 'log': LOG}
    if not dl:
        ok, e = T(MT + 'add_expression', {'material_or_function': {'refPath': M}, 'expression_class': {'refPath': '/Script/Engine.MaterialExpressionCollectionParameter'}, 'x': -900, 'y': 500})
        dl = rp(e)
        S(dl, {'Collection': MPC})
        S(dl, {'ParameterName': 'DustLight'})
        S(dl, {'ParameterId': DID})
        ok, e = T(MT + 'add_expression', {'material_or_function': {'refPath': M}, 'expression_class': {'refPath': '/Script/Engine.MaterialExpressionMax'}, 'x': -650, 'y': 450})
        mx = rp(e)
        T(MT + 'connect_expressions', {'from_expression': {'refPath': hl}, 'from_output_name': '', 'to_expression': {'refPath': mx}, 'to_input_name': 'A'})
        T(MT + 'connect_expressions', {'from_expression': {'refPath': dl}, 'from_output_name': '', 'to_expression': {'refPath': mx}, 'to_input_name': 'B'})
        T(MT + 'connect_expressions', {'from_expression': {'refPath': mx}, 'from_output_name': '', 'to_expression': {'refPath': CONSUMER}, 'to_input_name': CONS_INPUT})
        out['max'] = mx
    out['dl_props'] = G(dl, ['ParameterName', 'ParameterId'])
    ok, v = T(MT + 'get_expression_inputs', {'expression': {'refPath': CONSUMER}})
    out['consumer_inputs'] = str(v)[:400]
    out['log'] = LOG[:20]
    return out
  except BaseException as e:
    return {'err': 'run :: ' + str(e)[:300], 'log': LOG}
