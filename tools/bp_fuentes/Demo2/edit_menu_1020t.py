# edit_menu_1020t.py - 2026-10-20 (tarde, Beltran probo el menu). Sobre menu_dsl.py (respaldo menu_dsl_backup_1020t.py).
# 1) El viaje nunca frena: acelera y sigue a la misma velocidad (la de antes) mientras todo se va a negro y cambia el nivel.
# 2) Mas aire entre las voces: cada paso espera VoGap s de silencio (QuietT = tiempo desde que la voz se callo).
#    El cierre a negro dura 3,5 s (antes 2,5) y el nivel se abre a los 4 s.
# 3) Las instrucciones de boton ("apunta y aprieta el gatillo") salen como SUBTITULO (BP_DemoVoice_SC.ShowHint), no como texto
#    flotando en el espacio. Ids HINT_START / HINT_PICK (sus palabras estan en los subtitulos de la voz).
import shutil
p = 'menu_dsl.py'
shutil.copy(p, 'menu_dsl_backup_1020t.py')
s = open(p, encoding='utf-8').read()


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (s.count(a), a[:120])
    s = s.replace(a, b)


# --- 3) pistas como subtitulo
rep('''HINT = lambda txt: ('(Rendering|Components|TextRender|SetText %s (Utilities|Text|ToText(String) %s))\\n'
                    '        (Rendering|SetVisibility %s true)') % (D('Hint'), txt, D('Hint'))''',
    '''HINT = lambda hid: '(Class|BPDemoVoiceSC|ShowHint :self %s :Id "%s")' % (D('Voice'), hid)''')
rep("hstart=HINT(D('HintStart')), hpick=HINT(D('HintPick')),", "hstart=HINT('HINT_START'), hpick=HINT('HINT_PICK'),")
rep('''  (bind _btnc %(bc)s)
  (Rendering|SetVisibility %(hint)s false)''', '''  (bind _btnc %(bc)s)
  (Class|BPDemoVoiceSC|HideHint %(voice)s)''')
rep("''' % dict(bs=Z('BtnStart'), ba=Z('BtnA'), bb=Z('BtnB'), hint=D('Hint'), ph=Z('Phase'), kit=D('Kit'), dst=D('DrawShowTime'), bc=D('BtnC'),",
    "''' % dict(bs=Z('BtnStart'), ba=Z('BtnA'), bb=Z('BtnB'), hint=D('Hint'), voice=D('Voice'), ph=Z('Phase'), kit=D('Kit'), dst=D('DrawShowTime'), bc=D('BtnC'),")

# --- 1) el viaje no frena
rep('''  (bind _t (Math|Float|Min(Float) %(tt)s _T))
  (bind _v (/ %(L)s (Math|Float|Max(Float) (- _T (* 0.5 (+ _a _b))) 0.1)))
  (bind _d (select (< _t _a) (* (* 0.5 (/ _v _a)) (* _t _t)) (select (< _t (- _T _b)) (+ (* 0.5 (* _v _a)) (* _v (- _t _a))) (- %(L)s (* (* 0.5 (/ _v _b)) (* (- _T _t) (- _T _t)))))))''',
    '''  (bind _t %(tt)s)
  (bind _v (/ %(L)s (Math|Float|Max(Float) (- _T (* 0.5 (+ _a _b))) 0.1)))
  (bind _d (select (< _t _a) (* (* 0.5 (/ _v _a)) (* _t _t)) (+ (* 0.5 (* _v _a)) (* _v (- _t _a)))))''')

# --- 2) el cierre a negro, mas lento
rep("  (bind _close (Math|Float|FInterpEaseInOut 0.0 1.0 (Math|Float|MapRangeClamped %(pt)s 0.0 2.5 0.0 1.0) 2.0))",
    "  (bind _close (Math|Float|FInterpEaseInOut 0.0 1.0 (Math|Float|MapRangeClamped %(pt)s 0.0 3.5 0.0 1.0) 2.0))")

# --- 2) silencio entre voces
rep('''  %(rtp)s
  %(ptp)s
  (CallFunction|VeilFx)''', '''  %(rtp)s
  %(ptp)s
  %(qtp)s
  (CallFunction|VeilFx)''')
rep('''        (elif (and %(said)s (and (>= _pt 2.0) (not %(speak)s)))
          (Class|BPDemoHudKitSC|HudInstall %(kit)s)''', '''        (elif (and %(said)s (and (>= _pt 2.0) (>= %(qt)s %(gap)s)))
          (Class|BPDemoHudKitSC|HudInstall %(kit)s)''')
rep('''      (if (and (not %(said)s) (>= _pt 2.6))
        %(said1)s
        (Class|BPDemoVoiceSC|Say :self %(voice)s :Clip %(vom)s)
        (elif (and %(said)s (and (>= _pt 3.6) (not %(speak)s)))''', '''      (if (and (not %(said)s) (>= _pt 4.0))
        %(said1)s
        (Class|BPDemoVoiceSC|Say :self %(voice)s :Clip %(vom)s)
        (elif (and %(said)s (and (>= _pt 5.0) (>= %(qt)s %(gap)s)))''')
rep('''    (:9
      (if (and (>= _pt 1.0) (not %(speak)s))''', '''    (:9
      (if (and (>= _pt 1.0) (>= %(qt)s %(gap)s))''')
rep('''    (:10
      (if (>= _pt 3.0)''', '''    (:10
      (if (>= _pt 4.0)''')
rep("''' % dict(bc=D('BtnC'), voh=D('VoHeart'), lc=D('LevelC'), vodelay=D('VoDelay'),",
    "''' % dict(qt=D('QuietT'), gap=D('VoGap'), qtp=DS('QuietT', '(select %s 0.0 (+ %s _dt))' % (SPEAK, D('QuietT'))),\n"
    "           bc=D('BtnC'), voh=D('VoHeart'), lc=D('LevelC'), vodelay=D('VoDelay'),")
s = s.replace("# (FogOff: degrada a negro en su FadeOut) y la bienvenida espera VoDelay s.",
              "# (FogOff: degrada a negro en su FadeOut) y la bienvenida espera VoDelay s.\n"
              "# 2026-10-20 tarde: el viaje no frena nunca (sigue mientras todo se va a negro), VoGap s de silencio entre voces (QuietT) y las\n"
              "# instrucciones de boton como subtitulo (BP_DemoVoice_SC.ShowHint / HideHint, ids HINT_START y HINT_PICK).")
open(p, 'w', encoding='utf-8').write(s)
print('menu ok')
