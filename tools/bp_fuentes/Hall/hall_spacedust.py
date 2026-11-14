import json
# hall_spacedust.py - las MOTAS DEL ESPACIO del viaje (pedido de Beltrán 2026-09-30: "son distintas a las del interior, son del
# exterior, en el espacio"). NO se toca el polvo del Hall. Se duplican:
#   M_HallDust_SC -> M_SpaceDust_SC  (su CollectionParameter HallLight pasa a DustLight: se ven solo en el viaje/la salida)
#   NS_HallDust_SC -> NS_SpaceDust_SC (su sprite renderer apunta a M_SpaceDust_SC)
# MODO 'leer': duplica (idempotente), inspecciona el material (params, colección) y el renderer del Niagara.
# MODO 'aplicar': retarget de la colección + color frío + material del renderer. Requiere DustLight YA en MPC_Hall_SC.
# Sin `result = run()`. Nunca levanta.
MODO = 'leer'
RENDERER_PATCH = None   # dict con el campo de material del renderer, armado a partir de lo que devuelve el modo leer
MPC = '/Game/SoulCharger/Mechanics/Hall/MPC_Hall_SC.MPC_Hall_SC'
H = '/Game/SoulCharger/Mechanics/Hall/'
M_SRC, M_DST = H + 'M_HallDust_SC', H + 'M_SpaceDust_SC'
N_SRC, N_DST = H + 'NS_HallDust_SC', H + 'NS_SpaceDust_SC'
DID = 'F65416BF-23E0-4117-BC92-F37D8FB701B0'
MT = 'editor_toolset.toolsets.material.MaterialTools.'
MIT = 'editor_toolset.toolsets.material_instance.MaterialInstanceTools.'
OT = 'editor_toolset.toolsets.object.ObjectTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
NS = 'NiagaraToolsets.NiagaraToolset_System.'
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
def rp(x):
    return x['refPath'] if isinstance(x, dict) and 'refPath' in x else str(x)
def full(p):
    return p + '.' + p.split('/')[-1]
def run():
  try:
    out = {}
    for src, dst in [(M_SRC, M_DST), (N_SRC, N_DST)]:
        ok, ex = T(AS + 'exists', {'path': dst})
        if not ex:
            out['dup_' + dst.split('/')[-1]] = T(AS + 'duplicate', {'path': src, 'new_path': dst})[0]
    ok, ex = T(MT + 'get_expressions', {'material_or_function': {'refPath': full(M_DST)}})
    refs = [rp(e) for e in (ex or [])]
    col, params = [], {}
    for r in refs:
        n = r.split(':')[-1]
        if n.startswith('MaterialExpressionCollectionParameter'):
            col.append([r, G(r, ['ParameterName', 'ParameterId'])])
        elif 'Parameter' in n:
            g = G(r, ['ParameterName'])
            if g and 'ParameterName' in g:
                params[str(g['ParameterName'])] = r
    out['coleccion'] = [[c[0].split(':')[-1], c[1]] for c in col]
    out['params'] = sorted(params.keys())
    ok, summ = T(NS + 'GetSystemSummary', {'system': {'refPath': full(N_DST)}})
    out['ns_summary'] = str(summ)[:1500]
    if MODO != 'aplicar':
        out['log'] = LOG[:20]
        return out
    for r, g in col:
        if g and str(g.get('ParameterName', '')) == 'HallLight':
            S(r, {'ParameterName': 'DustLight'})
            S(r, {'ParameterId': DID})
            out['retarget'] = G(r, ['ParameterName', 'ParameterId'])
    T(MT + 'recompile', {'material_or_function': {'refPath': full(M_DST)}})
    if RENDERER_PATCH:
        out['renderer'] = T(NS + 'SetRendererData', RENDERER_PATCH)
    out['log'] = LOG[:20]
    return out
  except BaseException as e:
    return {'err': 'run :: ' + str(e)[:300], 'log': LOG}
