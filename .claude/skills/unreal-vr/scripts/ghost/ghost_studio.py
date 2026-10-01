import json
import math
# ghost_studio.py (2026-10-01) - arma el ESTUDIO de grabacion en el nivel ABIERTO (tiene que ser L_GhostRec_SC):
#   - 7 fantasmas Ghost_<ID> (BP_GhostPlayer_SC) con su Take; el GhostPreview de v1 pasa a ser Ghost_BELL;
#   - las piezas de referencia de cada estacion (StaticMeshActors con las mallas del arte real), tag = Id de la toma,
#     carpeta Estaciones/<ID>, sin colision;
#   - el grabador (GhostRecorder) con Ghosts = los 7 en orden.
# Posiciones = las de la obra respecto de los OJOS de un usuario sentado (ojos = PlayerStart + 120 en z, convencion del
# Hall): timbre y sensor 48 cm al frente y 28 bajo los ojos, mirando a los ojos (pitch +-59,7); almas en arco
# (Fwd 54-3|k|, Side 19k); slots del gusano en arco de radio 70 a 30 cm al frente, z 80 del piso; esfera de referencia en
# OrbRest. Fuente: scripts/ghost/v2_datos.md.
# Idempotente (busca por etiqueta). No saca actores ajenos. Canario de actores antes/despues; guarda con ruta explicita
# solo si el canario no bajo. Transforms en formato de TEXTO y releidos (gotcha 519). Se pega ENTERO. Nunca levanta.
GUARDAR = True
LEVEL = '/Game/SoulCharger/Mechanics/Ghost/L_GhostRec_SC'
PLAYER_BP = '/Game/SoulCharger/Mechanics/Ghost/BP_GhostPlayer_SC'
TAKES = '/Game/SoulCharger/Mechanics/Ghost/Takes/'
SC = 'editor_toolset.toolsets.scene.SceneTools.'
AT = 'editor_toolset.toolsets.actor.ActorTools.'
OT = 'editor_toolset.toolsets.object.ObjectTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
BELL = '/Game/SoulCharger/Mechanics/Bell/'
BS = '/Game/SoulCharger/Mechanics/BioSensor/'
SOUL = '/Game/SoulCharger/Core/Alma/SM_AlmaSphere'
SPH = '/Engine/BasicShapes/Sphere'
ORB_REST = (350.0, 120.0, 80.0)
ID_XF = {'location': {'x': 0, 'y': 0, 'z': 0}, 'rotation': {'pitch': 0, 'yaw': 0, 'roll': 0}, 'scale': {'x': 1, 'y': 1, 'z': 1}}


def slots():
    out = []
    for a in (-63.0, -45.0, -27.0, -9.0, 9.0, 27.0, 45.0, 63.0):
        r = math.radians(a)
        out.append((SPH, (30.0 + 70.0 * math.cos(r), 70.0 * math.sin(r), -40.0), (0.0, 0.0, 0.0), 0.07))
    return out


# (id corto, DA, origen del fantasma en espacio de los ojos, TextOffset, [ (malla, local, (pitch,yaw,roll), escala) ])
STATIONS = [
    ('BELL', 'DA_Ghost_Bell', (48.0, 0.0, -28.0), (0.0, 0.0, -16.0),
     [(BELL + m, (48.0, 0.0, -28.0), (59.7, 0.0, 0.0), 1.0) for m in ('SM_Bell_Base_SC', 'SM_Bell_Button_SC', 'SM_Bell_Slider_SC')]),
    ('TAKE', 'DA_Ghost_Take', (48.0, 0.0, -28.0), (0.0, 0.0, -16.0),
     [(BS + m, (48.0, 0.0, -28.0), (-59.7, 0.0, 0.0), 1.0) for m in ('SM_BioSensor_SC', 'SM_BioSensor_Button_SC')]),
    ('PICK', 'DA_Ghost_Pick', (54.0, 0.0, -28.0), (0.0, 0.0, -16.0),
     [(SOUL, (54.0 - 3.0 * abs(k), 19.0 * k, -28.0), (0.0, 0.0, 0.0), 0.15) for k in (0, -1, 1, -2, 2)]),
    ('BREATH', 'DA_Ghost_Breath', (0.0, 0.0, 0.0), (60.0, 0.0, -40.0), []),
    ('HEART', 'DA_Ghost_Heart', (0.0, 0.0, 0.0), (60.0, 0.0, -40.0), []),
    ('ATTRACT', 'DA_Ghost_Attract', (0.0, 0.0, 0.0), (60.0, 0.0, -45.0),
     [(SPH, ORB_REST, (0.0, 0.0, 0.0), 0.18)] + slots()),
    ('DRAW', 'DA_Ghost_Draw', (0.0, 0.0, 0.0), (60.0, 0.0, -40.0), []),
]
LOG = []


def T(name, payload):
    try:
        r = execute_tool(name, json.dumps(payload))
        v = r['returnValue'] if isinstance(r, dict) and ('returnValue' in r) else r
        return True, v
    except BaseException as e:
        LOG.append(name.split('.')[-1] + ' :: ' + str(e)[:180])
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


def refp(x):
    return str(x['refPath'] if isinstance(x, dict) and ('refPath' in x) else x)


def all_actors():
    ok, v = T(SC + 'find_actors', {'name': '', 'tag': '', 'collision_channels': []})
    return [refp(a) for a in (v or [])]


def labels(actors):
    m = {}
    for a in actors:
        ok, l = T(AT + 'get_label', {'actor': {'refPath': a}})
        if ok and l:
            m[str(l)] = a
    return m


class Frame(object):
    def __init__(self, loc, yaw):
        self.loc, self.yaw = loc, yaw
        self.c, self.s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))

    def w(self, p):
        x, y, z = p
        return (self.loc[0] + x * self.c - y * self.s, self.loc[1] + x * self.s + y * self.c, self.loc[2] + z)


def put(actor, loc, rot, sc):
    ok, root = T(AT + 'get_root_component', {'actor': {'refPath': actor}})
    rr = refp(root)
    S(rr, {'relativeLocation': '(X=%f,Y=%f,Z=%f)' % loc})
    S(rr, {'relativeRotation': '(Pitch=%f,Yaw=%f,Roll=%f)' % rot})
    S(rr, {'relativeScale3D': '(X=%f,Y=%f,Z=%f)' % (sc, sc, sc)})
    g = G(rr, ['relativeLocation'])
    try:
        got = g['relativeLocation']
        return abs(got['x'] - loc[0]) + abs(got['y'] - loc[1]) + abs(got['z'] - loc[2]) < 0.05
    except BaseException:
        return False


def setvec(actor, name, v):
    S(actor, {name: {'x': v[0], 'y': v[1], 'z': v[2]}})
    g = G(actor, [name])
    try:
        got = g[name]
        if abs(got['x'] - v[0]) + abs(got['y'] - v[1]) + abs(got['z'] - v[2]) < 0.01:
            return 'json'
    except BaseException:
        pass
    S(actor, {name: '(X=%f,Y=%f,Z=%f)' % v})
    return 'texto'


def run():
    try:
        return run2()
    except BaseException as e:
        return {'err': 'run :: ' + str(e)[:300], 'log': LOG}


def run2():
    ok, lvl = T(SC + 'get_current_level', {})
    if 'L_GhostRec_SC' not in str(lvl):
        return {'err': 'el nivel abierto no es L_GhostRec_SC: ' + str(lvl)[:120]}
    acts = all_actors()
    out = {'actores_antes': len(acts)}
    lab = labels(acts)
    ps = None
    for l, a in lab.items():
        if 'PlayerStart' in l:
            ps = a
            break
    if not ps:
        return {'err': 'no encontre el PlayerStart', 'labels': sorted(lab.keys())[:40]}
    ok, xf = T(AT + 'get_actor_transform', {'actor': {'refPath': ps}})
    try:
        loc = (xf['location']['x'], xf['location']['y'], xf['location']['z'])
        yaw = xf['rotation']['yaw']
    except BaseException:
        return {'err': 'transform del PlayerStart ilegible: ' + str(xf)[:200]}
    eyes = Frame((loc[0], loc[1], loc[2] + 120.0), yaw)
    out['ojos'] = [round(c, 1) for c in eyes.loc] + [round(yaw, 1)]
    ghosts, res = [], {}
    for short, da, gl, toff, props in STATIONS:
        label = 'Ghost_' + short
        rec = {}
        a = lab[label] if label in lab else None
        if not a and short == 'BELL' and 'GhostPreview' in lab:
            a = lab['GhostPreview']
            T(AT + 'set_label', {'actor': {'refPath': a}, 'label': label})
            rec['de_v1'] = 'GhostPreview'
        if not a:
            ok, r = T(SC + 'add_to_scene_from_asset', {'asset_path': PLAYER_BP, 'name': label, 'xform': ID_XF})
            a = refp(r) if ok and r else None
            if a:
                T(AT + 'set_label', {'actor': {'refPath': a}, 'label': label})
                rec['creado'] = True
        if not a:
            res[short] = 'NO se pudo colocar'
            continue
        rec['pos'] = put(a, eyes.w(gl), (0.0, yaw, 0.0), 1.0)
        rec['take'] = S(a, {'Take': {'refPath': TAKES + da + '.' + da}, 'bPreview': True, 'bAutoPlay': False})
        rec['text'] = setvec(a, 'TextOffset', toff)
        if short == 'ATTRACT':
            rec['orb'] = setvec(a, 'OrbRest', ORB_REST)
        T(SC + 'set_actor_folder', {'actor': {'refPath': a}, 'folder_path': 'Fantasmas'})
        ghosts.append(a)
        hechos = 0
        for i, (mesh, pl, rot, sc) in enumerate(props):
            pl_label = 'Est_%s_%d' % (short, i)
            if pl_label in lab:
                continue
            ok, r = T(SC + 'add_to_scene_from_asset', {'asset_path': mesh, 'name': pl_label, 'xform': ID_XF})
            if not ok or not r:
                continue
            p = refp(r)
            T(AT + 'set_label', {'actor': {'refPath': p}, 'label': pl_label})
            put(p, eyes.w(pl), (rot[0], yaw + rot[1], rot[2]), sc)
            T(AT + 'add_tag', {'actor': {'refPath': p}, 'tag': 'GHOST_' + short})
            ok, root = T(AT + 'get_root_component', {'actor': {'refPath': p}})
            S(refp(root), {'BodyInstance': {'CollisionEnabled': 'NoCollision'}})
            T(SC + 'set_actor_folder', {'actor': {'refPath': p}, 'folder_path': 'Estaciones/' + short})
            hechos += 1
        rec['piezas_nuevas'] = '%d de %d' % (hechos, len(props))
        res[short] = rec
    out['estaciones'] = res
    if 'GhostRecorder' in lab:
        rr = lab['GhostRecorder']
        out['grabador'] = S(rr, {'Ghosts': [{'refPath': g} for g in ghosts]})
        g = G(rr, ['Ghosts'])
        out['grabador_ghosts'] = len(g['Ghosts']) if g and ('Ghosts' in g) and g['Ghosts'] else 0
    else:
        out['grabador'] = 'NO encontre GhostRecorder'
    out['actores_despues'] = len(all_actors())
    if GUARDAR and out['actores_despues'] >= out['actores_antes']:
        out['guardado'] = T(AS + 'save_assets', {'asset_paths': [LEVEL]})[0]
    out['log'] = LOG[:30]
    return out
