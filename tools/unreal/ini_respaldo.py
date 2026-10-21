"""ini_respaldo.py - los empaquetadores cambian DefaultEngine.ini solo mientras corre UAT (2026-10-19).

Antes restauraban el texto leido al arrancar: si una corrida moria antes de su `finally` (timeout de la herramienta, ventana
cerrada), el ini quedaba con los cambios temporales y la corrida siguiente los "restauraba" como si fueran los buenos
(paso el 19-10: GameDefaultMap de la demo + shaders ES31 en Windows en el ini compartido).
Ahora, antes de escribir, se copia el ini a VR_Test/Saved/DefaultEngine.ini.antes_de_empaquetar; al terminar se restaura y
se borra la copia. Si al arrancar la copia sigue ahi, la corrida anterior se corto: se restaura esa copia primero.
"""
import os, shutil

def _resp(ini):
    return os.path.join(os.path.dirname(os.path.dirname(ini)), "Saved", "DefaultEngine.ini.antes_de_empaquetar")

def ini_limpio(ini):
    """el texto verdadero del ini (si una corrida anterior se corto, primero lo devuelve a como estaba)"""
    r = _resp(ini)
    if os.path.exists(r):
        shutil.copyfile(r, ini)
        os.remove(r)
        print("DefaultEngine.ini: una corrida anterior se corto con el ini cambiado; restaurado desde " + r)
    return open(ini, encoding="utf-8").read()

def escribir_temporal(ini, texto):
    shutil.copyfile(ini, _resp(ini))
    open(ini, "w", encoding="utf-8").write(texto)

def restaurar(ini, texto0):
    open(ini, "w", encoding="utf-8").write(texto0)
    r = _resp(ini)
    if os.path.exists(r):
        os.remove(r)
