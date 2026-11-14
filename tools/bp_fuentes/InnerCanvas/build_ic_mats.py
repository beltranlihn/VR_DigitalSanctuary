# build_ic_mats.py - arma M_ICKey_IC y M_ICSpace_IC (Inner Canvas) con un Custom de HLSL cada uno, y las MI del espacio.
# Se corre con execute_tool_script en Unreal. Idempotente (busca parametros por nombre y el Custom por Description).
# Nunca levanta excepcion: los errores vuelven como dato. Patron: .claude/skills/unreal-vr/scripts/apply_chladni_material.py
import json
MT = 'editor_toolset.toolsets.material.MaterialTools.'
MIT = 'editor_toolset.toolsets.material_instance.MaterialInstanceTools.'
OT = 'editor_toolset.toolsets.object.ObjectTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
DIR = 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/InnerCanvas/mat/'
FOLDER = '/Game/InnerCanvas/Materials'
LOG = []
PLANS = [
    dict(name='M_ICKey_IC', code='ICKeyPS.txt', two=True,
         params=[('Tex', 'texture', '/Game/InnerCanvas/Textures/T_ICKeyAtlas.T_ICKeyAtlas'), ('Rect', 'vector', [0.0, 0.0, 0.125]),
                 ('Asp', 'scalar', 1.0), ('Hover', 'scalar', 0.0), ('Fade', 'scalar', 1.0), ('Accent', 'vector', [0.45, 1.0, 0.65]),
                 ('Label', 'vector', [1.0, 1.0, 1.0])],
         inputs=[('UV', 'uv'), ('Tex', 'Tex'), ('Rect', 'Rect'), ('Asp', 'Asp'), ('Hover', 'Hover'), ('Fade', 'Fade'), ('Accent', 'Accent'), ('Label', 'Label')]),
    dict(name='M_ICSpace_IC', code='ICSpacePS.txt', two=True,
         params=[('Mode', 'scalar', 0.0), ('Size', 'scalar', 300.0), ('Cell', 'scalar', 50.0), ('Alpha', 'scalar', 0.0),
                 ('Color', 'vector', [0.55, 1.0, 0.75])],
         inputs=[('UV', 'uv'), ('Mode', 'Mode'), ('Size', 'Size'), ('Cell', 'Cell'), ('Alpha', 'Alpha'), ('Color', 'Color')]),
]
MIS = [('MI_ICSpaceWall_IC', 'M_ICSpace_IC', {'Mode': 0.0}), ('MI_ICSpaceFloor_IC', 'M_ICSpace_IC', {'Mode': 1.0})]


def T(name, payload):
    try:
        return True, execute_tool(name, json.dumps(payload))['returnValue']
    except BaseException as e:
        LOG.append(name.split('.')[-1] + ' :: ' + str(e)[:220])
        return False, None


def G(ref, props):
    ok, val = T(OT + 'get_properties', {'instance': {'refPath': ref}, 'properties': props})
    try:
        return json.loads(val) if ok and val else None
    except BaseException:
        return None


def S(ref, vals):
    return T(OT + 'set_properties', {'instance': {'refPath': ref}, 'values': json.dumps(vals)})[0]


def C(frm, fout, to, tin):
    return T(MT + 'connect_expressions', {'from_expression': {'refPath': frm}, 'from_output_name': fout, 'to_expression': {'refPath': to}, 'to_input_name': tin})[0]


def one(plan):
    out = {}
    path = FOLDER + '/' + plan['name']
    ok, ex = T(AS + 'exists', {'path': path})
    if not ex:
        T(MT + 'create_material', {'folder_path': FOLDER, 'asset_name': plan['name']})
    MATR = path + '.' + plan['name']
    MAT = {'refPath': MATR}
    S(MATR, {'shadingModel': 'MSM_Unlit', 'blendMode': 'BLEND_Translucent', 'twoSided': plan['two']})
    out['flags'] = G(MATR, ['shadingModel', 'blendMode', 'twoSided'])
    ok, exprs = T(MT + 'get_expressions', {'material_or_function': MAT})
    byParam, cust, byDesc = {}, None, {}
    for e in (exprs or []):
        r = e['refPath']
        cls = r.split(':')[-1]
        if 'Parameter' in cls:
            g = G(r, ['ParameterName'])
            if g:
                byParam[g['ParameterName']] = r
        elif 'Custom' in cls:
            cust = r
        else:
            g = G(r, ['Desc'])
            if g and g.get('Desc'):
                byDesc[g['Desc']] = r
    for i, (n, k, d) in enumerate(plan['params']):
        if k == 'vector':
            cls, vals = 'MaterialExpressionVectorParameter', {'DefaultValue': {'r': d[0], 'g': d[1], 'b': d[2], 'a': 1.0}}
        elif k == 'texture':
            cls, vals = 'MaterialExpressionTextureObjectParameter', {'Texture': {'refPath': d}, 'SamplerType': 'SAMPLERTYPE_LinearGrayscale'}
        else:
            cls, vals = 'MaterialExpressionScalarParameter', {'DefaultValue': d}
        if n not in byParam:
            ok, r = T(MT + 'add_expression', {'material_or_function': MAT, 'expression_class': {'refPath': '/Script/Engine.' + cls}, 'x': -900, 'y': -400 + i * 140})
            if not ok:
                continue
            byParam[n] = r['refPath']
            vals['ParameterName'] = n
        S(byParam[n], vals)
    def helper(desc, cls, props, x, y):
        if desc in byDesc:
            return byDesc[desc]
        ok, r = T(MT + 'add_expression', {'material_or_function': MAT, 'expression_class': {'refPath': '/Script/Engine.' + cls}, 'x': x, 'y': y})
        if not ok:
            return None
        pr = dict(props)
        pr['Desc'] = desc
        S(r['refPath'], pr)
        byDesc[desc] = r['refPath']
        return r['refPath']
    uv = helper('H_UV', 'MaterialExpressionTextureCoordinate', {}, -900, -600)
    mrgb = helper('H_RGB', 'MaterialExpressionComponentMask', {'R': True, 'G': True, 'B': True, 'A': False}, 300, 0)
    ma = helper('H_A', 'MaterialExpressionComponentMask', {'R': False, 'G': False, 'B': False, 'A': True}, 300, 200)
    if not cust:
        ok, r = T(MT + 'add_expression', {'material_or_function': MAT, 'expression_class': {'refPath': '/Script/Engine.MaterialExpressionCustom'}, 'x': -300, 'y': 0})
        cust = r['refPath'] if ok else None
    if not cust:
        out['err'] = 'sin Custom'
        return out
    ok, code = T(AS + 'read_file', {'file_path': DIR + plan['code']})
    S(cust, {'Description': plan['name'] + 'PS', 'OutputType': 'CMOT_Float4', 'Code': code})
    S(cust, {'Inputs': []})
    S(cust, {'Inputs': [{'inputName': n} for n, _ in plan['inputs']]})
    con, fallos = 0, []
    for n, src in plan['inputs']:
        if src == 'uv':
            frm, fo = uv, ''
        else:
            frm = byParam.get(src)
            kind = [k for (pn, k, d) in plan['params'] if pn == src][0]
            fo = 'RGB' if kind == 'vector' else ''
        if frm and C(frm, fo, cust, n):
            con += 1
        else:
            fallos.append(n)
    con += C(cust, '', mrgb, 'None') + C(cust, '', ma, 'None')
    con += T(MT + 'connect_to_output', {'expression': {'refPath': mrgb}, 'output_name': '', 'material_property': 'MP_EmissiveColor'})[0]
    con += T(MT + 'connect_to_output', {'expression': {'refPath': ma}, 'output_name': '', 'material_property': 'MP_Opacity'})[0]
    T(MT + 'recompile', {'material_or_function': MAT})
    out['conexiones'] = con
    out['fallos'] = fallos
    out['params'] = sorted(byParam.keys())
    return out


def run():
    try:
        res = {}
        for p in PLANS:
            res[p['name']] = one(p)
        for name, parent, sc in MIS:
            path = FOLDER + '/' + name
            ok, ex = T(AS + 'exists', {'path': path})
            if not ex:
                T(MIT + 'create', {'folder_path': FOLDER, 'asset_name': name, 'parent': {'refPath': FOLDER + '/' + parent + '.' + parent}})
            for k, val in sc.items():
                T(MIT + 'set_scalar_parameter', {'instance': {'refPath': path + '.' + name}, 'name': k, 'value': val})
        T(AS + 'save_assets', {'asset_paths': [FOLDER + '/' + p['name'] for p in PLANS] + [FOLDER + '/' + m[0] for m in MIS]})
        res['log'] = LOG[:30]
        return res
    except BaseException as e:
        return {'err': str(e)[:300], 'log': LOG[:30]}
