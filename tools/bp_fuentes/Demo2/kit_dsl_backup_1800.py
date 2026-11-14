# kit_dsl.py - BP_DemoHudKit_SC: adapta el HUD de la Obra (BP_SoulHUD3D_SC) a la demo
V = lambda n: '(Variables|Default|Get%s)' % n
S = lambda n, x: '(Variables|Default|Set%s %s)' % (n, x)
HUDC = '/Game/SoulCharger/Shared/HUD/Blueprints/BP_SoulHUD3D_SC.BP_SoulHUD3D_SC_C'
RIGC = '/SC_Breath/Blueprints/BP_BreathRig_SC.BP_BreathRig_SC_C'
CAM = '(Camera|GetCameraLocation (Game|GetPlayerCameraManager 0))'
SETS = lambda c, p, x: '(Rendering|Material|SetScalarParameterValueonMaterials %s "%s" %s)' % (c, p, x)
SETV = lambda c, p, x: '(Rendering|Material|SetVectorParameterValueonMaterials %s "%s" %s)' % (c, p, x)
HAP = lambda a: ('(Game|Feedback|SetHapticsbyValue (Game|GetPlayerController 0) 0.5 %s)\n'
                 '        (Game|Feedback|SetHapticsbyValue (Game|GetPlayerController 0) 0.5 %s "Right")') % (a, a)
ATT = lambda c: ('(Transformation|AttachComponentToComponent :self %s :Parent (Class|BPSoulHUD3DSC|GetArt %s) '
                 ':LocationRule "KeepWorld" :RotationRule "KeepWorld" :ScaleRule "KeepWorld" :bWeldSimulatedBodies false)') % (c, V('Hud'))
CODES = {}
CODES['KitFindHud'] = """(fn KitFindHud ()
  (Utilities|IsValid %s
    (:"Is Not Valid"
      %s)))
""" % (V('Hud'), S('Hud', '(Utilities|Casting|CastToBP_SoulHUD3D_SC (Actor|GetActorOfClass "%s"))' % HUDC))
CODES['KitFindArt'] = """(fn KitFindArt ()
  (Utilities|IsValid %s
    (:"Is Valid"
      (Utilities|IsValid %s
        (:"Is Not Valid"
          %s)))))
""" % (V('Hud'), V('Art'), S('Art', '(Utilities|Casting|CastToBP_HUDArt_SC (Class|ChildActorComponent|GetChildActor (Class|BPSoulHUD3DSC|GetArt %s)))' % V('Hud')))
CODES['KitFindRig'] = """(fn KitFindRig ()
  (if (== %s 1)
    (Utilities|IsValid %s
      (:"Is Not Valid"
        %s))))
""" % (V('Mode'), V('Rig'), S('Rig', '(Utilities|Casting|CastToBP_BreathRig_SC (Actor|GetActorOfClass "%s"))' % RIGC))
CODES['KitFind'] = """(fn KitFind ()
  (CallFunction|KitFindHud)
  (CallFunction|KitFindArt)
  (CallFunction|KitFindRig))
"""
CODES['KitDisc'] = """(fn KitDisc (Dt)
  (if (== %s 1)
    (Utilities|IsValid %s
      (:"Is Valid"
        %s))))
""" % (V('Mode'), V('Rig'), S('DiscK', '(Math|Interpolation|FInterpTo %s (Class|BPBreathRigSC|GetBreathOn %s) Dt 6.0)' % (V('DiscK'), V('Rig'))))

CODES['KitSetup'] = '''(fn KitSetup ()
  (bind _hud %(hud)s)
  (bind _ring (Class|BPSoulHUD3DSC|GetRing _hud))
  (bind _rl (Transformation|GetWorldLocation _ring))
  (bind _dir (- %(cam)s _rl))
  (bind _n (Math|Vector|Normalize _dir))
  (bind _s (* (/ (Math|Vector|VectorLength (Transformation|GetWorldScale _ring)) 1.732) 0.5))
  (bind _al (Transformation|GetActorLocation %(art)s))
  (bind _ad (- %(cam)s _al))
  (Transformation|SetWorldLocationAndRotation %(disc)s (+ _rl (* _n 0.3)) (Math|Rotator|MakeRotfromZ _dir))
  (Transformation|SetWorldScale3D %(disc)s (Math|Vector|MakeVector _s _s _s))
  %(attdisc)s
  (Transformation|SetWorldLocationAndRotation %(timer)s (+ _rl (* _n 0.4)) (Math|Rotator|MakeRotfromX _dir))
  (Rendering|Components|TextRender|SetWorldSize %(timer)s %(tcm)s)
  %(atttimer)s
  (Transformation|SetWorldLocationAndRotation %(wave)s (+ _al (* (Math|Vector|Normalize _ad) 0.5)) (Math|Rotator|MakeRotfromZ _ad))
  %(attwave)s
  (Transformation|SetWorldLocationAndRotation %(pop)s (+ _al (* (Math|Vector|Normalize _ad) 0.6)) (Math|Rotator|MakeRotfromZ _ad))
  %(attpop)s
  (Transformation|SetRelativeScale3D _ring (Math|Vector|MakeVector 0.0001 0.0001 0.0001))
  (Transformation|SetRelativeScale3D (Class|BPSoulHUD3DSC|GetRingSoul _hud) (Math|Vector|MakeVector 0.0001 0.0001 0.0001))
  %(artrest)s
  %(dc)s
  %(dr)s
  %(dw)s
  %(di)s
  %(df)s
  %(da)s
  %(wc)s
  %(wr)s
  %(ww)s
  %(wf)s
  %(wa)s
  %(pc)s
  %(pr)s
  %(pw)s
  %(pf)s
  %(pa)s
  %(setup)s
  (Development|PrintString "HUDKIT: listo (slot derecho, onda y plop colgados del HUD)" :bPrintToScreen false))
''' % dict(hud=V('Hud'), cam=CAM, art=V('Art'), disc=V('Disc'), timer=V('Timer'), wave=V('Wave'), pop=V('Pop'), tcm=V('TimerCm'),
           attdisc=ATT(V('Disc')), atttimer=ATT(V('Timer')), attwave=ATT(V('Wave')), attpop=ATT(V('Pop')),
           artrest=S('ArtRest', '(Class|SceneComponent|GetRelativeLocation (Class|BPSoulHUD3DSC|GetArt _hud))'),
           dc=SETV(V('Disc'), 'Color', '(Math|Conversions|ToVector(LinearColor) %s)' % V('DiscColor')), dr=SETS(V('Disc'), 'Radius', '0.85'),
           dw=SETS(V('Disc'), 'Width', '0.12'), di=SETS(V('Disc'), 'Inner', '0.4'), df=SETS(V('Disc'), 'Fill', '0.0'), da=SETS(V('Disc'), 'Amount', '0.0'),
           wc=SETV(V('Wave'), 'Color', '(Math|Conversions|ToVector(LinearColor) %s)' % V('WaveColor')), wr=SETS(V('Wave'), 'Radius', '0.9'),
           ww=SETS(V('Wave'), 'Width', '0.05'), wf=SETS(V('Wave'), 'Fill', '0.0'), wa=SETS(V('Wave'), 'Amount', '0.0'),
           pc=SETV(V('Pop'), 'Color', '(Math|Vector|MakeVector 1.0 0.82 0.62)'), pr=SETS(V('Pop'), 'Radius', '0.5'),
           pw=SETS(V('Pop'), 'Width', '0.45'), pf=SETS(V('Pop'), 'Fill', '0.6'), pa=SETS(V('Pop'), 'Amount', '0.0'),
           setup=S('Setup', 'true'))

CODES['KitSlot'] = '''(fn KitSlot (Dt)
  (bind _at (Class|BPCAppearLuzSC|GetAppearT (Class|BPHUDArtSC|GetAppear %(art)s)))
  (bind _sk (Math|Float|MapRangeClamped _at 0.6 0.9 0.0 1.0))
  (CallFunction|KitDisc :Dt Dt)
  %(da)s
  %(df)s
  (Rendering|SetVisibility %(timer)s (and (== %(mode)s 2) (> _sk 0.5)))
  (if (== %(mode)s 2)
    (bind _tl (Math|Float|Max(Float) %(tl)s 0.0))
    (bind _m (Math|Float|Floor (/ _tl 60.0)))
    (bind _s (- (Math|Float|Floor _tl) (* _m 60)))
    (Rendering|Components|TextRender|SetText %(timer)s (Utilities|Text|ToText(String) (Utilities|String|Append (Utilities|String|ToString(Integer) _m) (Utilities|String|Append (select (< _s 10) ":0" ":") (Utilities|String|ToString(Integer) _s)))))))
''' % dict(art=V('Art'), mode=V('Mode'), rig=V('Rig'), timer=V('Timer'), tl=V('TimeLeft'),
           dk=S('DiscK', '(Math|Interpolation|FInterpTo %s (Class|BPBreathRigSC|GetBreathOn %s) Dt 6.0)' % (V('DiscK'), V('Rig'))),
           da=SETS(V('Disc'), 'Amount', '(* (select (== %s 1) 1.0 0.0) (* _sk (+ 0.3 (* 0.7 %s))))' % (V('Mode'), V('DiscK'))),
           df=SETS(V('Disc'), 'Fill', '(* 0.6 %s)' % V('DiscK')))

CODES['KitSister'] = '''(fn KitSister ()
  (Class|BPHUDSisterSC|SetBPM :self (Utilities|Casting|CastToBP_HUDSister_SC (Class|ChildActorComponent|GetChildActor (Class|BPSoulHUD3DSC|GetSister %s))) :BPM (Class|BPSoulHUDSC|GetBPM %s)))
''' % (V('Hud'), V('Hud'))

CODES['HudShow'] = '''(fn HudShow ()
  (if (not %s)
    %s
    (Class|BPHUDArtSC|HUDAppear %s)
    %s
    (Audio|PlaySound2D %s)
    (Development|PrintString "HUDKIT: aparece el HUD" :bPrintToScreen false)))
''' % (V('Shown'), S('Shown', 'true'), V('Art'), S('BirthAt', '(+ %s 1.0)' % V('T')), V('ShowSound'))

CODES['HudInstall'] = '''(fn HudInstall ()
  (CallFunction|HudShow)
  %s
  (Development|PrintString "HUDKIT: instalacion con onda de luz" :bPrintToScreen false))
''' % S('WaveT', '0.0')

CODES['HudPlop'] = '''(fn HudPlop ()
  (if (and %s (< %s 0.0))
    %s
    (Development|PrintString "HUDKIT: el HUD tiembla y se va" :bPrintToScreen false)))
''' % (V('Shown'), V('PlopT'), S('PlopT', '0.0'))

CODES['KitWave'] = '''(fn KitWave (Dt)
  (if (>= %(wt)s 0.0)
    %(wtp)s
    (bind _k (Math|Float|Clamp(Float) (/ %(wt)s 1.6) 0.0 1.0))
    (bind _e (- 1.0 (* (- 1.0 _k) (* (- 1.0 _k) (- 1.0 _k)))))
    (bind _s (+ 0.02 (* 0.7 _e)))
    (Transformation|SetWorldScale3D %(wave)s (Math|Vector|MakeVector _s _s _s))
    %(wa)s
    %(hap)s
    (if (>= _k 1.0)
      %(wend)s
      %(w0)s)))
''' % dict(wt=V('WaveT'), wtp=S('WaveT', '(+ %s Dt)' % V('WaveT')), wave=V('Wave'),
           wa=SETS(V('Wave'), 'Amount', '(* 0.9 (* (- 1.0 _k) (- 1.0 _k)))'),
           hap=HAP('(select (< %s 0.3) 0.5 0.0)' % V('WaveT')), wend=S('WaveT', '-1.0'), w0=SETS(V('Wave'), 'Amount', '0.0'))

CODES['KitPlop'] = '''(fn KitPlop (Dt)
  (if (>= %(pt)s 0.0)
    %(ptp)s
    (bind _p %(pt)s)
    (bind _hud %(hud)s)
    (if (< _p 0.9)
      (bind _k (/ _p 0.9))
      (bind _a (+ 0.08 (* 0.35 (* _k _k))))
      (Transformation|SetRelativeLocation (Class|BPSoulHUD3DSC|GetArt _hud) (+ %(rest)s (Math|Vector|MakeVector 0.0 (* _a (Math|Trig|Sin(Radians) (* %(t)s 71.0))) (* _a (Math|Trig|Cos(Radians) (* %(t)s 83.0))))))
      %(flash)s
      %(hap1)s
      (else
        (if (not %(van)s)
          %(vant)s
          (Transformation|SetRelativeLocation (Class|BPSoulHUD3DSC|GetArt _hud) %(rest)s)
          %(flash0)s
          (Class|BPHUDArtSC|HUDVanish %(art)s)
          (Rendering|SetVisibility (Class|BPSoulHUDSC|GetHud _hud) false)
          (Audio|PlaySound2D %(snd)s)
          (Development|PrintString "HUDKIT: plop" :bPrintToScreen false))
        (bind _q (Math|Float|Clamp(Float) (/ (- _p 0.9) 0.6) 0.0 1.0))
        (bind _ps (+ 0.02 (* 0.1 _q)))
        (Transformation|SetWorldScale3D %(pop)s (Math|Vector|MakeVector _ps _ps _ps))
        %(pa)s
        %(hap2)s
        (if (>= _q 1.0)
          %(pend)s)))))
''' % dict(pt=V('PlopT'), ptp=S('PlopT', '(+ %s Dt)' % V('PlopT')), hud=V('Hud'), rest=V('ArtRest'), t=V('T'), art=V('Art'),
           flash=SETS('(Class|BPHUDArtSC|GetRim %s)' % V('Art'), 'Flash', '(+ 0.35 (* 0.65 _k))'),
           flash0=SETS('(Class|BPHUDArtSC|GetRim %s)' % V('Art'), 'Flash', '0.0'),
           hap1=HAP('(* 0.7 _k)'), hap2=HAP('(select (< _p 1.05) 1.0 0.0)'),
           van=V('Vanished'), vant=S('Vanished', 'true'), snd=V('PlopSound'), pop=V('Pop'),
           pa=SETS(V('Pop'), 'Amount', '(* 1.2 (* (- 1.0 _q) (- 1.0 _q)))'), pend=S('PlopT', '-1.0'))

CODES['KitTick'] = '''(fn KitTick (Dt)
  %(tp)s
  (CallFunction|KitFind)
  (Utilities|IsValid %(art)s
    (:"Is Valid"
      (if (and %(hos)s (and (not %(hid)s) (> %(t)s 0.15)))
        %(hidt)s
        (Class|BPHUDArtSC|HUDHideNow %(art)s))
      (if (and (not %(setup)s) (and (Class|BPSoulHUDSC|GetAttached %(hud)s) (> %(t)s 0.5)))
        (CallFunction|KitSetup))
      (if %(setup)s
        (CallFunction|KitSlot :Dt Dt)
        (CallFunction|KitSister)
        (CallFunction|KitWave :Dt Dt)
        (CallFunction|KitPlop :Dt Dt))
      (if (and (>= %(auto)s 0.0) (and (not %(shown)s) (>= %(t)s %(auto)s)))
        (CallFunction|HudShow))
      (if (and %(shown)s (and (not %(bd)s) (>= %(t)s %(ba)s)))
        %(bdt)s
        (Class|BPSoulHUDSC|Birth %(hud)s)))))
''' % dict(tp=S('T', '(+ %s Dt)' % V('T')), art=V('Art'), hos=V('HideOnStart'), hid=V('Hid0'), t=V('T'), hidt=S('Hid0', 'true'),
           setup=V('Setup'), hud=V('Hud'), auto=V('AutoShow'), shown=V('Shown'), bd=V('BirthDone'), ba=V('BirthAt'), bdt=S('BirthDone', 'true'))

ORDER = ['KitFindHud', 'KitFindArt', 'KitFindRig', 'KitFind', 'KitDisc', 'KitSetup', 'KitSlot', 'KitSister', 'HudShow', 'HudInstall', 'HudPlop', 'KitWave', 'KitPlop', 'KitTick']
EVG = '''(event EventTick (DeltaSeconds)
  (CallFunction|KitTick :Dt (Math|Float|Min(Float) DeltaSeconds 0.0333)))
'''
