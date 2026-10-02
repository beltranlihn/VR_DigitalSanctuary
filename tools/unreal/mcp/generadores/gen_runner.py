import json, ast
NL = chr(10)
def L(*xs):
    return NL.join(xs) + NL
RN = '/Game/SoulCharger/Obra/BP_StageRunner_SC.BP_StageRunner_SC'
DA = '/Game/SoulCharger/Obra/Partitura/DA_Partitura_Obra.DA_Partitura_Obra'
COPIES = [('Etapa_VeloAbreIni', 1.0), ('Etapa_VeloAbreFin', 4.0), ('Etapa_TituloRevelaIni', 0.5), ('Etapa_TituloRevelaFin', 1.8),
          ('Etapa_TituloSaleIni', 4.6), ('Etapa_TituloSaleFin', 5.6), ('Etapa_TituloOculto', 5.7), ('Alma_Entra', 5.5),
          ('Alma_TrasVoz', 3.0), ('Despedida_Retardo', 0.9), ('Corte_Espera', 30.0)]
VARS = [('Partitura', 'obj:/Game/SoulCharger/Obra/Partitura/BP_Partitura_SC.BP_Partitura_SC_C', DA, 'Partitura')]
VARS += [(n, 'f', v, 'Partitura') for (n, v) in COPIES]
VARS += [('EtapaTopeRun', 'f', 240.0, 'Partitura'), ('RCortePedido', 'bool', False, 'Interno'), ('VOEntrada', 'objarr:/Script/Engine.SoundBase', ['/Game/SoulCharger/Obra/Audio/VO_%s.VO_%s' % (x, x) for x in ['10', '15', '20', '26', '31']], 'Ensayo')]
DN = lambda n: n.replace('_', '')
PG = '(Class|BPPartituraSC|Get%s _p)'
AG = '(Utilities|Array|Get(acopy) %s (Variables|Ensayo|GetStageK))'
lines = ['      (Variables|Partitura|Set%s %s)' % (DN(n), PG % DN(n)) for (n, v) in COPIES]
lines += ['      (Variables|Ensayo|SetInstrTime %s)' % (AG % (PG % 'InstrDur')),
          '      (Variables|Ensayo|SetOutroTime %s)' % (AG % (PG % 'SalidaDur')),
          '      (Variables|Partitura|SetEtapaTopeRun %s)' % (AG % (PG % 'EtapaTope')),
          '      (Variables|Ensayo|SetTimeoutS (+ %s %s))' % (AG % (PG % 'EtapaTope'), PG % 'CorteEspera'),
          '      (Variables|Ensayo|SetChargeTime %s)' % (AG % (PG % 'CargaDur')),
          '      (Development|PrintString "ENSAYO: partitura cargada (los tiempos son los de la Obra)" false))']
LOAD = L('(fn RLoadPartitura ()', '  (bind _p (Variables|Partitura|GetPartitura))', '  (Utilities|IsValid _p', '    (:"Is Valid"') + NL.join(lines) + NL + L(
    '    (:"Is Not Valid"', '      (Development|PrintString "ENSAYO: ATENCION - sin partitura: quedan los tiempos por defecto" false))))')
BRE = '/Game/SoulCharger/Mechanics/Breath/BP_BreathStage_SC.BP_BreathStage_SC_C'
HRT = '/Game/SoulCharger/Mechanics/Heart/BP_HeartManager_SC.BP_HeartManager_SC_C'
LOV = '/Game/SoulCharger/Mechanics/Loving/BP_LovingCell_SC.BP_LovingCell_SC_C'
SEQ = '/Game/SoulCharger/Core/Attracting/BP_Sequencer_SC.BP_Sequencer_SC_C'
TBC = '/Game/NeuralCanvas/TB/BP_TBDirector_NC.BP_TBDirector_NC_C'
REQ = L('(fn RRequestEnd ()',
        '  (switch Utilities|FlowControl|Switch|SwitchonInt (Variables|Ensayo|GetStageK)',
        '    (:0', '      (Class|BPBreathStageSC|StageRequestEnd :self (Actor|GetActorOfClass "%s")))' % BRE,
        '    (:1', '      (Class|BPHeartManagerSC|StageRequestEnd :self (Actor|GetActorOfClass "%s")))' % HRT,
        '    (:2', '      (Class|BPLovingCellSC|StageRequestEnd :self (Actor|GetActorOfClass "%s")))' % LOV,
        '    (:3', '      (Class|BPSequencerSC|StageRequestEnd :self (Actor|GetActorOfClass "%s")))' % SEQ,
        '    (:4', '      (Class|BPTBDirectorNC|StageRequestEnd :self (Actor|GetActorOfClass "%s")))))' % TBC)
CORTES = L('(fn RCortes ()',
           '  (if (not (== (Variables|Default|GetRPhase) 3))',
           '    (Variables|Interno|SetRCortePedido false))',
           '  (if (and (== (Variables|Default|GetRPhase) 3) (and (not (Variables|Interno|GetRCortePedido)) (>= (Variables|Default|GetPT) (Variables|Partitura|GetEtapaTopeRun))))',
           '    (Variables|Interno|SetRCortePedido true)',
           '    (Variables|Ensayo|SetTimeoutS (+ (Variables|Default|GetPT) (Variables|Partitura|GetCorteEspera)))',
           '    (Development|PrintString "ENSAYO: se acabo el tiempo de la etapa - se le pide que cierre por su propio camino" false)',
           '    (CallFunction|RRequestEnd)))')
ALMA = '/Game/SoulCharger/Core/Alma/BP_Alma_SC.BP_Alma_SC_C'
RALMA = L('(fn RAlmaIn ()',
          '  (CallFunction|RAdjust :Tag (Variables|Ensayo|GetTagIn))',
          '  (CallFunction|RAdjust :Tag (Variables|Ensayo|GetTagSide))',
          '  (CallFunction|RAdjust :Tag (Variables|Ensayo|GetTagCharge))',
          '  (bind _alma (Actor|GetActorOfClass "%s"))' % ALMA,
          '  (Class|BPAlmaSC|AppearAt _alma (Variables|Ensayo|GetTagIn))',
          '  (CallFunction|RSay :Bye 0)',
          '  (Variables|Ensayo|SetAlmaTime (+ (Class|SoundBase|GetDuration (Utilities|Array|Get(acopy) (Variables|Ensayo|GetVOEntrada) (Variables|Ensayo|GetStageK))) (Variables|Partitura|GetAlmaTrasVoz)))',
          '  (Development|PrintString "ENSAYO: Alma recibe" false))')
MR = 'Math|Float|MapRangeClamped'; GE = 'Math|Float|float>=float'; LT = 'Math|Float|float<float'
SPECS = [
    dict(g='RVeil', t=MR, pin='InRangeA', v=1.0, f={'Value': '=|GetRT'}, var='EtapaVeloAbreIni', n=1),
    dict(g='RVeil', t=MR, pin='InRangeB', v=5.0, f={'Value': '=|GetRT'}, var='EtapaVeloAbreFin', n=1),
    dict(g='RVeil', t=MR, pin='InRangeA', v=1.0, f={'Value': '=Utilities|Select'}, var='EtapaTituloRevelaIni', n=1),
    dict(g='RVeil', t=MR, pin='InRangeB', v=5.5, f={'Value': '=Utilities|Select'}, var='EtapaTituloRevelaFin', n=1),
    dict(g='RVeil', t=MR, pin='InRangeA', v=9.0, var='EtapaTituloSaleIni', n=1),
    dict(g='RVeil', t=MR, pin='InRangeB', v=12.5, var='EtapaTituloSaleFin', n=1),
    dict(g='RVeil', t=LT, pin='B', v=13.0, var='EtapaTituloOculto', n=1),
    dict(g='RStep', t=GE, pin='B', v=5.5, f={'A': '=|GetRT'}, var='AlmaEntra', n=1),
    dict(g='RStep', t=GE, pin='B', v=0.9, var='DespedidaRetardo', n=1),
]
TAIL = '''
RN = %r
CDO = '/Game/SoulCharger/Obra/BP_StageRunner_SC.Default__BP_StageRunner_SC_C'
VARS = %r
LOAD = %r
REQ = %r
CORTES = %r
RALMA = %r
SPECS = %r
DUMP = 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/Obra/dump/runner_out.json'
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
        out['vars'] = add_vars(RN, CDO, VARS)
        out['load'] = write_graph(RN, 'RLoadPartitura', LOAD)
        out['req'] = write_graph(RN, 'RRequestEnd', REQ)
        out['cortes'] = write_graph(RN, 'RCortes', CORTES)
        out['ralma'] = write_graph(RN, 'RAlmaIn', RALMA)
        allw = all('WROTE' in str(out[k]) for k in ['load', 'req', 'cortes', 'ralma'])
        out['allw'] = allw
        if allw:
            T(BT + 'compile_blueprint', {'blueprint': {'refPath': RN}})
            out['ins1'] = insert_first(RN + ':RBoot', 'RLoadPartitura')
            out['ins2'] = insert_first(RN + ':RStep', 'RCortes')
            out['surg'] = surgery(RN, [dict(x) for x in SPECS], 'Variables|Partitura|Get')
            for vn in ['AlmaTime', 'InstrTime', 'OutroTime', 'TimeoutS', 'ChargeTime']:
                T(BT + 'set_variable_instance_editable', {'blueprint': {'refPath': RN}, 'variable_name': vn, 'instance_editable': False})
            out['compiled'] = compile_ok(RN)
            if out['compiled']:
                out['saved'] = T(AS + 'save_assets', {'asset_paths': ['/Game/SoulCharger/Obra/BP_StageRunner_SC']})[0]
        out['read'] = {g: str(T(BT + 'read_graph_dsl', {'graph': {'refPath': RN + ':' + g}})[1]) for g in ['RBoot', 'RStep', 'RVeil', 'RAlmaIn', 'RCortes']}
    except BaseException as e:
        LOG.append('run ' + str(e)[:300])
    out['log'] = [l[:400] for l in LOG[:12]]
    T(AS + 'write_file', {'file_path': DUMP, 'content': json.dumps(out)})
    return {k: v for k, v in out.items() if k != 'read'}
''' % (RN, VARS, LOAD, REQ, CORTES, RALMA, SPECS)
body = open('surg_lib.py', encoding='utf-8').read() + TAIL
ast.parse(body)
open('job_runner.json', 'w', encoding='utf-8').write(json.dumps({'script': body}))
print(len(body))
