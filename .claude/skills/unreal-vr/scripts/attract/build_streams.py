import json
# build_streams.py (2026-11-04) - crea BP_AttractStreams_SC (Test_AttractingHang): variables con categoria, instance-editable,
# funciones y sus parametros. Copia de feed/build_feed.py. Idempotente (salta lo que ya existe). Nunca levanta. Sin
# `result = run()`. Los grafos van aparte (write_graph_dsl por llamada directa, gotcha 617). Defaults del CDO despues de compilar.
BT = 'editor_toolset.toolsets.blueprint.BlueprintTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
FOLDER = '/Game/SoulCharger/Mechanics/Harp/Blueprints'
NAME = 'BP_AttractStreams_SC'
BPR = FOLDER + '/' + NAME + '.' + NAME
BPo = {'refPath': BPR}
HARP = '/Game/SoulCharger/Mechanics/Harp/Blueprints/BP_Harp_SC.BP_Harp_SC_C'
SMC = '/Script/Engine.StaticMeshComponent'
F = 'float'
def k(cat, names, t=F):
    return [(n, t, cat, True, False) for n in names.split()]
# (nombre, tipo, categoria, editable, array)
VARS = ([('Harp', 'obj:' + HARP, '0-Enlace', True, False), ('Amoeba', 'obj:/Script/Engine.Actor', '0-Enlace', True, False)]
        + [('MaxStreams', 'int', '1-Chorros', True, False)]
        + k('1-Chorros', 'Count Life Travel Bend Wobble WobbleHz Jitter')
        + k('2-Envoltura', 'Radius Squash CenterDrop Swirl Spread ShellNoise Follow')
        + k('3-Luz', 'Size MinAngle FadeIn FadeOut Brightness ColorPow')
        + [('MoteMesh', 'obj:/Script/Engine.StaticMesh', '3-Luz', True, False),
           ('MoteMat', 'obj:/Script/Engine.MaterialInterface', '3-Luz', True, False)]
        + k('4-Fuente', 'EmitOffset')
        + [('PreviewEye', 'Vector', '4-Fuente', True, False), ('NoAmoebaAt', 'Vector', '4-Fuente', True, False)]
        + [('PreviewStreams', 'int', '5-Prueba', True, False), ('bDebugNotes', 'bool', '5-Prueba', True, False),
           ('DebugEvery', F, '5-Prueba', True, False)]
        + [('Streams', 'obj:' + SMC, 'Z-Estado', False, True), ('Seen', F, 'Z-Estado', False, True)]
        + [(n, t, 'Z-Estado', False, False) for n, t in [
            ('Used', 'int'), ('Eye', 'Vector'), ('EmitW', 'Vector'), ('NextDebug', F)]])
# (funcion, [(param, tipo, entrada)])  'obj:<clase>' = objeto · 'struct:<ruta>' = struct
LC = 'struct:/Script/CoreUObject.LinearColor'
VEC = 'struct:/Script/CoreUObject.Vector'
FUNCS = [
    ('AsBuild', []), ('AsLook', [('Comp', 'obj:' + SMC, True)]),
    ('AsStart', [('Comp', 'obj:' + SMC, True), ('T0', F, True), ('Col', LC, True), ('Seed', F, True)]),
    ('AsPlace', [('Comp', 'obj:' + SMC, True), ('EyeL', VEC, True), ('EmitL', VEC, True)]),
    ('AsBoot', []), ('AsTick', [('Dt', F, True)]), ('AsSenseHarp', []), ('AsAdd', [('Col', LC, True)]),
    ('AsFollow', [('Dt', F, True)]), ('AsEmitUpdate', []), ('AsDebug', []),
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
