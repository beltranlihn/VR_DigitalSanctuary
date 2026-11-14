# q2_defaults.py - DESPUES de q1 (BP compilado): defaults del CDO de BP_BreathStage_SC para la voz del primer ciclo.
# Corre con cualquier nivel abierto (solo toca el CDO). Solo escribe propiedades que list_variables confirma (una propiedad
# inexistente tumba el script). Compila y guarda el BP. La instancia de Test_Entering se revisa aparte (q3).
import json
BT='editor_toolset.toolsets.blueprint.BlueprintTools.'
OT='editor_toolset.toolsets.object.ObjectTools.'
AT='editor_toolset.toolsets.asset.AssetTools.'
BPP='/Game/SoulCharger/Mechanics/Breath/BP_BreathStage_SC.BP_BreathStage_SC'
A='/Game/SoulCharger/Mechanics/Breath/Audio/'
VALS=[('bCycleVO','bCycleVO',True),('InhaleCueAt','inhaleCueAt',3.48),('CueLead','cueLead',0.3),('CountTime','countTime',3.6),
      ('HoldSound','holdSound',{'refPath':A+'VO_12f1.VO_12f1'}),('ExhaleSound','exhaleSound',{'refPath':A+'VO_12f2.VO_12f2'})]
ERRS=[]
def T(n,p):
    try:
        return True, execute_tool(n, json.dumps(p))['returnValue']
    except BaseException as e:
        ERRS.append(n.split('.')[-1]+' :: '+str(e)[:300]); return False, None
def run():
    try:
        ok,vs=T(BT+'list_variables',{'blueprint':{'refPath':BPP}})
        vh=set([(x['name'] if isinstance(x,dict) and 'name' in x else str(x)) for x in (vs or [])])
        ok,ex1=T(AT+'exists',{'path':A+'VO_12f1'}); ok,ex2=T(AT+'exists',{'path':A+'VO_12f2'})
        use=[v for v in VALS if v[0] in vh and (v[0] not in ('HoldSound','ExhaleSound') or (ex1 and ex2))]
        ok,cdo=T(BT+'get_default_object',{'blueprint':{'refPath':BPP}})
        cref=cdo['refPath'] if isinstance(cdo,dict) else str(cdo)
        ok,a=T(OT+'get_properties',{'instance':{'refPath':cref},'properties':[p for n,p,v in use]})
        for n,p,v in use:
            T(OT+'set_properties',{'instance':{'refPath':cref},'values':json.dumps({p:v})})
        T(BT+'compile_blueprint',{'blueprint':{'refPath':BPP},'warnings_as_errors':True})
        ok,b=T(OT+'get_properties',{'instance':{'refPath':cref},'properties':[p for n,p,v in use]})
        T(AT+'save_assets',{'asset_paths':['/Game/SoulCharger/Mechanics/Breath/BP_BreathStage_SC']})
        return {'errores':ERRS[:8],'faltan':[v[0] for v in VALS if v not in use],'antes':a,'despues':b,'sonidos':[ex1,ex2]}
    except BaseException as e:
        return {'errores':ERRS[:8]+['run :: '+str(e)[:300]]}
