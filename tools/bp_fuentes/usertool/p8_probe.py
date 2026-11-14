# p8_probe.py - PIE de Test_Entering: valores Prog* efectivos en el MID del Panel del pacer + reloj del pacer. SOLO LECTURA.
import json
OT='editor_toolset.toolsets.object.ObjectTools.'
SC='editor_toolset.toolsets.scene.SceneTools.'
ACT='editor_toolset.toolsets.actor.ActorTools.'
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
def run():
    try:
        ok,a=T(SC+'find_actors',{'name':'','tag':'','collision_channels':[]})
        pl=[rp(x) for x in (a or []) if 'UEDPIE' in rp(x) and '.BP_Pacer_SC_C_' in rp(x)]
        if len(pl)!=1: return {'errores':ERRS[:6],'aviso':str(pl)}
        p=pl[0]; rep={'pacer':p}
        rep['clock']=gp(p,['cycleIndex','t','total','cycles','bRunning','envT'])
        ok,cs=T(ACT+'get_components',{'actor':{'refPath':p}})
        pan=[rp(c) for c in (cs or []) if rp(c).split('.')[-1]=='Panel']
        if pan:
            om=gp(pan[0],['overrideMaterials'])
            rep['om']=str(om)[:300]
            mids=[]
            if isinstance(om,dict):
                for m in (om['overrideMaterials'] or []):
                    r=rp(m) if m else ''
                    if 'MaterialInstanceDynamic' in r or 'MID' in r: mids.append(r)
            if mids:
                sp=gp(mids[0],['scalarParameterValues'])
                vals={}
                if isinstance(sp,dict):
                    for s in sp['scalarParameterValues']:
                        n=s['parameterInfo']['name']
                        if n.startswith('Prog'): vals[n]=s['parameterValue']
                rep['prog']=vals
        return {'errores':ERRS[:6],'rep':rep}
    except BaseException as e:
        return {'errores':ERRS[:6]+['run :: '+str(e)[:300]]}
