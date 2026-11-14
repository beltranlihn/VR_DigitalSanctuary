# ic_flow2_dsl.py - BP_ICFlow_IC con el guion del 2026-11-12 (nota de Beltran): sin panel de instrucciones ni trazo de practica.
# Toma las funciones de ic_flow_dsl.py y reemplaza/agrega las del orden nuevo. Fases:
# 0 titulo + botones de idioma al alcance de la mano | 1 se elige TOCANDO | 2 se va el titulo, el mando flota al frente ("toca el
# control con tu mano habil") | 3 tomar el mando tocandolo -> queda en la mano | 4 teclado (laser + gatillo) | 5 tutorial (paleta y
# mando al frente, etiquetas con la voz, demostracion, se desarma; al final las herramientas aparecen en las manos) | 6 el espacio |
# 7 invitacion | 8 HUD + 5 minutos | 9 dibujo | 10 presentacion (el dibujo vuelve girando, NO se va) | 11 texto "ya puedes quitarte
# las gafas" + boton RESET (lo toca el operador) | 12 velo cierra | 13 recentra (ResetOrientationAndPosition) y reinicia (ICReset).
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ic_common import *
import ic_flow_dsl as base

SAY, SPEAK, READY, SKP, AT, HINT = base.SAY, base.SPEAK, base.READY, base.SKP, base.AT, base.HINT
TUTC = IC + 'BP_ICTutor_IC.BP_ICTutor_IC_C'
QC = '(Utilities|Casting|CastToBP_QuestCtrl_SC %s)' % D('Pedestal')
SAYK = lambda k: '(Class|BPICVoiceIC|Say :self %s :Clip (Utilities|Array|Get(acopy) %s %d))' % (D('Voice'), D('VoTut'), k)
TUT = lambda f, args='': '(Class|BPICTutorIC|%s :self %s%s)' % (f, D('Tut'), args)
FWD = '(Math|Vector|MakeVector (Math|Trig|Cos(Degrees) _yaw) (Math|Trig|Sin(Degrees) _yaw) 0.0)'
RGT = '(Math|Vector|MakeVector (* -1.0 (Math|Trig|Sin(Degrees) _yaw)) (Math|Trig|Cos(Degrees) _yaw) 0.0)'
MINH = lambda p: '(Math|Float|Min(Float) (Math|Vector|Distance(Vector) (Transformation|GetWorldLocation %s) %s) (Math|Vector|Distance(Vector) (Transformation|GetWorldLocation %s) %s))' % (D('HandR'), p, D('HandL'), p)
CODES = dict(base.CODES)

CODES['ResetVars'] = base.CODES['ResetVars'].replace("  %s)" % '', '') if False else base.CODES['ResetVars'].replace(
    '(fn ResetVars ()', '(fn ResetVars ()\n  %s\n  %s' % (DS('TutStep', '-1'), DS('Said04', 'false')), 1)

# FBoot: lo de siempre + el tutorial y el boton RESET (tag ic_reset, tapa MI_ICBtn_PlateTopReset_IC)
_brs = D('BtnReset')
CODES['FBoot'] = base.CODES['FBoot'].replace('  (CallFunction|ResetVars)\n', '''  %s
  %s
  (Rendering|Material|SetMaterial (Class|BPShareButtonSC|GetPlate %s) 1 (Class|BPShareButtonSC|GetTopShare %s))
  (Rendering|Material|SetVectorParameterValueonMaterials (Class|BPShareButtonSC|GetTrace %s) "Color" (Math|Conversions|ToVector(LinearColor) %s))
  (Actor|Tick|AddTickPrerequisiteActor :PrerequisiteActor %s)
  (Input|EnableInput self (Game|GetPlayerController 0))
  (CallFunction|ResetVars)
''' % (DS('Tut', '(Actor|GetActorOfClass "%s")' % TUTC),
       DS('BtnReset', AG('(Actor|GetAllActorsOfClassWithTag "%s" "ic_reset")' % BTN, 0)), _brs, _brs, _brs, D('TraceColor'), D('TB')), 1)
assert 'ic_reset' in CODES['FBoot'] and 'AddTickPrerequisiteActor' in CODES['FBoot']

# FVeil: el velo abre al empezar (fase 0) y en el cierre (fase 11) se cierra a la niebla y queda asi hasta la orden del PC. Titulo solo en 0-2.
CODES['FVeil'] = base.CODES['FVeil'].replace('(select (== _ph 16) _close (select (== _ph 17) 1.0 0.0))', '(select (== _ph 11) _close 0.0)') \
    .replace("(bind _clo (or (== _ph 15) (== _ph 16)))", "(bind _clo (== _ph 99))") \
    .replace("(bind _out (select (or (== _ph 2) (== _ph 16))", "(bind _out (select (== _ph 2)") \
    .replace(EASE(MAP('_pt', '0.0', '2.5')), EASE(MAP('_pt', '2.0', '5.0')))
assert '(== _ph 11) _close' in CODES['FVeil'] and '(== _ph 99)' in CODES['FVeil'] and "MapRangeClamped _pt 2.0 5.0" in CODES['FVeil']
# El mensaje del cierre ("ya puedes quitarte las gafas") usa el plano del titulo: su material va sobre el velo (prioridad 32700 > 32600);
# FEndShow le pone el material del idioma y lo coloca al frente; aparece a 1,0-2,6 s y se va a 15-17 s (la proxima persona ve solo niebla).
_v = CODES['FVeil']
_v = _v.replace('  (bind _clo (== _ph 99))\n', '  (bind _clo (== _ph 99))\n  (bind _msg (== _ph 11))\n', 1)
_v = _v.replace('(select (== _ph 15) %s 1.0)))' % EASE(MAP('_pt', '0.3', '1.8')), '(select _msg %s 1.0)))' % EASE(MAP('_pt', '1.0', '2.6')), 1)
_v = _v.replace('(Rendering|Material|SetScalarParameterValueOnMaterials %s "Out" _out)\n  (Rendering|SetVisibility %s (or _intro _clo))' % (D('Title'), D('Title')),
                '(Rendering|Material|SetScalarParameterValueOnMaterials %s "Out" (select _msg %s _out))\n  (Rendering|SetVisibility %s (or _intro _msg))' % (D('Title'), EASE(MAP('_pt', '15.0', '17.0')), D('Title')), 1)
assert '(bind _msg' in _v and '(select _msg (Math' in _v and '(or _intro _msg)' in _v and 'MapRangeClamped _pt 15.0 17.0' in _v, 'FVeil msg'
CODES['FVeil'] = _v

# FPlaceTitle: titulo y logo (los botones ya no van a 1,5 m: FPlaceBtns los pone al alcance de la mano)
CODES['FPlaceTitle'] = '''(fn FPlaceTitle ()
  (bind _tps (Actor|GetAllActorsWithTag %(tag)s))
  (bind _dz (- (.z %(cam)s) (+ (.z %(ps)s) %(eye)s)))
  (if (> (Utilities|Array|Length _tps) 0)
    (bind _tp (Utilities|Array|Get(acopy) _tps 0))
    (bind _tl (+ (Transformation|GetActorLocation _tp) (Math|Vector|MakeVector 0.0 0.0 _dz)))
    (bind _rot (Math|Rotator|CombineRotators (Math|Rotator|MakeRotator 90.0 0.0 90.0) (Math|Rotator|MakeRotator 0.0 0.0 (.yaw (Transformation|GetActorRotation _tp)))))
    (Transformation|SetWorldLocationAndRotation %(title)s _tl _rot)
    (Transformation|SetWorldScale3D %(title)s (Math|Vector|MakeVector 4.0 1.0 1.0))
    (Transformation|SetWorldLocationAndRotation %(logo)s (+ _tl (Math|Vector|MakeVector 0.0 0.0 -62.0)) _rot)
    (Transformation|SetWorldScale3D %(logo)s (Math|Vector|MakeVector 0.98 0.245 1.0))))
''' % dict(tag=D('TagTitle'), cam=CAM, ps=D('PStart'), eye=D('EyeRef'), title=D('Title'), logo=D('Logo'))

# FPlaceBtns: ENGLISH a la izquierda y ESPANOL a la derecha, 40 cm al frente y 30 cm bajo los ojos, inclinados hacia la cara
CODES['FPlaceBtns'] = '''(fn FPlaceBtns ()
  (bind _yaw (.yaw %(camrot)s))
  (bind _base (+ %(cam)s (+ (* %(fwd)s 42.0) (Math|Vector|MakeVector 0.0 0.0 -24.0))))
  (bind _rot (Math|Rotator|MakeRotator 0.0 35.0 (+ _yaw 180.0)))
  (Transformation|SetActorLocationAndRotation %(ben)s (- _base (* %(rgt)s 13.0)) _rot false true)
  (Transformation|SetActorLocationAndRotation %(bes)s (+ _base (* %(rgt)s 13.0)) _rot false true)
  (Transformation|SetActorScale3D %(ben)s (Math|Vector|MakeVector 1.0 1.0 1.0))
  (Transformation|SetActorScale3D %(bes)s (Math|Vector|MakeVector 1.0 1.0 1.0)))
''' % dict(camrot=CAMROT, cam=CAM, fwd=FWD, rgt=RGT, ben=D('BtnEn'), bes=D('BtnEs'))

CODES['FPlaceReset'] = '''(fn FPlaceReset ()
  (bind _yaw (.yaw %(camrot)s))
  (Transformation|SetActorLocationAndRotation %(br)s (+ %(cam)s (+ (* %(fwd)s 42.0) (Math|Vector|MakeVector 0.0 0.0 -24.0))) (Math|Rotator|MakeRotator 0.0 35.0 (+ _yaw 180.0)) false true)
  (Transformation|SetActorScale3D %(br)s (Math|Vector|MakeVector 1.0 1.0 1.0)))
''' % dict(camrot=CAMROT, cam=CAM, fwd=FWD, br=D('BtnReset'))

# PickLang: se elige TOCANDO el boton con cualquier mano (el grip a < BtnPressR; hover a < BtnHoverR). Sin laser.
CODES['PickLang'] = '''(fn PickLang ()
  (bind _en %(ben)s)
  (bind _es %(bes)s)
  (bind _de %(de)s)
  (bind _ds %(ds)s)
  (bind _ae (>= %(aten)s 0.999))
  (bind _as (>= %(ates)s 0.999))
  (Class|BPShareButtonSC|SetHover _en (and _ae (< _de %(hr)s)))
  (Class|BPShareButtonSC|SetHover _es (and _as (< _ds %(hr)s)))
  (if (and _ae (and (< _de %(pr)s) (<= _de _ds)))
    (CallFunction|ChooseLang :ES false)
    (elif (and _as (< _ds %(pr)s))
      (CallFunction|ChooseLang :ES true)
      (elif (and (>= %(al)s 0) (>= %(pt)s 2.0))
        (CallFunction|ChooseLang :ES (== %(al)s 1))))))
''' % dict(ben=D('BtnEn'), bes=D('BtnEs'), de=MINH('(Transformation|GetActorLocation _en)'), ds=MINH('(Transformation|GetActorLocation _es)'),
           aten=AT('_en'), ates=AT('_es'), hr=D('BtnHoverR'), pr=D('BtnPressR'), al=D('AutoLang'), pt=D('PT'))

CODES['FPawnHand'] = '''(fn FPawnHand (Right Vis)
  (for _c (Actor|GetComponentsByClass (Game|GetPlayerPawn 0) "/Script/Engine.SkeletalMeshComponent")
    (if (Utilities|String|Contains (Utilities|GetObjectName _c) (select Right "HandRight" "HandLeft"))
      (Rendering|SetVisibility _c Vis true))))
'''

# FHoldPed: el mando del pedestal pasa a la mano habil, con la pose del mando de dibujo (SM_RHand/SM_LHand del director de dibujo,
# + PicoGripUp en Pico) y la malla de esa mano; la mano del pawn de ese lado se oculta.
CODES['FHoldPed'] = '''(fn FHoldPed ()
  (bind _up (select %(po)s %(gu)s 0.0))
  (Class|BPQuestCtrlSC|SetLeft :self %(qc)s :bLeft (not %(r)s))
  (Class|BPQuestCtrlSC|ApplyHand %(qc)s)
  (Class|BPQuestCtrlSC|SetTrigger :self %(qc)s :Amount 0.0)
  (Class|BPQuestCtrlSC|ApplyTrigger %(qc)s)
  (Transformation|AttachActorToComponent :self %(ped)s :Parent (select %(r)s %(hr)s %(hl)s) :SocketName "None" :LocationRule "SnapToTarget" :RotationRule "SnapToTarget" :ScaleRule "KeepWorld" :bWeldSimulatedBodies false)
  (Transformation|SetActorRelativeLocation %(ped)s (select %(r)s (Math|Vector|MakeVector 5.686 0.54 (+ -1.678 _up)) (Math|Vector|MakeVector 5.877 -1.567 (+ -2.05 _up))) false true)
  (Transformation|SetActorRelativeRotation %(ped)s (select %(r)s (Math|Rotator|MakeRotator 64.231 -13.566 -83.539) (Math|Rotator|MakeRotator 65.0 0.0 -95.0)) false true)
  (CallFunction|FPawnHand :Right %(r)s :Vis false))
''' % dict(po=D('PicoOn'), gu=D('PicoGripUp'), qc=QC, r=D('Right'), ped=D('Pedestal'), hr=D('HandR'), hl=D('HandL'))

# Grab: el mando queda en la mano y aparece el teclado (laseres + gatillo); la voz pide el nombre
CODES['Grab'] = '''(fn Grab ()
  (Development|PrintString (Utilities|String|Append "IC: mando tomado con la mano " (select %(r)s "derecha" "izquierda")) :bPrintToScreen false)
  (Class|BPSeqRigSC|SetRightHanded :self %(rig)s :bRightHanded %(r)s)
  (Class|BPTBDirectorNC|SetHandedness :self %(tb)s :LeftHanded (not %(r)s))
  (CallFunction|FHoldPed)
  (Class|BPICVoiceIC|HideHint %(voice)s)
  (Class|BPICKeyboardIC|KbShow :self %(kb)s :Spanish %(les)s)
  %(hintn)s
  %(sayn)s
  (Class|BPSeqRigSC|ResultsBeam %(rig)s true)
  (Class|BPSeqRigSC|ResultsBeam %(rig2)s true)
  %(pp1)s
  (Variables|Default|SetClk1 false)
  %(go)s)
''' % dict(r=D('Right'), rig=D('Rig'), rig2=D('Rig2'), tb=D('TB'), voice=D('Voice'), kb=D('Kb'), les=D('LangES'),
           hintn=HINT('HintName'), sayn=SAY('VoName'), pp1=DS('PulsePend', 'true'), go=GOPH(4))

CODES['KbWait'] = base.CODES['KbWait'].replace('(Variables|Default|SetPhase 4)', '%s\n        (Variables|Default|SetPhase 5)' % DS('TutStep', '-1'), 1)
assert 'SetPhase 5' in CODES['KbWait'] and 'SetTutStep -1' in CODES['KbWait']

CODES['IntroTick'] = '''(fn IntroTick (Dt)
  (switch Utilities|FlowControl|Switch|SwitchonInt %(ph)s
    (:0
      (if (< %(rt)s 0.4)
        (CallFunction|FPlaceTitle))
      (if (< %(rt)s %(bat)s)
        (CallFunction|FPlaceBtns))
      (if (>= %(rt)s %(bat)s)
        (Class|BPShareButtonSC|Appear %(ben)s)
        (Class|BPShareButtonSC|Appear %(bes)s)
        %(hint)s
        %(p0)s
        %(g1)s))
    (:1
      (CallFunction|PickLang))
    (:2
      (if (>= %(pt)s 2.2)
        (CallFunction|ShowPed)
        %(hintt)s
        %(s1)s
        %(s04)s
        (Variables|Default|SetClk1 false)
        %(g3)s))
    (:3
      (if (and (not %(s04g)s) %(ready)s)
        %(s04t)s
        %(s4)s)
      (if (and %(s04g)s (and (not (Variables|Default|GetClk1)) (and (not (Class|BPICVoiceIC|GetSpeaking (Variables|Default|GetVoice))) (>= (Variables|Default|GetQuietT) 0.8))))
        (Variables|Default|SetClk1 true)
        %(hintt)s)
      (CallFunction|GrabStep))
    (:4
      (if (and (not (Variables|Default|GetClk1)) (and (not (Class|BPICVoiceIC|GetSpeaking (Variables|Default|GetVoice))) (>= (Variables|Default|GetQuietT) 0.8)))
        (Variables|Default|SetClk1 true)
        %(hintn)s)
      (CallFunction|KbWait))))
''' % dict(ph=D('Phase'), rt=D('RT'), pt=D('PT'), bat=D('ButtonsAt'), ben=D('BtnEn'), bes=D('BtnEs'), hint=HINT('HintLang'),
           p0=P('IC: titulo y botones de idioma al alcance de la mano'), g1=GOPH(1), hintt=HINT('HintTouch'), hintn=HINT('HintName'), s1=SAY('VoWelcome'),
           s04=DS('Said04', 'false'), g3=GOPH(3), s04g=D('Said04'), ready=READY, s04t=DS('Said04', 'true'), s4=SAY('VoGrab'))

# FlowTut (fase 5): el mando sale de la mano y el tutorial arranca; despues, cada paso k a TutAt[k] segundos (linea de tiempo, no el
# largo de la voz: cada TutAt deja lugar a la frase mas larga, la de espanol).
CODES['FlowTut'] = '''(fn FlowTut ()
  (if (== %(ts)s -1)
    (Transformation|DetachFromActor %(ped)s "KeepWorld" "KeepWorld" "KeepWorld")
    (CallFunction|FPawnHand :Right %(r)s :Vis true)
    (Class|BPICVoiceIC|SetSubs :self %(voice)s :bSubs false)
    %(begin)s
    %(ts0)s)
  (if (and (>= %(ts)s 0) (and (< %(ts)s 10) (>= %(pt)s %(at)s)))
    (CallFunction|TutAct :K %(ts)s)
    %(tsp)s))
''' % dict(ts=D('TutStep'), ped=D('Pedestal'), r=D('Right'), voice=D('Voice'),
           begin=TUT('TutBegin', ' :Spanish %s :Right %s :PedA %s :TBA %s' % (D('LangES'), D('Right'), QC, D('TB'))),
           ts0=DS('TutStep', '0'), pt=D('PT'), at='(Utilities|Array|Get(acopy) %s %s)' % (D('TutAt'), D('TutStep')),
           tsp=DS('TutStep', '(+ %s 1)' % D('TutStep')))

CODES['TutAct'] = '''(fn TutAct (K)
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
      %(out)s)
    (:9
      (Class|BPICVoiceIC|SetSubs :self %(voice)s :bSubs true)
      (Class|BPTBDirectorNC|StageIntro %(tb)s)
      %(s8)s
      %(p9)s
      %(g6)s)))
''' % dict(s0=SAYK(0), s1=SAYK(1), s2=SAYK(2), s3=SAYK(3), s4=SAYK(4), s5=SAYK(5), s6=SAYK(6), s7=SAYK(7), s8=SAYK(8),
           t0=TUT('TutShow', ' :K 0'), t1=TUT('TutShow', ' :K 1'), t2=TUT('TutShow', ' :K 2'), t3=TUT('TutShow', ' :K 3'),
           t4=TUT('TutShow', ' :K 4'), t5=TUT('TutShow', ' :K 5'), demo=TUT('TutDemo'), out=TUT('TutOut'), tb=D('TB'),
           p9=P('IC: paleta y pincel en las manos'), voice=D('Voice'), g6=GOPH(6))

CODES['GuideTick'] = '''(fn GuideTick (Dt)
  (switch Utilities|FlowControl|Switch|SwitchonInt (- %(ph)s 5)
    (:0
      (CallFunction|FlowTut))
    (:1
      (if %(ready)s
        %(s2)s
        (Class|BPICSpaceIC|SpaceReveal %(space)s)
        %(g7)s))
    (:2
      (if %(ready)s
        %(s3)s
        %(g8)s))
    (:3
      (if %(ready)s
        (Class|BPICHudKitIC|HudInstall %(kit)s)
        (Class|BPICHudKitIC|SetTimeLeft :self %(kit)s :TimeLeft %(dtime)s)
        (Class|BPICHudKitIC|KitSetInk :self %(kit)s :K 1.0)
        (Class|BPICHudKitIC|KitSetName :self %(kit)s :Tex (Class|BPICKeyboardIC|GetNameRT %(kb)s))
        (Class|BPTBDirectorNC|StageBegin %(tb)s)
        (Class|BPTBDirectorNC|SetInkUsed :self %(tb)s :InkUsed 0.0)
        %(ink1)s
        %(sgo)s
        %(tt0)s
        %(req0)s
        (Class|BPICLinkIC|LinkClear %(link)s)
        (if %(synth)s
          (Class|BPTBDirectorNC|DbgSynth %(tb)s))
        %(p9)s
        %(g9)s))))
''' % dict(ph=D('Phase'), ready=READY, s2=SAY('VoSpace'), space=D('Space'), g7=GOPH(7), s3=SAY('VoInvite'), g8=GOPH(8), kit=D('Kit'),
           dtime=D('DrawTime'), kb=D('Kb'), tb=D('TB'), ink1=DS('Ink01', '1.0'), sgo=SAY('VoGo'), tt0=DS('TimerT', '0.0'),
           req0=DS('Req', 'false'), link=D('Link'), synth=D('TestSynth'), p9=P('IC: arranca el dibujo libre'), g9=GOPH(9))

# DrawTick (9 dibujo, 10 presentacion): igual que antes, pero sin practica; al final el dibujo NO se va: tras SpinShow s girando
# (un par de vueltas) pasa a FEndShow.
_DT = base.CODES['DrawTick']
_i0 = _DT.index('    (:2\n')
_i1 = _DT.index('    (:3\n')
_draw = _DT[_i0:_i1].replace('    (:2\n', '    (:0\n', 1)
_pres = _DT[_i1:]
_draw = _draw.replace('(Variables|Default|SetPhase 14)', '(Variables|Default|SetPhase 10)')
_a = _draw.index('          (CallFunction|HandsBack)\n          (Class|BPICHudKitIC|HudPlop')
_b = _draw.index('(Variables|Default|SetPT 0.0)', _a)
_draw = _draw[:_a] + '          (Class|BPICHudKitIC|HudPlop %s)\n          (CallFunction|FEndShow)' % D('Kit') + _draw[_b + len('(Variables|Default|SetPT 0.0)'):]
_pres = _pres.replace('    (:3\n', '    (:1\n', 1)
_c = _pres.index('      (if (or (and (> ')
_pres = _pres[:_c] + '''      (if (or (and (> %s 0.0) (== %s 0)) (>= %s (+ %s 40.0)))
        (CallFunction|FEndShow)))))
''' % (D('SketchT'), SKP, D('PT'), D('SpinShow'))
CODES['DrawTick'] = _DT[:_DT.index('(switch')] + '(switch Utilities|FlowControl|Switch|SwitchonInt (- %s 9)\n' % D('Phase') + _draw + _pres
assert CODES['DrawTick'].count('(') == CODES['DrawTick'].count(')'), 'parentesis DrawTick'
assert 'FEndShow' in _draw and 'SetPhase 10' in _draw and 'SetPhase 15' not in CODES['DrawTick']

CODES['FEndShow'] = '''(fn FEndShow ()
  (CallFunction|HandsBack)
  %(say)s
  (Variables|Default|SetClk1 false)
  (Variables|Default|SetEndHintOff false)
  (Development|PrintString "IC: fin: quitarse las gafas + niebla blanca; espera la orden del PC" :bPrintToScreen false)
  %(g11)s
  (bind _yaw (.yaw %(camrot)s))
  (bind _base (+ %(cam)s (* %(fwd)s 300.0)))
  (bind _rot (Math|Rotator|CombineRotators (Math|Rotator|MakeRotator 90.0 0.0 90.0) (Math|Rotator|MakeRotator 0.0 0.0 _yaw)))
  (Transformation|SetWorldLocationAndRotation %(title)s (+ _base (Math|Vector|MakeVector 0.0 0.0 -8.0)) _rot)
  (Transformation|SetWorldScale3D %(title)s (Math|Vector|MakeVector 2.4 0.6 1.0))
  (if (Variables|Default|GetLangES)
    (Rendering|Material|SetMaterial %(title)s 0 "/Game/InnerCanvas/Materials/MI_TourTitle_ENDES.MI_TourTitle_ENDES")
    (else
      (Rendering|Material|SetMaterial %(title)s 0 "/Game/InnerCanvas/Materials/MI_TourTitle_ENDEN.MI_TourTitle_ENDEN"))))
''' % dict(say=SAY('VoThanks'), g11=GOPH(11), camrot=CAMROT, cam=CAM, fwd=FWD, title=D('Title'))

# RemoteCmd: orden del PC. Modo 1 = recentrar (la posicion y la mirada de la gafa en este momento pasan a ser el centro y el frente)
# y reiniciar desde la niebla; modo 2 = solo reiniciar. Sirve en cualquier fase.
CODES['RemoteCmd'] = '''(fn RemoteCmd (Mode)
  (Development|PrintString (Utilities|String|Append "IC: orden del PC: " (select (== Mode 1) "RESET (recentra y reinicia)" "REINICIAR")) :bPrintToScreen false)
  (if (== Mode 1)
    (Input|HeadMountedDisplay|ResetOrientationandPosition :Yaw 0.0 :Options "OrientationAndPosition")
    (CallFunction|ICReset)
    (else
      (CallFunction|ICReset))))
'''

# FResetPick: el operador toca RESET (o, solo en prueba, AutoGo > 0 lo aprieta a los AutoGo + 4 s)
CODES['FResetPick'] = '''(fn FResetPick ()
  (if (and (not (Variables|Default|GetClk1)) (and (not (Class|BPICVoiceIC|GetSpeaking (Variables|Default|GetVoice))) (>= (Variables|Default|GetQuietT) 0.8)))
    (Variables|Default|SetClk1 true)
    (Class|BPICVoiceIC|ShowHint :self %(voice)s :Id %(he)s))
  (bind _b %(br)s)
  (bind _d %(d)s)
  (bind _ok (>= %(at)s 0.999))
  (Class|BPShareButtonSC|SetHover _b (and _ok (< _d %(hr)s)))
  (if (or (and _ok (< _d %(pr)s)) (and (> %(ag)s 0.0) (>= %(pt)s (+ %(ag)s 4.0))))
    (Class|BPShareButtonSC|Press _b)
    (Class|BPICVoiceIC|HideHint %(voice)s)
    (Development|PrintString "IC: RESET (recentra y vuelve al titulo)" :bPrintToScreen false)
    %(g12)s))
''' % dict(br=D('BtnReset'), d=MINH('(Transformation|GetActorLocation _b)'), at=AT('_b'), hr=D('BtnHoverR'), pr=D('BtnPressR'),
           ag=D('AutoGo'), pt=D('PT'), voice=D('Voice'), he=D('HintEnd'), g12=GOPH(12))

CODES['EndTick'] = '''(fn EndTick (Dt)
  (if (and (> %(ag)s 0.0) (>= %(pt)s (+ %(ag)s 4.0)))
    (CallFunction|RemoteCmd :Mode 1)))
''' % dict(pt=D('PT'), ag=D('AutoGo'))

# ICReset: lo de siempre + tutorial, mando del pedestal (vuelve a ser derecho y suelto) y manos del pawn
CODES['ICReset'] = base.CODES['ICReset'].replace('  (CallFunction|ResetVars)\n', '''  %s
  (Class|BPICVoiceIC|SetSubs :self %s :bSubs true)
  (Transformation|DetachFromActor %s "KeepWorld" "KeepWorld" "KeepWorld")
  (Class|BPQuestCtrlSC|SetLeft :self %s :bLeft false)
  (Class|BPQuestCtrlSC|ApplyHand %s)
  (Class|BPQuestCtrlSC|ApplyTrigger %s)
  (CallFunction|FPawnHand :Right true :Vis true)
  (CallFunction|FPawnHand :Right false :Vis true)
  (Rendering|Material|SetMaterial %s 0 %s)
  (CallFunction|ResetVars)
''' % (TUT('TutHide'), D('Voice'), D('Pedestal'), QC, QC, QC, D('Title'), D('TitleMI')), 1)
assert 'TutHide' in CODES['ICReset'] and 'ApplyTrigger' in CODES['ICReset']

_FT = base.CODES['FlowTick']
CODES['FlowTick'] = _FT.replace('(and (>= %s 10) (<= %s 14))' % (D('Phase'), D('Phase')), '(and (>= %s 6) (<= %s 13))' % (D('Phase'), D('Phase'))) \
    .replace('(if (< %s 4)\n    (CallFunction|IntroTick' % D('Phase'), '(if (< %s 5)\n    (CallFunction|IntroTick' % D('Phase')) \
    .replace('(elif (< %s 11)\n      (CallFunction|GuideTick' % D('Phase'), '(elif (< %s 9)\n      (CallFunction|GuideTick' % D('Phase')) \
    .replace('(elif (< %s 15)\n        (CallFunction|DrawTick' % D('Phase'), '(elif (< %s 11)\n        (CallFunction|DrawTick' % D('Phase'))
CODES['FlowTick'] = CODES['FlowTick'].replace('  (CallFunction|LinkSync)\n', '''  (CallFunction|LinkSync)
  (if (> (Class|BPICLinkIC|GetCmd %(l)s) 0)
    (CallFunction|RemoteCmd :Mode (Class|BPICLinkIC|GetCmd %(l)s))
    (Class|BPICLinkIC|SetCmd :self %(l)s :Cmd 0))
  (bind _sh (select (select %(r)s (Input|EnhancedActionValues|IA_Shoot_Right) (Input|EnhancedActionValues|IA_Shoot_Left)) 1.0 0.0))
  (if (or (== %(ph)s 4) (>= %(ph)s 6))
    (if (!= (Class|BPQuestCtrlSC|GetTarget %(qc)s) _sh)
      (Development|PrintString (Utilities|String|Append "IC: gatillo " (Utilities|String|ToString(Float) _sh)) :bPrintToScreen false))
    (Class|BPQuestCtrlSC|SetTrigger :self %(qc)s :Amount _sh))
  (bind _shr (select (Input|EnhancedActionValues|IA_Shoot_Right) 1.0 0.0))
  (bind _shl (select (Input|EnhancedActionValues|IA_Shoot_Left) 1.0 0.0))
  (for _hc (Actor|GetComponentsByClass (Game|GetPlayerPawn 0) "/Script/Engine.SkeletalMeshComponent")
    (if (Utilities|String|Contains (Utilities|GetObjectName _hc) "Hand")
      (Class|ABPMannequinsXR|SetPoseAlphaIndexCurl :self (Utilities|Casting|CastToABP_MannequinsXR (Components|SkeletalMesh|GetAnimInstance _hc)) :PoseAlphaIndexCurl (Math|Interpolation|FInterpTo (Class|ABPMannequinsXR|GetPoseAlphaIndexCurl (Utilities|Casting|CastToABP_MannequinsXR (Components|SkeletalMesh|GetAnimInstance _hc))) (select (Utilities|String|Contains (Utilities|GetObjectName _hc) "HandRight") _shr _shl) _dt 16.0))))
  (Class|BPTBDirectorNC|TrigApply :self %(tb)s :T (select %(r)s (Class|BPTBDirectorNC|GetTrigR %(tb)s) (Class|BPTBDirectorNC|GetTrigL %(tb)s)) :Body (select %(r)s (Class|BPTBDirectorNC|GetSMRHand %(tb)s) (Class|BPTBDirectorNC|GetSMLHand %(tb)s)) :Axis (select %(r)s (Math|Vector|MakeVector 0.976 -0.2177 -0.0083) (Math|Vector|MakeVector 0.976 0.2177 0.0083)) :V (Math|Float|Clamp(Float) (Class|BPQuestCtrlSC|GetValue %(qc)s)))
''' % dict(l=D('Link'), ph=D('Phase'), qc=QC, r=D('Right'), tb=D('TB')), 1)
assert 'GetCmd' in CODES['FlowTick'] and 'IA_Shoot_Right' in CODES['FlowTick']
assert '(>= %s 6) (<= %s 13)' % (D('Phase'), D('Phase')) in CODES['FlowTick'] and '(< %s 5)' % D('Phase') in CODES['FlowTick'] \
    and '(< %s 9)' % D('Phase') in CODES['FlowTick'] and '(< %s 11)' % D('Phase') in CODES['FlowTick'], 'FlowTick'

# FHands: lo de siempre + la mano nueva de Inner Canvas (PolyOne "Free Pack - VR Hands", CC-BY 4.0, encajada al esqueleto de
# SK_MannequinsXR con tools/innercanvas/mano_ic_encaje.py) y su material. Solo en IC: el pawn de la Obra no se toca. El material
# va en el COMPONENTE porque BP_VRPawn_SC trae OverrideMaterials = MI_Hand_SC.
_HM = '/Game/InnerCanvas/Hands/'
CODES['FHands'] = '''(fn FHands ()
  (Utilities|IsValid (Game|GetPlayerPawn 0)
    (:"Is Valid"
      (for _c (Actor|GetComponentsByClass (Game|GetPlayerPawn 0) "/Script/Engine.SkeletalMeshComponent")
        (if (Utilities|String|Contains (Utilities|GetObjectName _c) "HandRight")
          %s
          (Components|SkeletalMesh|SetSkeletalMeshAsset _c "%sSKM_ICMano8_R.SKM_ICMano8_R")
          (Rendering|Material|SetMaterial _c 0 "%sMI_ICHand_IC.MI_ICHand_IC")
          (Transformation|SetRelativeScale3D _c (Math|Vector|MakeVector 0.9 0.9 0.9)))
        (if (Utilities|String|Contains (Utilities|GetObjectName _c) "HandLeft")
          %s
          (Components|SkeletalMesh|SetSkeletalMeshAsset _c "%sSKM_ICMano8_L.SKM_ICMano8_L")
          (Rendering|Material|SetMaterial _c 0 "%sMI_ICHand_IC.MI_ICHand_IC")
          (Transformation|SetRelativeScale3D _c (Math|Vector|MakeVector 0.9 0.9 0.9)))))))
''' % (DS('HandR', '(Transformation|GetAttachParent _c)'), _HM, _HM, DS('HandL', '(Transformation|GetAttachParent _c)'), _HM, _HM)
_FHANDS_SOLO = CODES['FHands']

# MODO COMPARAR (pedido de Beltran 2026-11-12 noche): la mano de Unreal queda en el pawn con su material translucido blanco
# (MI_Hand_SC) y encima va la nueva en un componente agregado por el director, que copia la pose de la otra en cada cuadro
# (SetLeaderPoseComponent: mismo esqueleto), translucida en verde (MI_ICHandCmp_IC), a escala 0,9. Para volver: COMPARAR = False.
COMPARAR = False
_CMP = '''          (bind _f%(s)s (Utilities|Casting|CastToSkeletalMeshComponent (Game|AddComponentbyClass :Class "/Script/Engine.SkeletalMeshComponent")))
          (Transformation|AttachComponentToComponent :self _f%(s)s :Parent _c :SocketName "None" :LocationRule "SnapToTarget" :RotationRule "SnapToTarget" :ScaleRule "KeepRelative" :bWeldSimulatedBodies false)
          (Components|SkeletalMesh|SetSkeletalMeshAsset _f%(s)s "%(hm)sSKM_ICMano8_%(s)s.SKM_ICMano8_%(s)s")
          (Rendering|Material|SetMaterial _f%(s)s 0 "%(hm)sMI_ICHandCmp_IC.MI_ICHandCmp_IC")
          (Transformation|SetRelativeScale3D _f%(s)s (Math|Vector|MakeVector 1.0 1.0 1.0))
          (Components|SkinnedMesh|SetLeaderPoseComponent _f%(s)s _c)'''
# una sola mano (Beltran 2026-11-12 noche, despues de comparar): la nueva v8 en el componente del pawn, BLANCA TRANSLUCIDA
# (MI_Hand_SC, el material de manos de la Obra, con el fundido hacia la muneca), escala 0,9.
CODES['FHands'] = _FHANDS_SOLO.replace(_HM + 'MI_ICHand_IC.MI_ICHand_IC', '/Game/SoulCharger/Core/Pawn/Materials/MI_Hand_SC.MI_Hand_SC')
assert 'MI_Hand_SC.MI_Hand_SC' in CODES['FHands'] and 'SKM_ICMano8_R' in CODES['FHands']
if COMPARAR:
    CODES['FHands'] = '''(fn FHands ()
  (Utilities|IsValid (Game|GetPlayerPawn 0)
    (:"Is Valid"
      (for _c (Actor|GetComponentsByClass (Game|GetPlayerPawn 0) "/Script/Engine.SkeletalMeshComponent")
        (if (Utilities|String|Contains (Utilities|GetObjectName _c) "HandRight")
          %s
%s)
        (if (Utilities|String|Contains (Utilities|GetObjectName _c) "HandLeft")
          %s
%s)))))
''' % (DS('HandR', '(Transformation|GetAttachParent _c)'), _CMP % dict(s='R', hm=_HM),
       DS('HandL', '(Transformation|GetAttachParent _c)'), _CMP % dict(s='L', hm=_HM))

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
        (Collision|SetCollisionEnabled (Class|BPICKeyboardIC|GetBoard %(kb)s) "QueryOnly")
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
           kb=D('Kb'), tut=D('Tut'), ink1=DS('Ink01', '1.0'), sgo=SAY('VoGo'), phud=P('IC: HUD con el nombre, 5:00 y la tinta'), ready=READY, g5=GOPH(5),
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


# =====================================================================================================================================
# (11-13: idioma y nombre SIN voz; la bienvenida narrativa VoGo = IC_28 suena con el HUD; el cierre VoThanks = IC_29, la reflexion)
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
NL2, NL8 = chr(10) + '  ', chr(10) + '        '
if RECORRIDO2:
    TY_EXPR = '''(bind _tps (Actor|GetAllActorsWithTag %s))
  (bind _tv (- (Transformation|GetActorLocation (Utilities|Array|Get(acopy) _tps 0)) %s))
  (bind _yaw (select (> (Utilities|Array|Length _tps) 0) (Math|Trig|Atan2(Degrees) (.y _tv) (.x _tv)) (.yaw %s)))''' % (D('TagTitle'), CAM, CAMROT)
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
        %(ty)s
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
        (Class|BPICTutorIC|FrameShow %(tut)s)
        (Transformation|SetActorLocationAndRotation %(kb)s (Math|Transform|TransformLocation (Transformation|GetActorTransform %(tut)s) (Math|Vector|MakeVector 5.0 0.0 -6.0)) (Transformation|GetActorRotation %(tut)s) false true)
        (Transformation|SetActorScale3D %(kb)s (Math|Vector|MakeVector 0.9 0.9 0.9))
        (Transformation|SetRelativeScale3D (Class|BPICKeyboardIC|GetField %(kb)s) (Math|Vector|MakeVector 0.56 0.14 1.0))
        (Transformation|SetRelativeLocation (Class|BPICKeyboardIC|GetField %(kb)s) (Math|Vector|MakeVector 0.0 0.0 24.5) false true)
        (for _ky (Class|BPICKeyboardIC|GetKeys %(kb)s)
          (Rendering|Material|SetVectorParameterValueonMaterials _ky "Accent" (Math|Vector|MakeVector 0.85 0.9 0.88)))
        (Collision|SetCollisionEnabled (Class|BPICKeyboardIC|GetBoard %(kb)s) "QueryOnly")
        (Variables|Default|SetClk1 false)
        %(hname)s
        %(pkb)s
        %(g3)s))
    (:3
      (CallFunction|KbWait))))
""" % dict(ph=D('Phase'), rt=D('RT'), pt=D('PT'), bat=D('ButtonsAt'), ben=D('BtnEn'), bes=D('BtnEs'), rig=D('Rig'), rig2=D('Rig2'),
           camrot=CAMROT, kb=D('Kb'), les=D('LangES'), ready=READY, ty=TY_EXPR.replace(NL2, NL8), tut=D('Tut'), voice=D('Voice'),
           hlang=TUT('HintShow', ' :Mode 1 :Spanish false :Pos (+ %s (+ (* %s 150.0) (Math|Vector|MakeVector 0.0 0.0 -72.0)))' % (CAM, FWD)),
           hname=TUT('HintShow', ' :Mode 2 :Spanish %s :Pos (Math|Transform|TransformLocation (Transformation|GetActorTransform %s) (Math|Vector|MakeVector 0.0 -4.5 -29.0))' % (D('LangES'), D('Kb'))),
           hoff=TUT('HintOff'),
           lp1=DS('LastPressN', '(Class|BPSeqRigSC|GetResPressN %s)' % D('Rig')), lp2=DS('LastPressN2', '(Class|BPSeqRigSC|GetResPressN %s)' % D('Rig2')),
           p0=P('IC: titulo, botones de idioma y la pista (laser)'), g1=GOPH(1), s1=SAY('VoWelcome'), s04=DS('Said04', 'false'),
           pkb=P('IC: bienvenida, teclado y su pista'), g3=GOPH(3), s04g=D('Said04'), s04t=DS('Said04', 'true'), sn=SAY('VoName'))

    # Botones de idioma y su pista CENTRADOS BAJO EL TITULO (Beltran 11-12 noche: "aparecieron un poco hacia la izquierda"): el yaw sale
    # de la direccion al TargetPoint del titulo (fijo en el mundo), no de hacia donde miraba la persona al empezar.
    CODES['FPlaceBtns'] = """(fn FPlaceBtns ()
  %(ty)s
  (bind _base (+ %(cam)s (+ (* %(fwd)s 150.0) (Math|Vector|MakeVector 0.0 0.0 -55.0))))
  (bind _rot (Math|Rotator|MakeRotator 0.0 15.0 (+ _yaw 180.0)))
  (Transformation|SetActorLocationAndRotation %(ben)s (- _base (* %(rgt)s 20.0)) _rot false true)
  (Transformation|SetActorLocationAndRotation %(bes)s (+ _base (* %(rgt)s 20.0)) _rot false true)
  (Transformation|SetActorScale3D %(ben)s (Math|Vector|MakeVector 1.5 1.5 1.5))
  (Transformation|SetActorScale3D %(bes)s (Math|Vector|MakeVector 1.5 1.5 1.5)))
""" % dict(ty=TY_EXPR, cam=CAM, fwd=FWD, rgt=RGT, ben=D('BtnEn'), bes=D('BtnEs'))

    # Colisiones que tapaban el laser de los botones de idioma (VR Preview de Beltran, 11-12 noche): el plano del teclado (Board) queda
    # delante a la altura de las manos aunque el teclado no se vea -> solo con el teclado a la vista; el mando del pedestal y la mesa
    # del sistema de dibujo (ocultos, BlockAllDynamic) -> sin colision.
    BOARD = '(Class|BPICKeyboardIC|GetBoard %s)' % D('Kb')
    CODES['FBoot'] = CODES['FBoot'].replace('  (CallFunction|ResetVars)\n', """  (Collision|SetActorEnableCollision %s false)
  (Collision|SetActorEnableCollision (Actor|GetActorOfClass "/SC_Draw/Blueprints/BP_TBTable.BP_TBTable_C") false)
  (Collision|SetCollisionEnabled %s "NoCollision")
  (Rendering|Material|SetMaterial %s 0 "/Game/InnerCanvas/Materials/M_ICLogo_IC.M_ICLogo_IC")
  (Rendering|SetTranslucentSortPriority (Class|BPICSpaceIC|GetFloor %s) 32650)
  (CallFunction|ResetVars)
""" % (D('Pedestal'), BOARD, D('Logo'), D('Space')), 1)
    assert 'SetActorEnableCollision' in CODES['FBoot']
    CODES['ICReset'] = CODES['ICReset'].replace('  (CallFunction|ResetVars)\n', '  (Collision|SetCollisionEnabled %s "NoCollision")\n  (CallFunction|ResetVars)\n' % BOARD, 1)
    assert 'GetBoard' in CODES['ICReset']

    # Reinicio desde el visor (Beltran 11-13): mantener los DOS grips 5 s = lo mismo que RESET del PC (RemoteCmd 1: recentra donde esta
    # parada la persona y reinicia). Lee IA_Hand_Grasp (el grip analogico de la animacion de la mano, que llega en el visor) y, de
    # respaldo, IA_Grab_*_Pressed. Funciona en cualquier fase.
    GRIP = lambda s: '(Math|Float|Max(Float) (Input|EnhancedActionValues|IA_Hand_Grasp_%s) (Input|EnhancedActionValues|IA_Grab_%s_Pressed))' % (s, s)
    CODES['FlowTick'] = CODES['FlowTick'].replace('  (CallFunction|LinkSync)' + chr(10), """  (CallFunction|LinkSync)
  %s
  (if (>= %s 5.0)
    %s
    (Development|PrintString "IC: los dos grips 5 s -> RESET desde el visor (recentra y reinicia)" :bPrintToScreen false)
    (CallFunction|RemoptCmd :Mode 1))
""".replace('RemoptCmd', 'RemoteCmd') % (DS('GripHoldT', '(select (and (> %s 0.7) (> %s 0.7)) (+ %s _dt) 0.0)' % (GRIP('Left'), GRIP('Right'), D('GripHoldT'))),
                                        D('GripHoldT'), DS('GripHoldT', '-30.0')) + chr(10), 1)
    assert 'GripHoldT' in CODES['FlowTick']

    # FlowTut: igual, con 9 pasos (0 paleta y pincel, 1-6 etiquetas, 7 demo, 8 cartas)
    CODES['FlowTut'] = CODES['FlowTut'].replace('(< %s 10)' % D('TutStep'), '(< %s 9)' % D('TutStep'), 1)
    # subtitulos de las voces SIEMPRE (Beltran 11-13: 'faltan subtitulos'): el tutorial ya no los apaga
    CODES['FlowTut'] = CODES['FlowTut'].replace(':bSubs false)', ':bSubs true)', 1)
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
    # leer el segundo); el gatillo del rig que apunta una carta la elige. AutoHand 1/2 (prueba) elige derecha/izquierda a los 3 s.
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
      (elif (and (> %(ah)s 0) (>= %(pt)s 3.0))
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
  (Class|BPICTutorIC|PalSndAll :self %(tut)s :Mute false)
  (Class|BPICVoiceIC|SetSubs :self %(voice)s :bSubs true)
  (CallFunction|FPawnHand :Right true :Vis false)
  (CallFunction|FPawnHand :Right false :Vis false)
  (Class|BPICSpaceIC|SpaceReveal %(space)s)
  %(say)s
  %(c2f)s
  %(go)s)
""" % dict(voice=D('Voice'), tut=D('Tut'), r=D('Right'), rig=D('Rig'), rig2=D('Rig2'), tb=D('TB'), pick=TUT('TutPick', ' :Right %s' % D('Right')), space=D('Space'),
           say=SAY('VoInvite'), c2f=DS('Clk2', 'false'), go=GOPH(7))

    CODES['GuideTick'] = """(fn GuideTick (Dt)
  (switch Utilities|FlowControl|Switch|SwitchonInt (- %(ph)s 4)
    (:0
      (if (and (not %(c2)s) (>= %(pt)s 0.3))
        %(c2t)s
        %(hoff)s
        (Class|BPICTutorIC|SetFrameOn :self %(tut)s :FrameOn false)
        (Collision|SetCollisionEnabled (Class|BPICKeyboardIC|GetBoard %(kb)s) "NoCollision")
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
        (Class|BPICTutorIC|PalSndAll :self %(tut)s :Mute false)
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
           hoff=TUT('HintOff'), tut=D('Tut'), ts_1=DS('TutStep', '-1'), tb=D('TB'), tt0=DS('TimerT', '0.0'), req0=DS('Req', 'false'), link=D('Link'),
           synth=D('TestSynth'), p9=P('IC: arranca el dibujo libre'), g9=GOPH(9))

    # FEndShow: el dibujo ya se fue; niebla blanca y el TITULO + el logo en su lugar original (FPlaceTitle: el TargetPoint del titulo,
    # fijo en el mundo), y se queda asi hasta la orden del PC. Sin el cartel del cierre.
    CODES['FEndShow'] = """(fn FEndShow ()
  (CallFunction|HandsBack)
  %(say)s
  (Variables|Default|SetClk1 false)
  (Variables|Default|SetEndHintOff false)
  %(woff)s
  (Class|BPICSpaceIC|SpaceReset %(space)s)
  (Development|PrintString "IC: fin: niebla blanca y el titulo en su lugar; espera la orden del PC" :bPrintToScreen false)
  %(g11)s
  (CallFunction|FPlaceTitle)
  (Rendering|Material|SetMaterial %(title)s 0 %(tmi)s)
  (Rendering|SetTranslucentSortPriority %(logo)s 32700))
""" % dict(say=SAY('VoThanks'), woff=TUT('WarnSet', ' :On false'), space=D('Space'), g11=GOPH(11), title=D('Title'), tmi=D('TitleMI'), logo=D('Logo'))

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
    for _k in ('IntroTick', 'GuideTick', 'TutAct', 'FlowTut', 'PickHand', 'HandChosen', 'FEndShow', 'FVeil', 'ICReset', 'FlowTick', 'FPlaceBtns', 'FBoot'):
        assert CODES[_k].count('(') == CODES[_k].count(')'), 'parentesis ' + _k

NEW = ['FPlaceBtns', 'FPlaceReset', 'FPawnHand', 'FHoldPed', 'FlowTut', 'TutAct', 'FEndShow', 'FResetPick', 'PickHand', 'HandChosen']
ORDER = ['FHands', 'ResetVars', 'FBoot', 'FVeil', 'FPlaceTitle', 'FPlaceBtns', 'FPlaceReset', 'PickLang', 'FPawnHand', 'FHoldPed', 'Grab', 'KbWait',
         'IntroTick', 'TutAct', 'FlowTut', 'PickHand', 'HandChosen', 'GuideTick', 'FEndShow', 'DrawTick', 'ICReset', 'RemoteCmd', 'EndTick', 'FlowTick']
EVG = base.EVG
