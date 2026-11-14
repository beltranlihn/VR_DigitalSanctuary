import json
BT = 'editor_toolset.toolsets.blueprint.BlueprintTools.'
BP = {'refPath': '/Game/SoulCharger/Mechanics/Hall/BP_HallDirector_SC.BP_HallDirector_SC'}
VARS = [["TestFromStep", "int", -1, true, "Prueba"], ["IntroHold", "float", 12.0, true, "Ritmo"], ["PaceWalkToVO", "float", 3.0, true, "Ritmo"], ["PaceJourneyPause", "float", 1.5, true, "Ritmo"], ["PaceArrive", "float", 0.5, true, "Ritmo"], ["PaceBellVO", "float", 0.5, true, "Ritmo"], ["PaceBellRing", "float", 0.8, true, "Ritmo"], ["PaceDoorOpen", "float", 1.5, true, "Ritmo"], ["PaceAlmaAppear", "float", 2.5, true, "Ritmo"], ["PaceAfterTool", "float", 0.5, true, "Ritmo"], ["PaceTilesOff", "float", 1.5, true, "Ritmo"], ["PaceHudBirth", "float", 3.0, true, "Ritmo"], ["PaceFollowMe", "float", 2.0, true, "Ritmo"], ["PaceLightsOffOut", "float", 5.0, true, "Ritmo"], ["PaceReturnDark", "float", 2.0, true, "Ritmo"], ["PaceReturnLight", "float", 1.5, true, "Ritmo"], ["PaceReturnDoor", "float", 1.0, true, "Ritmo"], ["PaceReturnVO", "float", 1.0, true, "Ritmo"], ["PaceDoorClose", "float", 1.0, true, "Ritmo"], ["PaceExitLightsOff", "float", 6.0, true, "Ritmo"], ["BellPressDepth", "float", 1.0, true, "Timbre"], ["DoorLeadDist", "float", 620.0, true, "Ritmo"], ["BellPressTime", "float", 0.12, true, "Timbre"], ["BellPress", "float", 0.0, false, null], ["BellRest", "Vector", null, false, null]]
LOG = []
def T(name, payload):
    try:
        return True, execute_tool(name, json.dumps(payload))['returnValue']
    except BaseException as e:
        LOG.append(name.split('.')[-1] + ' :: ' + str(e)[:200])
        return False, None
def run():
  try:
    ok, ya = T(BT + 'list_variables', {'blueprint': BP})
    ya = ya or []
    hechas = []
    for n, t, d, e, c in VARS:
        if n in ya:
            continue
        if T(BT + 'add_variable', {'blueprint': BP, 'name': n, 'type_name': t})[0]:
            hechas.append(n)
        if e:
            T(BT + 'set_variable_instance_editable', {'blueprint': BP, 'variable_name': n, 'instance_editable': True})
    T(BT + 'compile_blueprint', {'blueprint': BP})
    return {'hechas': len(hechas), 'log': LOG[:8]}
  except BaseException as e:
    return {'err': str(e)[:300], 'log': LOG}
