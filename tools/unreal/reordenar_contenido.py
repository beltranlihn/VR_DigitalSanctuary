"""reordenar_contenido.py - arma el mapa de traslado de Content/ al orden definitivo (2026-10-02).

Orden destino (lo pidió Beltrán: "las mecánicas ordenadas por Draw, Breath, Heart, Sequencer, Mind" y cada asset
guardado según su tipo):

  /Game/SoulCharger/
    Obra/                 el nivel final (L_SoulCharger_Obra), Blueprints/ del director y los ensayos, Partitura/,
                          Titles/, Audio/ (voces y Placeholder/), Materials/
    Hall/                 inicio, hall y regreso (+ timbre). Maps/Test_Hall
    Mechanics/Breath/     Entering (respiración + pacer).  Maps/Test_Breath
    Mechanics/Heart/      Recognizing (latido).            Maps/Test_Heart
    Mechanics/Mind/       Loving (célula + fluido).        Maps/Test_Mind
    Mechanics/Sequencer/  Attracting (secuenciador).       Maps/Test_Sequencer
    Mechanics/Draw/       Surrounding (dibujo, ex /Game/NeuralCanvas). Maps/Test_Draw
    Shared/<Pieza>/       lo que usan varias etapas o el marco: HUD, Results, Ghost, UserTool, Appear, BioSensor,
                          ChargeRing, QuestController, Subtitles
    Core/<Pieza>/         pawn, Alma, alma del usuario, señales, luz, audio general, puntero, input, UI, debug
  /Game/XRFramework, /Game/XRMannequins   base VR de Epic (no se tocan)
  /Game/_Deprecated/      lo que no usa nada (se saca del proyecto con archive_unused.py, con Unreal cerrado)

Dentro de cada mecánica, del Hall y de la Obra: Blueprints/ Materials/ Meshes/ Textures/ Audio/ Input/ VFX/ UI/ Data/ Maps/.
En Shared/ y Core/ las piezas chicas (menos de 12 assets) quedan planas.

Uso: python tools/unreal/reordenar_contenido.py   (lee el volcado de clases del editor, escribe el mapa y lo resume)
El traslado lo hace una sesión con el MCP (AssetTools.move, que arregla y guarda las referencias sin dejar redirector).
"""
import collections, json, os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
CLASES = os.path.join(ROOT, "VR_Test", "Saved", "ClaudeScripts", "Obra", "dump", "clases.json")
OUT = os.path.join(ROOT, "tools", "unreal", "reorden_contenido_2026-10-02.json")
SC = "/Game/SoulCharger"

# (prefijo viejo, grupo nuevo, modo)  modo: 'tipo' = subcarpetas por tipo · 'plano' = sin subcarpetas · 'keep' = conserva la ruta relativa
GRUPOS = [
    (SC + "/Mechanics/Breath/", SC + "/Mechanics/Breath", "tipo"),
    (SC + "/Mechanics/Pacer/", SC + "/Mechanics/Breath", "tipo"),
    (SC + "/Mechanics/Heart/", SC + "/Mechanics/Heart", "tipo"),
    (SC + "/Mechanics/Loving/", SC + "/Mechanics/Mind", "tipo"),
    (SC + "/Mechanics/Fluid/", SC + "/Mechanics/Mind", "tipo"),
    (SC + "/Mechanics/Sequencer/", SC + "/Mechanics/Sequencer", "tipo"),
    (SC + "/Mechanics/SaveMelody/", SC + "/Mechanics/Sequencer", "tipo"),
    (SC + "/Core/Attracting/", SC + "/Mechanics/Sequencer", "tipo"),
    (SC + "/Core/AttractingC/", SC + "/Mechanics/Sequencer", "tipo"),
    (SC + "/Core/Audio/AttractingSounds/", SC + "/Mechanics/Sequencer", "tipo"),
    ("/Game/NeuralCanvas/", SC + "/Mechanics/Draw", "tipo"),
    (SC + "/Mechanics/DrawPalette/", SC + "/Mechanics/Draw", "tipo"),
    (SC + "/Mechanics/Drawing/", SC + "/Mechanics/Draw", "tipo"),
    (SC + "/Mechanics/Hall/", SC + "/Hall", "tipo"),
    (SC + "/Mechanics/Bell/", SC + "/Hall", "tipo"),
    (SC + "/Mechanics/HUD/", SC + "/Shared/HUD", "auto"),
    (SC + "/Core/HUD/", SC + "/Shared/HUD", "auto"),
    (SC + "/Mechanics/Results/", SC + "/Shared/Results", "auto"),
    (SC + "/Mechanics/Ghost/", SC + "/Shared/Ghost", "auto"),
    (SC + "/Mechanics/UserTool/", SC + "/Shared/UserTool", "auto"),
    (SC + "/Calibration/Audio/", SC + "/Shared/UserTool", "auto"),
    (SC + "/Mechanics/Appear/", SC + "/Shared/Appear", "auto"),
    (SC + "/Mechanics/BioSensor/", SC + "/Shared/BioSensor", "auto"),
    (SC + "/Mechanics/ChargeRing/", SC + "/Shared/ChargeRing", "auto"),
    (SC + "/Mechanics/QuestController/", SC + "/Shared/QuestController", "auto"),
    (SC + "/Mechanics/Subtitles/", SC + "/Shared/Subtitles", "auto"),
    (SC + "/Stages/Breath/Input/", SC + "/Core/Input", "plano"),
    (SC + "/Core/UI/Input/", SC + "/Core/Input", "plano"),
    (SC + "/Core/UI/Materials/", SC + "/Core/UI", "plano"),
    (SC + "/Core/Sensor/", SC + "/Core/Pointer", "plano"),
    ("/Game/OSC/", SC + "/Core/Signals", "plano"),
    (SC + "/Tour/", SC + "/Obra/Titles", "plano"),
    (SC + "/Obra/Partitura/", SC + "/Obra/Partitura", "keep"),
    (SC + "/Obra/Titles/", SC + "/Obra/Titles", "keep"),
    (SC + "/Obra/Audio/", SC + "/Obra/Audio", "keep"),
    (SC + "/Obra/", SC + "/Obra", "tipo"),
    (SC + "/Core/", SC + "/Core", "keep"),  # Core ya está por pieza (Alma, Pawn, Light, Audio...): no cambia
]
SUELTOS = {  # assets de la raíz de /Game
    "/Game/BreathL": SC + "/Mechanics/Breath/Meshes/BreathL",
    "/Game/BreathR": SC + "/Mechanics/Breath/Meshes/BreathR",
    "/Game/ControllerL": SC + "/Shared/QuestController/ControllerL",
    "/Game/ControllerR": SC + "/Shared/QuestController/ControllerR",
    "/Game/Material_001": SC + "/Shared/QuestController/M_ControllerOld_001",
    "/Game/Material_002": SC + "/Shared/QuestController/M_ControllerOld_002",
}
NIVELES = {  # nombre nuevo de cada nivel de test (la Obra los carga por ruta: LevelPaths/LevelNames se actualizan aparte)
    "/Game/Test_Entering": SC + "/Mechanics/Breath/Maps/Test_Breath",
    "/Game/Test_Heart": SC + "/Mechanics/Heart/Maps/Test_Heart",
    "/Game/Test_Fluid": SC + "/Mechanics/Mind/Maps/Test_Mind",
    "/Game/Test_Sequencer": SC + "/Mechanics/Sequencer/Maps/Test_Sequencer",
    "/Game/NeuralCanvas/Maps/L_TBTest_SC": SC + "/Mechanics/Draw/Maps/Test_Draw",
    SC + "/Mechanics/Hall/Test_Hall": SC + "/Hall/Maps/Test_Hall",
}
QUEDAN = {SC + "/Obra/L_SoulCharger_Obra"}  # el nivel final no se mueve (ini, scripts y docs lo nombran)
# Sin uso desde ningún nivel (deps.py) y sin valor como herramienta -> /Game/_Deprecated/<ruta vieja>
MUERTOS_PREFIJOS = ["/Game/Drawing/", "/Game/Fab/", SC + "/Core/Movement/", SC + "/Mechanics/Heart/Scape/Debug/",
                    SC + "/Stages/Touch/"]
MUERTOS = {SC + "/Core/Audio/BP_AudioHub", SC + "/Core/Audio/BP_Director_Music", SC + "/Core/Audio/BP_HapticHub",
           SC + "/Core/Audio/Sounds/BreathCount", SC + "/Core/Audio/Sounds/Draw", SC + "/Core/Audio/Sounds/HeartFinal",
           SC + "/Core/Audio/Sounds/Mind1", SC + "/Core/Audio/Sounds/Mind2", SC + "/Core/Audio/Sounds/Mind3",
           SC + "/Core/Audio/Sounds/Trigger_Select", SC + "/Core/Audio/VO/Explora-Contador", SC + "/Core/Flow/BP_SoulState",
           SC + "/Mechanics/Breath/BP_BreathManager_SC", SC + "/Mechanics/Breath/Life/SM_ValleyDust_SC",
           SC + "/Mechanics/Breath/Valley/SM_BreathValley_SC", SC + "/Mechanics/Fluid/Meshes/SM_FluidShafts_SC",
           SC + "/Mechanics/HUD/MI_HUD_Pulse_SC", SC + "/Mechanics/HUD/MI_HUD_SeatOpaque_SC", SC + "/Mechanics/HUD/MI_HUD_Seat_SC",
           SC + "/Mechanics/HUD/SM_HUDPulse_SC", SC + "/Mechanics/Heart/Scape/SM_HeartMembrane_SC",
           SC + "/Mechanics/Heart/Scape/SM_HeartOrb_SC", SC + "/Mechanics/Loving/Dev/M_LovingProbe_SC",
           SC + "/Tour/BP_StageTour_SC"}
# El veil del recorrido es un material de la Obra, no un título
ESPECIALES = {SC + "/Tour/M_TourVeil_SC": SC + "/Obra/Materials/M_TourVeil_SC",
              SC + "/Obra/MI_FishSpark_SC": SC + "/Obra/Materials/MI_FishSpark_SC",
              # dos materiales se llamaban M_ProtoSoul: el de la ameba se renombra al juntarlos
              SC + "/Core/Amoeba/Materials/M_ProtoSoul": SC + "/Core/ProtoSoul/M_ProtoSoul_Amoeba"}

TIPO = {"World": "Maps", "Material": "Materials", "MaterialInstanceConstant": "Materials", "MaterialFunction": "Materials",
        "MaterialParameterCollection": "Materials", "Texture2D": "Textures", "TextureRenderTarget2D": "Textures",
        "StaticMesh": "Meshes", "SkeletalMesh": "Meshes", "SoundWave": "Audio", "SoundCue": "Audio",
        "MetaSoundSource": "Audio", "SoundAttenuation": "Audio", "InputAction": "Input", "InputMappingContext": "Input",
        "NiagaraSystem": "VFX", "Font": "UI", "FontFace": "UI"}

def tipo(path, cls):
    n = path.rsplit("/", 1)[1]
    c = cls.split(".")[-1]
    if c in TIPO:
        return TIPO[c]
    if n.startswith("WBP_"):
        return "UI"
    if n.startswith("DA_") or "/Takes/" in path:
        return "Data"
    if n.startswith(("BP_", "BPC_")) or c.endswith("_C"):
        return "Blueprints"
    return "Misc"

def main():
    cl = json.load(open(CLASES, encoding="utf-8"))["clases"]
    plan, dead, sin = [], [], []
    grupos_n = collections.Counter()
    for p in cl:
        for pre, g, m in GRUPOS:
            if p.startswith(pre):
                grupos_n[(g, m)] += 1
                break
    for p, c in sorted(cl.items()):
        if p.startswith("/Game/_Deprecated/") or p in QUEDAN:
            continue
        if p in MUERTOS or any(p.startswith(x) for x in MUERTOS_PREFIJOS):
            dead.append([p, "/Game/_Deprecated/" + p[len("/Game/"):]])
            continue
        if p in NIVELES:
            plan.append([p, NIVELES[p]]); continue
        if p in SUELTOS:
            plan.append([p, SUELTOS[p]]); continue
        if p in ESPECIALES:
            plan.append([p, ESPECIALES[p]]); continue
        n = p.rsplit("/", 1)[1]
        for pre, g, m in GRUPOS:
            if p.startswith(pre):
                rel = p[len(pre):]
                if m == "keep":
                    new = g + "/" + rel
                elif m == "plano":
                    new = g + "/" + n
                else:
                    small = m == "auto" and sum(v for (gg, mm), v in grupos_n.items() if gg == g) < 12
                    t = tipo(p, c)
                    sub = ""
                    if "/Icons/" in p:
                        sub = "/Icons"
                    if p.startswith(SC + "/Mechanics/Hall/Audio/") or p.startswith(SC + "/Mechanics/Pacer/Audio/"):
                        t = "Audio"
                    new = g + "/" + n if small else g + "/" + t + sub + "/" + n
                plan.append([p, new])
                break
        else:
            sin.append(p)
    plan = [x for x in plan if x[0] != x[1]]
    news = collections.Counter(x[1] for x in plan + dead)
    dup = [k for k, v in news.items() if v > 1]
    cl_new = {x[1] for x in plan}
    clash = [x for x in plan if x[1] in cl and x[1] != x[0]]
    doc = {"generado": "2026-10-02", "nota": "pares [ruta vieja, ruta nueva]; 'archivar' va a /Game/_Deprecated",
           "mover": plan, "archivar": dead, "sin_regla": sin, "duplicados": dup, "pisan_existente": clash}
    json.dump(doc, open(OUT, "w", encoding="utf-8"), indent=0, ensure_ascii=False)
    print("mover %d · archivar %d · sin regla %d · destinos duplicados %d · pisan existente %d" % (len(plan), len(dead), len(sin), len(dup), len(clash)))
    for s in sin:
        print("  SIN REGLA", s)
    for d in dup:
        print("  DUPLICADO", d)
    tree = collections.Counter(x[1].rsplit("/", 1)[0] for x in plan)
    for k in sorted(tree):
        print("  %4d  %s" % (tree[k], k))

if __name__ == "__main__":
    main()
