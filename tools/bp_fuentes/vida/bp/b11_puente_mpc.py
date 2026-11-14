# B11: puente VidaMPC (gotcha 291). execute_tool_script; IDEMPOTENTE (si ya hay nodos con pin Collection, no crea).
# Requiere VidaMPC escrito por DSL (entrada -> SetVSig 0 -> SetVGate 0). Verificado 2026-09-29: entrada -> Get(Signed)
# -> Get(On) -> SetVSig -> SetVGate; ReturnValue de cada Get al pin de valor; nodos K2Node_CallMaterialParameterCollectionFunction.
import json
BT='editor_toolset.toolsets.blueprint.BlueprintTools.'
SC='editor_toolset.toolsets.scene.SceneTools.'
G={'refPath':'/Game/SoulCharger/Mechanics/Breath/Life/BP_ValleyLife_SC.BP_ValleyLife_SC:VidaMPC'}
ERRS=[]
def T(n,p):
    try:
        return True, execute_tool(n, json.dumps(p))['returnValue']
    except BaseException as e:
        ERRS.append(n.split('.')[-1]+' :: '+str(e)[:300])
        return False, None
def canary():
    ok, acts = T(SC+'find_actors', {'name':'','tag':'','collision_channels':[]})
    if not ok: return -1
    return len([1 for x in acts if 'Test_Entering.Test_Entering:PersistentLevel.' in (x['refPath'] if isinstance(x, dict) else str(x))])
def infos():
    ok,ns=T(BT+'find_nodes',{'graph':G,'title':''})
    ok,inf=T(BT+'get_node_infos',{'nodes':ns})
    return inf or []
def pin(info, direction, name):
    for p in info[('input_pins' if direction=='in' else 'output_pins')]:
        if p['name']==name: return p
    return None
def run():
    try:
        a=canary()
        inf=infos()
        ent=[i for i in inf if i['type_id']=='|VidaMPC'][0]
        s0=[i for i in inf if i['type_id']=='|SetVSig'][0]
        s1=[i for i in inf if i['type_id']=='|SetVGate'][0]
        gets=[i for i in inf if 'Collection' in str(i['input_pins'])]
        if len(gets)==0:
            for pos in ({'x':280,'y':200},{'x':560,'y':200}):
                T(BT+'create_node',{'graph':G,'type_id':'Rendering|Material|GetScalarParameterValue','pos':pos,'declaring_class':{'refPath':'/Script/Engine.KismetMaterialLibrary'}})
            inf=infos()
            gets=[i for i in inf if 'Collection' in str(i['input_pins'])]
            gets.sort(key=lambda i: i['position']['x'])
            ga,gb=gets[0],gets[1]
            for g,nm in ((ga,'Signed'),(gb,'On')):
                T(BT+'set_pin_value',{'pin':pin(g,'in','Collection')['pin_id'],'value':'/Game/SoulCharger/Mechanics/Breath/MPC_Breath.MPC_Breath'})
                T(BT+'set_pin_value',{'pin':pin(g,'in','ParameterName')['pin_id'],'value':nm})
            T(BT+'break_pins',{'output_pin':pin(ent,'out','then')['pin_id'],'input_pin':pin(s0,'in','execute')['pin_id']})
            T(BT+'connect_pins',{'output_pin':pin(ent,'out','then')['pin_id'],'input_pin':pin(ga,'in','execute')['pin_id']})
            T(BT+'connect_pins',{'output_pin':pin(ga,'out','then')['pin_id'],'input_pin':pin(gb,'in','execute')['pin_id']})
            T(BT+'connect_pins',{'output_pin':pin(gb,'out','then')['pin_id'],'input_pin':pin(s0,'in','execute')['pin_id']})
            T(BT+'connect_pins',{'output_pin':pin(ga,'out','ReturnValue')['pin_id'],'input_pin':pin(s0,'in','VSig')['pin_id']})
            T(BT+'connect_pins',{'output_pin':pin(gb,'out','ReturnValue')['pin_id'],'input_pin':pin(s1,'in','VGate')['pin_id']})
        inf=infos()
        summ=[]
        for i in inf:
            summ.append([i['node']['refPath'].split('.')[-1], i['type_id'], [[p['name'],p['value'],[c['node']['refPath'].split('.')[-1] for c in p['connected_pins']]] for p in i['input_pins']], [[p['name'],[c['node']['refPath'].split('.')[-1] for c in p['connected_pins']]] for p in i['output_pins']]])
        b=canary()
        return {'errores':ERRS,'canario':str(a)+' -> '+str(b),'nodos':summ}
    except BaseException as e:
        return {'errores':ERRS+['run :: '+str(e)[:300]]}
