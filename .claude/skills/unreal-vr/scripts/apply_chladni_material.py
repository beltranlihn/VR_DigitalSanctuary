# apply_chladni_material.py - arma M_ChladniFloor_SC desde VR_Test/Saved/ClaudeScripts/chladni_build.json
# (lo genera scripts/gen_chladni_material.py). Se corre con execute_tool_script en Unreal. IDEMPOTENTE: busca
# parametros por nombre, Customs por Description y helpers por Desc; lo que ya existe lo actualiza.
# Adaptado de apply_valley_material_A.py + _B.py (el pipeline probado del valle), en un solo script.
# Nunca levanta excepcion (gotcha 60/418): todo va envuelto y los errores vuelven como DATO.
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
def C(frm, fout, to, tin):
    return T(MT + 'connect_expressions', {'from_expression': {'refPath': frm}, 'from_output_name': fout, 'to_expression': {'refPath': to}, 'to_input_name': tin})[0]
def run():
  try:
    return run2()
  except BaseException as e:
    return {'err': 'run :: ' + str(e)[:300], 'log': LOG}
def run2():
    out = {}
    ok, txt = T(AS + 'read_file', {'file_path': 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/chladni_build.json'})
    if not ok:
        return {'err': 'no pude leer el plan', 'log': LOG}
    plan = json.loads(txt)
    MATP = plan['material']
    MATR = MATP + '.' + MATP.split('/')[-1]
    MAT = {'refPath': MATR}
    S(MATR, {'shadingModel': 'MSM_Unlit', 'blendMode': 'BLEND_Opaque', 'twoSided': True, 'floatPrecisionMode': 'MFPM_Full_MaterialExpressionOnly'})
    out['flags'] = G(MATR, ['shadingModel', 'blendMode', 'twoSided', 'floatPrecisionMode'])
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
            if v and v.get('Desc'):
                byDesc[v['Desc']] = r
    # ---- parametros ----
    creados = 0
    for i, p in enumerate(plan['params']):
        k = p['kind']
        if k == 'vector':
            d = p['default']
            vals = {'Group': p['group'], 'DefaultValue': {'r': d[0], 'g': d[1], 'b': d[2], 'a': 1.0}}
            cls = 'MaterialExpressionVectorParameter'
        elif k == 'texture':
            vals = {'Group': p['group'], 'Texture': {'refPath': p['default']}, 'SamplerType': p.get('sampler', 'SAMPLERTYPE_LinearGrayscale')}
            cls = 'MaterialExpressionTextureObjectParameter'
        else:
            vals = {'Group': p['group'], 'DefaultValue': p['default']}
            cls = 'MaterialExpressionScalarParameter'
        if p['name'] not in byParam:
            ok, r = T(MT + 'add_expression', {'material_or_function': MAT, 'expression_class': {'refPath': '/Script/Engine.' + cls}, 'x': -2600 + (i // 20) * 280, 'y': -1200 + (i % 20) * 130})
            if not ok:
                continue
            byParam[p['name']] = r['refPath']
            vals['ParameterName'] = p['name']
            creados += 1
        S(byParam[p['name']], vals)
    out['params_creados'] = creados
    out['params_total'] = len(byParam)
    # ---- helpers ----
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
    H['V_VI1'] = helper('V_VI1', 'MaterialExpressionVertexInterpolator', {}, 200, -400)
    H['V_WPO'] = helper('V_WPO', 'MaterialExpressionTransform', {'TransformSourceType': 'TRANSFORMSOURCE_Local', 'TransformType': 'TRANSFORM_World'}, 400, -900)
    H['V_CamVec'] = helper('V_CamVec', 'MaterialExpressionCameraVectorWS', {}, -900, 200)
    H['V_AbsPos'] = helper('V_AbsPos', 'MaterialExpressionWorldPosition', {}, -900, 350)
    H['V_CamPos'] = helper('V_CamPos', 'MaterialExpressionCameraPositionWS', {}, -900, 450)
    H['V_Dist'] = helper('V_Dist', 'MaterialExpressionDistance', {}, -600, 400)
    dn = 'SunDir'
    H['D_cosaz'] = helper('D_cosaz', 'MaterialExpressionCosine', {'Period': 360.0}, -1500, 600)
    H['D_sinaz'] = helper('D_sinaz', 'MaterialExpressionSine', {'Period': 360.0}, -1500, 680)
    H['D_cosel'] = helper('D_cosel', 'MaterialExpressionCosine', {'Period': 360.0}, -1500, 760)
    H['D_sinel'] = helper('D_sinel', 'MaterialExpressionSine', {'Period': 360.0}, -1500, 840)
    H['D_mx'] = helper('D_mx', 'MaterialExpressionMultiply', {}, -1250, 600)
    H['D_my'] = helper('D_my', 'MaterialExpressionMultiply', {}, -1250, 700)
    H['D_a1'] = helper('D_a1', 'MaterialExpressionAppendVector', {}, -1050, 650)
    H['D_' + dn] = helper('D_' + dn, 'MaterialExpressionAppendVector', {}, -850, 720)
    def ins(ref):
        ok, v = T(MT + 'get_expression_input_names', {'material_or_function': MAT, 'expression': {'refPath': ref}})
        return v or []
    cons = 0
    tin = (ins(H['D_cosaz']) or [''])[0]
    cons += C(byParam['SunAz'], '', H['D_cosaz'], tin)
    cons += C(byParam['SunAz'], '', H['D_sinaz'], tin)
    cons += C(byParam['SunEl'], '', H['D_cosel'], tin)
    cons += C(byParam['SunEl'], '', H['D_sinel'], tin)
    cons += C(H['D_cosaz'], '', H['D_mx'], 'A')
    cons += C(H['D_cosel'], '', H['D_mx'], 'B')
    cons += C(H['D_sinaz'], '', H['D_my'], 'A')
    cons += C(H['D_cosel'], '', H['D_my'], 'B')
    cons += C(H['D_mx'], '', H['D_a1'], 'A')
    cons += C(H['D_my'], '', H['D_a1'], 'B')
    cons += C(H['D_a1'], '', H['D_' + dn], 'A')
    cons += C(H['D_sinel'], '', H['D_' + dn], 'B')
    cons += C(H['V_AbsPos'], '', H['V_Dist'], 'A')
    cons += C(H['V_CamPos'], '', H['V_Dist'], 'B')
    out['helpers_ok'] = cons
    # ---- Customs ----
    pos = {'ChladniHeightVS': (-100, -900), 'ChladniPS': (200, 100)}
    res = {}
    for c in plan['customs']:
        d = c['desc']
        if d not in cust:
            ok, r = T(MT + 'add_expression', {'material_or_function': MAT, 'expression_class': {'refPath': '/Script/Engine.MaterialExpressionCustom'}, 'x': pos[d][0], 'y': pos[d][1]})
            if not ok:
                continue
            cust[d] = r['refPath']
        ref = cust[d]
        ok, code = T(AS + 'read_file', {'file_path': 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/' + c['code_file']})
        S(ref, {'Description': d, 'OutputType': c['outputType'], 'Code': code})
        S(ref, {'Inputs': []})
        S(ref, {'Inputs': [{'inputName': e['name']} for e in c['inputs']]})
        okc, fallos = 0, []
        for e in c['inputs']:
            s = e['src']
            k = s['kind']
            if k == 'param':
                frm, fo = byParam.get(s['param']), ('RGB' if s['vector'] else '')
            elif k == 'texobj':
                frm, fo = byParam.get(s['param']), ''
            elif k == 'localpos':
                frm, fo = H['V_LP'], 'XYZ'
            elif k == 'vi':
                frm, fo = H['V_VI%d' % s['index']], 'PS'
            elif k == 'camvec':
                frm, fo = H['V_CamVec'], ''
            elif k == 'dist':
                frm, fo = H['V_Dist'], ''
            elif k == 'dir':
                frm, fo = H['D_' + e['name']], ''
            else:
                frm = None
            if frm and C(frm, fo, ref, e['name']):
                okc += 1
            else:
                fallos.append(e['name'])
        res[d] = {'entradas': len(c['inputs']), 'conectadas': okc, 'fallos': fallos}
    extra = 0
    extra += C(H['V_LP'], 'XYZ', H['V_VI1'], 'VS')
    extra += C(cust['ChladniHeightVS'], '', H['V_WPO'], 'None')
    extra += T(MT + 'connect_to_output', {'expression': {'refPath': H['V_WPO']}, 'output_name': '', 'material_property': 'MP_WorldPositionOffset'})[0]
    extra += T(MT + 'connect_to_output', {'expression': {'refPath': cust['ChladniPS']}, 'output_name': '', 'material_property': 'MP_EmissiveColor'})[0]
    out['customs'] = res
    out['salidas_ok'] = extra
    out['nombres'] = {'transform_in': ins(H['V_WPO']), 'vi_in': ins(H['V_VI1'])}
    out['log'] = LOG[:25]
    return out
result = run()
