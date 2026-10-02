"""limpiar_con_editor_cerrado.py - el último paso del reordenamiento, con Unreal CERRADO.

Con el editor abierto, los assets movidos y los redirectores borrados salen del registro, pero sus archivos siguen en
disco, bloqueados por el editor. Si se dejan, vuelven a aparecer como carpetas viejas al abrir el proyecto. Este script:
  1. se niega a correr si hay un UnrealEditor abierto;
  2. saca de Content/ todo paquete que sea solo un ObjectRedirector -> _Deprecated/Redirectores-<fecha>/;
  3. saca Content/_Deprecated (lo archivado dentro del editor) -> _Deprecated/Content-<fecha>/ con un manifiesto;
  4. borra las carpetas que quedaron vacías.
Todo queda en _Deprecated/ en la raíz del repo (fuera del proyecto y fuera de git), así que se puede devolver a mano.

Uso:  python tools/unreal/limpiar_con_editor_cerrado.py            (muestra qué haría)
      python tools/unreal/limpiar_con_editor_cerrado.py --aplicar
"""
import argparse, json, os, shutil, subprocess, time

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
CONTENT = os.path.join(ROOT, "VR_Test", "Content")
ARCH = os.path.join(ROOT, "_Deprecated")
PROTEGIDAS = ("Collections", "Developers")


def editor_abierto():
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq UnrealEditor.exe"], capture_output=True, text=True).stdout
        return "UnrealEditor.exe" in out
    except Exception:
        return False


def rutas_viejas():
    """Las rutas que dejaron los traslados (tools/unreal/reorden_*.json y plugin_*.json). Solo ahí puede quedar una sobra:
    un asset real chico que todavía apunte a un redirector también tiene el texto ObjectRedirector, y no se toca."""
    import glob
    viejas = set()
    for f in glob.glob(os.path.join(ROOT, "tools", "unreal", "reorden_contenido_*.json")) +              glob.glob(os.path.join(ROOT, "tools", "unreal", "plugin_*.json")):
        d = json.load(open(f, encoding="utf-8"))
        for o, n in d.get("mover", []) + d.get("archivar", []):
            viejas.add(o)
    return viejas


VIEJAS = None


def es_redirector(p, rel):
    global VIEJAS
    if VIEJAS is None:
        VIEJAS = rutas_viejas()
    if "/Game/" + rel.rsplit(".", 1)[0] not in VIEJAS:
        return False
    if os.path.getsize(p) > 20000:
        return False
    b = open(p, "rb").read()
    return b"ObjectRedirector" in b


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aplicar", action="store_true")
    a = ap.parse_args()
    if editor_abierto():
        print("Hay un Unreal abierto: cerralo primero (los archivos están bloqueados).")
        raise SystemExit(1)
    fecha = time.strftime("%Y-%m-%d")
    red, dep = [], []
    for dp, dn, fn in os.walk(CONTENT):
        rel_dir = os.path.relpath(dp, CONTENT).replace(os.sep, "/")
        if rel_dir.split("/")[0] in PROTEGIDAS:
            continue
        for f in fn:
            if not f.endswith((".uasset", ".umap")):
                continue
            rel = (rel_dir + "/" + f) if rel_dir != "." else f
            if rel.startswith("_Deprecated/"):
                dep.append(rel)
            elif es_redirector(os.path.join(dp, f), rel):
                red.append(rel)
    print("redirectores a sacar: %d" % len(red))
    print("archivados dentro del editor (/Game/_Deprecated) a sacar: %d" % len(dep))
    if not a.aplicar:
        for r in red[:15]:
            print("  R " + r)
        print("(nada movido: correr con --aplicar)")
        return
    man = {"fecha": fecha, "redirectores": [], "archivados": []}
    for rel in red:
        dst = os.path.join(ARCH, "Redirectores-" + fecha, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.move(os.path.join(CONTENT, rel), dst)
        man["redirectores"].append(rel)
    for rel in dep:
        dst = os.path.join(ARCH, "Content-" + fecha + "-editor", rel[len("_Deprecated/"):])
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.move(os.path.join(CONTENT, rel), dst)
        man["archivados"].append("/Game/" + rel.rsplit(".", 1)[0])
    vacias = 0
    for dp, dn, fn in sorted(os.walk(CONTENT), key=lambda t: len(t[0]), reverse=True):
        rel = os.path.relpath(dp, CONTENT).replace(os.sep, "/")
        if rel == "." or rel.split("/")[0] in PROTEGIDAS:
            continue
        if not os.listdir(dp):
            os.rmdir(dp)
            vacias += 1
    os.makedirs(ARCH, exist_ok=True)
    json.dump(man, open(os.path.join(ARCH, "MANIFEST-limpieza-%s.json" % fecha), "w", encoding="utf-8"), indent=1)
    print("listo: %d redirectores y %d archivados fuera del proyecto, %d carpetas vacías quitadas" % (len(red), len(dep), vacias))


if __name__ == "__main__":
    main()
