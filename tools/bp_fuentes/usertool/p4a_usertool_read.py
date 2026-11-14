# p4a_usertool_read.py - SOLO LECTURA, con Test_Entering abierto: valores de autor de Entering_UserTool que difieren del CDO
# (variables A-Herramienta + transform relativo de los componentes visibles). Escribe usertool_vals.json para p4b (Obra).
# bShowMandoOnBegin NO se copia (flag de test). Nombres de propiedad como en t5_level.py (bools con b, resto camelCase).
import json
BT='editor_toolset.toolsets.blueprint.BlueprintTools.'
OT='editor_toolset.toolsets.object.ObjectTools.'
SC='editor_toolset.toolsets.scene.SceneTools.'
ACT='editor_toolset.toolsets.actor.ActorTools.'
AT='editor_toolset.toolsets.asset.AssetTools.'
BP={'refPath':'/Game/SoulCharger/Mechanics/UserTool/BP_UserTool_SC.BP_UserTool_SC'}
TPL='/Game/SoulCharger/Mechanics/UserTool/BP_UserTool_SC.BP_UserTool_SC_C:'
LVL='/Game/Test_Entering.Test_Entering:PersistentLevel.'
OUT='C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/usertool/usertool_vals.json'
KEYS=['bRight','morphTime','colorTime','lightColor','sensorXfR','sensorXfL','mandoXfR','mandoXfL','mandoSound']
COMPS=['Body','Button','Waves','Trace','MandoBodyR','MandoTrigR','MandoBodyL','MandoTrigL']
CK=['relativeLocation','relativeRotation','relativeScale3D']
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
def run():
    try:
        ok,a=T(SC+'find_actors',{'name':'','tag':'','collision_channels':[]})
        acts=[rp(x) for x in (a or []) if LVL in rp(x)]
        tl=[r for r in acts if ':PersistentLevel.BP_UserTool_SC_C_' in r]
        if len(tl)!=1: return {'errores':ERRS[:8],'aviso':'UserTool en Test_Entering: '+str(tl)}
        inst=tl[0]
        ok,cdo=T(BT+'get_default_object',{'blueprint':BP})
        vi=gp(inst,KEYS); vc=gp(rp(cdo),KEYS)
        dif={}
        if isinstance(vi,dict) and isinstance(vc,dict):
            for k in KEYS:
                if json.dumps(vi.get(k),sort_keys=True)!=json.dumps(vc.get(k),sort_keys=True): dif[k]=vi.get(k)
        ok,cs=T(ACT+'get_components',{'actor':{'refPath':inst}})
        have=[rp(c).split('.')[-1] for c in (cs or [])]
        cdif={}
        for nm in COMPS:
            if nm not in have: continue
            ci=gp(inst+'.'+nm,CK); cc=gp(TPL+nm+'_GEN_VARIABLE',CK)
            d={}
            if isinstance(ci,dict) and isinstance(cc,dict):
                for k in CK:
                    if json.dumps(ci.get(k),sort_keys=True)!=json.dumps(cc.get(k),sort_keys=True): d[k]=ci.get(k)
            if d: cdif[nm]=d
        out={'inst':inst,'vars_inst':vi,'vars_cdo':vc,'dif':dif,'comp_dif':cdif,'comps':have,
             'test_flag_bShowMandoOnBegin':gp(inst,['bShowMandoOnBegin'])}
        T(AT+'write_file',{'file_path':OUT,'content':json.dumps(out,indent=1,default=str)})
        return {'errores':ERRS[:8],'dif':dif,'comp_dif':cdif,'comps':have}
    except BaseException as e:
        return {'errores':ERRS[:8]+['run :: '+str(e)[:300]]}
