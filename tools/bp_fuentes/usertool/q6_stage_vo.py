import json
BT='editor_toolset.toolsets.blueprint.BlueprintTools.'
OT='editor_toolset.toolsets.object.ObjectTools.'
AT='editor_toolset.toolsets.asset.AssetTools.'
BPP='/Game/SoulCharger/Mechanics/Breath/BP_BreathStage_SC.BP_BreathStage_SC'
BP={'refPath':BPP}
D='C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/usertool/'
NUM=[('SayAfterTool','float','0-Contrato'),('SayGap','float','0-Contrato'),('HelpAfter','float','0-Contrato'),('SayStep','int','Z-Estado'),('SayEndAt','float','Z-Estado')]
OBJ=['ClipInstr','ClipExplore','ClipHelp','ClipReady']
TEMP=['bContract']
ERRS=[]
def T(n,p):
    try:
        return True, execute_tool(n, json.dumps(p))['returnValue']
    except BaseException as e:
        ERRS.append(n.split('.')[-1]+' :: '+str(e)[:300]); return False, None
def g(d,k): return d[k] if k in d else ''
def rp(x): return x['refPath'] if isinstance(x,dict) else str(x)
def pin(i,d,name):
    for p in i['input_pins' if d=='in' else 'output_pins']:
        if p['name']==name: return p
    return None
def rd(f):
    ok,s=T(AT+'read_file',{'file_path':D+f})
    if isinstance(s,dict): s=g(s,'content') or g(s,'text') or ''
    return (s or '').strip()
def run():
    try:
        rep={}
        ok,lv=T('editor_toolset.toolsets.scene.SceneTools.get_current_level',{})
        if lv and ('Test_Entering' in str(lv) or 'Obra' in str(lv)): return {'aviso':'abrir Test_Results: '+str(lv)}
        ok,vs=T(BT+'list_variables',{'blueprint':BP})
        vh=set([g(x,'name') if isinstance(x,dict) else str(x) for x in (vs or [])])
        for n,t,c in NUM:
            if n not in vh: T(BT+'add_variable',{'blueprint':BP,'name':n,'type_name':t})
        for n in OBJ:
            if n not in vh: T(BT+'add_object_variable',{'blueprint':BP,'name':n,'object_class':{'refPath':'/Script/Engine.SoundBase'}})
        for n in [x[0] for x in NUM if x[2]=='0-Contrato']+OBJ:
            T(BT+'set_variable_instance_editable',{'blueprint':BP,'variable_name':n,'instance_editable':True})
        ok,gs=T(BT+'list_graphs',{'blueprint':BP})
        names=[rp(x).split(':')[-1] for x in (gs or [])]
        if 'StageSay' not in names:
            T(BT+'add_function_graph',{'blueprint':BP,'graph_name':'StageSay'})
            T(BT+'add_object_function_param',{'graph':{'refPath':BPP+':StageSay'},'param_name':'Clip','object_class':{'refPath':'/Script/Engine.SoundBase'},'input_param':True})
        if 'StepStageVO' not in names:
            T(BT+'add_function_graph',{'blueprint':BP,'graph_name':'StepStageVO'})
            T(BT+'add_function_param',{'graph':{'refPath':BPP+':StepStageVO'},'param_name':'DT','param_type':'float','input_param':True})
        cats={}
        for n in [x[0] for x in NUM]+OBJ+TEMP:
            ok,c=T(BT+'get_variable_category',{'blueprint':BP,'variable_name':n}); cats[n]=c
            T(BT+'set_variable_category',{'blueprint':BP,'variable_name':n,'category':'Default'})
        T(BT+'compile_blueprint',{'blueprint':BP})
        for gname,f in (('StageSay','stage_say_dsl.txt'),('StepStageVO','stage_step_dsl.txt')):
            gr={'refPath':BPP+':'+gname}
            ok,cur=T(BT+'read_graph_dsl',{'graph':gr})
            if len([x for x in str(cur).split('\n') if x.strip()])<=1:
                T(BT+'write_graph_dsl',{'graph':gr,'code':rd(f)})
            ok,cur=T(BT+'read_graph_dsl',{'graph':gr}); rep[gname]=str(cur)[:900]
        # Tick: StageTick -> StepStageVO -> ContractStep
        ok,eg=T(BT+'read_graph_dsl',{'graph':{'refPath':BPP+':EventGraph'}})
        if 'StepStageVO' not in str(eg):
            ok,ns=T(BT+'find_nodes',{'graph':{'refPath':BPP+':EventGraph'},'title':''})
            ok,inf=T(BT+'get_node_infos',{'nodes':ns or []})
            cs=[i for i in (inf or []) if str(g(i,'type_id')).endswith('ContractStep')]
            if len(cs)!=1: return {'errores':ERRS[:8],'aviso':'ContractStep: '+str(len(cs)),'rep':rep}
            cs=cs[0]; ex=pin(cs,'in','execute'); dt=pin(cs,'in','DT')
            srcs=list(ex['connected_pins']); dts=list(dt['connected_pins'])
            p=cs['position'] if 'position' in cs else {'x':0,'y':0}
            ok,cn=T(BT+'create_node',{'graph':{'refPath':BPP+':EventGraph'},'type_id':'CallFunction|StepStageVO','pos':{'x':p['x']-40,'y':p['y']-220}})
            ok,ni=T(BT+'get_node_infos',{'nodes':[{'refPath':rp(cn)}]}); ni=ni[0]
            for s0 in srcs: T(BT+'break_pins',{'output_pin':s0,'input_pin':ex['pin_id']})
            for s0 in srcs: T(BT+'connect_pins',{'output_pin':s0,'input_pin':pin(ni,'in','execute')['pin_id']})
            T(BT+'connect_pins',{'output_pin':pin(ni,'out','then')['pin_id'],'input_pin':ex['pin_id']})
            if dts: T(BT+'connect_pins',{'output_pin':dts[0],'input_pin':pin(ni,'in','DT')['pin_id']})
            rep['tick']=[len(srcs),len(dts)]
        for n,t,c in NUM: T(BT+'set_variable_category',{'blueprint':BP,'variable_name':n,'category':c})
        for n in OBJ: T(BT+'set_variable_category',{'blueprint':BP,'variable_name':n,'category':'0-Contrato'})
        for n in TEMP:
            if cats[n]: T(BT+'set_variable_category',{'blueprint':BP,'variable_name':n,'category':cats[n]})
        T(BT+'compile_blueprint',{'blueprint':BP,'warnings_as_errors':True})
        ok,cdo=T(BT+'get_default_object',{'blueprint':BP})
        A='/Game/SoulCharger/Obra/Audio/'
        for k,v in (('sayAfterTool',1.0),('sayGap',0.5),('helpAfter',4.0),('clipInstr',{'refPath':A+'VO_11.VO_11'}),('clipExplore',{'refPath':A+'VO_11b.VO_11b'}),('clipHelp',{'refPath':A+'VO_11h.VO_11h'}),('clipReady',{'refPath':A+'VO_12.VO_12'})):
            T(OT+'set_properties',{'instance':cdo,'values':json.dumps({k:v})})
        T(BT+'compile_blueprint',{'blueprint':BP,'warnings_as_errors':True})
        ok,v=T(OT+'get_properties',{'instance':cdo,'properties':['sayAfterTool','sayGap','helpAfter','clipInstr','clipExplore','clipHelp','clipReady']}); rep['cdo']=v
        ok,eg=T(BT+'read_graph_dsl',{'graph':{'refPath':BPP+':EventGraph'}}); e=str(eg); k=e.find('EventTick'); rep['tick_dsl']=e[k:k+300]
        T(AT+'save_assets',{'asset_paths':['/Game/SoulCharger/Mechanics/Breath/BP_BreathStage_SC']})
        return {'errores':ERRS[:10],'rep':rep}
    except BaseException as e:
        return {'errores':ERRS[:10]+['run :: '+str(e)[:300]]}
