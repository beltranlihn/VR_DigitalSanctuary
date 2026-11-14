# menu_dsl.py - BP_DemoMenu_SC v2 (guion de Beltran 2026-10-19): menu -> viaje por el espacio azul -> VO -> HUD -> negro
Z = lambda n: '(Variables|Z-Estado|Get%s)' % n
ZS = lambda n, x: '(Variables|Z-Estado|Set%s %s)' % (n, x)
M = lambda n: '(Variables|Menu|Get%s)' % n
D = lambda n: '(Variables|Default|Get%s)' % n
DS = lambda n, x: '(Variables|Default|Set%s %s)' % (n, x)
BTN = '/Game/SoulCharger/Shared/Results/Blueprints/BP_ShareButton_SC.BP_ShareButton_SC_C'
CAM = '(Camera|GetCameraLocation (Game|GetPlayerCameraManager 0))'
PS = '(Actor|GetActorOfClass "/Script/Engine.PlayerStart")'
AT = lambda b: '(Class|BPCAppearLuzSC|GetAppearT (Class|BPShareButtonSC|GetAppearLuz %s))' % b
HINT = lambda txt: ('(Rendering|Components|TextRender|SetText %s (Utilities|Text|ToText(String) %s))\n'
                    '        (Rendering|SetVisibility %s true)') % (D('Hint'), txt, D('Hint'))
P = lambda s: '(Development|PrintString "%s" :bPrintToScreen false)' % s
CODES = {}
CODES['Boot'] = '''(fn Boot ()
  (bind _veil %(veil)s)
  %(s1)s
  %(s2)s
  %(s3)s
  %(rig)s
  %(title)s
  %(voice)s
  %(kit)s
  %(amb)s
  (Transformation|SetAbsolute _veil true true true)
  (Transformation|SetWorldLocation _veil (+ (Transformation|GetActorLocation %(ps)s) (Math|Vector|MakeVector 0.0 0.0 %(eye)s)))
  (Rendering|Material|SetColorParameterValueOnMaterials _veil "CTop" %(tm)s)
  (Rendering|Material|SetColorParameterValueOnMaterials _veil "CHor" %(hm)s)
  (Rendering|SetVisibility %(hint)s false)
  %(ph)s
  %(rt)s
  %(pt)s
  %(ks)s
  %(ka)s
  %(kb)s
  %(p)s)
''' % dict(veil=D('Veil'), ps=PS, eye=M('EyeRef'), tm=M('TopMenu'), hm=M('HorMenu'), hint=D('Hint'),
           s1=ZS('BtnStart', '(Utilities|Array|Get(acopy) (Actor|GetAllActorsOfClassWithTag "%s" "demo_start") 0)' % BTN),
           s2=ZS('BtnA', '(Utilities|Array|Get(acopy) (Actor|GetAllActorsOfClassWithTag "%s" "demo_a") 0)' % BTN),
           s3=ZS('BtnB', '(Utilities|Array|Get(acopy) (Actor|GetAllActorsOfClassWithTag "%s" "demo_b") 0)' % BTN),
           rig=ZS('Rig', '(Actor|GetActorOfClass "/SC_Sequencer/Blueprints/BP_SeqRig_SC.BP_SeqRig_SC_C")'),
           title=ZS('Title', '(Utilities|Array|Get(acopy) (Actor|GetAllActorsWithTag "hall_intro_title") 0)'),
           voice=DS('Voice', '(Actor|GetActorOfClass "/Game/SoulCharger/Demo/Blueprints/BP_DemoVoice_SC.BP_DemoVoice_SC_C")'),
           kit=DS('Kit', '(Actor|GetActorOfClass "/Game/SoulCharger/Demo/Blueprints/BP_DemoHudKit_SC.BP_DemoHudKit_SC_C")'),
           amb=DS('Amb', '(Actor|GetActorOfClass "/Game/SoulCharger/Demo/Blueprints/BP_DemoAmb_SC.BP_DemoAmb_SC_C")'),
           ph=ZS('Phase', '0'), rt=ZS('RT', '0.0'), pt=ZS('PT', '0.0'), ks=DS('KS', '1.0'), ka=DS('KA', '1.0'), kb=DS('KB', '1.0'),
           p=P('DEMO: menu arranca'))

CODES['Place'] = '''(fn Place ()
  (bind _title %(title)s)
  %(dz)s
  (bind _off (Math|Vector|MakeVector 0.0 0.0 %(gdz)s))
  (Transformation|SetActorLocation _title (+ (Transformation|GetActorLocation _title) _off) false true)
  (Transformation|SetActorLocation %(bs)s (+ (Transformation|GetActorLocation %(bs)s) _off) false true)
  (Transformation|SetActorLocation %(ba)s (+ (Transformation|GetActorLocation %(ba)s) _off) false true)
  (Transformation|SetActorLocation %(bb)s (+ (Transformation|GetActorLocation %(bb)s) _off) false true)
  (Rendering|SetActorHiddenInGame _title false)
  %(bases)s
  %(basea)s
  %(baseb)s
  (Transformation|SetWorldLocationAndRotation %(hint)s (+ (Transformation|GetActorLocation %(bs)s) (Math|Vector|MakeVector 0.0 0.0 %(hdz)s)) (Math|Rotator|MakeRotator 0.0 0.0 180.0))
  (Rendering|Components|TextRender|SetWorldSize %(hint)s %(hcm)s)
  (Development|PrintString (Utilities|String|Append "DEMO: menu ubicado, dz = " (Utilities|String|ToString(Float) %(gdz)s)) :bPrintToScreen false))
''' % dict(title=Z('Title'), gdz=Z('DZ'), bs=Z('BtnStart'), ba=Z('BtnA'), bb=Z('BtnB'), hint=D('Hint'), hcm=D('HintCm'), hdz=D('HintDz'),
           dz=ZS('DZ', '(- (.z %s) (+ (.z (Transformation|GetActorLocation %s)) %s))' % (CAM, PS, M('EyeRef'))),
           bases=DS('BaseS', '(.x (Transformation|GetActorScale3D %s))' % Z('BtnStart')),
           basea=DS('BaseA', '(.x (Transformation|GetActorScale3D %s))' % Z('BtnA')),
           baseb=DS('BaseB', '(.x (Transformation|GetActorScale3D %s))' % Z('BtnB')))

CODES['Choose'] = '''(fn Choose (I)
  (bind _btnstart %(bs)s)
  (bind _btna %(ba)s)
  (bind _btnb %(bb)s)
  (Rendering|SetVisibility %(hint)s false)
  (if (== %(ph)s 2)
    (Class|BPShareButtonSC|Press _btnstart)
    %(ph3)s
    %(pt0)s
    %(pstart)s
    (elif (== I 0)
      (Class|BPShareButtonSC|Press _btnstart)
      (Class|BPShareButtonSC|Vanish _btna)
      (Class|BPShareButtonSC|Vanish _btnb)
      %(ph5)s
      %(pt0)s
      %(pback)s
      (else
        %(ch)s
        (Class|BPShareButtonSC|Press (select (== I 1) _btna _btnb))
        (Class|BPShareButtonSC|Vanish (select (== I 1) _btnb _btna))
        (Class|BPShareButtonSC|Vanish _btnstart)
        (Class|BPDemoHudKitSC|SetMode :self %(kit)s :Mode I)
        (Class|BPDemoHudKitSC|SetTimeLeft :self %(kit)s :TimeLeft 150.0)
        %(ph6)s
        %(pt0)s
        (Development|PrintString (Utilities|String|Append "DEMO: elegida la experiencia " (Utilities|String|ToString(Integer) I)) :bPrintToScreen false)))))
''' % dict(bs=Z('BtnStart'), ba=Z('BtnA'), bb=Z('BtnB'), hint=D('Hint'), ph=Z('Phase'), kit=D('Kit'),
           ph3=ZS('Phase', '3'), ph5=ZS('Phase', '5'), ph6=ZS('Phase', '6'), pt0=ZS('PT', '0.0'), ch=ZS('Choice', 'I'),
           pstart=P('DEMO: START'), pback=P('DEMO: BACK'))

CODES['VeilFx'] = '''(fn VeilFx ()
  (bind _close (Math|Float|FInterpEaseInOut 0.0 1.0 (Math|Float|MapRangeClamped %(pt)s 0.0 2.5 0.0 1.0) 2.0))
  (bind _open (- 1.0 (Math|Float|FInterpEaseInOut 0.0 1.0 (Math|Float|MapRangeClamped %(rt)s 0.5 3.0 0.0 1.0) 2.0)))
  (bind _a (select (== %(ph)s 10) _close (select (>= %(ph)s 11) 1.0 _open)))
  (bind _veil %(veil)s)
  (if (>= %(ph)s 7)
    (Transformation|SetWorldLocation _veil %(cam)s))
  (Rendering|Material|SetScalarParameterValueOnMaterials _veil "Amount" _a)
  (Rendering|Material|SetScalarParameterValueOnMaterials _veil "Floor" (select (> _a 0.985) 0.0 0.02))
  (Rendering|SetVisibility _veil (> _a 0.001)))
''' % dict(pt=Z('PT'), rt=Z('RT'), ph=Z('Phase'), veil=D('Veil'), cam=CAM)

CODES['TitleFx'] = '''(fn TitleFx ()
  (bind _rt %(rt)s)
  (for _array_element (Actor|GetComponentsByClass %(title)s "/Script/Engine.StaticMeshComponent")
    (Rendering|Material|SetScalarParameterValueOnMaterials _array_element "LT" _rt)
    (Rendering|Material|SetScalarParameterValueOnMaterials _array_element "Reveal" (Math|Float|FInterpEaseInOut 0.0 1.0 (Math|Float|MapRangeClamped _rt 1.5 5.0 0.0 1.0) 2.0))
    (Rendering|Material|SetScalarParameterValueOnMaterials _array_element "Out" (select (<= %(ph)s 2) 0.0 (select (== %(ph)s 3) (Math|Float|FInterpEaseInOut 0.0 1.0 (Math|Float|MapRangeClamped %(pt)s 0.0 2.0 0.0 1.0) 2.0) (select (== %(ph)s 5) (- 1.0 (Math|Float|FInterpEaseInOut 0.0 1.0 (Math|Float|MapRangeClamped %(pt)s 0.0 2.0 0.0 1.0) 2.0)) 1.0))))))
''' % dict(rt=Z('RT'), title=Z('Title'), ph=Z('Phase'), pt=Z('PT'))

CODES['Pick'] = '''(fn Pick ()
  (bind _btnstart %(bs)s)
  (bind _btna %(ba)s)
  (bind _btnb %(bb)s)
  (bind _rig %(rig)s)
  (bind _hit (Class|BPSeqRigSC|GetBeamHitActor _rig))
  (bind _four (== %(ph)s 4))
  (bind _auto (and (>= %(dbg)s 0) (>= %(pt)s 2.5)))
  (bind _hs (and (== _hit _btnstart) (>= %(ats)s 0.999)))
  (bind _ha (and _four (and (== _hit _btna) (>= %(ata)s 0.999))))
  (bind _hb (and _four (and (== _hit _btnb) (>= %(atb)s 0.999))))
  (bind _rp (Class|BPSeqRigSC|GetResPressN _rig))
  (Class|BPShareButtonSC|SetHover _btnstart _hs)
  (Class|BPShareButtonSC|SetHover _btna _ha)
  (Class|BPShareButtonSC|SetHover _btnb _hb)
  %(hovs)s
  %(hova)s
  %(hovb)s
  (if (or _auto (!= _rp %(lp)s))
    %(lpset)s
    (if (or _auto (or _hs (or _ha _hb)))
      (CallFunction|Choose :I (select _auto (select _four %(dbg)s 0) (select _hs 0 (select _ha 1 2)))))))
''' % dict(bs=Z('BtnStart'), ba=Z('BtnA'), bb=Z('BtnB'), rig=Z('Rig'), ph=Z('Phase'), dbg='(Variables|Debug|GetDebugPick)', pt=Z('PT'),
           ats=AT('_btnstart'), ata=AT('_btna'), atb=AT('_btnb'), lp=Z('LastPressN'), lpset=ZS('LastPressN', '_rp'),
           hovs=DS('HovS', '_hs'), hova=DS('HovA', '_ha'), hovb=DS('HovB', '_hb'))

CODES['HoverFx'] = '''(fn HoverFx (Dt)
  %(ks)s
  %(ka)s
  %(kb)s
  (bind _s (* %(bs0)s %(gks)s))
  (bind _a (* %(ba0)s %(gka)s))
  (bind _b (* %(bb0)s %(gkb)s))
  (Transformation|SetActorScale3D %(bs)s (Math|Vector|MakeVector _s _s _s))
  (Transformation|SetActorScale3D %(ba)s (Math|Vector|MakeVector _a _a _a))
  (Transformation|SetActorScale3D %(bb)s (Math|Vector|MakeVector _b _b _b)))
''' % dict(ks=DS('KS', '(Math|Interpolation|FInterpTo %s (select %s %s 1.0) Dt 10.0)' % (D('KS'), D('HovS'), D('HoverScale'))),
           ka=DS('KA', '(Math|Interpolation|FInterpTo %s (select %s %s 1.0) Dt 10.0)' % (D('KA'), D('HovA'), D('HoverScale'))),
           kb=DS('KB', '(Math|Interpolation|FInterpTo %s (select %s %s 1.0) Dt 10.0)' % (D('KB'), D('HovB'), D('HoverScale'))),
           bs0=D('BaseS'), ba0=D('BaseA'), bb0=D('BaseB'), gks=D('KS'), gka=D('KA'), gkb=D('KB'),
           bs=Z('BtnStart'), ba=Z('BtnA'), bb=Z('BtnB'))

CODES['TravelStep'] = '''(fn TravelStep (Dt)
  %(ttp)s
  (bind _T (Math|Float|Max(Float) %(T)s 1.0))
  (bind _a (Math|Float|Max(Float) %(a)s 0.1))
  (bind _b (Math|Float|Max(Float) %(b)s 0.1))
  (bind _t (Math|Float|Min(Float) %(tt)s _T))
  (bind _v (/ %(L)s (Math|Float|Max(Float) (- _T (* 0.5 (+ _a _b))) 0.1)))
  (bind _d (select (< _t _a) (* (* 0.5 (/ _v _a)) (* _t _t)) (select (< _t (- _T _b)) (+ (* 0.5 (* _v _a)) (* _v (- _t _a))) (- %(L)s (* (* 0.5 (/ _v _b)) (* (- _T _t) (- _T _t)))))))
  (Transformation|SetActorLocation (Game|GetPlayerPawn 0) (+ %(from)s (Math|Vector|MakeVector _d 0.0 0.0)) false true))
''' % dict(ttp=DS('TT', '(+ %s Dt)' % D('TT')), T=D('TravelTime'), a=D('AccelTime'), b=D('BrakeTime'), tt=D('TT'), L=D('TravelCm'), from_=None, **{'from': D('TravelFrom')})

SPEAK = '(Class|BPDemoVoiceSC|GetSpeaking %s)' % D('Voice')
CODES['MenuTick'] = '''(fn MenuTick (Dt)
  (bind _dt (Math|Float|Min(Float) Dt 0.0333))
  (bind _pt %(pt)s)
  (bind _rig %(rig)s)
  (bind _btnstart %(bs)s)
  %(rtp)s
  %(ptp)s
  (CallFunction|VeilFx)
  (CallFunction|TitleFx)
  (CallFunction|WaitMirror)
  (if (>= %(ph)s 7)
    (CallFunction|TravelStep :Dt _dt))
  (if (and (>= %(ph)s 2) (<= %(ph)s 5))
    (CallFunction|HoverFx :Dt _dt))
  (switch Utilities|FlowControl|Switch|SwitchonInt %(ph)s
    (:0
      (if (and (>= _pt 0.2) %(mok)s)
        (CallFunction|Place)
        %(ph1)s
        %(pt0)s))
    (:1
      (if (>= %(rt)s 4.5)
        (Class|BPSeqRigSC|ResultsBeam _rig true)
        %(lpset)s
        (Class|BPShareButtonSC|Appear _btnstart)
        %(hstart)s
        %(ph2)s
        %(pt0)s
        %(pvis)s))
    (:2
      (CallFunction|Pick))
    (:3
      (if (>= _pt 2.2)
        (Rendering|Material|SetMaterial (Class|BPShareButtonSC|GetPlate _btnstart) 1 %(miback)s)
        (Class|BPShareButtonSC|Appear _btnstart)
        (Class|BPShareButtonSC|Appear %(ba)s)
        (Class|BPShareButtonSC|Appear %(bb)s)
        %(hpick)s
        %(ph4)s
        %(pt0)s
        %(pexp)s))
    (:4
      (CallFunction|Pick))
    (:5
      (if (>= _pt 2.2)
        (Rendering|Material|SetMaterial (Class|BPShareButtonSC|GetPlate _btnstart) 1 %(mistart)s)
        (Class|BPShareButtonSC|Appear _btnstart)
        %(hstart)s
        %(ph2)s
        %(pt0)s))
    (:6
      (if (>= _pt 1.5)
        (Class|BPSeqRigSC|ResultsBeam _rig false)
        (Class|BPDemoAmbSC|Switch :self %(amb)s :NewClip %(amb2)s)
        %(from)s
        %(tt0)s
        %(said0)s
        %(ph7)s
        %(pt0)s
        %(ptravel)s))
    (:7
      (if (and (not %(said)s) (>= _pt 1.0))
        %(said1)s
        (Class|BPDemoVoiceSC|Say :self %(voice)s :Clip (select (== %(choice)s 1) %(vob)s %(vod)s))
        (elif (and %(said)s (and (>= _pt 2.0) (not %(speak)s)))
          (Class|BPDemoHudKitSC|HudInstall %(kit)s)
          %(ph8)s
          %(pt0)s)))
    (:8
      (if (>= _pt 2.6)
        (Class|BPDemoVoiceSC|Say :self %(voice)s :Clip %(vor)s)
        %(ph9)s
        %(pt0)s))
    (:9
      (if (and (>= _pt 1.0) (not %(speak)s))
        (Rendering|Material|SetColorParameterValueOnMaterials %(veil)s "CTop" %(black)s)
        (Rendering|Material|SetColorParameterValueOnMaterials %(veil)s "CHor" %(black)s)
        (Class|BPDemoAmbSC|FadeAll %(amb)s)
        %(ph10)s
        %(pt0)s
        %(pblack)s))
    (:10
      (if (>= _pt 3.0)
        (CallFunction|MenuRobot)
        %(ph11)s
        %(pt0)s
        %(popen)s
        (if (not %(robotm)s)
          (Game|OpenLevel(byName) (select (== %(choice)s 1) %(la)s %(lb)s)))))
    (:11
      (if (and %(robotm)s (>= _pt 30.0))
        %(pt0)s
        %(pnolink)s
        (Game|OpenLevel(byName) "L_Demo_Menu")))))
''' % dict(robotm=D('RobotM'), pnolink=P('DEMO: robot sin visor 30 s, vuelve al menu'), pt=Z('PT'), rig=Z('Rig'), bs=Z('BtnStart'), ba=Z('BtnA'), bb=Z('BtnB'), ph=Z('Phase'), rt=Z('RT'),
           rtp=ZS('RT', '(+ %s _dt)' % Z('RT')), ptp=ZS('PT', '(+ %s _dt)' % Z('PT')), mok='(Variables|Z-Estado|GetMirrorOk)',
           ph1=ZS('Phase', '1'), ph2=ZS('Phase', '2'), ph4=ZS('Phase', '4'), ph7=ZS('Phase', '7'), ph8=ZS('Phase', '8'),
           ph9=ZS('Phase', '9'), ph10=ZS('Phase', '10'), ph11=ZS('Phase', '11'), pt0=ZS('PT', '0.0'),
           lpset=ZS('LastPressN', '(Class|BPSeqRigSC|GetResPressN _rig)'),
           hstart=HINT(D('HintStart')), hpick=HINT(D('HintPick')), miback=M('MIBack'), mistart=M('MIStart'),
           amb=D('Amb'), amb2=D('Amb2'), **{'from': DS('TravelFrom', '(Transformation|GetActorLocation (Game|GetPlayerPawn 0))')},
           tt0=DS('TT', '0.0'), said0=DS('Said', 'false'), said1=DS('Said', 'true'), said=D('Said'), voice=D('Voice'), kit=D('Kit'),
           choice=Z('Choice'), vob=D('VoBreath'), vod=D('VoDraw'), vor=D('VoReady'), speak=SPEAK, veil=D('Veil'), black=D('Black'),
           la=M('LevelA'), lb=M('LevelB'),
           pvis=P('DEMO: START visible'), pexp=P('DEMO: experiencias visibles'), ptravel=P('DEMO: viaje por el espacio azul'),
           pblack=P('DEMO: negro'), popen=P('DEMO: abre la experiencia'))

CODES['MenuRobot'] = '''(fn MenuRobot ()
  %s
  (bind _ml (Actor|GetActorOfClass "/Game/SoulCharger/Demo/Blueprints/BP_MirrorLink_SC.BP_MirrorLink_SC_C"))
  (Utilities|IsValid _ml
    (:"Is Valid"
      (if (== (Class|BPMirrorLinkSC|GetMode _ml) 2)
        %s))))
''' % (DS('RobotM', 'false'), DS('RobotM', 'true'))

ORDER = ['Boot', 'Place', 'Choose', 'VeilFx', 'TitleFx', 'Pick', 'HoverFx', 'TravelStep', 'MenuRobot', 'MenuTick']
EVG = '''(event EventBeginPlay
  (CallFunction|Boot))

(event EventTick (DeltaSeconds)
  (CallFunction|MenuTick :Dt DeltaSeconds))
'''
