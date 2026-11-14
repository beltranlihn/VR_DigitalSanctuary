
# =====================================================================================================================================
# RECORRIDO NUEVO DEL INICIO (Beltran 2026-11-12 noche; memoria ic-recorrido-nuevo-acordado). Elegir con LASER, tocar solo para tomar
# el mando, dibujar al instante. Fases: 0 titulo + el piso ya marcado + botones de idioma (laser) | 1 elige idioma (laser + gatillo) |
# 2 bienvenida + teclado | 3 nombre (laser) | 4 HUD con el nombre, 5:00 y la tinta + voz del tiempo | 5 el espacio: el piso sube y las
# 4 paredes se encienden + voz corta | 6 tutorial (paleta y mando de ejemplo, etiquetas, demo) | 7 el MISMO mando de la demo flota hacia
# la persona + "toca el control" | (lo toca: Grab) 8 se desarma la paleta de ejemplo, el mando queda en la mano, la paleta y el pincel
# aparecen en las manos, "El lienzo es tuyo" | 9 a 1,2 s: se puede dibujar y corre el reloj (DrawTick igual que antes).
# Voces: VoGo = IC_23 (tiempo y tinta), VoSpace = IC_24 (espacio corto), VoInvite = IC_25 (el lienzo es tuyo); valores de la instancia.
# =====================================================================================================================================
RECORRIDO = True
if RECORRIDO:
    # botones de idioma: panel bajo el titulo, a 1,5 m y 55 cm bajo los ojos, inclinados hacia la cara (laser, como el 11-11)
    CODES['FPlaceBtns'] = '''(fn FPlaceBtns ()
  (bind _yaw (.yaw %(camrot)s))
  (bind _base (+ %(cam)s (+ (* %(fwd)s 150.0) (Math|Vector|MakeVector 0.0 0.0 -55.0))))
  (bind _rot (Math|Rotator|MakeRotator 0.0 15.0 (+ _yaw 180.0)))
  (Transformation|SetActorLocationAndRotation %(ben)s (- _base (* %(rgt)s 20.0)) _rot false true)
  (Transformation|SetActorLocationAndRotation %(bes)s (+ _base (* %(rgt)s 20.0)) _rot false true)
  (Transformation|SetActorScale3D %(ben)s (Math|Vector|MakeVector 1.0 1.0 1.0))
  (Transformation|SetActorScale3D %(bes)s (Math|Vector|MakeVector 1.0 1.0 1.0)))
''' % dict(camrot=CAMROT, cam=CAM, fwd=FWD, rgt=RGT, ben=D('BtnEn'), bes=D('BtnEs'))

    CODES['PickLang'] = base.CODES['PickLang']

    CODES['IntroTick'] = '''(fn IntroTick (Dt)
  (switch Utilities|FlowControl|Switch|SwitchonInt %(ph)s
    (:0
      (if (not (Class|BPICSpaceIC|GetShown %(space)s))
        (Class|BPICSpaceIC|SpaceReveal %(space)s)
        (Class|BPICSpaceIC|SetRevealT :self %(space)s :RevealT 10.0))
      (if (< %(rt)s 0.4)
        (CallFunction|FPlaceTitle))
      (if (< %(rt)s %(bat)s)
        (CallFunction|FPlaceBtns))
      (if (>= %(rt)s %(bat)s)
        (Class|BPShareButtonSC|Appear %(ben)s)
        (Class|BPShareButtonSC|Appear %(bes)s)
        (Class|BPSeqRigSC|ResultsBeam %(rig)s true)
        (Class|BPSeqRigSC|ResultsBeam %(rig2)s true)
        %(hint)s
        %(lp1)s
        %(lp2)s
        %(p0)s
        %(g1)s))
    (:1
      (CallFunction|PickLang))
    (:2
      (if (>= %(pt)s 1.0)
        (Class|BPICKeyboardIC|KbShow :self %(kb)s :Spanish %(les)s)
        %(s1)s
        %(s04)s
        (Variables|Default|SetClk1 false)
        %(pkb)s
        %(g3)s))
    (:3
      (if (and (not %(s04g)s) %(ready)s)
        %(s04t)s
        %(sn)s)
      (if (and %(s04g)s (and (not (Variables|Default|GetClk1)) (and (not %(speak)s) (>= (Variables|Default|GetQuietT) 0.8))))
        (Variables|Default|SetClk1 true)
        %(hintn)s)
      (CallFunction|KbWait))))
''' % dict(ph=D('Phase'), rt=D('RT'), pt=D('PT'), bat=D('ButtonsAt'), ben=D('BtnEn'), bes=D('BtnEs'), rig=D('Rig'), rig2=D('Rig2'),
           space=D('Space'), hint=HINT('HintLang'), hintn=HINT('HintName'), kb=D('Kb'), les=D('LangES'), speak=SPEAK, ready=READY,
           lp1=DS('LastPressN', '(Class|BPSeqRigSC|GetResPressN %s)' % D('Rig')), lp2=DS('LastPressN2', '(Class|BPSeqRigSC|GetResPressN %s)' % D('Rig2')),
           p0=P('IC: titulo, piso marcado y botones de idioma (laser)'), g1=GOPH(1), s1=SAY('VoWelcome'), s04=DS('Said04', 'false'),
           pkb=P('IC: bienvenida y teclado'), g3=GOPH(3), s04g=D('Said04'), s04t=DS('Said04', 'true'), sn=SAY('VoName'))

    CODES['KbWait'] = base.CODES['KbWait'].replace('(Variables|Default|SetPhase 4)', '%s\n        %s\n        (Variables|Default|SetPhase 4)' % (DS('TutStep', '-1'), DS('Clk2', 'false')), 1)
    assert 'SetPhase 4' in CODES['KbWait'] and 'SetTutStep -1' in CODES['KbWait'] and 'SetClk2 false' in CODES['KbWait']

    # TutAct: al terminar la demo (paso 8) ya no se desarma: el mando de la demo va hacia la persona (fase 7)
    _out8 = '    (:8\n      %s)' % TUT('TutOut')
    assert _out8 in CODES['TutAct'], 'TutAct :8'
    CODES['TutAct'] = CODES['TutAct'].replace(_out8, '    (:8\n      %s\n      %s\n      %s)' % (DS('Clk2', 'false'), P('IC: fin de la demo, el control va hacia la persona'), GOPH(7)), 1)

    CODES['GuideTick'] = '''(fn GuideTick (Dt)
  (switch Utilities|FlowControl|Switch|SwitchonInt (- %(ph)s 4)
    (:0
      (if (and (not %(c2)s) (>= %(pt)s 0.5))
        %(c2t)s
        (Class|BPICHudKitIC|HudInstall %(kit)s)
        (Class|BPICHudKitIC|SetTimeLeft :self %(kit)s :TimeLeft %(dtime)s)
        (Class|BPICHudKitIC|KitSetInk :self %(kit)s :K 1.0)
        (Class|BPICHudKitIC|KitSetName :self %(kit)s :Tex (Class|BPICKeyboardIC|GetNameRT %(kb)s))
        %(ink1)s
        %(sgo)s
        %(phud)s)
      (if (and %(c2)s %(ready)s)
        %(c2f)s
        %(g5)s))
    (:1
      (if (and (not %(c2)s) (>= %(pt)s 0.3))
        %(c2t)s
        (Class|BPICSpaceIC|SpaceReveal %(space)s)
        %(ssp)s
        %(psp)s)
      (if (and %(c2)s %(ready)s)
        %(c2f)s
        %(ts_1)s
        %(g6)s))
    (:2
      (CallFunction|FlowTut))
    (:3
      (if (not %(c2)s)
        %(c2t)s
        (Transformation|DetachFromActor %(ped)s "KeepWorld" "KeepWorld" "KeepWorld")
        (Class|BPICVoiceIC|SetSubs :self %(voice)s :bSubs true)
        (bind _yaw (.yaw %(camrot)s))
        %(pbase)s
        %(pyaw)s
        (Variables|Default|SetClk1 false)
        %(sgrab)s
        %(pcome)s)
      (if (and (not (Variables|Default|GetClk1)) (and (not %(speak)s) (>= (Variables|Default|GetQuietT) 0.8)))
        (Variables|Default|SetClk1 true)
        %(hintt)s)
      (if (< %(pt)s 1.6)
        (Transformation|SetActorLocationAndRotation %(ped)s (Math|Interpolation|VInterpTo (Transformation|GetActorLocation %(ped)s) %(gpb)s Dt 3.5) (Math|Interpolation|RInterpTo (Transformation|GetActorRotation %(ped)s) (Math|Rotator|MakeRotator 0.0 0.0 (+ %(gpy)s (* %(spin)s %(pt)s))) Dt 4.0) false true)
        (else
          (CallFunction|GrabStep))))
    (:4
      (if (>= %(pt)s 1.2)
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
''' % dict(ph=D('Phase'), pt=D('PT'), c2=D('Clk2'), c2t=DS('Clk2', 'true'), c2f=DS('Clk2', 'false'), kit=D('Kit'), dtime=D('DrawTime'),
           kb=D('Kb'), ink1=DS('Ink01', '1.0'), sgo=SAY('VoGo'), phud=P('IC: HUD con el nombre, 5:00 y la tinta'), ready=READY, g5=GOPH(5),
           space=D('Space'), ssp=SAY('VoSpace'), psp=P('IC: el espacio se ilumina'), ts_1=DS('TutStep', '-1'), g6=GOPH(6),
           ped=D('Pedestal'), voice=D('Voice'), camrot=CAMROT,
           pbase=DS('PedBase', '(+ %s (+ (* %s %s) (Math|Vector|MakeVector 0.0 0.0 (* -1.0 %s))))' % (CAM, FWD, D('ReachFwd'), D('ReachDown'))),
           pyaw=DS('PedYaw', '(+ _yaw 180.0)'), sgrab=SAY('VoGrab'), pcome=P('IC: el control flota hacia la persona'), speak=SPEAK,
           hintt=HINT('HintTouch'), gpb=D('PedBase'), gpy=D('PedYaw'), spin=D('SpinDeg'),
           tb=D('TB'), tt0=DS('TimerT', '0.0'), req0=DS('Req', 'false'), link=D('Link'), synth=D('TestSynth'),
           p9=P('IC: arranca el dibujo libre'), g9=GOPH(9))

    # Grab: el mando de la demo queda en la mano (misma pose que el mando de dibujo), la paleta de ejemplo se desarma (TutOut; el mando
    # en la mano no se achica y TutHide lo esconde a 1,3 s, cuando ya estan las herramientas de dibujo), aparecen paleta y pincel.
    CODES['Grab'] = '''(fn Grab ()
  (Development|PrintString (Utilities|String|Append "IC: control tomado con la mano " (select %(r)s "derecha" "izquierda")) :bPrintToScreen false)
  (Class|BPSeqRigSC|SetRightHanded :self %(rig)s :bRightHanded %(r)s)
  (Class|BPTBDirectorNC|SetHandedness :self %(tb)s :LeftHanded (not %(r)s))
  (CallFunction|FHoldPed)
  (Class|BPICVoiceIC|HideHint %(voice)s)
  %(tout)s
  (Class|BPTBDirectorNC|StageIntro %(tb)s)
  %(say)s
  %(pp1)s
  %(c2f)s
  %(go)s)
''' % dict(r=D('Right'), rig=D('Rig'), tb=D('TB'), voice=D('Voice'), tout=TUT('TutOut'), say=SAY('VoInvite'),
           pp1=DS('PulsePend', 'true'), c2f=DS('Clk2', 'false'), go=GOPH(8))

    # FlowTick: IntroTick hasta la 3; el mando de la mano copia el gatillo desde que se toma (fase 8)
    _a = '(if (< %s 5)\n    (CallFunction|IntroTick' % D('Phase')
    assert _a in CODES['FlowTick']
    CODES['FlowTick'] = CODES['FlowTick'].replace(_a, '(if (< %s 4)\n    (CallFunction|IntroTick' % D('Phase'), 1)
    _b = '(if (or (== %s 4) (>= %s 6))' % (D('Phase'), D('Phase'))
    assert _b in CODES['FlowTick']
    CODES['FlowTick'] = CODES['FlowTick'].replace(_b, '(if (>= %s 8)' % D('Phase'), 1)
    for _k in ('IntroTick', 'GuideTick', 'Grab', 'TutAct', 'FlowTick', 'FPlaceBtns', 'KbWait'):
        assert CODES[_k].count('(') == CODES[_k].count(')'), 'parentesis ' + _k

