

# =====================================================================================================================================
# RECORRIDO v2 (PDF + nota de voz de Beltran, 2026-11-12 noche; memoria ic-recorrido-v2-marco). Todo con mano + LASER hasta el final;
# nadie toma nada. Fases: 0 titulo + botones de idioma + pista bilingue debajo | 1 elige idioma | 2 bienvenida + teclado + pista "apunta
# y presiona..." debajo del teclado | 3 nombre | 4 se va el teclado, HUD con el nombre + voz del tiempo (IC_23) | 5 MARCO de
# instrucciones (BP_ICTutor_IC v2: paleta y mando grandes, mantos y textos uno a uno con la voz, demo) | 6 cartas de la mano dominante
# (laser) | 7 las herramientas en las manos, se esconden las manos, el borde del piso aparece, IC_27 "Este es tu espacio de dibujo. El
# lienzo es tuyo." | a 0,6 s: dibujo y reloj (9). Final: tras las vueltas, niebla blanca + el titulo y el logo EN SU LUGAR (no al frente
# de la camara) y se queda asi hasta la orden del PC. El circulo del centro del piso se ve siempre (BP_ICSpace_IC). Aviso de borde en el
# dibujo: BP_ICSpace_IC.WarnOn -> BP_ICTutor_IC.WarnSet. VoInvite = IC_27; VoTut[8] = IC_26 (valores de la instancia y del CDO).
# =====================================================================================================================================
RECORRIDO2 = True
if RECORRIDO2:
    CODES['IntroTick'] = """(fn IntroTick (Dt)
  (switch Utilities|FlowControl|Switch|SwitchonInt %(ph)s
    (:0
      (if (< %(rt)s 0.4)
        (CallFunction|FPlaceTitle))
      (if (< %(rt)s %(bat)s)
        (CallFunction|FPlaceBtns))
      (if (>= %(rt)s %(bat)s)
        (Class|BPShareButtonSC|Appear %(ben)s)
        (Class|BPShareButtonSC|Appear %(bes)s)
        (Class|BPSeqRigSC|ResultsBeam %(rig)s true)
        (Class|BPSeqRigSC|ResultsBeam %(rig2)s true)
        (bind _yaw (.yaw %(camrot)s))
        %(hlang)s
        %(lp1)s
        %(lp2)s
        %(p0)s
        %(g1)s))
    (:1
      (CallFunction|PickLang))
    (:2
      %(hoff)s
      (if (>= %(pt)s 1.0)
        (Class|BPICKeyboardIC|KbShow :self %(kb)s :Spanish %(les)s)
        %(s1)s
        %(s04)s
        (Variables|Default|SetClk1 false)
        %(hname)s
        %(pkb)s
        %(g3)s))
    (:3
      (if (and (not %(s04g)s) %(ready)s)
        %(s04t)s
        %(sn)s)
      (CallFunction|KbWait))))
""" % dict(ph=D('Phase'), rt=D('RT'), pt=D('PT'), bat=D('ButtonsAt'), ben=D('BtnEn'), bes=D('BtnEs'), rig=D('Rig'), rig2=D('Rig2'),
           camrot=CAMROT, kb=D('Kb'), les=D('LangES'), ready=READY,
           hlang=TUT('HintShow', ' :Mode 1 :Spanish false :Pos (+ %s (+ (* %s 150.0) (Math|Vector|MakeVector 0.0 0.0 -72.0)))' % (CAM, FWD)),
           hname=TUT('HintShow', ' :Mode 2 :Spanish %s :Pos (Math|Transform|TransformLocation (Transformation|GetActorTransform %s) (Math|Vector|MakeVector 0.0 -4.5 -29.0))' % (D('LangES'), D('Kb'))),
           hoff=TUT('HintOff'),
           lp1=DS('LastPressN', '(Class|BPSeqRigSC|GetResPressN %s)' % D('Rig')), lp2=DS('LastPressN2', '(Class|BPSeqRigSC|GetResPressN %s)' % D('Rig2')),
           p0=P('IC: titulo, botones de idioma y la pista (laser)'), g1=GOPH(1), s1=SAY('VoWelcome'), s04=DS('Said04', 'false'),
           pkb=P('IC: bienvenida, teclado y su pista'), g3=GOPH(3), s04g=D('Said04'), s04t=DS('Said04', 'true'), sn=SAY('VoName'))

    # FlowTut: igual, con 9 pasos (0 paleta y pincel, 1-6 etiquetas, 7 demo, 8 cartas)
    CODES['FlowTut'] = CODES['FlowTut'].replace('(< %s 10)' % D('TutStep'), '(< %s 9)' % D('TutStep'), 1)
    assert '(< %s 9)' % D('TutStep') in CODES['FlowTut']

    CODES['TutAct'] = """(fn TutAct (K)
  (switch Utilities|FlowControl|Switch|SwitchonInt K
    (:0
      %(s0)s)
    (:1
      %(s1)s
      %(t0)s)
    (:2
      %(s2)s
      %(t1)s)
    (:3
      %(s3)s
      %(t2)s)
    (:4
      %(s4)s
      %(t3)s)
    (:5
      %(s5)s
      %(t4)s)
    (:6
      %(s6)s
      %(t5)s)
    (:7
      %(s7)s
      %(demo)s)
    (:8
      (Class|BPICVoiceIC|SetSubs :self %(voice)s :bSubs true)
      %(cards)s
      %(s8)s
      (Class|BPSeqRigSC|ResultsBeam %(rig)s true)
      (Class|BPSeqRigSC|ResultsBeam %(rig2)s true)
      %(lp1)s
      %(lp2)s
      %(c2f)s
      %(p8)s
      %(g6)s)))
""" % dict(s0=SAYK(0), s1=SAYK(1), s2=SAYK(2), s3=SAYK(3), s4=SAYK(4), s5=SAYK(5), s6=SAYK(6), s7=SAYK(7), s8=SAYK(8),
           t0=TUT('TutShow', ' :K 0'), t1=TUT('TutShow', ' :K 1'), t2=TUT('TutShow', ' :K 2'), t3=TUT('TutShow', ' :K 3'),
           t4=TUT('TutShow', ' :K 4'), t5=TUT('TutShow', ' :K 5'), demo=TUT('TutDemo'), cards=TUT('TutCards'), voice=D('Voice'),
           rig=D('Rig'), rig2=D('Rig2'),
           lp1=DS('LastPressN', '(Class|BPSeqRigSC|GetResPressN %s)' % D('Rig')), lp2=DS('LastPressN2', '(Class|BPSeqRigSC|GetResPressN %s)' % D('Rig2')),
           c2f=DS('Clk2', 'false'), p8=P('IC: cartas de la mano dominante (laser)'), g6=GOPH(6))

    # PickHand (fase 6): la carta que apunta cada laser (CardHov deja el resultado en HitK: el del primer rig se copia a Hov antes de
    # leer el segundo); el gatillo del rig que apunta una carta la elige. AutoHand 1/2 (prueba) elige derecha/izquierda a los 2 s.
    CODES['PickHand'] = """(fn PickHand ()
  (bind _rp (Class|BPSeqRigSC|GetResPressN %(rig)s))
  (bind _rp2 (Class|BPSeqRigSC|GetResPressN %(rig2)s))
  (Class|BPICTutorIC|CardHov :self %(tut)s :R %(rig)s)
  (Class|BPICTutorIC|SetHov :self %(tut)s :Hov (Class|BPICTutorIC|GetHitK %(tut)s))
  (Class|BPICTutorIC|CardHov :self %(tut)s :R %(rig2)s)
  (if (and (!= _rp %(lp)s) (>= (Class|BPICTutorIC|GetHov %(tut)s) 0))
    %(r1)s
    %(lp1)s
    %(lp2)s
    (CallFunction|HandChosen)
    (elif (and (!= _rp2 %(lp2g)s) (>= (Class|BPICTutorIC|GetHitK %(tut)s) 0))
      %(r2)s
      %(lp1)s
      %(lp2)s
      (CallFunction|HandChosen)
      (elif (and (> %(ah)s 0) (>= %(pt)s 2.0))
        %(r3)s
        (CallFunction|HandChosen)
        (else
          %(lp1)s
          %(lp2)s
          (Class|BPICTutorIC|SetHov :self %(tut)s :Hov (select (>= (Class|BPICTutorIC|GetHov %(tut)s) 0) (Class|BPICTutorIC|GetHov %(tut)s) (Class|BPICTutorIC|GetHitK %(tut)s))))))))
""" % dict(rig=D('Rig'), rig2=D('Rig2'), tut=D('Tut'), lp=D('LastPressN'), lp2g=D('LastPressN2'),
           r1=DS('Right', '(== (Class|BPICTutorIC|GetHov %s) 1)' % D('Tut')), r2=DS('Right', '(== (Class|BPICTutorIC|GetHitK %s) 1)' % D('Tut')),
           r3=DS('Right', '(== %s 1)' % D('AutoHand')), ah=D('AutoHand'), pt=D('PT'),
           lp1=DS('LastPressN', '_rp'), lp2=DS('LastPressN2', '_rp2'))

    # HandChosen: la mano habil = Right. Se van marco y cartas (TutPick), los laseres se apagan, las herramientas aparecen en las manos
    # (StageIntro), las manos del pawn se esconden, el borde del piso aparece y la voz dice "Este es tu espacio de dibujo. El lienzo es tuyo."
    CODES['HandChosen'] = """(fn HandChosen ()
  (Development|PrintString (Utilities|String|Append "IC: mano dominante " (select %(r)s "derecha" "izquierda")) :bPrintToScreen false)
  (Class|BPSeqRigSC|SetRightHanded :self %(rig)s :bRightHanded %(r)s)
  (Class|BPTBDirectorNC|SetHandedness :self %(tb)s :LeftHanded (not %(r)s))
  %(pick)s
  (Class|BPSeqRigSC|ResultsBeam %(rig)s false)
  (Class|BPSeqRigSC|ResultsBeam %(rig2)s false)
  (Class|BPTBDirectorNC|StageIntro %(tb)s)
  (CallFunction|FPawnHand :Right true :Vis false)
  (CallFunction|FPawnHand :Right false :Vis false)
  (Class|BPICSpaceIC|SpaceReveal %(space)s)
  %(say)s
  %(c2f)s
  %(go)s)
""" % dict(r=D('Right'), rig=D('Rig'), rig2=D('Rig2'), tb=D('TB'), pick=TUT('TutPick', ' :Right %s' % D('Right')), space=D('Space'),
           say=SAY('VoInvite'), c2f=DS('Clk2', 'false'), go=GOPH(7))

    CODES['GuideTick'] = """(fn GuideTick (Dt)
  (switch Utilities|FlowControl|Switch|SwitchonInt (- %(ph)s 4)
    (:0
      (if (and (not %(c2)s) (>= %(pt)s 0.3))
        %(c2t)s
        %(hoff)s
        (Class|BPICHudKitIC|HudInstall %(kit)s)
        (Class|BPICHudKitIC|SetTimeLeft :self %(kit)s :TimeLeft %(dtime)s)
        (Class|BPICHudKitIC|KitSetInk :self %(kit)s :K 1.0)
        (Class|BPICHudKitIC|KitSetName :self %(kit)s :Tex (Class|BPICKeyboardIC|GetNameRT %(kb)s))
        %(ink1)s
        %(sgo)s
        %(phud)s)
      (if (and %(c2)s %(ready)s)
        %(c2f)s
        %(ts_1)s
        %(g5)s))
    (:1
      (CallFunction|FlowTut))
    (:2
      (CallFunction|PickHand))
    (:3
      (if (>= %(pt)s 0.6)
        (Class|BPTBDirectorNC|StageBegin %(tb)s)
        (Class|BPTBDirectorNC|SetInkUsed :self %(tb)s :InkUsed 0.0)
        %(ink1)s
        %(tt0)s
        %(req0)s
        (Class|BPICLinkIC|LinkClear %(link)s)
        (if %(synth)s
          (Class|BPTBDirectorNC|DbgSynth %(tb)s))
        %(p9)s
        %(g9)s))))
""" % dict(ph=D('Phase'), pt=D('PT'), c2=D('Clk2'), c2t=DS('Clk2', 'true'), c2f=DS('Clk2', 'false'), kit=D('Kit'), dtime=D('DrawTime'),
           kb=D('Kb'), ink1=DS('Ink01', '1.0'), sgo=SAY('VoGo'), phud=P('IC: HUD con el nombre, 5:00 y la tinta'), ready=READY, g5=GOPH(5),
           hoff=TUT('HintOff'), ts_1=DS('TutStep', '-1'), tb=D('TB'), tt0=DS('TimerT', '0.0'), req0=DS('Req', 'false'), link=D('Link'),
           synth=D('TestSynth'), p9=P('IC: arranca el dibujo libre'), g9=GOPH(9))

    # FEndShow: el dibujo ya se fue; niebla blanca y el TITULO + el logo en su lugar original (FPlaceTitle: el TargetPoint del titulo,
    # fijo en el mundo), y se queda asi hasta la orden del PC. Sin el cartel del cierre.
    CODES['FEndShow'] = """(fn FEndShow ()
  (CallFunction|HandsBack)
  %(say)s
  (Variables|Default|SetClk1 false)
  (Variables|Default|SetEndHintOff false)
  %(woff)s
  (Development|PrintString "IC: fin: niebla blanca y el titulo en su lugar; espera la orden del PC" :bPrintToScreen false)
  %(g11)s
  (CallFunction|FPlaceTitle)
  (Rendering|Material|SetMaterial %(title)s 0 %(tmi)s)
  (Rendering|SetTranslucentSortPriority %(logo)s 32700))
""" % dict(say=SAY('VoThanks'), woff=TUT('WarnSet', ' :On false'), g11=GOPH(11), title=D('Title'), tmi=D('TitleMI'), logo=D('Logo'))

    # FVeil: en el cierre (fase 11) el titulo y el logo aparecen y se QUEDAN (antes el cartel se iba a 15-17 s)
    _v = CODES['FVeil']
    _o = '(select _msg %s _out)' % EASE(MAP('_pt', '15.0', '17.0'))
    assert _o in _v, 'FVeil out'
    _v = _v.replace(_o, '(select _msg 0.0 _out)', 1)
    _lv = '(Rendering|SetVisibility %s (or _intro _clo))' % D('Logo')
    assert _lv in _v, 'FVeil logo'
    _v = _v.replace(_lv, '(Rendering|SetVisibility %s (or _intro _msg))' % D('Logo'), 1)
    CODES['FVeil'] = _v

    # ICReset: + pistas y aviso apagados
    CODES['ICReset'] = CODES['ICReset'].replace('  (CallFunction|ResetVars)\n', '  %s\n  %s\n  (CallFunction|ResetVars)\n' % (TUT('HintOff'), TUT('WarnSet', ' :On false')), 1)
    assert 'HintOff' in CODES['ICReset']

    # FlowTick: el mando del pedestal ya no va a la mano (su gatillo no copia el de la persona); aviso de borde mientras se dibuja
    _b8 = '(if (>= %s 8)' % D('Phase')
    assert _b8 in CODES['FlowTick'], 'FlowTick 8'
    CODES['FlowTick'] = CODES['FlowTick'].replace(_b8, '(if (== %s 99)' % D('Phase'), 1)
    CODES['FlowTick'] = CODES['FlowTick'].replace('  (CallFunction|LinkSync)\n', '  (CallFunction|LinkSync)\n  %s\n' % TUT('WarnSet', ' :On (and (== %s 9) (Class|BPICSpaceIC|GetWarnOn %s))' % (D('Phase'), D('Space'))), 1)
    assert 'GetWarnOn' in CODES['FlowTick']
    for _k in ('IntroTick', 'GuideTick', 'TutAct', 'FlowTut', 'PickHand', 'HandChosen', 'FEndShow', 'FVeil', 'ICReset', 'FlowTick'):
        assert CODES[_k].count('(') == CODES[_k].count(')'), 'parentesis ' + _k
