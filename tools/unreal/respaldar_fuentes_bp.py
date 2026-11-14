"""respaldar_fuentes_bp.py - copia al repo las fuentes de los Blueprints escritos por script (2026-11-14).

Los grafos que se escriben con el DSL (el director de Inner Canvas, la demo, el Hall, el arpa, Focus, Thoughts...) se generan
desde scripts .py/.dsl que viven en VR_Test/Saved/ClaudeScripts/<tema>/. Tienen que vivir ahí: AssetTools.read_file del editor
solo lee de /Game, del Content de un plugin o de Saved/. Pero Saved/ está ignorado por git, así que esas fuentes no tenían respaldo.

Este script espeja solo las fuentes (.py y .dsl, sin dumps, capturas ni __pycache__) en tools/bp_fuentes/<tema>/, con la
misma estructura. Correrlo antes de cada commit (lo hace la mini-skill /commit). Nunca borra nada en Saved/.

Uso:  python tools/unreal/respaldar_fuentes_bp.py          (copia lo nuevo o cambiado y resume)
      python tools/unreal/respaldar_fuentes_bp.py --seco   (solo muestra qué copiaría)
"""
import os, shutil, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
SRC = os.path.join(ROOT, "VR_Test", "Saved", "ClaudeScripts")
DST = os.path.join(ROOT, "tools", "bp_fuentes")
EXT = (".py", ".dsl")
SALTAR = {"__pycache__", "dump"}


def main():
    seco = "--seco" in sys.argv
    nuevos = cambiados = iguales = 0
    for dp, dn, fn in os.walk(SRC):
        dn[:] = [d for d in dn if d not in SALTAR]
        for f in fn:
            if not f.endswith(EXT):
                continue
            s = os.path.join(dp, f)
            d = os.path.join(DST, os.path.relpath(s, SRC))
            if os.path.exists(d):
                if os.path.getsize(d) == os.path.getsize(s) and open(d, "rb").read() == open(s, "rb").read():
                    iguales += 1
                    continue
                cambiados += 1
            else:
                nuevos += 1
            if not seco:
                os.makedirs(os.path.dirname(d), exist_ok=True)
                shutil.copy2(s, d)
    print("fuentes de BPs -> tools/bp_fuentes: %d nuevas, %d cambiadas, %d iguales%s"
          % (nuevos, cambiados, iguales, " (en seco: nada copiado)" if seco else ""))


if __name__ == "__main__":
    main()
