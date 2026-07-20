# Limpieza de nodos huérfanos por VITALIDAD DIRIGIDA — validado 2026-07-20.
# Se corre con ProgrammaticToolset.execute_tool_script (NO es Python general).
# Borró 531 huérfanos en 4 BP de esta sesión (Step 645->226, FadeSphere EventGraph 118->40, etc.)
# con el DSL vivo IDÉNTICO byte por byte antes/después (lógica 100% preservada).
#
# QUIRKS DEL SANDBOX (verificados — no reintentar):
#   - Módulos permitidos: datetime, re, copy, math, json, time. NADA de collections (Counter falla).
#   - Los dicts que devuelven las tools son _StrictDict: NO soportan .get(k, default) -> usar `d[k] if k in d else X`.
#   - execute_tool(tool_name_COMPLETO, json_input) -> dict. Raise en error.
#   - Debe definir run() -> dict. Solo el dict de retorno vuelve al contexto (los listados gigantes no).
#
# MÉTODO (ver gotchas.md §LIMPIEZA): NO usar BFS no-dirigido (marca todo vivo por el pin de datos del entry).
#   Pasada 1: EXEC hacia adelante desde entradas, siguiendo SOLO pines type_id=='Exec'.
#   Pasada 2: cierre de DATOS hacia atrás sobre los vivos (fuentes de pines de entrada no-Exec).
#   Huérfano = no alcanzado y no es tipo entrada. Los tipos entrada NUNCA se borran.
#
# SEGURIDAD: antes de correr, backup en disco de los .uasset (no hay git). El script captura
#   read_graph_dsl ANTES y DESPUÉS por grafo y devuelve identical=(before==after): si es False,
#   NO guardar y hacer Ctrl+Z en el editor. Compilar + save_assets sólo si identical=True en todos.

import json, re
BP='editor_toolset.toolsets.blueprint.BlueprintTools.'
def gv(d,k):
    return d[k] if k in d else []
def tv(p):
    return p['type_id'] if 'type_id' in p else ''
def list_graphs(bp):
    return execute_tool(BP+'list_graphs', json.dumps({'blueprint':{'refPath':bp}}))['returnValue']
def find_nodes(g):
    return execute_tool(BP+'find_nodes', json.dumps({'graph':{'refPath':g},'title':''}))['returnValue']
def read_dsl(g):
    return execute_tool(BP+'read_graph_dsl', json.dumps({'graph':{'refPath':g}}))['returnValue']
def delete_node(r):
    return execute_tool(BP+'delete_node', json.dumps({'node':{'refPath':r}}))
def get_infos(refs):
    out=[]
    for i in range(0,len(refs),80):
        chunk=[{'refPath':r} for r in refs[i:i+80]]
        out+=execute_tool(BP+'get_node_infos', json.dumps({'nodes':chunk}))['returnValue']
    return out
ENTRY=('K2Node_FunctionEntry','K2Node_FunctionResult','K2Node_Event','K2Node_CustomEvent','K2Node_Tunnel','K2Node_EnhancedInputAction','K2Node_InputAction','K2Node_InputKey','K2Node_InputAxis','K2Node_ComponentBoundEvent','K2Node_ActorBoundEvent','K2Node_Timeline','K2Node_InputTouch')
def cls(ref):
    return ref.split('.')[-1]
def is_entry(ref):
    c=cls(ref)
    return any(c.startswith(p) for p in ENTRY)
def vitality(g):
    refs=[n['refPath'] for n in find_nodes(g)]
    if not refs: return [],set(),[]
    by={}
    for inf in get_infos(refs):
        by[inf['node']['refPath']]=inf
    live=set(r for r in refs if is_entry(r))
    stack=list(live)
    while stack:
        r=stack.pop(); inf=by[r] if r in by else None
        if not inf: continue
        for op in gv(inf,'output_pins'):
            if tv(op)=='Exec':
                for cp in gv(op,'connected_pins'):
                    t=cp['node']['refPath']
                    if t in by and t not in live:
                        live.add(t); stack.append(t)
    stack=list(live)
    while stack:
        r=stack.pop(); inf=by[r] if r in by else None
        if not inf: continue
        for ip in gv(inf,'input_pins'):
            if tv(ip)!='Exec':
                for cp in gv(ip,'connected_pins'):
                    s=cp['node']['refPath']
                    if s in by and s not in live:
                        live.add(s); stack.append(s)
    orphans=[r for r in refs if r not in live and not is_entry(r)]
    return refs,live,orphans
def clean_bp(bp, dry=True):
    out={}
    for g in list_graphs(bp):
        gp=g['refPath']; gn=gp.split(':')[-1]
        refs,live,orphans=vitality(gp)
        if not orphans: continue
        if dry:
            out[gn]={'total':len(refs),'live':len(refs)-len(orphans),'orphan':len(orphans)}
        else:
            before=read_dsl(gp)
            for r in orphans:
                delete_node(r)
            after=read_dsl(gp)
            out[gn]={'deleted':len(orphans),'remaining':len(refs)-len(orphans),'identical':(before==after)}
    return out
def run():
    # dry=True primero para revisar; dry=False para borrar. Compilar + save_assets aparte si identical.
    return clean_bp('/Game/SoulCharger/Stages/Breath/BP_BreathSensor_V2.BP_BreathSensor_V2', dry=True)
