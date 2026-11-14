# edit_menu_heart_1020.py - 2026-10-20: tercer cuadro del menu (RECOGNIZING -> L_Demo_Heart), Choice 3. Sobre menu_dsl.py.
import shutil
p = 'menu_dsl.py'
shutil.copy(p, 'menu_dsl_backup_1020h.py')
s = open(p, encoding='utf-8').read()


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (s.count(a), a[:100])
    s = s.replace(a, b)


# Boot: BtnC (tag demo_c) y su escala de hover
rep('''  %(s3)s
  %(rig)s''', '''  %(s3)s
  %(s4)s
  %(rig)s''')
rep('''           s3=ZS('BtnB', '(Utilities|Array|Get(acopy) (Actor|GetAllActorsOfClassWithTag "%s" "demo_b") 0)' % BTN),''',
    '''           s3=ZS('BtnB', '(Utilities|Array|Get(acopy) (Actor|GetAllActorsOfClassWithTag "%s" "demo_b") 0)' % BTN),
           s4=DS('BtnC', '(Utilities|Array|Get(acopy) (Actor|GetAllActorsOfClassWithTag "%s" "demo_c") 0)' % BTN),''')
rep('''  %(kb)s
  %(p)s)''', '''  %(kb)s
  %(kc)s
  %(p)s)''')
rep("ka=DS('KA', '1.0'), kb=DS('KB', '1.0'),", "ka=DS('KA', '1.0'), kb=DS('KB', '1.0'), kc=DS('KC', '1.0'),")
# Place: el tercer cuadro sube/baja igual y guarda su escala
rep('''  (Transformation|SetActorLocation %(bb)s (+ (Transformation|GetActorLocation %(bb)s) _off) false true)''',
    '''  (Transformation|SetActorLocation %(bb)s (+ (Transformation|GetActorLocation %(bb)s) _off) false true)
  (Transformation|SetActorLocation %(bc)s (+ (Transformation|GetActorLocation %(bc)s) _off) false true)''')
rep('''  %(baseb)s
  (Transformation|SetWorldLocationAndRotation''', '''  %(baseb)s
  %(basec)s
  (Transformation|SetWorldLocationAndRotation''')
rep("baseb=DS('BaseB', '(.x (Transformation|GetActorScale3D %s))' % Z('BtnB')))",
    "baseb=DS('BaseB', '(.x (Transformation|GetActorScale3D %s))' % Z('BtnB')),\n           bc=D('BtnC'), basec=DS('BaseC', '(.x (Transformation|GetActorScale3D %s))' % D('BtnC')))")
# Choose: BACK se lleva tambien el tercero; al elegir, se aprieta el elegido y se van los otros dos
rep('''CODES['Choose'] = \'\'\'(fn Choose (I)
  (bind _btnstart %(bs)s)
  (bind _btna %(ba)s)
  (bind _btnb %(bb)s)''', '''CODES['Choose'] = \'\'\'(fn Choose (I)
  (bind _btnstart %(bs)s)
  (bind _btna %(ba)s)
  (bind _btnb %(bb)s)
  (bind _btnc %(bc)s)''')
rep('''      (Class|BPShareButtonSC|Vanish _btna)
      (Class|BPShareButtonSC|Vanish _btnb)
      %(ph5)s''', '''      (Class|BPShareButtonSC|Vanish _btna)
      (Class|BPShareButtonSC|Vanish _btnb)
      (Class|BPShareButtonSC|Vanish _btnc)
      %(ph5)s''')
rep('''        (Class|BPShareButtonSC|Press (select (== I 1) _btna _btnb))
        (Class|BPShareButtonSC|Vanish (select (== I 1) _btnb _btna))''', '''        (Class|BPShareButtonSC|Press (select (== I 1) _btna (select (== I 3) _btnc _btnb)))
        (Class|BPShareButtonSC|Vanish (select (== I 1) _btnb _btna))
        (Class|BPShareButtonSC|Vanish (select (== I 3) _btnb _btnc))''')
rep("hint=D('Hint'), ph=Z('Phase'), kit=D('Kit'), dst=D('DrawShowTime'),", "hint=D('Hint'), ph=Z('Phase'), kit=D('Kit'), dst=D('DrawShowTime'), bc=D('BtnC'),")
# Pick: el tercer cuadro (indice 3)
rep('''  (bind _btnb %(bb)s)
  (bind _rig %(rig)s)
  (bind _rig2 %(rig2)s)''', '''  (bind _btnb %(bb)s)
  (bind _btnc %(bc)s)
  (bind _rig %(rig)s)
  (bind _rig2 %(rig2)s)''')
rep('''  (bind _ab (and _four (>= %(atb)s 0.999)))''', '''  (bind _ab (and _four (>= %(atb)s 0.999)))
  (bind _ac (and _four (>= %(atc)s 0.999)))''')
rep('''  (bind _b2 (and (== _hit2 _btnb) _ab))''', '''  (bind _b2 (and (== _hit2 _btnb) _ab))
  (bind _c1 (and (== _hit _btnc) _ac))
  (bind _c2 (and (== _hit2 _btnc) _ac))''')
rep('''  (bind _hb (or _b1 _b2))''', '''  (bind _hb (or _b1 _b2))
  (bind _hc (or _c1 _c2))''')
rep('''  (Class|BPShareButtonSC|SetHover _btnb _hb)
  %(hovs)s
  %(hova)s
  %(hovb)s''', '''  (Class|BPShareButtonSC|SetHover _btnb _hb)
  (Class|BPShareButtonSC|SetHover _btnc _hc)
  %(hovs)s
  %(hova)s
  %(hovb)s
  %(hovc)s''')
rep('''      (elif (and _p1 (or _s1 (or _a1 _b1)))
        (CallFunction|Choose :I (select _s1 0 (select _a1 1 2)))''', '''      (elif (and _p1 (or _s1 (or _a1 (or _b1 _c1))))
        (CallFunction|Choose :I (select _s1 0 (select _a1 1 (select _c1 3 2))))''')
rep('''        (elif (and _p2 (or _s2 (or _a2 _b2)))
          (CallFunction|Choose :I (select _s2 0 (select _a2 1 2)))''', '''        (elif (and _p2 (or _s2 (or _a2 (or _b2 _c2))))
          (CallFunction|Choose :I (select _s2 0 (select _a2 1 (select _c2 3 2))))''')
rep("           ats=AT('_btnstart'), ata=AT('_btna'), atb=AT('_btnb'), lp=Z('LastPressN'), lp2=D('LastPressN2'),",
    "           ats=AT('_btnstart'), ata=AT('_btna'), atb=AT('_btnb'), atc=AT('_btnc'), bc=D('BtnC'), lp=Z('LastPressN'), lp2=D('LastPressN2'),")
rep("           hovs=DS('HovS', '_hs'), hova=DS('HovA', '_ha'), hovb=DS('HovB', '_hb'))\n\nCODES['HoverFx']",
    "           hovs=DS('HovS', '_hs'), hova=DS('HovA', '_ha'), hovb=DS('HovB', '_hb'), hovc=DS('HovC', '_hc'))\n\nCODES['HoverFx']")
# HoverFx: el tercero crece con el hover
rep('''  %(kb)s
  (bind _s (* %(bs0)s %(gks)s))''', '''  %(kb)s
  %(kc)s
  (bind _s (* %(bs0)s %(gks)s))''')
rep('''  (Transformation|SetActorScale3D %(bb)s (Math|Vector|MakeVector _b _b _b)))''', '''  (Transformation|SetActorScale3D %(bb)s (Math|Vector|MakeVector _b _b _b))
  (bind _c (* %(bc0)s %(gkc)s))
  (Transformation|SetActorScale3D %(bc)s (Math|Vector|MakeVector _c _c _c)))''')
rep("           bs=Z('BtnStart'), ba=Z('BtnA'), bb=Z('BtnB'))\n\nCODES['TravelStep']",
    "           bs=Z('BtnStart'), ba=Z('BtnA'), bb=Z('BtnB'),\n           kc=DS('KC', '(Math|Interpolation|FInterpTo %s (select %s %s 1.0) Dt 10.0)' % (D('KC'), D('HovC'), D('HoverScale'))),\n           bc0=D('BaseC'), gkc=D('KC'), bc=D('BtnC'))\n\nCODES['TravelStep']")
# MenuTick: aparece el tercero; voz y nivel por eleccion (1 Breath, 2 Draw, 3 Heart)
rep('''        (Class|BPShareButtonSC|Appear %(bb)s)
        %(hpick)s''', '''        (Class|BPShareButtonSC|Appear %(bb)s)
        (Class|BPShareButtonSC|Appear %(bc)s)
        %(hpick)s''')
rep('''(select (== %(choice)s 1) %(vob)s %(vod)s)''', '''(select (== %(choice)s 1) %(vob)s (select (== %(choice)s 3) %(voh)s %(vod)s))''')
rep('''(Game|OpenLevel(byName) (select (== %(choice)s 1) %(la)s %(lb)s))''', '''(Game|OpenLevel(byName) (select (== %(choice)s 1) %(la)s (select (== %(choice)s 3) %(lc)s %(lb)s)))''')
rep("''' % dict(vodelay=D('VoDelay'),", "''' % dict(bc=D('BtnC'), voh=D('VoHeart'), lc=D('LevelC'), vodelay=D('VoDelay'),")
s = s.replace("# el reloj del HUD del menu = DrawShowTime.", "# el reloj del HUD del menu = DrawShowTime. Tercer cuadro RECOGNIZING (tag demo_c, Choice 3 -> LevelC = L_Demo_Heart, VoHeart).")
open(p, 'w', encoding='utf-8').write(s)
print('menu ok')
