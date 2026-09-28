import json
# apply_breath_air_material.py - arma M_BreathAir_SC (el aliento visible) desde breath_air_build.json.
# Se pega ENTERO como `script` de ProgrammaticToolset.execute_tool_script. Idempotente (helpers por Desc, parametros
# por nombre, Customs por Description): se puede correr dos veces. Nunca levanta excepcion (todo dentro de
# try/except BaseException, gotcha 231). NO recompila: el recompile va aparte, para leer el log despues (gotcha 479).
# Fuente: scripts/plan_breath_air_material.py -> VR_Test/Saved/ClaudeScripts/aliento/breath_air_build.json.
MT = 'editor_toolset.toolsets.material.MaterialTools.'
MIT = 'editor_toolset.toolsets.material_instance.MaterialInstanceTools.'
OT = 'editor_toolset.toolsets.object.ObjectTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
PLAN = 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/aliento/breath_air_build.json'
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
    ok, txt = T(AS + 'read_file', {'file_path': PLAN})
    if not ok:
        return {'err': 'no pude leer el plan', 'log': LOG}
    plan = json.loads(txt)
    MATP = plan['material']
    folder, NAME = MATP.rsplit('/', 1)
    MATR = MATP + '.' + NAME
    MAT = {'refPath': MATR}
    ok, ex = T(AS + 'exists', {'path': MATP})
    if not ex:
        ok, r = T(MT + 'create_material', {'folder_path': folder, 'asset_name': NAME})
        out['creado'] = ok
    S(MATR, plan['flags'])
    out['flags'] = G(MATR, list(plan['flags'].keys()))
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
    creados = 0
    upd = 0
    for i, p in enumerate(plan['params']):
        if p['kind'] == 'vector':
            d = p['default']
            vals = {'Group': p['group'], 'DefaultValue': {'r': d[0], 'g': d[1], 'b': d[2], 'a': d[3]}}
        else:
            vals = {'Group': p['group'], 'DefaultValue': p['default']}
        if p['name'] in byParam:
            S(byParam[p['name']], vals)
            upd += 1
            continue
        cls = 'MaterialExpressionVectorParameter' if p['kind'] == 'vector' else 'MaterialExpressionScalarParameter'
        ok, r = T(MT + 'add_expression', {'material_or_function': MAT, 'expression_class': {'refPath': '/Script/Engine.' + cls}, 'x': -2200 + (i // 16) * 300, 'y': -1100 + (i % 16) * 130})
        if not ok:
            continue
        vals['ParameterName'] = p['name']
        S(r['refPath'], vals)
        byParam[p['name']] = r['refPath']
        creados += 1
    out['params'] = {'creados': creados, 'actualizados': upd, 'total': len(byParam),
                     'sobrantes': sorted(n for n in byParam if n not in set(q['name'] for q in plan['params']))}
    def helper(desc, cls, props, xx, yy):
        if desc in byDesc:
            S(byDesc[desc], props) if props else None
            return byDesc[desc]
        ok, r = T(MT + 'add_expression', {'material_or_function': MAT, 'expression_class': {'refPath': '/Script/Engine.' + cls}, 'x': xx, 'y': yy})
        if not ok:
            return None
        pr = dict(props)
        pr['Desc'] = desc
        S(r['refPath'], pr)
        byDesc[desc] = r['refPath']
        return r['refPath']
    H = {}
    H['A_LP'] = helper('A_LP', 'MaterialExpressionLocalPosition', {}, -900, -1000)
    for k in range(4):
        H['A_UV%d' % k] = helper('A_UV%d' % k, 'MaterialExpressionTextureCoordinate', {'CoordinateIndex': k}, -900, -900 + 90 * k)
    H['A_CamPos'] = helper('A_CamPos', 'MaterialExpressionCameraPositionWS', {}, -1100, -500)
    H['A_CamL'] = helper('A_CamL', 'MaterialExpressionTransformPosition', {'TransformSourceType': 'TRANSFORMPOSSOURCE_World', 'TransformType': 'TRANSFORMPOSSOURCE_Local'}, -900, -500)
    H['A_WPO'] = helper('A_WPO', 'MaterialExpressionTransform', {'TransformSourceType': 'TRANSFORMSOURCE_Local', 'TransformType': 'TRANSFORM_World'}, 300, -900)
    H['A_VI'] = helper('A_VI', 'MaterialExpressionVertexInterpolator', {}, 300, -500)
    def ins(ref):
        ok, v = T(MT + 'get_expression_input_names', {'material_or_function': MAT, 'expression': {'refPath': ref}})
        return v or []
    cons = 0
    ci = ins(H['A_CamL'])
    cons += C(H['A_CamPos'], '', H['A_CamL'], ci[0] if ci else '')
    pos = {'BreathAirVS': (-100, -900), 'BreathAirPS': (600, -300)}
    res = {}
    for c in plan['customs']:
        d = c['desc']
        if d not in cust:
            ok, r = T(MT + 'add_expression', {'material_or_function': MAT, 'expression_class': {'refPath': '/Script/Engine.MaterialExpressionCustom'}, 'x': pos[d][0], 'y': pos[d][1]})
            if not ok:
                res[d] = 'no se pudo crear'
                continue
            cust[d] = r['refPath']
        ref = cust[d]
        S(ref, {'Description': d, 'OutputType': c['outputType'], 'Code': c['code']})
        S(ref, {'AdditionalOutputs': []})
        S(ref, {'AdditionalOutputs': c['additionalOutputs']})
        S(ref, {'Inputs': []})
        S(ref, {'Inputs': [{'inputName': e['name']} for e in c['inputs']]})
        okc = 0
        fallos = []
        for e in c['inputs']:
            s = e['src']
            k = s['kind']
            if k == 'param':
                frm, fo = byParam.get(s['param']), (s['pin'] if s['vector'] else '')
            elif k == 'localpos':
                frm, fo = H['A_LP'], 'XYZ'
            elif k == 'texcoord':
                frm, fo = H['A_UV%d' % s['index']], ''
            elif k == 'campos_local':
                frm, fo = H['A_CamL'], ''
            elif k == 'vi':
                frm, fo = H['A_VI'], 'PS'
            else:
                frm, fo = None, ''
            if frm and C(frm, fo, ref, e['name']):
                okc += 1
            else:
                fallos.append(e['name'])
        res[d] = {'entradas': len(c['inputs']), 'conectadas': okc, 'fallos': fallos}
    out['customs'] = res
    vs, ps = cust.get('BreathAirVS'), cust.get('BreathAirPS')
    extra = 0
    if vs and ps:
        extra += C(vs, 'return', H['A_WPO'], 'None')
        extra += C(vs, 'AirV', H['A_VI'], 'VS')
        extra += T(MT + 'connect_to_output', {'expression': {'refPath': H['A_WPO']}, 'output_name': '', 'material_property': 'MP_WorldPositionOffset'})[0]
        extra += T(MT + 'connect_to_output', {'expression': {'refPath': ps}, 'output_name': 'return', 'material_property': 'MP_EmissiveColor'})[0]
        extra += T(MT + 'connect_to_output', {'expression': {'refPath': ps}, 'output_name': 'Alpha', 'material_property': 'MP_Opacity'})[0]
    out['internas_y_salidas_ok'] = '%d de 5' % extra
    out['helpers'] = sorted(k for k, v in H.items() if v)
    out['refs'] = {k: v.split(':')[-1] for k, v in cust.items()}
    MIP = plan['instance']
    mfolder, MINAME = MIP.rsplit('/', 1)
    ok, ex = T(AS + 'exists', {'path': MIP})
    if not ex:
        ok, r = T(MIT + 'create', {'folder_path': mfolder, 'asset_name': MINAME, 'parent': MAT})
        out['mi_creada'] = ok
    out['conexiones_helpers'] = cons
    out['log'] = LOG[:30]
    return out
result = run()
