# kit_dsl.py - BP_DemoHudKit_SC: adapta el HUD de la Obra (BP_SoulHUD3D_SC) a la demo
V = lambda n: '(Variables|Default|Get%s)' % n
S = lambda n, x: '(Variables|Default|Set%s %s)' % (n, x)
HUDC = '/Game/SoulCharger/Shared/HUD/Blueprints/BP_SoulHUD3D_SC.BP_SoulHUD3D_SC_C'
RIGC = '/SC_Breath/Blueprints/BP_BreathRig_SC.BP_BreathRig_SC_C'
HMC = '/Game/SoulCharger/Mechanics/Heart/Blueprints/BP_HeartManager_SC.BP_HeartManager_SC_C'
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
        %s))
    (elif (== %s 3)
      (Utilities|IsValid %s
        (:"Is Not Valid"
          %s)))))
""" % (V('Mode'), V('Rig'), S('Rig', '(Utilities|Casting|CastToBP_BreathRig_SC (Actor|GetActorOfClass "%s"))' % RIGC),
       V('Mode'), V('Heart'), S('Heart', '(Actor|GetActorOfClass "%s")' % HMC))
CODES['KitFind'] = """(fn KitFind ()
  (CallFunction|KitFindHud)
  (CallFunction|KitFindArt)
  (CallFunction|KitFindRig))
"""
# Mode 3 (Heart): 20-10 noche (Beltran) el disco es un PUNTO rojo que crece con cada pulso: DiscK = BeatCount / StageBeats (los pulsos que
# cierran la etapa) -> se llena de 0 a 100; destella con cada latido (BeatEnv). Lo dibuja KitSlot (Inner/Radius 0, Width crece).
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
       V('Mode'), V('Heart'), S('DiscK', '(Math|Interpolation|FInterpTo %s (Math|Float|MapRangeClamped (Class|BPHeartManagerSC|GetBeatCount %s) 0.0 (Class|BPHeartManagerSC|GetStageBeats %s) 0.0 1.0) Dt 3.0)' % (V('DiscK'), V('Heart'), V('Heart'))))

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
  (Rendering|SetVisibility %(wave)s false)
  (Rendering|SetVisibility %(pop)s false)
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
           setup=S('Setup', 'true'), mode=V('Mode'))

# 2026-10-20 noche: el reloj va ANTES del bloque del modo 3. Ese bloque termina en un IsValid y el DSL colgaba lo que seguia
# de su rama 'else': en Heart (Mode 3) el reloj nunca se escondia y se veia 'Text' sobre el disco.
CODES['KitSlot'] = '''(fn KitSlot (Dt)
  (bind _at (Class|BPCAppearLuzSC|GetAppearT (Class|BPHUDArtSC|GetAppear %(art)s)))
  (bind _sk (Math|Float|MapRangeClamped _at 0.6 0.9 0.0 1.0))
  (CallFunction|KitDisc :Dt Dt)
  (Rendering|SetVisibility %(disc)s (or (== %(mode)s 1) (== %(mode)s 3)))
  %(da)s
  %(df)s
  (Rendering|SetVisibility %(timer)s (and (== %(mode)s 2) (> _sk 0.5)))
  (if (== %(mode)s 2)
    (bind _tl (Math|Float|Max(Float) %(tl)s 0.0))
    (bind _fl (Math|Float|Floor _tl))
    (if (not (== _fl %(ls)s))
      %(lss)s
      (bind _m (Math|Float|Floor (/ _tl 60.0)))
      (bind _s (- _fl (* _m 60)))
      (Rendering|Components|TextRender|SetText %(timer)s (Utilities|Text|ToText(String) (Utilities|String|Append (Utilities|String|ToString(Integer) _m) (Utilities|String|Append (select (< _s 10) ":0" ":") (Utilities|String|ToString(Integer) _s)))))))
  (if (== %(mode)s 3)
    (Rendering|Material|SetScalarParameterValueonMaterials %(disc)s "Inner" -0.1)
    (Rendering|Material|SetScalarParameterValueonMaterials %(disc)s "Radius" 0.0)
    (Rendering|Material|SetScalarParameterValueonMaterials %(disc)s "Width" (+ 0.06 (* 0.5 %(dkk)s)))
    (Rendering|Material|SetScalarParameterValueonMaterials %(disc)s "Fill" 0.0)
    (Rendering|Material|SetScalarParameterValueonMaterials %(disc)s "Amount" (* _sk 0.6))
    (Utilities|IsValid %(heart)s
      (:"Is Valid"
        (Rendering|Material|SetScalarParameterValueonMaterials %(disc)s "Amount" (* _sk (+ 0.6 (* 0.6 (Class|BPHeartManagerSC|GetBeatEnv %(heart)s)))))))))
''' % dict(art=V('Art'), mode=V('Mode'), rig=V('Rig'), timer=V('Timer'), disc=V('Disc'), tl=V('TimeLeft'), ls=V('LastSec'), lss=S('LastSec', '_fl'), dkk=V('DiscK'), heart=V('Heart'),
           dk=S('DiscK', '(Math|Interpolation|FInterpTo %s (Class|BPBreathRigSC|GetBreathOn %s) Dt 6.0)' % (V('DiscK'), V('Rig'))),
           da=SETS(V('Disc'), 'Amount', '(* (select (or (== %s 1) (== %s 3)) 1.0 0.0) (* _sk (+ 0.3 (* 0.7 %s))))' % (V('Mode'), V('Mode'), V('DiscK'))),
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

# HudShowNow (2026-10-20, pedido de Beltran: el HUD instalado en el menu no se va y vuelve en la experiencia):
# el HUD aparece YA instalado, sin animacion, sin sonido y con el EEG ya nacido. Lo llama KitTick apenas esta colgado
# de la cara si bShowNow (perilla de los niveles de experiencia).
CODES['HudShowNow'] = '''(fn HudShowNow ()
  (if (not %(shown)s)
    %(shown1)s
    (bind _ap (Class|BPHUDArtSC|GetAppear %(art)s))
    (Class|BPHUDArtSC|HUDHideNow %(art)s)
    (Class|BPCAppearLuzSC|SetAppearT :self _ap :AppearT 1.0)
    (Class|BPCAppearLuzSC|ApplyT :self _ap :Tin 1.0)
    (Class|BPSoulHUDSC|Birth %(hud)s)
    (Class|BPSoulHUDSC|SetBirthT :self %(hud)s :BirthT 1.0)
    %(bd1)s
    (Development|PrintString "HUDKIT: HUD ya instalado (viene del menu, sin animacion)" :bPrintToScreen false)))
''' % dict(shown=V('Shown'), shown1=S('Shown', 'true'), art=V('Art'), hud=V('Hud'), bd1=S('BirthDone', 'true'))

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

# 2026-10-20 tarde: la onda de instalacion dura 2,4 s (era 1,6): Beltran pidio el inicio mas pausado
CODES['KitWave'] = '''(fn KitWave (Dt)
  (if (>= %(wt)s 0.0)
    %(wtp)s
    (Rendering|SetVisibility %(wave)s true)
    (bind _k (Math|Float|Clamp(Float) (/ %(wt)s 2.4) 0.0 1.0))
    (bind _e (- 1.0 (* (- 1.0 _k) (* (- 1.0 _k) (- 1.0 _k)))))
    (bind _s (+ 0.02 (* 0.7 _e)))
    (Transformation|SetWorldScale3D %(wave)s (Math|Vector|MakeVector _s _s _s))
    %(wa)s
    %(hap)s
    (if (>= _k 1.0)
      %(wend)s
      %(w0)s
      (Rendering|SetVisibility %(wave)s false))))
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
        (Rendering|SetVisibility %(pop)s true)
        (Transformation|SetWorldScale3D %(pop)s (Math|Vector|MakeVector _ps _ps _ps))
        %(pa)s
        %(hap2)s
        (if (>= _q 1.0)
          %(pend)s
          (Rendering|SetVisibility %(pop)s false))))))
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
        (CallFunction|KitSetup)
        (if %(now)s
          (CallFunction|HudShowNow)))
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
           setup=V('Setup'), hud=V('Hud'), now=V('ShowNow'), auto=V('AutoShow'), shown=V('Shown'), bd=V('BirthDone'), ba=V('BirthAt'), bdt=S('BirthDone', 'true'))

ORDER = ['KitFindHud', 'KitFindArt', 'KitFindRig', 'KitFind', 'KitDisc', 'KitSetup', 'KitSlot', 'KitSister', 'HudShow', 'HudShowNow', 'HudInstall', 'HudPlop', 'KitWave', 'KitPlop', 'KitTick']
EVG = '''(event EventTick (DeltaSeconds)
  (CallFunction|KitTick :Dt (Math|Float|Min(Float) DeltaSeconds 0.0333)))
'''
