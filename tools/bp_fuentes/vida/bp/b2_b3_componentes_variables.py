# B2 + B3 (parte 1): propiedades de los componentes (una por set_properties, gotcha 478) + las 90 variables.
# execute_tool_script; IDEMPOTENTE (gotcha 489). Requiere los componentes YA agregados por llamada directa
# (ActorTools.add_component DustMesh / GustAudio sobre el CDO). Verificado 2026-09-29: errores [], 90 variables,
# AttenuationOverrides bAttenuate false / bSpatialize true, BodyInstance NoCollision/NoCollision.
# Variables SIN category en add_variable (gotcha 296): la categoria va despues con set_variable_category.
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
BPP='/Game/SoulCharger/Mechanics/Breath/Life/BP_ValleyLife_SC.BP_ValleyLife_SC_C:'
ED=[('A-Vida','bool',['bVida']),('A-Vida','float',['VidaAmount','MeanderRate','GlobTau','SoulR']),
 ('B-Rafagas','bool',['bGusts']),('B-Rafagas','float',['GustAmount','FirstGap','GapMin','GapMax','GustLife','PathHalf','GustW','GustRamp','FrontHalf0','FrontHalf1','OffsetMin','OffsetMax','JitterDeg','GustStir','DriftRelax','GustLight','GustLean','LeanAz','GustRuffle','GustNear']),
 ('C-Soplo','bool',['bBreathGusts']),('C-Soplo','float',['BreathEvery','BreathWait','BreathLife','BreathLen','BreathW','BreathRamp','BreathHalf0','BreathHalf1','BreathJitter']),
 ('D-Sonido','float',['GustVolume','SndLen','BreathSndLen','SndFwd']),('E-Prueba','float',['PreviewGust','PreviewKind','PreviewDir'])]
Z=[('float',['Clock','Wait','GustIdx','GustKind','Front','Front0','Front1','FrontV','GW','E0','E1','Ramp','Lf0','Lf1','Life','SndMin','Amp','Hold','HoldPh','HoldV','HoldRate','Tm','Rate','GlobBase','Glob','ActUser','VSig','VGate','Sprev','Vel','VelF','Flow','InhHold']),('bool',['bGusting','bPrimed','bExhOnset','bSndWarned','bForce']),('Vector',['OrgW','DirW','SndOffW']),('int',['PerfMode'])]
OBJ=[('D-Sonido','GustSounds','/Script/Engine.SoundBase','Array',True),('D-Sonido','BreathSounds','/Script/Engine.SoundBase','Array',True),
 ('Z-Vida','Valley','/Game/SoulCharger/Mechanics/Breath/Valley/BP_BreathValley_SC.BP_BreathValley_SC_C',None,False),
 ('Z-Vida','Blob','/Game/SoulCharger/Mechanics/Breath/BP_BreathBlob_SC.BP_BreathBlob_SC_C',None,False),
 ('Z-Vida','Rig','/Game/SoulCharger/Mechanics/Breath/BP_BreathRig_SC.BP_BreathRig_SC_C',None,False)]
def names():
    ok, v = T(BT+'list_variables', {'blueprint':BP})
    return set([str(x['name']) if isinstance(x,dict) else str(x) for x in (v or [])])
def run():
    try:
        a=canary()
        dm = {'refPath': BPP+'DustMesh_GEN_VARIABLE'}
        ga = {'refPath': BPP+'GustAudio_GEN_VARIABLE'}
        sets = [(dm, {'staticMesh': {'refPath':'/Game/SoulCharger/Mechanics/Breath/Life/SM_ValleyDust_SC.SM_ValleyDust_SC'}}),
          (dm, {'overrideMaterials': [{'refPath':'/Game/SoulCharger/Mechanics/Breath/Life/MI_ValleyDust_SC.MI_ValleyDust_SC'}]}),
          (dm, {'BodyInstance': {'collisionEnabled':'NoCollision','collisionProfileName':'NoCollision'}}),
          (dm, {'castShadow': False}),(dm, {'translucencySortPriority': 5}),(dm, {'bReceivesDecals': False}),
          (ga, {'bAutoActivate': False}),(ga, {'bOverrideAttenuation': True}),
          (ga, {'AttenuationOverrides': '(bAttenuate=False,bSpatialize=True)'}),(ga, {'bAllowSpatialization': True})]
        for comp, v in sets:
            T(OT+'set_properties', {'instance': comp, 'values': json.dumps(v)})
        have=names()
        plan=[]
        for cat,t,ns in ED:
            for n in ns: plan.append((cat,n,t,True))
        for t,ns in Z:
            for n in ns: plan.append(('Z-Vida',n,t,False))
        for cat,n,t,ed in plan:
            if n not in have: T(BT+'add_variable', {'blueprint':BP,'name':n,'type_name':t})
        for cat,n,cls,cont,ed in OBJ:
            if n not in have:
                p={'blueprint':BP,'name':n,'object_class':{'refPath':cls}}
                if cont: p['container_type']=cont
                T(BT+'add_object_variable', p)
        for cat,n,t,ed in plan + [(o[0],o[1],None,o[4]) for o in OBJ]:
            T(BT+'set_variable_category', {'blueprint':BP,'variable_name':n,'category':cat})
            if ed: T(BT+'set_variable_instance_editable', {'blueprint':BP,'variable_name':n,'instance_editable':True})
        ok1,g1=T(OT+'get_properties', {'instance': dm, 'properties': ['staticMesh','overrideMaterials','castShadow','translucencySortPriority','bReceivesDecals']})
        ok2,g2=T(OT+'get_properties', {'instance': ga, 'properties': ['bAutoActivate','bOverrideAttenuation','bAllowSpatialization']})
        ok3,g3=T(OT+'get_properties', {'instance': ga, 'properties': ['AttenuationOverrides']})
        att=json.loads(g3)['AttenuationOverrides'] if ok3 else {}
        ok4,g4=T(OT+'get_properties', {'instance': dm, 'properties': ['BodyInstance']})
        bi=json.loads(g4)['BodyInstance'] if ok4 else {}
        after=names()
        b=canary()
        return {'errores':ERRS[:10],'canario':str(a)+' -> '+str(b),'vars':len(after),'raros':sorted([x for x in after if x.endswith('_0')]),'dm':g1,'ga':g2,'att':[att['bAttenuate'] if 'bAttenuate' in att else None, att['bSpatialize'] if 'bSpatialize' in att else None],'bi':[bi['collisionEnabled'] if 'collisionEnabled' in bi else None, bi['collisionProfileName'] if 'collisionProfileName' in bi else None]}
    except BaseException as e:
        return {'errores':ERRS[:10]+['run :: '+str(e)[:300]]}
