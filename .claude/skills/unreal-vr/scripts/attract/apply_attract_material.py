# apply_attract_material.py (2026-11-04) - arma M_AttractMote_SC desde VR_Test/Saved/ClaudeScripts/attract_mote_build.json
# (lo genera gen_mote_material.py). Copia del pipeline de apply_chladni_material.py. Se corre con execute_tool_script.
# IDEMPOTENTE: busca parametros por nombre, Customs por Description y helpers por Desc. Nunca levanta (gotcha 60/418).
# El material tiene que existir antes (create_material por llamada directa). Sin `result = run()` (gotcha 493).
import json
MT = 'editor_toolset.toolsets.material.MaterialTools.'
OT = 'editor_toolset.toolsets.object.ObjectTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
LOG = []
DIR = 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/'
# El plan a armar: attract_mote_build.json (chorros) o attract_ring_build.json (ondas). Con 'outputs' en el plan, las
# salidas se cablean desde ahi; sin 'outputs', el cableado de los chorros (MoteVS/MoteAlphaVS/MotePS/MoteOpPS).
PLAN = 'attract_shell_build.json'
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
    ok, txt = T(AS + 'read_file', {'file_path': DIR + PLAN})
    if not ok:
        return {'err': 'no pude leer el plan', 'log': LOG}
    plan = json.loads(txt)
    MATP = plan['material']
    MATR = MATP + '.' + MATP.split('/')[-1]
    MAT = {'refPath': MATR}
    S(MATR, {'shadingModel': 'MSM_Unlit', 'blendMode': plan['blend'], 'twoSided': True,
             'floatPrecisionMode': 'MFPM_Full_MaterialExpressionOnly'})
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
            if v and v['Desc']:
                byDesc[v['Desc']] = r
    creados = 0
    for i, p in enumerate(plan['params']):
        d = p['default']
        vals = {'Group': p['group'], 'DefaultValue': {'r': d[0], 'g': d[1], 'b': d[2], 'a': d[3]},
                'bUseCustomPrimitiveData': True, 'PrimitiveDataIndex': p['cpd']}
        if p['name'] not in byParam:
            ok, r = T(MT + 'add_expression', {'material_or_function': MAT, 'expression_class': {'refPath': '/Script/Engine.MaterialExpressionVectorParameter'}, 'x': -1400, 'y': -900 + i * 160})
            if not ok:
                continue
            byParam[p['name']] = r['refPath']
            vals['ParameterName'] = p['name']
            creados += 1
        S(byParam[p['name']], vals)
    out['params_creados'] = creados
    out['params_cpd'] = [G(byParam[p['name']], ['ParameterName', 'bUseCustomPrimitiveData', 'PrimitiveDataIndex']) for p in plan['params'] if p['name'] in byParam]
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
    H['V_LP'] = helper('V_LP', 'MaterialExpressionLocalPosition', {'IncludedOffsets': 'IncludeOffsets', 'LocalOrigin': 'Instance'}, -1400, -1100)
    usa_uv = any(e['src']['kind'] == 'uv' for c in plan['customs'] for e in c['inputs'])
    H['V_UV'] = helper('V_UV', 'MaterialExpressionTextureCoordinate', {}, -1400, -1250) if usa_uv else None
    usa_vi = ('outputs' not in plan) or any(e['src']['kind'] == 'vi' for c in plan['customs'] for e in c['inputs'])
    H['V_VI1'] = helper('V_VI1', 'MaterialExpressionVertexInterpolator', {}, -300, 300) if usa_vi else None
    usa_tr = ('outputs' not in plan) or any('wpo' in o for o in plan['outputs'])
    H['V_WPO'] = helper('V_WPO', 'MaterialExpressionTransform', {'TransformSourceType': 'TRANSFORMSOURCE_Local', 'TransformType': 'TRANSFORM_World'}, 0, -600) if usa_tr else None
    usa_nw = any(e['src']['kind'] == 'normalws' for c in plan['customs'] for e in c['inputs'])
    H['V_NWS'] = helper('V_NWS', 'MaterialExpressionVertexNormalWS', {}, -1400, -1400) if usa_nw else None
    def outs(ref):
        ok, v = T(MT + 'get_expression_output_names', {'material_or_function': MAT, 'expression': {'refPath': ref}})
        return v or []
    first = plan['params'][0]['name']
    pouts = outs(byParam[first]) if first in byParam else []
    pout = 'RGBA' if 'RGBA' in pouts else ''
    out['param_outputs'] = pouts
    pos = {'MoteVS': (-500, -600), 'MoteAlphaVS': (-700, 300), 'MotePS': (-100, 500), 'MoteOpPS': (-100, 750),
           'RingVS': (-500, -600), 'RingPS': (-100, 300), 'RingOpPS': (-100, 550),
           'ShellVS': (-500, -600), 'ShellPS': (-100, 300), 'ShellOpPS': (-100, 550)}
    res = {}
    for c in plan['customs']:
        d = c['desc']
        if d not in cust:
            xy = pos[d] if d in pos else (-300, 0)
            ok, r = T(MT + 'add_expression', {'material_or_function': MAT, 'expression_class': {'refPath': '/Script/Engine.MaterialExpressionCustom'}, 'x': xy[0], 'y': xy[1]})
            if not ok:
                continue
            cust[d] = r['refPath']
        ref = cust[d]
        ok, code = T(AS + 'read_file', {'file_path': DIR + c['code_file']})
        S(ref, {'Description': d, 'OutputType': c['outputType'], 'Code': code})
        S(ref, {'Inputs': []})
        S(ref, {'Inputs': [{'inputName': e['name']} for e in c['inputs']]})
        okc, fallos = 0, []
        for e in c['inputs']:
            s = e['src']
            k = s['kind']
            if k == 'param':
                frm, fo = byParam.get(s['param']), pout
            elif k == 'localpos':
                frm, fo = H['V_LP'], 'XYZ'
            elif k == 'uv':
                frm, fo = H['V_UV'], ''
            elif k == 'vi':
                frm, fo = H['V_VI1'], 'PS'
            elif k == 'normalws':
                frm, fo = H['V_NWS'], ''
            else:
                frm = None
            if frm and C(frm, fo, ref, e['name']):
                okc += 1
            else:
                fallos.append(e['name'])
        res[d] = {'entradas': len(c['inputs']), 'conectadas': okc, 'fallos': fallos}
    extra = 0
    if 'outputs' in plan:
        for o in plan['outputs']:
            if 'wpo_world' in o:
                extra += T(MT + 'connect_to_output', {'expression': {'refPath': cust[o['custom']]}, 'output_name': '', 'material_property': 'MP_WorldPositionOffset'})[0]
            elif 'wpo' in o:
                extra += C(cust[o['custom']], '', H['V_WPO'], 'None')
                extra += T(MT + 'connect_to_output', {'expression': {'refPath': H['V_WPO']}, 'output_name': '', 'material_property': 'MP_WorldPositionOffset'})[0]
            else:
                extra += T(MT + 'connect_to_output', {'expression': {'refPath': cust[o['custom']]}, 'output_name': '', 'material_property': o['prop']})[0]
    else:
        extra += C(cust['MoteAlphaVS'], '', H['V_VI1'], 'VS')
        extra += C(cust['MoteVS'], '', H['V_WPO'], 'None')
        extra += T(MT + 'connect_to_output', {'expression': {'refPath': H['V_WPO']}, 'output_name': '', 'material_property': 'MP_WorldPositionOffset'})[0]
        extra += T(MT + 'connect_to_output', {'expression': {'refPath': cust['MotePS']}, 'output_name': '', 'material_property': 'MP_EmissiveColor'})[0]
        if 'MoteOpPS' in cust:
            extra += T(MT + 'connect_to_output', {'expression': {'refPath': cust['MoteOpPS']}, 'output_name': '', 'material_property': 'MP_Opacity'})[0]
    out['customs'] = res
    out['salidas_ok'] = extra
    out['log'] = LOG[:25]
    return out
