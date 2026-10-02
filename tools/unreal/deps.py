# deps.py - grafo de dependencias de Content/ leyendo las rutas /Game/ de cada .uasset/.umap (sin abrir Unreal).
# Uso: python tools/unreal/deps.py  -> deps.json en la carpeta actual. Ver docs/AUDITORIA-ESTRUCTURA-2026-10-02.md
import os, re, json, sys
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "VR_Test", "Content")
pat = re.compile(rb"/Game/[A-Za-z0-9_/\-\.]+")
pkgs = {}
for dp, dn, fn in os.walk(ROOT):
    for f in fn:
        if f.endswith(('.uasset', '.umap')):
            p = os.path.join(dp, f)
            rel = os.path.relpath(p, ROOT).replace(os.sep, '/')
            pkg = '/Game/' + rel.rsplit('.', 1)[0]
            pkgs[pkg] = p
# Unreal guarda los FName que terminan en _<numero> partidos (base + numero): "VO_14" queda como "VO" + 14.
# Por eso una ruta base que no es paquete cuenta como referencia a todos sus hermanos base_<N> (conservador).
import collections
numbered = collections.defaultdict(list)
for k in pkgs:
    m = re.match(r"^(.*)_(\d+)$", k)
    if m and not m.group(2).startswith('0') or (m and m.group(2) == '0'):
        numbered[m.group(1)].append(k)
deps = {}
for pkg, p in pkgs.items():
    data = open(p, 'rb').read()
    s = set()
    for m in pat.findall(data):
        x = m.decode('ascii', 'ignore').split('.')[0].rstrip('/')
        if x in pkgs and x != pkg:
            s.add(x)
        elif x in numbered:
            s.update(n for n in numbered[x] if n != pkg)
    deps[pkg] = sorted(s)
json.dump(deps, open('deps.json', 'w'), indent=0)
print(len(pkgs), 'packages')
