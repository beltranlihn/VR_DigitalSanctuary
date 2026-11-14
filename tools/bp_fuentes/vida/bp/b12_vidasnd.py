# B12: VidaSnd por cirugia (los nodos de audio resuelven al homonimo de SynthComponent por DSL). execute_tool_script;
# IDEMPOTENTE (solo crea si el grafo tiene solo la entrada). Verificado 2026-09-29: entrada -> SetSound -> SetPitchMultiplier
# -> SetVolumeMultiplier -> VidaAudio -> Play; self de los 4 = GetGustAudio; NewSound = Snd; NewPitchMultiplier = Pitch;
# NewVolumeMultiplier = GetGustVolume; StartTime 0. Pines: execute/then/self/NewSound/NewPitchMultiplier/NewVolumeMultiplier/StartTime.
import json
BT='editor_toolset.toolsets.blueprint.BlueprintTools.'
SC='editor_toolset.toolsets.scene.SceneTools.'
G={'refPath':'/Game/SoulCharger/Mechanics/Breath/Life/BP_ValleyLife_SC.BP_ValleyLife_SC:VidaSnd'}
AC={'refPath':'/Script/Engine.AudioComponent'}
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
        if p['name']==name: return p['pin_id']
    ERRS.append('sin pin '+name+' en '+info['type_id'])
    return None
def run():
    try:
        a=canary()
        inf=infos()
        if len(inf)<=1:
            T(BT+'create_node',{'graph':G,'type_id':'Variables|Default|GetGustAudio','pos':{'x':200,'y':300}})
            T(BT+'create_node',{'graph':G,'type_id':'Variables|D-Sonido|GetGustVolume','pos':{'x':600,'y':400}})
            T(BT+'create_node',{'graph':G,'type_id':'Audio|Components|Audio|SetSound','pos':{'x':300,'y':0},'declaring_class':AC})
            T(BT+'create_node',{'graph':G,'type_id':'Audio|Components|Audio|SetPitchMultiplier','pos':{'x':600,'y':0},'declaring_class':AC})
            T(BT+'create_node',{'graph':G,'type_id':'Audio|Components|Audio|SetVolumeMultiplier','pos':{'x':900,'y':0},'declaring_class':AC})
            T(BT+'create_node',{'graph':G,'type_id':'CallFunction|VidaAudio','pos':{'x':1200,'y':0}})
            T(BT+'create_node',{'graph':G,'type_id':'Audio|Components|Audio|Play','pos':{'x':1500,'y':0},'declaring_class':AC})
            inf=infos()
            ga=[i for i in inf if 'GetGustAudio' in i['type_id']][0]
            gv=[i for i in inf if 'GetGustVolume' in i['type_id']][0]
            ss=[i for i in inf if i['type_id'].endswith('SetSound')][0]
            sp=[i for i in inf if i['type_id'].endswith('SetPitchMultiplier')][0]
            sv=[i for i in inf if i['type_id'].endswith('SetVolumeMultiplier')][0]
            va=[i for i in inf if i['type_id'].endswith('VidaAudio')][0]
            pl=[i for i in inf if i['type_id'].endswith('|Play')][0]
            ent=[i for i in inf if i['type_id']=='|VidaSnd'][0]
            C=lambda o,i: T(BT+'connect_pins',{'output_pin':o,'input_pin':i})
            C(pin(ent,'out','then'),pin(ss,'in','execute'))
            C(pin(ss,'out','then'),pin(sp,'in','execute'))
            C(pin(sp,'out','then'),pin(sv,'in','execute'))
            C(pin(sv,'out','then'),pin(va,'in','execute'))
            C(pin(va,'out','then'),pin(pl,'in','execute'))
            gout=[p['pin_id'] for p in ga['output_pins']][0]
            for n in (ss,sp,sv,pl): C(gout,pin(n,'in','self'))
            C(pin(ent,'out','Snd'),pin(ss,'in','NewSound'))
            C(pin(ent,'out','Pitch'),pin(sp,'in','NewPitchMultiplier'))
            C([p['pin_id'] for p in gv['output_pins']][0],pin(sv,'in','NewVolumeMultiplier'))
        inf=infos()
        summ=[]
        for i in inf:
            summ.append([i['node']['refPath'].split('.')[-1], i['type_id'], [[p['name'],p['value'],[c['node']['refPath'].split('.')[-1] for c in p['connected_pins']]] for p in i['input_pins']], [[p['name'],[c['node']['refPath'].split('.')[-1] for c in p['connected_pins']]] for p in i['output_pins']]])
        b=canary()
        return {'errores':ERRS,'canario':str(a)+' -> '+str(b),'nodos':summ}
    except BaseException as e:
        return {'errores':ERRS+['run :: '+str(e)[:300]]}
