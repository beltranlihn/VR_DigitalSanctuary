"""actualizar_rutas_docs.py - pasa los documentos vigentes por el mapa del reordenamiento de carpetas (2026-10-02).

Reemplaza en los .md vigentes (y el mapa del plugin de Draw, tools/unreal/plugin_draw_2026-10-02.json) (CLAUDE.md, docs/ salvo la historia, la skill unreal-vr) las rutas viejas de assets por
las nuevas (tools/unreal/reorden_contenido_2026-10-02.json), las carpetas viejas por las nuevas y los nombres de los
niveles que cambiaron (Test_Entering -> Test_Breath, Test_Fluid -> Test_Mind, L_TBTest_SC -> Test_Draw).
Los documentos de historia (PLAN-*, informes, auditorías viejas) no se tocan: describen el proyecto de su fecha.

Uso: python tools/unreal/actualizar_rutas_docs.py [--aplicar] [archivos...]
"""
import argparse, glob, json, os, re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
MAPAS = [os.path.join(ROOT, "tools", "unreal", f) for f in ("reorden_contenido_2026-10-02.json", "plugin_draw_2026-10-02.json",
                                                         "plugin_breath_2026-10-02.json", "plugin_base2_2026-10-02.json",
                                                         "plugin_sequencer_2026-10-02.json")]
SC = "/Game/SoulCharger/"
CARPETAS = [  # carpeta vieja -> nueva (despues de reemplazar las rutas de assets una por una)
    ("/Game/NeuralCanvas/Maps/", SC + "Mechanics/Draw/Maps/"), ("/Game/NeuralCanvas/", SC + "Mechanics/Draw/"),
    (SC + "Mechanics/DrawPalette/", SC + "Mechanics/Draw/"), (SC + "Mechanics/Drawing/", SC + "Mechanics/Draw/"),
    (SC + "Mechanics/Loving/", SC + "Mechanics/Mind/"), (SC + "Mechanics/Fluid/", SC + "Mechanics/Mind/"),
    (SC + "Mechanics/Pacer/", SC + "Mechanics/Breath/"), (SC + "Mechanics/SaveMelody/", SC + "Mechanics/Sequencer/"),
    (SC + "Core/Attracting/", SC + "Mechanics/Sequencer/"), (SC + "Core/AttractingC/", SC + "Mechanics/Sequencer/"),
    (SC + "Mechanics/Hall/", SC + "Hall/"), (SC + "Mechanics/Bell/", SC + "Hall/"),
    (SC + "Mechanics/HUD/", SC + "Shared/HUD/"), (SC + "Core/HUD/", SC + "Shared/HUD/"),
    (SC + "Mechanics/Results/", SC + "Shared/Results/"), (SC + "Mechanics/Ghost/", SC + "Shared/Ghost/"),
    (SC + "Mechanics/UserTool/", SC + "Shared/UserTool/"), (SC + "Mechanics/Appear/", SC + "Shared/Appear/"),
    (SC + "Mechanics/BioSensor/", SC + "Shared/BioSensor/"), (SC + "Mechanics/ChargeRing/", SC + "Shared/ChargeRing/"),
    (SC + "Mechanics/QuestController/", SC + "Shared/QuestController/"), (SC + "Mechanics/Subtitles/", SC + "Shared/Subtitles/"),
    (SC + "Core/Sensor/", SC + "Core/Pointer/"), (SC + "Tour/", SC + "Obra/Titles/"), ("/Game/OSC/", SC + "Core/Signals/"),
]
# formas cortas que aparecen en la prosa (sin /Game/SoulCharger/)
CORTAS = [(o.replace(SC, "").replace("/Game/", ""), n.replace(SC, "").replace("/Game/", "")) for o, n in CARPETAS
          if o.startswith(SC)]
NIVELES = [("Test_Entering", "Test_Breath"), ("Test_Fluid", "Test_Mind"), ("L_TBTest_SC", "Test_Draw")]
HISTORIA = re.compile(r"(PLAN-|INFORME-|NOTAS-|HALLAZGOS-|PERF-|ANALISIS-|AUDITORIA-2026-09|AUDITORIA-ESTRUCTURA|VO-AUDITORIA|"
                      r"INVESTIGACION-|IDEAS-|GUION-V4|ESTADO-STAGES|PENDIENTE-|BRIEF-|AJUSTES-ESTETICOS|AUDIO-QUE-PIDE)")


def archivos():
    fs = [os.path.join(ROOT, "CLAUDE.md"), os.path.join(ROOT, "GUIA-RAPIDA.md")]
    fs += [f for f in glob.glob(os.path.join(ROOT, "docs", "*.md")) if not HISTORIA.search(os.path.basename(f))]
    fs += glob.glob(os.path.join(ROOT, ".claude", "skills", "unreal-vr", "**", "*.md"), recursive=True)
    return [f for f in fs if os.path.exists(f)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("files", nargs="*")
    a = ap.parse_args()
    # los mapas se encadenan: una ruta de 09-30 pasa por el reordenamiento y despues por el plugin
    cadena = {}
    for mp in MAPAS:
        if os.path.exists(mp):
            for o, n in json.load(open(mp, encoding="utf-8"))["mover"]:
                for k, v in list(cadena.items()):
                    if v == o:
                        cadena[k] = n
                cadena[o] = n
    pares = sorted(cadena.items(), key=lambda x: -len(x[0]))
    total = 0
    for f in (a.files or archivos()):
        s = open(f, encoding="utf-8").read()
        t = s
        for o, n in pares:
            t = re.sub(re.escape(o) + r"(?![A-Za-z0-9_])", n, t)
        for o, n in CARPETAS:
            t = t.replace(o, n)
        for o, n in CORTAS:
            t = re.sub(r"(?<![A-Za-z/])" + re.escape(o), n, t)
        for o, n in NIVELES:
            t = re.sub(r"(?<![A-Za-z0-9_])" + re.escape(o) + r"(?![A-Za-z0-9_])", n, t)
        if t != s:
            k = sum(1 for x, y in zip(s.splitlines(), t.splitlines()) if x != y)
            total += 1
            print("%4d líneas  %s" % (k, os.path.relpath(f, ROOT)))
            if a.aplicar:
                open(f, "w", encoding="utf-8").write(t)
    print("%d archivos %s" % (total, "actualizados" if a.aplicar else "a actualizar (correr con --aplicar)"))


if __name__ == "__main__":
    main()
