# write_vida_graphs.py - escribe bloques de vida.dsl en BP_ValleyLife_SC (execute_tool_script; IDEMPOTENTE).
# Lee el DSL de Saved/ClaudeScripts/vida/vida_dsl.txt (copia de .claude/skills/unreal-vr/scripts/vida.dsl).
# Cambiar ONLY por tanda. Un grafo que ya tiene cuerpo NO se reescribe (gotcha 489: el script corre dos veces).
# EventGraph y VidaSnd NO van por aca (EventGraph: borrar antes los eventos fantasma; VidaSnd: cirugia B12).
import json
BT='editor_toolset.toolsets.blueprint.BlueprintTools.'
AT='editor_toolset.toolsets.asset.AssetTools.'
SC='editor_toolset.toolsets.scene.SceneTools.'
P='/Game/SoulCharger/Mechanics/Breath/Life/BP_ValleyLife_SC.BP_ValleyLife_SC:'
ONLY=__ONLY__
ERRS=[]
def T(n,p):
    try:
        return True, execute_tool(n, json.dumps(p))['returnValue']
    except BaseException as e:
        ERRS.append(n.split('.')[-1]+' :: '+str(e)[:400])
        return False, None
def canary():
    ok, acts = T(SC+'find_actors', {'name':'','tag':'','collision_channels':[]})
    if not ok: return -1
    return len([1 for x in acts if 'Test_Entering.Test_Entering:PersistentLevel.' in (x['refPath'] if isinstance(x, dict) else str(x))])
def blocks():
    ok,s=T(AT+'read_file',{'file_path':'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/vida/vida_dsl.txt'})
    out=[]; cur=None; body=[]
    for ln in s.split('\n'):
        if ln.startswith(';; ===== GRAFO: ') and not ln.startswith(';; ===== GRAFO: <'):
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
        a=canary()
        res={}
        for name,code in blocks():
            if name not in ONLY: continue
            g={'refPath':P+('UserConstructionScript' if name=='ConstructionScript' else name)}
            n0=nlines(g)
            if n0>1:
                res[name]='ya tenia cuerpo ('+str(n0)+')'; continue
            ok,r=T(BT+'write_graph_dsl',{'graph':g,'code':code})
            res[name]=('ok '+str(nlines(g))) if ok else ('FALLO '+ERRS[-1][:300])
        b=canary()
        return {'canario':str(a)+' -> '+str(b),'res':res,'errores':ERRS[:4]}
    except BaseException as e:
        return {'errores':ERRS[:4]+['run :: '+str(e)[:300]]}
