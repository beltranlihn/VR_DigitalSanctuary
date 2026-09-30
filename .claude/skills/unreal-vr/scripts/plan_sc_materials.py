# -*- coding: utf-8 -*-
"""plan_sc_materials.py - PLAN (JSON) de los materiales de la familia timbre / SAVE MELODY / sensor + la aparicion
'luz primero' (2026-09-30). Lo lee apply_sc_materials.py dentro de Unreal (AssetTools.read_file).

Maestros (en /Game/SoulCharger/Mechanics/Appear):
  M_SCObject_SC        hormigon con sombreado falso (SCObjectShadePS = DrawPaletteShadePS + Flash), mascara por UV1
  M_SCLight_SC         cintas de luz: Color * Glow * AppearGlow
  M_AppearTrace_SC     el trazo de luz (aditivo, dos caras)
  M_SCChargeSlider_SC  slider de carga transparente (aditivo)
  M_BioSensorWaves_SC  los aros del sensor (aditivo, dos caras) - en BioSensor/
Instancias por objeto y asignacion a los slots de cada malla.
Uso: python plan_sc_materials.py
"""
import json
import os

AQUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(AQUI, "..", "..", "..", ".."))
HLSL = os.path.join(AQUI, "hlsl")
SALIDA = os.path.join(REPO, "VR_Test", "Saved", "ClaudeScripts", "Appear", "sc_materials_build.json")
G = "/Game/SoulCharger/Mechanics/"
AP = G + "Appear/"
LIGHT = [1.0, 0.72, 0.45, 1.0]


def code(name):
    return open(os.path.join(HLSL, name), encoding="utf-8").read()


def S(name, d, group):
    return {"name": name, "kind": "scalar", "default": d, "group": group}


def Vv(name, d, group):
    return {"name": name, "kind": "vector", "default": list(d) + ([1.0] if len(d) == 3 else []), "group": group}


def P(name, vec=False):
    return {"kind": "param", "param": name, "pin": "RGB" if vec else ""}


UNLIT = {"shadingModel": "MSM_Unlit", "blendMode": "BLEND_Opaque", "twoSided": False}
ADD2 = {"shadingModel": "MSM_Unlit", "blendMode": "BLEND_Additive", "twoSided": True}
ADD1 = {"shadingModel": "MSM_Unlit", "blendMode": "BLEND_Additive", "twoSided": False}

obj_params = [Vv("Base", (0.62, 0.56, 0.48), "1 - Color"), Vv("Ink", (0.93, 0.91, 0.87), "1 - Color"),
              S("InkGlow", 0.35, "1 - Color"),
              Vv("LightDir", (-0.35, 0.30, 0.88), "2 - Luz"), S("Ambient", 0.30, "2 - Luz"), S("Diffuse", 0.55, "2 - Luz"),
              S("Wrap", 0.4, "2 - Luz"), S("Fill", 0.25, "2 - Luz"), S("SelfGlow", 0.10, "2 - Luz"),
              S("Grain", 0.06, "3 - Hormigon"), S("GrainScale", 0.08, "3 - Hormigon"), S("Mottle", 0.08, "3 - Hormigon"),
              S("MottleScale", 3.0, "3 - Hormigon"),
              S("Flash", 0.0, "4 - Aparicion"), Vv("FlashColor", LIGHT[:3], "4 - Aparicion")]
obj_inputs = [("N", {"kind": "normalws"}), ("V", {"kind": "camvec"}), ("P", {"kind": "localpos"}), ("Base", P("Base", True)),
              ("M", {"kind": "texparam", "param": "MaskTex", "pin": "R"}), ("UVm", {"kind": "texcoord", "index": 1}),
              ("Ink", P("Ink", True)), ("InkGlow", P("InkGlow")), ("LightDir", P("LightDir", True)), ("Ambient", P("Ambient")),
              ("Diffuse", P("Diffuse")), ("Wrap", P("Wrap")), ("Fill", P("Fill")), ("SelfGlow", P("SelfGlow")),
              ("Grain", P("Grain")), ("GrainScale", P("GrainScale")), ("Mottle", P("Mottle")), ("MottleScale", P("MottleScale")),
              ("Flash", P("Flash")), ("FlashColor", P("FlashColor", True))]
MATS = [
    {"material": AP + "M_SCObject_SC", "flags": UNLIT, "params": obj_params,
     "textures": [{"name": "MaskTex", "default": "/Engine/EngineResources/Black.Black", "uv": 1, "group": "1 - Color"}],
     "custom": {"desc": "SCObjectShadePS", "outputType": "CMOT_Float3", "code": code("SCObjectShadePS.hlsl"),
                "inputs": [{"name": n, "src": s} for n, s in obj_inputs]}},
    {"material": AP + "M_SCLight_SC", "flags": UNLIT,
     "params": [Vv("Color", LIGHT[:3], "1 - Luz"), S("Glow", 1.0, "1 - Luz"), S("AppearGlow", 1.0, "2 - Aparicion")],
     "custom": {"desc": "SCLightPS", "outputType": "CMOT_Float3", "code": code("SCLightPS.hlsl"),
                "inputs": [{"name": "Color", "src": P("Color", True)}, {"name": "Glow", "src": P("Glow")},
                           {"name": "AppearGlow", "src": P("AppearGlow")}]}},
    {"material": AP + "M_AppearTrace_SC", "flags": ADD2,
     "params": [S("Sweep", 0.0, "1 - Trazo"), S("Soft", 0.05, "1 - Trazo"), S("Head", 0.0, "1 - Trazo"), S("Glow", 0.0, "1 - Trazo"),
                S("Halo", 0.30, "1 - Trazo"), Vv("Color", LIGHT[:3], "1 - Trazo")],
     "custom": {"desc": "AppearTracePS", "outputType": "CMOT_Float3", "code": code("AppearTracePS.hlsl"),
                "inputs": [{"name": "UV", "src": {"kind": "texcoord", "index": 0}}] +
                          [{"name": n, "src": P(n, n == "Color")} for n in ("Sweep", "Soft", "Head", "Glow", "Halo", "Color")]}},
    {"material": AP + "M_SCChargeSlider_SC", "flags": ADD1,
     "params": [S("Progress", 0.0, "1 - Carga"), Vv("Color", LIGHT[:3], "1 - Carga"), S("Level", 0.58, "1 - Carga")],
     "custom": {"desc": "ChargeSliderPS", "outputType": "CMOT_Float3", "code": code("ChargeSliderPS.hlsl"),
                "inputs": [{"name": "UV", "src": {"kind": "texcoord", "index": 0}}, {"name": "Progress", "src": P("Progress")},
                           {"name": "Color", "src": P("Color", True)}, {"name": "Level", "src": P("Level")}]}},
    {"material": G + "BioSensor/M_BioSensorWaves_SC", "flags": ADD2,
     "params": [Vv("Color", LIGHT[:3], "1 - Aros"), S("Intensity", 1.0, "1 - Aros"), S("Count", 5.0, "1 - Aros"),
                S("Speed", 0.5, "1 - Aros"), S("Width", 0.055, "1 - Aros"), S("Squeeze", 2.0, "1 - Aros"),
                S("FadeIn", 0.35, "1 - Aros"), S("FadeOut", 0.45, "1 - Aros"), S("Active", 1.0, "2 - Estado"),
                S("AppearGlow", 1.0, "3 - Aparicion")],
     "custom": {"desc": "BioSensorWavesPS", "outputType": "CMOT_Float3", "code": code("BioSensorWavesPS.hlsl"),
                "inputs": [{"name": "UV", "src": {"kind": "texcoord", "index": 0}}, {"name": "T", "src": {"kind": "time"}}] +
                          [{"name": n, "src": P(n, n == "Color")} for n in ("Color", "Intensity", "Count", "Speed", "Width",
                                                                          "Squeeze", "FadeIn", "FadeOut", "Active", "AppearGlow")]}},
]


def mi(path, parent, scalars=None, vectors=None, textures=None):
    return {"path": path, "parent": parent, "scalars": scalars or {}, "vectors": {k: list(v) + [1.0] for k, v in (vectors or {}).items()},
            "textures": textures or {}}


OBJ, LI, SL = AP + "M_SCObject_SC", AP + "M_SCLight_SC", AP + "M_SCChargeSlider_SC"
B, SM, BS = G + "Bell/", G + "SaveMelody/", G + "BioSensor/"
INST = [
    mi(B + "MI_Bell_Body_SC", OBJ, vectors={"Base": (0.62, 0.56, 0.48)}),
    mi(B + "MI_Bell_Face_SC", OBJ, vectors={"Base": (0.55, 0.50, 0.43)}),
    mi(B + "MI_Bell_Pocket_SC", OBJ, {"SelfGlow": 0.02}, {"Base": (0.06, 0.06, 0.065)}),
    mi(B + "MI_Bell_ButtonSide_SC", OBJ, vectors={"Base": (0.70, 0.64, 0.55)}),
    mi(B + "MI_Bell_ButtonTop_SC", OBJ, vectors={"Base": (0.74, 0.68, 0.58)}),
    mi(B + "MI_Bell_Ring_SC", LI, {"Glow": 0.7}),
    mi(B + "MI_Bell_Slider_SC", SL),
    mi(SM + "MI_SaveMelody_Body_SC", OBJ, vectors={"Base": (0.62, 0.56, 0.48)}),
    mi(SM + "MI_SaveMelody_PlateSide_SC", OBJ, vectors={"Base": (0.70, 0.64, 0.55)}),
    mi(SM + "MI_SaveMelody_PlateTop_SC", OBJ, vectors={"Base": (0.56, 0.51, 0.45)},
       textures={"MaskTex": SM + "T_SaveMelody_Text.T_SaveMelody_Text"}),
    mi(SM + "MI_SaveMelody_Ring_SC", LI, {"Glow": 0.7}),
    mi(SM + "MI_SaveMelody_Slider_SC", SL),
    mi(BS + "MI_BioSensor_Body_SC", OBJ, vectors={"Base": (0.62, 0.56, 0.48)}),
    mi(BS + "MI_BioSensor_Face_SC", OBJ, vectors={"Base": (0.52, 0.47, 0.41)}),
    mi(BS + "MI_BioSensor_Grip_SC", OBJ, {"SelfGlow": 0.04}, {"Base": (0.05, 0.05, 0.055)}),
    mi(BS + "MI_BioSensor_Button_SC", OBJ, vectors={"Base": (0.70, 0.64, 0.55)}),
    mi(BS + "MI_BioSensor_Ring_SC", LI, {"Glow": 1.0}),
    mi(BS + "MI_BioSensor_BackRing_SC", LI, {"Glow": 0.9}),
    mi(BS + "MI_BioSensor_TipLight_SC", LI, {"Glow": 1.0}),
]
# slot -> material, por malla
ASSIGN = {
    B + "SM_Bell_Base_SC": {"M_Bell_Body": B + "MI_Bell_Body_SC", "M_Bell_Face": B + "MI_Bell_Face_SC",
                            "M_Bell_Ring": B + "MI_Bell_Ring_SC", "M_Bell_Pocket": B + "MI_Bell_Pocket_SC"},
    B + "SM_Bell_Button_SC": {"M_Bell_ButtonSide": B + "MI_Bell_ButtonSide_SC", "M_Bell_ButtonTop": B + "MI_Bell_ButtonTop_SC"},
    B + "SM_Bell_Slider_SC": {"M_Bell_Slider": B + "MI_Bell_Slider_SC"},
    B + "SM_Bell_Trace_SC": {"WorldGridMaterial": AP + "M_AppearTrace_SC"},
    SM + "SM_SaveMelody_Base_SC": {"M_SaveMelody_Body": SM + "MI_SaveMelody_Body_SC", "M_SaveMelody_Ring": SM + "MI_SaveMelody_Ring_SC"},
    SM + "SM_SaveMelody_Plate_SC": {"M_SaveMelody_PlateSide": SM + "MI_SaveMelody_PlateSide_SC",
                                    "M_SaveMelody_PlateTop": SM + "MI_SaveMelody_PlateTop_SC"},
    SM + "SM_SaveMelody_Slider_SC": {"M_SaveMelody_Slider": SM + "MI_SaveMelody_Slider_SC"},
    SM + "SM_SaveMelody_Trace_SC": {"WorldGridMaterial": AP + "M_AppearTrace_SC"},
    BS + "SM_BioSensor_SC": {"M_BioSensor_Body": BS + "MI_BioSensor_Body_SC", "M_BioSensor_Face": BS + "MI_BioSensor_Face_SC",
                             "M_BioSensor_Ring": BS + "MI_BioSensor_Ring_SC", "M_BioSensor_Grip": BS + "MI_BioSensor_Grip_SC",
                             "M_BioSensor_BackRing": BS + "MI_BioSensor_BackRing_SC"},
    BS + "SM_BioSensor_Button_SC": {"M_BioSensor_Button": BS + "MI_BioSensor_Button_SC", "M_BioSensor_TipLight": BS + "MI_BioSensor_TipLight_SC"},
    BS + "SM_BioSensorWaves_SC": {"M_BioSensor_Waves": BS + "M_BioSensorWaves_SC"},
    BS + "SM_BioSensor_Trace_SC": {"WorldGridMaterial": AP + "M_AppearTrace_SC"},
    G + "DrawPalette/SM_DrawPalette_Trace_SC": {"WorldGridMaterial": AP + "M_AppearTrace_SC"},
}

os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
json.dump({"materials": MATS, "instances": INST, "assign": ASSIGN}, open(SALIDA, "w", encoding="utf-8"), indent=1)
print("PLAN_OK", SALIDA, len(MATS), "maestros", len(INST), "instancias", len(ASSIGN), "mallas")
