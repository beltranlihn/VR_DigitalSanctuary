"""verificar_plugins.py - comprueba que los plugins de mecánicas (VR_Test/Plugins/SC_*) sigan siendo portables.

Lee las rutas que guarda cada .uasset del plugin (sin abrir Unreal) y avisa si alguno apunta:
  - a /Game/SoulCharger/  -> PROHIBIDO: ata el plugin a la obra (el plugin ya no se puede llevar a otro proyecto);
  - a otro plugin SC_* que no está declarado en su .uplugin;
  - a /Game/XRFramework/  -> permitido solo en los plugins que lo documentan (SC_Draw), se informa.
Las rutas de origen de importación (carpetas sin asset, p. ej. /Game/Drawing/TB/Icons) se ignoran.

Uso: python tools/unreal/verificar_plugins.py      (sale con 1 si hay algo prohibido)
"""
import json, os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
PLUG = os.path.join(ROOT, "VR_Test", "Plugins")
CONTENT = os.path.join(ROOT, "VR_Test", "Content")
PAT = re.compile(rb"/(?:Game|SC_[A-Za-z]+)/[A-Za-z0-9_/\-]+")
XR_OK = {"SC_Draw"}


def es_asset(ruta):
    """True si la ruta nombra un asset que existe (en Content o en un plugin)."""
    if ruta.startswith("/Game/"):
        base = os.path.join(CONTENT, *ruta[len("/Game/"):].split("/"))
    else:
        nombre = ruta.split("/")[1]
        base = os.path.join(PLUG, nombre, "Content", *ruta.split("/")[2:])
    return os.path.exists(base + ".uasset") or os.path.exists(base + ".umap")


def main():
    malo = 0
    for p in sorted(os.listdir(PLUG)):
        if not p.startswith("SC_"):
            continue
        up = json.load(open(os.path.join(PLUG, p, p + ".uplugin"), encoding="utf-8"))
        deps = {d["Name"] for d in up.get("Plugins", [])}
        prob, xr, otros = set(), set(), set()
        n = 0
        for dp, dn, fn in os.walk(os.path.join(PLUG, p, "Content")):
            for f in fn:
                if not f.endswith((".uasset", ".umap")):
                    continue
                n += 1
                for m in PAT.findall(open(os.path.join(dp, f), "rb").read()):
                    r = m.decode("ascii", "ignore")
                    if r.startswith("/" + p + "/") or not es_asset(r):
                        continue
                    if r.startswith("/Game/SoulCharger/"):
                        prob.add((r, f))
                    elif r.startswith("/Game/XRFramework/"):
                        xr.add(r)
                    elif r.startswith("/SC_") and r.split("/")[1] not in deps:
                        otros.add((r, f))
        estado = "OK" if not prob and not otros and (not xr or p in XR_OK) else "MAL"
        print("%-8s %3d assets  %s" % (p, n, estado))
        for r, f in sorted(prob):
            print("   PROHIBIDO  %s  <- %s" % (r, f))
        for r, f in sorted(otros):
            print("   SIN DECLARAR  %s  <- %s (agregar la dependencia en el .uplugin)" % (r, f))
        for r in sorted(xr):
            print("   XRFramework  %s%s" % (r, "" if p in XR_OK else "  (no documentado)"))
        malo += estado == "MAL"
    sys.exit(1 if malo else 0)


if __name__ == "__main__":
    main()
