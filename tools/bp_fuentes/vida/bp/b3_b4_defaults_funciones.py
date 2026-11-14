# B3 (parte 2: defaults del CDO, tabla 5.4) + B4 (37 funciones con sus parametros). execute_tool_script; IDEMPOTENTE.
# Requiere un compile_blueprint DESPUES de b2_b3 (el CDO no tiene los campos hasta compilar).
# Claves del CDO en camelCase (primera letra minuscula); los bool conservan la b (bVida). Un solo set_properties con
# todo anduvo (los arrays de SoundBase tambien). Verificado 2026-09-29: defaults_mal [], nuevas 37, ngrafos 39.
import json
OT='editor_toolset.toolsets.object.ObjectTools.'
BT='editor_toolset.toolsets.blueprint.BlueprintTools.'
SC='editor_toolset.toolsets.scene.SceneTools.'
ERRS=[]
def T(n,p):
    try:
        return True, execute_tool(n, json.dumps(p))['returnValue']
    except BaseException as e:
        ERRS.append(n.split('.')[-1]+' :: '+str(e)[:200])
        return False, None
def canary():
    ok, acts = T(SC+'find_actors', {'name':'','tag':'','collision_channels':[]})
    if not ok: return -1
    return len([1 for x in acts if 'Test_Entering.Test_Entering:PersistentLevel.' in (x['refPath'] if isinstance(x, dict) else str(x))])
BP={'refPath':'/Game/SoulCharger/Mechanics/Breath/Life/BP_ValleyLife_SC.BP_ValleyLife_SC'}
CDO={'refPath':'/Game/SoulCharger/Mechanics/Breath/Life/BP_ValleyLife_SC.Default__BP_ValleyLife_SC_C'}
AU='/Game/SoulCharger/Mechanics/Breath/Life/Audio/'
D={'bVida':True,'VidaAmount':1.0,'MeanderRate':1.0,'GlobTau':1.0,'SoulR':150.0,
'bGusts':True,'GustAmount':1.0,'FirstGap':14.0,'GapMin':20.0,'GapMax':40.0,'GustLife':28.0,'PathHalf':4000.0,'GustW':900.0,'GustRamp':1500.0,'FrontHalf0':4000.0,'FrontHalf1':7000.0,'OffsetMin':1500.0,'OffsetMax':4000.0,'JitterDeg':25.0,'GustStir':2.0,'DriftRelax':25.0,'GustLight':2.8,'GustLean':0.12,'LeanAz':20.0,'GustRuffle':0.0,'GustNear':2500.0,
'bBreathGusts':True,'BreathEvery':2.0,'BreathWait':15.0,'BreathLife':18.0,'BreathLen':6000.0,'BreathW':400.0,'BreathRamp':300.0,'BreathHalf0':2500.0,'BreathHalf1':4500.0,'BreathJitter':15.0,
'GustVolume':0.8,'SndLen':28.0,'BreathSndLen':18.0,'SndFwd':800.0,'PreviewGust':0.0,'PreviewKind':0.0,'PreviewDir':1.0,
'GustSounds':[{'refPath':AU+'SND_VidaGustA.SND_VidaGustA'},{'refPath':AU+'SND_VidaGustB.SND_VidaGustB'},{'refPath':AU+'SND_VidaGustC.SND_VidaGustC'}],
'BreathSounds':[{'refPath':AU+'SND_VidaSoplo.SND_VidaSoplo'}]}
FN=['VidaMPC','VidaBreath','VidaGap','VidaGo','VidaStartLat','VidaStartBreath','VidaSnd','VidaNoSnd','VidaPlayG','VidaPlayB','VidaLaunchLat','VidaLaunchBreath','VidaDue','VidaMaybe','VidaEnd','VidaRelaxStep','VidaRelax','VidaSchedule','VidaState','VidaPerf','VidaPushSoul','VidaNoCam','VidaCamC','VidaCamRig','VidaPushCam','VidaPushDust','VidaPushValley','VidaAudio','VidaVisible','VidaFind','VidaAfterRig','VidaZero','VidaReset','VidaTick','VidaPreGeo','VidaPreview','VidaBenchFull']
PF={'VidaBreath':['DT'],'VidaRelaxStep':['DT'],'VidaRelax':['DT'],'VidaSchedule':['DT'],'VidaState':['DT'],'VidaTick':['DT'],'VidaStartLat':['Sign'],'VidaSnd':['Pitch'],'VidaPlayG':['Pitch'],'VidaPlayB':['Pitch'],'VidaPushCam':['Live'],'VidaPushDust':['Live']}
def cc(k):
    if k.startswith('b') and k[1].isupper(): return k
    return k[0].lower()+k[1:]
def graphs():
    ok,g=T(BT+'list_graphs',{'blueprint':BP})
    out={}
    for x in (g or []):
        rp=x['refPath'] if isinstance(x,dict) else str(x)
        out[rp.split(':')[-1]]=rp
    return out
def run():
    try:
        a=canary()
        vals={cc(k):v for k,v in D.items()}
        T(OT+'set_properties', {'instance':CDO,'values':json.dumps(vals)})
        ok,g=T(OT+'get_properties', {'instance':CDO,'properties':list(vals.keys())})
        gd=json.loads(g) if ok else {}
        bad=[]
        for k,v in vals.items():
            if k not in gd: bad.append([k,'falta']); continue
            x=gd[k]
            if isinstance(v,float):
                if abs(float(x)-v)>1e-4: bad.append([k,x])
            elif isinstance(v,list):
                if len(x)!=len(v): bad.append([k,str(x)[:120]])
            elif x!=v: bad.append([k,x])
        have=graphs()
        new=[]
        for f in FN:
            if f not in have:
                ok,r=T(BT+'add_function_graph',{'blueprint':BP,'graph_name':f})
                if ok: new.append(f)
        have=graphs()
        for f in new:
            if f not in have: ERRS.append('sin grafo '+f); continue
            gr={'refPath':have[f]}
            if f=='VidaSnd':
                T(BT+'add_object_function_param',{'graph':gr,'param_name':'Snd','object_class':{'refPath':'/Script/Engine.SoundBase'},'input_param':True})
            for p in (PF[f] if f in PF else []):
                T(BT+'add_function_param',{'graph':gr,'param_name':p,'param_type':'float','input_param':True})
        b=canary()
        return {'errores':ERRS[:10],'canario':str(a)+' -> '+str(b),'defaults_mal':bad,'nuevas':len(new),'ngrafos':len(have),'raros':[k for k in have if k.endswith('_0')]}
    except BaseException as e:
        return {'errores':ERRS[:10]+['run :: '+str(e)[:300]]}
