# gen_shell_material.py (2026-11-05) - M_AttractShell_SC: la membrana de la ameba vista DESDE ADENTRO (el abrazo del final
# de BP_AttractCall_SC). La ameba (M_ProtoSoul) es translucida de una sola cara: desde adentro no se ve. Esta esfera de dos
# caras alrededor del ojo es lo que se ve cuando la ameba te envuelve.
# Custom Primitive Data: SH 0 = (Alfa, Pulso, Ondulacion cm, Venas) · SC 4 = (color RGB, brillo).
# VS: ondula la membrana por su normal (WPO en mundo). PS: tinte + venas lentas (patron suave que deriva) + pulso.
import json
OUT = 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/'
VS = r'''
float t = View.GameTime;
float3 q = LP * 0.04;
float n = sin(q.x * 1.7 + t * 0.53) * sin(q.y * 1.3 - t * 0.41) + 0.6 * sin(q.z * 2.1 + t * 0.37 + q.x);
return NW * (SH.z * n);
'''
VEIN = r'''
float t = View.GameTime;
float3 q = LP * 0.06;
float v = sin(q.x * 3.1 + t * 0.21) * sin(q.y * 2.7 - t * 0.17) * sin(q.z * 3.3 + t * 0.13);
v = 0.5 + 0.5 * v;
v = lerp(1.0, v, saturate(SH.w));
'''
PS = VEIN + r'''
return SC.rgb * SC.a * (0.8 + 0.4 * v + 0.8 * SH.y);
'''
OP = VEIN + r'''
return saturate(SH.x * (0.7 + 0.3 * v) * (1.0 + 0.6 * SH.y));
'''
CPD = [('SH', 0, (0.0, 0.0, 4.0, 0.6)), ('SC', 4, (1.0, 0.68, 0.38, 1.2))]
params = [{'name': n, 'kind': 'vector', 'group': 'Shell', 'default': list(d), 'cpd': i} for n, i, d in CPD]
customs = [
    {'desc': 'ShellVS', 'outputType': 'CMOT_Float3', 'code_file': 'attract_ShellVS.txt',
     'inputs': [{'name': 'LP', 'src': {'kind': 'localpos'}}, {'name': 'NW', 'src': {'kind': 'normalws'}}, {'name': 'SH', 'src': {'kind': 'param', 'param': 'SH'}}]},
    {'desc': 'ShellPS', 'outputType': 'CMOT_Float3', 'code_file': 'attract_ShellPS.txt',
     'inputs': [{'name': 'LP', 'src': {'kind': 'localpos'}}, {'name': 'SH', 'src': {'kind': 'param', 'param': 'SH'}}, {'name': 'SC', 'src': {'kind': 'param', 'param': 'SC'}}]},
    {'desc': 'ShellOpPS', 'outputType': 'CMOT_Float1', 'code_file': 'attract_ShellOpPS.txt',
     'inputs': [{'name': 'LP', 'src': {'kind': 'localpos'}}, {'name': 'SH', 'src': {'kind': 'param', 'param': 'SH'}}]},
]
outputs = [{'custom': 'ShellVS', 'wpo_world': True}, {'custom': 'ShellPS', 'prop': 'MP_EmissiveColor'}, {'custom': 'ShellOpPS', 'prop': 'MP_Opacity'}]
open(OUT + 'attract_ShellVS.txt', 'w').write(VS.strip() + '\n')
open(OUT + 'attract_ShellPS.txt', 'w').write(PS.strip() + '\n')
open(OUT + 'attract_ShellOpPS.txt', 'w').write(OP.strip() + '\n')
plan = {'material': '/Game/SoulCharger/Mechanics/Harp/Materials/M_AttractShell_SC', 'blend': 'BLEND_Translucent',
        'params': params, 'customs': customs, 'outputs': outputs}
json.dump(plan, open(OUT + 'attract_shell_build.json', 'w'), indent=1)
print('ok shell plan')
