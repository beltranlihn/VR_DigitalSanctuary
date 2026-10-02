import json, ast
OB='/Game/SoulCharger/Obra/BP_Obra_SC.BP_Obra_SC'
def app(*xs):
    e = xs[0]
    for x in xs[1:]:
        e = '(Utilities|String|Append %s %s)' % (e, x)
    return e
TS_F = '(Utilities|String|ToString(Float) %s)'
TS_I = '(Utilities|String|ToString(Integer) %s)'
TS_B = '(Utilities|String|ToString(Boolean) %s)'
CMD = '''(fn ObraCmdLine ()
  (bind _cmd (Utilities|GetCommandLine))
  (bind (_val _found) (Utilities|ParseParamValue _cmd "ObraSpeed="))
  (if _found
    (Variables|Default|SetSpeed (Utilities|String|StringToFloat _val))
    (Development|PrintString (Utilities|String|Append "OBRA: Speed por linea de comandos = " _val) false))
  (if (Utilities|ParseParam _cmd "ObraSmoke")
    (Variables|Debug|SetSmoke true)
    (Variables|Default|SetDisclaimer false)
    (Variables|Default|SetSimulated true)
    (Variables|Debug|SetDebugStart -1)
    (Development|PrintString "OBRA SMOKE: modo prueba de humo (sin aviso, datos simulados, arranque normal)" false))
  (Development|PrintString %s false)
  (if (or (!= (Variables|Default|GetSpeed) 1.0) (or (>= (Variables|Debug|GetDebugStart) 1) (or (Variables|Default|GetDbgDrawSynth) (or (Variables|Default|GetPhotos) (or (Variables|Default|GetDebugEnding) (!= (Variables|Default|GetDebugShare) -1))))))
    (Development|PrintString "OBRA CONFIG: ATENCION - hay perillas de prueba encendidas: esto NO es un build de publico" false)))
''' % app('"OBRA CONFIG: Speed="', TS_F % '(Variables|Default|GetSpeed)',
          '" Simulated="', TS_B % '(Variables|Default|GetSimulated)',
          '" Disclaimer="', TS_B % '(Variables|Default|GetDisclaimer)',
          '" DebugStart="', TS_I % '(Variables|Debug|GetDebugStart)',
          '" DebugShare="', TS_I % '(Variables|Default|GetDebugShare)',
          '" DbgDrawSynth="', TS_B % '(Variables|Default|GetDbgDrawSynth)',
          '" Photos="', TS_B % '(Variables|Default|GetPhotos)',
          '" DebugEnding="', TS_B % '(Variables|Default|GetDebugEnding)')
SMOKE = '''(fn SmokeTick ()
  (bind _ph (Variables|Default|GetPhase))
  (bind _st (Variables|Default|GetStage))
  (if (and (Variables|Debug|GetSmoke) (or (!= _ph (Variables|Debug|GetSmokePhase)) (!= _st (Variables|Debug|GetSmokeStage))))
    (Variables|Debug|SetSmokePhase _ph)
    (Variables|Debug|SetSmokeStage _st)
    (Development|PrintString %s false))
  (if (and (Variables|Debug|GetSmoke) (and (== _ph 15) (>= (Variables|Default|GetPT) 3.0)))
    (Development|PrintString "OBRA SMOKE: FIN OK" false)
    (Game|QuitGame)))
''' % app('"OBRA SMOKE: fase "', TS_I % '_ph', '" etapa "', TS_I % '_st')
SIM = '(Variables|Default|GetSimulated)'
SIMCUT = '''(fn SimCut ()
  (if (and %(S)s (and (== (Variables|Default|GetPhase) 6) (and (== (Variables|Default|GetStage) 3) (>= (Variables|Default|GetPT) (Variables|Default|GetSimStageMax)))))
    (Variables|Default|SetPT 1000.0)
    (Development|PrintString "OBRA: modo simulado - la etapa cierra por SimStageMax" false))
  (if (not (== (Variables|Default|GetPhase) 6))
    (Variables|Default|SetDrawCutDone false))
  (if (and (Variables|Default|GetDbgDrawSynth) (and (== (Variables|Default|GetPhase) 6) (and (== (Variables|Default|GetStage) 4) (>= (Variables|Default|GetPT) 2.0))))
    (Variables|Default|SetDbgDrawSynth false)
    (Class|BPTBDirectorNC|DbgSynth :self (Actor|GetActorOfClass "/Game/NeuralCanvas/TB/BP_TBDirector_NC.BP_TBDirector_NC_C")))
  (if (and (== (Variables|Default|GetPhase) 6) (and (== (Variables|Default|GetStage) 4) (and (not (Variables|Default|GetDrawCutDone)) (>= (Variables|Default|GetPT) (select %(S)s (Variables|Default|GetSimStageMax) (Variables|Default|GetDrawCutT))))))
    (Variables|Default|SetDrawCutDone true)
    (Variables|Default|SetDrawCutAt (Variables|Default|GetPT))
    (Development|PrintString "OBRA: dibujo - se acabo el tiempo: se guarda y se presenta antes de la carga" false)
    (Class|BPTBDirectorNC|TimeUp :self (Actor|GetActorOfClass "/Game/NeuralCanvas/TB/BP_TBDirector_NC.BP_TBDirector_NC_C")))
  (if (and (== (Variables|Default|GetPhase) 6) (and (== (Variables|Default|GetStage) 4) (and (Variables|Default|GetDrawCutDone) (>= (Variables|Default|GetPT) (+ (Variables|Default|GetDrawCutAt) (Variables|Default|GetDrawCutWait))))))
    (Variables|Default|SetPT 1000.0)
    (Development|PrintString "OBRA: dibujo - tope de seguridad despues del corte" false))
  (CallFunction|SmokeTick)
  (CallFunction|ObraDbgFF))
''' % {'S': SIM}
JOBS = [{'bp': OB, 'pkg': '/Game/SoulCharger/Obra/BP_Obra_SC', 'cdo': '/Game/SoulCharger/Obra/BP_Obra_SC.Default__BP_Obra_SC_C',
         'vars': [('Smoke', 'bool', False, 'Debug'), ('SmokePhase', 'int', -99, 'Debug'), ('SmokeStage', 'int', -99, 'Debug')],
         'graphs': [('ObraCmdLine', CMD), ('SmokeTick', SMOKE), ('SimCut', SIMCUT)], 'save': True, 'insert_first': [('Begin', 'ObraCmdLine')],
         'read': ['ObraCmdLine', 'SmokeTick', 'SimCut']}]
HDR = 'LOADLEVEL = ' + repr('/Game/XRFramework/Levels/L_XRTemplate') + chr(10) + 'JOBS = ' + repr(JOBS)
S = open('bp_tpl.py', encoding='utf-8').read().replace('__TAG__', 'smoke1').replace('__DATA__', HDR)
ast.parse(S)
open('job_smoke1.json', 'w', encoding='utf-8').write(json.dumps({'script': S}))
print(len(S))
