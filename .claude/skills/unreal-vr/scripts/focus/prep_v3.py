import json
# prep_v3.py (2026-10-29, 3.a vuelta) - vacia los grafos que se reescriben (deja FunctionEntry/Result), saca FcFinale y las
# variables del vaiven comun, y corre build_director.run() (variables y funciones nuevas). Nunca levanta. Sin `result = run()`.
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
