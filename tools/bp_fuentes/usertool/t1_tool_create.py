# t1_tool_create.py - crea BP_UserTool_SC (duplicado de BP_BioSensorArt_SC) + componentes del mando y la mano fantasma
# + variables + grafos de funcion vacios con sus parametros. execute_tool_script; IDEMPOTENTE (el plugin a veces corre
# el script dos veces). NO escribe grafos (eso es t2). Termina compilando y guardando SOLO el BP nuevo.
import json
BT='editor_toolset.toolsets.blueprint.BlueprintTools.'
OT='editor_toolset.toolsets.object.ObjectTools.'
AT='editor_toolset.toolsets.asset.AssetTools.'
ACT='editor_toolset.toolsets.actor.ActorTools.'
SC='editor_toolset.toolsets.scene.SceneTools.'
ERRS=[]
def T(n,p):
    try:
        return True, execute_tool(n, json.dumps(p))['returnValue']
    except BaseException as e:
        ERRS.append(n.split('.')[-1]+' :: '+str(e)[:240]); return False, None
SRC='/Game/SoulCharger/Mechanics/BioSensor/BP_BioSensorArt_SC'
DIR='/Game/SoulCharger/Mechanics/UserTool'
PKG=DIR+'/BP_UserTool_SC'
BP={'refPath':PKG+'.BP_UserTool_SC'}
TPL=PKG+'.BP_UserTool_SC_C:'
QC='/Game/SoulCharger/Mechanics/QuestController/'
GHOST='/Game/XRMannequins/Meshes/SKM_MannyXR_right.SKM_MannyXR_right'
GHOST_PROP='skeletalMeshAsset'
VARS=[('Right','bool'),('ShowMandoOnBegin','bool'),('MorphTime','float'),('ColorTime','float'),('LightColor','LinearColor'),
      ('SensorXfR','Transform'),('SensorXfL','Transform'),('MandoXfR','Transform'),('MandoXfL','Transform'),('HandRelR','Transform'),
      ('Mode','int'),('ModeReq','int'),('PrevMode','int'),('Mounted','bool'),('MorphT','float'),('ColorT','float'),
      ('ColorFrom','LinearColor'),('ColorTo','LinearColor'),('MandoRest','Transform')]
OBJ=[('Hand','/Script/Engine.SceneComponent'),('Grip','/Script/Engine.SceneComponent'),('MandoSound','/Script/Engine.SoundBase')]
FUNCS=[('ToolPose',[]),('PushColor',[('C','LinearColor')]),('ToolHide',[]),('ToolMount',[]),('ToolAttach',[]),('ToolApply',[]),
       ('ToolMorph',[('DT','float')]),('ToolAnim',[('DT','float')]),('ToolTick',[('DT','float')]),('ShowMando',[('Right','bool')]),
       ('ToSensor',[('Color','LinearColor')]),('SetSensorColor',[('Color','LinearColor')]),('Release',[])]
def run():
    try:
        rep={}
        ok,ex=T(AT+'exists',{'path':PKG})
        if not ex:
            T(AT+'create_folder',{'path':DIR})
            T(AT+'duplicate',{'path':SRC,'new_path':PKG})
        ok,cdo=T(BT+'get_default_object',{'blueprint':BP})
        ok,comps=T(ACT+'get_components',{'actor':cdo})
        have=[(c['refPath'] if isinstance(c,dict) else str(c)).split('.')[-1].split(':')[-1] for c in (comps or [])]
        rep['comps_antes']=have
        for nm,typ in (('MandoBodyR','/Script/Engine.StaticMeshComponent'),('MandoTrigR','/Script/Engine.StaticMeshComponent'),
                       ('MandoBodyL','/Script/Engine.StaticMeshComponent'),('MandoTrigL','/Script/Engine.StaticMeshComponent'),
                       ('HandGhost','/Script/Engine.SkeletalMeshComponent')):
            if not any(h.startswith(nm) for h in have):
                T(ACT+'add_component',{'owner':cdo,'component_type':{'refPath':typ},'name':nm})
        T(BT+'compile_blueprint',{'blueprint':BP})
        c=lambda nm: {'refPath':TPL+nm+'_GEN_VARIABLE'}
        T(ACT+'set_parent_component',{'component':c('MandoTrigR'),'parent':c('MandoBodyR')})
        T(ACT+'set_parent_component',{'component':c('MandoTrigL'),'parent':c('MandoBodyL')})
        sets=[('MandoBodyR',{'staticMesh':{'refPath':QC+'SM_QuestCtrl_Body_R_SC.SM_QuestCtrl_Body_R_SC'}}),
              ('MandoTrigR',{'staticMesh':{'refPath':QC+'SM_QuestCtrl_Trigger_R_SC.SM_QuestCtrl_Trigger_R_SC'}}),
              ('MandoBodyL',{'staticMesh':{'refPath':QC+'SM_QuestCtrl_Body_L_SC.SM_QuestCtrl_Body_L_SC'}}),
              ('MandoTrigL',{'staticMesh':{'refPath':QC+'SM_QuestCtrl_Trigger_L_SC.SM_QuestCtrl_Trigger_L_SC'}}),
              ('MandoTrigR',{'relativeLocation':'(X=1.565000,Y=2.432000,Z=-0.145000)'}),
              ('MandoTrigL',{'relativeLocation':'(X=-1.565000,Y=2.432000,Z=-0.145000)'}),
              ('HandGhost',{GHOST_PROP:{'refPath':GHOST}}),('HandGhost',{'bHiddenInGame':True})]
        for nm in ('MandoBodyR','MandoTrigR','MandoBodyL','MandoTrigL','HandGhost'):
            sets+= [(nm,{'castShadow':False}),(nm,{'BodyInstance':{'collisionEnabled':'NoCollision','collisionProfileName':'NoCollision'}})]
        for nm,v in sets:
            T(OT+'set_properties',{'instance':c(nm),'values':json.dumps(v)})
        # variables
        ok,vs=T(BT+'list_variables',{'blueprint':BP})
        vh=set([str(x['name']) if isinstance(x,dict) else str(x) for x in (vs or [])])
        for n,t in VARS:
            vn=('b'+n) if t=='bool' else n
            if vn not in vh: T(BT+'add_variable',{'blueprint':BP,'name':vn,'type_name':t})
        for n,cls in OBJ:
            if n not in vh: T(BT+'add_object_variable',{'blueprint':BP,'name':n,'object_class':{'refPath':cls}})
        # funciones vacias + parametros
        ok,gs=T(BT+'list_graphs',{'blueprint':BP})
        gh=' '.join([str(g) for g in (gs or [])])
        for f,params in FUNCS:
            if (':'+f+"'") in gh or (':'+f+'"') in gh or gh.endswith(':'+f): continue
            ok,r=T(BT+'add_function_graph',{'blueprint':BP,'graph_name':f})
            for pn,pt in params:
                T(BT+'add_function_param',{'graph':{'refPath':PKG+'.BP_UserTool_SC:'+f},'param_name':pn,'param_type':pt,'input_param':True})
        T(BT+'compile_blueprint',{'blueprint':BP})
        ok,vs=T(BT+'list_variables',{'blueprint':BP})
        rep['vars']=len(vs or [])
        ok,gs=T(BT+'list_graphs',{'blueprint':BP})
        rep['graphs']=gs
        ok,comps=T(ACT+'get_components',{'actor':cdo})
        rep['comps']=[(c2['refPath'] if isinstance(c2,dict) else str(c2)).split(':')[-1] for c2 in (comps or [])]
        T(AT+'save_assets',{'asset_paths':[PKG]})
        return {'errores':ERRS[:14],'rep':rep}
    except BaseException as e:
        return {'errores':ERRS[:14]+['run :: '+str(e)[:300]]}
