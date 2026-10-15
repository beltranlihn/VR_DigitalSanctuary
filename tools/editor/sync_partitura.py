"""sync_partitura.py - brings the Partitura definition (tools/unreal/partitura_def.py, owned by the director)
into the web editor as obra/unreal/partitura_def.json. Never edit that JSON by hand: change partitura_def.py
(the director does) and run this again.

  python tools/editor/sync_partitura.py

The values here are the ones the asset was CREATED with. The live values of DA_Partitura_Obra come from the
director's export (obra/unreal/partitura.json) when it exists.
"""
import hashlib, json, os, sys, time

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
SRC = os.path.join(ROOT, "tools", "unreal", "partitura_def.py")
OUT = os.path.join(ROOT, "obra", "unreal", "partitura_def.json")
sys.path.insert(0, os.path.dirname(SRC))
from partitura_def import P  # noqa: E402

STAGES = ["Entering", "Recognizing", "Loving", "Attracting", "Surrounding"]
src_bytes = open(SRC, "rb").read()
# the editor is in English: docs and categories come from the web-owned translations (obra/unreal/partitura_def_en.json);
# the director's original text stays next to them as docUnreal / categoryUnreal
EN_PATH = os.path.join(ROOT, "obra", "unreal", "partitura_def_en.json")
EN = json.load(open(EN_PATH, encoding="utf-8")).get("knobs", {}) if os.path.exists(EN_PATH) else {}
knobs, missing = [], []
for (n, t, v, c, d) in P:
    en = EN.get(n, {})
    if not en.get("doc") or not en.get("category"):
        missing.append(n)
    knobs.append({"name": n, "type": t, "initial": v, "category": en.get("category") or c, "doc": en.get("doc") or d,
                  "categoryUnreal": c, "docUnreal": d})
if missing:
    print("no English text yet in obra/unreal/partitura_def_en.json for: " + ", ".join(missing))
doc = {
    "source": "tools/unreal/partitura_def.py",
    "sourceSha1": hashlib.sha1(src_bytes).hexdigest()[:12],
    "synced": time.strftime("%Y-%m-%dT%H:%M:%S"),
    "asset": "/Game/SoulCharger/Obra/Partitura/DA_Partitura_Obra",
    "units": "seconds of the director clock; PT = time inside the current phase, T = stage time (phase 0 jumps T to 9 when Alma enters)",
    "stages": STAGES,
    "knobs": knobs,
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(doc, f, ensure_ascii=False, indent=1)
print("obra/unreal/partitura_def.json: %d knobs (%s @%s)" % (len(knobs), doc["source"], doc["sourceSha1"]))
