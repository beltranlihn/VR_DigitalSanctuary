# ic_wall_dsl.py - BP_ICWall_IC: la pantalla del PC de Inner Canvas (build de Windows). Recibe por OSC lo que manda cada visor
# (BP_ICLink_IC, ver ic_link_dsl.py) y reconstruye su dibujo en su celda con BP_TBStroke (StartStroke / UpdatePosition / EndStroke,
# los mismos trazos del visor). Celda k = visor k+1: origen Origins[k]; un pivote (TargetPoint) por celda del que cuelgan sus trazos.
# Al terminar la sesion (/ic/pr) el pivote gira SpinDeg grados/s: el dibujo queda girando hasta que ese visor empieza otra (/ic/new o
# una sesion mayor en /ic/st). Las 8 camaras fijas (SceneCapture2D con etiqueta ic_cap_<k>) dibujan en RTs[k]; BP_ICWallHUD_IC las
# pone en pantalla (4 x 2) con el nombre, el tiempo y la tinta.
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ic_common import *
NC = 8
AGI = lambda arr, i: '(Utilities|Array|Get(acopy) %s %s)' % (D(arr), i)
SET = lambda arr, i, x: '(Utilities|Array|SetArrayElem %s %s %s)' % (D(arr), i, x)
FL = lambda i: '(Utilities|Array|Get(acopy) %s %d)' % (D('Fl'), i)
TR = lambda x: '(Math|Float|Truncate %s)' % x
EQ = lambda s: '(Utilities|String|EqualExactly(String) %s "%s")' % (D('Addr'), s)
CODES = {}

CODES['WallBoot'] = '''(fn WallBoot ()
  (for _i (range %(nc)d)
    (Utilities|Array|Add %(ses)s 0)
    (Utilities|Array|Add %(names)s "")
    (Utilities|Array|Add %(phs)s -1)
    (Utilities|Array|Add %(tl)s 0.0)
    (Utilities|Array|Add %(inks)s 0.0)
    (Utilities|Array|Add %(spin)s false)
    (Utilities|Array|Add %(cur)s %(nost)s)
    (Utilities|Array|Add %(curi)s -1)
    (Utilities|Array|Add %(kn)s 0)
    (Utilities|Array|Add %(lrx)s -100.0)
    (Utilities|Array|Add %(prk)s 1.0)
    (Utilities|Array|Add %(pph)s 0)
    (Utilities|Array|Add %(ips)s "")
    (Utilities|Array|Add %(pt)s 0.0)
    (bind _o (Math|Vector|MakeVector (* (Math|Conversions|ToFloat(Integer) _i) %(gap)s) 0.0 0.0))
    (Utilities|Array|Add %(org)s _o)
    (Utilities|Array|Add %(piv)s (Game|SpawnActorfromClass "/Script/Engine.TargetPoint" (Math|Transform|MakeTransform :Location _o) "AlwaysSpawn"))
    (bind _rt (Rendering|CreateRenderTarget2D :Width %(rw)d :Height %(rh)d :Format "RTF_RGBA8" :ClearColor %(c0)s :bAutoGenerateMipMaps false))
    (Utilities|Array|Add %(rts)s _rt))
  (CallFunction|AssignCaps)
  %(cc)s
  (bind (_tv _tf) (Utilities|ParseParamValue (Utilities|GetCommandLine) "ICTestCmd="))
  %(tc)s
  (Development|PrintString "WALL: listo, 8 celdas" :bPrintToScreen false))
''' % dict(nc=NC, ses=D('Ses'), names=D('Names'), phs=D('Phases'), tl=D('TL'), inks=D('Inks'), spin=D('Spin'), cur=D('Cur'),
           nost=D('NoStroke'), curi=D('CurIdx'), kn=D('Knots'), lrx=D('LastRx'), gap=D('CellGap'), org=D('Origins'), piv=D('Pivots'),
           rts=D('RTs'), rw=3840, rh=1976, c0=LC(0.0, 0.0, 0.0, 1.0), prk=D('PresK'), pph=D('PresPh'), pt=D('PresT'), ips=D('IPs'),
           cc=DS('CmdClient', '(Audio|OSC|CreateOSCClient "127.0.0.1" %s "IC_Cmd")' % D('CmdPort')),
           tc=DS('TestCmd', '(select _tf (Utilities|String|StringToInteger _tv) 0)'))

# AssignCaps: cada SceneCapture2D del nivel dibuja en el RT de la celda mas cercana (celda k en x = k * CellGap)
CODES['AssignCaps'] = '''(fn AssignCaps ()
  (for _a (Actor|GetAllActorsOfClass "/Script/Engine.SceneCapture2D")
    (bind _l (Transformation|GetActorLocation _a))
    (bind _k (Math|Integer|Clamp(Integer) (Math|Float|Round (/ (.x _l) %(gap)s)) 0 7))
    (Class|SceneCaptureComponent2D|SetTextureTarget :self (Class|SceneCapture2D|GetCaptureComponent2D (Utilities|Casting|CastToSceneCapture2D _a)) :TextureTarget (Utilities|Array|Get(acopy) %(rts)s _k))))
''' % dict(gap=D('CellGap'), rts=D('RTs'))
CODES['ClearCell'] = '''(fn ClearCell (Cell)
  (bind _pv %(pv)s)
  (Variables|Default|SetTmp (Actor|GetAttachedActors _pv))
  (for _a (Variables|Default|GetTmp)
    (Actor|DestroyActor _a))
  (Transformation|SetActorRotation _pv (Math|Rotator|MakeRotator 0.0 0.0 0.0) false)
  (Transformation|SetActorLocation _pv %(org)s false true)
  (Transformation|SetActorScale3D _pv (Math|Vector|MakeVector 1.0 1.0 1.0))
  %(pk)s
  %(pp0)s
  %(sp)s
  %(cu)s
  %(ci)s
  %(kn)s)
''' % dict(pv=AGI('Pivots', 'Cell'), sp=SET('Spin', 'Cell', 'false'), cu=SET('Cur', 'Cell', D('NoStroke')), ci=SET('CurIdx', 'Cell', '-1'),
           kn=SET('Knots', 'Cell', '0'), org=AGI('Origins', 'Cell'), pk=SET('PresK', 'Cell', '1.0'), pp0=SET('PresPh', 'Cell', '0'))

# NewSes: una sesion mayor que la conocida = persona nueva en ese visor: se limpia la celda
CODES['NewSes'] = '''(fn NewSes ()
  (if (> %(s)s %(gs)s)
    (CallFunction|ClearCell :Cell %(c)s)
    %(ss)s
    %(nm)s
    (Development|PrintString (Utilities|String|Append "WALL: sesion nueva en el visor " (Utilities|String|ToString(Integer) (+ %(c)s 1))) :bPrintToScreen false)))
''' % dict(s=D('S'), gs=AGI('Ses', D('C')), c=D('C'), ss=SET('Ses', D('C'), D('S')), nm=SET('Names', D('C'), '""'))

CODES['OnState'] = '''(fn OnState ()
  (CallFunction|NewSes)
  (if (== %(s)s %(gs)s)
    %(ph)s
    %(tl)s
    %(ink)s
    %(lrx)s))
''' % dict(s=D('S'), gs=AGI('Ses', D('C')), ph=SET('Phases', D('C'), TR(FL(2))), tl=SET('TL', D('C'), FL(3)), ink=SET('Inks', D('C'), FL(4)),
           lrx=SET('LastRx', D('C'), '(Utilities|Time|GetGameTimeInSeconds)'))

# OnName: el indice cuenta TODOS los argumentos (slot, sesion, nombre = 2); salidas (valor, exito). El OSC de Unreal escribe un byte
# por letra (la Ñ como 0xD1) y al leer EXTIENDE EL SIGNO: llega U+FFD1. El teclado solo produce A-Z, Ñ y ñ: se devuelven esas dos.
CODES['OnName'] = '''(fn OnName (Message)
  (bind (_raw _ok) (Audio|OSC|GetOSCMessageStringatIndex Message 2))
  (bind _str (Utilities|String|Replace (Utilities|String|Replace _raw "\uffd1" "\u00d1") "\ufff1" "\u00f1"))
  (CallFunction|NewSes)
  (if (== %(s)s %(gs)s)
    %(nm)s))
''' % dict(s=D('S'), gs=AGI('Ses', D('C')), nm=SET('Names', D('C'), '_str'))

CODES['StrokeHead'] = '''(fn StrokeHead ()
  (CallFunction|EndCur :Cell %(c)s)
  (bind _s (Game|SpawnActorfromClass "%(strokec)s" (Math|Transform|MakeTransform) "AlwaysSpawn"))
  (Class|BPTBStroke|SetPreset :self _s :Preset %(pre)s)
  (Class|BPTBStroke|SetSize01 :self _s :Size01 %(sz)s)
  (Class|BPTBStroke|SetSizeLo :self _s :SizeLo %(lo)s)
  (Class|BPTBStroke|SetSizeHi :self _s :SizeHi %(hi)s)
  (Class|BPTBStroke|SetBaseColor :self _s :BaseColor (Utilities|Struct|MakeLinearColor %(r)s %(g)s %(b)s 1.0))
  (Class|BPTBStroke|SetUBase :self _s :UBase %(ub)s)
  (Class|BPTBStroke|SetAtlasV0 :self _s :AtlasV0 %(av0)s)
  (Class|BPTBStroke|SetAtlasV1 :self _s :AtlasV1 %(av1)s)
  (Class|BPTBStroke|SetSeed :self _s :Seed %(seed)s)
  (Class|BPTBStroke|SetLook _s (> %(grad)s 0.5) (Utilities|Struct|MakeLinearColor %(gar)s %(gag)s %(gab)s 1.0) (Utilities|Struct|MakeLinearColor %(gbr)s %(gbg)s %(gbb)s 1.0))
  (Transformation|AttachActorToActor :self _s :ParentActor %(pv)s :LocationRule "KeepWorld" :RotationRule "KeepWorld" :ScaleRule "KeepWorld" :bWeldSimulatedBodies false)
  %(cur)s
  %(ci)s
  %(kn)s)
''' % dict(c=D('C'), strokec=STROKEC, pre=TR(FL(3)), sz=FL(4), lo=FL(5), hi=FL(6), r=FL(7), g=FL(8), b=FL(9), grad=FL(10),
           gar=FL(11), gag=FL(12), gab=FL(13), gbr=FL(14), gbg=FL(15), gbb=FL(16), ub=FL(17), av0=FL(18), av1=FL(19), seed=TR(FL(20)),
           pv=AGI('Pivots', D('C')), cur=SET('Cur', D('C'), '_s'), ci=SET('CurIdx', D('C'), TR(FL(2))), kn=SET('Knots', D('C'), '0'))

CODES['StrokeKnot'] = '''(fn StrokeKnot ()
  (bind _s %(cur)s)
  (bind _k %(k)s)
  (bind _p (+ %(org)s (Math|Vector|MakeVector %(px)s %(py)s %(pz)s)))
  (bind _f (Math|Vector|MakeVector %(fx)s %(fy)s %(fz)s))
  (bind _u (Math|Vector|MakeVector %(ux)s %(uy)s %(uz)s))
  (Utilities|IsValid _s
    (:"Is Valid"
      (if (and (== %(i)s %(ci)s) (>= _k %(kn)s))
        (if (== %(kn)s 0)
          (Class|BPTBStroke|StartStroke _s _p _f _u %(pr)s)
          (else
            (Class|BPTBStroke|UpdatePosition _s _p _f _u %(pr)s)))
        %(kns)s))))
''' % dict(cur=AGI('Cur', D('C')), k=TR(FL(3)), org=AGI('Origins', D('C')), px=FL(4), py=FL(5), pz=FL(6), fx=FL(7), fy=FL(8), fz=FL(9),
           ux=FL(10), uy=FL(11), uz=FL(12), pr=FL(13), i=TR(FL(2)), ci=AGI('CurIdx', D('C')), kn=AGI('Knots', D('C')),
           kns=SET('Knots', D('C'), '(+ _k 1)'))

CODES['EndCur'] = '''(fn EndCur (Cell)
  (Utilities|IsValid %(cur)s
    (:"Is Valid"
      (if (> %(kn)s 0)
        (Class|BPTBStroke|SwayConfig %(cur)s %(on)s %(st)s %(wv)s %(sp)s %(spn)s %(spv)s %(sc)s %(dir)s %(fd)s)
        (Class|BPTBStroke|EndStroke %(cur)s))
      %(cu)s)
    (:"Is Not Valid"
      %(cu)s)))
''' % dict(cur=AGI('Cur', 'Cell'), kn=AGI('Knots', 'Cell'), on=D('SwOn'), st=D('SwStr'), wv=D('SwWave'), sp=D('SwSpeed'), spn=D('SwSpan'),
           spv=D('SwSpeedVar'), sc=D('SwScale'), dir=D('SwDir'), fd=D('SwFade'), cu=SET('Cur', 'Cell', D('NoStroke')))

CODES['OnClear'] = '''(fn OnClear ()
  (if (== %(s)s %(gs)s)
    (CallFunction|ClearCell :Cell %(c)s)))
''' % dict(s=D('S'), gs=AGI('Ses', D('C')), c=D('C'))

# Presentacion en la pantalla (2026-11-12, pedido de Beltran): el dibujo NO se agranda. Se des-dibuja en su lugar (Reveal 1 -> 0, como
# en el visor), se centra en su celda a su misma altura y vuelve a dibujarse (0 -> 1) girando; queda girando hasta la sesion nueva.
# GetAttachedActors es PURO: un for sobre el se re-evalua en cada vuelta y al soltar/destruir se saltea la mitad -> se copia a Tmp.
# Solo se achica si girando no cabe en el cuadro (PresFit cm de ancho y de alto). PresPh por celda: 0 nada, 1 se va, 2 vuelve.
CODES['OnPresent'] = '''(fn OnPresent ()
  (CallFunction|EndCur :Cell %(c)s)
  %(ph1)s
  %(t0)s
  (Development|PrintString (Utilities|String|Append "WALL: presentacion del visor " (Utilities|String|ToString(Integer) (+ %(c)s 1))) :bPrintToScreen false))
''' % dict(c=D('C'), ph1=SET('PresPh', D('C'), '1'), t0=SET('PresT', D('C'), '0.0'))

CODES['RevealCell'] = '''(fn RevealCell (Cell R)
  (for _a (Actor|GetAttachedActors %(pv)s)
    (bind _s (Utilities|Casting|CastToBP_TBStroke :Object _a)
      (:then
        (Class|BPTBStroke|SetTaper :self _s :T 6.0)
        (Class|BPTBStroke|SetReveal :self _s :R R))
      (:CastFailed))))
''' % dict(pv=AGI('Pivots', 'Cell'))

CODES['Relocate'] = '''(fn Relocate (Cell)
  (bind _pv %(pv)s)
  (Transformation|SetActorScale3D _pv (Math|Vector|MakeVector 1.0 1.0 1.0))
  (Transformation|SetActorRotation _pv (Math|Rotator|MakeRotator 0.0 0.0 0.0) false)
  (Variables|Default|SetTmp (Actor|GetAttachedActors _pv))
  (bind (_bc _be) (Collision|GetActorArrayBounds (Variables|Default|GetTmp) false))
  (for _a (Variables|Default|GetTmp)
    (Transformation|DetachFromActor _a "KeepWorld" "KeepWorld" "KeepWorld"))
  (Transformation|SetActorLocation _pv _bc false true)
  (for _a (Variables|Default|GetTmp)
    (Transformation|AttachActorToActor :self _a :ParentActor _pv :LocationRule "KeepWorld" :RotationRule "KeepWorld" :ScaleRule "KeepWorld" :bWeldSimulatedBodies false))
  (Transformation|SetActorLocation _pv (+ %(org)s (Math|Vector|MakeVector 0.0 0.0 (.z _bc))) false true)
  (bind _r (Math|Float|Max(Float) (Math|Float|Sqrt (+ (* (.x _be) (.x _be)) (* (.y _be) (.y _be)))) 10.0))
  (bind _h (Math|Float|Max(Float) (.z _be) 10.0))
  %(pk)s
  (bind _k %(pkg)s)
  (Transformation|SetActorScale3D _pv (Math|Vector|MakeVector _k _k _k))
  %(sp)s
  (Development|PrintString (Utilities|String|Append "WALL: el dibujo del visor " (Utilities|String|Append (Utilities|String|ToString(Integer) (+ Cell 1)) (Utilities|String|Append " vuelve girando, escala " (Utilities|String|Append (Utilities|String|ToString(Float) _k) (Utilities|String|Append " centro " (Utilities|String|Append (Utilities|String|ToString(Vector) _bc) (Utilities|String|Append " ext " (Utilities|String|ToString(Vector) _be)))))))) :bPrintToScreen false))
''' % dict(pv=AGI('Pivots', 'Cell'), org=AGI('Origins', 'Cell'), sp=SET('Spin', 'Cell', 'true'), pkg=AGI('PresK', 'Cell'),
           pk=SET('PresK', 'Cell', '(Math|Float|Min(Float) 1.0 (Math|Float|Min(Float) (/ %s (* 2.0 _r)) (/ %s (* 2.0 _h))))' % (D('PresFit'), D('PresFit'))))

CODES['PresStep'] = '''(fn PresStep (Cell Dt)
  (bind _ph %(ph)s)
  (if (> _ph 0)
    %(tp)s
    (bind _t %(t)s)
    (if (== _ph 1)
      (CallFunction|RevealCell :Cell Cell :R (- 1.0 %(eh)s))
      (if (>= _t %(ht)s)
        (CallFunction|Relocate :Cell Cell)
        (CallFunction|RevealCell :Cell Cell :R 0.0)
        %(ph2)s
        %(t0)s)
      (else
        (CallFunction|RevealCell :Cell Cell :R %(es)s)
        (if (>= _t %(st)s)
          (CallFunction|RevealCell :Cell Cell :R 1.0)
          %(ph0)s)))))
''' % dict(ph=AGI('PresPh', 'Cell'), t=AGI('PresT', 'Cell'), tp=SET('PresT', 'Cell', '(+ %s Dt)' % AGI('PresT', 'Cell')),
           ht=D('PresHideT'), st=D('PresShowT'), ph2=SET('PresPh', 'Cell', '2'), ph0=SET('PresPh', 'Cell', '0'), t0=SET('PresT', 'Cell', '0.0'),
           eh=EASE('(Math|Float|Clamp(Float) (/ _t (Math|Float|Max(Float) %s 0.1)) 0.0 1.0)' % D('PresHideT')),
           es=EASE('(Math|Float|Clamp(Float) (/ _t (Math|Float|Max(Float) %s 0.1)) 0.0 1.0)' % D('PresShowT')))

CODES['Route'] = '''(fn Route (Message)
  (if %(k)s
    (CallFunction|StrokeKnot)
    (elif %(st)s
      (CallFunction|OnState)
      (elif %(sb)s
        (CallFunction|StrokeHead)
        (elif %(se)s
          (CallFunction|EndCur :Cell %(c)s)
          (elif (or %(nm)s %(nw)s)
            (CallFunction|OnName :Message Message)
            (elif %(cl)s
              (CallFunction|OnClear)
              (elif %(pr)s
                (CallFunction|OnPresent)))))))))
''' % dict(k=EQ('/ic/k'), st=EQ('/ic/st'), sb=EQ('/ic/sb'), se=EQ('/ic/se'), nm=EQ('/ic/nm'), nw=EQ('/ic/new'), cl=EQ('/ic/cl'),
           pr=EQ('/ic/pr'), c=D('C'))

CODES['OnMsg'] = '''(fn OnMsg (Message)
  %(addr)s
  %(fl)s
  %(rx)s
  (if (>= (Utilities|Array|Length %(gfl)s) 2)
    %(c)s
    %(s)s
    (if (and (>= %(gc)s 0) (< %(gc)s %(nc)d))
      (Utilities|Array|SetArrayElem %(ips)s %(gc)s %(rxip)s)
      (CallFunction|Route :Message Message))))
''' % dict(addr=DS('Addr', '(Audio|OSC|ConvertOSCAddressToString (Audio|OSC|GetOSCMessageAddress Message))'),
           fl=DS('Fl', '(Audio|OSC|GetOSCMessageFloats Message)'), rx=DS('RxCount', '(+ %s 1)' % D('RxCount')), gfl=D('Fl'),
           c=DS('C', '(- %s 1)' % TR(FL(0))), s=DS('S', TR(FL(1))), gc=D('C'), nc=NC, ips=D('IPs'), rxip=D('RxIP'))

# SendCmd (2026-11-12): botones de la pantalla. Manda /ic/cmd (visor, modo, id) 3 veces a la IP de la que llegan los mensajes de ese
# visor (RxIP -> IPs[C] en OnMsg), puerto CmdPort (9301). Modo 1 = recentrar y reiniciar, 2 = solo reiniciar.
CODES['SendCmd'] = '''(fn SendCmd (Cell Mode)
  (bind _ip %(gip)s)
  (if (> (Utilities|String|Len _ip) 0)
    (Audio|OSC|SetSendIPAddress %(cl)s _ip %(port)s)
    %(sid)s
    (for _k (range 3)
      (Audio|OSC|ClearOSCMessage %(m)s)
      (Audio|OSC|SetOSCMessageAddress %(m)s (Audio|OSC|ConvertStringToOSCAddress "/ic/cmd"))
      (Audio|OSC|AddFloattoOSCMessage %(m)s (Math|Conversions|ToFloat(Integer) (+ Cell 1)))
      (Audio|OSC|AddFloattoOSCMessage %(m)s (Math|Conversions|ToFloat(Integer) Mode))
      (Audio|OSC|AddFloattoOSCMessage %(m)s (Math|Conversions|ToFloat(Integer) %(gid)s))
      (Audio|OSC|SendOSCMessage %(cl)s %(m)s))
    (Development|PrintString (Utilities|String|Append "WALL: orden " (Utilities|String|Append (Utilities|String|ToString(Integer) Mode) (Utilities|String|Append " al visor " (Utilities|String|Append (Utilities|String|ToString(Integer) (+ Cell 1)) (Utilities|String|Append " en " _ip))))) :bPrintToScreen false)))
''' % dict(gip=AGI('IPs', 'Cell'), cl=D('CmdClient'), port=D('CmdPort'), m=D('CMsg'), sid=DS('CmdId', '(Math|Random|RandomIntegerinRange 1 1000000)'),
           gid=D('CmdId'))

CODES['WallTick'] = '''(fn WallTick (Dt)
  (if (and (> %(tcg)s 0) (>= (Utilities|Time|GetGameTimeInSeconds) 25.0))
    (CallFunction|SendCmd :Cell (- %(tcg)s 1) :Mode 1)
    %(tc0)s)
  (for _i (range %(nc)d)
    (CallFunction|PresStep :Cell _i :Dt Dt)
    (if %(spin)s
      (Transformation|AddActorWorldRotation %(pv)s (Math|Rotator|MakeRotator 0.0 0.0 (* %(deg)s Dt)) false false)
      (bind _k (Math|Interpolation|FInterpTo (.x (Transformation|GetActorScale3D %(pv)s)) %(pk)s Dt %(gr)s))
      (Transformation|SetActorScale3D %(pv)s (Math|Vector|MakeVector _k _k _k)))))
''' % dict(nc=NC, spin=AGI('Spin', '_i'), pv=AGI('Pivots', '_i'), deg=D('SpinDeg'), pk=AGI('PresK', '_i'), gr=D('GrowSpeed'),
           tcg=D('TestCmd'), tc0=DS('TestCmd', '0'))

# EVG2 se escribe DESPUES de crear con create_node el AssignOnOscMessageReceived (que genera el evento con la firma correcta)
EVG2 = '''(event Custom|OnOscMessageReceived_Event (Message IPAddress Port)
  (CallFunction|OnMsg :Message Message))
'''
ORDER = ['AssignCaps', 'WallBoot', 'ClearCell', 'NewSes', 'OnState', 'OnName', 'EndCur', 'StrokeHead', 'StrokeKnot', 'OnClear', 'RevealCell', 'Relocate', 'PresStep', 'OnPresent', 'SendCmd', 'Route', 'OnMsg', 'WallTick']
EVG = '''(event EventBeginPlay
  (CallFunction|WallBoot)
  (bind _cmd (Utilities|GetCommandLine))
  (bind (_vp _fp) (Utilities|ParseParamValue _cmd "ICPort="))
  %(lp)s
  (bind _srv (Audio|OSC|CreateOSCServer "0.0.0.0" %(glp)s false true "IC_Wall"))
  %(sv)s
  (Development|PrintString (Utilities|String|Append "WALL: escuchando en el puerto " (Utilities|String|ToString(Integer) %(glp)s)) :bPrintToScreen false))

(event EventTick (DeltaSeconds)
  (CallFunction|WallTick :Dt (Math|Float|Min(Float) DeltaSeconds 0.05)))

(event EventEndPlay (EndPlayReason)
  (Utilities|IsValid %(gsv)s
    (:"Is Valid"
      (Audio|OSC|Stop %(gsv)s))))
''' % dict(lp=DS('ListenPort', '(select _fp (Utilities|String|StringToInteger _vp) %s)' % D('ListenPort')), glp=D('ListenPort'),
           sv=DS('Server', '_srv'), gsv=D('Server'))
