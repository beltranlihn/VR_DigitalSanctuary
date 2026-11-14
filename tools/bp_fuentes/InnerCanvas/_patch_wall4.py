# parche 2026-11-13 (Beltran: "finalmente seran 4 gafas en simultaneo"): la pantalla del PC muestra 4 visores (1-4) en 2 x 2, celdas
# apaisadas (en 4K 1920 x 988, "mas scope"); RT de cada celda = su tamano en 4K. Los visores 5-8 se siguen recibiendo pero no se
# dibujan (sus camaras quedan sin capturar cada cuadro: valor del nivel L_InnerCanvas_Wall).
import io, shutil


def sub(path, pairs, bak):
    shutil.copyfile(path, path + bak)
    s = io.open(path, encoding='utf-8').read()
    for old, new in pairs:
        assert s.count(old) == 1, (path, old[:80])
        s = s.replace(old, new, 1)
    io.open(path, 'w', encoding='utf-8').write(s)


sub('ic_hud_dsl.py', [
    ("  (bind _cw (/ W 4.0))\n", "  (bind _cw (/ W 2.0))\n"),
    ("  (for _i (range 8)\n", "  (for _i (range 4)\n"),
    ("(bind _x (* (Math|Conversions|ToFloat(Integer) (- _i (select (< _i 4) 0 4))) _cw))",
     "(bind _x (* (Math|Conversions|ToFloat(Integer) (- _i (select (< _i 2) 0 2))) _cw))"),
    ("(bind _y (+ _bh (select (< _i 4) 0.0 _ch)))", "(bind _y (+ _bh (select (< _i 2) 0.0 _ch)))"),
    ("(bind _sx (+ (* W 0.37) (* (Math|Conversions|ToFloat(Integer) _i) (* W 0.077))))",
     "(bind _sx (+ (* W 0.55) (* (Math|Conversions|ToFloat(Integer) _i) (* W 0.11))))"),
    ("# Los 8 cuadros van debajo: 4 x 2 de W/4 x (H - banner)/2 (en 4K 960 x 988 = el RT de BP_ICWall_IC).",
     "# 11-13: 4 visores (1-4) en 2 x 2 de W/2 x (H - banner)/2 (en 4K 1920 x 988 = el RT de BP_ICWall_IC); la senal de los 4 arriba."),
], '.bak_wall4')
sub('ic_wall_dsl.py', [("rw=1920, rh=1976", "rw=1920, rh=988")], '.bak_wall4')
print('ok')
