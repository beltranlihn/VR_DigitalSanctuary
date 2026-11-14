import json
CFGS = [{"lv": "/Game/Test_Heart", "short": "Test_Heart", "K": 1, "P": [0, 0, 0], "yaw": 0.0, "cy": 1.0, "sy": 0.0, "alma_t": 11.3, "timeout": 150.0, "charge_t": 4.0, "mi": "RECOGNIZING", "ctop": [0.4, 0.3, 0.31], "chor": [0.95, 0.85, 0.83]}, {"lv": "/Game/Test_Fluid", "short": "Test_Fluid", "K": 2, "P": [0, 0, 0], "yaw": 0.0, "cy": 1.0, "sy": 0.0, "alma_t": 7.2, "timeout": 120.0, "charge_t": 4.0, "mi": "LOVING", "ctop": [0.0369, 0.0273, 0.0482], "chor": [0.0176, 0.013, 0.0232]}, {"lv": "/Game/Test_Sequencer", "short": "Test_Sequencer", "K": 3, "P": [362700, 100000, 0], "yaw": 0.0, "cy": 1.0, "sy": 0.0, "alma_t": 9.4, "timeout": 240.0, "charge_t": 4.0, "mi": "ATTRACTING", "ctop": [0.863, 0.745, 0.631], "chor": [0.973, 0.815, 0.565]}, {"lv": "/Game/NeuralCanvas/Maps/L_TBTest_SC", "short": "L_TBTest_SC", "K": 4, "P": [-315, 0, 106], "yaw": 0.0, "cy": 1.0, "sy": 0.0, "alma_t": 15.0, "timeout": 240.0, "charge_t": 6.0, "mi": "SURROUNDING", "ctop": [0.0027, 0.0033, 0.008], "chor": [0.0137, 0.0194, 0.0395]}]
SC = 'editor_toolset.toolsets.scene.SceneTools.'
AT = 'editor_toolset.toolsets.actor.ActorTools.'
OT = 'editor_toolset.toolsets.object.ObjectTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
LOG = []
def T(name, payload):
    try:
        return True, execute_tool(name, json.dumps(payload))['returnValue']
    except BaseException as e:
        LOG.append(name.split('.')[-1] + ' :: ' + str(e)[:220])
        return False, None
def S(ref, vals):
    return T(OT + 'set_properties', {'instance': {'refPath': ref}, 'values': json.dumps(vals)})[0]
def rp(x):
    return x['refPath'] if isinstance(x, dict) and 'refPath' in x else str(x)
def actores():
    ok, acts = T(SC + 'find_actors', {'name': '', 'tag': '', 'collision_channels': []})
    return [rp(a) for a in (acts or [])]
def root(ref):
    ok, r = T(AT + 'get_root_component', {'actor': {'refPath': ref}})
    return rp(r) if ok else None
def xf(ref, p, yaw, sc):
    r = root(ref)
    if not r:
        return 'sin root'
    S(r, {'relativeLocation': '(X=%.3f,Y=%.3f,Z=%.3f)' % (p[0], p[1], p[2])})
    S(r, {'relativeRotation': '(Pitch=0.000000,Yaw=%.3f,Roll=0.000000)' % yaw})
    S(r, {'relativeScale3D': '(X=%.3f,Y=%.3f,Z=%.3f)' % (sc, sc, sc)})
    ok, t = T(AT + 'get_actor_transform', {'actor': {'refPath': ref}})
    try:
        l = t['location'] if 'location' in t else t['translation']
        return [round(float(l['x']), 1), round(float(l['y']), 1), round(float(l['z']), 1)]
    except BaseException:
        return str(t)[:80]
XF0 = {'location': {'x': 0, 'y': 0, 'z': 0}, 'rotation': {'x': 0, 'y': 0, 'z': 0, 'w': 1}, 'scale': {'x': 1, 'y': 1, 'z': 1}}
def place(CFG):
  try:
    out = {}
    ok, cur = T(SC + 'get_current_level', {})
    if str(cur) != CFG['lv']:
        T(SC + 'load_level', {'level_path': CFG['lv']})
    ok, cur = T(SC + 'get_current_level', {})
    out['nivel'] = cur
    if str(cur) != CFG['lv']:
        return {'err': 'no pude abrir ' + CFG['lv']}
    antes = actores()
    out['antes'] = len(antes)
    labels = {}
    for a in antes:
        ok, l = T(AT + 'get_label', {'actor': {'refPath': a}})
        labels[str(l)] = a
    K = CFG['K']
    P = CFG['P']
    yaw = CFG['yaw']
    cy = CFG['cy']
    sy = CFG['sy']
    def W(o):
        return [P[0] + o[0] * cy - o[1] * sy, P[1] + o[0] * sy + o[1] * cy, P[2] + o[2]]
    hechos = []
    lab = 'StageRunner'
    if lab not in labels:
        ok, r = T(SC + 'add_to_scene_from_asset', {'asset_path': '/Game/SoulCharger/Obra/BP_StageRunner_SC', 'name': lab, 'xform': XF0})
        if ok:
            ref = rp(r)
            T(AT + 'set_label', {'actor': {'refPath': ref}, 'label': lab})
            T(AT + 'add_tag', {'actor': {'refPath': ref}, 'tag': 'TestOnly'})
            T(AT + 'add_tag', {'actor': {'refPath': ref}, 'tag': 'TOUR'})
            hechos.append(lab + ' en ' + str(xf(ref, W([0, 0, 0]), yaw, 1.0)))
            labels[lab] = ref
    if lab in labels:
        ref = labels[lab]
        vals = {'StageK': K, 'LevelName': CFG['short'], 'TagIn': 'sc%d_alma_in' % K, 'TagSide': 'sc%d_alma_side' % K,
                'TagCharge': 'sc%d_charge' % K, 'TagTitle': 'sc%d_title' % K, 'AlmaTime': CFG['alma_t'], 'TimeoutS': CFG['timeout'],
                'ChargeTime': CFG['charge_t'], 'TitleMI': '/Game/SoulCharger/Tour/MI_TourTitle_%s.MI_TourTitle_%s' % (CFG['mi'], CFG['mi']),
                'CTop': {'r': CFG['ctop'][0], 'g': CFG['ctop'][1], 'b': CFG['ctop'][2], 'a': 1.0},
                'CHor': {'r': CFG['chor'][0], 'g': CFG['chor'][1], 'b': CFG['chor'][2], 'a': 1.0}}
        bad = [k for k, v in vals.items() if not S(ref, {k: v})]
        ok, g = T(OT + 'get_properties', {'instance': {'refPath': ref}, 'properties': ['StageK', 'LevelName', 'TagIn', 'AlmaTime', 'TimeoutS', 'ChargeTime', 'TitleMI']})
        out['runner'] = str(g)[:400]
        out['runner_bad'] = bad
    lab = 'Alma_Ensayo'
    if lab not in labels:
        ok, r = T(SC + 'add_to_scene_from_asset', {'asset_path': '/Game/SoulCharger/Core/Alma/BP_Alma_SC', 'name': lab, 'xform': XF0})
        if ok:
            ref = rp(r)
            T(AT + 'set_label', {'actor': {'refPath': ref}, 'label': lab})
            T(AT + 'add_tag', {'actor': {'refPath': ref}, 'tag': 'TestOnly'})
            hechos.append(lab + ' en ' + str(xf(ref, W([220, 0, 125]), yaw, 1.0)))
    tps = [('alma_in', [220, 0, 125], 1.0), ('alma_side', [140, -300, 140], 1.0), ('charge', [253, 0, 157], 2.115), ('title', [300, 0, 120], 1.0)]
    for nm, off, sc in tps:
        tag = 'sc%d_%s' % (K, nm)
        lab = 'TP_' + tag
        if lab in labels:
            continue
        ok, r = T(SC + 'add_to_scene_from_class', {'actor_type': {'refPath': '/Script/Engine.TargetPoint'}, 'name': lab, 'xform': XF0})
        if ok:
            ref = rp(r)
            T(AT + 'set_label', {'actor': {'refPath': ref}, 'label': lab})
            T(AT + 'add_tag', {'actor': {'refPath': ref}, 'tag': tag})
            hechos.append(lab + ' en ' + str(xf(ref, W(off), yaw, sc)))
    out['hechos'] = hechos
    despues = actores()
    out['despues'] = len(despues)
    perd = [a.split('.')[-1] for a in antes if a not in despues]
    out['perdidos'] = perd
    if not perd:
        out['guardado'] = T(AS + 'save_assets', {'asset_paths': [CFG['lv']]})[0]
    return out
  except BaseException as e:
    return {'err': 'place :: ' + str(e)[:300]}
def run():
    res = {}
    for c in CFGS:
        res[c['short']] = place(c)
    res['log'] = LOG[:20]
    return res
