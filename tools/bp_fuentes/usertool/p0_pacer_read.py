# p0_pacer_read.py - SOLO LECTURA: el Custom de M_Pacer_SC (codigo + Inputs con sus conexiones), sus parametros, y del
# BP_Pacer_SC las categorias de las variables que usa PacerPushProg, el EventGraph y el CS. Escribe pacer_read.json.
import json
BT='editor_toolset.toolsets.blueprint.BlueprintTools.'
MT='editor_toolset.toolsets.material.MaterialTools.'
OT='editor_toolset.toolsets.object.ObjectTools.'
AT='editor_toolset.toolsets.asset.AssetTools.'
MI='editor_toolset.toolsets.material_instance.MaterialInstanceTools.'
MAT={'refPath':'/Game/SoulCharger/Mechanics/Pacer/M_Pacer_SC.M_Pacer_SC'}
BPP='/Game/SoulCharger/Mechanics/Pacer/BP_Pacer_SC.BP_Pacer_SC'
ERRS=[]
def T(n,p):
    try:
        return True, execute_tool(n, json.dumps(p))['returnValue']
    except BaseException as e:
        ERRS.append(n.split('.')[-1]+' :: '+str(e)[:200]); return False, None
def run():
    try:
        out={}
        ok,ex=T(MT+'get_expressions',{'material_or_function':MAT})
        refs=[e['refPath'] for e in (ex or [])]
        out['exprs']=[r.split(':')[-1] for r in refs]
        cus=[r for r in refs if 'Custom' in r.split(':')[-1]]
        out['customs']=cus
        for c in cus:
            ok,g=T(OT+'get_properties',{'instance':{'refPath':c},'properties':['Code','Description','OutputType']})
            out['code.'+c.split(':')[-1]]=g
            ok,g=T(OT+'get_properties',{'instance':{'refPath':c},'properties':['Inputs']})
            out['inputs.'+c.split(':')[-1]]=g
            ok,g=T(MT+'get_expression_inputs',{'expression':{'refPath':c}})
            out['conn.'+c.split(':')[-1]]=g
        ok,ps=T(MI+'list_parameters',{'material':MAT})
        out['params']=ps
        ok,vs=T(BT+'list_variables',{'blueprint':{'refPath':BPP}})
        out['bp.vars']=vs
        # instancia de Entering: ritmo real (solo nombres que EXISTEN: una propiedad inexistente tumba el script)
        vh=set([str(x['name']) if isinstance(x,dict) else str(x) for x in (vs or [])])
        want=[n for n in ('LeadIn','LeadOut','InhaleTime','Hold1Time','ExhaleTime','Hold2Time','Cycles','Preset','SizeCm','ClearCenter','LineWidth','bAutoPlay') if n in vh]
        ok,a=T('editor_toolset.toolsets.scene.SceneTools.find_actors',{'name':'','tag':'','collision_channels':[]})
        pl=[(x['refPath'] if isinstance(x,dict) else str(x)) for x in (a or [])]
        pl=[r for r in pl if 'Test_Entering.Test_Entering:PersistentLevel.BP_Pacer_SC_C_' in r]
        out['pacer.inst']=pl
        if len(pl)==1:
            cam=[(n if (n.startswith('b') and n[1:2].isupper()) else n[0].lower()+n[1:]) for n in want]
            ok,g=T(OT+'get_properties',{'instance':{'refPath':pl[0]},'properties':cam}); out['pacer.inst.vals']=g
        cats={}
        for n in ('Cycles','CycleIndex','T','Total','Mode','bInhaleToCenter','EnvT'):
            ok,c=T(BT+'get_variable_category',{'blueprint':{'refPath':BPP},'variable_name':n}); cats[n]=c
        out['bp.cats']=cats
        for g in ('EventGraph','UserConstructionScript','PacerPlay'):
            ok,d=T(BT+'read_graph_dsl',{'graph':{'refPath':BPP+':'+g}}); out['bp.dsl.'+g]=d
        out['errores']=ERRS
        T(AT+'write_file',{'file_path':'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/usertool/pacer_read.json','content':json.dumps(out,indent=1,default=str)})
        return {'claves':len(out),'customs':cus,'pacer':out.get('pacer.inst'),'ritmo':out.get('pacer.inst.vals'),'errores':ERRS[:8]}
    except BaseException as e:
        return {'errores':ERRS[:8]+['run :: '+str(e)[:300]]}
