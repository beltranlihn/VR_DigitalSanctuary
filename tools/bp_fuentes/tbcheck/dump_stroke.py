# Vuelca la geometria del ULTIMO trazo del PIE a Saved/ClaudeScripts/tbcheck/<TAG>.txt (JSON). execute_tool_script.
# Uso: reemplazar TAG. No devuelve los datos al contexto, solo tamanos.
import json
OT='editor_toolset.toolsets.object.ObjectTools.'
SC='editor_toolset.toolsets.scene.SceneTools.'
AS='editor_toolset.toolsets.asset.AssetTools.'
TAG='A'
OUT='C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/tbcheck/'
ERRS=[]
def T(n,p):
    try:
        return execute_tool(n, json.dumps(p))['returnValue']
    except BaseException as e:
        ERRS.append(n.split('.')[-1]+' :: '+str(e)[:200]); return None
PROPS=['K_Pos','K_Size','K_Right','K_Surface','K_Arc','K_SmoothPress','V_Pos','V_Normal','V_UV','V_UV1','V_UV2','V_Color','V_Tri','bIncRebuild','IncN']
def run():
    out={}
    try:
        acts=T(SC+'find_actors',{'name':'','tag':'','collision_channels':[]}) or []
        refs=[(x['refPath'] if isinstance(x,dict) else str(x)) for x in acts]
        st=sorted([r for r in refs if 'UEDPIE' in r and 'BP_TBStroke_C' in r])
        out['strokes']=st
        if not st:
            out['errs']=ERRS; return out
        data={}
        for p in PROPS:
            g=T(OT+'get_properties',{'instance':{'refPath':st[-1]},'properties':[p]})
            if g: data[p]=json.loads(g)[p]
        txt=json.dumps(data)
        T(AS+'write_file',{'file_path':OUT+TAG+'.txt','content':txt})
        out['bytes']=len(txt)
        out['n']={k:(len(v) if isinstance(v,list) else v) for k,v in data.items()}
    except BaseException as e:
        ERRS.append('run :: '+str(e)[:200])
    out['errs']=ERRS
    return out
