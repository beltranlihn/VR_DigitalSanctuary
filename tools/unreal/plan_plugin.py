"""plan_plugin.py - arma el mapa de traslado de una mecánica a su plugin de contenido (VR_Test/Plugins/SC_<X>).

La mecánica ya está ordenada por tipo en /Game/SoulCharger/Mechanics/<X>/<Tipo>/ (reordenamiento del 2026-10-02),
así que el destino es /SC_<X>/<Tipo>/<Asset>. Qué va al plugin = el CIERRE de dependencias de las semillas (los BPs
del sistema: motor + herramienta) dentro de la carpeta de la mecánica, más los extras por patrón. Lo demás (la etapa:
el BP que habla con la Obra, el entorno, el nivel de test) se queda en el proyecto.

Uso:
  python tools/unreal/plan_plugin.py SC_Breath /Game/SoulCharger/Mechanics/Breath \
      --semillas BP_BreathRig_SC BP_BreathBlob_SC BP_Pacer_SC --extra "Audio/SND_Pacer*"
Escribe Saved/ClaudeScripts/Obra/dump/plugin_<x>.json (para tools/unreal/mcp/mover_job.py). Con --registrar (solo
DESPUES de mover) escribe además tools/unreal/plugin_<x>_<fecha>.json, el registro versionado del que
limpiar_con_editor_cerrado.py y actualizar_rutas_docs.py toman las rutas viejas: un plan sin ejecutar ahí sería peligroso. Muestra qué se queda en el proyecto y qué de lo que se queda usa el plugin.
Después: crear el plugin (PluginToolset.CreatePlugin, plantilla "Content Only"), mover, re-guardar niveles,
python tools/unreal/verificar_plugins.py y la prueba de humo. Detalle: gotcha 586.
"""
import argparse, fnmatch, json, os, subprocess, sys, tempfile, time

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
CONTENT = os.path.join(ROOT, "VR_Test", "Content")
DUMP = os.path.join(ROOT, "VR_Test", "Saved", "ClaudeScripts", "Obra", "dump")


def deps_actuales():
    tmp = tempfile.mkdtemp()
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "unreal", "deps.py")], cwd=tmp, check=True,
                   stdout=subprocess.DEVNULL)
    return json.load(open(os.path.join(tmp, "deps.json")))


def existe(pkg):
    base = os.path.join(CONTENT, *pkg[len("/Game/"):].split("/"))
    for ext in (".uasset", ".umap"):
        p = base + ext
        if os.path.exists(p):
            # los redirectores que quedaron bloqueados en disco no cuentan
            return not (os.path.getsize(p) < 20000 and b"ObjectRedirector" in open(p, "rb").read())
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plugin")
    ap.add_argument("carpeta")
    ap.add_argument("--semillas", nargs="+", required=True, help="nombres de los BPs del sistema")
    ap.add_argument("--extra", nargs="*", default=[], help="patrones relativos a la carpeta (Audio/SND_Pacer*)")
    ap.add_argument("--registrar", action="store_true",
                    help="escribir tambien tools/unreal/plugin_<x>_<fecha>.json. Solo DESPUES de mover: ese archivo es el "
                         "registro de lo que se movio y limpiar_con_editor_cerrado.py toma de ahi las rutas viejas")
    a = ap.parse_args()
    car = a.carpeta.replace("\\", "/")
    if "/Game/" in car and not car.startswith("/Game/"):
        car = car[car.index("/Game/"):]          # Git Bash convierte /Game/X en C:/Program Files/Git/Game/X
    car = car.rstrip("/") + "/"
    a.carpeta = car.rstrip("/")
    deps = deps_actuales()
    mios = [k for k in deps if k.startswith(car) and existe(k)]
    semillas = [k for k in mios if k.split("/")[-1] in a.semillas and "/Maps/" not in k]
    falt = set(a.semillas) - {k.split("/")[-1] for k in semillas}
    if falt:
        print("no encontré: " + ", ".join(sorted(falt)))
        raise SystemExit(1)
    s, st = set(), list(semillas)
    while st:
        x = st.pop()
        if x in s:
            continue
        s.add(x)
        st += [y for y in deps.get(x, []) if y.startswith(car) and existe(y)]
    for pat in a.extra:
        s |= {k for k in mios if fnmatch.fnmatch(k[len(car):], pat)}
    plug = sorted(s)
    if any("/Maps/" in k for k in plug):
        print("un nivel cayó en el cierre (no se mueven niveles a un plugin): " + ", ".join(k for k in plug if "/Maps/" in k))
        raise SystemExit(1)
    raiz = "/" + a.plugin + "/"
    mover = [[k, raiz + k[len(car):]] for k in plug]
    fuera = sorted({y for k in plug for y in deps.get(k, []) if not y.startswith(car)})
    quedan = sorted(k for k in mios if k not in s)
    print("al plugin %s: %d assets" % (a.plugin, len(mover)))
    for o, n in mover:
        print("   " + n)
    print("lo que usa de afuera de la carpeta (tiene que ser XR de Epic o un plugin SC_*):")
    for y in fuera:
        print("   " + y)
    print("se quedan en el proyecto (la etapa): %d" % len(quedan))
    for k in quedan:
        h = [x.split("/")[-1] for x in deps.get(k, []) if x in s]
        print("   %s%s" % (k[len(car):], ("   -> usa " + ", ".join(h)) if h else ""))
    nombre = a.plugin.lower().replace("sc_", "")
    doc = {"generado": time.strftime("%Y-%m-%d"), "plugin": a.plugin, "carpeta": a.carpeta,
           "semillas": a.semillas, "extra": a.extra, "mover": mover}
    os.makedirs(DUMP, exist_ok=True)
    json.dump({"mover": mover}, open(os.path.join(DUMP, "plugin_%s.json" % nombre), "w"))
    print("plan para mover_job.py: Saved/ClaudeScripts/Obra/dump/plugin_%s.json" % nombre)
    if a.registrar:
        reg = os.path.join(ROOT, "tools", "unreal", "plugin_%s_%s.json" % (nombre, doc["generado"]))
        json.dump(doc, open(reg, "w", encoding="utf-8"), indent=0, ensure_ascii=False)
        print("registro: tools/unreal/plugin_%s_%s.json" % (nombre, doc["generado"]))
    else:
        print("(sin --registrar: no queda registro versionado; correr de nuevo con --registrar despues de mover)")


if __name__ == "__main__":
    main()
