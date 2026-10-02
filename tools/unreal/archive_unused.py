"""archive_unused.py - saca de VR_Test/Content los assets que la obra no usa, sin borrarlos.

Mueve cada paquete (.uasset/.umap) de la lista a _Deprecated/<nombre>/Content/<misma ruta>,
fuera del proyecto Unreal (el editor no los carga ni los cocina). Tambien mueve los archivos
sueltos (wav, mp4, fbx) de las carpetas que quedan sin ningun asset.

  python tools/unreal/archive_unused.py --list dead.json --name Content-2026-10-02          # ensayo (no mueve)
  python tools/unreal/archive_unused.py --list dead.json --name Content-2026-10-02 --apply
  python tools/unreal/archive_unused.py --restore Content-2026-10-02 [--only /Game/Ruta]    # devuelve todo o una parte

🔴 Con Unreal CERRADO. Despues de mover: abrir el editor, abrir la Obra, correr smoke_obra.py.
La lista sale del grafo de dependencias (deps.py) desde las raices declaradas en
docs/AUDITORIA-ESTRUCTURA-2026-10-02.md. El git conserva todo en el tag respaldo-pre-reorden-2026-10-02.
"""
import argparse, json, os, shutil, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
CONTENT = os.path.join(ROOT, "VR_Test", "Content")
DEPR = os.path.join(ROOT, "_Deprecated")

def pkg_files(pkg):
    rel = pkg[len("/Game/"):]
    out = []
    for ext in (".uasset", ".umap"):
        p = os.path.join(CONTENT, rel + ext)
        if os.path.exists(p):
            out.append(p)
    return out

def move(src, dst_root, base):
    rel = os.path.relpath(src, base)
    dst = os.path.join(dst_root, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.move(src, dst)
    return rel

def remove_empty_dirs(base):
    n = 0
    for dp, dn, fn in os.walk(base, topdown=False):
        if dp != base and not os.listdir(dp):
            os.rmdir(dp); n += 1
    return n

def archive(lst, name, apply):
    dead = json.load(open(lst, encoding="utf-8"))
    dst_root = os.path.join(DEPR, name, "Content")
    files = []
    for pkg in dead:
        files += pkg_files(pkg)
    # carpetas que quedan sin ningun paquete: se lleva tambien lo suelto (fuentes wav/mp4/fbx)
    moving = set(os.path.normcase(f) for f in files)
    loose = []
    for dp, dn, fn in os.walk(CONTENT):
        pk = [f for f in fn if f.endswith((".uasset", ".umap"))]
        if pk and all(os.path.normcase(os.path.join(dp, f)) in moving for f in pk):
            loose += [os.path.join(dp, f) for f in fn if not f.endswith((".uasset", ".umap"))]
        elif not pk and fn and dp != CONTENT:
            # carpeta sin paquetes (p. ej. Media/): se archiva solo si se pide por la lista de carpetas
            pass
    size = sum(os.path.getsize(f) for f in files + loose)
    print("paquetes: %d archivos, sueltos: %d, total %.1f MB -> %s" % (len(files), len(loose), size / 1e6, dst_root))
    if not apply:
        return
    done = [move(f, dst_root, CONTENT) for f in files + loose]
    n = remove_empty_dirs(CONTENT)
    man = os.path.join(DEPR, name, "MANIFEST.json")
    prev = json.load(open(man, encoding="utf-8")) if os.path.exists(man) else []
    json.dump(sorted(set(prev + done)), open(man, "w", encoding="utf-8"), indent=0)
    print("movidos %d, carpetas vacias quitadas %d, manifiesto %s" % (len(done), n, man))

def archive_dirs(dirs, name, apply):
    dst_root = os.path.join(DEPR, name, "Content")
    files = []
    for d in dirs:
        p = os.path.join(CONTENT, d)
        for dp, dn, fn in os.walk(p):
            files += [os.path.join(dp, f) for f in fn]
    print("carpetas %s: %d archivos" % (dirs, len(files)))
    if apply:
        done = [move(f, dst_root, CONTENT) for f in files]
        remove_empty_dirs(CONTENT)
        man = os.path.join(DEPR, name, "MANIFEST.json")
        prev = json.load(open(man, encoding="utf-8")) if os.path.exists(man) else []
        json.dump(sorted(set(prev + done)), open(man, "w", encoding="utf-8"), indent=0)

def restore(name, only):
    src_root = os.path.join(DEPR, name, "Content")
    n = 0
    for dp, dn, fn in os.walk(src_root):
        for f in fn:
            src = os.path.join(dp, f)
            rel = os.path.relpath(src, src_root)
            game = "/Game/" + rel.replace(os.sep, "/").rsplit(".", 1)[0]
            if only and not game.startswith(only):
                continue
            dst = os.path.join(CONTENT, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(src, dst); n += 1
    remove_empty_dirs(src_root)
    print("restaurados %d archivos" % n)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--list"); ap.add_argument("--name", default="Content-archivo")
    ap.add_argument("--dirs", nargs="*", default=[])
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--restore"); ap.add_argument("--only", default=None)
    a = ap.parse_args()
    if a.restore:
        restore(a.restore, a.only); sys.exit(0)
    if a.list:
        archive(a.list, a.name, a.apply)
    if a.dirs:
        archive_dirs(a.dirs, a.name, a.apply)
