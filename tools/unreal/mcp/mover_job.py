# mover_job.py - script para ProgrammaticToolset.execute_tool_script (MCP de Unreal).
# Mueve una tanda de un mapa {"mover": [[vieja, nueva], ...]} que está en Saved/ClaudeScripts/Obra/dump/<ARCHIVO>
# (lo escriben tools/unreal/plan_plugin.py o reordenar_contenido.py). AssetTools.move arregla y guarda las
# referencias; solo deja redirector cuando quien lo usa es un nivel cerrado (gotchas 583 y 586).
# Uso: cambiar ARCHIVO/INI/FIN y pegar el archivo entero como 'script'. Log en dump/<ARCHIVO sin .json>_log_<INI>.json.
# Reglas: PIE detenido; el nivel abierto no puede estar en la tanda.
import json
ARCHIVO = 'plugin_breath.json'
INI = 0
FIN = 80
AS = 'editor_toolset.toolsets.asset.AssetTools.'
SC = 'editor_toolset.toolsets.scene.SceneTools.'
D = 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/Obra/dump/'
def G(f, a):
    try:
        return execute_tool(f, json.dumps(a))['returnValue']
    except BaseException as e:
        return 'ERR ' + str(e)[:300]
def run():
    plan = json.loads(G(AS + 'read_file', {'file_path': D + ARCHIVO}))['mover'][INI:FIN]
    lvl = G(SC + 'get_current_level', {})
    log = {'lvl': lvl, 'ok': 0, 'skip': [], 'err': [], 'redir': []}
    for old, new in plan:
        if old == lvl or new == lvl:
            log['skip'].append([old, 'nivel abierto']); continue
        if G(AS + 'exists', {'path': old}) is not True:
            log['skip'].append([old, 'ya movido' if G(AS + 'exists', {'path': new}) is True else 'no existe']); continue
        r = G(AS + 'move', {'path': old, 'new_path': new})
        if isinstance(r, str) and r.startswith('ERR'):
            log['err'].append([old, r]); continue
        if G(AS + 'exists', {'path': new}) is not True:
            log['err'].append([old, 'destino no existe: ' + str(r)[:200]]); continue
        if G(AS + 'exists', {'path': old}) is True:
            log['redir'].append(old)
        log['ok'] += 1
    log['save'] = G(AS + 'save_assets', {'asset_paths': []})
    execute_tool(AS + 'write_file', json.dumps({'file_path': D + ARCHIVO.replace('.json', '') + '_log_%d.json' % INI, 'content': json.dumps(log)}))
    return {'ok': log['ok'], 'skip': len(log['skip']), 'err': len(log['err']), 'redir': len(log['redir']), 'lvl': lvl}
