# p7_count_pacer.py - agilidad (2026-09-30): el pacer APARECE con el "three, two, one" (su pausa de entrada LeadIn 3 s corre
# DURANTE la cuenta) en vez de aparecer despues y esperar 3 s mas. Cirugia de exec en ContractStep de BP_BreathStage_SC:
#   antes:  ...PlaySound2D -> Print("three, two, one")            |  SetPhaseTimer 0 -> PacerPlay -> Print("arranca el pacer")
#   despues: ...PlaySound2D -> Print("three, two, one") -> PacerPlay |  SetPhaseTimer 0 -> Print("...")
# La fase 2 de la etapa espera Pacer.bRunning: si ya corre, pasa a la 3 en el mismo cuadro (sin cambio de logica).
# IDEMPOTENTE. Compila con warnings_as_errors y guarda SOLO el BP. Con PIE apagado.
import json
BT='editor_toolset.toolsets.blueprint.BlueprintTools.'
AT='editor_toolset.toolsets.asset.AssetTools.'
BPP='/Game/SoulCharger/Mechanics/Breath/BP_BreathStage_SC.BP_BreathStage_SC'
G={'refPath':BPP+':ContractStep'}
ERRS=[]
def T(n,p):
    try:
        return True, execute_tool(n, json.dumps(p))['returnValue']
    except BaseException as e:
        ERRS.append(n.split('.')[-1]+' :: '+str(e)[:300]); return False, None
def infos():
    ok,ns=T(BT+'find_nodes',{'graph':G,'title':''})
    ok,inf=T(BT+'get_node_infos',{'nodes':ns or []})
    return inf or []
def pin(info,d,name):
    for p in info[('input_pins' if d=='in' else 'output_pins')]:
        if p['name']==name: return p
    return None
def g(d,k): return d[k] if k in d else ''
def ref(i): return i['node']['refPath']
def val(i,name):
    p=pin(i,'in',name); return str(g(p,'value')) if p else ''
def run():
    try:
        inf=infos(); rep={}
        pp=[i for i in inf if 'PacerPlay' in str(g(i,'type_id'))]
        p3=[i for i in inf if 'PrintString' in str(g(i,'type_id')) and 'three' in val(i,'InString')]
        pa=[i for i in inf if 'PrintString' in str(g(i,'type_id')) and 'arranca el pacer' in val(i,'InString')]
        rep['hallados']=[len(pp),len(p3),len(pa)]
        if len(pp)!=1 or len(p3)!=1: return {'errores':ERRS[:8],'aviso':'nodos no unicos','rep':rep}
        pp,p3=pp[0],p3[0]
        t3=pin(p3,'out','then'); ex=pin(pp,'in','execute'); th=pin(pp,'out','then')
        if any(c['node']['refPath']==ref(pp) for c in t3['connected_pins']):
            rep['estado']='ya hecho'
        else:
            if t3['connected_pins']: return {'errores':ERRS[:8],'aviso':'el then de three, two, one ya tiene salida','rep':rep}
            srcs=list(ex['connected_pins']); dsts=list(th['connected_pins'])
            rep['srcs']=[c['node']['refPath'].split('.')[-1] for c in srcs]; rep['dsts']=[c['node']['refPath'].split('.')[-1] for c in dsts]
            for s in srcs: T(BT+'break_pins',{'output_pin':s,'input_pin':ex['pin_id']})
            for d in dsts: T(BT+'break_pins',{'output_pin':th['pin_id'],'input_pin':d})
            for s in srcs:
                for d in dsts: T(BT+'connect_pins',{'output_pin':s,'input_pin':d})
            T(BT+'connect_pins',{'output_pin':t3['pin_id'],'input_pin':ex['pin_id']})
            if pa:
                T(BT+'set_pin_value',{'pin':pin(pa[0],'in','InString')['pin_id'],'value':'BREATHSTAGE: fin de la cuenta (el pacer ya aparecio con ella)'})
            rep['estado']='cirugia'
        T(BT+'compile_blueprint',{'blueprint':{'refPath':BPP},'warnings_as_errors':True})
        inf=infos()
        pp=[i for i in inf if 'PacerPlay' in str(g(i,'type_id'))][0]
        e2=pin(pp,'in','execute'); rep['pacerplay_entra_de']=[c['node']['refPath'].split('.')[-1] for c in e2['connected_pins']]
        rep['pacerplay_sale_a']=[c['node']['refPath'].split('.')[-1] for c in pin(pp,'out','then')['connected_pins']]
        ok,d=T(BT+'read_graph_dsl',{'graph':G}); s=str(d); k=s.find('three'); rep['dsl']=s[max(0,k-200):k+900]
        T(AT+'save_assets',{'asset_paths':['/Game/SoulCharger/Mechanics/Breath/BP_BreathStage_SC']})
        return {'errores':ERRS[:8],'rep':rep}
    except BaseException as e:
        return {'errores':ERRS[:8]+['run :: '+str(e)[:300]]}
