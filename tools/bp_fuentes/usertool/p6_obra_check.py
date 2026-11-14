# p6_obra_check.py - SOLO LECTURA, con L_SoulCharger_Obra abierto: como encuentra BreathStage al UserTool (StageTool/StageFind),
# si Heart llama SetSensorColor/Release en StageIntro/StageOutro, y los UserTool del persistente. Escribe obra_check.json.
import json
BT='editor_toolset.toolsets.blueprint.BlueprintTools.'
SC='editor_toolset.toolsets.scene.SceneTools.'
AT='editor_toolset.toolsets.asset.AssetTools.'
ST='/Game/SoulCharger/Mechanics/Breath/BP_BreathStage_SC.BP_BreathStage_SC'
HM='/Game/SoulCharger/Mechanics/Heart/BP_HeartManager_SC.BP_HeartManager_SC'
LVL='/Game/SoulCharger/Obra/L_SoulCharger_Obra.L_SoulCharger_Obra:PersistentLevel.'
OUT='C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/usertool/obra_check.json'
ERRS=[]
def T(n,p):
    try:
        return True, execute_tool(n, json.dumps(p))['returnValue']
    except BaseException as e:
        ERRS.append(n.split('.')[-1]+' :: '+str(e)[:200]); return False, None
def rp(x): return x['refPath'] if isinstance(x,dict) else str(x)
GR={}
def dsl(bp,g):
    if bp not in GR:
        ok,gs=T(BT+'list_graphs',{'blueprint':{'refPath':bp}})
        GR[bp]=[rp(x).split(':')[-1] for x in (gs or [])]
    if g not in GR[bp]: return ''
    ok,d=T(BT+'read_graph_dsl',{'graph':{'refPath':bp+':'+g}}); return str(d)
def run():
    try:
        out={}
        for g in ('StageTool','StageFind'): out['stage.'+g]=dsl(ST,g)
        for g in ('StageIntro','StageOutro'): out['heart.'+g]=dsl(HM,g)
        ok,a=T(SC+'find_actors',{'name':'','tag':'','collision_channels':[]})
        acts=[rp(x) for x in (a or []) if LVL in rp(x)]
        out['n_actores']=len(acts)
        out['usertools']=[r for r in acts if 'BP_UserTool_SC_C' in r]
        out['errores']=ERRS
        T(AT+'write_file',{'file_path':OUT,'content':json.dumps(out,indent=1,default=str)})
        h=out['heart.StageIntro']+out['heart.StageOutro']
        return {'errores':ERRS[:8],'usertools':out['usertools'],'n':len(acts),
                'heart_llama_SetSensorColor':'SetSensorColor' in h and 'PrintString' not in h.split('SetSensorColor')[0][-80:],
                'heart_menciona':[k for k in ('SetSensorColor','Release','UserTool') if k in h]}
    except BaseException as e:
        return {'errores':ERRS[:8]+['run :: '+str(e)[:300]]}
