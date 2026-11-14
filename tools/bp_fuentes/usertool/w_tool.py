# write_graphs.py - escribe bloques ";; ===== GRAFO: X" de un .dsl de Saved en un BP (execute_tool_script; IDEMPOTENTE).
# Reemplazar /Game/SoulCharger/Mechanics/UserTool/BP_UserTool_SC.BP_UserTool_SC (ruta paquete.objeto), usertool.dsl (archivo), ['ToolPose','PushColor','ToolHide','ToolMount','ToolAttach','ToolApply','ToolMorph','ToolAnim','ToolTick','ShowMando','ToSensor','SetSensorColor','Release','ConstructionScript'] (lista de grafos). Un grafo con cuerpo NO se reescribe.
import json
BT='editor_toolset.toolsets.blueprint.BlueprintTools.'
AT='editor_toolset.toolsets.asset.AssetTools.'
BPP='/Game/SoulCharger/Mechanics/UserTool/BP_UserTool_SC.BP_UserTool_SC'
DSL='C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/usertool/usertool.dsl'
ONLY=['ToolPose','PushColor','ToolHide','ToolMount','ToolAttach','ToolApply','ToolMorph','ToolAnim','ToolTick','ShowMando','ToSensor','SetSensorColor','Release','ConstructionScript']
ERRS=[]
def T(n,p):
    try:
        return True, execute_tool(n, json.dumps(p))['returnValue']
    except BaseException as e:
        ERRS.append(n.split('.')[-1]+' :: '+str(e)[:500]); return False, None
def blocks():
    ok,s=T(AT+'read_file',{'file_path':DSL})
    out=[]; cur=None; body=[]
    for ln in (s or '').split('\n'):
        if ln.startswith(';; ===== GRAFO: '):
            if cur: out.append((cur,'\n'.join(body).strip()))
            cur=ln[len(';; ===== GRAFO: '):].split(' ')[0]; body=[]
        elif cur and not ln.lstrip().startswith(';;'):
            body.append(ln)
    if cur: out.append((cur,'\n'.join(body).strip()))
    return out
def nlines(g):
    ok,cur=T(BT+'read_graph_dsl',{'graph':g})
    return len([x for x in str(cur).split('\n') if x.strip()])
def run():
    try:
        res={}
        for name,code in blocks():
            if name not in ONLY or not code: continue
            g={'refPath':BPP+':'+('UserConstructionScript' if name=='ConstructionScript' else name)}
            n0=nlines(g)
            if n0>1 and name!='EventGraph':
                res[name]='ya tenia cuerpo ('+str(n0)+')'; continue
            ok,r=T(BT+'write_graph_dsl',{'graph':g,'code':code})
            res[name]=('ok '+str(nlines(g))) if ok else ('FALLO '+ERRS[-1][:500])
        return {'res':res,'errores':ERRS[:6]}
    except BaseException as e:
        return {'errores':ERRS[:6]+['run :: '+str(e)[:300]]}
