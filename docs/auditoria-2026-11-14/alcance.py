"""alcance.py - con deps.json (deps.py --plugins): que usa cada grupo de niveles y que no usa nadie."""
import json, os, re, glob, collections, sys
REPO = r"C:\Users\beltr\Desktop\Alma Digital Studio\Projects\VR Unreal"
d = json.load(open("deps.json"))
# los .umap reales
umaps = set()
for p in glob.glob(os.path.join(REPO, "VR_Test", "Content", "**", "*.umap"), recursive=True):
    rel = os.path.relpath(p, os.path.join(REPO, "VR_Test", "Content")).replace(os.sep, "/")[:-5]
    umaps.add("/Game/" + rel)
G = collections.OrderedDict()
G["OBRA"] = ["/Game/SoulCharger/Obra/L_SoulCharger_Obra"]
G["DEMO"] = [m for m in umaps if "/Demo/Maps/" in m]
G["INNERCANVAS"] = [m for m in umaps if m.startswith("/Game/InnerCanvas/")]
EXP = ["Test_AttractingHang", "Test_Harp", "Test_Feed", "Test_Focus", "Test_Thoughts"]
G["EXPERIMENTOS"] = [m for m in umaps if os.path.basename(m) in EXP]
G["UTILES"] = [m for m in umaps if os.path.basename(m) in ("Test_DrawPalette", "Test_Appear", "L_GhostRec_SC", "Test_QuestCtrl", "Test_Results")]
# raices de la config
cfg = set()
pat = re.compile(r"/(?:Game|SC_[A-Za-z]+|PICOOpenXR)/[A-Za-z0-9_/\-\.]+")
for ini in glob.glob(os.path.join(REPO, "VR_Test", "Config", "*.ini")):
    for m in pat.findall(open(ini, encoding="utf-8", errors="ignore").read()):
        x = m.split(".")[0].rstrip("/")
        if x in d: cfg.add(x)
G["CONFIG"] = sorted(cfg)

def clos(roots):
    seen, st = set(), list(roots)
    while st:
        x = st.pop()
        if x in seen or x not in d: continue
        seen.add(x); st.extend(d[x])
    return seen
C = {g: clos(r) for g, r in G.items()}
# cada celda de la Obra por separado (para saber que es de cada etapa)
cov = collections.defaultdict(set)
for g, s in C.items():
    for x in s: cov[x].add(g)
alive = set(cov)
print("paquetes:", len(d), " usados por algun grupo:", len(alive))
for g in G: print("  %-12s raices %2d  alcanza %4d" % (g, len(G[g]), len(C[g])))
print("niveles sin grupo:", sorted(m for m in umaps if not any(m in r for r in G.values())))
print("celdas que alcanza la Obra:", sorted(m for m in umaps if m in C["OBRA"]))
orph = sorted(set(d) - alive)
def carpeta(k, n=4): return "/".join(k.split("/")[:n])
print("\n== HUERFANOS (no los alcanza ningun nivel ni la config): %d ==" % len(orph))
for c, n in collections.Counter(carpeta(k) for k in orph).most_common(): print("  %4d  %s" % (n, c))
only = collections.defaultdict(list)
for x, gs in cov.items():
    if len(gs) == 1: only[next(iter(gs))].append(x)
print("\n== SOLO de un grupo ==")
for g in G:
    cs = collections.Counter(carpeta(k) for k in only[g])
    print("  %s: %d  -> %s" % (g, len(only[g]), ", ".join("%s(%d)" % (c, n) for c, n in cs.most_common(8))))
json.dump({"orph": orph, "cov": {k: sorted(v) for k, v in cov.items()}, "groups": G}, open("alcance.json", "w"), indent=0)
