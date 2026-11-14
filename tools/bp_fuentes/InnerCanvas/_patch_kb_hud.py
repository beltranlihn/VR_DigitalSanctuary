# parche 2026-11-12 noche (Beltran): botones de idioma a su escala del editor (1,5), logo de Alma blanco, teclado dentro del MARCO
# (mismo lugar que las instrucciones), HUD con la fuente de 64 (nombre y reloj nitidos) y alineado a la cabeza.
import io
NL = chr(10)


def sub(path, pairs):
    s = io.open(path, encoding='utf-8').read()
    for old, new, cnt in pairs:
        n = s.count(old)
        assert n >= 1, (path, old[:70])
        s = s.replace(old, new, cnt)
    io.open(path, 'w', encoding='utf-8').write(s)


WFONT = '/Game/InnerCanvas/UI/F_ICWall_IC.F_ICWall_IC'

# ---- teclado: nombre al doble de resolucion y con la fuente de 64 (la Quicksand de 9 estirada x8 se veia pixelada)
sub('ic_kb_dsl.py', [
    (":Width 1024 :Height 256 :Format", ":Width 2048 :Height 512 :Format", 1),
    (":Width 512 :Height 128 :Format", ":Width 1024 :Height 256 :Format", 1),
    ("nw=D('NameWork'), nrt=D('NameRT'), c0=LC(0.0, 0.0, 0.0, 0.0), font=FONT, mid=V2('512.0', '128.0'),",
     "nw=D('NameWork'), nrt=D('NameRT'), c0=LC(0.0, 0.0, 0.0, 0.0), font='" + WFONT + "', mid=V2('1024.0', '256.0'),", 1),
    ("sc=V2('8.0', '8.0'), sch=V2('5.0', '5.0'), tcol=D('TextColor'), hcol=D('PromptColor'), z2=V2('0.0', '0.0'),\n           half=V2('512.0', '128.0'),",
     "sc=V2('2.25', '2.25'), sch=V2('1.4', '1.4'), tcol=D('TextColor'), hcol=D('PromptColor'), z2=V2('0.0', '0.0'),\n           half=V2('1024.0', '256.0'),", 1),
])

# ---- HUD: reloj en 512/256 con la fuente de 64; al aparecer, el nombre y el reloj se alinean a la cabeza (antes al "arriba" del mundo
# en el momento del arranque: si la cabeza estaba ladeada quedaban girados)
s = io.open('ic_kit_dsl.py', encoding='utf-8').read()
s = s.replace("TW = 192\nT_SCALE = 4.8", "TW = 512\nT_SCALE = 1.8", 1)
s = s.replace("from ic_common import D as V, DS as S, CAM, V2, LC, FONT, PANE",
              "from ic_common import D as V, DS as S, CAM, CAMROT, V2, LC, FONT, PANE\nFONT = '" + WFONT + "'", 1)
old = """CODES['HudShow'] = '''(fn HudShow ()
  (if (not %s)
    %s
    (Class|BPHUDArtSC|HUDAppear %s)"""
assert old in s
new = """CODES['HudShow'] = '''(fn HudShow ()
  (if (not %s)
    %s
    (bind _cu (* (Math|Vector|GetUpVector """ + "' + CAMROT + '" + """) -1.0))
    (Transformation|SetWorldRotation """ + "' + V('TimerQuad') + '" + """ (Math|Rotator|MakeRotfromZY (- """ + "' + CAM + '" + """ (Transformation|GetWorldLocation """ + "' + V('TimerQuad') + '" + """)) _cu) false true)
    (Transformation|SetWorldRotation """ + "' + V('NameQuad') + '" + """ (Math|Rotator|MakeRotfromZY (- """ + "' + CAM + '" + """ (Transformation|GetWorldLocation """ + "' + V('NameQuad') + '" + """)) _cu) false true)
    (Class|BPHUDArtSC|HUDAppear %s)"""
s = s.replace(old, new, 1)
io.open('ic_kit_dsl.py', 'w', encoding='utf-8').write(s)

# ---- tutor: marco del teclado (FrameShow), el marco sigue hasta las instrucciones, pista del nombre dentro del marco
t = io.open('ic_tutor2_dsl.py', encoding='utf-8').read()
FRAMESHOW = '''
# FrameShow (Beltran 11-12 noche: "encaja el teclado dentro de un marco como el de las instrucciones, en el mismo lugar"): el actor
# va donde van las instrucciones y se ve el marco con el logo; el director pone el teclado delante. TutBegin no lo mueve si ya esta.
CODES['FrameShow'] = \'\'\'(fn FrameShow ()
  (bind _yaw (.yaw %(camrot)s))
  (bind _fwd (Math|Vector|MakeVector (Math|Trig|Cos(Degrees) _yaw) (Math|Trig|Sin(Degrees) _yaw) 0.0))
  (bind _pos (+ %(cam)s (+ (* _fwd %(dist)s) (Math|Vector|MakeVector 0.0 0.0 (* -1.0 %(below)s)))))
  (Transformation|SetActorLocationAndRotation self _pos (Math|Rotator|MakeRotfromX (- _pos %(cam)s)) false true)
  (Transformation|SetRelativeLocation %(frame)s (Math|Vector|MakeVector %(fx)s 0.0 %(fz)s) false true)
  (Transformation|SetRelativeScale3D %(frame)s (Math|Vector|MakeVector (/ %(fw)s 100.0) (/ %(fh)s 100.0) 1.0))
  %(fsize)s
  (Transformation|SetRelativeLocation %(logo)s (Math|Vector|MakeVector (- %(fx)s 0.5) (* -0.206 %(fw)s) (+ %(fz)s (* 0.376 %(fh)s))) false true)
  (Transformation|SetRelativeScale3D %(logo)s (Math|Vector|MakeVector (/ %(lw)s 100.0) (/ %(lw)s 400.0) 1.0))
  %(llt)s
  %(lout)s
  %(fon)s
  %(ft0)s
  (Development|PrintString "TUTOR: marco del teclado" :bPrintToScreen false))
\'\'\' % dict(camrot=CAMROT, cam=CAM, dist=D('Dist'), below=D('Below'), frame=D('Frame'), fx=D('FrameX'), fz=D('FrameZ'), fw=D('FrameW'),
           fh=D('FrameH'), fsize=VP(D('Frame'), 'Size', '(Math|Vector|MakeVector %s %s 6.0)' % (D('FrameW'), D('FrameH'))), logo=D('Logo'),
           lw=D('LogoW'), llt=SP(D('Logo'), 'LT', '20.0'), lout=SP(D('Logo'), 'Out', '0.0'), fon=DS('FrameOn', 'true'), ft0=DS('FrameT', '0.0'))
'''
anchor = "CODES['TutShow'] = "
assert anchor in t
t = t.replace(anchor, FRAMESHOW.lstrip(NL) + NL + anchor, 1)
# TutBegin: no se mueve si el marco ya esta (viene del teclado)
old = "  (Transformation|SetActorLocationAndRotation self _pos (Math|Rotator|MakeRotfromX (- _pos %(cam)s)) false true)\n  %(pc)s\n  (bind _pal (Game|SpawnActorfromClass \"%(palc)s\" (Math|Transform|MakeTransform :Location _pos) \"AlwaysSpawn\"))"
assert old in t
t = t.replace(old, "  (if (not %(fon)s)\n    (Transformation|SetActorLocationAndRotation self _pos (Math|Rotator|MakeRotfromX (- _pos %(cam)s)) false true))\n  %(pc)s\n  (bind _pal (Game|SpawnActorfromClass \"%(palc)s\" (Math|Transform|MakeTransform :Location (Transformation|GetActorLocation self)) \"AlwaysSpawn\"))", 1)
old = "''' % dict(es=DS('ES', 'Spanish'), tb=DS('TB', 'TBA'), ped=DS('Ped', 'PedA'), sd=DS('Sd', '1.0'), camrot=CAMROT, cam=CAM,"
assert old in t
t = t.replace(old, "''' % dict(es=DS('ES', 'Spanish'), tb=DS('TB', 'TBA'), ped=DS('Ped', 'PedA'), sd=DS('Sd', '1.0'), camrot=CAMROT, cam=CAM, fon=D('FrameOn'),", 1)
# TutBegin no debe apagar el marco ya visible: el Fade del marco lo maneja TutTick
t = t.replace("  %(fsize)s\n  %(ffade)s\n  (Transformation|SetRelativeLocation %(logo)s", "  %(fsize)s\n  (Transformation|SetRelativeLocation %(logo)s", 1)
t = t.replace("  %(lout)s\n  %(lrev)s\n  %(hrect)s", "  %(lout)s\n  %(hrect)s", 1)
# TutTick: el marco del teclado (FrameOn) y el de las instrucciones (Run) son el mismo; el titulo "Instrucciones" solo con Run
old = "  (if %(run)s\n    %(tp)s\n    (bind _in %(ein)s)"
assert old in t
t = t.replace(old, """  (if %(fo)s
    %(ftp)s)
  (bind _fo (select %(fo)s %(efo)s 0.0))
  (if (and %(fo)s (not %(run)s))
    %(fff)s
    %(ffl)s
    %(ffv)s
    %(ffw)s)
  (if %(run)s
    %(tp)s
    (bind _in %(ein)s)""", 1)
old = "    %(fk)s\n    (bind _fk %(gfk)s)\n    (bind _fv (> _fk 0.01))\n    %(ff)s\n    %(lr)s\n    %(hf)s\n    %(fv)s\n    %(lv)s\n    %(hdv)s"
assert old in t
t = t.replace(old, "    %(fk)s\n    (bind _fk %(gfk)s)\n    (bind _fv (> _fk 0.01))\n    (bind _hk (* _in (- 1.0 _pk)))\n    %(ff)s\n    %(lr)s\n    %(hf)s\n    %(fv)s\n    %(lv)s\n    %(hdv)s", 1)
t = t.replace("fk=DS('FrameK', '(* _in (- 1.0 _pk))'), gfk=D('FrameK'),", "fk=DS('FrameK', '(* (Math|Float|Max(Float) _in _fo) (- 1.0 _pk))'), gfk=D('FrameK'),", 1)
t = t.replace("ff=SP(D('Frame'), 'Fade', '_fk'), lr=SP(D('Logo'), 'Reveal', '_fk'), hf=SP(D('Hdr'), 'Fade', '_fk'),",
              "ff=SP(D('Frame'), 'Fade', '_fk'), lr=SP(D('Logo'), 'Reveal', '_fk'), hf=SP(D('Hdr'), 'Fade', '_hk'),", 1)
t = t.replace("fv=VIS(D('Frame'), '_fv'), lv=VIS(D('Logo'), '_fv'), hdv=VIS(D('Hdr'), '_fv'),",
              "fv=VIS(D('Frame'), '_fv'), lv=VIS(D('Logo'), '_fv'), hdv=VIS(D('Hdr'), '(> _hk 0.01)'),"
              " fo=D('FrameOn'), ftp=DS('FrameT', '(+ %s Dt)' % D('FrameT')), efo=EASE(CL('(/ %s 0.5)' % D('FrameT'))),"
              " fff=SP(D('Frame'), 'Fade', '_fo'), ffl=SP(D('Logo'), 'Reveal', '_fo'), ffv=VIS(D('Frame'), '(> _fo 0.01)'), ffw=VIS(D('Logo'), '(> _fo 0.01)'),", 1)
# TutHide: el marco del teclado tambien se apaga
t = t.replace("''' % dict(r0=DS('Run', 'false'), d0=DS('DemoT', '-1.0'), o0=DS('OutT', '-1.0'), c0=DS('CardsT', '-1.0'), p0=DS('PickT', '-1.0'),\n           cs0=DS('CardsOn', 'false'), h0c=D('H0'),",
              "''' % dict(r0=DS('Run', 'false') + NL2 + DS('FrameOn', 'false'), d0=DS('DemoT', '-1.0'), o0=DS('OutT', '-1.0'), c0=DS('CardsT', '-1.0'), p0=DS('PickT', '-1.0'),\n           cs0=DS('CardsOn', 'false'), h0c=D('H0'),", 1)
t = t.replace("PALROT = '", "NL2 = chr(10) + '  '\nPALROT = '", 1)
# HintShow: modo 2 (nombre) dentro del marco, abajo, sin mover el actor
old = "  (Transformation|SetActorLocationAndRotation self Pos (Math|Rotator|MakeRotfromX (- Pos %(cam)s)) false true)\n  %(hm)s"
assert old in t
t = t.replace(old, "  (if (== Mode 1)\n    (Transformation|SetActorLocationAndRotation self Pos (Math|Rotator|MakeRotfromX (- Pos %(cam)s)) false true))\n  %(hm)s", 1)
old = "  (Transformation|SetRelativeLocation %(h0)s (Math|Vector|MakeVector 0.0 0.0 0.0) false true)"
assert old in t
t = t.replace(old, "  (Transformation|SetRelativeLocation %(h0)s (select (== Mode 1) (Math|Vector|MakeVector 0.0 0.0 0.0) (Math|Vector|MakeVector (- %(fx)s 1.0) 0.0 (+ %(fz)s (+ (* -0.5 %(fh)s) 5.5)))) false true)", 1)
t = t.replace("''' % dict(cam=CAM, hm=DS('HintM', 'Mode'), h0=D('H0'), h1=D('H1'), hh=D('HintH'),",
              "''' % dict(cam=CAM, hm=DS('HintM', 'Mode'), h0=D('H0'), h1=D('H1'), hh=D('HintH'), fx=D('FrameX'), fz=D('FrameZ'), fh=D('FrameH'),", 1)
t = t.replace("ORDER = ['Kill', 'StrokeOut', 'TutBoot',", "ORDER = ['Kill', 'StrokeOut', 'FrameShow', 'TutBoot',", 1)
io.open('ic_tutor2_dsl.py', 'w', encoding='utf-8').write(t)

# ---- spec del tutor: FrameOn, FrameT y FrameShow
p = io.open('ic_spec_tutor.py', encoding='utf-8').read()
p = p.replace("v('FrameK', F), v('HintM', I),", "v('FrameK', F), v('FrameOn', B), v('FrameT', F), v('HintM', I),", 1)
p = p.replace("('Kill', [('A', O('/Script/Engine.Actor'), True)])],", "('Kill', [('A', O('/Script/Engine.Actor'), True)]), ('FrameShow', [])],", 1)
io.open('ic_spec_tutor.py', 'w', encoding='utf-8').write(p)

# ---- director: botones a 1,5 (su escala en el editor), logo blanco, teclado dentro del marco con teclas claras
f = io.open('ic_flow2_dsl.py', encoding='utf-8').read()
old = "  (Transformation|SetActorScale3D %(ben)s (Math|Vector|MakeVector 1.0 1.0 1.0))\n  (Transformation|SetActorScale3D %(bes)s (Math|Vector|MakeVector 1.0 1.0 1.0)))\n\"\"\" % dict(ty=TY_EXPR"
assert old in f
f = f.replace(old, "  (Transformation|SetActorScale3D %(ben)s (Math|Vector|MakeVector 1.5 1.5 1.5))\n  (Transformation|SetActorScale3D %(bes)s (Math|Vector|MakeVector 1.5 1.5 1.5)))\n\"\"\" % dict(ty=TY_EXPR", 1)
old = '  (Collision|SetCollisionEnabled %s "NoCollision")\n  (CallFunction|ResetVars)\n""" % (D(\'Pedestal\'), BOARD), 1)'
assert old in f
f = f.replace(old, '  (Collision|SetCollisionEnabled %s "NoCollision")\n  (Rendering|Material|SetMaterial %s 0 "/Game/InnerCanvas/Materials/M_ICLogo_IC.M_ICLogo_IC")\n  (CallFunction|ResetVars)\n""" % (D(\'Pedestal\'), BOARD, D(\'Logo\')), 1)', 1)
old = '        (Class|BPICKeyboardIC|KbShow :self %(kb)s :Spanish %(les)s)\n        (Collision|SetCollisionEnabled (Class|BPICKeyboardIC|GetBoard %(kb)s) "QueryOnly")'
assert f.count(old) >= 1
new = ('        (Class|BPICKeyboardIC|KbShow :self %(kb)s :Spanish %(les)s)\n'
       '        (Class|BPICTutorIC|FrameShow %(tut)s)\n'
       '        (Transformation|SetActorLocationAndRotation %(kb)s (Math|Transform|TransformLocation (Transformation|GetActorTransform %(tut)s) (Math|Vector|MakeVector -1.5 0.0 -4.0)) (Transformation|GetActorRotation %(tut)s) false true)\n'
       '        (for _ky (Class|BPICKeyboardIC|GetKeys %(kb)s)\n'
       '          (Rendering|Material|SetVectorParameterValueonMaterials _ky "Accent" (Math|Vector|MakeVector 0.85 0.9 0.88)))\n'
       '        (Collision|SetCollisionEnabled (Class|BPICKeyboardIC|GetBoard %(kb)s) "QueryOnly")')
# reemplazar la ULTIMA aparicion (la del bloque RECORRIDO2, que es la que vale)
i = f.rindex(old)
f = f[:i] + new + f[i + len(old):]
old = "           camrot=CAMROT, kb=D('Kb'), les=D('LangES'), ready=READY, ty=TY_EXPR.replace(NL2, NL8),"
assert old in f
f = f.replace(old, "           camrot=CAMROT, kb=D('Kb'), les=D('LangES'), ready=READY, ty=TY_EXPR.replace(NL2, NL8), tut=D('Tut'),", 1)
io.open('ic_flow2_dsl.py', 'w', encoding='utf-8').write(f)
print('ok')
