# ic_flow_dsl.py - BP_ICFlow_IC: el director de Inner Canvas (2026-11-11, guion docs/innercanvas/PLAN-INNER-CANVAS.md)
# Base: Demo2/flow_dsl.py (rama Draw, Exp 1), probada en BDW. Un solo nivel; al terminar se reinicia EN EL MISMO NIVEL (ICReset),
# sin OpenLevel (en el Pico el cambio de nivel de la demo quedo colgado en un glitch de colores). ResetMode 1 = OpenLevel (plan B).
# Fases: 0 titulo + idioma aparece | 1 elige idioma | 2 se va el titulo | 3 teclado (nombre) | 4 HUD | 5 bienvenida | 6 espacio |
# 7 invitacion | 8 pincel al frente | 9 tomar el pincel | 10 paleta | 11 trazo de practica | 12 se va la practica | 13 dibujo 3:00 |
# 14 presentacion (el dibujo grande al centro, girando) | 15 cierre (nombre + INNER CANVAS) | 16 velo cierra | 17 reinicio
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ic_common import *

SAY = lambda clip: '(Class|BPICVoiceIC|Say :self %s :Clip %s)' % (D('Voice'), D(clip))
SPEAK = '(Class|BPICVoiceIC|GetSpeaking %s)' % D('Voice')
READY = '(and (not %s) (and (>= %s %s) (>= %s 0.6)))' % (SPEAK, D('QuietT'), D('VoGap'), D('PT'))
SKP = '(Class|BPCTBToolNC|GetSketchPhase (Class|BPTBDirectorNC|GetTBTool %s))' % D('TB')
AT = lambda b: '(Class|BPCAppearLuzSC|GetAppearT (Class|BPShareButtonSC|GetAppearLuz %s))' % b
HINT = lambda var: '(Class|BPICVoiceIC|ShowHint :self %s :Id %s)' % (D('Voice'), D(var))
CODES = {}

CODES['ResetVars'] = '''(fn ResetVars ()
  %s
  %s
  %s
  %s
  %s
  %s
  %s
  %s
  %s
  %s
  %s
  %s
  %s
  %s
  %s
  %s
  %s)
''' % (DS('Phase', '0'), DS('RT', '0.0'), DS('PT', '0.0'), DS('Req', 'false'), DS('EndInk', 'false'), DS('Said07', 'false'),
       DS('Said08', 'false'), DS('Said11', 'false'), DS('PulsePend', 'false'), DS('HandsOn', 'false'), DS('TimerT', '0.0'),
       DS('ShrinkT', '0.0'), DS('SketchT', '0.0'), DS('QuietT', '0.0'), DS('Ink01', '1.0'),
       DS('LastPressN', '(Class|BPSeqRigSC|GetResPressN %s)' % D('Rig')), DS('LastPressN2', '(Class|BPSeqRigSC|GetResPressN %s)' % D('Rig2')))

# FBoot: referencias, velo y titulo absolutos, la tinta y la presentacion del dibujo de pie (mesa y destino al centro del espacio,
# a PresentZ del piso; el destino con escala PresentK, 1 desde el 2026-11-12: el dibujo reaparece a su tamano alrededor de la persona,
# da un par de vueltas (HoldTime del director de dibujo en el nivel) y se des-dibuja; ahi DrawTick pasa al cierre con la despedida).
CODES['FBoot'] = '''(fn FBoot ()
  (Audio|SetSubmixOutputVolume(lineargain) %(mm)s 1.0)
  %(ped)s
  (bind _rigs (Actor|GetAllActorsOfClass "%(rigc)s"))
  %(rig)s
  %(rig2)s
  %(voice)s
  %(kit)s
  %(amb)s
  %(tb)s
  %(kb)s
  %(link)s
  %(space)s
  %(ben)s
  %(bes)s
  %(ps)s
  %(psyaw)s
  %(cen)s
  (Transformation|SetAbsolute %(veil)s true true true)
  (Transformation|SetAbsolute %(title)s true true true)
  (Transformation|SetAbsolute %(logo)s true true true)
  (Transformation|SetAbsolute %(namep)s true true true)
  (Rendering|Material|SetColorParameterValueOnMaterials %(veil)s "CTop" %(ctop)s)
  (Rendering|Material|SetColorParameterValueOnMaterials %(veil)s "CHor" %(chor)s)
  (Rendering|Material|SetMaterial %(title)s 0 %(tmi)s)
  (Rendering|SetVisibility %(namep)s false)
  (Rendering|SetActorHiddenInGame %(pedv)s true)
  (Rendering|Material|SetMaterial (Class|BPShareButtonSC|GetPlate %(benv)s) 1 (Class|BPShareButtonSC|GetTopShare %(benv)s))
  (Rendering|Material|SetMaterial (Class|BPShareButtonSC|GetPlate %(besv)s) 1 (Class|BPShareButtonSC|GetTopShare %(besv)s))
  (Rendering|Material|SetVectorParameterValueonMaterials (Class|BPShareButtonSC|GetTrace %(benv)s) "Color" (Math|Conversions|ToVector(LinearColor) %(trc)s))
  (Rendering|Material|SetVectorParameterValueonMaterials (Class|BPShareButtonSC|GetTrace %(besv)s) "Color" (Math|Conversions|ToVector(LinearColor) %(trc)s))
  (Class|BPTBDirectorNC|SetInkMeters :self %(tbv)s :InkMeters %(inkm)s)
  (bind _pv (+ %(cenv)s (Math|Vector|MakeVector 0.0 0.0 %(pz)s)))
  (bind _tbl (Class|BPTBDirectorNC|GetDrawTable %(tbv)s))
  (bind _tgt (Class|BPTBDirectorNC|GetSketchTarget %(tbv)s))
  (Transformation|SetActorLocation _tbl _pv false true)
  (Transformation|SetActorLocation _tgt _pv false true)
  (Transformation|SetActorScale3D _tgt (Math|Vector|MakeVector %(pk)s %(pk)s %(pk)s))
  (for _c (Actor|GetComponentsByClass _tbl "/Script/Engine.PrimitiveComponent")
    (Rendering|SetVisibility _c false))
  (CallFunction|ResetVars)
  (CallFunction|PicoBoot)
  (Development|PrintString "IC: arranca Inner Canvas" :bPrintToScreen false))
''' % dict(mm=D('MasterMix'), rigc=RIGC,
           ped=DS('Pedestal', AG('(Actor|GetAllActorsWithTag "demo_pedestal")', 0)),
           rig=DS('Rig', AG('_rigs', 0)), rig2=DS('Rig2', AG('_rigs', 1)),
           voice=DS('Voice', '(Actor|GetActorOfClass "%s")' % VOICEC), kit=DS('Kit', '(Actor|GetActorOfClass "%s")' % KITC),
           amb=DS('Amb', '(Actor|GetActorOfClass "%s")' % AMBC), tb=DS('TB', '(Actor|GetActorOfClass "%s")' % TBC),
           kb=DS('Kb', '(Actor|GetActorOfClass "%s")' % KBC), link=DS('Link', '(Actor|GetActorOfClass "%s")' % LINKC),
           space=DS('Space', '(Actor|GetActorOfClass "%s")' % SPACEC),
           ben=DS('BtnEn', AG('(Actor|GetAllActorsOfClassWithTag "%s" "ic_en")' % BTN, 0)),
           bes=DS('BtnEs', AG('(Actor|GetAllActorsOfClassWithTag "%s" "ic_es")' % BTN, 0)),
           ps=DS('PStart', '(Transformation|GetActorLocation (Actor|GetActorOfClass "/Script/Engine.PlayerStart"))'),
           psyaw=DS('PsYaw', '(.yaw (Transformation|GetActorRotation (Actor|GetActorOfClass "/Script/Engine.PlayerStart")))'),
           cen=DS('Center', D('PStart')), veil=D('Veil'), title=D('Title'), logo=D('Logo'), namep=D('NameP'),
           ctop=D('CTop'), chor=D('CHor'), tmi=D('TitleMI'), pedv=D('Pedestal'), tbv=D('TB'), inkm=D('InkM'),
           cenv=D('Center'), pz=D('PresentZ'), pk=D('PresentK'), benv=D('BtnEn'), besv=D('BtnEs'), trc=D('TraceColor'))

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

# FVeil: velo (abre al empezar la sesion, cierra al color del mar al final), titulo y logo (entran en la fase 0, se van en la 2;
# vuelven en el cierre 15-16) y el nombre del cierre (NameP).
CODES['FVeil'] = '''(fn FVeil ()
  (bind _ph %(ph)s)
  (bind _rt %(rt)s)
  (bind _pt %(pt)s)
  (bind _open (- 1.0 %(eopen)s))
  (bind _close %(eclose)s)
  (bind _a (select (== _ph 0) _open (select (== _ph 16) _close (select (== _ph 17) 1.0 0.0))))
  (Transformation|SetWorldLocation %(veil)s %(cam)s)
  (Rendering|Material|SetScalarParameterValueOnMaterials %(veil)s "Amount" _a)
  (Rendering|Material|SetScalarParameterValueOnMaterials %(veil)s "Floor" (select (> _a 0.985) 0.0 0.02))
  (Rendering|SetVisibility %(veil)s (> _a 0.001))
  (bind _intro (<= _ph 2))
  (bind _clo (or (== _ph 15) (== _ph 16)))
  (bind _rev (select _intro %(erev)s (select (== _ph 15) %(ecrev)s 1.0)))
  (bind _lrev (select _intro %(elrev)s %(ecrev)s))
  (bind _out (select (or (== _ph 2) (== _ph 16)) %(eout)s 0.0))
  (Rendering|Material|SetScalarParameterValueOnMaterials %(title)s "LT" _rt)
  (Rendering|Material|SetScalarParameterValueOnMaterials %(title)s "Reveal" _rev)
  (Rendering|Material|SetScalarParameterValueOnMaterials %(title)s "Out" _out)
  (Rendering|SetVisibility %(title)s (or _intro _clo))
  (Rendering|Material|SetScalarParameterValueOnMaterials %(logo)s "LT" _rt)
  (Rendering|Material|SetScalarParameterValueOnMaterials %(logo)s "Reveal" _lrev)
  (Rendering|Material|SetScalarParameterValueOnMaterials %(logo)s "Out" _out)
  (Rendering|Material|SetScalarParameterValueOnMaterials %(logo)s "Fade" _lrev)
  (Rendering|SetVisibility %(logo)s (or _intro _clo))
  (Rendering|Material|SetScalarParameterValueOnMaterials %(namep)s "Fade" (* _rev (- 1.0 _out)))
  (Rendering|SetVisibility %(namep)s _clo))
''' % dict(ph=D('Phase'), rt=D('RT'), pt=D('PT'), veil=D('Veil'), title=D('Title'), logo=D('Logo'), namep=D('NameP'), cam=CAM,
           eopen=EASE(MAP('_rt', D('VeilA0'), D('VeilA1'))), eclose=EASE(MAP('_pt', '0.0', '2.5')),
           erev=EASE(MAP('_rt', D('TitleR0'), D('TitleR1'))), elrev=EASE(MAP('_rt', D('LogoR0'), D('LogoR1'))),
           ecrev=EASE(MAP('_pt', '0.3', '1.8')), eout=EASE(MAP('_pt', '0.0', '2.0')))

# FPlaceTitle: el titulo en el TargetPoint de la etapa (TagTitle), a la altura de los ojos; el logo debajo; los botones de idioma
# a 1,5 m al frente y 55 cm bajo los ojos (como los del menu de la demo).
CODES['FPlaceTitle'] = '''(fn FPlaceTitle ()
  (bind _tps (Actor|GetAllActorsWithTag %(tag)s))
  (bind _dz (- (.z %(cam)s) (+ (.z %(ps)s) %(eye)s)))
  (bind _ps %(ps)s)
  (bind _eyez (+ (.z _ps) (+ %(eye)s _dz)))
  (Transformation|SetActorLocationAndRotation %(ben)s (Math|Vector|MakeVector (+ (.x _ps) 150.0) (- (.y _ps) 20.0) (- _eyez 55.0)) (Math|Rotator|MakeRotator 0.0 15.0 180.0) false true)
  (Transformation|SetActorLocationAndRotation %(bes)s (Math|Vector|MakeVector (+ (.x _ps) 150.0) (+ (.y _ps) 20.0) (- _eyez 55.0)) (Math|Rotator|MakeRotator 0.0 15.0 180.0) false true)
  (if (> (Utilities|Array|Length _tps) 0)
    (bind _tp (Utilities|Array|Get(acopy) _tps 0))
    (bind _tl (+ (Transformation|GetActorLocation _tp) (Math|Vector|MakeVector 0.0 0.0 _dz)))
    (bind _rot (Math|Rotator|CombineRotators (Math|Rotator|MakeRotator 90.0 0.0 90.0) (Math|Rotator|MakeRotator 0.0 0.0 (.yaw (Transformation|GetActorRotation _tp)))))
    (Transformation|SetWorldLocationAndRotation %(title)s _tl _rot)
    (Transformation|SetWorldScale3D %(title)s (Math|Vector|MakeVector 4.0 1.0 1.0))
    (Transformation|SetWorldLocationAndRotation %(logo)s (+ _tl (Math|Vector|MakeVector 0.0 0.0 -62.0)) _rot)
    (Transformation|SetWorldScale3D %(logo)s (Math|Vector|MakeVector 0.98 0.245 1.0))))
''' % dict(tag=D('TagTitle'), cam=CAM, ps=D('PStart'), eye=D('EyeRef'), title=D('Title'), logo=D('Logo'), ben=D('BtnEn'), bes=D('BtnEs'))

# FPlaceClose: el cierre (titulo, nombre, logo) frente a donde mira la persona, a 2,6 m
CODES['FPlaceClose'] = '''(fn FPlaceClose ()
  (bind _yaw (.yaw %(camrot)s))
  (bind _fwd (Math|Vector|MakeVector (Math|Trig|Cos(Degrees) _yaw) (Math|Trig|Sin(Degrees) _yaw) 0.0))
  (bind _base (+ %(cam)s (* _fwd 260.0)))
  (bind _rot (Math|Rotator|CombineRotators (Math|Rotator|MakeRotator 90.0 0.0 90.0) (Math|Rotator|MakeRotator 0.0 0.0 _yaw)))
  (Transformation|SetWorldLocationAndRotation %(title)s (+ _base (Math|Vector|MakeVector 0.0 0.0 24.0)) _rot)
  (Transformation|SetWorldScale3D %(title)s (Math|Vector|MakeVector 3.2 0.8 1.0))
  (bind _np (+ _base (Math|Vector|MakeVector 0.0 0.0 -22.0)))
  (Transformation|SetWorldLocationAndRotation %(namep)s _np (Math|Rotator|MakeRotfromZY (- %(cam)s _np) (Math|Vector|MakeVector 0.0 0.0 -1.0)))
  (Transformation|SetWorldScale3D %(namep)s (Math|Vector|MakeVector 1.6 0.4 1.0))
  (Transformation|SetWorldLocationAndRotation %(logo)s (+ _base (Math|Vector|MakeVector 0.0 0.0 -64.0)) _rot)
  (Transformation|SetWorldScale3D %(logo)s (Math|Vector|MakeVector 0.8 0.2 1.0))
  (Development|PrintString "IC: cierre frente a la persona" :bPrintToScreen false))
''' % dict(camrot=CAMROT, cam=CAM, title=D('Title'), logo=D('Logo'), namep=D('NameP'))

# NameSetup: la textura del nombre (la dibuja el teclado) en el plano del cierre; el MID se crea una sola vez
CODES['NameSetup'] = '''(fn NameSetup ()
  (Utilities|IsValid %(nm)s
    (:"Is Not Valid"
      %(nms)s
      (Rendering|Material|SetTextureParameterValue %(nm)s "Card" (Class|BPICKeyboardIC|GetNameRT %(kb)s))
      (Rendering|Material|SetVectorParameterValueonMaterials %(namep)s "Color" (Math|Vector|MakeVector 0.0 0.0 0.0))
      (Rendering|Material|SetScalarParameterValueonMaterials %(namep)s "Base" 0.0)
      (Rendering|Material|SetScalarParameterValueonMaterials %(namep)s "Opacity" 0.0)
      (Rendering|Material|SetScalarParameterValueonMaterials %(namep)s "Gain" 1.2)
      (Rendering|Material|SetScalarParameterValueonMaterials %(namep)s "Boost" 1.4))))
''' % dict(nm=D('NameMID'), kb=D('Kb'), namep=D('NameP'),
           nms=DS('NameMID', '(Rendering|Material|CreateDynamicMaterialInstance %s :ElementIndex 0 :SourceMaterial "%s")' % (D('NameP'), PANE)))

# PickLang: los dos laseres (uno por mano); el clic se guarda en variables ANTES de actualizar los contadores (binds puros, gotcha 409)
CODES['PickLang'] = '''(fn PickLang ()
  (bind _rig %(rig)s)
  (bind _rig2 %(rig2)s)
  (bind _en %(ben)s)
  (bind _es %(bes)s)
  (bind _hit (Class|BPSeqRigSC|GetBeamHitActor _rig))
  (bind _hit2 (Class|BPSeqRigSC|GetBeamHitActor _rig2))
  (bind _ae (>= %(aten)s 0.999))
  (bind _as (>= %(ates)s 0.999))
  (bind _n1 (and (== _hit _en) _ae))
  (bind _n2 (and (== _hit2 _en) _ae))
  (bind _e1 (and (== _hit _es) _as))
  (bind _e2 (and (== _hit2 _es) _as))
  (bind _rp (Class|BPSeqRigSC|GetResPressN _rig))
  (bind _rp2 (Class|BPSeqRigSC|GetResPressN _rig2))
  (Class|BPShareButtonSC|SetHover _en (or _n1 _n2))
  (Class|BPShareButtonSC|SetHover _es (or _e1 _e2))
  %(c1)s
  %(c2)s
  %(ces)s
  %(lp1)s
  %(lp2)s
  (if (or %(gc1)s %(gc2)s)
    (CallFunction|ChooseLang :ES %(gces)s)
    (Class|BPSeqRigSC|Pulse :self (select %(gc1)s _rig _rig2) :bRight (Class|BPSeqRigSC|GetRightHanded (select %(gc1)s _rig _rig2)))
    (elif (and (>= %(al)s 0) (>= %(pt)s 2.0))
      (CallFunction|ChooseLang :ES (== %(al)s 1)))))
''' % dict(rig=D('Rig'), rig2=D('Rig2'), ben=D('BtnEn'), bes=D('BtnEs'), aten=AT('_en'), ates=AT('_es'),
           c1=DS('Clk1', '(and (!= _rp %s) (or _n1 _e1))' % D('LastPressN')),
           c2=DS('Clk2', '(and (!= _rp2 %s) (or _n2 _e2))' % D('LastPressN2')),
           ces=DS('ClkES', '(select (and (!= _rp %s) (or _n1 _e1)) _e1 _e2)' % D('LastPressN')),
           lp1=DS('LastPressN', '_rp'), lp2=DS('LastPressN2', '_rp2'),
           gc1=D('Clk1'), gc2=D('Clk2'), gces=D('ClkES'), al=D('AutoLang'), pt=D('PT'))

CODES['ChooseLang'] = '''(fn ChooseLang (ES)
  %(les)s
  (Class|BPICVoiceIC|SetLangES :self %(voice)s :LangES ES)
  (Class|BPICVoiceIC|HideHint %(voice)s)
  (Class|BPShareButtonSC|Press (select ES %(bes)s %(ben)s))
  (Class|BPShareButtonSC|Vanish (select ES %(ben)s %(bes)s))
  (Development|PrintString (Utilities|String|Append "IC: idioma " (select ES "es" "en")) :bPrintToScreen false)
  %(go)s)
''' % dict(les=DS('LangES', 'ES'), voice=D('Voice'), ben=D('BtnEn'), bes=D('BtnEs'), go=GOPH(2))

CODES['KbWait'] = '''(fn KbWait ()
  (bind _done (Class|BPICKeyboardIC|GetDone %(kb)s))
  (if (or _done (and (> (Utilities|String|Len %(an)s) 0) (>= %(pt)s 2.5)))
    %(nm)s
    (Class|BPICKeyboardIC|KbSetName :self %(kb)s :Name %(gnm)s)
    (Class|BPICKeyboardIC|KbHide %(kb)s)
    (Class|BPICVoiceIC|HideHint %(voice)s)
    (Class|BPSeqRigSC|ResultsBeam %(rig)s false)
    (Class|BPSeqRigSC|ResultsBeam %(rig2)s false)
    %(ses)s
    (Class|BPICLinkIC|LinkNew :self %(link)s :Name %(gnm)s :Ses %(gses)s)
    (CallFunction|NameSetup)
    (Development|PrintString (Utilities|String|Append "IC: nombre " %(gnm)s) :bPrintToScreen false)
    %(go)s))
''' % dict(kb=D('Kb'), an=D('AutoName'), pt=D('PT'), voice=D('Voice'), rig=D('Rig'), rig2=D('Rig2'), link=D('Link'),
           nm=DS('NameStr', '(select _done (Class|BPICKeyboardIC|GetNameStr %s) %s)' % (D('Kb'), D('AutoName'))),
           gnm=D('NameStr'), ses=DS('Session', '(+ %s 1)' % D('Session')), gses=D('Session'), go=GOPH(4))

CODES['ShowPed'] = '''(fn ShowPed ()
  (bind _yaw (.yaw %(camrot)s))
  (bind _fwd (Math|Vector|MakeVector (Math|Trig|Cos(Degrees) _yaw) (Math|Trig|Sin(Degrees) _yaw) 0.0))
  (Transformation|SetActorLocationAndRotation %(ped)s (+ %(cam)s (+ (* _fwd %(rf)s) (Math|Vector|MakeVector 0.0 0.0 (* -1.0 %(rd)s)))) (Math|Rotator|MakeRotator 0.0 0.0 (+ _yaw 180.0)) false true)
  %(pbase)s
  %(pyaw)s
  (Rendering|SetActorHiddenInGame %(ped)s false)
  (Development|PrintString "IC: el pincel flota al frente" :bPrintToScreen false))
''' % dict(camrot=CAMROT, cam=CAM, ped=D('Pedestal'), rf=D('ReachFwd'), rd=D('ReachDown'),
           pbase=DS('PedBase', '(Transformation|GetActorLocation %s)' % D('Pedestal')), pyaw=DS('PedYaw', '(+ _yaw 180.0)'))

CODES['PedSpin'] = '''(fn PedSpin ()
  (bind _tl (* 0.35 %(tilt)s))
  (Transformation|SetActorLocationAndRotation %(ped)s (+ %(base)s (Math|Vector|MakeVector 0.0 0.0 (* %(bob)s (Math|Trig|Sin(Radians) (* %(pt)s 1.6))))) (Math|Rotator|MakeRotator (* _tl (Math|Trig|Sin(Radians) (* %(pt)s 0.9))) (* _tl (Math|Trig|Sin(Radians) (* %(pt)s 0.65))) (+ %(pyaw)s (* %(spin)s %(pt)s))) false true))
''' % dict(ped=D('Pedestal'), spin=D('SpinDeg'), base=D('PedBase'), bob=D('BobCm'), pt=D('PT'), tilt=D('TiltDeg'), pyaw=D('PedYaw'))

CODES['GrabStep'] = '''(fn GrabStep ()
  (CallFunction|PedSpin)
  (bind _pl (Transformation|GetActorLocation %(ped)s))
  (bind _dr (Math|Vector|Distance(Vector) (Transformation|GetWorldLocation %(hr)s) _pl))
  (bind _dl (Math|Vector|Distance(Vector) (Transformation|GetWorldLocation %(hl)s) _pl))
  (bind _auto (and (> %(ah)s 0) (>= %(pt)s 2.0)))
  (bind _late (and (> %(gw)s 0.0) (>= %(pt)s %(gw)s)))
  (if (or (< _dr %(tr)s) (or (and _auto (== %(ah)s 1)) _late))
    %(r1)s
    (CallFunction|Grab)
    (elif (or (< _dl %(tr)s) (and _auto (== %(ah)s 2)))
      %(r0)s
      (CallFunction|Grab))))
''' % dict(ped=D('Pedestal'), hr=D('HandR'), hl=D('HandL'), ah=D('AutoHand'), pt=D('PT'), tr=D('TouchRadius'),
           r1=DS('Right', 'true'), r0=DS('Right', 'false'), gw=D('GrabWait'))

CODES['Grab'] = '''(fn Grab ()
  (Development|PrintString (Utilities|String|Append "IC: pincel tomado con la mano " (select %(r)s "derecha" "izquierda")) :bPrintToScreen false)
  (Class|BPSeqRigSC|SetRightHanded :self %(rig)s :bRightHanded %(r)s)
  (Rendering|SetActorHiddenInGame %(ped)s true)
  (Class|BPTBDirectorNC|SetHandedness :self %(tb)s :LeftHanded (not %(r)s))
  (Class|BPTBDirectorNC|StageIntro %(tb)s)
  %(pp1)s
  %(go)s)
''' % dict(r=D('Right'), rig=D('Rig'), ped=D('Pedestal'), tb=D('TB'), pp1=DS('PulsePend', 'true'), go=GOPH(10))

CODES['PracticeCut'] = '''(fn PracticeCut ()
  %(strokes)s
  (Utilities|Array|Clear %(sloc)s)
  (Utilities|Array|Clear %(scen)s)
  (for _s %(gs)s
    (Utilities|Array|Add %(sloc)s (Transformation|GetActorLocation _s))
    (bind (_o _e) (Collision|GetActorBounds _s false))
    (Utilities|Array|Add %(scen)s _o))
  %(sh0)s
  (Development|PrintString (Utilities|String|Append "IC: trazo de practica listo, trazos = " (Utilities|String|ToString(Integer) (Utilities|Array|Length %(gs)s))) :bPrintToScreen false))
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

# DrawGuard: la punta del pincel fuera del cubo de SpaceSize x SpaceSize x SpaceH (+ GuardM) corta el trazo (InkRelease)
CODES['DrawGuard'] = '''(fn DrawGuard ()
  (bind _tip (Transformation|GetWorldLocation (Class|BPTBDirectorNC|GetSMTip %(tb)s)))
  (bind _c %(cen)s)
  (bind _h (+ (* %(size)s 0.5) %(g)s))
  (if (or (> (Math|Float|Absolute(Float) (- (.x _tip) (.x _c))) _h) (or (> (Math|Float|Absolute(Float) (- (.y _tip) (.y _c))) _h) (or (< (.z _tip) (- (.z _c) %(g)s)) (> (.z _tip) (+ (.z _c) (+ %(sh)s %(g)s))))))
    (Class|BPTBDirectorNC|InkRelease %(tb)s)))
''' % dict(tb=D('TB'), cen=D('Center'), size=D('SpaceSize'), g=D('GuardM'), sh=D('SpaceH'))

CODES['HandsBack'] = '''(fn HandsBack ()
  (if (not %(hon)s)
    %(hon1)s
    (for _c (Actor|GetComponentsByClass (Game|GetPlayerPawn 0) "/Script/Engine.SkeletalMeshComponent")
      (Rendering|SetVisibility _c true true)
      (Development|SetHiddeninGame _c false true))
    (Development|PrintString "IC: se fueron los mandos, vuelven las manos" :bPrintToScreen false)
    (Class|BPTBDirectorNC|SetHidePawnHands :self %(tb)s :bHidePawnHands false)))
''' % dict(hon=D('HandsOn'), hon1=DS('HandsOn', 'true'), tb=D('TB'))

CODES['LinkSync'] = '''(fn LinkSync ()
  (Class|BPICLinkIC|LinkState :self %(link)s :P %(ph)s :TL (Math|Float|Max(Float) (- %(dt)s %(tt)s) 0.0) :InkK %(ink)s :ES %(les)s))
''' % dict(link=D('Link'), ph=D('Phase'), dt=D('DrawTime'), tt=D('TimerT'), ink=D('Ink01'), les=D('LangES'))

CODES['IntroTick'] = '''(fn IntroTick (Dt)
  (switch Utilities|FlowControl|Switch|SwitchonInt %(ph)s
    (:0
      (if (< %(rt)s 0.4)
        (CallFunction|FPlaceTitle))
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
      (if (>= %(pt)s 2.2)
        (Class|BPICKeyboardIC|KbShow :self %(kb)s :Spanish %(les)s)
        %(hintn)s
        %(g3)s))
    (:3
      (CallFunction|KbWait))))
''' % dict(ph=D('Phase'), rt=D('RT'), pt=D('PT'), bat=D('ButtonsAt'), ben=D('BtnEn'), bes=D('BtnEs'), rig=D('Rig'), rig2=D('Rig2'),
           hint=HINT('HintLang'), hintn=HINT('HintName'), kb=D('Kb'), les=D('LangES'),
           lp1=DS('LastPressN', '(Class|BPSeqRigSC|GetResPressN %s)' % D('Rig')), lp2=DS('LastPressN2', '(Class|BPSeqRigSC|GetResPressN %s)' % D('Rig2')),
           p0=P('IC: titulo y botones de idioma'), g1=GOPH(1), g3=GOPH(3))

CODES['GuideTick'] = '''(fn GuideTick (Dt)
  (switch Utilities|FlowControl|Switch|SwitchonInt (- %(ph)s 4)
    (:0
      (if (>= %(pt)s 1.0)
        (Class|BPICHudKitIC|HudInstall %(kit)s)
        (Class|BPICHudKitIC|SetTimeLeft :self %(kit)s :TimeLeft %(dtime)s)
        (Class|BPICHudKitIC|KitSetInk :self %(kit)s :K %(ink)s)
        (Class|BPICHudKitIC|KitSetName :self %(kit)s :Tex (Class|BPICKeyboardIC|GetNameRT %(kb)s))
        %(g5)s))
    (:1
      (if (>= %(pt)s 2.6)
        %(s1)s
        %(g6)s))
    (:2
      (if %(ready)s
        %(s2)s
        (Class|BPICSpaceIC|SpaceReveal %(space)s)
        %(g7)s))
    (:3
      (if %(ready)s
        %(s3)s
        %(g8)s))
    (:4
      (if %(ready)s
        (CallFunction|ShowPed)
        %(s4)s
        %(g9)s))
    (:5
      (CallFunction|GrabStep))
    (:6
      (if (>= %(pt)s 1.5)
        (Class|BPTBDirectorNC|StageBegin %(tb)s)
        (Class|BPTBDirectorNC|SetInkUsed :self %(tb)s :InkUsed 0.0)
        %(s5)s
        (if %(synth)s
          (Class|BPTBDirectorNC|DbgSynth %(tb)s))
        %(p6)s
        %(g11)s))))
''' % dict(ph=D('Phase'), pt=D('PT'), kit=D('Kit'), dtime=D('DrawTime'), ink=D('Ink01'), kb=D('Kb'), ready=READY, space=D('Space'), tb=D('TB'),
           synth=D('TestSynth'), s1=SAY('VoWelcome'), s2=SAY('VoSpace'), s3=SAY('VoInvite'), s4=SAY('VoGrab'), s5=SAY('VoPalette'),
           p6=P('IC: a dibujar (trazo de practica)'), g5=GOPH(5), g6=GOPH(6), g7=GOPH(7), g8=GOPH(8), g9=GOPH(9), g11=GOPH(11))

CODES['DrawTick'] = '''(fn DrawTick (Dt)
  (switch Utilities|FlowControl|Switch|SwitchonInt (- %(ph)s 11)
    (:0
      (CallFunction|DrawGuard)
      (bind _drw (Class|BPCTBToolNC|GetDrawing (Class|BPTBDirectorNC|GetTBTool %(tb)s)))
      (if (and (not _drw) (or (>= (Class|BPTBDirectorNC|GetInkUsed %(tb)s) %(pm)s) (or (and (> %(pw)s 0.0) (>= %(pt)s %(pw)s)) (and (> %(ag)s 0.0) (>= %(pt)s %(ag)s)))))
        (Class|BPTBDirectorNC|SetStageLock :self %(tb)s :bStageLock true)
        (CallFunction|PracticeCut)
        %(g12)s))
    (:1
      (CallFunction|ShrinkStep :Dt Dt)
      (if (>= %(sh)s 0.85)
        (CallFunction|UndoAll)
        (Class|BPTBDirectorNC|StageBegin %(tb)s)
        %(s6)s
        %(tt0)s
        %(req0)s
        (Class|BPICLinkIC|LinkClear %(link)s)
        (if %(synth)s
          (Class|BPTBDirectorNC|DbgSynth %(tb)s))
        %(p12)s
        %(g13)s))
    (:2
      (CallFunction|DrawGuard)
      %(ttp)s
      %(inks)s
      (Class|BPICHudKitIC|SetTimeLeft :self %(kit)s :TimeLeft (Math|Float|Max(Float) (- %(dtime)s %(tt)s) 0.0))
      (Class|BPICHudKitIC|KitSetInk :self %(kit)s :K %(ink)s)
      (if (and (not %(s07)s) (and (<= (- %(dtime)s %(tt)s) 30.0) (not %(speak)s)))
        %(s07t)s
        %(say07)s)
      (if (and (not %(s08)s) (and (<= %(ink)s 0.2) (not %(speak)s)))
        %(s08t)s
        %(say08)s)
      (if (and (not %(req)s) (>= %(tt)s %(dtime)s))
        %(req1)s
        %(eink0)s
        (Class|BPTBDirectorNC|StageRequestEnd %(tb)s)
        %(say09)s
        %(ptime)s)
      (if (and (not %(req)s) (>= %(skp)s 1))
        %(req1)s
        %(eink1)s
        %(say10)s
        %(pink)s)
      (if (>= %(skp)s 1)
        (Class|BPICHudKitIC|HudPlop %(kit)s)
        (Class|BPICLinkIC|LinkPresent :self %(link)s :Pivot (+ %(cen)s (Math|Vector|MakeVector 0.0 0.0 %(pz)s)) :K %(pk)s)
        %(sk0)s
        %(psave)s
        %(g14)s
        (elif (and %(req)s (or (Class|BPTBDirectorNC|GetStageDone %(tb)s) (>= %(tt)s (+ %(dtime)s 30.0))))
          (Class|BPTBDirectorNC|StageOutro %(tb)s)
          (CallFunction|HandsBack)
          (Class|BPICHudKitIC|HudPlop %(kit)s)
          (CallFunction|FPlaceClose)
          %(say12)s
          %(pnone)s
          %(g15)s)))
    (:3
      (if (and (not %(hon)s) (>= %(pt)s (Class|BPTBDirectorNC|GetOutroTime %(tb)s)))
        (CallFunction|HandsBack))
      (if (>= %(skp)s 3)
        %(skt)s)
      (if (and (not %(s11)s) (and (>= %(skp)s 3) (not %(speak)s)))
        %(s11t)s
        %(say11)s)
      (if (or (and (> %(skt0)s 0.0) (== %(skp)s 0)) (>= %(pt)s (+ %(spin)s 40.0)))
        (CallFunction|FPlaceClose)
        %(say12)s
        %(pclose)s
        %(g15)s))))
''' % dict(ph=D('Phase'), pt=D('PT'), tb=D('TB'), pm=D('PracticeM'), pw=D('PracticeWait'), ag=D('AutoGo'), sh=D('ShrinkT'),
           g12=GOPH(12), g13=GOPH(13), g14=GOPH(14), g15=GOPH(15), s6=SAY('VoGo'), tt0=DS('TimerT', '0.0'), req0=DS('Req', 'false'),
           link=D('Link'), synth=D('TestSynth'), p12=P('IC: se fue la practica, arranca el reloj'),
           ttp=DS('TimerT', '(+ %s Dt)' % D('TimerT')), tt=D('TimerT'), dtime=D('DrawTime'), kit=D('Kit'),
           inks=DS('Ink01', '(Math|Float|Clamp(Float) (- 1.0 (/ (Class|BPTBDirectorNC|GetInkUsed %s) (Math|Float|Max(Float) %s 1.0))))' % (D('TB'), D('InkM'))),
           ink=D('Ink01'), s07=D('Said07'), s07t=DS('Said07', 'true'), say07=SAY('Vo30'), s08=D('Said08'), s08t=DS('Said08', 'true'),
           say08=SAY('VoInk'), speak=SPEAK, req=D('Req'), req1=DS('Req', 'true'), eink0=DS('EndInk', 'false'), eink1=DS('EndInk', 'true'),
           say09=SAY('VoTime'), say10=SAY('VoNoInk'), ptime=P('IC: se acabo el tiempo'), pink=P('IC: se acabo la tinta'),
           skp=SKP, cen=D('Center'), pz=D('PresentZ'), pk=D('PresentK'), sk0=DS('SketchT', '0.0'),
           psave=P('IC: el dibujo se presenta al centro'), say12=SAY('VoThanks'), pnone=P('IC: sin dibujo, al cierre'),
           hon=D('HandsOn'), skt=DS('SketchT', '(+ %s Dt)' % D('SketchT')), s11=D('Said11'), s11t=DS('Said11', 'true'),
           say11=SAY('VoLook'), skt0=D('SketchT'), spin=D('SpinShow'), pclose=P('IC: cierre'))

CODES['EndTick'] = '''(fn EndTick (Dt)
  (switch Utilities|FlowControl|Switch|SwitchonInt (- %(ph)s 15)
    (:0
      (if (>= %(pt)s %(hold)s)
        %(g16)s))
    (:1
      (if (>= %(pt)s 2.8)
        %(g17)s))
    (:2
      (if (>= %(pt)s 0.3)
        (if (== %(rm)s 1)
          (Game|OpenLevel(byName) %(lvl)s)
          (else
            (CallFunction|ICReset)))))))
''' % dict(ph=D('Phase'), pt=D('PT'), hold=D('CloseHold'), g16=GOPH(16), g17=GOPH(17), rm=D('ResetMode'), lvl=D('ICLevel'))

# ICReset: vuelve al titulo sin recargar el nivel. Borra los trazos (historia, rehacer y el dibujo presentado), devuelve el
# director del dibujo a su estado de arranque (dormido hasta el proximo StageIntro) y reinicia HUD, teclado y espacio.
CODES['ICReset'] = '''(fn ICReset ()
  (bind _tb %(tb)s)
  (bind _tool (Class|BPTBDirectorNC|GetTBTool _tb))
  (Class|BPCTBToolNC|ClearAll _tool)
  (for _s (Actor|GetAllActorsOfClass "%(strokec)s")
    (Actor|DestroyActor _s))
  (Utilities|Array|Clear %(strokes)s)
  (Class|BPCTBToolNC|SetSketchSet :self _tool :SketchSet %(strokes)s)
  (Class|BPCTBToolNC|SetSketchPhase :self _tool :SketchPhase 0)
  (Class|BPTBDirectorNC|SetSystemDone :self _tb :bSystemDone false)
  (Class|BPTBDirectorNC|SetOutroCalled :self _tb :bOutroCalled false)
  (Class|BPTBDirectorNC|SetStageDone :self _tb :bStageDone false)
  (Class|BPTBDirectorNC|SetInkFired :self _tb :bInkFired false)
  (Class|BPTBDirectorNC|SetStageLock :self _tb :bStageLock false)
  (Class|BPTBDirectorNC|SetInkUsed :self _tb :InkUsed 0.0)
  (Class|BPTBDirectorNC|SetOutroT :self _tb :OutroT 0.0)
  (Class|BPTBDirectorNC|SetHidePawnHands :self _tb :bHidePawnHands true)
  (Transformation|SetRelativeScale3D (Class|BPTBDirectorNC|GetSMRHand _tb) (Class|BPTBDirectorNC|GetRHandS0 _tb))
  (Transformation|SetRelativeScale3D (Class|BPTBDirectorNC|GetSMLHand _tb) (Class|BPTBDirectorNC|GetLHandS0 _tb))
  (Transformation|SetRelativeScale3D (Class|BPTBDirectorNC|GetSMTip _tb) (Class|BPTBDirectorNC|GetTipS0 _tb))
  (Class|BPTBDirectorNC|TourSleepNow _tb)
  (Class|BPICHudKitIC|KitReset %(kit)s)
  (Class|BPICKeyboardIC|KbReset %(kb)s)
  (Class|BPICSpaceIC|SpaceReset %(space)s)
  (Class|BPICVoiceIC|HideHint %(voice)s)
  (Rendering|SetActorHiddenInGame %(ped)s true)
  (CallFunction|ResetVars)
  (Development|PrintString "IC: reinicio en el mismo nivel" :bPrintToScreen false))
''' % dict(tb=D('TB'), strokec=STROKEC, strokes=D('Strokes'), kit=D('Kit'), kb=D('Kb'), space=D('Space'), voice=D('Voice'), ped=D('Pedestal'))

CODES['FlowTick'] = '''(fn FlowTick (Dt)
  (bind _dt (Math|Float|Min(Float) Dt 0.0333))
  %(rtp)s
  %(ptp)s
  %(qt)s
  (CallFunction|FVeil)
  (CallFunction|EnsureHands)
  (CallFunction|LinkSync)
  (if (not (Variables|Default|GetAimDone))
    (CallFunction|PicoAim))
  (if (and (Variables|Default|GetPicoOn) (and (Variables|Default|GetAimDone) (and (>= %(ph)s 10) (<= %(ph)s 14))))
    (CallFunction|PicoTB))
  (if (Variables|Default|GetPoseDump)
    (CallFunction|PoseTick :Dt _dt))
  (if (and %(pp)s (>= %(pt)s 0.12))
    %(pp0)s
    (Class|BPSeqRigSC|Pulse :self %(rig)s :bRight %(right)s))
  (if (< %(ph)s 4)
    (CallFunction|IntroTick :Dt _dt)
    (elif (< %(ph)s 11)
      (CallFunction|GuideTick :Dt _dt)
      (elif (< %(ph)s 15)
        (CallFunction|DrawTick :Dt _dt)
        (else
          (CallFunction|EndTick :Dt _dt))))))
''' % dict(rtp=DS('RT', '(+ %s _dt)' % D('RT')), ptp=DS('PT', '(+ %s _dt)' % D('PT')),
           qt=DS('QuietT', '(select %s 0.0 (+ %s _dt))' % (SPEAK, D('QuietT'))),
           pp=D('PulsePend'), pp0=DS('PulsePend', 'false'), pt=D('PT'), rig=D('Rig'), right=D('Right'), ph=D('Phase'))


# ---- Correccion de poses del PICO (docs/innercanvas/PLAN-INNER-CANVAS.md §5) -----------------------------------------------------
# En el Pico el laser apunta mas arriba, el mando y la paleta quedan ~2 cm mas abajo y la punta del pincel queda pegada al mando:
# el runtime de PICO da otra pose AIM (laser, punta) y otro origen de GRIP (mando, paleta) que el de Meta, contra el que se ajusto todo.
# Sin tocar los sistemas compartidos: AimFixR/L (MotionController SIN fuente de seguimiento: no se mueven solos) cuelgan del aim real
# con (PicoAimFwd, 0, 0) cm y pitch PicoAimPitch; el laser (BP_SeqRig_SC.AimR/L) y la punta (BP_TBDirector_NC.RightAim) leen esos.
# Las mallas de los mandos y la paleta suben PicoGripUp cm en el marco del grip. Solo si es PICO (GetVersionString contiene "pico").
# Linea de comandos (UECommandLine.txt): -PicoFix=0/1 fuerza apagado/encendido · -PicoAimPitch= -PicoAimFwd= -PicoGripUp= ·
# -PoseDump imprime cada 1 s "SCPOSE R/L" = aim respecto del grip (medir en Quest y en Pico: adb logcat -s UE | findstr SCPOSE).
CODES['PicoBoot'] = """(fn PicoBoot ()
  (bind _cmd (Utilities|GetCommandLine))
  (bind (_fv _ff) (Utilities|ParseParamValue _cmd "PicoFix="))
  (Variables|Default|SetPicoOn (select _ff (== (Utilities|String|StringToInteger _fv) 1) (Utilities|String|Contains (HeadMountedDisplay|GetVersionString) "pico")))
  (bind (_pv _pf) (Utilities|ParseParamValue _cmd "PicoAimPitch="))
  (if _pf
    (Variables|Default|SetPicoAimPitch (Utilities|String|StringToFloat _pv)))
  (bind (_wv _wf) (Utilities|ParseParamValue _cmd "PicoAimFwd="))
  (if _wf
    (Variables|Default|SetPicoAimFwd (Utilities|String|StringToFloat _wv)))
  (bind (_uv _uf) (Utilities|ParseParamValue _cmd "PicoGripUp="))
  (if _uf
    (Variables|Default|SetPicoGripUp (Utilities|String|StringToFloat _uv)))
  (Variables|Default|SetPoseDump (Utilities|ParseParam _cmd "PoseDump"))
  (Variables|Default|SetRHandL0 (Class|SceneComponent|GetRelativeLocation (Class|BPTBDirectorNC|GetSMRHand TBX)))
  (Variables|Default|SetLHandL0 (Class|SceneComponent|GetRelativeLocation (Class|BPTBDirectorNC|GetSMLHand TBX)))
  (Variables|Default|SetPalOff0 (Class|BPTBDirectorNC|GetPaletteOffset TBX))
  (if (Variables|Default|GetPicoOn)
    (Class|BPTBDirectorNC|SetPaletteOffset :self TBX :PaletteOffset (+ (Variables|Default|GetPalOff0) (Math|Vector|MakeVector 0.0 0.0 (Variables|Default|GetPicoGripUp)))))
  (Development|PrintString (Utilities|String|Append "IC: correccion PICO " (Utilities|String|Append (select (Variables|Default|GetPicoOn) "ON" "off") (Utilities|String|Append " pitch " (Utilities|String|Append (Utilities|String|ToString(Float) (Variables|Default|GetPicoAimPitch)) (Utilities|String|Append " fwd " (Utilities|String|Append (Utilities|String|ToString(Float) (Variables|Default|GetPicoAimFwd)) (Utilities|String|Append " up " (Utilities|String|ToString(Float) (Variables|Default|GetPicoGripUp))))))))) :bPrintToScreen false))
""".replace('TBX', D('TB'))

CODES['PicoAim'] = """(fn PicoAim ()
  (Utilities|IsValid (Class|BPSeqRigSC|GetAimR RIGX)
    (:"Is Valid"
      (Utilities|IsValid (Class|BPSeqRigSC|GetAimL RIGX)
        (:"Is Valid"
          (Variables|Default|SetRawAimR (Class|BPSeqRigSC|GetAimR RIGX))
          (Variables|Default|SetRawAimL (Class|BPSeqRigSC|GetAimL RIGX))
          (Variables|Default|SetAimDone true)
          (if (Variables|Default|GetPicoOn)
            (Transformation|AttachComponentToComponent (Variables|Default|GetAimFixR) (Variables|Default|GetRawAimR))
            (Transformation|AttachComponentToComponent (Variables|Default|GetAimFixL) (Variables|Default|GetRawAimL))
            (Transformation|SetRelativeLocationAndRotation (Variables|Default|GetAimFixR) (Math|Vector|MakeVector (Variables|Default|GetPicoAimFwd) 0.0 0.0) (Math|Rotator|MakeRotator 0.0 (Variables|Default|GetPicoAimPitch) 0.0))
            (Transformation|SetRelativeLocationAndRotation (Variables|Default|GetAimFixL) (Math|Vector|MakeVector (Variables|Default|GetPicoAimFwd) 0.0 0.0) (Math|Rotator|MakeRotator 0.0 (Variables|Default|GetPicoAimPitch) 0.0))
            (Class|BPSeqRigSC|SetAimR :self RIGX :AimR (Variables|Default|GetAimFixR))
            (Class|BPSeqRigSC|SetAimL :self RIGX :AimL (Variables|Default|GetAimFixL))
            (Development|PrintString "IC: laser PICO corregido" :bPrintToScreen false)))))))
""".replace('RIGX', D('Rig'))

# PicoTB: mientras se dibuja (fases 10-14). La punta cuelga del aim corregido de la mano que dibuja (el director la vuelve a instalar
# si reordena los mandos, por eso se mira cada cuadro) y las mallas de los mandos suben PicoGripUp.
CODES['PicoTB'] = """(fn PicoTB ()
  (Transformation|SetRelativeLocation (Class|BPTBDirectorNC|GetSMRHand TBX) (+ (Variables|Default|GetRHandL0) (Math|Vector|MakeVector 0.0 0.0 (Variables|Default|GetPicoGripUp))))
  (Transformation|SetRelativeLocation (Class|BPTBDirectorNC|GetSMLHand TBX) (+ (Variables|Default|GetLHandL0) (Math|Vector|MakeVector 0.0 0.0 (Variables|Default|GetPicoGripUp))))
  (bind _ra (Class|BPTBDirectorNC|GetRightAim TBX))
  (if (== _ra (Variables|Default|GetRawAimR))
    (Class|BPTBDirectorNC|SetRightAim :self TBX :RightAim (Variables|Default|GetAimFixR))
    (Class|BPTBDirectorNC|InstallTip TBX)
    (Development|PrintString "IC: punta PICO en el aim corregido (derecha)" :bPrintToScreen false)
    (elif (== _ra (Variables|Default|GetRawAimL))
      (Class|BPTBDirectorNC|SetRightAim :self TBX :RightAim (Variables|Default|GetAimFixL))
      (Class|BPTBDirectorNC|InstallTip TBX)
      (Development|PrintString "IC: punta PICO en el aim corregido (izquierda)" :bPrintToScreen false))))
""".replace('TBX', D('TB'))

CODES['PoseTick'] = """(fn PoseTick (Dt)
  (Variables|Default|SetPoseT (+ (Variables|Default|GetPoseT) Dt))
  (if (and (Variables|Default|GetAimDone) (>= (Variables|Default|GetPoseT) 1.0))
    (Variables|Default|SetPoseT 0.0)
    (Utilities|IsValid (Class|BPSeqRigSC|GetGripR RIGX)
      (:"Is Valid"
        (Development|PrintString (Utilities|String|Append "SCPOSE R loc=" (Utilities|String|Append (Utilities|String|ToString(Vector) (Math|Transform|InverseTransformLocation (Transformation|GetWorldTransform (Class|BPSeqRigSC|GetGripR RIGX)) (Transformation|GetWorldLocation (Variables|Default|GetRawAimR)))) (Utilities|String|Append " rot=" (Utilities|String|ToString(Rotator) (Math|Transform|InverseTransformRotation (Transformation|GetWorldTransform (Class|BPSeqRigSC|GetGripR RIGX)) (Transformation|GetWorldRotation (Variables|Default|GetRawAimR))))))) :bPrintToScreen false)
        (Development|PrintString (Utilities|String|Append "SCPOSE L loc=" (Utilities|String|Append (Utilities|String|ToString(Vector) (Math|Transform|InverseTransformLocation (Transformation|GetWorldTransform (Class|BPSeqRigSC|GetGripL RIGX)) (Transformation|GetWorldLocation (Variables|Default|GetRawAimL)))) (Utilities|String|Append " rot=" (Utilities|String|ToString(Rotator) (Math|Transform|InverseTransformRotation (Transformation|GetWorldTransform (Class|BPSeqRigSC|GetGripL RIGX)) (Transformation|GetWorldRotation (Variables|Default|GetRawAimL))))))) :bPrintToScreen false)))))
""".replace('RIGX', D('Rig'))


ORDER = ['PicoBoot', 'PicoAim', 'PicoTB', 'PoseTick', 'ResetVars', 'FBoot', 'FHands', 'EnsureHands', 'FVeil', 'FPlaceTitle', 'FPlaceClose', 'NameSetup', 'ChooseLang', 'PickLang',
         'KbWait', 'ShowPed', 'PedSpin', 'Grab', 'GrabStep', 'PracticeCut', 'ShrinkStep', 'UndoAll', 'DrawGuard', 'HandsBack',
         'LinkSync', 'IntroTick', 'GuideTick', 'DrawTick', 'EndTick', 'ICReset', 'FlowTick']
EVG = '''(event EventBeginPlay
  (CallFunction|FBoot))

(event EventTick (DeltaSeconds)
  (CallFunction|FlowTick :Dt DeltaSeconds))
'''
