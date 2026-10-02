import json, ast
NL = chr(10)
def L(*xs):
    return NL.join(xs) + NL
UNUSED = ['Fired', 'InitHidden', 'LevelOuter', 'HallWait', 'ReturnWait', 'ExitWait', 'DbgShot', 'ResRingScale', 'RingSide', 'ShareDrop', 'SketchYaw']
CAT = {
    'Config': ['bDisclaimer', 'bSimulated'],
    'Debug': ['Speed', 'bPhotos', 'bDebugEnding', 'DebugShare', 'DbgDrawSynth', 'DbgK', 'DbgS', 'DbgHallStep', 'LastShot'],
    'Partitura': ['DiscTime', 'ChargeTimes', 'ExploreT', 'ShareFW', 'ResultsTime', 'SwimTime', 'AwayTime', 'CreditsTime', 'SimStageMax', 'AlmaTime', 'InstrTime', 'OutroTime'],
    'Etapas': ['LevelPaths', 'LevelNames', 'StageNames', 'StartLoc', 'StartYaw', 'CTops', 'CHors', 'StageCols', 'CavNames', 'TitleMIs', 'TpIn', 'TpSide', 'TpCharge', 'TpTitle', 'StAlma', 'StInstr', 'StOutro'],
    'Final': ['SoulSpot', 'RingSpot', 'DoorPt', 'AwayPt', 'RingRoll'],
}
NOT_IE = CAT['Partitura'] + CAT['Etapas'] + ['LastShot', 'DbgK', 'DbgS', 'DbgHallStep']
def app(*xs):
    e = xs[0]
    for x in xs[1:]:
        e = '(Utilities|String|Append %s %s)' % (e, x)
    return e
CFG = app('"OBRA CONFIG: Speed="', '(Utilities|String|ToString(Float) (Variables|Debug|GetSpeed))',
          '" Simulated="', '(Utilities|String|ToString(Boolean) (Variables|Config|GetSimulated))',
          '" Disclaimer="', '(Utilities|String|ToString(Boolean) (Variables|Config|GetDisclaimer))',
          '" DebugStart="', '(Utilities|String|ToString(Integer) (Variables|Debug|GetDebugStart))',
          '" DebugShare="', '(Utilities|String|ToString(Integer) (Variables|Debug|GetDebugShare))',
          '" DbgDrawSynth="', '(Utilities|String|ToString(Boolean) (Variables|Debug|GetDbgDrawSynth))',
          '" Photos="', '(Utilities|String|ToString(Boolean) (Variables|Debug|GetPhotos))',
          '" DebugEnding="', '(Utilities|String|ToString(Boolean) (Variables|Debug|GetDebugEnding))')
CMD = L('(fn ObraCmdLine ()',
        '  (bind _cmd (Utilities|GetCommandLine))',
        '  (bind (_val _found) (Utilities|ParseParamValue _cmd "ObraSpeed="))',
        '  (if _found',
        '    (Variables|Debug|SetSpeed (Utilities|String|StringToFloat _val))',
        '    (Development|PrintString (Utilities|String|Append "OBRA: Speed por linea de comandos = " _val) false))',
        '  (if (Utilities|ParseParam _cmd "ObraSmoke")',
        '    (Variables|Debug|SetSmoke true)',
        '    (Variables|Config|SetDisclaimer false)',
        '    (Variables|Config|SetSimulated true)',
        '    (Variables|Debug|SetDebugStart -1)',
        '    (Development|PrintString "OBRA SMOKE: modo prueba de humo (sin aviso, datos simulados, arranque normal)" false))',
        '  (bind (_val2 _found2) (Utilities|ParseParamValue _cmd "ObraStart="))',
        '  (if _found2',
        '    (Variables|Debug|SetDebugStart (Utilities|String|ToInteger(String) _val2))',
        '    (Development|PrintString (Utilities|String|Append "OBRA: DebugStart por linea de comandos = " _val2) false))',
        '  (Development|PrintString %s false)' % CFG,
        '  (if (or (!= (Variables|Debug|GetSpeed) 1.0) (or (>= (Variables|Debug|GetDebugStart) 1) (or (Variables|Debug|GetDbgDrawSynth) (or (Variables|Debug|GetPhotos) (or (Variables|Debug|GetDebugEnding) (!= (Variables|Debug|GetDebugShare) -1))))))',
        '    (Development|PrintString "OBRA CONFIG: ATENCION - hay perillas de prueba encendidas: esto NO es un build de publico" false)))')
TAIL = '''
OB = '/Game/SoulCharger/Obra/BP_Obra_SC.BP_Obra_SC'
UNUSED = %r
CAT = %r
NOT_IE = %r
CMD = %r
REPORT_CODE = None
def run():
    out = {}
    try:
        lv = T(ST + 'get_current_level', {})[1]
        if 'Test_QuestCtrl' not in str(lv):
            return {'err': 'nivel no neutro', 'level': lv}
        ok, vs = T(BT + 'list_variables', {'blueprint': {'refPath': OB}})
        names = [v['name'] if isinstance(v, dict) and 'name' in v else str(v) for v in (vs or [])]
        out['n_before'] = len(names)
        rm = []
        for n in UNUSED:
            if n in names:
                rm.append((n, T(BT + 'remove_variable', {'blueprint': {'refPath': OB}, 'name': n})[0]))
        out['removed'] = rm
        T(BT + 'compile_blueprint', {'blueprint': {'refPath': OB}})
        assigned = {}
        for c in CAT:
            for n in CAT[c]:
                assigned[n] = c
        moved = 0
        interno = 0
        for n in names:
            if n in UNUSED:
                continue
            ok, cur = T(BT + 'get_variable_category', {'blueprint': {'refPath': OB}, 'variable_name': n})
            cur = str(cur)
            if n in assigned:
                if cur != assigned[n]:
                    T(BT + 'set_variable_category', {'blueprint': {'refPath': OB}, 'variable_name': n, 'category': assigned[n]})
                    moved += 1
            elif cur in ('Default', 'None', ''):
                T(BT + 'set_variable_category', {'blueprint': {'refPath': OB}, 'variable_name': n, 'category': 'Interno'})
                interno += 1
        out['moved'] = moved
        out['to_interno'] = interno
        for n in NOT_IE:
            T(BT + 'set_variable_instance_editable', {'blueprint': {'refPath': OB}, 'variable_name': n, 'instance_editable': False})
        out['compiled1'] = compile_ok(OB)
        out['cmd'] = write_graph(OB, 'ObraCmdLine', CMD)
        out['compiled2'] = compile_ok(OB)
        if out['compiled2']:
            out['saved'] = T(AS + 'save_assets', {'asset_paths': ['/Game/SoulCharger/Obra/BP_Obra_SC']})[0]
        ok, vs2 = T(BT + 'list_variables', {'blueprint': {'refPath': OB}})
        out['n_after'] = len(vs2 or [])
        cats = {}
        for v in (vs2 or []):
            n = v['name'] if isinstance(v, dict) and 'name' in v else str(v)
            c = str(T(BT + 'get_variable_category', {'blueprint': {'refPath': OB}, 'variable_name': n})[1])
            cats[c] = G(cats, c, 0) + 1
        out['cats'] = cats
    except BaseException as e:
        LOG.append('run ' + str(e)[:300])
    out['log'] = [l[:400] for l in LOG[:10]]
    return out
''' % (UNUSED, CAT, NOT_IE, CMD)
lib = open('surg_lib.py', encoding='utf-8').read()
i = lib.index('def node_map(')
j = lib.index('def add_vars(')
body = lib[:i] + lib[j:] + TAIL
ast.parse(body)
open('job_obraorden.json', 'w', encoding='utf-8').write(json.dumps({'script': body}))
print(len(body))
