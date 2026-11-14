# edit_heart_1020.py - 2026-10-20: la TERCERA experiencia de la demo, Heart (RECOGNIZING), pedido de Beltran.
# Exp 2. Corre sobre flow_dsl.py, kit_dsl.py, results_dsl.py y menu_dsl.py (respaldos *_backup_1020h.py).
import shutil


def load(p):
    shutil.copy(p, p.replace('.py', '_backup_1020h.py'))
    return open(p, encoding='utf-8').read()


def rep(s, a, b, n=1):
    assert s.count(a) == n, (s.count(a), a[:100])
    return s.replace(a, b)


HMC = '/Game/SoulCharger/Mechanics/Heart/Blueprints/BP_HeartManager_SC.BP_HeartManager_SC_C'

# ======================================================================================= flow_dsl.py (BP_DemoFlow_SC)
s = load('flow_dsl.py')
s = rep(s, "           tb=DS('TB', '(Actor|GetActorOfClass \"/SC_Draw/Blueprints/BP_TBDirector_NC.BP_TBDirector_NC_C\")'),",
        "           tb=DS('TB', '(Actor|GetActorOfClass \"/SC_Draw/Blueprints/BP_TBDirector_NC.BP_TBDirector_NC_C\")') + chr(10) + '  ' + DS('HM', '(Actor|GetActorOfClass \"%s\")'),"
        % HMC)
# ShowPanel: el sensor que flota tambien en Heart
s = rep(s, '''  (if (== %(exp)s 0)
    (Class|BPCAppearLuzSC|Prepare''', '''  (if (or (== %(exp)s 0) (== %(exp)s 2))
    (Class|BPCAppearLuzSC|Prepare''')
# Grab: rama Heart (el sensor en la mano, la mano para el manager, StageIntro: la esfera sale del agua y el sensor se tine)
s = rep(s, '''    (Class|BPBreathRigSC|SetHandedness :self %(brig)s :bRightSide %(r)s)
    (else''', '''    (Class|BPBreathRigSC|SetHandedness :self %(brig)s :bRightSide %(r)s)
    (elif (== %(exp)s 2)
      (Class|BPCAppearLuzSC|Vanish (Class|BPBioSensorArtSC|GetAppear (Utilities|Casting|CastToBP_BioSensorArt_SC %(ped)s)))
      (Class|BPUserToolSC|ShowMando :self %(tool)s :Right %(r)s)
      (Class|BPUserToolSC|ToSensor :self %(tool)s :Color %(sc)s)
      (Class|BPHeartManagerSC|SetAutoHand :self %(hm)s :bAutoHand false)
      (Class|BPHeartManagerSC|SetRightHand :self %(hm)s :bRightHand %(r)s)
      (Class|BPHeartManagerSC|StageIntro %(hm)s)
      (else''')
s = rep(s, '''      (Class|BPTBDirectorNC|StageIntro %(tb)s)))
  %(go)s)''', '''      (Class|BPTBDirectorNC|StageIntro %(tb)s))))
  %(go)s)''')
s = rep(s, "go=GOPH(2))", "go=GOPH(2), hm=D('HM'))")

HEART = r'''
# HeartTick (Exp 2, 2026-10-20): RECOGNIZING. El latido es el de la Obra (BP_HeartManager_SC): sensor al pecho + quietud -> umbral ->
# un pulso cada BeatDiv latidos; cierra solo (StageBeats + la vuelta del mar) o al tope (StageRequestEnd). Sin Alma en el nivel su
# StageVO queda en silencio: las voces las dice este director (PageVo, Vo1 al primer pulso, Vo2 al empezar la vuelta, Vo3 al final).
CODES['HeartTick'] = """(fn HeartTick (Dt)
  (bind _pt %(pt)s)
  (switch Utilities|FlowControl|Switch|SwitchonInt %(ph)s
    (:0
      (if (and (>= %(rt)s 0.1) (not %(env)s))
        %(env1)s
        (Class|BPHeartManagerSC|TourSleep %(hm)s)
        (Class|BPHeartManagerSC|ScapeGo :self %(hm)s :D 0.0))
      (if (>= %(rt)s %(pat)s)
        (CallFunction|ShowPanel)
        %(g1)s))
    (:1
      (CallFunction|GrabStep))
    (:2
      (if (>= _pt 1.8)
        %(page1)s
        (CallFunction|FPanel)
        (Class|BPHeartManagerSC|StageBegin %(hm)s)
        %(zone0)s
        %(g3)s))
    (:3
      %(zone)s
      (if (or (and (>= %(zt)s 1.5) (not %(spk)s)) (or (>= %(rp)s 4) (or (and (> %(zw)s 0.0) (>= _pt %(zw)s)) (and (> %(ag)s 0.0) (>= _pt %(ag)s)))))
        %(page2)s
        (CallFunction|FPanel)
        %(g4)s))
    (:4
      (if (or (and (>= _pt 2.0) (not %(spk)s)) (or (>= %(rp)s 7) (and (> %(ag)s 0.0) (>= _pt %(ag)s))))
        (Class|BPShareButtonSC|Vanish %(card)s)
        %(st0)s
        %(req0)s
        %(h10)s
        %(h20)s
        %(p7)s
        %(g7)s))
    (:7
      %(stp)s
      (if (and (not %(h1)s) (and (>= (Class|BPHeartManagerSC|GetBeatCount %(hm)s) 1) (not %(spk)s)))
        %(h11)s
        %(say1)s)
      (if (and (not %(h2)s) (and (>= (Class|BPHeartManagerSC|GetBeatCount %(hm)s) (Class|BPHeartManagerSC|GetOrbitAtBeat %(hm)s)) (not %(spk)s)))
        %(h21)s
        %(say2)s)
      (if (and (not %(req)s) (or (>= %(st)s %(tope)s) (>= %(rp)s 10)))
        %(req1)s
        (Class|BPHeartManagerSC|StageRequestEnd %(hm)s)
        %(ptope)s)
      (if (or (Class|BPHeartManagerSC|GetStageDone %(hm)s) (and %(req)s (>= %(st)s (+ %(tope)s 30.0))))
        (Class|BPHeartManagerSC|StageOutro %(hm)s)
        %(pdone)s
        %(g10)s))
    (:10
      (if (>= _pt 2.8)
        %(say3)s
        %(g15)s))))
""" % dict(pt=D('PT'), ph=D('Phase'), rt=D('RT'), env=D('Env'), env1=DS('Env', 'true'), hm=D('HM'), pat=D('PanelAt'),
           g1=GOPH(1), g3=GOPH(3), g4=GOPH(4), g7=GOPH(7), g10=GOPH(10), g15=GOPH(15),
           page1=DS('Page', '1'), page2=DS('Page', '2'), zone0=DS('ZoneT', '0.0'),
           zone=DS('ZoneT', '(select (Class|BPHeartManagerSC|GetHeartZone %s) (+ %s Dt) 0.0)' % (D('HM'), D('ZoneT'))), zt=D('ZoneT'),
           spk=SPEAK, rp=D('RemotePhase'), zw=D('ZoneWait'), ag=D('AutoGo'), card=D('Card'),
           st0=DS('StageT', '0.0'), req0=DS('Req', 'false'), h10=DS('SaidH1', 'false'), h20=DS('SaidH2', 'false'),
           stp=DS('StageT', '(+ %s Dt)' % D('StageT')), st=D('StageT'), h1=D('SaidH1'), h11=DS('SaidH1', 'true'), h2=D('SaidH2'), h21=DS('SaidH2', 'true'),
           req=D('Req'), req1=DS('Req', 'true'), tope=D('TopeS'), say1=SAY(D('Vo1')), say2=SAY(D('Vo2')), say3=SAY(D('Vo3')),
           p7=P('DEMOFLOW: Heart, se va el panel: el latido'), ptope=P('DEMOFLOW: tope, se pide el cierre'),
           pdone=P('DEMOFLOW: la etapa termino, StageOutro'))
'''
i = s.index("CODES['PracticeCut']")
s = s[:i] + HEART + '\n' + s[i:]
s = rep(s, '''    (elif (== %(exp)s 0)
      (CallFunction|BreathTick :Dt _dt)
      (else
        (CallFunction|DrawTick :Dt _dt)))))''', '''    (elif (== %(exp)s 0)
      (CallFunction|BreathTick :Dt _dt)
      (elif (== %(exp)s 2)
        (CallFunction|HeartTick :Dt _dt)
        (else
          (CallFunction|DrawTick :Dt _dt))))))''')
s = rep(s, "'BreathCount', 'BreathTick',", "'BreathCount', 'BreathTick', 'HeartTick',")
s = rep(s, "DT_FUNCS = ['BreathTick',", "DT_FUNCS = ['BreathTick', 'HeartTick',")
open('flow_dsl.py', 'w', encoding='utf-8').write(s)

# ======================================================================================= kit_dsl.py (BP_DemoHudKit_SC): Mode 3 = Heart
s = load('kit_dsl.py')
s = rep(s, '''CODES['KitFindRig'] = """(fn KitFindRig ()
  (if (== %s 1)
    (Utilities|IsValid %s
      (:"Is Not Valid"
        %s))))
""" % (V('Mode'), V('Rig'), S('Rig', '(Utilities|Casting|CastToBP_BreathRig_SC (Actor|GetActorOfClass "%s"))' % RIGC))''',
        '''CODES['KitFindRig'] = """(fn KitFindRig ()
  (if (== %s 1)
    (Utilities|IsValid %s
      (:"Is Not Valid"
        %s))
    (elif (== %s 3)
      (Utilities|IsValid %s
        (:"Is Not Valid"
          %s)))))
""" % (V('Mode'), V('Rig'), S('Rig', '(Utilities|Casting|CastToBP_BreathRig_SC (Actor|GetActorOfClass "%s"))' % RIGC),
       V('Mode'), V('Heart'), S('Heart', '(Actor|GetActorOfClass "%s")' % HMC))''')
s = rep(s, '''CODES['KitDisc'] = """(fn KitDisc (Dt)
  (if (== %s 1)
    (Utilities|IsValid %s
      (:"Is Valid"
        %s))))
""" % (V('Mode'), V('Rig'), S('DiscK', '(Math|Interpolation|FInterpTo %s (Class|BPBreathRigSC|GetBreathOn %s) Dt 6.0)' % (V('DiscK'), V('Rig'))))''',
        '''# Mode 3 (Heart, 2026-10-20): el disco se enciende con el umbral del pecho y destella con cada pulso (BeatEnv)
CODES['KitDisc'] = """(fn KitDisc (Dt)
  (if (== %s 1)
    (Utilities|IsValid %s
      (:"Is Valid"
        %s))
    (elif (== %s 3)
      (Utilities|IsValid %s
        (:"Is Valid"
          %s)))))
""" % (V('Mode'), V('Rig'), S('DiscK', '(Math|Interpolation|FInterpTo %s (Class|BPBreathRigSC|GetBreathOn %s) Dt 6.0)' % (V('DiscK'), V('Rig'))),
       V('Mode'), V('Heart'), S('DiscK', '(Math|Interpolation|FInterpTo %s (Math|Float|Max(Float) (select (Class|BPHeartManagerSC|GetHeartZone %s) 0.55 0.0) (Class|BPHeartManagerSC|GetBeatEnv %s)) Dt 8.0)' % (V('DiscK'), V('Heart'), V('Heart'))))''')
s = rep(s, "  (Rendering|SetVisibility %(disc)s (== %(mode)s 1))", "  (Rendering|SetVisibility %(disc)s (or (== %(mode)s 1) (== %(mode)s 3)))")
s = rep(s, "da=SETS(V('Disc'), 'Amount', '(* (select (== %s 1) 1.0 0.0) (* _sk (+ 0.3 (* 0.7 %s))))' % (V('Mode'), V('DiscK'))),",
        "da=SETS(V('Disc'), 'Amount', '(* (select (or (== %s 1) (== %s 3)) 1.0 0.0) (* _sk (+ 0.3 (* 0.7 %s))))' % (V('Mode'), V('Mode'), V('DiscK'))),")
s = s.replace("RIGC = '/SC_Breath/Blueprints/BP_BreathRig_SC.BP_BreathRig_SC_C'",
              "RIGC = '/SC_Breath/Blueprints/BP_BreathRig_SC.BP_BreathRig_SC_C'\nHMC = '%s'" % HMC)
open('kit_dsl.py', 'w', encoding='utf-8').write(s)

# ======================================================================================= results_dsl.py (BP_DemoResults_SC): Exp 2
s = load('results_dsl.py')
s = s.replace("TBD = '/SC_Draw/Blueprints/BP_TBDirector_NC.BP_TBDirector_NC_C'",
              "TBD = '/SC_Draw/Blueprints/BP_TBDirector_NC.BP_TBDirector_NC_C'\nHMC = '%s'" % HMC)
s = rep(s, "  (Rendering|SetVisibility %s (and _on (== %s 1))))\n''' % (D('Shown'),",
        "  (Rendering|SetVisibility %s (and _on (or (== %s 1) (== %s 2)))))\n''' % (D('Shown'),")
s = rep(s, "D('LblCalm'), D('Big'), D('Note'), D('Exp'))\n\nCODES['ResHubCalm']", "D('LblCalm'), D('Big'), D('Note'), D('Exp'), D('Exp'))\n\nCODES['ResHubCalm']")
s = rep(s, """CODES['ResData'] = '''(fn ResData ()""", """# ResHeart (Exp 2): los latidos sentidos = pulsos x BeatDiv; un circulo por pulso (hasta 24) en la tercera ventana
CODES['ResHeart'] = '''(fn ResHeart ()
  (bind _hm (Actor|GetActorOfClass "%s"))
  (Utilities|IsValid _hm
    (:"Is Valid"
      %s
      (for _i (range (Math|Integer|Min(Integer) (Class|BPHeartManagerSC|GetBeatCount _hm) 24))
        (Utilities|Array|Add %s 0.12)))))
''' % (HMC, DS('NBeats', '(* (Class|BPHeartManagerSC|GetBeatCount _hm) (Class|BPHeartManagerSC|GetBeatDiv _hm))'), D('Scores'))

CODES['ResData'] = '''(fn ResData ()""")
s = rep(s, '''  (if (== %(exp)s 0)
    (CallFunction|ResBreath)
    (else
      (CallFunction|ResDraw)))''', '''  (if (== %(exp)s 0)
    (CallFunction|ResBreath)
    (elif (== %(exp)s 2)
      (CallFunction|ResHeart)
      (else
        (CallFunction|ResDraw))))''')
RINGH = '''RINGH = lambda: \'\'\'(for _k (range 40)
        (bind _a0 (* 9.0 (Math|Conversions|ToFloat(Integer) _k)))
        (bind _a1 (* 9.0 (Math|Conversions|ToFloat(Integer) (+ _k 1))))
        %s)\'\'\' % LINE(V2('(+ _cx (* _r (Math|Trig|Cos(Degrees) _a0)))', '(+ 76.0 (* _r (Math|Trig|Sin(Degrees) _a0)))'),
                      V2('(+ _cx (* _r (Math|Trig|Cos(Degrees) _a1)))', '(+ 76.0 (* _r (Math|Trig|Sin(Degrees) _a1)))'), '2.5', COL(1.0, 0.45, 0.4))
'''
s = rep(s, "CODES['DrawBreath'] = '''(fn DrawBreath ()", RINGH + "CODES['DrawBreath'] = '''(fn DrawBreath ()")
s = rep(s, '''  (if (== %s 0)
    (for _i (range _n)
      (bind _cx (+ 20.0 (* _sp (+ (Math|Conversions|ToFloat(Integer) _i) 0.5))))
      (bind _r (Math|Float|Min(Float) (+ 10.0 (* 44.0 (Math|Float|Clamp(Float) (Utilities|Array|Get(acopy) %s _i) 0.0 1.0))) (* 0.45 _sp)))
      %s))
  %s)
\'\'\' % (BEGIN(2), D('Scores'), D('Exp'), D('Scores'), RING(), END)''', '''  (if (== %s 0)
    (for _i (range _n)
      (bind _cx (+ 20.0 (* _sp (+ (Math|Conversions|ToFloat(Integer) _i) 0.5))))
      (bind _r (Math|Float|Min(Float) (+ 10.0 (* 44.0 (Math|Float|Clamp(Float) (Utilities|Array|Get(acopy) %s _i) 0.0 1.0))) (* 0.45 _sp)))
      %s)
    (elif (== %s 2)
      (for _i (range _n)
        (bind _cx (+ 20.0 (* _sp (+ (Math|Conversions|ToFloat(Integer) _i) 0.5))))
        (bind _r (Math|Float|Min(Float) (+ 10.0 (* 44.0 (Math|Float|Clamp(Float) (Utilities|Array|Get(acopy) %s _i) 0.0 1.0))) (* 0.45 _sp)))
        %s)))
  %s)
\'\'\' % (BEGIN(2), D('Scores'), D('Exp'), D('Scores'), RING(), D('Exp'), D('Scores'), RINGH(), END)''')
s = rep(s, '''breath=SETTEXT(D('LblBreath'), '(select (== %s 0) "BREATH CYCLES" "YOUR DRAWING")' % D('Exp')),''',
        '''breath=SETTEXT(D('LblBreath'), '(select (== %s 0) "BREATH CYCLES" (select (== %s 2) "YOUR HEARTBEAT" "YOUR DRAWING"))' % (D('Exp'), D('Exp'))),''')
s = rep(s, '''note=SETTEXT(D('Note'), '(Utilities|String|Append (Utilities|String|ToString(Integer) %s) (select (== %s 1) " stroke of light" " strokes of light"))' % (D('NStrokes'), D('NStrokes'))))''',
        '''note=SETTEXT(D('Note'), '(select (== %s 2) (Utilities|String|Append (Utilities|String|ToString(Integer) %s) " heartbeats felt") (Utilities|String|Append (Utilities|String|ToString(Integer) %s) (select (== %s 1) " stroke of light" " strokes of light")))' % (D('Exp'), D('NBeats'), D('NStrokes'), D('NStrokes'))))''')
s = rep(s, "'ResHub', 'ResBreath', 'ResDraw', 'ResData',", "'ResHub', 'ResBreath', 'ResDraw', 'ResHeart', 'ResData',")
open('results_dsl.py', 'w', encoding='utf-8').write(s)
print('flow, kit, results ok')
