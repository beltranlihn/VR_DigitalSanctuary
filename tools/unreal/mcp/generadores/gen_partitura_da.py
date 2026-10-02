import json, ast, sys
sys.path.insert(0, r"C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/tools/unreal")
from partitura_def import P
VARS=[(n, t, v, c) for (n,t,v,c,d) in P]
S = '''import json
BT='editor_toolset.toolsets.blueprint.BlueprintTools.'
AS='editor_toolset.toolsets.asset.AssetTools.'
OT='editor_toolset.toolsets.object.ObjectTools.'
DT='editor_toolset.toolsets.data_asset.DataAssetTools.'
FOLDER='/Game/SoulCharger/Obra/Partitura'
BP=FOLDER+'/BP_Partitura_SC.BP_Partitura_SC'
DA=FOLDER+'/DA_Partitura_Obra.DA_Partitura_Obra'
VARS=%r
LOG=[]
def T(name, payload):
    try:
        return True, execute_tool(name, json.dumps(payload))['returnValue']
    except BaseException as e:
        LOG.append(name.split('.')[-1] + ' :: ' + str(e)[:300])
        return False, None
def run():
    out={}
    ok, ex = T(AS+'exists', {'path': FOLDER+'/BP_Partitura_SC'})
    if not ex:
        out['create']=T(BT+'create', {'folder_path':FOLDER,'asset_name':'BP_Partitura_SC','asset_type':{'refPath':'/Script/Engine.PrimaryDataAsset'}})[0]
    ok, vs = T(BT+'list_variables', {'blueprint':{'refPath':BP}})
    have=str(vs)
    for (n,t,v,c) in VARS:
        if ("'"+n+"'") not in have:
            if t=='a5':
                T(BT+'add_variable', {'blueprint':{'refPath':BP},'name':n,'type_name':'float','container_type':'Array'})
            else:
                T(BT+'add_variable', {'blueprint':{'refPath':BP},'name':n,'type_name':'float'})
        T(BT+'set_variable_category', {'blueprint':{'refPath':BP},'variable_name':n,'category':c})
        T(BT+'set_variable_instance_editable', {'blueprint':{'refPath':BP},'variable_name':n,'instance_editable':True})
    n0=len(LOG)
    T(BT+'compile_blueprint', {'blueprint':{'refPath':BP}})
    out['compiled']=len(LOG)==n0
    cdo='/Game/SoulCharger/Obra/Partitura/BP_Partitura_SC.Default__BP_Partitura_SC_C'
    vals={n:v for (n,t,v,c) in VARS}
    out['cdo']=T(OT+'set_properties', {'instance':{'refPath':cdo},'values':json.dumps(vals)})[0]
    T(BT+'compile_blueprint', {'blueprint':{'refPath':BP}})
    ok, ex2 = T(AS+'exists', {'path': FOLDER+'/DA_Partitura_Obra'})
    if not ex2:
        out['da']=T(DT+'create', {'folder_path':FOLDER,'asset_name':'DA_Partitura_Obra','asset_type':{'refPath':BP+'_C'}})[0]
    out['da_set']=T(OT+'set_properties', {'instance':{'refPath':DA},'values':json.dumps(vals)})[0]
    out['saved']=T(AS+'save_assets', {'asset_paths':[FOLDER+'/BP_Partitura_SC', FOLDER+'/DA_Partitura_Obra']})[0]
    ok, rb = T(OT+'get_properties', {'instance':{'refPath':DA},'properties':['Instr_Dur','Etapa_Tope','Carga_Dur','Alma_Entra','Fundido_Dur']})
    out['readback']=str(rb)[:600]
    out['log']=LOG[:8]
    return out
''' % (VARS,)
ast.parse(S)
open('job_partda.json','w',encoding='utf-8').write(json.dumps({'script':S}))
print(len(S))
