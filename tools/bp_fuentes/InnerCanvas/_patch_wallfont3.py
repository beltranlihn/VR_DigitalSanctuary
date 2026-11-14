# parche 2026-11-13 (Beltran: "se siguen viendo pixelados, como una textura muy chica"): el Canvas dibuja las letras de una fuente
# Runtime SIN filtrar (copia el texel mas cercano): con escala != 1 salen dientes y trazos que faltan; con escala 1 salen limpias
# ("Lucia", a 1,01, era el unico texto nitido). Cada texto va ahora a :Scale 1.0 con una fuente rasterizada a SU tamano en pixeles
# (F_ICW<n>_IC, LegacyFontSize n) y en posicion entera. Dos juegos: H >= 1600 (4K) y el resto (1080), mismo diseno que antes.
import io, re, shutil
P = 'ic_hud_dsl.py'
# (respaldo ya hecho en .bak_font2)
s = io.open(P, encoding='utf-8').read()
F = lambda n: '/Game/InnerCanvas/UI/F_ICW%d_IC.F_ICW%d_IC' % (n, n)
# tamano en pixeles (4K, 1080) segun la escala que tenia cada texto
# medidos 11-13 contra la captura vieja (el raster de LegacyFontSize n sale ~1,45x mas grande que lo estimado)
SIZES = {'(* 3.0 _f)': (36, 18), '(* 0.9 _fs)': (11, 7), '(* 1.15 _fs)': (15, 8), '(* 1.0 _fs)': (12, 7),
         '(* 1.2 _fs)': (15, 8), '(* %(fs)s _fm)': (19, 10), '(* %(fs2)s _fm)': (22, 11)}
RND = lambda x: '(Math|Conversions|ToFloat(Integer) (Math|Float|Truncate (+ %s 0.5)))' % x


def val(line, key):
    i = line.index(':' + key + ' ') + len(key) + 2
    if line[i] != '(':
        j = line.index(' ', i)
        return i, j
    d = 0
    for j in range(i, len(line)):
        d += {'(': 1, ')': -1}.get(line[j], 0)
        if d == 0:
            return i, j + 1


def setv(line, key, new):
    i, j = val(line, key)
    return line[:i] + new + line[j:]


out, used = [], set()
for line in s.split('\n'):
    if '(HUD|DrawText ' not in line:
        out.append(line)
        continue
    i, j = val(line, 'Scale')
    sc = line[i:j]
    hi, lo = SIZES[sc]
    used.update([hi, lo])
    base = line
    for k in ('ScreenX', 'ScreenY'):
        a, b = val(base, k)
        base = base[:a] + RND(base[a:b]) + base[b:]
    base = setv(base, 'Scale', '1.0')
    ind = base[:len(base) - len(base.lstrip())]
    body = base.strip()
    fa, fb = val(body, 'Font')
    l4 = body[:fa] + '"%s"' % F(hi) + body[fb:]
    l1 = body[:fa] + '"%s"' % F(lo) + body[fb:]
    out += [ind + '(if _hi', ind + '  ' + l4, ind + '  (else', ind + '    ' + l1 + '))']
s = '\n'.join(out)
old = "  (bind _u (/ H 1080.0))\n"
assert s.count(old) == 1
s = s.replace(old, old + "  (bind _hi (>= H 1600.0))\n", 1)
s = s.replace("# DrawCells: todo en pixeles de 1080 escalados por _u = H / 1080 (en 4K el texto y las barras se ven igual que en 1080).",
              "# DrawCells: todo en pixeles de 1080 escalados por _u = H / 1080 (en 4K el texto y las barras se ven igual que en 1080).\n"
              "# Textos (11-13): :Scale 1.0 y fuente F_ICW<n>_IC al tamano justo (el Canvas no filtra las letras); _hi = H >= 1600 (juego 4K).", 1)
io.open(P, 'w', encoding='utf-8').write(s)
io.open('wall_font_sizes.txt', 'w').write(' '.join(str(n) for n in sorted(used)))
print('ok', sorted(used), s.count('(HUD|DrawText '))
