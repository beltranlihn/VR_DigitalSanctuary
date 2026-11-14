# menu_dsl.py - BP_DemoMenu_SC v2 (guion de Beltran 2026-10-19): menu -> viaje por el espacio azul -> VO -> HUD -> negro
# 2026-10-20: dos laseres (Rig + Rig2, uno por mano, con las manos visibles), VO_D03 (lo que se mide) entre el HUD y "You're ready",
# el reloj del HUD del menu = DrawShowTime. Tercer cuadro RECOGNIZING (tag demo_c, Choice 3 -> LevelC = L_Demo_Heart, VoHeart). La niebla azul (BP_HallFog_SC, bStartOn en el nivel) se apaga al empezar el viaje
# (FogOff: degrada a negro en su FadeOut) y la bienvenida espera VoDelay s. [20-10 noche: ya NO se llama FogOff: el menu nunca pasa a negro;
# el velo cierra en 6 s del azul al color de la experiencia, y el trazo de cada cuadro va del color de su experiencia (Boot).]
# 2026-10-20 tarde: el viaje no frena nunca (sigue mientras todo se va a negro), VoGap s de silencio entre voces (QuietT) y las
# instrucciones de boton como subtitulo (BP_DemoVoice_SC.ShowHint / HideHint, ids HINT_START y HINT_PICK).
# 2026-10-20 noche: la pista del START sale desde que el menu se ubica (fase 0) y el cierre a negro va sin el piso de brillo del velo
# (Floor 0,02 sobre negro se veia gris).
# 2026-10-21 noche (Beltran, arreglo 9): la pista "point the button" sale con el START (fase 1), no al ubicar el menu (fase 0).
# 2026-10-20 noche (Beltran): el menu ya no cierra a negro sino al COLOR con que arranca la experiencia elegida (TopA/HorA Breath,
# TopC/HorC Heart, TopB/HorB Draw = el CTop/CHor del DemoFlow de ese nivel): el visor congela ese cuadro durante la carga y empalma.
Z = lambda n: '(Variables|Z-Estado|Get%s)' % n
ZS = lambda n, x: '(Variables|Z-Estado|Set%s %s)' % (n, x)
M = lambda n: '(Variables|Menu|Get%s)' % n
D = lambda n: '(Variables|Default|Get%s)' % n
DS = lambda n, x: '(Variables|Default|Set%s %s)' % (n, x)
BTN = '/Game/SoulCharger/Shared/Results/Blueprints/BP_ShareButton_SC.BP_ShareButton_SC_C'
CAM = '(Camera|GetCameraLocation (Game|GetPlayerCameraManager 0))'
PS = '(Actor|GetActorOfClass "/Script/Engine.PlayerStart")'
AT = lambda b: '(Class|BPCAppearLuzSC|GetAppearT (Class|BPShareButtonSC|GetAppearLuz %s))' % b
HINT = lambda var: '(Class|BPDemoVoiceSC|ShowHint :self %s :Id %s)' % (D('Voice'), D(var))   # el id va por variable: un literal string a una funcion propia se pierde (dsl.md 4)
P = lambda s: '(Development|PrintString "%s" :bPrintToScreen false)' % s
CODES = {}
# Boot (20-10 noche): el titulo del menu dice DIGITAL SANCTUARY: TitleMI (MI_Demo_TitleDS_SC) en el TitleP del titulo de la Obra
# (su Construction Script rehace el material desde MI_Credit_Title: por eso se pone en el juego y no en la instancia)
CODES['Boot'] = '''(fn Boot ()
  (Audio|SetSubmixOutputVolume(lineargain) (Variables|Default|GetMasterMix) 1.0)
  (bind _veil %(veil)s)
  %(s1)s
  %(s2)s
  %(s3)s
  %(s4)s
  %(rig)s
  (bind _rigs (Actor|GetAllActorsOfClass "/SC_Sequencer/Blueprints/BP_SeqRig_SC.BP_SeqRig_SC_C"))
  (if (> (Utilities|Array|Length _rigs) 1)
    %(rig2)s)
  %(title)s
  %(voice)s
  %(kit)s
  %(amb)s
  (for _c (Actor|GetComponentsByClass %(tt)s "/Script/Engine.StaticMeshComponent")
    (if (Utilities|String|Contains (Utilities|GetObjectName _c) "TitleP")
      (Rendering|Material|SetMaterial _c 0 %(tmi)s)))
  (Transformation|SetAbsolute _veil true true true)
  (Transformation|SetWorldLocation _veil (+ (Transformation|GetActorLocation %(ps)s) (Math|Vector|MakeVector 0.0 0.0 %(eye)s)))
  (Rendering|Material|SetColorParameterValueOnMaterials _veil "CTop" %(tm)s)
  (Rendering|Material|SetColorParameterValueOnMaterials _veil "CHor" %(hm)s)
  (Rendering|SetVisibility %(hint)s false)
  %(tra)s
  %(trb)s
  %(trc)s
  %(ph)s
  %(rt)s
  %(pt)s
  %(ks)s
  %(ka)s
  %(kb)s
  %(kc)s
  %(p)s)
''' % dict(veil=D('Veil'), ps=PS, eye=M('EyeRef'), tm=M('TopMenu'), hm=M('HorMenu'), hint=D('Hint'), tt=Z('Title'), tmi=D('TitleMI'),
           tra='%s' % '(Rendering|Material|SetVectorParameterValueonMaterials (Class|BPShareButtonSC|GetTrace %s) "Color" (Math|Vector|MakeVector 0.55 0.72 1.0))' % Z('BtnA'),
           trb='%s' % '(Rendering|Material|SetVectorParameterValueonMaterials (Class|BPShareButtonSC|GetTrace %s) "Color" (Math|Vector|MakeVector 0.45 1.0 0.65))' % Z('BtnB'),
           trc='%s' % '(Rendering|Material|SetVectorParameterValueonMaterials (Class|BPShareButtonSC|GetTrace %s) "Color" (Math|Vector|MakeVector 1.0 0.45 0.4))' % D('BtnC'),
           s1=ZS('BtnStart', '(Utilities|Array|Get(acopy) (Actor|GetAllActorsOfClassWithTag "%s" "demo_start") 0)' % BTN),
           s2=ZS('BtnA', '(Utilities|Array|Get(acopy) (Actor|GetAllActorsOfClassWithTag "%s" "demo_a") 0)' % BTN),
           s3=ZS('BtnB', '(Utilities|Array|Get(acopy) (Actor|GetAllActorsOfClassWithTag "%s" "demo_b") 0)' % BTN),
           s4=DS('BtnC', '(Utilities|Array|Get(acopy) (Actor|GetAllActorsOfClassWithTag "%s" "demo_c") 0)' % BTN),
           rig=ZS('Rig', '(Utilities|Array|Get(acopy) (Actor|GetAllActorsOfClass "/SC_Sequencer/Blueprints/BP_SeqRig_SC.BP_SeqRig_SC_C") 0)'),
           rig2=DS('Rig2', '(Utilities|Array|Get(acopy) _rigs 1)'),
           title=ZS('Title', '(Utilities|Array|Get(acopy) (Actor|GetAllActorsWithTag "hall_intro_title") 0)'),
           voice=DS('Voice', '(Actor|GetActorOfClass "/Game/SoulCharger/Demo/Blueprints/BP_DemoVoice_SC.BP_DemoVoice_SC_C")'),
           kit=DS('Kit', '(Actor|GetActorOfClass "/Game/SoulCharger/Demo/Blueprints/BP_DemoHudKit_SC.BP_DemoHudKit_SC_C")'),
           amb=DS('Amb', '(Actor|GetActorOfClass "/Game/SoulCharger/Demo/Blueprints/BP_DemoAmb_SC.BP_DemoAmb_SC_C")'),
           ph=ZS('Phase', '0'), rt=ZS('RT', '0.0'), pt=ZS('PT', '0.0'), ks=DS('KS', '1.0'), ka=DS('KA', '1.0'), kb=DS('KB', '1.0'), kc=DS('KC', '1.0'),
           p=P('DEMO: menu arranca'))

CODES['Place'] = '''(fn Place ()
  (bind _title %(title)s)
  %(dz)s
  (bind _off (Math|Vector|MakeVector 0.0 0.0 %(gdz)s))
  (Transformation|SetActorLocation _title (+ (Transformation|GetActorLocation _title) _off) false true)
  (Transformation|SetActorLocation %(bs)s (+ (Transformation|GetActorLocation %(bs)s) _off) false true)
  (Transformation|SetActorLocation %(ba)s (+ (Transformation|GetActorLocation %(ba)s) _off) false true)
  (Transformation|SetActorLocation %(bb)s (+ (Transformation|GetActorLocation %(bb)s) _off) false true)
  (Transformation|SetActorLocation %(bc)s (+ (Transformation|GetActorLocation %(bc)s) _off) false true)
  (Rendering|SetActorHiddenInGame _title false)
  %(bases)s
  %(basea)s
  %(baseb)s
  %(basec)s
  (Transformation|SetWorldLocationAndRotation %(hint)s (+ (Transformation|GetActorLocation %(bs)s) (Math|Vector|MakeVector 0.0 0.0 %(hdz)s)) (Math|Rotator|MakeRotator 0.0 0.0 180.0))
  (Rendering|Components|TextRender|SetWorldSize %(hint)s %(hcm)s)
  (Development|PrintString (Utilities|String|Append "DEMO: menu ubicado, dz = " (Utilities|String|ToString(Float) %(gdz)s)) :bPrintToScreen false))
''' % dict(title=Z('Title'), gdz=Z('DZ'), bs=Z('BtnStart'), ba=Z('BtnA'), bb=Z('BtnB'), hint=D('Hint'), hcm=D('HintCm'), hdz=D('HintDz'),
           dz=ZS('DZ', '(- (.z %s) (+ (.z (Transformation|GetActorLocation %s)) %s))' % (CAM, PS, M('EyeRef'))),
           bases=DS('BaseS', '(.x (Transformation|GetActorScale3D %s))' % Z('BtnStart')),
           basea=DS('BaseA', '(.x (Transformation|GetActorScale3D %s))' % Z('BtnA')),
           baseb=DS('BaseB', '(.x (Transformation|GetActorScale3D %s))' % Z('BtnB')),
           bc=D('BtnC'), basec=DS('BaseC', '(.x (Transformation|GetActorScale3D %s))' % D('BtnC')))

CODES['Choose'] = '''(fn Choose (I)
  (bind _btnstart %(bs)s)
  (bind _btna %(ba)s)
  (bind _btnb %(bb)s)
  (bind _btnc %(bc)s)
  (Class|BPDemoVoiceSC|HideHint %(voice)s)
  (if (== %(ph)s 2)
    (Class|BPShareButtonSC|Press _btnstart)
    %(ph3)s
    %(pt0)s
    %(pstart)s
    (elif (== I 0)
      (Class|BPShareButtonSC|Press _btnstart)
      (Class|BPShareButtonSC|Vanish _btna)
      (Class|BPShareButtonSC|Vanish _btnb)
      (Class|BPShareButtonSC|Vanish _btnc)
      %(ph5)s
      %(pt0)s
      %(pback)s
      (else
        %(ch)s
        (Class|BPShareButtonSC|Press (select (== I 1) _btna (select (== I 3) _btnc _btnb)))
        (Class|BPShareButtonSC|Vanish (select (== I 1) _btnb _btna))
        (Class|BPShareButtonSC|Vanish (select (== I 3) _btnb _btnc))
        (Class|BPShareButtonSC|Vanish _btnstart)
        (Class|BPDemoHudKitSC|SetMode :self %(kit)s :Mode I)
        (Class|BPDemoHudKitSC|SetTimeLeft :self %(kit)s :TimeLeft %(dst)s)
        %(ph6)s
        %(pt0)s
        (Development|PrintString (Utilities|String|Append "DEMO: elegida la experiencia " (Utilities|String|ToString(Integer) I)) :bPrintToScreen false)))))
''' % dict(bs=Z('BtnStart'), ba=Z('BtnA'), bb=Z('BtnB'), hint=D('Hint'), voice=D('Voice'), ph=Z('Phase'), kit=D('Kit'), dst=D('DrawShowTime'), bc=D('BtnC'),
           ph3=ZS('Phase', '3'), ph5=ZS('Phase', '5'), ph6=ZS('Phase', '6'), pt0=ZS('PT', '0.0'), ch=ZS('Choice', 'I'),
           pstart=P('DEMO: START'), pback=P('DEMO: BACK'))

CODES['VeilFx'] = '''(fn VeilFx ()
  (bind _close (Math|Float|FInterpEaseInOut 0.0 1.0 (Math|Float|MapRangeClamped %(pt)s 0.0 6.0 0.0 1.0) 2.0))
  (bind _open (- 1.0 (Math|Float|FInterpEaseInOut 0.0 1.0 (Math|Float|MapRangeClamped %(rt)s 0.5 3.0 0.0 1.0) 2.0)))
  (bind _a (select (== %(ph)s 10) _close (select (>= %(ph)s 11) 1.0 _open)))
  (bind _veil %(veil)s)
  (if (>= %(ph)s 7)
    (Transformation|SetWorldLocation _veil %(cam)s))
  (Rendering|Material|SetScalarParameterValueOnMaterials _veil "Amount" _a)
  (Rendering|Material|SetScalarParameterValueOnMaterials _veil "Floor" (select (or (> _a 0.985) (>= %(ph)s 9)) 0.0 0.02))
  (Rendering|SetVisibility _veil (> _a 0.001)))
''' % dict(pt=Z('PT'), rt=Z('RT'), ph=Z('Phase'), veil=D('Veil'), cam=CAM)

CODES['TitleFx'] = '''(fn TitleFx ()
  (bind _rt %(rt)s)
  (for _array_element (Actor|GetComponentsByClass %(title)s "/Script/Engine.StaticMeshComponent")
    (Rendering|Material|SetScalarParameterValueOnMaterials _array_element "LT" _rt)
    (Rendering|Material|SetScalarParameterValueOnMaterials _array_element "Reveal" (Math|Float|FInterpEaseInOut 0.0 1.0 (Math|Float|MapRangeClamped _rt 1.5 5.0 0.0 1.0) 2.0))
    (Rendering|Material|SetScalarParameterValueOnMaterials _array_element "Out" (select (<= %(ph)s 2) 0.0 (select (== %(ph)s 3) (Math|Float|FInterpEaseInOut 0.0 1.0 (Math|Float|MapRangeClamped %(pt)s 0.0 2.0 0.0 1.0) 2.0) (select (== %(ph)s 5) (- 1.0 (Math|Float|FInterpEaseInOut 0.0 1.0 (Math|Float|MapRangeClamped %(pt)s 0.0 2.0 0.0 1.0) 2.0)) 1.0))))))
''' % dict(rt=Z('RT'), title=Z('Title'), ph=Z('Phase'), pt=Z('PT'))

# Pick con DOS laseres (2026-10-20, pedido de Beltran: en el menu las dos manos, cada una con su laser).
# Rig = un BP_SeqRig_SC por mano (DemoRig derecha, DemoRigL izquierda), cada uno cuenta SOLO el gatillo de su mano.
# Al elegir, vibra la mano que apreto: BP_SeqRig_SC.Pulse (el haptico de la Obra, PlayHapticEffect + GrabHapticEffect).
# El clic se decide ANTES de actualizar LastPressN/LastPressN2: _p1/_p2 son binds puros y se re-evaluan (gotcha 409).
CODES['Pick'] = '''(fn Pick ()
  (bind _btnstart %(bs)s)
  (bind _btna %(ba)s)
  (bind _btnb %(bb)s)
  (bind _btnc %(bc)s)
  (bind _rig %(rig)s)
  (bind _rig2 %(rig2)s)
  (bind _hit (Class|BPSeqRigSC|GetBeamHitActor _rig))
  (bind _hit2 (Class|BPSeqRigSC|GetBeamHitActor _rig2))
  (bind _four (== %(ph)s 4))
  (bind _auto (and (>= %(dbg)s 0) (>= %(pt)s 2.5)))
  (bind _as (>= %(ats)s 0.999))
  (bind _aa (and _four (>= %(ata)s 0.999)))
  (bind _ab (and _four (>= %(atb)s 0.999)))
  (bind _ac (and _four (>= %(atc)s 0.999)))
  (bind _s1 (and (== _hit _btnstart) _as))
  (bind _s2 (and (== _hit2 _btnstart) _as))
  (bind _a1 (and (== _hit _btna) _aa))
  (bind _a2 (and (== _hit2 _btna) _aa))
  (bind _b1 (and (== _hit _btnb) _ab))
  (bind _b2 (and (== _hit2 _btnb) _ab))
  (bind _c1 (and (== _hit _btnc) _ac))
  (bind _c2 (and (== _hit2 _btnc) _ac))
  (bind _hs (or _s1 _s2))
  (bind _ha (or _a1 _a2))
  (bind _hb (or _b1 _b2))
  (bind _hc (or _c1 _c2))
  (bind _rp (Class|BPSeqRigSC|GetResPressN _rig))
  (bind _rp2 (Class|BPSeqRigSC|GetResPressN _rig2))
  (bind _p1 (!= _rp %(lp)s))
  (bind _p2 (!= _rp2 %(lp2)s))
  (Class|BPShareButtonSC|SetHover _btnstart _hs)
  (Class|BPShareButtonSC|SetHover _btna _ha)
  (Class|BPShareButtonSC|SetHover _btnb _hb)
  (Class|BPShareButtonSC|SetHover _btnc _hc)
  %(hovs)s
  %(hova)s
  %(hovb)s
  %(hovc)s
  (if (or _auto (or _p1 _p2))
    (if _auto
      (CallFunction|Choose :I (select _four %(dbg)s 0))
      (elif (and _p1 (or _s1 (or _a1 (or _b1 _c1))))
        (CallFunction|Choose :I (select _s1 0 (select _a1 1 (select _c1 3 2))))
        (Class|BPSeqRigSC|Pulse :self _rig :bRight (Class|BPSeqRigSC|GetRightHanded _rig))
        (elif (and _p2 (or _s2 (or _a2 (or _b2 _c2))))
          (CallFunction|Choose :I (select _s2 0 (select _a2 1 (select _c2 3 2))))
          (Class|BPSeqRigSC|Pulse :self _rig2 :bRight (Class|BPSeqRigSC|GetRightHanded _rig2)))))
    %(lpset)s
    %(lpset2)s))
''' % dict(bs=Z('BtnStart'), ba=Z('BtnA'), bb=Z('BtnB'), rig=Z('Rig'), rig2=D('Rig2'), ph=Z('Phase'), dbg='(Variables|Debug|GetDebugPick)', pt=Z('PT'),
           ats=AT('_btnstart'), ata=AT('_btna'), atb=AT('_btnb'), atc=AT('_btnc'), bc=D('BtnC'), lp=Z('LastPressN'), lp2=D('LastPressN2'),
           lpset=ZS('LastPressN', '_rp'), lpset2=DS('LastPressN2', '_rp2'),
           hovs=DS('HovS', '_hs'), hova=DS('HovA', '_ha'), hovb=DS('HovB', '_hb'), hovc=DS('HovC', '_hc'))

CODES['HoverFx'] = '''(fn HoverFx (Dt)
  %(ks)s
  %(ka)s
  %(kb)s
  %(kc)s
  (bind _s (* %(bs0)s %(gks)s))
  (bind _a (* %(ba0)s %(gka)s))
  (bind _b (* %(bb0)s %(gkb)s))
  (Transformation|SetActorScale3D %(bs)s (Math|Vector|MakeVector _s _s _s))
  (Transformation|SetActorScale3D %(ba)s (Math|Vector|MakeVector _a _a _a))
  (Transformation|SetActorScale3D %(bb)s (Math|Vector|MakeVector _b _b _b))
  (bind _c (* %(bc0)s %(gkc)s))
  (Transformation|SetActorScale3D %(bc)s (Math|Vector|MakeVector _c _c _c)))
''' % dict(ks=DS('KS', '(Math|Interpolation|FInterpTo %s (select %s %s 1.0) Dt 10.0)' % (D('KS'), D('HovS'), D('HoverScale'))),
           ka=DS('KA', '(Math|Interpolation|FInterpTo %s (select %s %s 1.0) Dt 10.0)' % (D('KA'), D('HovA'), D('HoverScale'))),
           kb=DS('KB', '(Math|Interpolation|FInterpTo %s (select %s %s 1.0) Dt 10.0)' % (D('KB'), D('HovB'), D('HoverScale'))),
           bs0=D('BaseS'), ba0=D('BaseA'), bb0=D('BaseB'), gks=D('KS'), gka=D('KA'), gkb=D('KB'),
           bs=Z('BtnStart'), ba=Z('BtnA'), bb=Z('BtnB'),
           kc=DS('KC', '(Math|Interpolation|FInterpTo %s (select %s %s 1.0) Dt 10.0)' % (D('KC'), D('HovC'), D('HoverScale'))),
           bc0=D('BaseC'), gkc=D('KC'), bc=D('BtnC'))

CODES['TravelStep'] = '''(fn TravelStep (Dt)
  %(ttp)s
  (bind _T (Math|Float|Max(Float) %(T)s 1.0))
  (bind _a (Math|Float|Max(Float) %(a)s 0.1))
  (bind _b (Math|Float|Max(Float) %(b)s 0.1))
  (bind _t %(tt)s)
  (bind _v (/ %(L)s (Math|Float|Max(Float) (- _T (* 0.5 (+ _a _b))) 0.1)))
  (bind _d (select (< _t _a) (* (* 0.5 (/ _v _a)) (* _t _t)) (+ (* 0.5 (* _v _a)) (* _v (- _t _a)))))
  (Transformation|SetActorLocation (Game|GetPlayerPawn 0) (+ %(from)s (Math|Vector|MakeVector _d 0.0 0.0)) false true))
''' % dict(ttp=DS('TT', '(+ %s Dt)' % D('TT')), T=D('TravelTime'), a=D('AccelTime'), b=D('BrakeTime'), tt=D('TT'), L=D('TravelCm'), from_=None, **{'from': D('TravelFrom')})

SPEAK = '(Class|BPDemoVoiceSC|GetSpeaking %s)' % D('Voice')
# RenderPctStep (21-10, arreglo 2: nitidez). El pawn fija xr.SecondaryScreenPercentage.HMDRenderTarget 100 en su BeginPlay
# (gotcha 445): a 1 s del arranque (despues del pawn) cada nivel pone la suya, RenderPct (por instancia; CDO 100). Medido en
# visor el 21-10 al 100 %: menu GPU 0,47, Draw 0,57 (max 0,72), Breath max 0,94, Heart max 0,92 -> menu 120, Draw 115, los otros
# 100. "-DemoRenderPct=N" en la linea de comandos (UECommandLine.txt) pisa todos los niveles sin recompilar.
CODES['RenderPctStep'] = '''(fn RenderPctStep ()
  (if (and (not (Variables|Default|GetPctDone)) (>= (Variables|Z-Estado|GetRT) 1.0))
    (Variables|Default|SetPctDone true)
    (bind (_val _found) (Utilities|ParseParamValue (Utilities|GetCommandLine) "DemoRenderPct="))
    (bind _pct (select _found (Utilities|String|StringToFloat _val) (Variables|Default|GetRenderPct)))
    (if (> _pct 0.0)
      (Development|ExecuteConsoleCommand (Utilities|String|Append "xr.SecondaryScreenPercentage.HMDRenderTarget " (Utilities|String|ToString(Float) _pct)))
      (Development|PrintString (Utilities|String|Append "DEMO: resolucion del visor al " (Utilities|String|ToString(Float) _pct)) :bPrintToScreen false))))
'''

CODES['MenuTick'] = '''(fn MenuTick (Dt)
  (bind _dt (Math|Float|Min(Float) Dt 0.0333))
  (bind _pt %(pt)s)
  (bind _rig %(rig)s)
  (bind _btnstart %(bs)s)
  %(rtp)s
  %(ptp)s
  %(qtp)s
  (CallFunction|VeilFx)
  (CallFunction|RenderPctStep)
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
        (Class|BPSeqRigSC|ResultsBeam %(rig2)s true)
        %(lpset)s
        %(lpset2)s
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
        (Class|BPShareButtonSC|Appear %(bc)s)
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
        (Class|BPSeqRigSC|ResultsBeam %(rig2)s false)
        (Class|BPDemoAmbSC|Switch :self %(amb)s :NewClip %(amb2)s)
        %(from)s
        %(tt0)s
        %(said0)s
        %(ph7)s
        %(pt0)s
        %(ptravel)s))
    (:7
      (if (and (not %(said)s) (>= _pt %(vodelay)s))
        %(said1)s
        (Class|BPDemoVoiceSC|Say :self %(voice)s :Clip (select (== %(choice)s 1) %(vob)s (select (== %(choice)s 3) %(voh)s %(vod)s)))
        (elif (and %(said)s (and (>= _pt 2.0) (>= %(qt)s %(gap)s)))
          (Class|BPDemoHudKitSC|HudInstall %(kit)s)
          %(said0)s
          %(ph8)s
          %(pt0)s)))
    (:8
      (if (and (not %(said)s) (>= _pt 2.5))
        %(said1)s
        (Class|BPDemoVoiceSC|Say :self %(voice)s :Clip %(vom)s)
        (elif (and %(said)s (and (>= _pt 3.0) (>= %(qt)s %(gap)s)))
          (Class|BPDemoVoiceSC|Say :self %(voice)s :Clip %(vor)s)
          %(ph9)s
          %(pt0)s)))
    (:9
      (if (and (>= _pt 1.0) (>= %(qt)s 0.6))
        (Rendering|Material|SetColorParameterValueOnMaterials %(veil)s "CTop" %(ctopx)s)
        (Rendering|Material|SetColorParameterValueOnMaterials %(veil)s "CHor" %(chorx)s)
        %(ph10)s
        %(pt0)s
        %(pblack)s))
    (:10
      (Audio|SetSubmixOutputVolume(lineargain) %(mm)s (- 1.0 (Math|Float|MapRangeClamped _pt 3.0 6.0 0.0 1.0)))
      (if (>= _pt 6.5)
        (CallFunction|MenuRobot)
        %(ph11)s
        %(pt0)s
        %(popen)s
        (if (not %(robotm)s)
          (Game|OpenLevel(byName) (select (== %(choice)s 1) %(la)s (select (== %(choice)s 3) %(lc)s %(lb)s))))))
    (:11
      (if (and %(robotm)s (>= _pt 30.0))
        %(pt0)s
        %(pnolink)s
        (Game|OpenLevel(byName) "L_Demo_Menu")))))
''' % dict(mm=D('MasterMix'), ctopx='(select (== %s 1) %s (select (== %s 3) %s %s))' % (Z('Choice'), M('TopA'), Z('Choice'), D('TopC'), M('TopB')),
           chorx='(select (== %s 1) %s (select (== %s 3) %s %s))' % (Z('Choice'), M('HorA'), Z('Choice'), D('HorC'), M('HorB')),
           qt=D('QuietT'), gap=D('VoGap'), qtp=DS('QuietT', '(select %s 0.0 (+ %s _dt))' % (SPEAK, D('QuietT'))),
           bc=D('BtnC'), voh=D('VoHeart'), lc=D('LevelC'), vodelay=D('VoDelay'), rig2=D('Rig2'), lpset2=DS('LastPressN2', '(Class|BPSeqRigSC|GetResPressN %s)' % D('Rig2')), vom=D('VoMeasure'), robotm=D('RobotM'), pnolink=P('DEMO: robot sin visor 30 s, vuelve al menu'), pt=Z('PT'), rig=Z('Rig'), bs=Z('BtnStart'), ba=Z('BtnA'), bb=Z('BtnB'), ph=Z('Phase'), rt=Z('RT'),
           rtp=ZS('RT', '(+ %s _dt)' % Z('RT')), ptp=ZS('PT', '(+ %s _dt)' % Z('PT')), mok='(Variables|Z-Estado|GetMirrorOk)',
           ph1=ZS('Phase', '1'), ph2=ZS('Phase', '2'), ph4=ZS('Phase', '4'), ph7=ZS('Phase', '7'), ph8=ZS('Phase', '8'),
           ph9=ZS('Phase', '9'), ph10=ZS('Phase', '10'), ph11=ZS('Phase', '11'), pt0=ZS('PT', '0.0'),
           lpset=ZS('LastPressN', '(Class|BPSeqRigSC|GetResPressN _rig)'),
           hstart=HINT('HintStart'), hpick=HINT('HintPick'), miback=M('MIBack'), mistart=M('MIStart'),
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

ORDER = ['Boot', 'Place', 'Choose', 'VeilFx', 'TitleFx', 'Pick', 'HoverFx', 'TravelStep', 'MenuRobot', 'RenderPctStep', 'MenuTick']
EVG = '''(event EventBeginPlay
  (CallFunction|Boot))

(event EventTick (DeltaSeconds)
  (CallFunction|MenuTick :Dt DeltaSeconds))
'''
