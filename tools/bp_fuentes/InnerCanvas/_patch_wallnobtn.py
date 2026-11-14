# parche 2026-11-13 (Beltran): la pantalla del PC SIN los botones RESET / REINICIAR (el reinicio desde las gafas, los dos grips 5 s,
# funciona perfecto). Mas espacio para los dibujos: fuera las 16 zonas de clic, los dos botones de cada celda; la franja de arriba
# de cada celda (numero + reloj) baja de 52 a 40 px de 1080; sin cursor del mouse. OnBtn queda pero ya no se llama.
import io, re, shutil
P = 'ic_hud_dsl.py'
shutil.copyfile(P, P + '.bak_nobtn')
s = io.open(P, encoding='utf-8').read()
n0 = s.count('(HUD|AddHitBox ')
assert n0 == 16, n0
s = re.sub(r'  \(HUD\|AddHitBox [^\n]*\n', '', s)
for old in [
    "    (bind _now2 (Utilities|Time|GetGameTimeInSeconds))\n",
    "    (bind _arm1 (and (== %(ac)s _i) (and (== %(am)s 1) (< (- _now2 %(at)s) 3.0))))\n",
    "    (bind _arm2 (and (== %(ac)s _i) (and (== %(am)s 2) (< (- _now2 %(at)s) 3.0))))\n",
]:
    assert s.count(old) == 1, old[:60]
    s = s.replace(old, '', 1)
lines = s.split('\n')
keep = [l for l in lines if not (('_arm1' in l or '_arm2' in l) and ('DrawRect' in l or 'DrawText' in l))]
assert len(lines) - len(keep) == 4, len(lines) - len(keep)
s = '\n'.join(keep)
old = ":ScreenW (- _cw (* 6.0 _u)) :ScreenH (* 52.0 _u))"
assert s.count(old) == 1
s = s.replace(old, ":ScreenW (- _cw (* 6.0 _u)) :ScreenH (* 40.0 _u))", 1)
old = "  (Class|PlayerController|SetShowMouseCursor :self (HUD|GetOwningPlayerController) :bShowMouseCursor true)\n  (Class|PlayerController|SetEnableClickEvents :self (HUD|GetOwningPlayerController) :bEnableClickEvents true)\n"
assert s.count(old) == 1
s = s.replace(old, "  (Class|PlayerController|SetShowMouseCursor :self (HUD|GetOwningPlayerController) :bShowMouseCursor false)\n  (Class|PlayerController|SetEnableClickEvents :self (HUD|GetOwningPlayerController) :bEnableClickEvents false)\n", 1)
s = s.replace("# Arriba un banner de 92 px: INNER CANVAS y la senal de cada visor",
              "# (11-13: sin botones RESET/REINICIAR ni zonas de clic; franja de cada celda 40 px)\n# Arriba un banner de 92 px: INNER CANVAS y la senal de cada visor", 1)
assert '_arm' not in s.split("CODES['DrawCells']")[1].split("CODES['OnBtn']")[0].split("''' % dict")[0], 'quedo un _arm en DrawCells'
assert 'AddHitBox' not in s
io.open(P, 'w', encoding='utf-8').write(s)
print('ok')
