import json
# hall_level.py - Test_Hall: coloca el director + 3 TargetPoints de Alma + una Alma TestOnly, y marca las hojas (hall_leaf,
# Movable) y las baldosas (hall_tiles). NO saca ni repone nada. Canario antes/despues. Sin `result = run()`. Idempotente
# (busca por etiqueta antes de colocar). MODO = 'leer' solo inventaria; 'aplicar' hace los cambios.
MODO = 'aplicar'
SC = 'editor_toolset.toolsets.scene.SceneTools.'
AT = 'editor_toolset.toolsets.actor.ActorTools.'
OT = 'editor_toolset.toolsets.object.ObjectTools.'
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
def actores():
    ok, acts = T(SC + 'find_actors', {'name': '', 'tag': '', 'collision_channels': []})
    return [rp(a) for a in (acts or []) if 'Test_Hall' in rp(a)]
def loc_of(ref):
    ok, t = T(AT + 'get_actor_transform', {'actor': {'refPath': ref}})
    try:
        l = t['location'] if 'location' in t else t['translation']
        return [float(l['x']), float(l['y']), float(l['z'])]
    except BaseException:
        LOG.append('transform raro ' + str(t)[:160])
        return None
def root(ref):
    ok, r = T(AT + 'get_root_component', {'actor': {'refPath': ref}})
    return rp(r) if ok else None
def label(ref):
    ok, l = T(AT + 'get_label', {'actor': {'refPath': ref}})
    return str(l)
def place_loc(ref, p):
    r = root(ref)
    if r:
        S(r, {'relativeLocation': '(X=%.3f,Y=%.3f,Z=%.3f)' % (p[0], p[1], p[2])})
    return loc_of(ref)
def run():
  try:
    out = {}
    antes = actores()
    out['canario_antes'] = len(antes)
    inv = {}
    for a in antes:
        n = a.split('PersistentLevel.')[-1]
        if n.startswith('StaticMeshActor'):
            r = root(a)
            g = G(r, ['StaticMesh']) if r else None
            m = str(g['StaticMesh']) if g and 'StaticMesh' in g else '?'
            inv[n] = m.split('.')[-1][:40]
        elif n.startswith('PlayerStart') or n.startswith('BP_') or n.startswith('TargetPoint'):
            inv[n] = label(a)
    out['inventario'] = inv
    shell = [a for a in antes if a.split('PersistentLevel.')[-1] in inv and 'HallShell' in inv[a.split('PersistentLevel.')[-1]]]
    ps = [a for a in antes if 'PlayerStart' in a]
    C = loc_of(shell[0]) if shell else None
    out['hall_centro'] = C
    out['playerstart'] = loc_of(ps[0]) if ps else None
    if MODO != 'aplicar' or not C:
        out['log'] = LOG[:30]
        return out
    hechos = []
    for a in antes:
        n = a.split('PersistentLevel.')[-1]
        if n not in inv:
            continue
        if 'HallDoorLeaf' in inv[n]:
            T(AT + 'add_tag', {'actor': {'refPath': a}, 'tag': 'hall_leaf'})
            r = root(a)
            S(r, {'Mobility': 'Movable'})
            g = G(r, ['Mobility'])
            hechos.append(n + ' hall_leaf ' + str(g))
        if 'HallTiles' in inv[n]:
            T(AT + 'add_tag', {'actor': {'refPath': a}, 'tag': 'hall_tiles'})
            hechos.append(n + ' hall_tiles')
    labels = dict((label(a), a) for a in antes)
    F = C[2] + 30.0
    if 'HallDirector' not in labels:
        ok, d = T(SC + 'add_to_scene_from_asset', {'asset_path': '/Game/SoulCharger/Mechanics/Hall/BP_HallDirector_SC', 'name': 'HallDirector', 'xform': {'location': {'x': C[0], 'y': C[1], 'z': C[2]}, 'rotation': {'x': 0, 'y': 0, 'z': 0, 'w': 1}, 'scale': {'x': 1, 'y': 1, 'z': 1}}})
        if ok:
            hechos.append('director en ' + str(place_loc(rp(d), C)))
    tps = [('TP_hall_alma_center', 'hall_alma_center', [C[0], C[1], F + 150.0]),
           ('TP_hall_alma_side', 'hall_alma_side', [C[0] - 180.0, C[1] - 120.0, F + 140.0]),
           ('TP_hall_alma_exit', 'hall_alma_exit', [C[0] + 560.0, C[1], F + 170.0])]
    for lab, tag, p in tps:
        if lab in labels:
            continue
        ok, t = T(SC + 'add_to_scene_from_class', {'actor_type': {'refPath': '/Script/Engine.TargetPoint'}, 'name': lab, 'xform': {'location': {'x': p[0], 'y': p[1], 'z': p[2]}, 'rotation': {'x': 0, 'y': 0, 'z': 0, 'w': 1}, 'scale': {'x': 1, 'y': 1, 'z': 1}}})
        if ok:
            T(AT + 'add_tag', {'actor': {'refPath': rp(t)}, 'tag': tag})
            hechos.append(lab + ' en ' + str(place_loc(rp(t), p)))
    if 'Alma_HallTest' not in labels:
        ok, al = T(SC + 'add_to_scene_from_asset', {'asset_path': '/Game/SoulCharger/Core/Alma/BP_Alma_SC', 'name': 'Alma_HallTest', 'xform': {'location': {'x': C[0], 'y': C[1], 'z': F + 150.0}, 'rotation': {'x': 0, 'y': 0, 'z': 0, 'w': 1}, 'scale': {'x': 1, 'y': 1, 'z': 1}}})
        if ok:
            T(AT + 'add_tag', {'actor': {'refPath': rp(al)}, 'tag': 'TestOnly'})
            hechos.append('Alma_HallTest (TestOnly) en ' + str(place_loc(rp(al), [C[0], C[1], F + 150.0])))
    out['hechos'] = hechos
    despues = actores()
    out['canario_despues'] = len(despues)
    out['perdidos'] = [a.split('PersistentLevel.')[-1] for a in antes if a not in despues]
    out['log'] = LOG[:30]
    return out
  except BaseException as e:
    return {'err': 'run :: ' + str(e)[:300], 'log': LOG}
