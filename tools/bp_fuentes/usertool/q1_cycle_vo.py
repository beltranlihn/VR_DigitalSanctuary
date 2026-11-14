# q1_cycle_vo.py - BP_BreathStage_SC (correr con Test_Results o TestMeshes abierto, NUNCA con Test_Entering ni la Obra):
# variables nuevas + StepCycleVO(DT) por DSL + StepCycleVO en el Tick despues de ContractStep + sacar PacerPlay de la rama
# 11->12 de ContractStep. NO escribe defaults (eso es q2, despues de compilar). IDEMPOTENTE. Compila y guarda solo el BP.
import json
BT='editor_toolset.toolsets.blueprint.BlueprintTools.'
AT='editor_toolset.toolsets.asset.AssetTools.'
BPP='/Game/SoulCharger/Mechanics/Breath/BP_BreathStage_SC.BP_BreathStage_SC'
BP={'refPath':BPP}
DSL='C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/usertool/cycle_vo_dsl.txt'
NEW=[('bCycleVO','bool','0-Contrato',True),('InhaleCueAt','float','0-Contrato',True),('CueLead','float','0-Contrato',True),
     ('bPacerCued','bool','Z-Estado',False),('CueStep','int','Z-Estado',False)]
OBJ=[('HoldSound','0-Contrato'),('ExhaleSound','0-Contrato')]
TEMP=['bContract']
ERRS=[]
def T(n,p):
    try:
        return True, execute_tool(n, json.dumps(p))['returnValue']
    except BaseException as e:
        ERRS.append(n.split('.')[-1]+' :: '+str(e)[:300]); return False, None
def g(d,k): return d[k] if k in d else ''
def rp(x): return x['refPath'] if isinstance(x,dict) else str(x)
def infos(graph):
    ok,ns=T(BT+'find_nodes',{'graph':{'refPath':BPP+':'+graph},'title':''})
    ok,inf=T(BT+'get_node_infos',{'nodes':ns or []})
    return inf or []
def pin(i,d,name):
    for p in i['input_pins' if d=='in' else 'output_pins']:
        if p['name']==name: return p
    return None
def run():
    try:
        rep={}
        ok,lv=T('editor_toolset.toolsets.scene.SceneTools.get_current_level',{})
        if lv and ('Test_Entering' in str(lv) or 'Obra' in str(lv)):
            return {'aviso':'nivel abierto '+str(lv)+': abrir Test_Results o TestMeshes antes'}
        ok,vs=T(BT+'list_variables',{'blueprint':BP})
        vh=set([g(x,'name') if isinstance(x,dict) else str(x) for x in (vs or [])])
        for n,t,c,ed in NEW:
            if n not in vh: T(BT+'add_variable',{'blueprint':BP,'name':n,'type_name':t})
            if ed: T(BT+'set_variable_instance_editable',{'blueprint':BP,'variable_name':n,'instance_editable':True})
        for n,c in OBJ:
            if n not in vh: T(BT+'add_object_variable',{'blueprint':BP,'name':n,'object_class':{'refPath':'/Script/Engine.SoundBase'}})
            T(BT+'set_variable_instance_editable',{'blueprint':BP,'variable_name':n,'instance_editable':True})
        ok,gs=T(BT+'list_graphs',{'blueprint':BP})
        names=[rp(x).split(':')[-1] for x in (gs or [])]
        if 'StepCycleVO' not in names:
            T(BT+'add_function_graph',{'blueprint':BP,'graph_name':'StepCycleVO'})
            T(BT+'add_function_param',{'graph':{'refPath':BPP+':StepCycleVO'},'param_name':'DT','param_type':'float','input_param':True})
        cats={}
        for n in [x[0] for x in NEW]+[x[0] for x in OBJ]+TEMP:
            ok,c=T(BT+'get_variable_category',{'blueprint':BP,'variable_name':n}); cats[n]=c
            T(BT+'set_variable_category',{'blueprint':BP,'variable_name':n,'category':'Default'})
        rep['cats_antes']={k:cats[k] for k in TEMP}
        T(BT+'compile_blueprint',{'blueprint':BP})
        # DSL (solo si el grafo esta vacio)
        ok,s=T(AT+'read_file',{'file_path':DSL})
        if isinstance(s,dict): s=g(s,'content') or g(s,'text') or ''
        gr={'refPath':BPP+':StepCycleVO'}
        ok,cur=T(BT+'read_graph_dsl',{'graph':gr})
        if len([x for x in str(cur).split('\n') if x.strip()])<=1:
            T(BT+'write_graph_dsl',{'graph':gr,'code':s.strip()})
        ok,cur=T(BT+'read_graph_dsl',{'graph':gr}); rep['dsl']=str(cur)[:2500]
        # Tick: ContractStep -> StepCycleVO -> (lo que seguia), DT del mismo origen que ContractStep
        ok,eg=T(BT+'read_graph_dsl',{'graph':{'refPath':BPP+':EventGraph'}})
        if 'StepCycleVO' not in str(eg):
            inf=infos('EventGraph')
            cs=[i for i in inf if str(g(i,'type_id')).endswith('ContractStep')]
            if len(cs)!=1: return {'errores':ERRS[:8],'aviso':'ContractStep en el Tick: '+str(len(cs)),'rep':rep}
            cs=cs[0]; th=pin(cs,'out','then'); dt=pin(cs,'in','DT')
            nxt=list(th['connected_pins']); src=list(dt['connected_pins'])
            p=cs['position'] if 'position' in cs else {'x':0,'y':0}
            ok,cn=T(BT+'create_node',{'graph':{'refPath':BPP+':EventGraph'},'type_id':'CallFunction|StepCycleVO','pos':{'x':p['x']+60,'y':p['y']+220}})
            ok,ni=T(BT+'get_node_infos',{'nodes':[{'refPath':rp(cn)}]}); ni=ni[0]
            for d in nxt: T(BT+'break_pins',{'output_pin':th['pin_id'],'input_pin':d})
            T(BT+'connect_pins',{'output_pin':th['pin_id'],'input_pin':pin(ni,'in','execute')['pin_id']})
            for d in nxt: T(BT+'connect_pins',{'output_pin':pin(ni,'out','then')['pin_id'],'input_pin':d})
            if src: T(BT+'connect_pins',{'output_pin':src[0],'input_pin':pin(ni,'in','DT')['pin_id']})
            rep['tick_inserto']=[len(nxt),len(src)]
        # ContractStep: el PacerPlay sale de la rama 11->12 (lo lanza StepCycleVO a InhaleCueAt - LeadIn)
        inf=infos('ContractStep')
        pp=[i for i in inf if 'PacerPlay' in str(g(i,'type_id'))]
        if len(pp)==1:
            pp=pp[0]; ex=pin(pp,'in','execute'); th=pin(pp,'out','then')
            if th['connected_pins']: return {'errores':ERRS[:8],'aviso':'PacerPlay tiene salida conectada; revisar','rep':rep}
            for s0 in list(ex['connected_pins']): T(BT+'break_pins',{'output_pin':s0,'input_pin':ex['pin_id']})
            tgt=[c['node']['refPath'] for p0 in pp['input_pins'] if g(p0,'type_id')!='Exec' for c in p0['connected_pins']]
            T(BT+'delete_node',{'node':{'refPath':pp['node']['refPath']}})
            for t in tgt:
                ok,ti=T(BT+'get_node_infos',{'nodes':[{'refPath':t}]})
                if ti and all(len(o['connected_pins'])==0 for o in ti[0]['output_pins']): T(BT+'delete_node',{'node':{'refPath':t}})
            rep['contractstep']='PacerPlay fuera de la rama 11->12'
        else:
            rep['contractstep']='PacerPlay en ContractStep: '+str(len(pp))+' (0 = ya hecho)'
        # categorias
        for n,t,c,ed in NEW: T(BT+'set_variable_category',{'blueprint':BP,'variable_name':n,'category':c})
        for n,c in OBJ: T(BT+'set_variable_category',{'blueprint':BP,'variable_name':n,'category':c})
        for n in TEMP:
            if cats.get(n): T(BT+'set_variable_category',{'blueprint':BP,'variable_name':n,'category':cats[n]})
        T(BT+'compile_blueprint',{'blueprint':BP,'warnings_as_errors':True})
        ok,eg=T(BT+'read_graph_dsl',{'graph':{'refPath':BPP+':EventGraph'}}); e=str(eg); k=e.find('ContractStep'); rep['tick']=e[max(0,k-200):k+300]
        ok,c2=T(BT+'read_graph_dsl',{'graph':{'refPath':BPP+':ContractStep'}}); c2=str(c2); k=c2.find('three'); rep['cs']=c2[k-40:k+260]
        T(AT+'save_assets',{'asset_paths':['/Game/SoulCharger/Mechanics/Breath/BP_BreathStage_SC']})
        return {'errores':ERRS[:10],'rep':rep}
    except BaseException as e:
        return {'errores':ERRS[:10]+['run :: '+str(e)[:300]]}
