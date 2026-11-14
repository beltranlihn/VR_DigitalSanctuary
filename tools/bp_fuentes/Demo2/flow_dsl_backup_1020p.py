# flow_dsl.py - BP_DemoFlow_SC: el director de cada experiencia de la demo (guion de Beltran 2026-10-19).
# Reemplaza en L_Demo_Breath / L_Demo_Draw al ensayo (BP_StageRunner_SC) y al panel viejo (BP_DemoInstr_SC).
# Exp 0 = Breath, 1 = Draw. Fases: 0 intro (velo + titulo) ... 15-19 cierre comun (VO final, plop del HUD, resultados, negro, menu).
D = lambda n: '(Variables|Default|Get%s)' % n
DS = lambda n, x: '(Variables|Default|Set%s %s)' % (n, x)
P = lambda s: '(Development|PrintString "%s" :bPrintToScreen false)' % s
CAM = '(Camera|GetCameraLocation (Game|GetPlayerCameraManager 0))'
CAMROT = '(Camera|GetCameraRotation (Game|GetPlayerCameraManager 0))'
AG = lambda a, i: '(Utilities|Array|Get(acopy) %s %s)' % (a, i)
EASE = lambda k: '(Math|Float|FInterpEaseInOut 0.0 1.0 %s 2.0)' % k
MAP = lambda v, a, b: '(Math|Float|MapRangeClamped %s %s %s 0.0 1.0)' % (v, a, b)
BTN = '/Game/SoulCharger/Shared/Results/Blueprints/BP_ShareButton_SC.BP_ShareButton_SC_C'
GOPH = lambda n: '%s\n        %s' % (DS('Phase', str(n)), DS('PT', '0.0'))
SAY = lambda clip: '(Class|BPDemoVoiceSC|Say :self %s :Clip %s)' % (D('Voice'), clip)
SPEAK = '(Class|BPDemoVoiceSC|GetSpeaking %s)' % D('Voice')
CODES = {}

CODES['FBoot'] = '''(fn FBoot ()
  %(card)s
  %(go)s
  %(ped)s
  %(rig)s
  %(voice)s
  %(kit)s
  %(amb)s
  %(res)s
  %(bstage)s
  %(brig)s
  %(tool)s
  %(tb)s
  %(pstart)s
  (Transformation|SetAbsolute %(veil)s true true true)
  (Transformation|SetAbsolute %(title)s true true true)
  (Rendering|Material|SetColorParameterValueOnMaterials %(veil)s "CTop" %(ctop)s)
  (Rendering|Material|SetColorParameterValueOnMaterials %(veil)s "CHor" %(chor)s)
  (Rendering|Material|SetMaterial %(title)s 0 %(tmi)s)
  %(ph)s
  %(rt)s
  %(pt)s
  (if (== %(exp)s 1)
    (Class|BPDemoHudKitSC|SetTimeLeft :self %(kitv)s :TimeLeft %(dtime)s))
  (if (== %(exp)s 0)
    (Rendering|SetActorHiddenInGame (Actor|GetActorOfClass "/SC_Breath/Blueprints/BP_BreathBlob_SC.BP_BreathBlob_SC_C") true)
    (Rendering|SetActorHiddenInGame (Actor|GetActorOfClass "/SC_Breath/Blueprints/BP_Pacer_SC.BP_Pacer_SC_C") true))
  (Development|PrintString (Utilities|String|Append "DEMOFLOW: arranca la experiencia " (Utilities|String|ToString(Integer) %(exp)s)) :bPrintToScreen false))
''' % dict(card=DS('Card', AG('(Actor|GetAllActorsOfClassWithTag "%s" "demo_instr")' % BTN, 0)),
           go='''(bind _gos (Actor|GetAllActorsOfClassWithTag "%s" "demo_go"))
  (if (> (Utilities|Array|Length _gos) 0)
    %s)''' % (BTN, DS('Go', AG('_gos', 0))),
           ped=DS('Pedestal', AG('(Actor|GetAllActorsWithTag "demo_pedestal")', 0)),
           rig=DS('Rig', '(Actor|GetActorOfClass "/SC_Sequencer/Blueprints/BP_SeqRig_SC.BP_SeqRig_SC_C")'),
           voice=DS('Voice', '(Actor|GetActorOfClass "/Game/SoulCharger/Demo/Blueprints/BP_DemoVoice_SC.BP_DemoVoice_SC_C")'),
           kit=DS('Kit', '(Actor|GetActorOfClass "/Game/SoulCharger/Demo/Blueprints/BP_DemoHudKit_SC.BP_DemoHudKit_SC_C")'),
           amb=DS('Amb', '(Actor|GetActorOfClass "/Game/SoulCharger/Demo/Blueprints/BP_DemoAmb_SC.BP_DemoAmb_SC_C")'),
           res=DS('Results', '(Actor|GetActorOfClass "/Game/SoulCharger/Demo/Blueprints/BP_DemoResults_SC.BP_DemoResults_SC_C")'),
           bstage=DS('BStage', '(Actor|GetActorOfClass "/Game/SoulCharger/Mechanics/Breath/Blueprints/BP_BreathStage_SC.BP_BreathStage_SC_C")'),
           brig=DS('BRig', '(Actor|GetActorOfClass "/SC_Breath/Blueprints/BP_BreathRig_SC.BP_BreathRig_SC_C")'),
           tool=DS('Tool', '(Actor|GetActorOfClass "/Game/SoulCharger/Shared/UserTool/BP_UserTool_SC.BP_UserTool_SC_C")'),
           tb=DS('TB', '(Actor|GetActorOfClass "/SC_Draw/Blueprints/BP_TBDirector_NC.BP_TBDirector_NC_C")') + chr(10) + '  ' + DS('HM', '(Actor|GetActorOfClass "/Game/SoulCharger/Mechanics/Heart/Blueprints/BP_HeartManager_SC.BP_HeartManager_SC_C")'),
           pstart=DS('PStart', '(Transformation|GetActorLocation (Actor|GetActorOfClass "/Script/Engine.PlayerStart"))') + chr(10) + '  ' + DS('PsYaw', '(.yaw (Transformation|GetActorRotation (Actor|GetActorOfClass "/Script/Engine.PlayerStart")))'),
           veil=D('Veil'), title=D('Title'), ctop=D('CTop'), chor=D('CHor'), tmi=D('TitleMI'),
           ph=DS('Phase', '0'), rt=DS('RT', '0.0'), pt=DS('PT', '0.0'), exp=D('Exp'), kitv=D('Kit'), dtime=D('DrawTime'))

CODES['FHands'] = '''(fn FHands ()
  (Utilities|IsValid (Game|GetPlayerPawn 0)
    (:"Is Valid"
      (for _c (Actor|GetComponentsByClass (Game|GetPlayerPawn 0) "/Script/Engine.SkeletalMeshComponent")
        (if (Utilities|String|Contains (Utilities|GetObjectName _c) "HandRight")
          %s)
        (if (Utilities|String|Contains (Utilities|GetObjectName _c) "HandLeft")
          %s)))))
''' % (DS('HandR', '(Transformation|GetAttachParent _c)'), DS('HandL', '(Transformation|GetAttachParent _c)'))

CODES['EnsureHands'] = '''(fn EnsureHands ()
  (Utilities|IsValid %s
    (:"Is Not Valid"
      (CallFunction|FHands))))
''' % D('HandL')

CODES['FVeil'] = '''(fn FVeil ()
  (bind _rt %(rt)s)
  (bind _ph %(ph)s)
  (bind _open (- 1.0 %(eopen)s))
  (bind _close %(eclose)s)
  (bind _a (select (<= _ph 1) _open (select (== _ph 18) _close (select (>= _ph 19) 1.0 0.0))))
  (bind _lt %(rt)s)
  (Transformation|SetWorldLocation %(veil)s %(cam)s)
  (Rendering|Material|SetScalarParameterValueOnMaterials %(veil)s "Amount" _a)
  (Rendering|Material|SetScalarParameterValueOnMaterials %(veil)s "Floor" (select (or (> _a 0.985) (>= _ph 18)) 0.0 0.02))
  (Rendering|SetVisibility %(veil)s (> _a 0.001))
  (Rendering|Material|SetScalarParameterValueOnMaterials %(title)s "LT" _lt)
  (Rendering|Material|SetScalarParameterValueOnMaterials %(title)s "Reveal" %(erev)s)
  (Rendering|Material|SetScalarParameterValueOnMaterials %(title)s "Out" %(eout)s)
  (Rendering|SetVisibility %(title)s (and (< _lt %(hide)s) (<= _ph 1))))
''' % dict(rt=D('RT'), ph=D('Phase'), veil=D('Veil'), title=D('Title'), cam=CAM, hide=D('TitleHide'),
           eopen=EASE(MAP('_rt', D('VeilA0'), D('VeilA1'))), eclose=EASE(MAP(D('PT'), '0.0', '2.5')),
           erev=EASE(MAP('_lt', D('TitleR0'), D('TitleR1'))), eout=EASE(MAP('_lt', D('TitleO0'), D('TitleO1'))))

CODES['FPlaceTitle'] = '''(fn FPlaceTitle ()
  (bind _tps (Actor|GetAllActorsWithTag %(tag)s))
  (bind _cz (.z %(cam)s))
  (if (> (Utilities|Array|Length _tps) 0)
    (bind _tp (Utilities|Array|Get(acopy) _tps 0))
    (Transformation|SetWorldLocationAndRotation %(title)s (+ (Transformation|GetActorLocation _tp) (Math|Vector|MakeVector 0.0 0.0 (- _cz (+ (.z %(ps)s) %(eye)s)))) (Math|Rotator|CombineRotators (Math|Rotator|MakeRotator 90.0 0.0 90.0) (Math|Rotator|MakeRotator 0.0 0.0 (.yaw (Transformation|GetActorRotation _tp)))))
    (Transformation|SetWorldScale3D %(title)s (Math|Vector|MakeVector 4.0 1.0 1.0))))
''' % dict(tag=D('TagTitle'), cam=CAM, title=D('Title'), ps=D('PStart'), eye=D('EyeRef'))

CODES['FPanel'] = '''(fn FPanel ()
  (bind _plate (Class|BPShareButtonSC|GetPlate %(card)s))
  (Rendering|Material|SetMaterial _plate 1 (Utilities|Array|Get(acopy) %(pages)s %(page)s))
  (if (> (Utilities|Array|Length %(imgs)s) %(page)s)
    (Rendering|Material|SetMaterial _plate 2 (Utilities|Array|Get(acopy) %(imgs)s %(page)s)))
  (Rendering|Material|SetMaterial _plate 3 %(ring)s)
  (CallFunction|SayPage)
  (Development|PrintString (Utilities|String|Append "DEMOFLOW: pagina " (Utilities|String|ToString(Integer) %(page)s)) :bPrintToScreen false))
''' % dict(card=D('Card'), pages=D('Pages'), page=D('Page'), imgs=D('Images'), ring=D('WinRingMat'))

CODES['ShowPanel'] = '''(fn ShowPanel ()
  (bind _dz (- (.z %(cam)s) (+ (.z %(ps)s) %(eye)s)))
  (bind _yaw %(psyaw)s)
  (bind _fwd (Math|Vector|MakeVector (Math|Trig|Cos(Degrees) _yaw) (Math|Trig|Sin(Degrees) _yaw) 0.0))
  (Transformation|SetActorLocation %(card)s (+ (Transformation|GetActorLocation %(card)s) (Math|Vector|MakeVector 0.0 0.0 _dz)) false true)
  (CallFunction|GoAdjust)
  (Transformation|SetActorLocationAndRotation %(ped)s (+ %(cam)s (+ (* _fwd %(rf)s) (Math|Vector|MakeVector 0.0 0.0 (* -1.0 %(rd)s)))) (Math|Rotator|MakeRotator 0.0 0.0 (+ _yaw 180.0)) false true)
  %(pbase)s
  %(pyaw)s
  %(page0)s
  (CallFunction|FPanel)
  (Class|BPShareButtonSC|Appear %(card)s)
  (Rendering|SetActorHiddenInGame %(ped)s false)
  (if (or (== %(exp)s 0) (== %(exp)s 2))
    (Class|BPCAppearLuzSC|Prepare (Class|BPBioSensorArtSC|GetAppear (Utilities|Casting|CastToBP_BioSensorArt_SC %(ped)s)))
    (Class|BPCAppearLuzSC|Appear (Class|BPBioSensorArtSC|GetAppear (Utilities|Casting|CastToBP_BioSensorArt_SC %(ped)s))))
  %(p)s)
''' % dict(cam=CAM, ps=D('PStart'), eye=D('EyeRef'), psyaw=D('PsYaw'), card=D('Card'), ped=D('Pedestal'),
           rf=D('ReachFwd'), rd=D('ReachDown'), page0=DS('Page', '0'), pyaw=DS('PedYaw', '(+ _yaw 180.0)'), pbase=DS('PedBase', '(Transformation|GetActorLocation %s)' % D('Pedestal')), exp=D('Exp'), p=P('DEMOFLOW: panel y objeto al frente'))

CODES['GoAdjust'] = '''(fn GoAdjust ()
  (bind _dz (- (.z %(cam)s) (+ (.z %(ps)s) %(eye)s)))
  (Utilities|IsValid %(go)s
    (:"Is Valid"
      (Transformation|SetActorLocation %(go)s (+ (Transformation|GetActorLocation %(go)s) (Math|Vector|MakeVector 0.0 0.0 _dz)) false true))))
''' % dict(cam=CAM, ps=D('PStart'), eye=D('EyeRef'), go=D('Go'))

CODES['GrabStep'] = '''(fn GrabStep ()
  (CallFunction|PedSpin)
  (bind _pl (Transformation|GetActorLocation %(ped)s))
  (bind _dr (Math|Vector|Distance(Vector) (Transformation|GetWorldLocation %(hr)s) _pl))
  (bind _dl (Math|Vector|Distance(Vector) (Transformation|GetWorldLocation %(hl)s) _pl))
  (bind _auto (and (> %(ah)s 0) (>= %(pt)s 2.0)))
  (bind _rem (>= %(rp)s 2))
  (bind _late (and (> %(gw)s 0.0) (and (>= %(pt)s %(gw)s) (< %(rp)s 2))))
  (if (or (< _dr %(tr)s) (or (and _auto (== %(ah)s 1)) (or (and _rem %(rr)s) _late)))
    %(r1)s
    (CallFunction|Grab)
    (elif (or (< _dl %(tr)s) (or (and _auto (== %(ah)s 2)) (and _rem (not %(rr)s))))
      %(r0)s
      (CallFunction|Grab))))
''' % dict(ped=D('Pedestal'), hr=D('HandR'), hl=D('HandL'), ah=D('AutoHand'), pt=D('PT'), tr=D('TouchRadius'),
           r1=DS('Right', 'true'), r0=DS('Right', 'false'), rp=D('RemotePhase'), rr=D('RemoteRight'), gw=D('GrabWait'))

# Grab: haptico de la mano que toma (2026-10-20, pedido de Beltran) = BP_SeqRig_SC.Pulse, el de la Obra. Lo dispara FlowTick 0,12 s
# despues (PulsePend): en el cuadro del agarre la etapa corta la haptica de las dos manos y se comia el pulso.
CODES['Grab'] = '''(fn Grab ()
  (Development|PrintString (Utilities|String|Append "DEMOFLOW: tomado con la mano " (select %(r)s "derecha" "izquierda")) :bPrintToScreen false)
  (Class|BPSeqRigSC|SetRightHanded :self %(rig)s :bRightHanded %(r)s)
  (if (== %(exp)s 0)
    (Rendering|SetActorHiddenInGame %(ped)s true)
    (Class|BPUserToolSC|ShowMando :self %(tool)s :Right %(r)s)
    (Class|BPUserToolSC|ToSensor :self %(tool)s :Color %(sc)s)
    (Class|BPBreathRigSC|SetHandedness :self %(brig)s :bRightSide %(r)s)
    (elif (== %(exp)s 2)
      (Rendering|SetActorHiddenInGame %(ped)s true)
      (Class|BPUserToolSC|ShowMando :self %(tool)s :Right %(r)s)
      (Class|BPUserToolSC|ToSensor :self %(tool)s :Color %(sc)s)
      (Class|BPHeartManagerSC|SetAutoHand :self %(hm)s :bAutoHand false)
      (Class|BPHeartManagerSC|SetRightHand :self %(hm)s :bRightHand %(r)s)
      (Class|BPHeartManagerSC|StageIntro %(hm)s)
      (Class|BPHeartManagerSC|ScapeGo :self %(hm)s :D 0.0)
      (else
      (Rendering|SetActorHiddenInGame %(ped)s true)
      (Class|BPTBDirectorNC|SetHandedness :self %(tb)s :LeftHanded (not %(r)s))
      (Class|BPTBDirectorNC|StageIntro %(tb)s))))
  %(pp1)s
  %(go)s)
''' % dict(r=D('Right'), rig=D('Rig'), exp=D('Exp'), ped=D('Pedestal'), tool=D('Tool'), sc=D('SensorColor'), brig=D('BRig'), tb=D('TB'),
           go=GOPH(2), hm=D('HM'), pp1=DS('PulsePend', 'true'))

CODES['SaveHands'] = '''(fn SaveHands ()
  %s
  (Utilities|Array|Clear %s)
  (for _array_element %s
    (Utilities|Array|Add %s (Class|SceneComponent|GetHiddeninGame _array_element))))
''' % (DS('HandComps', '(Actor|GetComponentsByClass (Game|GetPlayerPawn 0) "/Script/Engine.SkeletalMeshComponent")'),
       D('HandHidden'), D('HandComps'), D('HandHidden'))

CODES['RestoreHands'] = '''(fn RestoreHands ()
  (for _index (range (Utilities|Array|Length %s))
    (Development|SetHiddeninGame (Utilities|Array|Get(acopy) %s _index) (Utilities|Array|Get(acopy) %s _index))))
''' % (D('HandComps'), D('HandComps'), D('HandHidden'))

CODES['PickGo'] = '''(fn PickGo ()
  (bind _go %(go)s)
  (bind _rig %(rig)s)
  (bind _auto (or (and (> %(ag)s 0.0) (>= %(pt)s %(ag)s)) (or (>= %(rp)s 6) (and (> %(gow)s 0.0) (>= %(pt)s %(gow)s)))))
  (bind _hov (and (== (Class|BPSeqRigSC|GetBeamHitActor _rig) _go) (>= (Class|BPCAppearLuzSC|GetAppearT (Class|BPShareButtonSC|GetAppearLuz _go)) 0.999)))
  (bind _rp (Class|BPSeqRigSC|GetResPressN _rig))
  (Class|BPShareButtonSC|SetHover _go _hov)
  (if (or _auto (!= _rp %(lp)s))
    %(lps)s
    (if (or _auto _hov)
      (Class|BPShareButtonSC|Press _go)
      (Class|BPSeqRigSC|Pulse :self _rig :bRight (Class|BPSeqRigSC|GetRightHanded _rig))
      %(p)s
      %(goph)s)))
''' % dict(go=D('Go'), rig=D('Rig'), ag=D('AutoGo'), pt=D('PT'), lp=D('LastPressN'), lps=DS('LastPressN', '_rp'),
           p=P('DEMOFLOW: START'), goph=GOPH(6), rp=D('RemotePhase'), gow=D('GoWait'), right=D('Right'))

CODES['BreathCount'] = '''(fn BreathCount ()
  (bind _s (Class|BPBreathRigSC|GetBreathSigned %s))
  (if (< _s -0.3)
    %s)
  (if (and %s (> _s 0.4))
    %s
    %s
    (Development|PrintString (Utilities|String|Append "DEMOFLOW: respiracion " (Utilities|String|ToString(Integer) %s)) :bPrintToScreen false)))
''' % (D('BRig'), DS('Low', 'true'), D('Low'), DS('Low', 'false'), DS('BreathN', '(+ %s 1)' % D('BreathN')), D('BreathN'))

CODES['BreathTick'] = '''(fn BreathTick (Dt)
  (bind _pt %(pt)s)
  (switch Utilities|FlowControl|Switch|SwitchonInt %(ph)s
    (:0
      (if (and (>= %(rt)s 0.1) (not %(env)s))
        %(env1)s
        (Class|BPBreathStageSC|StageEnv %(bstage)s))
      (if (>= %(rt)s %(pat)s)
        (CallFunction|ShowPanel)
        %(g1)s))
    (:1
      (CallFunction|GrabStep))
    (:2
      (if (>= _pt 1.8)
        %(page1)s
        (CallFunction|FPanel)
        (Class|BPBreathRigSC|SetRigActive :self %(brig)s :bOn true)
        %(zone0)s
        %(g3)s))
    (:3
      %(zone)s
      (if (or (and (>= %(zt)s 1.5) (not %(spk)s)) (or (>= %(rp)s 4) (or (and (> %(zw)s 0.0) (>= _pt %(zw)s)) (and (> %(ag)s 0.0) (>= _pt %(ag)s)))))
        %(page2)s
        (CallFunction|FPanel)
        %(bn0)s
        %(low0)s
        %(g4)s))
    (:4
      (CallFunction|BreathCount)
      (if (or (and (>= %(bn)s %(breaths)s) (not %(spk)s)) (or (>= _pt %(bw)s) (or (>= %(rp)s 5) (and (> %(ag)s 0.0) (>= _pt %(ag)s)))))
        %(page3)s
        (CallFunction|FPanel)
        %(g5)s))
    (:5
      (if (or (and (>= _pt 2.5) (not %(spk)s)) (or (>= _pt 25.0) (or (>= %(rp)s 6) (and (> %(ag)s 0.0) (>= _pt %(ag)s)))))
        %(p5)s
        %(g6)s))
    (:6
      (if (>= _pt 1.0)
        (Class|BPShareButtonSC|Vanish %(card)s)
        %(g7)s))
    (:7
      (if (>= _pt 1.2)
        (Rendering|SetActorHiddenInGame (Actor|GetActorOfClass "/SC_Breath/Blueprints/BP_BreathBlob_SC.BP_BreathBlob_SC_C") false)
        (Rendering|SetActorHiddenInGame (Actor|GetActorOfClass "/SC_Breath/Blueprints/BP_Pacer_SC.BP_Pacer_SC_C") false)
        (Class|BPBreathStageSC|StageIntro %(bstage)s)
        %(say1)s
        %(p7)s
        %(g8)s))
    (:8
      (if (>= _pt 2.0)
        (Class|BPBreathStageSC|StageBegin %(bstage)s)
        %(st0)s
        %(vo20)s
        %(req0)s
        %(p8)s
        %(g9)s))
    (:9
      %(stp)s
      (if (and (not %(vo2)s) (>= %(st)s (- (Class|BPBreathStageSC|GetExploreTime %(bstage)s) 3.2)))
        %(vo21)s
        %(say2)s)
      (if (and (not %(req)s) (or (>= %(st)s %(tope)s) (>= %(rp)s 10)))
        %(req1)s
        (Class|BPBreathStageSC|StageRequestEnd %(bstage)s)
        %(ptope)s)
      (if (or (Class|BPBreathStageSC|GetStageDone %(bstage)s) (and %(req)s (>= %(st)s (+ %(tope)s 30.0))))
        (Class|BPBreathStageSC|StageOutro %(bstage)s)
        (Class|BPUserToolSC|Release %(tool)s)
        %(pdone)s
        %(g10)s))
    (:10
      (if (and (not %(hon)s) (>= _pt 1.2))
        (CallFunction|HandsBack))
      (if (>= _pt 2.8)
        %(say3)s
        %(g15)s))))
''' % dict(pt=D('PT'), ph=D('Phase'), rt=D('RT'), env=D('Env'), env1=DS('Env', 'true'), bstage=D('BStage'), pat=D('PanelAt'),
           g1=GOPH(1), g3=GOPH(3), g4=GOPH(4), g5=GOPH(5), g6=GOPH(6), g7=GOPH(7), g8=GOPH(8), g9=GOPH(9), g10=GOPH(10), g15=GOPH(15),
           p5=P('DEMOFLOW: Breath, termino la ultima instruccion: se va el panel'),
           page1=DS('Page', '1'), page2=DS('Page', '2'), page3=DS('Page', '3'), brig=D('BRig'), zone0=DS('ZoneT', '0.0'),
           zone=DS('ZoneT', '(select (Class|BPBreathRigSC|GetZone %s) (+ %s Dt) 0.0)' % (D('BRig'), D('ZoneT'))), zt=D('ZoneT'),
           ag=D('AutoGo'), bn0=DS('BreathN', '0'), low0=DS('Low', 'false'), bn=D('BreathN'), breaths=D('Breaths'), bw=D('BreathWait'),
           rig=D('Rig'), lp=DS('LastPressN', '(Class|BPSeqRigSC|GetResPressN %s)' % D('Rig')), go=D('Go'), card=D('Card'),
           say1=SAY(D('Vo1')), say2=SAY(D('Vo2')), say3=SAY(D('Vo3')), st0=DS('StageT', '0.0'), vo20=DS('Vo2Done', 'false'),
           req0=DS('Req', 'false'), stp=DS('StageT', '(+ %s Dt)' % D('StageT')), vo2=D('Vo2Done'), st=D('StageT'), vo21=DS('Vo2Done', 'true'),
           req=D('Req'), req1=DS('Req', 'true'), tope=D('TopeS'), rp=D('RemotePhase'), zw=D('ZoneWait'),
           p7=P('DEMOFLOW: StageIntro (metaball)'), p8=P('DEMOFLOW: StageBegin'), ptope=P('DEMOFLOW: tope, se pide el cierre'),
           pdone=P('DEMOFLOW: la etapa termino, StageOutro'), spk=SPEAK, right=D('Right'), tool=D('Tool'), hon=D('HandsOn'))


# HeartTick (Exp 2, 2026-10-20): RECOGNIZING. (noche: la esfera sube recien cuando se va el panel; el 1.0 va cableado por Max:
# un literal numerico a una funcion propia se pierde, dsl.md 4) El latido es el de la Obra (BP_HeartManager_SC): sensor al pecho + quietud -> umbral ->
# un pulso cada BeatDiv latidos; cierra solo (StageBeats + la vuelta del mar) o al tope (StageRequestEnd). Fases 0-5 (2026-10-20 tarde:
# dos paginas; la 2 tiene la figura que late, HeartFig, y se va a los HeartPulses pulsos). Sin Alma en el nivel su
# StageVO queda en silencio: las voces las dice este director (PageVo, Vo1 al primer pulso, Vo2 al empezar la vuelta y al menos 10 s despues del panel, Vo3 al final).
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
        (Class|BPHeartManagerSC|ScapeGo :self %(hm)s :D 0.0)
        %(fz0)s
        %(g3)s))
    (:3
      (CallFunction|HeartFig)
      (if (or (and (>= (Class|BPHeartManagerSC|GetBeatCount %(hm)s) %(hp)s) (>= _pt 1.0)) (or (>= %(rp)s 4) (or (and (> %(zw)s 0.0) (>= _pt %(zw)s)) (and (> %(ag)s 0.0) (>= _pt %(ag)s)))))
        (Class|BPShareButtonSC|Vanish %(card)s)
        (Class|BPHeartManagerSC|ScapeGo :self %(hm)s :D (Math|Float|Max(Float) 1.0 0.0))
        %(st0)s
        %(req0)s
        %(h10)s
        %(h20)s
        %(p7)s
        %(g4)s))
    (:4
      %(stp)s
      (if (and (not %(h1)s) (and (>= (Class|BPHeartManagerSC|GetBeatCount %(hm)s) 1) (not %(spk)s)))
        %(h11)s
        %(say1)s)
      (if (and (not %(h2)s) (and (>= (Class|BPHeartManagerSC|GetBeatCount %(hm)s) (Class|BPHeartManagerSC|GetOrbitAtBeat %(hm)s)) (and (>= %(st)s 10.0) (not %(spk)s))))
        %(h21)s
        %(say2)s)
      (if (and (not %(req)s) (or (>= %(st)s %(tope)s) (>= %(rp)s 5)))
        %(req1)s
        (Class|BPHeartManagerSC|StageRequestEnd %(hm)s)
        %(ptope)s)
      (if (or (Class|BPHeartManagerSC|GetStageDone %(hm)s) (and %(req)s (>= %(st)s (+ %(tope)s 30.0))))
        (Class|BPHeartManagerSC|StageOutro %(hm)s)
        %(pdone)s
        %(g5)s))
    (:5
      (if (and (not %(hon)s) (>= _pt 1.2))
        (CallFunction|HandsBack))
      (if (>= _pt 2.8)
        %(say3)s
        %(g15)s))))
""" % dict(hon=D('HandsOn'), pt=D('PT'), ph=D('Phase'), rt=D('RT'), env=D('Env'), env1=DS('Env', 'true'), hm=D('HM'), pat=D('PanelAt'),
           g1=GOPH(1), g3=GOPH(3), g4=GOPH(4), g5=GOPH(5), g15=GOPH(15), hp=D('HeartPulses'), fz0=DS('FigZ', '0.0'),
           page1=DS('Page', '1'), page2=DS('Page', '2'), zone0=DS('ZoneT', '0.0'),
           zone=DS('ZoneT', '(select (Class|BPHeartManagerSC|GetHeartZone %s) (+ %s Dt) 0.0)' % (D('HM'), D('ZoneT'))), zt=D('ZoneT'),
           spk=SPEAK, rp=D('RemotePhase'), zw=D('ZoneWait'), ag=D('AutoGo'), card=D('Card'),
           st0=DS('StageT', '0.0'), req0=DS('Req', 'false'), h10=DS('SaidH1', 'false'), h20=DS('SaidH2', 'false'),
           stp=DS('StageT', '(+ %s Dt)' % D('StageT')), st=D('StageT'), h1=D('SaidH1'), h11=DS('SaidH1', 'true'), h2=D('SaidH2'), h21=DS('SaidH2', 'true'),
           req=D('Req'), req1=DS('Req', 'true'), tope=D('TopeS'), say1=SAY(D('Vo1')), say2=SAY(D('Vo2')), say3=SAY(D('Vo3')),
           p7=P('DEMOFLOW: Heart, tres pulsos: se va el panel, el latido sigue'), ptope=P('DEMOFLOW: tope, se pide el cierre'),
           pdone=P('DEMOFLOW: la etapa termino, StageOutro'))

CODES['HeartFig'] = """(fn HeartFig ()
  %(fz)s
  (bind _plate (Class|BPShareButtonSC|GetPlate %(card)s))
  (Rendering|Material|SetScalarParameterValueOnMaterials _plate "Pulse" (Class|BPHeartManagerSC|GetBeatEnv %(hm)s))
  (Rendering|Material|SetScalarParameterValueOnMaterials _plate "Zone" %(fzg)s))
""" % dict(fz=DS('FigZ', '(Math|Interpolation|FInterpTo %s (select (Class|BPHeartManagerSC|GetHeartZone %s) 1.0 0.0) (Utilities|Time|GetWorldDeltaSeconds) 5.0)' % (D('FigZ'), D('HM'))),
           card=D('Card'), hm=D('HM'), fzg=D('FigZ'))

CODES['PracticeCut'] = '''(fn PracticeCut ()
  %(strokes)s
  (Utilities|Array|Clear %(sloc)s)
  (Utilities|Array|Clear %(scen)s)
  (for _s %(gs)s
    (Utilities|Array|Add %(sloc)s (Transformation|GetActorLocation _s))
    (bind (_o _e) (Collision|GetActorBounds _s false))
    (Utilities|Array|Add %(scen)s _o))
  %(sh0)s
  (Development|PrintString (Utilities|String|Append "DEMOFLOW: trazo de practica listo, trazos = " (Utilities|String|ToString(Integer) (Utilities|Array|Length %(gs)s))) :bPrintToScreen false))
''' % dict(strokes=DS('Strokes', '(Class|BPCTBToolNC|GetStrokeHistory (Class|BPTBDirectorNC|GetTBTool %s))' % D('TB')),
           sloc=D('StrokeLoc'), scen=D('StrokeCen'), gs=D('Strokes'), sh0=DS('ShrinkT', '0.0'))

CODES['ShrinkStep'] = '''(fn ShrinkStep (Dt)
  %(shp)s
  (bind _k (Math|Float|Clamp(Float) (/ %(sh)s 0.8) 0.0 1.0))
  (bind _s (Math|Float|Max(Float) (- 1.0 (* _k (* _k (- 3.0 (* 2.0 _k))))) 0.001))
  (for _i (range (Utilities|Array|Length %(gs)s))
    (Transformation|SetActorScale3D (Utilities|Array|Get(acopy) %(gs)s _i) (Math|Vector|MakeVector _s _s _s))
    (bind _c (Utilities|Array|Get(acopy) %(scen)s _i))
    (Transformation|SetActorLocation (Utilities|Array|Get(acopy) %(gs)s _i) (+ (+ _c (* (- (Utilities|Array|Get(acopy) %(sloc)s _i) _c) _s)) (Math|Vector|MakeVector 0.0 0.0 (* 15.0 (- 1.0 _s)))) false true)))
''' % dict(shp=DS('ShrinkT', '(+ %s Dt)' % D('ShrinkT')), sh=D('ShrinkT'), gs=D('Strokes'), sloc=D('StrokeLoc'), scen=D('StrokeCen'))

CODES['UndoAll'] = '''(fn UndoAll ()
  (bind _tool (Class|BPTBDirectorNC|GetTBTool %s))
  (for _i (range (Utilities|Array|Length %s))
    (Class|BPCTBToolNC|UndoLast _tool))
  (Class|BPTBDirectorNC|SetInkUsed :self %s :InkUsed 0.0))
''' % (D('TB'), D('Strokes'), D('TB'))

CODES['ShiftStart'] = '''(fn ShiftStart ()
  (bind _yaw %s)
  %s
  %s
  %s
  %s
  (CallFunction|LogPivot))
''' % (D('PsYaw'), DS('ShiftVec', '(Math|Vector|MakeVector (* %s (* -1.0 (Math|Trig|Sin(Degrees) _yaw))) (* %s (Math|Trig|Cos(Degrees) _yaw)) 0.0)' % (D('ShiftCm'), D('ShiftCm'))),
       DS('Shifted', 'true'), DS('ShiftT', '0.0'), DS('ShiftK', '0.0'))

# ShiftK se escribe AL FINAL: _d es un bind puro y se re-evalua en cada uso (gotcha 409)
# registro del efecto (no solo de la ejecucion): el pivote del dibujo antes de correrse y cuando aparecen los resultados
CODES['LogPivot'] = '''(fn LogPivot ()
  (Utilities|IsValid %s
    (:"Is Valid"
      (Development|PrintString (Utilities|String|Append "DEMOFLOW: pivote del dibujo " (Utilities|String|ToString(Vector) (Class|BPCTBToolNC|GetSketchPivot (Class|BPTBDirectorNC|GetTBTool %s)))) :bPrintToScreen false))))
''' % (D('TB'), D('TB'))

CODES['ShiftStep'] = '''(fn ShiftStep (Dt)
  (if (< %(st)s 1.6)
    %(stp)s
    (bind _k %(ease)s)
    (bind _d (* %(sv)s (- _k %(sk)s)))
    (bind _tool (Class|BPTBDirectorNC|GetTBTool %(tb)s))
    (Class|BPCTBToolNC|SketchApplyXf :self _tool :M (Math|Transform|MakeTransform _d (Math|Rotator|MakeRotator 0.0 0.0 0.0) (Math|Vector|MakeVector 1.0 1.0 1.0)))
    (Class|BPCTBToolNC|SetSketchPivot :self _tool :SketchPivot (+ (Class|BPCTBToolNC|GetSketchPivot _tool) _d))
    (CallFunction|MoveTable :D _d)
    %(sks)s))
''' % dict(st=D('ShiftT'), stp=DS('ShiftT', '(+ %s Dt)' % D('ShiftT')), ease=EASE(MAP(D('ShiftT'), '0.0', '1.5')),
           sv=D('ShiftVec'), sk=D('ShiftK'), sks=DS('ShiftK', '_k'), tb=D('TB'))

SKP = '(Class|BPCTBToolNC|GetSketchPhase (Class|BPTBDirectorNC|GetTBTool %s))' % D('TB')
CODES['DrawTick'] = '''(fn DrawTick (Dt)
  (bind _pt %(pt)s)
  (switch Utilities|FlowControl|Switch|SwitchonInt %(ph)s
    (:0
      (if (>= %(rt)s %(pat)s)
        (CallFunction|ShowPanel)
        %(g1)s))
    (:1
      (CallFunction|GrabStep))
    (:2
      (if (>= _pt 1.5)
        %(page1)s
        (CallFunction|FPanel)
        (Class|BPTBDirectorNC|StageBegin %(tb)s)
        (Class|BPTBDirectorNC|SetInkUsed :self %(tb)s :InkUsed 0.0)
        (if %(synth)s
          (Class|BPTBDirectorNC|DbgSynth %(tb)s))
        %(p2)s
        %(g3)s))
    (:3
      (bind _drw (Class|BPCTBToolNC|GetDrawing (Class|BPTBDirectorNC|GetTBTool %(tb)s)))
      (if (or (>= %(rp)s 4) (and (not _drw) (or (>= (Class|BPTBDirectorNC|GetInkUsed %(tb)s) %(pm)s) (or (and (> %(pw)s 0.0) (>= _pt %(pw)s)) (and (> %(ag)s 0.0) (>= _pt %(ag)s))))))
        (Class|BPTBDirectorNC|SetStageLock :self %(tb)s :bStageLock true)
        (CallFunction|PracticeCut)
        %(g4)s))
    (:4
      (CallFunction|ShrinkStep :Dt Dt)
      (if (>= %(sh)s 0.85)
        (CallFunction|UndoAll)
        (Class|BPShareButtonSC|Vanish %(card)s)
        (Class|BPTBDirectorNC|StageBegin %(tb)s)
        %(say1)s
        %(tt0)s
        %(req0)s
        %(tl)s
        (if %(synth)s
          (Class|BPTBDirectorNC|DbgSynth %(tb)s))
        %(p4)s
        %(g5)s))
    (:5
      %(ttp)s
      (Class|BPDemoHudKitSC|SetTimeLeft :self %(kit)s :TimeLeft (- %(dt)s %(tt)s))
      (if (and (not %(req)s) (or (>= %(tt)s %(dt)s) (>= %(rp)s 6)))
        %(req1)s
        (Class|BPTBDirectorNC|StageRequestEnd %(tb)s)
        %(ptope)s)
      (if (>= %(skp)s 1)
        %(sk0)s
        %(psave)s
        %(g6)s
        (elif (and %(req)s (or (Class|BPTBDirectorNC|GetStageDone %(tb)s) (>= %(tt)s (+ %(dt)s 30.0))))
          (Class|BPTBDirectorNC|StageOutro %(tb)s)
          (CallFunction|HandsBack)
          %(say3)s
          %(pnone)s
          %(g15)s)))
    (:6
      (if (and (not %(hon)s) (>= _pt (Class|BPTBDirectorNC|GetOutroTime %(tb)s)))
        (CallFunction|HandsBack))
      (if (>= %(skp)s 3)
        %(skt)s)
      (if (or (>= %(skt0)s %(turns)s) (>= _pt (* 2.0 %(turns)s)))
        (CallFunction|ShiftStart)
        %(say3)s
        (Class|BPDemoHudKitSC|HudPlop %(kit)s)
        (Class|BPDemoResultsSC|ResShow %(res)s)
        %(pshift)s
        %(g17)s))))
''' % dict(pt=D('PT'), ph=D('Phase'), rt=D('RT'), pat=D('PanelAt'), g1=GOPH(1), g3=GOPH(3), g4=GOPH(4), g5=GOPH(5), g6=GOPH(6), g15=GOPH(15),
           page1=DS('Page', '1'), tb=D('TB'), pm=D('PracticeM'), ag=D('AgoDraw') if False else D('AutoGo'), sh=D('ShrinkT'), card=D('Card'),
           say1=SAY(D('Vo1')), say3=SAY(D('Vo3')), tt0=DS('TimerT', '0.0'), req0=DS('Req', 'false'),
           tl='(Class|BPDemoHudKitSC|SetTimeLeft :self %s :TimeLeft %s)' % (D('Kit'), D('DrawTime')),
           ttp=DS('TimerT', '(+ %s Dt)' % D('TimerT')), kit=D('Kit'), dt=D('DrawTime'), tt=D('TimerT'), req=D('Req'), req1=DS('Req', 'true'),
           skp=SKP, sk0=DS('SketchT', '0.0'), skt=DS('SketchT', '(+ %s Dt)' % D('SketchT')), skt0=D('SketchT'), turns=D('SpinTurnsT'),
           p2=P('DEMOFLOW: a dibujar (trazo de practica)'), p4=P('DEMOFLOW: se fue el trazo de practica, arranca el reloj'),
           ptope=P('DEMOFLOW: se acabo el tiempo, se pide el cierre'), psave=P('DEMOFLOW: el dibujo se guarda y se presenta'),
           pshift=P('DEMOFLOW: el dibujo se corre a la derecha, a la vez se va el HUD y aparecen los resultados'), synth=D('TestSynth'),
           pnone=P('DEMOFLOW: sin dibujo, sin presentacion: al cierre'), rp=D('RemotePhase'), pw=D('PracticeWait'), hon=D('HandsOn'), res=D('Results'), g17=GOPH(17))

CODES['EndTick'] = '''(fn EndTick (Dt)
  (bind _pt %(pt)s)
  (switch Utilities|FlowControl|Switch|SwitchonInt (- %(ph)s 15)
    (:0
      (if (and (>= _pt 1.0) (not %(speak)s))
        (Class|BPDemoHudKitSC|HudPlop %(kit)s)
        %(g16)s))
    (:1
      (if (>= _pt 1.7)
        (Class|BPDemoResultsSC|ResShow %(res)s)
        (if (== %(exp)s 1)
          (CallFunction|LogPivot))
        %(g17)s))
    (:2
      (if (>= _pt %(hold)s)
        (Class|BPDemoResultsSC|ResHide %(res)s)
        (Rendering|Material|SetColorParameterValueOnMaterials %(veil)s "CTop" %(black)s)
        (Rendering|Material|SetColorParameterValueOnMaterials %(veil)s "CHor" %(black)s)
        (Class|BPDemoAmbSC|FadeAll %(amb)s)
        %(pblack)s
        %(g18)s))
    (:3
      (if (>= _pt 3.0)
        %(g19)s
        %(pmenu)s
        (if (not %(robot)s)
          (Game|OpenLevel(byName) %(menu)s)
          (else
            %(pwait)s))))))
''' % dict(pt=D('PT'), ph=D('Phase'), speak=SPEAK, kit=D('Kit'), res=D('Results'), hold=D('ResultsHold'), veil=D('Veil'), black=D('Black'),
           amb=D('Amb'), menu=D('MenuLevel'), g16=GOPH(16), g17=GOPH(17), g18=GOPH(18), g19=GOPH(19),
           pblack=P('DEMOFLOW: negro'), pmenu=P('DEMOFLOW: vuelve al menu'), robot=D('RobotMode'), exp=D('Exp'), pwait=P('DEMOFLOW: robot espera al visor (no abre el menu)'))

CODES['FindLink'] = """(fn FindLink ()
  (Utilities|IsValid %s
    (:"Is Not Valid"
      %s)))
""" % (D('MLink'), DS('MLink', '(Actor|GetActorOfClass "/Game/SoulCharger/Demo/Blueprints/BP_MirrorLink_SC.BP_MirrorLink_SC_C")'))

CODES['RemoteSync'] = """(fn RemoteSync ()
  (CallFunction|FindLink)
  (Utilities|IsValid %s
    (:"Is Valid"
      (if (and (== (Class|BPMirrorLinkSC|GetMode %s) 2) (>= (Utilities|Array|Length (Class|BPMirrorLinkSC|GetRStF %s)) 4))
        %s
        %s
        %s))))
""" % (D('MLink'), D('MLink'), D('MLink'), DS('RobotMode', 'true'),
       DS('RemotePhase', '(Math|Float|Truncate (Utilities|Array|Get(acopy) (Class|BPMirrorLinkSC|GetRStF %s) 2))' % D('MLink')),
       DS('RemoteRight', '(> (Utilities|Array|Get(acopy) (Class|BPMirrorLinkSC|GetRStF %s) 3) 0.5)' % D('MLink')))

CODES['RobotHold'] = """(fn RobotHold ()
  %s
  (Utilities|IsValid %s
    (:"Is Valid"
      (if (and (== (Class|BPMirrorLinkSC|GetMode %s) 2) (not (Class|BPMirrorLinkSC|GetPoseReady %s)))
        %s))))
""" % (DS('Hold', 'false'), D('MLink'), D('MLink'), D('MLink'), DS('Hold', 'true'))


# --- 2026-10-20 (tarde), pedidos de Beltran tras probar Draw en Unreal ---
# PedSpin: el sensor / el mando que flota gira suave (SpinDeg grados/s) y sube y baja BobCm, invitando a tomarlo
CODES['PedSpin'] = """(fn PedSpin ()
  (bind _tl (select (== %(exp)s 1) (* 0.35 %(tilt)s) %(tilt)s))
  (Transformation|SetActorLocationAndRotation %(ped)s (+ %(base)s (Math|Vector|MakeVector 0.0 0.0 (* %(bob)s (Math|Trig|Sin(Radians) (* %(pt)s 1.6))))) (Math|Rotator|MakeRotator (* _tl (Math|Trig|Sin(Radians) (* %(pt)s 0.9))) (* _tl (Math|Trig|Sin(Radians) (* %(pt)s 0.65))) (+ %(pyaw)s (* %(spin)s %(pt)s))) false true))
""" % dict(ped=D('Pedestal'), spin=D('SpinDeg'), base=D('PedBase'), bob=D('BobCm'), pt=D('PT'), exp=D('Exp'), tilt=D('TiltDeg'), pyaw=D('PedYaw'))
# SayPage: la voz de la pagina del panel (PageVo por instancia: Breath VO_IB1-4, Draw VO_ID1-2)
CODES['SayPage'] = """(fn SayPage ()
  (if (> (Utilities|Array|Length %(pv)s) %(page)s)
    (Class|BPDemoVoiceSC|Say :self %(voice)s :Clip (Utilities|Array|Get(acopy) %(pv)s %(page)s))))
""" % dict(pv=D('PageVo'), page=D('Page'), voice=D('Voice'))
# HandsBack: al irse los mandos del dibujo vuelven las manos (el director las escondia con bHidePawnHands)
CODES['HandsBack'] = """(fn HandsBack ()
  (if (not %(hon)s)
    %(hon1)s
    (for _c (Actor|GetComponentsByClass (Game|GetPlayerPawn 0) "/Script/Engine.SkeletalMeshComponent")
      (Rendering|SetVisibility _c true true)
      (Development|SetHiddeninGame _c false true))
    (Development|PrintString "DEMOFLOW: se fueron los mandos / el sensor, vuelven las manos" :bPrintToScreen false)
    (Utilities|IsValid %(tb)s
      (:"Is Valid"
        (Class|BPTBDirectorNC|SetHidePawnHands :self %(tb)s :bHidePawnHands false)))))
""" % dict(hon=D('HandsOn'), hon1=DS('HandsOn', 'true'), tb=D('TB'))
# MoveTable: la mesa del dibujo se corre con el dibujo
CODES['MoveTable'] = """(fn MoveTable (D)
  (bind _tbl (Class|BPCTBToolNC|GetDrawTable (Class|BPTBDirectorNC|GetTBTool %(tb)s)))
  (Utilities|IsValid _tbl
    (:"Is Valid"
      (Transformation|SetActorLocation _tbl (+ (Transformation|GetActorLocation _tbl) D) false true))))
""" % dict(tb=D('TB'))

CODES['FlowTick'] = '''(fn FlowTick (Dt)
  (bind _dt (Math|Float|Min(Float) Dt 0.0333))
  (CallFunction|RemoteSync)
  (CallFunction|RobotHold)
  (if (not %(hold)s)
    %(rtp)s
    %(ptp)s)
  (CallFunction|FVeil)
  (if (< %(rt)s 0.4)
    (CallFunction|FPlaceTitle))
  (CallFunction|EnsureHands)
  (if (and %(pp)s (>= %(pt)s 0.12))
    %(pp0)s
    (Class|BPSeqRigSC|Pulse :self %(rig)s :bRight %(right)s))
  (if %(shifted)s
    (CallFunction|ShiftStep :Dt _dt))
  (if (>= %(ph)s 15)
    (CallFunction|EndTick :Dt _dt)
    (elif (== %(exp)s 0)
      (CallFunction|BreathTick :Dt _dt)
      (elif (== %(exp)s 2)
        (CallFunction|HeartTick :Dt _dt)
        (else
          (CallFunction|DrawTick :Dt _dt))))))
''' % dict(rtp=DS('RT', '(+ %s _dt)' % D('RT')), ptp=DS('PT', '(+ %s _dt)' % D('PT')), rt=D('RT'), hold=D('Hold'), shifted=D('Shifted'), ph=D('Phase'), exp=D('Exp'),
           pp=D('PulsePend'), pp0=DS('PulsePend', 'false'), pt=D('PT'), rig=D('Rig'), right=D('Right'))

ORDER = ['PedSpin', 'SayPage', 'HandsBack', 'MoveTable', 'FBoot', 'FHands', 'EnsureHands', 'FVeil', 'FPlaceTitle', 'FPanel', 'GoAdjust', 'ShowPanel', 'Grab', 'GrabStep', 'SaveHands', 'RestoreHands',
         'PickGo', 'BreathCount', 'BreathTick', 'HeartFig', 'HeartTick', 'PracticeCut', 'ShrinkStep', 'UndoAll', 'LogPivot', 'ShiftStart', 'ShiftStep', 'DrawTick', 'EndTick', 'FindLink', 'RemoteSync', 'RobotHold', 'FlowTick']
EVG = '''(event EventBeginPlay
  (CallFunction|FBoot))

(event EventTick (DeltaSeconds)
  (CallFunction|FlowTick :Dt DeltaSeconds))
'''
# funciones con parametro Dt (float)
DT_FUNCS = ['BreathTick', 'HeartTick', 'ShrinkStep', 'ShiftStep', 'DrawTick', 'EndTick', 'FlowTick']
