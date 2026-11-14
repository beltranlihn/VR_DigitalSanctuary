# gen_build4.py -> build4_args.json : funciones de los widgets + actor BP_Subtitles_SC (componente, variables, datos) + ids.
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = json.load(open(os.path.join(HERE, 'subs_ue.json'), encoding='utf-8'))
S = r'''
import json
UM = 'UMGToolSet.UMGToolSet.'
OT = 'editor_toolset.toolsets.object.ObjectTools.'
BT = 'editor_toolset.toolsets.blueprint.BlueprintTools.'
AT = 'editor_toolset.toolsets.actor.ActorTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
F = '/Game/SoulCharger/Mechanics/Subtitles/'
WW = F + 'WBP_SubWord_SC.WBP_SubWord_SC'
WL = F + 'WBP_SubLine_SC.WBP_SubLine_SC'
BP = F + 'BP_Subtitles_SC.BP_Subtitles_SC'
DUMP = 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/subtitles/build4_out.json'
DATA = __DATA__
WCODE = {
 (WW, 'Setup', (('Word', 'string'),)): '(fn Setup (Word)\n  (Widget|SetText(Text) (Variables|WBP_SubWord_SC|GetT) (Utilities|Text|ToText(String) Word)))\n',
 (WL, 'Clear', ()): '(fn Clear ()\n  (Widget|Panel|ClearChildren (Variables|WBP_SubLine_SC|GetBox)))\n',
 (WL, 'AddWord', (('Word', 'string'),)): '(fn AddWord (Word)\n  (bind _w (UserInterface|CreateWidget :Class "/Game/SoulCharger/Mechanics/Subtitles/WBP_SubWord_SC.WBP_SubWord_SC_C" :OwningPlayer (Game|GetPlayerController 0)))\n  (Class|WBPSubWordSC|Setup :self _w :Word Word)\n  (Panel|AddChildtoWrapBox (Variables|WBP_SubLine_SC|GetBox) _w))\n',
 (WL, 'WordK', (('I', 'int'), ('K', 'float'), ('Dim', 'float'), ('Rise', 'float'))): '(fn WordK (I K Dim Rise)\n  (bind _c (Widget|Panel|GetChildAt (Variables|WBP_SubLine_SC|GetBox) I))\n  (Widget|SetRenderOpacity _c (+ Dim (* (- 1.0 Dim) K)))\n  (Widget|Transform|SetRenderTranslation _c (Math|Vector2D|MakeVector2D 0.0 (* (- 1.0 K) Rise))))\n',
 (WL, 'LineAlpha', (('A', 'float'),)): '(fn LineAlpha (A)\n  (Widget|SetRenderOpacity (Variables|WBP_SubLine_SC|GetBox) A))\n',
}
KNOBS = [('On', 'bool', True), ('Offset', 'Vector', {'x': 0.0, 'y': 10.0, 'z': 12.0}), ('Dim', 'float', 0.32), ('Rise', 'float', 9.0), ('WordFade', 'float', 0.16), ('LineFade', 'float', 0.22)]
ARR = [('VoIds', 'string'), ('VoC0', 'int'), ('VoCN', 'int'), ('CS', 'float'), ('CE', 'float'), ('CW0', 'int'), ('CWN', 'int'), ('Words', 'string'), ('WS', 'float')]
STATE = [('Cur', 'int', -1), ('Card', 'int', -1), ('T', 'float', 0.0), ('Was', 'bool', False), ('LastName', 'string', ''), ('Attached', 'bool', False), ('Alpha', 'float', 0.0)]
LOG = []
def T(name, payload):
    try:
        return True, execute_tool(name, json.dumps(payload))['returnValue']
    except BaseException as e:
        LOG.append(name.split('.')[-1] + ' :: ' + str(e)[:240])
        return False, None
def rp(x):
    return x['refPath'] if isinstance(x, dict) and 'refPath' in x else str(x)
def has_graph(bp, name):
    ok, gs = T(BT + 'list_graphs', {'blueprint': {'refPath': bp}})
    return (':' + name + "'") in str(gs) or (':' + name + '"') in str(gs)
def ft(g, f, n=8):
    ok, t = T(BT + 'find_node_types', {'graph': {'refPath': g}, 'type_id_filter': f, 'context_pins': []})
    return [x for x in (t or [])][:n]
def run():
    out = {}
    try:
        ok, pie = T('EditorToolset.EditorAppToolset.IsPIERunning', {})
        if pie:
            return {'err': 'PIE'}
        # ---- 1. funciones de los widgets (grafos nuevos)
        if has_graph(WL, 'ShowCard'):
            T(BT + 'remove_function_graph', {'blueprint': {'refPath': WL}, 'graph_name': 'ShowCard'})
        for (bp, fn, params), code in WCODE.items():
            if not has_graph(bp, fn):
                T(BT + 'add_function_graph', {'blueprint': {'refPath': bp}, 'graph_name': fn})
                for pn, pt in params:
                    T(BT + 'add_function_param', {'graph': {'refPath': bp + ':' + fn}, 'param_name': pn, 'param_type': pt, 'input_param': True})
        for bp in (WW, WL):
            T(UM + 'CompileWidgetBlueprint', {'widgetBlueprint': {'refPath': bp}})
        wr = {}
        for (bp, fn, params), code in WCODE.items():
            if bp == WL:
                T(UM + 'CompileWidgetBlueprint', {'widgetBlueprint': {'refPath': WW}})
            n0 = len(LOG)
            ok, w = T(BT + 'write_graph_dsl', {'graph': {'refPath': bp + ':' + fn}, 'code': code})
            wr[fn] = [ok, [e[:200] for e in LOG[n0:n0 + 1]]]
        out['widget_writes'] = wr
        for bp in (WW, WL):
            n0 = len(LOG)
            ok, cc = T(UM + 'CompileWidgetBlueprint', {'widgetBlueprint': {'refPath': bp}})
            out['wc_' + bp.split('.')[-1]] = [str(cc)[:160], LOG[n0:n0 + 1]]
        out['save_w'] = T(AS + 'save_assets', {'asset_paths': [F + 'WBP_SubWord_SC', F + 'WBP_SubLine_SC']})[0]
        # ---- 2. el actor
        ok, ex = T(AS + 'exists', {'path': F + 'BP_Subtitles_SC'})
        if not ex:
            out['create_bp'] = T(BT + 'create', {'folder_path': F, 'asset_name': 'BP_Subtitles_SC', 'asset_type': {'refPath': '/Script/Engine.Actor'}})[0]
        ok, cdo = T(BT + 'get_default_object', {'blueprint': {'refPath': BP}})
        ok, comps = T(AT + 'get_components', {'actor': cdo})
        if 'Sub' not in str(comps):
            ok, c = T(AT + 'add_component', {'owner': cdo, 'component_type': {'refPath': '/Script/UMG.WidgetComponent'}, 'name': 'Sub'})
            out['add_sub'] = [ok, rp(c) if ok else None]
        ok, comps = T(AT + 'get_components', {'actor': cdo})
        sub = None
        for c in (comps or []):
            if rp(c).endswith('Sub') or 'Sub_GEN' in rp(c) or rp(c).split('.')[-1].startswith('Sub'):
                sub = rp(c)
        out['sub'] = sub
        if sub:
            ok, pl = T(OT + 'list_properties', {'instance': {'refPath': sub}})
            pls = str(pl)
            want = ['widgetClass', 'drawSize', 'space', 'tickMode', 'pivot', 'relativeRotation', 'relativeScale3D', 'overrideMaterials', 'translucencySortPriority', 'blendMode', 'bIsTwoSided', 'castShadow', 'bManuallyRedraw', 'timingPolicy', 'geometryMode', 'bDrawAtDesiredSize']
            out['sub_has'] = [k for k in want if ('"' + k + '"') in pls or ("'" + k + "'") in pls]
            vals = {'widgetClass': {'refPath': F + 'WBP_SubLine_SC.WBP_SubLine_SC_C'}, 'drawSize': {'x': 900, 'y': 160}, 'space': 'World', 'tickMode': 'Automatic', 'pivot': {'x': 0.5, 'y': 0.5}, 'relativeRotation': {'pitch': 0.0, 'yaw': 180.0, 'roll': 0.0}, 'relativeScale3D': {'x': 0.04, 'y': 0.04, 'z': 0.04}, 'overrideMaterials': [{'refPath': '/Game/SoulCharger/Core/HUD/M_HudWidget_SC.M_HudWidget_SC'}], 'translucencySortPriority': 32720, 'blendMode': 'Transparent', 'castShadow': False}
            res = {}
            for k, v in vals.items():
                res[k] = T(OT + 'set_properties', {'instance': {'refPath': sub}, 'values': json.dumps({k: v})})[0]
            out['sub_set'] = res
        # ---- 3. variables
        ok, vs = T(BT + 'list_variables', {'blueprint': {'refPath': BP}})
        vss = str(vs)
        for n, t, d in KNOBS:
            if ("'" + n + "'") not in vss and ('"' + n + '"') not in vss:
                T(BT + 'add_variable', {'blueprint': {'refPath': BP}, 'name': ('b' + n) if t == 'bool' else n, 'type_name': t})
        for n, t in ARR:
            if ("'" + n + "'") not in vss:
                T(BT + 'add_variable', {'blueprint': {'refPath': BP}, 'name': n, 'type_name': t, 'container_type': 'Array'})
        for n, t, d in STATE:
            if ("'" + n + "'") not in vss and ("'b" + n + "'") not in vss:
                T(BT + 'add_variable', {'blueprint': {'refPath': BP}, 'name': ('b' + n) if t == 'bool' else n, 'type_name': t})
        if 'LineW' not in vss:
            T(BT + 'add_object_variable', {'blueprint': {'refPath': BP}, 'name': 'LineW', 'object_class': {'refPath': F + 'WBP_SubLine_SC.WBP_SubLine_SC_C'}})
        T(BT + 'compile_blueprint', {'blueprint': {'refPath': BP}})
        for n, t, d in KNOBS:
            vn = ('b' + n) if t == 'bool' else n
            T(BT + 'set_variable_instance_editable', {'blueprint': {'refPath': BP}, 'variable_name': vn, 'instance_editable': True})
            T(BT + 'set_variable_category', {'blueprint': {'refPath': BP}, 'variable_name': vn, 'category': 'Subtitulos'})
        for n, t in ARR:
            T(BT + 'set_variable_category', {'blueprint': {'refPath': BP}, 'variable_name': n, 'category': 'Datos'})
        T(BT + 'compile_blueprint', {'blueprint': {'refPath': BP}})
        ok, cdo = T(BT + 'get_default_object', {'blueprint': {'refPath': BP}})
        cv = {}
        for n, t, d in KNOBS:
            cv[('b' + n) if t == 'bool' else n] = d
        for n, t, d in STATE:
            cv[('b' + n) if t == 'bool' else n] = d
        out['cdo_knobs'] = T(OT + 'set_properties', {'instance': cdo, 'values': json.dumps(cv)})[0]
        dr = {}
        for n, t in ARR:
            dr[n] = T(OT + 'set_properties', {'instance': cdo, 'values': json.dumps({n: DATA[n]})})[0]
        out['cdo_data'] = dr
        ok, chk = T(OT + 'get_properties', {'instance': cdo, 'properties': ['VoIds', 'bOn', 'Offset', 'Dim', 'Cur']})
        out['cdo_check'] = str(chk)[:300]
        # ---- 4. funciones vacias del actor + ids
        for fn, params in [('SubTick', [('Dt', 'float')]), ('SubAttach', []), ('SubRef', []), ('SubStart', [('Name', 'string')]), ('SubCard', [('C', 'int')]), ('SubCards', []), ('SubDraw', [('Dt', 'float'), ('Playing', 'bool')])]:
            if not has_graph(BP, fn):
                T(BT + 'add_function_graph', {'blueprint': {'refPath': BP}, 'graph_name': fn})
                for pn, pt in params:
                    T(BT + 'add_function_param', {'graph': {'refPath': BP + ':' + fn}, 'param_name': pn, 'param_type': pt, 'input_param': True})
        T(BT + 'compile_blueprint', {'blueprint': {'refPath': BP}})
        g = BP + ':SubTick'
        ids = {}
        for f in ['IsPlaying', 'GetSound', 'GetVOComp', 'FindItem', 'GetUserWidgetObject', 'CastToWBP_SubLine_SC', 'AttachActorToActor', 'SetActorRelativeLocation', 'Clamp(Float)', 'GetObjectName', 'EqualExactly(String)', 'WBPSubLineSC|', 'GetSub', 'Variables|Subtitulos|Get', 'Variables|Datos|Get', 'SetVisibility']:
            ids[f] = ft(g, f, 14)
        out['ids'] = ids
        n0 = len(LOG)
        ok, cc = T(BT + 'compile_blueprint', {'blueprint': {'refPath': BP}})
        out['compile_bp'] = [ok, LOG[n0:n0 + 1]]
        out['save_bp'] = T(AS + 'save_assets', {'asset_paths': [F + 'BP_Subtitles_SC']})[0]
    except BaseException as e:
        LOG.append('run ' + str(e)[:200])
    out['log'] = [l[:240] for l in LOG[:10]]
    T(AS + 'write_file', {'file_path': DUMP, 'content': json.dumps(out)})
    return {'keys': list(out.keys()), 'nlog': len(LOG)}
'''
S = S.replace('__DATA__', json.dumps(DATA, ensure_ascii=True))
import ast; ast.parse(S)
open(os.path.join(HERE, 'build4.py'), 'w', encoding='utf-8').write(S)
open(os.path.join(HERE, 'build4_args.json'), 'w', encoding='utf-8').write(json.dumps({'script': S}))
print('ok', len(S))
