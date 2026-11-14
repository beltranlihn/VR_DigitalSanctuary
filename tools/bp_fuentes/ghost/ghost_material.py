import json
# ghost_material.py (v2, 2026-10-01) - arma M_Ghost_SC (el fantasma de las instrucciones y los botones del grabador).
# Se pega ENTERO como `script` de ProgrammaticToolset.execute_tool_script. Idempotente (parametros por nombre, Custom por
# Description). Nunca levanta excepcion (try/except BaseException, gotcha 231). NO recompila (gotcha 479: aparte).
# SIN `result = run()` al final (gotcha 493). Salida de un Custom SIN AdditionalOutputs = '' (gotcha 560).
# v2 (pedido de Beltran: "material translucido suave, blanco azulado; color y brillo solo en el gatillo"):
# Unlit + TRANSLUCIDO, borde fresnel en la OPACIDAD (como MI_Hand_SC) y opacidad por instancia (PerInstanceCustomData[0],
# 1 por defecto fuera de un ISM) para los ecos:
#   Emissive = Color * (1 + Pressed*PressGain)                                  (Custom 'GhostPS')
#   Opacity  = saturate(Opacity * Inst * (Core + f*RimGain + Pressed*0.5))      (Custom 'GhostOP')
# Usos: mallas instanciadas (ecos) y con esqueleto (la mano). Recompilar APARTE y SIN MIDs vivas (gotcha 479 y el cuelgue
# del 09-29): correrlo ANTES de colocar fantasmas con vista previa.
MT = 'editor_toolset.toolsets.material.MaterialTools.'
OT = 'editor_toolset.toolsets.object.ObjectTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
FOLDER = '/Game/SoulCharger/Mechanics/Ghost'
NAME = 'M_Ghost_SC'
MATR = FOLDER + '/' + NAME + '.' + NAME
MAT = {'refPath': MATR}
FLAGS = {'shadingModel': 'MSM_Unlit', 'blendMode': 'BLEND_Translucent', 'twoSided': False, 'bUseTranslucencyVertexFog': False,
         'bUsedWithInstancedStaticMeshes': True, 'bUsedWithSkeletalMesh': True}
PARAMS = [('Color', 'vector', [0.78, 0.88, 1.0, 1.0]), ('Opacity', 'scalar', 1.0), ('Pressed', 'scalar', 0.0),
          ('RimPow', 'scalar', 2.0), ('RimGain', 'scalar', 0.9), ('Core', 'scalar', 0.35), ('PressGain', 'scalar', 2.0)]
NL = chr(10)
CODE_E = 'return Color.rgb * (1.0 + Pressed * PressGain);'
INPUTS_E = ['Color', 'Pressed', 'PressGain']
CODE_A = NL.join(['float3 n = normalize(N);',
                  'float3 v = normalize(V);',
                  'float f = pow(1.0 - saturate(abs(dot(n, v))), RimPow);',
                  'return saturate(Opacity * Inst * (Core + f * RimGain + Pressed * 0.5));'])
INPUTS_A = ['N', 'V', 'Opacity', 'Inst', 'Pressed', 'RimPow', 'RimGain', 'Core']
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


def custom(cust, desc, code, inputs, otype, x, y, out):
    if desc not in cust:
        ok, r = T(MT + 'add_expression', {'material_or_function': MAT, 'expression_class': {'refPath': '/Script/Engine.MaterialExpressionCustom'}, 'x': x, 'y': y})
        if ok:
            cust[desc] = r['refPath']
    ref = cust[desc] if desc in cust else None
    if not ref:
        out['err_' + desc] = 'no pude crear el Custom'
        return None
    S(ref, {'Description': desc, 'OutputType': otype, 'Code': code})
    S(ref, {'AdditionalOutputs': []})
    S(ref, {'Inputs': []})
    S(ref, {'Inputs': [{'inputName': n} for n in inputs]})
    return ref


def run2():
    out = {}
    ok, ex = T(AS + 'exists', {'path': FOLDER + '/' + NAME})
    if not ex:
        ok, r = T(MT + 'create_material', {'folder_path': FOLDER, 'asset_name': NAME})
        out['creado'] = ok
    for k, val in FLAGS.items():
        if not S(MATR, {k: val}):
            out['flag_no_' + k] = val
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
    hi = helper('GH_Inst', 'MaterialExpressionPerInstanceCustomData', -900, -900)
    if hi:
        S(hi, {'DataIndex': 0, 'ConstDefaultValue': 1.0})
        out['inst'] = G(hi, ['DataIndex', 'ConstDefaultValue'])
    # emisivo (reusa el Custom 'GhostPS' de v1, ya conectado al emisivo)
    ps = custom(cust, 'GhostPS', CODE_E, INPUTS_E, 'CMOT_Float3', -400, -400, out)
    if not ps:
        return {'err': 'no pude crear el Custom del emisivo', 'out': out, 'log': LOG}
    con = 0
    for name in INPUTS_E:
        con += C(byParam[name], '', ps, name)
    out['emisivo_entradas'] = '%d de %d' % (con, len(INPUTS_E))
    out['emisivo'] = T(MT + 'connect_to_output', {'expression': {'refPath': ps}, 'output_name': '', 'material_property': 'MP_EmissiveColor'})[0]
    # opacidad
    op = custom(cust, 'GhostOP', CODE_A, INPUTS_A, 'CMOT_Float1', -400, -100, out)
    if not op:
        return {'err': 'no pude crear el Custom de opacidad', 'out': out, 'log': LOG}
    ca = 0
    ca += C(hn, '', op, 'N')
    ca += C(hv, '', op, 'V')
    ca += C(hi, '', op, 'Inst') if hi else 0
    for name in ('Opacity', 'Pressed', 'RimPow', 'RimGain', 'Core'):
        ca += C(byParam[name], '', op, name)
    out['opacidad_entradas'] = '%d de %d' % (ca, len(INPUTS_A))
    out['opacidad'] = T(MT + 'connect_to_output', {'expression': {'refPath': op}, 'output_name': '', 'material_property': 'MP_Opacity'})[0]
    out['params'] = sorted(byParam.keys())
    out['log'] = LOG[:20]
    return out
