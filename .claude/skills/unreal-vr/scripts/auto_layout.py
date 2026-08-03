# Auto-layout de un EventGraph/función grande — validado 2026-07-30:
#   BP_CalibDirector:EventGraph (263 nodos, 262 colocados) y BP_BreathSensor_V2:Step (231, 231, el pipeline frágil) — ambos identical=true.
# Funciona igual en EventGraph (varios eventos = varias bandas) y en FUNCIÓN (una sola raíz FunctionEntry).
# Se corre con ProgrammaticToolset.execute_tool_script (NO es Python general — mismos quirks que clean_orphans.py:
#   módulos: json/math/re/datetime/copy/time; dicts _StrictDict sin .get; execute_tool(nombre_COMPLETO, json)->dict; run()->dict).
#
# QUÉ HACE: reordena TODOS los nodos aplicando la convención de bp-layout.md sin traer los nodos al contexto del modelo:
#   - Fila de exec izquierda->derecha: columna X = profundidad de exec (DFS desde cada evento), paso SX.
#   - Un CARRIL por rama: en un branch/switch, la 1a salida sigue en el mismo Y, las demás abren carril nuevo (low+SYL) -> no se pisan.
#   - Cada EVENTO en su propia BANDA vertical (BAND de separación), ordenados por su Y original (estable).
#   - Nodos de DATOS (getters/math puros, sin pin Exec) DEBAJO de su consumidor (apilados si comparten consumidor).
#   - Islas de exec sin evento -> banda extra al final.
# SEGURIDAD: set_node_position es COSMÉTICO (no toca lógica ni cables). Igual captura read_graph_dsl antes/después
#   y devuelve identical=(before==after) como prueba. Si sale False, algo raro pasó -> NO guardar, Ctrl+Z.
# LÍMITES (heredados de trabajar a ciegas, ver bp-layout.md): no clava el straighten fino (el humano da Q) ni crea
#   comment boxes; los datos muy compartidos pueden dejar cables largos. Da el ~85% — "suficiente para ordenar después".
#
# USO: cambiar G al grafo objetivo. Correr. Después: compile + save. Un getter SIN consumidor queda en 'unplaced'
#   (es huérfano; el layout no lo puede ubicar) -> moverlo a mano o borrarlo con clean_orphans.py.

import json
BP='editor_toolset.toolsets.blueprint.BlueprintTools.'
G='/Game/SoulCharger/Calibration/BP_CalibDirector.BP_CalibDirector:EventGraph'  # <-- editar

# --- tuning de la convención (medidas del usuario, BlueprintTestOrden) ---
SX=380      # paso horizontal por capa de exec
SYL=230     # separación vertical entre carriles (ramas de un branch/switch)
BAND=3200   # separación vertical entre eventos
DATA_DY=180 # datos: cuánto debajo del consumidor
DATA_DX=60  # datos: cuánto a la izquierda del consumidor
STK=150     # datos: apilado cuando varios cuelgan del mismo consumidor

def gv(d,k):
    return d[k] if k in d else []
def tv(p):
    return p['type_id'] if 'type_id' in p else ''
def find_nodes():
    return execute_tool(BP+'find_nodes', json.dumps({'graph':{'refPath':G},'title':''}))['returnValue']
def read_dsl():
    return execute_tool(BP+'read_graph_dsl', json.dumps({'graph':{'refPath':G}}))['returnValue']
def get_infos(refs):
    out=[]; i=0
    while i<len(refs):
        chunk=[{'refPath':r} for r in refs[i:i+80]]
        out+=execute_tool(BP+'get_node_infos', json.dumps({'nodes':chunk}))['returnValue']
        i+=80
    return out
def setpos(r,x,y):
    execute_tool(BP+'set_node_position', json.dumps({'node':{'refPath':r},'pos':{'x':int(x),'y':int(y)}}))

ENTRY=('K2Node_FunctionEntry','K2Node_Event','K2Node_CustomEvent','K2Node_Tunnel','K2Node_EnhancedInputAction','K2Node_InputAction','K2Node_ComponentBoundEvent','K2Node_ActorBoundEvent','K2Node_InputKey','K2Node_Timeline')
def cls(r):
    return r.split('.')[-1]
def is_root(r):
    # raíces del layout = FUENTES de exec (evento / FunctionEntry). NUNCA FunctionResult:
    # es un sumidero (tiene exec IN, no OUT) -> si fuera raíz quedaría mal en col 0.
    # Se coloca solo, al final de su cadena, como sucesor normal.
    c=cls(r)
    if c.startswith('K2Node_FunctionResult'):
        return False
    for p in ENTRY:
        if c.startswith(p):
            return True
    return False

def run():
    before=read_dsl()
    refs=[n['refPath'] for n in find_nodes()]
    by={}
    for inf in get_infos(refs):
        by[inf['node']['refPath']]=inf
    def has_exec(inf):
        for p in gv(inf,'input_pins')+gv(inf,'output_pins'):
            if tv(p)=='Exec':
                return True
        return False
    is_exec={}
    for r in refs:
        is_exec[r]=has_exec(by[r])
    def esuccs(r):
        inf=by[r]; res=[]
        ops=[p for p in gv(inf,'output_pins') if tv(p)=='Exec']
        ops.sort(key=lambda p:p['pin_id']['index_id'])
        for op in ops:
            for cp in gv(op,'connected_pins'):
                t=cp['node']['refPath']
                if t in by:
                    res.append(t)
        return res
    def consumers(r):
        inf=by[r]; cons=[]
        for op in gv(inf,'output_pins'):
            if tv(op)=='Exec':
                continue
            for cp in gv(op,'connected_pins'):
                t=cp['node']['refPath']
                if t in by:
                    cons.append(t)
        return cons
    placed={}; low=[0]
    def layout(r,col,y):
        if r in placed:
            return
        placed[r]=(col*SX,y)
        if y>low[0]:
            low[0]=y
        ss=[s for s in esuccs(r) if s not in placed]
        first=True
        for s in ss:
            if s in placed:
                continue
            if first:
                layout(s,col+1,y); first=False
            else:
                low[0]+=SYL
                layout(s,col+1,low[0])
    roots=[r for r in refs if is_root(r)]
    roots.sort(key=lambda r: by[r]['position']['y'])
    for i in range(len(roots)):
        base=i*BAND; low[0]=base
        layout(roots[i],0,base)
    extra=(len(roots)+1)*BAND
    for r in refs:
        if is_exec[r] and r not in placed:
            low[0]=extra; layout(r,0,extra); extra=low[0]+BAND
    slot={}; changed=True; guard=0
    while changed and guard<30:
        changed=False; guard+=1
        for r in refs:
            if is_exec[r] or r in placed:
                continue
            cs=[c for c in consumers(r) if c in placed]
            if not cs:
                continue
            cx=min(placed[c][0] for c in cs)
            cy=min(placed[c][1] for c in cs if placed[c][0]==cx)
            key=str(cx)+','+str(cy)
            k=slot[key] if key in slot else 0
            slot[key]=k+1
            placed[r]=(cx-DATA_DX, cy+DATA_DY+k*STK)
            changed=True
    for r in placed:
        x,y=placed[r]; setpos(r,x,y)
    after=read_dsl()
    return {'total':len(refs),'placed':len(placed),'roots':[cls(r) for r in roots],'unplaced':[cls(r) for r in refs if r not in placed],'identical':(before==after)}
