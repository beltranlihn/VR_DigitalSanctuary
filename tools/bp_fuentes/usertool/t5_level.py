# t5_level.py - Test_Entering: coloca la copia de prueba de BP_UserTool_SC (tag TestOnly) y escribe los flags de instancia.
# Lee ANTES y DESPUES (se anota en los trackers). execute_tool_script; IDEMPOTENTE. Canario de actores. NO guarda.
import json
OT='editor_toolset.toolsets.object.ObjectTools.'
SC='editor_toolset.toolsets.scene.SceneTools.'
ACT='editor_toolset.toolsets.actor.ActorTools.'
ERRS=[]
def T(n,p):
    try:
        return True, execute_tool(n, json.dumps(p))['returnValue']
    except BaseException as e:
        ERRS.append(n.split('.')[-1]+' :: '+str(e)[:200]); return False, None
LVL='/Game/Test_Entering.Test_Entering:PersistentLevel.'
def actors():
    ok,a=T(SC+'find_actors',{'name':'','tag':'','collision_channels':[]})
    return [(x['refPath'] if isinstance(x,dict) else str(x)) for x in (a or []) if LVL in (x['refPath'] if isinstance(x,dict) else str(x))]
def one(acts,cn):
    m=[r for r in acts if (':PersistentLevel.'+cn+'_') in r]
    return m[0] if len(m)==1 else None
def gp(ref,keys):
    ok,g=T(OT+'get_properties',{'instance':{'refPath':ref},'properties':keys})
    try: return json.loads(g)
    except BaseException: return g
def run():
    try:
        acts=actors(); a=len(acts); rep={}
        tool=one(acts,'BP_UserTool_SC_C')
        if not tool:
            T(SC+'add_to_scene_from_asset',{'asset_path':'/Game/SoulCharger/Mechanics/UserTool/BP_UserTool_SC','name':'Entering_UserTool','xform':{}})
            acts=actors(); tool=one(acts,'BP_UserTool_SC_C')
        if tool:
            t={'refPath':tool}
            ok,root=T(ACT+'get_root_component',{'actor':t})
            if root: T(OT+'set_properties',{'instance':root,'values':json.dumps({'relativeLocation':'(X=60.000000,Y=30.000000,Z=100.000000)'})})
            T(ACT+'set_label',{'actor':t,'label':'Entering_UserTool'})
            T(SC+'set_actor_folder',{'actor':t,'folder_path':'Entering'})
            ok,has=T(ACT+'has_tag',{'actor':t,'tag':'TestOnly'})
            if not has: T(ACT+'add_tag',{'actor':t,'tag':'TestOnly'})
            T(OT+'set_properties',{'instance':t,'values':json.dumps({'bShowMandoOnBegin':True})})
            rep['tool']={'ref':tool,'props':gp(tool,['bShowMandoOnBegin','bRight']),'tags':T(ACT+'get_tags',{'actor':t})[1],
                         'xf':T(ACT+'get_actor_transform',{'actor':t})[1]}
        rig=one(acts,'BP_BreathRig_SC_C')
        if rig:
            k=['bShowControllers','bShowSensors','bHideHands']
            b=gp(rig,k)
            T(OT+'set_properties',{'instance':{'refPath':rig},'values':json.dumps({'bShowControllers':False})})
            T(OT+'set_properties',{'instance':{'refPath':rig},'values':json.dumps({'bShowSensors':False})})
            T(OT+'set_properties',{'instance':{'refPath':rig},'values':json.dumps({'bHideHands':False})})
            rep['rig']={'antes':b,'despues':gp(rig,k)}
        st=one(acts,'BP_BreathStage_SC_C')
        if st:
            k=['bContractTest','bAutoStart','exploreTime','countTime','toolDelay','sensorColor','countSound']
            b=gp(st,k)
            T(OT+'set_properties',{'instance':{'refPath':st},'values':json.dumps({'bContractTest':True})})
            rep['stage']={'antes':b,'despues':gp(st,k)}
        bl=one(acts,'BP_BreathBlob_SC_C')
        if bl: rep['blob']=gp(bl,['introTime','outroTime','envT','morphScale','morphRadius','morphSpread'])
        rep['canario']=str(a)+' -> '+str(len(actors()))
        return {'errores':ERRS[:10],'rep':rep}
    except BaseException as e:
        return {'errores':ERRS[:10]+['run :: '+str(e)[:300]]}
