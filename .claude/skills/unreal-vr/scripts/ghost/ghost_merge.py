import json
import math
# ghost_merge.py (2026-10-01) - funde en UNA malla cada objeto que sostiene una mano fantasma: el sensor (cuerpo + boton),
# el SAVE (base + placa + deslizador) y la paleta (base, muestra, 8 teclas, deshacer/rehacer, deslizador y perilla en su
# reposo). Asi el fantasma los muestra completos con un solo componente (PropR/PropL, BodyR/BodyL).
# Arma StaticMeshActors temporales en un punto lejano del nivel ABIERTO (L_GhostRec_SC), los funde con
# SceneTools.merge_actors (destruye las fuentes) y apunta SensorMesh/SaveMesh/PaletteMesh del CDO del reproductor a las
# fundidas. Si un fundido falla, el reproductor sigue con la malla principal (la default de la spec).
# Pivote: se asume que la malla fundida toma el pivote del PRIMER actor (la base, en P con giro 0) -> el espacio de la
# malla fundida = el del arte. Se verifica con los bounds (centro esperado ~ (0,0,z)). Se pega ENTERO.
# Nunca levanta excepcion. Canario: cuenta de actores antes y despues (al final tiene que ser igual).
SC = 'editor_toolset.toolsets.scene.SceneTools.'
AT = 'editor_toolset.toolsets.actor.ActorTools.'
OT = 'editor_toolset.toolsets.object.ObjectTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
SMT = 'editor_toolset.toolsets.static_mesh.StaticMeshTools.'
BT = 'editor_toolset.toolsets.blueprint.BlueprintTools.'
OUT = '/Game/SoulCharger/Mechanics/Ghost'
PLAYER_CDO = '/Game/SoulCharger/Mechanics/Ghost/BP_GhostPlayer_SC.Default__BP_GhostPlayer_SC_C'
PLAYER = '/Game/SoulCharger/Mechanics/Ghost/BP_GhostPlayer_SC.BP_GhostPlayer_SC'
P = (0.0, 0.0, -20000.0)
BS = '/Game/SoulCharger/Mechanics/BioSensor/'
SV = '/Game/SoulCharger/Mechanics/SaveMelody/'
DP = '/Game/SoulCharger/Mechanics/DrawPalette/'
# (malla, (x y z), yaw, escala) en el espacio del arte. Paleta: reposo medido en BP_DrawPalette_SC.md (T = 1).
KR = 21.73
PIEZAS = {
    'SM_GhostSensor_SC': ('SensorMesh', [(BS + 'SM_BioSensor_SC', (0, 0, 0), 0.0, 1.0),
                                         (BS + 'SM_BioSensor_Button_SC', (0, 0, 0), 0.0, 1.0)]),
    'SM_GhostSave_SC': ('SaveMesh', [(SV + 'SM_SaveMelody_Base_SC', (0, 0, 0), 0.0, 1.0),
                                     (SV + 'SM_SaveMelody_Plate_SC', (0, 0, 0), 0.0, 1.0),
                                     (SV + 'SM_SaveMelody_Slider_SC', (0, 0, 0), 0.0, 1.0)]),
    'SM_GhostPalette_SC': ('PaletteMesh', [(DP + 'SM_DrawPalette_Base_SC', (0, 0, 0), 0.0, 1.0),
                                           (DP + 'SM_DrawPalette_Swatch_SC', (0, 0, 0), 0.0, 1.0)]
                           + [(DP + 'SM_DrawPalette_Key_SC', (0, 0, 0.9), y, 1.0) for y in (-60.0, -20.0, 20.0, 60.0)]
                           + [(DP + 'SM_DrawPalette_Key_SC', (0, 0, 0.9), y, 1.0) for y in (-120.0, -160.0, -200.0, -240.0)]
                           + [(DP + 'SM_DrawPalette_SideKey_SC', (0, 0, 0), -32.72, 1.4),
                              (DP + 'SM_DrawPalette_SideKey_SC', (0, 0, 0), 4.72, 1.4),
                              (DP + 'SM_DrawPalette_Slider_SC', (0, 0, 0), 0.0, 1.0),
                              (DP + 'SM_DrawPalette_Knob_SC', (-5.48, KR - 0.71, -1.705), 0.0, 0.863)]),
}
ID_XF = {'location': {'x': 0, 'y': 0, 'z': 0}, 'rotation': {'pitch': 0, 'yaw': 0, 'roll': 0}, 'scale': {'x': 1, 'y': 1, 'z': 1}}
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


def count_actors():
    ok, v = T(SC + 'find_actors', {'name': '', 'tag': '', 'collision_channels': []})
    return len(v or []) if ok else -1


def place(mesh, loc, yaw, sc, name):
    """StaticMeshActor con la malla, en P + loc. El xform de add_to_scene NO se aplica: se escribe en TEXTO y se relee."""
    ok, a = T(SC + 'add_to_scene_from_asset', {'asset_path': mesh, 'name': name, 'xform': ID_XF})
    if not ok or not a:
        return None
    ar = refp(a)
    ok, root = T(AT + 'get_root_component', {'actor': {'refPath': ar}})
    rr = refp(root)
    S(rr, {'relativeLocation': '(X=%f,Y=%f,Z=%f)' % (P[0] + loc[0], P[1] + loc[1], P[2] + loc[2])})
    S(rr, {'relativeRotation': '(Pitch=0.000000,Yaw=%f,Roll=0.000000)' % yaw})
    S(rr, {'relativeScale3D': '(X=%f,Y=%f,Z=%f)' % (sc, sc, sc)})
    return ar


def run():
    try:
        return run2()
    except BaseException as e:
        return {'err': 'run :: ' + str(e)[:300], 'log': LOG}


def run2():
    out = {'actores_antes': count_actors()}
    asignar = {}
    for name, (var, parts) in PIEZAS.items():
        rec = {}
        ok, ex = T(AS + 'exists', {'path': OUT + '/' + name})
        if not ex:
            actors = []
            for i, (mesh, loc, yaw, sc) in enumerate(parts):
                a = place(mesh, loc, yaw, sc, 'ZZ_merge_%s_%d' % (name, i))
                if a:
                    actors.append({'refPath': a})
            rec['piezas'] = '%d de %d' % (len(actors), len(parts))
            if len(actors) == len(parts):
                ok, r = T(SC + 'merge_actors', {'actors': actors, 'output_path': OUT, 'name': name, 'destroy_source_actors': True})
                rec['merge'] = ok
            # lo que haya quedado (fundido fallido o fuentes no destruidas) se saca: lo armo este script
            for a in actors:
                T(SC + 'remove_from_scene', {'actor': a})
            ok, ex = T(AS + 'exists', {'path': OUT + '/' + name})
        rec['existe'] = bool(ex)
        if ex:
            ok, b = T(SMT + 'get_bounds', {'mesh': {'refPath': OUT + '/' + name + '.' + name}})
            rec['bounds'] = b
            asignar[var] = OUT + '/' + name + '.' + name
        out[name] = rec
    for var, path in asignar.items():
        out['cdo_' + var] = S(PLAYER_CDO, {var: {'refPath': path}})
    if asignar:
        T(BT + 'compile_blueprint', {'blueprint': PLAYER})
        out['cdo_lectura'] = G(PLAYER_CDO, list(asignar.keys()))
    out['actores_despues'] = count_actors()
    out['log'] = LOG[:30]
    return out
