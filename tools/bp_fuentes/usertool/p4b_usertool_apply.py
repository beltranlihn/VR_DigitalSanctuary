# p4b_usertool_apply.py - con L_SoulCharger_Obra abierto: copia a UserTool_Obra los valores de autor de Entering_UserTool que
# difieren del CDO (usertool_vals.json de p4a). Una propiedad por llamada (componentes: gotcha 116), antes -> despues.
# bShowMandoOnBegin queda false (flag de test). Canario de actores. NO guarda (se guarda aparte con ruta explicita).
import json
OT='editor_toolset.toolsets.object.ObjectTools.'
SC='editor_toolset.toolsets.scene.SceneTools.'
AT='editor_toolset.toolsets.asset.AssetTools.'
LVL='/Game/SoulCharger/Obra/L_SoulCharger_Obra.L_SoulCharger_Obra:PersistentLevel.'
IN='C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/usertool/usertool_vals.json'
ERRS=[]
def T(n,p):
    try:
        return True, execute_tool(n, json.dumps(p))['returnValue']
    except BaseException as e:
        ERRS.append(n.split('.')[-1]+' :: '+str(e)[:200]); return False, None
def rp(x): return x['refPath'] if isinstance(x,dict) else str(x)
def gp(ref,keys):
    ok,g=T(OT+'get_properties',{'instance':{'refPath':ref},'properties':keys})
    try: return json.loads(g)
    except BaseException: return g
def txt(val):
    # structs de componente en formato texto (gotcha 116: el JSON de struct aplica un solo campo)
    if isinstance(val,dict):
        lk={k.lower():k for k in val}
        if all(c in lk for c in ('x','y','z')):
            return '(X=%f,Y=%f,Z=%f)'%(val[lk['x']],val[lk['y']],val[lk['z']])
        if all(c in lk for c in ('pitch','yaw','roll')):
            return '(Pitch=%f,Yaw=%f,Roll=%f)'%(val[lk['pitch']],val[lk['yaw']],val[lk['roll']])
    return val
def miss(want,got):
    if not isinstance(got,dict): return list(want.keys())
    return [k for k in want if json.dumps(want[k],sort_keys=True)!=json.dumps(got.get(k),sort_keys=True)]
def actors():
    ok,a=T(SC+'find_actors',{'name':'','tag':'','collision_channels':[]})
    return [rp(x) for x in (a or []) if LVL in rp(x)]
def run():
    try:
        ok,s=T(AT+'read_file',{'file_path':IN})
        v=json.loads(s)
        acts=actors(); n0=len(acts)
        tl=[r for r in acts if ':PersistentLevel.BP_UserTool_SC_C_' in r]
        if len(tl)!=1: return {'errores':ERRS[:8],'aviso':'UserTool en la Obra: '+str(tl)}
        inst=tl[0]; rep={'inst':inst}
        dif=v.get('dif',{}); cdif=v.get('comp_dif',{})
        if dif:
            rep['antes']=gp(inst,list(dif.keys()))
            for k,val in dif.items():
                T(OT+'set_properties',{'instance':{'refPath':inst},'values':json.dumps({k:val})})
            rep['despues']=gp(inst,list(dif.keys()))
            rep['no_aplicado']=miss(dif,rep['despues'])
        for nm,d in cdif.items():
            c=inst+'.'+nm
            rep['c.'+nm+'.antes']=gp(c,list(d.keys()))
            for k,val in d.items():
                T(OT+'set_properties',{'instance':{'refPath':c},'values':json.dumps({k:txt(val)})})
            got=gp(c,list(d.keys())); rep['c.'+nm]=got
            m=miss(d,got)
            if m: rep['c.'+nm+'.no_aplicado']=m
        fl=gp(inst,['bShowMandoOnBegin'])
        if isinstance(fl,dict) and fl.get('bShowMandoOnBegin'):
            T(OT+'set_properties',{'instance':{'refPath':inst},'values':json.dumps({'bShowMandoOnBegin':False})})
        rep['flag']=gp(inst,['bShowMandoOnBegin'])
        rep['canario']=str(n0)+' -> '+str(len(actors()))
        return {'errores':ERRS[:10],'rep':rep}
    except BaseException as e:
        return {'errores':ERRS[:10]+['run :: '+str(e)[:300]]}
