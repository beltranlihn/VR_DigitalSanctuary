import json
# inicio_a1.py - Test_Hall (turno INICIO): AutoOnDelay -1 · FadeOut 12 (CDO + instancia) · tag hall_arch en la arquitectura ·
# MPC_Hall_SC gana GrooveFront (2000) y DustLight (0) · lee la opacidad de M_HallFog_SC. Canario. Sin `result = run()`.
SC = 'editor_toolset.toolsets.scene.SceneTools.'
AT = 'editor_toolset.toolsets.actor.ActorTools.'
OT = 'editor_toolset.toolsets.object.ObjectTools.'
MT = 'editor_toolset.toolsets.material.MaterialTools.'
L = '/Game/SoulCharger/Mechanics/Hall/Test_Hall.Test_Hall:PersistentLevel.'
MPC = '/Game/SoulCharger/Mechanics/Hall/MPC_Hall_SC.MPC_Hall_SC'
FOG_CDO = '/Game/SoulCharger/Mechanics/Hall/BP_HallFog_SC.Default__BP_HallFog_SC_C'
FOG_M = '/Game/SoulCharger/Mechanics/Hall/M_HallFog_SC.M_HallFog_SC'
ARCH = ['StaticMeshActor_1', 'StaticMeshActor_2', 'StaticMeshActor_3', 'StaticMeshActor_4', 'StaticMeshActor_5',
        'StaticMeshActor_6', 'StaticMeshActor_7', 'BP_LightShaft_SC_C_0', 'NiagaraActor_0', 'NiagaraActor_1',
        'BP_HallTitle_SC_C_0', 'BP_HallTitle_SC_C_1', 'BP_HallGlow_SC_C_0']
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
    li = L + 'BP_HallLights_SC_C_0'
    out['auto_antes'] = G(li, ['AutoOnDelay'])
    S(li, {'AutoOnDelay': -1.0})
    out['auto_despues'] = G(li, ['AutoOnDelay'])
    fi = L + 'BP_HallFog_SC_C_0'
    out['fade_antes'] = [G(FOG_CDO, ['FadeOut']), G(fi, ['FadeOut'])]
    S(FOG_CDO, {'FadeOut': 12.0})
    S(fi, {'FadeOut': 12.0})
    out['fade_despues'] = [G(FOG_CDO, ['FadeOut']), G(fi, ['FadeOut'])]
    tags = []
    for n in ARCH:
        a = L + n
        g = G(a, ['Tags'])
        tg = g.get('Tags') if g else None
        if not tg or 'hall_arch' not in tg:
            T(AT + 'add_tag', {'actor': {'refPath': a}, 'tag': 'hall_arch'})
        g = G(a, ['Tags'])
        tags.append([n, g.get('Tags') if g else None])
    out['tags'] = tags
    mp = G(MPC, ['ScalarParameters'])
    sc = mp['ScalarParameters'] if mp and 'ScalarParameters' in mp else None
    if sc is not None:
        sc2 = [dict(p) for p in sc]
        if not any(p['parameterName'] == 'GrooveFront' for p in sc):
            sc2.append({'parameterName': 'GrooveFront', 'defaultValue': 2000.0, 'id': '9E4ABC17-2C7A-4156-9382-20B4D1751F6A'})
        if not any(p['parameterName'] == 'DustLight' for p in sc):
            sc2.append({'parameterName': 'DustLight', 'defaultValue': 0.0, 'id': 'F65416BF-23E0-4117-BC92-F37D8FB701B0'})
        out['mpc_antes'] = [(p['parameterName'], p['id'], p['defaultValue']) for p in sc]
        if len(sc2) != len(sc):
            S(MPC, {'ScalarParameters': sc2})
        mp2 = G(MPC, ['ScalarParameters'])
        out['mpc_despues'] = [(p['parameterName'], p['id'], p['defaultValue']) for p in mp2['ScalarParameters']] if mp2 else None
    out['fog_mat'] = G(FOG_M, ['BlendMode', 'bDisableDepthTest', 'TwoSided'])
    ok, op = T(MT + 'get_property_input', {'material': {'refPath': FOG_M}, 'material_property': 'MP_Opacity'})
    out['fog_opacity_in'] = str(op)[:300]
    out['canario_despues'] = n_act()
    out['log'] = LOG[:20]
    return out
  except BaseException as e:
    return {'err': 'run :: ' + str(e)[:300], 'log': LOG}
