# p1_pacer_mat.py - M_Pacer_SC: 4 ScalarParameters (ProgCount 0, ProgValue 0, ProgRadius -0.035, ProgAmt 1) + 3 AppendVector
# -> entrada 'Prog' (float4) del Custom (append puro: elementos completos, los viejos identicos) + codigo nuevo
# (pacer_code_new.txt). Recompila. IDEMPOTENTE. El log del compile se revisa aparte (corte por linea).
import json
MT='editor_toolset.toolsets.material.MaterialTools.'
OT='editor_toolset.toolsets.object.ObjectTools.'
AT='editor_toolset.toolsets.asset.AssetTools.'
MI='editor_toolset.toolsets.material_instance.MaterialInstanceTools.'
MP='/Game/SoulCharger/Mechanics/Pacer/M_Pacer_SC.M_Pacer_SC'
MAT={'refPath':MP}
CUS=MP+':MaterialExpressionCustom_0'
D='C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/usertool/'
PARAMS=[('ProgCount',0.0),('ProgValue',0.0),('ProgRadius',-0.035),('ProgAmt',1.0)]
ERRS=[]
def T(n,p):
    try:
        return True, execute_tool(n, json.dumps(p))['returnValue']
    except BaseException as e:
        ERRS.append(n.split('.')[-1]+' :: '+str(e)[:300]); return False, None
def rp(x): return x['refPath'] if isinstance(x,dict) else str(x)
def gp(ref,keys):
    ok,g=T(OT+'get_properties',{'instance':{'refPath':ref},'properties':keys})
    try: return json.loads(g)
    except BaseException: return g
def run():
    try:
        rep={}
        cur=gp(CUS,['Inputs'])
        ins=cur['Inputs'] if isinstance(cur,dict) else []
        rep['inputs_antes']=[i.get('inputName') for i in ins]
        if 'Prog' not in rep['inputs_antes']:
            ok,ps=T(MI+'list_parameters',{'material':MAT})
            have=[p.get('name') for p in (ps or [])]
            ex={}
            for i,(n,v) in enumerate(PARAMS):
                if n in have: ERRS.append('param ya existe '+n); continue
                ok,e=T(MT+'add_expression',{'material_or_function':MAT,'expression_class':{'refPath':'/Script/Engine.MaterialExpressionScalarParameter'},'x':-1400,'y':900+i*90})
                ex[n]=rp(e)
                T(OT+'set_properties',{'instance':e,'values':json.dumps({'parameterName':n})})
                T(OT+'set_properties',{'instance':e,'values':json.dumps({'defaultValue':v})})
            if len(ex)!=4: return {'errores':ERRS[:10],'aviso':'no se crearon los 4 parametros','rep':rep}
            ap=[]
            for i in range(3):
                ok,e=T(MT+'add_expression',{'material_or_function':MAT,'expression_class':{'refPath':'/Script/Engine.MaterialExpressionAppendVector'},'x':-1150+i*150,'y':920+i*60})
                ap.append(rp(e))
            T(MT+'connect_expressions',{'from_expression':{'refPath':ex['ProgCount']},'from_output_name':'','to_expression':{'refPath':ap[0]},'to_input_name':'A'})
            T(MT+'connect_expressions',{'from_expression':{'refPath':ex['ProgValue']},'from_output_name':'','to_expression':{'refPath':ap[0]},'to_input_name':'B'})
            T(MT+'connect_expressions',{'from_expression':{'refPath':ap[0]},'from_output_name':'','to_expression':{'refPath':ap[1]},'to_input_name':'A'})
            T(MT+'connect_expressions',{'from_expression':{'refPath':ex['ProgRadius']},'from_output_name':'','to_expression':{'refPath':ap[1]},'to_input_name':'B'})
            T(MT+'connect_expressions',{'from_expression':{'refPath':ap[1]},'from_output_name':'','to_expression':{'refPath':ap[2]},'to_input_name':'A'})
            T(MT+'connect_expressions',{'from_expression':{'refPath':ex['ProgAmt']},'from_output_name':'','to_expression':{'refPath':ap[2]},'to_input_name':'B'})
            new=ins+[{'inputName':'Prog','input':{'expression':{'refPath':ap[2]},'outputIndex':0,'inputName':'None','mask':0,'maskR':0,'maskG':0,'maskB':0,'maskA':0}}]
            T(OT+'set_properties',{'instance':{'refPath':CUS},'values':json.dumps({'Inputs':new})})
            rep['params']=ex; rep['appends']=ap
        cur=gp(CUS,['Inputs'])
        ins=cur['Inputs'] if isinstance(cur,dict) else []
        rep['inputs']=[(i.get('inputName'), rp(i.get('input',{}).get('expression') or '').split(':')[-1]) for i in ins]
        ok,code=T(AT+'read_file',{'file_path':D+'pacer_code_new.txt'})
        if isinstance(code,dict): code=code.get('content') or code.get('text') or ''
        if code and 'Prog.x' in code:
            T(OT+'set_properties',{'instance':{'refPath':CUS},'values':json.dumps({'Code':code})})
        c=gp(CUS,['Code']); cs=c.get('Code','') if isinstance(c,dict) else str(c)
        rep['code_ok']=('Prog.x' in cs, len(cs))
        T(MT+'recompile',{'material_or_function':MAT})
        return {'errores':ERRS[:10],'rep':rep}
    except BaseException as e:
        return {'errores':ERRS[:10]+['run :: '+str(e)[:300]]}
