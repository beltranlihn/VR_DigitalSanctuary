import json
# build_feed.py (2026-10-29) - crea BP_FeedDirector_SC (Test_Feed): variables con categoria, instance-editable, funciones y sus
# parametros. Copia de Focus/build_director.py. Idempotente (salta lo que ya existe). Nunca levanta. Sin `result = run()`.
# Los grafos van aparte (write_graph_dsl por llamada directa, gotcha 617). Los defaults del CDO van despues de compilar.
BT = 'editor_toolset.toolsets.blueprint.BlueprintTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
FOLDER = '/Game/SoulCharger/Mechanics/Mind/Blueprints'
NAME = 'BP_FeedDirector_SC'
BPR = FOLDER + '/' + NAME + '.' + NAME
BPo = {'refPath': BPR}
CELL = '/Game/SoulCharger/Mechanics/Mind/Blueprints/BP_LovingCell_SC.BP_LovingCell_SC_C'
FLUID = '/Game/SoulCharger/Mechanics/Mind/Blueprints/BP_FluidMedium_SC.BP_FluidMedium_SC_C'
SOUL = '/Game/SoulCharger/Core/ProtoSoul/BP_ProtoSoul_SC.BP_ProtoSoul_SC_C'
F = 'float'
# (nombre, tipo, categoria, editable, array)
def k(cat, names, t=F):
    return [(n, t, cat, True, False) for n in names.split()]
VARS = ([('Concepts', 'obj:' + SOUL, '1-Conceptos', True, True),
         ('TitleMats', 'obj:/Script/Engine.MaterialInterface', '1-Conceptos', True, True)]
        + k('1-Conceptos', 'HoldTime FadeBack GazeDeg GazeOut StartDelay ConceptDelay ConceptGap ConceptAppear HintDelay '
                           'HintLight HintHz ConceptGrow ConceptGlow ConceptSpin ChargePulse ChargePulseHz ExciteSpeed')
        + [('Main', 'obj:' + CELL, '2-Ameba', True, False), ('SleepTint', 'LinearColor', '2-Ameba', True, False)]
        + k('2-Ameba', 'RevealTime SleepState AwakeState SleepScale SleepDim SleepMix BloomTime BloomScale BloomLight DriftAmp '
                       'DriftHz DriftSleep WanderRot SleepAgit AwakeAgit FeedAgit AwakeLife AwakeCurl FeedLife FeedCurl LifeSteps FeedSpeed')
        + k('3-Punto', 'DotAngle DotIdle DotOpacity DotIdleOpacity')
        + [('DotColor', 'LinearColor', '3-Punto', True, False),
           ('DotMat', 'obj:/Script/Engine.MaterialInterface', '3-Punto', True, False),
           ('DotMesh', 'obj:/Script/Engine.StaticMesh', '3-Punto', True, False)]
        + k('4-Final', 'FinaleHold')
        + [('FeedSound', 'obj:/Script/Engine.SoundBase', '5-Sonido', True, False),
           ('FinaleSound', 'obj:/Script/Engine.SoundBase', '5-Sonido', True, False),
           ('SfxVol', F, '5-Sonido', True, False),
           ('HapticEffect', 'obj:/Script/Engine.HapticFeedbackEffect_Base', '5-Sonido', True, False),
           ('Fluid', 'obj:' + FLUID, '6-Mundo', True, False)]
        + k('6-Mundo', 'FluidCalm FluidActive')
        + [('MoteSystem', 'obj:/Script/Niagara.NiagaraSystem', '7-Particulas', True, False)]
        + k('7-Particulas', 'MoteRate MoteLife MoteSize MoteRadius MoteNoise MotePull MoteRelease MoteAlpha MoteFade '
                            'FlySpeed FlyRate FlyTime FlyRadius FlyNoise FlyPush FlyArc')
        + [('TitleMesh', 'obj:/Script/Engine.StaticMesh', '8-Titulos', True, False),
           ('EyePos', 'Vector', '8-Titulos', True, False)]
        + k('8-Titulos', 'TitleScale TitleDrop TitleDelay TitleTime TitleOutTime')
        + [('DebugTarget', 'int', '9-Prueba', True, False), ('bDebugAuto', 'bool', '9-Prueba', True, False)]
        + [(n, t, 'Z-Estado', False, True) for n, t in [
            ('Charge', F), ('Consumed', 'bool'), ('Reveal', F), ('RevealAt', F), ('ConsumeAt', F), ('FeedAt', F),
            ('FlyState', 'int'), ('Excite', F), ('MoteF', F), ('MoteOn', 'bool'),
            ('Motes', 'obj:/Script/Niagara.NiagaraComponent'), ('BaseSize', F), ('BaseEdge', F), ('BaseSpin', F),
            ('CCol', 'LinearColor'), ('TitleComps', 'obj:/Script/Engine.StaticMeshComponent'), ('OrigCol', 'LinearColor')]]
        + [(n, t, 'Z-Estado', False, False) for n, t in [
            ('MainHome', 'Vector'), ('MainRot', 'Rotator'), ('MainSc', 'Vector'), ('BaseLife', 'LinearColor'),
            ('BasePulse', F), ('WF', 'Vector'), ('WP', 'Vector'), ('MainRevealAt', F), ('Fed', 'int'), ('FedShown', F),
            ('LastFeedAt', F), ('LightP', F), ('Target', 'int'), ('GBest', 'int'), ('GBestDot', F), ('Clock', F),
            ('PhaseT', F), ('Phase', 'int'), ('NoLook', F), ('DotD', F), ('DotRing', F),
            ('DotComp', 'obj:/Script/Engine.StaticMeshComponent'), ('HintI', 'int'), ('LightSum', F), ('bStageDone', 'bool')]])
# (funcion, [(param, tipo, entrada)])  tipo 'obj:<clase>' = parametro objeto
FUNCS = [
    ('FdBoot', []), ('FdBootMain', []), ('FdStep', [('Dt', F, True)]), ('FdGaze', []), ('FdCharge', [('Dt', F, True)]),
    ('FdRevealConcepts', []), ('FdConsume', [('I', 'int', True)]), ('FdConcept', [('I', 'int', True), ('Dt', F, True)]),
    ('FdMote', [('I', 'int', True), ('Dt', F, True)]), ('FdMoteEdge', [('I', 'int', True), ('Want', 'bool', True)]),
    ('FdFly', [('I', 'int', True)]), ('FdMain', [('Dt', F, True)]), ('FdLook', [('L', F, True)]),
    ('FdMix', [('C', 'LinearColor', True), ('L', F, True), ('ReturnValue', 'LinearColor', False)]),
    ('FdDot', [('Dt', F, True)]), ('FdSound', [('Snd', 'obj:/Script/Engine.SoundBase', True)]),
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
                elif pt == 'LinearColor':
                    T(BT + 'add_struct_function_param', {'graph': g, 'param_name': pn, 'struct_type': {'refPath': '/Script/CoreUObject.LinearColor'}, 'input_param': inp})
                else:
                    T(BT + 'add_function_param', {'graph': g, 'param_name': pn, 'param_type': pt, 'input_param': inp})
        out['funcs_nuevas'] = fadded
        ok, c = T(BT + 'compile_blueprint', {'blueprint': BPo})
        out['compile'] = c
        out['log'] = LOG[:25]
        return out
    except BaseException as e:
        return {'err': 'run :: ' + str(e)[:300], 'log': LOG[:25]}
