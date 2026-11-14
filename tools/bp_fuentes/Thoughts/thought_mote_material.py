import json
# thought_mote_material.py (2026-10-30) - arma M_ThoughtMote_SC: el sprite del polvo de Test_Thoughts (NS_ThoughtMotes_SC).
# Pedido de Beltran: "las particulas no son tan lindas; algunas con opacidad; las del entorno funcionan porque hay variedad".
# Copia de Focus/focus_dot_material.py. Unlit + Translucent, usado con sprites de Niagara. Cada particula toma de su
# Particle Random (Particles.MaterialRandom, Write Material Random en InitializeParticle):
#   s = cuan difusa: nitida y brillante (s 0, nucleo de 0,3 del sprite) -> bokeh tenue (s 1, todo el sprite, alfa 0,18)
#   w = un tinte hacia blanco (hasta 35 %)
#   un titileo suave (Twinkle) con frecuencia y fase propias.
# Particle Color: la salida '' es RGB (float3); el alfa va por la salida 'A' (entrada PA).
# Parametros: Glow, Opacity, Twinkle. Idempotente; nunca levanta; NO recompila (aparte). Sin `result = run()`.
MT = 'editor_toolset.toolsets.material.MaterialTools.'
OT = 'editor_toolset.toolsets.object.ObjectTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
FOLDER = '/Game/SoulCharger/Mechanics/Mind/Materials'
NAME = 'M_ThoughtMote_SC'
MATR = FOLDER + '/' + NAME + '.' + NAME
MAT = {'refPath': MATR}
FLAGS = {'shadingModel': 'MSM_Unlit', 'blendMode': 'BLEND_Translucent', 'bUsedWithNiagaraSprites': True,
         'bUseTranslucencyVertexFog': False}
PARAMS = [('Glow', 'scalar', 1.0), ('Opacity', 'scalar', 1.0), ('Twinkle', 'scalar', 0.35)]
NL = chr(10)
CODE_E = NL.join(['float s = frac(PR * 7.31);',
                  'float w = frac(PR * 5.17);',
                  'float3 c = lerp(PC.rgb, float3(1.0, 1.0, 1.0), 0.35 * w);',
                  'return c * Glow * lerp(1.5, 0.8, s);'])
INPUTS_E = ['PC', 'PR', 'Glow']
CODE_A = NL.join(['float2 p = UV - 0.5;',
                  'float r = length(p) * 2.0;',
                  'float s = frac(PR * 7.31);',
                  'float soft = lerp(0.3, 1.0, s);',
                  'float d = saturate(1.0 - r / soft);',
                  'float core = d * d * (3.0 - 2.0 * d);',
                  'float a = lerp(1.0, 0.18, s);',
                  'float tw = lerp(1.0 - Twinkle, 1.0, 0.5 + 0.5 * sin(T * lerp(1.1, 3.3, frac(PR * 3.71)) + PR * 6.2831853));',
                  'return saturate(core * a * tw * PA * Opacity);'])
INPUTS_A = ['UV', 'PA', 'PR', 'T', 'Opacity', 'Twinkle']
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
        vals = {'Group': 'Mote', 'DefaultValue': dflt}
        if name in byParam:
            S(byParam[name], vals)
            continue
        ok, r = T(MT + 'add_expression', {'material_or_function': MAT, 'expression_class': {'refPath': '/Script/Engine.MaterialExpressionScalarParameter'},
                                          'x': -900, 'y': -300 + 110 * i})
        if not ok:
            continue
        vals['ParameterName'] = name
        S(r['refPath'], vals)
        byParam[name] = r['refPath']

    def helper(desc, cls, xx, yy, extra=None):
        if desc in byDesc:
            return byDesc[desc]
        ok, r = T(MT + 'add_expression', {'material_or_function': MAT, 'expression_class': {'refPath': '/Script/Engine.' + cls}, 'x': xx, 'y': yy})
        if not ok:
            return None
        S(r['refPath'], {'Desc': desc})
        if extra:
            S(r['refPath'], extra)
        byDesc[desc] = r['refPath']
        return r['refPath']
    huv = helper('TM_UV', 'MaterialExpressionTextureCoordinate', -900, -800)
    hpc = helper('TM_PC', 'MaterialExpressionParticleColor', -900, -700)
    hpr = helper('TM_PR', 'MaterialExpressionParticleRandom', -900, -600)
    ht = helper('TM_T', 'MaterialExpressionTime', -900, -500, {'bOverride_Period': True, 'Period': 300.0})
    out['helpers'] = [bool(huv), bool(hpc), bool(hpr), bool(ht)]
    ps = custom(cust, 'MotePS', CODE_E, INPUTS_E, 'CMOT_Float3', -400, -400, out)
    if not ps:
        return {'err': 'no pude crear el Custom del emisivo', 'out': out, 'log': LOG}
    con = C(hpc, '', ps, 'PC') + C(hpr, '', ps, 'PR') + C(byParam['Glow'], '', ps, 'Glow')
    out['emisivo_entradas'] = '%d de %d' % (con, len(INPUTS_E))
    out['emisivo'] = T(MT + 'connect_to_output', {'expression': {'refPath': ps}, 'output_name': '', 'material_property': 'MP_EmissiveColor'})[0]
    op = custom(cust, 'MoteOP', CODE_A, INPUTS_A, 'CMOT_Float1', -400, -100, out)
    if not op:
        return {'err': 'no pude crear el Custom de opacidad', 'out': out, 'log': LOG}
    ca = C(huv, '', op, 'UV') + C(hpc, 'A', op, 'PA') + C(hpr, '', op, 'PR') + C(ht, '', op, 'T')
    ca += C(byParam['Opacity'], '', op, 'Opacity') + C(byParam['Twinkle'], '', op, 'Twinkle')
    out['opacidad_entradas'] = '%d de %d' % (ca, len(INPUTS_A))
    out['opacidad'] = T(MT + 'connect_to_output', {'expression': {'refPath': op}, 'output_name': '', 'material_property': 'MP_Opacity'})[0]
    out['params'] = sorted(byParam.keys())
    out['log'] = LOG[:20]
    return out
