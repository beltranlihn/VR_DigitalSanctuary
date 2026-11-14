
import json
OT = 'editor_toolset.toolsets.object.ObjectTools.'
BT = 'editor_toolset.toolsets.blueprint.BlueprintTools.'
AT = 'editor_toolset.toolsets.actor.ActorTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
F = '/Game/SoulCharger/Mechanics/Subtitles/'
BP = F + 'BP_Subtitles_SC.BP_Subtitles_SC'
DUMP = 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/subtitles/build5_out.json'
CODES = {'SubRef': '(fn SubRef ()\n  (Utilities|IsValid (Variables|Default|GetLineW)\n    (:"Is Not Valid"\n      (bind _lw (Utilities|Casting|CastToWBP_SubLine_SC :Object (UserInterface|GetUserWidgetObject (Variables|Default|GetSub)))\n        (:then (Variables|Default|SetLineW _aswbp_sub_line_sc))\n        (:CastFailed)))))\n', 'SubAttach': '(fn SubAttach ()\n  (bind _h (Actor|GetActorOfClass "/Game/SoulCharger/Mechanics/HUD/BP_SoulHUD3D_SC.BP_SoulHUD3D_SC_C"))\n  (if (not (Variables|Default|GetAttached))\n    (Utilities|IsValid _h\n      (:"Is Valid"\n        (Transformation|AttachActorToActor :ParentActor _h :LocationRule "SnapToTarget" :RotationRule "SnapToTarget" :ScaleRule "KeepWorld" :bWeldSimulatedBodies false)\n        (Transformation|SetActorRelativeLocation :NewRelativeLocation (Variables|Subtitulos|GetOffset) :bSweep false :bTeleport false)\n        (Variables|Default|SetAttached true)\n        (Development|PrintString "SUBS: subtitulos colgados del HUD" false)))))\n', 'SubStart': '(fn SubStart (Name)\n  (Variables|Default|SetCur (Utilities|Array|FindItem (Variables|Datos|GetVoIds) Name))\n  (Variables|Default|SetCard -1)\n  (Variables|Default|SetT 0.0)\n  (Variables|Default|SetLastName Name)\n  (Development|PrintString (Utilities|String|Append "SUBS: " Name) false))\n', 'SubCard': '(fn SubCard (C)\n  (Variables|Default|SetCard C)\n  (Class|WBPSubLineSC|Clear :self (Variables|Default|GetLineW))\n  (for _i (range (Utilities|Array|Get(acopy) (Variables|Datos|GetCWN) C))\n    (Class|WBPSubLineSC|AddWord :self (Variables|Default|GetLineW) :Word (Utilities|Array|Get(acopy) (Variables|Datos|GetWords) (+ (Utilities|Array|Get(acopy) (Variables|Datos|GetCW0) C) _i)))))\n', 'SubCards': '(fn SubCards ()\n  (bind _c0 (Utilities|Array|Get(acopy) (Variables|Datos|GetVoC0) (Variables|Default|GetCur)))\n  (for _i (range (Utilities|Array|Get(acopy) (Variables|Datos|GetVoCN) (Variables|Default|GetCur)))\n    (if (and (>= (Variables|Default|GetT) (Utilities|Array|Get(acopy) (Variables|Datos|GetCS) (+ _c0 _i))) (and (< (Variables|Default|GetT) (Utilities|Array|Get(acopy) (Variables|Datos|GetCE) (+ _c0 _i))) (not (== (Variables|Default|GetCard) (+ _c0 _i)))))\n      (CallFunction|SubCard :C (+ _c0 _i)))))\n', 'SubDraw': '(fn SubDraw (Dt Playing)\n  (bind _cd (Variables|Default|GetCard))\n  (bind _t (Variables|Default|GetT))\n  (bind _lf (Math|Float|Max(Float) (Variables|Subtitulos|GetLineFade) 0.01))\n  (Variables|Default|SetAlpha (Math|Float|Clamp(Float) (+ (Variables|Default|GetAlpha) (* Dt (select (and Playing (Variables|Subtitulos|GetOn)) 5.0 -5.0))) 0.0 1.0))\n  (if (and (>= (Variables|Default|GetCur) 0) (>= _cd 0))\n    (bind _a (* (Variables|Default|GetAlpha) (Math|Float|Min(Float) (Math|Float|Clamp(Float) (/ (- _t (Utilities|Array|Get(acopy) (Variables|Datos|GetCS) _cd)) _lf) 0.0 1.0) (Math|Float|Clamp(Float) (/ (- (Utilities|Array|Get(acopy) (Variables|Datos|GetCE) _cd) _t) _lf) 0.0 1.0))))\n    (Class|WBPSubLineSC|LineAlpha :self (Variables|Default|GetLineW) :A _a)\n    (Rendering|SetVisibility (Variables|Default|GetSub) (> _a 0.002))\n    (for _i (range (Utilities|Array|Get(acopy) (Variables|Datos|GetCWN) _cd))\n      (bind _k (Math|Float|Clamp(Float) (/ (- _t (Utilities|Array|Get(acopy) (Variables|Datos|GetWS) (+ (Utilities|Array|Get(acopy) (Variables|Datos|GetCW0) _cd) _i))) (Math|Float|Max(Float) (Variables|Subtitulos|GetWordFade) 0.01)) 0.0 1.0))\n      (Class|WBPSubLineSC|WordK :self (Variables|Default|GetLineW) :I _i :K (* _k (* _k (- 3.0 (* 2.0 _k)))) :Dim (Variables|Subtitulos|GetDim) :Rise (Variables|Subtitulos|GetRise)))\n    (else\n      (Rendering|SetVisibility (Variables|Default|GetSub) false))))\n', 'SubAudio': '(fn SubAudio (Dt)\n  (bind _al (Actor|GetActorOfClass "/Game/SoulCharger/Core/Alma/BP_Alma_SC.BP_Alma_SC_C"))\n  (Utilities|IsValid _al\n    (:"Is Valid"\n      (Utilities|IsValid (Variables|Default|GetLineW)\n        (:"Is Valid"\n          (bind _vc (Class|BPAlmaSC|GetVOComp :self _al))\n          (bind _pl (Audio|Components|Audio|IsPlaying _vc))\n          (bind _nm (Utilities|GetObjectName (Class|AudioComponent|GetSound :self _vc)))\n          (if (and _pl (or (not (Variables|Default|GetWas)) (not (Utilities|String|EqualExactly(String) _nm (Variables|Default|GetLastName)))))\n            (CallFunction|SubStart :Name _nm))\n          (Variables|Default|SetWas _pl)\n          (if (>= (Variables|Default|GetCur) 0)\n            (Variables|Default|SetT (+ (Variables|Default|GetT) Dt))\n            (CallFunction|SubCards))\n          (CallFunction|SubDraw :Dt Dt :Playing _pl))))))\n', 'SubTick': '(fn SubTick (Dt)\n  (CallFunction|SubRef)\n  (CallFunction|SubAttach)\n  (CallFunction|SubAudio :Dt Dt))\n'}
PARAMS = {'SubAudio': [('Dt', 'float')], 'SubTick': [('Dt', 'float')], 'SubStart': [('Name', 'string')], 'SubCard': [('C', 'int')], 'SubDraw': [('Dt', 'float'), ('Playing', 'bool')]}
ORDER = ['SubRef', 'SubAttach', 'SubStart', 'SubCard', 'SubCards', 'SubDraw', 'SubAudio', 'SubTick']
EVG = '(event EventTick (DeltaSeconds)\n  (CallFunction|SubTick :Dt DeltaSeconds))\n'
LOG = []
def T(name, payload):
    try:
        return True, execute_tool(name, json.dumps(payload))['returnValue']
    except BaseException as e:
        LOG.append(name.split('.')[-1] + ' :: ' + str(e)[:260])
        return False, None
def rp(x):
    return x['refPath'] if isinstance(x, dict) and 'refPath' in x else str(x)
def has_graph(name):
    ok, gs = T(BT + 'list_graphs', {'blueprint': {'refPath': BP}})
    return (':' + name + "'") in str(gs) or (':' + name + '"') in str(gs)
def mk(name, params):
    if has_graph(name):
        return
    T(BT + 'add_function_graph', {'blueprint': {'refPath': BP}, 'graph_name': name})
    for pn, pt in params:
        T(BT + 'add_function_param', {'graph': {'refPath': BP + ':' + name}, 'param_name': pn, 'param_type': pt, 'input_param': True})
def clear(g):
    ok, ns = T(BT + 'find_nodes', {'graph': {'refPath': g}, 'title': ''})
    for n in (ns or []):
        r = rp(n)
        if 'FunctionEntry' not in r:
            T(BT + 'delete_node', {'node': {'refPath': r}})
def run():
    out = {}
    try:
        ok, pie = T('EditorToolset.EditorAppToolset.IsPIERunning', {})
        if pie:
            return {'err': 'PIE'}
        ok, cdo = T(BT + 'get_default_object', {'blueprint': {'refPath': BP}})
        ok, comps = T(AT + 'get_components', {'actor': cdo})
        names = [rp(c).split('.')[-1] for c in (comps or [])]
        out['comps_before'] = names
        if not [n for n in names if n == 'Sub' or n.startswith('Sub_')]:
            ok, c = T(AT + 'add_component', {'owner': cdo, 'component_type': {'refPath': '/Script/UMG.WidgetComponent'}, 'name': 'Sub'})
            out['add_sub'] = [ok, rp(c) if ok else None]
        ok, comps = T(AT + 'get_components', {'actor': cdo})
        sub = None
        for c in (comps or []):
            n = rp(c).split('.')[-1]
            if n == 'Sub' or n.startswith('Sub_'):
                sub = rp(c)
        out['sub'] = sub
        if sub:
            vals = {'widgetClass': {'refPath': F + 'WBP_SubLine_SC.WBP_SubLine_SC_C'}, 'drawSize': {'x': 900, 'y': 160}, 'space': 'World', 'tickMode': 'Automatic', 'pivot': {'x': 0.5, 'y': 0.5}, 'relativeRotation': {'pitch': 0.0, 'yaw': 180.0, 'roll': 0.0}, 'relativeScale3D': {'x': 0.04, 'y': 0.04, 'z': 0.04}, 'overrideMaterials': [{'refPath': '/Game/SoulCharger/Core/HUD/M_HudWidget_SC.M_HudWidget_SC'}], 'translucencySortPriority': 32720, 'blendMode': 'Transparent', 'castShadow': False}
            res = {}
            for k, v in vals.items():
                res[k] = T(OT + 'set_properties', {'instance': {'refPath': sub}, 'values': json.dumps({k: v})})[0]
            out['sub_set'] = res
            ok, chk = T(OT + 'get_properties', {'instance': {'refPath': sub}, 'properties': ['widgetClass', 'drawSize', 'space', 'tickMode', 'relativeScale3D', 'overrideMaterials', 'translucencySortPriority', 'blendMode']})
            out['sub_chk'] = str(chk)[:600]
        if not has_graph('SubAudio'):
            mk('SubAudio', PARAMS['SubAudio'])
        T(BT + 'compile_blueprint', {'blueprint': {'refPath': BP}})
        wr = {}
        for n in ORDER:
            clear(BP + ':' + n)
            n0 = len(LOG)
            ok, w = T(BT + 'write_graph_dsl', {'graph': {'refPath': BP + ':' + n}, 'code': CODES[n]})
            wr[n] = [ok, [e[:260] for e in LOG[n0:n0 + 1]]]
            T(BT + 'compile_blueprint', {'blueprint': {'refPath': BP}})
        out['writes'] = wr
        clear(BP + ':EventGraph')
        n0 = len(LOG)
        ok, w = T(BT + 'write_graph_dsl', {'graph': {'refPath': BP + ':EventGraph'}, 'code': EVG})
        out['w_evg'] = [ok, [e[:260] for e in LOG[n0:n0 + 1]]]
        n0 = len(LOG)
        ok, cc = T(BT + 'compile_blueprint', {'blueprint': {'refPath': BP}})
        out['compile'] = [ok, LOG[n0:n0 + 1]]
        rd = {}
        for n in ['SubCard', 'SubAudio', 'EventGraph', 'SubRef']:
            ok, s = T(BT + 'read_graph_dsl', {'graph': {'refPath': BP + ':' + n}})
            rd[n] = str(s)[:1600]
        out['reads'] = rd
        if out['compile'][0] and not out['compile'][1]:
            out['save'] = T(AS + 'save_assets', {'asset_paths': [F + 'BP_Subtitles_SC']})[0]
    except BaseException as e:
        LOG.append('run ' + str(e)[:200])
    out['log'] = [l[:260] for l in LOG[:10]]
    T(AS + 'write_file', {'file_path': DUMP, 'content': json.dumps(out)})
    return {'sub': out.get('sub'), 'writes': {k: v[0] for k, v in out.get('writes', {}).items()}, 'evg': out.get('w_evg', [None])[0], 'compile': out.get('compile'), 'save': out.get('save'), 'nlog': len(LOG)}
