import json
# obra_inventory.py - SOLO LEE: inventario compacto del nivel abierto (etiqueta, clase, posición, malla, tags). Sin `result = run()`.
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
        LOG.append(name.split('.')[-1] + ' :: ' + str(e)[:200])
        return False, None
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
def run():
  try:
    ok, lv = T(SC + 'get_current_level', {})
    ok, acts = T(SC + 'find_actors', {'name': '', 'tag': '', 'collision_channels': []})
    refs = [rp(a) for a in (acts or [])]
    out = {'level': str(lv)[:160], 'n': len(refs), 'a': []}
    for a in refs:
        n = a.split('PersistentLevel.')[-1]
        ok, l = T(AT + 'get_label', {'actor': {'refPath': a}})
        ok, t = T(AT + 'get_actor_transform', {'actor': {'refPath': a}})
        p = ''
        try:
            q = t['location'] if 'location' in t else t['translation']
            p = '%d,%d,%d' % (float(q['x']), float(q['y']), float(q['z']))
        except BaseException:
            pass
        g = G(a, ['Tags'])
        tg = g.get('Tags') if g else None
        row = [n[:40], str(l)[:32], p, tg if tg else '']
        if n.startswith('StaticMeshActor'):
            ok, r = T(AT + 'get_root_component', {'actor': {'refPath': a}})
            m = G(rp(r), ['StaticMesh']) if ok else None
            row.append(str(m.get('StaticMesh', '?')).split('.')[-1][:36] if m else '?')
        out['a'].append(row)
    out['log'] = LOG[:10]
    return out
  except BaseException as e:
    return {'err': 'run :: ' + str(e)[:300], 'log': LOG}
