import json
# apply_draw_sea_bp_B.py - defaults del CDO de BP_DrawSea_SC, CON RELECTURA variable por variable.
# Las plantillas de los componentes (malla, MI, sombras, bounds, escala del cielo) NO van aca: por llamada directa,
# porque un get_properties con un nombre de propiedad que no existe atraviesa el try/except (gotcha 482).
# Correr DESPUES de apply_draw_sea_bp_A.py + compile_blueprint (gotcha: el CDO no tiene el campo hasta compilar) y
# ANTES de colocar el actor (las instancias nacen con lo del CDO; lo agregado despues nace en 0: gotchas 146/164/478).
# Se pega ENTERO en execute_tool_script. Idempotente (solo escribe valores). Nunca levanta excepcion.
# set_properties exige `values` como TEXTO JSON (gotcha 483).
OT = 'editor_toolset.toolsets.object.ObjectTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
PLAN = 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/oceano/draw_sea_bp.json'
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
def S(ref, vals):
    return T(OT + 'set_properties', {'instance': {'refPath': ref}, 'values': json.dumps(vals)})[0]
def G(ref, props):
    ok, v = T(OT + 'get_properties', {'instance': {'refPath': ref}, 'properties': props})
    if not ok or v is None:
        return None
    try:
        return json.loads(v) if isinstance(v, str) else v
    except BaseException:
        return None
def cerca(a, b):
    try:
        if isinstance(b, bool) or isinstance(a, bool):
            return bool(a) == bool(b)
        if isinstance(b, (int, float)):
            return abs(float(a) - float(b)) <= 1e-6 * max(1.0, abs(float(b)))
        if isinstance(b, dict):
            return all(cerca(a[k], b[k]) for k in b)
        return str(b).split('.')[-1] in str(a)
    except BaseException:
        return False
def run():
  try:
    ok, txt = T(AS + 'read_file', {'file_path': PLAN})
    if not ok:
        return {'err': 'no pude leer el plan', 'log': LOG}
    plan = json.loads(txt)
    BPP = plan['blueprint']
    NAME = BPP.rsplit('/', 1)[1]
    CDO = BPP + '.Default__' + NAME + '_C'
    out = {}
    escritas, malas = 0, []
    for v in plan['vars']:
        d = v['default']
        if v['type'] == 'LinearColor':
            val = {'r': d[0], 'g': d[1], 'b': d[2], 'a': (d[3] if len(d) > 3 else 1.0)}
        else:
            val = d
        if S(CDO, {v['name']: val}):
            escritas += 1
        leido = G(CDO, [v['name']])
        if leido is None or v['name'] not in leido or not cerca(leido[v['name']], val):
            malas.append(v['name'] + '=' + str(leido)[:80])
    out['cdo'] = {'escritas': escritas, 'total': len(plan['vars']), 'no_coinciden': malas}
    out['log'] = LOG[:30]
    return out
  except BaseException as e:
    return {'err': 'run :: ' + str(e)[:300], 'log': LOG}
# Solo para el ensayo offline (dryrun lee `result`). AL PEGAR en execute_tool_script, QUITAR esta linea (gotcha 493).
result = run()
