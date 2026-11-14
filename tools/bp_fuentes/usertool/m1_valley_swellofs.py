# m1_valley_swellofs.py - M_BreathValley_SC: parametro SwellTimeOfs (0, '9 - Interno') + codigo y entradas NUEVAS de los dos
# Custom VS (ValleyHeightVS 30 entradas, ValleyGradVS 32) desde valley_build.json (lo regenera plan_valley_material.py).
# Solo toca esos dos Custom: NO recablea ValleyPS ni las conexiones de salida (GradVS -> GustLeanVS/VI0 de la capa de vida,
# HeightVS -> WPO), que dependen de la SALIDA del Custom y no de sus entradas. IDEMPOTENTE. No recompila (va aparte).
import json
MT = 'editor_toolset.toolsets.material.MaterialTools.'
OT = 'editor_toolset.toolsets.object.ObjectTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
MATR = '/Game/SoulCharger/Mechanics/Breath/Valley/M_BreathValley_SC.M_BreathValley_SC'
MAT = {'refPath': MATR}
LOG = []
def T(name, payload):
    try:
        return True, execute_tool(name, json.dumps(payload))['returnValue']
    except BaseException as e:
        LOG.append(name.split('.')[-1] + ' :: ' + str(e)[:200]); return False, None
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
    ok, txt = T(AS + 'read_file', {'file_path': 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/valley_build.json'})
    plan = json.loads(txt)
    ok, exprs = T(MT + 'get_expressions', {'material_or_function': MAT})
    byParam, desc, cust = {}, {}, {}
    for e in exprs:
        r = e['refPath']; cls = r.split(':')[-1]
        if 'Parameter' in cls:
            v = G(r, ['ParameterName'])
            if v: byParam[v['ParameterName']] = r
        elif 'Custom' in cls:
            v = G(r, ['Description'])
            if v: cust[v['Description']] = r
        else:
            v = G(r, ['Desc'])
            if v and v.get('Desc'): desc[v['Desc']] = r
    out = {'antes_param': 'SwellTimeOfs' in byParam}
    if 'SwellTimeOfs' not in byParam:
        ok, r = T(MT + 'add_expression', {'material_or_function': MAT, 'expression_class': {'refPath': '/Script/Engine.MaterialExpressionScalarParameter'}, 'x': -1400, 'y': -300})
        if ok:
            ref = r['refPath']
            S(ref, {'ParameterName': 'SwellTimeOfs'})
            S(ref, {'DefaultValue': 0.0})
            S(ref, {'Group': '9 - Interno'})
            byParam['SwellTimeOfs'] = ref
    out['param'] = G(byParam.get('SwellTimeOfs', ''), ['ParameterName', 'DefaultValue', 'Group']) if 'SwellTimeOfs' in byParam else None
    res = {}
    for c in plan['customs']:
        d = c['desc']
        if d not in ('ValleyHeightVS', 'ValleyGradVS'):
            continue
        ref = cust[d]
        S(ref, {'Code': c['code']})
        S(ref, {'Inputs': []})
        S(ref, {'Inputs': [{'inputName': e['name']} for e in c['inputs']]})
        okc, fallos = 0, []
        for e in c['inputs']:
            s = e['src']; k = s['kind']
            if k == 'param':
                frm, fo = byParam[s['param']], ('RGB' if s['vector'] else '')
            elif k == 'localpos':
                frm, fo = desc['V_LP'], 'XYZ'
            else:
                fallos.append(e['name']); continue
            if C(frm, fo, ref, e['name']):
                okc += 1
            else:
                fallos.append(e['name'])
        res[d] = {'entradas': len(c['inputs']), 'conectadas': okc, 'fallos': fallos}
    out['customs'] = res
    out['log'] = LOG[:12]
    return out
