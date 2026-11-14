# t0_recon.py - SOLO LECTURA. Junta todo lo que el turno necesita y lo escribe en Saved/ClaudeScripts/usertool/recon.json.
# Devuelve un resumen corto. execute_tool_script; no escribe nada en assets ni niveles.
import json
BT='editor_toolset.toolsets.blueprint.BlueprintTools.'
OT='editor_toolset.toolsets.object.ObjectTools.'
AT='editor_toolset.toolsets.asset.AssetTools.'
ACT='editor_toolset.toolsets.actor.ActorTools.'
SM='editor_toolset.toolsets.static_mesh.StaticMeshTools.'
MI='editor_toolset.toolsets.material_instance.MaterialInstanceTools.'
SC='editor_toolset.toolsets.scene.SceneTools.'
ERRS=[]
def T(n,p):
    try:
        return execute_tool(n, json.dumps(p))['returnValue']
    except BaseException as e:
        ERRS.append(n.split('.')[-1]+' '+json.dumps(p)[:120]+' :: '+str(e)[:200]); return None
M='/Game/SoulCharger/Mechanics/'
BPS={'stage':M+'Breath/BP_BreathStage_SC.BP_BreathStage_SC','blob':M+'Breath/BP_BreathBlob_SC.BP_BreathBlob_SC',
     'rig':M+'Breath/BP_BreathRig_SC.BP_BreathRig_SC','bio':M+'BioSensor/BP_BioSensorArt_SC.BP_BioSensorArt_SC',
     'pawn':'/Game/SoulCharger/Core/Pawn/BP_VRPawn_SC.BP_VRPawn_SC','tb':'/Game/NeuralCanvas/TB/BP_TBDirector_NC.BP_TBDirector_NC',
     'qc':M+'QuestController/BP_QuestCtrl_SC.BP_QuestCtrl_SC','pacer':M+'Pacer/BP_Pacer_SC.BP_Pacer_SC'}
GRAPHS={'stage':['EventGraph','StageTick','StageStart','TourCheck','TourCut','TourWake','StageIntro','StageBegin','StageOutro','StageFind'],
        'blob':['BlobApplyEnv','BlobEnvStep','BlobAppear','BlobDisappear','UserConstructionScript','EventGraph'],
        'pacer':['EventGraph'],
        'rig':['FindHand','FindHandMC'],'bio':['EventGraph','UserConstructionScript']}
XF=['relativeLocation','relativeRotation','relativeScale3D']
def props(ref, keys):
    g=T(OT+'get_properties',{'instance':{'refPath':ref},'properties':keys})
    try: return json.loads(g)
    except BaseException: return g
def run():
    try:
        out={}
        out['level']=T(SC+'get_current_level',{})
        for k in ('stage','blob','rig','bio','pacer'):
            bp={'refPath':BPS[k]}
            out[k+'.vars']=T(BT+'list_variables',{'blueprint':bp})
            out[k+'.graphs']=T(BT+'list_graphs',{'blueprint':bp})
            for g in GRAPHS.get(k,[]):
                out[k+'.dsl.'+g]=T(BT+'read_graph_dsl',{'graph':{'refPath':BPS[k]+':'+g}})
        # componentes del sensor de Mesh 3D (plantillas)
        cdo=T(BT+'get_default_object',{'blueprint':{'refPath':BPS['bio']}})
        out['bio.cdo']=cdo
        comps=T(ACT+'get_components',{'actor':cdo}) if cdo else None
        out['bio.comps']=comps
        for c in (comps or []):
            r=c['refPath'] if isinstance(c,dict) else str(c)
            nm=r.split('.')[-1]
            if 'DefaultSceneRoot' in nm or 'Appear' in nm: continue
            out['bio.comp.'+nm]=props(r, XF+['componentTags','staticMesh','overrideMaterials','castShadow','translucencySortPriority'])
            out['bio.comp.'+nm+'.parent']=T(ACT+'get_parent_component',{'component':{'refPath':r}})
        # pawn: manos respecto del grip; dibujo: mando NC respecto del grip; rig: sensor viejo
        for nm in ('HandRight','HandLeft'):
            r=BPS['pawn']+'_C:'+nm+'_GEN_VARIABLE'
            out['pawn.'+nm]=props(r, XF+['skeletalMeshAsset','skinnedAsset'])
            out['pawn.'+nm+'.parent']=T(ACT+'get_parent_component',{'component':{'refPath':r}})
        for nm in ('SM_RHand','SM_LHand'):
            out['tb.'+nm]=props(BPS['tb']+'_C:'+nm+'_GEN_VARIABLE', XF+['staticMesh'])
        for nm in ('SensR','SensL','CtrlR'):
            out['rig.'+nm]=props(BPS['rig']+'_C:'+nm+'_GEN_VARIABLE', XF+['staticMesh'])
        for nm in ('HandGhostR','HandGhostL'):
            out['rig.'+nm]=props(BPS['rig']+'_C:'+nm+'_GEN_VARIABLE', XF+['skeletalMeshAsset','skinnedAsset'])
        out['rig.GroupR']=props(BPS['rig']+'_C:GroupR_GEN_VARIABLE', XF)
        # materiales
        for m in ('Breath/M_BreathBlob_SC.M_BreathBlob_SC','Appear/M_SCLight_SC.M_SCLight_SC','Appear/M_SCObject_SC.M_SCObject_SC',
                  'BioSensor/M_BioSensorWaves_SC.M_BioSensorWaves_SC','QuestController/M_QuestCtrl_SC.M_QuestCtrl_SC'):
            out['params.'+m.split('/')[-1].split('.')[0]]=T(MI+'list_parameters',{'material':{'refPath':M+m}})
        for mi,pn in (('BioSensor/MI_BioSensor_Ring_SC.MI_BioSensor_Ring_SC','Color'),('BioSensor/MI_BioSensor_BackRing_SC.MI_BioSensor_BackRing_SC','Color'),
                      ('BioSensor/MI_BioSensor_TipLight_SC.MI_BioSensor_TipLight_SC','Color')):
            out['mi.'+mi.split('.')[-1]+'.'+pn]=T(MI+'get_vector_parameter',{'instance':{'refPath':M+mi},'name':pn})
        for s in ('Body_R','Body_L','Trigger_R','Trigger_L'):
            msh={'refPath':M+'QuestController/SM_QuestCtrl_'+s+'_SC.SM_QuestCtrl_'+s+'_SC'}
            sl=T(SM+'get_material_slots',{'mesh':msh}) or []
            out['qc.'+s]={'slots':sl,'mats':[T(SM+'get_material',{'mesh':msh,'slot_name':x}) for x in sl]}
        out['vo']=props('/Game/SoulCharger/Core/Audio/VO/Explora-Contador.Explora-Contador',['duration'])
        out['vo.class']=T(AT+'get_asset_class',{'asset_path':'/Game/SoulCharger/Core/Audio/VO/Explora-Contador'})
        for snd in ('/Game/SoulCharger/Calibration/Audio/Aparece','/Game/SoulCharger/Calibration/Audio/Tomado',
                    '/Game/SoulCharger/Calibration/Audio/Termino','/Game/NeuralCanvas/Sound/VR_shep_scale_up_01',
                    '/Game/NeuralCanvas/Sound/VR_shep_scale_up_02','/Game/NeuralCanvas/Sound/VR_shep_scale_down_02',
                    '/Game/SoulCharger/Core/Audio/Sounds/ProtoSelect','/Game/SoulCharger/Core/Audio/Sounds/SBubbleHoverOn',
                    '/Game/SoulCharger/Core/Audio/Sounds/SBubbleHoverOut','/Game/SoulCharger/Core/Audio/Sounds/Charge1'):
            nm=snd.split('/')[-1]
            out['snd.'+nm]={'class':T(AT+'get_asset_class',{'asset_path':snd}),'p':props(snd+'.'+nm,['duration'])}
        out['tool.exists']=T(AT+'exists',{'path':'/Game/SoulCharger/Mechanics/UserTool/BP_UserTool_SC'})
        out['vo12c.exists']=T(AT+'exists',{'path':'/Game/SoulCharger/Mechanics/Breath/Audio/VO_12c'})
        out['errores']=ERRS
        T(AT+'write_file',{'file_path':'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/usertool/recon.json','content':json.dumps(out,indent=1,default=str)})
        return {'claves':len(out),'errores':ERRS[:12],'level':out['level']}
    except BaseException as e:
        return {'errores':ERRS[:12]+['run :: '+str(e)[:300]]}
