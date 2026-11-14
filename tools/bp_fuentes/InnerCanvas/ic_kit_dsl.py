# ic_kit_dsl.py - BP_ICHudKit_IC: el HUD de Inner Canvas. Copia de Demo2/kit_dsl.py (BP_DemoHudKit_SC) sin Breath/Heart.
# HUD de la Obra (BP_SoulHUD3D_SC): izquierda = circulo verde de TINTA (InkDisc, en lugar de la protoameba), centro = el NOMBRE
# (NameQuad, en lugar de la onda del EEG; la textura la dibuja el teclado), derecha = el RELOJ (TimerQuad, como en Draw).
# KitReset lo deja listo para la proxima sesion (el director reinicia en el mismo nivel).
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ic_common import D as V, DS as S, CAM, CAMROT, V2, LC, FONT, PANE
FONT = '/Game/InnerCanvas/UI/F_ICWall_IC.F_ICWall_IC'
HUDC = '/Game/SoulCharger/Shared/HUD/Blueprints/BP_SoulHUD3D_SC.BP_SoulHUD3D_SC_C'
SETS = lambda c, p, x: '(Rendering|Material|SetScalarParameterValueonMaterials %s "%s" %s)' % (c, p, x)
SETV = lambda c, p, x: '(Rendering|Material|SetVectorParameterValueonMaterials %s "%s" %s)' % (c, p, x)
HAP = lambda a: ('(Game|Feedback|SetHapticsbyValue (Game|GetPlayerController 0) 0.5 %s)\n'
                 '        (Game|Feedback|SetHapticsbyValue (Game|GetPlayerController 0) 0.5 %s "Right")') % (a, a)
ATT = lambda c: ('(Transformation|AttachComponentToComponent :self %s :Parent (Class|BPSoulHUD3DSC|GetArt %s) '
                 ':LocationRule "KeepWorld" :RotationRule "KeepWorld" :ScaleRule "KeepWorld" :bWeldSimulatedBodies false)') % (c, V('Hud'))
HAND_OPACITY = '0.32'
TQ_CM = 3.0
TQ_UP = '-1.0'
TW = 512
T_SCALE = 1.45
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
CODES['KitFind'] = """(fn KitFind ()
  (CallFunction|KitFindHud)
  (CallFunction|KitFindArt))
"""

# KitSetup: reloj a la derecha (igual que en la demo), tinta a la izquierda (donde estaba la protoameba, que se esconde con escala
# 0,0001 como el anillo derecho), nombre al centro (donde estaba la onda del EEG, que se esconde). Onda y plop colgados del HUD.
CODES['KitSetup'] = '''(fn KitSetup ()
  (bind _hud %(hud)s)
  (bind _ring (Class|BPSoulHUD3DSC|GetRing _hud))
  (bind _rl (Transformation|GetWorldLocation _ring))
  (bind _dir (- %(cam)s _rl))
  (bind _s (* (/ (Math|Vector|VectorLength (Transformation|GetWorldScale _ring)) 1.732) 0.5))
  (bind _al (Transformation|GetActorLocation %(art)s))
  (bind _ad (- %(cam)s _al))
  (bind _sis (Class|BPSoulHUD3DSC|GetSister _hud))
  (bind _sl (- (* _al 2.0) _rl))
  (bind _sd (- %(cam)s _sl))
  (bind _eeg (Class|BPSoulHUDSC|GetHud _hud))
  (Transformation|SetWorldLocationAndRotation %(ink)s (+ _sl (* (Math|Vector|Normalize _sd) 0.3)) (Math|Rotator|MakeRotfromZ _sd))
  (Transformation|SetWorldScale3D %(ink)s (Math|Vector|MakeVector _s _s _s))
  %(attink)s
  (Transformation|SetWorldLocationAndRotation %(tq)s (+ _rl (* (Math|Vector|Normalize _dir) 0.45)) (Math|Rotator|MakeRotfromZY _dir (Math|Vector|MakeVector 0.0 0.0 %(tqup)s)))
  (Transformation|SetWorldScale3D %(tq)s (Math|Vector|MakeVector %(tqs)s %(tqs)s 1.0))
  %(atttq)s
  (Transformation|SetWorldLocationAndRotation %(nq)s (+ _al (* (Math|Vector|Normalize _ad) 0.55)) (Math|Rotator|MakeRotfromZY _ad (Math|Vector|MakeVector 0.0 0.0 %(tqup)s)))
  (Transformation|SetWorldScale3D %(nq)s (Math|Vector|MakeVector %(nqw)s %(nqh)s 1.0))
  %(attnq)s
  (bind _tr (Class|SceneComponent|GetRelativeLocation %(tq)s))
  (Transformation|SetRelativeLocation %(ink)s (Math|Vector|MakeVector (* -1.0 (.x _tr)) (.y _tr) (.z _tr)))
  (Transformation|SetRelativeLocationAndRotation %(nq)s (Math|Vector|MakeVector 0.0 (.y _tr) (.z _tr)) (Class|SceneComponent|GetRelativeRotation %(tq)s))
  %(trt)s
  %(twk)s
  (bind _tm (Rendering|Material|CreateDynamicMaterialInstance %(tq)s :ElementIndex 0 :SourceMaterial "%(pane)s"))
  (Rendering|Material|SetTextureParameterValue _tm "Card" %(trtg)s)
  %(nmid)s
  (CallFunction|KitPaneLook :C %(tq)s)
  (CallFunction|KitPaneLook :C %(nq)s)
  (Transformation|SetWorldLocationAndRotation %(wave)s (+ _al (* (Math|Vector|Normalize _ad) 0.5)) (Math|Rotator|MakeRotfromZ _ad))
  %(attwave)s
  (Transformation|SetWorldLocationAndRotation %(pop)s (+ _al (* (Math|Vector|Normalize _ad) 0.6)) (Math|Rotator|MakeRotfromZ _ad))
  %(attpop)s
  (Rendering|SetVisibility %(wave)s false)
  (Rendering|SetVisibility %(pop)s false)
  (Rendering|SetVisibility %(disc)s false)
  (Rendering|SetVisibility %(timer)s false)
  (Rendering|SetVisibility _eeg false)
  (Transformation|SetRelativeScale3D _ring (Math|Vector|MakeVector 0.0001 0.0001 0.0001))
  (Transformation|SetRelativeScale3D (Class|BPSoulHUD3DSC|GetRingSoul _hud) (Math|Vector|MakeVector 0.0001 0.0001 0.0001))
  (Transformation|SetRelativeScale3D _sis (Math|Vector|MakeVector 0.0001 0.0001 0.0001))
  %(artrest)s
  %(ic)s
  %(ir)s
  %(iw)s
  %(ii)s
  %(if_)s
  %(ia)s
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
  (for _hc (Actor|GetComponentsByClass (Game|GetPlayerPawn 0) "/Script/Engine.SkeletalMeshComponent")
    (if (Utilities|String|Contains (Utilities|GetObjectName (Rendering|Material|GetMaterial _hc 0)) "MI_Hand")
      (Rendering|Material|SetScalarParameterValueOnMaterials _hc "Opacity" %(handop)s)))
  (Development|PrintString "HUDKIT IC: listo (tinta, nombre y reloj colgados del HUD)" :bPrintToScreen false))
''' % dict(handop=HAND_OPACITY, hud=V('Hud'), cam=CAM, art=V('Art'), disc=V('Disc'), timer=V('Timer'), wave=V('Wave'), pop=V('Pop'),
           ink=V('InkDisc'), attink=ATT(V('InkDisc')), nq=V('NameQuad'), attnq=ATT(V('NameQuad')),
           nqw='%.4f' % 0.12, nqh='%.4f' % 0.03,
           attwave=ATT(V('Wave')), attpop=ATT(V('Pop')),
           tqup=TQ_UP, tq=V('TimerQuad'), tqs='%.4f' % (TQ_CM / 100.0), atttq=ATT(V('TimerQuad')), pane=PANE, trtg=V('TimerRT'),
           nmid=S('NameMID', '(Rendering|Material|CreateDynamicMaterialInstance %s :ElementIndex 0 :SourceMaterial "%s")' % (V('NameQuad'), PANE)),
           trt=S('TimerRT', '(Rendering|CreateRenderTarget2D :Width %d :Height %d :Format "RTF_RGBA8" :ClearColor %s :bAutoGenerateMipMaps false)' % (TW // 2, TW // 2, LC(0.0, 0.0, 0.0, 0.0))),
           twk=S('TimerWork', '(Rendering|CreateRenderTarget2D :Width %d :Height %d :Format "RTF_RGBA8" :ClearColor %s :bAutoGenerateMipMaps false)' % (TW, TW, LC(0.0, 0.0, 0.0, 0.0))),
           artrest=S('ArtRest', '(Class|SceneComponent|GetRelativeLocation (Class|BPSoulHUD3DSC|GetArt _hud))'),
           ic=SETV(V('InkDisc'), 'Color', '(Math|Conversions|ToVector(LinearColor) %s)' % V('InkColor')), ir=SETS(V('InkDisc'), 'Radius', '0.0'),
           iw=SETS(V('InkDisc'), 'Width', '0.56'), ii=SETS(V('InkDisc'), 'Inner', '-0.1'), if_=SETS(V('InkDisc'), 'Fill', '0.0'), ia=SETS(V('InkDisc'), 'Amount', '0.0'),
           wc=SETV(V('Wave'), 'Color', '(Math|Conversions|ToVector(LinearColor) %s)' % V('WaveColor')), wr=SETS(V('Wave'), 'Radius', '0.9'),
           ww=SETS(V('Wave'), 'Width', '0.05'), wf=SETS(V('Wave'), 'Fill', '0.0'), wa=SETS(V('Wave'), 'Amount', '0.0'),
           pc=SETV(V('Pop'), 'Color', '(Math|Vector|MakeVector 1.0 0.82 0.62)'), pr=SETS(V('Pop'), 'Radius', '0.5'),
           pw=SETS(V('Pop'), 'Width', '0.45'), pf=SETS(V('Pop'), 'Fill', '0.6'), pa=SETS(V('Pop'), 'Amount', '0.0'),
           setup=S('Setup', 'true'))

# HudShow (2026-11-13, Beltran: 'el nombre y el timer se sienten mas cerca que el HUD'): nombre y reloj pegados al vidrio del HUD
# (11-13: el nombre al 75 %: 'esta demasiado mas grande que el timer'.)
# (z 0,3 en el espacio del arte, justo sobre el borde de 0,25; antes 1,97 = ~1 cm adelante) y coplanares con el (rotacion relativa 0).
# KitPaneLook: el vidrio de los resultados con solo el texto visible (la receta del reloj de la demo)
CODES['KitPaneLook'] = '''(fn KitPaneLook (C)
  (Rendering|Material|SetVectorParameterValueonMaterials C "Color" (Math|Vector|MakeVector 0.0 0.0 0.0))
  (Rendering|Material|SetScalarParameterValueonMaterials C "Base" 0.0)
  (Rendering|Material|SetScalarParameterValueonMaterials C "Opacity" 0.0)
  (Rendering|Material|SetScalarParameterValueonMaterials C "Gain" 1.2)
  (Rendering|Material|SetScalarParameterValueonMaterials C "Fade" 1.0)
  (Rendering|Material|SetScalarParameterValueonMaterials C "Boost" 1.4))
'''

# KitSlot: reloj (cuando cambia el segundo, texto Quicksand a 2x en TimerWork reducido a TimerRT), tinta (un punto verde que se
# achica: ancho 0,04 + 0,52 x tinta) y nombre (visible con el HUD).
CODES['KitSlot'] = '''(fn KitSlot (Dt)
  (bind _at (Class|BPCAppearLuzSC|GetAppearT (Class|BPHUDArtSC|GetAppear %(art)s)))
  (bind _sk (Math|Float|MapRangeClamped _at 0.6 0.9 0.0 1.0))
  %(inkk)s
  (Rendering|SetVisibility %(ink)s (> _sk 0.05))
  (Rendering|Material|SetScalarParameterValueonMaterials %(ink)s "Width" (+ 0.04 (* 0.52 %(ik)s)))
  (Rendering|Material|SetScalarParameterValueonMaterials %(ink)s "Amount" (* _sk (+ 0.25 (* 0.75 (Math|Float|Clamp(Float) (* 4.0 %(ik)s))))))
  (Rendering|SetVisibility %(nq)s (> _sk 0.5))
  (Rendering|SetVisibility %(tq)s (> _sk 0.5))
  (bind _tl (Math|Float|Max(Float) %(tl)s 0.0))
  (bind _fl (Math|Float|Floor _tl))
  (if (not (== _fl %(ls)s))
    %(lss)s
    (bind _m (Math|Float|Floor (/ _tl 60.0)))
    (bind _s (- _fl (* _m 60)))
    (Rendering|ClearRenderTarget2D :TextureRenderTarget %(twk)s :ClearColor %(c0)s)
    (bind (_cv _sz _ctx) (Rendering|BeginDrawCanvastoRenderTarget :TextureRenderTarget %(twk)s))
    (Canvas|DrawText _cv :RenderFont "%(font)s" :RenderText (Utilities|String|Append (Utilities|String|ToString(Integer) _m) (Utilities|String|Append (select (< _s 10) ":0" ":") (Utilities|String|ToString(Integer) _s))) :ScreenPosition %(mid)s :Scale %(sc)s :RenderColor %(tcol)s :Kerning 0.0 :ShadowColor %(c0)s :ShadowOffset %(z2)s :bCentreX true :bCentreY true :bOutlined false :OutlineColor %(c0)s)
    (Rendering|EndDrawCanvastoRenderTarget :Context _ctx)
    (Rendering|ClearRenderTarget2D :TextureRenderTarget %(trt)s :ClearColor %(c0)s)
    (bind (_cv2 _sz2 _ctx2) (Rendering|BeginDrawCanvastoRenderTarget :TextureRenderTarget %(trt)s))
    (Canvas|DrawTexture _cv2 :RenderTexture %(twk)s :ScreenPosition %(z2)s :ScreenSize %(half)s :CoordinatePosition %(z2)s :CoordinateSize %(one2)s :RenderColor %(white)s :BlendMode "BLEND_Opaque" :Rotation 0.0 :PivotPoint %(piv)s)
    (Rendering|EndDrawCanvastoRenderTarget :Context _ctx2)))
''' % dict(art=V('Art'), ink=V('InkDisc'), ik=V('InkShown'), inkk=S('InkShown', '(Math|Interpolation|FInterpTo %s %s Dt 4.0)' % (V('InkShown'), V('InkK'))),
           nq=V('NameQuad'), tq=V('TimerQuad'), tl=V('TimeLeft'), ls=V('LastSec'), lss=S('LastSec', '_fl'),
           twk=V('TimerWork'), trt=V('TimerRT'), font=FONT, c0=LC(0.0, 0.0, 0.0, 0.0), z2=V2('0.0', '0.0'),
           mid=V2('%.1f' % (TW / 2), '%.1f' % (TW / 2)), sc=V2('%.3f' % T_SCALE, '%.3f' % T_SCALE), tcol=V('TimerColor'),
           half=V2('%.1f' % (TW / 2), '%.1f' % (TW / 2)), one2=V2('1.0', '1.0'), white=LC(1.0, 1.0, 1.0, 1.0), piv=V2('0.5', '0.5'))

CODES['KitSetInk'] = '''(fn KitSetInk (K)
  %s)
''' % S('InkK', 'K')

CODES['KitSetName'] = '''(fn KitSetName (Tex)
  %s
  (Utilities|IsValid %s
    (:"Is Valid"
      (Rendering|Material|SetTextureParameterValue %s "Card" Tex))))
''' % (S('NameTex', 'Tex'), V('NameMID'), V('NameMID'))

CODES['HudShow'] = '''(fn HudShow ()
  (if (not %s)
    %s
    (bind _tr (Class|SceneComponent|GetRelativeLocation (Variables|Default|GetTimerQuad)))
    (Transformation|SetRelativeLocationAndRotation (Variables|Default|GetTimerQuad) (Math|Vector|MakeVector (.x _tr) (.y _tr) 0.3) (Math|Rotator|MakeRotator 0.0 0.0 0.0) false true)
    (bind _nr (Class|SceneComponent|GetRelativeLocation (Variables|Default|GetNameQuad)))
    (Transformation|SetRelativeLocationAndRotation (Variables|Default|GetNameQuad) (Math|Vector|MakeVector (.x _nr) (.y _nr) 0.3) (Math|Rotator|MakeRotator 0.0 0.0 0.0) false true)
    (Transformation|SetRelativeScale3D (Variables|Default|GetNameQuad) (Math|Vector|MakeVector 0.2045 0.0511 1.0))
    (bind _ir (Class|SceneComponent|GetRelativeLocation (Variables|Default|GetInkDisc)))
    (Transformation|SetRelativeLocationAndRotation (Variables|Default|GetInkDisc) (Math|Vector|MakeVector (.x _ir) (.y _ir) 0.3) (Math|Rotator|MakeRotator 0.0 0.0 0.0) false true)
    (Rendering|SetTranslucentSortPriority (Variables|Default|GetInkDisc) 12)
    (Rendering|SetTranslucentSortPriority (Variables|Default|GetTimerQuad) 12)
    (Rendering|SetTranslucentSortPriority (Variables|Default|GetNameQuad) 12)
    (Class|BPHUDArtSC|HUDAppear %s)
    (Utilities|IsValid %s
      (:"Is Valid"
        (Rendering|Material|SetTextureParameterValue %s "Card" %s)))))
''' % (V('Shown'), S('Shown', 'true'), V('Art'), V('NameMID'), V('NameMID'), V('NameTex'))

CODES['HudInstall'] = '''(fn HudInstall ()
  (Audio|PlaySound2D %s)
  %s
  (Development|PrintString "HUDKIT IC: instalacion con onda de luz" :bPrintToScreen false)
  (CallFunction|HudShow))
''' % (V('ShowSound'), S('WaveT', '0.0'))

CODES['HudPlop'] = '''(fn HudPlop ()
  (if (and %s (< %s 0.0))
    %s
    (Development|PrintString "HUDKIT IC: el HUD tiembla y se va" :bPrintToScreen false)))
''' % (V('Shown'), V('PlopT'), S('PlopT', '0.0'))

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
          (Audio|PlaySound2D %(snd)s)
          (Development|PrintString "HUDKIT IC: plop" :bPrintToScreen false))
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

# KitReset: el HUD vuelve a estar listo para instalarse (Shown/Vanished/PlopT/WaveT/LastSec), oculto, con el arte en su lugar
CODES['KitReset'] = '''(fn KitReset ()
  %s
  %s
  %s
  %s
  %s
  %s
  %s
  (Rendering|SetVisibility %s false)
  (Rendering|SetVisibility %s false)
  (Utilities|IsValid %s
    (:"Is Valid"
      (Transformation|SetRelativeLocation (Class|BPSoulHUD3DSC|GetArt %s) %s)
      (Class|BPHUDArtSC|HUDHideNow %s))))
''' % (S('Shown', 'false'), S('Vanished', 'false'), S('PlopT', '-1.0'), S('WaveT', '-1.0'), S('LastSec', '-1.0'), S('InkK', '1.0'), S('InkShown', '1.0'),
       V('Wave'), V('Pop'), V('Art'), V('Hud'), V('ArtRest'), V('Art'))

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
        (CallFunction|KitWave :Dt Dt)
        (CallFunction|KitPlop :Dt Dt)))))
''' % dict(tp=S('T', '(+ %s Dt)' % V('T')), art=V('Art'), hos=V('HideOnStart'), hid=V('Hid0'), t=V('T'), hidt=S('Hid0', 'true'),
           setup=V('Setup'), hud=V('Hud'))

ORDER = ['KitFindHud', 'KitFindArt', 'KitFind', 'KitPaneLook', 'KitSetup', 'KitSlot', 'KitSetInk', 'KitSetName', 'HudShow', 'HudInstall',
         'HudPlop', 'KitWave', 'KitPlop', 'KitReset', 'KitTick']
EVG = '''(event EventTick (DeltaSeconds)
  (CallFunction|KitTick :Dt (Math|Float|Min(Float) DeltaSeconds 0.0333)))
'''
