# partitura_export_job.py - script para ProgrammaticToolset.execute_tool_script (MCP de Unreal).
# Lee los valores VIVOS de DA_Partitura_Obra y los escribe en Saved/ClaudeScripts/Obra/dump/partitura_live.json.
# Despues, fuera del editor: python tools/unreal/partitura_export.py  (copia a obra/unreal/partitura.json con hash).
# Uso desde Claude: pegar este archivo entero como 'script' de execute_tool_script.
import json
OT = 'editor_toolset.toolsets.object.ObjectTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
BT = 'editor_toolset.toolsets.blueprint.BlueprintTools.'
DA = '/Game/SoulCharger/Obra/Partitura/DA_Partitura_Obra.DA_Partitura_Obra'
PB = '/Game/SoulCharger/Obra/Partitura/BP_Partitura_SC.BP_Partitura_SC'
OUT = 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/Obra/dump/partitura_live.json'
def run():
    vs = execute_tool(BT + 'list_variables', json.dumps({'blueprint': {'refPath': PB}}))['returnValue']
    names = [v['name'] if isinstance(v, dict) and 'name' in v else str(v) for v in vs]
    vals = {}
    for n in names:
        r = execute_tool(OT + 'get_properties', json.dumps({'instance': {'refPath': DA}, 'properties': [n]}))['returnValue']
        d = json.loads(r) if isinstance(r, str) else r
        vals[n] = d[n] if n in d else d
    execute_tool(AS + 'write_file', json.dumps({'file_path': OUT, 'content': json.dumps({'asset': DA, 'valores': vals})}))
    return {'n': len(vals)}
