# p2_pacer_bp.py - BP_Pacer_SC: perillas del progreso + PacerPushProg (DSL) + cirugia en el Tick (despues de
# PacerEnvelopeStep, antes del if bRunning: corre SIEMPRE, asi la pausa de entrada muestra 0 y la de salida el arco lleno)
# y al final del Construction Script (se ve scrubbeando T en el editor). Instancia Entering_Pacer: las variables nuevas
# nacen en 0 en el nivel abierto -> se escriben (gotcha 518). IDEMPOTENTE. Compila y guarda el BP (el nivel va aparte).
import json
BT='editor_toolset.toolsets.blueprint.BlueprintTools.'
OT='editor_toolset.toolsets.object.ObjectTools.'
AT='editor_toolset.toolsets.asset.AssetTools.'
BPP='/Game/SoulCharger/Mechanics/Pacer/BP_Pacer_SC.BP_Pacer_SC'
BP={'refPath':BPP}
INST=None  # se busca en run() (find_actors): nada de rutas fijas de instancia
DSL='C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/usertool/pacer_prog_dsl.txt'
NEW=[('bShowProgress','bool',True),('ProgRadius','float',-0.035),('ProgAmt','float',1.0)]
USED=['Cycles','CycleIndex','T','Total']
ERRS=[]
def T(n,p):
    try:
        return True, execute_tool(n, json.dumps(p))['returnValue']
    except BaseException as e:
        ERRS.append(n.split('.')[-1]+' :: '+str(e)[:300]); return False, None
def camel(n): return n if (n.startswith('b') and n[1:2].isupper()) else n[0].lower()+n[1:]
def info(ref):
    ok,i=T(BT+'get_node_infos',{'nodes':[{'refPath':ref}]})
    d=i[0] if isinstance(i,list) else i
    if isinstance(d,str): d=json.loads(d)
    return d
def node(graph,title):
    ok,ns=T(BT+'find_nodes',{'graph':{'refPath':BPP+':'+graph},'title':title})
    rs=[(n['refPath'] if isinstance(n,dict) else str(n)) for n in (ns or [])]
    return rs[0] if rs else None
def pin(d,side,name):
    ps=d['output_pins' if side=='o' else 'input_pins']
    m=[p for p in ps if p['name']==name]
    return m[0] if m else None
def run():
    global INST
    try:
        rep={}
        ok,a=T('editor_toolset.toolsets.scene.SceneTools.find_actors',{'name':'','tag':'','collision_channels':[]})
        pl=[(x['refPath'] if isinstance(x,dict) else str(x)) for x in (a or [])]
        pl=[r for r in pl if 'Test_Entering.Test_Entering:PersistentLevel.BP_Pacer_SC_C_' in r]
        if len(pl)!=1: return {'errores':ERRS[:8],'aviso':'pacer de Test_Entering: '+str(pl)}
        INST=pl[0]
        ok,vs=T(BT+'list_variables',{'blueprint':BP})
        vh=set([str(x) for x in (vs or [])])
        for n,t,d in NEW:
            if n not in vh: T(BT+'add_variable',{'blueprint':BP,'name':n,'type_name':t})
            T(BT+'set_variable_instance_editable',{'blueprint':BP,'variable_name':n,'instance_editable':True})
        ok,gs=T(BT+'list_graphs',{'blueprint':BP})
        names=[(g['refPath'] if isinstance(g,dict) else str(g)).split(':')[-1] for g in (gs or [])]
        if 'PacerPushProg' not in names:
            T(BT+'add_function_graph',{'blueprint':BP,'graph_name':'PacerPushProg'})
        cats={}
        for n in USED:
            ok,c=T(BT+'get_variable_category',{'blueprint':BP,'variable_name':n}); cats[n]=c
            T(BT+'set_variable_category',{'blueprint':BP,'variable_name':n,'category':'Default'})
        rep['cats_antes']=cats
        T(BT+'compile_blueprint',{'blueprint':BP})
        ok,cdo=T(BT+'get_default_object',{'blueprint':BP})
        for n,t,d in NEW:
            T(OT+'set_properties',{'instance':cdo,'values':json.dumps({camel(n):d})})
        ok,ia=T(OT+'get_properties',{'instance':{'refPath':INST},'properties':[camel(n) for n,t,d in NEW]})
        rep['inst_antes']=ia
        for n,t,d in NEW:
            T(OT+'set_properties',{'instance':{'refPath':INST},'values':json.dumps({camel(n):d})})
        # DSL
        ok,s=T(AT+'read_file',{'file_path':DSL})
        code='\n'.join(l for l in (s or '').split('\n') if not l.lstrip().startswith(';;')).strip()
        g={'refPath':BPP+':PacerPushProg'}
        ok,cur=T(BT+'read_graph_dsl',{'graph':g})
        if len([x for x in str(cur).split('\n') if x.strip()])<=1:
            T(BT+'write_graph_dsl',{'graph':g,'code':code})
        ok,cur=T(BT+'read_graph_dsl',{'graph':g}); rep['dsl']=str(cur)[:1200]
        # cirugia Tick: EnvelopeStep.then -> PushProg -> (lo que seguia)
        ok,eg=T(BT+'read_graph_dsl',{'graph':{'refPath':BPP+':EventGraph'}})
        if 'PacerPushProg' not in str(eg):
            env=node('EventGraph','PacerEnvelopeStep')
            ei=info(env); th=pin(ei,'o','then')
            nxt=th['connected_pins'][0] if th and th['connected_pins'] else None
            ok,cn=T(BT+'create_node',{'graph':{'refPath':BPP+':EventGraph'},'type_id':'CallFunction|PacerPushProg','pos':{'x':700,'y':250}})
            cref=cn['refPath'] if isinstance(cn,dict) else str(cn)
            ci=info(cref)
            if nxt: T(BT+'break_pins',{'output_pin':th['pin_id'],'input_pin':nxt})
            T(BT+'connect_pins',{'output_pin':th['pin_id'],'input_pin':pin(ci,'i','execute')['pin_id']})
            if nxt: T(BT+'connect_pins',{'output_pin':pin(ci,'o','then')['pin_id'],'input_pin':nxt})
        # cirugia CS: al final (despues del ultimo nodo con then libre de la cadena: PacerHaloPreview)
        ok,cs=T(BT+'read_graph_dsl',{'graph':{'refPath':BPP+':UserConstructionScript'}})
        if 'PacerPushProg' not in str(cs):
            last=node('UserConstructionScript','PacerHaloPreview')
            li=info(last) if last else None
            th=pin(li,'o','then') if li else None
            if th and not th['connected_pins']:
                ok,cn=T(BT+'create_node',{'graph':{'refPath':BPP+':UserConstructionScript'},'type_id':'CallFunction|PacerPushProg','pos':{'x':3000,'y':0}})
                cref=cn['refPath'] if isinstance(cn,dict) else str(cn)
                T(BT+'connect_pins',{'output_pin':th['pin_id'],'input_pin':pin(info(cref),'i','execute')['pin_id']})
            else:
                rep['cs_aviso']='PacerHaloPreview no esta al final o ya tiene then conectado: revisar a mano'
        # categorias de vuelta + las nuevas
        for n,c in cats.items():
            if c: T(BT+'set_variable_category',{'blueprint':BP,'variable_name':n,'category':c})
        for n,t,d in NEW:
            T(BT+'set_variable_category',{'blueprint':BP,'variable_name':n,'category':'G - Progreso'})
        T(BT+'compile_blueprint',{'blueprint':BP,'warnings_as_errors':True})
        ok,eg=T(BT+'read_graph_dsl',{'graph':{'refPath':BPP+':EventGraph'}}); rep['tick']=str(eg)[str(eg).find('EventTick'):][:400]
        ok,cs=T(BT+'read_graph_dsl',{'graph':{'refPath':BPP+':UserConstructionScript'}}); rep['cs_fin']=str(cs)[-300:]
        ok,ib=T(OT+'get_properties',{'instance':{'refPath':INST},'properties':[camel(n) for n,t,d in NEW]}); rep['inst']=ib
        T(AT+'save_assets',{'asset_paths':['/Game/SoulCharger/Mechanics/Pacer/BP_Pacer_SC']})
        return {'rep':rep,'errores':ERRS[:10]}
    except BaseException as e:
        return {'errores':ERRS[:10]+['run :: '+str(e)[:300]]}
