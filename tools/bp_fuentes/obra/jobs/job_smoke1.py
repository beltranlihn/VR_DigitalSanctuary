import json
BT = 'editor_toolset.toolsets.blueprint.BlueprintTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
OT = 'editor_toolset.toolsets.object.ObjectTools.'
ST = 'editor_toolset.toolsets.scene.SceneTools.'
DUMP = 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/Obra/dump/smoke1_out.json'
JOBS = [{'bp': '/Game/SoulCharger/Obra/BP_Obra_SC.BP_Obra_SC', 'pkg': '/Game/SoulCharger/Obra/BP_Obra_SC', 'cdo': '/Game/SoulCharger/Obra/BP_Obra_SC.Default__BP_Obra_SC_C', 'vars': [('Smoke', 'bool', False, 'Debug'), ('SmokePhase', 'int', -99, 'Debug'), ('SmokeStage', 'int', -99, 'Debug')], 'graphs': [('ObraCmdLine', '(fn ObraCmdLine ()\n  (bind _cmd (Utilities|GetCommandLine))\n  (bind (_val _found) (Utilities|ParseParamValue _cmd "ObraSpeed="))\n  (if _found\n    (Variables|Default|SetSpeed (Utilities|String|StringToFloat _val))\n    (Development|PrintString (Utilities|String|Append "OBRA: Speed por linea de comandos = " _val) false))\n  (if (Utilities|ParseParam _cmd "ObraSmoke")\n    (Variables|Default|SetSmoke true)\n    (Variables|Default|SetDisclaimer false)\n    (Variables|Default|SetSimulated true)\n    (Variables|Debug|SetDebugStart -1)\n    (Development|PrintString "OBRA SMOKE: modo prueba de humo (sin aviso, datos simulados, arranque normal)" false))\n  (Development|PrintString (Utilities|String|Append (Utilities|String|Append (Utilities|String|Append (Utilities|String|Append (Utilities|String|Append (Utilities|String|Append (Utilities|String|Append (Utilities|String|Append (Utilities|String|Append (Utilities|String|Append (Utilities|String|Append (Utilities|String|Append (Utilities|String|Append (Utilities|String|Append (Utilities|String|Append "OBRA CONFIG: Speed=" (Utilities|String|ToString(Float) (Variables|Default|GetSpeed))) " Simulated=") (Utilities|String|ToString(Boolean) (Variables|Default|GetSimulated))) " Disclaimer=") (Utilities|String|ToString(Boolean) (Variables|Default|GetDisclaimer))) " DebugStart=") (Utilities|String|ToString(Integer) (Variables|Debug|GetDebugStart))) " DebugShare=") (Utilities|String|ToString(Integer) (Variables|Default|GetDebugShare))) " DbgDrawSynth=") (Utilities|String|ToString(Boolean) (Variables|Default|GetDbgDrawSynth))) " Photos=") (Utilities|String|ToString(Boolean) (Variables|Default|GetPhotos))) " DebugEnding=") (Utilities|String|ToString(Boolean) (Variables|Default|GetDebugEnding))) false)\n  (if (or (!= (Variables|Default|GetSpeed) 1.0) (or (>= (Variables|Debug|GetDebugStart) 1) (or (Variables|Default|GetDbgDrawSynth) (or (Variables|Default|GetPhotos) (or (Variables|Default|GetDebugEnding) (!= (Variables|Default|GetDebugShare) -1))))))\n    (Development|PrintString "OBRA CONFIG: ATENCION - hay perillas de prueba encendidas: esto NO es un build de publico" false)))\n'), ('SmokeTick', '(fn SmokeTick ()\n  (bind _ph (Variables|Default|GetPhase))\n  (bind _st (Variables|Default|GetStage))\n  (if (and (Variables|Default|GetSmoke) (or (!= _ph (Variables|Default|GetSmokePhase)) (!= _st (Variables|Default|GetSmokeStage))))\n    (Variables|Default|SetSmokePhase _ph)\n    (Variables|Default|SetSmokeStage _st)\n    (Development|PrintString (Utilities|String|Append (Utilities|String|Append (Utilities|String|Append "OBRA SMOKE: fase " (Utilities|String|ToString(Integer) _ph)) " etapa ") (Utilities|String|ToString(Integer) _st)) false))\n  (if (and (Variables|Default|GetSmoke) (and (== _ph 15) (>= (Variables|Default|GetPT) 3.0)))\n    (Development|PrintString "OBRA SMOKE: FIN OK" false)\n    (Game|QuitGame)))\n'), ('SimCut', '(fn SimCut ()\n  (if (and (Variables|Default|GetSimulated) (and (== (Variables|Default|GetPhase) 6) (and (== (Variables|Default|GetStage) 3) (>= (Variables|Default|GetPT) (Variables|Default|GetSimStageMax)))))\n    (Variables|Default|SetPT 1000.0)\n    (Development|PrintString "OBRA: modo simulado - la etapa cierra por SimStageMax" false))\n  (if (not (== (Variables|Default|GetPhase) 6))\n    (Variables|Default|SetDrawCutDone false))\n  (if (and (Variables|Default|GetDbgDrawSynth) (and (== (Variables|Default|GetPhase) 6) (and (== (Variables|Default|GetStage) 4) (>= (Variables|Default|GetPT) 2.0))))\n    (Variables|Default|SetDbgDrawSynth false)\n    (Class|BPTBDirectorNC|DbgSynth :self (Actor|GetActorOfClass "/Game/NeuralCanvas/TB/BP_TBDirector_NC.BP_TBDirector_NC_C")))\n  (if (and (== (Variables|Default|GetPhase) 6) (and (== (Variables|Default|GetStage) 4) (and (not (Variables|Default|GetDrawCutDone)) (>= (Variables|Default|GetPT) (select (Variables|Default|GetSimulated) (Variables|Default|GetSimStageMax) (Variables|Default|GetDrawCutT))))))\n    (Variables|Default|SetDrawCutDone true)\n    (Variables|Default|SetDrawCutAt (Variables|Default|GetPT))\n    (Development|PrintString "OBRA: dibujo - se acabo el tiempo: se guarda y se presenta antes de la carga" false)\n    (Class|BPTBDirectorNC|TimeUp :self (Actor|GetActorOfClass "/Game/NeuralCanvas/TB/BP_TBDirector_NC.BP_TBDirector_NC_C")))\n  (if (and (== (Variables|Default|GetPhase) 6) (and (== (Variables|Default|GetStage) 4) (and (Variables|Default|GetDrawCutDone) (>= (Variables|Default|GetPT) (+ (Variables|Default|GetDrawCutAt) (Variables|Default|GetDrawCutWait))))))\n    (Variables|Default|SetPT 1000.0)\n    (Development|PrintString "OBRA: dibujo - tope de seguridad despues del corte" false))\n  (CallFunction|SmokeTick)\n  (CallFunction|ObraDbgFF))\n')], 'save': False, 'read': ['ObraCmdLine', 'SmokeTick', 'SimCut']}]
# JOBS = [{'bp': '/Game/..BP.BP', 'pkg': '/Game/..BP', 'cdo': '/Game/..Default__BP_C',
#          'vars': [(name, type, default, category)], 'graphs': [(name, code)], 'write': True}]
LOG = []
def T(name, payload):
    try:
        return True, execute_tool(name, json.dumps(payload))['returnValue']
    except BaseException as e:
        LOG.append(name.split('.')[-1] + ' :: ' + str(e)[:400])
        return False, None
def graphs_of(bp):
    ok, gs = T(BT + 'list_graphs', {'blueprint': {'refPath': bp}})
    return [g['refPath'].split(':')[-1] for g in (gs or [])]
def mk(bp, name):
    if name not in graphs_of(bp):
        T(BT + 'add_function_graph', {'blueprint': {'refPath': bp}, 'graph_name': name})
def clear(g):
    ok, ns = T(BT + 'find_nodes', {'graph': {'refPath': g}, 'title': ''})
    for n in (ns or []):
        r = n['refPath'] if isinstance(n, dict) else str(n)
        if 'FunctionEntry' not in r and 'FunctionResult' not in r:
            T(BT + 'delete_node', {'node': {'refPath': r}})
def dry(bp, name, code):
    tmp = '_tmp_' + name
    before = set(graphs_of(bp))
    mk(bp, tmp)
    T(BT + 'compile_blueprint', {'blueprint': {'refPath': bp}})
    n0 = len(LOG)
    okd, w = T(BT + 'write_graph_dsl', {'graph': {'refPath': bp + ':' + tmp}, 'code': code.replace('(fn ' + name + ' ', '(fn ' + tmp + ' ', 1)})
    err = LOG[n0:]
    T(BT + 'remove_function_graph', {'blueprint': {'refPath': bp}, 'graph_name': tmp})
    left = [g for g in graphs_of(bp) if g not in before]
    for g in left:
        T(BT + 'remove_function_graph', {'blueprint': {'refPath': bp}, 'graph_name': g})
    return okd and not err, [e[:400] for e in err[:2]]
def compile_ok(bp):
    n0 = len(LOG)
    ok, r = T(BT + 'compile_blueprint', {'blueprint': {'refPath': bp}})
    return ok and len(LOG) == n0
def run():
    out = {}
    try:
        ok, pie = T('EditorToolset.EditorAppToolset.IsPIERunning', {})
        if pie:
            return {'err': 'PIE'}
        ok, lv = T(ST + 'get_current_level', {})
        out['level'] = lv
        for j in JOBS:
            bp = j['bp']; k = bp.split('.')[-1]; r = {}
            if j.get('vars'):
                ok, vs = T(BT + 'list_variables', {'blueprint': {'refPath': bp}})
                have = str(vs)
                added = []
                for (n, t, d, cat) in j['vars']:
                    if ("'" + n + "'") not in have:
                        if t.startswith('obj:'):
                            T(BT + 'add_object_variable', {'blueprint': {'refPath': bp}, 'name': n, 'object_class': {'refPath': t[4:]}})
                        elif t.startswith('arr:'):
                            T(BT + 'add_variable', {'blueprint': {'refPath': bp}, 'name': n, 'type_name': t[4:], 'container_type': 'Array'})
                        else:
                            T(BT + 'add_variable', {'blueprint': {'refPath': bp}, 'name': n, 'type_name': t})
                        added.append(n)
                    if cat:
                        T(BT + 'set_variable_category', {'blueprint': {'refPath': bp}, 'variable_name': n, 'category': cat})
                r['added'] = added
                T(BT + 'compile_blueprint', {'blueprint': {'refPath': bp}})
                vals = {n: d for (n, t, d, cat) in j['vars'] if d is not None}
                if vals:
                    r['cdo'] = T(OT + 'set_properties', {'instance': {'refPath': j['cdo']}, 'values': json.dumps(vals)})[0]
            res = []
            allok = True
            for (gname, code) in j.get('graphs', []):
                d = dry(bp, gname, code)
                if not d[0]:
                    allok = False
                    res.append((gname, 'DRY FAIL', d[1]))
                    continue
                if j.get('write', True):
                    mk(bp, gname)
                    clear(bp + ':' + gname)
                    w = T(BT + 'write_graph_dsl', {'graph': {'refPath': bp + ':' + gname}, 'code': code})[0]
                    res.append((gname, 'WROTE' if w else 'WRITE FAIL'))
                    allok = allok and w
                else:
                    res.append((gname, 'DRY OK'))
            r['graphs'] = res
            r['compiled'] = compile_ok(bp)
            if r['compiled'] and allok and j.get('save', True):
                r['saved'] = T(AS + 'save_assets', {'asset_paths': [j['pkg']]})[0]
            if j.get('read'):
                r['read'] = {g: str(T(BT + 'read_graph_dsl', {'graph': {'refPath': bp + ':' + g}})[1]) for g in j['read']}
            out[k] = r
    except BaseException as e:
        LOG.append('run ' + str(e)[:300])
    out['log'] = [l[:400] for l in LOG[:12]]
    T(AS + 'write_file', {'file_path': DUMP, 'content': json.dumps(out)})
    return {k: ({kk: vv for kk, vv in v.items() if kk != 'read'} if isinstance(v, dict) else v) for k, v in out.items()}
