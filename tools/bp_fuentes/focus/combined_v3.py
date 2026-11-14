import json
BT = 'editor_toolset.toolsets.blueprint.BlueprintTools.'
BPR = '/Game/SoulCharger/Mechanics/Mind/Blueprints/BP_FocusDirector_SC.BP_FocusDirector_SC'
BPo = {'refPath': BPR}
WIPE = ['FcBoot', 'FcStep', 'FcCharge', 'FcCell']
GONE_VARS = ['ClockSeed', 'FinaleDelay', 'FinaleTime', 'OrbitAmp', 'OrbitPeriod', 'OrbitYaw']
PLOG = []


def P(name, payload):
    try:
        return True, execute_tool(name, json.dumps(payload))['returnValue']
    except BaseException as e:
        PLOG.append(name.split('.')[-1] + ' :: ' + str(e)[:180])
        return False, None


def prep():
    try:
        out = {}
        ok, pie = P('EditorToolset.EditorAppToolset.IsPIERunning', {})
        out['pie'] = pie
        if pie:
            return {'err': 'PIE corriendo: no se toca', 'log': PLOG}
        ok, acts = P('editor_toolset.toolsets.scene.SceneTools.find_actors', {'name': '', 'tag': '', 'collision_channels': []})
        out['actors_before'] = len(acts or [])
        wiped = {}
        for g in WIPE:
            ok, nodes = P(BT + 'find_nodes', {'graph': {'refPath': BPR + ':' + g}, 'title': ''})
            n = 0
            for nd in (nodes or []):
                ref = nd['refPath'] if isinstance(nd, dict) else str(nd)
                if 'FunctionEntry' in ref or 'FunctionResult' in ref:
                    continue
                ok2, _ = P(BT + 'delete_node', {'node': {'refPath': ref}})
                n += 1 if ok2 else 0
            wiped[g] = n
        out['wiped'] = wiped
        ok, _ = P(BT + 'remove_function_graph', {'blueprint': BPo, 'graph_name': 'FcFinale'})
        out['fcfinale_removed'] = ok
        rv = 0
        for v in GONE_VARS:
            ok, _ = P(BT + 'remove_variable', {'blueprint': BPo, 'name': v})
            rv += 1 if ok else 0
        out['vars_removed'] = rv
        ok, c = P(BT + 'compile_blueprint', {'blueprint': BPo})
        out['compile_mid'] = c
        out['plog'] = PLOG[:25]
        return out
    except BaseException as e:
        return {'err': 'prep :: ' + str(e)[:300], 'log': PLOG[:25]}

AS = 'editor_toolset.toolsets.asset.AssetTools.'
FOLDER = '/Game/SoulCharger/Mechanics/Mind/Blueprints'
NAME = 'BP_FocusDirector_SC'
BPR = FOLDER + '/' + NAME + '.' + NAME
BPo = {'refPath': BPR}
CELL = '/Game/SoulCharger/Mechanics/Mind/Blueprints/BP_LovingCell_SC.BP_LovingCell_SC_C'
FLUID = '/Game/SoulCharger/Mechanics/Mind/Blueprints/BP_FluidMedium_SC.BP_FluidMedium_SC_C'
VARS = [
    ('Cells', 'obj:' + CELL, '1-Foco', True, True),
    ('HoldTime', 'float', '1-Foco', True, False), ('FadeBack', 'float', '1-Foco', True, False),
    ('GazeDeg', 'float', '1-Foco', True, False), ('GazeOut', 'float', '1-Foco', True, False),
    ('StartDelay', 'float', '1-Foco', True, False), ('RevealDelay', 'float', '1-Foco', True, False),
    ('RevealTime', 'float', '1-Foco', True, False), ('RevealGap', 'float', '1-Foco', True, False),
    ('HintDelay', 'float', '1-Foco', True, False),
    ('SleepState', 'float', '2-Ameba', True, False), ('AwakeState', 'float', '2-Ameba', True, False),
    ('SleepScale', 'float', '2-Ameba', True, False), ('SleepDim', 'float', '2-Ameba', True, False),
    ('SleepMix', 'float', '2-Ameba', True, False), ('SleepTint', 'LinearColor', '2-Ameba', True, False),
    ('BloomTime', 'float', '2-Ameba', True, False), ('BloomScale', 'float', '2-Ameba', True, False),
    ('BloomLight', 'float', '2-Ameba', True, False), ('DriftAmp', 'float', '2-Ameba', True, False),
    ('DriftHz', 'float', '2-Ameba', True, False), ('DriftSleep', 'float', '2-Ameba', True, False),
    ('WanderRot', 'float', '2-Ameba', True, False), ('HintLight', 'float', '2-Ameba', True, False),
    ('HintHz', 'float', '2-Ameba', True, False), ('SleepAgit', 'float', '2-Ameba', True, False),
    ('AwakeAgit', 'float', '2-Ameba', True, False), ('ChargeAgit', 'float', '2-Ameba', True, False),
    ('ChargePulse', 'float', '2-Ameba', True, False), ('ChargePulseHz', 'float', '2-Ameba', True, False),
    ('AwakeLife', 'float', '2-Ameba', True, False), ('ChargeLife', 'float', '2-Ameba', True, False),
    ('AwakeCurl', 'float', '2-Ameba', True, False), ('ChargeCurl', 'float', '2-Ameba', True, False),
    ('LifeSteps', 'float', '2-Ameba', True, False), ('ExciteSpeed', 'float', '2-Ameba', True, False),
    ('DotAngle', 'float', '3-Punto', True, False), ('DotIdle', 'float', '3-Punto', True, False),
    ('DotColor', 'LinearColor', '3-Punto', True, False), ('DotOpacity', 'float', '3-Punto', True, False),
    ('DotIdleOpacity', 'float', '3-Punto', True, False),
    ('DotMat', 'obj:/Script/Engine.MaterialInterface', '3-Punto', True, False),
    ('DotMesh', 'obj:/Script/Engine.StaticMesh', '3-Punto', True, False),
    ('FinaleHold', 'float', '4-Final', True, False),
    ('RevealSound', 'obj:/Script/Engine.SoundBase', '5-Sonido', True, False),
    ('ChargeSound', 'obj:/Script/Engine.SoundBase', '5-Sonido', True, False),
    ('LockSound', 'obj:/Script/Engine.SoundBase', '5-Sonido', True, False),
    ('FinaleSound', 'obj:/Script/Engine.SoundBase', '5-Sonido', True, False),
    ('SfxVol', 'float', '5-Sonido', True, False),
    ('HapticEffect', 'obj:/Script/Engine.HapticFeedbackEffect_Base', '5-Sonido', True, False),
    ('Fluid', 'obj:' + FLUID, '6-Mundo', True, False),
    ('FluidCalm', 'float', '6-Mundo', True, False), ('FluidActive', 'float', '6-Mundo', True, False),
    ('MoteSystem', 'obj:/Script/Niagara.NiagaraSystem', '7-Particulas', True, False),
    ('MoteRate', 'float', '7-Particulas', True, False), ('MoteLife', 'float', '7-Particulas', True, False),
    ('MoteSize', 'float', '7-Particulas', True, False), ('MoteRadius', 'float', '7-Particulas', True, False),
    ('MoteNoise', 'float', '7-Particulas', True, False), ('MotePull', 'float', '7-Particulas', True, False),
    ('MoteRelease', 'float', '7-Particulas', True, False), ('MoteAlpha', 'float', '7-Particulas', True, False),
    ('MoteFade', 'float', '7-Particulas', True, False),
    ('DebugTarget', 'int', '9-Prueba', True, False), ('bDebugAuto', 'bool', '9-Prueba', True, False),
    ('Charge', 'float', 'Z-Estado', False, True), ('Locked', 'bool', 'Z-Estado', False, True),
    ('Reveal', 'float', 'Z-Estado', False, True), ('RevealAt', 'float', 'Z-Estado', False, True),
    ('LockAt', 'float', 'Z-Estado', False, True), ('LightP', 'float', 'Z-Estado', False, True),
    ('Excite', 'float', 'Z-Estado', False, True), ('MoteF', 'float', 'Z-Estado', False, True),
    ('MoteOn', 'bool', 'Z-Estado', False, True), ('Motes', 'obj:/Script/Niagara.NiagaraComponent', 'Z-Estado', False, True),
    ('BaseLife', 'LinearColor', 'Z-Estado', False, True), ('BasePulse', 'float', 'Z-Estado', False, True),
    ('WF', 'Vector', 'Z-Estado', False, True), ('WP', 'Vector', 'Z-Estado', False, True),
    ('Home', 'Vector', 'Z-Estado', False, True), ('HomeRot', 'Rotator', 'Z-Estado', False, True),
    ('BaseSc', 'Vector', 'Z-Estado', False, True), ('OrigCol', 'LinearColor', 'Z-Estado', False, True),
    ('DotComp', 'obj:/Script/Engine.StaticMeshComponent', 'Z-Estado', False, False),
    ('ChargeAC', 'obj:/Script/Engine.AudioComponent', 'Z-Estado', False, False),
    ('Target', 'int', 'Z-Estado', False, False), ('GBest', 'int', 'Z-Estado', False, False),
    ('GBestDot', 'float', 'Z-Estado', False, False), ('Clock', 'float', 'Z-Estado', False, False),
    ('PhaseT', 'float', 'Z-Estado', False, False), ('Phase', 'int', 'Z-Estado', False, False),
    ('NoLook', 'float', 'Z-Estado', False, False), ('DotD', 'float', 'Z-Estado', False, False),
    ('DotRing', 'float', 'Z-Estado', False, False),
    ('LockedN', 'int', 'Z-Estado', False, False), ('HintI', 'int', 'Z-Estado', False, False),
    ('ChargeOn', 'int', 'Z-Estado', False, False), ('LightSum', 'float', 'Z-Estado', False, False),
    ('RevSnd', 'bool', 'Z-Estado', False, False), ('bStageDone', 'bool', 'Z-Estado', False, False),
]
FUNCS = [
    ('FcBoot', []), ('FcStep', [('Dt', 'float', True)]), ('FcGaze', []), ('FcCharge', [('Dt', 'float', True)]),
    ('FcChargeSnd', [('W', 'int', True)]), ('FcACFade', []), ('FcLock', [('I', 'int', True)]),
    ('FcSound', [('Snd', 'obj:/Script/Engine.SoundBase', True)]), ('FcRevealRest', []),
    ('FcCell', [('I', 'int', True)]), ('FcLook', [('I', 'int', True), ('L', 'float', True)]),
    ('FcMix', [('C', 'LinearColor', True), ('L', 'float', True), ('ReturnValue', 'LinearColor', False)]),
    ('FcDot', [('Dt', 'float', True)]), ('FcMote', [('I', 'int', True), ('Dt', 'float', True)]),
    ('FcMoteEdge', [('I', 'int', True), ('Want', 'bool', True)]),
]
LOG = []


def T(name, payload):
    try:
        return True, execute_tool(name, json.dumps(payload))['returnValue']
    except BaseException as e:
        LOG.append(name.split('.')[-1] + ' :: ' + str(e)[:180])
        return False, None


def build_run():
    try:
        out = {}
        ok, ex = T(AS + 'exists', {'path': FOLDER + '/' + NAME})
        if not ex:
            ok, r = T(BT + 'create', {'folder_path': FOLDER, 'asset_name': NAME, 'asset_type': {'refPath': '/Script/Engine.Actor'}})
            out['creado'] = ok
        ok, have = T(BT + 'list_variables', {'blueprint': BPo})
        have = set(have or [])
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


def run():
    res = {}
    try:
        res['prep'] = prep()
        if res['prep'].get('err'):
            return res
        res['build'] = build_run()
        ok, a = P('editor_toolset.toolsets.scene.SceneTools.find_actors', {'name': '', 'tag': '', 'collision_channels': []})
        res['actors_after'] = len(a or [])
    except BaseException as e:
        res['err'] = str(e)[:300]
    return res