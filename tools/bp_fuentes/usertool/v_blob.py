# vars.py - agrega variables a un BP (sin categoria: gotcha 296), compila, escribe defaults en el CDO y relee.
# execute_tool_script; IDEMPOTENTE. Reemplazar /Game/SoulCharger/Mechanics/Breath/BP_BreathBlob_SC.BP_BreathBlob_SC (paquete.objeto), [('MorphScale', 'float', 0.5, True), ('MorphRadius', 'float', 0.08, True), ('MorphSizeVar', 'float', 1.6, True), ('MorphSpread', 'float', 1.9, True), ('MorphSpreadOut', 'float', 2.3, True), ('MorphSmooth', 'float', 0.2, True), ('MorphBright', 'float', 1.35, True), ('MorphCurl', 'float', 1.3, True), ('IntroTime', 'float', 4.0, False), ('OutroTime', 'float', 2.5, False)] [(nombre, tipo, default|None, editable)],
# [] [(nombre, clase, default|None, editable)], [('EnvT', 'Default'), ('bShown', 'Default'), ('BlobRadius', 'Default'), ('SizeVariation', 'Default'), ('Spread', 'Default'), ('Smoothness', 'Default'), ('Brightness', 'Default'), ('CurlAmount', 'Default')] [(var, categoria)] (mover a una categoria, p. ej. Default).
# Los defaults van en formato de TEXTO de Unreal cuando son structs ("(R=..,G=..,B=..,A=..)"; transformadas en texto).
import json
BT='editor_toolset.toolsets.blueprint.BlueprintTools.'
OT='editor_toolset.toolsets.object.ObjectTools.'
BPP='/Game/SoulCharger/Mechanics/Breath/BP_BreathBlob_SC.BP_BreathBlob_SC'
BP={'refPath':BPP}
VARS=[('MorphScale', 'float', 0.5, True), ('MorphRadius', 'float', 0.08, True), ('MorphSizeVar', 'float', 1.6, True), ('MorphSpread', 'float', 1.9, True), ('MorphSpreadOut', 'float', 2.3, True), ('MorphSmooth', 'float', 0.2, True), ('MorphBright', 'float', 1.35, True), ('MorphCurl', 'float', 1.3, True), ('IntroTime', 'float', 4.0, False), ('OutroTime', 'float', 2.5, False)]
OBJ=[]
TOCAT=[('EnvT', 'Default'), ('bShown', 'Default'), ('BlobRadius', 'Default'), ('SizeVariation', 'Default'), ('Spread', 'Default'), ('Smoothness', 'Default'), ('Brightness', 'Default'), ('CurlAmount', 'Default')]
ERRS=[]
def T(n,p):
    try:
        return True, execute_tool(n, json.dumps(p))['returnValue']
    except BaseException as e:
        ERRS.append(n.split('.')[-1]+' '+json.dumps(p)[:90]+' :: '+str(e)[:200]); return False, None
def camel(n):
    return n[0].lower()+n[1:] if not (n.startswith('b') and n[1:2].isupper()) else n
def run():
    try:
        ok,vs=T(BT+'list_variables',{'blueprint':BP})
        vh=set([str(x['name']) if isinstance(x,dict) else str(x) for x in (vs or [])])
        for n,t,d,ed in VARS:
            if n not in vh: T(BT+'add_variable',{'blueprint':BP,'name':n,'type_name':t})
        for n,cls,d,ed in OBJ:
            if n not in vh: T(BT+'add_object_variable',{'blueprint':BP,'name':n,'object_class':{'refPath':cls}})
        for n,*rest in VARS+OBJ:
            ed=rest[-1]
            if ed: T(BT+'set_variable_instance_editable',{'blueprint':BP,'variable_name':n,'instance_editable':True})
        cats={}
        for n,cat in TOCAT:
            ok,c0=T(BT+'get_variable_category',{'blueprint':BP,'variable_name':n})
            cats[n]=c0
            T(BT+'set_variable_category',{'blueprint':BP,'variable_name':n,'category':cat})
        T(BT+'compile_blueprint',{'blueprint':BP})
        ok,cdo=T(BT+'get_default_object',{'blueprint':BP})
        rb={}
        for n,t,d,ed in VARS+[(o[0],'obj',o[2],o[3]) for o in OBJ]:
            if d is None: continue
            k=camel(n)
            T(OT+'set_properties',{'instance':cdo,'values':json.dumps({k:d})})
            ok,g=T(OT+'get_properties',{'instance':cdo,'properties':[k]})
            rb[n]=g
        T(BT+'compile_blueprint',{'blueprint':BP})
        return {'errores':ERRS[:10],'categorias_antes':cats,'releido':rb}
    except BaseException as e:
        return {'errores':ERRS[:10]+['run :: '+str(e)[:300]]}
