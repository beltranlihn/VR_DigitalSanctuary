import json
MT = 'editor_toolset.toolsets.material.MaterialTools.'
OT = 'editor_toolset.toolsets.object.ObjectTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
LOG = []
def T(name, payload):
    try:
        return True, execute_tool(name, json.dumps(payload))['returnValue']
    except BaseException as e:
        LOG.append(name.split('.')[-1] + ' :: ' + str(e)[:220])
        return False, None
def G(ref, props):
    ok, v = T(OT + 'get_properties', {'instance': {'refPath': ref}, 'properties': props})
    if not ok or v is None:
        return None
    try:
        return json.loads(v)
    except BaseException:
        return None
def S(ref, vals):
    return T(OT + 'set_properties', {'instance': {'refPath': ref}, 'values': json.dumps(vals)})[0]
def run():
  try:
    return run2()
  except BaseException as e:
    return {'err': 'run :: ' + str(e)[:300], 'log': LOG}
def run2():
    out = {}
    ok, txt = T(AS + 'read_file', {'file_path': 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/valley_build.json'})
    if not ok:
        return {'err': 'no pude leer el plan', 'log': LOG}
    plan = json.loads(txt)
    MATP = plan['material']
    NAME = MATP.split('/')[-1]
    MATR = MATP + '.' + NAME
    MAT = {'refPath': MATR}
    S(MATR, {'shadingModel': 'MSM_Unlit', 'blendMode': 'BLEND_Opaque', 'twoSided': True, 'floatPrecisionMode': 'MFPM_Full_MaterialExpressionOnly'})
    out['flags'] = G(MATR, ['shadingModel', 'blendMode', 'twoSided', 'floatPrecisionMode'])
    ok, exprs = T(MT + 'get_expressions', {'material_or_function': MAT})
    byParam = {}
    byDesc = {}
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
                byDesc[v['Description']] = r
        else:
            v = G(r, ['Desc'])
            if v and v.get('Desc'):
                byDesc[v['Desc']] = r
    creados = 0
    x = -2600
    y = -1200
    upd = 0
    nombres_plan = set(q['name'] for q in plan['params'])
    out['sobrantes'] = sorted([n for n in byParam if n not in nombres_plan])
    for i, p in enumerate(plan['params']):
        if p['name'] in byParam:
            ref = byParam[p['name']]
            if p['kind'] == 'vector':
                d = p['default']
                S(ref, {'Group': p['group'], 'DefaultValue': {'r': d[0], 'g': d[1], 'b': d[2], 'a': 1.0}})
            else:
                S(ref, {'Group': p['group'], 'DefaultValue': p['default']})
            upd += 1
            continue
        cls = 'MaterialExpressionVectorParameter' if p['kind'] == 'vector' else 'MaterialExpressionScalarParameter'
        ok, r = T(MT + 'add_expression', {'material_or_function': MAT, 'expression_class': {'refPath': '/Script/Engine.' + cls}, 'x': x + (i // 20) * 280, 'y': y + (i % 20) * 130})
        if not ok:
            continue
        ref = r['refPath']
        if p['kind'] == 'vector':
            d = p['default']
            S(ref, {'ParameterName': p['name'], 'Group': p['group'], 'DefaultValue': {'r': d[0], 'g': d[1], 'b': d[2], 'a': 1.0}})
        else:
            S(ref, {'ParameterName': p['name'], 'Group': p['group'], 'DefaultValue': p['default']})
        byParam[p['name']] = ref
        creados += 1
    out['params_creados'] = creados
    out['params_actualizados'] = upd
    out['params_total'] = len(byParam)
    def helper(desc, cls, props, xx, yy):
        if desc in byDesc:
            return byDesc[desc]
        ok, r = T(MT + 'add_expression', {'material_or_function': MAT, 'expression_class': {'refPath': '/Script/Engine.' + cls}, 'x': xx, 'y': yy})
        if not ok:
            return None
        ref = r['refPath']
        pr = dict(props)
        pr['Desc'] = desc
        S(ref, pr)
        byDesc[desc] = ref
        return ref
    H = {}
    H['V_LP'] = helper('V_LP', 'MaterialExpressionLocalPosition', {'IncludedOffsets': 'IncludeOffsets', 'LocalOrigin': 'Instance'}, -900, -900)
    H['V_VI0'] = helper('V_VI0', 'MaterialExpressionVertexInterpolator', {}, 200, -600)
    H['V_VI1'] = helper('V_VI1', 'MaterialExpressionVertexInterpolator', {}, 200, -400)
    H['V_WPO'] = helper('V_WPO', 'MaterialExpressionTransform', {'TransformSourceType': 'TRANSFORMSOURCE_Local', 'TransformType': 'TRANSFORM_World'}, 400, -900)
    H['V_CamVec'] = helper('V_CamVec', 'MaterialExpressionCameraVectorWS', {}, -900, 200)
    H['V_CamL'] = helper('V_CamL', 'MaterialExpressionTransform', {'TransformSourceType': 'TRANSFORMSOURCE_World', 'TransformType': 'TRANSFORM_Local'}, -600, 200)
    H['V_AbsPos'] = helper('V_AbsPos', 'MaterialExpressionWorldPosition', {}, -900, 350)
    H['V_CamPos'] = helper('V_CamPos', 'MaterialExpressionCameraPositionWS', {}, -900, 450)
    H['V_Dist'] = helper('V_Dist', 'MaterialExpressionDistance', {}, -600, 400)
    dirs = {}
    for c in plan['customs']:
        for e in c['inputs']:
            s = e['src']
            if s['kind'] == 'dir':
                dirs[e['name']] = s
    yy = 600
    for dn, s in dirs.items():
        H['D_' + dn + '_cosaz'] = helper('D_' + dn + '_cosaz', 'MaterialExpressionCosine', {'Period': 360.0}, -1500, yy)
        H['D_' + dn + '_sinaz'] = helper('D_' + dn + '_sinaz', 'MaterialExpressionSine', {'Period': 360.0}, -1500, yy + 80)
        H['D_' + dn + '_cosel'] = helper('D_' + dn + '_cosel', 'MaterialExpressionCosine', {'Period': 360.0}, -1500, yy + 160)
        H['D_' + dn + '_sinel'] = helper('D_' + dn + '_sinel', 'MaterialExpressionSine', {'Period': 360.0}, -1500, yy + 240)
        H['D_' + dn + '_mx'] = helper('D_' + dn + '_mx', 'MaterialExpressionMultiply', {}, -1250, yy)
        H['D_' + dn + '_my'] = helper('D_' + dn + '_my', 'MaterialExpressionMultiply', {}, -1250, yy + 100)
        H['D_' + dn + '_a1'] = helper('D_' + dn + '_a1', 'MaterialExpressionAppendVector', {}, -1050, yy + 50)
        H['D_' + dn] = helper('D_' + dn, 'MaterialExpressionAppendVector', {}, -850, yy + 120)
        yy += 340
    H['C_MoonCosR'] = helper('C_MoonCosR', 'MaterialExpressionCosine', {'Period': 360.0}, -1500, yy)
    def ins(ref):
        ok, v = T(MT + 'get_expression_input_names', {'material_or_function': MAT, 'expression': {'refPath': ref}})
        return v or []
    def outs(ref):
        ok, v = T(MT + 'get_expression_output_names', {'material_or_function': MAT, 'expression': {'refPath': ref}})
        return v or []
    def C(frm, fout, to, tin):
        return T(MT + 'connect_expressions', {'from_expression': {'refPath': frm}, 'from_output_name': fout, 'to_expression': {'refPath': to}, 'to_input_name': tin})[0]
    cons = 0
    for dn, s in dirs.items():
        ci = ins(H['D_' + dn + '_cosaz'])
        tin = ci[0] if ci else ''
        cons += C(byParam[s['az']], '', H['D_' + dn + '_cosaz'], tin)
        cons += C(byParam[s['az']], '', H['D_' + dn + '_sinaz'], tin)
        cons += C(byParam[s['el']], '', H['D_' + dn + '_cosel'], tin)
        cons += C(byParam[s['el']], '', H['D_' + dn + '_sinel'], tin)
        cons += C(H['D_' + dn + '_cosaz'], '', H['D_' + dn + '_mx'], 'A')
        cons += C(H['D_' + dn + '_cosel'], '', H['D_' + dn + '_mx'], 'B')
        cons += C(H['D_' + dn + '_sinaz'], '', H['D_' + dn + '_my'], 'A')
        cons += C(H['D_' + dn + '_cosel'], '', H['D_' + dn + '_my'], 'B')
        cons += C(H['D_' + dn + '_mx'], '', H['D_' + dn + '_a1'], 'A')
        cons += C(H['D_' + dn + '_my'], '', H['D_' + dn + '_a1'], 'B')
        cons += C(H['D_' + dn + '_a1'], '', H['D_' + dn], 'A')
        cons += C(H['D_' + dn + '_sinel'], '', H['D_' + dn], 'B')
    ci = ins(H['C_MoonCosR'])
    cons += C(byParam['MoonRadius'], '', H['C_MoonCosR'], ci[0] if ci else '')
    ci = ins(H['V_CamL'])
    cons += C(H['V_CamVec'], '', H['V_CamL'], ci[0] if ci else '')
    cons += C(H['V_AbsPos'], '', H['V_Dist'], 'A')
    cons += C(H['V_CamPos'], '', H['V_Dist'], 'B')
    # CAPA VIVA (2026-09-28): cadenas de preshader Mul (A*B), Mix (A + (B - A)*T) y Tint (A*(1 + (B - 1)*T)) de plan_valley_material.py.
    # Solo cuentas de uniformes: Unreal las resuelve en la CPU (costo 0 por pixel). Idempotente (helpers por Desc).
    vecs = set(q['name'] for q in plan['params'] if q['kind'] == 'vector')
    def pout(n):
        return 'RGB' if n in vecs else ''
    vivas = {}
    for c in plan['customs']:
        for e in c['inputs']:
            if e['src']['kind'] in ('mul', 'mix', 'tint'):
                vivas[e['name']] = e['src']
    yy = -1500
    for nm, s in vivas.items():
        if s['kind'] == 'mul':
            m_ = helper('M_' + nm, 'MaterialExpressionMultiply', {}, -1250, yy)
            H['M_' + nm] = m_
            cons += C(byParam[s['a']], pout(s['a']), m_, 'A')
            cons += C(byParam[s['b']], pout(s['b']), m_, 'B')
            yy -= 100
        elif s['kind'] == 'tint':
            # Tint(A, B, T) = A * (1 + (B - 1) * T): tinte RELATIVO (rev. 2). Con T = 0 da A * 1 exacto.
            d_ = helper('T_' + nm + '_d', 'MaterialExpressionSubtract', {'ConstB': 1.0}, -1650, yy)
            m_ = helper('T_' + nm + '_m', 'MaterialExpressionMultiply', {}, -1450, yy)
            o_ = helper('T_' + nm + '_o', 'MaterialExpressionAdd', {'ConstB': 1.0}, -1250, yy)
            x_ = helper('T_' + nm, 'MaterialExpressionMultiply', {}, -1050, yy)
            H['T_' + nm + '_d'], H['T_' + nm + '_m'], H['T_' + nm + '_o'], H['T_' + nm] = d_, m_, o_, x_
            cons += C(byParam[s['b']], pout(s['b']), d_, 'A')
            cons += C(d_, '', m_, 'A')
            cons += C(byParam[s['t']], pout(s['t']), m_, 'B')
            cons += C(m_, '', o_, 'A')
            cons += C(byParam[s['a']], pout(s['a']), x_, 'A')
            cons += C(o_, '', x_, 'B')
            yy -= 180
        else:
            d_ = helper('X_' + nm + '_d', 'MaterialExpressionSubtract', {}, -1450, yy)
            m_ = helper('X_' + nm + '_m', 'MaterialExpressionMultiply', {}, -1250, yy)
            x_ = helper('X_' + nm, 'MaterialExpressionAdd', {}, -1050, yy)
            H['X_' + nm + '_d'], H['X_' + nm + '_m'], H['X_' + nm] = d_, m_, x_
            cons += C(byParam[s['b']], pout(s['b']), d_, 'A')
            cons += C(byParam[s['a']], pout(s['a']), d_, 'B')
            cons += C(d_, '', m_, 'A')
            cons += C(byParam[s['t']], pout(s['t']), m_, 'B')
            cons += C(byParam[s['a']], pout(s['a']), x_, 'A')
            cons += C(m_, '', x_, 'B')
            yy -= 180
    out['vivas'] = sorted(vivas)
    # helpers de capa viva que YA NO usa el plan (p. ej. volver a la v2, o la rev. 1 con LiveShadowRadius/LiveGlowHeight):
    # se borran a mano con delete_expression despues del script B (el B ya no los conecta a nada)
    out['helpers_sobrantes'] = sorted([k for k in byDesc if k[:2] in ('M_', 'X_', 'T_') and k not in H])
    out['conexiones_ok'] = cons
    out['helpers'] = sorted([k for k, v in H.items() if v])
    out['nombres'] = {'cos_in': ins(H['C_MoonCosR']), 'transform_in': ins(H['V_CamL']), 'vi_in': ins(H['V_VI0']), 'vi_out': outs(H['V_VI0']), 'lp_out': outs(H['V_LP']), 'vec_out': outs(byParam['ColLit']), 'abspos_out': outs(H['V_AbsPos']), 'campos_out': outs(H['V_CamPos'])}
    out['log'] = LOG[:30]
    return out
result = run()
