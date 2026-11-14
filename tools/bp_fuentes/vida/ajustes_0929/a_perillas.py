# Ajustes de Beltran en visor (2026-09-29, tarde) sobre Test_Entering. execute_tool_script; IDEMPOTENTE.
# Requiere: Test_Entering cargado y SM_ValleyDust2_SC ya importado en Mechanics/Breath/Life.
# Devuelve los valores ANTES y DESPUES de cada perilla (el ANTES es el rollback).
import json
OT='editor_toolset.toolsets.object.ObjectTools.'
SC='editor_toolset.toolsets.scene.SceneTools.'
MI='editor_toolset.toolsets.material_instance.MaterialInstanceTools.'
ERRS=[]
def T(n,p):
    try:
        return True, execute_tool(n, json.dumps(p))['returnValue']
    except BaseException as e:
        ERRS.append(n.split('.')[-1]+' :: '+str(e)[:200])
        return False, None
LVL='/Game/Test_Entering.Test_Entering:PersistentLevel.'
def actors():
    ok, acts = T(SC+'find_actors', {'name':'','tag':'','collision_channels':[]})
    out=[]
    for x in (acts or []):
        r = x['refPath'] if isinstance(x, dict) else str(x)
        if LVL in r: out.append(r)
    return out
BR='/Game/SoulCharger/Mechanics/Breath/'
CLS={'blob':(BR+'BP_BreathBlob_SC.Default__BP_BreathBlob_SC_C','BP_BreathBlob_SC_C'),
     'air':(BR+'Air/BP_BreathAir_SC.Default__BP_BreathAir_SC_C','BP_BreathAir_SC_C'),
     'valley':(BR+'Valley/BP_BreathValley_SC.Default__BP_BreathValley_SC_C','BP_BreathValley_SC_C'),
     'vida':(BR+'Life/BP_ValleyLife_SC.Default__BP_ValleyLife_SC_C','BP_ValleyLife_SC_C')}
KN={'blob':{'breathBrightOut':0.0},
    'air':{'frontLead':6.0,'turnFade0':400.0,'turnFade1':800.0,'lagRot':0.25,'lagPos':0.1,'pitchFollow':1.0},
    'valley':{'morphAmt':0.45,'morphSpeed':2.0,'swellAmp':2800.0,'swellSpeed':2.0}}
MIS={BR+'Air/MI_BreathAir_SC.MI_BreathAir_SC':{'InSpreadH':18.0,'InSpreadV':8.0,'OutStart':40.0,'PlumeLen':95.0,
        'OutSpread':18.0,'OutFlat':0.45,'OutSizeCm':0.22,'OutGrow':0.0,'MaxDegOut':0.4,'OutAlpha':0.45,
        'SpeedFade0':90.0,'SpeedFade1':180.0},
     BR+'Life/MI_ValleyDust_SC.MI_ValleyDust_SC':{'FarFade0':8000.0,'FarFade1':11000.0}}
MESH=BR+'Life/SM_ValleyDust2_SC.SM_ValleyDust2_SC'
def getp(ref, keys):
    ok, g = T(OT+'get_properties', {'instance':{'refPath':ref}, 'properties':keys})
    return json.loads(g) if ok and g else None
def run():
    try:
        acts=actors()
        a=len(acts)
        inst={}
        for k,(cdo,cn) in CLS.items():
            m=[r for r in acts if (':PersistentLevel.'+cn+'_') in r]
            inst[k]=m[0] if len(m)==1 else None
            if len(m)!=1: ERRS.append('instancia '+k+': '+str(m))
        rep={}
        for k,kv in KN.items():
            keys=list(kv.keys())
            for tag,ref in (('cdo',CLS[k][0]),('inst',inst[k])):
                if not ref: continue
                before=getp(ref, keys)
                T(OT+'set_properties', {'instance':{'refPath':ref}, 'values':json.dumps(kv)})
                rep[k+'.'+tag]={'antes':before,'despues':getp(ref, keys)}
        for mi,kv in MIS.items():
            r={}
            for n,v in kv.items():
                ok,b=T(MI+'get_scalar_parameter', {'instance':{'refPath':mi},'name':n})
                T(MI+'set_scalar_parameter', {'instance':{'refPath':mi},'name':n,'value':v})
                ok,d=T(MI+'get_scalar_parameter', {'instance':{'refPath':mi},'name':n})
                r[n]=[b,d]
            rep[mi.split('.')[-1]]=r
        tpl=BR+'Life/BP_ValleyLife_SC.BP_ValleyLife_SC_C:DustMesh_GEN_VARIABLE'
        comps=[tpl]+([inst['vida']+'.DustMesh'] if inst['vida'] else [])
        for c in comps:
            before=getp(c,['staticMesh'])
            T(OT+'set_properties', {'instance':{'refPath':c}, 'values':json.dumps({'staticMesh':{'refPath':MESH}})})
            rep['mesh '+c.split('.')[-1]]={'antes':before,'despues':getp(c,['staticMesh','overrideMaterials'])}
        b=len(actors())
        return {'errores':ERRS[:12],'canario':str(a)+' -> '+str(b),'instancias':inst,'rep':rep}
    except BaseException as e:
        return {'errores':ERRS[:12]+['run :: '+str(e)[:300]]}
