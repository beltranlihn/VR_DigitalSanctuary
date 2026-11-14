# PlaceArt: Spin gira sobre el eje PROPIO del disco (2026-09-30). execute_tool_script; IDEMPOTENTE.
# Antes: CombineRotators(MakeRotator(Tilt, Bank, Spin), Base) -> dentro de UN rotador el yaw se aplica al final,
# respecto del padre: con Bank != 0 el Spin inclinaba en vez de girar en el plano.
# Ahora: rot = Base * Tilt * Bank * Spin  (Spin el mas interno = siempre en el plano del disco).
#   C1 (_50) = Combine(MR_tilt(_43), Base)   -> C2 = Combine(MR_bank, C1) -> C3 = Combine(MR_spin, C2) -> MakeTransform.Rotation
import json
BT='editor_toolset.toolsets.blueprint.BlueprintTools.'
G={'refPath':'/Game/NeuralCanvas/TB/BP_TBDirector_NC.BP_TBDirector_NC:PlaceArt'}
P='/Game/NeuralCanvas/TB/BP_TBDirector_NC.BP_TBDirector_NC:PlaceArt.'
ERRS=[]
LOG=[]
def T(n,p):
    try:
        return True, execute_tool(n, json.dumps(p))['returnValue']
    except BaseException as e:
        ERRS.append(n.split('.')[-1]+' :: '+str(e)[:300]); return False, None
def infos():
    ok,ns=T(BT+'find_nodes',{'graph':G,'title':''})
    ok,inf=T(BT+'get_node_infos',{'nodes':ns})
    return inf or []
def pin(info, direction, name):
    for p in info[('input_pins' if direction=='in' else 'output_pins')]:
        if p['name']==name: return p['pin_id']
    ERRS.append('pin '+name+' no esta'); return None
def PID(n,d,i): return {'direction':('EGPD_Input' if d=='in' else 'EGPD_Output'),'index_id':i,'node':{'refPath':P+n}}
def at(inf,tid,y):
    m=[i for i in inf if i['type_id']==tid and abs(i['position']['y']-y)<1 and i['position']['x']>=17000]
    return m[0] if len(m)==1 else None
def conn(o,i,tag):
    ok,_=T(BT+'connect_pins',{'output_pin':o,'input_pin':i}); LOG.append(tag+(' ok' if ok else ' FALLO'))
def brk(o,i,tag):
    ok,_=T(BT+'break_pins',{'output_pin':o,'input_pin':i}); LOG.append(tag+(' ok' if ok else ' FALLO'))
MR='Math|Rotator|MakeRotator'; CR='Math|Rotator|CombineRotators'
def run():
    try:
        inf=infos()
        if len([i for i in inf if i['type_id']==CR])>=3:
            return {'skip':'ya hay 3 CombineRotators','errs':ERRS}
        for tid,pos in ((MR,{'x':17640,'y':420}),(MR,{'x':17640,'y':640}),(CR,{'x':20720,'y':420}),(CR,{'x':20720,'y':640})):
            ok,r=T(BT+'create_node',{'graph':G,'type_id':tid,'pos':pos}); LOG.append('create '+tid+' '+str(ok))
        inf=infos()
        mrB=at(inf,MR,420); mrS=at(inf,MR,640); c2=at(inf,CR,420); c3=at(inf,CR,640)
        if not (mrB and mrS and c2 and c3):
            ERRS.append('no ubique los nodos nuevos'); return {'log':LOG,'errs':ERRS}
        conn(PID('K2Node_VariableGet_15','out',0), pin(mrB,'in','Pitch'), 'bank->mrB.Pitch')
        brk (PID('K2Node_VariableGet_15','out',0), PID('K2Node_CallFunction_43','in',1), 'x bank->_43.Pitch')
        conn(PID('K2Node_Select_7','out',0), pin(mrS,'in','Yaw'), 'spin->mrS.Yaw')
        brk (PID('K2Node_Select_7','out',0), PID('K2Node_CallFunction_43','in',2), 'x spin->_43.Yaw')
        conn(PID('K2Node_CallFunction_50','out',0), pin(c2,'in','B'), 'C1->C2.B')
        conn(pin(mrB,'out','ReturnValue'), pin(c2,'in','A'), 'mrB->C2.A')
        conn(pin(c2,'out','ReturnValue'), pin(c3,'in','B'), 'C2->C3.B')
        conn(pin(mrS,'out','ReturnValue'), pin(c3,'in','A'), 'mrS->C3.A')
        conn(pin(c3,'out','ReturnValue'), PID('K2Node_CallFunction_52','in',1), 'C3->MakeTransform.Rotation')
        brk (PID('K2Node_CallFunction_50','out',0), PID('K2Node_CallFunction_52','in',1), 'x C1->MakeTransform (por si quedo)')
    except BaseException as e:
        ERRS.append('run :: '+str(e)[:300])
    return {'log':LOG,'errs':ERRS}
