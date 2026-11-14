import json
# ghost_nodecheck.py (v2, 2026-10-01) - SOLO LECTURA. Verifica EXACTO cada nombre de nodo que usan los dos DSL (gotcha 558:
# "extraer TODOS los ids con una regex y verificar cada uno EXACTO en un solo script"). Correr DESPUES de ghost_build.py
# 'player' y 'recorder' (usa sus grafos como contexto y las variables/componentes ya tienen que existir).
# Lee la lista de ids de Saved/ClaudeScripts/ghost/node_ids.json (la arma split_ghost.py). Devuelve los que NO existen
# exactos, con candidatos por la ultima palabra. Se pega ENTERO. Nunca levanta excepcion.
BT = 'editor_toolset.toolsets.blueprint.BlueprintTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
IDS = 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/ghost/node_ids.json'
CTX = {'ghost_player': '/Game/SoulCharger/Mechanics/Ghost/BP_GhostPlayer_SC.BP_GhostPlayer_SC:GhReset',
       'ghost_recorder': '/Game/SoulCharger/Mechanics/Ghost/BP_GhostRecorder_SC.BP_GhostRecorder_SC:RcBoot'}


def find(graph, filt):
    try:
        r = execute_tool(BT + 'find_node_types', json.dumps({'graph': {'refPath': graph}, 'type_id_filter': filt, 'context_pins': []}))
        v = r['returnValue'] if isinstance(r, dict) and ('returnValue' in r) else r
        out = []
        for x in (v or []):
            t = x['type_id'] if isinstance(x, dict) and ('type_id' in x) else str(x)
            if t not in out:
                out.append(t)
        return out
    except BaseException as e:
        return ['ERR ' + str(e)[:80]]


def run():
    try:
        r = execute_tool(AS + 'read_file', json.dumps({'file_path': IDS}))
        txt = r['returnValue'] if isinstance(r, dict) and ('returnValue' in r) else r
        ids = json.loads(txt)
    except BaseException as e:
        return {'err': 'no pude leer node_ids.json: ' + str(e)[:120]}
    out = {'faltan': {}, 'ok': 0}
    for cual, lista in ids.items():
        g = CTX[cual]
        for tid in lista:
            got = find(g, tid)
            if tid in got:
                out['ok'] += 1
                continue
            last = tid.split('|')[-1].split('(')[0]
            cand = [c for c in find(g, last) if not c.startswith('ERR')][:6]
            out['faltan'][cual + ' :: ' + tid] = cand
    out['total'] = sum(len(v) for v in ids.values())
    return out
