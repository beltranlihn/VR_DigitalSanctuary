import json
# apply_vida_gust_valley.py - agrega LA FRANJA DE LA RAFAGA a M_BreathValley_SC desde vida_build.json (seccion "valley").
# Se pega ENTERO como `script` de ProgrammaticToolset.execute_tool_script. Idempotente (parametros por nombre, el Custom
# por Description): se puede correr dos veces. Nunca levanta excepcion (try/except BaseException, gotcha 231). NO
# recompila (el recompile va aparte, gotcha 479) y NO borra nada.
# Que hace (y nada mas):
#   1. crea o actualiza 5 VectorParameter (GustP, GustQ, GustR, GustK, GustS; grupo "10 - Rafaga"; defaults = NEUTRO);
#   2. crea o actualiza el Custom "GustLeanVS" (codigo, salida float4, 8 entradas) y lo cablea: G <- ValleyGradVS,
#      LP <- V_LP (XYZ), Part <- Part, Gust* <- sus parametros (RGBA);
#   3. cambia la entrada VS de V_VI0: antes ValleyGradVS, ahora GustLeanVS. Es el UNICO cambio del grafo del valle.
#   Con GustK = (0,0,0,0) (el default) la rama de GustLeanVS se saltea y devuelve la salida de ValleyGradVS sin tocar:
#   NEUTRO EXACTO EN EL MODELO (Vida_check.py, HLSL traducido). En la GPU el shader del valle se recompila con un Custom
#   mas en la cadena y no esta demostrado que el compilador deje los mismos bits aguas arriba (FMA, reordenamiento): en
#   el editor se verifica con el control negativo del paso M5 (captura antes/despues, cielo y piso cercano iguales).
# Aborta SIN TOCAR NADA si falta algo del valle (ValleyGradVS, V_VI0, V_LP o Part): no deja un cableado a medias.
# Deshacer: rollback_vida_gust_valley.py (vuelve a conectar ValleyGradVS -> V_VI0).
# OJO: si alguien vuelve a pegar apply_valley_material_B.py, ese script reconecta ValleyGradVS -> V_VI0 y la franja se
#    apaga (neutro, sin error): volver a pegar ESTE script. Y apply_valley_material_A.py lista los Gust* como
#    "sobrantes": NO borrarlos (son de la capa de vida).
MT = 'editor_toolset.toolsets.material.MaterialTools.'
OT = 'editor_toolset.toolsets.object.ObjectTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
PLAN = 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/vida/vida_build.json'
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
    plan = json.loads(txt)['valley']
    MATP = plan['material']
    NAME = MATP.rsplit('/', 1)[1]
    MATR = MATP + '.' + NAME
    MAT = {'refPath': MATR}
    ok, exprs = T(MT + 'get_expressions', {'material_or_function': MAT})
    if not ok or not exprs:
        return {'err': 'no pude leer las expresiones del valle', 'log': LOG}
    byParam, byDesc, cust = {}, {}, {}
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
                byDesc[v['Desc']] = r
    faltan = [n for n, d in ((plan['grad_desc'], cust), (plan['vi_desc'], byDesc), (plan['lp_desc'], byDesc), ('Part', byParam)) if n not in d]
    if faltan:
        return {'err': 'al valle le falta %s: no toco nada' % faltan, 'log': LOG}
    creados = 0
    upd = 0
    for i, p in enumerate(plan['params']):
        d = p['default']
        vals = {'Group': p['group'], 'DefaultValue': {'r': d[0], 'g': d[1], 'b': d[2], 'a': d[3]}}
        if p['name'] in byParam:
            S(byParam[p['name']], vals)
            upd += 1
            continue
        ok, r = T(MT + 'add_expression', {'material_or_function': MAT, 'expression_class': {'refPath': '/Script/Engine.MaterialExpressionVectorParameter'}, 'x': -700, 'y': -2200 + i * 130})
        if not ok:
            continue
        vals['ParameterName'] = p['name']
        S(r['refPath'], vals)
        byParam[p['name']] = r['refPath']
        creados += 1
    out['params'] = {'creados': creados, 'actualizados': upd, 'gust': sorted(n for n in byParam if n.startswith('Gust'))}
    c = plan['custom']
    d = c['desc']
    if d not in cust:
        ok, r = T(MT + 'add_expression', {'material_or_function': MAT, 'expression_class': {'refPath': '/Script/Engine.MaterialExpressionCustom'}, 'x': 150, 'y': -700})
        if not ok:
            return {'err': 'no pude crear el Custom %s' % d, 'log': LOG, 'params': out['params']}
        cust[d] = r['refPath']
        out['custom_creado'] = True
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
            frm, fo = byParam.get(s['param']), (s['pin'] if s['vector'] else '')
        elif k == 'localpos':
            frm, fo = byDesc[plan['lp_desc']], 'XYZ'
        elif k == 'custom':
            frm, fo = cust.get(s['desc']), ''
        else:
            frm, fo = None, ''
        if frm and C(frm, fo, ref, e['name']):
            okc += 1
        else:
            fallos.append(e['name'])
    out['custom'] = {'entradas': len(c['inputs']), 'conectadas': okc, 'fallos': fallos}
    # el unico cambio del grafo del valle: el interpolador del gradiente pasa a leer GustLeanVS
    if not fallos:
        out['vi0_a_gust'] = C(ref, '', byDesc[plan['vi_desc']], 'VS')
    else:
        out['vi0_a_gust'] = False
        out['aviso'] = 'no reconecte V_VI0 (entradas sin conectar): el valle sigue leyendo ValleyGradVS'
    out['refs'] = {'GustLeanVS': ref.split(':')[-1], 'ValleyGradVS': cust[plan['grad_desc']].split(':')[-1],
                   'V_VI0': byDesc[plan['vi_desc']].split(':')[-1]}
    out['log'] = LOG[:30]
    return out
result = run()
