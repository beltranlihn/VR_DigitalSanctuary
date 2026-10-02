"""partitura_export.py - publica los valores vivos de DA_Partitura_Obra para el editor web de la obra.

Paso 1 (con Unreal abierto, desde Claude): correr tools/unreal/mcp/partitura_export_job.py con el MCP
        (execute_tool_script). Escribe VR_Test/Saved/ClaudeScripts/Obra/dump/partitura_live.json.
Paso 2: python tools/unreal/partitura_export.py
        -> obra/unreal/partitura.json  {exportado, hash, asset, valores}
        -> obra/unreal/perillas.json   (si existe el volcado de perillas: Saved/ClaudeScripts/Obra/dump/perillas.json)
El editor web NUNCA escribe .uasset: sus cambios van a obra/unreal/partitura_propuesta.json y una sesion con el
editor los aplica al DA (y corre la prueba de humo).
"""
import hashlib, json, os, time

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
DUMP = os.path.join(ROOT, "VR_Test", "Saved", "ClaudeScripts", "Obra", "dump")
OUT = os.path.join(ROOT, "obra", "unreal")

def main():
    os.makedirs(OUT, exist_ok=True)
    src = json.load(open(os.path.join(DUMP, "partitura_live.json"), encoding="utf-8"))
    vals = src["valores"]
    h = hashlib.sha1(json.dumps(vals, sort_keys=True).encode("utf-8")).hexdigest()[:12]
    doc = {"exportado": time.strftime("%Y-%m-%dT%H:%M:%S"), "hash": h, "asset": src["asset"], "valores": vals}
    json.dump(doc, open(os.path.join(OUT, "partitura.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("obra/unreal/partitura.json: %d perillas, hash %s" % (len(vals), h))
    pp = os.path.join(DUMP, "perillas.json")
    if os.path.exists(pp):
        per = json.load(open(pp, encoding="utf-8"))
        per.pop("log", None)
        out = {"exportado": time.strftime("%Y-%m-%dT%H:%M:%S"), "nota": "variables de cada BP central: [nombre, categoria, valor en el CDO (truncado)]", "bps": per}
        json.dump(out, open(os.path.join(OUT, "perillas.json"), "w", encoding="utf-8"), indent=0, ensure_ascii=False)
        print("obra/unreal/perillas.json: %d Blueprints" % len(per))

if __name__ == "__main__":
    main()
