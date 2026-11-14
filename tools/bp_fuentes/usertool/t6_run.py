# t6_pie_run.py - con PIE corriendo (bContractTest true en la instancia): acelera la prueba SOLO en el mundo de PIE
# (exploracion 4 s, 1 ciclo de pacer, respiracion falsa) y sigue la maquina de fases cuadro a cuadro (cada execute_tool
# consume un cuadro). Devuelve las transiciones con su tiempo y el estado de la herramienta y el metaball en cada una.
import json
OT='editor_toolset.toolsets.object.ObjectTools.'
SC='editor_toolset.toolsets.scene.SceneTools.'
ERRS=[]
def T(n,p):
    try:
        return True, execute_tool(n, json.dumps(p))['returnValue']
    except BaseException as e:
        ERRS.append(n.split('.')[-1]+' :: '+str(e)[:160]); return False, None
def gp(ref,keys):
    ok,g=T(OT+'get_properties',{'instance':{'refPath':ref},'properties':keys})
    try: return json.loads(g)
    except BaseException: return None
N=3200
def run():
    try:
        ok,a=T(SC+'find_actors',{'name':'','tag':'','collision_channels':[]})
        rs=[(x['refPath'] if isinstance(x,dict) else str(x)) for x in (a or [])]
        pie=[r for r in rs if 'UEDPIE' in r]
        pick=lambda cn: ([r for r in pie if (':PersistentLevel.'+cn+'_') in r] or [None])[0]
        st,pac,rig,tool,blob=pick('BP_BreathStage_SC_C'),pick('BP_Pacer_SC_C'),pick('BP_BreathRig_SC_C'),pick('BP_UserTool_SC_C'),pick('BP_BreathBlob_SC_C')
        if st: T(OT+'set_properties',{'instance':{'refPath':st},'values':json.dumps({'exploreTime':4.0})})
        if pac: T(OT+'set_properties',{'instance':{'refPath':pac},'values':json.dumps({'cycles':1})})
        if rig: T(OT+'set_properties',{'instance':{'refPath':rig},'values':json.dumps({'bFakeBreath':True})})
        tr=[]; last=None; clock=0.0
        for i in range(N):
            s=gp(st,['phase','testStage','bStageDone','contractTimer']) if st else None
            if not s: continue
            key=(s.get('phase'),s.get('testStage'),s.get('bStageDone'))
            if key!=last:
                snap={'i':i,'st':s}
                if tool: snap['tool']=gp(tool,['mode','morphT','bMounted','lightColor'])
                if tool: snap['appear']=gp(tool+'.Appear',['AppearT','Playing'])
                if blob: snap['blob']=gp(blob,['envT','bShown'])
                tr.append(snap); last=key
            if s.get('phase')==6 and s.get('testStage')==4: break
        fin={'tool':gp(tool,['mode','morphT','bMounted']) if tool else None,'blob':gp(blob,['envT']) if blob else None}
        return {'errores':ERRS[:8],'actores':{'stage':st,'tool':tool,'blob':blob},'transiciones':tr,'fin':fin,'cuadros':i+1}
    except BaseException as e:
        return {'errores':ERRS[:8]+['run :: '+str(e)[:300]]}
