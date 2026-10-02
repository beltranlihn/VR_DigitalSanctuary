"""gen_perillas_doc.py - escribe docs/PERILLAS.md desde un volcado del editor (perillas.json).

El volcado lo saca una sesion de Claude con el MCP (lista de variables de cada Blueprint central, su categoria
y su valor en el CDO): VR_Test/Saved/ClaudeScripts/Obra/dump/perillas.json. Despues:
  python tools/unreal/gen_perillas_doc.py
"""
import json, os, re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
SRC = os.path.join(ROOT, "VR_Test", "Saved", "ClaudeScripts", "Obra", "dump", "perillas.json")
D = json.load(open(SRC, encoding="utf-8"))
INFO = {
    "BP_Obra_SC": ("El director de la Obra", "L_SoulCharger_Obra", "Los tiempos NO se tocan aca: van en DA_Partitura_Obra (ver docs/PARTITURA.md). En la instancia del nivel solo cuentan Config y Debug."),
    "BP_StageRunner_SC": ("El ensayo de una etapa en su nivel de test", "cada Test_* (actor TestOnly)", "Tiempos desde la Partitura; en la instancia quedan StageK, colores del velo (CTop/CHor), tags de los TargetPoints, Loop, Speed."),
    "BP_HallRunner_SC": ("El ensayo del Hall", "Test_Hall (TestOnly)", "DebugStart 2-9 para arrancar en un paso del Hall."),
    "BP_HallDirector_SC": ("El Hall: inicio, regreso y salida", "Test_Hall", "Las paradas son flechas arrastrables en el nivel; los ritmos estan en sus categorias."),
    "BP_BreathStage_SC": ("Entering: la etapa", "Test_Entering", ""),
    "BP_BreathRig_SC": ("Entering: el sensor de respiracion (mandos)", "Test_Entering", "Umbral y suavizado de la respiracion."),
    "BP_BreathBlob_SC": ("Entering: el metaball", "Test_Entering", ""),
    "BP_Pacer_SC": ("Entering: el pacer (guia de respiracion)", "Test_Entering", "Ciclos y tiempos 4-3-4-3."),
    "BP_HeartManager_SC": ("Recognizing: el latido", "Test_Heart", "StageBeats = latidos hasta el fin."),
    "BP_LovingCell_SC": ("Loving: la celula", "Test_Fluid", "StageDuration = duracion de la mecanica."),
    "BP_FluidMedium_SC": ("Loving: el fluido cerebral", "Test_Fluid", ""),
    "BP_Sequencer_SC": ("Attracting: el secuenciador", "Test_Sequencer", ""),
    "BP_SeqRig_SC": ("Attracting: los mandos y el laser", "Test_Sequencer", ""),
    "BP_TBDirector_NC": ("Surrounding: el dibujo (director)", "L_TBTest_SC", "Tinta, paleta, presentacion."),
    "BPC_TBTool_NC": ("Surrounding: la herramienta de dibujo", "L_TBTest_SC", ""),
    "BP_Alma_SC": ("Alma (la guia)", "todos", "Su aspecto vive en el material; aca la voz y los movimientos."),
    "BP_SoulHUD3D_SC": ("El HUD (pildora)", "L_SoulCharger_Obra", ""),
    "BP_ChargeFx_SC": ("La carga del anillo", "L_SoulCharger_Obra", ""),
    "BP_UserTool_SC": ("El objeto de la mano (mando/sensor)", "L_SoulCharger_Obra", ""),
    "BP_GhostPlayer_SC": ("Los fantasmas de instrucciones", "L_SoulCharger_Obra", ""),
    "BP_JourneyContent_SC": ("Resultados: el contenido", "L_SoulCharger_Obra", ""),
    "BP_ResultsArt_SC": ("Resultados: el cuadro", "L_SoulCharger_Obra", ""),
}
INTERNAL = re.compile(r"(Interno|Estado|Z-|Runtime|State|Internal|Cache|Refs?$|^Y-Publicado)", re.I)
def val(s):
    try:
        d = json.loads(s)
        v = list(d.values())[0] if isinstance(d, dict) and d else s
    except Exception:
        m = re.match(r'^\{"[^"]+":(.*)$', s)
        v = m.group(1) if m else s
    t = json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
    t = t.replace("|", "/")
    return (t[:70] + "...") if len(t) > 70 else t
out = ["# Perillas de cada mecanica", "",
       "> Generado por `tools/unreal/gen_perillas_doc.py` desde un volcado del editor (`perillas.json`, 2026-10-02). Valores = los del Blueprint (CDO).",
       "> 🔴 Si una perilla tambien esta puesta en la INSTANCIA de su nivel de test, manda la instancia: mirar el Details del actor en ese nivel.",
       "", "**Regla de donde se ajusta cada cosa** (detalle en `docs/GUIA-DE-DIRECCION.md`):",
       "- **Cuando** pasa algo en la obra -> `DA_Partitura_Obra` (`docs/PARTITURA.md`).",
       "- **Donde** pasa -> TargetPoints y actores en el nivel de test de la etapa.",
       "- **Como se ve y se siente** una mecanica -> las perillas de esta pagina, en su nivel de test.",
       "", "Las categorias que parecen internas (Interno, Estado, Z-...) se omiten: no son perillas.", ""]
for bp in D:
    if bp == "log":
        continue
    title, lvl, note = INFO.get(bp, (bp, "", ""))
    rows = D[bp]
    cats = {}
    for n, c, v in rows:
        c = c if c not in ("None", "") else "Default"
        cats.setdefault(c, []).append((n, v))
    out.append("## %s — `%s`" % (title, bp))
    out.append("")
    if lvl:
        out.append("Nivel donde se ajusta: **%s**. %s" % (lvl, note))
        out.append("")
    shown = 0
    for c in sorted(cats):
        if INTERNAL.search(c):
            continue
        items = cats[c]
        if bp == "BP_Obra_SC" and c not in ("Config", "Debug", "Partitura", "Etapas", "Final", "Ambientes", "Hall - Anillo", "Instrucciones"):
            continue
        out.append("**%s** — " % c + " · ".join("`%s` %s" % (n, val(v)) for n, v in items))
        out.append("")
        shown += len(items)
    out.append("_%d perillas listadas de %d variables._" % (shown, len(rows)))
    out.append("")
open(os.path.join(ROOT, "docs", "PERILLAS.md"), "w", encoding="utf-8").write("\n".join(out) + "\n")
print("docs/PERILLAS.md listo")
