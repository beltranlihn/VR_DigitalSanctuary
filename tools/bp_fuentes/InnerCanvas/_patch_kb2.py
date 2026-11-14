# parche 2026-11-12 noche: teclado al 90 % y 2 cm mas abajo dentro del marco (el campo tocaba el logo); subtitulos apagados mientras
# se ve el marco (se encimaban abajo) y de vuelta al empezar a dibujar.
import io
p = 'ic_flow2_dsl.py'
f = io.open(p, encoding='utf-8').read()
old = "(Math|Vector|MakeVector -1.5 0.0 -4.0)) (Transformation|GetActorRotation %(tut)s) false true)\n"
assert f.count(old) == 1
f = f.replace(old, "(Math|Vector|MakeVector -1.5 0.0 -6.0)) (Transformation|GetActorRotation %(tut)s) false true)\n"
              "        (Transformation|SetActorScale3D %(kb)s (Math|Vector|MakeVector 0.9 0.9 0.9))\n"
              "        (Class|BPICVoiceIC|SetSubs :self %(voice)s :bSubs false)\n", 1)
old = "           camrot=CAMROT, kb=D('Kb'), les=D('LangES'), ready=READY, ty=TY_EXPR.replace(NL2, NL8), tut=D('Tut'),"
assert old in f
f = f.replace(old, "           camrot=CAMROT, kb=D('Kb'), les=D('LangES'), ready=READY, ty=TY_EXPR.replace(NL2, NL8), tut=D('Tut'), voice=D('Voice'),", 1)
# TutAct :8 (cartas) ya no prende los subtitulos; HandChosen si
old = "    (:8\n      (Class|BPICVoiceIC|SetSubs :self %(voice)s :bSubs true)\n      %(cards)s"
assert old in f
f = f.replace(old, "    (:8\n      %(cards)s", 1)
old = "  (Class|BPTBDirectorNC|StageIntro %(tb)s)\n  (CallFunction|FPawnHand :Right true :Vis false)"
assert old in f
f = f.replace(old, "  (Class|BPTBDirectorNC|StageIntro %(tb)s)\n  (Class|BPICVoiceIC|SetSubs :self %(voice)s :bSubs true)\n  (CallFunction|FPawnHand :Right true :Vis false)", 1)
old = "\"\"\" % dict(r=D('Right'), rig=D('Rig'), rig2=D('Rig2'), tb=D('TB'), pick=TUT('TutPick'"
assert old in f
f = f.replace(old, "\"\"\" % dict(voice=D('Voice'), r=D('Right'), rig=D('Rig'), rig2=D('Rig2'), tb=D('TB'), pick=TUT('TutPick'", 1)
io.open(p, 'w', encoding='utf-8').write(f)
print('ok')
