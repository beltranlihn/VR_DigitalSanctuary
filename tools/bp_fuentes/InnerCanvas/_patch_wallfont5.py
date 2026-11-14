# parche 2026-11-13 ~10:35: el juego corria SIN reconocer la escala de Windows (TV 4K al 300 %): Windows le daba 1280 x 720 y lo
# estiraba x3 (de ahi el pixelado). Con __COMPAT_LAYER=HighDpiAware en los .bat corre en 4K real; las fuentes 4K se calibran ahora
# para que cada texto se vea del mismo tamano que se veia (el juego 1080 dibujado en 720 y estirado x3): 4K = 3 x el de 1080 de antes.
import io, re, shutil
P = 'ic_hud_dsl.py'
shutil.copyfile(P, P + '.bak_font5')
s = io.open(P, encoding='utf-8').read()
HI = {36: 54, 11: 21, 15: 24, 12: 21, 19: 30, 22: 33}     # titulo, alma, visor/esperando, ok, numero, nombre/reloj (4K)
LO = {18: 27, 7: 11, 8: 12, 10: 15, 11: 17}               # el juego para 1080 = la mitad
out, mode, n = [], None, 0
for line in s.split('\n'):
    t = line.strip()
    if t == '(if _hi':
        mode = 'hi'
    elif t == '(else':
        mode = 'lo'
    elif '(HUD|DrawText ' in line and mode:
        m = re.search(r'F_ICW(\d+)_IC\.F_ICW(\d+)_IC', line)
        k = int(m.group(1))
        nk = (HI if mode == 'hi' else LO)[k]
        line = line.replace(m.group(0), 'F_ICW%d_IC.F_ICW%d_IC' % (nk, nk))
        n += 1
        mode = None
    out.append(line)
s = '\n'.join(out)
assert n == 16, n
io.open(P, 'w', encoding='utf-8').write(s)
print('ok', n, sorted(set(int(x) for x in re.findall(r'F_ICW(\d+)_IC\.', s))))
