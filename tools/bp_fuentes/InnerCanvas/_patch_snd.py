# parche 2026-11-13 (Beltran, sonidos de Desktop/Sonidos, mezclados en Ableton: NO tocar volumenes en Unreal):
# - paleta: PaletteIn al entrar (la del marco y la de la mano), sin sonido al irse, sin sonido las dos chicas de las cartas
#   -> BP_ICTutor_IC.PalSndAll(Mute) recorre las BP_DrawPalette_SC vivas y pone AppearSound/VanishSound en la paleta y en su
#      BPC_AppearLuz_SC (si ya existe). La llaman TutBegin, CardsSpawn (Mute) y el flujo (HandChosen y el arranque del dibujo).
# - teclado: HoverTecla al pasar el laser a otra tecla (HoverSound, PH1/PH2 = la tecla anterior de cada laser)
import io, shutil


def sub(path, pairs):
    s = io.open(path, encoding='utf-8').read()
    for old, new in pairs:
        assert s.count(old) == 1, (path, old[:90])
        s = s.replace(old, new, 1)
    io.open(path, 'w', encoding='utf-8').write(s)


for f in ('ic_tutor2_dsl.py', 'ic_kb_dsl.py', 'ic_flow2_dsl.py', 'ic_spec.py', 'ic_spec_tutor.py'):
    shutil.copyfile(f, f + '.bak_snd')

SND_PAL = '/Game/InnerCanvas/Audio/SFX/SND_IC_PaletteIn.SND_IC_PaletteIn'
SND_HOV = '/Game/InnerCanvas/Audio/SFX/SND_IC_HoverTecla.SND_IC_HoverTecla'
SND_SEL = '/Game/InnerCanvas/Audio/SFX/SND_IC_SelectTecla.SND_IC_SelectTecla'

# ---- tutor
sub('ic_tutor2_dsl.py', [
    ("  (Class|BPDrawPaletteSC|ApplyState _pal)\n",
     "  (Class|BPDrawPaletteSC|ApplyState _pal)\n  (CallFunction|PalSndAll :Mute false)\n"),
    ("  %(rplace)s\n  (Development|PrintString \"TUTOR: cartas\" :bPrintToScreen false))\n",
     "  %(rplace)s\n  (CallFunction|PalSndAll :Mute true)\n  (Development|PrintString \"TUTOR: cartas\" :bPrintToScreen false))\n"),
    ("ORDER = ['Kill', ", "ORDER = ['PalSndAll', 'Kill', "),
])
t = io.open('ic_tutor2_dsl.py', encoding='utf-8').read()
i = t.index('ORDER = [')
blk = '''# PalSndAll(Mute): sonido de la aparicion de TODAS las paletas vivas (Beltran 11-13): entrar = PalInSound (PaletteIn); irse = nada;
# Mute = sin sonido al entrar (las dos chicas de las cartas). Se escribe en la paleta (la copia a su BPC_AppearLuz_SC al crearlo) y,
# si el componente ya existe, tambien en el.
CODES['PalSndAll'] = \'\'\'(fn PalSndAll (Mute)
  (for _p (Actor|GetAllActorsOfClass "%(palc)s")
    (Class|BPDrawPaletteSC|SetVanishSound :self _p)
    (if Mute
      (Class|BPDrawPaletteSC|SetAppearSound :self _p)
      (else
        (Class|BPDrawPaletteSC|SetAppearSound :self _p :AppearSound %(snd)s)))
    (bind _lz (Utilities|Casting|CastToBPC_AppearLuz_SC (Actor|GetComponentbyClass _p "/SC_Base/Blueprints/BPC_AppearLuz_SC.BPC_AppearLuz_SC_C")))
    (Utilities|IsValid _lz
      (:"Is Valid"
        (Class|BPCAppearLuzSC|SetVanishSound :self _lz)
        (if Mute
          (Class|BPCAppearLuzSC|SetAppearSound :self _lz)
          (else
            (Class|BPCAppearLuzSC|SetAppearSound :self _lz :AppearSound %(snd)s)))))))
\'\'\' % dict(palc=PALC, snd=D('PalInSound'))

'''
t = t[:i] + blk + t[i:]
io.open('ic_tutor2_dsl.py', 'w', encoding='utf-8').write(t)

# ---- teclado
sub('ic_kb_dsl.py', [
    ("  (CallFunction|KbHit :R %(rig2)s)\n  %(h2)s\n",
     "  (CallFunction|KbHit :R %(rig2)s)\n  %(h2)s\n"
     "  (if (and (>= %(gh1)s 0) (and (!= %(gh1)s %(ph1)s) (not %(done)s)))\n    (Audio|PlaySound2D %(hsnd)s))\n"
     "  (if (and (>= %(gh2)s 0) (and (!= %(gh2)s %(ph2)s) (and (!= %(gh2)s %(gh1)s) (not %(done)s))))\n    (Audio|PlaySound2D %(hsnd)s))\n"
     "  %(sph1)s\n  %(sph2)s\n"),
    ("gc1=D('Clk1'), gc2=D('Clk2'), done=D('Done'))",
     "gc1=D('Clk1'), gc2=D('Clk2'), done=D('Done'),\n           ph1=D('PH1'), ph2=D('PH2'), hsnd=D('HoverSound'), sph1=DS('PH1', D('H1')), sph2=DS('PH2', D('H2')))"),
])

# ---- flujo: la paleta de la mano (la crea StageIntro o el arranque del dibujo)
sub('ic_flow2_dsl.py', [
    ("  (Class|BPTBDirectorNC|StageIntro %(tb)s)\n  (Class|BPICVoiceIC|SetSubs :self %(voice)s :bSubs true)\n",
     "  (Class|BPTBDirectorNC|StageIntro %(tb)s)\n  (Class|BPICTutorIC|PalSndAll :self %(tut)s :Mute false)\n  (Class|BPICVoiceIC|SetSubs :self %(voice)s :bSubs true)\n"),
    ("\"\"\" % dict(voice=D('Voice'), r=D('Right'), rig=D('Rig'), rig2=D('Rig2'), tb=D('TB'), pick=TUT(",
     "\"\"\" % dict(voice=D('Voice'), tut=D('Tut'), r=D('Right'), rig=D('Rig'), rig2=D('Rig2'), tb=D('TB'), pick=TUT("),
    ("        (Class|BPTBDirectorNC|StageBegin %(tb)s)\n        (Class|BPTBDirectorNC|SetInkUsed :self %(tb)s :InkUsed 0.0)\n        %(ink1)s\n        %(tt0)s\n        %(req0)s\n        (Class|BPICLinkIC|LinkClear %(link)s)\n        (if %(synth)s\n          (Class|BPTBDirectorNC|DbgSynth %(tb)s))\n        %(p9)s\n        %(g9)s))))\n\"\"\" % dict(ph=D('Phase'), pt=D('PT'), c2=D('Clk2')",
     "        (Class|BPTBDirectorNC|StageBegin %(tb)s)\n        (Class|BPICTutorIC|PalSndAll :self %(tut)s :Mute false)\n        (Class|BPTBDirectorNC|SetInkUsed :self %(tb)s :InkUsed 0.0)\n        %(ink1)s\n        %(tt0)s\n        %(req0)s\n        (Class|BPICLinkIC|LinkClear %(link)s)\n        (if %(synth)s\n          (Class|BPTBDirectorNC|DbgSynth %(tb)s))\n        %(p9)s\n        %(g9)s))))\n\"\"\" % dict(ph=D('Phase'), pt=D('PT'), c2=D('Clk2')"),
])

# ---- specs (para que una reconstruccion no los pierda)
sub('ic_spec.py', [
    ("v('PromptES', S, ed=True), v('ClickSound', SND, ed=True)],",
     "v('PromptES', S, ed=True), v('ClickSound', SND, ed=True),\n          v('PH1', I), v('PH2', I), v('HoverSound', SND, ed=True)],"),
    ("         'ClickSound': '/Game/SoulCharger/Demo/Audio/Mix/SND_Demo_Select.SND_Demo_Select'}))",
     "         'ClickSound': '%s', 'HoverSound': '%s', 'PH1': -1, 'PH2': -1}))" % (SND_SEL, SND_HOV)),
])
sub('ic_spec_tutor.py', [
    ("v('HintH', F, ed=True), v('WarnH', F, ed=True), v('WarnD', F, ed=True), v('LabB', VEC, ed=True, arr=True)],",
     "v('HintH', F, ed=True), v('WarnH', F, ed=True), v('WarnD', F, ed=True), v('LabB', VEC, ed=True, arr=True),\n          v('PalInSound', O('/Script/Engine.SoundBase'), ed=True)],"),
    ("('Kill', [('A', O('/Script/Engine.Actor'), True)]), ('FrameShow', [])],",
     "('Kill', [('A', O('/Script/Engine.Actor'), True)]), ('FrameShow', []), ('PalSndAll', [('Mute', B, True)])],"),
    ("'HintH': 3.6, 'WarnH': 3.0, 'WarnD': 55.0, 'MSign': 1.0,",
     "'HintH': 3.6, 'WarnH': 3.0, 'WarnD': 55.0, 'MSign': 1.0, 'PalInSound': '%s'," % SND_PAL),
])
print('ok')
