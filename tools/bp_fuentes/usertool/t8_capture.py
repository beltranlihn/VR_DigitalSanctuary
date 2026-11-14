# t8_capture.py - capturas del EDITOR (sin PIE): el metaball a varios EnvT (vista previa del morfeo: el CS aplica
# BlobApplyEnv -> BlobMorph) y la herramienta colocada. Restaura EnvT de la instancia a su valor leido al empezar.
# Guarda el base64 de cada captura en Saved/ClaudeScripts/usertool/cap_*.txt (se decodifica afuera).
import json
OT='editor_toolset.toolsets.object.ObjectTools.'
SC='editor_toolset.toolsets.scene.SceneTools.'
AT='editor_toolset.toolsets.asset.AssetTools.'
EA='EditorToolset.EditorAppToolset.'
OUT='C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/usertool/'
ERRS=[]
def T(n,p):
    try:
        return True, execute_tool(n, json.dumps(p))['returnValue']
    except BaseException as e:
        ERRS.append(n.split('.')[-1]+' :: '+str(e)[:160]); return False, None
def cap(name, loc, rot):
    xf={'location':{'x':loc[0],'y':loc[1],'z':loc[2]},'rotation':{'pitch':rot[0],'yaw':rot[1],'roll':0.0},'scale':{'x':1,'y':1,'z':1}}
    ok,r=T(EA+'CaptureViewport',{'captureTransform':xf,'annotations':[],'bShowUI':False})
    s=json.dumps(r) if not isinstance(r,str) else r
    T(AT+'write_file',{'file_path':OUT+'cap_'+name+'.txt','content':s})
    return len(s)
LVL='/Game/Test_Entering.Test_Entering:PersistentLevel.'
def run():
    try:
        ok,a=T(SC+'find_actors',{'name':'','tag':'','collision_channels':[]})
        rs=[(x['refPath'] if isinstance(x,dict) else str(x)) for x in (a or [])]
        blob=([r for r in rs if LVL+'BP_BreathBlob_SC_C_' in r] or [None])[0]
        ok,g=T(OT+'get_properties',{'instance':{'refPath':blob},'properties':['envT']})
        e0=json.loads(g)['envT'] if g else 1.0
        sizes={}
        cap('dummy',(100,0,130),(5,0))
        for e in __ENVS__:
            T(OT+'set_properties',{'instance':{'refPath':blob},'values':json.dumps({'envT':e})})
            sizes['blob_%03d'%int(e*100)]=cap('blob_%03d'%int(e*100),(100,0,130),(5,0))
        T(OT+'set_properties',{'instance':{'refPath':blob},'values':json.dumps({'envT':e0})})
        ok,g=T(OT+'get_properties',{'instance':{'refPath':blob},'properties':['envT']})
        sizes['tool']=cap('tool',(20,-10,115),(-14.8,45))
        return {'errores':ERRS[:6],'envT_restaurado':g,'bytes':sizes}
    except BaseException as e:
        return {'errores':ERRS[:6]+['run :: '+str(e)[:300]]}
