# p5_agilidad.py - decisiones de Narrativa (2026-09-30, agilidad): ExploreTime 20 -> 12, ToolDelay 1,5 -> 0,8 (BP_BreathStage_SC)
# e IntroTime 4 -> 2,5 (BP_BreathBlob_SC). CDO + compilar + guardar los BP; despues las INSTANCIAS de Test_Entering (re-buscadas
# tras el compile, gotcha 47). Lee antes y despues. Canario de actores. NO guarda el nivel.
import json
BT='editor_toolset.toolsets.blueprint.BlueprintTools.'
OT='editor_toolset.toolsets.object.ObjectTools.'
SC='editor_toolset.toolsets.scene.SceneTools.'
AT='editor_toolset.toolsets.asset.AssetTools.'
LVL='/Game/Test_Entering.Test_Entering:PersistentLevel.'
ST='/Game/SoulCharger/Mechanics/Breath/BP_BreathStage_SC'
BL='/Game/SoulCharger/Mechanics/Breath/BP_BreathBlob_SC'
SETS=[(ST,'BP_BreathStage_SC_C',{'exploreTime':12.0,'toolDelay':0.8}),(BL,'BP_BreathBlob_SC_C',{'introTime':2.5})]
ERRS=[]
def T(n,p):
    try:
        return True, execute_tool(n, json.dumps(p))['returnValue']
    except BaseException as e:
        ERRS.append(n.split('.')[-1]+' :: '+str(e)[:200]); return False, None
def rp(x): return x['refPath'] if isinstance(x,dict) else str(x)
def gp(ref,keys):
    ok,g=T(OT+'get_properties',{'instance':{'refPath':ref},'properties':keys})
    try: return json.loads(g)
    except BaseException: return g
def actors():
    ok,a=T(SC+'find_actors',{'name':'','tag':'','collision_channels':[]})
    return [rp(x) for x in (a or []) if LVL in rp(x)]
def one(acts,cn):
    m=[r for r in acts if (':PersistentLevel.'+cn+'_') in r]
    return m[0] if len(m)==1 else None
def run():
    try:
        rep={}; n0=len(actors())
        for path,cn,vals in SETS:
            bp={'refPath':path+'.'+path.split('/')[-1]}
            ok,cdo=T(BT+'get_default_object',{'blueprint':bp})
            rep[cn+'.cdo_antes']=gp(rp(cdo),list(vals.keys()))
            for k,v in vals.items():
                T(OT+'set_properties',{'instance':cdo,'values':json.dumps({k:v})})
            T(BT+'compile_blueprint',{'blueprint':bp})
            rep[cn+'.cdo']=gp(rp(cdo),list(vals.keys()))
            T(AT+'save_assets',{'asset_paths':[path]})
        acts=actors()
        for path,cn,vals in SETS:
            inst=one(acts,cn)
            if not inst: rep[cn+'.inst']='no encontrado'; continue
            rep[cn+'.inst_antes']=gp(inst,list(vals.keys()))
            for k,v in vals.items():
                T(OT+'set_properties',{'instance':{'refPath':inst},'values':json.dumps({k:v})})
            rep[cn+'.inst']=gp(inst,list(vals.keys()))
        rep['canario']=str(n0)+' -> '+str(len(actors()))
        return {'errores':ERRS[:10],'rep':rep}
    except BaseException as e:
        return {'errores':ERRS[:10]+['run :: '+str(e)[:300]]}
