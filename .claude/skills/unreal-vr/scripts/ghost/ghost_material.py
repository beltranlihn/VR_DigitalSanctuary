import json
# ghost_material.py - arma M_Ghost_SC (el fantasma de las instrucciones y los botones del grabador).
# Se pega ENTERO como `script` de ProgrammaticToolset.execute_tool_script. Idempotente (parametros por nombre, Custom por
# Description). Nunca levanta excepcion (try/except BaseException, gotcha 231). NO recompila (gotcha 479: aparte).
# Patron de apply_alma_aura_material.py, sin plan externo. SIN `result = run()` al final (gotcha 493).
# Salida del Custom SIN AdditionalOutputs = '' (con 'return' falla y el error escapa del try; 2026-09-30).
# Unlit + ADITIVO (sin problemas de orden entre ecos) + borde fresnel: Emissive = Color * (Core + f*RimGain + Pressed*PressGain) * Opacity
MT = 'editor_toolset.toolsets.material.MaterialTools.'
OT = 'editor_toolset.toolsets.object.ObjectTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
FOLDER = '/Game/SoulCharger/Mechanics/Ghost'
NAME = 'M_Ghost_SC'
MATR = FOLDER + '/' + NAME + '.' + NAME
MAT = {'refPath': MATR}
FLAGS = {'shadingModel': 'MSM_Unlit', 'blendMode': 'BLEND_Additive', 'twoSided': False, 'bUseTranslucencyVertexFog': False}
PARAMS = [('Color', 'vector', [0.75, 0.85, 1.0, 1.0]), ('Opacity', 'scalar', 1.0), ('Pressed', 'scalar', 0.0),
          ('RimPow', 'scalar', 2.2), ('RimGain', 'scalar', 1.6), ('Core', 'scalar', 0.12), ('PressGain', 'scalar', 0.9)]
CODE = ('float3 n = normalize(N);\n'
        'float3 v = normalize(V);\n'
        'float f = pow(1.0 - saturate(abs(dot(n, v))), RimPow);\n'
        'float k = (Core + f * RimGain + Pressed * PressGain) * Opacity;\n'
        'return Color.rgb * k;')
INPUTS = ['N', 'V', 'Color', 'Opacity', 'Pressed', 'RimPow', 'RimGain', 'Core', 'PressGain']
LOG = []


def T(name, payload):
    try:
        v = execute_tool(name, json.dumps(payload))['returnValue']
        return True, v
    except BaseException as e:
        LOG.append(name.split('.')[-1] + ' :: ' + str(e)[:200])
        return False, None


def G(ref, props):
    ok, v = T(OT + 'get_properties', {'instance': {'refPath': ref}, 'properties': props})
    if not ok or v is None:
        return None
    try:
        return json.loads(v) if isinstance(v, str) else v
    except BaseException:
        return None


def S(ref, vals):
    return T(OT + 'set_properties', {'instance': {'refPath': ref}, 'values': json.dumps(vals)})[0]


def C(frm, fout, to, tin):
    return T(MT + 'connect_expressions', {'from_expression': {'refPath': frm}, 'from_output_name': fout,
                                          'to_expression': {'refPath': to}, 'to_input_name': tin})[0]


def run():
    try:
        return run2()
    except BaseException as e:
        return {'err': 'run :: ' + str(e)[:300], 'log': LOG}


def run2():
    out = {}
    ok, ex = T(AS + 'exists', {'path': FOLDER + '/' + NAME})
    if not ex:
        ok, r = T(MT + 'create_material', {'folder_path': FOLDER, 'asset_name': NAME})
        out['creado'] = ok
    S(MATR, FLAGS)
    out['flags'] = G(MATR, list(FLAGS.keys()))
    ok, exprs = T(MT + 'get_expressions', {'material_or_function': MAT})
    byParam, byDesc, cust = {}, {}, {}
    for e in (exprs or []):
        r = e['refPath']
        cls = r.split(':')[-1]
        if 'Parameter' in cls:
            v = G(r, ['ParameterName'])
            if v:
                byParam[v['ParameterName']] = r
        elif 'Custom' in cls:
            v = G(r, ['Description'])
            if v:
                cust[v['Description']] = r
        else:
            v = G(r, ['Desc'])
            if v and ('Desc' in v) and v['Desc']:
                byDesc[v['Desc']] = r
    for i, (name, kind, dflt) in enumerate(PARAMS):
        vals = {'Group': 'Ghost', 'DefaultValue': ({'r': dflt[0], 'g': dflt[1], 'b': dflt[2], 'a': dflt[3]} if kind == 'vector' else dflt)}
        if name in byParam:
            S(byParam[name], vals)
            continue
        cls = 'MaterialExpressionVectorParameter' if kind == 'vector' else 'MaterialExpressionScalarParameter'
        ok, r = T(MT + 'add_expression', {'material_or_function': MAT, 'expression_class': {'refPath': '/Script/Engine.' + cls},
                                          'x': -900, 'y': -500 + 110 * i})
        if not ok:
            continue
        vals['ParameterName'] = name
        S(r['refPath'], vals)
        byParam[name] = r['refPath']

    def helper(desc, cls, xx, yy):
        if desc in byDesc:
            return byDesc[desc]
        ok, r = T(MT + 'add_expression', {'material_or_function': MAT, 'expression_class': {'refPath': '/Script/Engine.' + cls}, 'x': xx, 'y': yy})
        if not ok:
            return None
        S(r['refPath'], {'Desc': desc})
        byDesc[desc] = r['refPath']
        return r['refPath']
    hn = helper('GH_N', 'MaterialExpressionVertexNormalWS', -900, -800)
    hv = helper('GH_V', 'MaterialExpressionCameraVectorWS', -900, -700)
    if 'GhostPS' not in cust:
        ok, r = T(MT + 'add_expression', {'material_or_function': MAT, 'expression_class': {'refPath': '/Script/Engine.MaterialExpressionCustom'}, 'x': -400, 'y': -400})
        if ok:
            cust['GhostPS'] = r['refPath']
    ps = cust['GhostPS'] if 'GhostPS' in cust else None
    if not ps:
        return {'err': 'no pude crear el Custom', 'log': LOG}
    S(ps, {'Description': 'GhostPS', 'OutputType': 'CMOT_Float3', 'Code': CODE})
    S(ps, {'AdditionalOutputs': []})
    S(ps, {'Inputs': []})
    S(ps, {'Inputs': [{'inputName': n} for n in INPUTS]})
    con = 0
    con += C(hn, '', ps, 'N')
    con += C(hv, '', ps, 'V')
    for name, kind, dflt in PARAMS:
        con += C(byParam[name], '', ps, name)
    out['entradas_conectadas'] = '%d de %d' % (con, len(INPUTS))
    ok, r = T(MT + 'connect_to_output', {'expression': {'refPath': ps}, 'output_name': '', 'material_property': 'MP_EmissiveColor'})
    out['emisivo'] = ok
    out['params'] = sorted(byParam.keys())
    out['log'] = LOG[:20]
    return out
