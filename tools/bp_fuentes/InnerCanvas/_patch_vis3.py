# parche 2026-11-13 (Beltran): paneles 1 m mas lejos (Dist 210, valor de instancia), teclado casi pegado al panel, logo centrado en el
# panel del teclado, el panel se va al elegir el nombre (fundido), el circulo del centro sobre la niebla del final.
import io
NL = chr(10)

t = io.open('ic_tutor2_dsl.py', encoding='utf-8').read()
logo = "  (Transformation|SetRelativeLocation %(logo)s (Math|Vector|MakeVector (- %(fx)s 0.5) (* -0.206 %(fw)s) (+ %(fz)s (* 0.376 %(fh)s))) false true)"
assert t.count(logo) == 2
i = t.index(logo, t.index("CODES['FrameShow']"))
t = t[:i] + logo.replace("(* -0.206 %(fw)s)", "0.0") + t[i + len(logo):]
old = """  (if (and %(fo)s (not %(run)s))
    %(fff)s
    %(ffl)s
    %(ffv)s
    %(ffw)s)
"""
assert old in t
new = """  (if (and %(fo)s (not %(run)s))
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
"""
t = t.replace(old, new, 1)
old = " fo=D('FrameOn'),"
assert old in t
t = t.replace(old, " fo=D('FrameOn'), fks=DS('FrameK', '_fo'), fkd=DS('FrameK', '(Math|Interpolation|FInterpTo %s 0.0 Dt 8.0)' % D('FrameK')),"
                   " gff=SP(D('Frame'), 'Fade', D('FrameK')), gfl=SP(D('Logo'), 'Reveal', D('FrameK')),"
                   " gfv=VIS(D('Frame'), '(> %s 0.01)' % D('FrameK')), gfw=VIS(D('Logo'), '(> %s 0.01)' % D('FrameK')),", 1)
io.open('ic_tutor2_dsl.py', 'w', encoding='utf-8').write(t)

f = io.open('ic_flow2_dsl.py', encoding='utf-8').read()
# teclado casi pegado al panel (el panel esta en FrameX = 7; el teclado a 5)
old = "(Math|Vector|MakeVector -1.5 0.0 -6.0)) (Transformation|GetActorRotation %(tut)s) false true)"
assert f.count(old) == 1
f = f.replace(old, "(Math|Vector|MakeVector 5.0 0.0 -6.0)) (Transformation|GetActorRotation %(tut)s) false true)", 1)
# al elegir el nombre: se va el panel (el teclado ya se va solo) y aparece el HUD
old = "        %(c2t)s\n        %(hoff)s\n        (Collision|SetCollisionEnabled (Class|BPICKeyboardIC|GetBoard %(kb)s) \"NoCollision\")"
assert f.count(old) == 1
f = f.replace(old, "        %(c2t)s\n        %(hoff)s\n        (Class|BPICTutorIC|SetFrameOn :self %(tut)s :FrameOn false)\n        (Collision|SetCollisionEnabled (Class|BPICKeyboardIC|GetBoard %(kb)s) \"NoCollision\")", 1)
old = "           kb=D('Kb'), ink1=DS('Ink01', '1.0'), sgo=SAY('VoGo'), phud=P('IC: HUD con el nombre, 5:00 y la tinta'), ready=READY, g5=GOPH(5),"
assert old in f
f = f.replace(old, "           kb=D('Kb'), tut=D('Tut'), ink1=DS('Ink01', '1.0'), sgo=SAY('VoGo'), phud=P('IC: HUD con el nombre, 5:00 y la tinta'), ready=READY, g5=GOPH(5),", 1)
# el circulo del centro se ve sobre la niebla (el velo tiene 32600, el titulo 32700); al final se va el borde y queda el circulo
old = "  (Rendering|Material|SetMaterial %s 0 \"/Game/InnerCanvas/Materials/M_ICLogo_IC.M_ICLogo_IC\")\n  (CallFunction|ResetVars)\n\"\"\" % (D('Pedestal'), BOARD, D('Logo')), 1)"
assert old in f
f = f.replace(old, "  (Rendering|Material|SetMaterial %s 0 \"/Game/InnerCanvas/Materials/M_ICLogo_IC.M_ICLogo_IC\")\n  (Rendering|SetTranslucentSortPriority (Class|BPICSpaceIC|GetFloor %s) 32650)\n  (CallFunction|ResetVars)\n\"\"\" % (D('Pedestal'), BOARD, D('Logo'), D('Space')), 1)", 1)
old = "  %(woff)s\n  (Development|PrintString \"IC: fin: niebla blanca y el titulo en su lugar; espera la orden del PC\" :bPrintToScreen false)"
assert old in f
f = f.replace(old, "  %(woff)s\n  (Class|BPICSpaceIC|SpaceReset %(space)s)\n  (Development|PrintString \"IC: fin: niebla blanca y el titulo en su lugar; espera la orden del PC\" :bPrintToScreen false)", 1)
old = "\"\"\" % dict(say=SAY('VoThanks'), woff=TUT('WarnSet', ' :On false'), g11=GOPH(11),"
assert old in f
f = f.replace(old, "\"\"\" % dict(say=SAY('VoThanks'), woff=TUT('WarnSet', ' :On false'), space=D('Space'), g11=GOPH(11),", 1)
io.open('ic_flow2_dsl.py', 'w', encoding='utf-8').write(f)
print('ok')
