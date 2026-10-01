import json
# turn_build.py (2026-10-01) - BP_Credits_SC: SOLO variables y funciones (vacias) de StarsGrow. Idempotente; nunca levanta.
# Los 5 grafos se escriben DESPUES con llamadas DIRECTAS a write_graph_dsl (una por grafo, desde credits_graphs.json): con
# la Obra abierta y cambios de Beltran SIN GUARDAR, un execute_tool_script que falla dispara un Undo global (gotcha 557 /
# 2026-10-01: se llevo un actor del nivel); una llamada directa que falla se revierte sola (gotcha 560).
# NO toca CreditsStep ni el EventGraph (la llamada a StarsGrow se cuelga aparte, por cirugia directa).
B = '/Game/SoulCharger/Obra/BP_Credits_SC.BP_Credits_SC'   # CONFIRMAR con turn_read.py (credits_bp)
CDO = '/Game/SoulCharger/Obra/BP_Credits_SC.Default__BP_Credits_SC_C'
GJ = 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/credits/credits_graphs.json'
BT = 'editor_toolset.toolsets.blueprint.BlueprintTools.'
OT = 'editor_toolset.toolsets.object.ObjectTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
VARS = [('GrowTime', 'float', 'Stars', None), ('StarStep', 'float', 'Stars', None),
        ('StarsCached', 'bool', 'Z-Stars', None), ('StarsDone', 'bool', 'Z-Stars', None),
        ('StarActors', 'object', 'Z-Stars', '/Script/Engine.Actor'), ('StarScale', 'Vector', 'Z-Stars', None)]
ARRAYS = ('StarActors', 'StarScale')
FNS = {'StarsGrow': [], 'StarsCache': [], 'StarsCacheGo': [], 'StarsAll': [], 'StarOne': [('I', 'int')]}
LOG = []


def T(n, p):
    try:
        r = execute_tool(n, json.dumps(p))
        return True, (r['returnValue'] if isinstance(r, dict) and ('returnValue' in r) else r)
    except BaseException as e:
        LOG.append(n.split('.')[-1] + ' :: ' + str(e)[:180])
        return False, None


def refp(x):
    return str(x['refPath'] if isinstance(x, dict) and ('refPath' in x) else x)


def run():
    out = {}
    try:
        ok, vs = T(BT + 'list_variables', {'blueprint': B})
        have = set((v['name'] if isinstance(v, dict) else str(v)) for v in (vs or []))
        nuevas = []
        for name, typ, cat, cls in VARS:
            if name in have:
                continue
            cont = {'container_type': 'Array'} if name in ARRAYS else {}
            if typ == 'object':
                p = {'blueprint': B, 'name': name, 'object_class': cls}
                p.update(cont)
                ok, r = T(BT + 'add_object_variable', p)
            else:
                p = {'blueprint': B, 'name': name, 'type_name': typ}
                p.update(cont)
                ok, r = T(BT + 'add_variable', p)
            T(BT + 'set_variable_category', {'blueprint': B, 'variable_name': name, 'category': cat})
            if ok:
                nuevas.append(name)
        out['vars_nuevas'] = nuevas
        ok, gs = T(BT + 'list_graphs', {'blueprint': B})
        gnames = set(refp(g).split(':')[-1] for g in (gs or []))
        fns = []
        for fn, params in FNS.items():
            if fn in gnames:
                continue
            ok, r = T(BT + 'add_function_graph', {'blueprint': B, 'graph_name': fn})
            if not ok:
                continue
            fns.append(fn)
            for pn, pt in params:
                T(BT + 'add_function_param', {'graph': B + ':' + fn, 'param_name': pn, 'param_type': pt, 'input_param': True})
        out['funciones_nuevas'] = fns
        ok, r = T(BT + 'compile_blueprint', {'blueprint': B})
        T(OT + 'set_properties', {'instance': {'refPath': CDO}, 'values': json.dumps({'GrowTime': 1.2, 'StarStep': 0.18})})
        ok, g = T(OT + 'get_properties', {'instance': {'refPath': CDO}, 'properties': ['GrowTime', 'StarStep']})
        out['cdo'] = g
        ok, r = T(BT + 'compile_blueprint', {'blueprint': B})
        out['compile'] = r
    except BaseException as e:
        out['err'] = str(e)[:200]
    out['log'] = LOG[:12]
    return out
