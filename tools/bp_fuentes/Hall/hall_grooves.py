import json
# hall_grooves.py - HallGroovesPS v6 en el Custom de M_Hall_Interior_SC (junta de las baldosas a -1,7 cm).
# Busca el Custom cuyo code contiene "HallGroovesPS" y le escribe el archivo. NUNCA escribe si la lectura falla o viene
# vacia (gotcha BellArt: un read_file fallido dejo Code = None y el material sin compilar). Recompilar aparte, sin PIE.
M = '/Game/SoulCharger/Mechanics/Hall/M_Hall_Interior_SC.M_Hall_Interior_SC'
SRC = 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/Hall/HallGroovesPS_v6.txt'
MT = 'editor_toolset.toolsets.material.MaterialTools.'
OT = 'editor_toolset.toolsets.object.ObjectTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
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
def rp(x):
    return x['refPath'] if isinstance(x, dict) and 'refPath' in x else str(x)
def run():
  try:
    ok, code = T(AS + 'read_file', {'file_path': SRC})
    if not ok or not code or 'HallGroovesPS v6' not in str(code):
        return {'err': 'no pude leer el v6: NO escribo nada', 'log': LOG}
    ok, ex = T(MT + 'get_expressions', {'material_or_function': {'refPath': M}})
    target = None
    for e in (ex or []):
        r = rp(e)
        if r.split(':')[-1].startswith('MaterialExpressionCustom'):
            ok, g = T(OT + 'get_properties', {'instance': {'refPath': r}, 'properties': ['code']})
            try:
                g = json.loads(g) if isinstance(g, str) else g
            except BaseException:
                g = None
            if g and 'code' in g and str(g['code']).startswith('// HallGroovesPS'):
                target = r
                antes = str(g['code'])[:40]
                break
    if not target:
        return {'err': 'no encontre el Custom de HallGroovesPS', 'log': LOG}
    ok = T(OT + 'set_properties', {'instance': {'refPath': target}, 'values': json.dumps({'code': str(code)})})[0]
    ok2, g2 = T(OT + 'get_properties', {'instance': {'refPath': target}, 'properties': ['code']})
    txt = str(g2)
    return {'custom': target.split(':')[-1], 'antes': antes, 'escrito': ok, 'v6_leido': 'HallGroovesPS v6' in txt and '-1.7' in txt, 'log': LOG}
  except BaseException as e:
    return {'err': 'run :: ' + str(e)[:300], 'log': LOG}
