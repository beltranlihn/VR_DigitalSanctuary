"""gen_catalogo.py - escribe docs/CATALOGO.md: qué hace cada Blueprint, material, Niagara, MPC y data asset (2026-11-14).

Cruza dos cosas:
  - el grafo de dependencias de los .uasset (tools/unreal/deps.py --plugins, sin abrir Unreal): qué existe y qué proyecto lo usa
    (Obra, Demo, Inner Canvas, experimentos) recorriendo desde sus niveles;
  - tools/unreal/catalogo_desc.json: una frase por asset (ruta -> descripción). Se edita a mano; un asset nuevo sin frase sale
    marcado "⬜ sin descripción" para completarlo al tocarlo.

Uso:  python tools/unreal/gen_catalogo.py
"""
import collections, io, json, os, subprocess, sys, tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
DESC = os.path.join(ROOT, "tools", "unreal", "catalogo_desc.json")
OUT = os.path.join(ROOT, "docs", "CATALOGO.md")
PRE = ("BP_", "BPC_", "WBP_", "ABP_", "BPI_", "M_", "MF_", "MPC_", "NS_", "DA_", "ML_")
TIPO = {"BP": "Blueprint", "BPC": "componente", "WBP": "widget", "ABP": "anim BP", "BPI": "interfaz", "M": "material",
        "MF": "función de material", "MPC": "parámetros de material", "NS": "Niagara", "DA": "data asset", "ML": "capa de material"}
# los niveles de cada proyecto (raíces del recorrido)
def grupos(d):
    umaps = [k for k in d if os.path.basename(k).startswith(("L_", "Test_"))]
    return collections.OrderedDict([
        ("Obra", ["/Game/SoulCharger/Obra/L_SoulCharger_Obra"]),
        ("Demo", [m for m in umaps if "/SoulCharger/Demo/Maps/" in m]),
        ("Inner Canvas", [m for m in umaps if m.startswith("/Game/InnerCanvas/")]),
        ("experimentos", [m for m in umaps if os.path.basename(m) in ("Test_Thoughts", "Test_Feed", "Test_Focus", "Test_AttractingHang", "Test_Harp")]),
        ("pruebas", [m for m in umaps if os.path.basename(m) in ("Test_QuestCtrl", "Test_Appear", "Test_Results", "L_GhostRec_SC", "Test_DrawPalette")]),
    ])

def cierre(d, roots):
    s, st = set(), list(roots)
    while st:
        x = st.pop()
        if x in s or x not in d: continue
        s.add(x); st.extend(d[x])
    return s

def seccion(k):
    p = k.split("/")
    if p[1] != "Game": return "Plugin " + p[1]
    if p[2] == "SoulCharger": return "SoulCharger/" + p[3]
    return p[2]

def main():
    tmp = tempfile.mkdtemp()
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "unreal", "deps.py"), "--plugins"], cwd=tmp, check=True, capture_output=True)
    d = json.load(open(os.path.join(tmp, "deps.json")))
    desc = json.load(io.open(DESC, encoding="utf-8")) if os.path.exists(DESC) else {}
    G = grupos(d)
    C = {g: cierre(d, r) for g, r in G.items()}
    filas = collections.defaultdict(list)
    sin = 0
    for k in sorted(d):
        n = k.rsplit("/", 1)[1]
        if k.startswith("/PICOOpenXR") or not n.startswith(PRE): continue
        usos = [g for g in G if k in C[g]] or ["— nadie"]
        t = desc.get(k)
        if not t: t = "⬜ sin descripción"; sin += 1
        filas[seccion(k)].append((n, TIPO.get(n.split("_")[0], ""), "/".join(k.split("/")[:-1]), ", ".join(usos), t))
    orden = sorted(filas, key=lambda s: (s.startswith("Plugin"), s not in ("SoulCharger/Obra",), s))
    L = ["# 📚 Catálogo: qué hace cada asset", "",
         "Generado por `python tools/unreal/gen_catalogo.py` (no editar a mano: las frases están en `tools/unreal/catalogo_desc.json`).",
         "Una fila por Blueprint, material maestro, función de material, MPC, Niagara y data asset del proyecto y de los plugins `SC_*`.",
         "**Usado por** = qué proyecto lo alcanza desde sus niveles (Obra, Demo, Inner Canvas, experimentos, niveles de prueba).",
         "Las instancias de material (`MI_*`), texturas, mallas y sonidos no van: se entienden por su material o su BP.",
         "Mapa general: [`MAPA-DEL-PROYECTO.md`](MAPA-DEL-PROYECTO.md) · detalle de cada BP: `.claude/skills/unreal-vr/blueprints/`.", "",
         "Índice: " + " · ".join("[%s](#%s)" % (s, s.lower().replace("/", "").replace(" ", "-").replace("_", "")) for s in orden), ""]
    for s in orden:
        L += ["## " + s, "", "| Asset | Tipo | Usado por | Qué hace |", "|---|---|---|---|"]
        for n, tipo, carpeta, usos, t in filas[s]:
            L.append("| `%s` <br><sub>%s</sub> | %s | %s | %s |" % (n, carpeta, tipo, usos, t.replace("|", "\\|")))
        L.append("")
    io.open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(L))
    print("CATALOGO.md: %d assets en %d secciones, %d sin descripción" % (sum(len(v) for v in filas.values()), len(filas), sin))

if __name__ == "__main__":
    main()
