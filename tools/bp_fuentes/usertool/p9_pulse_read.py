# p9_pulse_read.py - SOLO LECTURA: PacerPulseAudio / PacerPlaySnd / PacerPlay de BP_Pacer_SC, categorias de las variables que usa el
# pulso nuevo y los sonidos de la instancia Entering_Pacer. Escribe pulse_read.json.
import json
BT='editor_toolset.toolsets.blueprint.BlueprintTools.'
OT='editor_toolset.toolsets.object.ObjectTools.'
SC='editor_toolset.toolsets.scene.SceneTools.'
AT='editor_toolset.toolsets.asset.AssetTools.'
BPP='/Game/SoulCharger/Mechanics/Pacer/BP_Pacer_SC.BP_Pacer_SC'
VARS=['PulseMode','CurPhase','InhaleTime','Hold1Time','ExhaleTime','T','PulseInterval','PulseT','SndPulse','SfxVolume','SndInhale','SndHold','SndExhale']
OUT='C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/usertool/pulse_read.json'
ERRS=[]
def T(n,p):
    try:
        return True, execute_tool(n, json.dumps(p))['returnValue']
    except BaseException as e:
        ERRS.append(n.split('.')[-1]+' :: '+str(e)[:200]); return False, None
def rp(x): return x['refPath'] if isinstance(x,dict) else str(x)
def run():
    try:
        out={}
        for g in ('PacerPulseAudio','PacerPlaySnd','PacerPlay','PacerPhaseAudio'):
            ok,d=T(BT+'read_graph_dsl',{'graph':{'refPath':BPP+':'+g}}); out[g]=d
        cats={}
        for v in VARS:
            ok,c=T(BT+'get_variable_category',{'blueprint':{'refPath':BPP},'variable_name':v}); cats[v]=c
        out['cats']=cats
        ok,a=T(SC+'find_actors',{'name':'','tag':'','collision_channels':[]})
        pl=[rp(x) for x in (a or []) if 'Test_Entering.Test_Entering:PersistentLevel.BP_Pacer_SC_C_' in rp(x) and 'UEDPIE' not in rp(x)]
        out['inst']=pl
        if len(pl)==1:
            ok,g=T(OT+'get_properties',{'instance':{'refPath':pl[0]},'properties':['sndInhale','sndHold','sndExhale','sndPulse','pulseMode','pulseInterval','sfxVolume']}); out['inst.vals']=g
        out['errores']=ERRS
        T(AT+'write_file',{'file_path':OUT,'content':json.dumps(out,indent=1,default=str)})
        return {'cats':cats,'inst':pl,'vals':out.get('inst.vals'),'errores':ERRS[:6]}
    except BaseException as e:
        return {'errores':ERRS[:6]+['run :: '+str(e)[:300]]}
