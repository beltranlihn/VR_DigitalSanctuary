# gen_build5.py -> build5_args.json : componente Sub + los grafos del actor BP_Subtitles_SC
import json, os, ast
HERE = os.path.dirname(os.path.abspath(__file__))
ALMA = '/Game/SoulCharger/Core/Alma/BP_Alma_SC.BP_Alma_SC_C'
HUD = '/Game/SoulCharger/Mechanics/HUD/BP_SoulHUD3D_SC.BP_SoulHUD3D_SC_C'
G = lambda arr, i: '(Utilities|Array|Get(acopy) (Variables|Datos|Get%s) %s)' % (arr, i)
LW = '(Variables|Default|GetLineW)'
CODES = {
'SubRef': '''(fn SubRef ()
  (Utilities|IsValid %s
    (:"Is Not Valid"
      (bind _lw (Utilities|Casting|CastToWBP_SubLine_SC :Object (UserInterface|GetUserWidgetObject (Variables|Default|GetSub)))
        (:then (Variables|Default|SetLineW _aswbp_sub_line_sc))
        (:CastFailed)))))
''' % LW,
'SubAttach': '''(fn SubAttach ()
  (bind _h (Actor|GetActorOfClass "%s"))
  (if (not (Variables|Default|GetAttached))
    (Utilities|IsValid _h
      (:"Is Valid"
        (Transformation|AttachActorToActor :ParentActor _h :LocationRule "SnapToTarget" :RotationRule "SnapToTarget" :ScaleRule "KeepWorld" :bWeldSimulatedBodies false)
        (Transformation|SetActorRelativeLocation :NewRelativeLocation (Variables|Subtitulos|GetOffset) :bSweep false :bTeleport false)
        (Variables|Default|SetAttached true)
        (Development|PrintString "SUBS: subtitulos colgados del HUD" false)))))
''' % HUD,
'SubStart': '''(fn SubStart (Name)
  (Variables|Default|SetCur (Utilities|Array|FindItem (Variables|Datos|GetVoIds) Name))
  (Variables|Default|SetCard -1)
  (Variables|Default|SetT 0.0)
  (Variables|Default|SetLastName Name)
  (Development|PrintString (Utilities|String|Append "SUBS: " Name) false))
''',
'SubCard': '''(fn SubCard (C)
  (Variables|Default|SetCard C)
  (Class|WBPSubLineSC|Clear :self %s)
  (for _i (range %s)
    (Class|WBPSubLineSC|AddWord :self %s :Word %s)))
''' % (LW, G('CWN', 'C'), LW, G('Words', '(+ %s _i)' % G('CW0', 'C'))),
'SubCards': '''(fn SubCards ()
  (bind _c0 %s)
  (for _i (range %s)
    (if (and (>= (Variables|Default|GetT) %s) (and (< (Variables|Default|GetT) %s) (not (== (Variables|Default|GetCard) (+ _c0 _i)))))
      (CallFunction|SubCard :C (+ _c0 _i)))))
''' % (G('VoC0', '(Variables|Default|GetCur)'), G('VoCN', '(Variables|Default|GetCur)'), G('CS', '(+ _c0 _i)'), G('CE', '(+ _c0 _i)')),
'SubDraw': '''(fn SubDraw (Dt Playing)
  (bind _cd (Variables|Default|GetCard))
  (bind _t (Variables|Default|GetT))
  (bind _lf (Math|Float|Max(Float) (Variables|Subtitulos|GetLineFade) 0.01))
  (Variables|Default|SetAlpha (Math|Float|Clamp(Float) (+ (Variables|Default|GetAlpha) (* Dt (select (and Playing (Variables|Subtitulos|GetOn)) 5.0 -5.0))) 0.0 1.0))
  (if (and (>= (Variables|Default|GetCur) 0) (>= _cd 0))
    (bind _a (* (Variables|Default|GetAlpha) (Math|Float|Min(Float) (Math|Float|Clamp(Float) (/ (- _t %s) _lf) 0.0 1.0) (Math|Float|Clamp(Float) (/ (- %s _t) _lf) 0.0 1.0))))
    (Class|WBPSubLineSC|LineAlpha :self %s :A _a)
    (Rendering|SetVisibility (Variables|Default|GetSub) (> _a 0.002))
    (for _i (range %s)
      (bind _k (Math|Float|Clamp(Float) (/ (- _t %s) (Math|Float|Max(Float) (Variables|Subtitulos|GetWordFade) 0.01)) 0.0 1.0))
      (Class|WBPSubLineSC|WordK :self %s :I _i :K (* _k (* _k (- 3.0 (* 2.0 _k)))) :Dim (Variables|Subtitulos|GetDim) :Rise (Variables|Subtitulos|GetRise)))
    (else
      (Rendering|SetVisibility (Variables|Default|GetSub) false))))
''' % (G('CS', '_cd'), G('CE', '_cd'), LW, G('CWN', '_cd'), G('WS', '(+ %s _i)' % G('CW0', '_cd')), LW),
'SubAudio': '''(fn SubAudio (Dt)
  (bind _al (Actor|GetActorOfClass "%s"))
  (Utilities|IsValid _al
    (:"Is Valid"
      (Utilities|IsValid %s
        (:"Is Valid"
          (bind _vc (Class|BPAlmaSC|GetVOComp :self _al))
          (bind _pl (Audio|Components|Audio|IsPlaying _vc))
          (bind _nm (Utilities|GetObjectName (Class|AudioComponent|GetSound :self _vc)))
          (if (and _pl (or (not (Variables|Default|GetWas)) (not (Utilities|String|EqualExactly(String) _nm (Variables|Default|GetLastName)))))
            (CallFunction|SubStart :Name _nm))
          (Variables|Default|SetWas _pl)
          (if (>= (Variables|Default|GetCur) 0)
            (Variables|Default|SetT (+ (Variables|Default|GetT) Dt))
            (CallFunction|SubCards))
          (CallFunction|SubDraw :Dt Dt :Playing _pl))))))
''' % (ALMA, LW),
'SubTick': '''(fn SubTick (Dt)
  (CallFunction|SubRef)
  (CallFunction|SubAttach)
  (CallFunction|SubAudio :Dt Dt))
''',
}
PARAMS = {'SubAudio': [('Dt', 'float')], 'SubTick': [('Dt', 'float')], 'SubStart': [('Name', 'string')], 'SubCard': [('C', 'int')], 'SubDraw': [('Dt', 'float'), ('Playing', 'bool')]}
ORDER = ['SubRef', 'SubAttach', 'SubStart', 'SubCard', 'SubCards', 'SubDraw', 'SubAudio', 'SubTick']
EVG = '(event EventTick (DeltaSeconds)\n  (CallFunction|SubTick :Dt DeltaSeconds))\n'
S = r'''
import json
OT = 'editor_toolset.toolsets.object.ObjectTools.'
BT = 'editor_toolset.toolsets.blueprint.BlueprintTools.'
AT = 'editor_toolset.toolsets.actor.ActorTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
F = '/Game/SoulCharger/Mechanics/Subtitles/'
BP = F + 'BP_Subtitles_SC.BP_Subtitles_SC'
DUMP = 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/subtitles/build5_out.json'
CODES = __CODES__
PARAMS = __PARAMS__
ORDER = __ORDER__
EVG = __EVG__
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
'''
S = S.replace('__CODES__', repr(CODES)).replace('__PARAMS__', repr(PARAMS)).replace('__ORDER__', repr(ORDER)).replace('__EVG__', repr(EVG))
ast.parse(S)
open(os.path.join(HERE, 'build5.py'), 'w', encoding='utf-8').write(S)
open(os.path.join(HERE, 'build5_args.json'), 'w', encoding='utf-8').write(json.dumps({'script': S}))
print('ok', len(S))
