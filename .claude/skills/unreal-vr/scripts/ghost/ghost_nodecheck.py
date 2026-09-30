import json
# ghost_nodecheck.py - SOLO LECTURA: verifica de una vez los nombres de nodo marcados ';;?' en ghost_player.dsl y
# ghost_recorder.dsl (find_node_types con filtro). Correr DESPUES de ghost_build.py PARTE 'player' (usa un grafo del
# reproductor como contexto). Devuelve, por filtro, los type_id que existen (recortados). Se pega ENTERO.
BT = 'editor_toolset.toolsets.blueprint.BlueprintTools.'
G = {'refPath': '/Game/SoulCharger/Mechanics/Ghost/BP_GhostPlayer_SC.BP_GhostPlayer_SC:GhPose'}
FILTROS = [
    'SetActorHiddenInGame', 'SetWorldSize', 'SetHorizontalAlignment', 'SetVerticalAlignment', 'TextRender|SetText',
    'SetTextRenderColor', 'SetTextMaterial', 'ToText', 'ToColor', 'RotatorFromAxisAndAngle', 'GetForwardVector',
    'ComposeRotators', 'TransformRotation', 'InverseTransformRotation', 'Normalize', 'Dot', 'SetRelativeScale3D',
    'ToString(Name)', 'EnableInput', 'GetMotionControllerState', 'BreakXRMotionControllerState', 'Quat|',
    'EnhancedActionValues|IA_Hand', 'Class|BPGhostTakeSC|', 'AddComponentbyClass', 'CastToTextRenderComponent',
    'SetTimerbyFunctionName', 'ClearTimerbyFunctionName', 'GetWorldDeltaSeconds', 'SetScalarParameterValueOnMaterials',
    'SetVectorParameterValueOnMaterials', 'SetCastShadow', 'SetCollisionEnabled', 'PlaySound2D']


def run():
    out = {}
    for f in FILTROS:
        try:
            r = execute_tool(BT + 'find_node_types', json.dumps({'graph': G, 'type_id_filter': f, 'context_pins': []}))
            v = r['returnValue'] if isinstance(r, dict) and ('returnValue' in r) else r
            ids = []
            for x in (v or []):
                t = x['type_id'] if isinstance(x, dict) and ('type_id' in x) else str(x)
                if t not in ids:
                    ids.append(t)
            out[f] = ids[:6]
        except BaseException as e:
            out[f] = 'ERR ' + str(e)[:100]
    return out
