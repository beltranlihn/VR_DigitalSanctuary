# b1_valley_swell.py - BP_BreathValley_SC: variables de la aceleracion al exhalar + funcion StepSwell (vacia) + defaults del
# CDO y de la instancia Entering_Valle (las variables nuevas nacen en 0 en la instancia ya colocada, gotcha 518).
# IDEMPOTENTE. No escribe el grafo (va con write_graphs) ni la cirugia del Tick.
import json
BT='editor_toolset.toolsets.blueprint.BlueprintTools.'
OT='editor_toolset.toolsets.object.ObjectTools.'
SC='editor_toolset.toolsets.scene.SceneTools.'
BPP='/Game/SoulCharger/Mechanics/Breath/Valley/BP_BreathValley_SC.BP_BreathValley_SC'
BP={'refPath':BPP}
INST='/Game/Test_Entering.Test_Entering:PersistentLevel.BP_BreathValley_SC_C_0'
ED=[('ExhaleSwell',3.0),('SwellVelRef',0.3),('SwellFollow',0.6)]
ST=[('SwellSigPrev',0.0),('SwellVel',0.0),('SwellK',1.0),('SwellOfs',0.0)]
ERRS=[]
def T(n,p):
    try:
        return True, execute_tool(n, json.dumps(p))['returnValue']
    except BaseException as e:
        ERRS.append(n.split('.')[-1]+' :: '+str(e)[:200]); return False, None
def camel(n): return n[0].lower()+n[1:]
def gp(ref,keys):
    ok,g=T(OT+'get_properties',{'instance':{'refPath':ref},'properties':keys})
    try: return json.loads(g)
    except BaseException: return g
def run():
    try:
        ok,vs=T(BT+'list_variables',{'blueprint':BP})
        vh=set([str(x) for x in (vs or [])])
        for n,d in ED+ST:
            if n not in vh: T(BT+'add_variable',{'blueprint':BP,'name':n,'type_name':'float'})
        for n,d in ED:
            T(BT+'set_variable_instance_editable',{'blueprint':BP,'variable_name':n,'instance_editable':True})
        ok,gs=T(BT+'list_graphs',{'blueprint':BP})
        names=[(g['refPath'] if isinstance(g,dict) else str(g)).split(':')[-1] for g in (gs or [])]
        if 'StepSwell' not in names:
            T(BT+'add_function_graph',{'blueprint':BP,'graph_name':'StepSwell'})
            T(BT+'add_function_param',{'graph':{'refPath':BPP+':StepSwell'},'param_name':'DT','param_type':'float','input_param':True})
        T(BT+'compile_blueprint',{'blueprint':BP})
        ok,cdo=T(BT+'get_default_object',{'blueprint':BP})
        for n,d in ED+ST:
            T(OT+'set_properties',{'instance':cdo,'values':json.dumps({camel(n):d})})
        antes=gp(INST,[camel(n) for n,d in ED])
        for n,d in ED:
            T(OT+'set_properties',{'instance':{'refPath':INST},'values':json.dumps({camel(n):d})})
        return {'errores':ERRS[:8],'cdo':gp(cdo['refPath'] if isinstance(cdo,dict) else cdo,[camel(n) for n,d in ED+ST]),
                'inst_antes':antes,'inst':gp(INST,[camel(n) for n,d in ED])}
    except BaseException as e:
        return {'errores':ERRS[:8]+['run :: '+str(e)[:300]]}
