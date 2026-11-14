# parche 2026-11-13 (Beltran): hover de las cartas de mano (los mismos de los botones de idioma: entrar / salir; mudo despues de
# elegir) y volumen del hover de teclas (HoverVol 0,5). El pad a 0,7 es un valor de instancia (BP_ICAmb_IC_C_0.Volume).
import io, shutil


def sub(path, pairs):
    s = io.open(path, encoding='utf-8').read()
    for old, new in pairs:
        assert s.count(old) == 1, (path, old[:90])
        s = s.replace(old, new, 1)
    io.open(path, 'w', encoding='utf-8').write(s)


for f in ('ic_tutor2_dsl.py', 'ic_kb_dsl.py', 'ic_spec.py', 'ic_spec_tutor.py'):
    shutil.copyfile(f, f + '.bak_snd2')

HON = '/Game/SoulCharger/Demo/Audio/Mix/SND_Demo_HoverOn.SND_Demo_HoverOn'
HOUT = '/Game/SoulCharger/Demo/Audio/Mix/SND_Demo_HoverOut.SND_Demo_HoverOut'

# ---- tutor: hover de las cartas (Hov lo escribe el flujo en PickHand: -1 nada, 0 zurda, 1 diestra)
sub('ic_tutor2_dsl.py', [
    ("      %(chl)s\n      %(chr)s\n      (bind _ms ",
     "      %(chl)s\n      %(chr)s\n"
     "      (if (and (< %(pt)s 0.0) (!= %(hov)s %(phv)s))\n"
     "        (if (>= %(phv)s 0)\n          (Audio|PlaySound2D %(cos)s))\n"
     "        (if (>= %(hov)s 0)\n          (Audio|PlaySound2D %(chs)s))\n"
     "        %(sphv)s)\n"
     "      (bind _ms "),
    ("pr=D('PickR'), hov=D('Hov'),",
     "pr=D('PickR'), hov=D('Hov'), phv=D('PrevHov'), cos=D('CardOutSound'), chs=D('CardHovSound'), sphv=DS('PrevHov', D('Hov')),"),
    ("''' % dict(on=DS('CardsOn', 'true'), ml=_mini('L')",
     "''' % dict(on=DS('CardsOn', 'true') + NL2 + DS('PrevHov', '-1'), ml=_mini('L')"),
])

# ---- teclado: volumen del hover
sub('ic_kb_dsl.py', [
    ("  (if (and (>= %(gh1)s 0) (and (!= %(gh1)s %(ph1)s) (not %(done)s)))\n    (Audio|PlaySound2D %(hsnd)s))\n",
     "  (if (and (>= %(gh1)s 0) (and (!= %(gh1)s %(ph1)s) (not %(done)s)))\n    (Audio|PlaySound2D %(hsnd)s :VolumeMultiplier %(hvol)s))\n"),
    ("  (if (and (>= %(gh2)s 0) (and (!= %(gh2)s %(ph2)s) (and (!= %(gh2)s %(gh1)s) (not %(done)s))))\n    (Audio|PlaySound2D %(hsnd)s))\n",
     "  (if (and (>= %(gh2)s 0) (and (!= %(gh2)s %(ph2)s) (and (!= %(gh2)s %(gh1)s) (not %(done)s))))\n    (Audio|PlaySound2D %(hsnd)s :VolumeMultiplier %(hvol)s))\n"),
    ("hsnd=D('HoverSound'),", "hsnd=D('HoverSound'), hvol=D('HoverVol'),"),
])

# ---- specs
sub('ic_spec.py', [
    ("v('PH1', I), v('PH2', I), v('HoverSound', SND, ed=True)],", "v('PH1', I), v('PH2', I), v('HoverSound', SND, ed=True), v('HoverVol', F, ed=True)],"),
    ("'PH1': -1, 'PH2': -1}))", "'PH1': -1, 'PH2': -1, 'HoverVol': 0.5}))"),
])
sub('ic_spec_tutor.py', [
    ("          v('PalInSound', O('/Script/Engine.SoundBase'), ed=True)],",
     "          v('PalInSound', O('/Script/Engine.SoundBase'), ed=True), v('PrevHov', I),\n"
     "          v('CardHovSound', O('/Script/Engine.SoundBase'), ed=True), v('CardOutSound', O('/Script/Engine.SoundBase'), ed=True)],"),
    ("'MSign': 1.0, 'PalInSound':", "'MSign': 1.0, 'PrevHov': -1, 'CardHovSound': '%s', 'CardOutSound': '%s', 'PalInSound':" % (HON, HOUT)),
])
print('ok')
