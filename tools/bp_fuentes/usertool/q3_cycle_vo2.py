# q3_cycle_vo2.py - StepCycleVO v2 (mezcla de Beltran: "inhale" a 2,56 s < LeadIn 3): el pacer puede lanzarse en la fase 11,
# antes de la cuenta (ExploreTime + InhaleCueAt - LeadIn); reset del cue en fases 9/10 (no en la 11, donde ahora se puede lanzar).
# Rehace el grafo: borra todos los nodos menos la entrada y escribe cycle_vo2_dsl.txt. CDO InhaleCueAt -> 2,56. Con Test_Results abierto.
import json
BT='editor_toolset.toolsets.blueprint.BlueprintTools.'
OT='editor_toolset.toolsets.object.ObjectTools.'
AT='editor_toolset.toolsets.asset.AssetTools.'
BPP='/Game/SoulCharger/Mechanics/Breath/BP_BreathStage_SC.BP_BreathStage_SC'
BP={'refPath':BPP}; G={'refPath':BPP+':StepCycleVO'}
DSL='C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/usertool/cycle_vo2_dsl.txt'
MOVE=['bCycleVO','InhaleCueAt','CueLead','bPacerCued','CueStep','HoldSound','ExhaleSound','bContract']
ERRS=[]
def T(n,p):
    try:
        return True, execute_tool(n, json.dumps(p))['returnValue']
    except BaseException as e:
        ERRS.append(n.split('.')[-1]+' :: '+str(e)[:300]); return False, None
def g(d,k): return d[k] if k in d else ''
def run():
    try:
        rep={}
        ok,lv=T('editor_toolset.toolsets.scene.SceneTools.get_current_level',{})
        if lv and ('Test_Entering' in str(lv) or 'Obra' in str(lv)): return {'aviso':'abrir Test_Results antes: '+str(lv)}
        cats={}
        for n in MOVE:
            ok,c=T(BT+'get_variable_category',{'blueprint':BP,'variable_name':n}); cats[n]=c
            T(BT+'set_variable_category',{'blueprint':BP,'variable_name':n,'category':'Default'})
        ok,ns=T(BT+'find_nodes',{'graph':G,'title':''})
        refs=[n['refPath'] if isinstance(n,dict) else str(n) for n in (ns or [])]
        borr=[r for r in refs if 'FunctionEntry' not in r.split('.')[-1]]
        for r in borr: T(BT+'delete_node',{'node':{'refPath':r}})
        rep['borrados']=len(borr)
        ok,s=T(AT+'read_file',{'file_path':DSL})
        if isinstance(s,dict): s=g(s,'content') or g(s,'text') or ''
        T(BT+'write_graph_dsl',{'graph':G,'code':s.strip()})
        for n in MOVE:
            if cats[n]: T(BT+'set_variable_category',{'blueprint':BP,'variable_name':n,'category':cats[n]})
        T(BT+'compile_blueprint',{'blueprint':BP,'warnings_as_errors':True})
        ok,cdo=T(BT+'get_default_object',{'blueprint':BP})
        T(OT+'set_properties',{'instance':cdo,'values':json.dumps({'inhaleCueAt':2.56})})
        T(BT+'compile_blueprint',{'blueprint':BP,'warnings_as_errors':True})
        ok,v=T(OT+'get_properties',{'instance':cdo,'properties':['inhaleCueAt','countTime','exploreTime']}); rep['cdo']=v
        ok,d=T(BT+'read_graph_dsl',{'graph':G}); rep['dsl']=str(d)[:1400]
        ok,ns=T(BT+'find_nodes',{'graph':G,'title':''}); rep['nodos']=len(ns or [])
        T(AT+'save_assets',{'asset_paths':['/Game/SoulCharger/Mechanics/Breath/BP_BreathStage_SC']})
        return {'errores':ERRS[:10],'rep':rep}
    except BaseException as e:
        return {'errores':ERRS[:10]+['run :: '+str(e)[:300]]}
