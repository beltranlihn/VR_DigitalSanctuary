# parche 2026-11-12 noche: colisiones que tapaban el laser de los botones de idioma
import io
BS = chr(92)

p = 'ic_flow2_dsl.py'
s = io.open(p, encoding='utf-8').read()
anchor = "    # FlowTut: igual, con 9 pasos"
assert anchor in s
add = '''    # Colisiones que tapaban el laser de los botones de idioma (VR Preview de Beltran, 11-12 noche): el plano del teclado (Board) queda
    # delante a la altura de las manos aunque el teclado no se vea -> solo con el teclado a la vista; el mando del pedestal y la mesa
    # del sistema de dibujo (ocultos, BlockAllDynamic) -> sin colision.
    BOARD = '(Class|BPICKeyboardIC|GetBoard %s)' % D('Kb')
    CODES['FBoot'] = CODES['FBoot'].replace('  (CallFunction|ResetVars)BSn', """  (Collision|SetActorEnableCollision %s false)
  (Collision|SetActorEnableCollision (Actor|GetActorOfClass "/SC_Draw/Blueprints/BP_TBTable.BP_TBTable_C") false)
  (Collision|SetCollisionEnabled %s "NoCollision")
  (CallFunction|ResetVars)
""" % (D('Pedestal'), BOARD), 1)
    assert 'SetActorEnableCollision' in CODES['FBoot']
    CODES['ICReset'] = CODES['ICReset'].replace('  (CallFunction|ResetVars)BSn', '  (Collision|SetCollisionEnabled %s "NoCollision")BSn  (CallFunction|ResetVars)BSn' % BOARD, 1)
    assert 'GetBoard' in CODES['ICReset']

'''.replace('BSn', BS + 'n')
s = s.replace(anchor, add + anchor, 1)
old = '        (Class|BPICKeyboardIC|KbShow :self %(kb)s :Spanish %(les)s)\n        %(s1)s'
assert old in s
s = s.replace(old, '        (Class|BPICKeyboardIC|KbShow :self %(kb)s :Spanish %(les)s)\n        (Collision|SetCollisionEnabled (Class|BPICKeyboardIC|GetBoard %(kb)s) "QueryOnly")\n        %(s1)s', 1)
old2 = '        %(c2t)s\n        %(hoff)s\n        (Class|BPICHudKitIC|HudInstall %(kit)s)'
assert old2 in s
s = s.replace(old2, '        %(c2t)s\n        %(hoff)s\n        (Collision|SetCollisionEnabled (Class|BPICKeyboardIC|GetBoard %(kb)s) "NoCollision")\n        (Class|BPICHudKitIC|HudInstall %(kit)s)', 1)
s = s.replace("'FlowTick', 'FPlaceBtns'):", "'FlowTick', 'FPlaceBtns', 'FBoot'):", 1)
io.open(p, 'w', encoding='utf-8').write(s)

p = 'ic_tutor2_dsl.py'
s = io.open(p, encoding='utf-8').read()
for old, new in (
        ("  %(spal)s\n  (Class|BPDrawPaletteSC|SetAppearDelay :self _pal :AppearDelay 0.0)",
         "  %(spal)s\n  (Collision|SetActorEnableCollision _pal false)\n  (Class|BPDrawPaletteSC|SetAppearDelay :self _pal :AppearDelay 0.0)"),
        ("  %(spal)s\n  (Class|BPDrawPaletteSC|SetAppearDelay :self _p%(s)s :AppearDelay 0.0)",
         "  %(spal)s\n  (Collision|SetActorEnableCollision _p%(s)s false)\n  (Class|BPDrawPaletteSC|SetAppearDelay :self _p%(s)s :AppearDelay 0.0)"),
        ("  %(sctl)s\n  (Class|BPQuestCtrlSC|SetLeft :self _c%(s)s :bLeft %(left)s)",
         "  %(sctl)s\n  (Collision|SetActorEnableCollision _c%(s)s false)\n  (Class|BPQuestCtrlSC|SetLeft :self _c%(s)s :bLeft %(left)s)")):
    assert old in s, old[:60]
    s = s.replace(old, new, 1)
io.open(p, 'w', encoding='utf-8').write(s)
print('ok')
