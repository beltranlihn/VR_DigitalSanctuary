import json
# build_call.py (2026-11-04) - crea BP_AttractCall_SC (Test_AttractingHang): llamada y respuesta. Copia de build_streams.py.
# Idempotente. Nunca levanta. Sin `result = run()`. Grafos aparte (write_graph_dsl por llamada directa). Defaults del CDO
# despues de compilar.
BT = 'editor_toolset.toolsets.blueprint.BlueprintTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
FOLDER = '/Game/SoulCharger/Mechanics/Harp/Blueprints'
NAME = 'BP_AttractCall_SC'
BPR = FOLDER + '/' + NAME + '.' + NAME
BPo = {'refPath': BPR}
HARP = '/Game/SoulCharger/Mechanics/Harp/Blueprints/BP_Harp_SC.BP_Harp_SC_C'
SOUL = '/Game/SoulCharger/Core/ProtoSoul/BP_ProtoSoul_SC.BP_ProtoSoul_SC_C'
SMC = '/Script/Engine.StaticMeshComponent'
F = 'float'
def k(cat, names, t=F):
    return [(n, t, cat, True, False) for n in names.split()]
VARS = ([('Harp', 'obj:' + HARP, '0-Enlace', True, False), ('Voice', 'obj:' + HARP, '0-Enlace', True, False),
         ('Amoeba', 'obj:' + SOUL, '0-Enlace', True, False)]
        + k('1-Onda', 'WaveSpeed RingWidth RingWidthGrow RingAlpha ReturnAlpha RingFade RingAfter RingSoft RingGlow RingZ')
        + [('RingPool', 'int', '1-Onda', True, False),
           ('RingMesh', 'obj:/Script/Engine.StaticMesh', '1-Onda', True, False),
           ('RingMat', 'obj:/Script/Engine.MaterialInterface', '1-Onda', True, False)]
        + [('FarPoint', 'Vector', '2-Ameba', True, False), ('NearPoint', 'Vector', '2-Ameba', True, False)]
        + k('2-Ameba', 'AmoebaSize StepPerCall StepVelGain Drift Brake BrakeFloor GlowPeak GlowDecay')
        + k('3-Voz', 'VoiceSpeedFar VoiceSpeedNear')
        + [('bVoiceRight', 'bool', '3-Voz', True, False)]
        + [('bDebugNotes', 'bool', '4-Prueba', True, False), ('DebugEvery', F, '4-Prueba', True, False),
           ('bPreviewEmbrace', 'bool', '4-Prueba', True, False), ('PreviewEye', 'Vector', '4-Prueba', True, False)]
        + k('5-Abrazo', 'EmbraceTime EmbraceSize ShellRadius ShellAlpha ShellGlow ShellWobble ShellVeins')
        + [('ShellColor', 'LinearColor', '5-Abrazo', True, False),
           ('ShellMesh', 'obj:/Script/Engine.StaticMesh', '5-Abrazo', True, False),
           ('ShellMat', 'obj:/Script/Engine.MaterialInterface', '5-Abrazo', True, False)]
        + [(n, t, 'Z-Estado', False, True) for n, t in [
            ('Rings', 'obj:' + SMC), ('RAge', F), ('RRad', F), ('RHit', F), ('RKind', 'int'), ('RVoice', 'int'),
            ('RVel', F), ('RFired', 'bool'), ('RAlive', 'bool'), ('Seen', F)]]
        + [(n, t, 'Z-Estado', False, False) for n, t in [
            ('Progress', F), ('Shown', F), ('Pulse', F), ('BaseEdge', F), ('NextRing', 'int'), ('NextDebug', F),
            ('Calls', 'int'), ('bStageDone', 'bool'), ('Embrace', F), ('bEmbracing', 'bool'), ('EmbraceEye', 'Vector'),
            ('Shell', 'obj:' + SMC)]])
LC = 'struct:/Script/CoreUObject.LinearColor'
VEC = 'struct:/Script/CoreUObject.Vector'
FUNCS = [
    ('AcBuild', []), ('AcBoot', []), ('AcTick', [('Dt', F, True)]), ('AcSense', []),
    ('AcCall', [('V', 'int', True), ('Vel', F, True)]),
    ('AcRing', [('Kind', 'int', True), ('V', 'int', True), ('Vel', F, True), ('Origin', VEC, True), ('Col', LC, True)]),
    ('AcRingStep', [('I', 'int', True), ('Dt', F, True), ('Eye', VEC, True)]),
    ('AcArrive', [('I', 'int', True)]), ('AcAnswer', [('V', 'int', True), ('Vel', F, True)]),
    ('AcAmoeba', [('Dt', F, True)]), ('AcDebug', []), ('AcBootVoice', []), ('AcBootHarp', []),
    ('AcEmbrace', [('Dt', F, True), ('Eye', VEC, True)]), ('AcEmbraceStep', [('Dt', F, True)]),
]
LOG = []


def T(name, payload):
    try:
        return True, execute_tool(name, json.dumps(payload))['returnValue']
    except BaseException as e:
        LOG.append(name.split('.')[-1] + ' :: ' + str(e)[:180])
        return False, None


def run():
    try:
        out = {}
        ok, ex = T(AS + 'exists', {'path': FOLDER + '/' + NAME})
        if not ex:
            ok, r = T(BT + 'create', {'folder_path': FOLDER, 'asset_name': NAME, 'asset_type': {'refPath': '/Script/Engine.Actor'}})
            out['creado'] = ok
        ok, have = T(BT + 'list_variables', {'blueprint': BPo})
        have = set([(h['name'] if isinstance(h, dict) else str(h)) for h in (have or [])])
        added = 0
        for n, t, cat, ed, arr in VARS:
            if n not in have:
                args = {'blueprint': BPo, 'name': n}
                if arr:
                    args['container_type'] = 'Array'
                if t.startswith('obj:'):
                    args['object_class'] = {'refPath': t[4:]}
                    ok, _ = T(BT + 'add_object_variable', args)
                else:
                    args['type_name'] = t
                    ok, _ = T(BT + 'add_variable', args)
                added += 1 if ok else 0
            T(BT + 'set_variable_category', {'blueprint': BPo, 'variable_name': n, 'category': cat})
            if ed:
                T(BT + 'set_variable_instance_editable', {'blueprint': BPo, 'variable_name': n, 'instance_editable': True})
        out['vars_nuevas'] = added
        out['vars_total'] = len(VARS)
        ok, gr = T(BT + 'list_graphs', {'blueprint': BPo})
        gnames = set([(g['refPath'] if isinstance(g, dict) else str(g)).split(':')[-1] for g in (gr or [])])
        fadded = 0
        for fn, params in FUNCS:
            if fn in gnames:
                continue
            ok, _ = T(BT + 'add_function_graph', {'blueprint': BPo, 'graph_name': fn})
            if not ok:
                continue
            fadded += 1
            g = {'refPath': BPR + ':' + fn}
            for pn, pt, inp in params:
                if pt.startswith('obj:'):
                    T(BT + 'add_object_function_param', {'graph': g, 'param_name': pn, 'object_class': {'refPath': pt[4:]}, 'input_param': inp})
                elif pt.startswith('struct:'):
                    T(BT + 'add_struct_function_param', {'graph': g, 'param_name': pn, 'struct_type': {'refPath': pt[7:]}, 'input_param': inp})
                else:
                    T(BT + 'add_function_param', {'graph': g, 'param_name': pn, 'param_type': pt, 'input_param': inp})
        out['funcs_nuevas'] = fadded
        ok, c = T(BT + 'compile_blueprint', {'blueprint': BPo})
        out['compile'] = c
        out['log'] = LOG[:25]
        return out
    except BaseException as e:
        return {'err': 'run :: ' + str(e)[:300], 'log': LOG[:25]}
