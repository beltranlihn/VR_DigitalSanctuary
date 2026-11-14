import json
# turno4_values.py - Test_Hall, pedido de Beltrán tras probar la Obra ("faltaba agilidad"; "la ameba apareció muy grande y
# cerca: debe quedar al centro del Hall"). Director: VOAir 0,8→0,5 · OutTime 13→11 · ReturnTime 9→8 · ExitTime 14→12
# (CDO + instancia, antes→después). TP_hall_soul_present (TargetPoint_4): (−230,0,167) → (0,0,160) bajo el óculo, escala
# → 0,3 (la ameba copia la escala X de su TargetPoint como Size). Canario. MODO 'leer' / 'aplicar'. Sin `result = run()`.
MODO = 'leer'
SC = 'editor_toolset.toolsets.scene.SceneTools.'
AT = 'editor_toolset.toolsets.actor.ActorTools.'
OT = 'editor_toolset.toolsets.object.ObjectTools.'
L = '/Game/SoulCharger/Mechanics/Hall/Test_Hall.Test_Hall:PersistentLevel.'
CDO = '/Game/SoulCharger/Mechanics/Hall/BP_HallDirector_SC.Default__BP_HallDirector_SC_C'
INST = L + 'BP_HallDirector_SC_C_0'
TP = L + 'TargetPoint_4'
NEW = {'VOAir': 0.5, 'OutTime': 11.0, 'ReturnTime': 8.0, 'ExitTime': 12.0}
TP_LOC = (0.0, 0.0, 160.0)
TP_SCALE = 0.3
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
def n_act():
    ok, a = T(SC + 'find_actors', {'name': '', 'tag': '', 'collision_channels': []})
    return len(a or [])
def run():
  try:
    out = {'canario_antes': n_act()}
    ks = list(NEW.keys())
    out['antes'] = {'cdo': G(CDO, ks), 'inst': G(INST, ks)}
    ok, lab = T(AT + 'get_label', {'actor': {'refPath': TP}})
    ok, r = T(AT + 'get_root_component', {'actor': {'refPath': TP}})
    root = rp(r) if ok else None
    out['tp'] = [str(lab), G(root, ['RelativeLocation', 'RelativeScale3D']) if root else None]
    if MODO == 'aplicar' and str(lab) == 'TP_hall_soul_present' and root:
        for k, v in NEW.items():
            S(CDO, {k: v})
            S(INST, {k: v})
        S(root, {'relativeLocation': '(X=%.1f,Y=%.1f,Z=%.1f)' % TP_LOC})
        S(root, {'relativeScale3D': '(X=%.3f,Y=%.3f,Z=%.3f)' % (TP_SCALE, TP_SCALE, TP_SCALE)})
        out['despues'] = {'cdo': G(CDO, ks), 'inst': G(INST, ks), 'tp': G(root, ['RelativeLocation', 'RelativeScale3D'])}
    out['canario_despues'] = n_act()
    out['log'] = LOG[:10]
    return out
  except BaseException as e:
    return {'err': 'run :: ' + str(e)[:300], 'log': LOG}
