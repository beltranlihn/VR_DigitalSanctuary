# vo_referencers.py - SOLO LECTURA: quien referencia cada SoundWave VO_* (AssetTools.get_referencers). El grep de los .uasset no
# ve los nombres que terminan en numero (FName guarda "VO_13" como "VO" + 13). Escribe vo_referencers.json.
import json
AT='editor_toolset.toolsets.asset.AssetTools.'
DIRS={'Obra':'/Game/SoulCharger/Obra/Audio/','Hall':'/Game/SoulCharger/Mechanics/Hall/Audio/','Breath':'/Game/SoulCharger/Mechanics/Breath/Audio/'}
IDS=['VO_01a','VO_01b','VO_01c','VO_01d','VO_01h','VO_02','VO_03','VO_03h','VO_04','VO_04b','VO_05','VO_06a','VO_06b','VO_06c','VO_06d','VO_06e','VO_06f','VO_06g','VO_07',
     'VO_10','VO_11','VO_11h','VO_11b','VO_12','VO_12c','VO_12f1','VO_12f2','VO_13','VO_14','VO_15','VO_16','VO_16h','VO_17a','VO_17c','VO_18','VO_19','VO_20','VO_22','VO_23','VO_23b',
     'VO_24','VO_25','VO_26','VO_27','VO_27d','VO_27h','VO_27b','VO_27c','VO_28','VO_29','VO_30','VO_31','VO_32','VO_32d','VO_32h','VO_32b','VO_32c','VO_33','VO_34a','VO_34b','VO_34c',
     'VO_35a','VO_35b','VO_35c','VO_36','VO_36b','VO_36c','VO_36d','VO_36p','VO_37']
OUT='C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/vo_final/vo_referencers.json'
def run():
    out={}; err=[]
    for i in IDS:
        for k,d in DIRS.items():
            p=d+i
            try:
                ex=execute_tool(AT+'exists', json.dumps({'path':p}))['returnValue']
            except BaseException as e:
                err.append(p+' exists :: '+str(e)[:80]); continue
            if not ex: continue
            try:
                r=execute_tool(AT+'get_referencers', json.dumps({'asset_path':p}))['returnValue']
                out[k+'/'+i]=[x['refPath'] if isinstance(x,dict) else str(x) for x in (r or [])]
            except BaseException as e:
                err.append(p+' refs :: '+str(e)[:120])
    try: execute_tool(AT+'write_file', json.dumps({'file_path':OUT,'content':json.dumps(out,indent=1)}))
    except BaseException as e: err.append('write :: '+str(e)[:120])
    return {'n':len(out),'sin_referencias':sorted(k for k,v in out.items() if not v),'errores':err[:8]}
