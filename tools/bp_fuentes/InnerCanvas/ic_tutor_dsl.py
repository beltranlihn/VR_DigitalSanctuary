# ic_tutor_dsl.py - BP_ICTutor_IC: el tutorial visual de Inner Canvas (2026-11-12, nota de Beltran con dibujo).
# Despues del nombre: la paleta (una BP_DrawPalette_SC de muestra con los 4 colores del dibujo) y el mando (el BP_QuestCtrl_SC del
# pedestal) aparecen al frente, de cara a la persona. El director (BP_ICFlow_IC) dice cada frase y llama TutShow(k): aparece la
# etiqueta k con su linea (0 COLOR, 1 PINCEL, 2 TAMANO, 3 DESHACER, 4 REHACER, 5 GATILLO, que ademas late). TutDemo: el mando toca
# un color, toca un pincel y dibuja un trazo corto con el gatillo apretado. TutOut: la paleta se desarma (las piezas se separan y se
# achican), el mando se achica y el trazo se des-dibuja; despues TutHide limpia. El actor mira como el teclado: +X lejos de la
# persona, +Y a su derecha, +Z arriba. Etiquetas y lineas = planos con MI_ICLabel_IC (M_ICKey_IC + atlas T_ICLabels).
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ic_common import *
PALC = '/SC_Draw/Blueprints/BP_DrawPalette_SC.BP_DrawPalette_SC_C'
CL = lambda x: '(Math|Float|Clamp(Float) %s 0.0 1.0)' % x
LERPV = lambda a, b, k: '(+ %s (* (- %s %s) %s))' % (a, b, a, k)
G = lambda arr, i: '(Utilities|Array|Get(acopy) %s %s)' % (D(arr), i)
SETA = lambda arr, i, x: '(Utilities|Array|SetArrayElem %s %s %s)' % (D(arr), i, x)
ROTTXT = '(Math|Rotator|MakeRotator 90.0 0.0 90.0)'
CODES = {}

CODES['TutBoot'] = '''(fn TutBoot ()
  (Utilities|Array|Clear %(labs)s)
  (Utilities|Array|Clear %(lines)s)
  (Utilities|Array|Clear %(on)s)
  (Utilities|Array|Clear %(labk)s)
  (Utilities|Array|Clear %(anch)s)
  %(addl)s
  %(addk)s
  (for _i (range 6)
    (Utilities|Array|Add %(on)s false)
    (Utilities|Array|Add %(labk)s 0.0)
    (Utilities|Array|Add %(anch)s (Math|Vector|MakeVector 0.0 0.0 0.0)))
  (for _c %(labs)s
    (Rendering|SetVisibility _c false false))
  (for _c %(lines)s
    (Rendering|SetVisibility _c false false))
  %(r0)s
  %(d0)s
  %(o0)s)
''' % dict(labs=D('Labs'), lines=D('Lines'), on=D('On'), labk=D('LabK'), anch=D('Anch'),
           addl='\n  '.join('(Utilities|Array|Add %s %s)' % (D('Labs'), D('L%d' % k)) for k in range(6)),
           addk='\n  '.join('(Utilities|Array|Add %s %s)' % (D('Lines'), D('K%d' % k)) for k in range(6)),
           r0=DS('Run', 'false'), d0=DS('DemoT', '-1.0'), o0=DS('OutT', '-1.0'))

# TutBegin: frente a la persona (como el teclado), la paleta de muestra a un lado (Sd = +1 diestro: paleta a la izquierda, mando a la
# derecha) y el mando del pedestal al otro, mirando a la persona. Las etiquetas se ubican con la paleta a escala final; despues la
# paleta arranca chica y crece en TutTick.
CODES['TutBegin'] = '''(fn TutBegin (Spanish Right PedA TBA)
  %(es)s
  %(tb)s
  %(ped)s
  %(sd)s
  (bind _yaw (.yaw %(camrot)s))
  (bind _fwd (Math|Vector|MakeVector (Math|Trig|Cos(Degrees) _yaw) (Math|Trig|Sin(Degrees) _yaw) 0.0))
  (bind _pos (+ %(cam)s (+ (* _fwd %(dist)s) (Math|Vector|MakeVector 0.0 0.0 (* -1.0 %(below)s)))))
  (Transformation|SetActorLocationAndRotation self _pos (Math|Rotator|MakeRotfromX (- _pos %(cam)s)) false true)
  %(pc)s
  (bind _pal (Game|SpawnActorfromClass "%(palc)s" (Math|Transform|MakeTransform :Location _pos) "AlwaysSpawn"))
  %(spal)s
  (Transformation|AttachActorToActor :self _pal :ParentActor self :LocationRule "SnapToTarget" :RotationRule "SnapToTarget" :ScaleRule "KeepWorld" :bWeldSimulatedBodies false)
  (Transformation|SetActorRelativeLocation _pal %(gpc)s false true)
  (Transformation|SetActorRelativeRotation _pal (Math|Rotator|MakeRotfromXY (Math|Vector|MakeVector 0.0 1.0 0.0) (Math|Vector|MakeVector 0.0 0.0 -1.0)) false true)
  (Transformation|SetActorRelativeScale3D _pal (Math|Vector|MakeVector %(ps)s %(ps)s %(ps)s))
  (Class|BPDrawPaletteSC|SetKeyColors :self _pal :KeyColors (Class|BPTBDirectorNC|GetSlotColorA TBA))
  (Class|BPDrawPaletteSC|SetSelectedColor :self _pal :SelectedColor 0)
  (Class|BPDrawPaletteSC|SetSelectedBrush :self _pal :SelectedBrush 0)
  (Class|BPDrawPaletteSC|ApplyState _pal)
  (Rendering|Material|SetVectorParameterValueonMaterials (Class|BPDrawPaletteSC|GetColor0 _pal) "BaseColor" (Math|Conversions|ToVector(LinearColor) (Utilities|Array|Get(acopy) (Class|BPTBDirectorNC|GetSlotColorA TBA) 0)))
  (Rendering|Material|SetVectorParameterValueonMaterials (Class|BPDrawPaletteSC|GetColor1 _pal) "BaseColor" (Math|Conversions|ToVector(LinearColor) (Utilities|Array|Get(acopy) (Class|BPTBDirectorNC|GetSlotColorA TBA) 1)))
  (Rendering|Material|SetVectorParameterValueonMaterials (Class|BPDrawPaletteSC|GetColor2 _pal) "BaseColor" (Math|Conversions|ToVector(LinearColor) (Utilities|Array|Get(acopy) (Class|BPTBDirectorNC|GetSlotColorA TBA) 2)))
  (Rendering|Material|SetVectorParameterValueonMaterials (Class|BPDrawPaletteSC|GetColor3 _pal) "BaseColor" (Math|Conversions|ToVector(LinearColor) (Utilities|Array|Get(acopy) (Class|BPTBDirectorNC|GetSlotColorA TBA) 3)))
  (Rendering|Material|SetVectorParameterValueonMaterials (Class|BPDrawPaletteSC|GetSwatch _pal) "BaseColor" (Math|Conversions|ToVector(LinearColor) (Utilities|Array|Get(acopy) (Class|BPTBDirectorNC|GetSlotColorA TBA) 0)))
  (Rendering|SetActorHiddenInGame PedA false)
  (Transformation|AttachActorToActor :self PedA :ParentActor self :LocationRule "SnapToTarget" :RotationRule "SnapToTarget" :ScaleRule "KeepWorld" :bWeldSimulatedBodies false)
  %(rest)s
  %(draw)s
  (Transformation|SetActorRelativeLocation PedA (Math|Vector|MakeVector 0.0 (* %(gsd)s %(pedy)s) 2.0) false true)
  (Transformation|SetActorRelativeRotation PedA %(grest)s false true)
  (Transformation|SetActorScale3D PedA (Math|Vector|MakeVector 1.0 1.0 1.0))
  (Class|BPQuestCtrlSC|SetTrigger :self PedA :Amount 0.0)
  (CallFunction|PlaceLabels)
  (Transformation|SetActorRelativeScale3D _pal (Math|Vector|MakeVector 0.001 0.001 0.001))
  %(t0)s
  %(d0)s
  %(o0)s
  %(dp)s
  (for _i (range 6)
    %(on0)s
    %(lk0)s)
  %(run)s
  (Development|PrintString "TUTOR: paleta y mando al frente" :bPrintToScreen false))
''' % dict(es=DS('ES', 'Spanish'), tb=DS('TB', 'TBA'), ped=DS('Ped', 'PedA'), sd=DS('Sd', '1.0'), camrot=CAMROT, cam=CAM,
           dist=D('Dist'), below=D('Below'), pc=DS('Pc', '(Math|Vector|MakeVector 0.0 (* -1.0 (* %s %s)) 0.0)' % (D('Sd'), D('PalY'))),
           palc=PALC, spal=DS('Pal', '_pal'), gpc=D('Pc'), ps=D('PalScale'),
           rest=DS('RestRot', '(Math|Rotator|MakeRotator 0.0 0.0 180.0)'),
           draw=DS('DrawRot', '(Math|Rotator|MakeRotfromX (Math|Vector|MakeVector 0.75 (* -0.45 %s) -0.45))' % D('Sd')),
           gsd=D('Sd'), pedy=D('PedY'), grest=D('RestRot'), t0=DS('T', '0.0'), d0=DS('DemoT', '-1.0'), o0=DS('OutT', '-1.0'),
           dp=DS('DemoPrev', '-1.0'), on0=SETA('On', '_i', 'false'), lk0=SETA('LabK', '_i', '0.0'), run=DS('Run', 'true'))

# PlaceLabels (2026-11-12, "diagramacion ordenada"): las etiquetas van en dos columnas a los lados de la paleta (LabOff relativo al
# centro de la paleta Pc: y < 0 columna izquierda alineada a la derecha, y > 0 columna derecha alineada a la izquierda) y la linea
# termina en el BORDE de la etiqueta que mira al ancla (no la atraviesa).
# PlaceLabels: anclas (en el espacio del actor) = centro de la caja de cada pieza de la paleta (todas las mallas tienen el origen en
# el centro de la paleta) y el gatillo del mando; la etiqueta k va en ancla + LabOff[k] (el Y de la del gatillo se espeja con Sd);
# la linea va del ancla a la etiqueta, en el plano YZ del actor, detras de la etiqueta.
CODES['PlaceLabels'] = '''(fn PlaceLabels ()
  (bind _xf (Transformation|GetActorTransform self))
  (bind _pal %(pal)s)
  (bind (_c1 _e1 _r1) (Collision|GetComponentBounds (Class|BPDrawPaletteSC|GetColor1 _pal)))
  (bind (_c2 _e2 _r2) (Collision|GetComponentBounds (Class|BPDrawPaletteSC|GetColor2 _pal)))
  (bind (_b1 _f1 _q1) (Collision|GetComponentBounds (Class|BPDrawPaletteSC|GetBrush1 _pal)))
  (bind (_b2 _f2 _q2) (Collision|GetComponentBounds (Class|BPDrawPaletteSC|GetBrush0 _pal)))
  (bind (_un _ue _ur) (Collision|GetComponentBounds (Class|BPDrawPaletteSC|GetUndo _pal)))
  (bind (_re _rx _rr) (Collision|GetComponentBounds (Class|BPDrawPaletteSC|GetRedo _pal)))
  %(a0)s
  %(a1)s
  %(a2)s
  %(a3)s
  %(a4)s
  %(a5)s
  (for _k (range 6)
    (bind _a %(ga)s)
    (bind _o %(go)s)
    (bind _rc (select %(es)s %(res)s %(ren)s))
    (bind _asp (+ (/ (.z _rc) 0.125) 0.5))
    (bind _hw (* 0.5 (* %(lh)s _asp)))
    (bind _hh (* 0.5 %(lh)s))
    (bind _cy (+ (.y %(pc)s) (+ (.y _o) (select (< (.y _o) 0.0) (* -1.0 _hw) _hw))))
    (bind _cz (+ (.z %(pc)s) (.z _o)))
    (bind _l %(gl)s)
    (Transformation|SetRelativeLocation _l (Math|Vector|MakeVector (.x _o) _cy _cz) false true)
    (Transformation|SetRelativeScale3D _l (Math|Vector|MakeVector (/ (* %(lh)s _asp) 100.0) (/ %(lh)s 100.0) 1.0))
    (Rendering|Material|SetVectorParameterValueonMaterials _l "Rect" _rc)
    (Rendering|Material|SetScalarParameterValueonMaterials _l "Asp" _asp)
    (Rendering|Material|SetScalarParameterValueonMaterials _l "Hover" 1.0)
    (Rendering|Material|SetScalarParameterValueonMaterials _l "Fade" 0.0)
    (bind _dy (- (.y _a) _cy))
    (bind _dz (- (.z _a) _cz))
    (bind _s (Math|Float|Min(Float) 1.0 (Math|Float|Min(Float) (/ (+ _hw 0.5) (Math|Float|Max(Float) (Math|Float|Absolute(Float) _dy) 0.001)) (/ (+ _hh 0.5) (Math|Float|Max(Float) (Math|Float|Absolute(Float) _dz) 0.001)))))
    (bind _ey (+ _cy (* _dy _s)))
    (bind _ez (+ _cz (* _dz _s)))
    (bind _ly (- _ey (.y _a)))
    (bind _lz (- _ez (.z _a)))
    (bind _len (Math|Float|Max(Float) (Math|Float|Sqrt (+ (* _ly _ly) (* _lz _lz))) 0.3))
    (bind _ln %(gk)s)
    (Transformation|SetRelativeLocationAndRotation _ln (Math|Vector|MakeVector (+ (.x _o) 0.3) (* 0.5 (+ (.y _a) _ey)) (* 0.5 (+ (.z _a) _ez))) (Math|Rotator|CombineRotators %(rottxt)s (Math|Rotator|MakeRotator (* -1.0 (Math|Trig|Atan2(Degrees) _lz _ly)) 0.0 0.0)) false true)
    (Transformation|SetRelativeScale3D _ln (Math|Vector|MakeVector (/ _len 100.0) (/ %(lw)s 100.0) 1.0))
    (Rendering|Material|SetVectorParameterValueonMaterials _ln "Rect" (Math|Vector|MakeVector 0.0 0.875 0.05))
    (Rendering|Material|SetScalarParameterValueonMaterials _ln "Asp" (/ _len %(lw)s))
    (Rendering|Material|SetScalarParameterValueonMaterials _ln "Hover" 2.0)
    (Rendering|Material|SetScalarParameterValueonMaterials _ln "Fade" 0.0)))
''' % dict(pal=D('Pal'), sd=D('Sd'), es=D('ES'), lh=D('LabH'), lw=D('LineW'), rottxt=ROTTXT, pc=D('Pc'),
           a0=SETA('Anch', '0', '(Math|Transform|InverseTransformLocation _xf (* (+ _c1 _c2) 0.5))'),
           a1=SETA('Anch', '1', '(Math|Transform|InverseTransformLocation _xf (* (+ _b1 _b2) 0.5))'),
           a2=SETA('Anch', '2', '(Math|Transform|InverseTransformLocation _xf (Transformation|GetWorldLocation (Class|BPDrawPaletteSC|GetKnob _pal)))'),
           a3=SETA('Anch', '3', '(Math|Transform|InverseTransformLocation _xf _un)'),
           a4=SETA('Anch', '4', '(Math|Transform|InverseTransformLocation _xf _re)'),
           a5=SETA('Anch', '5', '(Math|Transform|InverseTransformLocation _xf (Transformation|GetWorldLocation (Class|BPQuestCtrlSC|GetTrigger %s)))' % D('Ped')),
           ga=G('Anch', '_k'), go=G('LabOff', '_k'), res=G('RectES', '_k'), ren=G('RectEN', '_k'), gl=G('Labs', '_k'), gk=G('Lines', '_k'))

CODES['TutShow'] = '''(fn TutShow (K)
  %s
  (Development|PrintString (Utilities|String|Append "TUTOR: etiqueta " (Utilities|String|ToString(Integer) K)) :bPrintToScreen false))
''' % SETA('On', 'K', 'true')

# TutDemo: las etiquetas se van (la demostracion se ve limpia, pedido de Beltran) y arranca el reloj de DemoStep
CODES['TutDemo'] = '''(fn TutDemo ()
  %s
  %s
  (for _i (range 6)
    %s)
  (Development|PrintString "TUTOR: demostracion" :bPrintToScreen false))
''' % (DS('DemoT', D('T')), DS('DemoPrev', '-0.001'), SETA('On', '_i', 'false'))

# TutOut: las etiquetas se van y la paleta se desarma (el mando solo se achica si sigue colgado del tutor: desde el recorrido del
# 2026-11-12 noche TutOut corre cuando la persona TOMA el mando, que ya esta en su mano): se guarda donde esta cada pieza y hacia donde sale (del centro de la paleta al
# centro de la pieza); OutStep las separa 16 cm y las achica en 1,2 s.
CODES['TutOut'] = '''(fn TutOut ()
  %(ot)s
  (for _i (range 6)
    %(on0)s)
  (Utilities|Array|Clear %(kc)s)
  (Utilities|Array|Clear %(kw)s)
  (Utilities|Array|Clear %(kd)s)
  (bind _pc (Transformation|GetActorLocation %(pal)s))
  (for _c (Actor|GetComponentsByClass %(pal)s "/Script/Engine.StaticMeshComponent")
    (bind (_o _e _r) (Collision|GetComponentBounds _c))
    (Utilities|Array|Add %(kc)s _c)
    (Utilities|Array|Add %(kw)s (Transformation|GetWorldLocation _c))
    (Utilities|Array|Add %(kd)s (Math|Vector|Normalize (- _o _pc))))
  (Development|PrintString "TUTOR: la paleta se desarma" :bPrintToScreen false))
''' % dict(ot=DS('OutT', D('T')), on0=SETA('On', '_i', 'false'), kc=D('KeyC'), kw=D('KeyW'), kd=D('KeyD'), pal=D('Pal'))

CODES['OutStep'] = '''(fn OutStep ()
  (bind _e %(e)s)
  (bind _s (Math|Float|Max(Float) (- 1.0 _e) 0.001))
  (for _i (range (Utilities|Array|Length %(kc)s))
    (bind _c %(gc)s)
    (Transformation|SetWorldLocation _c (+ %(gw)s (* %(gd)s (* 16.0 _e))) false true)
    (Transformation|SetRelativeScale3D _c (Math|Vector|MakeVector _s _s _s)))
  (if (== (Actor|GetAttachParentActor %(ped)s) self)
    (Transformation|SetActorScale3D %(ped)s (Math|Vector|MakeVector _s _s _s)))
  (Utilities|IsValid %(st)s
    (:"Is Valid"
      (Class|BPTBStroke|SetTaper :self %(st)s :T 6.0)
      (Class|BPTBStroke|SetReveal :self %(st)s :R _s))))
''' % dict(e=EASE(CL('(/ (- %s %s) 1.2)' % (D('T'), D('OutT')))), kc=D('KeyC'), gc=G('KeyC', '_i'), gw=G('KeyW', '_i'), gd=G('KeyD', '_i'),
           ped=D('Ped'), st=D('Stroke'))

# DemoStep: tau = T - DemoT. 0-1,2 va al color (punta 2,5 cm delante de la tecla) · 1,2 lo elige · 1,6-2,8 va al pincel · 2,8 lo elige ·
# 3,2-4 va al inicio del trazo · 4-6,4 dibuja (gatillo apretado, trazo con el color 2 de la paleta) · 6,4-7,4 vuelve a su lugar.
# Mando de la demostracion (medido con get_bounds de SM_QuestCtrl_Body_R_SC): el gatillo mira a +X de la malla (= el frente, hacia
# donde apunta); el mango baja hacia (0, -0,6, -0,8). La punta del pincel esta en (5 · 2,4 · 0) cm de la malla, delante del gatillo.
# Para dibujar el mando queda DE PIE (mango abajo) y de perfil, apuntando a la paleta (_dd): rot = inversa de MakeRotFromXZ(+X, arriba
# de la malla) y despues MakeRotFromXZ(_dd, Z). El trazo y los toques salen de esa punta: el dibujo calza con el mando.
CODES['DemoStep'] = '''(fn DemoStep ()
  (bind _t (- %(gt)s %(dt)s))
  (bind _p %(dp)s)
  (bind _rm (Math|Rotator|MakeRotfromXZ (Math|Vector|MakeVector 1.0 0.0 0.0) (Math|Vector|MakeVector 0.0 0.6 0.8)))
  (bind _qi (Math|Transform|InverseTransformRotation (Math|Transform|MakeTransform :Rotation _rm) (Math|Rotator|MakeRotator 0.0 0.0 0.0)))
  (bind _dd (Math|Vector|MakeVector 0.35 -0.85 -0.25))
  (bind _rd (Math|Rotator|CombineRotators _qi (Math|Rotator|MakeRotfromXZ _dd (Math|Vector|MakeVector 0.0 0.0 1.0))))
  (bind _tip0 (+ (Math|Vector|MakeVector 0.0 (* %(sd)s %(pedy)s) 2.0) (+ (* (Math|Vector|GetForwardVector %(rest)s) 5.0) (* (Math|Vector|GetRightVector %(rest)s) 2.4))))
  (bind _tc (+ %(a0)s (Math|Vector|MakeVector -2.5 0.0 0.0)))
  (bind _tb (+ %(a1)s (Math|Vector|MakeVector -2.5 0.0 0.0)))
  (bind _p0 (+ %(pc)s (Math|Vector|MakeVector -6.0 (* %(sd)s 14.0) 14.0)))
  (bind _p1 (+ %(pc)s (Math|Vector|MakeVector -6.0 (* %(sd)s 29.0) 9.0)))
  (bind _u %(u)s)
  (bind _pp (+ %(lp)s (Math|Vector|MakeVector 0.0 0.0 (* 3.0 (Math|Trig|Sin(Radians) (* _u 6.2832))))))
  (bind _tip (select (< _t 1.6) %(l1)s (select (< _t 3.2) %(l2)s (select (< _t 4.0) %(l3)s (select (< _t 6.4) _pp %(l5)s)))))
  (bind _ka (select (< _t 6.4) %(ea)s (- 1.0 %(k5)s)))
  (bind _rot (Math|Rotator|Lerp(Rotator) %(rest)s _rd _ka true))
  (Transformation|SetActorRelativeLocation %(ped)s (- _tip (+ (* (Math|Vector|GetForwardVector _rot) 5.0) (* (Math|Vector|GetRightVector _rot) 2.4))) false true)
  (Transformation|SetActorRelativeRotation %(ped)s _rot false true)
  (Class|BPQuestCtrlSC|SetTrigger :self %(ped)s :Amount (select (and (>= _t 4.0) (< _t 6.4)) 1.0 0.0))
  (bind _w (Math|Transform|TransformLocation (Transformation|GetActorTransform self) _tip))
  (bind _fw (Math|Transform|TransformDirection (Transformation|GetActorTransform self) (Math|Vector|Normalize _dd)))
  (bind _up (Math|Transform|TransformDirection (Transformation|GetActorTransform self) (Math|Vector|MakeVector 0.0 0.0 1.0)))
  (if (and (< _p 1.2) (>= _t 1.2))
    (Class|BPDrawPaletteSC|SetSelectedColor :self %(pal)s :SelectedColor 2)
    (Class|BPDrawPaletteSC|ApplyState %(pal)s)
    (Rendering|Material|SetVectorParameterValueonMaterials (Class|BPDrawPaletteSC|GetColor0 %(pal)s) "BaseColor" (Math|Conversions|ToVector(LinearColor) (Utilities|Array|Get(acopy) (Class|BPTBDirectorNC|GetSlotColorA %(tbv)s) 0)))
    (Rendering|Material|SetVectorParameterValueonMaterials (Class|BPDrawPaletteSC|GetColor1 %(pal)s) "BaseColor" (Math|Conversions|ToVector(LinearColor) (Utilities|Array|Get(acopy) (Class|BPTBDirectorNC|GetSlotColorA %(tbv)s) 1)))
    (Rendering|Material|SetVectorParameterValueonMaterials (Class|BPDrawPaletteSC|GetColor2 %(pal)s) "BaseColor" (Math|Conversions|ToVector(LinearColor) (Utilities|Array|Get(acopy) (Class|BPTBDirectorNC|GetSlotColorA %(tbv)s) 2)))
    (Rendering|Material|SetVectorParameterValueonMaterials (Class|BPDrawPaletteSC|GetColor3 %(pal)s) "BaseColor" (Math|Conversions|ToVector(LinearColor) (Utilities|Array|Get(acopy) (Class|BPTBDirectorNC|GetSlotColorA %(tbv)s) 3)))
    (Rendering|Material|SetVectorParameterValueonMaterials (Class|BPDrawPaletteSC|GetSwatch %(pal)s) "BaseColor" (Math|Conversions|ToVector(LinearColor) (Utilities|Array|Get(acopy) (Class|BPTBDirectorNC|GetSlotColorA %(tbv)s) 2))))
  (if (and (< _p 2.8) (>= _t 2.8))
    (Class|BPDrawPaletteSC|SetSelectedBrush :self %(pal)s :SelectedBrush 1)
    (Class|BPDrawPaletteSC|ApplyState %(pal)s)
    (Rendering|Material|SetVectorParameterValueonMaterials (Class|BPDrawPaletteSC|GetColor0 %(pal)s) "BaseColor" (Math|Conversions|ToVector(LinearColor) (Utilities|Array|Get(acopy) (Class|BPTBDirectorNC|GetSlotColorA %(tbv)s) 0)))
    (Rendering|Material|SetVectorParameterValueonMaterials (Class|BPDrawPaletteSC|GetColor1 %(pal)s) "BaseColor" (Math|Conversions|ToVector(LinearColor) (Utilities|Array|Get(acopy) (Class|BPTBDirectorNC|GetSlotColorA %(tbv)s) 1)))
    (Rendering|Material|SetVectorParameterValueonMaterials (Class|BPDrawPaletteSC|GetColor2 %(pal)s) "BaseColor" (Math|Conversions|ToVector(LinearColor) (Utilities|Array|Get(acopy) (Class|BPTBDirectorNC|GetSlotColorA %(tbv)s) 2)))
    (Rendering|Material|SetVectorParameterValueonMaterials (Class|BPDrawPaletteSC|GetColor3 %(pal)s) "BaseColor" (Math|Conversions|ToVector(LinearColor) (Utilities|Array|Get(acopy) (Class|BPTBDirectorNC|GetSlotColorA %(tbv)s) 3)))
    (Rendering|Material|SetVectorParameterValueonMaterials (Class|BPDrawPaletteSC|GetSwatch %(pal)s) "BaseColor" (Math|Conversions|ToVector(LinearColor) (Utilities|Array|Get(acopy) (Class|BPTBDirectorNC|GetSlotColorA %(tbv)s) 2))))
  (if (and (< _p 4.0) (>= _t 4.0))
    (bind _st (Game|SpawnActorfromClass "%(strokec)s" (Math|Transform|MakeTransform) "AlwaysSpawn"))
    %(sst)s
    (Class|BPTBStroke|SetPreset :self _st :Preset 0)
    (Class|BPTBStroke|SetSize01 :self _st :Size01 0.6)
    (Class|BPTBStroke|SetSizeLo :self _st :SizeLo 0.5)
    (Class|BPTBStroke|SetSizeHi :self _st :SizeHi 1.5)
    (Class|BPTBStroke|SetBaseColor :self _st :BaseColor %(ca)s)
    (Class|BPTBStroke|SetLook _st true %(ca)s %(cb)s)
    (Class|BPTBStroke|StartStroke _st _w _fw _up 0.8))
  (if (and (> _p 4.0) (< _t 6.4))
    (Class|BPTBStroke|UpdatePosition %(st)s _w _fw _up 0.8))
  (if (and (< _p 6.4) (>= _t 6.4))
    (Class|BPTBStroke|EndStroke %(st)s))
  %(dps)s
  (if (>= _t 7.4)
    %(dend)s))
''' % dict(gt=D('T'), dt=D('DemoT'), dp=D('DemoPrev'), sd=D('Sd'), pedy=D('PedY'), rest=D('RestRot'), draw=D('DrawRot'), tl=D('TipL'),
           a0=G('Anch', '0'), a1=G('Anch', '1'), pc=D('Pc'), u=CL('(/ (- _t 4.0) 2.4)'), lp=LERPV('_p0', '_p1', '_u'),
           l1=LERPV('_tip0', '_tc', EASE(CL('(/ _t 1.2)'))), l2=LERPV('_tc', '_tb', EASE(CL('(/ (- _t 1.6) 1.2)'))),
           l3=LERPV('_tb', '_p0', EASE(CL('(/ (- _t 3.2) 0.8)'))), l5=LERPV('_p1', '_tip0', EASE(CL('(/ (- _t 6.4) 1.0)'))),
           k5=EASE(CL('(/ (- _t 6.4) 1.0)')), ea=EASE(CL('(/ _t 1.0)')), ped=D('Ped'), pal=D('Pal'), tbv=D('TB'), strokec=STROKEC,
           sst=DS('Stroke', '_st'), st=D('Stroke'),
           ca='(Utilities|Array|Get(acopy) (Class|BPTBDirectorNC|GetSlotColorA %s) 2)' % D('TB'),
           cb='(Utilities|Array|Get(acopy) (Class|BPTBDirectorNC|GetSlotColorB %s) 2)' % D('TB'),
           dps=DS('DemoPrev', '_t'), dend=DS('DemoT', '-1.0'))

CODES['LabTick'] = '''(fn LabTick (Dt)
  (for _k (range 6)
    %(lk)s
    (bind _f %(glk)s)
    (bind _l %(gl)s)
    (bind _ln %(gk)s)
    (Rendering|Material|SetScalarParameterValueonMaterials _l "Fade" _f)
    (Rendering|Material|SetScalarParameterValueonMaterials _ln "Fade" _f)
    (Rendering|SetVisibility _l (> _f 0.01) false)
    (Rendering|SetVisibility _ln (> _f 0.01) false)))
''' % dict(lk=SETA('LabK', '_k', '(Math|Interpolation|FInterpTo %s (select %s 1.0 0.0) Dt 5.0)' % (G('LabK', '_k'), G('On', '_k'))),
           glk=G('LabK', '_k'), gl=G('Labs', '_k'), gk=G('Lines', '_k'))

CODES['TutHide'] = '''(fn TutHide ()
  %(r0)s
  %(d0)s
  %(o0)s
  (for _c %(labs)s
    (Rendering|SetVisibility _c false false))
  (for _c %(lines)s
    (Rendering|SetVisibility _c false false))
  (Utilities|IsValid %(pal)s
    (:"Is Valid"
      (Class|BPQuestCtrlSC|SetTrigger :self %(ped)s :Amount 0.0)
      (Transformation|DetachFromActor %(ped)s "KeepWorld" "KeepWorld" "KeepWorld")
      (Transformation|SetActorScale3D %(ped)s (Math|Vector|MakeVector 1.0 1.0 1.0))
      (Rendering|SetActorHiddenInGame %(ped)s true)
      (Actor|DestroyActor %(pal)s)
      (Development|PrintString "TUTOR: fin" :bPrintToScreen false)
      (Utilities|IsValid %(st)s
        (:"Is Valid"
          (Actor|DestroyActor %(st)s))))))
''' % dict(r0=DS('Run', 'false'), d0=DS('DemoT', '-1.0'), o0=DS('OutT', '-1.0'), labs=D('Labs'), lines=D('Lines'), pal=D('Pal'),
           ped=D('Ped'), st=D('Stroke'))

CODES['TutTick'] = '''(fn TutTick (Dt)
  (if %(run)s
    %(tp)s
    (CallFunction|LabTick :Dt Dt)
    (if (< %(ot)s 0.0)
      (bind _a (Math|Float|Max(Float) %(ea)s 0.001))
      (Transformation|SetActorRelativeScale3D %(pal)s (Math|Vector|MakeVector (* %(ps)s _a) (* %(ps)s _a) (* %(ps)s _a))))
    (if (and %(on5)s (< %(dt)s 0.0))
      (Class|BPQuestCtrlSC|SetTrigger :self %(ped)s :Amount (+ 0.5 (* 0.5 (Math|Trig|Sin(Radians) (* %(gt)s 5.0))))))
    (if (>= %(dt)s 0.0)
      (CallFunction|DemoStep))
    (if (>= %(ot)s 0.0)
      (CallFunction|OutStep))
    (if (and (>= %(ot)s 0.0) (>= (- %(gt)s %(ot)s) 1.3))
      (CallFunction|TutHide))))
''' % dict(run=D('Run'), tp=DS('T', '(+ %s Dt)' % D('T')), ot=D('OutT'), ea=EASE(CL('(/ %s 0.8)' % D('T'))), pal=D('Pal'),
           ps=D('PalScale'), on5=G('On', '5'), dt=D('DemoT'), ped=D('Ped'), gt=D('T'))

ORDER = ['TutBoot', 'TutShow', 'TutDemo', 'TutOut', 'OutStep', 'LabTick', 'TutHide', 'PlaceLabels', 'DemoStep', 'TutBegin', 'TutTick']
EVG = '''(event EventBeginPlay
  (CallFunction|TutBoot))

(event EventTick (DeltaSeconds)
  (CallFunction|TutTick :Dt (Math|Float|Min(Float) DeltaSeconds 0.05)))
'''
