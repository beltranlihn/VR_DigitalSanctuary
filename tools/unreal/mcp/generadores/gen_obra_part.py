import json, ast, sys
sys.path.insert(0, r"C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/tools/unreal")
from partitura_def import P
MAPPED = {'Aviso_Dur': 'DiscTime', 'Carga_Dur': 'ChargeTimes', 'Res_Explorar': 'ExploreT', 'Res_Cortafuegos': 'ShareFW', 'Res_Tope': 'ResultsTime',
          'Comp_Nado': 'SwimTime', 'Comp_Lejos': 'AwayTime', 'Creditos_Dur': 'CreditsTime', 'Sim_EtapaMax': 'SimStageMax', 'Dibujo_Corte': 'DrawCutT', 'Dibujo_TopeTrasCorte': 'DrawCutWait'}
OB = '/Game/SoulCharger/Obra/BP_Obra_SC.BP_Obra_SC'
CDO = '/Game/SoulCharger/Obra/BP_Obra_SC.Default__BP_Obra_SC_C'
DA = '/Game/SoulCharger/Obra/Partitura/DA_Partitura_Obra.DA_Partitura_Obra'
VARS = [('Partitura', 'obj:/Game/SoulCharger/Obra/Partitura/BP_Partitura_SC.BP_Partitura_SC_C', DA, 'Partitura')]
for (n, t, v, c, d) in P:
    if n not in MAPPED:
        VARS.append((n, t, v, 'Partitura'))
VARS += [('Velo_CierreFinT', 'f', 71.5, 'Partitura'), ('Final_NegroIniPT', 'f', 9.5, 'Partitura'), ('Hall_VeloGuarda', 'f', 6.0, 'Partitura'), ('Etapa_TopeK', 'f', 240.0, 'Partitura')]
PG = '(Class|BPPartituraSC|Get%s _p)'
DN = lambda n: n.replace('_', '')
lines = []
for (n, t, v, c, d) in P:
    tgt = ('Variables|Default|Set' + MAPPED[n]) if n in MAPPED else ('Variables|Partitura|Set' + DN(n))
    lines.append('      (%s %s)' % (tgt, PG % DN(n)))
lines.append('      (Variables|Partitura|SetVeloCierreFinT (+ 69.0 %s))' % (PG % 'VeloCierreDur'))
lines.append('      (Variables|Partitura|SetFinalNegroIniPT (- (+ 5.5 (Utilities|Array|Get(acopy) %s 4)) %s))' % (PG % 'CargaDur', PG % 'FinalNegroRampa'))
lines.append('      (Variables|Partitura|SetHallVeloGuarda (+ %s 0.5))' % (PG % 'HallVeloAbreFin'))
lines.append('      (Development|PrintString "OBRA: partitura cargada (DA_Partitura_Obra)" false))')
LOAD = ('(fn LoadPartitura ()\n  (bind _p (Variables|Partitura|GetPartitura))\n  (Utilities|IsValid _p\n    (:"Is Valid"\n'
        + '\n'.join(lines)
        + '\n    (:"Is Not Valid"\n      (Development|PrintString "OBRA: ATENCION - sin partitura (DA_Partitura_Obra): quedan los valores por defecto del Blueprint" false))))\n')
STAGETIMES = ('(fn StageTimes (K)\n'
              '  (Variables|Default|SetInstrTime (Utilities|Array|Get(acopy) (Variables|Partitura|GetInstrDur) K))\n'
              '  (Variables|Default|SetOutroTime (Utilities|Array|Get(acopy) (Variables|Partitura|GetSalidaDur) K))\n'
              '  (Variables|Partitura|SetEtapaTopeK (Utilities|Array|Get(acopy) (Variables|Partitura|GetEtapaTope) K))\n'
              '  (Variables|Default|SetAlmaTime (+ (Variables|Default|GetVODur) (Variables|Partitura|GetAlmaTrasVoz))))\n')
GT = '=|GetT'; GPT = '=|GetPT'
MR = 'Math|Float|MapRangeClamped'; GE = 'Math|Float|float>=float'; LT = 'Math|Float|float<float'; ADD = 'Math|Float|float+float'; SUB = 'Math|Float|float-float'
S = [
    dict(g='RunObra', t=MR, pin='InRangeB', v=71.5, var='Velo_CierreFinT', n=1),
    dict(g='RunObra', t=GE, pin='B', v=71.5, f={'A': GT}, var='Velo_CierreFinT', n=1),
    dict(g='RunObra', t=MR, pin='InRangeA', v=1.0, f={'Value': GT}, var='Etapa_VeloAbreIni', n=1),
    dict(g='RunObra', t=MR, pin='InRangeB', v=4.0, f={'Value': GT}, var='Etapa_VeloAbreFin', n=1),
    dict(g='RunObra', t=MR, pin='InRangeA', v=0.5, f={'Value': GT}, var='Etapa_TituloRevelaIni', n=1),
    dict(g='RunObra', t=MR, pin='InRangeB', v=1.8, f={'Value': GT}, var='Etapa_TituloRevelaFin', n=1),
    dict(g='RunObra', t=MR, pin='InRangeA', v=4.6, f={'Value': GT}, var='Etapa_TituloSaleIni', n=1),
    dict(g='RunObra', t=MR, pin='InRangeB', v=5.6, f={'Value': GT}, var='Etapa_TituloSaleFin', n=1),
    dict(g='RunObra', t=LT, pin='B', v=5.7, f={'A': GT}, var='Etapa_TituloOculto', n=1),
    dict(g='RunObra', t=GE, pin='B', v=5.8, f={'A': GT}, var='Alma_Entra', n=1),
    dict(g='RunObra', t=GE, pin='B', src='=Utilities|Select', f={'A': GPT}, var='Etapa_TopeK', n=1),
    dict(g='RunObra', t=GE, pin='B', v=1.0, f={'A': GPT}, var='Carga_Minima', n=1),
    dict(g='RunObra', t=GE, pin='B', v=3.5, f={'A': GPT}, var='Fundido_Dur', n=1),
    dict(g='FlowVeil', t=MR, pin='InRangeA', v=3.5, var='Hall_VeloAbreIni', n=1),
    dict(g='FlowVeil', t=MR, pin='InRangeB', v=5.5, var='Hall_VeloAbreFin', n=1),
    dict(g='FlowVeil', t=LT, pin='B', v=6.0, f={'A': GPT}, var='Hall_VeloGuarda', n=2),
    dict(g='FlowVeil', t=MR, pin='InRangeA', v=9.5, var='Final_NegroIniPT', n=1),
    dict(g='FlowVeil', t=MR, pin='InRangeA', v=0.2, var='Regreso_VeloIni', n=1),
    dict(g='FlowVeil', t=MR, pin='InRangeB', v=1.4, var='Regreso_VeloFin', n=1),
    dict(g='FlowVeil', t=MR, pin='InRangeA', v=1.0, f={'Value': GT}, var='Etapa_VeloAbreIni', n=1),
    dict(g='FlowVeil', t=MR, pin='InRangeB', v=4.0, f={'Value': GT}, var='Etapa_VeloAbreFin', n=1),
    dict(g='FlowVeil', t=GE, pin='B', v=5.5, f={'A': GT}, var='Alma_Entra', n=1),
    dict(g='IntroTitle', t=GE, pin='B', v=2.5, var='Titulo_Aparece', n=-1),
    dict(g='IntroTitle', t=MR, pin='InRangeA', v=3.0, var='Titulo_RevelaIni', n=-1),
    dict(g='IntroTitle', t=MR, pin='InRangeB', v=6.5, var='Titulo_RevelaFin', n=-1),
    dict(g='IntroTitle', t=MR, pin='InRangeA', v=5.0, var='Bajada_RevelaIni', n=-1),
    dict(g='IntroTitle', t=MR, pin='InRangeB', v=7.5, var='Bajada_RevelaFin', n=-1),
    dict(g='IntroTitle', t=MR, pin='InRangeA', v=17.0, var='Titulo_SaleIni', n=-1),
    dict(g='IntroTitle', t=MR, pin='InRangeB', v=19.5, var='Titulo_SaleFin', n=-1),
    dict(g='IntroTitle', t=GE, pin='B', v=20.0, var='Titulo_Fin', n=-1),
    dict(g='IntroTitle', t=ADD, pin='A', v=6.0, var='Logos_RevelaIni', n=-1),
    dict(g='IntroTitle', t=ADD, pin='A', v=8.0, var='Logos_RevelaFin', n=-1),
    dict(g='HallCheck', t=GE, pin='B', v=3.0, var='Hall_IntroA', n=1),
    dict(g='HallCheck', t=ADD, pin='B', v=1.0, var='HUD_EEGRetardo', n=1),
    dict(g='AlmaSpeak', t='|ObraSayLater', pin='Delay', v=1.5, var='Alma_VozRetardo', n=-1),
    dict(g='AlmaCharge', t=ADD, pin='B', v=0.6, var='Salida_TrasVoz', n=1),
    dict(g='FlowBye', t=GE, pin='B', v=0.9, var='Despedida_Retardo', n=1),
    dict(g='FlowBye', t=ADD, pin='A', v=1.3, var='Despedida_TrasVoz', n=1),
    dict(g='StageCues', t=ADD, pin='B', v=20.0, var='Instr_EsperaMax', n=1),
    dict(g='FlowShare', t=GE, pin='B', v=0.5, var='Res_AlmaA', n=1),
    dict(g='FlowShare', t=SUB, pin='B', v=1.2, var='Res_InvitaRecorte', n=1),
    dict(g='FlowShare', t=ADD, pin='B', v=1.8, var='Res_BotonesVoz', n=1),
    dict(g='FlowShare', t=ADD, pin='B', v=0.5, var='Res_SalidaRetardo', n=1),
    dict(g='FlowConst', t=GE, pin='B', v=5.0, var='Const_AlmaLlega', n=1),
    dict(g='FlowConst', t=GE, pin='B', v=8.0, var='Const_Voz35', n=1),
    dict(g='FlowConst', t=ADD, pin='B', v=0.6, var='Const_Voz37TrasVoz', n=1),
    dict(g='FlowFinal', t=GE, pin='B', v=0.3, var='Regreso_HallA', n=1),
    dict(g='FlowFinal', t=GE, pin='B', v=1.8, var='Res_PezMin', n=1),
    dict(g='FlowFinal', t=GE, pin='B', v=3.4, var='Res_PezMax', n=1),
    dict(g='FlowFinal', t=GE, pin='B', v=2.0, var='Res_GusanoA', n=1),
    dict(g='ReturnCheck', t=GE, pin='B', v=1.6, var='Regreso_PezA', n=1),
    dict(g='ExitCheck', t=GE, pin='B', v=0.5, var='Salida_HallA', n=1),
]
TAIL = '''
OB = %r
CDO = %r
DA = %r
VARS = %r
LOAD = %r
STAGETIMES = %r
SPECS = %r
SAVE = %r
DUMP = 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/Obra/dump/obrapart_%s.json'
def run():
    out = {}
    try:
        ok, pie = T('EditorToolset.EditorAppToolset.IsPIERunning', {})
        if pie:
            return {'err': 'PIE'}
        T(ST + 'load_level', {'level_path': '/Game/SoulCharger/Mechanics/QuestController/Test_QuestCtrl'})
        out['level'] = T(ST + 'get_current_level', {})[1]
        if not REPORT:
            T(OT + 'set_properties', {'instance': {'refPath': DA}, 'values': json.dumps({'Alma_Entra': 5.5})})
            T(AS + 'save_assets', {'asset_paths': ['/Game/SoulCharger/Obra/Partitura/DA_Partitura_Obra']})
            out['vars'] = add_vars(OB, CDO, VARS)
            out['load'] = write_graph(OB, 'LoadPartitura', LOAD)
            out['stagetimes'] = write_graph(OB, 'StageTimes', STAGETIMES, [('K', 'int')])
            T(BT + 'compile_blueprint', {'blueprint': {'refPath': OB}})
            out['ins'] = insert_first(OB + ':Begin', 'LoadPartitura')
        out['surg'] = surgery(OB, [dict(x, var=x['var'].replace('_', '')) for x in SPECS], 'Variables|Partitura|Get')
        if not REPORT:
            out['compiled'] = compile_ok(OB)
            if out['compiled'] and SAVE:
                out['saved'] = T(AS + 'save_assets', {'asset_paths': ['/Game/SoulCharger/Obra/BP_Obra_SC']})[0]
            out['read'] = {g: str(T(BT + 'read_graph_dsl', {'graph': {'refPath': OB + ':' + g}})[1]) for g in ['Begin', 'LoadPartitura', 'StageTimes', 'FlowVeil', 'HallCheck', 'FlowBye', 'AlmaSpeak', 'RunObra']}
    except BaseException as e:
        LOG.append('run ' + str(e)[:300])
    out['log'] = [l[:400] for l in LOG[:12]]
    T(AS + 'write_file', {'file_path': DUMP, 'content': json.dumps(out)})
    return {k: v for k, v in out.items() if k != 'read'}
'''
def build(report, save):
    body = open('surg_lib.py', encoding='utf-8').read().replace('REPORT = False', 'REPORT = %s' % report)
    body += TAIL % (OB, CDO, DA, VARS, LOAD, STAGETIMES, S, save, 'report' if report else 'apply')
    ast.parse(body)
    return body
open('job_obrapart_report.json', 'w', encoding='utf-8').write(json.dumps({'script': build(True, False)}))
open('job_obrapart_apply.json', 'w', encoding='utf-8').write(json.dumps({'script': build(False, True)}))
print(len(build(True, False)), len(build(False, True)))
