import json

MT = 'editor_toolset.toolsets.material.MaterialTools.'
OT = 'editor_toolset.toolsets.object.ObjectTools.'
MAT = {'refPath': '/Game/SoulCharger/Core/ProtoSoul/M_SoulRibbon_SC.M_SoulRibbon_SC'}
E = '/Script/Engine.MaterialExpression'

ERRS = []


def T(name, payload):
    try:
        return True, execute_tool(name, json.dumps(payload))['returnValue']
    except BaseException as e:
        ERRS.append(name.split('.')[-1] + ' :: ' + str(e)[:160])
        return False, None


N = {}


def add(key, cls, x, y, props=None):
    ok, ex = T(MT + 'add_expression', {'material_or_function': MAT,
                                       'expression_class': {'refPath': E + cls},
                                       'x': x, 'y': y})
    if not ok or ex is None:
        ERRS.append('add failed: ' + key)
        return None
    N[key] = ex
    if props:
        T(OT + 'set_properties', {'instance': ex, 'values': json.dumps(props)})
    return ex


def C(a, b, to_in, from_out=None):
    if a is None or b is None:
        ERRS.append('connect skipped (missing) to_in=' + to_in)
        return
    if from_out is None:
        ok, outs = T(MT + 'get_expression_output_names', {'expression': a})
        from_out = (outs[0] if outs else '')
    T(MT + 'connect_expressions', {'from_expression': a, 'from_output_name': from_out,
                                   'to_expression': b, 'to_input_name': to_in})


def S(key, name, val, x, y):
    return add(key, 'ScalarParameter', x, y,
               {'ParameterName': name, 'DefaultValue': val, 'Group': 'A - Trazo'})


def K(key, val, x, y):
    return add(key, 'Constant', x, y, {'R': val})


def run():
    S('bright', 'Brightness', 1.0, -1900, -900)
    S('reveal', 'Reveal', 1.05, -1900, -820)
    S('revsoft', 'RevealSoft', 0.05, -1900, -740)
    S('tipboost', 'TipBoost', 2.5, -1900, -660)
    S('tipwidth', 'TipWidth', 0.07, -1900, -580)
    S('brAmt', 'BreathAmount', 0.45, -1900, -500)
    S('brFreq', 'BreathFreq', 3.0, -1900, -420)
    S('brSpd', 'BreathSpeed', 0.5, -1900, -340)
    S('wbAmt', 'WobbleAmount', 2.0, -1900, -260)
    S('wbFreq', 'WobbleFreq', 2.3, -1900, -180)
    S('wbSpd', 'WobbleSpeed', 0.35, -1900, -20)
    S('halfw', 'HalfWidthBaked', 1.0, -1900, 20)
    S('edgesoft', 'EdgeSoft', 0.55, -1900, 60)
    S('fltSpd', 'FloatSpeed', 0.35, -1900, 140)
    S('seed', 'PhaseSeed', 0.0, -1900, 220)
    add('color', 'VectorParameter', -1900, 300,
        {'ParameterName': 'Color', 'Group': 'A - Trazo',
         'DefaultValue': {'r': 0.10, 'g': 0.35, 'b': 1.0, 'a': 1.0}})
    add('fltAmt', 'VectorParameter', -1900, 400,
        {'ParameterName': 'FloatAmount', 'Group': 'A - Trazo',
         'DefaultValue': {'r': 4.0, 'g': 4.0, 'b': 6.0, 'a': 1.0}})

    add('uv', 'TextureCoordinate', -1700, -1000, {'CoordinateIndex': 0})
    add('time', 'Time', -1700, -900, {'bOverride_Period': True, 'Period': 300.0})
    add('nrm', 'VertexNormalWS', -1700, -800)
    add('U', 'ComponentMask', -1550, -1020, {'R': True, 'G': False, 'B': False, 'A': False})
    add('V', 'ComponentMask', -1550, -950, {'R': False, 'G': True, 'B': False, 'A': False})
    C(N.get('uv'), N.get('U'), 'Input')
    C(N.get('uv'), N.get('V'), 'Input')

    K('k1', 1.0, -1700, -700)
    K('k2', 2.0, -1700, -650)
    K('kHalf', 0.5, -1700, -600)
    K('r073', 0.73, -1700, -550)
    K('r137', 1.37, -1700, -500)

    add('sideMul', 'Multiply', -1400, -950)
    C(N.get('V'), N.get('sideMul'), 'A')
    C(N.get('k2'), N.get('sideMul'), 'B')
    add('side', 'Subtract', -1250, -950)
    C(N.get('sideMul'), N.get('side'), 'A')
    C(N.get('k1'), N.get('side'), 'B')

    add('brA', 'Multiply', -1400, -500)
    C(N.get('U'), N.get('brA'), 'A')
    C(N.get('brFreq'), N.get('brA'), 'B')
    add('brB', 'Multiply', -1400, -430)
    C(N.get('time'), N.get('brB'), 'A')
    C(N.get('brSpd'), N.get('brB'), 'B')
    add('brC', 'Add', -1250, -470)
    C(N.get('brA'), N.get('brC'), 'A')
    C(N.get('brB'), N.get('brC'), 'B')
    add('brD', 'Add', -1150, -470)
    C(N.get('brC'), N.get('brD'), 'A')
    C(N.get('seed'), N.get('brD'), 'B')
    add('brSin', 'Sine', -1050, -470, {'Period': 1.0})
    C(N.get('brD'), N.get('brSin'), 'Input')
    add('brMul', 'Multiply', -950, -470)
    C(N.get('brAmt'), N.get('brMul'), 'A')
    C(N.get('brSin'), N.get('brMul'), 'B')
    add('breath', 'Add', -850, -470)
    C(N.get('k1'), N.get('breath'), 'A')
    C(N.get('brMul'), N.get('breath'), 'B')

    add('tapA', 'Multiply', -1400, -300)
    C(N.get('U'), N.get('tapA'), 'A')
    C(N.get('kHalf'), N.get('tapA'), 'B')
    add('taper', 'Sine', -1250, -300, {'Period': 1.0})
    C(N.get('tapA'), N.get('taper'), 'Input')

    add('rvA', 'Subtract', -1400, -180)
    C(N.get('reveal'), N.get('rvA'), 'A')
    C(N.get('U'), N.get('rvA'), 'B')
    add('rvB', 'Divide', -1250, -180)
    C(N.get('rvA'), N.get('rvB'), 'A')
    C(N.get('revsoft'), N.get('rvB'), 'B')
    add('rev', 'Saturate', -1100, -180)
    C(N.get('rvB'), N.get('rev'), 'Input')

    add('tpAbs', 'Abs', -1250, -80)
    C(N.get('rvA'), N.get('tpAbs'), 'Input')
    add('tpDiv', 'Divide', -1100, -80)
    C(N.get('tpAbs'), N.get('tpDiv'), 'A')
    C(N.get('tipwidth'), N.get('tpDiv'), 'B')
    add('tpOm', 'OneMinus', -980, -80)
    C(N.get('tpDiv'), N.get('tpOm'), 'Input')
    add('tip', 'Saturate', -870, -80)
    C(N.get('tpOm'), N.get('tip'), 'Input')

    add('wfA', 'Multiply', -720, -400)
    C(N.get('breath'), N.get('wfA'), 'A')
    C(N.get('taper'), N.get('wfA'), 'B')
    add('wf', 'Multiply', -600, -400)
    C(N.get('wfA'), N.get('wf'), 'A')
    C(N.get('rev'), N.get('wf'), 'B')

    add('wfm1', 'Subtract', -480, -400)
    C(N.get('wf'), N.get('wfm1'), 'A')
    C(N.get('k1'), N.get('wfm1'), 'B')
    add('owA', 'Multiply', -480, -300)
    C(N.get('side'), N.get('owA'), 'A')
    C(N.get('halfw'), N.get('owA'), 'B')
    add('owB', 'Multiply', -360, -350)
    C(N.get('owA'), N.get('owB'), 'A')
    C(N.get('wfm1'), N.get('owB'), 'B')
    add('offW', 'Multiply', -240, -350)
    C(N.get('nrm'), N.get('offW'), 'A')
    C(N.get('owB'), N.get('offW'), 'B')

    add('wbA', 'Multiply', -1400, 60)
    C(N.get('U'), N.get('wbA'), 'A')
    C(N.get('wbFreq'), N.get('wbA'), 'B')
    add('wbB', 'Multiply', -1400, 130)
    C(N.get('time'), N.get('wbB'), 'A')
    C(N.get('wbSpd'), N.get('wbB'), 'B')
    add('wbC', 'Add', -1250, 95)
    C(N.get('wbA'), N.get('wbC'), 'A')
    C(N.get('wbB'), N.get('wbC'), 'B')
    add('wbSin', 'Sine', -1120, 95, {'Period': 1.0})
    C(N.get('wbC'), N.get('wbSin'), 'Input')
    add('wbMul', 'Multiply', -1000, 95)
    C(N.get('wbAmt'), N.get('wbMul'), 'A')
    C(N.get('wbSin'), N.get('wbMul'), 'B')
    add('offWob', 'Multiply', -860, 95)
    C(N.get('nrm'), N.get('offWob'), 'A')
    C(N.get('wbMul'), N.get('offWob'), 'B')

    add('ftBase', 'Multiply', -1400, 260)
    C(N.get('time'), N.get('ftBase'), 'A')
    C(N.get('fltSpd'), N.get('ftBase'), 'B')
    add('ft2', 'Multiply', -1280, 320)
    C(N.get('ftBase'), N.get('ft2'), 'A')
    C(N.get('r073'), N.get('ft2'), 'B')
    add('ft3', 'Multiply', -1280, 380)
    C(N.get('ftBase'), N.get('ft3'), 'A')
    C(N.get('r137'), N.get('ft3'), 'B')
    add('fs1', 'Sine', -1140, 260, {'Period': 1.0})
    C(N.get('ftBase'), N.get('fs1'), 'Input')
    add('fs2', 'Sine', -1140, 320, {'Period': 1.0})
    C(N.get('ft2'), N.get('fs2'), 'Input')
    add('fs3', 'Sine', -1140, 380, {'Period': 1.0})
    C(N.get('ft3'), N.get('fs3'), 'Input')
    add('fap1', 'AppendVector', -1000, 290)
    C(N.get('fs1'), N.get('fap1'), 'A')
    C(N.get('fs2'), N.get('fap1'), 'B')
    add('fap2', 'AppendVector', -880, 320)
    C(N.get('fap1'), N.get('fap2'), 'A')
    C(N.get('fs3'), N.get('fap2'), 'B')
    add('offFloat', 'Multiply', -740, 320)
    C(N.get('fap2'), N.get('offFloat'), 'A')
    C(N.get('fltAmt'), N.get('offFloat'), 'B')

    add('wpoA', 'Add', -120, -200)
    C(N.get('offW'), N.get('wpoA'), 'A')
    C(N.get('offWob'), N.get('wpoA'), 'B')
    add('wpo', 'Add', 0, -150)
    C(N.get('wpoA'), N.get('wpo'), 'A')
    C(N.get('offFloat'), N.get('wpo'), 'B')

    add('emA', 'Multiply', -600, 500)
    C(N.get('color'), N.get('emA'), 'A')
    C(N.get('bright'), N.get('emA'), 'B')
    add('tpB', 'Multiply', -720, 600)
    C(N.get('tipboost'), N.get('tpB'), 'A')
    C(N.get('tip'), N.get('tpB'), 'B')
    add('tpC', 'Add', -600, 600)
    C(N.get('k1'), N.get('tpC'), 'A')
    C(N.get('tpB'), N.get('tpC'), 'B')
    add('emis', 'Multiply', -420, 540)
    C(N.get('emA'), N.get('emis'), 'A')
    C(N.get('tpC'), N.get('emis'), 'B')

    add('edAbs', 'Abs', -900, 780)
    C(N.get('side'), N.get('edAbs'), 'Input')
    add('edOm', 'OneMinus', -780, 780)
    C(N.get('edAbs'), N.get('edOm'), 'Input')
    add('edDiv', 'Divide', -660, 780)
    C(N.get('edOm'), N.get('edDiv'), 'A')
    C(N.get('edgesoft'), N.get('edDiv'), 'B')
    add('edge', 'Saturate', -540, 780)
    C(N.get('edDiv'), N.get('edge'), 'Input')
    add('opac', 'Multiply', -400, 760)
    C(N.get('rev'), N.get('opac'), 'A')
    C(N.get('edge'), N.get('opac'), 'B')

    outs_map = ((N.get('emis'), 'MP_EmissiveColor'),
                (N.get('opac'), 'MP_Opacity'),
                (N.get('wpo'), 'MP_WorldPositionOffset'))
    for ex, prop in outs_map:
        if ex is None:
            ERRS.append('output missing: ' + prop)
            continue
        ok, outs = T(MT + 'get_expression_output_names', {'expression': ex})
        T(MT + 'connect_to_output', {'expression': ex,
                                     'output_name': (outs[0] if outs else ''),
                                     'material_property': prop})

    T(OT + 'set_properties', {'instance': MAT, 'values': json.dumps({
        'BlendMode': 'BLEND_Additive',
        'ShadingModel': 'MSM_Unlit',
        'TwoSided': True,
        'FloatPrecisionMode': 'MFPM_Full_MaterialExpressionOnly'})})

    T(MT + 'recompile', {'material_or_function': MAT})

    ok, exprs = T(MT + 'get_expressions', {'material_or_function': MAT})
    return {'errores': ERRS[:25], 'total_errores': len(ERRS),
            'expresiones': (len(exprs) if exprs else -1)}

