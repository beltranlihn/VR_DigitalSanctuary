# plan_results_materials.py - plan de materiales del CUADRO DE RESULTADOS (blender-3d/assets/results.md) para el
# constructor de apply_sc_materials.py (con 'opacity'). Sale de hud_materials_build.json (los maestros del HUD):
#   M_SCPanel_SC      = M_SCObjectTrans_SC (hormigon translucido) SIN el doblez del HUD y CON prueba de profundidad
#   M_SCPanelGlass_SC = M_SCGlass_SC (lamina) igual
# El cuadro va PARADO en el mundo a 2 m (no pegado a la cabeza): el doblez (MPC_HUD_SC.CurveR) lo curvaria y sin
# depth test taparia a Alma o a lo que pase por delante. Los maestros del HUD NO se tocan (son de Narrativa).
# Valores = la vista previa aprobada (render_results.py): marco 0,55, contornos 0,45, lamina ahumada 0,55, vidrio de
# la ventana 0,30 SOBRE la lamina, vidrio de la cajita 0,74.
# Uso: python plan_results_materials.py  (escribe VR_Test/Saved/ClaudeScripts/Results/results_materials_build.json)
import copy
import json
import os

AQUI = os.path.dirname(os.path.abspath(__file__))
SAVED = os.path.abspath(os.path.join(AQUI, "..", "..", "..", "..", "VR_Test", "Saved", "ClaudeScripts"))
AP = "/Game/SoulCharger/Mechanics/Appear/"
RF = "/Game/SoulCharger/Mechanics/Results/"
BASE = [0.66, 0.60, 0.52, 1.0]


def main():
    hud = json.load(open(os.path.join(SAVED, "Appear", "hud_materials_build.json"), encoding="utf-8"))
    mats = []
    for M in hud["materials"]:
        M2 = copy.deepcopy(M)
        if M["material"].endswith("M_SCObjectTrans_SC"):
            M2["material"] = AP + "M_SCPanel_SC"
            op = 0.55
        else:
            M2["material"] = AP + "M_SCPanelGlass_SC"
            op = 0.55
            for p in M2["params"]:
                if p["name"] == "Color":
                    p["default"] = [0.55, 0.60, 0.85, 1.0]
                elif p["name"] == "Base":
                    p["default"] = 0.10
                elif p["name"] == "Rim":
                    p["default"] = 0.12
        for p in M2["params"]:
            if p["name"] == "Opacity":
                p["default"] = op
        M2["opacity"] = "Opacity"
        mats.append(M2)
    panel, glass = AP + "M_SCPanel_SC", AP + "M_SCPanelGlass_SC"
    inst = [
        {"path": RF + "MI_Results_Rim_SC", "parent": panel, "scalars": {"SelfGlow": 0.14, "Opacity": 0.55}, "vectors": {"Base": BASE}, "textures": {}},
        {"path": RF + "MI_Results_Frame_SC", "parent": panel, "scalars": {"SelfGlow": 0.14, "Opacity": 0.45}, "vectors": {"Base": BASE}, "textures": {}},
        {"path": RF + "MI_Results_TipFrame_SC", "parent": panel, "scalars": {"SelfGlow": 0.14, "Opacity": 0.55}, "vectors": {"Base": BASE}, "textures": {}},
        {"path": RF + "MI_Results_Glass_SC", "parent": glass, "scalars": {"Base": 0.10, "Rim": 0.12, "Opacity": 0.55}, "vectors": {"Color": [0.55, 0.60, 0.85, 1.0]}, "textures": {}},
        {"path": RF + "MI_Results_Pane_SC", "parent": glass, "scalars": {"Base": 0.05, "Rim": 0.03, "Opacity": 0.30}, "vectors": {"Color": [0.60, 0.68, 1.0, 1.0]}, "textures": {}},
        {"path": RF + "MI_Results_TipGlass_SC", "parent": glass, "scalars": {"Base": 0.07, "Rim": 0.084, "Opacity": 0.74}, "vectors": {"Color": [0.64, 0.71, 1.0, 1.0]}, "textures": {}},
    ]
    # slot (nombre base del material de Blender) -> material; el script de import resuelve el nombre REAL del slot
    slots = {"M_Results_Rim": RF + "MI_Results_Rim_SC", "M_Results_Frame": RF + "MI_Results_Frame_SC",
             "M_Results_Pane": RF + "MI_Results_Pane_SC", "M_Results_Glass": RF + "MI_Results_Glass_SC",
             "M_Results_TipFrame": RF + "MI_Results_TipFrame_SC", "M_Results_TipGlass": RF + "MI_Results_TipGlass_SC",
             "M_Results_Trace": AP + "M_AppearTrace_SC"}
    plan = {"materials": mats, "instances": inst, "slots": slots}
    out = os.path.join(SAVED, "Results", "results_materials_build.json")
    json.dump(plan, open(out, "w", encoding="utf-8"), indent=1)
    print("PLAN_OK", out, [m["material"] for m in mats], len(inst), "MI")


if __name__ == "__main__":
    main()
