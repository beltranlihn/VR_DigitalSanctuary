import json
# apply_sc_materials.py - arma los maestros de la familia + la aparicion 'luz primero' (M_SCObject_SC, M_SCLight_SC,
# M_AppearTrace_SC, M_SCChargeSlider_SC, M_BioSensorWaves_SC) desde Appear/sc_materials_build.json
# (plan_sc_materials.py). MODE = 'masters' arma los maestros (sin recompilar: el recompile va aparte para leer el log);
# MODE = 'instances' crea las MI, les pone sus valores y asigna los slots de las mallas.
# Se pega ENTERO como `script` de execute_tool_script (sin `result = run()`, gotcha 493). Idempotente. Nunca levanta.
MODE = 'masters'
MT = 'editor_toolset.toolsets.material.MaterialTools.'
MIT = 'editor_toolset.toolsets.material_instance.MaterialInstanceTools.'
OT = 'editor_toolset.toolsets.object.ObjectTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
SMT = 'editor_toolset.toolsets.static_mesh.StaticMeshTools.'
PLAN = 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/Appear/sc_materials_build.json'
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
    if not frm or not to:
        return False
    return T(MT + 'connect_expressions', {'from_expression': {'refPath': frm}, 'from_output_name': fout, 'to_expression': {'refPath': to}, 'to_input_name': tin})[0]
def R(path):
    return path + '.' + path.rsplit('/', 1)[1]
def run():
  try:
    ok, txt = T(AS + 'read_file', {'file_path': PLAN})
    if not ok:
        return {'err': 'no pude leer el plan', 'log': LOG}
    plan = json.loads(txt)
    out = {}
    if MODE == 'masters':
        for M in plan['materials']:
            out[M['material'].rsplit('/', 1)[1]] = master(M)
    else:
        out['instancias'] = instances(plan)
        out['slots'] = assign(plan)
    out['log'] = LOG[:40]
    return out
  except BaseException as e:
    return {'err': 'run :: ' + str(e)[:300], 'log': LOG}
def master(M):
    out = {}
    MATP = M['material']
    folder, NAME = MATP.rsplit('/', 1)
    MATR = R(MATP)
    MAT = {'refPath': MATR}
    ok, ex = T(AS + 'exists', {'path': MATP})
    if not ex:
        ok, r = T(MT + 'create_material', {'folder_path': folder, 'asset_name': NAME})
        out['creado'] = ok
        if not ok:
            return out
    S(MATR, M['flags'])
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
    n = 0
    for i, p in enumerate(M['params']):
        if p['kind'] == 'vector':
            d = p['default']
            vals = {'Group': p['group'], 'DefaultValue': {'r': d[0], 'g': d[1], 'b': d[2], 'a': d[3]}}
            cls = 'MaterialExpressionVectorParameter'
        else:
            vals = {'Group': p['group'], 'DefaultValue': p['default']}
            cls = 'MaterialExpressionScalarParameter'
        if p['name'] in byParam:
            S(byParam[p['name']], vals)
            continue
        ok, r = T(MT + 'add_expression', {'material_or_function': MAT, 'expression_class': {'refPath': '/Script/Engine.' + cls}, 'x': -1400 + (i // 12) * 300, 'y': -700 + (i % 12) * 120})
        if not ok:
            continue
        vals['ParameterName'] = p['name']
        S(r['refPath'], vals)
        byParam[p['name']] = r['refPath']
        n += 1
    out['params_nuevos'] = n
    def helper(desc, cls, props, xx, yy):
        if desc in byDesc:
            return byDesc[desc]
        ok, r = T(MT + 'add_expression', {'material_or_function': MAT, 'expression_class': {'refPath': '/Script/Engine.' + cls}, 'x': xx, 'y': yy})
        if not ok:
            return None
        pr = dict(props)
        pr['Desc'] = desc
        S(r['refPath'], pr)
        byDesc[desc] = r['refPath']
        return r['refPath']
    tex = {}
    for k, t in enumerate(M.get('textures', [])):
        if t['name'] in byParam:
            tex[t['name']] = byParam[t['name']]
            continue
        ok, r = T(MT + 'add_expression', {'material_or_function': MAT, 'expression_class': {'refPath': '/Script/Engine.MaterialExpressionTextureSampleParameter2D'}, 'x': -1000, 'y': -900 - 250 * k})
        if not ok:
            continue
        S(r['refPath'], {'ParameterName': t['name'], 'Group': t['group'], 'Texture': {'refPath': t['default']}})
        uvh = helper('UV%d' % t['uv'], 'MaterialExpressionTextureCoordinate', {'CoordinateIndex': t['uv']}, -1300, -900)
        C(uvh, '', r['refPath'], 'UVs')
        tex[t['name']] = r['refPath']
        byParam[t['name']] = r['refPath']
    c = M['custom']
    d = c['desc']
    if d not in cust:
        ok, r = T(MT + 'add_expression', {'material_or_function': MAT, 'expression_class': {'refPath': '/Script/Engine.MaterialExpressionCustom'}, 'x': -300, 'y': -200})
        if not ok:
            out['custom'] = 'no se pudo crear'
            return out
        cust[d] = r['refPath']
    ref = cust[d]
    S(ref, {'Description': d, 'OutputType': c['outputType'], 'Code': c['code']})
    S(ref, {'Inputs': []})
    S(ref, {'Inputs': [{'inputName': e['name']} for e in c['inputs']]})
    okc, fallos = 0, []
    for e in c['inputs']:
        s = e['src']
        k = s['kind']
        if k == 'param':
            frm, fo = byParam.get(s['param']), s['pin']
        elif k == 'texparam':
            frm, fo = tex.get(s['param']), s['pin']
        elif k == 'texcoord':
            frm, fo = helper('UV%d' % s['index'], 'MaterialExpressionTextureCoordinate', {'CoordinateIndex': s['index']}, -1300, -900 + 100 * s['index']), ''
        elif k == 'localpos':
            frm, fo = helper('LP', 'MaterialExpressionLocalPosition', {}, -1300, -1100), 'XYZ'
        elif k == 'normalws':
            frm, fo = helper('NWS', 'MaterialExpressionVertexNormalWS', {}, -1300, -1200), ''
        elif k == 'camvec':
            frm, fo = helper('CV', 'MaterialExpressionCameraVectorWS', {}, -1300, -1300), ''
        elif k == 'time':
            frm, fo = helper('TIME', 'MaterialExpressionTime', {}, -1300, -1400), ''
        else:
            frm, fo = None, ''
        if frm and C(frm, fo, ref, e['name']):
            okc += 1
        else:
            fallos.append(e['name'])
    out['entradas'] = '%d de %d' % (okc, len(c['inputs']))
    out['fallos'] = fallos
    out['emissive'] = T(MT + 'connect_to_output', {'expression': {'refPath': ref}, 'output_name': '', 'material_property': 'MP_EmissiveColor'})[0]
    out['flags'] = G(MATR, list(M['flags'].keys()))
    return out
def instances(plan):
    res = {}
    for I in plan['instances']:
        p = I['path']
        folder, name = p.rsplit('/', 1)
        ok, ex = T(AS + 'exists', {'path': p})
        if not ex:
            ok, r = T(MIT + 'create', {'folder_path': folder, 'asset_name': name, 'parent': {'refPath': R(I['parent'])}})
            if not ok:
                res[name] = 'fallo'
                continue
        ref = {'refPath': R(p)}
        n = 0
        for k, v in I['scalars'].items():
            n += T(MIT + 'set_scalar_parameter', {'instance': ref, 'name': k, 'value': v})[0]
        for k, v in I['vectors'].items():
            n += T(MIT + 'set_vector_parameter', {'instance': ref, 'name': k, 'value': {'r': v[0], 'g': v[1], 'b': v[2], 'a': v[3]}})[0]
        for k, v in I['textures'].items():
            n += T(MIT + 'set_texture_parameter', {'instance': ref, 'name': k, 'value': {'refPath': v}})[0]
        res[name] = n
    return res
def assign(plan):
    res = {}
    for mesh, slots in plan['assign'].items():
        n = 0
        for slot, mat in slots.items():
            n += T(SMT + 'set_material', {'mesh': {'refPath': R(mesh)}, 'slot_name': slot, 'material': {'refPath': R(mat)}})[0]
        res[mesh.rsplit('/', 1)[1]] = '%d de %d' % (n, len(slots))
    return res
