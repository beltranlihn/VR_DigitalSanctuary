# parche 2026-11-13 (Beltran): volumen del trigger del teclado (ClickVol 0,5). Hover de teclas 0,2 y pad 0,5 son valores de perilla.
import io, shutil


def sub(path, pairs):
    s = io.open(path, encoding='utf-8').read()
    for old, new in pairs:
        assert s.count(old) == 1, (path, old[:90])
        s = s.replace(old, new, 1)
    io.open(path, 'w', encoding='utf-8').write(s)


for f in ('ic_kb_dsl.py', 'ic_spec.py'):
    shutil.copyfile(f, f + '.bak_snd3')
sub('ic_kb_dsl.py', [
    ("  (Utilities|Array|SetArrayElem %(hov)s I 2.0)\n  (Audio|PlaySound2D %(snd)s)\n",
     "  (Utilities|Array|SetArrayElem %(hov)s I 2.0)\n  (Audio|PlaySound2D %(snd)s :VolumeMultiplier %(cvol)s)\n"),
    ("''' % dict(nm=D('NameStr'), hov=D('Hov'), snd=D('ClickSound'), max=D('MaxLen'),",
     "''' % dict(nm=D('NameStr'), hov=D('Hov'), snd=D('ClickSound'), cvol=D('ClickVol'), max=D('MaxLen'),"),
])
sub('ic_spec.py', [
    ("v('HoverSound', SND, ed=True), v('HoverVol', F, ed=True)],", "v('HoverSound', SND, ed=True), v('HoverVol', F, ed=True), v('ClickVol', F, ed=True)],"),
    ("'HoverVol': 0.5}))", "'HoverVol': 0.2, 'ClickVol': 0.5}))"),
])
print('ok')
