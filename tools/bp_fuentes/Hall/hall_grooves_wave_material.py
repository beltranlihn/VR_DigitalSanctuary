import json
# hall_grooves_wave_material.py - la onda de las líneas de luz del Hall (pedido de Beltrán 2026-09-30).
# 1) MPC_Hall_SC gana GrooveFront (default 2000 = todo encendido, como hoy) y DustLight (0) CONSERVANDO los ids de los viejos.
# 2) M_Hall_Interior_SC: Custom nuevo HallGrooveRevealPS ENTRE HallGroovesPS (Custom_1) y la entrada G de HallInteriorPS
#    (Custom_0), con P = LocalPosition existente, Front = CollectionParameter(GrooveFront), GrooveSoft 60, GroovePulse 1,2.
# Custom por PRIMERA LÍNEA del code (gotcha §526). Idempotente. Sin `result = run()`. Recompilar aparte, sin PIE.
MPC = '/Game/SoulCharger/Mechanics/Hall/MPC_Hall_SC.MPC_Hall_SC'
M = '/Game/SoulCharger/Mechanics/Hall/M_Hall_Interior_SC.M_Hall_Interior_SC'
SRC = 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/Hall/HallGrooveRevealPS.txt'
GID = '9E4ABC17-2C7A-4156-9382-20B4D1751F6A'
MT = 'editor_toolset.toolsets.material.MaterialTools.'
OT = 'editor_toolset.toolsets.object.ObjectTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
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
def C(a, ao, b, bi):
    return T(MT + 'connect_expressions', {'from_expression': {'refPath': a}, 'from_output_name': ao, 'to_expression': {'refPath': b}, 'to_input_name': bi})[0]
def add(cls, x, y):
    ok, e = T(MT + 'add_expression', {'material_or_function': {'refPath': M}, 'expression_class': {'refPath': '/Script/Engine.' + cls}, 'x': x, 'y': y})
    return rp(e) if ok else None
def run():
  try:
    out = {}
    ok, code = T(AS + 'read_file', {'file_path': SRC})
    if not ok or not str(code).startswith('// HallGrooveRevealPS'):
        return {'err': 'no pude leer el shader: no toco nada', 'log': LOG}
    # 1) MPC
    mp = G(MPC, ['ScalarParameters'])
    sc = mp['ScalarParameters'] if mp and 'ScalarParameters' in mp else None
    if sc is None:
        return {'err': 'no pude leer el MPC', 'log': LOG}
    out['mpc_antes'] = [(p['parameterName'], p['id']) for p in sc]
    sc2 = [dict(p) for p in sc]
    if not any(p['parameterName'] == 'GrooveFront' for p in sc):
        sc2.append({'parameterName': 'GrooveFront', 'defaultValue': 2000.0, 'id': GID})
    if not any(p['parameterName'] == 'DustLight' for p in sc):
        sc2.append({'parameterName': 'DustLight', 'defaultValue': 0.0, 'id': 'F65416BF-23E0-4117-BC92-F37D8FB701B0'})
    if len(sc2) != len(sc):
        S(MPC, {'ScalarParameters': sc2})
    mp2 = G(MPC, ['ScalarParameters'])
    out['mpc_despues'] = [(p['parameterName'], p['id'], p['defaultValue']) for p in mp2['ScalarParameters']] if mp2 else None
    # 2) material
    ok, ex = T(MT + 'get_expressions', {'material_or_function': {'refPath': M}})
    refs = [rp(e) for e in (ex or [])]
    cus = {}
    lp = None
    params = {}
    colp = None
    for r in refs:
        n = r.split(':')[-1]
        if n.startswith('MaterialExpressionCustom'):
            g = G(r, ['code'])
            c = str(g['code']) if g and 'code' in g else ''
            for key in ('// HallInteriorPS', '// HallGroovesPS', '// HallGrooveRevealPS'):
                if c.startswith(key):
                    cus[key] = r
        elif n.startswith('MaterialExpressionLocalPosition') and lp is None:
            lp = r
        elif n.startswith('MaterialExpressionScalarParameter'):
            g = G(r, ['parameterName'])
            if g and 'parameterName' in g:
                params[str(g['parameterName'])] = r
        elif n.startswith('MaterialExpressionCollectionParameter'):
            g = G(r, ['parameterName'])
            if g and str(g.get('parameterName', '')) == 'GrooveFront':
                colp = r
    out['customs'] = dict((k, v.split(':')[-1]) for k, v in cus.items())
    if '// HallInteriorPS' not in cus or '// HallGroovesPS' not in cus or not lp:
        out['err'] = 'faltan Custom interior/grooves o LocalPosition'
        out['log'] = LOG
        return out
    rev = cus.get('// HallGrooveRevealPS')
    if not rev:
        rev = add('MaterialExpressionCustom', -700, 300)
        S(rev, {'Description': 'HallGrooveRevealPS', 'OutputType': 'CMOT_Float3', 'Code': str(code)})
        S(rev, {'Inputs': []})
        S(rev, {'Inputs': [{'inputName': n} for n in ['G', 'P', 'Front', 'Soft', 'Pulse']]})
    if not colp:
        colp = add('MaterialExpressionCollectionParameter', -1000, 450)
        S(colp, {'Collection': MPC})
        S(colp, {'ParameterName': 'GrooveFront'})
        S(colp, {'ParameterId': GID})
    if 'GrooveSoft' not in params:
        params['GrooveSoft'] = add('MaterialExpressionScalarParameter', -1000, 550)
        S(params['GrooveSoft'], {'ParameterName': 'GrooveSoft', 'DefaultValue': 60.0})
    if 'GroovePulse' not in params:
        params['GroovePulse'] = add('MaterialExpressionScalarParameter', -1000, 650)
        S(params['GroovePulse'], {'ParameterName': 'GroovePulse', 'DefaultValue': 1.2})
    out['con'] = [C(cus['// HallGroovesPS'], '', rev, 'G'), C(lp, 'XYZ', rev, 'P'), C(colp, '', rev, 'Front'),
                  C(params['GrooveSoft'], '', rev, 'Soft'), C(params['GroovePulse'], '', rev, 'Pulse'),
                  C(rev, '', cus['// HallInteriorPS'], 'G')]
    out['colp'] = G(colp, ['ParameterName', 'ParameterId'])
    ok, ins = T(MT + 'get_expression_inputs', {'expression': {'refPath': cus['// HallInteriorPS']}})
    out['interior_inputs'] = str(ins)[:600]
    out['log'] = LOG[:20]
    return out
  except BaseException as e:
    return {'err': 'run :: ' + str(e)[:300], 'log': LOG}
