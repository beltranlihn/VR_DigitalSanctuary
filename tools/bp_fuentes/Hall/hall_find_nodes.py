import json
import re
# hall_find_nodes.py - confirma los type_id dudosos del DSL del director (find_node_types NO crea nodos; get_node_type_pins SI).
# Devuelve solo los ids que contienen cada filtro (compacto). Sin `result = run()`.
BT = 'editor_toolset.toolsets.blueprint.BlueprintTools.'
GRAPH = '/Game/SoulCharger/Mechanics/Hall/BP_HallDirector_SC.BP_HallDirector_SC:EventGraph'
FILTROS = ['Actor|GetAllActorswithTag', 'GetActorBounds', 'SetLifeSpan', 'SetGlobalTimeDilation', 'Audio|PlaySound2D',
           'Audio|SpawnSound2D', 'Class|SoundBase|GetDuration', 'Audio|Components|Audio|Stop', 'SetActorLocationAndRotation',
           'Transformation|SetActorRotation', 'Transformation|GetWorldRotation', 'MakeRotfromZ', 'Math|Vector|Distance',
           'Math|Transform|MakeTransform', 'Rendering|Material|GetMaterial', 'Camera|GetCameraRotation',
           'Class|BPAlmaSC|', 'Class|BPHallLightsSC|Lights', 'Class|BPCAppearLuzSC|', 'Class|BPBellArtSC|Get',
           'Class|BPBioSensorArtSC|Get', 'Class|BPSoulHUD3DSC|', 'Class|BPSoulPickerSC|', 'CallFunction|Hall',
           'Rendering|Material|SetScalarParameterValue', 'Game|SpawnActorfromClass', 'Variables|Default|GetFW',
           'Variables|Default|GetTileMID', 'Variables|Default|GetBellLive', 'Variables|Default|GetVOAir',
           'Math|Float|FInterpEaseinOut', 'SpawnSoundat', 'Math|Interpolation|FInterptoConstant']
LOG = []
def run():
  try:
    out = {}
    for f in FILTROS:
        try:
            v = execute_tool(BT + 'find_node_types', json.dumps({'graph': {'refPath': GRAPH}, 'type_id_filter': f, 'context_pins': []}))['returnValue']
            txt = json.dumps(v)
            ids = sorted(set(re.findall(r'"([A-Za-z][^"]*\|[^"]*)"', txt)))
            ids = [i for i in ids if f.split('|')[-1].lower() in i.lower()]
            out[f] = ids[:25]
        except BaseException as e:
            out[f] = 'ERR ' + str(e)[:150]
    return out
  except BaseException as e:
    return {'err': 'run :: ' + str(e)[:300]}
