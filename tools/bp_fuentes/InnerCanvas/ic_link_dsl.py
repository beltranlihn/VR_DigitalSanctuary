# ic_link_dsl.py - BP_ICLink_IC: el visor le manda al PC (pantalla de los 8 dibujos) su estado y sus trazos, por OSC/UDP.
# No se toca el sistema de dibujo: se LEEN los trazos que va creando la herramienta (StrokeHistory de BPC_TBTool_NC) y sus
# nudos (K_Pos, K_Fwd, K_Up, K_Press de cada BP_TBStroke). El PC los reconstruye con BP_TBStroke (StartStroke/UpdatePosition).
# Linea de comandos (UECommandLine.txt del visor): -ICSlot=N (1..8) -ICWall=<IP del PC> -ICPort=9300.
# Mensajes (todos empiezan con slot y sesion):
#   /ic/st  slot sesion fase tiempo tinta idioma          (StateHz por segundo)
#   /ic/nm  slot sesion + nombre (string)                 (al empezar la sesion y cada 2 s)
#   /ic/new slot sesion + nombre                          (sesion nueva: el PC limpia ese cuadro)
#   /ic/cl  slot sesion                                   (se borraron los trazos: el de practica)
#   /ic/sb  slot sesion trazo preset size01 sizeLo sizeHi r g b grad gaR gaG gaB gbR gbG gbB ubase atlasV0 atlasV1 seed
#   /ic/k   slot sesion trazo nudo px py pz fx fy fz ux uy uz presion   (posicion relativa al centro del espacio, en el piso)
#   /ic/se  slot sesion trazo nudos
#   /ic/pr  slot sesion px py pz escala                   (empieza la presentacion: pivote relativo al centro y escala)
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ic_common import *
MSG = D('Msg')
CLR = lambda addr: '(Audio|OSC|ClearOSCMessage %s)\n  (Audio|OSC|SetOSCMessageAddress %s (Audio|OSC|ConvertStringToOSCAddress "%s"))' % (MSG, MSG, addr)
F = lambda x: '(Audio|OSC|AddFloattoOSCMessage %s %s)' % (MSG, x)
FI = lambda x: F('(Math|Conversions|ToFloat(Integer) %s)' % x)
STR = lambda x: '(Audio|OSC|AddStringtoOSCMessage %s %s)' % (MSG, x)
SEND = '(Audio|OSC|SendOSCMessage %s %s)' % (D('Client'), MSG)
HEAD2 = '%s\n  %s' % (FI(D('Slot')), FI(D('Session')))
CODES = {}

CODES['LinkBoot'] = '''(fn LinkBoot ()
  (bind _cmd (Utilities|GetCommandLine))
  (bind (_vs _fs) (Utilities|ParseParamValue _cmd "ICSlot="))
  (bind (_vw _fw) (Utilities|ParseParamValue _cmd "ICWall="))
  (bind (_vp _fp) (Utilities|ParseParamValue _cmd "ICPort="))
  (bind (_vc _fc) (Utilities|ParseParamValue _cmd "ICCmdPort="))
  %(slot)s
  %(wall)s
  %(port)s
  %(cp)s
  %(tb)s
  %(cen)s
  %(cl)s
  %(ok)s
  (Development|PrintString (Utilities|String|Append "LINK: visor " (Utilities|String|Append (Utilities|String|ToString(Integer) %(gslot)s) (Utilities|String|Append " -> " (Utilities|String|Append %(gwall)s (Utilities|String|Append ":" (Utilities|String|ToString(Integer) %(gport)s)))))) :bPrintToScreen false))
''' % dict(slot=DS('Slot', '(select _fs (Utilities|String|StringToInteger _vs) %s)' % D('Slot')),
           wall=DS('WallIP', '(select _fw _vw %s)' % D('WallIP')),
           port=DS('Port', '(select _fp (Utilities|String|StringToInteger _vp) %s)' % D('Port')),
           cp=DS('CmdPort', '(select _fc (Utilities|String|StringToInteger _vc) %s)' % D('CmdPort')),
           tb=DS('TB', '(Actor|GetActorOfClass "%s")' % TBC),
           cen=DS('Center', '(Transformation|GetActorLocation (Actor|GetActorOfClass "/Script/Engine.PlayerStart"))'),
           cl=DS('Client', '(Audio|OSC|CreateOSCClient %s %s "IC_Link")' % (D('WallIP'), D('Port'))),
           ok=DS('Ready', 'true'), gslot=D('Slot'), gwall=D('WallIP'), gport=D('Port'))

CODES['LinkState'] = '''(fn LinkState (P TL InkK ES)
  %s
  %s
  %s
  %s)
''' % (DS('Phase', 'P'), DS('TimeLeft', 'TL'), DS('Ink', 'InkK'), DS('LangES', 'ES'))

CODES['SendState'] = '''(fn SendState ()
  %s
  %s
  %s
  %s
  %s
  %s
  %s)
''' % (CLR('/ic/st'), HEAD2, FI(D('Phase')), F(D('TimeLeft')), F(D('Ink')), F('(select %s 1.0 0.0)' % D('LangES')), SEND)

CODES['SendName'] = '''(fn SendName ()
  %s
  %s
  %s
  %s)
''' % (CLR('/ic/nm'), HEAD2, STR(D('NameStr')), SEND)

CODES['LinkNew'] = '''(fn LinkNew (Name Ses)
  %s
  %s
  %s
  %s
  %s
  %s
  %s
  %s
  (CallFunction|SendName))
''' % (DS('NameStr', 'Name'), DS('Session', 'Ses'), DS('SentStrokes', '0'), DS('SentKnots', '0'),
       CLR('/ic/new'), HEAD2, STR(D('NameStr')), SEND)

CODES['LinkClear'] = '''(fn LinkClear ()
  %s
  %s
  %s
  %s
  %s)
''' % (DS('SentStrokes', '0'), DS('SentKnots', '0'), CLR('/ic/cl'), HEAD2, SEND)

CODES['LinkPresent'] = '''(fn LinkPresent (Pivot K)
  (bind _p (- Pivot %s))
  %s
  %s
  %s
  %s
  %s
  %s
  %s)
''' % (D('Center'), CLR('/ic/pr'), HEAD2, F('(.x _p)'), F('(.y _p)'), F('(.z _p)'), F('K'), SEND)

CODES['SendHead'] = '''(fn SendHead (S I)
  (bind (_cr _cg _cb _ca) (Utilities|Struct|BreakLinearColor (Class|BPTBStroke|GetBaseColor S)))
  (bind (_ar _ag _ab _aa) (Utilities|Struct|BreakLinearColor (Class|BPTBStroke|GetGradA S)))
  (bind (_br _bg _bb _ba) (Utilities|Struct|BreakLinearColor (Class|BPTBStroke|GetGradB S)))
  %(clr)s
  %(head)s
  %(i)s
  %(pre)s
  %(sz)s
  %(lo)s
  %(hi)s
  %(r)s
  %(g)s
  %(b)s
  %(grad)s
  %(gar)s
  %(gag)s
  %(gab)s
  %(gbr)s
  %(gbg)s
  %(gbb)s
  %(ub)s
  %(av0)s
  %(av1)s
  %(seed)s
  %(send)s)
''' % dict(clr=CLR('/ic/sb'), head=HEAD2, i=FI('I'), pre=FI('(Class|BPTBStroke|GetPreset S)'), sz=F('(Class|BPTBStroke|GetSize01 S)'),
           lo=F('(Class|BPTBStroke|GetSizeLo S)'), hi=F('(Class|BPTBStroke|GetSizeHi S)'), r=F('_cr'), g=F('_cg'), b=F('_cb'),
           grad=F('(select (Class|BPTBStroke|GetGradient S) 1.0 0.0)'), gar=F('_ar'), gag=F('_ag'), gab=F('_ab'),
           gbr=F('_br'), gbg=F('_bg'), gbb=F('_bb'), ub=F('(Class|BPTBStroke|GetUBase S)'),
           av0=F('(Class|BPTBStroke|GetAtlasV0 S)'), av1=F('(Class|BPTBStroke|GetAtlasV1 S)'), seed=FI('(Class|BPTBStroke|GetSeed S)'),
           send=SEND)

CODES['SendKnot'] = '''(fn SendKnot (S I K)
  (bind _p (- (Utilities|Array|Get(acopy) (Class|BPTBStroke|GetKPos S) K) %(cen)s))
  (bind _f (Utilities|Array|Get(acopy) (Class|BPTBStroke|GetKFwd S) K))
  (bind _u (Utilities|Array|Get(acopy) (Class|BPTBStroke|GetKUp S) K))
  %(clr)s
  %(head)s
  %(i)s
  %(k)s
  %(px)s
  %(py)s
  %(pz)s
  %(fx)s
  %(fy)s
  %(fz)s
  %(ux)s
  %(uy)s
  %(uz)s
  %(pr)s
  %(send)s)
''' % dict(cen=D('Center'), clr=CLR('/ic/k'), head=HEAD2, i=FI('I'), k=FI('K'), px=F('(.x _p)'), py=F('(.y _p)'), pz=F('(.z _p)'),
           fx=F('(.x _f)'), fy=F('(.y _f)'), fz=F('(.z _f)'), ux=F('(.x _u)'), uy=F('(.y _u)'), uz=F('(.z _u)'),
           pr=F('(Utilities|Array|Get(acopy) (Class|BPTBStroke|GetKPress S) K)'), send=SEND)

CODES['SendEnd'] = '''(fn SendEnd (I N)
  %s
  %s
  %s
  %s
  %s)
''' % (CLR('/ic/se'), HEAD2, FI('I'), FI('N'), SEND)

# FlushKnots: manda hasta 24 nudos nuevos del trazo S por cuadro (KBase/KTo en variables: los binds puros se re-evaluan)
CODES['FlushKnots'] = '''(fn FlushKnots (S I)
  %(kb)s
  %(kt)s
  (for _i (range (- %(gkt)s %(gkb)s))
    (CallFunction|SendKnot :S S :I I :K (+ %(gkb)s _i)))
  %(sk)s)
''' % dict(kb=DS('KBase', D('SentKnots')),
           kt=DS('KTo', '(select (< (Utilities|Array|Length (Class|BPTBStroke|GetKPos S)) (+ %s 24)) (Utilities|Array|Length (Class|BPTBStroke|GetKPos S)) (+ %s 24))' % (D('SentKnots'), D('SentKnots'))),
           gkt=D('KTo'), gkb=D('KBase'), sk=DS('SentKnots', D('KTo')))

# StreamStrokes: el trazo en curso manda sus nudos nuevos; si aparecio uno nuevo, cierra el anterior y abre el siguiente.
# Si la historia se achico (deshacer: el trazo de practica), avisa que se borro.
CODES['StreamStrokes'] = '''(fn StreamStrokes ()
  %(hist)s
  (bind _n (Utilities|Array|Length %(gh)s))
  (if (< _n %(ss)s)
    (CallFunction|LinkClear))
  (if (> %(ss)s 0)
    (CallFunction|FlushKnots :S (Utilities|Array|Get(acopy) %(gh)s (- %(ss)s 1)) :I (- %(ss)s 1)))
  (if (and (> _n %(ss)s) (> %(ss)s 0))
    (CallFunction|SendEnd :I (- %(ss)s 1) :N %(sk)s))
  (if (> _n %(ss)s)
    (CallFunction|SendHead :S (Utilities|Array|Get(acopy) %(gh)s %(ss)s) :I %(ss)s)
    %(sk0)s
    %(ssp)s))
''' % dict(hist=DS('Hist', '(Class|BPCTBToolNC|GetStrokeHistory (Class|BPTBDirectorNC|GetTBTool %s))' % D('TB')), gh=D('Hist'),
           ss=D('SentStrokes'), sk=D('SentKnots'), sk0=DS('SentKnots', '0'), ssp=DS('SentStrokes', '(+ %s 1)' % D('SentStrokes')))

CODES['LinkTick'] = '''(fn LinkTick (Dt)
  %(stt)s
  %(nmt)s
  (if (>= %(st)s (/ 1.0 (Math|Float|Max(Float) %(hz)s 0.5)))
    %(st0)s
    (CallFunction|SendState))
  (if (>= %(nm)s 2.0)
    %(nm0)s
    (CallFunction|SendName))
  (Utilities|IsValid %(tb)s
    (:"Is Valid"
      (CallFunction|StreamStrokes))))
''' % dict(stt=DS('StT', '(+ %s Dt)' % D('StT')), nmt=DS('NmT', '(+ %s Dt)' % D('NmT')), st=D('StT'), hz=D('StateHz'),
           st0=DS('StT', '0.0'), nm=D('NmT'), nm0=DS('NmT', '0.0'), tb=D('TB'))

# OnCmd (2026-11-12): ordenes del PC (botones RESET / REINICIAR de la pantalla). /ic/cmd visor modo id: visor 0 = todos; modo 1 =
# recentrar y reiniciar, 2 = solo reiniciar; el PC manda 3 copias con el mismo id (UDP) y aca se ejecuta una sola. El director lee Cmd.
CODES['OnCmd'] = '''(fn OnCmd (Message)
  %(fl)s
  (bind _a (Audio|OSC|ConvertOSCAddressToString (Audio|OSC|GetOSCMessageAddress Message)))
  (if (and (Utilities|String|EqualExactly(String) _a "/ic/cmd") (>= (Utilities|Array|Length %(gfl)s) 3))
    (bind _sl (Math|Float|Truncate (Utilities|Array|Get(acopy) %(gfl)s 0)))
    (bind _id (Math|Float|Truncate (Utilities|Array|Get(acopy) %(gfl)s 2)))
    (if (and (or (== _sl %(slot)s) (== _sl 0)) (!= _id %(last)s))
      %(setlast)s
      %(setcmd)s
      (Development|PrintString (Utilities|String|Append "LINK: orden del PC " (Utilities|String|ToString(Integer) %(gcmd)s)) :bPrintToScreen false))))
''' % dict(fl=DS('CFl', '(Audio|OSC|GetOSCMessageFloats Message)'), gfl=D('CFl'), slot=D('Slot'), last=D('LastCmdId'),
           setlast=DS('LastCmdId', '_id'), setcmd=DS('Cmd', '(Math|Float|Truncate (Utilities|Array|Get(acopy) %s 1))' % D('CFl')),
           gcmd=D('Cmd'))

ORDER = ['OnCmd', 'LinkBoot', 'LinkState', 'SendState', 'SendName', 'LinkNew', 'LinkClear', 'LinkPresent', 'SendHead', 'SendKnot', 'SendEnd',
         'FlushKnots', 'StreamStrokes', 'LinkTick']
EVG = '''(event EventBeginPlay
  (CallFunction|LinkBoot)
  (bind _srv (Audio|OSC|CreateOSCServer "0.0.0.0" %(gcp)s false true "IC_Cmd"))
  %(scs)s
  (Development|PrintString (Utilities|String|Append "LINK: escucho ordenes del PC en el puerto " (Utilities|String|ToString(Integer) %(gcp)s)) :bPrintToScreen false))

(event EventTick (DeltaSeconds)
  (if %(ready)s
    (CallFunction|LinkTick :Dt DeltaSeconds)))
''' % dict(ready=D('Ready'), gcp=D('CmdPort'), scs=DS('CmdServer', '_srv'))
