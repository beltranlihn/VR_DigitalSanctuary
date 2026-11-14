import json
# ghost_write.py - escribe los grafos de un BP desde <bp>_graphs.json (lo arma split_ghost.py). Idempotente: salta los
# grafos que ya tienen cuerpo (mas de 1 nodo; ninguna funcion de los fantasmas tiene salida, asi que "vacia" = 1 nodo,
# gotcha 541). El EventGraph de un Actor nuevo trae 3 eventos fantasma: se borran antes de escribir (una sola vez).
# Un error del DSL ESCAPA del try (gotchas): la corrida se corta en ese grafo. Se vuelve a correr y sigue desde ahi;
# 'hechos' dice hasta donde llego. Se pega ENTERO como `script` de execute_tool_script.
# CUAL = 'ghost_player' | 'ghost_recorder'  (cambiar antes de cada corrida)
CUAL = 'ghost_player'
DIR = 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/ghost/'
BT = 'editor_toolset.toolsets.blueprint.BlueprintTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
LOG = []


def T(name, payload):
    try:
        r = execute_tool(name, json.dumps(payload))
        v = r['returnValue'] if isinstance(r, dict) and ('returnValue' in r) else r
        return True, v
    except BaseException as e:
        LOG.append(name.split('.')[-1] + ' :: ' + str(e)[:200])
        return False, None


def nodes(g):
    ok, v = T(BT + 'find_nodes', {'graph': g, 'title': ''})
    return v or []


def run():
    ok, txt = T(AS + 'read_file', {'file_path': DIR + CUAL + '_graphs.json'})
    if not ok:
        return {'err': 'no pude leer ' + CUAL, 'log': LOG}
    d = json.loads(txt)
    hechos, saltados = [], []
    for g in d['order']:
        name = g.split(':')[-1]
        ns = nodes(g)
        if name == 'EventGraph':
            # ya escrito si hay algun nodo que no sea evento fantasma: con mas de 3 nodos se asume escrito
            if len(ns) > 3:
                saltados.append(name)
                continue
            for x in ns:
                T(BT + 'delete_node', {'node': {'refPath': x['refPath'] if isinstance(x, dict) else str(x)}})
        elif len(ns) > 1:
            saltados.append(name)
            continue
        execute_tool(BT + 'write_graph_dsl', json.dumps({'graph': g, 'code': d['code'][g]}))
        hechos.append(name)
    return {'cual': CUAL, 'hechos': hechos, 'saltados': len(saltados), 'total': len(d['order']), 'log': LOG[:20]}
