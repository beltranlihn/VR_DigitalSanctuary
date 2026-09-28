import json
# apply_draw_sea_material.py - arma M_DrawSea_SC y M_DrawDust_SC (+ sus MI) desde oceano/draw_sea_build.json.
# Se pega ENTERO como `script` de ProgrammaticToolset.execute_tool_script. IDEMPOTENTE (gotcha 489: la tool corre el
# script DOS veces): parametros por nombre, Customs por Description, helpers por Desc, assets por exists.
# Nunca levanta excepcion (gotchas 60/418/231): todo dentro de try/except BaseException y los errores vuelven como DATO.
# Nombres de pin (gotchas 446/447/453/482): Custom de UNA salida = '' (NO 'return'); VectorParameter 'RGB'/'RGBA';
# LocalPosition 'XYZ'; VertexInterpolator entra 'VS' y sale 'PS'; Transform entra 'None'.
# NO recompila (gotcha 479): el recompile va en una llamada aparte, para leer el log despues.
# Fuente: scripts/plan_draw_sea_material.py. Ensayo sin Unreal: scripts/dryrun_draw_sea.py. Receta copiada de
# apply_breath_air_material.py (el pipeline probado del aliento).
MT = 'editor_toolset.toolsets.material.MaterialTools.'
MIT = 'editor_toolset.toolsets.material_instance.MaterialInstanceTools.'
OT = 'editor_toolset.toolsets.object.ObjectTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
PLAN = 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/oceano/draw_sea_build.json'
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
    if not frm or not to:
        return False
    return T(MT + 'connect_expressions', {'from_expression': {'refPath': frm}, 'from_output_name': fout, 'to_expression': {'refPath': to}, 'to_input_name': tin})[0]
def run():
  try:
    ok, txt = T(AS + 'read_file', {'file_path': PLAN})
    if not ok:
        return {'err': 'no pude leer el plan', 'log': LOG}
    plan = json.loads(txt)
    out = {}
    for M in plan['materials']:
        out[M['material'].rsplit('/', 1)[1]] = one(M)
    out['log'] = LOG[:40]
    return out
  except BaseException as e:
    return {'err': 'run :: ' + str(e)[:300], 'log': LOG}
def one(M):
    out = {}
    MATP = M['material']
    folder, NAME = MATP.rsplit('/', 1)
    MATR = MATP + '.' + NAME
    MAT = {'refPath': MATR}
    P = 'S_' if 'Sea' in NAME else 'D_'
    ok, ex = T(AS + 'exists', {'path': MATP})
    if not ex:
        ok, r = T(MT + 'create_material', {'folder_path': folder, 'asset_name': NAME})
        out['creado'] = ok
        if not ok:
            return out
    S(MATR, M['flags'])
    out['flags'] = G(MATR, list(M['flags'].keys()))
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
    creados, upd = 0, 0
    for i, p in enumerate(M['params']):
        d = p['default']
        if p['kind'] == 'vector':
            vals = {'Group': p['group'], 'DefaultValue': {'r': d[0], 'g': d[1], 'b': d[2], 'a': d[3]}}
        else:
            vals = {'Group': p['group'], 'DefaultValue': d}
        if p['name'] in byParam:
            S(byParam[p['name']], vals)
            upd += 1
            continue
        cls = 'MaterialExpressionVectorParameter' if p['kind'] == 'vector' else 'MaterialExpressionScalarParameter'
        ok, r = T(MT + 'add_expression', {'material_or_function': MAT, 'expression_class': {'refPath': '/Script/Engine.' + cls}, 'x': -2400 + (i // 16) * 300, 'y': -1200 + (i % 16) * 130})
        if not ok:
            continue
        vals['ParameterName'] = p['name']
        S(r['refPath'], vals)
        byParam[p['name']] = r['refPath']
        creados += 1
    out['params'] = {'creados': creados, 'actualizados': upd, 'total': len(byParam),
                     'sobrantes': sorted(n for n in byParam if n not in set(q['name'] for q in M['params']))}
    def helper(desc, cls, props, xx, yy):
        if desc in byDesc:
            if props:
                S(byDesc[desc], props)
            return byDesc[desc]
        ok, r = T(MT + 'add_expression', {'material_or_function': MAT, 'expression_class': {'refPath': '/Script/Engine.' + cls}, 'x': xx, 'y': yy})
        if not ok:
            return None
        pr = dict(props)
        pr['Desc'] = desc
        S(r['refPath'], pr)
        byDesc[desc] = r['refPath']
        return r['refPath']
    kinds = set(e['src']['kind'] for c in M['customs'] for e in c['inputs'])
    outs = set(c['output'] for c in M['customs'])
    H = {}
    if 'localpos' in kinds:
        H['LP'] = helper(P + 'LP', 'MaterialExpressionLocalPosition', {}, -900, -1000)
    uvs = set(e['src']['index'] for c in M['customs'] for e in c['inputs'] if e['src']['kind'] == 'texcoord')
    for k in range(3):
        if k in uvs:
            H['UV%d' % k] = helper(P + 'UV%d' % k, 'MaterialExpressionTextureCoordinate', {'CoordinateIndex': k}, -900, -900 + 90 * k)
    if 'campos' in kinds or 'relcam' in kinds:
        H['Cam'] = helper(P + 'CamPos', 'MaterialExpressionCameraPositionWS', {}, -1150, -450)
    if 'relcam' in kinds:
        H['WP'] = helper(P + 'WorldPos', 'MaterialExpressionWorldPosition', {}, -1150, -350)
        H['Rel'] = helper(P + 'RelCam', 'MaterialExpressionSubtract', {}, -900, -400)
    if 'vi' in outs:
        H['VI'] = helper(P + 'VI', 'MaterialExpressionVertexInterpolator', {}, 300, -500)
    if 'wpo_local' in outs:
        H['WPO'] = helper(P + 'WPO', 'MaterialExpressionTransform', {'TransformSourceType': 'TRANSFORMSOURCE_Local', 'TransformType': 'TRANSFORM_World'}, 300, -900)
    cons = 0
    if 'Rel' in H:
        cons += C(H['WP'], '', H['Rel'], 'A')
        cons += C(H['Cam'], '', H['Rel'], 'B')
    pos = {'wpo_local': (-100, -900), 'wpo_world': (-100, -900), 'vi': (-100, -500), 'emissive': (600, -200)}
    res = {}
    for c in M['customs']:
        d = c['desc']
        if d not in cust:
            ok, r = T(MT + 'add_expression', {'material_or_function': MAT, 'expression_class': {'refPath': '/Script/Engine.MaterialExpressionCustom'}, 'x': pos[c['output']][0], 'y': pos[c['output']][1]})
            if not ok:
                res[d] = 'no se pudo crear'
                continue
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
            elif k == 'localpos':
                frm, fo = H.get('LP'), 'XYZ'
            elif k == 'texcoord':
                frm, fo = H.get('UV%d' % s['index']), ''
            elif k == 'campos':
                frm, fo = H.get('Cam'), ''
            elif k == 'relcam':
                frm, fo = H.get('Rel'), ''
            elif k == 'vi':
                frm, fo = H.get('VI'), 'PS'
            else:
                frm, fo = None, ''
            if frm and C(frm, fo, ref, e['name']):
                okc += 1
            else:
                fallos.append(e['name'])
        res[d] = {'entradas': len(c['inputs']), 'conectadas': okc, 'fallos': fallos}
    out['customs'] = res
    sal, n_sal = 0, 0
    for c in M['customs']:
        ref = cust.get(c['desc'])
        if not ref:
            continue
        if c['output'] == 'wpo_local':
            n_sal += 2
            sal += C(ref, '', H.get('WPO'), 'None')
            if H.get('WPO'):
                sal += T(MT + 'connect_to_output', {'expression': {'refPath': H['WPO']}, 'output_name': '', 'material_property': 'MP_WorldPositionOffset'})[0]
        elif c['output'] == 'wpo_world':
            n_sal += 1
            sal += T(MT + 'connect_to_output', {'expression': {'refPath': ref}, 'output_name': '', 'material_property': 'MP_WorldPositionOffset'})[0]
        elif c['output'] == 'vi':
            n_sal += 1
            sal += C(ref, '', H.get('VI'), 'VS')
        elif c['output'] == 'emissive':
            n_sal += 1
            sal += T(MT + 'connect_to_output', {'expression': {'refPath': ref}, 'output_name': '', 'material_property': 'MP_EmissiveColor'})[0]
    out['salidas_ok'] = '%d de %d' % (sal, n_sal)
    out['helpers_ok'] = cons
    out['helpers'] = sorted(k for k, v in H.items() if v)
    MIP = M['instance']
    mfolder, MINAME = MIP.rsplit('/', 1)
    ok, ex = T(AS + 'exists', {'path': MIP})
    if not ex:
        ok, r = T(MIT + 'create', {'folder_path': mfolder, 'asset_name': MINAME, 'parent': MAT})
        out['mi_creada'] = ok
    return out
# Solo para el ensayo offline (dryrun lee `result`). AL PEGAR en execute_tool_script, QUITAR esta linea (gotcha 493).
result = run()
