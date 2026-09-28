import json
MT = 'editor_toolset.toolsets.material.MaterialTools.'
OT = 'editor_toolset.toolsets.object.ObjectTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
MATR = '/Game/SoulCharger/Mechanics/Breath/Valley/M_BreathValley_SC.M_BreathValley_SC'
MAT = {'refPath': MATR}
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
    try:
        return json.loads(v) if ok and isinstance(v, str) else None
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
    ok, txt = T(AS + 'read_file', {'file_path': 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/valley_build.json'})
    plan = json.loads(txt)
    ok, exprs = T(MT + 'get_expressions', {'material_or_function': MAT})
    byParam = {}
    desc = {}
    cust = {}
    for e in exprs:
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
                desc[v['Desc']] = r
    pos = {'ValleyHeightVS': (-100, -900), 'ValleyGradVS': (-100, -600), 'ValleyPS': (200, 100)}
    res = {}
    for c in plan['customs']:
        d = c['desc']
        if d not in cust:
            ok, r = T(MT + 'add_expression', {'material_or_function': MAT, 'expression_class': {'refPath': '/Script/Engine.MaterialExpressionCustom'}, 'x': pos[d][0], 'y': pos[d][1]})
            if not ok:
                continue
            cust[d] = r['refPath']
        ref = cust[d]
        S(ref, {'Description': d, 'OutputType': c['outputType'], 'Code': c['code']})
        S(ref, {'Inputs': []})
        S(ref, {'Inputs': [{'inputName': e['name']} for e in c['inputs']]})
        okc = 0
        fallos = []
        for e in c['inputs']:
            s = e['src']
            k = s['kind']
            if k == 'param':
                frm, fo = byParam[s['param']], ('RGB' if s['vector'] else '')
            elif k == 'localpos':
                frm, fo = desc['V_LP'], 'XYZ'
            elif k == 'vi':
                frm, fo = desc['V_VI%d' % s['index']], 'PS'
            elif k == 'camlocal':
                frm, fo = desc['V_CamL'], ''
            elif k == 'dist':
                frm, fo = desc['V_Dist'], ''
            elif k == 'dir':
                frm, fo = desc['D_' + e['name']], ''
            elif k == 'cos':
                frm, fo = desc['C_' + e['name']], ''
            elif k == 'mul':
                frm, fo = desc['M_' + e['name']], ''
            elif k == 'mix':
                frm, fo = desc['X_' + e['name']], ''
            elif k == 'tint':
                frm, fo = desc['T_' + e['name']], ''
            else:
                fallos.append(e['name'])
                continue
            if C(frm, fo, ref, e['name']):
                okc += 1
            else:
                fallos.append(e['name'])
        res[d] = {'entradas': len(c['inputs']), 'conectadas': okc, 'fallos': fallos}
    extra = 0
    extra += C(cust['ValleyGradVS'], '', desc['V_VI0'], 'VS')
    extra += C(desc['V_LP'], 'XYZ', desc['V_VI1'], 'VS')
    extra += C(cust['ValleyHeightVS'], '', desc['V_WPO'], 'None')
    out['customs'] = res
    out['internas_ok'] = extra
    out['refs'] = {k: v.split(':')[-1] for k, v in cust.items()}
    out['log'] = LOG[:20]
    return out
result = run()
