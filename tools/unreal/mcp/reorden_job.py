# reorden_job.py - script para ProgrammaticToolset.execute_tool_script (MCP de Unreal).
# Mueve una tanda del mapa de tools/unreal/reorden_contenido_2026-10-02.json (copiado a Saved/.../dump/reorden.json).
# AssetTools.move arregla y GUARDA las referencias y no deja redirector (probado 2026-10-02).
# Uso: cambiar LISTA/INI/FIN, pegar el archivo entero como 'script'. Cada tanda deja su log en dump/reorden_log_<LISTA>_<INI>.json.
# Reglas: PIE detenido; el nivel abierto no puede estar en la tanda; contar actores del nivel abierto antes y después.
import json
LISTA = 'mover'   # 'mover' o 'archivar'
INI = 0
FIN = 40
AS = 'editor_toolset.toolsets.asset.AssetTools.'
SC = 'editor_toolset.toolsets.scene.SceneTools.'
D = 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/Obra/dump/'
def G(f, a):
    try:
        return execute_tool(f, json.dumps(a))['returnValue']
    except BaseException as e:
        return 'ERR ' + str(e)[:300]
def run():
    plan = json.loads(G(AS + 'read_file', {'file_path': D + 'reorden.json'}))[LISTA][INI:FIN]
    lvl = G(SC + 'get_current_level', {})
    log = {'lvl': lvl, 'ok': 0, 'skip': [], 'err': [], 'redir': []}
    for old, new in plan:
        if old == lvl or new == lvl:
            log['skip'].append([old, 'nivel abierto']); continue
        if G(AS + 'exists', {'path': old}) is not True:
            log['skip'].append([old, 'no existe (ya movido?)' if G(AS + 'exists', {'path': new}) is True else 'no existe']); continue
        r = G(AS + 'move', {'path': old, 'new_path': new})
        if isinstance(r, str) and r.startswith('ERR'):
            log['err'].append([old, r]); continue
        if G(AS + 'exists', {'path': new}) is not True:
            log['err'].append([old, 'el destino no existe despues de mover: ' + str(r)[:200]]); continue
        if G(AS + 'exists', {'path': old}) is True:
            log['redir'].append(old)
        log['ok'] += 1
    log['save'] = G(AS + 'save_assets', {'asset_paths': []})
    execute_tool(AS + 'write_file', json.dumps({'file_path': D + 'reorden_log_%s_%d.json' % (LISTA, INI), 'content': json.dumps(log)}))
    return {'ok': log['ok'], 'skip': len(log['skip']), 'err': len(log['err']), 'redir': len(log['redir'])}
