# ic_tutor2_dsl.py - BP_ICTutor_IC v2: el MARCO de instrucciones de Inner Canvas (recorrido v2, PDF de Beltran 2026-11-12 noche;
# memoria ic-recorrido-v2-marco). Reemplaza a ic_tutor_dsl.py (v1, respaldo .bak_v2).
# Despues del HUD: marco semitransparente (como el HUD) con el logo INNER CANVAS y "Instructions"; la paleta de muestra y el mando,
# grandes, por delante; entran JUNTOS en 0,5 s (la paleta sin la espera de 3 s de su aparicion: AppearDelay 0).
# El director dice cada frase y llama TutShow(k): se enciende el MANTO blanco de esa zona (M0..M4, colgados de la Base de la paleta:
# sectores de anillo de M_ICMantle_IC que dejan ver los botones) + el punto en la zona, la linea, el punto de la punta y el texto
# (0 Color, 1 Brush Type, 2 Brush Size, 3 Undo, 4 Redo, 5 Draw = el gatillo, que late). Se van sumando (como el PDF).
# TutDemo: se van los textos; el mando toca un color, un pincel y dibuja un trazo grande dentro del marco.
# TutCards: se van paleta, mando y trazo; en el mismo marco, dos cartas (paleta y mando chicos, en espejo para la zurda) con
# "Select your dominant hand"; el director lee el laser con CardHov(rig) -> HitK (-1 nada, 0 izquierda, 1 derecha) y llama TutPick.
# Ademas: HintShow / HintOff = el texto bajo los botones de idioma (dos lineas, ingles y espanol) o bajo el teclado; WarnSet = el
# aviso "vuelve a la zona de dibujo" pegado a la vista (se cuelga de la camara del pawn).
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ic_common import *
HERE = os.path.dirname(os.path.abspath(__file__))
TX = json.load(open(os.path.join(HERE, 'texts_rects.json'), encoding='utf-8'))
PALC = '/SC_Draw/Blueprints/BP_DrawPalette_SC.BP_DrawPalette_SC_C'
QCC = '/SC_Base/Blueprints/BP_QuestCtrl_SC.BP_QuestCtrl_SC_C'
TXTM = '/Game/InnerCanvas/Materials/M_ICText_IC.M_ICText_IC'
PANM = '/Game/InnerCanvas/Materials/M_ICPanel_IC.M_ICPanel_IC'
MANM = '/Game/InnerCanvas/Materials/M_ICMantle_IC.M_ICMantle_IC'
TITM = '/Game/InnerCanvas/Materials/MI_TourTitle_INNERCANVAS.MI_TourTitle_INNERCANVAS'
CL = lambda x: '(Math|Float|Clamp(Float) %s 0.0 1.0)' % x
LERPV = lambda a, b, k: '(+ %s (* (- %s %s) %s))' % (a, b, a, k)
G = lambda arr, i: '(Utilities|Array|Get(acopy) %s %s)' % (D(arr), i)
SETA = lambda arr, i, x: '(Utilities|Array|SetArrayElem %s %s %s)' % (D(arr), i, x)
ROTTXT = '(Math|Rotator|MakeRotator 90.0 0.0 90.0)'
F = lambda x: '%.6f' % x
VEC = lambda x, y, z: '(Math|Vector|MakeVector %s %s %s)' % (x, y, z)
SP = lambda c, n, x: '(Rendering|Material|SetScalarParameterValueonMaterials %s "%s" %s)' % (c, n, x)
VP = lambda c, n, x: '(Rendering|Material|SetVectorParameterValueonMaterials %s "%s" %s)' % (c, n, x)
VIS = lambda c, x: '(Rendering|SetVisibility %s %s false)' % (c, x)
RV = lambda k: VEC(F(TX[k][0]), F(TX[k][1]), F(TX[k][2]))
NL2 = chr(10) + '  '
PALROT = '(Math|Rotator|MakeRotfromXY (Math|Vector|MakeVector 0.0 1.0 0.0) (Math|Vector|MakeVector 0.0 0.0 -1.0))'
PALROT_L = '(Math|Rotator|MakeRotfromXY (Math|Vector|MakeVector 0.0 -1.0 0.0) (Math|Vector|MakeVector 0.0 0.0 1.0))'


def RECT(c, ken, kes=None, es=None):
    """Rect y VS de un texto del atlas en el componente c (con kes: segun el idioma es)"""
    r = RV(ken) if not kes else '(select %s %s %s)' % (es, RV(kes), RV(ken))
    return '%s\n  %s' % (VP(c, 'Rect', r), SP(c, 'VS', F(TX[ken][3])))


def ASP(ken, kes=None, es=None):
    return F(TX[ken][4]) if not kes else '(select %s %s %s)' % (es, F(TX[kes][4]), F(TX[ken][4]))


def PLACE(c, x, y, z, h, asp, align):
    """texto c de alto h y aspecto asp; align -1 = termina en y, 0 = centrado en y, 1 = empieza en y"""
    w = '(* %s %s)' % (h, asp)
    cy = y if align == 0 else '(+ %s (* %s %s))' % (y, F(0.5 * align), w)
    return ('(Transformation|SetRelativeLocation %s %s false true)\n  '
            '(Transformation|SetRelativeScale3D %s (Math|Vector|MakeVector (/ %s 100.0) (/ %s 100.0) 1.0))') % (c, VEC(x, cy, z), c, w, h)


CODES = {}

_txt = ['L%d' % k for k in range(6)] + ['K%d' % k for k in range(6)]
CODES['TutBoot'] = '''(fn TutBoot ()
  (Utilities|Array|Clear %(labs)s)
  (Utilities|Array|Clear %(lines)s)
  (Utilities|Array|Clear %(da)s)
  (Utilities|Array|Clear %(db)s)
  (Utilities|Array|Clear %(mants)s)
  (Utilities|Array|Clear %(on)s)
  (Utilities|Array|Clear %(labk)s)
  (Utilities|Array|Clear %(anch)s)
  %(adds)s
  %(fix)s
  (for _i (range 6)
    (Utilities|Array|Add %(on)s false)
    (Utilities|Array|Add %(labk)s 0.0)
    (Utilities|Array|Add %(anch)s (Math|Vector|MakeVector 0.0 0.0 0.0)))
  (for _c (Actor|GetComponentsByClass self "/Script/Engine.StaticMeshComponent")
    (Rendering|SetVisibility _c false false)
    (Collision|SetCollisionEnabled _c "NoCollision")
    (Rendering|SetTranslucentSortPriority _c 6))
  %(mats)s
  (for _c %(lines)s
    %(rk)s)
  (for _c %(da)s
    %(rd)s)
  (for _c %(db)s
    %(rd)s)
  (Rendering|SetTranslucentSortPriority %(frame)s 1)
  (Rendering|Material|SetVectorParameterValueonMaterials %(frame)s "Rim" (Math|Vector|MakeVector 0.45 0.272 0.85))
  (Rendering|SetTranslucentSortPriority %(cl)s 2)
  (Rendering|SetTranslucentSortPriority %(cr)s 2)
  (Rendering|SetTranslucentSortPriority %(warn)s 20)
  (Collision|SetCollisionEnabled %(hit)s "NoCollision")
  %(r0)s
  %(d0)s
  %(o0)s
  %(c0)s
  %(p0)s
  %(cs0)s
  %(h0)s
  %(w0)s
  %(hk0)s
  %(wk0)s
  %(wa0)s)
''' % dict(labs=D('Labs'), lines=D('Lines'), da=D('DotsA'), db=D('DotsB'), mants=D('Mants'), on=D('On'), labk=D('LabK'), anch=D('Anch'),
           adds='\n  '.join(['(Utilities|Array|Add %s %s)' % (D('Labs'), D('L%d' % k)) for k in range(6)] +
                            ['(Utilities|Array|Add %s %s)' % (D('Lines'), D('K%d' % k)) for k in range(6)] +
                            ['(Utilities|Array|Add %s %s)' % (D('DotsA'), D('DA%d' % k)) for k in range(6)] +
                            ['(Utilities|Array|Add %s %s)' % (D('DotsB'), D('DB%d' % k)) for k in range(6)] +
                            ['(Utilities|Array|Add %s %s)' % (D('Mants'), D('M%d' % k)) for k in range(5)]),
           fix='\n  '.join(['(Components|StaticMesh|SetStaticMesh %s "/Engine/BasicShapes/Plane.Plane")\n  (Transformation|SetRelativeRotation %s %s false true)' % (D(n), D(n), ROTTXT)
                            for n in ['Frame', 'Logo', 'Hdr', 'CardL', 'CardR', 'CardHit', 'Sel', 'CapL', 'CapR', 'H0', 'H1', 'Warn'] + ['DA%d' % k for k in range(6)] + ['DB%d' % k for k in range(6)]] +
                           ['(Components|StaticMesh|SetStaticMesh %s "/Engine/BasicShapes/Plane.Plane")' % D('M%d' % k) for k in range(5)] +
                           ['(Development|SetHiddeninGame %s true false)' % D('CardHit')]),
           mats='\n  '.join(['(Rendering|Material|SetMaterial %s 0 "%s")' % (D(n), TXTM) for n in _txt +['Hdr', 'Sel', 'CapL', 'CapR', 'H0', 'H1', 'Warn'] + ['DA%d' % k for k in range(6)] + ['DB%d' % k for k in range(6)]] +
                            ['(Rendering|Material|SetMaterial %s 0 "%s")' % (D(n), PANM) for n in ('Frame', 'CardL', 'CardR')] +
                            ['(Rendering|Material|SetMaterial %s 0 "%s")' % (D('M%d' % k), MANM) for k in range(5)] +
                            ['(Rendering|Material|SetMaterial %s 0 "%s")' % (D('Logo'), TITM)]),
           rk=RECT('_c', 'white').replace('\n  ', '\n    '), rd=RECT('_c', 'dot').replace('\n  ', '\n    '),
           frame=D('Frame'), cl=D('CardL'), cr=D('CardR'), warn=D('Warn'), hit=D('CardHit'),
           r0=DS('Run', 'false'), d0=DS('DemoT', '-1.0'), o0=DS('OutT', '-1.0'), c0=DS('CardsT', '-1.0'), p0=DS('PickT', '-1.0'),
           cs0=DS('CardsOn', 'false'), h0=DS('HintOn', 'false'), w0=DS('WarnOn', 'false'), hk0=DS('HintK', '0.0'), wk0=DS('WarnK', '0.0'),
           wa0=DS('WarnAtt', 'false'))

# TutBegin: el actor frente a la persona a Dist cm y Below cm bajo los ojos, mirandola; la paleta de muestra a la izquierda y el mando
# a la derecha (siempre de diestro: la mano se elige despues, en las cartas). Marco, logo y titulo a la escala del marco (las medidas
# del PDF en fraccion de FrameW / FrameH). Todo arranca con Fade 0 y TutTick lo hace entrar junto en 0,5 s.
CODES['TutBegin'] = '''(fn TutBegin (Spanish Right PedA TBA)
  %(es)s
  %(tb)s
  %(ped)s
  %(sd)s
  (bind _yaw (.yaw %(camrot)s))
  (bind _fwd (Math|Vector|MakeVector (Math|Trig|Cos(Degrees) _yaw) (Math|Trig|Sin(Degrees) _yaw) 0.0))
  (bind _pos (+ %(cam)s (+ (* _fwd %(dist)s) (Math|Vector|MakeVector 0.0 0.0 (* -1.0 %(below)s)))))
  (if (not %(fon)s)
    (Transformation|SetActorLocationAndRotation self _pos (Math|Rotator|MakeRotfromX (- _pos %(cam)s)) false true))
  %(pc)s
  (bind _pal (Game|SpawnActorfromClass "%(palc)s" (Math|Transform|MakeTransform :Location (Transformation|GetActorLocation self)) "AlwaysSpawn"))
  %(spal)s
  (Collision|SetActorEnableCollision _pal false)
  (Class|BPDrawPaletteSC|SetAppearDelay :self _pal :AppearDelay 0.0)
  (Transformation|AttachActorToActor :self _pal :ParentActor self :LocationRule "SnapToTarget" :RotationRule "SnapToTarget" :ScaleRule "KeepWorld" :bWeldSimulatedBodies false)
  (Transformation|SetActorRelativeLocation _pal %(gpc)s false true)
  (Transformation|SetActorRelativeRotation _pal %(palrot)s false true)
  (Transformation|SetActorRelativeScale3D _pal (Math|Vector|MakeVector %(ps)s %(ps)s %(ps)s))
  (Class|BPDrawPaletteSC|SetSideSize :self _pal :SideSize 1.25)
  (Class|BPDrawPaletteSC|ApplySideScale _pal)
  (Class|BPDrawPaletteSC|SetKeyColors :self _pal :KeyColors (Class|BPTBDirectorNC|GetSlotColorA TBA))
  (Class|BPDrawPaletteSC|SetSelectedColor :self _pal :SelectedColor 0)
  (Class|BPDrawPaletteSC|SetSelectedBrush :self _pal :SelectedBrush 0)
  (Class|BPDrawPaletteSC|ApplyState _pal)
  (CallFunction|PalSndAll :Mute false)
  %(cols)s
  (Rendering|SetActorHiddenInGame PedA false)
  (Transformation|AttachActorToActor :self PedA :ParentActor self :LocationRule "SnapToTarget" :RotationRule "SnapToTarget" :ScaleRule "KeepWorld" :bWeldSimulatedBodies false)
  %(rest)s
  %(draw)s
  %(pedp)s
  (Transformation|SetActorRelativeLocation PedA %(gpedp)s false true)
  (Transformation|SetActorRelativeRotation PedA %(grest)s false true)
  (Transformation|SetActorScale3D PedA (Math|Vector|MakeVector 0.001 0.001 0.001))
  (Class|BPQuestCtrlSC|SetTrigger :self PedA :Amount 0.0)
  (CallFunction|PlaceLabels)
  (CallFunction|MantleSet)
  (Transformation|SetRelativeLocation %(frame)s (Math|Vector|MakeVector %(fx)s 0.0 %(fz)s) false true)
  (Transformation|SetRelativeScale3D %(frame)s (Math|Vector|MakeVector (/ %(fw)s 100.0) (/ %(fh)s 100.0) 1.0))
  %(fsize)s
  (Transformation|SetRelativeLocation %(logo)s (Math|Vector|MakeVector (- %(fx)s 0.5) (* -0.206 %(fw)s) (+ %(fz)s (* 0.376 %(fh)s))) false true)
  (Transformation|SetRelativeScale3D %(logo)s (Math|Vector|MakeVector (/ %(lw)s 100.0) (/ %(lw)s 400.0) 1.0))
  %(llt)s
  %(lout)s
  %(hrect)s
  %(hplace)s
  %(t0)s
  %(fk0)s
  %(d0)s
  %(o0)s
  %(c0)s
  %(p0)s
  %(cs0)s
  %(hv)s
  %(dp)s
  (for _i (range 6)
    %(on0)s
    %(lk0)s)
  %(run)s
  (Development|PrintString "TUTOR: marco, paleta y mando al frente" :bPrintToScreen false))
''' % dict(es=DS('ES', 'Spanish'), tb=DS('TB', 'TBA'), ped=DS('Ped', 'PedA'), sd=DS('Sd', '1.0'), camrot=CAMROT, cam=CAM, fon=D('FrameOn'),
           dist=D('Dist'), below=D('Below'), pc=DS('Pc', '(Math|Vector|MakeVector 0.0 (* -1.0 %s) %s)' % (D('PalY'), D('PalZ'))),
           palc=PALC, spal=DS('Pal', '_pal'), gpc=D('Pc'), ps=D('PalScale'), palrot=PALROT,
           cols='\n  '.join(VP('(Class|BPDrawPaletteSC|Get%s _pal)' % n, 'BaseColor',
                                '(Math|Conversions|ToVector(LinearColor) (Utilities|Array|Get(acopy) (Class|BPTBDirectorNC|GetSlotColorA TBA) %d))' % i)
                            for n, i in (('Color0', 0), ('Color1', 1), ('Color2', 2), ('Color3', 3), ('Swatch', 0))),
           rest=DS('RestRot', '(Math|Rotator|MakeRotator 0.0 0.0 180.0)'),
           draw=DS('DrawRot', '(Math|Rotator|MakeRotfromX (Math|Vector|MakeVector 0.75 -0.45 -0.45))'),
           pedp=DS('PedP', '(Math|Vector|MakeVector 0.0 %s %s)' % (D('PedY'), D('PedZ'))), gpedp=D('PedP'), grest=D('RestRot'),
           frame=D('Frame'), fx=D('FrameX'), fz=D('FrameZ'), fw=D('FrameW'), fh=D('FrameH'),
           fsize=VP(D('Frame'), 'Size', '(Math|Vector|MakeVector %s %s 6.0)' % (D('FrameW'), D('FrameH'))), ffade=SP(D('Frame'), 'Fade', '0.0'),
           logo=D('Logo'), lw=D('LogoW'), llt=SP(D('Logo'), 'LT', '20.0'), lout=SP(D('Logo'), 'Out', '0.0'), lrev=SP(D('Logo'), 'Reveal', '0.0'),
           hrect=RECT(D('Hdr'), 'hdr_en', 'hdr_es', 'Spanish'),
           hplace=PLACE(D('Hdr'), '(- %s 0.5)' % D('FrameX'), '(* 0.0876 %s)' % D('FrameW'), '(+ %s (* 0.364 %s))' % (D('FrameZ'), D('FrameH')),
                        D('HdrH'), ASP('hdr_en', 'hdr_es', 'Spanish'), 1),
           t0=DS('T', '0.0'), fk0=DS('FrameK', '0.0'), d0=DS('DemoT', '-1.0'), o0=DS('OutT', '-1.0'), c0=DS('CardsT', '-1.0'),
           p0=DS('PickT', '-1.0'), cs0=DS('CardsOn', 'false'), hv=DS('Hov', '-1'), dp=DS('DemoPrev', '-1.0'),
           on0=SETA('On', '_i', 'false'), lk0=SETA('LabK', '_i', '0.0'), run=DS('Run', 'true'))

# PlaceLabels: los puntos de toque de la demo (centro de las teclas) y las anclas de las etiquetas (en el espacio del actor): borde de
# cada manto (Color a la derecha, Brush arriba a la izquierda a 138 grados, Size abajo en el arco, Undo y Redo en el borde izquierdo de
# su tecla, Draw = el gatillo). La punta = ancla + LabB[k] (y, z). El texto sigue a la punta: a la izquierda alineado a la derecha y
# a la derecha alineado a la izquierda (como el PDF). La linea va de ancla a punta; un punto en cada extremo.
def _lab(k, ken, kes):
    a = G('Anch', str(k))
    b = '(+ %s (Math|Vector|MakeVector 0.0 (.y %s) (.z %s)))' % (a, G('LabB', str(k)), G('LabB', str(k)))
    al = '(select (< (.y %s) 0.0) -1.0 1.0)' % G('LabB', str(k))
    lab, ln, da, db = D('L%d' % k), D('K%d' % k), D('DA%d' % k), D('DB%d' % k)
    asp = ASP(ken, kes, D('ES'))
    return '''(bind _kb%(k)d %(b)s)
  (bind _kw%(k)d (* %(lh)s %(asp)s))
  (Transformation|SetRelativeLocation %(lab)s (Math|Vector|MakeVector (.x _kb%(k)d) (+ (.y _kb%(k)d) (* %(al)s (+ 1.0 (* 0.5 _kw%(k)d)))) (.z _kb%(k)d)) false true)
  (Transformation|SetRelativeScale3D %(lab)s (Math|Vector|MakeVector (/ _kw%(k)d 100.0) (/ %(lh)s 100.0) 1.0))
  %(rect)s
  (Transformation|SetRelativeLocation %(da)s %(a)s false true)
  (Transformation|SetRelativeScale3D %(da)s (Math|Vector|MakeVector (/ %(dd)s 100.0) (/ %(dd)s 100.0) 1.0))
  (Transformation|SetRelativeLocation %(db)s _kb%(k)d false true)
  (Transformation|SetRelativeScale3D %(db)s (Math|Vector|MakeVector (/ %(dd)s 100.0) (/ %(dd)s 100.0) 1.0))
  (bind _ky%(k)d (- (.y _kb%(k)d) (.y %(a)s)))
  (bind _kz%(k)d (- (.z _kb%(k)d) (.z %(a)s)))
  (bind _kl%(k)d (Math|Float|Max(Float) (Math|Float|Sqrt (+ (* _ky%(k)d _ky%(k)d) (* _kz%(k)d _kz%(k)d))) 0.3))
  (Transformation|SetRelativeLocationAndRotation %(ln)s (Math|Vector|MakeVector (+ (.x %(a)s) 0.05) (* 0.5 (+ (.y %(a)s) (.y _kb%(k)d))) (* 0.5 (+ (.z %(a)s) (.z _kb%(k)d)))) (Math|Rotator|CombineRotators %(rottxt)s (Math|Rotator|MakeRotator (* -1.0 (Math|Trig|Atan2(Degrees) _kz%(k)d _ky%(k)d)) 0.0 0.0)) false true)
  (Transformation|SetRelativeScale3D %(ln)s (Math|Vector|MakeVector (/ _kl%(k)d 100.0) (/ %(lw)s 100.0) 1.0))''' % dict(
        k=k, b=b, lh=D('LabH'), asp=asp, lab=lab, al=al, rect=RECT(lab, ken, kes, D('ES')), da=da, db=db, a=a, dd=D('DotD'), ln=ln,
        rottxt=ROTTXT, lw=D('LineW'))


CODES['PlaceLabels'] = '''(fn PlaceLabels ()
  (bind _xf (Transformation|GetActorTransform self))
  (bind _pal %(pal)s)
  (bind _s %(ps)s)
  (bind _pc %(pc)s)
  (bind _ax (- (.x _pc) 1.2))
  (bind (_c1 _e1 _r1) (Collision|GetComponentBounds (Class|BPDrawPaletteSC|GetColor1 _pal)))
  (bind (_c2 _e2 _r2) (Collision|GetComponentBounds (Class|BPDrawPaletteSC|GetColor2 _pal)))
  (bind (_b1 _f1 _q1) (Collision|GetComponentBounds (Class|BPDrawPaletteSC|GetBrush1 _pal)))
  (bind (_b2 _f2 _q2) (Collision|GetComponentBounds (Class|BPDrawPaletteSC|GetBrush0 _pal)))
  (bind (_un _ue _ur) (Collision|GetComponentBounds (Class|BPDrawPaletteSC|GetUndo _pal)))
  (bind (_re _rx _rr) (Collision|GetComponentBounds (Class|BPDrawPaletteSC|GetRedo _pal)))
  %(tc)s
  %(tb)s
  (bind _ul (Math|Transform|InverseTransformLocation _xf _un))
  (bind _rl (Math|Transform|InverseTransformLocation _xf _re))
  (bind _tl (Math|Transform|InverseTransformLocation _xf (Transformation|GetWorldLocation (Class|BPQuestCtrlSC|GetTrigger %(ped)s))))
  %(a0)s
  %(a1)s
  %(a2)s
  %(a3)s
  %(a4)s
  %(a5)s
  %(labs)s)
''' % dict(pal=D('Pal'), ps=D('PalScale'), pc=D('Pc'), ped=D('Ped'),
           tc=DS('TouchC', '(Math|Transform|InverseTransformLocation _xf (* (+ _c1 _c2) 0.5))'),
           tb=DS('TouchB', '(Math|Transform|InverseTransformLocation _xf (* (+ _b1 _b2) 0.5))'),
           a0=SETA('Anch', '0', '(Math|Vector|MakeVector _ax (+ (.y _pc) (* 17.3 _s)) (.z _pc))'),
           a1=SETA('Anch', '1', '(Math|Vector|MakeVector _ax (+ (.y _pc) (* -13.08 _s)) (+ (.z _pc) (* 11.78 _s)))'),
           a2=SETA('Anch', '2', '(Math|Vector|MakeVector _ax (.y _pc) (- (.z _pc) (* 21.7 _s)))'),
           a3=SETA('Anch', '3', '(Math|Vector|MakeVector _ax (- (.y _ul) (* 2.4 _s)) (.z _ul))'),
           a4=SETA('Anch', '4', '(Math|Vector|MakeVector _ax (- (.y _rl) (* 2.4 _s)) (.z _rl))'),
           a5=SETA('Anch', '5', '(Math|Vector|MakeVector _ax (.y _tl) (.z _tl))'),
           labs='\n  '.join(_lab(k, 'lab%d_en' % k, 'lab%d_es' % k) for k in range(6)))

# MantleSet: cuelga M0..M4 de la Base de la paleta (su espacio: cara +Z, +X = colores; medidas de la malla en cm, Base de radio 20):
# 0 colores (plato, de 4,6 a 16,9 cm, +-80 grados) · 1 pinceles (igual a 180) · 2 slider (detras del arco, 20,4-23,0) · 3 undo y
# 4 redo (detras de cada tecla lateral, 19-26,2, +-15). El angulo de slider, undo y redo sale de su caja real (atan2 en el espacio
# de la Base), por MSign (+1 / -1 si la UV del plano corre al reves).
def _man(k, z, ring, ang, parent='_base'):
    m = D('M%d' % k)
    return '''(Transformation|AttachComponentToComponent :self %(m)s :Parent %(parent)s :SocketName "None" :LocationRule "KeepRelative" :RotationRule "KeepRelative" :ScaleRule "KeepRelative" :bWeldSimulatedBodies false)
  (Transformation|SetRelativeLocationAndRotation %(m)s (Math|Vector|MakeVector 0.0 0.0 %(z)s) (Math|Rotator|MakeRotator 0.0 0.0 0.0) false true)
  (Transformation|SetRelativeScale3D %(m)s (Math|Vector|MakeVector 0.54 0.54 1.0))
  %(size)s
  %(ring)s
  %(ang)s
  %(fade)s''' % dict(m=m, z=z, parent=parent, size=SP(m, 'Size', '54.0'), ring=VP(m, 'Ring', VEC(*ring)), ang=VP(m, 'Ang', ang), fade=SP(m, 'Fade', '0.0'))


ANGOF = lambda c: '(Math|Vector|MakeVector (* %s (Math|Trig|Atan2(Degrees) (.y %s) (.x %s))) %%s 0.0)' % (D('MSign'), c, c)
CODES['MantleSet'] = '''(fn MantleSet ()
  (bind _pal %(pal)s)
  (bind _base (Class|BPDrawPaletteSC|GetBase _pal))
  (bind _bx (Transformation|GetWorldTransform _base))
  (bind (_so _se _sr) (Collision|GetComponentBounds (Class|BPDrawPaletteSC|GetSlider _pal)))
  (bind (_uo _ue _ur) (Collision|GetComponentBounds (Class|BPDrawPaletteSC|GetUndo _pal)))
  (bind (_ro _re _rr) (Collision|GetComponentBounds (Class|BPDrawPaletteSC|GetRedo _pal)))
  (bind _sl (Math|Transform|InverseTransformLocation _bx _so))
  (bind _ul (Math|Transform|InverseTransformLocation _bx _uo))
  (bind _rl (Math|Transform|InverseTransformLocation _bx _ro))
  %(m0)s
  %(m1)s
  %(m2)s
  %(m3)s
  %(m4)s)
''' % dict(pal=D('Pal'),
           m0=_man(0, '-0.30', ('4.6', '16.9', '1.2'), VEC('0.0', '80.0', '0.0')),
           m1=_man(1, '-0.30', ('4.6', '16.9', '1.2'), VEC('180.0', '80.0', '0.0')),
           m2=_man(2, '-1.95', ('20.4', '23.0', '0.9'), ANGOF('_sl') % '47.0'),
           m3=_man(3, '-2.6', ('19.6', '26.0', '0.9'), VEC('-165.7', '14.5', '0.0'), '(Class|BPDrawPaletteSC|GetUndo _pal)'),
           m4=_man(4, '-2.6', ('19.6', '26.0', '0.9'), VEC('-165.7', '14.5', '0.0'), '(Class|BPDrawPaletteSC|GetRedo _pal)'))

# FrameShow (Beltran 11-12 noche: "encaja el teclado dentro de un marco como el de las instrucciones, en el mismo lugar"): el actor
# va donde van las instrucciones y se ve el marco con el logo; el director pone el teclado delante. TutBegin no lo mueve si ya esta.
CODES['FrameShow'] = '''(fn FrameShow ()
  (bind _yaw (.yaw %(camrot)s))
  (bind _fwd (Math|Vector|MakeVector (Math|Trig|Cos(Degrees) _yaw) (Math|Trig|Sin(Degrees) _yaw) 0.0))
  (bind _pos (+ %(cam)s (+ (* _fwd %(dist)s) (Math|Vector|MakeVector 0.0 0.0 (* -1.0 %(below)s)))))
  (Transformation|SetActorLocationAndRotation self _pos (Math|Rotator|MakeRotfromX (- _pos %(cam)s)) false true)
  (Transformation|SetRelativeLocation %(frame)s (Math|Vector|MakeVector %(fx)s 0.0 %(fz)s) false true)
  (Transformation|SetRelativeScale3D %(frame)s (Math|Vector|MakeVector (/ %(fw)s 100.0) (/ %(fh)s 100.0) 1.0))
  %(fsize)s
  (Transformation|SetRelativeLocation %(logo)s (Math|Vector|MakeVector (- %(fx)s 0.5) 0.0 (+ %(fz)s (* 0.376 %(fh)s))) false true)
  (Transformation|SetRelativeScale3D %(logo)s (Math|Vector|MakeVector (/ %(lw)s 100.0) (/ %(lw)s 400.0) 1.0))
  %(llt)s
  %(lout)s
  %(fon)s
  %(ft0)s
  (Development|PrintString "TUTOR: marco del teclado" :bPrintToScreen false))
''' % dict(camrot=CAMROT, cam=CAM, dist=D('Dist'), below=D('Below'), frame=D('Frame'), fx=D('FrameX'), fz=D('FrameZ'), fw=D('FrameW'),
           fh=D('FrameH'), fsize=VP(D('Frame'), 'Size', '(Math|Vector|MakeVector %s %s 6.0)' % (D('FrameW'), D('FrameH'))), logo=D('Logo'),
           lw=D('LogoW'), llt=SP(D('Logo'), 'LT', '20.0'), lout=SP(D('Logo'), 'Out', '0.0'), fon=DS('FrameOn', 'true'), ft0=DS('FrameT', '0.0'))

CODES['TutShow'] = '''(fn TutShow (K)
  %s
  (Development|PrintString (Utilities|String|Append "TUTOR: etiqueta " (Utilities|String|ToString(Integer) K)) :bPrintToScreen false))
''' % SETA('On', 'K', 'true')

# TutDemo: los textos y los mantos se van (la demostracion se ve limpia) y arranca el reloj de DemoStep
CODES['TutDemo'] = '''(fn TutDemo ()
  %s
  %s
  (for _i (range 6)
    %s)
  (Development|PrintString "TUTOR: demostracion" :bPrintToScreen false))
''' % (DS('DemoT', D('T')), DS('DemoPrev', '-0.001'), SETA('On', '_i', 'false'))

# DemoStep: tau = T - DemoT. 0-1,2 va al color (punta 2 cm delante de la tecla) · 1,2 lo elige · 1,6-2,8 va al pincel · 2,8 lo elige ·
# 3,2-4 va al inicio del trazo · 4-6,8 dibuja un trazo grande en S (Bezier B0..B3, en cm del actor, dentro del marco: del mando hacia
# abajo a la izquierda, como el PDF) con el gatillo apretado · 6,8-7,8 vuelve a su lugar. El mando esta a PedScale: la punta del
# pincel (5 · 2,4 cm en la malla) se escala igual.
CODES['DemoStep'] = '''(fn DemoStep ()
  (bind _t (- %(gt)s %(dt)s))
  (bind _p %(dp)s)
  (bind _k %(pks)s)
  (bind _rm (Math|Rotator|MakeRotfromXZ (Math|Vector|MakeVector 1.0 0.0 0.0) (Math|Vector|MakeVector 0.0 0.6 0.8)))
  (bind _qi (Math|Transform|InverseTransformRotation (Math|Transform|MakeTransform :Rotation _rm) (Math|Rotator|MakeRotator 0.0 0.0 0.0)))
  (bind _dd (Math|Vector|MakeVector 0.35 -0.85 -0.25))
  (bind _rd (Math|Rotator|CombineRotators _qi (Math|Rotator|MakeRotfromXZ _dd (Math|Vector|MakeVector 0.0 0.0 1.0))))
  (bind _tip0 (+ %(pedp)s (+ (* (Math|Vector|GetForwardVector %(rest)s) (* 5.0 _k)) (* (Math|Vector|GetRightVector %(rest)s) (* 2.4 _k)))))
  (bind _tc (+ %(tch)s (Math|Vector|MakeVector -2.0 0.0 0.0)))
  (bind _tb (+ %(tbr)s (Math|Vector|MakeVector -2.0 0.0 0.0)))
  (bind _q0 (Math|Vector|MakeVector -4.0 44.0 12.0))
  (bind _q1 (Math|Vector|MakeVector -4.0 24.0 17.0))
  (bind _q2 (Math|Vector|MakeVector -4.0 32.0 -15.0))
  (bind _q3 (Math|Vector|MakeVector -4.0 16.0 -20.0))
  (bind _u %(u)s)
  (bind _v (- 1.0 _u))
  (bind _pp (+ (+ (* _q0 (* _v (* _v _v))) (* _q1 (* 3.0 (* _v (* _v _u))))) (+ (* _q2 (* 3.0 (* _v (* _u _u)))) (* _q3 (* _u (* _u _u))))))
  (bind _tip (select (< _t 1.6) %(l1)s (select (< _t 3.2) %(l2)s (select (< _t 4.0) %(l3)s (select (< _t 6.8) _pp %(l5)s)))))
  (bind _ka (select (< _t 6.8) %(ea)s (- 1.0 %(k5)s)))
  (bind _rot (Math|Rotator|Lerp(Rotator) %(rest)s _rd _ka true))
  (Transformation|SetActorRelativeLocation %(ped)s (- _tip (+ (* (Math|Vector|GetForwardVector _rot) (* 5.0 _k)) (* (Math|Vector|GetRightVector _rot) (* 2.4 _k)))) false true)
  (Transformation|SetActorRelativeRotation %(ped)s _rot false true)
  (Class|BPQuestCtrlSC|SetTrigger :self %(ped)s :Amount (select (and (>= _t 4.0) (< _t 6.8)) 1.0 0.0))
  (bind _w (Math|Transform|TransformLocation (Transformation|GetActorTransform self) _tip))
  (bind _fw (Math|Transform|TransformDirection (Transformation|GetActorTransform self) (Math|Vector|Normalize _dd)))
  (bind _up (Math|Transform|TransformDirection (Transformation|GetActorTransform self) (Math|Vector|MakeVector 0.0 0.0 1.0)))
  (if (and (< _p 1.2) (>= _t 1.2))
    (Class|BPDrawPaletteSC|SetSelectedColor :self %(pal)s :SelectedColor 2)
    (Class|BPDrawPaletteSC|ApplyState %(pal)s)
    %(cols2)s)
  (if (and (< _p 2.8) (>= _t 2.8))
    (Class|BPDrawPaletteSC|SetSelectedBrush :self %(pal)s :SelectedBrush 1)
    (Class|BPDrawPaletteSC|ApplyState %(pal)s)
    %(cols2)s)
  (if (and (< _p 4.0) (>= _t 4.0))
    (bind _st (Game|SpawnActorfromClass "%(strokec)s" (Math|Transform|MakeTransform) "AlwaysSpawn"))
    %(sst)s
    (Class|BPTBStroke|SetPreset :self _st :Preset 0)
    (Class|BPTBStroke|SetSize01 :self _st :Size01 0.8)
    (Class|BPTBStroke|SetSizeLo :self _st :SizeLo 1.0)
    (Class|BPTBStroke|SetSizeHi :self _st :SizeHi 3.0)
    (Class|BPTBStroke|SetBaseColor :self _st :BaseColor %(ca)s)
    (Class|BPTBStroke|SetLook _st true %(ca)s %(cb)s)
    (Class|BPTBStroke|StartStroke _st _w _fw _up 0.8))
  (if (and (> _p 4.0) (< _t 6.8))
    (Class|BPTBStroke|UpdatePosition %(st)s _w _fw _up 0.8))
  (if (and (< _p 6.8) (>= _t 6.8))
    (Class|BPTBStroke|EndStroke %(st)s))
  %(dps)s
  (if (>= _t 7.8)
    %(dend)s))
''' % dict(gt=D('T'), dt=D('DemoT'), dp=D('DemoPrev'), pks=D('PedScale'), pedp=D('PedP'), rest=D('RestRot'),
           tch=D('TouchC'), tbr=D('TouchB'), u=CL('(/ (- _t 4.0) 2.8)'),
           l1=LERPV('_tip0', '_tc', EASE(CL('(/ _t 1.2)'))), l2=LERPV('_tc', '_tb', EASE(CL('(/ (- _t 1.6) 1.2)'))),
           l3=LERPV('_tb', '_q0', EASE(CL('(/ (- _t 3.2) 0.8)'))), l5=LERPV('_q3', '_tip0', EASE(CL('(/ (- _t 6.8) 1.0)'))),
           k5=EASE(CL('(/ (- _t 6.8) 1.0)')), ea=EASE(CL('(/ _t 1.0)')), ped=D('Ped'), pal=D('Pal'), strokec=STROKEC,
           cols2='\n    '.join(VP('(Class|BPDrawPaletteSC|Get%s %s)' % (n, D('Pal')), 'BaseColor',
                                   '(Math|Conversions|ToVector(LinearColor) (Utilities|Array|Get(acopy) (Class|BPTBDirectorNC|GetSlotColorA %s) %d))' % (D('TB'), i))
                                for n, i in (('Color0', 0), ('Color1', 1), ('Color2', 2), ('Color3', 3), ('Swatch', 2))),
           sst=DS('Stroke', '_st'), st=D('Stroke'),
           ca='(Utilities|Array|Get(acopy) (Class|BPTBDirectorNC|GetSlotColorA %s) 2)' % D('TB'),
           cb='(Utilities|Array|Get(acopy) (Class|BPTBDirectorNC|GetSlotColorB %s) 2)' % D('TB'),
           dps=DS('DemoPrev', '_t'), dend=DS('DemoT', '-1.0'))

# LabTick: cada etiqueta k (texto, linea, dos puntos y su manto) entra y sale con LabK[k]
CODES['LabTick'] = '''(fn LabTick (Dt)
  (for _k (range 6)
    %(lk)s
    (bind _f %(glk)s)
    (bind _v (> _f 0.01))
    %(f1)s
    %(f2)s
    %(f3)s
    %(f4)s
    %(v1)s
    %(v2)s
    %(v3)s
    %(v4)s
    (if (< _k 5)
      %(f5)s
      %(v5)s)))
''' % dict(lk=SETA('LabK', '_k', '(Math|Interpolation|FInterpTo %s (select %s 1.0 0.0) Dt 6.0)' % (G('LabK', '_k'), G('On', '_k'))),
           glk=G('LabK', '_k'),
           f1=SP(G('Labs', '_k'), 'Fade', '_f'), f2=SP(G('Lines', '_k'), 'Fade', '_f'), f3=SP(G('DotsA', '_k'), 'Fade', '_f'),
           f4=SP(G('DotsB', '_k'), 'Fade', '_f'), f5=SP(G('Mants', '_k'), 'Fade', '(* _f 0.6)'),
           v1=VIS(G('Labs', '_k'), '_v'), v2=VIS(G('Lines', '_k'), '_v'), v3=VIS(G('DotsA', '_k'), '_v'), v4=VIS(G('DotsB', '_k'), '_v'),
           v5=VIS(G('Mants', '_k'), '_v'))

# TutCards: se van paleta, mando y trazo (OutStep, 0,4 s) y a los 0,45 s entran las cartas (CardsSpawn desde TutTick)
CODES['TutCards'] = '''(fn TutCards ()
  %s
  %s
  %s
  (for _i (range 6)
    %s)
  (Development|PrintString "TUTOR: se van la paleta y el mando; cartas de la mano" :bPrintToScreen false))
''' % (DS('OutT', D('T')), DS('CardsT', '(+ %s 0.45)' % D('T')), DS('Hov', '-1'), SETA('On', '_i', 'false'))

# TutOut: se conserva por compatibilidad (el director viejo la llamaba): ahora = TutCards
CODES['TutOut'] = '''(fn TutOut ()
  (CallFunction|TutCards))
'''

CODES['OutStep'] = '''(fn OutStep ()
  (bind _e %(e)s)
  (bind _s (Math|Float|Max(Float) (- 1.0 _e) 0.001))
  (Transformation|SetActorRelativeScale3D %(pal)s (Math|Vector|MakeVector (* %(ps)s _s) (* %(ps)s _s) (* %(ps)s _s)))
  (Transformation|SetActorScale3D %(ped)s (Math|Vector|MakeVector (* %(pks)s _s) (* %(pks)s _s) (* %(pks)s _s)))
  (CallFunction|StrokeOut :R _s)
  (if (>= _e 1.0)
    (Rendering|SetActorHiddenInGame %(pal)s true)
    (Rendering|SetActorHiddenInGame %(ped)s true)
    %(o0)s))
''' % dict(e=EASE(CL('(/ (- %s %s) 0.4)' % (D('T'), D('OutT')))), pal=D('Pal'), ps=D('PalScale'), ped=D('Ped'), pks=D('PedScale'),
           o0=DS('OutT', '-1.0'))

CODES['StrokeOut'] = '''(fn StrokeOut (R)
  (Utilities|IsValid %(st)s
    (:"Is Valid"
      (Class|BPTBStroke|SetTaper :self %(st)s :T 6.0)
      (Class|BPTBStroke|SetReveal :self %(st)s :R R))))
''' % dict(st=D('Stroke'))


# CardsSpawn: las dos cartas en el marco (izquierda = zurda: mando a la izquierda y paleta espejada; derecha = diestra), el titulo
# "Select your dominant hand" y los rotulos; CardHit (invisible, con colision) las cubre para el laser.
def _mini(side):
    left = side == 'L'
    y0 = '(* %s %s)' % ('-1.0' if left else '1.0', D('CardY'))
    py = '(+ %s %s)' % (y0, '7.0' if left else '-7.0')
    cy = '(+ %s %s)' % (y0, '-15.5' if left else '15.5')
    sy = '(* %s %s)' % ('-1.0' if left else '1.0', D('MiniPal'))
    # zurda: espejo izquierda-derecha SIN escala X negativa (con X negativa las teclas laterales de la paleta salian gigantes):
    # giro de 180 grados en su plano + Y negativa = solo X espejada
    prot = PALROT_L if left else PALROT
    pal, ctl = 'PalL' if left else 'PalR', 'CtlL' if left else 'CtlR'
    return '''(bind _p%(s)s (Game|SpawnActorfromClass "%(palc)s" (Math|Transform|MakeTransform :Location (Transformation|GetActorLocation self)) "AlwaysSpawn"))
  %(spal)s
  (Collision|SetActorEnableCollision _p%(s)s false)
  (Class|BPDrawPaletteSC|SetAppearDelay :self _p%(s)s :AppearDelay 0.0)
  (Transformation|AttachActorToActor :self _p%(s)s :ParentActor self :LocationRule "SnapToTarget" :RotationRule "SnapToTarget" :ScaleRule "KeepWorld" :bWeldSimulatedBodies false)
  (Transformation|SetActorRelativeLocation _p%(s)s (Math|Vector|MakeVector 0.0 %(py)s %(pz)s) false true)
  (Transformation|SetActorRelativeRotation _p%(s)s %(prot)s false true)
  (Transformation|SetActorRelativeScale3D _p%(s)s (Math|Vector|MakeVector %(mp)s %(sy)s %(mp)s))
  (Class|BPDrawPaletteSC|SetKeyColors :self _p%(s)s :KeyColors (Class|BPTBDirectorNC|GetSlotColorA %(tb)s))
  (Class|BPDrawPaletteSC|ApplyState _p%(s)s)
  %(cols)s
  (bind _c%(s)s (Game|SpawnActorfromClass "%(qcc)s" (Math|Transform|MakeTransform :Location (Transformation|GetActorLocation self)) "AlwaysSpawn"))
  %(sctl)s
  (Collision|SetActorEnableCollision _c%(s)s false)
  (Class|BPQuestCtrlSC|SetLeft :self _c%(s)s :bLeft %(left)s)
  (Class|BPQuestCtrlSC|ApplyHand _c%(s)s)
  (Class|BPQuestCtrlSC|SetTrigger :self _c%(s)s :Amount 0.0)
  (Class|BPQuestCtrlSC|ApplyTrigger _c%(s)s)
  (Transformation|AttachActorToActor :self _c%(s)s :ParentActor self :LocationRule "SnapToTarget" :RotationRule "SnapToTarget" :ScaleRule "KeepWorld" :bWeldSimulatedBodies false)
  (Transformation|SetActorRelativeLocation _c%(s)s (Math|Vector|MakeVector 0.0 %(cy)s (+ %(pz)s 5.0)) false true)
  (Transformation|SetActorRelativeRotation _c%(s)s %(crot)s false true)
  (Transformation|SetActorScale3D _c%(s)s (Math|Vector|MakeVector %(mc)s %(mc)s %(mc)s))''' % dict(
        s=side, palc=PALC, spal=DS(pal, '_p' + side), py=py, pz=D('PalZ'), prot=prot, sy=sy, mp=D('MiniPal'), tb=D('TB'),
        cols='\n  '.join(VP('(Class|BPDrawPaletteSC|Get%s _p%s)' % (n, side), 'BaseColor',
                              '(Math|Conversions|ToVector(LinearColor) (Utilities|Array|Get(acopy) (Class|BPTBDirectorNC|GetSlotColorA %s) %d))' % (D('TB'), i))
                           for n, i in (('Color0', 0), ('Color1', 1), ('Color2', 2), ('Color3', 3), ('Swatch', 0))),
        qcc=QCC, sctl=DS(ctl, '_c' + side), left='true' if left else 'false', cy=cy,
        # el mando zurdo (mallas L de BP_QuestCtrl_SC) ya viene espejado en su eje X: sin el giro de 180 queda como espejo del derecho
        # + un giro en el plano de la carta (alrededor de X del actor) para dejarlos parados, mango abajo, como el PDF (izq/der espejados)
        crot=('(Math|Rotator|CombineRotators (Math|Rotator|MakeRotator 0.0 0.0 0.0) (Math|Rotator|MakeRotator %s 0.0 0.0))' % F(-1.0 * 20.0)) if left
             else ('(Math|Rotator|CombineRotators %s (Math|Rotator|MakeRotator %s 0.0 0.0))' % (D('RestRot'), F(20.0))), mc=D('MiniCtl'))


def _card(c, sign):
    return '''(Transformation|SetRelativeLocation %(c)s (Math|Vector|MakeVector (- %(fx)s 0.6) (* %(sg)s %(cy)s) %(pz)s) false true)
  (Transformation|SetRelativeScale3D %(c)s (Math|Vector|MakeVector (/ %(cw)s 100.0) (/ %(ch)s 100.0) 1.0))
  %(size)s
  %(rim)s
  %(fill)s
  %(fade)s''' % dict(c=c, fx=D('FrameX'), sg=sign, cy=D('CardY'), pz=D('PalZ'), cw=D('CardW'), ch=D('CardH'),
                     size=VP(c, 'Size', '(Math|Vector|MakeVector %s %s 3.5)' % (D('CardW'), D('CardH'))),
                     rim=VP(c, 'Rim', VEC('0.25', '0.2', '0.55')), fill=VP(c, 'Fill', VEC('0.86', '0.89', '0.88')), fade=SP(c, 'Fade', '0.0'))


CODES['CardsSpawn'] = '''(fn CardsSpawn ()
  %(on)s
  %(ml)s
  %(mr)s
  %(cl)s
  %(cr)s
  (Transformation|SetRelativeLocation %(hit)s (Math|Vector|MakeVector (- %(fx)s 0.8) 0.0 %(pz)s) false true)
  (Transformation|SetRelativeScale3D %(hit)s (Math|Vector|MakeVector (/ (+ %(cw)s (* 2.0 %(cy)s)) 100.0) (/ %(ch)s 100.0) 1.0))
  (Collision|SetCollisionObjectType %(hit)s "ECC_Destructible")
  (Collision|SetCollisionEnabled %(hit)s "QueryOnly")
  %(srect)s
  %(splace)s
  %(lrect)s
  %(lplace)s
  %(rrect)s
  %(rplace)s
  (CallFunction|PalSndAll :Mute true)
  (Development|PrintString "TUTOR: cartas" :bPrintToScreen false))
''' % dict(on=DS('CardsOn', 'true') + NL2 + DS('PrevHov', '-1'), ml=_mini('L'), mr=_mini('R'), cl=_card(D('CardL'), '-1.0'), cr=_card(D('CardR'), '1.0'),
           hit=D('CardHit'), fx=D('FrameX'), pz=D('PalZ'), cw=D('CardW'), cy=D('CardY'), ch=D('CardH'),
           srect=RECT(D('Sel'), 'sel_en', 'sel_es', D('ES')),
           splace=PLACE(D('Sel'), '(- %s 0.6)' % D('FrameX'), '0.0', '(+ %s (* 0.216 %s))' % (D('FrameZ'), D('FrameH')), D('LabH'),
                        ASP('sel_en', 'sel_es', D('ES')), 0),
           lrect=RECT(D('CapL'), 'cl_en', 'cl_es', D('ES')),
           lplace=PLACE(D('CapL'), '(- %s 0.6)' % D('FrameX'), '(* -1.0 %s)' % D('CardY'), '(- %s (* 0.272 %s))' % (D('FrameZ'), D('FrameH')),
                        D('LabH'), ASP('cl_en', 'cl_es', D('ES')), 0),
           rrect=RECT(D('CapR'), 'cr_en', 'cr_es', D('ES')),
           rplace=PLACE(D('CapR'), '(- %s 0.6)' % D('FrameX'), D('CardY'), '(- %s (* 0.272 %s))' % (D('FrameZ'), D('FrameH')),
                        D('LabH'), ASP('cr_en', 'cr_es', D('ES')), 0))

# CardHov: la carta que apunta el laser del rig R -> HitK (-1 ninguna, 0 izquierda = zurda, 1 derecha = diestra)
CODES['CardHov'] = '''(fn CardHov (R)
  %(h0)s
  (if (and %(on)s (== (Class|BPSeqRigSC|GetBeamHitActor R) self))
    (bind _l (Math|Transform|InverseTransformLocation (Transformation|GetActorTransform self) (Class|BPSeqRigSC|GetBeamHitLoc R)))
    (if (<= (Math|Float|Absolute(Float) (- (.z _l) %(pz)s)) (* 0.5 %(ch)s))
      (if (<= (Math|Float|Absolute(Float) (+ (.y _l) %(cy)s)) (* 0.5 %(cw)s))
        %(h1)s)
      (if (<= (Math|Float|Absolute(Float) (- (.y _l) %(cy)s)) (* 0.5 %(cw)s))
        %(h2)s))))
''' % dict(h0=DS('HitK', '-1'), on=D('CardsOn'), pz=D('PalZ'), ch=D('CardH'), cy=D('CardY'), cw=D('CardW'), h1=DS('HitK', '0'), h2=DS('HitK', '1'))

CODES['TutPick'] = '''(fn TutPick (Right)
  %s
  %s
  (Collision|SetCollisionEnabled %s "NoCollision")
  (Development|PrintString (Utilities|String|Append "TUTOR: carta elegida " (select Right "derecha" "izquierda")) :bPrintToScreen false))
''' % (DS('PickT', D('T')), DS('PickR', 'Right'), D('CardHit'))

CODES['Kill'] = '''(fn Kill (A)
  (Utilities|IsValid A
    (:"Is Valid"
      (Actor|DestroyActor A))))
'''

CODES['TutHide'] = '''(fn TutHide ()
  %(r0)s
  %(d0)s
  %(o0)s
  %(c0)s
  %(p0)s
  %(cs0)s
  %(mants)s
  (for _c (Actor|GetComponentsByClass self "/Script/Engine.StaticMeshComponent")
    (if (and (!= _c %(h0c)s) (and (!= _c %(h1c)s) (!= _c %(wc)s)))
      (Rendering|SetVisibility _c false false)))
  (Collision|SetCollisionEnabled %(hit)s "NoCollision")
  (CallFunction|Kill :A %(pal)s)
  (CallFunction|Kill :A %(pall)s)
  (CallFunction|Kill :A %(palr)s)
  (CallFunction|Kill :A %(ctll)s)
  (CallFunction|Kill :A %(ctlr)s)
  (CallFunction|Kill :A %(st)s)
  (Utilities|IsValid %(ped)s
    (:"Is Valid"
      (Class|BPQuestCtrlSC|SetTrigger :self %(ped)s :Amount 0.0)
      (Transformation|DetachFromActor %(ped)s "KeepWorld" "KeepWorld" "KeepWorld")
      (Transformation|SetActorScale3D %(ped)s (Math|Vector|MakeVector 1.0 1.0 1.0))
      (Rendering|SetActorHiddenInGame %(ped)s true)
      (Development|PrintString "TUTOR: fin" :bPrintToScreen false))))
''' % dict(r0=DS('Run', 'false') + NL2 + DS('FrameOn', 'false'), d0=DS('DemoT', '-1.0'), o0=DS('OutT', '-1.0'), c0=DS('CardsT', '-1.0'), p0=DS('PickT', '-1.0'),
           cs0=DS('CardsOn', 'false'), h0c=D('H0'), h1c=D('H1'), wc=D('Warn'), hit=D('CardHit'),
           mants='\n  '.join('(Transformation|AttachComponentToComponent :self %s :Parent %s :SocketName "None" :LocationRule "KeepRelative" :RotationRule "KeepRelative" :ScaleRule "KeepRelative" :bWeldSimulatedBodies false)' % (D('M%d' % k), D('Frame')) for k in range(5)),
           pal=D('Pal'), pall=D('PalL'), palr=D('PalR'), ctll=D('CtlL'), ctlr=D('CtlR'), st=D('Stroke'), ped=D('Ped'))

# HintShow: el texto de ayuda, de cara a la persona en Pos. Mode 1 = idioma (dos lineas: ingles arriba, espanol abajo);
# Mode 2 = nombre (una linea, en el idioma elegido).
CODES['HintShow'] = '''(fn HintShow (Mode Spanish Pos)
  (if (== Mode 1)
    (Transformation|SetActorLocationAndRotation self Pos (Math|Rotator|MakeRotfromX (- Pos %(cam)s)) false true))
  %(hm)s
  %(r0)s
  (bind _a0 (select (== Mode 1) %(alen)s (select Spanish %(ahes)s %(ahen)s)))
  (Transformation|SetRelativeLocation %(h0)s (select (== Mode 1) (Math|Vector|MakeVector 0.0 0.0 0.0) (Math|Vector|MakeVector (- %(fx)s 1.0) 0.0 (+ %(fz)s (+ (* -0.5 %(fh)s) 5.5)))) false true)
  (Transformation|SetRelativeScale3D %(h0)s (Math|Vector|MakeVector (/ (* %(hh)s _a0) 100.0) (/ %(hh)s 100.0) 1.0))
  %(r1)s
  (Transformation|SetRelativeLocation %(h1)s (Math|Vector|MakeVector 0.0 0.0 (* -1.05 %(hh)s)) false true)
  (Transformation|SetRelativeScale3D %(h1)s (Math|Vector|MakeVector (/ (* %(hh)s %(ales)s) 100.0) (/ %(hh)s 100.0) 1.0))
  %(on)s)
''' % dict(cam=CAM, hm=DS('HintM', 'Mode'), h0=D('H0'), h1=D('H1'), hh=D('HintH'), fx=D('FrameX'), fz=D('FrameZ'), fh=D('FrameH'),
           r0='%s\n  %s' % (VP(D('H0'), 'Rect', '(select (== Mode 1) %s (select Spanish %s %s))' % (RV('hlang_en'), RV('hname_es'), RV('hname_en'))),
                            SP(D('H0'), 'VS', F(TX['hname_en'][3]))),
           alen=F(TX['hlang_en'][4]), ahes=F(TX['hname_es'][4]), ahen=F(TX['hname_en'][4]), ales=F(TX['hlang_es'][4]),
           r1=RECT(D('H1'), 'hlang_es'), on=DS('HintOn', 'true'))

CODES['HintOff'] = '''(fn HintOff ()
  %s)
''' % DS('HintOn', 'false')

# WarnSet: el aviso de borde. La primera vez se cuelga de la camara del pawn (queda pegado a la vista, WarnD cm al frente y un poco
# abajo); al encenderse toma el texto del idioma. TutTick lo hace aparecer y desaparecer suave.
CODES['WarnSet'] = '''(fn WarnSet (On)
  (if (and On (not %(wa)s))
    (bind _cam (Utilities|Casting|CastToSceneComponent (Actor|GetComponentbyClass (Game|GetPlayerPawn 0) "/Script/Engine.CameraComponent")))
    (Transformation|AttachComponentToComponent :self %(w)s :Parent _cam :SocketName "None" :LocationRule "KeepRelative" :RotationRule "KeepRelative" :ScaleRule "KeepRelative" :bWeldSimulatedBodies false)
    (Transformation|SetRelativeLocationAndRotation %(w)s (Math|Vector|MakeVector %(wd)s 0.0 -4.0) %(rottxt)s false true)
    %(wa1)s)
  (if (and On (not %(won)s))
    %(rect)s
    (Transformation|SetRelativeScale3D %(w)s (Math|Vector|MakeVector (/ (* %(wh)s %(asp)s) 100.0) (/ %(wh)s 100.0) 1.0))
    %(col)s)
  %(set)s)
''' % dict(wa=D('WarnAtt'), w=D('Warn'), wd=D('WarnD'), rottxt=ROTTXT, wa1=DS('WarnAtt', 'true'), won=D('WarnOn'),
           rect=RECT(D('Warn'), 'warn_en', 'warn_es', D('ES')).replace('\n  ', '\n    '), wh=D('WarnH'), asp=ASP('warn_en', 'warn_es', D('ES')),
           col=VP(D('Warn'), 'Color', VEC('1.0', '0.92', '0.8')), set=DS('WarnOn', 'On'))

# TutTick: pistas y aviso (siempre); el resto con Run: marco + logo + titulo + mando entran juntos en 0,5 s y salen al elegir carta.
CODES['TutTick'] = '''(fn TutTick (Dt)
  %(hk)s
  %(hf0)s
  %(hf1)s
  %(hv0)s
  %(hv1)s
  %(wk)s
  %(wf)s
  %(wv)s
  (if %(fo)s
    %(ftp)s)
  (bind _fo (select %(fo)s %(efo)s 0.0))
  (if (and %(fo)s (not %(run)s))
    %(fks)s
    %(fff)s
    %(ffl)s
    %(ffv)s
    %(ffw)s)
  (if (and (not %(fo)s) (not %(run)s))
    %(fkd)s
    %(gff)s
    %(gfl)s
    %(gfv)s
    %(gfw)s)
  (if %(run)s
    %(tp)s
    (bind _in %(ein)s)
    (bind _pk (select (>= %(pt)s 0.0) %(epk)s 0.0))
    %(fk)s
    (bind _fk %(gfk)s)
    (bind _fv (> _fk 0.01))
    (bind _hk (* _in (- 1.0 _pk)))
    %(ff)s
    %(lr)s
    %(hf)s
    %(fv)s
    %(lv)s
    %(hdv)s
    (if (< %(ct)s 0.0)
      (Transformation|SetActorScale3D %(ped)s (Math|Vector|MakeVector (* %(pks)s (Math|Float|Max(Float) _in 0.001)) (* %(pks)s (Math|Float|Max(Float) _in 0.001)) (* %(pks)s (Math|Float|Max(Float) _in 0.001)))))
    (CallFunction|LabTick :Dt Dt)
    (if (and %(on5)s (< %(dt)s 0.0))
      (Class|BPQuestCtrlSC|SetTrigger :self %(ped)s :Amount (+ 0.5 (* 0.5 (Math|Trig|Sin(Radians) (* %(gt)s 5.0))))))
    (if (>= %(dt)s 0.0)
      (CallFunction|DemoStep))
    (if (>= %(ot)s 0.0)
      (CallFunction|OutStep))
    (if (and (>= %(ct)s 0.0) (and (>= %(gt)s %(ct)s) (not %(con)s)))
      (CallFunction|CardsSpawn))
    (if %(con)s
      (bind _ck (* %(eck)s (- 1.0 _pk)))
      (bind _cv (> _ck 0.01))
      (bind _hl (select (>= %(pt)s 0.0) (not %(pr)s) (== %(hov)s 0)))
      (bind _hr (select (>= %(pt)s 0.0) %(pr)s (== %(hov)s 1)))
      %(cf)s
      %(cvis)s
      %(chl)s
      %(chr)s
      (if (and (< %(pt)s 0.0) (!= %(hov)s %(phv)s))
        (if (>= %(phv)s 0)
          (Audio|PlaySound2D %(cos)s))
        (if (>= %(hov)s 0)
          (Audio|PlaySound2D %(chs)s))
        %(sphv)s)
      (bind _ms (Math|Float|Max(Float) (- 1.0 _pk) 0.001))
      (Transformation|SetActorRelativeScale3D %(pall)s (Math|Vector|MakeVector (* %(mp)s _ms) (* -1.0 (* %(mp)s _ms)) (* %(mp)s _ms)))
      (Transformation|SetActorRelativeScale3D %(palr)s (Math|Vector|MakeVector (* %(mp)s _ms) (* %(mp)s _ms) (* %(mp)s _ms)))
      (Transformation|SetActorScale3D %(ctll)s (Math|Vector|MakeVector (* %(mc)s _ms) (* %(mc)s _ms) (* %(mc)s _ms)))
      (Transformation|SetActorScale3D %(ctlr)s (Math|Vector|MakeVector (* %(mc)s _ms) (* %(mc)s _ms) (* %(mc)s _ms))))
    (if (and (>= %(pt)s 0.0) (>= (- %(gt)s %(pt)s) 0.5))
      (CallFunction|TutHide))))
''' % dict(hk=DS('HintK', '(Math|Interpolation|FInterpTo %s (select %s 1.0 0.0) Dt 7.0)' % (D('HintK'), D('HintOn'))),
           hf0=SP(D('H0'), 'Fade', D('HintK')), hf1=SP(D('H1'), 'Fade', D('HintK')),
           hv0=VIS(D('H0'), '(> %s 0.01)' % D('HintK')), hv1=VIS(D('H1'), '(and (> %s 0.01) (== %s 1))' % (D('HintK'), D('HintM'))),
           wk=DS('WarnK', '(Math|Interpolation|FInterpTo %s (select %s 1.0 0.0) Dt 8.0)' % (D('WarnK'), D('WarnOn'))),
           wf=SP(D('Warn'), 'Fade', D('WarnK')), wv=VIS(D('Warn'), '(> %s 0.01)' % D('WarnK')),
           run=D('Run'), tp=DS('T', '(+ %s Dt)' % D('T')), ein=EASE(CL('(/ %s 0.5)' % D('T'))), pt=D('PickT'),
           epk=EASE(CL('(/ (- %s %s) 0.45)' % (D('T'), D('PickT')))), fk=DS('FrameK', '(* (Math|Float|Max(Float) _in _fo) (- 1.0 _pk))'), gfk=D('FrameK'),
           ff=SP(D('Frame'), 'Fade', '_fk'), lr=SP(D('Logo'), 'Reveal', '_fk'), hf=SP(D('Hdr'), 'Fade', '_hk'),
           fv=VIS(D('Frame'), '_fv'), lv=VIS(D('Logo'), '_fv'), hdv=VIS(D('Hdr'), '(> _hk 0.01)'), fo=D('FrameOn'), fks=DS('FrameK', '_fo'), fkd=DS('FrameK', '(Math|Interpolation|FInterpTo %s 0.0 Dt 8.0)' % D('FrameK')), gff=SP(D('Frame'), 'Fade', D('FrameK')), gfl=SP(D('Logo'), 'Reveal', D('FrameK')), gfv=VIS(D('Frame'), '(> %s 0.01)' % D('FrameK')), gfw=VIS(D('Logo'), '(> %s 0.01)' % D('FrameK')), ftp=DS('FrameT', '(+ %s Dt)' % D('FrameT')), efo=EASE(CL('(/ %s 0.5)' % D('FrameT'))), fff=SP(D('Frame'), 'Fade', '_fo'), ffl=SP(D('Logo'), 'Reveal', '_fo'), ffv=VIS(D('Frame'), '(> _fo 0.01)'), ffw=VIS(D('Logo'), '(> _fo 0.01)'),
           ct=D('CardsT'), ped=D('Ped'), pks=D('PedScale'), on5=G('On', '5'), dt=D('DemoT'), gt=D('T'), ot=D('OutT'), con=D('CardsOn'),
           eck=EASE(CL('(/ (- %s %s) 0.5)' % (D('T'), D('CardsT')))), pr=D('PickR'), hov=D('Hov'), phv=D('PrevHov'), cos=D('CardOutSound'), chs=D('CardHovSound'), sphv=DS('PrevHov', D('Hov')),
           cf='\n      '.join(SP(D(n), 'Fade', '_ck') for n in ('CardL', 'CardR', 'Sel', 'CapL', 'CapR')),
           cvis='\n      '.join(VIS(D(n), '_cv') for n in ('CardL', 'CardR', 'Sel', 'CapL', 'CapR')),
           chl=SP(D('CardL'), 'Hover', '(select _hl 1.0 0.0)'), chr=SP(D('CardR'), 'Hover', '(select _hr 1.0 0.0)'),
           pall=D('PalL'), palr=D('PalR'), ctll=D('CtlL'), ctlr=D('CtlR'), mp=D('MiniPal'), mc=D('MiniCtl'))

# PalSndAll(Mute): sonido de la aparicion de TODAS las paletas vivas (Beltran 11-13): entrar = PalInSound (PaletteIn); irse = nada;
# Mute = sin sonido al entrar (las dos chicas de las cartas). Se escribe en la paleta (la copia a su BPC_AppearLuz_SC al crearlo) y,
# si el componente ya existe, tambien en el.
CODES['PalSndAll'] = '''(fn PalSndAll (Mute)
  (for _p (Actor|GetAllActorsOfClass "%(palc)s")
    (Class|BPDrawPaletteSC|SetVanishSound :self _p)
    (if Mute
      (Class|BPDrawPaletteSC|SetAppearSound :self _p)
      (else
        (Class|BPDrawPaletteSC|SetAppearSound :self _p :AppearSound %(snd)s)))
    (bind _lz (Utilities|Casting|CastToBPC_AppearLuz_SC (Actor|GetComponentbyClass _p "/SC_Base/Blueprints/BPC_AppearLuz_SC.BPC_AppearLuz_SC_C")))
    (Utilities|IsValid _lz
      (:"Is Valid"
        (Class|BPCAppearLuzSC|SetVanishSound :self _lz)
        (if Mute
          (Class|BPCAppearLuzSC|SetAppearSound :self _lz)
          (else
            (Class|BPCAppearLuzSC|SetAppearSound :self _lz :AppearSound %(snd)s)))))))
''' % dict(palc=PALC, snd=D('PalInSound'))

ORDER = ['PalSndAll', 'Kill', 'StrokeOut', 'FrameShow', 'TutBoot', 'TutShow', 'TutDemo', 'TutCards', 'TutOut', 'OutStep', 'LabTick', 'TutHide', 'PlaceLabels',
         'MantleSet', 'DemoStep', 'TutBegin', 'CardsSpawn', 'CardHov', 'TutPick', 'HintShow', 'HintOff', 'WarnSet', 'TutTick']
EVG = '''(event EventBeginPlay
  (CallFunction|TutBoot))

(event EventTick (DeltaSeconds)
  (CallFunction|TutTick :Dt (Math|Float|Min(Float) DeltaSeconds 0.05)))
'''
for _k in ORDER:
    assert CODES[_k].count('(') == CODES[_k].count(')'), 'parentesis ' + _k
