import json
# build_thoughts.py (2026-10-30) - crea BP_ThoughtsDirector_SC (Test_Thoughts): variables con categoria, instance-editable,
# funciones y sus parametros. Copia de Feed/build_feed.py. Idempotente (salta lo que ya existe). Nunca levanta. Sin `result = run()`.
# Los grafos van aparte (write_graph_dsl por llamada directa, gotcha 617). Los defaults del CDO van despues de compilar.
BT = 'editor_toolset.toolsets.blueprint.BlueprintTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
FOLDER = '/Game/SoulCharger/Mechanics/Mind/Blueprints'
NAME = 'BP_ThoughtsDirector_SC'
BPR = FOLDER + '/' + NAME + '.' + NAME
BPo = {'refPath': BPR}
CELL = '/Game/SoulCharger/Mechanics/Mind/Blueprints/BP_LovingCell_SC.BP_LovingCell_SC_C'
FLUID = '/Game/SoulCharger/Mechanics/Mind/Blueprints/BP_FluidMedium_SC.BP_FluidMedium_SC_C'
SOUL = '/Game/SoulCharger/Core/ProtoSoul/BP_ProtoSoul_SC.BP_ProtoSoul_SC_C'
SND = 'obj:/Script/Engine.SoundBase'
F = 'float'
def k(cat, names, t=F):
    return [(n, t, cat, True, False) for n in names.split()]
VARS = ([('Thoughts', 'obj:' + SOUL, '1-Pensamientos', True, True),
         ('TitleMats', 'obj:/Script/Engine.MaterialInterface', '1-Pensamientos', True, True),
         ('Slots', 'obj:/Script/Engine.Actor', '1-Pensamientos', True, True)]
        + k('1-Pensamientos', 'GazeDeg GazeOut ObsSpeed ObsGrow ObsGlow ObsSpin LifeMin LifeMax ReleaseLife GapMin GapMax '
                              'FormDelay FormGap LifeSteps')
        + k('2-Eleccion', 'HoldTime FadeBack ChooseGrow ChooseGlow ChargePulse ChargePulseHz ExciteSpeed ChoiceDelay '
                          'ChoiceTimeout ChosenTint ChosenDrop ChosenScale Burst BurstGrow BurstGlow ShrinkTime GatherDelay GatherGap')
        + [('Main', 'obj:' + CELL, '3-Ameba', True, False), ('SleepTint', 'LinearColor', '3-Ameba', True, False)]
        + k('3-Ameba', 'RevealTime SleepState AwakeState SleepScale SleepDim SleepMix BloomTime BloomScale BloomLight DriftAmp '
                       'DriftHz DriftSleep WanderRot SleepAgit AwakeAgit FeedAgit AwakeLife AwakeCurl FeedLife FeedCurl FeedSpeed '
                       'AttnMax AttnFull FeedKick BloomRise')
        + k('4-Tiempos', 'StartDelay DustAt T22 T23 FinaleHold')
        + [('VoLines', SND, '5-Sonido', True, True), ('FeedSound', SND, '5-Sonido', True, False),
           ('HapticEffect', 'obj:/Script/Engine.HapticFeedbackEffect_Base', '5-Sonido', True, False)]
        + k('5-Sonido', 'VoVol SfxVol')
        + [('Fluid', 'obj:' + FLUID, '6-Mundo', True, False)]
        + k('6-Mundo', 'FluidCalm FluidActive')
        + [('MoteSystem', 'obj:/Script/Niagara.NiagaraSystem', '7-Particulas', True, False),
           ('DustColor', 'LinearColor', '7-Particulas', True, False)]
        + k('7-Particulas', 'MoteRate MoteLife MoteSize MoteRadius MoteNoise MotePull MoteRelease MoteAlpha MoteFade '
                            'FlySpeed FlyRate FlyTime FlyRadius FlyNoise FlyPush FlyArc DustRate DustRadius DustDist DustSpeed DustAlpha BurstRadius')
        + [('TitleMesh', 'obj:/Script/Engine.StaticMesh', '8-Titulos', True, False),
           ('EyePos', 'Vector', '8-Titulos', True, False)]
        + k('8-Titulos', 'TitleScale TitleDrop TitleTime TitleOutTime TitleRise')
        + [('DebugTarget', 'int', '9-Prueba', True, False), ('bDebugAuto', 'bool', '9-Prueba', True, False)]
        + [(n, t, 'Z-Estado', False, True) for n, t in [
            ('TState', 'int'), ('Obs', F), ('ObsTotal', F), ('Charge', F), ('Excite', F), ('NextAt', F), ('DieAt', F),
            ('ConsumeAt', F), ('FeedAt', F), ('FlyAt', F), ('FlyState', 'int'), ('MoteF', F), ('MoteOn', 'bool'),
            ('Motes', 'obj:/Script/Niagara.NiagaraComponent'), ('SlotOf', 'int'), ('SlotLoc', 'Vector'), ('SlotBusy', 'bool'),
            ('BaseSize', F), ('BaseEdge', F), ('BaseSpin', F), ('CCol', 'LinearColor'),
            ('TitleComps', 'obj:/Script/Engine.StaticMeshComponent'), ('OrigCol', 'LinearColor')]]
        + [(n, t, 'Z-Estado', False, False) for n, t in [
            ('MainHome', 'Vector'), ('MainRot', 'Rotator'), ('MainSc', 'Vector'), ('BaseLife', 'LinearColor'),
            ('BasePulse', F), ('WF', 'Vector'), ('WP', 'Vector'), ('MainRevealAt', F), ('CellE', F), ('CellV', F), ('AttnSum', F),
            ('BloomE', F), ('BloomV', F), ('GatherK', 'int'), ('LightP', F), ('TintNow', F), ('Target', 'int'), ('HintI', 'int'), ('GBest', 'int'),
            ('GBestDot', F), ('Clock', F), ('Phase', 'int'), ('Chosen', 'int'), ('ChosenAt', F), ('bChosenIn', 'bool'),
            ('ChosenInAt', F), ('bFormOn', 'bool'), ('bChoiceOn', 'bool'), ('PickSlot', 'int'), ('PickStart', 'int'),
            ('DustComp', 'obj:/Script/Niagara.NiagaraComponent'), ('DustPos', 'Vector'),
            ('ChosenComp', 'obj:/Script/Engine.StaticMeshComponent'), ('LightSum', F), ('bStageDone', 'bool')]])
# (funcion, [(param, tipo, entrada)])  tipo 'obj:<clase>' = parametro objeto
FUNCS = [
    ('TdBoot', []), ('TdBootMain', []), ('TdStep', [('Dt', F, True)]), ('TdPhase', []), ('TdGaze', []),
    ('TdThought', [('I', 'int', True), ('Dt', F, True)]), ('TdForm', [('I', 'int', True)]), ('TdFade', [('I', 'int', True)]),
    ('TdChoose', [('I', 'int', True)]), ('TdAutoChoose', []), ('TdConsume', [('I', 'int', True), ('At', F, True)]),
    ('TdMote', [('I', 'int', True), ('Dt', F, True)]), ('TdMoteEdge', [('I', 'int', True), ('Want', 'bool', True)]),
    ('TdFly', [('I', 'int', True)]), ('TdDust', [('Dt', F, True)]), ('TdDustAt', [('Dt', F, True), ('P', 'Vector', True)]),
    ('TdMain', [('Dt', F, True)]), ('TdChosenTitle', []), ('TdLook', [('L', F, True)]),
    ('TdMix', [('C', 'LinearColor', True), ('L', F, True), ('ReturnValue', 'LinearColor', False)]),
    ('TdSound', [('Snd', SND, True), ('Vol', F, True)]),
]
STRUCTS = {'LinearColor': '/Script/CoreUObject.LinearColor', 'Vector': '/Script/CoreUObject.Vector'}
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
                elif pt in STRUCTS:
                    T(BT + 'add_struct_function_param', {'graph': g, 'param_name': pn, 'struct_type': {'refPath': STRUCTS[pt]}, 'input_param': inp})
                else:
                    T(BT + 'add_function_param', {'graph': g, 'param_name': pn, 'param_type': pt, 'input_param': inp})
        out['funcs_nuevas'] = fadded
        ok, c = T(BT + 'compile_blueprint', {'blueprint': BPo})
        out['compile'] = c
        out['log'] = LOG[:25]
        return out
    except BaseException as e:
        return {'err': 'run :: ' + str(e)[:300], 'log': LOG[:25]}
