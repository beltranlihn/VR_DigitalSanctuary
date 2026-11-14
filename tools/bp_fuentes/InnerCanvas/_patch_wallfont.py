# parche 2026-11-13 (Beltran, foto del TV 4K): los textos chicos de la pantalla del PC se veian rotos. A 4K miden 16-32 px y salian de
# la fuente de 64 px reducida 2-4 veces (el Canvas no tiene mips: se pierden trazos). Cada texto usa ahora la fuente de su tamano,
# dibujada ~1:1 en 4K: F_ICWall_IC 64 (titulo), F_ICWallM_IC 32 (numero, nombre, reloj), F_ICWallS_IC 18 (el resto).
import io, shutil
P = 'ic_hud_dsl.py'
shutil.copyfile(P, P + '.bak_font')
s = io.open(P, encoding='utf-8').read()
pairs = [
    ("WFONT = '/Game/InnerCanvas/UI/F_ICWall_IC.F_ICWall_IC'\n",
     "WFONT = '/Game/InnerCanvas/UI/F_ICWall_IC.F_ICWall_IC'\n"
     "MFONT = '/Game/InnerCanvas/UI/F_ICWallM_IC.F_ICWallM_IC'   # 32 px\n"
     "SFONT = '/Game/InnerCanvas/UI/F_ICWallS_IC.F_ICWallS_IC'   # 18 px\n"),
    ("  (bind _f (* _u 0.140625))\n",
     "  (bind _f (* _u 0.140625))\n  (bind _fm (* _u 0.28125))\n  (bind _fs (* _u 0.5))\n"),
    (':Font "%(font)s" :Scale (* 0.9 _f) :bScalePosition false)', ':Font "%(sfont)s" :Scale (* 0.9 _fs) :bScalePosition false)'),
    (':Font "%(font)s" :Scale (* 1.15 _f) :bScalePosition false)', ':Font "%(sfont)s" :Scale (* 1.15 _fs) :bScalePosition false)'),
    (':Font "%(font)s" :Scale (* 1.0 _f) :bScalePosition false)', ':Font "%(sfont)s" :Scale (* 1.0 _fs) :bScalePosition false)'),
    (':Font "%(font)s" :Scale (* 1.2 _f) :bScalePosition false)', ':Font "%(sfont)s" :Scale (* 1.2 _fs) :bScalePosition false)'),
    (':Font "%(font)s" :Scale (* %(fs)s _f) :bScalePosition false)', ':Font "%(mfont)s" :Scale (* %(fs)s _fm) :bScalePosition false)'),
    ("num=D('NumColor'), font=WFONT,", "num=D('NumColor'), font=WFONT, mfont=MFONT, sfont=SFONT,"),
]
for old, new in pairs:
    assert s.count(old) == 1, old[:70]
    s = s.replace(old, new, 1)
# los dos botones (0,95) y el nombre y el reloj (FS2) aparecen dos veces cada uno
for old, new in [(':Font "%(font)s" :Scale (* 0.95 _f) :bScalePosition false)', ':Font "%(sfont)s" :Scale (* 0.95 _fs) :bScalePosition false)'),
                 (':Font "%(font)s" :Scale (* %(fs2)s _f) :bScalePosition false)', ':Font "%(mfont)s" :Scale (* %(fs2)s _fm) :bScalePosition false)')]:
    assert s.count(old) == 2, old[:70]
    s = s.replace(old, new)
assert s.count(':Font "%(font)s"') == 1, 'solo el titulo con la de 64'
io.open(P, 'w', encoding='utf-8').write(s)
print('ok')
