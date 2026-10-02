import json, ast, sys
sys.path.insert(0, r"C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/tools/unreal")
import importlib, partitura_def
importlib.reload(partitura_def)
P = partitura_def.P
MAPPED = {'Aviso_Dur': 'DiscTime', 'Carga_Dur': 'ChargeTimes', 'Res_Explorar': 'ExploreT', 'Res_Cortafuegos': 'ShareFW', 'Res_Tope': 'ResultsTime',
          'Comp_Nado': 'SwimTime', 'Comp_Lejos': 'AwayTime', 'Creditos_Dur': 'CreditsTime', 'Sim_EtapaMax': 'SimStageMax'}
NL = chr(10)
DN = lambda n: n.replace('_', '')
PG = '(Class|BPPartituraSC|Get%s _p)'
lines = []
for (n, t, v, c, d) in P:
    tgt = ('Variables|Default|Set' + MAPPED[n]) if n in MAPPED else ('Variables|Partitura|Set' + DN(n))
    lines.append('      (%s %s)' % (tgt, PG % DN(n)))
lines.append('      (Variables|Partitura|SetVeloCierreFinT (+ 69.0 %s))' % (PG % 'VeloCierreDur'))
lines.append('      (Variables|Partitura|SetFinalNegroIniPT (- (+ 5.5 (Utilities|Array|Get(acopy) %s 4)) %s))' % (PG % 'CargaDur', PG % 'FinalNegroRampa'))
lines.append('      (Variables|Partitura|SetHallVeloGuarda (+ %s 0.5))' % (PG % 'HallVeloAbreFin'))
lines.append('      (Development|PrintString "OBRA: partitura cargada (DA_Partitura_Obra)" false))')
def L(*xs):
    return NL.join(xs) + NL
LOAD = L('(fn LoadPartitura ()', '  (bind _p (Variables|Partitura|GetPartitura))', '  (Utilities|IsValid _p', '    (:"Is Valid"') + NL.join(lines) + NL + L(
    '    (:"Is Not Valid"', '      (Development|PrintString "OBRA: ATENCION - sin partitura (DA_Partitura_Obra): quedan los valores por defecto del Blueprint" false))))')
STAGETIMES = L('(fn StageTimes (K)',
               '  (Variables|Default|SetInstrTime (Utilities|Array|Get(acopy) (Variables|Partitura|GetInstrDur) K))',
               '  (Variables|Default|SetOutroTime (Utilities|Array|Get(acopy) (Variables|Partitura|GetSalidaDur) K))',
               '  (Variables|Partitura|SetEtapaTopeK (+ (Utilities|Array|Get(acopy) (Variables|Partitura|GetEtapaTope) K) (Variables|Partitura|GetCorteEspera)))',
               '  (Variables|Default|SetAlmaTime (+ (Variables|Default|GetVODur) (Variables|Partitura|GetAlmaTrasVoz))))')
BRE = '/Game/SoulCharger/Mechanics/Breath/BP_BreathStage_SC.BP_BreathStage_SC_C'
HRT = '/Game/SoulCharger/Mechanics/Heart/BP_HeartManager_SC.BP_HeartManager_SC_C'
LOV = '/Game/SoulCharger/Mechanics/Loving/BP_LovingCell_SC.BP_LovingCell_SC_C'
SEQ = '/Game/SoulCharger/Core/Attracting/BP_Sequencer_SC.BP_Sequencer_SC_C'
TBC = '/Game/NeuralCanvas/TB/BP_TBDirector_NC.BP_TBDirector_NC_C'
REQ = L('(fn RequestEnd (K)',
        '  (switch Utilities|FlowControl|Switch|SwitchonInt K',
        '    (:0', '      (Class|BPBreathStageSC|StageRequestEnd :self (Actor|GetActorOfClass "%s")))' % BRE,
        '    (:1', '      (Class|BPHeartManagerSC|StageRequestEnd :self (Actor|GetActorOfClass "%s")))' % HRT,
        '    (:2', '      (Class|BPLovingCellSC|StageRequestEnd :self (Actor|GetActorOfClass "%s")))' % LOV,
        '    (:3', '      (Class|BPSequencerSC|StageRequestEnd :self (Actor|GetActorOfClass "%s")))' % SEQ,
        '    (:4', '      (Class|BPTBDirectorNC|StageRequestEnd :self (Actor|GetActorOfClass "%s")))))' % TBC)
def SRE_SIMPLE(tag):
    return L('(fn StageRequestEnd ()',
             '  (Development|PrintString "%s: la Obra pide cerrar la etapa - queda lista (bStageDone)" false)' % tag,
             '  (Variables|Default|SetStageDone true))')
SRE_SEQ = L('(fn StageRequestEnd ()',
            '  (CallFunction|ResultsCountOcc)',
            '  (if (and (== (Variables|Z-Estado|GetPhase) 2) (> (Variables|Z-Estado|GetResUserOrbs) 0))',
            '    (Development|PrintString "SEQ: la Obra pide cerrar la etapa - se guarda la melodia (SAVE)" false)',
            '    (CallFunction|SaveMelody)',
            '    (else',
            '      (Development|PrintString "SEQ: la Obra pide cerrar la etapa - sin melodia: queda lista (bStageDone)" false)',
            '      (Variables|Default|SetStageDone true))))')
SRE_TB = L('(fn StageRequestEnd ()', '  (CallFunction|TimeUp))')
CORTES = L('(fn EtapaCortes ()',
           '  (bind _ph (Variables|Default|GetPhase))',
           '  (bind _st (Variables|Default|GetStage))',
           '  (bind _pt (Variables|Default|GetPT))',
           '  (if (not (== _ph 6))',
           '    (Variables|Interno|SetCortePedido false))',
           '  (if (and (== _ph 6) (and (not (Variables|Interno|GetCortePedido)) (>= _pt (select (and (Variables|Default|GetSimulated) (>= _st 3)) (Variables|Default|GetSimStageMax) (Utilities|Array|Get(acopy) (Variables|Partitura|GetEtapaTope) _st)))))',
           '    (Variables|Interno|SetCortePedido true)',
           '    (Variables|Interno|SetCorteAt _pt)',
           '    (Variables|Partitura|SetEtapaTopeK (+ _pt (Variables|Partitura|GetCorteEspera)))',
           '    (Development|PrintString (Utilities|String|Append (Utilities|String|Append "OBRA: se acabo el tiempo de la etapa " (Utilities|String|ToString(Integer) _st)) " - se le pide que cierre por su propio camino") false)',
           '    (CallFunction|RequestEnd :K _st)))')
SIMCUT = L('(fn SimCut ()',
           '  (CallFunction|EtapaCortes)',
           '  (if (and (Variables|Default|GetDbgDrawSynth) (and (== (Variables|Default|GetPhase) 6) (and (== (Variables|Default|GetStage) 4) (>= (Variables|Default|GetPT) 2.0))))',
           '    (Variables|Default|SetDbgDrawSynth false)',
           '    (Class|BPTBDirectorNC|DbgSynth :self (Actor|GetActorOfClass "%s")))' % TBC,
           '  (CallFunction|SmokeTick)',
           '  (CallFunction|ObraDbgFF))')
TIMEUP = L('(fn TimeUp ()',
           '  (bind _self self)',
           '  (bind _tbtool (Variables|Default|GetTBTool))',
           '  (Utilities|IsValid _tbtool',
           '    (:"Is Valid"',
           '      (if (> (Utilities|Array|Length (Class|BPCTBToolNC|GetStrokeHistory _tbtool)) 0)',
           '        (Variables|Z-Tinta|SetInkUsed (Math|Float|Max(Float) (Variables|Z-Tinta|GetInkUsed) (Variables|10TINTA|GetInkMeters)))',
           '        (Development|PrintString "TB: se acabo el tiempo - se guarda el dibujo y se presenta" false)',
           '        (CallFunction|InkEnd _self)',
           '        (else',
           '          (Development|PrintString "TB: se acabo el tiempo sin dibujo - queda lista para cerrar (bStageDone)" false)',
           '          (Variables|Default|SetStageDone true))))',
           '    (:"Is Not Valid"',
           '      (Variables|Default|SetStageDone true))))')
TAIL = '''
OB = '/Game/SoulCharger/Obra/BP_Obra_SC.BP_Obra_SC'
CDO = '/Game/SoulCharger/Obra/BP_Obra_SC.Default__BP_Obra_SC_C'
PB = '/Game/SoulCharger/Obra/Partitura/BP_Partitura_SC.BP_Partitura_SC'
DA = '/Game/SoulCharger/Obra/Partitura/DA_Partitura_Obra.DA_Partitura_Obra'
TB = '/Game/NeuralCanvas/TB/BP_TBDirector_NC.BP_TBDirector_NC'
LOAD = %r
STAGETIMES = %r
REQ = %r
SRE_B = %r
SRE_H = %r
SRE_L = %r
SRE_SEQ = %r
SRE_TB = %r
CORTES = %r
SIMCUT = %r
TIMEUP = %r
DUMP = 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/Obra/dump/cortes_out.json'
def run():
    out = {}
    try:
        ok, pie = T('EditorToolset.EditorAppToolset.IsPIERunning', {})
        if pie:
            return {'err': 'PIE'}
        lv = T(ST + 'get_current_level', {})[1]
        out['level'] = lv
        if 'Test_QuestCtrl' not in str(lv):
            return {'err': 'nivel no neutro', 'level': lv}
        ok, vs = T(BT + 'list_variables', {'blueprint': {'refPath': PB}})
        if "'Corte_Espera'" not in str(vs):
            T(BT + 'add_variable', {'blueprint': {'refPath': PB}, 'name': 'Corte_Espera', 'type_name': 'float'})
        T(BT + 'set_variable_category', {'blueprint': {'refPath': PB}, 'variable_name': 'Corte_Espera', 'category': '2 Cada etapa'})
        T(BT + 'set_variable_instance_editable', {'blueprint': {'refPath': PB}, 'variable_name': 'Corte_Espera', 'instance_editable': True})
        T(BT + 'set_variable_category', {'blueprint': {'refPath': PB}, 'variable_name': 'Sim_EtapaMax', 'category': '3 Simulado'})
        T(BT + 'compile_blueprint', {'blueprint': {'refPath': PB}})
        vals = json.dumps({'Corte_Espera': 30.0, 'Etapa_Tope': [240.0, 180.0, 120.0, 240.0, 205.0]})
        out['pb_cdo'] = T(OT + 'set_properties', {'instance': {'refPath': '/Game/SoulCharger/Obra/Partitura/BP_Partitura_SC.Default__BP_Partitura_SC_C'}, 'values': vals})[0]
        out['da_set'] = T(OT + 'set_properties', {'instance': {'refPath': DA}, 'values': vals})[0]
        out['timeup'] = write_graph(TB, 'TimeUp', TIMEUP)
        out['sre_tb'] = write_graph(TB, 'StageRequestEnd', SRE_TB)
        out['tb_compiled'] = compile_ok(TB)
        STG = [('/Game/SoulCharger/Mechanics/Breath/BP_BreathStage_SC', SRE_B), ('/Game/SoulCharger/Mechanics/Heart/BP_HeartManager_SC', SRE_H), ('/Game/SoulCharger/Mechanics/Loving/BP_LovingCell_SC', SRE_L), ('/Game/SoulCharger/Core/Attracting/BP_Sequencer_SC', SRE_SEQ)]
        out['stages'] = []
        for (pk, code) in STG:
            b = pk + '.' + pk.split('/')[-1]
            w = write_graph(b, 'StageRequestEnd', code)
            c = compile_ok(b)
            sv = T(AS + 'save_assets', {'asset_paths': [pk]})[0] if ('WROTE' in w and c) else False
            out['stages'].append((pk.split('/')[-1], w[:300], c, sv))
        out['vars'] = add_vars(OB, CDO, [('Corte_Espera', 'f', 30.0, 'Partitura'), ('Corte_Pedido', 'bool', False, 'Interno'), ('Corte_At', 'f', 0.0, 'Interno')])
        out['load'] = write_graph(OB, 'LoadPartitura', LOAD)
        out['stagetimes'] = write_graph(OB, 'StageTimes', STAGETIMES, [('K', 'int')])
        out['req'] = write_graph(OB, 'RequestEnd', REQ, [('K', 'int')])
        out['cortes'] = write_graph(OB, 'EtapaCortes', CORTES)
        out['simcut'] = write_graph(OB, 'SimCut', SIMCUT)
        allw = all('WROTE' in str(out[k]) for k in ['load', 'stagetimes', 'req', 'cortes', 'simcut', 'timeup', 'sre_tb'])
        allw = allw and all(x[1].startswith('WROTE') and x[2] for x in out['stages'])
        out['allw'] = allw
        if allw:
            T(BT + 'compile_blueprint', {'blueprint': {'refPath': OB}})
            for vn in ['DrawCutDone', 'DrawCutAt', 'DrawCutT', 'DrawCutWait']:
                out['rm_' + vn] = T(BT + 'remove_variable', {'blueprint': {'refPath': OB}, 'name': vn})[0]
            out['ob_compiled'] = compile_ok(OB)
            if out['ob_compiled']:
                for vn in ['Dibujo_Corte', 'Dibujo_TopeTrasCorte']:
                    out['rmp_' + vn] = T(BT + 'remove_variable', {'blueprint': {'refPath': PB}, 'name': vn})[0]
                out['pb_compiled'] = compile_ok(PB)
                out['ob_compiled2'] = compile_ok(OB)
                if out['pb_compiled'] and out['ob_compiled2'] and out['tb_compiled']:
                    out['saved'] = T(AS + 'save_assets', {'asset_paths': ['/Game/SoulCharger/Obra/BP_Obra_SC', '/Game/SoulCharger/Obra/Partitura/BP_Partitura_SC', '/Game/SoulCharger/Obra/Partitura/DA_Partitura_Obra', '/Game/NeuralCanvas/TB/BP_TBDirector_NC']})[0]
        out['da_read'] = str(T(OT + 'get_properties', {'instance': {'refPath': DA}, 'properties': ['Etapa_Tope', 'Corte_Espera']})[1])
        out['read'] = {g: str(T(BT + 'read_graph_dsl', {'graph': {'refPath': OB + ':' + g}})[1]) for g in ['EtapaCortes', 'RequestEnd', 'SimCut', 'StageTimes']}
        out['read_tb'] = str(T(BT + 'read_graph_dsl', {'graph': {'refPath': TB + ':TimeUp'}})[1])
        ok, ns = T(BT + 'find_nodes', {'graph': {'refPath': OB + ':RequestEnd'}, 'title': ''})
        ok, inf = T(BT + 'get_node_infos', {'nodes': ns or []})
        out['req_targets'] = [(n['type_id'], [p['type_id'] for p in n['input_pins'] if p['name'] == 'self']) for n in (inf or []) if 'StageRequestEnd' in n['type_id']]
    except BaseException as e:
        LOG.append('run ' + str(e)[:300])
    out['log'] = [l[:400] for l in LOG[:12]]
    T(AS + 'write_file', {'file_path': DUMP, 'content': json.dumps(out)})
    return {k: v for k, v in out.items() if k not in ('read', 'read_tb')}
''' % (LOAD, STAGETIMES, REQ, SRE_SIMPLE('BREATH'), SRE_SIMPLE('HEART'), SRE_SIMPLE('LOVING'), SRE_SEQ, SRE_TB, CORTES, SIMCUT, TIMEUP)
lib = open('surg_lib.py', encoding='utf-8').read()
i = lib.index('def node_map(')
j = lib.index('def add_vars(')
lib = lib[:i] + lib[j:]
body = lib + TAIL
ast.parse(body)
open('job_cortes2.json', 'w', encoding='utf-8').write(json.dumps({'script': body}))
print(len(body))
